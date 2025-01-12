"""Tauon Music Box

Preamble

Welcome to the Tauon Music Box source code. I started this project when I was first
learning python, as a result this code can be quite messy. No doubt I have
written some things terribly wrong or inefficiently in places.
I would highly recommend not using this project as an example on how to code cleanly or correctly.
"""

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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import base64
import builtins
import certifi
import colorsys
import copy
import ctypes
import ctypes.util
import datetime
import gc as gbc
import gettext
import glob
import hashlib
import io
import json
import locale as py_locale
import logging
#import magic
import math
#import mimetypes
import os
import pickle
import platform
import random
import re
import secrets
import shlex
import shutil
import signal
import ssl
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET
import zipfile
from collections import OrderedDict
from ctypes import Structure, byref, c_char_p, c_double, c_int, c_uint32, c_void_p, pointer
from pathlib import Path
from typing import TYPE_CHECKING

import musicbrainzngs
import mutagen
import mutagen.flac
import mutagen.id3
import mutagen.mp4
import mutagen.oggvorbis
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from sdl2 import (
	SDL_BLENDMODE_BLEND,
	SDL_BLENDMODE_NONE,
	SDL_BUTTON_LEFT,
	SDL_BUTTON_MIDDLE,
	SDL_BUTTON_RIGHT,
	SDL_BUTTON_X1,
	SDL_BUTTON_X2,
	SDL_CONTROLLER_AXIS_LEFTY,
	SDL_CONTROLLER_AXIS_RIGHTX,
	SDL_CONTROLLER_AXIS_RIGHTY,
	SDL_CONTROLLER_AXIS_TRIGGERLEFT,
	SDL_CONTROLLER_BUTTON_A,
	SDL_CONTROLLER_BUTTON_B,
	SDL_CONTROLLER_BUTTON_DPAD_DOWN,
	SDL_CONTROLLER_BUTTON_DPAD_LEFT,
	SDL_CONTROLLER_BUTTON_DPAD_RIGHT,
	SDL_CONTROLLER_BUTTON_DPAD_UP,
	SDL_CONTROLLER_BUTTON_LEFTSHOULDER,
	SDL_CONTROLLER_BUTTON_RIGHTSHOULDER,
	SDL_CONTROLLER_BUTTON_X,
	SDL_CONTROLLER_BUTTON_Y,
	SDL_CONTROLLERAXISMOTION,
	SDL_CONTROLLERBUTTONDOWN,
	SDL_CONTROLLERDEVICEADDED,
	SDL_DROPFILE,
	SDL_DROPTEXT,
	SDL_FALSE,
	SDL_HITTEST_DRAGGABLE,
	SDL_HITTEST_NORMAL,
	SDL_HITTEST_RESIZE_BOTTOM,
	SDL_HITTEST_RESIZE_BOTTOMLEFT,
	SDL_HITTEST_RESIZE_BOTTOMRIGHT,
	SDL_HITTEST_RESIZE_LEFT,
	SDL_HITTEST_RESIZE_RIGHT,
	SDL_HITTEST_RESIZE_TOPLEFT,
	SDL_HITTEST_RESIZE_TOPRIGHT,
	SDL_INIT_EVERYTHING,
	SDL_INIT_GAMECONTROLLER,
	SDL_KEYDOWN,
	SDL_KEYUP,
	SDL_MOUSEBUTTONDOWN,
	SDL_MOUSEBUTTONUP,
	SDL_MOUSEMOTION,
	SDL_MOUSEWHEEL,
	SDL_PIXELFORMAT_ARGB8888,
	SDL_QUIT,
	SDL_RENDER_TARGETS_RESET,
	SDL_SCANCODE_A,
	SDL_SCANCODE_C,
	SDL_SCANCODE_V,
	SDL_SCANCODE_X,
	SDL_SCANCODE_Z,
	SDL_SYSTEM_CURSOR_ARROW,
	SDL_SYSTEM_CURSOR_HAND,
	SDL_SYSTEM_CURSOR_IBEAM,
	SDL_SYSTEM_CURSOR_SIZENS,
	SDL_SYSTEM_CURSOR_SIZENWSE,
	SDL_SYSTEM_CURSOR_SIZEWE,
	SDL_SYSWM_COCOA,
	SDL_SYSWM_UNKNOWN,
	SDL_SYSWM_WAYLAND,
	SDL_SYSWM_X11,
	SDL_TEXTEDITING,
	SDL_TEXTINPUT,
	SDL_TEXTUREACCESS_TARGET,
	SDL_TRUE,
	SDL_WINDOW_FULLSCREEN_DESKTOP,
	SDL_WINDOW_INPUT_FOCUS,
	SDL_WINDOWEVENT,
	SDL_WINDOWEVENT_DISPLAY_CHANGED,
	SDL_WINDOWEVENT_ENTER,
	SDL_WINDOWEVENT_EXPOSED,
	SDL_WINDOWEVENT_FOCUS_GAINED,
	SDL_WINDOWEVENT_FOCUS_LOST,
	SDL_WINDOWEVENT_LEAVE,
	SDL_WINDOWEVENT_MAXIMIZED,
	SDL_WINDOWEVENT_MINIMIZED,
	SDL_WINDOWEVENT_RESIZED,
	SDL_WINDOWEVENT_RESTORED,
	SDL_WINDOWEVENT_SHOWN,
	SDLK_BACKSPACE,
	SDLK_DELETE,
	SDLK_DOWN,
	SDLK_END,
	SDLK_HOME,
	SDLK_KP_ENTER,
	SDLK_LALT,
	SDLK_LCTRL,
	SDLK_LEFT,
	SDLK_LGUI,
	SDLK_LSHIFT,
	SDLK_RALT,
	SDLK_RCTRL,
	SDLK_RETURN,
	SDLK_RETURN2,
	SDLK_RIGHT,
	SDLK_RSHIFT,
	SDLK_TAB,
	SDLK_UP,
	SDL_CaptureMouse,
	SDL_CreateColorCursor,
	SDL_CreateRGBSurfaceWithFormatFrom,
	SDL_CreateSystemCursor,
	SDL_CreateTexture,
	SDL_CreateTextureFromSurface,
	SDL_Delay,
	SDL_DestroyTexture,
	SDL_DestroyWindow,
	SDL_Event,
	SDL_FreeSurface,
	SDL_GameControllerNameForIndex,
	SDL_GameControllerOpen,
	SDL_GetClipboardText,
	SDL_GetCurrentVideoDriver,
	SDL_GetGlobalMouseState,
	SDL_GetKeyFromName,
	SDL_GetMouseState,
	SDL_GetScancodeFromName,
	SDL_GetVersion,
	SDL_GetWindowFlags,
	SDL_GetWindowPosition,
	SDL_GetWindowSize,
	SDL_GetWindowWMInfo,
	SDL_GL_GetDrawableSize,
	SDL_HasClipboardText,
	SDL_HideWindow,
	SDL_HitTest,
	SDL_InitSubSystem,
	SDL_IsGameController,
	SDL_MaximizeWindow,
	SDL_MinimizeWindow,
	SDL_PollEvent,
	SDL_PumpEvents,
	SDL_PushEvent,
	SDL_QueryTexture,
	SDL_Quit,
	SDL_QuitSubSystem,
	SDL_RaiseWindow,
	SDL_Rect,
	SDL_RenderClear,
	SDL_RenderCopy,
	SDL_RenderFillRect,
	SDL_RenderPresent,
	SDL_RestoreWindow,
	SDL_SetClipboardText,
	SDL_SetCursor,
	SDL_SetRenderDrawBlendMode,
	SDL_SetRenderDrawColor,
	SDL_SetRenderTarget,
	SDL_SetTextInputRect,
	SDL_SetTextureAlphaMod,
	SDL_SetTextureBlendMode,
	SDL_SetTextureColorMod,
	SDL_SetWindowAlwaysOnTop,
	SDL_SetWindowBordered,
	SDL_SetWindowFullscreen,
	SDL_SetWindowHitTest,
	SDL_SetWindowIcon,
	SDL_SetWindowMinimumSize,
	SDL_SetWindowOpacity,
	SDL_SetWindowPosition,
	SDL_SetWindowResizable,
	SDL_SetWindowSize,
	SDL_SetWindowTitle,
	SDL_ShowWindow,
	SDL_StartTextInput,
	SDL_SysWMinfo,
	SDL_version,
	SDL_WaitEventTimeout,
	SDLK_a,
	SDLK_c,
	SDLK_v,
	SDLK_x,
	SDLK_z,
	rw_from_object,
)
from sdl2.sdlimage import IMG_Load, IMG_Load_RW, IMG_Quit
from send2trash import send2trash
from unidecode import unidecode

builtins._ = lambda x: x

from tauon.t_modules.t_config import Config
from tauon.t_modules.t_db_migrate import database_migrate
from tauon.t_modules.t_dbus import Gnome
from tauon.t_modules.t_draw import QuickThumbnail, TDraw
from tauon.t_modules.t_extra import (
	ColourGenCache,
	FunctionStore,
	TauonPlaylist,
	TauonQueueItem,
	TestTimer,
	Timer,
	alpha_blend,
	alpha_mod,
	archive_file_scan,
	check_equal,
	clean_string,
	colour_slide,
	colour_value,
	commonprefix,
	contrast_ratio,
	d_date_display,
	d_date_display2,
	filename_safe,
	filename_to_metadata,
	fit_box,
	folder_file_scan,
	genre_correct,
	get_artist_safe,
	get_artist_strip_feat,
	get_display_time,
	get_filesize_string,
	get_filesize_string_rounded,
	get_folder_size,
	get_hms_time,
	get_split_artists,
	get_year_from_string,
	grow_rect,
	hls_to_rgb,
	hms_to_seconds,
	hsl_to_rgb,
	is_grey,
	is_light,
	j_chars,
	mac_styles,
	point_distance,
	point_proximity_test,
	process_odat,
	reduce_paths,
	rgb_add_hls,
	rgb_to_hls,
	search_magic,
	search_magic_any,
	seconds_to_day_hms,
	shooter,
	sleep_timeout,
	star_count,
	star_count3,
	subtract_rect,
	test_lumi,
	tmp_cache_dir,
	tryint,
	uri_parse,
	year_search,
)
from tauon.t_modules.t_jellyfin import Jellyfin
from tauon.t_modules.t_launch import Launch
from tauon.t_modules.t_lyrics import genius, lyric_sources, uses_scraping
from tauon.t_modules.t_phazor import phazor_exists, player4
from tauon.t_modules.t_prefs import Prefs
from tauon.t_modules.t_search import bandcamp_search
from tauon.t_modules.t_spot import SpotCtl
from tauon.t_modules.t_stream import StreamEnc
from tauon.t_modules.t_tagscan import Ape, Flac, M4a, Opus, Wav, parse_picture_block
from tauon.t_modules.t_themeload import Deco, load_theme
from tauon.t_modules.t_tidal import Tidal
from tauon.t_modules.t_webserve import authserve, controller, stream_proxy, webserve, webserve2
from tauon.t_modules.t_main_rework import (
	LoadImageAsset,
	WhiteModImageAsset,
	DConsole,
	GuiVar,
	StarStore,
	AlbumStarStore,
	Fonts,
	Input,
	KeyMap,
	ColoursClass,
	TrackClass,
	LoadClass,
	GetSDLInput,
	MOD,
	GMETrackInfo,
	PlayerCtl,
	LastFMapi,
	ListenBrainz,
	LastScrob,
	Strings,
	Chunker,
	MenuIcon,
	MenuItem,
	ThreadManager,
	Menu,
	GallClass,
	ThumbTracks,
	Tauon,
	PlexService,
	SubsonicService,
	STray,
	GStats,
	Drawing,
	DropShadow,
	LyricsRenMini,
	LyricsRen,
	TimedLyricsToStatic,
	TimedLyricsRen,
	TextBox2,
	TextBox,
	ImageObject,
	AlbumArt,
	StyleOverlay,
	ToolTip,
	ToolTip3,
	RenameTrackBox,
	TransEditBox,
	TransEditBox,
	ExportPlaylistBox,
	KoelService,
	TauService,
	SearchOverlay,
	MessageBox,
	NagBox,
	PowerTag,
	Over,
	Fields,
	TopPanel,
	BottomBarType1,
	BottomBarType_ao1,
	MiniMode,
	MiniMode2,
	MiniMode3,
	StandardPlaylist,
	ArtBox,
	ScrollBox,
	RadioBox,
	RenamePlaylistBox,
	PlaylistBox,
	ArtistList,
	TreeView,
	QueueBox,
	MetaBox,
	PictureRender,
	PictureRender,
	RadioThumbGen,
	RadioThumbGen,
	Showcase,
	ColourPulse2,
	ViewBox,
	DLMon,
	Fader,
	EdgePulse,
	EdgePulse2,
	Undo,
)
#from tauon.t_modules.guitar_chords import GuitarChords

if TYPE_CHECKING:
	from ctypes import CDLL
	from io import BufferedReader, BytesIO
	from pylast import Artist, LibreFMNetwork
	from PIL.ImageFile import ImageFile
	from tauon.t_modules.t_bootstrap import Holder

# Log to debug as we don't care at all when user does not have this
try:
	import colored_traceback.always
	logging.debug("Found colored_traceback for colored crash tracebacks")
except ModuleNotFoundError:
	logging.debug("Unable to import colored_traceback, tracebacks will be dull.")
except Exception:
	logging.exception("Unknown error trying to import colored_traceback, tracebacks will be dull.")

try:
	from jxlpy import JXLImagePlugin
	# We've already logged this once to INFO from t_draw, so just log to DEBUG
	logging.debug("Found jxlpy for JPEG XL support")
except ModuleNotFoundError:
	logging.warning("Unable to import jxlpy, JPEG XL support will be disabled.")
except Exception:
	logging.exception("Unknown error trying to import jxlpy, JPEG XL support will be disabled.")

try:
	import setproctitle
except ModuleNotFoundError:
	logging.warning("Unable to import setproctitle, won't be setting process title.")
except Exception:
	logging.exception("Unknown error trying to import setproctitle, won't be setting process title.")
else:
	setproctitle.setproctitle("tauonmb")

# try:
#	 import rpc
#	 discord_allow = True
# except Exception:
#	logging.exception("Unable to import rpc, Discord Rich Presence will be disabled.")
discord_allow = False
try:
	from pypresence import Presence
except ModuleNotFoundError:
	logging.warning("Unable to import pypresence, Discord Rich Presence will be disabled.")
except Exception:
	logging.exception("Unknown error trying to import pypresence, Discord Rich Presence will be disabled.")
else:
	import asyncio
	discord_allow = True

use_cc = False
try:
	import opencc
except ModuleNotFoundError:
	logging.warning("Unable to import opencc, Traditional and Simplified Chinese searches will not be usable interchangeably.")
except Exception:
	logging.exception("Unknown error trying to import opencc, Traditional and Simplified Chinese searches will not be usable interchangeably.")
else:
	s2t = opencc.OpenCC("s2t")
	t2s = opencc.OpenCC("t2s")
	use_cc = True

use_natsort = False
try:
	import natsort
except ModuleNotFoundError:
	logging.warning("Unable to import natsort, playlists may not sort as intended!")
except Exception:
	logging.exception("Unknown error trying to import natsort, playlists may not sort as intended!")
else:
	use_natsort = True

# Detect platform
windows_native = False
macos = False
msys = False
system = "Linux"
arch = platform.machine()
platform_release = platform.release()
platform_system = platform.system()
win_ver = 0
if platform_system == "Windows":
	try:
		win_ver = int(platform_release)
	except Exception:
		logging.exception("Failed getting Windows version from platform.release()")

if sys.platform == "win32":
	# system = 'Windows'
	# windows_native = False
	system = "Linux"
	msys = True
else:
	system = "Linux"
	import fcntl

if sys.platform == "darwin":
	macos = True

if system == "Windows":
	import win32con
	import win32api
	import win32gui
	import win32ui
	import comtypes
	import atexit

if system == "Linux":
	from tauon.t_modules import t_topchart

if system == "Linux" and not macos and not msys:
	from tauon.t_modules.t_dbus import Gnome

holder                 = t_bootstrap.holder
t_window               = holder.t_window
renderer               = holder.renderer
logical_size           = holder.logical_size
window_size            = holder.window_size
maximized              = holder.maximized
scale                  = holder.scale
window_opacity         = holder.window_opacity
draw_border            = holder.draw_border
transfer_args_and_exit = holder.transfer_args_and_exit
old_window_position    = holder.old_window_position
install_directory      = holder.install_directory
user_directory         = holder.user_directory
pyinstaller_mode       = holder.pyinstaller_mode
phone                  = holder.phone
window_default_size    = holder.window_default_size
window_title           = holder.window_title
fs_mode                = holder.fs_mode
t_title                = holder.t_title
n_version              = holder.n_version
t_version              = holder.t_version
t_id                   = holder.t_id
t_agent                = holder.t_agent
dev_mode               = holder.dev_mode
instance_lock          = holder.instance_lock
log                    = holder.log
logging.info(f"Window size: {window_size}")

should_save_state = True

try:
	import pylast
	last_fm_enable = True
except Exception:
	logging.exception("PyLast module not found, last fm will be disabled.")
	last_fm_enable = False

if not windows_native:
	import gi
	from gi.repository import GLib

	font_folder = str(install_directory / "fonts")
	if os.path.isdir(font_folder):
		logging.info(f"Fonts directory:           {font_folder}")
		import ctypes

		fc = ctypes.cdll.LoadLibrary("libfontconfig-1.dll")
		fc.FcConfigReference.restype = ctypes.c_void_p
		fc.FcConfigReference.argtypes = (ctypes.c_void_p,)
		fc.FcConfigAppFontAddDir.argtypes = (ctypes.c_void_p, ctypes.c_char_p)
		config = ctypes.c_void_p()
		config.contents = fc.FcConfigGetCurrent()
		fc.FcConfigAppFontAddDir(config.value, font_folder.encode())

# TLS setup (needed for frozen installs)
def get_cert_path() -> str:
	if pyinstaller_mode:
		return os.path.join(sys._MEIPASS, 'certifi', 'cacert.pem')
	# Running as script
	return certifi.where()


def setup_ssl() -> ssl.SSLContext:
	# Set the SSL certificate path environment variable
	cert_path = get_cert_path()
	logging.debug(f"Found TLS cert file at: {cert_path}")
	os.environ['SSL_CERT_FILE'] = cert_path
	os.environ['REQUESTS_CA_BUNDLE'] = cert_path

	# Create default TLS context
	ssl_context = ssl.create_default_context(cafile=get_cert_path())
	return ssl_context

ssl_context = setup_ssl()



# Detect what desktop environment we are in to enable specific features
desktop = os.environ.get("XDG_CURRENT_DESKTOP")
# de_notify_support = desktop == 'GNOME' or desktop == 'KDE'
de_notify_support = False
draw_min_button = True
draw_max_button = True
left_window_control = False
xdpi = 0

detect_macstyle = False
gtk_settings: Settings | None = None
mac_close = (253, 70, 70, 255)
mac_maximize = (254, 176, 36, 255)
mac_minimize = (42, 189, 49, 255)
try:
	# TODO(Martin): Bump to 4.0 - https://github.com/Taiko2k/Tauon/issues/1316
	gi.require_version("Gtk", "3.0")
	from gi.repository import Gtk

	gtk_settings = Gtk.Settings().get_default()
	xdpi = gtk_settings.get_property("gtk-xft-dpi") / 1024
	if "minimize" not in str(gtk_settings.get_property("gtk-decoration-layout")):
		draw_min_button = False
	if "maximize" not in str(gtk_settings.get_property("gtk-decoration-layout")):
		draw_max_button = False
	if "close" in str(gtk_settings.get_property("gtk-decoration-layout")).split(":")[0]:
		left_window_control = True
	gtk_theme = str(gtk_settings.get_property("gtk-theme-name")).lower()
	#logging.info(f"GTK theme is: {gtk_theme}")
	for k, v in mac_styles.items():
		if k in gtk_theme:
			detect_macstyle = True
			if v is not None:
				mac_close = v[0]
				mac_maximize = v[1]
				mac_minimize = v[2]

except Exception:
	logging.exception("Error accessing GTK settings")

# Set data folders (portable mode)
config_directory = user_directory
cache_directory = user_directory / "cache"
home_directory = os.path.join(os.path.expanduser("~"))

asset_directory = install_directory / "assets"
svg_directory = install_directory / "assets" / "svg"
scaled_asset_directory = asset_directory

music_directory = Path("~").expanduser() / "Music"
if not music_directory.is_dir():
	music_directory = Path("~").expanduser() / "music"

download_directory = Path("~").expanduser() / "Downloads"

# Detect if we are installed or running portable
install_mode = False
flatpak_mode = False
snap_mode = False
if str(install_directory).startswith(("/opt/", "/usr/", "/app/", "/snap/")):
	install_mode = True
	if str(install_directory)[:6] == "/snap/":
		snap_mode = True
	if str(install_directory)[:5] == "/app/":
		# Flatpak mode
		logging.info("Detected running as Flatpak")

		# [old / no longer used] Symlink fontconfig from host system as workaround for poor font rendering
		if os.path.exists(os.path.join(home_directory, ".var/app/com.github.taiko2k.tauonmb/config")):

			host_fcfg = os.path.join(home_directory, ".config/fontconfig/")
			flatpak_fcfg = os.path.join(home_directory, ".var/app/com.github.taiko2k.tauonmb/config/fontconfig")

			if os.path.exists(host_fcfg):

				# if os.path.isdir(flatpak_fcfg) and not os.path.islink(flatpak_fcfg):
				#	 shutil.rmtree(flatpak_fcfg)
				if os.path.islink(flatpak_fcfg):
					logging.info("-- Symlink to fonconfig exists, removing")
					os.unlink(flatpak_fcfg)
				# else:
				#	 logging.info("-- Symlinking user fonconfig")
				#	 #os.symlink(host_fcfg, flatpak_fcfg)

		flatpak_mode = True

# If we're installed, use home data locations
if (install_mode and system == "Linux") or macos or msys:
	cache_directory  = Path(GLib.get_user_cache_dir()) / "TauonMusicBox"
	#user_directory   = Path(GLib.get_user_data_dir()) / "TauonMusicBox"
	config_directory = user_directory

#	if not user_directory.is_dir():
#		os.makedirs(user_directory)

	if not config_directory.is_dir():
		os.makedirs(config_directory)

	if snap_mode:
		logging.info("Installed as Snap")
	elif flatpak_mode:
		logging.info("Installed as Flatpak")
	else:
		logging.info("Running from installed location")

	if not (user_directory / "encoder").is_dir():
		os.makedirs(user_directory / "encoder")


# elif (system == 'Windows' or msys) and (
# 	'Program Files' in install_directory or
# 	os.path.isfile(install_directory + '\\unins000.exe')):
#
#	 user_directory = os.path.expanduser('~').replace("\\", '/') + "/Music/TauonMusicBox"
#	 config_directory = user_directory
#	 cache_directory = user_directory / "cache"
#	 logging.info(f"User Directory: {user_directory}")
#	 install_mode = True
#	 if not os.path.isdir(user_directory):
#		 os.makedirs(user_directory)

else:
	logging.info("Running in portable mode")
	config_directory = user_directory

if not (user_directory / "state.p").is_file() and cache_directory.is_dir():
	logging.info("Clearing old cache directory")
	logging.info(cache_directory)
	shutil.rmtree(str(cache_directory))

n_cache_dir = str(cache_directory / "network")
e_cache_dir = str(cache_directory / "export")
g_cache_dir = str(cache_directory / "gallery")
a_cache_dir = str(cache_directory / "artist")
r_cache_dir = str(cache_directory / "radio-thumbs")
b_cache_dir = str(user_directory / "artist-backgrounds")

if not os.path.isdir(n_cache_dir):
	os.makedirs(n_cache_dir)
if not os.path.isdir(e_cache_dir):
	os.makedirs(e_cache_dir)
if not os.path.isdir(g_cache_dir):
	os.makedirs(g_cache_dir)
if not os.path.isdir(a_cache_dir):
	os.makedirs(a_cache_dir)
if not os.path.isdir(b_cache_dir):
	os.makedirs(b_cache_dir)
if not os.path.isdir(r_cache_dir):
	os.makedirs(r_cache_dir)

if not (user_directory / "artist-pictures").is_dir():
	os.makedirs(user_directory / "artist-pictures")

if not (user_directory / "theme").is_dir():
	os.makedirs(user_directory / "theme")


if platform_system == "Linux":
	system_config_directory = Path(GLib.get_user_config_dir())
	xdg_dir_file = system_config_directory / "user-dirs.dirs"

	if xdg_dir_file.is_file():
		with xdg_dir_file.open() as f:
			for line in f:
				if line.startswith("XDG_MUSIC_DIR="):
					music_directory = Path(os.path.expandvars(line.split("=")[1].strip().replace('"', ""))).expanduser()
					logging.debug(f"Found XDG-Music:     {music_directory}     in {xdg_dir_file}")
				if line.startswith("XDG_DOWNLOAD_DIR="):
					target = Path(os.path.expandvars(line.split("=")[1].strip().replace('"', ""))).expanduser()
					if Path(target).is_dir():
						download_directory = target
					logging.debug(f"Found XDG-Downloads: {download_directory} in {xdg_dir_file}")


if os.getenv("XDG_MUSIC_DIR"):
	music_directory = Path(os.getenv("XDG_MUSIC_DIR"))
	logging.debug("Override music to: " + music_directory)

if os.getenv("XDG_DOWNLOAD_DIR"):
	download_directory = Path(os.getenv("XDG_DOWNLOAD_DIR"))
	logging.debug("Override downloads to: " + download_directory)

if music_directory:
	music_directory = Path(os.path.expandvars(music_directory))
if download_directory:
	download_directory = Path(os.path.expandvars(download_directory))

if not music_directory.is_dir():
	music_directory = None

locale_directory = install_directory / "locale"
#if flatpak_mode:
#	locale_directory = Path("/app/share/locale")
#elif str(install_directory).startswith(("/opt/", "/usr/")):
#	locale_directory = Path("/usr/share/locale")

logging.info(f"Install directory:         {install_directory}")
#logging.info(f"SVG directory:             {svg_directory}")
logging.info(f"Asset directory:           {asset_directory}")
#logging.info(f"Scaled Asset Directory:    {scaled_asset_directory}")
if locale_directory.exists():
	logging.info(f"Locale directory:          {locale_directory}")
else:
	logging.error(f"Locale directory MISSING:  {locale_directory}")
logging.info(f"Userdata directory:        {user_directory}")
logging.info(f"Config directory:          {config_directory}")
logging.info(f"Cache directory:           {cache_directory}")
logging.info(f"Home directory:            {home_directory}")
logging.info(f"Music directory:           {music_directory}")
logging.info(f"Downloads directory:       {download_directory}")

# Things for detecting and launching programs outside of flatpak sandbox
def whicher(target: str) -> bool | str | None:
	try:
		if flatpak_mode:
			complete = subprocess.run(
				shlex.split("flatpak-spawn --host which " + target), stdout=subprocess.PIPE,
					stderr=subprocess.PIPE, check=True)
			r = complete.stdout.decode()
			return "bin/" + target in r
		return shutil.which(target)
	except Exception:
		logging.exception("Failed to run flatpak-spawn")
		return False


launch_prefix = ""
if flatpak_mode:
	launch_prefix = "flatpak-spawn --host "

pid = os.getpid()

if not macos:
	icon = IMG_Load(str(asset_directory / "icon-64.png").encode())
else:
	icon = IMG_Load(str(asset_directory / "tau-mac.png").encode())

SDL_SetWindowIcon(t_window, icon)

if not phone:
	if window_size[0] != logical_size[0]:
		SDL_SetWindowMinimumSize(t_window, 560, 330)
	else:
		SDL_SetWindowMinimumSize(t_window, round(560 * scale), round(330 * scale))

max_window_tex = 1000
if window_size[0] > max_window_tex or window_size[1] > max_window_tex:

	while window_size[0] > max_window_tex:
		max_window_tex += 1000
	while window_size[1] > max_window_tex:
		max_window_tex += 1000

main_texture = SDL_CreateTexture(
	renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, max_window_tex,
	max_window_tex)
main_texture_overlay_temp = SDL_CreateTexture(
	renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET,
	max_window_tex, max_window_tex)

overlay_texture_texture = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, 300, 300)
SDL_SetTextureBlendMode(overlay_texture_texture, SDL_BLENDMODE_BLEND)
SDL_SetRenderTarget(renderer, overlay_texture_texture)
SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
SDL_RenderClear(renderer)
SDL_SetRenderTarget(renderer, None)

tracklist_texture = SDL_CreateTexture(
	renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, max_window_tex,
	max_window_tex)
tracklist_texture_rect = SDL_Rect(0, 0, max_window_tex, max_window_tex)
SDL_SetTextureBlendMode(tracklist_texture, SDL_BLENDMODE_BLEND)

SDL_SetRenderTarget(renderer, None)

# Paint main texture
SDL_SetRenderTarget(renderer, main_texture)
SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)

SDL_SetRenderTarget(renderer, main_texture_overlay_temp)
SDL_SetTextureBlendMode(main_texture_overlay_temp, SDL_BLENDMODE_BLEND)
SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
SDL_RenderClear(renderer)


#
# SDL_SetRenderTarget(renderer, None)
# SDL_SetRenderDrawColor(renderer, 7, 7, 7, 255)
# SDL_RenderClear(renderer)
# #SDL_RenderPresent(renderer)
#
# SDL_SetWindowOpacity(t_window, window_opacity)

def asset_loader(
	scaled_asset_directory: Path, loaded_asset_dc: dict[str, WhiteModImageAsset | LoadImageAsset], name: str, mod: bool = False,
) -> WhiteModImageAsset | LoadImageAsset:
	if name in loaded_asset_dc:
		return loaded_asset_dc[name]

	target = str(scaled_asset_directory / name)
	if mod:
		item = WhiteModImageAsset(scaled_asset_directory=scaled_asset_directory, path=target, scale_name=name)
	else:
		item = LoadImageAsset(scaled_asset_directory=scaled_asset_directory, path=target, scale_name=name)
	loaded_asset_dc[name] = item
	return item

loaded_asset_dc: dict[str, WhiteModImageAsset | LoadImageAsset] = {}
# loading_image = asset_loader(scaled_asset_directory, loaded_asset_dc, "loading.png")

if maximized:
	i_x = pointer(c_int(0))
	i_y = pointer(c_int(0))

	time.sleep(0.02)
	SDL_PumpEvents()
	SDL_GetWindowSize(t_window, i_x, i_y)
	logical_size[0] = i_x.contents.value
	logical_size[1] = i_y.contents.value
	SDL_GL_GetDrawableSize(t_window, i_x, i_y)
	window_size[0] = i_x.contents.value
	window_size[1] = i_y.contents.value

# loading_image.render(window_size[0] // 2 - loading_image.w // 2, window_size[1] // 2 - loading_image.h // 2)
# SDL_RenderPresent(renderer)

if install_directory != config_directory and not (config_directory / "input.txt").is_file():
	logging.warning("Input config file is missing, first run? Copying input.txt template from templates directory")
	#logging.warning(install_directory)
	#logging.warning(config_directory)
	shutil.copy(install_directory / "templates" / "input.txt", config_directory)


if snap_mode:
	discord_allow = False


musicbrainzngs.set_useragent("TauonMusicBox", n_version, "https://github.com/Taiko2k/Tauon")

# logging.info(arch)
# -----------------------------------------------------------
# Detect locale for translations

try:
	py_locale.setlocale(py_locale.LC_ALL, "")
except Exception:
	logging.exception("SET LOCALE ERROR")

# ------------------------------------------------

if system == "Windows":
	os.environ["PYSDL2_DLL_PATH"] = str(install_directory / "lib")
elif not msys and not macos:
	try:
		gi.require_version("Notify", "0.7")
	except Exception:
		logging.exception("Failed importing gi Notify 0.7, will try 0.8")
		gi.require_version("Notify", "0.8")
	from gi.repository import Notify



def no_padding() -> int:
	"""This will remove all padding"""
	return 0

wayland = True
if os.environ.get("SDL_VIDEODRIVER") != "wayland":
	wayland = False
	os.environ["GDK_BACKEND"] = "x11"


# Setting various timers

message_box_min_timer = Timer()
cursor_blink_timer = Timer()
animate_monitor_timer = Timer()
min_render_timer = Timer()
check_file_timer = Timer()
vis_rate_timer = Timer()
vis_decay_timer = Timer()
scroll_timer = Timer()
perf_timer = Timer()
quick_d_timer = Timer()
core_timer = Timer()
sleep_timer = Timer()
gallery_select_animate_timer = Timer()
gallery_select_animate_timer.force_set(10)
search_clear_timer = Timer()
gall_pl_switch_timer = Timer()
gall_pl_switch_timer.force_set(999)
d_click_timer = Timer()
d_click_timer.force_set(10)
lyrics_check_timer = Timer()
scroll_hide_timer = Timer(100)
scroll_gallery_hide_timer = Timer(100)
get_lfm_wait_timer = Timer(10)
lyrics_fetch_timer = Timer(10)
gallery_load_delay = Timer(10)
queue_add_timer = Timer(100)
toast_love_timer = Timer(100)
toast_mode_timer = Timer(100)
scrobble_warning_timer = Timer(1000)
sync_file_timer = Timer(1000)
sync_file_update_timer = Timer(1000)
sync_get_device_click_timer = Timer(100)

f_store = FunctionStore()

after_scan = []

search_string_cache = {}
search_dia_string_cache = {}

vis_update = False


# GUI Variables -------------------------------------------------------------------------------------------

# Variables now go in the gui, pctl, input and prefs class instances. The following just haven't been moved yet

console = DConsole()

spot_cache_saved_albums = []

resize_mode = False

side_panel_text_align = 0

album_mode = False
spec_smoothing = True

# gui.offset_extra = 0

old_album_pos = -55

album_dex = []
album_artist_dict = {}
row_len = 5
last_row = 0
album_v_gap = 66
album_h_gap = 30
album_v_slide_value = 50

album_mode_art_size = int(200 * scale)

time_last_save = 0

b_info_y = int(window_size[1] * 0.7)  # For future possible panel below playlist

volume_store = 50  # Used to save the previous volume when muted

# row_alt = False

to_get = 0  # Used to store temporary import count display
to_got = 0

editline = ""
# gui.rsp = True
quick_drag = False

# Playlist Panel
pl_view_offset = 0
pl_rect = (2, 12, 10, 10)

theme = 7
scroll_enable = True
scroll_timer = Timer()
scroll_timer.set()
scroll_opacity = 0
break_enable = True

source = None

album_playlist_width = 430

update_title = False

playlist_hold_position = 0
playlist_hold = False
selection_stage = 0

selected_in_playlist = -1

shift_selection = []

gen_codes: dict[int, str] = {}
# Control Variables--------------------------------------------------------------------------

mouse_down = False
right_down = False
click_location = [200, 200]
last_click_location = [0, 0]
mouse_position = [0, 0]
mouse_up_position = [0, 0]

k_input = True
key_shift_down = False
drag_mode = False
side_drag = False
clicked = False

# Player Variables----------------------------------------------------------------------------

format_colours = {  # These are the colours used for the label icon in UI 'track info box'
	"MP3":   [255, 130, 80,  255],  # Burnt orange
	"FLAC":  [156, 249, 79,  255],  # Bright lime green
	"M4A":   [81,  220, 225, 255],  # Soft cyan
	"AIFF":  [81,  220, 225, 255],  # Soft cyan
	"OGG":   [244, 244, 78,  255],  # Light yellow
	"OGA":   [244, 244, 78,  255],  # Light yellow
	"WMA":   [213, 79,  247, 255],  # Magenta
	"APE":   [247, 79,  79,  255],  # Deep pink
	"TTA":   [94,  78,  244, 255],  # Purple
	"OPUS":  [247, 79,  146, 255],  # Pink
	"AAC":   [79,  247, 168, 255],  # Teal
	"WV":    [229, 23,  18,  255],  # Deep red
	"PLEX":  [229, 160, 13,  255],  # Orange-brown
	"KOEL":  [111, 98,  190, 255],  # Lavender
	"TAU":   [111, 98,  190, 255],  # Lavender
	"SUB":   [235, 140, 20,  255],  # Golden yellow
	"SPTY":  [30,  215, 96,  255],  # Bright green
	"TIDAL": [0,   0,   0,   255],  # Black
	"JELY":  [190, 100, 210, 255],  # Fuchsia
	"XM":    [50,  50,  50,  255],  # Grey
	"MOD":   [50,  50,  50,  255],  # Grey
	"S3M":   [50,  50,  50,  255],  # Grey
	"IT":    [50,  50,  50,  255],  # Grey
	"MPTM":  [50,  50,  50,  255],  # Grey
	"AY":    [237, 212, 255, 255],  # Pastel purple
	"GBS":   [255, 165, 0,   255],  # Vibrant orange
	"GYM":   [0,   191, 255, 255],  # Bright blue
	"HES":   [176, 224, 230, 255],  # Light blue-green
	"KSS":   [255, 255, 153, 255],  # Bright yellow
	"NSF":   [255, 140, 0,   255],  # Deep orange
	"NSFE":  [255, 140, 0,   255],  # Deep orange
	"SAP":   [152, 255, 152, 255],  # Light green
	"SPC":   [255, 128, 0,   255],  # Bright orange
	"VGM":   [0,   128, 255, 255],  # Deep blue
	"VGZ":   [0,   128, 255, 255],  # Deep blue
}

# These will be the extensions of files to be added when importing
VID_Formats = {"mp4", "webm"}

MOD_Formats = {"xm", "mod", "s3m", "it", "mptm", "umx", "okt", "mtm", "669", "far", "wow", "dmf", "med", "mt2", "ult"}

GME_Formats = {"ay", "gbs", "gym", "hes", "kss", "nsf", "nsfe", "sap", "spc", "vgm", "vgz"}

DA_Formats = {
	"mp3", "wav", "opus", "flac", "ape", "aiff",
	"m4a", "ogg", "oga", "aac", "tta", "wv", "wma",
} | MOD_Formats | GME_Formats

Archive_Formats = {"zip"}

if whicher("unrar"):
	Archive_Formats.add("rar")

if whicher("7z"):
	Archive_Formats.add("7z")

cargo = []

# ---------------------------------------------------------------------
# Player variables

# pl_follow = False

# List of encodings to check for with the fix mojibake function
encodings = ["cp932", "utf-8", "big5hkscs", "gbk"]  # These seem to be the most common for Japanese

track_box = False

transcode_list: list[list[int]] = []
transcode_state = ""

taskbar_progress = True
track_queue: list[int] = []

playing_in_queue = 0
draw_sep_hl = False

# -------------------------------------------------------------------------------
# Playlist Variables
playlist_view_position = 0
playlist_playing = -1

loading_in_progress = False

core_use = 0
dl_use = 0

random_mode = False
repeat_mode = False




def uid_gen() -> int:
	return random.randrange(1, 100000000)


notify_change = lambda: None


def pl_gen(
	title:        str = "Default",
	playing:      int = 0,
	playlist_ids: list[int] | None = None,
	position:     int = 0,
	hide_title:   bool = False,
	selected:     int = 0,
	parent:       str = "",
	hidden:       bool = False,
) -> TauonPlaylist:
	"""Generate a TauonPlaylist

	Creates a default playlist when called without parameters
	"""
	if playlist_ids == None:
		playlist_ids = []

	notify_change()

#	return copy.deepcopy([title, playing, playlist, position, hide_title, selected, uid_gen(), [], hidden, False, parent, False])
	return TauonPlaylist(title=title, playing=playing, playlist_ids=playlist_ids, position=position, hide_title=hide_title, selected=selected, uuid_int=uid_gen(), last_folder=[], hidden=hidden, locked=False, parent_playlist_id=parent, persist_time_positioning=False)

multi_playlist: list[TauonPlaylist] = [pl_gen()]


def queue_item_gen(track_id: int, position: int, pl_id: int, type: int = 0, album_stage: int = 0) -> TauonQueueItem:
	# type; 0 is track, 1 is album
	auto_stop = False

#	return [track_id, position, pl_id, type, album_stage, uid_gen(), auto_stop]
	return TauonQueueItem(track_id=track_id, position=position, playlist_id=pl_id, type=type, album_stage=album_stage, uuid_int=uid_gen(), auto_stop=auto_stop)


default_playlist: list[int] = multi_playlist[0].playlist_ids
playlist_active: int = 0

quick_search_mode = False
search_index = 0

# ----------------------------------------
# Playlist right click menu

r_menu_index = 0
r_menu_position = 0

# Library and loader Variables--------------------------------------------------------
master_library: dict[int, TrackClass] = {}

cue_list = []

LC_None = 0
LC_Done = 1
LC_Folder = 2
LC_File = 3

loaderCommand = LC_None
loaderCommandReady = False

master_count = 0

load_orders = []

volume = 75

folder_image_offsets: dict[str, int] = {}
db_version: float = 0.0
latest_db_version: float = 69

albums = []
album_position = 0

prefs = Prefs(
	user_directory=user_directory,
	music_directory=music_directory,
	cache_directory=cache_directory,
	macos=macos,
	phone=phone,
	left_window_control=left_window_control,
	detect_macstyle=detect_macstyle,
	gtk_settings=gtk_settings,
	discord_allow=discord_allow,
	flatpak_mode=flatpak_mode,
	desktop=desktop,
	window_opacity=window_opacity,
	scale=scale,
)


def open_uri(uri:str) -> None:
	logging.info("OPEN URI")
	load_order = LoadClass()

	for w in range(len(pctl.multi_playlist)):
		if pctl.multi_playlist[w].title == "Default":
			load_order.playlist = pctl.multi_playlist[w].uuid_int
			break
	else:
		logging.warning("'Default' playlist not found, generating a new one!")
		pctl.multi_playlist.append(pl_gen())
		load_order.playlist = pctl.multi_playlist[len(pctl.multi_playlist) - 1].uuid_int
		switch_playlist(len(pctl.multi_playlist) - 1)

	load_order.target = str(urllib.parse.unquote(uri)).replace("file:///", "/").replace("\r", "")

	if gui.auto_play_import is False:
		load_order.play = True
		gui.auto_play_import = True

	load_orders.append(copy.deepcopy(load_order))
	gui.update += 1

gui = GuiVar(prefs=prefs)


def toast(text: str) -> None:
	gui.mode_toast_text = text
	toast_mode_timer.set()
	gui.frame_callback_list.append(TestTimer(1.5))


def set_artist_preview(path, artist, x, y):
	m = min(round(500 * gui.scale), window_size[1] - (gui.panelY + gui.panelBY + 50 * gui.scale))
	artist_preview_render.load(path, box_size=(m, m))
	artist_preview_render.show = True
	ah = artist_preview_render.size[1]
	ay = round(y) - (ah // 2)
	if ay < gui.panelY + 20 * gui.scale:
		ay = gui.panelY + round(20 * gui.scale)
	if ay + ah > window_size[1] - (gui.panelBY + 5 * gui.scale):
		ay = window_size[1] - (gui.panelBY + ah + round(5 * gui.scale))
	gui.preview_artist = artist
	gui.preview_artist_location = (x + 15 * gui.scale, ay)


def get_artist_preview(artist, x, y):
	# show_message(_("Loading artist image..."))

	gui.preview_artist_loading = artist
	artist_info_box.get_data(artist, force_dl=True)
	path = artist_info_box.get_data(artist, get_img_path=True)
	if not path:
		show_message(_("No artist image found."))
		if not prefs.enable_fanart_artist and not verify_discogs():
			show_message(_("No artist image found."), _("No providers are enabled in settings!"), mode="warning")
		gui.preview_artist_loading = ""
		return
	set_artist_preview(path, artist, x, y)
	gui.message_box = False
	gui.preview_artist_loading = ""


def set_drag_source():
	gui.drag_source_position = tuple(click_location)
	gui.drag_source_position_persist = tuple(click_location)


# Functions for reading and setting play counts
star_store = StarStore()
album_star_store = AlbumStarStore()
fonts = Fonts()
inp = Input()
keymaps = KeyMap()


def update_set():
	"""This is used to scale columns when windows is resized or items added/removed"""
	wid = gui.plw - round(16 * gui.scale)
	if gui.tracklist_center_mode:
		wid = gui.tracklist_highlight_width - round(16 * gui.scale)

	total = 0
	for item in gui.pl_st:
		if item[2] is False:
			total += item[1]
		else:
			wid -= item[1]

	wid = max(75, wid)

	for i in range(len(gui.pl_st)):
		if gui.pl_st[i][2] is False and total:
			gui.pl_st[i][1] = int(round((gui.pl_st[i][1] / total) * wid))  # + 1


def auto_size_columns():
	fixed_n = 0

	wid = gui.plw - round(16 * gui.scale)
	if gui.tracklist_center_mode:
		wid = gui.tracklist_highlight_width - round(16 * gui.scale)

	total = wid
	for item in gui.pl_st:

		if item[2]:
			fixed_n += 1

		if item[0] == "Lyrics":
			item[1] = round(50 * gui.scale)
			total -= round(50 * gui.scale)

		if item[0] == "Rating":
			item[1] = round(80 * gui.scale)
			total -= round(80 * gui.scale)

		if item[0] == "Starline":
			item[1] = round(78 * gui.scale)
			total -= round(78 * gui.scale)

		if item[0] == "Time":
			item[1] = round(58 * gui.scale)
			total -= round(58 * gui.scale)

		if item[0] == "Codec":
			item[1] = round(58 * gui.scale)
			total -= round(58 * gui.scale)

		if item[0] == "P" or item[0] == "S" or item[0] == "#":
			item[1] = round(32 * gui.scale)
			total -= round(32 * gui.scale)

		if item[0] == "Date":
			item[1] = round(55 * gui.scale)
			total -= round(55 * gui.scale)

		if item[0] == "Bitrate":
			item[1] = round(67 * gui.scale)
			total -= round(67 * gui.scale)

		if item[0] == "❤":
			item[1] = round(27 * gui.scale)
			total -= round(27 * gui.scale)

	vr = len(gui.pl_st) - fixed_n

	if vr > 0 and total > 50:

		space = round(total / vr)

		for item in gui.pl_st:
			if not item[2]:
				item[1] = space

	gui.pl_update += 1
	update_set()

colours = ColoursClass()
colours.post_config()


def set_colour(colour):
	SDL_SetRenderDrawColor(renderer, colour[0], colour[1], colour[2], colour[3])


def get_themes(deco: bool = False):
	themes = []  # full, name
	decos = {}
	direcs = [str(install_directory / "theme")]
	if user_directory != install_directory:
		direcs.append(str(user_directory / "theme"))

	def scan_folders(folders: list[str]) -> None:
		for folder in folders:
			if not os.path.isdir(folder):
				continue
			paths = [os.path.join(folder, f) for f in os.listdir(folder)]
			for path in paths:
				if os.path.islink(path):
					path = os.readlink(path)
				if os.path.isfile(path):
					if path[-7:] == ".ttheme":
						themes.append((path, os.path.basename(path).split(".")[0]))
					elif path[-6:] == ".tdeco":
						decos[os.path.basename(path).split(".")[0]] = path
				elif os.path.isdir(path):
					scan_folders([path])

	scan_folders(direcs)
	themes.sort()
	if deco:
		return decos
	return themes


# This is legacy. New settings are added straight to the save list (need to overhaul)
view_prefs = {
	"split-line": True,
	"update-title": False,
	"star-lines": False,
	"side-panel": True,
	"dim-art": False,
	"pl-follow": False,
	"scroll-enable": True,
}

def get_end_folder(direc):
	for w in range(len(direc)):
		if direc[-w - 1] == "\\" or direc[-w - 1] == "/":
			direc = direc[-w:]
			return direc
	return None

def set_path(nt: TrackClass, path: str) -> None:
	nt.fullpath = path.replace("\\", "/")
	nt.filename = os.path.basename(path)
	nt.parent_folder_path = os.path.dirname(path.replace("\\", "/"))
	nt.parent_folder_name = get_end_folder(os.path.dirname(path))
	nt.file_ext = os.path.splitext(os.path.basename(path))[1][1:].upper()


# url_saves = []
rename_files_previous = ""
rename_folder_previous = ""
p_force_queue: list[TauonQueueItem] = []

reload_state = None


def show_message(line1: str, line2: str ="", line3: str = "", mode: str = "info") -> None:
	gui.message_box = True
	gui.message_text = line1
	gui.message_mode = mode
	gui.message_subtext = line2
	gui.message_subtext2 = line3
	message_box_min_timer.set()
	match mode:
		case "done" | "confirm":
			logging.debug("Message: " + line1 + line2 + line3)
		case "info":
			logging.info("Message: " + line1 + line2 + line3)
		case "warning":
			logging.warning("Message: " + line1 + line2 + line3)
		case "error":
			logging.error("Message: " + line1 + line2 + line3)
		case _:
			logging.error(f"Unknown mode '{mode}' for message: " + line1 + line2 + line3)
	gui.update = 1


# -----------------------------------------------------
# STATE LOADING
# Loading of program data from previous run
gbc.disable()
ggc = 2

star_path1 = user_directory / "star.p"
star_path2 = user_directory / "star.p.backup"
star_size1 = 0
star_size2 = 0
to_load = star_path1
if star_path1.is_file():
	star_size1 = star_path1.stat().st_size
if star_path2.is_file():
	star_size2 = star_path2.stat().st_size
if star_size2 > star_size1:
	logging.warning("Loading backup star.p as it was bigger than regular file!")
	to_load = star_path2
if star_size1 == 0 and star_size2 == 0:
	logging.warning("Star database file is missing, first run? Will create one anew!")
else:
	try:
		with to_load.open("rb") as file:
			star_store.db = pickle.load(file)
	except Exception:
		logging.exception("Unknown error loading star.p file")


album_star_path = user_directory / "album-star.p"
if album_star_path.is_file():
	try:
		with album_star_path.open("rb") as file:
			album_star_store.db = pickle.load(file)
	except Exception:
		logging.exception("Unknown error loading album-star.p file")
else:
	logging.warning("Album star database file is missing, first run? Will create one anew!")

if (user_directory / "lyrics_substitutions.json").is_file():
	try:
		with (user_directory / "lyrics_substitutions.json").open() as f:
			prefs.lyrics_subs = json.load(f)
	except FileNotFoundError:
		logging.error("No existing lyrics_substitutions.json file")
	except Exception:
		logging.exception("Unknown error loading lyrics_substitutions.json")

perf_timer.set()

radio_playlists = [{"uid": uid_gen(), "name": "Default", "items": []}]

primary_stations: list[dict[str, str]] = []
station = {
	"title": "SomaFM Groove Salad",
	"stream_url": "https://ice3.somafm.com/groovesalad-128-mp3",
	"country": "USA",
	"website_url": "https://somafm.com/groovesalad",
	"icon": "https://somafm.com/logos/120/groovesalad120.png",
}
primary_stations.append(station)
station = {
	"title": "SomaFM PopTron",
	"stream_url": "https://ice3.somafm.com/poptron-128-mp3",
	"country": "USA",
	"website_url": "https://somafm.com/poptron/",
	"icon": "https://somafm.com/logos/120/poptron120.jpg",
}
primary_stations.append(station)
station = {
	"title": "SomaFM Vaporwaves",
	"stream_url": "https://ice4.somafm.com/vaporwaves-128-mp3",
	"country": "USA",
	"website_url": "https://somafm.com/vaporwaves",
	"icon": "https://somafm.com/img3/vaporwaves400.png",
}
primary_stations.append(station)

station = {
	"title": "DKFM Shoegaze Radio",
	"stream_url": "https://kathy.torontocast.com:2005/stream",
	"country": "Canada",
	"website_url": "https://decayfm.com",
	"icon": "https://cdn-profiles.tunein.com/s193842/images/logod.png",
}
primary_stations.append(station)

for item in primary_stations:
	radio_playlists[0]["items"].append(item)

radio_playlist_viewing = 0

pump = True


def pumper():
	if macos:
		return
	while pump:
		time.sleep(0.005)
		SDL_PumpEvents()


shoot_pump = threading.Thread(target=pumper)
shoot_pump.daemon = True
shoot_pump.start()

state_path1 = user_directory / "state.p"
state_path2 = user_directory / "state.p.backup"
for t in range(2):
	#	 os.path.getsize(user_directory / "state.p") < 100
	try:
		if t == 0:
			if not state_path1.is_file():
				continue
			with state_path1.open("rb") as file:
				save = pickle.load(file)
		if t == 1:
			if not state_path2.is_file():
				logging.warning("State database file is missing, first run? Will create one anew!")
				break
			logging.warning("Loading backup state.p!")
			with state_path2.open("rb") as file:
				save = pickle.load(file)

		# def tt():
		#	 while True:
		#		 logging.info(state_file.tell())
		#		 time.sleep(0.01)
		# shooter(tt)

		db_version = save[17]
		if db_version != latest_db_version:
			if db_version > latest_db_version:
				logging.critical(f"Loaded DB version: '{db_version}' is newer than latest known DB version '{latest_db_version}', refusing to load!\nAre you running an out of date Tauon version using Configuration directory from a newer one?")
				sys.exit(42)
			logging.warning(f"Loaded older DB version: {db_version}")
		if save[63] is not None:
			prefs.ui_scale = save[63]
			# prefs.ui_scale = 1.3
			# gui.__init__()

		if save[0] is not None:
			master_library = save[0]
		master_count = save[1]
		playlist_playing = save[2]
		playlist_active = save[3]
		playlist_view_position = save[4]
		if save[5] is not None:
			if db_version > 68:
				multi_playlist = []
				tauonplaylist_jar = save[5]
				for d in tauonplaylist_jar:
					nt = TauonPlaylist(**d)
					multi_playlist.append(nt)
			else:
				multi_playlist = save[5]
		volume = save[6]
		track_queue = save[7]
		playing_in_queue = save[8]
		default_playlist = save[9]
		# playlist_playing = save[10]
		# cue_list = save[11]
		# radio_field_text = save[12]
		theme = save[13]
		folder_image_offsets = save[14]
		# lfm_username = save[15]
		# lfm_hash = save[16]
		view_prefs = save[18]
		# window_size = save[19]
		gui.save_size = copy.copy(save[19])
		gui.rspw = save[20]
		# savetime = save[21]
		gui.vis_want = save[22]
		selected_in_playlist = save[23]
		if save[24] is not None:
			album_mode_art_size = save[24]
		if save[25] is not None:
			draw_border = save[25]
		if save[26] is not None:
			prefs.enable_web = save[26]
		if save[27] is not None:
			prefs.allow_remote = save[27]
		if save[28] is not None:
			prefs.expose_web = save[28]
		if save[29] is not None:
			prefs.enable_transcode = save[29]
		if save[30] is not None:
			prefs.show_rym = save[30]
		# if save[31] is not None:
		#	 combo_mode_art_size = save[31]
		if save[32] is not None:
			gui.maximized = save[32]
		if save[33] is not None:
			prefs.prefer_bottom_title = save[33]
		if save[34] is not None:
			gui.display_time_mode = save[34]
		# if save[35] is not None:
		#	 prefs.transcode_mode = save[35]
		if save[36] is not None:
			prefs.transcode_codec = save[36]
		if save[37] is not None:
			prefs.transcode_bitrate = save[37]
		# if save[38] is not None:
		#	 prefs.line_style = save[38]
		# if save[39] is not None:
		#	 prefs.cache_gallery = save[39]
		if save[40] is not None:
			prefs.playlist_font_size = save[40]
		if save[41] is not None:
			prefs.use_title = save[41]
		if save[42] is not None:
			gui.pl_st = save[42]
		# if save[43] is not None:
		#	 gui.set_mode = save[43]
		#	 gui.set_bar = gui.set_mode
		if save[45] is not None:
			prefs.playlist_row_height = save[45]
		if save[46] is not None:
			prefs.show_wiki = save[46]
		if save[47] is not None:
			prefs.auto_extract = save[47]
		if save[48] is not None:
			prefs.colour_from_image = save[48]
		if save[49] is not None:
			gui.set_bar = save[49]
		if save[50] is not None:
			gui.gallery_show_text = save[50]
		if save[51] is not None:
			gui.bb_show_art = save[51]
		# if save[52] is not None:
		#	 gui.show_stars = save[52]
		if save[53] is not None:
			prefs.auto_lfm = save[53]
		if save[54] is not None:
			prefs.scrobble_mark = save[54]
		if save[55] is not None:
			prefs.replay_gain = save[55]
		# if save[56] is not None:
		#	 prefs.radio_page_lyrics = save[56]
		if save[57] is not None:
			prefs.show_gimage = save[57]
		if save[58] is not None:
			prefs.end_setting = save[58]
		if save[59] is not None:
			prefs.show_gen = save[59]
		# if save[60] is not None:
		#	 url_saves = save[60]
		if save[61] is not None:
			prefs.auto_del_zip = save[61]
		if save[62] is not None:
			gui.level_meter_colour_mode = save[62]
		if save[64] is not None:
			prefs.show_lyrics_side = save[64]
		# if save[65] is not None:
		#	 prefs.last_device = save[65]
		if save[66] is not None:
			gui.restart_album_mode = save[66]
		if save[67] is not None:
			album_playlist_width = save[67]
		if save[68] is not None:
			prefs.transcode_opus_as = save[68]
		if save[69] is not None:
			gui.star_mode = save[69]
		if save[70] is not None:
			gui.rsp = save[70]
		if save[71] is not None:
			gui.lsp = save[71]
		if save[72] is not None:
			gui.rspw = save[72]
		if save[73] is not None:
			gui.pref_gallery_w = save[73]
		if save[74] is not None:
			gui.pref_rspw = save[74]
		if save[75] is not None:
			gui.show_hearts = save[75]
		if save[76] is not None:
			prefs.monitor_downloads = save[76]
		if save[77] is not None:
			gui.artist_info_panel = save[77]
		if save[78] is not None:
			prefs.extract_to_music = save[78]
		if save[79] is not None:
			prefs.enable_lb = save[79]
		# if save[80] is not None:
		#	 prefs.lb_token = save[80]
		#	 if prefs.lb_token is None:
		#		 prefs.lb_token = ""
		if save[81] is not None:
			rename_files_previous = save[81]
		if save[82] is not None:
			rename_folder_previous = save[82]
		if save[83] is not None:
			prefs.use_jump_crossfade = save[83]
		if save[84] is not None:
			prefs.use_transition_crossfade = save[84]
		if save[85] is not None:
			prefs.show_notifications = save[85]
		# if save[86] is not None:
		#	 prefs.true_shuffle = save[86]
		if save[87] is not None:
			gui.remember_library_mode = save[87]
		# if save[88] is not None:
		#	 prefs.show_queue = save[88]
		# if save[89] is not None:
		#	 prefs.show_transfer = save[89]
		if save[90] is not None:
			if db_version > 68:
				tauonqueueitem_jar = save[90]
				for d in tauonqueueitem_jar:
					nt = TauonQueueItem(**d)
					p_force_queue.append(nt)
			else:
				p_force_queue = save[90]
		if save[91] is not None:
			prefs.use_pause_fade = save[91]
		if save[92] is not None:
			prefs.append_total_time = save[92]
		if save[93] is not None:
			prefs.backend = save[93]  # moved to config file
		if save[94] is not None:
			prefs.album_shuffle_mode = save[94]
		if save[95] is not None:
			prefs.album_repeat_mode = save[95]
		# if save[96] is not None:
		#	 prefs.finish_current = save[96]
		if save[97] is not None:
			reload_state = save[97]
		# if save[98] is not None:
		#	 prefs.reload_play_state = save[98]
		if save[99] is not None:
			prefs.last_fm_token = save[99]
		if save[100] is not None:
			prefs.last_fm_username = save[100]
		# if save[101] is not None:
		#	 prefs.use_card_style = save[101]
		# if save[102] is not None:
		#	 prefs.auto_lyrics = save[102]
		if save[103] is not None:
			prefs.auto_lyrics_checked = save[103]
		if save[104] is not None:
			prefs.show_side_art = save[104]
		if save[105] is not None:
			prefs.window_opacity = save[105]
		if save[106] is not None:
			prefs.gallery_single_click = save[106]
		if save[107] is not None:
			prefs.tabs_on_top = save[107]
		if save[108] is not None:
			prefs.showcase_vis = save[108]
		if save[109] is not None:
			prefs.spec2_colour_mode = save[109]
		# if save[110] is not None:
		#	 prefs.device_buffer = save[110]
		if save[111] is not None:
			prefs.use_eq = save[111]
		if save[112] is not None:
			prefs.eq = save[112]
		if save[113] is not None:
			prefs.bio_large = save[113]
		if save[114] is not None:
			prefs.discord_show = save[114]
		if save[115] is not None:
			prefs.min_to_tray = save[115]
		if save[116] is not None:
			prefs.guitar_chords = save[116]
		if save[117] is not None:
			prefs.playback_follow_cursor = save[117]
		if save[118] is not None:
			prefs.art_bg = save[118]
		if save[119] is not None:
			prefs.random_mode = save[119]
		if save[120] is not None:
			prefs.repeat_mode = save[120]
		if save[121] is not None:
			prefs.art_bg_stronger = save[121]
		if save[122] is not None:
			prefs.art_bg_always_blur = save[122]
		if save[123] is not None:
			prefs.failed_artists = save[123]
		if save[124] is not None:
			prefs.artist_list = save[124]
		if save[125] is not None:
			prefs.auto_sort = save[125]
		if save[126] is not None:
			prefs.lyrics_enables = save[126]
		if save[127] is not None:
			prefs.fanart_notify = save[127]
		if save[128] is not None:
			prefs.bg_showcase_only = save[128]
		if save[129] is not None:
			prefs.discogs_pat = save[129]
		if save[130] is not None:
			prefs.mini_mode_mode = save[130]
		if save[131] is not None:
			after_scan = save[131]
		if save[132] is not None:
			gui.gallery_positions = save[132]
		if save[133] is not None:
			prefs.chart_bg = save[133]
		if save[134] is not None:
			prefs.left_panel_mode = save[134]
		if save[135] is not None:
			gui.last_left_panel_mode = save[135]
		# if save[136] is not None:
		#	 prefs.gst_device = save[136]
		if save[137] is not None:
			search_string_cache = save[137]
		if save[138] is not None:
			search_dia_string_cache = save[138]
		if save[139] is not None:
			gen_codes = save[139]
		if save[140] is not None:
			gui.show_ratings = save[140]
		if save[141] is not None:
			gui.show_album_ratings = save[141]
		if save[142] is not None:
			prefs.radio_urls = save[142]
		if save[143] is not None:
			gui.restore_showcase_view = save[143]
		if save[144] is not None:
			gui.saved_prime_tab = save[144]
		if save[145] is not None:
			gui.saved_prime_direction = save[145]
		if save[146] is not None:
			prefs.sync_playlist = save[146]
		if save[147] is not None:
			prefs.spot_client = save[147]
		if save[148] is not None:
			prefs.spot_secret = save[148]
		if save[149] is not None:
			prefs.show_band = save[149]
		if save[150] is not None:
			prefs.download_playlist = save[150]
		if save[151] is not None:
			spot_cache_saved_albums = save[151]
		if save[152] is not None:
			prefs.auto_rec = save[152]
		if save[153] is not None:
			prefs.spotify_token = save[153]
		if save[154] is not None:
			prefs.use_libre_fm = save[154]
		if save[155] is not None:
			prefs.old_playlist_box_position = save[155]
		if save[156] is not None:
			prefs.artist_list_sort_mode = save[156]
		if save[157] is not None:
			prefs.phazor_device_selected = save[157]
		if save[158] is not None:
			prefs.failed_background_artists = save[158]
		if save[159] is not None:
			prefs.bg_flips = save[159]
		if save[160] is not None:
			prefs.tray_show_title = save[160]
		if save[161] is not None:
			prefs.artist_list_style = save[161]
		if save[162] is not None:
			trackclass_jar = save[162]
			for d in trackclass_jar:
				nt = TrackClass()
				nt.__dict__.update(d)
				master_library[d["index"]] = nt
		if save[163] is not None:
			prefs.premium = save[163]
		if save[164] is not None:
			gui.restore_radio_view = save[164]
		if save[165] is not None:
			radio_playlists = save[165]
		if save[166] is not None:
			radio_playlist_viewing = save[166]
		if save[167] is not None:
			prefs.radio_thumb_bans = save[167]
		if save[168] is not None:
			prefs.playlist_exports = save[168]
		if save[169] is not None:
			prefs.show_chromecast = save[169]
		if save[170] is not None:
			prefs.cache_list = save[170]
		if save[171] is not None:
			prefs.shuffle_lock = save[171]
		if save[172] is not None:
			prefs.album_shuffle_lock_mode = save[172]
		if save[173] is not None:
			gui.was_radio = save[173]
		if save[174] is not None:
			prefs.spot_username = save[174]
		# if save[175] is not None:
		# 	prefs.spot_password = save[175]
		if save[176] is not None:
			prefs.artist_list_threshold = save[176]
		if save[177] is not None:
			prefs.tray_theme = save[177]
		if save[178] is not None:
			prefs.row_title_format = save[178]
		if save[179] is not None:
			prefs.row_title_genre = save[179]
		if save[180] is not None:
			prefs.row_title_separator_type = save[180]
		if save[181] is not None:
			prefs.replay_preamp = save[181]
		if save[182] is not None:
			prefs.gallery_combine_disc = save[182]

		del save
		break

	except IndexError:
		logging.exception("Index error")
		break
	except Exception:
		logging.exception("Failed to load save file")

core_timer.set()
logging.info(f"Database loaded in {round(perf_timer.get(), 3)} seconds.")

perf_timer.set()
keys = set(master_library.keys())
for pl in multi_playlist:
	if db_version > 68 or db_version == 0:
		keys -= set(pl.playlist_ids)
	else:
		keys -= set(pl[2])
if len(keys) > 5000:
	gui.suggest_clean_db = True
# logging.info(f"Database scanned in {round(perf_timer.get(), 3)} seconds.")

pump = False
shoot_pump.join()

# temporary
if window_size is None:
	window_size = window_default_size
	gui.rspw = 200


def track_number_process(line: str) -> str:
	line = str(line).split("/", 1)[0].lstrip("0")
	if prefs.dd_index and len(line) == 1:
		return "0" + line
	return line


def advance_theme() -> None:
	global theme

	theme += 1
	gui.reload_theme = True


def get_theme_number(name: str) -> int:
	if name == "Mindaro":
		return 0
	themes = get_themes()
	for i, theme in enumerate(themes):
		if theme[1] == name:
			return i + 1
	return 0


def get_theme_name(number: int) -> str:
	if number == 0:
		return "Mindaro"
	number -= 1
	themes = get_themes()
	logging.info((number, themes))
	if len(themes) > number:
		return themes[number][1]
	return ""

# Run upgrades if we're behind the current DB standard
if db_version > 0 and db_version < latest_db_version:
	logging.warning(f"Current DB version {db_version} was lower than latest {latest_db_version}, running migrations!")
	try:
		master_library, multi_playlist, star_store, p_force_queue, theme, prefs, gui, gen_codes, radio_playlists = database_migrate(
			db_version=db_version,
			master_library=master_library,
			install_mode=install_mode,
			multi_playlist=multi_playlist,
			star_store=star_store,
			install_directory=install_directory,
			a_cache_dir=a_cache_dir,
			cache_directory=cache_directory,
			config_directory=config_directory,
			user_directory=user_directory,
			gui=gui,
			gen_codes=gen_codes,
			prefs=prefs,
			radio_playlists=radio_playlists,
			theme=theme,
			p_force_queue=p_force_queue,
		)
	except ValueError:
		logging.exception("That should not happen")
	except Exception:
		logging.exception("Unknown error running database migration!")

playing_in_queue = min(playing_in_queue, len(track_queue) - 1)

shoot = threading.Thread(target=keymaps.load)
shoot.daemon = True
shoot.start()

# Loading Config -----------------

download_directories: list[str] = []

if download_directory.is_dir():
	download_directories.append(str(download_directory))

if music_directory is not None and music_directory.is_dir():
	download_directories.append(str(music_directory))

cf = Config()


def save_prefs():
	cf.update_value("sync-bypass-transcode", prefs.bypass_transcode)
	cf.update_value("sync-bypass-low-bitrate", prefs.smart_bypass)
	cf.update_value("radio-record-codec", prefs.radio_record_codec)

	cf.update_value("plex-username", prefs.plex_username)
	cf.update_value("plex-password", prefs.plex_password)
	cf.update_value("plex-servername", prefs.plex_servername)

	cf.update_value("subsonic-username", prefs.subsonic_user)
	cf.update_value("subsonic-password", prefs.subsonic_password)
	cf.update_value("subsonic-password-plain", prefs.subsonic_password_plain)
	cf.update_value("subsonic-server-url", prefs.subsonic_server)

	cf.update_value("jelly-username", prefs.jelly_username)
	cf.update_value("jelly-password", prefs.jelly_password)
	cf.update_value("jelly-server-url", prefs.jelly_server_url)

	cf.update_value("koel-username", prefs.koel_username)
	cf.update_value("koel-password", prefs.koel_password)
	cf.update_value("koel-server-url", prefs.koel_server_url)
	cf.update_value("stream-bitrate", prefs.network_stream_bitrate)

	cf.update_value("display-language", prefs.ui_lang)
	# cf.update_value("decode-search", prefs.diacritic_search)

	# cf.update_value("use-log-volume-scale", prefs.log_vol)
	# cf.update_value("audio-backend", prefs.backend)
	cf.update_value("use-pipewire", prefs.pipewire)
	cf.update_value("seek-interval", prefs.seek_interval)
	cf.update_value("pause-fade-time", prefs.pause_fade_time)
	cf.update_value("cross-fade-time", prefs.cross_fade_time)
	cf.update_value("device-buffer-ms", prefs.device_buffer)
	cf.update_value("output-samplerate", prefs.samplerate)
	cf.update_value("resample-quality", prefs.resample)
	cf.update_value("avoid_resampling", prefs.avoid_resampling)
	# cf.update_value("fast-scrubbing", prefs.pa_fast_seek)
	cf.update_value("precache-local-files", prefs.precache)
	cf.update_value("cache-use-tmp", prefs.tmp_cache)
	cf.update_value("cache-limit", prefs.cache_limit)
	cf.update_value("always-ffmpeg", prefs.always_ffmpeg)
	cf.update_value("volume-curve", prefs.volume_power)
	# cf.update_value("force-mono", prefs.mono)
	# cf.update_value("disconnect-device-pause", prefs.dc_device_setting)
	# cf.update_value("use-short-buffering", prefs.short_buffer)

	# cf.update_value("gst-output", prefs.gst_output)
	# cf.update_value("gst-use-custom-output", prefs.gst_use_custom_output)

	cf.update_value("separate-multi-genre", prefs.sep_genre_multi)

	cf.update_value("tag-editor-name", prefs.tag_editor_name)
	cf.update_value("tag-editor-target", prefs.tag_editor_target)

	cf.update_value("playback-follow-cursor", prefs.playback_follow_cursor)
	cf.update_value("spotify-prefer-web", prefs.launch_spotify_web)
	cf.update_value("spotify-allow-local", prefs.launch_spotify_local)
	cf.update_value("back-restarts", prefs.back_restarts)
	cf.update_value("end-queue-stop", prefs.stop_end_queue)
	cf.update_value("block-suspend", prefs.block_suspend)
	cf.update_value("allow-video-formats", prefs.allow_video_formats)

	cf.update_value("ui-scale", prefs.scale_want)
	cf.update_value("auto-scale", prefs.x_scale)
	cf.update_value("tracklist-y-text-offset", prefs.tracklist_y_text_offset)
	cf.update_value("theme-name", prefs.theme_name)
	cf.update_value("mac-style", prefs.macstyle)
	cf.update_value("allow-art-zoom", prefs.zoom_art)

	cf.update_value("scroll-gallery-by-row", prefs.gallery_row_scroll)
	cf.update_value("prefs.gallery_scroll_wheel_px", prefs.gallery_row_scroll)
	cf.update_value("scroll-spectrogram", prefs.spec2_scroll)
	cf.update_value("mascot-opacity", prefs.custom_bg_opacity)
	cf.update_value("synced-lyrics-time-offset", prefs.sync_lyrics_time_offset)

	cf.update_value("artist-list-prefers-album-artist", prefs.artist_list_prefer_album_artist)
	cf.update_value("side-panel-info-persists", prefs.meta_persists_stop)
	cf.update_value("side-panel-info-selected", prefs.meta_shows_selected)
	cf.update_value("side-panel-info-selected-always", prefs.meta_shows_selected_always)
	cf.update_value("mini-mode-avoid-notifications", prefs.stop_notifications_mini_mode)
	cf.update_value("hide-queue-when-empty", prefs.hide_queue)
	# cf.update_value("show-playlist-list", prefs.show_playlist_list)
	cf.update_value("enable-art-header-bar", prefs.art_in_top_panel)
	cf.update_value("always-art-header-bar", prefs.always_art_header)
	# cf.update_value("prefer-center-bg", prefs.center_bg)
	cf.update_value("showcase-texture-background", prefs.showcase_overlay_texture)
	cf.update_value("side-panel-style", prefs.side_panel_layout)
	cf.update_value("side-lyrics-art", prefs.show_side_lyrics_art_panel)
	cf.update_value("side-lyrics-art-on-top", prefs.lyric_metadata_panel_top)
	cf.update_value("absolute-track-indices", prefs.use_absolute_track_index)
	cf.update_value("auto-hide-bottom-title", prefs.hide_bottom_title)
	cf.update_value("auto-show-playing", prefs.auto_goto_playing)
	cf.update_value("notify-include-album", prefs.notify_include_album)
	cf.update_value("show-rating-hint", prefs.rating_playtime_stars)
	cf.update_value("drag-tab-to-unpin", prefs.drag_to_unpin)

	cf.update_value("gallery-thin-borders", prefs.thin_gallery_borders)
	cf.update_value("increase-row-spacing", prefs.increase_gallery_row_spacing)
	cf.update_value("gallery-center-text", prefs.center_gallery_text)

	cf.update_value("use-custom-fonts", prefs.use_custom_fonts)
	cf.update_value("font-main-standard", prefs.linux_font)
	cf.update_value("font-main-medium", prefs.linux_font_semibold)
	cf.update_value("font-main-bold", prefs.linux_font_bold)
	cf.update_value("font-main-condensed", prefs.linux_font_condensed)
	cf.update_value("font-main-condensed-bold", prefs.linux_font_condensed_bold)

	cf.update_value("force-subpixel-text", prefs.force_subpixel_text)

	cf.update_value("double-digit-indices", prefs.dd_index)
	cf.update_value("column-album-artist-fallsback", prefs.column_aa_fallback_artist)
	cf.update_value("left-aligned-album-artist-title", prefs.left_align_album_artist_title)
	cf.update_value("import-auto-sort", prefs.auto_sort)

	cf.update_value("encode-output-dir", prefs.custom_encoder_output)
	cf.update_value("sync-device-music-dir", prefs.sync_target)
	cf.update_value("add_download_directory", prefs.download_dir1)

	cf.update_value("use-system-tray", prefs.use_tray)
	cf.update_value("use-gamepad", prefs.use_gamepad)
	cf.update_value("enable-remote-interface", prefs.enable_remote)

	cf.update_value("enable-mpris", prefs.enable_mpris)
	cf.update_value("hide-maximize-button", prefs.force_hide_max_button)
	cf.update_value("restore-window-position", prefs.save_window_position)
	cf.update_value("mini-mode-always-on-top", prefs.mini_mode_on_top)
	cf.update_value("resume-playback-on-restart", prefs.reload_play_state)
	cf.update_value("resume-playback-on-wake", prefs.resume_play_wake)
	cf.update_value("auto-dl-artist-data", prefs.auto_dl_artist_data)

	cf.update_value("fanart.tv-cover", prefs.enable_fanart_cover)
	cf.update_value("fanart.tv-artist", prefs.enable_fanart_artist)
	cf.update_value("fanart.tv-background", prefs.enable_fanart_bg)
	cf.update_value("auto-update-playlists", prefs.always_auto_update_playlists)
	cf.update_value("write-ratings-to-tag", prefs.write_ratings)
	cf.update_value("enable-spotify", prefs.spot_mode)
	cf.update_value("enable-discord-rpc", prefs.discord_enable)
	cf.update_value("auto-search-lyrics", prefs.auto_lyrics)
	cf.update_value("shortcuts-ignore-keymap", prefs.use_scancodes)
	cf.update_value("alpha_key_activate_search", prefs.search_on_letter)

	cf.update_value("discogs-personal-access-token", prefs.discogs_pat)
	cf.update_value("listenbrainz-token", prefs.lb_token)
	cf.update_value("custom-listenbrainz-url", prefs.listenbrainz_url)

	cf.update_value("maloja-key", prefs.maloja_key)
	cf.update_value("maloja-url", prefs.maloja_url)
	cf.update_value("maloja-enable", prefs.maloja_enable)

	cf.update_value("tau-url", prefs.sat_url)

	cf.update_value("lastfm-pull-love", prefs.lastfm_pull_love)

	cf.update_value("broadcast-page-port", prefs.metadata_page_port)
	cf.update_value("show-current-on-transition", prefs.show_current_on_transition)

	cf.update_value("chart-columns", prefs.chart_columns)
	cf.update_value("chart-rows", prefs.chart_rows)
	cf.update_value("chart-uses-text", prefs.chart_text)
	cf.update_value("chart-font", prefs.chart_font)
	cf.update_value("chart-sorts-top-played", prefs.topchart_sorts_played)

	if config_directory.is_dir():
		cf.dump(str(config_directory / "tauon.conf"))
	else:
		logging.error("Missing config directory")


def load_prefs():
	cf.reset()
	cf.load(str(config_directory / "tauon.conf"))

	cf.add_comment("Tauon Music Box configuration file")
	cf.br()
	cf.add_comment(
		"This file will be regenerated while app is running. Formatting and additional comments will be lost.")
	cf.add_comment("Tip: Use TOML syntax highlighting")

	cf.br()
	cf.add_text("[audio]")

	# prefs.backend = cf.sync_add("int", "audio-backend", prefs.backend, "4: Built in backend (Phazor), 2: GStreamer")
	prefs.pipewire = cf.sync_add(
		"bool", "use-pipewire", prefs.pipewire,
		"Experimental setting to use Pipewire native only.")

	prefs.seek_interval = cf.sync_add(
		"int", "seek-interval", prefs.seek_interval,
		"In s. Interval to seek when using keyboard shortcut. Default is 15.")
	# prefs.pause_fade_time = cf.sync_add("int", "pause-fade-time", prefs.pause_fade_time, "In milliseconds. Default is 400. (GStreamer Only)")

	prefs.pause_fade_time = max(prefs.pause_fade_time, 100)
	prefs.pause_fade_time = min(prefs.pause_fade_time, 5000)

	prefs.cross_fade_time = cf.sync_add(
		"int", "cross-fade-time", prefs.cross_fade_time,
		"In ms. Min: 200, Max: 2000, Default: 700. Applies to track change crossfades. End of track is always gapless.")

	prefs.device_buffer = cf.sync_add("int", "device-buffer-ms", prefs.device_buffer, "Default: 80")
	#prefs.samplerate = cf.sync_add(
	#	"int", "output-samplerate", prefs.samplerate,
	#	"In hz. Default: 48000, alt: 44100. (restart app to apply change)")
	prefs.avoid_resampling = cf.sync_add(
		"bool", "avoid_resampling", prefs.avoid_resampling,
		"Only implemented for FLAC, MP3, OGG, OPUS")
	prefs.resample = cf.sync_add(
		"int", "resample-quality", prefs.resample,
		"0=best, 1=medium, 2=fast, 3=fastest. Default: 1. (applies on restart)")
	if prefs.resample < 0 or prefs.resample > 4:
		prefs.resample = 1
	# prefs.pa_fast_seek = cf.sync_add("bool", "fast-scrubbing", prefs.pa_fast_seek, "Seek without a delay but may cause audible popping")
	prefs.cache_limit = cf.sync_add(
		"int", "cache-limit", prefs.cache_limit,
		"Limit size of network audio file cache. In MB.")
	prefs.tmp_cache = cf.sync_add(
		"bool", "cache-use-tmp", prefs.tmp_cache,
		"Use /tmp for cache. When enabled, above setting overridden to a small value. (applies on restart)")
	prefs.precache = cf.sync_add(
		"bool", "precache-local-files", prefs.precache,
		"Cache files from local sources too. (Useful for mounted network drives)")
	prefs.always_ffmpeg = cf.sync_add(
		"bool", "always-ffmpeg", prefs.always_ffmpeg,
		"Prefer decoding using FFMPEG. Fixes stuttering on Raspberry Pi OS.")
	prefs.volume_power = cf.sync_add(
		"int", "volume-curve", prefs.volume_power,
		"1=Linear volume control. Values above one give greater control bias over lower volume range. Default: 2")

	# prefs.mono = cf.sync_add("bool", "force-mono", prefs.mono, "This is a placeholder setting and currently has no effect.")
	# prefs.dc_device_setting = cf.sync_add("string", "disconnect-device-pause", prefs.dc_device_setting, "Can be \"on\" or \"off\". BASS only. When off, connection to device will he held open.")
	# prefs.short_buffer = cf.sync_add("bool", "use-short-buffering", prefs.short_buffer, "BASS only.")

	# cf.br()
	# cf.add_text("[audio (gstreamer only)]")
	#
	# prefs.gst_output = cf.sync_add("string", "gst-output", prefs.gst_output, "GStreamer output pipeline specification. Only used with GStreamer backend.")
	# prefs.gst_use_custom_output = cf.sync_add("bool", "gst-use-custom-output", prefs.gst_use_custom_output, "Set this to true to apply any manual edits of the above string.")

	if prefs.dc_device_setting == "on":
		prefs.dc_device = True
	elif prefs.dc_device_setting == "off":
		prefs.dc_device = False

	cf.br()
	cf.add_text("[locale]")
	prefs.ui_lang = cf.sync_add(
		"string", "display-language", prefs.ui_lang, "Override display language to use if "
		"available. E.g. \"en\", \"ja\", \"zh_CH\". "
		"Default: \"auto\"")
	# prefs.diacritic_search = cf.sync_add("bool", "decode-search", prefs.diacritic_search, "Allow searching of diacritics etc using ascii in search functions. (Disablng may speed up search)")
	cf.br()
	cf.add_text("[search]")
	prefs.sep_genre_multi = cf.sync_add(
		"bool", "separate-multi-genre", prefs.sep_genre_multi,
		"If true, the standard genre result will exclude results from multi-value tags. These will be included in a separate result.")

	cf.br()
	cf.add_text("[tag-editor]")
	if system == "Windows" or msys:
		prefs.tag_editor_name = cf.sync_add("string", "tag-editor-name", "Picard", "Name to display in UI.")
		prefs.tag_editor_target = cf.sync_add(
			"string", "tag-editor-target",
			"C:\\Program Files (x86)\\MusicBrainz Picard\\picard.exe",
			"The path of the exe to run.")
	else:
		prefs.tag_editor_name = cf.sync_add("string", "tag-editor-name", "Picard", "Name to display in UI.")
		prefs.tag_editor_target = cf.sync_add(
			"string", "tag-editor-target", "picard",
			"The name of the binary to call.")

	cf.br()
	cf.add_text("[playback]")
	prefs.playback_follow_cursor = cf.sync_add(
		"bool", "playback-follow-cursor", prefs.playback_follow_cursor,
		"When advancing, always play the track that is selected.")
	prefs.launch_spotify_web = cf.sync_add(
		"bool", "spotify-prefer-web", prefs.launch_spotify_web,
		"Launch the web client rather than attempting to launch the desktop client.")
	prefs.launch_spotify_local = cf.sync_add(
		"bool", "spotify-allow-local", prefs.launch_spotify_local,
		"Play Spotify audio through Tauon.")
	prefs.back_restarts = cf.sync_add(
		"bool", "back-restarts", prefs.back_restarts,
		"Pressing the back button restarts playing track on first press.")
	prefs.stop_end_queue = cf.sync_add(
		"bool", "end-queue-stop", prefs.stop_end_queue,
		"Queue will always enable auto-stop on last track")
	prefs.block_suspend = cf.sync_add(
		"bool", "block-suspend", prefs.block_suspend,
		"Prevent system suspend during playback")
	prefs.allow_video_formats = cf.sync_add(
		"bool", "allow-video-formats", prefs.allow_video_formats,
		"Allow the import of MP4 and WEBM formats")
	if prefs.allow_video_formats:
		for item in VID_Formats:
			if item not in DA_Formats:
				DA_Formats.add(item)

	cf.br()
	cf.add_text("[HiDPI]")
	prefs.scale_want = cf.sync_add(
		"float", "ui-scale", prefs.scale_want,
		"UI scale factor. Default is 1.0, try increase if using a HiDPI display.")
	prefs.x_scale = cf.sync_add("bool", "auto-scale", prefs.x_scale, "Automatically choose above setting")
	prefs.tracklist_y_text_offset = cf.sync_add(
		"int", "tracklist-y-text-offset", prefs.tracklist_y_text_offset,
		"If you're using a UI scale, you may need to tweak this.")

	cf.br()
	cf.add_text("[ui]")

	prefs.theme_name = cf.sync_add("string", "theme-name", prefs.theme_name)
	macstyle = cf.sync_add("bool", "mac-style", prefs.macstyle, "Use macOS style window buttons")
	prefs.zoom_art = cf.sync_add("bool", "allow-art-zoom", prefs.zoom_art)
	prefs.gallery_row_scroll = cf.sync_add("bool", "scroll-gallery-by-row", True)
	prefs.gallery_scroll_wheel_px = cf.sync_add(
		"int", "scroll-gallery-distance", 90,
		"Only has effect if scroll-gallery-by-row is false.")
	prefs.spec2_scroll = cf.sync_add("bool", "scroll-spectrogram", prefs.spec2_scroll)
	prefs.custom_bg_opacity = cf.sync_add("int", "mascot-opacity", prefs.custom_bg_opacity)
	if prefs.custom_bg_opacity < 0 or prefs.custom_bg_opacity > 100:
		prefs.custom_bg_opacity = 40
		logging.warning("Invalid value for mascot-opacity")

	prefs.sync_lyrics_time_offset = cf.sync_add(
		"int", "synced-lyrics-time-offset", prefs.sync_lyrics_time_offset,
		"In milliseconds. May be negative.")
	prefs.artist_list_prefer_album_artist = cf.sync_add(
		"bool", "artist-list-prefers-album-artist",
		prefs.artist_list_prefer_album_artist,
		"May require restart for change to take effect.")
	prefs.meta_persists_stop = cf.sync_add(
		"bool", "side-panel-info-persists", prefs.meta_persists_stop,
		"Show album art and metadata of last played track when stopped.")
	prefs.meta_shows_selected = cf.sync_add(
		"bool", "side-panel-info-selected", prefs.meta_shows_selected,
		"Show album art and metadata of selected track when stopped. (overides above setting)")
	prefs.meta_shows_selected_always = cf.sync_add(
		"bool", "side-panel-info-selected-always",
		prefs.meta_shows_selected_always,
		"Show album art and metadata of selected track at all times. (overides the above 2 settings)")
	prefs.stop_notifications_mini_mode = cf.sync_add(
		"bool", "mini-mode-avoid-notifications",
		prefs.stop_notifications_mini_mode,
		"Avoid sending track change notifications when in Mini Mode")
	prefs.hide_queue = cf.sync_add("bool", "hide-queue-when-empty", prefs.hide_queue)
	# prefs.show_playlist_list = cf.sync_add("bool", "show-playlist-list", prefs.show_playlist_list)

	prefs.show_current_on_transition = cf.sync_add(
		"bool", "show-current-on-transition",
		prefs.show_current_on_transition,
		"Always jump to new playing track even with natural transition (broken setting, is always enabled")
	prefs.art_in_top_panel = cf.sync_add(
		"bool", "enable-art-header-bar", prefs.art_in_top_panel,
		"Show art in top panel when window is narrow")
	prefs.always_art_header = cf.sync_add(
		"bool", "always-art-header-bar", prefs.always_art_header,
		"Show art in top panel at any size. (Requires enable-art-header-bar)")

	# prefs.center_bg = cf.sync_add("bool", "prefer-center-bg", prefs.center_bg, "Always center art for the background art function")
	prefs.showcase_overlay_texture = cf.sync_add(
		"bool", "showcase-texture-background", prefs.showcase_overlay_texture,
		"Draw pattern over background art")
	prefs.side_panel_layout = cf.sync_add("int", "side-panel-style", prefs.side_panel_layout, "0:default, 1:centered")
	prefs.show_side_lyrics_art_panel = cf.sync_add("bool", "side-lyrics-art", prefs.show_side_lyrics_art_panel)
	prefs.lyric_metadata_panel_top = cf.sync_add("bool", "side-lyrics-art-on-top", prefs.lyric_metadata_panel_top)
	prefs.use_absolute_track_index = cf.sync_add(
		"bool", "absolute-track-indices", prefs.use_absolute_track_index,
		"For playlists with titles disabled only")
	prefs.hide_bottom_title = cf.sync_add(
		"bool", "auto-hide-bottom-title", prefs.hide_bottom_title,
		"Hide title in bottom panel when already shown in side panel")
	prefs.auto_goto_playing = cf.sync_add(
		"bool", "auto-show-playing", prefs.auto_goto_playing,
		"Show playing track in current playlist on track and playlist change even if not the playing playlist")

	prefs.notify_include_album = cf.sync_add(
		"bool", "notify-include-album", prefs.notify_include_album,
		"Include album name in track change notifications")
	prefs.rating_playtime_stars = cf.sync_add(
		"bool", "show-rating-hint", prefs.rating_playtime_stars,
		"Indicate playtime in rating stars")

	prefs.drag_to_unpin = cf.sync_add(
		"bool", "drag-tab-to-unpin", prefs.drag_to_unpin,
		"Dragging a tab off the top-panel un-pins it")

	cf.br()
	cf.add_text("[gallery]")
	prefs.thin_gallery_borders = cf.sync_add("bool", "gallery-thin-borders", prefs.thin_gallery_borders)
	prefs.increase_gallery_row_spacing = cf.sync_add("bool", "increase-row-spacing", prefs.increase_gallery_row_spacing)
	prefs.center_gallery_text = cf.sync_add("bool", "gallery-center-text", prefs.center_gallery_text)

	# show-current-on-transition", prefs.show_current_on_transition)
	if system != "windows":
		cf.br()
		cf.add_text("[fonts]")
		cf.add_comment("Changes will require app restart.")
		prefs.use_custom_fonts = cf.sync_add(
			"bool", "use-custom-fonts", prefs.use_custom_fonts,
			"Setting to false will reset below settings to default on restart")
		if prefs.use_custom_fonts:
			prefs.linux_font = cf.sync_add(
				"string", "font-main-standard", prefs.linux_font,
				"Suggested alternate: Liberation Sans")
			prefs.linux_font_semibold = cf.sync_add("string", "font-main-medium", prefs.linux_font_semibold)
			prefs.linux_font_bold = cf.sync_add("string", "font-main-bold", prefs.linux_font_bold)
			prefs.linux_font_condensed = cf.sync_add("string", "font-main-condensed", prefs.linux_font_condensed)
			prefs.linux_font_condensed_bold = cf.sync_add("string", "font-main-condensed-bold", prefs.linux_font_condensed_bold)

		else:
			cf.sync_add("string", "font-main-standard", prefs.linux_font, "Suggested alternate: Liberation Sans")
			cf.sync_add("string", "font-main-medium", prefs.linux_font_semibold)
			cf.sync_add("string", "font-main-bold", prefs.linux_font_bold)
			cf.sync_add("string", "font-main-condensed", prefs.linux_font_condensed)
			cf.sync_add("string", "font-main-condensed-bold", prefs.linux_font_condensed_bold)

		# prefs.force_subpixel_text = cf.sync_add("bool", "force-subpixel-text", prefs.force_subpixel_text, "(Subpixel rendering defaults to off with Flatpak)")

	cf.br()
	cf.add_text("[tracklist]")
	prefs.dd_index = cf.sync_add("bool", "double-digit-indices", prefs.dd_index)
	prefs.column_aa_fallback_artist = cf.sync_add(
		"bool", "column-album-artist-fallsback",
		prefs.column_aa_fallback_artist,
		"'Album artist' column shows 'artist' if otherwise blank.")
	prefs.left_align_album_artist_title = cf.sync_add(
		"bool", "left-aligned-album-artist-title",
		prefs.left_align_album_artist_title,
		"Show 'Album artist' in the folder/album title. Uses colour 'column-album-artist' from theme file")
	prefs.auto_sort = cf.sync_add(
		"bool", "import-auto-sort", prefs.auto_sort,
		"This setting is deprecated and will be removed in a future version")

	cf.br()
	cf.add_text("[transcode]")
	prefs.bypass_transcode = cf.sync_add(
		"bool", "sync-bypass-transcode", prefs.bypass_transcode,
		"Don't transcode files with sync function")
	prefs.smart_bypass = cf.sync_add("bool", "sync-bypass-low-bitrate", prefs.smart_bypass,
		"Skip transcode of <=128kbs folders")
	prefs.radio_record_codec = cf.sync_add("string", "radio-record-codec", prefs.radio_record_codec,
		"Can be OPUS, OGG, FLAC, or MP3. Default: OPUS")

	cf.br()
	cf.add_text("[directories]")
	cf.add_comment("Use full paths")
	prefs.sync_target = cf.sync_add("string", "sync-device-music-dir", prefs.sync_target)
	prefs.custom_encoder_output = cf.sync_add(
		"string", "encode-output-dir", prefs.custom_encoder_output,
		"E.g. \"/home/example/music/output\". If left blank, encode-output in home music dir will be used.")
	if prefs.custom_encoder_output:
		prefs.encoder_output = prefs.custom_encoder_output
	prefs.download_dir1 = cf.sync_add(
		"string", "add_download_directory", prefs.download_dir1,
		"Add another folder to monitor in addition to home downloads and music.")
	if prefs.download_dir1 and prefs.download_dir1 not in download_directories:
		if os.path.isdir(prefs.download_dir1):
			download_directories.append(prefs.download_dir1)
		else:
			logging.warning("Invalid download directory in config")

	cf.br()
	cf.add_text("[app]")
	prefs.enable_remote = cf.sync_add(
		"bool", "enable-remote-interface", prefs.enable_remote,
		"For use with Tauon Music Remote for Android")
	prefs.use_gamepad = cf.sync_add("bool", "use-gamepad", prefs.use_gamepad, "Use game controller for UI control, restart on change.")
	prefs.use_tray = cf.sync_add("bool", "use-system-tray", prefs.use_tray)
	prefs.force_hide_max_button = cf.sync_add("bool", "hide-maximize-button", prefs.force_hide_max_button)
	prefs.save_window_position = cf.sync_add(
		"bool", "restore-window-position", prefs.save_window_position,
		"Save and restore the last window position on desktop on open")
	prefs.mini_mode_on_top  = cf.sync_add("bool", "mini-mode-always-on-top", prefs.mini_mode_on_top)
	prefs.enable_mpris = cf.sync_add("bool", "enable-mpris", prefs.enable_mpris)
	prefs.reload_play_state = cf.sync_add("bool", "resume-playback-on-restart", prefs.reload_play_state)
	prefs.resume_play_wake = cf.sync_add("bool", "resume-playback-on-wake", prefs.resume_play_wake)
	prefs.auto_dl_artist_data = cf.sync_add(
		"bool", "auto-dl-artist-data", prefs.auto_dl_artist_data,
		"Enable automatic downloading of thumbnails in artist list")
	prefs.enable_fanart_cover = cf.sync_add("bool", "fanart.tv-cover", prefs.enable_fanart_cover)
	prefs.enable_fanart_artist = cf.sync_add("bool", "fanart.tv-artist", prefs.enable_fanart_artist)
	prefs.enable_fanart_bg = cf.sync_add("bool", "fanart.tv-background", prefs.enable_fanart_bg)
	prefs.always_auto_update_playlists = cf.sync_add(
		"bool", "auto-update-playlists",
		prefs.always_auto_update_playlists,
		"Automatically update generator playlists")
	prefs.write_ratings = cf.sync_add(
		"bool", "write-ratings-to-tag", prefs.write_ratings,
		"This writes FMPS_Rating tags on disk. Only writing to MP3, OGG and FLAC files is currently supported.")
	prefs.spot_mode = cf.sync_add("bool", "enable-spotify", prefs.spot_mode, "Enable Spotify specific features")
	prefs.discord_enable = cf.sync_add(
		"bool", "enable-discord-rpc", prefs.discord_enable,
		"Show track info in running Discord application")
	prefs.auto_lyrics = cf.sync_add(
		"bool", "auto-search-lyrics", prefs.auto_lyrics,
		"Automatically search internet for lyrics when display is wanted")

	prefs.use_scancodes = cf.sync_add(
		"bool", "shortcuts-ignore-keymap", prefs.use_scancodes,
		"When enabled, shortcuts will map to the physical keyboard layout")
	prefs.search_on_letter = cf.sync_add("bool", "alpha_key_activate_search", prefs.search_on_letter,
		"When enabled, pressing single letter keyboard key will activate the global search")

	cf.br()
	cf.add_text("[tokens]")
	temp = cf.sync_add(
		"string", "discogs-personal-access-token", prefs.discogs_pat,
		"Used for sourcing of artist thumbnails.")
	if not temp:
		prefs.discogs_pat = ""
	elif len(temp) != 40:
		logging.warning("Invalid discogs token in config")
	else:
		prefs.discogs_pat = temp

	prefs.listenbrainz_url = cf.sync_add(
		"string", "custom-listenbrainz-url", prefs.listenbrainz_url,
		"Specify a custom Listenbrainz compatible api url. E.g. \"https://example.tld/apis/listenbrainz/\" Default: Blank")
	prefs.lb_token = cf.sync_add("string", "listenbrainz-token", prefs.lb_token)

	cf.br()
	cf.add_text("[tauon_satellite]")
	prefs.sat_url = cf.sync_add("string", "tau-url", prefs.sat_url, "Exclude the port")

	cf.br()
	cf.add_text("[lastfm]")
	prefs.lastfm_pull_love = cf.sync_add(
		"bool", "lastfm-pull-love", prefs.lastfm_pull_love,
		"Overwrite local love status on scrobble")


	cf.br()
	cf.add_text("[maloja_account]")
	prefs.maloja_url = cf.sync_add(
		"string", "maloja-url", prefs.maloja_url,
		"A Maloja server URL, e.g. http://localhost:32400")
	prefs.maloja_key = cf.sync_add("string", "maloja-key", prefs.maloja_key, "One of your Maloja API keys")
	prefs.maloja_enable = cf.sync_add("bool", "maloja-enable", prefs.maloja_enable)

	cf.br()
	cf.add_text("[plex_account]")
	prefs.plex_username = cf.sync_add(
		"string", "plex-username", prefs.plex_username,
		"Probably the email address you used to make your PLEX account.")
	prefs.plex_password = cf.sync_add(
		"string", "plex-password", prefs.plex_password,
		"The password associated with your PLEX account.")
	prefs.plex_servername = cf.sync_add(
		"string", "plex-servername", prefs.plex_servername,
		"Probably your servers hostname.")

	cf.br()
	cf.add_text("[subsonic_account]")
	prefs.subsonic_user = cf.sync_add("string", "subsonic-username", prefs.subsonic_user)
	prefs.subsonic_password = cf.sync_add("string", "subsonic-password", prefs.subsonic_password)
	prefs.subsonic_password_plain = cf.sync_add("bool", "subsonic-password-plain", prefs.subsonic_password_plain)
	prefs.subsonic_server = cf.sync_add("string", "subsonic-server-url", prefs.subsonic_server)

	cf.br()
	cf.add_text("[koel_account]")
	prefs.koel_username = cf.sync_add("string", "koel-username", prefs.koel_username, "E.g. admin@example.com")
	prefs.koel_password = cf.sync_add("string", "koel-password", prefs.koel_password, "The default is admin")
	prefs.koel_server_url = cf.sync_add(
		"string", "koel-server-url", prefs.koel_server_url,
		"The URL or IP:Port where the Koel server is hosted. E.g. http://localhost:8050 or https://localhost:8060")
	prefs.koel_server_url = prefs.koel_server_url.rstrip("/")

	cf.br()
	cf.add_text("[jellyfin_account]")
	prefs.jelly_username = cf.sync_add("string", "jelly-username", prefs.jelly_username, "")
	prefs.jelly_password = cf.sync_add("string", "jelly-password", prefs.jelly_password, "")
	prefs.jelly_server_url = cf.sync_add(
		"string", "jelly-server-url", prefs.jelly_server_url,
		"The IP:Port where the jellyfin server is hosted.")
	prefs.jelly_server_url = prefs.jelly_server_url.rstrip("/")

	cf.br()
	cf.add_text("[network]")
	prefs.network_stream_bitrate = cf.sync_add(
		"int", "stream-bitrate", prefs.network_stream_bitrate,
		"Optional bitrate koel/subsonic should transcode to (Server may need to be configured for this). Set to 0 to disable transcoding.")

	cf.br()
	cf.add_text("[listenalong]")
	prefs.metadata_page_port = cf.sync_add(
		"int", "broadcast-page-port", prefs.metadata_page_port,
		"Change applies on app restart or setting re-enable")

	cf.br()
	cf.add_text("[chart]")
	prefs.chart_columns = cf.sync_add("int", "chart-columns", prefs.chart_columns)
	prefs.chart_rows = cf.sync_add("int", "chart-rows", prefs.chart_rows)
	prefs.chart_text = cf.sync_add("bool", "chart-uses-text", prefs.chart_text)
	prefs.topchart_sorts_played = cf.sync_add("bool", "chart-sorts-top-played", prefs.topchart_sorts_played)
	prefs.chart_font = cf.sync_add(
		"string", "chart-font", prefs.chart_font,
		"Format is fontname + size. Default is Monospace 10")


load_prefs()
save_prefs()

# Temporary
if 0 < db_version <= 34:
	prefs.theme_name = get_theme_name(theme)
if 0 < db_version <= 66:
	prefs.device_buffer = 80
if 0 < db_version <= 53:
	logging.info("Resetting fonts to defaults")
	prefs.linux_font = "Noto Sans"
	prefs.linux_font_semibold = "Noto Sans Medium"
	prefs.linux_font_bold = "Noto Sans Bold"
	save_prefs()

# Auto detect lang
lang: list[str] | None = None
if prefs.ui_lang != "auto" or prefs.ui_lang == "":
	# Force set lang
	lang = [prefs.ui_lang]

f = gettext.find("tauon", localedir=str(locale_directory), languages=lang)
if f:
	translation = gettext.translation("tauon", localedir=str(locale_directory), languages=lang)
	translation.install()
	builtins._ = translation.gettext

	logging.info(f"Translation file for '{lang}' loaded")
elif lang:
	logging.error(f"No translation file available for '{lang}'")

# ----

sss = SDL_SysWMinfo()
SDL_GetWindowWMInfo(t_window, sss)

if prefs.use_gamepad:
	SDL_InitSubSystem(SDL_INIT_GAMECONTROLLER)

smtc = False

if msys and win_ver >= 10:

	#logging.info(sss.info.win.window)
	SMTC_path = install_directory / "lib" / "TauonSMTC.dll"
	if SMTC_path.exists():
		try:
			sm = ctypes.cdll.LoadLibrary(str(SMTC_path))

			def SMTC_button_callback(button: int) -> None:
				logging.debug(f"SMTC sent key ID: {button}")
				if button == 1:
					inp.media_key = "Play"
				if button == 2:
					inp.media_key = "Pause"
				if button == 3:
					inp.media_key = "Next"
				if button == 4:
					inp.media_key = "Previous"
				if button == 5:
					inp.media_key = "Stop"
				gui.update += 1
				tauon.wake()

			close_callback = ctypes.WINFUNCTYPE(ctypes.c_void_p, ctypes.c_int)(SMTC_button_callback)
			smtc = sm.init(close_callback) == 0
		except Exception:
			logging.exception("Failed to load TauonSMTC.dll - Media keys will not work!")
	else:
		logging.warning("Failed to load TauonSMTC.dll - Media keys will not work!")


def auto_scale() -> None:

	old = prefs.scale_want

	if prefs.x_scale:
		if sss.subsystem in (SDL_SYSWM_WAYLAND, SDL_SYSWM_COCOA, SDL_SYSWM_UNKNOWN):
			prefs.scale_want = window_size[0] / logical_size[0]
			if old != prefs.scale_want:
				logging.info("Applying scale based on buffer size")
		elif sss.subsystem == SDL_SYSWM_X11:
			if xdpi > 40:
				prefs.scale_want = xdpi / 96
				if old != prefs.scale_want:
					logging.info("Applying scale based on xft setting")

	prefs.scale_want = round(round(prefs.scale_want / 0.05) * 0.05, 2)

	if prefs.scale_want == 0.95:
		prefs.scale_want = 1.0
	if prefs.scale_want == 1.05:
		prefs.scale_want = 1.0
	if prefs.scale_want == 1.95:
		prefs.scale_want = 2.0
	if prefs.scale_want == 2.05:
		prefs.scale_want = 2.0

	if old != prefs.scale_want:
		logging.info(f"Using UI scale: {prefs.scale_want}")

	if prefs.scale_want < 0.5:
		prefs.scale_want = 1.0

	if window_size[0] < (560 * prefs.scale_want) * 0.9 or window_size[1] < (330 * prefs.scale_want) * 0.9:
		logging.info("Window overscale!")
		show_message(_("Detected unsuitable UI scaling."), _("Scaling setting reset to 1x"))
		prefs.scale_want = 1.0

auto_scale()


def scale_assets(scale_want: int, force: bool = False) -> None:
	global scaled_asset_directory
	if scale_want != 1:
		scaled_asset_directory = user_directory / "scaled-icons"
		if not scaled_asset_directory.exists() or len(os.listdir(str(svg_directory))) != len(
				os.listdir(str(scaled_asset_directory))):
			logging.info("Force rerender icons")
			force = True
	else:
		scaled_asset_directory = asset_directory

	if scale_want != prefs.ui_scale or force:

		if scale_want != 1:
			if scaled_asset_directory.is_dir() and scaled_asset_directory != asset_directory:
				shutil.rmtree(str(scaled_asset_directory))
			from tauon.t_modules.t_svgout import render_icons

			if scaled_asset_directory != asset_directory:
				logging.info("Rendering icons...")
				render_icons(str(svg_directory), str(scaled_asset_directory), scale_want)

		logging.info("Done rendering icons")

		diff_ratio = scale_want / prefs.ui_scale
		prefs.ui_scale = scale_want
		prefs.playlist_row_height = round(22 * prefs.ui_scale)

		# Save user values
		column_backup = gui.pl_st
		rspw = gui.pref_rspw
		grspw = gui.pref_gallery_w

		gui.destroy_textures()
		gui.rescale()

		# Scale saved values
		gui.pl_st = column_backup
		for item in gui.pl_st:
			item[1] *= diff_ratio
		gui.pref_rspw = rspw * diff_ratio
		gui.pref_gallery_w = grspw * diff_ratio
		global album_mode_art_size
		album_mode_art_size = int(album_mode_art_size * diff_ratio)


scale_assets(scale_want=prefs.scale_want)

try:
	#star_lines        = view_prefs['star-lines']
	update_title      = view_prefs["update-title"]
	prefs.prefer_side = view_prefs["side-panel"]
	prefs.dim_art     = False  # view_prefs['dim-art']
	#gui.turbo         = view_prefs['level-meter']
	#pl_follow         = view_prefs['pl-follow']
	scroll_enable     = view_prefs["scroll-enable"]
	if "break-enable" in view_prefs:
		break_enable    = view_prefs["break-enable"]
	else:
		logging.warning("break-enable not found in view_prefs[] when trying to load settings! First run?")
	#dd_index          = view_prefs['dd-index']
	#custom_line_mode  = view_prefs['custom-line']
	#thick_lines       = view_prefs['thick-lines']
	if "append-date" in view_prefs:
		prefs.append_date = view_prefs["append-date"]
	else:
		logging.warning("append-date not found in view_prefs[] when trying to load settings! First run?")
except KeyError:
	logging.exception("Failed to load settings - pref not found!")
except Exception:
	logging.exception("Failed to load settings!")

if prefs.prefer_side is False:
	gui.rsp = False


def get_global_mouse():
	i_y = pointer(c_int(0))
	i_x = pointer(c_int(0))
	SDL_GetGlobalMouseState(i_x, i_y)
	return i_x.contents.value, i_y.contents.value


def get_window_position():
	i_y = pointer(c_int(0))
	i_x = pointer(c_int(0))
	SDL_GetWindowPosition(t_window, i_x, i_y)
	return i_x.contents.value, i_y.contents.value




mpt = None
try:
	p = ctypes.util.find_library("libopenmpt")
	if p:
		mpt = ctypes.cdll.LoadLibrary(p)
	elif msys:
		mpt = ctypes.cdll.LoadLibrary("libopenmpt-0.dll")
	else:
		mpt = ctypes.cdll.LoadLibrary("libopenmpt.so")

	mpt.openmpt_module_create_from_memory.restype = c_void_p
	mpt.openmpt_module_get_metadata.restype = c_char_p
	mpt.openmpt_module_get_duration_seconds.restype = c_double
except Exception:
	logging.exception("Failed to load libopenmpt!")





gme = None
p = None
try:
	p = ctypes.util.find_library("libgme")
	if p:
		gme = ctypes.cdll.LoadLibrary(p)
	elif msys:
		gme = ctypes.cdll.LoadLibrary("libgme-0.dll")
	else:
		gme = ctypes.cdll.LoadLibrary("libgme.so")

	gme.gme_free_info.argtypes = [ctypes.POINTER(GMETrackInfo)]
	gme.gme_track_info.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.POINTER(GMETrackInfo)), ctypes.c_int]
	gme.gme_track_info.restype = ctypes.c_char_p
	gme.gme_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
	gme.gme_open_file.restype = ctypes.c_char_p

except Exception:
	logging.exception("Cannot find libgme")

def use_id3(tags: ID3, nt: TrackClass):
	def natural_get(tag: ID3, track: TrackClass, frame: str, attr: str) -> str | None:
		frames = tag.getall(frame)
		if frames and frames[0].text:
			if track is None:
				return str(frames[0].text[0])
			setattr(track, attr, str(frames[0].text[0]))
		elif track is None:
			return ""
		else:
			setattr(track, attr, "")

	tag = tags

	natural_get(tags, nt, "TIT2", "title")
	natural_get(tags, nt, "TPE1", "artist")
	natural_get(tags, nt, "TPE2", "album_artist")
	natural_get(tags, nt, "TCON", "genre")  # content type
	natural_get(tags, nt, "TALB", "album")
	natural_get(tags, nt, "TDRC", "date")
	natural_get(tags, nt, "TCOM", "composer")
	natural_get(tags, nt, "COMM", "comment")

	process_odat(nt, natural_get(tags, None, "TDOR", None))

	frames = tag.getall("POPM")
	rating = 0
	if frames:
		for frame in frames:
			if frame.rating:
				rating = frame.rating
				nt.misc["POPM"] = frame.rating

	if len(nt.comment) > 4 and nt.comment[2] == "+":
		nt.comment = ""
	if nt.comment[0:3] == "000":
		nt.comment = ""

	frames = tag.getall("USLT")
	if frames:
		nt.lyrics = frames[0].text
		if 0 < len(nt.lyrics) < 150:
			if "unavailable" in nt.lyrics or ".com" in nt.lyrics or "www." in nt.lyrics:
				nt.lyrics = ""

	frames = tag.getall("TPE1")
	if frames:
		d = []
		for frame in frames:
			for t in frame.text:
				d.append(t)
		if len(d) > 1:
			nt.misc["artists"] = d
			nt.artist = "; ".join(d)

	frames = tag.getall("TCON")
	if frames:
		d = []
		for frame in frames:
			for t in frame.text:
				d.append(t)
		if len(d) > 1:
			nt.misc["genres"] = d
		nt.genre = " / ".join(d)

	track_no = natural_get(tags, None, "TRCK", None)
	nt.track_total = ""
	nt.track_number = ""
	if track_no and track_no != "null":
		if "/" in track_no:
			a, b = track_no.split("/")
			nt.track_number = a
			nt.track_total = b
		else:
			nt.track_number = track_no

	disc = natural_get(tags, None, "TPOS", None)  # set ? or ?/?
	nt.disc_total = ""
	nt.disc_number = ""
	if disc:
		if "/" in disc:
			a, b = disc.split("/")
			nt.disc_number = a
			nt.disc_total = b
		else:
			nt.disc_number = disc

	tx = tags.getall("UFID")
	if tx:
		for item in tx:
			if item.owner == "http://musicbrainz.org":
				nt.misc["musicbrainz_recordingid"] = item.data.decode()

	tx = tags.getall("TSOP")
	if tx:
		nt.misc["artist_sort"] = tx[0].text[0]

	tx = tags.getall("TXXX")
	if tx:
		for item in tx:
			if item.desc == "MusicBrainz Release Track Id":
				nt.misc["musicbrainz_trackid"] = item.text[0]
			if item.desc == "MusicBrainz Album Id":
				nt.misc["musicbrainz_albumid"] = item.text[0]
			if item.desc == "MusicBrainz Release Group Id":
				nt.misc["musicbrainz_releasegroupid"] = item.text[0]
			if item.desc == "MusicBrainz Artist Id":
				artist_id_list: list[str] = []
				for uuid in item.text:
					split_uuids = uuid.split("/") # UUIDs can be split by a special character
					for split_uuid in split_uuids:
						artist_id_list.append(split_uuid)
				nt.misc["musicbrainz_artistids"] = artist_id_list

			try:
				desc = item.desc.lower()
				if desc == "replaygain_track_gain":
					nt.misc["replaygain_track_gain"] = float(item.text[0].strip(" dB"))
				if desc == "replaygain_track_peak":
					nt.misc["replaygain_track_peak"] = float(item.text[0])
				if desc == "replaygain_album_gain":
					nt.misc["replaygain_album_gain"] = float(item.text[0].strip(" dB"))
				if desc == "replaygain_album_peak":
					nt.misc["replaygain_album_peak"] = float(item.text[0])
			except Exception:
				logging.exception("Tag Scan: Read Replay Gain MP3 error")
				logging.debug(nt.fullpath)

			if item.desc == "FMPS_RATING":
				nt.misc["FMPS_Rating"] = float(item.text[0])


def scan_ffprobe(nt: TrackClass):
	startupinfo = None
	if system == "Windows" or msys:
		startupinfo = subprocess.STARTUPINFO()
		startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
	try:
		result = subprocess.run(
			[tauon.get_ffprobe(), "-v", "error", "-show_entries", "format=duration", "-of",
			"default=noprint_wrappers=1:nokey=1", nt.fullpath], stdout=subprocess.PIPE, startupinfo=startupinfo, check=True)
		nt.length = float(result.stdout.decode())
	except Exception:
		logging.exception("FFPROBE couldn't supply a duration")
	try:
		result = subprocess.run(
			[tauon.get_ffprobe(), "-v", "error", "-show_entries", "format_tags=title", "-of",
			"default=noprint_wrappers=1:nokey=1", nt.fullpath], stdout=subprocess.PIPE, startupinfo=startupinfo, check=True)
		nt.title = str(result.stdout.decode())
	except Exception:
		logging.exception("FFPROBE couldn't supply a title")
	try:
		result = subprocess.run(
			[tauon.get_ffprobe(), "-v", "error", "-show_entries", "format_tags=artist", "-of",
			"default=noprint_wrappers=1:nokey=1", nt.fullpath], stdout=subprocess.PIPE, startupinfo=startupinfo, check=True)
		nt.artist = str(result.stdout.decode())
	except Exception:
		logging.exception("FFPROBE couldn't supply a artist")
	try:
		result = subprocess.run(
			[tauon.get_ffprobe(), "-v", "error", "-show_entries", "format_tags=album", "-of",
			"default=noprint_wrappers=1:nokey=1", nt.fullpath], stdout=subprocess.PIPE, startupinfo=startupinfo, check=True)
		nt.album = str(result.stdout.decode())
	except Exception:
		logging.exception("FFPROBE couldn't supply a album")
	try:
		result = subprocess.run(
			[tauon.get_ffprobe(), "-v", "error", "-show_entries", "format_tags=date", "-of",
			"default=noprint_wrappers=1:nokey=1", nt.fullpath], stdout=subprocess.PIPE, startupinfo=startupinfo, check=True)
		nt.date = str(result.stdout.decode())
	except Exception:
		logging.exception("FFPROBE couldn't supply a date")
	try:
		result = subprocess.run(
			[tauon.get_ffprobe(), "-v", "error", "-show_entries", "format_tags=track", "-of",
			"default=noprint_wrappers=1:nokey=1", nt.fullpath], stdout=subprocess.PIPE, startupinfo=startupinfo, check=True)
		nt.track_number = str(result.stdout.decode())
	except Exception:
		logging.exception("FFPROBE couldn't supply a track")



def tag_scan(nt: TrackClass) -> TrackClass | None:
	"""This function takes a track object and scans metadata for it. (Filepath needs to be set)"""
	if nt.is_embed_cue:
		return nt
	if nt.is_network or not nt.fullpath:
		return None
	try:
		try:
			nt.modified_time = os.path.getmtime(nt.fullpath)
			nt.found = True
		except FileNotFoundError:
			logging.error("File not found when executing getmtime!")
			nt.found = False
			return nt
		except Exception:
			logging.exception("Unknown error executing getmtime!")
			nt.found = False
			return nt

		nt.misc.clear()

		nt.file_ext = os.path.splitext(os.path.basename(nt.fullpath))[1][1:].upper()

		if nt.file_ext.lower() in GME_Formats and gme:

			emu = ctypes.c_void_p()
			track_info = ctypes.POINTER(GMETrackInfo)()
			err = gme.gme_open_file(nt.fullpath.encode("utf-8"), ctypes.byref(emu), -1)
			#logging.error(err)
			if not err:
				n = nt.subtrack
				err = gme.gme_track_info(emu, byref(track_info), n)
				#logging.error(err)
				if not err:
					nt.length = track_info.contents.play_length / 1000
					nt.title = track_info.contents.song.decode("utf-8")
					nt.artist = track_info.contents.author.decode("utf-8")
					nt.album = track_info.contents.game.decode("utf-8")
					nt.comment = track_info.contents.comment.decode("utf-8")
					gme.gme_free_info(track_info)
				gme.gme_delete(emu)

				filepath = nt.fullpath  # this is the full file path
				filename = nt.filename  # this is the name of the file

				# Get the directory of the file
				dir_path = os.path.dirname(filepath)

				# Loop through all files in the directory to find any matching M3U
				for file in os.listdir(dir_path):
					if file.endswith(".m3u"):
						with open(os.path.join(dir_path, file), encoding="utf-8", errors="replace") as f:
							content = f.read()
							if "�" in content:  # Check for replacement marker
								with open(os.path.join(dir_path, file), encoding="windows-1252") as b:
									content = b.read()
							if "::" in content:
								a, b = content.split("::")
								if a == filename:
									s = re.split(r"(?<!\\),", b)
									try:
										st = int(s[1])
									except Exception:
										logging.exception("Failed to assign st to int")
										continue
									if st == n:
										nt.title = s[2].split(" - ")[0].replace("\\", "")
										nt.artist = s[2].split(" - ")[1].replace("\\", "")
										nt.album = s[2].split(" - ")[2].replace("\\", "")
										nt.length = hms_to_seconds(s[3])
										break
			if not nt.title:
				nt.title = "Track " + str(nt.subtrack + 1)

		elif nt.file_ext in ("MOD", "IT", "XM", "S3M", "MPTM") and mpt:
			with Path(nt.fullpath).open("rb") as file:
				data = file.read()
			MOD1 = MOD.from_address(
				mpt.openmpt_module_create_from_memory(
					ctypes.c_char_p(data), ctypes.c_size_t(len(data)), None, None, None))
			nt.length = mpt.openmpt_module_get_duration_seconds(byref(MOD1))
			nt.title = mpt.openmpt_module_get_metadata(byref(MOD1), ctypes.c_char_p(b"title")).decode()
			nt.artist = mpt.openmpt_module_get_metadata(byref(MOD1), ctypes.c_char_p(b"artist")).decode()
			nt.comment = mpt.openmpt_module_get_metadata(byref(MOD1), ctypes.c_char_p(b"message_raw")).decode()

			mpt.openmpt_module_destroy(byref(MOD1))
			del MOD1

		elif nt.file_ext == "FLAC":
			with Flac(nt.fullpath) as audio:
				audio.read()

				nt.length = audio.length
				nt.title = audio.title
				nt.artist = audio.artist
				nt.album = audio.album
				nt.composer = audio.composer
				nt.date = audio.date
				nt.samplerate = audio.sample_rate
				nt.bit_depth = audio.bit_depth
				nt.size = os.path.getsize(nt.fullpath)
				nt.track_number = audio.track_number
				nt.genre = audio.genre
				nt.album_artist = audio.album_artist
				nt.disc_number = audio.disc_number
				nt.lyrics = audio.lyrics
				if nt.length:
					nt.bitrate = int(nt.size / nt.length * 8 / 1024)
				nt.track_total = audio.track_total
				nt.disc_total = audio.disc_total
				nt.comment = audio.comment
				nt.cue_sheet = audio.cue_sheet
				nt.misc = audio.misc

		elif nt.file_ext == "WAV":
			with Wav(nt.fullpath) as audio:
				try:
					audio.read()

					nt.samplerate = audio.sample_rate
					nt.length = audio.length
					nt.title = audio.title
					nt.artist = audio.artist
					nt.album = audio.album
					nt.track_number = audio.track_number

				except Exception:
					logging.exception("Failed saving WAV file as a Track, will try again differently")
					audio = mutagen.File(nt.fullpath)
					nt.samplerate = audio.info.sample_rate
					nt.bitrate = audio.info.bitrate // 1000
					nt.length = audio.info.length
					nt.size = os.path.getsize(nt.fullpath)
				audio = mutagen.File(nt.fullpath)
				if audio.tags and type(audio.tags) == mutagen.wave._WaveID3:
					use_id3(audio.tags, nt)

		elif nt.file_ext == "OPUS" or nt.file_ext == "OGG" or nt.file_ext == "OGA":

			#logging.info("get opus")
			with Opus(nt.fullpath) as audio:
				audio.read()

				#logging.info(audio.title)

				nt.length = audio.length
				nt.title = audio.title
				nt.artist = audio.artist
				nt.album = audio.album
				nt.composer = audio.composer
				nt.date = audio.date
				nt.samplerate = audio.sample_rate
				nt.size = os.path.getsize(nt.fullpath)
				nt.track_number = audio.track_number
				nt.genre = audio.genre
				nt.album_artist = audio.album_artist
				nt.bitrate = audio.bit_rate
				nt.lyrics = audio.lyrics
				nt.disc_number = audio.disc_number
				nt.track_total = audio.track_total
				nt.disc_total = audio.disc_total
				nt.comment = audio.comment
				nt.misc = audio.misc
				if nt.bitrate == 0 and nt.length > 0:
					nt.bitrate = int(nt.size / nt.length * 8 / 1024)

		elif nt.file_ext == "APE":
			with mutagen.File(nt.fullpath) as audio:
				nt.length = audio.info.length
				nt.bit_depth = audio.info.bits_per_sample
				nt.samplerate = audio.info.sample_rate
				nt.size = os.path.getsize(nt.fullpath)
				if nt.length > 0:
					nt.bitrate = int(nt.size / nt.length * 8 / 1024)

				# # def getter(audio, key, type):
				# #	 if
				# t = audio.tags
				# logging.info(t.keys())
				# nt.size = os.path.getsize(nt.fullpath)
				# nt.title = str(t.get("title", ""))
				# nt.album = str(t.get("album", ""))
				# nt.date = str(t.get("year", ""))
				# nt.disc_number = str(t.get("discnumber", ""))
				# nt.comment = str(t.get("comment", ""))
				# nt.artist = str(t.get("artist", ""))
				# nt.composer = str(t.get("composer", ""))
				# nt.composer = str(t.get("composer", ""))

			with Ape(nt.fullpath) as audio:
				audio.read()

				# logging.info(audio.title)

				# nt.length = audio.length
				nt.title = audio.title
				nt.artist = audio.artist
				nt.album = audio.album
				nt.date = audio.date
				nt.composer = audio.composer
				# nt.bit_depth = audio.bit_depth
				nt.track_number = audio.track_number
				nt.genre = audio.genre
				nt.album_artist = audio.album_artist
				nt.disc_number = audio.disc_number
				nt.lyrics = audio.lyrics
				nt.track_total = audio.track_total
				nt.disc_total = audio.disc_total
				nt.comment = audio.comment
				nt.misc = audio.misc

		elif nt.file_ext == "WV" or nt.file_ext == "TTA":

			with Ape(nt.fullpath) as audio:
				audio.read()

				# logging.info(audio.title)

				nt.length = audio.length
				nt.title = audio.title
				nt.artist = audio.artist
				nt.album = audio.album
				nt.date = audio.date
				nt.composer = audio.composer
				nt.samplerate = audio.sample_rate
				nt.bit_depth = audio.bit_depth
				nt.size = os.path.getsize(nt.fullpath)
				nt.track_number = audio.track_number
				nt.genre = audio.genre
				nt.album_artist = audio.album_artist
				nt.disc_number = audio.disc_number
				nt.lyrics = audio.lyrics
				if nt.length > 0:
					nt.bitrate = int(nt.size / nt.length * 8 / 1024)
				nt.track_total = audio.track_total
				nt.disc_total = audio.disc_total
				nt.comment = audio.comment
				nt.misc = audio.misc

		else:
			# Use MUTAGEN
			try:
				if nt.file_ext.lower() in VID_Formats:
					scan_ffprobe(nt)
					return nt

				try:
					audio = mutagen.File(nt.fullpath)
				except Exception:
					logging.exception("Mutagen scan failed, falling back to FFPROBE")
					scan_ffprobe(nt)
					return nt

				nt.samplerate = audio.info.sample_rate
				nt.bitrate = audio.info.bitrate // 1000
				nt.length = audio.info.length
				nt.size = os.path.getsize(nt.fullpath)

				if not nt.length:
					try:
						startupinfo = None
						if system == "Windows" or msys:
							startupinfo = subprocess.STARTUPINFO()
							startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
						result = subprocess.run([tauon.get_ffprobe(), "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", nt.fullpath], stdout=subprocess.PIPE, startupinfo=startupinfo, check=True)
						nt.length = float(result.stdout.decode())
					except Exception:
						logging.exception("FFPROBE couldn't supply a duration")

				if type(audio.tags) == mutagen.mp4.MP4Tags:
					tags = audio.tags

					def in_get(key, tags):
						if key in tags:
							return tags[key][0]
						return ""

					nt.title = in_get("\xa9nam", tags)
					nt.album = in_get("\xa9alb", tags)
					nt.artist = in_get("\xa9ART", tags)
					nt.album_artist = in_get("aART", tags)
					nt.composer = in_get("\xa9wrt", tags)
					nt.date = in_get("\xa9day", tags)
					nt.comment = in_get("\xa9cmt", tags)
					nt.genre = in_get("\xa9gen", tags)
					if "\xa9lyr" in tags:
						nt.lyrics = in_get("\xa9lyr", tags)
					nt.track_total = ""
					nt.track_number = ""
					t = in_get("trkn", tags)
					if t:
						nt.track_number = str(t[0])
						if t[1]:
							nt.track_total = str(t[1])

					nt.disc_total = ""
					nt.disc_number = ""
					t = in_get("disk", tags)
					if t:
						nt.disc_number = str(t[0])
						if t[1]:
							nt.disc_total = str(t[1])

					if "----:com.apple.iTunes:MusicBrainz Track Id" in tags:
						nt.misc["musicbrainz_recordingid"] = in_get(
							"----:com.apple.iTunes:MusicBrainz Track Id",
							tags).decode()
					if "----:com.apple.iTunes:MusicBrainz Release Track Id" in tags:
						nt.misc["musicbrainz_trackid"] = in_get(
							"----:com.apple.iTunes:MusicBrainz Release Track Id",
							tags).decode()
					if "----:com.apple.iTunes:MusicBrainz Album Id" in tags:
						nt.misc["musicbrainz_albumid"] = in_get(
							"----:com.apple.iTunes:MusicBrainz Album Id",
							tags).decode()
					if "----:com.apple.iTunes:MusicBrainz Release Group Id" in tags:
						nt.misc["musicbrainz_releasegroupid"] = in_get(
							"----:com.apple.iTunes:MusicBrainz Release Group Id",
							tags).decode()
					if "----:com.apple.iTunes:MusicBrainz Artist Id" in tags:
						nt.misc["musicbrainz_artistids"] = [x.decode() for x in
							tags.get("----:com.apple.iTunes:MusicBrainz Artist Id")]


				elif type(audio.tags) == mutagen.id3.ID3:
					use_id3(audio.tags, nt)


			except Exception:
				logging.exception("Failed loading file through Mutagen")
				raise


		# Parse any multiple artists into list
		artists = nt.artist.split(";")
		if len(artists) > 1:
			for a in artists:
				a = a.strip()
				if a:
					if "artists" not in nt.misc:
						nt.misc["artists"] = []
					if a not in nt.misc["artists"]:
						nt.misc["artists"].append(a)


	except Exception:
		try:
			if Exception is UnicodeDecodeError:
				logging.exception("Unicode decode error on file:", nt.fullpath, "\n")
			else:
				logging.exception("Error: Tag read failed on file:", nt.fullpath, "\n")
		except Exception:
			logging.exception("Error printing error. Non utf8 not allowed:", nt.fullpath.encode("utf-8", "surrogateescape").decode("utf-8", "replace"), "\n")
		return nt

	return nt


def get_radio_art() -> None:
	if radiobox.loaded_url in radiobox.websocket_source_urls:
		return
	if "ggdrasil" in radiobox.playing_title:
		time.sleep(3)
		url = "https://yggdrasilradio.net/data.php?"
		response = requests.get(url, timeout=10)
		if response.status_code == 200:
			lines = response.content.decode().split("|")
			if len(lines) > 11 and lines[11]:
				art_id = lines[11].strip().strip("*")
				art_url = "https://yggdrasilradio.net/images/albumart/" + art_id
				art_response = requests.get(art_url, timeout=10)
				if art_response.status_code == 200:
					if pctl.radio_image_bin:
						pctl.radio_image_bin.close()
						pctl.radio_image_bin = None
					pctl.radio_image_bin = io.BytesIO(art_response.content)
					pctl.radio_image_bin.seek(0)
					radiobox.dummy_track.art_url_key = "ok"
			pctl.update_tag_history()

	elif "gensokyoradio.net" in radiobox.loaded_url:

		response = requests.get("https://gensokyoradio.net/api/station/playing/", timeout=10)

		if response.status_code == 200:
			d = json.loads(response.text)
			song_info = d.get("SONGINFO")
			if song_info:
				radiobox.dummy_track.artist = song_info.get("ARTIST", "")
				radiobox.dummy_track.title = song_info.get("TITLE", "")
				radiobox.dummy_track.album = song_info.get("ALBUM", "")

			misc = d.get("MISC")
			if misc:
				art = misc.get("ALBUMART")
				if art:
					art_url = "https://gensokyoradio.net/images/albums/500/" + art
					art_response = requests.get(art_url, timeout=10)
					if art_response.status_code == 200:
						if pctl.radio_image_bin:
							pctl.radio_image_bin.close()
							pctl.radio_image_bin = None
						pctl.radio_image_bin = io.BytesIO(art_response.content)
						pctl.radio_image_bin.seek(0)
						radiobox.dummy_track.art_url_key = "ok"
			pctl.update_tag_history()

	elif "radio.plaza.one" in radiobox.loaded_url:
		time.sleep(3)
		logging.info("Fetching plaza art")
		response = requests.get("https://api.plaza.one/status", timeout=10)
		if response.status_code == 200:
			d = json.loads(response.text)
			if "song" in d:
				tr = d["song"]["length"] - d["song"]["position"]
				tr += 1
				tr = max(tr, 10)
				pctl.radio_poll_timer.force_set(tr * -1)

				if "artist" in d["song"]:
					radiobox.dummy_track.artist = d["song"]["artist"]
				if "title" in d["song"]:
					radiobox.dummy_track.title = d["song"]["title"]
				if "album" in d["song"]:
					radiobox.dummy_track.album = d["song"]["album"]
				if "artwork_src" in d["song"]:
					art_url = d["song"]["artwork_src"]
					art_response = requests.get(art_url, timeout=10)
					if art_response.status_code == 200:
						if pctl.radio_image_bin:
							pctl.radio_image_bin.close()
							pctl.radio_image_bin = None
						pctl.radio_image_bin = io.BytesIO(art_response.content)
						pctl.radio_image_bin.seek(0)
						radiobox.dummy_track.art_url_key = "ok"
				pctl.update_tag_history()

	# Failure
	elif pctl.radio_image_bin:
		pctl.radio_image_bin.close()
		pctl.radio_image_bin = None

	gui.clear_image_cache_next += 1

pctl = PlayerCtl()

notify_change = pctl.notify_change


def auto_name_pl(target_pl: int) -> None:
	if not pctl.multi_playlist[target_pl].playlist_ids:
		return

	albums = []
	artists = []
	parents = []

	track = None

	for index in pctl.multi_playlist[target_pl].playlist_ids:
		track = pctl.get_track(index)
		albums.append(track.album)
		if track.album_artist:
			artists.append(track.album_artist)
		else:
			artists.append(track.artist)
		parents.append(track.parent_folder_path)

	nt = ""
	artist = ""

	if track:
		artist = track.artist
		if track.album_artist:
			artist = track.album_artist

	if track and albums and albums[0] and albums.count(albums[0]) == len(albums):
		nt = artist + " - " + track.album

	elif track and artists and artists[0] and artists.count(artists[0]) == len(artists):
		nt = artists[0]

	else:
		nt = os.path.basename(commonprefix(parents))

	pctl.multi_playlist[target_pl].title = nt


def get_object(index: int) -> TrackClass:
	return pctl.master_library[index]


def update_title_do() -> None:
	if pctl.playing_state > 0:
		if len(pctl.track_queue) > 0:
			line = pctl.master_library[pctl.track_queue[pctl.queue_step]].artist + " - " + \
				pctl.master_library[pctl.track_queue[pctl.queue_step]].title
			# line += "   : :   Tauon Music Box"
			line = line.encode("utf-8")
			SDL_SetWindowTitle(t_window, line)
	else:
		line = "Tauon Music Box"
		line = line.encode("utf-8")
		SDL_SetWindowTitle(t_window, line)


def open_encode_out() -> None:
	if not prefs.encoder_output.exists():
		prefs.encoder_output.mkdir()
	if system == "Windows" or msys:
		line = r"explorer " + prefs.encoder_output.replace("/", "\\")
		subprocess.Popen(line)
	else:
		if macos:
			subprocess.Popen(["open", prefs.encoder_output])
		else:
			subprocess.Popen(["xdg-open", prefs.encoder_output])


def g_open_encode_out(a, b, c) -> None:
	open_encode_out()



if system == "Linux" and not macos and not msys:

	try:
		Notify.init("Tauon Music Box")
		g_tc_notify = Notify.Notification.new(
			"Tauon Music Box",
			"Transcoding has finished.")
		value = GLib.Variant("s", t_id)
		g_tc_notify.set_hint("desktop-entry", value)

		g_tc_notify.add_action(
			"action_click",
			"Open Output Folder",
			g_open_encode_out,
			None,
		)

		de_notify_support = True

	except Exception:
		logging.exception("Failed init notifications")

	if de_notify_support:
		song_notification = Notify.Notification.new("Next track notification")
		value = GLib.Variant("s", t_id)
		song_notification.set_hint("desktop-entry", value)


def notify_song_fire(notification, delay, id) -> None:
	time.sleep(delay)
	notification.show()
	if id is None:
		return

	time.sleep(8)
	if id == gui.notify_main_id:
		notification.close()


def notify_song(notify_of_end: bool = False, delay: float = 0.0) -> None:
	if not de_notify_support:
		return

	if notify_of_end and prefs.end_setting != "stop":
		return

	if prefs.show_notifications and pctl.playing_object() is not None and not window_is_focused():
		if prefs.stop_notifications_mini_mode and gui.mode == 3:
			return

		track = pctl.playing_object()

		if not track or not (track.title or track.artist or track.album or track.filename):
			return  # only display if we have at least one piece of metadata avaliable

		i_path = ""
		try:
			if not notify_of_end:
				i_path = tauon.thumb_tracks.path(track)
		except Exception:
			logging.exception(track.fullpath.encode("utf-8", "replace").decode("utf-8"))
			logging.error("Thumbnail error")

		top_line = track.title

		if prefs.notify_include_album:
			bottom_line = (track.artist + " | " + track.album).strip("| ")
		else:
			bottom_line = track.artist

		if not track.title:
			a, t = filename_to_metadata(clean_string(track.filename))
			if not track.artist:
				bottom_line = a
			top_line = t

		gui.notify_main_id = uid_gen()
		id = gui.notify_main_id

		if notify_of_end:
			bottom_line = "Tauon Music Box"
			top_line = (_("End of playlist"))
			id = None

		song_notification.update(top_line, bottom_line, i_path)

		shoot_dl = threading.Thread(target=notify_song_fire, args=([song_notification, delay, id]))
		shoot_dl.daemon = True
		shoot_dl.start()


# Last.FM -----------------------------------------------------------------


def get_backend_time(path):
	pctl.time_to_get = path

	pctl.playerCommand = "time"
	pctl.playerCommandReady = True

	while pctl.playerCommand != "done":
		time.sleep(0.005)

	return pctl.time_to_get


lastfm = LastFMapi()




lb = ListenBrainz()


def get_love(track_object: TrackClass) -> bool:
	star = star_store.full_get(track_object.index)
	if star is None:
		return False

	if "L" in star[1]:
		return True
	return False


def get_love_index(index: int) -> bool:
	star = star_store.full_get(index)
	if star is None:
		return False

	if "L" in star[1]:
		return True
	return False

def get_love_timestamp_index(index: int):
	star = star_store.full_get(index)
	if star is None:
		return 0
	return star[3]

def love(set=True, track_id=None, no_delay=False, notify=False, sync=True):
	if len(pctl.track_queue) < 1:
		return False

	if track_id is not None and track_id < 0:
		return False

	if track_id is None:
		track_id = pctl.track_queue[pctl.queue_step]

	loved = False
	star = star_store.full_get(track_id)

	if star is not None:
		if "L" in star[1]:
			loved = True

	if set is False:
		return loved

	# global lfm_username
	# if len(lfm_username) > 0 and not lastfm.connected and not prefs.auto_lfm:
	#	 show_message("You have a last.fm account ready but it is not enabled.", 'info',
	#				  'Either connect, enable auto connect, or remove the account.')
	#	 return

	if star is None:
		star = star_store.new_object()

	loved ^= True

	if notify:
		gui.toast_love_object = pctl.get_track(track_id)
		gui.toast_love_added = loved
		toast_love_timer.set()
		gui.delay_frame(1.81)

	delay = 0.3
	if no_delay or not sync or not lastfm.details_ready():
		delay = 0

	star[3] = time.time()

	if loved:
		time.sleep(delay)
		gui.update += 1
		gui.pl_update += 1
		star[1] = star[1] + "L" # = [star[0], star[1] + "L", star[2]]
		star_store.insert(track_id, star)
		if sync:
			if prefs.last_fm_token:
				try:
					lastfm.love(pctl.master_library[track_id].artist, pctl.master_library[track_id].title)
				except Exception:
					logging.exception("Failed updating last.fm love status")
					show_message(_("Failed updating last.fm love status"), mode="warning")
					star[1] = star[1].replace("L", "") # = [star[0], star[1].strip("L"), star[2]]
					star_store.insert(track_id, star)
					show_message(
						_("Error updating love to last.fm!"),
						_("Maybe check your internet connection and try again?"), mode="error")

			if pctl.master_library[track_id].file_ext == "JELY":
				jellyfin.favorite(pctl.master_library[track_id])

	else:
		time.sleep(delay)
		gui.update += 1
		gui.pl_update += 1
		star[1] = star[1].replace("L", "")
		star_store.insert(track_id, star)
		if sync:
			if prefs.last_fm_token:
				try:
					lastfm.unlove(pctl.master_library[track_id].artist, pctl.master_library[track_id].title)
				except Exception:
					logging.exception("Failed updating last.fm love status")
					show_message(_("Failed updating last.fm love status"), mode="warning")
					star[1] = star[1] + "L"
					star_store.insert(track_id, star)
			if pctl.master_library[track_id].file_ext == "JELY":
				jellyfin.favorite(pctl.master_library[track_id], un=True)

	gui.pl_update = 2
	gui.update += 1
	if sync and pctl.mpris is not None:
		pctl.mpris.update(force=True)


def maloja_get_scrobble_counts():
	if lastfm.scanning_scrobbles is True or not prefs.maloja_url:
		return

	url = prefs.maloja_url
	if not url.endswith("/"):
		url += "/"
	url += "apis/mlj_1/scrobbles"
	lastfm.scanning_scrobbles = True
	try:
		r = requests.get(url, timeout=10)

		if r.status_code != 200:
			show_message(_("There was an error with the Maloja server"), r.text, mode="warning")
			lastfm.scanning_scrobbles = False
			return
	except Exception:
		logging.exception("There was an error reaching the Maloja server")
		show_message(_("There was an error reaching the Maloja server"), mode="warning")
		lastfm.scanning_scrobbles = False
		return

	try:
		data = json.loads(r.text)
		l = data["list"]

		counts = {}

		for item in l:
			artists = item.get("artists")
			title = item.get("title")
			if title and artists:
				key = (title, tuple(artists))
				c = counts.get(key, 0)
				counts[key] = c + 1

		touched = []

		for key, value in counts.items():
			title, artists = key
			artists = [x.lower() for x in artists]
			title = title.lower()
			for track in pctl.master_library.values():
				if track.artist.lower() in artists and track.title.lower() == title:
					if track.index in touched:
						track.lfm_scrobbles += value
					else:
						track.lfm_scrobbles = value
						touched.append(track.index)
		show_message(_("Scanning scrobbles complete"), mode="done")

	except Exception:
		logging.exception("There was an error parsing the data")
		show_message(_("There was an error parsing the data"), mode="warning")

	gui.pl_update += 1
	lastfm.scanning_scrobbles = False
	tauon.bg_save()


def maloja_scrobble(track: TrackClass, timestamp: int = int(time.time())) -> bool | None:
	url = prefs.maloja_url

	if not track.artist or not track.title:
		return None

	if not url.endswith("/newscrobble"):
		if not url.endswith("/"):
			url += "/"
		url += "apis/mlj_1/newscrobble"

	d = {}
	d["artists"] = [track.artist] # let Maloja parse/fix artists
	d["title"] = track.title

	if track.album:
		d["album"] = track.album
	if track.album_artist:
		d["albumartists"] = [track.album_artist] # let Maloja parse/fix artists

	d["length"] = int(track.length)
	d["time"] = timestamp
	d["key"] = prefs.maloja_key

	try:
		r = requests.post(url, json=d, timeout=10)
		if r.status_code != 200:
			show_message(_("There was an error submitting data to Maloja server"), r.text, mode="warning")
			return False
	except Exception:
		logging.exception("There was an error submitting data to Maloja server")
		show_message(_("There was an error submitting data to Maloja server"), mode="warning")
		return False
	return True




lfm_scrobbler = LastScrob()

QuickThumbnail.renderer = renderer





strings = Strings()


def id_to_pl(id: int):
	for i, item in enumerate(pctl.multi_playlist):
		if item.uuid_int == id:
			return i
	return None


def pl_to_id(pl: int) -> int:
	return pctl.multi_playlist[pl].uuid_int




def encode_track_name(track_object: TrackClass) -> str:
	if track_object.is_cue or not track_object.filename:
		out_line = str(track_object.track_number) + ". "
		out_line += track_object.artist + " - " + track_object.title
		return filename_safe(out_line)
	return os.path.splitext(track_object.filename)[0]


def encode_folder_name(track_object: TrackClass) -> str:
	folder_name = track_object.artist + " - " + track_object.album

	if folder_name == " - ":
		folder_name = track_object.parent_folder_name

	folder_name = filename_safe(folder_name).strip()

	if not folder_name:
		folder_name = str(track_object.index)

	if "cd" not in folder_name.lower() or "disc" not in folder_name.lower():
		if track_object.disc_total not in ("", "0", 0, "1", 1) or (
				str(track_object.disc_number).isdigit() and int(track_object.disc_number) > 1):
			folder_name += " CD" + str(track_object.disc_number)

	return folder_name


tauon = Tauon()

def signal_handler(signum, frame):
	signal.signal(signum, signal.SIG_IGN) # ignore additional signals
	tauon.exit(reason="SIGINT recieved")

signal.signal(signal.SIGINT, signal_handler)

deco = Deco(tauon)
deco.get_themes = get_themes
deco.renderer = renderer

if prefs.backend != 4:
	prefs.backend = 4

chrome = None

try:
	from tauon.t_modules.t_chrome import Chrome
	chrome = Chrome(tauon)
except ModuleNotFoundError as e:
	logging.debug(f"pychromecast import error: {e}")
	logging.warning("Unable to import Chrome(pychromecast), chromecast support will be disabled.")
except Exception:
	logging.exception("Unknown error trying to import Chrome(pychromecast), chromecast support will be disabled.")
finally:
	logging.debug("Found Chrome(pychromecast) for chromecast support")

tauon.chrome = chrome



plex = PlexService()
tauon.plex = plex

jellyfin = Jellyfin(tauon)
tauon.jellyfin = jellyfin




subsonic = SubsonicService()




koel = KoelService()
tauon.koel = koel




tau = TauService()
tauon.tau = tau


def get_network_thumbnail_url(track_object: TrackClass):
	if track_object.file_ext == "TIDAL":
		return track_object.art_url_key
	if track_object.file_ext == "SPTY":
		return track_object.art_url_key
	if track_object.file_ext == "PLEX":
		url = plex.resolve_thumbnail(track_object.art_url_key)
		assert url is not None
		return url
#	if track_object.file_ext == "JELY":
#		url = jellyfin.resolve_thumbnail(track_object.art_url_key)
#		assert url is not None
#		assert url != ""
#		return url
	if track_object.file_ext == "KOEL":
		url = track_object.art_url_key
		assert url
		return url
	if track_object.file_ext == "TAU":
		url = tau.resolve_picture(track_object.art_url_key)
		assert url
		return url

	return None


def jellyfin_get_playlists_thread() -> None:
	if jellyfin.scanning:
		inp.mouse_click = False
		show_message(_("Job already in progress!"))
		return
	jellyfin.scanning = True
	shoot_dl = threading.Thread(target=jellyfin.get_playlists)
	shoot_dl.daemon = True
	shoot_dl.start()

def jellyfin_get_library_thread() -> None:
	pref_box.close()
	save_prefs()
	if jellyfin.scanning:
		inp.mouse_click = False
		show_message(_("Job already in progress!"))
		return

	jellyfin.scanning = True
	shoot_dl = threading.Thread(target=jellyfin.ingest_library)
	shoot_dl.daemon = True
	shoot_dl.start()


def plex_get_album_thread() -> None:
	pref_box.close()
	save_prefs()
	if plex.scanning:
		inp.mouse_click = False
		show_message(_("Already scanning!"))
		return
	plex.scanning = True

	shoot_dl = threading.Thread(target=plex.get_albums)
	shoot_dl.daemon = True
	shoot_dl.start()


def sub_get_album_thread() -> None:
	# if prefs.backend != 1:
	#	 show_message("This feature is currently only available with the BASS backend")
	#	 return

	pref_box.close()
	save_prefs()
	if subsonic.scanning:
		inp.mouse_click = False
		show_message(_("Already scanning!"))
		return
	subsonic.scanning = True

	shoot_dl = threading.Thread(target=subsonic.get_music3)
	shoot_dl.daemon = True
	shoot_dl.start()


def koel_get_album_thread() -> None:
	# if prefs.backend != 1:
	#	 show_message("This feature is currently only available with the BASS backend")
	#	 return

	pref_box.close()
	save_prefs()
	if koel.scanning:
		inp.mouse_click = False
		show_message(_("Already scanning!"))
		return
	koel.scanning = True

	shoot_dl = threading.Thread(target=koel.get_albums)
	shoot_dl.daemon = True
	shoot_dl.start()


if system == "Windows" or msys:
	from lynxtray import SysTrayIcon




tray = STray()

if system == "Linux" and not macos and not msys:

	gnome = Gnome(tauon)

	try:
		gnomeThread = threading.Thread(target=gnome.main)
		gnomeThread.daemon = True
		gnomeThread.start()
	except Exception:
		logging.exception("Could not start Dbus thread")

if (system == "Windows" or msys):

	tray.start()

	if win_ver < 10:
		logging.warning("Unsupported Windows version older than W10, hooking media keys the old way without SMTC!")
		import keyboard

		def key_callback(event):

			if event.event_type == "down":
				if event.scan_code == -179:
					inp.media_key = "Play"
				elif event.scan_code == -178:
					inp.media_key = "Stop"
				elif event.scan_code == -177:
					inp.media_key = "Previous"
				elif event.scan_code == -176:
					inp.media_key = "Next"
				gui.update += 1
				tauon.wake()

		keyboard.hook_key(-179, key_callback)
		keyboard.hook_key(-178, key_callback)
		keyboard.hook_key(-177, key_callback)
		keyboard.hook_key(-176, key_callback)




stats_gen = GStats()


def do_exit_button() -> None:
	if mouse_up or ab_click:
		if gui.tray_active and prefs.min_to_tray:
			if key_shift_down:
				tauon.exit("User clicked X button with shift key")
				return
			tauon.min_to_tray()
		elif gui.sync_progress and not gui.stop_sync:
			show_message(_("Stop the sync before exiting!"))
		else:
			tauon.exit("User clicked X button")


def do_maximize_button() -> None:
	global mouse_down
	global drag_mode
	if gui.fullscreen:
		gui.fullscreen = False
		SDL_SetWindowFullscreen(t_window, 0)
	elif gui.maximized:
		gui.maximized = False
		SDL_RestoreWindow(t_window)
	else:
		gui.maximized = True
		SDL_MaximizeWindow(t_window)

	mouse_down = False
	inp.mouse_click = False
	drag_mode = False


def do_minimize_button():

	global mouse_down
	global drag_mode
	if macos:
		# hack
		SDL_SetWindowBordered(t_window, True)
		SDL_MinimizeWindow(t_window)
		SDL_SetWindowBordered(t_window, False)
	else:
		SDL_MinimizeWindow(t_window)

	mouse_down = False
	inp.mouse_click = False
	drag_mode = False


mac_circle = asset_loader(scaled_asset_directory, loaded_asset_dc, "macstyle.png", True)


def draw_window_tools():
	global mouse_down
	global drag_mode

	# rect = (window_size[0] - 55 * gui.scale, window_size[1] - 35 * gui.scale, 53 * gui.scale, 33 * gui.scale)
	# fields.add(rect)
	# prefs.left_window_control = not key_shift_down
	macstyle = gui.macstyle

	bg_off = colours.window_buttons_bg
	bg_on = colours.window_buttons_bg_over
	fg_off = colours.window_button_icon_off
	fg_on = colours.window_buttons_icon_over
	x_on = colours.window_button_x_on
	x_off = colours.window_button_x_off

	h = round(28 * gui.scale)
	y = round(1 * gui.scale)
	if macstyle:
		y = round(9 * gui.scale)

	x_width = round(26 * gui.scale)
	ma_width = round(33 * gui.scale)
	mi_width = round(35 * gui.scale)
	re_width = round(30 * gui.scale)
	last_width = 0

	xx = 0
	l = prefs.left_window_control
	r = not l
	focused = window_is_focused()

	# Close
	if r:
		xx = window_size[0] - x_width
		xx -= round(2 * gui.scale)

	if macstyle:
		xx = window_size[0] - 27 * gui.scale
		if l:
			xx = round(4 * gui.scale)
		rect = (xx + 5, y - 1, 14 * gui.scale, 14 * gui.scale)
		fields.add(rect)
		colour = mac_close
		if not focused:
			colour = (86, 85, 86, 255)
		mac_circle.render(xx + 6 * gui.scale, y, colour)
		if coll(rect) and not gui.mouse_unknown:
			if coll_point(last_click_location, rect):
				do_exit_button()
	else:
		rect = (xx, y, x_width, h)
		last_width = x_width
		ddt.rect((rect[0], rect[1], rect[2], rect[3]), bg_off)
		fields.add(rect)
		if coll(rect) and not gui.mouse_unknown:
			ddt.rect((rect[0], rect[1], rect[2], rect[3]), bg_on)
			top_panel.exit_button.render(rect[0] + 8 * gui.scale, rect[1] + 8 * gui.scale, x_on)
			if coll_point(last_click_location, rect):
				do_exit_button()
		else:
			top_panel.exit_button.render(rect[0] + 8 * gui.scale, rect[1] + 8 * gui.scale, x_off)

	# Macstyle restore
	if gui.mode == 3:
		if macstyle:
			if r:
				xx -= round(20 * gui.scale)
			if l:
				xx += round(20 * gui.scale)
			rect = (xx + 5, y - 1, 14 * gui.scale, 14 * gui.scale)

			fields.add(rect)
			colour = (160, 55, 225, 255)
			if not focused:
				colour = (86, 85, 86, 255)
			mac_circle.render(xx + 6 * gui.scale, y, colour)
			if coll(rect) and not gui.mouse_unknown:
				if (mouse_up or ab_click) and coll_point(last_click_location, rect):
					restore_full_mode()
					gui.update += 2

	# maximize

	if draw_max_button and gui.mode != 3:
		if macstyle:
			if r:
				xx -= round(20 * gui.scale)
			if l:
				xx += round(20 * gui.scale)
			rect = (xx + 5, y - 1, 14 * gui.scale, 14 * gui.scale)

			fields.add(rect)
			colour = mac_maximize
			if not focused:
				colour = (86, 85, 86, 255)
			mac_circle.render(xx + 6 * gui.scale, y, colour)
			if coll(rect) and not gui.mouse_unknown:
				if (mouse_up or ab_click) and coll_point(last_click_location, rect):
					do_minimize_button()

		else:
			if r:
				xx -= ma_width
			if l:
				xx += last_width
			rect = (xx, y, ma_width, h)
			last_width = ma_width
			ddt.rect_a((rect[0], rect[1]), (rect[2], rect[3]), bg_off)
			fields.add(rect)
			if coll(rect):
				ddt.rect_a((rect[0], rect[1]), (rect[2], rect[3]), bg_on)
				top_panel.maximize_button.render(rect[0] + 10 * gui.scale, rect[1] + 10 * gui.scale, fg_on)
				if (mouse_up or ab_click) and coll_point(last_click_location, rect):
					do_maximize_button()
			else:
				top_panel.maximize_button.render(rect[0] + 10 * gui.scale, rect[1] + 10 * gui.scale, fg_off)

	# minimize

	if draw_min_button:

		# x = window_size[0] - round(65 * gui.scale)
		# if draw_max_button and not gui.mode == 3:
		#	 x -= round(34 * gui.scale)
		if macstyle:
			if r:
				xx -= round(20 * gui.scale)
			if l:
				xx += round(20 * gui.scale)
			rect = (xx + 5, y - 1, 14 * gui.scale, 14 * gui.scale)

			fields.add(rect)
			colour = mac_minimize
			if not focused:
				colour = (86, 85, 86, 255)
			mac_circle.render(xx + 6 * gui.scale, y, colour)
			if coll(rect) and not gui.mouse_unknown:
				if (mouse_up or ab_click) and coll_point(last_click_location, rect):
					do_maximize_button()

		else:
			if r:
				xx -= mi_width
			if l:
				xx += last_width

			rect = (xx, y, mi_width, h)
			last_width = mi_width
			ddt.rect_a((rect[0], rect[1]), (rect[2], rect[3]), bg_off)
			fields.add(rect)
			if coll(rect):
				ddt.rect_a((rect[0], rect[1]), (rect[2], rect[3]), bg_on)
				ddt.rect_a((rect[0] + 11 * gui.scale, rect[1] + 16 * gui.scale), (14 * gui.scale, 3 * gui.scale), fg_on)
				if (mouse_up or ab_click) and coll_point(last_click_location, rect):
					do_minimize_button()
			else:
				ddt.rect_a(
					(rect[0] + 11 * gui.scale, rect[1] + 16 * gui.scale), (14 * gui.scale, 3 * gui.scale), fg_off)

	# restore

	if gui.mode == 3:

		# bg_off = [0, 0, 0, 50]
		# bg_on = [255, 255, 255, 10]
		# fg_off =(255, 255, 255, 40)
		# fg_on = (255, 255, 255, 60)
		if macstyle:
			pass
		else:
			if r:
				xx -= re_width
			if l:
				xx += last_width

			rect = (xx, y, re_width, h)
			ddt.rect_a((rect[0], rect[1]), (rect[2], rect[3]), bg_off)
			fields.add(rect)
			if coll(rect):
				ddt.rect_a((rect[0], rect[1]), (rect[2], rect[3]), bg_on)
				top_panel.restore_button.render(rect[0] + 8 * gui.scale, rect[1] + 9 * gui.scale, fg_on)
				if (inp.mouse_click or ab_click) and coll_point(click_location, rect):
					restore_full_mode()
					gui.update += 2
			else:
				top_panel.restore_button.render(rect[0] + 8 * gui.scale, rect[1] + 9 * gui.scale, fg_off)


def draw_window_border():
	corner_icon.render(window_size[0] - corner_icon.w, window_size[1] - corner_icon.h, colours.corner_icon)

	corner_rect = (window_size[0] - 20 * gui.scale, window_size[1] - 20 * gui.scale, 20, 20)
	fields.add(corner_rect)

	right_rect = (window_size[0] - 3 * gui.scale, 20 * gui.scale, 10, window_size[1] - 40 * gui.scale)
	fields.add(right_rect)

	# top_rect = (20 * gui.scale, 0, window_size[0] - 40 * gui.scale, 2 * gui.scale)
	# fields.add(top_rect)

	left_rect = (0, 10 * gui.scale, 4 * gui.scale, window_size[1] - 50 * gui.scale)
	fields.add(left_rect)

	bottom_rect = (20 * gui.scale, window_size[1] - 4, window_size[0] - 40 * gui.scale, 7 * gui.scale)
	fields.add(bottom_rect)

	if coll(corner_rect):
		gui.cursor_want = 4
	elif coll(right_rect):
		gui.cursor_want = 8
	# elif coll(top_rect):
	#	 gui.cursor_want = 9
	elif coll(left_rect):
		gui.cursor_want = 10
	elif coll(bottom_rect):
		gui.cursor_want = 11

	colour = colours.window_frame

	ddt.rect((0, 0, window_size[0], 1 * gui.scale), colour)
	ddt.rect((0, 0, 1 * gui.scale, window_size[1]), colour)
	ddt.rect((0, window_size[1] - 1 * gui.scale, window_size[0], 1 * gui.scale), colour)
	ddt.rect((window_size[0] - 1 * gui.scale, 0, 1 * gui.scale, window_size[1]), colour)


# -------------------------------------------------------------------------------------------
# initiate SDL2 --------------------------------------------------------------------C-IS-----

cursor_hand = SDL_CreateSystemCursor(SDL_SYSTEM_CURSOR_HAND)
cursor_standard = SDL_CreateSystemCursor(SDL_SYSTEM_CURSOR_ARROW)
cursor_shift = SDL_CreateSystemCursor(SDL_SYSTEM_CURSOR_SIZEWE)
cursor_text = SDL_CreateSystemCursor(SDL_SYSTEM_CURSOR_IBEAM)

cursor_br_corner = cursor_standard
cursor_right_side = cursor_standard
cursor_top_side = cursor_standard
cursor_left_side = cursor_standard
cursor_bottom_side = cursor_standard

if msys:
	cursor_br_corner = SDL_CreateSystemCursor(SDL_SYSTEM_CURSOR_SIZENWSE)
	cursor_right_side = cursor_shift
	cursor_left_side = cursor_shift
	cursor_top_side = SDL_CreateSystemCursor(SDL_SYSTEM_CURSOR_SIZENS)
	cursor_bottom_side = cursor_top_side
elif not msys and system == "Linux" and "XCURSOR_THEME" in os.environ and "XCURSOR_SIZE" in os.environ:
	try:
		class XcursorImage(ctypes.Structure):
			_fields_ = [
					("version", c_uint32),
					("size", c_uint32),
					("width", c_uint32),
					("height", c_uint32),
					("xhot", c_uint32),
					("yhot", c_uint32),
					("delay", c_uint32),
					("pixels", c_void_p),
				]

		try:
			xcu = ctypes.cdll.LoadLibrary("libXcursor.so")
		except Exception:
			logging.exception("Failed to load libXcursor.so, will try libXcursor.so.1")
			xcu = ctypes.cdll.LoadLibrary("libXcursor.so.1")
		xcu.XcursorLibraryLoadImage.restype = ctypes.POINTER(XcursorImage)

		def get_xcursor(name: str):
			if "XCURSOR_THEME" not in os.environ:
				raise ValueError("Missing XCURSOR_THEME in env")
			if "XCURSOR_SIZE" not in os.environ:
				raise ValueError("Missing XCURSOR_SIZE in env")
			xcursor_theme = os.environ["XCURSOR_THEME"]
			xcursor_size = os.environ["XCURSOR_SIZE"]
			c1 = xcu.XcursorLibraryLoadImage(c_char_p(name.encode()), c_char_p(xcursor_theme.encode()), c_int(int(xcursor_size))).contents
			sdl_surface = SDL_CreateRGBSurfaceWithFormatFrom(c1.pixels, c1.width, c1.height, 32, c1.width * 4, SDL_PIXELFORMAT_ARGB8888)
			cursor = SDL_CreateColorCursor(sdl_surface, round(c1.xhot), round(c1.yhot))
			xcu.XcursorImageDestroy(ctypes.byref(c1))
			SDL_FreeSurface(sdl_surface)
			return cursor

		cursor_br_corner = get_xcursor("se-resize")
		cursor_right_side = get_xcursor("right_side")
		cursor_top_side = get_xcursor("top_side")
		cursor_left_side = get_xcursor("left_side")
		cursor_bottom_side = get_xcursor("bottom_side")

		if SDL_GetCurrentVideoDriver() == b"wayland":
			cursor_standard = get_xcursor("left_ptr")
			cursor_text = get_xcursor("xterm")
			cursor_shift = get_xcursor("sb_h_double_arrow")
			cursor_hand = get_xcursor("hand2")
			SDL_SetCursor(cursor_standard)

	except Exception:
		logging.exception("Error loading xcursor")


if not maximized and gui.maximized:
	SDL_MaximizeWindow(t_window)

# logging.error(SDL_GetError())

# t_window = SDL_CreateShapedWindow(
# window_title,
#	SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
#	window_size[0], window_size[1],
#	flags)

# logging.error(SDL_GetError())

if system == "Windows" or msys:
	gui.window_id = sss.info.win.window


# try:
#	 SDL_SetHint(SDL_HINT_MOUSE_FOCUS_CLICKTHROUGH, b"1")
#
# except Exception:
#	 logging.exception("old version of SDL detected")

# get window surface and set up renderer
# renderer = SDL_CreateRenderer(t_window, 0, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)

# renderer = SDL_CreateRenderer(t_window, 0, SDL_RENDERER_ACCELERATED)
#
# # window_surface = SDL_GetWindowSurface(t_window)
#
# SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND)
#
# display_index = SDL_GetWindowDisplayIndex(t_window)
# display_bounds = SDL_Rect(0, 0)
# SDL_GetDisplayBounds(display_index, display_bounds)
#
# icon = IMG_Load(os.path.join(asset_directory, "icon-64.png").encode())
# SDL_SetWindowIcon(t_window, icon)
# SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "best".encode())
#
# SDL_SetWindowMinimumSize(t_window, round(560 * gui.scale), round(330 * gui.scale))
#
#
# gui.max_window_tex = 1000
# if window_size[0] > gui.max_window_tex or window_size[1] > gui.max_window_tex:
#
#	 while window_size[0] > gui.max_window_tex:
#		 gui.max_window_tex += 1000
#	 while window_size[1] > gui.max_window_tex:
#		 gui.max_window_tex += 1000
#
# gui.ttext = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, gui.max_window_tex, gui.max_window_tex)
#
# # gui.pl_surf = SDL_CreateRGBSurfaceWithFormat(0, gui.max_window_tex, gui.max_window_tex, 32, SDL_PIXELFORMAT_RGB888)
#
# SDL_SetTextureBlendMode(gui.ttext, SDL_BLENDMODE_BLEND)
#
# gui.spec2_tex = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, gui.spec2_w, gui.spec2_y)
# gui.spec1_tex = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, gui.spec_w, gui.spec_h)
# gui.spec4_tex = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, gui.spec4_w, gui.spec4_h)
# gui.spec_level_tex = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, gui.level_ww, gui.level_hh)
#
# SDL_SetTextureBlendMode(gui.spec4_tex, SDL_BLENDMODE_BLEND)
#
# SDL_SetRenderTarget(renderer, None)
#
# gui.main_texture = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, gui.max_window_tex, gui.max_window_tex)
# gui.main_texture_overlay_temp = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, gui.max_window_tex, gui.max_window_tex)
#
# SDL_SetRenderTarget(renderer, gui.main_texture)
# SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
#
# SDL_SetRenderTarget(renderer, gui.main_texture_overlay_temp)
# SDL_SetTextureBlendMode(gui.main_texture_overlay_temp, SDL_BLENDMODE_BLEND)
# SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
#
# SDL_RenderClear(renderer)
#
# gui.abc = SDL_Rect(0, 0, gui.max_window_tex, gui.max_window_tex)
# gui.pl_update = 2
#
# SDL_SetWindowOpacity(t_window, prefs.window_opacity)

# gui.spec1_tex = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, gui.spec_w, gui.spec_h)
# gui.spec4_tex = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, gui.spec4_w, gui.spec4_h)
# gui.spec_level_tex = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, gui.level_ww, gui.level_hh)
# SDL_SetTextureBlendMode(gui.spec4_tex, SDL_BLENDMODE_BLEND)


def bass_player_thread(player):
	# logging.basicConfig(filename=user_directory + '/crash.log', level=logging.ERROR,
	#					 format='%(asctime)s %(levelname)s %(name)s %(message)s')

	try:
		player(pctl, gui, prefs, lfm_scrobbler, star_store, tauon)
	except Exception:
		logging.exception("Exception on player thread")
		show_message(_("Playback thread has crashed. Sorry about that."), _("App will need to be restarted."), mode="error")
		time.sleep(1)
		show_message(_("Playback thread has crashed. Sorry about that."), _("App will need to be restarted."), mode="error")
		time.sleep(1)
		show_message(_("Playback thread has crashed. Sorry about that."), _("App will need to be restarted."), mode="error")
		raise


if (system == "Windows" or msys) and taskbar_progress:

	class WinTask:

		def __init__(self):
			self.start = time.time()
			self.updated_state = 0
			self.window_id = gui.window_id
			import comtypes.client as cc
			cc.GetModule(str(install_directory / "TaskbarLib.tlb"))
			import comtypes.gen.TaskbarLib as tbl
			self.taskbar = cc.CreateObject(
				"{56FDF344-FD6D-11d0-958A-006097C9A090}",
				interface=tbl.ITaskbarList3)
			self.taskbar.HrInit()

			self.d_timer = Timer()

		def update(self, force=False):
			if self.d_timer.get() > 2 or force:
				self.d_timer.set()

				if pctl.playing_state == 1 and self.updated_state != 1:
					self.taskbar.SetProgressState(self.window_id, 0x2)

				if pctl.playing_state == 1:
					self.updated_state = 1
					if pctl.playing_length > 2:
						perc = int(pctl.playing_time * 100 / int(pctl.playing_length))
						if perc < 2:
							perc = 1
						elif perc > 100:
							prec = 100
					else:
						perc = 0

					self.taskbar.SetProgressValue(self.window_id, perc, 100)

				elif pctl.playing_state == 2 and self.updated_state != 2:
					self.updated_state = 2
					self.taskbar.SetProgressState(self.window_id, 0x8)

				elif pctl.playing_state == 0 and self.updated_state != 0:
					self.updated_state = 0
					self.taskbar.SetProgressState(self.window_id, 0x2)
					self.taskbar.SetProgressValue(self.window_id, 0, 100)


	if (install_directory / "TaskbarLib.tlb").is_file():
		logging.info("Taskbar progress enabled")
		pctl.windows_progress = WinTask()

	else:
		pctl.taskbar_progress = False
		logging.warning("Could not find TaskbarLib.tlb")


# ---------------------------------------------------------------------------------------------
# ABSTRACT SDL DRAWING FUNCTIONS -----------------------------------------------------


def coll_point(l, r):
	# rect point collision detection
	return r[0] < l[0] <= r[0] + r[2] and r[1] <= l[1] <= r[1] + r[3]


def coll(r):
	return r[0] < mouse_position[0] <= r[0] + r[2] and r[1] <= mouse_position[1] <= r[1] + r[3]


ddt = TDraw(renderer)
ddt.scale = gui.scale
ddt.force_subpixel_text = prefs.force_subpixel_text

launch = Launch(tauon, pctl, gui, ddt)




draw = Drawing()


def prime_fonts():
	standard_font = prefs.linux_font
	# if msys:
	#	 standard_font = prefs.linux_font + ", Sans"  # The CJK ones dont appear to be working
	ddt.prime_font(standard_font, 8, 9)
	ddt.prime_font(standard_font, 8, 10)
	ddt.prime_font(standard_font, 8.5, 11)
	ddt.prime_font(standard_font, 8.7, 11.5)
	ddt.prime_font(standard_font, 9, 12)
	ddt.prime_font(standard_font, 10, 13)
	ddt.prime_font(standard_font, 10, 14)
	ddt.prime_font(standard_font, 10.2, 14.5)
	ddt.prime_font(standard_font, 11, 15)
	ddt.prime_font(standard_font, 12, 16)
	ddt.prime_font(standard_font, 12, 17)
	ddt.prime_font(standard_font, 12, 18)
	ddt.prime_font(standard_font, 13, 19)
	ddt.prime_font(standard_font, 14, 20)
	ddt.prime_font(standard_font, 24, 30)

	ddt.prime_font(standard_font, 9, 412)
	ddt.prime_font(standard_font, 10, 413)

	standard_font = prefs.linux_font_semibold
	# if msys:
	#	 standard_font = prefs.linux_font_semibold + ", Noto Sans Med, Sans" #, Noto Sans CJK JP Medium, Noto Sans CJK Medium, Sans"

	ddt.prime_font(standard_font, 8, 309)
	ddt.prime_font(standard_font, 8, 310)
	ddt.prime_font(standard_font, 8.5, 311)
	ddt.prime_font(standard_font, 9, 312)
	ddt.prime_font(standard_font, 10, 313)
	ddt.prime_font(standard_font, 10.5, 314)
	ddt.prime_font(standard_font, 11, 315)
	ddt.prime_font(standard_font, 12, 316)
	ddt.prime_font(standard_font, 12, 317)
	ddt.prime_font(standard_font, 12, 318)
	ddt.prime_font(standard_font, 13, 319)
	ddt.prime_font(standard_font, 24, 330)

	standard_font = prefs.linux_font_bold
	# if msys:
	#	 standard_font = prefs.linux_font_bold + ", Noto Sans, Sans Bold"

	ddt.prime_font(standard_font, 6, 209)
	ddt.prime_font(standard_font, 7, 210)
	ddt.prime_font(standard_font, 8, 211)
	ddt.prime_font(standard_font, 9, 212)
	ddt.prime_font(standard_font, 10, 213)
	ddt.prime_font(standard_font, 11, 214)
	ddt.prime_font(standard_font, 12, 215)
	ddt.prime_font(standard_font, 13, 216)
	ddt.prime_font(standard_font, 14, 217)
	ddt.prime_font(standard_font, 17, 218)
	ddt.prime_font(standard_font, 19, 219)
	ddt.prime_font(standard_font, 20, 220)
	ddt.prime_font(standard_font, 25, 228)

	standard_font = prefs.linux_font_condensed
	# if msys:
	#	 standard_font = "Noto Sans ExtCond, Sans"
	ddt.prime_font(standard_font, 10, 413)
	ddt.prime_font(standard_font, 11, 414)
	ddt.prime_font(standard_font, 12, 415)
	ddt.prime_font(standard_font, 13, 416)

	standard_font = prefs.linux_font_condensed_bold  # "Noto Sans, ExtraCondensed Bold"
	# if msys:
	#	 standard_font = "Noto Sans ExtCond, Sans Bold"
	# ddt.prime_font(standard_font, 9, 512)
	ddt.prime_font(standard_font, 10, 513)
	ddt.prime_font(standard_font, 11, 514)
	ddt.prime_font(standard_font, 12, 515)
	ddt.prime_font(standard_font, 13, 516)


if system == "Linux":
	prime_fonts()

else:
	# standard_font = "Meiryo"
	standard_font = "Arial"
	# semibold_font = "Meiryo Semibold"
	semibold_font = "Arial Bold"
	standard_weight = 500
	bold_weight = 600
	ddt.win_prime_font(standard_font, 14, 10, weight=standard_weight, y_offset=0)
	ddt.win_prime_font(standard_font, 15, 11, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 15, 11.5, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 15, 12, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 15, 13, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 16, 14, weight=standard_weight, y_offset=0)
	ddt.win_prime_font(standard_font, 16, 14.5, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 17, 15, weight=standard_weight, y_offset=-1)
	ddt.win_prime_font(standard_font, 20, 16, weight=standard_weight, y_offset=-2)
	ddt.win_prime_font(standard_font, 20, 17, weight=standard_weight, y_offset=-1)

	ddt.win_prime_font(standard_font, 30 + 4, 30, weight=standard_weight, y_offset=-12)
	ddt.win_prime_font(semibold_font, 9, 209, weight=bold_weight, y_offset=1)
	ddt.win_prime_font("Arial", 10 + 4, 210, weight=600, y_offset=2)
	ddt.win_prime_font("Arial", 11 + 3, 211, weight=600, y_offset=2)
	ddt.win_prime_font(semibold_font, 12 + 4, 212, weight=bold_weight, y_offset=1)
	ddt.win_prime_font(semibold_font, 13 + 3, 213, weight=bold_weight, y_offset=-1)
	ddt.win_prime_font(semibold_font, 14 + 2, 214, weight=bold_weight, y_offset=1)
	ddt.win_prime_font(semibold_font, 15 + 2, 215, weight=bold_weight, y_offset=1)
	ddt.win_prime_font(semibold_font, 16 + 2, 216, weight=bold_weight, y_offset=1)
	ddt.win_prime_font(semibold_font, 17 + 2, 218, weight=bold_weight, y_offset=1)
	ddt.win_prime_font(semibold_font, 18 + 2, 218, weight=bold_weight, y_offset=1)
	ddt.win_prime_font(semibold_font, 19 + 2, 220, weight=bold_weight, y_offset=1)
	ddt.win_prime_font(semibold_font, 28 + 2, 228, weight=bold_weight, y_offset=1)

	standard_weight = 550
	ddt.win_prime_font(standard_font, 14, 310, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 15, 311, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 16, 312, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 17, 313, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 18, 314, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 19, 315, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 20, 316, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 21, 317, weight=standard_weight, y_offset=1)

	standard_font = "Arial Narrow"
	standard_weight = 500

	ddt.win_prime_font(standard_font, 14, 410, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 15, 411, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 16, 412, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 17, 413, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 18, 414, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 19, 415, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 20, 416, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 21, 417, weight=standard_weight, y_offset=1)

	standard_weight = 600

	ddt.win_prime_font(standard_font, 14, 510, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 15, 511, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 16, 512, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 17, 513, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 18, 514, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 19, 515, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 20, 516, weight=standard_weight, y_offset=1)
	ddt.win_prime_font(standard_font, 21, 517, weight=standard_weight, y_offset=1)




drop_shadow = DropShadow()




lyrics_ren_mini = LyricsRenMini()




lyrics_ren = LyricsRen()


def find_synced_lyric_data(track: TrackClass) -> list[str] | None:
	if track.is_network:
		return None

	direc = track.parent_folder_path
	name = os.path.splitext(track.filename)[0] + ".lrc"

	if len(track.lyrics) > 20 and track.lyrics[0] == "[" and ":" in track.lyrics[:20] and "." in track.lyrics[:20]:
		return track.lyrics.splitlines()

	try:
		if os.path.isfile(os.path.join(direc, name)):
			with open(os.path.join(direc, name), encoding="utf-8") as f:
				data = f.readlines()
		else:
			return None
	except Exception:
		logging.exception("Read lyrics file error")
		return None

	return data




tauon.synced_to_static_lyrics = TimedLyricsToStatic()


def get_real_time():
	offset = pctl.decode_time - (prefs.sync_lyrics_time_offset / 1000)
	if prefs.backend == 4:
		offset -= (prefs.device_buffer - 120) / 1000
	elif prefs.backend == 2:
		offset += 0.1
	return max(0, offset)



timed_lyrics_ren = TimedLyricsRen()


def draw_internel_link(x, y, text, colour, font):
	tweak = font
	while tweak > 100:
		tweak -= 100

	if gui.scale == 2:
		tweak *= 2
		tweak += 4
	if gui.scale == 1.25:
		tweak = round(tweak * 1.25)
		tweak += 1

	sp = ddt.text((x, y), text, colour, font)

	rect = [x - 5 * gui.scale, y - 2 * gui.scale, sp + 11 * gui.scale, 23 * gui.scale]
	fields.add(rect)

	if coll(rect):
		if not inp.mouse_click:
			gui.cursor_want = 3
		ddt.line(x, y + tweak + 2, x + sp, y + tweak + 2, alpha_mod(colour, 180))
		if inp.mouse_click:
			return True
	return False


# No hit detect
def draw_linked_text(location, text, colour, font, force=False, replace=""):
	base = ""
	link_text = ""
	rest = ""
	on_base = True

	if force:
		on_base = False
		base = ""
		link_text = text
		rest = ""
	else:
		for i in range(len(text)):
			if text[i:i + 7] == "http://" or text[i:i + 4] == "www." or text[i:i + 8] == "https://":
				on_base = False
			if on_base:
				base += text[i]
			elif i == len(text) or text[i] in '\\) "\'':
				rest = text[i:]
				break
			else:
				link_text += text[i]

	target_link = link_text
	if replace:
		link_text = replace

	left = ddt.get_text_w(base, font)
	right = ddt.get_text_w(base + link_text, font)

	x = location[0]
	y = location[1]

	ddt.text((x, y), base, colour, font)
	ddt.text((x + left, y), link_text, colours.link_text, font)
	ddt.text((x + right, y), rest, colour, font)

	tweak = font
	while tweak > 100:
		tweak -= 100

	if gui.scale == 2:
		tweak *= 2
		tweak += 4
	elif gui.scale != 1:
		tweak = round(tweak * gui.scale)
		tweak += 2

	if system == "Windows":
		tweak += 1

	# ddt.line(x + left, y + tweak + 2, x + right, y + tweak + 2, alpha_mod(colours.link_text, 120))
	ddt.rect((x + left, y + tweak + 2, right - left, round(1 * gui.scale)), alpha_mod(colours.link_text, 120))

	return left, right - left, target_link


def draw_linked_text2(x, y, text, colour, font, click=False, replace=""):
	link_pa = draw_linked_text(
		(x, y), text, colour, font, replace=replace)
	link_rect = [x + link_pa[0], y, link_pa[1], 18 * gui.scale]
	if coll(link_rect):
		if not click:
			gui.cursor_want = 3
		if click:
			webbrowser.open(link_pa[2], new=2, autoraise=True)
	fields.add(link_rect)


def link_activate(x, y, link_pa, click=None):
	link_rect = [x + link_pa[0], y - 2 * gui.scale, link_pa[1], 20 * gui.scale]

	if click is None:
		click = inp.mouse_click

	fields.add(link_rect)
	if coll(link_rect):
		if not click:
			gui.cursor_want = 3
		if click:
			webbrowser.open(link_pa[2], new=2, autoraise=True)
			track_box = True


text_box_canvas_rect = SDL_Rect(0, 0, round(2000 * gui.scale), round(40 * gui.scale))
text_box_canvas_hide_rect = SDL_Rect(0, 0, round(2000 * gui.scale), round(40 * gui.scale))
text_box_canvas = SDL_CreateTexture(
	renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, text_box_canvas_rect.w, text_box_canvas_rect.h)
SDL_SetTextureBlendMode(text_box_canvas, SDL_BLENDMODE_BLEND)


def pixel_to_logical(x):
	return round((x / window_size[0]) * logical_size[0])





rename_text_area = TextBox()
gst_output_field = TextBox2()
gst_output_field.text = prefs.gst_output
search_text = TextBox()
rename_files = TextBox2()
sub_lyrics_a = TextBox2()
sub_lyrics_b = TextBox2()
sync_target = TextBox2()
edit_artist = TextBox2()
edit_album = TextBox2()
edit_title = TextBox2()
edit_album_artist = TextBox2()

rename_files.text = prefs.rename_tracks_template
if rename_files_previous:
	rename_files.text = rename_files_previous

text_plex_usr = TextBox2()
text_plex_pas = TextBox2()
text_plex_ser = TextBox2()

text_jelly_usr = TextBox2()
text_jelly_pas = TextBox2()
text_jelly_ser = TextBox2()

text_koel_usr = TextBox2()
text_koel_pas = TextBox2()
text_koel_ser = TextBox2()

text_air_usr = TextBox2()
text_air_pas = TextBox2()
text_air_ser = TextBox2()

text_spot_client = TextBox2()
text_spot_secret = TextBox2()
text_spot_username = TextBox2()
text_spot_password = TextBox2()

text_maloja_url = TextBox2()
text_maloja_key = TextBox2()

text_sat_url = TextBox2()
text_sat_playlist = TextBox2()

rename_folder = TextBox2()
rename_folder.text = prefs.rename_folder_template
if rename_folder_previous:
	rename_folder.text = rename_folder_previous

temp_dest = SDL_Rect(0, 0)

def img_slide_update_gall(value, pause: bool = True) -> None:
	global album_mode_art_size
	gui.halt_image_rendering = True

	album_mode_art_size = value

	clear_img_cache(False)
	if pause:
		gallery_load_delay.set()
		gui.frame_callback_list.append(TestTimer(0.6))
	gui.halt_image_rendering = False

	# Update sizes
	tauon.gall_ren.size = album_mode_art_size

	if album_mode_art_size > 150:
		prefs.thin_gallery_borders = False


def clear_img_cache(delete_disk: bool = True) -> None:
	global album_art_gen
	album_art_gen.clear_cache()
	prefs.failed_artists.clear()
	prefs.failed_background_artists.clear()
	tauon.gall_ren.key_list = []

	i = 0
	while len(tauon.gall_ren.queue) > 0:
		time.sleep(0.01)
		i += 1
		if i > 5 / 0.01:
			break

	for key, value in tauon.gall_ren.gall.items():
		SDL_DestroyTexture(value[2])
	tauon.gall_ren.gall = {}

	if delete_disk:
		dirs = [g_cache_dir, n_cache_dir, e_cache_dir]
		for direc in dirs:
			if os.path.isdir(direc):
				for item in os.listdir(direc):
					path = os.path.join(direc, item)
					os.remove(path)

	prefs.failed_artists.clear()
	for key, value in artist_list_box.thumb_cache.items():
		if value:
			SDL_DestroyTexture(value[0])
	artist_list_box.thumb_cache.clear()
	gui.update += 1


def clear_track_image_cache(track: TrackClass):
	gui.halt_image_rendering = True
	if tauon.gall_ren.queue:
		time.sleep(0.05)
	if tauon.gall_ren.queue:
		time.sleep(0.2)
	if tauon.gall_ren.queue:
		time.sleep(0.5)

	direc = os.path.join(g_cache_dir)
	if os.path.isdir(direc):
		for item in os.listdir(direc):
			n = item.split("-")
			if len(n) > 2 and n[2] == str(track.index):
				os.remove(os.path.join(direc, item))
				logging.info("Cleared cache thumbnail: " + os.path.join(direc, item))

	keys = set()
	for key, value in tauon.gall_ren.gall.items():
		if key[0] == track:
			SDL_DestroyTexture(value[2])
			if key not in keys:
				keys.add(key)
	for key in keys:
		del tauon.gall_ren.gall[key]
		if key in tauon.gall_ren.key_list:
			tauon.gall_ren.key_list.remove(key)

	gui.halt_image_rendering = False
	album_art_gen.clear_cache()






album_art_gen = AlbumArt()


# 0 - blank
# 1 - preparing first
# 2 - render first
# 3 - preparing 2nd



style_overlay = StyleOverlay()


def trunc_line(line: str, font: str, px: int, dots: bool = True) -> str:
	"""This old function is slow and should be avoided"""
	if ddt.get_text_w(line, font) < px + 10:
		return line

	if dots:
		while ddt.get_text_w(line.rstrip(" ") + gui.trunk_end, font) > px:
			if len(line) == 0:
				return gui.trunk_end
			line = line[:-1]
		return line.rstrip(" ") + gui.trunk_end

	while ddt.get_text_w(line, font) > px:

		line = line[:-1]
		if len(line) < 2:
			break

	return line


def right_trunc(line: str, font: str, px: int, dots: bool = True) -> str:
	if ddt.get_text_w(line, font) < px + 10:
		return line

	if dots:
		while ddt.get_text_w(line.rstrip(" ") + gui.trunk_end, font) > px:
			if len(line) == 0:
				return gui.trunk_end
			line = line[1:]
		return gui.trunk_end + line.rstrip(" ")

	while ddt.get_text_w(line, font) > px:
		# trunk = True
		line = line[1:]
		if len(line) < 2:
			break
	# if trunk and dots:
	#	 line = line.rstrip(" ") + gui.trunk_end
	return line


# def trunc_line2(line, font, px):
#	 trunk = False
#	 p = ddt.get_text_w(line, font)
#	 if p == 0 or p < px + 15:
#		 return line
#
#	 tl = line[0:(int(px / p * len(line)) + 3)]
#
#	 if ddt.get_text_w(line.rstrip(" ") + gui.trunk_end, font) > px:
#		 line = tl
#
#	 while ddt.get_text_w(line.rstrip(" ") + gui.trunk_end, font) > px + 10:
#		 trunk = True
#		 line = line[:-1]
#		 if len(line) < 1:
#			 break
#
#	 return line.rstrip(" ") + gui.trunk_end


click_time = time.time()
scroll_hold = False
scroll_point = 0
scroll_bpoint = 0
sbl = 50
sbp = 100

asbp = 50
album_scroll_hold = False


def fix_encoding(index, mode, enc):
	global default_playlist
	global enc_field

	todo = []

	if mode == 1:
		todo = [index]
	elif mode == 0:
		for b in range(len(default_playlist)):
			if pctl.master_library[default_playlist[b]].parent_folder_name == pctl.master_library[
				index].parent_folder_name:
				todo.append(default_playlist[b])

	for q in range(len(todo)):

		# key = pctl.master_library[todo[q]].title + pctl.master_library[todo[q]].filename
		old_star = star_store.full_get(todo[q])
		if old_star != None:
			star_store.remove(todo[q])

		if enc_field == "All" or enc_field == "Artist":
			line = pctl.master_library[todo[q]].artist
			line = line.encode("Latin-1", "ignore")
			line = line.decode(enc, "ignore")
			pctl.master_library[todo[q]].artist = line

		if enc_field == "All" or enc_field == "Album":
			line = pctl.master_library[todo[q]].album
			line = line.encode("Latin-1", "ignore")
			line = line.decode(enc, "ignore")
			pctl.master_library[todo[q]].album = line

		if enc_field == "All" or enc_field == "Title":
			line = pctl.master_library[todo[q]].title
			line = line.encode("Latin-1", "ignore")
			line = line.decode(enc, "ignore")
			pctl.master_library[todo[q]].title = line

		if old_star != None:
			star_store.insert(todo[q], old_star)

		# if key in pctl.star_library:
		#	 newkey = pctl.master_library[todo[q]].title + pctl.master_library[todo[q]].filename
		#	 if newkey not in pctl.star_library:
		#		 pctl.star_library[newkey] = copy.deepcopy(pctl.star_library[key])
		#		 # del pctl.star_library[key]


def transfer_tracks(index, mode, to):
	todo = []

	if mode == 0:
		todo = [index]
	elif mode == 1:
		for b in range(len(default_playlist)):
			if pctl.master_library[default_playlist[b]].parent_folder_name == pctl.master_library[
				index].parent_folder_name:
				todo.append(default_playlist[b])
	elif mode == 2:
		todo = default_playlist

	pctl.multi_playlist[to].playlist_ids += todo


def prep_gal():
	global albums
	albums = []

	folder = ""

	for index in default_playlist:

		if folder != pctl.master_library[index].parent_folder_name:
			albums.append([index, 0])
			folder = pctl.master_library[index].parent_folder_name


def add_stations(stations: list[dict[str, int | str]], name: str):
	if len(stations) == 1:
		for i, s in enumerate(pctl.radio_playlists):
			if s["name"] == "Default":
				s["items"].insert(0, stations[0])
				s["scroll"] = 0
				pctl.radio_playlist_viewing = i
				break
		else:
			r = {}
			r["uid"] = uid_gen()
			r["name"] = "Default"
			r["items"] = stations
			r["scroll"] = 0
			pctl.radio_playlists.append(r)
			pctl.radio_playlist_viewing = len(pctl.radio_playlists) - 1
	else:
		r = {}
		r["uid"] = uid_gen()
		r["name"] = name
		r["items"] = stations
		r["scroll"] = 0
		pctl.radio_playlists.append(r)
		pctl.radio_playlist_viewing = len(pctl.radio_playlists) - 1
	if not gui.radio_view:
		enter_radio_view()


def load_m3u(path: str) -> None:
	name = os.path.basename(path)[:-4]
	playlist = []
	stations = []

	location_dict = {}
	titles = {}

	if not os.path.isfile(path):
		return

	with Path(path).open(encoding="utf-8") as file:
		lines = file.readlines()

	for i, line in enumerate(lines):
		line = line.strip("\r\n").strip()
		if not line.startswith("#"):  # line.startswith("http"):

			# Get title if present
			line_title = ""
			if i > 0:
				bline = lines[i - 1]
				if "," in bline and bline.startswith("#EXTINF:"):
					line_title = bline.split(",", 1)[1].strip("\r\n").strip()

			if line.startswith("http"):
				radio: dict[str, int | str] = {}
				radio["stream_url"] = line

				if line_title:
					radio["title"] = line_title
				else:
					radio["title"] = os.path.splitext(os.path.basename(path))[0].strip()

				stations.append(radio)

				if gui.auto_play_import:
					gui.auto_play_import = False
					radiobox.start(radio)
			else:
				line = uri_parse(line)
				# Join file path if possibly relative
				if not line.startswith("/"):
					line = os.path.join(os.path.dirname(path), line)

				# Cache datbase file paths for quick lookup
				if not location_dict:
					for key, value in pctl.master_library.items():
						if value.fullpath:
							location_dict[value.fullpath] = value
						if value.title:
							titles[value.artist + " - " + value.title] = value

				# Is file path already imported?
				logging.info(line)
				if line in location_dict:
					playlist.append(location_dict[line].index)
					logging.info("found imported")
				# Or... does the file exist? Then import it
				elif os.path.isfile(line):
					nt = TrackClass()
					nt.index = pctl.master_count
					set_path(nt, line)
					nt = tag_scan(nt)
					pctl.master_library[pctl.master_count] = nt
					playlist.append(pctl.master_count)
					pctl.master_count += 1
					logging.info("found file")
				# Last resort, guess based on title
				elif line_title in titles:
					playlist.append(titles[line_title].index)
					logging.info("found title")
				else:
					logging.info("not found")

	if playlist:
		pctl.multi_playlist.append(
			pl_gen(title=name, playlist_ids=playlist))
	if stations:
		add_stations(stations, name)

	gui.update = 1


def read_pls(lines: list[str], path: str, followed: bool = False) -> None:
	ids = []
	urls = {}
	titles = {}

	for line in lines:
		line = line.strip("\r\n")
		if "=" in line and line.startswith("File") and "http" in line:
			# Get number
			n = line.split("=")[0][4:]
			if n.isdigit():
				if n not in ids:
					ids.append(n)
				urls[n] = line.split("=", 1)[1].strip()

		if "=" in line and line.startswith("Title"):
			# Get number
			n = line.split("=")[0][5:]
			if n.isdigit():
				if n not in ids:
					ids.append(n)
				titles[n] = line.split("=", 1)[1].strip()

	stations: list[dict[str, int | str]] = []
	for id in ids:
		if id in urls:
			radio: dict[str, int | str] = {}
			radio["stream_url"] = urls[id]
			radio["title"] = os.path.splitext(os.path.basename(path))[0]
			radio["scroll"] = 0
			if id in titles:
				radio["title"] = titles[id]

			if ".pls" in radio["stream_url"]:
				if not followed:
					try:
						logging.info("Download .pls")
						response = requests.get(radio["stream_url"], stream=True, timeout=15)
						if int(response.headers["Content-Length"]) < 2000:
							read_pls(response.content.decode().splitlines(), path, followed=True)
					except Exception:
						logging.exception("Failed to retrieve .pls")
			else:
				stations.append(radio)
				if gui.auto_play_import:
					gui.auto_play_import = False
					radiobox.start(radio)
	if stations:
		add_stations(stations, os.path.basename(path))


def load_pls(path: str) -> None:
	if os.path.isfile(path):
		f = open(path)
		lines = f.readlines()
		read_pls(lines, path)
		f.close()


def load_xspf(path: str) -> None:
	global to_got

	name = os.path.basename(path)[:-5]
	# tauon.log("Importing XSPF playlist: " + path, title=True)
	logging.info("Importing XSPF playlist: " + path)

	try:
		parser = ET.XMLParser(encoding="utf-8")
		e = ET.parse(path, parser).getroot()

		a = []
		b = {}
		info = ""

		for top in e:

			if top.tag.endswith("info"):
				info = top.text
			if top.tag.endswith("title"):
				name = top.text
			if top.tag.endswith("trackList"):
				for track in top:
					if track.tag.endswith("track"):
						for field in track:
							logging.info(field.tag)
							logging.info(field.text)
							if "title" in field.tag and field.text:
								b["title"] = field.text
							if "location" in field.tag and field.text:
								l = field.text
								l = str(urllib.parse.unquote(l))
								if l[:5] == "file:":
									l = l.replace("file:", "")
									l = l.lstrip("/")
									l = "/" + l

								b["location"] = l
							if "creator" in field.tag and field.text:
								b["artist"] = field.text
							if "album" in field.tag and field.text:
								b["album"] = field.text
							if "duration" in field.tag and field.text:
								b["duration"] = field.text

						b["info"] = info
						b["name"] = name
						a.append(copy.deepcopy(b))
						b = {}

	except Exception:
		logging.exception("Error importing/parsing XSPF playlist")
		show_message(_("Error importing XSPF playlist."), _("Sorry about that."), mode="warning")
		return

	# Extract internet streams first
	stations: list[dict[str, int | str]] = []
	for i in reversed(range(len(a))):
		item = a[i]
		if item["location"].startswith("http"):
			radio: dict[str, int | str] = {}
			radio["stream_url"] = item["location"]
			radio["title"] = item["name"]
			radio["scroll"] = 0
			if item["info"].startswith("http"):
				radio["website_url"] = item["info"]

			stations.append(radio)

			if gui.auto_play_import:
				gui.auto_play_import = False
				radiobox.start(radio)

			del a[i]
	if stations:
		add_stations(stations, os.path.basename(path))
	playlist = []
	missing = 0

	if len(a) > 5000:
		to_got = "xspfl"

	# Generate location dict
	location_dict = {}
	base_names = {}
	r_base_names = {}
	titles = {}
	for key, value in pctl.master_library.items():
		if value.fullpath != "":
			location_dict[value.fullpath] = key
		if value.filename != "":
			base_names[value.filename] = 0
			r_base_names[key] = value.filename
		if value.title != "":
			titles[value.title] = 0

	for track in a:
		found = False

		# Check if we already have a track with full file path in database
		if not found and "location" in track:

			location = track["location"]
			if location in location_dict:
				playlist.append(location_dict[location])
				if not os.path.isfile(location):
					missing += 1
				found = True

			if found is True:
				continue

		# Then check for title, artist and filename match
		if not found and "location" in track and "duration" in track and "title" in track and "artist" in track:
			base = os.path.basename(track["location"])
			if base in base_names:
				for index, bn in r_base_names.items():
					va = pctl.master_library[index]
					if va.artist == track["artist"] and va.title == track["title"] and \
							os.path.isfile(va.fullpath) and \
							va.filename == base:
						playlist.append(index)
						if not os.path.isfile(va.fullpath):
							missing += 1
						found = True
						break
				if found is True:
					continue

		# Then check for just title and artist match
		if not found and "title" in track and "artist" in track and track["title"] in titles:
			for key, value in pctl.master_library.items():
				if value.artist == track["artist"] and value.title == track["title"] and os.path.isfile(value.fullpath):
					playlist.append(key)
					if not os.path.isfile(value.fullpath):
						missing += 1
					found = True
					break
			if found is True:
				continue

		if (not found and "location" in track) or "title" in track:
			nt = TrackClass()
			nt.index = pctl.master_count
			nt.found = False

			if "location" in track:
				location = track["location"]
				set_path(nt, location)
				if os.path.isfile(location):
					nt.found = True
			elif "album" in track:
				nt.parent_folder_name = track["album"]
			if "artist" in track:
				nt.artist = track["artist"]
			if "title" in track:
				nt.title = track["title"]
			if "duration" in track:
				nt.length = int(float(track["duration"]) / 1000)
			if "album" in track:
				nt.album = track["album"]
			nt.is_cue = False
			if nt.found:
				nt = tag_scan(nt)

			pctl.master_library[pctl.master_count] = nt
			playlist.append(pctl.master_count)
			pctl.master_count += 1
			if nt.found:
				continue

		missing += 1
		logging.error("-- Failed to locate track")
		if "location" in track:
			logging.error("-- -- Expected path: " + track["location"])
		if "title" in track:
			logging.error("-- -- Title: " + track["title"])
		if "artist" in track:
			logging.error("-- -- Artist: " + track["artist"])
		if "album" in track:
			logging.error("-- -- Album: " + track["album"])

	if missing > 0:
		show_message(
			_("Failed to locate {N} out of {T} tracks.")
			.format(N=str(missing), T=str(len(a))))
	#logging.info(playlist)
	if playlist:
		pctl.multi_playlist.append(
			pl_gen(title=name, playlist_ids=playlist))
	gui.update = 1

	# tauon.log("Finished importing XSPF")


bb_type = 0

# gui.scroll_hide_box = (0, gui.panelY, 28, window_size[1] - gui.panelBY - gui.panelY)

encoding_menu = False
enc_index = 0
enc_setting = 0
enc_field = "All"

gen_menu = False

transfer_setting = 0

b_panel_size = 300
b_info_bar = False

message_info_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "notice.png")
message_warning_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "warning.png")
message_tick_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "done.png")
message_arrow_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "ext.png")
message_error_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "error.png")
message_bubble_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "bubble.png")
message_download_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "ddl.png")




tool_tip = ToolTip()
tool_tip2 = ToolTip()
tool_tip2.trigger = 1.8
track_box_path_tool_timer = Timer()


def ex_tool_tip(x, y, text1_width, text, font):
	text2_width = ddt.get_text_w(text, font)
	if text2_width == text1_width:
		return

	y -= 10 * gui.scale

	w = ddt.get_text_w(text, 312) + 24 * gui.scale
	h = 24 * gui.scale

	x -= int(w / 2)

	border = 1 * gui.scale
	ddt.rect((x - border, y - border, w + border * 2, h + border * 2), colours.grey(60))
	ddt.rect((x, y, w, h), colours.menu_background)
	p = ddt.text((x + int(w / 2), y + 3 * gui.scale, 2), text, colours.menu_text, 312, bg=colours.menu_background)




columns_tool_tip = ToolTip3()

tool_tip_instant = ToolTip3()

def close_all_menus():
	for menu in Menu.instances:
		menu.active = False
	Menu.active = False


def menu_standard_or_grey(bool: bool):
	if bool:
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled

	return [line_colour, colours.menu_background, None]


# Create empty area menu
playlist_menu = Menu(130)
radio_entry_menu = Menu(125)
showcase_menu = Menu(135)
center_info_menu = Menu(125)
cancel_menu = Menu(100)
gallery_menu = Menu(175, show_icons=True)
artist_info_menu = Menu(135)
queue_menu = Menu(150)
repeat_menu = Menu(120)
shuffle_menu = Menu(120)
artist_list_menu = Menu(165, show_icons=True)
lightning_menu = Menu(165)
lsp_menu = Menu(145)
folder_tree_menu = Menu(175, show_icons=True)
folder_tree_stem_menu = Menu(190, show_icons=True)
overflow_menu = Menu(175)
spotify_playlist_menu = Menu(175)
radio_context_menu = Menu(175)
#chrome_menu = Menu(175)




def enable_artist_list():
	if prefs.left_panel_mode != "artist list":
		gui.last_left_panel_mode = prefs.left_panel_mode
	prefs.left_panel_mode = "artist list"
	gui.lsp = True
	gui.update_layout()


def enable_playlist_list():
	if prefs.left_panel_mode != "playlist":
		gui.last_left_panel_mode = prefs.left_panel_mode
	prefs.left_panel_mode = "playlist"
	gui.lsp = True
	gui.update_layout()


def enable_queue_panel():
	if prefs.left_panel_mode != "queue":
		gui.last_left_panel_mode = prefs.left_panel_mode
	prefs.left_panel_mode = "queue"
	gui.lsp = True
	gui.update_layout()


def enable_folder_list():
	if prefs.left_panel_mode != "folder view":
		gui.last_left_panel_mode = prefs.left_panel_mode
	prefs.left_panel_mode = "folder view"
	gui.lsp = True
	gui.update_layout()


def lsp_menu_test_queue():
	if not gui.lsp:
		return False
	return prefs.left_panel_mode == "queue"


def lsp_menu_test_playlist():
	if not gui.lsp:
		return False
	return prefs.left_panel_mode == "playlist"


def lsp_menu_test_tree():
	if not gui.lsp:
		return False
	return prefs.left_panel_mode == "folder view"


def lsp_menu_test_artist():
	if not gui.lsp:
		return False
	return prefs.left_panel_mode == "artist list"


def toggle_left_last():
	gui.lsp = True
	t = prefs.left_panel_mode
	if t != gui.last_left_panel_mode:
		prefs.left_panel_mode = gui.last_left_panel_mode
		gui.last_left_panel_mode = t


# . Menu entry: A side panel view layout

lsp_menu.add(MenuItem(_("Playlists + Queue"), enable_playlist_list, disable_test=lsp_menu_test_playlist))
lsp_menu.add(MenuItem(_("Queue"), enable_queue_panel, disable_test=lsp_menu_test_queue))
# . Menu entry: Side panel view layout showing a list of artists with thumbnails
lsp_menu.add(MenuItem(_("Artist List"), enable_artist_list, disable_test=lsp_menu_test_artist))
# . Menu entry: A side panel view layout. Alternative name: Folder Tree
lsp_menu.add(MenuItem(_("Folder Navigator"), enable_folder_list, disable_test=lsp_menu_test_tree))




rename_track_box = RenameTrackBox()



trans_edit_box = TransEditBox()




sub_lyrics_box = SubLyricsBox()




export_playlist_box = ExportPlaylistBox()


def toggle_repeat() -> None:
	gui.update += 1
	pctl.repeat_mode ^= True
	if pctl.mpris is not None:
		pctl.mpris.update_loop()


tauon.toggle_repeat = toggle_repeat


def menu_repeat_off() -> None:
	pctl.repeat_mode = False
	pctl.album_repeat_mode = False
	if pctl.mpris is not None:
		pctl.mpris.update_loop()


def menu_set_repeat() -> None:
	pctl.repeat_mode = True
	pctl.album_repeat_mode = False
	if pctl.mpris is not None:
		pctl.mpris.update_loop()


def menu_album_repeat() -> None:
	pctl.repeat_mode = True
	pctl.album_repeat_mode = True
	if pctl.mpris is not None:
		pctl.mpris.update_loop()


tauon.menu_album_repeat = menu_album_repeat
tauon.menu_repeat_off = menu_repeat_off
tauon.menu_set_repeat = menu_set_repeat

repeat_menu.add(MenuItem(_("Repeat OFF"), menu_repeat_off))
repeat_menu.add(MenuItem(_("Repeat Track"), menu_set_repeat))
repeat_menu.add(MenuItem(_("Repeat Album"), menu_album_repeat))


def toggle_random():
	gui.update += 1
	pctl.random_mode ^= True
	if pctl.mpris is not None:
		pctl.mpris.update_shuffle()


tauon.toggle_random = toggle_random


def toggle_random_on():
	pctl.random_mode = True
	if pctl.mpris is not None:
		pctl.mpris.update_shuffle()


def toggle_random_off():
	pctl.random_mode = False
	if pctl.mpris is not None:
		pctl.mpris.update_shuffle()


def menu_shuffle_off():
	pctl.random_mode = False
	pctl.album_shuffle_mode = False
	if pctl.mpris is not None:
		pctl.mpris.update_shuffle()


def menu_set_random():
	pctl.random_mode = True
	pctl.album_shuffle_mode = False
	if pctl.mpris is not None:
		pctl.mpris.update_shuffle()


def menu_album_random():
	pctl.random_mode = True
	pctl.album_shuffle_mode = True
	if pctl.mpris is not None:
		pctl.mpris.update_shuffle()


def toggle_shuffle_layout(albums=False):
	prefs.shuffle_lock ^= True
	if prefs.shuffle_lock:

		gui.shuffle_was_showcase = gui.showcase_mode
		gui.shuffle_was_random = pctl.random_mode
		gui.shuffle_was_repeat = pctl.repeat_mode

		if not gui.combo_mode:
			view_box.lyrics(hit=True)
		pctl.random_mode = True
		pctl.repeat_mode = False
		if albums:
			prefs.album_shuffle_lock_mode = True
		if pctl.playing_state == 0:
			pctl.advance()
	else:
		pctl.random_mode = gui.shuffle_was_random
		pctl.repeat_mode = gui.shuffle_was_repeat
		prefs.album_shuffle_lock_mode = False
		if not gui.shuffle_was_showcase:
			exit_combo()


def toggle_shuffle_layout_albums():
	toggle_shuffle_layout(albums=True)


def exit_shuffle_layout(_):
	return prefs.shuffle_lock


shuffle_menu.add(MenuItem(_("Shuffle Lockdown"), toggle_shuffle_layout))
shuffle_menu.add(MenuItem(_("Shuffle Lockdown Albums"), toggle_shuffle_layout_albums))
shuffle_menu.br()
shuffle_menu.add(MenuItem(_("Shuffle OFF"), menu_shuffle_off))
shuffle_menu.add(MenuItem(_("Shuffle Tracks"), menu_set_random))
shuffle_menu.add(MenuItem(_("Random Albums"), menu_album_random))


def bio_set_large():
	# if window_size[0] >= round(1000 * gui.scale):
	# gui.artist_panel_height = 320 * gui.scale
	prefs.bio_large = True
	if gui.artist_info_panel:
		artist_info_box.get_data(artist_info_box.artist_on)


def bio_set_small():
	# gui.artist_panel_height = 200 * gui.scale
	prefs.bio_large = False
	update_layout_do()
	if gui.artist_info_panel:
		artist_info_box.get_data(artist_info_box.artist_on)


def artist_info_panel_close():
	gui.artist_info_panel ^= True
	gui.update_layout()


def toggle_bio_size_deco():
	line = _("Make Large Size")
	if prefs.bio_large:
		line = _("Make Compact Size")

	return [colours.menu_text, colours.menu_background, line]


def toggle_bio_size():
	if prefs.bio_large:
		prefs.bio_large = False
		update_layout_do()
		# bio_set_small()

	else:
		prefs.bio_large = True
		update_layout_do()
		# bio_set_large()
	# gui.update_layout()


def flush_artist_bio(artist):
	if os.path.isfile(os.path.join(a_cache_dir, artist + "-lfm.txt")):
		os.remove(os.path.join(a_cache_dir, artist + "-lfm.txt"))
	artist_info_box.text = ""
	artist_info_box.artist_on = None


def test_shift(_):
	return key_shift_down or key_shiftr_down


def test_artist_dl(_):
	return not prefs.auto_dl_artist_data


artist_info_menu.add(MenuItem(_("Close Panel"), artist_info_panel_close))
artist_info_menu.add(MenuItem(_("Make Large"), toggle_bio_size, toggle_bio_size_deco))


def show_in_playlist():
	if album_mode and window_size[0] < 750 * gui.scale:
		toggle_album_mode()

	pctl.playlist_view_position = pctl.selected_in_playlist
	logging.debug("Position changed by show in playlist")
	shift_selection.clear()
	shift_selection.append(pctl.selected_in_playlist)
	pctl.render_playlist()


filter_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "filter.png", True))
filter_icon.colour = [43, 213, 255, 255]
filter_icon.xoff = 1

folder_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "folder.png", True))
info_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "info.png", True))

folder_icon.colour = [244, 220, 66, 255]
info_icon.colour = [61, 247, 163, 255]

power_bar_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "power.png", True)


def open_folder_stem(path):
	if system == "Windows" or msys:
		line = r'explorer /select,"%s"' % (
			path.replace("/", "\\"))
		subprocess.Popen(line)
	else:
		line = path
		line += "/"
		if macos:
			subprocess.Popen(["open", line])
		else:
			subprocess.Popen(["xdg-open", line])


def open_folder_disable_test(index: int):
	track = pctl.master_library[index]
	return track.is_network and not os.path.isdir(track.parent_folder_path)

def open_folder(index: int):
	track = pctl.master_library[index]
	if open_folder_disable_test(index):
		show_message(_("Can't open folder of a network track."))
		return

	if system == "Windows" or msys:
		line = r'explorer /select,"%s"' % (
			track.fullpath.replace("/", "\\"))
		subprocess.Popen(line)
	else:
		line = track.parent_folder_path
		line += "/"
		if macos:
			line = track.fullpath
			subprocess.Popen(["open", "-R", line])
		else:
			subprocess.Popen(["xdg-open", line])


def tag_to_new_playlist(tag_item):
	path_stem_to_playlist(tag_item.path, tag_item.name)


def folder_to_new_playlist_by_track_id(track_id: int) -> None:
	track = pctl.get_track(track_id)
	path_stem_to_playlist(track.parent_folder_path, track.parent_folder_name)


def stem_to_new_playlist(path: str) -> None:
	path_stem_to_playlist(path, os.path.basename(path))


move_jobs = []
move_in_progress = False


def move_playing_folder_to_tree_stem(path: str) -> None:
	move_playing_folder_to_stem(path, pl_id=tree_view_box.get_pl_id())


def move_playing_folder_to_stem(path: str, pl_id: int | None = None) -> None:
	if not pl_id:
		pl_id = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int

	track = pctl.playing_object()

	if not track or pctl.playing_state == 0:
		show_message(_("No item is currently playing"))
		return

	move_folder = track.parent_folder_path

	# Stop playing track if its in the current folder
	if pctl.playing_state > 0:
		if move_folder in pctl.playing_object().parent_folder_path:
			pctl.stop(True)

	target_base = path

	# Determine name for artist folder
	artist = track.artist
	if track.album_artist:
		artist = track.album_artist

	# Make filename friendly
	artist = filename_safe(artist)
	if not artist:
		artist = "unknown artist"

	# Sanity checks
	if track.is_network:
		show_message(_("This track is a networked track."), mode="error")
		return

	if not os.path.isdir(move_folder):
		show_message(_("The source folder does not exist."), mode="error")
		return

	if not os.path.isdir(target_base):
		show_message(_("The destination folder does not exist."), mode="error")
		return

	if os.path.normpath(target_base) == os.path.normpath(move_folder):
		show_message(_("The destination and source folders are the same."), mode="error")
		return

	if len(target_base) < 4:
		show_message(_("Safety interupt! The source path seems oddly short."), target_base, mode="error")
		return

	protect = ("", "Documents", "Music", "Desktop", "Downloads")
	for fo in protect:
		if move_folder.strip("\\/") == os.path.join(os.path.expanduser("~"), fo).strip("\\/"):
			show_message(
				_("Better not do anything to that folder!"), os.path.join(os.path.expanduser("~"), fo),
				mode="warning")
			return

	if directory_size(move_folder) > 3000000000:
		show_message(_("Folder size safety limit reached! (3GB)"), move_folder, mode="warning")
		return

	# Use target folder if it already is an artist folder
	if os.path.basename(target_base).lower() == artist.lower():
		artist_folder = target_base

	# Make artist folder if it does not exist
	else:
		artist_folder = os.path.join(target_base, artist)
		if not os.path.exists(artist_folder):
			os.makedirs(artist_folder)

	# Remove all tracks with the old paths
	for pl in pctl.multi_playlist:
		for i in reversed(range(len(pl.playlist_ids))):
			if pctl.get_track(pl.playlist_ids[i]).parent_folder_path == track.parent_folder_path:
				del pl.playlist_ids[i]

	# Find insert location
	pl = pctl.multi_playlist[id_to_pl(pl_id)].playlist_ids

	matches = []
	insert = 0

	for i, item in enumerate(pl):
		if pctl.get_track(item).fullpath.startswith(target_base):
			insert = i

	for i, item in enumerate(pl):
		if pctl.get_track(item).fullpath.startswith(artist_folder):
			insert = i

	logging.info("The folder to be moved is: " + move_folder)
	load_order = LoadClass()
	load_order.target = os.path.join(artist_folder, track.parent_folder_name)
	load_order.playlist = pl_id
	load_order.playlist_position = insert

	logging.info(artist_folder)
	logging.info(os.path.join(artist_folder, track.parent_folder_name))
	move_jobs.append(
		(move_folder, os.path.join(artist_folder, track.parent_folder_name), True,
		track.parent_folder_name, load_order))
	tauon.thread_manager.ready("worker")


def move_playing_folder_to_tag(tag_item):
	move_playing_folder_to_stem(tag_item.path)


def re_import4(id):
	p = None
	for i, idd in enumerate(default_playlist):
		if idd == id:
			p = i
			break

	load_order = LoadClass()

	if p is not None:
		load_order.playlist_position = p

	load_order.replace_stem = True
	load_order.target = pctl.get_track(id).parent_folder_path
	load_order.notify = True
	load_order.playlist = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int
	load_orders.append(copy.deepcopy(load_order))
	show_message(_("Rescanning folder..."), pctl.get_track(id).parent_folder_path, mode="info")


def re_import3(stem):
	p = None
	for i, id in enumerate(default_playlist):
		if pctl.get_track(id).fullpath.startswith(stem + "/"):
			p = i
			break

	load_order = LoadClass()

	if p is not None:
		load_order.playlist_position = p

	load_order.replace_stem = True
	load_order.target = stem
	load_order.notify = True
	load_order.playlist = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int
	load_orders.append(copy.deepcopy(load_order))
	show_message(_("Rescanning folder..."), stem, mode="info")


def collapse_tree_deco():
	pl_id = tree_view_box.get_pl_id()

	if tree_view_box.opens.get(pl_id):
		return [colours.menu_text, colours.menu_background, None]
	return [colours.menu_text_disabled, colours.menu_background, None]


def collapse_tree():
	tree_view_box.collapse_all()


def lock_folder_tree():
	if tree_view_box.lock_pl:
		tree_view_box.lock_pl = None
	else:
		tree_view_box.lock_pl = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int


def lock_folder_tree_deco():
	if tree_view_box.lock_pl:
		return [colours.menu_text, colours.menu_background, _("Unlock Panel")]
	return [colours.menu_text, colours.menu_background, _("Lock Panel")]


folder_tree_stem_menu.add(MenuItem(_("Open Folder"), open_folder_stem, pass_ref=True, icon=folder_icon))
folder_tree_menu.add(MenuItem(_("Open Folder"), open_folder, pass_ref=True, pass_ref_deco=True, icon=folder_icon, disable_test=open_folder_disable_test))

lightning_menu.add(MenuItem(_("Filter to New Playlist"), tag_to_new_playlist, pass_ref=True, icon=filter_icon))
folder_tree_menu.add(MenuItem(_("Filter to New Playlist"), folder_to_new_playlist_by_track_id, pass_ref=True, icon=filter_icon))
folder_tree_stem_menu.add(MenuItem(_("Filter to New Playlist"), stem_to_new_playlist, pass_ref=True, icon=filter_icon))
folder_tree_stem_menu.add(MenuItem(_("Rescan Folder"), re_import3, pass_ref=True))
folder_tree_menu.add(MenuItem(_("Rescan Folder"), re_import4, pass_ref=True))
lightning_menu.add(MenuItem(_("Move Playing Folder Here"), move_playing_folder_to_tag, pass_ref=True))

folder_tree_stem_menu.add(MenuItem(_("Move Playing Folder Here"), move_playing_folder_to_tree_stem, pass_ref=True))

folder_tree_stem_menu.br()

folder_tree_stem_menu.add(MenuItem(_("Collapse All"), collapse_tree, collapse_tree_deco))

folder_tree_stem_menu.add(MenuItem("lock", lock_folder_tree, lock_folder_tree_deco))
# folder_tree_menu.add("lock", lock_folder_tree, lock_folder_tree_deco)

gallery_menu.add(MenuItem(_("Open Folder"), open_folder, pass_ref=True, pass_ref_deco=True, icon=folder_icon, disable_test=open_folder_disable_test))

gallery_menu.add(MenuItem(_("Show in Playlist"), show_in_playlist))


def finish_current():
	playing_object = pctl.playing_object()
	if playing_object is None:
		show_message("")

	if not pctl.force_queue:
		pctl.force_queue.insert(
			0, queue_item_gen(playing_object.index,
			pctl.playlist_playing_position,
			pl_to_id(pctl.active_playlist_playing), 1, 1))


def add_album_to_queue(ref, position=None, playlist_id=None):
	if position is None:
		position = r_menu_position
	if playlist_id is None:
		playlist_id = pl_to_id(pctl.active_playlist_viewing)

	partway = 0
	playing_object = pctl.playing_object()
	if not pctl.force_queue and playing_object is not None:
		if pctl.get_track(ref).parent_folder_path == playing_object.parent_folder_path:
			partway = 1

	queue_object = queue_item_gen(ref, position, playlist_id, 1, partway)
	pctl.force_queue.append(queue_object)
	queue_timer_set(queue_object=queue_object)
	if prefs.stop_end_queue:
		pctl.auto_stop = False


def add_album_to_queue_fc(ref):
	playing_object = pctl.playing_object()
	if playing_object is None:
		show_message("")

	queue_item = None

	if not pctl.force_queue:
		queue_item = queue_item_gen(
			playing_object.index, pctl.playlist_playing_position, pl_to_id(pctl.active_playlist_playing), 1, 1)
		pctl.force_queue.insert(0, queue_item)
		add_album_to_queue(ref)
		return

	if pctl.force_queue[0].album_stage == 1:
		queue_item = queue_item_gen(ref, pctl.playlist_playing_position, pl_to_id(pctl.active_playlist_playing), 1, 0)
		pctl.force_queue.insert(1, queue_item)
	else:

		p = pctl.get_track(ref).parent_folder_path
		p = ""
		if pctl.playing_ready():
			p = pctl.playing_object().parent_folder_path

		# fixme for network tracks

		for i, item in enumerate(pctl.force_queue):

			if p != pctl.get_track(item.track_id).parent_folder_path:
				queue_item = queue_item_gen(
					ref,
					pctl.playlist_playing_position,
					pl_to_id(pctl.active_playlist_playing), 1, 0)
				pctl.force_queue.insert(i, queue_item)
				break

		else:
			queue_item = queue_item_gen(
				ref, pctl.playlist_playing_position, pl_to_id(pctl.active_playlist_playing), 1, 0)
			pctl.force_queue.insert(len(pctl.force_queue), queue_item)
	if queue_item:
		queue_timer_set(queue_object=queue_item)
	if prefs.stop_end_queue:
		pctl.auto_stop = False



gallery_menu.add_sub(_("Image…"), 160)
gallery_menu.add(MenuItem(_("Add Album to Queue"), add_album_to_queue, pass_ref=True))
gallery_menu.add(MenuItem(_("Enqueue Album Next"), add_album_to_queue_fc, pass_ref=True))


def cancel_import():
	if transcode_list:
		del transcode_list[1:]
		gui.tc_cancel = True
	if loading_in_progress:
		gui.im_cancel = True
	if gui.sync_progress:
		gui.stop_sync = True
		gui.sync_progress = _("Aborting Sync")


cancel_menu.add(MenuItem(_("Cancel"), cancel_import))


def toggle_lyrics_show(a):
	return not gui.combo_mode


def toggle_side_art_deco():
	colour = colours.menu_text
	if prefs.show_side_lyrics_art_panel:
		line = _("Hide Metadata Panel")
	else:
		line = _("Show Metadata Panel")

	if gui.combo_mode:
		colour = colours.menu_text_disabled

	return [colour, colours.menu_background, line]


def toggle_lyrics_panel_position_deco():
	colour = colours.menu_text
	if prefs.lyric_metadata_panel_top:
		line = _("Panel Below Lyrics")
	else:
		line = _("Panel Above Lyrics")

	if gui.combo_mode or not prefs.show_side_lyrics_art_panel:
		colour = colours.menu_text_disabled

	return [colour, colours.menu_background, line]


def toggle_lyrics_panel_position():
	prefs.lyric_metadata_panel_top ^= True


def lyrics_in_side_show(track_object: TrackClass):
	if gui.combo_mode or not prefs.show_lyrics_side:
		return False
	return True


def toggle_side_art():
	prefs.show_side_lyrics_art_panel ^= True


def toggle_lyrics_deco(track_object: TrackClass):
	colour = colours.menu_text

	if gui.combo_mode:
		if prefs.show_lyrics_showcase:
			line = _("Hide Lyrics")
		else:
			line = _("Show Lyrics")
		if not track_object or (track_object.lyrics == "" and not timed_lyrics_ren.generate(track_object)):
			colour = colours.menu_text_disabled
		return [colour, colours.menu_background, line]

	if prefs.side_panel_layout == 1:  # and prefs.show_side_art:

		if prefs.show_lyrics_side:
			line = _("Hide Lyrics")
		else:
			line = _("Show Lyrics")
		if (track_object.lyrics == "" and not timed_lyrics_ren.generate(track_object)):
			colour = colours.menu_text_disabled
		return [colour, colours.menu_background, line]

	if prefs.show_lyrics_side:
		line = _("Hide Lyrics")
	else:
		line = _("Show Lyrics")
	if (track_object.lyrics == "" and not timed_lyrics_ren.generate(track_object)):
		colour = colours.menu_text_disabled
	return [colour, colours.menu_background, line]


def toggle_lyrics(track_object: TrackClass):
	if not track_object:
		return

	if gui.combo_mode:
		prefs.show_lyrics_showcase ^= True
		if prefs.show_lyrics_showcase and track_object.lyrics == "" and timed_lyrics_ren.generate(track_object):
			prefs.prefer_synced_lyrics = True
		# if prefs.show_lyrics_showcase and track_object.lyrics == "":
		#	 show_message("No lyrics for this track")
	else:

		# Handling for alt panel layout
		# if prefs.side_panel_layout == 1 and prefs.show_side_art:
		#	 #prefs.show_side_art = False
		#	 prefs.show_lyrics_side = True
		#	 return

		prefs.show_lyrics_side ^= True
		if prefs.show_lyrics_side and track_object.lyrics == "" and timed_lyrics_ren.generate(track_object):
			prefs.prefer_synced_lyrics = True
		# if prefs.show_lyrics_side and track_object.lyrics == "":
		#	 show_message("No lyrics for this track")


def get_lyric_fire(track_object: TrackClass, silent: bool = False) -> str | None:
	lyrics_ren.lyrics_position = 0

	if not prefs.lyrics_enables:
		if not silent:
			show_message(
				_("There are no lyric sources enabled."),
				_("See 'lyrics settings' under 'functions' tab in settings."), mode="info")
		return None

	t = lyrics_fetch_timer.get()
	logging.info("Lyric rate limit timer is: " + str(t) + " / -60")
	if t < -40:
		logging.info("Lets try again later")
		if not silent:
			show_message(_("Let's be polite and try later."))

			if t < -65:
				show_message(_("Stop requesting lyrics AAAAAA."), mode="error")

		# If the user keeps pressing, lets mess with them haha
		lyrics_fetch_timer.force_set(t - 5)

		return "later"

	if t > 0:
		lyrics_fetch_timer.set()
		t = 0

	lyrics_fetch_timer.force_set(t - 10)

	if not silent:
		show_message(_("Searching..."))

	s_artist = track_object.artist
	s_title = track_object.title

	if s_artist in prefs.lyrics_subs:
		s_artist = prefs.lyrics_subs[s_artist]
	if s_title in prefs.lyrics_subs:
		s_title = prefs.lyrics_subs[s_title]

	logging.info(f"Searching for lyrics: {s_artist} - {s_title}")

	found = False
	for name in prefs.lyrics_enables:

		if name in lyric_sources.keys():
			func = lyric_sources[name]

			try:
				lyrics = func(s_artist, s_title)
				if lyrics:
					logging.info(f"Found lyrics from {name}")
					track_object.lyrics = lyrics
					found = True
					break
			except Exception:
				logging.exception("Failed to find lyrics")

			if not found:
				logging.error(f"Could not find lyrics from source {name}")

	if not found:
		if not silent:
			show_message(_("No lyrics for this track were found"))
	else:
		gui.message_box = False
		if not gui.showcase_mode:
			prefs.show_lyrics_side = True
		gui.update += 1
		lyrics_ren.lyrics_position = 0
		pctl.notify_change()


def get_lyric_wiki(track_object: TrackClass):
	if track_object.artist == "" or track_object.title == "":
		show_message(_("Insufficient metadata to get lyrics"), mode="warning")
		return

	shoot_dl = threading.Thread(target=get_lyric_fire, args=([track_object]))
	shoot_dl.daemon = True
	shoot_dl.start()

	logging.info("..Done")


def get_lyric_wiki_silent(track_object: TrackClass):
	logging.info("Searching for lyrics...")

	if track_object.artist == "" or track_object.title == "":
		return

	shoot_dl = threading.Thread(target=get_lyric_fire, args=([track_object, True]))
	shoot_dl.daemon = True
	shoot_dl.start()

	logging.info("..Done")


def test_auto_lyrics(track_object: TrackClass):
	if not track_object:
		return

	if prefs.auto_lyrics and not track_object.lyrics and track_object.index not in prefs.auto_lyrics_checked:
		if lyrics_check_timer.get() > 5 and pctl.playing_time > 1:
			result = get_lyric_wiki_silent(track_object)
			if result == "later":
				pass
			else:
				lyrics_check_timer.set()
				prefs.auto_lyrics_checked.append(track_object.index)


def get_bio(track_object: TrackClass):
	if track_object.artist != "":
		lastfm.get_bio(track_object.artist)


def search_lyrics_deco(track_object: TrackClass):
	if not track_object.lyrics:
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled

	return [line_colour, colours.menu_background, None]


showcase_menu.add(MenuItem(_("Search for Lyrics"), get_lyric_wiki, search_lyrics_deco, pass_ref=True, pass_ref_deco=True))


def toggle_synced_lyrics(tr):
	prefs.prefer_synced_lyrics ^= True

def toggle_synced_lyrics_deco(track):
	if prefs.prefer_synced_lyrics:
		text = _("Show static lyrics")
	else:
		text = _("Show synced lyrics")
	if timed_lyrics_ren.generate(track) and track.lyrics:
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled
		if not track.lyrics:
			text = _("Show static lyrics")
		if not timed_lyrics_ren.generate(track):
			text = _("Show synced lyrics")

	return [line_colour, colours.menu_background, text]

showcase_menu.add(MenuItem("Toggle synced", toggle_synced_lyrics, toggle_synced_lyrics_deco, pass_ref=True, pass_ref_deco=True))

def paste_lyrics_deco():
	if SDL_HasClipboardText():
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled

	return [line_colour, colours.menu_background, None]

def paste_lyrics(track_object: TrackClass):
	if SDL_HasClipboardText():
		clip = SDL_GetClipboardText()
		#logging.info(clip)
		track_object.lyrics = clip.decode("utf-8")
	else:
		logging.warning("NO TEXT TO PASTE")

#def chord_lyrics_paste_show_test(_) -> bool:
#	return gui.combo_mode and prefs.guitar_chords
# showcase_menu.add(MenuItem(_("Search GuitarParty"), search_guitarparty, pass_ref=True, show_test=chord_lyrics_paste_show_test))

#guitar_chords = GuitarChords(user_directory=user_directory, ddt=ddt, inp=inp, gui=gui, pctl=pctl)
#showcase_menu.add(MenuItem(_("Paste Chord Lyrics"), guitar_chords.paste_chord_lyrics, pass_ref=True, show_test=chord_lyrics_paste_show_test))
#showcase_menu.add(MenuItem(_("Clear Chord Lyrics"), guitar_chords.clear_chord_lyrics, pass_ref=True, show_test=chord_lyrics_paste_show_test))


def copy_lyrics_deco(track_object: TrackClass):
	if track_object.lyrics:
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled

	return [line_colour, colours.menu_background, None]


def copy_lyrics(track_object: TrackClass):
	copy_to_clipboard(track_object.lyrics)


def clear_lyrics(track_object: TrackClass):
	track_object.lyrics = ""


def clear_lyrics_deco(track_object: TrackClass):
	if track_object.lyrics:
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled

	return [line_colour, colours.menu_background, None]


def split_lyrics(track_object: TrackClass):
	if track_object.lyrics != "":
		track_object.lyrics = track_object.lyrics.replace(". ", ". \n")
	else:
		pass


def show_sub_search(track_object: TrackClass):
	sub_lyrics_box.activate(track_object)


showcase_menu.add(MenuItem(_("Toggle Lyrics"), toggle_lyrics, toggle_lyrics_deco, pass_ref=True, pass_ref_deco=True))
showcase_menu.add_sub(_("Misc…"), 150)
showcase_menu.add_to_sub(0, MenuItem(_("Substitute Search..."), show_sub_search, pass_ref=True))
showcase_menu.add_to_sub(0, MenuItem(_("Paste Lyrics"), paste_lyrics, paste_lyrics_deco, pass_ref=True))
showcase_menu.add_to_sub(0, MenuItem(_("Copy Lyrics"), copy_lyrics, copy_lyrics_deco, pass_ref=True, pass_ref_deco=True))
showcase_menu.add_to_sub(0, MenuItem(_("Clear Lyrics"), clear_lyrics, clear_lyrics_deco, pass_ref=True, pass_ref_deco=True))
showcase_menu.add_to_sub(0, MenuItem(_("Toggle art panel"), toggle_side_art, toggle_side_art_deco, show_test=lyrics_in_side_show))
showcase_menu.add_to_sub(0, MenuItem(_("Toggle art position"),
	toggle_lyrics_panel_position, toggle_lyrics_panel_position_deco, show_test=lyrics_in_side_show))

center_info_menu.add(MenuItem(_("Search for Lyrics"), get_lyric_wiki, search_lyrics_deco, pass_ref=True, pass_ref_deco=True))
center_info_menu.add(MenuItem(_("Toggle Lyrics"), toggle_lyrics, toggle_lyrics_deco, pass_ref=True, pass_ref_deco=True))
center_info_menu.add_sub(_("Misc…"), 150)
center_info_menu.add_to_sub(0, MenuItem(_("Substitute Search..."), show_sub_search, pass_ref=True))
center_info_menu.add_to_sub(0, MenuItem(_("Paste Lyrics"), paste_lyrics, paste_lyrics_deco, pass_ref=True))
center_info_menu.add_to_sub(0, MenuItem(_("Copy Lyrics"), copy_lyrics, copy_lyrics_deco, pass_ref=True, pass_ref_deco=True))
center_info_menu.add_to_sub(0, MenuItem(_("Clear Lyrics"), clear_lyrics, clear_lyrics_deco, pass_ref=True, pass_ref_deco=True))
center_info_menu.add_to_sub(0, MenuItem(_("Toggle art panel"), toggle_side_art, toggle_side_art_deco, show_test=lyrics_in_side_show))
center_info_menu.add_to_sub(0, MenuItem(_("Toggle art position"),
	toggle_lyrics_panel_position, toggle_lyrics_panel_position_deco, show_test=lyrics_in_side_show))

def save_embed_img_disable_test(track_object: TrackClass):
	if type(track_object) is int:
		track_object = pctl.master_library[track_object]
	return track_object.is_network

def save_embed_img(track_object: TrackClass):
	if type(track_object) is int:
		track_object = pctl.master_library[track_object]
	filepath = track_object.fullpath
	folder = track_object.parent_folder_path
	ext = track_object.file_ext

	if save_embed_img_disable_test(track_object):
		show_message(_("Saving network images not implemented"))
		return

	try:
		pic = album_art_gen.get_embed(track_object)

		if not pic:
			show_message(_("Image save error."), _("No embedded album art found file."), mode="warning")
			return

		source_image = io.BytesIO(pic)
		im = Image.open(source_image)

		source_image.close()

		ext = "." + im.format.lower()
		if im.format == "JPEG":
			ext = ".jpg"

		target = os.path.join(folder, "embed-" + str(im.height) + "px-" + str(track_object.index) + ext)

		if len(pic) > 30:
			with open(target, "wb") as w:
				w.write(pic)

		open_folder(track_object.index)

	except Exception:
		logging.exception("Unknown error trying to save an image")
		show_message(_("Image save error."), _("A mysterious error occurred"), mode="error")


picture_menu = Menu(175)


def open_image_deco(track_object: TrackClass):
	if type(track_object) is int:
		track_object = pctl.master_library[track_object]
	info = album_art_gen.get_info(track_object)

	if info is None:
		return [colours.menu_text_disabled, colours.menu_background, None]

	line_colour = colours.menu_text

	return [line_colour, colours.menu_background, None]


def open_image_disable_test(track_object: TrackClass):
	if type(track_object) is int:
		track_object = pctl.master_library[track_object]
	return track_object.is_network

def open_image(track_object: TrackClass):
	if type(track_object) is int:
		track_object = pctl.master_library[track_object]
	album_art_gen.open_external(track_object)


def extract_image_deco(track_object: TrackClass):
	if type(track_object) is int:
		track_object = pctl.master_library[track_object]
	info = album_art_gen.get_info(track_object)

	if info is None:
		return [colours.menu_text_disabled, colours.menu_background, None]

	if info[0] == 1:
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled

	return [line_colour, colours.menu_background, None]


picture_menu.add(MenuItem(_("Open Image"), open_image, open_image_deco, pass_ref=True, pass_ref_deco=True, disable_test=open_image_disable_test))


def cycle_image_deco(track_object: TrackClass):
	info = album_art_gen.get_info(track_object)

	if pctl.playing_state != 0 and (info is not None and info[1] > 1):
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled

	return [line_colour, colours.menu_background, None]

def cycle_image_gal_deco(track_object: TrackClass):
	if type(track_object) is int:
		track_object = pctl.master_library[track_object]
	info = album_art_gen.get_info(track_object)

	if info is not None and info[1] > 1:
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled

	return [line_colour, colours.menu_background, None]

def cycle_offset(track_object: TrackClass):
	if type(track_object) is int:
		track_object = pctl.master_library[track_object]
	album_art_gen.cycle_offset(track_object)


def cycle_offset_back(track_object: TrackClass):
	if type(track_object) is int:
		track_object = pctl.master_library[track_object]
	album_art_gen.cycle_offset_reverse(track_object)


# Next and previous pictures
picture_menu.add(MenuItem(_("Next Image"), cycle_offset, cycle_image_deco, pass_ref=True, pass_ref_deco=True))
#picture_menu.add(_("Previous"), cycle_offset_back, cycle_image_deco, pass_ref=True, pass_ref_deco=True)

# Extract embedded artwork from file
picture_menu.add(MenuItem(_("Extract Image"), save_embed_img, extract_image_deco, pass_ref=True, pass_ref_deco=True, disable_test=save_embed_img_disable_test))


def dl_art_deco(track_object: TrackClass):
	if type(track_object) is int:
		track_object = pctl.master_library[track_object]
	if not track_object.album or not track_object.artist:
		return [colours.menu_text_disabled, colours.menu_background, None]
	return [colours.menu_text, colours.menu_background, None]


def download_art1(tr):
	if tr.is_network:
		show_message(_("Cannot download art for network tracks."))
		return

	# Determine noise of folder ----------------
	siblings = []
	parent = tr.parent_folder_path

	for pl in pctl.multi_playlist:
		for ti in pl.playlist_ids:
			tr = pctl.get_track(ti)
			if tr.parent_folder_path == parent:
				siblings.append(tr)

	album_tags = []
	date_tags = []

	for tr in siblings:
		album_tags.append(tr.album)
		date_tags.append(tr.date)

	album_tags = set(album_tags)
	date_tags = set(date_tags)

	if len(album_tags) > 2 or len(date_tags) > 2:
		show_message(_("It doesn't look like this folder belongs to a single album, sorry"))
		return

	# -------------------------------------------

	if not os.path.isdir(tr.parent_folder_path):
		show_message(_("Directory missing."))
		return

	try:
		show_message(_("Looking up MusicBrainz ID..."))

		if "musicbrainz_releasegroupid" not in tr.misc or "musicbrainz_artistids" not in tr.misc or not tr.misc[
			"musicbrainz_artistids"]:

			logging.info("MusicBrainz ID lookup...")

			artist = tr.album_artist
			if not tr.album:
				return
			if not artist:
				artist = tr.artist

			s = musicbrainzngs.search_release_groups(tr.album, artist=artist, limit=1)

			album_id = s["release-group-list"][0]["id"]
			artist_id = s["release-group-list"][0]["artist-credit"][0]["artist"]["id"]

			logging.info("Found release group ID: " + album_id)
			logging.info("Found artist ID: " + artist_id)

		else:

			album_id = tr.misc["musicbrainz_releasegroupid"]
			artist_id = tr.misc["musicbrainz_artistids"][0]

			logging.info("Using tagged release group ID: " + album_id)
			logging.info("Using tagged artist ID: " + artist_id)

		if prefs.enable_fanart_cover:
			try:
				show_message(_("Searching fanart.tv for cover art..."))

				r = requests.get("https://webservice.fanart.tv/v3/music/albums/" \
					+ artist_id + "?api_key=" + prefs.fatvap, timeout=(4, 10))

				artlink = r.json()["albums"][album_id]["albumcover"][0]["url"]
				id = r.json()["albums"][album_id]["albumcover"][0]["id"]

				response = urllib.request.urlopen(artlink, context=ssl_context)
				info = response.info()

				t = io.BytesIO()
				t.seek(0)
				t.write(response.read())
				t.seek(0, 2)
				l = t.tell()
				t.seek(0)

				if info.get_content_maintype() == "image" and l > 1000:

					if info.get_content_subtype() == "jpeg":
						filepath = os.path.join(tr.parent_folder_path, "cover-" + id + ".jpg")
					elif info.get_content_subtype() == "png":
						filepath = os.path.join(tr.parent_folder_path, "cover-" + id + ".png")
					else:
						show_message(_("Could not detect downloaded filetype."), mode="error")
						return

					f = open(filepath, "wb")
					f.write(t.read())
					f.close()

					show_message(_("Cover art downloaded from fanart.tv"), mode="done")
					# clear_img_cache()
					for track_id in default_playlist:
						if tr.parent_folder_path == pctl.get_track(track_id).parent_folder_path:
							clear_track_image_cache(pctl.get_track(track_id))
					return
			except Exception:
				logging.exception("Failed to get from fanart.tv")

		show_message(_("Searching MusicBrainz for cover art..."))
		t = io.BytesIO(musicbrainzngs.get_release_group_image_front(album_id, size=None))
		l = 0
		t.seek(0, 2)
		l = t.tell()
		t.seek(0)
		if l > 1000:
			filepath = os.path.join(tr.parent_folder_path, album_id + ".jpg")
			f = open(filepath, "wb")
			f.write(t.read())
			f.close()

			show_message(_("Cover art downloaded from MusicBrainz"), mode="done")
			# clear_img_cache()
			clear_track_image_cache(tr)

			for track_id in default_playlist:
				if tr.parent_folder_path == pctl.get_track(track_id).parent_folder_path:
					clear_track_image_cache(pctl.get_track(track_id))

			return

	except Exception:
		logging.exception("Matching cover art or ID could not be found.")
		show_message(_("Matching cover art or ID could not be found."))


def download_art1_fire_disable_test(track_object: TrackClass):
	if type(track_object) is int:
		track_object = pctl.master_library[track_object]
	return track_object.is_network

def download_art1_fire(track_object: TrackClass):
	if type(track_object) is int:
		track_object = pctl.master_library[track_object]
	shoot_dl = threading.Thread(target=download_art1, args=[track_object])
	shoot_dl.daemon = True
	shoot_dl.start()


def remove_embed_picture(track_object: TrackClass, dry: bool = True) -> int | None:
	"""Return amount of removed objects or None"""
	index = track_object.index

	if key_shift_down or key_shiftr_down:
		tracks = [index]
		if track_object.is_cue or track_object.is_network:
			show_message(_("Error - No handling for this kind of track"), mode="warning")
			return None
	else:
		tracks = []
		original_parent_folder = track_object.parent_folder_name
		for k in default_playlist:
			tr = pctl.get_track(k)
			if original_parent_folder == tr.parent_folder_name:
				tracks.append(k)

	removed = 0
	if not dry:
		pr = pctl.stop(True)
	try:
		for item in tracks:

			tr = pctl.get_track(item)

			if tr.is_cue:
				continue

			if tr.is_network:
				continue

			if dry:
				removed += 1
			else:
				if tr.file_ext == "MP3":
					try:
						tag = mutagen.id3.ID3(tr.fullpath)
						tag.delall("APIC")
						remove = True
						tag.save(padding=no_padding)
						removed += 1
					except Exception:
						logging.exception("No MP3 APIC found")

				if tr.file_ext == "M4A":
					try:
						tag = mutagen.mp4.MP4(tr.fullpath)
						del tag.tags["covr"]
						tag.save(padding=no_padding)
						removed += 1
					except Exception:
						logging.exception("No m4A covr tag found")

				if tr.file_ext in ("OGA", "OPUS", "OGG"):
					show_message(_("Removing vorbis image not implemented"))
					# try:
					#	 tag = mutagen.File(tr.fullpath).tags
					#	 logging.info(tag)
					#	 removed += 1
					# except Exception:
					#	 logging.exception("Failed to manipulate tags")

				if tr.file_ext == "FLAC":
					try:
						tag = mutagen.flac.FLAC(tr.fullpath)
						tag.clear_pictures()
						tag.save(padding=no_padding)
						removed += 1
					except Exception:
						logging.exception("Failed to save tags on FLAC")

				clear_track_image_cache(tr)

	except Exception:
		logging.exception("Image remove error")
		show_message(_("Image remove error"), mode="error")
		return None

	if dry:
		return removed

	if removed == 0:
		show_message(_("Image removal failed."), mode="error")
		return None
	if removed == 1:
		show_message(_("Deleted embedded picture from file"), mode="done")
	else:
		show_message(_("{N} files processed").local(N=removed), mode="done")
	if pr == 1:
		pctl.revert()


del_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "del.png", True)
delete_icon = MenuIcon(del_icon)


def delete_file_image(track_object: TrackClass):
	try:
		showc = album_art_gen.get_info(track_object)
		if showc is not None and showc[0] == 0:
			source = album_art_gen.get_sources(track_object)[showc[2]][1]
			os.remove(source)
			# clear_img_cache()
			clear_track_image_cache(track_object)
			logging.info("Deleted file: " + source)
	except Exception:
		logging.exception("Failed to delete file")
		show_message(_("Something went wrong"), mode="error")


def delete_track_image_deco(track_object: TrackClass):
	if type(track_object) is int:
		track_object = pctl.master_library[track_object]
	info = album_art_gen.get_info(track_object)

	text = _("Delete Image File")
	line_colour = colours.menu_text

	if info is None or track_object.is_network:
		return [colours.menu_text_disabled, colours.menu_background, None]

	if info and info[0] == 0:
		text = _("Delete Image File")

	elif info and info[0] == 1:
		if pctl.playing_state > 0 and track_object.file_ext in ("MP3", "FLAC", "M4A"):
			line_colour = colours.menu_text
		else:
			line_colour = colours.menu_text_disabled

		text = _("Delete Embedded | Folder")
		if key_shift_down or key_shiftr_down:
			text = _("Delete Embedded | Track")

	return [line_colour, colours.menu_background, text]


def delete_track_image(track_object: TrackClass):
	if type(track_object) is int:
		track_object = pctl.master_library[track_object]
	if track_object.is_network:
		return
	info = album_art_gen.get_info(track_object)
	if info and info[0] == 0:
		delete_file_image(track_object)
	elif info and info[0] == 1:
		n = remove_embed_picture(track_object, dry=True)
		gui.message_box_confirm_callback = remove_embed_picture
		gui.message_box_confirm_reference = (track_object, False)
		show_message(_("This will erase any embedded image in {N} files. Are you sure?").format(N=n), mode="confirm")



picture_menu.add(
	MenuItem(_("Delete Image File"), delete_track_image, delete_track_image_deco, pass_ref=True,
	pass_ref_deco=True, icon=delete_icon))

picture_menu.add(MenuItem(_("Quick-Fetch Cover Art"), download_art1_fire, dl_art_deco, pass_ref=True, pass_ref_deco=True, disable_test=download_art1_fire_disable_test))


def toggle_gimage(mode: int = 0) -> bool:
	if mode == 1:
		return prefs.show_gimage
	prefs.show_gimage ^= True
	return None


def search_image_deco(track_object: TrackClass):
	if track_object.artist and track_object.album:
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled

	return [line_colour, colours.menu_background, None]


def ser_gimage(track_object: TrackClass):
	if track_object.artist and track_object.album:
		line = "https://www.google.com/search?tbm=isch&q=" + urllib.parse.quote(
			track_object.artist + " " + track_object.album)
		webbrowser.open(line, new=2, autoraise=True)


# picture_menu.add(_('Search Google for Images'), ser_gimage, search_image_deco, pass_ref=True, pass_ref_deco=True, show_test=toggle_gimage)

# picture_menu.add(_('Toggle art box'), toggle_side_art, toggle_side_art_deco)

picture_menu.add(MenuItem(_("Search for Lyrics"), get_lyric_wiki, search_lyrics_deco, pass_ref=True, pass_ref_deco=True))
picture_menu.add(MenuItem(_("Toggle Lyrics"), toggle_lyrics, toggle_lyrics_deco, pass_ref=True, pass_ref_deco=True))

gallery_menu.add_to_sub(0, MenuItem(_("Next"), cycle_offset, cycle_image_gal_deco, pass_ref=True, pass_ref_deco=True))
gallery_menu.add_to_sub(0, MenuItem(_("Previous"), cycle_offset_back, cycle_image_gal_deco, pass_ref=True, pass_ref_deco=True))
gallery_menu.add_to_sub(0, MenuItem(_("Open Image"), open_image, open_image_deco, pass_ref=True, pass_ref_deco=True, disable_test=open_image_disable_test))
gallery_menu.add_to_sub(0, MenuItem(_("Extract Image"), save_embed_img, extract_image_deco, pass_ref=True, pass_ref_deco=True, disable_test=save_embed_img_disable_test))
gallery_menu.add_to_sub(0, MenuItem(_("Delete Image <combined>"), delete_track_image, delete_track_image_deco, pass_ref=True, pass_ref_deco=True)) #, icon=delete_icon)
gallery_menu.add_to_sub(0, MenuItem(_("Quick-Fetch Cover Art"), download_art1_fire, dl_art_deco, pass_ref=True, pass_ref_deco=True, disable_test=download_art1_fire_disable_test))

def append_here():
	global cargo
	global default_playlist
	default_playlist += cargo


def paste_deco():
	active = False
	line = None
	if len(cargo) > 0:
		active = True
	elif SDL_HasClipboardText():
		text = copy_from_clipboard()
		if text.startswith(("/", "spotify")) or "file://" in text:
			active = True
		elif prefs.spot_mode and text.startswith("https://open.spotify.com/album/"):  # or text.startswith("https://open.spotify.com/track/"):
			active = True
			line = _("Paste Spotify Album")

	if active:
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled

	return [line_colour, colours.menu_background, line]


def lightning_move_test(discard):
	return gui.lightning_copy and prefs.show_transfer


# def copy_deco():
#	 line = "Copy"
#	 if key_shift_down:
#		 line = "Copy" #Folder From Library"
#	 else:
#		 line = "Copy"
#
#
#	 return [colours.menu_text, colours.menu_background, line]


# playlist_menu.add('Paste', append_here, paste_deco)

def unique_template(string):
	return "<t>" in string or \
		"<title>" in string or \
		"<n>" in string or \
		"<number>" in string or \
		"<tracknumber>" in string or \
		"<tn>" in string or \
		"<sn>" in string or \
		"<singlenumber>" in string or \
		"<s>" in string or "%t" in string or "%tn" in string


def re_template_word(word, tr):
	if word == "aa" or word == "albumartist":

		if tr.album_artist:
			return tr.album_artist
		return tr.artist

	if word == "a" or word == "artist":
		return tr.artist

	if word == "t" or word == "title":
		return tr.title

	if word == "n" or word == "number" or word == "tracknumber" or word == "tn":
		if len(str(tr.track_number)) < 2:
			return "0" + str(tr.track_number)
		return str(tr.track_number)

	if word == "sn" or word == "singlenumber" or word == "singletracknumber" or word == "s":
		return str(tr.track_number)

	if word == "d" or word == "date" or word == "year":
		return str(tr.date)

	if word == "b" or "album" in word:
		return str(tr.album)

	if word == "g" or word == "genre":
		return tr.genre

	if word == "x" or "ext" in word or "file" in word:
		return tr.file_ext.lower()

	if word == "ux" or "upper" in word:
		return tr.file_ext.upper()

	if word == "c" or "composer" in word:
		return tr.composer

	if "comment" in word:
		return tr.comment.replace("\n", "").replace("\r", "")

	return ""


def parse_template2(string: str, track_object: TrackClass, strict: bool = False):
	temp = ""
	out = ""

	mode = 0

	for c in string:

		if mode == 0:

			if c == "<":
				mode = 1
			else:
				out += c

		else:

			if c == ">":

				test = re_template_word(temp, track_object)
				if strict:
					assert test
				out += test

				mode = 0
				temp = ""

			else:

				temp += c

	if "<und" in string:
		out = out.replace(" ", "_")

	return parse_template(out, track_object, strict=strict)


def parse_template(string, track_object: TrackClass, up_ext: bool = False, strict: bool = False):
	set = 0
	underscore = False
	output = ""

	while set < len(string):
		if string[set] == "%" and set < len(string) - 1:
			set += 1
			if string[set] == "n":
				if len(str(track_object.track_number)) < 2:
					output += "0"
				if strict:
					assert str(track_object.track_number)
				output += str(track_object.track_number)
			elif string[set] == "a":
				if up_ext and track_object.album_artist != "":  # Context of renaming a folder
					output += track_object.album_artist
				else:
					if strict:
						assert track_object.artist
					output += track_object.artist
			elif string[set] == "t":
				if strict:
					assert track_object.title
				output += track_object.title
			elif string[set] == "c":
				if strict:
					assert track_object.composer
				output += track_object.composer
			elif string[set] == "d":
				if strict:
					assert track_object.date
				output += track_object.date
			elif string[set] == "b":
				if strict:
					assert track_object.album
				output += track_object.album
			elif string[set] == "x":
				if up_ext:
					output += track_object.file_ext.upper()
				else:
					output += "." + track_object.file_ext.lower()
			elif string[set] == "u":
				underscore = True
		else:
			output += string[set]
		set += 1

	output = output.rstrip(" -").lstrip(" -")

	if underscore:
		output = output.replace(" ", "_")

	# Attempt to ensure the output text is filename safe
	output = filename_safe(output)

	return output


# Create playlist tab menu
tab_menu = Menu(160, show_icons=True)
radio_tab_menu = Menu(160, show_icons=True)


def rename_playlist(index, generator: bool = False) -> None:
	gui.rename_playlist_box = True
	rename_playlist_box.edit_generator = False
	rename_playlist_box.playlist_index = index
	rename_playlist_box.x = mouse_position[0]
	rename_playlist_box.y = mouse_position[1]

	if generator:
		rename_playlist_box.y = window_size[1] // 2 - round(200 * gui.scale)
		rename_playlist_box.x = window_size[0] // 2 - round(250 * gui.scale)

	rename_playlist_box.y = min(rename_playlist_box.y, round(350 * gui.scale))

	if rename_playlist_box.y < gui.panelY:
		rename_playlist_box.y = gui.panelY + 10 * gui.scale

	if gui.radio_view:
		rename_text_area.set_text(pctl.radio_playlists[index]["name"])
	else:
		rename_text_area.set_text(pctl.multi_playlist[index].title)
	rename_text_area.highlight_all()
	gui.gen_code_errors = False

	if generator:
		rename_playlist_box.toggle_edit_gen()


def edit_generator_box(index: int) -> None:
	rename_playlist(index, generator=True)


tab_menu.add(MenuItem(_("Rename"), rename_playlist, pass_ref=True, hint="Ctrl+R"))
radio_tab_menu.add(MenuItem(_("Rename"), rename_playlist, pass_ref=True, hint="Ctrl+R"))


def pin_playlist_toggle(pl: int) -> None:
	pctl.multi_playlist[pl].hidden ^= True


def pl_pin_deco(pl: int):
	# if pctl.multi_playlist[pl].hidden == True and tab_menu.pos[1] >

	if pctl.multi_playlist[pl].hidden == True:
		return [colours.menu_text, colours.menu_background, _("Pin")]
	return [colours.menu_text, colours.menu_background, _("Unpin")]


tab_menu.add(MenuItem("Pin", pin_playlist_toggle, pl_pin_deco, pass_ref=True, pass_ref_deco=True))


def pl_lock_deco(pl: int):
	if pctl.multi_playlist[pl].locked == True:
		return [colours.menu_text, colours.menu_background, _("Unlock")]
	return [colours.menu_text, colours.menu_background, _("Lock")]


def view_pl_is_locked(_) -> bool:
	return pctl.multi_playlist[pctl.active_playlist_viewing].locked


def pl_is_locked(pl: int) -> bool:
	if not pctl.multi_playlist:
		return False
	return pctl.multi_playlist[pl].locked


def lock_playlist_toggle(pl: int) -> None:
	pctl.multi_playlist[pl].locked ^= True


def lock_colour_callback():
	if pctl.multi_playlist[gui.tab_menu_pl].locked:
		if colours.lm:
			return [230, 180, 60, 255]
		return [240, 190, 10, 255]
	return None


lock_asset = asset_loader(scaled_asset_directory, loaded_asset_dc, "lock.png", True)
lock_icon = MenuIcon(lock_asset)
lock_icon.base_asset_mod = asset_loader(scaled_asset_directory, loaded_asset_dc, "unlock.png", True)
lock_icon.colour = [240, 190, 10, 255]
lock_icon.colour_callback = lock_colour_callback
lock_icon.xoff = 4
lock_icon.yoff = -1

tab_menu.add(MenuItem(_("Lock"), lock_playlist_toggle, pl_lock_deco,
	pass_ref=True, pass_ref_deco=True, icon=lock_icon, show_test=test_shift))


def export_m3u(pl: int, direc: str | None = None, relative: bool = False, show: bool = True) -> int | str:
	if len(pctl.multi_playlist[pl].playlist_ids) < 1:
		show_message(_("There are no tracks in this playlist. Nothing to export"))
		return 1

	if not direc:
		direc = str(user_directory / "playlists")
		if not os.path.exists(direc):
			os.makedirs(direc)
	target = os.path.join(direc, pctl.multi_playlist[pl].title + ".m3u")

	f = open(target, "w", encoding="utf-8")
	f.write("#EXTM3U")
	for number in pctl.multi_playlist[pl].playlist_ids:
		track = pctl.master_library[number]
		title = track.artist
		if title:
			title += " - "
		title += track.title

		if not track.is_network:
			f.write("\n#EXTINF:")
			f.write(str(round(track.length)))
			if title:
				f.write(f",{title}")
			path = track.fullpath
			if relative:
				path = os.path.relpath(path, start=direc)
			f.write(f"\n{path}")
	f.close()

	if show:
		line = direc
		line += "/"
		if system == "Windows" or msys:
			os.startfile(line)
		elif macos:
			subprocess.Popen(["open", line])
		else:
			subprocess.Popen(["xdg-open", line])
	return target


def export_xspf(pl: int, direc: str | None = None, relative: bool = False, show: bool = True) -> int | str:
	if len(pctl.multi_playlist[pl].playlist_ids) < 1:
		show_message(_("There are no tracks in this playlist. Nothing to export"))
		return 1

	if not direc:
		direc = str(user_directory / "playlists")
		if not os.path.exists(direc):
			os.makedirs(direc)

	target = os.path.join(direc, pctl.multi_playlist[pl].title + ".xspf")

	xspf_root = ET.Element("playlist", version="1", xmlns="http://xspf.org/ns/0/")
	xspf_tracklist_tag = ET.SubElement(xspf_root, "trackList")

	for number in pctl.multi_playlist[pl].playlist_ids:
		track = pctl.master_library[number]
		path = track.fullpath
		if relative:
			path = os.path.relpath(path, start=direc)

		xspf_track_tag = ET.SubElement(xspf_tracklist_tag, "track")
		if track.title != "":
			ET.SubElement(xspf_track_tag, "title").text = track.title
		if track.is_cue is False and track.fullpath != "":
			ET.SubElement(xspf_track_tag, "location").text = urllib.parse.quote(path)
		if track.artist != "":
			ET.SubElement(xspf_track_tag, "creator").text = track.artist
		if track.album != "":
			ET.SubElement(xspf_track_tag, "album").text = track.album
		if track.track_number != "":
			ET.SubElement(xspf_track_tag, "trackNum").text = str(track.track_number)

		ET.SubElement(xspf_track_tag, "duration").text = str(int(track.length * 1000))

	xspf_tree = ET.ElementTree(xspf_root)
	ET.indent(xspf_tree, space='  ', level=0)
	xspf_tree.write(target, encoding='UTF-8', xml_declaration=True)

	if show:
		line = direc
		line += "/"
		if system == "Windows" or msys:
			os.startfile(line)
		elif macos:
			subprocess.Popen(["open", line])
		else:
			subprocess.Popen(["xdg-open", line])

	return target


def reload():
	if album_mode:
		reload_albums(quiet=True)

	# tree_view_box.clear_all()
	# elif gui.combo_mode:
	#	 reload_albums(quiet=True)
	#	 combo_pl_render.prep()


def clear_playlist(index: int):
	global default_playlist

	if pl_is_locked(index):
		show_message(_("Playlist is locked to prevent accidental erasure"))
		return

	pctl.multi_playlist[index].last_folder.clear()  # clear import folder list # TODO(Martin): This was actually a string not a list wth?

	if not pctl.multi_playlist[index].playlist_ids:
		logging.info("Playlist is already empty")
		return

	li = []
	for i, ref in enumerate(pctl.multi_playlist[index].playlist_ids):
		li.append((i, ref))

	undo.bk_tracks(index, list(reversed(li)))

	del pctl.multi_playlist[index].playlist_ids[:]
	if pctl.active_playlist_viewing == index:
		default_playlist = pctl.multi_playlist[index].playlist_ids
		reload()

	# pctl.playlist_playing = 0
	pctl.multi_playlist[index].position = 0
	if index == pctl.active_playlist_viewing:
		pctl.playlist_view_position = 0

	gui.pl_update = 1


def convert_playlist(pl: int, get_list: bool = False) -> list[list[int]]| None:
	global transcode_list

	if not tauon.test_ffmpeg():
		return None

	paths: list[str] = []
	folders: list[list[int]] = []

	for track in pctl.multi_playlist[pl].playlist_ids:
		if pctl.master_library[track].parent_folder_path not in paths:
			paths.append(pctl.master_library[track].parent_folder_path)

	for path in paths:
		folder: list[int] = []
		for track in pctl.multi_playlist[pl].playlist_ids:
			if pctl.master_library[track].parent_folder_path == path:
				folder.append(track)
				if prefs.transcode_codec == "flac" and pctl.master_library[track].file_ext.lower() in (
					"mp3", "opus",
					"m4a", "mp4",
					"ogg", "aac"):
					show_message(_("This includes the conversion of a lossy codec to a lossless one!"))

		folders.append(folder)

	if get_list:
		return folders

	transcode_list.extend(folders)


def get_folder_tracks_local(pl_in: int) -> list[int]:
	selection = []
	parent = os.path.normpath(pctl.master_library[default_playlist[pl_in]].parent_folder_path)
	while pl_in < len(default_playlist) and parent == os.path.normpath(
			pctl.master_library[default_playlist[pl_in]].parent_folder_path):
		selection.append(pl_in)
		pl_in += 1
	return selection


def test_pl_tab_locked(pl: int) -> bool:
	if gui.radio_view:
		return False
	return pctl.multi_playlist[pl].locked


# Clear playlist
tab_menu.add(MenuItem(_("Clear"), clear_playlist, pass_ref=True, disable_test=test_pl_tab_locked, pass_ref_deco=True))


def move_radio_playlist(source, dest):
	if dest > source:
		dest += 1
	try:
		temp = pctl.radio_playlists[source]
		pctl.radio_playlists[source] = "old"
		pctl.radio_playlists.insert(dest, temp)
		pctl.radio_playlists.remove("old")
		pctl.radio_playlist_viewing = pctl.radio_playlists.index(temp)
	except Exception:
		logging.exception("Playlist move error")


def move_playlist(source, dest):
	global default_playlist
	if dest > source:
		dest += 1
	try:
		active = pctl.multi_playlist[pctl.active_playlist_playing]
		view = pctl.multi_playlist[pctl.active_playlist_viewing]

		temp = pctl.multi_playlist[source]
		pctl.multi_playlist[source] = "old"
		pctl.multi_playlist.insert(dest, temp)
		pctl.multi_playlist.remove("old")

		pctl.active_playlist_playing = pctl.multi_playlist.index(active)
		pctl.active_playlist_viewing = pctl.multi_playlist.index(view)
		default_playlist = default_playlist = pctl.multi_playlist[pctl.active_playlist_viewing].playlist_ids
	except Exception:
		logging.exception("Playlist move error")


def delete_playlist(index: int, force: bool = False, check_lock: bool = False) -> None:
	if gui.radio_view:
		del pctl.radio_playlists[index]
		if not pctl.radio_playlists:
			pctl.radio_playlists = [{"uid": uid_gen(), "name": "Default", "items": []}]
		return

	global default_playlist

	if check_lock and pl_is_locked(index):
		show_message(_("Playlist is locked to prevent accidental deletion"))
		return

	if not force:
		if pl_is_locked(index):
			show_message(_("Playlist is locked to prevent accidental deletion"))
			return

	if gui.rename_playlist_box:
		return

	# Set screen to be redrawn
	gui.pl_update = 1
	gui.update += 1

	# Backup the playlist to be deleted
	# pctl.playlist_backup.append(pctl.multi_playlist[index])
	# pctl.playlist_backup.append(pctl.multi_playlist[index])
	undo.bk_playlist(index)

	# If we're deleting the final playlist, delete it and create a blank one in place
	if len(pctl.multi_playlist) == 1:
		logging.warning("Deleting final playlist and creating a new Default one")
		pctl.multi_playlist.clear()
		pctl.multi_playlist.append(pl_gen())
		default_playlist = pctl.multi_playlist[0].playlist_ids
		pctl.active_playlist_playing = 0
		return

	# Take note of the id of the playing playlist
	old_playing_id = pctl.multi_playlist[pctl.active_playlist_playing].uuid_int

	# Take note of the id of the viewed open playlist
	old_view_id = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int

	# Delete the requested playlist
	del pctl.multi_playlist[index]

	# Re-set the open viewed playlist number by uid
	for i, pl in enumerate(pctl.multi_playlist):

		if pl.uuid_int == old_view_id:
			pctl.active_playlist_viewing = i
			break
	else:
		# logging.info("Lost the viewed playlist!")
		# Try find the playing playlist and make it the viewed playlist
		for i, pl in enumerate(pctl.multi_playlist):
			if pl.uuid_int == old_playing_id:
				pctl.active_playlist_viewing = i
				break
		else:
			# Playing playlist was deleted, lets just move down one playlist
			if pctl.active_playlist_viewing > 0:
				pctl.active_playlist_viewing -= 1

	# Re-initiate the now viewed playlist
	if old_view_id != pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int:
		default_playlist = pctl.multi_playlist[pctl.active_playlist_viewing].playlist_ids
		pctl.playlist_view_position = pctl.multi_playlist[pctl.active_playlist_viewing].position
		logging.debug("Position reset by playlist delete")
		pctl.selected_in_playlist = pctl.multi_playlist[pctl.active_playlist_viewing].selected
		shift_selection = [pctl.selected_in_playlist]

		if album_mode:
			reload_albums(True)
			goto_album(pctl.playlist_view_position)

	# Re-set the playing playlist number by uid
	for i, pl in enumerate(pctl.multi_playlist):

		if pl.uuid_int == old_playing_id:
			pctl.active_playlist_playing = i
			break
	else:
		logging.info("Lost the playing playlist!")
		pctl.active_playlist_playing = pctl.active_playlist_viewing
		pctl.playlist_playing_position = -1

	test_show_add_home_music()

	# Cleanup
	ids = []
	for p in pctl.multi_playlist:
		ids.append(p.uuid_int)

	for key in list(gui.gallery_positions.keys()):
		if key not in ids:
			del gui.gallery_positions[key]
	for key in list(pctl.gen_codes.keys()):
		if key not in ids:
			del pctl.gen_codes[key]

	pctl.db_inc += 1

to_scan = []


def delete_playlist_force(index: int):
	delete_playlist(index, force=True, check_lock=True)


def delete_playlist_by_id(id: int, force: bool = False, check_lock: bool = False) -> None:
	delete_playlist(id_to_pl(id), force=force, check_lock=check_lock)


def delete_playlist_ask(index: int):
	print("ark")
	if gui.radio_view:
		delete_playlist_force(index)
		return
	gen = pctl.gen_codes.get(pl_to_id(index), "")
	if (gen and not gen.startswith("self ")) or len(pctl.multi_playlist[index].playlist_ids) < 2:
		delete_playlist(index)
		return

	gui.message_box_confirm_callback = delete_playlist_by_id
	gui.message_box_confirm_reference = (pl_to_id(index), True, True)
	show_message(_("Are you sure you want to delete playlist: {name}?").format(name=pctl.multi_playlist[index].title), mode="confirm")


def rescan_tags(pl: int) -> None:
	for track in pctl.multi_playlist[pl].playlist_ids:
		if pctl.master_library[track].is_cue is False:
			to_scan.append(track)
	tauon.thread_manager.ready("worker")


# def re_import(pl: int) -> None:
#
#	 path = pctl.multi_playlist[pl].last_folder
#	 if path == "":
#		 return
#	 for i in reversed(range(len(pctl.multi_playlist[pl].playlist_ids))):
#		 if path.replace('\\', '/') in pctl.master_library[pctl.multi_playlist[pl].playlist_ids[i]].parent_folder_path:
#			 del pctl.multi_playlist[pl].playlist_ids[i]
#
#	 load_order = LoadClass()
#	 load_order.replace_stem = True
#	 load_order.target = path
#	 load_order.playlist = pctl.multi_playlist[pl].uuid_int
#	 load_orders.append(copy.deepcopy(load_order))


def re_import2(pl: int) -> None:
	paths = pctl.multi_playlist[pl].last_folder

	reduce_paths(paths)

	for path in paths:
		if os.path.isdir(path):
			load_order = LoadClass()
			load_order.replace_stem = True
			load_order.target = path
			load_order.notify = True
			load_order.playlist = pctl.multi_playlist[pl].uuid_int
			load_orders.append(copy.deepcopy(load_order))

	if paths:
		show_message(_("Rescanning folders..."), mode="info")


def rescan_all_folders():
	for i, p in enumerate(pctl.multi_playlist):
		re_import2(i)

def s_append(index: int):
	paste(playlist_no=index)


def append_playlist(index: int):
	global cargo
	pctl.multi_playlist[index].playlist_ids += cargo

	gui.pl_update = 1
	reload()

def index_key(index: int):
	tr = pctl.master_library[index]
	s = str(tr.track_number)
	d = str(tr.disc_number)

	if "/" in d:
		d = d.split("/")[0]

	# Make sure the value for disc number is an int, make 1 if 0, otherwise ignore
	if d:
		try:
			dd = int(d)
			if dd < 2:
				dd = 1
			d = str(dd)
		except Exception:
			logging.exception("Failed to parse as index as int")
			d = ""


	# Add the disc number for sorting by CD, make it '1' if theres isnt one
	if s or d:
		if not d:
			s = "1" + "d" + s
		else:
			s = d + "d" + s

	# Use the filename if we dont have any metadata to sort by,
	# since it could likely have the track number in it
	else:
		s = tr.filename

	if (not tr.disc_number or tr.disc_number == "0") and tr.is_cue:
		s = tr.filename + "-" + s

	# This splits the line by groups of numbers, causing the sorting algorithum to sort
	# by those numbers. Should work for filenames, even with the disc number in the name
	try:
		return [tryint(c) for c in re.split("([0-9]+)", s)]
	except Exception:
		logging.exception("Failed to parse as int, returning 'a'")
		return "a"


def sort_tracK_numbers_album_only(pl: int, custom_list=None):
	current_folder = ""
	albums = []
	if custom_list is None:
		playlist = pctl.multi_playlist[pl].playlist_ids
	else:
		playlist = custom_list

	for i in range(len(playlist)):
		if i == 0:
			albums.append(i)
			current_folder = pctl.master_library[playlist[i]].album
		elif pctl.master_library[playlist[i]].album != current_folder:
			current_folder = pctl.master_library[playlist[i]].album
			albums.append(i)

	i = 0
	while i < len(albums) - 1:
		playlist[albums[i]:albums[i + 1]] = sorted(playlist[albums[i]:albums[i + 1]], key=index_key)
		i += 1
	if len(albums) > 0:
		playlist[albums[i]:] = sorted(playlist[albums[i]:], key=index_key)

	gui.pl_update += 1


def sort_track_2(pl: int, custom_list: list[int] | None = None) -> None:
	current_folder = ""
	current_album = ""
	current_date = ""
	albums = []
	if custom_list is None:
		playlist = pctl.multi_playlist[pl].playlist_ids
	else:
		playlist = custom_list

	for i in range(len(playlist)):
		tr = pctl.master_library[playlist[i]]
		if i == 0:
			albums.append(i)
			current_folder = tr.parent_folder_path
			current_album = tr.album
			current_date = tr.date
		elif tr.parent_folder_path != current_folder:
			if tr.album == current_album and tr.album and tr.date == current_date and tr.disc_number \
					and os.path.dirname(tr.parent_folder_path) == os.path.dirname(current_folder):
				continue
			current_folder = tr.parent_folder_path
			current_album = tr.album
			current_date = tr.date
			albums.append(i)

	i = 0
	while i < len(albums) - 1:
		playlist[albums[i]:albums[i + 1]] = sorted(playlist[albums[i]:albums[i + 1]], key=index_key)
		i += 1
	if len(albums) > 0:
		playlist[albums[i]:] = sorted(playlist[albums[i]:], key=index_key)

	gui.pl_update += 1


tauon.sort_track_2 = sort_track_2


def key_filepath(index: int):
	track = pctl.master_library[index]
	return track.parent_folder_path.lower(), track.filename


def key_fullpath(index: int):
	return pctl.master_library[index].fullpath


def key_filename(index: int):
	track = pctl.master_library[index]
	return track.filename


def sort_path_pl(pl: int, custom_list=None):
	if custom_list is not None:
		target = custom_list
	else:
		target = pctl.multi_playlist[pl].playlist_ids

	if use_natsort and False:
		target[:] = natsort.os_sorted(target, key=key_fullpath)
	else:
		target.sort(key=key_filepath)


def append_current_playing(index: int):
	if tauon.spot_ctl.coasting:
		tauon.spot_ctl.append_playing(index)
		gui.pl_update = 1
		return

	if pctl.playing_state > 0 and len(pctl.track_queue) > 0:
		pctl.multi_playlist[index].playlist_ids.append(pctl.track_queue[pctl.queue_step])
		gui.pl_update = 1


def export_stats(pl: int) -> None:
	playlist_time = 0
	play_time = 0
	total_size = 0
	tracks_in_playlist = len(pctl.multi_playlist[pl].playlist_ids)

	seen_files = {}
	seen_types = {}

	mp3_bitrates = {}
	ogg_bitrates = {}
	m4a_bitrates = {}

	are_cue = 0

	for index in pctl.multi_playlist[pl].playlist_ids:
		track = pctl.get_track(index)

		playlist_time += int(track.length)
		play_time += star_store.get(index)

		if track.is_cue:
			are_cue += 1

		if track.file_ext == "MP3":
			mp3_bitrates[track.bitrate] = mp3_bitrates.get(track.bitrate, 0) + 1
		if track.file_ext == "OGG" or track.file_ext == "OGA":
			ogg_bitrates[track.bitrate] = ogg_bitrates.get(track.bitrate, 0) + 1
		if track.file_ext == "M4A":
			m4a_bitrates[track.bitrate] = m4a_bitrates.get(track.bitrate, 0) + 1

		type = track.file_ext
		if type == "OGA":
			type = "OGG"
		seen_types[type] = seen_types.get(type, 0) + 1

		if track.fullpath and not track.is_network:
			if track.fullpath not in seen_files:
				size = track.size
				if not size and os.path.isfile(track.fullpath):
					size = os.path.getsize(track.fullpath)
				seen_files[track.fullpath] = size

	total_size = sum(seen_files.values())

	stats_gen.update(pl)
	line = _("Playlist:") + "\n" + pctl.multi_playlist[pl].title + "\n\n"
	line += _("Generated:") + "\n" + time.strftime("%c") + "\n\n"
	line += _("Tracks in playlist:") + "\n" + str(tracks_in_playlist)
	line += "\n\n"
	line += _("Repeats in playlist:") + "\n"
	unique = len(set(pctl.multi_playlist[pl].playlist_ids))
	line += str(tracks_in_playlist - unique)
	line += "\n\n"
	line += _("Total local size:") + "\n" + get_filesize_string(total_size) + "\n\n"
	line += _("Playlist duration:") + "\n" + str(datetime.timedelta(seconds=int(playlist_time))) + "\n\n"
	line += _("Total playtime:") + "\n" + str(datetime.timedelta(seconds=int(play_time))) + "\n\n"

	line += _("Track types:") + "\n"
	if tracks_in_playlist:
		types = sorted(seen_types, key=seen_types.get, reverse=True)
		for type in types:
			perc = round((seen_types.get(type) / tracks_in_playlist) * 100, 1)
			if perc < 0.1:
				perc = "<0.1"
			if type == "SPOT":
				type = "SPOTIFY"
			if type == "SUB":
				type = "AIRSONIC"
			line += f"{type} ({perc}%); "
	line = line.rstrip("; ")
	line += "\n\n"

	if tracks_in_playlist:
		line += _("Percent of tracks are CUE type:") + "\n"
		perc = are_cue / tracks_in_playlist
		if perc == 0:
			perc = 0
		if 0 < perc < 0.01:
			perc = "<0.01"
		else:
			perc = round(perc, 2)

		line += str(perc) + "%"
		line += "\n\n"

	if tracks_in_playlist and mp3_bitrates:
		line += _("MP3 bitrates (kbps):") + "\n"
		rates = sorted(mp3_bitrates, key=mp3_bitrates.get, reverse=True)
		others = 0
		for rate in rates:
			perc = round((mp3_bitrates.get(rate) / sum(mp3_bitrates.values())) * 100, 1)
			if perc < 1:
				others += perc
			else:
				line += f"{rate} ({perc}%); "

		if others:
			others = round(others, 1)
			if others < 0.1:
				others = "<0.1"
			line += _("Others") + f"({others}%);"
		line = line.rstrip("; ")
		line += "\n\n"

	if tracks_in_playlist and ogg_bitrates:
		line += _("OGG bitrates (kbps):") + "\n"
		rates = sorted(ogg_bitrates, key=ogg_bitrates.get, reverse=True)
		others = 0
		for rate in rates:
			perc = round((ogg_bitrates.get(rate) / sum(ogg_bitrates.values())) * 100, 1)
			if perc < 1:
				others += perc
			else:
				line += f"{rate} ({perc}%); "

		if others:
			others = round(others, 1)
			if others < 0.1:
				others = "<0.1"
			line += _("Others") + f"({others}%);"
		line = line.rstrip("; ")
		line += "\n\n"

	# if tracks_in_playlist and m4a_bitrates:
	#	 line += "M4A bitrates (kbps):\n"
	#	 rates = sorted(m4a_bitrates, key=m4a_bitrates.get, reverse=True)
	#	 others = 0
	#	 for rate in rates:
	#		 perc = round((m4a_bitrates.get(rate) / sum(m4a_bitrates.values())) * 100, 1)
	#		 if perc < 1:
	#			 others += perc
	#		 else:
	#			 line += f"{rate} ({perc}%); "
	#
	#	 if others:
	#		 others = round(others, 1)
	#		 if others < 0.1:
	#			 others = "<0.1"
	#		 line += f"Others ({others}%);"
	#
	#	 line = line.rstrip("; ")
	#	 line += "\n\n"

	line += "\n" + f"-------------- {_('Top Artists')} --------------------" + "\n\n"

	ls = stats_gen.artist_list
	for i, item in enumerate(ls[:50]):
		line += str(i + 1) + ".\t" + stt2(item[1]) + "\t" + item[0] + "\n"

	line += "\n\n" + f"-------------- {_('Top Albums')} --------------------" + "\n\n"
	ls = stats_gen.album_list
	for i, item in enumerate(ls[:50]):
		line += str(i + 1) + ".\t" + stt2(item[1]) + "\t" + item[0] + "\n"
	line += "\n\n" + f"-------------- {_('Top Genres')} --------------------" + "\n\n"
	ls = stats_gen.genre_list
	for i, item in enumerate(ls[:50]):
		line += str(i + 1) + ".\t" + stt2(item[1]) + "\t" + item[0] + "\n"

	line = line.encode("utf-8")
	xport = (user_directory / "stats.txt").open("wb")
	xport.write(line)
	xport.close()
	target = str(user_directory / "stats.txt")
	if system == "Windows" or msys:
		os.startfile(target)
	elif macos:
		subprocess.call(["open", target])
	else:
		subprocess.call(["xdg-open", target])


def imported_sort(pl: int) -> None:
	if pl_is_locked(pl):
		show_message(_("Playlist is locked"))
		return

	og = pctl.multi_playlist[pl].playlist_ids
	og.sort(key=lambda x: pctl.get_track(x).index)

	reload_albums()
	tree_view_box.clear_target_pl(pl)

def imported_sort_folders(pl: int) -> None:
	if pl_is_locked(pl):
		show_message(_("Playlist is locked"))
		return

	og = pctl.multi_playlist[pl].playlist_ids
	og.sort(key=lambda x: pctl.get_track(x).index)

	first_occurrences = {}
	for i, x in enumerate(og):
		b = pctl.get_track(x).parent_folder_path
		if b not in first_occurrences:
			first_occurrences[b] = i

	og.sort(key=lambda x: first_occurrences[pctl.get_track(x).parent_folder_path])

	reload_albums()
	tree_view_box.clear_target_pl(pl)

def standard_sort(pl: int) -> None:
	if pl_is_locked(pl):
		show_message(_("Playlist is locked"))
		return

	sort_path_pl(pl)
	sort_track_2(pl)
	reload_albums()
	tree_view_box.clear_target_pl(pl)


def year_s(plt):
	sorted_temp = sorted(plt, key=lambda x: x[1])
	temp = []

	for album in sorted_temp:
		temp += album[0]
	return temp


def year_sort(pl: int, custom_list=None):
	if custom_list:
		playlist = custom_list
	else:
		playlist = pctl.multi_playlist[pl].playlist_ids
	plt = []
	pl2 = []
	artist = ""
	album_artist = ""

	p = 0
	while p < len(playlist):

		track = get_object(playlist[p])

		if track.artist != artist:
			if album_artist and track.album_artist and album_artist == track.album_artist:
				pass
			elif len(artist) > 5 and artist.lower() in track.parent_folder_name.lower():
				pass
			else:
				artist = track.artist
				pl2 += year_s(plt)
				plt = []

		if track.album_artist:
			album_artist = track.album_artist

		if p > len(playlist) - 1:
			break

		album = []
		on = get_object(playlist[p]).parent_folder_path
		album.append(playlist[p])
		t = 1

		while t + p < len(playlist) - 1 and get_object(playlist[p + t]).parent_folder_path == on:
			album.append(playlist[p + t])
			t += 1

		date = get_object(playlist[p]).date

		# If date is xx-xx-yyyy format, just grab the year from the end
		# so that the M and D don't interfere with the sorter
		if len(date) > 4 and date[-4:].isnumeric():
			date = date[-4:]

		# If we don't have a date, see if we can grab one from the folder name
		# following the format: (XXXX)
		if date == "":
			pfn = get_object(playlist[p]).parent_folder_name
			if len(pfn) > 6 and pfn[-1] == ")" and pfn[-6] == "(":
				date = pfn[-5:-1]

		plt.append((album, date, artist + " " + get_object(playlist[p]).album))
		p += len(album)
		#logging.info(album)

	if plt:
		pl2 += year_s(plt)
		plt = []

	if custom_list is not None:
		return pl2

	# We can't just assign the playlist because it may disconnect the 'pointer' default_playlist
	pctl.multi_playlist[pl].playlist_ids[:] = pl2[:]
	reload_albums()
	tree_view_box.clear_target_pl(pl)


def pl_toggle_playlist_break(ref):
	pctl.multi_playlist[ref].hide_title ^= 1
	gui.pl_update = 1


delete_icon.xoff = 3
delete_icon.colour = [249, 70, 70, 255]

tab_menu.add(MenuItem(_("Delete"),
	delete_playlist_force, pass_ref=True, hint="Ctrl+W", icon=delete_icon, disable_test=test_pl_tab_locked, pass_ref_deco=True))
radio_tab_menu.add(MenuItem(_("Delete"),
	delete_playlist_force, pass_ref=True, hint="Ctrl+W", icon=delete_icon, disable_test=test_pl_tab_locked, pass_ref_deco=True))


def gen_unique_pl_title(base: str, extra: str="", start: int = 1) -> str:
	ex = start
	title = base
	while ex < 100:
		for playlist in pctl.multi_playlist:
			if playlist.title == title:
				ex += 1
				if ex == 1:
					title = base + " (" + extra.rstrip(" ") + ")"
				else:
					title = base + " (" + extra + str(ex) + ")"
				break
		else:
			break

	return title


def new_playlist(switch: bool = True) -> int | None:
	if gui.radio_view:
		r = {}
		r["uid"] = uid_gen()
		r["name"] = _("New Radio List")
		r["items"] = []  # copy.copy(prefs.radio_urls)
		r["scroll"] = 0
		pctl.radio_playlists.append(r)
		return None

	title = gen_unique_pl_title(_("New Playlist"))

	top_panel.prime_side = 1
	top_panel.prime_tab = len(pctl.multi_playlist)

	pctl.multi_playlist.append(pl_gen(title=title))  # [title, 0, [], 0, 0, 0])
	if switch:
		switch_playlist(len(pctl.multi_playlist) - 1)
	return len(pctl.multi_playlist) - 1


heartx_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "heart-menu.png", True))
spot_heartx_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "heart-menu.png", True))
transcode_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "transcode.png", True))
mod_folder_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "mod_folder.png", True))
settings_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "settings2.png", True))
rename_tracks_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "pen.png", True))
add_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "new.png", True))
spot_asset = asset_loader(scaled_asset_directory, loaded_asset_dc, "spot.png", True)
spot_icon = MenuIcon(spot_asset)
spot_icon.colour = [30, 215, 96, 255]
spot_icon.xoff = 5
spot_icon.yoff = 2

jell_icon = MenuIcon(spot_asset)
jell_icon.colour = [190, 100, 210, 255]
jell_icon.xoff = 5
jell_icon.yoff = 2

tab_menu.br()


def append_deco():
	if pctl.playing_state > 0:
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled

	text = None
	if tauon.spot_ctl.coasting:
		text = _("Add Spotify Album")

	return [line_colour, colours.menu_background, text]


def rescan_deco(pl: int):
	if pctl.multi_playlist[pl].last_folder:
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled

	# base = os.path.basename(pctl.multi_playlist[pl].last_folder)

	return [line_colour, colours.menu_background, None]


def regenerate_deco(pl: int):
	id = pl_to_id(pl)
	value = pctl.gen_codes.get(id)

	if value:
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled

	return [line_colour, colours.menu_background, None]


column_names = (
	"Artist",
	"Album Artist",
	"Album",
	"Title",
	"Composer",
	"Time",
	"Date",
	"Genre",
	"#",
	"P",
	"Starline",
	"Rating",
	"Comment",
	"Codec",
	"Lyrics",
	"Bitrate",
	"S",
	"Filename",
	"Disc",
	"CUE",
)


def parse_generator(string: str):
	cmds = []
	quotes = []
	current = ""
	q_string = ""
	inquote = False
	for cha in string:
		if not inquote and cha == " ":
			if current:
				cmds.append(current)
				quotes.append(q_string)
			q_string = ""
			current = ""
			continue
		if cha == "\"":
			inquote ^= True

		current += cha

		if inquote and cha != "\"":
			q_string += cha

	if current:
		cmds.append(current)
		quotes.append(q_string)

	return cmds, quotes, inquote


def upload_spotify_playlist(pl: int):
	p_id = pl_to_id(pl)
	string = pctl.gen_codes.get(p_id)
	id = None
	if string:
		cmds, quotes, inquote = parse_generator(string)
		for i, cm in enumerate(cmds):
			if cm.startswith("spl\""):
				id = quotes[i]
				break

	urls = []
	playlist = pctl.multi_playlist[pl].playlist_ids

	warn = False
	for track_id in playlist:
		tr = pctl.get_track(track_id)
		url = tr.misc.get("spotify-track-url")
		if not url:
			warn = True
			continue
		urls.append(url)

	if warn:
		show_message(_("Playlist contains non-Spotify tracks"), mode="error")
		return

	new = False
	if id is None:
		name = pctl.multi_playlist[pl].title.split(" by ")[0]
		show_message(_("Created new Spotify playlist"), name, mode="done")
		id = tauon.spot_ctl.create_playlist(name)
		if id:
			new = True
			pctl.gen_codes[p_id] = "spl\"" + id + "\""
	if id is None:
		show_message(_("Error creating Spotify playlist"))
		return
	if not new:
		show_message(_("Updated Spotify playlist"), mode="done")
	tauon.spot_ctl.upload_playlist(id, urls)


def regenerate_playlist(pl: int = -1, silent: bool = False, id: int | None = None) -> None:
	if id is None and pl == -1:
		return

	if id is None:
		id = pl_to_id(pl)

	if pl == -1:
		pl = id_to_pl(id)
		if pl is None:
			return

	source_playlist = pctl.multi_playlist[pl].playlist_ids

	string = pctl.gen_codes.get(id)
	if not string:
		if not silent:
			show_message(_("This playlist has no generator"))
		return

	cmds, quotes, inquote = parse_generator(string)

	if inquote:
		gui.gen_code_errors = "close"
		return

	playlist = []
	selections = []
	errors = False
	selections_searched = 0

	def is_source_type(code: str | None) -> bool:
		return \
			code is None or \
			code == "" or \
			code.startswith(("self", "jelly", "plex", "koel", "tau", "air", "sal"))

	#logging.info(cmds)
	#logging.info(quotes)

	pctl.regen_in_progress = True

	for i, cm in enumerate(cmds):

		quote = quotes[i]

		if cm.startswith("\"") and (cm.endswith((">", "<"))):
			cm_found = False

			for col in column_names:

				if quote.lower() == col.lower() or _(quote).lower() == col.lower():
					cm_found = True

					if cm[-1] == ">":
						sort_ass(0, invert=False, custom_list=playlist, custom_name=col)
					elif cm[-1] == "<":
						sort_ass(0, invert=True, custom_list=playlist, custom_name=col)
					break
			if cm_found:
				continue

		elif cm == "self":
			selections.append(pctl.multi_playlist[pl].playlist_ids)

		elif cm == "auto":
			pass

		elif cm.startswith("spl\""):
			playlist.extend(tauon.spot_ctl.playlist(quote, return_list=True))

		elif cm.startswith("tpl\""):
			playlist.extend(tauon.tidal.playlist(quote, return_list=True))

		elif cm == "tfa":
			playlist.extend(tauon.tidal.fav_albums(return_list=True))

		elif cm == "tft":
			playlist.extend(tauon.tidal.fav_tracks(return_list=True))

		elif cm.startswith("tar\""):
			playlist.extend(tauon.tidal.artist(quote, return_list=True))

		elif cm.startswith("tmix\""):
			playlist.extend(tauon.tidal.mix(quote, return_list=True))

		elif cm == "sal":
			playlist.extend(tauon.spot_ctl.get_library_albums(return_list=True))

		elif cm == "slt":
			playlist.extend(tauon.spot_ctl.get_library_likes(return_list=True))

		elif cm == "plex":
			if not plex.scanning:
				playlist.extend(plex.get_albums(return_list=True))

		elif cm.startswith("jelly\""):
			if not jellyfin.scanning:
				playlist.extend(jellyfin.get_playlist(quote, return_list=True))

		elif cm == "jelly":
			if not jellyfin.scanning:
				playlist.extend(jellyfin.ingest_library(return_list=True))

		elif cm == "koel":
			if not koel.scanning:
				playlist.extend(koel.get_albums(return_list=True))

		elif cm == "tau":
			if not tau.processing:
				playlist.extend(tau.get_playlist(pctl.multi_playlist[pl].title, return_list=True))

		elif cm == "air":
			if not subsonic.scanning:
				playlist.extend(subsonic.get_music3(return_list=True))

		elif cm == "a":
			if not selections and not selections_searched:
				for plist in pctl.multi_playlist:
					code = pctl.gen_codes.get(plist.uuid_int)
					if is_source_type(code):
						selections.append(plist.playlist_ids)

			temp = []
			for selection in selections:
				temp += selection

			playlist += list(OrderedDict.fromkeys(temp))
			selections.clear()

		elif cm == "cue":

			for i in reversed(range(len(playlist))):
				tr = pctl.get_track(playlist[i])
				if not tr.is_cue:
					del playlist[i]
			playlist = list(OrderedDict.fromkeys(playlist))

		elif cm == "today":
			d = datetime.date.today()
			for i in reversed(range(len(playlist))):
				tr = pctl.get_track(playlist[i])
				if tr.date[5:7] != f"{d:%m}" or tr.date[8:10] != f"{d:%d}":
					del playlist[i]
			playlist = list(OrderedDict.fromkeys(playlist))

		elif cm.startswith("com\""):
			for i in reversed(range(len(playlist))):
				tr = pctl.get_track(playlist[i])
				if quote not in tr.comment:
					del playlist[i]
			playlist = list(OrderedDict.fromkeys(playlist))

		elif cm.startswith("ext"):
			value = quote.upper()
			if value:
				if not selections:
					for plist in pctl.multi_playlist:
						selections.append(plist.playlist_ids)

				temp = []
				for selection in selections:
					for track in selection:
						tr = pctl.get_track(track)
						if tr.file_ext == value:
							temp.append(track)

				playlist += list(OrderedDict.fromkeys(temp))

		elif cm == "ypa":
			playlist = year_sort(0, playlist)

		elif cm == "tn":
			sort_track_2(0, playlist)

		elif cm == "ia>":
			playlist = gen_last_imported_folders(0, playlist)

		elif cm == "ia<":
			playlist = gen_last_imported_folders(0, playlist, reverse=True)

		elif cm == "m>":
			playlist = gen_last_modified(0, playlist)

		elif cm == "m<":
			playlist = gen_last_modified(0, playlist, reverse=False)

		elif cm == "ly" or cm == "lyrics":
			playlist = gen_lyrics(0, playlist)

		elif cm == "l" or cm == "love" or cm == "loved":
			playlist = gen_love(0, playlist)

		elif cm == "clr":
			selections.clear()

		elif cm == "rv" or cm == "reverse":
			playlist = gen_reverse(0, playlist)

		elif cm == "rva":
			playlist = gen_folder_reverse(0, playlist)

		elif cm == "rata>":

			playlist = gen_folder_top_rating(0, custom_list=playlist)

		elif cm == "rat>":

			def rat_key(track_id):
				return star_store.get_rating(track_id)

			playlist = sorted(playlist, key=rat_key, reverse=True)

		elif cm == "rat<":

			def rat_key(track_id):
				return star_store.get_rating(track_id)

			playlist = sorted(playlist, key=rat_key)

		elif cm[:4] == "rat=":
			value = cm[4:]
			try:
				value = float(value) * 2
				temp = []
				for item in playlist:
					if value == star_store.get_rating(item):
						temp.append(item)
				playlist = temp
			except Exception:
				logging.exception("Failed to get rating")
				errors = True

		elif cm[:4] == "rat<":
			value = cm[4:]
			try:
				value = float(value) * 2
				temp = []
				for item in playlist:
					if value > star_store.get_rating(item):
						temp.append(item)
				playlist = temp
			except Exception:
				logging.exception("Failed to get rating")
				errors = True

		elif cm[:4] == "rat>":
			value = cm[4:]
			try:
				value = float(value) * 2
				temp = []
				for item in playlist:
					if value < star_store.get_rating(item):
						temp.append(item)
				playlist = temp
			except Exception:
				logging.exception("Failed to get rating")
				errors = True

		elif cm == "rat":
			temp = []
			for item in playlist:
				# tr = pctl.get_track(item)
				if star_store.get_rating(item) > 0:
					temp.append(item)
			playlist = temp

		elif cm == "norat":
			temp = []
			for item in playlist:
				if star_store.get_rating(item) == 0:
					temp.append(item)
			playlist = temp

		elif cm == "d>":
			playlist = gen_sort_len(0, custom_list=playlist)

		elif cm == "d<":
			playlist = gen_sort_len(0, custom_list=playlist)
			playlist = list(reversed(playlist))

		elif cm[:2] == "d<":
			value = cm[2:]
			if value and value.isdigit():
				value = int(value)
				for i in reversed(range(len(playlist))):
					tr = pctl.get_track(playlist[i])
					if not value > tr.length:
						del playlist[i]

		elif cm[:2] == "d>":
			value = cm[2:]
			if value and value.isdigit():
				value = int(value)
				for i in reversed(range(len(playlist))):
					tr = pctl.get_track(playlist[i])
					if not value < tr.length:
						del playlist[i]

		elif cm == "path":
			sort_path_pl(0, custom_list=playlist)

		elif cm == "pa>":
			playlist = gen_folder_top(0, custom_list=playlist)

		elif cm == "pa<":
			playlist = gen_folder_top(0, custom_list=playlist)
			playlist = gen_folder_reverse(0, playlist)

		elif cm == "pt>" or cm == "pc>":
			playlist = gen_top_100(0, custom_list=playlist)

		elif cm == "pt<" or cm == "pc<":
			playlist = gen_top_100(0, custom_list=playlist)
			playlist = list(reversed(playlist))

		elif cm[:3] == "pt>":
			value = cm[3:]
			if value and value.isdigit():
				value = int(value)
				for i in reversed(range(len(playlist))):
					t_time = star_store.get(playlist[i])
					if t_time < value:
						del playlist[i]

		elif cm[:3] == "pt<":
			value = cm[3:]
			if value and value.isdigit():
				value = int(value)
				for i in reversed(range(len(playlist))):
					t_time = star_store.get(playlist[i])
					if t_time > value:
						del playlist[i]

		elif cm[:3] == "pc>":
			value = cm[3:]
			if value and value.isdigit():
				value = int(value)
				for i in reversed(range(len(playlist))):
					t_time = star_store.get(playlist[i])
					tr = pctl.get_track(playlist[i])
					if tr.length > 0:
						if not value < t_time / tr.length:
							del playlist[i]

		elif cm[:3] == "pc<":
			value = cm[3:]
			if value and value.isdigit():
				value = int(value)
				for i in reversed(range(len(playlist))):
					t_time = star_store.get(playlist[i])
					tr = pctl.get_track(playlist[i])
					if tr.length > 0:
						if not value > t_time / tr.length:
							del playlist[i]

		elif cm == "y<":
			playlist = gen_sort_date(0, False, playlist)

		elif cm == "y>":
			playlist = gen_sort_date(0, True, playlist)

		elif cm[:2] == "y=":
			value = cm[2:]
			if value:
				temp = []
				for item in playlist:
					if value in pctl.master_library[item].date:
						temp.append(item)
				playlist = temp

		elif cm[:3] == "y>=":
			value = cm[3:]
			if value and value.isdigit():
				value = int(value)
				temp = []
				for item in playlist:
					if pctl.master_library[item].date[:4].isdigit() and int(
							pctl.master_library[item].date[:4]) >= value:
						temp.append(item)
				playlist = temp

		elif cm[:3] == "y<=":
			value = cm[3:]
			if value and value.isdigit():
				value = int(value)
				temp = []
				for item in playlist:
					if pctl.master_library[item].date[:4].isdigit() and int(
							pctl.master_library[item].date[:4]) <= value:
						temp.append(item)
				playlist = temp

		elif cm[:2] == "y>":
			value = cm[2:]
			if value and value.isdigit():
				value = int(value)
				temp = []
				for item in playlist:
					if pctl.master_library[item].date[:4].isdigit() and int(pctl.master_library[item].date[:4]) > value:
						temp.append(item)
				playlist = temp

		elif cm[:2] == "y<":
			value = cm[2:]
			if value and value.isdigit:
				value = int(value)
				temp = []
				for item in playlist:
					if pctl.master_library[item].date[:4].isdigit() and int(pctl.master_library[item].date[:4]) < value:
						temp.append(item)
				playlist = temp

		elif cm == "st" or cm == "rt" or cm == "r":
			random.shuffle(playlist)

		elif cm == "sf" or cm == "rf" or cm == "ra" or cm == "sa":
			playlist = gen_folder_shuffle(0, custom_list=playlist)

		elif cm.startswith("n"):
			value = cm[1:]
			if value.isdigit():
				playlist = playlist[:int(value)]

		# SEARCH FOLDER
		elif cm.startswith("p\"") and len(cm) > 3:

			if not selections:
				for plist in pctl.multi_playlist:
					code = pctl.gen_codes.get(plist.uuid_int)
					if is_source_type(code):
						selections.append(plist.playlist_ids)

			search = quote
			search_over.all_folders = True
			search_over.sip = True
			search_over.search_text.text = search
			if worker2_lock.locked():
				try:
					worker2_lock.release()
				except RuntimeError as e:
					if str(e) == "release unlocked lock":
						logging.error("RuntimeError: Attempted to release already unlocked worker2_lock")
					else:
						logging.exception("Unknown RuntimeError trying to release worker2_lock")
				except Exception:
					logging.exception("Unknown error trying to release worker2_lock")
			while search_over.sip:
				time.sleep(0.01)

			found_name = ""

			for result in search_over.results:
				if result[0] == 5:
					found_name = result[1]
					break
			else:
				logging.info("No folder search result found")
				continue

			search_over.clear()

			playlist += search_over.click_meta(found_name, get_list=True, search_lists=selections)

		# SEARCH GENRE
		elif (cm.startswith(('g"', 'gm"', 'g="'))) and len(cm) > 3:

			if not selections:
				for plist in pctl.multi_playlist:
					code = pctl.gen_codes.get(plist.uuid_int)
					if is_source_type(code):
						selections.append(plist.playlist_ids)

			g_search = quote.lower().replace("-", "")  # .replace(" ", "")

			search = g_search
			search_over.sip = True
			search_over.search_text.text = search
			if worker2_lock.locked():
				try:
					worker2_lock.release()
				except RuntimeError as e:
					if str(e) == "release unlocked lock":
						logging.error("RuntimeError: Attempted to release already unlocked worker2_lock")
					else:
						logging.exception("Unknown RuntimeError trying to release worker2_lock")
				except Exception:
					logging.exception("Unknown error trying to release worker2_lock")
			while search_over.sip:
				time.sleep(0.01)

			found_name = ""

			if cm.startswith("g=\""):
				for result in search_over.results:
					if result[0] == 3 and result[1].lower().replace("-", "").replace(" ", "") == g_search:
						found_name = result[1]
						break
			elif cm.startswith("g\"") or not prefs.sep_genre_multi:
				for result in search_over.results:
					if result[0] == 3:
						found_name = result[1]
						break
			elif cm.startswith("gm\""):
				for result in search_over.results:
					if result[0] == 3 and result[1].endswith("+"):
						found_name = result[1]
						break

			if not found_name:
				logging.warning("No genre search result found")
				continue

			search_over.clear()

			playlist += search_over.click_genre(found_name, get_list=True, search_lists=selections)

		# SEARCH ARTIST
		elif cm.startswith("a\"") and len(cm) > 3 and cm != "auto":
			if not selections:
				for plist in pctl.multi_playlist:
					code = pctl.gen_codes.get(plist.uuid_int)
					if is_source_type(code):
						selections.append(plist.playlist_ids)

			search = quote
			search_over.sip = True
			search_over.search_text.text = "artist " + search
			if worker2_lock.locked():
				try:
					worker2_lock.release()
				except RuntimeError as e:
					if str(e) == "release unlocked lock":
						logging.error("RuntimeError: Attempted to release already unlocked worker2_lock")
					else:
						logging.exception("Unknown RuntimeError trying to release worker2_lock")
				except Exception:
					logging.exception("Unknown error trying to release worker2_lock")
			while search_over.sip:
				time.sleep(0.01)

			found_name = ""

			for result in search_over.results:
				if result[0] == 0:
					found_name = result[1]
					break
			else:
				logging.warning("No artist search result found")
				continue

			search_over.clear()
			# for item in search_over.click_artist(found_name, get_list=True, search_lists=selections):
			#	 playlist.append(item)
			playlist += search_over.click_artist(found_name, get_list=True, search_lists=selections)

		elif cm.startswith("ff\""):

			for i in reversed(range(len(playlist))):
				tr = pctl.get_track(playlist[i])
				line = " ".join([tr.title, tr.artist, tr.album, tr.fullpath, tr.composer, tr.comment, tr.album_artist]).lower()

				if prefs.diacritic_search and all([ord(c) < 128 for c in quote]):
					line = str(unidecode(line))

				if not search_magic(quote.lower(), line):
					del playlist[i]

			playlist = list(OrderedDict.fromkeys(playlist))

		elif cm.startswith("fx\""):

			for i in reversed(range(len(playlist))):
				tr = pctl.get_track(playlist[i])
				line = " ".join(
					[tr.title, tr.artist, tr.album, tr.fullpath, tr.composer, tr.comment, tr.album_artist]).lower()
				if prefs.diacritic_search and all([ord(c) < 128 for c in quote]):
					line = str(unidecode(line))

				if search_magic(quote.lower(), line):
					del playlist[i]


		elif cm.startswith(('find"', 'f"', 'fs"')):

			if not selections:
				for plist in pctl.multi_playlist:
					code = pctl.gen_codes.get(plist.uuid_int)
					if is_source_type(code):
						selections.append(plist.playlist_ids)

			cooldown = 0
			dones = {}
			for selection in selections:
				for track_id in selection:
					if track_id not in dones:
						tr = pctl.get_track(track_id)

						if cm.startswith("fs\""):
							line = "|".join([tr.title, tr.artist, tr.album, tr.fullpath, tr.composer, tr.comment, tr.album_artist]).lower()
							if quote.lower() in line:
								playlist.append(track_id)

						else:
							line = " ".join([tr.title, tr.artist, tr.album, tr.fullpath, tr.composer, tr.comment, tr.album_artist]).lower()

							# if prefs.diacritic_search and all([ord(c) < 128 for c in quote]):
							#	 line = str(unidecode(line))

							if search_magic(quote.lower(), line):
								playlist.append(track_id)

						cooldown += 1
						if cooldown > 300:
							time.sleep(0.005)
							cooldown = 0

						dones[track_id] = None

			playlist = list(OrderedDict.fromkeys(playlist))


		elif cm.startswith(('s"', 'px"')):
			pl_name = quote
			target = None
			for p in pctl.multi_playlist:
				if p.title.lower() == pl_name.lower():
					target = p.playlist_ids
					break
			else:
				for p in pctl.multi_playlist:
					#logging.info(p.title.lower())
					#logging.info(pl_name.lower())
					if p.title.lower().startswith(pl_name.lower()):
						target = p.playlist_ids
						break
			if target is None:
				logging.warning(f"not found: {pl_name}")
				logging.warning("Target playlist not found")
				if cm.startswith("s\""):
					selections_searched += 1
				errors = "playlist"
				continue

			if cm.startswith("s\""):
				selections_searched += 1
				selections.append(target)
			elif cm.startswith("px\""):
				playlist[:] = [x for x in playlist if x not in target]

		else:
			errors = True

	gui.gen_code_errors = errors
	if not playlist and not errors:
		gui.gen_code_errors = "empty"

	if gui.rename_playlist_box and (not playlist or cmds.count("a") > 1):
		pass
	else:
		source_playlist[:] = playlist[:]

	tree_view_box.clear_target_pl(0, id)
	pctl.regen_in_progress = False
	gui.pl_update = 1
	reload()
	pctl.notify_change()

	#logging.info(cmds)


def make_auto_sorting(pl: int) -> None:
	pctl.gen_codes[pl_to_id(pl)] = "self a path tn ypa auto"
	show_message(
		_("OK. This playlist will automatically sort on import from now on"),
		_("You remove or edit this behavior by going \"Misc...\" > \"Edit generator...\""), mode="done")


extra_tab_menu = Menu(155, show_icons=True)

extra_tab_menu.add(MenuItem(_("New Playlist"), new_playlist, icon=add_icon))


def spotify_show_test(_):
	return prefs.spot_mode

def jellyfin_show_test(_):
	return prefs.jelly_password and prefs.jelly_username


tab_menu.add(MenuItem(_("Upload"),
	upload_spotify_playlist, pass_ref=True, pass_ref_deco=True, icon=jell_icon, show_test=spotify_show_test))

def upload_jellyfin_playlist(pl: TauonPlaylist) -> None:
	if jellyfin.scanning:
		return
	shooter(jellyfin.upload_playlist, [pl])

tab_menu.add(MenuItem(_("Upload"),
	upload_jellyfin_playlist, pass_ref=True, pass_ref_deco=True, icon=spot_icon, show_test=jellyfin_show_test))


def regen_playlist_async(pl: int) -> None:
	if pctl.regen_in_progress:
		show_message(_("A regen is already in progress..."))
		return
	shoot_dl = threading.Thread(target=regenerate_playlist, args=([pl]))
	shoot_dl.daemon = True
	shoot_dl.start()


tab_menu.add(MenuItem(_("Regenerate"), regen_playlist_async, regenerate_deco, pass_ref=True, pass_ref_deco=True, hint="Alt+R"))
tab_menu.add_sub(_("Generate…"), 150)
tab_menu.add_sub(_("Sort…"), 170)
extra_tab_menu.add_sub(_("From Current…"), 133)
# tab_menu.add(_("Sort by Filepath"), standard_sort, pass_ref=True, disable_test=test_pl_tab_locked, pass_ref_deco=True)
# tab_menu.add(_("Sort Track Numbers"), sort_track_2, pass_ref=True)
# tab_menu.add(_("Sort Year per Artist"), year_sort, pass_ref=True)

tab_menu.add_to_sub(1, MenuItem(_("Sort by Imported Tracks"), imported_sort, pass_ref=True))
tab_menu.add_to_sub(1, MenuItem(_("Sort by Imported Folders"), imported_sort_folders, pass_ref=True))
tab_menu.add_to_sub(1, MenuItem(_("Sort by Filepath"), standard_sort, pass_ref=True))
tab_menu.add_to_sub(1, MenuItem(_("Sort Track Numbers"), sort_track_2, pass_ref=True))
tab_menu.add_to_sub(1, MenuItem(_("Sort Year per Artist"), year_sort, pass_ref=True))
tab_menu.add_to_sub(1, MenuItem(_("Make Playlist Auto-Sorting"), make_auto_sorting, pass_ref=True))

tab_menu.br()

tab_menu.add(MenuItem(_("Rescan Folder"), re_import2, rescan_deco, pass_ref=True, pass_ref_deco=True))

tab_menu.add(MenuItem(_("Paste"), s_append, paste_deco, pass_ref=True))
tab_menu.add(MenuItem(_("Append Playing"), append_current_playing, append_deco, pass_ref=True))
tab_menu.br()

# tab_menu.add("Sort By Filepath", sort_path_pl, pass_ref=True)

tab_menu.add(MenuItem(_("Export…"), export_playlist_box.activate, pass_ref=True))

tab_menu.add_sub(_("Misc…"), 175)


def forget_pl_import_folder(pl: int) -> None:
	pctl.multi_playlist[pl].last_folder = []


def remove_duplicates(pl: int) -> None:
	playlist = []

	for item in pctl.multi_playlist[pl].playlist_ids:
		if item not in playlist:
			playlist.append(item)

	removed = len(pctl.multi_playlist[pl].playlist_ids) - len(playlist)
	if not removed:
		show_message(_("No duplicates were found"))
	else:
		show_message(_("{N} duplicates removed").format(N=removed), mode="done")

	pctl.multi_playlist[pl].playlist_ids[:] = playlist[:]


def start_quick_add(pl: int) -> None:
	pctl.quick_add_target = pl_to_id(pl)
	show_message(
		_("You can now add/remove albums to this playlist by right clicking in gallery of any playlist"),
		_("To exit this mode, click \"Disengage\" from main MENU"))


def auto_get_sync_targets():
	search_paths = [
		"/run/user/*/gvfs/*/*/[Mm]usic",
		"/run/media/*/*/[Mm]usic"]
	result_paths = []
	for item in search_paths:
		result_paths.extend(glob.glob(item))
	return result_paths


def auto_sync_thread(pl: int) -> None:
	if prefs.transcode_inplace:
		show_message(_("Cannot sync when in transcode inplace mode"))
		return

	# Find target path
	gui.sync_progress = "Starting Sync..."
	gui.update += 1

	path = Path(sync_target.text.strip().rstrip("/").rstrip("\\").replace("\n", "").replace("\r", ""))
	logging.debug(f"sync_path: {path}")
	if not path:
		show_message(_("No target folder selected"))
		gui.sync_progress = ""
		gui.stop_sync = False
		gui.update += 1
		return
	if not path.is_dir():
		show_message(_("Target folder could not be found"))
		gui.sync_progress = ""
		gui.stop_sync = False
		gui.update += 1
		return

	prefs.sync_target = str(path)

	# Get list of folder names on device
	logging.info("Getting folder list from device...")
	d_folder_names = path.iterdir()
	logging.info("Got list")

	# Get list of folders we want
	folders = convert_playlist(pl, get_list=True)
	folder_names: list[str] = []
	folder_dict = {}

	if gui.stop_sync:
		gui.sync_progress = ""
		gui.stop_sync = False
		gui.update += 1

	# Find the folder names the transcode function would name them
	for folder in folders:
		name = encode_folder_name(pctl.get_track(folder[0]))
		for item in folder:
			if pctl.get_track(item).album != pctl.get_track(folder[0]).album:
				name = os.path.basename(pctl.get_track(folder[0]).parent_folder_path)
				break
		folder_names.append(name)
		folder_dict[name] = folder

	# ------
	# Find deletes
	if prefs.sync_deletes:
		for d_folder in d_folder_names:
			d_folder = d_folder.name
			if gui.stop_sync:
				break
			if d_folder not in folder_names:
				gui.sync_progress = _("Deleting folders...")
				gui.update += 1
				logging.warning(f"DELETING: {d_folder}")
				shutil.rmtree(path / d_folder)

	# -------
	# Find todos
	todos: list[str] = []
	for folder in folder_names:
		if folder not in d_folder_names:
			todos.append(folder)
			logging.info(f"Want to add: {folder}")
		else:
			logging.error(f"Already exists: {folder}")

	gui.update += 1
	# -----
	# Prepare and copy
	for i, item in enumerate(todos):
		gui.sync_progress = _("Copying files to device")
		if gui.stop_sync:
			break

		free_space = shutil.disk_usage(path)[2] / 8 / 100000000  # in GB
		if free_space < 0.6:
			show_message(_("Sync aborted! Low disk space on target device"), mode="warning")
			break

		if prefs.bypass_transcode or (prefs.smart_bypass and 0 < pctl.get_track(folder_dict[item][0]).bitrate <= 128):
			logging.info("Smart bypass...")

			source_parent = Path(pctl.get_track(folder_dict[item][0]).parent_folder_path)
			if source_parent.exists():
				if (path / item).exists():
					show_message(
						_("Sync warning"), _("One or more folders to sync has the same name. Skipping."), mode="warning")
					continue

				(path / item).mkdir()
				encode_done = source_parent
			else:
				show_message(_("One or more folders is missing"))
				continue

		else:

			encode_done = prefs.encoder_output / item
			# TODO(Martin): We should make sure that the length of the source and target matches or is greater, not just that the dir exists and is not empty!
			if not encode_done.exists() or not any(encode_done.iterdir()):
				logging.info("Need to transcode")
				remain = len(todos) - i
				if remain > 1:
					gui.sync_progress = _("{N} Folders Remaining").format(N=str(remain))
				else:
					gui.sync_progress = _("{N} Folder Remaining").format(N=str(remain))
				transcode_list.append(folder_dict[item])
				tauon.thread_manager.ready("worker")
				while transcode_list:
					time.sleep(1)
				if gui.stop_sync:
					break
			else:
				logging.warning("A transcode is already done")

			if encode_done.exists():

				if (path / item).exists():
					show_message(
						_("Sync warning"), _("One or more folders to sync has the same name. Skipping."), mode="warning")
					continue

				(path / item).mkdir()

		for file in encode_done.iterdir():
			file = file.name
			logging.info(f"Copy file {file} to {path / item}…")
			# gui.sync_progress += "."
			gui.update += 1

			if (encode_done / file).is_file():
				size = os.path.getsize(encode_done / file)
				sync_file_timer.set()
				try:
					shutil.copyfile(encode_done / file, path / item / file)
				except OSError as e:
					if str(e).startswith("[Errno 22] Invalid argument: "):
						sanitized_file = re.sub(r'[<>:"/\\|?*]', '_', file)
						if sanitized_file == file:
							logging.exception("Unknown OSError trying to copy file, maybe FS does not support the name?")
						else:
							shutil.copyfile(encode_done / file, path / item / sanitized_file)
							logging.warning(f"Had to rename {file} to {sanitized_file} on the output! Probably a FS limitation!")
					else:
						logging.exception("Unknown OSError trying to copy file")
				except Exception:
					logging.exception("Unknown error trying to copy file")

			if gui.sync_speed == 0 or (sync_file_update_timer.get() > 1 and not file.endswith(".jpg")):
				sync_file_update_timer.set()
				gui.sync_speed = size / sync_file_timer.get()
				gui.sync_progress = _("Copying files to device") + " @ " + get_filesize_string_rounded(
					gui.sync_speed) + "/s"
				if gui.stop_sync:
					gui.sync_progress = _("Aborting Sync") + " @ " + get_filesize_string_rounded(gui.sync_speed) + "/s"

		logging.info("Finished copying folder")

	gui.sync_speed = 0
	gui.sync_progress = ""
	gui.stop_sync = False
	gui.update += 1
	show_message(_("Sync completed"), mode="done")


def auto_sync(pl: int) -> None:
	shoot_dl = threading.Thread(target=auto_sync_thread, args=([pl]))
	shoot_dl.daemon = True
	shoot_dl.start()


def set_sync_playlist(pl: int) -> None:
	id = pl_to_id(pl)
	if prefs.sync_playlist == id:
		prefs.sync_playlist = None
	else:
		prefs.sync_playlist = pl_to_id(pl)


def sync_playlist_deco(pl: int):
	text = _("Set as Sync Playlist")
	id = pl_to_id(pl)
	if id == prefs.sync_playlist:
		text = _("Un-set as Sync Playlist")
	return [colours.menu_text, colours.menu_background, text]


def set_download_playlist(pl: int) -> None:
	id = pl_to_id(pl)
	if prefs.download_playlist == id:
		prefs.download_playlist = None
	else:
		prefs.download_playlist = pl_to_id(pl)

def set_podcast_playlist(pl: int) -> None:
	pctl.multi_playlist[pl].persist_time_positioning ^= True


def set_download_deco(pl: int):
	text = _("Set as Downloads Playlist")
	if id == prefs.download_playlist:
		text = _("Un-set as Downloads Playlist")
	return [colours.menu_text, colours.menu_background, text]

def set_podcast_deco(pl: int):
	text = _("Set Use Persistent Time")
	if pctl.multi_playlist[pl].persist_time_positioning:
		text = _("Un-set Use Persistent Time")
	return [colours.menu_text, colours.menu_background, text]


def csv_string(item):
	item = str(item)
	item.replace("\"", "\"\"")
	return f"\"{item}\""


def export_playlist_albums(pl: int) -> None:
	p = pctl.multi_playlist[pl]
	name = p.title
	playlist = p.playlist_ids

	albums = []
	playtimes = {}
	last_folder = None
	for i, id in enumerate(playlist):
		track = pctl.get_track(id)
		if last_folder != track.parent_folder_path:
			last_folder = track.parent_folder_path
			if id not in albums:
				albums.append(id)

		playtimes[last_folder] = playtimes.get(last_folder, 0) + int(star_store.get(id))

	filename = f"{user_directory}/{name}.csv"
	xport = open(filename, "w")

	xport.write("Album name;Artist;Release date;Genre;Rating;Playtime;Folder path")

	for id in albums:
		track = pctl.get_track(id)
		artist = track.album_artist
		if not artist:
			artist = track.artist

		xport.write("\n")
		xport.write(csv_string(track.album) + ",")
		xport.write(csv_string(artist) + ",")
		xport.write(csv_string(track.date) + ",")
		xport.write(csv_string(track.genre) + ",")
		xport.write(str(int(album_star_store.get_rating(track))))
		xport.write(",")
		xport.write(str(round(playtimes[track.parent_folder_path])))
		xport.write(",")
		xport.write(csv_string(track.parent_folder_path))

	xport.close()
	show_message(_("Export complete."), _("Saved as: ") + filename, mode="done")


tab_menu.add_to_sub(2, MenuItem(_("Export Playlist Stats"), export_stats, pass_ref=True))
tab_menu.add_to_sub(2, MenuItem(_("Export Albums CSV"), export_playlist_albums, pass_ref=True))
tab_menu.add_to_sub(2, MenuItem(_("Transcode All"), convert_playlist, pass_ref=True))
tab_menu.add_to_sub(2, MenuItem(_("Rescan Tags"), rescan_tags, pass_ref=True))
# tab_menu.add_to_sub(_('Forget Import Folder'), 2, forget_pl_import_folder, rescan_deco, pass_ref=True, pass_ref_deco=True)
# tab_menu.add_to_sub(_('Re-Import Last Folder'), 1, re_import, pass_ref=True)
# tab_menu.add_to_sub(_('Quick Export XSPF'), 2, export_xspf, pass_ref=True)
# tab_menu.add_to_sub(_('Quick Export M3U'), 2, export_m3u, pass_ref=True)
tab_menu.add_to_sub(2, MenuItem(_("Toggle Breaks"), pl_toggle_playlist_break, pass_ref=True))
tab_menu.add_to_sub(2, MenuItem(_("Edit Generator..."), edit_generator_box, pass_ref=True))
tab_menu.add_to_sub(2, MenuItem(_("Engage Gallery Quick Add"), start_quick_add, pass_ref=True))
tab_menu.add_to_sub(2, MenuItem(_("Set as Sync Playlist"), set_sync_playlist, sync_playlist_deco, pass_ref_deco=True, pass_ref=True))
tab_menu.add_to_sub(2, MenuItem(_("Set as Downloads Playlist"), set_download_playlist, set_download_deco, pass_ref_deco=True, pass_ref=True))
tab_menu.add_to_sub(2, MenuItem(_("Set podcast mode"), set_podcast_playlist, set_podcast_deco, pass_ref_deco=True, pass_ref=True))
tab_menu.add_to_sub(2, MenuItem(_("Remove Duplicates"), remove_duplicates, pass_ref=True))
tab_menu.add_to_sub(2, MenuItem(_("Toggle Console"), console.toggle))


# tab_menu.add_to_sub("Empty Playlist", 0, new_playlist)

def best(index: int):
	# key = pctl.master_library[index].title + pctl.master_library[index].filename
	if pctl.master_library[index].length < 1:
		return 0
	return int(star_store.get(index))


def key_rating(index: int):
	return star_store.get_rating(index)

def key_scrobbles(index: int):
	return pctl.get_track(index).lfm_scrobbles

def key_disc(index: int):
	return pctl.get_track(index).disc_number

def key_cue(index: int):
	return pctl.get_track(index).is_cue

def key_playcount(index: int):
	# key = pctl.master_library[index].title + pctl.master_library[index].filename
	if pctl.master_library[index].length < 1:
		return 0
	return star_store.get(index) / pctl.master_library[index].length
	# if key in pctl.star_library:
	#	 return pctl.star_library[key] / pctl.master_library[index].length
	# else:
	#	 return 0


def add_pl_tag(text):
	return f" <{text}>"


def gen_top_rating(index, custom_list=None):
	source = custom_list
	if source is None:
		source = pctl.multi_playlist[index].playlist_ids
	playlist = copy.deepcopy(source)
	playlist = sorted(playlist, key=key_rating, reverse=True)

	if custom_list is not None:
		return playlist

	pctl.multi_playlist.append(
		pl_gen(
			title=pctl.multi_playlist[index].title + add_pl_tag(_("Top Rated Tracks")),
			playlist_ids=copy.deepcopy(playlist),
			hide_title=True))

	pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[index].title + "\" a rat>"


def gen_top_100(index, custom_list=None):
	source = custom_list
	if source is None:
		source = pctl.multi_playlist[index].playlist_ids
	playlist = copy.deepcopy(source)
	playlist = sorted(playlist, key=best, reverse=True)

	if custom_list is not None:
		return playlist

	pctl.multi_playlist.append(
		pl_gen(
			title=pctl.multi_playlist[index].title + add_pl_tag(_("Top Played Tracks")),
			playlist_ids=copy.deepcopy(playlist),
			hide_title=True))

	pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[index].title + "\" a pt>"


tab_menu.add_to_sub(0, MenuItem(_("Top Played Tracks"), gen_top_100, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("Top Played Tracks"), gen_top_100, pass_ref=True))


def gen_folder_top(pl: int, get_sets: bool = False, custom_list=None):
	source = custom_list
	if source is None:
		source = pctl.multi_playlist[pl].playlist_ids

	if len(source) < 3:
		return []

	sets = []
	se = []
	tr = pctl.get_track(source[0])
	last = tr.parent_folder_path
	last_al = tr.album
	for track in source:
		if last != pctl.master_library[track].parent_folder_path or last_al != pctl.master_library[track].album:
			last = pctl.master_library[track].parent_folder_path
			last_al = pctl.master_library[track].album
			sets.append(copy.deepcopy(se))
			se = []
		se.append(track)
	sets.append(copy.deepcopy(se))

	def best(folder):
		#logging.info(folder)
		total_star = 0
		for item in folder:
			# key = pctl.master_library[item].title + pctl.master_library[item].filename
			# if key in pctl.star_library:
			#	 total_star += int(pctl.star_library[key])
			total_star += int(star_store.get(item))
		#logging.info(total_star)
		return total_star

	if get_sets:
		r = []
		for item in sets:
			r.append((item, best(item)))
		return r

	sets = sorted(sets, key=best, reverse=True)

	playlist = []

	for se in sets:
		playlist += se

	# pctl.multi_playlist.append(
	#	 [pctl.multi_playlist[pl].title + " <Most Played Albums>", 0, copy.deepcopy(playlist), 0, 0, 0])
	if custom_list is not None:
		return playlist

	pctl.multi_playlist.append(
		pl_gen(
			title=pctl.multi_playlist[pl].title + add_pl_tag(_("Top Played Albums")),
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))

	pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[pl].title + "\" a pa>"


tab_menu.add_to_sub(0, MenuItem(_("Top Played Albums"), gen_folder_top, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("Top Played Albums"), gen_folder_top, pass_ref=True))

tab_menu.add_to_sub(0, MenuItem(_("Top Rated Tracks"), gen_top_rating, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("Top Rated Tracks"), gen_top_rating, pass_ref=True))


def gen_folder_top_rating(pl: int, get_sets: bool = False, custom_list=None):
	source = custom_list
	if source is None:
		source = pctl.multi_playlist[pl].playlist_ids

	if len(source) < 3:
		return []

	sets = []
	se = []
	tr = pctl.get_track(source[0])
	last = tr.parent_folder_path
	last_al = tr.album
	for track in source:
		if last != pctl.master_library[track].parent_folder_path or last_al != pctl.master_library[track].album:
			last = pctl.master_library[track].parent_folder_path
			last_al = pctl.master_library[track].album
			sets.append(copy.deepcopy(se))
			se = []
		se.append(track)
	sets.append(copy.deepcopy(se))

	def best(folder):
		return album_star_store.get_rating(pctl.get_track(folder[0]))

	if get_sets:
		r = []
		for item in sets:
			r.append((item, best(item)))
		return r

	sets = sorted(sets, key=best, reverse=True)

	playlist = []

	for se in sets:
		playlist += se

	if custom_list is not None:
		return playlist

	pctl.multi_playlist.append(
		pl_gen(
			title=pctl.multi_playlist[pl].title + add_pl_tag(_("Top Rated Albums")),
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))

	pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[pl].title + "\" a rata>"


def gen_lyrics(plpl: int, custom_list=None):
	playlist = []

	source = custom_list
	if source is None:
		source = pctl.multi_playlist[pl].playlist_ids

	for item in source:
		if pctl.master_library[item].lyrics != "":
			playlist.append(item)

	if custom_list is not None:
		return playlist

	if len(playlist) > 0:
		pctl.multi_playlist.append(
			pl_gen(
				title=_("Tracks with lyrics"),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=False))

		pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[pl].title + "\" a ly"

	else:
		show_message(_("No tracks with lyrics were found."))


tab_menu.add_to_sub(0, MenuItem(_("Top Rated Albums"), gen_folder_top_rating, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("Top Rated Albums"), gen_folder_top_rating, pass_ref=True))


def gen_incomplete(plpl: int, custom_list=None):
	playlist = []

	source = custom_list
	if source is None:
		source = pctl.multi_playlist[pl].playlist_ids

	albums = {}
	nums = {}
	for id in source:
		track = pctl.get_track(id)
		if track.album and track.track_number:

			if type(track.track_number) is str and not track.track_number.isdigit():
				continue

			if track.album not in albums:
				albums[track.album] = []
				nums[track.album] = []

			if track not in albums[track.album]:
				albums[track.album].append(track)
				nums[track.album].append(int(track.track_number))

	for album, tracks in albums.items():
		numbers = nums[album]
		if len(numbers) > 2:
			mi = min(numbers)
			mx = max(numbers)
			for track in tracks:
				if type(track.track_total) is int or (type(track.track_total) is str and track.track_total.isdigit()):
					mx = max(mx, int(track.track_total))
			r = list(range(int(mi), int(mx)))
			for track in tracks:
				if int(track.track_number) in r:
					r.remove(int(track.track_number))
			if r or mi > 1:
				for tr in tracks:
					playlist.append(tr.index)

	if custom_list is not None:
		return playlist

	if len(playlist) > 0:
		show_message(_("Note this may include albums that simply have tracks missing an album tag"))
		pctl.multi_playlist.append(
			pl_gen(
				title=pctl.multi_playlist[pl].title + add_pl_tag(_("Incomplete Albums")),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=False))

		# pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[pl].title + "\" a ly"

	else:
		show_message(_("No incomplete albums were found."))


def gen_codec_pl(codec):
	playlist = []

	for pl in pctl.multi_playlist:
		for item in pl.playlist_ids:
			if pctl.master_library[item].file_ext == codec and item not in playlist:
				playlist.append(item)

	if len(playlist) > 0:
		pctl.multi_playlist.append(
			pl_gen(
				title=_("Codec: ") + codec,
				playlist_ids=copy.deepcopy(playlist),
				hide_title=False))


def gen_last_imported_folders(index, custom_list=None, reverse=True):
	source = custom_list
	if source is None:
		source = pctl.multi_playlist[index].playlist_ids

	a_cache = {}

	def key_import(index: int):

		track = pctl.master_library[index]
		cached = a_cache.get((track.album, track.parent_folder_name))
		if cached is not None:
			return cached

		if track.album:
			a_cache[(track.album, track.parent_folder_name)] = index
		return index

	playlist = copy.deepcopy(source)
	playlist = sorted(playlist, key=key_import, reverse=reverse)
	sort_track_2(0, playlist)

	if custom_list is not None:
		return playlist


def gen_last_modified(index, custom_list=None, reverse=True):
	source = custom_list
	if source is None:
		source = pctl.multi_playlist[index].playlist_ids

	a_cache = {}

	def key_modified(index: int):

		track = pctl.master_library[index]
		cached = a_cache.get((track.album, track.parent_folder_name))
		if cached is not None:
			return cached

		if track.album:
			a_cache[(track.album, track.parent_folder_name)] = pctl.master_library[index].modified_time
		return pctl.master_library[index].modified_time

	playlist = copy.deepcopy(source)
	playlist = sorted(playlist, key=key_modified, reverse=reverse)
	sort_track_2(0, playlist)

	if custom_list is not None:
		return playlist

	pctl.multi_playlist.append(
		pl_gen(
			title=pctl.multi_playlist[index].title + add_pl_tag(_("File Modified")),
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))

	pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[index].title + "\" a m>"


tab_menu.add_to_sub(0, MenuItem(_("File Modified"), gen_last_modified, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("File Modified"), gen_last_modified, pass_ref=True))


# tab_menu.add_to_sub(_("File Path"), 0, standard_sort, pass_ref=True)
# extra_tab_menu.add_to_sub(_("File Path"), 0, standard_sort, pass_ref=True)


def gen_love(pl: int, custom_list=None):
	playlist = []

	source = custom_list
	if source is None:
		source = pctl.multi_playlist[pl].playlist_ids

	for item in source:
		if get_love_index(item):
			playlist.append(item)

	playlist.sort(key=lambda x: get_love_timestamp_index(x), reverse=True)

	if custom_list is not None:
		return playlist

	if len(playlist) > 0:
		# pctl.multi_playlist.append(["Interesting Comments", 0, copy.deepcopy(playlist), 0, 0, 0])
		pctl.multi_playlist.append(
			pl_gen(
				title=_("Loved"),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=False))
		pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[pl].title + "\" a l"
	else:
		show_message(_("No loved tracks were found."))


def gen_comment(pl: int) -> None:
	playlist = []

	for item in pctl.multi_playlist[pl].playlist_ids:
		cm = pctl.master_library[item].comment
		if len(cm) > 20 and \
				cm[0] != "0" and \
				"http://" not in cm and \
				"www." not in cm and \
				"Release" not in cm and \
				"EAC" not in cm and \
				"@" not in cm and \
				".com" not in cm and \
				"ipped" not in cm and \
				"ncoded" not in cm and \
				"ExactA" not in cm and \
				"WWW." not in cm and \
				cm[2] != "+" and \
				cm[1] != "+":
			playlist.append(item)

	if len(playlist) > 0:
		# pctl.multi_playlist.append(["Interesting Comments", 0, copy.deepcopy(playlist), 0, 0, 0])
		pctl.multi_playlist.append(
			pl_gen(
				title=_("Interesting Comments"),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=False))
	else:
		show_message(_("Nothing of interest was found."))


def gen_replay(pl: int) -> None:
	playlist = []

	for item in pctl.multi_playlist[pl].playlist_ids:
		if pctl.master_library[item].misc.get("replaygain_track_gain"):
			playlist.append(item)

	if len(playlist) > 0:
		pctl.multi_playlist.append(
			pl_gen(
				title=_("ReplayGain Tracks"),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=False))
	else:
		show_message(_("No replay gain tags were found."))


def gen_sort_len(index: int, custom_list=None):
	source = custom_list
	if source is None:
		source = pctl.multi_playlist[index].playlist_ids

	def length(index: int) -> int:

		if pctl.master_library[index].length < 1:
			return 0
		return int(pctl.master_library[index].length)

	playlist = copy.deepcopy(source)
	playlist = sorted(playlist, key=length, reverse=True)

	if custom_list is not None:
		return playlist

	# pctl.multi_playlist.append(
	#	 [pctl.multi_playlist[index].title + " <Duration Sorted>", 0, copy.deepcopy(playlist), 0, 1, 0])

	pctl.multi_playlist.append(
		pl_gen(
			title=pctl.multi_playlist[index].title + add_pl_tag(_("Duration Sorted")),
			playlist_ids=copy.deepcopy(playlist),
			hide_title=True))

	pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[index].title + "\" a d>"


tab_menu.add_to_sub(0, MenuItem(_("Longest Tracks"), gen_sort_len, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("Longest Tracks"), gen_sort_len, pass_ref=True))


def gen_folder_duration(pl: int, get_sets: bool = False):
	if len(pctl.multi_playlist[pl].playlist_ids) < 3:
		return None

	sets = []
	se = []
	last = pctl.master_library[pctl.multi_playlist[pl].playlist_ids[0]].parent_folder_path
	last_al = pctl.master_library[pctl.multi_playlist[pl].playlist_ids[0]].album
	for track in pctl.multi_playlist[pl].playlist_ids:
		if last != pctl.master_library[track].parent_folder_path or last_al != pctl.master_library[track].album:
			last = pctl.master_library[track].parent_folder_path
			last_al = pctl.master_library[track].album
			sets.append(copy.deepcopy(se))
			se = []
		se.append(track)
	sets.append(copy.deepcopy(se))

	def best(folder):
		total_duration = 0
		for item in folder:
			total_duration += pctl.master_library[item].length
		return total_duration

	if get_sets:
		r = []
		for item in sets:
			r.append((item, best(item)))
		return r

	sets = sorted(sets, key=best, reverse=True)
	playlist = []

	for se in sets:
		playlist += se

	pctl.multi_playlist.append(
		pl_gen(
			title=pctl.multi_playlist[pl].title + add_pl_tag(_("Longest Albums")),
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))


tab_menu.add_to_sub(0, MenuItem(_("Longest Albums"), gen_folder_duration, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("Longest Albums"), gen_folder_duration, pass_ref=True))


def gen_sort_date(index: int, rev: bool = False, custom_list=None):
	def g_date(index: int):

		if pctl.master_library[index].date != "":
			return str(pctl.master_library[index].date)
		return "z"

	playlist = []
	lowest = 0
	highest = 0
	first = True

	source = custom_list
	if source is None:
		source = pctl.multi_playlist[index].playlist_ids

	for item in source:
		date = pctl.master_library[item].date
		if date != "":
			playlist.append(item)
			if len(date) > 4 and date[:4].isdigit():
				date = date[:4]
			if len(date) == 4 and date.isdigit():
				year = int(date)
				if first:
					lowest = year
					highest = year
					first = False
				lowest = min(year, lowest)
				highest = max(year, highest)

	playlist = sorted(playlist, key=g_date, reverse=rev)

	if custom_list is not None:
		return playlist

	line = add_pl_tag(_("Year Sorted"))
	if lowest != highest and lowest != 0 and highest != 0:
		if rev:
			line = " <" + str(highest) + "-" + str(lowest) + ">"
		else:
			line = " <" + str(lowest) + "-" + str(highest) + ">"

	pctl.multi_playlist.append(
		pl_gen(
			title=pctl.multi_playlist[index].title + line,
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))

	if rev:
		pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[index].title + "\" a y>"
	else:
		pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[index].title + "\" a y<"


tab_menu.add_to_sub(0, MenuItem(_("Year by Oldest"), gen_sort_date, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("Year by Oldest"), gen_sort_date, pass_ref=True))


def gen_sort_date_new(index: int):
	gen_sort_date(index, True)


tab_menu.add_to_sub(0, MenuItem(_("Year by Latest"), gen_sort_date_new, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("Year by Latest"), gen_sort_date_new, pass_ref=True))


# tab_menu.add_to_sub(_("Year by Artist"), 0, year_sort, pass_ref=True)
# extra_tab_menu.add_to_sub(_("Year by Artist"), 0, year_sort, pass_ref=True)

def gen_500_random(index: int):
	playlist = copy.deepcopy(pctl.multi_playlist[index].playlist_ids)

	random.shuffle(playlist)

	pctl.multi_playlist.append(
		pl_gen(
			title=pctl.multi_playlist[index].title + add_pl_tag(_("Shuffled Tracks")),
			playlist_ids=copy.deepcopy(playlist),
			hide_title=True))

	pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[index].title + "\" a st"


tab_menu.add_to_sub(0, MenuItem(_("Shuffled Tracks"), gen_500_random, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("Shuffled Tracks"), gen_500_random, pass_ref=True))


def gen_folder_shuffle(index, custom_list=None):
	folders = []
	dick = {}

	source = custom_list
	if source is None:
		source = pctl.multi_playlist[index].playlist_ids

	for track in source:
		parent = pctl.master_library[track].parent_folder_path
		if parent not in folders:
			folders.append(parent)
		if parent not in dick:
			dick[parent] = []
		dick[parent].append(track)

	random.shuffle(folders)
	playlist = []

	for folder in folders:
		playlist += dick[folder]

	if custom_list is not None:
		return playlist

	pctl.multi_playlist.append(
		pl_gen(
			title=pctl.multi_playlist[index].title + add_pl_tag(_("Shuffled Albums")),
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))

	pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[index].title + "\" a ra"


tab_menu.add_to_sub(0, MenuItem(_("Shuffled Albums"), gen_folder_shuffle, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("Shuffled Albums"), gen_folder_shuffle, pass_ref=True))


def gen_best_random(index: int):
	playlist = []

	for p in pctl.multi_playlist[index].playlist_ids:
		time = star_store.get(p)

		if time > 300:
			playlist.append(p)

	random.shuffle(playlist)

	if len(playlist) > 0:
		pctl.multi_playlist.append(
			pl_gen(
				title=pctl.multi_playlist[index].title + add_pl_tag(_("Lucky Random")),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=True))

		pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[index].title + "\" a pt>300 rt"


tab_menu.add_to_sub(0, MenuItem(_("Lucky Random"), gen_best_random, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("Lucky Random"), gen_best_random, pass_ref=True))


def gen_reverse(index, custom_list=None):
	source = custom_list
	if source is None:
		source = pctl.multi_playlist[index].playlist_ids

	playlist = list(reversed(source))

	if custom_list is not None:
		return playlist

	pctl.multi_playlist.append(
		pl_gen(
			title=pctl.multi_playlist[index].title + add_pl_tag(_("Reversed")),
			playlist_ids=copy.deepcopy(playlist),
			hide_title=pctl.multi_playlist[index].hide_title))

	pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[index].title + "\" a rv"


tab_menu.add_to_sub(0, MenuItem(_("Reverse Tracks"), gen_reverse, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("Reverse Tracks"), gen_reverse, pass_ref=True))


def gen_folder_reverse(index: int, custom_list=None):
	source = custom_list
	if source is None:
		source = pctl.multi_playlist[index].playlist_ids

	folders = []
	dick = {}
	for track in source:
		parent = pctl.master_library[track].parent_folder_path
		if parent not in folders:
			folders.append(parent)
		if parent not in dick:
			dick[parent] = []
		dick[parent].append(track)

	folders = list(reversed(folders))
	playlist = []

	for folder in folders:
		playlist += dick[folder]

	if custom_list is not None:
		return playlist

	pctl.multi_playlist.append(
		pl_gen(
			title=pctl.multi_playlist[index].title + add_pl_tag(_("Reversed Albums")),
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))

	pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[index].title + "\" a rva"


tab_menu.add_to_sub(0, MenuItem(_("Reverse Albums"), gen_folder_reverse, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("Reverse Albums"), gen_folder_reverse, pass_ref=True))


def gen_dupe(index: int) -> None:
	playlist = pctl.multi_playlist[index].playlist_ids

	pctl.multi_playlist.append(
		pl_gen(
			title=gen_unique_pl_title(pctl.multi_playlist[index].title, _("Duplicate") + " ", 0),
			playing=pctl.multi_playlist[index].playing,
			playlist_ids=copy.deepcopy(playlist),
			position=pctl.multi_playlist[index].position,
			hide_title=pctl.multi_playlist[index].hide_title,
			selected=pctl.multi_playlist[index].selected))


tab_menu.add_to_sub(0, MenuItem(_("Duplicate"), gen_dupe, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("Duplicate"), gen_dupe, pass_ref=True))


def gen_sort_path(index: int) -> None:
	def path(index: int) -> str:
		return pctl.master_library[index].fullpath

	playlist = copy.deepcopy(pctl.multi_playlist[index].playlist_ids)
	playlist = sorted(playlist, key=path)

	pctl.multi_playlist.append(
		pl_gen(
			title=pctl.multi_playlist[index].title + add_pl_tag(_("Filepath Sorted")),
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))


# tab_menu.add_to_sub("Filepath", 1, gen_sort_path, pass_ref=True)


def gen_sort_artist(index: int) -> None:
	def artist(index: int) -> str:
		return pctl.master_library[index].artist

	playlist = copy.deepcopy(pctl.multi_playlist[index].playlist_ids)
	playlist = sorted(playlist, key=artist)

	pctl.multi_playlist.append(
		pl_gen(
			title=pctl.multi_playlist[index].title + add_pl_tag(_("Artist Sorted")),
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))


# tab_menu.add_to_sub("Artist → gui.abc", 0, gen_sort_artist, pass_ref=True)


def gen_sort_album(index: int) -> None:
	def album(index: int) -> None:
		return pctl.master_library[index].album

	playlist = copy.deepcopy(pctl.multi_playlist[index].playlist_ids)
	playlist = sorted(playlist, key=album)

	pctl.multi_playlist.append(
		pl_gen(
			title=pctl.multi_playlist[index].title + add_pl_tag(_("Album Sorted")),
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))


# tab_menu.add_to_sub("Album → gui.abc", 0, gen_sort_album, pass_ref=True)
tab_menu.add_to_sub(0, MenuItem(_("Loved"), gen_love, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("Loved"), gen_love, pass_ref=True))
tab_menu.add_to_sub(0, MenuItem(_("Has Comment"), gen_comment, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("Has Comment"), gen_comment, pass_ref=True))
tab_menu.add_to_sub(0, MenuItem(_("Has Lyrics"), gen_lyrics, pass_ref=True))
extra_tab_menu.add_to_sub(0, MenuItem(_("Has Lyrics"), gen_lyrics, pass_ref=True))


def get_playing_line() -> str:
	if 3 > pctl.playing_state > 0:
		title = pctl.master_library[pctl.track_queue[pctl.queue_step]].title
		artist = pctl.master_library[pctl.track_queue[pctl.queue_step]].artist
		return artist + " - " + title
	return "Stopped"



def reload_config_file():
	if transcode_list:
		show_message(_("Cannot reload while a transcode is in progress!"), mode="error")
		return

	load_prefs()
	gui.opened_config_file = False

	ddt.force_subpixel_text = prefs.force_subpixel_text
	ddt.clear_text_cache()
	pctl.playerCommand = "reload"
	pctl.playerCommandReady = True
	show_message(_("Configuration reloaded"), mode="done")
	gui.update_layout()


def open_config_file():
	save_prefs()
	target = str(config_directory / "tauon.conf")
	if system == "Windows" or msys:
		os.startfile(target)
	elif macos:
		subprocess.call(["open", "-t", target])
	else:
		subprocess.call(["xdg-open", target])
	show_message(_("Config file opened."), _('Click "Reload" if you made any changes'), mode="arrow")
	# reload_config_file()
	# gui.message_box = False
	gui.opened_config_file = True


def open_keymap_file():
	target = str(config_directory / "input.txt")

	if not os.path.isfile(target):
		show_message(_("Input file missing"))
		return

	if system == "Windows" or msys:
		os.startfile(target)
	elif macos:
		subprocess.call(["open", target])
	else:
		subprocess.call(["xdg-open", target])


def open_file(target):
	if not os.path.isfile(target):
		show_message(_("Input file missing"))
		return

	if system == "Windows" or msys:
		os.startfile(target)
	elif macos:
		subprocess.call(["open", target])
	else:
		subprocess.call(["xdg-open", target])


def open_data_directory():
	target = str(user_directory)
	if system == "Windows" or msys:
		os.startfile(target)
	elif macos:
		subprocess.call(["open", target])
	else:
		subprocess.call(["xdg-open", target])


def remove_folder(index: int):
	global default_playlist

	for b in range(len(default_playlist) - 1, -1, -1):
		r_folder = pctl.master_library[index].parent_folder_name
		if pctl.master_library[default_playlist[b]].parent_folder_name == r_folder:
			del default_playlist[b]

	reload()


def convert_folder(index: int):
	global default_playlist
	global transcode_list

	if not tauon.test_ffmpeg():
		return

	folder = []
	if key_shift_down or key_shiftr_down:
		track_object = pctl.get_track(index)
		if track_object.is_network:
			show_message(_("Transcoding tracks from network locations is not supported"))
			return
		folder = [index]

		if prefs.transcode_codec == "flac" and track_object.file_ext.lower() in (
			"mp3", "opus",
			"mp4", "ogg",
			"aac"):
			show_message(_("NO! Bad user!"), _("Im not going to let you transcode a lossy codec to a lossless one!"),
				mode="warning")

			return
		folder = [index]

	else:
		r_folder = pctl.master_library[index].parent_folder_path
		for item in default_playlist:
			if r_folder == pctl.master_library[item].parent_folder_path:

				track_object = pctl.get_track(item)
				if track_object.file_ext == "SPOT":  # track_object.is_network:
					show_message(_("Transcoding spotify tracks not possible"))
					return

				if item not in folder:
					folder.append(item)
				#logging.info(prefs.transcode_codec)
				#logging.info(track_object.file_ext)
				if prefs.transcode_codec == "flac" and track_object.file_ext.lower() in (
					"mp3", "opus",
					"mp4", "ogg",
					"aac"):
					show_message(_("NO! Bad user!"), _("Im not going to let you transcode a lossy codec to a lossless one!"),
						mode="warning")

					return

	#logging.info(folder)
	transcode_list.append(folder)
	tauon.thread_manager.ready("worker")


def transfer(index: int, args) -> None:
	global cargo
	global default_playlist
	old_cargo = copy.deepcopy(cargo)

	if args[0] == 1 or args[0] == 0:  # copy
		if args[1] == 1:  # single track
			cargo.append(index)
			if args[0] == 0:  # cut
				del default_playlist[pctl.selected_in_playlist]

		elif args[1] == 2:  # folder
			for b in range(len(default_playlist)):
				if pctl.master_library[default_playlist[b]].parent_folder_name == pctl.master_library[
					index].parent_folder_name:
					cargo.append(default_playlist[b])
			if args[0] == 0:  # cut
				for b in reversed(range(len(default_playlist))):
					if pctl.master_library[default_playlist[b]].parent_folder_name == pctl.master_library[
						index].parent_folder_name:
						del default_playlist[b]

		elif args[1] == 3:  # playlist
			cargo += default_playlist
			if args[0] == 0:  # cut
				default_playlist = []

	elif args[0] == 2:  # Drop
		if args[1] == 1:  # Before

			insert = pctl.selected_in_playlist
			while insert > 0 and pctl.master_library[default_playlist[insert]].parent_folder_name == \
					pctl.master_library[index].parent_folder_name:
				insert -= 1
				if insert == 0:
					break
			else:
				insert += 1

			while len(cargo) > 0:
				default_playlist.insert(insert, cargo.pop())

		elif args[1] == 2:  # After
			insert = pctl.selected_in_playlist

			while insert < len(default_playlist) and pctl.master_library[default_playlist[insert]].parent_folder_name == \
					pctl.master_library[index].parent_folder_name:
				insert += 1

			while len(cargo) > 0:
				default_playlist.insert(insert, cargo.pop())
		elif args[1] == 3:  # End
			default_playlist += cargo
			# cargo = []

		cargo = old_cargo

	reload()


def temp_copy_folder(ref):
	global cargo
	cargo = []
	transfer(ref, args=[1, 2])


def activate_track_box(index: int):
	global track_box
	global r_menu_index
	r_menu_index = index
	track_box = True
	track_box_path_tool_timer.set()


def menu_paste(position):
	paste(None, position)


def s_copy():
	# Copy tracks to internal clipboard
	# gui.lightning_copy = False
	# if key_shift_down:
	gui.lightning_copy = True

	clip = copy_from_clipboard()
	if "file://" in clip:
		copy_to_clipboard("")

	global cargo
	cargo = []
	if default_playlist:
		for item in shift_selection:
			cargo.append(default_playlist[item])

	if not cargo and -1 < pctl.selected_in_playlist < len(default_playlist):
		cargo.append(default_playlist[pctl.selected_in_playlist])

	tauon.copied_track = None

	if len(cargo) == 1:
		tauon.copied_track = cargo[0]


def directory_size(path: str) -> int:
	total = 0
	for dirpath, dirname, filenames in os.walk(path):
		for file in filenames:
			path = os.path.join(dirpath, file)
			total += os.path.getsize(path)
	return total


def lightning_paste():
	move = True
	# if not key_shift_down:
	#	 move = False

	move_track = pctl.get_track(cargo[0])
	move_path = move_track.parent_folder_path

	for item in cargo:
		if move_path != pctl.get_track(item).parent_folder_path:
			show_message(
				_("More than one folder is in the clipboard"),
				_("This function can only move one folder at a time."), mode="info")
			return

	match_track = pctl.get_track(default_playlist[shift_selection[0]])
	match_path = match_track.parent_folder_path

	if pctl.playing_state > 0 and move:
		if pctl.playing_object().parent_folder_path == move_path:
			pctl.stop(True)

	p = Path(match_path)
	s = list(p.parts)
	base = s[0]
	c = base
	del s[0]

	to_move = []
	for pl in pctl.multi_playlist:
		for i in reversed(range(len(pl.playlist_ids))):
			if pctl.get_track(pl.playlist_ids[i]).parent_folder_path == move_track.parent_folder_path:
				to_move.append(pl.playlist_ids[i])

	to_move = list(set(to_move))

	for level in s:
		upper = c
		c = os.path.join(c, level)

		t_artist = match_track.artist
		ta_artist = match_track.album_artist

		t_artist = filename_safe(t_artist)
		ta_artist = filename_safe(ta_artist)

		if (len(t_artist) > 0 and t_artist in level) or \
				(len(ta_artist) > 0 and ta_artist in level):

			logging.info("found target artist level")
			logging.info(t_artist)
			logging.info("Upper folder is: " + upper)

			if len(move_path) < 4:
				show_message(_("Safety interupt! The source path seems oddly short."), move_path, mode="error")
				return

			if not os.path.isdir(upper):
				show_message(_("The target directory is missing!"), upper, mode="warning")
				return

			if not os.path.isdir(move_path):
				show_message(_("The source directory is missing!"), move_path, mode="warning")
				return

			protect = ("", "Documents", "Music", "Desktop", "Downloads")
			for fo in protect:
				if move_path.strip("\\/") == os.path.join(os.path.expanduser("~"), fo).strip("\\/"):
					show_message(_("Better not do anything to that folder!"), os.path.join(os.path.expanduser("~"), fo),
						mode="warning")
					return

			if directory_size(move_path) > 3000000000:
				show_message(_("Folder size safety limit reached! (3GB)"), move_path, mode="warning")
				return

			if len(next(os.walk(move_path))[2]) > max(20, len(to_move) * 2):
				show_message(_("Safety interupt! The source folder seems to have many files."), move_path, mode="warning")
				return

			artist = move_track.artist
			if move_track.album_artist != "":
				artist = move_track.album_artist

			artist = filename_safe(artist)

			if artist == "":
				show_message(_("The track needs to have an artist name."))
				return

			artist_folder = os.path.join(upper, artist)

			logging.info("Target will be: " + artist_folder)

			if os.path.isdir(artist_folder):
				logging.info("The target artist folder already exists")
			else:
				logging.info("Need to make artist folder")
				os.makedirs(artist_folder)

			logging.info("The folder to be moved is: " + move_path)
			load_order = LoadClass()
			load_order.target = os.path.join(artist_folder, move_track.parent_folder_name)
			load_order.playlist = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int

			insert = shift_selection[0]
			old_insert = insert
			while insert < len(default_playlist) and pctl.master_library[
				pctl.multi_playlist[pctl.active_playlist_viewing].playlist_ids[insert]].parent_folder_name == \
					pctl.master_library[
						pctl.multi_playlist[pctl.active_playlist_viewing].playlist_ids[old_insert]].parent_folder_name:
				insert += 1

			load_order.playlist_position = insert

			move_jobs.append(
				(move_path, os.path.join(artist_folder, move_track.parent_folder_name), move,
				move_track.parent_folder_name, load_order))
			tauon.thread_manager.ready("worker")
			# Remove all tracks with the old paths
			for pl in pctl.multi_playlist:
				for i in reversed(range(len(pl.playlist_ids))):
					if pctl.get_track(pl.playlist_ids[i]).parent_folder_path == move_track.parent_folder_path:
						del pl.playlist_ids[i]

			break
	else:
		show_message(_("Could not find a folder with the artist's name to match level at."))
		return

	# for file in os.listdir(artist_folder):
	#

	if album_mode:
		prep_gal()
		reload_albums(True)

	cargo.clear()
	gui.lightning_copy = False


def paste(playlist_no=None, track_id=None):
	clip = copy_from_clipboard()
	logging.info(clip)
	if "tidal.com/album/" in clip:
		logging.info(clip)
		num = clip.split("/")[-1].split("?")[0]
		if num and num.isnumeric():
			logging.info(num)
			tauon.tidal.append_album(num)
		clip = False

	elif "tidal.com/playlist/" in clip:
		logging.info(clip)
		num = clip.split("/")[-1].split("?")[0]
		tauon.tidal.playlist(num)
		clip = False

	elif "tidal.com/mix/" in clip:
		logging.info(clip)
		num = clip.split("/")[-1].split("?")[0]
		tauon.tidal.mix(num)
		clip = False

	elif "tidal.com/browse/track/" in clip:
		logging.info(clip)
		num = clip.split("/")[-1].split("?")[0]
		tauon.tidal.track(num)
		clip = False

	elif "tidal.com/browse/artist/" in clip:
		logging.info(clip)
		num = clip.split("/")[-1].split("?")[0]
		tauon.tidal.artist(num)
		clip = False

	elif "spotify" in clip:
		cargo.clear()
		for link in clip.split("\n"):
			logging.info(link)
			link = link.strip()
			if clip.startswith(("https://open.spotify.com/track/", "spotify:track:")):
				tauon.spot_ctl.append_track(link)
			elif clip.startswith(("https://open.spotify.com/album/", "spotify:album:")):
				l = tauon.spot_ctl.append_album(link, return_list=True)
				if l:
					cargo.extend(l)
			elif clip.startswith("https://open.spotify.com/playlist/"):
				tauon.spot_ctl.playlist(link)
		if album_mode:
			reload_albums()
		gui.pl_update += 1
		clip = False

	found = False
	if clip:
		clip = clip.split("\n")
		for i, line in enumerate(clip):
			if line.startswith(("file://", "/")):
				target = str(urllib.parse.unquote(line)).replace("file://", "").replace("\r", "")
				load_order = LoadClass()
				load_order.target = target
				load_order.playlist = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int

				if playlist_no is not None:
					load_order.playlist = pl_to_id(playlist_no)
				if track_id is not None:
					load_order.playlist_position = r_menu_position

				load_orders.append(copy.deepcopy(load_order))
				found = True

	if not found:

		if playlist_no is None:
			if track_id is None:
				transfer(0, (2, 3))
			else:
				transfer(track_id, (2, 2))
		else:
			append_playlist(playlist_no)

	gui.pl_update += 1


def s_cut():
	s_copy()
	del_selected()


playlist_menu.add(MenuItem("Paste", paste, paste_deco))


def paste_playlist_coast_fire():
	url = None
	if tauon.spot_ctl.coasting and pctl.playing_state == 3:
		url = tauon.spot_ctl.get_album_url_from_local(pctl.playing_object())
	elif pctl.playing_ready() and "spotify-album-url" in pctl.playing_object().misc:
		url = pctl.playing_object().misc["spotify-album-url"]
	if url:
		default_playlist.extend(tauon.spot_ctl.append_album(url, return_list=True))
	gui.pl_update += 1

def paste_playlist_track_coast_fire():
	url = None
	# if tauon.spot_ctl.coasting and pctl.playing_state == 3:
	#	 url = tauon.spot_ctl.get_album_url_from_local(pctl.playing_object())
	if pctl.playing_ready() and "spotify-track-url" in pctl.playing_object().misc:
		url = pctl.playing_object().misc["spotify-track-url"]
	if url:
		tauon.spot_ctl.append_track(url)
	gui.pl_update += 1


def paste_playlist_coast_album():
	shoot_dl = threading.Thread(target=paste_playlist_coast_fire)
	shoot_dl.daemon = True
	shoot_dl.start()
def paste_playlist_coast_track():
	shoot_dl = threading.Thread(target=paste_playlist_track_coast_fire)
	shoot_dl.daemon = True
	shoot_dl.start()

def paste_playlist_coast_album_deco():
	if tauon.spot_ctl.coasting or tauon.spot_ctl.playing:
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled

	return [line_colour, colours.menu_background, None]


playlist_menu.add(MenuItem(_("Add Playing Spotify Album"), paste_playlist_coast_album, paste_playlist_coast_album_deco,
	show_test=spotify_show_test))
playlist_menu.add(MenuItem(_("Add Playing Spotify Track"), paste_playlist_coast_track, paste_playlist_coast_album_deco,
	show_test=spotify_show_test))

def refind_playing():
	# Refind playing index
	if pctl.playing_ready():
		for i, n in enumerate(default_playlist):
			if pctl.track_queue[pctl.queue_step] == n:
				pctl.playlist_playing_position = i
				break


def del_selected(force_delete=False):
	global shift_selection

	gui.update += 1
	gui.pl_update = 1

	if not shift_selection:
		shift_selection = [pctl.selected_in_playlist]

	if not default_playlist:
		return

	li = []

	for item in reversed(shift_selection):
		if item > len(default_playlist) - 1:
			return

		li.append((item, default_playlist[item]))  # take note for force delete

		# Correct track playing position
		if pctl.active_playlist_playing == pctl.active_playlist_viewing:
			if 0 < pctl.playlist_playing_position + 1 > item:
				pctl.playlist_playing_position -= 1

		del default_playlist[item]

	if force_delete:
		for item in li:

			tr = pctl.get_track(item[1])
			if not tr.is_network:
				try:
					send2trash(tr.fullpath)
					show_message(_("Tracks sent to trash"))
				except Exception:
					logging.exception("One or more tracks could not be sent to trash")
					show_message(_("One or more tracks could not be sent to trash"))

					if force_delete:
						try:
							os.remove(tr.fullpath)
							show_message(_("Files deleted"), mode="info")
						except Exception:
							logging.exception("Error deleting one or more files")
							show_message(_("Error deleting one or more files"), mode="error")

	else:
		undo.bk_tracks(pctl.active_playlist_viewing, li)

	reload()
	tree_view_box.clear_target_pl(pctl.active_playlist_viewing)

	pctl.selected_in_playlist = min(pctl.selected_in_playlist, len(default_playlist) - 1)

	shift_selection = [pctl.selected_in_playlist]
	gui.pl_update += 1
	refind_playing()
	pctl.notify_change()


def force_del_selected():
	del_selected(force_delete=True)


def test_show(dummy):
	return album_mode


def show_in_gal(track: TrackClass, silent: bool = False):
	# goto_album(pctl.playlist_selected)
	gui.gallery_animate_highlight_on = goto_album(pctl.selected_in_playlist)
	if not silent:
		gallery_select_animate_timer.set()


# Create track context menu
track_menu = Menu(195, show_icons=True)

track_menu.add(MenuItem(_("Open Folder"), open_folder, pass_ref=True, pass_ref_deco=True, icon=folder_icon, disable_test=open_folder_disable_test))
track_menu.add(MenuItem(_("Track Info…"), activate_track_box, pass_ref=True, icon=info_icon))


def last_fm_test(ignore):
	if lastfm.connected:
		return True
	return False


def heart_xmenu_colour():
	global r_menu_index
	if love(False, r_menu_index):
		return [245, 60, 60, 255]
	if colours.lm:
		return [255, 150, 180, 255]
	return None


heartx_icon.colour = [55, 55, 55, 255]
heartx_icon.xoff = 1
heartx_icon.yoff = 0
heartx_icon.colour_callback = heart_xmenu_colour


def spot_heart_xmenu_colour():
	if not (pctl.playing_state == 1 or pctl.playing_state == 2):
		return None
	tr = pctl.playing_object()
	if tr and "spotify-liked" in tr.misc:
		return [30, 215, 96, 255]
	return None


spot_heartx_icon.colour = [30, 215, 96, 255]
spot_heartx_icon.xoff = 3
spot_heartx_icon.yoff = 0
spot_heartx_icon.colour_callback = spot_heart_xmenu_colour


def love_decox():
	global r_menu_index

	if love(False, r_menu_index):
		return [colours.menu_text, colours.menu_background, _("Un-Love Track")]
	return [colours.menu_text, colours.menu_background, _("Love Track")]


def love_index():
	global r_menu_index

	notify = False
	if not gui.show_hearts:
		notify = True

	# love(True, r_menu_index)
	shoot_love = threading.Thread(target=love, args=[True, r_menu_index, False, notify])
	shoot_love.daemon = True
	shoot_love.start()


# Mark track as 'liked'
track_menu.add(MenuItem("Love", love_index, love_decox, icon=heartx_icon))

def toggle_spotify_like_ref():
	tr = pctl.get_track(r_menu_index)
	if tr:
		shoot_dl = threading.Thread(target=toggle_spotify_like_active2, args=([tr]))
		shoot_dl.daemon = True
		shoot_dl.start()

def toggle_spotify_like3():
	toggle_spotify_like_active2(pctl.get_track(r_menu_index))

def toggle_spotify_like_row_deco():
	tr = pctl.get_track(r_menu_index)
	text = _("Spotify Like Track")

	# if pctl.playing_state == 0 or not tr or not "spotify-track-url" in tr.misc:
	#	 return [colours.menu_text_disabled, colours.menu_background, text]
	if "spotify-liked" in tr.misc:
		text = _("Un-like Spotify Track")

	return [colours.menu_text, colours.menu_background, text]

def spot_like_show_test(x):

	return spotify_show_test and pctl.get_track(r_menu_index).file_ext == "SPTY"

def spot_heart_menu_colour():
	tr = pctl.get_track(r_menu_index)
	if tr and "spotify-liked" in tr.misc:
		return [30, 215, 96, 255]
	return None

heart_spot_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "heart-menu.png", True))
heart_spot_icon.colour = [30, 215, 96, 255]
heart_spot_icon.xoff = 1
heart_spot_icon.yoff = 0
heart_spot_icon.colour_callback = spot_heart_menu_colour

track_menu.add(MenuItem("Spotify Like Track", toggle_spotify_like_ref, toggle_spotify_like_row_deco, show_test=spot_like_show_test, icon=heart_spot_icon))


def add_to_queue(ref):
	pctl.force_queue.append(queue_item_gen(ref, r_menu_position, pl_to_id(pctl.active_playlist_viewing)))
	queue_timer_set()
	if prefs.stop_end_queue:
		pctl.auto_stop = False


def add_selected_to_queue():
	gui.pl_update += 1
	if prefs.stop_end_queue:
		pctl.auto_stop = False
	if gui.album_tab_mode:
		add_album_to_queue(default_playlist[get_album_info(pctl.selected_in_playlist)[1][0]], pctl.selected_in_playlist)
		queue_timer_set()
	else:
		pctl.force_queue.append(
			queue_item_gen(default_playlist[pctl.selected_in_playlist],
			pctl.selected_in_playlist,
			pl_to_id(pctl.active_playlist_viewing)))
		queue_timer_set()


def add_selected_to_queue_multi():
	if prefs.stop_end_queue:
		pctl.auto_stop = False
	for index in shift_selection:
		pctl.force_queue.append(
			queue_item_gen(default_playlist[index],
			index,
			pl_to_id(pctl.active_playlist_viewing)))


def queue_timer_set(plural: bool = False, queue_object: TauonQueueItem | None = None) -> None:
	queue_add_timer.set()
	gui.frame_callback_list.append(TestTimer(2.51))
	gui.queue_toast_plural = plural
	if queue_object:
		gui.toast_queue_object = queue_object
	elif pctl.force_queue:
		gui.toast_queue_object = pctl.force_queue[-1]


def split_queue_album(id: int) -> int | None:
	item = pctl.force_queue[0]

	pl = id_to_pl(item.playlist_id)
	if pl is None:
		return None

	playlist = pctl.multi_playlist[pl].playlist_ids

	i = pctl.playlist_playing_position + 1
	parts = []
	album_parent_path = pctl.get_track(item.track_id).parent_folder_path

	while i < len(playlist):
		if pctl.get_track(playlist[i]).parent_folder_path != album_parent_path:
			break

		parts.append((playlist[i], i))
		i += 1

	del pctl.force_queue[0]

	for part in reversed(parts):
		pctl.force_queue.insert(0, queue_item_gen(part[0], part[1], item.type))
	return (len(parts))


def add_to_queue_next(ref: int) -> None:
	if pctl.force_queue and pctl.force_queue[0].album_stage == 1:
		split_queue_album(None)

	pctl.force_queue.insert(0, queue_item_gen(ref, r_menu_position, pl_to_id(pctl.active_playlist_viewing)))


# def toggle_queue(mode: int = 0) -> bool:
#	 if mode == 1:
#		 return prefs.show_queue
#	 prefs.show_queue ^= True
#	 prefs.show_queue ^= True


track_menu.add(MenuItem(_("Add to Queue"), add_to_queue, pass_ref=True, hint="MB3"))

track_menu.add(MenuItem(_("↳ After Current Track"), add_to_queue_next, pass_ref=True, show_test=test_shift))

track_menu.add(MenuItem(_("Show in Gallery"), show_in_gal, pass_ref=True, show_test=test_show))

track_menu.add_sub(_("Meta…"), 160)

track_menu.br()
# track_menu.add('Cut', s_cut, pass_ref=False)
# track_menu.add('Remove', del_selected)
track_menu.add(MenuItem(_("Copy"), s_copy, pass_ref=False))

# track_menu.add(_('Paste + Transfer Folder'), lightning_paste, pass_ref=False, show_test=lightning_move_test)

track_menu.add(MenuItem(_("Paste"), menu_paste, paste_deco, pass_ref=True))


def delete_track(track_ref):
	tr = pctl.get_track(track_ref)
	fullpath = tr.fullpath

	if system == "Windows" or msys:
		fullpath = fullpath.replace("/", "\\")

	if tr.is_network:
		show_message(_("Cannot delete a network track"))
		return

	while track_ref in default_playlist:
		default_playlist.remove(track_ref)

	try:
		send2trash(fullpath)

		if os.path.exists(fullpath):
			try:
				os.remove(fullpath)
				show_message(_("File deleted"), fullpath, mode="info")
			except Exception:
				logging.exception("Error deleting file")
				show_message(_("Error deleting file"), fullpath, mode="error")
		else:
			show_message(_("File moved to trash"))

	except Exception:
		try:
			os.remove(fullpath)
			show_message(_("File deleted"), fullpath, mode="info")
		except Exception:
			logging.exception("Error deleting file")
			show_message(_("Error deleting file"), fullpath, mode="error")

	reload()
	refind_playing()
	pctl.notify_change()


track_menu.add(MenuItem(_("Delete Track File"), delete_track, pass_ref=True, icon=delete_icon, show_test=test_shift))

track_menu.br()


def rename_tracks_deco(track_id: int):
	if key_shift_down or key_shiftr_down:
		return [colours.menu_text, colours.menu_background, _("Rename (Single track)")]
	return [colours.menu_text, colours.menu_background, _("Rename Tracks…")]


# rename_tracks_icon.colour = [244, 241, 66, 255]
# rename_tracks_icon.colour = [204, 255, 66, 255]
rename_tracks_icon.colour = [204, 100, 205, 255]
rename_tracks_icon.xoff = 1
track_menu.add_to_sub(0, MenuItem(_("Rename Tracks…"), rename_track_box.activate, rename_tracks_deco, pass_ref=True,
	pass_ref_deco=True, icon=rename_tracks_icon, disable_test=rename_track_box.disable_test))


def activate_trans_editor():
	trans_edit_box.active = True


track_menu.add_to_sub(0, MenuItem(_("Edit fields…"), activate_trans_editor))


def delete_folder(index, force=False):
	track = pctl.master_library[index]

	if track.is_network:
		show_message(_("Cannot physically delete"), _("One or more tracks is from a network location!"), mode="info")
		return

	old = track.parent_folder_path

	if len(old) < 5:
		show_message(_("This folder path seems short, I don't wanna try delete that"), mode="warning")
		return

	if not os.path.exists(old):
		show_message(_("Error deleting folder. The folder seems to be missing."), _("It's gone! Just gone!"), mode="error")
		return

	protect = ("", "Documents", "Music", "Desktop", "Downloads")

	for fo in protect:
		if old.strip("\\/") == os.path.join(os.path.expanduser("~"), fo).strip("\\/"):
			show_message(_("Woah, careful there!"), _("I don't think we should delete that folder."), mode="warning")
			return

	if directory_size(old) > 1500000000:
		show_message(_("Delete size safety limit reached! (1.5GB)"), old, mode="warning")
		return

	try:

		if pctl.playing_state > 0 and os.path.normpath(
				pctl.master_library[pctl.track_queue[pctl.queue_step]].parent_folder_path) == os.path.normpath(old):
			pctl.stop(True)

		if force:
			shutil.rmtree(old)
		elif system == "Windows" or msys:
			send2trash(old.replace("/", "\\"))
		else:
			send2trash(old)

		for i in reversed(range(len(default_playlist))):

			if old == pctl.master_library[default_playlist[i]].parent_folder_path:
				del default_playlist[i]

		if not os.path.exists(old):
			if force:
				show_message(_("Folder deleted."), old, mode="done")
			else:
				show_message(_("Folder sent to trash."), old, mode="done")
		else:
			show_message(_("Hmm, its still there"), old, mode="error")

		if album_mode:
			prep_gal()
			reload_albums()

	except Exception:
		if force:
			logging.exception("Unable to comply, could not delete folder. Try checking permissions.")
			show_message(_("Unable to comply."), _("Could not delete folder. Try checking permissions."), mode="error")
		else:
			logging.exception("Folder could not be trashed, try again while holding shift to force delete.")
			show_message(_("Folder could not be trashed."), _("Try again while holding shift to force delete."),
				mode="error")

	tree_view_box.clear_target_pl(pctl.active_playlist_viewing)
	gui.pl_update += 1
	pctl.notify_change()


def rename_parent(index: int, template: str) -> None:
	# template = prefs.rename_folder_template
	template = template.strip("/\\")
	track = pctl.master_library[index]

	if track.is_network:
		show_message(_("Cannot rename"), _("One or more tracks is from a network location!"), mode="info")
		return

	old = track.parent_folder_path
	#logging.info(old)

	new = parse_template2(template, track)

	if len(new) < 1:
		show_message(_("Rename error."), _("The generated name is too short"), mode="warning")
		return

	if len(old) < 5:
		show_message(_("Rename error."), _("This folder path seems short, I don't wanna try rename that"), mode="warning")
		return

	if not os.path.exists(old):
		show_message(_("Rename Failed. The original folder is missing."), mode="warning")
		return

	protect = ("", "Documents", "Music", "Desktop", "Downloads")

	for fo in protect:
		if os.path.normpath(old) == os.path.normpath(os.path.join(os.path.expanduser("~"), fo)):
			show_message(_("Woah, careful there!"), _("I don't think we should rename that folder."), mode="warning")
			return

	logging.info(track.parent_folder_path)
	re = os.path.dirname(track.parent_folder_path.rstrip("/\\"))
	logging.info(re)
	new_parent_path = os.path.join(re, new)
	logging.info(new_parent_path)

	pre_state = 0

	for key, object in pctl.master_library.items():

		if object.fullpath == "":
			continue

		if old == object.parent_folder_path:

			new_fullpath = os.path.join(new_parent_path, object.filename)

			if os.path.normpath(new_parent_path) == os.path.normpath(old):
				show_message(_("The folder already has that name."))
				return

			if os.path.exists(new_parent_path):
				show_message(_("Rename Failed."), _("A folder with that name already exists"), mode="warning")
				return

			if key == pctl.track_queue[pctl.queue_step] and pctl.playing_state > 0:
				pre_state = pctl.stop(True)

			object.parent_folder_name = new
			object.parent_folder_path = new_parent_path
			object.fullpath = new_fullpath

			search_string_cache.pop(object.index, None)
			search_dia_string_cache.pop(object.index, None)

		# Fix any other tracks paths that contain the old path
		if os.path.normpath(object.fullpath)[:len(old)] == os.path.normpath(old) \
				and os.path.normpath(object.fullpath)[len(old)] in ("/", "\\"):
			object.fullpath = os.path.join(new_parent_path, object.fullpath[len(old):].lstrip("\\/"))
			object.parent_folder_path = os.path.join(new_parent_path, object.parent_folder_path[len(old):].lstrip("\\/"))

			search_string_cache.pop(object.index, None)
			search_dia_string_cache.pop(object.index, None)

	if new_parent_path is not None:
		try:
			os.rename(old, new_parent_path)
			logging.info(new_parent_path)
		except Exception:
			logging.exception("Rename failed, something went wrong!")
			show_message(_("Rename Failed!"), _("Something went wrong, sorry."), mode="error")
			return

	show_message(_("Folder renamed."), _("Renamed to: {name}").format(name=new), mode="done")

	if pre_state == 1:
		pctl.revert()

	tree_view_box.clear_target_pl(pctl.active_playlist_viewing)
	pctl.notify_change()


def rename_folders_disable_test(index: int) -> bool:
	return pctl.get_track(index).is_network

def rename_folders(index: int):
	global track_box
	global rename_index
	global input_text

	track_box = False
	rename_index = index

	if rename_folders_disable_test(index):
		show_message(_("Not applicable for a network track."))
		return

	gui.rename_folder_box = True
	input_text = ""
	shift_selection.clear()

	global quick_drag
	global playlist_hold
	quick_drag = False
	playlist_hold = False


mod_folder_icon.colour = [229, 98, 98, 255]
track_menu.add_to_sub(0, MenuItem(_("Modify Folder…"), rename_folders, pass_ref=True, pass_ref_deco=True, icon=mod_folder_icon, disable_test=rename_folders_disable_test))


def move_folder_up(index: int, do: bool = False) -> bool | None:
	track = pctl.master_library[index]

	if track.is_network:
		show_message(_("Cannot move"), _("One or more tracks is from a network location!"), mode="info")
		return None

	parent_folder = os.path.dirname(track.parent_folder_path)
	folder_name = track.parent_folder_name
	move_target = track.parent_folder_path
	upper_folder = os.path.dirname(parent_folder)

	if not os.path.exists(track.parent_folder_path):
		if do:
			show_message(_("Error shifting directory"), _("The directory does not appear to exist"), mode="warning")
		return False

	if len(os.listdir(parent_folder)) > 1:
		return False

	if do is False:
		return True

	pre_state = 0
	if pctl.playing_state > 0 and track.parent_folder_path in pctl.playing_object().parent_folder_path:
		pre_state = pctl.stop(True)

	try:

		# Rename the track folder to something temporary
		os.rename(move_target, os.path.join(parent_folder, "RMTEMP000"))

		# Move the temporary folder up 2 levels
		shutil.move(os.path.join(parent_folder, "RMTEMP000"), upper_folder)

		# Delete the old directory that contained the original folder
		shutil.rmtree(parent_folder)

		# Rename the moved folder back to its original name
		os.rename(os.path.join(upper_folder, "RMTEMP000"), os.path.join(upper_folder, folder_name))

	except Exception as e:
		logging.exception("System Error!")
		show_message(_("System Error!"), str(e), mode="error")

	# Fix any other tracks paths that contain the old path
	old = track.parent_folder_path
	new_parent_path = os.path.join(upper_folder, folder_name)
	for key, object in pctl.master_library.items():

		if os.path.normpath(object.fullpath)[:len(old)] == os.path.normpath(old) \
				and os.path.normpath(object.fullpath)[len(old)] in ("/", "\\"):
			object.fullpath = os.path.join(new_parent_path, object.fullpath[len(old):].lstrip("\\/"))
			object.parent_folder_path = os.path.join(
				new_parent_path, object.parent_folder_path[len(old):].lstrip("\\/"))

			search_string_cache.pop(object.index, None)
			search_dia_string_cache.pop(object.index, None)

			logging.info(object.fullpath)
			logging.info(object.parent_folder_path)

	if pre_state == 1:
		pctl.revert()


def clean_folder(index: int, do: bool = False) -> int | None:
	track = pctl.master_library[index]

	if track.is_network:
		show_message(_("Cannot clean"), _("One or more tracks is from a network location!"), mode="info")
		return None

	folder = track.parent_folder_path
	found = 0
	to_purge = []
	if not os.path.isdir(folder):
		return 0
	try:
		for item in os.listdir(folder):
			if (item[:8] == "AlbumArt" and ".jpg" in item.lower()) \
					or item == "desktop.ini" \
					or item == "Thumbs.db" \
					or item == ".DS_Store":

				to_purge.append(item)
				found += 1
			elif item == "__MACOSX" and os.path.isdir(os.path.join(folder, item)):
				found += 1
				found += 1
				if do:
					logging.info("Deleting Folder: " + os.path.join(folder, item))
					shutil.rmtree(os.path.join(folder, item))

		if do:
			for item in to_purge:
				if os.path.isfile(os.path.join(folder, item)):
					logging.info("Deleting File: " + os.path.join(folder, item))
					os.remove(os.path.join(folder, item))
			# clear_img_cache()

			for track_id in default_playlist:
				if pctl.get_track(track_id).parent_folder_path == folder:
					clear_track_image_cache(pctl.get_track(track_id))

	except Exception:
		logging.exception("Error deleting files, may not have permission or file may be set to read-only")
		show_message(_("Error deleting files."), _("May not have permission or file may be set to read-only"), mode="warning")
		return 0

	return found


def reset_play_count(index: int):
	star_store.remove(index)


# track_menu.add_to_sub("Reset Track Play Count", 0, reset_play_count, pass_ref=True)


def vacuum_playtimes(index: int):
	todo = []
	for k in default_playlist:
		if pctl.master_library[index].parent_folder_name == pctl.master_library[k].parent_folder_name:
			todo.append(k)

	for track in todo:

		tr = pctl.get_track(track)

		total_playtime = 0
		flags = ""

		to_del = []

		for key, value in star_store.db.items():
			if key[0].lower() == tr.artist.lower() and tr.artist and key[1].lower().replace(
				" ", "") == tr.title.lower().replace(
				" ", "") and tr.title:
				to_del.append(key)
				total_playtime += value[0]
				flags = "".join(set(flags + value[1]))

		for key in to_del:
			del star_store.db[key]

		key = star_store.object_key(tr)
		value = [total_playtime, flags, 0]
		if key not in star_store.db:
			logging.info("Saving value")
			star_store.db[key] = value
		else:
			logging.error("ERROR KEY ALREADY HERE?")


def reload_metadata(input, keep_star: bool = True) -> None:
	global todo

	# vacuum_playtimes(index)
	# return
	todo = []

	if isinstance(input, list):
		todo = input

	else:
		for k in default_playlist:
			if pctl.master_library[input].parent_folder_path == pctl.master_library[k].parent_folder_path:
				todo.append(pctl.master_library[k])

	for i in reversed(range(len(todo))):
		if todo[i].is_cue:
			del todo[i]

	for track in todo:

		search_string_cache.pop(track.index, None)
		search_dia_string_cache.pop(track.index, None)

		#logging.info('Reloading Metadata for ' + track.filename)
		if keep_star:
			to_scan.append(track.index)
		else:
			# if keep_star:
			#     star = star_store.full_get(track.index)
			#     star_store.remove(track.index)

			pctl.master_library[track.index] = tag_scan(track)

			# if keep_star:
			#     if star is not None and (star[0] > 0 or star[1] or star[2] > 0):
			#         star_store.merge(track.index, star)

			pctl.notify_change()

	gui.pl_update += 1
	tauon.thread_manager.ready("worker")


def reload_metadata_selection() -> None:
	cargo = []
	for item in shift_selection:
		cargo.append(default_playlist[item])

	for k in cargo:
		if pctl.master_library[k].is_cue == False:
			to_scan.append(k)
	tauon.thread_manager.ready("worker")



def editor(index: int | None) -> None:
	todo = []
	obs = []

	if key_shift_down and index is not None:
		todo = [index]
		obs = [pctl.master_library[index]]
	elif index is None:
		for item in shift_selection:
			todo.append(default_playlist[item])
			obs.append(pctl.master_library[default_playlist[item]])
		if len(todo) > 0:
			index = todo[0]
	else:
		for k in default_playlist:
			if pctl.master_library[index].parent_folder_path == pctl.master_library[k].parent_folder_path:
				if pctl.master_library[k].is_cue == False:
					todo.append(k)
					obs.append(pctl.master_library[k])

	# Keep copy of play times
	old_stars = []
	for track in todo:
		item = []
		item.append(pctl.get_track(track))
		item.append(star_store.key(track))
		item.append(star_store.full_get(track))
		old_stars.append(item)

	file_line = ""
	for track in todo:
		file_line += ' "'
		file_line += pctl.master_library[track].fullpath
		file_line += '"'

	if system == "Windows" or msys:
		file_line = file_line.replace("/", "\\")

	prefix = ""
	app = prefs.tag_editor_target

	if (system == "Windows" or msys) and app:
		if app[0] != '"':
			app = '"' + app
		if app[-1] != '"':
			app = app + '"'

	app_switch = ""

	ok = False

	prefix = launch_prefix

	if system == "Linux":
		ok = whicher(prefs.tag_editor_target)
	else:

		if not os.path.isfile(prefs.tag_editor_target.strip('"')):
			logging.info(prefs.tag_editor_target)
			show_message(_("Application not found"), prefs.tag_editor_target, mode="info")
			return

		ok = True

	if not ok:
		show_message(_("Tag editor app does not appear to be installed."), mode="warning")

		if flatpak_mode:
			show_message(
				_("App not found on host OR insufficient Flatpak permissions."),
				_(" For details, see {link}").format(link="https://github.com/Taiko2k/Tauon/wiki/Flatpak-Extra-Steps"),
				mode="bubble")

		return

	if "picard" in prefs.tag_editor_target:
		app_switch = " --d "

	line = prefix + app + app_switch + file_line

	show_message(
		prefs.tag_editor_name + " launched.", "Fields will be updated once application is closed.", mode="arrow")
	gui.update = 1

	complete = subprocess.run(shlex.split(line), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

	if "picard" in prefs.tag_editor_target:
		r = complete.stderr.decode()
		for line in r.split("\n"):
			if "file._rename" in line and " Moving file " in line:
				a, b = line.split(" Moving file ")[1].split(" => ")
				a = a.strip("'").strip('"')
				b = b.strip("'").strip('"')

				for track in todo:
					if pctl.master_library[track].fullpath == a:
						pctl.master_library[track].fullpath = b
						pctl.master_library[track].filename = os.path.basename(b)
						logging.info("External Edit: File rename detected.")
						logging.info("    Renaming: " + a)
						logging.info("          To: " + b)
						break
				else:
					logging.warning("External Edit: A file rename was detected but track was not found.")

	gui.message_box = False
	reload_metadata(obs, keep_star=False)

	# Re apply playtime data in case file names change
	for item in old_stars:

		old_key = item[1]
		old_value = item[2]

		if not old_value:  # ignore if there was no old playcount metadata
			continue

		new_key = star_store.object_key(item[0])
		new_value = star_store.full_get(item[0].index)

		if old_key == new_key:
			continue

		if new_value is None:
			new_value = [0, "", 0]

		new_value[0] += old_value[0]
		new_value[1] = "".join(set(new_value[1] + old_value[1]))

		if old_key in star_store.db:
			del star_store.db[old_key]

		star_store.db[new_key] = new_value

	gui.pl_update = 1
	gui.update = 1
	pctl.notify_change()


def launch_editor(index: int):
	if snap_mode:
		show_message(_("Sorry, this feature isn't (yet) available with Snap."))
		return

	if launch_editor_disable_test(index):
		show_message(_("Cannot edit tags of a network track."))
		return

	mini_t = threading.Thread(target=editor, args=[index])
	mini_t.daemon = True
	mini_t.start()

def launch_editor_selection_disable_test(index: int):
	for position in shift_selection:
		if pctl.get_track(default_playlist[position]).is_network:
			return True
	return False

def launch_editor_selection(index: int):
	if launch_editor_selection_disable_test(index):
		show_message(_("Cannot edit tags of a network track."))
		return

	mini_t = threading.Thread(target=editor, args=[None])
	mini_t.daemon = True
	mini_t.start()


# track_menu.add('Reload Metadata', reload_metadata, pass_ref=True)
track_menu.add_to_sub(0, MenuItem(_("Rescan Tags"), reload_metadata, pass_ref=True))

mbp_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "mbp-g.png"))
mbp_icon.base_asset = asset_loader(scaled_asset_directory, loaded_asset_dc, "mbp-gs.png")

mbp_icon.xoff = 2
mbp_icon.yoff = -1

if gui.scale == 1.25:
	mbp_icon.yoff = 0

edit_icon = None
if prefs.tag_editor_name == "Picard":
	edit_icon = mbp_icon


def edit_deco(index: int):
	if key_shift_down or key_shiftr_down:
		return [colours.menu_text, colours.menu_background, prefs.tag_editor_name + " (Single track)"]
	return [colours.menu_text, colours.menu_background, _("Edit with ") + prefs.tag_editor_name]

def launch_editor_disable_test(index: int):
	return pctl.get_track(index).is_network

track_menu.add_to_sub(0, MenuItem(_("Edit with"), launch_editor, pass_ref=True, pass_ref_deco=True, icon=edit_icon, render_func=edit_deco, disable_test=launch_editor_disable_test))


def show_lyrics_menu(index: int):
	global track_box
	track_box = False
	enter_showcase_view(track_id=r_menu_index)
	inp.mouse_click = False


track_menu.add_to_sub(0, MenuItem(_("Lyrics..."), show_lyrics_menu, pass_ref=True))


def recode(text, enc):
	return text.encode("Latin-1", "ignore").decode(enc, "ignore")


def intel_moji(index: int):
	gui.pl_update += 1
	gui.update += 1

	track = pctl.master_library[index]

	lot = []

	for item in default_playlist:

		if track.album == pctl.master_library[item].album and \
				track.parent_folder_name == pctl.master_library[item].parent_folder_name:
			lot.append(item)

	lot = set(lot)

	l_artist = track.artist.encode("Latin-1", "ignore")
	l_album = track.album.encode("Latin-1", "ignore")
	detect = None

	if track.artist not in track.parent_folder_path:
		for enc in encodings:
			try:
				q_artist = l_artist.decode(enc)
				if q_artist.strip(" ") in track.parent_folder_path.strip(" "):
					detect = enc
					break
			except Exception:
				logging.exception("Error decoding artist")
				continue

	if detect is None and track.album not in track.parent_folder_path:
		for enc in encodings:
			try:
				q_album = l_album.decode(enc)
				if q_album in track.parent_folder_path:
					detect = enc
					break
			except Exception:
				logging.exception("Error decoding album")
				continue

	for item in lot:
		t_track = pctl.master_library[item]

		if detect is None:
			for enc in encodings:
				test = recode(t_track.artist, enc)
				for cha in test:
					if cha in j_chars:
						detect = enc
						logging.info("This looks like Japanese: " + test)
						break
					if detect is not None:
						break

		if detect is None:
			for enc in encodings:
				test = recode(t_track.title, enc)
				for cha in test:
					if cha in j_chars:
						detect = enc
						logging.info("This looks like Japanese: " + test)
						break
					if detect is not None:
						break
		if detect is not None:
			break

	if detect is not None:
		logging.info("Fix Mojibake: Detected encoding as: " + detect)
		for item in lot:
			track = pctl.master_library[item]
			# key = pctl.master_library[item].title + pctl.master_library[item].filename
			key = star_store.full_get(item)
			star_store.remove(item)

			track.title = recode(track.title, detect)
			track.album = recode(track.album, detect)
			track.artist = recode(track.artist, detect)
			track.album_artist = recode(track.album_artist, detect)
			track.genre = recode(track.genre, detect)
			track.comment = recode(track.comment, detect)
			track.lyrics = recode(track.lyrics, detect)

			if key != None:
				star_store.insert(item, key)

			search_string_cache.pop(track.index, None)
			search_dia_string_cache.pop(track.index, None)

	else:
		show_message(_("Autodetect failed"))


track_menu.add_to_sub(0, MenuItem(_("Fix Mojibake"), intel_moji, pass_ref=True))


def sel_to_car():
	global default_playlist
	cargo = []

	for item in shift_selection:
		cargo.append(default_playlist[item])


# track_menu.add_to_sub("Copy Playlist", 1, transfer, pass_ref=True, args=[1, 3])
def cut_selection():
	sel_to_car()
	del_selected()


def clip_ar_al(index: int):
	line = pctl.master_library[index].artist + " - " + pctl.master_library[index].album
	SDL_SetClipboardText(line.encode("utf-8"))


def clip_ar(index: int):
	if pctl.master_library[index].album_artist != "":
		line = pctl.master_library[index].album_artist
	else:
		line = pctl.master_library[index].artist
	SDL_SetClipboardText(line.encode("utf-8"))


def clip_title(index: int):
	n_track = pctl.master_library[index]

	if not prefs.use_title and n_track.album_artist != "" and n_track.album != "":
		line = n_track.album_artist + " - " + n_track.album
	else:
		line = n_track.parent_folder_name

	SDL_SetClipboardText(line.encode("utf-8"))


selection_menu = Menu(200, show_icons=False)
folder_menu = Menu(193, show_icons=True)

folder_menu.add(MenuItem(_("Open Folder"), open_folder, pass_ref=True, pass_ref_deco=True, icon=folder_icon, disable_test=open_folder_disable_test))

folder_menu.add(MenuItem(_("Modify Folder…"), rename_folders, pass_ref=True, pass_ref_deco=True, icon=mod_folder_icon, disable_test=rename_folders_disable_test))
folder_tree_menu.add(MenuItem(_("Modify Folder…"), rename_folders, pass_ref=True, pass_ref_deco=True, icon=mod_folder_icon, disable_test=rename_folders_disable_test))
# folder_menu.add(_("Add Album to Queue"), add_album_to_queue, pass_ref=True)
folder_menu.add(MenuItem(_("Add Album to Queue"), add_album_to_queue, pass_ref=True))
folder_menu.add(MenuItem(_("Enqueue Album Next"), add_album_to_queue_fc, pass_ref=True))

gallery_menu.add(MenuItem(_("Modify Folder…"), rename_folders, pass_ref=True, pass_ref_deco=True, icon=mod_folder_icon, disable_test=rename_folders_disable_test))

folder_menu.add(MenuItem(_("Rename Tracks…"), rename_track_box.activate, rename_tracks_deco,
	pass_ref=True, pass_ref_deco=True, icon=rename_tracks_icon, disable_test=rename_track_box.disable_test))
folder_tree_menu.add(MenuItem(_("Rename Tracks…"), rename_track_box.activate, pass_ref=True, pass_ref_deco=True, icon=rename_tracks_icon, disable_test=rename_track_box.disable_test))

if not snap_mode:
	folder_menu.add(MenuItem("Edit with", launch_editor_selection, pass_ref=True,
		pass_ref_deco=True, icon=edit_icon, render_func=edit_deco, disable_test=launch_editor_selection_disable_test))

folder_tree_menu.add(MenuItem(_("Add Album to Queue"), add_album_to_queue, pass_ref=True))
folder_tree_menu.add(MenuItem(_("Enqueue Album Next"), add_album_to_queue_fc, pass_ref=True))

folder_tree_menu.br()
folder_tree_menu.add(MenuItem(_("Collapse All"), collapse_tree, collapse_tree_deco))
folder_tree_menu.add(MenuItem("lock", lock_folder_tree, lock_folder_tree_deco))


def lightning_copy():
	s_copy()
	gui.lightning_copy = True


# selection_menu.br()

def toggle_transcode(mode: int = 0) -> bool:
	if mode == 1:
		return prefs.enable_transcode
	prefs.enable_transcode ^= True
	return None


def toggle_chromecast(mode: int = 0) -> bool:
	if mode == 1:
		return prefs.show_chromecast
	prefs.show_chromecast ^= True
	return None


def toggle_transfer(mode: int = 0) -> bool:
	if mode == 1:
		return prefs.show_transfer
	prefs.show_transfer ^= True

	if prefs.show_transfer:
		show_message(
			_("Warning! Using this function moves physical folders."),
			_("This menu entry appears after selecting 'copy'. See manual (github wiki) for more info."),
			mode="info")
	return None


transcode_icon.colour = [239, 74, 157, 255]


def transcode_deco():
	if key_shift_down or key_shiftr_down:
		return [colours.menu_text, colours.menu_background, _("Transcode Single")]
	return [colours.menu_text, colours.menu_background, _("Transcode Folder")]


folder_menu.add(MenuItem(_("Rescan Tags"), reload_metadata, pass_ref=True))
folder_menu.add(MenuItem(_("Edit fields…"), activate_trans_editor))
folder_menu.add(MenuItem(_("Vacuum Playtimes"), vacuum_playtimes, pass_ref=True, show_test=test_shift))
folder_menu.add(MenuItem(_("Transcode Folder"), convert_folder, transcode_deco, pass_ref=True, icon=transcode_icon,
	show_test=toggle_transcode))
gallery_menu.add(MenuItem(_("Transcode Folder"), convert_folder, transcode_deco, pass_ref=True, icon=transcode_icon,
	show_test=toggle_transcode))
folder_menu.br()

tauon.spot_ctl.cache_saved_albums = spot_cache_saved_albums

# Copy album title text to clipboard
folder_menu.add(MenuItem(_('Copy "Artist - Album"'), clip_title, pass_ref=True))


def get_album_spot_url(track_id: int):
	track_object = pctl.get_track(track_id)
	url = tauon.spot_ctl.get_album_url_from_local(track_object)
	if url:
		copy_to_clipboard(url)
		show_message(_("URL copied to clipboard"), mode="done")
	else:
		show_message(_("No results found"))


def get_album_spot_url_deco(track_id: int):
	track_object = pctl.get_track(track_id)
	if "spotify-album-url" in track_object.misc:
		text = _("Copy Spotify Album URL")
	else:
		text = _("Lookup Spotify Album URL")
	return [colours.menu_text, colours.menu_background, text]


folder_menu.add(MenuItem("Lookup Spotify Album URL", get_album_spot_url, get_album_spot_url_deco, pass_ref=True,
	pass_ref_deco=True, show_test=spotify_show_test, icon=spot_icon))


def add_to_spotify_library_deco(track_id: int):
	track_object = pctl.get_track(track_id)
	text = _("Save Album to Spotify")
	if track_object.file_ext != "SPTY":
		return (colours.menu_text_disabled, colours.menu_background, text)

	album_url = track_object.misc.get("spotify-album-url")
	if album_url and album_url in tauon.spot_ctl.cache_saved_albums:
		text = _("Un-save Spotify Album")

	return (colours.menu_text, colours.menu_background, text)


def add_to_spotify_library2(album_url: str) -> None:
	if album_url in tauon.spot_ctl.cache_saved_albums:
		tauon.spot_ctl.remove_album_from_library(album_url)
	else:
		tauon.spot_ctl.add_album_to_library(album_url)

	for i, p in enumerate(pctl.multi_playlist):
		code = pctl.gen_codes.get(p.uuid_int)
		if code and code.startswith("sal"):
			logging.info("Fetching Spotify Library...")
			regenerate_playlist(i, silent=True)


def add_to_spotify_library(track_id: int) -> None:
	track_object = pctl.get_track(track_id)
	album_url = track_object.misc.get("spotify-album-url")
	if track_object.file_ext != "SPTY" or not album_url:
		return

	shoot_dl = threading.Thread(target=add_to_spotify_library2, args=([album_url]))
	shoot_dl.daemon = True
	shoot_dl.start()


folder_menu.add(MenuItem("Add to Spotify Library", add_to_spotify_library, add_to_spotify_library_deco, pass_ref=True,
	pass_ref_deco=True, show_test=spotify_show_test, icon=spot_icon))


# Copy artist name text to clipboard
# folder_menu.add(_('Copy "Artist"'), clip_ar, pass_ref=True)

def selection_queue_deco():
	total = 0
	for item in shift_selection:
		total += pctl.get_track(default_playlist[item]).length

	total = get_hms_time(total)

	text = (_("Queue {N}").format(N=len(shift_selection))) + f" [{total}]"

	return [colours.menu_text, colours.menu_background, text]


selection_menu.add(MenuItem(_("Add to queue"), add_selected_to_queue_multi, selection_queue_deco))

selection_menu.br()

selection_menu.add(MenuItem(_("Rescan Tags"), reload_metadata_selection))

selection_menu.add(MenuItem(_("Edit fields…"), activate_trans_editor))

selection_menu.add(MenuItem(_("Edit with "), launch_editor_selection, pass_ref=True, pass_ref_deco=True, icon=edit_icon, render_func=edit_deco, disable_test=launch_editor_selection_disable_test))

selection_menu.br()
folder_menu.br()

# It's complicated
# folder_menu.add(_('Copy Folder From Library'), lightning_copy)

selection_menu.add(MenuItem(_("Copy"), s_copy))
selection_menu.add(MenuItem(_("Cut"), s_cut))
selection_menu.add(MenuItem(_("Remove"), del_selected))
selection_menu.add(MenuItem(_("Delete Files"), force_del_selected, show_test=test_shift, icon=delete_icon))

folder_menu.add(MenuItem(_("Copy"), s_copy))
gallery_menu.add(MenuItem(_("Copy"), s_copy))
# folder_menu.add(_('Cut'), s_cut)
# folder_menu.add(_('Paste + Transfer Folder'), lightning_paste, pass_ref=False, show_test=lightning_move_test)
# gallery_menu.add(_('Paste + Transfer Folder'), lightning_paste, pass_ref=False, show_test=lightning_move_test)
folder_menu.add(MenuItem(_("Remove"), del_selected))
gallery_menu.add(MenuItem(_("Remove"), del_selected))


def toggle_rym(mode: int = 0) -> bool:
	if mode == 1:
		return prefs.show_rym
	prefs.show_rym ^= True
	return None


def toggle_band(mode: int = 0) -> bool:
	if mode == 1:
		return prefs.show_band
	prefs.show_band ^= True
	return None


def toggle_wiki(mode: int = 0) -> bool:
	if mode == 1:
		return prefs.show_wiki
	prefs.show_wiki ^= True
	return None


# def toggle_show_discord(mode: int = 0) -> bool:
#     if mode == 1:
#         return prefs.discord_show
#     if prefs.discord_show is False and discord_allow is False:
#         show_message(_("Warning: pypresence package not installed"))
#     prefs.discord_show ^= True

def toggle_gen(mode: int = 0) -> bool:
	if mode == 1:
		return prefs.show_gen
	prefs.show_gen ^= True
	return None


def ser_band_done(result: str) -> None:
	if result:
		webbrowser.open(result, new=2, autoraise=True)
		gui.message_box = False
		gui.update += 1
	else:
		show_message(_("No matching artist result found"))


def ser_band(track_id: int) -> None:
	tr = pctl.get_track(track_id)
	if tr.artist:
		shoot_dl = threading.Thread(target=bandcamp_search, args=([tr.artist, ser_band_done]))
		shoot_dl.daemon = True
		shoot_dl.start()
		show_message(_("Searching..."))


def ser_rym(index: int) -> None:
	if len(pctl.master_library[index].artist) < 2:
		return
	line = "https://rateyourmusic.com/search?searchtype=a&searchterm=" + urllib.parse.quote(
		pctl.master_library[index].artist)
	webbrowser.open(line, new=2, autoraise=True)


def copy_to_clipboard(text: str) -> None:
	SDL_SetClipboardText(text.encode(errors="surrogateescape"))


def copy_from_clipboard():
	return SDL_GetClipboardText().decode()


def clip_aar_al(index: int):
	if pctl.master_library[index].album_artist == "":
		line = pctl.master_library[index].artist + " - " + pctl.master_library[index].album
	else:
		line = pctl.master_library[index].album_artist + " - " + pctl.master_library[index].album
	SDL_SetClipboardText(line.encode("utf-8"))


def ser_gen_thread(tr):
	s_artist = tr.artist
	s_title = tr.title

	if s_artist in prefs.lyrics_subs:
		s_artist = prefs.lyrics_subs[s_artist]
	if s_title in prefs.lyrics_subs:
		s_title = prefs.lyrics_subs[s_title]

	line = genius(s_artist, s_title, return_url=True)

	r = requests.head(line, timeout=10)

	if r.status_code != 404:
		webbrowser.open(line, new=2, autoraise=True)
		gui.message_box = False
	else:
		line = "https://genius.com/search?q=" + urllib.parse.quote(f"{s_artist} {s_title}")
		webbrowser.open(line, new=2, autoraise=True)
		gui.message_box = False


def ser_gen(track_id, get_lyrics=False):
	tr = pctl.master_library[track_id]
	if len(tr.title) < 1:
		return

	show_message(_("Searching..."))

	shoot = threading.Thread(target=ser_gen_thread, args=[tr])
	shoot.daemon = True
	shoot.start()


def ser_wiki(index: int) -> None:
	if len(pctl.master_library[index].artist) < 2:
		return
	line = "https://en.wikipedia.org/wiki/Special:Search?search=" + urllib.parse.quote(pctl.master_library[index].artist)
	webbrowser.open(line, new=2, autoraise=True)


track_menu.add(MenuItem(_("Search Artist on Wikipedia"), ser_wiki, pass_ref=True, show_test=toggle_wiki))

track_menu.add(MenuItem(_("Search Track on Genius"), ser_gen, pass_ref=True, show_test=toggle_gen))

son_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "sonemic-g.png"))
son_icon.base_asset = asset_loader(scaled_asset_directory, loaded_asset_dc, "sonemic-gs.png")

son_icon.xoff = 1
track_menu.add(MenuItem(_("Search Artist on Sonemic"), ser_rym, pass_ref=True, icon=son_icon, show_test=toggle_rym))

band_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "band.png", True))
band_icon.xoff = 0
band_icon.yoff = 1
band_icon.colour = [96, 147, 158, 255]

track_menu.add(MenuItem(_("Search Artist on Bandcamp"), ser_band, pass_ref=True, icon=band_icon, show_test=toggle_band))


def clip_ar_tr(index: int) -> None:
	line = pctl.master_library[index].artist + " - " + pctl.master_library[index].title

	SDL_SetClipboardText(line.encode("utf-8"))


# Copy metadata to clipboard
# track_menu.add(_('Copy "Artist - Album"'), clip_aar_al, pass_ref=True)
# Copy metadata to clipboard
track_menu.add(MenuItem(_('Copy "Artist - Track"'), clip_ar_tr, pass_ref=True))

def tidal_copy_album(index: int) -> None:
	t = pctl.master_library.get(index)
	if t and t.file_ext == "TIDAL":
		id = t.misc.get("tidal_album")
		if id:
			url = "https://listen.tidal.com/album/" + str(id)
			copy_to_clipboard(url)

def is_tidal_track(_) -> bool:
	return pctl.master_library[r_menu_index].file_ext == "TIDAL"


track_menu.add(MenuItem(_("Copy TIDAL Album URL"), tidal_copy_album, show_test=is_tidal_track, pass_ref=True))

# def get_track_spot_url_show_test(_):
#     if pctl.get_track(r_menu_index).misc.get("spotify-track-url"):
#         return True
#     return False


def get_track_spot_url(track_id: int) -> None:
	track_object = pctl.get_track(track_id)
	url = track_object.misc.get("spotify-track-url")
	if url:
		copy_to_clipboard(url)
		show_message(_("Url copied to clipboard"), mode="done")
	else:
		show_message(_("No results found"))

def get_track_spot_url_deco():
	if pctl.get_track(r_menu_index).misc.get("spotify-track-url"):
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled

	return [line_colour, colours.menu_background, None]

track_menu.add_sub(_("Spotify…"), 190, show_test=spotify_show_test)

def get_spot_artist_track(index: int) -> None:
	get_artist_spot(pctl.get_track(index))

track_menu.add_to_sub(1, MenuItem(_("Show Full Artist"), get_spot_artist_track, pass_ref=True, icon=spot_icon))

def get_album_spot_active(tr: TrackClass | None = None) -> None:
	if tr is None:
		tr = pctl.playing_object()
	if not tr:
		return
	url = tauon.spot_ctl.get_album_url_from_local(tr)
	if not url:
		show_message(_("No results found"))
		return
	l = tauon.spot_ctl.append_album(url, return_list=True)
	if len(l) < 2:
		show_message(_("Looks like that's the only track in the album"))
		return
	pctl.multi_playlist.append(
		pl_gen(
			title=f"{pctl.get_track(l[0]).artist} - {pctl.get_track(l[0]).album}",
			playlist_ids=l,
			hide_title=False))
	switch_playlist(len(pctl.multi_playlist) - 1)


def get_spot_album_track(index: int):
	get_album_spot_active(pctl.get_track(index))

track_menu.add_to_sub(1, MenuItem(_("Show Full Album"), get_spot_album_track, pass_ref=True, icon=spot_icon))



track_menu.add_to_sub(1, MenuItem(_("Copy Track URL"), get_track_spot_url, get_track_spot_url_deco, pass_ref=True,
	icon=spot_icon))

# def get_spot_recs(tr: TrackClass | None = None) -> None:
# 	if not tr:
# 		tr = pctl.playing_object()
# 	if not tr:
# 		return
# 	url = tauon.spot_ctl.get_artist_url_from_local(tr)
# 	if not url:
# 		show_message(_("No results found"))
# 		return
# 	track_url = tr.misc.get("spotify-track-url")
#
# 	show_message(_("Fetching..."))
# 	shooter(tauon.spot_ctl.rec_playlist, (url, track_url))
#
# def get_spot_recs_track(index: int):
# 	get_spot_recs(pctl.get_track(index))
#
# track_menu.add_to_sub(1, MenuItem(_("Get Recommended"), get_spot_recs_track, pass_ref=True, icon=spot_icon))


def drop_tracks_to_new_playlist(track_list: list[int], hidden: bool = False) -> None:
	pl = new_playlist(switch=False)
	albums = []
	artists = []
	for item in track_list:
		albums.append(pctl.get_track(default_playlist[item]).album)
		artists.append(pctl.get_track(default_playlist[item]).artist)
		pctl.multi_playlist[pl].playlist_ids.append(default_playlist[item])

	if len(track_list) > 1:
		if len(albums) > 0 and albums.count(albums[0]) == len(albums):
			track = pctl.get_track(default_playlist[track_list[0]])
			artist = track.artist
			if track.album_artist != "":
				artist = track.album_artist
			pctl.multi_playlist[pl].title = artist + " - " + albums[0][:50]

	elif len(track_list) == 1 and artists:
		pctl.multi_playlist[pl].title = artists[0]

	if tree_view_box.dragging_name:
		pctl.multi_playlist[pl].title = tree_view_box.dragging_name

	pctl.notify_change()


def queue_deco():
	if len(pctl.force_queue) > 0:
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled

	return [line_colour, colours.menu_background, None]


track_menu.br()
track_menu.add(MenuItem(_("Transcode Folder"), convert_folder, transcode_deco, pass_ref=True, icon=transcode_icon,
	show_test=toggle_transcode))


def bass_test(_) -> bool:
	# return True
	return prefs.backend == 1


def gstreamer_test(_) -> bool:
	# return True
	return prefs.backend == 2


# Create top menu
x_menu: Menu = Menu(190, show_icons=True)
view_menu = Menu(170)
set_menu = Menu(150)
set_menu_hidden = Menu(100)
vis_menu = Menu(140)
window_menu = Menu(140)
field_menu = Menu(140)
dl_menu = Menu(90)

window_menu = Menu(140)
window_menu.add(MenuItem(_("Minimize"), do_minimize_button))
window_menu.add(MenuItem(_("Maximize"), do_maximize_button))
window_menu.add(MenuItem(_("Exit"), do_exit_button))

def field_copy(text_field) -> None:
	text_field.copy()


def field_paste(text_field) -> None:
	text_field.paste()


def field_clear(text_field) -> None:
	text_field.clear()


# Copy text
field_menu.add(MenuItem(_("Copy"), field_copy, pass_ref=True))
# Paste text
field_menu.add(MenuItem(_("Paste"), field_paste, pass_ref=True))
# Clear text
field_menu.add(MenuItem(_("Clear"), field_clear, pass_ref=True))


def vis_off() -> None:
	gui.vis_want = 0
	gui.update_layout()
	# gui.turbo = False


vis_menu.add(MenuItem(_("Off"), vis_off))


def level_on() -> None:
	if gui.vis_want == 1 and gui.turbo is True:
		gui.level_meter_colour_mode += 1
		if gui.level_meter_colour_mode > 4:
			gui.level_meter_colour_mode = 0

	gui.vis_want = 1
	gui.update_layout()
	# if prefs.backend == 2:
	#     show_message("Visualisers not implemented in GStreamer mode")
	# gui.turbo = True


vis_menu.add(MenuItem(_("Level Meter"), level_on))


def spec_on() -> None:
	gui.vis_want = 2
	# if prefs.backend == 2:
	#     show_message("Not implemented")
	gui.update_layout()


vis_menu.add(MenuItem(_("Spectrum Visualizer"), spec_on))


def spec2_def() -> None:
	if gui.vis_want == 3:
		prefs.spec2_colour_mode += 1
		if prefs.spec2_colour_mode > 1:
			prefs.spec2_colour_mode = 0

	gui.vis_want = 3
	if prefs.backend == 2:
		show_message(_("Not implemented"))
	# gui.turbo = True
	prefs.spec2_colour_setting = "custom"
	gui.update_layout()


# vis_menu.add(_("Spectrogram"), spec2_def)

def sa_remove(h: int) -> None:
	if len(gui.pl_st) > 1:
		del gui.pl_st[h]
		gui.update_layout()
	else:
		show_message(_("Cannot remove the only column."))


def sa_artist() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["Artist", 220, False])
	gui.update_layout()


def sa_album_artist() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["Album Artist", 220, False])
	gui.update_layout()


def sa_composer() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["Composer", 220, False])
	gui.update_layout()


def sa_title() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["Title", 220, False])
	gui.update_layout()


def sa_album() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["Album", 220, False])
	gui.update_layout()


def sa_comment() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["Comment", 300, False])
	gui.update_layout()


def sa_track() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["#", 25, True])
	gui.update_layout()


def sa_count() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["P", 25, True])
	gui.update_layout()


def sa_scrobbles() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["S", 25, True])
	gui.update_layout()


def sa_time() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["Time", 55, True])
	gui.update_layout()


def sa_date() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["Date", 55, True])
	gui.update_layout()


def sa_genre() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["Genre", 150, False])
	gui.update_layout()


def sa_file() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["Filepath", 350, False])
	gui.update_layout()


def sa_filename() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["Filename", 300, False])
	gui.update_layout()


def sa_codec() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["Codec", 65, True])
	gui.update_layout()


def sa_bitrate() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["Bitrate", 65, True])
	gui.update_layout()


def sa_lyrics() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["Lyrics", 50, True])
	gui.update_layout()

def sa_cue() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["CUE", 50, True])
	gui.update_layout()

def sa_star() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["Starline", 80, True])
	gui.update_layout()

def sa_disc() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["Disc", 50, True])
	gui.update_layout()

def sa_rating() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["Rating", 80, True])
	gui.update_layout()


def sa_love() -> None:
	gui.pl_st.insert(set_menu.reference + 1, ["❤", 25, True])
	# gui.pl_st.append(["❤", 25, True])
	gui.update_layout()


def key_love(index: int) -> bool:
	return get_love_index(index)


def key_artist(index: int) -> str:
	return pctl.master_library[index].artist.lower()


def key_album_artist(index: int) -> str:
	return pctl.master_library[index].album_artist.lower()


def key_composer(index: int) -> str:
	return pctl.master_library[index].composer.lower()


def key_comment(index: int) -> str:
	return pctl.master_library[index].comment


def key_title(index: int) -> str:
	return pctl.master_library[index].title.lower()


def key_album(index: int) -> str:
	return pctl.master_library[index].album.lower()


def key_duration(index: int) -> int:
	return pctl.master_library[index].length


def key_date(index: int) -> str:
	return pctl.master_library[index].date


def key_genre(index: int) -> str:
	return pctl.master_library[index].genre.lower()


def key_t(index: int):
	# return str(pctl.master_library[index].track_number)
	return index_key(index)


def key_codec(index: int) -> str:
	return pctl.master_library[index].file_ext


def key_bitrate(index: int) -> int:
	return pctl.master_library[index].bitrate

def key_hl(index: int) -> int:
	if len(pctl.master_library[index].lyrics) > 5:
		return 0
	return 1


def sort_ass(h, invert=False, custom_list=None, custom_name=""):
	global default_playlist

	if custom_list is None:
		if pl_is_locked(pctl.active_playlist_viewing):
			show_message(_("Playlist is locked"))
			return

		name = gui.pl_st[h][0]
		playlist = pctl.multi_playlist[pctl.active_playlist_viewing].playlist_ids
	else:
		name = custom_name
		playlist = custom_list

	key = None
	ns = False

	if name == "Filepath":
		key = key_filepath
		if use_natsort:
			key = key_fullpath
			ns = True
	if name == "Filename":
		key = key_filepath  # key_filename
		if use_natsort:
			key = key_fullpath
			ns = True
	if name == "Artist":
		key = key_artist
	if name == "Album Artist":
		key = key_album_artist
	if name == "Title":
		key = key_title
	if name == "Album":
		key = key_album
	if name == "Composer":
		key = key_composer
	if name == "Time":
		key = key_duration
	if name == "Date":
		key = key_date
	if name == "Genre":
		key = key_genre
	if name == "#":
		key = key_t
	if name == "S":
		key = key_scrobbles
	if name == "P":
		key = key_playcount
	if name == "Starline":
		key = best
	if name == "Rating":
		key = key_rating
	if name == "Comment":
		key = key_comment
	if name == "Codec":
		key = key_codec
	if name == "Bitrate":
		key = key_bitrate
	if name == "Lyrics":
		key = key_hl
	if name == "❤":
		key = key_love
	if name == "Disc":
		key = key_disc
	if name == "CUE":
		key = key_cue

	if custom_list is None:
		if key is not None:

			if ns:
				key = natsort.natsort_keygen(key=key, alg=natsort.PATH)

			playlist.sort(key=key, reverse=invert)

			pctl.multi_playlist[pctl.active_playlist_viewing].playlist_ids = playlist
			default_playlist = pctl.multi_playlist[pctl.active_playlist_viewing].playlist_ids

			pctl.playlist_view_position = 0
			logging.debug("Position changed by sort")
			gui.pl_update = 1

	elif custom_list is not None:
		playlist.sort(key=key, reverse=invert)

	reload()


def sort_dec(h):
	sort_ass(h, True)


def hide_set_bar():
	gui.set_bar = False
	gui.update_layout()
	gui.pl_update = 1


def show_set_bar():
	gui.set_bar = True
	gui.update_layout()
	gui.pl_update = 1


# Mark for translation
_("Time")
_("Filepath")

#
# set_menu.add(_("Sort Ascending"), sort_ass, pass_ref=True, disable_test=view_pl_is_locked, pass_ref_deco=True)
# set_menu.add(_("Sort Decending"), sort_dec, pass_ref=True, disable_test=view_pl_is_locked, pass_ref_deco=True)
# set_menu.br()
set_menu.add(MenuItem(_("Auto Resize"), auto_size_columns))
set_menu.add(MenuItem(_("Hide bar"), hide_set_bar))
set_menu_hidden.add(MenuItem(_("Show bar"), show_set_bar))
set_menu.br()
set_menu.add(MenuItem("- " + _("Remove This"), sa_remove, pass_ref=True))
set_menu.br()
set_menu.add(MenuItem("+ " + _("Artist"), sa_artist))
set_menu.add(MenuItem("+ " + _("Title"), sa_title))
set_menu.add(MenuItem("+ " + _("Album"), sa_album))
set_menu.add(MenuItem("+ " + _("Duration"), sa_time))
set_menu.add(MenuItem("+ " + _("Date"), sa_date))
set_menu.add(MenuItem("+ " + _("Genre"), sa_genre))
set_menu.add(MenuItem("+ " + _("Track Number"), sa_track))
set_menu.add(MenuItem("+ " + _("Play Count"), sa_count))
set_menu.add(MenuItem("+ " + _("Codec"), sa_codec))
set_menu.add(MenuItem("+ " + _("Bitrate"), sa_bitrate))
set_menu.add(MenuItem("+ " + _("Filename"), sa_filename))
set_menu.add(MenuItem("+ " + _("Starline"), sa_star))
set_menu.add(MenuItem("+ " + _("Rating"), sa_rating))
set_menu.add(MenuItem("+ " + _("Loved"), sa_love))

set_menu.add_sub("+ " + _("More…"), 150)

set_menu.add_to_sub(0, MenuItem("+ " + _("Album Artist"), sa_album_artist))
set_menu.add_to_sub(0, MenuItem("+ " + _("Comment"), sa_comment))
set_menu.add_to_sub(0, MenuItem("+ " + _("Filepath"), sa_file))
set_menu.add_to_sub(0, MenuItem("+ " + _("Scrobble Count"), sa_scrobbles))
set_menu.add_to_sub(0, MenuItem("+ " + _("Composer"), sa_composer))
set_menu.add_to_sub(0, MenuItem("+ " + _("Disc Number"), sa_disc))
set_menu.add_to_sub(0, MenuItem("+ " + _("Has Lyrics"), sa_lyrics))
set_menu.add_to_sub(0, MenuItem("+ " + _("Is CUE Sheet"), sa_cue))

def bass_features_deco():
	line_colour = colours.menu_text
	if prefs.backend != 1:
		line_colour = colours.menu_text_disabled
	return [line_colour, colours.menu_background, None]


def toggle_dim_albums(mode: int = 0) -> bool:
	if mode == 1:
		return prefs.dim_art

	prefs.dim_art ^= True
	gui.pl_update = 1
	gui.update += 1


def toggle_gallery_combine(mode: int = 0) -> bool:
	if mode == 1:
		return prefs.gallery_combine_disc

	prefs.gallery_combine_disc ^= True
	reload_albums()
def toggle_gallery_click(mode: int = 0) -> bool:
	if mode == 1:
		return prefs.gallery_single_click

	prefs.gallery_single_click ^= True


def toggle_gallery_thin(mode: int = 0) -> bool:
	if mode == 1:
		return prefs.thin_gallery_borders

	prefs.thin_gallery_borders ^= True
	gui.update += 1
	update_layout_do()


def toggle_gallery_row_space(mode: int = 0) -> bool:
	if mode == 1:
		return prefs.increase_gallery_row_spacing

	prefs.increase_gallery_row_spacing ^= True
	gui.update += 1
	update_layout_do()


def toggle_galler_text(mode: int = 0) -> bool:
	if mode == 1:
		return gui.gallery_show_text

	gui.gallery_show_text ^= True
	gui.update += 1
	update_layout_do()

	# Jump to playing album
	if album_mode and gui.first_in_grid is not None:

		if gui.first_in_grid < len(default_playlist):
			goto_album(gui.first_in_grid, force=True)


def toggle_card_style(mode: int = 0) -> bool:
	if mode == 1:
		return prefs.use_card_style

	prefs.use_card_style ^= True
	gui.update += 1


def toggle_side_panel(mode: int = 0) -> bool:
	global update_layout
	global album_mode

	if mode == 1:
		return prefs.prefer_side

	prefs.prefer_side ^= True
	update_layout = True

	if album_mode or prefs.prefer_side is True:
		gui.rsp = True
	else:
		gui.rsp = False

	if prefs.prefer_side:
		gui.rspw = gui.pref_rspw


def force_album_view():
	toggle_album_mode(True)


def enter_combo():
	if not gui.combo_mode:
		gui.combo_was_album = album_mode
		gui.showcase_mode = False
		gui.radio_view = False
		if album_mode:
			toggle_album_mode()
		if gui.rsp:
			gui.rsp = False
		gui.combo_mode = True
		gui.update_layout()


def exit_combo(restore=False):
	if gui.combo_mode:
		if gui.combo_was_album and restore:
			force_album_view()
		gui.showcase_mode = False
		gui.radio_view = False
		if prefs.prefer_side:
			gui.rsp = True
		gui.update_layout()
		gui.combo_mode = False
		gui.was_radio = False


def enter_showcase_view(track_id=None):
	if not gui.combo_mode:
		enter_combo()
		gui.was_radio = False
	gui.showcase_mode = True
	gui.radio_view = False
	if track_id is None or pctl.playing_object() is None or pctl.playing_object().index == track_id:
		pass
	else:
		gui.force_showcase_index = track_id
	inp.mouse_click = False
	gui.update_layout()


def enter_radio_view():
	if not gui.combo_mode:
		enter_combo()
	gui.showcase_mode = False
	gui.radio_view = True
	inp.mouse_click = False
	gui.update_layout()


def standard_size():
	global album_mode
	global window_size
	global update_layout

	global album_mode_art_size

	album_mode = False
	gui.rsp = True
	window_size = window_default_size
	SDL_SetWindowSize(t_window, logical_size[0], logical_size[1])

	gui.rspw = 80 + int(window_size[0] * 0.18)
	update_layout = True
	album_mode_art_size = 130
	# clear_img_cache()


def path_stem_to_playlist(path: str, title: str) -> None:
	"""Used with gallery power bar"""
	playlist = []

	# Hack for networked tracks
	if path.lstrip("/") == title:
		for item in pctl.multi_playlist[pctl.active_playlist_viewing].playlist_ids:
			if title == os.path.basename(pctl.master_library[item].parent_folder_path):
				playlist.append(item)

	else:
		for item in pctl.multi_playlist[pctl.active_playlist_viewing].playlist_ids:
			if path in pctl.master_library[item].parent_folder_path:
				playlist.append(item)

	pctl.multi_playlist.append(pl_gen(
		title=os.path.basename(title).upper(),
		playlist_ids=copy.deepcopy(playlist),
		hide_title=False))

	pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[pctl.active_playlist_viewing].title + "\" f\"" + path + "\""

	switch_playlist(len(pctl.multi_playlist) - 1)


def goto_album(playlist_no: int, down: bool = False, force: bool = False) -> list | int | None:
	logging.debug("Postion set by album locate")

	if core_timer.get() < 0.5:
		return None

	global album_dex

	# ----
	w = gui.rspw
	if window_size[0] < 750 * gui.scale:
		w = window_size[0] - 20 * gui.scale
		if gui.lsp:
			w -= gui.lspw
	area_x = w + 38 * gui.scale
	row_len = int((area_x - album_h_gap) / (album_mode_art_size + album_h_gap))
	global last_row
	last_row = row_len
	# ----

	px = 0
	row = 0
	re = 0

	for i in range(len(album_dex)):
		if i == len(album_dex) - 1:
			re = i
			break
		if album_dex[i + 1] - 1 > playlist_no - 1:
			re = i
			break
		row += 1
		if row > row_len - 1:
			row = 0
			px += album_mode_art_size + album_v_gap

	# If the album is within the view port already, dont jump to it
	# (unless we really want to with force)
	if not force and gui.album_scroll_px + album_v_slide_value < px < gui.album_scroll_px + window_size[1]:

		# Dont chance the view since its alread in the view port
		# But if the album is just out of view on the bottom, bring it into view on to bottom row
		if window_size[1] > (album_mode_art_size + album_v_gap) * 2:
			while not gui.album_scroll_px - 20 < px + (album_mode_art_size + album_v_gap + 3) < gui.album_scroll_px + \
				window_size[1] - 40:
				gui.album_scroll_px += 1

	else:
		# Set the view to the calculated position
		gui.album_scroll_px = px
		gui.album_scroll_px -= album_v_slide_value

		gui.album_scroll_px = max(gui.album_scroll_px, 0 - album_v_slide_value)

	if len(album_dex) > 0:
		return album_dex[re]
	return 0

	gui.update += 1


def toggle_album_mode(force_on=False):
	global album_mode
	global window_size
	global update_layout
	global album_playlist_width
	global old_album_pos

	gui.gall_tab_enter = False

	if album_mode is True:

		album_mode = False
		# album_playlist_width = gui.playlist_width
		# old_album_pos = gui.album_scroll_px
		gui.rspw = gui.pref_rspw
		gui.rsp = prefs.prefer_side
		gui.album_tab_mode = False
	else:
		album_mode = True
		if gui.combo_mode:
			exit_combo()

		gui.rsp = True

		gui.rspw = gui.pref_gallery_w

	space = window_size[0] - gui.rspw
	if gui.lsp:
		space -= gui.lspw

	if album_mode and gui.set_mode and len(gui.pl_st) > 6 and space < 600 * gui.scale:
		gui.set_mode = False
		gui.pl_update = True
		gui.update_layout()

	reload_albums(quiet=True)

	# if pctl.active_playlist_playing == pctl.active_playlist_viewing:
	# goto_album(pctl.playlist_playing_position)

	if album_mode:
		if pctl.selected_in_playlist < len(pctl.playing_playlist()):
			goto_album(pctl.selected_in_playlist)


def toggle_gallery_keycontrol(always_exit=False):
	if is_level_zero():
		if not album_mode:
			toggle_album_mode()
			gui.gall_tab_enter = True
			gui.album_tab_mode = True
			show_in_gal(pctl.selected_in_playlist, silent=True)
		elif gui.gall_tab_enter or always_exit:
			# Exit gallery and tab mode
			toggle_album_mode()
		else:
			gui.album_tab_mode ^= True
			if gui.album_tab_mode:
				show_in_gal(pctl.selected_in_playlist, silent=True)


def check_auto_update_okay(code, pl=None):
	try:
		cmds = shlex.split(code)
	except Exception:
		logging.exception("Malformed generator code!")
		return False
	return "auto" in cmds or (
		prefs.always_auto_update_playlists and
		pctl.active_playlist_playing != pl and
		"sf"     not in cmds and
		"rf"     not in cmds and
		"ra"     not in cmds and
		"sa"     not in cmds and
		"st"     not in cmds and
		"rt"     not in cmds and
		"plex"   not in cmds and
		"jelly"  not in cmds and
		"koel"   not in cmds and
		"tau"    not in cmds and
		"air"    not in cmds and
		"sal"    not in cmds and
		"slt"    not in cmds and
		"spl\""  not in code and
		"tpl\""  not in code and
		"tar\""  not in code and
		"tmix\"" not in code and
		"r"      not in cmds)


def switch_playlist(number, cycle=False, quiet=False):
	global default_playlist

	global search_index
	global shift_selection

	# Close any active menus
	# for instance in Menu.instances:
	#     instance.active = False
	close_all_menus()
	if gui.radio_view:
		if cycle:
			pctl.radio_playlist_viewing += number
		else:
			pctl.radio_playlist_viewing = number
		if pctl.radio_playlist_viewing > len(pctl.radio_playlists) - 1:
			pctl.radio_playlist_viewing = 0
		return

	gui.previous_playlist_id = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int

	gui.pl_update = 1
	search_index = 0
	gui.column_d_click_on = -1
	gui.search_error = False
	if quick_search_mode:
		gui.force_search = True

	# if pl_follow:
	#     pctl.multi_playlist[pctl.playlist_active][1] = copy.deepcopy(pctl.playlist_playing)

	if gui.showcase_mode and gui.combo_mode and not quiet:
		view_standard()

	pctl.multi_playlist[pctl.active_playlist_viewing].playlist_ids = default_playlist
	pctl.multi_playlist[pctl.active_playlist_viewing].position = pctl.playlist_view_position
	pctl.multi_playlist[pctl.active_playlist_viewing].selected = pctl.selected_in_playlist

	if gall_pl_switch_timer.get() > 240:
		gui.gallery_positions.clear()
	gall_pl_switch_timer.set()

	gui.gallery_positions[gui.previous_playlist_id] = gui.album_scroll_px

	if cycle:
		pctl.active_playlist_viewing += number
	else:
		pctl.active_playlist_viewing = number

	while pctl.active_playlist_viewing > len(pctl.multi_playlist) - 1:
		pctl.active_playlist_viewing -= len(pctl.multi_playlist)
	while pctl.active_playlist_viewing < 0:
		pctl.active_playlist_viewing += len(pctl.multi_playlist)

	default_playlist = pctl.multi_playlist[pctl.active_playlist_viewing].playlist_ids
	pctl.playlist_view_position = pctl.multi_playlist[pctl.active_playlist_viewing].position
	pctl.selected_in_playlist = pctl.multi_playlist[pctl.active_playlist_viewing].selected
	logging.debug("Position changed by playlist change")
	shift_selection = [pctl.selected_in_playlist]

	id = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int

	code = pctl.gen_codes.get(id)
	if code is not None and check_auto_update_okay(code, pctl.active_playlist_viewing):
		gui.regen_single_id = id
		tauon.thread_manager.ready("worker")

	if album_mode:
		reload_albums(True)
		if id in gui.gallery_positions:
			gui.album_scroll_px = gui.gallery_positions[id]
		else:
			goto_album(pctl.playlist_view_position)

	if prefs.auto_goto_playing:
		pctl.show_current(this_only=True, playing=False, highlight=True, no_switch=True)

	if prefs.shuffle_lock:
		view_box.lyrics(hit=True)
		if pctl.active_playlist_viewing:
			pctl.active_playlist_playing = pctl.active_playlist_viewing
			random_track()


def cycle_playlist_pinned(step):
	if gui.radio_view:

		pctl.radio_playlist_viewing += step * -1
		if pctl.radio_playlist_viewing > len(pctl.radio_playlists) - 1:
			pctl.radio_playlist_viewing = 0
		if pctl.radio_playlist_viewing < 0:
			pctl.radio_playlist_viewing = len(pctl.radio_playlists) - 1
		return

	if step > 0:
		p = pctl.active_playlist_viewing
		le = len(pctl.multi_playlist)
		on = p
		on -= 1
		while True:
			if on < 0:
				on = le - 1
			if on == p:
				break
			if pctl.multi_playlist[on].hidden is False or not prefs.tabs_on_top or (
					gui.lsp and prefs.left_panel_mode == "playlist"):
				switch_playlist(on)
				break
			on -= 1

	elif step < 0:
		p = pctl.active_playlist_viewing
		le = len(pctl.multi_playlist)
		on = p
		on += 1
		while True:
			if on == le:
				on = 0
			if on == p:
				break
			if pctl.multi_playlist[on].hidden is False or not prefs.tabs_on_top or (
					gui.lsp and prefs.left_panel_mode == "playlist"):
				switch_playlist(on)
				break
			on += 1


def activate_info_box():
	fader.rise()
	pref_box.enabled = True


def activate_radio_box():
	radiobox.active = True
	radiobox.radio_field.clear()
	radiobox.radio_field_title.clear()


def new_playlist_colour_callback():
	if gui.radio_view:
		return [120, 90, 245, 255]
	return [237, 80, 221, 255]


add_icon.xoff = 3
add_icon.yoff = 0
add_icon.colour = [237, 80, 221, 255]
add_icon.colour_callback = new_playlist_colour_callback


def new_playlist_deco():
	if gui.radio_view:
		text = _("New Radio List")
	else:
		text = _("New Playlist")
	return [colours.menu_text, colours.menu_background, text]


x_menu.add(MenuItem(_("New Playlist"), new_playlist, new_playlist_deco, icon=add_icon))


def clean_db_show_test(_):
	return gui.suggest_clean_db


def clean_db_fast():
	keys = set(pctl.master_library.keys())
	for pl in pctl.multi_playlist:
		keys -= set(pl.playlist_ids)
	for item in keys:
		pctl.purge_track(item, fast=True)
	gui.show_message(_("Done! {N} old items were removed.").format(N=len(keys)), mode="done")
	gui.suggest_clean_db = False


def clean_db_deco():
	return [colours.menu_text, [30, 150, 120, 255], _("Clean Database!")]


x_menu.add(MenuItem(_("Clean Database!"), clean_db_fast, clean_db_deco, show_test=clean_db_show_test))

# x_menu.add(_("Internet Radio…"), activate_radio_box)

tauon.switch_playlist = switch_playlist


def import_spotify_playlist() -> None:
	clip = copy_from_clipboard()
	for line in clip.split("\n"):
		if line.startswith(("https://open.spotify.com/playlist/", "spotify:playlist:")):
			clip = clip.strip()
			tauon.spot_ctl.playlist(line)

	if album_mode:
		reload_albums()
	gui.pl_update += 1


def import_spotify_playlist_deco():
	clip = copy_from_clipboard()
	if clip.startswith(("https://open.spotify.com/playlist/", "spotify:playlist:")):
		return [colours.menu_text, colours.menu_background, None]
	return [colours.menu_text_disabled, colours.menu_background, None]


x_menu.add(MenuItem(_("Paste Spotify Playlist"), import_spotify_playlist, import_spotify_playlist_deco, icon=spot_icon,
	show_test=spotify_show_test))


def show_import_music(_):
	return gui.add_music_folder_ready


def import_music():
	pl = pl_gen(_("Music"))
	pl.last_folder = [str(music_directory)]
	pctl.multi_playlist.append(pl)
	load_order = LoadClass()
	load_order.target = str(music_directory)
	load_order.playlist = pl.uuid_int
	load_orders.append(load_order)
	switch_playlist(len(pctl.multi_playlist) - 1)
	gui.add_music_folder_ready = False


x_menu.add(MenuItem(_("Import Music Folder"), import_music, show_test=show_import_music))

x_menu.br()

settings_icon.xoff = 0
settings_icon.yoff = 2
settings_icon.colour = [232, 200, 96, 255]  # [230, 152, 118, 255]#[173, 255, 47, 255] #[198, 237, 56, 255]
# settings_icon.colour = [180, 140, 255, 255]
x_menu.add(MenuItem(_("Settings"), activate_info_box, icon=settings_icon))
x_menu.add_sub(_("Database…"), 190)
if dev_mode:
	def dev_mode_enable_save_state() -> None:
		global should_save_state
		should_save_state = True
		show_message(_("Enabled saving state"))

	def dev_mode_disable_save_state() -> None:
		global should_save_state
		should_save_state = False
		show_message(_("Disabled saving state"))

	x_menu.add_sub(_("Dev Mode"), 190)
	x_menu.add_to_sub(1, MenuItem(_("Enable Saving State"), dev_mode_enable_save_state))
	x_menu.add_to_sub(1, MenuItem(_("Disable Saving State"), dev_mode_disable_save_state))
x_menu.br()


# x_menu.add('Toggle Side panel', toggle_combo_view, combo_deco)

def stt2(sec):
	days, rem = divmod(sec, 86400)
	hours, rem = divmod(rem, 3600)
	min, sec = divmod(rem, 60)

	s_day = str(days) + "d"
	if s_day == "0d":
		s_day = "  "

	s_hours = str(hours) + "h"
	if s_hours == "0h" and s_day == "  ":
		s_hours = "  "

	s_min = str(min) + "m"

	return s_day.rjust(3) + " " + s_hours.rjust(3) + " " + s_min.rjust(3)


def export_database():
	path = str(user_directory / "DatabaseExport.csv")
	xport = open(path, "w")

	xport.write("Artist;Title;Album;Album artist;Track number;Type;Duration;Release date;Genre;Playtime;File path")

	for index, track in pctl.master_library.items():

		xport.write("\n")

		xport.write(csv_string(track.artist) + ",")
		xport.write(csv_string(track.title) + ",")
		xport.write(csv_string(track.album) + ",")
		xport.write(csv_string(track.album_artist) + ",")
		xport.write(csv_string(track.track_number) + ",")
		type = "File"
		if track.is_network:
			type = "Network"
		elif track.is_cue:
			type = "CUE File"
		xport.write(type + ",")
		xport.write(str(track.length) + ",")
		xport.write(csv_string(track.date) + ",")
		xport.write(csv_string(track.genre) + ",")
		xport.write(str(int(star_store.get_by_object(track))) + ",")
		xport.write(csv_string(track.fullpath))

	xport.close()
	show_message(_("Export complete."), _("Saved as: ") + path, mode="done")


def q_to_playlist():
	pctl.multi_playlist.append(pl_gen(
		title=_("Play History"),
		playing=0,
		playlist_ids=list(reversed(copy.deepcopy(pctl.track_queue))),
		position=0,
		hide_title=True,
		selected=0))


x_menu.add_to_sub(0, MenuItem(_("Export as CSV"), export_database))
x_menu.add_to_sub(0, MenuItem(_("Rescan All Folders"), rescan_all_folders))
x_menu.add_to_sub(0, MenuItem(_("Play History to Playlist"), q_to_playlist))
x_menu.add_to_sub(0, MenuItem(_("Reset Image Cache"), clear_img_cache))

cm_clean_db = False


def clean_db() -> None:
	global cm_clean_db
	prefs.remove_network_tracks = False
	cm_clean_db = True
	tauon.thread_manager.ready("worker")


def clean_db2() -> None:
	global cm_clean_db
	prefs.remove_network_tracks = True
	cm_clean_db = True
	tauon.thread_manager.ready("worker")


x_menu.add_to_sub(0, MenuItem(_("Remove Network Tracks"), clean_db2))
x_menu.add_to_sub(0, MenuItem(_("Remove Missing Tracks"), clean_db))



def import_fmps() -> None:
	unique = set()
	for playlist in pctl.multi_playlist:
		for id in playlist.playlist_ids:
			tr = pctl.get_track(id)
			if "FMPS_Rating" in tr.misc:
				rating = round(tr.misc["FMPS_Rating"] * 10)
				star_store.set_rating(tr.index, rating)
				unique.add(tr.index)

	show_message(_("{N} ratings imported").format(N=str(len(unique))), mode="done")

	gui.pl_update += 1

x_menu.add_to_sub(0, MenuItem(_("Import FMPS Ratings"), import_fmps))


def import_popm():
	unique = set()
	skipped = set()
	for playlist in pctl.multi_playlist:
		for id in playlist.playlist_ids:
			tr = pctl.get_track(id)
			if "POPM" in tr.misc:
				rating = tr.misc["POPM"]
				t_rating = 0
				if rating <= 1:
					t_rating = 2
				elif rating <= 64:
					t_rating = 4
				elif rating <= 128:
					t_rating = 6
				elif rating <= 196:
					t_rating = 8
				elif rating <= 255:
					t_rating = 10

				if star_store.get_rating(tr.index) == 0:
					star_store.set_rating(tr.index, t_rating)
					unique.add(tr.index)
				else:
					logging.info("Won't import POPM because track is already rated")
					skipped.add(tr.index)

	s = str(len(unique)) + " ratings imported"
	if len(skipped) > 0:
		s += f", {len(skipped)} skipped"
	show_message(s, mode="done")

	gui.pl_update += 1

x_menu.add_to_sub(0, MenuItem(_("Import POPM Ratings"), import_popm))


def clear_ratings() -> None:
	if not key_shift_down:
		show_message(
			_("This will delete all track and album ratings from the local database!"),
			_("Press button again while holding shift key if you're sure you want to do that."),
			mode="warning")
		return
	for key, star in star_store.db.items():
		star[2] = 0
	album_star_store.db.clear()
	gui.pl_update += 1


x_menu.add_to_sub(0, MenuItem(_("Reset User Ratings"), clear_ratings))


def find_incomplete() -> None:
	gen_incomplete(pctl.active_playlist_viewing)


x_menu.add_to_sub(0, MenuItem(_("Find Incomplete Albums"), find_incomplete))
x_menu.add_to_sub(0, MenuItem(_("Mark Missing as Found"), pctl.reset_missing_flags, show_test=test_shift))


def cast_deco():
	line_colour = colours.menu_text
	if tauon.chrome_mode:
		return [line_colour, colours.menu_background, _("Stop Cast")]  # [24, 25, 60, 255]
	return [line_colour, colours.menu_background, None]


def cast_search2() -> None:
	chrome.rescan()

def cast_search() -> None:

	if tauon.chrome_mode:
		pctl.stop()
		chrome.end()
	else:
		if not chrome:
			show_message(_("pychromecast not found"))
			return
		show_message(_("Searching for Chomecasts..."))
		shooter(cast_search2)


if chrome:
	x_menu.add_sub(_("Chromecast…"), 220)
	shooter(cast_search2)

tauon.chrome_menu = x_menu

#x_menu.add(_("Cast…"), cast_search, cast_deco)


def clear_queue() -> None:
	pctl.force_queue = []
	gui.pl_update = 1
	pctl.pause_queue = False


mode_menu = Menu(175)


def set_mini_mode_A1() -> None:
	prefs.mini_mode_mode = 0
	set_mini_mode()


def set_mini_mode_B1() -> None:
	prefs.mini_mode_mode = 1
	set_mini_mode()


def set_mini_mode_A2() -> None:
	prefs.mini_mode_mode = 2
	set_mini_mode()


def set_mini_mode_C1() -> None:
	prefs.mini_mode_mode = 5
	set_mini_mode()

def set_mini_mode_B2() -> None:
	prefs.mini_mode_mode = 3
	set_mini_mode()


def set_mini_mode_D() -> None:
	prefs.mini_mode_mode = 4
	set_mini_mode()


mode_menu.add(MenuItem(_("Tab"), set_mini_mode_D))
mode_menu.add(MenuItem(_("Mini"), set_mini_mode_A1))
# mode_menu.add(_('Mini Mode Large'), set_mini_mode_A2)
mode_menu.add(MenuItem(_("Slate"), set_mini_mode_C1))
mode_menu.add(MenuItem(_("Square"), set_mini_mode_B1))
mode_menu.add(MenuItem(_("Square Large"), set_mini_mode_B2))


def copy_bb_metadata() -> str | None:
	tr = pctl.playing_object()
	if tr is None:
		return None
	if not tr.title and not tr.artist and pctl.playing_state == 3:
		return pctl.tag_meta
	text = f"{tr.artist} - {tr.title}".strip(" -")
	if text:
		copy_to_clipboard(text)
	else:
		show_message(_("No metadata available to copy"))
	return None


mode_menu.br()
mode_menu.add(MenuItem(_("Copy Title to Clipboard"), copy_bb_metadata))

extra_menu = Menu(175, show_icons=True)


def stop() -> None:
	pctl.stop()


def random_track() -> None:
	playlist = pctl.multi_playlist[pctl.active_playlist_playing].playlist_ids
	if playlist:
		random_position = random.randrange(0, len(playlist))
		track_id = playlist[random_position]
		pctl.jump(track_id, random_position)
		pctl.show_current()


extra_menu.add(MenuItem(_("Random Track"), random_track, hint=";"))


def random_album() -> None:
	folders = {}
	playlist = pctl.multi_playlist[pctl.active_playlist_playing].playlist_ids
	if playlist:
		for i, id in enumerate(playlist):
			track = pctl.get_track(id)
			if track.parent_folder_path not in folders:
				folders[track.parent_folder_path] = (id, i)

		key = random.choice(list(folders.keys()))
		result = folders[key]
		pctl.jump(*result)
		pctl.show_current()


def radio_random() -> None:
	pctl.advance(rr=True)


radiorandom_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "radiorandom.png", True))
revert_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "revert.png", True))

radiorandom_icon.xoff = 1
radiorandom_icon.yoff = 0
radiorandom_icon.colour = [153, 229, 133, 255]
extra_menu.add(MenuItem(_("Radio Random"), radio_random, hint="/", icon=radiorandom_icon))

revert_icon.xoff = 1
revert_icon.yoff = 0
revert_icon.colour = [229, 102, 59, 255]
extra_menu.add(MenuItem(_("Revert"), pctl.revert, hint="Shift+/", icon=revert_icon))

# extra_menu.add('Toggle Repeat', toggle_repeat, hint='COMMA')


# extra_menu.add('Toggle Random', toggle_random, hint='PERIOD')
extra_menu.add(MenuItem(_("Clear Queue"), clear_queue, queue_deco, hint="Alt+Shift+Q"))


def heart_menu_colour() -> list[int] | None:
	if not (pctl.playing_state == 1 or pctl.playing_state == 2):
		if colours.lm:
			return [255, 150, 180, 255]
		return None
	if love(False):
		return [245, 60, 60, 255]
	if colours.lm:
		return [255, 150, 180, 255]
	return None


heart_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "heart-menu.png", True))
heart_row_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "heart-track.png", True)
heart_notify_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "heart-notify.png", True)
heart_notify_break_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "heart-notify-break.png", True)
# spotify_row_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "spotify-row.png", True)
star_pc_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "star-pc.png", True)
star_row_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "star.png", True)
star_half_row_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "star-half.png", True)


def draw_rating_widget(x: int, y: int, n_track: TrackClass, album: bool = False):
	if album:
		rat = album_star_store.get_rating(n_track)
	else:
		rat = star_store.get_rating(n_track.index)

	rect = (x - round(5 * gui.scale), y - round(4 * gui.scale), round(80 * gui.scale), round(16 * gui.scale))
	gui.heart_fields.append(rect)

	if coll(rect) and (inp.mouse_click or (is_level_zero() and not quick_drag)):
		gui.pl_update = 2
		pp = mouse_position[0] - x

		if pp < 5 * gui.scale:
			rat = 0
		elif pp > 70 * gui.scale:
			rat = 10
		else:
			rat = pp // (star_row_icon.w // 2)

		if inp.mouse_click:
			rat = min(rat, 10)
			if album:
				album_star_store.set_rating(n_track, rat)
			else:
				star_store.set_rating(n_track.index, rat, write=True)

	# bg = colours.grey(40)
	bg = [255, 255, 255, 17]
	fg = colours.grey(210)

	if gui.tracklist_bg_is_light:
		bg = [0, 0, 0, 25]
		fg = colours.grey(70)

	playtime_stars = 0
	if prefs.rating_playtime_stars and rat == 0 and not album:
		playtime_stars = star_count3(star_store.get(n_track.index), n_track.length)
		if gui.tracklist_bg_is_light:
			fg2 = alpha_blend([0, 0, 0, 70], ddt.text_background_colour)
		else:
			fg2 = alpha_blend([255, 255, 255, 50], ddt.text_background_colour)

	for ss in range(5):

		xx = x + ss * star_row_icon.w

		if playtime_stars:
			if playtime_stars - 1 < ss * 2:
				star_row_icon.render(xx, y, bg)
			elif playtime_stars - 1 == ss * 2:
				star_row_icon.render(xx, y, bg)
				star_half_row_icon.render(xx, y, fg2)
			else:
				star_row_icon.render(xx, y, fg2)
		else:

			if rat - 1 < ss * 2:
				star_row_icon.render(xx, y, bg)
			elif rat - 1 == ss * 2:
				star_row_icon.render(xx, y, bg)
				star_half_row_icon.render(xx, y, fg)
			else:
				star_row_icon.render(xx, y, fg)


heart_colours = ColourGenCache(0.7, 0.7)

heart_icon.colour = [245, 60, 60, 255]
heart_icon.xoff = 3
heart_icon.yoff = 0



if gui.scale == 1.25:
	heart_icon.yoff = 1

heart_icon.colour_callback = heart_menu_colour


def love_deco():
	if love(False):
		return [colours.menu_text, colours.menu_background, _("Un-Love Track")]
	if pctl.playing_state == 1 or pctl.playing_state == 2:
		return [colours.menu_text, colours.menu_background, _("Love Track")]
	return [colours.menu_text_disabled, colours.menu_background, _("Love Track")]


def bar_love(notify: bool = False) -> None:
	shoot_love = threading.Thread(target=love, args=[True, None, False, notify])
	shoot_love.daemon = True
	shoot_love.start()


def bar_love_notify() -> None:
	bar_love(notify=True)


def select_love(notify: bool = False) -> None:
	selected = pctl.selected_in_playlist
	playlist = pctl.multi_playlist[pctl.active_playlist_viewing].playlist_ids
	if -1 < selected < len(playlist):
		track_id = playlist[selected]

		shoot_love = threading.Thread(target=love, args=[True, track_id, False, notify])
		shoot_love.daemon = True
		shoot_love.start()


extra_menu.add(MenuItem("Love", bar_love_notify, love_deco, icon=heart_icon))

def toggle_spotify_like_active2(tr: TrackClass) -> None:
	if "spotify-track-url" in tr.misc:
		if "spotify-liked" in tr.misc:
			tauon.spot_ctl.unlike_track(tr)
		else:
			tauon.spot_ctl.like_track(tr)
	gui.pl_update += 1
	for i, p in enumerate(pctl.multi_playlist):
		code = pctl.gen_codes.get(p.uuid_int)
		if code and code.startswith("slt"):
			logging.info("Fetching Spotify likes...")
			regenerate_playlist(i, silent=True)
	gui.pl_update += 1

def toggle_spotify_like_active() -> None:
	tr = pctl.playing_object()
	if tr:
		shoot_dl = threading.Thread(target=toggle_spotify_like_active2, args=([tr]))
		shoot_dl.daemon = True
		shoot_dl.start()


def toggle_spotify_like_active_deco():
	tr = pctl.playing_object()
	text = _("Spotify Like Track")

	if pctl.playing_state == 0 or not tr or "spotify-track-url" not in tr.misc:
		return [colours.menu_text_disabled, colours.menu_background, text]
	if "spotify-liked" in tr.misc:
		text = _("Un-like Spotify Track")

	return [colours.menu_text, colours.menu_background, text]


def locate_artist() -> None:
	track = pctl.playing_object()
	if not track:
		return

	artist = track.artist
	if track.album_artist:
		artist = track.album_artist

	block_starts = []
	current = False
	for i in range(len(default_playlist)):
		track = pctl.get_track(default_playlist[i])
		if current is False:
			if track.artist == artist or track.album_artist == artist or (
					"artists" in track.misc and artist in track.misc["artists"]):
				block_starts.append(i)
				current = True
		elif (track.artist != artist and track.album_artist != artist) or (
				"artists" in track.misc and artist in track.misc["artists"]):
			current = False

	if block_starts:

		next = False
		for start in block_starts:

			if next:
				pctl.selected_in_playlist = start
				pctl.playlist_view_position = start
				shift_selection.clear()
				break

			if pctl.selected_in_playlist == start:
				next = True
				continue

		else:
			pctl.selected_in_playlist = block_starts[0]
			pctl.playlist_view_position = block_starts[0]
			shift_selection.clear()

		tree_view_box.show_track(pctl.get_track(default_playlist[pctl.selected_in_playlist]))
	else:
		show_message(_("No exact matching artist could be found in this playlist"))

	logging.debug("Position changed by artist locate")

	gui.pl_update += 1


def activate_search_overlay() -> None:
	if cm_clean_db:
		show_message(_("Please wait for cleaning process to finish"))
		return
	search_over.active = True
	search_over.delay_enter = False
	search_over.search_text.selection = 0
	search_over.search_text.cursor_position = 0
	search_over.spotify_mode = False


extra_menu.add(MenuItem(_("Global Search"), activate_search_overlay, hint="Ctrl+G"))


def get_album_spot_url_active() -> None:
	tr = pctl.playing_object()
	if tr:
		url = tauon.spot_ctl.get_album_url_from_local(tr)

		if url:
			copy_to_clipboard(url)
			show_message(_("URL copied to clipboard"), mode="done")
		else:
			show_message(_("No results found"))


def get_album_spot_url_actove_deco():
	tr = pctl.playing_object()
	text = _("Copy Album URL")
	if not tr:
		return [colours.menu_text_disabled, colours.menu_background, text]
	if "spotify-album-url" not in tr.misc:
		text = _("Lookup Spotify Album")

	return [colours.menu_text, colours.menu_background, text]



def goto_playing_extra() -> None:
	pctl.show_current(highlight=True)


extra_menu.add(MenuItem(_("Locate Artist"), locate_artist))

extra_menu.add(MenuItem(_("Go To Playing"), goto_playing_extra, hint="'"))

def show_spot_playing_deco():
	if not (tauon.spot_ctl.coasting or tauon.spot_ctl.playing):
		return [colours.menu_text, colours.menu_background, None]
	return [colours.menu_text_disabled, colours.menu_background, None]

def show_spot_coasting_deco():
	if tauon.spot_ctl.coasting:
		return [colours.menu_text, colours.menu_background, None]
	return [colours.menu_text_disabled, colours.menu_background, None]


def show_spot_playing() -> None:
	if pctl.playing_state != 0 and pctl.playing_state != 3 and not tauon.spot_ctl.coasting and not tauon.spot_ctl.playing:
		pctl.stop()
	tauon.spot_ctl.update(start=True)


def spot_transfer_playback_here() -> None:
	tauon.spot_ctl.preparing_spotify = True
	if not (tauon.spot_ctl.playing or tauon.spot_ctl.coasting):
		tauon.spot_ctl.update(start=True)
	pctl.playerCommand = "spotcon"
	pctl.playerCommandReady = True
	pctl.playing_state = 3
	shooter(tauon.spot_ctl.transfer_to_tauon)


extra_menu.br()
extra_menu.add(MenuItem("Spotify Like Track", toggle_spotify_like_active, toggle_spotify_like_active_deco,
	show_test=spotify_show_test, icon=spot_heartx_icon))

def spot_import_albums() -> None:
	if not tauon.spot_ctl.spotify_com:
		tauon.spot_ctl.spotify_com = True
		shoot = threading.Thread(target=tauon.spot_ctl.get_library_albums)
		shoot.daemon = True
		shoot.start()
	else:
		show_message(_("Please wait until current job is finished"))

extra_menu.add_sub(_("Import Spotify…"), 140, show_test=spotify_show_test)

extra_menu.add_to_sub(0, MenuItem(_("Liked Albums"), spot_import_albums, show_test=spotify_show_test, icon=spot_icon))

def spot_import_tracks() -> None:
	if not tauon.spot_ctl.spotify_com:
		tauon.spot_ctl.spotify_com = True
		shoot = threading.Thread(target=tauon.spot_ctl.get_library_likes)
		shoot.daemon = True
		shoot.start()
	else:
		show_message(_("Please wait until current job is finished"))

extra_menu.add_to_sub(0, MenuItem(_("Liked Tracks"), spot_import_tracks, show_test=spotify_show_test, icon=spot_icon))

def spot_import_playlists() -> None:
	if not tauon.spot_ctl.spotify_com:
		show_message(_("Importing Spotify playlists..."))
		shoot_dl = threading.Thread(target=tauon.spot_ctl.import_all_playlists)
		shoot_dl.daemon = True
		shoot_dl.start()
	else:
		show_message(_("Please wait until current job is finished"))


#extra_menu.add_to_sub(_("Import All Playlists"), 0, spot_import_playlists, show_test=spotify_show_test, icon=spot_icon)

def spot_import_playlist_menu() -> None:
	if not tauon.spot_ctl.spotify_com:
		playlists = tauon.spot_ctl.get_playlist_list()
		spotify_playlist_menu.items.clear()
		if playlists:
			for item in playlists:
				spotify_playlist_menu.add(MenuItem(item[0], tauon.spot_ctl.playlist, pass_ref=True, set_ref=item[1]))

			spotify_playlist_menu.add(MenuItem(_("> Import All Playlists"), spot_import_playlists))
			spotify_playlist_menu.activate(position=(extra_menu.pos[0], window_size[1] - gui.panelBY))
	else:
		show_message(_("Please wait until current job is finished"))

extra_menu.add_to_sub(0, MenuItem(_("Playlist…"), spot_import_playlist_menu, show_test=spotify_show_test, icon=spot_icon))


def spot_import_context() -> None:
	shooter(tauon.spot_ctl.import_context)

extra_menu.add_to_sub(0, MenuItem(_("Current Context"), spot_import_context, show_spot_coasting_deco, show_test=spotify_show_test, icon=spot_icon))


def get_album_spot_deco():
	tr = pctl.playing_object()
	text = _("Show Full Album")
	if not tr:
		return [colours.menu_text_disabled, colours.menu_background, text]
	if "spotify-album-url" not in tr.misc:
		text = _("Lookup Spotify Album")

	return [colours.menu_text, colours.menu_background, text]


extra_menu.add(MenuItem("Show Full Album", get_album_spot_active, get_album_spot_deco,
	show_test=spotify_show_test, icon=spot_icon))


def get_artist_spot(tr: TrackClass = None) -> None:
	if not tr:
		tr = pctl.playing_object()
	if not tr:
		return
	url = tauon.spot_ctl.get_artist_url_from_local(tr)
	if not url:
		show_message(_("No results found"))
		return
	show_message(_("Fetching..."))
	shooter(tauon.spot_ctl.artist_playlist, (url,))

extra_menu.add(MenuItem(_("Show Full Artist"), get_artist_spot,
	show_test=spotify_show_test, icon=spot_icon))

extra_menu.add(MenuItem(_("Start Spotify Remote"), show_spot_playing, show_spot_playing_deco, show_test=spotify_show_test,
	icon=spot_icon))

# def spot_transfer_playback_here_deco():
#     tr = pctl.playing_state == 3:
#     text = _("Show Full Album")
#     if not tr:
#         return [colours.menu_text_disabled, colours.menu_background, text]
#     if not "spotify-album-url" in tr.misc:
#         text = _("Lookup Spotify Album")
#
#     return [colours.menu_text, colours.menu_background, text]


extra_menu.add(MenuItem("Transfer audio here", spot_transfer_playback_here, show_test=lambda x:spotify_show_test(0) and tauon.enable_librespot and prefs.launch_spotify_local and not pctl.spot_playing and (tauon.spot_ctl.coasting or tauon.spot_ctl.playing),
	icon=spot_icon))

def toggle_auto_theme(mode: int = 0) -> None:
	if mode == 1:
		return prefs.colour_from_image

	prefs.colour_from_image ^= True
	gui.theme_temp_current = -1

	gui.reload_theme = True

	# if prefs.colour_from_image and prefs.art_bg and not key_shift_down:
	#     toggle_auto_bg()


def toggle_auto_bg(mode: int= 0) -> bool | None:
	if mode == 1:
		return prefs.art_bg
	prefs.art_bg ^= True

	if prefs.art_bg:
		gui.update = 60

	style_overlay.flush()
	tauon.thread_manager.ready("style")
	# if prefs.colour_from_image and prefs.art_bg and not key_shift_down:
	#     toggle_auto_theme()
	return None


def toggle_auto_bg_strong(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.art_bg_stronger == 2

	if prefs.art_bg_stronger == 2:
		prefs.art_bg_stronger = 1
	else:
		prefs.art_bg_stronger = 2
	gui.update_layout()
	return None

def toggle_auto_bg_strong1(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.art_bg_stronger == 1
	prefs.art_bg_stronger = 1
	gui.update_layout()
	return None


def toggle_auto_bg_strong2(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.art_bg_stronger == 2
	prefs.art_bg_stronger = 2
	gui.update_layout()
	if prefs.art_bg:
		gui.update = 60
	return None


def toggle_auto_bg_strong3(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.art_bg_stronger == 3
	prefs.art_bg_stronger = 3
	gui.update_layout()
	if prefs.art_bg:
		gui.update = 60
	return None


def toggle_auto_bg_blur(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.art_bg_always_blur
	prefs.art_bg_always_blur ^= True
	style_overlay.flush()
	tauon.thread_manager.ready("style")
	return None


def toggle_auto_bg_showcase(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.bg_showcase_only
	prefs.bg_showcase_only ^= True
	gui.update_layout()
	return None


def toggle_notifications(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.show_notifications

	prefs.show_notifications ^= True

	if prefs.show_notifications:
		if not de_notify_support:
			show_message(_("Notifications for this DE not supported"), "", mode="warning")
	return None


# def toggle_al_pref_album_artist(mode: int = 0) -> bool:
#
#     if mode == 1:
#         return prefs.artist_list_prefer_album_artist
#
#     prefs.artist_list_prefer_album_artist ^= True
#     artist_list_box.saves.clear()
#     return None

def toggle_mini_lyrics(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.show_lyrics_side
	prefs.show_lyrics_side ^= True
	return None


def toggle_showcase_vis(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.showcase_vis

	prefs.showcase_vis ^= True
	gui.update_layout()
	return None


def toggle_level_meter(mode: int = 0) -> bool | None:
	if mode == 1:
		return gui.vis_want != 0

	if gui.vis_want == 0:
		gui.vis_want = 1
	else:
		gui.vis_want = 0

	gui.update_layout()
	return None


# def toggle_force_subpixel(mode: int = 0) -> bool | None:
#
#     if mode == 1:
#         return prefs.force_subpixel_text != 0
#
#     prefs.force_subpixel_text ^= True
#     ddt.force_subpixel_text = prefs.force_subpixel_text
#     ddt.clear_text_cache()


def level_meter_special_2():
	gui.level_meter_colour_mode = 2


theme_files = os.listdir(str(install_directory / "theme"))
theme_files.sort()


def last_fm_menu_deco():
	if prefs.scrobble_hold:
		if not prefs.auto_lfm and lb.enable:
			line = _("ListenBrainz is Paused")
		else:
			line = _("Scrobbling is Paused")
		bg = colours.menu_background
	else:
		if not prefs.auto_lfm and lb.enable:
			line = _("ListenBrainz is Active")
		else:
			line = _("Scrobbling is Active")

		bg = colours.menu_background

	return [colours.menu_text, bg, line]


def lastfm_colour() -> list[int] | None:
	if not prefs.scrobble_hold:
		return [250, 50, 50, 255]
	return None


last_fm_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "as.png", True)
lastfm_icon = MenuIcon(last_fm_icon)

if gui.scale == 2 or gui.scale == 1.25:
	lastfm_icon.xoff = 0
else:
	lastfm_icon.xoff = -1

lastfm_icon.yoff = 1

lastfm_icon.colour = [249, 70, 70, 255]
lastfm_icon.colour_callback = lastfm_colour


def lastfm_menu_test(a) -> bool:
	if (prefs.auto_lfm and prefs.last_fm_token is not None) or prefs.enable_lb or prefs.maloja_enable:
		return True
	return False


lb_icon = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "lb-g.png"))
lb_icon.base_asset = asset_loader(scaled_asset_directory, loaded_asset_dc, "lb-gs.png")


def lb_mode() -> bool:
	return prefs.enable_lb


lb_icon.mode_callback = lb_mode

lb_icon.xoff = 3
lb_icon.yoff = -1

if gui.scale == 1.25:
	lb_icon.yoff = 0

if prefs.auto_lfm:
	listen_icon = lastfm_icon
elif lb.enable:
	listen_icon = lb_icon
else:
	listen_icon = None

x_menu.add(MenuItem("LFM", lastfm.toggle, last_fm_menu_deco, icon=listen_icon, show_test=lastfm_menu_test))



def get_album_art_url(tr: TrackClass):

	artist = tr.album_artist
	if not tr.album:
		return None
	if not artist:
		artist = tr.artist
	if not artist:
		return None

	release_id = None
	release_group_id = None
	if (artist, tr.album) in pctl.album_mbid_release_cache or (artist, tr.album) in pctl.album_mbid_release_group_cache:
		release_id = pctl.album_mbid_release_cache[(artist, tr.album)]
		release_group_id = pctl.album_mbid_release_group_cache[(artist, tr.album)]
		if release_id is None and release_group_id is None:
			return None

	if not release_group_id:
		release_group_id = tr.misc.get("musicbrainz_releasegroupid")

	if not release_id:
		release_id = tr.misc.get("musicbrainz_albumid")

	if not release_group_id:
		try:
			#logging.info("lookup release group id")
			s = musicbrainzngs.search_release_groups(tr.album, artist=artist, limit=1)
			release_group_id = s["release-group-list"][0]["id"]
			tr.misc["musicbrainz_releasegroupid"] = release_group_id
			#logging.info("got release group id")
		except Exception:
			logging.exception("Error lookup mbid for discord")
			pctl.album_mbid_release_group_cache[(artist, tr.album)] = None

	if not release_id:
		try:
			#logging.info("lookup release id")
			s = musicbrainzngs.search_releases(tr.album, artist=artist, limit=1)
			release_id = s["release-list"][0]["id"]
			tr.misc["musicbrainz_albumid"] = release_id
			#logging.info("got release group id")
		except Exception:
			logging.exception("Error lookup mbid for discord")
			pctl.album_mbid_release_cache[(artist, tr.album)] = None

	image_data = None
	final_id = None
	if release_group_id:
		url = pctl.mbid_image_url_cache.get(release_group_id)
		if url:
			return url

		base_url = "https://coverartarchive.org/release-group/"
		url = f"{base_url}{release_group_id}"

		try:
			#logging.info("lookup image url from release group")
			response = requests.get(url, timeout=10)
			response.raise_for_status()
			image_data = response.json()
			final_id = release_group_id
		except (requests.RequestException, ValueError):
			logging.exception("No image found for release group")
			pctl.album_mbid_release_group_cache[(artist, tr.album)] = None
		except Exception:
			logging.exception("Unknown error finding image for release group")

	if release_id and not image_data:
		url = pctl.mbid_image_url_cache.get(release_id)
		if url:
			return url

		base_url = "https://coverartarchive.org/release/"
		url = f"{base_url}{release_id}"

		try:
			#logging.print("lookup image url from album id")
			response = requests.get(url, timeout=10)
			response.raise_for_status()
			image_data = response.json()
			final_id = release_id
		except (requests.RequestException, ValueError):
			logging.exception("No image found for album id")
			pctl.album_mbid_release_cache[(artist, tr.album)] = None
		except Exception:
			logging.exception("Unknown error getting image found for album id")

	if image_data:
		for image in image_data["images"]:
			if image.get("front") and ("250" in image["thumbnails"] or "small" in image["thumbnails"]):
				pctl.album_mbid_release_cache[(artist, tr.album)] = release_id
				pctl.album_mbid_release_group_cache[(artist, tr.album)] = release_group_id

				url = image["thumbnails"].get("250")
				if url is None:
					url = image["thumbnails"].get("small")

				if url:
					logging.info("got mb image url for discord")
					pctl.mbid_image_url_cache[final_id] = url
					return url

	pctl.album_mbid_release_cache[(artist, tr.album)] = None
	pctl.album_mbid_release_group_cache[(artist, tr.album)] = None

	return None


def discord_loop() -> None:
	prefs.discord_active = True

	try:
		if not pctl.playing_ready():
			return
		asyncio.set_event_loop(asyncio.new_event_loop())

		# logging.info("Attempting to connect to Discord...")
		client_id = "954253873160286278"
		RPC = Presence(client_id)
		RPC.connect()

		logging.info("Discord RPC connection successful.")
		time.sleep(1)
		start_time = time.time()
		idle_time = Timer()

		state = 0
		index = -1
		br = False
		gui.discord_status = "Connected"
		gui.update += 1
		current_state = 0

		while True:
			while True:

				current_index = pctl.playing_object().index
				if pctl.playing_state == 3:
					current_index = radiobox.song_key

				if current_state == 0 and pctl.playing_state in (1, 3):
					current_state = 1
				elif current_state == 1 and pctl.playing_state not in (1, 3):
					current_state = 0
					idle_time.set()

				if state != current_state or index != current_index:
					if pctl.a_time > 4 or current_state != 1:
						state = current_state
						index = current_index
						start_time = time.time() - pctl.playing_time

						break

				if current_state == 0 and idle_time.get() > 13:
					logging.info("Pause discord RPC...")
					gui.discord_status = "Idle"
					RPC.clear(pid)
					# RPC.close()

					while True:
						if prefs.disconnect_discord:
							break
						if pctl.playing_state == 1:
							logging.info("Reconnect discord...")
							RPC.connect()
							gui.discord_status = "Connected"
							break
						time.sleep(2)

					if not prefs.disconnect_discord:
						continue

				time.sleep(2)

				if prefs.disconnect_discord:
					RPC.clear(pid)
					RPC.close()
					prefs.disconnect_discord = False
					gui.discord_status = "Not connected"
					br = True
					break

			if br:
				break

			title = _("Unknown Track")
			tr = pctl.playing_object()
			if tr.artist != "" and tr.title != "":
				title = tr.title + " | " + tr.artist
				if len(title) > 150:
					title = _("Unknown Track")

			if tr.album:
				album = tr.album
			else:
				album = _("Unknown Album")
				if pctl.playing_state == 3:
					album = radiobox.loaded_station["title"]

			if len(album) == 1:
				album += " "

			if state == 1:
				#logging.info("PLAYING: " + title)
				#logging.info(start_time)
				url = get_album_art_url(pctl.playing_object())

				large_image = "tauon-standard"
				small_image = None
				if url:
					large_image = url
					small_image = "tauon-standard"
				RPC.update(
					pid=pid,
					state=album,
					details=title,
					start=int(start_time),
					large_image=large_image,
					small_image=small_image)

			else:
				#logging.info("Discord RPC - Stop")
				RPC.update(
					pid=pid,
					state="Idle",
					large_image="tauon-standard")

			time.sleep(5)

			if prefs.disconnect_discord:
				RPC.clear(pid)
				RPC.close()
				prefs.disconnect_discord = False
				break

	except Exception:
		logging.exception("Error connecting to Discord - is Discord running?")
		# show_message(_("Error connecting to Discord", mode='error')
		gui.discord_status = _("Error - Discord not running?")
		prefs.disconnect_discord = False

	finally:
		loop = asyncio.get_event_loop()
		if not loop.is_closed():
			loop.close()
		prefs.discord_active = False


def hit_discord() -> None:
	if prefs.discord_enable and prefs.discord_allow and not prefs.discord_active:
		discord_t = threading.Thread(target=discord_loop)
		discord_t.daemon = True
		discord_t.start()



x_menu.add(MenuItem(_("Exit Shuffle Lockdown"), toggle_shuffle_layout, show_test=exit_shuffle_layout))

def open_donate_link() -> None:
	webbrowser.open("https://github.com/sponsors/Taiko2k", new=2, autoraise=True)


x_menu.add(MenuItem(_("Donate"), open_donate_link))

x_menu.add(MenuItem(_("Exit"), tauon.exit, hint="Alt+F4", set_ref="User clicked menu exit button", pass_ref=+True))


def stop_quick_add() -> None:
	pctl.quick_add_target = None


def show_stop_quick_add(_) -> bool:
	return pctl.quick_add_target is not None


x_menu.add(MenuItem(_("Disengage Quick Add"), stop_quick_add, show_test=show_stop_quick_add))


def view_tracks() -> None:
	# if gui.show_playlist is False:
	#     gui.show_playlist = True
	if album_mode:
		toggle_album_mode()
	if gui.combo_mode:
		exit_combo()
	if gui.rsp:
		toggle_side_panel()


#
# def view_standard_full():
#     # if gui.show_playlist is False:
#     #     gui.show_playlist = True
#
#     if album_mode:
#         toggle_album_mode()
#     if gui.combo_mode:
#         toggle_combo_view(off=True)
#     if not gui.rsp:
#         toggle_side_panel()
#     global update_layout
#     update_layout = True
#     gui.rspw = window_size[0]


def view_standard_meta() -> None:
	# if gui.show_playlist is False:
	#     gui.show_playlist = True
	if album_mode:
		toggle_album_mode()

	if gui.combo_mode:
		exit_combo()

	if not gui.rsp:
		toggle_side_panel()

	global update_layout
	update_layout = True
	# gui.rspw = 80 + int(window_size[0] * 0.18)


def view_standard() -> None:
	# if gui.show_playlist is False:
	#     gui.show_playlist = True
	if album_mode:
		toggle_album_mode()
	if gui.combo_mode:
		exit_combo()
	if not gui.rsp:
		toggle_side_panel()


def standard_view_deco():
	if album_mode or gui.combo_mode or not gui.rsp:
		line_colour = colours.menu_text
	else:
		line_colour = colours.menu_text_disabled
	return [line_colour, colours.menu_background, None]


# def gallery_only_view():
#     if gui.show_playlist is False:
#         return
#     if not album_mode:
#         toggle_album_mode()
#     gui.show_playlist = False
#     global album_playlist_width
#     global update_layout
#     update_layout = True
#     gui.rspw = window_size[0]
#     album_playlist_width = gui.playlist_width
#     #gui.playlist_width = -19


def toggle_library_mode() -> None:
	if gui.set_mode:
		gui.set_mode = False
		# gui.set_bar = False
	else:
		gui.set_mode = True
		# gui.set_bar = True
	gui.update_layout()


def library_deco():
	tc = colours.menu_text
	if gui.combo_mode or (gui.show_playlist is False and album_mode):
		tc = colours.menu_text_disabled

	if gui.set_mode:
		return [tc, colours.menu_background, _("Disable Columns")]
	return [tc, colours.menu_background, _("Enable Columns")]


def break_deco():
	tex = colours.menu_text
	if gui.combo_mode or (gui.show_playlist is False and album_mode):
		tex = colours.menu_text_disabled
	if not break_enable:
		tex = colours.menu_text_disabled

	if not pctl.multi_playlist[pctl.active_playlist_viewing].hide_title:
		return [tex, colours.menu_background, _("Disable Title Breaks")]
	return [tex, colours.menu_background, _("Enable Title Breaks")]


def toggle_playlist_break() -> None:
	pctl.multi_playlist[pctl.active_playlist_viewing].hide_title ^= 1
	gui.pl_update = 1


# ---------------------------------------------------------------------------------------


def transcode_single(item: list[tuple[int, str]], manual_directory: str | None = None, manual_name: str | None = None):
	global core_use
	global dl_use

	if manual_directory != None:
		codec = "opus"
		output = manual_directory
		track = item
		core_use += 1
		bitrate = 48
	else:
		track = item[0]
		codec = prefs.transcode_codec
		output = prefs.encoder_output / item[1]
		bitrate = prefs.transcode_bitrate

	t = pctl.master_library[track]

	path = t.fullpath
	cleanup = False

	if t.is_network:
		while dl_use > 1:
			time.sleep(0.2)
		dl_use += 1
		try:
			url, params = pctl.get_url(t)
			assert url
			path = os.path.join(tmp_cache_dir(), str(t.index))
			if os.path.exists(path):
				os.remove(path)
			logging.info("Downloading file...")
			with requests.get(url, params=params, timeout=60) as response, open(path, "wb") as out_file:
				out_file.write(response.content)
			logging.info("Download complete")
			cleanup = True
		except Exception:
			logging.exception("Error downloading file")
		dl_use -= 1

	if not os.path.isfile(path):
		show_message(_("Encoding warning: Missing one or more files"))
		core_use -= 1
		return

	out_line = encode_track_name(t)

	if not (output / _("output")).exists():
		(output / _("output")).mkdir()
	target_out = str(output / _("output") / (str(track) + "." + codec))

	command = tauon.get_ffmpeg() + " "

	if not t.is_cue:
		command += '-i "'
	else:
		command += "-ss " + str(t.start_time)
		command += " -t " + str(t.length)

		command += ' -i "'

	command += path.replace('"', '\\"')

	command += '" '
	if pctl.master_library[track].is_cue:
		if t.title != "":
			command += '-metadata title="' + t.title.replace('"', "").replace("'", "") + '" '
		if t.artist != "":
			command += '-metadata artist="' + t.artist.replace('"', "").replace("'", "") + '" '
		if t.album != "":
			command += '-metadata album="' + t.album.replace('"', "").replace("'", "") + '" '
		if t.track_number != "":
			command += '-metadata track="' + str(t.track_number).replace('"', "").replace("'", "") + '" '
		if t.date != "":
			command += '-metadata year="' + str(t.date).replace('"', "").replace("'", "") + '" '

	if codec != "flac":
		command += " -b:a " + str(bitrate) + "k -vn "

	command += '"' + target_out.replace('"', '\\"') + '"'

	# logging.info(shlex.split(command))
	startupinfo = None
	if system == "Windows" or msys:
		startupinfo = subprocess.STARTUPINFO()
		startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

	if not msys:
		command = shlex.split(command)

	subprocess.call(command, stdout=subprocess.PIPE, shell=False, startupinfo=startupinfo)

	logging.info("FFmpeg finished")
	if codec == "opus" and prefs.transcode_opus_as:
		codec = "ogg"

	# logging.info(target_out)

	if manual_name is None:
		final_out = output / (out_line + "." + codec)
		final_name = out_line + "." + codec
		os.rename(target_out, final_out)
	else:
		final_out = output / (manual_name + "." + codec)
		final_name = manual_name + "." + codec
		os.rename(target_out, final_out)

	if prefs.transcode_inplace and not t.is_network and not t.is_cue:
		logging.info("MOVE AND REPLACE!")
		if os.path.isfile(final_out) and os.path.getsize(final_out) > 1000:
			new_name = os.path.join(t.parent_folder_path, final_name)
			logging.info(new_name)
			shutil.move(final_out, new_name)

			old_key = star_store.key(track)
			old_star = star_store.full_get(track)

			try:
				send2trash(pctl.master_library[track].fullpath)
			except Exception:
				logging.exception("File trash error")

			if os.path.isfile(pctl.master_library[track].fullpath):
				try:
					os.remove(pctl.master_library[track].fullpath)
				except Exception:
					logging.exception("File delete error")

			pctl.master_library[track].fullpath = new_name
			pctl.master_library[track].file_ext = codec.upper()

			# Update and merge playtimes
			new_key = star_store.key(track)
			if old_star and (new_key != old_key):

				new_star = star_store.full_get(track)
				if new_star is None:
					new_star = star_store.new_object()

				new_star[0] += old_star[0]
				if old_star[2] > 0 and new_star[2] == 0:
					new_star[2] = old_star[2]
				new_star[1] = "".join(set(new_star[1] + old_star[1]))

				if old_key in star_store.db:
					del star_store.db[old_key]

				star_store.db[new_key] = new_star

	gui.transcoding_bach_done += 1
	if cleanup:
		os.remove(path)
	core_use -= 1
	gui.update += 1


# ---------------------
added = []


def cue_scan(content: str, tn: TrackClass) -> int | None:
	# Get length from backend

	lasttime = tn.length

	content = content.replace("\r", "")
	content = content.split("\n")

	#logging.info(content)

	global added

	cued = []

	LENGTH = 0
	PERFORMER = ""
	TITLE = ""
	START = 0
	DATE = ""
	ALBUM = ""
	GENRE = ""
	MAIN_PERFORMER = ""

	for LINE in content:
		if 'TITLE "' in LINE:
			ALBUM = LINE[7:len(LINE) - 2]

		if 'PERFORMER "' in LINE:
			while LINE[0] != "P":
				LINE = LINE[1:]

			MAIN_PERFORMER = LINE[11:len(LINE) - 2]

		if "REM DATE" in LINE:
			DATE = LINE[9:len(LINE) - 1]

		if "REM GENRE" in LINE:
			GENRE = LINE[10:len(LINE) - 1]

		if "TRACK " in LINE:
			break

	for LINE in reversed(content):
		if len(LINE) > 100:
			return 1
		if "INDEX 01 " in LINE:
			temp = ""
			pos = len(LINE)
			pos -= 1
			while LINE[pos] != ":":
				pos -= 1
				if pos < 8:
					break

			START = int(LINE[pos - 2:pos]) + (int(LINE[pos - 5:pos - 3]) * 60)
			LENGTH = int(lasttime) - START
			lasttime = START

		elif 'PERFORMER "' in LINE:
			switch = 0
			for i in range(len(LINE)):
				if switch == 1 and LINE[i] == '"':
					break
				if switch == 1:
					PERFORMER += LINE[i]
				if LINE[i] == '"':
					switch = 1

		elif 'TITLE "' in LINE:

			switch = 0
			for i in range(len(LINE)):
				if switch == 1 and LINE[i] == '"':
					break
				if switch == 1:
					TITLE += LINE[i]
				if LINE[i] == '"':
					switch = 1

		elif "TRACK " in LINE:

			pos = 0
			while LINE[pos] != "K":
				pos += 1
				if pos > 15:
					return 1
			TN = LINE[pos + 2:pos + 4]

			TN = int(TN)

			# try:
			#     bitrate = audio.info.bitrate
			# except Exception:
			#     logging.exception("Failed to set audio bitrate")
			#     bitrate = 0

			if PERFORMER == "":
				PERFORMER = MAIN_PERFORMER

			nt = copy.deepcopy(tn)

			nt.cue_sheet = ""
			nt.is_embed_cue = True

			nt.index = pctl.master_count
			# nt.fullpath = filepath.replace('\\', '/')
			# nt.filename = filename
			# nt.parent_folder_path = os.path.dirname(filepath.replace('\\', '/'))
			# nt.parent_folder_name = os.path.splitext(os.path.basename(filepath))[0]
			# nt.file_ext = os.path.splitext(os.path.basename(filepath))[1][1:].upper()
			if MAIN_PERFORMER:
				nt.album_artist = MAIN_PERFORMER
			if PERFORMER:
				nt.artist = PERFORMER
			if GENRE:
				nt.genre = GENRE
			nt.title = TITLE
			nt.length = LENGTH
			# nt.bitrate = source_track.bitrate
			if ALBUM:
				nt.album = ALBUM
			if DATE:
				nt.date = DATE.replace('"', "")
			nt.track_number = TN
			nt.start_time = START
			nt.is_cue = True
			nt.size = 0  # source_track.size
			# nt.samplerate = source_track.samplerate
			if TN == 1:
				nt.size = os.path.getsize(nt.fullpath)

			pctl.master_library[pctl.master_count] = nt

			cued.append(pctl.master_count)
			# loaded_pathes_cache[filepath.replace('\\', '/')] = pctl.master_count
			# added.append(pctl.master_count)

			pctl.master_count += 1
			LENGTH = 0
			PERFORMER = ""
			TITLE = ""
			START = 0
			TN = 0

	added += reversed(cued)

	# cue_list.append(filepath)


def get_album_from_first_track(track_position, track_id=None, pl_number=None, pl_id: int | None = None):
	if pl_number is None:

		if pl_id:
			pl_number = id_to_pl(pl_id)
		else:
			pl_number = pctl.active_playlist_viewing

	playlist = pctl.multi_playlist[pl_number].playlist_ids

	if track_id is None:
		track_id = playlist[track_position]

	if playlist[track_position] != track_id:
		return []

	tracks = []
	album_parent_path = pctl.get_track(track_id).parent_folder_path

	i = track_position

	while i < len(playlist):
		if pctl.get_track(playlist[i]).parent_folder_path != album_parent_path:
			break

		tracks.append(playlist[i])
		i += 1

	return tracks





search_over = SearchOverlay()




message_box = MessageBox()




nagbox = NagBox()


def worker3():
	while True:
		# time.sleep(0.04)

		# if tauon.thread_manager.exit_worker3:
		#     tauon.thread_manager.exit_worker3 = False
		#     return
		# time.sleep(1)

		tauon.gall_ren.worker_render()


def worker4():
	gui.style_worker_timer.set()
	while True:
		if prefs.art_bg or (gui.mode == 3 and prefs.mini_mode_mode == 5):
			style_overlay.worker()

		time.sleep(0.01)
		if pctl.playing_state > 0 and pctl.playing_time < 5:
			gui.style_worker_timer.set()
		if gui.style_worker_timer.get() > 5:
			return


worker2_lock = threading.Lock()
spot_search_rate_timer = Timer()


def worker2():
	while True:
		worker2_lock.acquire()

		if search_over.search_text.text and not (len(search_over.search_text.text) == 1 and ord(search_over.search_text.text[0]) < 128):

			if search_over.spotify_mode:
				t = spot_search_rate_timer.get()
				if t < 1:
					time.sleep(1 - t)
					spot_search_rate_timer.set()
				logging.info("Spotify search")
				search_over.results.clear()
				results = tauon.spot_ctl.search(search_over.search_text.text)
				if results is not None:
					search_over.results = results
				else:
					search_over.active = False
					gui.show_message(_(
						"Global search + Tab triggers Spotify search but Spotify is not enabled in settings!"),
						mode="warning")
				search_over.searched_text = search_over.search_text.text
				search_over.sip = False

			elif True:
				# perf_timer.set()

				temp_results = []

				search_over.searched_text = search_over.search_text.text

				artists = {}
				albums = {}
				genres = {}
				metas = {}
				composers = {}
				years = {}

				tracks = set()

				br = 0

				if search_over.searched_text in ("the", "and"):
					continue

				search_over.sip = True
				gui.update += 1

				o_text = search_over.search_text.text.lower().replace("-", "")

				dia_mode = False
				if all([ord(c) < 128 for c in o_text]):
					dia_mode = True

				artist_mode = False
				if o_text.startswith("artist "):
					o_text = o_text[7:]
					artist_mode = True

				album_mode = False
				if o_text.startswith("album "):
					o_text = o_text[6:]
					album_mode = True

				composer_mode = False
				if o_text.startswith("composer "):
					o_text = o_text[9:]
					composer_mode = True

				year_mode = False
				if o_text.startswith("year "):
					o_text = o_text[5:]
					year_mode = True

				cn_mode = False
				if use_cc and re.search(r"[\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df\u2a700-\u2b73f\u2b740-\u2b81f\u2b820-\u2ceaf\uf900-\ufaff\u2f800-\u2fa1f]", o_text):
					t_cn = s2t.convert(o_text)
					s_cn = t2s.convert(o_text)
					cn_mode = True

				s_text = o_text

				searched = set()

				for playlist in pctl.multi_playlist:

					# if "<" in playlist.title:
					#     #logging.info("Skipping search on derivative playlist: " + playlist.title)
					#     continue

					for track in playlist.playlist_ids:

						if track in searched:
							continue
						searched.add(track)


						if cn_mode:
							s_text = o_text
							cache_string = search_string_cache.get(track)
							if cache_string:
								if search_magic_any(s_text, cache_string):
									pass
								elif search_magic_any(t_cn, cache_string):
									s_text = t_cn
								elif search_magic_any(s_cn, cache_string):
									s_text = s_cn

						if dia_mode:
							cache_string = search_dia_string_cache.get(track)
							if cache_string is not None:
								if not search_magic_any(s_text, cache_string):
									continue
								# if s_text not in cache_string:
								#     continue
						else:
							cache_string = search_string_cache.get(track)
							if cache_string is not None:
								if not search_magic_any(s_text, cache_string):
									continue

						t = pctl.master_library[track]

						title = t.title.lower().replace("-", "")
						artist = t.artist.lower().replace("-", "")
						album_artist = t.album_artist.lower().replace("-", "")
						composer = t.composer.lower().replace("-", "")
						date = t.date.lower().replace("-", "")
						album = t.album.lower().replace("-", "")
						genre = t.genre.lower().replace("-", "")
						filename = t.filename.lower().replace("-", "")
						stem = os.path.dirname(t.parent_folder_path).lower().replace("-", "")
						sartist = t.misc.get("artist_sort", "").lower()

						if cache_string is None:
							if not dia_mode:
								search_string_cache[
									track] = title + artist + album_artist + composer + date + album + genre + sartist + filename + stem

							if cn_mode:
								cache_string = search_string_cache.get(track)
								if cache_string:
									if search_magic_any(s_text, cache_string):
										pass
									elif search_magic_any(t_cn, cache_string):
										s_text = t_cn
									elif search_magic_any(s_cn, cache_string):
										s_text = s_cn

						if dia_mode:
							title = unidecode(title)

							artist = unidecode(artist)
							album_artist = unidecode(album_artist)
							composer = unidecode(composer)
							album = unidecode(album)
							filename = unidecode(filename)
							sartist = unidecode(sartist)

							if cache_string is None:
								search_dia_string_cache[
									track] = title + artist + album_artist + composer + date + album + genre + sartist + filename + stem

						stem = os.path.dirname(t.parent_folder_path)

						if len(s_text) > 2 and s_text in stem.replace("-", "").lower():
							# if search_over.all_folders or (artist not in stem.lower() and album not in stem.lower()):

							if stem in metas:
								metas[stem] += 2
							else:
								temp_results.append([5, stem, track, playlist.uuid_int, 0])
								metas[stem] = 2

						if s_text in genre:

							if "/" in genre or "," in genre or ";" in genre:

								for split in genre.replace(";", "/").replace(",", "/").split("/"):
									if s_text in split:

										split = genre_correct(split)
										if prefs.sep_genre_multi:
											split += "+"
										if split in genres:
											genres[split] += 3
										else:
											temp_results.append([3, split, track, playlist.uuid_int, 0])
											genres[split] = 1
							else:
								name = genre_correct(t.genre)
								if name in genres:
									genres[name] += 3
								else:
									temp_results.append([3, name, track, playlist.uuid_int, 0])
									genres[name] = 1

						if s_text in composer:

							if t.composer in composers:
								composers[t.composer] += 2
							else:
								temp_results.append([6, t.composer, track, playlist.uuid_int, 0])
								composers[t.composer] = 2

						if s_text in date:

							year = get_year_from_string(date)
							if year:

								if year in years:
									years[year] += 1
								else:
									temp_results.append([7, year, track, playlist.uuid_int, 0])
									years[year] = 1000

						if search_magic(s_text, title + artist + filename + album + sartist + album_artist):

							if "artists" in t.misc and t.misc["artists"]:
								for a in t.misc["artists"]:
									if search_magic(s_text, a.lower()):

										value = 1
										if a.lower().startswith(s_text):
											value = 5

										# Add artist
										if a in artists:
											artists[a] += value
										else:
											temp_results.append([0, a, track, playlist.uuid_int, 0])
											artists[a] = value

										if t.album in albums:
											albums[t.album] += 1
										else:
											temp_results.append([1, t.album, track, playlist.uuid_int, 0])
											albums[t.album] = 1

							elif search_magic(s_text, artist + sartist):

								value = 1
								if artist.startswith(s_text):
									value = 10

								# Add artist
								if t.artist in artists:
									artists[t.artist] += value
								else:
									temp_results.append([0, t.artist, track, playlist.uuid_int, 0])
									artists[t.artist] = value

								if t.album in albums:
									albums[t.album] += 1
								else:
									temp_results.append([1, t.album, track, playlist.uuid_int, 0])
									albums[t.album] = 1

							elif search_magic(s_text, album_artist):

								# Add album artist
								value = 1
								if t.album_artist.startswith(s_text):
									value = 5

								if t.album_artist in artists:
									artists[t.album_artist] += value
								else:
									temp_results.append([0, t.album_artist, track, playlist.uuid_int, 0])
									artists[t.album_artist] = value

								if t.album in albums:
									albums[t.album] += 1
								else:
									temp_results.append([1, t.album, track, playlist.uuid_int, 0])
									albums[t.album] = 1

							if s_text in album:

								value = 1
								if s_text == album:
									value = 3

								if t.album in albums:
									albums[t.album] += value
								else:
									temp_results.append([1, t.album, track, playlist.uuid_int, 0])
									albums[t.album] = value

							if search_magic(s_text, artist + sartist) or search_magic(s_text, album):

								if t.album in albums:
									albums[t.album] += 3
								else:
									temp_results.append([1, t.album, track, playlist.uuid_int, 0])
									albums[t.album] = 3

							elif search_magic_any(s_text, artist + sartist) and search_magic_any(s_text, album):

								if t.album in albums:
									albums[t.album] += 3
								else:
									temp_results.append([1, t.album, track, playlist.uuid_int, 0])
									albums[t.album] = 3

							if s_text in title:

								if t not in tracks:

									value = 50
									if s_text == title:
										value = 200

									temp_results.append([2, t.title, track, playlist.uuid_int, value])

									tracks.add(t)

							elif t not in tracks:
								temp_results.append([2, t.title, track, playlist.uuid_int, 1])

								tracks.add(t)

						br += 1
						if br > 800:
							time.sleep(0.005)  # Throttle thread
							br = 0
							if search_over.searched_text != search_over.search_text.text:
								break

				search_over.sip = False
				search_over.on = 0
				gui.update += 1

				# Remove results not matching any filter keyword

				if artist_mode:
					for i in reversed(range(len(temp_results))):
						if temp_results[i][0] != 0:
							del temp_results[i]

				elif album_mode:
					for i in reversed(range(len(temp_results))):
						if temp_results[i][0] != 1:
							del temp_results[i]

				elif composer_mode:
					for i in reversed(range(len(temp_results))):
						if temp_results[i][0] != 6:
							del temp_results[i]

				elif year_mode:
					for i in reversed(range(len(temp_results))):
						if temp_results[i][0] != 7:
							del temp_results[i]

				# Sort results by weightings
				for i, item in enumerate(temp_results):
					if item[0] == 0:
						temp_results[i][4] = artists[item[1]]
					if item[0] == 1:
						temp_results[i][4] = albums[item[1]]
					if item[0] == 3:
						temp_results[i][4] = genres[item[1]]
					if item[0] == 5:
						temp_results[i][4] = metas[item[1]]
						if not search_over.all_folders:
							if metas[item[1]] < 42:
								temp_results[i] = None
					if item[0] == 6:
						temp_results[i][4] = composers[item[1]]
					if item[0] == 7:
						temp_results[i][4] = years[item[1]]
					# 8 is playlists

				temp_results[:] = [item for item in temp_results if item is not None]
				search_over.results = sorted(temp_results, key=lambda x: x[4], reverse=True)
				#logging.info(search_over.results)

				i = 0
				for playlist in pctl.multi_playlist:
					if search_magic(s_text, playlist.title.lower()):
						item = [8, playlist.title, None, playlist.uuid_int, 100000]
						search_over.results.insert(0, item)
						i += 1
						if i > 3:
							break

				search_over.on = 0
				search_over.force_select = 0
				#logging.info(perf_timer.get())


def worker1():
	global cue_list
	global loaderCommand
	global loaderCommandReady
	global DA_Formats
	global home
	global loading_in_progress
	global added
	global to_get
	global to_got

	loaded_pathes_cache = {}
	loaded_cue_cache = {}
	added = []

	def get_quoted_from_line(line):

		# Extract quoted or unquoted string from a line
		# e.g., 'FILE "01 - Track01.wav" WAVE' or 'TITLE Track01' or "PERFORMER 'Artist Name'"

		parts = line.split(None, 1)
		if len(parts) < 2:
			return ""

		content = parts[1].strip()

		if content.startswith('"'):
			end = content.find('"', 1)
			return content[1:end] if end != -1 else content[1:]
		if content.startswith("'"):
			end = content.find("'", 1)
			return content[1:end] if end != -1 else content[1:]
		# If not quoted, return the first word
		return content.split()[0]

	def add_from_cue(path):

		global added

		if not msys:  # Windows terminal doesn't like unicode
			logging.info("Reading CUE file: " + path)

		try:

			try:
				with open(path, encoding="utf_8") as f:
					content = f.readlines()
					logging.info("-- Reading as UTF-8")
			except Exception:
				logging.exception("Failed opening file as UTF-8")
				try:
					with open(path, encoding="utf_16") as f:
						content = f.readlines()
						logging.info("-- Reading as UTF-16")
				except Exception:
					logging.exception("Failed opening file as UTF-16")
					try:
						j = False
						try:
							with open(path, encoding="shiftjis") as f:
								content = f.readlines()
								for line in content:
									for c in j_chars:
										if c in line:
											j = True
											logging.info("-- Reading as SHIFT-JIS")
											break
						except Exception:
							logging.exception("Failed opening file as shiftjis")
						if not j:
							with open(path, encoding="windows-1251") as f:
								content = f.readlines()
							logging.info("-- Fallback encoding read as windows-1251")

					except Exception:
						logging.exception("Abort: Can't detect encoding of CUE file")
						return 1

			f.close()

			# We want to detect if this is a cue sheet that points to either a single file with subtracks, or multiple
			# files with mutiple subtracks, but not multiple files that are individual tracks
			# i.e, is there really any splitting going on

			files = 0
			files_with_subtracks = 0
			subtrack_count = 0
			for line in content:
				if line.startswith("FILE "):
					files += 1
					if subtrack_count > 2:  # A hack way to avoid non-compliant EAC CUE sheet
						files_with_subtracks += 1
					subtrack_count = 0
				elif line.strip().startswith("TRACK "):
					subtrack_count += 1
			if subtrack_count > 2:
				files_with_subtracks += 1

			if files == 1:
				pass
			elif files_with_subtracks > 1:
				pass
			else:
				return 1

			cue_performer = ""
			cue_date = ""
			cue_album = ""
			cue_genre = ""
			cue_main_performer = ""
			cue_songwriter = ""
			cue_disc = 0
			cue_disc_total = 0

			cd = []
			cds = []

			file_name = ""
			file_path = ""

			in_header = True

			i = -1
			while True:
				i += 1

				if i > len(content) - 1:
					break

				line = content[i].strip()

				if in_header:
					if line.startswith("REM "):
						line = line[4:]

					if line.startswith("TITLE "):
						cue_album = get_quoted_from_line(line)
					if line.startswith("PERFORMER "):
						cue_performer = get_quoted_from_line(line)
					if line.startswith("MAIN PERFORMER "):
						cue_main_performer = get_quoted_from_line(line)
					if line.startswith("SONGWRITER "):
						cue_songwriter = get_quoted_from_line(line)
					if line.startswith("GENRE "):
						cue_genre = get_quoted_from_line(line)
					if line.startswith("DATE "):
						cue_date = get_quoted_from_line(line)
					if line.startswith("DISCNUMBER "):
						cue_disc = get_quoted_from_line(line)
					if line.startswith("TOTALDISCS "):
						cue_disc_total = get_quoted_from_line(line)

					if line.startswith("FILE "):
						in_header = False
					else:
						continue

				if line.startswith("FILE "):

					if cd:
						cds.append(cd)
						cd = []

					file_name = get_quoted_from_line(line)
					file_path = os.path.join(os.path.dirname(path), file_name)

					if not os.path.isfile(file_path):
						if files == 1:
							logging.info("-- The referenced source file wasn't found. Searching for matching file name...")
							for item in os.listdir(os.path.dirname(path)):
								if os.path.splitext(item)[0] == os.path.splitext(os.path.basename(path))[0]:
									if ".cue" not in item.lower() and item.split(".")[-1].lower() in DA_Formats:
										file_name = item
										file_path = os.path.join(os.path.dirname(path), file_name)
										logging.info("-- Source found at: " + file_path)
										break
							else:
								logging.error("-- Abort: Source file not found")
								return 1
						else:
							logging.error("-- Abort: Source file not found")
							return 1

				if line.startswith("TRACK "):
					line = line[6:]
					if line.endswith("AUDIO"):
						line = line[:-5]

					c = loaded_cue_cache.get((file_path.replace("\\", "/"), int(line.strip())))
					if c is not None:
						nt = c
					else:
						nt = TrackClass()
						nt.index = pctl.master_count
						pctl.master_count += 1

					nt.fullpath = file_path
					nt.filename = file_name
					nt.parent_folder_path = os.path.dirname(file_path.replace("\\", "/"))
					nt.parent_folder_name = os.path.splitext(os.path.basename(file_path))[0]
					nt.file_ext = os.path.splitext(file_name)[1][1:].upper()
					nt.is_cue = True

					nt.album_artist = cue_main_performer
					if not cue_main_performer:
						nt.album_artist = cue_performer
					nt.artist = cue_performer
					nt.composer = cue_songwriter
					nt.genre = cue_genre
					nt.album = cue_album
					nt.date = cue_date.replace('"', "")
					nt.track_number = int(line.strip())
					if nt.track_number == 1:
						nt.size = os.path.getsize(nt.fullpath)
					nt.misc["parent-size"] = os.path.getsize(nt.fullpath)

					while True:
						i += 1
						if i > len(content) - 1 or content[i].startswith("FILE ") or content[i].strip().startswith(
								"TRACK"):
							break

						line = content[i]
						line = line.strip()

						if line.startswith("TITLE"):
							nt.title = get_quoted_from_line(line)
						if line.startswith("PERFORMER"):
							nt.artist = get_quoted_from_line(line)
						if line.startswith("SONGWRITER"):
							nt.composer = get_quoted_from_line(line)
						if line.startswith("INDEX 01 ") and ":" in line:
							line = line[9:]
							times = line.split(":")
							nt.start_time = int(times[0]) * 60 + int(times[1]) + int(times[2]) / 100

					i -= 1
					cd.append(nt)

			if cd:
				cds.append(cd)

			for cdn, cd in enumerate(cds):

				last_end = None
				end_track = TrackClass()
				end_track.fullpath = cd[-1].fullpath
				tag_scan(end_track)

				# Remove target track if already imported
				for i in reversed(range(len(added))):
					if pctl.get_track(added[i]).fullpath == end_track.fullpath:
						del added[i]

				# Update with proper length
				for track in reversed(cd):

					if last_end == None:
						last_end = end_track.length

					track.length = last_end - track.start_time
					track.samplerate = end_track.samplerate
					track.bitrate = end_track.bitrate
					track.bit_depth = end_track.bit_depth
					track.misc["parent-length"] = end_track.length
					last_end = track.start_time

					# inherit missing metadata
					if not track.date:
						track.date = end_track.date
					if not track.album_artist:
						track.album_artist = end_track.album_artist
					if not track.album:
						track.album = end_track.album
					if not track.artist:
						track.artist = end_track.artist
					if not track.genre:
						track.genre = end_track.genre
					if not track.comment:
						track.comment = end_track.comment
					if not track.composer:
						track.composer = end_track.composer

					if cue_disc:
						track.disc_number = cue_disc
					elif len(cds) == 0:
						track.disc_number = ""
					else:
						track.disc_number = str(cdn)

					if cue_disc_total:
						track.disc_total = cue_disc_total
					elif len(cds) == 0:
						track.disc_total = ""
					else:
						track.disc_total = str(len(cds))


			# Add all tracks for import to playlist
			for cd in cds:
				for track in cd:
					pctl.master_library[track.index] = track
					if track.fullpath not in cue_list:
						cue_list.append(track.fullpath)
					loaded_pathes_cache[track.fullpath] = track.index
					added.append(track.index)

		except Exception:
			logging.exception("Internal error processing CUE file")

	def add_file(path, force_scan: bool = False) -> int | None:
		# bm.get("add file start")
		global DA_Formats
		global to_got

		if not os.path.isfile(path):
			logging.error("File to import missing")
			return 0

		if os.path.splitext(path)[1][1:] in {"CUE", "cue"}:
			add_from_cue(path)
			return 0

		if path.lower().endswith(".xspf"):
			logging.info("Found XSPF file at: " + path)
			load_xspf(path)
			return 0

		if path.lower().endswith(".m3u") or path.lower().endswith(".m3u8"):
			load_m3u(path)
			return 0

		if path.endswith(".pls"):
			load_pls(path)
			return 0

		if os.path.splitext(path)[1][1:].lower() not in DA_Formats:
			if os.path.splitext(path)[1][1:].lower() in Archive_Formats:
				if not prefs.auto_extract:
					show_message(
						_("You attempted to drop an archive."),
						_('However the "extract archive" function is not enabled.'), mode="info")
				else:
					type = os.path.splitext(path)[1][1:].lower()
					split = os.path.splitext(path)
					target_dir = split[0]
					if prefs.extract_to_music and music_directory is not None:
						target_dir = os.path.join(str(music_directory), os.path.basename(target_dir))
					#logging.info(os.path.getsize(path))
					if os.path.getsize(path) > 4e+9:
						logging.warning("Archive file is large!")
						show_message(_("Skipping oversize zip file (>4GB)"))
						return 1
					if not os.path.isdir(target_dir) and not os.path.isfile(target_dir):
						if type == "zip":
							try:
								b = to_got
								to_got = "ex"
								gui.update += 1
								zip_ref = zipfile.ZipFile(path, "r")

								zip_ref.extractall(target_dir)
								zip_ref.close()
							except RuntimeError as e:
								logging.exception("Zip error")
								to_got = b
								if "encrypted" in e:
									show_message(
										_("Failed to extract zip archive."),
										_("The archive is encrypted. You'll need to extract it manually with the password."),
										mode="warning")
								else:
									show_message(
										_("Failed to extract zip archive."),
										_("Maybe archive is corrupted? Does disk have enough space and have write permission?"),
										mode="warning")
								return 1
							except Exception:
								logging.exception("Zip error 2")
								to_got = b
								show_message(
									_("Failed to extract zip archive."),
									_("Maybe archive is corrupted? Does disk have enough space and have write permission?"),
									mode="warning")
								return 1

						elif type == "rar":
							b = to_got
							try:
								to_got = "ex"
								gui.update += 1
								line = launch_prefix + "unrar x -y -p- " + shlex.quote(path) + " " + shlex.quote(
									target_dir) + os.sep
								result = subprocess.run(shlex.split(line), check=True)
								logging.info(result)
							except Exception:
								logging.exception("Failed to extract rar archive.")
								to_got = b
								show_message(_("Failed to extract rar archive."), mode="warning")

								return 1

						elif type == "7z":
							b = to_got
							try:
								to_got = "ex"
								gui.update += 1
								line = launch_prefix + "7z x -y " + shlex.quote(path) + " -o" + shlex.quote(
									target_dir) + os.sep
								result = subprocess.run(shlex.split(line), check=True)
								logging.info(result)
							except Exception:
								logging.exception("Failed to extract 7z archive.")
								to_got = b
								show_message(_("Failed to extract 7z archive."), mode="warning")

								return 1

						upper = os.path.dirname(target_dir)
						cont = os.listdir(target_dir)
						new = upper + "/temporaryfolderd"
						error = False
						if len(cont) == 1 and os.path.isdir(split[0] + "/" + cont[0]):
							logging.info("one thing")
							os.rename(target_dir, new)
							try:
								shutil.move(new + "/" + cont[0], upper)
							except Exception:
								logging.exception("Could not move file")
								error = True
							shutil.rmtree(new)
							logging.info(new)
							target_dir = upper + "/" + cont[0]
							if not os.path.isdir(target_dir):
								logging.error("Extract error, expected directory not found")

						if True and not error and prefs.auto_del_zip:
							logging.info("Moving archive file to trash: " + path)
							try:
								send2trash(path)
							except Exception:
								logging.exception("Could not move archive to trash")
								show_message(_("Could not move archive to trash"), path, mode="info")

						to_got = b
						gets(target_dir)
						quick_import_done.append(target_dir)
					# gets(target_dir)

			return 1

		to_got += 1
		gui.update = 1

		path = path.replace("\\", "/")

		if path in loaded_pathes_cache:
			de = loaded_pathes_cache[path]

			if pctl.master_library[de].fullpath in cue_list:
				logging.info("File has an associated .cue file... Skipping")
				return None

			if pctl.master_library[de].file_ext.lower() in GME_Formats:
				# Skip cache for subtrack formats
				pass
			else:
				added.append(de)
				return None

		time.sleep(0.002)

		# audio = auto.File(path)

		nt = TrackClass()

		nt.index = pctl.master_count
		set_path(nt, path)

		def commit_track(nt):
			pctl.master_library[pctl.master_count] = nt
			added.append(pctl.master_count)

			if prefs.auto_sort or force_scan:
				tag_scan(nt)
			else:
				after_scan.append(nt)
				tauon.thread_manager.ready("worker")

			pctl.master_count += 1

		# nt = tag_scan(nt)
		if nt.cue_sheet != "":
			tag_scan(nt)
			cue_scan(nt.cue_sheet, nt)
			del nt

		elif nt.file_ext.lower() in GME_Formats and gme:

			emu = ctypes.c_void_p()
			err = gme.gme_open_file(nt.fullpath.encode("utf-8"), ctypes.byref(emu), -1)
			if not err:
				n = gme.gme_track_count(emu)
				for i in range(n):
					nt = TrackClass()
					set_path(nt, path)
					nt.index = pctl.master_count
					nt.subtrack = i
					commit_track(nt)

				gme.gme_delete(emu)

		else:

			commit_track(nt)

		# bm.get("fill entry")
		if gui.auto_play_import:
			pctl.jump(pctl.master_count - 1)
			gui.auto_play_import = False

	# Count the approx number of files to be imported
	def pre_get(direc):

		global to_get

		to_get = 0
		for root, dirs, files in os.walk(direc):
			to_get += len(files)
			if gui.im_cancel:
				return
			gui.update = 3

	def gets(direc, force_scan=False):

		global DA_Formats

		if os.path.basename(direc) == "__MACOSX":
			return

		try:
			items_in_dir = os.listdir(direc)
			if use_natsort:
				items_in_dir = natsort.os_sorted(items_in_dir)
			else:
				items_in_dir.sort()
		except PermissionError:
			logging.exception("Permission error accessing one or more files")
			if snap_mode:
				show_message(
					_("Permission error accessing one or more files."),
					_("If this location is on external media, see https://") + "github.com/Taiko2k/TauonMusicBox/wiki/Snap-Permissions",
					mode="bubble")
			else:
				show_message(_("Permission error accessing one or more files"), mode="warning")

			return
		except Exception:
			logging.exception("Unknown error accessing one or more files")
			return

		for q in range(len(items_in_dir)):
			if items_in_dir[q][0] == ".":
				continue
			if os.path.isdir(os.path.join(direc, items_in_dir[q])):
				gets(os.path.join(direc, items_in_dir[q]))
			if gui.im_cancel:
				return

		for q in range(len(items_in_dir)):
			if items_in_dir[q][0] == ".":
				continue
			if os.path.isdir(os.path.join(direc, items_in_dir[q])) is False:

				if os.path.splitext(items_in_dir[q])[1][1:].lower() in DA_Formats:

					if len(items_in_dir[q]) > 2 and items_in_dir[q][0:2] == "._":
						continue

					add_file(os.path.join(direc, items_in_dir[q]).replace("\\", "/"), force_scan)

				elif os.path.splitext(items_in_dir[q])[1][1:] in {"CUE", "cue"}:
					add_from_cue(os.path.join(direc, items_in_dir[q]).replace("\\", "/"))

			if gui.im_cancel:
				return

	def cache_paths():
		dic = {}
		dic2 = {}
		for key, value in pctl.master_library.items():
			if value.is_network:
				continue
			dic[value.fullpath.replace("\\", "/")] = key
			if value.is_cue:
				dic2[(value.fullpath.replace("\\", "/"), value.track_number)] = value
		return dic, dic2


	#logging.info(pctl.master_library)

	global transcode_list
	global transcode_state
	global album_art_gen
	global cm_clean_db
	global to_got
	global to_get
	global move_in_progress

	active_timer = Timer()
	while True:

		if not after_scan:
			time.sleep(0.1)

		if after_scan or load_orders or \
				artist_list_box.load or \
				artist_list_box.to_fetch or \
				gui.regen_single_id or \
				gui.regen_single > -1 or \
				pctl.after_import_flag or \
				tauon.worker_save_state or \
				move_jobs or \
				cm_clean_db or \
				transcode_list or \
				to_scan or \
				loaderCommandReady:
			active_timer.set()
		elif active_timer.get() > 5:
			return

		if after_scan:
			i = 0
			while after_scan:
				i += 1

				if i > 123:
					break

				tag_scan(after_scan[0])

				gui.update = 2
				gui.pl_update = 1
				# time.sleep(0.001)
				if pctl.running:
					del after_scan[0]
				else:
					break

			album_artist_dict.clear()

		artist_list_box.worker()

		# Update smart playlists
		if gui.regen_single_id is not None:
			regenerate_playlist(pl=-1, silent=True, id=gui.regen_single_id)
			gui.regen_single_id = None

		# Update smart playlists
		if gui.regen_single > -1:
			target = gui.regen_single
			gui.regen_single = -1
			regenerate_playlist(target, silent=True)

		if pctl.after_import_flag and not after_scan and not search_over.active and not loading_in_progress:
			pctl.after_import_flag = False

			for i, plist in enumerate(pctl.multi_playlist):
				if pl_to_id(i) in pctl.gen_codes:
					code = pctl.gen_codes[pl_to_id(i)]
					try:
						if check_auto_update_okay(code, pl=i):
							if not pl_is_locked(i):
								logging.info("Reloading smart playlist: " + plist.title)
								regenerate_playlist(i, silent=True)
								time.sleep(0.02)
					except Exception:
						logging.exception("Failed to handle playlist")

			tree_view_box.clear_all()

		if tauon.worker_save_state and \
				not gui.pl_pulse and \
				not loading_in_progress and \
				not to_scan and not after_scan and \
				not plex.scanning and \
				not jellyfin.scanning and \
				not cm_clean_db and \
				not lastfm.scanning_friends and \
				not move_in_progress and \
				(gui.lowered or not window_is_focused() or not gui.mouse_in_window):
			save_state()
			cue_list.clear()
			tauon.worker_save_state = False

		# Folder moving
		if len(move_jobs) > 0:
			gui.update += 1
			move_in_progress = True
			job = move_jobs[0]
			del move_jobs[0]

			if job[0].strip("\\/") == job[1].strip("\\/"):
				show_message(_("Folder copy error."), _("The target and source are the same."), mode="info")
				gui.update += 1
				move_in_progress = False
				continue

			try:
				shutil.copytree(job[0], job[1])
			except Exception:
				logging.exception("Failed to copy directory")
				move_in_progress = False
				gui.update += 1
				show_message(_("The folder copy has failed!"), _("Some files may have been written."), mode="warning")
				continue

			if job[2] == True:
				try:
					shutil.rmtree(job[0])

				except Exception:
					logging.exception("Failed to delete directory")
					show_message(_("Something has gone horribly wrong!"), _("Could not delete {name}").format(name=job[0]), mode="error")
					gui.update += 1
					move_in_progress = False
					return

				show_message(_("Folder move complete."), _("Folder name: {name}").format(name=job[3]), mode="done")
			else:
				show_message(_("Folder copy complete."), _("Folder name: {name}").format(name=job[3]), mode="done")

			move_in_progress = False
			load_orders.append(job[4])
			gui.update += 1

		# Clean database
		if cm_clean_db is True:
			items_removed = 0

			# old_db = copy.deepcopy(pctl.master_library)
			to_got = 0
			to_get = len(pctl.master_library)
			search_over.results.clear()

			keys = set(pctl.master_library.keys())
			for index in keys:
				time.sleep(0.0001)
				track = pctl.master_library[index]
				to_got += 1

				if to_got % 100 == 0:
					gui.update = 1

				if not prefs.remove_network_tracks and track.file_ext == "SPTY":

					for playlist in pctl.multi_playlist:
						if index in playlist.playlist_ids:
							break
					else:
						pctl.purge_track(index)
						items_removed += 1

					continue

				if (prefs.remove_network_tracks is False and not track.is_network and not os.path.isfile(
						track.fullpath)) or \
						(prefs.remove_network_tracks is True and track.is_network):

					if track.is_network and track.file_ext == "SPTY":
						continue

					pctl.purge_track(index)
					items_removed += 1

			cm_clean_db = False
			show_message(
				_("Cleaning complete."),
				_("{N} items were removed from the database.").format(N=str(items_removed)), mode="done")
			if album_mode:
				reload_albums(True)
			if gui.combo_mode:
				reload_albums()

			gui.update = 1
			gui.pl_update = 1
			pctl.notify_change()

			search_dia_string_cache.clear()
			search_string_cache.clear()
			search_over.results.clear()

			pctl.notify_change()

		# FOLDER ENC
		if transcode_list:

			try:
				transcode_state = ""
				gui.update += 1

				folder_items = transcode_list[0]

				ref_track_object = pctl.master_library[folder_items[0]]
				ref_album = ref_track_object.album

				# Generate a folder name based on artist and album of first track in batch
				folder_name = encode_folder_name(ref_track_object)

				# If folder contains tracks from multiple albums, use original folder name instead
				for item in folder_items:
					test_object = pctl.master_library[item]
					if test_object.album != ref_album:
						folder_name = ref_track_object.parent_folder_name
						break

				logging.info("Transcoding folder: " + folder_name)

				# Remove any existing matching folder
				if (prefs.encoder_output / folder_name).is_dir():
					shutil.rmtree(prefs.encoder_output / folder_name)

				# Create new empty folder to output tracks to
				(prefs.encoder_output / folder_name).mkdir(parents=True)

				full_wav_out_p = prefs.encoder_output / "output.wav"
				full_target_out_p = prefs.encoder_output / ("output." + prefs.transcode_codec)
				if full_wav_out_p.is_file():
					full_wav_out_p.unlink()
				if full_target_out_p.is_file():
					full_target_out_p.unlink()

				cache_dir = tmp_cache_dir()
				if not os.path.isdir(cache_dir):
					os.makedirs(cache_dir)

				if prefs.transcode_codec in ("opus", "ogg", "flac", "mp3"):
					global core_use
					cores = os.cpu_count()

					total = len(folder_items)
					gui.transcoding_batch_total = total
					gui.transcoding_bach_done = 0
					dones = []

					q = 0
					while True:
						if core_use < cores and q < len(folder_items):
							agg = [[folder_items[q], folder_name]]
							if agg not in dones:
								core_use += 1
								dones.append(agg)
								loaderThread = threading.Thread(target=transcode_single, args=agg)
								loaderThread.daemon = True
								loaderThread.start()

							q += 1
							gui.update += 1
						time.sleep(0.05)
						if gui.tc_cancel:
							while core_use > 0:
								time.sleep(1)
							break
						if q == len(folder_items) and core_use == 0:
							gui.update += 1
							break

				else:
					logging.error("Codec error")

				output_dir = prefs.encoder_output / folder_name
				if prefs.transcode_inplace:
					try:
						output_dir.unlink()
					except Exception:
						logging.exception("Encode folder not removed")
					reload_metadata(folder_items[0])
				else:
					album_art_gen.save_thumb(pctl.get_track(folder_items[0]), (1080, 1080), str(output_dir / "cover"))

				#logging.info(transcode_list[0])

				del transcode_list[0]
				transcode_state = ""
				gui.update += 1

			except Exception:
				logging.exception("Transcode failed")
				transcode_state = "Transcode Error"
				time.sleep(0.2)
				show_message(_("Transcode failed."), _("An error was encountered."), mode="error")
				gui.update += 1
				time.sleep(0.1)
				del transcode_list[0]

			if len(transcode_list) == 0:
				if gui.tc_cancel:
					gui.tc_cancel = False
					show_message(
						_("The transcode was canceled before completion."),
						_("Incomplete files will remain."),
						mode="warning")
				else:
					line = _("Press F9 to show output.")
					if prefs.transcode_codec == "flac":
						line = _("Note that any associated output picture is a thumbnail and not an exact copy.")
					if not gui.sync_progress:
						if not gui.message_box:
							show_message(_("Encoding complete."), line, mode="done")
						if system == "Linux" and de_notify_support:
							g_tc_notify.show()

		if to_scan:
			while to_scan:
				track = to_scan[0]
				star = star_store.full_get(track)
				star_store.remove(track)
				pctl.master_library[track] = tag_scan(pctl.master_library[track])
				star_store.merge(track, star)
				lastfm.sync_pull_love(pctl.master_library[track])
				del to_scan[0]
				gui.update += 1
			album_artist_dict.clear()
			pctl.notify_change()
			gui.pl_update += 1

		if loaderCommandReady is True:
			for order in load_orders:
				if order.stage == 1:
					if loaderCommand == LC_Folder:
						to_get = 0
						to_got = 0
						loaded_pathes_cache, loaded_cue_cache = cache_paths()
						# pre_get(order.target)
						if order.force_scan:
							gets(order.target, force_scan=True)
						else:
							gets(order.target)
					elif loaderCommand == LC_File:
						loaded_pathes_cache, loaded_cue_cache = cache_paths()
						add_file(order.target)

					if gui.im_cancel:
						gui.im_cancel = False
						to_get = 0
						to_got = 0
						load_orders.clear()
						added = []
						loaderCommand = LC_Done
						loaderCommandReady = False
						break

					loaderCommand = LC_Done
					#logging.info("LOAD ORDER")
					order.tracks = added

					# Double check for cue dupes
					for i in reversed(range(len(order.tracks))):
						if pctl.master_library[order.tracks[i]].fullpath in cue_list:
							if pctl.master_library[order.tracks[i]].is_cue is False:
								del order.tracks[i]

					added = []
					order.stage = 2
					loaderCommandReady = False
					#logging.info("DONE LOADING")
					break


album_info_cache = {}
perfs = []
album_info_cache_key = (-1, -1)


def get_album_info(position, pl: int | None = None):

	playlist = default_playlist
	if pl is not None:
		playlist = pctl.multi_playlist[pl].playlist_ids

	global album_info_cache_key

	if album_info_cache_key != (pctl.selected_in_playlist, pctl.playing_object()):  # Premature optimisation?
		album_info_cache.clear()
		album_info_cache_key = (pctl.selected_in_playlist, pctl.playing_object())

	if position in album_info_cache:
		return album_info_cache[position]

	if album_dex and album_mode and (pl is None or pl == pctl.active_playlist_viewing):
		dex = album_dex
	else:
		dex = reload_albums(custom_list=playlist)

	end = len(playlist)
	start = 0

	for i, p in enumerate(reversed(dex)):
		if p <= position:
			start = p
			break
		end = p

	album = list(range(start, end))

	playing = 0
	select = False

	if pctl.selected_in_playlist in album:
		select = True

	if len(pctl.track_queue) > 0 and p < len(playlist):
		if pctl.track_queue[pctl.queue_step] in playlist[start:end]:
			playing = 1

	album_info_cache[position] = playing, album, select
	return playing, album, select


tauon.get_album_info = get_album_info


def get_folder_list(index: int):
	playlist = []

	for item in default_playlist:
		if pctl.master_library[item].parent_folder_name == pctl.master_library[index].parent_folder_name and \
				pctl.master_library[item].album == pctl.master_library[index].album:
			playlist.append(item)
	return list(set(playlist))


def gal_jump_select(up=False, num=1):

	old_selected = pctl.selected_in_playlist
	old_num = num

	if not default_playlist:
		return

	on = pctl.selected_in_playlist
	if on > len(default_playlist) - 1:
		on = 0
		pctl.selected_in_playlist = 0

	if up is False:

		while num > 0:
			while pctl.master_library[
				default_playlist[on]].parent_folder_name == pctl.master_library[
				default_playlist[pctl.selected_in_playlist]].parent_folder_name:
				on += 1

				if on > len(default_playlist) - 1:
					pctl.selected_in_playlist = old_selected
					return

			pctl.selected_in_playlist = on
			num -= 1
	else:

		if num > 1:
			if pctl.selected_in_playlist > len(default_playlist) - 1:
				pctl.selected_in_playlist = old_selected
				return

			alb = get_album_info(pctl.selected_in_playlist)
			if alb[1][0] in album_dex[:num]:
				pctl.selected_in_playlist = old_selected
				return

		while num > 0:
			alb = get_album_info(pctl.selected_in_playlist)

			if alb[1][0] > -1:
				on = alb[1][0] - 1

			pctl.selected_in_playlist = max(get_album_info(on)[1][0], 0)
			num -= 1


power_tag_colours = ColourGenCache(0.5, 0.8)




gui.pt_on = Timer()
gui.pt_off = Timer()
gui.pt = 0


def gen_power2():
	tags = {}  # [tag name]: (first position, number of times we saw it)
	tag_list = []

	last = "a"
	noise = 0

	def key(tag):
		return tags[tag][1]

	for position in album_dex:

		index = default_playlist[position]
		track = pctl.get_track(index)

		crumbs = track.parent_folder_path.split("/")

		for i, b in enumerate(crumbs):

			if i > 0 and (track.artist in b and track.artist):
				tag = crumbs[i - 1]

				if tag != last:
					noise += 1
				last = tag

				if tag in tags:
					tags[tag][1] += 1
				else:
					tags[tag] = [position, 1, "/".join(crumbs[:i])]
					tag_list.append(tag)
				break

	if noise > len(album_dex) / 2:
		#logging.info("Playlist is too noisy for power bar.")
		return []

	tag_list_sort = sorted(tag_list, key=key, reverse=True)

	max_tags = round((window_size[1] - gui.panelY - gui.panelBY - 10) // 30 * gui.scale)

	tag_list_sort = tag_list_sort[:max_tags]

	for i in reversed(range(len(tag_list))):
		if tag_list[i] not in tag_list_sort:
			del tag_list[i]

	h = []

	for tag in tag_list:

		if tags[tag][1] > 2:
			t = PowerTag()
			t.path = tags[tag][2]
			t.name = tag.upper()
			t.position = tags[tag][0]
			h.append(t)

	cc = random.random()
	cj = 0.03
	if len(h) < 5:
		cj = 0.11

	cj = 0.5 / max(len(h), 2)

	for item in h:
		item.colour = hsl_to_rgb(cc, 0.8, 0.7)
		cc += cj

	return h


def reload_albums(quiet: bool = False, return_playlist: int = -1, custom_list=None) -> list[int] | None:
	global album_dex
	global update_layout
	global old_album_pos

	if cm_clean_db:
		# Doing reload while things are being removed may cause crash
		return None

	dex = []
	current_folder = ""
	current_album = ""
	current_artist = ""
	current_date = ""
	current_title = ""

	if custom_list is not None:
		playlist = custom_list
	else:
		target_pl_no = pctl.active_playlist_viewing
		if return_playlist > -1:
			target_pl_no = return_playlist

		playlist = pctl.multi_playlist[target_pl_no].playlist_ids

	for i in range(len(playlist)):
		tr = pctl.master_library[playlist[i]]

		split = False
		if i == 0:
			split = True
		elif tr.parent_folder_path != current_folder and tr.date and tr.date != current_date:
			split = True
		elif prefs.gallery_combine_disc and "Disc" in tr.album and "Disc" in current_album and tr.album.split("Disc")[0].rstrip(" ") == current_album.split("Disc")[0].rstrip(" "):
			split = False
		elif prefs.gallery_combine_disc and "CD" in tr.album and "CD" in current_album and tr.album.split("CD")[0].rstrip() == current_album.split("CD")[0].rstrip():
			split = False
		elif prefs.gallery_combine_disc and "cd" in tr.album and "cd" in current_album and tr.album.split("cd")[0].rstrip() == current_album.split("cd")[0].rstrip():
			split = False
		elif tr.album and tr.album == current_album and prefs.gallery_combine_disc:
			split = False
		elif tr.parent_folder_path != current_folder or current_title != tr.parent_folder_name:
			split = True

		if split:
			dex.append(i)
			current_folder = tr.parent_folder_path
			current_title = tr.parent_folder_name
			current_album = tr.album
			current_date = tr.date
			current_artist = tr.artist

	if return_playlist > -1 or custom_list:
		return dex

	album_dex = dex
	album_info_cache.clear()
	gui.update += 2
	gui.pl_update = 1
	update_layout = True

	if not quiet:
		goto_album(pctl.playlist_playing_position)

	# Generate POWER BAR
	gui.power_bar = gen_power2()
	gui.pt = 0


tauon.reload_albums = reload_albums

# ------------------------------------------------------------------------------------
# WEBSERVER
if prefs.enable_web is True:
	webThread = threading.Thread(
		target=webserve, args=[pctl, prefs, gui, album_art_gen, str(install_directory), strings, tauon])
	webThread.daemon = True
	webThread.start()

ctlThread = threading.Thread(target=controller, args=[tauon])
ctlThread.daemon = True
ctlThread.start()

if prefs.enable_remote:
	tauon.start_remote()
	tauon.remote_limited = False


# --------------------------------------------------------------

def star_line_toggle(mode: int= 0) -> bool | None:
	if mode == 1:
		return gui.star_mode == "line"

	if gui.star_mode == "line":
		gui.star_mode = "none"
	else:
		gui.star_mode = "line"

	gui.show_ratings = False

	gui.update += 1
	gui.pl_update = 1
	return None


def star_toggle(mode: int = 0) -> bool | None:
	if gui.show_ratings:
		if mode == 1:
			return prefs.rating_playtime_stars
		prefs.rating_playtime_stars ^= True

	else:
		if mode == 1:
			return gui.star_mode == "star"

		if gui.star_mode == "star":
			gui.star_mode = "none"
		else:
			gui.star_mode = "star"

	# gui.show_ratings = False
	gui.update += 1
	gui.pl_update = 1
	return None

def heart_toggle(mode: int = 0) -> bool | None:
	if mode == 1:
		return gui.show_hearts

	gui.show_hearts ^= True
	# gui.show_ratings = False

	gui.update += 1
	gui.pl_update = 1
	return None


def album_rating_toggle(mode: int = 0) -> bool | None:
	if mode == 1:
		return gui.show_album_ratings

	gui.show_album_ratings ^= True

	gui.update += 1
	gui.pl_update = 1
	return None


def rating_toggle(mode: int = 0) -> bool | None:
	if mode == 1:
		return gui.show_ratings

	gui.show_ratings ^= True

	if gui.show_ratings:
		# gui.show_hearts = False
		gui.star_mode = "none"
		prefs.rating_playtime_stars = True
		if not prefs.write_ratings:
			show_message(_("Note that ratings are stored in the local database and not written to tags."))

	gui.update += 1
	gui.pl_update = 1
	return None


def toggle_titlebar_line(mode: int = 0) -> bool | None:
	global update_title
	if mode == 1:
		return update_title

	line = window_title
	SDL_SetWindowTitle(t_window, line)
	update_title ^= True
	if update_title:
		update_title_do()
	return None


def toggle_meta_persists_stop(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.meta_persists_stop
	prefs.meta_persists_stop ^= True
	return None


def toggle_side_panel_layout(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.side_panel_layout == 1

	if prefs.side_panel_layout == 1:
		prefs.side_panel_layout = 0
	else:
		prefs.side_panel_layout = 1
	return None


def toggle_meta_shows_selected(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.meta_shows_selected_always
	prefs.meta_shows_selected_always ^= True
	return None


def scale1(mode: int = 0) -> bool | None:
	if mode == 1:
		if prefs.ui_scale == 1:
			return True
		return False

	prefs.ui_scale = 1
	pref_box.large_preset()

	if prefs.ui_scale != gui.scale:
		show_message(_("Change will be applied on restart."))
	return None


def scale125(mode: int = 0) -> bool | None:
	if mode == 1:
		if prefs.ui_scale == 1.25:
			return True
		return False
	return None

	prefs.ui_scale = 1.25
	pref_box.large_preset()

	if prefs.ui_scale != gui.scale:
		show_message(_("Change will be applied on restart."))
	return None


def toggle_use_tray(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.use_tray
	prefs.use_tray ^= True
	if not prefs.use_tray:
		prefs.min_to_tray = False
		gnome.hide_indicator()
	else:
		gnome.show_indicator()
	return None


def toggle_text_tray(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.tray_show_title
	prefs.tray_show_title ^= True
	pctl.notify_update()
	return None


def toggle_min_tray(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.min_to_tray
	prefs.min_to_tray ^= True
	return None


def scale2(mode: int = 0) -> bool | None:
	if mode == 1:
		if prefs.ui_scale == 2:
			return True
		return False

	prefs.ui_scale = 2
	pref_box.large_preset()

	if prefs.ui_scale != gui.scale:
		show_message(_("Change will be applied on restart."))
	return None


def toggle_borderless(mode: int = 0) -> bool | None:
	global draw_border
	global update_layout

	if mode == 1:
		return draw_border

	update_layout = True
	draw_border ^= True

	if draw_border:
		SDL_SetWindowBordered(t_window, False)
	else:
		SDL_SetWindowBordered(t_window, True)
	return None


def toggle_break(mode: int = 0) -> bool | None:
	global break_enable
	if mode == 1:
		return break_enable ^ True
	break_enable ^= True
	gui.pl_update = 1
	return None


def toggle_scroll(mode: int = 0) -> bool | None:
	global scroll_enable
	global update_layout

	if mode == 1:
		if scroll_enable:
			return False
		return True

	scroll_enable ^= True
	gui.pl_update = 1
	update_layout = True
	return None


def toggle_hide_bar(mode: int = 0) -> bool | None:
	if mode == 1:
		return gui.set_bar ^ True
	gui.update_layout()
	gui.set_bar ^= True
	show_message(_("Tip: You can also toggle this from a right-click context menu"))
	return None


def toggle_append_total_time(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.append_total_time
	prefs.append_total_time ^= True
	gui.pl_update = 1
	gui.update += 1
	return None


def toggle_append_date(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.append_date
	prefs.append_date ^= True
	gui.pl_update = 1
	gui.update += 1
	return None


def toggle_true_shuffle(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.true_shuffle
	prefs.true_shuffle ^= True
	return None


def toggle_auto_artist_dl(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.auto_dl_artist_data
	prefs.auto_dl_artist_data ^= True
	for artist, value in list(artist_list_box.thumb_cache.items()):
		if value is None:
			del artist_list_box.thumb_cache[artist]
	return None


def toggle_enable_web(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.enable_web

	prefs.enable_web ^= True

	if prefs.enable_web and not gui.web_running:
		webThread = threading.Thread(
			target=webserve, args=[pctl, prefs, gui, album_art_gen, str(install_directory), strings, tauon])
		webThread.daemon = True
		webThread.start()
		show_message(_("Web server starting"), _("External connections will be accepted."), mode="done")

	elif prefs.enable_web is False:
		if tauon.radio_server is not None:
			tauon.radio_server.shutdown()
			gui.web_running = False

		time.sleep(0.25)
	return None


def toggle_scrobble_mark(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.scrobble_mark
	prefs.scrobble_mark ^= True
	return None


def toggle_lfm_auto(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.auto_lfm
	prefs.auto_lfm ^= True
	if prefs.auto_lfm and not last_fm_enable:
		show_message(_("Optional module python-pylast not installed"), mode="warning")
		prefs.auto_lfm = False
	# if prefs.auto_lfm:
	#     lastfm.hold = False
	# else:
	#     lastfm.hold = True
	return None


def toggle_lb(mode: int = 0) -> bool | None:
	if mode == 1:
		return lb.enable
	if not lb.enable and not prefs.lb_token:
		show_message(_("Can't enable this if there's no token."), mode="warning")
		return None
	lb.enable ^= True
	return None


def toggle_maloja(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.maloja_enable
	if not prefs.maloja_url or not prefs.maloja_key:
		show_message(_("One or more fields is missing."), mode="warning")
		return None
	prefs.maloja_enable ^= True
	return None


def toggle_ex_del(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.auto_del_zip
	prefs.auto_del_zip ^= True
	# if prefs.auto_del_zip is True:
	#     show_message("Caution! This function deletes things!", mode='info', "This could result in data loss if the process were to malfunction.")
	return None


def toggle_dl_mon(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.monitor_downloads
	prefs.monitor_downloads ^= True
	return None


def toggle_music_ex(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.extract_to_music
	prefs.extract_to_music ^= True
	return None


def toggle_extract(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.auto_extract
	prefs.auto_extract ^= True
	if prefs.auto_extract is False:
		prefs.auto_del_zip = False
	return None


def toggle_top_tabs(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.tabs_on_top
	prefs.tabs_on_top ^= True
	return None


#def toggle_guitar_chords(mode: int = 0) -> bool | None:
#	if mode == 1:
#		return prefs.guitar_chords
#	prefs.guitar_chords ^= True
#	return None


# def toggle_auto_lyrics(mode: int = 0) -> bool | None:
#     if mode == 1:
#         return prefs.auto_lyrics
#     prefs.auto_lyrics ^= True


def switch_single(mode: int = 0) -> bool | None:
	if mode == 1:
		if prefs.transcode_mode == "single":
			return True
		return False
	prefs.transcode_mode = "single"
	return None


def switch_mp3(mode: int = 0) -> bool | None:
	if mode == 1:
		if prefs.transcode_codec == "mp3":
			return True
		return False
	prefs.transcode_codec = "mp3"
	return None


def switch_ogg(mode: int = 0) -> bool | None:
	if mode == 1:
		if prefs.transcode_codec == "ogg":
			return True
		return False
	prefs.transcode_codec = "ogg"
	return None


def switch_opus(mode: int = 0) -> bool | None:
	if mode == 1:
		if prefs.transcode_codec == "opus":
			return True
		return False
	prefs.transcode_codec = "opus"
	return None


def switch_opus_ogg(mode: int = 0) -> bool | None:
	if mode == 1:
		if prefs.transcode_opus_as:
			return True
		return False
	prefs.transcode_opus_as ^= True
	return None


def toggle_transcode_output(mode: int = 0) -> bool | None:
	if mode == 1:
		if prefs.transcode_inplace:
			return False
		return True
	prefs.transcode_inplace ^= True
	if prefs.transcode_inplace:
		transcode_icon.colour = [250, 20, 20, 255]
		show_message(
			_("DANGER! This will delete the original files. Keeping a backup is recommended in case of malfunction."),
			_("For safety, this setting will default to off. Embedded thumbnails are not kept so you may want to extract them first."),
			mode="warning")
	else:
		transcode_icon.colour = [239, 74, 157, 255]
	return None


def toggle_transcode_inplace(mode: int = 0) -> bool | None:
	if mode == 1:
		if prefs.transcode_inplace:
			return True
		return False

	if gui.sync_progress:
		prefs.transcode_inplace = False
		return None

	prefs.transcode_inplace ^= True
	if prefs.transcode_inplace:
		transcode_icon.colour = [250, 20, 20, 255]
		show_message(
			_("DANGER! This will delete the original files. Keeping a backup is recommended in case of malfunction."),
			_("For safety, this setting will reset on restart. Embedded thumbnails are not kept so you may want to extract them first."),
			mode="warning")
	else:
		transcode_icon.colour = [239, 74, 157, 255]
	return None


def switch_flac(mode: int = 0) -> bool | None:
	if mode == 1:
		if prefs.transcode_codec == "flac":
			return True
		return False
	prefs.transcode_codec = "flac"
	return None


def toggle_sbt(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.prefer_bottom_title
	prefs.prefer_bottom_title ^= True
	return None


def toggle_bba(mode: int = 0) -> bool | None:
	if mode == 1:
		return gui.bb_show_art
	gui.bb_show_art ^= True
	gui.update_layout()
	return None


def toggle_use_title(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.use_title
	prefs.use_title ^= True
	return None


def switch_rg_off(mode: int = 0) -> bool | None:
	if mode == 1:
		return True if prefs.replay_gain == 0 else False
	prefs.replay_gain = 0
	return None


def switch_rg_track(mode: int = 0) -> bool | None:
	if mode == 1:
		return True if prefs.replay_gain == 1 else False
	prefs.replay_gain = 0 if prefs.replay_gain == 1 else 1
	# prefs.replay_gain = 1
	return None


def switch_rg_album(mode: int = 0) -> bool | None:
	if mode == 1:
		return True if prefs.replay_gain == 2 else False
	prefs.replay_gain = 0 if prefs.replay_gain == 2 else 2
	return None


def switch_rg_auto(mode: int = 0) -> bool | None:
	if mode == 1:
		return True if prefs.replay_gain == 3 else False
	prefs.replay_gain = 0 if prefs.replay_gain == 3 else 3
	return None


def toggle_jump_crossfade(mode: int = 0) -> bool | None:
	if mode == 1:
		return True if prefs.use_jump_crossfade else False
	prefs.use_jump_crossfade ^= True
	return None


def toggle_pause_fade(mode: int = 0) -> bool | None:
	if mode == 1:
		return True if prefs.use_pause_fade else False
	prefs.use_pause_fade ^= True
	return None


def toggle_transition_crossfade(mode: int = 0) -> bool | None:
	if mode == 1:
		return True if prefs.use_transition_crossfade else False
	prefs.use_transition_crossfade ^= True
	return None


def toggle_transition_gapless(mode: int = 0) -> bool | None:
	if mode == 1:
		return False if prefs.use_transition_crossfade else True
	prefs.use_transition_crossfade ^= True
	return None


def toggle_eq(mode: int = 0) -> bool | None:
	if mode == 1:
		return prefs.use_eq
	prefs.use_eq ^= True
	pctl.playerCommand = "seteq"
	pctl.playerCommandReady = True
	return None


key_shiftr_down = False
key_ctrl_down = False
key_rctrl_down = False
key_meta = False
key_ralt = False
key_lalt = False


def reload_backend() -> None:
	gui.backend_reloading = True
	logging.info("Reload backend...")
	wait = 0
	pre_state = pctl.stop(True)

	while pctl.playerCommandReady:
		time.sleep(0.01)
		wait += 1
		if wait > 20:
			break
	if tauon.thread_manager.player_lock.locked():
		try:
			tauon.thread_manager.player_lock.release()
		except RuntimeError as e:
			if str(e) == "release unlocked lock":
				logging.error("RuntimeError: Attempted to release already unlocked player_lock")
			else:
				logging.exception("Unknown RuntimeError trying to release player_lock")
		except Exception:
			logging.exception("Unknown error trying to release player_lock")

	pctl.playerCommand = "unload"
	pctl.playerCommandReady = True

	wait = 0
	while pctl.playerCommand != "done":
		time.sleep(0.01)
		wait += 1
		if wait > 200:
			break

	tauon.thread_manager.ready_playback()

	if pre_state == 1:
		pctl.revert()
	gui.backend_reloading = False



def gen_chart() -> None:
	try:

		topchart = t_topchart.TopChart(tauon, album_art_gen)

		tracks = []

		source_tracks = pctl.multi_playlist[pctl.active_playlist_viewing].playlist_ids

		if prefs.topchart_sorts_played:
			source_tracks = gen_folder_top(0, custom_list=source_tracks)
			dex = reload_albums(quiet=True, custom_list=source_tracks)
		else:
			dex = reload_albums(quiet=True, return_playlist=pctl.active_playlist_viewing)

		for item in dex:
			tracks.append(pctl.get_track(source_tracks[item]))

		cascade = False
		if prefs.chart_cascade:
			cascade = (
				(prefs.chart_c1, prefs.chart_c2, prefs.chart_c3),
				(prefs.chart_d1, prefs.chart_d2, prefs.chart_d3))

		path = topchart.generate(
			tracks, prefs.chart_bg, prefs.chart_rows, prefs.chart_columns, prefs.chart_text,
			prefs.chart_font, prefs.chart_tile, cascade)

	except Exception:
		logging.exception("There was an error generating the chart")
		gui.generating_chart = False
		show_message(_("There was an error generating the chart"), _("Sorry!"), mode="error")
		return

	gui.generating_chart = False

	if path:
		open_file(path)
	else:
		show_message(_("There was an error generating the chart"), _("Sorry!"), mode="error")
		return

	show_message(_("Chart generated"), mode="done")

fields = Fields()

def update_playlist_call():
	gui.update + 2
	gui.pl_update = 2

pref_box = Over()

inc_arrow = asset_loader(scaled_asset_directory, loaded_asset_dc, "inc.png", True)
dec_arrow = asset_loader(scaled_asset_directory, loaded_asset_dc, "dec.png", True)
corner_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "corner.png", True)

# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
def pl_is_mut(pl: int) -> bool:
	id = pl_to_id(pl)
	if id is None:
		return False
	return not (pctl.gen_codes.get(id) and "self" not in pctl.gen_codes[id])

def clear_gen(id: int) -> None:
	del pctl.gen_codes[id]
	show_message(_("Okay, it's a normal playlist now."), mode="done")

def clear_gen_ask(id: int) -> None:
	if "jelly\"" in pctl.gen_codes.get(id, ""):
		return
	if "spl\"" in pctl.gen_codes.get(id, ""):
		return
	if "tpl\"" in pctl.gen_codes.get(id, ""):
		return
	if "tar\"" in pctl.gen_codes.get(id, ""):
		return
	if "tmix\"" in pctl.gen_codes.get(id, ""):
		return
	gui.message_box_confirm_callback = clear_gen
	gui.message_box_confirm_reference = (id,)
	show_message(_("You added tracks to a generator playlist. Do you want to clear the generator?"), mode="confirm")

top_panel = TopPanel()
bottom_bar1 = BottomBarType1()
bottom_bar_ao1 = BottomBarType_ao1()
mini_mode = MiniMode()
mini_mode2 = MiniMode2()
mini_mode3 = MiniMode3()

def set_mini_mode():
	if gui.fullscreen:
		return

	global mouse_down
	global mouse_up
	global old_window_position
	mouse_down = False
	mouse_up = False
	inp.mouse_click = False

	if gui.maximized:
		SDL_RestoreWindow(t_window)
		update_layout_do()

	if gui.mode < 3:
		old_window_position = get_window_position()

	if prefs.mini_mode_on_top:
		SDL_SetWindowAlwaysOnTop(t_window, True)

	gui.mode = 3
	gui.vis = 0
	gui.turbo = False
	gui.draw_vis4_top = False
	gui.level_update = False

	i_y = pointer(c_int(0))
	i_x = pointer(c_int(0))
	SDL_GetWindowPosition(t_window, i_x, i_y)
	gui.save_position = (i_x.contents.value, i_y.contents.value)

	mini_mode.was_borderless = draw_border
	SDL_SetWindowBordered(t_window, False)

	size = (350, 429)
	if prefs.mini_mode_mode == 1:
		size = (330, 330)
	if prefs.mini_mode_mode == 2:
		size = (420, 499)
	if prefs.mini_mode_mode == 3:
		size = (430, 430)
	if prefs.mini_mode_mode == 4:
		size = (330, 80)
	if prefs.mini_mode_mode == 5:
		size = (350, 545)
		style_overlay.flush()
		tauon.thread_manager.ready("style")

	if logical_size == window_size:
		size = (int(size[0] * gui.scale), int(size[1] * gui.scale))

	logical_size[0] = size[0]
	logical_size[1] = size[1]

	SDL_SetWindowMinimumSize(t_window, 100, 100)

	SDL_SetWindowResizable(t_window, False)
	SDL_SetWindowSize(t_window, logical_size[0], logical_size[1])

	if mini_mode.save_position:
		SDL_SetWindowPosition(t_window, mini_mode.save_position[0], mini_mode.save_position[1])

	i_x = pointer(c_int(0))
	i_y = pointer(c_int(0))
	SDL_GL_GetDrawableSize(t_window, i_x, i_y)
	window_size[0] = i_x.contents.value
	window_size[1] = i_y.contents.value

	gui.update += 3

restore_ignore_timer = Timer()
restore_ignore_timer.force_set(100)

def restore_full_mode():
	logging.info("RESTORE FULL")
	i_y = pointer(c_int(0))
	i_x = pointer(c_int(0))
	SDL_GetWindowPosition(t_window, i_x, i_y)
	mini_mode.save_position = [i_x.contents.value, i_y.contents.value]

	if not mini_mode.was_borderless:
		SDL_SetWindowBordered(t_window, True)

	logical_size[0] = gui.save_size[0]
	logical_size[1] = gui.save_size[1]

	SDL_SetWindowPosition(t_window, gui.save_position[0], gui.save_position[1])


	SDL_SetWindowResizable(t_window, True)
	SDL_SetWindowSize(t_window, logical_size[0], logical_size[1])
	SDL_SetWindowAlwaysOnTop(t_window, False)

	# if macos:
	#     SDL_SetWindowMinimumSize(t_window, 560, 330)
	# else:
	SDL_SetWindowMinimumSize(t_window, 560, 330)

	restore_ignore_timer.set()  # Hacky

	gui.mode = 1

	global mouse_down
	global mouse_up
	mouse_down = False
	mouse_up = False
	inp.mouse_click = False

	if gui.maximized:
		SDL_MaximizeWindow(t_window)
		time.sleep(0.05)
		SDL_PumpEvents()
		SDL_GetWindowSize(t_window, i_x, i_y)
		logical_size[0] = i_x.contents.value
		logical_size[1] = i_y.contents.value

		#logging.info(window_size)

	SDL_PumpEvents()
	SDL_GL_GetDrawableSize(t_window, i_x, i_y)
	window_size[0] = i_x.contents.value
	window_size[1] = i_y.contents.value

	gui.update_layout()
	if prefs.art_bg:
		tauon.thread_manager.ready("style")


def line_render(n_track: TrackClass, p_track: TrackClass, y, this_line_playing, album_fade, start_x, width, style=1, ry=None):
	timec = colours.bar_time
	titlec = colours.title_text
	indexc = colours.index_text
	artistc = colours.artist_text
	albumc = colours.album_text

	if this_line_playing is True:
		timec = colours.time_text
		titlec = colours.title_playing
		indexc = colours.index_playing
		artistc = colours.artist_playing
		albumc = colours.album_playing

	if n_track.found is False:
		timec = colours.playlist_text_missing
		titlec = colours.playlist_text_missing
		indexc = colours.playlist_text_missing
		artistc = colours.playlist_text_missing
		albumc = colours.playlist_text_missing

	artistoffset = 0
	indexLine = ""

	offset_font_extra = 0
	if gui.row_font_size > 14:
		offset_font_extra = 8

	# In windows (arial?) draws numbers too high (hack fix)
	num_y_offset = 0
	# if system == 'Windows':
	#    num_y_offset = 1

	if True or style == 1:

		# if not gui.rsp and not gui.combo_mode:
		#     width -= 10 * gui.scale

		dash = False
		if n_track.artist and colours.artist_text == colours.title_text:
			dash = True

		if n_track.title:

			line = track_number_process(n_track.track_number)

			indexLine = line

			if prefs.use_absolute_track_index and pctl.multi_playlist[pctl.active_playlist_viewing].hide_title:
				indexLine = str(p_track)
				if len(indexLine) > 3:
					indexLine += "  "

			line = ""

			if n_track.artist != "" and not dash:
				line0 = n_track.artist

				artistoffset = ddt.text(
					(start_x + 27 * gui.scale, y),
					line0,
					alpha_mod(artistc, album_fade),
					gui.row_font_size,
					int(width / 2))

				line = n_track.title
			else:
				line += n_track.title
		else:
			line = \
				os.path.splitext(n_track.filename)[
					0]

		if p_track >= len(default_playlist):
			gui.pl_update += 1
			return

		index = default_playlist[p_track]
		star_x = 0
		total = star_store.get(index)

		if gui.star_mode == "line" and total > 0 and pctl.master_library[index].length > 0:

			ratio = total / pctl.master_library[index].length
			if ratio > 0.55:
				star_x = int(ratio * 4 * gui.scale)
				star_x = min(star_x, 60 * gui.scale)
				sp = y - 0 - gui.playlist_text_offset + int(gui.playlist_row_height / 2)
				if gui.playlist_row_height > 17 * gui.scale:
					sp -= 1

				lh = 1
				if gui.scale != 1:
					lh = 2

				colour = colours.star_line
				if this_line_playing and colours.star_line_playing is not None:
					colour = colours.star_line_playing

				ddt.rect(
					[
						width + start_x - star_x - 45 * gui.scale - offset_font_extra,
						sp,
						star_x + 3 * gui.scale,
						lh],
					alpha_mod(colour, album_fade))

				star_x += 6 * gui.scale

		if gui.show_ratings:
			sx = round(width + start_x - round(40 * gui.scale) - offset_font_extra)
			sy = round(ry + (gui.playlist_row_height // 2) - round(7 * gui.scale))
			sx -= round(68 * gui.scale)

			draw_rating_widget(sx, sy, n_track)

			star_x += round(70 * gui.scale)

		if gui.star_mode == "star" and total > 0 and pctl.master_library[
			index].length != 0:

			sx = width + start_x - 40 * gui.scale - offset_font_extra
			sy = ry + (gui.playlist_row_height // 2) - (6 * gui.scale)
			# if gui.scale == 1.25:
			#     sy += 1
			playtime_stars = star_count(total, pctl.master_library[index].length) - 1

			sx2 = sx
			selected_star = -2
			rated_star = -1

			# if key_ctrl_down:

			c = 60
			d = 6

			colour = [70, 70, 70, 255]
			if colours.lm:
				colour = [90, 90, 90, 255]
			# colour = alpha_mod(indexc, album_fade)

			for count in range(8):

				if selected_star < count and playtime_stars < count and rated_star < count:
					break

				if count == 0:
					sx -= round(13 * gui.scale)
					star_x += round(13 * gui.scale)
				elif playtime_stars > 3:
					dd = round((13 - (playtime_stars - 3)) * gui.scale)
					sx -= dd
					star_x += dd
				else:
					sx -= round(13 * gui.scale)
					star_x += round(13 * gui.scale)

				# if playtime_stars > 4:
				#     colour = [c + d * count, c + d * count, c + d * count, 255]
				# if playtime_stars > 6: # and count < 1:
				#     colour = [230, 220, 60, 255]
				if gui.tracklist_bg_is_light:
					colour = alpha_blend([0, 0, 0, 200], ddt.text_background_colour)
				else:
					colour = alpha_blend([255, 255, 255, 50], ddt.text_background_colour)

				# if selected_star > -2:
				#     if selected_star >= count:
				#         colour = (220, 200, 60, 255)
				# else:
				#     if rated_star >= count:
				#         colour = (220, 200, 60, 255)

				star_pc_icon.render(sx, sy, colour)

		if gui.show_hearts:

			xxx = star_x

			count = 0
			spacing = 6 * gui.scale

			yy = ry + (gui.playlist_row_height // 2) - (5 * gui.scale)
			if gui.scale == 1.25:
				yy += 1
			if xxx > 0:
				xxx += 3 * gui.scale

			if love(False, index):
				count = 1

				x = width + start_x - 52 * gui.scale - offset_font_extra - xxx

				f_store.store(display_you_heart, (x, yy))

				star_x += 18 * gui.scale

			if "spotify-liked" in pctl.master_library[index].misc:

				x = width + start_x - 52 * gui.scale - offset_font_extra - (heart_row_icon.w + spacing) * count - xxx

				f_store.store(display_spot_heart, (x, yy))

				star_x += heart_row_icon.w + spacing + 2

			for name in pctl.master_library[index].lfm_friend_likes:

				# Limit to number of hears to display
				if gui.star_mode == "none":
					if count > 6:
						break
				elif count > 4:
					break

				x = width + start_x - 52 * gui.scale - offset_font_extra - (heart_row_icon.w + spacing) * count - xxx

				f_store.store(display_friend_heart, (x, yy, name))

				count += 1

				star_x += heart_row_icon.w + spacing + 2

		# Draw track number/index
		display_queue = False

		if pctl.force_queue:

			marks = []
			album_type = False
			for i, item in enumerate(pctl.force_queue):
				if item.track_id == n_track.index and item.position == p_track and item.playlist_id == pl_to_id(
						pctl.active_playlist_viewing):
					if item.type == 0:  # Only show mark if track type
						marks.append(i)
					# else:
					#     album_type = True
					#     marks.append(i)

			if marks:
				display_queue = True

		if display_queue:

			li = str(marks[0] + 1)
			if li == "1":
				li = "N"
				# if item.track_id == n_track.index and item.position == p_track and item.playlist_id == pctl.active_playlist_viewing
				if pctl.playing_ready() and n_track.index == pctl.track_queue[
					pctl.queue_step] and p_track == pctl.playlist_playing_position:
					li = "R"
				# if album_type:
				#     li = "A"

			# rect = (start_x + 3 * gui.scale, y - 1 * gui.scale, 5 * gui.scale, 5 * gui.scale)
			# ddt.rect_r(rect, [100, 200, 100, 255], True)
			if len(marks) > 1:
				li += " " + ("." * (len(marks) - 1))
				li = li[:5]

			# if album_type:
			#     li += "🠗"

			colour = [244, 200, 66, 255]
			if colours.lm:
				colour = [220, 40, 40, 255]

			ddt.text(
				(start_x + 5 * gui.scale, y, 2),
				li, colour, gui.row_font_size + 200 - 1)

		elif len(indexLine) > 2:

			ddt.text(
				(start_x + 5 * gui.scale, y, 2), indexLine,
				alpha_mod(indexc, album_fade), gui.row_font_size)
		else:

			ddt.text(
				(start_x, y), indexLine,
				alpha_mod(indexc, album_fade), gui.row_font_size)

		if dash and n_track.artist and n_track.title:
			line = n_track.artist + " - " + n_track.title

		ddt.text(
			(start_x + 33 * gui.scale + artistoffset, y),
			line,
			alpha_mod(titlec, album_fade),
			gui.row_font_size,
			width - 71 * gui.scale - artistoffset - star_x - 20 * gui.scale)

		line = get_display_time(n_track.length)

		ddt.text(
			(width + start_x - (round(36 * gui.scale) + offset_font_extra),
			y + num_y_offset, 0), line,
			alpha_mod(timec, album_fade), gui.row_font_size)

		f_store.recall_all()

pl_bg = None
if (user_directory / "bg.png").exists():
	pl_bg = LoadImageAsset(
		scaled_asset_directory=scaled_asset_directory, path=str(user_directory / "bg.png"), is_full_path=True)

playlist_render = StandardPlaylist()
art_box = ArtBox()
mini_lyrics_scroll = ScrollBox()
playlist_panel_scroll = ScrollBox()
artist_info_scroll = ScrollBox()
device_scroll = ScrollBox()
artist_list_scroll = ScrollBox()
gallery_scroll = ScrollBox()
tree_view_scroll = ScrollBox()
radio_view_scroll = ScrollBox()
radiobox = RadioBox()
tauon.radiobox = radiobox
tauon.dummy_track = radiobox.dummy_track

# def visit_radio_site_show_test(p):
# 	return "website_url" in prefs.radio_urls[p] and prefs.radio_urls[p]["website_url"]
#

def visit_radio_site_deco(item):
	if "website_url" in item and item["website_url"]:
		return [colours.menu_text, colours.menu_background, None]
	return [colours.menu_text_disabled, colours.menu_background, None]

def visit_radio_station_site_deco(item):
	return visit_radio_site_deco(item[1])

def visit_radio_site(item):
	if "website_url" in item and item["website_url"]:
		webbrowser.open(item["website_url"], new=2, autoraise=True)

def visit_radio_station(item):
	visit_radio_site(item[1])

def radio_saved_panel_test(_):
	return radiobox.tab == 0

def save_to_radios(item):
	pctl.radio_playlists[pctl.radio_playlist_viewing]["items"].append(item)
	toast(_("Added station to: ") + pctl.radio_playlists[pctl.radio_playlist_viewing]["name"])

radio_entry_menu.add(MenuItem(_("Visit Website"), visit_radio_site, visit_radio_site_deco, pass_ref=True, pass_ref_deco=True))
radio_entry_menu.add(MenuItem(_("Save"), save_to_radios, pass_ref=True))

rename_playlist_box = RenamePlaylistBox()
playlist_box = PlaylistBox()

def create_artist_pl(artist: str, replace: bool = False):
	source_pl = pctl.active_playlist_viewing
	this_pl = pctl.active_playlist_viewing

	if pctl.multi_playlist[source_pl].parent_playlist_id:
		if pctl.multi_playlist[source_pl].title.startswith("Artist:"):
			new = id_to_pl(pctl.multi_playlist[source_pl].parent_playlist_id)
			if new is None:
				# The original playlist is now gone
				pctl.multi_playlist[source_pl].parent_playlist_id = ""
			else:
				source_pl = new
				# replace = True

	playlist = []

	for item in pctl.multi_playlist[source_pl].playlist_ids:
		track = pctl.get_track(item)
		if track.artist == artist or track.album_artist == artist:
			playlist.append(item)

	if replace:
		pctl.multi_playlist[this_pl].playlist_ids[:] = playlist[:]
		pctl.multi_playlist[this_pl].title = _("Artist: ") + artist
		if album_mode:
			reload_albums()

		# Transfer playing track back to original playlist
		if pctl.multi_playlist[this_pl].parent_playlist_id:
			new = id_to_pl(pctl.multi_playlist[this_pl].parent_playlist_id)
			tr = pctl.playing_object()
			if new is not None and tr and pctl.active_playlist_playing == this_pl:
				if tr.index not in pctl.multi_playlist[this_pl].playlist_ids and tr.index in pctl.multi_playlist[source_pl].playlist_ids:
					logging.info("Transfer back playing")
					pctl.active_playlist_playing = source_pl
					pctl.playlist_playing_position = pctl.multi_playlist[source_pl].playlist_ids.index(tr.index)

		pctl.gen_codes[pl_to_id(this_pl)] = "s\"" + pctl.multi_playlist[source_pl].title + "\" a\"" + artist + "\""

	else:

		pctl.multi_playlist.append(
			pl_gen(
				title=_("Artist: ") + artist,
				playlist_ids=playlist,
				hide_title=False,
				parent=pl_to_id(source_pl)))

		pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[source_pl].title + "\" a\"" + artist + "\""

		switch_playlist(len(pctl.multi_playlist) - 1)

artist_list_menu.add(MenuItem(_("Filter to New Playlist"), create_artist_pl, pass_ref=True, icon=filter_icon))
artist_list_menu.add_sub(_("View..."), 140)

def aa_sort_alpha():
	prefs.artist_list_sort_mode = "alpha"
	artist_list_box.saves.clear()

def aa_sort_popular():
	prefs.artist_list_sort_mode = "popular"
	artist_list_box.saves.clear()

def aa_sort_play():
	prefs.artist_list_sort_mode = "play"
	artist_list_box.saves.clear()

def toggle_artist_list_style():
	if prefs.artist_list_style == 1:
		prefs.artist_list_style = 2
	else:
		prefs.artist_list_style = 1

def toggle_artist_list_threshold():
	if prefs.artist_list_threshold > 0:
		prefs.artist_list_threshold = 0
	else:
		prefs.artist_list_threshold = 4
	artist_list_box.saves.clear()

def toggle_artist_list_threshold_deco():
	if prefs.artist_list_threshold == 0:
		return [colours.menu_text, colours.menu_background, _("Filter Small Artists")]
	save = artist_list_box.saves.get(pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int)
	if save and save[5] == 0:
		return [colours.menu_text_disabled, colours.menu_background, _("Include All Artists")]
	return [colours.menu_text, colours.menu_background, _("Include All Artists")]

artist_list_menu.add_to_sub(0, MenuItem(_("Sort Alphabetically"), aa_sort_alpha))
artist_list_menu.add_to_sub(0, MenuItem(_("Sort by Popularity"), aa_sort_popular))
artist_list_menu.add_to_sub(0, MenuItem(_("Sort by Playtime"), aa_sort_play))
artist_list_menu.add_to_sub(0, MenuItem(_("Toggle Thumbnails"), toggle_artist_list_style))
artist_list_menu.add_to_sub(0, MenuItem(_("Toggle Filter"), toggle_artist_list_threshold, toggle_artist_list_threshold_deco))

def verify_discogs():
	return len(prefs.discogs_pat) == 40

def save_discogs_artist_thumb(artist, filepath):
	logging.info("Searching discogs for artist image...")

	# Make artist name url safe
	artist = artist.replace("/", "").replace("\\", "").replace(":", "")

	# Search for Discogs artist id
	url = "https://api.discogs.com/database/search"
	r = requests.get(url, params={"query": artist, "type": "artist", "token": prefs.discogs_pat}, headers={"User-Agent": t_agent}, timeout=10)
	id = r.json()["results"][0]["id"]

	# Search artist info, get images
	url = "https://api.discogs.com/artists/" + str(id)
	r = requests.get(url, headers={"User-Agent": t_agent}, params={"token": prefs.discogs_pat}, timeout=10)
	images = r.json()["images"]

	# Respect rate limit
	rate_remaining = r.headers["X-Discogs-Ratelimit-Remaining"]
	if int(rate_remaining) < 30:
		time.sleep(5)

	# Find a square image in list of images
	for image in images:
		if image["height"] == image["width"]:
			logging.info("Found square")
			url = image["uri"]
			break
	else:
		url = images[0]["uri"]

	response = urllib.request.urlopen(url, context=ssl_context)
	im = Image.open(response)

	width, height = im.size
	if width > height:
		delta = width - height
		left = int(delta / 2)
		upper = 0
		right = height + left
		lower = height
	else:
		delta = height - width
		left = 0
		upper = int(delta / 2)
		right = width
		lower = width + upper

	im = im.crop((left, upper, right, lower))
	im.save(filepath, "JPEG", quality=90)
	im.close()
	logging.info("Found artist image from Discogs")

def save_fanart_artist_thumb(mbid, filepath, preview=False):
	logging.info("Searching fanart.tv for image...")
	#logging.info("mbid is " + mbid)
	r = requests.get("https://webservice.fanart.tv/v3/music/" + mbid + "?api_key=" + prefs.fatvap, timeout=5)
	#logging.info(r.json())
	thumblink = r.json()["artistthumb"][0]["url"]
	if preview:
		thumblink = thumblink.replace("/fanart/music", "/preview/music")

	response = urllib.request.urlopen(thumblink, timeout=10, context=ssl_context)
	info = response.info()

	t = io.BytesIO()
	t.seek(0)
	t.write(response.read())
	l = 0
	t.seek(0, 2)
	l = t.tell()
	t.seek(0)

	if info.get_content_maintype() == "image" and l > 1000:
		f = open(filepath, "wb")
		f.write(t.read())
		f.close()

		if prefs.fanart_notify:
			prefs.fanart_notify = False
			show_message(
				_("Notice: Artist image sourced from fanart.tv"),
				_("They encourage you to contribute at {link}").format(link="https://fanart.tv"), mode="link")
		logging.info("Found artist thumbnail from fanart.tv")

artist_list_box = ArtistList()
tree_view_box = TreeView()

def queue_pause_deco():
	if pctl.pause_queue:
		return [colours.menu_text, colours.menu_background, _("Resume Queue")]
	return [colours.menu_text, colours.menu_background, _("Pause Queue")]

# def finish_current_deco():
#
#     colour = colours.menu_text
#     line = "Finish Playing Album"
#
#     if pctl.playing_object() is None:
#         colour = colours.menu_text_disabled
#     if pctl.force_queue and pctl.force_queue[0].album_stage == 1:
#         colour = colours.menu_text_disabled
#
#     return [colour, colours.menu_background, line]

queue_box = QueueBox()

def art_metadata_overlay(right, bottom, showc):
	if not showc:
		return

	padding = 6 * gui.scale

	if not key_shift_down:

		line = ""
		if showc[0] == 1:
			line += "E "
		elif showc[0] == 2:
			line += "N "
		else:
			line += "F "

		line += str(showc[2] + 1) + "/" + str(showc[1])

		y = bottom - 40 * gui.scale

		tag_width = ddt.get_text_w(line, 12) + 12 * gui.scale
		ddt.rect_a((right - (tag_width + padding), y), (tag_width, 18 * gui.scale), [8, 8, 8, 255])
		ddt.text(((right) - (6 * gui.scale + padding), y, 1), line, [200, 200, 200, 255], 12, bg=[30, 30, 30, 255])

	else:  # Extended metadata

		line = ""
		if showc[0] == 1:
			line += "Embedded"
		elif showc[0] == 2:
			line += "Network"
		else:
			line += "File"

		y = bottom - 76 * gui.scale

		tag_width = ddt.get_text_w(line, 12) + 12 * gui.scale
		ddt.rect_a((right - (tag_width + padding), y), (tag_width, 18 * gui.scale), [8, 8, 8, 255])
		ddt.text(((right) - (6 * gui.scale + padding), y, 1), line, [200, 200, 200, 255], 12, bg=[30, 30, 30, 255])

		y += 18 * gui.scale

		line = ""
		line += showc[4]
		line += " " + str(showc[3][0]) + "×" + str(showc[3][1])

		tag_width = ddt.get_text_w(line, 12) + 12 * gui.scale
		ddt.rect_a((right - (tag_width + padding), y), (tag_width, 18 * gui.scale), [8, 8, 8, 255])
		ddt.text(((right) - (6 * gui.scale + padding), y, 1), line, [200, 200, 200, 255], 12, bg=[30, 30, 30, 255])

		y += 18 * gui.scale

		line = ""
		line += str(showc[2] + 1) + "/" + str(showc[1])

		tag_width = ddt.get_text_w(line, 12) + 12 * gui.scale
		ddt.rect_a((right - (tag_width + padding), y), (tag_width, 18 * gui.scale), [8, 8, 8, 255])
		ddt.text(((right) - (6 * gui.scale + padding), y, 1), line, [200, 200, 200, 255], 12, bg=[30, 30, 30, 255])

meta_box = MetaBox()
artist_picture_render = PictureRender()
artist_preview_render = PictureRender()

# artist info box def
artist_info_box = ArtistInfoBox()

def artist_dl_deco():
	if artist_info_box.status == "Ready":
		return [colours.menu_text_disabled, colours.menu_background, None]
	return [colours.menu_text, colours.menu_background, None]

artist_info_menu.add(MenuItem(_("Download Artist Data"), artist_info_box.manual_dl, artist_dl_deco, show_test=test_artist_dl))
artist_info_menu.add(MenuItem(_("Clear Bio"), flush_artist_bio, pass_ref=True, show_test=test_shift))

radio_thumb_gen = RadioThumbGen()

def station_browse():
	radiobox.active = True
	radiobox.edit_mode = False
	radiobox.add_mode = False
	radiobox.center = True
	radiobox.tab = 1

def add_station():
	radiobox.active = True
	radiobox.edit_mode = True
	radiobox.add_mode = True
	radiobox.radio_field.text = ""
	radiobox.radio_field_title.text = ""
	radiobox.station_editing = None
	radiobox.center = True

def rename_station(item):
	station = item[1]
	radiobox.active = True
	radiobox.center = False
	radiobox.edit_mode = True
	radiobox.add_mode = False
	radiobox.radio_field.text = station["stream_url"]
	radiobox.radio_field_title.text = station.get("title", "")
	radiobox.station_editing = station

radio_context_menu.add(MenuItem(_("Edit..."), rename_station, pass_ref=True))
radio_context_menu.add(
	MenuItem(_("Visit Website"), visit_radio_station, visit_radio_station_site_deco, pass_ref=True, pass_ref_deco=True))

def remove_station(item):
	index = item[0]
	del pctl.radio_playlists[pctl.radio_playlist_viewing]["items"][index]

radio_context_menu.add(MenuItem(_("Remove"), remove_station, pass_ref=True))

radio_view = RadioView()
showcase = Showcase()
cctest = ColourPulse2()
view_box = ViewBox()
dl_mon = DLMon()
tauon.dl_mon = dl_mon

def dismiss_dl():
	dl_mon.ready.clear()
	dl_mon.done.update(dl_mon.watching)
	dl_mon.watching.clear()

dl_menu.add(MenuItem("Dismiss", dismiss_dl))

fader = Fader()
edge_playlist2 = EdgePulse2()
bottom_playlist2 = EdgePulse2()
gallery_pulse_top = EdgePulse2()
tab_pulse = EdgePulse()
lyric_side_top_pulse = EdgePulse2()
lyric_side_bottom_pulse = EdgePulse2()

def download_img(link: str, target_folder: str, track: TrackClass) -> None:
	try:
		response = urllib.request.urlopen(link, context=ssl_context)
		info = response.info()
		if info.get_content_maintype() == "image":
			if info.get_content_subtype() == "jpeg":
				save_target = os.path.join(target_dir, "image.jpg")
				with open(save_target, "wb") as f:
					f.write(response.read())
				# clear_img_cache()
				clear_track_image_cache(track)

			elif info.get_content_subtype() == "png":
				save_target = os.path.join(target_dir, "image.png")
				with open(save_target, "wb") as f:
					f.write(response.read())
				# clear_img_cache()
				clear_track_image_cache(track)
			else:
				show_message(_("Image types other than PNG or JPEG are currently not supported"), mode="warning")
		else:
			show_message(_("The link does not appear to refer to an image file."), mode="warning")
		gui.image_downloading = False

	except Exception as e:
		logging.exception("Image download failed")
		show_message(_("Image download failed."), str(e), mode="warning")
		gui.image_downloading = False

def display_you_heart(x: int, yy: int, just: int = 0) -> None:
	rect = [x - 1 * gui.scale, yy - 4 * gui.scale, 15 * gui.scale, 17 * gui.scale]
	gui.heart_fields.append(rect)
	fields.add(rect, update_playlist_call)
	if coll(rect) and not track_box:
		gui.pl_update += 1
		w = ddt.get_text_w(_("You"), 13)
		xx = (x - w) - 5 * gui.scale

		if just == 1:
			xx += w + 15 * gui.scale

		ty = yy - 28 * gui.scale
		tx = xx
		if ty < gui.panelY + 5 * gui.scale:
			ty = gui.panelY + 5 * gui.scale
			tx -= 20 * gui.scale

		# ddt.rect_r((xx - 1 * gui.scale, yy - 26 * gui.scale - 1 * gui.scale, w + 10 * gui.scale + 2 * gui.scale, 19 * gui.scale + 2 * gui.scale), [50, 50, 50, 255], True)
		ddt.rect((tx - 5 * gui.scale, ty, w + 20 * gui.scale, 24 * gui.scale), [15, 15, 15, 255])
		ddt.rect((tx - 5 * gui.scale, ty, w + 20 * gui.scale, 24 * gui.scale), [35, 35, 35, 255])
		ddt.text((tx + 5 * gui.scale, ty + 4 * gui.scale), _("You"), [250, 250, 250, 255], 13, bg=[15, 15, 15, 255])

	heart_row_icon.render(x, yy, [244, 100, 100, 255])

def display_spot_heart(x: int, yy: int, just: int = 0) -> None:
	rect = [x - 1 * gui.scale, yy - 4 * gui.scale, 15 * gui.scale, 17 * gui.scale]
	gui.heart_fields.append(rect)
	fields.add(rect, update_playlist_call)
	if coll(rect) and not track_box:
		gui.pl_update += 1
		w = ddt.get_text_w(_("Liked on Spotify"), 13)
		xx = (x - w) - 5 * gui.scale

		if just == 1:
			xx += w + 15 * gui.scale

		ty = yy - 28 * gui.scale
		tx = xx
		if ty < gui.panelY + 5 * gui.scale:
			ty = gui.panelY + 5 * gui.scale
			tx -= 20 * gui.scale

		# ddt.rect_r((xx - 1 * gui.scale, yy - 26 * gui.scale - 1 * gui.scale, w + 10 * gui.scale + 2 * gui.scale, 19 * gui.scale + 2 * gui.scale), [50, 50, 50, 255], True)
		ddt.rect((tx - 5 * gui.scale, ty, w + 20 * gui.scale, 24 * gui.scale), [15, 15, 15, 255])
		ddt.rect((tx - 5 * gui.scale, ty, w + 20 * gui.scale, 24 * gui.scale), [35, 35, 35, 255])
		ddt.text((tx + 5 * gui.scale, ty + 4 * gui.scale), _("Liked on Spotify"), [250, 250, 250, 255], 13, bg=[15, 15, 15, 255])

	heart_row_icon.render(x, yy, [100, 244, 100, 255])

def display_friend_heart(x: int, yy: int, name: str, just: int = 0) -> None:
	heart_row_icon.render(x, yy, heart_colours.get(name))

	rect = [x - 1, yy - 4, 15 * gui.scale, 17 * gui.scale]
	gui.heart_fields.append(rect)
	fields.add(rect, update_playlist_call)
	if coll(rect) and not track_box:
		gui.pl_update += 1
		w = ddt.get_text_w(name, 13)
		xx = (x - w) - 5 * gui.scale

		if just == 1:
			xx += w + 15 * gui.scale

		ty = yy - 28 * gui.scale
		tx = xx
		if ty < gui.panelY + 5 * gui.scale:
			ty = gui.panelY + 5 * gui.scale
			tx -= 20 * gui.scale

		ddt.rect((tx - 5 * gui.scale, ty, w + 20 * gui.scale, 24 * gui.scale), [15, 15, 15, 255])
		ddt.rect((tx - 5 * gui.scale, ty, w + 20 * gui.scale, 24 * gui.scale), [35, 35, 35, 255])
		ddt.text((tx + 5 * gui.scale, ty + 4 * gui.scale), name, [250, 250, 250, 255], 13, bg=[15, 15, 15, 255])

# Set SDL window drag areas
# if system != 'windows':

def hit_callback(win, point, data):
	x = point.contents.x / logical_size[0] * window_size[0]
	y = point.contents.y / logical_size[0] * window_size[0]

	# Special layout modes
	if gui.mode == 3:

		if key_shift_down or key_shiftr_down:
			return SDL_HITTEST_NORMAL

		# if prefs.mini_mode_mode == 5:
		#     return SDL_HITTEST_NORMAL

		if prefs.mini_mode_mode in (4, 5) and x > window_size[1] - 5 * gui.scale and y > window_size[1] - 12 * gui.scale:
			return SDL_HITTEST_NORMAL

		if y < gui.window_control_hit_area_h and x > window_size[
			0] - gui.window_control_hit_area_w:
			return SDL_HITTEST_NORMAL

		# Square modes
		y1 = window_size[0]
		# if prefs.mini_mode_mode == 5:
		#     y1 = window_size[1]
		y0 = 0
		if macos:
			y0 = round(35 * gui.scale)
		if window_size[0] == window_size[1]:
			y1 = window_size[1] - 79 * gui.scale
		if y0 < y < y1 and not search_over.active:
			return SDL_HITTEST_DRAGGABLE

		return SDL_HITTEST_NORMAL

	# Standard player mode
	if not gui.maximized:
		if y < 0 and x > window_size[0]:
			return SDL_HITTEST_RESIZE_TOPRIGHT

		if y < 0 and x < 1:
			return SDL_HITTEST_RESIZE_TOPLEFT

		# if draw_border and y < 3 * gui.scale and x < window_size[0] - 40 * gui.scale and not gui.maximized:
		#     return SDL_HITTEST_RESIZE_TOP

	if y < gui.panelY:

		if gui.top_bar_mode2:

			if y < gui.panelY - gui.panelY2:
				if prefs.left_window_control and x < 100 * gui.scale:
					return SDL_HITTEST_NORMAL

				if x > window_size[0] - 100 * gui.scale and y < 30 * gui.scale:
					return SDL_HITTEST_NORMAL
				return SDL_HITTEST_DRAGGABLE
			if top_panel.drag_zone_start_x > x or tab_menu.active:
				return SDL_HITTEST_NORMAL
			return SDL_HITTEST_DRAGGABLE

		if top_panel.drag_zone_start_x < x < window_size[0] - (gui.offset_extra + 5):

			if tab_menu.active or mouse_up or mouse_down:  # mouse up/down is workaround for Wayland
				return SDL_HITTEST_NORMAL

			if (prefs.left_window_control and x > window_size[0] - (100 * gui.scale) and (
					macos or system == "Windows" or msys)) or (not prefs.left_window_control and x > window_size[0] - (160 * gui.scale) and (
					macos or system == "Windows" or msys)):
				return SDL_HITTEST_NORMAL

			return SDL_HITTEST_DRAGGABLE

	if not gui.maximized:
		if x > window_size[0] - 20 * gui.scale and y > window_size[1] - 20 * gui.scale:
			return SDL_HITTEST_RESIZE_BOTTOMRIGHT
		if x < 5 and y > window_size[1] - 5:
			return SDL_HITTEST_RESIZE_BOTTOMLEFT
		if y > window_size[1] - 5 * gui.scale:
			return SDL_HITTEST_RESIZE_BOTTOM

		if x > window_size[0] - 3 * gui.scale and y > 20 * gui.scale:
			return SDL_HITTEST_RESIZE_RIGHT
		if x < 5 * gui.scale and y > 10 * gui.scale:
			return SDL_HITTEST_RESIZE_LEFT
		return SDL_HITTEST_NORMAL
	return SDL_HITTEST_NORMAL

c_hit_callback = SDL_HitTest(hit_callback)
SDL_SetWindowHitTest(t_window, c_hit_callback, 0)

# --------------------------------------------------------------------------------------------

# caster = threading.Thread(target=enc, args=[tauon])
# caster.daemon = True
# caster.start()

tauon.thread_manager.ready_playback()

try:
	tauon.thread_manager.d["caster"] = [lambda: x, [tauon], None]
except Exception:
	logging.exception("Failed to cast")

tauon.thread_manager.d["worker"] = [worker1, (), None]
tauon.thread_manager.d["search"] = [worker2, (), None]
tauon.thread_manager.d["gallery"] = [worker3, (), None]
tauon.thread_manager.d["style"] = [worker4, (), None]
tauon.thread_manager.d["radio-thumb"] = [radio_thumb_gen.loader, (), None]

tauon.thread_manager.ready("search")
tauon.thread_manager.ready("gallery")
tauon.thread_manager.ready("worker")

# thread = threading.Thread(target=worker1)
# thread.daemon = True
# thread.start()
# # #
# thread = threading.Thread(target=worker2)
# thread.daemon = True
# thread.start()
# # #
# thread = threading.Thread(target=worker3)
# thread.daemon = True
# thread.start()
#
# thread = threading.Thread(target=worker4)
# thread.daemon = True
# thread.start()


gui.playlist_view_length = int(((window_size[1] - gui.playlist_top) / 16) - 1)

ab_click = False
d_border = 1

update_layout = True

event = SDL_Event()

mouse_moved = False

power = 0

for item in sys.argv:
	if (os.path.isdir(item) or os.path.isfile(item) or "file://" in item) \
			and not item.endswith(".py") and not item.endswith("tauon.exe") and not item.endswith("tauonmb") \
			and not item.startswith("-"):
		open_uri(item)

sv = SDL_version()
SDL_GetVersion(sv)
sdl_version = sv.major * 100 + sv.minor * 10 + sv.patch
logging.info("Using SDL version: " + str(sv.major) + "." + str(sv.minor) + "." + str(sv.patch))

# C-ML
# if prefs.backend == 2:
#     logging.warning("Using GStreamer as fallback. Some functions disabled")
if prefs.backend == 0:
	show_message(_("ERROR: No backend found"), mode="error")

undo = Undo()

def reload_scale():
	auto_scale()

	scale = prefs.scale_want

	gui.scale = scale
	ddt.scale = gui.scale
	prime_fonts()
	ddt.clear_text_cache()
	scale_assets(scale_want=scale, force=True)
	img_slide_update_gall(album_mode_art_size)

	for item in WhiteModImageAsset.assets:
		item.reload()
	for item in LoadImageAsset.assets:
		item.reload()
	for menu in Menu.instances:
		menu.rescale()
	bottom_bar1.__init__()
	bottom_bar_ao1.__init__()
	top_panel.__init__()
	view_box.__init__(reload=True)
	queue_box.recalc()
	playlist_box.recalc()

def update_layout_do():
	if prefs.scale_want != gui.scale:
		reload_scale()

	w = window_size[0]
	h = window_size[1]

	if gui.switch_showcase_off:
		ddt.force_gray = False
		gui.switch_showcase_off = False
		exit_combo(restore=True)

	global draw_max_button
	if draw_max_button and prefs.force_hide_max_button:
		draw_max_button = False

	if gui.theme_name != prefs.theme_name:
		gui.reload_theme = True
		global theme
		theme = get_theme_number(prefs.theme_name)
		#logging.info("Config reload theme...")

	# Restore in case of error
	if gui.rspw < 30 * gui.scale:

		gui.rspw = 100 * gui.scale

	# Lock right side panel to full size if fully extended -----
	if prefs.side_panel_layout == 0 and not album_mode:
		max_w = round(
			((window_size[1] - gui.panelY - gui.panelBY - 17 * gui.scale) * gui.art_max_ratio_lock) + 17 * gui.scale)
		# 17 here is the art box inset value

		if not album_mode and gui.rspw > max_w - 12 * gui.scale and side_drag:
			gui.rsp_full_lock = True
	# ----------------------------------------------------------

	# Auto shrink left side panel --------------
	pl_width = window_size[0]
	pl_width_a = pl_width
	if gui.rsp:
		pl_width_a = pl_width - gui.rspw
		pl_width -= gui.rspw - 300 * gui.scale  # More sensitivity for compact with rsp for better visual balancing

	if pl_width < 900 * gui.scale and not gui.hide_tracklist_in_gallery:
		gui.lspw = 180 * gui.scale

		if pl_width < 700 * gui.scale:
			gui.lspw = 150 * gui.scale

		if prefs.left_panel_mode == "artist list" and prefs.artist_list_style == 1:
			gui.compact_artist_list = True
			gui.lspw = 75 * gui.scale
			if gui.force_side_on_drag:
				gui.lspw = 180 * gui.scale
	else:
		gui.lspw = 220 * gui.scale
		gui.compact_artist_list = False
		if prefs.left_panel_mode == "artist list":
			gui.lspw = 230 * gui.scale

	if gui.lsp and prefs.left_panel_mode == "folder view":
		gui.lspw = 260 * gui.scale
		max_insets = 0
		for item in tree_view_box.rows:
			max_insets = max(item[2], max_insets)

		p = (pl_width_a * 0.15) - round(200 * gui.scale)
		if gui.hide_tracklist_in_gallery:
			p = ((window_size[0] - gui.lspw) * 0.15) - round(170 * gui.scale)

		p = min(round(200 * gui.scale), p)
		if p > 0:
			gui.lspw += p
		if max_insets > 1:
			gui.lspw = max(gui.lspw, 260 * gui.scale + round(15 * gui.scale) * max_insets)

	# -----

	# Set bg art strength according to setting ----
	if prefs.art_bg_stronger == 3:
		prefs.art_bg_opacity = 29
	elif prefs.art_bg_stronger == 2:
		prefs.art_bg_opacity = 19
	else:
		prefs.art_bg_opacity = 10

	if prefs.bg_showcase_only:
		prefs.art_bg_opacity += 21

	# -----

	# Adjust for for compact window sizes ----
	if (prefs.always_art_header or (w < 600 * gui.scale and not gui.rsp and prefs.art_in_top_panel)) and not album_mode:
		gui.top_bar_mode2 = True
		gui.panelY = round(100 * gui.scale)
		gui.playlist_top = gui.panelY + (8 * gui.scale)
		gui.playlist_top_bk = gui.playlist_top

	else:
		gui.top_bar_mode2 = False
		gui.panelY = round(30 * gui.scale)
		gui.playlist_top = gui.panelY + (8 * gui.scale)
		gui.playlist_top_bk = gui.playlist_top

	gui.show_playlist = True
	if w < 750 * gui.scale and album_mode:
		gui.show_playlist = False

	# Set bio panel size according to setting
	if prefs.bio_large:
		gui.artist_panel_height = 320 * gui.scale
		if window_size[0] < 600 * gui.scale:
			gui.artist_panel_height = 200 * gui.scale

	else:
		gui.artist_panel_height = 200 * gui.scale
		if window_size[0] < 600 * gui.scale:
			gui.artist_panel_height = 150 * gui.scale

	# Trigger artist bio reload if panel size has changed
	if gui.artist_info_panel:
		if gui.last_artist_panel_height != gui.artist_panel_height:
			artist_info_box.get_data(artist_info_box.artist_on)
		gui.last_artist_panel_height = gui.artist_panel_height

	# prefs.art_bg_blur = 9
	# if prefs.bg_showcase_only:
	#     prefs.art_bg_blur = 15
	#
	# if w / h == 16 / 9:
	#     logging.info("YEP")
	# elif w / h < 16 / 9:
	#     logging.info("too low")
	# else:
	#     logging.info("too high")
	#logging.info((w, h))

	# input.mouse_click = False

	global renderer

	if prefs.spec2_colour_mode == 0:
		prefs.spec2_base = [10, 10, 100]
		prefs.spec2_multiply = [0.5, 1, 1]
	elif prefs.spec2_colour_mode == 1:
		prefs.spec2_base = [10, 10, 10]
		prefs.spec2_multiply = [2, 1.2, 5]
	# elif prefs.spec2_colour_mode == 2:
	#     prefs.spec2_base = [10, 100, 10]
	#     prefs.spec2_multiply = [1, -1, 0.4]

	gui.draw_vis4_top = False

	if gui.combo_mode and gui.showcase_mode and prefs.showcase_vis and gui.mode != 3 and prefs.backend == 4:
		gui.vis = 4
		gui.turbo = True
	elif gui.vis_want == 0:
		gui.turbo = False
		gui.vis = 0
	else:
		gui.vis = gui.vis_want
		if gui.vis > 0:
			gui.turbo = True

	# Disable vis when in compact view
	if gui.mode == 3 or gui.top_bar_mode2:  # or prefs.backend == 2:
		if not gui.combo_mode:
			gui.vis = 0
			gui.turbo = False

	if gui.mode == 1:
		if not gui.maximized and not gui.lowered and gui.mode != 3:
			gui.save_size[0] = logical_size[0]
			gui.save_size[1] = logical_size[1]

		bottom_bar1.update()

		# if system != 'windows':
		#     if draw_border:
		#         gui.panelY = 30 * gui.scale + 3 * gui.scale
		#         top_panel.ty = 3 * gui.scale
		#     else:
		#         gui.panelY = 30 * gui.scale
		#         top_panel.ty = 0

		if gui.set_bar and gui.set_mode:
			gui.playlist_top = gui.playlist_top_bk + gui.set_height - 6 * gui.scale
		else:
			gui.playlist_top = gui.playlist_top_bk

		if gui.artist_info_panel:
			gui.playlist_top += gui.artist_panel_height

		gui.offset_extra = 0
		if draw_border and not prefs.left_window_control:

			offset = 61 * gui.scale
			if not draw_min_button:
				offset -= 35 * gui.scale
			if draw_max_button:
				offset += 33 * gui.scale
			if gui.macstyle:
				offset = 24
				if draw_min_button:
					offset += 20
				if draw_max_button:
					offset += 20
				offset = round(offset * gui.scale)
			gui.offset_extra = offset

		global album_v_gap
		global album_h_gap
		global album_v_slide_value

		album_v_slide_value = round(50 * gui.scale)
		if gui.gallery_show_text:
			album_h_gap = 30 * gui.scale
			album_v_gap = 66 * gui.scale
		else:
			album_h_gap = 30 * gui.scale
			album_v_gap = 25 * gui.scale

		if prefs.thin_gallery_borders:

			if gui.gallery_show_text:
				album_h_gap = 20 * gui.scale
				album_v_gap = 55 * gui.scale
			else:
				album_h_gap = 17 * gui.scale
				album_v_gap = 15 * gui.scale

			album_v_slide_value = round(45 * gui.scale)

		if prefs.increase_gallery_row_spacing:
			album_v_gap = round(album_v_gap * 1.3)

		gui.gallery_scroll_field_left = window_size[0] - round(40 * gui.scale)

		# gui.spec_rect[0] = window_size[0] - gui.offset_extra - 90
		gui.spec1_rec.x = int(round(window_size[0] - gui.offset_extra - 90 * gui.scale))

		# gui.spec_x = window_size[0] - gui.offset_extra - 90

		gui.spec2_rec.x = int(round(window_size[0] - gui.spec2_rec.w - 10 * gui.scale - gui.offset_extra))

		gui.scroll_hide_box = (1, gui.panelY, 28 * gui.scale, window_size[1] - gui.panelBY - gui.panelY)

		# Tracklist row size and text positioning ---------------------------------
		gui.playlist_row_height = prefs.playlist_row_height
		gui.row_font_size = prefs.playlist_font_size  # 13

		gui.playlist_text_offset = round(gui.playlist_row_height * 0.55) + 4 - 13 * gui.scale

		if gui.scale != 1:
			real_font_px = ddt.f_dict[gui.row_font_size][2]
			# gui.playlist_text_offset = (round(gui.playlist_row_height - real_font_px) / 2) - ddt.get_y_offset("AbcD", gui.row_font_size, 100) + round(1.3 * gui.scale)

			if gui.scale < 1.3:
				gui.playlist_text_offset = round(((gui.playlist_row_height - real_font_px) / 2) - 1.9 * gui.scale)
			elif gui.scale < 1.5:
				gui.playlist_text_offset = round(((gui.playlist_row_height - real_font_px) / 2) - 1.3 * gui.scale)
			elif gui.scale < 1.75:
				gui.playlist_text_offset = round(((gui.playlist_row_height - real_font_px) / 2) - 1.1 * gui.scale)
			elif gui.scale < 2.3:
				gui.playlist_text_offset = round(((gui.playlist_row_height - real_font_px) / 2) - 1.5 * gui.scale)
			else:
				gui.playlist_text_offset = round(((gui.playlist_row_height - real_font_px) / 2) - 1.8 * gui.scale)

		gui.playlist_text_offset += prefs.tracklist_y_text_offset

		gui.pl_title_real_height = round(gui.playlist_row_height * 0.55) + 4 - 12

		# -------------------------------------------------------------------------
		gui.playlist_view_length = int(
			(window_size[1] - gui.panelBY - gui.playlist_top - 12 * gui.scale) // gui.playlist_row_height)

		box_r = gui.rspw / (window_size[1] - gui.panelBY - gui.panelY)

		if gui.art_aspect_ratio > 1.01:
			gui.art_unlock_ratio = True
			gui.art_max_ratio_lock = max(gui.art_aspect_ratio, gui.art_max_ratio_lock)


		#logging.info("Avaliabe: " + str(box_r))
		elif box_r <= 1:
			gui.art_unlock_ratio = False
			gui.art_max_ratio_lock = 1

		if side_drag and key_shift_down:
			gui.art_unlock_ratio = True
			gui.art_max_ratio_lock = 5

		gui.rspw = gui.pref_rspw
		if album_mode:
			gui.rspw = gui.pref_gallery_w

		# Limit the right side panel width to height of area
		if gui.rsp and prefs.side_panel_layout == 0:
			if album_mode:
				pass
			else:

				if not gui.art_unlock_ratio:

					if gui.rsp_full_lock and not side_drag:
						gui.rspw = window_size[0]

					gui.rspw = min(gui.rspw, window_size[1] - gui.panelY - gui.panelBY)

		# Determine how wide the playlist need to be
		gui.plw = window_size[0]
		gui.playlist_left = 0
		if gui.lsp:
			# if gui.plw > gui.lspw:
			gui.plw -= gui.lspw
			gui.playlist_left = gui.lspw
		if gui.rsp:
			gui.plw -= gui.rspw

		# Shrink side panel if playlist gets too small
		if window_size[0] > 100 and not gui.hide_tracklist_in_gallery:

			if gui.plw < 300:
				if gui.rsp:

					l = 0
					if gui.lsp:
						l = gui.lspw

					gui.rspw = max(window_size[0] - l - 300, 110)
					# if album_mode and window_size[0] > 750 * gui.scale:
					#     gui.pref_gallery_w = gui.rspw

		# Determine how wide the playlist need to be (again)
		gui.plw = window_size[0]
		gui.playlist_left = 0
		if gui.lsp:
			# if gui.plw > gui.lspw:
			gui.plw -= gui.lspw
			gui.playlist_left = gui.lspw
		if gui.rsp:
			gui.plw -= gui.rspw

		if window_size[0] < 630 * gui.scale:
			gui.compact_bar = True
		else:
			gui.compact_bar = False

		gui.pl_update = 1

		# Tracklist sizing ----------------------------------------------------
		left = gui.playlist_left
		width = gui.plw

		center_mode = True
		if gui.lsp or gui.rsp or gui.set_mode:
			center_mode = False

		if gui.set_mode and window_size[0] < 600:
			center_mode = False

		highlight_left = 0
		highlight_width = width

		inset_left = highlight_left + 23 * gui.scale
		inset_width = highlight_width - 32 * gui.scale

		if gui.lsp and not gui.rsp:
			inset_width -= 10 * gui.scale

		if gui.lsp:
			inset_left -= 10 * gui.scale
			inset_width += 10 * gui.scale

		if center_mode:
			if gui.set_mode:
				highlight_left = int(pow((window_size[0] / gui.scale * 0.005), 2) * gui.scale)
			else:
				highlight_left = int(pow((window_size[0] / gui.scale * 0.01), 2) * gui.scale)

			if window_size[0] < 600 * gui.scale:
				highlight_left = 3 * gui.scale

			highlight_width -= highlight_left * 2
			inset_left = highlight_left + 18 * gui.scale
			inset_width = highlight_width - 25 * gui.scale

		if window_size[0] < 600 and gui.lsp:
			inset_width = highlight_width - 18 * gui.scale

		gui.tracklist_center_mode = center_mode
		gui.tracklist_inset_left = inset_left
		gui.tracklist_inset_width = inset_width
		gui.tracklist_highlight_left = highlight_left
		gui.tracklist_highlight_width = highlight_width

		if album_mode and gui.hide_tracklist_in_gallery:
			gui.show_playlist = False
			gui.rspw = window_size[0] - 20 * gui.scale
			if gui.lsp:
				gui.rspw -= gui.lspw

		# --------------------------------------------------------------------

		if window_size[0] > gui.max_window_tex or window_size[1] > gui.max_window_tex:

			while window_size[0] > gui.max_window_tex:
				gui.max_window_tex += 1000
			while window_size[1] > gui.max_window_tex:
				gui.max_window_tex += 1000

			gui.tracklist_texture_rect = SDL_Rect(0, 0, gui.max_window_tex, gui.max_window_tex)

			SDL_DestroyTexture(gui.tracklist_texture)
			SDL_RenderClear(renderer)
			gui.tracklist_texture = SDL_CreateTexture(
				renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET,
				gui.max_window_tex,
				gui.max_window_tex)

			SDL_SetRenderTarget(renderer, gui.tracklist_texture)
			SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
			SDL_RenderClear(renderer)
			SDL_SetTextureBlendMode(gui.tracklist_texture, SDL_BLENDMODE_BLEND)

			# SDL_SetRenderTarget(renderer, gui.main_texture)
			# SDL_RenderClear(renderer)

			SDL_DestroyTexture(gui.main_texture)
			gui.main_texture = SDL_CreateTexture(
				renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET,
				gui.max_window_tex,
				gui.max_window_tex)
			SDL_SetTextureBlendMode(gui.main_texture, SDL_BLENDMODE_BLEND)
			SDL_SetRenderTarget(renderer, gui.main_texture)
			SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
			SDL_SetRenderTarget(renderer, gui.main_texture)
			SDL_RenderClear(renderer)

			SDL_DestroyTexture(gui.main_texture_overlay_temp)
			gui.main_texture_overlay_temp = SDL_CreateTexture(
				renderer, SDL_PIXELFORMAT_ARGB8888,
				SDL_TEXTUREACCESS_TARGET, gui.max_window_tex,
				gui.max_window_tex)
			SDL_SetTextureBlendMode(gui.main_texture_overlay_temp, SDL_BLENDMODE_BLEND)
			SDL_SetRenderTarget(renderer, gui.main_texture_overlay_temp)
			SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
			SDL_SetRenderTarget(renderer, gui.main_texture_overlay_temp)
			SDL_RenderClear(renderer)

		update_set()

	if prefs.art_bg:
		tauon.thread_manager.ready("style")

# SDL_RenderClear(renderer)
# SDL_RenderPresent(renderer)


# SDL_ShowWindow(t_window)

# Clear spectogram texture
SDL_SetRenderTarget(renderer, gui.spec2_tex)
SDL_RenderClear(renderer)
ddt.rect((0, 0, 1000, 1000), [7, 7, 7, 255])

SDL_SetRenderTarget(renderer, gui.spec1_tex)
SDL_RenderClear(renderer)
ddt.rect((0, 0, 1000, 1000), [7, 7, 7, 255])

SDL_SetRenderTarget(renderer, gui.spec_level_tex)
SDL_RenderClear(renderer)
ddt.rect((0, 0, 1000, 1000), [7, 7, 7, 255])

SDL_SetRenderTarget(renderer, None)


# SDL_RenderPresent(renderer)

# time.sleep(3)

gal_up = False
gal_down = False
gal_left = False
gal_right = False

get_sdl_input = GetSDLInput()

def window_is_focused() -> bool:
	"""Thread safe?"""
	if SDL_GetWindowFlags(t_window) & SDL_WINDOW_INPUT_FOCUS:
		return True
	return False


def save_state() -> None:
	if should_save_state:
		logging.info("Writing database to disk... ")
	else:
		logging.warning("Dev mode, not saving state... ")
		return

	# view_prefs['star-lines'] = star_lines
	view_prefs["update-title"] = update_title
	view_prefs["side-panel"] = prefs.prefer_side
	view_prefs["dim-art"] = prefs.dim_art
	#view_prefs['level-meter'] = gui.turbo
	# view_prefs['pl-follow'] = pl_follow
	view_prefs["scroll-enable"] = scroll_enable
	view_prefs["break-enable"] = break_enable
	# view_prefs['dd-index'] = dd_index
	view_prefs["append-date"] = prefs.append_date

	tauonplaylist_jar = []
	tauonqueueitem_jar = []
#	if db_version > 68:
	for v in pctl.multi_playlist:
#		logging.warning(f"Playlist: {v}")
		tauonplaylist_jar.append(v.__dict__)
	for v in pctl.force_queue:
#		logging.warning(f"Queue: {v}")
		tauonqueueitem_jar.append(v.__dict__)
#	else:
#		tauonplaylist_jar = pctl.multi_playlist
#		tauonqueueitem_jar = pctl.track_queue

	trackclass_jar = []
	for v in pctl.master_library.values():
		trackclass_jar.append(v.__dict__)

	save = [
		None,
		pctl.master_count,
		pctl.playlist_playing_position,
		pctl.active_playlist_viewing,
		pctl.playlist_view_position,
		tauonplaylist_jar, # pctl.multi_playlist, # list[TauonPlaylist]
		pctl.player_volume,
		pctl.track_queue,
		pctl.queue_step,
		default_playlist,
		None,  # pctl.playlist_playing_position,
		None,  # Was cue list
		"",  # radio_field.text,
		theme,
		folder_image_offsets,
		None,  # lfm_username,
		None,  # lfm_hash,
		latest_db_version,  # Used for upgrading
		view_prefs,
		gui.save_size,
		None,  # old side panel size
		0,  # save time (unused)
		gui.vis_want,  # gui.vis
		pctl.selected_in_playlist,
		album_mode_art_size,
		draw_border,
		prefs.enable_web,
		prefs.allow_remote,
		prefs.expose_web,
		prefs.enable_transcode,
		prefs.show_rym,
		None,  # was combo mode art size
		gui.maximized,
		prefs.prefer_bottom_title,
		gui.display_time_mode,
		prefs.transcode_mode,
		prefs.transcode_codec,
		prefs.transcode_bitrate,
		1,  # prefs.line_style,
		prefs.cache_gallery,
		prefs.playlist_font_size,
		prefs.use_title,
		gui.pl_st,
		None,  # gui.set_mode,
		None,
		prefs.playlist_row_height,
		prefs.show_wiki,
		prefs.auto_extract,
		prefs.colour_from_image,
		gui.set_bar,
		gui.gallery_show_text,
		gui.bb_show_art,
		False,  # Was show stars
		prefs.auto_lfm,
		prefs.scrobble_mark,
		prefs.replay_gain,
		True,  # Was radio lyrics
		prefs.show_gimage,
		prefs.end_setting,
		prefs.show_gen,
		[],  # was old radio urls
		prefs.auto_del_zip,
		gui.level_meter_colour_mode,
		prefs.ui_scale,
		prefs.show_lyrics_side,
		None, #prefs.last_device,
		album_mode,
		None,  # album_playlist_width
		prefs.transcode_opus_as,
		gui.star_mode,
		prefs.prefer_side,  # gui.rsp,
		gui.lsp,
		gui.rspw,
		gui.pref_gallery_w,
		gui.pref_rspw,
		gui.show_hearts,
		prefs.monitor_downloads,  # 76
		gui.artist_info_panel,  # 77
		prefs.extract_to_music,  # 78
		lb.enable,
		None,  # lb.key,
		rename_files.text,
		rename_folder.text,
		prefs.use_jump_crossfade,
		prefs.use_transition_crossfade,
		prefs.show_notifications,
		prefs.true_shuffle,
		gui.set_mode,
		None,  # prefs.show_queue, # 88
		None,  # prefs.show_transfer,
		tauonqueueitem_jar, # pctl.force_queue, # 90
		prefs.use_pause_fade,  # 91
		prefs.append_total_time,  # 92
		None,  # prefs.backend,
		pctl.album_shuffle_mode,
		pctl.album_repeat_mode,  # 95
		prefs.finish_current,  # Not used
		prefs.reload_state,  # 97
		None,  # prefs.reload_play_state,
		prefs.last_fm_token,
		prefs.last_fm_username,
		prefs.use_card_style,
		prefs.auto_lyrics,
		prefs.auto_lyrics_checked,
		prefs.show_side_art,
		prefs.window_opacity,
		prefs.gallery_single_click,
		prefs.tabs_on_top,
		prefs.showcase_vis,
		prefs.spec2_colour_mode,
		prefs.device_buffer,  # moved to config file
		prefs.use_eq,
		prefs.eq,
		prefs.bio_large,
		prefs.discord_show,
		prefs.min_to_tray,
		prefs.guitar_chords,
		None,  # prefs.playback_follow_cursor,
		prefs.art_bg,
		pctl.random_mode,
		pctl.repeat_mode,
		prefs.art_bg_stronger,
		prefs.art_bg_always_blur,
		prefs.failed_artists,
		prefs.artist_list,
		None,  # prefs.auto_sort,
		prefs.lyrics_enables,
		prefs.fanart_notify,
		prefs.bg_showcase_only,
		None,  # prefs.discogs_pat,
		prefs.mini_mode_mode,
		after_scan,
		gui.gallery_positions,
		prefs.chart_bg,
		prefs.left_panel_mode,
		gui.last_left_panel_mode,
		None, #prefs.gst_device,
		search_string_cache,
		search_dia_string_cache,
		pctl.gen_codes,
		gui.show_ratings,
		gui.show_album_ratings,
		prefs.radio_urls,
		gui.showcase_mode,  # gui.combo_mode,
		top_panel.prime_tab,
		top_panel.prime_side,
		prefs.sync_playlist,
		prefs.spot_client,
		prefs.spot_secret,
		prefs.show_band,
		prefs.download_playlist,
		tauon.spot_ctl.cache_saved_albums,
		prefs.auto_rec,
		prefs.spotify_token,
		prefs.use_libre_fm,
		playlist_box.scroll_on,
		prefs.artist_list_sort_mode,
		prefs.phazor_device_selected,
		prefs.failed_background_artists,
		prefs.bg_flips,
		prefs.tray_show_title,
		prefs.artist_list_style,
		trackclass_jar,
		prefs.premium,
		gui.radio_view,
		pctl.radio_playlists,
		pctl.radio_playlist_viewing,
		prefs.radio_thumb_bans,
		prefs.playlist_exports,
		prefs.show_chromecast,
		prefs.cache_list,
		prefs.shuffle_lock,
		prefs.album_shuffle_lock_mode,
		gui.was_radio,
		prefs.spot_username,
		"", #prefs.spot_password,  # No longer used
		prefs.artist_list_threshold,
		prefs.tray_theme,
		prefs.row_title_format,
		prefs.row_title_genre,
		prefs.row_title_separator_type,
		prefs.replay_preamp,  # 181
		prefs.gallery_combine_disc,
	]

	try:
		with (user_directory / "state.p.backup").open("wb") as file:
			pickle.dump(save, file, protocol=pickle.HIGHEST_PROTOCOL)
		# if not pctl.running:
		with (user_directory / "state.p").open("wb") as file:
			pickle.dump(save, file, protocol=pickle.HIGHEST_PROTOCOL)

		old_position = old_window_position
		if not prefs.save_window_position:
			old_position = None

		save = [
			draw_border,
			gui.save_size,
			prefs.window_opacity,
			gui.scale,
			gui.maximized,
			old_position,
		]

		if not fs_mode:
			with (user_directory / "window.p").open("wb") as file:
				pickle.dump(save, file, protocol=pickle.HIGHEST_PROTOCOL)

		tauon.spot_ctl.save_token()

		with (user_directory / "lyrics_substitutions.json").open("w") as file:
			json.dump(prefs.lyrics_subs, file)

		save_prefs()

		for key, item in prefs.playlist_exports.items():
			pl = id_to_pl(key)
			if pl is None:
				continue
			if item["auto"] is False:
				continue
			export_playlist_box.run_export(item, key, warnings=False)

		logging.info("Done writing database")

	except PermissionError:
		logging.exception("Permission error encountered while writing database")
		show_message(_("Permission error encountered while writing database"), "error")
	except Exception:
		logging.exception("Unknown error encountered while writing database")

SDL_StartTextInput()

# SDL_SetHint(SDL_HINT_IME_INTERNAL_EDITING, b"1")
# SDL_EventState(SDL_SYSWMEVENT, 1)


def test_show_add_home_music() -> None:
	gui.add_music_folder_ready = True

	if music_directory is None:
		gui.add_music_folder_ready = False
		return

	for item in pctl.multi_playlist:
		if item.last_folder == str(music_directory):
			gui.add_music_folder_ready = False
			break

test_show_add_home_music()

if gui.restart_album_mode:
	toggle_album_mode(True)

if gui.remember_library_mode:
	toggle_library_mode()

quick_import_done = []

if reload_state:
	if reload_state[0] == 1:
		pctl.jump_time = reload_state[1]
		pctl.play()

pctl.notify_update()

key_focused = 0

theme = get_theme_number(prefs.theme_name)

if pl_to_id(pctl.active_playlist_viewing) in gui.gallery_positions:
	gui.album_scroll_px = gui.gallery_positions[pl_to_id(pctl.active_playlist_viewing)]


def menu_is_open():
	for menu in Menu.instances:
		if menu.active:
			return True
	return False


def is_level_zero(include_menus: bool = True) -> bool:
	if include_menus:
		for menu in Menu.instances:
			if menu.active:
				return False

	return not gui.rename_folder_box \
		and not track_box \
		and not rename_track_box.active \
		and not radiobox.active \
		and not pref_box.enabled \
		and not quick_search_mode \
		and not gui.rename_playlist_box \
		and not search_over.active \
		and not gui.box_over \
		and not trans_edit_box.active


# Hold the splash/loading screen for a minimum duration
# while core_timer.get() < 0.5:
#     time.sleep(0.01)

# Resize menu widths to text length (length can vary due to translations)
for menu in Menu.instances:

	w = 0
	icon_space = 0

	if menu.show_icons:
		icon_space = 25 * gui.scale

	for item in menu.items:
		if item is None:
			continue
		test_width = ddt.get_text_w(item.title, menu.font) + icon_space + 21 * gui.scale
		if not item.is_sub_menu and item.hint:
			test_width += ddt.get_text_w(item.hint, menu.font) + 4 * gui.scale

		w = max(test_width, w)

		# sub
		if item.is_sub_menu:
			ww = 0
			sub_icon_space = 0
			for sub_item in menu.subs[item.sub_menu_number]:
				if sub_item.icon is not None:
					sub_icon_space = 25 * gui.scale
					break
			for sub_item in menu.subs[item.sub_menu_number]:

				test_width = ddt.get_text_w(sub_item.title, menu.font) + sub_icon_space + 23 * gui.scale
				ww = max(test_width, ww)

			item.sub_menu_width = max(ww, item.sub_menu_width)

	menu.w = max(w, menu.w)


def drop_file(target):
	global new_playlist_cooldown
	global mouse_down
	global drag_mode

	if system != "windows" and sdl_version >= 204:
		gmp = get_global_mouse()
		gwp = get_window_position()
		i_x = gmp[0] - gwp[0]
		i_x = max(i_x, 0)
		i_x = min(i_x, window_size[0])
		i_y = gmp[1] - gwp[1]
		i_y = max(i_y, 0)
		i_y = min(i_y, window_size[1])
	else:
		i_y = pointer(c_int(0))
		i_x = pointer(c_int(0))

		SDL_GetMouseState(i_x, i_y)
		i_y = i_y.contents.value / logical_size[0] * window_size[0]
		i_x = i_x.contents.value / logical_size[0] * window_size[0]

	#logging.info((i_x, i_y))
	gui.drop_playlist_target = 0
	#logging.info(event.drop)

	if i_y < gui.panelY and not new_playlist_cooldown and gui.mode == 1:
		x = top_panel.tabs_left_x
		for tab in top_panel.shown_tabs:
			wid = top_panel.tab_text_spaces[tab] + top_panel.tab_extra_width

			if x < i_x < x + wid:
				gui.drop_playlist_target = tab
				tab_pulse.pulse()
				gui.update += 1
				gui.pl_pulse = True
				logging.info("Direct drop")
				break

			x += wid
		else:
			logging.info("MISS")
			if new_playlist_cooldown:
				gui.drop_playlist_target = pctl.active_playlist_viewing
			else:
				if not target.lower().endswith(".xspf"):
					gui.drop_playlist_target = new_playlist()
				new_playlist_cooldown = True

	elif gui.lsp and gui.panelY < i_y < window_size[1] - gui.panelBY and i_x < gui.lspw and gui.mode == 1:

		y = gui.panelY
		y += 5 * gui.scale
		y += playlist_box.tab_h + playlist_box.gap

		for i, pl in enumerate(pctl.multi_playlist):
			if i_y < y:
				gui.drop_playlist_target = i
				tab_pulse.pulse()
				gui.update += 1
				gui.pl_pulse = True
				logging.info("Direct drop")
				break
			y += playlist_box.tab_h + playlist_box.gap
		else:
			if new_playlist_cooldown:
				gui.drop_playlist_target = pctl.active_playlist_viewing
			else:
				if not target.lower().endswith(".xspf"):
					gui.drop_playlist_target = new_playlist()
				new_playlist_cooldown = True


	else:
		gui.drop_playlist_target = pctl.active_playlist_viewing

	if not os.path.exists(target) and flatpak_mode:
		show_message(
			_("Could not access! Possible insufficient Flatpak permissions."),
			_(" For details, see {link}").format(link="https://github.com/Taiko2k/TauonMusicBox/wiki/Flatpak-Extra-Steps"),
			mode="bubble")

	load_order = LoadClass()
	load_order.target = target.replace("\\", "/")

	if os.path.isdir(load_order.target):
		quick_import_done.append(load_order.target)

		# if not pctl.multi_playlist[gui.drop_playlist_target].last_folder:
		pctl.multi_playlist[gui.drop_playlist_target].last_folder.append(load_order.target)
		reduce_paths(pctl.multi_playlist[gui.drop_playlist_target].last_folder)

	load_order.playlist = pctl.multi_playlist[gui.drop_playlist_target].uuid_int
	load_orders.append(copy.deepcopy(load_order))

	#logging.info('dropped: ' + str(dropped_file))
	gui.update += 1
	mouse_down = False
	drag_mode = False


if gui.restore_showcase_view:
	enter_showcase_view()
if gui.restore_radio_view:
	enter_radio_view()

# switch_playlist(len(pctl.multi_playlist) - 1)

SDL_SetRenderTarget(renderer, overlay_texture_texture)

block_size = 3

x = 0
y = 0
while y < 300:
	x = 0
	while x < 300:
		ddt.rect((x, y, 1, 1), [0, 0, 0, 70])
		ddt.rect((x + 2, y + 0, 1, 1), [0, 0, 0, 70])
		ddt.rect((x + 2, y + 2, 1, 1), [0, 0, 0, 70])
		ddt.rect((x + 0, y + 2, 1, 1), [0, 0, 0, 70])

		x += block_size
	y += block_size

sync_target.text = prefs.sync_target
SDL_SetRenderTarget(renderer, None)

if msys:
	SDL_SetWindowResizable(t_window, True)  # Not sure why this is needed

# Generate theme buttons
pref_box.themes.append((ColoursClass(), "Mindaro", 0))
theme_files = get_themes()
for i, theme in enumerate(theme_files):
	c = ColoursClass()
	load_theme(c, Path(theme[0]))
	pref_box.themes.append((c, theme[1], i + 1))

pctl.total_playtime = star_store.get_total()

mouse_up = False
mouse_wheel = 0
reset_render = False
c_yax = 0
c_yax_timer = Timer()
c_xax = 0
c_xax_timer = Timer()
c_xay = 0
c_xay_timer = Timer()
rt = 0

# MAIN LOOP

while pctl.running:
	# bm.get('main')
	# time.sleep(100)
	if k_input:

		keymaps.hits.clear()

		d_mouse_click = False
		right_click = False
		level_2_right_click = False
		inp.mouse_click = False
		middle_click = False
		mouse_up = False
		inp.key_return_press = False
		key_down_press = False
		key_up_press = False
		key_right_press = False
		key_left_press = False
		key_esc_press = False
		key_del = False
		inp.backspace_press = 0
		key_backspace_press = False
		inp.key_tab_press = False
		key_c_press = False
		key_v_press = False
		key_a_press = False
		key_z_press = False
		key_x_press = False
		key_home_press = False
		key_end_press = False
		mouse_wheel = 0
		pref_box.scroll = 0
		new_playlist_cooldown = False
		input_text = ""
		inp.level_2_enter = False

		mouse_enter_window = False
		gui.mouse_in_window = True
		if key_focused:
			key_focused -= 1

	# f not mouse_down:
	k_input = False
	clicked = False
	focused = False
	mouse_moved = False
	gui.level_2_click = False

	# gui.update = 2

	while SDL_PollEvent(ctypes.byref(event)) != 0:

		# if event.type == SDL_SYSWMEVENT:
		#      logging.info(event.syswm.msg.contents) # Not implemented by pysdl2

		if event.type == SDL_CONTROLLERDEVICEADDED and prefs.use_gamepad:
			if SDL_IsGameController(event.cdevice.which):
				SDL_GameControllerOpen(event.cdevice.which)
				try:
					logging.info(f"Found game controller: {SDL_GameControllerNameForIndex(event.cdevice.which).decode()}")
				except Exception:
					logging.exception("Error getting game controller")

		if event.type == SDL_CONTROLLERAXISMOTION and prefs.use_gamepad:
			if event.caxis.axis == SDL_CONTROLLER_AXIS_TRIGGERLEFT:
				rt = event.caxis.value > 5000
			if event.caxis.axis == SDL_CONTROLLER_AXIS_LEFTY:
				if event.caxis.value < -10000:
					new = -1
				elif event.caxis.value > 10000:
					new = 1
				else:
					new = 0
				if new != c_yax:
					c_yax_timer.force_set(1)
				c_yax = new
				power += 5
				gui.update += 1
			if event.caxis.axis == SDL_CONTROLLER_AXIS_RIGHTX:
				if event.caxis.value < -15000:
					new = -1
				elif event.caxis.value > 15000:
					new = 1
				else:
					new = 0
				if new != c_xax:
					c_xax_timer.force_set(1)
				c_xax = new
				power += 5
				gui.update += 1
			if event.caxis.axis == SDL_CONTROLLER_AXIS_RIGHTY:
				if event.caxis.value < -15000:
					new = -1
				elif event.caxis.value > 15000:
					new = 1
				else:
					new = 0
				if new != c_xay:
					c_xay_timer.force_set(1)
				c_xay = new
				power += 5
				gui.update += 1

		if event.type == SDL_CONTROLLERBUTTONDOWN and prefs.use_gamepad:
			k_input = True
			power += 5
			gui.update += 2
			if event.cbutton.button == SDL_CONTROLLER_BUTTON_RIGHTSHOULDER:
				if rt:
					toggle_random()
				else:
					pctl.advance()
			if event.cbutton.button == SDL_CONTROLLER_BUTTON_LEFTSHOULDER:
				if rt:
					toggle_repeat()
				else:
					pctl.back()
			if event.cbutton.button == SDL_CONTROLLER_BUTTON_A:
				if rt:
					pctl.show_current(highlight=True)
				elif pctl.playing_ready() and pctl.active_playlist_playing == pctl.active_playlist_viewing and \
						pctl.selected_ready() and default_playlist[
					pctl.selected_in_playlist] == pctl.playing_object().index:
					pctl.play_pause()
				else:
					inp.key_return_press = True
			if event.cbutton.button == SDL_CONTROLLER_BUTTON_X:
				if rt:
					random_track()
				else:
					toggle_gallery_keycontrol(always_exit=True)
			if event.cbutton.button == SDL_CONTROLLER_BUTTON_Y:
				if rt:
					pctl.advance(rr=True)
				else:
					pctl.play_pause()
			if event.cbutton.button == SDL_CONTROLLER_BUTTON_B:
				if rt:
					pctl.revert()
				elif is_level_zero():
					pctl.stop()
				else:
					key_esc_press = True
			if event.cbutton.button == SDL_CONTROLLER_BUTTON_DPAD_UP:
				key_up_press = True
			if event.cbutton.button == SDL_CONTROLLER_BUTTON_DPAD_DOWN:
				key_down_press = True
			if event.cbutton.button == SDL_CONTROLLER_BUTTON_DPAD_LEFT:
				if gui.album_tab_mode:
					key_left_press = True
				elif is_level_zero() or quick_search_mode:
					cycle_playlist_pinned(1)
			if event.cbutton.button == SDL_CONTROLLER_BUTTON_DPAD_RIGHT:
				if gui.album_tab_mode:
					key_right_press = True
				elif is_level_zero() or quick_search_mode:
					cycle_playlist_pinned(-1)

		if event.type == SDL_RENDER_TARGETS_RESET and not msys:
			reset_render = True

		if event.type == SDL_DROPTEXT:

			power += 5

			link = event.drop.file.decode()
			#logging.info(link)

			if pctl.playing_ready() and link.startswith("http"):
				if system != "windows" and sdl_version >= 204:
					gmp = get_global_mouse()
					gwp = get_window_position()
					i_x = gmp[0] - gwp[0]
					i_x = max(i_x, 0)
					i_x = min(i_x, window_size[0])
					i_y = gmp[1] - gwp[1]
					i_y = max(i_y, 0)
					i_y = min(i_y, window_size[1])
				else:
					i_y = pointer(c_int(0))
					i_x = pointer(c_int(0))

					SDL_GetMouseState(i_x, i_y)
					i_y = i_y.contents.value / logical_size[0] * window_size[0]
					i_x = i_x.contents.value / logical_size[0] * window_size[0]

				if coll_point((i_x, i_y), gui.main_art_box):
					logging.info("Drop picture...")
					#logging.info(link)
					gui.image_downloading = True
					track = pctl.playing_object()
					target_dir = track.parent_folder_path

					shoot_dl = threading.Thread(target=download_img, args=(link, target_dir, track))
					shoot_dl.daemon = True
					shoot_dl.start()

					gui.update = True

			elif link.startswith("file:///"):
				link = link.replace("\r", "")
				for line in link.split("\n"):
					target = str(urllib.parse.unquote(line)).replace("file:///", "/")
					drop_file(target)

		if event.type == SDL_DROPFILE:

			power += 5
			dropped_file_sdl = event.drop.file
			#logging.info(dropped_file_sdl)
			target = str(urllib.parse.unquote(
				dropped_file_sdl.decode("utf-8", errors="surrogateescape"))).replace("file:///", "/").replace("\r", "")
			#logging.info(target)
			drop_file(target)


		elif event.type == 8192:
			gui.pl_update = 1
			gui.update += 2

		elif event.type == SDL_QUIT:
			power += 5

			if gui.tray_active and prefs.min_to_tray and not key_shift_down:
				tauon.min_to_tray()
			else:
				tauon.exit("Window received exit signal")
				break
		elif event.type == SDL_TEXTEDITING:
			power += 5
			#logging.info("edit text")
			editline = event.edit.text
			#logging.info(editline)
			editline = editline.decode("utf-8", "ignore")
			k_input = True
			gui.update += 1

		elif event.type == SDL_MOUSEMOTION:

			mouse_position[0] = int(event.motion.x / logical_size[0] * window_size[0])
			mouse_position[1] = int(event.motion.y / logical_size[0] * window_size[0])
			mouse_moved = True
			gui.mouse_unknown = False
		elif event.type == SDL_MOUSEBUTTONDOWN:

			k_input = True
			focused = True
			power += 5
			gui.update += 1
			gui.mouse_in_window = True

			if ggc == 2:  # dont click on first full frame
				continue

			if event.button.button == SDL_BUTTON_RIGHT:
				right_click = True
				right_down = True
				#logging.info("RIGHT DOWN")
			elif event.button.button == SDL_BUTTON_LEFT:
				#logging.info("LEFT DOWN")

				# if mouse_position[1] > 1 and mouse_position[0] > 1:
				#     mouse_down = True

				inp.mouse_click = True

				mouse_down = True
			elif event.button.button == SDL_BUTTON_MIDDLE:
				if not search_over.active:
					middle_click = True
				gui.update += 1
			elif event.button.button == SDL_BUTTON_X1:
				keymaps.hits.append("MB4")
			elif event.button.button == SDL_BUTTON_X2:
				keymaps.hits.append("MB5")
		elif event.type == SDL_MOUSEBUTTONUP:
			k_input = True
			power += 5
			gui.update += 1
			if event.button.button == SDL_BUTTON_RIGHT:
				right_down = False
			elif event.button.button == SDL_BUTTON_LEFT:
				if mouse_down:
					mouse_up = True
					mouse_up_position[0] = event.motion.x / logical_size[0] * window_size[0]
					mouse_up_position[1] = event.motion.y / logical_size[0] * window_size[0]

				mouse_down = False
				gui.update += 1
		elif event.type == SDL_KEYDOWN and key_focused == 0:
			k_input = True
			power += 5
			gui.update += 2
			if prefs.use_scancodes:
				keymaps.hits.append(event.key.keysym.scancode)
			else:
				keymaps.hits.append(event.key.keysym.sym)

			if prefs.use_scancodes:
				if event.key.keysym.scancode == SDL_SCANCODE_V:
					key_v_press = True
				elif event.key.keysym.scancode == SDL_SCANCODE_A:
					key_a_press = True
				elif event.key.keysym.scancode == SDL_SCANCODE_C:
					key_c_press = True
				elif event.key.keysym.scancode == SDL_SCANCODE_Z:
					key_z_press = True
				elif event.key.keysym.scancode == SDL_SCANCODE_X:
					key_x_press = True
			elif event.key.keysym.sym == SDLK_v:
				key_v_press = True
			elif event.key.keysym.sym == SDLK_a:
				key_a_press = True
			elif event.key.keysym.sym == SDLK_c:
				key_c_press = True
			elif event.key.keysym.sym == SDLK_z:
				key_z_press = True
			elif event.key.keysym.sym == SDLK_x:
				key_x_press = True

			if event.key.keysym.sym == (SDLK_RETURN or SDLK_RETURN2) and len(editline) == 0:
				inp.key_return_press = True
			elif event.key.keysym.sym == SDLK_KP_ENTER and len(editline) == 0:
				inp.key_return_press = True
			elif event.key.keysym.sym == SDLK_TAB:
				inp.key_tab_press = True
			elif event.key.keysym.sym == SDLK_BACKSPACE:
				inp.backspace_press += 1
				key_backspace_press = True
			elif event.key.keysym.sym == SDLK_DELETE:
				key_del = True
			elif event.key.keysym.sym == SDLK_RALT:
				key_ralt = True
			elif event.key.keysym.sym == SDLK_LALT:
				key_lalt = True
			elif event.key.keysym.sym == SDLK_DOWN:
				key_down_press = True
			elif event.key.keysym.sym == SDLK_UP:
				key_up_press = True
			elif event.key.keysym.sym == SDLK_LEFT:
				key_left_press = True
			elif event.key.keysym.sym == SDLK_RIGHT:
				key_right_press = True
			elif event.key.keysym.sym == SDLK_LSHIFT:
				key_shift_down = True
			elif event.key.keysym.sym == SDLK_RSHIFT:
				key_shiftr_down = True
			elif event.key.keysym.sym == SDLK_LCTRL:
				key_ctrl_down = True
			elif event.key.keysym.sym == SDLK_RCTRL:
				key_rctrl_down = True
			elif event.key.keysym.sym == SDLK_HOME:
				key_home_press = True
			elif event.key.keysym.sym == SDLK_END:
				key_end_press = True
			elif event.key.keysym.sym == SDLK_LGUI:
				if macos:
					key_ctrl_down = True
				else:
					key_meta = True
					key_focused = 1

		elif event.type == SDL_KEYUP:

			k_input = True
			power += 5
			gui.update += 2
			if event.key.keysym.sym == SDLK_LSHIFT:
				key_shift_down = False
			elif event.key.keysym.sym == SDLK_LCTRL:
				key_ctrl_down = False
			elif event.key.keysym.sym == SDLK_RCTRL:
				key_rctrl_down = False
			elif event.key.keysym.sym == SDLK_RSHIFT:
				key_shiftr_down = False
			elif event.key.keysym.sym == SDLK_RALT:
				gui.album_tab_mode = False
				key_ralt = False
			elif event.key.keysym.sym == SDLK_LALT:
				gui.album_tab_mode = False
				key_lalt = False
			elif event.key.keysym.sym == SDLK_LGUI:
				if macos:
					key_ctrl_down = False
				else:
					key_meta = False
					key_focused = 1

		elif event.type == SDL_TEXTINPUT:
			k_input = True
			power += 5
			input_text += event.text.text.decode("utf-8")

			gui.update += 1
			#logging.info(input_text)

		elif event.type == SDL_MOUSEWHEEL:
			k_input = True
			power += 6
			mouse_wheel += event.wheel.y
			gui.update += 1
		elif event.type == SDL_WINDOWEVENT:

			power += 5
			#logging.info(event.window.event)

			if event.window.event == SDL_WINDOWEVENT_FOCUS_GAINED:
				#logging.info("SDL_WINDOWEVENT_FOCUS_GAINED")

				if system == "Linux" and not macos and not msys:
					gnome.focus()
				k_input = True

				mouse_enter_window = True
				focused = True
				gui.lowered = False
				key_focused = 1
				mouse_down = False
				gui.album_tab_mode = False
				gui.pl_update = 1
				gui.update += 1

			elif event.window.event == SDL_WINDOWEVENT_FOCUS_LOST:
				close_all_menus()
				key_focused = 1
				gui.update += 1

			elif event.window.event == SDL_WINDOWEVENT_DISPLAY_CHANGED:
				# SDL_WINDOWEVENT_DISPLAY_CHANGED logs new display ID as data1 (0 or 1 or 2...), it not width, and data 2 is always 0
				pass
			elif event.window.event == SDL_WINDOWEVENT_RESIZED:
				# SDL_WINDOWEVENT_RESIZED logs width to data1 and height to data2
				if event.window.data1 < 500:
					logging.error("Window width is less than 500, grrr why does this happen, stupid bug")
					SDL_SetWindowSize(t_window, logical_size[0], logical_size[1])
				elif restore_ignore_timer.get() > 1:  # Hacky
					gui.update = 2

					logical_size[0] = event.window.data1
					logical_size[1] = event.window.data2

					if gui.mode != 3:
						logical_size[0] = max(300, logical_size[0])
						logical_size[1] = max(300, logical_size[1])

					i_x = pointer(c_int(0))
					i_y = pointer(c_int(0))
					SDL_GL_GetDrawableSize(t_window, i_x, i_y)
					window_size[0] = i_x.contents.value
					window_size[1] = i_y.contents.value

					auto_scale()
					update_layout = True


			elif event.window.event == SDL_WINDOWEVENT_ENTER:
				#logging.info("ENTER")
				mouse_enter_window = True
				gui.mouse_in_window = True
				gui.update += 1

			# elif event.window.event == SDL_WINDOWEVENT_HIDDEN:
			#
			elif event.window.event == SDL_WINDOWEVENT_EXPOSED:
				#logging.info("expose")
				gui.lowered = False

			elif event.window.event == SDL_WINDOWEVENT_MINIMIZED:
				gui.lowered = True
				# if prefs.min_to_tray:
				#     tray.down()
				# tauon.thread_manager.sleep()

			elif event.window.event == SDL_WINDOWEVENT_RESTORED:

				gui.lowered = False
				gui.maximized = False
				gui.pl_update = 1
				gui.update += 2

				if update_title:
					update_title_do()
					#logging.info("restore")

			elif event.window.event == SDL_WINDOWEVENT_SHOWN:
				focused = True
				gui.pl_update = 1
				gui.update += 1

			# elif event.window.event == SDL_WINDOWEVENT_FOCUS_GAINED:
			#     logging.info("FOCUS GAINED")
			#     # input.mouse_enter_event = True
			#     # gui.update += 1
			#     # k_input = True

			elif event.window.event == SDL_WINDOWEVENT_MAXIMIZED:
				if gui.mode != 3:  # workaround. sdl bug? gives event on window size set
					gui.maximized = True
				update_layout = True
				gui.pl_update = 1
				gui.update += 1

			elif event.window.event == SDL_WINDOWEVENT_LEAVE:
				gui.mouse_in_window = False
				gui.update += 1
				power = 1000

	if mouse_moved:
		if fields.test():
			gui.update += 1

	if gui.request_raise:
		gui.request_raise = False
		logging.info("Raise")
		SDL_ShowWindow(t_window)
		SDL_RestoreWindow(t_window)
		SDL_RaiseWindow(t_window)
		gui.lowered = False

	# if tauon.thread_manager.sleeping:
	#     if not gui.lowered:
	#         tauon.thread_manager.wake()
	if gui.lowered:
		gui.update = 0
	# ----------------
	# This section of code controls the internal processing speed or 'frame-rate'
	# It's pretty messy
	# if not gui.pl_update and gui.rendered_playlist_position != playlist_view_position:
	#     logging.warning("The playlist failed to render at the latest position!!!!")

	power += 1

	if pctl.playerCommandReady:
		if tauon.thread_manager.player_lock.locked():
			try:
				tauon.thread_manager.player_lock.release()
			except RuntimeError as e:
				if str(e) == "release unlocked lock":
					logging.error("RuntimeError: Attempted to release already unlocked player_lock")
				else:
					logging.exception("Unknown RuntimeError trying to release player_lock")
			except Exception:
				logging.exception("Unknown exception trying to release player_lock")

	if gui.frame_callback_list:
		i = len(gui.frame_callback_list) - 1
		while i >= 0:
			if gui.frame_callback_list[i].test():
				gui.update = 1
				power = 1000
				del gui.frame_callback_list[i]
			i -= 1

	if animate_monitor_timer.get() < 1 or load_orders:

		if cursor_blink_timer.get() > 0.65:
			cursor_blink_timer.set()
			TextBox.cursor ^= True
			gui.update = 1

		if k_input:
			cursor_blink_timer.set()
			TextBox.cursor = True

		SDL_Delay(3)
		power = 1000

	if mouse_wheel or k_input or gui.pl_update or gui.update or top_panel.adds:  # or mouse_moved:
		power = 1000

	if prefs.art_bg and core_timer.get() < 3:
		power = 1000

	if mouse_down and mouse_moved:
		power = 1000
		if gui.update_on_drag:
			gui.update += 1
		if gui.pl_update_on_drag:
			gui.pl_update += 1

	if pctl.wake_past_time:

		if get_real_time() > pctl.wake_past_time:
			pctl.wake_past_time = 0
			power = 1000
			gui.update += 1

	if gui.level_update and not album_scroll_hold and not scroll_hold:
		power = 500

	# if gui.vis == 3 and (pctl.playing_state == 1 or pctl.playing_state == 3):
	#     power = 500
	#     if len(gui.spec2_buffers) > 0 and gui.spec2_timer.get() > 0.04:
	#         gui.spec2_timer.set()
	#         gui.level_update = True
	#         vis_update = True
	#     else:
	#         SDL_Delay(5)

	if not pctl.running:
		break

	if pctl.playing_state > 0:
		power += 400

	if power < 500:

		time.sleep(0.03)

		if (
				pctl.playing_state == 0 or pctl.playing_state == 2) and not load_orders and gui.update == 0 and not tauon.gall_ren.queue and not transcode_list and not gui.frame_callback_list:
			pass
		else:
			sleep_timer.set()
		if sleep_timer.get() > 2:
			SDL_WaitEventTimeout(None, 1000)
		continue

	else:
		power = 0

	gui.pl_update = min(gui.pl_update, 2)

	new_playlist_cooldown = False

	if prefs.auto_extract and prefs.monitor_downloads:
		dl_mon.scan()

	if mouse_down and not coll((2, 2, window_size[0] - 4, window_size[1] - 4)):
		#logging.info(SDL_GetMouseState(None, None))
		if SDL_GetGlobalMouseState(None, None) == 0:
			mouse_down = False
			mouse_up = True
			quick_drag = False

	#logging.info(window_size)
	# if window_size[0] / window_size[1] == 16 / 9:
	#     logging.info('OK')
	# if window_size[0] / window_size[1] > 16 / 9:
	#     logging.info("A")

	if key_meta:
		input_text = ""
		k_input = False
		inp.key_return_press = False
		inp.key_tab_press = False

	if k_input:
		if inp.mouse_click or right_click or mouse_up:
			last_click_location = copy.deepcopy(click_location)
			click_location = copy.deepcopy(mouse_position)

		if key_focused != 0:
			keymaps.hits.clear()

			# d_mouse_click = False
			# right_click = False
			# level_2_right_click = False
			# inp.mouse_click = False
			# middle_click = False
			mouse_up = False
			inp.key_return_press = False
			key_down_press = False
			key_up_press = False
			key_right_press = False
			key_left_press = False
			key_esc_press = False
			key_del = False
			inp.backspace_press = 0
			key_backspace_press = False
			inp.key_tab_press = False
			key_c_press = False
			key_v_press = False
			# key_f_press = False
			key_a_press = False
			# key_t_press = False
			key_z_press = False
			key_x_press = False
			key_home_press = False
			key_end_press = False
			mouse_wheel = 0
			pref_box.scroll = 0
			input_text = ""
			inp.level_2_enter = False

	if c_yax != 0:
		if c_yax_timer.get() >= 0:
			if c_yax == -1:
				key_up_press = True
			if c_yax == 1:
				key_down_press = True
			c_yax_timer.force_set(-0.01)
			gui.delay_frame(0.02)
			k_input = True
	if c_xax != 0:
		if c_xax_timer.get() >= 0:
			if c_xax == 1:
				pctl.seek_time(pctl.playing_time + 2)
			if c_xax == -1:
				pctl.seek_time(pctl.playing_time - 2)
			c_xax_timer.force_set(-0.01)
			gui.delay_frame(0.02)
			k_input = True
	if c_xay != 0:
		if c_xay_timer.get() >= 0:
			if c_xay == -1:
				pctl.player_volume += 1
				pctl.player_volume = min(pctl.player_volume, 100)
				pctl.set_volume()
			if c_xay == 1:
				if pctl.player_volume > 1:
					pctl.player_volume -= 1
				else:
					pctl.player_volume = 0
				pctl.set_volume()
			c_xay_timer.force_set(-0.01)
			gui.delay_frame(0.02)
			k_input = True

	if k_input and key_focused == 0:

		if keymaps.hits:
			n = 1
			while n < 10:
				if keymaps.test(f"jump-playlist-{n}"):
					if len(pctl.multi_playlist) > n - 1:
						switch_playlist(n - 1)
				n += 1

			if keymaps.test("cycle-playlist-left"):
				if gui.album_tab_mode and key_left_press:
					pass
				elif is_level_zero() or quick_search_mode:
					cycle_playlist_pinned(1)
			if keymaps.test("cycle-playlist-right"):
				if gui.album_tab_mode and key_right_press:
					pass
				elif is_level_zero() or quick_search_mode:
					cycle_playlist_pinned(-1)

			if keymaps.test("toggle-console"):
				console.toggle()

			if keymaps.test("toggle-fullscreen"):
				if not gui.fullscreen and gui.mode != 3:
					gui.fullscreen = True
					SDL_SetWindowFullscreen(t_window, SDL_WINDOW_FULLSCREEN_DESKTOP)
				elif gui.fullscreen:
					gui.fullscreen = False
					SDL_SetWindowFullscreen(t_window, 0)

			if keymaps.test("playlist-toggle-breaks"):
				# Toggle force off folder break for viewed playlist
				pctl.multi_playlist[pctl.active_playlist_viewing].hide_title ^= 1
				gui.pl_update = 1

			if keymaps.test("find-playing-artist"):
				# standard_size()
				if len(pctl.track_queue) > 0:
					quick_search_mode = True
					search_text.text = ""
					input_text = pctl.playing_object().artist

			if keymaps.test("show-encode-folder"):
				open_encode_out()

			if keymaps.test("toggle-left-panel"):
				gui.lsp ^= True
				update_layout_do()

			if keymaps.test("toggle-last-left-panel"):
				toggle_left_last()
				update_layout_do()

			if keymaps.test("escape"):
				key_esc_press = True

		if key_ctrl_down:
			gui.pl_update += 1

		if mouse_enter_window:
			inp.key_return_press = False

		if gui.fullscreen and key_esc_press:
			gui.fullscreen = False
			SDL_SetWindowFullscreen(t_window, 0)

		# Disable keys for text cursor control
		if not gui.rename_folder_box and not rename_track_box.active and not gui.rename_playlist_box and not radiobox.active and not pref_box.enabled and not trans_edit_box.active:

			if not quick_search_mode and not search_over.active:
				if album_mode and gui.album_tab_mode \
						and not key_ctrl_down \
						and not key_meta \
						and not key_lalt:
					if key_left_press:
						gal_left = True
						key_left_press = False
					if key_right_press:
						gal_right = True
						key_right_press = False
					if key_up_press:
						gal_up = True
						key_up_press = False
					if key_down_press:
						gal_down = True
						key_down_press = False

			if not search_over.active:
				if key_del:
					close_all_menus()
					del_selected()

				# Arrow keys to change playlist
				if (key_left_press or key_right_press) and len(pctl.multi_playlist) > 1:
					gui.pl_update = 1
					gui.update += 1

			if keymaps.test("start"):
				if pctl.playing_time < 4:
					pctl.back()
				else:
					pctl.new_time = 0
					pctl.playing_time = 0
					pctl.decode_time = 0
					pctl.playerCommand = "seek"
					pctl.playerCommandReady = True

			if keymaps.test("goto-top"):
				pctl.playlist_view_position = 0
				logging.debug("Position changed by key")
				pctl.selected_in_playlist = 0
				gui.pl_update = 1

			if keymaps.test("goto-bottom"):
				n = len(default_playlist) - gui.playlist_view_length + 1
				n = max(n, 0)
				pctl.playlist_view_position = n
				logging.debug("Position changed by key")
				pctl.selected_in_playlist = len(default_playlist) - 1
				gui.pl_update = 1

		if not pref_box.enabled and not radiobox.active and not rename_track_box.active \
				and not gui.rename_folder_box \
				and not gui.rename_playlist_box and not search_over.active and not gui.box_over and not trans_edit_box.active:

			if quick_search_mode:
				if keymaps.test("add-to-queue") and pctl.selected_ready():
					add_selected_to_queue()
					input_text = ""

			else:

				if key_c_press and key_ctrl_down:
					gui.pl_update = 1
					s_copy()

				if key_x_press and key_ctrl_down:
					gui.pl_update = 1
					s_cut()

				if key_v_press and key_ctrl_down:
					gui.pl_update = 1
					paste()

				if keymaps.test("playpause"):
					pctl.play_pause()


		if inp.key_return_press and (gui.rename_folder_box or rename_track_box.active or radiobox.active):
			inp.key_return_press = False
			inp.level_2_enter = True

		if key_ctrl_down and key_z_press:
			undo.undo()

		if keymaps.test("quit"):
			tauon.exit("Quit keyboard shortcut pressed")

		if keymaps.test("testkey"):  # F7: test
			pass

		if gui.mode < 3:
			if keymaps.test("toggle-auto-theme"):
				prefs.colour_from_image ^= True
				if prefs.colour_from_image:
					show_message(_("Enabled auto theme"))
				else:
					show_message(_("Disabled auto theme"))
					gui.reload_theme = True
					gui.theme_temp_current = -1

			if keymaps.test("transfer-playtime-to"):
				if len(cargo) == 1 and tauon.copied_track is not None and -1 < pctl.selected_in_playlist < len(
						default_playlist):
					fr = pctl.get_track(tauon.copied_track)
					to = pctl.get_track(default_playlist[pctl.selected_in_playlist])

					fr_s = star_store.full_get(fr.index)
					to_s = star_store.full_get(to.index)

					fr_scr = fr.lfm_scrobbles
					to_scr = to.lfm_scrobbles

					undo.bk_playtime_transfer(fr, fr_s, fr_scr, to, to_s, to_scr)

					if to_s is None:
						to_s = star_store.new_object()
					if fr_s is None:
						fr_s = star_store.new_object()

					new = star_store.new_object()

					new[0] = fr_s[0] + to_s[0]  # playtime
					new[1] = fr_s[1]  # flags
					if to_s[1]:
						new[1] = to_s[1]  # keep target flags
					new[2] = fr_s[2]  # raiting
					if to_s[2] > 0 and fr_s[2] == 0:
						new[2] = to_s[2]  # keep target rating
					to.lfm_scrobbles = fr.lfm_scrobbles

					star_store.remove(fr.index)
					star_store.remove(to.index)
					if new[0] or new[1] or new[2]:
						star_store.insert(to.index, new)

					tauon.copied_track = None
					gui.pl_update += 1
					logging.info("Transferred track stats!")
				elif tauon.copied_track is None:
					show_message(_("First select a source track by copying it into clipboard"))

			if keymaps.test("toggle-gallery"):
				toggle_album_mode()

			if keymaps.test("toggle-right-panel"):
				if gui.combo_mode:
					exit_combo()
				elif not album_mode:
					toggle_side_panel()
				else:
					toggle_album_mode()

			if keymaps.test("toggle-minimode"):
				set_mini_mode()
				gui.update += 1

			if keymaps.test("cycle-layouts"):

				if view_box.tracks():
					view_box.side(True)
				elif view_box.side():
					view_box.gallery1(True)
				elif view_box.gallery1():
					view_box.lyrics(True)
				else:
					view_box.tracks(True)

			if keymaps.test("cycle-layouts-reverse"):

				if view_box.tracks():
					view_box.lyrics(True)
				elif view_box.lyrics():
					view_box.gallery1(True)
				elif view_box.gallery1():
					view_box.side(True)
				else:
					view_box.tracks(True)

			if keymaps.test("toggle-columns"):
				view_box.col(True)

			if keymaps.test("toggle-artistinfo"):
				view_box.artist_info(True)

			if keymaps.test("toggle-showcase"):
				view_box.lyrics(True)

			if keymaps.test("toggle-gallery-keycontrol"):
				toggle_gallery_keycontrol()

			if keymaps.test("toggle-show-art"):
				toggle_side_art()

		elif gui.mode == 3:
			if keymaps.test("toggle-minimode"):
				restore_full_mode()
				gui.update += 1

		ab_click = False

		if keymaps.test("new-playlist"):
			new_playlist()

		if keymaps.test("edit-generator"):
			edit_generator_box(pctl.active_playlist_viewing)

		if keymaps.test("new-generator-playlist"):
			new_playlist()
			edit_generator_box(pctl.active_playlist_viewing)

		if keymaps.test("delete-playlist"):
			delete_playlist(pctl.active_playlist_viewing)

		if keymaps.test("delete-playlist-force"):
			delete_playlist(pctl.active_playlist_viewing, force=True)

		if keymaps.test("rename-playlist"):
			if gui.radio_view:
				rename_playlist(pctl.radio_playlist_viewing)
			else:
				rename_playlist(pctl.active_playlist_viewing)
			rename_playlist_box.x = 60 * gui.scale
			rename_playlist_box.y = 60 * gui.scale

		# Transfer click register to menus
		if inp.mouse_click:
			for instance in Menu.instances:
				if instance.active:
					instance.click()
					inp.mouse_click = False
					ab_click = True
			if view_box.active:
				view_box.clicked = True

		if inp.mouse_click and (
				prefs.show_nag or gui.box_over or radiobox.active or search_over.active or gui.rename_folder_box or gui.rename_playlist_box or rename_track_box.active or view_box.active or trans_edit_box.active):  # and not gui.message_box:
			inp.mouse_click = False
			gui.level_2_click = True
		else:
			gui.level_2_click = False

		if track_box and inp.mouse_click:
			w = 540
			h = 240
			x = int(window_size[0] / 2) - int(w / 2)
			y = int(window_size[1] / 2) - int(h / 2)
			if coll([x, y, w, h]):
				inp.mouse_click = False
				gui.level_2_click = True

		if right_click:
			level_2_right_click = True

		if pref_box.enabled:

			if pref_box.inside():
				if inp.mouse_click:  # and not gui.message_box:
					pref_box.click = True
					inp.mouse_click = False
				if right_click:
					right_click = False
					pref_box.right_click = True

				pref_box.scroll = mouse_wheel
				mouse_wheel = 0
			else:
				if inp.mouse_click:
					pref_box.close()
				if right_click:
					pref_box.close()
				if pref_box.lock is False:
					pass

		if right_click and (
				radiobox.active or rename_track_box.active or gui.rename_playlist_box or gui.rename_folder_box or search_over.active):
			right_click = False

		if mouse_wheel != 0:
			gui.update += 1
		if mouse_down is True:
			gui.update += 1

		if keymaps.test("pagedown"):  # key_PGD:
			if len(default_playlist) > 10:
				pctl.playlist_view_position += gui.playlist_view_length - 4
				if pctl.playlist_view_position > len(default_playlist):
					pctl.playlist_view_position = len(default_playlist) - 2
				gui.pl_update = 1
				pctl.selected_in_playlist = pctl.playlist_view_position
				logging.debug("Position changed by page key")
				shift_selection.clear()
		if keymaps.test("pageup"):
			if len(default_playlist) > 0:
				pctl.playlist_view_position -= gui.playlist_view_length - 4
				pctl.playlist_view_position = max(pctl.playlist_view_position, 0)
				gui.pl_update = 1
				pctl.selected_in_playlist = pctl.playlist_view_position
				logging.debug("Position changed by page key")
				shift_selection.clear()

		if quick_search_mode is False and rename_track_box.active is False and gui.rename_folder_box is False and gui.rename_playlist_box is False and not pref_box.enabled and not radiobox.active:

			if keymaps.test("info-playing"):
				if pctl.selected_in_playlist < len(default_playlist):
					r_menu_index = pctl.get_track(default_playlist[pctl.selected_in_playlist]).index
					track_box = True

			if keymaps.test("info-show"):
				if pctl.selected_in_playlist < len(default_playlist):
					r_menu_index = pctl.get_track(default_playlist[pctl.selected_in_playlist]).index
					track_box = True

			# These need to be disabled when text fields are active
			if not search_over.active and not gui.box_over and not radiobox.active and not gui.rename_folder_box and not rename_track_box.active and not gui.rename_playlist_box and not trans_edit_box.active:
				if keymaps.test("advance"):
					key_right_press = False
					pctl.advance()

				if keymaps.test("previous"):
					key_left_press = False
					pctl.back()

				if key_a_press and key_ctrl_down:
					gui.pl_update = 1
					shift_selection = range(len(default_playlist)) # TODO(Martin): This can under some circumstances end up doing a range.clear()

				if keymaps.test("revert"):
					pctl.revert()

				if keymaps.test("random-track-start"):
					pctl.advance(rr=True)

				if keymaps.test("vol-down"):
					if pctl.player_volume > 3:
						pctl.player_volume -= 3
					else:
						pctl.player_volume = 0
					pctl.set_volume()

				if keymaps.test("toggle-mute"):
					pctl.toggle_mute()

				if keymaps.test("vol-up"):
					pctl.player_volume += 3
					pctl.player_volume = min(pctl.player_volume, 100)
					pctl.set_volume()

				if keymaps.test("shift-down") and len(default_playlist) > 0:
					gui.pl_update += 1
					if pctl.selected_in_playlist > len(default_playlist) - 1:
						pctl.selected_in_playlist = 0

					if not shift_selection:
						shift_selection.append(pctl.selected_in_playlist)
					if pctl.selected_in_playlist < len(default_playlist) - 1:
						r = pctl.selected_in_playlist
						pctl.selected_in_playlist += 1
						if pctl.selected_in_playlist not in shift_selection:
							shift_selection.append(pctl.selected_in_playlist)
						else:
							shift_selection.remove(r)

				if keymaps.test("shift-up") and pctl.selected_in_playlist > -1:
					gui.pl_update += 1
					if pctl.selected_in_playlist > len(default_playlist) - 1:
						pctl.selected_in_playlist = 0

					if not shift_selection:
						shift_selection.append(pctl.selected_in_playlist)
					if pctl.selected_in_playlist < len(default_playlist) - 1:
						r = pctl.selected_in_playlist
						pctl.selected_in_playlist -= 1
						if pctl.selected_in_playlist not in shift_selection:
							shift_selection.insert(0, pctl.selected_in_playlist)
						else:
							shift_selection.remove(r)

				if keymaps.test("toggle-shuffle"):
					# pctl.random_mode ^= True
					toggle_random()

				if keymaps.test("goto-playing"):
					pctl.show_current()
				if keymaps.test("goto-previous"):
					if pctl.queue_step > 1:
						pctl.show_current(index=pctl.track_queue[pctl.queue_step - 1])

				if keymaps.test("toggle-repeat"):
					toggle_repeat()

				if keymaps.test("random-track"):
					random_track()

				if keymaps.test("random-album"):
					random_album()

				if keymaps.test("opacity-up"):
					prefs.window_opacity += .05
					prefs.window_opacity = min(prefs.window_opacity, 1)
					SDL_SetWindowOpacity(t_window, prefs.window_opacity)

				if keymaps.test("opacity-down"):
					prefs.window_opacity -= .05
					prefs.window_opacity = max(prefs.window_opacity, .30)
					SDL_SetWindowOpacity(t_window, prefs.window_opacity)

				if keymaps.test("seek-forward"):
					pctl.seek_time(pctl.playing_time + prefs.seek_interval)

				if keymaps.test("seek-back"):
					pctl.seek_time(pctl.playing_time - prefs.seek_interval)

				if keymaps.test("play"):
					pctl.play()

				if keymaps.test("stop"):
					pctl.stop()

				if keymaps.test("pause"):
					pctl.pause_only()

				if keymaps.test("love-playing"):
					bar_love(notify=True)

				if keymaps.test("love-selected"):
					select_love(notify=True)

				if keymaps.test("search-lyrics-selected"):
					if pctl.selected_ready():
						track = pctl.get_track(default_playlist[pctl.selected_in_playlist])
						if track.lyrics:
							show_message(_("Track already has lyrics"))
						else:
							get_lyric_wiki(track)

				if keymaps.test("substitute-search-selected"):
					if pctl.selected_ready():
						show_sub_search(pctl.get_track(default_playlist[pctl.selected_in_playlist]))

				if keymaps.test("global-search"):
					activate_search_overlay()

				if keymaps.test("add-to-queue") and pctl.selected_ready():
					add_selected_to_queue()

				if keymaps.test("clear-queue"):
					clear_queue()

				if keymaps.test("regenerate-playlist"):
					regenerate_playlist(pctl.active_playlist_viewing)

		if keymaps.test("cycle-theme"):
			gui.reload_theme = True
			gui.theme_temp_current = -1
			gui.temp_themes.clear()
			theme += 1

		if keymaps.test("cycle-theme-reverse"):
			gui.theme_temp_current = -1
			gui.temp_themes.clear()
			pref_box.devance_theme()

		if keymaps.test("reload-theme"):
			gui.reload_theme = True

	# if mouse_position[1] < 1:
	#     mouse_down = False

	if mouse_down is False:
		scroll_hold = False

	# if focused is True:
	#     mouse_down = False

	if inp.media_key:
		if inp.media_key == "Play":
			if pctl.playing_state == 0:
				pctl.play()
			else:
				pctl.pause()
		elif inp.media_key == "Pause":
			pctl.pause_only()
		elif inp.media_key == "Stop":
			pctl.stop()
		elif inp.media_key == "Next":
			pctl.advance()
		elif inp.media_key == "Previous":
			pctl.back()

		elif inp.media_key == "Rewind":
			pctl.seek_time(pctl.playing_time - 10)
		elif inp.media_key == "FastForward":
			pctl.seek_time(pctl.playing_time + 10)
		elif inp.media_key == "Repeat":
			toggle_repeat()
		elif inp.media_key == "Shuffle":
			toggle_random()

		inp.media_key = ""

	if len(load_orders) > 0:
		loading_in_progress = True
		pctl.after_import_flag = True
		tauon.thread_manager.ready("worker")
		if loaderCommand == LC_None:

			# Fliter out files matching CUE filenames
			# This isnt the only mechanism that does this. This one helps in the situation
			# where the user drags and drops multiple files at onec. CUEs in folders are handled elsewhere
			if len(load_orders) > 1:
				for order in load_orders:
					if order.stage == 0 and order.target.endswith(".cue"):
						for order2 in load_orders:
							if not order2.target.endswith(".cue") and\
									os.path.splitext(order2.target)[0] == os.path.splitext(order.target)[0] and\
									os.path.isfile(order2.target):
								order2.stage = -1
				for i in reversed(range(len(load_orders))):
					order = load_orders[i]
					if order.stage == -1:
						del load_orders[i]

			# Prepare loader thread with load order
			for order in load_orders:
				if order.stage == 0:
					order.traget = order.target.replace("\\", "/")
					order.stage = 1
					if os.path.isdir(order.traget):
						loaderCommand = LC_Folder
					else:
						loaderCommand = LC_File
						if order.traget.endswith(".xspf"):
							to_got = "xspf"
							to_get = 0
						else:
							to_got = 1
							to_get = 1
					loaderCommandReady = True
					tauon.thread_manager.ready("worker")
					break

	elif loading_in_progress is True:
		loading_in_progress = False
		pctl.notify_change()

	if loaderCommand == LC_Done:
		loaderCommand = LC_None
		gui.update += 1
		# gui.pl_update = 1
		# loading_in_progress = False

	if update_layout:
		update_layout_do()
		update_layout = False

	# if tauon.worker_save_state and\
	#         not gui.pl_pulse and\
	#         not loading_in_progress and\
	#         not to_scan and\
	#         not plex.scanning and\
	#         not cm_clean_db and\
	#         not lastfm.scanning_friends and\
	#         not move_in_progress:
	#     save_state()
	#     cue_list.clear()
	#     tauon.worker_save_state = False

	# -----------------------------------------------------
	# THEME SWITCHER--------------------------------------------------------------------

	if gui.reload_theme is True:

		gui.pl_update = 1
		theme_files = get_themes()

		if theme > len(theme_files):  # sic
			theme = 0

		if theme > 0:
			theme_number = theme - 1
			try:

				colours.column_colours.clear()
				colours.column_colours_playing.clear()

				theme_item = theme_files[theme_number]

				gui.theme_name = theme_item[1]
				colours.lm = False
				colours.__init__()

				load_theme(colours, Path(theme_item[0]))
				deco.load(colours.deco)
				logging.info("Applying theme: " + gui.theme_name)

				if colours.lm:
					info_icon.colour = [60, 60, 60, 255]
				else:
					info_icon.colour = [61, 247, 163, 255]

				if colours.lm:
					folder_icon.colour = [255, 190, 80, 255]
				else:
					folder_icon.colour = [244, 220, 66, 255]

				if colours.lm:
					settings_icon.colour = [85, 187, 250, 255]
				else:
					settings_icon.colour = [232, 200, 96, 255]

				if colours.lm:
					radiorandom_icon.colour = [120, 200, 120, 255]
				else:
					radiorandom_icon.colour = [153, 229, 133, 255]

			except Exception:
				logging.exception("Error loading theme file")
				raise
				show_message(_("Error loading theme file"), "", mode="warning")

		if theme == 0:
			gui.theme_name = "Mindaro"
			logging.info("Applying default theme: Mindaro")
			colours.lm = False
			colours.__init__()
			colours.post_config()
			deco.unload()

		prefs.theme_name = gui.theme_name

		#logging.info("Theme number: " + str(theme))
		gui.reload_theme = False
		ddt.text_background_colour = colours.playlist_panel_background

	# ---------------------------------------------------------------------------------------------------------
	# GUI DRAWING------
	#logging.info(gui.update)
	#logging.info(gui.lowered)
	if gui.mode == 3:
		gui.pl_update = 0

	if gui.pl_update and not gui.update:
		gui.update = 1

	if gui.update > 0 and not resize_mode:
		gui.update = min(gui.update, 2)

		if reset_render:
			logging.info("Reset render targets!")
			clear_img_cache(delete_disk=False)
			ddt.clear_text_cache()
			for item in WhiteModImageAsset.assets:
				item.reload()
			reset_render = False

		SDL_SetRenderTarget(renderer, None)
		SDL_SetRenderDrawColor(
			renderer, colours.top_panel_background[0], colours.top_panel_background[1],
			colours.top_panel_background[2], colours.top_panel_background[3])
		SDL_RenderClear(renderer)
		SDL_SetRenderTarget(renderer, gui.main_texture)
		SDL_RenderClear(renderer)

		# perf_timer.set()
		gui.update_on_drag = False
		gui.pl_update_on_drag = False

		# mouse_position[0], mouse_position[1] = get_sdl_input.mouse()
		gui.showed_title = False

		if not gui.mouse_in_window and not bottom_bar1.volume_bar_being_dragged and not bottom_bar1.volume_hit and not bottom_bar1.seek_hit:
			mouse_position[0] = -300
			mouse_position[1] = -300

		if gui.clear_image_cache_next:
			gui.clear_image_cache_next -= 1
			album_art_gen.clear_cache()
			style_overlay.radio_meta = None
			if prefs.art_bg:
				tauon.thread_manager.ready("style")

		fields.clear()
		gui.cursor_want = 0

		gui.layer_focus = 0

		if inp.mouse_click or mouse_wheel or right_click:
			mouse_position[0], mouse_position[1] = get_sdl_input.mouse()

		if inp.mouse_click:
			n_click_time = time.time()
			if n_click_time - click_time < 0.42:
				d_mouse_click = True
			click_time = n_click_time

			# Don't register bottom level click when closing message box
			if gui.message_box and pref_box.enabled and not key_focused and not coll(message_box.get_rect()):
				inp.mouse_click = False
				gui.message_box = False

		# Enable the garbage collecter (since we disabled it during startup)
		if ggc > 0:
			if ggc == 2:
				ggc = 1
			elif ggc == 1:
				ggc = 0
				gbc.enable()
				#logging.info("Enabling garbage collecting")

		if gui.mode == 4:
			launch.render()
		elif gui.mode == 1 or gui.mode == 2:

			ddt.text_background_colour = colours.playlist_panel_background

			# Side Bar Draging----------

			if not mouse_down:
				side_drag = False

			rect = (window_size[0] - gui.rspw - 5 * gui.scale, gui.panelY, 12 * gui.scale,
					window_size[1] - gui.panelY - gui.panelBY)
			fields.add(rect)

			if (coll(rect) or side_drag is True) \
				and rename_track_box.active is False \
				and radiobox.active is False \
				and gui.rename_playlist_box is False \
				and gui.message_box is False \
				and pref_box.enabled is False \
				and track_box is False \
				and not gui.rename_folder_box \
				and not Menu.active \
				and (gui.rsp or album_mode) \
				and not artist_info_scroll.held \
				and gui.layer_focus == 0 and gui.show_playlist:

				if side_drag is True:
					draw_sep_hl = True
					# gui.update += 1
					gui.update_on_drag = True

				if inp.mouse_click:
					side_drag = True
					gui.side_bar_drag_source = mouse_position[0]
					gui.side_bar_drag_original = gui.rspw

				if not quick_drag:
					gui.cursor_want = 1

			# side drag update
			if side_drag:

				offset = gui.side_bar_drag_source - mouse_position[0]

				target = gui.side_bar_drag_original + offset

				# Snap to album mode position if close
				if not album_mode and prefs.side_panel_layout == 1:
					if abs(target - gui.pref_gallery_w) < 35 * gui.scale:
						target = gui.pref_gallery_w

				# Reset max ratio if drag drops below ratio width
				if prefs.side_panel_layout == 0:
					if target < round((window_size[1] - gui.panelY - gui.panelBY) * gui.art_aspect_ratio):
						gui.art_max_ratio_lock = gui.art_aspect_ratio

					max_w = round(((window_size[
										1] - gui.panelY - gui.panelBY - 17 * gui.scale) * gui.art_max_ratio_lock) + 17 * gui.scale)
					# 17 here is the art box inset value

				else:
					max_w = window_size[0]

				if not album_mode and target > max_w - 12 * gui.scale:
					target = max_w
					gui.rspw = target
					gui.rsp_full_lock = True

				else:
					gui.rspw = target
					gui.rsp_full_lock = False

				if album_mode:
					pass
					# gui.rspw = target

				if album_mode and gui.rspw < album_mode_art_size + 50 * gui.scale:
					target = album_mode_art_size + 50 * gui.scale

				# Prevent side bar getting too small
				target = max(target, 120 * gui.scale)

				# Remember size for this view mode
				if not album_mode:
					gui.pref_rspw = target
				else:
					gui.pref_gallery_w = target

				update_layout_do()

			# ALBUM GALLERY RENDERING:
			# Gallery view
			# C-AR

			if album_mode:
				try:
					# Arrow key input
					if gal_right:
						gal_right = False
						gal_jump_select(False, 1)
						goto_album(pctl.selected_in_playlist)
						pctl.playlist_view_position = pctl.selected_in_playlist
						logging.debug("Position changed by gallery key press")
						gui.pl_update = 1
					if gal_down:
						gal_down = False
						gal_jump_select(False, row_len)
						goto_album(pctl.selected_in_playlist, down=True)
						pctl.playlist_view_position = pctl.selected_in_playlist
						logging.debug("Position changed by gallery key press")
						gui.pl_update = 1
					if gal_left:
						gal_left = False
						gal_jump_select(True, 1)
						goto_album(pctl.selected_in_playlist)
						pctl.playlist_view_position = pctl.selected_in_playlist
						logging.debug("Position changed by gallery key press")
						gui.pl_update = 1
					if gal_up:
						gal_up = False
						gal_jump_select(True, row_len)
						goto_album(pctl.selected_in_playlist)
						pctl.playlist_view_position = pctl.selected_in_playlist
						logging.debug("Position changed by gallery key press")
						gui.pl_update = 1

					w = gui.rspw

					if window_size[0] < 750 * gui.scale:
						w = window_size[0] - 20 * gui.scale
						if gui.lsp:
							w -= gui.lspw

					x = window_size[0] - w
					h = window_size[1] - gui.panelY - gui.panelBY

					if not gui.show_playlist and inp.mouse_click:
						left = 0
						if gui.lsp:
							left = gui.lspw

						if left < mouse_position[0] < left + 20 * gui.scale and window_size[1] - gui.panelBY > \
								mouse_position[1] > gui.panelY:
							toggle_album_mode()
							inp.mouse_click = False
							mouse_down = False

					rect = [x, gui.panelY, w, h]
					ddt.rect(rect, colours.gallery_background)
					# ddt.rect_r(rect, [255, 0, 0, 200], True)

					area_x = w + 38 * gui.scale
					# area_x = w - 40 * gui.scale

					row_len = int((area_x - album_h_gap) / (album_mode_art_size + album_h_gap))

					#logging.info(row_len)

					compact = 40 * gui.scale
					a_offset = 7 * gui.scale

					l_area = x
					r_area = w
					c_area = r_area // 2 + l_area

					ddt.text_background_colour = colours.gallery_background

					line1_colour = colours.gallery_artist_line
					line2_colour = colours.grey(240)  # colours.side_bar_line1

					if colours.side_panel_background != colours.gallery_background:
						line2_colour = [240, 240, 240, 255]
						line1_colour = alpha_mod([220, 220, 220, 255], 120)

					if test_lumi(colours.gallery_background) < 0.5 or (prefs.use_card_style and colours.lm):
						line1_colour = colours.grey(80)
						line2_colour = colours.grey(40)

					if row_len == 0:
						row_len = 1

					dev = int((r_area - compact) / (row_len + 0))

					render_pos = 0
					album_on = 0

					max_scroll = round(
						(math.ceil((len(album_dex)) / row_len) - 1) * (album_mode_art_size + album_v_gap)) - round(
						50 * gui.scale)

					# Mouse wheel scrolling
					if not search_over.active and not radiobox.active \
							and mouse_position[0] > window_size[0] - w and gui.panelY < mouse_position[1] < window_size[
						1] - gui.panelBY:

						if mouse_wheel != 0:
							scroll_gallery_hide_timer.set()
							gui.frame_callback_list.append(TestTimer(0.9))

						if prefs.gallery_row_scroll:
							gui.album_scroll_px -= mouse_wheel * (album_mode_art_size + album_v_gap)  # 90
						else:
							gui.album_scroll_px -= mouse_wheel * prefs.gallery_scroll_wheel_px

						if gui.album_scroll_px < round(album_v_slide_value * -1):
							gui.album_scroll_px = round(album_v_slide_value * -1)
							if album_dex:
								gallery_pulse_top.pulse()

						if gui.album_scroll_px > max_scroll:
							gui.album_scroll_px = max_scroll
							gui.album_scroll_px = max(gui.album_scroll_px, round(album_v_slide_value * -1))

					rect = (
					gui.gallery_scroll_field_left, gui.panelY, window_size[0] - gui.gallery_scroll_field_left - 2, h)

					card_mode = False
					if prefs.use_card_style and colours.lm and gui.gallery_show_text:
						card_mode = True

					rect = (window_size[0] - 40 * gui.scale, gui.panelY, 38 * gui.scale, h)
					fields.add(rect)

					# Show scroll area
					if coll(rect) or gallery_scroll.held or scroll_gallery_hide_timer.get() < 0.9 or gui.album_tab_mode:

						if gallery_scroll.held:
							while len(tauon.gall_ren.queue) > 2:
								tauon.gall_ren.queue.pop()

						# Draw power bar button
						if gui.pt == 0 and gui.power_bar is not None and len(gui.power_bar) > 3:
							rect = (window_size[0] - (15 + 20) * gui.scale, gui.panelY + 3 * gui.scale, 18 * gui.scale,
									24 * gui.scale)
							fields.add(rect)
							colour = [255, 255, 255, 35]
							if colours.lm:
								colour = [0, 0, 0, 30]
							if coll(rect) and not gallery_scroll.held:
								colour = [255, 220, 100, 245]
								if colours.lm:
									colour = [250, 100, 0, 255]
								if inp.mouse_click:
									gui.pt = 1

							power_bar_icon.render(rect[0] + round(5 * gui.scale), rect[1] + round(3 * gui.scale), colour)

						# Draw scroll bar
						if gui.pt == 0:
							gui.album_scroll_px = gallery_scroll.draw(
								window_size[0] - 16 * gui.scale, gui.panelY,
								15 * gui.scale,
								window_size[1] - (gui.panelY + gui.panelBY),
								gui.album_scroll_px + album_v_slide_value,
								max_scroll + album_v_slide_value,
								jump_distance=1400 * gui.scale,
								r_click=right_click,
								extend_field=15 * gui.scale) - album_v_slide_value

					if last_row != row_len:
						last_row = row_len

						if pctl.selected_in_playlist < len(pctl.playing_playlist()):
							goto_album(pctl.selected_in_playlist)
						# else:
						#     goto_album(pctl.playlist_playing_position)

					extend = 0
					if card_mode:  # gui.gallery_show_text:
						extend = 40 * gui.scale

					# Process inputs first
					if (inp.mouse_click or right_click or middle_click or mouse_down or mouse_up) and default_playlist:
						while render_pos < gui.album_scroll_px + window_size[1]:

							if b_info_bar and render_pos > gui.album_scroll_px + b_info_y:
								break

							if render_pos < gui.album_scroll_px - album_mode_art_size - album_v_gap:
								# Skip row
								render_pos += album_mode_art_size + album_v_gap
								album_on += row_len
							else:
								# render row
								y = render_pos - gui.album_scroll_px
								row_x = 0
								for a in range(row_len):
									if album_on > len(album_dex) - 1:
										break

									x = (l_area + dev * a) - int(album_mode_art_size / 2) + int(dev / 2) + int(
										compact / 2) - a_offset

									if album_dex[album_on] > len(default_playlist):
										break

									rect = (x, y, album_mode_art_size, album_mode_art_size + extend * gui.scale)
									# fields.add(rect)
									m_in = coll(rect) and gui.panelY < mouse_position[1] < window_size[1] - gui.panelBY

									# if m_in:
									#     ddt.rect_r((x - 7, y - 7, album_mode_art_size + 14, album_mode_art_size + extend + 55), [80, 80, 80, 80], True)

									# Quick drag and drop
									if mouse_up and (playlist_hold and m_in) and not side_drag and shift_selection:

										info = get_album_info(album_dex[album_on])
										if info[1]:

											track_position = info[1][0]

											if track_position > shift_selection[0]:
												track_position = info[1][-1] + 1

											ref = []
											for item in shift_selection:
												ref.append(default_playlist[item])

											for item in shift_selection:
												default_playlist[item] = "old"

											for item in shift_selection:
												default_playlist.insert(track_position, "new")

											for b in reversed(range(len(default_playlist))):
												if default_playlist[b] == "old":
													del default_playlist[b]
											shift_selection = []
											for b in range(len(default_playlist)):
												if default_playlist[b] == "new":
													shift_selection.append(b)
													default_playlist[b] = ref.pop(0)

											pctl.selected_in_playlist = shift_selection[0]
											gui.pl_update += 1
											playlist_hold = False

											reload_albums(True)
											pctl.notify_change()

									elif not side_drag and is_level_zero():

										if coll_point(click_location, rect) and gui.panelY < mouse_position[1] < \
												window_size[1] - gui.panelBY:
											info = get_album_info(album_dex[album_on])

											if m_in and mouse_up and prefs.gallery_single_click:

												if is_level_zero() and gui.d_click_ref == album_dex[album_on]:

													if info[0] == 1 and pctl.playing_state == 2:
														pctl.play()
													elif info[0] == 1 and pctl.playing_state > 0:
														pctl.playlist_view_position = album_dex[album_on]
														logging.debug("Position changed by gallery click")
													else:
														pctl.playlist_view_position = album_dex[album_on]
														logging.debug("Position changed by gallery click")
														pctl.jump(default_playlist[album_dex[album_on]], album_dex[album_on])

													pctl.show_current()

											elif mouse_down and not m_in:
												info = get_album_info(album_dex[album_on])
												quick_drag = True
												if not pl_is_locked(pctl.active_playlist_viewing) or key_shift_down:
													playlist_hold = True
												shift_selection = info[1]
												gui.pl_update += 1
												click_location = [0, 0]

									if m_in:

										info = get_album_info(album_dex[album_on])
										if inp.mouse_click:

											if prefs.gallery_single_click:
												gui.d_click_ref = album_dex[album_on]

											else:

												if d_click_timer.get() < 0.5 and gui.d_click_ref == album_dex[album_on]:

													if info[0] == 1 and pctl.playing_state == 2:
														pctl.play()
													elif info[0] == 1 and pctl.playing_state > 0:
														pctl.playlist_view_position = album_dex[album_on]
														logging.debug("Position changed by gallery click")
													else:
														pctl.playlist_view_position = album_dex[album_on]
														logging.debug("Position changed by gallery click")
														pctl.jump(default_playlist[album_dex[album_on]], album_dex[album_on])

												else:
													gui.d_click_ref = album_dex[album_on]
													d_click_timer.set()

												pctl.playlist_view_position = album_dex[album_on]
												logging.debug("Position changed by gallery click")
												pctl.selected_in_playlist = album_dex[album_on]
												gui.pl_update += 1

										elif middle_click and is_level_zero():
											# Middle click to add album to queue
											if key_ctrl_down:
												# Add to queue ungrouped
												album = get_album_info(album_dex[album_on])[1]
												for item in album:
													pctl.force_queue.append(
														queue_item_gen(default_playlist[item], item, pl_to_id(
															pctl.active_playlist_viewing)))
												queue_timer_set(plural=True)
												if prefs.stop_end_queue:
													pctl.auto_stop = False
											else:
												# Add to queue grouped
												add_album_to_queue(default_playlist[album_dex[album_on]])

										elif right_click:
											if pctl.quick_add_target:

												pl = id_to_pl(pctl.quick_add_target)
												if pl is not None:
													parent = pctl.get_track(
														default_playlist[album_dex[album_on]]).parent_folder_path
													# remove from target pl
													if default_playlist[album_dex[album_on]] in pctl.multi_playlist[pl].playlist_ids:
														for i in reversed(range(len(pctl.multi_playlist[pl].playlist_ids))):
															if pctl.get_track(pctl.multi_playlist[pl].playlist_ids[i]).parent_folder_path == parent:
																del pctl.multi_playlist[pl].playlist_ids[i]
													else:
														# add
														for i in range(len(default_playlist)):
															if pctl.get_track(default_playlist[i]).parent_folder_path == parent:
																pctl.multi_playlist[pl].playlist_ids.append(default_playlist[i])

												reload_albums(True)

											else:
												pctl.selected_in_playlist = album_dex[album_on]
												# playlist_position = pctl.playlist_selected
												shift_selection = [pctl.selected_in_playlist]
												gallery_menu.activate(default_playlist[pctl.selected_in_playlist])
												r_menu_position = pctl.selected_in_playlist

												shift_selection = []
												u = pctl.selected_in_playlist
												while u < len(default_playlist) and pctl.master_library[
													default_playlist[u]].parent_folder_path == \
														pctl.master_library[
															default_playlist[pctl.selected_in_playlist]].parent_folder_path:
													shift_selection.append(u)
													u += 1
												pctl.render_playlist()

									album_on += 1

								if album_on > len(album_dex):
									break
								render_pos += album_mode_art_size + album_v_gap

					render_pos = 0
					album_on = 0
					album_count = 0

					if not pref_box.enabled or mouse_wheel != 0:
						gui.first_in_grid = None

					# Render album grid
					while render_pos < gui.album_scroll_px + window_size[1] and default_playlist:

						if b_info_bar and render_pos > gui.album_scroll_px + b_info_y:
							break

						if render_pos < gui.album_scroll_px - album_mode_art_size - album_v_gap:
							# Skip row
							render_pos += album_mode_art_size + album_v_gap
							album_on += row_len
						else:
							# render row
							y = render_pos - gui.album_scroll_px

							row_x = 0

							if y > window_size[1] - gui.panelBY - 30 * gui.scale and window_size[1] < 340 * gui.scale:
								break
							# if y >

							for a in range(row_len):

								if album_on > len(album_dex) - 1:
									break

								x = (l_area + dev * a) - int(album_mode_art_size / 2) + int(dev / 2) + int(
									compact / 2) - a_offset

								if album_dex[album_on] > len(default_playlist):
									break

								track = pctl.master_library[default_playlist[album_dex[album_on]]]

								info = get_album_info(album_dex[album_on])
								album = info[1]
								# info = (0, 0, 0)

								# rect = (x, y, album_mode_art_size, album_mode_art_size + extend * gui.scale)
								# fields.add(rect)
								# m_in = coll(rect) and gui.panelY < mouse_position[1] < window_size[1] - gui.panelBY

								if gui.first_in_grid is None and y > gui.panelY:  # This marks what track is the first in the grid
									gui.first_in_grid = album_dex[album_on]

								# artisttitle = colours.side_bar_line2
								# albumtitle = colours.side_bar_line1  # grey(220)

								if card_mode:
									ddt.text_background_colour = colours.grey(250)
									drop_shadow.render(
										x + 3 * gui.scale, y + 3 * gui.scale,
										album_mode_art_size + 11 * gui.scale,
										album_mode_art_size + 45 * gui.scale + 13 * gui.scale)
									ddt.rect(
										(x, y, album_mode_art_size, album_mode_art_size + 45 * gui.scale), colours.grey(250))

								# White background needs extra border
								if colours.lm and not card_mode:
									ddt.rect_a((x - 2, y - 2), (album_mode_art_size + 4, album_mode_art_size + 4), colours.grey(200))

								if a == row_len - 1:
									gui.gallery_scroll_field_left = max(
										x + album_mode_art_size,
										window_size[0] - round(50 * gui.scale))

								if info[0] == 1 and 0 < pctl.playing_state < 3:
									ddt.rect_a(
										(x - 4, y - 4), (album_mode_art_size + 8, album_mode_art_size + 8),
										colours.gallery_highlight)
									# ddt.rect_a((x, y), (album_mode_art_size, album_mode_art_size),
									#            colours.gallery_background, True)

								# Draw quick add highlight
								if pctl.quick_add_target:
									pl = id_to_pl(pctl.quick_add_target)
									if pl is not None and default_playlist[album_dex[album_on]] in \
											pctl.multi_playlist[pl].playlist_ids:
										c = [110, 233, 90, 255]
										if colours.lm:
											c = [66, 244, 66, 255]
										ddt.rect_a((x - 4, y - 4), (album_mode_art_size + 8, album_mode_art_size + 8), c)

								# Draw transcode highlight
								if transcode_list and os.path.isdir(prefs.encoder_output):

									tr = False

									if (encode_folder_name(track) in os.listdir(prefs.encoder_output)):
										tr = True
									else:
										for folder in transcode_list:
											if pctl.get_track(folder[0]).parent_folder_path == track.parent_folder_path:
												tr = True
												break
									if tr:
										c = [244, 212, 66, 255]
										if colours.lm:
											c = [244, 64, 244, 255]
										ddt.rect_a((x - 4, y - 4), (album_mode_art_size + 8, album_mode_art_size + 8), c)
										# ddt.rect_a((x, y), (album_mode_art_size, album_mode_art_size),
										#            colours.gallery_background, True)

								# Draw selection

								if (gui.album_tab_mode or gallery_menu.active) and info[2] is True:
									c = colours.gallery_highlight
									c = [c[1], c[2], c[0], c[3]]
									ddt.rect_a((x - 4, y - 4), (album_mode_art_size + 8, album_mode_art_size + 8), c)  # [150, 80, 222, 255]
									# ddt.rect_a((x, y), (album_mode_art_size, album_mode_art_size),
									#            colours.gallery_background, True)

								# Draw selection animation
								if gui.gallery_animate_highlight_on == album_dex[
									album_on] and gallery_select_animate_timer.get() < 1.5:

									t = gallery_select_animate_timer.get()
									c = colours.gallery_highlight
									if t < 0.2:
										a = int(255 * (t / 0.2))
									elif t < 0.5:
										a = 255
									else:
										a = int(255 - 255 * (t - 0.5))

									c = [c[1], c[2], c[0], a]
									ddt.rect_a((x - 5, y - 5), (album_mode_art_size + 10, album_mode_art_size + 10), c)  # [150, 80, 222, 255]

									gui.update += 1

								# Draw faint outline
								ddt.rect(
									(x - 1, y - 1, album_mode_art_size + 2, album_mode_art_size + 2),
									[255, 255, 255, 11])

								if gui.album_tab_mode or gallery_menu.active:
									if info[2] is False and info[0] != 1 and not colours.lm:
										ddt.rect_a((x, y), (album_mode_art_size, album_mode_art_size), [0, 0, 0, 110])
										albumtitle = colours.grey(160)

								elif info[0] != 1 and pctl.playing_state != 0 and prefs.dim_art:
									ddt.rect_a((x, y), (album_mode_art_size, album_mode_art_size), [0, 0, 0, 110])
									albumtitle = colours.grey(160)

								# Determine meta info
								singles = False
								artists = 0
								last_album = ""
								last_artist = ""
								s = 0
								ones = 0
								for id in album:
									tr = pctl.get_track(default_playlist[id])
									if tr.album != last_album:
										if last_album:
											s += 1
										last_album = tr.album
										if str(tr.track_number) == "1":
											ones += 1
									if tr.artist != last_artist:
										artists += 1
								if s > 2 or ones > 2:
									singles = True

								# Draw blank back colour
								back_colour = [40, 40, 40, 50]
								if colours.lm:
									back_colour = [10, 10, 10, 15]

								back_colour = alpha_blend([10, 10, 10, 15], colours.gallery_background)

								ddt.rect_a((x, y), (album_mode_art_size, album_mode_art_size), back_colour)

								# Draw album art
								if singles:
									dia = math.sqrt(album_mode_art_size * album_mode_art_size * 2)
									ran = dia * 0.25
									off = (dia - ran) / 2
									albs = min(len(album), 5)
									spacing = ran / (albs - 1)
									size = round(album_mode_art_size * 0.5)

									i = 0
									for p in album[:albs]:

										pp = spacing * i
										pp += off
										xx = pp / math.sqrt(2)

										xx -= size / 2
										drawn_art = tauon.gall_ren.render(
											pctl.get_track(default_playlist[p]), (x + xx, y + xx),
											size=size, force_offset=0)
										if not drawn_art:
											g = 50 + round(100 / albs) * i
											ddt.rect((x + xx, y + xx, size, size), [g, g, g, 100])
										drawn_art = True
										i += 1

								else:
									album_count += 1
									if (album_count * 1.5) + 10 > tauon.gall_ren.limit:
										tauon.gall_ren.limit = round((album_count * 1.5) + 30)
									drawn_art = tauon.gall_ren.render(track, (x, y))

								# Determine mouse collision
								rect = (x, y, album_mode_art_size, album_mode_art_size + extend * gui.scale)
								m_in = coll(rect) and gui.panelY < mouse_position[1] < window_size[1] - gui.panelBY
								fields.add(rect)

								# Draw mouse-over highlight
								if (not gallery_menu.active and m_in) or (gallery_menu.active and info[2]):
									if is_level_zero():
										ddt.rect(rect, [255, 255, 255, 10])

								if drawn_art is False and gui.gallery_show_text is False:
									ddt.text(
										(x + int(album_mode_art_size / 2), y + album_mode_art_size - 22 * gui.scale, 2),
										pctl.master_library[default_playlist[album_dex[album_on]]].parent_folder_name,
										colours.gallery_artist_line,
										13,
										album_mode_art_size - 15 * gui.scale,
										bg=alpha_blend(back_colour, colours.gallery_background))

								if prefs.art_bg and drawn_art:
									rect = SDL_Rect(round(x), round(y), album_mode_art_size, album_mode_art_size)
									if rect.y < gui.panelY:
										diff = round(gui.panelY - rect.y)
										rect.y += diff
										rect.h -= diff
									elif (rect.y + rect.h) > window_size[1] - gui.panelBY:
										diff = round((rect.y + rect.h) - (window_size[1] - gui.panelBY))
										rect.h -= diff

									if rect.h > 0:
										style_overlay.hole_punches.append(rect)

								# # Drag over highlight
								# if quick_drag and playlist_hold and mouse_down:
								#     rect = (x, y, album_mode_art_size, album_mode_art_size + extend * gui.scale)
								#     m_in = coll(rect) and gui.panelY < mouse_position[1] < window_size[1] - gui.panelBY
								#     if m_in:
								#         ddt.rect_a((x, y), (album_mode_art_size, album_mode_art_size), [120, 10, 255, 100], True)

								if gui.gallery_show_text:
									c_index = default_playlist[album_dex[album_on]]

									if c_index in album_artist_dict:
										pass
									else:
										i = album_dex[album_on]
										if pctl.master_library[default_playlist[i]].album_artist:
											album_artist_dict[c_index] = pctl.master_library[
												default_playlist[i]].album_artist
										else:
											while i < len(default_playlist) - 1:
												if pctl.master_library[default_playlist[i]].parent_folder_name != \
														pctl.master_library[
															default_playlist[album_dex[album_on]]].parent_folder_name:
													album_artist_dict[c_index] = pctl.master_library[
														default_playlist[album_dex[album_on]]].artist
													break
												if pctl.master_library[default_playlist[i]].artist != \
														pctl.master_library[
															default_playlist[album_dex[album_on]]].artist:
													album_artist_dict[c_index] = _("Various Artists")

													break
												i += 1
											else:
												album_artist_dict[c_index] = pctl.master_library[
													default_playlist[album_dex[album_on]]].artist

									line = album_artist_dict[c_index]
									line2 = pctl.master_library[default_playlist[album_dex[album_on]]].album
									if singles:
										line2 = pctl.master_library[
											default_playlist[album_dex[album_on]]].parent_folder_name
										if artists > 1:
											line = _("Various Artists")

									text_align = 0
									if prefs.center_gallery_text:
										x += album_mode_art_size // 2
										text_align = 2
									elif card_mode:
										x += round(6 * gui.scale)

									if card_mode:

										if line2 == "":

											ddt.text(
												(x, y + album_mode_art_size + 8 * gui.scale, text_align),
												line,
												line1_colour,
												310,
												album_mode_art_size - 18 * gui.scale)
										else:

											ddt.text(
												(x, y + album_mode_art_size + 7 * gui.scale, text_align),
												line2,
												line2_colour,
												311,
												album_mode_art_size - 18 * gui.scale)

											ddt.text(
												(x, y + album_mode_art_size + (10 + 14) * gui.scale, text_align),
												line,
												line1_colour,
												10,
												album_mode_art_size - 18 * gui.scale)
									elif line2 == "":

										ddt.text(
											(x, y + album_mode_art_size + 9 * gui.scale, text_align),
											line,
											line1_colour,
											311,
											album_mode_art_size - 5 * gui.scale)
									else:

										ddt.text(
											(x, y + album_mode_art_size + 8 * gui.scale, text_align),
											line2,
											line2_colour,
											212,
											album_mode_art_size)

										ddt.text(
											(x, y + album_mode_art_size + (10 + 14) * gui.scale, text_align),
											line,
											line1_colour,
											311,
											album_mode_art_size - 5 * gui.scale)

								album_on += 1

							if album_on > len(album_dex):
								break
							render_pos += album_mode_art_size + album_v_gap

					# POWER TAG BAR --------------

					if gui.pt > 0:  # gui.pt > 0 or (gui.power_bar is not None and len(gui.power_bar) > 1):

						top = gui.panelY
						run_y = top + 1

						hot_r = (window_size[0] - 47 * gui.scale, top, 45 * gui.scale, h)
						fields.add(hot_r)

						if gui.pt == 0:  # mouse moves in
							if coll(hot_r) and window_is_focused():
								gui.pt_on.set()
								gui.pt = 1
						elif gui.pt == 1:  # wait then trigger if stays, reset if goes out
							if not coll(hot_r):
								gui.pt = 0
							elif gui.pt_on.get() > 0.2:
								gui.pt = 2

								off = 0
								for item in gui.power_bar:
									item.ani_timer.force_set(off)
									off -= 0.005

						elif gui.pt == 2:  # wait to turn off

							if coll(hot_r):
								gui.pt_off.set()
							if gui.pt_off.get() > 0.6 and not lightning_menu.active:
								gui.pt = 3

								off = 0
								for item in gui.power_bar:
									item.ani_timer.force_set(off)
									off -= 0.01

						done = True
						# Animate tages on
						if gui.pt == 2:
							for item in gui.power_bar:
								t = item.ani_timer.get()
								if t < 0:
									break
								if t > 0.2:
									item.peak_x = 9 * gui.scale
								else:
									item.peak_x = (t / 0.2) * 9 * gui.scale

						# Animate tags off
						if gui.pt == 3:
							for item in gui.power_bar:
								t = item.ani_timer.get()
								if t < 0:
									done = False
									break
								if t > 0.2:
									item.peak_x = 0
								else:
									item.peak_x = 9 * gui.scale - ((t / 0.2) * 9 * gui.scale)
									done = False
							if done:
								gui.pt = 0
								gui.update += 1

						# Keep draw loop running while on
						if gui.pt > 0:
							gui.update = 2

						# Draw tags

						block_h = round(27 * gui.scale)
						block_gap = 1 * gui.scale
						if gui.scale == 1.25:
							block_gap = 1

						if coll(hot_r) or gui.pt > 0:

							for i, item in enumerate(gui.power_bar):

								if run_y + block_h > top + h:
									break

								rect = [window_size[0] - item.peak_x, run_y, 7 * gui.scale, block_h]
								i_rect = [window_size[0] - 36 * gui.scale, run_y, 34 * gui.scale, block_h]
								fields.add(i_rect)

								if (coll(i_rect) or (
									lightning_menu.active and lightning_menu.reference == item)) and item.peak_x == 9 * gui.scale:

									if not lightning_menu.active or lightning_menu.reference == item or right_click:

										minx = 100 * gui.scale
										maxx = minx * 2

										ww = ddt.get_text_w(item.name, 213)

										w = max(minx, ww)
										w = min(maxx, w)

										ddt.rect(
											(rect[0] - w - 25 * gui.scale, run_y, w + 26 * gui.scale, block_h),
											[230, 230, 230, 255])
										ddt.text(
											(rect[0] - 10 * gui.scale, run_y + 5 * gui.scale, 1), item.name,
											[5, 5, 5, 255], 213, w, bg=[230, 230, 230, 255])

										if inp.mouse_click:
											goto_album(item.position)
										if right_click:
											lightning_menu.activate(item, position=(
											window_size[0] - 180 * gui.scale, rect[1] + rect[3] + 5 * gui.scale))
										if middle_click:
											path_stem_to_playlist(item.path, item.name)

								ddt.rect(rect, item.colour)
								run_y += block_h + block_gap

					gallery_pulse_top.render(
						window_size[0] - gui.rspw, gui.panelY, gui.rspw - round(16 * gui.scale), 20 * gui.scale)
				except Exception:
					logging.exception("Gallery render error!")
				# END POWER BAR ------------------------

			# End of gallery view
			# --------------------------------------------------------------------------
			# Main Playlist:
			if len(load_orders) > 0:

				for i, order in enumerate(load_orders):
					if order.stage == 2:
						target_pl = 0

						# Sort the tracks by track number
						sort_track_2(None, order.tracks)

						for p, playlist in enumerate(pctl.multi_playlist):
							if playlist.uuid_int == order.playlist:
								target_pl = p
								break
						else:
							del load_orders[i]
							logging.error("Target playlist lost")
							break

						if order.replace_stem:
							for ii, id in reversed(list(enumerate(pctl.multi_playlist[target_pl].playlist_ids))):
								pfp = pctl.get_track(id).parent_folder_path
								if pfp.startswith(order.target.replace("\\", "/")):
									if pfp.rstrip("/\\") == order.target.rstrip("/\\") or \
											(len(pfp) > len(order.target) and pfp[
												len(order.target.rstrip("/\\"))] in ("/", "\\")):
										del pctl.multi_playlist[target_pl].playlist_ids[ii]

						#logging.info(order.tracks)
						if order.playlist_position is not None:
							#logging.info(order.playlist_position)
							pctl.multi_playlist[target_pl].playlist_ids[
							order.playlist_position:order.playlist_position] = order.tracks
						# else:

						else:
							pctl.multi_playlist[target_pl].playlist_ids += order.tracks

						pctl.update_shuffle_pool(pctl.multi_playlist[target_pl].uuid_int)

						gui.update += 2
						gui.pl_update += 2
						if order.notify and gui.message_box and len(load_orders) == 1:
							show_message(_("Rescan folders complete."), mode="done")
						reload()
						tree_view_box.clear_target_pl(target_pl)

						if order.play and order.tracks:

							for p, plst in enumerate(pctl.multi_playlist):
								if order.tracks[0] in plst.playlist_ids:
									target_pl = p
									break

							switch_playlist(target_pl)

							pctl.active_playlist_playing = pctl.active_playlist_viewing

							# If already in playlist, delete latest add
							if pctl.multi_playlist[target_pl].title == "Default":
								if default_playlist.count(order.tracks[0]) > 1:
									for q in reversed(range(len(default_playlist))):
										if default_playlist[q] == order.tracks[0]:
											del default_playlist[q]
											break

							pctl.jump(order.tracks[0], pl_position=default_playlist.index(order.tracks[0]))

							pctl.show_current(True, True, True, True, True)

						del load_orders[i]

						# Are there more orders for this playlist?
						# If not, decide on a name for the playlist
						for item in load_orders:
							if item.playlist == order.playlist:
								break
						else:

							if _("New Playlist") in pctl.multi_playlist[target_pl].title:
								auto_name_pl(target_pl)

							if prefs.auto_sort:
								if pctl.multi_playlist[target_pl].locked:
									show_message(_("Auto sort skipped because playlist is locked."))
								else:
									logging.info("Auto sorting")
									standard_sort(target_pl)
									year_sort(target_pl)

						if not load_orders:
							loading_in_progress = False
							pctl.notify_change()
							gui.auto_play_import = False
							album_artist_dict.clear()
						break

			if gui.show_playlist:

				# playlist hit test
				if coll((
						gui.playlist_left, gui.playlist_top, gui.plw,
						window_size[1] - gui.panelY - gui.panelBY)) and not drag_mode and (
						inp.mouse_click or mouse_wheel != 0 or right_click or middle_click or mouse_up or mouse_down):
					gui.pl_update = 1

				if gui.combo_mode and mouse_wheel != 0:
					gui.pl_update = 1

				# MAIN PLAYLIST
				# C-PR

				top = gui.panelY
				if gui.artist_info_panel:
					top += gui.artist_panel_height

				if gui.set_mode and not gui.set_bar:
					left = 0
					if gui.lsp:
						left = gui.lspw
					rect = [left, top, gui.plw, 12 * gui.scale]
					if right_click and coll(rect):
						set_menu_hidden.activate()
						right_click = False

				width = gui.plw
				if gui.set_bar and gui.set_mode:
					left = 0
					if gui.lsp:
						left = gui.lspw

					if gui.tracklist_center_mode:
						left = gui.tracklist_inset_left - round(20 * gui.scale)
						width = gui.tracklist_inset_width + round(20 * gui.scale)

					rect = [left, top, width, gui.set_height]
					start = left + 16 * gui.scale
					run = 0
					in_grip = False

					if not mouse_down and gui.set_hold != -1:
						gui.set_hold = -1

					for h, item in enumerate(gui.pl_st):
						box = (start + run, rect[1], item[1], rect[3])
						grip = (start + run, rect[1], 3 * gui.scale, rect[3])
						m_grip = (grip[0] - 4 * gui.scale, grip[1], grip[2] + 8 * gui.scale, grip[3])
						l_grip = (grip[0] + 9 * gui.scale, grip[1], box[2] - 14 * gui.scale, grip[3])
						fields.add(m_grip)

						if coll(l_grip):
							if mouse_up and gui.set_label_hold != -1:
								if point_distance(mouse_position, gui.set_label_point) < 8 * gui.scale:
									sort_direction = 0
									if h != gui.column_d_click_on or gui.column_d_click_timer.get() > 2.5:
										gui.column_d_click_timer.set()
										gui.column_d_click_on = h

										sort_direction = 1

										gui.column_sort_ani_direction = 1
										gui.column_sort_ani_x = start + run + item[1]

									elif gui.column_d_click_on == h:
										gui.column_d_click_on = -1
										gui.column_d_click_timer.force_set(10)

										sort_direction = -1

										gui.column_sort_ani_direction = -1
										gui.column_sort_ani_x = start + run + item[1]

									if sort_direction:

										if gui.pl_st[h][0] in {"Starline", "Rating", "❤", "P", "S", "Time", "Date"}:
											sort_direction *= -1

										if sort_direction == 1:
											sort_ass(h)
										else:
											sort_ass(h, True)
										gui.column_sort_ani_timer.set()

								else:
									gui.column_d_click_on = -1
									if h != gui.set_label_hold:
										dest = h
										if dest > gui.set_label_hold:
											dest += 1
										temp = gui.pl_st[gui.set_label_hold]
										gui.pl_st[gui.set_label_hold] = "old"
										gui.pl_st.insert(dest, temp)
										gui.pl_st.remove("old")

										gui.pl_update = 1
										gui.set_label_hold = -1
										#logging.info("MOVE")
										break

									gui.set_label_hold = -1

							if inp.mouse_click:
								gui.set_label_hold = h
								gui.set_label_point = copy.deepcopy(mouse_position)
							if right_click:
								set_menu.activate(h)

						if h != 0:
							if coll(m_grip):
								in_grip = True
								if inp.mouse_click:
									gui.set_hold = h
									gui.set_point = mouse_position[0]
									gui.set_old = gui.pl_st[h - 1][1]

							if mouse_down and gui.set_hold == h:
								gui.pl_st[h - 1][1] = gui.set_old + (mouse_position[0] - gui.set_point)
								gui.pl_st[h - 1][1] = max(gui.pl_st[h - 1][1], 25)

								gui.update = 1
								# gui.pl_update = 1

								total = 0
								for i in range(len(gui.pl_st) - 1):
									total += gui.pl_st[i][1]

								wid = gui.plw - round(16 * gui.scale)
								if gui.tracklist_center_mode:
									wid = gui.tracklist_highlight_width - round(16 * gui.scale)
								gui.pl_st[len(gui.pl_st) - 1][1] = wid - total

						run += item[1]

					if not mouse_down:
						gui.set_label_hold = -1
					#logging.info(in_grip)
					if gui.set_label_hold == -1:
						if in_grip and not x_menu.active and not view_menu.active and not tab_menu.active and not set_menu.active:
							gui.cursor_want = 1
						if gui.set_hold != -1:
							gui.cursor_want = 1
							gui.pl_update_on_drag = True

				# heart field test
				if gui.heart_fields:
					for field in gui.heart_fields:
						fields.add(field, update_playlist_call)

				if gui.pl_update > 0:
					gui.rendered_playlist_position = playlist_view_position

					gui.pl_update -= 1
					if gui.combo_mode:
						if gui.radio_view:
							radio_view.render()
						elif gui.showcase_mode:
							showcase.render()


						# else:
						#     combo_pl_render.full_render()
					else:
						gui.heart_fields.clear()
						playlist_render.full_render()

				elif gui.combo_mode:
					if gui.radio_view:
						radio_view.render()
					elif gui.showcase_mode:
						showcase.render()
					# else:
					#     combo_pl_render.cache_render()
				else:
					playlist_render.cache_render()

				if gui.combo_mode and key_esc_press and is_level_zero():
					exit_combo()

				if not gui.set_bar and gui.set_mode and not gui.combo_mode:
					width = gui.plw
					left = 0
					if gui.lsp:
						left = gui.lspw
					if gui.tracklist_center_mode:
						left = gui.tracklist_highlight_left
						width = gui.tracklist_highlight_width
					rect = [left, top, width, gui.set_height // 2.5]
					fields.add(rect)
					gui.delay_frame(0.26)

					if coll(rect) and gui.bar_hover_timer.get() > 0.25:
						ddt.rect(rect, colours.column_bar_background)
						if inp.mouse_click:
							gui.set_bar = True
							update_layout_do()
					if not coll(rect):
						gui.bar_hover_timer.set()

				if gui.set_bar and gui.set_mode and not gui.combo_mode:

					x = 0
					if gui.lsp:
						x = gui.lspw

					width = gui.plw

					if gui.tracklist_center_mode:
						x = gui.tracklist_highlight_left
						width = gui.tracklist_highlight_width

					rect = [x, top, width, gui.set_height]

					c_bar_background = colours.column_bar_background

					# if colours.lm:
					#     c_bar_background = [235, 110, 160, 255]

					if gui.tracklist_center_mode:
						ddt.rect((0, top, window_size[0], gui.set_height), c_bar_background)
					else:
						ddt.rect(rect, c_bar_background)

					start = x + 16 * gui.scale
					c_width = width - 16 * gui.scale

					run = 0

					for i, item in enumerate(gui.pl_st):

						# if run > rect[2] - 55 * gui.scale:
						#     break

						wid = item[1]

						if run + wid > c_width:
							wid = c_width - run

						if run > c_width - 22 * gui.scale:
							break

						# if run > c_width - 20 * gui.scale:
						#     run = run - 20 * gui.scale

						wid = max(0, wid)

						# ddt.rect_r((run, 40, wid, 10), [255, 0, 0, 100])
						box = (start + run, rect[1], wid, rect[3])

						grip = (start + run, rect[1], 3 * gui.scale, rect[3])

						bg = c_bar_background

						if coll(box) and gui.set_label_hold != -1:
							bg = [39, 39, 39, 255]

						if i == gui.set_label_hold:
							bg = [22, 22, 22, 255]

						ddt.rect(box, bg)
						ddt.rect(grip, colours.column_grip)

						line = _(item[0])
						ddt.text_background_colour = bg

						# # Remove columns if positioned out of view
						# if box[0] + 10 * gui.scale > start + (gui.plw - 25 * gui.scale):
						#
						#     if box[0] + 10 * gui.scale > start + gui.plw:
						#         del gui.pl_st[i]
						#
						#     i += 1
						#     while i < len(gui.pl_st):
						#         del gui.pl_st[i]
						#         i += 1
						#
						#     break
						if line == "❤":
							heart_row_icon.render(box[0] + 9 * gui.scale, top + 8 * gui.scale, colours.column_bar_text)
						else:
							ddt.text(
								(box[0] + 10 * gui.scale, top + 4 * gui.scale), line, colours.column_bar_text, 312,
								bg=bg, max_w=box[2] - 25 * gui.scale)

						run += box[2]

					t = gui.column_sort_ani_timer.get()
					if t < 0.30:
						gui.update += 1
						x = round(gui.column_sort_ani_x - 22 * gui.scale)
						p = t / 0.30

						if gui.column_sort_ani_direction == 1:
							y = top + 8 * p + 3 * gui.scale
							gui.column_sort_down_icon.render(x, round(y), [255, 255, 255, 90])
						else:
							p = 1 - p
							y = top + 8 * p + 2 * gui.scale
							gui.column_sort_up_icon.render(x, round(y), [255, 255, 255, 90])

				# Switch Vis:
				if right_click and coll(
					(window_size[0] - 130 * gui.scale - gui.offset_extra, 0, 125 * gui.scale,
					gui.panelY)) and not gui.top_bar_mode2:
					vis_menu.activate(None, (window_size[0] - 100 * gui.scale - gui.offset_extra, 30 * gui.scale))
				elif right_click and top_panel.tabs_right_x < mouse_position[0] and \
						mouse_position[1] < gui.panelY and \
						mouse_position[0] > top_panel.tabs_right_x and \
						mouse_position[0] < window_size[0] - 130 * gui.scale - gui.offset_extra:

					window_menu.activate(None, (mouse_position[0], 30 * gui.scale))

				elif middle_click and top_panel.tabs_right_x < mouse_position[0] and \
						mouse_position[1] < gui.panelY and \
						mouse_position[0] > top_panel.tabs_right_x and \
						mouse_position[0] < window_size[0] - gui.offset_extra:

					do_minimize_button()

				# edge_playlist.render(gui.playlist_left, gui.panelY, gui.plw, 2 * gui.scale)

				bottom_playlist2.render(gui.playlist_left, window_size[1] - gui.panelBY, gui.plw, 25 * gui.scale,
										bottom=True)
				# --------------------------------------------
				# ALBUM ART

				# Right side panel drawing

				if gui.rsp and not album_mode:
					gui.showing_l_panel = False
					target_track = pctl.show_object()

					if middle_click:
						if coll(
							(window_size[0] - gui.rspw, gui.panelY, gui.rspw,
							window_size[1] - gui.panelY - gui.panelBY)):

							if (target_track and target_track.lyrics and prefs.show_lyrics_side) or \
									(
											prefs.show_lyrics_side and prefs.prefer_synced_lyrics and target_track is not None and timed_lyrics_ren.generate(
										target_track)):

								prefs.show_lyrics_side ^= True
								prefs.side_panel_layout = 1
							else:

								if prefs.side_panel_layout == 0:

									if (target_track and target_track.lyrics and not prefs.show_lyrics_side) or \
											(
													prefs.prefer_synced_lyrics and target_track is not None and timed_lyrics_ren.generate(
												target_track)):
										prefs.show_lyrics_side = True
										prefs.side_panel_layout = 1
									else:
										prefs.side_panel_layout = 1
								else:
									prefs.side_panel_layout = 0

					if prefs.show_lyrics_side and prefs.prefer_synced_lyrics and target_track is not None and timed_lyrics_ren.generate(
							target_track):

						if prefs.show_side_lyrics_art_panel:
							l_panel_h = round(200 * gui.scale)
							l_panel_y = window_size[1] - (gui.panelBY + l_panel_h)
							gui.showing_l_panel = True

							if not prefs.lyric_metadata_panel_top:
								timed_lyrics_ren.render(target_track.index, (window_size[0] - gui.rspw) + 9 * gui.scale,
														gui.panelY + 25 * gui.scale, side_panel=True, w=gui.rspw,
														h=window_size[1] - gui.panelY - gui.panelBY - l_panel_h)
								meta_box.l_panel(window_size[0] - gui.rspw, l_panel_y, gui.rspw, l_panel_h, target_track)
							else:
								timed_lyrics_ren.render(target_track.index, (window_size[0] - gui.rspw) + 9 * gui.scale,
														gui.panelY + 25 * gui.scale + l_panel_h, side_panel=True,
														w=gui.rspw,
														h=window_size[1] - gui.panelY - gui.panelBY - l_panel_h)
								meta_box.l_panel(window_size[0] - gui.rspw, gui.panelY, gui.rspw, l_panel_h, target_track)
						else:
							timed_lyrics_ren.render(target_track.index, (window_size[0] - gui.rspw) + 9 * gui.scale,
													gui.panelY + 25 * gui.scale, side_panel=True, w=gui.rspw,
													h=window_size[1] - gui.panelY - gui.panelBY)

							if right_click and coll(
								(window_size[0] - gui.rspw, gui.panelY + 25 * gui.scale, gui.rspw, window_size[1] - (gui.panelBY + gui.panelY))):
								center_info_menu.activate(target_track)

					elif prefs.show_lyrics_side and target_track is not None and target_track.lyrics != "" and gui.rspw > 192 * gui.scale:

						if prefs.show_side_lyrics_art_panel:
							l_panel_h = round(200 * gui.scale)
							l_panel_y = window_size[1] - (gui.panelBY + l_panel_h)
							gui.showing_l_panel = True

							if not prefs.lyric_metadata_panel_top:
								meta_box.lyrics(
									window_size[0] - gui.rspw, gui.panelY, gui.rspw,
									window_size[1] - gui.panelY - gui.panelBY - l_panel_h, target_track)
								meta_box.l_panel(window_size[0] - gui.rspw, l_panel_y, gui.rspw, l_panel_h, target_track)
							else:
								meta_box.lyrics(
									window_size[0] - gui.rspw, gui.panelY + l_panel_h, gui.rspw,
									window_size[1] - (gui.panelY + gui.panelBY + l_panel_h), target_track)

								meta_box.l_panel(
									window_size[0] - gui.rspw, gui.panelY, gui.rspw, l_panel_h,
									target_track, top_border=False)
						else:
							meta_box.lyrics(
								window_size[0] - gui.rspw, gui.panelY, gui.rspw,
								window_size[1] - gui.panelY - gui.panelBY, target_track)

					elif prefs.side_panel_layout == 0:

						boxw = gui.rspw
						boxh = gui.rspw

						if prefs.show_side_art:

							meta_box.draw(
								window_size[0] - gui.rspw, gui.panelY + boxh, gui.rspw,
								window_size[1] - gui.panelY - gui.panelBY - boxh, track=target_track)

							boxh = min(boxh, window_size[1] - gui.panelY - gui.panelBY)

							art_box.draw(window_size[0] - gui.rspw, gui.panelY, boxw, boxh, target_track=target_track)

						else:
							meta_box.draw(
								window_size[0] - gui.rspw, gui.panelY, gui.rspw,
								window_size[1] - gui.panelY - gui.panelBY, track=target_track)

					elif prefs.side_panel_layout == 1:

						h = window_size[1] - (gui.panelY + gui.panelBY)
						x = window_size[0] - gui.rspw
						y = gui.panelY
						w = gui.rspw

						ddt.rect((x, y, w, h), colours.side_panel_background)
						test_auto_lyrics(target_track)
						# Draw lyrics if avaliable
						if prefs.show_lyrics_side and target_track and target_track.lyrics != "":  # and not prefs.show_side_art:
							# meta_box.lyrics(x, y, w, h, target_track)
							if right_click and coll((x, y, w, h)) and target_track:
								center_info_menu.activate(target_track)
						else:

							box_wide_w = round(w * 0.98)
							boxx = round(min(h * 0.7, w * 0.9))
							boxy = round(min(h * 0.7, w * 0.9))

							bx = (x + w // 2) - (boxx // 2)
							bx_wide = (x + w // 2) - (box_wide_w // 2)
							by = round(h * 0.1)

							bby = by + boxy

							# We want the text in the center, but slightly raised when area is large
							text_y = y + by + boxy + ((h - bby) // 2) - 44 * gui.scale - round(
								(h - bby - 94 * gui.scale) * 0.08)

							small_mode = False
							if window_size[1] < 550 * gui.scale:
								small_mode = True
								text_y = y + by + boxy + ((h - bby) // 2) - 38 * gui.scale

							text_x = x + w // 2

							if prefs.show_side_art:
								gui.art_drawn_rect = None
								default_border = (bx, by, boxx, boxy)
								coll_border = default_border

								art_box.draw(
									bx_wide, by, box_wide_w, boxy, target_track=target_track,
									tight_border=True, default_border=default_border)

								if gui.art_drawn_rect:
									coll_border = gui.art_drawn_rect

								if right_click and coll((x, y, w, h)) and not coll(coll_border):
									if is_level_zero(include_menus=False) and target_track:
										center_info_menu.activate(target_track)

							else:
								text_y = y + round(h * 0.40)
								if right_click and coll((x, y, w, h)) and target_track:
									center_info_menu.activate(target_track)

							ww = w - 25 * gui.scale

							gui.showed_title = True

							if target_track:
								ddt.text_background_colour = colours.side_panel_background

								if pctl.playing_state == 3 and not radiobox.dummy_track.title:
									title = pctl.tag_meta
								else:
									title = target_track.title
									if not title:
										title = clean_string(target_track.filename)

								if small_mode:
									ddt.text(
										(text_x, text_y - 15 * gui.scale, 2), target_track.artist,
										colours.side_bar_line1, 315, max_w=ww)

									ddt.text(
										(text_x, text_y + 12 * gui.scale, 2), title, colours.side_bar_line1, 216, max_w=ww)

									line = " | ".join(
										filter(None, (target_track.album, target_track.date, target_track.genre)))
									ddt.text((text_x, text_y + 35 * gui.scale, 2), line, colours.side_bar_line2, 313, max_w=ww)

								else:
									ddt.text((text_x, text_y - 15 * gui.scale, 2), target_track.artist, colours.side_bar_line1, 317, max_w=ww)

									ddt.text((text_x, text_y + 17 * gui.scale, 2), title, colours.side_bar_line1, 218, max_w=ww)

									line = " | ".join(
										filter(None, (target_track.album, target_track.date, target_track.genre)))
									ddt.text((text_x, text_y + 45 * gui.scale, 2), line, colours.side_bar_line2, 314, max_w=ww)

				# Seperation Line Drawing
				if gui.rsp:

					# Draw Highlight when mouse over
					if draw_sep_hl:
						ddt.line(
							window_size[0] - gui.rspw + 1 * gui.scale, gui.panelY + 1 * gui.scale,
							window_size[0] - gui.rspw + 1 * gui.scale,
							window_size[1] - 50 * gui.scale, [100, 100, 100, 70])
						draw_sep_hl = False

			if (gui.artist_info_panel and not gui.combo_mode) and not (window_size[0] < 750 * gui.scale and album_mode):
				artist_info_box.draw(gui.playlist_left, gui.panelY, gui.plw, gui.artist_panel_height)

			if gui.lsp and not gui.combo_mode:

				# left side panel

				h_estimate = ((playlist_box.tab_h + playlist_box.gap) * gui.scale * len(
					pctl.multi_playlist)) + 13 * gui.scale

				full = (window_size[1] - (gui.panelY + gui.panelBY))
				half = int(round(full / 2))

				pl_box_h = full

				panel_rect = (0, gui.panelY, gui.lspw, pl_box_h)
				fields.add(panel_rect)

				if gui.force_side_on_drag and not quick_drag and not coll(panel_rect):
					gui.force_side_on_drag = False
					update_layout_do()

				if quick_drag and not coll_point(gui.drag_source_position_persist, panel_rect) and \
					not point_proximity_test(
						gui.drag_source_position,
						mouse_position,
						10 * gui.scale):
					gui.force_side_on_drag = True
					if mouse_up:
						update_layout_do()

				if prefs.left_panel_mode == "folder view" and not gui.force_side_on_drag:
					tree_view_box.render(0, gui.panelY, gui.lspw, pl_box_h)
				elif prefs.left_panel_mode == "artist list" and not gui.force_side_on_drag:
					artist_list_box.render(*panel_rect)
				else:

					preview_queue = False
					if quick_drag and coll(
							panel_rect) and not pctl.force_queue and prefs.show_playlist_list and prefs.hide_queue:
						preview_queue = True

					if pctl.force_queue or preview_queue or not prefs.hide_queue:

						if h_estimate < half:
							pl_box_h = h_estimate
						else:
							pl_box_h = half

						if preview_queue:
							pl_box_h = int(round(full * 5 / 6))

					if prefs.left_panel_mode != "queue":

						playlist_box.draw(0, gui.panelY, gui.lspw, pl_box_h)
					else:
						pl_box_h = 0

					if pctl.force_queue or preview_queue or not prefs.show_playlist_list or not prefs.hide_queue:

						queue_box.draw(0, gui.panelY + pl_box_h, gui.lspw, full - pl_box_h)
					elif prefs.left_panel_mode == "queue":
						text = _("Queue is Empty")
						rect = (0, gui.panelY + pl_box_h, gui.lspw, full - pl_box_h)
						ddt.rect(rect, colours.queue_background)
						ddt.text_background_colour = colours.queue_background
						ddt.text(
							(0 + (gui.lspw // 2), gui.panelY + pl_box_h + 15 * gui.scale, 2),
							text, alpha_mod(colours.index_text, 200), 212)

			# ------------------------------------------------
			# Scroll Bar

			# if not scroll_enable:
			top = gui.panelY
			if gui.artist_info_panel:
				top += gui.artist_panel_height

			edge_top = top
			if gui.set_bar and gui.set_mode:
				edge_top += gui.set_height
			edge_playlist2.render(gui.playlist_left, edge_top, gui.plw, 25 * gui.scale)

			width = 15 * gui.scale

			x = 0
			if gui.lsp:  # Move left so it sits over panel divide

				x = gui.lspw - 1 * gui.scale
				if not gui.set_mode:
					width = 11 * gui.scale
			if gui.set_mode and prefs.left_align_album_artist_title:
				width = 11 * gui.scale

			# x = gui.plw
			# width = round(14 * gui.scale)
			# if gui.lsp:
			#     x += gui.lspw
			# x -= width

			gui.scroll_hide_box = (
				x + 1 if not gui.maximized else x, top, 28 * gui.scale, window_size[1] - gui.panelBY - top)

			fields.add(gui.scroll_hide_box)
			if scroll_hide_timer.get() < 0.9 or ((coll(
					gui.scroll_hide_box) or scroll_hold or quick_search_mode) and \
					not menu_is_open() and \
					not pref_box.enabled and \
					not gui.rename_playlist_box \
					and gui.layer_focus == 0 and gui.show_playlist and not search_over.active):

				scroll_opacity = 255

				if not gui.combo_mode:
					sy = 31 * gui.scale
					ey = window_size[1] - (30 + 22) * gui.scale

					if len(default_playlist) < 50:
						sbl = 85 * gui.scale
						if len(default_playlist) == 0:
							sbp = top
					else:
						sbl = 105 * gui.scale

					fields.add((x + 2 * gui.scale, sbp, 20 * gui.scale, sbl))
					if coll((x, top, 28 * gui.scale, ey - top)) and (
							mouse_down or right_click) \
							and coll_point(click_location, (x, top, 28 * gui.scale, ey - top)):

						gui.pl_update = 1
						if right_click:

							sbp = mouse_position[1] - int(sbl / 2)
							if sbp + sbl > ey:
								sbp = ey - sbl
							elif sbp < top:
								sbp = top
							per = (sbp - top) / (ey - top - sbl)
							pctl.playlist_view_position = int(len(default_playlist) * per)
							logging.debug("Position set by scroll bar (right click)")
							pctl.playlist_view_position = max(pctl.playlist_view_position, 0)

							# if playlist_position == len(default_playlist):
							#     logging.info("END")

						# elif mouse_position[1] < sbp:
						#     pctl.playlist_view_position -= 2
						# elif mouse_position[1] > sbp + sbl:
						#     pctl.playlist_view_position += 2
						elif inp.mouse_click:

							if mouse_position[1] < sbp:
								gui.scroll_direction = -1
							elif mouse_position[1] > sbp + sbl:
								gui.scroll_direction = 1
							else:
								# p_y = pointer(c_int(0))
								# p_x = pointer(c_int(0))
								# SDL_GetGlobalMouseState(p_x, p_y)
								get_sdl_input.mouse_capture_want = True

								scroll_hold = True
								# scroll_point = p_y.contents.value  # mouse_position[1]
								scroll_point = mouse_position[1]
								scroll_bpoint = sbp
						else:
							# gui.update += 1
							if sbp < mouse_position[1] < sbp + sbl:
								gui.scroll_direction = 0
							pctl.playlist_view_position += gui.scroll_direction * 2
							logging.debug("Position set by scroll bar (slide)")
							pctl.playlist_view_position = max(pctl.playlist_view_position, 0)
							pctl.playlist_view_position = min(pctl.playlist_view_position, len(default_playlist))

							if sbp + sbl > ey:
								sbp = ey - sbl
							elif sbp < top:
								sbp = top

					if not mouse_down:
						scroll_hold = False

					if scroll_hold and not inp.mouse_click:
						gui.pl_update = 1
						# p_y = pointer(c_int(0))
						# p_x = pointer(c_int(0))
						# SDL_GetGlobalMouseState(p_x, p_y)
						get_sdl_input.mouse_capture_want = True

						sbp = mouse_position[1] - (scroll_point - scroll_bpoint)
						if sbp + sbl > ey:
							sbp = ey - sbl
						elif sbp < top:
							sbp = top
						per = (sbp - top) / (ey - top - sbl)
						pctl.playlist_view_position = int(len(default_playlist) * per)
						logging.debug("Position set by scroll bar (drag)")


					elif len(default_playlist) > 0:
						per = pctl.playlist_view_position / len(default_playlist)
						sbp = int((ey - top - sbl) * per) + top + 1

					bg = [255, 255, 255, 6]
					fg = colours.scroll_colour

					if colours.lm:
						bg = [200, 200, 200, 100]
						fg = [100, 100, 100, 200]

					ddt.rect_a((x, top), (width + 1 * gui.scale, window_size[1] - top - gui.panelBY), bg)
					ddt.rect_a((x + 1, sbp), (width, sbl), alpha_mod(fg, scroll_opacity))

					if (coll((x + 2 * gui.scale, sbp, 20 * gui.scale, sbl)) and mouse_position[
						0] != 0) or scroll_hold:
						ddt.rect_a((x + 1 * gui.scale, sbp), (width, sbl), [255, 255, 255, 19])

			# NEW TOP BAR
			# C-TBR

			if gui.mode == 1:
				top_panel.render()

			# RENDER EXTRA FRAME DOUBLE
			if colours.lm:
				if gui.lsp and not gui.combo_mode and not gui.compact_artist_list:
					ddt.rect(
						(0 + gui.lspw - 6 * gui.scale, gui.panelY, 6 * gui.scale,
						int(round(window_size[1] - gui.panelY - gui.panelBY))), colours.grey(200))
					ddt.rect(
						(0 + gui.lspw - 5 * gui.scale, gui.panelY - 1, 4 * gui.scale,
						int(round(window_size[1] - gui.panelY - gui.panelBY)) + 1), colours.grey(245))
				if gui.rsp and gui.show_playlist:
					w = window_size[0] - gui.rspw
					ddt.rect(
						(w - round(3 * gui.scale), gui.panelY, 6 * gui.scale,
						int(round(window_size[1] - gui.panelY - gui.panelBY))), colours.grey(200))
					ddt.rect(
						(w - round(2 * gui.scale), gui.panelY - 1, 4 * gui.scale,
						int(round(window_size[1] - gui.panelY - gui.panelBY)) + 1), colours.grey(245))
				if gui.queue_frame_draw is not None:
					if gui.lsp:
						ddt.rect((0, gui.queue_frame_draw, gui.lspw - 6 * gui.scale, 6 * gui.scale), colours.grey(200))
						ddt.rect(
							(0, gui.queue_frame_draw + 1 * gui.scale, gui.lspw - 5 * gui.scale, 4 * gui.scale), colours.grey(250))

					gui.queue_frame_draw = None

			# BOTTOM BAR!
			# C-BB

			ddt.text_background_colour = colours.bottom_panel_colour

			if prefs.shuffle_lock:
				bottom_bar_ao1.render()
			else:
				bottom_bar1.render()

			if prefs.art_bg and not prefs.bg_showcase_only:
				style_overlay.display()
				# if key_shift_down:
				#     ddt.rect_r(gui.seek_bar_rect,
				#                alpha_mod([150, 150, 150 ,255], 20), True)
				#     ddt.rect_r(gui.volume_bar_rect,
				#                alpha_mod(colours.volume_bar_fill, 100), True)

			style_overlay.hole_punches.clear()

			if gui.set_mode:
				if rename_track_box.active is False \
						and radiobox.active is False \
						and gui.rename_playlist_box is False \
						and gui.message_box is False \
						and pref_box.enabled is False \
						and track_box is False \
						and not gui.rename_folder_box \
						and not Menu.active \
						and not artist_info_scroll.held:

					columns_tool_tip.render()
				else:
					columns_tool_tip.show = False

			# Overlay GUI ----------------------

			if gui.rename_playlist_box:
				rename_playlist_box.render()

			if gui.preview_artist:

				border = round(4 * gui.scale)
				ddt.rect(
					(gui.preview_artist_location[0] - border,
					gui.preview_artist_location[1] - border,
					artist_preview_render.size[0] + border * 2,
					artist_preview_render.size[0] + border * 2), (20, 20, 20, 255))

				artist_preview_render.draw(gui.preview_artist_location[0], gui.preview_artist_location[1])
				if inp.mouse_click or right_click or mouse_wheel:
					gui.preview_artist = ""

			if track_box:
				if inp.key_return_press or right_click or key_esc_press or inp.backspace_press or keymaps.test(
						"quick-find"):
					track_box = False

					inp.key_return_press = False

				if gui.level_2_click:
					inp.mouse_click = True
				gui.level_2_click = False

				tc = pctl.master_library[r_menu_index]

				w = round(540 * gui.scale)
				h = round(240 * gui.scale)
				comment_mode = 0

				if len(tc.comment) > 0:
					h += 22 * gui.scale
					if window_size[0] > 599:
						w += 25 * gui.scale
					if ddt.get_text_w(tc.comment, 12) > 330 * gui.scale or "\n" in tc.comment:
						h += 80 * gui.scale
						if window_size[0] > 599:
							w += 30 * gui.scale
						comment_mode = 1

				x = round((window_size[0] / 2) - (w / 2))
				y = round((window_size[1] / 2) - (h / 2))

				x1 = int(x + 18 * gui.scale)
				x2 = int(x + 98 * gui.scale)

				value_font_a = 312
				value_font = 12

				# if key_shift_down:
				#     value_font = 12
				key_colour_off = colours.box_text_label  # colours.grey_blend_bg(90)
				key_colour_on = colours.box_title_text
				value_colour = colours.box_sub_text
				path_colour = alpha_mod(value_colour, 240)

				# if colours.lm:
				#     key_colour_off = colours.grey(80)
				#     key_colour_on = colours.grey(120)
				#     value_colour = colours.grey(50)
				#     path_colour = colours.grey(70)

				ddt.rect_a(
					(x - 3 * gui.scale, y - 3 * gui.scale), (w + 6 * gui.scale, h + 6 * gui.scale),
					colours.box_border)
				ddt.rect_a((x, y), (w, h), colours.box_background)
				ddt.text_background_colour = colours.box_background

				if inp.mouse_click and not coll([x, y, w, h]):
					track_box = False

				else:
					art_size = int(115 * gui.scale)

					# if not tc.is_network: # Don't draw album art if from network location for better performance
					if comment_mode == 1:
						album_art_gen.display(
							tc, (int(x + w - 135 * gui.scale), int(y + 105 * gui.scale)),
							(art_size, art_size))  # Mirror this size in auto theme #mark2233
					else:
						album_art_gen.display(
							tc, (int(x + w - 135 * gui.scale), int(y + h - 135 * gui.scale)),
							(art_size, art_size))

					y -= int(24 * gui.scale)
					y1 = int(y + (40 * gui.scale))

					ext_rect = [x + w - round(38 * gui.scale), y + round(44 * gui.scale), round(38 * gui.scale),
								round(12 * gui.scale)]

					line = tc.file_ext
					ex_colour = [130, 130, 130, 255]
					if line in format_colours:
						ex_colour = format_colours[line]

					# Spotify icon rendering
					if line == "SPTY":
						colour = [30, 215, 96, 255]
						h, l, s = rgb_to_hls(colour[0], colour[1], colour[2])

						rect = (x + w - round(35 * gui.scale), y + round(30 * gui.scale), round(30 * gui.scale),
								round(30 * gui.scale))
						fields.add(rect)
						if coll(rect):
							l += 0.1
							gui.cursor_want = 3

							if inp.mouse_click:
								url = tc.misc.get("spotify-album-url")
								if url is None:
									url = tc.misc.get("spotify-track-url")
								if url:
									webbrowser.open(url, new=2, autoraise=True)

						colour = hls_to_rgb(h, l, s)

						gui.spot_info_icon.render(x + w - round(33 * gui.scale), y + round(35 * gui.scale), colour)

					# Codec tag rendering
					else:
						if tc.file_ext in ("JELY", "TIDAL"):
							e_colour = [130, 130, 130, 255]
							if "container" in tc.misc:
								line = tc.misc["container"].upper()
								if line in format_colours:
									e_colour = format_colours[line]

							ddt.rect(ext_rect, e_colour)
							colour = alpha_blend([10, 10, 10, 235], e_colour)
							if colour_value(e_colour) < 180:
								colour = alpha_blend([200, 200, 200, 235], e_colour)
							ddt.text(
								(int(x + w - 35 * gui.scale), round(y + (41) * gui.scale)), line, colour, 211, bg=e_colour)
							ext_rect[1] += 16 * gui.scale
							y += 16 * gui.scale

						ddt.rect(ext_rect, ex_colour)
						colour = alpha_blend([10, 10, 10, 235], ex_colour)
						if colour_value(ex_colour) < 180:
							colour = alpha_blend([200, 200, 200, 235], ex_colour)
						ddt.text(
							(int(x + w - 35 * gui.scale), round(y + 41 * gui.scale)), tc.file_ext, colour, 211, bg=ex_colour)

						if tc.is_cue:
							ext_rect[1] += 16 * gui.scale
							colour = [218, 222, 73, 255]
							if tc.is_embed_cue:
								colour = [252, 199, 55, 255]
							ddt.rect(ext_rect, colour)
							ddt.text(
								(int(x + w - 35 * gui.scale), int(y + (41 + 16) * gui.scale)), "CUE",
								alpha_blend([10, 10, 10, 235], colour), 211, bg=colour)


					rect = [x1, y1 + int(2 * gui.scale), 450 * gui.scale, 14 * gui.scale]
					fields.add(rect)
					if coll(rect):
						ddt.text((x1, y1), _("Title"), key_colour_on, 212)
						if inp.mouse_click:
							show_message(_("Copied text to clipboard"))
							copy_to_clipboard(tc.title)
							inp.mouse_click = False
					else:
						ddt.text((x1, y1), _("Title"), key_colour_off, 212)
					q = ddt.text(
						(x2, y1 - int(2 * gui.scale)), tc.title,
						value_colour, 314, max_w=w - 170 * gui.scale)

					if coll(rect):
						ex_tool_tip(x2 + 185 * gui.scale, y1, q, tc.title, 314)

					y1 += int(16 * gui.scale)

					rect = [x1, y1 + (2 * gui.scale), 450 * gui.scale, 14 * gui.scale]
					fields.add(rect)
					if coll(rect):
						ddt.text((x1, y1), _("Artist"), key_colour_on, 212)
						if inp.mouse_click:
							show_message(_("Copied text to clipboard"))
							copy_to_clipboard(tc.artist)
							inp.mouse_click = False
					else:
						ddt.text((x1, y1), _("Artist"), key_colour_off, 212)

					q = ddt.text(
						(x2, y1 - (1 * gui.scale)), tc.artist,
						value_colour, value_font_a, max_w=390 * gui.scale)

					if coll(rect):
						ex_tool_tip(x2 + 185 * gui.scale, y1, q, tc.artist, value_font_a)

					y1 += int(16 * gui.scale)

					rect = [x1, y1 + (2 * gui.scale), 450 * gui.scale, 14 * gui.scale]
					fields.add(rect)
					if coll(rect):
						ddt.text((x1, y1), _("Album"), key_colour_on, 212)
						if inp.mouse_click:
							show_message(_("Copied text to clipboard"))
							copy_to_clipboard(tc.album)
							inp.mouse_click = False
					else:
						ddt.text((x1, y1), _("Album"), key_colour_off, 212)

					q = ddt.text(
						(x2, y1 - 1 * gui.scale), tc.album,
						value_colour,
						value_font_a, max_w=390 * gui.scale)

					if coll(rect):
						ex_tool_tip(x2 + 185 * gui.scale, y1, q, tc.album, value_font_a)

					y1 += int(26 * gui.scale)

					rect = [x1, y1, 450 * gui.scale, 16 * gui.scale]
					fields.add(rect)
					path = tc.fullpath
					if msys:
						path = path.replace("/", "\\")
					if coll(rect):
						ddt.text((x1, y1), _("Path"), key_colour_on, 212)
						if inp.mouse_click:
							show_message(_("Copied text to clipboard"))
							copy_to_clipboard(path)
							inp.mouse_click = False
					else:
						ddt.text((x1, y1), _("Path"), key_colour_off, 212)

					q = ddt.text(
						(x2, y1 - int(3 * gui.scale)), clean_string(path),
						path_colour, 210, max_w=425 * gui.scale)

					if coll(rect):
						gui.frame_callback_list.append(TestTimer(0.71))
						if track_box_path_tool_timer.get() > 0.7:
							ex_tool_tip(x2 + 185 * gui.scale, y1, q, clean_string(tc.fullpath), 210)
					else:
						track_box_path_tool_timer.set()

					y1 += int(15 * gui.scale)

					if tc.samplerate != 0:
						ddt.text((x1, y1), _("Samplerate"), key_colour_off, 212, max_w=70 * gui.scale)

						line = str(tc.samplerate) + " Hz"

						off = ddt.text((x2, y1), line, value_colour, value_font)

						if tc.bit_depth > 0:
							line = str(tc.bit_depth) + " bit"
							ddt.text((x2 + off + 9 * gui.scale, y1), line, value_colour, 311)

					y1 += int(15 * gui.scale)

					if tc.bitrate not in (0, "", "0"):
						ddt.text((x1, y1), _("Bitrate"), key_colour_off, 212, max_w=70 * gui.scale)
						line = str(tc.bitrate)
						if tc.file_ext in ("FLAC", "OPUS", "APE", "WV"):
							line = "≈" + line
						line += _(" kbps")
						ddt.text((x2, y1), line, value_colour, 312)

					# -----------
					if tc.artist != tc.album_artist != "":
						x += int(170 * gui.scale)
						rect = [x + 7 * gui.scale, y1 + (2 * gui.scale), 220 * gui.scale, 14 * gui.scale]
						fields.add(rect)
						if coll(rect):
							ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Album Artist"), key_colour_on, 212)
							if inp.mouse_click:
								show_message(_("Copied text to clipboard"))
								copy_to_clipboard(tc.album_artist)
								inp.mouse_click = False
						else:
							ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Album Artist"), key_colour_off, 212)

						q = ddt.text(
							(x + (8 + 88) * gui.scale, y1), tc.album_artist,
							value_colour, value_font, max_w=120 * gui.scale)
						if coll(rect):
							ex_tool_tip(x2 + 185 * gui.scale, y1, q, tc.album_artist, value_font)

						x -= int(170 * gui.scale)

					y1 += int(15 * gui.scale)

					rect = [x1, y1, 150 * gui.scale, 16 * gui.scale]
					fields.add(rect)
					if coll(rect):
						ddt.text((x1, y1), _("Duration"), key_colour_on, 212)
						if inp.mouse_click:
							copy_to_clipboard(time.strftime("%M:%S", time.gmtime(tc.length)).lstrip("0"))
							show_message(_("Copied text to clipboard"))
							inp.mouse_click = False
					else:
						ddt.text((x1, y1), _("Duration"), key_colour_off, 212)
					line = time.strftime("%M:%S", time.gmtime(tc.length))
					ddt.text((x2, y1), line, value_colour, value_font)

					# -----------
					if tc.track_total not in ("", "0"):
						x += int(170 * gui.scale)
						line = str(tc.track_number) + _(" of ") + str(
							tc.track_total)
						ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Track"), key_colour_off, 212)
						ddt.text((x + (8 + 88) * gui.scale, y1), line, value_colour, value_font)
						x -= int(170 * gui.scale)

					y1 += int(15 * gui.scale)
					#logging.info(tc.size)
					if tc.is_cue and tc.misc.get("parent-length", 0) > 0 and tc.misc.get("parent-size", 0) > 0:
						ddt.text((x1, y1), _("File size"), key_colour_off, 212, max_w=70 * gui.scale)
						estimate = (tc.length / tc.misc.get("parent-length")) * tc.misc.get("parent-size")
						line = f"≈{get_filesize_string(estimate, rounding=0)} / {get_filesize_string(tc.misc.get('parent-size'))}"
						ddt.text((x2, y1), line, value_colour, value_font)

					elif tc.size != 0:
						ddt.text((x1, y1), _("File size"), key_colour_off, 212, max_w=70 * gui.scale)
						ddt.text((x2, y1), get_filesize_string(tc.size), value_colour, value_font)

					# -----------
					if tc.disc_total not in ("", "0", 0):
						x += int(170 * gui.scale)
						line = str(tc.disc_number) + _(" of ") + str(
							tc.disc_total)
						ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Disc"), key_colour_off, 212)
						ddt.text((x + (8 + 88) * gui.scale, y1), line, value_colour, value_font)
						x -= int(170 * gui.scale)

					y1 += int(23 * gui.scale)

					rect = [x1, y1 + (2 * gui.scale), 150 * gui.scale, 14 * gui.scale]
					fields.add(rect)
					if coll(rect):
						ddt.text((x1, y1), _("Genre"), key_colour_on, 212)
						if inp.mouse_click:
							show_message(_("Copied text to clipboard"))
							copy_to_clipboard(tc.genre)
							inp.mouse_click = False
					else:
						ddt.text((x1, y1), _("Genre"), key_colour_off, 212)
					ddt.text(
						(x2, y1), tc.genre, value_colour,
						value_font, max_w=290 * gui.scale)

					y1 += int(15 * gui.scale)

					rect = [x1, y1 + (2 * gui.scale), 150 * gui.scale, 14 * gui.scale]
					fields.add(rect)
					if coll(rect):
						ddt.text((x1, y1), _("Date"), key_colour_on, 212)
						if inp.mouse_click:
							show_message(_("Copied text to clipboard"))
							copy_to_clipboard(tc.date)
							inp.mouse_click = False
					else:
						ddt.text((x1, y1), _("Date"), key_colour_off, 212)
					ddt.text((x2, y1), d_date_display(tc), value_colour, value_font)

					if tc.composer and tc.composer != tc.artist:
						x += int(170 * gui.scale)
						rect = [x + 7 * gui.scale, y1 + (2 * gui.scale), 220 * gui.scale, 14 * gui.scale]
						fields.add(rect)
						if coll(rect):
							ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Composer"), key_colour_on, 212)
							if inp.mouse_click:
								show_message(_("Copied text to clipboard"))
								copy_to_clipboard(tc.album_artist)
								inp.mouse_click = False
						else:
							ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Composer"), key_colour_off, 212)
						q = ddt.text(
							(x + (8 + 88) * gui.scale, y1), tc.composer,
							value_colour, value_font, max_w=120 * gui.scale)
						if coll(rect):
							ex_tool_tip(x2 + 185 * gui.scale, y1, q, tc.composer, value_font_a)

						x -= int(170 * gui.scale)

					y1 += int(23 * gui.scale)

					total = star_store.get(r_menu_index)

					ratio = 0

					if total > 0 and pctl.master_library[
						r_menu_index].length > 1:
						ratio = total / (tc.length - 1)

					ddt.text((x1, y1), _("Play count"), key_colour_off, 212, max_w=70 * gui.scale)
					ddt.text((x2, y1), str(int(ratio)), value_colour, value_font)

					y1 += int(15 * gui.scale)

					rect = [x1, y1, 150, 14]

					if coll(rect) and key_shift_down and mouse_wheel != 0:
						star_store.add(r_menu_index, 60 * mouse_wheel)

					line = time.strftime("%H:%M:%S", time.gmtime(total))

					ddt.text((x1, y1), _("Play time"), key_colour_off, 212, max_w=70 * gui.scale)
					ddt.text((x2, y1), str(line), value_colour, value_font)

					# -------
					if tc.lyrics != "":

						if draw.button(_("Lyrics"), x1 + 200 * gui.scale, y1 - 10 * gui.scale):
							prefs.show_lyrics_showcase = True
							track_box = False
							enter_showcase_view(track_id=r_menu_index)
							inp.mouse_click = False

					if len(tc.comment) > 0:
						y1 += 20 * gui.scale
						rect = [x1, y1 + (2 * gui.scale), 60 * gui.scale, 14 * gui.scale]
						# ddt.rect_r((x2, y1, 335, 10), [255, 20, 20, 255])
						fields.add(rect)
						if coll(rect):
							ddt.text((x1, y1), _("Comment"), key_colour_on, 212)
							if inp.mouse_click:
								show_message(_("Copied text to clipboard"))
								copy_to_clipboard(tc.comment)
								inp.mouse_click = False
						else:
							ddt.text((x1, y1), _("Comment"), key_colour_off, 212)
						# ddt.draw_text((x1, y1), "Comment", key_colour_off, 12)

						if "\n" not in tc.comment and (
								"http://" in tc.comment or "www." in tc.comment or "https://" in tc.comment) and ddt.get_text_w(
								tc.comment, 12) < 335 * gui.scale:

							link_pa = draw_linked_text((x2, y1), tc.comment, value_colour, 12)
							link_rect = [x + 98 * gui.scale + link_pa[0], y1 - 2 * gui.scale, link_pa[1], 20 * gui.scale]

							fields.add(link_rect)
							if coll(link_rect):
								if not inp.mouse_click:
									gui.cursor_want = 3
								if inp.mouse_click:
									webbrowser.open(link_pa[2], new=2, autoraise=True)
									track_box = True

						elif comment_mode == 1:
							ddt.text(
								(x + 18 * gui.scale, y1 + 18 * gui.scale, 4, w - 36 * gui.scale, 90 * gui.scale),
								tc.comment, value_colour, 12)
						else:
							ddt.text((x2, y1), tc.comment, value_colour, 12)

			if draw_border and gui.mode != 3:

				tool_rect = [window_size[0] - 110 * gui.scale, 2, 95 * gui.scale, 45 * gui.scale]
				if prefs.left_window_control:
					tool_rect[0] = 0
				fields.add(tool_rect)
				if not gui.top_bar_mode2 or coll(tool_rect):
					draw_window_tools()

				if not gui.fullscreen and not gui.maximized:
					draw_window_border()

			fader.render()
			if pref_box.enabled:
				# rect = [0, 0, window_size[0], window_size[1]]
				# ddt.rect_r(rect, [0, 0, 0, 90], True)
				pref_box.render()

			if gui.rename_folder_box:

				if gui.level_2_click:
					inp.mouse_click = True

				gui.level_2_click = False

				w = 500 * gui.scale
				h = 127 * gui.scale
				x = int(window_size[0] / 2) - int(w / 2)
				y = int(window_size[1] / 2) - int(h / 2)

				ddt.rect_a(
					(x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale), colours.box_border)
				ddt.rect_a((x, y), (w, h), colours.box_background)

				ddt.text_background_colour = colours.box_background

				if key_esc_press or (
						(inp.mouse_click or right_click or level_2_right_click) and not coll((x, y, w, h))):
					gui.rename_folder_box = False

				p = ddt.text(
					(x + 10 * gui.scale, y + 9 * gui.scale), _("Folder Modification"), colours.box_title_text, 213)

				if rename_folder.text != prefs.rename_folder_template and draw.button(
					_("Default"),
					x + (300 - 63) * gui.scale,
					y + 11 * gui.scale,
					70 * gui.scale):
					rename_folder.text = prefs.rename_folder_template

				rename_folder.draw(x + 14 * gui.scale, y + 41 * gui.scale, colours.box_input_text, width=300)

				ddt.rect_s(
					(x + 8 * gui.scale, y + 38 * gui.scale, 300 * gui.scale, 22 * gui.scale),
					colours.box_text_border, 1 * gui.scale)

				if draw.button(
					_("Rename"), x + (8 + 300 + 10) * gui.scale, y + 38 * gui.scale, 80 * gui.scale,
					tooltip=_("Renames the physical folder based on the template")) or inp.level_2_enter:
					rename_parent(rename_index, rename_folder.text)
					gui.rename_folder_box = False
					inp.mouse_click = False

				text = _("Trash")
				tt = _("Moves folder to system trash")
				if key_shift_down:
					text = _("Delete")
					tt = _("Physically deletes folder from disk")
				if draw.button(
					text, x + (8 + 300 + 10) * gui.scale, y + 11 * gui.scale, 80 * gui.scale,
					text_highlight_colour=colours.grey(255), background_highlight_colour=[180, 60, 60, 255],
					press=mouse_up, tooltip=tt):
					if key_shift_down:
						delete_folder(rename_index, True)
					else:
						delete_folder(rename_index)
					gui.rename_folder_box = False
					inp.mouse_click = False

				if move_folder_up(rename_index):
					if draw.button(
						_("Raise"), x + 408 * gui.scale, y + 38 * gui.scale, 80 * gui.scale,
						tooltip=_("Moves folder up 2 levels and deletes the old container folder")):
						move_folder_up(rename_index, True)
						inp.mouse_click = False

				to_clean = clean_folder(rename_index)
				if to_clean > 0:
					if draw.button(
						"Clean (" + str(to_clean) + ")", x + 408 * gui.scale, y + 11 * gui.scale,
						80 * gui.scale, tooltip=_("Deletes some unnecessary files from folder")):
						clean_folder(rename_index, True)
						inp.mouse_click = False

				ddt.text((x + 10 * gui.scale, y + 65 * gui.scale), _("PATH"), colours.box_text_label, 212)
				line = os.path.dirname(
					pctl.master_library[rename_index].parent_folder_path.rstrip("\\/")).replace("\\","/") + "/"
				line = right_trunc(line, 12, 420 * gui.scale)
				line = clean_string(line)
				ddt.text((x + 60 * gui.scale, y + 65 * gui.scale), line, colours.grey(220), 211)

				ddt.text((x + 10 * gui.scale, y + 83 * gui.scale), _("OLD"), colours.box_text_label, 212)
				line = pctl.master_library[rename_index].parent_folder_name
				line = clean_string(line)
				ddt.text((x + 60 * gui.scale, y + 83 * gui.scale), line, colours.grey(220), 211, max_w=420 * gui.scale)

				ddt.text((x + 10 * gui.scale, y + 101 * gui.scale), _("NEW"), colours.box_text_label, 212)
				line = parse_template2(rename_folder.text, pctl.master_library[rename_index])
				ddt.text((x + 60 * gui.scale, y + 101 * gui.scale), line, colours.grey(220), 211, max_w=420 * gui.scale)

			if rename_track_box.active:
				rename_track_box.render()

			if sub_lyrics_box.active:
				sub_lyrics_box.render()

			if export_playlist_box.active:
				export_playlist_box.render()

			if trans_edit_box.active:
				trans_edit_box.render()

			if radiobox.active:
				radiobox.render()

			if gui.message_box:
				message_box.render()

			if prefs.show_nag:
				nagbox.draw()

			# SEARCH
			# if key_ctrl_down and key_v_press:

			#     search_over.active = True

			search_over.render()

			if keymaps.test("quick-find") and quick_search_mode is False:
				if not search_over.active and not gui.box_over:
					quick_search_mode = True
				if search_clear_timer.get() > 3:
					search_text.text = ""
				input_text = ""
			elif (keymaps.test("quick-find") or (
					key_esc_press and len(editline) == 0)) or (inp.mouse_click and quick_search_mode is True):
				quick_search_mode = False
				search_text.text = ""

			# if (key_backslash_press or (key_ctrl_down and key_f_press)) and quick_search_mode is False:
			#     if not search_over.active:
			#         quick_search_mode = True
			#     if search_clear_timer.get() > 3:
			#         search_text.text = ""
			#     input_text = ""
			# elif ((key_backslash_press or (key_ctrl_down and key_f_press)) or (
			#             key_esc_press and len(editline) == 0)) or input.mouse_click and quick_search_mode is True:
			#     quick_search_mode = False
			#     search_text.text = ""

			if quick_search_mode is True:

				rect2 = [0, window_size[1] - 85 * gui.scale, 420 * gui.scale, 25 * gui.scale]
				rect = [0, window_size[1] - 125 * gui.scale, 420 * gui.scale, 65 * gui.scale]
				rect[0] = int(window_size[0] / 2) - int(rect[2] / 2)
				rect2[0] = rect[0]

				ddt.rect((rect[0] - 2, rect[1] - 2, rect[2] + 4, rect[3] + 4), colours.box_border)  # [220, 100, 5, 255]
				# ddt.rect_r((rect[0], rect[1], rect[2], rect[3]), [255,120,5,255], True)

				ddt.text_background_colour = colours.box_background
				# ddt.text_background_colour = [255,120,5,255]
				# ddt.text_background_colour = [220,100,5,255]
				ddt.rect(rect, colours.box_background)

				if len(input_text) > 0:
					search_index = -1

				if inp.backspace_press and search_text.text == "":
					quick_search_mode = False

				if len(search_text.text) == 0:
					gui.search_error = False

				if len(search_text.text) != 0 and search_text.text[0] == "/":
					# if "/love" in search_text.text:
					#     line = "last.fm loved tracks from user. Format: /love <username>"
					# else:
					line = _("Folder filter mode. Enter path segment.")
					ddt.text((rect[0] + 23 * gui.scale, window_size[1] - 87 * gui.scale), line, (220, 220, 220, 100), 312)
				else:
					line = _("UP / DOWN to navigate. SHIFT + RETURN for new playlist.")
					if len(search_text.text) == 0:
						line = _("Quick find")
					ddt.text((rect[0] + int(rect[2] / 2), window_size[1] - 87 * gui.scale, 2), line, colours.box_text_label, 312)

					# ddt.draw_text((rect[0] + int(rect[2] / 2), window_size[1] - 118 * gui.scale, 2), "Find",
					#           colours.grey(90), 214)

				# if len(pctl.track_queue) > 0:

				# if input_text == 'A':
				#     search_text.text = pctl.playing_object().artist
				#     input_text = ""

				if gui.search_error:
					ddt.rect([rect[0], rect[1], rect[2], 30 * gui.scale], [180, 40, 40, 255])
					ddt.text_background_colour = [180, 40, 40, 255]  # alpha_blend([255,0,0,25], ddt.text_background_colour)
				# if input.backspace_press:
				#     gui.search_error = False

				search_text.draw(rect[0] + 8 * gui.scale, rect[1] + 6 * gui.scale, colours.grey(250), font=213)

				if (key_shift_down or (
						len(search_text.text) > 0 and search_text.text[0] == "/")) and inp.key_return_press:
					inp.key_return_press = False
					playlist = []
					if len(search_text.text) > 0:
						if search_text.text[0] == "/":

							if search_text.text.lower() == "/random" or search_text.text.lower() == "/shuffle":
								gen_500_random(pctl.active_playlist_viewing)
							elif search_text.text.lower() == "/top" or search_text.text.lower() == "/most":
								gen_top_100(pctl.active_playlist_viewing)
							elif search_text.text.lower() == "/length" or search_text.text.lower() == "/duration" \
									or search_text.text.lower() == "/len":
								gen_sort_len(pctl.active_playlist_viewing)
							else:

								if search_text.text[-1] == "/":
									tt_title = search_text.text.replace("/", "")
								else:
									search_text.text = search_text.text.replace("/", "")
									tt_title = search_text.text
								search_text.text = search_text.text.lower()
								for item in default_playlist:
									if search_text.text in pctl.master_library[item].parent_folder_path.lower():
										playlist.append(item)
								if len(playlist) > 0:
									pctl.multi_playlist.append(pl_gen(title=tt_title, playlist_ids=copy.deepcopy(playlist)))
									switch_playlist(len(pctl.multi_playlist) - 1)

						else:
							search_terms = search_text.text.lower().split()
							for item in default_playlist:
								tr = pctl.get_track(item)
								line = " ".join(
									[
										tr.title, tr.artist, tr.album, tr.fullpath,
										tr.composer, tr.comment, tr.album_artist, tr.misc.get("artist_sort", "")]).lower()

								# if prefs.diacritic_search and all([ord(c) < 128 for c in search_text.text]):
								#     line = str(unidecode(line))

								if all(word in line for word in search_terms):
									playlist.append(item)
							if len(playlist) > 0:
								pctl.multi_playlist.append(pl_gen(
									title=_("Search Results"),
									playlist_ids=copy.deepcopy(playlist)))
								pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "s\"" + pctl.multi_playlist[
									pctl.active_playlist_viewing].title + "\" f\"" + search_text.text + "\""
								switch_playlist(len(pctl.multi_playlist) - 1)
						search_text.text = ""
						quick_search_mode = False

				if (len(input_text) > 0 and not gui.search_error) or key_down_press is True or inp.backspace_press \
						or gui.force_search:

					gui.pl_update = 1

					if gui.force_search:
						search_index = 0

					if inp.backspace_press:
						search_index = 0

					if len(search_text.text) > 0 and search_text.text[0] != "/":
						oi = search_index

						while search_index < len(default_playlist) - 1:
							search_index += 1
							if search_index > len(default_playlist) - 1:
								search_index = 0

							search_terms = search_text.text.lower().split()
							tr = pctl.get_track(default_playlist[search_index])
							line = " ".join(
								[tr.title, tr.artist, tr.album, tr.fullpath, tr.composer, tr.comment,
								tr.album_artist, tr.misc.get("artist_sort", "")]).lower()

							# if prefs.diacritic_search and all([ord(c) < 128 for c in search_text.text]):
							#     line = str(unidecode(line))

							if all(word in line for word in search_terms):

								pctl.selected_in_playlist = search_index
								if len(default_playlist) > 10 and search_index > 10:
									pctl.playlist_view_position = search_index - 7
									logging.debug("Position changed by search")
								else:
									pctl.playlist_view_position = 0

								if gui.combo_mode:
									pctl.show_selected()
								gui.search_error = False

								break

						else:
							search_index = oi
							if len(input_text) > 0 or gui.force_search:
								gui.search_error = True
							if key_down_press:
								bottom_playlist2.pulse()

						gui.force_search = False

				if key_up_press is True \
						and not key_shiftr_down \
						and not key_shift_down \
						and not key_ctrl_down \
						and not key_rctrl_down \
						and not key_meta \
						and not key_lalt \
						and not key_ralt:

					gui.pl_update = 1
					oi = search_index

					while search_index > 1:
						search_index -= 1
						search_index = min(search_index, len(default_playlist) - 1)
						search_terms = search_text.text.lower().split()
						line = pctl.master_library[default_playlist[search_index]].title.lower() + \
							pctl.master_library[default_playlist[search_index]].artist.lower() \
							+ pctl.master_library[default_playlist[search_index]].album.lower() + \
							pctl.master_library[default_playlist[search_index]].filename.lower()

						if prefs.diacritic_search and all([ord(c) < 128 for c in search_text.text]):
							line = str(unidecode(line))

						if all(word in line for word in search_terms):

							pctl.selected_in_playlist = search_index
							if len(default_playlist) > 10 and search_index > 10:
								pctl.playlist_view_position = search_index - 7
								logging.debug("Position changed by search")
							else:
								pctl.playlist_view_position = 0
							if gui.combo_mode:
								pctl.show_selected()
							break
					else:
						search_index = oi

						edge_playlist2.pulse()

				if inp.key_return_press is True and search_index > -1:
					gui.pl_update = 1
					pctl.jump(default_playlist[search_index], search_index)
					if album_mode:
						goto_album(pctl.playlist_playing_position)
					quick_search_mode = False
					search_clear_timer.set()

			elif not search_over.active:

				if key_up_press and ((
					not key_shiftr_down \
					and not key_shift_down \
					and not key_ctrl_down \
					and not key_rctrl_down \
					and not key_meta \
					and not key_lalt \
					and not key_ralt) or (keymaps.test("shift-up"))):

					pctl.show_selected()
					gui.pl_update = 1

					if not keymaps.test("shift-up"):
						if pctl.selected_in_playlist > 0:
							pctl.selected_in_playlist -= 1
							r_menu_index = default_playlist[pctl.selected_in_playlist]
						shift_selection = []

					if pctl.playlist_view_position > 0 and pctl.selected_in_playlist < pctl.playlist_view_position + 2:
						pctl.playlist_view_position -= 1
						logging.debug("Position changed by key up")

						scroll_hide_timer.set()
						gui.frame_callback_list.append(TestTimer(0.9))

					pctl.selected_in_playlist = min(pctl.selected_in_playlist, len(default_playlist))

				if pctl.selected_in_playlist < len(default_playlist) and (
					(key_down_press and \
					not key_shiftr_down \
					and not key_shift_down \
					and not key_ctrl_down \
					and not key_rctrl_down \
					and not key_meta \
					and not key_lalt \
					and not key_ralt) or keymaps.test("shift-down")):

					pctl.show_selected()
					gui.pl_update = 1

					if not keymaps.test("shift-down"):
						if pctl.selected_in_playlist < len(default_playlist) - 1:
							pctl.selected_in_playlist += 1
							r_menu_index = default_playlist[pctl.selected_in_playlist]
						shift_selection = []

					if pctl.playlist_view_position < len(
							default_playlist) and pctl.selected_in_playlist > pctl.playlist_view_position + gui.playlist_view_length - 3 - gui.row_extra:
						pctl.playlist_view_position += 1
						logging.debug("Position changed by key down")

						scroll_hide_timer.set()
						gui.frame_callback_list.append(TestTimer(0.9))

					pctl.selected_in_playlist = max(pctl.selected_in_playlist, 0)

				if inp.key_return_press and not pref_box.enabled and not radiobox.active and not trans_edit_box.active:
					gui.pl_update = 1
					if pctl.selected_in_playlist > len(default_playlist) - 1:
						pctl.selected_in_playlist = 0
						shift_selection = []
					if default_playlist:
						pctl.jump(default_playlist[pctl.selected_in_playlist], pctl.selected_in_playlist)
						if album_mode:
							goto_album(pctl.playlist_playing_position)


		elif gui.mode == 3:

			if (key_shift_down and inp.mouse_click) or middle_click:
				if prefs.mini_mode_mode == 4:
					prefs.mini_mode_mode = 1
					window_size[0] = int(330 * gui.scale)
					window_size[1] = int(330 * gui.scale)
					SDL_SetWindowMinimumSize(t_window, window_size[0], window_size[1])
					SDL_SetWindowSize(t_window, window_size[0], window_size[1])
				else:
					prefs.mini_mode_mode = 4
					window_size[0] = int(320 * gui.scale)
					window_size[1] = int(90 * gui.scale)
					SDL_SetWindowMinimumSize(t_window, window_size[0], window_size[1])
					SDL_SetWindowSize(t_window, window_size[0], window_size[1])

			if prefs.mini_mode_mode == 5:
				mini_mode3.render()
			elif prefs.mini_mode_mode == 4:
				mini_mode2.render()
			else:
				mini_mode.render()

		t = toast_love_timer.get()
		if t < 1.8 and gui.toast_love_object is not None:
			track = gui.toast_love_object

			ww = 0
			if gui.lsp:
				ww = gui.lspw

			rect = (ww + 5 * gui.scale, gui.panelY + 5 * gui.scale, 235 * gui.scale, 39 * gui.scale)
			fields.add(rect)

			if coll(rect):
				toast_love_timer.force_set(10)
			else:
				ddt.rect(grow_rect(rect, 2 * gui.scale), colours.box_border)
				ddt.rect(rect, colours.queue_card_background)

				# fqo = copy.copy(pctl.force_queue[-1])

				ddt.text_background_colour = colours.queue_card_background

				if gui.toast_love_added:
					text = _("Loved track")
					heart_notify_icon.render(rect[0] + 9 * gui.scale, rect[1] + 8 * gui.scale, [250, 100, 100, 255])
				else:
					text = _("Un-Loved track")
					heart_notify_break_icon.render(
						rect[0] + 9 * gui.scale, rect[1] + 7 * gui.scale,
						[150, 150, 150, 255])

				ddt.text_background_colour = colours.queue_card_background
				ddt.text((rect[0] + 42 * gui.scale, rect[1] + 3 * gui.scale), text, colours.box_text, 313)
				ddt.text(
					(rect[0] + 42 * gui.scale, rect[1] + 20 * gui.scale),
					f"{track.track_number}. {track.artist} - {track.title}".strip(".- "), colours.box_text_label,
					13, max_w=rect[2] - 50 * gui.scale)

		t = queue_add_timer.get()
		if t < 2.5 and gui.toast_queue_object:
			track = pctl.get_track(gui.toast_queue_object.track_id)

			ww = 0
			if gui.lsp:
				ww = gui.lspw
			if search_over.active:
				ww = window_size[0] // 2 - (215 * gui.scale // 2)

			rect = (ww + 5 * gui.scale, gui.panelY + 5 * gui.scale, 215 * gui.scale, 39 * gui.scale)
			fields.add(rect)

			if coll(rect):
				queue_add_timer.force_set(10)
			elif len(pctl.force_queue) > 0:

				fqo = copy.copy(pctl.force_queue[-1])

				ddt.rect(grow_rect(rect, 2 * gui.scale), colours.box_border)
				ddt.rect(rect, colours.queue_card_background)

				ddt.text_background_colour = colours.queue_card_background
				top_text = _("Track")
				if gui.queue_toast_plural:
					top_text = "Album"
					fqo.type = 1
				if pctl.force_queue[-1].type == 1:
					top_text = "Album"

				queue_box.draw_card(
					rect[0] - 8 * gui.scale, 0, 160 * gui.scale, 210 * gui.scale,
					rect[1] + 1 * gui.scale, track, fqo, True, False)

				ddt.text_background_colour = colours.queue_card_background
				ddt.text(
					(rect[0] + rect[2] - 50 * gui.scale, rect[1] + 3 * gui.scale, 2), f"{top_text} added",
					colours.box_text_label, 11)
				ddt.text(
					(rect[0] + rect[2] - 50 * gui.scale, rect[1] + 15 * gui.scale, 2), "to queue",
					colours.box_text_label, 11)

		t = toast_mode_timer.get()
		if t < 0.98:

			wid = ddt.get_text_w(gui.mode_toast_text, 313)
			wid = max(round(68 * gui.scale), wid)

			ww = round(7 * gui.scale)
			if gui.lsp and not gui.combo_mode:
				ww += gui.lspw

			rect = (ww + 8 * gui.scale, gui.panelY + 15 * gui.scale, wid + 20 * gui.scale, 25 * gui.scale)
			fields.add(rect)

			if coll(rect):
				toast_mode_timer.force_set(10)
			else:
				ddt.rect(grow_rect(rect, round(2 * gui.scale)), colours.grey(60))
				ddt.rect(rect, colours.queue_card_background)

				ddt.text_background_colour = colours.queue_card_background
				ddt.text((rect[0] + (rect[2] // 2), rect[1] + 4 * gui.scale, 2), gui.mode_toast_text, colours.grey(230), 313)

		# Render Menus-------------------------------
		for instance in Menu.instances:
			instance.render()

		if view_box.active:
			view_box.render()

		tool_tip.render()
		tool_tip2.render()

		if console.show:
			rect = (20 * gui.scale, 40 * gui.scale, 580 * gui.scale, 200 * gui.scale)
			ddt.rect(rect, [0, 0, 0, 245])

			yy = rect[3] + 15 * gui.scale
			u = False
			for record in reversed(log.log_history):

				if yy < rect[1] + 5 * gui.scale:
					break

				text_colour = [60, 255, 60, 255]
				message = log.format(record)

				t = record.created
				d = time.time() - t
				dt = time.localtime(t)

				fade = 255
				if d > 2:
					fade = 200

				text_colour = [120, 120, 120, fade]
				if record.levelno == 10:
					text_colour = [80, 80, 80, fade]
				if record.levelno == 30:
					text_colour = [230, 190, 90, fade]
				if record.levelno == 40:
					text_colour = [255, 120, 90, fade]
				if record.levelno == 50:
					text_colour = [255, 90, 90, fade]

				time_colour = [255, 80, 160, fade]

				w = ddt.text(
					(rect[0] + 10 * gui.scale, yy), time.strftime("%H:%M:%S", dt), time_colour, 311,
					rect[2] - 60 * gui.scale, bg=[5,5,5,255])

				ddt.text((w + rect[0] + 17 * gui.scale, yy), message, text_colour, 311, rect[2] - 60 * gui.scale, bg=[5,5,5,255])
				yy -= 14 * gui.scale
			if u:
				gui.delay_frame(5)

			if draw.button("Copy", rect[0] + rect[2] - 55 * gui.scale, rect[1] + rect[3] - 30 * gui.scale):

				text = ""
				for record in log.log_history[-50:]:
					t = record.created
					dt = time.localtime(t)
					text += time.strftime("%H:%M:%S", dt) + " " + log.format(record) + "\n"
				copy_to_clipboard(text)
				show_message(_("Lines copied to clipboard"), mode="done")

		if gui.cursor_is != gui.cursor_want:

			gui.cursor_is = gui.cursor_want

			if gui.cursor_is == 0:
				SDL_SetCursor(cursor_standard)
			elif gui.cursor_is == 1:
				SDL_SetCursor(cursor_shift)
			elif gui.cursor_is == 2:
				SDL_SetCursor(cursor_text)
			elif gui.cursor_is == 3:
				SDL_SetCursor(cursor_hand)
			elif gui.cursor_is == 4:
				SDL_SetCursor(cursor_br_corner)
			elif gui.cursor_is == 8:
				SDL_SetCursor(cursor_right_side)
			elif gui.cursor_is == 9:
				SDL_SetCursor(cursor_top_side)
			elif gui.cursor_is == 10:
				SDL_SetCursor(cursor_left_side)
			elif gui.cursor_is == 11:
				SDL_SetCursor(cursor_bottom_side)

		get_sdl_input.test_capture_mouse()
		get_sdl_input.mouse_capture_want = False

		# # Quick view
		# quick_view_box.render()

		# Drag icon next to cursor
		if quick_drag and mouse_down and not point_proximity_test(
			gui.drag_source_position, mouse_position, 15 * gui.scale):
			i_x, i_y = get_sdl_input.mouse()
			gui.drag_source_position = (0, 0)

			block_size = round(10 * gui.scale)
			x_offset = round(20 * gui.scale)
			y_offset = round(1 * gui.scale)

			if len(shift_selection) == 1:  # Single track
				ddt.rect((i_x + x_offset, i_y + y_offset, block_size, block_size), [160, 140, 235, 240])
			elif key_ctrl_down:  # Add to queue undrouped
				small_block = round(6 * gui.scale)
				spacing = round(2 * gui.scale)
				ddt.rect((i_x + x_offset, i_y + y_offset, small_block, small_block), [160, 140, 235, 240])
				ddt.rect(
					(i_x + x_offset + spacing + small_block, i_y + y_offset, small_block, small_block), [160, 140, 235, 240])
				ddt.rect(
					(i_x + x_offset, i_y + y_offset + spacing + small_block, small_block, small_block), [160, 140, 235, 240])
				ddt.rect(
					(i_x + x_offset + spacing + small_block, i_y + y_offset + spacing + small_block, small_block, small_block),
					[160, 140, 235, 240])
				ddt.rect(
					(i_x + x_offset, i_y + y_offset + spacing + small_block + spacing + small_block, small_block, small_block),
					[160, 140, 235, 240])
				ddt.rect(
					(i_x + x_offset + spacing + small_block,
					i_y + y_offset + spacing + small_block + spacing + small_block,
					small_block, small_block), [160, 140, 235, 240])

			else:  # Multiple tracks
				long_block = round(25 * gui.scale)
				ddt.rect((i_x + x_offset, i_y + y_offset, block_size, long_block), [160, 140, 235, 240])

			# gui.update += 1
			gui.update_on_drag = True

		# Drag pl tab next to cursor
		if (playlist_box.drag) and mouse_down and not point_proximity_test(
			gui.drag_source_position, mouse_position, 10 * gui.scale):
			i_x, i_y = get_sdl_input.mouse()
			gui.drag_source_position = (0, 0)
			ddt.rect(
				(i_x + 20 * gui.scale, i_y + 3 * gui.scale, int(50 * gui.scale), int(15 * gui.scale)), [50, 50, 50, 225])
			# ddt.rect_r((i_x + 20 * gui.scale, i_y + 1 * gui.scale, int(60 * gui.scale), int(15 * gui.scale)), [240, 240, 240, 255], True)
			# ddt.draw_text((i_x + 75 * gui.scale, i_y - 0 * gui.scale, 1), pctl.multi_playlist[playlist_box.drag_on].title, [30, 30, 30, 255], 212, bg=[240, 240, 240, 255])
		if radio_view.drag and not point_proximity_test(radio_view.click_point, mouse_position, round(4 * gui.scale)):
			ddt.rect((
				mouse_position[0] + round(8 * gui.scale), mouse_position[1] - round(8 * gui.scale), 48 * gui.scale,
				14 * gui.scale), colours.grey(70))
		if (gui.set_label_hold != -1) and mouse_down:

			gui.update_on_drag = True

			if not point_proximity_test(gui.set_label_point, mouse_position, 3):
				i_x, i_y = get_sdl_input.mouse()
				gui.set_label_point = (0, 0)

				w = ddt.get_text_w(gui.pl_st[gui.set_label_hold][0], 212)
				w = max(w, 45 * gui.scale)
				ddt.rect(
					(i_x + 25 * gui.scale, i_y + 1 * gui.scale, w + int(20 * gui.scale), int(15 * gui.scale)),
					[240, 240, 240, 255])
				ddt.text(
					(i_x + 25 * gui.scale + w + int(20 * gui.scale) - 4 * gui.scale, i_y - 0 * gui.scale, 1),
					gui.pl_st[gui.set_label_hold][0], [30, 30, 30, 255], 212, bg=[240, 240, 240, 255])

		input_text = ""
		gui.update -= 1

		# logging.info("FRAME " + str(core_timer.get()))
		gui.update = min(gui.update, 1)
		gui.present = True

		SDL_SetRenderTarget(renderer, None)
		SDL_RenderCopy(renderer, gui.main_texture, None, gui.tracklist_texture_rect)

		if gui.turbo:
			gui.level_update = True

	# if gui.vis == 1 and pctl.playing_state != 1 and gui.level_peak != [0, 0] and gui.turbo:
	#
	#     # logging.info(gui.level_peak)
	#     gui.time_passed = gui.level_time.hit()
	#     if gui.time_passed > 1:
	#         gui.time_passed = 0
	#     while gui.time_passed > 0.01:
	#         gui.level_peak[1] -= 0.5
	#         if gui.level_peak[1] < 0:
	#             gui.level_peak[1] = 0
	#         gui.level_peak[0] -= 0.5
	#         if gui.level_peak[0] < 0:
	#             gui.level_peak[0] = 0
	#         gui.time_passed -= 0.020
	#
	#     gui.level_update = True

	if gui.level_update is True and not resize_mode and gui.mode != 3:
		gui.level_update = False

		SDL_SetRenderTarget(renderer, None)
		if not gui.present:
			SDL_RenderCopy(renderer, gui.main_texture, None, gui.tracklist_texture_rect)
			gui.present = True

		if gui.vis == 3:
			# Scrolling spectrogram

			# if not vis_update:
			#     logging.info("No UPDATE " + str(random.randint(1,50)))
			if len(gui.spec2_buffers) > 0 and gui.spec2_timer.get() > 0.04:
				# gui.spec2_timer.force_set(gui.spec2_timer.get() - 0.04)
				gui.spec2_timer.set()
				vis_update = True

			if len(gui.spec2_buffers) > 0 and vis_update:
				vis_update = False

				SDL_SetRenderTarget(renderer, gui.spec2_tex)
				for i, value in enumerate(gui.spec2_buffers[0]):
					ddt.rect(
						[gui.spec2_position, i, 1, 1],
						[
							min(255, prefs.spec2_base[0] + int(value * prefs.spec2_multiply[0])),
							min(255, prefs.spec2_base[1] + int(value * prefs.spec2_multiply[1])),
							min(255, prefs.spec2_base[2] + int(value * prefs.spec2_multiply[2])),
							255])

				del gui.spec2_buffers[0]

				gui.spec2_position += 1

				if gui.spec2_position > gui.spec2_w - 1:
					gui.spec2_position = 0

				SDL_SetRenderTarget(renderer, None)

			#
			# else:
			#     logging.info("animation stall" + str(random.randint(1, 10)))

			if prefs.spec2_scroll:

				gui.spec2_source.x = 0
				gui.spec2_source.y = 0
				gui.spec2_source.w = gui.spec2_position
				gui.spec2_dest.x = gui.spec2_rec.x + gui.spec2_rec.w - gui.spec2_position
				gui.spec2_dest.w = gui.spec2_position
				SDL_RenderCopy(renderer, gui.spec2_tex, gui.spec2_source, gui.spec2_dest)

				gui.spec2_source.x = gui.spec2_position
				gui.spec2_source.y = 0
				gui.spec2_source.w = gui.spec2_rec.w - gui.spec2_position
				gui.spec2_dest.x = gui.spec2_rec.x
				gui.spec2_dest.w = gui.spec2_rec.w - gui.spec2_position
				SDL_RenderCopy(renderer, gui.spec2_tex, gui.spec2_source, gui.spec2_dest)

			else:

				SDL_RenderCopy(renderer, gui.spec2_tex, None, gui.spec2_rec)

			if pref_box.enabled:
				ddt.rect((gui.spec2_rec.x, gui.spec2_rec.y, gui.spec2_rec.w, gui.spec2_rec.h), [0, 0, 0, 90])

		if gui.vis == 4 and gui.draw_vis4_top:
			showcase.render_vis(True)
			# gui.level_update = False

		if gui.vis == 2 and gui.spec is not None:

			# Standard spectrum visualiser

			if gui.update_spec == 0 and pctl.playing_state != 2:
				if vis_decay_timer.get() > 0.007:  # Controls speed of decay after stop
					vis_decay_timer.set()
					for i in range(len(gui.spec)):
						if gui.s_spec[i] > 0:
							if gui.spec[i] > 0:
								gui.spec[i] -= 1
							gui.level_update = True
				else:
					gui.level_update = True

			if vis_rate_timer.get() > 0.027:  # Limit the change rate #to 60 fps
				vis_rate_timer.set()

				if spec_smoothing and pctl.playing_state > 0:

					for i in range(len(gui.spec)):
						if gui.spec[i] > gui.s_spec[i]:
							gui.s_spec[i] += 1
							if abs(gui.spec[i] - gui.s_spec[i]) > 4:
								gui.s_spec[i] += 1
							if abs(gui.spec[i] - gui.s_spec[i]) > 6:
								gui.s_spec[i] += 1
							if abs(gui.spec[i] - gui.s_spec[i]) > 8:
								gui.s_spec[i] += 1

						elif gui.spec[i] == gui.s_spec[i]:
							pass
						elif gui.spec[i] < gui.s_spec[i] > 0:
							gui.s_spec[i] -= 1
							if abs(gui.spec[i] - gui.s_spec[i]) > 4:
								gui.s_spec[i] -= 1
							if abs(gui.spec[i] - gui.s_spec[i]) > 6:
								gui.s_spec[i] -= 1
							if abs(gui.spec[i] - gui.s_spec[i]) > 8:
								gui.s_spec[i] -= 1

					if pctl.playing_state == 0 and check_equal(gui.s_spec):
						gui.level_update = True
						time.sleep(0.008)
				else:
					gui.s_spec = gui.spec
			else:
				pass

			if not gui.test:

				SDL_SetRenderTarget(renderer, gui.spec1_tex)

				# ddt.rect_r(gui.spec_rect, colours.top_panel_background, True)
				ddt.rect((0, 0, gui.spec_w, gui.spec_h), colours.vis_bg)

				# xx = 0
				gui.bar.x = 0
				on = 0

				SDL_SetRenderDrawColor(
					renderer, colours.vis_colour[0],
					colours.vis_colour[1], colours.vis_colour[2],
					colours.vis_colour[3])

				for item in gui.s_spec:

					if on > 19:
						break
					on += 1

					item -= 1

					if item < 1:
						gui.bar.x += round(4 * gui.scale)
						continue

					item = min(item, 20)

					if gui.scale >= 2:
						item = round(item * gui.scale)

					gui.bar.y = 0 + gui.spec_h - item
					gui.bar.h = item

					SDL_RenderFillRect(renderer, gui.bar)

					gui.bar.x += round(4 * gui.scale)

				if pref_box.enabled:
					ddt.rect((0, 0, gui.spec_w, gui.spec_h), [0, 0, 0, 90])

				SDL_SetRenderTarget(renderer, None)
				SDL_RenderCopy(renderer, gui.spec1_tex, None, gui.spec1_rec)

		if gui.vis == 1:

			if prefs.backend == 2 or True:
				if pctl.playing_state == 1 or pctl.playing_state == 3:
					# gui.level_update = True
					while tauon.level_train and tauon.level_train[0][0] < time.time():

						l = tauon.level_train[0][1]
						r = tauon.level_train[0][2]

						gui.level_peak[0] = max(r, gui.level_peak[0])
						gui.level_peak[1] = max(l, gui.level_peak[1])

						del tauon.level_train[0]

				else:
					tauon.level_train.clear()

			SDL_SetRenderTarget(renderer, gui.spec_level_tex)

			x = window_size[0] - 20 * gui.scale - gui.offset_extra
			y = gui.level_y
			w = gui.level_w
			s = gui.level_s

			y = 0

			gui.spec_level_rec.x = round(x - 70 * gui.scale)
			ddt.rect_a((0, 0), (79 * gui.scale, 18 * gui.scale), colours.grey(10))

			x = round(gui.level_ww - 9 * gui.scale)
			y = 10 * gui.scale

			if prefs.backend == 2 or True:
				if (gui.level_peak[0] > 0 or gui.level_peak[1] > 0):
					# gui.level_update = True
					if pctl.playing_time < 1:
						gui.delay_frame(0.032)

					if pctl.playing_state == 1 or pctl.playing_state == 3:
						t = gui.level_decay_timer.hit()
						decay = 14 * t
						gui.level_peak[1] -= decay
						gui.level_peak[0] -= decay
					elif pctl.playing_state == 0 or pctl.playing_state == 2:
						gui.level_update = True
						time.sleep(0.016)
						t = gui.level_decay_timer.hit()
						decay = 16 * t
						gui.level_peak[1] -= decay
						gui.level_peak[0] -= decay

			for t in range(12):

				if gui.level_peak[0] < t:
					met = False
				else:
					met = True
				if gui.level_peak[0] < 0.2:
					met = False

				if gui.level_meter_colour_mode == 1:

					if not met:
						cc = [15, 10, 20, 255]
					else:
						cc = colorsys.hls_to_rgb(0.68 + (t * 0.015), 0.4, 0.7)
						cc = (int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)

				elif gui.level_meter_colour_mode == 2:

					if not met:
						cc = [11, 11, 13, 255]
					else:
						cc = colorsys.hls_to_rgb(0.63 - (t * 0.015), 0.4, 0.7)
						cc = (int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)

				elif gui.level_meter_colour_mode == 3:

					if not met:
						cc = [12, 6, 0, 255]
					else:
						cc = colorsys.hls_to_rgb(0.11 - (t * 0.010), 0.4, 0.7 + (t * 0.02))
						cc = (int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)

				elif gui.level_meter_colour_mode == 4:

					if not met:
						cc = [10, 10, 10, 255]
					else:
						cc = colorsys.hls_to_rgb(0.3 - (t * 0.03), 0.4, 0.7 + (t * 0.02))
						cc = (int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)

				else:

					if t < 7:
						cc = colours.level_green
						if met is False:
							cc = colours.level_1_bg
					elif t < 10:
						cc = colours.level_yellow
						if met is False:
							cc = colours.level_2_bg
					else:
						cc = colours.level_red
						if met is False:
							cc = colours.level_3_bg
				if gui.level > 0 and pctl.playing_state > 0:
					pass
				ddt.rect_a(((x - (w * t) - (s * t)), y), (w, w), cc)

			y -= 7 * gui.scale
			for t in range(12):

				if gui.level_peak[1] < t:
					met = False
				else:
					met = True
				if gui.level_peak[1] < 0.2:
					met = False

				if gui.level_meter_colour_mode == 1:

					if not met:
						cc = [15, 10, 20, 255]
					else:
						cc = colorsys.hls_to_rgb(0.68 + (t * 0.015), 0.4, 0.7)
						cc = (int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)

				elif gui.level_meter_colour_mode == 2:

					if not met:
						cc = [11, 11, 13, 255]
					else:
						cc = colorsys.hls_to_rgb(0.63 - (t * 0.015), 0.4, 0.7)
						cc = (int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)

				elif gui.level_meter_colour_mode == 3:

					if not met:
						cc = [12, 6, 0, 255]
					else:
						cc = colorsys.hls_to_rgb(0.11 - (t * 0.010), 0.4, 0.7 + (t * 0.02))
						cc = (int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)

				elif gui.level_meter_colour_mode == 4:

					if not met:
						cc = [10, 10, 10, 255]
					else:
						cc = colorsys.hls_to_rgb(0.3 - (t * 0.03), 0.4, 0.7 + (t * 0.02))
						cc = (int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)

				else:

					if t < 7:
						cc = colours.level_green
						if met is False:
							cc = colours.level_1_bg
					elif t < 10:
						cc = colours.level_yellow
						if met is False:
							cc = colours.level_2_bg
					else:
						cc = colours.level_red
						if met is False:
							cc = colours.level_3_bg

				if gui.level > 0 and pctl.playing_state > 0:
					pass
				ddt.rect_a(((x - (w * t) - (s * t)), y), (w, w), cc)

			SDL_SetRenderTarget(renderer, None)
			SDL_RenderCopy(renderer, gui.spec_level_tex, None, gui.spec_level_rec)

	if gui.present:
		# Possible bug older version of SDL (2.0.16) Wayland, setting render target to None causer last copy
		# to fail when resizing? Not a big deal as it doesn't matter what the target is when presenting, just
		# set to something else
		# SDL_SetRenderTarget(renderer, None)
		SDL_SetRenderTarget(renderer, gui.main_texture)
		SDL_RenderPresent(renderer)

		gui.present = False

	# -------------------------------------------------------------------------------------------
	# Misc things to update every tick

	# Update d-bus metadata on Linux
	if (pctl.playing_state == 1 or pctl.playing_state == 3) and pctl.mpris is not None:
		pctl.mpris.update_progress()

	# GUI time ticker update
	if (pctl.playing_state == 1 or pctl.playing_state == 3) and gui.lowered is False:
		if int(pctl.playing_time) != int(pctl.last_playing_time):
			pctl.last_playing_time = pctl.playing_time
			bottom_bar1.seek_time = pctl.playing_time
			if not prefs.power_save or window_is_focused():
				gui.update = 1

	# Auto save play times to disk
	if pctl.total_playtime - time_last_save > 600:
		try:
			if should_save_state:
				logging.info("Auto save playtime")
				with (user_directory / "star.p").open("wb") as file:
					pickle.dump(star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)
			else:
				logging.info("Dev mode, skip auto saving playtime")
		except PermissionError:
			logging.exception("Permission error encountered while writing database")
			show_message(_("Permission error encountered while writing database"), "error")
		except Exception:
			logging.exception("Unknown error encountered while writing database")
		time_last_save = pctl.total_playtime

	# Always render at least one frame per minute (to avoid SDL bugs I guess)
	if min_render_timer.get() > 60:
		min_render_timer.set()
		gui.pl_update = 1
		gui.update += 1

	# Save power if the window is minimized
	if gui.lowered:
		time.sleep(0.2)

if tauon.spot_ctl.playing:
	tauon.spot_ctl.control("stop")

# Send scrobble if pending
if lfm_scrobbler.queue and not lfm_scrobbler.running:
	lfm_scrobbler.start_queue()
	logging.info("Sending scrobble before close...")

if gui.mode < 3:
	old_window_position = get_window_position()


SDL_DestroyTexture(gui.main_texture)
SDL_DestroyTexture(gui.tracklist_texture)
SDL_DestroyTexture(gui.spec2_tex)
SDL_DestroyTexture(gui.spec1_tex)
SDL_DestroyTexture(gui.spec_level_tex)
ddt.clear_text_cache()
clear_img_cache(False)

SDL_DestroyWindow(t_window)

pctl.playerCommand = "unload"
pctl.playerCommandReady = True

if prefs.reload_play_state and pctl.playing_state in (1, 2):
	logging.info("Saving play state...")
	prefs.reload_state = (pctl.playing_state, pctl.playing_time)

if should_save_state:
	with (user_directory / "star.p").open("wb") as file:
		pickle.dump(star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)
	with (user_directory / "album-star.p").open("wb") as file:
		pickle.dump(album_star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)

gui.gallery_positions[pl_to_id(pctl.active_playlist_viewing)] = gui.album_scroll_px
save_state()

date = datetime.date.today()
if should_save_state:
	with (user_directory / "star.p.backup").open("wb") as file:
		pickle.dump(star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)
	with (user_directory / f"star.p.backup{str(date.month)}").open("wb") as file:
		pickle.dump(star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)

if tauon.stream_proxy and tauon.stream_proxy.download_running:
	logging.info("Stopping stream...")
	tauon.stream_proxy.stop()
	time.sleep(2)

try:
	if tauon.thread_manager.player_lock.locked():
		tauon.thread_manager.player_lock.release()
except RuntimeError as e:
	if str(e) == "release unlocked lock":
		logging.error("RuntimeError: Attempted to release already unlocked player_lock")
	else:
		logging.exception("Unknown RuntimeError trying to release player_lock")
except Exception:
	logging.exception("Unknown error trying to release player_lock")

if tauon.radio_server is not None:
	try:
		tauon.radio_server.server_close()
	except Exception:
		logging.exception("Failed to close radio server")

if system == "Windows" or msys:
	tray.stop()
	if smtc:
		sm.unload()
elif de_notify_support:
	try:
		song_notification.close()
		g_tc_notify.close()
		Notify.uninit()
	except Exception:
		logging.exception("uninit notification error")

try:
	instance_lock.close()
except Exception:
	logging.exception("No lock object to close")

def main(holder: Holder):
	IMG_Quit()
	SDL_QuitSubSystem(SDL_INIT_EVERYTHING)
	SDL_Quit()
	#logging.info("SDL unloaded")

	exit_timer = Timer()
	exit_timer.set()

	if not tauon.quick_close:
		while tauon.thread_manager.check_playback_running():
			time.sleep(0.2)
			if exit_timer.get() > 2:
				logging.warning("Phazor unload timeout")
				break

		while lfm_scrobbler.running:
			time.sleep(0.2)
			lfm_scrobbler.running = False
			if exit_timer.get() > 15:
				logging.warning("Scrobble wait timeout")
				break

	if tauon.sleep_lock is not None:
		del tauon.sleep_lock
	if tauon.shutdown_lock is not None:
		del tauon.shutdown_lock
	if tauon.play_lock is not None:
		del tauon.play_lock

	if tauon.librespot_p:
		time.sleep(1)
		logging.info("Killing librespot")
		tauon.librespot_p.kill()
		#tauon.librespot_p.communicate()

	cache_dir = tmp_cache_dir()
	if os.path.isdir(cache_dir):
		# This check can be Windows only, lazy deletes are fine on Linux/macOS
		if sys.platform == "win32":
			while tauon.cachement.running:
				logging.warning("Waiting for caching to stop before deleting cache directory…")
				time.sleep(0.2)
		logging.info("Clearing tmp cache")
		shutil.rmtree(cache_dir)

	logging.info("Bye!")
