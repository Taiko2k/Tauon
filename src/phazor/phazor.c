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

#ifdef WIN64
	#include <windows.h>
	#ifndef __MINGW64__
		#define usleep(usec) Sleep((usec) / 1000)  // Convert microseconds to milliseconds
	#endif
#else
	#include <unistd.h>
#endif

#if defined(PIPE) && defined(MINI)
	#error "Only one backend can be selected!"
#endif
#ifdef PIPE
	#pragma message("Building using PipeWire as the backend.")
#elif defined(MINI)
	#pragma message("Building using miniaudio as the backend.")
#else
	#error "You need to select a backend with '-D MINI' or '-D PIPE'!"
#endif

#ifdef PIPE
	#include <pipewire/pipewire.h>
	#include <pipewire/extensions/metadata.h>
	#include <spa/param/audio/format-utils.h>
	#include <spa/param/audio/dsd.h>
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
float rg_value_pending = 1.0;
float rg_value_current = 1.0;
float rg_output_base = 1.0f;
float rg_output_correction = 1.0f;
float rg_output_correction_target = 1.0f;
int rg_output_correction_ramp_remaining = 0;
float rg_output_pending_base = 1.0f;
float rg_output_pending_correction = 1.0f;
bool rg_output_boundary_pending = false;


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
int config_dsd_direct = 0;  // Send DSD to the device untouched instead of decoding it to PCM

#define EQ_BAND_COUNT 10
#define EQ_AUTO_HEADROOM_MARGIN_DB 1.0f
#define LIMITER_THRESHOLD 0.89125093813f // -1 dBFS
#define LIMITER_ATTACK_MS 1.5f
#define LIMITER_RELEASE_MS 120.0f
#define RG_COMPRESSOR_THRESHOLD 0.89125093813f // -1 dBFS
#define RG_COMPRESSOR_RELEASE_MS 150.0f

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
// Shared output compressor for ReplayGain and positive EQ boosts.
int rg_compressor_enabled = 0;
int rg_compressor_active = 0;
float rg_compressor_gain = 1.0f;
float rg_compressor_release_coeff = 0.0f;
int rg_compressor_coeff_sample_rate = 0;

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
	DSD_RAW,
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
	// Layout the device negotiated for a DSD stream. `interleave` follows the
	// SPA convention: magnitude is how many bytes of one channel are grouped,
	// negative means those bytes are stored back to front. Defaults match
	// DSD_U32_BE, which is what most USB DACs advertise.
	volatile int pipe_dsd_streaming = 0;   // the connected stream is carrying DSD
	int pipe_dsd_interleave = 4;
	int pipe_dsd_lsb = 0;
	// What the live connection was *asked* to carry, and at what byte rate.
	// Negotiation is asynchronous, so pipe_dsd_streaming lags this; comparing
	// against the request rather than the result is what stops pump_decode
	// tearing the stream down again while the answer is still in flight.
	int pipe_dsd_requested = 0;
	int pipe_dsd_requested_rate = 0;
	int64_t pipe_dsd_wait_start_ms = 0;
	// Last rate we asked the device to re-clock to, so we request each rate at
	// most once and never spin in pump_decode when the device can't comply.
	int pipe_requested_rate = 0;
	// Set while we tear down the stream on purpose (rate switch) so the state
	// callback doesn't mistake our own disconnect for the stream being lost.
	volatile bool pipe_expecting_disconnect = false;
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

	// PipeWire will happily fixate a DSD format on our side of the graph even
	// when the sink cannot carry it — pw-cat behaves the same way — and the
	// stream then reports "streaming" while the ALSA device is never opened,
	// so playback is silent with no error anywhere. The only reliable check is
	// to ask the sink node what it supports before offering DSD at all.
	//
	// Kept out of struct device_info because that array is compacted on
	// removal, and spa_hook is an intrusive list node that cannot be moved.
	struct dsd_probe {
		uint32_t id;
		struct pw_proxy *proxy;
		struct spa_hook listener;
		int used;
		int dsd_capable;
		int announced;   // keeps the capability out of the log on every re-probe
	};
	struct dsd_probe dsd_probes[MAX_DEVICES] = {0};

	// node.name of the sink the session manager would pick for us, read from
	// the "default" metadata object. Needed because the device preference is
	// usually just "Default", which names no node.
	char pipe_default_sink[256] = "";

	// Watch the "default" metadata object so a device preference of "Default"
	// can be resolved to a concrete sink, which is what the DSD capability
	// check needs.
	static struct pw_proxy *pipe_metadata_proxy = NULL;
	static struct spa_hook pipe_metadata_listener;

	static int metadata_property_cb(void *data, uint32_t subject, const char *key,
			const char *type, const char *value) {
		if (key == NULL || value == NULL || !spa_streq(key, "default.audio.sink")) return 0;
		// The value is a small JSON object, {"name":"alsa_output...."}. Pulling
		// the one field out by hand avoids taking on a JSON dependency.
		const char *at = strstr(value, "\"name\"");
		if (at == NULL) return 0;
		at = strchr(at + 6, '"');
		if (at == NULL) return 0;
		at++;
		const char *end = strchr(at, '"');
		if (end == NULL) return 0;
		size_t len = (size_t) (end - at);
		if (len >= sizeof(pipe_default_sink)) len = sizeof(pipe_default_sink) - 1;
		pthread_mutex_lock(&pipe_devices_mutex);
		memcpy(pipe_default_sink, at, len);
		pipe_default_sink[len] = '\0';
		pthread_mutex_unlock(&pipe_devices_mutex);
		log_msg(LOG_INFO, "ph: Default sink is %s", pipe_default_sink);
		return 0;
	}

	static const struct pw_metadata_events metadata_events = {
		PW_VERSION_METADATA_EVENTS,
		.property = metadata_property_cb,
	};

	static void pipe_metadata_bind(uint32_t id) {
		if (pipe_metadata_proxy != NULL) return;
		pipe_metadata_proxy = pw_registry_bind(
			registry, id, PW_TYPE_INTERFACE_Metadata, PW_VERSION_METADATA, 0);
		if (pipe_metadata_proxy == NULL) return;
		spa_zero(pipe_metadata_listener);
		pw_metadata_add_listener((struct pw_metadata *) pipe_metadata_proxy,
			&pipe_metadata_listener, &metadata_events, NULL);
	}

	// The sink told us about a format it accepts. We only care whether DSD is
	// among them.
	static void node_param_cb(void *data, int seq, uint32_t id, uint32_t index,
			uint32_t next, const struct spa_pod *param) {
		struct dsd_probe *probe = data;
		if (id != SPA_PARAM_EnumFormat || param == NULL) return;
		uint32_t media_type, media_subtype;
		if (spa_format_parse(param, &media_type, &media_subtype) < 0) return;
		if (media_type != SPA_MEDIA_TYPE_audio || media_subtype != SPA_MEDIA_SUBTYPE_dsd) return;
		// Read from the audio thread when a track loads, so take the lock the
		// rest of the device list uses
		pthread_mutex_lock(&pipe_devices_mutex);
		probe->dsd_capable = 1;
		int announce = !probe->announced;
		probe->announced = 1;
		uint32_t probe_id = probe->id;
		pthread_mutex_unlock(&pipe_devices_mutex);
		if (announce) log_msg(LOG_INFO, "ph: Sink %u supports direct DSD", probe_id);
	}

	// Node info arrives on bind and again whenever the node changes, which
	// includes the card profile being switched. Re-read the formats each time:
	// the same sink can gain or lose DSD when its profile changes.
	static void node_info_cb(void *data, const struct pw_node_info *info) {
		struct dsd_probe *probe = data;
		if (info == NULL || info->params == NULL) return;
		for (uint32_t i = 0; i < info->n_params; i++) {
			if (info->params[i].id != SPA_PARAM_EnumFormat) continue;
			if (!(info->params[i].flags & SPA_PARAM_INFO_READ)) continue;
			pthread_mutex_lock(&pipe_devices_mutex);
			probe->dsd_capable = 0;
			pthread_mutex_unlock(&pipe_devices_mutex);
			pw_node_enum_params((struct pw_node *) probe->proxy, 0,
				SPA_PARAM_EnumFormat, 0, UINT32_MAX, NULL);
			break;
		}
	}

	static const struct pw_node_events node_events = {
		PW_VERSION_NODE_EVENTS,
		.info = node_info_cb,
		.param = node_param_cb,
	};

	static void dsd_probe_add(uint32_t id) {
		int slot = -1;
		pthread_mutex_lock(&pipe_devices_mutex);
		for (int i = 0; i < MAX_DEVICES; i++) {
			if (dsd_probes[i].used && dsd_probes[i].id == id) {
				pthread_mutex_unlock(&pipe_devices_mutex);
				return;
			}
			if (slot < 0 && !dsd_probes[i].used) slot = i;
		}
		if (slot < 0) {
			pthread_mutex_unlock(&pipe_devices_mutex);
			return;
		}
		// Claim the slot before binding so a second call cannot take it too
		dsd_probes[slot].id = id;
		dsd_probes[slot].used = 1;
		dsd_probes[slot].dsd_capable = 0;
		dsd_probes[slot].announced = 0;
		pthread_mutex_unlock(&pipe_devices_mutex);

		struct pw_proxy *proxy = pw_registry_bind(
			registry, id, PW_TYPE_INTERFACE_Node, PW_VERSION_NODE, 0);
		if (proxy == NULL) {
			pthread_mutex_lock(&pipe_devices_mutex);
			spa_zero(dsd_probes[slot]);
			pthread_mutex_unlock(&pipe_devices_mutex);
			return;
		}
		dsd_probes[slot].proxy = proxy;
		spa_zero(dsd_probes[slot].listener);
		pw_node_add_listener((struct pw_node *) proxy,
			&dsd_probes[slot].listener, &node_events, &dsd_probes[slot]);
	}

	// PipeWire thread only, so the proxy teardown needs no lock; the lock is
	// just to keep the slot from being read while it is being cleared.
	static void dsd_probe_remove(uint32_t id) {
		for (int i = 0; i < MAX_DEVICES; i++) {
			if (!dsd_probes[i].used || dsd_probes[i].id != id) continue;
			spa_hook_remove(&dsd_probes[i].listener);
			if (dsd_probes[i].proxy) pw_proxy_destroy(dsd_probes[i].proxy);
			pthread_mutex_lock(&pipe_devices_mutex);
			spa_zero(dsd_probes[i]);
			pthread_mutex_unlock(&pipe_devices_mutex);
			return;
		}
	}

	// Whether the sink we would actually play to accepts a DSD stream. Unknown
	// sinks answer no: silence is a far worse outcome than decoding to PCM.
	static int pipe_target_supports_dsd() {
		int found = 0;
		pthread_mutex_lock(&pipe_devices_mutex);
		const char *want_name = NULL;
		if (strcmp(config_output_sink, "Default") == 0) {
			want_name = pipe_default_sink[0] ? pipe_default_sink : NULL;
		}
		for (size_t i = 0; i < pipe_devices.device_count; i++) {
			int match = want_name != NULL
				? strcmp(pipe_devices.devices[i].name, want_name) == 0
				: strcmp(pipe_devices.devices[i].description, config_output_sink) == 0;
			if (!match) continue;
			for (int j = 0; j < MAX_DEVICES; j++) {
				if (dsd_probes[j].used && dsd_probes[j].id == pipe_devices.devices[i].id) {
					found = dsd_probes[j].dsd_capable;
					break;
				}
			}
			break;
		}
		pthread_mutex_unlock(&pipe_devices_mutex);
		return found;
	}

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
		dsd_probe_remove(id);

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

		if (props == NULL || type == NULL) return;

		// The "default" metadata object names the sink the session manager
		// routes us to, which is what a device preference of "Default"
		// resolves to. It is not a Node, so it has to be picked off before the
		// Node filter below.
		if (spa_streq(type, PW_TYPE_INTERFACE_Metadata)) {
			const char *mname = spa_dict_lookup(props, PW_KEY_METADATA_NAME);
			if (mname != NULL && spa_streq(mname, "default")) pipe_metadata_bind(id);
			return;
		}

		if (!spa_streq(type, PW_TYPE_INTERFACE_Node)) return;

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
			// Ask this sink whether it can carry DSD
			dsd_probe_add(id);

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

// Fill of whichever buffer is actually feeding the device. Direct DSD has its
// own ring and never puts anything in the float buffers, so the plain
// get_buff_fill() reads as permanently empty on that path.
int pending_output_fill();

// Defined further down with the rest of the exported API, but the direct DSD
// fallback needs it to carry the playback position over to the PCM decoder.
EXPORT int get_position_ms();

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

// Monotonic milliseconds, for timing out waits that have no other end
static inline int64_t now_ms() {
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (int64_t) ts.tv_sec * 1000 + ts.tv_nsec / 1000000;
}

static void bs_wait_locked(int ms) {
	struct timespec ts;
	// clock_gettime + CLOCK_REALTIME is provided by winpthreads on MinGW
	// (already linked for pthreads), so this is portable across platforms.
	// timespec_get() is avoided as it is missing on the MSVCRT runtime.
	clock_gettime(CLOCK_REALTIME, &ts);
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

	if (rg_value_current != 1.0) {
		bfr[high] *= rg_value_current;
		bfl[high] *= rg_value_current;
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


// Direct DSD related ------------------------------------------------
//
// When the user enables direct DSD output and the backend can carry it, DSF
// and DSDIFF files are demuxed here and their 1 bit stream is handed to the
// device untouched. Nothing in the normal pipeline can be applied to DSD, so
// this path deliberately bypasses the float mixing buffers, the resampler,
// ReplayGain, the EQ and the fades. Every other backend keeps decoding DSD to
// PCM with FFmpeg as before.
//
// Internally the stream is kept in a canonical layout: one planar buffer per
// channel, most significant bit first. It is converted to whatever byte
// grouping and bit order the device negotiated only on the way out.

#define DSD_MAX_CHANNELS 2
#define DSD_BUFF_SIZE (2 * 1024 * 1024)  // Per channel. ~5.9s of DSD64, ~0.7s of DSD512
// How long to wait for the device to accept an offered DSD stream before
// deciding it never will. A sink that cannot take DSD normally errors out
// well inside this; the timeout only covers one that goes quiet instead.
#define DSD_NEGOTIATE_TIMEOUT_MS 1500

struct dsd_stream_info {
	int is_dff;             // 0 = DSF (planar, lsb first), 1 = DSDIFF (interleaved, msb first)
	int channels;
	uint32_t rate;          // DSD bit rate per channel, e.g. 2822400 for DSD64
	int lsb_first;          // Bit order as stored in the file
	uint32_t block_size;    // DSF block size per channel, normally 4096
	int64_t data_start;     // Offset of the first audio byte
	int64_t data_bytes;     // Total audio bytes for all channels
	int64_t data_pos;       // Audio bytes consumed so far
	int64_t sample_bytes;   // Exact audio bytes per channel, excluding DSF block padding
};

struct dsd_stream_info dsd_info;
int dsd_active = 0;             // The loaded track is being played as raw DSD
int dsd_runtime_disabled = 0;   // Set after the device refuses a DSD stream
int dsd_negotiation_failed = 0; // Latched for the UI so it can explain the fallback

// Only the PipeWire backend can carry a DSD stream to the device. Everywhere
// else the preference is ignored and DSD keeps going out as PCM.
int dsd_direct_supported() {
	#ifdef PIPE
		return 1;
	#else
		return 0;
	#endif
}

#ifdef PIPE
	static int pipe_target_supports_dsd();
#endif

static int dsd_direct_wanted() {
	// Once a device has refused a DSD stream, stop offering it. Turning the
	// preference off and on again clears this, as does restarting.
	if (!config_dsd_direct || !dsd_direct_supported() || dsd_runtime_disabled) return 0;
	#ifdef PIPE
		// The sink has to actually accept DSD. PipeWire will otherwise fixate
		// the format on our side and then never open the device, which plays
		// as silence rather than failing, so this check is what stands between
		// the user and a silent track.
		if (!pipe_target_supports_dsd()) return 0;
	#endif
	return 1;
}

// Planar ring buffer, one per channel. All channels share the indices since
// they always advance together. Allocated on the first direct DSD track so
// builds that can never use it pay nothing.
unsigned char *dsd_buf[DSD_MAX_CHANNELS] = { NULL };
int dsd_low = 0;
int dsd_high = 0;
int64_t dsd_bytes_played = 0;  // Per channel, for position reporting

// Staging area for one read straight out of the file, before the bytes are
// split into the planar ring. Sized for one chunk per channel so a whole DSF
// block group fits, which lets the file reads happen outside the buffer lock.
#define DSD_READ_CHUNK 16384
unsigned char dsd_read_buf[DSD_MAX_CHANNELS * DSD_READ_CHUNK];

unsigned char dsd_bit_reverse[256];

void dsd_build_bit_reverse_table() {
	for (int i = 0; i < 256; i++) {
		unsigned char v = (unsigned char) i;
		v = (unsigned char) (((v & 0xF0) >> 4) | ((v & 0x0F) << 4));
		v = (unsigned char) (((v & 0xCC) >> 2) | ((v & 0x33) << 2));
		v = (unsigned char) (((v & 0xAA) >> 1) | ((v & 0x55) << 1));
		dsd_bit_reverse[i] = v;
	}
}

static int dsd_alloc() {
	for (int c = 0; c < DSD_MAX_CHANNELS; c++) {
		if (dsd_buf[c] == NULL) {
			dsd_buf[c] = malloc(DSD_BUFF_SIZE);
			if (dsd_buf[c] == NULL) {
				log_msg(LOG_ERROR, "pa: Could not allocate DSD buffer");
				return 1;
			}
		}
	}
	return 0;
}

int dsd_buff_fill() {
	if (dsd_low <= dsd_high) return dsd_high - dsd_low;
	return DSD_BUFF_SIZE - dsd_low + dsd_high;
}

int dsd_buff_space() {
	return DSD_BUFF_SIZE - dsd_buff_fill() - 1;
}

void dsd_buff_reset() {
	dsd_low = 0;
	dsd_high = 0;
}

int pending_output_fill() {
	return dsd_active ? dsd_buff_fill() : get_buff_fill();
}

// Read a big endian 64 bit chunk length, as used by DSDIFF
static int64_t dsd_be64(const unsigned char *p) {
	int64_t v = 0;
	for (int i = 0; i < 8; i++) v = (v << 8) | p[i];
	return v;
}

static uint32_t dsd_le32(const unsigned char *p) {
	return ((uint32_t) p[0]) | ((uint32_t) p[1] << 8) | ((uint32_t) p[2] << 16) | ((uint32_t) p[3] << 24);
}

static int64_t dsd_le64(const unsigned char *p) {
	int64_t v = 0;
	for (int i = 7; i >= 0; i--) v = (v << 8) | p[i];
	return v;
}

// Parse a DSF header. The byte stream must already be open and positioned at 0.
// Returns 0 on success.
static int dsd_open_dsf(struct dsd_stream_info *info) {
	unsigned char hdr[28];
	unsigned char fmt[52];

	if (bs_seek_abs(0) != 0) return 1;
	if (bs_read_exact(hdr, sizeof(hdr)) != (int) sizeof(hdr)) return 1;
	if (memcmp(hdr, "DSD ", 4) != 0) return 1;

	// The fmt chunk follows the 28 byte DSD chunk
	if (bs_seek_abs(28) != 0) return 1;
	if (bs_read_exact(fmt, sizeof(fmt)) != (int) sizeof(fmt)) return 1;
	if (memcmp(fmt, "fmt ", 4) != 0) return 1;

	uint32_t format_id = dsd_le32(fmt + 16);
	if (format_id != 0) {
		log_msg(LOG_ERROR, "pa: DSF is not raw DSD (format id %u)", format_id);
		return 1;
	}

	info->is_dff = 0;
	info->lsb_first = 1;  // DSF stores the earliest sample in the least significant bit
	info->channels = (int) dsd_le32(fmt + 24);
	info->rate = dsd_le32(fmt + 28);
	uint32_t bits = dsd_le32(fmt + 32);
	int64_t samples = dsd_le64(fmt + 36);
	info->block_size = dsd_le32(fmt + 44);

	if (bits != 1) {
		log_msg(LOG_ERROR, "pa: DSF bits per sample is %u, expected 1", bits);
		return 1;
	}
	if (info->channels < 1 || info->channels > DSD_MAX_CHANNELS) {
		log_msg(LOG_ERROR, "pa: DSF has %d channels, only up to %d supported", info->channels, DSD_MAX_CHANNELS);
		return 1;
	}
	if (info->block_size == 0 || info->block_size > DSD_READ_CHUNK) {
		log_msg(LOG_ERROR, "pa: DSF block size %u out of range", info->block_size);
		return 1;
	}

	// The data chunk follows the fmt chunk
	unsigned char data_hdr[12];
	if (bs_seek_abs(28 + 52) != 0) return 1;
	if (bs_read_exact(data_hdr, sizeof(data_hdr)) != (int) sizeof(data_hdr)) return 1;
	if (memcmp(data_hdr, "data", 4) != 0) return 1;

	int64_t data_chunk_size = dsd_le64(data_hdr + 4);
	info->data_start = 28 + 52 + 12;
	info->data_bytes = data_chunk_size - 12;
	info->data_pos = 0;
	// Samples are padded out to whole blocks, so the useful length is shorter
	// than the chunk. Track it so playback stops at the real end.
	info->sample_bytes = samples / 8;
	if (info->sample_bytes <= 0 || info->sample_bytes * info->channels > info->data_bytes) {
		info->sample_bytes = info->data_bytes / info->channels;
	}

	log_msg(LOG_INFO, "pa: DSF %d ch, %u Hz DSD, block %u", info->channels, info->rate, info->block_size);
	return 0;
}

// Parse a DSDIFF (.dff) header. Only uncompressed DSD is handled here; DST
// compressed files stay on the FFmpeg path since unpacking them would mean
// decoding, which defeats the point of a direct path.
static int dsd_open_dff(struct dsd_stream_info *info) {
	unsigned char hdr[16];

	if (bs_seek_abs(0) != 0) return 1;
	if (bs_read_exact(hdr, 16) != 16) return 1;
	if (memcmp(hdr, "FRM8", 4) != 0 || memcmp(hdr + 12, "DSD ", 4) != 0) return 1;

	info->is_dff = 1;
	info->lsb_first = 0;  // DSDIFF stores the earliest sample in the most significant bit
	info->channels = 0;
	info->rate = 0;
	info->block_size = 0;
	info->data_start = 0;
	info->data_bytes = 0;
	info->data_pos = 0;

	int compressed = 0;
	int64_t pos = 16;  // First chunk after FRM8 header and the "DSD " form type
	int64_t file_len = bs_length();

	// Walk the top level chunks looking for PROP (which carries the format)
	// and DSD (the audio itself)
	for (int guard = 0; guard < 64; guard++) {
		// 12 byte chunk header (4 byte id, 8 byte length) plus the first 4
		// payload bytes, which is where the form/property type lives
		unsigned char ch[16];
		if (bs_seek_abs(pos) != 0) break;
		if (bs_read_exact(ch, 16) != 16) break;
		int64_t len = dsd_be64(ch + 4);
		if (len < 0) break;

		if (memcmp(ch, "PROP", 4) == 0 && memcmp(ch + 12, "SND ", 4) == 0) {
			// Walk the property chunks nested inside PROP, which start after
			// the PROP header and its 4 byte property type
			int64_t p = pos + 16;
			int64_t prop_end = pos + 12 + len;
			while (p + 12 <= prop_end) {
				unsigned char pc[16];
				if (bs_seek_abs(p) != 0) break;
				if (bs_read_exact(pc, 16) != 16) break;
				int64_t plen = dsd_be64(pc + 4);
				if (plen < 0) break;

				if (memcmp(pc, "FS  ", 4) == 0) {
					info->rate = ((uint32_t) pc[12] << 24) | ((uint32_t) pc[13] << 16)
						| ((uint32_t) pc[14] << 8) | (uint32_t) pc[15];
				} else if (memcmp(pc, "CHNL", 4) == 0) {
					info->channels = (pc[12] << 8) | pc[13];
				} else if (memcmp(pc, "CMPR", 4) == 0) {
					// Compression type is a four character code; "DSD " means
					// uncompressed, "DST " means DST compressed
					if (memcmp(pc + 12, "DSD ", 4) != 0) compressed = 1;
				}
				p += 12 + plen + (plen & 1);  // chunks are padded to even length
			}
		} else if (memcmp(ch, "DSD ", 4) == 0) {
			info->data_start = pos + 12;
			info->data_bytes = len;
		} else if (memcmp(ch, "DST ", 4) == 0) {
			compressed = 1;
		}

		pos += 12 + len + (len & 1);
		if (file_len > 0 && pos >= file_len) break;
	}

	if (compressed) {
		log_msg(LOG_INFO, "pa: DSDIFF is DST compressed, not eligible for direct DSD");
		return 1;
	}
	if (info->rate == 0 || info->channels < 1 || info->channels > DSD_MAX_CHANNELS || info->data_bytes <= 0) {
		log_msg(LOG_ERROR, "pa: DSDIFF header incomplete (rate %u, %d ch)", info->rate, info->channels);
		return 1;
	}

	info->sample_bytes = info->data_bytes / info->channels;
	log_msg(LOG_INFO, "pa: DSDIFF %d ch, %u Hz DSD", info->channels, info->rate);
	return 0;
}

// Append one channel's worth of bytes to the planar ring, normalising to msb
// first so the output stage only has to think about the device's layout.
// `stride` steps over the other channels when the source is interleaved.
static void dsd_push_channel(int ch, const unsigned char *src, int n, int stride, int lsb_first, int at) {
	for (int i = 0; i < n; i++) {
		unsigned char v = src[(size_t) i * stride];
		dsd_buf[ch][at] = lsb_first ? dsd_bit_reverse[v] : v;
		at++;
		if (at >= DSD_BUFF_SIZE) at = 0;
	}
}

// Pull one block of audio out of the file and into the ring. Returns the bytes
// per channel added, 0 at end of stream, or -1 when the ring has no room yet.
// The file reads deliberately happen outside buffer_mutex and only the short
// copy into the ring takes it, so a slow read can never starve the device
// callback of the audio already buffered.
static int dsd_fill_buffer() {
	int space = dsd_buff_space();
	if (space < DSD_READ_CHUNK) return -1;  // No room right now, try again later

	// Anything past sample_bytes is DSF block padding rather than audio.
	// Stopping there keeps playback position and reported length in agreement.
	int64_t remaining = dsd_info.sample_bytes - (dsd_info.data_pos / dsd_info.channels);
	if (remaining <= 0) return 0;

	int per_channel;
	int stride;
	int64_t advance;

	if (dsd_info.is_dff) {
		// Interleaved, one byte per channel in turn
		per_channel = DSD_READ_CHUNK;
		if (per_channel > space) per_channel = space;
		if ((int64_t) per_channel > remaining) per_channel = (int) remaining;
		if (per_channel <= 0) return -1;

		if (bs_seek_abs(dsd_info.data_start + dsd_info.data_pos) != 0) return 0;
		int got = bs_read_exact(dsd_read_buf, per_channel * dsd_info.channels);
		if (got < dsd_info.channels) return 0;
		per_channel = got / dsd_info.channels;
		stride = dsd_info.channels;
		advance = (int64_t) per_channel * dsd_info.channels;
	} else {
		// DSF stores a whole block for each channel in turn, so a block group
		// has to be taken as a unit or the channels would skew apart
		uint32_t block = dsd_info.block_size;
		int short_read = 0;
		for (int c = 0; c < dsd_info.channels; c++) {
			int64_t at = dsd_info.data_start + dsd_info.data_pos + (int64_t) c * block;
			if (bs_seek_abs(at) != 0) return 0;
			int got = bs_read_exact(dsd_read_buf + (size_t) c * DSD_READ_CHUNK, (int) block);
			if (got <= 0) return 0;
			// A truncated file cuts every channel back to the shortest read
			if (got < (int) block && (short_read == 0 || got < short_read)) short_read = got;
		}
		per_channel = short_read ? short_read : (int) block;
		if ((int64_t) per_channel > remaining) per_channel = (int) remaining;
		stride = 1;
		// Padding inside the final block is dropped above, but the group still
		// occupies a whole block group in the file
		advance = (int64_t) block * dsd_info.channels;
	}

	pthread_mutex_lock(&buffer_mutex);
	for (int c = 0; c < dsd_info.channels; c++) {
		const unsigned char *src = dsd_info.is_dff
			? dsd_read_buf + c
			: dsd_read_buf + (size_t) c * DSD_READ_CHUNK;
		dsd_push_channel(c, src, per_channel, stride, dsd_info.lsb_first, dsd_high);
	}
	dsd_high = (dsd_high + per_channel) % DSD_BUFF_SIZE;
	dsd_info.data_pos += advance;
	pthread_mutex_unlock(&buffer_mutex);
	return per_channel;
}

// Convert bytes_per_channel of planar msb first DSD into the layout the device
// asked for. `interleave` is the SPA convention: the magnitude is how many
// bytes of one channel are grouped together, a negative value means those
// bytes are stored in reverse order. Returns bytes written to dest.
int dsd_pack(unsigned char *dest, int bytes_per_channel, int channels, int interleave, int bitorder_lsb) {
	int group = interleave < 0 ? -interleave : interleave;
	if (group < 1) group = 1;
	// Only whole groups can be emitted
	bytes_per_channel -= bytes_per_channel % group;
	if (bytes_per_channel <= 0) return 0;

	int out = 0;
	int groups = bytes_per_channel / group;
	for (int g = 0; g < groups; g++) {
		for (int c = 0; c < channels; c++) {
			for (int b = 0; b < group; b++) {
				// For a reversed group take the bytes back to front
				int src_b = interleave < 0 ? (group - 1 - b) : b;
				int idx = (dsd_low + g * group + src_b) % DSD_BUFF_SIZE;
				unsigned char v = dsd_buf[c][idx];
				dest[out++] = bitorder_lsb ? dsd_bit_reverse[v] : v;
			}
		}
	}
	return out;
}

// GME related -------------------

Music_Emu* emu;

// FFmpeg related -----------------------------------------------------

FILE *ffm;
char exe_string[4096];
char ffm_buffer[4096];  // float32 stereo, so this is the same frame count the 16 bit path used

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

static inline float f32le_to_float(const unsigned char *p) {
	union {
		uint32_t i;
		float f;
	} convert;
	convert.i = ((uint32_t) p[0]) | ((uint32_t) p[1] << 8) | ((uint32_t) p[2] << 16) | ((uint32_t) p[3] << 24);
	return convert.f;
}

static inline float clamp_unit(float v) {
	if (v > 1.0f) return 1.0f;
	if (v < -1.0f) return -1.0f;
	return v;
}

void read_to_buffer_charf32_resample(char src[], int n_bytes) {

	int i = 0;
	int f = 0;

	// Convert little endian float32 bytes to float
	while (i < n_bytes) {
		re_in[f * 2] = clamp_unit(f32le_to_float((const unsigned char *) src + i));
		if (src_channels == 1) {
			re_in[(f * 2) + 1] = re_in[f * 2];
			i += 4;
		} else {
			re_in[(f * 2) + 1] = clamp_unit(f32le_to_float((const unsigned char *) src + i + 4));
			i += 8;
		}

		f++;
	}

	resample_to_buffer(f);

}


void read_to_buffer_charf32(char src[], int n_bytes) {

	if (sample_rate_src != sample_rate_out) {
		read_to_buffer_charf32_resample(src, n_bytes);
		return;
	}

	int i = 0;
	if (src_channels == 1) {
		while (i < n_bytes) {
			bfl[high] = clamp_unit(f32le_to_float((const unsigned char *) src + i));
			bfr[high] = bfl[high];
			fade_fx();
			high++;
			i += 4;
		}
	} else {
		while (i < n_bytes) {
			bfl[high] = clamp_unit(f32le_to_float((const unsigned char *) src + i));
			bfr[high] = clamp_unit(f32le_to_float((const unsigned char *) src + i + 4));
			fade_fx();
			high++;
			i += 8;
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

	// Normalise samples of any bit depth to [-1.0, 1.0). FLAC supports 4-32
	// bits per sample; the decoded values are already sign-extended int32s
	// scaled to the frame's bit depth, so dividing by 2^(bits-1) works for all.
	if (frame->header.bits_per_sample < 1 || frame->header.bits_per_sample > 32) {
		log_msg(LOG_CRITICAL, "ph: INVALID BIT DEPTH!");
		pthread_mutex_unlock(&buffer_mutex);
		return FLAC__STREAM_DECODER_WRITE_STATUS_CONTINUE;
	}
	const double sample_divisor = ldexp(1.0, frame->header.bits_per_sample - 1);

	if (resample == 0) {

		// No resampling needed, transfer data to main buffer

		while (i < frame->header.blocksize) {

			bfl[high] = (buffer[0][i]) / sample_divisor;

			if (frame->header.channels == 1) {
				bfr[high] = bfl[high];
			} else {
				bfr[high] = (buffer[1][i]) / sample_divisor;
			}

			fade_fx();


			high++;
			i++;
		}

		buff_cycle();

	} else {

		// Transfer data to resampler for resampling

		while (i < frame->header.blocksize) {

			re_in[i * 2] = (buffer[0][i]) / sample_divisor;
			if (frame->header.channels == 1) re_in[(i * 2) + 1] = re_in[i * 2];
			else re_in[(i * 2) + 1] = (buffer[1][i]) / sample_divisor;

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
		case DSD_RAW:
			dsd_active = 0;
			dsd_buff_reset();
			bs_close();
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

static void rg_compressor_reset_state() {
	rg_compressor_gain = 1.0f;
	rg_compressor_active = 0;
}

static void rg_compressor_update_coefficients(int sample_rate) {
	if (sample_rate <= 0) return;

	float release_samples = (RG_COMPRESSOR_RELEASE_MS * 0.001f) * (float)sample_rate;
	if (release_samples < 1.0f) release_samples = 1.0f;

	rg_compressor_release_coeff = expf(-1.0f / release_samples);
	rg_compressor_coeff_sample_rate = sample_rate;
}

static inline void rg_apply_live_correction(float *l, float *r) {
	if (rg_output_boundary_pending && low == rg_byte) {
		rg_output_base = rg_output_pending_base;
		rg_output_correction = rg_output_pending_correction;
		rg_output_correction_target = rg_output_pending_correction;
		rg_output_correction_ramp_remaining = 0;
		rg_output_boundary_pending = false;
	}

	if (rg_output_correction_ramp_remaining > 0) {
		// Complete live setting changes in 10 ms without introducing a click.
		rg_output_correction += (
			rg_output_correction_target - rg_output_correction
		) / (float)rg_output_correction_ramp_remaining;
		rg_output_correction_ramp_remaining--;
	} else {
		rg_output_correction = rg_output_correction_target;
	}

	*l *= rg_output_correction;
	*r *= rg_output_correction;
}

static inline void rg_compressor_process_stereo(float *l, float *r) {
	if (!rg_compressor_enabled) return;

	if (current_sample_rate > 0 && rg_compressor_coeff_sample_rate != current_sample_rate) {
		rg_compressor_update_coefficients(current_sample_rate);
	}

	float peak = fmaxf(fabsf(*l), fabsf(*r));
	float target_gain = 1.0f;
	if (peak > RG_COMPRESSOR_THRESHOLD) {
		target_gain = RG_COMPRESSOR_THRESHOLD / (peak + 1e-20f);
	}

	// An immediate, stereo-linked attack prevents overshoot. Release is
	// smoothed so isolated peaks do not produce abrupt level changes.
	if (target_gain < rg_compressor_gain) {
		rg_compressor_gain = target_gain;
	} else {
		rg_compressor_gain = target_gain
			+ (rg_compressor_release_coeff * (rg_compressor_gain - target_gain));
	}

	if (!isfinite(rg_compressor_gain) || rg_compressor_gain <= 0.0f) {
		rg_compressor_gain = 1.0f;
	}

	*l *= rg_compressor_gain;
	*r *= rg_compressor_gain;
	rg_compressor_active = rg_compressor_gain < 0.9995f;

	// Guard against rounding error after gain reduction.
	if (*l > 1.0f) *l = 1.0f;
	else if (*l < -1.0f) *l = -1.0f;
	if (*r > 1.0f) *r = 1.0f;
	else if (*r < -1.0f) *r = -1.0f;
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

// Output side of the direct DSD path. Fills up to max_bytes of the device
// buffer in the negotiated layout and returns how many bytes were written.
// Nothing here touches volume, ReplayGain, the EQ or the fades: a DSD stream
// has to reach the DAC bit for bit or it is just noise.
int get_dsd_audio(int max_bytes, void *dest, int interleave, int bitorder_lsb) {
	int group = interleave < 0 ? -interleave : interleave;
	if (group < 1) group = 1;

	pthread_mutex_lock(&buffer_mutex);

	int channels = dsd_info.channels > 0 ? dsd_info.channels : 2;
	int frame = group * channels;  // bytes emitted per group of source bytes
	int available = dsd_buff_fill();
	int want_groups = max_bytes / frame;
	int have_groups = available / group;
	int groups = want_groups < have_groups ? want_groups : have_groups;

	if (groups <= 0 || (mode != PLAYING && mode != ENDING)) {
		pthread_mutex_unlock(&buffer_mutex);
		// Silence in DSD is an alternating bit pattern, not zeroes. Zeroes
		// would be a DC offset that some DACs reproduce as a thump.
		memset(dest, 0x69, max_bytes);
		return max_bytes;
	}

	int bytes_per_channel = groups * group;
	int written = dsd_pack((unsigned char *) dest, bytes_per_channel, channels, interleave, bitorder_lsb);

	dsd_low = (dsd_low + bytes_per_channel) % DSD_BUFF_SIZE;
	dsd_bytes_played += bytes_per_channel;

	// Out of buffered audio and the file is finished, so wind the track up
	if (dsd_buff_fill() == 0 && mode == PLAYING
			&& dsd_info.data_pos / dsd_info.channels >= dsd_info.sample_bytes) {
		mode = ENDING;
	}

	pthread_mutex_unlock(&buffer_mutex);
	return written;
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
				rg_apply_live_correction(&l, &r);
				eq_process_stereo(&l, &r);
				if (eq_enabled && eq_active && !rg_compressor_enabled) {
					l *= eq_headroom_gain;
					r *= eq_headroom_gain;
				}

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
				l = l * final_vol;
				r = r * final_vol;
				// Limiting after soft volume lets ReplayGain and EQ boosts use
				// its headroom before any compression is applied.
				rg_compressor_process_stereo(&l, &r);
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
		struct spa_data *data;
		uint32_t frames;
		const uint32_t stride = sizeof(float) * 2;


		if ((buffer = pw_stream_dequeue_buffer(global_stream)) == NULL)
			return;

		buf = buffer->buffer;
		data = &buf->datas[0];

		if (pipe_dsd_streaming) {
			// Raw DSD: bytes, not frames, and nothing may be applied to them
			uint32_t max = data->maxsize;
			int group = pipe_dsd_interleave < 0 ? -pipe_dsd_interleave : pipe_dsd_interleave;
			int channels = dsd_info.channels > 0 ? dsd_info.channels : 2;
			uint32_t unit = (uint32_t) (group * channels);
			if (buffer->requested > 0 && buffer->requested * unit < max) {
				max = (uint32_t) buffer->requested * unit;
			}
			max -= max % unit;
			data->chunk->offset = 0;
			data->chunk->stride = (int32_t) unit;
			data->chunk->size = (uint32_t) get_dsd_audio(
				(int) max, data->data, pipe_dsd_interleave, pipe_dsd_lsb);
			pw_stream_queue_buffer(global_stream, buffer);
			return;
		}

		// `requested` is the number of source frames wanted by PipeWire's
		// resampler, not a guarantee that the mapped buffer is that large.
		// Respect the actual capacity or high-rate streams can advance our
		// position counter for frames that do not fit in the output buffer.
		frames = data->maxsize / stride;
		if (buffer->requested > 0 && buffer->requested < frames) {
			frames = buffer->requested;
		}

		if (frames > 0) {
			data->chunk->size = get_audio(frames * 2, data->data) * sizeof(float);
		} else {
			data->chunk->size = 0;
		}
		data->chunk->offset = 0;
		data->chunk->stride = stride;
		buffer->size = data->chunk->size / stride;
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
			// Ignore the transient disconnect we trigger ourselves during a
			// rate switch; only a genuine, unexpected drop means we're lost.
			if (pipe_expecting_disconnect) return;
			if (dsd_active && !pipe_dsd_streaming) {
				// The sink would not take a DSD stream. Most likely the DAC
				// has no native DSD, or another app is holding the device in
				// PCM mode. Give up on direct output and let the track play
				// as PCM instead of failing outright.
				log_msg(LOG_ERROR, "ph: Device refused a direct DSD stream (%s), falling back to PCM",
					error ? error : "no error");
				dsd_runtime_disabled = 1;
				dsd_negotiation_failed = 1;
			}
			log_msg(LOG_ERROR, "PipeWire stream lost (%s)", error ? error : "no error");
			pulse_connected = false;
		}
	}

	// PipeWire tells us the format it actually negotiated here. The requested
	// rate is only a preference; the graph may settle on something else. Track
	// the real value in sample_rate_out so the internal resampler bridges any
	// residual gap instead of pump_decode spinning trying to force a match.
	static void pipe_apply_output_rate(int rate) {
		if (rate <= 0 || (rate == sample_rate_out && rate == current_sample_rate)) return;

		pthread_mutex_lock(&buffer_mutex);
		if (current_sample_rate > 0 && current_sample_rate != rate && position_count > 0) {
			position_count = (int) (position_count * ((double) rate / current_sample_rate));
		}
		sample_rate_out = rate;
		current_sample_rate = rate;
		pthread_mutex_unlock(&buffer_mutex);
	}

	static void on_param_changed(void *userdata, uint32_t id, const struct spa_pod *param) {
		if (param == NULL || id != SPA_PARAM_Format) return;

		uint32_t media_type, media_subtype;
		if (spa_format_parse(param, &media_type, &media_subtype) < 0) return;
		if (media_type != SPA_MEDIA_TYPE_audio) return;

		if (media_subtype == SPA_MEDIA_SUBTYPE_dsd) {
			struct spa_audio_info_dsd dsd = { 0 };
			if (spa_format_audio_dsd_parse(param, &dsd) < 0) {
				log_msg(LOG_ERROR, "ph: Could not parse negotiated DSD format");
				return;
			}
			// interleave 0 means one plane per channel, which needs a
			// multi-plane buffer this output stage does not fill. No ALSA DSD
			// format asks for it, but honouring it wrongly would send the
			// device noise, so refuse and let the track fall back to PCM.
			if (dsd.interleave == 0) {
				log_msg(LOG_ERROR, "ph: Device negotiated planar DSD, which is unsupported");
				dsd_runtime_disabled = 1;
				dsd_negotiation_failed = 1;
				return;
			}
			pipe_dsd_interleave = dsd.interleave;
			pipe_dsd_lsb = (dsd.bitorder == SPA_PARAM_BITORDER_lsb) ? 1 : 0;
			pipe_dsd_streaming = 1;
			// The DSD rate is in bytes per second, which is what we already
			// clock the decoder at, so there is nothing to re-rate here
			log_msg(LOG_INFO, "ph: PipeWire negotiated DSD, %u B/s, %u ch, interleave %d, %s first",
				dsd.rate, dsd.channels, pipe_dsd_interleave, pipe_dsd_lsb ? "lsb" : "msb");
			return;
		}

		pipe_dsd_streaming = 0;
		if (media_subtype != SPA_MEDIA_SUBTYPE_raw) return;

		struct spa_audio_info_raw info = { 0 };
		if (spa_format_audio_raw_parse(param, &info) < 0) return;

		if (info.rate > 0 && (
			(int) info.rate != sample_rate_out ||
			(int) info.rate != current_sample_rate
		)) {
			if ((int) info.rate != sample_rate_out) {
				log_msg(LOG_INFO, "ph: PipeWire negotiated samplerate %u", info.rate);
			}
			pipe_apply_output_rate(info.rate);
		}
	}

	static const struct pw_stream_events stream_events = {
		PW_VERSION_STREAM_EVENTS,
		.process = on_process,
		.state_changed = on_stream_state_changed,
		.param_changed = on_param_changed,
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
		case DSD_RAW: {
			// Seek by byte. DSF is stored a block at a time per channel, so
			// land on a block boundary or the channels would be skewed.
			int64_t byte = ((int64_t) (dsd_info.rate / 8) * abs_ms) / 1000;
			if (!dsd_info.is_dff && dsd_info.block_size)
				byte -= byte % dsd_info.block_size;
			if (byte < 0) byte = 0;
			if (byte > dsd_info.sample_bytes) byte = dsd_info.sample_bytes;
			// The output callback reads exactly this state, so unlike the
			// other codecs the seek has to be done under the buffer lock or
			// it can hand out bytes from the old position.
			pthread_mutex_lock(&buffer_mutex);
			dsd_info.data_pos = byte * dsd_info.channels;
			dsd_bytes_played = byte;
			dsd_buff_reset();
			pthread_mutex_unlock(&buffer_mutex);
			break;
		}
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
		pipe_dsd_streaming = 0;
		pipe_dsd_requested = 0;
		pipe_dsd_requested_rate = 0;
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

		// A fresh connection has negotiated nothing yet. Remember what it is
		// being asked for so pump_decode can tell "still negotiating" apart
		// from "needs a different format".
		pipe_dsd_streaming = 0;
		pipe_dsd_requested = dsd_active ? 1 : 0;
		pipe_dsd_requested_rate = dsd_active ? (int) (dsd_info.rate / 8) : 0;
		pipe_dsd_wait_start_ms = now_ms();

		// Build audio format parameters
		if (dsd_active) {
			// Offer the DSD stream itself. Nothing in the graph can convert
			// DSD, so this only negotiates against a sink whose hardware
			// takes it natively; if it cannot, the connect fails and we fall
			// back to decoding this track as PCM.
			//
			// The rate here is bytes per second, not bits: 352800 is DSD64.
			// interleave and bitorder are left for the device to choose, and
			// whatever it picks is read back in on_param_changed.
			// Mirrors what pw-cat offers: channels, rate and a channel map,
			// with interleave and bitorder left unset so the device picks
			// whatever grouping its hardware actually wants.
			struct spa_audio_info_dsd dsd_info_out;
			spa_zero(dsd_info_out);
			dsd_info_out.channels = (uint32_t) (dsd_info.channels > 0 ? dsd_info.channels : 2);
			dsd_info_out.rate = (uint32_t) (dsd_info.rate / 8);
			if (dsd_info_out.channels == 1) {
				dsd_info_out.position[0] = SPA_AUDIO_CHANNEL_MONO;
			} else {
				dsd_info_out.position[0] = SPA_AUDIO_CHANNEL_FL;
				dsd_info_out.position[1] = SPA_AUDIO_CHANNEL_FR;
			}
			params[0] = spa_format_audio_dsd_build(&b, SPA_PARAM_EnumFormat, &dsd_info_out);
			if (params[0] == NULL) {
				log_msg(LOG_ERROR, "Failed to build DSD format parameters");
				return -EINVAL;
			}
			log_msg(LOG_INFO, "ph: Offering direct DSD, %u bytes/s, %u ch",
				dsd_info_out.rate, dsd_info_out.channels);
		} else {
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

		// When avoiding resampling, ask the graph/driver to run at our rate so
		// the device re-clocks instead of resampling us. Without this the format
		// rate alone just gets adapted to the running graph rate. When resampling
		// is allowed, clear it so we don't disturb the shared graph rate.
		if (dsd_active) {
			// Leave the graph rate alone. A DSD stream is passthrough, so the
			// sink takes the rate from the negotiated format; pw-cat does not
			// set this either and forcing it risks disturbing the graph.
			pw_properties_set(mutable_props, PW_KEY_NODE_RATE, NULL);
		} else if (config_resample == 0) {
			pw_properties_setf(mutable_props, PW_KEY_NODE_RATE, "1/%d", pipe_set_samplerate);
		} else {
			pw_properties_set(mutable_props, PW_KEY_NODE_RATE, NULL);
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

			pipe_expecting_disconnect = true;
			pw_stream_disconnect(global_stream);
			int ret = pipe_connect(loop, async, seq, _data, size, user_data);
			pipe_expecting_disconnect = false;
			return ret;
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
		if (sample_rate_src > 0) pipe_set_samplerate = sample_rate_src;
		log_msg(LOG_INFO, "SET PIPE SAMPLERATE: %d", pipe_set_samplerate);
		sample_rate_out = pipe_set_samplerate;
		// We're connecting fresh at this rate, so it's already satisfied; pump
		// only re-requests when a later track needs a different rate.
		pipe_requested_rate = pipe_set_samplerate;

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
	rg_value_current = rg_value_pending;

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

	pthread_mutex_lock(&buffer_mutex);
	rg_byte = high;
	if (get_buff_fill() == 0) {
		rg_output_base = rg_value_current;
		rg_output_correction = 1.0f;
		rg_output_correction_target = 1.0f;
		rg_output_correction_ramp_remaining = 0;
		rg_output_boundary_pending = false;
		rg_compressor_reset_state();
	} else {
		rg_output_pending_base = rg_value_current;
		rg_output_pending_correction = 1.0f;
		rg_output_boundary_pending = true;
	}
	pthread_mutex_unlock(&buffer_mutex);

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

	} else if (memcmp(peak, "DSD ", 4) == 0) {
		// With direct output the 1 bit stream goes to the device untouched,
		// otherwise FFmpeg decodes it to PCM at an eighth of the DSD bit rate
		codec = dsd_direct_wanted() ? DSD_RAW : FFMPEG;
		log_msg(LOG_INFO, "Detected DSF");
	} else if (memcmp(peak, "FRM8", 4) == 0) {
		codec = dsd_direct_wanted() ? DSD_RAW : FFMPEG;
		log_msg(LOG_INFO, "Detected DSDIFF");
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
			strcmp(ext, ".wma") == 0 || strcmp(ext, ".WMA") == 0 ||
			strcmp(ext, ".dsf") == 0 || strcmp(ext, ".DSF") == 0 ||
			strcmp(ext, ".dff") == 0 || strcmp(ext, ".DFF") == 0
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
	if (codec == DSD_RAW) {
		// Parse the container ourselves; FFmpeg cannot help here because it
		// only ever hands back PCM. If anything about the file rules out a
		// direct path (DST compression, too many channels, a malformed
		// header) quietly fall back to decoding it as PCM.
		int failed = (memcmp(peak, "FRM8", 4) == 0) ? dsd_open_dff(&dsd_info) : dsd_open_dsf(&dsd_info);
		if (failed) {
			log_msg(LOG_INFO, "pa: Falling back to PCM decode for this DSD file");
			codec = FFMPEG;
		} else if (dsd_alloc()) {
			codec = FFMPEG;
		} else {
			pthread_mutex_lock(&buffer_mutex);
			dsd_buff_reset();
			dsd_bytes_played = 0;
			dsd_active = 1;
			// The device is clocked in bytes per second, not bits
			sample_rate_src = (int) (dsd_info.rate / 8);
			src_channels = dsd_info.channels;
			pthread_mutex_unlock(&buffer_mutex);

			if (load_target_seek > 0) {
				int64_t byte = ((int64_t) load_target_seek * (dsd_info.rate / 8)) / 1000;
				byte -= byte % (dsd_info.is_dff ? 1 : dsd_info.block_size);
				if (byte < 0) byte = 0;
				if (byte > dsd_info.sample_bytes) byte = dsd_info.sample_bytes;
				dsd_info.data_pos = byte * dsd_info.channels;
				dsd_bytes_played = byte;
			}
			load_target_seek = 0;
			decoder_allocated = 1;
			return 0;
		}
	}

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
				wpc = WavpackOpenFileInputEx64(&bs_wv_reader, &bs, NULL, wv_error, OPEN_2CH_MAX | OPEN_DSD_AS_PCM, 0);
			} else {
				// Keep the path based open for local files so the .wvc
				// correction file keeps working
				bs_close();
				wpc = WavpackOpenFileInput(loaded_target_file, wv_error, OPEN_WVC | OPEN_2CH_MAX | OPEN_DSD_AS_PCM, 0);
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
			// For network streams, stop mpg123 from seeking to the end of the
			// file to read the ID3v1 tag on open. That end-seek makes the byte
			// stream abandon the in-progress linear download, fetch the last
			// 128 bytes, then restart the whole download from 0 - roughly
			// doubling start-up time. We don't use mpg123's ID3 anyway.
			if (is_net) {
				mpg123_param(mh, MPG123_ADD_FLAGS, MPG123_NO_PEEK_END, 0);
			} else {
				mpg123_param(mh, MPG123_REMOVE_FLAGS, MPG123_NO_PEEK_END, 0);
			}
			int ret = mpg123_open_handle(mh, &bs);
			if (ret != MPG123_OK) {
				log_msg(
					LOG_ERROR,
					"ph: mpg123_open failed for '%s': %s",
					loaded_target_file,
					mpg123_strerror(mh)
				);
				return 1;
			}
			decoder_allocated = 1;

			// NO_PEEK_END leaves the file size unknown; supply it so length
			// estimation and time seeking still work
			if (is_net) {
				int64_t fsz = bs_length();
				if (fsz > 0) mpg123_set_filesize(mh, (off_t) fsz);
			}

			ret = mpg123_getformat(mh, &rate, &channels, &encoding);
			if (ret != MPG123_OK) {
				log_msg(
					LOG_WARNING,
					"pa: mpg123_getformat failed for '%s': %s",
					loaded_target_file,
					mpg123_strerror(mh)
				);
				log_msg(LOG_WARNING, "ph: Attempting to find valid frames across the entire file...");
				// Change resync limit to go through the entire file instead of just first 1KB
				// This allows us to play weird polyglot or otherwise semi-broken files
				mpg123_param(mh, MPG123_RESYNC_LIMIT, -1, 0.0);
				ret = mpg123_getformat(mh, &rate, &channels, &encoding);
				if (ret != MPG123_OK) {
					log_msg(
						LOG_ERROR,
						"ph: mpg123_open failed again for '%s': %s",
						loaded_target_file,
						mpg123_strerror(mh)
					);
					return 1;
				}
			}
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
				log_msg(LOG_ERROR, "ph: encoding format not supported!");
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
	// A gapless handover swaps decoders while the buffer keeps playing, which
	// the direct DSD path cannot do: its ring still holds audio for this track
	// and the next file may need a different stream format entirely. Drain and
	// stop instead. The player normally avoids queueing across a DSD track at
	// all, so this is a backstop.
	if (dsd_active) {
		mode = ENDING;
		return;
	}
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

	#ifdef MINI
	if (config_resample == 0 && sample_rate_out != sample_rate_src) {
		if (get_buff_fill() > 0) {
			return;
		}
		log_msg(LOG_ERROR, "ph: Pump wrong samplerate");
		stop_out();
		fade_fill = 0;
		fade_position = 0;
		reset_set_value = 0;
		buff_reset();
		reconnect = true;
	}
	#endif

	#ifdef PIPE
	// Moving between PCM and raw DSD changes the stream format, not just its
	// rate, so the stream has to be torn down and reconnected. The comparison
	// is against what the live connection was asked to carry rather than what
	// it negotiated: the answer arrives asynchronously, and comparing against
	// the result would tear the stream down again on every pass while the
	// device was still making up its mind.
	int dsd_want_rate = dsd_active ? (int) (dsd_info.rate / 8) : 0;
	if ((dsd_active != 0) != pipe_dsd_requested
			|| (dsd_active && dsd_want_rate != pipe_dsd_requested_rate)) {
		// Let anything already queued play out before changing format
		if (get_buff_fill() > 0) return;
		log_msg(LOG_INFO, "ph: Reconnecting output for %s", dsd_active ? "direct DSD" : "PCM");
		fade_fill = 0;
		fade_position = 0;
		reset_set_value = 0;
		reset_set = false;
		buff_reset();
		if (dsd_active) {
			pipe_set_samplerate = dsd_want_rate;
			// Nothing about the PCM rate survives the switch, so make sure the
			// rate request below fires again on the way back
			pipe_requested_rate = 0;
		} else {
			pipe_requested_rate = sample_rate_src;
			pipe_set_samplerate = sample_rate_src;
			pipe_apply_output_rate(sample_rate_src);
		}
		pw_loop_invoke(pw_main_loop_get_loop(loop), pipe_update, SPA_ID_INVALID, NULL, 0, true, NULL);
		return;
	}

	// Direct DSD was offered but the device has not answered yet. It either
	// accepts the format or drops the stream; if it does neither, give up
	// after a moment rather than sitting on a silent stream indefinitely.
	// dsd_runtime_disabled is the signal here, not dsd_negotiation_failed,
	// which is a one-shot latch the UI consumes and clears.
	if (dsd_active && !pipe_dsd_streaming) {
		if (dsd_runtime_disabled || now_ms() - pipe_dsd_wait_start_ms >= DSD_NEGOTIATE_TIMEOUT_MS) {
			if (!dsd_runtime_disabled) {
				log_msg(LOG_ERROR, "ph: Device never accepted the direct DSD stream, falling back to PCM");
				dsd_runtime_disabled = 1;
				dsd_negotiation_failed = 1;
			}
			// Read the position while the DSD path still owns it, so playback
			// resumes where it left off rather than from the start
			int resume_ms = get_position_ms();
			stop_decoder();  // clears dsd_active and closes the byte stream
			load_target_seek = resume_ms;
			// dsd_runtime_disabled is set, so this comes back as FFMPEG, and
			// the block above brings the stream back up as PCM next pass
			if (load_next() != 0) {
				log_msg(LOG_ERROR, "ph: PCM fallback reload failed");
				mode = STOPPED;
			}
			return;
		}
		// Still negotiating. Fall through and keep filling the DSD ring so
		// playback can start the moment the device answers.
	}

	// Re-clock the device to the track's native rate once per rate. If the
	// device honours it, on_param_changed leaves sample_rate_out == src and we
	// pass through untouched; if it can't, sample_rate_out reflects the real
	// negotiated rate and the internal resampler covers the gap. Either way we
	// don't request the same rate again, so we never spin here.
	if (!dsd_active && config_resample == 0 && sample_rate_src > 0
		&& pipe_requested_rate != sample_rate_src) {
		if (get_buff_fill() > 0) {
			return;
		}
		log_msg(LOG_INFO, "ph: Requesting device samplerate %d", sample_rate_src);
		fade_fill = 0;
		fade_position = 0;
		reset_set_value = 0;
		buff_reset();
		pipe_requested_rate = sample_rate_src;
		pipe_set_samplerate = sample_rate_src;
		// The buffer is empty here, so move both audio generation and position
		// timing to the new rate. on_param_changed corrects both if negotiation
		// settles on a different rate.
		pipe_apply_output_rate(sample_rate_src);
		pw_loop_invoke(pw_main_loop_get_loop(loop), pipe_update, SPA_ID_INVALID, NULL, 0, true, NULL);
	}
	#endif

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
	} else if (codec == DSD_RAW) {

		// Takes buffer_mutex itself, only for the copy into the ring
		int got = dsd_fill_buffer();
		// -1 just means the ring is full for now, which is not end of stream
		if (got == 0) decoder_eos();

	} else if (codec == FFMPEG) {

		int b = 0;
		if (ff_read != NULL) b = ff_read(ffm_buffer, sizeof(ffm_buffer));
		else {
			log_msg(LOG_WARNING, "pa: FFmpeg read callback is NULL");
			decoder_eos();
			return;
		}

		// FFmpeg is asked for stereo float32, so 8 bytes per frame
		if (b % 8 != 0) {
			log_msg(LOG_WARNING, "pa: Uneven data");
			decoder_eos();
			return;
		}

		pthread_mutex_lock(&buffer_mutex);
		read_to_buffer_charf32(ffm_buffer, b);
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
					if (mode == PLAYING || (dsd_active && mode == ENDING)
							|| (mode == RAMP_DOWN && gate == 0)) {
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
					if ((mode == RAMP_DOWN && (gate == 0 || get_buff_fill() == 0)) || mode == PAUSED
							|| (dsd_active && mode != STOPPED)) {
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
			if ((mode == PLAYING || mode == ENDING) && dsd_active) {
				// The direct DSD path skips the ramp. A 1 bit stream cannot
				// be faded, and nothing would drive the gate to zero anyway
				// since the float buffers stay empty on this path.
				// ENDING is seekable here because the ring buffers seconds of
				// DSD, so a track enters ENDING long before it has played out;
				// refusing would make the whole tail of every track unseekable.
				decode_seek(seek_request_ms, sample_rate_src);
				reset_set = false;
				pthread_mutex_lock(&buffer_mutex);
				mode = PLAYING;
				command = NONE;
				pthread_mutex_unlock(&buffer_mutex);

			} else if (mode == PLAYING) {
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
			while (mode != ENDING) {
				// Stop once the buffer feeding the device has enough in it
				if (dsd_active) {
					if (dsd_buff_space() < DSD_READ_CHUNK) break;
				} else if (get_buff_fill() >= BUFF_SAFE) break;
				// Wait for enough network data so decoding can't block
				// the loop for long; commands stay responsive meanwhile
				if (!bs_decode_ready()) break;
				int before = pending_output_fill();
				pump_decode();
				// Headers/metadata produce no PCM, but a decoder that makes
				// no progress at all must not starve command processing
				if (pending_output_fill() == before) {
					idle_pumps++;
					if (idle_pumps > 500) break;
				} else idle_pumps = 0;
			}
		}

		if (mode == ENDING && pending_output_fill() == 0) {
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
	dsd_build_bit_reverse_table();
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

	rg_value_pending = rg;
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
		rg_value_pending = rg;
		next_ready = 1;
	}

	return 0;
}

EXPORT int pause() {
	while (command != NONE) {
		usleep(1000);
	}
	if (mode == PAUSED) return 0;
	// The fade is applied in get_audio, which the direct DSD path never
	// reaches, so gate would never fall to zero and the command would wedge.
	// A 1 bit stream cannot be faded anyway, so pause it outright. ENDING is
	// included because the DSD ring holds seconds of audio, putting a track
	// into ENDING long before it is actually over.
	if (out_thread_running && dsd_active && (mode == PLAYING || mode == ENDING)) {
		command = PAUSE;
	} else if (out_thread_running && (mode == PLAYING || mode == RAMP_DOWN)) {
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

EXPORT void replaygain_set_live(float multiplier) {
	if (!isfinite(multiplier) || multiplier <= 0.0f) multiplier = 1.0f;

	pthread_mutex_lock(&buffer_mutex);
	float base = rg_output_base;
	if (!isfinite(base) || base <= 0.0f) base = 1.0f;
	rg_output_correction_target = multiplier / base;
	int sample_rate = current_sample_rate > 0 ? current_sample_rate : 44100;
	rg_output_correction_ramp_remaining = sample_rate / 100;
	if (rg_output_correction_ramp_remaining < 1) rg_output_correction_ramp_remaining = 1;
	pthread_mutex_unlock(&buffer_mutex);
}

EXPORT void replaygain_set_pending(float multiplier) {
	if (!isfinite(multiplier) || multiplier <= 0.0f) multiplier = 1.0f;

	pthread_mutex_lock(&buffer_mutex);
	rg_value_pending = multiplier;
	if (rg_output_boundary_pending) {
		float base = rg_output_pending_base;
		if (!isfinite(base) || base <= 0.0f) base = 1.0f;
		rg_output_pending_correction = multiplier / base;
	}
	pthread_mutex_unlock(&buffer_mutex);
}

EXPORT void replaygain_set_compressor(int enabled) {
	pthread_mutex_lock(&buffer_mutex);
	rg_compressor_enabled = enabled != 0;
	if (!rg_compressor_enabled) rg_compressor_reset_state();
	pthread_mutex_unlock(&buffer_mutex);
}

EXPORT int replaygain_get_compressor_active() {
	pthread_mutex_lock(&buffer_mutex);
	int active = rg_compressor_active;
	pthread_mutex_unlock(&buffer_mutex);
	return active;
}

EXPORT float replaygain_get_compressor_reduction_db() {
	pthread_mutex_lock(&buffer_mutex);
	float reduction = 0.0f;
	if (rg_compressor_enabled && isfinite(rg_compressor_gain) && rg_compressor_gain < 1.0f) {
		reduction = 20.0f * log10f(rg_compressor_gain);
	}
	pthread_mutex_unlock(&buffer_mutex);
	return reduction;
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
	if (dsd_active) {
		// The DSD path never reaches the float buffers, so position comes
		// from the bytes handed to the device rather than position_count
		if (command == START || command == LOAD || dsd_info.rate == 0) return 0;
		return (int) ((dsd_bytes_played / (double) (dsd_info.rate / 8)) * 1000.0);
	}
	if (command != START && command != LOAD && !reset_set && current_sample_rate > 0) {
		return (int) ((position_count / (float) current_sample_rate) * 1000.0);
	} else return 0;
}

EXPORT void set_position_ms(int ms) {
	position_count = ((float)(ms / 1000.0)) * current_sample_rate;
}

EXPORT int get_length_ms() {
	if (dsd_active) {
		// Kept separate from current_length_count, which is an int and would
		// overflow on a long track at the higher DSD rates
		if (dsd_info.rate == 0) return 0;
		return (int) ((dsd_info.sample_bytes / (double) (dsd_info.rate / 8)) * 1000.0);
	}
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

// Send DSD to the device untouched rather than decoding it to PCM. Applies
// from the next track load; the current track keeps whatever path it started on.
EXPORT void config_set_dsd_direct(int n) {
	if (n != config_dsd_direct) dsd_runtime_disabled = 0;  // let the user retry
	config_dsd_direct = n;
}

// Whether this build can do direct DSD at all. The UI greys the option out
// when this is 0, which is every backend except PipeWire.
EXPORT int get_dsd_direct_supported() {
	return dsd_direct_supported();
}

// Whether the output device selected right now can take a DSD stream at all.
// The settings row uses this to tell the user before they hit play, since a
// device without native DSD input just quietly plays as PCM.
EXPORT int get_dsd_device_supported() {
	#ifdef PIPE
		return pipe_target_supports_dsd();
	#else
		return 0;
	#endif
}

// Whether the track playing right now is actually going out as raw DSD. This
// is not the same as the preference: a DST compressed file, an unusual channel
// count or a device that would not accept the format all fall back to PCM.
EXPORT int get_dsd_direct_active() {
	return dsd_active;
}

// DSD bit rate of the playing track, e.g. 2822400 for DSD64, else 0
EXPORT int get_dsd_rate() {
	return dsd_active ? (int) dsd_info.rate : 0;
}

// Raw DSD bytes per channel currently buffered. Diagnostics, and lets a test
// wait for the ring to fill rather than guessing at a sleep.
EXPORT int get_dsd_buffered_bytes() {
	return dsd_active ? dsd_buff_fill() : 0;
}

// Latched when a device refused a DSD stream, so the UI can say why playback
// went out as PCM. Reading it clears the latch.
EXPORT int get_dsd_direct_failed() {
	int v = dsd_negotiation_failed;
	dsd_negotiation_failed = 0;
	return v;
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

// The visualisers all measure the float mixing buffers, which the direct DSD
// path never touches: the 1 bit stream goes straight to the device. Left alone
// they would keep reporting whatever the last PCM track left in those buffers,
// so a DSD track plays under a meter frozen on the previous song. Report
// silence instead. Analysing the DSD itself would mean decoding it to PCM,
// which is the whole thing this output path exists to avoid.
EXPORT float get_level_peak_l() {
	if (dsd_active) return 0.0f;
	float peak = peak_l;
	peak_l = 0.0;
	return peak;
}

EXPORT float get_level_peak_r() {
	if (dsd_active) return 0.0f;
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
	// See get_level_peak_l: nothing reaches the float buffers on the direct
	// DSD path, so the FFT would just re-analyse the previous track
	if (dsd_active) {
		for (int i = 0; i < n_bins; i++) bins[i] = 0.0f;
		return 0;
	}

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

// High-resolution spectrum path for the custom-layout spectrogram widget: a
// 4096-sample window (double get_spectrum's) for finer frequency resolution,
// especially in the low end. Entirely separate buffers and FFT config
// (lazily allocated, single caller: the tauon vis thread) so the standard
// visualiser path above is unaffected.
#define SPEC_HI_N 4096
kiss_fft_scalar* rbuf_hi = NULL;
kiss_fft_cpx* cbuf_hi = NULL;
kiss_fftr_cfg ffta_hi = NULL;

EXPORT int get_spectrum_hires(int n_bins, float* bins) {
	int samples = SPEC_HI_N;
	static int hi_failed = 0;

	if (hi_failed) return 1;
	// See get_level_peak_l
	if (dsd_active) {
		for (int i = 0; i < n_bins; i++) bins[i] = 0.0f;
		return 0;
	}
	if (ffta_hi == NULL) {
		rbuf_hi = (kiss_fft_scalar*) malloc(sizeof(kiss_fft_scalar) * samples);
		cbuf_hi = (kiss_fft_cpx*) malloc(sizeof(kiss_fft_cpx) * (samples / 2 + 1));
		ffta_hi = kiss_fftr_alloc(samples, 0, 0, 0);
		if (rbuf_hi == NULL || cbuf_hi == NULL || ffta_hi == NULL) {
			log_msg(LOG_ERROR, "pa: Error allocating memory for hires spectrum");
			hi_failed = 1;
			return 1;
		}
	}

	int base = low;
	int i = 0;
	while (i < samples) {
		if (base >= watermark) {
			base = 0;
		}
		rbuf_hi[i] = bfl[base] * 0.5 * (1 - cos(2 * 3.1415926 * i / samples));
		i++;
		base += 1;
	}

	kiss_fftr(ffta_hi, rbuf_hi, cbuf_hi);

	i = 0;
	while (i < samples / 2) {
		rbuf_hi[i] = sqrt((cbuf_hi[i].r * cbuf_hi[i].r) + (cbuf_hi[i].i * cbuf_hi[i].i));
		i++;
	}

	// 11 octaves reach bin 2048 (Nyquist) for the 4096 window, as 10 did for
	// the 2048 one.
	int b0 = 0;
	for (int x = 0; x < n_bins; x++) {
		float peak = 0;
		int b1 = pow(2, x * 11.0 / (n_bins - 1));
		if (b1 > (samples / 2) - 1) b1 = (samples / 2) - 1;
		if (b1 <= b0) b1 = b0 + 1;
		for (; b0 < b1; b0++) {
			if (peak < rbuf_hi[1 + b0]) peak = rbuf_hi[1 + b0];
		}
		bins[x] = sqrt(peak);
	}

	return 0;
}

EXPORT int is_buffering() {
	if (buffering == 0) return 0;
	// Fill ratio as a percentage. Multiply before dividing so this isn't
	// truncated to 0 by integer division, and keep it non-zero (truthy)
	// for the whole time we are actually buffering.
	int pct = (int) (get_buff_fill() * 100.0 / config_min_buffer);
	if (pct < 1) pct = 1;
	if (pct > 99) pct = 99;
	return pct;
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
