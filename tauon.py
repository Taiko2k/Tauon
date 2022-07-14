#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import pickle
import sys
from ctypes import pointer
from gi.repository import GLib

if sys.platform != 'win32':
    import fcntl


# Early arg processing
def transfer_args_and_exit():
    import urllib.request
    base = "http://localhost:7813/"

    if len(sys.argv) <= 1:
        url = base + "raise/"
        urllib.request.urlopen(url)

    for item in sys.argv:

        if not item.endswith(".py") and not item.startswith("-") and not item.endswith("exe") and (item.startswith("file://") or os.path.exists(item)):
            import base64
            url = base + "open/" + base64.urlsafe_b64encode(item.encode()).decode()
            urllib.request.urlopen(url)
        if item == "--play-pause":
            url = base + "playpause/"
            urllib.request.urlopen(url)
        if item == "--play":
            url = base + "play/"
            urllib.request.urlopen(url)
        if item == "--pause":
            url = base + "pause/"
            urllib.request.urlopen(url)
        if item == "--stop":
            url = base + "stop/"
            urllib.request.urlopen(url)
        if item == "--next":
            url = base + "next/"
            urllib.request.urlopen(url)
        if item == "--previous":
            url = base + "previous/"
            urllib.request.urlopen(url)
        if item == "--shuffle":
            url = base + "shuffle/"
            urllib.request.urlopen(url)
        if item == "--repeat":
            url = base + "repeat/"
            urllib.request.urlopen(url)

    sys.exit()


if "--no-start" in sys.argv:
    transfer_args_and_exit()

t_title = 'Tauon Music Box'
os.environ["SDL_VIDEO_X11_WMCLASS"] = t_title  # This sets the window title under some desktop environments

install_directory = os.path.dirname(os.path.abspath(__file__))

pyinstaller_mode = False
if 'base_library' in install_directory:
    pyinstaller_mode = True
    install_directory = os.path.dirname(install_directory)
if hasattr(sys, "_MEIPASS"):
    pyinstaller_mode = True

if pyinstaller_mode:
     os.environ["PATH"] += ":" + sys._MEIPASS

user_directory = os.path.join(install_directory, "user-data")
config_directory = user_directory

asset_directory = os.path.join(install_directory, "assets")


# If we're installed, use home data locations
install_mode = False
if install_directory.startswith("/opt/")\
        or install_directory.startswith("/usr/")\
        or install_directory.startswith("/app/")\
        or install_directory.startswith("/snap/") or sys.platform == "darwin" or sys.platform == 'win32':
    install_mode = True

if install_mode:
    user_directory = os.path.join(GLib.get_user_data_dir(), "TauonMusicBox")
if not os.path.isdir(user_directory):
    os.makedirs(user_directory)

if os.path.isfile('.gitignore'):
    print("Dev mode, ignoring single instancing")
elif sys.platform != 'win32':
    pid_file = os.path.join(user_directory, 'program.pid')
    fp = open(pid_file, 'w')
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        # another instance is running
        print("Program is already running")
        transfer_args_and_exit()
else:
    if sys.platform == "win32":
        pid_file = os.path.join(user_directory, 'program.pid')
        try:
            if os.path.isfile(pid_file):
                os.remove(pid_file)
            fp = open(pid_file, 'w')
        except IOError:
            # another instance is running
            print("Program is already running")
            transfer_args_and_exit()
    if pyinstaller_mode:
        os.environ["FONTCONFIG_PATH"] = os.path.join(install_directory, "etc\\fonts")#"C:\\msys64\\mingw64\\etc\\fonts"

phone = False
d = os.environ.get('XDG_CURRENT_DESKTOP')
if d in ["GNOME:Phosh"]:
    os.environ["SDL_VIDEODRIVER"] = "wayland"
    phone = True

if pyinstaller_mode: # and sys.platform == 'darwin':
    os.environ["PYSDL2_DLL_PATH"] = install_directory

from sdl2 import *
from sdl2.sdlimage import *

SDL_SetHint(SDL_HINT_VIDEO_ALLOW_SCREENSAVER, b'1')
SDL_SetHint(SDL_HINT_MOUSE_FOCUS_CLICKTHROUGH, b"1")
SDL_SetHint(SDL_HINT_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR, b"0")

draw_border = True
w = 1120
h = 600
if phone:
    w = 720
    h = 1800
window_default_size = [w, h]
window_size = [w, h]
logical_size = [w, h]
window_opacity = 1
scale = 1
if sys.platform == "darwin":
    scale = 2
if phone:
    scale = 1.3

maximized = False
old_window_position = None

window_p = os.path.join(user_directory, "window.p")
if os.path.isfile(window_p):
    try:
        state_file = open(window_p, "rb")
        save = pickle.load(state_file)
        state_file.close()

        draw_border = save[0]
        window_size = save[1]
        w, h = save[1]
        if 100 < w < 10000 and 100 < h < 5000:
            logical_size[0], logical_size[1] = w, h
        window_opacity = save[2]
        scale = save[3]
        maximized = save[4]
        old_window_position = save[5]
        del save

    except:
        print('Corrupted window state file?!')
        print('Please restart app')
        os.remove(window_p)
        exit(1)
else:
    print("No window state file")


#os.environ["SDL_VIDEODRIVER"] = "wayland"

SDL_Init(SDL_INIT_VIDEO | SDL_INIT_GAMECONTROLLER)

err = SDL_GetError()
if err and "GLX" in err.decode():
    print(f"SDL init error: {err.decode()}")
    SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, b"Tauon Music Box failed to start :(",
                             b"Error: " + err + b".\n If you're using Flatpak, try run `$ flatpak update`", None)
    sys.exit()

window_title = t_title
window_title = window_title.encode('utf-8')

flags = SDL_WINDOW_RESIZABLE
flags |= SDL_WINDOW_ALLOW_HIGHDPI
if draw_border:
    flags |= SDL_WINDOW_BORDERLESS

if old_window_position is None:
    o_x = SDL_WINDOWPOS_UNDEFINED
    o_y = SDL_WINDOWPOS_UNDEFINED
else:
    o_x = old_window_position[0]
    o_y = old_window_position[1]

if "--tray" in sys.argv:
    flags |= SDL_WINDOW_HIDDEN

t_window = SDL_CreateWindow(window_title,
                            o_x, o_y,
                            logical_size[0], logical_size[1],
                            flags) # | SDL_WINDOW_FULLSCREEN)


if maximized:
    SDL_MaximizeWindow(t_window)

renderer = SDL_CreateRenderer(t_window, 0, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)
SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND)
SDL_SetWindowOpacity(t_window, window_opacity)

SDL_SetRenderDrawColor(renderer, 7, 7, 7, 255)
SDL_RenderClear(renderer)


i_x = pointer(c_int(0))
i_y = pointer(c_int(0))
SDL_GL_GetDrawableSize(t_window, i_x, i_y)
window_size[0] = i_x.contents.value
window_size[1] = i_y.contents.value

raw_image = IMG_Load(os.path.join(asset_directory, "loading.png").encode())
sdl_texture = SDL_CreateTextureFromSurface(renderer, raw_image)
w = raw_image.contents.w
h = raw_image.contents.h
rect = SDL_Rect(window_size[0] // 2 - w // 2, window_size[1] // 2 - h // 2, w, h)

SDL_RenderCopy(renderer, sdl_texture, None, rect)

SDL_RenderPresent(renderer)

SDL_FreeSurface(raw_image)
SDL_DestroyTexture(sdl_texture)

from t_modules import t_bootstrap
h = t_bootstrap.holder
h.w = t_window
h.r = renderer
h.wl = logical_size
h.wr = window_size
h.wdf = window_default_size
h.s = scale
h.m = maximized
h.e = transfer_args_and_exit
h.d = draw_border
h.o = window_opacity
h.ow = old_window_position
h.id = install_directory
h.py = pyinstaller_mode
h.p = phone
h.window_title = window_title

del raw_image
del sdl_texture
del w
del h
del rect
del flags

if pyinstaller_mode or sys.platform == "darwin":
    from t_modules import t_main
else:
    # Using the above import method breaks previous pickles. Could be fixed
    # but yet to decide what best method is.
    big_boy_path = os.path.join(install_directory, 't_modules/t_main.py')
    f = open(big_boy_path, "rb")
    main = compile(f.read(), big_boy_path, 'exec')
    f.close()
    del big_boy_path
    del f
    exec(main)

