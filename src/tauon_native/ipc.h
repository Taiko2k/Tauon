#pragma once

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <filesystem>
#include <string_view>

// Private channel from a launcher to the instance that owns a user data
// directory: a Unix socket inside that directory, or a named pipe on Windows.
// Only processes running as the same user can connect, in either direction.

// Sends one command, with an optional argument such as a path to open.
// Returns whether the running instance accepted it, reporting failures on stderr.
bool ipc_send(const std::filesystem::path& user_data_directory, std::string_view command, std::string_view argument = {});

// Serves requests on a background thread, calling handler(command, argument)
// with the GIL held. Call with the GIL held; sets a Python error on failure.
bool ipc_start_server(const std::filesystem::path& user_data_directory, PyObject* handler);

// Stops the server, if running. Call with the GIL held, before finalizing Python.
void ipc_stop_server();
