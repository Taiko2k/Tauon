# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

"""Blurred window background on Windows, for the window-transparency styles.

Two ways exist, and they are the same trade-off as on macOS.

user32's SetWindowCompositionAttribute with ACCENT_ENABLE_BLURBEHIND is the one
that does what ext-background-effect-v1 does on Wayland: it blurs what is
behind the window, and the tint is ours to choose — a zero alpha in the accent
policy's gradient colour leaves the blur untinted. It works on Windows 10 and
11 and is undocumented.

DWM's system backdrop (Windows 11 22H2 and later) is documented, but its
acrylic bakes in a scrim the way NSVisualEffectView's materials do, and its
mica samples the wallpaper rather than the windows actually behind us. It is
kept here as a fallback for when the accent call is refused.

Either way the call is one the OS is free to stop honouring, so everything
here fails quietly: a missing export, a refused call or a driver that isn't
"windows" all end with `unavailable` set and the app carrying on with no blur.
"""

from __future__ import annotations

import ctypes
import logging
from typing import TYPE_CHECKING

import sdl3

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Tauon

# ACCENT_STATE
ACCENT_DISABLED = 0
ACCENT_ENABLE_BLURBEHIND = 3
# The acrylic variant tints, and has dragged windows lagging behind the cursor
# since Windows 10 1803, so it isn't used here
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
WCA_ACCENT_POLICY = 19
# AABBGGRR. Alpha 0 asks for no tint at all; if a build turns out to want some
# alpha before it will draw the blur, a very low one (0x01000000) is the usual
# workaround
BLUR_TINT = 0x00000000

# DwmSetWindowAttribute
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMSBT_NONE = 1
DWMSBT_TRANSIENTWINDOW = 3  # Acrylic


class AccentPolicy(ctypes.Structure):
	_fields_ = (
		("accent_state", ctypes.c_int),
		("accent_flags", ctypes.c_uint),
		("gradient_colour", ctypes.c_uint),
		("animation_id", ctypes.c_uint),
	)


class CompositionAttributeData(ctypes.Structure):
	_fields_ = (
		("attribute", ctypes.c_int),
		("data", ctypes.c_void_p),
		("size", ctypes.c_size_t),
	)


class Margins(ctypes.Structure):
	_fields_ = (
		("left", ctypes.c_int),
		("right", ctypes.c_int),
		("top", ctypes.c_int),
		("bottom", ctypes.c_int),
	)


class WindowsBlur:
	"""Blurs what is behind the window while a glass style is on"""

	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.prefs = tauon.prefs

		self.set_composition = None
		self.dwm = None
		self.hwnd: int | None = None
		# Which of the two mechanisms took: "accent", "dwm" or None
		self.mechanism: str | None = None

		self.applied: bool | None = False
		self.attached = False
		self.unavailable = False

	# --- Public interface

	def sync(self) -> None:
		"""Apply the wanted blur state; call once per frame, before present"""
		if self.unavailable:
			return
		wanted = bool(self.prefs.transparent_mode)
		if not self.attached:
			# Nothing to reach for until a glass style is actually on: one of
			# these calls is undocumented, and someone who never turns one on
			# should never be making it
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
			self.apply(False)
		self.attached = False
		self.unavailable = True

	# --- Applying it

	def apply(self, blur: bool) -> None:
		if self.set_composition is not None and self.set_accent(blur):
			self.mechanism = "accent"
			self.applied = blur
			return
		# The accent policy is the one that can be left untinted, so it is only
		# worth falling back to the backdrop if that call is refused outright
		if self.dwm is not None and self.set_backdrop(blur):
			self.mechanism = "dwm"
			self.applied = blur
			return
		logging.info("Window blur was refused, carrying on without it")
		self.unavailable = True

	def set_accent(self, blur: bool) -> bool:
		policy = AccentPolicy(
			ACCENT_ENABLE_BLURBEHIND if blur else ACCENT_DISABLED, 0, BLUR_TINT, 0)
		data = CompositionAttributeData(
			WCA_ACCENT_POLICY, ctypes.cast(ctypes.byref(policy), ctypes.c_void_p), ctypes.sizeof(policy))
		try:
			return bool(self.set_composition(ctypes.c_void_p(self.hwnd), ctypes.byref(data)))
		except OSError:
			logging.exception("SetWindowCompositionAttribute failed")
			return False

	def set_backdrop(self, blur: bool) -> bool:
		value = ctypes.c_int(DWMSBT_TRANSIENTWINDOW if blur else DWMSBT_NONE)
		try:
			result = self.dwm.DwmSetWindowAttribute(
				ctypes.c_void_p(self.hwnd), DWMWA_SYSTEMBACKDROP_TYPE,
				ctypes.byref(value), ctypes.sizeof(value))
			if result != 0:
				return False
			# The backdrop is drawn behind the frame, so the frame has to cover
			# the window for any of it to show
			margins = Margins(-1, -1, -1, -1) if blur else Margins(0, 0, 0, 0)
			self.dwm.DwmExtendFrameIntoClientArea(ctypes.c_void_p(self.hwnd), ctypes.byref(margins))
		except OSError:
			logging.exception("DwmSetWindowAttribute failed")
			return False
		return True

	# --- Plumbing

	def attach(self) -> bool:
		if not self.load_libraries():
			return False
		handle = self.get_hwnd()
		if handle is None:
			self.unavailable = True
			return False
		self.hwnd = handle
		self.attached = True
		logging.info("Using the Windows compositor for window blur")
		return True

	def load_libraries(self) -> bool:
		if self.set_composition is not None or self.dwm is not None:
			return True
		if sdl3.SDL_GetCurrentVideoDriver() != b"windows":
			self.unavailable = True
			return False
		try:
			# ctypes.windll only exists on Windows
			user32 = ctypes.windll.user32
			dwm = ctypes.windll.dwmapi
		except (AttributeError, OSError):
			logging.info("Window blur is not available on this system")
			self.unavailable = True
			return False
		# Not in any header, so it is fetched by name and simply may not be there
		self.set_composition = getattr(user32, "SetWindowCompositionAttribute", None)
		if self.set_composition is not None:
			self.set_composition.argtypes = (ctypes.c_void_p, ctypes.POINTER(CompositionAttributeData))
			self.set_composition.restype = ctypes.c_int
		self.dwm = dwm if hasattr(dwm, "DwmSetWindowAttribute") else None
		if self.set_composition is None and self.dwm is None:
			self.unavailable = True
			return False
		return True

	def get_hwnd(self) -> int | None:
		"""The window handle the blur calls take"""
		try:
			properties = sdl3.SDL_GetWindowProperties(self.tauon.t_window)
			pointer = sdl3.SDL_GetPointerProperty(
				properties, sdl3.SDL_PROP_WINDOW_WIN32_HWND_POINTER, None)
			return int(pointer) if pointer else None
		except Exception:
			logging.exception("Failed to find the Windows window handle")
			return None

	def check_window(self) -> bool:
		"""Follow SDL if it has handed us a different window since"""
		handle = self.get_hwnd()
		if handle is None:
			return False
		if handle != self.hwnd:
			self.hwnd = handle
			# A new window carries no blur of its own yet
			self.applied = None
		return True
