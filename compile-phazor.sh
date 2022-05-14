#!/bin/bash

set -e

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    gcc src/phazor/kissfft/kiss_fftr.c src/phazor/kissfft/kiss_fft.c src/phazor/phazor.c `pkg-config --cflags --libs samplerate wavpack libpulse-simple opusfile vorbisfile libmpg123 flac libopenmpt` -shared -o libphazor.so -fPIC -Wall -O3 -g #-Wextra
    mkdir -p lib
    mv libphazor.so lib/libphazor.so
elif [[ "$OSTYPE" == "darwin"* ]]; then
    gcc src/phazor/kissfft/kiss_fftr.c src/phazor/kissfft/kiss_fft.c src/phazor/phazor.c `pkg-config --cflags --libs ao wavpack samplerate opusfile vorbisfile libmpg123 flac libopenmpt` -shared -o libphazor.so -fPIC -Wall -O3 -D AO -g # -Wextra
    mkdir -p lib
    mv libphazor.so lib/libphazor.so
else
    echo -e "== == == == == == \n\
 Unsupported OS. \n\
== == == == == =="
    exit 1
fi
