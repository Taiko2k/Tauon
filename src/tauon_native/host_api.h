#pragma once

#include <cstdint>

constexpr std::uint32_t TAUON_PYTHON_HOST_ABI_VERSION = 1;

struct TauonPythonHostContext {
	std::uint32_t abi_version;
	void* window;
	void* renderer;
	const char* sdl_library_path;
	const char* user_data_directory;
	const char* source_directory;
	const char* site_packages_directory;
};

using TauonPythonHostRun = int (*)(const TauonPythonHostContext*, int, char**);

#if defined(_WIN32)
#define TAUON_PYTHON_HOST_EXPORT extern "C" __declspec(dllexport)
#else
#define TAUON_PYTHON_HOST_EXPORT extern "C" __attribute__((visibility("default")))
#endif
