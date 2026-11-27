"""xdg-activation tokens for handing focus to another app on Wayland

This module exists because SDL has no public function for getting an
activation token for another app. SDL makes one internally for SDL_OpenURL
(Wayland_GetActivationTokenForExport, since 3.4.6) but doesn't export it.
Replace this with an SDL call if one appears.

A token only raises the other app's window if it carries the serial of the
user's latest input. SDL doesn't expose that either, so this binds its own
wl_seat and input devices on a private queue to see the same serials:
- KWin wants a serial no older than the latest button or key press.
- Mutter wants the button press serial, or a held key's press or latest key
  release serial.

Marshalled directly against libwayland-client, like t_wayland_blur. Anything
missing just means no token, and the other app may open behind Tauon.
"""

# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

from __future__ import annotations

import contextlib
import ctypes
import logging
import os
from typing import TYPE_CHECKING

from tauon.t_modules import t_native as sdl3
from tauon.t_modules.t_wayland_blur import (
	CAPABILITIES_CALLBACK,
	GLOBAL_CALLBACK,
	GLOBAL_REMOVE_CALLBACK,
	WL_DISPLAY_GET_REGISTRY,
	WL_MARSHAL_FLAG_DESTROY,
	WL_REGISTRY_BIND,
	WlInterface,
	WlMessage,
)

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Tauon

SEAT_NAME = b"wl_seat"
ACTIVATION_NAME = b"xdg_activation_v1"
TOKEN_NAME = b"xdg_activation_token_v1"

# Version 1 keeps the event sets (and the listeners we must supply) small
SEAT_VERSION = 1

# wl_seat requests and capabilities
WL_SEAT_GET_POINTER = 0
WL_SEAT_GET_KEYBOARD = 1
WL_SEAT_GET_TOUCH = 2
SEAT_CAPABILITY_POINTER = 1
SEAT_CAPABILITY_KEYBOARD = 2
SEAT_CAPABILITY_TOUCH = 4
WL_POINTER_BUTTON_STATE_PRESSED = 1

# xdg_activation_v1 / xdg_activation_token_v1 requests
XDG_ACTIVATION_DESTROY = 0
XDG_ACTIVATION_GET_ACTIVATION_TOKEN = 1
TOKEN_SET_SERIAL = 0
TOKEN_SET_SURFACE = 2
TOKEN_COMMIT = 3
TOKEN_DESTROY = 4

# Listener signatures, (data, proxy, event args...)
U32 = ctypes.c_uint32
I32 = ctypes.c_int32
PTR = ctypes.c_void_p
POINTER_ENTER = ctypes.CFUNCTYPE(None, PTR, PTR, U32, PTR, I32, I32)
POINTER_LEAVE = ctypes.CFUNCTYPE(None, PTR, PTR, U32, PTR)
POINTER_MOTION = ctypes.CFUNCTYPE(None, PTR, PTR, U32, I32, I32)
POINTER_BUTTON = ctypes.CFUNCTYPE(None, PTR, PTR, U32, U32, U32, U32)
POINTER_AXIS = ctypes.CFUNCTYPE(None, PTR, PTR, U32, U32, I32)
KEYBOARD_KEYMAP = ctypes.CFUNCTYPE(None, PTR, PTR, U32, I32, U32)
KEYBOARD_ENTER = ctypes.CFUNCTYPE(None, PTR, PTR, U32, PTR, PTR)
KEYBOARD_LEAVE = ctypes.CFUNCTYPE(None, PTR, PTR, U32, PTR)
KEYBOARD_KEY = ctypes.CFUNCTYPE(None, PTR, PTR, U32, U32, U32, U32)
KEYBOARD_MODIFIERS = ctypes.CFUNCTYPE(None, PTR, PTR, U32, U32, U32, U32, U32)
TOUCH_DOWN = ctypes.CFUNCTYPE(None, PTR, PTR, U32, U32, PTR, I32, I32, I32)
TOUCH_UP = ctypes.CFUNCTYPE(None, PTR, PTR, U32, U32, I32)
TOUCH_MOTION = ctypes.CFUNCTYPE(None, PTR, PTR, U32, I32, I32, I32)
TOUCH_BARE = ctypes.CFUNCTYPE(None, PTR, PTR)
TOKEN_DONE = ctypes.CFUNCTYPE(None, PTR, PTR, ctypes.c_char_p)


class WaylandActivation:
	"""Tracks the latest input serial and turns it into activation tokens"""

	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.lib: ctypes.CDLL | None = None
		self.display: int | None = None
		self.queue: int | None = None
		self.registry: int | None = None
		self.seat: int | None = None
		self.activation: int | None = None
		self.pointer: int | None = None
		self.keyboard: int | None = None
		self.touch: int | None = None

		self.interfaces: dict[str, WlInterface] = {}
		# C holds pointers into these; they must outlive the proxies using them
		self.keep_alive: list = []
		self.globals: dict[bytes, tuple[int, int]] = {}

		self.serial: int | None = None
		self.token: str | None = None
		self.attached = False
		self.unavailable = False

	# --- Public interface

	def drain(self) -> None:
		"""Handle queued input events; call once per main loop pass so they don't pile up"""
		if self.unavailable:
			return
		if not self.attached and not self.attach():
			return
		self.lib.wl_display_dispatch_queue_pending(ctypes.c_void_p(self.display), ctypes.c_void_p(self.queue))

	def request_token(self) -> str | None:
		"""A fresh single-use token from the latest input, or None. Main thread only."""
		try:
			self.drain()
			if not self.attached or self.serial is None:
				return None
			surface = sdl3.get_window_pointer_property(
				self.tauon.t_window, sdl3.SDL_PROP_WINDOW_WAYLAND_SURFACE_POINTER)
			if not surface:
				return None

			token = self.marshal(
				self.activation, XDG_ACTIVATION_GET_ACTIVATION_TOKEN,
				ctypes.byref(self.interfaces["token"]), 1, 0, None)
			if not token:
				return None
			self.token = None
			self.listen(token, (TOKEN_DONE, self.on_token_done))
			self.marshal(token, TOKEN_SET_SERIAL, None, 1, 0, ctypes.c_uint32(self.serial), ctypes.c_void_p(self.seat))
			self.marshal(token, TOKEN_SET_SURFACE, None, 1, 0, ctypes.c_void_p(surface))
			self.marshal(token, TOKEN_COMMIT, None, 1, 0)
			# Compositors answer the commit straight away, but allow for a slower one
			for _ in range(3):
				if self.token is not None:
					break
				if self.lib.wl_display_roundtrip_queue(ctypes.c_void_p(self.display), ctypes.c_void_p(self.queue)) < 0:
					break
			self.marshal(token, TOKEN_DESTROY, None, 1, WL_MARSHAL_FLAG_DESTROY)
			return self.token
		except Exception:
			logging.exception("Failed to get a Wayland activation token")
			return None

	def shutdown(self) -> None:
		"""Stop using the connection (the window is going away)"""
		self.attached = False
		self.unavailable = True

	# --- Event handlers

	def on_token_done(self, _data: int, _token: int, token: bytes) -> None:
		self.token = token.decode(errors="replace") if token else None

	def on_capabilities(self, _data: int, _seat: int, caps: int) -> None:
		if caps & SEAT_CAPABILITY_POINTER and not self.pointer:
			self.pointer = self.marshal(
				self.seat, WL_SEAT_GET_POINTER, ctypes.byref(self.interfaces["pointer"]), SEAT_VERSION, 0, None)
			if self.pointer:
				self.listen(
					self.pointer,
					(POINTER_ENTER, lambda *_a: None),
					(POINTER_LEAVE, lambda *_a: None),
					(POINTER_MOTION, lambda *_a: None),
					(POINTER_BUTTON, self.on_button),
					(POINTER_AXIS, lambda *_a: None))
		if caps & SEAT_CAPABILITY_KEYBOARD and not self.keyboard:
			self.keyboard = self.marshal(
				self.seat, WL_SEAT_GET_KEYBOARD, ctypes.byref(self.interfaces["keyboard"]), SEAT_VERSION, 0, None)
			if self.keyboard:
				self.listen(
					self.keyboard,
					(KEYBOARD_KEYMAP, self.on_keymap),
					(KEYBOARD_ENTER, lambda *_a: None),
					(KEYBOARD_LEAVE, lambda *_a: None),
					(KEYBOARD_KEY, self.on_key),
					(KEYBOARD_MODIFIERS, lambda *_a: None))
		if caps & SEAT_CAPABILITY_TOUCH and not self.touch:
			self.touch = self.marshal(
				self.seat, WL_SEAT_GET_TOUCH, ctypes.byref(self.interfaces["touch"]), SEAT_VERSION, 0, None)
			if self.touch:
				self.listen(
					self.touch,
					(TOUCH_DOWN, self.on_touch_down),
					(TOUCH_UP, lambda *_a: None),
					(TOUCH_MOTION, lambda *_a: None),
					(TOUCH_BARE, lambda *_a: None),
					(TOUCH_BARE, lambda *_a: None))

	def on_button(self, _data: int, _pointer: int, serial: int, _time: int, _button: int, state: int) -> None:
		# Press only: both compositors check the press serial, not the release
		if state == WL_POINTER_BUTTON_STATE_PRESSED:
			self.serial = serial

	def on_key(self, _data: int, _keyboard: int, serial: int, _time: int, _key: int, _state: int) -> None:
		# Press or release: Mutter accepts the latest release once a key is up
		self.serial = serial

	def on_touch_down(self, _data: int, _touch: int, serial: int, *_rest: object) -> None:
		self.serial = serial

	def on_keymap(self, _data: int, _keyboard: int, _format: int, fd: int, _size: int) -> None:
		# We don't read the keymap, but we own the fd
		with contextlib.suppress(OSError):
			os.close(fd)

	# --- Setup

	def attach(self) -> bool:
		try:
			# tauon.wayland only reflects SDL_VIDEODRIVER; ask SDL what it chose
			if sdl3.get_current_video_driver() != b"wayland":
				self.unavailable = True
				return False
			if not self.load_library():
				return False
			display = sdl3.get_window_pointer_property(
				self.tauon.t_window, sdl3.SDL_PROP_WINDOW_WAYLAND_DISPLAY_POINTER)
			if not display:
				# The window may not be shown yet; try again next pass
				return False
			self.display = display
			if not self.collect_globals():
				self.unavailable = True
				return False
			if SEAT_NAME not in self.globals or ACTIVATION_NAME not in self.globals:
				logging.info("Compositor has no xdg-activation-v1, apps Tauon opens may not take focus")
				self.unavailable = True
				return False

			name, _version = self.globals[ACTIVATION_NAME]
			self.activation = self.bind(name, self.interfaces["activation"], 1)
			name, _version = self.globals[SEAT_NAME]
			self.seat = self.bind(name, self.interfaces["seat"], SEAT_VERSION)
			if not self.activation or not self.seat:
				self.unavailable = True
				return False
			self.listen(self.seat, (CAPABILITIES_CALLBACK, self.on_capabilities))
			# Capabilities, then the devices' first events
			self.lib.wl_display_roundtrip_queue(ctypes.c_void_p(display), ctypes.c_void_p(self.queue))
			self.attached = True
			return True
		except Exception:
			logging.exception("Failed to set up Wayland activation tokens")
			self.unavailable = True
			return False

	def load_library(self) -> bool:
		if self.lib is not None:
			return True
		try:
			lib = ctypes.CDLL("libwayland-client.so.0")
		except OSError:
			logging.warning("Could not load libwayland-client, no activation tokens")
			self.unavailable = True
			return False
		# Arguments are passed as explicit ctypes values (wl_proxy_marshal_flags is variadic)
		lib.wl_proxy_marshal_flags.restype = ctypes.c_void_p
		lib.wl_proxy_create_wrapper.restype = ctypes.c_void_p
		lib.wl_proxy_create_wrapper.argtypes = (ctypes.c_void_p,)
		lib.wl_proxy_wrapper_destroy.argtypes = (ctypes.c_void_p,)
		lib.wl_proxy_set_queue.argtypes = (ctypes.c_void_p, ctypes.c_void_p)
		lib.wl_proxy_add_listener.argtypes = (ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
		lib.wl_proxy_add_listener.restype = ctypes.c_int
		lib.wl_display_create_queue.argtypes = (ctypes.c_void_p,)
		lib.wl_display_create_queue.restype = ctypes.c_void_p
		lib.wl_display_roundtrip_queue.argtypes = (ctypes.c_void_p, ctypes.c_void_p)
		lib.wl_display_roundtrip_queue.restype = ctypes.c_int
		lib.wl_display_dispatch_queue_pending.argtypes = (ctypes.c_void_p, ctypes.c_void_p)
		lib.wl_display_dispatch_queue_pending.restype = ctypes.c_int
		self.lib = lib
		self.build_interfaces()
		return True

	def build_interfaces(self) -> None:
		"""Core interfaces from libwayland; hand-built ones for xdg-activation-v1"""
		lib = self.lib
		for key, symbol in (
			("registry", "wl_registry_interface"), ("seat", "wl_seat_interface"),
			("pointer", "wl_pointer_interface"), ("keyboard", "wl_keyboard_interface"),
			("touch", "wl_touch_interface"), ("surface", "wl_surface_interface"),
		):
			self.interfaces[key] = WlInterface.in_dll(lib, symbol)
		self.keep_alive.extend(self.interfaces.values())

		def address(interface: WlInterface) -> ctypes.c_void_p:
			return ctypes.cast(ctypes.pointer(interface), ctypes.c_void_p)

		token = WlInterface()
		activation = WlInterface()
		surface = address(self.interfaces["surface"])
		seat = address(self.interfaces["seat"])

		token_methods = self.build_messages(
			("set_serial", "uo", (None, seat)),
			("set_app_id", "s", (None,)),
			("set_surface", "o", (surface,)),
			("commit", "", ()),
			("destroy", "", ()),
		)
		token_events = self.build_messages(("done", "s", (None,)))
		token.name = TOKEN_NAME
		token.version = 1
		token.method_count = 5
		token.methods = ctypes.cast(token_methods, ctypes.POINTER(WlMessage))
		token.event_count = 1
		token.events = ctypes.cast(token_events, ctypes.POINTER(WlMessage))

		activation_methods = self.build_messages(
			("destroy", "", ()),
			("get_activation_token", "n", (address(token),)),
			("activate", "so", (None, surface)),
		)
		activation.name = ACTIVATION_NAME
		activation.version = 1
		activation.method_count = 3
		activation.methods = ctypes.cast(activation_methods, ctypes.POINTER(WlMessage))
		activation.event_count = 0
		activation.events = None

		self.interfaces["token"] = token
		self.interfaces["activation"] = activation
		self.keep_alive.extend((token, activation, token_methods, token_events, activation_methods))

	def build_messages(self, *specs: tuple[str, str, tuple]) -> ctypes.Array:
		"""Build a wl_message array from (name, signature, argument types)"""
		messages = (WlMessage * len(specs))()
		for index, (name, signature, types) in enumerate(specs):
			name_bytes = name.encode()
			signature_bytes = signature.encode()
			type_array = (ctypes.c_void_p * max(len(types), 1))()
			for type_index, interface_pointer in enumerate(types):
				type_array[type_index] = interface_pointer
			messages[index].name = name_bytes
			messages[index].signature = signature_bytes
			messages[index].types = ctypes.cast(type_array, ctypes.POINTER(ctypes.c_void_p))
			self.keep_alive.extend((name_bytes, signature_bytes, type_array))
		return messages

	def collect_globals(self) -> bool:
		"""Read the registry on a queue of our own, so we never take events SDL waits for"""
		lib = self.lib
		self.queue = lib.wl_display_create_queue(ctypes.c_void_p(self.display))
		if not self.queue:
			return False
		wrapper = lib.wl_proxy_create_wrapper(ctypes.c_void_p(self.display))
		if not wrapper:
			return False
		lib.wl_proxy_set_queue(ctypes.c_void_p(wrapper), ctypes.c_void_p(self.queue))
		self.registry = self.marshal(
			wrapper, WL_DISPLAY_GET_REGISTRY, ctypes.byref(self.interfaces["registry"]), 1, 0, None)
		lib.wl_proxy_wrapper_destroy(ctypes.c_void_p(wrapper))
		if not self.registry:
			return False

		def on_global(_data: int, _registry: int, name: int, interface: bytes, version: int) -> None:
			# First seat only
			if interface in (SEAT_NAME, ACTIVATION_NAME) and interface not in self.globals:
				self.globals[interface] = (name, version)

		self.listen(self.registry, (GLOBAL_CALLBACK, on_global), (GLOBAL_REMOVE_CALLBACK, lambda *_a: None))
		lib.wl_display_roundtrip_queue(ctypes.c_void_p(self.display), ctypes.c_void_p(self.queue))
		return True

	def listen(self, proxy: int, *handlers: tuple[type, object]) -> None:
		"""wl_proxy_add_listener with one callback per event, in declaration order"""
		callbacks = [kind(handler) for kind, handler in handlers]
		listener = (ctypes.c_void_p * len(callbacks))(*(ctypes.cast(c, ctypes.c_void_p) for c in callbacks))
		# The listener holds bare addresses; the callbacks must outlive the proxy
		self.keep_alive.extend((listener, *callbacks))
		self.lib.wl_proxy_add_listener(ctypes.c_void_p(proxy), ctypes.cast(listener, ctypes.c_void_p), None)

	def bind(self, name: int, interface: WlInterface, version: int) -> int | None:
		"""wl_registry.bind, as the generated inline would send it"""
		return self.marshal(
			self.registry, WL_REGISTRY_BIND, ctypes.byref(interface), version, 0,
			ctypes.c_uint32(name), ctypes.c_char_p(interface.name), ctypes.c_uint32(version), None)

	def marshal(
		self, proxy: int | None, opcode: int, interface: object, version: int, flags: int,
		*args: object) -> int | None:
		"""wl_proxy_marshal_flags, which every request goes through"""
		if not proxy:
			return None
		return self.lib.wl_proxy_marshal_flags(
			ctypes.c_void_p(proxy),
			ctypes.c_uint32(opcode),
			interface,
			ctypes.c_uint32(version),
			ctypes.c_uint32(flags),
			*args,
		)
