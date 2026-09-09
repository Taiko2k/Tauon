# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

"""Blurred window background on macOS, for the window-transparency styles.

The public way to do this is an NSVisualEffectView, but every material it
offers bakes a scrim into the blur — the panels would sit on a grey fill
rather than on the blurred desktop, which is not what the glass styles are
after. SkyLight's window background blur does what ext-background-effect-v1
does on Wayland instead: it blurs what is behind the window and tints nothing
(the average colour behind the window comes out unchanged, only the detail
goes).

That call is private, so everything here is written to fail quietly. A missing
framework, a missing symbol or an error from the call itself all end with
`unavailable` set and the app carrying on with no blur, the same as it does
under a compositor that doesn't offer the protocol.
"""

from __future__ import annotations

import ctypes
import logging
from typing import TYPE_CHECKING

import sdl3

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Tauon

SKYLIGHT_PATH = "/System/Library/PrivateFrameworks/SkyLight.framework/SkyLight"
# Enough to lose the detail of whatever is behind without smearing the desktop
# into one flat colour, which is about where the Hyprland side sits too
BLUR_RADIUS = 24


class MacOSBlur:
	"""Blurs what is behind the window while a glass style is on"""

	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.prefs = tauon.prefs

		self.lib: ctypes.CDLL | None = None
		self.connection: int | None = None
		self.window_number: int | None = None

		self.applied: int | None = 0
		self.attached = False
		self.unavailable = False

	# --- Public interface

	def sync(self) -> None:
		"""Apply the wanted blur state; call once per frame, before present"""
		if self.unavailable:
			return
		wanted = self.wanted_radius()
		if not self.attached:
			# Nothing to reach for until a glass style is actually on: this is
			# private API, and someone who never turns one on should never be
			# calling it
			if not wanted or not self.attach():
				return
		elif not self.check_window():
			return
		if wanted == self.applied:
			return
		self.apply(wanted)

	def shutdown(self) -> None:
		"""Take the blur back off (the window is going away)"""
		if not self.unavailable and self.attached and self.applied:
			self.apply(0)
		self.attached = False
		self.unavailable = True

	# --- Wanted state

	def wanted_radius(self) -> int:
		"""Blur radius for the window, or 0 for no blur"""
		return BLUR_RADIUS if self.prefs.transparent_mode else 0

	def apply(self, radius: int) -> None:
		result = self.lib.CGSSetWindowBackgroundBlurRadius(self.connection, self.window_number, radius)
		if result != 0:
			logging.warning("SkyLight refused the window blur (%s), carrying on without it", result)
			self.unavailable = True
			return
		self.applied = radius

	# --- SkyLight plumbing

	def attach(self) -> bool:
		if not self.load_library():
			return False
		number = self.get_window_number()
		if number is None:
			self.unavailable = True
			return False
		self.window_number = number
		self.attached = True
		logging.info("Using SkyLight window background blur")
		return True

	def load_library(self) -> bool:
		if self.lib is not None:
			return True
		if sdl3.SDL_GetCurrentVideoDriver() != b"cocoa":
			self.unavailable = True
			return False
		try:
			lib = ctypes.CDLL(SKYLIGHT_PATH)
			lib.CGSDefaultConnectionForThread.argtypes = ()
			lib.CGSDefaultConnectionForThread.restype = ctypes.c_int
			lib.CGSSetWindowBackgroundBlurRadius.argtypes = (ctypes.c_int, ctypes.c_uint32, ctypes.c_int)
			lib.CGSSetWindowBackgroundBlurRadius.restype = ctypes.c_int
			connection = lib.CGSDefaultConnectionForThread()
		except (OSError, AttributeError):
			# The framework or the call being gone is a thing that is allowed
			# to happen to private API; it just means no blur
			logging.info("SkyLight window blur is not available on this system")
			self.unavailable = True
			return False
		if not connection:
			self.unavailable = True
			return False
		self.lib = lib
		self.connection = connection
		return True

	def get_window_number(self) -> int | None:
		"""The window server's id for our window, which the blur call takes"""
		try:
			import objc  # noqa: PLC0415 - macOS only

			properties = sdl3.SDL_GetWindowProperties(self.tauon.t_window)
			pointer = sdl3.SDL_GetPointerProperty(
				properties, sdl3.SDL_PROP_WINDOW_COCOA_WINDOW_POINTER, None)
			if not pointer:
				return None
			window = objc.objc_object(c_void_p=ctypes.c_void_p(int(pointer)))
			return int(window.windowNumber())
		except Exception:
			logging.exception("Failed to find the macOS window")
			return None

	def check_window(self) -> bool:
		"""Follow SDL if it has handed us a different window since"""
		number = self.get_window_number()
		if number is None:
			return False
		if number != self.window_number:
			self.window_number = number
			# A new window carries no blur of its own yet
			self.applied = None
		return True
