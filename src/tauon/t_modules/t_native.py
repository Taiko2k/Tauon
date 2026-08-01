"""Python facade for Tauon's built-in native SDL bridge."""

from __future__ import annotations

from dataclasses import dataclass

import tauon_native

from tauon.t_modules.t_image import ImageData

SDL_BLENDMODE_NONE = 0
SDL_BLENDMODE_BLEND = 1
SDL_BLENDMODE_ADD = 2
SDL_BLENDFACTOR_ONE = 2
SDL_BLENDFACTOR_ONE_MINUS_SRC_ALPHA = 6
SDL_BLENDOPERATION_ADD = 1
SDL_SCALEMODE_LINEAR = 1
SDL_PIXELFORMAT_ARGB8888 = 372645892
SDL_PIXELFORMAT_XRGB8888 = 370546692
SDL_TEXTUREACCESS_STREAMING = 1
SDL_TEXTUREACCESS_TARGET = 2
SDL_WINDOW_MAXIMIZED = 0x00000080
SDL_WINDOW_BORDERLESS = 0x00000010
SDL_WINDOW_RESIZABLE = 0x00000020
SDL_WINDOW_HIGH_PIXEL_DENSITY = 0x00002000
SDL_WINDOW_POPUP_MENU = 0x00080000
SDL_WINDOW_TRANSPARENT = 0x40000000
SDL_WINDOW_NOT_FOCUSABLE = 0x80000000

# SDL's public integer ABI. Keeping these names here lets Python UI code use
# semantic constants without importing a ctypes binding.
SDLK_A, SDLK_C, SDLK_S, SDLK_V, SDLK_X, SDLK_Z = 97, 99, 115, 118, 120, 122
SDLK_BACKSPACE, SDLK_TAB, SDLK_RETURN, SDLK_DELETE = 8, 9, 13, 127
SDLK_LEFT, SDLK_RIGHT, SDLK_DOWN, SDLK_UP = 1073741904, 1073741903, 1073741905, 1073741906
SDLK_HOME, SDLK_END, SDLK_KP_ENTER, SDLK_RETURN2 = 1073741898, 1073741901, 1073741912, 1073741982
SDLK_LCTRL, SDLK_LSHIFT, SDLK_LALT, SDLK_LGUI = 1073742048, 1073742049, 1073742050, 1073742051
SDLK_RCTRL, SDLK_RSHIFT, SDLK_RALT = 1073742052, 1073742053, 1073742054
SDL_BUTTON_LEFT, SDL_BUTTON_MIDDLE, SDL_BUTTON_RIGHT, SDL_BUTTON_X1, SDL_BUTTON_X2 = 1, 2, 3, 4, 5
SDL_EVENT_QUIT = 256
SDL_EVENT_KEY_DOWN, SDL_EVENT_KEY_UP, SDL_EVENT_TEXT_EDITING, SDL_EVENT_TEXT_INPUT = 768, 769, 770, 771
SDL_EVENT_MOUSE_MOTION, SDL_EVENT_MOUSE_BUTTON_DOWN = 1024, 1025
SDL_EVENT_MOUSE_BUTTON_UP, SDL_EVENT_MOUSE_WHEEL = 1026, 1027
SDL_EVENT_GAMEPAD_AXIS_MOTION, SDL_EVENT_GAMEPAD_BUTTON_DOWN, SDL_EVENT_GAMEPAD_ADDED = 1616, 1617, 1619
SDL_EVENT_FINGER_DOWN, SDL_EVENT_FINGER_UP, SDL_EVENT_FINGER_MOTION, SDL_EVENT_FINGER_CANCELED = 1792, 1793, 1794, 1795
SDL_EVENT_DROP_FILE, SDL_EVENT_DROP_TEXT, SDL_EVENT_DROP_BEGIN = 4096, 4097, 4098
SDL_EVENT_DROP_COMPLETE, SDL_EVENT_DROP_POSITION = 4099, 4100
SDL_EVENT_RENDER_TARGETS_RESET = 8192
SDL_EVENT_WINDOW_FIRST, SDL_EVENT_WINDOW_SHOWN, SDL_EVENT_WINDOW_EXPOSED = 514, 514, 516
SDL_EVENT_WINDOW_RESIZED, SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED = 518, 519
SDL_EVENT_WINDOW_MINIMIZED, SDL_EVENT_WINDOW_MAXIMIZED, SDL_EVENT_WINDOW_RESTORED = 521, 522, 523
SDL_EVENT_WINDOW_MOUSE_ENTER, SDL_EVENT_WINDOW_MOUSE_LEAVE = 524, 525
SDL_EVENT_WINDOW_FOCUS_GAINED, SDL_EVENT_WINDOW_FOCUS_LOST = 526, 527
SDL_EVENT_WINDOW_CLOSE_REQUESTED, SDL_EVENT_WINDOW_DISPLAY_CHANGED, SDL_EVENT_WINDOW_LAST = 528, 531, 538
SDL_GAMEPAD_AXIS_LEFTY, SDL_GAMEPAD_AXIS_RIGHTX, SDL_GAMEPAD_AXIS_RIGHTY, SDL_GAMEPAD_AXIS_LEFT_TRIGGER = 1, 2, 3, 4
SDL_GAMEPAD_BUTTON_SOUTH, SDL_GAMEPAD_BUTTON_EAST, SDL_GAMEPAD_BUTTON_WEST, SDL_GAMEPAD_BUTTON_NORTH = 0, 1, 2, 3
SDL_GAMEPAD_BUTTON_LEFT_SHOULDER, SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER = 9, 10
SDL_GAMEPAD_BUTTON_DPAD_UP, SDL_GAMEPAD_BUTTON_DPAD_DOWN = 11, 12
SDL_GAMEPAD_BUTTON_DPAD_LEFT, SDL_GAMEPAD_BUTTON_DPAD_RIGHT = 13, 14
SDL_SCANCODE_A, SDL_SCANCODE_C, SDL_SCANCODE_S = 4, 6, 22
SDL_SCANCODE_V, SDL_SCANCODE_X, SDL_SCANCODE_Z = 25, 27, 29
SDL_BLENDFACTOR_ZERO, SDL_BLENDFACTOR_SRC_COLOR, SDL_BLENDFACTOR_ONE_MINUS_SRC_COLOR = 1, 3, 4
SDL_BLENDFACTOR_SRC_ALPHA = 5
SDL_BLENDMODE_BLEND_PREMULTIPLIED = 16
SDL_FLIP_VERTICAL = 2
SDL_PIXELFORMAT_RGBA32, SDL_PIXELFORMAT_RGBA8888 = 376840196, 373694468
SDL_INIT_GAMEPAD = 8192
SDL_PROGRESS_STATE_NONE, SDL_PROGRESS_STATE_NORMAL, SDL_PROGRESS_STATE_PAUSED = 0, 2, 3
SDL_SYSTEM_CURSOR_DEFAULT, SDL_SYSTEM_CURSOR_TEXT = 0, 1
SDL_SYSTEM_CURSOR_NWSE_RESIZE, SDL_SYSTEM_CURSOR_EW_RESIZE, SDL_SYSTEM_CURSOR_NS_RESIZE = 5, 7, 8
SDL_SYSTEM_CURSOR_POINTER = 11
SDL_HITTEST_NORMAL, SDL_HITTEST_DRAGGABLE = 0, 1
SDL_HITTEST_RESIZE_TOPLEFT, SDL_HITTEST_RESIZE_TOP, SDL_HITTEST_RESIZE_TOPRIGHT = 2, 3, 4
SDL_HITTEST_RESIZE_RIGHT, SDL_HITTEST_RESIZE_BOTTOMRIGHT = 5, 6
SDL_HITTEST_RESIZE_BOTTOM, SDL_HITTEST_RESIZE_BOTTOMLEFT, SDL_HITTEST_RESIZE_LEFT = 7, 8, 9
SDL_GL_CONTEXT_MAJOR_VERSION, SDL_GL_CONTEXT_MINOR_VERSION = 17, 18
SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE = 20, 1
SDL_TRAYENTRY_BUTTON = 1
SDL_WINDOW_INPUT_FOCUS = 0x200
SDL_PROP_WINDOW_WIN32_HWND_POINTER = "SDL.window.win32.hwnd"
SDL_PROP_TEXTURE_CREATE_OPENGL_TEXTURE_NUMBER = "opengl_texture"
SDL_PROP_TEXTURE_CREATE_WIDTH_NUMBER = "width"
SDL_PROP_TEXTURE_CREATE_HEIGHT_NUMBER = "height"
SDL_PROP_TEXTURE_CREATE_ACCESS_NUMBER = "access"
SDL_version = 300



@dataclass(slots=True)
class FRect:
	x: float = 0.0
	y: float = 0.0
	w: float = 0.0
	h: float = 0.0


@dataclass(slots=True)
class Rect:
	x: int = 0
	y: int = 0
	w: int = 0
	h: int = 0


class _EventData:
	__slots__ = ("_fields",)

	_DEFAULTS = {
		"axis": 0, "button": 0, "data": b"", "data1": 0, "data2": 0,
		"dy": 0.0, "finger_id": 0, "integer_y": 0, "key": 0,
		"scancode": 0, "text": b"", "value": 0, "which": 0,
		"window_id": 0, "x": 0.0, "y": 0.0,
	}

	def __init__(self, fields: dict[str, object]) -> None:
		self._fields = fields

	@property
	def windowID(self) -> int:
		return int(self._fields.get("window_id", 0))

	@property
	def fingerID(self) -> int:
		return int(self._fields.get("finger_id", 0))

	def __getattr__(self, name: str):
		if name in self._DEFAULTS:
			return self._fields.get(name, self._DEFAULTS[name])
		raise AttributeError(name)


class Event:
	"""Lazy view of one native SDL event.

	The legacy UI still uses SDL union-style access such as ``event.key.key``.
	Returning this same view for each union member preserves that spelling
	without constructing a tree of temporary namespace objects for every event.
	"""

	__slots__ = ("_fields", "_data")

	def __init__(self, fields: dict[str, object]) -> None:
		self._fields = fields
		self._data = _EventData(fields)

	@property
	def type(self) -> int:
		return int(self._fields["type"])

	def __getattr__(self, name: str):
		if name in {"gdevice", "gaxis", "gbutton", "drop", "edit", "text", "motion",
				"button", "key", "wheel", "tfinger", "window"}:
			return self._data
		raise AttributeError(name)


def poll_events():
	for fields in tauon_native.poll_events():
		yield Event(fields)


LP_SDL_Cursor = object
LP_SDL_Renderer = object
LP_SDL_Surface = ImageData
LP_SDL_Texture = object
LP_SDL_Tray = object
LP_SDL_Window = object
SDL_Scancode = int


def create_texture(renderer, pixel_format: int, access: int, width: int, height: int) -> int:
	return tauon_native.create_texture(renderer, pixel_format, access, width, height)


def create_texture_from_rgba(renderer, width: int, height: int, pixels) -> int:
	return tauon_native.create_texture_from_rgba(renderer, width, height, pixels)


def create_texture_from_surface(renderer, surface: ImageData) -> int:
	return create_texture_from_rgba(renderer, surface.width, surface.height, surface.pixels)


def create_color_cursor_from_surface(surface: ImageData, hot_x: int, hot_y: int) -> int:
	return create_color_cursor(surface.width, surface.height, surface.pixels, hot_x, hot_y)


destroy_texture = tauon_native.destroy_texture
get_render_target = tauon_native.get_render_target


def get_renderer_name(renderer) -> str:
	del renderer
	return tauon_native.renderer_name()


get_error = tauon_native.get_error
set_render_target = tauon_native.set_render_target
set_render_draw_blend_mode = tauon_native.set_render_draw_blend_mode
set_render_draw_color = tauon_native.set_render_draw_color
render_clear = tauon_native.render_clear
render_fill_rect = tauon_native.render_fill_rect
render_texture = tauon_native.render_texture
set_texture_blend_mode = tauon_native.set_texture_blend_mode
set_texture_scale_mode = tauon_native.set_texture_scale_mode


set_texture_alpha_mod = tauon_native.set_texture_alpha_mod
set_texture_color_mod = tauon_native.set_texture_color_mod
flush_renderer = tauon_native.flush_renderer


def render_texture_rotated(renderer, texture, source, destination, angle: float, center, flip: int) -> None:
	center_tuple = None if center is None else (center.x, center.y)
	tauon_native.render_texture_rotated(
		renderer, texture, source, destination, angle, center_tuple, flip
	)


clear_error = tauon_native.clear_error
gl_get_current_context = tauon_native.gl_get_current_context
gl_set_attribute = tauon_native.gl_set_attribute
gl_create_context = tauon_native.gl_create_context
gl_make_current = tauon_native.gl_make_current


def create_properties() -> dict[str, int]:
	return {}


def set_number_property(properties: dict[str, int], name: str, value: int) -> None:
	properties[name] = value


def create_texture_with_properties(renderer, properties: dict[str, int]) -> int:
	return tauon_native.create_texture_from_opengl(
		renderer,
		properties[SDL_PROP_TEXTURE_CREATE_OPENGL_TEXTURE_NUMBER],
		properties[SDL_PROP_TEXTURE_CREATE_WIDTH_NUMBER],
		properties[SDL_PROP_TEXTURE_CREATE_HEIGHT_NUMBER],
		properties[SDL_PROP_TEXTURE_CREATE_ACCESS_NUMBER],
	)


update_texture = tauon_native.update_texture
set_render_clip_rect = tauon_native.set_render_clip_rect
get_window_flags = tauon_native.get_window_flags
maximize_window = tauon_native.maximize_window
minimize_window = tauon_native.minimize_window
restore_window = tauon_native.restore_window
render_geometry = tauon_native.render_geometry
create_popup_window = tauon_native.create_popup_window


create_window = tauon_native.create_window
create_renderer = tauon_native.create_renderer
destroy_renderer = tauon_native.destroy_renderer
destroy_window = tauon_native.destroy_window
get_window_id = tauon_native.get_window_id


def get_window_size(window) -> tuple[int, int]:
	return tauon_native.get_window_size(window, False)


def get_window_size_in_pixels(window) -> tuple[int, int]:
	return tauon_native.get_window_size(window, True)


set_window_size = tauon_native.set_window_size
set_window_position = tauon_native.set_window_position
set_window_mouse_grab = tauon_native.set_window_mouse_grab
capture_mouse = tauon_native.capture_mouse
show_window = tauon_native.show_window
hide_window = tauon_native.hide_window
raise_window = tauon_native.raise_window
render_present = tauon_native.render_present
get_render_scale = tauon_native.get_render_scale
set_render_scale = tauon_native.set_render_scale
set_window_minimum_size = tauon_native.set_window_minimum_size
set_window_resizable = tauon_native.set_window_resizable
set_window_bordered = tauon_native.set_window_bordered
set_window_opacity = tauon_native.set_window_opacity
set_window_always_on_top = tauon_native.set_window_always_on_top


set_window_title = tauon_native.set_window_title
set_window_fullscreen = tauon_native.set_window_fullscreen
sync_window = tauon_native.sync_window
get_window_position = tauon_native.get_window_position


def get_mouse_state() -> tuple[int, float, float]:
	return tauon_native.get_mouse_state(False)


def get_global_mouse_state() -> tuple[int, float, float]:
	return tauon_native.get_mouse_state(True)


create_system_cursor = tauon_native.create_system_cursor
set_cursor = tauon_native.set_cursor
create_color_cursor = tauon_native.create_color_cursor
set_window_hit_test = tauon_native.set_window_hit_test


def set_window_icon(window, icon: ImageData) -> None:
	tauon_native.set_window_icon(window, icon.width, icon.height, icon.pixels)


set_window_progress_state = tauon_native.set_window_progress_state
set_window_progress_value = tauon_native.set_window_progress_value
start_text_input = tauon_native.start_text_input
stop_text_input = tauon_native.stop_text_input
set_text_input_area = tauon_native.set_text_input_area
get_display_refresh_rate = tauon_native.get_display_refresh_rate


def create_tray(icon: ImageData, tooltip) -> int:
	return tauon_native.create_tray(icon.width, icon.height, icon.pixels, _text(tooltip))


def set_tray_icon(tray, icon: ImageData) -> None:
	tauon_native.set_tray_icon(tray, icon.width, icon.height, icon.pixels)


def set_tray_tooltip(tray, tooltip) -> None:
	tauon_native.set_tray_tooltip(tray, _text(tooltip))


create_tray_menu = tauon_native.create_tray_menu


def insert_tray_entry(menu, position: int, label, flags: int) -> int:
	return tauon_native.insert_tray_entry(menu, position, None if label is None else _text(label), flags)


set_tray_entry_callback = tauon_native.set_tray_entry_callback
destroy_tray = tauon_native.destroy_tray


def _text(value) -> str:
	return value.decode("utf-8", errors="surrogateescape") if isinstance(value, bytes) else value


def get_key_from_name(name) -> int:
	return tauon_native.key_from_name(_text(name))


def get_scancode_from_name(name) -> int:
	return tauon_native.scancode_from_name(_text(name))


init_subsystem = tauon_native.init_subsystem
pump_events = tauon_native.pump_events
is_gamepad = tauon_native.is_gamepad
open_gamepad = tauon_native.open_gamepad


def get_gamepad_name(identifier: int) -> bytes | None:
	name = tauon_native.gamepad_name(identifier)
	return name.encode("utf-8") if name is not None else None


get_version = tauon_native.sdl_version


def get_current_video_driver() -> bytes | None:
	driver = tauon_native.video_driver()
	return driver.encode("utf-8") if driver is not None else None


def set_clipboard_text(text) -> None:
	tauon_native.set_clipboard_text(_text(text))


def get_clipboard_text() -> bytes:
	return tauon_native.get_clipboard_text().encode("utf-8", errors="surrogateescape")


has_clipboard_text = tauon_native.has_clipboard_text
render_line = tauon_native.render_line
get_texture_size = tauon_native.get_texture_size


def create_texture_from_cairo(renderer, width: int, height: int, pitch: int, pixels, alpha: bool, colour_key=None):
	return tauon_native.create_texture_from_cairo(
		renderer, width, height, pitch, pixels, alpha, colour_key
	)


def read_render_pixels(renderer, rectangle, alpha: bool) -> tuple[bytes, int]:
	return tauon_native.read_render_pixels(renderer, rectangle, alpha)


def compose_custom_blend_mode(
	source_colour: int,
	destination_colour: int,
	colour_operation: int,
	source_alpha: int,
	destination_alpha: int,
	alpha_operation: int,
) -> int:
	return tauon_native.compose_blend_mode(
		source_colour, destination_colour, colour_operation, source_alpha, destination_alpha, alpha_operation
	)
