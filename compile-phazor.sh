#!/bin/bash

set -e

gcc src/phazor/kissfft/kiss_fftr.c src/phazor/kissfft/kiss_fft.c src/phazor/phazor.c \
    $(pkg-config --cflags --libs python3 samplerate wavpack opusfile vorbisfile libmpg123 flac libopenmpt libgme) \
    -shared -o libphazor.so -fPIC -Wall -O3 -g #-Wextra

mkdir -p build
mv libphazor.so build/libphazor.so
