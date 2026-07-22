#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "host_api.h"

#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <string_view>

namespace {

const TauonPythonHostContext* g_context = nullptr;

bool has_argument(int argc, char** argv, std::string_view wanted) {
	for (int index = 1; index < argc; ++index) {
		if (argv[index] != nullptr && wanted == argv[index]) {
			return true;
		}
	}
	return false;
}

PyObject* bridge_is_active(PyObject*, PyObject*) {
	return PyBool_FromLong(g_context != nullptr ? 1 : 0);
}

PyObject* bridge_window_address(PyObject*, PyObject*) {
	if (g_context == nullptr || g_context->window == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, "Tauon's native window is unavailable");
		return nullptr;
	}
	return PyLong_FromVoidPtr(g_context->window);
}

PyObject* bridge_renderer_address(PyObject*, PyObject*) {
	if (g_context == nullptr || g_context->renderer == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, "Tauon's native renderer is unavailable");
		return nullptr;
	}
	return PyLong_FromVoidPtr(g_context->renderer);
}

PyObject* bridge_sdl_library_path(PyObject*, PyObject*) {
	if (g_context == nullptr || g_context->sdl_library_path == nullptr || g_context->sdl_library_path[0] == '\0') {
		Py_RETURN_NONE;
	}
	return PyUnicode_DecodeFSDefault(g_context->sdl_library_path);
}

PyObject* bridge_user_data_directory(PyObject*, PyObject*) {
	if (g_context == nullptr || g_context->user_data_directory == nullptr || g_context->user_data_directory[0] == '\0') {
		PyErr_SetString(PyExc_RuntimeError, "Tauon's user data directory is unavailable");
		return nullptr;
	}
	return PyUnicode_DecodeFSDefault(g_context->user_data_directory);
}

PyMethodDef bridge_methods[] = {
	{"is_active", bridge_is_active, METH_NOARGS, "Return whether Tauon is running under the native bootstrap."},
	{"window_address", bridge_window_address, METH_NOARGS, "Return the transitional native SDL_Window address."},
	{"renderer_address", bridge_renderer_address, METH_NOARGS, "Return the transitional native SDL_Renderer address."},
	{"sdl_library_path", bridge_sdl_library_path, METH_NOARGS, "Return the SDL library used by the native executable."},
	{"user_data_directory", bridge_user_data_directory, METH_NOARGS, "Return Tauon's native-resolved user data directory."},
	{nullptr, nullptr, 0, nullptr},
};

PyModuleDef bridge_module = {
	PyModuleDef_HEAD_INIT,
	"tauon_native",
	"Bridge to Tauon's native SDL bootstrap.",
	-1,
	bridge_methods,
	nullptr,
	nullptr,
	nullptr,
	nullptr,
};

PyMODINIT_FUNC PyInit_tauon_native() {
	return PyModule_Create(&bridge_module);
}

std::filesystem::path source_directory() {
	if (const char* override_path = std::getenv("TAUON_PYTHONPATH")) {
		return std::filesystem::path(override_path);
	}
	return std::filesystem::path(g_context->source_directory);
}

std::filesystem::path python_site_packages_directory() {
	if (const char* override_path = std::getenv("TAUON_PYTHON_SITE_PACKAGES")) {
		return std::filesystem::path(override_path);
	}
	return std::filesystem::path(g_context->site_packages_directory);
}

bool prepend_python_path(const std::filesystem::path& directory) {
	if (directory.empty()) {
		return true;
	}
	PyObject* sys_path = PySys_GetObject("path");
	PyObject* path = PyUnicode_DecodeFSDefault(directory.string().c_str());
	if (sys_path == nullptr || path == nullptr) {
		Py_XDECREF(path);
		return false;
	}
	const int result = PyList_Insert(sys_path, 0, path);
	Py_DECREF(path);
	return result == 0;
}

int run_python(int argc, char** argv) {
	if (PyImport_AppendInittab("tauon_native", &PyInit_tauon_native) == -1) {
		std::cerr << "Tauon: failed to register the native Python bridge\n";
		return 1;
	}

	PyConfig config;
	PyConfig_InitPythonConfig(&config);
	config.parse_argv = 0;
	PyStatus status = PyConfig_SetBytesArgv(&config, argc, argv);
	if (!PyStatus_Exception(status)) {
		status = Py_InitializeFromConfig(&config);
	}
	PyConfig_Clear(&config);
	if (PyStatus_Exception(status)) {
		std::cerr << "Tauon: Python initialisation failed: "
			<< (status.err_msg != nullptr ? status.err_msg : "unknown error") << '\n';
		return 1;
	}

	int exit_code = 0;
	if (!prepend_python_path(python_site_packages_directory()) || !prepend_python_path(source_directory())) {
		PyErr_Print();
		exit_code = 1;
	} else if (has_argument(argc, argv, "--native-smoke-test")) {
		const char* smoke_test =
			"import ctypes\n"
			"import json\n"
			"from pathlib import Path\n"
			"import sdl3\n"
			"import tauon_native\n"
			"window = ctypes.cast(tauon_native.window_address(), ctypes.POINTER(sdl3.SDL_Window))\n"
			"renderer = ctypes.cast(tauon_native.renderer_address(), ctypes.POINTER(sdl3.SDL_Renderer))\n"
			"assert sdl3.SDL_GetWindowID(window) > 0\n"
			"assert sdl3.SDL_GetRendererName(renderer) is not None\n"
			"state_path = Path(tauon_native.user_data_directory()) / 'window-state.json'\n"
			"if state_path.is_file():\n"
			"    state = json.loads(state_path.read_text(encoding='utf-8'))\n"
			"    if not state.get('maximized', False):\n"
			"        width, height = ctypes.c_int(), ctypes.c_int()\n"
			"        assert sdl3.SDL_GetWindowSize(window, ctypes.byref(width), ctypes.byref(height))\n"
			"        assert (width.value, height.value) == (state['width'], state['height'])\n"
			"    borderless = bool(sdl3.SDL_GetWindowFlags(window) & sdl3.SDL_WINDOW_BORDERLESS)\n"
			"    assert borderless == state.get('borderless', True)\n";
		if (PyRun_SimpleString(smoke_test) != 0) {
			PyErr_Print();
			exit_code = 1;
		}
	} else {
		const char* launch_tauon =
			"import runpy\n"
			"runpy.run_module('tauon.__main__', run_name='__main__')\n";
		if (PyRun_SimpleString(launch_tauon) != 0) {
			PyErr_Print();
			exit_code = 1;
		}
	}
	if (Py_FinalizeEx() < 0 && exit_code == 0) {
		exit_code = 120;
	}
	return exit_code;
}

}  // namespace

TAUON_PYTHON_HOST_EXPORT int tauon_python_host_run(
	const TauonPythonHostContext* context,
	int argc,
	char** argv
) {
	if (context == nullptr || context->abi_version != TAUON_PYTHON_HOST_ABI_VERSION ||
		context->window == nullptr || context->renderer == nullptr ||
		context->source_directory == nullptr || context->site_packages_directory == nullptr) {
		std::cerr << "Tauon: invalid Python host context\n";
		return 1;
	}
	g_context = context;
	const int exit_code = run_python(argc, argv);
	g_context = nullptr;
	return exit_code;
}
