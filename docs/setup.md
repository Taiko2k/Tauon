
## Setup release on Windows

Program should work after running setup installer exe. Otherwise ensure Visual C++ Runtime 2015 and DirectX are installed.

	
## PKGBUILD setup on Arch Linux

Open terminal to directory with downloaded PKGBUILD and install. For example using yaourt:

    $ yaourt -P -i

To uninstall:

    $ sudo pacman -R tauon-music-box
 
#### Possible conflicts when libraries have previously been installed via pip: 

To remove pip flask and python-xlib:  
   
        $ sudo pip3 uninstall flask pylast click Werkzeug itsdangerous Jinja2 MarkupSafe python3-xlib
 
 
## Dependencies

 - SDL >= 2.0.5
 - SDL_Image
 - Bass
 - BassEnc
 - BassMix
 - Bassenc_ogg (optional)
 - Bassopus (optional)
 - Bassflac (optional)
 - Bass_ape (optional)
 - Basstta (optional)
 - Basswma (optional)
 - Basswv (optional)
 - xclip (Linux only)
 - Python 3 >= 3.5
 - Python Win32api  (Windows only)
 - Python pysdl2
 - Python Pillow
 - Python Stagger
 - Python hsaudiotag
 - Python pylast
 - Python flask (optional)
 - Python gi.repository/pygobject (Linux only)
 - Python pyCairo >= 1.10.1 (Linux only)
 - Python xlib
 - Python pyxhook (Linux only, optional)
 
 Bass and SDL dynamic libraries should be placed in /lib folder.
 
## Running Manually

Run using python

    $ python tauon.py


