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
import subprocess
import sys
from pathlib import Path

from gi.repository import GLib

install_directory = Path(__file__).resolve().parent
sys.path.insert(0, str(install_directory.parent))

from tauon.t_modules.t_bootstrap import Holder  # noqa: E402
from tauon.t_modules.t_logging import CustomLoggingFormatter, LogHistoryHandler  # noqa: E402
from tauon.t_modules.t_window_state import WINDOW_STATE_FILENAME, WindowState, load_window_state  # noqa: E402

try:
	import tauon_native as _tauon_native
except ImportError:
	_tauon_native = None

native_bootstrap = bool(
	_tauon_native is not None
	and callable(getattr(_tauon_native, "is_active", None))
	and _tauon_native.is_active()
)
if not native_bootstrap:
	raise RuntimeError("Tauon must be launched through the tauon-native executable")

pyinstaller_mode = bool(
	hasattr(sys, "_MEIPASS") or getattr(sys, "frozen", False) or install_directory.name.endswith("_internal")
)

log = LogHistoryHandler()
formatter = logging.Formatter("[%(levelname)s] %(message)s")
log.setFormatter(formatter)

# DEBUG+ to file and std_err
logging.basicConfig(
	level=logging.DEBUG,
	handlers=[
		logging.StreamHandler(),
		log,
		# logging.FileHandler('/tmp/tauon.log'),
	],
)
logging.getLogger().handlers[0].setFormatter(CustomLoggingFormatter())

# https://docs.python.org/3/library/warnings.html
logging.captureWarnings(capture=True)
if not sys.warnoptions:
	import warnings

	warnings.simplefilter("default")
	os.environ["PYTHONWARNINGS"] = "default"  # Also affect subprocesses

if sys.platform != "win32":
	import fcntl

n_version = "11.1.1"  # Should also be bumped in pyproject.toml, extra/*.appdata.xml
t_version = "v" + n_version
t_title = "Tauon"
t_id = "tauonmb"
if str(install_directory).startswith("/app/") or sys.platform == "darwin":
	# Its Flatpak or macOS
	t_id = "com.github.taiko2k.tauonmb"
t_agent = f"{t_title}/" + n_version
t_creator = "Taiko2k"
t_copyright = "Copyright 2015-2026 Taiko2k"
t_url = "https://tauonmusicbox.rocks/"
t_type = "mediaplayer"

logging.info(f"{t_title} {t_version}")
logging.info(f"{t_copyright} captain.gxj@gmail.com\n")

logging.info(f"Started with arguments: {sys.argv}")


def open_discord() -> None:
	webbrowser.open("https://discord.gg/v4EmhES")


def open_github() -> None:
	webbrowser.open("https://github.com/Taiko2k/Tauon/issues")


def open_crash_log(path: Path) -> None:
	try:
		if sys.platform == "win32":
			os.startfile(path)  # type: ignore[attr-defined]
		elif sys.platform == "darwin":
			subprocess.Popen(["open", str(path)])
		else:
			subprocess.Popen(["xdg-open", str(path)])
	except Exception:
		webbrowser.open(path.as_uri())


def main() -> None:
	"""Launch Tauon by means of importing t_main.py"""
	from tauon.t_modules.t_main import main as t_main

	t_main(holder)


def transfer_args_and_exit() -> None:
	"""Early arg processing"""
	import urllib.request

	base = "http://localhost:7813/"

	if len(sys.argv) <= 1:
		url = base + "raise/"
		urllib.request.urlopen(url)

	for item in sys.argv:
		if (
			not item.endswith(".py")
			and not item.startswith("-")
			and not item.endswith("exe")
			and (item.startswith("file://") or Path(item).exists())
		):
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
		if item == "--reload-theme":
			url = base + "reloadtheme/"
			urllib.request.urlopen(url)

	sys.exit()


if "--no-start" in sys.argv or os.environ.get("TAUON_FORWARD_ARGS_ONLY") == "1":
	transfer_args_and_exit()

## TODO(Martin): This code is partially duped in t_main.py
# If we're installed, use home data locations
install_mode = bool(
	str(install_directory).startswith(("/opt/", "/usr/", "/app/", "/snap/", "/nix/store/"))
	or sys.platform in ("darwin", "win32")
)

# Assume that it's a classic Linux install, use standard paths
if str(install_directory).startswith("/usr/") and Path("/usr/share/TauonMusicBox").is_dir():
	install_directory = Path("/usr/share/TauonMusicBox")

if (install_directory / "portable").is_file():
	install_mode = False

# Handle regular install, running from a git cloned directory and finally a portable install, usually a venv
if install_mode:
	# logging.info("Running in installed mode")
	user_directory = Path(GLib.get_user_data_dir()) / "TauonMusicBox"
elif install_directory.parent.name == "src":
	# logging.info("Running in portable mode from cloned dir")
	user_directory = install_directory.parent.parent / "user-data"
else:
	# logging.info("Running in portable mode")
	user_directory = install_directory / "user-data"

if native_bootstrap:
	user_directory = Path(_tauon_native.user_data_directory())

debug = bool((user_directory / "debug").is_file())

# INFO+ to std_err
# TODO(Martin): This hereabout section is wonk, setting INFO on streamhandler removes formatting for DEBUG
logging.getLogger().handlers[0].setLevel(logging.DEBUG if debug else logging.INFO)

asset_directory = install_directory / "assets"

if not user_directory.is_dir():
	user_directory.mkdir(parents=True)

if debug:
	file_handler = logging.FileHandler(user_directory / "tauon.log")
	file_handler.setLevel(logging.DEBUG)
	file_handler.setFormatter(formatter)
	logging.getLogger().addHandler(file_handler)
	logging.info(f"Debug mode enabled - saving log to {user_directory / 'tauon.log'}")

fp = None
dev_mode = (install_directory / ".dev").is_file()
if native_bootstrap and _tauon_native.owns_instance_lock():
	logging.debug("Native launcher owns the instance lock")
elif dev_mode:
	logging.warning("Dev mode, ignoring single instancing")
elif sys.platform != "win32":
	pid_file = user_directory / "program.pid"
	fp = pid_file.open("w")
	try:
		fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
	except OSError:
		logging.exception("Another Tauon instance is already running")
		# TODO(Martin): Silent crash
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
			# TODO(Martin): Silent crash
			transfer_args_and_exit()
	if pyinstaller_mode:
		os.environ["FONTCONFIG_PATH"] = str(install_directory / "etc" / "fonts")  # "C:\\msys64\\mingw64\\etc\\fonts"

phone = False
d = os.environ.get("XDG_CURRENT_DESKTOP")
if d in ["GNOME:Phosh"]:
	os.environ["SDL_VIDEODRIVER"] = "wayland"
	phone = True

os.environ["SDL_VIDEO_WAYLAND_ALLOW_LIBDECOR"] = "0"  # emergency crash workaround

if pyinstaller_mode:  # and sys.platform == 'darwin':
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

from tauon.t_modules import t_native as sdl3  # noqa: E402

draw_border = True
w = 1120
h = 600
if phone:
	w = 720
	h = 1800
window_default_size: tuple[int, int] = (w, h)
window_size: list[int] = [w, h]
logical_size: list[int] = [w, h]
window_opacity = 1
scale = 1
if sys.platform == "darwin":
	scale = 2
if phone:
	scale = 1.3

maximized = False
old_window_position: tuple[int, int] | None = None

window_state_path = user_directory / WINDOW_STATE_FILENAME
if window_state_path.is_file() and not fs_mode:
	try:
		window_state = load_window_state(
			window_state_path,
			WindowState(width=w, height=h, scale=scale),
		)
		draw_border = window_state.borderless
		window_size = [window_state.width, window_state.height]
		logical_size = [window_state.width, window_state.height]
		window_opacity = window_state.opacity
		scale = window_state.scale
		maximized = window_state.maximized
		old_window_position = window_state.position
	except (OSError, ValueError):
		logging.exception("Ignoring invalid window state file: %s", window_state_path)
else:
	logging.info("No window state file")


##  Maybe this is needed any more?
# if d == "GNOME": #and os.environ.get("XDG_SESSION_TYPE") and os.environ.get("XDG_SESSION_TYPE") == "wayland":
# 	try:
# 		import gi.repository
# 		# TODO(Martin): Bump to 4.0 - https://github.com/Taiko2k/Tauon/issues/1316
# 		gi.require_version("Gtk", "3.0")
# 		from gi.repository import Gtk
#
#
# 		gtk_settings = Gtk.Settings().get_default()
# 		xtheme = gtk_settings.get_property("gtk-cursor-theme-name")
# 		xsize = gtk_settings.get_property("gtk-cursor-theme-size")
# 		os.environ["XCURSOR_THEME"] = xtheme
# 		os.environ["XCURSOR_SIZE"] = str(xsize)
# 	except Exception:
# 		logging.exception("Failed to set cursor")

window_title = t_title.encode("utf-8")
t_window = _tauon_native.window_address()
sdl3.SDL_SetWindowBordered(t_window, not draw_border)
sdl3.SDL_SetWindowSize(t_window, logical_size[0], logical_size[1])

if old_window_position is not None and not fs_mode:
	sdl3.SDL_SetWindowPosition(t_window, old_window_position[0], old_window_position[1])

if maximized:
	sdl3.SDL_MaximizeWindow(t_window)

logging.debug(f"PATH that will be used for ffmpeg/ffprobe and similar: {os.environ.get('PATH')}")
renderer = _tauon_native.renderer_address()

sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)
sdl3.SDL_SetWindowOpacity(t_window, window_opacity)

sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
sdl3.SDL_RenderClear(renderer)

logging.info(f"SDL renderer: {_tauon_native.renderer_name()}")

window_size[:] = _tauon_native.get_window_size(t_window, True)
logical_size[:] = _tauon_native.get_window_size(t_window, False)

# Loading screen: a full window grid of interconnected isometric wireframe boxes
def draw_loading_screen() -> None:
	box_w = round(44 * scale)  # half-width of a box top face
	box_r = box_w // 2         # half-height of the top face (2:1 isometric)
	box_d = round(35 * scale)  # vertical edge length

	def polyline(points: list[tuple[float, float]]) -> None:
		for start, end in zip(points, points[1:], strict=False):
			sdl3.SDL_RenderLine(renderer, start[0], start[1], end[0], end[1])

	sdl3.SDL_SetRenderDrawColor(renderer, 7, 7, 7, 255)
	sdl3.SDL_RenderFillRect(renderer, None)

	sdl3.SDL_SetRenderDrawColor(renderer, 120, 134, 150, 35)
	# Boxes tile seamlessly: each box's bottom front edges and right vertical
	# coincide with its neighbours' top faces and left vertical, so per box only
	# the top face and the west + south verticals are drawn to avoid doubling up
	cy = -box_r
	row = 0
	while cy < window_size[1] + box_r + box_d:
		cx = -box_w * 2 + (box_w if row % 2 else 0)
		while cx < window_size[0] + box_w * 2:
			n = (cx, cy - box_r)
			e = (cx + box_w, cy)
			s = (cx, cy + box_r)
			w = (cx - box_w, cy)
			polyline([n, e, s, w, n])
			polyline([w, (w[0], w[1] + box_d)])
			polyline([s, (s[0], s[1] + box_d)])
			cx += box_w * 2
		cy += box_r + box_d
		row += 1

	sdl3.SDL_RenderPresent(renderer)


draw_loading_screen()

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
	native_bootstrap=native_bootstrap,
)

if __name__ == "__main__":
	try:
		main()
	except Exception as e:
		crash_logger = logging.getLogger("crash_logger")
		crash_logger.setLevel(logging.DEBUG)
		crash_log_path = user_directory / "tauon-crash.log"
		file_handler = logging.FileHandler(crash_log_path)
		crash_logger.addHandler(file_handler)
		crash_logger.handlers[0].setFormatter(CustomLoggingFormatter(color=False))
		error_message = f"Oops, looks like Tauon crashed.\n\nPlease report a bug over at GitHub or Discord.\n\nCrash log was saved to\n{crash_log_path}"
		crash_logger.exception(error_message)
		_tauon_native.show_error_message("Tauon Music Box crashed :(", f"{error_message}\n\nShortlog:\n{e}")
