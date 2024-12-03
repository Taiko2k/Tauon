#!/bin/bash

set -e

gcc src/phazor/kissfft/kiss_fftr.c src/phazor/kissfft/kiss_fft.c src/phazor/phazor.c \
    $(pkg-config --cflags --libs python3 samplerate wavpack opusfile vorbisfile libmpg123 flac libopenmpt libgme libpipewire-0.3) \
    -shared -o libphazor-pw.so -fPIC -Wall -O3 -g -DPIPE #-Wextra

mkdir -p build
mv libphazor-pw.so build/libphazor-pw.so
