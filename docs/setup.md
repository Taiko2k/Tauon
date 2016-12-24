# Binary release setup on Windows

Release bundle should work by running tauon.exe. Otherwise ensure Visual C++ Runtime 2015 and DirectX are installed.


# Setup on Linux

#### Backend:

BASS binaries are included with release package or can be downloaded from http://www.un4seen.com/. See [libraries.txt](libraries.txt) for needed files in lib/ folder (use 64 bit versions).

Alternatively GStreamer can be used as the audio backend and thus not requiring proprietary libraries. (Install on Arch: python-gobject). However the following player features will not be avaliable:

 - Inbound streaming
 - Outbound streaming
 - Track crossfade
 - Pause fade
 - Visualizations
 - Some audio codecs depending on gstreamer plugins installed on your system

#### Use the following commands to install other dependencies:


###Arch Linux:

        $ sudo pacman -S python3 sdl2 sdl2_image sdl2_ttf python-pip python-pillow python-pylast python-flask python-setuptools python-xlib pulseaudio-alsa
        $ sudo pip3 install hsaudiotag3k pysdl2 stagger
	
   Upgrading Note: Previously (v some packages were advised to be installed via pip now use pacman instead. To remove existing files that will conflict when upgrading use this command first (not tested):  
   
        $ sudo pip3 uninstall flask pylast click Werkzeug itsdangerous Jinja2 MarkupSafe python3-xlib
   

###Ubuntu:

        $ sudo apt-get install libsdl2-2.0-0 libsdl2-ttf-2.0-0 libsdl2-image-2.0-0 python3-pip python3-pil python3-setuptools
        $ sudo pip3 install hsaudiotag3k pylast pysdl2 flask stagger python3-xlib



Finally run using python 3 (Alternatively create a desktop or launcher shortcut. Set the command to "python3 /path/to/program/tauon.py").

    $ python3 tauon.py


# Development setup on OS X


OSX is not officially supported, but the program may run. As a rough guide to get started: 

Install Python 3, SDL, SDL_ttf and SDL_image frameworks
Install Bass libraries to programs /lib folder, required are libbass.dylib, libbassenc.dylib and libbassmix.dylib
Install Python libraries (Install pip if required $ sudo easy_install pip):

        $ sudo python3 -m pip install hsaudiotag3k pylast pysdl2 flask stagger

Finally run from install directroy using:

	$ python3 tauon.py


# Development setup on Windows

As a rough guide:

- Download and run python3, pywin32, pillow and pysdl2 installers for windows
- Find and place BASS and SDL dll's in lib directory as listed in libraries.txt
- Install python libraries with cmd command: python -m pip install hsaudiotag3k pylast pysdl2 flask stagger

Start by running command from program directroy: python tauon.py  
Install any other dependencies as required, see cmd output for details etc

