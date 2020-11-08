#!/bin/bash

gcc src/phazor/phazor.c `pkg-config --cflags --libs samplerate libpulse-simple opusfile vorbisfile libmpg123 flac` -shared -o libphazor.so -fPIC -Wall # -Wextra 
mkdir -p lib
mv libphazor.so lib/libphazor.so

