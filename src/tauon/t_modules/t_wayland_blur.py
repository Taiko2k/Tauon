"""Background blur behind the window on Wayland

Implements the ``ext-background-effect-v1`` staging protocol so compositors
blur whatever is behind Tauon while a glass (window transparency) style is
selected. Supported by KWin 6.7+, Hyprland 0.56+, niri 26.04+ and Mutter 51+;
Hyprland in particular no longer blurs translucent windows unless the client
asks for it through this protocol.

The protocol is tiny — a manager global that hands out a per-surface effect
object, and one ``set_blur_region`` request on it — so rather than adding a
wayland-scanner build step it is marshalled here directly against
libwayland-client, exactly as the generated code would. Anything missing
(non-Wayland session, no library, compositor without the global) simply
disables the feature.

The blur region is double-buffered surface state applied on the next
``wl_surface.commit``, and SDL owns this surface's commit cycle, so nothing
here commits: `sync` is called just before ``SDL_RenderPresent`` and SDL's
own commit publishes the region.
"""

# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

from __future__ import annotations

import ctypes
import logging
import math
from typing import TYPE_CHECKING

import sdl3

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Tauon

# wl_proxy_marshal_flags: destroy the proxy after sending the request
WL_MARSHAL_FLAG_DESTROY = 1

# Request opcodes, in interface declaration order
WL_DISPLAY_GET_REGISTRY = 1
WL_REGISTRY_BIND = 0
WL_COMPOSITOR_CREATE_REGION = 1
WL_REGION_DESTROY = 0
WL_REGION_ADD = 1
EXT_BACKGROUND_EFFECT_MANAGER_DESTROY = 0
EXT_BACKGROUND_EFFECT_MANAGER_GET_BACKGROUND_EFFECT = 1
EXT_BACKGROUND_EFFECT_SURFACE_DESTROY = 0
EXT_BACKGROUND_EFFECT_SURFACE_SET_BLUR_REGION = 1

# ext_background_effect_manager_v1.capability
CAPABILITY_BLUR = 1

MANAGER_NAME = b"ext_background_effect_manager_v1"
EFFECT_NAME = b"ext_background_effect_surface_v1"
COMPOSITOR_NAME = b"wl_compositor"
# wl_compositor version we can make use of (create_region exists since 1)
COMPOSITOR_WANT_VERSION = 4


class WlMessage(ctypes.Structure):
	_fields_ = (
		("name", ctypes.c_char_p),
		("signature", ctypes.c_char_p),
		("types", ctypes.POINTER(ctypes.c_void_p)),
	)


class WlInterface(ctypes.Structure):
	_fields_ = (
		("name", ctypes.c_char_p),
		("version", ctypes.c_int),
		("method_count", ctypes.c_int),
		("methods", ctypes.POINTER(WlMessage)),
		("event_count", ctypes.c_int),
		("events", ctypes.POINTER(WlMessage)),
	)


# Registry listener callbacks
GLOBAL_CALLBACK = ctypes.CFUNCTYPE(
	None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32)
GLOBAL_REMOVE_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32)
# ext_background_effect_manager_v1.capabilities
CAPABILITIES_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32)


def region_rects(width: int, height: int, radius: int) -> list[tuple[int, int, int, int]]:
	"""The rects making up the blur region, in surface-local coordinates

	The region tracks the window's real size: the protocol says an oversized
	rect is clipped to the surface, but Hyprland 0.56 clips it to the size the
	surface had when the effect object was made, leaving part of a since
	resized window unblurred. With rounded corners the region has to follow
	the window's shape anyway, or blur shows through the corners Tauon cut
	away, so the arcs are approximated a row at a time.
	"""
	if width <= 0 or height <= 0:
		return []
	if radius <= 0:
		return [(0, 0, width, height)]
	radius = min(radius, width // 2, height // 2)
	if radius <= 0:
		return [(0, 0, width, height)]

	rects = []
	middle = height - radius * 2
	if middle > 0:
		rects.append((0, radius, width, middle))
	for row in range(radius):
		# Horizontal inset of the corner arc at this row, sampled at the row's
		# centre; the same inset serves the two corners on that edge
		distance = radius - row - 0.5
		inset = math.ceil(radius - math.sqrt(max(radius * radius - distance * distance, 0.0)))
		span = width - inset * 2
		if span <= 0:
			continue
		rects.append((inset, row, span, 1))
		rects.append((inset, height - row - 1, span, 1))
	return rects


class WaylandBlur:
	"""Asks the compositor to blur behind the window while a glass style is on"""

	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.prefs = tauon.prefs
		self.lib: ctypes.CDLL | None = None

		self.display: int | None = None
		self.queue: int | None = None
		self.registry: int | None = None
		self.compositor: int | None = None
		self.compositor_version = 1
		self.manager: int | None = None
		self.manager_version = 1
		self.effect: int | None = None
		self.surface: int | None = None
		self.capabilities = 0

		self.manager_interface: WlInterface | None = None
		self.effect_interface: WlInterface | None = None
		self.compositor_interface: WlInterface | None = None
		self.region_interface: WlInterface | None = None
		self.registry_interface: WlInterface | None = None
		# wl_interface/wl_message/callback objects the C side holds pointers
		# into; they must outlive every proxy that references them
		self.keep_alive: list = []

		self.globals: dict[bytes, tuple[int, int]] = {}
		self.applied: tuple[int, int, int] | None = None
		self.attached = False
		self.unavailable = False

	# --- Public interface

	def sync(self) -> None:
		"""Apply the wanted blur state; call once per frame, before present

		The region is double-buffered surface state, so what is set here is
		published by the commit inside the present that follows.
		"""
		if self.unavailable:
			return
		if not self.attached and not self.attach():
			return
		if not self.check_surface():
			return
		# Events for our queue are read by SDL's own dispatch and left pending;
		# draining is non-blocking and keeps the capabilities up to date
		self.lib.wl_display_dispatch_queue_pending(ctypes.c_void_p(self.display), ctypes.c_void_p(self.queue))

		wanted = self.wanted_shape()
		if wanted == self.applied:
			return
		self.apply(wanted)
		self.applied = wanted

	def shutdown(self) -> None:
		"""Drop the protocol objects (the window is going away)"""
		if self.lib is None:
			return
		if self.effect is not None:
			self.marshal(self.effect, EXT_BACKGROUND_EFFECT_SURFACE_DESTROY, None, 1, WL_MARSHAL_FLAG_DESTROY)
			self.effect = None
		if self.manager is not None:
			self.marshal(
				self.manager, EXT_BACKGROUND_EFFECT_MANAGER_DESTROY, None, self.manager_version,
				WL_MARSHAL_FLAG_DESTROY)
			self.manager = None
		self.attached = False
		self.unavailable = True

	# --- Wanted state

	def wanted_shape(self) -> tuple[int, int, int] | None:
		"""``(width, height, radius)`` for the blur region, or None for no blur

		Surface-local coordinates are logical units, so this works from the
		window's logical size; a resize changes the shape and re-sends it.
		"""
		if not self.prefs.transparent_mode or not self.capabilities & CAPABILITY_BLUR:
			return None
		radius = self.tauon.corner_round_radius()
		return (
			self.tauon.logical_size[0],
			self.tauon.logical_size[1],
			# corner_round_radius is in pixels, the surface is in logical units
			max(1, self.tauon.pixel_to_logical(radius)) if radius else 0,
		)

	def apply(self, shape: tuple[int, int, int] | None) -> None:
		if self.effect is None:
			return
		if shape is None:
			# A null region turns the effect off
			self.marshal(self.effect, EXT_BACKGROUND_EFFECT_SURFACE_SET_BLUR_REGION, None, 1, 0, None)
			return

		region = self.create_region(*shape)
		if region is None:
			return
		self.marshal(
			self.effect, EXT_BACKGROUND_EFFECT_SURFACE_SET_BLUR_REGION, None, 1, 0, ctypes.c_void_p(region))
		# set_blur_region copies the region, so it can go straight away
		self.marshal(region, WL_REGION_DESTROY, None, self.compositor_version, WL_MARSHAL_FLAG_DESTROY)

	def create_region(self, width: int, height: int, radius: int) -> int | None:
		rects = region_rects(width, height, radius)
		if not rects:
			return None
		region = self.marshal(
			self.compositor, WL_COMPOSITOR_CREATE_REGION, ctypes.byref(self.region_interface),
			self.compositor_version, 0, None)
		if not region:
			return None
		for x, y, w, h in rects:
			self.marshal(
				region, WL_REGION_ADD, None, self.compositor_version, 0,
				ctypes.c_int32(x), ctypes.c_int32(y), ctypes.c_int32(w), ctypes.c_int32(h))
		return region

	# --- Setup

	def attach(self) -> bool:
		"""Connect to the compositor's background-effect global

		Returns False (and disables further attempts) when anything needed is
		missing; blur is entirely optional.
		"""
		try:
			# Ask SDL what it actually chose rather than trusting tauon.wayland,
			# which only reflects the SDL_VIDEODRIVER environment variable
			if sdl3.SDL_GetCurrentVideoDriver() != b"wayland":
				self.unavailable = True
				return False
			if not self.load_library():
				return False

			props = sdl3.SDL_GetWindowProperties(self.tauon.t_window)
			display = sdl3.SDL_GetPointerProperty(props, sdl3.SDL_PROP_WINDOW_WAYLAND_DISPLAY_POINTER, None)
			surface = sdl3.SDL_GetPointerProperty(props, sdl3.SDL_PROP_WINDOW_WAYLAND_SURFACE_POINTER, None)
			if not display or not surface:
				# The window may not be shown yet; try again next frame
				return False

			if not self.collect_globals(display):
				return False
			if MANAGER_NAME not in self.globals or COMPOSITOR_NAME not in self.globals:
				logging.info("Compositor has no ext-background-effect-v1 support, window blur unavailable")
				self.unavailable = True
				return False

			self.bind_globals()
			self.lib.wl_display_roundtrip_queue(ctypes.c_void_p(display), ctypes.c_void_p(self.queue))
			if not self.capabilities & CAPABILITY_BLUR:
				logging.info("Compositor does not offer background blur, window blur unavailable")
				self.unavailable = True
				return False

			self.effect = self.create_effect(surface)
			if self.effect is None:
				self.unavailable = True
				return False

			self.display = display
			self.surface = surface
			self.attached = True
			self.applied = None
			logging.info("Using ext-background-effect-v1 for window blur")
			return True

		except Exception:
			logging.exception("Failed to set up Wayland background blur")
			self.unavailable = True
			return False

	def create_effect(self, surface: int) -> int | None:
		"""ext_background_effect_manager_v1.get_background_effect"""
		return self.marshal(
			self.manager, EXT_BACKGROUND_EFFECT_MANAGER_GET_BACKGROUND_EFFECT,
			ctypes.byref(self.effect_interface), self.manager_version, 0, None, ctypes.c_void_p(surface)) or None

	def check_surface(self) -> bool:
		"""Make a new effect object if SDL has given the window a new wl_surface"""
		props = sdl3.SDL_GetWindowProperties(self.tauon.t_window)
		surface = sdl3.SDL_GetPointerProperty(props, sdl3.SDL_PROP_WINDOW_WAYLAND_SURFACE_POINTER, None)
		if surface == self.surface:
			return True
		if not surface:
			return False
		if self.effect is not None:
			self.marshal(self.effect, EXT_BACKGROUND_EFFECT_SURFACE_DESTROY, None, 1, WL_MARSHAL_FLAG_DESTROY)
		self.effect = self.create_effect(surface)
		self.surface = surface
		self.applied = None
		return self.effect is not None

	def load_library(self) -> bool:
		if self.lib is not None:
			return True
		try:
			lib = ctypes.CDLL("libwayland-client.so.0")
		except OSError:
			logging.warning("Could not load libwayland-client, window blur unavailable")
			self.unavailable = True
			return False

		# Only the return types matter; the arguments are passed as explicit
		# ctypes values (wl_proxy_marshal_flags is variadic)
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
		"""Hand-build the wl_interface data wayland-scanner would generate"""
		lib = self.lib
		# Interfaces libwayland already knows about
		self.registry_interface = WlInterface.in_dll(lib, "wl_registry_interface")
		self.compositor_interface = WlInterface.in_dll(lib, "wl_compositor_interface")
		self.region_interface = WlInterface.in_dll(lib, "wl_region_interface")
		surface_interface = WlInterface.in_dll(lib, "wl_surface_interface")
		self.keep_alive.extend((
			self.registry_interface, self.compositor_interface, self.region_interface, surface_interface))

		effect = WlInterface()
		manager = WlInterface()
		effect_pointer = ctypes.cast(ctypes.pointer(effect), ctypes.c_void_p)
		surface_pointer = ctypes.cast(ctypes.pointer(surface_interface), ctypes.c_void_p)
		region_pointer = ctypes.cast(ctypes.pointer(self.region_interface), ctypes.c_void_p)

		effect_methods = self.build_messages(
			("destroy", "", ()),
			("set_blur_region", "?o", (region_pointer,)),
		)
		effect.name = EFFECT_NAME
		effect.version = 1
		effect.method_count = 2
		effect.methods = ctypes.cast(effect_methods, ctypes.POINTER(WlMessage))
		effect.event_count = 0
		effect.events = None

		manager_methods = self.build_messages(
			("destroy", "", ()),
			("get_background_effect", "no", (effect_pointer, surface_pointer)),
		)
		manager_events = self.build_messages(
			("capabilities", "u", (None,)),
		)
		manager.name = MANAGER_NAME
		manager.version = 1
		manager.method_count = 2
		manager.methods = ctypes.cast(manager_methods, ctypes.POINTER(WlMessage))
		manager.event_count = 1
		manager.events = ctypes.cast(manager_events, ctypes.POINTER(WlMessage))

		self.effect_interface = effect
		self.manager_interface = manager
		self.keep_alive.extend((effect, manager, effect_methods, manager_methods, manager_events))

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

	def collect_globals(self, display: int) -> bool:
		"""Read the registry on a queue of our own

		SDL dispatches this display's default queue, so the registry is put on
		a private queue (via a proxy wrapper) to avoid taking events SDL is
		waiting for.
		"""
		lib = self.lib
		self.queue = lib.wl_display_create_queue(ctypes.c_void_p(display))
		if not self.queue:
			self.unavailable = True
			return False

		wrapper = lib.wl_proxy_create_wrapper(ctypes.c_void_p(display))
		if not wrapper:
			self.unavailable = True
			return False
		lib.wl_proxy_set_queue(ctypes.c_void_p(wrapper), ctypes.c_void_p(self.queue))
		self.registry = self.marshal(
			wrapper, WL_DISPLAY_GET_REGISTRY, ctypes.byref(self.registry_interface), 1, 0, None)
		lib.wl_proxy_wrapper_destroy(ctypes.c_void_p(wrapper))
		if not self.registry:
			self.unavailable = True
			return False

		def on_global(_data: int, _registry: int, name: int, interface: bytes, version: int) -> None:
			if interface in (MANAGER_NAME, COMPOSITOR_NAME):
				self.globals[interface] = (name, version)

		def on_global_remove(_data: int, _registry: int, _name: int) -> None:
			pass

		global_callback = GLOBAL_CALLBACK(on_global)
		global_remove_callback = GLOBAL_REMOVE_CALLBACK(on_global_remove)
		listener = (ctypes.c_void_p * 2)(
			ctypes.cast(global_callback, ctypes.c_void_p),
			ctypes.cast(global_remove_callback, ctypes.c_void_p),
		)
		# The listener holds bare addresses, so the callback objects have to
		# outlive the proxy they are attached to
		self.keep_alive.extend((listener, global_callback, global_remove_callback))
		lib.wl_proxy_add_listener(ctypes.c_void_p(self.registry), ctypes.cast(listener, ctypes.c_void_p), None)
		lib.wl_display_roundtrip_queue(ctypes.c_void_p(display), ctypes.c_void_p(self.queue))
		return True

	def bind_globals(self) -> None:
		name, version = self.globals[COMPOSITOR_NAME]
		self.compositor_version = min(version, COMPOSITOR_WANT_VERSION)
		self.compositor = self.bind(name, self.compositor_interface, self.compositor_version)

		name, version = self.globals[MANAGER_NAME]
		self.manager_version = min(version, 1)
		self.manager = self.bind(name, self.manager_interface, self.manager_version)
		if not self.manager:
			return

		def on_capabilities(_data: int, _manager: int, flags: int) -> None:
			self.capabilities = flags

		capabilities_callback = CAPABILITIES_CALLBACK(on_capabilities)
		listener = (ctypes.c_void_p * 1)(ctypes.cast(capabilities_callback, ctypes.c_void_p))
		self.keep_alive.extend((listener, capabilities_callback))
		self.lib.wl_proxy_add_listener(
			ctypes.c_void_p(self.manager), ctypes.cast(listener, ctypes.c_void_p), None)

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
