# Binary setup on Windows

Release bundle should 'just work' by running tmb.exe. Otherwise make sure Visual C++ Runtime and DirectX are installed.

# Source setup on Linux

BASS binaries are included with release package or can be downloaded from http://www.un4seen.com/. See [libraries.txt](libraries.txt) for needed files in lib/ folder (use 64 bit versions). Stagger and pyxhook also included in release due to failing to install with pip.

Use the following commands to install other dependencies:

Arch Linux:

        $ sudo pacman -S python3 sdl2 sdl2_image sdl2_ttf xclip python-pip python-pillow
        $ sudo pip3 install hsaudiotag3k pylast pyperclip pysdl2 flask

Ubuntu (not recently tested):

        $ sudo apt-get install libsdl2-2.0-0 libsdl2-ttf-2.0-0 libsdl2-image-2.0-0 python3-pip xclip python3-pil
        $ sudo pip3 install hsaudiotag3k pylast pyperclip pysdl2 flask



Finally run using python 3 (Alternatively create a desktop or launcher shortcut. Make sure to set the working directory to the directory you extracted the program files to).

    $ python3.5 tmb.py
