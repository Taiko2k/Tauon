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
import sys
from pathlib import Path

install_directory = Path(__file__).resolve().parent
sys.path.insert(0, str(install_directory.parent))

from tauon.t_modules.t_logging import CustomLoggingFormatter, LogHistoryHandler  # noqa: E402

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

# Remote control commands, mapped to their endpoint on the controller server.
# Leading dashes are optional and hyphens within a command are ignored, so
# --play-pause, --playpause and playpause are all equivalent.
COMMANDS = {
	"play": "play",
	"pause": "pause",
	"playpause": "playpause",
	"stop": "stop",
	"next": "next",
	"advance": "next",
	"previous": "previous",
	"prev": "previous",
	"back": "previous",
	"raise": "raise",
	"shuffle": "shuffle",
	"repeat": "repeat",
	"reloadtheme": "reloadtheme",
}


def resolve_command(item: str) -> str | None:
	"""Return the endpoint for a command argument, or None if it isn't one"""
	return COMMANDS.get(item.removeprefix("--").replace("-", ""))


def is_file_argument(item: str) -> bool:
	"""Whether an argument names a file to open rather than a command"""
	return (
		not item.endswith(".py")
		and not item.startswith("-")
		and not item.endswith("exe")
		and (item.startswith("file://") or Path(item).exists())
	)


def transfer_args_and_exit() -> None:
	"""Hand our arguments to the already running instance and exit"""
	import urllib.error
	import urllib.request

	base = "http://localhost:7813/"

	def send(path: str) -> None:
		try:
			urllib.request.urlopen(base + path)
		except urllib.error.URLError:
			logging.error("Could not connect to Tauon. Make sure Tauon is running.")  # noqa: TRY400
			sys.exit(1)

	if len(sys.argv) <= 1:
		send("raise/")

	for item in sys.argv[1:]:
		# An existing path is a file to open, even if it looks like a command
		if is_file_argument(item):
			import base64

			send("open/" + base64.urlsafe_b64encode(item.encode()).decode())
			continue

		command = resolve_command(item)
		if command is not None:
			send(command + "/")

	sys.exit()


# A remote control command, or an explicit --no-start, means we talk to the
# already running instance instead of starting up ourselves
if "--no-start" in sys.argv or os.environ.get("TAUON_FORWARD_ARGS_ONLY") == "1" or any(
	resolve_command(item) is not None and not is_file_argument(item) for item in sys.argv[1:]
):
	transfer_args_and_exit()

# Everything below is only needed to actually start up, so keep it after the
# remote control path above - a command like --playpause must not pay for it.
import subprocess  # noqa: E402

from tauon.t_modules.t_bootstrap import Holder  # noqa: E402
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
portable_mode = bool(_tauon_native.portable_mode())

# https://docs.python.org/3/library/warnings.html
logging.captureWarnings(capture=True)
if not sys.warnoptions:
	import warnings

	warnings.simplefilter("default")
	os.environ["PYTHONWARNINGS"] = "default"  # Also affect subprocesses

if sys.platform != "win32":
	import fcntl

n_version = "13.1.0"  # Should also be bumped in pyproject.toml, extra/*.metainfo.xml
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


# Assume that it's a classic Linux install, use standard paths
if str(install_directory).startswith("/usr/") and Path("/usr/share/TauonMusicBox").is_dir():
	install_directory = Path("/usr/share/TauonMusicBox")

# The native launcher resolves the user data directory (installed, portable or
# source checkout) before Python starts, since it needs it for the window state
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
if _tauon_native.owns_instance_lock():
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

# SDL is already running by now: the native launcher applies the video driver
# environment (Wayland, Phosh and the x11 preference) before initialising it.
phone = os.environ.get("XDG_CURRENT_DESKTOP") == "GNOME:Phosh"

fs_mode = False
if os.environ.get("GAMESCOPE_WAYLAND_DISPLAY") is not None:
	fs_mode = True
	logging.info("Running in GAMESCOPE MODE")

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


window_title = t_title.encode("utf-8")
t_window = _tauon_native.window_address()
sdl3.set_window_bordered(t_window, not draw_border)
sdl3.set_window_size(t_window, logical_size[0], logical_size[1])

if old_window_position is not None and not fs_mode:
	sdl3.set_window_position(t_window, old_window_position[0], old_window_position[1])

if maximized:
	sdl3.maximize_window(t_window)

logging.debug(f"PATH that will be used for ffmpeg/ffprobe and similar: {os.environ.get('PATH')}")
renderer = _tauon_native.renderer_address()

sdl3.set_render_draw_blend_mode(renderer, sdl3.SDL_BLENDMODE_BLEND)
sdl3.set_window_opacity(t_window, window_opacity)

logging.info(f"SDL renderer: {_tauon_native.renderer_name()}")
logging.info(f"SDL window system: {_tauon_native.video_driver()}")

window_size[:] = _tauon_native.get_window_size(t_window, True)
logical_size[:] = _tauon_native.get_window_size(t_window, False)

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
	portable_mode=portable_mode,
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
		import webbrowser

		choice = _tauon_native.show_error_message(
			"Tauon Music Box crashed :(",
			f"{error_message}\n\nShortlog:\n{e}",
			("GitHub", "Discord", "Open Crash Log", "Quit"),
		)
		if choice == 0:
			open_github()
		elif choice == 1:
			open_discord()
		elif choice == 2:
			open_crash_log(crash_log_path)
