#pragma once

#define PY_SSIZE_T_CLEAN
#include <Python.h>

// Folder import walk: scan_folder, scan_folder_progress, cancel_scan_folder
int add_native_scan_methods(PyObject* module);
