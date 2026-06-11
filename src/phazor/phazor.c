// PHAzOR - Audio playback module for Tauon Music Box
//
// Copyright © 2020, Taiko2k captain(dot)gxj(at)gmail.com
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

#define STRINGIFY(x) #x
#define TOSTRING(x) STRINGIFY(x)
#if __STDC_VERSION__ < 201710L
	#pragma message("Current __STDC_VERSION__ value: " TOSTRING(__STDC_VERSION__))
	#error "Phazor requires C17 or later."
#endif
#if __STDC_VERSION__ < 202311L
	#pragma message("Note: C23 not supported! Current __STDC_VERSION__ value: " TOSTRING(__STDC_VERSION__))
//	#error "Phazor requires C23 or later."
#endif

#define MINI

#ifdef WIN64
	#include <windows.h>
	#ifndef __MINGW64__
		#define usleep(usec) Sleep((usec) / 1000)  // Convert microseconds to milliseconds
	#endif
#else
	#include <unistd.h>
#endif

#ifdef PIPE
	#undef MINI
#endif

//#define MINI

#ifdef PIPE
	#include <pipewire/pipewire.h>
	#include <spa/param/audio/format-utils.h>
	#include <spa/pod/builder.h>
	#include <spa/utils/result.h>
#endif

#define _GNU_SOURCE
// C23 has it by default
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <limits.h>
#include <math.h>
#include <pthread.h>
#include <time.h>


#ifdef MINI
	#define MINIAUDIO_IMPLEMENTATION
	#define MA_NO_GENERATION
	#define MA_NO_DECODING
	#define MA_NO_ENCODING
	#define MA_ENABLE_ONLY_SPECIFIC_BACKENDS
	#if defined(__ANDROID__)
		#define MA_ENABLE_AAUDIO
		#define MA_ENABLE_OPENSL
	#else
		#define MA_ENABLE_WASAPI
		#define MA_ENABLE_PULSEAUDIO
		#define MA_ENABLE_COREAUDIO
		#define MA_ENABLE_OSS
		#define MA_ENABLE_SNDIO
		#define MA_ENABLE_AUDIO4
	#endif	//#define MA_DEBUG_OUTPUT
	#include "miniaudio/miniaudio.h"
#endif

#include <FLAC/stream_decoder.h>
#include <mpg123.h>
#include "vorbis/codec.h"
#include "vorbis/vorbisfile.h"
#include "opus/opusfile.h"
#include <sys/stat.h>
#include <samplerate.h>
#include <libopenmpt/libopenmpt.h>
#include <libopenmpt/libopenmpt_stream_callbacks_file.h>
#include "kissfft/kiss_fftr.h"
#include "wavpack/wavpack.h"
#include "gme/gme.h"

#include <Python.h>
// Module method definitions (if any)
static PyMethodDef PhazorMethods[] = {
	{NULL, NULL, 0, NULL} // Sentinel
};

// Module definition
static struct PyModuleDef phazor_module = {
	PyModuleDef_HEAD_INIT,
	"phazor",                  // Module name
	NULL,                      // Module documentation (may be NULL)
	-1,                        // Size of per-interpreter state of the module
	PhazorMethods              // Methods table
};

#ifdef WIN64
	__declspec(dllexport)
	#define EXPORT __declspec(dllexport)
#else
	#define EXPORT
#endif

enum logtypes {LOG_INFO, LOG_WARNING, LOG_ERROR, LOG_CRITICAL, LOG_DEBUG};

static void log_msg(int type, const char *fmt, ...) {
	PyGILState_STATE gstate = PyGILState_Ensure();
	static PyObject *logging = NULL;

	// import logging module on demand
	if (logging == NULL){
		logging = PyImport_ImportModule("logging");
		if (logging == NULL) {
			PyErr_SetString(
				PyExc_ImportError,
				"Could not import module 'logging'"
			);
			PyGILState_Release(gstate);
			return;
		}
	}
	/* format message */
	char buffer[1024];

	va_list args;
	va_start(args, fmt);
	vsnprintf(buffer, sizeof(buffer), fmt, args);
	va_end(args);
	PyObject *py_msg = PyUnicode_FromString(buffer);

	const char *method = NULL;
	switch (type) {
		case LOG_INFO:     method = "info";     break;
		case LOG_WARNING:  method = "warning";  break;
		case LOG_ERROR:    method = "error";    break;
		case LOG_CRITICAL: method = "critical"; break;
		case LOG_DEBUG:    method = "debug";    break;
		default:           method = "info";     break;
	}
	PyObject_CallMethod(logging, method, "O", py_msg);

	Py_DECREF(py_msg);
	PyGILState_Release(gstate);
}

// Entry point for the module
PyMODINIT_FUNC PyInit_phazor(void) {
	return PyModule_Create(&phazor_module);
}

#define BUFF_SIZE 240000  // Decoded data buffer size
#define BUFF_SAFE 100000  // Ensure there is this much space free in the buffer

#define VIS_SIDE_MAX 10000
float vis_side_buffer[VIS_SIDE_MAX];
int vis_side_fill = 0;

double t_start, t_end;

bool out_thread_running = false;
bool called_to_stop_device = false;
bool device_stopped = false;
bool signaled_device_unavailable = false;
bool pulse_connected = false;
static volatile bool pw_need_restart = false;
static volatile bool pw_running = false;

float fadefl[BUFF_SIZE];
float fadefr[BUFF_SIZE];

int16_t temp16l[BUFF_SIZE];
int16_t temp16r[BUFF_SIZE];

float re_in[BUFF_SIZE * 2];
float re_out[BUFF_SIZE * 2];

int fade_fill = 0;
bool fade_lockout = false;
float fade_mini = 0.0;
int fade_position = 0;
int fade_2_flag = 0;

pthread_mutex_t buffer_mutex;
pthread_mutex_t fade_mutex;

//pthread_mutex_t pulse_mutex;

float out_buff[2048 * 2];

//#ifdef AO
//	char out_buffc[2048 * 4];
//	int32_t temp32 = 0;
//#endif

int position_count = 0;
int current_length_count = 0;

int sample_rate_out = 44100;
int sample_rate_src = 0;
int src_channels = 2;

int current_sample_rate = 0;
int want_sample_rate = 0;
int sample_change_byte = 0;

bool reset_set = false;
int reset_set_value = 0;
int reset_set_byte = 0;

int rg_byte = 0;
float rg_value_want = 0.0;


char load_target_file[4096]; // 4069 bytes for max linux filepath
char loaded_target_file[4096] = ""; // 4069 bytes for max linux filepath

// Marks whether the (pending/loaded) target is a network URL that should be
// streamed through the byte_stream buffer rather than handed to FFmpeg (radio)
int load_target_net_pending = 0;
int load_target_net = 0;
int loaded_target_net = 0;

unsigned int load_target_seek = 0;
unsigned int next_ready = 0;
unsigned int seek_request_ms = 0;

int subtrack = 0;

float volume_want = 1.0;
float volume_on = 1.0;
float volume_ramp_speed = 750;  // ms for 1 to 0

/* int active_latency = 0; */

int codec = 0;
int error = 0;

float peak_l = 0.;
float peak_roll_l = 0.;
float peak_r = 0.;
float peak_roll_r = 0.;

float gate = 1.0;  // Used for ramping

int config_fast_seek = 0;
int config_dev_buffer = 80;
int config_fade_jump = 1;
char config_output_sink[256]; // 256 just a conservative guess
int config_fade_duration = 700;
int config_resample_quality = 2;
int config_resample = 1;
int config_always_ffmpeg = 0;
int config_volume_power = 2;
int config_feed_samplerate = 48000;
int config_min_buffer = 30000;
int config_stream_buffer_mb = 50;  // In-memory file/stream buffer size in MB

#define EQ_BAND_COUNT 10
#define EQ_AUTO_HEADROOM_MARGIN_DB 1.0f
#define LIMITER_THRESHOLD 0.89125093813f // -1 dBFS
#define LIMITER_ATTACK_MS 1.5f
#define LIMITER_RELEASE_MS 120.0f

typedef struct {
	float b0;
	float b1;
	float b2;
	float a1;
	float a2;
	float z1_l;
	float z2_l;
	float z1_r;
	float z2_r;
} eq_biquad_t;

static const float eq_band_freqs[EQ_BAND_COUNT] = {
	31.25f, 62.5f, 125.0f, 250.0f, 500.0f, 1000.0f, 2000.0f, 4000.0f, 8000.0f, 16000.0f
};
eq_biquad_t eq_bands[EQ_BAND_COUNT];
float eq_band_gain_db[EQ_BAND_COUNT] = {0};
int eq_enabled = 0;
int eq_active = 0;
int eq_coeff_sample_rate = 0;
bool eq_dirty = true;
float eq_headroom_db = 0.0f;
float eq_headroom_gain = 1.0f;
float limiter_gain = 1.0f;
float limiter_attack_coeff = 0.0f;
float limiter_release_coeff = 0.0f;
int limiter_coeff_sample_rate = 0;

unsigned int test1 = 0;

enum status {
	PLAYING,
	PAUSED,
	STOPPED,
	RAMP_DOWN,
	ENDING,
};

enum command_status {
	NONE,
	START,
	LOAD, // used internally only
	SEEK,
	STOP,
	PAUSE,
	RESUME,
	EXIT,
};

enum decoder_types {
	UNKNOWN,
	FLAC,
	MPG,
	VORBIS,
	OPUS,
	FFMPEG,
	WAVE,
	MPT,
	FEED,
	WAVPACK,
	GME,
};

enum result_status_enum {
	WAITING,
	SUCCESS,
	FAILURE
};

int result_status = WAITING;
int mode = STOPPED;
int command = NONE;

int decoder_allocated = 0;
int buffering = 0;

int flac_got_rate = 0;

#ifdef MINI
	ma_context_config c_config;
	ma_device_config config;
	ma_device device;
#endif


#ifdef PIPE
	pthread_t pw_thread;
	pthread_mutex_t pipe_devices_mutex;
	struct pw_main_loop *loop;
	struct pw_context *context;
	struct pw_core *core;
	struct pw_registry *registry;
	struct spa_hook registry_listener;
	struct spa_hook core_listener;
	struct pw_stream *global_stream;
	int enum_done = 0;
	int pipe_set_samplerate = 48000;
	#define MAX_DEVICES 64
	#define POD_BUFFER_SIZE 2048
	struct device_info {
		uint32_t id;
		char name[256];
		char description[256];
	};
	struct pipe_devices_struct {
		struct device_info devices[MAX_DEVICES];
		int device_count;
	};

	struct pipe_devices_struct pipe_devices = {0};

	static void registry_event_remove_global(void *data, uint32_t id) {
		bool removed_active_sink = false;
		uint32_t stream_node_id = PW_ID_ANY;

		/* Determine the node ID currently used by the stream */
		if (global_stream) {
			stream_node_id = pw_stream_get_node_id(global_stream);
		}

		pthread_mutex_lock(&pipe_devices_mutex);
		for (size_t i = 0; i < pipe_devices.device_count; i++) {
			if (pipe_devices.devices[i].id == id) { // Assuming each device has a unique ID
				/* Check if THIS is the active sink */
				log_msg(LOG_INFO, "Removed device with ID: %u (%s)", id, pipe_devices.devices[i].description);
				if (id == stream_node_id) {
					log_msg(LOG_WARNING, "Active sink removed!");
					removed_active_sink = true;
				}
				// Shift remaining devices to fill the gap
				for (size_t j = i; j < pipe_devices.device_count - 1; j++) {
					pipe_devices.devices[j] = pipe_devices.devices[j + 1];
				}
				pipe_devices.device_count--;
				break;
			}
		}
		pthread_mutex_unlock(&pipe_devices_mutex);

		/* IMPORTANT: handle stream loss OUTSIDE the mutex */
		if (removed_active_sink && global_stream) {
			log_msg(LOG_ERROR, "Active sink removed — disconnecting PipeWire stream");

			pw_stream_disconnect(global_stream);

			/* Mark output as dead so start_out() will reconnect */
			pulse_connected = false;
		}
	}

	static void registry_event_global(
		void *data, uint32_t id,
		uint32_t permissions, const char *type, uint32_t version,
		const struct spa_dict *props)
	{

		if (props == NULL || type == NULL || !spa_streq(type, PW_TYPE_INTERFACE_Node))
			return;


		//log_msg(LOG_INFO, "object: id:%u type:%s/%d", id, type, version);
		const char *media_class;

		media_class = spa_dict_lookup(props, PW_KEY_MEDIA_CLASS);
		if (media_class == NULL)
			return;

		if (spa_streq(media_class, "Audio/Sink")) {

			pthread_mutex_lock(&pipe_devices_mutex);
			if (pipe_devices.device_count >= MAX_DEVICES) {
				log_msg(LOG_ERROR, "Error: Max devices");
				pthread_mutex_unlock(&pipe_devices_mutex);
				return;
			}
			const char *name = spa_dict_lookup(props, PW_KEY_NODE_NAME);
			const char *description = spa_dict_lookup(props, PW_KEY_NODE_DESCRIPTION);
			if (!name || !description) {
				log_msg(LOG_ERROR, "Error: Missing name or description for device");
				pthread_mutex_unlock(&pipe_devices_mutex);
				return;
			}

			// Check if already added
			for (size_t i = 0; i < pipe_devices.device_count; i++) {
				if (pipe_devices.devices[i].id == id) {
					pthread_mutex_unlock(&pipe_devices_mutex);
					return;
					}
				}
			pipe_devices.devices[pipe_devices.device_count].id = id;
			snprintf(pipe_devices.devices[pipe_devices.device_count].name, sizeof(pipe_devices.devices[pipe_devices.device_count].name), "%s", name);
			snprintf(pipe_devices.devices[pipe_devices.device_count].description, sizeof(pipe_devices.devices[pipe_devices.device_count].description), "%s", description);
			pipe_devices.device_count++;
			log_msg(LOG_INFO, "Found audio sink: %s (%s)", name, description);
			pthread_mutex_unlock(&pipe_devices_mutex);

		}
	}

	static const struct pw_registry_events registry_events = {
		PW_VERSION_REGISTRY_EVENTS,
		.global = registry_event_global,
		.global_remove = registry_event_remove_global,
	};

	static void on_core_done(void *userdata, uint32_t id, int seq) {
		if (id == PW_ID_CORE) {
			enum_done = 1;
		}
	}

	static void on_core_error(void *data, uint32_t id, int seq, int res, const char *message) {
		log_msg(LOG_ERROR,
			"PipeWire core error: id=%u res=%d (%s) msg=%s",
			id, res, spa_strerror(res), message ? message : "(null)");
		// Mark disconnected so the app can attempt reconnect
		pulse_connected = false;

		if (res == -EPIPE || res == -ECONNRESET) {
			pw_need_restart = true;
			if (loop) pw_main_loop_quit(loop);
		}
	}

	static const struct pw_core_events core_events = {
		PW_VERSION_CORE_EVENTS,
		.done = on_core_done,
		.error = on_core_error,
	};
#endif

float bfl[BUFF_SIZE];
float bfr[BUFF_SIZE];
int low = 0;
int high = 0;
int high_mark = BUFF_SIZE - BUFF_SAFE;
int watermark = BUFF_SIZE - BUFF_SAFE;

int get_buff_fill() {
	if (low <= high) return high - low;
	return (watermark - low) + high;
}

void buff_cycle() {
	if (high > high_mark) {
		watermark = high;
		high = 0;
	}
	if (low >= watermark) low = 0;
}

void buff_reset() {
	low = 0;
	high = 0;
	watermark = high_mark;
}

// Cross-compatibility -------------------------------------------

#ifdef WIN64
	static wchar_t *loaded_target_wpath = NULL;
	#include <wchar.h>
	static wchar_t *utf8_to_wide_path(const char *utf8) {
		if (!utf8) return NULL;

		// 1) UTF-8 -> wide
		int wlen = MultiByteToWideChar(CP_UTF8, 0, utf8, -1, NULL, 0);
		if (wlen <= 0) return NULL;

		wchar_t *wtmp = (wchar_t*)malloc(sizeof(wchar_t) * (size_t)wlen);
		if (!wtmp) return NULL;

		if (!MultiByteToWideChar(CP_UTF8, 0, utf8, -1, wtmp, wlen)) {
			free(wtmp);
			return NULL;
		}

		// 2) Make absolute (required for \\?\)
		DWORD abs_len = GetFullPathNameW(wtmp, 0, NULL, NULL);
		if (abs_len == 0) {
			free(wtmp);
			return NULL;
		}

		wchar_t *abs_path = (wchar_t*)malloc(sizeof(wchar_t) * (size_t)abs_len);
		if (!abs_path) {
			free(wtmp);
			return NULL;
		}

		DWORD abs_len2 = GetFullPathNameW(wtmp, abs_len, abs_path, NULL);
		free(wtmp);
		if (abs_len2 == 0 || abs_len2 >= abs_len) {
			free(abs_path);
			return NULL;
		}

		// Already prefixed?
		if (wcsncmp(abs_path, L"\\\\?\\", 4) == 0) {
			return abs_path;
		}

		// 3) Add long-path prefix only if needed
		size_t abs_chars = wcslen(abs_path);
		if (abs_chars < MAX_PATH) {
			return abs_path;
		}

		// UNC path: \\server\share\...
		if (wcsncmp(abs_path, L"\\\\", 2) == 0) {
			// Build: \\?\UNC\ + (abs_path without leading \\)
			const wchar_t *tail = abs_path + 2;
			size_t tail_len = wcslen(tail);
			wchar_t *out = (wchar_t*)malloc(sizeof(wchar_t) * (tail_len + 8 + 1)); // "\\?\UNC\" = 8 chars
			if (!out) {
				free(abs_path);
				return NULL;
			}
			wcscpy(out, L"\\\\?\\UNC\\");
			wcscat(out, tail);
			free(abs_path);
			return out;
		}

		// Drive path: C:\...
		wchar_t *out = (wchar_t*)malloc(sizeof(wchar_t) * (abs_chars + 4 + 1));
		if (!out) {
			free(abs_path);
			return NULL;
		}
		wcscpy(out, L"\\\\?\\");
		wcscat(out, abs_path);
		free(abs_path);
		return out;
	}
#endif

FILE *uni_fopen(char *ff) {
	#ifdef WIN64
		wchar_t *wpath = utf8_to_wide_path(ff);
		if (!wpath) return NULL;

		FILE *f = _wfopen(wpath, L"rb");
		free(wpath);
		return f;
	#else
		return fopen(ff, "rb");
	#endif
}

#ifdef WIN64
static int uni_stat(const char *path, struct stat *st) {
	if (!loaded_target_wpath) return -1;

	struct _stat64 wst;
	int r = _wstat64(loaded_target_wpath, &wst);

	if (r != 0) return r;

	st->st_size  = (off_t)wst.st_size;
	st->st_mtime = wst.st_mtime;
	st->st_atime = wst.st_atime;
	st->st_ctime = wst.st_ctime;
	st->st_mode  = wst.st_mode;

	return 0;
}
#else
	#define uni_stat stat
#endif


// Byte stream ----------------------------------------------------
// A single in-memory window over the file being played. Data is produced
// either by a local file reader thread or by the Python network feeder
// (net_* exports), and consumed by the decoders through small fread-like
// callbacks. Seeking outside the buffered window redirects the producer,
// which for network sources becomes an HTTP range request.

#define BS_CHUNK 262144                  // local file read chunk
#define BS_DECODE_AHEAD 262144           // bytes buffered ahead before (re)starting a network decode
#define BS_DECODE_CONTINUE 32768         // bytes ahead needed to keep decoding once started
#define BS_FORWARD_GAP (1024 * 1024)     // forward seeks within this of the tail wait rather than restart
#define BS_STALL_TIMEOUT_MS 30000        // give up if no data arrives for this long

typedef struct {
	unsigned char *buf;
	int64_t capacity;
	int64_t win_start;      // absolute file offset of the first byte in the window
	int64_t head;           // physical index in buf of win_start
	int64_t filled;         // valid bytes in the window
	int64_t read_pos;       // absolute file offset of the reader
	int64_t file_size;      // total size, -1 if unknown
	int64_t want_offset;    // producer restart offset
	bool want_restart;      // producer must restart at want_offset
	bool eof;               // producer has delivered up to the end of the file
	bool error;             // producer failed fatally
	bool active;
	bool net;               // true: fed by Python network feeder, false: local thread
	bool abort;             // cancel all waits and shut the stream down
	bool seek_ok;           // producer can supply arbitrary offsets (HTTP range support)
	int generation;
	FILE *file;             // local source
	bool thread_running;
	pthread_t thread;
	pthread_mutex_t mut;
	pthread_cond_t cond;
} byte_stream;

static byte_stream bs = {
	.file_size = -1,
	.mut = PTHREAD_MUTEX_INITIALIZER,
	.cond = PTHREAD_COND_INITIALIZER,
};

static char bs_net_url[4096];
static char bs_net_url_out[4096];
static unsigned char bs_local_chunk[BS_CHUNK];

static int64_t bs_keep_behind() {
	// Bytes kept behind the read position so small backward seeks stay in memory
	int64_t k = bs.capacity / 8;
	if (k > 1024 * 1024) k = 1024 * 1024;
	return k;
}

static void bs_window_reset_locked(int64_t offset) {
	bs.win_start = offset;
	bs.head = 0;
	bs.filled = 0;
	bs.eof = false;
}

static void bs_discard_front_locked(int64_t n) {
	if (n > bs.filled) n = bs.filled;
	bs.head = (bs.head + n) % bs.capacity;
	bs.win_start += n;
	bs.filled -= n;
}

static int64_t bs_make_space_locked() {
	// Free space the producer may append into, sliding the window forward
	// over data the reader has already consumed when full
	int64_t free_space = bs.capacity - bs.filled;
	if (free_space > 0) return free_space;
	int64_t discard = (bs.read_pos - bs_keep_behind()) - bs.win_start;
	if (discard > 0) {
		bs_discard_front_locked(discard);
		free_space = bs.capacity - bs.filled;
	}
	return free_space;
}

static void bs_append_locked(const unsigned char *data, int64_t n) {
	int64_t tail = (bs.head + bs.filled) % bs.capacity;
	int64_t first = bs.capacity - tail;
	if (first > n) first = n;
	memcpy(bs.buf + tail, data, (size_t) first);
	if (n > first) memcpy(bs.buf, data + first, (size_t) (n - first));
	bs.filled += n;
}

static void bs_copy_out_locked(unsigned char *dst, int64_t offset, int64_t n) {
	int64_t pos = (bs.head + (offset - bs.win_start)) % bs.capacity;
	int64_t first = bs.capacity - pos;
	if (first > n) first = n;
	memcpy(dst, bs.buf + pos, (size_t) first);
	if (n > first) memcpy(dst + first, bs.buf, (size_t) (n - first));
}

static void bs_request_restart_locked(int64_t offset) {
	bs.want_restart = true;
	bs.want_offset = offset;
	bs.eof = false;
	pthread_cond_broadcast(&bs.cond);
}

static void bs_wait_locked(int ms) {
	struct timespec ts;
	#ifdef WIN64
		// timespec_get is C11 and available on mingw
		timespec_get(&ts, TIME_UTC);
	#else
		clock_gettime(CLOCK_REALTIME, &ts);
	#endif
	ts.tv_sec += ms / 1000;
	ts.tv_nsec += (long) (ms % 1000) * 1000000L;
	if (ts.tv_nsec >= 1000000000L) {
		ts.tv_sec += 1;
		ts.tv_nsec -= 1000000000L;
	}
	pthread_cond_timedwait(&bs.cond, &bs.mut, &ts);
}

static void *bs_local_thread(void *arg) {
	pthread_mutex_lock(&bs.mut);
	while (bs.active && !bs.abort) {
		if (bs.want_restart) {
			int64_t target = bs.want_offset;
			bs_window_reset_locked(target);
			bs.want_restart = false;
			fseek(bs.file, (long) target, SEEK_SET);
			clearerr(bs.file);
		}
		if (bs.eof) {
			// At end of file; poll for growth, the file may be a cache
			// file that is still downloading
			bs_wait_locked(1000);
			if (!bs.active || bs.abort || bs.want_restart) continue;
			struct stat fst;
			if (bs.file != NULL && fstat(fileno(bs.file), &fst) == 0
					&& (int64_t) fst.st_size > bs.file_size) {
				bs.file_size = (int64_t) fst.st_size;
				bs.eof = false;
				clearerr(bs.file);
				pthread_cond_broadcast(&bs.cond);
			}
			continue;
		}
		int64_t free_space = bs_make_space_locked();
		if (free_space <= 0) {
			pthread_cond_wait(&bs.cond, &bs.mut);
			continue;
		}
		int64_t off = bs.win_start + bs.filled;
		int64_t n = free_space < BS_CHUNK ? free_space : BS_CHUNK;
		pthread_mutex_unlock(&bs.mut);

		size_t got = fread(bs_local_chunk, 1, (size_t) n, bs.file);

		pthread_mutex_lock(&bs.mut);
		if (!bs.active || bs.abort) break;
		if (bs.want_restart || bs.win_start + bs.filled != off) {
			// A restart raced with the read, drop this chunk
			clearerr(bs.file);
			continue;
		}
		if (got > 0) {
			bs_append_locked(bs_local_chunk, (int64_t) got);
			if (bs.file_size >= 0 && bs.win_start + bs.filled >= bs.file_size) bs.eof = true;
			pthread_cond_broadcast(&bs.cond);
		} else {
			bs.eof = true;
			clearerr(bs.file);
			pthread_cond_broadcast(&bs.cond);
		}
	}
	pthread_cond_broadcast(&bs.cond);
	pthread_mutex_unlock(&bs.mut);
	return arg;
}

static int bs_ensure_buffer() {
	int64_t want = (int64_t) config_stream_buffer_mb * 1024 * 1024;
	if (want < 4 * 1024 * 1024) want = 4 * 1024 * 1024;
	if (bs.buf != NULL && bs.capacity == want) return 0;
	free(bs.buf);
	bs.buf = malloc((size_t) want);
	if (bs.buf == NULL) {
		bs.capacity = 0;
		log_msg(LOG_ERROR, "pa: Failed to allocate stream buffer (%d MB)", config_stream_buffer_mb);
		return 1;
	}
	bs.capacity = want;
	return 0;
}

// Cancel any blocking stream waits. Safe to call from any thread.
static void bs_cancel() {
	pthread_mutex_lock(&bs.mut);
	if (bs.active) {
		bs.abort = true;
		pthread_cond_broadcast(&bs.cond);
	}
	pthread_mutex_unlock(&bs.mut);
}

// Close the stream and join the local producer. Main loop thread only.
static void bs_close() {
	pthread_mutex_lock(&bs.mut);
	bool was_active = bs.active || bs.thread_running;
	bs.active = false;
	bs.abort = true;
	pthread_cond_broadcast(&bs.cond);
	bool join = bs.thread_running;
	bs.thread_running = false;
	pthread_mutex_unlock(&bs.mut);
	if (!was_active) return;
	if (join) pthread_join(bs.thread, NULL);
	pthread_mutex_lock(&bs.mut);
	if (bs.file != NULL) {
		fclose(bs.file);
		bs.file = NULL;
	}
	pthread_mutex_unlock(&bs.mut);
}

static void bs_reset_state_locked() {
	bs.read_pos = 0;
	bs.win_start = 0;
	bs.head = 0;
	bs.filled = 0;
	bs.eof = false;
	bs.error = false;
	bs.abort = false;
	bs.want_restart = false;
	bs.want_offset = 0;
	bs.seek_ok = true;
	bs.generation++;
}

static int bs_open_local(char *path) {
	bs_close();
	if (bs_ensure_buffer() != 0) return 1;
	FILE *f = uni_fopen(path);
	if (f == NULL) {
		log_msg(LOG_ERROR, "pa: Error opening file: '%s' (%s)", path, strerror(errno));
		return 1;
	}
	int64_t size = -1;
	struct stat fst;
	if (fstat(fileno(f), &fst) == 0) size = (int64_t) fst.st_size;
	pthread_mutex_lock(&bs.mut);
	bs.file = f;
	bs.net = false;
	bs.file_size = size;
	bs_reset_state_locked();
	bs.active = true;
	pthread_mutex_unlock(&bs.mut);
	if (pthread_create(&bs.thread, NULL, bs_local_thread, NULL) != 0) {
		log_msg(LOG_ERROR, "pa: Failed to create stream reader thread");
		pthread_mutex_lock(&bs.mut);
		bs.active = false;
		bs.file = NULL;
		pthread_mutex_unlock(&bs.mut);
		fclose(f);
		return 1;
	}
	bs.thread_running = true;
	return 0;
}

static int bs_open_net(char *url) {
	bs_close();
	if (bs_ensure_buffer() != 0) return 1;
	pthread_mutex_lock(&bs.mut);
	snprintf(bs_net_url, sizeof(bs_net_url), "%s", url);
	bs.file = NULL;
	bs.net = true;
	bs.file_size = -1;
	bs_reset_state_locked();
	bs.active = true;
	pthread_mutex_unlock(&bs.mut);
	return 0;
}

// Blocking read at the current read position. Returns bytes read,
// 0 on end of stream, -1 on abort/error.
static int bs_read(void *dst, int n) {
	if (n <= 0) return 0;
	int64_t got = -1;
	int waited_ms = 0;
	pthread_mutex_lock(&bs.mut);
	while (true) {
		if (!bs.active || bs.abort || bs.error) {
			got = -1;
			break;
		}
		if (bs.file_size >= 0 && bs.read_pos >= bs.file_size) {
			got = 0;
			break;
		}
		int64_t end = bs.win_start + bs.filled;
		if (bs.read_pos >= bs.win_start && bs.read_pos < end) {
			int64_t avail = end - bs.read_pos;
			got = avail < n ? avail : n;
			bs_copy_out_locked(dst, bs.read_pos, got);
			bs.read_pos += got;
			pthread_cond_broadcast(&bs.cond);
			break;
		}
		if (bs.eof && !bs.want_restart && bs.read_pos >= end) {
			got = 0;
			break;
		}
		// Out of window, redirect the producer
		if ((bs.read_pos < bs.win_start || bs.read_pos > end + BS_FORWARD_GAP)
				&& (!bs.want_restart || bs.want_offset != bs.read_pos)) {
			bs_request_restart_locked(bs.read_pos);
		}
		bs_wait_locked(100);
		waited_ms += 100;
		if (waited_ms >= BS_STALL_TIMEOUT_MS) {
			log_msg(LOG_ERROR, "pa: Stream stalled, giving up");
			bs.error = true;
			got = -1;
			break;
		}
	}
	pthread_mutex_unlock(&bs.mut);
	return (int) got;
}

static int bs_read_exact(void *dst, int n) {
	int total = 0;
	while (total < n) {
		int r = bs_read((unsigned char *) dst + total, n - total);
		if (r <= 0) return total;
		total += r;
	}
	return total;
}

static int bs_seek_abs(int64_t offset) {
	if (offset < 0) return -1;
	pthread_mutex_lock(&bs.mut);
	if (!bs.active) {
		pthread_mutex_unlock(&bs.mut);
		return -1;
	}
	bs.read_pos = offset;
	int64_t end = bs.win_start + bs.filled;
	if (offset < bs.win_start || offset > end + BS_FORWARD_GAP || (bs.eof && offset > end)) {
		// No data needed when seeking to/past a known end of file
		if (!(bs.file_size >= 0 && offset >= bs.file_size)) {
			bs_request_restart_locked(offset);
		}
	}
	pthread_cond_broadcast(&bs.cond);
	pthread_mutex_unlock(&bs.mut);
	return 0;
}

static int64_t bs_tell() {
	return bs.read_pos;
}

static int64_t bs_length() {
	return bs.file_size;
}

static bool bs_seekable() {
	return bs.active && bs.file_size >= 0 && bs.seek_ok;
}

static bool bs_at_eof() {
	pthread_mutex_lock(&bs.mut);
	bool r = (bs.file_size >= 0 && bs.read_pos >= bs.file_size)
		|| (bs.eof && !bs.want_restart && bs.read_pos >= bs.win_start + bs.filled);
	pthread_mutex_unlock(&bs.mut);
	return r;
}

// Whether a network decode can proceed without risking a long block in
// the decoder read callbacks. Keeps the main loop responsive to commands
// while the network buffers. Uses hysteresis: after an open, seek or
// underrun a larger amount must accumulate before decoding (re)starts,
// then decoding continues as long as a small headroom remains.
static int64_t bs_decode_need = BS_DECODE_AHEAD;

static bool bs_decode_ready() {
	if (!bs.active || !bs.net) return true;
	pthread_mutex_lock(&bs.mut);
	bool ready = bs.abort || bs.error;
	int64_t end = bs.win_start + bs.filled;
	int64_t avail = 0;
	if (bs.read_pos >= bs.win_start && bs.read_pos < end) avail = end - bs.read_pos;
	if (avail < BS_DECODE_CONTINUE && !bs.eof) bs_decode_need = BS_DECODE_AHEAD;  // underrun, re-arm
	if (avail >= bs_decode_need) ready = true;
	if (bs.eof && !bs.want_restart && bs.read_pos >= bs.win_start) ready = true;
	if (bs.file_size >= 0 && bs.read_pos >= bs.file_size) ready = true;
	if (ready) bs_decode_need = BS_DECODE_CONTINUE;
	pthread_mutex_unlock(&bs.mut);
	return ready;
}

// Read the entire stream into memory (for module/GME formats)
static unsigned char *bs_read_all(int64_t *out_size) {
	int64_t cap = bs.file_size >= 0 ? bs.file_size : 1024 * 1024;
	if (cap <= 0) cap = 1024 * 1024;
	if (cap > 512 * 1024 * 1024) return NULL;
	unsigned char *data = malloc((size_t) cap);
	if (data == NULL) return NULL;
	int64_t size = 0;
	while (true) {
		if (size == cap) {
			if (cap >= 512 * 1024 * 1024) {
				free(data);
				return NULL;
			}
			cap *= 2;
			unsigned char *n = realloc(data, (size_t) cap);
			if (n == NULL) {
				free(data);
				return NULL;
			}
			data = n;
		}
		int64_t want = cap - size;
		if (want > BS_CHUNK) want = BS_CHUNK;
		int r = bs_read(data + size, (int) want);
		if (r < 0) {
			free(data);
			return NULL;
		}
		if (r == 0) break;
		size += r;
	}
	*out_size = size;
	return data;
}

// Decoder I/O callbacks over the byte stream ---------------------

static int64_t bs_whence_target(int64_t offset, int whence) {
	switch (whence) {
		case SEEK_SET: return offset;
		case SEEK_CUR: return bs.read_pos + offset;
		case SEEK_END:
			if (bs.file_size < 0) return -1;
			return bs.file_size + offset;
	}
	return -1;
}

// opusfile
static int bs_op_read(void *stream, unsigned char *ptr, int nbytes) {
	int r = bs_read(ptr, nbytes);
	return r < 0 ? -1 : r;
}

static int bs_op_seek(void *stream, opus_int64 offset, int whence) {
	int64_t target = bs_whence_target((int64_t) offset, whence);
	if (target < 0) return -1;
	return bs_seek_abs(target) == 0 ? 0 : -1;
}

static opus_int64 bs_op_tell(void *stream) {
	return (opus_int64) bs_tell();
}

static const OpusFileCallbacks bs_op_callbacks = {
	.read = bs_op_read,
	.seek = bs_op_seek,
	.tell = bs_op_tell,
	.close = NULL,
};

static const OpusFileCallbacks bs_op_callbacks_unseekable = {
	.read = bs_op_read,
	.seek = NULL,
	.tell = NULL,
	.close = NULL,
};

// vorbisfile
static size_t bs_ov_read(void *ptr, size_t size, size_t nmemb, void *datasource) {
	if (size == 0) return 0;
	int64_t want = (int64_t) size * (int64_t) nmemb;
	if (want > INT_MAX) want = INT_MAX;
	int r = bs_read(ptr, (int) want);
	if (r <= 0) return 0;
	return (size_t) r / size;
}

static int bs_ov_seek(void *datasource, ogg_int64_t offset, int whence) {
	if (!bs_seekable()) return -1;
	int64_t target = bs_whence_target((int64_t) offset, whence);
	if (target < 0) return -1;
	return bs_seek_abs(target) == 0 ? 0 : -1;
}

static long bs_ov_tell(void *datasource) {
	return (long) bs_tell();
}

static const ov_callbacks bs_ov_cb = {
	.read_func = bs_ov_read,
	.seek_func = bs_ov_seek,
	.close_func = NULL,
	.tell_func = bs_ov_tell,
};

static const ov_callbacks bs_ov_cb_unseekable = {
	.read_func = bs_ov_read,
	.seek_func = NULL,
	.close_func = NULL,
	.tell_func = NULL,
};

// FLAC
static FLAC__StreamDecoderReadStatus bs_flac_read(
		const FLAC__StreamDecoder *decoder, FLAC__byte buffer[], size_t *bytes, void *client_data) {
	if (*bytes == 0) return FLAC__STREAM_DECODER_READ_STATUS_ABORT;
	int64_t want = (int64_t) *bytes;
	if (want > INT_MAX) want = INT_MAX;
	int r = bs_read(buffer, (int) want);
	if (r < 0) {
		*bytes = 0;
		return FLAC__STREAM_DECODER_READ_STATUS_ABORT;
	}
	*bytes = (size_t) r;
	if (r == 0) return FLAC__STREAM_DECODER_READ_STATUS_END_OF_STREAM;
	return FLAC__STREAM_DECODER_READ_STATUS_CONTINUE;
}

static FLAC__StreamDecoderSeekStatus bs_flac_seek(
		const FLAC__StreamDecoder *decoder, FLAC__uint64 absolute_byte_offset, void *client_data) {
	if (!bs_seekable()) return FLAC__STREAM_DECODER_SEEK_STATUS_UNSUPPORTED;
	if (bs_seek_abs((int64_t) absolute_byte_offset) != 0) return FLAC__STREAM_DECODER_SEEK_STATUS_ERROR;
	return FLAC__STREAM_DECODER_SEEK_STATUS_OK;
}

static FLAC__StreamDecoderTellStatus bs_flac_tell(
		const FLAC__StreamDecoder *decoder, FLAC__uint64 *absolute_byte_offset, void *client_data) {
	*absolute_byte_offset = (FLAC__uint64) bs_tell();
	return FLAC__STREAM_DECODER_TELL_STATUS_OK;
}

static FLAC__StreamDecoderLengthStatus bs_flac_length(
		const FLAC__StreamDecoder *decoder, FLAC__uint64 *stream_length, void *client_data) {
	int64_t l = bs_length();
	if (l < 0) return FLAC__STREAM_DECODER_LENGTH_STATUS_UNSUPPORTED;
	*stream_length = (FLAC__uint64) l;
	return FLAC__STREAM_DECODER_LENGTH_STATUS_OK;
}

static FLAC__bool bs_flac_eof(const FLAC__StreamDecoder *decoder, void *client_data) {
	return bs_at_eof();
}

// mpg123
static mpg123_ssize_t bs_mpg_read(void *handle, void *buffer, size_t nbytes) {
	int64_t want = (int64_t) nbytes;
	if (want > INT_MAX) want = INT_MAX;
	return (mpg123_ssize_t) bs_read(buffer, (int) want);
}

static off_t bs_mpg_lseek(void *handle, off_t offset, int whence) {
	// Refusing seeks makes mpg123 fall back to its unseekable stream mode
	if (!bs_seekable()) return (off_t) -1;
	int64_t target = bs_whence_target((int64_t) offset, whence);
	if (target < 0) return (off_t) -1;
	if (bs_seek_abs(target) != 0) return (off_t) -1;
	return (off_t) target;
}

// WavPack
static int32_t bs_wv_read_bytes(void *id, void *data, int32_t bcount) {
	int r = bs_read_exact(data, bcount);
	return r < 0 ? 0 : (int32_t) r;
}

static int64_t bs_wv_get_pos(void *id) {
	return bs_tell();
}

static int bs_wv_set_pos_abs(void *id, int64_t pos) {
	return bs_seek_abs(pos) == 0 ? 0 : -1;
}

static int bs_wv_set_pos_rel(void *id, int64_t delta, int mode) {
	int64_t target = bs_whence_target(delta, mode);
	if (target < 0) return -1;
	return bs_seek_abs(target) == 0 ? 0 : -1;
}

static int bs_wv_push_back_byte(void *id, int c) {
	if (bs_tell() <= 0) return EOF;
	if (bs_seek_abs(bs_tell() - 1) != 0) return EOF;
	return c;
}

static int64_t bs_wv_get_length(void *id) {
	int64_t l = bs_length();
	return l < 0 ? 0 : l;
}

static int bs_wv_can_seek(void *id) {
	return bs_seekable() ? 1 : 0;
}

static WavpackStreamReader64 bs_wv_reader = {
	.read_bytes = bs_wv_read_bytes,
	.write_bytes = NULL,
	.get_pos = bs_wv_get_pos,
	.set_pos_abs = bs_wv_set_pos_abs,
	.set_pos_rel = bs_wv_set_pos_rel,
	.push_back_byte = bs_wv_push_back_byte,
	.get_length = bs_wv_get_length,
	.can_seek = bs_wv_can_seek,
	.truncate_here = NULL,
	.close = NULL,
};


// Misc ----------------------------------------------------------

float ramp_step(int sample_rate, int milliseconds) {
	return 1.0 / sample_rate / (milliseconds / 1000.0);
}

void fade_fx() {
	//pthread_mutex_lock(&fade_mutex);

	if (rg_value_want != 0.0 && rg_value_want != 1.0) {
		bfr[high] *= rg_value_want;
		bfl[high] *= rg_value_want;
		if (bfl[high] > 1) bfl[high] = 1;
		if (bfl[high] < -1) bfl[high] = -1;
		if (bfr[high] > 1) bfr[high] = 1;
		if (bfr[high] < -1) bfr[high] = -1;
	}

	if (fade_mini < 1.0) {
		fade_mini += ramp_step(sample_rate_out, 10); // 10ms ramp
		bfr[high] *= fade_mini;
		bfl[high] *= fade_mini;
		if (fade_mini > 1.0) fade_mini = 1.0;
	}
	if (fade_fill > 0) {
		if (fade_fill == fade_position) {
			fade_fill = 0;
			fade_position = 0;
		} else {
			fade_lockout = true;
			float cross = fade_position / (float) fade_fill;
			float cross_i = 1.0 - cross;


			bfl[high] *= cross;
			bfl[high] += fadefl[fade_position] * cross_i;

			bfr[high] *= cross;
			bfr[high] += fadefr[fade_position] * cross_i;
			fade_position++;

		}
	}
	//pthread_mutex_unlock(&fade_mutex);
}

off_t load_file_size = 0;
int samples_decoded = 0;

// Secret Rabbit Code --------------------------------------------------

SRC_DATA src_data;
SRC_STATE *src;

// wavpack -----------------------------------

WavpackContext *wpc;
int wp_bit = 0;
int wp_float = 0;

// kiss fft -----------------------------------------------------------

kiss_fft_scalar * rbuf;
kiss_fft_cpx * cbuf;
kiss_fftr_cfg ffta;

// Vorbis related --------------------------------------------------------

OggVorbis_File vf;
vorbis_info vi;

// Opus related ----------------------------------------

OggOpusFile *opus_dec;
int16_t opus_buffer[2048 * 2];

// MP3 related ------------------------------------------------

mpg123_handle *mh;
char parse_buffer[2048 * 2];

// openMPT related ---------------

FILE* mod_file = 0;
openmpt_module* mod = 0;


// GME related -------------------

Music_Emu* emu;

// FFmpeg related -----------------------------------------------------

FILE *ffm;
char exe_string[4096];
char ffm_buffer[2048];

int (*ff_start)(char*, int, int);
int (*ff_read)(char*, int);
void (*ff_close)();
void (*on_device_unavailable)();

void start_ffmpeg(char uri[], int start_ms) {
	int status = 0;
	if (ff_start != NULL) status = ff_start(uri, start_ms, sample_rate_out);
	else {
		log_msg(LOG_ERROR, "pa: FFmpeg callback is NULL");
		return;
	}

	if (status != 0) {
		log_msg(LOG_ERROR, "pa: Error starting FFmpeg");
		return;
	}

	decoder_allocated = 1;
	sample_rate_src = sample_rate_out;

}

void stop_ffmpeg() {
	if (ff_close != NULL) ff_close();
}


void resample_to_buffer(int in_frames) {

	src_data.data_in = re_in;
	src_data.data_out = re_out;
	src_data.input_frames = in_frames;
	src_data.output_frames = BUFF_SIZE - BUFF_SAFE;
	src_data.src_ratio = (double) sample_rate_out / (double) sample_rate_src;
	src_data.end_of_input = 0;

	src_process(src, &src_data);
	//log_msg(LOG_ERROR, "pa: SRC error code: %d", src_result);
	//log_msg(LOG_ERROR, "pa: SRC output frames: %lu", src_data.output_frames_gen);
	//log_msg(LOG_ERROR, "pa: SRC input frames used: %lu", src_data.input_frames_used);
	int out_frames = src_data.output_frames_gen;

	int i = 0;
	while (i < out_frames) {

		bfl[high] = re_out[i * 2];
		bfr[high] = re_out[(i * 2) + 1];

		fade_fx();

		high += 1;
		i++;
	}
	buff_cycle();

}

// WAV Decoder ----------------------------------------------------------------

FILE *wave_file;
int wave_channels = 2;
int wave_samplerate = 44100;
int wave_depth = 16;
int wave_size = 0;
int wave_start = 0;
int wave_error = 0;
int16_t wave_16 = 0;

int wave_open(char *filename) {
	wave_file = uni_fopen(filename);
	if (wave_file == NULL) {
		log_msg(LOG_ERROR, "pa: Error opening WAVE file: %s", strerror(errno));
		return 1;
	}

	char b[16];
	int i;

	b[15] = '\0';
	fread(b, 4, 1, wave_file);
	//log_msg(LOG_INFO, "pa: mark: %s", b)

	fread(&i, 4, 1, wave_file);
	//log_msg(LOG_INFO, "pa: size: %d", i);
	wave_size = i - 44;

	fread(b, 4, 1, wave_file);
	//log_msg(LOG_INFO, "pa: head: %s", b);
	if (memcmp(b, "WAVE", 4) == 1) {
		log_msg(LOG_ERROR, "pa: Invalid WAVE file");
		fclose(wave_file);
		return 1;
	}

	while (true) {

		// Read data block label
		wave_error = fread(b, 4, 1, wave_file);
		if (wave_error != 1) {
			fclose(wave_file);
			return 1;
		}
		// Read data block length
		wave_error = fread(&i, 4, 1, wave_file);
		if (wave_error != 1) {
			fclose(wave_file);
			return 1;
		}
		// Is audio data?
		if (memcmp(b, "fmt ", 4) == 0) {
			wave_start = ftell(wave_file);
			wave_size = i;
			break;
		}
		// Skip to next block
		fseek(wave_file, i, SEEK_CUR);
	}


	//fread(b, 4, 1, wave_file);
	//log_msg(LOG_INFO, "pa: fmt : %s", b);

	//fread(&i, 4, 1, wave_file);
	//log_msg(LOG_INFO, "pa: abov: %d", i);
	//if (i != 16) {
	//	log_msg(LOG_ERROR, "pa: Unsupported WAVE file");
	//	return 1;
	//}

	fread(&i, 2, 1, wave_file);
	//log_msg(LOG_INFO, "pa: type: %d", i);
	if (i != 1) {
		log_msg(LOG_ERROR, "pa: Unsupported WAVE file");
		fclose(wave_file);
		return 1;
	}

	fread(&i, 2, 1, wave_file);
	//log_msg(LOG_INFO, "pa: chan: %d\n", i);
	if (i != 1 && i != 2) {
		log_msg(LOG_ERROR, "pa: Unsupported WAVE channels");
		fclose(wave_file);
		return 1;
	}
	wave_channels = i;

	fread(&i, 4, 1, wave_file);
	//log_msg(LOG_INFO, "pa: smpl: %d", i);
	wave_samplerate = i;
	sample_rate_src = i;

	fseek(wave_file, 6, SEEK_CUR);

	fread(&i, 2, 1, wave_file);
	//log_msg(LOG_INFO, "pa: bitd: %d", i);
	if (i != 16) {
		log_msg(LOG_ERROR, "pa: Unsupported WAVE depth");
		fclose(wave_file);
		return 1;
	}
	wave_depth = i;
	fseek(wave_file, wave_start + wave_size, SEEK_SET);

	while (true) {
		// Read data block label
		wave_error = fread(b, 4, 1, wave_file);
		if (wave_error != 1) {
			fclose(wave_file);
			return 1;
		}
		// Read data block length
		wave_error = fread(&i, 4, 1, wave_file);
		if (wave_error != 1) {
			fclose(wave_file);
			return 1;
		}
		// Is audio data?
		//log_msg(LOG_INFO, "label %s", b);
		if (memcmp(b, "data", 4) == 0) {
			wave_start = ftell(wave_file);
			wave_size = i;
			break;
		}
		// Skip to next block
		fseek(wave_file, i, SEEK_CUR);
	}

	return 0;
}

int wave_decode(int read_frames) {

	int frames_read = 0;
	bool end = false;
	int i = 0;
	while (i < read_frames) {

		wave_error = fread(&wave_16, 2, 1, wave_file);
		if (wave_error != 1) return 1;
		re_in[i * 2] = wave_16 / 32768.0;

		wave_error = fread(&wave_16, 2, 1, wave_file);
		if (wave_error != 1) return 1;
		re_in[i * 2 + 1] = wave_16 / 32768.0;

		i++;
		frames_read++;
		if ((ftell(wave_file) - wave_start) > wave_size) {
			log_msg(LOG_INFO, "pa: End of WAVE file data");
			end = true;
			break;
		}

	}

	if (sample_rate_src != sample_rate_out) {
		resample_to_buffer(frames_read);
	} else {

		i = 0;
		while (i < frames_read) {

			bfl[high] = re_in[i * 2];
			bfr[high] = re_in[i * 2 + 1];

			fade_fx();

			//buff_filled++;
			high++;
			samples_decoded++;
			i++;
		}
		buff_cycle();
	}
	if (end) return 1;
	return 0;

}

int wave_seek(int frame_position) {
	return fseek(wave_file, (frame_position * 4) + wave_start, SEEK_SET);
}

void wave_close() {
	if (wave_file != NULL) fclose(wave_file);
}

void read_to_buffer_24in32_fs(int32_t src[], int n_samples) {
	// full samples version
	int i = 0;
	int f = 0;

	// Convert int16 to float
	while (f < n_samples) {
		re_in[f * 2] = (src[i]) / 8388608.0;
		if (src_channels == 1) {
			re_in[(f * 2) + 1] = re_in[f * 2];
			i += 1;
		} else {
			re_in[(f * 2) + 1] = (src[i + 1]) / 8388608.0;
			i += 2;
		}

		f++;
	}

	resample_to_buffer(f);
}

void read_to_buffer_32in32_fs(int32_t src[], int n_samples) {
	// full samples version
	int i = 0;
	int f = 0;

	// Convert int32 to float
	while (f < n_samples) {
		re_in[f * 2] = (src[i]) / 2147483648.0;
		if (src_channels == 1) {
			re_in[(f * 2) + 1] = re_in[f * 2];
			i += 1;
		} else {
			re_in[(f * 2) + 1] = (src[i + 1]) / 2147483648.0;
			i += 2;
		}

		f++;
	}

	resample_to_buffer(f);
}

void read_to_buffer_float32_fs(int32_t src[], int n_samples) {
	// full samples version for floating point WavPack
	int i = 0;
	int f = 0;

	// Reinterpret int32 as float (WavPack stores float as int32)
	union {
		int32_t i;
		float f;
	} convert;

	while (f < n_samples) {
		convert.i = src[i];
		re_in[f * 2] = convert.f;
		if (re_in[f * 2] > 1) re_in[f * 2] = 1;
		if (re_in[f * 2] < -1) re_in[f * 2] = -1;
		if (src_channels == 1) {
			re_in[(f * 2) + 1] = re_in[f * 2];
			i += 1;
		} else {
			convert.i = src[i + 1];
			re_in[(f * 2) + 1] = convert.f;
			if (re_in[(f * 2) + 1] > 1) re_in[(f * 2) + 1] = 1;
			if (re_in[(f * 2) + 1] < -1) re_in[(f * 2) + 1] = -1;
			i += 2;
		}

		f++;
	}

	resample_to_buffer(f);
}

void read_to_buffer_16in32_fs(int32_t src[], int n_samples) {
	// full samples version
	int i = 0;
	int f = 0;

	// Convert int16 to float
	while (f < n_samples) {
		re_in[f * 2] = (src[i]) / 32768.0;
		if (src_channels == 1) {
			re_in[(f * 2) + 1] = re_in[f * 2];
			i += 1;
		} else {
			re_in[(f * 2) + 1] = (src[i + 1]) / 32768.0;
			i += 2;
		}

		f++;
	}

	resample_to_buffer(f);
}

static inline float s16_to_float(const unsigned char *p) {
	return ((int16_t)((p[1] << 8) | p[0])) / 32768.0f;
}

void read_to_buffer_char16_resample(char src[], int n_bytes) {

	int i = 0;
	int f = 0;

	// Convert bytes16 to float
	while (i < n_bytes) {
		re_in[f * 2] = (float)((int16_t)((src[i + 1] << 8) | (src[i + 0] & 0xFF)) / 32768.0);
		if (src_channels == 1) {
			re_in[(f * 2) + 1] = re_in[f * 2];
			i += 2;
		} else {
			re_in[(f * 2) + 1] = (float)((int16_t)((src[i + 3] << 8) | (src[i + 2] & 0xFF)) / 32768.0);
			i += 4;
		}

		f++;
	}

	resample_to_buffer(f);

}



void read_to_buffer_char16(char src[], int n_bytes) {

	if (sample_rate_src != sample_rate_out) {
		read_to_buffer_char16_resample(src, n_bytes);
		return;
	}

	int i = 0;
	if (src_channels == 1) {
		while (i < n_bytes) {
			bfl[high] = (float)((int16_t)((src[i + 1] << 8) | (src[i + 0] & 0xFF)) / 32768.0);
			bfr[high] = bfl[high];
			fade_fx();
			high++;
			i += 2;
		}
	} else {
		while (i < n_bytes) {
			bfl[high] = (float)((int16_t)((src[i + 1] << 8) | (src[i + 0] & 0xFF)) / 32768.0);
			bfr[high] = (float)((int16_t)((src[i + 3] << 8) | (src[i + 2] & 0xFF)) / 32768.0);
			fade_fx();
			high++;
			i += 4;
		}
	}
	buff_cycle();
}

void read_to_buffer_s16int_resample(int16_t src[], int n_samples) {

	int i = 0;
	int f = 0;

	// Convert int16 to float
	while (i < n_samples) {
		re_in[f * 2] = (src[i]) / 32768.0;
		if (src_channels == 1) {
			re_in[(f * 2) + 1] = re_in[f * 2];
			i += 1;
		} else {
			re_in[(f * 2) + 1] = (src[i + 1]) / 32768.0;
			i += 2;
		}

		f++;
	}

	resample_to_buffer(f);

}

void read_to_buffer_s16int(int16_t src[], int n_samples) {

	if (sample_rate_src != sample_rate_out) {
		read_to_buffer_s16int_resample(src, n_samples);
		return;
	}

	int i = 0;
	if (src_channels == 1) {
		while (i < n_samples) {
			bfl[high] = src[i] / 32768.0;
			bfr[high] = bfl[high];
			fade_fx();

			i+=1;
			//buff_filled++;
			high++;
		}
		buff_cycle();

	} else {
		while (i < n_samples) {
			bfl[high] = src[i] / 32768.0;
			bfr[high] = src[i + 1] / 32768.0;
			fade_fx();

			i+=2;
			high++;
		}
		buff_cycle();
	}
}

// FLAC related ---------------------------------------------------------------

FLAC__StreamDecoderWriteStatus
f_write(const FLAC__StreamDecoder *decoder, const FLAC__Frame *frame, const FLAC__int32 *const buffer[],
		void *client_data) {

	//log_msg(LOG_INFO, "Frame size is: %d", frame->header.blocksize);
	//log_msg(LOG_INFO, "Resolution is: %d", frame->header.bits_per_sample);
	//log_msg(LOG_INFO, "Samplerate is: %d", frame->header.sample_rate);
	//log_msg(LOG_INFO, "Channels is  : %d", frame->header.channels);

	pthread_mutex_lock(&buffer_mutex);

	/* if (frame->header.sample_rate != current_sample_rate) { */
	/*   if (want_sample_rate != frame->header.sample_rate) { */
	/*     want_sample_rate = frame->header.sample_rate; */
	/*     sample_change_byte = (buff_filled + buff_base) % BUFF_SIZE; */
	/*   } */
	/* } */

//    if (sample_rate_out != current_sample_rate) {
//        if (want_sample_rate != sample_rate_out) {
//            want_sample_rate = sample_rate_out;
//            sample_change_byte = high;
//        }
//    }

	if (current_length_count == 0) {
		current_length_count = FLAC__stream_decoder_get_total_samples(decoder);
	}


	unsigned int i = 0;
	int resample = 0;
	int old_sample_rate = sample_rate_src;
	sample_rate_src = frame->header.sample_rate;
	flac_got_rate = 1;
	if (old_sample_rate != sample_rate_src) {
		src_reset(src);
	}
	if (sample_rate_src != sample_rate_out && config_resample == 1) {
		resample = 1;
	}

	if (load_target_seek > 0) {
		pthread_mutex_unlock(&buffer_mutex);
		return FLAC__STREAM_DECODER_WRITE_STATUS_CONTINUE;
	}

	if (frame->header.blocksize > (BUFF_SIZE - get_buff_fill())) {
		log_msg(LOG_CRITICAL, "pa: BUFFER OVERFLOW!");
	}

	int temp_fill = 0;

	if (resample == 0) {

		// No resampling needed, transfer data to main buffer

		while (i < frame->header.blocksize) {

			// Read and handle 24bit audio
			if (frame->header.bits_per_sample == 24) {

				bfl[high] = (buffer[0][i]) / 8388608.0;

				if (frame->header.channels == 1) {
					bfr[high] = bfl[high];
				} else {
					bfr[high] = (buffer[1][i]) / 8388608.0;
				}
			} // end 24 bit audio

				// Read 16bit audio
			else if (frame->header.bits_per_sample == 16) {
				bfl[high] = (buffer[0][i]) / 32768.0;
				if (frame->header.channels == 1) {
					bfr[high] = (buffer[0][i]) / 32768.0;
				} else {
					bfr[high] = (buffer[1][i]) / 32768.0;
				}
			} else log_msg(LOG_CRITICAL, "ph: INVALID BIT DEPTH!");

			fade_fx();


			high++;
			i++;
		}

		buff_cycle();

	} else {

		// Transfer data to resampler for resampling

		while (i < frame->header.blocksize) {
			// Read and handle 24bit audio
			if (frame->header.bits_per_sample == 24) {

				re_in[i * 2] = (buffer[0][i]) / (8388608.0);
				if (frame->header.channels == 1) re_in[(i * 2) + 1] = re_in[i * 2];
				else re_in[(i * 2) + 1] = (buffer[1][i]) / 8388608.0;

			} // end 24 bit audio

				// Read 16bit audio
			else if (frame->header.bits_per_sample == 16) {

				re_in[i * 2] = (buffer[0][i]) / 32768.0;
				if (frame->header.channels == 1) re_in[(i * 2) + 1] = re_in[i * 2];
				else re_in[(i * 2) + 1] = (buffer[1][i]) / 32768.0;

			} else log_msg(LOG_CRITICAL, "ph: INVALID BIT DEPTH!");

			temp_fill++;
			i++;

		}

		resample_to_buffer(temp_fill);

	}

	pthread_mutex_unlock(&buffer_mutex);
	return FLAC__STREAM_DECODER_WRITE_STATUS_CONTINUE;
}

void f_meta(const FLAC__StreamDecoder *decoder, const FLAC__StreamMetadata *metadata, void *client_data) {
	log_msg(LOG_INFO, "GOT META");
}

void f_err(const FLAC__StreamDecoder *decoder, FLAC__StreamDecoderErrorStatus status, void *client_data) {
	log_msg(LOG_ERROR, "GOT FLAC ERR");
}


FLAC__StreamDecoder *dec;
FLAC__StreamDecoderInitStatus status;

// -----------------------------------------------------------------------------------

void stop_decoder() {

	if (decoder_allocated == 0) {
		bs_close();
		return;
	}

	switch (codec) {
		case OPUS:
			op_free(opus_dec);
			break;
		case VORBIS:
			ov_clear(&vf);
			break;
		case FLAC:
			FLAC__stream_decoder_finish(dec);
			break;
		case WAVPACK:
			WavpackCloseFile(wpc);
			break;
		case MPG:
			mpg123_close(mh);
			break;
		case FFMPEG:
			stop_ffmpeg();
			break;
		case WAVE:
			wave_close();
			break;
		case MPT:
			openmpt_module_destroy(mod);
			break;
		case GME:
			gme_delete(emu);
			break;
	}
	//src_reset(src);
	bs_close();
	decoder_allocated = 0;
}

static void eq_reset_state() {
	for (int i = 0; i < EQ_BAND_COUNT; i++) {
		eq_bands[i].z1_l = 0.0f;
		eq_bands[i].z2_l = 0.0f;
		eq_bands[i].z1_r = 0.0f;
		eq_bands[i].z2_r = 0.0f;
	}
}

static void limiter_reset_state() {
	limiter_gain = 1.0f;
}

static void limiter_update_coefficients(int sample_rate) {
	if (sample_rate <= 0) return;

	float attack_samples = (LIMITER_ATTACK_MS * 0.001f) * (float)sample_rate;
	float release_samples = (LIMITER_RELEASE_MS * 0.001f) * (float)sample_rate;

	if (attack_samples < 1.0f) attack_samples = 1.0f;
	if (release_samples < 1.0f) release_samples = 1.0f;

	limiter_attack_coeff = expf(-1.0f / attack_samples);
	limiter_release_coeff = expf(-1.0f / release_samples);
	limiter_coeff_sample_rate = sample_rate;
}

static float eq_biquad_magnitude(const eq_biquad_t *f, float w) {
	float cos_w = cosf(w);
	float sin_w = sinf(w);
	float cos_2w = cosf(2.0f * w);
	float sin_2w = sinf(2.0f * w);

	float nr = f->b0 + (f->b1 * cos_w) + (f->b2 * cos_2w);
	float ni = -(f->b1 * sin_w) - (f->b2 * sin_2w);
	float dr = 1.0f + (f->a1 * cos_w) + (f->a2 * cos_2w);
	float di = -(f->a1 * sin_w) - (f->a2 * sin_2w);

	float den = (dr * dr) + (di * di);
	if (den <= 1e-20f) return 1.0f;

	float mag2 = ((nr * nr) + (ni * ni)) / den;
	if (mag2 <= 0.0f || !isfinite(mag2)) return 1.0f;

	return sqrtf(mag2);
}

static void eq_update_auto_headroom(int sample_rate) {
	const float two_pi = 6.28318530717958647692f;
	const float min_freq = 20.0f;
	const int sweep_points = 192;

	eq_headroom_db = 0.0f;
	eq_headroom_gain = 1.0f;

	if (!eq_enabled || !eq_active || sample_rate <= 0) return;

	float max_freq = sample_rate * 0.49f;
	if (max_freq <= min_freq) return;

	float ratio = max_freq / min_freq;
	float max_mag = 1.0f;

	for (int i = 0; i < sweep_points; i++) {
		float t = i / (float)(sweep_points - 1);
		float freq = min_freq * powf(ratio, t);
		float w = two_pi * (freq / (float)sample_rate);
		float total_mag = 1.0f;

		for (int band = 0; band < EQ_BAND_COUNT; band++) {
			if (fabsf(eq_band_gain_db[band]) < 0.01f) continue;
			total_mag *= eq_biquad_magnitude(&eq_bands[band], w);
		}

		if (isfinite(total_mag) && total_mag > max_mag) max_mag = total_mag;
	}

	if (max_mag > 1.0f) {
		eq_headroom_db = (20.0f * log10f(max_mag)) + EQ_AUTO_HEADROOM_MARGIN_DB;
		eq_headroom_gain = powf(10.0f, -eq_headroom_db / 20.0f);
	}
}

static void eq_set_identity(eq_biquad_t *f) {
	f->b0 = 1.0f;
	f->b1 = 0.0f;
	f->b2 = 0.0f;
	f->a1 = 0.0f;
	f->a2 = 0.0f;
}

static void eq_rebuild_coefficients(int sample_rate) {
	const float q = 1.41421356237f;
	const float two_pi = 6.28318530717958647692f;
	bool reset_state = (eq_coeff_sample_rate != sample_rate);

	if (sample_rate <= 0) return;

	eq_active = 0;

	for (int i = 0; i < EQ_BAND_COUNT; i++) {
		float gain_db = eq_band_gain_db[i];
		float freq = eq_band_freqs[i];
		eq_biquad_t *f = &eq_bands[i];

		if (gain_db > 12.0f) gain_db = 12.0f;
		if (gain_db < -12.0f) gain_db = -12.0f;
		eq_band_gain_db[i] = gain_db;

		if (fabsf(gain_db) < 0.01f || freq >= (sample_rate * 0.49f)) {
			eq_set_identity(f);
			continue;
		}

		float w0 = two_pi * (freq / (float) sample_rate);
		float cw = cosf(w0);
		float sw = sinf(w0);
		float alpha = sw / (2.0f * q);
		float a = powf(10.0f, gain_db / 40.0f);
		float b0 = 1.0f + (alpha * a);
		float b1 = -2.0f * cw;
		float b2 = 1.0f - (alpha * a);
		float a0 = 1.0f + (alpha / a);
		float a1 = -2.0f * cw;
		float a2 = 1.0f - (alpha / a);

		if (a0 == 0.0f || !isfinite(b0) || !isfinite(b1) || !isfinite(b2) || !isfinite(a1) || !isfinite(a2)) {
			eq_set_identity(f);
			continue;
		}

		f->b0 = b0 / a0;
		f->b1 = b1 / a0;
		f->b2 = b2 / a0;
		f->a1 = a1 / a0;
		f->a2 = a2 / a0;
		eq_active = 1;
	}

	eq_coeff_sample_rate = sample_rate;
	eq_dirty = false;
	eq_update_auto_headroom(sample_rate);
	if (reset_state) {
		eq_reset_state();
		limiter_reset_state();
		limiter_update_coefficients(sample_rate);
	}
}

static inline float eq_process_biquad(float x, eq_biquad_t *f, bool left) {
	float *z1 = left ? &f->z1_l : &f->z1_r;
	float *z2 = left ? &f->z2_l : &f->z2_r;
	float y = (f->b0 * x) + *z1;
	*z1 = (f->b1 * x) - (f->a1 * y) + *z2;
	*z2 = (f->b2 * x) - (f->a2 * y);
	return y;
}

static inline void eq_process_stereo(float *l, float *r) {
	if (!eq_enabled || !eq_active) return;

	float ll = *l;
	float rr = *r;
	for (int i = 0; i < EQ_BAND_COUNT; i++) {
		ll = eq_process_biquad(ll, &eq_bands[i], true);
		rr = eq_process_biquad(rr, &eq_bands[i], false);
	}

	*l = ll;
	*r = rr;
}

static inline void limiter_process_stereo(float *l, float *r) {
	if (!eq_enabled || !eq_active) return;

	if (current_sample_rate > 0 && limiter_coeff_sample_rate != current_sample_rate) {
		limiter_update_coefficients(current_sample_rate);
	}

	float peak = fmaxf(fabsf(*l), fabsf(*r));
	float target_gain = 1.0f;
	if (peak > LIMITER_THRESHOLD) {
		target_gain = LIMITER_THRESHOLD / (peak + 1e-20f);
	}

	if (target_gain < limiter_gain) {
		limiter_gain = target_gain + (limiter_attack_coeff * (limiter_gain - target_gain));
	} else {
		limiter_gain = target_gain + (limiter_release_coeff * (limiter_gain - target_gain));
	}

	if (!isfinite(limiter_gain) || limiter_gain <= 0.0f) limiter_gain = 1.0f;

	*l *= limiter_gain;
	*r *= limiter_gain;

	// final guard against any possible hard clipping
	if (*l > 1.0f) *l = 1.0f;
	else if (*l < -1.0f) *l = -1.0f;
	if (*r > 1.0f) *r = 1.0f;
	else if (*r < -1.0f) *r = -1.0f;
}

int get_audio(int max, float* buff) {
		int b = 0;

		pthread_mutex_lock(&buffer_mutex);

		if (buffering == 1 && get_buff_fill() > config_min_buffer) {
			buffering = 0;
			log_msg(LOG_INFO, "pa: Buffering -> Playing");
		}

		if (get_buff_fill() < 10 && loaded_target_file[0] == 'h') {

			if (mode == PLAYING) {
				if (buffering == 0) log_msg(LOG_INFO, "pa: Buffering...");
				buffering = 1;
			} else buffering = 0;
		}

		// Don't let a buffering wait hold up draining/stopping
		if (buffering == 1 && mode != PLAYING) buffering = 0;


//		if (get_buff_fill() < max && mode == PLAYING && decoder_allocated == 1) {
//			//log_msg(LOG_WARNING, "pa: Buffer underrun");
//		}

		// Put fade buffer back
		if (mode == PLAYING && fade_fill > 0 && get_buff_fill() < max && !fade_lockout) {
			//pthread_mutex_lock(&buffer_mutex);
			int i = 0;
			while (fade_position < fade_fill) {
				float cross = fade_position / (float) fade_fill;
				float cross_i = 1.0 - cross;
				bfl[high] = fadefl[fade_position] * cross_i;
				bfr[high] = fadefr[fade_position] * cross_i;
				fade_position++;
				high++;
				i++;
				if (i > max) break;
			}
			buff_cycle();
			if (fade_position == fade_fill) {
				fade_fill = 0;
				fade_position = 0;
			}
			//pthread_mutex_unlock(&buffer_mutex);
		}

		if (mode == PAUSED || (mode == PLAYING && get_buff_fill() == 0)) {

		}
		// Process decoded audio data and send out
		else if ((mode == PLAYING || mode == RAMP_DOWN || mode == ENDING) && get_buff_fill() > 0 && buffering == 0) {

			//pthread_mutex_lock(&buffer_mutex);
			if (eq_enabled && current_sample_rate > 0 && (eq_dirty || eq_coeff_sample_rate != current_sample_rate)) {
				eq_rebuild_coefficients(current_sample_rate);
			}

			b = 0; // byte number

			peak_roll_l = 0;
			peak_roll_r = 0;

			//log_msg(LOG_INFO, "pa: Buffer is at %d", buff_filled);

			// Fill the out buffer...
			while (get_buff_fill() > 0) {


				// Truncate data if gate is closed anyway
				if (mode == RAMP_DOWN && gate == 0) break;

//				if (want_sample_rate > 0 && sample_change_byte == buff_base) {
//					//log_msg(LOG_INFO, "pa: Set new sample rate");
//					connect_pulse();
//					break;
//				}

				if (reset_set && reset_set_byte == low) {
					//log_msg(LOG_INFO, "pa: Reset position counter");
					reset_set = false;
					position_count = reset_set_value;
				}


				// Ramp control ---
				if (mode == RAMP_DOWN) {
					gate -= ramp_step(current_sample_rate, 5);
					if (gate < 0) gate = 0;
				}

				if (gate < 1 && mode == PLAYING) {
					gate += ramp_step(current_sample_rate, 5);
					if (gate > 1) gate = 1;
				}

				// Volume control ---
				if (volume_want > volume_on) {
					volume_on += ramp_step(current_sample_rate, volume_ramp_speed);

					if (volume_on > volume_want) {
						volume_on = volume_want;
					}
				}

				if (volume_want < volume_on) {
					volume_on -= ramp_step(current_sample_rate, volume_ramp_speed);

					if (volume_on < volume_want) {
						volume_on = volume_want;
					}
				}

				float l = bfl[low];
				float r = bfr[low];
				eq_process_stereo(&l, &r);

				if (fabs(l) > peak_roll_l) peak_roll_l = fabs(l);
				if (fabs(r) > peak_roll_r) peak_roll_r = fabs(r);

				// vis stuff
				if (vis_side_fill + 2 < VIS_SIDE_MAX){
					vis_side_buffer[vis_side_fill] = l;
					vis_side_buffer[vis_side_fill + 1] = r;
					vis_side_fill += 2;
				}

				// Apply final volume adjustment
				float final_vol = pow((gate * volume_on), config_volume_power);
				if (eq_enabled && eq_active) final_vol *= eq_headroom_gain;
				l = l * final_vol;
				r = r * final_vol;
				limiter_process_stereo(&l, &r);

				buff[b] = l;
				buff[b + 1] = r;
				b += 2;

				low += 1;
				buff_cycle();

				position_count++;

				if (b >= max) break; // Buffer is now full
			}



			if (b > 0) {
				if (peak_roll_l > peak_l) peak_l = peak_roll_l;
				if (peak_roll_r > peak_r) peak_r = peak_roll_r;
				pthread_mutex_unlock(&buffer_mutex);
				return b;

			} // sent data

		} // close if data
		memset(buff, 0, max * sizeof(float));
		pthread_mutex_unlock(&buffer_mutex);
		return max;
}

#ifdef PIPE
	static void on_process(void *userdata) {
		//struct pw_stream *stream = userdata;
		struct pw_buffer *buffer;
		struct spa_buffer *buf;
		//void *data;
		int size;


		if ((buffer = pw_stream_dequeue_buffer(global_stream)) == NULL)
			return;

		buf = buffer->buffer;

		size = get_audio(buffer->requested * 2, buf->datas[0].data) * 4;

		buf->datas[0].chunk->size = size;
		pw_stream_queue_buffer(global_stream, buffer);

	}

	static void on_stream_state_changed(
		void *data,
		enum pw_stream_state old,
		enum pw_stream_state state,
		const char *error) {
		if (
			state == PW_STREAM_STATE_ERROR ||
			state == PW_STREAM_STATE_UNCONNECTED) {
			log_msg(LOG_ERROR, "PipeWire stream lost (%s)", error ? error : "no error");
			pulse_connected = false;
		}
	}

	static const struct pw_stream_events stream_events = {
		PW_VERSION_STREAM_EVENTS,
		.process = on_process,
		.state_changed = on_stream_state_changed,
	};


	void *pipewire_main_loop_thread(void *thread_id) {

		pw_running = true;
		log_msg(LOG_INFO, "Begin Pipewire init...");
		pw_init(NULL, NULL);

		loop = pw_main_loop_new(NULL /* properties */);
		if (loop == NULL) {
			log_msg(LOG_ERROR, "Error: Failed to create main loop");
			return thread_id;
		}

		context = pw_context_new(
			pw_main_loop_get_loop(loop),
			NULL /* properties */,
			0 /* user_data size */);
		if (context == NULL) {
			log_msg(LOG_ERROR, "Error: Failed to create context");
			return thread_id;
		}

		core = pw_context_connect(
			context,
			NULL /* properties */,
			0 /* user_data size */);
		if (core == NULL) {
			log_msg(LOG_ERROR, "Error: Failed to connect to PipeWire");
			return thread_id;
		}

		registry = pw_core_get_registry(core, PW_VERSION_REGISTRY,
						0 /* user_data size */);
		if (registry == NULL) {
			log_msg(LOG_ERROR, "Error: Failed to get registry");
			return thread_id;
		}

		spa_zero(registry_listener);
		int res;
		res = pw_registry_add_listener(registry, &registry_listener, &registry_events, NULL);

		if (res < 0) {
			log_msg(LOG_ERROR, "Error: Failed to add registry listener: %s", spa_strerror(res));
			return thread_id;
		}

		res = pw_core_add_listener(core, &core_listener, &core_events, NULL);
		if (res < 0) {
			log_msg(LOG_ERROR, "Error: Failed to add core listener: %s", spa_strerror(res));
			return thread_id;
		}
		pw_core_sync(core, PW_ID_CORE, 0);


		global_stream = pw_stream_new_simple(
			pw_main_loop_get_loop(loop),
			"Tauon",
			pw_properties_new(
				PW_KEY_MEDIA_TYPE, "Audio",
				PW_KEY_MEDIA_CATEGORY, "Playback",
				PW_KEY_MEDIA_ROLE, "Music",
				NULL),
			&stream_events,
			NULL
		);
		if (global_stream == NULL) {
			log_msg(LOG_ERROR, "Error: Failed to create stream");
			return thread_id;
		}
		//log_msg(LOG_INFO, "Run pipewire main loop...");
		res = pw_main_loop_run(loop);

		if (res < 0) {
			log_msg(LOG_ERROR, "Error: Main loop run failed: %s", spa_strerror(res));
			return thread_id;
		}


		if (registry) {
			pw_proxy_destroy((struct pw_proxy*)registry);
		}
		if (core) {
			spa_hook_remove(&core_listener);
			pw_core_disconnect(core);
		}
		if (global_stream) {
			pw_stream_destroy(global_stream);
		}
		if (context) {
			pw_context_destroy(context);
		}
		if (loop) {
			pw_main_loop_destroy(loop);
		}
		pw_deinit();
		//log_msg(LOG_INFO, "Exit pipewire main loop");
		pw_running = false;
		return thread_id;
	}
#endif


#ifdef MINI
	void data_callback(ma_device* pDevice, void* pOutput, const void* pInput, ma_uint32 frameCount) {
		get_audio(frameCount * 2, pOutput);
		//if (0 < b && b < frameCount) log_msg(LOG_INFO, "ph: Buffer underrun");
	}

	void notification_callback(const ma_device_notification* pNotification) {
		if (pNotification->type == ma_device_notification_type_stopped) {
			device_stopped = true;
			signaled_device_unavailable = false;
		}
	}

	ma_device_info* pPlaybackDeviceInfos;
	ma_uint32 playbackDeviceCount = 0;
	ma_result result;
	ma_context context;
	int context_allocated = 0;
	ma_uint32 iDevice;

	int initiate_ma_context() {
		if (context_allocated == 0) {
			if (ma_context_init(NULL, 0, NULL, &context) != MA_SUCCESS) {
				log_msg(LOG_ERROR, "Failed to initialize context.");
				return -1;
			}
			context_allocated = 1;
		}
		return 1;
	}

	void my_log_callback(void* pUserData, ma_uint32 level, const char* pMessage) {
		log_msg(LOG_INFO, "Log [%u]: %s", level, pMessage);
		// Additional logic for handling log messages can be added here
	}
#endif

void decode_seek(int abs_ms, int sample_rate) {
	switch (codec) {
		case FLAC:
			FLAC__stream_decoder_seek_absolute(dec, (int) sample_rate * (abs_ms / 1000.0));
			break;
		case OPUS:
			op_pcm_seek(opus_dec, (int) sample_rate * (abs_ms / 1000.0));
			samples_decoded = sample_rate * (abs_ms / 1000.0) * 2;
			break;
		case VORBIS:
			ov_pcm_seek(&vf, (ogg_int64_t) sample_rate * (abs_ms / 1000.0));
			break;
		case WAVPACK:
			WavpackSeekSample64(wpc, (int64_t) sample_rate * (abs_ms / 1000.0));
			break;
		case MPG:
			mpg123_seek(mh, (int) sample_rate * (abs_ms / 1000.0), SEEK_SET);
			break;
		case FFMPEG:
			stop_ffmpeg();
			start_ffmpeg(loaded_target_file, abs_ms);
			break;
		case WAVE:
			wave_seek((int) sample_rate * (abs_ms / 1000.0));
			break;
		case MPT:
			openmpt_module_set_position_seconds(mod, abs_ms / 1000.0);
			break;
		case GME:
			gme_seek(emu, (long) abs_ms);
			break;
	}
}

#ifdef PIPE
	static int pipe_disconnect(struct spa_loop *loop, bool async, uint32_t seq, const void *_data, size_t size, void *user_data) {
		return pw_stream_disconnect(global_stream);
	}
#endif

int disconnect_pulse() {
	//log_msg(LOG_INFO, "ph: Disconnect Device");

	if (pulse_connected) {
		#ifdef MINI
			ma_device_uninit(&device);
		#endif

		#ifdef PIPE
			pw_loop_invoke(pw_main_loop_get_loop(loop), pipe_disconnect, SPA_ID_INVALID, NULL, 0, true, NULL);
		#endif

	}
	pulse_connected = false;
	gate = 0.0;
	return 0;
}

#ifdef PIPE
	static int pipe_exit(
		struct spa_loop *loopo, bool async, uint32_t seq, const void *_data, size_t size, void *user_data
	) {
		pw_main_loop_quit(loop);
		return 0;
	}

	struct pw_stream *global_stream = NULL; // Initialize appropriately

	static int pipe_connect(
		struct spa_loop *loop, bool async, uint32_t seq, const void *_data, size_t size, void *user_data
	) {
		enum pw_stream_state st = pw_stream_get_state(global_stream, NULL);
		if (st != PW_STREAM_STATE_UNCONNECTED) {
			log_msg(LOG_ERROR, "pipe_connect: stream not unconnected (state=%d)", st);
			return -EBUSY;
		}
		struct spa_pod_builder b = { 0 };
		uint8_t buffer[POD_BUFFER_SIZE];
		const struct spa_pod *params[1];
		int ret;

		// Initialize the pod builder
		spa_pod_builder_init(&b, buffer, sizeof(buffer));

		// Build audio format parameters
		params[0] = spa_format_audio_raw_build(
			&b, SPA_PARAM_EnumFormat,
			&SPA_AUDIO_INFO_RAW_INIT(
			.format = SPA_AUDIO_FORMAT_F32,
			.channels = 2,
			.rate = pipe_set_samplerate));
		if (params[0] == NULL) {
			log_msg(LOG_ERROR, "Failed to build audio format parameters");
			return -EINVAL;
		}

		// Select the appropriate device
		ssize_t selected_index = -1;

		pthread_mutex_lock(&pipe_devices_mutex);
		for (size_t i = 0; i < pipe_devices.device_count; i++) {
			if (strcmp(pipe_devices.devices[i].description, config_output_sink) == 0) {
				selected_index = i;
				break; // Stop at the first match
			}
		}
		pthread_mutex_unlock(&pipe_devices_mutex);

		// Get and copy stream properties
		const struct pw_properties *props = pw_stream_get_properties(global_stream);
		if (props == NULL) {
			log_msg(LOG_ERROR, "Failed to get stream properties");
			return -EINVAL;
		}

		struct pw_properties *mutable_props = pw_properties_copy(props);
		if (mutable_props == NULL) {
			log_msg(LOG_ERROR, "Failed to copy stream properties");
			return -ENOMEM;
		}

		// Set the target device if selected
		if (selected_index != -1) {
			pthread_mutex_lock(&pipe_devices_mutex);
			const char *device_name = pipe_devices.devices[selected_index].name;
			pthread_mutex_unlock(&pipe_devices_mutex);

			if (device_name) {
				pw_properties_set(mutable_props, PW_KEY_TARGET_OBJECT, device_name);
				log_msg(LOG_INFO, "Selected device index: %zu (%s)", selected_index, device_name);
			} else {
				log_msg(LOG_ERROR, "Selected device has no name");
				pw_properties_set(mutable_props, PW_KEY_TARGET_OBJECT, "");
			}
		} else {
			// Optionally, handle the case where no device is selected
			pw_properties_set(mutable_props, PW_KEY_TARGET_OBJECT, "");
			log_msg(LOG_INFO, "Using default device.");
		}

		// Update the stream properties
		ret = pw_stream_update_properties(global_stream, &mutable_props->dict);
		if (ret < 0) {
			log_msg(LOG_ERROR, "Failed to update stream properties: %d", ret);
			pw_properties_free(mutable_props);
			return ret;
		}

		pw_properties_free(mutable_props);

		// Connect the stream
		ret = pw_stream_connect(
			global_stream,
			PW_DIRECTION_OUTPUT,
			PW_ID_ANY,
			PW_STREAM_FLAG_AUTOCONNECT |
			PW_STREAM_FLAG_MAP_BUFFERS |
			PW_STREAM_FLAG_RT_PROCESS,
			params, 1);
		if (ret < 0) {
			log_msg(LOG_ERROR, "Failed to connect stream: %d", ret);
			return ret;
		}

		log_msg(LOG_INFO, "Stream connected successfully.");
		return 0; // Success
	}

	static int pipe_update(
		struct spa_loop *loop, bool async, uint32_t seq,
		const void *_data, size_t size, void *user_data) {

			pw_stream_disconnect(global_stream);
			return pipe_connect(loop, async, seq, _data, size, user_data);
	}
#endif

void connect_pulse() {

	if (pulse_connected) {
		//log_msg(LOG_INFO, "pa: Reconnect");
		disconnect_pulse();
	}
	log_msg(LOG_INFO, "ph: Connect");

	#ifdef MINI
		if (getenv("MA_DEBUG")) {
			ma_result result;
			ma_log logger;

			log_msg(LOG_INFO, "Initialize logger.");

			// Initialize the logger
			result = ma_log_init(NULL, &logger);
			if (result != MA_SUCCESS) {
				log_msg(LOG_ERROR, "Failed to initialize logger.");
				return;
			}

				// Create the log callback structure
			ma_log_callback logCallback = ma_log_callback_init(my_log_callback, NULL);

			// Register the log callback
			result = ma_log_register_callback(&logger, logCallback);
			if (result != MA_SUCCESS) {
				log_msg(LOG_ERROR, "Failed to register log callback.");
				ma_log_uninit(&logger);
				return;
			}
		}

		int n = -1;
		if (strcmp(config_output_sink, "Default") != 0) {
			for (int i = 0; i < playbackDeviceCount; ++i) {
				if (strcmp(pPlaybackDeviceInfos[i].name, config_output_sink) == 0) {
					n = i;
				}
			}
		}

		//log_msg(LOG_INFO, "ph: Connect device\n");

		c_config.pulse.pApplicationName = "Tauon Music Box";
		if (initiate_ma_context() == -1) return;

		result = ma_context_get_devices(&context, &pPlaybackDeviceInfos, &playbackDeviceCount, NULL, NULL);
		if (result != MA_SUCCESS) {
			log_msg(LOG_ERROR, "Failed to retrieve device information.");
			return;
		}

		int set_samplerate = 0;

		if (sample_rate_src > 0) set_samplerate = sample_rate_src;

		ma_device_config config = ma_device_config_init(ma_device_type_playback);
		if (n > -1) config.playback.pDeviceID = &pPlaybackDeviceInfos[n].id;
		config.playback.format   = ma_format_f32;   // Set to ma_format_unknown to use the device's native format.
		config.playback.channels = 2;               // Set to 0 to use the device's native channel count.
		config.sampleRate        = set_samplerate;           // Set to 0 to use the device's native sample rate.
		config.dataCallback      = data_callback;   // This function will be called when miniaudio needs more data.
		config.notificationCallback = notification_callback;
		config.periodSizeInMilliseconds      = config_dev_buffer / 4;
		config.periods      = 4;   //

		ma_result result;
		result = ma_device_init(&context, &config, &device);
		if (result != MA_SUCCESS) {
			log_msg(LOG_ERROR, "ph: Device init error");
			const char* description = ma_result_description(result);
			log_msg(LOG_ERROR, "Result Description: %s", description);
			mode = STOPPED;
			return;  // Failed to initialize the device.
		}

		//dev = config_output_sink;
		log_msg(LOG_INFO, "ph: Connected using samplerate %uhz", device.sampleRate);

		sample_rate_out = device.sampleRate;
	#endif

	#ifdef PIPE
		int set_samplerate = 48000;
		if (sample_rate_src > 0) pipe_set_samplerate = sample_rate_src;
		log_msg(LOG_INFO, "SET PIPE SAMPLERATE: %d", set_samplerate);
		sample_rate_out = pipe_set_samplerate;

		pw_loop_invoke(pw_main_loop_get_loop(loop), pipe_connect, SPA_ID_INVALID, NULL, 0, true, NULL);
	#endif

	if (decoder_allocated == 1 && current_sample_rate > 0 &&
		sample_rate_out > 0 && position_count > get_buff_fill() &&
		current_sample_rate != sample_rate_out && position_count > 0 && get_buff_fill() > 0) {

		src_reset(src);
		log_msg(LOG_WARNING, "ph: The samplerate changed, rewinding");
		if (!reset_set) {
			decode_seek(position_count / sample_rate_src * 1000, sample_rate_src);
		}

		buff_reset();
	}

	current_sample_rate = sample_rate_out;

	pulse_connected = true;

}

volatile int stream_loading = 0;  // load_next in progress; loads can block on network I/O

int64_t stream_meta_end = 0;  // bytes of leading metadata (ID3/FLAC blocks) before the audio data

int load_next_inner() {
	// Function to load a file / prepare decoder
	#ifdef WIN64
		free(loaded_target_wpath);
		loaded_target_wpath = utf8_to_wide_path(loaded_target_file);
	#endif

	stop_decoder();

	strcpy(loaded_target_file, load_target_file);
	loaded_target_net = load_target_net;

	int channels;
	int encoding;
	long rate;
	int e = 0;
	int old_sample_rate = sample_rate_src;
	src_channels = 2;

	bool is_net = loaded_target_net == 1 && loaded_target_file[0] == 'h';

	// For URLs, ignore any query string when looking at the file extension
	static char ext_path[4096];
	strcpy(ext_path, loaded_target_file);
	if (is_net) {
		char *q = strchr(ext_path, '?');
		if (q != NULL) *q = '\0';
	}
	char *ext;
	ext = strrchr(ext_path, '.');

	codec = UNKNOWN;
	current_length_count = 0;
	buffering = 0;
	samples_decoded = 0;
	stream_meta_end = 0;

	if (loaded_target_file[0] == 'h') buffering = 1;

	rg_byte = high;

	char peak[35];

	if (strcmp(loaded_target_file, "RAW FEED") == 0) {
		codec = FEED;
		load_target_seek = 0;
		pthread_mutex_lock(&buffer_mutex);
//		if (current_sample_rate != sample_rate_out) {
//			sample_change_byte = high;
//			want_sample_rate = config_feed_samplerate;
//		}
		sample_rate_src = config_feed_samplerate;
		src_reset(src);
		pthread_mutex_unlock(&buffer_mutex);
		decoder_allocated = 1;
		buffering = 1;
		return 0;
	}

	// If target is a radio/plain url, use FFMPEG
	if (loaded_target_file[0] == 'h' && !is_net) {
		codec = FFMPEG;
		start_ffmpeg(loaded_target_file, load_target_seek);
		load_target_seek = 0;
		pthread_mutex_lock(&buffer_mutex);
		if (old_sample_rate != sample_rate_src) {
			src_reset(src);
		}
		pthread_mutex_unlock(&buffer_mutex);

		return 0;
	}

	// Open the byte stream. For network targets the Python feeder will
	// notice the new generation and start supplying data.
	if (is_net) {
		if (bs_open_net(loaded_target_file) != 0) return 1;
	} else {
		if (bs_open_local(loaded_target_file) != 0) return 1;
	}

	// We need to identify the file type
	// Peak into file and try to detect signature

	if (bs_read_exact(peak, sizeof(peak)) != sizeof(peak)) {
		log_msg(LOG_ERROR, "pa: Could not read start of file: '%s'", loaded_target_file);
		bs_close();
		return 1;
	}
	load_file_size = (off_t) bs_length();

	if (memcmp(peak, "fLaC", 4) == 0) {
		codec = FLAC;
		//log_msg(LOG_INFO, "Detected flac");
	} else if (memcmp(peak, "RIFF", 4) == 0) {
		codec = FFMPEG; //WAVE;
	} else if (memcmp(peak, "OggS", 4) == 0) {
		codec = VORBIS;
		if (peak[28] == 'O' && peak[29] == 'p') codec = OPUS;
	} else if (memcmp(peak, "\xff\xfb", 2) == 0) {
		codec = MPG;
		//log_msg(LOG_INFO, "Detected mp3");
	} else if (memcmp(peak, "\xff\xf3", 2) == 0) {
		codec = MPG;
		//log_msg(LOG_INFO, "Detected mp3");
	} else if (memcmp(peak, "\xff\xf2", 2) == 0) {
		codec = MPG;
		//log_msg(LOG_INFO, "Detected mp3");
	} else if (memcmp(peak, "\0\0\0\x20" "ftypM4A", 11) == 0) {
		codec = FFMPEG;
		//log_msg(LOG_INFO, "Detected m4a");
	} else if (memcmp(peak, "\0\0\0\x18" "ftypdash", 12) == 0) {
		codec = FFMPEG;
		//log_msg(LOG_INFO, "Detected m4a");
	} else if (memcmp(peak, "\0\0\0\x18" "ftypiso5", 12) == 0) {
		codec = FFMPEG;
		//log_msg(LOG_INFO, "Detected m4a");
	} else if (memcmp(peak, "\x30\x26\xb2\x75\x8e\x66\xcf\x11", 8) == 0) {
		codec = FFMPEG;
		//log_msg(LOG_INFO, "Detected wma");
	} else if (memcmp(peak, "MAC\x20", 4) == 0) {
		codec = FFMPEG;
		//log_msg(LOG_INFO, "Detected ape");
	} else if (memcmp(peak, "TTA1", 4) == 0) {
		codec = FFMPEG;
		//log_msg(LOG_INFO, "Detected tta");
	} else if (memcmp(peak, "wvpk", 4) == 0) {
		codec = WAVPACK;
		log_msg(LOG_INFO, "Detected wavpack");

	} else if (memcmp(peak, "\x49\x44\x33", 3) == 0) {
		int id3_size = (peak[6] << 21) | (peak[7] << 14) | (peak[8] << 7) | peak[9];
		codec = MPG;
		stream_meta_end = id3_size + 10;
		// Probing past the ID3 tag for a FLAC marker would mean an extra
		// range request round trip on network streams with large embedded
		// art, so only look when the tag end is near
		if (!is_net || id3_size + 14 < BS_FORWARD_GAP) {
			unsigned char flac_marker[4];
			if (bs_seek_abs(id3_size + 10) == 0 && bs_read_exact(flac_marker, 4) == 4
					&& memcmp(flac_marker, "fLaC", 4) == 0) {
				codec = FLAC;
				log_msg(LOG_INFO, "Detected FLAC with ID3 header\n");
			}
		}
	}
	bs_seek_abs(0);

	// Fallback to detecting using file extension
	if (codec == UNKNOWN && ext != NULL && (
			strcmp(ext, ".ape") == 0 || strcmp(ext, ".APE") == 0 ||
			strcmp(ext, ".m4a") == 0 || strcmp(ext, ".M4A") == 0 ||
			strcmp(ext, ".mp4") == 0 || strcmp(ext, ".MP4") == 0 ||
			strcmp(ext, ".webm") == 0 || strcmp(ext, ".WEBM") == 0 ||
			strcmp(ext, ".tta") == 0 || strcmp(ext, ".TTA") == 0 ||
			strcmp(ext, ".wma") == 0 || strcmp(ext, ".WMA") == 0
		)
		) codec = FFMPEG;

	if (codec == UNKNOWN && ext != NULL && (
			strcmp(ext, ".xm") == 0 || strcmp(ext, ".XM") == 0 ||
			strcmp(ext, ".s3m") == 0 || strcmp(ext, ".S3M") == 0 ||
			strcmp(ext, ".it") == 0 || strcmp(ext, ".IT") == 0 ||
			strcmp(ext, ".mptm") == 0 || strcmp(ext, ".MPTM") == 0 ||
			strcmp(ext, ".mod") == 0 || strcmp(ext, ".MOD") == 0 ||
			strcmp(ext, ".umx") == 0 || strcmp(ext, ".UMX") == 0 ||
			strcmp(ext, ".okt") == 0 || strcmp(ext, ".OKT") == 0 ||
			strcmp(ext, ".mtm") == 0 || strcmp(ext, ".MTM") == 0 ||
			strcmp(ext, ".far") == 0 || strcmp(ext, ".FAR") == 0 ||
			strcmp(ext, ".wow") == 0 || strcmp(ext, ".WOW") == 0 ||
			strcmp(ext, ".dmf") == 0 || strcmp(ext, ".DMF") == 0 ||
			strcmp(ext, ".med") == 0 || strcmp(ext, ".MED") == 0 ||
			strcmp(ext, ".md2") == 0 || strcmp(ext, ".MD2") == 0 ||
			strcmp(ext, ".ult") == 0 || strcmp(ext, ".ULT") == 0 ||
			strcmp(ext, ".669") == 0
		)
			) codec = MPT;

	if (codec == UNKNOWN && ext != NULL && (
				strcmp(ext, ".spc") == 0 || strcmp(ext, ".SPC") == 0 ||
				strcmp(ext, ".ay") == 0 || strcmp(ext, ".AY") == 0 ||
				strcmp(ext, ".gbs") == 0 || strcmp(ext, ".GBS") == 0 ||
				strcmp(ext, ".gym") == 0 || strcmp(ext, ".GYM") == 0 ||
				strcmp(ext, ".hes") == 0 || strcmp(ext, ".HES") == 0 ||
				strcmp(ext, ".kss") == 0 || strcmp(ext, ".KSS") == 0 ||
				strcmp(ext, ".nsf") == 0 || strcmp(ext, ".NSF") == 0 ||
				strcmp(ext, ".nsfe") == 0 || strcmp(ext, ".NSFE") == 0 ||
				strcmp(ext, ".sap") == 0 || strcmp(ext, ".SAP") == 0 ||
				strcmp(ext, ".vgm") == 0 || strcmp(ext, ".VGM") == 0 ||
				strcmp(ext, ".vgz") == 0 || strcmp(ext, ".VGZ") == 0
				)
			) codec = GME;

	if (codec == UNKNOWN && ext != NULL) {
		if (strcmp(ext, ".flac") == 0 || strcmp(ext, ".FLAC") == 0) {
			codec = FLAC;
		}
		if (strcmp(ext, ".mp3") == 0 || strcmp(ext, ".MP3") == 0) {
			codec = MPG;
		}
		if (strcmp(ext, ".ogg") == 0 || strcmp(ext, ".OGG") == 0 ||
			strcmp(ext, ".oga") == 0 || strcmp(ext, ".OGA") == 0) {
			codec = VORBIS;
		}
		if (strcmp(ext, ".opus") == 0 || strcmp(ext, ".OPUS") == 0) {
			codec = OPUS;
		}
		if (strcmp(ext, ".wv") == 0 || strcmp(ext, ".WV") == 0) {
			codec = WAVPACK;
		}
	}

	if (codec == UNKNOWN || config_always_ffmpeg == 1) {
		codec = FFMPEG;
		log_msg(LOG_INFO, "pa: Decode using FFmpeg\n");
	}

	if (codec == FLAC) {
		// Walk the metadata block headers to find where the audio frames
		// start, so the UI can show the metadata region (embedded art can
		// be large). Only the 4 byte headers are read; block bodies are
		// skipped over.
		int64_t p = stream_meta_end + 4;  // past any ID3 tag and the fLaC marker
		unsigned char bh[4];
		for (int i = 0; i < 64; i++) {
			if (is_net && p > (int64_t) BS_FORWARD_GAP) {
				// Reading the next header would need a new range request;
				// this position is already at/near the end of the metadata
				stream_meta_end = p;
				break;
			}
			if (bs_seek_abs(p) != 0 || bs_read_exact(bh, 4) != 4) break;
			int64_t block_len = ((int64_t) bh[1] << 16) | ((int64_t) bh[2] << 8) | (int64_t) bh[3];
			p += 4 + block_len;
			if (bh[0] & 0x80) {  // last-metadata-block flag
				stream_meta_end = p;
				break;
			}
		}
		bs_seek_abs(0);
	}

	// Start decoders
	if (codec == FFMPEG) {
		// FFmpeg reads files and URLs itself
		bs_close();
		start_ffmpeg(loaded_target_file, load_target_seek);
		load_target_seek = 0;
		pthread_mutex_lock(&buffer_mutex);
		if (old_sample_rate != sample_rate_src) {
			src_reset(src);
		}
		pthread_mutex_unlock(&buffer_mutex);
		if (decoder_allocated == 0) return 1;
		return 0;
	}

	if (codec == GME) {
		sample_rate_src = 48000;
		if (is_net) {
			int64_t data_size = 0;
			unsigned char *data = bs_read_all(&data_size);
			bs_close();
			if (data == NULL) {
				log_msg(LOG_ERROR, "pa: Failed to read GME stream");
				return 1;
			}
			gme_err_t gme_error = gme_open_data(data, (long) data_size, &emu, (long) sample_rate_src);
			free(data);
			if (gme_error != NULL) {
				log_msg(LOG_ERROR, "pa: GME: %s", gme_error);
				return 1;
			}
		} else {
			bs_close();
			gme_open_file(loaded_target_file, &emu, (long) sample_rate_src);
		}
		gme_start_track(emu, subtrack);

		if (load_target_seek > 0) gme_seek(emu, (long) load_target_seek);

		if (old_sample_rate != sample_rate_src) {
			src_reset(src);
		}

		decoder_allocated = 1;

		return 0;
	}

	if (codec == MPT) {
		if (is_net) {
			int64_t data_size = 0;
			unsigned char *data = bs_read_all(&data_size);
			bs_close();
			if (data == NULL) {
				log_msg(LOG_ERROR, "pa: Failed to read MPT stream");
				return 1;
			}
			mod = openmpt_module_create_from_memory2(data, (size_t) data_size, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
			free(data);
		} else {
			bs_close();
			mod_file = uni_fopen(loaded_target_file);
			if (mod_file == NULL) {
				log_msg(LOG_ERROR, "pa: Error opening MPT file: %s", strerror(errno));
				return 1;
			}
			mod = openmpt_module_create2(openmpt_stream_get_file_callbacks2(), mod_file, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
			fclose(mod_file);
		}
		src_channels = 2;

		if (mod == NULL) {
			log_msg(LOG_INFO, "pa: Error creating MPT modules");
			return 1;
		}
		pthread_mutex_lock(&buffer_mutex);
		sample_rate_src = 48000;
		current_length_count = openmpt_module_get_duration_seconds(mod) * 48000;

		if (old_sample_rate != sample_rate_src) {
			src_reset(src);
		}

		if (load_target_seek > 0) {
			// log_msg(LOG_INFO, "pa: Start at position %d", load_target_seek);
			openmpt_module_set_position_seconds(mod, load_target_seek / 1000.0);
			reset_set_value = 48000 * (load_target_seek / 1000.0);
			samples_decoded = reset_set_value * 2;
			reset_set = true;
			reset_set_byte = high;
			load_target_seek = 0;
		}
		pthread_mutex_unlock(&buffer_mutex);
		decoder_allocated = 1;

		return 0;
	}


	switch (codec) {
		// Unlock the output thread mutex cause loading could take a while?..
		// and we dont wanna interrupt the output for too long.
		//
		case WAVE:
			bs_close();
			if (wave_open(loaded_target_file) != 0) return 1;
			if (load_target_seek > 0) {
				wave_seek((int) wave_samplerate * (load_target_seek / 1000.0));
			}
			pthread_mutex_lock(&buffer_mutex);
			if (old_sample_rate != sample_rate_src) {
				src_reset(src);
			}

			if (load_target_seek > 0) {
				reset_set_value = (int) wave_samplerate * (load_target_seek / 1000.0);
				reset_set = true;
				reset_set_byte = high;
				load_target_seek = 0;
			}
			pthread_mutex_unlock(&buffer_mutex);
			decoder_allocated = 1;
			return 0;

		case OPUS:
			opus_dec = op_open_callbacks(
				&bs,
				bs_seekable() ? &bs_op_callbacks : &bs_op_callbacks_unseekable,
				NULL, 0, &e);
			decoder_allocated = 1;

			if (e != 0) {
				log_msg(LOG_ERROR, "pa: Error reading ogg file (expecting opus)");
				log_msg(LOG_ERROR, "pa: %d", e);
				log_msg(LOG_ERROR, "pa: %s", loaded_target_file);
			}

			if (e == 0) {
				pthread_mutex_lock(&buffer_mutex);

				sample_rate_src = 48000;
				src_channels = op_channel_count(opus_dec, -1);

				if (old_sample_rate != sample_rate_src) {
					src_reset(src);
				}

				current_length_count = op_pcm_total(opus_dec, -1);

				if (load_target_seek > 0) {
					// log_msg(LOG_INFO, "pa: Start at position %d", load_target_seek);
					op_pcm_seek(opus_dec, (int) 48000 * (load_target_seek / 1000.0));
					reset_set_value = op_raw_tell(opus_dec);
					samples_decoded = reset_set_value * 2;
					reset_set = true;
					reset_set_byte = high;
					load_target_seek = 0;
				}
				pthread_mutex_unlock(&buffer_mutex);
				return 0;
			} else {
				decoder_allocated = 0;
				return 1;
			}

			break;
		case VORBIS:
			e = ov_open_callbacks(&bs, &vf, NULL, 0, bs_seekable() ? bs_ov_cb : bs_ov_cb_unseekable);
			decoder_allocated = 1;
			if (e != 0) {
				log_msg(LOG_ERROR, "pa: Error reading ogg file (expecting vorbis)");
				decoder_allocated = 0;

				return 1;
			} else {

				vi = *ov_info(&vf, -1);

				pthread_mutex_lock(&buffer_mutex);
				//log_msg(LOG_INFO, "pa: Vorbis samplerate is %lu", vi.rate);

				sample_rate_src = vi.rate;
				src_channels = vi.channels;

				if (old_sample_rate != sample_rate_src) {
					src_reset(src);
				}

				current_length_count = ov_pcm_total(&vf, -1);

				if (load_target_seek > 0) {
					//log_msg(LOG_INFO, "pa: Start at position %d", load_target_seek);
					ov_pcm_seek(&vf, (ogg_int64_t) vi.rate * (load_target_seek / 1000.0));
					reset_set_value = vi.rate * (load_target_seek / 1000.0); // op_pcm_tell(opus_dec); that segfaults?
					//reset_set_value = 0;
					reset_set = true;
					reset_set_byte = high;
					load_target_seek = 0;
				}
				pthread_mutex_unlock(&buffer_mutex);
				return 0;

			}

			break;
		case FLAC:
			if (FLAC__stream_decoder_init_stream(
					dec,
					&bs_flac_read,
					&bs_flac_seek,
					&bs_flac_tell,
					&bs_flac_length,
					&bs_flac_eof,
					&f_write,
					NULL, //&f_meta,
					&f_err,
					0) == FLAC__STREAM_DECODER_INIT_STATUS_OK) {

				decoder_allocated = 1;
				flac_got_rate = 0;

				return 0;

			} else {
				log_msg(LOG_ERROR, "pa: Error initialising FLAC decoder");
				return 1;
			}

			break;

		case WAVPACK: {
			char wv_error[80] = "";
			if (is_net) {
				wpc = WavpackOpenFileInputEx64(&bs_wv_reader, &bs, NULL, wv_error, OPEN_2CH_MAX, 0);
			} else {
				// Keep the path based open for local files so the .wvc
				// correction file keeps working
				bs_close();
				wpc = WavpackOpenFileInput(loaded_target_file, wv_error, OPEN_WVC | OPEN_2CH_MAX, 0);
			}
			if (wpc == NULL) {
				log_msg(LOG_ERROR, "pa: Error loading wavpak file (%s)", wv_error);
				return 1;
			}
			src_channels = WavpackGetReducedChannels(wpc);
			sample_rate_src = WavpackGetSampleRate(wpc);
			if (old_sample_rate != sample_rate_src) {
				src_reset(src);
			}
			wp_bit = WavpackGetBitsPerSample(wpc);
			wp_float = 0;
			if (WavpackGetMode(wpc) & MODE_FLOAT) {
				wp_float = 1;
				if (wp_bit != 32) {
					log_msg(LOG_ERROR, "pa: wavpak float mode only supported for 32-bit");
					WavpackCloseFile(wpc);
					return 1;
				}
			} else {
				if (! (wp_bit == 16 || wp_bit == 24 || wp_bit == 32)) {
					log_msg(LOG_ERROR, "pa: wavpak bit depth not supported");
					WavpackCloseFile(wpc);
					return 1;
				}
			}

			current_length_count = WavpackGetNumSamples(wpc);
			decoder_allocated = 1;
			return 0;
		}

		case MPG: {
			int ret = mpg123_open_handle(mh, &bs);
			if (ret != MPG123_OK) {
				log_msg(
					LOG_ERROR,
					"pa: mpg123_open failed for '%s': %s",
					loaded_target_file,
					mpg123_strerror(mh)
				);
				return 1;
			}
			decoder_allocated = 1;

			mpg123_getformat(mh, &rate, &channels, &encoding);
			// Scanning reads the whole file for an exact length, so only do
			// it when the data is already on disk
			if (!is_net) mpg123_scan(mh);
			//log_msg(LOG_INFO, "pa: %lu. / %d. / %d", rate, channels, encoding);

			pthread_mutex_lock(&buffer_mutex);

			sample_rate_src = rate;
			src_channels = channels;
			if (old_sample_rate != sample_rate_src) {
				src_reset(src);
			}
			off_t mpg_length = mpg123_length(mh);
			current_length_count = mpg_length > 0 ? (unsigned int) mpg_length : 0;

			if (encoding == MPG123_ENC_SIGNED_16) {

				if (load_target_seek > 0) {
					//log_msg(LOG_INFO, "pa: Start at position %d", load_target_seek);
					mpg123_seek(mh, (int) rate * (load_target_seek / 1000.0), SEEK_SET);
					reset_set_value = mpg123_tell(mh);
					reset_set = true;
					reset_set_byte = high;
					load_target_seek = 0;
				}
				pthread_mutex_unlock(&buffer_mutex);
				return 0;

			} else {
				// Pretty much every MP3 ive tried is S16, so we might not have
				// to worry about this.
				log_msg(LOG_ERROR, "pa: encoding format not supported!");
				pthread_mutex_unlock(&buffer_mutex);
				return 1;
			}

			break;
		}
	}
	return 1;
}

int load_next() {
	stream_loading = 1;
	int r = load_next_inner();
	stream_loading = 0;
	return r;
}

void end() {
	// Call when buffer has run out or otherwise ready to stop and flush
	stop_decoder();
	pthread_mutex_lock(&buffer_mutex);
	mode = STOPPED;
	command = NONE;
	buff_reset();
	buffering = 0;
	pthread_mutex_unlock(&buffer_mutex);
}

void decoder_eos() {
	// Call once current decode steam has run out
	//log_msg(LOG_INFO, "pa: End of stream");
	if (next_ready == 1) {
		//log_msg(LOG_INFO, "pa: Read next gapless");
		int result = load_next();
		if (result == 1) {
			result_status = FAILURE;
		}
		pthread_mutex_lock(&buffer_mutex);
		next_ready = 0;
		reset_set_value = 0;
		reset_set = true;
		reset_set_byte = high;
		pthread_mutex_unlock(&buffer_mutex);

	} else mode = ENDING;
}

void stop_out() {
	if (out_thread_running) {
		called_to_stop_device = true;
		#ifdef MINI
			ma_device_stop(&device);
		#endif
		out_thread_running = false;
	}
	disconnect_pulse();
}

void start_out() {
	if (!pulse_connected) connect_pulse();

	if (!out_thread_running) {
		called_to_stop_device = false;
		device_stopped = false;
		#ifdef MINI
			ma_device_start(&device);
		#endif
		out_thread_running = true;

		#ifdef PIPE

		#endif
	}
}

void pump_decode() {
	// Here we get data from the decoders to fill the main buffer

	bool reconnect = false;
	if (config_resample == 0 && sample_rate_out != sample_rate_src) {
		if (get_buff_fill() > 0) {
			return;
		}
		log_msg(LOG_ERROR, "ph: Pump wrong samplerate");

		#ifdef MINI
			stop_out();
			fade_fill = 0;
			fade_position = 0;
			reset_set_value = 0;
			buff_reset();
			reconnect = true;
		#endif

		#ifdef PIPE
			fade_fill = 0;
			fade_position = 0;
			reset_set_value = 0;
			buff_reset();
			pipe_set_samplerate = sample_rate_src;
			sample_rate_out = pipe_set_samplerate;
			pw_loop_invoke(pw_main_loop_get_loop(loop), pipe_update, SPA_ID_INVALID, NULL, 0, true, NULL);
		#endif
	}

	if (codec == WAVE) {
		int result;
		pthread_mutex_lock(&buffer_mutex);
		result = wave_decode(1024 * 2);
		pthread_mutex_unlock(&buffer_mutex);
		if (result == 1) decoder_eos();

	} else if (codec == MPT) {
		int count;
		count = openmpt_module_read_interleaved_stereo(mod, 48000, 4096, temp16l);
		if (count == 0) {
			decoder_eos();
		} else {
			pthread_mutex_lock(&buffer_mutex);
			read_to_buffer_s16int(temp16l, count * 2);
			samples_decoded += count * 2;
			pthread_mutex_unlock(&buffer_mutex);
		}

	} else if (codec == GME) {
		if (emu != NULL) {
			gme_play(emu, 1024, temp16l);

			pthread_mutex_lock(&buffer_mutex);
			read_to_buffer_s16int(temp16l, 1024);
			samples_decoded += 1024;
			pthread_mutex_unlock(&buffer_mutex);

			if (gme_track_ended(emu)) decoder_eos();
		}


	} else if (codec == FLAC) {
		// FLAC decoding
		if (dec != NULL) {
			switch (FLAC__stream_decoder_get_state(dec)) {
				case FLAC__STREAM_DECODER_END_OF_STREAM:
				// Fatal states; process_single() would make no further
				// progress (aborted happens when a stream is cancelled)
				case FLAC__STREAM_DECODER_ABORTED:
				case FLAC__STREAM_DECODER_SEEK_ERROR:
				case FLAC__STREAM_DECODER_MEMORY_ALLOCATION_ERROR:
					decoder_eos();
					break;

				default:
					FLAC__stream_decoder_process_single(dec);

			}

			if (load_target_seek > 0 && flac_got_rate == 1) {
				//log_msg(LOG_INFO, "pa: Set start position %d", load_target_seek);

				FLAC__stream_decoder_seek_absolute(dec, (int) sample_rate_src * (load_target_seek / 1000.0));
				pthread_mutex_lock(&buffer_mutex);
				reset_set = true;
				reset_set_byte = high;
				load_target_seek = 0;
				pthread_mutex_unlock(&buffer_mutex);
			}
		} else decoder_eos();

	} else if (codec == OPUS) {
		if (opus_dec != NULL) {
			int done;

			if (src_channels == 1) {
				done = op_read(opus_dec, opus_buffer, 4096, NULL);
			}
			else {
				int frames = op_read_stereo(opus_dec, opus_buffer, 1024 * 2);
				if (frames < 0) done = frames;
				else done = frames * 2;
			}

			if (done > 0) {
				pthread_mutex_lock(&buffer_mutex);
				read_to_buffer_s16int(opus_buffer, done);
				samples_decoded += done;
				pthread_mutex_unlock(&buffer_mutex);
			}
			if (done == 0) {

				// Check if file was appended to... (a local cache file that
				// is still downloading). The stream producer re-stats on EOF,
				// so a grown bs.file_size signals more data appeared.
				if (bs.active && !bs.net && load_file_size != (off_t) bs_length()) {
					log_msg(LOG_WARNING, "pa: Ogg file size changed!");
					int e = 0;
					bs_seek_abs(0);
					OggOpusFile *new_opus_dec = op_open_callbacks(&bs, &bs_op_callbacks, NULL, 0, &e);
					if (new_opus_dec != NULL && e == 0) {
						op_free(opus_dec);
						opus_dec = new_opus_dec;
						// Reset the size baseline so true EOF can flow to decoder_eos().
						load_file_size = (off_t) bs_length();
						if (op_pcm_seek(opus_dec, samples_decoded / 2) == 0) {
							return;
						}
						log_msg(LOG_WARNING, "pa: Failed to seek reopened Opus stream");
					} else {
						log_msg(LOG_WARNING, "pa: Failed to reopen appended Opus stream (err %d)", e);
					}
				}

				decoder_eos();
			} else if (done < 0) {
				log_msg(LOG_ERROR, "pa: Opus decode error: %d", done);
				decoder_eos();
			}
		}


	} else if (codec == VORBIS) {
		unsigned int done;
		int stream;
		done = ov_read(&vf, parse_buffer, sizeof(parse_buffer), 0, 2, 1, &stream);

		if (done > 0) {
			pthread_mutex_lock(&buffer_mutex);

			int bytes_per_frame = src_channels * 2;
			int frames = done / bytes_per_frame;

			int16_t stereo_buf[frames * 2];
			const unsigned char *p = (const unsigned char *)parse_buffer;

			for (int f = 0; f < frames; f++) {
				float l = 0.0f;
				float r = 0.0f;

				if (src_channels == 1) {
					l = r = s16_to_float(p);
				}
				else if (src_channels == 2) {
					l = s16_to_float(p + 0); // FL
					r = s16_to_float(p + 2); // FR
				}
				else if (src_channels == 6) {
					float fl = s16_to_float(p + 0);
					float c  = s16_to_float(p + 2);
					float fr = s16_to_float(p + 4);
					float sl = s16_to_float(p + 6);
					float sr = s16_to_float(p + 8);
					// float lfe = s16_to_float(p + 10); // ignore or very low

					l = fl + 0.707f * c + 0.707f * sl;
					r = fr + 0.707f * c + 0.707f * sr;
				}
				else {
					// Fallback: average pairs
					for (int ch = 0; ch < src_channels; ch++) {
						float v = s16_to_float(p + ch * 2);
						if (ch & 1) r += v;
						else        l += v;
					}
					float norm = 1.0f / (src_channels / 2.0f);
					l *= norm;
					r *= norm;
				}

				stereo_buf[f * 2 + 0] = (int16_t)(l * 32767.0f);
				stereo_buf[f * 2 + 1] = (int16_t)(r * 32767.0f);

				p += bytes_per_frame;
			}

			read_to_buffer_char16((char *)stereo_buf, frames * 4);
			pthread_mutex_unlock(&buffer_mutex);
		}
		if (done == 0) decoder_eos();

	} else if (codec == WAVPACK) {
		if (wpc != NULL) {
			int samples;
			int32_t buffer[4 * 1024 * 2];
			samples = WavpackUnpackSamples(wpc, buffer, 1024);
			if (samples == 0) {
				// End of file or unrecoverable error
				decoder_eos();
			} else if (wp_float) {
				read_to_buffer_float32_fs(buffer, samples);
			} else if (wp_bit == 16) {
				read_to_buffer_16in32_fs(buffer, samples);
			} else if (wp_bit == 24) {
				read_to_buffer_24in32_fs(buffer, samples);
			} else if (wp_bit == 32) {
				read_to_buffer_32in32_fs(buffer, samples);
			}
			samples_decoded += samples;
		} else decoder_eos();

	} else if (codec == MPG) {
		// MP3 decoding
		if (mh != NULL) {
			size_t done;

			mpg123_read(mh, parse_buffer, 2048 * 2, &done);

			pthread_mutex_lock(&buffer_mutex);
			read_to_buffer_char16(parse_buffer, done);
			pthread_mutex_unlock(&buffer_mutex);
			if (done == 0) decoder_eos();
		}
	} else if (codec == FFMPEG) {

		int b = 0;
		if (ff_read != NULL) b = ff_read(ffm_buffer, 2048);
		else {
			log_msg(LOG_WARNING, "pa: FFmpeg read callback is NULL");
			decoder_eos();
			return;
		}

		if (b % 4 != 0) {
			log_msg(LOG_WARNING, "pa: Uneven data");
			decoder_eos();
			return;
		}

		pthread_mutex_lock(&buffer_mutex);
		read_to_buffer_char16(ffm_buffer, b);
		pthread_mutex_unlock(&buffer_mutex);
		if (b == 0) {
			log_msg(LOG_INFO, "pa: FFmpeg has finished");
			decoder_eos();
		}
	}

	if (reconnect && sample_rate_src > 0) start_out();
}




// ---------------------------------------------------------------------------------------
// Main loop

int main_running = 0;

void *main_loop(void *thread_id) {

	rbuf = (kiss_fft_scalar*)malloc(sizeof(kiss_fft_scalar) * 2048 );
	if (rbuf == NULL) {
		log_msg(LOG_ERROR, "pa: Error allocating memory for rbuf");
		return thread_id;
	}
	cbuf = (kiss_fft_cpx*)malloc(sizeof(kiss_fft_cpx) * (2048/2+1) );
	if (cbuf == NULL) {
		log_msg(LOG_ERROR, "pa: Error allocating memory for cbuf");
		free(rbuf);
		return thread_id;
	}
	ffta = kiss_fftr_alloc(2048 ,0 ,0,0 );
	if (ffta == NULL) {
		log_msg(LOG_ERROR, "pa: Error allocating memory for ffta");
		free(rbuf);
		free(cbuf);
		return thread_id;
	}

	int error = 0;

	int load_result = 0;
	bool using_fade = false;
	int load_prepared = 0;     // target loaded, transition cutover pending
	int preload_waited_ms = 0;

	// SRC ----------------------------

	src = src_new(config_resample_quality, 2, &error);
	if (src == NULL) {
		log_msg(LOG_ERROR, "pa: Error creating SRC state");
		free(rbuf);
		free(cbuf);
		kiss_fftr_free(ffta);
		return thread_id;
	}
	// log_msg(LOG_ERROR, "pa: SRC error code %d", error);
	error = 0;

	// MP3 decoder --------------------------------------------------------------

	mpg123_init();
	mh = mpg123_new(NULL, &error);
	if (!mh) {
		log_msg(LOG_ERROR, "pa: mpg123_new failed: %d", error);
		return thread_id;
	}
	mpg123_param(mh, MPG123_ADD_FLAGS, MPG123_QUIET | MPG123_SKIP_ID3V2, 0);
	mpg123_param(mh, MPG123_RESYNC_LIMIT, 10000, 0);
	mpg123_replace_reader_handle(mh, &bs_mpg_read, &bs_mpg_lseek, NULL);

	// FLAC decoder ----------------------------------------------------------------

	dec = FLAC__stream_decoder_new();

	// ---------------------------------------------

	// PIPEWIRE -----------
	#ifdef PIPE
		log_msg(LOG_INFO, "Start pipewire thread...");
		enum_done = 0;
		if (pthread_create(&pw_thread, NULL, pipewire_main_loop_thread, NULL) != 0) {
				log_msg(LOG_ERROR, "Failed to create Pipewire main loop thread");
				return thread_id;
		}
		log_msg(LOG_INFO, "Done Pipewire prep, wait for ready event...");
		while (enum_done != 1) {
			usleep(10000);
		}
		log_msg(LOG_INFO, "Pipewire load done.");
	#endif
	//int test1 = 0;
	// Main loop ---------------------------------------------------------------
	while (true) {

//		test1++;
//		if (test1 > 650) {
//			log_msg(LOG_INFO, "pa: Status: mode %d, command %d, buffer %d, gate %f", mode, command, get_buff_fill(), gate);
//			test1 = 0;
//		}

		if (device_stopped && !called_to_stop_device && !signaled_device_unavailable) {
			log_msg(LOG_WARNING, "Device was unplugged or became unavailable.");
			on_device_unavailable();
			signaled_device_unavailable = true;
		}
		#ifdef PIPE
			if (pw_need_restart) {
				pw_need_restart = false;

				// Wait for pw thread to actually stop
				if (pw_running) {
					// loop will quit soon because we called pw_main_loop_quit()
					while (pw_running) usleep(10000);
				}

				// Join old thread (safe if it already exited)
				pthread_join(pw_thread, NULL);

				// Reset enumeration readiness
				enum_done = 0;

				// Start fresh thread
				if (pthread_create(&pw_thread, NULL, pipewire_main_loop_thread, NULL) != 0) {
					log_msg(LOG_ERROR, "Failed to restart PipeWire thread");
				} else {
					// Wait for new core sync
					while (enum_done != 1) usleep(10000);
				}
				if (mode == PLAYING || mode == RAMP_DOWN) {
					log_msg(LOG_ERROR, "Reconnecting output after PipeWire restart");
					start_out();
				}
			}
		#endif

		if (command != NONE) {
			if (command == EXIT) {
				break;
			}
			switch (command) {

				case PAUSE:
					if (mode == PLAYING || (mode == RAMP_DOWN && gate == 0)) {
						mode = PAUSED;
						//stop_out();
						command = NONE;
					}
					break;

				case RESUME:
					if (mode == PAUSED) {
						start_out();
						mode = PLAYING;
					}
					command = NONE;
					break;

				case STOP:
					if (mode == STOPPED) {
						command = NONE;
					} else if (mode == PLAYING || mode == ENDING) {
						// ENDING can also be reached when a stream is
						// cancelled; ramp down rather than draining it all
						mode = RAMP_DOWN;
					}
					if ((mode == RAMP_DOWN && (gate == 0 || get_buff_fill() == 0)) || mode == PAUSED) {
						end();
					}
					break;

				case START:
				case LOAD:
					// Load/prepare the new target first; already decoded
					// audio of the current track keeps playing out of the
					// main buffer in the meantime
					if (!load_prepared) {
						load_result = load_next();
						load_prepared = 1;
						preload_waited_ms = 0;
					}

					// For network streams, hold the transition until enough
					// data is buffered (or 1.5s passes) so fast connections
					// switch tracks without an audible gap
					if (load_result == 0 && mode == PLAYING && get_buff_fill() > 0
							&& preload_waited_ms < 1500 && !bs_decode_ready()) {
						preload_waited_ms += 5;
						break;
					}

					if (command == START) {
						if (mode == PLAYING) {
							mode = RAMP_DOWN;
						}
						if (mode == RAMP_DOWN && gate == 0) {
							command = LOAD;
						} else break;
					}

					// Prepare for a crossfade if enabled and suitable
					using_fade = false;
					if (load_result == 0 && config_fade_jump == 1 && mode == PLAYING) {
						pthread_mutex_lock(&buffer_mutex);
						if (fade_fill > 0) {
							log_msg(LOG_WARNING, "pa: Fade already in progress");
						}
						int l = current_sample_rate * (config_fade_duration / 1000.0);
						int reserve = 0; //current_sample_rate / 10.0;
						if (get_buff_fill() > l) {
							int i = 0;
							int p = low + reserve;
							i = 0;

							while (i < l) {
								fadefl[i] = bfl[p]; //buffl[(buff_base + i + reserve) % BUFF_SIZE];
								fadefr[i] = bfr[p]; //buffr[(buff_base + i + reserve) % BUFF_SIZE];
								i++;
								p++;
								if (p >= watermark) {
									p = 0;
								}
							}
							fade_position = 0;
							//position_count = 0;
							fade_fill = l;
							high = low + reserve;
							using_fade = true;
							fade_lockout = false;
							fade_mini = 0.0;

							reset_set_byte = p;
							if (!reset_set) {
								reset_set = true;
								reset_set_value = 0;
							}

						}
						pthread_mutex_unlock(&buffer_mutex);
					}

					if (!using_fade) {
						// Jump immediately
						//log_msg(LOG_INFO, "ph: Jump");
						position_count = 0;
						buff_reset();
						gate = 0;
						sample_change_byte = 0;
						reset_set = true;
						reset_set_byte = 0;
						reset_set_value = 0;
					}

					if (load_result == 0) {
						mode = PLAYING;
						result_status = SUCCESS;
						start_out();
						command = NONE;
					} else {
						log_msg(LOG_ERROR, "ph: Load file failed");
						stop_decoder();  // release any half opened stream
						result_status = FAILURE;
						command = NONE;
						mode = STOPPED;
					}
					load_prepared = 0;

					break;

			} // end switch
		} // end if none


		if (command == SEEK) {
			//log_msg(LOG_INFO, "command is %d, mode is %d, gate is %f, pulse_connected is %d, pw_running is %d", command, mode, gate, pulse_connected, pw_running);
			#ifdef PIPE
				if (!pulse_connected || !pw_running) {
					// No callback means gate won't hit 0 unless we force progress.
					gate = 0;
				}
			#endif
			if (mode == PLAYING) {
				mode = RAMP_DOWN;

				//if (want_sample_rate > 0) decode_seek(seek_request_ms, want_sample_rate);
				decode_seek(seek_request_ms, sample_rate_src);
				reset_set = false;

				//if (want_sample_rate > 0) position_count = want_sample_rate * (seek_request_ms / 1000.0);
				position_count = current_sample_rate * (seek_request_ms / 1000.0);

			} else if (mode == PAUSED) {
				//if (want_sample_rate > 0) decode_seek(seek_request_ms, want_sample_rate);
				decode_seek(seek_request_ms, current_sample_rate);

				//if (want_sample_rate > 0) position_count = want_sample_rate * (seek_request_ms / 1000.0);
				position_count = current_sample_rate * (seek_request_ms / 1000.0);

				pthread_mutex_lock(&buffer_mutex);

				buff_reset();

				command = NONE;

				pthread_mutex_unlock(&buffer_mutex);

			} else if (mode != RAMP_DOWN) {
				log_msg(LOG_CRITICAL, "pa: fixme - cannot seek at this time");
				//log_msg(LOG_INFO, "command is %d, mode is %d, gate is %f", command, mode, gate);
				command = NONE;
			}

			if (mode == RAMP_DOWN && gate == 0) {
				pthread_mutex_lock(&buffer_mutex);
				buff_reset();
				mode = PLAYING;
				command = NONE;
				pthread_mutex_unlock(&buffer_mutex);

			}
		}

		// Refill the buffer. Held off while a loaded track waits for its
		// transition cutover, the buffer still holds the previous track then.
		if (mode == PLAYING && codec != FEED && !load_prepared) {
			int idle_pumps = 0;
			while (get_buff_fill() < BUFF_SAFE && mode != ENDING) {
				// Wait for enough network data so decoding can't block
				// the loop for long; commands stay responsive meanwhile
				if (!bs_decode_ready()) break;
				int before = get_buff_fill();
				pump_decode();
				// Headers/metadata produce no PCM, but a decoder that makes
				// no progress at all must not starve command processing
				if (get_buff_fill() == before) {
					idle_pumps++;
					if (idle_pumps > 500) break;
				} else idle_pumps = 0;
			}
		}

		if (mode == ENDING && get_buff_fill() == 0) {
			//log_msg(LOG_INFO, "pa: Buffer ran out at end of track");
			end();
		}
		if (mode == ENDING && next_ready == 1) {
			//log_msg(LOG_INFO, "pa: Next registered while buffer was draining");
			//log_msg(LOG_INFO, "pa: -- remaining was %d", get_buff_fill());
			mode = PLAYING;
		}

		usleep(5000);
	}

	//log_msg(LOG_INFO, "pa: Cleanup and exit");

	pthread_mutex_lock(&buffer_mutex);

	main_running = 0;

	position_count = 0;
	buff_reset();

	//disconnect_pulse();
	if (dec != NULL) FLAC__stream_decoder_finish(dec);
	FLAC__stream_decoder_delete(dec);
	mpg123_delete(mh);
	src_delete(src);
	free(rbuf);
	free(cbuf);
	kiss_fftr_free(ffta);

	pthread_mutex_unlock(&buffer_mutex);

	stop_out();
	disconnect_pulse();
	bs_close();
	free(bs.buf);
	bs.buf = NULL;
	bs.capacity = 0;
	#ifdef MINI
		if (context_allocated == 1) {
			ma_context_uninit(&context);
			context_allocated = 0;
		}
	#endif

	#ifdef PIPE
		pw_loop_invoke(pw_main_loop_get_loop(loop), pipe_exit, SPA_ID_INVALID, NULL, 0, true, NULL);
	#endif
	command = NONE;
	log_msg(LOG_INFO, "Exit PHAzOR");
	return thread_id;
}


// ---------------------------------------------------------------------------------------
// Begin exported functions

EXPORT int scan_devices() {
	#ifdef MINI
		if (initiate_ma_context() == -1) return -1;
		result = ma_context_get_devices(&context, &pPlaybackDeviceInfos, &playbackDeviceCount, NULL, NULL);
		if (result != MA_SUCCESS) {
			log_msg(LOG_ERROR, "Failed to retrieve device information.");
			return -2;
		}
		return playbackDeviceCount;
	#endif

	#ifdef PIPE
		while (enum_done != 1) {
			usleep(10000);
		}
		return pipe_devices.device_count;
	#endif
}

EXPORT int init() {
	//log_msg(LOG_INFO, "ph: PHAzOR starting up");
	if (main_running == 0) {
		main_running = 1;
		pthread_t main_thread_id;
		pthread_create(&main_thread_id, NULL, main_loop, NULL);
	} else log_msg(LOG_ERROR, "ph: Cannot init. Main loop already running!");
	return 0;
}

EXPORT int get_status() {
	return mode;
}

EXPORT int get_result() {
	return result_status;
}

EXPORT int start(char *filename, int start_ms, int fade, float rg) {

	// If a previous load is blocked waiting on (network) data, abort it
	// so the command queue keeps moving
	while (command != NONE || stream_loading) {
		if (stream_loading) bs_cancel();
		usleep(1000);
	}

	result_status = WAITING;

	rg_value_want = rg;
	config_fade_jump = fade;

	load_target_seek = start_ms;
	strcpy(load_target_file, filename);
	load_target_net = load_target_net_pending;

	if (mode == PLAYING) {
		if (fade == 1) command = LOAD;
		else command = START;
	} else command = LOAD;

	return 0;
}

EXPORT int next(char *filename, int start_ms, float rg) {

	while (command != NONE) {
		usleep(1000);
	}

	result_status = WAITING;

	if (mode == STOPPED) {
		start(filename, start_ms, 0, rg);
	} else {
		load_target_seek = start_ms;
		strcpy(load_target_file, filename);
		load_target_net = load_target_net_pending;
		rg_value_want = rg;
		next_ready = 1;
	}

	return 0;
}

EXPORT int pause() {
	while (command != NONE) {
		usleep(1000);
	}
	if (mode == PAUSED) return 0;
	if (out_thread_running && (mode == PLAYING || mode == RAMP_DOWN)) {
		mode = RAMP_DOWN;
		command = PAUSE;
	}

	return 0;
}

EXPORT int resume() {
	while (command != NONE) {
		usleep(1000);
	}
	if (mode == PAUSED) {
		gate = 0;
	}
	command = RESUME;
	return 0;
}

EXPORT int stop() {
	// Abort any blocked load, pre-buffer wait or in-flight network
	// transfers immediately
	while (command != NONE || stream_loading) {
		bs_cancel();
		usleep(1000);
	}
	bs_cancel();
	command = STOP;
	return 0;
}

EXPORT void wait_for_command() {
	while (command != NONE) {
		usleep(1000);
	}
}

EXPORT int seek(int ms_absolute, int flag) {
	while (command != NONE) {
		usleep(1000);
	}

	// This is checked on the Python side, but race conditions can happen,
	// so check again
	//if (mode == ENDING || mode == STOPPED) {
	//	log_msg(LOG_INFO, "command is %d, mode is %d, gate is %f, pulse_connected is %d, pw_running is %d", command, mode, gate, pulse_connected, pw_running);
	//	return 1;
	//}
	config_fast_seek = flag;
	seek_request_ms = ms_absolute;
	command = SEEK;

	return 0;
}

EXPORT int set_volume(int percent) {
	volume_want = percent / 100.0;
	volume_on = percent / 100.0;

	return 0;
}

EXPORT int ramp_volume(int percent, int speed) {
	volume_ramp_speed = speed;
	volume_want = percent / 100.0;
	return 0;
}

EXPORT void eq_set_enable(int n) {
	pthread_mutex_lock(&buffer_mutex);
	eq_enabled = (n != 0);
	eq_dirty = true;
	if (!eq_enabled) {
		eq_headroom_db = 0.0f;
		eq_headroom_gain = 1.0f;
		eq_reset_state();
	}
	limiter_reset_state();
	pthread_mutex_unlock(&buffer_mutex);
}

EXPORT void eq_set_band(int band, float gain_db) {
	if (band < 0 || band >= EQ_BAND_COUNT) return;
	if (gain_db > 12.0f) gain_db = 12.0f;
	if (gain_db < -12.0f) gain_db = -12.0f;

	pthread_mutex_lock(&buffer_mutex);
	eq_band_gain_db[band] = gain_db;
	eq_dirty = true;
	pthread_mutex_unlock(&buffer_mutex);
}

EXPORT void eq_reset() {
	pthread_mutex_lock(&buffer_mutex);
	for (int i = 0; i < EQ_BAND_COUNT; i++) {
		eq_band_gain_db[i] = 0.0f;
	}
	eq_dirty = true;
	eq_headroom_db = 0.0f;
	eq_headroom_gain = 1.0f;
	eq_reset_state();
	limiter_reset_state();
	pthread_mutex_unlock(&buffer_mutex);
}

EXPORT int get_position_ms() {
	if (command != START && command != LOAD && !reset_set && current_sample_rate > 0) {
		return (int) ((position_count / (float) current_sample_rate) * 1000.0);
	} else return 0;
}

EXPORT void set_position_ms(int ms) {
	position_count = ((float)(ms / 1000.0)) * current_sample_rate;
}

EXPORT int get_length_ms() {
	if (!reset_set && sample_rate_src > 0 && current_length_count > 0) {
		return (int) ((current_length_count / (float) sample_rate_src) * 1000.0);
	} else return 0;
}

EXPORT void config_set_dev_buffer(int ms) {
	config_dev_buffer = ms;
}

EXPORT void config_set_samplerate(int hz) {
	sample_rate_out = hz;
}

EXPORT void config_set_resample_quality(int n) {
	config_resample_quality = n;
}

EXPORT void config_set_resample(int n) {
	config_resample = n;
}

EXPORT void config_set_always_ffmpeg(int n) {
	config_always_ffmpeg = n;
}

EXPORT void config_set_fade_duration(int ms) {
	if (ms < 200) ms = 200;
	if (ms > 2000) ms = 2000;
	config_fade_duration = ms;
}

EXPORT void config_set_dev_name(char *device) {
	if (device == NULL) {
		strcpy(config_output_sink, "Default");
	} else {
		strcpy(config_output_sink, device);
	}
}

EXPORT void config_set_volume_power(int n) {
	config_volume_power = n;
}

EXPORT void config_set_feed_samplerate(int n) {
	config_feed_samplerate = n;
}

EXPORT void config_set_min_buffer(int n) {
	config_min_buffer = n;
}

EXPORT void config_set_stream_buffer(int mb) {
	if (mb < 4) mb = 4;
	if (mb > 2048) mb = 2048;
	config_stream_buffer_mb = mb;
}

// Mark whether the next start()/next() target is a network track to be
// streamed through the byte stream (as opposed to a radio URL or local file)
EXPORT void set_load_net(int n) {
	load_target_net_pending = n;
}

// Network feeder protocol -----------------------------------------------
// The Python side polls net_generation(); when an active network stream
// exists it fetches net_get_url() with HTTP range requests starting at
// net_want() and pushes data in with net_feed().

EXPORT int net_generation() {
	pthread_mutex_lock(&bs.mut);
	int g = (bs.active && bs.net && !bs.abort && !bs.error) ? bs.generation : -1;
	pthread_mutex_unlock(&bs.mut);
	return g;
}

EXPORT char* net_get_url() {
	pthread_mutex_lock(&bs.mut);
	memcpy(bs_net_url_out, bs_net_url, sizeof(bs_net_url_out));
	pthread_mutex_unlock(&bs.mut);
	return bs_net_url_out;
}

// Returns the next file offset the feeder should supply data from,
// -1 if no data is currently needed (end of file reached),
// -2 if the stream is gone (stop feeding)
EXPORT long long net_want(int gen) {
	pthread_mutex_lock(&bs.mut);
	long long r = -2;
	if (bs.active && bs.net && !bs.abort && !bs.error && gen == bs.generation) {
		if (bs.want_restart) r = (long long) bs.want_offset;
		else if (bs.eof) r = -1;
		else if (bs.file_size >= 0 && bs.win_start + bs.filled >= bs.file_size) r = -1;
		else r = (long long) (bs.win_start + bs.filled);
	}
	pthread_mutex_unlock(&bs.mut);
	return r;
}

// Append data at the given absolute file offset. Returns the number of
// bytes accepted (0 = buffer full, try again shortly), -1 if the stream
// is gone, -2 if the offset no longer matches (re-check net_want)
EXPORT int net_feed(int gen, long long offset, char *data, int len) {
	if (len < 0) return -1;
	pthread_mutex_lock(&bs.mut);
	if (!bs.active || !bs.net || bs.abort || gen != bs.generation) {
		pthread_mutex_unlock(&bs.mut);
		return -1;
	}
	if (bs.want_restart) {
		if (offset == (long long) bs.want_offset) {
			bs_window_reset_locked((int64_t) offset);
			bs.want_restart = false;
		} else {
			pthread_mutex_unlock(&bs.mut);
			return -2;
		}
	} else if (offset != (long long) (bs.win_start + bs.filled)) {
		pthread_mutex_unlock(&bs.mut);
		return -2;
	}
	int64_t space = bs_make_space_locked();
	int64_t n = len < space ? len : space;
	if (n > 0) {
		bs_append_locked((unsigned char *) data, n);
		if (bs.file_size >= 0 && bs.win_start + bs.filled >= bs.file_size) bs.eof = true;
		pthread_cond_broadcast(&bs.cond);
	}
	pthread_mutex_unlock(&bs.mut);
	return (int) n;
}

EXPORT void net_set_size(int gen, long long size) {
	pthread_mutex_lock(&bs.mut);
	if (bs.active && bs.net && gen == bs.generation && size >= 0) {
		bs.file_size = (int64_t) size;
		pthread_cond_broadcast(&bs.cond);
	}
	pthread_mutex_unlock(&bs.mut);
}

EXPORT void net_eof(int gen) {
	pthread_mutex_lock(&bs.mut);
	if (bs.active && bs.net && gen == bs.generation && !bs.want_restart) {
		bs.eof = true;
		// The response ended; if no length was known before, we know it now
		if (bs.file_size < 0) bs.file_size = bs.win_start + bs.filled;
		pthread_cond_broadcast(&bs.cond);
	}
	pthread_mutex_unlock(&bs.mut);
}

// Tell the stream whether the server honours range requests. Must be
// called before the first data is fed so the decoders open appropriately.
EXPORT void net_set_seekable(int gen, int seekable) {
	pthread_mutex_lock(&bs.mut);
	if (bs.active && bs.net && gen == bs.generation) {
		bs.seek_ok = seekable != 0;
	}
	pthread_mutex_unlock(&bs.mut);
}

EXPORT void net_fail(int gen) {
	pthread_mutex_lock(&bs.mut);
	if (bs.active && bs.net && gen == bs.generation) {
		bs.error = true;
		pthread_cond_broadcast(&bs.cond);
	}
	pthread_mutex_unlock(&bs.mut);
}

EXPORT float get_level_peak_l() {
	float peak = peak_l;
	peak_l = 0.0;
	return peak;
}

EXPORT float get_level_peak_r() {
	float peak = peak_r;
	peak_r = 0.0;
	return peak;
}

EXPORT void set_callbacks(void *start, void *read, void *close, void *device_unavailable) {
	ff_start = start;
	ff_read = read;
	ff_close = close;
	on_device_unavailable = device_unavailable;
}

EXPORT char* get_device(int n) {
	#ifdef MINI
		return pPlaybackDeviceInfos[n].name;
	#endif
	#ifdef PIPE
		return pipe_devices.devices[n].description;
	#endif
}

EXPORT int get_spectrum(int n_bins, float* bins) {
	int samples = 2048;
	int base = low;

	int i = 0;
	while (i < samples) {
		if (base >= watermark) {
			base = 0;
		}
		rbuf[i] = bfl[base] * 0.5 * (1 - cos(2*3.1415926*i/samples));
		i++;
		base += 1;
	}

	kiss_fftr( ffta , rbuf , cbuf );

	i = 0;
	while (i < samples / 2) {
		rbuf[i] = sqrt((cbuf[i].r * cbuf[i].r) + (cbuf[i].i * cbuf[i].i));
		i++;
	}

	int b0 = 0;
	for (int x = 0; x < n_bins; x++) {
		float peak = 0;
		int b1 = pow(2, x * 10.0 / (n_bins - 1));
		if (b1 > (samples / 2) - 1) b1 = (samples / 2) - 1;
		if (b1 <= b0) b1 = b0 + 1;
		for (; b0 < b1; b0++) {
			if (peak < rbuf[1 + b0]) peak = rbuf[1 + b0];
		}
		bins[x] = sqrt(peak);
	}

	return 0;
}

EXPORT int is_buffering() {
	if (buffering == 0) return 0;
	return (int) (get_buff_fill() / config_min_buffer * 100.0);
}

// How much decoded audio is waiting in the PCM buffer
EXPORT int get_buffered_ms() {
	if (sample_rate_out <= 0) return 0;
	return (int) ((int64_t) get_buff_fill() * 1000 / sample_rate_out);
}

// Snapshot of the byte stream state, for the in-app console graph.
// Returns whether a stream is active.
EXPORT int get_stream_stats(
		long long *size, long long *start, long long *end, long long *pos,
		long long *meta, int *net, int *eof) {
	pthread_mutex_lock(&bs.mut);
	int active = bs.active ? 1 : 0;
	*size = (long long) bs.file_size;
	*start = (long long) bs.win_start;
	*end = (long long) (bs.win_start + bs.filled);
	*pos = (long long) bs.read_pos;
	*meta = (long long) stream_meta_end;
	*net = bs.net ? 1 : 0;
	*eof = bs.eof ? 1 : 0;
	pthread_mutex_unlock(&bs.mut);
	return active;
}

/* EXPORT int get_latency() { */
/*	return active_latency / 1000; */
/* } */

EXPORT int feed_ready(int request_size) {
	if (mode != STOPPED && high_mark - get_buff_fill() > request_size && codec == FEED) return 1;
	return 0;
}

EXPORT void feed_raw(int len, char* data) {
	if (feed_ready(len) == 0) return;
	pthread_mutex_lock(&buffer_mutex);
	read_to_buffer_char16(data, len);
	pthread_mutex_unlock(&buffer_mutex);
}

EXPORT void set_subtrack(int n) {
	subtrack = n;
}

EXPORT void print_status() {
	log_msg(LOG_INFO, "command is %d, mode is %d, gate is %f", command, mode, gate);
}

EXPORT float* get_vis_side_buffer(){
	return vis_side_buffer;
	}

EXPORT int get_vis_side_buffer_fill(){
	return vis_side_fill;
	}

EXPORT void reset_vis_side_buffer(){
	vis_side_fill = 0;
	}

EXPORT int phazor_shutdown() {
	while (command != NONE || stream_loading) {
		bs_cancel();
		usleep(1000);
	}
	bs_cancel();
	command = EXIT;
	return 0;
}
