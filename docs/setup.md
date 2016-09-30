# Binary release setup on Windows

Release bundle should 'just work' by running tauon.exe. Otherwise ensure Visual C++ Runtime 2015 and DirectX are installed.


# Development setup on Linux

BASS binaries are included with release package or can be downloaded from http://www.un4seen.com/. See [libraries.txt](libraries.txt) for needed files in lib/ folder (use 64 bit versions).

Use the following commands to install other dependencies:

Arch Linux:

        $ sudo pacman -S python3 sdl2 sdl2_image sdl2_ttf xclip python-pip python-pillow
        $ sudo pip3 install hsaudiotag3k pylast pysdl2 flask python3-xlib stagger

   Note: You mas also need to install pulseaudio-alsa for desktop audio to function correctly

Ubuntu:

        $ sudo apt-get install libsdl2-2.0-0 libsdl2-ttf-2.0-0 libsdl2-image-2.0-0 python3-pip xclip python3-pil python3-setuptools
        $ sudo pip3 install hsaudiotag3k pylast pysdl2 flask python3-xlib stagger



Finally run using python 3 (Alternatively create a desktop or launcher shortcut. Set the command to "python3 /path/to/program/tauon.py").

    $ python3 tauon.py

  Note: Python 3.5 reccomended (or later), you may need to specifiy this if you have multiple python versions i.e python3.5

# Development setup on OS X

OSX is not fully supported, but the program may run. As a rough guide to get started: 

Install Python 3, SDL, SDL_ttf and SDL_image frameworks
Install Bass libraries to programs /lib folder, required are libbass.dylib, libbassenc.dylib and libbassmix.dylib
Install Python libraries (Install pip if required $ sudo easy_install pip):

        $ sudo python3 -m pip install hsaudiotag3k pylast pysdl2 flask stagger

Finally run from install directroy using:

	$ python3 tauon.py
