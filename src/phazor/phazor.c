// PHAzOR - A high level audio playback library
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


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <math.h>
#include <pthread.h>
#include <time.h>
#include <pulse/simple.h>
#include <pulse/error.h>
#include <FLAC/stream_decoder.h>
#include <mpg123.h>
#include "vorbis/codec.h"
#include "vorbis/vorbisfile.h"
#include "opus/opusfile.h"
#include <sys/stat.h>
#include <samplerate.h>

#define BUFF_SIZE 240000  // Decoded data buffer size
#define BUFF_SAFE 100000  // Ensure there is this much space free in the buffer
// before writing

double get_time_ms() {
    struct timeval t;
    gettimeofday(&t, NULL);
    return (t.tv_sec + (t.tv_usec / 1000000.0)) * 1000.0;
}

double t_start, t_end;

int16_t buff16l[BUFF_SIZE];
int16_t buff16r[BUFF_SIZE];
unsigned int buff_filled = 0;
unsigned int buff_base = 0;

int16_t fade16l[BUFF_SIZE];
int16_t fade16r[BUFF_SIZE];

int16_t temp16l[BUFF_SIZE];
int16_t temp16r[BUFF_SIZE];

float re_in[BUFF_SIZE * 2];
float re_out[BUFF_SIZE * 2];

int fade_fill = 0;
int fade_position = 0;
int fade_2_flag = 0;

pthread_mutex_t buffer_mutex;
pthread_mutex_t pulse_mutex;

unsigned char out_buf[2048 * 4]; // 4 bytes for 16bit stereo

int position_count = 0;
int current_length_count = 0;

int sample_rate_out = 44100;
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

int peak_l = 0;
int peak_roll_l = 0;
int peak_r = 0;
int peak_roll_r = 0;

int config_fast_seek = 0;
int config_dev_buffer = 40;
int config_fade_jump = 1;
char config_output_sink[256]; // 256 just a conservative guess

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
};

int mode = STOPPED;
int command = NONE;

int decoder_allocated = 0;
int buffering = 0;

// Misc ----------------------------------------------------------

float ramp_step(int sample_rate, int milliseconds) {
    return 1.0 / sample_rate / (milliseconds / 1000.0);
}

void fade_fx() {

    if (fade_fill > 0) {
        if (fade_fill == fade_position) {
            fade_fill = 0;
            fade_position = 0;
        } else {

            float cross = fade_position / (float) fade_fill;
            float cross_i = 1.0 - cross;

            buff16l[(buff_filled + buff_base) % BUFF_SIZE] *= cross;
            buff16l[(buff_filled + buff_base) % BUFF_SIZE] += fade16l[fade_position] * cross_i;

            buff16r[(buff_filled + buff_base) % BUFF_SIZE] *= cross;
            buff16r[(buff_filled + buff_base) % BUFF_SIZE] += fade16r[fade_position] * cross_i;
            fade_position++;
        }
    }
}

FILE *fptr;

struct stat st;
int load_file_size = 0;
int samples_decoded = 0;

// Secret Rabbit Code --------------------------------------------------

SRC_DATA src_data;
SRC_STATE *src;

// Pulseaudio ---------------------------------------------------------

pa_simple *s;
pa_sample_spec ss;

pa_buffer_attr pab;

// Vorbis related --------------------------------------------------------

OggVorbis_File vf;
vorbis_info vi;

// Opus related ----------------------------------------

OggOpusFile *opus_dec;
int16_t opus_buffer[2048 * 2];

// MP3 related ------------------------------------------------

mpg123_handle *mh;
char parse_buffer[2048 * 2];

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

    fread(b, 4, 1, wave_file);
    //printf("pa: fmt : %s\n", b);

    fread(&i, 4, 1, wave_file);
    //printf("pa: abov: %d\n", i);
    if (i != 16) {
        printf("pa: Unsupported WAVE file\n");
        return 1;
    }

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

    fseek(wave_file, 6, SEEK_CUR);

    fread(&i, 2, 1, wave_file);
    //printf("pa: bitd: %d\n", i);
    if (i != 16) {
        printf("pa: Unsupported WAVE depth\n");
        return 1;
    }
    wave_depth = i;

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

    int i = 0;
    while (i < read_frames) {

        wave_error = fread(&wave_16, 2, 1, wave_file);
        if (wave_error != 1) return 1;
        buff16l[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) wave_16;

        wave_error = fread(&wave_16, 2, 1, wave_file);
        if (wave_error != 1) return 1;
        buff16r[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) wave_16;

        if (fade_fill > 0) {
            fade_fx();
        }

        buff_filled++;
        samples_decoded++;
        i++;


        if ((ftell(wave_file) - wave_start) > wave_size) {
            printf("pa: End of WAVE file data\n");
            return 1;
        }

    }
    return 0;

}

int wave_seek(int frame_position) {
    return fseek(wave_file, (frame_position * 4) + wave_start, SEEK_SET);
}

void wave_close() {
    fclose(wave_file);
}


void resample_to_buffer(int in_frames) {

    src_data.data_in = re_in;
    src_data.data_out = re_out;
    src_data.input_frames = in_frames;
    src_data.output_frames = BUFF_SIZE;
    src_data.src_ratio = (double) sample_rate_out / (double) sample_rate_src;
    src_data.end_of_input = 0;

    src_process(src, &src_data);
    //printf("pa: SRC error code: %d\n", src_result);
    //printf("pa: SRC output frames: %lu\n", src_data.output_frames_gen);
    //printf("pa: SRC input frames used: %lu\n", src_data.input_frames_used);
    int out_frames = src_data.output_frames_gen;

    int i = 0;
    int32_t t = 0;
    while (i < out_frames) {

        t = (re_out[i * 2] + (((float) rand() / (float) (RAND_MAX)) * 0.00004) - 0.00002) * 32768;
        if (t > 32767) t = 32767;
        if (t < -32768) t = -32768;
        buff16l[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) t;

        //t = re_out[(i * 2) + 1] * 32768;
        t = (re_out[(i * 2) + 1] + (((float) rand() / (float) (RAND_MAX)) * 0.00004) - 0.00002) * 32768;
        if (t > 32767) t = 32767;
        if (t < -32768) t = -32768;
        buff16r[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) t;

        if (fade_fill > 0) {
            fade_fx();
        }

        buff_filled++;
        i++;
    }

}

void read_to_buffer_char16_resample(char src[], int n_bytes) {

    int i = 0;
    int f = 0;

    // Convert bytes16 to float
    while (i < n_bytes) {
        re_in[f * 2] = ((float) (int16_t)((src[i + 1] << 8) | (src[i + 0] & 0xFF))) / (float) 32768.0;
        if (src_channels == 1) {
            re_in[(f * 2) + 1] = re_in[f * 2];
            i += 2;
        } else {
            re_in[(f * 2) + 1] = ((float) (int16_t)((src[i + 3] << 8) | (src[i + 2] & 0xFF))) / (float) 32768.0;
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
            buff16l[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t)((src[i + 1] << 8) | (src[i + 0] & 0xFF));
            buff16r[(buff_filled + buff_base) % BUFF_SIZE] = buff16l[(buff_filled + buff_base) % BUFF_SIZE];
            if (fade_fill > 0) {
                fade_fx();
            }
            buff_filled++;
            i += 2;
        }
    } else {
        while (i < n_bytes) {
            buff16l[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t)((src[i + 1] << 8) | (src[i + 0] & 0xFF));
            buff16r[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t)((src[i + 3] << 8) | (src[i + 2] & 0xFF));
            if (fade_fill > 0) {
                fade_fx();
            }
            buff_filled++;
            i += 4;
        }
    }
}

void read_to_buffer_s16int_resample(int16_t src[], int n_samples) {

    int i = 0;
    int f = 0;

    // Convert int16 to float
    while (i < n_samples) {
        re_in[f * 2] = ((float) src[i]) / (float) 32768.0;
        if (src_channels == 1) {
            re_in[(f * 2) + 1] = re_in[f * 2];
            i += 1;
        } else {
            re_in[(f * 2) + 1] = ((float) src[i + 1]) / (float) 32768.0;
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
            buff16l[(buff_filled + buff_base) % BUFF_SIZE] = src[i];
            buff16r[(buff_filled + buff_base) % BUFF_SIZE] = buff16l[(buff_filled + buff_base) % BUFF_SIZE];
            if (fade_fill > 0) {
                fade_fx();
            }
            i+=1;
            buff_filled++;
        }

    } else {
        while (i < n_samples){
            buff16l[(buff_filled + buff_base) % BUFF_SIZE] = src[i];
            buff16r[(buff_filled + buff_base) % BUFF_SIZE] = src[i + 1];
            if (fade_fill > 0) {
                fade_fx();
            }
            i+=2;
            buff_filled++;
        }
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
            sample_change_byte = (buff_filled + buff_base) % BUFF_SIZE;
        }
    }

    if (current_length_count == 0) {
        current_length_count = FLAC__stream_decoder_get_total_samples(decoder);
    }

    if (load_target_seek > 0) {
        pthread_mutex_unlock(&buffer_mutex);
        return FLAC__STREAM_DECODER_WRITE_STATUS_CONTINUE;
    }

    unsigned int i = 0;
    int ran = 512;
    int resample = 0;
    sample_rate_src = frame->header.sample_rate;
    if (sample_rate_src != sample_rate_out) {
        resample = 1;
    }

    if (frame->header.blocksize > (BUFF_SIZE - buff_filled)) {
        printf("pa: critical: BUFFER OVERFLOW!");
    }

    int temp_fill = 0;

    if (resample == 0) {

        // No resampling needed, transfer data to main buffer

        while (i < frame->header.blocksize) {

            // Read and handle 24bit audio
            if (frame->header.bits_per_sample == 24) {

                // Here we downscale 24bit to 16bit. Dithering is appied to reduce quantisation noise.

                // left
                ran = 512;
                if (buffer[0][i] > 8388351) ran = (8388608 - buffer[0][i]) - 3;
                if (buffer[0][i] < -8388353) ran = (8388608 - abs(buffer[0][i])) - 3;

                if (ran > 1)
                    buff16l[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t)(
                            (buffer[0][i] + (rand() % ran) - (ran / 2)) / 256);
                else buff16l[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t)(buffer[0][i] / 256);

                if (frame->header.channels == 1) {
                    buff16r[(buff_filled + buff_base) % BUFF_SIZE] = buff16l[(buff_filled + buff_base) % BUFF_SIZE];
                } else {

                    //right
                    ran = 512;
                    if (buffer[1][i] > 8388351) ran = (8388608 - buffer[1][i]) - 3;
                    if (buffer[1][i] < -8388353) ran = (8388608 - abs(buffer[1][i])) - 3;

                    if (ran > 1)
                        buff16r[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t)(
                                (buffer[1][i] + (rand() % ran) - (ran / 2)) / 256);
                    else buff16r[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t)(buffer[1][i] / 256);
                }
            } // end 24 bit audio

                // Read 16bit audio
            else if (frame->header.bits_per_sample == 16) {
                buff16l[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) buffer[0][i];
                if (frame->header.channels == 1) {
                    buff16r[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) buffer[0][i];
                } else {
                    buff16r[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) buffer[1][i];
                }
            } else printf("ph: CRITIAL ERROR - INVALID BIT DEPTH!\n");

            if (fade_fill > 0) {
                fade_fx();
            }

            buff_filled++;
            i++;
        }

    } else {

        // Transfer data to resampler for resampling

        while (i < frame->header.blocksize) {
            // Read and handle 24bit audio
            if (frame->header.bits_per_sample == 24) {

                re_in[i * 2] = ((float) buffer[0][i]) / ((float) 8388608.0);
                if (frame->header.channels == 1) re_in[(i * 2) + 1] = re_in[i * 2];
                else re_in[(i * 2) + 1] = ((float) buffer[1][i]) / ((float) 8388608.0);

            } // end 24 bit audio

                // Read 16bit audio
            else if (frame->header.bits_per_sample == 16) {

                re_in[i * 2] = ((float) buffer[0][i]) / (float) 32768.0;
                if (frame->header.channels == 1) re_in[(i * 2) + 1] = re_in[i * 2];
                else re_in[(i * 2) + 1] = ((float) buffer[1][i]) / (float) 32768.0;

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
            src_reset(src);
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
    }
    decoder_allocated = 0;
}


int disconnect_pulse() {
    if (pulse_connected == 1) {
        //pa_simple_drain(s, NULL);
        //pa_simple_flush(s, NULL);
        pthread_mutex_lock(&pulse_mutex);
        pa_simple_free(s);
        pthread_mutex_unlock(&pulse_mutex);
        //printf("pa: Disconnect from PulseAudio\n");
    }
    pulse_connected = 0;
    return 0;
}


void connect_pulse() {

    if (pulse_connected == 1) disconnect_pulse();
    //printf("pa: Connect pulse\n");
    pthread_mutex_lock(&pulse_mutex);
    if (want_sample_rate > 0) {
        current_sample_rate = want_sample_rate;
        want_sample_rate = 0;
    }

    if (current_sample_rate <= 1) {
        printf("pa: Samplerate detection warning.\n");
        pthread_mutex_unlock(&pulse_mutex);
        return;
    }

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
    ss.format = PA_SAMPLE_S16LE;
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

    if (error > 0) {
        printf("pa: PulseAudio init error\n");
        //printf(pa_strerror(error));
        //printf("\n");
        mode = STOPPED;
    } else pulse_connected = 1;

    pthread_mutex_unlock(&pulse_mutex);

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
    rg_byte = (buff_filled + buff_base) % BUFF_SIZE;

    char peak[35];

    if (strcmp(ext, ".ape") == 0 || strcmp(ext, ".APE") == 0 ||
        strcmp(ext, ".m4a") == 0 || strcmp(ext, ".M4A") == 0 ||
        strcmp(ext, ".tta") == 0 || strcmp(ext, ".TTA") == 0 ||
        strcmp(ext, ".wma") == 0 || strcmp(ext, ".WMA") == 0 ||
        //strcmp(ext, ".wav") == 0 || strcmp(ext, ".WAV") == 0 ||
        loaded_target_file[0] == 'h') {
        codec = FFMPEG;

        start_ffmpeg(loaded_target_file, load_target_seek);
        pthread_mutex_lock(&buffer_mutex);
        if (current_sample_rate != sample_rate_out) {
            sample_change_byte = (buff_filled + buff_base) % BUFF_SIZE;
            want_sample_rate = sample_rate_out;
        }
        pthread_mutex_unlock(&buffer_mutex);
        return 0;
    }


    if ((fptr = fopen(loaded_target_file, "rb")) == NULL) {

        printf("pa: Error opening file\n");
        return 1;
    }


    stat(loaded_target_file, &st);
    load_file_size = st.st_size;

    fread(peak, sizeof(peak), 1, fptr);

    if (memcmp(peak, "fLaC", 4) == 0) {
        codec = FLAC;
    } else if (memcmp(peak, "RIFF", 4) == 0) {
        codec = WAVE;
    } else if (memcmp(peak, "OggS", 4) == 0) {
        codec = VORBIS;
        if (peak[28] == 'O' && peak[29] == 'p') codec = OPUS;
    }

    if (codec == UNKNOWN) {

        if (strcmp(ext, ".flac") == 0 || strcmp(ext, ".FLAC") == 0) {
            codec = FLAC;
            //printf("pa: Set codec as FLAC\n");
        }
        if (strcmp(ext, ".mp3") == 0 || strcmp(ext, ".MP3") == 0) {
            //printf("pa: Set codec as MP3\n");
            codec = MPG;
        }
        if (strcmp(ext, ".ogg") == 0 || strcmp(ext, ".OGG") == 0 ||
            strcmp(ext, ".oga") == 0 || strcmp(ext, ".OGA") == 0) {
            //printf("pa: Set codec as OGG Vorbis\n");
            codec = VORBIS;
        }
        if (strcmp(ext, ".opus") == 0 || strcmp(ext, ".OPUS") == 0) {
            //printf("pa: Set codec as OGG Opus\n");
            codec = OPUS;
        }
    }

    // todo - search further into file for identification

    if (codec == UNKNOWN) {
        codec = MPG;
        printf("pa: Codec could not be identified, assuming MP3\n");
    }

    fclose(fptr);

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
            if (current_sample_rate != wave_samplerate) {
                sample_change_byte = (buff_filled + buff_base) % BUFF_SIZE;
                want_sample_rate = wave_samplerate;
            }

            if (load_target_seek > 0) {
                reset_set_value = (int) wave_samplerate * (load_target_seek / 1000.0);
                reset_set = 1;
                reset_set_byte = (buff_filled + buff_base) % BUFF_SIZE;
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
                    sample_change_byte = (buff_filled + buff_base) % BUFF_SIZE;
                    want_sample_rate = sample_rate_out;
                }

                current_length_count = op_pcm_total(opus_dec, -1);

                if (load_target_seek > 0) {
                    // printf("pa: Start at position %d\n", load_target_seek);
                    op_pcm_seek(opus_dec, (int) 48000 * (load_target_seek / 1000.0));
                    reset_set_value = op_raw_tell(opus_dec);
                    samples_decoded = reset_set_value * 2;
                    reset_set = 1;
                    reset_set_byte = (buff_filled + buff_base) % BUFF_SIZE;
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
                    sample_change_byte = (buff_filled + buff_base) % BUFF_SIZE;
                    want_sample_rate = sample_rate_out;
                }

                current_length_count = ov_pcm_total(&vf, -1);

                if (load_target_seek > 0) {
                    //printf("pa: Start at position %d\n", load_target_seek);
                    ov_pcm_seek(&vf, (ogg_int64_t) vi.rate * (load_target_seek / 1000.0));
                    reset_set_value = vi.rate * (load_target_seek / 1000.0); // op_pcm_tell(opus_dec); that segfaults?
                    reset_set_value = 0;
                    reset_set = 1;
                    reset_set_byte = (buff_filled + buff_base) % BUFF_SIZE;
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
                return 0;

            } else return 1;

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
                sample_change_byte = (buff_filled + buff_base) % BUFF_SIZE;
                want_sample_rate = sample_rate_out;
            }
            current_length_count = (u_int) mpg123_length(mh);

            if (encoding == MPG123_ENC_SIGNED_16) {

                if (load_target_seek > 0) {
                    //printf("pa: Start at position %d\n", load_target_seek);
                    mpg123_seek(mh, (int) rate * (load_target_seek / 1000.0), SEEK_SET);
                    reset_set_value = mpg123_tell(mh);
                    reset_set = 1;
                    reset_set_byte = (buff_filled + buff_base) % BUFF_SIZE;
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
    buff_base = 0;
    buff_filled = 0;
    pthread_mutex_unlock(&buffer_mutex);
    //pa_simple_flush (s, &error);
    disconnect_pulse();
    current_sample_rate = 0;
}

void decoder_eos() {
    // Call once current decode steam has run out
    printf("pa: End of stream\n");
    if (next_ready == 1) {
        printf("pa: Read next gapless\n");
        load_next();
        pthread_mutex_lock(&buffer_mutex);
        next_ready = 0;
        reset_set_value = 0;
        reset_set = 1;
        reset_set_byte = (buff_filled + buff_base) % BUFF_SIZE;
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
    } else if (codec == FLAC) {
        // FLAC decoding

        switch (FLAC__stream_decoder_get_state(dec)) {
            case FLAC__STREAM_DECODER_END_OF_STREAM:
                decoder_eos();
                break;

            default:
                FLAC__stream_decoder_process_single(dec);

        }

        if (load_target_seek > 0) {
            //printf("pa: Set start position %d\n", load_target_seek);

            int rate = current_sample_rate;
            if (want_sample_rate > 0) rate = want_sample_rate;

            FLAC__stream_decoder_seek_absolute(dec, (int) rate * (load_target_seek / 1000.0));
            pthread_mutex_lock(&buffer_mutex);
            reset_set_value = rate * (load_target_seek / 1000.0);
            reset_set = 1;
            reset_set_byte = (buff_filled + buff_base) % BUFF_SIZE;
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

        int i = 0;
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
        if (b % 2 == 1) {
            printf("pa: Uneven data\n");
            decoder_eos();
            return;
        }

        pthread_mutex_lock(&buffer_mutex);
        while (i < b) {

            buff16l[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t)(
                    (ffm_buffer[i + 1] << 8) | (ffm_buffer[i] & 0xFF));
            buff16r[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t)(
                    (ffm_buffer[i + 3] << 8) | (ffm_buffer[i + 2] & 0xFF));
            if (fade_fill > 0) {
                fade_fx();
            }
            buff_filled++;
            i += 4;
        }
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

int out_thread_running = 0; // bool

void *out_thread(void *thread_id) {

    out_thread_running = 1;
    int b = 0;
    //double testa, testb;

    t_start = get_time_ms();

    while (out_thread_running == 1) {

        if (buffering == 1 && buff_filled > 90000) {

            buffering = 0;
            printf("pa: Buffering -> Playing\n");
            if (mode == PLAYING) connect_pulse();

        }

        if (buff_filled < 10 && loaded_target_file[0] == 'h') {

            if (mode == PLAYING) {
                disconnect_pulse();
                if (buffering == 0) printf("pa: Buffering...\n");
                buffering = 1;
            } else buffering = 0;
        }

        // Process decoded audio data and send out
        if ((mode == PLAYING || mode == RAMP_DOWN || mode == ENDING) && buff_filled > 0 && buffering == 0) {

            pthread_mutex_lock(&buffer_mutex);

            b = 0; // byte number

            peak_roll_l = 0;
            peak_roll_r = 0;

            //printf("pa: Buffer is at %d\n", buff_filled);

            // Fill the out buffer...
            while (buff_filled > 0) {


                // Truncate data if gate is closed anyway
                if (mode == RAMP_DOWN && gate == 0) break;

                if (want_sample_rate > 0 && sample_change_byte == buff_base) {
                    //printf("pa: Set new sample rate\n");
                    connect_pulse();
                    break;
                }

                if (reset_set == 1 && reset_set_byte == buff_base) {
                    //printf("pa: Reset position counter\n");
                    reset_set = 0;
                    position_count = reset_set_value;
                }

                // Set new gain value
                if (config_fade_jump == 0) {
                    if (rg_set == 1 && reset_set_byte == buff_base) {
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

                if (abs(buff16l[buff_base]) > peak_roll_l) peak_roll_l = abs(buff16l[buff_base]);
                if (abs(buff16r[buff_base]) > peak_roll_r) peak_roll_r = abs(buff16r[buff_base]);

                // Apply gain amp
                if (rg_value_on != 0.0) {

                    // Left channel
                    if (buff16l[buff_base] > 0 && buff16l[buff_base] * rg_value_on <= 0) {
                        printf("pa: Warning: Audio clipped!\n");
                    } else if (buff16l[buff_base] < 0 && buff16l[buff_base] * rg_value_on >= 0) {
                        printf("pa: Warning: Audio clipped!\n");
                    } else buff16l[buff_base] *= rg_value_on;

                    // Right channel
                    if (buff16r[buff_base] > 0 && buff16r[buff_base] * rg_value_on <= 0) {
                        printf("pa: Warning: Audio clipped!\n");
                    } else if (buff16r[buff_base] < 0 && buff16r[buff_base] * rg_value_on >= 0) {
                        printf("pa: Warning: Audio clipped!\n");
                    } else buff16r[buff_base] *= rg_value_on;

                } // End amp

                // Apply final volume adjustment (logarithmic)
                buff16l[buff_base] *= pow(gate * volume_on, 2.0);
                buff16r[buff_base] *= pow(gate * volume_on, 2.0);

                // Pack integer audio data to bytes
                out_buf[b] = (buff16l[buff_base]) & 0xFF;
                out_buf[b + 1] = (buff16l[buff_base] >> 8) & 0xFF;
                out_buf[b + 2] = (buff16r[buff_base]) & 0xFF;
                out_buf[b + 3] = (buff16r[buff_base] >> 8) & 0xFF;

                b += 4;
                buff_filled--;
                buff_base = (buff_base + 1) % BUFF_SIZE;

                position_count++;


                if (b >= 256 * 4) break; // Buffer is now full
            }
            pthread_mutex_unlock(&buffer_mutex);
            // Send data to pulseaudio server
            if (b > 0) {

                if (peak_roll_l > peak_l) peak_l = peak_roll_l;
                if (peak_roll_r > peak_r) peak_r = peak_roll_r;

                pthread_mutex_lock(&pulse_mutex);
                if (pulse_connected == 0) {
                    printf("pa: Error, not connected to any output!\n");
                } else {

                    /* t_end = get_time_ms(); */
                    /* testa = (t_end - t_start); */
                    /* t_start = t_end; */

                    pa_simple_write(s, out_buf, b, &error);
                    /* active_latency = (int) pa_simple_get_latency(s, &error); */

                    /* t_end = get_time_ms(); */
                    /* testb = (t_end - t_start); */
                    /* t_start = t_end; */

                    /* if (testa + testb > config_dev_buffer - 5){ */
                    /*   printf("Write at: %f\n", testa); */
                    /*   printf("Took: %f\n", testb); */
                    /*   printf("Buffer: %d\n", buff_filled); */
                    /* } */

                    // Flush buffer with 0s to avoid popping noise on close
                    if (mode == RAMP_DOWN && gate == 0 && (command == PAUSE || command == STOP)) {
                        pulse_connected = 0;
                        b = 0;
                        while (b < 256 * 4) {
                            out_buf[b] = 0 & 0xFF;
                            b += 1;
                        }
                        int g = 0;
                        while (g < 12) {
                            g++;
                            pa_simple_write(s, out_buf, b, &error);
                        }
                        pa_simple_flush(s, &error);
                        pa_simple_free(s);
                        usleep(100000);
                    }
                }

                pthread_mutex_unlock(&pulse_mutex);

            } // sent data

        } // close if data
        else usleep(500);

    } // close main loop

    return thread_id;
} // close thread


// ---------------------------------------------------------------------------------------
// Main loop

int main_running = 0;

void *main_loop(void *thread_id) {


    pthread_t out_thread_id;
    pthread_create(&out_thread_id, NULL, out_thread, NULL);


    int error = 0;

    int load_result = 0;

    // SRC ----------------------------

    src = src_new(SRC_SINC_MEDIUM_QUALITY, 2, &error);
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

                        //disconnect_pulse();
                        command = NONE;
                    }

                    break;
                case RESUME:
                    if (mode == PAUSED) {
                        if (pulse_connected == 0) connect_pulse();
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

                    load_result = load_next();
                    if (load_result == 0) {
                        pthread_mutex_lock(&buffer_mutex);
                        // Prepare for a crossfade if enabled and suitable

                        if (config_fade_jump == 2 && want_sample_rate == 0 && mode == PLAYING){

                            float l = current_sample_rate * 0.6;
                            int i = 0;
                            float v = 1.0;
                            while (i < l){
                                v = 1.0 - (i / l);
                                printf("%f\n", v);
                                buff16l[(buff_base + i) % BUFF_SIZE] *= v;
                                buff16r[(buff_base + i) % BUFF_SIZE] *= v;
                                i++;
                            }
                            buff_filled = l;
                            reset_set_byte = (buff_base + i) % BUFF_SIZE;
                            if (reset_set == 0) {
                                reset_set = 1;
                                reset_set_value = 0;
                            }


                        }
                        else if (config_fade_jump == 1 && want_sample_rate == 0 && mode == PLAYING) {
                            int reserve = current_sample_rate * 0.1;
                            int l;
                            l = current_sample_rate * 0.7;
                            if (buff_filled > l + reserve) {
                                int i = 0;
                                while (i < l) {
                                    fade16l[i] = buff16l[(buff_base + i + reserve) % BUFF_SIZE];
                                    fade16r[i] = buff16r[(buff_base + i + reserve) % BUFF_SIZE];
                                    i++;
                                }
                                fade_position = 0;
                                fade_fill = l;
                                buff_filled = reserve;

                                reset_set_byte = (buff_base + reserve) % BUFF_SIZE;
                                if (reset_set == 0) {
                                    reset_set = 1;
                                    reset_set_value = 0;

                                }

                            }
                        } else {

                            // Jump immediately
                            position_count = 0;
                            buff_base = 0;
                            buff_filled = 0;
                            gate = 0;
                            sample_change_byte = 0;
                            reset_set_byte = 0;
                            reset_set_value = 0;

                        }

                        if (want_sample_rate == 0 && pulse_connected == 0) {
                            connect_pulse();

                        }

                        mode = PLAYING;
                        command = NONE;
                        pthread_mutex_unlock(&buffer_mutex);


                    } else {
                        printf("pa: Load file failed\n");
                        command = STOP;
                        //mode = STOPPED;
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

                buff_base = 0;
                buff_filled = 0;
                if (pulse_connected == 1) {
                    pthread_mutex_lock(&pulse_mutex);
                    pa_simple_flush(s, &error);
                    pthread_mutex_unlock(&pulse_mutex);
                }

                command = NONE;

                pthread_mutex_unlock(&buffer_mutex);

            } else if (mode != RAMP_DOWN) {
                printf("pa: fixme - cannot seek at this time\n");
                command = NONE;
            }

            if (mode == RAMP_DOWN && gate == 0) {
                pthread_mutex_lock(&buffer_mutex);
                buff_base = (buff_base + buff_filled) & BUFF_SIZE;
                buff_filled = 0;
                if (command == SEEK && config_fast_seek == 1) {
                    pthread_mutex_lock(&pulse_mutex);
                    pa_simple_flush(s, &error);
                    pthread_mutex_unlock(&pulse_mutex);
                }
                mode = PLAYING;
                command = NONE;
                pthread_mutex_unlock(&buffer_mutex);

            }
        }


        // Refill the buffer
        if (mode == PLAYING) {
            while (buff_filled < BUFF_SAFE && mode != ENDING) {
                pump_decode();

            }
        }

        if (mode == ENDING && buff_filled == 0) {
            printf("pa: Buffer ran out at end of track\n");
            end();

        }
        if (mode == ENDING && next_ready == 1) {
            printf("pa: Next registered while buffer was draining\n");
            printf("pa: -- remaining was %d\n", buff_filled);
            mode = PLAYING;
        }

        usleep(5000);
    }

    printf("pa: Cleanup and exit\n");

    pthread_mutex_lock(&buffer_mutex);

    main_running = 0;
    out_thread_running = 0;
    command = NONE;
    position_count = 0;
    buff_base = 0;
    buff_filled = 0;

    disconnect_pulse();
    FLAC__stream_decoder_finish(dec);
    FLAC__stream_decoder_delete(dec);
    mpg123_delete(mh);
    src_delete(src);

    pthread_mutex_unlock(&buffer_mutex);

    return thread_id;
}


// ---------------------------------------------------------------------------------------
// Begin exported functions

int init() {
    printf("ph: PHAzOR starting up\n");
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

int start(char *filename, int start_ms, int fade, float rg) {

    while (command != NONE) {
        usleep(1000);
    }

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
    if (reset_set == 0 && current_sample_rate > 0) {
        return (int) ((position_count / (float) current_sample_rate) * 1000.0);
    } else return 0;
}

int get_length_ms() {
    if (reset_set == 0 && sample_rate_src > 0 && current_length_count > 0) {

        return (int) ((current_length_count / (float) sample_rate_src) * 1000.0);
    } else return 0;
}

void config_set_dev_buffer(int ms) {
    config_dev_buffer = ms;
}

void config_set_dev_name(char *device) {
    if (device == NULL) {
        strcpy(config_output_sink, "Default");
    } else {
        strcpy(config_output_sink, device);
    }
}

int get_level_peak_l() {
    int peak = peak_l;
    peak_l = 0;
    return peak;
}

int get_level_peak_r() {
    int peak = peak_r;
    peak_r = 0;
    return peak;
}

int is_buffering(){
    if (buffering == 0) return 0;
    return (int) (buff_filled / 90000.0 * 100);
}
/* int get_latency(){ */
/*   return active_latency / 1000; */
/* } */

int shutdown() {
    while (command != NONE) {
        usleep(1000);
    }
    command = EXIT;
    return 0;
}

                                      
