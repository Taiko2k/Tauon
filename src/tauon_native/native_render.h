#pragma once

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <SDL3/SDL.h>

// Runs SDL work with the GIL released, as ctypes does for every foreign call,
// so Python worker threads (imports, tag scans) keep running while SDL blocks,
// for example in SDL_RenderPresent's vsync wait. The work must not touch
// Python objects.
#define TAUON_WITHOUT_GIL(...) \
	do { \
		Py_BEGIN_ALLOW_THREADS \
		__VA_ARGS__; \
		Py_END_ALLOW_THREADS \
	} while (false)

int add_native_render_methods(PyObject* module);

// Shared handles for the launcher's main window and renderer
PyObject* native_window_handle(SDL_Window* window);
PyObject* native_renderer_handle(SDL_Renderer* renderer);

// Python may use these but not destroy them
void set_launcher_owned(SDL_Window* window, SDL_Renderer* renderer);
