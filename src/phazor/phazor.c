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


#define BUFF_SIZE 240000  // Decoded data buffer size
#define BUFF_SAFE 100000  // Ensure there is this much space free in the buffer
                          // before writing

double get_time_ms()
{
struct timeval t;
gettimeofday(&t, NULL);
return (t.tv_sec + (t.tv_usec / 1000000.0)) * 1000.0;
}

double t_start, t_end;

int16_t buff16l[BUFF_SIZE];
int16_t buff16r[BUFF_SIZE];
unsigned int buff_filled = 0;
unsigned int buff_base = 0;

pthread_mutex_t buffer_mutex;
pthread_mutex_t pulse_mutex;

unsigned char out_buf[2048 * 4]; // 4 bytes for 16bit stereo

unsigned int position_count = 0;
unsigned int current_length_count = 0;

unsigned int current_sample_rate = 0;
unsigned int want_sample_rate = 0;
unsigned int sample_change_byte = 0;

unsigned int reset_set = 0;
unsigned int reset_set_value = 0;
unsigned int reset_set_byte = 0;

char load_target_file[4096]; // 4069 bytes for max linux filepath

unsigned int load_target_seek = 0;
unsigned int next_ready = 0;
unsigned int seek_request_ms = 0;

float volume_want = 1.0;
float volume_on = 1.0;
float volume_ramp_speed = 750;  // ms for 1 to 0

int codec = 0;
int error = 0;

int peak_l = 0;
int peak_roll_l = 0;
int peak_r = 0;
int peak_roll_r = 0;

int config_fast_seek = 0;
int config_dev_buffer = 40;

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
};

int mode = STOPPED;
int command = NONE;

int decoder_allocated = 0;
int buffering = 0;

// Misc ----------------------------------------------------------

float ramp_step(int sample_rate, int milliseconds){
  return 1.0 / sample_rate / (milliseconds / 1000.0); 
}

FILE *fptr;

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

void start_ffmpeg(char uri[], int start_ms){
  
  sprintf(exe_string, "ffmpeg -loglevel quiet -i \"%s\" -ss %dms -acodec pcm_s16le -f s16le -ac 2 -ar 44100 - ", uri, start_ms);
  //printf(exe_string, uri, start_ms);
  ffm = popen(exe_string, "r");
  if (ffm == NULL){
    printf("pa: Error starting FFMPEG\n");
  } 
}

void stop_ffmpeg(){
  printf("pa: Stop FFMPEG\n");
  pclose(ffm);
}

// FLAC related ---------------------------------------------------------------

FLAC__StreamDecoderWriteStatus f_write(const FLAC__StreamDecoder *decoder, const FLAC__Frame *frame, const FLAC__int32 *const buffer[], void *client_data){
  
  //printf("Frame size is: %d\n", frame->header.blocksize);
  //printf("Resolution is: %d\n", frame->header.bits_per_sample);
  //printf("Samplerate is: %d\n", frame->header.sample_rate); 
  //printf("Pointer is %d\n", buffer[0]);
  pthread_mutex_lock(&buffer_mutex);
  if (frame->header.sample_rate != current_sample_rate){
    if (want_sample_rate != frame->header.sample_rate){
      want_sample_rate = frame->header.sample_rate;
      sample_change_byte = (buff_filled + buff_base) % BUFF_SIZE;
    }
  }
  
  if (current_length_count == 0){
    current_length_count = FLAC__stream_decoder_get_total_samples(decoder);
  }
  
  if (load_target_seek > 0) {
    pthread_mutex_unlock(&buffer_mutex);
    return FLAC__STREAM_DECODER_WRITE_STATUS_CONTINUE;
  }                                                                                                                                                        
                                                                                                                                                            
                                                                                                                                                            
  unsigned int i = 0;
  int ran = 512;
  
  while (i < frame->header.blocksize){

    if (buff_filled >= BUFF_SIZE){
      // This shouldn't happen
      printf("ERROR: Buffer overrun!\n");
    }
    else {
      // Read and handle 24bit audio
      if (frame->header.bits_per_sample == 24){

        // Here we downscale 24bit to 16bit. Dithering is appied to reduce quantisation noise.
        
        // left
        ran = 512;
        if (buffer[0][i] > 8388351) {
          ran = (8388608 - buffer[0][i]) - 3;
        }
          
        if (buffer[0][i] < -8388353) {
          ran = (8388608 - abs(buffer[0][i])) - 3;
        } 
        
        if (ran > 1) buff16l[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) ((buffer[0][i] + (rand() % ran) - (ran / 2)) / 256);
        else buff16l[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) (buffer[0][i] / 256);
        
        //right
        ran = 512;

        if (buffer[1][i] > 8388351) {
          ran = (8388608 - buffer[1][i]) - 3;
        }
          
        if (buffer[1][i] < -8388353) {
          ran = (8388608 - abs(buffer[1][i])) - 3;
        } 
        
        if (ran > 1) buff16r[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) ((buffer[1][i] + (rand() % ran) - (ran / 2)) / 256);
        else buff16r[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) (buffer[1][i] / 256);
                                                                                  
      }
      // Read 16bit audio
      else if (frame->header.bits_per_sample == 16){
        buff16l[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) buffer[0][i];
        buff16r[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) buffer[1][i];       
      }
      else printf("ph: CRITIAL ERROR - INVALID BIT DEPTH!\n");
      
    buff_filled++;
    }
    
    i++;
  }
  pthread_mutex_unlock(&buffer_mutex);
  return FLAC__STREAM_DECODER_WRITE_STATUS_CONTINUE;
}

void f_meta(const FLAC__StreamDecoder *decoder, const FLAC__StreamMetadata *metadata, void *client_data){
  printf("GOT META\n");
}
 
void f_err(const FLAC__StreamDecoder *decoder, FLAC__StreamDecoderErrorStatus status, void *client_data){
  printf("GOT ERR\n");
}


FLAC__StreamDecoder* dec;
FLAC__StreamDecoderInitStatus status;

// -----------------------------------------------------------------------------------

int pulse_connected = 0;
int want_reconnect = 0;

int disconnect_pulse(){
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


void connect_pulse(){
  
  if (pulse_connected == 1) disconnect_pulse(); 
  
  pthread_mutex_lock(&pulse_mutex);
  if (want_sample_rate > 0){
  current_sample_rate = want_sample_rate;
  want_sample_rate = 0;
  }
  
  int error = 0;

  pab.maxlength = (uint32_t) -1;
  pab.fragsize = (uint32_t) -1;
  pab.minreq = (uint32_t) -1;
  pab.prebuf = (uint32_t) -1;
  pab.tlength =  (current_sample_rate * 4 * (config_dev_buffer / 1000.0));
  
  //printf("pa: Connect to PulseAudio\n");
  ss.format = PA_SAMPLE_S16LE;
  ss.channels = 2;
  ss.rate = current_sample_rate;
  
  s = pa_simple_new(NULL,                // Use default server
                    "Tauon Music Box",   // Application name
                    PA_STREAM_PLAYBACK,  // Flow direction
                    NULL,                // Use the default device
                    "Music",             // Description
                    &ss,                 // Format
                    NULL,                // Channel map
                    &pab,                // Buffering attributes
                    &error               // Error
                    );
  
  if (error > 0){

    printf("pa: PulseAudio init error: ");
    printf(pa_strerror(error));
    printf("\n");
    mode = STOPPED;
  }
  else pulse_connected = 1;
  
  pthread_mutex_unlock(&pulse_mutex);
      
}

void stop_decoder(){
  
  if (decoder_allocated == 0) return;
  
  switch(codec){
  case OPUS:
    op_free(opus_dec);
    break;
  case VORBIS:
    ov_clear(&vf);
    break;
  case FLAC:
    FLAC__stream_decoder_finish(dec);
    break;
  case MPG:
    mpg123_close(mh);
    break;
  case FFMPEG:
    pclose(ffm);
  }
  decoder_allocated = 0;
}                                        

void decode_seek(int abs_ms, int sample_rate){
  
  switch (codec){
  case FLAC:
    FLAC__stream_decoder_seek_absolute (dec, (int) sample_rate * (abs_ms / 1000.0));
    break;
  case OPUS:
    op_pcm_seek(opus_dec, (int) sample_rate * (abs_ms / 1000.0)); 
    break;
  case VORBIS:
    ov_pcm_seek (&vf, (ogg_int64_t) sample_rate * (abs_ms / 1000.0));
    break;
  case MPG:
    mpg123_seek(mh, (int) sample_rate * (abs_ms / 1000.0), SEEK_SET);
    break;
  case FFMPEG:
    stop_ffmpeg();
    start_ffmpeg (load_target_file, abs_ms);
    break;
    }
  
}
                            
int load_next(){
  // Function to load a file / prepare decoder
  
  //printf("pa: Loading file: %s\n", load_target_file);
  
  stop_decoder();
 
  int channels;
  int encoding;
  long rate;
  int e = 0;
  
  char *ext;
  ext = strrchr(load_target_file, '.');
  
  codec = UNKNOWN;
  current_length_count = 0;
  buffering = 0;
  
  if (load_target_file[0] == 'h') buffering = 1;
  
  char peak[35];
  
  if (strcmp(ext, ".ape") == 0 || strcmp(ext, ".APE") == 0 ||
      strcmp(ext, ".m4a") == 0 || strcmp(ext, ".M4A") == 0 ||
      strcmp(ext, ".tta") == 0 || strcmp(ext, ".TTA") == 0 ||
      strcmp(ext, ".wma") == 0 || strcmp(ext, ".WMA") == 0 ||
      strcmp(ext, ".wav") == 0 || strcmp(ext, ".WAV") == 0 ||
      load_target_file[0] == 'h'){
        codec = FFMPEG;
        start_ffmpeg (load_target_file, load_target_seek);
        pthread_mutex_lock(&buffer_mutex);
        if (current_sample_rate != 44100){
          sample_change_byte = (buff_filled + buff_base) % BUFF_SIZE;
          want_sample_rate = 44100;
        }
        pthread_mutex_unlock(&buffer_mutex);
        return 0;
  }
  
  
  if ((fptr = fopen(load_target_file, "rb")) == NULL) {
    
      printf("pa: Error opening file\n");
      return 1;
  }
  
  fread(peak, sizeof (peak), 1, fptr); 
  
  if (memcmp(peak, "fLaC", 4) == 0) {
    codec = FLAC;
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
  
                 
  switch(codec){

    // Unlock the output thread mutex cause loading could take a while?..
    // and we dont wanna interrupt the output for too long.
    case OPUS:
    
    opus_dec = op_open_file (load_target_file, &e);
    decoder_allocated = 1;
    
    if (e != 0){
      printf("pa: Error reading ogg file (expecting opus)\n");
      return 1;    
    }
    else{
      pthread_mutex_lock(&buffer_mutex);
      if (current_sample_rate != 48000){
        sample_change_byte = (buff_filled + buff_base) % BUFF_SIZE;
        want_sample_rate = 48000;
      }
      current_length_count = op_pcm_total(opus_dec, -1);
      
      if (load_target_seek > 0) {
        printf("pa: Start at position %d\n", load_target_seek);
        op_pcm_seek(opus_dec, (int) 48000 * (load_target_seek / 1000.0)); 
        reset_set_value = op_raw_tell(opus_dec);
        reset_set = 1;
        reset_set_byte = (buff_filled + buff_base) % BUFF_SIZE;
        load_target_seek = 0;
      }
      pthread_mutex_unlock(&buffer_mutex);
      return 0;
    }
      
    break;  
    case VORBIS:

    e = ov_fopen(load_target_file, &vf);
    decoder_allocated = 1;
    if (e != 0){
      printf("pa: Error reading ogg file (expecting vorbis)\n");

      return 1;
    } else {
      
      vi = *ov_info(&vf, -1);
      
      pthread_mutex_lock(&buffer_mutex);
      //printf("pa: Vorbis samplerate is %lu\n", vi.rate);
      if (current_sample_rate != vi.rate){
        sample_change_byte = (buff_filled + buff_base) % BUFF_SIZE;
        want_sample_rate = vi.rate;
      }
      current_length_count = ov_pcm_total(&vf, -1);
      
      if (load_target_seek > 0) {
        //printf("pa: Start at position %d\n", load_target_seek);
        ov_pcm_seek (&vf, (ogg_int64_t) vi.rate * (load_target_seek / 1000.0));
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
      if ( FLAC__stream_decoder_init_file(
        dec,
        load_target_file,
        &f_write,
        NULL, //&f_meta,
        &f_err,
        0) == FLAC__STREAM_DECODER_INIT_STATUS_OK) { 
          
        decoder_allocated = 1;
        return 0;
          
      } else return 1;
      
      break;
    
    case MPG:

      mpg123_open(mh, load_target_file);
      decoder_allocated = 1;
      mpg123_getformat(mh, &rate, &channels, &encoding);
      mpg123_scan(mh);
      //printf("pa: %lu. / %d. / %d\n", rate, channels, encoding);

      pthread_mutex_lock(&buffer_mutex);
      if (current_sample_rate != rate){
        sample_change_byte = (buff_filled + buff_base) % BUFF_SIZE;
        want_sample_rate = rate;
      }
      current_length_count = (u_int) mpg123_length(mh);
    
      if (encoding == MPG123_ENC_SIGNED_16){
        
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

void end(){
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

void decoder_eos(){
  // Call once current decode steam has run out
  printf("pa: End of stream\n");
  if (next_ready == 1){
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


void pump_decode(){
  // Here we get data from the decoders to fill the main buffer
  
  if (codec == FLAC){
    // FLAC decoding

    switch (FLAC__stream_decoder_get_state(dec)) {
      case FLAC__STREAM_DECODER_END_OF_STREAM:
        decoder_eos();
        break;
          
      default:
        FLAC__stream_decoder_process_single(dec); 

    }
    
    if (load_target_seek > 0){
      //printf("pa: Set start position %d\n", load_target_seek);
      
      int rate = current_sample_rate;
      if (want_sample_rate > 0) rate = want_sample_rate;
      
      FLAC__stream_decoder_seek_absolute (dec, (int) rate * (load_target_seek / 1000.0));
      pthread_mutex_lock(&buffer_mutex);
      reset_set_value = rate * (load_target_seek / 1000.0);
      reset_set = 1;
      reset_set_byte = (buff_filled + buff_base) % BUFF_SIZE;
      load_target_seek = 0;
      pthread_mutex_unlock(&buffer_mutex);
    }         

  } else if (codec == OPUS){
    
    unsigned int done;
    
    done = op_read_stereo(opus_dec, opus_buffer, 1024*2) * 2;
    unsigned int i = 0;
    
    pthread_mutex_lock(&buffer_mutex);
    while (i < done){
      buff16l[(buff_filled + buff_base) % BUFF_SIZE] = opus_buffer[i];
      buff16r[(buff_filled + buff_base) % BUFF_SIZE] = opus_buffer[i + 1];
      buff_filled++;
      i += 2;
    }
    pthread_mutex_unlock(&buffer_mutex);
    if (done == 0){
      decoder_eos();
    }    
    
                      
  } else if (codec == VORBIS){
    
    unsigned int done;
    int stream;
    done = ov_read(&vf, parse_buffer, 2048*2, 0, 2, 1, &stream);
    unsigned int i = 0;
    pthread_mutex_lock(&buffer_mutex);
    while (i < done){
    
      buff16l[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) ((parse_buffer[i + 1] << 8) | (parse_buffer[i+0] & 0xFF));
      buff16r[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) ((parse_buffer[i + 3] << 8) | (parse_buffer[i+2] & 0xFF));
      buff_filled++;
      i += 4;
    }
    pthread_mutex_unlock(&buffer_mutex);
    if (done == 0){
      decoder_eos();
    }    
    
  } else if (codec == MPG){
    // MP3 decoding
    
    size_t done;

    mpg123_read(mh, parse_buffer, 2048 * 2, &done);

    
    unsigned int i = 0;
    pthread_mutex_lock(&buffer_mutex);
    while (i < done){
    
      buff16l[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) ((parse_buffer[i + 1] << 8) | (parse_buffer[i+0] & 0xFF));
      buff16r[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) ((parse_buffer[i + 3] << 8) | (parse_buffer[i+2] & 0xFF));
      buff_filled++;
      i += 4;
    }
    pthread_mutex_unlock(&buffer_mutex);                    
    if (done == 0){
      decoder_eos();
    }
  } else if (codec == FFMPEG) {
    
    int i = 0;
    int b = 0;
    int done = 0;
    
    while (b < 2048){
      if (feof(ffm)){
        done = 1;
        break;
      }
      ffm_buffer[b] = fgetc(ffm);
      b++;
    }
                                
    if (b % 2 == 1){
      printf("pa: Uneven data\n");
      decoder_eos();
      return;
    }
    pthread_mutex_lock(&buffer_mutex);
    while (i < b){
        
      buff16l[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) ((ffm_buffer[i + 1] << 8) | (ffm_buffer[i] & 0xFF));
      buff16r[(buff_filled + buff_base) % BUFF_SIZE] = (int16_t) ((ffm_buffer[i + 3] << 8) | (ffm_buffer[i + 2] & 0xFF));
      buff_filled++;
      i += 4;
    }
    pthread_mutex_unlock(&buffer_mutex);
    if (done == 1){
      printf("pa: FFMPEG has finished\n");
      decoder_eos();

    }
                               
    
  }

}

                                       
// ------------------------------------------------------------------------------------
// Audio output thread

float gate = 1.0;  // Used for ramping
    
int out_thread_running = 0; // bool
    
void *out_thread(void *thread_id){    

  out_thread_running = 1;
  int b = 0;
  double testa, testb;
  
  t_start = get_time_ms();
  
  while (out_thread_running == 1){
    
    if (buffering == 1 && buff_filled > 9000){

      buffering = 0;
      printf("pa: Buffering -> Playing\n");
      sleep(1);
      connect_pulse();

    }
    
    if (buff_filled < 1000 && load_target_file[0] == 'h'){

        disconnect_pulse();
        if (mode == RAMP_DOWN) gate = 0;
        printf("pa: Buffering...\n");
        buffering = 1;

      }
    
    // Process decoded audio data and send out
    if ((mode == PLAYING || mode == RAMP_DOWN || mode==ENDING) && buff_filled > 0 && buffering == 0){
      
      pthread_mutex_lock(&buffer_mutex);
      
      b = 0; // byte number  

      peak_roll_l = 0;
      peak_roll_r = 0;
      
      //printf("pa: Buffer is at %d\n", buff_filled);
      
      // Fill the out buffer...
      while (buff_filled > 0) {
          
                  
          // Truncate data if gate is closed anyway
          if (mode == RAMP_DOWN && gate == 0) break;
        
          if (want_sample_rate > 0 && sample_change_byte == buff_base){
            //printf("pa: Set new sample rate\n");
            connect_pulse();
            break;
          } 
          
          if (reset_set == 1 && reset_set_byte == buff_base){
            printf("pa: Reset position counter\n");
            reset_set = 0;
            position_count = reset_set_value;
          }
          
          // Ramp control ---
          if (mode == RAMP_DOWN){
            gate -= ramp_step(current_sample_rate, 5);
            if (gate < 0) gate = 0; }

          if (gate < 1 && mode == PLAYING){
            gate += ramp_step(current_sample_rate, 5);
            if (gate > 1) gate = 1; 
          }
          
          // Volume control ---
          if (volume_want > volume_on){
            volume_on += ramp_step(current_sample_rate, volume_ramp_speed);
            
            if (volume_on > volume_want){
              volume_on = volume_want;
            }
          }

          if (volume_want < volume_on){
            volume_on -= ramp_step(current_sample_rate, volume_ramp_speed);
            
            if (volume_on < volume_want){
              volume_on = volume_want;
            }
          }                                
          
          if (abs(buff16l[buff_base]) > peak_roll_l) peak_roll_l = abs(buff16l[buff_base]);
          if (abs(buff16r[buff_base]) > peak_roll_r) peak_roll_r = abs(buff16r[buff_base]);
                                  
          // Apply total volume adjustment (logarithmic)
          buff16l[buff_base] *= pow(gate * volume_on, 2.0);
          buff16r[buff_base] *= pow(gate * volume_on, 2.0);
          
          // Pack integer audio data to bytes
          out_buf[b    ] = (buff16l[buff_base]) & 0xFF;
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
      if (b > 0){
        
        if (peak_roll_l > peak_l) peak_l = peak_roll_l;
        if (peak_roll_r > peak_r) peak_r = peak_roll_r;
        
        pthread_mutex_lock(&pulse_mutex);
        if (pulse_connected == 0){
          printf("pa: Error, not connected to any output!\n");
        } else {
          
          /* t_end = get_time_ms(); */
          /* testa = (t_end - t_start); */
          /* t_start = t_end; */
          
          
          pa_simple_write (s, out_buf, b, &error); 
  
          /* t_end = get_time_ms(); */
          /* testb = (t_end - t_start); */
          /* t_start = t_end; */
          
          /* if (testa + testb > config_dev_buffer - 5){ */
          /*   printf("Write at: %f\n", testa); */
          /*   printf("Took: %f\n", testb); */
          /*   printf("Buffer: %d\n", buff_filled); */
          /* } */
        
          
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

void *main_loop(void *thread_id){
  
  
  pthread_t out_thread_id;
  pthread_create(&out_thread_id, NULL, out_thread, NULL); 
  
  
  int error = 0;
    
  int load_result = 0;
  
  // MP3 decoder --------------------------------------------------------------

  mpg123_init();
  mh = mpg123_new(NULL, &error);
  mpg123_param(mh, MPG123_ADD_FLAGS, MPG123_SKIP_ID3V2, 0);
  mpg123_param(mh, MPG123_RESYNC_LIMIT, 10000, 0);
  
  // FLAC decoder ----------------------------------------------------------------
  
  dec = FLAC__stream_decoder_new();

  // Main loop ---------------------------------------------------------------
  while (1){
    
  /* test1++; */
  /* if (test1 > 650){ */
  /*   printf("pa: Status: mode %d, command %d, buffer %d\n", mode, command, buff_filled); */
  /*   test1 = 0; */
  /* } */

    if (command != NONE){
      
      if (command == EXIT){
      break;
      }
      switch (command) {
      case PAUSE:
        if (mode == PLAYING){
          mode = PAUSED;
          disconnect_pulse();
        }
        command = NONE;
        break;
      case RESUME:
        if (mode == PAUSED){
          mode = PLAYING;
          connect_pulse();
        }
        command = NONE;  
        break;
      case STOP:
        if (mode == STOPPED){
          command = NONE;
        }
        else if (mode == PLAYING){
          mode = RAMP_DOWN;
        }
        if ((mode == RAMP_DOWN && gate == 0) || mode == PAUSED){
          end();
        }
        break;
      case START:
        if (mode == PLAYING){
          mode = RAMP_DOWN;
        }
        if (mode == RAMP_DOWN && gate == 0){
          command = LOAD;
        } else break;
      case LOAD:
              
        load_result = load_next();
        
        if (load_result == 0){
          pthread_mutex_lock(&buffer_mutex);
          position_count = 0;
          buff_base = 0;
          buff_filled = 0;
          gate = 0;
          sample_change_byte = 0;
          reset_set_byte = 0;
          
          if (want_sample_rate == 0 && pulse_connected == 0){
            connect_pulse();
            
          }
          
          mode = PLAYING;
          command = NONE;
          pthread_mutex_unlock(&buffer_mutex);
        
          
        } else {
          printf("pa: Load file failed\n");
          command = NONE;
          mode = NONE;
        }
              
        break;
        
      } // end switch
      
    } // end if none
    
    
    if (command == SEEK){
      
      if (mode == PLAYING){
        
        mode = RAMP_DOWN;
        
        if (want_sample_rate > 0) decode_seek(seek_request_ms, want_sample_rate);
        else decode_seek(seek_request_ms, current_sample_rate);
        
        if (want_sample_rate > 0) position_count = want_sample_rate * (seek_request_ms / 1000.0);
        else position_count = current_sample_rate * (seek_request_ms / 1000.0);

      } else if (mode == PAUSED) {
        

        
        if (want_sample_rate > 0) decode_seek(seek_request_ms, want_sample_rate);
        else decode_seek(seek_request_ms, current_sample_rate);
        
        if (want_sample_rate > 0) position_count = want_sample_rate * (seek_request_ms / 1000.0);
        else position_count = current_sample_rate * (seek_request_ms / 1000.0);
        
        pthread_mutex_lock(&buffer_mutex);
        
        buff_base = 0;
        buff_filled = 0;
        if (pulse_connected == 1){
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
                          
      if (mode == RAMP_DOWN && gate == 0){
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
    if (mode == PLAYING){
      while (buff_filled < BUFF_SAFE && mode != ENDING){
        pump_decode();

      }
    }
    
    if (mode == ENDING && buff_filled == 0){
      printf("pa: Buffer ran out at end of track\n");
      end();

    }
    if (mode == ENDING && next_ready == 1){
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
  
  pthread_mutex_unlock(&buffer_mutex);
                                  
  return thread_id;
}


// ---------------------------------------------------------------------------------------
// Begin exported functions

int init(){
  printf("ph: PHAzOR starting up\n");
  if (main_running == 0){
    main_running = 1;
    pthread_t main_thread_id;
    pthread_create(&main_thread_id, NULL, main_loop, NULL); 
  } else printf("ph: Cannot init. Main loop already running!\n");
  return 0;
}
                                  
int get_status(){
  return mode;
}

int start(char *filename, int start_ms){

  while (command != NONE){
    usleep(1000);
  }
  
  load_target_seek = start_ms;
  strcpy(load_target_file, filename);  
  
  if (mode == PLAYING){
    command = START;
  } else command = LOAD;
  
  return 0;
}


int next(char *filename, int start_ms){

  while (command != NONE){
    usleep(1000);
  }

  if (mode == STOPPED){
    start(filename, start_ms);
  } else {
    load_target_seek = start_ms;
    strcpy(load_target_file, filename);  
    next_ready = 1;
  }
                                        
  return 0;
}

int pause(){
  while (command != NONE){
      usleep(1000);
    }  
  command = PAUSE;
  return 0;
}

int resume(){
  while (command != NONE){
      usleep(1000);
    }  
  command = RESUME;
  return 0;
}
                                  
int stop(){
  while (command != NONE){
      usleep(1000);
    }
  command = STOP;
  return 0;
}

int seek(int ms_absolute, int flag){
  
  while (command != NONE){
      usleep(1000);
    }
                                     
  config_fast_seek = flag;
  seek_request_ms = ms_absolute;
  command = SEEK;  
  
  return 0;
}

int set_volume(int percent){
  volume_want = percent / 100.0;
  volume_on = percent / 100.0;
  
  return 0;
}

int ramp_volume(int percent, int speed){
  volume_ramp_speed = speed;
  volume_want = percent / 100.0;
  return 0;
}
                                       
int get_position_ms(){
  if (reset_set == 0 && current_sample_rate > 0){
    return (int) ((position_count / (float) current_sample_rate) * 1000.0);
  } else return 0;
}
 
int get_length_ms(){
  if (reset_set == 0 && current_sample_rate > 0 && current_length_count > 0){
    
    return (int) ((current_length_count / (float) current_sample_rate) * 1000.0);
  } else return 0;
}
                                                    
void config_set_dev_buffer(int ms){
  config_dev_buffer = ms;
}
                                  
int get_level_peak_l(){
  int peak = peak_l;
  peak_l = 0;
  return peak;
}  
int get_level_peak_r(){
  int peak = peak_r; 
  peak_r = 0;
  return peak;
}  

int shutdown(){
  while (command != NONE){
      usleep(1000);
    }
  command = EXIT;
  return 0;
}

                                      
