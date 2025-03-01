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
#include <math.h>
#include <pthread.h>
#include <time.h>


#ifdef MINI
	#define MINIAUDIO_IMPLEMENTATION
	#define MA_NO_GENERATION
	#define MA_NO_DECODING
	#define MA_NO_ENCODING
	#define MA_ENABLE_ONLY_SPECIFIC_BACKENDS
	#define MA_ENABLE_WASAPI
	#define MA_ENABLE_PULSEAUDIO
	#define MA_ENABLE_COREAUDIO
	#define MA_ENABLE_OSS
	#define MA_ENABLE_SNDIO
	#define MA_ENABLE_AUDIO4
	//#define MA_DEBUG_OUTPUT
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

// Entry point for the module
PyMODINIT_FUNC PyInit_phazor(void) {
	return PyModule_Create(&phazor_module);
}

#define BUFF_SIZE 240000  // Decoded data buffer size
#define BUFF_SAFE 100000  // Ensure there is this much space free in the buffer

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
		pthread_mutex_lock(&pipe_devices_mutex);
		for (size_t i = 0; i < pipe_devices.device_count; i++) {
			if (pipe_devices.devices[i].id == id) { // Assuming each device has a unique ID
				// Shift remaining devices to fill the gap
				for (size_t j = i; j < pipe_devices.device_count - 1; j++) {
					pipe_devices.devices[j] = pipe_devices.devices[j + 1];
				}
				pipe_devices.device_count--;
				printf("Removed device with ID: %u\n", id);
				break;
			}
		}
		pthread_mutex_unlock(&pipe_devices_mutex);
	}

	static void registry_event_global(
		void *data, uint32_t id,
		uint32_t permissions, const char *type, uint32_t version,
		const struct spa_dict *props)
	{

		if (props == NULL || type == NULL || !spa_streq(type, PW_TYPE_INTERFACE_Node))
			return;


		//printf("object: id:%u type:%s/%d\n", id, type, version);
		const char *media_class;

		media_class = spa_dict_lookup(props, PW_KEY_MEDIA_CLASS);
		if (media_class == NULL)
			return;

		if (spa_streq(media_class, "Audio/Sink")) {

			pthread_mutex_lock(&pipe_devices_mutex);
			if (pipe_devices.device_count >= MAX_DEVICES) {
				printf("Error: Max devices\n");
				pthread_mutex_unlock(&pipe_devices_mutex);
				return;
			}
			const char *name = spa_dict_lookup(props, PW_KEY_NODE_NAME);
			const char *description = spa_dict_lookup(props, PW_KEY_NODE_DESCRIPTION);
			if (!name || !description) {
				printf("Error: Missing name or description for device\n");
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
			printf("Found audio sink: %s (%s)\n", name, description);
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

	static const struct pw_core_events core_events = {
		PW_VERSION_CORE_EVENTS,
		.done = on_core_done,
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

double t_start, t_end;

bool out_thread_running = false;
bool called_to_stop_device = false;
bool device_stopped = false;
bool signaled_device_unavailable = false;

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

FILE *d_file;

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

FILE *fptr;

struct stat st;
int load_file_size = 0;
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

// FFMPEG related -----------------------------------------------------

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
		printf("pa: FFMPEG callback is NULL\n");
		return;
	}

	if (status != 0) {
		printf("pa: Error starting FFMPEG\n");
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
	//printf("pa: SRC error code: %d\n", src_result);
	//printf("pa: SRC output frames: %lu\n", src_data.output_frames_gen);
	//printf("pa: SRC input frames used: %lu\n", src_data.input_frames_used);
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
	wave_file = fopen(filename, "rb");
	if (wave_file == NULL) {
		printf("pa: Error opening WAVE file: %s\n", strerror(errno));
		return 1;
	}

	char b[16];
	int i;

	b[15] = '\0';
	fread(b, 4, 1, wave_file);
	//printf("pa: mark: %s\n", b)

	fread(&i, 4, 1, wave_file);
	//printf("pa: size: %d\n", i);
	wave_size = i - 44;

	fread(b, 4, 1, wave_file);
	//printf("pa: head: %s\n", b);
	if (memcmp(b, "WAVE", 4) == 1) {
		printf("pa: Invalid WAVE file\n");
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
	//printf("pa: fmt : %s\n", b);

	//fread(&i, 4, 1, wave_file);
	//printf("pa: abov: %d\n", i);
	//if (i != 16) {
	//	printf("pa: Unsupported WAVE file\n");
	//	return 1;
	//}

	fread(&i, 2, 1, wave_file);
	//printf("pa: type: %d\n", i);
	if (i != 1) {
		printf("pa: Unsupported WAVE file\n");
		fclose(wave_file);
		return 1;
	}

	fread(&i, 2, 1, wave_file);
	//printf("pa: chan: %d\n", i);
	if (i != 1 && i != 2) {
		printf("pa: Unsupported WAVE channels\n");
		fclose(wave_file);
		return 1;
	}
	wave_channels = i;

	fread(&i, 4, 1, wave_file);
	//printf("pa: smpl: %d\n", i);
	wave_samplerate = i;
	sample_rate_src = i;

	fseek(wave_file, 6, SEEK_CUR);

	fread(&i, 2, 1, wave_file);
	//printf("pa: bitd: %d\n", i);
	if (i != 16) {
		printf("pa: Unsupported WAVE depth\n");
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
		//printf("label %s\n", b);
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
			printf("pa: End of WAVE file data\n");
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

	//printf("Frame size is: %d\n", frame->header.blocksize);
	//printf("Resolution is: %d\n", frame->header.bits_per_sample);
	//printf("Samplerate is: %d\n", frame->header.sample_rate);
	//printf("Channels is  : %d\n", frame->header.channels);

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
		printf("pa: critical: BUFFER OVERFLOW!");
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
			} else printf("ph: CRITIAL ERROR - INVALID BIT DEPTH!\n");

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

			} else printf("ph: CRITIAL ERROR - INVALID BIT DEPTH!\n");

			temp_fill++;
			i++;

		}

		resample_to_buffer(temp_fill);

	}

	pthread_mutex_unlock(&buffer_mutex);
	return FLAC__STREAM_DECODER_WRITE_STATUS_CONTINUE;
}

void f_meta(const FLAC__StreamDecoder *decoder, const FLAC__StreamMetadata *metadata, void *client_data) {
	printf("GOT META\n");
}

void f_err(const FLAC__StreamDecoder *decoder, FLAC__StreamDecoderErrorStatus status, void *client_data) {
	printf("GOT FLAC ERR\n");
}


FLAC__StreamDecoder *dec;
FLAC__StreamDecoderInitStatus status;

// -----------------------------------------------------------------------------------

bool pulse_connected = false;

void stop_decoder() {

	if (decoder_allocated == 0) return;

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
	decoder_allocated = 0;
}

float gate = 1.0;  // Used for ramping

int get_audio(int max, float* buff) {
		int b = 0;

		pthread_mutex_lock(&buffer_mutex);

		if (buffering == 1 && get_buff_fill() > config_min_buffer) {
			buffering = 0;
			printf("pa: Buffering -> Playing\n");
		}

		if (get_buff_fill() < 10 && loaded_target_file[0] == 'h') {

			if (mode == PLAYING) {
				if (buffering == 0) printf("pa: Buffering...\n");
				buffering = 1;
			} else buffering = 0;
		}


//		if (get_buff_fill() < max && mode == PLAYING && decoder_allocated == 1) {
//			//printf("pa: Buffer underrun\n");
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

			b = 0; // byte number

			peak_roll_l = 0;
			peak_roll_r = 0;

			//printf("pa: Buffer is at %d\n", buff_filled);

			// Fill the out buffer...
			while (get_buff_fill() > 0) {


				// Truncate data if gate is closed anyway
				if (mode == RAMP_DOWN && gate == 0) break;

//				if (want_sample_rate > 0 && sample_change_byte == buff_base) {
//					//printf("pa: Set new sample rate\n");
//					connect_pulse();
//					break;
//				}

				if (reset_set && reset_set_byte == low) {
					//printf("pa: Reset position counter\n");
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

				if (fabs(l) > peak_roll_l) peak_roll_l = fabs(l);
				if (fabs(r) > peak_roll_r) peak_roll_r = fabs(r);


				// Apply final volume adjustment
				float final_vol = pow((gate * volume_on), config_volume_power);
				l = l * final_vol;
				r = r * final_vol;

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

	static const struct pw_stream_events stream_events = {
		PW_VERSION_STREAM_EVENTS,
		.process = on_process,
	};


	void *pipewire_main_loop_thread(void *thread_id) {

		printf("Begin Pipewire init...\n");
		pw_init(NULL, NULL);

		loop = pw_main_loop_new(NULL /* properties */);
		if (loop == NULL) {
			fprintf(stderr, "Error: Failed to create main loop\n");
			return thread_id;
		}

		context = pw_context_new(
			pw_main_loop_get_loop(loop),
			NULL /* properties */,
			0 /* user_data size */);
		if (context == NULL) {
			fprintf(stderr, "Error: Failed to create context\n");
			return thread_id;
		}

		core = pw_context_connect(
			context,
			NULL /* properties */,
			0 /* user_data size */);
		if (core == NULL) {
			fprintf(stderr, "Error: Failed to connect to PipeWire\n");
			return thread_id;
		}

		registry = pw_core_get_registry(core, PW_VERSION_REGISTRY,
						0 /* user_data size */);
		if (registry == NULL) {
			fprintf(stderr, "Error: Failed to get registry\n");
			return thread_id;
		}

		spa_zero(registry_listener);
		int res;
		res = pw_registry_add_listener(registry, &registry_listener, &registry_events, NULL);

		if (res < 0) {
			fprintf(stderr, "Error: Failed to add registry listener: %s\n", spa_strerror(res));
			return thread_id;
		}

		res = pw_core_add_listener(core, &core_listener, &core_events, NULL);
		if (res < 0) {
			fprintf(stderr, "Error: Failed to add core listener: %s\n", spa_strerror(res));
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
			fprintf(stderr, "Error: Failed to create stream\n");
			return thread_id;
		}
		//printf("Run pipewire main loop...\n");
		res = pw_main_loop_run(loop);

		if (res < 0) {
			fprintf(stderr, "Error: Main loop run failed: %s\n", spa_strerror(res));
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
		//printf("Exit pipewire main loop\n");
		return thread_id;
	}
#endif


#ifdef MINI
	void data_callback(ma_device* pDevice, void* pOutput, const void* pInput, ma_uint32 frameCount) {
		get_audio(frameCount * 2, pOutput);
		//if (0 < b && b < frameCount) printf("ph: Buffer underrun\n");
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
				printf("Failed to initialize context.\n");
				return -1;
			}
			context_allocated = 1;
		}
		return 1;
	}

	void my_log_callback(void* pUserData, ma_uint32 level, const char* pMessage) {
		printf("Log [%u]: %s\n", level, pMessage);
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
	//printf("ph: Disconnect Device\n");

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
			fprintf(stderr, "Failed to build audio format parameters\n");
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
			fprintf(stderr, "Failed to get stream properties\n");
			return -EINVAL;
		}

		struct pw_properties *mutable_props = pw_properties_copy(props);
		if (mutable_props == NULL) {
			fprintf(stderr, "Failed to copy stream properties\n");
			return -ENOMEM;
		}

		// Set the target device if selected
		if (selected_index != -1) {
			pthread_mutex_lock(&pipe_devices_mutex);
			const char *device_name = pipe_devices.devices[selected_index].name;
			pthread_mutex_unlock(&pipe_devices_mutex);

			if (device_name) {
				pw_properties_set(mutable_props, PW_KEY_TARGET_OBJECT, device_name);
				printf("Selected device index: %zu (%s)\n", selected_index, device_name);
			} else {
				fprintf(stderr, "Selected device has no name\n");
				pw_properties_set(mutable_props, PW_KEY_TARGET_OBJECT, "");
			}
		} else {
			// Optionally, handle the case where no device is selected
			pw_properties_set(mutable_props, PW_KEY_TARGET_OBJECT, "");
			printf("Using default device.\n");
		}

		// Update the stream properties
		ret = pw_stream_update_properties(global_stream, &mutable_props->dict);
		if (ret < 0) {
			fprintf(stderr, "Failed to update stream properties: %d\n", ret);
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
			fprintf(stderr, "Failed to connect stream: %d\n", ret);
			return ret;
		}

		printf("Stream connected successfully.\n");
		return 0; // Success
	}

	static int pipe_update(struct spa_loop *loop, bool async, uint32_t seq,
						 const void *_data, size_t size, void *user_data) {

			pw_stream_disconnect(global_stream);
			return pipe_connect(loop, async, seq, _data, size, user_data);
	}
#endif

void connect_pulse() {

	if (pulse_connected) {
		//printf("pa: Reconnect\n");
		disconnect_pulse();
	}
	printf("ph: Connect\n");

	#ifdef MINI
		if (getenv("MA_DEBUG")) {
			ma_result result;
			ma_log logger;

			printf("Initialize logger.\n");

			// Initialize the logger
			result = ma_log_init(NULL, &logger);
			if (result != MA_SUCCESS) {
				printf("Failed to initialize logger.\n");
				return;
			}

				// Create the log callback structure
			ma_log_callback logCallback = ma_log_callback_init(my_log_callback, NULL);

			// Register the log callback
			result = ma_log_register_callback(&logger, logCallback);
			if (result != MA_SUCCESS) {
				printf("Failed to register log callback.\n");
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

		//printf("ph: Connect device\n");

		c_config.pulse.pApplicationName = "Tauon Music Box";
		if (initiate_ma_context() == -1) return;

		result = ma_context_get_devices(&context, &pPlaybackDeviceInfos, &playbackDeviceCount, NULL, NULL);
		if (result != MA_SUCCESS) {
			printf("Failed to retrieve device information.\n");
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
			printf("ph: Device init error\n");
			const char* description = ma_result_description(result);
			printf("Result Description: %s\n", description);
			mode = STOPPED;
			return;  // Failed to initialize the device.
		}

		//dev = config_output_sink;
		printf("ph: Connected using samplerate %uhz\n", device.sampleRate);

		sample_rate_out = device.sampleRate;
	#endif

	#ifdef PIPE
		int set_samplerate = 48000;
		if (sample_rate_src > 0) pipe_set_samplerate = sample_rate_src;
		printf("SET PIPE SAMPLERATE: %d\n", set_samplerate);
		sample_rate_out = pipe_set_samplerate;

		pw_loop_invoke(pw_main_loop_get_loop(loop), pipe_connect, SPA_ID_INVALID, NULL, 0, true, NULL);
	#endif

	if (decoder_allocated == 1 && current_sample_rate > 0 &&
		sample_rate_out > 0 && position_count > get_buff_fill() &&
		current_sample_rate != sample_rate_out && position_count > 0 && get_buff_fill() > 0) {

		src_reset(src);
		printf("ph: The samplerate changed, rewinding\n");
		if (!reset_set) {
			decode_seek(position_count / sample_rate_src * 1000, sample_rate_src);
		}

		buff_reset();
	}

	current_sample_rate = sample_rate_out;

	pulse_connected = true;

}

FILE *uni_fopen(char *ff) {
	#ifdef WIN64
		wchar_t w_path[MAX_PATH];
		MultiByteToWideChar(CP_UTF8, 0, ff, -1, w_path, MAX_PATH);
		FILE *file = _wfopen(w_path, L"rb");
		return file;
	#else
		return fopen(ff, "rb");
	#endif
}


int load_next() {
	// Function to load a file / prepare decoder

	stop_decoder();

	strcpy(loaded_target_file, load_target_file);

	int channels;
	int encoding;
	long rate;
	int e = 0;
	int old_sample_rate = sample_rate_src;
	src_channels = 2;

	char *ext;
	ext = strrchr(loaded_target_file, '.');

	codec = UNKNOWN;
	current_length_count = 0;
	buffering = 0;
	samples_decoded = 0;

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

	// If target is url, use FFMPEG
	if (loaded_target_file[0] == 'h') {

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


	// We need to identify the file type
	// Peak into file and try to detect signature

	if ((fptr = uni_fopen(loaded_target_file)) == NULL) {
		printf("pa: Error opening file: %s\n", strerror(errno));
		perror("Error");
		return 1;
	}

	stat(loaded_target_file, &st);
	load_file_size = st.st_size;

	fread(peak, sizeof(peak), 1, fptr);

	if (memcmp(peak, "fLaC", 4) == 0) {
		codec = FLAC;
		//printf("Detected flac\n");
	} else if (memcmp(peak, "RIFF", 4) == 0) {
		codec = FFMPEG; //WAVE;
	} else if (memcmp(peak, "OggS", 4) == 0) {
		codec = VORBIS;
		if (peak[28] == 'O' && peak[29] == 'p') codec = OPUS;
	} else if (memcmp(peak, "\xff\xfb", 2) == 0) {
		codec = MPG;
		//printf("Detected mp3\n");
	} else if (memcmp(peak, "\xff\xf3", 2) == 0) {
		codec = MPG;
		//printf("Detected mp3\n");
	} else if (memcmp(peak, "\xff\xf2", 2) == 0) {
		codec = MPG;
		//printf("Detected mp3\n");
	} else if (memcmp(peak, "\0\0\0\x20" "ftypM4A", 11) == 0) {
		codec = FFMPEG;
		//printf("Detected m4a\n");
	} else if (memcmp(peak, "\0\0\0\x18" "ftypdash", 12) == 0) {
		codec = FFMPEG;
		//printf("Detected m4a\n");
	} else if (memcmp(peak, "\0\0\0\x18" "ftypiso5", 12) == 0) {
		codec = FFMPEG;
		//printf("Detected m4a\n");
	} else if (memcmp(peak, "\x30\x26\xb2\x75\x8e\x66\xcf\x11", 8) == 0) {
		codec = FFMPEG;
		//printf("Detected wma\n");
	} else if (memcmp(peak, "MAC\x20", 4) == 0) {
		codec = FFMPEG;
		//printf("Detected ape\n");
	} else if (memcmp(peak, "TTA1", 4) == 0) {
		codec = FFMPEG;
		//printf("Detected tta\n");
	} else if (memcmp(peak, "wvpk", 4) == 0) {
		codec = WAVPACK;
		printf("Detected wavpack\n");

	} else if (memcmp(peak, "\x49\x44\x33", 3) == 0) {
		int id3_size = (peak[6] << 21) | (peak[7] << 14) | (peak[8] << 7) | peak[9];
		fseek(fptr, id3_size + 10, SEEK_SET);
		codec = MPG;
		unsigned char flac_marker[4];
		if (fread(flac_marker, 1, 4, fptr) == 4 && memcmp(flac_marker, "fLaC", 4) == 0) {
			codec = FLAC;
			printf("Detected FLAC with ID3 header\n");
		}
	}
	fclose(fptr);

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
		printf("pa: Decode using FFMPEG\n");
	}

	// Start decoders
	if (codec == FFMPEG) {
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
		gme_open_file(loaded_target_file, &emu, (long) sample_rate_src);
		gme_start_track(emu, subtrack);

		if (load_target_seek > 0) gme_seek(emu, (long) load_target_seek);

		if (old_sample_rate != sample_rate_src) {
			src_reset(src);
		}

		pthread_mutex_unlock(&buffer_mutex);
		decoder_allocated = 1;

		return 0;

	}

	if (codec == MPT) {
		mod_file = uni_fopen(loaded_target_file);
		mod = openmpt_module_create2(openmpt_stream_get_file_callbacks2(), mod_file, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
		src_channels = 2;
		fclose(mod_file);

		if (mod == NULL) {
			printf("pa: Error creating MPT modules\n");
			return 1;
		}
		pthread_mutex_lock(&buffer_mutex);
		sample_rate_src = 48000;
		current_length_count = openmpt_module_get_duration_seconds(mod) * 48000;

		if (old_sample_rate != sample_rate_src) {
			src_reset(src);
		}

		if (load_target_seek > 0) {
			// printf("pa: Start at position %d\n", load_target_seek);
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

			opus_dec = op_open_file(loaded_target_file, &e);
			decoder_allocated = 1;

			if (e != 0) {
				printf("pa: Error reading ogg file (expecting opus)\n");
				printf("pa: %d\n", e);
				printf("pa: %s\n", loaded_target_file);
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
					// printf("pa: Start at position %d\n", load_target_seek);
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
			d_file = uni_fopen(loaded_target_file);
			if (d_file == NULL) {
				printf("pa: Error opening VORBIS file: %s\n", strerror(errno));
				return 1;
			}
			//e = ov_fopen(loaded_target_file, &vf);
			e = ov_open(d_file, &vf, NULL, 0);
			decoder_allocated = 1;
			if (e != 0) {
				printf("pa: Error reading ogg file (expecting vorbis)\n");
				fclose(d_file);

				return 1;
			} else {

				vi = *ov_info(&vf, -1);

				pthread_mutex_lock(&buffer_mutex);
				//printf("pa: Vorbis samplerate is %lu\n", vi.rate);

				sample_rate_src = vi.rate;
				src_channels = vi.channels;

				if (old_sample_rate != sample_rate_src) {
					src_reset(src);
				}

				current_length_count = ov_pcm_total(&vf, -1);

				if (load_target_seek > 0) {
					//printf("pa: Start at position %d\n", load_target_seek);
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
			d_file = uni_fopen(loaded_target_file);
			if (FLAC__stream_decoder_init_FILE(
					dec,
					d_file,
					&f_write,
					NULL, //&f_meta,
					&f_err,
					0) == FLAC__STREAM_DECODER_INIT_STATUS_OK) {

				decoder_allocated = 1;
				flac_got_rate = 0;

				return 0;

			} else {
				FLAC__stream_decoder_delete(dec);
				fclose(d_file);
				return 1;
			}

			break;

		case WAVPACK:
			wpc = WavpackOpenFileInput(loaded_target_file, NULL, OPEN_WVC | OPEN_2CH_MAX, 0);
			if (wpc == NULL) {
				printf("pa: Error loading wavpak file\n");
				WavpackCloseFile(wpc);
				return 1;
			}
			src_channels = WavpackGetReducedChannels(wpc);
			sample_rate_src = WavpackGetSampleRate(wpc);
			if (old_sample_rate != sample_rate_src) {
				src_reset(src);
			}
			wp_bit = WavpackGetBitsPerSample(wpc);
			if (! (wp_bit == 16 || wp_bit == 24)) {
				printf("pa: wavpak bit depth not supported\n");
				WavpackCloseFile(wpc);
				return 1;
			}
			wp_float = 0;
			if (WavpackGetMode(wpc) & MODE_FLOAT) {
				wp_float = 1;
				printf("pa: wavpak float mode not implemented");
				return 1;
			}

			current_length_count = WavpackGetNumSamples(wpc);
			return 0;
			break;

		case MPG:
			mpg123_open(mh, loaded_target_file);
			decoder_allocated = 1;

			mpg123_getformat(mh, &rate, &channels, &encoding);
			mpg123_scan(mh);
			//printf("pa: %lu. / %d. / %d\n", rate, channels, encoding);

			pthread_mutex_lock(&buffer_mutex);

			sample_rate_src = rate;
			src_channels = channels;
			if (old_sample_rate != sample_rate_src) {
				src_reset(src);
			}
			current_length_count = (unsigned int) mpg123_length(mh);

			if (encoding == MPG123_ENC_SIGNED_16) {

				if (load_target_seek > 0) {
					//printf("pa: Start at position %d\n", load_target_seek);
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
				printf("pa: ERROR, encoding format not supported!\n");
				pthread_mutex_unlock(&buffer_mutex);
				return 1;
			}

			break;
	}
	return 1;
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
	//printf("pa: End of stream\n");
	if (next_ready == 1) {
		//printf("pa: Read next gapless\n");
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
		printf("ph: Pump wrong samplerate\n");

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
					decoder_eos();
					break;

				default:
					FLAC__stream_decoder_process_single(dec);

			}

			if (load_target_seek > 0 && flac_got_rate == 1) {
				//printf("pa: Set start position %d\n", load_target_seek);

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
			unsigned int done;

			if (src_channels == 1) {
				done = op_read(opus_dec, opus_buffer, 4096, NULL);
			}
			else done = op_read_stereo(opus_dec, opus_buffer, 1024 * 2) * 2;

			pthread_mutex_lock(&buffer_mutex);
			read_to_buffer_s16int(opus_buffer, done);
			samples_decoded += done;

			pthread_mutex_unlock(&buffer_mutex);
			if (done == 0) {

				// Check if file was appended to...
				stat(loaded_target_file, &st);
				if (load_file_size != st.st_size) {
					printf("pa: Ogg file size changed!\n");
					int e = 0;
					op_free(opus_dec);
					opus_dec = op_open_file(loaded_target_file, &e);
					op_pcm_seek(opus_dec, samples_decoded / 2);
					return;
				}

				decoder_eos();
			}
		}


	} else if (codec == VORBIS) {

		unsigned int done;
		int stream;
		done = ov_read(&vf, parse_buffer, 2048 * 2, 0, 2, 1, &stream);

		pthread_mutex_lock(&buffer_mutex);
		read_to_buffer_char16(parse_buffer, done);
		pthread_mutex_unlock(&buffer_mutex);
		if (done == 0) decoder_eos();

	} else if (codec == WAVPACK) {
		if (wpc != NULL) {
			int samples;
			int32_t buffer[4 * 1024 * 2];
			samples = WavpackUnpackSamples(wpc, buffer, 1024);
			if (wp_bit == 16) {
				read_to_buffer_16in32_fs(buffer, samples);
			} else if (wp_bit == 24) {
				read_to_buffer_24in32_fs(buffer, samples);
			}
			samples_decoded += samples;
		}

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
			printf("pa: FFMPEG read callback is NULL\n");
			decoder_eos();
			return;
		}

		if (b % 4 != 0) {
			printf("pa: Uneven data\n");
			decoder_eos();
			return;
		}

		pthread_mutex_lock(&buffer_mutex);
		read_to_buffer_char16(ffm_buffer, b);
		pthread_mutex_unlock(&buffer_mutex);
		if (b == 0) {
			printf("pa: FFMPEG has finished\n");
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
		printf("pa: Error allocating memory for rbuf\n");
		return thread_id;
	}
	cbuf = (kiss_fft_cpx*)malloc(sizeof(kiss_fft_cpx) * (2048/2+1) );
	if (cbuf == NULL) {
		printf("pa: Error allocating memory for cbuf\n");
		free(rbuf);
		return thread_id;
	}
	ffta = kiss_fftr_alloc(2048 ,0 ,0,0 );
	if (ffta == NULL) {
		printf("pa: Error allocating memory for ffta\n");
		free(rbuf);
		free(cbuf);
		return thread_id;
	}

	int error = 0;

	int load_result = 0;
	bool using_fade = false;

	// SRC ----------------------------

	src = src_new(config_resample_quality, 2, &error);
	if (src == NULL) {
		printf("pa: Error creating SRC state\n");
		free(rbuf);
		free(cbuf);
		kiss_fftr_free(ffta);
		return thread_id;
	}
	// printf("pa: SRC error code %d", error);
	error = 0;

	// MP3 decoder --------------------------------------------------------------

	mpg123_init();
	mh = mpg123_new(NULL, &error);

	mpg123_param(mh, MPG123_ADD_FLAGS, MPG123_QUIET | MPG123_SKIP_ID3V2, 0);
	mpg123_param(mh, MPG123_RESYNC_LIMIT, 10000, 0);

	// FLAC decoder ----------------------------------------------------------------

	dec = FLAC__stream_decoder_new();

	// ---------------------------------------------

	// PIPEWIRE -----------
	#ifdef PIPE
		printf("Start pipewire thread...\n");
		enum_done = 0;
		if (pthread_create(&pw_thread, NULL, pipewire_main_loop_thread, NULL) != 0) {
				fprintf(stderr, "Failed to create Pipewire main loop thread\n");
				return thread_id;
		}
		printf("Done Pipewire prep, wait for ready event...\n");
		while (enum_done != 1) {
			usleep(10000);
		}
		printf("Pipewire load done.\n");
	#endif
	//int test1 = 0;
	// Main loop ---------------------------------------------------------------
	while (true) {

//		test1++;
//		if (test1 > 650) {
//			printf("pa: Status: mode %d, command %d, buffer %d, gate %f\n", mode, command, get_buff_fill(), gate);
//			test1 = 0;
//		}

		if (device_stopped && !called_to_stop_device && !signaled_device_unavailable) {
			printf("Device was unplugged or became unavailable.\n");
			on_device_unavailable();
			signaled_device_unavailable = true;
		}

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
					} else if (mode == PLAYING) {
						mode = RAMP_DOWN;
					}
					if ((mode == RAMP_DOWN && (gate == 0 || get_buff_fill() == 0)) || mode == PAUSED) {
						end();
					}
					break;
				case START:
					if (mode == PLAYING) {
						mode = RAMP_DOWN;
					}
					if (mode == RAMP_DOWN && gate == 0) {
						command = LOAD;
					} else break;

				case LOAD:

					// Prepare for a crossfade if enabled and suitable
					using_fade = false;
					if (config_fade_jump == 1 && mode == PLAYING) {
						pthread_mutex_lock(&buffer_mutex);
						if (fade_fill > 0) {
							printf("pa: Fade already in progress\n");
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

					load_result = load_next();

					if (!using_fade) {
						// Jump immediately
						//printf("ph: Jump\n");
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
						printf("ph: Load file failed\n");
						result_status = FAILURE;
						command = NONE;
						mode = STOPPED;
					}

					break;

			} // end switch
		} // end if none


		if (command == SEEK) {
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
				printf("pa: fixme - cannot seek at this time\n");
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

		// Refill the buffer
		if (mode == PLAYING && codec != FEED) {
			while (get_buff_fill() < BUFF_SAFE && mode != ENDING) {
				pump_decode();
			}
		}

		if (mode == ENDING && get_buff_fill() == 0) {
			//printf("pa: Buffer ran out at end of track\n");
			end();
		}
		if (mode == ENDING && next_ready == 1) {
			//printf("pa: Next registered while buffer was draining\n");
			//printf("pa: -- remaining was %d\n", get_buff_fill());
			mode = PLAYING;
		}

		usleep(5000);
	}

	//printf("pa: Cleanup and exit\n");

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
	printf("Exit PHAzOR\n");
	return thread_id;
}


// ---------------------------------------------------------------------------------------
// Begin exported functions

EXPORT int scan_devices() {
	#ifdef MINI
		if (initiate_ma_context() == -1) return -1;
		result = ma_context_get_devices(&context, &pPlaybackDeviceInfos, &playbackDeviceCount, NULL, NULL);
		if (result != MA_SUCCESS) {
			printf("Failed to retrieve device information.\n");
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
	//printf("ph: PHAzOR starting up\n");
	if (main_running == 0) {
		main_running = 1;
		pthread_t main_thread_id;
		pthread_create(&main_thread_id, NULL, main_loop, NULL);
	} else printf("ph: Cannot init. Main loop already running!\n");
	return 0;
}

EXPORT int get_status() {
	return mode;
}

EXPORT int get_result() {
	return result_status;
}

EXPORT int start(char *filename, int start_ms, int fade, float rg) {

	while (command != NONE) {
		usleep(1000);
	}

	result_status = WAITING;

	rg_value_want = rg;
	config_fade_jump = fade;

	load_target_seek = start_ms;
	strcpy(load_target_file, filename);

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
	while (command != NONE) {
		usleep(1000);
	}
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
	printf("command is %d, mode is %d, gate is %f\n", command, mode, gate);
}

EXPORT int phazor_shutdown() {
	while (command != NONE) {
		usleep(1000);
	}
	command = EXIT;
	return 0;
}
