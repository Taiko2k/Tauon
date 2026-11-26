#include "native_scan.h"

#include <atomic>
#include <cwchar>
#include <exception>
#include <filesystem>
#include <string>
#include <system_error>
#include <utility>
#include <vector>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <sys/stat.h>
#endif

namespace fs = std::filesystem;

namespace {

// Names stay in the platform's own form, as os.scandir keeps them: UTF-16 on
// Windows, raw bytes elsewhere. Nothing is transcoded until Python decodes it
#if defined(_WIN32)
using NativeString = std::wstring;
#define NATIVE_TEXT(text) L##text
#else
using NativeString = std::string;
#define NATIVE_TEXT(text) text
#endif

// Folder walks for imports. The walk holds no GIL, so other Python threads
// (UI, tag scanning) run freely, and the worker isn't slowed by reacquiring
// the GIL after every readdir and stat as os.scandir would be.

std::atomic<Py_ssize_t> scan_found{0};
std::atomic<bool> scan_cancelled{false};

constexpr int kMaxDepth = 256;

struct Node {
	NativeString name;
	std::vector<NativeString> files;
	std::vector<Node> folders;
};

struct ScanError {
	NativeString path;
	NativeString message;
	bool permission;
};

struct Walk {
	std::vector<ScanError> errors;
#if !defined(_WIN32)
	// Identities of the folders being walked, to stop at symlink loops
	std::vector<std::pair<dev_t, ino_t>> ancestors;
#endif
};

// Narrow text from the C++ runtime, such as exception messages
NativeString from_narrow(const std::string& text) {
#if defined(_WIN32)
	if (text.empty()) {
		return {};
	}
	const int length = MultiByteToWideChar(CP_ACP, 0, text.data(), static_cast<int>(text.size()), nullptr, 0);
	if (length <= 0) {
		return L"?";
	}
	std::wstring wide(static_cast<std::size_t>(length), L'\0');
	MultiByteToWideChar(CP_ACP, 0, text.data(), static_cast<int>(text.size()), wide.data(), length);
	return wide;
#else
	return text;
#endif
}

NativeString error_text(const std::error_code& error) {
#if defined(_WIN32)
	// Directory errors carry Win32 codes; ask for the message as UTF-16
	if (error.category() == std::system_category()) {
		wchar_t* buffer = nullptr;
		const DWORD length = FormatMessageW(
			FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
			nullptr, static_cast<DWORD>(error.value()), 0, reinterpret_cast<wchar_t*>(&buffer), 0, nullptr);
		if (length > 0 && buffer != nullptr) {
			std::wstring text(buffer, length);
			LocalFree(buffer);
			while (!text.empty() && (text.back() == L'\n' || text.back() == L'\r' || text.back() == L' ')) {
				text.pop_back();
			}
			return text;
		}
	}
#endif
	return from_narrow(error.message());
}

void record_error(Walk& walk, const fs::path& path, NativeString message, bool permission) {
	walk.errors.push_back({path.native(), std::move(message), permission});
}

void record_error(Walk& walk, const fs::path& path, const std::error_code& error) {
	const bool permission = error == std::errc::permission_denied || error == std::errc::operation_not_permitted;
	record_error(walk, path, error_text(error), permission);
}

// Types come from readdir where possible; only symlinks need a stat
fs::file_type entry_type(const fs::directory_entry& entry) {
	std::error_code error;
	if (entry.is_directory(error)) {
		return fs::file_type::directory;
	}
	if (error) {
		return fs::file_type::not_found;
	}
	if (entry.is_regular_file(error)) {
		return fs::file_type::regular;
	}
	return fs::file_type::unknown;
}

void walk_folder(Walk& walk, const fs::path& folder, Node& node, int depth) {
	if (depth > kMaxDepth) {
		record_error(walk, folder, NATIVE_TEXT("Folder nesting too deep"), false);
		return;
	}

#if !defined(_WIN32)
	struct stat info {};
	if (::stat(folder.c_str(), &info) == 0) {
		for (const auto& ancestor : walk.ancestors) {
			if (ancestor.first == info.st_dev && ancestor.second == info.st_ino) {
				return;
			}
		}
		walk.ancestors.emplace_back(info.st_dev, info.st_ino);
	} else {
		walk.ancestors.emplace_back(0, 0);
	}
#endif

	std::vector<std::pair<NativeString, fs::path>> subfolders;
	{
		// Scoped so the handle closes before recursing
		std::error_code error;
		fs::directory_iterator it(folder, error);
		if (error) {
			record_error(walk, folder, error);
		} else {
			const fs::directory_iterator end;
			while (it != end) {
				if (scan_cancelled.load(std::memory_order_relaxed)) {
					break;
				}
				const fs::directory_entry& entry = *it;
				NativeString name = entry.path().filename().native();
				if (!name.empty() && name[0] != NATIVE_TEXT('.')) {
					const fs::file_type type = entry_type(entry);
					if (type == fs::file_type::directory) {
						if (name != NATIVE_TEXT("__MACOSX")) {
							subfolders.emplace_back(std::move(name), entry.path());
						}
					} else if (type == fs::file_type::regular) {
						node.files.push_back(std::move(name));
						scan_found.fetch_add(1, std::memory_order_relaxed);
					}
				}
				it.increment(error);
				if (error) {
					record_error(walk, folder, error);
					break;
				}
			}
		}
	}

	node.folders.reserve(subfolders.size());
	for (auto& subfolder : subfolders) {
		if (scan_cancelled.load(std::memory_order_relaxed)) {
			break;
		}
		node.folders.push_back(Node{std::move(subfolder.first), {}, {}});
		walk_folder(walk, subfolder.second, node.folders.back(), depth + 1);
	}

#if !defined(_WIN32)
	walk.ancestors.pop_back();
#endif
}

// The same conversions os.scandir makes, so names match what Python sees
PyObject* decode_name(const NativeString& name) {
#if defined(_WIN32)
	return PyUnicode_FromWideChar(name.data(), static_cast<Py_ssize_t>(name.size()));
#else
	return PyUnicode_DecodeFSDefaultAndSize(name.data(), static_cast<Py_ssize_t>(name.size()));
#endif
}

PyObject* decode_message(const NativeString& message) {
#if defined(_WIN32)
	return PyUnicode_FromWideChar(message.data(), static_cast<Py_ssize_t>(message.size()));
#else
	return PyUnicode_DecodeUTF8(message.data(), static_cast<Py_ssize_t>(message.size()), "replace");
#endif
}

// Python path argument to native form, as os.fspath and os.fsencode would
bool encode_path(PyObject* argument, NativeString& out) {
#if defined(_WIN32)
	PyObject* text = PyOS_FSPath(argument);
	if (text == nullptr) {
		return false;
	}
	if (PyBytes_Check(text)) {
		PyObject* decoded = PyUnicode_DecodeFSDefaultAndSize(PyBytes_AS_STRING(text), PyBytes_GET_SIZE(text));
		Py_DECREF(text);
		if (decoded == nullptr) {
			return false;
		}
		text = decoded;
	}
	Py_ssize_t length = 0;
	wchar_t* wide = PyUnicode_AsWideCharString(text, &length);
	Py_DECREF(text);
	if (wide == nullptr) {
		return false;
	}
	if (std::wcslen(wide) != static_cast<std::size_t>(length)) {
		PyMem_Free(wide);
		PyErr_SetString(PyExc_ValueError, "embedded null character in path");
		return false;
	}
	out.assign(wide, static_cast<std::size_t>(length));
	PyMem_Free(wide);
	return true;
#else
	PyObject* encoded = nullptr;
	if (!PyUnicode_FSConverter(argument, &encoded)) {
		return false;
	}
	out.assign(PyBytes_AS_STRING(encoded), static_cast<std::size_t>(PyBytes_GET_SIZE(encoded)));
	Py_DECREF(encoded);
	return true;
#endif
}

PyObject* pack_pair(PyObject* first, PyObject* second) {
	if (first == nullptr || second == nullptr) {
		Py_XDECREF(first);
		Py_XDECREF(second);
		return nullptr;
	}
	PyObject* pair = PyTuple_Pack(2, first, second);
	Py_DECREF(first);
	Py_DECREF(second);
	return pair;
}

// (files, [(folder name, node), ...])
PyObject* node_to_python(const Node& node) {
	PyObject* files = PyList_New(static_cast<Py_ssize_t>(node.files.size()));
	if (files == nullptr) {
		return nullptr;
	}
	for (std::size_t i = 0; i < node.files.size(); ++i) {
		PyObject* name = decode_name(node.files[i]);
		if (name == nullptr) {
			Py_DECREF(files);
			return nullptr;
		}
		PyList_SET_ITEM(files, static_cast<Py_ssize_t>(i), name);
	}

	PyObject* folders = PyList_New(static_cast<Py_ssize_t>(node.folders.size()));
	if (folders == nullptr) {
		Py_DECREF(files);
		return nullptr;
	}
	for (std::size_t i = 0; i < node.folders.size(); ++i) {
		PyObject* child = pack_pair(decode_name(node.folders[i].name), node_to_python(node.folders[i]));
		if (child == nullptr) {
			Py_DECREF(files);
			Py_DECREF(folders);
			return nullptr;
		}
		PyList_SET_ITEM(folders, static_cast<Py_ssize_t>(i), child);
	}
	return pack_pair(files, folders);
}

PyObject* errors_to_python(const std::vector<ScanError>& errors) {
	PyObject* list = PyList_New(static_cast<Py_ssize_t>(errors.size()));
	if (list == nullptr) {
		return nullptr;
	}
	for (std::size_t i = 0; i < errors.size(); ++i) {
		const ScanError& error = errors[i];
		PyObject* path = decode_name(error.path);
		PyObject* message = decode_message(error.message);
		PyObject* item = nullptr;
		if (path != nullptr && message != nullptr) {
			item = PyTuple_Pack(3, path, message, error.permission ? Py_True : Py_False);
		}
		Py_XDECREF(path);
		Py_XDECREF(message);
		if (item == nullptr) {
			Py_DECREF(list);
			return nullptr;
		}
		PyList_SET_ITEM(list, static_cast<Py_ssize_t>(i), item);
	}
	return list;
}

PyObject* native_scan_folder(PyObject*, PyObject* argument) {
	NativeString root_name;
	if (!encode_path(argument, root_name)) {
		return nullptr;
	}

	Node root;
	Walk walk;
	bool cancelled = false;
	Py_BEGIN_ALLOW_THREADS
	scan_found.store(0);
	scan_cancelled.store(false);
	try {
		walk_folder(walk, fs::path(root_name), root, 0);
	} catch (const std::exception& error) {
		walk.errors.push_back({root_name, from_narrow(error.what()), false});
	}
	cancelled = scan_cancelled.load();
	Py_END_ALLOW_THREADS

	if (cancelled) {
		Py_RETURN_NONE;
	}
	return pack_pair(node_to_python(root), errors_to_python(walk.errors));
}

PyObject* native_scan_folder_progress(PyObject*, PyObject*) {
	return PyLong_FromSsize_t(scan_found.load(std::memory_order_relaxed));
}

PyObject* native_cancel_scan_folder(PyObject*, PyObject*) {
	scan_cancelled.store(true);
	Py_RETURN_NONE;
}

PyMethodDef native_scan_methods[] = {
	{"scan_folder", native_scan_folder, METH_O,
		"Walk a folder tree without the GIL. Returns ((files, [(name, node), ...]), errors), "
		"or None if cancelled. Hidden entries and __MACOSX are skipped, names are unsorted, "
		"and errors are (path, message, is_permission_error) tuples."},
	{"scan_folder_progress", native_scan_folder_progress, METH_NOARGS, "Return the number of files the current folder walk has found."},
	{"cancel_scan_folder", native_cancel_scan_folder, METH_NOARGS, "Stop the current folder walk."},
	{nullptr, nullptr, 0, nullptr},
};

}  // namespace

int add_native_scan_methods(PyObject* module) {
	return PyModule_AddFunctions(module, native_scan_methods);
}
