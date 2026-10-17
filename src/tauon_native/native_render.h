#pragma once

#define PY_SSIZE_T_CLEAN
#include <Python.h>

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
