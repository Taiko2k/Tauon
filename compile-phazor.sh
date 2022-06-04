#!/bin/bash

set -e

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    gcc src/phazor/kissfft/kiss_fftr.c src/phazor/kissfft/kiss_fft.c src/phazor/phazor.c \
        `pkg-config --cflags --libs samplerate wavpack libpulse-simple opusfile vorbisfile libmpg123 flac libopenmpt` \
        -shared -o libphazor.so -fPIC -Wall -O3 -g #-Wextra
    mkdir -p lib
    mv libphazor.so lib/libphazor.so

elif [[ "$OSTYPE" == "darwin"* ]]; then
    gcc src/phazor/kissfft/kiss_fftr.c src/phazor/kissfft/kiss_fft.c src/phazor/phazor.c \
        `pkg-config --cflags --libs ao wavpack samplerate opusfile vorbisfile libmpg123 flac libopenmpt` \
        -shared -o libphazor.so -fPIC -Wall -O3 -D AO -g # -Wextra
    mkdir -p lib
    mv libphazor.so lib/libphazor.so

elif [[ "$OSTYPE" == "msys"* ]]; then
    if [[ "$gcc -v" -eq 0 ]]; then
        ( PATH="/mingw64/bin:$PATH"
	    gcc src/phazor/kissfft/kiss_fftr.c src/phazor/kissfft/kiss_fft.c src/phazor/phazor.c \
            `pkg-config --cflags --libs ao samplerate wavpack opusfile vorbisfile libmpg123 flac libopenmpt` \
            -shared -o libphazor.so -fPIC -Wall -O3 -D AO -D WIN -g #-Wextra
	    )
    	mkdir -p lib
    	mv libphazor.so lib/libphazor.so
    else
	    echo -e "Is this MSYS2? \n\
Make sure you're following the wiki guide for Windows build: \n\
https://github.com/Taiko2k/TauonMusicBox/wiki/Building-for-Windows \n\n\
Read there please, then try again."
        exit 1
    fi

else
    echo -e "== == == == == == \n\
 Unsupported OS. \n\
== == == == == =="
    exit 1
fi
