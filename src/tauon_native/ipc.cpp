#include "ipc.h"

#if defined(_WIN32)
#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0A00
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <sddl.h>
#else
#include <fcntl.h>
#include <poll.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/un.h>
#include <unistd.h>
#endif

#include <cerrno>
#include <cstdint>
#include <cstring>
#include <cwchar>
#include <iostream>
#include <optional>
#include <string>
#include <thread>
#include <vector>

// Wire format: the client sends "command" or "command\nargument" and the
// server answers with one byte, '1' if the command was accepted.

namespace {

constexpr std::size_t kMaxRequestSize = 64 * 1024;
constexpr int kTimeoutMs = 5000;

std::string encode_request(std::string_view command, std::string_view argument) {
	std::string request(command);
	if (!argument.empty()) {
		request.push_back('\n');
		request.append(argument);
	}
	return request;
}

// Runs on the server thread
bool dispatch(PyObject* handler, const std::string& request) {
	const std::size_t newline = request.find('\n');
	const std::size_t command_size = newline == std::string::npos ? request.size() : newline;
	const PyGILState_STATE gil_state = PyGILState_Ensure();
	PyObject* command = PyUnicode_DecodeUTF8(request.data(), static_cast<Py_ssize_t>(command_size), "replace");
	PyObject* argument = nullptr;
	if (newline == std::string::npos) {
		argument = Py_NewRef(Py_None);
	} else {
		argument = PyUnicode_DecodeFSDefaultAndSize(
			request.data() + newline + 1,
			static_cast<Py_ssize_t>(request.size() - newline - 1)
		);
	}
	PyObject* result = command != nullptr && argument != nullptr
		? PyObject_CallFunctionObjArgs(handler, command, argument, nullptr)
		: nullptr;
	Py_XDECREF(command);
	Py_XDECREF(argument);
	int accepted = result != nullptr ? PyObject_IsTrue(result) : -1;
	Py_XDECREF(result);
	if (accepted < 0) {
		PyErr_WriteUnraisable(handler);
		accepted = 0;
	}
	PyGILState_Release(gil_state);
	return accepted != 0;
}

#if defined(_WIN32)

struct Server {
	std::thread thread;
	PyObject* handler = nullptr;
	HANDLE pipe = INVALID_HANDLE_VALUE;
	HANDLE stop_event = nullptr;
};

Server* g_server = nullptr;

std::wstring process_user_sid(HANDLE process) {
	HANDLE token = nullptr;
	if (!OpenProcessToken(process, TOKEN_QUERY, &token)) {
		return {};
	}
	std::wstring result;
	DWORD size = 0;
	GetTokenInformation(token, TokenUser, nullptr, 0, &size);
	std::vector<unsigned char> buffer(size);
	LPWSTR text = nullptr;
	if (size > 0
		&& GetTokenInformation(token, TokenUser, buffer.data(), size, &size)
		&& ConvertSidToStringSidW(reinterpret_cast<TOKEN_USER*>(buffer.data())->User.Sid, &text)) {
		result = text;
		LocalFree(text);
	}
	CloseHandle(token);
	return result;
}

// Pipe names are global, so the name is keyed by user and data directory, and
// the server's DACL and the client's owner check keep users apart
std::wstring pipe_name(const std::filesystem::path& user_data_directory, const std::wstring& sid) {
	std::error_code error;
	std::filesystem::path directory = std::filesystem::weakly_canonical(user_data_directory, error);
	if (error) {
		directory = user_data_directory.lexically_normal();
	}
	std::wstring key = sid + L"|" + directory.wstring();
	while (key.size() > 1 && (key.back() == L'\\' || key.back() == L'/')) {
		key.pop_back();
	}
	CharLowerBuffW(key.data(), static_cast<DWORD>(key.size()));
	std::uint64_t hash = 14695981039346656037ULL;
	for (const wchar_t character : key) {
		hash ^= static_cast<std::uint64_t>(character);
		hash *= 1099511628211ULL;
	}
	wchar_t digest[17]{};
	std::swprintf(digest, 17, L"%016llx", static_cast<unsigned long long>(hash));
	return L"\\\\.\\pipe\\TauonMusicBox-" + std::wstring(digest);
}

enum class IoStatus {
	Done,
	MoreData,
	Failed,
};

// One overlapped read or write, abandoned after the timeout or once stop_event is set
IoStatus pipe_io(HANDLE pipe, bool write, void* buffer, DWORD size, DWORD& transferred, HANDLE stop_event) {
	OVERLAPPED overlapped{};
	overlapped.hEvent = CreateEventW(nullptr, TRUE, FALSE, nullptr);
	if (overlapped.hEvent == nullptr) {
		return IoStatus::Failed;
	}
	const BOOL started = write
		? WriteFile(pipe, buffer, size, nullptr, &overlapped)
		: ReadFile(pipe, buffer, size, nullptr, &overlapped);
	const DWORD start_error = started ? ERROR_SUCCESS : GetLastError();
	if (!started && start_error != ERROR_IO_PENDING && start_error != ERROR_MORE_DATA) {
		CloseHandle(overlapped.hEvent);
		return IoStatus::Failed;
	}
	if (start_error == ERROR_IO_PENDING) {
		const HANDLE events[2] = {overlapped.hEvent, stop_event};
		const DWORD wait = WaitForMultipleObjects(stop_event != nullptr ? 2 : 1, events, FALSE, kTimeoutMs);
		if (wait != WAIT_OBJECT_0) {
			CancelIoEx(pipe, &overlapped);
		}
	}
	const BOOL done = GetOverlappedResult(pipe, &overlapped, &transferred, TRUE);
	const DWORD result_error = done ? ERROR_SUCCESS : GetLastError();
	CloseHandle(overlapped.hEvent);
	if (done) {
		return IoStatus::Done;
	}
	return result_error == ERROR_MORE_DATA ? IoStatus::MoreData : IoStatus::Failed;
}

std::optional<std::string> read_message(HANDLE pipe, HANDLE stop_event) {
	std::string message;
	char buffer[4096];
	while (true) {
		DWORD received = 0;
		const IoStatus status = pipe_io(pipe, false, buffer, sizeof(buffer), received, stop_event);
		if (status == IoStatus::Failed) {
			return std::nullopt;
		}
		message.append(buffer, received);
		if (message.size() > kMaxRequestSize) {
			return std::nullopt;
		}
		if (status == IoStatus::Done) {
			return message;
		}
	}
}

void handle_client(Server& server) {
	const std::optional<std::string> request = read_message(server.pipe, server.stop_event);
	char reply = request && dispatch(server.handler, *request) ? '1' : '0';
	DWORD transferred = 0;
	if (pipe_io(server.pipe, true, &reply, 1, transferred, server.stop_event) == IoStatus::Done) {
		// Disconnecting discards unread data, so wait for the client to hang up
		char ignored = 0;
		pipe_io(server.pipe, false, &ignored, 1, transferred, server.stop_event);
	}
}

void serve(Server* server) {
	const HANDLE connect_event = CreateEventW(nullptr, TRUE, FALSE, nullptr);
	if (connect_event == nullptr) {
		return;
	}
	while (WaitForSingleObject(server->stop_event, 0) != WAIT_OBJECT_0) {
		OVERLAPPED overlapped{};
		overlapped.hEvent = connect_event;
		ResetEvent(connect_event);
		const DWORD error = ConnectNamedPipe(server->pipe, &overlapped) ? ERROR_SUCCESS : GetLastError();
		if (error == ERROR_IO_PENDING) {
			const HANDLE events[2] = {connect_event, server->stop_event};
			if (WaitForMultipleObjects(2, events, FALSE, INFINITE) != WAIT_OBJECT_0) {
				CancelIoEx(server->pipe, &overlapped);
				DWORD ignored = 0;
				GetOverlappedResult(server->pipe, &overlapped, &ignored, TRUE);
				break;
			}
			DWORD ignored = 0;
			if (!GetOverlappedResult(server->pipe, &overlapped, &ignored, FALSE)) {
				DisconnectNamedPipe(server->pipe);
				continue;
			}
		} else if (error != ERROR_SUCCESS && error != ERROR_PIPE_CONNECTED) {
			std::cerr << "Tauon: the command pipe failed (error " << error << ")\n";
			break;
		}
		handle_client(*server);
		DisconnectNamedPipe(server->pipe);
	}
	CloseHandle(connect_event);
}

bool start_server(Server& server, const std::filesystem::path& user_data_directory) {
	const std::wstring sid = process_user_sid(GetCurrentProcess());
	if (sid.empty()) {
		PyErr_SetString(PyExc_RuntimeError, "unable to determine the current user for the command pipe");
		return false;
	}
	// Protected DACL granting the current user alone
	const std::wstring sddl = L"D:P(A;;GA;;;" + sid + L")";
	PSECURITY_DESCRIPTOR descriptor = nullptr;
	if (!ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl.c_str(), SDDL_REVISION_1, &descriptor, nullptr)) {
		PyErr_SetFromWindowsErr(0);
		return false;
	}
	SECURITY_ATTRIBUTES attributes{sizeof(attributes), descriptor, FALSE};
	// FILE_FLAG_FIRST_PIPE_INSTANCE fails if another process already holds the name
	server.pipe = CreateNamedPipeW(
		pipe_name(user_data_directory, sid).c_str(),
		PIPE_ACCESS_DUPLEX | FILE_FLAG_OVERLAPPED | FILE_FLAG_FIRST_PIPE_INSTANCE,
		PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT | PIPE_REJECT_REMOTE_CLIENTS,
		1,
		4096,
		4096,
		0,
		&attributes
	);
	const DWORD error = GetLastError();
	LocalFree(descriptor);
	if (server.pipe == INVALID_HANDLE_VALUE) {
		PyErr_SetFromWindowsErr(static_cast<int>(error));
		return false;
	}
	server.stop_event = CreateEventW(nullptr, TRUE, FALSE, nullptr);
	if (server.stop_event == nullptr) {
		PyErr_SetFromWindowsErr(0);
		return false;
	}
	return true;
}

void signal_stop(Server& server) {
	SetEvent(server.stop_event);
}

void close_server(Server& server) {
	if (server.pipe != INVALID_HANDLE_VALUE) {
		CloseHandle(server.pipe);
	}
	if (server.stop_event != nullptr) {
		CloseHandle(server.stop_event);
	}
}

bool send_request(const std::filesystem::path& user_data_directory, const std::string& request) {
	const std::wstring sid = process_user_sid(GetCurrentProcess());
	if (sid.empty()) {
		std::cerr << "Tauon: unable to determine the current user\n";
		return false;
	}
	const std::wstring name = pipe_name(user_data_directory, sid);
	HANDLE pipe = INVALID_HANDLE_VALUE;
	DWORD error = ERROR_SUCCESS;
	for (int attempt = 0; attempt < 2; ++attempt) {
		// Identification level stops the server from impersonating us
		pipe = CreateFileW(
			name.c_str(),
			GENERIC_READ | GENERIC_WRITE,
			0,
			nullptr,
			OPEN_EXISTING,
			FILE_FLAG_OVERLAPPED | SECURITY_SQOS_PRESENT | SECURITY_IDENTIFICATION,
			nullptr
		);
		if (pipe != INVALID_HANDLE_VALUE) {
			break;
		}
		error = GetLastError();
		if (error != ERROR_PIPE_BUSY || !WaitNamedPipeW(name.c_str(), kTimeoutMs)) {
			break;
		}
	}
	if (pipe == INVALID_HANDLE_VALUE) {
		if (error == ERROR_FILE_NOT_FOUND) {
			std::cerr << "Tauon: no running instance found\n";
		} else {
			std::cerr << "Tauon: unable to connect to the running instance (error " << error << ")\n";
		}
		return false;
	}

	// The pipe name is public, so make sure our own user created it
	ULONG server_process_id = 0;
	bool trusted = false;
	if (GetNamedPipeServerProcessId(pipe, &server_process_id)) {
		const HANDLE process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, server_process_id);
		if (process != nullptr) {
			trusted = process_user_sid(process) == sid;
			CloseHandle(process);
		}
	}
	if (!trusted) {
		CloseHandle(pipe);
		std::cerr << "Tauon: refusing to send to a command pipe owned by another user\n";
		return false;
	}

	DWORD mode = PIPE_READMODE_MESSAGE;
	SetNamedPipeHandleState(pipe, &mode, nullptr, nullptr);
	std::string message = request;
	DWORD transferred = 0;
	char reply = '0';
	const bool sent = pipe_io(pipe, true, message.data(), static_cast<DWORD>(message.size()), transferred, nullptr)
		== IoStatus::Done;
	const bool answered = sent && pipe_io(pipe, false, &reply, 1, transferred, nullptr) == IoStatus::Done
		&& transferred == 1;
	CloseHandle(pipe);
	if (!answered) {
		std::cerr << "Tauon: the running instance did not respond\n";
		return false;
	}
	return reply == '1';
}

#else

struct Server {
	std::thread thread;
	PyObject* handler = nullptr;
	int listen_fd = -1;
	int wake_fds[2] = {-1, -1};
	std::filesystem::path socket_path;
};

Server* g_server = nullptr;

std::optional<sockaddr_un> socket_address(const std::filesystem::path& path) {
	const std::string text = path.string();
	sockaddr_un address{};
	if (text.size() >= sizeof(address.sun_path)) {
		return std::nullopt;
	}
	address.sun_family = AF_UNIX;
	std::memcpy(address.sun_path, text.c_str(), text.size() + 1);
	return address;
}

std::filesystem::path socket_path(const std::filesystem::path& user_data_directory) {
	return user_data_directory / "tauon.sock";
}

void set_close_on_exec(int fd) {
	fcntl(fd, F_SETFD, FD_CLOEXEC);
}

void prepare_connection(int fd) {
	set_close_on_exec(fd);
	const timeval timeout{kTimeoutMs / 1000, 0};
	setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
	setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout));
#if defined(SO_NOSIGPIPE)
	const int enabled = 1;
	setsockopt(fd, SOL_SOCKET, SO_NOSIGPIPE, &enabled, sizeof(enabled));
#endif
}

bool peer_is_current_user(int fd) {
#if defined(SO_PEERCRED)
	ucred credentials{};
	socklen_t size = sizeof(credentials);
	return getsockopt(fd, SOL_SOCKET, SO_PEERCRED, &credentials, &size) == 0 && credentials.uid == geteuid();
#else
	uid_t uid = 0;
	gid_t gid = 0;
	return getpeereid(fd, &uid, &gid) == 0 && uid == geteuid();
#endif
}

bool send_all(int fd, const char* data, std::size_t size) {
#if defined(MSG_NOSIGNAL)
	constexpr int flags = MSG_NOSIGNAL;
#else
	constexpr int flags = 0;
#endif
	while (size > 0) {
		const ssize_t sent = send(fd, data, size, flags);
		if (sent < 0 && errno == EINTR) {
			continue;
		}
		if (sent <= 0) {
			return false;
		}
		data += sent;
		size -= static_cast<std::size_t>(sent);
	}
	return true;
}

void handle_client(Server& server, int fd) {
	if (!peer_is_current_user(fd)) {
		return;
	}
	std::string request;
	char buffer[4096];
	while (true) {
		const ssize_t received = recv(fd, buffer, sizeof(buffer), 0);
		if (received < 0 && errno == EINTR) {
			continue;
		}
		if (received < 0) {
			return;
		}
		if (received == 0) {
			break;
		}
		request.append(buffer, static_cast<std::size_t>(received));
		if (request.size() > kMaxRequestSize) {
			return;
		}
	}
	const char reply = dispatch(server.handler, request) ? '1' : '0';
	send_all(fd, &reply, 1);
}

void serve(Server* server) {
	while (true) {
		pollfd fds[2] = {{server->listen_fd, POLLIN, 0}, {server->wake_fds[0], POLLIN, 0}};
		if (poll(fds, 2, -1) < 0) {
			if (errno == EINTR) {
				continue;
			}
			break;
		}
		if (fds[1].revents != 0 || (fds[0].revents & (POLLERR | POLLHUP | POLLNVAL)) != 0) {
			break;
		}
		const int client = accept(server->listen_fd, nullptr, nullptr);
		if (client < 0) {
			continue;
		}
		prepare_connection(client);
		handle_client(*server, client);
		close(client);
	}
}

bool start_server(Server& server, const std::filesystem::path& user_data_directory) {
	server.socket_path = socket_path(user_data_directory);
	const std::optional<sockaddr_un> address = socket_address(server.socket_path);
	if (!address) {
		PyErr_Format(PyExc_OSError, "the command socket path is too long: %s", server.socket_path.c_str());
		return false;
	}
	if (pipe(server.wake_fds) != 0) {
		PyErr_SetFromErrno(PyExc_OSError);
		return false;
	}
	set_close_on_exec(server.wake_fds[0]);
	set_close_on_exec(server.wake_fds[1]);
	server.listen_fd = socket(AF_UNIX, SOCK_STREAM, 0);
	if (server.listen_fd < 0) {
		PyErr_SetFromErrno(PyExc_OSError);
		return false;
	}
	set_close_on_exec(server.listen_fd);
	// We hold the instance lock, so an existing socket is left over from a crash
	unlink(server.socket_path.c_str());
	if (bind(server.listen_fd, reinterpret_cast<const sockaddr*>(&*address), sizeof(*address)) != 0
		|| chmod(server.socket_path.c_str(), S_IRUSR | S_IWUSR) != 0
		|| listen(server.listen_fd, 8) != 0) {
		PyErr_SetFromErrnoWithFilename(PyExc_OSError, server.socket_path.c_str());
		return false;
	}
	return true;
}

void signal_stop(Server& server) {
	const char byte = 0;
	[[maybe_unused]] const ssize_t written = write(server.wake_fds[1], &byte, 1);
}

void close_server(Server& server) {
	if (server.listen_fd >= 0) {
		close(server.listen_fd);
		unlink(server.socket_path.c_str());
	}
	for (const int fd : server.wake_fds) {
		if (fd >= 0) {
			close(fd);
		}
	}
}

bool send_request(const std::filesystem::path& user_data_directory, const std::string& request) {
	const std::filesystem::path path = socket_path(user_data_directory);
	const std::optional<sockaddr_un> address = socket_address(path);
	if (!address) {
		std::cerr << "Tauon: the command socket path is too long: " << path.string() << '\n';
		return false;
	}
	const int fd = socket(AF_UNIX, SOCK_STREAM, 0);
	if (fd < 0) {
		std::cerr << "Tauon: unable to create a socket: " << std::strerror(errno) << '\n';
		return false;
	}
	prepare_connection(fd);
	if (connect(fd, reinterpret_cast<const sockaddr*>(&*address), sizeof(*address)) != 0) {
		const int error = errno;
		close(fd);
		if (error == ENOENT || error == ECONNREFUSED) {
			std::cerr << "Tauon: no running instance found\n";
		} else {
			std::cerr << "Tauon: unable to connect to " << path.string() << ": " << std::strerror(error) << '\n';
		}
		return false;
	}
	if (!peer_is_current_user(fd)) {
		close(fd);
		std::cerr << "Tauon: refusing to send to a command socket owned by another user\n";
		return false;
	}
	char reply = '0';
	ssize_t received = -1;
	if (send_all(fd, request.data(), request.size()) && shutdown(fd, SHUT_WR) == 0) {
		do {
			received = recv(fd, &reply, 1, 0);
		} while (received < 0 && errno == EINTR);
	}
	close(fd);
	if (received != 1) {
		std::cerr << "Tauon: the running instance did not respond\n";
		return false;
	}
	return reply == '1';
}

#endif

}  // namespace

bool ipc_send(const std::filesystem::path& user_data_directory, std::string_view command, std::string_view argument) {
	const std::string request = encode_request(command, argument);
	if (request.size() > kMaxRequestSize) {
		std::cerr << "Tauon: the request to the running instance is too long\n";
		return false;
	}
	return send_request(user_data_directory, request);
}

bool ipc_start_server(const std::filesystem::path& user_data_directory, PyObject* handler) {
	if (g_server != nullptr) {
		PyErr_SetString(PyExc_RuntimeError, "the command server is already running");
		return false;
	}
	auto* server = new Server;
	if (!start_server(*server, user_data_directory)) {
		close_server(*server);
		delete server;
		return false;
	}
	server->handler = Py_NewRef(handler);
	server->thread = std::thread(serve, server);
	g_server = server;
	return true;
}

void ipc_stop_server() {
	Server* server = g_server;
	if (server == nullptr) {
		return;
	}
	g_server = nullptr;
	signal_stop(*server);
	// The server thread may be waiting for the GIL to run the handler
	Py_BEGIN_ALLOW_THREADS
	server->thread.join();
	Py_END_ALLOW_THREADS
	close_server(*server);
	Py_DECREF(server->handler);
	delete server;
}
