#!/bin/bash

set -e

gcc src/phazor/kissfft/kiss_fftr.c src/phazor/kissfft/kiss_fft.c src/phazor/phazor.c \
    `pkg-config --cflags --libs samplerate wavpack opusfile vorbisfile libmpg123 flac libopenmpt libgme libpipewire-0.3` \
    -shared -o libphazor.so -fPIC -Wall -O3 -g #-Wextra
mkdir -p lib
mv libphazor.so lib/libphazor.so

