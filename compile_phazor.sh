#!/bin/bash

# Needed libraries: flac, (lib)mpg123, libopusfile, libvorbis, libpulse

gcc src/phazor/phazor.c -D_REENTRANT -lpulse-simple -lFLAC -lmpg123 -lvorbis -lvorbisfile -I/usr/include/opus -lopusfile -shared -pthread -o libphazor.so -fPIC -Wall # -Wextra 
mkdir -p lib
mv libphazor.so lib/libphazor.so


