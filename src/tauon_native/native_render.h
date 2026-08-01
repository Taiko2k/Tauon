#pragma once

#define PY_SSIZE_T_CLEAN
#include <Python.h>

int add_native_render_methods(PyObject* module);
