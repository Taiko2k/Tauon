# Tauon Music Box - secondary window scaffold
#
# Provides on-screen windows that render with their own SDL renderer, *in
# addition to* the main window, sharing the same draw stack.
#
# This is the shared foundation for any UI that needs to live in its own OS
# window rather than being clipped to the main window:
#
#   * Context menus that can extend past the edge of the main window. This
#     matters most on Wayland, where a client cannot position a top-level
#     window at arbitrary screen coordinates - menus must instead be popup
#     surfaces (xdg_popup) anchored to the parent, which the compositor keeps
#     on-screen by flipping/sliding near display edges.
#   * In future, mini-mode views drawn alongside the main window instead of
#     replacing it.
#
# Each SecondaryWindow owns:
#   * an SDL window (a popup/menu child of the main window, so the compositor
#     handles on-screen constraint for us, or a borderless top-level)
#   * its own SDL renderer
#   * its own TDraw instance, and therefore its own glyph/text cache
#
# Drawing code renders into a SecondaryWindow exactly as it renders into the
# main window, by using the window's `ddt`. Image assets are shared across
# renderers via their per-renderer lazy texture cache (see LoadImageAsset /
# WhiteModImageAsset in t_main).

from __future__ import annotations

import ctypes
import logging
from typing import TYPE_CHECKING

import sdl3

from tauon.t_modules.t_draw import TDraw
from tauon.t_modules.t_extra import ColourRGBA

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Tauon


def renderer_key(renderer: sdl3.LP_SDL_Renderer) -> int:
	"""Stable integer identity for an SDL renderer pointer.

	Used as a dict key so shared resources (image-asset textures) can be cached
	per renderer. ctypes pointer objects are not reliably hashable/comparable by
	address, so we cast to the raw pointer value.
	"""
	return ctypes.cast(renderer, ctypes.c_void_p).value or 0


class SecondaryWindow:
	"""A borderless popup window with its own renderer and draw context."""

	def __init__(self, tauon: Tauon, *, popup: bool = True, transparent: bool = True, high_dpi: bool = True, focusable: bool = True) -> None:
		self.tauon = tauon
		self.parent: sdl3.LP_SDL_Window = tauon.t_window
		self.popup = popup
		self.transparent = transparent
		self.high_dpi = high_dpi
		# A non-focusable window never steals keyboard focus from the parent, so
		# the main window stays focused and keeps receiving keyboard input while
		# the popup is up. Mouse focus is independent and still follows the
		# pointer, so the popup still gets its own mouse events. This is what a
		# context menu wants.
		self.focusable = focusable

		self.window: sdl3.LP_SDL_Window | None = None
		self.renderer: sdl3.LP_SDL_Renderer | None = None
		self.ddt: TDraw | None = None

		# All public sizes/positions are in *content pixels* - the same space the
		# main window draws in (gui.scale baked in, matching tauon.window_size).
		# SDL window sizing/positioning and mouse-motion events are in logical
		# *points*, so we convert through the parent window's pixel/point ratio.
		# `scale` is pixels-per-point; the input router multiplies popup event
		# coordinates by it to recover content-pixel coordinates.
		self.scale = 1.0
		self.w = 0
		self.h = 0
		self.pos: tuple[int, int] = (0, 0)
		# Last pointer position seen inside this window, in its own content
		# pixels (window-local). The menu hit-tests against this; it is kept
		# entirely separate from the main window's mouse position.
		self.last_local: tuple[int, int] = (0, 0)
		self.visible = False

	# --- lifecycle -------------------------------------------------------

	def _refresh_scale(self) -> None:
		pt_w, pt_h = ctypes.c_int(0), ctypes.c_int(0)
		px_w, px_h = ctypes.c_int(0), ctypes.c_int(0)
		sdl3.SDL_GetWindowSize(self.parent, ctypes.byref(pt_w), ctypes.byref(pt_h))
		sdl3.SDL_GetWindowSizeInPixels(self.parent, ctypes.byref(px_w), ctypes.byref(px_h))
		if self.high_dpi and pt_w.value > 0:
			self.scale = px_w.value / pt_w.value
		else:
			self.scale = 1.0

	def _to_points(self, value: int) -> int:
		return int(round(value / self.scale)) if self.scale else int(value)

	def _create(self, w: int, h: int, offset_x: int, offset_y: int) -> bool:
		flags = 0
		if self.high_dpi:
			flags |= sdl3.SDL_WINDOW_HIGH_PIXEL_DENSITY
		if self.transparent:
			flags |= sdl3.SDL_WINDOW_TRANSPARENT
		if not self.focusable:
			flags |= sdl3.SDL_WINDOW_NOT_FOCUSABLE

		if self.popup:
			# POPUP_MENU maps to xdg_popup on Wayland: the position is an offset
			# relative to the parent window, and the compositor constrains it to
			# the display (flipping/sliding near edges) - which is exactly the
			# edge handling we want, against the real screen rather than the
			# main window bounds.
			flags |= sdl3.SDL_WINDOW_POPUP_MENU
			self.window = sdl3.SDL_CreatePopupWindow(
				self.parent, self._to_points(offset_x), self._to_points(offset_y),
				self._to_points(w), self._to_points(h), flags,
			)
		else:
			flags |= sdl3.SDL_WINDOW_BORDERLESS | sdl3.SDL_WINDOW_RESIZABLE
			self.window = sdl3.SDL_CreateWindow(b"Tauon", self._to_points(w), self._to_points(h), flags)

		if not self.window:
			logging.error(f"SecondaryWindow: failed to create window - {sdl3.SDL_GetError()}")
			return False

		self.renderer = sdl3.SDL_CreateRenderer(self.window, None)
		if not self.renderer:
			logging.error(f"SecondaryWindow: failed to create renderer - {sdl3.SDL_GetError()}")
			sdl3.SDL_DestroyWindow(self.window)
			self.window = None
			return False

		sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_BLEND)

		self.ddt = TDraw(self.renderer)
		self.ddt.scale = self.tauon.ddt.scale
		# Share the main context's font registry. Font handles (e.g. 412) are
		# primed once on the main ddt via prime_font(); the spec strings are
		# renderer-independent, and these dicts are mutated in place on rescale,
		# so sharing the references keeps the popup's fonts in sync for free.
		self.ddt.f_dict = self.tauon.ddt.f_dict
		self.ddt.font_desc_cache = self.tauon.ddt.font_desc_cache

		self.w = int(w)
		self.h = int(h)
		return True

	def show(self, w: int, h: int, offset_x: int, offset_y: int) -> bool:
		"""Create-or-resize the window, position it relative to the parent, show it.

		`w`/`h`/`offset_x`/`offset_y` are in content pixels; offsets are relative
		to the parent window's top-left, matching Wayland popup anchor semantics.
		"""
		self._refresh_scale()

		if self.window is None:
			if not self._create(w, h, offset_x, offset_y):
				return False
			self.pos = (int(offset_x), int(offset_y))
		else:
			# Only touch geometry when it actually changes: Wayland restricts
			# moving/resizing popup surfaces after they are mapped.
			if (int(w), int(h)) != (self.w, self.h):
				sdl3.SDL_SetWindowSize(self.window, self._to_points(w), self._to_points(h))
				self.w = int(w)
				self.h = int(h)
			if (int(offset_x), int(offset_y)) != self.pos:
				sdl3.SDL_SetWindowPosition(self.window, self._to_points(offset_x), self._to_points(offset_y))
				self.pos = (int(offset_x), int(offset_y))

		if self.ddt is not None:
			self.ddt.scale = self.tauon.ddt.scale

		# Only show on the visible transition: re-showing every frame re-grabs
		# input focus and churns window state.
		if not self.visible:
			# Seed the pointer to the popup's top-left until real motion arrives.
			self.last_local = (0, 0)
			sdl3.SDL_ShowWindow(self.window)
			self.visible = True
		return True

	def _release_input_grab(self) -> None:
		"""Release any window mouse grab and the global mouse capture.

		SDL_CaptureMouse is a *global* capture (not tied to this window), which
		SDL acquires during window operations such as resizing. Destroying the
		window does NOT release it, so it must be released explicitly or the OS
		keeps routing all mouse events to this window and the main window goes
		unresponsive.
		"""
		if self.window is not None:
			sdl3.SDL_SetWindowMouseGrab(self.window, False)
		sdl3.SDL_CaptureMouse(False)

	def hide(self) -> None:
		if self.window is not None and self.visible:
			self._release_input_grab()
			sdl3.SDL_HideWindow(self.window)
			# Hiding does not reliably hand input focus back to the parent, so
			# raise it explicitly.
			sdl3.SDL_RaiseWindow(self.parent)
		self.visible = False

	def destroy(self) -> None:
		self._release_input_grab()
		if self.renderer is not None:
			sdl3.SDL_DestroyRenderer(self.renderer)
			self.renderer = None
		if self.window is not None:
			sdl3.SDL_DestroyWindow(self.window)
			self.window = None
		self.ddt = None
		self.visible = False

	# --- per-frame drawing ----------------------------------------------

	def begin_frame(self, clear: ColourRGBA = ColourRGBA(0, 0, 0, 0)) -> None:
		"""Make this window's renderer current and clear it."""
		sdl3.SDL_SetRenderTarget(self.renderer, None)
		sdl3.SDL_SetRenderDrawColor(self.renderer, clear.r, clear.g, clear.b, clear.a)
		sdl3.SDL_RenderClear(self.renderer)
		if self.ddt is not None:
			self.ddt.new_frame()

	def end_frame(self) -> None:
		sdl3.SDL_RenderPresent(self.renderer)

	def window_id(self) -> int:
		if self.window is None:
			return 0
		return sdl3.SDL_GetWindowID(self.window)
