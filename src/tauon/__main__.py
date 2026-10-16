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
if "--no-start" in sys.argv or any(
	resolve_command(item) is not None and not is_file_argument(item) for item in sys.argv[1:]
):
	transfer_args_and_exit()

# Everything below is only needed to actually start up. Importing GLib and the
# rest costs far more than the whole remote control path above, so keep them
# after it - a command like --playpause must not pay for them.
import array  # noqa: E402
import ctypes  # noqa: E402
import ctypes.util  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
import pickle  # noqa: E402
import random  # noqa: E402
import subprocess  # noqa: E402
from ctypes import c_int, pointer  # noqa: E402

from gi.repository import GLib  # noqa: E402

from tauon.t_modules.t_bootstrap import Holder  # noqa: E402

pyinstaller_mode = bool(
	hasattr(sys, "_MEIPASS") or getattr(sys, "frozen", False) or install_directory.name.endswith("_internal")
)

# https://docs.python.org/3/library/warnings.html
logging.captureWarnings(capture=True)
if not sys.warnoptions:
	import warnings

	warnings.simplefilter("default")
	os.environ["PYTHONWARNINGS"] = "default"  # Also affect subprocesses

if sys.platform != "win32":
	import fcntl

n_version = "13.0.0"  # Should also be bumped in pyproject.toml, extra/*.metainfo.xml
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


def set_sdl_app_metadata() -> None:
	"""Populate SDL app metadata before SDL_Init()."""
	if not sdl3.SDL_SetAppMetadata(
		t_title.encode("utf-8"),
		n_version.encode("utf-8"),
		t_id.encode("utf-8"),
	):
		logging.warning("Failed to set SDL app metadata")

	metadata_properties = (
		(sdl3.SDL_PROP_APP_METADATA_NAME_STRING, t_title.encode("utf-8")),
		(sdl3.SDL_PROP_APP_METADATA_VERSION_STRING, n_version.encode("utf-8")),
		(sdl3.SDL_PROP_APP_METADATA_IDENTIFIER_STRING, t_id.encode("utf-8")),
		(sdl3.SDL_PROP_APP_METADATA_CREATOR_STRING, t_creator.encode("utf-8")),
		(sdl3.SDL_PROP_APP_METADATA_COPYRIGHT_STRING, t_copyright.encode("utf-8")),
		(sdl3.SDL_PROP_APP_METADATA_URL_STRING, t_url.encode("utf-8")),
		(sdl3.SDL_PROP_APP_METADATA_TYPE_STRING, t_type.encode("utf-8")),
	)
	for key, value in metadata_properties:
		if not sdl3.SDL_SetAppMetadataProperty(key, value):
			logging.warning(f"Failed to set SDL app metadata property: {key!r}")


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
if dev_mode:
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
		os.environ["FONTCONFIG_PATH"] = str(install_directory / "etc" / "fonts")  # "C:\\msys64\\ucrt64\\etc\\fonts"

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

# Pysdl3 doesn't seem to find system sdl3. REF: https://github.com/Aermoss/PySDL3/issues/35 pysdl
# As a workaround we try find it ourselves
# find_library() can return both a filename "libSDL3.so.0" or a full path "/opt/homebrew/lib/libSDL3.dylib"
sdl_dll_name = ctypes.util.find_library("SDL3")
if sdl_dll_name:
	sdl_dll_name = str(Path(sdl_dll_name).name)
	candidates = [
		"./" + sdl_dll_name,
		os.path.join("/app/lib", sdl_dll_name),
		os.path.join("/usr/lib64", sdl_dll_name),
		os.path.join("/lib64", sdl_dll_name),
		os.path.join("/usr/local/lib64", sdl_dll_name),
		os.path.join("/usr/lib", sdl_dll_name),
		os.path.join("/lib", sdl_dll_name),
		os.path.join("/usr/local/lib", sdl_dll_name),
	]
else:
	candidates = []
sdl_library_path = next((p for p in candidates if p and os.path.exists(p)), None)
if sdl_library_path:
	os.environ["SDL_BINARY_PATH"] = os.path.dirname(sdl_library_path)

os.environ["SDL_FIND_BINARIES"] = "1"
if pyinstaller_mode:
	os.environ["SDL_FIND_BINARIES"]            = "0" # Disable binary searching,                   "1"        by default.

os.environ["SDL_DOC_GENERATOR"]            = "0" # Disable doc generation                       "1"        by default.
os.environ["SDL_DISABLE_METADATA"]         = "1" # Disable metadata method,                     "0"        by default.
os.environ["SDL_CHECK_VERSION"]            = "0" # Disable version checking,                    "1"        by default.
os.environ["SDL_CHECK_BINARY_VERSION"]     = "0" # Disable binary version checking,             "1"        by default.
os.environ["SDL_IGNORE_MISSING_FUNCTIONS"] = "1" # Disable missing function warnings,           "0"        by default.

import sdl3  # noqa: E402

# Test the first SetHint to catch if we loaded SDL3 correctly
sethint_result = sdl3.SDL_SetHint(sdl3.SDL_HINT_VIDEO_ALLOW_SCREENSAVER, b"1")
if sethint_result is None:
	logging.error(
		"Failed to run SetHint, probably due to https://github.com/Aermoss/PySDL3/issues/35, will try a workaround"
	)
	sys.exit(1)

set_sdl_app_metadata()

sdl3.SDL_SetHint(sdl3.SDL_HINT_MOUSE_FOCUS_CLICKTHROUGH, b"1")
sdl3.SDL_SetHint(sdl3.SDL_HINT_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR, b"0")
if sys.platform == "darwin":
	# SDL 3.4 allows apps to remain in the background by default on recent
	# macOS versions. Tauon opens a normal application window, so ensure it is
	# activated when launched.
	sdl3.SDL_SetHint(sdl3.SDL_HINT_MAC_BACKGROUND_APP, b"0")
	if hasattr(sdl3, "SDL_HINT_MAC_SCROLL_MOMENTUM"):
		sdl3.SDL_SetHint(sdl3.SDL_HINT_MAC_SCROLL_MOMENTUM, b"1")
# sdl3.SDL_SetHint(sdl3.SDL_HINT_APP_ID, t_id.encode("utf-8"))
# sdl3.SDL_SetHint(sdl3.SDL_HINT_APP_NAME, t_title.encode("utf-8"))

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


sdl3.SDL_Init(sdl3.SDL_INIT_VIDEO | sdl3.SDL_INIT_EVENTS)

err = sdl3.SDL_GetError()
if err and "GLX" in err.decode():
	logging.error(f"SDL init error: {err.decode()}")
	sdl3.SDL_ShowSimpleMessageBox(
		sdl3.SDL_MESSAGEBOX_ERROR,
		b"Tauon Music Box failed to start :(",
		b"Error: " + err + b".\n If you're using Flatpak, try running `$ flatpak update`",
		None,
	)
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


window_properties = sdl3.SDL_CreateProperties()
if window_properties:
	sdl3.SDL_SetStringProperty(window_properties, sdl3.SDL_PROP_WINDOW_CREATE_TITLE_STRING, window_title)
	sdl3.SDL_SetNumberProperty(window_properties, sdl3.SDL_PROP_WINDOW_CREATE_X_NUMBER, o_x)
	sdl3.SDL_SetNumberProperty(window_properties, sdl3.SDL_PROP_WINDOW_CREATE_Y_NUMBER, o_y)
	sdl3.SDL_SetNumberProperty(
		window_properties,
		sdl3.SDL_PROP_WINDOW_CREATE_WIDTH_NUMBER,
		logical_size[0],
	)
	sdl3.SDL_SetNumberProperty(
		window_properties,
		sdl3.SDL_PROP_WINDOW_CREATE_HEIGHT_NUMBER,
		logical_size[1],
	)
	sdl3.SDL_SetNumberProperty(window_properties, sdl3.SDL_PROP_WINDOW_CREATE_FLAGS_NUMBER, flags)
	t_window = sdl3.SDL_CreateWindowWithProperties(window_properties)
	sdl3.SDL_DestroyProperties(window_properties)
else:
	t_window = None

if not t_window:
	logging.error("ERROR CREATING WINDOW!")
	logging.error(f"Title: {window_title}")
	logging.error(f"X: {o_x}")
	logging.error(f"Y: {o_y}")
	logging.error(f"Size 0: {logical_size[0]}")
	logging.error(f"Size 1: {logical_size[1]}")
	logging.error(f"Flags: {flags}")
	sdl_err = sdl3.SDL_GetError()
	logging.error(f"SDL Error: {sdl_err}")
	if sdl_err and sdl_err.decode() == "x11 not available":
		x11_path = user_directory / "x11"
		if x11_path.exists():
			logging.critical(
				"Disabled Xwayland preference as X11 was not found - Known issue if on Flatpak - https://github.com/Taiko2k/Tauon/issues/1034"
			)
			x11_path.unlink()
			# TODO(Martin): This does not seem to work on SDL3, it attempts to relaunch under x11 again
			# os.environ["SDL_VIDEODRIVER"] = "wayland"
			# t_window = sdl3.SDL_CreateWindow(
			# 	window_title,
			# 	o_x, o_y,
			# 	logical_size[0], logical_size[1],
			# 	flags)
			# if not t_window:
			# 	logging.error(f"Failed to create Wayland fallback window - SDL Error: {sdl3.SDL_GetError()}")
			# 	sys.exit(1)
			sys.exit(1)
		else:
			logging.critical(f"Failed to find {x11_path} but got 'x11 not available' error, hm?")
			sys.exit(1)

if maximized:
	sdl3.SDL_MaximizeWindow(t_window)

drivers: list[bytes] = []
i = 0
while True:
	x = sdl3.SDL_GetRenderDriver(i)
	i += 1
	if x is None:
		break
	drivers.append(x)

logging.debug(f"SDL available drivers: {drivers}")
logging.debug(f"PATH that will be used for ffmpeg/ffprobe and similar: {os.environ.get('PATH')}")

driver = None
if b"opengl" in drivers:
	driver = b"opengl"

renderer = sdl3.SDL_CreateRenderer(t_window, driver)  # sdl3.SDL_RENDERER_PRESENTVSYNC
if not renderer and driver == b"opengl":
	renderer_error = sdl3.SDL_GetError()
	logging.warning(f"Failed to create OpenGL renderer: {renderer_error}")
	logging.warning("Trying SDL default renderer")
	sdl3.SDL_ClearError()
	renderer = sdl3.SDL_CreateRenderer(t_window, None)

if not renderer:
	logging.error("ERROR CREATING RENDERER!")
	logging.error(f"SDL Error: {sdl3.SDL_GetError()}")
	sys.exit(1)

sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)
sdl3.SDL_SetWindowOpacity(t_window, window_opacity)

sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
sdl3.SDL_RenderClear(renderer)

logging.info(f"SDL window system: {sdl3.SDL_GetCurrentVideoDriver().decode()}")

# Vsync is not trusted for frame pacing (visualisers self-pace to the display
# refresh rate, see Tauon.frame_pace) — enabling it just aligns frames to vblank.
sdl3.SDL_SetRenderVSync(
	renderer, 1
)  # 1 == enable vsync, 0 == disable, -1 == late swap tearing, 2 == second vertical refresh

i_x = pointer(c_int(0))
i_y = pointer(c_int(0))
sdl3.SDL_GetWindowSizeInPixels(t_window, i_x, i_y)
window_size[0] = i_x.contents.value
window_size[1] = i_y.contents.value

sdl3.SDL_GetWindowSize(t_window, i_x, i_y)
logical_size[0] = i_x.contents.value
logical_size[1] = i_y.contents.value

# Loading screen: a star field crossed by a faint Milky Way, laid out randomly each startup
def draw_loading_screen() -> None:
	width, height = window_size
	rng = random.Random()
	rand = rng.random
	grey = 134 / 255

	sdl3.SDL_SetRenderDrawColor(renderer, 11, 11, 11, 255)
	sdl3.SDL_RenderFillRect(renderer, None)

	# Faint stars are pixel sized squares, batched by brightness level as x, y, w, h
	levels = 5
	batches: list[list[float]] = [[] for _level in range(levels)]
	size = 1.0 * scale
	half = size / 2

	def faint(x: float, y: float, level: int) -> None:
		batches[level].extend((x - half, y - half, size, size))

	# Brighter stars are soft round dots
	verts: list[float] = []
	idx: list[int] = []
	segments = 8
	circle = [(math.cos(math.tau * s / segments), math.sin(math.tau * s / segments)) for s in range(segments)]

	def bright(x: float, y: float, radius: float, alpha: float) -> None:
		base = len(verts) // 8
		verts.extend((x, y, grey, grey, grey, alpha, 0.0, 0.0))
		for ring_radius, ring_alpha in ((radius, alpha), (radius + scale, 0.0)):
			for cx, cy in circle:
				verts.extend((x + cx * ring_radius, y + cy * ring_radius, grey, grey, grey, ring_alpha, 0.0, 0.0))
		i, o = base + 1, base + 1 + segments
		for s in range(segments):
			n = (s + 1) % segments
			idx.extend((base, i + s, i + n, i + s, o + s, o + n, i + s, o + n, i + n))

	def star(x: float, y: float, b: float) -> None:
		"""One brightness scale for every star, b from 0 to 1."""
		if b < 0.35:
			faint(x, y, int(b / 0.35 * levels))
		else:
			bright(x, y, (0.3 + 0.7 * b) * scale, 0.1 + 0.45 * b)

	# Background field: mostly faint stars with the odd bright one
	for _k in range(int(width * height / (1100 * scale * scale))):
		star(rand() * width, rand() * height, rand() ** 3.5)

	# The band runs diagonally through a point near the middle of the window
	angle = rng.uniform(math.radians(15), math.radians(55)) * rng.choice((-1, 1))
	ux, uy = math.cos(angle), math.sin(angle)
	nx, ny = -uy, ux
	centre_x = width * rng.uniform(0.3, 0.7)
	centre_y = height * rng.uniform(0.3, 0.7)
	sigma = min(width, height) * rng.uniform(0.1, 0.15)
	length = math.hypot(width, height) + 4 * sigma

	# Profiles along the band: clumps of brighter haze, a gentle meander, and a soft, patchy
	# dust lane that thins out and returns along its length
	step = 8 * scale
	bins = int(length / step) + 1
	clumps = [(rng.uniform(-0.5, 0.5) * length, rng.uniform(0.6, 1.6) * sigma) for _c in range(10)]
	meander_phase, lane_phase = rng.uniform(0, math.tau), rng.uniform(0, math.tau)
	patches = [(rng.uniform(1.5, 4) * sigma, rng.uniform(0, math.tau)) for _p in range(3)]
	clump: list[float] = []
	meander: list[float] = []
	lane: list[float] = []
	lane_depth: list[float] = []
	for k in range(bins):
		along = k * step - length / 2
		clump.append(0.35 + 0.65 * min(1.0, sum(math.exp(-((along - c) / r) ** 2) for c, r in clumps)))
		meander.append(sigma * 0.25 * math.sin(along / (length * 0.3) + meander_phase))
		lane.append(sigma * (0.08 + 0.13 * math.sin(along / (1.9 * sigma) + lane_phase)))
		patchiness = sum(math.sin(along / wavelength + phase) for wavelength, phase in patches) / 3
		lane_depth.append(0.45 * max(0.0, 0.5 + patchiness))
	lane_width = sigma * 0.26

	# Band stars, slice by slice: uniform along each slice and roughly Gaussian across it, mixing
	# a core, a halo and a wide skirt so the band eases into the field. Offsets across the band
	# come from a precomputed table (sums of three uniforms), and slices wholly outside the
	# window are skipped.
	spread = sigma * math.sqrt(2)
	halo, skirt = spread * 2.2, spread * 4.5
	table_size = 2048
	offsets = [
		(rand() + rand() + rand() - 1.5) * (spread if mix < 0.6 else halo if mix < 0.9 else skirt)
		for mix in (rand() for _t in range(table_size))]
	reach = 1.5 * skirt + sigma * 0.25 + step
	exp = math.exp
	extends = [batch.extend for batch in batches]
	per_slice = step * sigma * 0.2 / (scale * scale)
	for k in range(bins):
		start = k * step - length / 2
		mid_x = centre_x + ux * (start + step / 2)
		mid_y = centre_y + uy * (start + step / 2)
		if mid_x < -reach or mid_x > width + reach or mid_y < -reach or mid_y > height + reach:
			continue
		lane_k, depth = lane[k], lane_depth[k]
		base_x = centre_x + nx * meander[k]
		base_y = centre_y + ny * meander[k]
		for _j in range(int(per_slice * clump[k] + rand())):
			d = offsets[int(rand() * table_size)]
			along = start + rand() * step
			x = base_x + ux * along + nx * d
			y = base_y + uy * along + ny * d
			if not (0 <= x < width and 0 <= y < height):
				continue
			gap = (d - lane_k) / lane_width
			if -3 < gap < 3 and rand() < depth * exp(-gap * gap):
				continue
			b = rand()
			if b < 0.012:
				star(x, y, 0.35 + 0.5 * rand() ** 2)
			else:
				extends[int(b * b * b * levels)]((x - half, y - half, size, size))

	# A few small star clusters along the band
	for _c in range(rng.randint(2, 4)):
		along = rng.uniform(-0.3, 0.3) * length
		d = rng.gauss(0, sigma * 0.5) + meander[int((along + length / 2) / step)]
		cluster_x = centre_x + ux * along + nx * d
		cluster_y = centre_y + uy * along + ny * d
		radius = rng.uniform(6, 16) * scale * 2
		for _s in range(rng.randint(30, 80)):
			star(
				cluster_x + (rand() + rand() + rand() - 1.5) * radius,
				cluster_y + (rand() + rand() + rand() - 1.5) * radius,
				rand() ** 3 * 0.7)

	for level, batch in enumerate(batches):
		count = len(batch) // 4
		if count:
			rects = (sdl3.SDL_FRect * count).from_buffer(array.array("f", batch))
			sdl3.SDL_SetRenderDrawColorFloat(renderer, grey, grey, grey, 0.08 + 0.3 * (level + 0.5) / levels)
			sdl3.SDL_RenderFillRects(renderer, rects, count)

	count = len(verts) // 8
	if count:
		vertices = (sdl3.SDL_Vertex * count).from_buffer(array.array("f", verts))
		indices = (ctypes.c_int * len(idx)).from_buffer(array.array("i", idx))
		sdl3.SDL_RenderGeometry(renderer, None, vertices, count, indices, len(idx))

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
)

del flags

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
		import ctypes
		import webbrowser

		BUTTON_ID_GITHUB = 1
		BUTTON_ID_DISCORD = 2
		BUTTON_ID_OPEN_LOG = 3
		BUTTON_ID_QUIT = 4

		# Create buttons
		button_array = (sdl3.SDL_MessageBoxButtonData * 4)(
			sdl3.SDL_MessageBoxButtonData(0, BUTTON_ID_GITHUB, b"GitHub"),
			sdl3.SDL_MessageBoxButtonData(0, BUTTON_ID_DISCORD, b"Discord"),
			sdl3.SDL_MessageBoxButtonData(0, BUTTON_ID_OPEN_LOG, b"Open Crash Log"),
			sdl3.SDL_MessageBoxButtonData(sdl3.SDL_MESSAGEBOX_BUTTON_ESCAPEKEY_DEFAULT, BUTTON_ID_QUIT, b"Quit"),
		)
		messageboxdata = sdl3.SDL_MessageBoxData(
			flags=sdl3.SDL_MESSAGEBOX_ERROR,
			window=None,
			title=b"Tauon Music Box crashed :(",
			message=str.encode(f"{error_message}\n\nShortlog:\n{e}"),
			numbuttons=4,
			buttons=button_array,
			color_scheme=None,
		)
		buttonid = ctypes.c_int(-1)

		# Show the message box
		success = sdl3.SDL_ShowMessageBox(ctypes.byref(messageboxdata), ctypes.byref(buttonid))

		if not success:
			logging.error(f"SDL_ShowMessageBox failed: {sdl3.SDL_GetError().decode()}")
		elif buttonid.value == BUTTON_ID_DISCORD:
			open_discord()
		elif buttonid.value == BUTTON_ID_GITHUB:
			open_github()
		elif buttonid.value == BUTTON_ID_OPEN_LOG:
			open_crash_log(crash_log_path)
		elif buttonid.value == BUTTON_ID_QUIT:
			pass
		sdl3.SDL_Quit()
