"""Python facade for Tauon's built-in native SDL bridge."""

from __future__ import annotations

import ctypes
import io
import logging
from pathlib import Path
from ctypes import c_float, c_int, c_void_p
from dataclasses import dataclass

import tauon_native
from PIL import Image

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



class SDL_FRect(ctypes.Structure):
	_fields_ = (("x", c_float), ("y", c_float), ("w", c_float), ("h", c_float))


class SDL_Rect(ctypes.Structure):
	_fields_ = (("x", c_int), ("y", c_int), ("w", c_int), ("h", c_int))


@dataclass(slots=True)
class ImageData:
	width: int
	height: int
	pixels: bytes


LP_SDL_Cursor = int
LP_SDL_Renderer = int
LP_SDL_Surface = ImageData
LP_SDL_Texture = int
LP_SDL_Tray = int
LP_SDL_Window = int
SDL_Scancode = int


def _handle(value) -> int | None:
	if value is None:
		return None
	if isinstance(value, int):
		return value
	return ctypes.cast(value, c_void_p).value


def _rectangle(value) -> tuple[float, float, float, float] | None:
	if value is None:
		return None
	if not hasattr(value, "x") and hasattr(value, "_obj"):
		value = value._obj
	return value.x, value.y, value.w, value.h


def _integer_rectangle(value) -> tuple[int, int, int, int] | None:
	rectangle = _rectangle(value)
	if rectangle is None:
		return None
	return tuple(int(component) for component in rectangle)


def SDL_CreateTexture(renderer, pixel_format: int, access: int, width: int, height: int) -> int:
	return tauon_native.create_texture(_handle(renderer), pixel_format, access, width, height)


def create_texture_from_rgba(renderer, width: int, height: int, pixels) -> int:
	return tauon_native.create_texture_from_rgba(_handle(renderer), width, height, pixels)


def SDL_CreateTextureFromSurface(renderer, surface: ImageData) -> int:
	return create_texture_from_rgba(renderer, surface.width, surface.height, surface.pixels)


def SDL_DestroySurface(surface: ImageData | None) -> None:
	del surface


def SDL_CreateSurfaceFrom(width: int, height: int, _format: int, pixels, pitch: int) -> ImageData:
	del _format
	if isinstance(pixels, (bytes, bytearray, memoryview)):
		data = bytes(pixels)
	else:
		data = ctypes.string_at(pixels, pitch * height)
	if pitch != width * 4:
		data = b"".join(data[row * pitch:row * pitch + width * 4] for row in range(height))
	return ImageData(width, height, data)


def SDL_CreateColorCursor(surface: ImageData, hot_x: int, hot_y: int) -> int:
	return create_color_cursor(surface.width, surface.height, surface.pixels, hot_x, hot_y)


def SDL_DestroyTexture(texture) -> None:
	tauon_native.destroy_texture(_handle(texture))


def SDL_GetRenderTarget(renderer) -> int | None:
	return tauon_native.get_render_target(_handle(renderer))


def SDL_GetRendererName(renderer) -> str:
	del renderer
	return tauon_native.renderer_name()


def SDL_GetError() -> str:
	return "native SDL operation failed"


def SDL_SetRenderTarget(renderer, texture) -> None:
	tauon_native.set_render_target(_handle(renderer), _handle(texture))


def SDL_SetRenderDrawBlendMode(renderer, mode: int) -> None:
	tauon_native.set_render_draw_blend_mode(_handle(renderer), mode)


def SDL_SetRenderDrawColor(renderer, red: int, green: int, blue: int, alpha: int) -> None:
	tauon_native.set_render_draw_color(_handle(renderer), red, green, blue, alpha)


def SDL_RenderClear(renderer) -> None:
	tauon_native.render_clear(_handle(renderer))


def SDL_RenderFillRect(renderer, rectangle) -> None:
	tauon_native.render_fill_rect(_handle(renderer), _rectangle(rectangle))


def SDL_RenderTexture(renderer, texture, source, destination) -> None:
	tauon_native.render_texture(_handle(renderer), _handle(texture), _rectangle(source), _rectangle(destination))


def SDL_SetTextureBlendMode(texture, mode: int) -> bool:
	tauon_native.set_texture_blend_mode(_handle(texture), mode)
	return True


def SDL_SetTextureScaleMode(texture, mode: int) -> None:
	tauon_native.set_texture_scale_mode(_handle(texture), mode)


def SDL_SetTextureAlphaMod(texture, alpha: int) -> None:
	if hasattr(alpha, "value"):
		alpha = alpha.value
	tauon_native.set_texture_alpha_mod(_handle(texture), alpha)


def SDL_SetTextureColorMod(texture, red: int, green: int, blue: int) -> None:
	tauon_native.set_texture_color_mod(_handle(texture), red, green, blue)


def SDL_FlushRenderer(renderer) -> None:
	tauon_native.flush_renderer(_handle(renderer))


def SDL_RenderTextureRotated(renderer, texture, source, destination, angle: float, center, flip: int) -> None:
	center_tuple = None if center is None else (center.x, center.y)
	tauon_native.render_texture_rotated(
		_handle(renderer), _handle(texture), _rectangle(source), _rectangle(destination), angle, center_tuple, flip
	)


def SDL_ClearError() -> None:
	return None


def SDL_GL_GetCurrentContext():
	return tauon_native.gl_get_current_context()


def SDL_GL_SetAttribute(attribute: int, value: int) -> None:
	tauon_native.gl_set_attribute(attribute, value)


def SDL_GL_CreateContext(window):
	return tauon_native.gl_create_context(_handle(window))


def SDL_GL_MakeCurrent(window, context) -> None:
	tauon_native.gl_make_current(_handle(window), _handle(context))


def SDL_CreateProperties() -> dict[str, int]:
	return {}


def SDL_SetNumberProperty(properties: dict[str, int], name: str, value: int) -> None:
	properties[name] = value


def SDL_CreateTextureWithProperties(renderer, properties: dict[str, int]) -> int:
	return tauon_native.create_texture_from_opengl(
		_handle(renderer),
		properties[SDL_PROP_TEXTURE_CREATE_OPENGL_TEXTURE_NUMBER],
		properties[SDL_PROP_TEXTURE_CREATE_WIDTH_NUMBER],
		properties[SDL_PROP_TEXTURE_CREATE_HEIGHT_NUMBER],
		properties[SDL_PROP_TEXTURE_CREATE_ACCESS_NUMBER],
	)


def IMG_Load(path) -> ImageData:
	if hasattr(path, "value"):
		path = path.value
	if isinstance(path, bytes):
		path = path.decode("utf-8")
	path = Path(path)
	if not path.is_file() and path.parent.name == "scaled-icons":
		unscaled = Path(__file__).resolve().parent.parent / "assets" / path.name
		if unscaled.is_file():
			path = unscaled
	if not path.is_file():
		logging.warning("Native image loader could not find %s; using a transparent placeholder", path)
		return ImageData(1, 1, bytes(4))
	if path.suffix.lower() == ".svg":
		import cairo
		from gi import require_version

		require_version("Rsvg", "2.0")
		from gi.repository import Rsvg

		svg = Rsvg.Handle.new_from_file(str(path))
		width = max(1, round(svg.props.width))
		height = max(1, round(svg.props.height))
		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
		context = cairo.Context(surface)
		viewport = Rsvg.Rectangle()
		viewport.x, viewport.y, viewport.width, viewport.height = 0, 0, width, height
		svg.render_document(context, viewport)
		encoded = io.BytesIO()
		surface.write_to_png(encoded)
		encoded.seek(0)
		with Image.open(encoded) as image:
			rgba = image.convert("RGBA")
			return ImageData(rgba.width, rgba.height, rgba.tobytes())
	with Image.open(path) as image:
		if image.mode != "RGBA":
			image = image.convert("RGBA")
		return ImageData(image.width, image.height, image.tobytes())


def IMG_Quit() -> None:
	pass


def SDL_UpdateTexture(texture, rectangle, pixels, pitch: int) -> None:
	tauon_native.update_texture(_handle(texture), _integer_rectangle(rectangle), pixels, pitch)


def SDL_SetRenderClipRect(renderer, rectangle) -> None:
	tauon_native.set_render_clip_rect(_handle(renderer), _integer_rectangle(rectangle))


def SDL_GetWindowFlags(window) -> int:
	return tauon_native.get_window_flags(_handle(window))


def SDL_MaximizeWindow(window) -> None:
	tauon_native.maximize_window(_handle(window))


def SDL_MinimizeWindow(window) -> None:
	tauon_native.minimize_window(_handle(window))


def SDL_RestoreWindow(window) -> None:
	tauon_native.restore_window(_handle(window))


def SDL_RenderGeometry(renderer, texture, vertices, vertex_count: int, indices, index_count: int) -> None:
	del vertex_count, index_count
	tauon_native.render_geometry(_handle(renderer), _handle(texture), vertices, indices)


def SDL_CreatePopupWindow(parent, x: int, y: int, width: int, height: int, flags: int) -> int:
	return tauon_native.create_popup_window(_handle(parent), x, y, width, height, flags)


def SDL_CreateWindow(title, width: int, height: int, flags: int) -> int:
	if isinstance(title, bytes):
		title = title.decode("utf-8")
	return tauon_native.create_window(title, width, height, flags)


def SDL_CreateRenderer(window, name=None) -> int:
	if isinstance(name, bytes):
		name = name.decode("utf-8")
	return tauon_native.create_renderer(_handle(window), name)


def SDL_DestroyRenderer(renderer) -> None:
	tauon_native.destroy_renderer(_handle(renderer))


def SDL_DestroyWindow(window) -> None:
	tauon_native.destroy_window(_handle(window))


def SDL_GetWindowID(window) -> int:
	return tauon_native.get_window_id(_handle(window))


def _set_output(pointer, value: int) -> None:
	if pointer is not None:
		if hasattr(pointer, "_obj"):
			pointer._obj.value = value
		else:
			pointer.contents.value = value


def SDL_GetWindowSize(window, width, height) -> None:
	w, h = tauon_native.get_window_size(_handle(window), False)
	_set_output(width, w)
	_set_output(height, h)


def SDL_GetWindowSizeInPixels(window, width, height) -> None:
	w, h = tauon_native.get_window_size(_handle(window), True)
	_set_output(width, w)
	_set_output(height, h)


def SDL_SetWindowSize(window, width: int, height: int) -> None:
	tauon_native.set_window_size(_handle(window), width, height)


def SDL_SetWindowPosition(window, x: int, y: int) -> None:
	tauon_native.set_window_position(_handle(window), x, y)


def SDL_SetWindowMouseGrab(window, enabled: bool) -> None:
	tauon_native.set_window_mouse_grab(_handle(window), enabled)


def SDL_CaptureMouse(enabled: bool) -> None:
	tauon_native.capture_mouse(enabled)


def SDL_ShowWindow(window) -> None:
	tauon_native.show_window(_handle(window))


def SDL_HideWindow(window) -> None:
	tauon_native.hide_window(_handle(window))


def SDL_RaiseWindow(window) -> None:
	tauon_native.raise_window(_handle(window))


def SDL_RenderPresent(renderer) -> None:
	tauon_native.render_present(_handle(renderer))


def SDL_SetWindowMinimumSize(window, width: int, height: int) -> None:
	tauon_native.set_window_minimum_size(_handle(window), width, height)


SDLSetWindowMinimumSize = SDL_SetWindowMinimumSize


def SDL_SetWindowResizable(window, enabled: bool) -> None:
	tauon_native.set_window_resizable(_handle(window), enabled)


def SDL_SetWindowBordered(window, enabled: bool) -> None:
	tauon_native.set_window_bordered(_handle(window), enabled)


def SDL_SetWindowOpacity(window, opacity: float) -> None:
	tauon_native.set_window_opacity(_handle(window), opacity)


def SDL_SetWindowAlwaysOnTop(window, enabled: bool) -> None:
	tauon_native.set_window_always_on_top(_handle(window), enabled)


def SDL_SetWindowTitle(window, title) -> None:
	if isinstance(title, bytes):
		title = title.decode("utf-8", errors="replace")
	tauon_native.set_window_title(_handle(window), title)


def SDL_SetWindowFullscreen(window, enabled: bool) -> None:
	tauon_native.set_window_fullscreen(_handle(window), enabled)


def SDL_SetWindowFullscreenMode(window, mode) -> None:
	del window, mode


def SDL_SyncWindow(window) -> None:
	tauon_native.sync_window(_handle(window))


def SDL_GetWindowPosition(window, x, y) -> None:
	position_x, position_y = tauon_native.get_window_position(_handle(window))
	_set_output(x, position_x)
	_set_output(y, position_y)


def _mouse_state(global_state: bool, x, y) -> int:
	buttons, position_x, position_y = tauon_native.get_mouse_state(global_state)
	_set_output(x, position_x)
	_set_output(y, position_y)
	return buttons


def SDL_GetMouseState(x, y) -> int:
	return _mouse_state(False, x, y)


def SDL_GetGlobalMouseState(x, y) -> int:
	return _mouse_state(True, x, y)


def SDL_CreateSystemCursor(cursor_id: int) -> int:
	return tauon_native.create_system_cursor(cursor_id)


def SDL_SetCursor(cursor) -> None:
	tauon_native.set_cursor(_handle(cursor))


def create_color_cursor(width: int, height: int, pixels, hot_x: int, hot_y: int) -> int:
	return tauon_native.create_color_cursor(width, height, pixels, hot_x, hot_y)


def SDL_SetWindowHitTest(window, callback, _data=None) -> None:
	tauon_native.set_window_hit_test(_handle(window), callback)


def SDL_StartTextInput(window) -> None:
	tauon_native.start_text_input(_handle(window))


def SDL_StopTextInput(window) -> None:
	tauon_native.stop_text_input(_handle(window))


def SDL_SetTextInputArea(window, rectangle, cursor: int) -> None:
	tauon_native.set_text_input_area(_handle(window), _integer_rectangle(rectangle), cursor)


def get_display_refresh_rate(window) -> float:
	return tauon_native.get_display_refresh_rate(_handle(window))


def SDL_CreateTray(icon: ImageData, tooltip) -> int:
	return tauon_native.create_tray(icon.width, icon.height, icon.pixels, _text(tooltip))


def SDL_SetTrayIcon(tray, icon: ImageData) -> None:
	tauon_native.set_tray_icon(_handle(tray), icon.width, icon.height, icon.pixels)


def SDL_SetTrayTooltip(tray, tooltip) -> None:
	tauon_native.set_tray_tooltip(_handle(tray), _text(tooltip))


def SDL_CreateTrayMenu(tray) -> int:
	return tauon_native.create_tray_menu(_handle(tray))


def SDL_InsertTrayEntryAt(menu, position: int, label, flags: int) -> int:
	return tauon_native.insert_tray_entry(_handle(menu), position, None if label is None else _text(label), flags)


def SDL_TrayCallback(callback):
	return callback


def SDL_SetTrayEntryCallback(entry, callback, _userdata=None) -> None:
	tauon_native.set_tray_entry_callback(_handle(entry), callback)


def SDL_DestroyTray(tray) -> None:
	tauon_native.destroy_tray(_handle(tray))


def _text(value) -> str:
	return value.decode("utf-8") if isinstance(value, bytes) else value


def SDL_GetKeyFromName(name) -> int:
	return tauon_native.key_from_name(_text(name))


def SDL_GetScancodeFromName(name) -> int:
	return tauon_native.scancode_from_name(_text(name))


def SDL_InitSubSystem(flags: int) -> None:
	tauon_native.init_subsystem(flags)


def SDL_PumpEvents() -> None:
	tauon_native.pump_events()


def SDL_IsGamepad(identifier: int) -> bool:
	return tauon_native.is_gamepad(identifier)


def SDL_OpenGamepad(identifier: int) -> int:
	return tauon_native.open_gamepad(identifier)


def SDL_GetGamepadNameForID(identifier: int) -> bytes | None:
	name = tauon_native.gamepad_name(identifier)
	return name.encode("utf-8") if name is not None else None


def SDL_GetVersion() -> int:
	return tauon_native.sdl_version()


def SDL_GetWindowProperties(window):
	del window
	return None


def SDL_GetPointerProperty(properties, name, default=None):
	del properties, name
	return default


def SDL_RenderLine(renderer, x1: float, y1: float, x2: float, y2: float) -> None:
	tauon_native.render_line(_handle(renderer), x1, y1, x2, y2)


def SDL_GetTextureSize(texture, width, height) -> None:
	w, h = get_texture_size(texture)
	_set_output(width, w)
	_set_output(height, h)


def get_texture_size(texture) -> tuple[float, float]:
	return tauon_native.get_texture_size(_handle(texture))


def create_texture_from_cairo(renderer, width: int, height: int, pitch: int, pixels, alpha: bool, colour_key=None):
	return tauon_native.create_texture_from_cairo(
		_handle(renderer), width, height, pitch, pixels, alpha, colour_key
	)


def read_render_pixels(renderer, rectangle, alpha: bool) -> tuple[bytes, int]:
	return tauon_native.read_render_pixels(_handle(renderer), _integer_rectangle(rectangle), alpha)


def SDL_ComposeCustomBlendMode(
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
