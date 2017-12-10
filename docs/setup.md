
## Setup release on Windows

Program should work after running setup installer exe. Otherwise ensure Visual C++ Runtime 2015 and DirectX are installed.

## Dependencies for manual setup

Take special note of the entires with bolded version numbers meaning they specifically require the newer versions of those libraries.

Italicized entires are included in the releasae zip package.

 - Python 3 >= 3.5
 - SDL >= **2.0.5**
 - SDL_Image
 - Python Pillow
 - Python Stagger
 - Python hsaudiotag
 - Python pylast
 - Noto Fonts and Notos Fonts Emoji (reccomended, linux only)
 - Python flask (optional)
 - Python gi.repository/pygobject (Linux only)
 - Python pyCairo >= **1.10.1** (Linux only)
 - Python Win32api  (Windows only)
 - *Bass*
 - *BassEnc*
 - *BassMix*
 - *Bassenc_ogg*
 - *Bass_fx*
 - *Bassopus* (optional)
 - *Bassflac* (optional)
 - *Bass_ape* (optional)
 - *Basstta* (optional)
 - *Basswma* (optional, windows only)
 - *Basswv* (optional)
 - *Bass_tta* (optional)
 - *Bass_aac* (optional, linux only)
 - *Bassalac* (optional)
 - *Python pysdl2*
 - *Python pyxhook* (Linux only, optional)
 - *Python pylyrics*

## Development setup on Arch Linux

1. Install from AUR or install dependencies manually such as listed in the PKGBUILD.
2. Copy program files or release package contents to a new folder.
3. Run using ```python tauon.py```

## Development setup on Ubuntu

Something like this:

1. Download and extract the Tauon Music Box release package for linux from releases section.
2. Install dependencies ```sudo apt-get install libsdl2-2.0-0 libsdl2-image-2.0-0 python3-pylast python3-xlib fonts-noto python3-pil python3-gi python3-bs4```
2. Build latest pycairo.
    1. Download or clone from https://github.com/pygobject/pycairo
    2. Install build deps. ```sudo apt-get install python3-dev libcairo2-dev```
    3. Build pycairo ```sudo python3 setup.py build``` and copy resulting "cairo" folder (in build/lib.linux-x86_64-36) to extracted tauon-music-box folder
3. Download or clone hsaudiotag https://github.com/hsoft/hsaudiotag and copy inner "hsaudiotag" folder to extracted tauon-music-box folder
4. Download or clone stagger https://github.com/lorentey/stagger and copy inner "stagger" folder to extracted tauon-music-box folder
5. Finally, run from extracted tauon-music-box directory using ```python3 tauon.py```
