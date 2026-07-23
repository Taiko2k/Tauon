#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <SDL3/SDL.h>

#include <cstdint>
#include <unordered_map>
#include <vector>

#include "native_render.h"

namespace {

PyObject* hit_test_callback = nullptr;
std::unordered_map<SDL_TrayEntry*, PyObject*> tray_callbacks;

void python_tray_callback(void* userdata, SDL_TrayEntry* entry) {
	PyObject* callback = static_cast<PyObject*>(userdata);
	if (callback == nullptr) return;
	const PyGILState_STATE gil_state = PyGILState_Ensure();
	PyObject* result = PyObject_CallFunction(callback, "ON", Py_None, PyLong_FromVoidPtr(entry));
	if (result == nullptr) {
		PyErr_WriteUnraisable(callback);
	} else {
		Py_DECREF(result);
	}
	PyGILState_Release(gil_state);
}

SDL_Surface* surface_from_rgba(int width, int height, Py_buffer& pixels) {
	const Py_ssize_t required = static_cast<Py_ssize_t>(width) * height * 4;
	if (width <= 0 || height <= 0 || pixels.len < required) {
		PyErr_SetString(PyExc_ValueError, "RGBA buffer is smaller than width * height * 4");
		return nullptr;
	}
	return SDL_CreateSurfaceFrom(width, height, SDL_PIXELFORMAT_RGBA32, pixels.buf, width * 4);
}

SDL_HitTestResult python_hit_test(SDL_Window*, const SDL_Point* point, void*) {
	if (hit_test_callback == nullptr || point == nullptr) return SDL_HITTEST_NORMAL;
	const PyGILState_STATE gil_state = PyGILState_Ensure();
	PyObject* result = PyObject_CallFunction(hit_test_callback, "ii", point->x, point->y);
	SDL_HitTestResult hit = SDL_HITTEST_NORMAL;
	if (result != nullptr) {
		const long value = PyLong_AsLong(result);
		if (!PyErr_Occurred()) hit = static_cast<SDL_HitTestResult>(value);
		Py_DECREF(result);
	}
	if (PyErr_Occurred()) PyErr_WriteUnraisable(hit_test_callback);
	PyGILState_Release(gil_state);
	return hit;
}

template<typename T>
T* pointer_from_python(PyObject* value, const char* name, bool allow_none = false) {
	if (value == Py_None && allow_none) {
		return nullptr;
	}
	void* pointer = PyLong_AsVoidPtr(value);
	if (pointer == nullptr && !PyErr_Occurred() && !allow_none) {
		PyErr_Format(PyExc_ValueError, "%s handle is null", name);
	}
	return static_cast<T*>(pointer);
}

PyObject* pointer_to_python(void* pointer) {
	if (pointer == nullptr) {
		Py_RETURN_NONE;
	}
	return PyLong_FromVoidPtr(pointer);
}

bool parse_frect(PyObject* value, SDL_FRect& rectangle) {
	if (!PyTuple_Check(value) || PyTuple_GET_SIZE(value) != 4) {
		PyErr_SetString(PyExc_TypeError, "rectangle must be a four-item tuple");
		return false;
	}
	rectangle.x = static_cast<float>(PyFloat_AsDouble(PyTuple_GET_ITEM(value, 0)));
	rectangle.y = static_cast<float>(PyFloat_AsDouble(PyTuple_GET_ITEM(value, 1)));
	rectangle.w = static_cast<float>(PyFloat_AsDouble(PyTuple_GET_ITEM(value, 2)));
	rectangle.h = static_cast<float>(PyFloat_AsDouble(PyTuple_GET_ITEM(value, 3)));
	return !PyErr_Occurred();
}

bool parse_rect(PyObject* value, SDL_Rect& rectangle) {
	if (!PyTuple_Check(value) || PyTuple_GET_SIZE(value) != 4) {
		PyErr_SetString(PyExc_TypeError, "rectangle must be a four-item tuple");
		return false;
	}
	rectangle.x = static_cast<int>(PyLong_AsLong(PyTuple_GET_ITEM(value, 0)));
	rectangle.y = static_cast<int>(PyLong_AsLong(PyTuple_GET_ITEM(value, 1)));
	rectangle.w = static_cast<int>(PyLong_AsLong(PyTuple_GET_ITEM(value, 2)));
	rectangle.h = static_cast<int>(PyLong_AsLong(PyTuple_GET_ITEM(value, 3)));
	return !PyErr_Occurred();
}

PyObject* sdl_result(bool success) {
	if (!success) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	Py_RETURN_NONE;
}

}  // namespace

PyObject* native_create_texture(PyObject*, PyObject* args) {
	PyObject* renderer_value = nullptr;
	unsigned int format = 0;
	int access = 0;
	int width = 0;
	int height = 0;
	if (!PyArg_ParseTuple(args, "OIiii", &renderer_value, &format, &access, &width, &height)) {
		return nullptr;
	}
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(renderer_value, "renderer");
	if (renderer == nullptr) {
		return nullptr;
	}
	SDL_Texture* texture = SDL_CreateTexture(renderer, static_cast<SDL_PixelFormat>(format),
		static_cast<SDL_TextureAccess>(access), width, height);
	if (texture == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return PyLong_FromVoidPtr(texture);
}

PyObject* native_create_texture_from_rgba(PyObject*, PyObject* args) {
	PyObject* renderer_value = nullptr;
	int width = 0;
	int height = 0;
	Py_buffer pixels{};
	if (!PyArg_ParseTuple(args, "Oiiy*", &renderer_value, &width, &height, &pixels)) {
		return nullptr;
	}
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(renderer_value, "renderer");
	if (renderer == nullptr) {
		PyBuffer_Release(&pixels);
		return nullptr;
	}
	const Py_ssize_t required_size = static_cast<Py_ssize_t>(width) * height * 4;
	if (width <= 0 || height <= 0 || pixels.len < required_size) {
		PyBuffer_Release(&pixels);
		PyErr_SetString(PyExc_ValueError, "RGBA buffer is smaller than width * height * 4");
		return nullptr;
	}
	SDL_Surface* surface = SDL_CreateSurfaceFrom(width, height, SDL_PIXELFORMAT_RGBA32, pixels.buf, width * 4);
	SDL_Texture* texture = surface != nullptr ? SDL_CreateTextureFromSurface(renderer, surface) : nullptr;
	SDL_DestroySurface(surface);
	PyBuffer_Release(&pixels);
	if (texture == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return PyLong_FromVoidPtr(texture);
}

PyObject* native_destroy_texture(PyObject*, PyObject* value) {
	SDL_Texture* texture = pointer_from_python<SDL_Texture>(value, "texture", true);
	if (PyErr_Occurred()) {
		return nullptr;
	}
	SDL_DestroyTexture(texture);
	Py_RETURN_NONE;
}

PyObject* native_get_render_target(PyObject*, PyObject* value) {
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(value, "renderer");
	if (renderer == nullptr) {
		return nullptr;
	}
	return pointer_to_python(SDL_GetRenderTarget(renderer));
}

PyObject* native_set_render_target(PyObject*, PyObject* args) {
	PyObject* renderer_value = nullptr;
	PyObject* texture_value = nullptr;
	if (!PyArg_ParseTuple(args, "OO", &renderer_value, &texture_value)) {
		return nullptr;
	}
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(renderer_value, "renderer");
	SDL_Texture* texture = pointer_from_python<SDL_Texture>(texture_value, "texture", true);
	if (renderer == nullptr || PyErr_Occurred()) {
		return nullptr;
	}
	return sdl_result(SDL_SetRenderTarget(renderer, texture));
}

PyObject* native_set_render_draw_blend_mode(PyObject*, PyObject* args) {
	PyObject* renderer_value = nullptr;
	unsigned int mode = 0;
	if (!PyArg_ParseTuple(args, "OI", &renderer_value, &mode)) {
		return nullptr;
	}
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(renderer_value, "renderer");
	if (renderer == nullptr) {
		return nullptr;
	}
	return sdl_result(SDL_SetRenderDrawBlendMode(renderer, static_cast<SDL_BlendMode>(mode)));
}

PyObject* native_set_render_draw_color(PyObject*, PyObject* args) {
	PyObject* renderer_value = nullptr;
	unsigned char red = 0;
	unsigned char green = 0;
	unsigned char blue = 0;
	unsigned char alpha = 0;
	if (!PyArg_ParseTuple(args, "OBBBB", &renderer_value, &red, &green, &blue, &alpha)) {
		return nullptr;
	}
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(renderer_value, "renderer");
	if (renderer == nullptr) {
		return nullptr;
	}
	return sdl_result(SDL_SetRenderDrawColor(renderer, red, green, blue, alpha));
}

PyObject* native_render_clear(PyObject*, PyObject* value) {
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(value, "renderer");
	if (renderer == nullptr) {
		return nullptr;
	}
	return sdl_result(SDL_RenderClear(renderer));
}

PyObject* native_render_fill_rect(PyObject*, PyObject* args) {
	PyObject* renderer_value = nullptr;
	PyObject* rectangle_value = nullptr;
	if (!PyArg_ParseTuple(args, "OO", &renderer_value, &rectangle_value)) {
		return nullptr;
	}
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(renderer_value, "renderer");
	if (renderer == nullptr) {
		return nullptr;
	}
	SDL_FRect rectangle{};
	const SDL_FRect* rectangle_pointer = nullptr;
	if (rectangle_value != Py_None) {
		if (!parse_frect(rectangle_value, rectangle)) {
			return nullptr;
		}
		rectangle_pointer = &rectangle;
	}
	return sdl_result(SDL_RenderFillRect(renderer, rectangle_pointer));
}

PyObject* native_render_texture(PyObject*, PyObject* args) {
	PyObject* renderer_value = nullptr;
	PyObject* texture_value = nullptr;
	PyObject* source_value = nullptr;
	PyObject* destination_value = nullptr;
	if (!PyArg_ParseTuple(args, "OOOO", &renderer_value, &texture_value, &source_value, &destination_value)) {
		return nullptr;
	}
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(renderer_value, "renderer");
	SDL_Texture* texture = pointer_from_python<SDL_Texture>(texture_value, "texture");
	if (renderer == nullptr || texture == nullptr) {
		return nullptr;
	}
	SDL_FRect source{};
	SDL_FRect destination{};
	const SDL_FRect* source_pointer = nullptr;
	const SDL_FRect* destination_pointer = nullptr;
	if (source_value != Py_None) {
		if (!parse_frect(source_value, source)) {
			return nullptr;
		}
		source_pointer = &source;
	}
	if (destination_value != Py_None) {
		if (!parse_frect(destination_value, destination)) {
			return nullptr;
		}
		destination_pointer = &destination;
	}
	return sdl_result(SDL_RenderTexture(renderer, texture, source_pointer, destination_pointer));
}

PyObject* native_set_texture_blend_mode(PyObject*, PyObject* args) {
	PyObject* texture_value = nullptr;
	unsigned int mode = 0;
	if (!PyArg_ParseTuple(args, "OI", &texture_value, &mode)) {
		return nullptr;
	}
	SDL_Texture* texture = pointer_from_python<SDL_Texture>(texture_value, "texture");
	if (texture == nullptr) {
		return nullptr;
	}
	return sdl_result(SDL_SetTextureBlendMode(texture, static_cast<SDL_BlendMode>(mode)));
}

PyObject* native_set_texture_scale_mode(PyObject*, PyObject* args) {
	PyObject* texture_value = nullptr;
	int mode = 0;
	if (!PyArg_ParseTuple(args, "Oi", &texture_value, &mode)) {
		return nullptr;
	}
	SDL_Texture* texture = pointer_from_python<SDL_Texture>(texture_value, "texture");
	if (texture == nullptr) {
		return nullptr;
	}
	return sdl_result(SDL_SetTextureScaleMode(texture, static_cast<SDL_ScaleMode>(mode)));
}

PyObject* native_set_texture_alpha_mod(PyObject*, PyObject* args) {
	PyObject* texture_value = nullptr;
	unsigned char alpha = 0;
	if (!PyArg_ParseTuple(args, "OB", &texture_value, &alpha)) {
		return nullptr;
	}
	SDL_Texture* texture = pointer_from_python<SDL_Texture>(texture_value, "texture");
	if (texture == nullptr) {
		return nullptr;
	}
	return sdl_result(SDL_SetTextureAlphaMod(texture, alpha));
}

PyObject* native_update_texture(PyObject*, PyObject* args) {
	PyObject* texture_value = nullptr;
	PyObject* rectangle_value = nullptr;
	Py_buffer pixels{};
	int pitch = 0;
	if (!PyArg_ParseTuple(args, "OOy*i", &texture_value, &rectangle_value, &pixels, &pitch)) {
		return nullptr;
	}
	SDL_Texture* texture = pointer_from_python<SDL_Texture>(texture_value, "texture");
	SDL_Rect rectangle{};
	const SDL_Rect* rectangle_pointer = nullptr;
	if (texture != nullptr && rectangle_value != Py_None) {
		if (!parse_rect(rectangle_value, rectangle)) {
			PyBuffer_Release(&pixels);
			return nullptr;
		}
		rectangle_pointer = &rectangle;
	}
	if (texture == nullptr) {
		PyBuffer_Release(&pixels);
		return nullptr;
	}
	const bool success = SDL_UpdateTexture(texture, rectangle_pointer, pixels.buf, pitch);
	PyBuffer_Release(&pixels);
	return sdl_result(success);
}

PyObject* native_set_render_clip_rect(PyObject*, PyObject* args) {
	PyObject* renderer_value = nullptr;
	PyObject* rectangle_value = nullptr;
	if (!PyArg_ParseTuple(args, "OO", &renderer_value, &rectangle_value)) {
		return nullptr;
	}
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(renderer_value, "renderer");
	if (renderer == nullptr) {
		return nullptr;
	}
	SDL_Rect rectangle{};
	const SDL_Rect* rectangle_pointer = nullptr;
	if (rectangle_value != Py_None) {
		if (!parse_rect(rectangle_value, rectangle)) {
			return nullptr;
		}
		rectangle_pointer = &rectangle;
	}
	return sdl_result(SDL_SetRenderClipRect(renderer, rectangle_pointer));
}

PyObject* native_get_window_flags(PyObject*, PyObject* value) {
	SDL_Window* window = pointer_from_python<SDL_Window>(value, "window");
	if (window == nullptr) {
		return nullptr;
	}
	return PyLong_FromUnsignedLongLong(SDL_GetWindowFlags(window));
}

#define WINDOW_ACTION(function_name, sdl_name) \
	PyObject* function_name(PyObject*, PyObject* value) { \
		SDL_Window* window = pointer_from_python<SDL_Window>(value, "window"); \
		if (window == nullptr) return nullptr; \
		return sdl_result(sdl_name(window)); \
	}

WINDOW_ACTION(native_maximize_window, SDL_MaximizeWindow)
WINDOW_ACTION(native_minimize_window, SDL_MinimizeWindow)
WINDOW_ACTION(native_restore_window, SDL_RestoreWindow)

PyObject* native_render_geometry(PyObject*, PyObject* args) {
	PyObject* renderer_value = nullptr;
	PyObject* texture_value = nullptr;
	PyObject* vertices_value = nullptr;
	PyObject* indices_value = nullptr;
	if (!PyArg_ParseTuple(args, "OOOO", &renderer_value, &texture_value, &vertices_value, &indices_value)) {
		return nullptr;
	}
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(renderer_value, "renderer");
	SDL_Texture* texture = pointer_from_python<SDL_Texture>(texture_value, "texture", true);
	PyObject* vertices_fast = PySequence_Fast(vertices_value, "vertices must be a sequence");
	PyObject* indices_fast = PySequence_Fast(indices_value, "indices must be a sequence");
	if (renderer == nullptr || PyErr_Occurred() || vertices_fast == nullptr || indices_fast == nullptr) {
		Py_XDECREF(vertices_fast);
		Py_XDECREF(indices_fast);
		return nullptr;
	}
	std::vector<SDL_Vertex> vertices;
	vertices.reserve(static_cast<std::size_t>(PySequence_Fast_GET_SIZE(vertices_fast)));
	for (Py_ssize_t index = 0; index < PySequence_Fast_GET_SIZE(vertices_fast); ++index) {
		PyObject* item = PySequence_Fast_GET_ITEM(vertices_fast, index);
		if (!PyTuple_Check(item) || PyTuple_GET_SIZE(item) != 8) {
			PyErr_SetString(PyExc_TypeError, "each vertex must be an eight-item tuple");
			Py_DECREF(vertices_fast);
			Py_DECREF(indices_fast);
			return nullptr;
		}
		SDL_Vertex vertex{};
		vertex.position.x = static_cast<float>(PyFloat_AsDouble(PyTuple_GET_ITEM(item, 0)));
		vertex.position.y = static_cast<float>(PyFloat_AsDouble(PyTuple_GET_ITEM(item, 1)));
		vertex.tex_coord.x = static_cast<float>(PyFloat_AsDouble(PyTuple_GET_ITEM(item, 2)));
		vertex.tex_coord.y = static_cast<float>(PyFloat_AsDouble(PyTuple_GET_ITEM(item, 3)));
		vertex.color.r = static_cast<float>(PyFloat_AsDouble(PyTuple_GET_ITEM(item, 4)));
		vertex.color.g = static_cast<float>(PyFloat_AsDouble(PyTuple_GET_ITEM(item, 5)));
		vertex.color.b = static_cast<float>(PyFloat_AsDouble(PyTuple_GET_ITEM(item, 6)));
		vertex.color.a = static_cast<float>(PyFloat_AsDouble(PyTuple_GET_ITEM(item, 7)));
		if (PyErr_Occurred()) {
			Py_DECREF(vertices_fast);
			Py_DECREF(indices_fast);
			return nullptr;
		}
		vertices.push_back(vertex);
	}
	std::vector<int> indices;
	indices.reserve(static_cast<std::size_t>(PySequence_Fast_GET_SIZE(indices_fast)));
	for (Py_ssize_t index = 0; index < PySequence_Fast_GET_SIZE(indices_fast); ++index) {
		const long value = PyLong_AsLong(PySequence_Fast_GET_ITEM(indices_fast, index));
		if (PyErr_Occurred()) {
			Py_DECREF(vertices_fast);
			Py_DECREF(indices_fast);
			return nullptr;
		}
		indices.push_back(static_cast<int>(value));
	}
	Py_DECREF(vertices_fast);
	Py_DECREF(indices_fast);
	return sdl_result(SDL_RenderGeometry(renderer, texture, vertices.data(), static_cast<int>(vertices.size()),
		indices.data(), static_cast<int>(indices.size())));
}

PyObject* native_create_popup_window(PyObject*, PyObject* args) {
	PyObject* parent_value = nullptr;
	int x = 0;
	int y = 0;
	int width = 0;
	int height = 0;
	unsigned long long flags = 0;
	if (!PyArg_ParseTuple(args, "OiiiiK", &parent_value, &x, &y, &width, &height, &flags)) return nullptr;
	SDL_Window* parent = pointer_from_python<SDL_Window>(parent_value, "parent window");
	if (parent == nullptr) return nullptr;
	SDL_Window* window = SDL_CreatePopupWindow(parent, x, y, width, height, static_cast<SDL_WindowFlags>(flags));
	if (window == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return PyLong_FromVoidPtr(window);
}

PyObject* native_create_window(PyObject*, PyObject* args) {
	const char* title = nullptr;
	int width = 0;
	int height = 0;
	unsigned long long flags = 0;
	if (!PyArg_ParseTuple(args, "siiK", &title, &width, &height, &flags)) return nullptr;
	SDL_Window* window = SDL_CreateWindow(title, width, height, static_cast<SDL_WindowFlags>(flags));
	if (window == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return PyLong_FromVoidPtr(window);
}

PyObject* native_create_renderer(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	const char* name = nullptr;
	if (!PyArg_ParseTuple(args, "Oz", &window_value, &name)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	if (window == nullptr) return nullptr;
	SDL_Renderer* renderer = SDL_CreateRenderer(window, name);
	if (renderer == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return PyLong_FromVoidPtr(renderer);
}

PyObject* native_destroy_renderer(PyObject*, PyObject* value) {
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(value, "renderer", true);
	if (PyErr_Occurred()) return nullptr;
	SDL_DestroyRenderer(renderer);
	Py_RETURN_NONE;
}

PyObject* native_destroy_window(PyObject*, PyObject* value) {
	SDL_Window* window = pointer_from_python<SDL_Window>(value, "window", true);
	if (PyErr_Occurred()) return nullptr;
	SDL_DestroyWindow(window);
	Py_RETURN_NONE;
}

PyObject* native_get_window_id(PyObject*, PyObject* value) {
	SDL_Window* window = pointer_from_python<SDL_Window>(value, "window");
	if (window == nullptr) return nullptr;
	return PyLong_FromUnsignedLong(SDL_GetWindowID(window));
}

PyObject* native_get_window_size(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	int pixels = 0;
	if (!PyArg_ParseTuple(args, "Op", &window_value, &pixels)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	if (window == nullptr) return nullptr;
	int width = 0;
	int height = 0;
	const bool success = pixels ? SDL_GetWindowSizeInPixels(window, &width, &height) : SDL_GetWindowSize(window, &width, &height);
	if (!success) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return Py_BuildValue("(ii)", width, height);
}

PyObject* native_set_window_size(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	int width = 0;
	int height = 0;
	if (!PyArg_ParseTuple(args, "Oii", &window_value, &width, &height)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	if (window == nullptr) return nullptr;
	return sdl_result(SDL_SetWindowSize(window, width, height));
}

PyObject* native_set_window_position(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	int x = 0;
	int y = 0;
	if (!PyArg_ParseTuple(args, "Oii", &window_value, &x, &y)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	if (window == nullptr) return nullptr;
	return sdl_result(SDL_SetWindowPosition(window, x, y));
}

PyObject* native_set_window_mouse_grab(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	int enabled = 0;
	if (!PyArg_ParseTuple(args, "Op", &window_value, &enabled)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	if (window == nullptr) return nullptr;
	return sdl_result(SDL_SetWindowMouseGrab(window, enabled != 0));
}

PyObject* native_capture_mouse(PyObject*, PyObject* value) {
	const int enabled = PyObject_IsTrue(value);
	if (enabled < 0) return nullptr;
	return sdl_result(SDL_CaptureMouse(enabled != 0));
}

WINDOW_ACTION(native_show_window, SDL_ShowWindow)
WINDOW_ACTION(native_hide_window, SDL_HideWindow)
WINDOW_ACTION(native_raise_window, SDL_RaiseWindow)

PyObject* native_render_present(PyObject*, PyObject* value) {
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(value, "renderer");
	if (renderer == nullptr) return nullptr;
	SDL_RenderPresent(renderer);
	Py_RETURN_NONE;
}

PyObject* native_render_line(PyObject*, PyObject* args) {
	PyObject* renderer_value = nullptr;
	float x1 = 0;
	float y1 = 0;
	float x2 = 0;
	float y2 = 0;
	if (!PyArg_ParseTuple(args, "Offff", &renderer_value, &x1, &y1, &x2, &y2)) return nullptr;
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(renderer_value, "renderer");
	if (renderer == nullptr) return nullptr;
	return sdl_result(SDL_RenderLine(renderer, x1, y1, x2, y2));
}

PyObject* native_get_texture_size(PyObject*, PyObject* value) {
	SDL_Texture* texture = pointer_from_python<SDL_Texture>(value, "texture");
	if (texture == nullptr) return nullptr;
	float width = 0;
	float height = 0;
	if (!SDL_GetTextureSize(texture, &width, &height)) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return Py_BuildValue("(ff)", width, height);
}

PyObject* native_create_texture_from_cairo(PyObject*, PyObject* args) {
	PyObject* renderer_value = nullptr;
	int width = 0;
	int height = 0;
	int pitch = 0;
	Py_buffer pixels{};
	int alpha = 0;
	PyObject* colour_key = nullptr;
	if (!PyArg_ParseTuple(args, "Oiiiy*pO", &renderer_value, &width, &height, &pitch, &pixels, &alpha, &colour_key)) {
		return nullptr;
	}
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(renderer_value, "renderer");
	if (renderer == nullptr) {
		PyBuffer_Release(&pixels);
		return nullptr;
	}
	const SDL_PixelFormat format = alpha ? SDL_PIXELFORMAT_ARGB8888 : SDL_PIXELFORMAT_XRGB8888;
	SDL_Surface* surface = SDL_CreateSurfaceFrom(width, height, format, pixels.buf, pitch);
	if (surface != nullptr && colour_key != Py_None) {
		unsigned char red = 0;
		unsigned char green = 0;
		unsigned char blue = 0;
		if (!PyArg_ParseTuple(colour_key, "BBB", &red, &green, &blue)) {
			SDL_DestroySurface(surface);
			PyBuffer_Release(&pixels);
			return nullptr;
		}
		const SDL_PixelFormatDetails* details = SDL_GetPixelFormatDetails(format);
		const Uint32 key = SDL_MapRGB(details, nullptr, red, green, blue);
		if (!SDL_SetSurfaceColorKey(surface, true, key)) {
			SDL_DestroySurface(surface);
			PyBuffer_Release(&pixels);
			PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
			return nullptr;
		}
	}
	SDL_Texture* texture = surface != nullptr ? SDL_CreateTextureFromSurface(renderer, surface) : nullptr;
	SDL_DestroySurface(surface);
	PyBuffer_Release(&pixels);
	if (texture == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return PyLong_FromVoidPtr(texture);
}

PyObject* native_read_render_pixels(PyObject*, PyObject* args) {
	PyObject* renderer_value = nullptr;
	PyObject* rectangle_value = nullptr;
	int alpha = 0;
	if (!PyArg_ParseTuple(args, "OOp", &renderer_value, &rectangle_value, &alpha)) return nullptr;
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(renderer_value, "renderer");
	SDL_Rect rectangle{};
	if (renderer == nullptr || !parse_rect(rectangle_value, rectangle)) return nullptr;
	SDL_Surface* raw = SDL_RenderReadPixels(renderer, &rectangle);
	if (raw == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	const SDL_PixelFormat format = alpha ? SDL_PIXELFORMAT_ARGB8888 : SDL_PIXELFORMAT_XRGB8888;
	SDL_Surface* surface = raw->format == format ? raw : SDL_ConvertSurface(raw, format);
	if (surface != raw) SDL_DestroySurface(raw);
	if (surface == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	PyObject* data = PyBytes_FromStringAndSize(static_cast<const char*>(surface->pixels),
		static_cast<Py_ssize_t>(surface->pitch) * surface->h);
	PyObject* result = data != nullptr ? Py_BuildValue("(Ni)", data, surface->pitch) : nullptr;
	SDL_DestroySurface(surface);
	return result;
}

PyObject* native_compose_blend_mode(PyObject*, PyObject* args) {
	int source_colour = 0;
	int destination_colour = 0;
	int colour_operation = 0;
	int source_alpha = 0;
	int destination_alpha = 0;
	int alpha_operation = 0;
	if (!PyArg_ParseTuple(args, "iiiiii", &source_colour, &destination_colour, &colour_operation,
		&source_alpha, &destination_alpha, &alpha_operation)) return nullptr;
	const SDL_BlendMode mode = SDL_ComposeCustomBlendMode(
		static_cast<SDL_BlendFactor>(source_colour), static_cast<SDL_BlendFactor>(destination_colour),
		static_cast<SDL_BlendOperation>(colour_operation), static_cast<SDL_BlendFactor>(source_alpha),
		static_cast<SDL_BlendFactor>(destination_alpha), static_cast<SDL_BlendOperation>(alpha_operation));
	return PyLong_FromUnsignedLong(mode);
}

PyObject* native_set_window_minimum_size(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	int width = 0;
	int height = 0;
	if (!PyArg_ParseTuple(args, "Oii", &window_value, &width, &height)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	if (window == nullptr) return nullptr;
	return sdl_result(SDL_SetWindowMinimumSize(window, width, height));
}

#define WINDOW_BOOL_ACTION(function_name, sdl_name) \
	PyObject* function_name(PyObject*, PyObject* args) { \
		PyObject* window_value = nullptr; int enabled = 0; \
		if (!PyArg_ParseTuple(args, "Op", &window_value, &enabled)) return nullptr; \
		SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window"); \
		if (window == nullptr) return nullptr; \
		return sdl_result(sdl_name(window, enabled != 0)); \
	}

WINDOW_BOOL_ACTION(native_set_window_resizable, SDL_SetWindowResizable)
WINDOW_BOOL_ACTION(native_set_window_bordered, SDL_SetWindowBordered)
WINDOW_BOOL_ACTION(native_set_window_always_on_top, SDL_SetWindowAlwaysOnTop)
WINDOW_BOOL_ACTION(native_set_window_fullscreen, SDL_SetWindowFullscreen)

PyObject* native_set_window_opacity(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	float opacity = 0;
	if (!PyArg_ParseTuple(args, "Of", &window_value, &opacity)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	if (window == nullptr) return nullptr;
	return sdl_result(SDL_SetWindowOpacity(window, opacity));
}

PyObject* native_set_window_title(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	const char* title = nullptr;
	if (!PyArg_ParseTuple(args, "Os", &window_value, &title)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	if (window == nullptr) return nullptr;
	return sdl_result(SDL_SetWindowTitle(window, title));
}

WINDOW_ACTION(native_sync_window, SDL_SyncWindow)

PyObject* native_get_window_position(PyObject*, PyObject* value) {
	SDL_Window* window = pointer_from_python<SDL_Window>(value, "window");
	if (window == nullptr) return nullptr;
	int x = 0;
	int y = 0;
	if (!SDL_GetWindowPosition(window, &x, &y)) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return Py_BuildValue("(ii)", x, y);
}

PyObject* native_get_mouse_state(PyObject*, PyObject* value) {
	const int global = PyObject_IsTrue(value);
	if (global < 0) return nullptr;
	float x = 0;
	float y = 0;
	const SDL_MouseButtonFlags buttons = global ? SDL_GetGlobalMouseState(&x, &y) : SDL_GetMouseState(&x, &y);
	return Py_BuildValue("(Iff)", buttons, x, y);
}

PyObject* native_set_texture_color_mod(PyObject*, PyObject* args) {
	PyObject* texture_value = nullptr;
	unsigned char red = 0;
	unsigned char green = 0;
	unsigned char blue = 0;
	if (!PyArg_ParseTuple(args, "OBBB", &texture_value, &red, &green, &blue)) return nullptr;
	SDL_Texture* texture = pointer_from_python<SDL_Texture>(texture_value, "texture");
	if (texture == nullptr) return nullptr;
	return sdl_result(SDL_SetTextureColorMod(texture, red, green, blue));
}

PyObject* native_create_system_cursor(PyObject*, PyObject* value) {
	const long cursor_id = PyLong_AsLong(value);
	if (cursor_id == -1 && PyErr_Occurred()) return nullptr;
	SDL_Cursor* cursor = SDL_CreateSystemCursor(static_cast<SDL_SystemCursor>(cursor_id));
	if (cursor == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return PyLong_FromVoidPtr(cursor);
}

PyObject* native_set_cursor(PyObject*, PyObject* value) {
	SDL_Cursor* cursor = pointer_from_python<SDL_Cursor>(value, "cursor", true);
	if (PyErr_Occurred()) return nullptr;
	return sdl_result(SDL_SetCursor(cursor));
}

PyObject* native_create_color_cursor(PyObject*, PyObject* args) {
	int width = 0;
	int height = 0;
	Py_buffer pixels{};
	int hot_x = 0;
	int hot_y = 0;
	if (!PyArg_ParseTuple(args, "iiy*ii", &width, &height, &pixels, &hot_x, &hot_y)) return nullptr;
	SDL_Surface* surface = SDL_CreateSurfaceFrom(width, height, SDL_PIXELFORMAT_ARGB8888, pixels.buf, width * 4);
	SDL_Cursor* cursor = surface != nullptr ? SDL_CreateColorCursor(surface, hot_x, hot_y) : nullptr;
	SDL_DestroySurface(surface);
	PyBuffer_Release(&pixels);
	if (cursor == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return PyLong_FromVoidPtr(cursor);
}

PyObject* native_set_window_hit_test(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	PyObject* callback = nullptr;
	if (!PyArg_ParseTuple(args, "OO", &window_value, &callback)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	if (window == nullptr) return nullptr;
	if (callback != Py_None && !PyCallable_Check(callback)) {
		PyErr_SetString(PyExc_TypeError, "hit-test callback must be callable or None");
		return nullptr;
	}
	if (!SDL_SetWindowHitTest(window, callback == Py_None ? nullptr : python_hit_test, nullptr)) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	PyObject* replacement = callback == Py_None ? nullptr : callback;
	Py_XINCREF(replacement);
	Py_XDECREF(hit_test_callback);
	hit_test_callback = replacement;
	Py_RETURN_NONE;
}

PyObject* native_start_text_input(PyObject*, PyObject* value) {
	SDL_Window* window = pointer_from_python<SDL_Window>(value, "window");
	if (window == nullptr) return nullptr;
	return sdl_result(SDL_StartTextInput(window));
}

PyObject* native_stop_text_input(PyObject*, PyObject* value) {
	SDL_Window* window = pointer_from_python<SDL_Window>(value, "window");
	if (window == nullptr) return nullptr;
	return sdl_result(SDL_StopTextInput(window));
}

PyObject* native_set_text_input_area(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	PyObject* rectangle_value = nullptr;
	int cursor = 0;
	if (!PyArg_ParseTuple(args, "OOi", &window_value, &rectangle_value, &cursor)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	SDL_Rect rectangle{};
	if (window == nullptr || !parse_rect(rectangle_value, rectangle)) return nullptr;
	return sdl_result(SDL_SetTextInputArea(window, &rectangle, cursor));
}

PyObject* native_get_display_refresh_rate(PyObject*, PyObject* value) {
	SDL_Window* window = pointer_from_python<SDL_Window>(value, "window");
	if (window == nullptr) return nullptr;
	const SDL_DisplayID display = SDL_GetDisplayForWindow(window);
	const SDL_DisplayMode* mode = display != 0 ? SDL_GetCurrentDisplayMode(display) : nullptr;
	return PyFloat_FromDouble(mode != nullptr ? mode->refresh_rate : 0.0);
}

PyObject* native_create_tray(PyObject*, PyObject* args) {
	int width = 0;
	int height = 0;
	Py_buffer pixels{};
	const char* tooltip = nullptr;
	if (!PyArg_ParseTuple(args, "iiy*s", &width, &height, &pixels, &tooltip)) return nullptr;
	SDL_Surface* surface = surface_from_rgba(width, height, pixels);
	SDL_Tray* tray = surface != nullptr ? SDL_CreateTray(surface, tooltip) : nullptr;
	SDL_DestroySurface(surface);
	PyBuffer_Release(&pixels);
	if (tray == nullptr) {
		if (!PyErr_Occurred()) PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return PyLong_FromVoidPtr(tray);
}

PyObject* native_set_tray_icon(PyObject*, PyObject* args) {
	PyObject* tray_value = nullptr;
	int width = 0;
	int height = 0;
	Py_buffer pixels{};
	if (!PyArg_ParseTuple(args, "Oiiy*", &tray_value, &width, &height, &pixels)) return nullptr;
	SDL_Tray* tray = pointer_from_python<SDL_Tray>(tray_value, "tray");
	SDL_Surface* surface = tray != nullptr ? surface_from_rgba(width, height, pixels) : nullptr;
	if (surface != nullptr) SDL_SetTrayIcon(tray, surface);
	SDL_DestroySurface(surface);
	PyBuffer_Release(&pixels);
	if (surface == nullptr) return nullptr;
	Py_RETURN_NONE;
}

PyObject* native_set_tray_tooltip(PyObject*, PyObject* args) {
	PyObject* tray_value = nullptr;
	const char* tooltip = nullptr;
	if (!PyArg_ParseTuple(args, "Os", &tray_value, &tooltip)) return nullptr;
	SDL_Tray* tray = pointer_from_python<SDL_Tray>(tray_value, "tray");
	if (tray == nullptr) return nullptr;
	SDL_SetTrayTooltip(tray, tooltip);
	Py_RETURN_NONE;
}

PyObject* native_create_tray_menu(PyObject*, PyObject* value) {
	SDL_Tray* tray = pointer_from_python<SDL_Tray>(value, "tray");
	if (tray == nullptr) return nullptr;
	SDL_TrayMenu* menu = SDL_CreateTrayMenu(tray);
	if (menu == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return PyLong_FromVoidPtr(menu);
}

PyObject* native_insert_tray_entry(PyObject*, PyObject* args) {
	PyObject* menu_value = nullptr;
	int position = 0;
	PyObject* label_value = nullptr;
	unsigned int flags = 0;
	if (!PyArg_ParseTuple(args, "OiOI", &menu_value, &position, &label_value, &flags)) return nullptr;
	SDL_TrayMenu* menu = pointer_from_python<SDL_TrayMenu>(menu_value, "tray menu");
	const char* label = label_value == Py_None ? nullptr : PyUnicode_AsUTF8(label_value);
	if (menu == nullptr || (label_value != Py_None && label == nullptr)) return nullptr;
	SDL_TrayEntry* entry = SDL_InsertTrayEntryAt(menu, position, label, static_cast<SDL_TrayEntryFlags>(flags));
	if (entry == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return PyLong_FromVoidPtr(entry);
}

PyObject* native_set_tray_entry_callback(PyObject*, PyObject* args) {
	PyObject* entry_value = nullptr;
	PyObject* callback = nullptr;
	if (!PyArg_ParseTuple(args, "OO", &entry_value, &callback)) return nullptr;
	SDL_TrayEntry* entry = pointer_from_python<SDL_TrayEntry>(entry_value, "tray entry");
	if (entry == nullptr) return nullptr;
	if (!PyCallable_Check(callback)) {
		PyErr_SetString(PyExc_TypeError, "tray callback must be callable");
		return nullptr;
	}
	auto existing = tray_callbacks.find(entry);
	if (existing != tray_callbacks.end()) Py_DECREF(existing->second);
	Py_INCREF(callback);
	tray_callbacks[entry] = callback;
	SDL_SetTrayEntryCallback(entry, python_tray_callback, callback);
	Py_RETURN_NONE;
}

PyObject* native_destroy_tray(PyObject*, PyObject* value) {
	SDL_Tray* tray = pointer_from_python<SDL_Tray>(value, "tray", true);
	if (PyErr_Occurred()) return nullptr;
	SDL_DestroyTray(tray);
	for (auto& item : tray_callbacks) Py_DECREF(item.second);
	tray_callbacks.clear();
	Py_RETURN_NONE;
}

PyObject* native_set_window_icon(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	int width = 0;
	int height = 0;
	Py_buffer pixels{};
	if (!PyArg_ParseTuple(args, "Oiiy*", &window_value, &width, &height, &pixels)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	SDL_Surface* surface = window != nullptr ? surface_from_rgba(width, height, pixels) : nullptr;
	const bool success = surface != nullptr && SDL_SetWindowIcon(window, surface);
	SDL_DestroySurface(surface);
	PyBuffer_Release(&pixels);
	if (!success) {
		if (!PyErr_Occurred()) PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	Py_RETURN_NONE;
}

PyObject* native_set_window_progress_state(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	int state = 0;
	if (!PyArg_ParseTuple(args, "Oi", &window_value, &state)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	if (window == nullptr) return nullptr;
	return sdl_result(SDL_SetWindowProgressState(window, static_cast<SDL_ProgressState>(state)));
}

PyObject* native_set_window_progress_value(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	float value = 0;
	if (!PyArg_ParseTuple(args, "Of", &window_value, &value)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	if (window == nullptr) return nullptr;
	return sdl_result(SDL_SetWindowProgressValue(window, value));
}

PyObject* native_video_driver(PyObject*, PyObject*) {
	const char* driver = SDL_GetCurrentVideoDriver();
	if (driver == nullptr) Py_RETURN_NONE;
	return PyUnicode_FromString(driver);
}

PyObject* native_flush_renderer(PyObject*, PyObject* value) {
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(value, "renderer");
	if (renderer == nullptr) return nullptr;
	return sdl_result(SDL_FlushRenderer(renderer));
}

PyObject* native_render_texture_rotated(PyObject*, PyObject* args) {
	PyObject* renderer_value = nullptr;
	PyObject* texture_value = nullptr;
	PyObject* source_value = nullptr;
	PyObject* destination_value = nullptr;
	double angle = 0;
	PyObject* center_value = nullptr;
	int flip = 0;
	if (!PyArg_ParseTuple(args, "OOOOdOi", &renderer_value, &texture_value, &source_value,
		&destination_value, &angle, &center_value, &flip)) return nullptr;
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(renderer_value, "renderer");
	SDL_Texture* texture = pointer_from_python<SDL_Texture>(texture_value, "texture");
	SDL_FRect source{};
	SDL_FRect destination{};
	const SDL_FRect* source_pointer = nullptr;
	const SDL_FRect* destination_pointer = nullptr;
	if (source_value != Py_None) {
		if (!parse_frect(source_value, source)) return nullptr;
		source_pointer = &source;
	}
	if (destination_value != Py_None) {
		if (!parse_frect(destination_value, destination)) return nullptr;
		destination_pointer = &destination;
	}
	SDL_FPoint center{};
	const SDL_FPoint* center_pointer = nullptr;
	if (center_value != Py_None) {
		if (!PyTuple_Check(center_value) || PyTuple_GET_SIZE(center_value) != 2) {
			PyErr_SetString(PyExc_TypeError, "rotation center must be a two-item tuple");
			return nullptr;
		}
		center.x = static_cast<float>(PyFloat_AsDouble(PyTuple_GET_ITEM(center_value, 0)));
		center.y = static_cast<float>(PyFloat_AsDouble(PyTuple_GET_ITEM(center_value, 1)));
		if (PyErr_Occurred()) return nullptr;
		center_pointer = &center;
	}
	if (renderer == nullptr || texture == nullptr) return nullptr;
	return sdl_result(SDL_RenderTextureRotated(renderer, texture, source_pointer, destination_pointer,
		angle, center_pointer, static_cast<SDL_FlipMode>(flip)));
}

PyObject* native_gl_get_current_context(PyObject*, PyObject*) {
	return pointer_to_python(SDL_GL_GetCurrentContext());
}

PyObject* native_gl_set_attribute(PyObject*, PyObject* args) {
	int attribute = 0;
	int value = 0;
	if (!PyArg_ParseTuple(args, "ii", &attribute, &value)) return nullptr;
	return sdl_result(SDL_GL_SetAttribute(static_cast<SDL_GLAttr>(attribute), value));
}

PyObject* native_gl_create_context(PyObject*, PyObject* value) {
	SDL_Window* window = pointer_from_python<SDL_Window>(value, "window");
	if (window == nullptr) return nullptr;
	SDL_GLContext context = SDL_GL_CreateContext(window);
	if (context == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return PyLong_FromVoidPtr(context);
}

PyObject* native_gl_make_current(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	PyObject* context_value = nullptr;
	if (!PyArg_ParseTuple(args, "OO", &window_value, &context_value)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	SDL_GLContext context = pointer_from_python<SDL_GLContextState>(context_value, "GL context", true);
	if (window == nullptr || PyErr_Occurred()) return nullptr;
	return sdl_result(SDL_GL_MakeCurrent(window, context));
}

PyObject* native_create_texture_from_opengl(PyObject*, PyObject* args) {
	PyObject* renderer_value = nullptr;
	unsigned long long texture_id = 0;
	int width = 0;
	int height = 0;
	int access = 0;
	if (!PyArg_ParseTuple(args, "OKiii", &renderer_value, &texture_id, &width, &height, &access)) return nullptr;
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(renderer_value, "renderer");
	if (renderer == nullptr) return nullptr;
	SDL_PropertiesID properties = SDL_CreateProperties();
	SDL_SetNumberProperty(properties, SDL_PROP_TEXTURE_CREATE_OPENGL_TEXTURE_NUMBER, static_cast<Sint64>(texture_id));
	SDL_SetNumberProperty(properties, SDL_PROP_TEXTURE_CREATE_WIDTH_NUMBER, width);
	SDL_SetNumberProperty(properties, SDL_PROP_TEXTURE_CREATE_HEIGHT_NUMBER, height);
	SDL_SetNumberProperty(properties, SDL_PROP_TEXTURE_CREATE_ACCESS_NUMBER, access);
	SDL_Texture* texture = SDL_CreateTextureWithProperties(renderer, properties);
	SDL_DestroyProperties(properties);
	if (texture == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return PyLong_FromVoidPtr(texture);
}
