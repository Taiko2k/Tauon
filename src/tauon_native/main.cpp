#define PY_SSIZE_T_CLEAN
#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <shellapi.h>
#endif

#include <Python.h>
#include <SDL3/SDL.h>

#include <cmath>
#include <cerrno>
#include <charconv>
#include <cctype>
#include <cstring>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "native_render.h"

#if defined(__APPLE__)
#include <mach-o/dyld.h>
#endif

#if !defined(_WIN32)
#include <arpa/inet.h>
#include <dlfcn.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>
#endif

namespace {

constexpr int kDefaultWidth = 1120;
constexpr int kDefaultHeight = 600;
#if defined(__APPLE__)
constexpr double kDefaultScale = 2.0;
#else
constexpr double kDefaultScale = 1.0;
#endif

struct WindowState {
	int width = kDefaultWidth;
	int height = kDefaultHeight;
	double scale = kDefaultScale;
	double opacity = 1.0;
	bool borderless = true;
	bool maximized = false;
	std::optional<std::pair<int, int>> position;
};

struct WindowDeleter {
	void operator()(SDL_Window* window) const noexcept {
		if (window != nullptr) {
			SDL_DestroyWindow(window);
		}
	}
};

struct RendererDeleter {
	void operator()(SDL_Renderer* renderer) const noexcept {
		if (renderer != nullptr) {
			SDL_DestroyRenderer(renderer);
		}
	}
};

using WindowPtr = std::unique_ptr<SDL_Window, WindowDeleter>;
using RendererPtr = std::unique_ptr<SDL_Renderer, RendererDeleter>;

struct NativeState {
	WindowPtr window;
	RendererPtr renderer;
	std::filesystem::path executable_path;
	std::filesystem::path sdl_library_path;
	std::filesystem::path user_data_directory;
	WindowState window_state;
	bool sdl_initialised = false;
	bool hidden = false;
	bool portable = false;
#if defined(_WIN32)
	HANDLE instance_lock_handle = INVALID_HANDLE_VALUE;
#else
	int instance_lock_fd = -1;
#endif
};

NativeState* g_state = nullptr;

std::filesystem::path current_executable_path(const char* executable_argument) {
#if defined(_WIN32)
	std::vector<wchar_t> buffer(32768);
	const DWORD length = GetModuleFileNameW(nullptr, buffer.data(), static_cast<DWORD>(buffer.size()));
	if (length > 0 && length < buffer.size()) {
		return std::filesystem::weakly_canonical(std::filesystem::path(std::wstring(buffer.data(), length)));
	}
#elif defined(__APPLE__)
	uint32_t size = 0;
	_NSGetExecutablePath(nullptr, &size);
	std::vector<char> buffer(size + 1);
	if (_NSGetExecutablePath(buffer.data(), &size) == 0) {
		return std::filesystem::weakly_canonical(std::filesystem::path(buffer.data()));
	}
#else
	std::vector<char> buffer(4096);
	const ssize_t length = readlink("/proc/self/exe", buffer.data(), buffer.size() - 1);
	if (length > 0) {
		buffer[static_cast<std::size_t>(length)] = '\0';
		return std::filesystem::weakly_canonical(std::filesystem::path(buffer.data()));
	}
#endif
	std::error_code error;
	const std::filesystem::path fallback = std::filesystem::weakly_canonical(
		executable_argument != nullptr ? executable_argument : "tauon-native",
		error
	);
	return error ? std::filesystem::absolute(executable_argument != nullptr ? executable_argument : "tauon-native") : fallback;
}

std::filesystem::path bundled_python_directory(const std::filesystem::path& executable) {
#if defined(__APPLE__)
	return executable.parent_path().parent_path() / "Resources" / "python";
#else
	return executable.parent_path() / "_internal" / "python";
#endif
}

std::filesystem::path bundled_library_directory(const std::filesystem::path& executable) {
#if defined(__APPLE__)
	return executable.parent_path().parent_path() / "Frameworks";
#else
	return executable.parent_path() / "_internal" / "lib";
#endif
}

std::filesystem::path bundled_resource_directory(const std::filesystem::path& executable) {
#if defined(__APPLE__)
	return executable.parent_path().parent_path() / "Resources";
#else
	return executable.parent_path() / "_internal";
#endif
}

bool is_bundled_install(const std::filesystem::path& executable) {
	const std::filesystem::path python_directory = bundled_python_directory(executable);
	return std::filesystem::is_directory(python_directory / "stdlib")
		&& std::filesystem::is_directory(python_directory / "site-packages");
}

void set_environment_variable(const char* name, const std::string& value) {
#if defined(_WIN32)
	_putenv_s(name, value.c_str());
#else
	setenv(name, value.c_str(), 1);
#endif
}

void prepend_environment_path(const char* name, const std::filesystem::path& directory) {
	if (directory.empty() || !std::filesystem::exists(directory)) {
		return;
	}
	const char separator =
#if defined(_WIN32)
		';';
#else
		':';
#endif
	std::string value = directory.string();
	if (const char* existing = std::getenv(name); existing != nullptr && existing[0] != '\0') {
		value.push_back(separator);
		value.append(existing);
	}
	set_environment_variable(name, value);
}

void configure_bundled_environment(const std::filesystem::path& executable) {
	if (!is_bundled_install(executable)) {
		return;
	}
	const std::filesystem::path library_directory = bundled_library_directory(executable);
	const std::filesystem::path resource_directory = bundled_resource_directory(executable);
	prepend_environment_path("PATH", library_directory);
	prepend_environment_path("GI_TYPELIB_PATH", resource_directory / "lib" / "girepository-1.0");
	prepend_environment_path("XDG_DATA_DIRS", resource_directory / "share");
	const std::filesystem::path fontconfig_directory = resource_directory / "etc" / "fonts";
	if (std::filesystem::is_directory(fontconfig_directory)) {
		set_environment_variable("FONTCONFIG_PATH", fontconfig_directory.string());
	}
}

std::filesystem::path linked_sdl_library_path() {
#if defined(_WIN32)
	HMODULE module = nullptr;
	if (!GetModuleHandleExW(
			GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
			reinterpret_cast<LPCWSTR>(&SDL_Init),
			&module)) {
		return {};
	}
	std::vector<wchar_t> buffer(32768);
	const DWORD length = GetModuleFileNameW(module, buffer.data(), static_cast<DWORD>(buffer.size()));
	if (length == 0 || length >= buffer.size()) {
		return {};
	}
	return std::filesystem::path(std::wstring(buffer.data(), length));
#else
	Dl_info info{};
	if (dladdr(reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(&SDL_Init)), &info) == 0 || info.dli_fname == nullptr) {
		return {};
	}
	std::filesystem::path library_path(info.dli_fname);
	const std::string path_text = library_path.string();
	const std::size_t cellar = path_text.find("/Cellar/");
	if (cellar != std::string::npos) {
		const std::filesystem::path homebrew_lib = std::filesystem::path(path_text.substr(0, cellar)) / "lib";
		const std::filesystem::path shared_link = homebrew_lib / library_path.filename();
		if (std::filesystem::exists(shared_link)) {
			// Homebrew keeps SDL satellite libraries (notably SDL3_image) in
			// this shared prefix rather than SDL3's versioned Cellar directory.
			return shared_link;
		}
	}
	return std::filesystem::absolute(library_path);
#endif
}

bool has_argument(int argc, char** argv, std::string_view wanted) {
	for (int index = 1; index < argc; ++index) {
		if (argv[index] != nullptr && wanted == argv[index]) {
			return true;
		}
	}
	return false;
}

std::optional<std::string_view> controller_endpoint(std::string_view argument) {
	if (argument == "--play") {
		return "play";
	}
	if (argument == "--pause") {
		return "pause";
	}
	if (argument == "--playpause" || argument == "--play-pause") {
		return "playpause";
	}
	if (argument == "--stop") {
		return "stop";
	}
	if (argument == "--next") {
		return "next";
	}
	if (argument == "--previous") {
		return "previous";
	}
	if (argument == "--raise") {
		return "raise";
	}
	if (argument == "--reloadtheme" || argument == "--reload-theme") {
		return "reloadtheme";
	}
	if (argument == "--shuffle") {
		return "shuffle";
	}
	if (argument == "--repeat") {
		return "repeat";
	}
	return std::nullopt;
}

bool has_controller_argument(int argc, char** argv) {
	for (int index = 1; index < argc; ++index) {
		if (argv[index] != nullptr && controller_endpoint(argv[index])) {
			return true;
		}
	}
	return false;
}

void print_usage(const char* executable) {
	const std::filesystem::path executable_path(executable != nullptr ? executable : "tauon-native");
	std::cout
		<< "Usage: " << executable_path.filename().string() << " [options] [file-or-URI ...]\n\n"
		<< "Commands (forwarded to a running Tauon instance):\n"
		<< "  --play           Start playback\n"
		<< "  --pause          Pause playback\n"
		<< "  --playpause      Toggle play/pause\n"
		<< "  --stop           Stop playback\n"
		<< "  --next           Skip to the next track\n"
		<< "  --previous       Return to the previous track\n"
		<< "  --raise          Bring the Tauon window to the front\n"
		<< "  --reloadtheme    Reload the active UI theme\n"
		<< "  --shuffle        Toggle shuffle mode\n"
		<< "  --repeat         Toggle repeat mode\n\n"
		<< "Options:\n"
		<< "  -h, --help       Show this help\n"
		<< "  --tray           Start Tauon hidden in the tray\n"
		<< "  --no-start       Forward arguments without starting Tauon\n";
}

std::string urlsafe_base64(std::string_view input) {
	constexpr std::string_view alphabet =
		"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
	std::string encoded;
	encoded.reserve(((input.size() + 2) / 3) * 4);
	for (std::size_t offset = 0; offset < input.size(); offset += 3) {
		const auto first = static_cast<unsigned char>(input[offset]);
		const auto second = offset + 1 < input.size() ? static_cast<unsigned char>(input[offset + 1]) : 0;
		const auto third = offset + 2 < input.size() ? static_cast<unsigned char>(input[offset + 2]) : 0;
		const unsigned int value = (static_cast<unsigned int>(first) << 16U)
			| (static_cast<unsigned int>(second) << 8U)
			| static_cast<unsigned int>(third);
		encoded.push_back(alphabet[(value >> 18U) & 0x3fU]);
		encoded.push_back(alphabet[(value >> 12U) & 0x3fU]);
		encoded.push_back(offset + 1 < input.size() ? alphabet[(value >> 6U) & 0x3fU] : '=');
		encoded.push_back(offset + 2 < input.size() ? alphabet[value & 0x3fU] : '=');
	}
	return encoded;
}

#if defined(_WIN32)
using SocketHandle = SOCKET;
constexpr SocketHandle kInvalidSocket = INVALID_SOCKET;

void close_socket(SocketHandle socket_handle) {
	closesocket(socket_handle);
}
#else
using SocketHandle = int;
constexpr SocketHandle kInvalidSocket = -1;

void close_socket(SocketHandle socket_handle) {
	close(socket_handle);
}
#endif

bool send_controller_request(std::string_view endpoint) {
#if defined(_WIN32)
	WSADATA winsock_data {};
	if (WSAStartup(MAKEWORD(2, 2), &winsock_data) != 0) {
		std::cerr << "Tauon: unable to initialise local IPC networking\n";
		return false;
	}
#endif
	const SocketHandle socket_handle = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
	if (socket_handle == kInvalidSocket) {
		std::cerr << "Tauon: unable to create local IPC socket\n";
#if defined(_WIN32)
		WSACleanup();
#endif
		return false;
	}

#if defined(_WIN32)
	const DWORD timeout_ms = 2000;
	setsockopt(
		socket_handle,
		SOL_SOCKET,
		SO_RCVTIMEO,
		reinterpret_cast<const char*>(&timeout_ms),
		static_cast<int>(sizeof(timeout_ms))
	);
	setsockopt(
		socket_handle,
		SOL_SOCKET,
		SO_SNDTIMEO,
		reinterpret_cast<const char*>(&timeout_ms),
		static_cast<int>(sizeof(timeout_ms))
	);
#else
	const timeval timeout {2, 0};
	setsockopt(socket_handle, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
	setsockopt(socket_handle, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout));
#endif

	sockaddr_in address {};
	address.sin_family = AF_INET;
	address.sin_port = htons(7813);
	address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
	if (connect(
		socket_handle,
		reinterpret_cast<const sockaddr*>(&address),
		static_cast<int>(sizeof(address))
	) != 0) {
		close_socket(socket_handle);
#if defined(_WIN32)
		WSACleanup();
#endif
		std::cerr << "Tauon: could not connect to the running instance on 127.0.0.1:7813\n";
		return false;
	}

	const std::string request =
		"GET /" + std::string(endpoint) + " HTTP/1.0\r\n"
		"Host: 127.0.0.1:7813\r\n"
		"Connection: close\r\n\r\n";
	std::size_t sent_bytes = 0;
	while (sent_bytes < request.size()) {
		const int sent = send(
			socket_handle,
			request.data() + sent_bytes,
			static_cast<int>(request.size() - sent_bytes),
			0
		);
		if (sent <= 0) {
			close_socket(socket_handle);
#if defined(_WIN32)
			WSACleanup();
#endif
			std::cerr << "Tauon: failed to send a request to the running instance\n";
			return false;
		}
		sent_bytes += static_cast<std::size_t>(sent);
	}

	std::string response;
	char response_buffer[1024];
	while (response.size() < 8192) {
		const int received = recv(socket_handle, response_buffer, static_cast<int>(sizeof(response_buffer)), 0);
		if (received <= 0) {
			break;
		}
		response.append(response_buffer, static_cast<std::size_t>(received));
	}
	close_socket(socket_handle);
#if defined(_WIN32)
	WSACleanup();
#endif

	const std::size_t first_space = response.find(' ');
	if (first_space == std::string::npos || response.size() < first_space + 4) {
		std::cerr << "Tauon: the running instance returned an invalid IPC response\n";
		return false;
	}
	const int status = std::strtol(response.c_str() + first_space + 1, nullptr, 10);
	if (status < 200 || status >= 300) {
		std::cerr << "Tauon: the running instance returned HTTP status " << status << '\n';
		return false;
	}
	return true;
}

bool is_open_argument(std::string_view argument) {
	if (argument.empty() || argument.front() == '-') {
		return false;
	}
	if (argument.rfind("file://", 0) == 0) {
		return true;
	}
	std::error_code error;
	return std::filesystem::exists(std::filesystem::path(argument), error) && !error;
}

int forward_arguments(int argc, char** argv) {
	std::vector<std::string> endpoints;
	for (int index = 1; index < argc; ++index) {
		if (argv[index] == nullptr) {
			continue;
		}
		const std::string_view argument(argv[index]);
		if (const std::optional<std::string_view> endpoint = controller_endpoint(argument)) {
			endpoints.emplace_back(*endpoint);
		} else if (is_open_argument(argument)) {
			endpoints.emplace_back("open/" + urlsafe_base64(argument));
		}
	}
	if (argc <= 1) {
		endpoints.emplace_back("raise");
	}

	for (const std::string& endpoint : endpoints) {
		if (!send_controller_request(endpoint)) {
			return 1;
		}
	}
	return 0;
}

std::filesystem::path user_data_directory(const char* executable_argument) {
	if (const char* override_path = std::getenv("TAUON_USER_DATA_DIR")) {
		return std::filesystem::path(override_path);
	}

	const std::filesystem::path executable = current_executable_path(executable_argument);
	if (std::filesystem::exists(executable.parent_path() / "portable")) {
		return executable.parent_path() / "user-data";
	}

#if defined(_WIN32)
	if (const char* local_app_data = std::getenv("LOCALAPPDATA")) {
		return std::filesystem::path(local_app_data) / "TauonMusicBox";
	}
	if (const char* app_data = std::getenv("APPDATA")) {
		return std::filesystem::path(app_data) / "TauonMusicBox";
	}
#elif !defined(__APPLE__) && defined(TAUON_DEVELOPMENT_BUILD)
	// Match Python's source-tree development mode when this executable is run
	// from the same checkout. Installed builds use the XDG location below.
	const std::filesystem::path project_root = std::filesystem::path(TAUON_SOURCE_DIR).parent_path();
	const std::filesystem::path relative = executable.lexically_relative(project_root);
	if (!relative.empty() && *relative.begin() != "..") {
		return project_root / "user-data";
	}
#endif

	if (const char* xdg_data_home = std::getenv("XDG_DATA_HOME")) {
		return std::filesystem::path(xdg_data_home) / "TauonMusicBox";
	}
	if (const char* home = std::getenv("HOME")) {
		return std::filesystem::path(home) / ".local" / "share" / "TauonMusicBox";
	}
	return std::filesystem::current_path() / "user-data";
}

enum class InstanceLockResult {
	Acquired,
	AlreadyRunning,
	Unavailable,
};

InstanceLockResult acquire_instance_lock(NativeState& state, const char* executable_argument) {
#if defined(_WIN32)
	state.user_data_directory = user_data_directory(executable_argument);
	std::error_code error;
	std::filesystem::create_directories(state.user_data_directory, error);
	if (error) {
		std::cerr << "Tauon: unable to create user data directory for instance lock: " << error.message() << '\n';
		return InstanceLockResult::Unavailable;
	}

	const std::filesystem::path lock_path = state.user_data_directory / "program.pid";
	state.instance_lock_handle = CreateFileW(
		lock_path.c_str(),
		GENERIC_READ | GENERIC_WRITE,
		FILE_SHARE_READ,
		nullptr,
		OPEN_ALWAYS,
		FILE_ATTRIBUTE_NORMAL,
		nullptr
	);
	if (state.instance_lock_handle == INVALID_HANDLE_VALUE) {
		const DWORD lock_error = GetLastError();
		if (lock_error == ERROR_SHARING_VIOLATION || lock_error == ERROR_LOCK_VIOLATION) {
			return InstanceLockResult::AlreadyRunning;
		}
		std::cerr << "Tauon: unable to acquire instance lock " << lock_path.string() << '\n';
		return InstanceLockResult::Unavailable;
	}
	SetFilePointer(state.instance_lock_handle, 0, nullptr, FILE_BEGIN);
	SetEndOfFile(state.instance_lock_handle);
	const std::string pid = std::to_string(GetCurrentProcessId()) + "\n";
	DWORD bytes_written = 0;
	WriteFile(state.instance_lock_handle, pid.data(), static_cast<DWORD>(pid.size()), &bytes_written, nullptr);
	return InstanceLockResult::Acquired;
#else
	state.user_data_directory = user_data_directory(executable_argument);
	std::error_code error;
	std::filesystem::create_directories(state.user_data_directory, error);
	if (error) {
		std::cerr << "Tauon: unable to create user data directory for instance lock: " << error.message() << '\n';
		return InstanceLockResult::Unavailable;
	}

	const std::filesystem::path lock_path = state.user_data_directory / "program.pid";
	state.instance_lock_fd = open(lock_path.c_str(), O_WRONLY | O_CREAT, 0600);
	if (state.instance_lock_fd == -1) {
		std::cerr << "Tauon: unable to open instance lock " << lock_path << ": " << std::strerror(errno) << '\n';
		return InstanceLockResult::Unavailable;
	}

	struct flock lock {};
	lock.l_type = F_WRLCK;
	lock.l_whence = SEEK_SET;
	if (fcntl(state.instance_lock_fd, F_SETLK, &lock) == -1) {
		const int lock_error = errno;
		close(state.instance_lock_fd);
		state.instance_lock_fd = -1;
		if (lock_error == EACCES || lock_error == EAGAIN) {
			return InstanceLockResult::AlreadyRunning;
		}
		std::cerr << "Tauon: unable to acquire instance lock " << lock_path << ": " << std::strerror(lock_error) << '\n';
		return InstanceLockResult::Unavailable;
	}

	ftruncate(state.instance_lock_fd, 0);
	const std::string pid = std::to_string(getpid()) + '\n';
	write(state.instance_lock_fd, pid.data(), pid.size());
	return InstanceLockResult::Acquired;
#endif
}

std::optional<std::size_t> json_value_position(const std::string& document, std::string_view key) {
	const std::string quoted_key = "\"" + std::string(key) + "\"";
	std::size_t position = document.find(quoted_key);
	if (position == std::string::npos) {
		return std::nullopt;
	}
	position = document.find(':', position + quoted_key.size());
	if (position == std::string::npos) {
		return std::nullopt;
	}
	++position;
	while (position < document.size() && std::isspace(static_cast<unsigned char>(document[position])) != 0) {
		++position;
	}
	return position;
}

bool parse_json_int(const std::string& document, std::string_view key, int& value, bool required = false) {
	const std::optional<std::size_t> position = json_value_position(document, key);
	if (!position) {
		return !required;
	}
	const char* begin = document.data() + *position;
	const char* end = document.data() + document.size();
	const std::from_chars_result result = std::from_chars(begin, end, value);
	return result.ec == std::errc{} && result.ptr != begin;
}

bool parse_json_number(const std::string& document, std::string_view key, double& value) {
	const std::optional<std::size_t> position = json_value_position(document, key);
	if (!position) {
		return true;
	}
	errno = 0;
	char* end = nullptr;
	value = std::strtod(document.c_str() + *position, &end);
	return errno == 0 && end != document.c_str() + *position && std::isfinite(value);
}

bool parse_json_bool(const std::string& document, std::string_view key, bool& value) {
	const std::optional<std::size_t> position = json_value_position(document, key);
	if (!position) {
		return true;
	}
	const std::string_view remaining(document.data() + *position, document.size() - *position);
	if (remaining.substr(0, 4) == "true") {
		value = true;
		return true;
	}
	if (remaining.substr(0, 5) == "false") {
		value = false;
		return true;
	}
	return false;
}

bool parse_json_position(const std::string& document, std::optional<std::pair<int, int>>& value) {
	const std::optional<std::size_t> position = json_value_position(document, "position");
	if (!position) {
		return true;
	}
	std::size_t cursor = *position;
	if (document.compare(cursor, 4, "null") == 0) {
		value.reset();
		return true;
	}
	if (cursor >= document.size() || document[cursor] != '[') {
		return false;
	}
	++cursor;
	while (cursor < document.size() && std::isspace(static_cast<unsigned char>(document[cursor])) != 0) {
		++cursor;
	}
	int x = 0;
	auto first = std::from_chars(document.data() + cursor, document.data() + document.size(), x);
	if (first.ec != std::errc{}) {
		return false;
	}
	cursor = static_cast<std::size_t>(first.ptr - document.data());
	while (cursor < document.size() && std::isspace(static_cast<unsigned char>(document[cursor])) != 0) {
		++cursor;
	}
	if (cursor >= document.size() || document[cursor] != ',') {
		return false;
	}
	++cursor;
	while (cursor < document.size() && std::isspace(static_cast<unsigned char>(document[cursor])) != 0) {
		++cursor;
	}
	int y = 0;
	auto second = std::from_chars(document.data() + cursor, document.data() + document.size(), y);
	if (second.ec != std::errc{}) {
		return false;
	}
	cursor = static_cast<std::size_t>(second.ptr - document.data());
	while (cursor < document.size() && std::isspace(static_cast<unsigned char>(document[cursor])) != 0) {
		++cursor;
	}
	if (cursor >= document.size() || document[cursor] != ']') {
		return false;
	}
	value = std::pair{x, y};
	return true;
}

WindowState load_window_state(const std::filesystem::path& path) {
	WindowState state;
	std::ifstream file(path);
	if (!file) {
		return state;
	}
	const std::string document{
		std::istreambuf_iterator<char>(file),
		std::istreambuf_iterator<char>()
	};
	int version = 0;
	const bool valid =
		parse_json_int(document, "version", version, true) && version == 1 &&
		parse_json_int(document, "width", state.width) &&
		parse_json_int(document, "height", state.height) &&
		parse_json_number(document, "scale", state.scale) &&
		parse_json_number(document, "opacity", state.opacity) &&
		parse_json_bool(document, "borderless", state.borderless) &&
		parse_json_bool(document, "maximized", state.maximized) &&
		parse_json_position(document, state.position) &&
		state.width > 100 && state.width < 10000 &&
		state.height > 100 && state.height < 5000 &&
		state.scale >= 0.5 && state.scale <= 4.0 &&
		state.opacity >= 0.3 && state.opacity <= 1.0;
	if (!valid) {
		std::cerr << "Tauon: ignoring invalid window state file: " << path << '\n';
		return WindowState{};
	}
	return state;
}

void set_environment(const char* name, const std::string& value) {
#if defined(_WIN32)
	_putenv_s(name, value.c_str());
#else
	setenv(name, value.c_str(), 1);
#endif
}

void configure_python_sdl_loader(const NativeState& state) {
	if (!state.sdl_library_path.empty()) {
		set_environment("SDL_BINARY_PATH", state.sdl_library_path.parent_path().string());
	}
	// PySDL3 normally installs an atexit handler that enters SDL's Python main
	// wrapper.  tauon-native already owns the process main function and tears
	// down the SDL objects after CPython has finalized, so letting that handler
	// run re-enters SDL during interpreter shutdown and can dereference state
	// that is already being finalized.
	set_environment("SDL_MAIN_NOIMPL", "1");
	set_environment("SDL_FIND_BINARIES", "0");
	set_environment("SDL_DISABLE_METADATA", "1");
	set_environment("SDL_CHECK_VERSION", "0");
	set_environment("SDL_CHECK_BINARY_VERSION", "0");
	set_environment("SDL_IGNORE_MISSING_FUNCTIONS", "1");
}

void configure_sdl_metadata() {
#if defined(__APPLE__)
	constexpr const char* app_identifier = "com.github.taiko2k.tauonmb";
#else
	const char* app_identifier = std::getenv("FLATPAK_ID") != nullptr
		? "com.github.taiko2k.tauonmb"
		: "tauonmb";
#endif
	SDL_SetAppMetadata("Tauon", TAUON_VERSION, app_identifier);
	SDL_SetAppMetadataProperty(SDL_PROP_APP_METADATA_CREATOR_STRING, "Taiko2k");
	SDL_SetAppMetadataProperty(SDL_PROP_APP_METADATA_COPYRIGHT_STRING, "Copyright 2015-2026 Taiko2k");
	SDL_SetAppMetadataProperty(SDL_PROP_APP_METADATA_URL_STRING, "https://tauonmusicbox.rocks/");
	SDL_SetAppMetadataProperty(SDL_PROP_APP_METADATA_TYPE_STRING, "mediaplayer");

	SDL_SetHint(SDL_HINT_MOUSE_FOCUS_CLICKTHROUGH, "1");
	SDL_SetHint(SDL_HINT_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR, "0");
#if defined(__APPLE__)
	SDL_SetHint(SDL_HINT_MAC_SCROLL_MOMENTUM, "1");
#endif
}

void configure_video_environment() {
	set_environment("SDL_VIDEO_WAYLAND_ALLOW_LIBDECOR", "0");
	if (std::getenv("SDL_VIDEODRIVER") != nullptr) {
		return;
	}
	const char* desktop = std::getenv("XDG_CURRENT_DESKTOP");
	const char* session = std::getenv("XDG_SESSION_TYPE");
	if ((desktop != nullptr && std::string_view(desktop) == "GNOME:Phosh") ||
		(session != nullptr && std::string_view(session) == "wayland")) {
		set_environment("SDL_VIDEODRIVER", "wayland");
	}
}

void draw_polyline(SDL_Renderer* renderer, const std::vector<SDL_FPoint>& points) {
	SDL_RenderLines(renderer, points.data(), static_cast<int>(points.size()));
}

void draw_loading_screen(SDL_Renderer* renderer, SDL_Window* window, double scale) {
	int width = 0;
	int height = 0;
	SDL_GetWindowSizeInPixels(window, &width, &height);

	const int box_width = static_cast<int>(std::lround(44.0 * scale));
	const int box_radius = box_width / 2;
	const int box_depth = static_cast<int>(std::lround(35.0 * scale));

	SDL_SetRenderDrawColor(renderer, 7, 7, 7, 255);
	SDL_RenderFillRect(renderer, nullptr);
	SDL_SetRenderDrawColor(renderer, 120, 134, 150, 35);

	int centre_y = -box_radius;
	int row = 0;
	while (centre_y < height + box_radius + box_depth) {
		int centre_x = -box_width * 2 + ((row % 2 != 0) ? box_width : 0);
		while (centre_x < width + box_width * 2) {
			const SDL_FPoint north{static_cast<float>(centre_x), static_cast<float>(centre_y - box_radius)};
			const SDL_FPoint east{static_cast<float>(centre_x + box_width), static_cast<float>(centre_y)};
			const SDL_FPoint south{static_cast<float>(centre_x), static_cast<float>(centre_y + box_radius)};
			const SDL_FPoint west{static_cast<float>(centre_x - box_width), static_cast<float>(centre_y)};

			draw_polyline(renderer, {north, east, south, west, north});
			draw_polyline(renderer, {west, {west.x, west.y + static_cast<float>(box_depth)}});
			draw_polyline(renderer, {south, {south.x, south.y + static_cast<float>(box_depth)}});
			centre_x += box_width * 2;
		}
		centre_y += box_radius + box_depth;
		++row;
	}

	SDL_RenderPresent(renderer);
}

bool initialise_native_app(NativeState& state, int argc, char** argv) {
	state.user_data_directory = user_data_directory(argv[0]);
	state.window_state = load_window_state(state.user_data_directory / "window-state.json");
	configure_video_environment();
	configure_sdl_metadata();
	if (!SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS)) {
		std::cerr << "Tauon: SDL initialisation failed: " << SDL_GetError() << '\n';
		return false;
	}
	state.sdl_initialised = true;
	state.sdl_library_path = linked_sdl_library_path();
	configure_python_sdl_loader(state);
	state.hidden = has_argument(argc, argv, "--tray");

	// Create hidden even for a normal launch so the compositor never exposes an
	// empty window between creation and the first rendered splash.
	SDL_WindowFlags flags = SDL_WINDOW_RESIZABLE | SDL_WINDOW_TRANSPARENT | SDL_WINDOW_HIGH_PIXEL_DENSITY |
		SDL_WINDOW_HIDDEN;
	if (state.window_state.borderless) {
		flags |= SDL_WINDOW_BORDERLESS;
	}
	if (std::getenv("GAMESCOPE_WAYLAND_DISPLAY") != nullptr) {
		flags |= SDL_WINDOW_FULLSCREEN;
	}

	const SDL_PropertiesID window_properties = SDL_CreateProperties();
	if (window_properties == 0) {
		std::cerr << "Tauon: window property creation failed: " << SDL_GetError() << '\n';
		return false;
	}
	SDL_SetStringProperty(window_properties, SDL_PROP_WINDOW_CREATE_TITLE_STRING, "Tauon");
	SDL_SetNumberProperty(window_properties, SDL_PROP_WINDOW_CREATE_WIDTH_NUMBER, state.window_state.width);
	SDL_SetNumberProperty(window_properties, SDL_PROP_WINDOW_CREATE_HEIGHT_NUMBER, state.window_state.height);
	SDL_SetNumberProperty(window_properties, SDL_PROP_WINDOW_CREATE_FLAGS_NUMBER, flags);
	if (state.window_state.position && (flags & SDL_WINDOW_FULLSCREEN) == 0) {
		SDL_SetNumberProperty(
			window_properties,
			SDL_PROP_WINDOW_CREATE_X_NUMBER,
			state.window_state.position->first
		);
		SDL_SetNumberProperty(
			window_properties,
			SDL_PROP_WINDOW_CREATE_Y_NUMBER,
			state.window_state.position->second
		);
	}
	state.window.reset(SDL_CreateWindowWithProperties(window_properties));
	SDL_DestroyProperties(window_properties);
	if (!state.window) {
		std::cerr << "Tauon: window creation failed: " << SDL_GetError() << '\n';
		return false;
	}
	SDL_SetWindowOpacity(state.window.get(), static_cast<float>(state.window_state.opacity));
	if (state.window_state.maximized && (flags & SDL_WINDOW_FULLSCREEN) == 0) {
		SDL_MaximizeWindow(state.window.get());
	}

	const char* preferred_driver = nullptr;
	for (int index = 0;; ++index) {
		const char* driver = SDL_GetRenderDriver(index);
		if (driver == nullptr) {
			break;
		}
		if (std::string_view(driver) == "opengl") {
			preferred_driver = "opengl";
			break;
		}
	}

	state.renderer.reset(SDL_CreateRenderer(state.window.get(), preferred_driver));
	if (!state.renderer && preferred_driver != nullptr) {
		SDL_ClearError();
		state.renderer.reset(SDL_CreateRenderer(state.window.get(), nullptr));
	}
	if (!state.renderer) {
		std::cerr << "Tauon: renderer creation failed: " << SDL_GetError() << '\n';
		return false;
	}

	SDL_SetRenderDrawBlendMode(state.renderer.get(), SDL_BLENDMODE_BLEND);
	SDL_SetRenderVSync(state.renderer.get(), 1);
	if (!state.hidden) {
		// Prime the renderer while hidden, then synchronously map the native
		// window. SDL window operations are asynchronous on several backends
		// (including Cocoa), so without SDL_SyncWindow() it might not become
		// visible until Python begins polling events.
		draw_loading_screen(state.renderer.get(), state.window.get(), state.window_state.scale);
		if (!SDL_ShowWindow(state.window.get())) {
			std::cerr << "Tauon: failed to show the startup window: " << SDL_GetError() << '\n';
			return false;
		}
		// A window created hidden is not treated like a newly created visible
		// application window by every backend. Explicitly request focus now that
		// the splash is mapped, matching the legacy Python startup path.
		if (!SDL_RaiseWindow(state.window.get())) {
			std::cerr << "Tauon: startup window focus request was declined: " << SDL_GetError() << '\n';
		}
		if (!SDL_SyncWindow(state.window.get())) {
			std::cerr << "Tauon: failed to synchronize the startup window: " << SDL_GetError() << '\n';
			return false;
		}
		SDL_PumpEvents();
		// Present once more after mapping in case the video backend discarded the
		// hidden window's drawable contents.
		draw_loading_screen(state.renderer.get(), state.window.get(), state.window_state.scale);
		SDL_PumpEvents();
	}
	return true;
}

void shutdown_native_sdl(NativeState& state) {
	state.renderer.reset();
	state.window.reset();
	if (state.sdl_initialised) {
		SDL_Quit();
		state.sdl_initialised = false;
	}
}

void shutdown_native_app(NativeState& state) {
	shutdown_native_sdl(state);
#if defined(_WIN32)
	if (state.instance_lock_handle != INVALID_HANDLE_VALUE) {
		CloseHandle(state.instance_lock_handle);
		state.instance_lock_handle = INVALID_HANDLE_VALUE;
	}
#else
	if (state.instance_lock_fd != -1) {
		close(state.instance_lock_fd);
		state.instance_lock_fd = -1;
	}
#endif
}

PyObject* bridge_is_active(PyObject*, PyObject*) {
	return PyBool_FromLong(g_state != nullptr ? 1 : 0);
}

PyObject* bridge_window_address(PyObject*, PyObject*) {
	if (g_state == nullptr || !g_state->window) {
		PyErr_SetString(PyExc_RuntimeError, "Tauon's native window is unavailable");
		return nullptr;
	}
	return PyLong_FromVoidPtr(g_state->window.get());
}

PyObject* bridge_renderer_address(PyObject*, PyObject*) {
	if (g_state == nullptr || !g_state->renderer) {
		PyErr_SetString(PyExc_RuntimeError, "Tauon's native renderer is unavailable");
		return nullptr;
	}
	return PyLong_FromVoidPtr(g_state->renderer.get());
}

PyObject* bridge_window_size(PyObject*, PyObject*) {
	if (g_state == nullptr || !g_state->window) {
		PyErr_SetString(PyExc_RuntimeError, "Tauon's native window is unavailable");
		return nullptr;
	}
	int width = 0;
	int height = 0;
	if (!SDL_GetWindowSize(g_state->window.get(), &width, &height)) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return Py_BuildValue("(ii)", width, height);
}

PyObject* bridge_renderer_name(PyObject*, PyObject*) {
	if (g_state == nullptr || !g_state->renderer) {
		PyErr_SetString(PyExc_RuntimeError, "Tauon's native renderer is unavailable");
		return nullptr;
	}
	const char* name = SDL_GetRendererName(g_state->renderer.get());
	if (name == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return PyUnicode_FromString(name);
}

PyObject* bridge_sdl_library_path(PyObject*, PyObject*) {
	if (g_state == nullptr || g_state->sdl_library_path.empty()) {
		Py_RETURN_NONE;
	}
	return PyUnicode_DecodeFSDefault(g_state->sdl_library_path.string().c_str());
}

PyObject* bridge_user_data_directory(PyObject*, PyObject*) {
	if (g_state == nullptr || g_state->user_data_directory.empty()) {
		PyErr_SetString(PyExc_RuntimeError, "Tauon's user data directory is unavailable");
		return nullptr;
	}
	return PyUnicode_DecodeFSDefault(g_state->user_data_directory.string().c_str());
}

PyObject* bridge_executable_directory(PyObject*, PyObject*) {
	if (g_state == nullptr || g_state->executable_path.empty()) {
		PyErr_SetString(PyExc_RuntimeError, "Tauon's executable directory is unavailable");
		return nullptr;
	}
	return PyUnicode_DecodeFSDefault(g_state->executable_path.parent_path().string().c_str());
}

PyObject* bridge_portable_mode(PyObject*, PyObject*) {
	return PyBool_FromLong(g_state != nullptr && g_state->portable ? 1 : 0);
}

PyObject* bridge_owns_instance_lock(PyObject*, PyObject*) {
	if (g_state == nullptr) {
		Py_RETURN_FALSE;
	}
#if defined(_WIN32)
	return PyBool_FromLong(g_state->instance_lock_handle != INVALID_HANDLE_VALUE ? 1 : 0);
#else
	return PyBool_FromLong(g_state->instance_lock_fd != -1 ? 1 : 0);
#endif
}

bool dict_set_owned(PyObject* dictionary, const char* key, PyObject* value) {
	if (value == nullptr) {
		return false;
	}
	const int result = PyDict_SetItemString(dictionary, key, value);
	Py_DECREF(value);
	return result == 0;
}

bool dict_set_long(PyObject* dictionary, const char* key, long long value) {
	return dict_set_owned(dictionary, key, PyLong_FromLongLong(value));
}

bool dict_set_unsigned(PyObject* dictionary, const char* key, unsigned long long value) {
	return dict_set_owned(dictionary, key, PyLong_FromUnsignedLongLong(value));
}

bool dict_set_float(PyObject* dictionary, const char* key, double value) {
	return dict_set_owned(dictionary, key, PyFloat_FromDouble(value));
}

bool dict_set_bytes(PyObject* dictionary, const char* key, const char* value) {
	return dict_set_owned(dictionary, key, PyBytes_FromString(value != nullptr ? value : ""));
}

PyObject* event_to_dictionary(const SDL_Event& event) {
	PyObject* result = PyDict_New();
	if (result == nullptr || !dict_set_unsigned(result, "type", event.type)) {
		Py_XDECREF(result);
		return nullptr;
	}

	bool valid = true;
	switch (event.type) {
	case SDL_EVENT_GAMEPAD_ADDED:
		valid = dict_set_unsigned(result, "which", event.gdevice.which);
		break;
	case SDL_EVENT_GAMEPAD_AXIS_MOTION:
		valid = dict_set_unsigned(result, "axis", event.gaxis.axis) &&
			dict_set_long(result, "value", event.gaxis.value);
		break;
	case SDL_EVENT_GAMEPAD_BUTTON_DOWN:
	case SDL_EVENT_GAMEPAD_BUTTON_UP:
		valid = dict_set_unsigned(result, "button", event.gbutton.button);
		break;
	case SDL_EVENT_DROP_TEXT:
	case SDL_EVENT_DROP_FILE:
		valid = dict_set_bytes(result, "data", event.drop.data) &&
			dict_set_float(result, "x", event.drop.x) &&
			dict_set_float(result, "y", event.drop.y);
		break;
	case SDL_EVENT_DROP_BEGIN:
	case SDL_EVENT_DROP_POSITION:
	case SDL_EVENT_DROP_COMPLETE:
		valid = dict_set_float(result, "x", event.drop.x) &&
			dict_set_float(result, "y", event.drop.y);
		break;
	case SDL_EVENT_TEXT_EDITING:
		valid = dict_set_bytes(result, "text", event.edit.text);
		break;
	case SDL_EVENT_TEXT_INPUT:
		valid = dict_set_bytes(result, "text", event.text.text);
		break;
	case SDL_EVENT_MOUSE_MOTION:
		valid = dict_set_unsigned(result, "window_id", event.motion.windowID) &&
			dict_set_float(result, "x", event.motion.x) &&
			dict_set_float(result, "y", event.motion.y);
		break;
	case SDL_EVENT_MOUSE_BUTTON_DOWN:
	case SDL_EVENT_MOUSE_BUTTON_UP:
		valid = dict_set_unsigned(result, "window_id", event.button.windowID) &&
			dict_set_unsigned(result, "button", event.button.button) &&
			dict_set_float(result, "x", event.button.x) &&
			dict_set_float(result, "y", event.button.y);
		break;
	case SDL_EVENT_KEY_DOWN:
	case SDL_EVENT_KEY_UP:
		valid = dict_set_unsigned(result, "key", event.key.key) &&
			dict_set_unsigned(result, "scancode", event.key.scancode);
		break;
	case SDL_EVENT_MOUSE_WHEEL:
		valid = dict_set_float(result, "y", event.wheel.y) &&
			dict_set_long(result, "integer_y", event.wheel.integer_y);
		break;
	case SDL_EVENT_FINGER_DOWN:
	case SDL_EVENT_FINGER_UP:
	case SDL_EVENT_FINGER_MOTION:
	case SDL_EVENT_FINGER_CANCELED:
		valid = dict_set_unsigned(result, "finger_id", event.tfinger.fingerID) &&
			dict_set_float(result, "x", event.tfinger.x) &&
			dict_set_float(result, "y", event.tfinger.y) &&
			dict_set_float(result, "dy", event.tfinger.dy);
		break;
	default:
		if (event.type >= SDL_EVENT_WINDOW_FIRST && event.type <= SDL_EVENT_WINDOW_LAST) {
			valid = dict_set_unsigned(result, "window_id", event.window.windowID) &&
				dict_set_long(result, "data1", event.window.data1) &&
				dict_set_long(result, "data2", event.window.data2);
		}
		break;
	}

	if (!valid) {
		Py_DECREF(result);
		return nullptr;
	}
	return result;
}

PyObject* bridge_poll_events(PyObject*, PyObject*) {
	PyObject* events = PyList_New(0);
	if (events == nullptr) {
		return nullptr;
	}

	SDL_Event event;
	while (SDL_PollEvent(&event)) {
		PyObject* dictionary = event_to_dictionary(event);
		if (dictionary == nullptr || PyList_Append(events, dictionary) != 0) {
			Py_XDECREF(dictionary);
			Py_DECREF(events);
			return nullptr;
		}
		Py_DECREF(dictionary);
	}
	return events;
}

PyObject* bridge_wait_for_event(PyObject*, PyObject* argument) {
	const long timeout = PyLong_AsLong(argument);
	if (timeout == -1 && PyErr_Occurred()) {
		return nullptr;
	}
	if (timeout < 0 || timeout > 60000) {
		PyErr_SetString(PyExc_ValueError, "event wait timeout must be between 0 and 60000 milliseconds");
		return nullptr;
	}
	bool received = false;
	Py_BEGIN_ALLOW_THREADS
	received = SDL_WaitEventTimeout(nullptr, static_cast<Sint32>(timeout));
	Py_END_ALLOW_THREADS
	return PyBool_FromLong(received ? 1 : 0);
}

PyObject* bridge_wake_event_loop(PyObject*, PyObject*) {
	SDL_Event event{};
	event.type = SDL_EVENT_USER;
	if (!SDL_PushEvent(&event)) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	Py_RETURN_NONE;
}

PyObject* bridge_key_from_name(PyObject*, PyObject* argument) {
	const char* name = PyUnicode_AsUTF8(argument);
	if (name == nullptr) return nullptr;
	return PyLong_FromUnsignedLong(SDL_GetKeyFromName(name));
}

PyObject* bridge_scancode_from_name(PyObject*, PyObject* argument) {
	const char* name = PyUnicode_AsUTF8(argument);
	if (name == nullptr) return nullptr;
	return PyLong_FromLong(SDL_GetScancodeFromName(name));
}

PyObject* bridge_init_subsystem(PyObject*, PyObject* argument) {
	const unsigned long flags = PyLong_AsUnsignedLong(argument);
	if (PyErr_Occurred()) return nullptr;
	if (!SDL_InitSubSystem(static_cast<SDL_InitFlags>(flags))) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	Py_RETURN_NONE;
}

PyObject* bridge_pump_events(PyObject*, PyObject*) {
	SDL_PumpEvents();
	Py_RETURN_NONE;
}

PyObject* bridge_is_gamepad(PyObject*, PyObject* argument) {
	const unsigned long identifier = PyLong_AsUnsignedLong(argument);
	if (PyErr_Occurred()) return nullptr;
	return PyBool_FromLong(SDL_IsGamepad(static_cast<SDL_JoystickID>(identifier)) ? 1 : 0);
}

PyObject* bridge_open_gamepad(PyObject*, PyObject* argument) {
	const unsigned long identifier = PyLong_AsUnsignedLong(argument);
	if (PyErr_Occurred()) return nullptr;
	SDL_Gamepad* gamepad = SDL_OpenGamepad(static_cast<SDL_JoystickID>(identifier));
	if (gamepad == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	return PyLong_FromVoidPtr(gamepad);
}

PyObject* bridge_gamepad_name(PyObject*, PyObject* argument) {
	const unsigned long identifier = PyLong_AsUnsignedLong(argument);
	if (PyErr_Occurred()) return nullptr;
	const char* name = SDL_GetGamepadNameForID(static_cast<SDL_JoystickID>(identifier));
	if (name == nullptr) Py_RETURN_NONE;
	return PyUnicode_FromString(name);
}

PyObject* bridge_sdl_version(PyObject*, PyObject*) {
	return PyLong_FromLong(SDL_GetVersion());
}

PyObject* bridge_set_clipboard_text(PyObject*, PyObject* argument) {
	if (!PyUnicode_Check(argument)) {
		PyErr_SetString(PyExc_TypeError, "clipboard text must be a string");
		return nullptr;
	}

	PyObject* encoded = PyUnicode_AsEncodedString(argument, "utf-8", "surrogateescape");
	if (encoded == nullptr) {
		return nullptr;
	}
	const bool success = SDL_SetClipboardText(PyBytes_AS_STRING(encoded));
	Py_DECREF(encoded);
	if (!success) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	Py_RETURN_NONE;
}

PyObject* bridge_get_clipboard_text(PyObject*, PyObject*) {
	char* text = SDL_GetClipboardText();
	if (text == nullptr) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	PyObject* result = PyUnicode_DecodeUTF8(text, -1, "surrogateescape");
	SDL_free(text);
	return result;
}

PyObject* bridge_has_clipboard_text(PyObject*, PyObject*) {
	return PyBool_FromLong(SDL_HasClipboardText() ? 1 : 0);
}

PyObject* bridge_show_error_message(PyObject*, PyObject* args) {
	const char* title = nullptr;
	const char* message = nullptr;
	if (!PyArg_ParseTuple(args, "ss", &title, &message)) return nullptr;
	if (!SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, title, message, g_state != nullptr ? g_state->window.get() : nullptr)) {
		PyErr_SetString(PyExc_RuntimeError, SDL_GetError());
		return nullptr;
	}
	Py_RETURN_NONE;
}

PyMethodDef bridge_methods[] = {
	{"is_active", bridge_is_active, METH_NOARGS, "Return whether Tauon is running under the native bootstrap."},
	{"window_address", bridge_window_address, METH_NOARGS, "Return the transitional native SDL_Window address."},
	{"renderer_address", bridge_renderer_address, METH_NOARGS, "Return the transitional native SDL_Renderer address."},
	{"window_size", bridge_window_size, METH_NOARGS, "Return the main window size in logical points."},
	{"renderer_name", bridge_renderer_name, METH_NOARGS, "Return the main renderer name."},
	{"sdl_library_path", bridge_sdl_library_path, METH_NOARGS, "Return the SDL library used by the native executable."},
	{"user_data_directory", bridge_user_data_directory, METH_NOARGS, "Return Tauon's native-resolved user data directory."},
	{"executable_directory", bridge_executable_directory, METH_NOARGS, "Return the directory containing the native executable."},
	{"portable_mode", bridge_portable_mode, METH_NOARGS, "Return whether a portable marker was found beside the executable."},
	{"owns_instance_lock", bridge_owns_instance_lock, METH_NOARGS, "Return whether the native launcher owns Tauon's instance lock."},
	{"poll_events", bridge_poll_events, METH_NOARGS, "Poll pending SDL events into Python-owned dictionaries."},
	{"wait_for_event", bridge_wait_for_event, METH_O, "Wait for SDL activity without removing the pending event."},
	{"wake_event_loop", bridge_wake_event_loop, METH_NOARGS, "Wake the native SDL event loop."},
	{"key_from_name", bridge_key_from_name, METH_O, "Return an SDL keycode by name."},
	{"scancode_from_name", bridge_scancode_from_name, METH_O, "Return an SDL scancode by name."},
	{"init_subsystem", bridge_init_subsystem, METH_O, "Initialize an SDL subsystem."},
	{"pump_events", bridge_pump_events, METH_NOARGS, "Pump SDL events."},
	{"is_gamepad", bridge_is_gamepad, METH_O, "Return whether a joystick is a gamepad."},
	{"open_gamepad", bridge_open_gamepad, METH_O, "Open a gamepad."},
	{"gamepad_name", bridge_gamepad_name, METH_O, "Return a gamepad name."},
	{"sdl_version", bridge_sdl_version, METH_NOARGS, "Return the linked SDL version."},
	{"create_texture", native_create_texture, METH_VARARGS, "Create an SDL texture and return its native handle."},
	{"create_texture_from_rgba", native_create_texture_from_rgba, METH_VARARGS, "Create a texture from packed RGBA pixels."},
	{"destroy_texture", native_destroy_texture, METH_O, "Destroy an SDL texture handle."},
	{"get_render_target", native_get_render_target, METH_O, "Return the current render-target handle."},
	{"set_render_target", native_set_render_target, METH_VARARGS, "Set the renderer target."},
	{"set_render_draw_blend_mode", native_set_render_draw_blend_mode, METH_VARARGS, "Set renderer blend mode."},
	{"set_render_draw_color", native_set_render_draw_color, METH_VARARGS, "Set renderer draw colour."},
	{"render_clear", native_render_clear, METH_O, "Clear the renderer target."},
	{"render_fill_rect", native_render_fill_rect, METH_VARARGS, "Fill a rectangle."},
	{"render_texture", native_render_texture, METH_VARARGS, "Render a texture."},
	{"set_texture_blend_mode", native_set_texture_blend_mode, METH_VARARGS, "Set texture blend mode."},
	{"set_texture_scale_mode", native_set_texture_scale_mode, METH_VARARGS, "Set texture scale mode."},
	{"set_texture_alpha_mod", native_set_texture_alpha_mod, METH_VARARGS, "Set texture alpha modulation."},
	{"update_texture", native_update_texture, METH_VARARGS, "Upload texture pixels."},
	{"set_render_clip_rect", native_set_render_clip_rect, METH_VARARGS, "Set renderer clipping."},
	{"get_window_flags", native_get_window_flags, METH_O, "Return window flags."},
	{"maximize_window", native_maximize_window, METH_O, "Maximize a window."},
	{"minimize_window", native_minimize_window, METH_O, "Minimize a window."},
	{"restore_window", native_restore_window, METH_O, "Restore a window."},
	{"render_geometry", native_render_geometry, METH_VARARGS, "Render indexed geometry."},
	{"create_popup_window", native_create_popup_window, METH_VARARGS, "Create a popup window."},
	{"create_window", native_create_window, METH_VARARGS, "Create an SDL window."},
	{"create_renderer", native_create_renderer, METH_VARARGS, "Create a renderer for a window."},
	{"destroy_renderer", native_destroy_renderer, METH_O, "Destroy a renderer."},
	{"destroy_window", native_destroy_window, METH_O, "Destroy a window."},
	{"get_window_id", native_get_window_id, METH_O, "Return a window ID."},
	{"get_window_size", native_get_window_size, METH_VARARGS, "Return logical or pixel window size."},
	{"set_window_size", native_set_window_size, METH_VARARGS, "Set window size."},
	{"set_window_position", native_set_window_position, METH_VARARGS, "Set window position."},
	{"set_window_mouse_grab", native_set_window_mouse_grab, METH_VARARGS, "Set window mouse grab."},
	{"capture_mouse", native_capture_mouse, METH_O, "Set global mouse capture."},
	{"show_window", native_show_window, METH_O, "Show a window."},
	{"hide_window", native_hide_window, METH_O, "Hide a window."},
	{"raise_window", native_raise_window, METH_O, "Raise a window."},
	{"render_present", native_render_present, METH_O, "Present a renderer."},
	{"render_line", native_render_line, METH_VARARGS, "Render a line."},
	{"get_texture_size", native_get_texture_size, METH_O, "Return texture dimensions."},
	{"create_texture_from_cairo", native_create_texture_from_cairo, METH_VARARGS, "Upload a Cairo ARGB32/RGB24 buffer."},
	{"read_render_pixels", native_read_render_pixels, METH_VARARGS, "Read renderer pixels into a Python-owned buffer."},
	{"compose_blend_mode", native_compose_blend_mode, METH_VARARGS, "Compose an SDL custom blend mode."},
	{"set_window_minimum_size", native_set_window_minimum_size, METH_VARARGS, "Set minimum window size."},
	{"set_window_resizable", native_set_window_resizable, METH_VARARGS, "Set resizable state."},
	{"set_window_bordered", native_set_window_bordered, METH_VARARGS, "Set window borders."},
	{"set_window_opacity", native_set_window_opacity, METH_VARARGS, "Set window opacity."},
	{"set_window_always_on_top", native_set_window_always_on_top, METH_VARARGS, "Set always-on-top state."},
	{"set_window_title", native_set_window_title, METH_VARARGS, "Set window title."},
	{"set_window_fullscreen", native_set_window_fullscreen, METH_VARARGS, "Set fullscreen state."},
	{"sync_window", native_sync_window, METH_O, "Synchronize pending window operations."},
	{"get_window_position", native_get_window_position, METH_O, "Return window position."},
	{"get_mouse_state", native_get_mouse_state, METH_O, "Return mouse buttons and coordinates."},
	{"set_texture_color_mod", native_set_texture_color_mod, METH_VARARGS, "Set texture colour modulation."},
	{"create_system_cursor", native_create_system_cursor, METH_O, "Create a system cursor."},
	{"set_cursor", native_set_cursor, METH_O, "Set the active cursor."},
	{"create_color_cursor", native_create_color_cursor, METH_VARARGS, "Create a colour cursor from ARGB pixels."},
	{"set_window_hit_test", native_set_window_hit_test, METH_VARARGS, "Set a Python window hit-test callback."},
	{"start_text_input", native_start_text_input, METH_O, "Start text input for a window."},
	{"stop_text_input", native_stop_text_input, METH_O, "Stop text input for a window."},
	{"set_text_input_area", native_set_text_input_area, METH_VARARGS, "Set the active text input area."},
	{"get_display_refresh_rate", native_get_display_refresh_rate, METH_O, "Get the window display refresh rate."},
	{"create_tray", native_create_tray, METH_VARARGS, "Create a system tray icon."},
	{"set_tray_icon", native_set_tray_icon, METH_VARARGS, "Update a system tray icon."},
	{"set_tray_tooltip", native_set_tray_tooltip, METH_VARARGS, "Update a system tray tooltip."},
	{"create_tray_menu", native_create_tray_menu, METH_O, "Create a tray menu."},
	{"insert_tray_entry", native_insert_tray_entry, METH_VARARGS, "Insert a tray menu entry."},
	{"set_tray_entry_callback", native_set_tray_entry_callback, METH_VARARGS, "Set a tray entry callback."},
	{"destroy_tray", native_destroy_tray, METH_O, "Destroy a tray icon."},
	{"set_window_icon", native_set_window_icon, METH_VARARGS, "Set a window icon from RGBA pixels."},
	{"set_window_progress_state", native_set_window_progress_state, METH_VARARGS, "Set taskbar progress state."},
	{"set_window_progress_value", native_set_window_progress_value, METH_VARARGS, "Set taskbar progress value."},
	{"video_driver", native_video_driver, METH_NOARGS, "Get the active SDL video driver."},
	{"flush_renderer", native_flush_renderer, METH_O, "Flush queued renderer commands."},
	{"render_texture_rotated", native_render_texture_rotated, METH_VARARGS, "Render a rotated texture."},
	{"gl_get_current_context", native_gl_get_current_context, METH_NOARGS, "Get the current OpenGL context."},
	{"gl_set_attribute", native_gl_set_attribute, METH_VARARGS, "Set an OpenGL context attribute."},
	{"gl_create_context", native_gl_create_context, METH_O, "Create an OpenGL context."},
	{"gl_make_current", native_gl_make_current, METH_VARARGS, "Make an OpenGL context current."},
	{"create_texture_from_opengl", native_create_texture_from_opengl, METH_VARARGS, "Wrap an OpenGL texture for SDL rendering."},
	{"set_clipboard_text", bridge_set_clipboard_text, METH_O, "Set UTF-8 text on the system clipboard."},
	{"get_clipboard_text", bridge_get_clipboard_text, METH_NOARGS, "Get UTF-8 text from the system clipboard."},
	{"has_clipboard_text", bridge_has_clipboard_text, METH_NOARGS, "Return whether the clipboard contains text."},
	{"show_error_message", bridge_show_error_message, METH_VARARGS, "Show a native error message box."},
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
#if defined(TAUON_DEVELOPMENT_BUILD)
	return std::filesystem::path(TAUON_SOURCE_DIR);
#else
	return {};
#endif
}

std::filesystem::path python_site_packages_directory() {
	if (const char* override_path = std::getenv("TAUON_PYTHON_SITE_PACKAGES")) {
		return std::filesystem::path(override_path);
	}
#if defined(TAUON_DEVELOPMENT_BUILD)
	return std::filesystem::path(TAUON_PYTHON_SITE_PACKAGES);
#else
	return {};
#endif
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

PyStatus set_config_path(PyConfig& config, wchar_t** target, const std::filesystem::path& path) {
#if defined(_WIN32)
	return PyConfig_SetString(&config, target, path.c_str());
#else
	wchar_t* decoded = Py_DecodeLocale(path.string().c_str(), nullptr);
	if (decoded == nullptr) {
		return PyStatus_Error("unable to decode a bundled Python path");
	}
	const PyStatus status = PyConfig_SetString(&config, target, decoded);
	PyMem_RawFree(decoded);
	return status;
#endif
}

PyStatus append_config_path(PyConfig& config, const std::filesystem::path& path) {
#if defined(_WIN32)
	return PyWideStringList_Append(&config.module_search_paths, path.c_str());
#else
	wchar_t* decoded = Py_DecodeLocale(path.string().c_str(), nullptr);
	if (decoded == nullptr) {
		return PyStatus_Error("unable to decode a bundled Python search path");
	}
	const PyStatus status = PyWideStringList_Append(&config.module_search_paths, decoded);
	PyMem_RawFree(decoded);
	return status;
#endif
}

int run_python(NativeState& state, int argc, char** argv) {
	if (PyImport_AppendInittab("tauon_native", &PyInit_tauon_native) == -1) {
		std::cerr << "Tauon: failed to register the native Python bridge\n";
		return 1;
	}

	const bool bundled = is_bundled_install(state.executable_path);
	const std::filesystem::path python_directory = bundled_python_directory(state.executable_path);
	PyConfig config;
	if (bundled) {
		PyConfig_InitIsolatedConfig(&config);
		config.module_search_paths_set = 1;
		config.site_import = 0;
		config.user_site_directory = 0;
		config.write_bytecode = 0;
	} else {
		PyConfig_InitPythonConfig(&config);
	}
	config.parse_argv = 0;
	PyStatus status = set_config_path(config, &config.program_name, state.executable_path);
	if (!PyStatus_Exception(status)) {
		status = set_config_path(config, &config.executable, state.executable_path);
	}
	if (bundled && !PyStatus_Exception(status)) {
		status = set_config_path(config, &config.home, python_directory);
	}
	if (bundled && !PyStatus_Exception(status)) {
		status = append_config_path(config, python_directory / "stdlib");
	}
	if (bundled && !PyStatus_Exception(status)) {
		status = append_config_path(config, python_directory / "stdlib" / "lib-dynload");
	}
	if (bundled && !PyStatus_Exception(status)) {
		status = append_config_path(config, python_directory / "site-packages");
	}
	if (!PyStatus_Exception(status)) {
		status = PyConfig_SetBytesArgv(&config, argc, argv);
	}
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
			"import json\n"
			"import os\n"
			"from pathlib import Path\n"
			"import cairo\n"
			"import gi\n"
			"gi.require_version('Gtk', '3.0')\n"
			"gi.require_version('Pango', '1.0')\n"
			"gi.require_version('PangoCairo', '1.0')\n"
			"gi.require_version('Rsvg', '2.0')\n"
			"from gi.repository import GLib, Gtk, PangoCairo, Rsvg\n"
			"from PIL import Image\n"
			"import tauon\n"
			"import tauon_native\n"
			"Gtk.Settings.get_default()\n"
			"surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 16, 16)\n"
			"context = cairo.Context(surface)\n"
			"layout = PangoCairo.create_layout(context)\n"
			"layout.set_text('Tauon smoke test', -1)\n"
			"PangoCairo.show_layout(context, layout)\n"
			"surface.flush()\n"
			"surface.finish()\n"
			"assert os.environ.get('SDL_MAIN_NOIMPL') == '1'\n"
			"assert tauon_native.owns_instance_lock()\n"
			"window = tauon_native.window_address()\n"
			"renderer = tauon_native.renderer_address()\n"
			"assert window > 0 and renderer > 0\n"
			"assert tauon_native.renderer_name()\n"
			"texture = tauon_native.create_texture(renderer, 372645892, 1, 2, 2)\n"
			"tauon_native.update_texture(texture, None, bytes(16), 8)\n"
			"tauon_native.destroy_texture(texture)\n"
			"test_window = tauon_native.create_window('Tauon native smoke test', 8, 8, 0x8)\n"
			"test_renderer = tauon_native.create_renderer(test_window, None)\n"
			"tauon_native.set_render_draw_color(test_renderer, 1, 2, 3, 255)\n"
			"tauon_native.render_clear(test_renderer)\n"
			"tauon_native.render_present(test_renderer)\n"
			"tauon_native.destroy_renderer(test_renderer)\n"
			"tauon_native.destroy_window(test_window)\n"
			"assert isinstance(tauon_native.poll_events(), list)\n"
			"state_path = Path(tauon_native.user_data_directory()) / 'window-state.json'\n"
			"if state_path.is_file():\n"
			"    state = json.loads(state_path.read_text(encoding='utf-8'))\n"
			"    if not state.get('maximized', False):\n"
			"        assert tauon_native.window_size() == (state['width'], state['height'])\n"
			"    borderless = bool(tauon_native.get_window_flags(window) & 0x10)\n"
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
	// SDL's Wayland backend can dispatch callbacks registered by PySDL3 while
	// destroying the renderer and window.  Those callbacks use ctypes, so SDL
	// must be torn down before Py_FinalizeEx() releases Python's callback
	// machinery.  Doing this afterwards causes a use-after-finalize segfault.
	shutdown_native_sdl(state);
	g_state = nullptr;
#if defined(_WIN32)
	// PyGObject and GTK can crash while their DLL state is torn down by
	// Py_FinalizeEx(). The process exits immediately after this function, so
	// let Windows reclaim the embedded interpreter instead.
#else
	if (Py_FinalizeEx() < 0 && exit_code == 0) {
		exit_code = 120;
	}
#endif
	return exit_code;
}

}  // namespace

int tauon_main(int argc, char** argv) {
	if (has_argument(argc, argv, "-h") || has_argument(argc, argv, "--help")) {
		print_usage(argc > 0 ? argv[0] : "tauon-native");
		return 0;
	}
	// Match the shell launcher: controller commands never start a new player.
	if (has_controller_argument(argc, argv)) {
		return forward_arguments(argc, argv);
	}

	NativeState state;
	state.executable_path = current_executable_path(argc > 0 ? argv[0] : "tauon-native");
	state.portable = std::filesystem::exists(state.executable_path.parent_path() / "portable");
	configure_bundled_environment(state.executable_path);
	g_state = &state;
	const InstanceLockResult instance_lock = acquire_instance_lock(state, argv[0]);
	if (instance_lock == InstanceLockResult::AlreadyRunning || has_argument(argc, argv, "--no-start")) {
		const int exit_code = forward_arguments(argc, argv);
		shutdown_native_app(state);
		g_state = nullptr;
		return exit_code;
	}
	if (!initialise_native_app(state, argc, argv)) {
		shutdown_native_app(state);
		g_state = nullptr;
		return 1;
	}

	const int exit_code = run_python(state, argc, argv);
	shutdown_native_app(state);
	g_state = nullptr;
	return exit_code;
}

#if defined(_WIN32)
std::string utf8_from_wide(const wchar_t* value) {
	if (value == nullptr) {
		return {};
	}
	const int size = WideCharToMultiByte(CP_UTF8, 0, value, -1, nullptr, 0, nullptr, nullptr);
	if (size <= 1) {
		return {};
	}
	std::string result(static_cast<std::size_t>(size), '\0');
	WideCharToMultiByte(CP_UTF8, 0, value, -1, result.data(), size, nullptr, nullptr);
	result.resize(static_cast<std::size_t>(size - 1));
	return result;
}

int WINAPI WinMain(HINSTANCE, HINSTANCE, LPSTR, int) {
	int argc = 0;
	LPWSTR* wide_argv = CommandLineToArgvW(GetCommandLineW(), &argc);
	if (wide_argv == nullptr) {
		return 1;
	}
	std::vector<std::string> arguments;
	arguments.reserve(static_cast<std::size_t>(argc));
	for (int index = 0; index < argc; ++index) {
		arguments.push_back(utf8_from_wide(wide_argv[index]));
	}
	LocalFree(wide_argv);
	std::vector<char*> argv;
	argv.reserve(arguments.size());
	for (std::string& argument : arguments) {
		argv.push_back(argument.data());
	}
	return tauon_main(argc, argv.data());
}
#else
int main(int argc, char** argv) {
	return tauon_main(argc, argv);
}
#endif
