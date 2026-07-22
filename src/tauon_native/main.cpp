#include <SDL3/SDL.h>

#include "host_api.h"

#include <cmath>
#include <cerrno>
#include <charconv>
#include <cctype>
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

#if defined(_WIN32)
#include <windows.h>
#else
#include <dlfcn.h>
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
	std::filesystem::path sdl_library_path;
	std::filesystem::path user_data_directory;
	WindowState window_state;
	bool sdl_initialised = false;
	bool hidden = false;
};

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

std::filesystem::path user_data_directory(const char* executable_argument) {
	if (const char* override_path = std::getenv("TAUON_USER_DATA_DIR")) {
		return std::filesystem::path(override_path);
	}

	std::error_code error;
	const std::filesystem::path executable = std::filesystem::weakly_canonical(executable_argument, error);
	if (!error && std::filesystem::exists(executable.parent_path() / "portable")) {
		return executable.parent_path() / "user-data";
	}

#if defined(_WIN32)
	if (const char* local_app_data = std::getenv("LOCALAPPDATA")) {
		return std::filesystem::path(local_app_data) / "TauonMusicBox";
	}
	if (const char* app_data = std::getenv("APPDATA")) {
		return std::filesystem::path(app_data) / "TauonMusicBox";
	}
#elif !defined(__APPLE__)
	// Match Python's source-tree development mode when this executable is run
	// from the same checkout. Installed builds use the XDG location below.
	const std::filesystem::path project_root = std::filesystem::path(TAUON_SOURCE_DIR).parent_path();
	const std::filesystem::path relative = executable.lexically_relative(project_root);
	if (!error && !relative.empty() && *relative.begin() != "..") {
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
	// empty window between SDL_CreateWindow() and the first rendered splash.
	SDL_WindowFlags flags = SDL_WINDOW_RESIZABLE | SDL_WINDOW_TRANSPARENT | SDL_WINDOW_HIGH_PIXEL_DENSITY |
		SDL_WINDOW_HIDDEN;
	if (state.window_state.borderless) {
		flags |= SDL_WINDOW_BORDERLESS;
	}
	if (std::getenv("GAMESCOPE_WAYLAND_DISPLAY") != nullptr) {
		flags |= SDL_WINDOW_FULLSCREEN;
	}

	state.window.reset(SDL_CreateWindow("Tauon", state.window_state.width, state.window_state.height, flags));
	if (!state.window) {
		std::cerr << "Tauon: window creation failed: " << SDL_GetError() << '\n';
		return false;
	}
	if (state.window_state.position && (flags & SDL_WINDOW_FULLSCREEN) == 0) {
		SDL_SetWindowPosition(
			state.window.get(),
			state.window_state.position->first,
			state.window_state.position->second
		);
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
		// A window created with SDL_WINDOW_HIDDEN is not necessarily activated
		// when it is later shown. Request foreground focus explicitly so normal
		// launches behave like SDL_CreateWindow() with an initially visible
		// window. Compositors may decline the request; that is not fatal.
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

void shutdown_native_app(NativeState& state) {
	state.renderer.reset();
	state.window.reset();
	if (state.sdl_initialised) {
		SDL_Quit();
		state.sdl_initialised = false;
	}
}

std::filesystem::path executable_directory(const char* executable_argument) {
	std::error_code error;
	const std::filesystem::path executable = std::filesystem::weakly_canonical(executable_argument, error);
	if (!error) {
		return executable.parent_path();
	}
	return std::filesystem::absolute(executable_argument).parent_path();
}

int run_python_host(const NativeState& state, int argc, char** argv) {
	std::filesystem::path host_path;
	if (const char* override_path = std::getenv("TAUON_PYTHON_HOST_PATH")) {
		host_path = override_path;
	} else {
		host_path = executable_directory(argv[0]) / TAUON_PYTHON_HOST_FILENAME;
	}

#if defined(_WIN32)
	HMODULE library = LoadLibraryW(host_path.wstring().c_str());
	if (library == nullptr) {
		std::cerr << "Tauon: failed to load Python host: " << host_path << '\n';
		return 1;
	}
	auto host_run = reinterpret_cast<TauonPythonHostRun>(GetProcAddress(library, "tauon_python_host_run"));
#else
	void* library = dlopen(host_path.c_str(), RTLD_NOW | RTLD_GLOBAL);
	if (library == nullptr) {
		std::cerr << "Tauon: failed to load Python host " << host_path << ": " << dlerror() << '\n';
		return 1;
	}
	auto host_run = reinterpret_cast<TauonPythonHostRun>(dlsym(library, "tauon_python_host_run"));
#endif
	if (host_run == nullptr) {
		std::cerr << "Tauon: Python host is missing tauon_python_host_run: " << host_path << '\n';
#if defined(_WIN32)
		FreeLibrary(library);
#else
		dlclose(library);
#endif
		return 1;
	}

	const std::string sdl_library_path = state.sdl_library_path.string();
	const std::string user_directory_path = state.user_data_directory.string();
	const TauonPythonHostContext context{
		TAUON_PYTHON_HOST_ABI_VERSION,
		state.window.get(),
		state.renderer.get(),
		sdl_library_path.c_str(),
		user_directory_path.c_str(),
		TAUON_SOURCE_DIR,
		TAUON_PYTHON_SITE_PACKAGES,
	};
	const int exit_code = host_run(&context, argc, argv);
#if defined(_WIN32)
	FreeLibrary(library);
#else
	dlclose(library);
#endif
	return exit_code;
}

}  // namespace

int main(int argc, char** argv) {
	NativeState state;
	if (!initialise_native_app(state, argc, argv)) {
		shutdown_native_app(state);
		return 1;
	}

	const int exit_code = run_python_host(state, argc, argv);
	shutdown_native_app(state);
	return exit_code;
}
