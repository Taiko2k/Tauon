#!/bin/bash

gcc src/phazor/kissfft/kiss_fftr.c src/phazor/kissfft/kiss_fft.c src/phazor/phazor.c `pkg-config --cflags --libs ao wavpack samplerate opusfile vorbisfile libmpg123 flac libopenmpt` -shared -o libphazor.so -fPIC -Wall -O3 -D AO -g # -Wextra
mkdir -p lib
mv libphazor.so lib/libphazor.so

