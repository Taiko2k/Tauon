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

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <math.h>
#include <pthread.h>
#include <time.h>

#ifdef AO
#include <ao/ao.h>
#else
#include <pulse/simple.h>
#include <pulse/error.h>
#endif

#include <FLAC/stream_decoder.h>
#include <mpg123.h>
#include "vorbis/codec.h"
#include "vorbis/vorbisfile.h"
#include "opusfile.h"
#include <sys/stat.h>
#include <samplerate.h>
#include <libopenmpt/libopenmpt.h>
#include <libopenmpt/libopenmpt_stream_callbacks_file.h>
#include "kissfft/kiss_fftr.h"
#include "wavpack/wavpack.h"

#define BUFF_SIZE 240000  // Decoded data buffer size
#define BUFF_SAFE 100000  // Ensure there is this much space free in the buffer
#define BUFFER_STREAM_READY 30000

float bfl[BUFF_SIZE];
float bfr[BUFF_SIZE];
int low = 0;
int high = 0;
int high_mark = BUFF_SIZE - BUFF_SAFE;
int watermark = BUFF_SIZE - BUFF_SAFE;

int get_buff_fill(){
    if (low <= high) return high - low;
    return (watermark - low) + high;
}

void buff_cycle(){
    if (high > high_mark){
        watermark = high;
        high = 0;
    }
    if (low >= watermark) low = 0;
}

void buff_reset(){
    low = 0;
    high = 0;
    watermark = high_mark;
}

double t_start, t_end;

int out_thread_running = 0; // bool

float fadefl[BUFF_SIZE];
float fadefr[BUFF_SIZE];

int16_t temp16l[BUFF_SIZE];
int16_t temp16r[BUFF_SIZE];

float re_in[BUFF_SIZE * 2];
float re_out[BUFF_SIZE * 2];

int fade_fill = 0;
int fade_position = 0;
int fade_2_flag = 0;

pthread_mutex_t buffer_mutex;
pthread_mutex_t fade_mutex;
//pthread_mutex_t pulse_mutex;

float out_buff[2048 * 2];

#ifdef AO
char out_buffc[2048 * 4];
int32_t temp32 = 0;
#endif

int position_count = 0;
int current_length_count = 0;

int sample_rate_out = 48000;
int sample_rate_src = 0;
int src_channels = 2;

int current_sample_rate = 0;
int want_sample_rate = 0;
int sample_change_byte = 0;

int reset_set = 0;
int reset_set_value = 0;
int reset_set_byte = 0;

int rg_set = 0;
int rg_byte = 0;
float rg_value_want = 0.0;
float rg_value_on = 0.0;


char load_target_file[4096]; // 4069 bytes for max linux filepath
char loaded_target_file[4096] = ""; // 4069 bytes for max linux filepath

unsigned int load_target_seek = 0;
unsigned int next_ready = 0;
unsigned int seek_request_ms = 0;

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
int config_dev_buffer = 40;
int config_fade_jump = 1;
char config_output_sink[256]; // 256 just a conservative guess
int config_fade_duration = 700;
int config_resample_quality = 2;
int config_always_ffmpeg = 0;
int config_volume_power = 2;

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

// Misc ----------------------------------------------------------

float ramp_step(int sample_rate, int milliseconds) {
    return 1.0 / sample_rate / (milliseconds / 1000.0);
}

void fade_fx() {
    pthread_mutex_lock(&fade_mutex);
    if (fade_fill > 0) {
        if (fade_fill == fade_position) {
            fade_fill = 0;
            fade_position = 0;
        } else {

            float cross = fade_position / (float) fade_fill;
            float cross_i = 1.0 - cross;

            bfl[high] *= cross;
            bfl[high] += fadefl[fade_position] * cross_i;

            bfr[high] *= cross;
            bfr[high] += fadefr[fade_position] * cross_i;
            fade_position++;
        }
    }
    pthread_mutex_unlock(&fade_mutex);
}

FILE *fptr;

struct stat st;
int load_file_size = 0;
int samples_decoded = 0;

// AO --------------

#ifdef AO
ao_device *device;
ao_sample_format format;
#endif
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

// Pulseaudio ---------------------------------------------------------
#ifndef AO
pa_simple *s;
pa_sample_spec ss;
pa_buffer_attr pab;
#endif
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

// FFMPEG related -----------------------------------------------------

FILE *ffm;
char exe_string[4096];
char ffm_buffer[2048];

void start_ffmpeg(char uri[], int start_ms) {
    if (start_ms > 0)
        sprintf(exe_string, "ffmpeg -loglevel quiet -ss %dms -i \"%s\" -acodec pcm_s16le -f s16le -ac 2 -ar %d - ",
                start_ms, uri, sample_rate_out);
    else sprintf(exe_string, "ffmpeg -loglevel quiet -i \"%s\" -acodec pcm_s16le -f s16le -ac 2 -ar %d - ", uri, sample_rate_out);

    ffm = popen(exe_string, "r");
    if (ffm == NULL) {
        printf("pa: Error starting FFMPEG\n");
        return;
    }
    decoder_allocated = 1;
}

void stop_ffmpeg() {
    //printf("pa: Stop FFMPEG\n");
    pclose(ffm);
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

        //buffl[(buff_filled + buff_base) % BUFF_SIZE] = re_out[i * 2];
        //buffr[(buff_filled + buff_base) % BUFF_SIZE] = re_out[(i * 2) + 1];
        bfl[high] = re_out[i * 2];
        bfr[high] = re_out[(i * 2) + 1];

        if (fade_fill > 0) {
            fade_fx();
        }

        high += 1;
        //buff_filled++;
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
        return 1;
    }

    while (1) {

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
    //    printf("pa: Unsupported WAVE file\n");
    //    return 1;
    //}

    fread(&i, 2, 1, wave_file);
    //printf("pa: type: %d\n", i);
    if (i != 1) {
        printf("pa: Unsupported WAVE file\n");
        return 1;
    }

    fread(&i, 2, 1, wave_file);
    //printf("pa: chan: %d\n", i);
    if (i != 1 && i != 2) {
        printf("pa: Unsupported WAVE channels\n");
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
        return 1;
    }
    wave_depth = i;
    fseek(wave_file, wave_start + wave_size, SEEK_SET);

    while (1) {

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
    int end = 0;
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
            end = 1;
            break;
        }

    }

    if (sample_rate_src != sample_rate_out){
        resample_to_buffer(frames_read);
    } else {

        i = 0;
        while (i < frames_read){

            bfl[high] = re_in[i * 2];
            bfr[high] = re_in[i * 2 + 1];

            if (fade_fill > 0) {
                fade_fx();
            }

            //buff_filled++;
            high++;
            samples_decoded++;
            i++;
        }
        buff_cycle();
    }
    if (end == 1) return 1;
    return 0;

}

int wave_seek(int frame_position) {
    return fseek(wave_file, (frame_position * 4) + wave_start, SEEK_SET);
}

void wave_close() {
    fclose(wave_file);
}

void read_to_buffer_24in32_fs(int32_t src[], int n_samples){
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

void read_to_buffer_16in32_fs(int32_t src[], int n_samples){
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
        re_in[f * 2] = ( ((src[i + 1] << 8) | (src[i + 0] & 0xFF))) / 32768.0;
        if (src_channels == 1) {
            re_in[(f * 2) + 1] = re_in[f * 2];
            i += 2;
        } else {
            re_in[(f * 2) + 1] = (((src[i + 3] << 8) | (src[i + 2] & 0xFF))) / 32768.0;
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
    if (src_channels == 1){
        while (i < n_bytes) {
            bfl[high] = ((src[i + 1] << 8) | (src[i + 0] & 0xFF)) / 32768.0;
            bfr[high] = bfl[high];
            if (fade_fill > 0) {
                fade_fx();
            }
            high++;
            i += 2;
        }
    } else {
        while (i < n_bytes) {
            bfl[high] = (((src[i + 1] << 8) | (src[i + 0] & 0xFF)) / 32768.0);
            bfr[high] = (((src[i + 3] << 8) | (src[i + 2] & 0xFF)) / 32768.0);
            if (fade_fill > 0) {
                fade_fx();
            }
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

void read_to_buffer_s16int(int16_t src[], int n_samples){

    if (sample_rate_src != sample_rate_out) {
        read_to_buffer_s16int_resample(src, n_samples);
        return;
    }

    int i = 0;
    if (src_channels == 1){
        while (i < n_samples){
            bfl[high] = src[i] / 32768.0;
            bfr[high] = bfl[high];
            if (fade_fill > 0) {
                fade_fx();
            }
            i+=1;
            //buff_filled++;
            high++;
        }
        buff_cycle();

    } else {
        while (i < n_samples){
            bfl[high] = src[i] / 32768.0;
            bfr[high] = src[i + 1] / 32768.0;
            if (fade_fill > 0) {
                fade_fx();
            }
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

    /* if (frame->header.sample_rate != current_sample_rate){ */
    /*   if (want_sample_rate != frame->header.sample_rate){ */
    /*     want_sample_rate = frame->header.sample_rate; */
    /*     sample_change_byte = (buff_filled + buff_base) % BUFF_SIZE; */
    /*   } */
    /* } */

    if (sample_rate_out != current_sample_rate) {
        if (want_sample_rate != sample_rate_out) {
            want_sample_rate = sample_rate_out;
            sample_change_byte = high;
        }
    }

    if (current_length_count == 0) {
        current_length_count = FLAC__stream_decoder_get_total_samples(decoder);
    }


    unsigned int i = 0;
    int resample = 0;
    sample_rate_src = frame->header.sample_rate;
    flac_got_rate = 1;
    if (sample_rate_src != sample_rate_out) {
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

            if (fade_fill > 0) {
                fade_fx();
            }

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

int pulse_connected = 0;
int want_reconnect = 0;

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
    }
    src_reset(src);
    decoder_allocated = 0;
}


int disconnect_pulse() {

    if (pulse_connected == 1) {

        #ifdef AO
            ao_close(device);
        #else
            printf("pa: Disconnect from PulseAudio\n");
            pa_simple_free(s);
        #endif


    }
    pulse_connected = 0;
    return 0;
}


void connect_pulse() {

    if (pulse_connected == 1) {
        printf("pa: reconnect pulse\n");
        disconnect_pulse();
    }
    printf("pa: Connect pulse\n");

    if (want_sample_rate > 0) {
        current_sample_rate = want_sample_rate;
        want_sample_rate = 0;
    }

//    if (current_sample_rate <= 1) {
//        printf("pa: Samplerate detection warning.\n");
//        return;
//    }
    current_sample_rate = sample_rate_out;

    #ifndef AO
    int error = 0;
    char *dev = NULL;
    if (strcmp(config_output_sink, "Default") != 0) {
        dev = config_output_sink;
    }

    pab.maxlength = (current_sample_rate * 8 * (config_dev_buffer / 1000.0));
    pab.fragsize = (uint32_t) - 1;
    pab.minreq = (uint32_t) - 1;
    pab.prebuf = (uint32_t) - 1;
    pab.tlength = (current_sample_rate * 4 * (config_dev_buffer / 1000.0));

    //printf("pa: Connect to PulseAudio\n");
    //ss.format = PA_SAMPLE_S16LE;
    ss.format = PA_SAMPLE_FLOAT32NE;
    ss.channels = 2;
    ss.rate = current_sample_rate;

    s = pa_simple_new(NULL,                // Use default server
                      "Tauon Music Box",   // Application name
                      PA_STREAM_PLAYBACK,  // Flow direction
                      dev, //NULL,                // Use the default device
                      "Music",             // Description
                      &ss,                 // Format
                      NULL,                // Channel map
                      &pab,                // Buffering attributes
                      &error               // Error
    );

    if (error != 0) {
        printf("pa: PulseAudio init error\n");
        //printf(pa_strerror(error));
        //printf("\n");
        mode = STOPPED;
    } else pulse_connected = 1;

    #else

	int default_driver = ao_default_driver_id();

    memset(&format, 0, sizeof(format));
	format.bits = 32;
	format.channels = 2;
	format.rate = current_sample_rate;
	format.byte_format = AO_FMT_LITTLE;

    ao_option option;
    option.key = "buffer_time";
    option.value = "100";

	/* -- Open driver -- */
	device = ao_open_live(default_driver, &format, &option);

	if (device == NULL) {
		fprintf(stderr, "Error opening device.\n");
	}
    pulse_connected = 1;
    usleep(50000);

    #endif
    //src_reset(src);
    //pthread_mutex_unlock(&pulse_mutex);

}

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
    }
}

int load_next() {
    // Function to load a file / prepare decoder

    stop_decoder();

    strcpy(loaded_target_file, load_target_file);

    int channels;
    int encoding;
    long rate;
    int e = 0;

    char *ext;
    ext = strrchr(loaded_target_file, '.');

    codec = UNKNOWN;
    current_length_count = 0;
    buffering = 0;
    samples_decoded = 0;

    if (loaded_target_file[0] == 'h') buffering = 1;

    rg_set = 1;
    rg_byte = high;

    char peak[35];

    if (strcmp(loaded_target_file, "RAW FEED") == 0){
        codec = FEED;
        load_target_seek = 0;
        pthread_mutex_lock(&buffer_mutex);
        if (current_sample_rate != sample_rate_out) {
            sample_change_byte = high;
            want_sample_rate = sample_rate_out;
        }
        sample_rate_src = sample_rate_out;
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
        if (current_sample_rate != sample_rate_out) {
            sample_change_byte = high;
            want_sample_rate = sample_rate_out;
        }
        pthread_mutex_unlock(&buffer_mutex);

        return 0;
    }

    // We need to identify the file type
    // Peak into file and try to detect signature
    if ((fptr = fopen(loaded_target_file, "rb")) == NULL) {
        printf("pa: Error opening file\n");
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
    } else if (memcmp(peak, "\0\0\0\x20" "ftypM4A", 11) == 0) {
        codec = FFMPEG;
        //printf("Detected m4a\n");
    } else if (memcmp(peak, "\xff\xfb", 2) == 0) {
        codec = MPG;
        //printf("Detected mp3\n");
    } else if (memcmp(peak, "\xff\xf3", 2) == 0) {
        codec = MPG;
        //printf("Detected mp3\n");
    } else if (memcmp(peak, "\xff\xf2", 2) == 0) {
        codec = MPG;
        //printf("Detected mp3\n");
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
        codec = MPG;
        char peak2[10000];
        memset(peak2, 0, sizeof(peak2));
        rewind(fptr);
        fread(peak2, sizeof(peak2), 1, fptr);
        if (memmem(peak2, sizeof(peak2), "fLaC", 4) != NULL){
          codec = FLAC;
          printf("ph: Detected FLAC with id3 header\n");
        }
        //printf("Detected mp3 id3\n");
    }
    fclose(fptr);

    // Fallback to detecting using file extension
    if (codec == UNKNOWN && ext != NULL && (
            strcmp(ext, ".ape") == 0 || strcmp(ext, ".APE") == 0 ||
            strcmp(ext, ".m4a") == 0 || strcmp(ext, ".M4A") == 0 ||
            strcmp(ext, ".tta") == 0 || strcmp(ext, ".TTA") == 0 ||
            strcmp(ext, ".wma") == 0 || strcmp(ext, ".WMA") == 0
                            )
        ) codec = FFMPEG;

    if (codec == UNKNOWN && ext != NULL && (
            (strcmp(ext, ".xm") == 0 || strcmp(ext, ".XM") == 0 ||
             strcmp(ext, ".s3m") == 0 || strcmp(ext, ".S3M") == 0 ||
             strcmp(ext, ".it") == 0 || strcmp(ext, ".IT") == 0 ||
             strcmp(ext, ".mptm") == 0 || strcmp(ext, ".MPTM") == 0 ||
             strcmp(ext, ".mod") == 0 || strcmp(ext, ".MOD") == 0)
                            )
            ) codec = MPT;

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
    if (codec == FFMPEG){
        start_ffmpeg(loaded_target_file, load_target_seek);
        load_target_seek = 0;
        pthread_mutex_lock(&buffer_mutex);
        if (current_sample_rate != sample_rate_out) {
            sample_change_byte = high;
            want_sample_rate = sample_rate_out;
        }
        pthread_mutex_unlock(&buffer_mutex);
        return 0;
    }

    if (codec == MPT){

      mod_file = fopen(loaded_target_file, "rb");
      mod = openmpt_module_create2(openmpt_stream_get_file_callbacks(), mod_file, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
      src_channels = 2;
      fclose(mod_file);
      pthread_mutex_lock(&buffer_mutex);
      sample_rate_src = 48000;
      current_length_count = openmpt_module_get_duration_seconds(mod) * 48000;

      if (current_sample_rate != sample_rate_out) {
            sample_change_byte = high;
            want_sample_rate = sample_rate_out;
                }

      if (load_target_seek > 0) {
                    // printf("pa: Start at position %d\n", load_target_seek);
          openmpt_module_set_position_seconds(mod, load_target_seek / 1000.0);
          reset_set_value =  48000 * (load_target_seek / 1000.0);
          samples_decoded = reset_set_value * 2;
          reset_set = 1;
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
            //if (current_sample_rate != wave_samplerate) {
            //    sample_change_byte = (buff_filled + buff_base) % BUFF_SIZE;
            //    want_sample_rate = wave_samplerate;
            //}

            if (load_target_seek > 0) {
                reset_set_value = (int) wave_samplerate * (load_target_seek / 1000.0);
                reset_set = 1;
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

                if (current_sample_rate != sample_rate_out) {
                    sample_change_byte = high;
                    want_sample_rate = sample_rate_out;
                }

                current_length_count = op_pcm_total(opus_dec, -1);

                if (load_target_seek > 0) {
                    // printf("pa: Start at position %d\n", load_target_seek);
                    op_pcm_seek(opus_dec, (int) 48000 * (load_target_seek / 1000.0));
                    reset_set_value = op_raw_tell(opus_dec);
                    samples_decoded = reset_set_value * 2;
                    reset_set = 1;
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

            e = ov_fopen(loaded_target_file, &vf);
            decoder_allocated = 1;
            if (e != 0) {
                printf("pa: Error reading ogg file (expecting vorbis)\n");

                return 1;
            } else {

                vi = *ov_info(&vf, -1);

                pthread_mutex_lock(&buffer_mutex);
                //printf("pa: Vorbis samplerate is %lu\n", vi.rate);

                sample_rate_src = vi.rate;
                src_channels = vi.channels;

                if (current_sample_rate != sample_rate_out) {
                    sample_change_byte = high;
                    want_sample_rate = sample_rate_out;
                }

                current_length_count = ov_pcm_total(&vf, -1);

                if (load_target_seek > 0) {
                    //printf("pa: Start at position %d\n", load_target_seek);
                    ov_pcm_seek(&vf, (ogg_int64_t) vi.rate * (load_target_seek / 1000.0));
                    reset_set_value = vi.rate * (load_target_seek / 1000.0); // op_pcm_tell(opus_dec); that segfaults?
                    //reset_set_value = 0;
                    reset_set = 1;
                    reset_set_byte = high;
                    load_target_seek = 0;
                }
                pthread_mutex_unlock(&buffer_mutex);
                return 0;

            }

            break;
        case FLAC:
            if (FLAC__stream_decoder_init_file(
                    dec,
                    loaded_target_file,
                    &f_write,
                    NULL, //&f_meta,
                    &f_err,
                    0) == FLAC__STREAM_DECODER_INIT_STATUS_OK) {

                decoder_allocated = 1;
                flac_got_rate = 0;

                return 0;

            } else return 1;

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
            wp_bit = WavpackGetBitsPerSample(wpc);
            if (! (wp_bit == 16 || wp_bit == 24)){
                printf("pa: wavpak bit depth not supported\n");
                WavpackCloseFile(wpc);
                return 1;
            }
            wp_float = 0;
            if (WavpackGetMode(wpc) & MODE_FLOAT){
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
            if (current_sample_rate != sample_rate_out) {
                sample_change_byte = high;
                want_sample_rate = sample_rate_out;
            }
            current_length_count = (u_int) mpg123_length(mh);

            if (encoding == MPG123_ENC_SIGNED_16) {

                if (load_target_seek > 0) {
                    //printf("pa: Start at position %d\n", load_target_seek);
                    mpg123_seek(mh, (int) rate * (load_target_seek / 1000.0), SEEK_SET);
                    reset_set_value = mpg123_tell(mh);
                    reset_set = 1;
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
    //buff_base = 0;
    //buff_filled = 0;
    buff_reset();
    buffering = 0;
    pthread_mutex_unlock(&buffer_mutex);
//    #ifndef AO
//        if (pulse_connected == 1){
//            pa_simple_flush (s, &error);
//        }
//    #endif
    //disconnect_pulse();
    //current_sample_rate = 0;
}

void decoder_eos() {
    // Call once current decode steam has run out
    printf("pa: End of stream\n");
    if (next_ready == 1) {
        printf("pa: Read next gapless\n");
        int result = load_next();
        if (result == 1){
          result_status = FAILURE;
        }
        pthread_mutex_lock(&buffer_mutex);
        next_ready = 0;
        reset_set_value = 0;
        reset_set = 1;
        reset_set_byte = high;
        pthread_mutex_unlock(&buffer_mutex);

    } else mode = ENDING;
}


void pump_decode() {
    // Here we get data from the decoders to fill the main buffer

    if (codec == WAVE) {
        int result;
        pthread_mutex_lock(&buffer_mutex);
        result = wave_decode(1024 * 2);
        pthread_mutex_unlock(&buffer_mutex);
        if (result == 1) {
            decoder_eos();
        }
                         
    } else if (codec == MPT) {
      int count;  
      count = openmpt_module_read_interleaved_stereo(mod, 48000, 4096, temp16l);
      if (count == 0){
        decoder_eos();
      } else {
        pthread_mutex_lock(&buffer_mutex);
        read_to_buffer_s16int(temp16l, count * 2);
        samples_decoded += count * 2;
        pthread_mutex_unlock(&buffer_mutex);
      }
    
    } else if (codec == FLAC) {
        // FLAC decoding

        switch (FLAC__stream_decoder_get_state(dec)) {
            case FLAC__STREAM_DECODER_END_OF_STREAM:
                decoder_eos();
                break;

            default:
                FLAC__stream_decoder_process_single(dec);

        }

        if (load_target_seek > 0 && flac_got_rate == 1) {
            //printf("pa: Set start position %d\n", load_target_seek);

            int rate = current_sample_rate;
            if (want_sample_rate > 0) rate = want_sample_rate;

            FLAC__stream_decoder_seek_absolute(dec, (int) sample_rate_src * (load_target_seek / 1000.0));
            pthread_mutex_lock(&buffer_mutex);
            reset_set_value = rate * (load_target_seek / 1000.0);
            reset_set = 1;
            reset_set_byte = high;
            load_target_seek = 0;
            pthread_mutex_unlock(&buffer_mutex);
        }

    } else if (codec == OPUS) {

        unsigned int done;

        done = op_read_stereo(opus_dec, opus_buffer, 1024 * 2) * 2;

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


    } else if (codec == VORBIS) {

        unsigned int done;
        int stream;
        done = ov_read(&vf, parse_buffer, 2048 * 2, 0, 2, 1, &stream);

        pthread_mutex_lock(&buffer_mutex);
        read_to_buffer_char16(parse_buffer, done);
        pthread_mutex_unlock(&buffer_mutex);
        if (done == 0) {
            decoder_eos();
        }

    } else if (codec == WAVPACK) {
        int samples;
        int32_t buffer[4 * 1024 * 2];
        samples = WavpackUnpackSamples(wpc, buffer, 1024);
        if (wp_bit == 16){
            read_to_buffer_16in32_fs(buffer, samples);
        } else if (wp_bit == 24){
            read_to_buffer_24in32_fs(buffer, samples);
        }
        samples_decoded += samples;

    } else if (codec == MPG) {
        // MP3 decoding

        size_t done;

        mpg123_read(mh, parse_buffer, 2048 * 2, &done);

        pthread_mutex_lock(&buffer_mutex);
        read_to_buffer_char16(parse_buffer, done);
        pthread_mutex_unlock(&buffer_mutex);
        if (done == 0) {
            decoder_eos();
        }
    } else if (codec == FFMPEG) {

        int b = 0;
        int done = 0;

        int c;
        while(b < 2048 && (c = fgetc(ffm)) != EOF ){
            ffm_buffer[b] = (char) c;
            b++;
        }

        if (feof(ffm)) {
            done = 1;
            printf("pa: FFMPEG EOF\n");
        }


//        while (b < 2048) {
//            if (feof(ffm)) {
//                done = 1;
//                printf("pa: FFMPEG EOF\n");
//                break;
//            }
//            ffm_buffer[b] = fgetc(ffm);
//            b++;
//        }
//
        if (b % 4 != 0) {
            printf("pa: Uneven data\n");
            decoder_eos();
            return;
        }

        pthread_mutex_lock(&buffer_mutex);
        read_to_buffer_char16(ffm_buffer, b);
//        while (i < b) {
//
//            memcpy(&bfl[high], &ffm_buffer[i], 4);
//            memcpy(&bfr[high], &ffm_buffer[i + 4], 4);
//
//            if (fade_fill > 0) {
//                fade_fx();
//            }
//            high++;
//            i += 8;
//        }
//        buff_cycle();
        pthread_mutex_unlock(&buffer_mutex);
        if (done == 1) {
            printf("pa: FFMPEG has finished\n");
            decoder_eos();

        }


    }

}


// ------------------------------------------------------------------------------------
// Audio output thread

float gate = 1.0;  // Used for ramping

void *out_thread(void *thread_id) {

    int b = 0;
    //double testa, testb;

    //t_start = get_time_ms();
    //printf("pa: Start out thread\n");

    while (out_thread_running == 1) {
        if (buffering == 1 && get_buff_fill() > BUFFER_STREAM_READY) {

            buffering = 0;
            printf("pa: Buffering -> Playing\n");
            #ifndef AO
            if (mode == PLAYING) connect_pulse();
            #endif

        }

        if (get_buff_fill() < 10 && loaded_target_file[0] == 'h') {

            if (mode == PLAYING) {
                #ifndef AO
                disconnect_pulse();
                #endif
                if (buffering == 0) printf("pa: Buffering...\n");
                buffering = 1;
            } else buffering = 0;
        }

        // Put fade buffer back
        if (mode == PLAYING && fade_fill > 0 && get_buff_fill() == 0){
            pthread_mutex_lock(&fade_mutex);
            int i = 0;
            while (fade_position < fade_fill){
                float cross = fade_position / (float) fade_fill;
                float cross_i = 1.0 - cross;
                bfl[high] = fadefl[fade_position] * cross_i;
                bfr[high] = fadefr[fade_position] * cross_i;
                fade_position++;
                high++;
                i++;
                if (i > current_sample_rate * 0.05) break;
            }
            buff_cycle();
            if (fade_position == fade_fill){
                fade_fill = 0;
                fade_position = 0;
            }
            pthread_mutex_unlock(&fade_mutex);
        }

        // Process decoded audio data and send out
        if ((mode == PLAYING || mode == RAMP_DOWN || mode == ENDING) && get_buff_fill() > 0 && buffering == 0) {
            pthread_mutex_lock(&fade_mutex);
            //pthread_mutex_lock(&buffer_mutex);

            b = 0; // byte number

            peak_roll_l = 0;
            peak_roll_r = 0;

            //printf("pa: Buffer is at %d\n", buff_filled);

            // Fill the out buffer...
            while (get_buff_fill() > 0) {


                // Truncate data if gate is closed anyway
                if (mode == RAMP_DOWN && gate == 0) break;

//                if (want_sample_rate > 0 && sample_change_byte == buff_base) {
//                    //printf("pa: Set new sample rate\n");
//                    connect_pulse();
//                    break;
//                }

                if (reset_set == 1 && reset_set_byte == low) {
                    //printf("pa: Reset position counter\n");
                    reset_set = 0;
                    position_count = reset_set_value;
                }

                // Set new gain value
                if (config_fade_jump == 0) {
                    if (rg_set == 1 && reset_set_byte == low) {
                        rg_value_on = rg_value_want;
                        rg_set = 0;
                    }
                } else {
                    if (rg_set == 1) {
                        if (fabs(rg_value_on - rg_value_want) < 0.01) {
                            // printf("pa: SET\n");
                            rg_value_on = rg_value_want;
                        }
                        if (rg_value_on < rg_value_want) rg_value_on += ramp_step(current_sample_rate, 2000);
                        if (rg_value_on > rg_value_want) rg_value_on -= ramp_step(current_sample_rate, 2000);
                        if (rg_value_on == rg_value_want) rg_set = 0;
                        // printf("%f\n", rg_value_on);
                    }
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

                // Apply gain amp
                if (rg_value_on != 0.0) {

                    // Left channel
                    if (l > 0 && l * rg_value_on <= 0) {
                        printf("pa: Warning: Audio clipped!\n");
                    } else if (l < 0 && l * rg_value_on >= 0) {
                        printf("pa: Warning: Audio clipped!\n");
                    } else l *= rg_value_on;

                    // Right channel
                    if (r > 0 && r * rg_value_on <= 0) {
                        printf("pa: Warning: Audio clipped!\n");
                    } else if (r < 0 && r * rg_value_on >= 0) {
                        printf("pa: Warning: Audio clipped!\n");
                    } else r *= rg_value_on;

                } // End amp

                // Apply final volume adjustment
                float final_vol = pow((gate * volume_on), config_volume_power);
                l = l * final_vol;
                r = r * final_vol;

                // Pack integer audio data to bytes
//                out_buf[b] = (buffl[buff_base]) & 0xFF;
//                out_buf[b + 1] = (buffl[buff_base] >> 8) & 0xFF;
//                out_buf[b + 2] = (buffr[buff_base]) & 0xFF;
//                out_buf[b + 3] = (buffr[buff_base] >> 8) & 0xFF;
                //printf("%f\n",out_buff[b]);

                #ifndef AO
                out_buff[b] = l;
                out_buff[b + 1] = r;
                b += 2;
                #else
                temp32 = l * 2147483648;
                out_buffc[b] = (temp32) & 0xFF;
                out_buffc[b + 1] = (temp32 >> 8) & 0xFF;
                out_buffc[b + 2] = (temp32 >> 16) & 0xFF;
                out_buffc[b + 3] = (temp32 >> 24) & 0xFF;
                temp32 = r * 2147483648;
                out_buffc[b + 4] = (temp32) & 0xFF;
                out_buffc[b + 5] = (temp32 >> 8) & 0xFF;
                out_buffc[b + 6] = (temp32 >> 16) & 0xFF;
                out_buffc[b + 7] = (temp32 >> 24) & 0xFF;
                b += 8;
                #endif


                //buff_filled--;
                //buff_base = (buff_base + 1) % BUFF_SIZE;
                low += 1;
                buff_cycle();

                position_count++;


                if (b >= 256 * 2) break; // Buffer is now full
            }
            //pthread_mutex_unlock(&buffer_mutex);
            pthread_mutex_unlock(&fade_mutex);
            // Send data to pulseaudio server
            if (b > 0) {

                if (peak_roll_l > peak_l) peak_l = peak_roll_l;
                if (peak_roll_r > peak_r) peak_r = peak_roll_r;

                if (pulse_connected == 0) {
                    connect_pulse();
                }

                //pthread_mutex_lock(&pulse_mutex);
                if (pulse_connected == 0) {
                    printf("pa: Error, not connected to any output!\n");
                } else {

                    #ifndef AO
                        pa_simple_write(s, &out_buff, b * 4, &error);
                    #else
                        ao_play(device, out_buffc, b);
                    #endif

                    // Flush buffer with 0s to avoid popping noise on close
                    if (mode == RAMP_DOWN && gate == 0 && (command == PAUSE || command == STOP)) {

                        b = 0;
                        while (b < 256 * 8) {
                            out_buff[b] = 0.0;
                            b += 1;
                        }
                        #ifndef AO
                            int g = 0;
                            while (g < 8) {
                                g++;
                                pa_simple_write(s, out_buff, b, &error);
                            }
                            pa_simple_flush(s, &error);
                            pa_simple_free(s);
                            //printf("Auto free\n");
                            pulse_connected = 0;

                        #else

                        #endif
                        usleep(100000);
                    }
                }

                //pthread_mutex_unlock(&pulse_mutex);

            } // sent data

        } // close if data
        else {
            usleep(2000);
        }

    } // close main loop
    out_thread_running = 0;
    //printf("Exit out thread\n");
    return thread_id;
} // close thread


// ---------------------------------------------------------------------------------------
// Main loop

int main_running = 0;

void *main_loop(void *thread_id) {


#ifdef AO
    	ao_initialize();
    	connect_pulse();
    #endif
    rbuf = (kiss_fft_scalar*)malloc(sizeof(kiss_fft_scalar) * 2048 );
    cbuf = (kiss_fft_cpx*)malloc(sizeof(kiss_fft_cpx) * (2048/2+1) );
    ffta = kiss_fftr_alloc(2048 ,0 ,0,0 );


    //pthread_t out_thread_id;
    //pthread_create(&out_thread_id, NULL, out_thread, NULL);


    int error = 0;

    int load_result = 0;
    int using_fade = 0;

    // SRC ----------------------------

    src = src_new(config_resample_quality, 2, &error);
    // printf("pa: SRC error code %d", error);
    error = 0;

    // MP3 decoder --------------------------------------------------------------

    mpg123_init();
    mh = mpg123_new(NULL, &error);
    mpg123_param(mh, MPG123_ADD_FLAGS, MPG123_QUIET | MPG123_SKIP_ID3V2, 0);
    mpg123_param(mh, MPG123_RESYNC_LIMIT, 10000, 0);

    // FLAC decoder ----------------------------------------------------------------

    dec = FLAC__stream_decoder_new();

    // Main loop ---------------------------------------------------------------
    while (1) {

        /* test1++; */
        /* if (test1 > 650){ */
        /*   printf("pa: Status: mode %d, command %d, buffer %d\n", mode, command, buff_filled); */
        /*   test1 = 0; */
        /* } */

        if (command != NONE) {

            if (command == EXIT) {
                break;
            }
            switch (command) {

                case PAUSE:
                    if (mode == PLAYING || (mode == RAMP_DOWN && gate == 0)) {
                        mode = PAUSED;
                        if (out_thread_running == 1){
                            out_thread_running = 2;
                            usleep(20000);
                          }
                        
                        command = NONE;
                    }

                    break;
                case RESUME:
                    if (mode == PAUSED) {
                        //if (pulse_connected == 0) connect_pulse();
                        while (out_thread_running == 2){
                            usleep(1000);

                        }
                        if (out_thread_running == 0) {
                              out_thread_running = 1;
                              pthread_t out_thread_id;
                              pthread_create(&out_thread_id, NULL, out_thread, NULL);
                        }
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
                    if ((mode == RAMP_DOWN && gate == 0) || mode == PAUSED) {
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
                    using_fade = 0;
                    if (config_fade_jump == 1 && want_sample_rate == 0 && mode == PLAYING) {
                        pthread_mutex_lock(&fade_mutex);
                        int l = current_sample_rate * (config_fade_duration / 1000.0);

                        if (get_buff_fill() > l) {
                            int i = 0;
                            int p = low;
                            i = 0;

                            while (i < l) {
                                fadefl[i] = bfl[p]; //buffl[(buff_base + i + reserve) % BUFF_SIZE];
                                fadefr[i] = bfr[p]; //buffr[(buff_base + i + reserve) % BUFF_SIZE];
                                i++;
                                p++;
                                if (p >= watermark){
                                    p = 0;
                                }
                            }
                            fade_position = 0;
                            fade_fill = l;
                            high = low;
                            using_fade = 1;

                            reset_set_byte = p;
                            if (reset_set == 0) {
                                reset_set = 1;
                                reset_set_value = 0;
                            }

                        }
                        pthread_mutex_unlock(&fade_mutex);
                    }

                    load_result = load_next();

                    if (using_fade == 0){
                            // Jump immediately
                            printf("jump\n");
                            position_count = 0;
                            buff_reset();
                            gate = 0;
                            sample_change_byte = 0;
                            reset_set_byte = 0;
                            reset_set_value = 0;
                    }

                    if (load_result == 0){

                        mode = PLAYING;
                        result_status = SUCCESS;
                        while (out_thread_running == 2){
                            usleep(1000);
                        }
                        if (out_thread_running == 0) {
                             out_thread_running = 1;
                              pthread_t out_thread_id;
                              pthread_create(&out_thread_id, NULL, out_thread, NULL);
                        }
                        command = NONE;


                    } else {
                        printf("pa: Load file failed\n");
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

                if (want_sample_rate > 0) position_count = want_sample_rate * (seek_request_ms / 1000.0);
                else position_count  = current_sample_rate * (seek_request_ms / 1000.0);

            } else if (mode == PAUSED) {


                if (want_sample_rate > 0) decode_seek(seek_request_ms, want_sample_rate);
                else decode_seek(seek_request_ms, current_sample_rate);

                if (want_sample_rate > 0) position_count = want_sample_rate * (seek_request_ms / 1000.0);
                else position_count = current_sample_rate * (seek_request_ms / 1000.0);

                pthread_mutex_lock(&buffer_mutex);

                buff_reset();

//                #ifndef AO
//                pthread_mutex_lock(&pulse_mutex);
//                if (pulse_connected == 1) {
//                    pa_simple_flush(s, &error);
//                }
//                pthread_mutex_unlock(&pulse_mutex);
//                #endif

                command = NONE;

                pthread_mutex_unlock(&buffer_mutex);

            } else if (mode != RAMP_DOWN) {
                printf("pa: fixme - cannot seek at this time\n");
                command = NONE;
            }

            if (mode == RAMP_DOWN && gate == 0) {
                pthread_mutex_lock(&buffer_mutex);
                buff_reset();
                //buff_base = 0; //(buff_base + buff_filled) % BUFF_SIZE;
                //buff_filled = 0;
//                if (command == SEEK && config_fast_seek == 1) {
//                    pthread_mutex_lock(&pulse_mutex);
//                    #ifndef AO
//                    pa_simple_flush(s, &error);
//                    #endif
//                    pthread_mutex_unlock(&pulse_mutex);
//                }
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
            printf("pa: Buffer ran out at end of track\n");
            end();

        }
        if (mode == ENDING && next_ready == 1) {
            printf("pa: Next registered while buffer was draining\n");
            printf("pa: -- remaining was %d\n", get_buff_fill());
            mode = PLAYING;
        }

        usleep(5000);
    }

    printf("pa: Cleanup and exit\n");

    pthread_mutex_lock(&buffer_mutex);

    main_running = 0;
    if (out_thread_running == 1) {
        out_thread_running = 2;
    }

    position_count = 0;
    buff_reset();

    //disconnect_pulse();
    FLAC__stream_decoder_finish(dec);
    FLAC__stream_decoder_delete(dec);
    mpg123_delete(mh);
    src_delete(src);

    pthread_mutex_unlock(&buffer_mutex);

    while (out_thread_running != 0){
        usleep(10000);
    }
    disconnect_pulse();
    command = NONE;

    return thread_id;
}


// ---------------------------------------------------------------------------------------
// Begin exported functions

int init() {
    //printf("ph: PHAzOR starting up\n");
    if (main_running == 0) {
        main_running = 1;
        pthread_t main_thread_id;
        pthread_create(&main_thread_id, NULL, main_loop, NULL);
    } else printf("ph: Cannot init. Main loop already running!\n");
    return 0;
}

int get_status() {
    return mode;
}
                                   
int get_result() {
  return result_status;
}

int start(char *filename, int start_ms, int fade, float rg) {

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


int next(char *filename, int start_ms, float rg) {

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

int pause() {
    while (command != NONE) {
        usleep(1000);
    }
    if (mode == PAUSED) return 0;
    if (mode == PLAYING) {
        mode = RAMP_DOWN;
    }
    command = PAUSE;
    return 0;
}

int resume() {
    while (command != NONE) {
        usleep(1000);
    }
    if (mode == PAUSED) {
        gate = 0;
    }
    command = RESUME;
    return 0;
}

int stop() {
    while (command != NONE) {
        usleep(1000);
    }
    command = STOP;
    return 0;
}

                                   
int seek(int ms_absolute, int flag) {

    while (command != NONE) {
        usleep(1000);
    }

    config_fast_seek = flag;
    seek_request_ms = ms_absolute;
    command = SEEK;

    return 0;
}

int set_volume(int percent) {
    volume_want = percent / 100.0;
    volume_on = percent / 100.0;

    return 0;
}

int ramp_volume(int percent, int speed) {
    volume_ramp_speed = speed;
    volume_want = percent / 100.0;
    return 0;
}

int get_position_ms() {
    if (command != START && command != LOAD && reset_set == 0 && current_sample_rate > 0) {
        return (int) ((position_count / (float) current_sample_rate) * 1000.0);
    } else return 0;
}
                                   
void set_position_ms(int ms) {
    position_count = ((float)(ms / 1000.0)) * current_sample_rate; 
}

int get_length_ms() {
    if (reset_set == 0 && sample_rate_src > 0 && current_length_count > 0) {

        return (int) ((current_length_count / (float) sample_rate_src) * 1000.0);
    } else return 0;
}

void config_set_dev_buffer(int ms) {
    config_dev_buffer = ms;
}

void config_set_samplerate(int hz) {
    sample_rate_out = hz;
}
void config_set_resample_quality(int n) {
    config_resample_quality = n;
}
void config_set_always_ffmpeg(int n) {
    config_always_ffmpeg = n;
}

void config_set_fade_duration(int ms){
    if (ms < 200) ms = 200;
    if (ms > 2000) ms = 2000;
    config_fade_duration = ms;
}

void config_set_dev_name(char *device) {
    if (device == NULL) {
        strcpy(config_output_sink, "Default");
    } else {
        strcpy(config_output_sink, device);
    }
}

void config_set_volume_power(int n){
    config_volume_power = n;
}

float get_level_peak_l() {

    float peak = peak_l;
    peak_l = 0.0;
    return peak;
}

float get_level_peak_r() {
    float peak = peak_r;
    peak_r = 0.0;
    return peak;
}

int get_spectrum(int n_bins, float* bins) {

    int samples = 2048;
    int base = low;

    int i = 0;
    while (i < samples) {
        if (base >= watermark){
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


int is_buffering(){
    if (buffering == 0) return 0;
    return (int) (get_buff_fill() / BUFFER_STREAM_READY * 100.0);
}
/* int get_latency(){ */
/*   return active_latency / 1000; */
/* } */

int feed_ready(int request_size){
    if (mode != STOPPED && high_mark - get_buff_fill() > request_size && codec == FEED) return 1;
    return 0;
}

void feed_raw(int len, char* data){
    if (feed_ready(len) == 0) return;
    pthread_mutex_lock(&buffer_mutex);
    read_to_buffer_char16(data, len);
    pthread_mutex_unlock(&buffer_mutex);
}


int shutdown() {
    while (command != NONE) {
        usleep(1000);
    }
    command = EXIT;
    return 0;
}

                                      
