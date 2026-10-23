#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <SDL3/SDL.h>

#include <cstdint>
#include <cstring>
#include <iterator>
#include <string>
#include <unordered_map>
#include <vector>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <shobjidl.h>
#endif

#include "native_render.h"

namespace {

PyObject* hit_test_callback = nullptr;
std::unordered_map<SDL_TrayEntry*, PyObject*> tray_callbacks;
SDL_Window* launcher_window = nullptr;
SDL_Renderer* launcher_renderer = nullptr;

// One capsule per live native object, so destroying through any handle
// invalidates every reference Python holds. Entries are borrowed.
std::unordered_map<void*, PyObject*> live_handles;
constexpr const char* kDestroyedName = "tauon_native.Destroyed";

void forget_handle(PyObject* capsule) {
	const auto existing = live_handles.find(PyCapsule_GetPointer(capsule, PyCapsule_GetName(capsule)));
	if (existing != live_handles.end() && existing->second == capsule) {
		live_handles.erase(existing);
	}
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
const char* capsule_name();

template<> const char* capsule_name<SDL_Window>() { return "tauon_native.Window"; }
template<> const char* capsule_name<SDL_Renderer>() { return "tauon_native.Renderer"; }
template<> const char* capsule_name<SDL_Texture>() { return "tauon_native.Texture"; }
template<> const char* capsule_name<SDL_Cursor>() { return "tauon_native.Cursor"; }
template<> const char* capsule_name<SDL_Tray>() { return "tauon_native.Tray"; }
template<> const char* capsule_name<SDL_TrayMenu>() { return "tauon_native.TrayMenu"; }
template<> const char* capsule_name<SDL_TrayEntry>() { return "tauon_native.TrayEntry"; }
template<> const char* capsule_name<SDL_GLContextState>() { return "tauon_native.GLContext"; }

template<typename T>
T* pointer_from_python(PyObject* value, const char* name, bool allow_none = false) {
	if (value == Py_None && allow_none) {
		return nullptr;
	}
	if (!PyCapsule_CheckExact(value)) {
		PyErr_Format(PyExc_TypeError, "%s must be an opaque native handle", name);
		return nullptr;
	}
	void* pointer = PyCapsule_GetPointer(value, capsule_name<T>());
	if (pointer == nullptr && !PyErr_Occurred() && !allow_none) {
		PyErr_Format(PyExc_ValueError, "%s handle is null", name);
	}
	return static_cast<T*>(pointer);
}

template<typename T>
PyObject* pointer_to_python(T* pointer) {
	if (pointer == nullptr) {
		Py_RETURN_NONE;
	}
	const auto existing = live_handles.find(pointer);
	if (existing != live_handles.end()) {
		if (std::strcmp(PyCapsule_GetName(existing->second), capsule_name<T>()) == 0) {
			return Py_NewRef(existing->second);
		}
		// SDL freed the old object implicitly and reused its address
		live_handles.erase(existing);
	}
	PyObject* capsule = PyCapsule_New(pointer, capsule_name<T>(), forget_handle);
	if (capsule != nullptr) {
		live_handles[pointer] = capsule;
	}
	return capsule;
}

PyObject* invalidate_handle(PyObject* value) {
	if (value == Py_None) Py_RETURN_NONE;
	forget_handle(value);
	if (PyCapsule_SetName(value, kDestroyedName) != 0) return nullptr;
	Py_RETURN_NONE;
}

// Handles to objects SDL frees along with their owner
void invalidate_handles_named(const char* name) {
	for (auto entry = live_handles.begin(); entry != live_handles.end();) {
		if (std::strcmp(PyCapsule_GetName(entry->second), name) == 0) {
			PyCapsule_SetName(entry->second, kDestroyedName);
			entry = live_handles.erase(entry);
		} else {
			++entry;
		}
	}
}

void python_tray_callback(void* userdata, SDL_TrayEntry* entry) {
	PyObject* callback = static_cast<PyObject*>(userdata);
	if (callback == nullptr) return;
	const PyGILState_STATE gil_state = PyGILState_Ensure();
	PyObject* entry_handle = pointer_to_python(entry);
	PyObject* result = entry_handle != nullptr
		? PyObject_CallFunctionObjArgs(callback, Py_None, entry_handle, nullptr)
		: nullptr;
	Py_XDECREF(entry_handle);
	if (result == nullptr) {
		PyErr_WriteUnraisable(callback);
	} else {
		Py_DECREF(result);
	}
	PyGILState_Release(gil_state);
}


template<typename Rectangle, typename Convert>
bool parse_rectangle(PyObject* value, Rectangle& rectangle, Convert convert) {
	PyObject* sequence = PySequence_Fast(value, "rectangle must be a four-item sequence");
	PyObject* components[4]{};
	bool owns_components = false;
	if (sequence != nullptr && PySequence_Fast_GET_SIZE(sequence) == 4) {
		for (int index = 0; index < 4; ++index) {
			components[index] = PySequence_Fast_GET_ITEM(sequence, index);
		}
	} else {
		Py_XDECREF(sequence);
		sequence = nullptr;
		PyErr_Clear();
		constexpr const char* names[] = {"x", "y", "w", "h"};
		owns_components = true;
		for (int index = 0; index < 4; ++index) {
			components[index] = PyObject_GetAttrString(value, names[index]);
			if (components[index] == nullptr) {
				for (int cleanup = 0; cleanup < index; ++cleanup) Py_DECREF(components[cleanup]);
				PyErr_SetString(PyExc_TypeError, "rectangle must provide x, y, w and h");
				return false;
			}
		}
	}

	rectangle.x = static_cast<decltype(rectangle.x)>(convert(components[0]));
	rectangle.y = static_cast<decltype(rectangle.y)>(convert(components[1]));
	rectangle.w = static_cast<decltype(rectangle.w)>(convert(components[2]));
	rectangle.h = static_cast<decltype(rectangle.h)>(convert(components[3]));
	if (owns_components) {
		for (PyObject* component : components) Py_DECREF(component);
	}
	Py_XDECREF(sequence);
	return !PyErr_Occurred();
}

bool parse_frect(PyObject* value, SDL_FRect& rectangle) {
	return parse_rectangle(value, rectangle, PyFloat_AsDouble);
}

bool parse_rect(PyObject* value, SDL_Rect& rectangle) {
	return parse_rectangle(value, rectangle, PyLong_AsLong);
}

// SDL reports failure through its return value and SDL_GetError(), and
// Tauon's UI checks those return values (many failures, such as unsupported
// window opacity on some compositors, are harmless). Mirror that convention
// instead of raising. Invalid handles and arguments still raise.
PyObject* sdl_result(bool success) {
	return PyBool_FromLong(success ? 1 : 0);
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
	SDL_Texture* texture = nullptr;
	TAUON_WITHOUT_GIL(texture = SDL_CreateTexture(renderer, static_cast<SDL_PixelFormat>(format),
		static_cast<SDL_TextureAccess>(access), width, height));
	return pointer_to_python(texture);
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
	SDL_Texture* texture = nullptr;
	TAUON_WITHOUT_GIL(
		SDL_Surface* surface = SDL_CreateSurfaceFrom(width, height, SDL_PIXELFORMAT_RGBA32, pixels.buf, width * 4);
		texture = surface != nullptr ? SDL_CreateTextureFromSurface(renderer, surface) : nullptr;
		SDL_DestroySurface(surface)
	);
	PyBuffer_Release(&pixels);
	return pointer_to_python(texture);
}

PyObject* native_destroy_texture(PyObject*, PyObject* value) {
	SDL_Texture* texture = pointer_from_python<SDL_Texture>(value, "texture", true);
	if (PyErr_Occurred()) {
		return nullptr;
	}
	SDL_DestroyTexture(texture);
	return invalidate_handle(value);
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
	// SDL reads every row of the region from the buffer, so a short buffer
	// would upload whatever memory follows it. A negative pitch would read
	// before it, and planar formats need a per-plane size check.
	const auto format = static_cast<SDL_PixelFormat>(SDL_GetNumberProperty(
		SDL_GetTextureProperties(texture), SDL_PROP_TEXTURE_FORMAT_NUMBER, SDL_PIXELFORMAT_UNKNOWN));
	if (pitch < 0 || SDL_ISPIXELFORMAT_FOURCC(format)) {
		PyBuffer_Release(&pixels);
		PyErr_SetString(PyExc_ValueError, "texture updates need a non-negative pitch and a packed pixel format");
		return nullptr;
	}
	int width = rectangle.w;
	int height = rectangle.h;
	if (rectangle_pointer == nullptr) {
		float texture_width = 0;
		float texture_height = 0;
		SDL_GetTextureSize(texture, &texture_width, &texture_height);
		width = static_cast<int>(texture_width);
		height = static_cast<int>(texture_height);
	}
	if (width > 0 && height > 0) {
		const Py_ssize_t required = static_cast<Py_ssize_t>(height - 1) * pitch
			+ static_cast<Py_ssize_t>(width) * SDL_BYTESPERPIXEL(format);
		if (pixels.len < required) {
			PyErr_Format(PyExc_ValueError, "pixel buffer has %zd bytes, but the update needs %zd", pixels.len, required);
			PyBuffer_Release(&pixels);
			return nullptr;
		}
	}
	bool success = false;
	TAUON_WITHOUT_GIL(success = SDL_UpdateTexture(texture, rectangle_pointer, pixels.buf, pitch));
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
	SDL_Window* window = nullptr;
	TAUON_WITHOUT_GIL(window = SDL_CreatePopupWindow(parent, x, y, width, height, static_cast<SDL_WindowFlags>(flags)));
	return pointer_to_python(window);
}

PyObject* native_create_window(PyObject*, PyObject* args) {
	const char* title = nullptr;
	int width = 0;
	int height = 0;
	unsigned long long flags = 0;
	if (!PyArg_ParseTuple(args, "siiK", &title, &width, &height, &flags)) return nullptr;
	SDL_Window* window = nullptr;
	TAUON_WITHOUT_GIL(window = SDL_CreateWindow(title, width, height, static_cast<SDL_WindowFlags>(flags)));
	return pointer_to_python(window);
}

PyObject* native_create_renderer(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	const char* name = nullptr;
	if (!PyArg_ParseTuple(args, "Oz", &window_value, &name)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	if (window == nullptr) return nullptr;
	SDL_Renderer* renderer = nullptr;
	TAUON_WITHOUT_GIL(renderer = SDL_CreateRenderer(window, name));
	return pointer_to_python(renderer);
}

PyObject* native_destroy_renderer(PyObject*, PyObject* value) {
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(value, "renderer", true);
	if (PyErr_Occurred()) return nullptr;
	if (renderer != nullptr && renderer == launcher_renderer) {
		PyErr_SetString(PyExc_ValueError, "the main renderer belongs to the launcher");
		return nullptr;
	}
	TAUON_WITHOUT_GIL(SDL_DestroyRenderer(renderer));
	return invalidate_handle(value);
}

PyObject* native_destroy_window(PyObject*, PyObject* value) {
	SDL_Window* window = pointer_from_python<SDL_Window>(value, "window", true);
	if (PyErr_Occurred()) return nullptr;
	if (window != nullptr && window == launcher_window) {
		PyErr_SetString(PyExc_ValueError, "the main window belongs to the launcher");
		return nullptr;
	}
	TAUON_WITHOUT_GIL(SDL_DestroyWindow(window));
	return invalidate_handle(value);
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
	if (pixels) {
		SDL_GetWindowSizeInPixels(window, &width, &height);
	} else {
		SDL_GetWindowSize(window, &width, &height);
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
	TAUON_WITHOUT_GIL(SDL_RenderPresent(renderer));
	Py_RETURN_NONE;
}

PyObject* native_get_render_scale(PyObject*, PyObject* value) {
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(value, "renderer");
	if (renderer == nullptr) return nullptr;
	float scale_x = 0.0F;
	float scale_y = 0.0F;
	if (!SDL_GetRenderScale(renderer, &scale_x, &scale_y)) return sdl_result(false);
	return Py_BuildValue("(ff)", scale_x, scale_y);
}

PyObject* native_set_render_scale(PyObject*, PyObject* args) {
	PyObject* renderer_value = nullptr;
	float scale_x = 0.0F;
	float scale_y = 0.0F;
	if (!PyArg_ParseTuple(args, "Off", &renderer_value, &scale_x, &scale_y)) return nullptr;
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(renderer_value, "renderer");
	if (renderer == nullptr) return nullptr;
	return sdl_result(SDL_SetRenderScale(renderer, scale_x, scale_y));
}

PyObject* native_get_error(PyObject*, PyObject*) {
	return PyUnicode_FromString(SDL_GetError());
}

PyObject* native_clear_error(PyObject*, PyObject*) {
	SDL_ClearError();
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
	SDL_GetTextureSize(texture, &width, &height);
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
	// Non-positive sizes fall through to SDL, which rejects them
	if (width > 0 && height > 0) {
		const Py_ssize_t row_size = static_cast<Py_ssize_t>(width) * 4;
		if (pitch < row_size || pixels.len < static_cast<Py_ssize_t>(height - 1) * pitch + row_size) {
			PyBuffer_Release(&pixels);
			PyErr_SetString(PyExc_ValueError, "pixel buffer is smaller than its pitch, width and height need");
			return nullptr;
		}
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
			Py_RETURN_NONE;
		}
	}
	SDL_Texture* texture = nullptr;
	if (surface != nullptr) {
		TAUON_WITHOUT_GIL(texture = SDL_CreateTextureFromSurface(renderer, surface));
	}
	SDL_DestroySurface(surface);
	PyBuffer_Release(&pixels);
	return pointer_to_python(texture);
}

PyObject* native_read_render_pixels(PyObject*, PyObject* args) {
	PyObject* renderer_value = nullptr;
	PyObject* rectangle_value = nullptr;
	int alpha = 0;
	if (!PyArg_ParseTuple(args, "OOp", &renderer_value, &rectangle_value, &alpha)) return nullptr;
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(renderer_value, "renderer");
	SDL_Rect rectangle{};
	if (renderer == nullptr || !parse_rect(rectangle_value, rectangle)) return nullptr;
	SDL_Surface* raw = nullptr;
	TAUON_WITHOUT_GIL(raw = SDL_RenderReadPixels(renderer, &rectangle));
	if (raw == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	const SDL_PixelFormat format = alpha ? SDL_PIXELFORMAT_ARGB8888 : SDL_PIXELFORMAT_XRGB8888;
	SDL_Surface* surface = raw;
	if (raw->format != format) {
		TAUON_WITHOUT_GIL(surface = SDL_ConvertSurface(raw, format));
	}
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
	SDL_GetWindowPosition(window, &x, &y);
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
	return pointer_to_python(cursor);
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
	if (width > 0 && height > 0 && pixels.len < static_cast<Py_ssize_t>(width) * height * 4) {
		PyBuffer_Release(&pixels);
		PyErr_SetString(PyExc_ValueError, "ARGB buffer is smaller than width * height * 4");
		return nullptr;
	}
	SDL_Surface* surface = SDL_CreateSurfaceFrom(width, height, SDL_PIXELFORMAT_ARGB8888, pixels.buf, width * 4);
	SDL_Cursor* cursor = surface != nullptr ? SDL_CreateColorCursor(surface, hot_x, hot_y) : nullptr;
	SDL_DestroySurface(surface);
	PyBuffer_Release(&pixels);
	return pointer_to_python(cursor);
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
		Py_RETURN_FALSE;
	}
	PyObject* replacement = callback == Py_None ? nullptr : callback;
	Py_XINCREF(replacement);
	Py_XDECREF(hit_test_callback);
	hit_test_callback = replacement;
	Py_RETURN_TRUE;
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
	SDL_Tray* tray = nullptr;
	if (surface != nullptr) {
		TAUON_WITHOUT_GIL(tray = SDL_CreateTray(surface, tooltip));
	}
	SDL_DestroySurface(surface);
	PyBuffer_Release(&pixels);
	if (PyErr_Occurred()) {
		return nullptr;
	}
	return pointer_to_python(tray);
}

PyObject* native_set_tray_icon(PyObject*, PyObject* args) {
	PyObject* tray_value = nullptr;
	int width = 0;
	int height = 0;
	Py_buffer pixels{};
	if (!PyArg_ParseTuple(args, "Oiiy*", &tray_value, &width, &height, &pixels)) return nullptr;
	SDL_Tray* tray = pointer_from_python<SDL_Tray>(tray_value, "tray");
	SDL_Surface* surface = tray != nullptr ? surface_from_rgba(width, height, pixels) : nullptr;
	if (surface != nullptr) TAUON_WITHOUT_GIL(SDL_SetTrayIcon(tray, surface));
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
	return pointer_to_python(menu);
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
	return pointer_to_python(entry);
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
	TAUON_WITHOUT_GIL(SDL_DestroyTray(tray));
	for (auto& item : tray_callbacks) Py_DECREF(item.second);
	tray_callbacks.clear();
	invalidate_handles_named(capsule_name<SDL_TrayMenu>());
	invalidate_handles_named(capsule_name<SDL_TrayEntry>());
	return invalidate_handle(value);
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
	if (PyErr_Occurred()) {
		return nullptr;
	}
	return sdl_result(success);
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

#if defined(_WIN32)
// Taskbar thumbnail toolbar: buttons under the window's taskbar preview.
// Windows only allows adding them once per taskbar button, so the button set
// is kept here and re-added whenever Explorer recreates the taskbar button.
struct ThumbButton {
	UINT id = 0;
	HICON icon = nullptr;
	std::wstring tooltip;
	bool enabled = true;
};

struct ThumbBar {
	HWND hwnd = nullptr;
	WNDPROC previous_proc = nullptr;
	ITaskbarList3* taskbar = nullptr;
	UINT button_created_message = 0;
	bool added = false;
	bool com_initialized = false;
	PyObject* callback = nullptr;
	std::vector<ThumbButton> buttons;
};

ThumbBar thumbbar;

void destroy_thumb_icons(std::vector<ThumbButton>& buttons) {
	for (ThumbButton& button : buttons) {
		if (button.icon != nullptr) DestroyIcon(button.icon);
		button.icon = nullptr;
	}
}

HICON icon_from_rgba(int width, int height, const std::uint8_t* rgba) {
	BITMAPV5HEADER header{};
	header.bV5Size = sizeof(header);
	header.bV5Width = width;
	header.bV5Height = -height;  // top-down
	header.bV5Planes = 1;
	header.bV5BitCount = 32;
	header.bV5Compression = BI_BITFIELDS;
	header.bV5RedMask = 0x00FF0000;
	header.bV5GreenMask = 0x0000FF00;
	header.bV5BlueMask = 0x000000FF;
	header.bV5AlphaMask = 0xFF000000;
	void* bits = nullptr;
	HDC screen = GetDC(nullptr);
	HBITMAP color = CreateDIBSection(screen, reinterpret_cast<BITMAPINFO*>(&header), DIB_RGB_COLORS, &bits, nullptr, 0);
	ReleaseDC(nullptr, screen);
	if (color == nullptr) return nullptr;
	auto* out = static_cast<std::uint8_t*>(bits);
	for (int i = 0; i < width * height; ++i) {
		out[i * 4 + 0] = rgba[i * 4 + 2];
		out[i * 4 + 1] = rgba[i * 4 + 1];
		out[i * 4 + 2] = rgba[i * 4 + 0];
		out[i * 4 + 3] = rgba[i * 4 + 3];
	}
	HBITMAP mask = CreateBitmap(width, height, 1, 1, nullptr);
	ICONINFO info{};
	info.fIcon = TRUE;
	info.hbmMask = mask;
	info.hbmColor = color;
	HICON icon = mask != nullptr ? CreateIconIndirect(&info) : nullptr;
	DeleteObject(color);
	if (mask != nullptr) DeleteObject(mask);
	return icon;
}

// Adds the buttons the first time, updates them after that
void thumbbar_apply() {
	if (thumbbar.taskbar == nullptr || thumbbar.buttons.empty()) return;
	std::vector<THUMBBUTTON> native(thumbbar.buttons.size());
	for (std::size_t i = 0; i < thumbbar.buttons.size(); ++i) {
		const ThumbButton& button = thumbbar.buttons[i];
		THUMBBUTTON& item = native[i];
		item.dwMask = static_cast<THUMBBUTTONMASK>(THB_ICON | THB_TOOLTIP | THB_FLAGS);
		item.iId = button.id;
		item.hIcon = button.icon;
		wcsncpy(item.szTip, button.tooltip.c_str(), std::size(item.szTip) - 1);
		item.dwFlags = button.enabled ? THBF_ENABLED : THBF_DISABLED;
	}
	const UINT count = static_cast<UINT>(native.size());
	if (!thumbbar.added) {
		// Fails until the taskbar button exists; TaskbarButtonCreated retries
		thumbbar.added = SUCCEEDED(thumbbar.taskbar->ThumbBarAddButtons(thumbbar.hwnd, count, native.data()));
	} else {
		thumbbar.taskbar->ThumbBarUpdateButtons(thumbbar.hwnd, count, native.data());
	}
}

LRESULT CALLBACK thumbbar_window_proc(HWND hwnd, UINT message, WPARAM wparam, LPARAM lparam) {
	if (thumbbar.button_created_message != 0 && message == thumbbar.button_created_message) {
		// A new taskbar button (first show, or Explorer restarted) has no thumbnail buttons
		const LRESULT result = CallWindowProcW(thumbbar.previous_proc, hwnd, message, wparam, lparam);
		thumbbar.added = false;
		thumbbar_apply();
		return result;
	}
	if (message == WM_COMMAND && HIWORD(wparam) == THBN_CLICKED && thumbbar.callback != nullptr) {
		const PyGILState_STATE gil_state = PyGILState_Ensure();
		PyObject* result = PyObject_CallFunction(thumbbar.callback, "i", static_cast<int>(LOWORD(wparam)));
		if (result == nullptr) {
			PyErr_WriteUnraisable(thumbbar.callback);
		} else {
			Py_DECREF(result);
		}
		PyGILState_Release(gil_state);
		return 0;
	}
	return CallWindowProcW(thumbbar.previous_proc, hwnd, message, wparam, lparam);
}

HWND window_hwnd(SDL_Window* window) {
	return static_cast<HWND>(SDL_GetPointerProperty(SDL_GetWindowProperties(window), SDL_PROP_WINDOW_WIN32_HWND_POINTER, nullptr));
}

std::wstring wide_from_utf8(const char* text) {
	const int length = MultiByteToWideChar(CP_UTF8, 0, text, -1, nullptr, 0);
	if (length <= 1) return {};
	std::wstring result(static_cast<std::size_t>(length - 1), L'\0');
	MultiByteToWideChar(CP_UTF8, 0, text, -1, result.data(), length);
	return result;
}

void thumbbar_release() {
	if (thumbbar.hwnd != nullptr && thumbbar.previous_proc != nullptr
		&& GetWindowLongPtrW(thumbbar.hwnd, GWLP_WNDPROC) == reinterpret_cast<LONG_PTR>(thumbbar_window_proc)) {
		SetWindowLongPtrW(thumbbar.hwnd, GWLP_WNDPROC, reinterpret_cast<LONG_PTR>(thumbbar.previous_proc));
	}
	if (thumbbar.taskbar != nullptr) thumbbar.taskbar->Release();
	destroy_thumb_icons(thumbbar.buttons);
	Py_CLEAR(thumbbar.callback);
	if (thumbbar.com_initialized) CoUninitialize();
	thumbbar = ThumbBar{};
}

// thumbbar_create(window, callback) -> bool; callback(button_id) runs on the main thread
PyObject* native_thumbbar_create(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	PyObject* callback = nullptr;
	if (!PyArg_ParseTuple(args, "OO", &window_value, &callback)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	if (window == nullptr) return nullptr;
	if (!PyCallable_Check(callback)) {
		PyErr_SetString(PyExc_TypeError, "thumbbar callback must be callable");
		return nullptr;
	}
	if (thumbbar.hwnd != nullptr) Py_RETURN_TRUE;
	HWND hwnd = window_hwnd(window);
	if (hwnd == nullptr) Py_RETURN_FALSE;

	const HRESULT init = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
	thumbbar.com_initialized = SUCCEEDED(init);
	ITaskbarList3* taskbar = nullptr;
	if (FAILED(CoCreateInstance(CLSID_TaskbarList, nullptr, CLSCTX_INPROC_SERVER, IID_ITaskbarList3,
			reinterpret_cast<void**>(&taskbar))) || FAILED(taskbar->HrInit())) {
		if (taskbar != nullptr) taskbar->Release();
		thumbbar_release();
		Py_RETURN_FALSE;
	}
	thumbbar.hwnd = hwnd;
	thumbbar.taskbar = taskbar;
	thumbbar.button_created_message = RegisterWindowMessageW(L"TaskbarButtonCreated");
	// Let Explorer reach us even if Tauon runs elevated
	ChangeWindowMessageFilterEx(hwnd, thumbbar.button_created_message, MSGFLT_ALLOW, nullptr);
	ChangeWindowMessageFilterEx(hwnd, WM_COMMAND, MSGFLT_ALLOW, nullptr);
	Py_INCREF(callback);
	thumbbar.callback = callback;
	thumbbar.previous_proc = reinterpret_cast<WNDPROC>(
		SetWindowLongPtrW(hwnd, GWLP_WNDPROC, reinterpret_cast<LONG_PTR>(thumbbar_window_proc)));
	if (thumbbar.previous_proc == nullptr) {
		thumbbar_release();
		Py_RETURN_FALSE;
	}
	Py_RETURN_TRUE;
}

// thumbbar_set_buttons([(id, width, height, rgba, tooltip, enabled), ...])
// The number of buttons must stay the same after the first call.
PyObject* native_thumbbar_set_buttons(PyObject*, PyObject* value) {
	if (thumbbar.taskbar == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, "thumbbar_create has not succeeded");
		return nullptr;
	}
	PyObject* sequence = PySequence_Fast(value, "buttons must be a sequence");
	if (sequence == nullptr) return nullptr;
	const Py_ssize_t count = PySequence_Fast_GET_SIZE(sequence);
	if (count < 1 || count > 7) {
		Py_DECREF(sequence);
		PyErr_SetString(PyExc_ValueError, "the taskbar allows 1 to 7 thumbnail buttons");
		return nullptr;
	}
	std::vector<ThumbButton> buttons;
	for (Py_ssize_t i = 0; i < count; ++i) {
		unsigned int id = 0;
		int width = 0;
		int height = 0;
		Py_buffer pixels{};
		const char* tooltip = nullptr;
		int enabled = 1;
		if (!PyArg_ParseTuple(PySequence_Fast_GET_ITEM(sequence, i), "Iiiy*sp", &id, &width, &height, &pixels, &tooltip, &enabled)) {
			destroy_thumb_icons(buttons);
			Py_DECREF(sequence);
			return nullptr;
		}
		if (width <= 0 || height <= 0 || pixels.len < static_cast<Py_ssize_t>(width) * height * 4) {
			PyBuffer_Release(&pixels);
			destroy_thumb_icons(buttons);
			Py_DECREF(sequence);
			PyErr_SetString(PyExc_ValueError, "RGBA buffer is smaller than width * height * 4");
			return nullptr;
		}
		ThumbButton button;
		button.id = id;
		button.icon = icon_from_rgba(width, height, static_cast<const std::uint8_t*>(pixels.buf));
		button.tooltip = wide_from_utf8(tooltip);
		button.enabled = enabled != 0;
		PyBuffer_Release(&pixels);
		buttons.push_back(std::move(button));
	}
	Py_DECREF(sequence);
	if (!thumbbar.buttons.empty() && buttons.size() != thumbbar.buttons.size()) {
		destroy_thumb_icons(buttons);
		PyErr_SetString(PyExc_ValueError, "the number of thumbnail buttons cannot change");
		return nullptr;
	}
	// The taskbar copies the icons, so the old ones can go once it has the new ones
	std::vector<ThumbButton> old = std::move(thumbbar.buttons);
	thumbbar.buttons = std::move(buttons);
	thumbbar_apply();
	destroy_thumb_icons(old);
	return PyBool_FromLong(thumbbar.added ? 1 : 0);
}

PyObject* native_thumbbar_icon_size(PyObject*, PyObject* value) {
	SDL_Window* window = pointer_from_python<SDL_Window>(value, "window");
	if (window == nullptr) return nullptr;
	HWND hwnd = window_hwnd(window);
	const UINT dpi = hwnd != nullptr ? GetDpiForWindow(hwnd) : 96;
	return PyLong_FromLong(GetSystemMetricsForDpi(SM_CXSMICON, dpi != 0 ? dpi : 96));
}

PyObject* native_thumbbar_destroy(PyObject*, PyObject*) {
	thumbbar_release();
	Py_RETURN_NONE;
}
#endif

PyObject* native_video_driver(PyObject*, PyObject*) {
	const char* driver = SDL_GetCurrentVideoDriver();
	if (driver == nullptr) Py_RETURN_NONE;
	return PyUnicode_FromString(driver);
}

PyObject* native_flush_renderer(PyObject*, PyObject* value) {
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(value, "renderer");
	if (renderer == nullptr) return nullptr;
	bool success = false;
	TAUON_WITHOUT_GIL(success = SDL_FlushRenderer(renderer));
	return sdl_result(success);
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
	SDL_GLContext context = nullptr;
	TAUON_WITHOUT_GIL(context = SDL_GL_CreateContext(window));
	return pointer_to_python(context);
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

PyObject* rect_to_python(const SDL_Rect& rectangle) {
	return Py_BuildValue("(iiii)", rectangle.x, rectangle.y, rectangle.w, rectangle.h);
}

PyObject* native_get_display_bounds(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	int usable = 0;
	if (!PyArg_ParseTuple(args, "Op", &window_value, &usable)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	if (window == nullptr) return nullptr;
	const SDL_DisplayID display = SDL_GetDisplayForWindow(window);
	SDL_Rect bounds{};
	if (display == 0 || !(usable ? SDL_GetDisplayUsableBounds(display, &bounds) : SDL_GetDisplayBounds(display, &bounds))) {
		Py_RETURN_NONE;
	}
	return rect_to_python(bounds);
}

PyObject* native_get_render_clip_rect(PyObject*, PyObject* value) {
	SDL_Renderer* renderer = pointer_from_python<SDL_Renderer>(value, "renderer");
	if (renderer == nullptr) return nullptr;
	SDL_Rect clip{};
	if (!SDL_RenderClipEnabled(renderer) || !SDL_GetRenderClipRect(renderer, &clip)) {
		Py_RETURN_NONE;
	}
	return rect_to_python(clip);
}

PyObject* native_set_window_fullscreen_desktop_mode(PyObject*, PyObject* value) {
	SDL_Window* window = pointer_from_python<SDL_Window>(value, "window");
	if (window == nullptr) return nullptr;
	return sdl_result(SDL_SetWindowFullscreenMode(window, nullptr));
}

// Platform handles are exposed only for compositor integrations (background
// blur) that must call platform APIs on Tauon's own window.
PyObject* native_get_window_pointer_property(PyObject*, PyObject* args) {
	PyObject* window_value = nullptr;
	const char* name = nullptr;
	if (!PyArg_ParseTuple(args, "Os", &window_value, &name)) return nullptr;
	SDL_Window* window = pointer_from_python<SDL_Window>(window_value, "window");
	if (window == nullptr) return nullptr;
	void* pointer = SDL_GetPointerProperty(SDL_GetWindowProperties(window), name, nullptr);
	if (pointer == nullptr) Py_RETURN_NONE;
	return PyLong_FromVoidPtr(pointer);
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
	SDL_Texture* texture = nullptr;
	TAUON_WITHOUT_GIL(texture = SDL_CreateTextureWithProperties(renderer, properties));
	SDL_DestroyProperties(properties);
	return pointer_to_python(texture);
}

#define NATIVE_METHOD(name, function, flags) {name, function, flags, nullptr}

namespace {

PyMethodDef native_render_methods[] = {
	NATIVE_METHOD("create_texture", native_create_texture, METH_VARARGS),
	NATIVE_METHOD("create_texture_from_rgba", native_create_texture_from_rgba, METH_VARARGS),
	NATIVE_METHOD("destroy_texture", native_destroy_texture, METH_O),
	NATIVE_METHOD("get_render_target", native_get_render_target, METH_O),
	NATIVE_METHOD("set_render_target", native_set_render_target, METH_VARARGS),
	NATIVE_METHOD("set_render_draw_blend_mode", native_set_render_draw_blend_mode, METH_VARARGS),
	NATIVE_METHOD("set_render_draw_color", native_set_render_draw_color, METH_VARARGS),
	NATIVE_METHOD("render_clear", native_render_clear, METH_O),
	NATIVE_METHOD("render_fill_rect", native_render_fill_rect, METH_VARARGS),
	NATIVE_METHOD("render_texture", native_render_texture, METH_VARARGS),
	NATIVE_METHOD("set_texture_blend_mode", native_set_texture_blend_mode, METH_VARARGS),
	NATIVE_METHOD("set_texture_scale_mode", native_set_texture_scale_mode, METH_VARARGS),
	NATIVE_METHOD("set_texture_alpha_mod", native_set_texture_alpha_mod, METH_VARARGS),
	NATIVE_METHOD("update_texture", native_update_texture, METH_VARARGS),
	NATIVE_METHOD("set_render_clip_rect", native_set_render_clip_rect, METH_VARARGS),
	NATIVE_METHOD("get_window_flags", native_get_window_flags, METH_O),
	NATIVE_METHOD("maximize_window", native_maximize_window, METH_O),
	NATIVE_METHOD("minimize_window", native_minimize_window, METH_O),
	NATIVE_METHOD("restore_window", native_restore_window, METH_O),
	NATIVE_METHOD("render_geometry", native_render_geometry, METH_VARARGS),
	NATIVE_METHOD("create_popup_window", native_create_popup_window, METH_VARARGS),
	NATIVE_METHOD("create_window", native_create_window, METH_VARARGS),
	NATIVE_METHOD("create_renderer", native_create_renderer, METH_VARARGS),
	NATIVE_METHOD("destroy_renderer", native_destroy_renderer, METH_O),
	NATIVE_METHOD("destroy_window", native_destroy_window, METH_O),
	NATIVE_METHOD("get_window_id", native_get_window_id, METH_O),
	NATIVE_METHOD("get_window_size", native_get_window_size, METH_VARARGS),
	NATIVE_METHOD("set_window_size", native_set_window_size, METH_VARARGS),
	NATIVE_METHOD("set_window_position", native_set_window_position, METH_VARARGS),
	NATIVE_METHOD("set_window_mouse_grab", native_set_window_mouse_grab, METH_VARARGS),
	NATIVE_METHOD("capture_mouse", native_capture_mouse, METH_O),
	NATIVE_METHOD("show_window", native_show_window, METH_O),
	NATIVE_METHOD("hide_window", native_hide_window, METH_O),
	NATIVE_METHOD("raise_window", native_raise_window, METH_O),
	NATIVE_METHOD("render_present", native_render_present, METH_O),
	NATIVE_METHOD("get_render_scale", native_get_render_scale, METH_O),
	NATIVE_METHOD("set_render_scale", native_set_render_scale, METH_VARARGS),
	NATIVE_METHOD("get_error", native_get_error, METH_NOARGS),
	NATIVE_METHOD("clear_error", native_clear_error, METH_NOARGS),
	NATIVE_METHOD("render_line", native_render_line, METH_VARARGS),
	NATIVE_METHOD("get_texture_size", native_get_texture_size, METH_O),
	NATIVE_METHOD("create_texture_from_cairo", native_create_texture_from_cairo, METH_VARARGS),
	NATIVE_METHOD("read_render_pixels", native_read_render_pixels, METH_VARARGS),
	NATIVE_METHOD("compose_blend_mode", native_compose_blend_mode, METH_VARARGS),
	NATIVE_METHOD("set_window_minimum_size", native_set_window_minimum_size, METH_VARARGS),
	NATIVE_METHOD("set_window_resizable", native_set_window_resizable, METH_VARARGS),
	NATIVE_METHOD("set_window_bordered", native_set_window_bordered, METH_VARARGS),
	NATIVE_METHOD("set_window_opacity", native_set_window_opacity, METH_VARARGS),
	NATIVE_METHOD("set_window_always_on_top", native_set_window_always_on_top, METH_VARARGS),
	NATIVE_METHOD("set_window_title", native_set_window_title, METH_VARARGS),
	NATIVE_METHOD("set_window_fullscreen", native_set_window_fullscreen, METH_VARARGS),
	NATIVE_METHOD("sync_window", native_sync_window, METH_O),
	NATIVE_METHOD("get_window_position", native_get_window_position, METH_O),
	NATIVE_METHOD("get_mouse_state", native_get_mouse_state, METH_O),
	NATIVE_METHOD("set_texture_color_mod", native_set_texture_color_mod, METH_VARARGS),
	NATIVE_METHOD("create_system_cursor", native_create_system_cursor, METH_O),
	NATIVE_METHOD("set_cursor", native_set_cursor, METH_O),
	NATIVE_METHOD("create_color_cursor", native_create_color_cursor, METH_VARARGS),
	NATIVE_METHOD("set_window_hit_test", native_set_window_hit_test, METH_VARARGS),
	NATIVE_METHOD("start_text_input", native_start_text_input, METH_O),
	NATIVE_METHOD("stop_text_input", native_stop_text_input, METH_O),
	NATIVE_METHOD("set_text_input_area", native_set_text_input_area, METH_VARARGS),
	NATIVE_METHOD("get_display_refresh_rate", native_get_display_refresh_rate, METH_O),
	NATIVE_METHOD("create_tray", native_create_tray, METH_VARARGS),
	NATIVE_METHOD("set_tray_icon", native_set_tray_icon, METH_VARARGS),
	NATIVE_METHOD("set_tray_tooltip", native_set_tray_tooltip, METH_VARARGS),
	NATIVE_METHOD("create_tray_menu", native_create_tray_menu, METH_O),
	NATIVE_METHOD("insert_tray_entry", native_insert_tray_entry, METH_VARARGS),
	NATIVE_METHOD("set_tray_entry_callback", native_set_tray_entry_callback, METH_VARARGS),
	NATIVE_METHOD("destroy_tray", native_destroy_tray, METH_O),
	NATIVE_METHOD("set_window_icon", native_set_window_icon, METH_VARARGS),
	NATIVE_METHOD("set_window_progress_state", native_set_window_progress_state, METH_VARARGS),
	NATIVE_METHOD("set_window_progress_value", native_set_window_progress_value, METH_VARARGS),
	NATIVE_METHOD("video_driver", native_video_driver, METH_NOARGS),
	NATIVE_METHOD("flush_renderer", native_flush_renderer, METH_O),
	NATIVE_METHOD("render_texture_rotated", native_render_texture_rotated, METH_VARARGS),
	NATIVE_METHOD("gl_get_current_context", native_gl_get_current_context, METH_NOARGS),
	NATIVE_METHOD("gl_set_attribute", native_gl_set_attribute, METH_VARARGS),
	NATIVE_METHOD("gl_create_context", native_gl_create_context, METH_O),
	NATIVE_METHOD("gl_make_current", native_gl_make_current, METH_VARARGS),
	NATIVE_METHOD("create_texture_from_opengl", native_create_texture_from_opengl, METH_VARARGS),
	NATIVE_METHOD("get_display_bounds", native_get_display_bounds, METH_VARARGS),
	NATIVE_METHOD("get_render_clip_rect", native_get_render_clip_rect, METH_O),
	NATIVE_METHOD("set_window_fullscreen_desktop_mode", native_set_window_fullscreen_desktop_mode, METH_O),
	NATIVE_METHOD("get_window_pointer_property", native_get_window_pointer_property, METH_VARARGS),
#if defined(_WIN32)
	NATIVE_METHOD("thumbbar_create", native_thumbbar_create, METH_VARARGS),
	NATIVE_METHOD("thumbbar_set_buttons", native_thumbbar_set_buttons, METH_O),
	NATIVE_METHOD("thumbbar_icon_size", native_thumbbar_icon_size, METH_O),
	NATIVE_METHOD("thumbbar_destroy", native_thumbbar_destroy, METH_NOARGS),
#endif
	{nullptr, nullptr, 0, nullptr},
};

}  // namespace

PyObject* native_window_handle(SDL_Window* window) {
	return pointer_to_python(window);
}

PyObject* native_renderer_handle(SDL_Renderer* renderer) {
	return pointer_to_python(renderer);
}

void set_launcher_owned(SDL_Window* window, SDL_Renderer* renderer) {
	launcher_window = window;
	launcher_renderer = renderer;
}

int add_native_render_methods(PyObject* module) {
	return PyModule_AddFunctions(module, native_render_methods);
}

#undef NATIVE_METHOD
