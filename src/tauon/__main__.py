#!/usr/bin/env python3
"""Tauon Music Box"""

# Copyright © 2015-2025, Taiko2k captain(dot)gxj(at)gmail.com

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
from ctypes import c_int, pointer, c_float, byref
from pathlib import Path

from gi.repository import GLib
import sdl3

install_directory: Path = Path(__file__).resolve().parent
sys.path.append(str(install_directory.parent))

from tauon.t_modules.logging import CustomLoggingFormatter, LogHistoryHandler

from tauon.t_modules.t_bootstrap import Holder

debug = False
if (install_directory / "debug").is_file():
	debug = True

log = LogHistoryHandler()
formatter = logging.Formatter('[%(levelname)s] %(message)s')
log.setFormatter(formatter)

# DEBUG+ to file and std_err
logging.basicConfig(
	level=logging.DEBUG,
	handlers=[
		logging.StreamHandler(),
		log,
#		logging.FileHandler('/tmp/tauon.log'),
	],
)
# INFO+ to std_err
# TODO(Martin): This hereabout section is wonk, setting INFO on streamhandler removes formatting for DEBUG
logging.getLogger().handlers[0].setLevel(logging.DEBUG if debug else logging.INFO)
logging.getLogger().handlers[0].setFormatter(CustomLoggingFormatter())

# https://docs.python.org/3/library/warnings.html
logging.captureWarnings(capture=True)
if not sys.warnoptions:
	import warnings
	warnings.simplefilter("default")
	os.environ["PYTHONWARNINGS"] = "default" # Also affect subprocesses

if sys.platform != "win32":
	import fcntl

n_version = "8.0.0"
t_version = "v" + n_version
t_title = "Tauon"
t_id = "tauonmb"
t_agent = "TauonMusicBox/" + n_version

logging.info(f"{t_title} {t_version}")
logging.info("Copyright 2015-2025 Taiko2k captain.gxj@gmail.com\n")

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



pyinstaller_mode = False
if hasattr(sys, "_MEIPASS") or getattr(sys, "frozen", False) or install_directory.name.endswith("_internal"):
	pyinstaller_mode = True

# If we're installed, use home data locations
install_mode = False
if str(install_directory).startswith(("/opt/", "/usr/", "/app/", "/snap/")) or sys.platform == "darwin" or sys.platform == "win32":
	install_mode = True

# Assume that it's a classic Linux install, use standard paths
if str(install_directory).startswith("/usr/") and Path("/usr/share/TauonMusicBox").is_dir():
	install_directory = Path("/usr/share/TauonMusicBox")

if str(install_directory).startswith("/app/"):
	# Its Flatpak
	t_id = "com.github.taiko2k.tauonmb"


if (install_directory / "portable").is_file():
	install_mode = False

# Handle regular install, running from a directory and finally a portable install, usually a venv
if install_mode:
#	logging.info("Running in installed mode")
	user_directory = Path(GLib.get_user_data_dir()) / "TauonMusicBox"
elif install_directory.parent.name == "src":
#	logging.info("Running in portable mode from cloned dir")
	user_directory = install_directory.parent.parent / "user-data"
else:
#	logging.info("Running in portable mode")
	user_directory = install_directory / "user-data"

asset_directory = install_directory / "assets"

if not user_directory.is_dir():
	user_directory.mkdir(parents=True)

if debug:
	file_handler = logging.FileHandler(user_directory / "tauon.log")
	file_handler.setLevel(logging.DEBUG)
	file_handler.setFormatter(formatter)
	logging.getLogger().addHandler(file_handler)
	logging.info("Debug mode enabled!")

fp = None
dev_mode = (install_directory / ".dev").is_file()
if dev_mode:
	logging.warning("Dev mode, ignoring single instancing")
elif sys.platform != "win32":
	pid_file = user_directory / "program.pid"
	fp = pid_file.open("w")
	try:
		fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
	except OSError:
		logging.exception("Another Tauon instance is already running")
		transfer_args_and_exit()
else:
	if sys.platform == "win32":
		pid_file = user_directory / "program.pid"
		try:
			if pid_file.is_file():
				pid_file.unlink()
			fp = pid_file.open("w")
		except OSError:
			logging.exception("Another Tauon instance is already running")
			transfer_args_and_exit()
	if pyinstaller_mode:
		os.environ["FONTCONFIG_PATH"] = str(install_directory / "etc" / "fonts") #"C:\\msys64\\mingw64\\etc\\fonts"

phone = False
d = os.environ.get("XDG_CURRENT_DESKTOP")
if d in ["GNOME:Phosh"]:
	os.environ["SDL_VIDEODRIVER"] = "wayland"
	phone = True

if pyinstaller_mode: # and sys.platform == 'darwin':
	os.environ["SDL_BINARY_PATH"] = str(install_directory)

fs_mode = False
if os.environ.get("GAMESCOPE_WAYLAND_DISPLAY") is not None:
	fs_mode = True
	logging.info("Running in GAMESCOPE MODE")

if os.environ.get("XDG_SESSION_TYPE") and os.environ.get("XDG_SESSION_TYPE") == "wayland":
	# Force Wayland, as SDL3 otherwise requires the compositor to support specific protocols
	# and defaults to X11 - https://github.com/libsdl-org/SDL/pull/9383
	# We should be able to remove this in 2026+
	os.environ["SDL_VIDEODRIVER"] = "wayland"
if Path(user_directory / "x11").exists():
	logging.debug("Forcing X11 due to user prefs")
	os.environ["SDL_VIDEODRIVER"] = "x11"

sdl3.SDL_SetHint(sdl3.SDL_HINT_VIDEO_ALLOW_SCREENSAVER, b"1")
sdl3.SDL_SetHint(sdl3.SDL_HINT_MOUSE_FOCUS_CLICKTHROUGH, b"1")
sdl3.SDL_SetHint(sdl3.SDL_HINT_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR, b"0")
sdl3.SDL_SetHint(sdl3.SDL_HINT_APP_ID, t_id.encode("utf-8"))
sdl3.SDL_SetHint(sdl3.SDL_HINT_APP_NAME, t_title.encode("utf-8"))

draw_border = True
w = 1120
h = 600
if phone:
	w = 720
	h = 1800
window_default_size: tuple[int, int] = (w, h)
window_size:         list[int] = [w, h]
logical_size:        list[int] = [w, h]
window_opacity = 1
scale = 1
if sys.platform == "darwin":
	scale = 2
if phone:
	scale = 1.3

maximized = False
old_window_position: tuple [int, int] | None = None

window_p = user_directory / "window.p"
if window_p.is_file() and not fs_mode:
	try:
		state_file = window_p.open("rb")
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
		logging.exception("Corrupted window state file?! Please restart app!")
		window_p.unlink()
		sys.exit(1)
else:
	logging.info("No window state file")


if d == "GNOME": #and os.environ.get("XDG_SESSION_TYPE") and os.environ.get("XDG_SESSION_TYPE") == "wayland":
	try:
		import gi.repository
		# TODO(Martin): Bump to 4.0 - https://github.com/Taiko2k/Tauon/issues/1316
		gi.require_version("Gtk", "3.0")
		from gi.repository import Gtk

		gtk_settings = Gtk.Settings().get_default()
		xtheme = gtk_settings.get_property("gtk-cursor-theme-name")
		xsize = gtk_settings.get_property("gtk-cursor-theme-size")
		os.environ["XCURSOR_THEME"] = xtheme
		os.environ["XCURSOR_SIZE"] = str(xsize)
	except Exception:
		logging.exception("Failed to set cursor")
sdl3.SDL_Init(sdl3.SDL_INIT_VIDEO | sdl3.SDL_INIT_EVENTS)

err = sdl3.SDL_GetError()
if err and "GLX" in err.decode():
	logging.error(f"SDL init error: {err.decode()}")
	sdl3.SDL_ShowSimpleMessageBox(
		sdl3.SDL_MESSAGEBOX_ERROR, b"Tauon Music Box failed to start :(",
		b"Error: " + err + b".\n If you're using Flatpak, try run `$ flatpak update`", None)
	sys.exit(1)

window_title = t_title
window_title = window_title.encode("utf-8")

flags = sdl3.SDL_WINDOW_RESIZABLE | sdl3.SDL_WINDOW_TRANSPARENT | sdl3.SDL_WINDOW_HIGH_PIXEL_DENSITY

if draw_border and not fs_mode:
	flags |= sdl3.SDL_WINDOW_BORDERLESS

if fs_mode:
	flags |= sdl3.SDL_WINDOW_FULLSCREEN

if old_window_position is None:
	o_x = sdl3.SDL_WINDOWPOS_UNDEFINED
	o_y = sdl3.SDL_WINDOWPOS_UNDEFINED
else:
	o_x = old_window_position[0]
	o_y = old_window_position[1]

if "--tray" in sys.argv:
	flags |= sdl3.SDL_WINDOW_HIDDEN


t_window = sdl3.SDL_CreateWindow(  # todo use SDL_CreateWindowAndRenderer()
	window_title,
	# o_x, o_y,
	logical_size[0], logical_size[1],
	flags)

if not t_window:
	logging.error("ERROR CREATING WINDOW!")
	logging.error(f"Title: {window_title}")
	logging.error(f"X: {o_x}")
	logging.error(f"Y: {o_y}")
	logging.error(f"Size 0: {logical_size[0]}")
	logging.error(f"Size 1: {logical_size[1]}")
	logging.error(f"Flags: {flags}")
	logging.error(f"SDL Error: {sdl3.SDL_GetError()}")
	sys.exit(1)

if maximized:
	sdl3.SDL_MaximizeWindow(t_window)

drivers = []
i = 0
while True:
	x = sdl3.SDL_GetRenderDriver(i)
	i += 1
	if x is None:
		break
	drivers.append(x)

logging.debug(f"SDL availiable drivers: {drivers}")

driver = None
if "opengl" in drivers:
	driver = b"opengl"

renderer = sdl3.SDL_CreateRenderer(t_window, driver)  # sdl3.SDL_RENDERER_PRESENTVSYNC

if not renderer:
	logging.error("ERROR CREATING RENDERER!")
	logging.error(f"SDL Error: {sdl3.SDL_GetError()}")
	sys.exit(1)

sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)
sdl3.SDL_SetWindowOpacity(t_window, window_opacity)

sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
sdl3.SDL_RenderClear(renderer)

logging.info(f"SDL window system: {sdl3.SDL_GetCurrentVideoDriver().decode()}")

i_x = pointer(c_int(0))
i_y = pointer(c_int(0))
sdl3.SDL_GetWindowSizeInPixels(t_window, i_x, i_y)
window_size[0] = i_x.contents.value
window_size[1] = i_y.contents.value

sdl3.SDL_GetWindowSize(t_window, i_x, i_y)
logical_size[0] = i_x.contents.value
logical_size[1] = i_y.contents.value

img_path = asset_directory / "loading.png"
if not img_path.exists():
	raise FileNotFoundError(f"{str(img_path)} not found, exiting!")

if scale != 1:
	img_path2 = user_directory / "scaled-icons" / "loading.png"
	if img_path2.is_file():
		img_path = img_path2
	del img_path2

sdl3.SDL_SetRenderDrawColor(renderer, 7, 7, 7, 255)
sdl3.SDL_RenderFillRect(renderer, None)

raw_image = sdl3.IMG_Load(str(img_path).encode())
texture = sdl3.SDL_CreateTextureFromSurface(renderer, raw_image)
i_x = c_float(0.0)
i_y = c_float(0.0)
sdl3.SDL_GetTextureSize(texture, byref(i_x), byref(i_y))
w = i_x.value
h = i_y.value
rect = sdl3.SDL_FRect(window_size[0] // 2 - w // 2, window_size[1] // 2 - h // 2, w, h)
sdl3.SDL_RenderTexture(renderer, texture, None, rect)




sdl3.SDL_RenderPresent(renderer)

sdl3.SDL_DestroySurface(raw_image)
sdl3.SDL_DestroyTexture(texture)

holder = Holder(
	t_window=t_window,
	renderer=renderer,
	logical_size=logical_size,
	window_size=window_size,
	window_default_size=window_default_size,
	scale=scale,
	maximized=maximized,
	transfer_args_and_exit=transfer_args_and_exit,
	draw_border=draw_border,
	window_opacity=window_opacity,
	old_window_position=old_window_position,
	install_directory=install_directory,
	user_directory=user_directory,
	pyinstaller_mode=pyinstaller_mode,
	phone=phone,
	window_title=window_title,
	fs_mode=fs_mode,
	t_title=t_title,
	n_version=n_version,
	t_version=t_version,
	t_id=t_id,
	t_agent=t_agent,
	dev_mode=dev_mode,
	instance_lock=fp,
	log=log,
)

del raw_image
del texture
del w
del h
del rect
del flags
del img_path


def main() -> None:
	"""Launch Tauon by means of importing t_main.py"""
	from tauon.t_modules.t_main import main as t_main
	t_main(holder)

if __name__ == "__main__":
	main()

# if pyinstaller_mode or sys.platform == "darwin" or install_mode:
# 	from tauon.t_modules import t_main
# else:
# 	# Using the above import method breaks previous pickles.
# 	# Could be fixed, but yet to decide what best method is.
# 	big_boy_path = install_directory / "t_modules/t_main.py"
# 	f = big_boy_path.open("rb")
# 	main_func = compile(f.read(), big_boy_path, "exec")
# 	f.close()
# 	del big_boy_path
# 	del f
#
# #	main = main_func
# #	exec(main)
#
# 	def main() -> None:
# 		"""Execute the compiled code and return"""
# 		exec(main_func, {})
