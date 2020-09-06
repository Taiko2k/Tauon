#!/bin/bash

# Needed libraries: flac, (lib)mpg123, libopus, libvorbis, libpulse

gcc src/phazor/phazor.c -D_REENTRANT -lpulse-simple -lFLAC -lmpg123 -lvorbis -lvorbisfile -I/usr/include/opus -lopusfile -shared -pthread -o libphazor.so -fPIC -Wall -Wextra 
mkdir lib
mv libphazor.so lib/libphazor.so


