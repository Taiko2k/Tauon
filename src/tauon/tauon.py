#!/usr/bin/env python3
"""Tauon Music Box"""

# Copyright © 2015-2024, Taiko2k captain(dot)gxj(at)gmail.com

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import os
import pickle
import sys
from ctypes import c_int, pointer
from pathlib import Path

from gi.repository import GLib
from sdl2 import (
	SDL_BLENDMODE_BLEND,
	SDL_HINT_MOUSE_FOCUS_CLICKTHROUGH,
	SDL_HINT_RENDER_SCALE_QUALITY,
	SDL_HINT_VIDEO_ALLOW_SCREENSAVER,
	SDL_HINT_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR,
	SDL_INIT_VIDEO,
	SDL_MESSAGEBOX_ERROR,
	SDL_RENDERER_ACCELERATED,
	SDL_RENDERER_PRESENTVSYNC,
	SDL_WINDOW_ALLOW_HIGHDPI,
	SDL_WINDOW_BORDERLESS,
	SDL_WINDOW_FULLSCREEN_DESKTOP,
	SDL_WINDOW_HIDDEN,
	SDL_WINDOW_RESIZABLE,
	SDL_WINDOWPOS_UNDEFINED,
	SDL_CreateRenderer,
	SDL_CreateTextureFromSurface,
	SDL_CreateWindow,
	SDL_DestroyTexture,
	SDL_FreeSurface,
	SDL_GetError,
	SDL_GetWindowSize,
	SDL_GL_GetDrawableSize,
	SDL_Init,
	SDL_MaximizeWindow,
	SDL_Rect,
	SDL_RenderClear,
	SDL_RenderCopy,
	SDL_RenderPresent,
	SDL_SetHint,
	SDL_SetRenderDrawBlendMode,
	SDL_SetRenderDrawColor,
	SDL_SetWindowOpacity,
	SDL_ShowSimpleMessageBox,
)
from sdl2.sdlimage import IMG_Load

from tauon.t_modules import t_bootstrap


class CustomLoggingFormatter(logging.Formatter):
	"""Nicely format logging.loglevel logs"""

	grey        = "\x1b[38;20m"
	grey_bold   = "\x1b[38;1m"
	yellow      = "\x1b[33;20m"
	yellow_bold = "\x1b[33;1m"
	red         = "\x1b[31;20m"
	bold_red    = "\x1b[31;1m"
	reset       = "\x1b[0m"
	format         = "%(asctime)s [%(levelname)s] [%(module)s] %(message)s"
	format_verbose = "%(asctime)s [%(levelname)s] [%(module)s] %(message)s (%(filename)s:%(lineno)d)"

	FORMATS = {
		logging.DEBUG:    grey_bold   + format_verbose + reset,
		logging.INFO:     yellow      + format         + reset,
		logging.WARNING:  yellow_bold + format         + reset,
		logging.ERROR:    red         + format         + reset,
		logging.CRITICAL: bold_red    + format_verbose + reset,
	}

	def format(self, record: dict) -> str:
		log_fmt = self.FORMATS.get(record.levelno)
		# Remove the miliseconds(%f) from the default string
		date_fmt = "%Y-%m-%d %H:%M:%S"
		formatter = logging.Formatter(log_fmt, date_fmt)
		# Center align + min length things to prevent logs jumping around when switching between different values
		record.levelname = f"{record.levelname:^7}"
		record.module = f"{record.module:^10}"
		return formatter.format(record)

# DEBUG+ to file and std_err
logging.basicConfig(
	level=logging.DEBUG,
	handlers=[
		logging.StreamHandler(),
#		logging.FileHandler('/tmp/tauon.log'),
	],
)
# INFO+ to std_err
logging.getLogger().handlers[0].setLevel(logging.INFO)
logging.getLogger().handlers[0].setFormatter(CustomLoggingFormatter())

if sys.platform != "win32":
	import fcntl

n_version = "7.9.0"
t_version = "v" + n_version
t_title = "Tauon"
t_id = "tauonmb"
t_agent = "TauonMusicBox/" + n_version

# Leave these outside of logging for prettiness
print(f"{t_title} {t_version}")
print("Copyright 2015-2024 Taiko2k captain.gxj@gmail.com\n")

# Early arg processing
def transfer_args_and_exit() -> None:
	import urllib.request
	base = "http://localhost:7813/"

	if len(sys.argv) <= 1:
		url = base + "raise/"
		urllib.request.urlopen(url)

	for item in sys.argv:

		if not item.endswith(".py") and not item.startswith("-") and not item.endswith("exe") and (item.startswith("file://") or Path(item).exists()):
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

install_directory = str(Path(__file__).resolve().parent)

pyinstaller_mode = False
if hasattr(sys, "_MEIPASS"):
	pyinstaller_mode = True
if install_directory.endswith("\\_internal"):
	pyinstaller_mode = True
	install_directory = str(Path(install_directory).parent)

if pyinstaller_mode:
	os.environ["PATH"] += ":" + sys._MEIPASS
	os.environ["SSL_CERT_FILE"] = Path(install_directory) / "certifi" / "cacert.pem"

# If we're installed, use home data locations
install_mode = False
if install_directory.startswith(("/opt/", "/usr/", "/app/", "/snap/")) or sys.platform == "darwin" or sys.platform == "win32":
	install_mode = True

# Assume that it's a classic Linux install, use standard paths
if install_directory.startswith("/usr/"):
	install_directory = "/usr/share/TauonMusicBox"

user_directory = Path(install_directory) / "user-data"
config_directory = user_directory
asset_directory = Path(install_directory) / "assets"

if install_directory.startswith("/app/"):
	# Its Flatpak
	t_id = "com.github.taiko2k.tauonmb"
os.environ["SDL_VIDEO_WAYLAND_WMCLASS"] = t_id
os.environ["SDL_VIDEO_X11_WMCLASS"] = t_id

if Path(Path(install_directory) / "portable").is_file():
	install_mode = False

if install_mode:
	user_directory = Path(GLib.get_user_data_dir()) / "TauonMusicBox"
if not Path(user_directory).is_dir():
	Path(user_directory).mkdir(parents=True)

fp = None
dev_mode = Path(Path(install_directory) / ".dev").is_file()
if dev_mode:
	logging.warning("Dev mode, ignoring single instancing")
elif sys.platform != "win32":
	pid_file = Path(user_directory) / "program.pid"
	fp = open(pid_file, "w")
	try:
		fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
	except OSError:
		logging.exception("Another Tauon instance is already running")
		transfer_args_and_exit()
else:
	if sys.platform == "win32":
		pid_file = Path(user_directory) / "program.pid"
		try:
			if Path(pid_file).is_file():
				Path(pid_file).unlink()
			fp = open(pid_file, "w")
		except OSError:
			logging.exception("Another Tauon instance is already running")
			transfer_args_and_exit()
	if pyinstaller_mode:
		os.environ["FONTCONFIG_PATH"] = Path(install_directory) / "etc\\fonts" #"C:\\msys64\\mingw64\\etc\\fonts"

phone = False
d = os.environ.get("XDG_CURRENT_DESKTOP")
if d in ["GNOME:Phosh"]:
	os.environ["SDL_VIDEODRIVER"] = "wayland"
	phone = True

if pyinstaller_mode: # and sys.platform == 'darwin':
	os.environ["PYSDL2_DLL_PATH"] = install_directory

fs_mode = False
if os.environ.get("GAMESCOPE_WAYLAND_DISPLAY") is not None:
	fs_mode = True
	logging.info("Running in GAMESCOPE MODE")

allow_hidpi = True
if sys.platform == "win32" and sys.getwindowsversion().major < 10 or Path(Path(user_directory) / "nohidpi").is_file():
	allow_hidpi = False

SDL_SetHint(SDL_HINT_VIDEO_ALLOW_SCREENSAVER, b"1")
SDL_SetHint(SDL_HINT_MOUSE_FOCUS_CLICKTHROUGH, b"1")
SDL_SetHint(SDL_HINT_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR, b"0")
SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "best".encode())

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

window_p = Path(user_directory) / "window.p"
if Path(window_p).is_file() and not fs_mode:
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

	except Exception:
		logging.exception("Corrupted window state file?!")
		logging.error("Please restart app")
		Path(window_p).unlink()
		sys.exit(1)
else:
	logging.info("No window state file")


if d == "GNOME": #and os.environ.get("XDG_SESSION_TYPE") and os.environ.get("XDG_SESSION_TYPE") == "wayland":
	try:
		import gi.repository
		gi.require_version("Gtk", "4.0")
		from gi.repository import Gtk

		gtk_settings = Gtk.Settings().get_default()
		xtheme = gtk_settings.get_property("gtk-cursor-theme-name")
		xsize = gtk_settings.get_property("gtk-cursor-theme-size")
		os.environ["XCURSOR_THEME"] = xtheme
		os.environ["XCURSOR_SIZE"] = str(xsize)
	except Exception:
		logging.exception("Failed to set cursor")

if os.environ.get("XDG_SESSION_TYPE") and os.environ.get("XDG_SESSION_TYPE") == "wayland":
	os.environ["SDL_VIDEODRIVER"] = "wayland"
if Path(Path(user_directory) / "x11").exists():
	os.environ["SDL_VIDEODRIVER"] = "x11"

SDL_Init(SDL_INIT_VIDEO)
err = SDL_GetError()
if err and "GLX" in err.decode():
	logging.error(f"SDL init error: {err.decode()}")
	SDL_ShowSimpleMessageBox(
		SDL_MESSAGEBOX_ERROR, b"Tauon Music Box failed to start :(",
		b"Error: " + err + b".\n If you're using Flatpak, try run `$ flatpak update`", None)
	sys.exit()

window_title = t_title
window_title = window_title.encode("utf-8")

flags = SDL_WINDOW_RESIZABLE

if allow_hidpi:
	flags |= SDL_WINDOW_ALLOW_HIGHDPI

if draw_border and not fs_mode:
	flags |= SDL_WINDOW_BORDERLESS

if fs_mode:
	flags |= SDL_WINDOW_FULLSCREEN_DESKTOP

if old_window_position is None:
	o_x = SDL_WINDOWPOS_UNDEFINED
	o_y = SDL_WINDOWPOS_UNDEFINED
else:
	o_x = old_window_position[0]
	o_y = old_window_position[1]

if "--tray" in sys.argv:
	flags |= SDL_WINDOW_HIDDEN

error = False

t_window = SDL_CreateWindow(
	window_title,
	o_x, o_y,
	logical_size[0], logical_size[1],
	flags) # | SDL_WINDOW_FULLSCREEN)


if maximized:
	SDL_MaximizeWindow(t_window)

renderer = SDL_CreateRenderer(t_window, 0, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)

if not renderer or not t_window:
	logging.error("ERROR CREATING WINDOW!")

SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND)
SDL_SetWindowOpacity(t_window, window_opacity)

SDL_SetRenderDrawColor(renderer, 7, 7, 7, 255)
SDL_RenderClear(renderer)


i_x = pointer(c_int(0))
i_y = pointer(c_int(0))
SDL_GL_GetDrawableSize(t_window, i_x, i_y)
window_size[0] = i_x.contents.value
window_size[1] = i_y.contents.value

SDL_GetWindowSize(t_window, i_x, i_y)
logical_size[0] = i_x.contents.value
logical_size[1] = i_y.contents.value

img_path = Path(asset_directory) / "loading.png"
if not img_path.exists():
	raise FileNotFoundError(f"{str(img_path)} not found, exiting!")

if scale != 1:
	img_path2 = Path(user_directory) / "scaled-icons" / "loading.png"
	if Path(img_path2).is_file():
		img_path = img_path2
	del img_path2

raw_image = IMG_Load(str(img_path).encode())
sdl_texture = SDL_CreateTextureFromSurface(renderer, raw_image)
w = raw_image.contents.w
h = raw_image.contents.h
rect = SDL_Rect(window_size[0] // 2 - w // 2, window_size[1] // 2 - h // 2, w, h)

SDL_RenderCopy(renderer, sdl_texture, None, rect)

SDL_RenderPresent(renderer)

SDL_FreeSurface(raw_image)
SDL_DestroyTexture(sdl_texture)

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
h.fs_mode = fs_mode
h.title = t_title
h.n_version = n_version
h.t_version = t_version
h.t_id = t_id
h.agent = t_agent
h.dev_mode = dev_mode
h.lock = fp

del raw_image
del sdl_texture
del w
del h
del rect
del flags
del img_path

if pyinstaller_mode or sys.platform == "darwin" or install_mode:
	from tauon.t_modules import t_main
else:
	# Using the above import method breaks previous pickles.
	# Could be fixed, but yet to decide what best method is.
	big_boy_path = Path(install_directory) / "t_modules/t_main.py"
	f = big_boy_path.open("rb")
	main_func = compile(f.read(), big_boy_path, "exec")
	f.close()
	del big_boy_path
	del f

#	main = main_func
#	exec(main)

	def main() -> None:
		"""Execute the compiled code and return"""
		exec(main_func, {})
