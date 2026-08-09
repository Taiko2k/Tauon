"""Tauon Music Box

Preamble

Welcome to the Tauon Music Box source code.
I started this project when I was first learning python, as a result this code can be quite messy.
No doubt I have written some things terribly wrong or inefficiently in places.
I would highly recommend not using this project as an example on how to code cleanly or correctly.
"""

# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

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
import colorsys
import copy
import ctypes
import ctypes.util
import datetime
import gc as gbc
import gettext
import glob
import hashlib
import importlib
import io
import json
import locale as py_locale
import logging

# import magic
import math

# import mimetypes
import os
import pickle
import platform
import random
import re
import shlex
import shutil
import signal
import socket
import ssl
import subprocess
import sys
import threading
import time

# import type_enforced
import urllib.parse
import urllib.request
import webbrowser
import xml.etree.ElementTree as ET
import zipfile
from collections import OrderedDict, deque
from ctypes import (
	POINTER,
	Structure,
	byref,
	c_char_p,
	c_double,
	c_float,
	c_int,
	c_ubyte,
	c_uint,
	c_uint32,
	c_void_p,
	pointer,
)
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import certifi
import musicbrainzngs
import mutagen
import mutagen.apev2
import mutagen.flac
import mutagen.id3
import mutagen.mp4
import mutagen.oggopus
import mutagen.oggvorbis
import requests
import sdl3
from bs4 import BeautifulSoup
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter
from send2trash import send2trash
from unidecode import unidecode

builtins._ = lambda x: x

from tauon.t_modules import t_topchart, t_visuals  # noqa: E402
from tauon.t_modules.t_config import Config  # noqa: E402
from tauon.t_modules.t_db_migrate import (  # noqa: E402
	database_migrate,
	migrate_star_store_71,
)
from tauon.t_modules.t_custom import (  # noqa: E402
	SPECTRO_PRESETS as CL_SPECTRO_PRESETS,
	STACK_COUNTS as CL_STACK_COUNTS,
	TEMPLATES as CL_TEMPLATES,
	WIDGET_SPECS as CL_WIDGET_SPECS,
	AlbumflowWidget,
	CustomLayout,
	GridGalleryWidget,
	draw_layout_glyph,
)
from tauon.t_modules.t_draw import QuickThumbnail, TDraw  # noqa: E402
from tauon.t_modules.t_room import DreamRoom  # noqa: E402
from tauon.t_modules.t_enums import (  # noqa: E402
	Backend,
	GuiMode,
	LoaderCommand,
	MiniModeMode,
	PlayerState,
	PlayingState,
	QueueType,
	StopMode,
)
from tauon.t_modules.t_extra import (  # noqa: E402
	ColourGenCache,
	FPSCounter,
	FunctionStore,
	TestTimer,
	Timer,
	alpha_blend,
	alpha_mod,
	archive_file_scan,
	atomic_save,
	check_equal,
	clean_string,
	colour_slide,
	colour_value,
	coll_point,
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
	get_first_artist,
	get_folder_size,
	get_hms_time,
	get_modify_date_string,
	get_split_artists,
	get_year_from_string,
	grow_rect,
	hls_hue_mix,
	hls_pull_contrast,
	hls_to_rgb,
	hms_to_seconds,
	hsl_to_rgb,
	is_grey,
	is_light,
	j_chars,
	mac_styles,
	point_distance,
	point_proximity_test,
	reduce_paths,
	rgb_add_hls,
	rgb_to_hls,
	search_magic,
	search_magic_any,
	search_magic_beefy,
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
	window_is_focused,
	year_search,
)
from tauon.t_modules.t_guitar_chords import GuitarChords  # noqa: E402
from tauon.t_modules.t_jellyfin import Jellyfin  # noqa: E402
from tauon.t_modules.t_lyrics import genius, get_lrclib_challenge, lyric_sources, uses_scraping  # noqa: E402
from tauon.t_modules.t_nowplaying_macos import MacNowPlayingHelper  # noqa: E402
from tauon.t_modules.t_phazor import Cachement, get_phazor_path, phazor_exists, player4  # noqa: E402
from tauon.t_modules.t_prefs import Prefs  # noqa: E402
from tauon.t_modules.t_search import bandcamp_search  # noqa: E402
from tauon.t_modules.t_stream import StreamEnc  # noqa: E402
from tauon.t_modules.t_subsonic import SubsonicService  # noqa: E402
from tauon.t_modules.t_svgout import render_icons  # noqa: E402
from tauon.t_modules.t_tagscan import (  # noqa: E402
	Ape,
	Flac,
	M4a,
	Opus,
	TrackFile,
	Wav,
	lyrics_are_synced,
	parse_picture_block,
)
from tauon.t_modules.t_themeload import Deco, load_theme, save_theme  # noqa: E402
from tauon.t_modules.t_tidal import Tidal  # noqa: E402
from tauon.t_modules.t_models import (  # noqa: E402
	_MISC_TO_FIELD,
	ColourRGBA,
	Directories,
	Formats,
	LoadClass,
	RadioPlaylist,
	RadioStation,
	StarRecord,
	TauonPlaylist,
	TauonQueueItem,
	TrackClass,
	copy_trackfile_metadata,
	intern_track_strings,
	queue_item_gen,
	set_path,
	uid_gen,
)
from tauon.t_modules.t_state import (  # noqa: E402
	ColoursClass,
	DConsole,
	Decorator,
	Fonts,
	GuiVar,
	Input,
	KeyMap,
	LoadImageAsset,
	MenuIcon,
	MenuTrackRef,
	WhiteModImageAsset,
	asset_loader,
)
from tauon.t_modules.t_menu import Menu, MenuItem, close_all_menus  # noqa: E402
from tauon.t_modules.t_input import (
	SCROLL_ANIMATION_FRAME_INTERVAL,
	SCROLL_ANIMATION_MAX_FPS,
	SCROLL_PHYSICS_ACCELERATION_BOOST,
	SCROLL_PHYSICS_DAMPING,
	SCROLL_PHYSICS_FIXED_DAMPING,
	SCROLL_PHYSICS_FIXED_TIMESTEP,
	SCROLL_PHYSICS_GALLERY_PRECISE_PIXEL_BASE,
	SCROLL_PHYSICS_MAX_TIMESTEP,
	SCROLL_PHYSICS_MAX_VELOCITY,
	SCROLL_PHYSICS_MIN_VELOCITY,
	SCROLL_PHYSICS_MIN_PIXELS,
	SCROLL_PHYSICS_PRECISE_MAX_TIMESTEP,
	SCROLL_PHYSICS_PRECISE_RELEASE_GRACE,
	SCROLL_PHYSICS_PRECISE_SMOOTHING,
	SCROLL_PHYSICS_PRECISE_STOP_THRESHOLD,
	SCROLL_PHYSICS_PRECISE_WHEEL_PIXEL_MULTIPLIER,
	SCROLL_PHYSICS_REPEAT_ACCELERATION,
	SCROLL_PHYSICS_REPEAT_CURVE,
	SCROLL_PHYSICS_REPEAT_WINDOW,
	SCROLL_PHYSICS_TOUCH_DRAG_MULTIPLIER,
	SCROLL_PHYSICS_TOUCH_FLING_MULTIPLIER,
	SCROLL_PHYSICS_WHEEL_MAGNITUDE_ACCELERATION,
	SCROLL_PHYSICS_WHEEL_MAX_VELOCITY_MULTIPLIER,
	SCROLL_PHYSICS_WHEEL_VELOCITY,
	TOUCH_LOGIC_COOL_GESTURE_PIXELS_TO_SKIP_TRACK,
	TOUCH_LOGIC_TAP_VS_LONG_NS,
	GetSDLInput,
	copy_from_clipboard,
	copy_to_clipboard,
	field_clear,
	field_copy,
	field_paste,
	ScrollMotionState,
	SmoothScroll,
	TouchInputTracker,
	XcursorImage,
)  # noqa: E402
from tauon.t_modules.t_player import PlayerCtl, WinTask  # noqa: E402
from tauon.t_modules.t_lyrics_ui import (
	LyricsRen,
	LyricsRenMini,
	TimedLyricsEdit,
	TimedLyricsRen,
	TimedLyricsToStatic,
	find_synced_lyric_data,
	strip_lrc_formatting,
)  # noqa: E402
from tauon.t_modules.t_scrobble import LastFMapi, LastScrob, ListenBrainz, pylast  # noqa: E402
from tauon.t_modules.t_stars import StarStore  # noqa: E402
from tauon.t_modules.t_services import AlbumStarStore, GStats, PlexService, TauService  # noqa: E402
from tauon.t_modules.t_text import MultiLineTextBox, TextBox, TextBox2  # noqa: E402
from tauon.t_modules.t_workers import DLMon, ThreadManager  # noqa: E402
from tauon.t_modules.t_widgets import (
	Drawing,
	DropShadow,
	EdgePulse,
	EdgePulse2,
	Fader,
	Fields,
	ScrollBox,
	ToolTip,
	ToolTip3,
	Undo,
)  # noqa: E402
from tauon.t_modules.t_art import AlbumArt, GallClass, ImageObject, ThumbTracks  # noqa: E402
from tauon.t_modules.t_overlays import (
	ExportPlaylistBox,
	MessageBox,
	NagBox,
	PowerTag,
	PresetDownloadBox,
	RenameTrackBox,
	SearchOverlay,
	StyleOverlay,
	SubLyricsBox,
	TransEditBox,
)  # noqa: E402
from tauon.t_modules.t_playlist import (
	ArtistList,
	ArtistListSaveState,
	PlaylistBox,
	QueueBox,
	RenamePlaylistBox,
	SCROLL_PHYSICS_TRACKLIST_PRECISE_SCALE,
	StandardPlaylist,
	TreeView,
)  # noqa: E402
from tauon.t_modules.t_panels import (
	ArtBox,
	ArtistInfoBox,
	BottomBarType1,
	BottomBarType_ao1,
	MetaBox,
	MiniMode,
	MiniMode2,
	MiniMode3,
	MiniModeSignal,
	PictureRender,
	RadioBox,
	RadioThumbGen,
	RadioView,
	TopPanel,
)  # noqa: E402
from tauon.t_modules.t_templates import (
	add_pl_tag,
	encode_folder_name,
	encode_track_name,
	parse_generator,
	parse_template,
	parse_template2,
	re_template_word,
	unique_template,
)  # noqa: E402
from tauon.t_modules.t_visuals import (
	ColourPulse2,
	DrawnIcon,
	MilkPresetChooser,
	Milky,
	ProjectM,
	Showcase,
	ViewBox,
	_draw_custom_layout_icon,
	draw_showcase_art_box,
	find_projectm_library,
	get_renderer_name,
	renderer_name_supports_milkdrop,
)  # noqa: E402
from tauon.t_modules.t_settings import (  # noqa: E402
	THEME_EDITOR_COMPONENTS,
	Over,
	auto_get_sync_targets,
	auto_scale,
	clone_theme_colours,
	get_theme_name,
	get_theme_number,
	get_themes,
)
from tauon.t_modules.t_webserve import (  # noqa: E402
	VorbisMonitor,
	authserve,
	controller,
	stream_proxy,
	webserve,
	webserve2,
)

if sys.platform == "linux":
	import gi

	try:
		gi.require_version("Notify", "0.7")
	except Exception:
		logging.exception("Failed importing gi Notify 0.7, will try 0.8")
		gi.require_version("Notify", "0.8")
	from gi.repository import GdkPixbuf, GLib, Notify

if sys.platform == "darwin":
	import gi
	from gi.repository import GLib

try:
	from jxlpy import JXLImagePlugin

	# We've already logged this once to INFO from t_draw, so just log to DEBUG
	logging.debug("Found jxlpy for JPEG XL support")
except ModuleNotFoundError:
	logging.warning("Unable to import jxlpy, JPEG XL support will be disabled.")
except Exception:
	logging.exception("Unknown error trying to import jxlpy, JPEG XL support will be disabled.")

if not sys.platform == "darwin":
	try:
		import setproctitle
	except ModuleNotFoundError:
		logging.warning("Unable to import setproctitle, won't be setting process title.")
	except Exception:
		logging.exception("Unknown error trying to import setproctitle, won't be setting process title.")
	else:
		setproctitle.setproctitle("tauonmb")

# try:
# 	import rpc
# 	discord_allow = True
# except Exception:
# 	logging.exception("Unable to import rpc, Discord Rich Presence will be disabled.")
try:
	from pypresence import ActivityType, StatusDisplayType, Presence
except ModuleNotFoundError:
	logging.warning("Unable to import pypresence, Discord Rich Presence will be disabled.")
except Exception:
	logging.exception("Unknown error trying to import pypresence, Discord Rich Presence will be disabled.")
else:
	import asyncio

try:
	import opencc
except ModuleNotFoundError:
	logging.warning(
		"Unable to import opencc, Traditional and Simplified Chinese searches will not be usable interchangeably."
	)
except Exception:
	logging.exception(
		"Unknown error trying to import opencc, Traditional and Simplified Chinese searches will not be usable interchangeably."
	)

try:
	import natsort
except ModuleNotFoundError:
	logging.warning("Unable to import natsort, playlists may not sort as intended!")
except Exception:
	logging.exception("Unknown error trying to import natsort, playlists may not sort as intended!")

CJK_SEARCH_PATTERN = re.compile(
	r"[\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df\u2a700-\u2b73f\u2b740-\u2b81f\u2b820-\u2ceaf\uf900-\ufaff\u2f800-\u2fa1f]"
)

try:
	from tauon.t_modules.t_chrome import Chrome
	logging.debug("Found Chrome(pychromecast) for chromecast support")
except ModuleNotFoundError as e:
	logging.debug(f"pychromecast import error: {e}")
	logging.warning("Unable to import Chrome(pychromecast), chromecast support will be disabled.")
except Exception:
	logging.exception("Unknown error trying to import Chrome(pychromecast), chromecast support will be disabled.")

if TYPE_CHECKING:
	from ctypes import CDLL
	from io import BufferedReader, BytesIO
	from typing import ClassVar

	from PIL.ImageFile import ImageFile
	from websocket import WebSocketApp

	from tauon.t_modules.t_bootstrap import Holder
	from tauon.t_modules.t_dbus import MPRIS
	from tauon.t_modules.t_logging import LogHistoryHandler
	from collections.abc import Callable, Sequence
	from subprocess import Popen

	from tauon.t_modules.t_webserve import ThreadedHTTPServer

# Detect platform
macos: bool = False
windows: bool = False
arch: str = platform.machine()
platform_release: str = platform.release()
platform_system: str = platform.system()
win_ver: int = 0
if platform_system == "Windows":
	try:
		win_ver = int(platform_release)
	except Exception:
		logging.exception("Failed getting Windows version from platform.release()")

if sys.platform == "win32":
	windows = True
	import gi
	from gi.repository import GLib

if sys.platform == "darwin":
	macos = True

if not macos and not windows:
	from tauon.t_modules.t_dbus import Gnome

CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")




		# tauon.view_box.off_colour = self.grey(200)

class MOD(Structure):
	"""Access functions from libopenmpt for scanning tracker files"""

	_fields_ = [("ctl", c_char_p), ("value", c_char_p)]

class GMETrackInfo(Structure):
	_fields_ = [
		("length", c_int),
		("intro_length", c_int),
		("loop_length", c_int),
		("play_length", c_int),
		("fade_length", c_int),
		("i5", c_int),
		("i6", c_int),
		("i7", c_int),
		("i8", c_int),
		("i9", c_int),
		("i10", c_int),
		("i11", c_int),
		("i12", c_int),
		("i13", c_int),
		("i14", c_int),
		("i15", c_int),
		("system", c_char_p),
		("game", c_char_p),
		("song", c_char_p),
		("author", c_char_p),
		("copyright", c_char_p),
		("comment", c_char_p),
		("dumper", c_char_p),
		("s7", c_char_p),
		("s8", c_char_p),
		("s9", c_char_p),
		("s10", c_char_p),
		("s11", c_char_p),
		("s12", c_char_p),
		("s13", c_char_p),
		("s14", c_char_p),
		("s15", c_char_p),
	]


class Strings:

	def __init__(self) -> None:
		self.day = _("day")
		self.days = _("days")

		self.scan_chrome = _("Scanning for Chromecasts...")
		self.cast_to = _("Cast to: %s")
		self.no_chromecasts = _("No Chromecast devices found")
		self.stop_cast = _("End Cast")

		self.web_server_stopped = _("Web server stopped.")

		self.menu_open_tauon = _("Open Tauon Music Box")
		self.menu_play_pause = _("Play/Pause")
		self.menu_next = _("Next Track")
		self.menu_previous = _("Previous Track")
		self.menu_quit = _("Quit")

class Chunker:

	def __init__(self) -> None:
		self.master_count = 0
		self.chunks = {}
		self.header = None
		self.headers = []
		self.h2 = None

		self.clients = {}


class Tauon:
	"""Root class for everything Tauon"""

	def __init__(self, holder: Holder, bag: Bag, gui: GuiVar) -> None:
		self.use_cc                       = is_module_loaded("opencc")
		self.use_natsort                  = is_module_loaded("natsort")
		self._opencc_local                = threading.local()

		self.bag: Bag                          = bag
		self.log: LogHistoryHandler            = bag.log
		self.mpt: CDLL | None                  = bag.mpt
		self.gme: CDLL | None                  = bag.gme
		self.dev_mode: bool                    = bag.dev_mode
		self.renderer               = bag.renderer
		self.ddt: TDraw                        = TDraw(bag.renderer)
		self.fonts: Fonts                      = bag.fonts
		self.formats: Formats                  = bag.formats
		self.macos: bool                       = bag.macos
		self.mac_close: ColourRGBA             = bag.mac_close
		self.mac_maximize: ColourRGBA          = bag.mac_maximize
		self.mac_minimize: ColourRGBA          = bag.mac_minimize
		self.platform_system: str              = bag.platform_system
		self.primary_stations: list[RadioStation] = bag.primary_stations
		self.wayland: bool                      = bag.wayland
		self.windows: bool                         = bag.windows
		self.dirs: Directories                  = bag.dirs
		self.colours: ColoursClass              = bag.colours
		self.download_directories: list[str]    = bag.download_directories
		self.launch_prefix: str                 = bag.launch_prefix
		self.overlay_texture_texture            = bag.overlay_texture_texture
		self.de_notify_support: bool            = bag.de_notify_support
		self.old_window_position: tuple[int, int]          = bag.old_window_position
		self.mini_mode_restore_size: tuple[int, int] | None = None
		self.mini_mode_wm_forced_floating: bool = False
		self.mini_mode_wm_was_floating: bool = False
		self._wayland_wm_ipc_warned: bool = False
		self.cache_directory: Path              = bag.dirs.cache_directory
		self.config_directory: Path             = bag.dirs.config_directory
		self.user_directory: Path               = bag.dirs.user_directory
		self.install_directory: Path            = bag.dirs.install_directory
		self.music_directory: Path              = bag.dirs.music_directory
		self.locale_directory: Path             = bag.dirs.locale_directory
		self.n_cache_directory: Path            = bag.dirs.n_cache_directory
		self.e_cache_directory: Path            = bag.dirs.e_cache_directory
		self.g_cache_directory: Path            = bag.dirs.g_cache_directory
		self.a_cache_directory: Path            = bag.dirs.a_cache_directory
		self.r_cache_directory: Path            = bag.dirs.r_cache_directory
		self.b_cache_directory: Path            = bag.dirs.b_cache_directory
		self.draw_max_button: bool              = bag.draw_max_button
		self.draw_min_button: bool              = bag.draw_min_button
		self.song_notification: None            = bag.song_notification
		self.tls_context: ssl.SSLContext        = bag.tls_context
		self.folder_image_offsets: dict[str, int] = bag.folder_image_offsets
		self.inp: Input                          = gui.inp
		self.instance_lock: io.TextIOWrapper[io._WrappedBuffer] | None = holder.instance_lock
		self.n_version: str                    = holder.n_version
		self.t_window                     = holder.t_window
		self.t_title: str                         = holder.t_title
		self.t_version: str                       = holder.t_version
		self.t_agent: str                         = holder.t_agent
		self.t_id: str                            = holder.t_id
		self.fs_mode: bool                        = holder.fs_mode
		self.window_default_size: tuple[int, int] = holder.window_default_size
		self.window_title: bytes                  = holder.window_title
		self.logical_size: list[int]              = bag.logical_size
		self.window_size: list[int]               = bag.window_size
		self.draw_border: bool                    = holder.draw_border
		self.corner_mask_textures: list | None    = None
		self.corner_border_textures: list | None  = None
		self.corner_texture_size: tuple[int, int] = (0, 0)
		self.corner_textures_failed: bool         = False
		self.desktop: str | None                  = bag.desktop
		self.pid: int                             = os.getpid()
		# List of encodings to check for with the fix mojibake function
		self.encodings: list[str] = ["cp932", "utf-8", "big5hkscs", "gbk"]  # These seem to be the most common for Japanese
		self.column_names = (
			"Artist",
			"Album Artist",
			"Album",
			"Album Art",
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
			"ID",
			"=/=",
		)
		self.device: str                       = socket.gethostname()
		self.search_string_cache:     dict[int, str] = {}
		self.search_dia_string_cache: dict[int, str] = {}
		self.search_field_cache:      dict[int, tuple[str, str, str, str, str, str, str, str, str, str, str, str, str]] = {}
		self.search_dia_field_cache:  dict[int, tuple[str, str, str, str, str, str, str, str]] = {}
		self.albums:            list[int] = []
		self.added:             list[int] = []
		self.album_dex:         list[int] = []
		self.album_dex_pl_uuid:       int = -1  # uuid_int of the playlist album_dex was built for
		self.to_scan:           list[int] = []
		self.after_scan: list[TrackClass] = []
		self.quick_import_done: list[str] = []
		self.move_jobs: list[tuple[str, str, bool, str, LoadClass]] = []
		self.move_in_progress:       bool = False
		self.worker2_lock: threading.LockType                 = threading.Lock()
		self.dummy_event:          sdl3.SDL_Event = sdl3.SDL_Event()
		self.temp_dest:            sdl3.SDL_FRect = sdl3.SDL_FRect(0, 0)
		self.text_box_canvas_rect:      sdl3.SDL_FRect = sdl3.SDL_FRect(0, 0, round(2000 * gui.scale), round(40 * gui.scale))
		self.text_box_canvas_hide_rect: sdl3.SDL_FRect = sdl3.SDL_FRect(0, 0, round(2000 * gui.scale), round(40 * gui.scale))
		self.text_box_canvas           = sdl3.SDL_CreateTexture(
			self.renderer, sdl3.SDL_PIXELFORMAT_ARGB8888,
			sdl3.SDL_TEXTUREACCESS_TARGET, round(self.text_box_canvas_rect.w), round(self.text_box_canvas_rect.h))
		self.translate                            = _
		self.strings: Strings                              = Strings()
		self.gui: GuiVar                                  = gui
		self.prefs: Prefs                                = bag.prefs
		self.snap_mode: bool                            = bag.snap_mode
		self.flatpak_mode: bool                         = bag.flatpak_mode
		self.core_use: int                        = 0
		self.dl_use: int                          = 0
		self.latest_db_version: int                    = bag.latest_db_version
		self.g_tc_notify: Notify.Notification | None                          = None
		# Setting various timers
		self.track_box_path_tool_timer: Timer    = Timer()
		self.message_box_min_timer: Timer        = Timer()
		self.cursor_blink_timer: Timer           = Timer()
		self.animate_monitor_timer: Timer        = Timer()
		self.min_render_timer: Timer             = Timer()
		self.vis_rate_timer: Timer               = Timer()
		self.vis_decay_timer: Timer              = Timer()
		self.scroll_timer: Timer                 = Timer()
		self.scroll_timer.set()
		self.scroll_animation_deadline: float    = 0.0
		self.perf_timer: Timer                   = Timer() # Reassigned later
		self.quick_d_timer: Timer                = Timer()
		self.core_timer: Timer                   = Timer() # Reassigned later
		self.sleep_timer: Timer                  = Timer()
		self.gallery_select_animate_timer: Timer = Timer()
		self.gallery_select_animate_timer.force_set(10)
		self.search_clear_timer: Timer           = Timer()
		self.gall_pl_switch_timer: Timer         = Timer()
		self.gall_pl_switch_timer.force_set(999)
		self.d_click_timer: Timer                = Timer()
		self.d_click_timer.force_set(10)
		self.lyrics_check_timer: Timer           = Timer()
		self.scroll_hide_timer: Timer            = Timer(100)
		self.scroll_gallery_hide_timer: Timer    = Timer(100)
		self.get_lfm_wait_timer: Timer           = Timer(10)
		self.lyrics_fetch_timer: Timer           = Timer(10)
		self.gallery_load_delay: Timer           = Timer(10)
		self.queue_add_timer: Timer              = Timer(100)
		self.toast_love_timer: Timer             = Timer(100)
		self.toast_mode_timer: Timer             = Timer(100)
		self.scrobble_warning_timer: Timer       = Timer(1000)
		self.sync_file_timer: Timer              = Timer(1000)
		self.sync_file_update_timer: Timer       = Timer(1000)
		self.restore_ignore_timer: Timer         = Timer()
		self.restore_ignore_timer.force_set(100)
		self.fields: Fields = Fields(self)
		# Create top menu
		self.view_menu: Menu             = Menu(self, 170)
		self.set_menu_hidden: Menu       = Menu(self, 100)
		self.window_menu: Menu           = Menu(self, 160)
		self.x_menu: Menu                = Menu(self, 190, show_icons=True)
		self.set_menu: Menu              = Menu(self, 150)
		self.field_menu: Menu            = Menu(self, 140)
		self.dl_menu: Menu               = Menu(self, 90)

		self.cancel_menu: Menu           = Menu(self, 100)
		self.extra_menu: Menu            = Menu(self, 175, show_icons=True)
		self.stop_menu: Menu             = Menu(self, 175, show_icons=False)
		self.shuffle_menu: Menu          = Menu(self, 120)
		self.repeat_menu: Menu           = Menu(self, 120)
		self.tab_menu: Menu              = Menu(self, 160, show_icons=True)
		self.playlist_menu: Menu         = Menu(self, 130)
		self.showcase_menu: Menu         = Menu(self, 135)
		# Showcase view's own background menu: the lyrics menu plus
		# showcase-specific layout settings (wide mode, visualiser)
		self.showcase_view_menu: Menu    = Menu(self, 160)
		self.queue_menu: Menu            = Menu(self, 150)
		self.radio_entry_menu: Menu      = Menu(self, 125)
		self.center_info_menu: Menu      = Menu(self, 125)
		self.gallery_menu: Menu          = Menu(self, 175, show_icons=True)
		self.artist_info_menu: Menu      = Menu(self, 135)
		self.artist_list_menu: Menu      = Menu(self, 165, show_icons=True)
		self.lightning_menu: Menu        = Menu(self, 165)
		self.lsp_menu: Menu              = Menu(self, 145)
		self.folder_tree_menu: Menu      = Menu(self, 175, show_icons=True)
		self.folder_tree_stem_menu: Menu = Menu(self, 190, show_icons=True)
		self.overflow_menu: Menu         = Menu(self, 175)
		self.radio_context_menu: Menu    = Menu(self, 175)
		self.radio_tab_menu: Menu        = Menu(self, 160, show_icons=True)
		self.mode_menu: Menu             = Menu(self, 175)
		self.track_menu: Menu            = Menu(self, 195, show_icons=True)
		self.picture_menu: Menu          = Menu(self, 175)
		self.milky_menu: Menu            = Menu(self, 175)
		self.selection_menu: Menu        = Menu(self, 200, show_icons=False)
		self.folder_menu: Menu           = Menu(self, 193, show_icons=True)
		self.extra_tab_menu: Menu        = Menu(self, 155, show_icons=True)

		# Lazily created popup windows for context menus (see draw_popup_menus /
		# t_window): the main column and the active submenu each get their own.
		# active_pointer_window is whichever of them the pointer is currently in.
		self.menu_popup = None
		self.submenu_popup = None
		self.active_pointer_window = None

		self.smooth_scroll:                     SmoothScroll = SmoothScroll(tauon=self)
		self.lb:                                ListenBrainz = ListenBrainz(
			tauon=self,
			copy_from_clipboard_fn=copy_from_clipboard,
			save_prefs_fn=save_prefs,
		)
		self.thread_manager:                   ThreadManager = ThreadManager(tauon=self)
		self.album_mode_art_size:                        int = bag.album_mode_art_size
		self.artist_picture_render:            PictureRender = PictureRender(tauon=self)
		self.artist_preview_render:            PictureRender = PictureRender(tauon=self)
		self.input_sdl:                          GetSDLInput = GetSDLInput(tauon=self)
		self.pctl:                                 PlayerCtl = PlayerCtl(tauon=self)
		self.mini_lyrics_scroll:                   ScrollBox = self.pctl.mini_lyrics_scroll
		self.playlist_panel_scroll:                ScrollBox = self.pctl.playlist_panel_scroll
		self.artist_info_scroll:                   ScrollBox = self.pctl.artist_info_scroll
		self.device_scroll:                        ScrollBox = self.pctl.device_scroll
		self.artist_list_scroll:                   ScrollBox = self.pctl.artist_list_scroll
		self.gallery_scroll:                       ScrollBox = self.pctl.gallery_scroll
		self.tree_view_scroll:                     ScrollBox = self.pctl.tree_view_scroll
		self.radio_view_scroll:                    ScrollBox = self.pctl.radio_view_scroll
		self.artist_info_box:                  ArtistInfoBox = self.pctl.artist_info_box
		self.draw:                                   Drawing = self.pctl.draw
		self.radiobox:                              RadioBox = self.pctl.radiobox
		self.dummy_track:                         TrackClass = self.radiobox.dummy_track
		self.queue_box:                             QueueBox = self.pctl.queue_box
		self.tree_view_box:                         TreeView = self.pctl.tree_view_box
		self.star_store:                           StarStore = self.pctl.star_store
		self.lastfm:                               LastFMapi = self.pctl.lastfm
		self.lfm_scrobbler:                        LastScrob = self.pctl.lfm_scrobbler
		self.artist_list_box:                     ArtistList = self.pctl.artist_list_box
		self.touch_input_tracker:          TouchInputTracker = TouchInputTracker(tauon=self)
		self.guitar_chords:                     GuitarChords = GuitarChords(tauon=self, mouse_wheel=self.inp.mouse_wheel, mouse_position=self.inp.mouse_position, window_size=self.window_size)
		self.search_over:                      SearchOverlay = SearchOverlay(tauon=self)
		self.stats_gen:                               GStats = GStats(tauon=self)
		self.deco:                                      Deco = Deco(tauon=self)
		self.bottom_bar1:                     BottomBarType1 = BottomBarType1(tauon=self)
		self.bottom_bar_ao1:               BottomBarType_ao1 = BottomBarType_ao1(tauon=self)
		self.top_panel:                             TopPanel = TopPanel(tauon=self)
		self.playlist_box:                       PlaylistBox = PlaylistBox(tauon=self)
		self.radio_view:                           RadioView = RadioView(tauon=self)
		self.view_box:                               ViewBox = ViewBox(tauon=self)
		self.custom:                            CustomLayout = CustomLayout(tauon=self)
		self.dream_room:                           DreamRoom = DreamRoom(tauon=self)
		self.pref_box:                                  Over = Over(tauon=self)
		self.fader:                                    Fader = Fader(tauon=self)
		self.style_overlay:                     StyleOverlay = StyleOverlay(tauon=self)
		self.album_art_gen:                         AlbumArt = self.style_overlay.album_art_gen
		self.tool_tip:                               ToolTip = ToolTip(tauon=self)
		self.tool_tip2:                              ToolTip = ToolTip(tauon=self)
		self.columns_tool_tip:                      ToolTip3 = ToolTip3(tauon=self)
		self.f_store:                          FunctionStore = FunctionStore()
		self.tool_tip2.trigger:                        float = 1.8
		self.undo:                                      Undo = Undo(tauon=self)
		self.rename_files:                          TextBox2 = TextBox2(tauon=self)
		self.rename_track_box:                RenameTrackBox = RenameTrackBox(tauon=self)
		self.edit_artist:                           TextBox2 = TextBox2(tauon=self)
		self.edit_album:                            TextBox2 = TextBox2(tauon=self)
		self.edit_title:                            TextBox2 = TextBox2(tauon=self)
		self.edit_album_artist:                     TextBox2 = TextBox2(tauon=self)
		self.trans_edit_box:                    TransEditBox = TransEditBox(tauon=self)
		self.sub_lyrics_a:                          TextBox2 = TextBox2(tauon=self)
		self.sub_lyrics_b:                          TextBox2 = TextBox2(tauon=self)
		self.sub_lyrics_box:                      SubLyricsBox = SubLyricsBox(tauon=self)
		self.export_playlist_box:                 ExportPlaylistBox = ExportPlaylistBox(tauon=self)
		self.rename_text_area:                    TextBox = TextBox(tauon=self)
		self.rename_playlist_box:                 RenamePlaylistBox = RenamePlaylistBox(tauon=self)
		self.message_box:                         MessageBox = MessageBox(tauon=self)
		self.preset_download_box:                 PresetDownloadBox = PresetDownloadBox(tauon=self)
		self.milk_choose:                       MilkPresetChooser = MilkPresetChooser(tauon=self)
		self.search_text                          = self.search_over.search_text
		self.sync_target:                         TextBox2 = TextBox2(tauon=self)
		self.playlist_folder_box:                 TextBox2 = TextBox2(tauon=self)
		self.edge_playlist2:                      EdgePulse2 = EdgePulse2(tauon=self)
		self.lyric_side_top_pulse:                EdgePulse2 = EdgePulse2(tauon=self)
		self.lyric_side_bottom_pulse:             EdgePulse2 = EdgePulse2(tauon=self)
		self.tab_pulse:                           EdgePulse = EdgePulse(tauon=self)
		self.radio_thumb_gen:                     RadioThumbGen = RadioThumbGen(tauon=self)
		self.dl_mon:                              DLMon = DLMon(tauon=self)
		self.drop_shadow:                         DropShadow = DropShadow(tauon=self)
		self.lyrics_ren_mini:                     LyricsRenMini = LyricsRenMini(tauon=self)
		self.lyrics_ren:                          LyricsRen = LyricsRen(tauon=self)
		self.timed_lyrics_ren:                    TimedLyricsRen = TimedLyricsRen(tauon=self)
		self.synced_to_static_lyrics:             TimedLyricsToStatic = TimedLyricsToStatic()
		self.mini_mode:                           MiniMode = MiniMode(tauon=self)
		self.mini_mode2:                          MiniMode2 = MiniMode2(tauon=self)
		self.mini_mode3:                          MiniMode3 = MiniMode3(tauon=self)
		self.mini_mode_signal:                    MiniModeSignal = MiniModeSignal(tauon=self)
		self.vb:                                  VorbisMonitor = VorbisMonitor(tauon=self)
		self.bottom_playlist2:                    EdgePulse2 = EdgePulse2(tauon=self)
		self.gallery_pulse_top:                   EdgePulse2 = EdgePulse2(tauon=self)
		self.art_box:                             ArtBox = ArtBox(tauon=self)
		self.nagbox:                              NagBox = NagBox(tauon=self)

		if not self.macos and not self.windows:
			self.gnome = Gnome(tauon=self)

		self.text_plex_usr: TextBox2 = TextBox2(tauon=self)
		self.text_plex_pas: TextBox2 = TextBox2(tauon=self)
		self.text_plex_ser: TextBox2 = TextBox2(tauon=self)
		self.text_plex_lib: TextBox2 = TextBox2(tauon=self)
		self.text_plex_2fa: TextBox2 = TextBox2(tauon=self)

		self.text_jelly_usr: TextBox2 = TextBox2(tauon=self)
		self.text_jelly_pas: TextBox2 = TextBox2(tauon=self)
		self.text_jelly_ser: TextBox2 = TextBox2(tauon=self)

		self.text_air_usr: TextBox2 = TextBox2(tauon=self)
		self.text_air_pas: TextBox2 = TextBox2(tauon=self)
		self.text_air_ser: TextBox2 = TextBox2(tauon=self)

		self.text_maloja_url: TextBox2 = TextBox2(tauon=self)
		self.text_maloja_key: TextBox2 = TextBox2(tauon=self)

		self.text_sat_url:      TextBox2 = TextBox2(tauon=self)
		self.text_sat_playlist: TextBox2 = TextBox2(tauon=self)

		self.rename_folder: TextBox2 = TextBox2(tauon=self)
		self.transcode_list:      list[list[int]] = []
		self.transcode_state:                 str = ""
		self.loaderCommand:                   int = LoaderCommand.NONE
		self.loaderCommandReady:             bool = False
		self.cm_clean_db:                    bool = False
		self.worker_save_state:              bool = False
		self.whicher                              = whicher
		self.load_orders:         list[LoadClass] = []
		self.switch_playlist                      = self.pctl.switch_playlist
		self.album_info_cache: dict[int, tuple[bool, list[int], bool]] = {}
		self.album_info_cache_key: tuple[int, TrackClass | None, int] = (-1, None, -1)
		self.console:                    DConsole = bag.console
		self.TrackClass                           = TrackClass
		self.quickthumbnail:       QuickThumbnail = QuickThumbnail(tauon=self)
		self.gall_ren:                  GallClass = GallClass(tauon=self, size=self.album_mode_art_size)
		self.thumb_tracks:            ThumbTracks = ThumbTracks(tauon=self)
		self.chunker:                     Chunker = Chunker()
		self.stream_proxy:              StreamEnc = StreamEnc(self)
		self.level_train:       list[list[float]] = []
		self.radio_server: ThreadedHTTPServer | None = None
		self.listen_alongers:    dict[str, Timer] = {}
		self.encode_folder_name                   = encode_folder_name
		self.encode_track_name                    = encode_track_name
		self.lrclib_uploads:           list[dict] = []
		self.todo:               list[TrackClass] = []
		self.heart_colours:        ColourGenCache = ColourGenCache(0.7, 0.7)
		#self.power_tag_colours:    ColourGenCache = ColourGenCache(0.5, 0.8)

		self.tray_lock = threading.Lock()
		self.tray_releases = 0

		self.play_lock = None
		self.update_play_lock: Callable[[], None] | None = None
		self.sleep_lock = None
		self.shutdown_lock = None
		self.quick_close: bool = False
		self.pl_to_id = self.pctl.pl_to_id
		self.id_to_pl = self.pctl.id_to_pl

		self.copied_track: int | None = None
		self.aud:                        CDLL = ctypes.cdll.LoadLibrary(str(get_phazor_path(self.pctl)))
		self.stream_feeder = None  # set by player4; exposes network download stats
		logging.debug(f"Loaded Phazor path at: {get_phazor_path(self.pctl)}")
		self.player4_state:       PlayerState = PlayerState.STOPPED
		self.cachement:              Cachement = Cachement(self)
		self.milky:                      Milky = Milky(self)

		#self.recorded_songs = []

		self.chrome_mode: bool = False
		self.web_running: bool = False
		self.web_thread = None
		self.remote_limited: bool = True

		self.MenuItem = MenuItem

		self.chrome: Chrome | None = None
		self.chrome_menu: Menu | None = None

		self.tidal: Tidal       = Tidal(self)
		self.plex: PlexService  = PlexService(self)
		self.jellyfin: Jellyfin = Jellyfin(self)
		self.tau: TauService    = TauService(self)
		self.album_star_store: AlbumStarStore = AlbumStarStore(self)
		self.subsonic: SubsonicService = self.album_star_store.subsonic

		self.playlist_autoscan = False
		self.dropped_playlist = -1

		self.now_searching: Literal["off", "searching", "errored", "success"] = "off"

		self.requested_raise: bool = False
		self.requested_tray: bool = False
		self.requested_tray_destruct: bool = False
		self.sdl_tray: sdl3.LP_SDL_Tray | None = None
		self.sdl_tray_state: PlayingState = PlayingState.STOPPED
		self.sdl_tray_launched: bool = False
		self.sdl_tray_text: str = ""
		self._tray_quit_cb = None
		self._tray_open_cb = None
		self._tray_playpause_cb = None
		self._tray_next_cb = None
		self._tray_prev_cb = None

	def tray_quit_callback(self, userdata, entry) -> None:
		"""Called when the 'Quit' tray entry is clicked."""
		logging.info("Exit via tray")
		self.exit("Exit received from app indicator")

	def tray_open_callback(self, userdata, entry) -> None:
		"""Open Tauon main UI."""
		# Adjust to whatever your real function is
		self.request_raise()


	def tray_playpause_callback(self, userdata, entry) -> None:
		"""Toggle play/pause."""
		self.pctl.play_pause()


	def tray_next_callback(self, userdata, entry) -> None:
		"""Next track."""
		self.pctl.advance()


	def tray_prev_callback(self, userdata, entry) -> None:
		"""Previous track."""
		self.pctl.back()

	def load_sdl_icon(self, path: Path) -> sdl3.LP_SDL_Surface:
		"""Load an image file into an SDL_Surface suitable for a tray icon."""
		surf = sdl3.IMG_Load(str(path).encode("utf-8"))
		if not surf:
			raise RuntimeError(f"IMG_Load failed: {sdl3.SDL_GetError().decode()}")
		return surf


	def update_tray_icon(self, name: str) -> None:
		"""Name like \"tray-indicator-stop\""""
		surf = self.load_sdl_icon(Path(self.get_tray_icon(name)))
		sdl3.SDL_SetTrayIcon(self.sdl_tray, surf)


	def sdl_set_tray_tooltip(self, tooltip: str) -> None:
		#logging.debug(f"Setting tray tooltip to '{tooltip}'")
		sdl3.SDL_SetTrayTooltip(self.sdl_tray, tooltip.encode("utf-8"))

	# TODO(Martin): Get this working with native SDL scroll implementation when available
	#def sdl_tray_scroll(self, indicator: AppIndicator3.Indicator, steps: int, direction: int) -> None:
	#	if direction == Gdk.ScrollDirection.UP:
	#		self.tauon.pctl.player_volume += 4
	#		self.tauon.pctl.player_volume = min(self.tauon.pctl.player_volume, 100)
	#		self.tauon.pctl.set_volume()
	#	if direction == Gdk.ScrollDirection.DOWN:
	#		if self.tauon.pctl.player_volume > 4:
	#			self.tauon.pctl.player_volume -= 4
	#		else:
	#			self.tauon.pctl.player_volume = 0
	#		self.tauon.pctl.set_volume()
	#	self.tauon.gui.update += 1


	def show_tray(self) -> None:
		self.requested_tray = True

		# TODO(Martin): https://github.com/libsdl-org/SDL/pull/14582#issuecomment-3627318392
		#if not self.sdl_tray_launched:
		#	try:
		#		self.init_sdl_tray()
		#	except Exception:
		#		logging.exception("Failed to start tray")
		#		self.show_message(_("Failed to start tray"), mode="error")
		#else:
		#	self.indicator.set_status(1)


	def hide_tray(self) -> None:
		self.requested_tray_destruct = True
		# TODO(Martin): https://github.com/libsdl-org/SDL/pull/14582#issuecomment-3627318392
		#if self.sdl_tray_launched:
		#	self.indicator.set_status(0)


	def tray_icon_play(self) -> None:
		if self.sdl_tray_launched:
			self.update_tray_icon("tray-indicator-play")
			# TODO(Martin): https://github.com/libsdl-org/SDL/pull/14582#issuecomment-3627318392
			#self.indicator.set_icon_full(self.tauon.get_tray_icon("tray-indicator-play"), "playing")


	def tray_icon_pause(self) -> None:
		if self.sdl_tray_launched:
			self.update_tray_icon("tray-indicator-pause")
			# TODO(Martin): https://github.com/libsdl-org/SDL/pull/14582#issuecomment-3627318392
			#self.indicator.set_icon_full(self.tauon.get_tray_icon("tray-indicator-pause"), "paused")


	def tray_icon_stop(self) -> None:
		if self.sdl_tray_launched:
			self.update_tray_icon("tray-indicator-default")
			# TODO(Martin): https://github.com/libsdl-org/SDL/pull/14582#issuecomment-3627318392
			#self.indicator.set_icon_full(self.tauon.get_tray_icon("tray-indicator-default"), "default")


	def init_sdl_tray(self) -> None:
		icon_surface = self.load_sdl_icon(Path(self.get_tray_icon("tray-indicator-default")))
		# Create tray (no icon, just tooltip)
		self.sdl_tray = sdl3.SDL_CreateTray(icon_surface, b"Tauon Music Box")
		if not self.sdl_tray:
			logging.error(f"SDL_CreateTray failed: {sdl3.SDL_GetError().decode()}")
			return

		# Create menu
		menu = sdl3.SDL_CreateTrayMenu(self.sdl_tray)
		if not menu:
			raise RuntimeError(f"SDL_CreateTrayMenu failed: {sdl3.SDL_GetError().decode()}")

		# --- Open Tauon Music Box ---
		open_entry = sdl3.SDL_InsertTrayEntryAt(
			menu,
			-1,
			b"Open Tauon Music Box",
			sdl3.SDL_TRAYENTRY_BUTTON,
		)
		if not open_entry:
			raise RuntimeError(f"SDL_InsertTrayEntryAt(Open) failed: {sdl3.SDL_GetError().decode()}")

		# --- Separator ---
		sep1 = sdl3.SDL_InsertTrayEntryAt(
			menu,
			-1,
			None,  # NULL label => separator
			0,     # flags ignored for separators
		)
		if not sep1:
			raise RuntimeError(f"SDL_InsertTrayEntryAt(sep1) failed: {sdl3.SDL_GetError().decode()}")

		# --- Play/Pause ---
		playpause_entry = sdl3.SDL_InsertTrayEntryAt(
			menu,
			-1,
			b"Play/Pause",
			sdl3.SDL_TRAYENTRY_BUTTON,
		)
		if not playpause_entry:
			raise RuntimeError(f"SDL_InsertTrayEntryAt(Play/Pause) failed: {sdl3.SDL_GetError().decode()}")

		# --- Next Track ---
		next_entry = sdl3.SDL_InsertTrayEntryAt(
			menu,
			-1,
			b"Next Track",
			sdl3.SDL_TRAYENTRY_BUTTON,
		)
		if not next_entry:
			raise RuntimeError(f"SDL_InsertTrayEntryAt(Next) failed: {sdl3.SDL_GetError().decode()}")

		# --- Previous Track ---
		prev_entry = sdl3.SDL_InsertTrayEntryAt(
			menu,
			-1,
			b"Previous Track",
			sdl3.SDL_TRAYENTRY_BUTTON,
		)
		if not prev_entry:
			raise RuntimeError(f"SDL_InsertTrayEntryAt(Previous) failed: {sdl3.SDL_GetError().decode()}")

		# --- Separator ---
		sep2 = sdl3.SDL_InsertTrayEntryAt(
			menu,
			-1,
			None,  # separator
			0,
		)
		if not sep2:
			raise RuntimeError(f"SDL_InsertTrayEntryAt(sep2) failed: {sdl3.SDL_GetError().decode()}")

		# --- Quit ---
		quit_entry = sdl3.SDL_InsertTrayEntryAt(
			menu,
			-1,
			b"Quit",
			sdl3.SDL_TRAYENTRY_BUTTON,
		)
		if not quit_entry:
			raise RuntimeError(f"SDL_InsertTrayEntryAt(Quit) failed: {sdl3.SDL_GetError().decode()}")

		self._tray_open_cb =      sdl3.SDL_TrayCallback(self.tray_open_callback)
		self._tray_playpause_cb = sdl3.SDL_TrayCallback(self.tray_playpause_callback)
		self._tray_next_cb =      sdl3.SDL_TrayCallback(self.tray_next_callback)
		self._tray_quit_cb =      sdl3.SDL_TrayCallback(self.tray_quit_callback)
		self._tray_prev_cb =      sdl3.SDL_TrayCallback(self.tray_prev_callback)

		sdl3.SDL_SetTrayEntryCallback(open_entry, self._tray_open_cb, None)
		sdl3.SDL_SetTrayEntryCallback(playpause_entry, self._tray_playpause_cb, None)
		sdl3.SDL_SetTrayEntryCallback(next_entry, self._tray_next_cb, None)
		sdl3.SDL_SetTrayEntryCallback(quit_entry, self._tray_quit_cb, None)
		sdl3.SDL_SetTrayEntryCallback(prev_entry, self._tray_prev_cb, None)

		self.sdl_tray_launched = True
		self.gui.tray_active = True

	def destroy_sdl_tray(self) -> None:
		if self.sdl_tray is None:
			logging.warning("Attempted to destroy non-existent tray")
			return
		sdl3.SDL_DestroyTray(self.sdl_tray)
		self.sdl_tray = None
		self.sdl_tray_launched = False
		self.gui.tray_active = False

	def update_sdl_tray(self) -> None:
		#if self.tray_releases <= 0:
		#	self.tray_lock.acquire()
		#self.tray_releases -= 1

		if self.pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM):
			if self.sdl_tray_state not in (PlayingState.PLAYING, PlayingState.URL_STREAM):
				self.sdl_tray_state = self.pctl.playing_state
				self.tray_icon_play()
		elif self.pctl.playing_state == PlayingState.PAUSED:
			if self.sdl_tray_state != PlayingState.PAUSED:
				self.sdl_tray_state = PlayingState.PAUSED
				self.tray_icon_pause()
		elif self.sdl_tray_state != PlayingState.STOPPED:
			self.sdl_tray_state = PlayingState.STOPPED
			self.tray_icon_stop()

		text = ""
		if self.prefs.tray_show_title:
			tr = self.pctl.playing_object()
			if tr and tr.title and tr.artist:
				text = tr.artist + " - " + tr.title
			elif tr and tr.title:
				text = tr.title
			elif self.pctl.playing_state == PlayingState.URL_STREAM:
				# Stream metadata that couldn't be split into artist/title, else the station name
				if self.pctl.tag_meta:
					text = self.pctl.tag_meta
				elif self.radiobox.loaded_station:
					text = self.radiobox.loaded_station.title
			elif tr and tr.filename:
				text = tr.filename

			if self.pctl.playing_state == PlayingState.STOPPED:
				text = ""

		if self.sdl_tray_launched and text != self.sdl_tray_text:
			if text:
				self.sdl_set_tray_tooltip(text)
			else:
				self.sdl_set_tray_tooltip(self.t_title)
			self.sdl_tray_text = text

	def coll(self, r: list[int]) -> bool:
		return r[0] < self.inp.mouse_position[0] <= r[0] + r[2] and r[1] <= self.inp.mouse_position[1] <= r[1] + r[3]

	def draw_ab_repeat_markers(self, seek_x: float, seek_y: float, seek_w: float, seek_h: float) -> None:
		if self.pctl.playing_length <= 0 or seek_w <= 0:
			return

		marker_w = max(1, round(2 * self.gui.scale))
		marker_h = max(round(seek_h + (8 * self.gui.scale)), marker_w + 2)
		marker_y = round(seek_y - ((marker_h - seek_h) / 2))
		seek_start = round(seek_x)
		seek_end = round(seek_x + seek_w)
		if seek_end - seek_start <= marker_w:
			return

		def draw_marker(timestamp: float, colour: ColourRGBA) -> None:
			if timestamp < 0:
				return
			timestamp = min(timestamp, self.pctl.playing_length)
			marker_x = round(seek_x + seek_w * (timestamp / self.pctl.playing_length))
			marker_x = min(max(marker_x - marker_w // 2, seek_start), seek_end - marker_w)
			self.ddt.rect((marker_x, marker_y, marker_w, marker_h), colour)

		draw_marker(self.pctl.ab_repeat_a, ColourRGBA(0, 255, 0, 255))
		draw_marker(self.pctl.ab_repeat_b, ColourRGBA(0, 255, 255, 255))

	def scan_ffprobe(self, nt: TrackClass) -> None:
		startupinfo = None
		if self.windows:
			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		try:
			result = subprocess.run(
				[self.get_ffprobe(), "-v", "error", "-show_entries", "format=duration", "-of",
				"default=noprint_wrappers=1:nokey=1", nt.fullpath], stdout=subprocess.PIPE, startupinfo=startupinfo, check=True)
			nt.length = float(result.stdout.decode())
		except Exception:
			logging.exception("FFPROBE couldn't supply a duration")
		try:
			result = subprocess.run(
				[self.get_ffprobe(), "-v", "error", "-show_entries", "format_tags=title", "-of",
				"default=noprint_wrappers=1:nokey=1", nt.fullpath], stdout=subprocess.PIPE, startupinfo=startupinfo, check=True)
			nt.title = str(result.stdout.decode())
		except Exception:
			logging.exception("FFPROBE couldn't supply a title")
		try:
			result = subprocess.run(
				[self.get_ffprobe(), "-v", "error", "-show_entries", "format_tags=artist", "-of",
				"default=noprint_wrappers=1:nokey=1", nt.fullpath], stdout=subprocess.PIPE, startupinfo=startupinfo, check=True)
			nt.artist = str(result.stdout.decode())
		except Exception:
			logging.exception("FFPROBE couldn't supply a artist")
		try:
			result = subprocess.run(
				[self.get_ffprobe(), "-v", "error", "-show_entries", "format_tags=album", "-of",
				"default=noprint_wrappers=1:nokey=1", nt.fullpath], stdout=subprocess.PIPE, startupinfo=startupinfo, check=True)
			nt.album = str(result.stdout.decode())
		except Exception:
			logging.exception("FFPROBE couldn't supply a album")
		try:
			result = subprocess.run(
				[self.get_ffprobe(), "-v", "error", "-show_entries", "format_tags=date", "-of",
				"default=noprint_wrappers=1:nokey=1", nt.fullpath], stdout=subprocess.PIPE, startupinfo=startupinfo, check=True)
			nt.date = str(result.stdout.decode())
		except Exception:
			logging.exception("FFPROBE couldn't supply a date")
		try:
			result = subprocess.run(
				[self.get_ffprobe(), "-v", "error", "-show_entries", "format_tags=track", "-of",
				"default=noprint_wrappers=1:nokey=1", nt.fullpath], stdout=subprocess.PIPE, startupinfo=startupinfo, check=True)
			nt.track_number = str(result.stdout.decode())
		except Exception:
			logging.exception("FFPROBE couldn't supply a track")

	def hit_callback(self, win, point, data):
		gui          = self.gui
		inp          = self.inp
		windows         = self.windows
		prefs        = self.prefs
		macos        = self.macos
		logical_size = self.logical_size
		window_size  = self.window_size

		x = point.contents.x / logical_size[0] * window_size[0]
		y = point.contents.y / logical_size[0] * window_size[0]

		# Special layout modes
		if gui.mode == GuiMode.MINI:
			if inp.key_shift_down or inp.key_shiftr_down:
				return sdl3.SDL_HITTEST_NORMAL

			# if prefs.mini_mode_mode == MiniModeMode.SLATE:
			#     return sdl3.SDL_HITTEST_NORMAL

			if prefs.mini_mode_mode in (MiniModeMode.TAB, MiniModeMode.SLATE) and x > window_size[1] - 5 * gui.scale and y > window_size[1] - 12 * gui.scale:
				return sdl3.SDL_HITTEST_NORMAL

			if y < gui.window_control_hit_area_h and x > window_size[
				0] - gui.window_control_hit_area_w:
				return sdl3.SDL_HITTEST_NORMAL

			if prefs.mini_mode_mode == MiniModeMode.SIGNAL:
				if prefs.left_window_control:
					if x < gui.window_control_hit_area_w and y < gui.window_control_hit_area_h:
						return sdl3.SDL_HITTEST_NORMAL

				for field, _callback in self.fields.field_array:
					if coll_point((x, y), field):
						return sdl3.SDL_HITTEST_NORMAL

				frame = round(14 * gui.scale)
				box_y = round(14 * gui.scale)
				box_side = min(window_size[0] - frame * 2, window_size[1] - round(30 * gui.scale))
				box_rect = (frame, box_y, window_size[0] - frame * 2, box_side)
				graph_rect = (
					box_rect[0] + round(12 * gui.scale),
					box_rect[1] + round(28 * gui.scale),
					box_rect[2] - round(24 * gui.scale),
					box_rect[3] - round(54 * gui.scale),
				)
				baseline = graph_rect[1] + graph_rect[3] - round(16 * gui.scale)
				playlist = self.pctl.default_playlist
				if playlist:
					tracklist_focus = self.mini_mode_signal.focus_position
					if not self.mini_mode_signal.focus_ready:
						tracklist_focus = float(self.mini_mode_signal._current_playlist_position())
					current_index = self.mini_mode_signal._current_playlist_position()
					anchor_x = box_rect[0] + round(box_rect[2] * 0.32) + round(75 * gui.scale)
					anchor_y = box_rect[1] + round(box_rect[3] * 0.24)
					x_step = round(18 * gui.scale)
					y_step = round(16 * gui.scale)
					max_delta = 7
					start = max(0, int(math.floor(tracklist_focus)) - max_delta)
					end = min(len(playlist), int(math.ceil(tracklist_focus)) + max_delta + 1)
					for i in range(start, end):
						rel = i - tracklist_focus
						if abs(rel) > max_delta:
							continue
						tx = anchor_x + round(rel * x_step)
						ty = anchor_y + round(rel * y_step)
						if ty < graph_rect[1] - round(20 * gui.scale) or ty > baseline - round(4 * gui.scale):
							continue

						track_object = self.pctl.get_track(playlist[i])
						title = self.mini_mode_signal._track_title(track_object)
						font = 413 if i == current_index else 211
						tw = self.ddt.get_text_w(title, font)
						th = self.ddt.get_text_w(title, font, height=True)
						if tw is None:
							tw = round(120 * gui.scale)
						if th is None:
							th = round(14 * gui.scale)
						if tx > graph_rect[0] + graph_rect[2] or tx + round(tw) < graph_rect[0]:
							continue
						track_hit_rect = (
							round(tx) - round(4 * gui.scale),
							round(ty) - round(2 * gui.scale),
							round(tw) + round(8 * gui.scale),
							round(th) + round(4 * gui.scale),
						)
						track_drag_gap = round(6 * gui.scale)
						track_drag_clear_rect = (
							track_hit_rect[0] - track_drag_gap,
							track_hit_rect[1] - track_drag_gap,
							track_hit_rect[2] + track_drag_gap * 2,
							track_hit_rect[3] + track_drag_gap * 2,
						)
						if coll_point((x, y), track_drag_clear_rect):
							return sdl3.SDL_HITTEST_NORMAL

				art_size = round(127 * gui.scale)
				art_rect = (
					box_rect[0] + box_rect[2] - art_size - round(18 * gui.scale),
					box_rect[1] + round(34 * gui.scale),
					art_size,
					art_size,
				)
				if coll_point((x, y), art_rect):
					return sdl3.SDL_HITTEST_NORMAL

				return sdl3.SDL_HITTEST_DRAGGABLE

			# Square modes
			y1 = window_size[0]
			# if prefs.mini_mode_mode == MiniModeMode.SLATE:
			#     y1 = window_size[1]
			y0 = 0
			if macos:
				y0 = round(35 * gui.scale)
			if window_size[0] == window_size[1]:
				y1 = window_size[1] - 79 * gui.scale
			if y0 < y < y1 and not self.search_over.active:
				return sdl3.SDL_HITTEST_DRAGGABLE
			return sdl3.SDL_HITTEST_NORMAL

		# Standard player mode
		if not gui.maximized:
			if y < 0 and x > window_size[0]:
				return sdl3.SDL_HITTEST_RESIZE_TOPRIGHT

			if y < 0 and x < 1:
				return sdl3.SDL_HITTEST_RESIZE_TOPLEFT

			# if draw_border and y < 3 * gui.scale and x < window_size[0] - 40 * gui.scale and not gui.maximized:
			#     return sdl3.SDL_HITTEST_RESIZE_TOP

		if y < gui.panelY:
			if gui.top_bar_mode2:
				if y < gui.panelY - gui.panelY2:
					if prefs.left_window_control and x < 100 * gui.scale:
						return sdl3.SDL_HITTEST_NORMAL

					if x > window_size[0] - 100 * gui.scale and y < 30 * gui.scale:
						return sdl3.SDL_HITTEST_NORMAL
					return sdl3.SDL_HITTEST_DRAGGABLE
				if self.top_panel.drag_zone_start_x > x or self.tab_menu.active:
					return sdl3.SDL_HITTEST_NORMAL
				return sdl3.SDL_HITTEST_DRAGGABLE

			if self.top_panel.drag_zone_start_x < x < window_size[0] - (gui.offset_extra + 5):
				if self.tab_menu.active or inp.mouse_up or inp.mouse_down:  # mouse up/down is workaround for Wayland
					return sdl3.SDL_HITTEST_NORMAL

				if (prefs.left_window_control and x > window_size[0] - (100 * gui.scale) and (macos or windows)) \
				or (not prefs.left_window_control and x > window_size[0] - (160 * gui.scale) and (macos or windows)):
					return sdl3.SDL_HITTEST_NORMAL
				return sdl3.SDL_HITTEST_DRAGGABLE

		if not gui.maximized:
			if x > window_size[0] - 20 * gui.scale and y > window_size[1] - 20 * gui.scale:
				return sdl3.SDL_HITTEST_RESIZE_BOTTOMRIGHT
			if x < 5 and y > window_size[1] - 5:
				return sdl3.SDL_HITTEST_RESIZE_BOTTOMLEFT
			if y > window_size[1] - 5 * gui.scale:
				return sdl3.SDL_HITTEST_RESIZE_BOTTOM

			if x > window_size[0] - 3 * gui.scale and y > 20 * gui.scale:
				return sdl3.SDL_HITTEST_RESIZE_RIGHT
			if x < 5 * gui.scale and y > 10 * gui.scale:
				return sdl3.SDL_HITTEST_RESIZE_LEFT
			return sdl3.SDL_HITTEST_NORMAL
		return sdl3.SDL_HITTEST_NORMAL

	def draw_window_tools(self) -> None:
		gui         = self.gui
		inp         = self.inp
		colours     = self.colours
		window_size = self.window_size
		ddt         = self.ddt
		prefs       = self.prefs

		# rect = (window_size[0] - 55 * gui.scale, window_size[1] - 35 * gui.scale, 53 * gui.scale, 33 * gui.scale)
		# self.fields.add(rect)
		# prefs.left_window_control = not inp.key_shift_down
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
		left = prefs.left_window_control
		right = not left
		focused = window_is_focused(self.t_window)

		# Close
		if right:
			xx = window_size[0] - x_width
			xx -= round(2 * gui.scale)

		if macstyle:
			xx = window_size[0] - 27 * gui.scale
			if left:
				xx = round(4 * gui.scale)
			rect = (xx + 5, y - 1, 14 * gui.scale, 14 * gui.scale)
			self.fields.add(rect)
			colour = self.mac_close
			if not focused:
				colour = ColourRGBA(86, 85, 86, 255)
			elif self.coll(rect):
				colour = rgb_add_hls(colour, 0, 0.11, 0.05)
			self.gui.mac_circle.render(xx + 6 * gui.scale, y, colour)
			if self.coll(rect) and not gui.mouse_unknown and coll_point(inp.last_click_location, rect):
				self.do_exit_button()
		else:
			rect = (xx, y, x_width, h)
			last_width = x_width
			ddt.rect((rect[0], rect[1], rect[2], rect[3]), bg_off)
			self.fields.add(rect)
			if self.coll(rect) and not gui.mouse_unknown:
				ddt.rect((rect[0], rect[1], rect[2], rect[3]), bg_on)
				self.top_panel.exit_button.render(rect[0] + 8 * gui.scale, rect[1] + 8 * gui.scale, x_on)
				if coll_point(inp.last_click_location, rect):
					self.do_exit_button()
			else:
				self.top_panel.exit_button.render(rect[0] + 8 * gui.scale, rect[1] + 8 * gui.scale, x_off)

		# Macstyle restore
		if gui.mode == GuiMode.MINI and macstyle:
			if right:
				xx -= round(20 * gui.scale)
			if left:
				xx += round(20 * gui.scale)
			rect = (xx + 5, y - 1, 14 * gui.scale, 14 * gui.scale)

			self.fields.add(rect)
			colour = ColourRGBA(160, 55, 225, 255)
			if not focused:
				colour = ColourRGBA(86, 85, 86, 255)
			elif self.coll(rect):
				colour = rgb_add_hls(colour, 0, 0.1, 0.04)
			self.gui.mac_circle.render(xx + 6 * gui.scale, y, colour)
			if self.coll(rect) and not gui.mouse_unknown:
				if (inp.mouse_up or inp.ab_click) and coll_point(inp.last_click_location, rect):
					self.restore_full_mode()
					gui.request_frame()

		# maximize

		if self.draw_max_button and gui.mode != GuiMode.MINI:
			if macstyle:
				if right:
					xx -= round(20 * gui.scale)
				if left:
					xx += round(20 * gui.scale)
				rect = (xx + 5, y - 1, 14 * gui.scale, 14 * gui.scale)

				self.fields.add(rect)
				colour = self.mac_maximize
				if not focused:
					colour = ColourRGBA(86, 85, 86, 255)
				elif self.coll(rect):
					colour = rgb_add_hls(colour, 0, 0.11, 0.05)
				self.gui.mac_circle.render(xx + 6 * gui.scale, y, colour)
				if self.coll(rect) and not gui.mouse_unknown:
					if (inp.mouse_up or inp.ab_click) and coll_point(inp.last_click_location, rect):
						self.do_minimize_button()

			else:
				if right:
					xx -= ma_width
				if left:
					xx += last_width
				rect = (xx, y, ma_width, h)
				last_width = ma_width
				ddt.rect_a((rect[0], rect[1]), (rect[2], rect[3]), bg_off)
				self.fields.add(rect)
				if self.coll(rect):
					ddt.rect_a((rect[0], rect[1]), (rect[2], rect[3]), bg_on)
					self.top_panel.maximize_button.render(rect[0] + 10 * gui.scale, rect[1] + 10 * gui.scale, fg_on)
					if (inp.mouse_up or inp.ab_click) and coll_point(inp.last_click_location, rect):
						self.do_maximize_button()
				else:
					self.top_panel.maximize_button.render(rect[0] + 10 * gui.scale, rect[1] + 10 * gui.scale, fg_off)

		# minimize

		if self.draw_min_button:
			# x = window_size[0] - round(65 * gui.scale)
			# if draw_max_button and not gui.mode == GuiMode.MINI:
			#	 x -= round(34 * gui.scale)
			if macstyle:
				if right:
					xx -= round(20 * gui.scale)
				if left:
					xx += round(20 * gui.scale)
				rect = (xx + 5, y - 1, 14 * gui.scale, 14 * gui.scale)

				self.fields.add(rect)
				colour = self.mac_minimize
				if not focused:
					colour = ColourRGBA(86, 85, 86, 255)
				elif self.coll(rect):
					colour = rgb_add_hls(colour, 0, 0.1, 0.04)
				self.gui.mac_circle.render(xx + 6 * gui.scale, y, colour)
				if self.coll(rect) and not gui.mouse_unknown:
					if (inp.mouse_up or inp.ab_click) and coll_point(inp.last_click_location, rect):
						self.do_maximize_button()
			else:
				if right:
					xx -= mi_width
				if left:
					xx += last_width

				rect = (xx, y, mi_width, h)
				last_width = mi_width
				ddt.rect_a((rect[0], rect[1]), (rect[2], rect[3]), bg_off)
				self.fields.add(rect)
				if self.coll(rect):
					ddt.rect_a((rect[0], rect[1]), (rect[2], rect[3]), bg_on)
					ddt.rect_a((rect[0] + 11 * gui.scale, rect[1] + 16 * gui.scale), (14 * gui.scale, 3 * gui.scale), fg_on)
					if (inp.mouse_up or inp.ab_click) and coll_point(inp.last_click_location, rect):
						self.do_minimize_button()
				else:
					ddt.rect_a(
						(rect[0] + 11 * gui.scale, rect[1] + 16 * gui.scale), (14 * gui.scale, 3 * gui.scale), fg_off)

		# restore
		if gui.mode == GuiMode.MINI:
			# bg_off = [0, 0, 0, 50]
			# bg_on = [255, 255, 255, 10]
			# fg_off =(255, 255, 255, 40)
			# fg_on = (255, 255, 255, 60)
			if macstyle:
				pass
			else:
				if right:
					xx -= re_width
				if left:
					xx += last_width

				rect = (xx, y, re_width, h)
				ddt.rect_a((rect[0], rect[1]), (rect[2], rect[3]), bg_off)
				self.fields.add(rect)
				if self.coll(rect):
					ddt.rect_a((rect[0], rect[1]), (rect[2], rect[3]), bg_on)
					self.top_panel.restore_button.render(rect[0] + 8 * gui.scale, rect[1] + 9 * gui.scale, fg_on)
					if (inp.mouse_click or inp.ab_click) and coll_point(inp.click_location, rect):
						self.restore_full_mode()
						gui.request_frame()
				else:
					self.top_panel.restore_button.render(rect[0] + 8 * gui.scale, rect[1] + 9 * gui.scale, fg_off)

	def draw_window_border(self) -> None:
		ddt         = self.ddt
		colours     = self.colours
		gui         = self.gui
		corner_icon = self.gui.corner_icon
		window_size = self.window_size

		# The grip triangle would clash with a rounded corner, the resize
		# hit-zone below still works without it
		if not self.corner_round_radius():
			corner_icon.render(window_size[0] - corner_icon.w, window_size[1] - corner_icon.h, colours.corner_icon)

		corner_rect = (window_size[0] - 20 * gui.scale, window_size[1] - 20 * gui.scale, 20, 20)
		self.fields.add(corner_rect)

		right_rect = (window_size[0] - 3 * gui.scale, 20 * gui.scale, 10, window_size[1] - 40 * gui.scale)
		self.fields.add(right_rect)

		# top_rect = (20 * gui.scale, 0, window_size[0] - 40 * gui.scale, 2 * gui.scale)
		# self.fields.add(top_rect)

		left_rect = (0, 10 * gui.scale, 4 * gui.scale, window_size[1] - 50 * gui.scale)
		self.fields.add(left_rect)

		bottom_rect = (20 * gui.scale, window_size[1] - 4, window_size[0] - 40 * gui.scale, 7 * gui.scale)
		self.fields.add(bottom_rect)

		if self.coll(corner_rect):
			gui.cursor_want = 4
		elif self.coll(right_rect):
			gui.cursor_want = 8
		# elif self.coll(top_rect):
		#	 gui.cursor_want = 9
		elif self.coll(left_rect):
			gui.cursor_want = 10
		elif self.coll(bottom_rect):
			gui.cursor_want = 11

		colour = colours.window_frame

		# When corners are rounded, stop the straight edges short so the
		# corner arc textures can continue the contour
		inset = self.corner_round_radius()

		ddt.rect((inset, 0, window_size[0] - inset * 2, 1 * gui.scale), colour)
		ddt.rect((0, inset, 1 * gui.scale, window_size[1] - inset * 2), colour)
		ddt.rect((inset, window_size[1] - 1 * gui.scale, window_size[0] - inset * 2, 1 * gui.scale), colour)
		ddt.rect((window_size[0] - 1 * gui.scale, inset, 1 * gui.scale, window_size[1] - inset * 2), colour)

	def corner_round_radius(self) -> int:
		"""The window corner radius in pixels, 0 when rounding is inactive"""
		if not self.prefs.rounded_corners or not self.draw_border or self.corner_textures_failed:
			return 0
		gui = self.gui
		if gui.mode == GuiMode.MINI or gui.fullscreen or gui.maximized:
			return 0
		return max(2, round(self.prefs.corner_radius * gui.scale))

	def destroy_corner_textures(self) -> None:
		for textures in (self.corner_mask_textures, self.corner_border_textures):
			if textures:
				for texture in textures:
					sdl3.SDL_DestroyTexture(texture)
		self.corner_mask_textures = None
		self.corner_border_textures = None
		self.corner_texture_size = (0, 0)

	def _build_corner_textures(self, radius: int, thickness: int) -> bool:
		"""Generate anti-aliased corner cutout masks and border arcs for each window corner

		The mask textures erase the window corners by multiplying destination
		alpha, the border textures draw the window frame arc over the contour.
		"""
		self.destroy_corner_textures()

		# Draw supersampled then downsample for smooth anti-aliased edges
		ss = 8
		size = radius * ss

		cutout = Image.new("L", (size, size), 0)
		draw = ImageDraw.Draw(cutout)
		draw.ellipse((0, 0, size * 2, size * 2), fill=255)
		cutout = cutout.resize((radius, radius), Image.Resampling.LANCZOS)

		arc = Image.new("L", (size, size), 0)
		draw = ImageDraw.Draw(arc)
		draw.ellipse((0, 0, size * 2, size * 2), outline=255, width=thickness * ss)
		arc = arc.resize((radius, radius), Image.Resampling.LANCZOS)

		# dst = dst * srcA, keeps pixels inside the corner circle and erases outside
		mask_blend = sdl3.SDL_ComposeCustomBlendMode(
			sdl3.SDL_BLENDFACTOR_ZERO,
			sdl3.SDL_BLENDFACTOR_SRC_ALPHA,
			sdl3.SDL_BLENDOPERATION_ADD,
			sdl3.SDL_BLENDFACTOR_ZERO,
			sdl3.SDL_BLENDFACTOR_SRC_ALPHA,
			sdl3.SDL_BLENDOPERATION_ADD,
		)

		# Top-left, top-right, bottom-left, bottom-right
		transposes = (None, Image.Transpose.FLIP_LEFT_RIGHT, Image.Transpose.FLIP_TOP_BOTTOM, Image.Transpose.ROTATE_180)

		self.corner_mask_textures = []
		self.corner_border_textures = []
		for alpha_image, textures, blend in (
			(cutout, self.corner_mask_textures, mask_blend),
			(arc, self.corner_border_textures, sdl3.SDL_BLENDMODE_BLEND),
		):
			rgba = Image.new("RGBA", (radius, radius), (255, 255, 255, 0))
			rgba.putalpha(alpha_image)
			for transpose in transposes:
				corner = rgba if transpose is None else rgba.transpose(transpose)
				g = io.BytesIO()
				corner.save(g, "PNG")
				g.seek(0)
				surface = self.ddt.load_image(g)
				texture = sdl3.SDL_CreateTextureFromSurface(self.renderer, surface)
				sdl3.SDL_DestroySurface(surface)
				if not texture or not sdl3.SDL_SetTextureBlendMode(texture, blend):
					logging.warning(f"Failed to create corner texture: {sdl3.SDL_GetError()}")
					if texture:
						sdl3.SDL_DestroyTexture(texture)
					self.destroy_corner_textures()
					self.corner_textures_failed = True
					return False
				textures.append(texture)

		self.corner_texture_size = (radius, thickness)
		return True

	def render_rounded_corners(self) -> None:
		"""Cut out the window corners with anti-aliased alpha masks, then draw the frame arcs

		Called on the backbuffer just before present. Per-frame cost is eight
		small texture copies, the textures themselves are cached.
		"""
		radius = self.corner_round_radius()
		if not radius:
			return

		thickness = max(1, round(1 * self.gui.scale))
		if self.corner_mask_textures is None or self.corner_texture_size != (radius, thickness):
			if not self._build_corner_textures(radius, thickness):
				return

		w = self.window_size[0]
		h = self.window_size[1]
		positions = ((0, 0), (w - radius, 0), (0, h - radius), (w - radius, h - radius))
		rect = sdl3.SDL_FRect(0.0, 0.0, float(radius), float(radius))

		for texture, (x, y) in zip(self.corner_mask_textures, positions):
			rect.x = float(x)
			rect.y = float(y)
			sdl3.SDL_RenderTexture(self.renderer, texture, None, rect)

		frame = self.colours.window_frame
		for texture, (x, y) in zip(self.corner_border_textures, positions):
			sdl3.SDL_SetTextureColorMod(texture, frame.r, frame.g, frame.b)
			sdl3.SDL_SetTextureAlphaMod(texture, frame.a)
			rect.x = float(x)
			rect.y = float(y)
			sdl3.SDL_RenderTexture(self.renderer, texture, None, rect)

	def prime_fonts(self) -> None:
		standard_font = self.prefs.linux_font
		# if self.windows:
		#	 standard_font = self.prefs.linux_font + ", Sans"  # The CJK ones dont appear to be working
		self.ddt.prime_font(standard_font, 8, 9)
		self.ddt.prime_font(standard_font, 8, 10)
		self.ddt.prime_font(standard_font, 8.5, 11)
		self.ddt.prime_font(standard_font, 8.7, 11.5)
		self.ddt.prime_font(standard_font, 9, 12)
		self.ddt.prime_font(standard_font, 10, 13)
		self.ddt.prime_font(standard_font, 10, 14)
		self.ddt.prime_font(standard_font, 10.2, 14.5)
		self.ddt.prime_font(standard_font, 11, 15)
		self.ddt.prime_font(standard_font, 12, 16)
		self.ddt.prime_font(standard_font, 12, 17)
		self.ddt.prime_font(standard_font, 12, 18)
		self.ddt.prime_font(standard_font, 13, 19)
		self.ddt.prime_font(standard_font, 14, 20)
		self.ddt.prime_font(standard_font, 24, 30)

		self.ddt.prime_font(standard_font, 9, 412)
		self.ddt.prime_font(standard_font, 10, 413)

		standard_font = self.prefs.linux_font_semibold
		# if self.windows:
		#	 standard_font = self.prefs.linux_font_semibold + ", Noto Sans Med, Sans" #, Noto Sans CJK JP Medium, Noto Sans CJK Medium, Sans"

		self.ddt.prime_font(standard_font, 8, 309)
		self.ddt.prime_font(standard_font, 8, 310)
		self.ddt.prime_font(standard_font, 8.5, 311)
		self.ddt.prime_font(standard_font, 9, 312)
		self.ddt.prime_font(standard_font, 10, 313)
		self.ddt.prime_font(standard_font, 10.5, 314)
		self.ddt.prime_font(standard_font, 11, 315)
		self.ddt.prime_font(standard_font, 12, 316)
		self.ddt.prime_font(standard_font, 12, 317)
		self.ddt.prime_font(standard_font, 12, 318)
		self.ddt.prime_font(standard_font, 13, 319)
		self.ddt.prime_font(standard_font, 24, 330)

		standard_font = self.prefs.linux_font_bold
		# if self.windows:
		#	 standard_font = self.prefs.linux_font_bold + ", Noto Sans, Sans Bold"

		self.ddt.prime_font(standard_font, 6, 209)
		self.ddt.prime_font(standard_font, 7, 210)
		self.ddt.prime_font(standard_font, 8, 211)
		self.ddt.prime_font(standard_font, 9, 212)
		self.ddt.prime_font(standard_font, 10, 213)
		self.ddt.prime_font(standard_font, 11, 214)
		self.ddt.prime_font(standard_font, 12, 215)
		self.ddt.prime_font(standard_font, 13, 216)
		self.ddt.prime_font(standard_font, 14, 217)
		self.ddt.prime_font(standard_font, 17, 218)
		self.ddt.prime_font(standard_font, 19, 219)
		self.ddt.prime_font(standard_font, 20, 220)
		self.ddt.prime_font(standard_font, 25, 228)

		standard_font = self.prefs.linux_font_condensed
		# if self.windows:
		#	 standard_font = "Noto Sans ExtCond, Sans"
		self.ddt.prime_font(standard_font, 10, 413)
		self.ddt.prime_font(standard_font, 11, 414)
		self.ddt.prime_font(standard_font, 12, 415)
		self.ddt.prime_font(standard_font, 13, 416)

		standard_font = self.prefs.linux_font_condensed_bold  # "Noto Sans, ExtraCondensed Bold"
		# if self.windows:
		#	 standard_font = "Noto Sans ExtCond, Sans Bold"
		# self.ddt.prime_font(standard_font, 9, 512)
		self.ddt.prime_font(standard_font, 10, 513)
		self.ddt.prime_font(standard_font, 11, 514)
		self.ddt.prime_font(standard_font, 12, 515)
		self.ddt.prime_font(standard_font, 13, 516)

	def get_real_time(self) -> float:
		offset = self.pctl.decode_time - (self.prefs.sync_lyrics_time_offset / 1000)
		if self.prefs.backend == Backend.PHAZOR:
			offset -= (self.prefs.device_buffer - 120) / 1000
		elif self.prefs.backend == Backend.GSTREAMER:
			offset += 0.1
		return max(0, offset)

	def draw_internal_link(self, x: int, y: int, text: str, colour: ColourRGBA, font: int) -> bool:
		tweak = font
		while tweak > 100:
			tweak -= 100

		if self.gui.scale == 2:
			tweak *= 2
			tweak += 4
		if self.gui.scale == 1.25:
			tweak = round(tweak * 1.25)
			tweak += 1

		sp = self.ddt.text((x, y), text, colour, font)

		rect = [x - 5 * self.gui.scale, y - 2 * self.gui.scale, sp + 11 * self.gui.scale, 23 * self.gui.scale]
		self.fields.add(rect)

		if self.coll(rect):
			if not self.inp.mouse_click:
				self.gui.cursor_want = 3
			self.ddt.line(x, y + tweak + 2, x + sp, y + tweak + 2, alpha_mod(colour, 180))
			if self.inp.mouse_click:
				return True
		return False

	def pixel_to_logical(self, x: int) -> int:
		return round((x / self.window_size[0]) * self.logical_size[0])

	def img_slide_update_gall(self, value: int, pause: bool = True) -> None:
		self.gui.halt_image_rendering = True

		self.album_mode_art_size = value

		self.clear_img_cache(False)
		if pause:
			self.gallery_load_delay.set()
			self.gui.frame_callback_list.append(TestTimer(0.6))
		self.gui.halt_image_rendering = False

		# Update sizes
		self.gall_ren.size = self.album_mode_art_size

		if self.album_mode_art_size > 150:
			self.prefs.thin_gallery_borders = False

	def fix_encoding(self, index: int, mode: int, enc: str) -> None:
		todo: list[int] = []
		# TODO(Martin): What's the point of this? It was global before but is only used here
		enc_field = "All"

		if mode == 1:
			todo = [index]
		elif mode == 0:
			for b in range(len(self.pctl.default_playlist)):
				if self.pctl.master_library[self.pctl.default_playlist[b]].parent_folder_name == self.pctl.master_library[
					index].parent_folder_name:
					todo.append(self.pctl.default_playlist[b])

		for q in range(len(todo)):
			# key = self.pctl.master_library[todo[q]].title + self.pctl.master_library[todo[q]].filename
			old_star = self.star_store.full_get(todo[q])
			if old_star is not None:
				self.star_store.remove(todo[q])

			if enc_field in ("All", "Artist"):
				line = self.pctl.master_library[todo[q]].artist
				line = line.encode("Latin-1", "ignore")
				line = line.decode(enc, "ignore")
				self.pctl.master_library[todo[q]].artist = line

			if enc_field in ("All", "Album"):
				line = self.pctl.master_library[todo[q]].album
				line = line.encode("Latin-1", "ignore")
				line = line.decode(enc, "ignore")
				self.pctl.master_library[todo[q]].album = line

			if enc_field in ("All", "Title"):
				line = self.pctl.master_library[todo[q]].title
				line = line.encode("Latin-1", "ignore")
				line = line.decode(enc, "ignore")
				self.pctl.master_library[todo[q]].title = line

			if old_star is not None:
				self.star_store.insert(todo[q], old_star)

			# if key in self.pctl.star_library:
			#	 newkey = self.pctl.master_library[todo[q]].title + self.pctl.master_library[todo[q]].filename
			#	 if newkey not in self.pctl.star_library:
			#		 self.pctl.star_library[newkey] = copy.deepcopy(self.pctl.star_library[key])
			#		 # del self.pctl.star_library[key]

	def transfer_tracks(self, index: int, mode: int, to: int) -> None:
		todo: list[int] = []

		if mode == 0:
			todo = [index]
		elif mode == 1:
			for b in range(len(self.pctl.default_playlist)):
				if self.pctl.master_library[self.pctl.default_playlist[b]].parent_folder_name == self.pctl.master_library[
					index].parent_folder_name:
					todo.append(self.pctl.default_playlist[b])
		elif mode == 2:
			todo = self.pctl.default_playlist

		self.pctl.multi_playlist[to].playlist_ids += todo

	def add_stations(self, stations: list[RadioStation], name: str) -> None:
		if len(stations) == 1:
			for i, playlist in enumerate(self.pctl.radio_playlists):
				if playlist.name == "Default":
					playlist.stations.insert(0, stations[0])
					playlist.scroll = 0
					self.pctl.radio_playlist_viewing = i
					break
			else:
				self.pctl.radio_playlists.append(RadioPlaylist(uid=uid_gen(), name="Default", stations=stations, scroll=0))
				self.pctl.radio_playlist_viewing = len(self.pctl.radio_playlists) - 1
		else:
			self.pctl.radio_playlists.append(RadioPlaylist(uid=uid_gen(), name=name, stations=stations, scroll=0))
			self.pctl.radio_playlist_viewing = len(self.pctl.radio_playlists) - 1
		if not self.gui.radio_view:
			self.enter_radio_view()

	def parse_m3u(self, m3u_path: str) -> tuple[list[int], list[RadioStation]]:
		"""Read specified .m3u[8] playlist file, return list of track IDs/stations"""
		playlist: list[int] = []
		stations: list[RadioStation] = []

		titles:        dict[str, TrackClass] = {}
		location_dict: dict[str, TrackClass] = {}
		pl_dir = Path(m3u_path).parent
		path = Path(m3u_path)
		try:
			with path.open(encoding="utf-8") as file:
				lines = file.readlines()
		except UnicodeDecodeError as e:
			self.show_message(_("Error importing M3U playlist"), _("Error trying to parse playlist as UTF-8:") + f" {e}", mode="warning")
			logging.error(f"Error trying to parse playlist as UTF-8: {e}")
			return [], []
		except Exception as e:
			self.show_message(_("Exception importing M3U playlist"), _("Unknown exception trying to parse playlist") + f" {e}", mode="warning")
			logging.exception("Unknown exception trying to parse playlist")
			return [], []

		# parse data lines - either song files or radio links
		found_imported = 0
		found_file = 0
		found_title = 0
		not_found = 0
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
					radio: RadioStation = RadioStation(
						stream_url=line,
						title=line_title or os.path.splitext(os.path.basename(path))[0].strip())
					stations.append(radio)

					if self.gui.auto_play_import:
						self.gui.auto_play_import = False
						self.radiobox.start(radio)
				else:
					line = uri_parse(line)
					# Fix up relative filepaths
					if not Path(line).is_absolute():
						line = Path(pl_dir / Path(line) ).resolve()
					else:
						line = Path(line).resolve()
					line = str(line)

					# Cache database file paths for quick lookup
					if not location_dict:
						for key, value in self.pctl.master_library.items():
							if value.fullpath:
								location_dict[value.fullpath] = value
							if value.title:
								titles[value.artist + " - " + value.title] = value

					# Is file path already imported?
					# logging.info(line)
					if line in location_dict:
						playlist.append(location_dict[line].index)
						found_imported += 1
					# Or... does the file exist? Then import it
					elif os.path.isfile(line):
						nt = TrackClass()
						nt.index = self.pctl.master_count
						set_path(nt, line)
						nt = self.tag_scan(nt)
						self.pctl.master_library[self.pctl.master_count] = nt
						playlist.append(self.pctl.master_count)
						self.pctl.master_count += 1
						found_file += 1
					# Last resort, guess based on title
					elif line_title in titles:
						playlist.append(titles[line_title].index)
						found_title += 1
					else:
						log_line = line_title or line
						logging.info(f"track \"{log_line}\" not found")
						not_found += 1
		logging.info(f"playlist imported with {found_imported} tracks already in library, {found_file} found from filepath, {found_title} from title and {not_found} not found")
		return playlist, stations

	def load_m3u(self, m3u_path: str) -> None:
		"""Import an m3u file and create a new Tauon playlist for it"""
		path = Path(m3u_path)
		name = path.stem
		if not path.is_file():
			return

		playlist, stations = self.parse_m3u(path)

		# & then add it to the list
		if playlist:
			filesize = path.stat().st_size
			final_playlist = self.pl_gen(title=name, playlist_ids=playlist, playlist_file=str(path), file_size=filesize, export_type="m3u", auto_import=True)
			logging.info(f"Imported m3u file as {final_playlist.title}")
			self.pctl.multi_playlist.append(
				final_playlist)
		if stations:
			self.add_stations(stations, name)
		if not playlist and not stations:
			return

		self.gui.request_frame()

	def read_pls(self, lines: list[str], path: str, followed: bool = False) -> None:
		ids:         list[str] = []
		urls:   dict[str, str] = {}
		titles: dict[str, str] = {}

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

		stations: list[RadioStation] = []
		for id in ids:
			if id in urls:
				radio = RadioStation(
					stream_url=urls[id],
					title=titles[id] if id in titles else os.path.splitext(os.path.basename(path))[0],
					#scroll=0, # TODO(Martin): This was here wrong as scrolling is meant to be for RadioPlaylist?
					)

				if ".pls" in radio.stream_url:
					if not followed:
						try:
							logging.info("Download .pls")
							response = requests.get(radio.stream_url, stream=True, timeout=15)
							if int(response.headers["Content-Length"]) < 2000:
								self.read_pls(response.content.decode().splitlines(), path, followed=True)
						except Exception:
							logging.exception("Failed to retrieve .pls")
				else:
					stations.append(radio)
					if self.gui.auto_play_import:
						self.gui.auto_play_import = False
						self.radiobox.start(radio)
		if stations:
			self.add_stations(stations, os.path.basename(path))

	def load_pls(self, path: str) -> None:
		if os.path.isfile(path):
			with open(path) as f:
				lines = f.readlines()
				self.read_pls(lines, path)

	def parse_xspf(self, path: str) -> tuple[list[int], list[RadioStation], str]:
		"""Read specified .xspf playlist file, return lists of track IDs & stations plus playlist name if stored"""
		try:
			parser = ET.XMLParser(encoding="utf-8")
			e = ET.parse(path, parser).getroot()

			a: list[dict[str, str | None]] = []
			b: dict[str, str | None] = {}
			info = ""
			name = ""
			pl_dir = Path(path).parent

			for top in e:

				if top.tag.endswith("info"):
					info = top.text
				if top.tag.endswith("title"):
					name = top.text
				if top.tag.endswith("trackList"):
					for track in top:
						if track.tag.endswith("track"):
							for field in track:
								# logging.info(field.tag)
								# logging.info(field.text)
								if "title" in field.tag and field.text:
									b["title"] = field.text
								if "location" in field.tag and field.text:
									loc = field.text
									loc = str(urllib.parse.unquote(loc))
									parsed_loc = urllib.parse.urlparse(loc)

									# Preserve remote stream URLs; only normalize filesystem paths.
									if parsed_loc.scheme and parsed_loc.scheme != "file":
										pass
									else:
										if parsed_loc.scheme == "file":
											try:
												loc = str(Path.from_uri(loc))
											except Exception:
												logging.exception("Unknown error getting Path from URI")

										if not Path(loc).is_absolute():
											loc = str(Path(pl_dir / Path(loc)).resolve())
										else:
											loc = str(Path(loc).resolve())

									b["location"] = loc
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
			self.show_message(_("Error importing XSPF playlist."), _("Sorry about that."), mode="warning")
			raise

		# Extract internet streams first
		stations: list[RadioStation] = []
		for i in reversed(range(len(a))):
			item = a[i]
			if item["location"].startswith("http"):
				radio = RadioStation(
					stream_url=item["location"],
					title=item["name"])
			#	radio.scroll = 0 # TODO(Martin): This was here wrong as scrolling is meant to be for RadioPlaylist?
				if item["info"].startswith("http"):
					radio.website_url = item["info"]

				stations.append(radio)

				if self.gui.auto_play_import:
					self.gui.auto_play_import = False
					self.radiobox.start(radio)

				del a[i]
		playlist: list[int] = []
		missing = 0

		if len(a) > 5000:
			self.gui.to_got = "xspfl"

		# Generate location dict
		location_dict: dict[str, int] = {}
		base_names:    dict[str, int] = {}
		r_base_names:  dict[int, str] = {}
		titles:        dict[str, int] = {}
		for key, value in self.pctl.master_library.items():
			if value.fullpath:
				location_dict[value.fullpath] = key
			if value.filename:
				base_names[value.filename] = 0
				r_base_names[key] = value.filename
			if value.title:
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
						va = self.pctl.master_library[index]
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
				for key, value in self.pctl.master_library.items():
					if value.artist == track["artist"] and value.title == track["title"] and os.path.isfile(value.fullpath):
						playlist.append(key)
						if not os.path.isfile(value.fullpath):
							missing += 1
						found = True
						break
				if found is True:
					continue

			if "location" in track or "title" in track:
				nt = TrackClass()
				nt.index = self.pctl.master_count
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
					nt = self.tag_scan(nt)

				self.pctl.master_library[self.pctl.master_count] = nt
				playlist.append(self.pctl.master_count)
				self.pctl.master_count += 1
				if nt.found:
					continue

			missing += 1
			logging.error("-- Failed to locate track")
			if "location" in track:
				logging.error(f"-- -- Expected path: {track['location']}")
			if "title" in track:
				logging.error(f"-- -- Title: {track['title']}")
			if "artist" in track:
				logging.error(f"-- -- Artist: {track['artist']}")
			if "album" in track:
				logging.error(f"-- -- Album: {track['album']}")

		if missing > 0:
			self.show_message(
				_("Failed to locate {N} out of {T} tracks.")
				.format(N=str(missing), T=str(len(a))))

		return playlist, stations, name


	def load_xspf(self, xspf_path: str) -> None:
		# self.log("Importing XSPF playlist: " + path, title=True)

		if not Path(xspf_path).is_file():
			return

		playlist, stations, name = self.parse_xspf(xspf_path)
		path = Path(xspf_path)
		if not name:
			name = path.stem

		#logging.info(playlist)
		if playlist:
			filesize = path.stat().st_size
			final_playlist = self.pl_gen(title=name, playlist_ids=playlist, playlist_file=str(path), file_size=filesize, export_type="xspf", auto_import=True)
			logging.info(f"Imported xspf file as {final_playlist.title}")
			self.pctl.multi_playlist.append(
				final_playlist)
		if stations:
			self.add_stations(stations, name)
		if not stations and not playlist:
			return
		self.gui.request_frame()


	def ex_tool_tip(self, x: int, y: float, text1_width: int, text: str, font: int) -> None:
		text2_width = self.ddt.get_text_w(text, font)
		if text2_width == text1_width:
			return

		y -= 10 * self.gui.scale

		w = self.ddt.get_text_w(text, 312) + 24 * self.gui.scale
		h = 24 * self.gui.scale

		x -= int(w / 2)

		border = 1 * self.gui.scale
		self.ddt.rect((x - border, y - border, w + border * 2, h + border * 2), self.colours.grey(60))
		self.ddt.rect((x, y, w, h), self.colours.menu_background)
		p = self.ddt.text((x + int(w / 2), y + 3 * self.gui.scale, 2), text, self.colours.menu_text, 312, bg=self.colours.menu_background)

	def menu_standard_or_grey(self, enabled: bool) -> Decorator:
		line_colour = self.colours.menu_text if enabled else self.colours.menu_text_disabled
		return Decorator(line_colour, self.colours.menu_background, None)

	def enable_artist_list(self) -> None:
		if self.prefs.left_panel_mode != "artist list":
			self.gui.last_left_panel_mode = self.prefs.left_panel_mode
		self.prefs.left_panel_mode = "artist list"
		self.gui.lsp = True
		self.gui.update_layout = True

	def enable_playlist_list(self) -> None:
		if self.prefs.left_panel_mode != "playlist":
			self.gui.last_left_panel_mode = self.prefs.left_panel_mode
		self.prefs.left_panel_mode = "playlist"
		self.gui.lsp = True
		self.gui.update_layout = True

	def enable_queue_panel(self) -> None:
		if self.prefs.left_panel_mode != "queue":
			self.gui.last_left_panel_mode = self.prefs.left_panel_mode
		self.prefs.left_panel_mode = "queue"
		self.gui.lsp = True
		self.gui.update_layout = True

	def enable_folder_list(self) -> None:
		if self.prefs.left_panel_mode != "folder view":
			self.gui.last_left_panel_mode = self.prefs.left_panel_mode
		self.prefs.left_panel_mode = "folder view"
		self.gui.lsp = True
		self.gui.update_layout = True

	def lsp_menu_test_queue(self) -> bool:
		if not self.gui.lsp:
			return False
		return self.prefs.left_panel_mode == "queue"

	def lsp_menu_test_playlist(self) -> bool:
		if not self.gui.lsp:
			return False
		return self.prefs.left_panel_mode == "playlist"

	def lsp_menu_test_tree(self) -> bool:
		if not self.gui.lsp:
			return False
		return self.prefs.left_panel_mode == "folder view"

	def lsp_menu_test_artist(self) -> bool:
		if not self.gui.lsp:
			return False
		return self.prefs.left_panel_mode == "artist list"

	def toggle_left_last(self) -> None:
		self.gui.lsp = True
		t = self.prefs.left_panel_mode
		if t != self.gui.last_left_panel_mode:
			self.prefs.left_panel_mode = self.gui.last_left_panel_mode
			self.gui.last_left_panel_mode = t

	def toggle_repeat(self) -> None:
		self.gui.request_frame()
		self.pctl.repeat_mode ^= True
		if self.pctl.mpris is not None:
			self.pctl.mpris.update_loop()

	def menu_repeat_off(self) -> None:
		self.pctl.repeat_mode = False
		self.pctl.album_repeat_mode = False
		if self.pctl.mpris is not None:
			self.pctl.mpris.update_loop()

	def menu_set_repeat(self) -> None:
		self.pctl.repeat_mode = True
		self.pctl.album_repeat_mode = False
		if self.pctl.mpris is not None:
			self.pctl.mpris.update_loop()

	def menu_album_repeat(self) -> None:
		self.pctl.repeat_mode = True
		self.pctl.album_repeat_mode = True
		if self.pctl.mpris is not None:
			self.pctl.mpris.update_loop()

	def menu_ab_repeat_deco(self) -> Decorator:
		text = _("A/B Repeat")
		if self.pctl.ab_repeat_a >= 0:
			text = _("Set B Marker")
		if self.pctl.ab_repeat_b >= 0:
			text = _("Clear A/B")
		return Decorator(self.colours.menu_text, self.colours.menu_background, text)

	def menu_ab_repeat(self) -> None:
		if self.pctl.playing_state == PlayingState.STOPPED or self.pctl.playing_length <= 0:
			return

		marker_time = min(max(self.pctl.playing_time, 0), self.pctl.playing_length)

		if self.pctl.ab_repeat_a < 0:
			self.pctl.ab_repeat_a = marker_time
			self.pctl.ab_repeat_b = -1.0
		elif self.pctl.ab_repeat_b < 0:
			if marker_time <= self.pctl.ab_repeat_a:
				marker_time = min(self.pctl.playing_length, self.pctl.ab_repeat_a + 0.1)
				if marker_time <= self.pctl.ab_repeat_a:
					return
			self.pctl.ab_repeat_b = marker_time
		else:
			self.pctl.clear_ab_repeat(update_gui=False)

		self.gui.request_frame()

	def toggle_random(self) -> None:
		self.gui.request_frame()
		self.pctl.random_mode ^= True
		if self.pctl.mpris is not None:
			self.pctl.mpris.update_shuffle()

	def toggle_random_on(self) -> None:
		self.pctl.random_mode = True
		if self.pctl.mpris is not None:
			self.pctl.mpris.update_shuffle()

	def toggle_random_off(self) -> None:
		self.pctl.random_mode = False
		if self.pctl.mpris is not None:
			self.pctl.mpris.update_shuffle()

	def menu_shuffle_off(self) -> None:
		self.pctl.random_mode = False
		self.pctl.album_shuffle_mode = False
		if self.pctl.mpris is not None:
			self.pctl.mpris.update_shuffle()

	def menu_set_random(self) -> None:
		self.pctl.random_mode = True
		self.pctl.album_shuffle_mode = False
		if self.pctl.mpris is not None:
			self.pctl.mpris.update_shuffle()

	def menu_album_random(self) -> None:
		self.pctl.random_mode = True
		self.pctl.album_shuffle_mode = True
		if self.pctl.mpris is not None:
			self.pctl.mpris.update_shuffle()

	def toggle_shuffle_layout(self, albums: bool = False) -> None:
		self.prefs.shuffle_lock ^= True
		if self.prefs.shuffle_lock:

			self.gui.shuffle_was_showcase = self.gui.showcase_mode
			self.gui.shuffle_was_random = self.pctl.random_mode
			self.gui.shuffle_was_repeat = self.pctl.repeat_mode

			if not self.gui.combo_mode:
				self.view_box.lyrics(hit=True)
			self.pctl.random_mode = True
			self.pctl.repeat_mode = False
			if albums:
				self.prefs.album_shuffle_lock_mode = True
			if self.pctl.playing_state == PlayingState.STOPPED and self.pctl.track_queue:
				self.pctl.advance()
		else:
			self.pctl.random_mode = self.gui.shuffle_was_random
			self.pctl.repeat_mode = self.gui.shuffle_was_repeat
			self.prefs.album_shuffle_lock_mode = False
			if not self.gui.shuffle_was_showcase:
				self.exit_combo()

	def toggle_shuffle_layout_albums(self) -> None:
		self.toggle_shuffle_layout(albums=True)

	def toggle_shuffle_layout_deco(self) -> Decorator:
		if not self.prefs.shuffle_lock:
			return Decorator(self.colours.menu_text, self.colours.menu_background, _("Shuffle Lockdown"))
		return Decorator(self.colours.menu_text, self.colours.menu_background, _("Exit Shuffle Lockdown"))

	def exit_shuffle_layout(self, _unused: int) -> bool:
		return self.prefs.shuffle_lock

	def bio_set_large(self) -> None:
		# if self.window_size[0] >= round(1000 * self.gui.scale):
		# self.gui.artist_panel_height = 320 * self.gui.scale
		self.prefs.bio_large = True
		if self.gui.artist_info_panel:
			self.artist_info_box.get_data(self.artist_info_box.artist_on)

	def bio_set_small(self) -> None:
		# self.gui.artist_panel_height = 200 * self.gui.scale
		self.prefs.bio_large = False
		self.update_layout_do()
		if self.gui.artist_info_panel:
			self.artist_info_box.get_data(self.artist_info_box.artist_on)

	def artist_info_panel_close(self) -> None:
		self.gui.artist_info_panel ^= True
		self.gui.update_layout = True

	def toggle_bio_size_deco(self) -> Decorator:
		line = _("Make Large Size")
		if self.prefs.bio_large:
			line = _("Make Compact Size")
		return Decorator(self.colours.menu_text, self.colours.menu_background, line)

	def toggle_bio_size(self) -> None:
		if self.prefs.bio_large:
			self.prefs.bio_large = False
			self.update_layout_do()
			# bio_set_small()
		else:
			self.prefs.bio_large = True
			self.update_layout_do()
			# bio_set_large()
		# self.gui.update_layout = True

	def flush_artist_bio(self, artist: str) -> None:
		if os.path.isfile(os.path.join(self.a_cache_directory, artist + "-lfm.txt")):
			os.remove(os.path.join(self.a_cache_directory, artist + "-lfm.txt"))
		self.artist_info_box.text = ""
		self.artist_info_box.artist_on = None

	def clear_artist_cache(self) -> None:
		if os.path.isdir(self.a_cache_directory):
			for filename in os.listdir(self.a_cache_directory):
				if filename.endswith(("-lfm.txt", "-lfm.png", "-lfm.jpg", "-lfm.webp", "-ftv-full.jpg", "-dcg.jpg")):
					os.remove(os.path.join(self.a_cache_directory, filename))
		artist_pictures_dir = self.user_directory / "artist-pictures"
		if artist_pictures_dir.is_dir():
			for ext in ("png", "jpg", "webp"):
				for f in artist_pictures_dir.glob(f"*.{ext}"):
					f.unlink()
		self.artist_info_box.text = ""
		self.artist_info_box.artist_on = None
		self.artist_info_box.lock = False
		self.artist_info_box.status = ""

	def test_artist_dl(self, _unused: int) -> bool:
		return not self.prefs.auto_dl_artist_data

	def show_in_playlist(self) -> None:
		if self.prefs.album_mode and self.window_size[0] < 750 * self.gui.scale:
			self.toggle_album_mode()

		self.pctl.playlist_view_position = self.pctl.selected_in_playlist
		logging.debug("Position changed by show in playlist")
		self.gui.shift_selection.clear()
		self.gui.shift_selection.append(self.pctl.selected_in_playlist)
		self.pctl.render_playlist()

	def open_folder_stem(self, path: str) -> None:
		if self.windows:
			line = r'explorer /select,"{}"'.format(path.replace("/", "\\"))
			subprocess.Popen(line)
		else:
			line = path
			line += "/"
			if self.macos:
				subprocess.Popen(["open", line])
			else:
				subprocess.Popen(["xdg-open", line])

	def open_folder_disable_test(self, index: int) -> bool:
		track = self.pctl.master_library[index]
		return track.is_network and not os.path.isdir(track.parent_folder_path)

	def menu_open_folder_disable_test(self, ref: MenuTrackRef) -> bool:
		return self.open_folder_disable_test(ref.track_id)

	def open_folder(self, index: int) -> None:
		track = self.pctl.master_library[index]
		if self.open_folder_disable_test(index):
			self.show_message(_("Can't open folder of a network track."))
			return

		if self.windows:
			line = r'explorer /select,"{}"'.format(track.fullpath.replace("/", "\\"))
			subprocess.Popen(line)
		else:
			line = track.parent_folder_path
			line += "/"
			if self.macos:
				line = track.fullpath
				subprocess.Popen(["open", "-R", line])
			else:
				subprocess.Popen(["xdg-open", line])

	def menu_open_folder(self, ref: MenuTrackRef) -> None:
		self.open_folder(ref.track_id)

	def tag_to_new_playlist(self, tag_item) -> None:
		logging.critical(type(tag_item))
		self.path_stem_to_playlist(tag_item.path, tag_item.name)

	def folder_to_new_playlist_by_track_id(self, track_ref: MenuTrackRef) -> None:
		track = self.pctl.get_track(track_ref.track_id)
		self.path_stem_to_playlist(track.parent_folder_path, track.parent_folder_name)

	def stem_to_new_playlist(self, path: str) -> None:
		self.path_stem_to_playlist(path, os.path.basename(path))

	def move_playing_folder_to_tree_stem(self, path: str) -> None:
		self.move_playing_folder_to_stem(path, pl_id=self.tree_view_box.get_pl_id())

	def move_playing_folder_to_stem(self, path: str, pl_id: int | None = None) -> None:
		if not pl_id:
			pl_id = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].uuid_int

		track = self.pctl.playing_object()

		if not track or self.pctl.playing_state == PlayingState.STOPPED:
			self.show_message(_("No item is currently playing"))
			return

		move_folder = track.parent_folder_path

		# Stop playing track if its in the current folder
		if self.pctl.playing_state != PlayingState.STOPPED and move_folder in self.pctl.playing_object().parent_folder_path:
			self.pctl.stop(True)

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
			self.show_message(_("This track is a networked track."), mode="error")
			return

		if not os.path.isdir(move_folder):
			self.show_message(_("The source folder does not exist."), mode="error")
			return

		if not os.path.isdir(target_base):
			self.show_message(_("The destination folder does not exist."), mode="error")
			return

		if os.path.normpath(target_base) == os.path.normpath(move_folder):
			self.show_message(_("The destination and source folders are the same."), mode="error")
			return

		if len(target_base) < 4:
			self.show_message(_("Safety interrupt! The source path seems oddly short."), target_base, mode="error")
			return

		protect = ("", "Documents", "Music", "Desktop", "Downloads")
		for fo in protect:
			if move_folder.strip("\\/") == os.path.join(os.path.expanduser("~"), fo).strip("\\/"):
				self.show_message(
					_("Better not do anything to that folder!"), os.path.join(os.path.expanduser("~"), fo),
					mode="warning")
				return

		if directory_size(move_folder) > 3000000000:
			self.show_message(_("Folder size safety limit reached! (3GB)"), move_folder, mode="warning")
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
		for pl in self.pctl.multi_playlist:
			for i in reversed(range(len(pl.playlist_ids))):
				if self.pctl.get_track(pl.playlist_ids[i]).parent_folder_path == track.parent_folder_path:
					del pl.playlist_ids[i]

		# Find insert location
		pl = self.pctl.multi_playlist[self.pctl.id_to_pl(pl_id)].playlist_ids

		#matches = []
		insert = 0

		for i, item in enumerate(pl):
			if self.pctl.get_track(item).fullpath.startswith(target_base):
				insert = i

		for i, item in enumerate(pl):
			if self.pctl.get_track(item).fullpath.startswith(artist_folder):
				insert = i

		logging.info(f"The folder to be moved is: {move_folder}")
		load_order = LoadClass()
		load_order.target = os.path.join(artist_folder, track.parent_folder_name)
		load_order.playlist = pl_id
		load_order.playlist_position = insert

		logging.info(artist_folder)
		logging.info(os.path.join(artist_folder, track.parent_folder_name))
		self.move_jobs.append(
			(move_folder, os.path.join(artist_folder, track.parent_folder_name), True,
			track.parent_folder_name, load_order))
		self.thread_manager.ready("worker")

	def move_playing_folder_to_tag(self, tag_item) -> None:
		self.move_playing_folder_to_stem(tag_item.path)

	def re_import4(self, track_ref: MenuTrackRef) -> None:
		load_order = LoadClass()
		load_order.playlist_position = track_ref.position
		load_order.replace_stem = True
		load_order.target = self.pctl.get_track(track_ref.track_id).parent_folder_path
		load_order.notify = True
		load_order.playlist = track_ref.playlist_id
		self.load_orders.append(copy.deepcopy(load_order))
		self.show_message(_("Rescanning folder..."), self.pctl.get_track(track_ref.track_id).parent_folder_path, mode="info")

	def re_import3(self, stem) -> None:
		p = None
		for i, id in enumerate(self.pctl.default_playlist):
			if self.pctl.get_track(id).fullpath.startswith(stem + "/"):
				p = i
				break

		load_order = LoadClass()

		if p is not None:
			load_order.playlist_position = p

		load_order.replace_stem = True
		load_order.target = stem
		load_order.notify = True
		load_order.playlist = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].uuid_int
		self.load_orders.append(copy.deepcopy(load_order))
		self.show_message(_("Rescanning folder..."), stem, mode="info")

	def collapse_tree_deco(self) -> Decorator:
		pl_id = self.tree_view_box.get_pl_id()

		if self.tree_view_box.opens.get(pl_id):
			return Decorator(self.colours.menu_text, self.colours.menu_background, None)
		return Decorator(self.colours.menu_text_disabled, self.colours.menu_background, None)

	def collapse_tree(self) -> None:
		self.tree_view_box.collapse_all()

	def lock_folder_tree(self) -> None:
		if self.tree_view_box.lock_pl:
			self.tree_view_box.lock_pl = None
		else:
			self.tree_view_box.lock_pl = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].uuid_int

	def lock_folder_tree_deco(self) -> Decorator:
		if self.tree_view_box.lock_pl:
			return Decorator(self.colours.menu_text, self.colours.menu_background, _("Unlock Panel"))
		return Decorator(self.colours.menu_text, self.colours.menu_background, _("Lock Panel"))

	def finish_current(self) -> None:
		playing_object = self.pctl.playing_object()
		if playing_object is None:
			self.show_message("")
			return

		if not self.pctl.force_queue:
			self.pctl.force_queue.insert(
				0, queue_item_gen(
					playing_object.index,
					self.pctl.playlist_playing_position,
					self.pctl.pl_to_id(self.pctl.active_playlist_playing), QueueType.ALBUM, 1))

	def add_album_to_queue(self, track_id: int, position: int, playlist_id: int) -> None:
		partway = 0
		playing_object = self.pctl.playing_object()
		if not self.pctl.force_queue and playing_object is not None:
			if self.pctl.get_track(track_id).parent_folder_path == playing_object.parent_folder_path:
				partway = 1

		queue_object = queue_item_gen(track_id, position, playlist_id, QueueType.ALBUM, partway)
		self.pctl.force_queue.append(queue_object)
		self.queue_timer_set(queue_object=queue_object)
		if self.prefs.stop_end_queue:
			self.pctl.stop_mode = StopMode.OFF

	def menu_add_album_to_queue(self, ref: MenuTrackRef) -> None:
		self.add_album_to_queue(ref.track_id, ref.position, ref.playlist_id)

	def add_album_to_queue_fc(self, ref: MenuTrackRef) -> None:
		playing_object = self.pctl.playing_object()
		if playing_object is None:
			self.show_message("")
			return

		queue_item = None

		if not self.pctl.force_queue:
			queue_item = queue_item_gen(
				playing_object.index, self.pctl.playlist_playing_position, self.pctl.pl_to_id(self.pctl.active_playlist_playing), QueueType.ALBUM, 1)
			self.pctl.force_queue.insert(0, queue_item)
			self.add_album_to_queue(ref.track_id, ref.position, ref.playlist_id)
			return

		if self.pctl.force_queue[0].album_stage == 1:
			queue_item = queue_item_gen(ref.track_id, ref.position, ref.playlist_id, QueueType.ALBUM, 0)
			self.pctl.force_queue.insert(1, queue_item)
		else:
			p = self.pctl.get_track(ref.track_id).parent_folder_path
			p = ""
			if self.pctl.playing_ready():
				p = self.pctl.playing_object().parent_folder_path

			# TODO(Taiko): fixme for network tracks
			for i, item in enumerate(self.pctl.force_queue):
				if p != self.pctl.get_track(item.track_id).parent_folder_path:
					queue_item = queue_item_gen(
						ref.track_id,
						ref.position,
						ref.playlist_id, QueueType.ALBUM, 0)
					self.pctl.force_queue.insert(i, queue_item)
					break
			else:
				queue_item = queue_item_gen(
					ref.track_id, ref.position, ref.playlist_id, QueueType.ALBUM, 0)
				self.pctl.force_queue.insert(len(self.pctl.force_queue), queue_item)
		if queue_item:
			self.queue_timer_set(queue_object=queue_item)
		if self.prefs.stop_end_queue:
			self.pctl.stop_mode = StopMode.OFF

	def cancel_import(self) -> None:
		if self.transcode_list:
			del self.transcode_list[1:]
			self.gui.tc_cancel = True
		if self.pctl.loading_in_progress:
			self.gui.im_cancel = True
		if self.gui.sync_progress:
			self.gui.stop_sync = True
			self.gui.sync_progress = _("Aborting Sync")

	def toggle_lyrics_show(self, _unused) -> bool:
		return not self.gui.combo_mode

	def toggle_side_art_deco(self) -> Decorator:
		colour = self.colours.menu_text
		line = _("Hide Metadata Panel") if self.prefs.show_side_lyrics_art_panel else _("Show Metadata Panel")

		if self.gui.combo_mode:
			colour = self.colours.menu_text_disabled
		return Decorator(colour, self.colours.menu_background, line)

	def toggle_lyrics_panel_position_deco(self) -> Decorator:
		colour = self.colours.menu_text
		line = _("Panel Below Lyrics") if self.prefs.lyric_metadata_panel_top else _("Panel Above Lyrics")

		if self.gui.combo_mode or not self.prefs.show_side_lyrics_art_panel:
			colour = self.colours.menu_text_disabled
		return Decorator(colour, self.colours.menu_background, line)

	def toggle_lyrics_panel_position(self) -> None:
		self.prefs.lyric_metadata_panel_top ^= True

	def lyrics_in_side_show(self, _track_object: TrackClass) -> bool:
		return not (self.gui.combo_mode or not self.prefs.show_lyrics_side)

	def toggle_side_art(self) -> None:
		self.prefs.show_side_lyrics_art_panel ^= True

	def toggle_milky_deco(self, _track_object: TrackClass) -> Decorator:
		text = _("Enable Milkdrop Visualiser")
		if self.prefs.milk:
			text = _("Disable Milkdrop Visualiser")
		return Decorator(self.colours.menu_text, self.colours.menu_background, text)

	def toggle_showcase_wide_art_deco(self, _track_object: TrackClass) -> Decorator:
		text = _("Disable Wide Mode") if self.prefs.showcase_wide_art else _("Enable Wide Mode")
		return Decorator(self.colours.menu_text, self.colours.menu_background, text)

	def toggle_showcase_wide_art(self, _track_object: TrackClass) -> None:
		self.prefs.showcase_wide_art ^= True
		self.gui.request_frame()

	def showcase_mode_show_test(self, _track_object: TrackClass) -> bool:
		return self.gui.showcase_mode

	def toggle_lyrics_check(self) -> bool:
		if self.gui.combo_mode:
			return self.prefs.show_lyrics_showcase
		return self.prefs.show_lyrics_side

	def toggle_lyrics_deco(self, track_object: TrackClass) -> Decorator:
		text = _("Show Lyrics")
		if not track_object or (track_object.lyrics == "" and not self.timed_lyrics_ren.generate(track_object)):
			text = _("Prefer Lyrics Display")
		return Decorator(self.colours.menu_text, self.colours.menu_background, text)

	def toggle_milky(self, _track_object: TrackClass) -> None:
		if not self.prefs.milk and not t_visuals.milky_ready:
			self.show_message(_("MilkDrop visualiser is not available"), t_visuals.milky_error, mode="error")
			return
		if not self.prefs.milk:
			self.milky.projectm.rescan_presets()
			if not self.milky.projectm.presets:
				def download_presets() -> None:
					self.preset_download_box.start(
						title=_("Downloading Milkdrop presets"),
						status=_("Starting download..."),
						cancel_detail=_("Milkdrop will still be enabled."),
					)
					def dl() -> None:
						url = "https://github.com/Taiko2k/Tauon/releases/download/Extras/creamingsodav1.zip"
						assert url
						target_directory = self.user_directory / "presets"
						target_directory.mkdir(parents=True, exist_ok=True)
						logging.info(
							"Preset download starting: url=%s user_directory=%s target_directory=%s dirs=%s",
							url,
							self.user_directory,
							target_directory,
							[str(path) for path in self.milky.projectm.dirs],
						)

						def count_installed_presets() -> int:
							try:
								return sum(1 for path in target_directory.rglob("*.milk") if path.is_file())
							except Exception:
								logging.exception("Failed to count installed Milkdrop presets in %s", target_directory)
								return -1

						def enable_milkdrop(status: str, detail: str = "", toast_text: str | None = None) -> None:
							count_before = len(self.milky.projectm.presets)
							self.prefs.milk = True
							try:
								self.milky.projectm.rescan_presets()
							except Exception:
								logging.exception("Preset rescan failed after download")
								if not detail:
									detail = _("Restart Tauon if presets are not visible yet.")
							logging.info(
								"Preset download enable complete: status=%s detail=%s prefs.milk=%s scanned_before=%s scanned_after=%s installed_count=%s",
								status,
								detail,
								self.prefs.milk,
								count_before,
								len(self.milky.projectm.presets),
								count_installed_presets(),
							)
							self.preset_download_box.complete(status=status, detail=detail, toast_text=toast_text)

						try:
							with io.BytesIO() as buffer:
								with requests.get(url, stream=True, timeout=1800) as response:
									response.raise_for_status()  # fail if download failed
									total_bytes = int(response.headers.get("Content-Length", 0))
									downloaded = 0
									last_logged_mb = -1
									logging.info(
										"Preset download response: status=%s content_length=%s final_url=%s",
										response.status_code,
										total_bytes,
										response.url,
									)

									for data in response.iter_content(chunk_size=65536):
										if self.preset_download_box.cancel_requested:
											logging.info("Preset download cancelled during download after %s bytes", downloaded)
											enable_milkdrop(
												status=_("Preset download cancelled"),
												detail=_("Milkdrop visualiser enabled."),
											)
											return
										if not data:
											continue

										buffer.write(data)
										downloaded += len(data)
										if total_bytes:
											progress = min(0.95, downloaded / total_bytes * 0.95)
											total_mb = total_bytes / 1000 / 1000
											detail = f"{downloaded / 1000 / 1000:.1f} / {total_mb:.1f} MB"
										else:
											progress = None
											detail = f"{downloaded / 1000 / 1000:.1f} MB"
										current_mb = int(downloaded / 1000 / 1000)
										if current_mb != last_logged_mb:
											last_logged_mb = current_mb
											logging.info(
												"Preset download progress: downloaded=%s total=%s detail=%s",
												downloaded,
												total_bytes,
												detail,
											)
										self.preset_download_box.update(progress, _("Downloading preset pack..."), detail)

								buffer.seek(0)
								self.preset_download_box.update(0.95, _("Extracting presets..."))
								logging.info("Preset download complete: bytes=%s target=%s", buffer.getbuffer().nbytes, target_directory)
								with zipfile.ZipFile(buffer) as z:
									members = z.infolist()
									total_members = len(members) or 1
									target_root = target_directory.resolve()
									extracted = 0
									skipped = 0
									logging.info("Preset package opened: members=%s target_root=%s", len(members), target_root)
									for index, member in enumerate(members):
										if self.preset_download_box.cancel_requested:
											logging.info("Preset download cancelled during extraction at index=%s extracted=%s skipped=%s", index, extracted, skipped)
											enable_milkdrop(
												status=_("Preset download cancelled"),
												detail=_("Milkdrop visualiser enabled."),
											)
											return

										member_path = (target_directory / member.filename).resolve()
										if target_root not in (member_path, *member_path.parents):
											raise ValueError(_("Preset package contains an unsafe path"))
										try:
											z.extract(member, target_directory)
											extracted += 1
										except FileNotFoundError:
											if self.windows and len(str(member_path)) >= 240:
												skipped += 1
												logging.warning(
													"Skipping preset package member with too-long Windows path: index=%s name=%r target_length=%s target=%s",
													index,
													member.filename,
													len(str(member_path)),
													member_path,
													exc_info=True,
												)
											else:
												logging.exception(
													"Preset package member extraction failed: index=%s name=%r target_length=%s target=%s",
													index,
													member.filename,
													len(str(member_path)),
													member_path,
												)
												raise
										progress = 0.95 + 0.05 * ((index + 1) / total_members)
										self.preset_download_box.update(progress, _("Extracting presets..."), member.filename)
									logging.info(
										"Preset extraction complete: extracted=%s skipped=%s installed_count=%s target=%s",
										extracted,
										skipped,
										count_installed_presets(),
										target_directory,
									)

							enable_milkdrop(
								status=_("Presets ready"),
								detail=_("Milkdrop visualiser enabled."),
								toast_text=_("Download completed"),
							)
						except Exception as e:
							logging.exception("Preset download failed")
							self.preset_download_box.fail(_("Download failed"), f"{type(e).__name__}: {e}")

					shooter(dl)
				def skip_presets() -> None:
					self.prefs.milk = True
				self.gui.message_box_confirm_callback = download_presets
				self.gui.message_box_no_callback = skip_presets
				self.gui.message_box_confirm_reference = []
				self.show_message(_(
					"No presets loaded. Download preset pack? (~5MB)"),
					mode="confirm")
				return

		self.prefs.milk ^= True

	def toggle_milky_settings(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.milk

		self.toggle_milky(self.pctl.playing_object())
		return None

	def toggle_milky_auto(self, _track_object: TrackClass) -> None:
		self.milky.projectm.auto_frames = 0
		self.milky.projectm.timer.set()
		self.prefs.auto_milk ^= True

	def toggle_milk_cut_out(self, _track_object: TrackClass) -> None:
		self.prefs.milk_cut_out ^= True
		self.gui.request_frame()

	def milk_preset_is_favorite(self) -> bool:
		preset = self.milky.projectm.loaded_preset
		return preset is not None and str(preset) in self.prefs.milk_favorite_presets

	def toggle_milk_preset_favorite(self, _track_object: TrackClass) -> None:
		preset = self.milky.projectm.loaded_preset
		if preset is None:
			return
		key = str(preset)
		if key in self.prefs.milk_favorite_presets:
			self.prefs.milk_favorite_presets.remove(key)
		else:
			self.prefs.milk_favorite_presets.append(key)

	def open_milk_preset_chooser(self, _track_object: TrackClass) -> None:
		self.milk_choose.activate()

	def open_preset_folder(self, _track_object: TrackClass) -> None:
		target = self.user_directory / "presets"
		if not target.exists():
			target.mkdir()
		self.open_file_browser_at(target)

	def open_file_browser_at(self, path) -> None:
		if self.windows:
			line = r'explorer /select,"{}"'.format(str(path).replace("/", "\\"))
			subprocess.Popen(line)
		else:
			line = str(path)
			if self.macos:
				subprocess.Popen(["open", "-R", line])
			else:
				line += "/"
				subprocess.Popen(["xdg-open", line])


	def toggle_lyrics(self, track_object: TrackClass) -> None:
		if not track_object:
			return

		if self.gui.combo_mode:
			self.prefs.show_lyrics_showcase ^= True
			if self.prefs.show_lyrics_showcase and track_object.lyrics == "" and self.timed_lyrics_ren.generate(track_object):
				self.prefs.prefer_synced_lyrics = True
			# if self.prefs.show_lyrics_showcase and track_object.lyrics == "":
			#	 self.show_message("No lyrics for this track")
		else:
			# Handling for alt panel layout
			# if self.prefs.side_panel_layout == 1 and self.prefs.show_side_art:
			#	 #self.prefs.show_side_art = False
			#	 self.prefs.show_lyrics_side = True
			#	 return

			self.prefs.show_lyrics_side ^= True
			if self.prefs.show_lyrics_side and track_object.lyrics == "" and self.timed_lyrics_ren.generate(track_object):
				self.prefs.prefer_synced_lyrics = True
			# if self.prefs.show_lyrics_side and track_object.lyrics == "":
			#	 self.show_message("No lyrics for this track")

	def get_lyric_fire(self, track_object: TrackClass, silent: bool = False) -> str | None:

		def clear_search_cache(track: TrackClass) -> None:
			# clear cached search data (user can search by lyrics immediately)
			self.search_string_cache.pop(track.index, None)
			self.search_dia_string_cache.pop(track.index, None)
			self.search_field_cache.pop(track.index, None)
			self.search_dia_field_cache.pop(track.index, None)

		self.lyrics_ren.lyrics_position = 0

		if not self.prefs.lyrics_enables:
			if not silent:
				self.show_message(
					_("There are no lyric sources enabled."),
					_("See 'lyrics settings' under 'functions' tab in settings."), mode="info")
			self.now_searching = "errored"
			return None

		t = self.lyrics_fetch_timer.get()
		logging.info(f"Lyric rate limit timer is: {t!s} / -60")
		if t < -40:
			logging.info("Lets try again later")
			if not silent:
				self.show_message(_("Let's be polite and try later."))

				if t < -65:
					self.show_message(_("Stop requesting lyrics AAAAAA."), mode="error")

			# If the user keeps pressing, lets mess with them haha
			self.lyrics_fetch_timer.force_set(t - 5)
			self.now_searching = "errored"
			return "later"

		if t > 0:
			self.lyrics_fetch_timer.set()
			t = 0

		self.lyrics_fetch_timer.force_set(t - 10)

		if not silent:
			self.show_message(_("Searching..."))

		s_artist = track_object.artist
		s_title = track_object.title

		if s_artist in self.prefs.lyrics_subs:
			s_artist = self.prefs.lyrics_subs[s_artist]
		if s_title in self.prefs.lyrics_subs:
			s_title = self.prefs.lyrics_subs[s_title]

		logging.info(f"Searching for lyrics: {s_artist} - {s_title}")

		found = False
		for name in self.prefs.lyrics_enables:

			if name in lyric_sources:
				func = lyric_sources[name]

				try:
					lyrics, synced = func(s_artist, s_title, user_agent=self.t_agent)
					if lyrics or synced:
						if lyrics:
							logging.info(f"Found lyrics from {name}")
							track_object.lyrics = lyrics
							clear_search_cache(track_object)
							self.gui.lyrics_editor_update_now[0] = True
							if not self.gui.timed_lyrics_edit_view and self.prefs.save_lyrics_changes_to_files:
								self.write_lyrics(track_object)
						if synced:
							logging.info("Found synced lyrics")
							track_object.synced = synced
							clear_search_cache(track_object)
							self.gui.lyrics_editor_update_now[1] = True
							# TODO (Flynn): SYLT
							if not self.gui.timed_lyrics_edit_view:
								if self.prefs.save_synced_to_lrc:
									self.write_lyrics(track_object, True, synced_target="lrc")
								if self.prefs.save_lyrics_changes_to_files:
									self.write_lyrics(track_object, True, synced_target="tags")
						found = True
						break
				except Exception:
					logging.exception("Failed to find lyrics")

				if not found:
					logging.error(f"Could not find lyrics from source {name}")

		if not found:
			self.now_searching = "errored"
			if not silent:
				self.show_message(_("No lyrics for this track were found"))
		else:
			self.gui.message_box = False
			if not self.gui.showcase_mode:
				self.prefs.show_lyrics_side = True
			self.gui.request_frame()
			self.lyrics_ren.lyrics_position = 0
			self.timed_lyrics_ren.index = -1
			self.pctl.notify_database_changed()
			self.now_searching = "success"
		return None

	def get_lyric_wiki(self, track_object: TrackClass) -> None:
		if track_object.artist == "" or track_object.title == "":
			self.show_message(_("Insufficient metadata to get lyrics"), mode="warning")
			return

		self.now_searching = "searching"
		shoot_dl = threading.Thread(target=self.get_lyric_fire, args=([track_object]))
		shoot_dl.daemon = True
		shoot_dl.start()

		logging.info("..Done")

	def get_lyric_wiki_silent(self, track_object: TrackClass) -> None:
		logging.info("Searching for lyrics...")

		if track_object.artist == "" or track_object.title == "":
			return

		shoot_dl = threading.Thread(target=self.get_lyric_fire, args=([track_object, True]))
		shoot_dl.daemon = True
		shoot_dl.start()

		logging.info("..Done")

	def get_bio(self, track_object: TrackClass) -> None:
		if track_object.artist:
			self.lastfm.get_bio(track_object.artist)

	def search_lyrics_deco(self, track_object: TrackClass) -> Decorator:
		line_colour = self.colours.menu_text if not track_object.lyrics else self.colours.menu_text_disabled
		return Decorator(line_colour, self.colours.menu_background, None)

	def toggle_synced_lyrics(self, tr: TrackClass) -> None:
		self.prefs.prefer_synced_lyrics ^= True

	def toggle_synced_lyrics_deco(self, track: TrackClass) -> Decorator:
		text = None
		return Decorator(self.colours.menu_text, self.colours.menu_background, text)

	def paste_lyrics(self, track_object: TrackClass) -> None:
		if sdl3.SDL_HasClipboardText():
			clip = sdl3.SDL_GetClipboardText()
			#logging.info(clip)
			track_object.lyrics = clip.decode("utf-8")
			if self.prefs.save_lyrics_changes_to_files:
				self.write_lyrics(track_object)
			self.lyrics_ren_mini.to_reload = True
		else:
			logging.warning("NO TEXT TO PASTE")

	def copy_lyrics(self, track_object: TrackClass) -> None:
		copy_to_clipboard(track_object.lyrics)

	def clear_lyrics(self, track_object: TrackClass) -> None:
		track_object.lyrics = ""
		if self.prefs.save_lyrics_changes_to_files:
			self.write_lyrics(track_object)
		self.lyrics_ren_mini.to_reload = True

	def track_has_synced_lyrics(self, track_object: TrackClass) -> bool:
		return find_synced_lyric_data(track_object) is not None

	def clear_synced_lyrics_disable_test(self, track_object: TrackClass) -> bool:
		return not self.track_has_synced_lyrics(track_object)

	def clear_synced_lyrics(self, track_object: TrackClass) -> None:
		had_embedded_synced = find_synced_lyric_data(track_object, just_check=True)
		lrc_path: Path | None = None
		had_cached_synced = bool(track_object.synced)
		deleted_lrc = False
		cleared_tags = False
		kept_lrc = False

		if not track_object.is_network:
			direc = Path(track_object.parent_folder_path)
			name = Path(track_object.filename).stem
			if direc.is_dir():
				lrc_path = next(
					(
						f for f in direc.iterdir()
						if f.is_file()
						and f.stem == name
						and f.suffix.lower() == ".lrc"
					),
					None,
				)

		track_object.synced = ""

		if had_embedded_synced:
			track_object.lyrics = ""
			if self.prefs.save_lyrics_changes_to_files:
				self.write_lyrics(track_object)
				cleared_tags = True

		if lrc_path and lrc_path.is_file():
			if self.prefs.save_synced_to_lrc:
				try:
					lrc_path.unlink()
					deleted_lrc = True
				except Exception:
					logging.exception("Failed to delete synced lyrics file")
					self.show_message(
						_("Could not clear synced lyrics"),
						_("The .lrc file could not be deleted."),
						mode="error",
					)
					return
			else:
				kept_lrc = True

		self.lyrics_ren_mini.to_reload = True
		if deleted_lrc and cleared_tags:
			self.show_message(_("Cleared synced lyrics"), _("Removed from .lrc and tags"), mode="done")
		elif deleted_lrc:
			self.show_message(_("Cleared synced lyrics"), _("Removed from .lrc"), mode="done")
		elif cleared_tags:
			self.show_message(_("Cleared synced lyrics"), _("Removed from tags"), mode="done")
		elif kept_lrc:
			self.show_message(
				_("Cleared synced lyrics in Tauon only"),
				_("The .lrc file was kept because \"Save Synced to .lrc\" is off."),
				mode="done",
			)
		elif had_embedded_synced or had_cached_synced:
			self.show_message(_("Cleared synced lyrics in Tauon only"), mode="done")
		else:
			self.show_message(_("No synced lyrics were cleared"), mode="info")

	def split_lyrics(self, track_object: TrackClass) -> None:
		if track_object.lyrics:
			track_object.lyrics = track_object.lyrics.replace(". ", ". \n")
			if self.prefs.save_lyrics_changes_to_files:
				self.write_lyrics(track_object)
			self.lyrics_ren_mini.to_reload = True

	def paste_lyrics_deco(self) -> Decorator:
		line_colour = self.colours.menu_text if sdl3.SDL_HasClipboardText() else self.colours.menu_text_disabled
		return Decorator(line_colour, self.colours.menu_background, None)

	def chord_lyrics_paste_show_test(self, _unused) -> bool:
		return self.gui.combo_mode and self.prefs.guitar_chords

	def copy_lyrics_deco(self, track_object: TrackClass) -> Decorator:
		line_colour = self.colours.menu_text if track_object.lyrics else self.colours.menu_text_disabled
		return Decorator(line_colour, self.colours.menu_background, None)

	def clear_lyrics_deco(self, track_object: TrackClass) -> Decorator:
		line_colour = self.colours.menu_text if track_object.lyrics else self.colours.menu_text_disabled
		return Decorator(line_colour, self.colours.menu_background, None)

	def edit_lyrics_deco(self, _track_object: TrackClass) -> Decorator:
		line_colour = self.colours.menu_text# if track_object.lyrics else self.colours.menu_text_disabled
		return Decorator(line_colour, self.colours.menu_background, None)


	def write_lyrics(
		self,
		track: TrackClass,
		synced: bool = False,
		loud: bool = False,
		synced_target: Literal["auto", "lrc", "tags"] = "auto",
	) -> bool:
		lyrics = track.synced if synced else track.lyrics
		if track.is_network or not track.fullpath:
			logging.warning(f"Cannot write lyrics to network track {track.artist} - {track.title}")
			return False
		write_synced_to_lrc = synced and (
			synced_target == "lrc" or (synced_target == "auto" and self.prefs.save_synced_to_lrc)
		)
		if write_synced_to_lrc:
			with open( Path(track.fullpath).with_suffix(".lrc"), "w", encoding="utf-8") as lrc:
				lrc.write( lyrics )
				logging.info(f"Edited the LRC file for {track.artist} - {track.title}")
				return True
		try:
			if track.file_ext == "MP3":
				try:
					audio = mutagen.id3.ID3(track.fullpath)
				except mutagen.id3._util.ID3NoHeaderError:
					tags = mutagen.id3.ID3()
					tags.save(track.fullpath)
					audio = mutagen.id3.ID3(track.fullpath)
				try:
					audio.getall("USLT")[0].text = lyrics
					audio.getall("USLT")[0].encoding = 3
				except IndexError:
					audio.add( mutagen.id3.USLT( encoding=3,text=lyrics ) )
			elif track.file_ext == "FLAC":
				audio = mutagen.flac.FLAC(track.fullpath)
				audio["SYNCEDLYRICS" if synced else "UNSYNCEDLYRICS"] = lyrics
			elif track.file_ext == "OPUS":
				audio = mutagen.oggopus.OggOpus(track.fullpath)
				audio["SYNCEDLYRICS" if synced else "UNSYNCEDLYRICS"] = lyrics
			elif track.file_ext == "OGG":
				audio = mutagen.oggvorbis.OggVorbis(track.fullpath)
				audio["SYNCEDLYRICS" if synced else "UNSYNCEDLYRICS"] = lyrics
			elif track.file_ext in ("APE","WV","TTA"):
				audio = mutagen.apev2.APEv2(track.fullpath)
				audio["Lyrics"] = lyrics
			elif track.file_ext in ("MP4","M4A","M4B","M4P"):
				audio = mutagen.mp4.MP4(track.fullpath)
				audio["\xa9lyr"] = lyrics
			else:
				if loud:
					self.show_message(
						_("Could not write lyrics to file"),
						_("We don't know how to write lyrics to the filetype: ") + track.file_ext,
						_("(We still saved to the internal database)"),
						mode="error"
					)
				return False

			try:
				lyrics.encode('latin1')
				audio.save()
			except UnicodeEncodeError:
				audio.save(v1=0)
			logging.info(f"Edited lyrics in the file for {track.artist} - {track.title}")

		except Exception as e:
			logging.exception("Could not write lyrics to file")
			if loud:
				self.show_message(
					_("Could not write lyrics to file"),
					_("File doesn't exist or is not accessible"),
					_("(We still saved to the internal database)"),
					mode="error"
				)
			return False
		self.lyrics_ren_mini.to_reload = True
		return True
		# TODO: add more formats


	def show_sub_search(self, track_object: TrackClass) -> None:
		self.sub_lyrics_box.activate(track_object)

	def save_embed_img_disable_test(self, track_object: TrackClass) -> bool:
		return track_object.is_network

	def menu_save_embed_img_disable_test(self, ref: MenuTrackRef) -> bool:
		return self.save_embed_img_disable_test(self.pctl.get_track(ref.track_id))

	def save_embed_img(self, track_object: TrackClass) -> None:
		filepath = track_object.fullpath
		folder = track_object.parent_folder_path
		ext = track_object.file_ext

		if self.save_embed_img_disable_test(track_object):
			self.show_message(_("Saving network images not implemented"))
			return

		try:
			pic = self.album_art_gen.get_embed(track_object)

			if not pic:
				self.show_message(_("Image save error."), _("No embedded album art found in file."), mode="warning")
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

			self.open_folder(track_object.index)

		except Exception:
			logging.exception("Unknown error trying to save an image")
			self.show_message(_("Image save error."), _("A mysterious error occurred"), mode="error")

	def menu_save_embed_img(self, ref: MenuTrackRef) -> None:
		self.save_embed_img(self.pctl.get_track(ref.track_id))

	def open_image_deco(self, track_object: TrackClass)-> Decorator:
		info = self.album_art_gen.get_info(track_object)

		if info is None:
			return Decorator(self.colours.menu_text_disabled, self.colours.menu_background, None)

		line_colour = self.colours.menu_text
		return Decorator(line_colour, self.colours.menu_background, None)

	def menu_open_image_deco(self, ref: MenuTrackRef) -> Decorator:
		return self.open_image_deco(self.pctl.get_track(ref.track_id))

	def open_image_disable_test(self, track_object: TrackClass) -> bool:
		return track_object.is_network

	def menu_open_image_disable_test(self, ref: MenuTrackRef) -> bool:
		return self.open_image_disable_test(self.pctl.get_track(ref.track_id))

	def open_image(self, track_object: TrackClass) -> None:
		self.album_art_gen.open_external(track_object)

	def menu_open_image(self, ref: MenuTrackRef) -> None:
		self.open_image(self.pctl.get_track(ref.track_id))

	def extract_image_deco(self, track_object: TrackClass) -> Decorator:
		info = self.album_art_gen.get_info(track_object)

		if info is None:
			return Decorator(self.colours.menu_text_disabled, self.colours.menu_background, None)

		line_colour = self.colours.menu_text if info[0] == 1 else self.colours.menu_text_disabled
		return Decorator(line_colour, self.colours.menu_background, None)

	def menu_extract_image_deco(self, ref: MenuTrackRef) -> Decorator:
		return self.extract_image_deco(self.pctl.get_track(ref.track_id))

	def cycle_image_deco(self, track_object: TrackClass) -> Decorator:
		info = self.album_art_gen.get_info(track_object)

		if self.pctl.playing_state != PlayingState.STOPPED and (info is not None and info[1] > 1):
			line_colour = self.colours.menu_text
		else:
			line_colour = self.colours.menu_text_disabled

		return Decorator(line_colour, self.colours.menu_background, None)

	def cycle_image_gal_deco(self, ref: MenuTrackRef) -> Decorator:
		info = self.album_art_gen.get_info(self.pctl.get_track(ref.track_id))

		line_colour = self.colours.menu_text if info is not None and info[1] > 1 else self.colours.menu_text_disabled
		return Decorator(line_colour, self.colours.menu_background, None)

	def cycle_offset(self, track_object: TrackClass) -> None:
		self.album_art_gen.cycle_offset(track_object)

	def menu_cycle_offset(self, ref: MenuTrackRef) -> None:
		self.cycle_offset(self.pctl.get_track(ref.track_id))

	def cycle_offset_back(self, ref: MenuTrackRef) -> None:
		self.album_art_gen.cycle_offset_reverse(self.pctl.get_track(ref.track_id))

	def dl_art_deco(self, track_object: TrackClass) -> Decorator:
		if not track_object.album or not track_object.artist:
			return Decorator(self.colours.menu_text_disabled, self.colours.menu_background, None)
		return Decorator(self.colours.menu_text, self.colours.menu_background, None)

	def menu_dl_art_deco(self, ref: MenuTrackRef) -> Decorator:
		return self.dl_art_deco(self.pctl.get_track(ref.track_id))

	def download_art1(self, tr: TrackClass) -> None:
		if tr.is_network:
			self.show_message(_("Cannot download art for network tracks."))
			return

		# Determine noise of folder ----------------
		siblings: list[TrackClass] = []
		parent = tr.parent_folder_path

		for pl in self.pctl.multi_playlist:
			for ti in pl.playlist_ids:
				tr = self.pctl.get_track(ti)
				if tr.parent_folder_path == parent:
					siblings.append(tr)

		album_tags: list[str] | set[str] = []
		date_tags:  list[str] | set[str] = []

		for tr in siblings:
			album_tags.append(tr.album)
			date_tags.append(tr.date)

		album_tags = set(album_tags)
		date_tags = set(date_tags)

		if len(album_tags) > 2 or len(date_tags) > 2:
			self.show_message(_("It doesn't look like this folder belongs to a single album, sorry"))
			return

		# -------------------------------------------

		if not os.path.isdir(tr.parent_folder_path):
			self.show_message(_("Directory missing."))
			return

		try:
			self.show_message(_("Looking up MusicBrainz ID..."))

			if tr.musicbrainz_releasegroupid is None or tr.musicbrainz_artistids is None or not tr.musicbrainz_artistids:

				logging.info("MusicBrainz ID lookup...")

				artist = tr.album_artist
				if not tr.album:
					return
				if not artist:
					artist = tr.artist

				s = musicbrainzngs.search_release_groups(tr.album, artist=artist, limit=1)

				album_id = s["release-group-list"][0]["id"]
				artist_id = s["release-group-list"][0]["artist-credit"][0]["artist"]["id"]

				logging.info(f"Found release group ID: {album_id}")
				logging.info(f"Found artist ID: {artist_id}")
			else:
				album_id = tr.musicbrainz_releasegroupid
				artist_id = tr.musicbrainz_artistids[0]

				logging.info(f"Using tagged release group ID: {album_id}")
				logging.info(f"Using tagged artist ID: {artist_id}")

			if self.prefs.enable_fanart_cover:
				try:
					self.show_message(_("Searching fanart.tv for cover art..."))

					r = requests.get("https://webservice.fanart.tv/v3/music/albums/" \
						+ artist_id + "?api_key=" + self.prefs.fatvap, timeout=(4, 10))

					artlink = r.json()["albums"][album_id]["albumcover"][0]["url"]
					id = r.json()["albums"][album_id]["albumcover"][0]["id"]

					response = urllib.request.urlopen(artlink, context=self.tls_context)
					info = response.info()

					t = io.BytesIO()
					t.seek(0)
					t.write(response.read())
					t.seek(0, 2)
					buffer_size = t.tell()
					t.seek(0)

					if info.get_content_maintype() == "image" and buffer_size > 1000:
						if info.get_content_subtype() == "jpeg":
							filepath = os.path.join(tr.parent_folder_path, "cover-" + id + ".jpg")
						elif info.get_content_subtype() == "png":
							filepath = os.path.join(tr.parent_folder_path, "cover-" + id + ".png")
						else:
							self.show_message(_("Could not detect downloaded filetype."), mode="error")
							return

						with open(filepath, "wb") as f:
							f.write(t.read())

						self.show_message(_("Cover art downloaded from fanart.tv"), mode="done")
						# self.clear_img_cache()
						for track_id in self.pctl.default_playlist:
							if tr.parent_folder_path == self.pctl.get_track(track_id).parent_folder_path:
								self.clear_track_image_cache(self.pctl.get_track(track_id))
						return
				except Exception:
					logging.exception("Failed to get from fanart.tv")

			self.show_message(_("Searching MusicBrainz for cover art..."))
			t = io.BytesIO(musicbrainzngs.get_release_group_image_front(album_id, size=None))
			buffer_size = 0
			t.seek(0, 2)
			buffer_size = t.tell()
			t.seek(0)
			if buffer_size > 1000:
				filepath = os.path.join(tr.parent_folder_path, album_id + ".jpg")
				f = open(filepath, "wb")
				f.write(t.read())
				f.close()

				self.show_message(_("Cover art downloaded from MusicBrainz"), mode="done")
				# self.clear_img_cache()
				self.clear_track_image_cache(tr)

				for track_id in self.pctl.default_playlist:
					if tr.parent_folder_path == self.pctl.get_track(track_id).parent_folder_path:
						self.clear_track_image_cache(self.pctl.get_track(track_id))

				return

		except Exception:
			logging.exception("Matching cover art or ID could not be found.")
			self.show_message(_("Matching cover art or ID could not be found."))

	def download_art1_fire_disable_test(self, track_object: TrackClass) -> bool:
		return track_object.is_network

	def menu_download_art1_fire_disable_test(self, ref: MenuTrackRef) -> bool:
		return self.download_art1_fire_disable_test(self.pctl.get_track(ref.track_id))

	def download_art1_fire(self, track_object: TrackClass) -> None:
		shoot_dl = threading.Thread(target=self.download_art1, args=[track_object])
		shoot_dl.daemon = True
		shoot_dl.start()

	def menu_download_art1_fire(self, ref: MenuTrackRef) -> None:
		self.download_art1_fire(self.pctl.get_track(ref.track_id))

	def remove_embed_picture(self, track_object: TrackClass, dry: bool = True) -> int | None:
		"""Return amount of removed objects or None"""
		index = track_object.index

		if self.inp.key_shift_down or self.inp.key_shiftr_down:
			tracks = [index]
			if track_object.is_cue or track_object.is_network:
				self.show_message(_("Error - No handling for this kind of track"), mode="warning")
				return None
		else:
			tracks: list[int] = []
			original_parent_folder = track_object.parent_folder_name
			for k in self.pctl.default_playlist:
				tr = self.pctl.get_track(k)
				if original_parent_folder == tr.parent_folder_name:
					tracks.append(k)

		removed = 0
		if not dry:
			pr = self.pctl.stop(True)
		try:
			for item in tracks:
				tr =self. pctl.get_track(item)

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
						self.show_message(_("Removing vorbis image not implemented"))
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

					self.clear_track_image_cache(tr)

		except Exception:
			logging.exception("Image remove error")
			self.show_message(_("Image remove error"), mode="error")
			return None

		if dry:
			return removed

		if removed == 0:
			self.show_message(_("Image removal failed."), mode="error")
			return None
		if removed == 1:
			self.show_message(_("Deleted embedded picture from file"), mode="done")
		else:
			self.show_message(_("{N} files processed").local(N=removed), mode="done")
		if pr == 1:
			self.pctl.revert()
		return None

	def delete_file_image(self, track_object: TrackClass) -> None:
		try:
			showc = self.album_art_gen.get_info(track_object)
			if showc is not None and showc[0] == 0:
				source = self.album_art_gen.get_sources(track_object)[showc[2]][1]
				os.remove(source)
				# self.clear_img_cache()
				self.clear_track_image_cache(track_object)
				logging.info(f"Deleted file: {source}")
		except Exception:
			logging.exception("Failed to delete file")
			self.show_message(_("Something went wrong"), mode="error")

	def delete_track_image_deco(self, track_object: TrackClass) -> Decorator:
		info = self.album_art_gen.get_info(track_object)

		text = _("Delete Image File")
		line_colour = self.colours.menu_text

		if info is None or track_object.is_network:
			return Decorator(self.colours.menu_text_disabled, self.colours.menu_background, None)

		if info and info[0] == 0:
			text = _("Delete Image File")

		elif info and info[0] == 1:
			if self.pctl.playing_state != PlayingState.STOPPED and track_object.file_ext in ("MP3", "FLAC", "M4A"):
				line_colour = self.colours.menu_text
			else:
				line_colour = self.colours.menu_text_disabled

			text = _("Delete Embedded | Folder")
			if self.inp.key_shift_down or self.inp.key_shiftr_down:
				text = _("Delete Embedded | Track")
		return Decorator(line_colour, self.colours.menu_background, text)

	def menu_delete_track_image_deco(self, ref: MenuTrackRef) -> Decorator:
		return self.delete_track_image_deco(self.pctl.get_track(ref.track_id))

	def delete_track_image(self, track_object: TrackClass) -> None:
		if track_object.is_network:
			return
		info = self.album_art_gen.get_info(track_object)
		if info and info[0] == 0:
			self.delete_file_image(track_object)
		elif info and info[0] == 1:
			n = self.remove_embed_picture(track_object, dry=True)
			self.gui.message_box_confirm_callback = self.remove_embed_picture
			self.gui.message_box_no_callback = None
			self.gui.message_box_confirm_reference = (track_object, False)
			self.show_message(_("This will erase any embedded image in {N} files. Are you sure?").format(N=n), mode="confirm")

	def menu_delete_track_image(self, ref: MenuTrackRef) -> None:
		self.delete_track_image(self.pctl.get_track(ref.track_id))

	def search_image_deco(self, track_object: TrackClass) -> Decorator:
		if track_object.artist and track_object.album:
			line_colour = self.colours.menu_text
		else:
			line_colour = self.colours.menu_text_disabled
		return Decorator(line_colour, self.colours.menu_background, None)

	def append_here(self) -> None:
		self.pctl.default_playlist += self.pctl.cargo

	def paste_deco(self) -> Decorator:
		active = False
		line = None
		if len(self.pctl.cargo) > 0:
			active = True
		elif sdl3.SDL_HasClipboardText():
			text = copy_from_clipboard()
			if text.startswith("/") or "file://" in text:
				active = True

		line_colour = self.colours.menu_text if active else self.colours.menu_text_disabled
		return Decorator(line_colour, self.colours.menu_background, line)

	def lightning_move_test(self, _unused: int) -> bool:
		return self.gui.lightning_copy and self.prefs.show_transfer

	# def copy_deco(self) -> Decorator:
	#	 line = "Copy"
	#	 if self.inp.key_shift_down:
	#		 line = "Copy" #Folder From Library"
	#	 else:
	#		 line = "Copy"
	#	 return Decorator(self.colours.menu_text, self.colours.menu_background, line)

	def export_m3u(self, pl: int, pl_file: Path | None = None, relative: bool = False) -> int | Path:
		"""Exports an m3u file from a Playlist dictionary in multi_playlist to a playlist file denoted by pl_file.
		pl_file is normalized by run_export; you should not call this function directly if you are uncertain.
		"""
		if len(self.pctl.multi_playlist[pl].playlist_ids) < 1:
			self.show_message(_("There are no tracks in this playlist. Nothing to export"))
			return 1
		if relative:
			for num in set( self.pctl.multi_playlist[pl].playlist_ids ):
				track = self.pctl.master_library[num]
				if not track.is_network:
					try:
						Path( track.fullpath ).relative_to( pl_file.parent, walk_up=True )
					except Exception:
						logging.exception("Unknown exception, probably tried to use relative paths")
						self.show_message(
							_("Cannot use relative paths"),
							_("One or more tracks are stored on a separate drive from the playlist file."),
							mode="error",
						)
						return 1

		with pl_file.open(mode = "w", encoding="utf-8") as f:
			f.write("#EXTM3U")
			for number in self.pctl.multi_playlist[pl].playlist_ids:
				track = self.pctl.master_library[number]
				title = track.artist
				if title:
					title += " - "
				title += track.title

				if not track.is_network:
					f.write("\n#EXTINF:")
					f.write(str(round(track.length)))
					if title:
						f.write(f",{title}")
					path = Path( track.fullpath )
					if relative:
						path = path.relative_to( pl_file.parent, walk_up=True)
					path = str( path )
					f.write(f"\n{path}")

		return pl_file


	def export_xspf(self, pl: int, pl_file: Path | None = None, relative: bool = False) -> int | Path:
		"""Exports an xspf file from a Playlist dictionary in multi_playlist to a playlist file denoted by pl_file.
		pl_file is normalized by run_export; you should not call this function directly if you are uncertain.
		"""
		if len(self.pctl.multi_playlist[pl].playlist_ids) < 1:
			self.show_message(_("There are no tracks in this playlist. Nothing to export"))
			return 1
		if relative:
			for num in set( self.pctl.multi_playlist[pl].playlist_ids ):
				track = self.pctl.master_library[num]
				if not track.is_network:
					try:
						Path( track.fullpath ).relative_to( pl_file.parent, walk_up=True )
					except Exception:
						logging.exception("Unknown exception, probably tried to use relative paths")
						self.show_message(
							_("Cannot use relative paths"),
							_("One or more tracks are stored on a separate drive from the playlist file."),
							mode="error",
						)
						return 1

		xspf_root = ET.Element("playlist", version="1", xmlns="http://xspf.org/ns/0/")
		xspf_tracklist_tag = ET.SubElement(xspf_root, "trackList")

		for number in self.pctl.multi_playlist[pl].playlist_ids:
			track = self.pctl.master_library[number]
			try:
				path = track.fullpath
			except Exception:
				logging.exception("Unknown exception getting track fullpath")
				continue
			if relative:
				path = Path( track.fullpath ).relative_to( pl_file.parent, walk_up=True )

			xspf_track_tag = ET.SubElement(xspf_tracklist_tag, "track")
			if track.title:
				ET.SubElement(xspf_track_tag, "title").text = track.title
			if track.is_cue is False and track.fullpath:
				ET.SubElement(xspf_track_tag, "location").text = urllib.parse.quote(str(path))
			if track.artist:
				ET.SubElement(xspf_track_tag, "creator").text = track.artist
			if track.album:
				ET.SubElement(xspf_track_tag, "album").text = track.album
			if track.track_number:
				ET.SubElement(xspf_track_tag, "trackNum").text = str(track.track_number)

			ET.SubElement(xspf_track_tag, "duration").text = str(int(track.length * 1000))

		xspf_tree = ET.ElementTree(xspf_root)
		ET.indent(xspf_tree, space="  ", level=0)

		xspf_tree.write( str(pl_file) , encoding="UTF-8", xml_declaration=True)

		return pl_file

	def reload(self) -> None:
		if self.prefs.album_mode:
			self.reload_albums(quiet=True)

		# self.tree_view_box.clear_all()
		# elif self.gui.combo_mode:
		#	 self.reload_albums(quiet=True)
		#	 self.combo_pl_render.prep()

	def clear_playlist(self, index: int) -> None:
		if self.pl_is_locked(index):
			self.show_message(_("Playlist is locked to prevent accidental erasure"))
			return

		self.pctl.multi_playlist[index].last_folder.clear()  # clear import folder list

		if not self.pctl.multi_playlist[index].playlist_ids:
			logging.info("Playlist is already empty")
			return

		li: list[tuple[int, int]] = []
		for i, ref in enumerate(self.pctl.multi_playlist[index].playlist_ids):
			li.append((i, ref))

		self.undo.bk_tracks(index, list(reversed(li)))

		del self.pctl.multi_playlist[index].playlist_ids[:]
		if self.pctl.active_playlist_viewing == index:
			self.pctl.default_playlist = self.pctl.multi_playlist[index].playlist_ids
			self.reload()

		# self.pctl.playlist_playing = 0
		self.pctl.multi_playlist[index].position = 0
		if index == self.pctl.active_playlist_viewing:
			self.pctl.playlist_view_position = 0

		self.gui.request_tracklist_redraw()

	def clear_current_playlist(self) -> None:
		self.clear_playlist(self.pctl.active_playlist_viewing)

	def import_folder_to_current_playlist(self, path: str) -> None:
		pl = self.pctl.active_playlist_viewing
		if self.pl_is_locked(pl):
			self.show_message(_("Playlist is locked"))
			return

		target = path.replace("\\", "/")
		if not os.path.isdir(target):
			self.show_message(_("Folder not found"), mode="warning")
			return

		load_order = LoadClass()
		load_order.target = target
		load_order.playlist = self.pctl.multi_playlist[pl].uuid_int

		self.quick_import_done.append(load_order.target)
		self.pctl.multi_playlist[pl].last_folder.append(load_order.target)
		reduce_paths(self.pctl.multi_playlist[pl].last_folder)

		self.load_orders.append(copy.deepcopy(load_order))
		self.gui.request_frame()

	def convert_playlist(self, pl: int, get_list: bool = False) -> list[list[int]] | None:
		if not self.test_ffmpeg():
			return None

		paths: list[str] = []
		folders: list[list[int]] = []

		for track in self.pctl.multi_playlist[pl].playlist_ids:
			if self.pctl.master_library[track].parent_folder_path not in paths:
				paths.append(self.pctl.master_library[track].parent_folder_path)

		for path in paths:
			folder: list[int] = []
			for track in self.pctl.multi_playlist[pl].playlist_ids:
				if self.pctl.master_library[track].parent_folder_path == path:
					folder.append(track)
					if self.prefs.transcode_codec == "flac" and self.pctl.master_library[track].file_ext.lower() in (
						"mp3", "opus",
						"m4a", "mp4",
						"ogg", "aac"):
						self.show_message(_("This includes the conversion of a lossy codec to a lossless one!"))

			folders.append(folder)

		if get_list:
			return folders

		self.transcode_list.extend(folders)
		return None

	def get_folder_tracks_local(self, pl_in: int) -> list[int]:
		selection: list[int] = []
		parent = os.path.normpath(self.pctl.master_library[self.pctl.default_playlist[pl_in]].parent_folder_path)
		while pl_in < len(self.pctl.default_playlist) and parent == os.path.normpath(
				self.pctl.master_library[self.pctl.default_playlist[pl_in]].parent_folder_path):
			selection.append(pl_in)
			pl_in += 1
		return selection

	def test_pl_tab_locked(self, pl: int) -> bool:
		if self.gui.radio_view:
			return False
		return self.pctl.multi_playlist[pl].locked

	def rescan_tags(self, pl: int) -> None:
		for track in self.pctl.multi_playlist[pl].playlist_ids:
			if self.pctl.master_library[track].is_cue is False:
				self.to_scan.append(track)
		self.thread_manager.ready("worker")

	def append_playlist(self, index: int) -> None:
		self.pctl.multi_playlist[index].playlist_ids += self.pctl.cargo

		self.gui.request_tracklist_redraw()
		self.reload()

	#def sort_track_numbers_album_only(self, pl: int, custom_list: list[int] | None = None):
	#	current_folder = ""
	#	albums = []
	#	playlist = self.pctl.multi_playlist[pl].playlist_ids if custom_list is None else custom_list
	#
	#	for i in range(len(playlist)):
	#		if i == 0:
	#			albums.append(i)
	#			current_folder = self.pctl.master_library[playlist[i]].album
	#		elif self.pctl.master_library[playlist[i]].album != current_folder:
	#			current_folder = self.pctl.master_library[playlist[i]].album
	#			albums.append(i)
	#
	#	i = 0
	#	while i < len(albums) - 1:
	#		playlist[albums[i]:albums[i + 1]] = sorted(playlist[albums[i]:albums[i + 1]], key=self.pctl.index_key)
	#		i += 1
	#	if len(albums) > 0:
	#		playlist[albums[i]:] = sorted(playlist[albums[i]:], key=self.pctl.index_key)
	#
	#	gui.pl_update += 1

	def append_current_playing(self, index: int) -> None:
		if self.pctl.playing_state != PlayingState.STOPPED and len(self.pctl.track_queue) > 0:
			self.pctl.multi_playlist[index].playlist_ids.append(self.pctl.track_queue[self.pctl.queue_step])
			self.gui.request_tracklist_redraw()

	def export_stats(self, pl: int) -> None:
		playlist_time = 0
		play_time = 0
		total_size = 0
		tracks_in_playlist = len(self.pctl.multi_playlist[pl].playlist_ids)

		seen_files = {}
		seen_types = {}

		mp3_bitrates = {}
		ogg_bitrates = {}
		m4a_bitrates = {}

		are_cue = 0

		for index in self.pctl.multi_playlist[pl].playlist_ids:
			track = self.pctl.get_track(index)

			playlist_time += int(track.length)
			play_time += self.star_store.get(index)

			if track.is_cue:
				are_cue += 1

			if track.file_ext == "MP3":
				mp3_bitrates[track.bitrate] = mp3_bitrates.get(track.bitrate, 0) + 1
			if track.file_ext in ("OGG", "OGA"):
				ogg_bitrates[track.bitrate] = ogg_bitrates.get(track.bitrate, 0) + 1
			if track.file_ext == "M4A":
				m4a_bitrates[track.bitrate] = m4a_bitrates.get(track.bitrate, 0) + 1

			file_type = track.file_ext
			if file_type == "OGA":
				file_type = "OGG"
			seen_types[file_type] = seen_types.get(file_type, 0) + 1

			if track.fullpath and not track.is_network and track.fullpath not in seen_files:
				size = track.size
				if not size and os.path.isfile(track.fullpath):
					size = os.path.getsize(track.fullpath)
				seen_files[track.fullpath] = size

		total_size = sum(seen_files.values())

		self.stats_gen.update(pl)
		line = _("Playlist:") + "\n" + self.pctl.multi_playlist[pl].title + "\n\n"
		line += _("Generated:") + "\n" + time.strftime("%c") + "\n\n"
		line += _("Tracks in playlist:") + "\n" + str(tracks_in_playlist)
		line += "\n\n"
		line += _("Repeats in playlist:") + "\n"
		unique = len(set(self.pctl.multi_playlist[pl].playlist_ids))
		line += str(tracks_in_playlist - unique)
		line += "\n\n"
		line += _("Total local size:") + "\n" + get_filesize_string(total_size) + "\n\n"
		line += _("Playlist duration:") + "\n" + str(datetime.timedelta(seconds=int(playlist_time))) + "\n\n"
		line += _("Total playtime:") + "\n" + str(datetime.timedelta(seconds=int(play_time))) + "\n\n"

		line += _("Track types:") + "\n"
		if tracks_in_playlist:
			types = sorted(seen_types, key=seen_types.get, reverse=True)
			for track_type in types:
				perc = round((seen_types.get(track_type) / tracks_in_playlist) * 100, 1)
				if perc < 0.1:
					perc = "<0.1"
				if track_type == "SPOT":
					track_type = "SPOTIFY"
				if track_type == "SUB":
					track_type = "AIRSONIC"
				line += f"{track_type} ({perc}%); "
		line = line.rstrip("; ")
		line += "\n\n"

		if tracks_in_playlist:
			line += _("Percent of tracks are CUE type:") + "\n"
			perc = are_cue / tracks_in_playlist
			if perc == 0:
				perc = 0
			perc = "<0.01" if 0 < perc < 0.01 else round(perc, 2)

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

		ls = self.stats_gen.artist_list
		for i, item in enumerate(ls[:50]):
			line += str(i + 1) + ".\t" + self.stt2(item[1]) + "\t" + item[0] + "\n"

		line += "\n\n" + f"-------------- {_('Top Albums')} --------------------" + "\n\n"
		ls = self.stats_gen.album_list
		for i, item in enumerate(ls[:50]):
			line += str(i + 1) + ".\t" + self.stt2(item[1]) + "\t" + item[0] + "\n"
		line += "\n\n" + f"-------------- {_('Top Genres')} --------------------" + "\n\n"
		ls = self.stats_gen.genre_list
		for i, item in enumerate(ls[:50]):
			line += str(i + 1) + ".\t" + self.stt2(item[1]) + "\t" + item[0] + "\n"

		line = line.encode("utf-8")
		xport = (self.user_directory / "stats.txt").open("wb")
		xport.write(line)
		xport.close()
		target = str(self.user_directory / "stats.txt")
		if self.windows:
			os.startfile(target)
		elif self.macos:
			subprocess.call(["open", target])
		else:
			subprocess.call(["xdg-open", target])

	def imported_sort(self, pl: int) -> None:
		if self.pl_is_locked(pl):
			self.show_message(_("Playlist is locked"))
			return

		og = self.pctl.multi_playlist[pl].playlist_ids
		og.sort(key=lambda x: self.pctl.get_track(x).index)

		self.reload_albums()
		self.tree_view_box.clear_target_pl(pl)

	def imported_sort_folders(self, pl: int) -> None:
		if self.pl_is_locked(pl):
			self.show_message(_("Playlist is locked"))
			return

		og = self.pctl.multi_playlist[pl].playlist_ids
		og.sort(key=lambda x: self.pctl.get_track(x).index)

		first_occurrences = {}
		for i, x in enumerate(og):
			b = self.pctl.get_track(x).parent_folder_path
			if b not in first_occurrences:
				first_occurrences[b] = i

		og.sort(key=lambda x: first_occurrences[self.pctl.get_track(x).parent_folder_path])

		self.reload_albums()
		self.tree_view_box.clear_target_pl(pl)

	def standard_sort(self, pl: int) -> None:
		if self.pl_is_locked(pl):
			self.show_message(_("Playlist is locked"))
			return

		self.sort_path_pl(pl)
		self.sort_track_2(pl)
		self.reload_albums()
		self.tree_view_box.clear_target_pl(pl)

	def year_sort(self, pl: int, custom_list: list[int] | None = None) -> list[int] | None:
		playlist = self.pctl.multi_playlist[pl].playlist_ids if custom_list is None else custom_list
		plt: list[tuple[list[int], str, str]] = []
		pl2: list[int] = []
		artist = ""
		album_artist = ""

		p = 0
		while p < len(playlist):
			track = self.get_object(playlist[p])

			if track.artist != artist:
				if (album_artist and track.album_artist and album_artist == track.album_artist) or (len(artist) > 5 and artist.lower() in track.parent_folder_name.lower()):
					pass
				else:
					artist = track.artist
					pl2 += year_s(plt)
					plt = []

			if track.album_artist:
				album_artist = track.album_artist

			if p > len(playlist) - 1:
				break

			album: list[int] = []
			on = self.get_object(playlist[p]).parent_folder_path
			album.append(playlist[p])
			t = 1

			while t + p < len(playlist) and self.get_object(playlist[p + t]).parent_folder_path == on:
				album.append(playlist[p + t])
				t += 1

			date = self.get_object(playlist[p]).date

			# If date is xx-xx-yyyy format, just grab the year from the end
			# so that the M and D don't interfere with the sorter
			if len(date) > 4 and date[-4:].isnumeric():
				date = date[-4:]

			# If we don't have a date, see if we can grab one from the folder name
			# following the format: (XXXX)
			if date == "":
				pfn = self.get_object(playlist[p]).parent_folder_name
				if len(pfn) > 6 and pfn[-1] == ")" and pfn[-6] == "(":
					date = pfn[-5:-1]
			plt.append((album, date, artist + " " + self.get_object(playlist[p]).album))
			p += len(album)
			#logging.info(album)

		if plt:
			pl2 += year_s(plt)
			plt = []

		if custom_list is not None:
			return pl2

		# We can't just assign the playlist because it may disconnect the 'pointer' pctl.default_playlist
		self.pctl.multi_playlist[pl].playlist_ids[:] = pl2[:]
		self.reload_albums()
		self.tree_view_box.clear_target_pl(pl)
		return None

	def gen_unique_pl_title(self, base: str, extra: str = "", start: int = 1) -> str:
		ex = start
		title = base
		while ex < 100:
			for playlist in self.pctl.multi_playlist:
				if playlist.title == title:
					ex += 1
					title = base + " (" + extra.rstrip(" ") + ")" if ex == 1 else base + " (" + extra + str(ex) + ")"
					break
			else:
				break
		return title

	def append_deco(self) -> Decorator:
		line_colour = self.colours.menu_text if self.pctl.playing_state != PlayingState.STOPPED else self.colours.menu_text_disabled
		return Decorator(line_colour, self.colours.menu_background, None)

	def rescan_deco(self, pl: int) -> Decorator:
		if self.pctl.multi_playlist[pl].last_folder:
			line_colour = self.colours.menu_text
		else:
			line_colour = self.colours.menu_text_disabled

		# base = os.path.basename(self.pctl.multi_playlist[pl].last_folder)
		return Decorator(line_colour, self.colours.menu_background, None)

	def regenerate_deco(self, pl: int) -> Decorator:
		id = self.pctl.pl_to_id(pl)
		value = self.pctl.gen_codes.get(id)

		line_colour = self.colours.menu_text if value else self.colours.menu_text_disabled
		return Decorator(line_colour, self.colours.menu_background, None)

	def auto_sync_thread(self, pl: int) -> None:
		if self.prefs.transcode_inplace:
			self.show_message(_("Cannot sync when in transcode inplace mode"))
			return

		# Find target path
		self.gui.sync_progress = "Starting Sync..."
		self.gui.request_frame()

		path = Path(self.sync_target.text.strip().rstrip("/").rstrip("\\").replace("\n", "").replace("\r", ""))
		logging.debug(f"sync_path: {path}")
		if not path:
			self.show_message(_("No target folder selected"))
			self.gui.sync_progress = ""
			self.gui.stop_sync = False
			self.gui.request_frame()
			return
		if not path.is_dir():
			self.show_message(_("Target folder could not be found"))
			self.gui.sync_progress = ""
			self.gui.stop_sync = False
			self.gui.request_frame()
			return

		self.prefs.sync_target = str(path)

		# Get list of folder names on device
		logging.info("Getting folder list from device...")
		d_folder_names = [p.name for p in path.iterdir()]
		logging.info("Got list")

		# Get list of folders we want
		folders = self.convert_playlist(pl, get_list=True)
		folder_names: list[str] = []
		folder_dict: dict[str, list[int]] = {}

		if self.gui.stop_sync:
			self.gui.sync_progress = ""
			self.gui.stop_sync = False
			self.gui.request_frame()

		# Find the folder names the transcode function would name them
		for folder in folders:
			name = encode_folder_name(self.pctl.get_track(folder[0]))
			for item in folder:
				if self.pctl.get_track(item).album != self.pctl.get_track(folder[0]).album:
					name = os.path.basename(self.pctl.get_track(folder[0]).parent_folder_path)
					break
			folder_names.append(name)
			folder_dict[name] = folder

		# ------
		# Find deletes
		if self.prefs.sync_deletes:
			for d_folder in d_folder_names:
				d_folder = d_folder.name
				if self.gui.stop_sync:
					break
				if d_folder not in folder_names:
					self.gui.sync_progress = _("Deleting folders...")
					self.gui.request_frame()
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

		self.gui.request_frame()
		# -----
		# Prepare and copy
		for i, item in enumerate(todos):
			self.gui.sync_progress = _("Copying files to device")
			if self.gui.stop_sync:
				break

			free_space = shutil.disk_usage(path)[2] / 8 / 100000000  # in GB
			if free_space < 0.6:
				self.show_message(_("Sync aborted! Low disk space on target device"), mode="warning")
				break

			if self.prefs.bypass_transcode or (self.prefs.smart_bypass and 0 < self.pctl.get_track(folder_dict[item][0]).bitrate <= 128):
				logging.info("Smart bypass...")

				source_parent = Path(self.pctl.get_track(folder_dict[item][0]).parent_folder_path)
				if source_parent.exists():
					if (path / item).exists():
						self.show_message(
							_("Sync warning"), _("Multiple folders to sync have the same name. Skipping."), mode="warning")
						continue

					(path / item).mkdir()
					encode_done = source_parent
				else:
					self.show_message(_("One or more folders is missing"))
					continue
			else:
				encode_done = self.prefs.encoder_output / item
				# TODO(Martin): We should make sure that the length of the source and target matches or is greater, not just that the dir exists and is not empty!
				if not encode_done.exists() or not any(encode_done.iterdir()):
					logging.info("Need to transcode")
					remain = len(todos) - i
					if remain > 1:
						self.gui.sync_progress = _("{N} Folders Remaining").format(N=str(remain))
					else:
						self.gui.sync_progress = _("{N} Folder Remaining").format(N=str(remain))
					self.transcode_list.append(folder_dict[item])
					self.thread_manager.ready("worker")
					while self.transcode_list:
						time.sleep(1)
					if self.gui.stop_sync:
						break
				else:
					logging.warning("A transcode is already done")

				if encode_done.exists():
					if (path / item).exists():
						self.show_message(
							_("Sync warning"), _("Multiple folders to sync have the same name. Skipping."), mode="warning")
						continue

					(path / item).mkdir()

			for file in encode_done.iterdir():
				file = file.name
				logging.info(f"Copy file {file} to {path / item}…")
				# self.gui.sync_progress += "."
				self.gui.request_frame()

				if (encode_done / file).is_file():
					size = os.path.getsize(encode_done / file)
					self.sync_file_timer.set()
					try:
						shutil.copyfile(encode_done / file, path / item / file)
					except OSError as e:
						if str(e).startswith("[Errno 22] Invalid argument: "):
							sanitized_file = re.sub(r'[<>:"/\\|?*]', "_", file)
							if sanitized_file == file:
								logging.exception("Unknown OSError trying to copy file, maybe FS does not support the name?")
							else:
								shutil.copyfile(encode_done / file, path / item / sanitized_file)
								logging.warning(f"Had to rename {file} to {sanitized_file} on the output! Probably a FS limitation!")
						else:
							logging.exception("Unknown OSError trying to copy file")
					except Exception:
						logging.exception("Unknown error trying to copy file")

				if self.gui.sync_speed == 0 or (self.sync_file_update_timer.get() > 1 and not file.endswith(".jpg")):
					self.sync_file_update_timer.set()
					self.gui.sync_speed = size / self.sync_file_timer.get()
					self.gui.sync_progress = _("Copying files to device") + " @ " + get_filesize_string_rounded(
						self.gui.sync_speed) + "/s"
					if self.gui.stop_sync:
						self.gui.sync_progress = _("Aborting Sync") + " @ " + get_filesize_string_rounded(self.gui.sync_speed) + "/s"

			logging.info("Finished copying folder")

		self.gui.sync_speed = 0
		self.gui.sync_progress = ""
		self.gui.stop_sync = False
		self.gui.request_frame()
		self.show_message(_("Sync completed"), mode="done")

	def auto_sync(self, pl: int) -> None:
		shoot_dl = threading.Thread(target=self.auto_sync_thread, args=([pl]))
		shoot_dl.daemon = True
		shoot_dl.start()

	def set_sync_playlist(self, pl: int) -> None:
		id = self.pctl.pl_to_id(pl)
		if self.prefs.sync_playlist == id:
			self.prefs.sync_playlist = None
		else:
			self.prefs.sync_playlist = self.pctl.pl_to_id(pl)

	def sync_playlist_deco(self, pl: int) -> Decorator:
		text = _("Set as Sync Playlist")
		id = self.pctl.pl_to_id(pl)
		if id == self.prefs.sync_playlist:
			text = _("Un-set as Sync Playlist")
		return Decorator(self.colours.menu_text, self.colours.menu_background, text)

	def set_download_playlist(self, pl: int) -> None:
		id = self.pctl.pl_to_id(pl)
		if self.prefs.download_playlist == id:
			self.prefs.download_playlist = None
		else:
			self.prefs.download_playlist = self.pctl.pl_to_id(pl)

	def set_podcast_playlist(self, pl: int) -> None:
		self.pctl.multi_playlist[pl].persist_time_positioning ^= True

	def set_download_deco(self, pl: int) -> Decorator:
		id = self.pctl.pl_to_id(pl)
		text = _("Set as Downloads Playlist")
		if id == self.prefs.download_playlist:
			text = _("Un-set as Downloads Playlist")
		return Decorator(self.colours.menu_text, self.colours.menu_background, text)

	def set_podcast_deco(self, pl: int) -> Decorator:
		text = _("Set Use Persistent Time")
		if self.pctl.multi_playlist[pl].persist_time_positioning:
			text = _("Un-set Use Persistent Time")
		return Decorator(self.colours.menu_text, self.colours.menu_background, text)

	def export_playlist_albums(self, pl: int) -> None:
		p = self.pctl.multi_playlist[pl]
		name = p.title
		playlist = p.playlist_ids

		albums: list[int] = []
		playtimes: dict[str, int] = {}
		last_folder = None
		for i, id in enumerate(playlist):
			track = self.pctl.get_track(id)
			if last_folder != track.parent_folder_path:
				last_folder = track.parent_folder_path
				if id not in albums:
					albums.append(id)

			playtimes[last_folder] = playtimes.get(last_folder, 0) + int(self.star_store.get(id))

		filepath = self.user_directory / f"{name}.csv"
		with open(filepath, "w", encoding="utf-8") as xport:
			xport.write("Album name,Artist,Release date,Genre,Rating,Playtime,Folder path")

			for id in albums:
				track = self.pctl.get_track(id)
				artist = track.album_artist
				if not artist:
					artist = track.artist

				xport.write("\n")
				xport.write(csv_string(track.album) + ",")
				xport.write(csv_string(artist) + ",")
				xport.write(csv_string(track.date) + ",")
				xport.write(csv_string(track.genre) + ",")
				xport.write(str(int(self.album_star_store.get_rating(track))))
				xport.write(",")
				xport.write(str(round(playtimes[track.parent_folder_path])))
				xport.write(",")
				xport.write(csv_string(track.parent_folder_path))

		self.show_message(_("Export complete."), _("Saved as: ") + str(filepath), mode="done")

	def best(self, index: int) -> float:
		# key = self.pctl.master_library[index].title + pctl.master_library[index].filename
		if self.pctl.master_library[index].length < 1:
			return 0
		return int(self.star_store.get(index))

	def key_rating(self, index: int) -> int:
		return self.star_store.get_rating(index)

	def key_scrobbles(self, index: int) -> int:
		return self.pctl.get_track(index).lfm_scrobbles

	def key_disc(self, index: int) -> str:
		return self.pctl.get_track(index).disc_number

	def key_cue(self, index: int) -> bool:
		return self.pctl.get_track(index).is_cue

	def key_track_id(self, index: int) -> int:
		return index

	def key_playcount(self, index: int) -> float:
		# key = self.pctl.master_library[index].title + self.pctl.master_library[index].filename
		if self.pctl.master_library[index].length < 1:
			return 0
		return self.star_store.get(index) / self.pctl.master_library[index].length
		# if key in self.pctl.star_library:
		#	 return self.pctl.star_library[key] / self.pctl.master_library[index].length
		# else:
		#	 return 0

	def gen_top_rating(self, index: int, custom_list: list[int] | None = None) -> list[int] | None:
		source = self.pctl.multi_playlist[index].playlist_ids if custom_list is None else custom_list
		playlist = copy.deepcopy(source)
		playlist = sorted(playlist, key=self.key_rating, reverse=True)

		if custom_list is not None:
			return playlist

		self.pctl.multi_playlist.append(
			self.pl_gen(
				title=self.pctl.multi_playlist[index].title + add_pl_tag(_("Top Rated Tracks")),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=True))

		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[index].title + "\" a rat>"
		return None

	def gen_top_100(self, index: int, custom_list: list[int] | None = None) -> list[int] | None:
		source = self.pctl.multi_playlist[index].playlist_ids if custom_list is None else custom_list
		playlist = copy.deepcopy(source)
		playlist = sorted(playlist, key=self.best, reverse=True)

		if custom_list is not None:
			return playlist

		self.pctl.multi_playlist.append(
			self.pl_gen(
				title=self.pctl.multi_playlist[index].title + add_pl_tag(_("Top Played Tracks")),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=True))

		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[index].title + "\" a pt>"
		return None

	def gen_folder_top(self, pl: int, get_sets: bool = False, custom_list: list[int] | None = None) -> list[int] | list[tuple[list[int], int]] | None:
		source = self.pctl.multi_playlist[pl].playlist_ids if custom_list is None else custom_list

		if not source:
			return []

		sets: list[list[int]] = []
		se: list[int] = []
		tr = self.pctl.get_track(source[0])
		last = tr.parent_folder_path
		last_al = tr.album
		for track in source:
			if last != self.pctl.master_library[track].parent_folder_path or last_al != self.pctl.master_library[track].album:
				last = self.pctl.master_library[track].parent_folder_path
				last_al = self.pctl.master_library[track].album
				sets.append(copy.deepcopy(se))
				se = []
			se.append(track)
		sets.append(copy.deepcopy(se))

		def best(folder: list[int]) -> int:
			#logging.info(folder)
			total_star: int = 0
			for item in folder:
				# key = self.pctl.master_library[item].title + self.pctl.master_library[item].filename
				# if key in self.pctl.star_library:
				#	 total_star += int(self.pctl.star_library[key])
				total_star += int(self.star_store.get(item))
			#logging.info(total_star)
			return total_star

		if get_sets:
			r: list[tuple[list[int], int]] = []
			for item in sets:
				r.append((item, best(item)))
			return r

		sets = sorted(sets, key=best, reverse=True)

		playlist: list[int] = []

		for se in sets:
			playlist += se

		# self.pctl.multi_playlist.append(
		#	 [self.pctl.multi_playlist[pl].title + " <Most Played Albums>", 0, copy.deepcopy(playlist), 0, 0, 0])
		if custom_list is not None:
			return playlist

		self.pctl.multi_playlist.append(
			self.pl_gen(
				title=self.pctl.multi_playlist[pl].title + add_pl_tag(_("Top Played Albums")),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=False))

		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[pl].title + "\" a pa>"
		return None

	def gen_folder_top_rating(self, pl: int, get_sets: bool = False, custom_list: list[int] | None = None) -> list[int] | None:
		source = self.pctl.multi_playlist[pl].playlist_ids if custom_list is None else custom_list

		if not source:
			return []

		sets: list[list[int]] = []
		se: list[int] = []
		tr = self.pctl.get_track(source[0])
		last = tr.parent_folder_path
		last_al = tr.album
		for track in source:
			if last != self.pctl.master_library[track].parent_folder_path or last_al != self.pctl.master_library[track].album:
				last = self.pctl.master_library[track].parent_folder_path
				last_al = self.pctl.master_library[track].album
				sets.append(copy.deepcopy(se))
				se = []
			se.append(track)
		sets.append(copy.deepcopy(se))

		def best(folder: list[int]) -> int:
			return self.album_star_store.get_rating(self.pctl.get_track(folder[0]))

		if get_sets:
			r = []
			for item in sets:
				r.append((item, best(item)))
			return r

		sets = sorted(sets, key=best, reverse=True)

		playlist: list[int] = []

		for se in sets:
			playlist += se

		if custom_list is not None:
			return playlist

		self.pctl.multi_playlist.append(
			self.pl_gen(
				title=self.pctl.multi_playlist[pl].title + add_pl_tag(_("Top Rated Albums")),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=False))

		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[pl].title + "\" a rata>"
		return None

	def gen_lyrics(self, pl: int, custom_list: list[int] | None = None) -> list[int] | None:
		playlist: list[int] = []
		source = self.pctl.multi_playlist[pl].playlist_ids if custom_list is None else custom_list

		for item in source:
			if self.pctl.master_library[item].lyrics:
				playlist.append(item)

		if custom_list is not None:
			return playlist

		if len(playlist) > 0:
			self.pctl.multi_playlist.append(
				self.pl_gen(
					title=_("Tracks with lyrics"),
					playlist_ids=copy.deepcopy(playlist),
					hide_title=False))

			self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[pl].title + "\" a ly"
		else:
			self.show_message(_("No tracks with lyrics were found."))
		return None

	def gen_incomplete(self, pl: int, custom_list: list[int] | None = None) -> list[int] | None:
		playlist: list[int] = []

		source = self.pctl.multi_playlist[pl].playlist_ids if custom_list is None else custom_list

		albums: dict[str, list[TrackClass]] = {}
		nums: dict[str, list[int]] = {}
		for id in source:
			track = self.pctl.get_track(id)
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
				r = list(range(int(mi), int(mx) + 1))
				for track in tracks:
					if int(track.track_number) in r:
						r.remove(int(track.track_number))
				if r or mi > 1:
					for tr in tracks:
						playlist.append(tr.index)

		if custom_list is not None:
			return playlist

		if len(playlist) > 0:
			self.show_message(_("Note this may include albums that simply have tracks missing an album tag"))
			self.pctl.multi_playlist.append(
				self.pl_gen(
					title=self.pctl.multi_playlist[pl].title + add_pl_tag(_("Incomplete Albums")),
					playlist_ids=copy.deepcopy(playlist),
					hide_title=False))

			# self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[pl].title + "\" a ly"
		else:
			self.show_message(_("No incomplete albums were found."))
		return None

	def gen_codec_pl(self, codec: str) -> None:
		playlist = []

		for pl in self.pctl.multi_playlist:
			for item in pl.playlist_ids:
				if self.pctl.master_library[item].file_ext == codec and item not in playlist:
					playlist.append(item)

		if len(playlist) > 0:
			self.pctl.multi_playlist.append(
				self.pl_gen(
					title=_("Codec: ") + codec,
					playlist_ids=copy.deepcopy(playlist),
					hide_title=False))

	def gen_last_imported_folders(self, index: int, custom_list: list[int] | None = None, reverse: bool = True) -> int | list[int] | None:
		source = self.pctl.multi_playlist[index].playlist_ids if custom_list is None else custom_list

		a_cache: dict[tuple[str, str], int] = {}

		def key_import(index: int) -> int:
			track = self.pctl.master_library[index]
			cached = a_cache.get((track.album, track.parent_folder_name))
			if cached is not None:
				return cached

			if track.album:
				a_cache[(track.album, track.parent_folder_name)] = index
			return index

		playlist = copy.deepcopy(source)
		playlist = sorted(playlist, key=key_import, reverse=reverse)
		self.sort_track_2(0, playlist)

		if custom_list is not None:
			return playlist
		return None

	def gen_last_modified(self, index: int, custom_list: list[int] | None = None, reverse: bool = True) -> list[int] | None:
		source = self.pctl.multi_playlist[index].playlist_ids if custom_list is None else custom_list

		a_cache: dict[tuple[str, str], float] = {}

		def key_modified(index: int) -> float:
			track = self.pctl.master_library[index]
			cached = a_cache.get((track.album, track.parent_folder_name))
			if cached is not None:
				return cached

			if track.album:
				a_cache[(track.album, track.parent_folder_name)] = self.pctl.master_library[index].modified_time
			return self.pctl.master_library[index].modified_time

		playlist = copy.deepcopy(source)
		playlist = sorted(playlist, key=key_modified, reverse=reverse)
		self.sort_track_2(0, playlist)

		if custom_list is not None:
			return playlist

		self.pctl.multi_playlist.append(
			self.pl_gen(
				title=self.pctl.multi_playlist[index].title + add_pl_tag(_("File Modified")),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=False))

		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[index].title + "\" a m>"
		return None

	def gen_love(self, pl: int, custom_list: list[int] | None = None) -> list[int] | None:
		playlist: list[int] = []

		source = self.pctl.multi_playlist[pl].playlist_ids if custom_list is None else custom_list

		for item in source:
			if self.get_love_index(item):
				playlist.append(item)

		playlist.sort(key=lambda x: self.get_love_timestamp_index(x), reverse=True)

		if custom_list is not None:
			return playlist

		if len(playlist) > 0:
			# self.pctl.multi_playlist.append(["Interesting Comments", 0, copy.deepcopy(playlist), 0, 0, 0])
			self.pctl.multi_playlist.append(
				self.pl_gen(
					title=_("Loved"),
					playlist_ids=copy.deepcopy(playlist),
					hide_title=False))
			self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[pl].title + "\" a l"
		else:
			self.show_message(_("No loved tracks were found."))
		return None

	def gen_comment(self, pl: int) -> None:
		playlist: list[int] = []

		for item in self.pctl.multi_playlist[pl].playlist_ids:
			cm = self.pctl.master_library[item].comment
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
			# self.pctl.multi_playlist.append(["Interesting Comments", 0, copy.deepcopy(playlist), 0, 0, 0])
			self.pctl.multi_playlist.append(
				self.pl_gen(
					title=_("Interesting Comments"),
					playlist_ids=copy.deepcopy(playlist),
					hide_title=False))
		else:
			self.show_message(_("Nothing of interest was found."))

	def gen_replay(self, pl: int) -> None:
		playlist: list[int] = []

		for item in self.pctl.multi_playlist[pl].playlist_ids:
			if self.pctl.master_library[item].replaygain_track_gain:
				playlist.append(item)

		if len(playlist) > 0:
			self.pctl.multi_playlist.append(
				self.pl_gen(
					title=_("ReplayGain Tracks"),
					playlist_ids=copy.deepcopy(playlist),
					hide_title=False))
		else:
			self.show_message(_("No replay gain tags were found."))

	def gen_sort_len(self, index: int, custom_list: list[int] | None = None) -> list[int] | None:
		source = self.pctl.multi_playlist[index].playlist_ids if custom_list is None else custom_list

		def length(index: int) -> int:
			if self.pctl.master_library[index].length < 1:
				return 0
			return int(self.pctl.master_library[index].length)

		playlist = copy.deepcopy(source)
		playlist = sorted(playlist, key=length, reverse=True)

		if custom_list is not None:
			return playlist

		# self.pctl.multi_playlist.append(
		#	 [self.pctl.multi_playlist[index].title + " <Duration Sorted>", 0, copy.deepcopy(playlist), 0, 1, 0])

		self.pctl.multi_playlist.append(
			self.pl_gen(
				title=self.pctl.multi_playlist[index].title + add_pl_tag(_("Duration Sorted")),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=True))

		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[index].title + "\" a d>"
		return None

	def gen_folder_duration(
		self, pl: int, get_sets: bool = False, custom_list: list[int] | None = None, reverse: bool = True,
	) -> list[int] | list[tuple[list[int], float]] | None:
		source = self.pctl.multi_playlist[pl].playlist_ids if custom_list is None else custom_list

		if not source:
			if custom_list is not None or get_sets:
				return []
			return None

		sets: list[list[int]] = []
		se:         list[int] = []
		last = self.pctl.master_library[source[0]].parent_folder_path
		last_al = self.pctl.master_library[source[0]].album
		for track in source:
			if last != self.pctl.master_library[track].parent_folder_path or last_al != self.pctl.master_library[track].album:
				last = self.pctl.master_library[track].parent_folder_path
				last_al = self.pctl.master_library[track].album
				sets.append(copy.deepcopy(se))
				se = []
			se.append(track)
		sets.append(copy.deepcopy(se))

		def best(folder: list[int]) -> float:
			total_duration = 0.
			for item in folder:
				total_duration += self.pctl.master_library[item].length
			return total_duration

		if get_sets:
			r: list[tuple[list[int], float]] = []
			for item in sets:
				r.append((item, best(item)))
			return r

		sets = sorted(sets, key=best, reverse=reverse)
		playlist: list[int] = []

		for se in sets:
			playlist += se

		if custom_list is not None:
			return playlist

		self.pctl.multi_playlist.append(
			self.pl_gen(
				title=self.pctl.multi_playlist[pl].title + add_pl_tag(_("Longest Albums")),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=False))
		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[pl].title + "\" a ad>"
		return None

	def gen_sort_date(self, index: int, rev: bool = False, custom_list: list[int] | None = None) -> list[int] | None:
		def g_date(index: int) -> str:
			if self.pctl.master_library[index].date:
				return str(self.pctl.master_library[index].date)
			return "z"

		playlist: list[int] = []
		lowest = 0
		highest = 0
		first = True

		source = self.pctl.multi_playlist[index].playlist_ids if custom_list is None else custom_list

		for item in source:
			date = self.pctl.master_library[item].date
			if date:
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
		if lowest not in (highest, 0) and highest != 0:
			if rev:
				line = " <" + str(highest) + "-" + str(lowest) + ">"
			else:
				line = " <" + str(lowest) + "-" + str(highest) + ">"

		self.pctl.multi_playlist.append(
			self.pl_gen(
				title=self.pctl.multi_playlist[index].title + line,
				playlist_ids=copy.deepcopy(playlist),
				hide_title=False))

		if rev:
			self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[index].title + "\" a y>"
		else:
			self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[index].title + "\" a y<"
		return None

	def gen_sort_date_new(self, index: int) -> None:
		self.gen_sort_date(index, True)

	def gen_500_random(self, index: int) -> None:
		playlist = copy.deepcopy(self.pctl.multi_playlist[index].playlist_ids)

		random.shuffle(playlist)

		self.pctl.multi_playlist.append(
			self.pl_gen(
				title=self.pctl.multi_playlist[index].title + add_pl_tag(_("Shuffled Tracks")),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=True))

		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[index].title + "\" a st"

	def gen_folder_shuffle(self, index: int, custom_list: list[int] | None = None) -> list[int] | None:
		folders: list[str] = []
		dick: dict[str, list[int]] = {}

		source = self.pctl.multi_playlist[index].playlist_ids if custom_list is None else custom_list

		for track in source:
			parent = self.pctl.master_library[track].parent_folder_path
			if parent not in folders:
				folders.append(parent)
			if parent not in dick:
				dick[parent] = []
			dick[parent].append(track)

		random.shuffle(folders)
		playlist: list[int] = []

		for folder in folders:
			playlist += dick[folder]

		if custom_list is not None:
			return playlist

		self.pctl.multi_playlist.append(
			self.pl_gen(
				title=self.pctl.multi_playlist[index].title + add_pl_tag(_("Shuffled Albums")),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=False))

		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[index].title + "\" a ra"
		return None

	def gen_best_random(self, index: int) -> None:
		playlist = []

		for p in self.pctl.multi_playlist[index].playlist_ids:
			time = self.star_store.get(p)

			if time > 300:
				playlist.append(p)

		random.shuffle(playlist)

		if len(playlist) > 0:
			self.pctl.multi_playlist.append(
				self.pl_gen(
					title=self.pctl.multi_playlist[index].title + add_pl_tag(_("Lucky Random")),
					playlist_ids=copy.deepcopy(playlist),
					hide_title=True))

			self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[index].title + "\" a pt>300 rt"

	def gen_reverse(self, index: int, custom_list: list[int] | None = None) -> list[int] | None:
		source = self.pctl.multi_playlist[index].playlist_ids if custom_list is None else custom_list

		playlist = list(reversed(source))

		if custom_list is not None:
			return playlist

		self.pctl.multi_playlist.append(
			self.pl_gen(
				title=self.pctl.multi_playlist[index].title + add_pl_tag(_("Reversed")),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=self.pctl.multi_playlist[index].hide_title))

		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[index].title + "\" a rv"
		return None

	def gen_folder_reverse(self, index: int, custom_list: list[int] | None = None) -> list[int] | None:
		source = self.pctl.multi_playlist[index].playlist_ids if custom_list is None else custom_list

		folders: list[str] = []
		dick: dict[str, list[int]] = {}
		for track in source:
			parent = self.pctl.master_library[track].parent_folder_path
			if parent not in folders:
				folders.append(parent)
			if parent not in dick:
				dick[parent] = []
			dick[parent].append(track)

		folders = list(reversed(folders))
		playlist: list[int] = []

		for folder in folders:
			playlist += dick[folder]

		if custom_list is not None:
			return playlist

		self.pctl.multi_playlist.append(
			self.pl_gen(
				title=self.pctl.multi_playlist[index].title + add_pl_tag(_("Reversed Albums")),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=False))

		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[index].title + "\" a rva"
		return None

	def gen_dupe(self, index: int) -> None:
		playlist = self.pctl.multi_playlist[index].playlist_ids

		self.pctl.multi_playlist.append(
			self.pl_gen(
				title=self.gen_unique_pl_title(self.pctl.multi_playlist[index].title, _("Duplicate") + " ", 0),
				playing=self.pctl.multi_playlist[index].playing,
				playlist_ids=copy.deepcopy(playlist),
				position=self.pctl.multi_playlist[index].position,
				hide_title=self.pctl.multi_playlist[index].hide_title,
				selected=self.pctl.multi_playlist[index].selected))

	def gen_sort_path(self, index: int) -> None:
		def path(index: int) -> str:
			return self.pctl.master_library[index].fullpath

		playlist = copy.deepcopy(self.pctl.multi_playlist[index].playlist_ids)
		playlist = sorted(playlist, key=path)

		self.pctl.multi_playlist.append(
			self.pl_gen(
				title=self.pctl.multi_playlist[index].title + add_pl_tag(_("Filepath Sorted")),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=False))

	def gen_sort_artist(self, index: int) -> None:
		def artist(index: int) -> str:
			return self.pctl.master_library[index].artist

		playlist = copy.deepcopy(self.pctl.multi_playlist[index].playlist_ids)
		playlist = sorted(playlist, key=artist)

		self.pctl.multi_playlist.append(
			self.pl_gen(
				title=self.pctl.multi_playlist[index].title + add_pl_tag(_("Artist Sorted")),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=False))

	def gen_sort_album(self, index: int) -> None:
		def album(index: int) -> str:
			return self.pctl.master_library[index].album

		playlist = copy.deepcopy(self.pctl.multi_playlist[index].playlist_ids)
		playlist = sorted(playlist, key=album)

		self.pctl.multi_playlist.append(
			self.pl_gen(
				title=self.pctl.multi_playlist[index].title + add_pl_tag(_("Album Sorted")),
				playlist_ids=copy.deepcopy(playlist),
				hide_title=False))

	def get_playing_line(self) -> str:
		if self.pctl.playing_state in (PlayingState.PLAYING, PlayingState.PAUSED):
			title = self.pctl.master_library[self.pctl.track_queue[self.pctl.queue_step]].title
			artist = self.pctl.master_library[self.pctl.track_queue[self.pctl.queue_step]].artist
			return artist + " - " + title
		return "Stopped"

	def reload_config_file(self) -> None:
		if self.transcode_list:
			self.show_message(_("Cannot reload while a transcode is in progress!"), mode="error")
			return

		load_prefs(bag=self.bag)
		self.gui.opened_config_file = False

		self.ddt.force_subpixel_text = self.prefs.force_subpixel_text
		self.ddt.clear_text_cache()
		self.pctl.playerCommand = "reload"
		self.pctl.playerCommandReady = True
		self.show_message(_("Configuration reloaded"), mode="done")
		self.gui.update_layout = True

	def open_config_file(self) -> None:
		save_prefs(bag=self.bag)
		target = str(self.config_directory / "tauon.conf")
		if self.windows:
			os.startfile(target)
		elif self.macos:
			subprocess.call(["open", "-t", target])
		else:
			subprocess.call(["xdg-open", target])
		self.show_message(_("Config file opened."), _('Click "Reload" if you made any changes'), mode="arrow")
		# self.reload_config_file()
		# self.gui.message_box = False
		self.gui.opened_config_file = True

	def open_keymap_file(self) -> None:
		target = str(self.config_directory / "input.txt")

		if not os.path.isfile(target):
			self.show_message(_("Input file missing"))
			return

		if self.windows:
			os.startfile(target)
		elif self.macos:
			subprocess.call(["open", target])
		else:
			subprocess.call(["xdg-open", target])

	def open_file(self, target: str) -> None:
		if not os.path.isfile(target):
			self.show_message(_("Input file missing"))
			return

		if self.windows:
			os.startfile(target)
		elif self.macos:
			subprocess.call(["open", target])
		else:
			subprocess.call(["xdg-open", target])

	def open_data_directory(self) -> None:
		target = str(self.user_directory)
		if self.windows:
			os.startfile(target)
		elif self.macos:
			subprocess.call(["open", target])
		else:
			subprocess.call(["xdg-open", target])

	def remove_folder(self, index: int) -> None:
		for b in range(len(self.pctl.default_playlist) - 1, -1, -1):
			r_folder = self.pctl.master_library[index].parent_folder_name
			if self.pctl.master_library[self.pctl.default_playlist[b]].parent_folder_name == r_folder:
				del self.pctl.default_playlist[b]
		self.reload()

	def convert_folder(self, ref: MenuTrackRef) -> None:
		if not self.test_ffmpeg():
			return

		track_id = ref.track_id
		folder = []
		if self.inp.key_shift_down or self.inp.key_shiftr_down:
			track_object = self.pctl.get_track(track_id)
			if track_object.is_network:
				self.show_message(_("Transcoding tracks from network locations is not supported"))
				return
			folder = [track_id]

			if self.prefs.transcode_codec == "flac" and track_object.file_ext.lower() in (
				"mp3", "opus",
				"mp4", "ogg",
				"aac"):
				self.show_message(_("NO! Bad user!"), _("I'm not going to let you transcode a lossy codec to a lossless one!"),
					mode="warning")

				return
			folder = [track_id]

		else:
			r_folder = self.pctl.master_library[track_id].parent_folder_path
			for item in self.pctl.default_playlist:
				if r_folder == self.pctl.master_library[item].parent_folder_path:

					track_object = self.pctl.get_track(item)
					if track_object.file_ext == "SPOT":  # track_object.is_network:
						self.show_message(_("Transcoding this network track type is not possible"))
						return

					if item not in folder:
						folder.append(item)
					#logging.info(prefs.transcode_codec)
					#logging.info(track_object.file_ext)
					if self.prefs.transcode_codec == "flac" and track_object.file_ext.lower() in (
						"mp3", "opus",
						"mp4", "ogg",
						"aac"):
						self.show_message(_("NO! Bad user!"), _("I'm not going to let you transcode a lossy codec to a lossless one!"),
							mode="warning")

						return

		#logging.info(folder)
		self.transcode_list.append(folder)
		self.thread_manager.ready("worker")

	def transfer(self, index: int, args: list[int]) -> None:
		old_cargo = copy.deepcopy(self.pctl.cargo)

		if args[0] == 1 or args[0] == 0:  # copy
			if args[1] == 1:  # single track
				self.pctl.cargo.append(index)
				if args[0] == 0:  # cut
					del self.pctl.default_playlist[self.pctl.selected_in_playlist]
			elif args[1] == 2:  # folder
				for b in range(len(self.pctl.default_playlist)):
					if self.pctl.master_library[self.pctl.default_playlist[b]].parent_folder_name == self.pctl.master_library[
						index].parent_folder_name:
						self.pctl.cargo.append(self.pctl.default_playlist[b])
				if args[0] == 0:  # cut
					for b in reversed(range(len(self.pctl.default_playlist))):
						if self.pctl.master_library[self.pctl.default_playlist[b]].parent_folder_name == self.pctl.master_library[
							index].parent_folder_name:
							del self.pctl.default_playlist[b]
			elif args[1] == 3:  # playlist
				self.pctl.cargo += self.pctl.default_playlist
				if args[0] == 0:  # cut
					self.pctl.default_playlist = []
		elif args[0] == 2:  # Drop
			if args[1] == 1:  # Before
				insert = self.pctl.selected_in_playlist
				while insert > 0 and self.pctl.master_library[self.pctl.default_playlist[insert]].parent_folder_name == \
						self.pctl.master_library[index].parent_folder_name:
					insert -= 1
					if insert == 0:
						break
				else:
					insert += 1

				while len(self.pctl.cargo) > 0:
					self.pctl.default_playlist.insert(insert, self.pctl.cargo.pop())
			elif args[1] == 2:  # After
				insert = self.pctl.selected_in_playlist

				while insert < len(self.pctl.default_playlist) \
				and self.pctl.master_library[self.pctl.default_playlist[insert]].parent_folder_name == self.pctl.master_library[index].parent_folder_name:
					insert += 1

				while len(self.pctl.cargo) > 0:
					self.pctl.default_playlist.insert(insert, self.pctl.cargo.pop())
			elif args[1] == 3:  # End
				self.pctl.default_playlist += self.pctl.cargo
				# self.pctl.cargo = []

			self.pctl.cargo = old_cargo
		self.reload()

	def temp_copy_folder(self, ref: int) -> None:
		self.pctl.cargo = []
		self.transfer(ref, args=[1, 2])

	def show_track_box(self, track_id: int) -> None:
		self.gui.track_box_track_id = track_id
		self.gui.track_box = True
		self.track_box_path_tool_timer.set()

	def sync_track_box_to_selected(self) -> None:
		if self.gui.track_box and self.pctl.selected_ready():
			self.gui.track_box_track_id = self.pctl.default_playlist[self.pctl.selected_in_playlist]

	def activate_track_box(self, ref: MenuTrackRef) -> None:
		self.show_track_box(ref.track_id)

	def menu_paste(self, ref: MenuTrackRef) -> None:
		self.paste(None, ref.track_id, ref.position)

	def lightning_paste(self) -> None:
		move = True
		# if not self.inp.key_shift_down:
		#	 move = False

		move_track = self.pctl.get_track(self.pctl.cargo[0])
		move_path = move_track.parent_folder_path

		for item in self.pctl.cargo:
			if move_path != self.pctl.get_track(item).parent_folder_path:
				self.show_message(
					_("More than one folder is in the clipboard"),
					_("This function can only move one folder at a time."), mode="info")
				return

		match_track = self.pctl.get_track(self.pctl.default_playlist[self.gui.shift_selection[0]])
		match_path = match_track.parent_folder_path

		if self.pctl.playing_state != PlayingState.STOPPED and move and self.pctl.playing_object().parent_folder_path == move_path:
			self.pctl.stop(True)

		p = Path(match_path)
		s = list(p.parts)
		base = s[0]
		c = base
		del s[0]

		to_move = []
		for pl in self.pctl.multi_playlist:
			for i in reversed(range(len(pl.playlist_ids))):
				if self.pctl.get_track(pl.playlist_ids[i]).parent_folder_path == move_track.parent_folder_path:
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
				logging.info(f"Upper folder is: {upper}")

				if len(move_path) < 4:
					self.show_message(_("Safety interrupt! The source path seems oddly short."), move_path, mode="error")
					return

				if not os.path.isdir(upper):
					self.show_message(_("The target directory is missing!"), upper, mode="warning")
					return

				if not os.path.isdir(move_path):
					self.show_message(_("The source directory is missing!"), move_path, mode="warning")
					return

				protect = ("", "Documents", "Music", "Desktop", "Downloads")
				for fo in protect:
					if move_path.strip("\\/") == os.path.join(os.path.expanduser("~"), fo).strip("\\/"):
						self.show_message(_("Better not do anything to that folder!"), os.path.join(os.path.expanduser("~"), fo),
							mode="warning")
						return

				if directory_size(move_path) > 3000000000:
					self.show_message(_("Folder size safety limit reached! (3GB)"), move_path, mode="warning")
					return

				if len(next(os.walk(move_path))[2]) > max(20, len(to_move) * 2):
					self.show_message(_("Safety interrupt! The source folder seems to have many files."), move_path, mode="warning")
					return

				artist = move_track.artist
				if move_track.album_artist:
					artist = move_track.album_artist

				artist = filename_safe(artist)

				if artist == "":
					self.show_message(_("The track needs to have an artist name."))
					return

				artist_folder = os.path.join(upper, artist)

				logging.info(f"Target will be: {artist_folder}")

				if os.path.isdir(artist_folder):
					logging.info("The target artist folder already exists")
				else:
					logging.info("Need to make artist folder")
					os.makedirs(artist_folder)

				logging.info(f"The folder to be moved is: {move_path}")
				load_order = LoadClass()
				load_order.target = os.path.join(artist_folder, move_track.parent_folder_name)
				load_order.playlist = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].uuid_int

				insert = self.gui.shift_selection[0]
				old_insert = insert
				while insert < len(self.pctl.default_playlist) and self.pctl.master_library[
					self.pctl.multi_playlist[self.pctl.active_playlist_viewing].playlist_ids[insert]].parent_folder_name == \
						self.pctl.master_library[
							self.pctl.multi_playlist[self.pctl.active_playlist_viewing].playlist_ids[old_insert]].parent_folder_name:
					insert += 1

				load_order.playlist_position = insert

				self.move_jobs.append(
					(move_path, os.path.join(artist_folder, move_track.parent_folder_name), move,
					move_track.parent_folder_name, load_order))
				self.thread_manager.ready("worker")
				# Remove all tracks with the old paths
				for pl in self.pctl.multi_playlist:
					for i in reversed(range(len(pl.playlist_ids))):
						if self.pctl.get_track(pl.playlist_ids[i]).parent_folder_path == move_track.parent_folder_path:
							del pl.playlist_ids[i]

				break
		else:
			self.show_message(_("Could not find a folder with the artist's name to match level at."))
			return

		# for file in os.listdir(artist_folder):

		if self.prefs.album_mode:
			self.prep_gal()
			self.reload_albums(True)

		self.pctl.cargo.clear()
		self.gui.lightning_copy = False

	def repair_playing_position_after_removals(self, removed_positions: list[int], playlist_index: int) -> None:
		if self.pctl.active_playlist_playing != playlist_index:
			return
		if self.pctl.playlist_playing_position < 0 or not removed_positions:
			return

		current_position = self.pctl.playlist_playing_position
		removed_positions = sorted(set(removed_positions))
		removed_before_current = sum(item < current_position for item in removed_positions)

		if current_position in removed_positions:
			self.pctl.playlist_playing_position = current_position - removed_before_current - 1
		else:
			self.pctl.playlist_playing_position = current_position - removed_before_current

		if not self.pctl.playing_playlist():
			self.pctl.playlist_playing_position = -1
		else:
			self.pctl.playlist_playing_position = max(self.pctl.playlist_playing_position, 0)
			self.pctl.playlist_playing_position = min(
				self.pctl.playlist_playing_position,
				len(self.pctl.playing_playlist()) - 1,
			)

	def del_selected(self, force_delete: bool = False) -> None:
		if self.gui.showcase_mode or self.gui.radio_view:
			return None
		self.gui.request_frame()
		self.gui.request_tracklist_redraw()

		if not self.gui.shift_selection:
			if not self.pctl.selected_ready():
				return
			self.gui.shift_selection = [self.pctl.selected_in_playlist]

		if not self.pctl.default_playlist:
			return

		li: list[tuple[int, int]] = []
		removed_positions = sorted(self.gui.shift_selection)

		for item in reversed(self.gui.shift_selection):
			if not 0 <= item < len(self.pctl.default_playlist):
				return

			li.append((item, self.pctl.default_playlist[item]))  # take note for force delete

			del self.pctl.default_playlist[item]

		self.repair_playing_position_after_removals(removed_positions, self.pctl.active_playlist_viewing)

		if force_delete:
			for item in li:
				tr = self.pctl.get_track(item[1])
				if not tr.is_network:
					try:
						send2trash(tr.fullpath)
						self.show_message(_("Tracks sent to trash"))
					except Exception:
						logging.exception("One or more tracks could not be sent to trash")
						self.show_message(_("One or more tracks could not be sent to trash"))

						if force_delete:
							try:
								os.remove(tr.fullpath)
								self.show_message(_("Files deleted"), mode="info")
							except Exception:
								logging.exception("Error deleting one or more files")
								self.show_message(_("Error deleting one or more files"), mode="error")
		else:
			self.undo.bk_tracks(self.pctl.active_playlist_viewing, li)

		self.reload()
		self.tree_view_box.clear_target_pl(self.pctl.active_playlist_viewing)

		self.pctl.selected_in_playlist = min(self.pctl.selected_in_playlist, len(self.pctl.default_playlist) - 1)

		self.gui.shift_selection = [self.pctl.selected_in_playlist]
		self.gui.request_tracklist_redraw()
		self.pctl.notify_database_changed()

	def force_del_selected(self) -> None:
		self.del_selected(force_delete=True)

	def test_show(self, _unused: MenuTrackRef) -> bool:
		return self.prefs.album_mode

	def show_in_gal(self, position: int, silent: bool = False) -> None:
		self.gui.gallery_animate_highlight_on = self.goto_album(position)
		if not silent:
			self.gallery_select_animate_timer.set()

	def menu_show_in_gal(self, ref: MenuTrackRef) -> None:
		self.show_in_gal(ref.position)

	def last_fm_test(self, _ignore) -> bool:
		return self.lastfm.connected

	def heart_xmenu_colour(self) -> ColourRGBA | None:
		if self.love(False, self.track_menu.reference.track_id):
			return ColourRGBA(245, 60, 60, 255)
		if self.colours.lm:
			return ColourRGBA(255, 150, 180, 255)
		return None

	def love_decox(self, ref: MenuTrackRef) -> Decorator:
		if self.love(False, ref.track_id):
			return Decorator(self.colours.menu_text, self.colours.menu_background, _("Un-Love Track"))
		return Decorator(self.colours.menu_text, self.colours.menu_background, _("Love Track"))

	def love_index(self, ref: MenuTrackRef) -> None:
		notify = False
		if not self.gui.show_hearts:
			notify = True

		shoot_love = threading.Thread(target=self.love, args=[True, ref.track_id, False, notify])
		shoot_love.daemon = True
		shoot_love.start()

	def add_to_queue(self, ref: MenuTrackRef) -> None:
		self.pctl.force_queue.append(queue_item_gen(ref.track_id, ref.position, ref.playlist_id))
		self.queue_timer_set()
		if self.prefs.stop_end_queue:
			self.pctl.stop_mode = StopMode.OFF

	def add_selected_to_queue(self) -> None:
		self.gui.request_tracklist_redraw()
		if self.prefs.stop_end_queue:
			self.pctl.stop_mode = StopMode.OFF
		if self.gui.album_tab_mode:
			self.add_album_to_queue(
				self.pctl.default_playlist[self.get_album_info(self.pctl.selected_in_playlist)[1][0]],
				self.pctl.selected_in_playlist,
				self.pctl.pl_to_id(self.pctl.active_playlist_viewing),
			)
			self.queue_timer_set()
		else:
			self.pctl.force_queue.append(
				queue_item_gen(self.pctl.default_playlist[self.pctl.selected_in_playlist],
				self.pctl.selected_in_playlist,
				self.pctl.pl_to_id(self.pctl.active_playlist_viewing)))
			self.queue_timer_set()

	def add_selected_to_queue_multi(self) -> None:
		if self.prefs.stop_end_queue:
			self.pctl.stop_mode = StopMode.OFF
		for index in self.gui.shift_selection:
			self.pctl.force_queue.append(
				queue_item_gen(self.pctl.default_playlist[index],
				index,
				self.pctl.pl_to_id(self.pctl.active_playlist_viewing)))

	def queue_timer_set(self, plural: bool = False, queue_object: TauonQueueItem | None = None) -> None:
		self.queue_add_timer.set()
		self.gui.frame_callback_list.append(TestTimer(2.51))
		self.gui.queue_toast_plural = plural
		if queue_object:
			self.gui.toast_queue_object = queue_object
		elif self.pctl.force_queue:
			self.gui.toast_queue_object = self.pctl.force_queue[-1]

	def split_queue_album(self, id: int) -> int | None:
		item = self.pctl.force_queue[0]

		pl = self.pctl.id_to_pl(item.playlist_id)
		if pl is None:
			return None

		playlist = self.pctl.multi_playlist[pl].playlist_ids

		i = self.pctl.playlist_playing_position + 1
		parts = []
		album_parent_path = self.pctl.get_track(item.track_id).parent_folder_path

		while i < len(playlist):
			if self.pctl.get_track(playlist[i]).parent_folder_path != album_parent_path:
				break

			parts.append((playlist[i], i))
			i += 1

		del self.pctl.force_queue[0]

		for part in reversed(parts):
			self.pctl.force_queue.insert(0, queue_item_gen(part[0], part[1], item.playlist_id, queue_type=item.type))
		return (len(parts))

	def add_to_queue_next(self, ref: MenuTrackRef) -> None:
		if self.pctl.force_queue and self.pctl.force_queue[0].album_stage == 1:
			self.split_queue_album(None)

		self.pctl.force_queue.insert(0, queue_item_gen(ref.track_id, ref.position, ref.playlist_id))

	def delete_track(self, ref: MenuTrackRef) -> None:
		tr = self.pctl.get_track(ref.track_id)
		fullpath = tr.fullpath

		if self.windows:
			fullpath = fullpath.replace("/", "\\")

		if tr.is_network:
			self.show_message(_("Cannot delete a network track"))
			return

		removed_positions = [i for i, track_id in enumerate(self.pctl.default_playlist) if track_id == ref.track_id]
		while ref.track_id in self.pctl.default_playlist:
			self.pctl.default_playlist.remove(ref.track_id)
		self.repair_playing_position_after_removals(removed_positions, self.pctl.active_playlist_viewing)

		try:
			send2trash(fullpath)

			if os.path.exists(fullpath):
				try:
					os.remove(fullpath)
					self.show_message(_("File deleted"), fullpath, mode="info")
				except Exception:
					logging.exception("Error deleting file")
					self.show_message(_("Error deleting file"), fullpath, mode="error")
			else:
				self.show_message(_("File moved to trash"))

		except Exception:
			try:
				os.remove(fullpath)
				self.show_message(_("File deleted"), fullpath, mode="info")
			except Exception:
				logging.exception("Error deleting file")
				self.show_message(_("Error deleting file"), fullpath, mode="error")

		self.reload()
		self.pctl.notify_database_changed()

	def rename_tracks_deco(self, _track_ref: MenuTrackRef) -> Decorator:
		if self.inp.key_shift_down or self.inp.key_shiftr_down:
			return Decorator(self.colours.menu_text, self.colours.menu_background, _("Rename (Single track)"))
		return Decorator(self.colours.menu_text, self.colours.menu_background, _("Rename Tracks…"))

	def activate_trans_editor(self) -> None:
		self.trans_edit_box.active = True

	def delete_folder(self, index: int, force: bool = False) -> None:
		track = self.pctl.master_library[index]

		if track.is_network:
			self.show_message(_("Cannot physically delete"), _("One or more tracks is from a network location!"), mode="info")
			return

		old = track.parent_folder_path

		if len(old) < 5:
			self.show_message(_("This folder path seems short, I don't wanna try delete that"), mode="warning")
			return

		if not os.path.exists(old):
			self.show_message(_("Error deleting folder. The folder seems to be missing."), _("It's gone! Just gone!"), mode="error")
			return

		protect = ("", "Documents", "Music", "Desktop", "Downloads")

		for fo in protect:
			if old.strip("\\/") == os.path.join(os.path.expanduser("~"), fo).strip("\\/"):
				self.show_message(_("Woah, careful there!"), _("I don't think we should delete that folder."), mode="warning")
				return

		if directory_size(old) > 1500000000:
			self.show_message(_("Delete size safety limit reached! (1.5GB)"), old, mode="warning")
			return

		try:
			if self.pctl.playing_state != PlayingState.STOPPED and os.path.normpath(
					self.pctl.master_library[self.pctl.track_queue[self.pctl.queue_step]].parent_folder_path) == os.path.normpath(old):
				self.pctl.stop(True)

			if force:
				shutil.rmtree(old)
			elif self.windows:
				send2trash(old.replace("/", "\\"))
			else:
				send2trash(old)

			for i in reversed(range(len(self.pctl.default_playlist))):

				if old == self.pctl.master_library[self.pctl.default_playlist[i]].parent_folder_path:
					del self.pctl.default_playlist[i]

			if not os.path.exists(old):
				if force:
					self.show_message(_("Folder deleted."), old, mode="done")
				else:
					self.show_message(_("Folder sent to trash."), old, mode="done")
			else:
				self.show_message(_("Hmm, its still there"), old, mode="error")

			if self.prefs.album_mode:
				self.prep_gal()
				self.reload_albums()

		except Exception:
			if force:
				logging.exception("Unable to comply, could not delete folder. Try checking permissions.")
				self.show_message(_("Unable to comply."), _("Could not delete folder. Try checking permissions."), mode="error")
			else:
				logging.exception("Folder could not be trashed, try again while holding shift to force delete.")
				self.show_message(_("Folder could not be trashed."), _("Try again while holding shift to force delete."),
					mode="error")

		self.tree_view_box.clear_target_pl(self.pctl.active_playlist_viewing)
		self.gui.request_tracklist_redraw()
		self.pctl.notify_database_changed()

	def rename_parent(self, index: int, template: str) -> None:
		# template = prefs.rename_folder_template
		template = template.strip("/\\")
		track = self.pctl.master_library[index]

		if track.is_network:
			self.show_message(_("Cannot rename"), _("One or more tracks is from a network location!"), mode="info")
			return

		old = track.parent_folder_path
		#logging.info(old)

		new = parse_template2(template, track)

		if len(new) < 1:
			self.show_message(_("Rename error."), _("The generated name is too short"), mode="warning")
			return

		if len(old) < 5:
			self.show_message(_("Rename error."), _("This folder path seems short, I don't wanna try rename that"), mode="warning")
			return

		if not os.path.exists(old):
			self.show_message(_("Rename Failed. The original folder is missing."), mode="warning")
			return

		protect = ("", "Documents", "Music", "Desktop", "Downloads")

		for fo in protect:
			if os.path.normpath(old) == os.path.normpath(os.path.join(os.path.expanduser("~"), fo)):
				self.show_message(_("Woah, careful there!"), _("I don't think we should rename that folder."), mode="warning")
				return

		logging.info(track.parent_folder_path)
		re = os.path.dirname(track.parent_folder_path.rstrip("/\\"))
		logging.info(re)
		new_parent_path = os.path.join(re, new)
		logging.info(new_parent_path)

		if os.path.normpath(new_parent_path) == os.path.normpath(old):
			self.show_message(_("The folder already has that name."))
			return

		if os.path.exists(new_parent_path):
			self.show_message(_("Rename Failed."), _("A folder with that name already exists"), mode="warning")
			return

		def path_contains(parent: str, child: str) -> bool:
			try:
				parent = os.path.normpath(parent)
				child = os.path.normpath(child)
				return child != parent and os.path.commonpath([parent, child]) == parent
			except ValueError:
				return False

		pre_state = 0
		affected_tracks: list[tuple[int, TrackClass, str, str, str]] = []

		for key, track_object in self.pctl.master_library.items():
			if track_object.fullpath == "":
				continue

			if old == track_object.parent_folder_path:
				new_fullpath = os.path.join(new_parent_path, track_object.filename)
				affected_tracks.append((key, track_object, new, new_parent_path, new_fullpath))

			# Fix any other tracks paths that contain the old path
			elif path_contains(old, track_object.fullpath):
				new_fullpath = os.path.join(new_parent_path, os.path.relpath(track_object.fullpath, old))
				new_folder_path = os.path.join(new_parent_path, os.path.relpath(track_object.parent_folder_path, old))
				affected_tracks.append((
					key,
					track_object,
					track_object.parent_folder_name,
					new_folder_path,
					new_fullpath,
				))

		if self.pctl.playing_state != PlayingState.STOPPED and self.pctl.track_queue:
			playing_track = self.pctl.track_queue[self.pctl.queue_step]
			if any(key == playing_track for key, *_unused in affected_tracks):
				pre_state = self.pctl.stop(True)

		try:
			os.rename(old, new_parent_path)
			logging.info(new_parent_path)
		except Exception:
			logging.exception("Rename failed, something went wrong!")
			self.show_message(_("Rename Failed!"), _("Something went wrong, sorry."), mode="error")
			if pre_state == 1:
				self.pctl.revert()
			return

		for key, track_object, parent_folder_name, parent_folder_path, fullpath in affected_tracks:
			track_object.parent_folder_name = parent_folder_name
			track_object.parent_folder_path = parent_folder_path
			track_object.fullpath = fullpath

			self.search_string_cache.pop(key, None)
			self.search_dia_string_cache.pop(key, None)
			self.search_field_cache.pop(key, None)
			self.search_dia_field_cache.pop(key, None)

		self.show_message(_("Folder renamed."), _("Renamed to: {name}").format(name=new), mode="done")

		if pre_state == 1:
			self.pctl.revert()

		self.tree_view_box.clear_target_pl(self.pctl.active_playlist_viewing)
		self.pctl.notify_database_changed()

	def rename_folders_disable_test(self, ref: MenuTrackRef) -> bool:
		return self.pctl.get_track(ref.track_id).is_network

	def rename_folders(self, ref: MenuTrackRef) -> None:
		track_id = ref.track_id
		self.gui.track_box = False
		self.gui.rename_index = track_id

		if self.rename_folders_disable_test(ref):
			self.show_message(_("Not applicable for a network track."))
			return

		self.gui.rename_folder_box = True
		self.inp.input_text = ""
		self.gui.shift_selection.clear()

		self.inp.quick_drag = False
		self.gui.playlist_hold = False

	def move_folder_up(self, index: int, do: bool = False) -> bool | None:
		track = self.pctl.master_library[index]

		if track.is_network:
			self.show_message(_("Cannot move"), _("One or more tracks is from a network location!"), mode="info")
			return None

		parent_folder = os.path.dirname(track.parent_folder_path)
		folder_name = track.parent_folder_name
		move_target = track.parent_folder_path
		upper_folder = os.path.dirname(parent_folder)

		if not os.path.exists(track.parent_folder_path):
			if do:
				self.show_message(_("Error shifting directory"), _("The directory does not appear to exist"), mode="warning")
			return False

		if len(os.listdir(parent_folder)) > 1:
			return False

		if do is False:
			return True

		pre_state = 0
		if self.pctl.playing_state != PlayingState.STOPPED and track.parent_folder_path in self.pctl.playing_object().parent_folder_path:
			pre_state = self.pctl.stop(True)

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
			self.show_message(_("System Error!"), str(e), mode="error")

		# Fix any other tracks paths that contain the old path
		old = track.parent_folder_path
		new_parent_path = os.path.join(upper_folder, folder_name)
		for key, object in self.pctl.master_library.items():
			if os.path.normpath(object.fullpath)[:len(old)] == os.path.normpath(old) \
					and os.path.normpath(object.fullpath)[len(old)] in ("/", "\\"):
				object.fullpath = os.path.join(new_parent_path, object.fullpath[len(old):].lstrip("\\/"))
				object.parent_folder_path = os.path.join(
					new_parent_path, object.parent_folder_path[len(old):].lstrip("\\/"))

				self.search_string_cache.pop(object.index, None)
				self.search_dia_string_cache.pop(object.index, None)
				self.search_field_cache.pop(object.index, None)
				self.search_dia_field_cache.pop(object.index, None)

				logging.info(object.fullpath)
				logging.info(object.parent_folder_path)

		if pre_state == 1:
			self.pctl.revert()
		return None

	def clean_folder(self, index: int, do: bool = False) -> int | None:
		track = self.pctl.master_library[index]

		if track.is_network:
			self.show_message(_("Cannot clean"), _("One or more tracks is from a network location!"), mode="info")
			return None

		folder = track.parent_folder_path
		found = 0
		to_purge = []
		if not os.path.isdir(folder):
			return 0
		try:
			for item in os.listdir(folder):
				if (item[:8] == "AlbumArt" and ".jpg" in item.lower()) or item in ("desktop.ini", "Thumbs.db", ".DS_Store"):

					to_purge.append(item)
					found += 1
				elif item == "__MACOSX" and os.path.isdir(os.path.join(folder, item)):
					found += 1
					found += 1
					if do:
						logging.info(f"Deleting Folder: {os.path.join(folder, item)}")
						shutil.rmtree(os.path.join(folder, item))

			if do:
				for item in to_purge:
					if os.path.isfile(os.path.join(folder, item)):
						logging.info(f"Deleting File: {os.path.join(folder, item)}")
						os.remove(os.path.join(folder, item))
				# self.clear_img_cache()

				for track_id in self.pctl.default_playlist:
					if self.pctl.get_track(track_id).parent_folder_path == folder:
						self.clear_track_image_cache(self.pctl.get_track(track_id))

		except Exception:
			logging.exception("Error deleting files, may not have permission or file may be set to read-only")
			self.show_message(_("Error deleting files."), _("May not have permission or file may be set to read-only"), mode="warning")
			return 0

		return found

	def reset_play_count(self, index: int) -> None:
		self.star_store.remove(index)

	def vacuum_playtimes(self, ref: MenuTrackRef) -> None:
		track_id = ref.track_id
		todo = []
		for k in self.pctl.default_playlist:
			if self.pctl.master_library[track_id].parent_folder_name == self.pctl.master_library[k].parent_folder_name:
				todo.append(k)

		for track in todo:
			tr = self.pctl.get_track(track)

			total_playtime = 0
			flags = ""

			to_del = []

			for key, value in self.star_store.db.items():
				if key[0].lower() == tr.artist.lower() and tr.artist and key[1].lower().replace(
					" ", "") == tr.title.lower().replace(
					" ", "") and tr.title:
					to_del.append(key)
					total_playtime += value.playtime

			for key in to_del:
				del self.star_store.db[key]

			key = self.star_store.object_key(tr)
			value = StarRecord(playtime=total_playtime)
			if key not in self.star_store.db:
				logging.info("Saving value")
				self.star_store.db[key] = value
			else:
				logging.error("KEY ALREADY HERE?")

	def intel_moji(self, ref: MenuTrackRef) -> None:
		self.gui.request_tracklist_redraw()
		self.gui.request_frame()

		index = ref.track_id
		track = self.pctl.master_library[index]
		lot = []

		for item in self.pctl.default_playlist:
			if track.album == self.pctl.master_library[item].album and \
					track.parent_folder_name == self.pctl.master_library[item].parent_folder_name:
				lot.append(item)

		lot = set(lot)

		l_artist = track.artist.encode("Latin-1", "ignore")
		l_album = track.album.encode("Latin-1", "ignore")
		detect = None

		if track.artist not in track.parent_folder_path:
			for enc in self.encodings:
				try:
					q_artist = l_artist.decode(enc)
					if q_artist.strip(" ") in track.parent_folder_path.strip(" "):
						detect = enc
						break
				except Exception:
					logging.exception("Error decoding artist")
					continue

		if detect is None and track.album not in track.parent_folder_path:
			for enc in self.encodings:
				try:
					q_album = l_album.decode(enc)
					if q_album in track.parent_folder_path:
						detect = enc
						break
				except Exception:
					logging.exception("Error decoding album")
					continue

		for item in lot:
			t_track = self.pctl.master_library[item]

			if detect is None:
				for enc in self.encodings:
					test = recode(t_track.artist, enc)
					for cha in test:
						if cha in j_chars:
							detect = enc
							logging.info(f"This looks like Japanese: {test}")
							break
						if detect is not None:
							break

			if detect is None:
				for enc in self.encodings:
					test = recode(t_track.title, enc)
					for cha in test:
						if cha in j_chars:
							detect = enc
							logging.info(f"This looks like Japanese: {test}")
							break
						if detect is not None:
							break
			if detect is not None:
				break

		if detect is not None:
			logging.info(f"Fix Mojibake: Detected encoding as: {detect}")
			for item in lot:
				track = self.pctl.master_library[item]
				# key = self.pctl.master_library[item].title + self.pctl.master_library[item].filename
				key = self.star_store.full_get(item)
				self.star_store.remove(item)

				track.title = recode(track.title, detect)
				track.album = recode(track.album, detect)
				track.artist = recode(track.artist, detect)
				track.album_artist = recode(track.album_artist, detect)
				track.genre = recode(track.genre, detect)
				track.comment = recode(track.comment, detect)
				track.lyrics = recode(track.lyrics, detect)

				if key is not None:
					self.star_store.insert(item, key)

				self.search_string_cache.pop(track.index, None)
				self.search_dia_string_cache.pop(track.index, None)
				self.search_field_cache.pop(track.index, None)
				self.search_dia_field_cache.pop(track.index, None)
		else:
			self.show_message(_("Autodetect failed"))

	def sel_to_car(self) -> None:
		self.pctl.cargo = []

		for item in self.gui.shift_selection:
			self.pctl.cargo.append(self.pctl.default_playlist[item])

	def cut_selection(self) -> None:
		self.sel_to_car()
		self.del_selected()

	def clip_ar_al(self, index: int) -> None:
		line = self.pctl.master_library[index].artist + " - " + self.pctl.master_library[index].album
		sdl3.SDL_SetClipboardText(line.encode("utf-8"))

	def clip_ar(self, index: int) -> None:
		if self.pctl.master_library[index].album_artist:
			line = self.pctl.master_library[index].album_artist
		else:
			line = self.pctl.master_library[index].artist
		sdl3.SDL_SetClipboardText(line.encode("utf-8"))

	def clip_title(self, ref: MenuTrackRef) -> None:
		n_track = self.pctl.get_track(ref.track_id)

		if not self.prefs.use_title and n_track.album_artist and n_track.album:
			line = n_track.album_artist + " - " + n_track.album
		else:
			line = n_track.parent_folder_name
		sdl3.SDL_SetClipboardText(line.encode("utf-8"))

	def lightning_copy(self) -> None:
		self.s_copy()
		self.gui.lightning_copy = True

	def transcode_deco(self) -> Decorator:
		if self.inp.key_shift_down or self.inp.key_shiftr_down:
			return Decorator(self.colours.menu_text, self.colours.menu_background, _("Transcode Single"))
		return Decorator(self.colours.menu_text, self.colours.menu_background, _("Transcode Folder"))

	def selection_queue_deco(self) -> Decorator:
		total = 0
		for item in self.gui.shift_selection:
			total += self.pctl.get_track(self.pctl.default_playlist[item]).length

		total = get_hms_time(total)
		text = (_("Queue {N}").format(N=len(self.gui.shift_selection))) + f" [{total}]"
		return Decorator(self.colours.menu_text, self.colours.menu_background, text)

	def ser_band_done(self, result: str) -> None:
		if result:
			webbrowser.open(result, new=2, autoraise=True)
			self.gui.message_box = False
			self.gui.request_frame()
		else:
			self.show_message(_("No matching artist result found"))

	def ser_band(self, ref: MenuTrackRef) -> None:
		tr = self.pctl.get_track(ref.track_id)
		if tr.artist:
			shoot_dl = threading.Thread(target=bandcamp_search, args=([tr.artist, self.ser_band_done]))
			shoot_dl.daemon = True
			shoot_dl.start()
			self.show_message(_("Searching..."))

	def ser_rym(self, ref: MenuTrackRef) -> None:
		index = ref.track_id
		if len(self.pctl.master_library[index].artist) < 2:
			return
		line = "https://rateyourmusic.com/search?searchtype=a&searchterm=" + urllib.parse.quote(
			self.pctl.master_library[index].artist)
		webbrowser.open(line, new=2, autoraise=True)

	def vis_off(self) -> None:
		self.gui.vis_want = 0
		self.gui.update_layout = True
		# self.gui.turbo = False

	def level_on(self) -> None:
		if self.gui.vis_want == 1 and self.gui.turbo is True:
			self.gui.level_meter_colour_mode += 1
			if self.gui.level_meter_colour_mode > 4:
				self.gui.level_meter_colour_mode = 0

		self.gui.vis_want = 1
		self.gui.update_layout = True
		# if self.prefs.backend == Backend.GSTREAMER:
		# 	self.show_message("Visualisers not implemented in GStreamer mode")
		# self.gui.turbo = True

	def spec_on(self) -> None:
		self.gui.vis_want = 2
		# if self.prefs.backend == Backend.GSTREAMER:
		# 	self.show_message("Not implemented")
		self.gui.update_layout = True

	def spec2_def(self) -> None:
		if self.gui.vis_want == 3:
			self.prefs.spec2_colour_mode += 1
			if self.prefs.spec2_colour_mode > 1:
				self.prefs.spec2_colour_mode = 0

		self.gui.vis_want = 3
		if self.prefs.backend == Backend.GSTREAMER:
			self.show_message(_("Not implemented"))
		# self.gui.turbo = True
		self.prefs.spec2_colour_setting = "custom"
		self.gui.update_layout = True

	def sa_regen_menu(self) -> None:
		"""Recreate the column select menu to correctly populate the checkbox state"""
		set_menu = self.set_menu
		set_menu.subs = []
		set_menu.sub_number = 0
		set_menu.items = []
		checked = set()
		fields = [
			[_("Artist"),"Artist", self.sa_artist],
			[_("Title"), "Title", self.sa_title],
			[_("Album"), "Album", self.sa_album],
			[_("Album Art"), "Album Art", self.sa_album_art],
			[_("Duration"), "Time", self.sa_time],
			[_("Date"), "Date", self.sa_date],
			[_("Genre"), "Genre", self.sa_genre],
			[_("Track Number"), "#", self.sa_track],
			[_("Play Count"), "P", self.sa_count],
			[_("Codec"), "Codec", self.sa_codec],
			[_("Bitrate"), "Bitrate", self.sa_bitrate],
			[_("Filename"), "Filename", self.sa_filename],
			[_("Starline"), "Starline", self.sa_star],
			[_("Rating"), "Rating", self.sa_rating],
			[_("Loved"), "❤", self.sa_love],
			[_("Album Artist"), "Album Artist", self.sa_album_artist],
			[_("Comment"), "Comment", self.sa_comment],
			[_("Filepath"), "Filepath", self.sa_file],
			[_("Scrobble Count"), "S", self.sa_scrobbles],
			[_("Composer"), "Composer", self.sa_composer],
			[_("Disc Number"), "Disc", self.sa_disc],
			[_("Has Lyrics"), "Lyrics", self.sa_lyrics],
			[_("Is CUE Sheet"), "CUE", self.sa_cue],
			[_("Internal Track ID"), "ID", self.sa_track_id],
			[_("File Changed"), "=/=", self.sa_modify_date],
		]
		for checked_column in self.gui.pl_st:
			checked.add( checked_column[0] )

		set_menu.add(MenuItem(_("Auto Resize"), self.auto_size_columns))
		set_menu.add(MenuItem(_("Hide bar"), self.hide_set_bar))
		# Magnet Mode: draw the next column's text immediately after this column's
		# text (packed left, standard-layout style) instead of confining it to its
		# own column. Only meaningful when there is a column to the right.
		set_menu.add(MenuItem(_("Enable Magnet Mode"), self.sa_toggle_magnet, pass_ref=True, show_test=self.sa_magnet_off_test))
		set_menu.add(MenuItem(_("Disable Magnet Mode"), self.sa_toggle_magnet, pass_ref=True, show_test=self.sa_magnet_on_test))
		set_menu.br()
		set_menu.add(MenuItem("- " + _("Remove This"), self.sa_remove, pass_ref=True))
		set_menu.br()

		for i, c in enumerate(fields):
			# The menu is rebuilt on each activation, so the column state can
			# be captured at build time.
			item = MenuItem(c[0], c[2], check_test=(lambda on=(c[1] in checked): on))
			if i < 14:
				set_menu.add(item)
			if i == 14:
				set_menu.add_sub("+ " + _("More…"), 150)
			if i >= 14:
				set_menu.add_to_sub(0, item)


	def sa_remove(self, h: int) -> None:
		if len(self.gui.pl_st) > 1:
			del self.gui.pl_st[h]
			self.gui.update_layout = True
			self.sa_regen_menu()
		else:
			self.show_message(_("Cannot remove the only column."))

	def sa_magnet_eligible(self, ref: object) -> bool:
		"""A column can hold magnet mode only if there is a column to its right."""
		return isinstance(ref, int) and 0 <= ref < len(self.gui.pl_st) - 1

	def sa_magnet_is_on(self, ref: object) -> bool:
		if not self.sa_magnet_eligible(ref):
			return False
		item = self.gui.pl_st[ref]
		return len(item) > 3 and bool(item[3])

	def sa_magnet_off_test(self, ref: object) -> bool:
		return self.sa_magnet_eligible(ref) and not self.sa_magnet_is_on(ref)

	def sa_magnet_on_test(self, ref: object) -> bool:
		return self.sa_magnet_is_on(ref)

	def sa_toggle_magnet(self, ref: int) -> None:
		if not self.sa_magnet_eligible(ref):
			return
		item = self.gui.pl_st[ref]
		while len(item) < 4:
			item.append(False)
		item[3] = not item[3]
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_try_uncheck(self, field: str) -> bool:
		unchecks = [] # you could have multiple copies of the same column
		for i, column in enumerate(self.gui.pl_st):
			if column[0] == field:
				unchecks.append(i)
		unchecks.reverse()
		for column in unchecks:
			self.sa_remove(column)
		return bool(unchecks)

	def sa_artist(self) -> None:
		if not self.sa_try_uncheck("Artist"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Artist", 220, False])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_album_artist(self) -> None:
		if not self.sa_try_uncheck("Album Artist"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Album Artist", 220, False])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_composer(self) -> None:
		if not self.sa_try_uncheck("Composer"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Composer", 220, False])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_title(self) -> None:
		if not self.sa_try_uncheck("Title"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Title", 220, False])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_album(self) -> None:
		if not self.sa_try_uncheck("Album"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Album", 220, False])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_album_art(self) -> None:
		if not self.sa_try_uncheck("Album Art"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Album Art", 140, False])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_comment(self) -> None:
		if not self.sa_try_uncheck("Comment"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Comment", 300, False])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_track(self) -> None:
		if not self.sa_try_uncheck("#"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["#", 25, True])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_count(self) -> None:
		if not self.sa_try_uncheck("P"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["P", 25, True])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_scrobbles(self) -> None:
		if not self.sa_try_uncheck("S"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["S", 25, True])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_time(self) -> None:
		if not self.sa_try_uncheck("Time"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Time", 55, True])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_date(self) -> None:
		if not self.sa_try_uncheck("Date"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Date", 95, True])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_genre(self) -> None:
		if not self.sa_try_uncheck("Genre"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Genre", 150, False])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_file(self) -> None:
		if not self.sa_try_uncheck("Filepath"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Filepath", 350, False])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_filename(self) -> None:
		if not self.sa_try_uncheck("Filename"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Filename", 300, False])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_codec(self) -> None:
		if not self.sa_try_uncheck("Codec"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Codec", 65, True])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_bitrate(self) -> None:
		if not self.sa_try_uncheck("Bitrate"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Bitrate", 65, True])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_lyrics(self) -> None:
		if not self.sa_try_uncheck("Lyrics"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Lyrics", 50, True])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_cue(self) -> None:
		if not self.sa_try_uncheck("CUE"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["CUE", 50, True])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_star(self) -> None:
		if not self.sa_try_uncheck("Starline"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Starline", 80, True])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_disc(self) -> None:
		if not self.sa_try_uncheck("Disc"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Disc", 50, True])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_rating(self) -> None:
		if not self.sa_try_uncheck("Rating"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["Rating", 80, True])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_love(self) -> None:
		if not self.sa_try_uncheck("❤"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["❤", 25, True])
		# self.gui.pl_st.append(["❤", 25, True])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_track_id(self) -> None:
		if not self.sa_try_uncheck("ID"):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["ID", 55, True])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def sa_modify_date(self) -> None:
		if not self.sa_try_uncheck("=/="):
			self.gui.pl_st.insert(self.set_menu.reference + 1, ["=/=", 65, True])
		self.gui.update_layout = True
		self.sa_regen_menu()

	def key_love(self, index: int) -> bool:
		return self.get_love_index(index)

	def key_artist(self, index: int) -> str:
		return self.pctl.master_library[index].artist.lower()

	def key_album_artist(self, index: int) -> str:
		return self.pctl.master_library[index].album_artist.lower()

	def key_composer(self, index: int) -> str:
		return self.pctl.master_library[index].composer.lower()

	def key_comment(self, index: int) -> str:
		return self.pctl.master_library[index].comment

	def key_title(self, index: int) -> str:
		return self.pctl.master_library[index].title.lower()

	def key_album(self, index: int) -> str:
		return self.pctl.master_library[index].album.lower()

	def key_duration(self, index: int) -> float:
		return self.pctl.master_library[index].length

	def key_date(self, index: int) -> str:
		return self.pctl.master_library[index].date

	def key_genre(self, index: int) -> str:
		return self.pctl.master_library[index].genre.lower()

	def key_t(self, index: int) -> list[int | str] | Literal["a"]:
		# return str(self.pctl.master_library[index].track_number)
		return self.pctl.index_key(index)

	def key_codec(self, index: int) -> str:
		return self.pctl.master_library[index].file_ext

	def key_bitrate(self, index: int) -> int:
		return self.pctl.master_library[index].bitrate

	def key_hl(self, index: int) -> int:
		if len(self.pctl.master_library[index].lyrics) > 5:
			return 0
		return 1

	def key_modify_date(self, index: int) -> float:
		return self.pctl.master_library[index].modified_time

	def sort_dec(self, h: int) -> None:
		self.sort_ass(h, True)

	def sort_ass(self, h: int, invert: bool = False, custom_list: list[int] | None = None, custom_name: str = "") -> None:
		if custom_list is None:
			if self.pl_is_locked(self.pctl.active_playlist_viewing):
				self.show_message(_("Playlist is locked"))
				return

			name = self.gui.pl_st[h][0]
			playlist = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].playlist_ids
		else:
			name = custom_name
			playlist = custom_list

		key = None
		ns = False

		if self.use_natsort:
			natsort = sys.modules.get("natsort")  # Fetch from loaded modules

		if name == "Filepath":
			key = self.key_filepath
			if self.use_natsort:
				key = self.key_fullpath
				ns = True
		if name == "Filename":
			key = self.key_filepath  # self.key_filename
			if self.use_natsort:
				key = self.key_fullpath
				ns = True
		if name == "Artist":
			key = self.key_artist
		if name == "Album Artist":
			key = self.key_album_artist
		if name == "Title":
			key = self.key_title
		if name == "Album":
			key = self.key_album
		if name == "Composer":
			key = self.key_composer
		if name == "Time":
			key = self.key_duration
		if name == "Date":
			key = self.key_date
		if name == "Genre":
			key = self.key_genre
		if name == "#":
			key = self.key_t
		if name == "S":
			key = self.key_scrobbles
		if name == "P":
			key = self.key_playcount
		if name == "Starline":
			key = self.best
		if name == "Rating":
			key = self.key_rating
		if name == "Comment":
			key = self.key_comment
		if name == "Codec":
			key = self.key_codec
		if name == "Bitrate":
			key = self.key_bitrate
		if name == "Lyrics":
			key = self.key_hl
		if name == "❤":
			key = self.key_love
		if name == "Disc":
			key = self.key_disc
		if name == "CUE":
			key = self.key_cue
		if name == "ID":
			key = self.key_track_id
		if name == "=/=":
			key = self.key_modify_date

		if custom_list is None:
			if key is not None:
				if ns:
					key = natsort.natsort_keygen(key=key, alg=natsort.PATH|natsort.U|natsort.I)

				playlist.sort(key=key, reverse=invert)

				self.pctl.multi_playlist[self.pctl.active_playlist_viewing].playlist_ids = playlist
				self.pctl.default_playlist = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].playlist_ids

				self.pctl.playlist_view_position = 0
				logging.debug("Position changed by sort")
				self.gui.request_tracklist_redraw()
		elif custom_list is not None:
			playlist.sort(key=key, reverse=invert)
		self.reload()

	def stt2(self, sec: int) -> str:
		"""Converts seconds into days hours minutes"""
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

	def export_database(self) -> None:
		path = self.user_directory / "DatabaseExport.csv"
		xport = path.open("w", encoding="utf-8")

		xport.write("Artist,Title,Album,Album artist,Track number,Type,Duration,Release date,Genre,Playtime,File path")

		for index, track in self.pctl.master_library.items():
			xport.write("\n")
			xport.write(csv_string(track.artist) + ",")
			xport.write(csv_string(track.title) + ",")
			xport.write(csv_string(track.album) + ",")
			xport.write(csv_string(track.album_artist) + ",")
			xport.write(csv_string(track.track_number) + ",")
			track_type = "File"
			if track.is_network:
				track_type = "Network"
			elif track.is_cue:
				track_type = "CUE File"
			xport.write(track_type + ",")
			xport.write(str(track.length) + ",")
			xport.write(csv_string(track.date) + ",")
			xport.write(csv_string(track.genre) + ",")
			xport.write(str(int(self.star_store.get_by_object(track))) + ",")
			xport.write(csv_string(track.fullpath))

		xport.close()
		self.show_message(_("Export complete."), _("Saved as: ") + str(path), mode="done")

	def q_to_playlist(self) -> None:
		self.pctl.multi_playlist.append(self.pl_gen(
			title=_("Play History"),
			playing=0,
			playlist_ids=list(reversed(copy.deepcopy(self.pctl.track_queue))),
			position=0,
			hide_title=True,
			selected=0))

	def clean_db(self) -> None:
		self.prefs.remove_network_tracks = False
		self.cm_clean_db = True
		self.thread_manager.ready("worker")

	def clean_db2(self) -> None:
		self.prefs.remove_network_tracks = True
		self.cm_clean_db = True
		self.thread_manager.ready("worker")

	def import_fmps(self) -> None:
		"""FMPS spec: https://gitorious.org/xdg-specs/xdg-specs/trees/master/specifications/FMPSpecs?p=xdg-specs:xdg-specs.git;a=blob;f=specifications/FMPSpecs/specification.txt;hb=HEAD#l235"""
		unique = set()
		for playlist in self.pctl.multi_playlist:
			for id in playlist.playlist_ids:
				tr = self.pctl.get_track(id)
				if tr.FMPS_Rating is not None:
					if tr.FMPS_Rating > 1 or tr.FMPS_Rating < 0:
						logging.warning(f"Nonstandard FMPS_RATING in track, skipping {tr.fullpath}: {tr.FMPS_Rating}")
						continue
					rating = round(tr.FMPS_Rating * 10)
					self.star_store.set_rating(tr.index, rating)
					unique.add(tr.index)

		self.show_message(_("{N} ratings imported").format(N=str(len(unique))), mode="done")

		self.gui.request_tracklist_redraw()

	def import_popm(self) -> None:
		unique = set()
		skipped = set()
		for playlist in self.pctl.multi_playlist:
			for id in playlist.playlist_ids:
				tr = self.pctl.get_track(id)
				if tr.POPM is not None:
					rating = tr.POPM
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

					if self.star_store.get_rating(tr.index) == 0:
						self.star_store.set_rating(tr.index, t_rating)
						unique.add(tr.index)
					else:
						logging.info("Won't import POPM because track is already rated")
						skipped.add(tr.index)

		s = str(len(unique)) + " ratings imported"
		if len(skipped) > 0:
			s += f", {len(skipped)} skipped"
		self.show_message(s, mode="done")

		self.gui.request_tracklist_redraw()

	def clear_ratings(self) -> None:
		if not self.inp.key_shift_down:
			self.show_message(
				_("This will delete all track and album ratings from the local database!"),
				_("Press button again while holding shift key if you're sure you want to do that."),
				mode="warning")
			return
		for key, star in self.star_store.db.items():
			star.rating = 0
		self.album_star_store.db.clear()
		self.gui.request_tracklist_redraw()

	def find_incomplete(self) -> None:
		self.gen_incomplete(self.pctl.active_playlist_viewing)

	def cast_deco(self) -> Decorator:
		line_colour = self.colours.menu_text
		if self.chrome_mode:
			return Decorator(line_colour, self.colours.menu_background, _("Stop Cast"))  # [24, 25, 60, 255]
		return Decorator(line_colour, self.colours.menu_background, None)

	def cast_search2(self) -> None:
		self.chrome.rescan()

	def cast_search(self) -> None:
		if self.chrome_mode:
			self.pctl.stop()
			self.chrome.end()
		else:
			if not self.chrome:
				self.show_message(_("pychromecast not found"))
				return
			self.show_message(_("Searching for Chromecasts..."))
			shooter(self.cast_search2)

	def clear_queue(self) -> None:
		self.pctl.force_queue = []
		self.gui.request_tracklist_redraw()
		self.pctl.pause_queue = False

	def set_mini_mode_A1(self) -> None:
		self.prefs.mini_mode_mode = MiniModeMode.MINI
		self.set_mini_mode()

	def set_mini_mode_B1(self) -> None:
		self.prefs.mini_mode_mode = MiniModeMode.SQUARE
		self.set_mini_mode()

	def set_mini_mode_A2(self) -> None:
		self.prefs.mini_mode_mode = MiniModeMode.LARGE
		self.set_mini_mode()

	def set_mini_mode_C1(self) -> None:
		self.prefs.mini_mode_mode = MiniModeMode.SLATE
		self.set_mini_mode()

	def set_mini_mode_B2(self) -> None:
		self.prefs.mini_mode_mode = MiniModeMode.SQUARE_LARGE
		self.set_mini_mode()

	def set_mini_mode_D(self) -> None:
		self.prefs.mini_mode_mode = MiniModeMode.TAB
		self.set_mini_mode()

	def set_mini_mode_E(self) -> None:
		self.prefs.mini_mode_mode = MiniModeMode.SIGNAL
		self.set_mini_mode()

	def copy_bb_metadata(self) -> str | None:
		tr = self.pctl.playing_object()
		if tr is None:
			return None
		if not tr.title and not tr.artist and self.pctl.playing_state == PlayingState.URL_STREAM:
			return self.pctl.tag_meta
		text = f"{tr.artist} - {tr.title}".strip(" -")
		if text:
			copy_to_clipboard(text)
		else:
			self.show_message(_("No metadata available to copy"))
		return None

	def stop(self) -> None:
		self.pctl.stop()

	def stop_mode_off(self) -> None:
		self.pctl.stop_mode = StopMode.OFF
		self.pctl.stop_ref = None

	def stop_mode_track(self) -> None:
		self.pctl.stop_mode = StopMode.TRACK
		self.pctl.stop_ref = None

	def stop_mode_album(self) -> None:
		self.pctl.stop_mode = StopMode.ALBUM

	def stop_mode_track_persist(self) -> None:
		self.pctl.stop_mode = StopMode.TRACK_PERSIST
		self.pctl.stop_ref = None

	def stop_mode_album_persist(self) -> None:
		tr = self.pctl.playing_object()
		if tr:
			self.pctl.stop_mode = StopMode.ALBUM_PERSIST
			self.pctl.stop_ref = (tr.parent_folder_path, tr.album)

	def random_track(self) -> None:
		playlist = self.pctl.multi_playlist[self.pctl.active_playlist_playing].playlist_ids
		if playlist:
			random_position = random.randrange(0, len(playlist))
			track_id = playlist[random_position]
			self.pctl.jump(track_id, random_position)
			self.pctl.show_current()

	def random_album(self) -> None:
		folders = {}
		playlist = self.pctl.multi_playlist[self.pctl.active_playlist_playing].playlist_ids
		if playlist:
			for i, id in enumerate(playlist):
				track = self.pctl.get_track(id)
				if track.parent_folder_path not in folders:
					folders[track.parent_folder_path] = (id, i)

			key = random.choice(list(folders.keys()))
			result = folders[key]
			self.pctl.jump(*result)
			self.pctl.show_current()

	def radio_random(self) -> None:
		self.pctl.advance(rr=True)

	def heart_menu_colour(self) -> ColourRGBA | None:
		if self.pctl.playing_state not in (PlayingState.PLAYING, PlayingState.PAUSED):
			if self.colours.lm:
				return ColourRGBA(255, 150, 180, 255)
			return None
		if self.love(False):
			return ColourRGBA(245, 60, 60, 255)
		if self.colours.lm:
			return ColourRGBA(255, 150, 180, 255)
		return None

	def activate_search_overlay(self) -> None:
		if self.cm_clean_db:
			self.show_message(_("Please wait for cleaning process to finish"))
			return
		self.search_over.active = True
		self.search_over.delay_enter = False
		self.search_over.search_text.selection = 0
		self.search_over.search_text.cursor_position = 0

	def goto_playing_extra(self) -> None:
		self.pctl.show_current(highlight=True)

	def level_meter_special_2(self) -> None:
		self.gui.level_meter_colour_mode = 2

	def last_fm_menu_deco(self) -> Decorator:
		if self.prefs.scrobble_hold:
			if not self.prefs.auto_lfm and self.lb.enable:
				line = _("ListenBrainz is Paused")
			else:
				line = _("Scrobbling is Paused")
			bg = self.colours.menu_background
		else:
			if not self.prefs.auto_lfm and self.lb.enable:
				line = _("ListenBrainz is Active")
			else:
				line = _("Scrobbling is Active")

			bg = self.colours.menu_background
		return Decorator(self.colours.menu_text, bg, line)

	def lastfm_colour(self) -> ColourRGBA | None:
		if not self.prefs.scrobble_hold:
			return ColourRGBA(250, 50, 50, 255)
		return None

	def lastfm_menu_test(self, _unused: int) -> bool:
		return bool((self.prefs.auto_lfm and self.prefs.last_fm_token is not None) or self.prefs.enable_lb or self.prefs.maloja_enable)

	def lb_mode(self) -> bool:
		return self.prefs.enable_lb

	def get_album_art_url(self, tr: TrackClass) -> str | None:
		artist = tr.album_artist
		if not tr.album:
			return None
		if not artist:
			artist = tr.artist
		if not artist:
			return None

		# Embedded MBIDs are the most accurate source, check first
		release_id = tr.musicbrainz_albumid
		release_group_id = tr.musicbrainz_releasegroupid
		had_embedded_mbid = bool(release_id or release_group_id)

		# If no embedded MBIDs, fall back to the name-based cache
		if not had_embedded_mbid:
			cache_key = (artist, tr.album)
			if cache_key in self.pctl.album_mbid_release_cache or cache_key in self.pctl.album_mbid_release_group_cache:
				release_id = self.pctl.album_mbid_release_cache.get(cache_key)
				release_group_id = self.pctl.album_mbid_release_group_cache.get(cache_key)
				if release_id is None and release_group_id is None:
					return None

		if not release_group_id:
			try:
				s = musicbrainzngs.search_release_groups(tr.album, artist=artist, limit=1)
				release_group_id = s["release-group-list"][0]["id"]
				tr.musicbrainz_releasegroupid = release_group_id
			except Exception:
				logging.exception("Error lookup mbid for discord")
				if not had_embedded_mbid:
					self.pctl.album_mbid_release_group_cache[(artist, tr.album)] = None

		if not release_id:
			try:
				s = musicbrainzngs.search_releases(tr.album, artist=artist, limit=1)
				release_id = s["release-list"][0]["id"]
				tr.musicbrainz_albumid = release_id
			except Exception:
				logging.exception("Error lookup mbid for discord")
				if not had_embedded_mbid:
					self.pctl.album_mbid_release_cache[(artist, tr.album)] = None

		image_data = None
		final_id = None
		if release_group_id:
			url = self.pctl.mbid_image_url_cache.get(release_group_id)
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
				self.pctl.album_mbid_release_group_cache[(artist, tr.album)] = None
			except Exception:
				logging.exception("Unknown error finding image for release group")

		if release_id and not image_data:
			url = self.pctl.mbid_image_url_cache.get(release_id)
			if url:
				return url

			base_url = "https://coverartarchive.org/release/"
			url = f"{base_url}{release_id}"

			try:
				response = requests.get(url, timeout=10)
				response.raise_for_status()
				image_data = response.json()
				final_id = release_id
			except (requests.RequestException, ValueError):
				logging.exception("No image found for album id")
				self.pctl.album_mbid_release_cache[(artist, tr.album)] = None
			except Exception:
				logging.exception("Unknown error getting image found for album id")

		if image_data:
			for image in image_data["images"]:
				if image.get("front") and ("250" in image["thumbnails"] or "small" in image["thumbnails"]):
					self.pctl.album_mbid_release_cache[(artist, tr.album)] = release_id
					self.pctl.album_mbid_release_group_cache[(artist, tr.album)] = release_group_id

					url = image["thumbnails"].get("250")
					if url is None:
						url = image["thumbnails"].get("small")

					if url:
						logging.info("got mb image url for discord")
						self.pctl.mbid_image_url_cache[final_id] = url
						return url

		self.pctl.album_mbid_release_cache[(artist, tr.album)] = None
		self.pctl.album_mbid_release_group_cache[(artist, tr.album)] = None

		return None

	def clean_track_title(self, title: str | None) -> str:
		if not title:
			return ""

		cleaned = title.strip()
		cleaned = re.sub(r"[\(\[\{].*?[\)\]\}]", "", cleaned)
		cleaned = re.split(r"\s*(?:ft\.?|feat\.?|featuring|with)\b", cleaned, flags=re.I)[0]
		if " - " in cleaned:
			left, right = cleaned.split(" - ", 1)
			if re.search(r"(?i)(remix|mix|version|edit|remaster|remastered|live|acoustic|instrumental|single|radio|bonus)", right):
				cleaned = left
		cleaned = cleaned.strip()
		cleaned = re.sub(r"[-–—:;]+$", "", cleaned).strip()
		return cleaned or title.strip()

	def discord_loop(self) -> None:
		try:
			from tauon.t_modules.t_discord import discord_loop_entrypoint
		except Exception:
			logging.exception("Failed to import Discord module")
			if hasattr(self, "_discord_loop_guard_lock"):
				with self._discord_loop_guard_lock:
					self._discord_loop_guard_running = False
					self.prefs.discord_active = False
			return

		discord_loop_entrypoint(self)

	# def discord_loop(self) -> None:
	# 	self.prefs.discord_active = True

	# 	try:
	# 		if not self.pctl.playing_ready():
	# 			return
	# 		asyncio.set_event_loop(asyncio.new_event_loop())

	# 		# logging.info("Attempting to connect to Discord...")
	# 		client_id = "954253873160286278"
	# 		RPC = Presence(client_id)
	# 		RPC.connect()

	# 		logging.info("Discord RPC connection successful.")
	# 		time.sleep(1)
	# 		start_time = time.time()
	# 		idle_time = Timer()

	# 		state = 0
	# 		index = -1
	# 		br = False
	# 		self.gui.discord_status = "Connected"
	# 		self.gui.update += 1
	# 		current_state = 0

	# 		while True:
	# 			while True:

	# 				current_index = self.pctl.playing_object().index
	# 				if self.pctl.playing_state == PlayingState.URL_STREAM:
	# 					current_index = self.radiobox.song_key

	# 				if current_state == 0 and self.pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM):
	# 					current_state = 1
	# 				elif current_state == 1 and self.pctl.playing_state not in (PlayingState.PLAYING, PlayingState.URL_STREAM):
	# 					current_state = 0
	# 					idle_time.set()

	# 				if state != current_state or index != current_index:
	# 					if self.pctl.a_time > 4 or current_state != 1:
	# 						state = current_state
	# 						index = current_index
	# 						break
	# 				if abs(start_time - (time.time() - self.pctl.playing_time)) > 1:
	# 					start_time = time.time() - self.pctl.playing_time
	# 				else:
	# 					break

	# 				if current_state == 0 and idle_time.get() > 13:
	# 					logging.info("Pause discord RPC...")
	# 					self.gui.discord_status = "Idle"
	# 					RPC.clear(self.pid)
	# 					# RPC.close()

	# 					while True:
	# 						if self.prefs.disconnect_discord:
	# 							break
	# 						if self.pctl.playing_state == PlayingState.PLAYING:
	# 							logging.info("Reconnect discord...")
	# 							RPC.connect()
	# 							self.gui.discord_status = "Connected"
	# 							break
	# 						time.sleep(1)

	# 					if not self.prefs.disconnect_discord:
	# 						continue

	# 				time.sleep(1)

	# 				if self.prefs.disconnect_discord:
	# 					RPC.clear(self.pid)
	# 					RPC.close()
	# 					self.prefs.disconnect_discord = False
	# 					self.gui.discord_status = "Not connected"
	# 					br = True
	# 					break

	# 			if br:
	# 				break

	# 			title = _("Unknown Track")
	# 			tr = self.pctl.playing_object()
	# 			if tr.artist and tr.title and self.pctl.playing_state == PlayingState.URL_STREAM:
	# 				title = tr.title + " | " + tr.artist
	# 			else:
	# 				title = tr.title
	# 			if len(title) > 150:
	# 				title = _("Unknown Track")

	# 			artist = tr.artist or _("Unknown Artist")

	# 			if self.pctl.playing_state == PlayingState.URL_STREAM and tr.album:
	# 				album = self.radiobox.loaded_station["title"]
	# 			else:
	# 				album = None if tr.album.lower() in (tr.title.lower(), tr.artist.lower()) else tr.album

	# 			if album and len(album) == 1:
	# 				album += " "

	# 			if state == 1:
	# 				#logging.info("PLAYING: " + title)
	# 				#logging.info(start_time)
	# 				url = self.get_album_art_url(self.pctl.playing_object())

	# 				large_image = "tauon-standard"
	# 				small_image = None
	# 				if url:
	# 					large_image = url
	# 					small_image = "tauon-standard"
	# 				RPC.update(
	# 					activity_type = ActivityType.LISTENING,
	# 					status_display_type = StatusDisplayType.STATE,
	# 					pid=self.pid,
	# 					**({"state": artist} if self.pctl.playing_state != PlayingState.URL_STREAM else {"state": album}),
	# 					details=title,
	# 					start=int(start_time),
	# 					**({"end": int(start_time + tr.length)} if self.pctl.playing_state != PlayingState.URL_STREAM else {}),
	# 					**({"large_text": album} if album and self.pctl.playing_state != PlayingState.URL_STREAM else {}),
	# 					large_image=large_image,
	# 					small_image=small_image)

	# 			else:
	# 				#logging.info("Discord RPC - Stop")
	# 				RPC.update(
	# 					activity_type = ActivityType.LISTENING,
	# 					pid=self.pid,
	# 					state="Idle",
	# 					large_image="tauon-standard")

	# 			time.sleep(2)

	# 			if self.prefs.disconnect_discord:
	# 				RPC.clear(self.pid)
	# 				RPC.close()
	# 				self.prefs.disconnect_discord = False
	# 				break

	# 	except Exception:
	# 		logging.exception("Error connecting to Discord - is Discord running?")
	# 		# self.show_message(_("Error connecting to Discord", mode='error')
	# 		self.gui.discord_status = _("Error - Discord not running?")
	# 		self.prefs.disconnect_discord = False

	# 	finally:
	# 		loop = asyncio.get_event_loop()
	# 		if not loop.is_closed():
	# 			loop.close()
	# 		self.prefs.discord_active = False

	#def open_donate_link() -> None:
	#	webbrowser.open("https://github.com/sponsors/Taiko2k", new=2, autoraise=True)

	def open_manual_link(self) -> None:
		webbrowser.open("https://tauonmusicbox.rocks/manual/overview/", new=2, autoraise=True)

	def stop_quick_add(self) -> None:
		self.pctl.quick_add_target = None

	def show_stop_quick_add(self, _unused: int) -> bool:
		return self.pctl.quick_add_target is not None

	def view_tracks(self) -> None:
		# if self.gui.show_playlist is False:
		# 	self.gui.show_playlist = True
		if self.prefs.album_mode:
			self.toggle_album_mode()
		if self.gui.combo_mode:
			self.exit_combo()
		if self.gui.rsp:
			self.toggle_side_panel()

	# def view_standard_full(self):
	# 	# if self.gui.show_playlist is False:
	# 	# 	self.gui.show_playlist = True
	# 	if self.prefs.album_mode:
	# 		self.toggle_album_mode()
	# 	if self.gui.combo_mode:
	# 		self.toggle_combo_view(off=True)
	# 	if not self.gui.rsp:
	# 		self.toggle_side_panel()
	# 	self.gui.update_layout = True
	# 	self.gui.rspw = self.window_size[0]

	def view_standard_meta(self) -> None:
		# if self.gui.show_playlist is False:
		# 	self.gui.show_playlist = True
		if self.prefs.album_mode:
			self.toggle_album_mode()

		if self.gui.combo_mode:
			self.exit_combo()

		if not self.gui.rsp:
			self.toggle_side_panel()

		self.gui.update_layout = True
		# self.gui.rspw = 80 + int(self.window_size[0] * 0.18)

	def view_standard(self) -> None:
		# if self.gui.show_playlist is False:
		# 	self.gui.show_playlist = True
		if self.prefs.album_mode:
			self.toggle_album_mode()
		if self.gui.combo_mode:
			self.exit_combo()
		if not self.gui.rsp:
			self.toggle_side_panel()

	def get_folder_list(self, index: int) -> list[int]:
		playlist: list[int] = []

		for item in self.pctl.default_playlist:
			if self.pctl.master_library[item].parent_folder_name == self.pctl.master_library[index].parent_folder_name and \
					self.pctl.master_library[item].album == self.pctl.master_library[index].album:
				playlist.append(item)
		return list(set(playlist))

	def gal_jump_select(self, up: bool = False, num: int = 1) -> None:
		old_selected = self.pctl.selected_in_playlist
		old_num = num

		if not self.pctl.default_playlist:
			return

		on = self.pctl.selected_in_playlist
		if on > len(self.pctl.default_playlist) - 1:
			on = 0
			self.pctl.selected_in_playlist = 0

		if up is False:
			while num > 0:
				while self.pctl.master_library[
					self.pctl.default_playlist[on]].parent_folder_name == self.pctl.master_library[
					self.pctl.default_playlist[self.pctl.selected_in_playlist]].parent_folder_name:
					on += 1

					if on > len(self.pctl.default_playlist) - 1:
						self.pctl.selected_in_playlist = old_selected
						return

				self.pctl.selected_in_playlist = on
				num -= 1
		else:
			if num > 1:
				if self.pctl.selected_in_playlist > len(self.pctl.default_playlist) - 1:
					self.pctl.selected_in_playlist = old_selected
					return

				alb = self.get_album_info(self.pctl.selected_in_playlist)
				if alb[1][0] in self.album_dex[:num]:
					self.pctl.selected_in_playlist = old_selected
					return

			while num > 0:
				alb = self.get_album_info(self.pctl.selected_in_playlist)

				if alb[1][0] > -1:
					on = alb[1][0] - 1

				self.pctl.selected_in_playlist = max(self.get_album_info(on)[1][0], 0)
				num -= 1

	def update_playlist_call(self) -> None:
		self.gui.request_frame()
		self.gui.request_tracklist_redraw()

	def pl_is_mut(self, pl: int) -> bool:
		"""Returns True if specified playlist number is modifiable/not associated with a generator i think"""
		id = self.pctl.pl_to_id(pl)
		if id is None:
			return False
		return not (self.pctl.gen_codes.get(id) and "self" not in self.pctl.gen_codes[id])

	def clear_gen(self, id: int) -> None:
		del self.pctl.gen_codes[id]
		self.show_message(_("Okay, it's a normal playlist now."), mode="done")

	def clear_gen_ask(self, id: int) -> None:
		if "jelly\"" in self.pctl.gen_codes.get(id, ""):
			return
		if "spl\"" in self.pctl.gen_codes.get(id, ""):
			return
		if "tpl\"" in self.pctl.gen_codes.get(id, ""):
			return
		if "tar\"" in self.pctl.gen_codes.get(id, ""):
			return
		if "tmix\"" in self.pctl.gen_codes.get(id, ""):
			return
		self.gui.message_box_confirm_callback = self.clear_gen
		self.gui.message_box_no_callback = None
		self.gui.message_box_confirm_reference = (id,)
		self.show_message(_("You added tracks to a generator playlist. Do you want to clear the generator?"), mode="confirm")

	def _window_is_maximized(self) -> bool:
		flags = sdl3.SDL_GetWindowFlags(self.t_window)
		return bool(flags & sdl3.SDL_WINDOW_MAXIMIZED)

	def frame_pace(self) -> float:
		"""Delay to schedule the next frame of a continuously animating visual
		(delay_frame argument), paced to the window's display refresh rate.

		Slightly under one refresh period: when vsync is working the present
		absorbs the slack and frames stay locked to vblank, and when it isn't
		(driver override, occluded window) this still caps the loop near the
		refresh rate instead of letting it spin unbounded."""
		hz = 0.0
		mode = sdl3.SDL_GetCurrentDisplayMode(sdl3.SDL_GetDisplayForWindow(self.t_window))
		if mode:
			hz = mode.contents.refresh_rate
		if not 0 < hz < 1000:
			hz = 60.0
		return 0.85 / hz

	def _is_wayland_standalone_wm(self) -> bool:
		if not self.wayland:
			return False
		desktop = (self.desktop or "").lower()
		de_names = ("gnome", "kde", "plasma", "xfce", "cinnamon", "mate", "unity", "lxqt", "lxde", "budgie", "pantheon", "cosmic")
		return not any(name in desktop for name in de_names)

	def _get_wayland_wm_controller(self) -> Literal["sway", "hyprland"] | None:
		if os.environ.get("SWAYSOCK"):
			return "sway"
		if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
			return "hyprland"
		return None

	def _run_wm_command(self, cmd: list[str]) -> str | None:
		binary = cmd[0]
		if shutil.which(binary) is None:
			if not self._wayland_wm_ipc_warned:
				logging.warning("Wayland mini-mode WM integration unavailable: missing %s", binary)
				self._wayland_wm_ipc_warned = True
			return None
		try:
			result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=0.8)
		except Exception:
			return None
		if result.returncode != 0:
			return None
		return result.stdout

	def _reset_mini_mode_wm_tracking(self) -> None:
		self.mini_mode_wm_forced_floating = False
		self.mini_mode_wm_was_floating = False

	def _get_sway_focused_floating_state(self) -> bool | None:
		tree_raw = self._run_wm_command(["swaymsg", "-t", "get_tree", "-r"])
		if not tree_raw:
			return None
		try:
			tree = json.loads(tree_raw)
		except json.JSONDecodeError:
			return None

		stack = [tree]
		while stack:
			node = stack.pop()
			if node.get("focused"):
				fstate = node.get("floating")
				return fstate in ("user_on", "auto_on")
			stack.extend(node.get("nodes", []))
			stack.extend(node.get("floating_nodes", []))
		return None

	def _get_hyprland_active_window(self) -> dict[str, object] | None:
		active_raw = self._run_wm_command(["hyprctl", "-j", "activewindow"])
		if not active_raw:
			return None
		try:
			active = json.loads(active_raw)
		except json.JSONDecodeError:
			return None
		if not isinstance(active, dict):
			return None
		return active


	def _wayland_window_is_floating(self) -> bool | None:
		if not self._is_wayland_standalone_wm():
			return None

		wm_controller = self._get_wayland_wm_controller()
		if wm_controller == "sway":
			return self._get_sway_focused_floating_state()

		if wm_controller == "hyprland":
			active = self._get_hyprland_active_window()
			if active is None:
				return None
			return bool(active.get("floating", False))

		return None

	def _set_wayland_mini_mode_window_state(self, entering: bool, width: int = 0, height: int = 0, reset_tracking: bool = True) -> None:
		if not self._is_wayland_standalone_wm():
			return
		if entering and reset_tracking:
			self._reset_mini_mode_wm_tracking()

		wm_controller = self._get_wayland_wm_controller()
		if wm_controller is None:
			if not entering:
				self._reset_mini_mode_wm_tracking()
			return

		if wm_controller == "sway":
			if entering:
				if reset_tracking:
					floating_state = self._get_sway_focused_floating_state()
					if floating_state is not None:
						self.mini_mode_wm_was_floating = floating_state

					if not self.mini_mode_wm_was_floating:
						self._run_wm_command(["swaymsg", "floating", "enable"])
						self.mini_mode_wm_forced_floating = True
				elif self.mini_mode_wm_forced_floating:
					self._run_wm_command(["swaymsg", "floating", "enable"])

				if width > 0 and height > 0:
					self._run_wm_command(["swaymsg", "resize", "set", "width", f"{width}px", "height", f"{height}px"])
			else:
				if self.mini_mode_wm_forced_floating and not self.mini_mode_wm_was_floating:
					self._run_wm_command(["swaymsg", "floating", "disable"])
				self._reset_mini_mode_wm_tracking()
			return

		if wm_controller == "hyprland":
			active = self._get_hyprland_active_window()
			if active is None:
				if not entering:
					self._reset_mini_mode_wm_tracking()
				return
			address = str(active.get("address", ""))
			if not address:
				if not entering:
					self._reset_mini_mode_wm_tracking()
				return

			if entering:
				if reset_tracking:
					self.mini_mode_wm_was_floating = bool(active.get("floating", False))
					if not self.mini_mode_wm_was_floating:
						self._run_wm_command(["hyprctl", "dispatch", "togglefloating", f"address:{address}"])
						self.mini_mode_wm_forced_floating = True
				elif self.mini_mode_wm_forced_floating and not bool(active.get("floating", False)):
					self._run_wm_command(["hyprctl", "dispatch", "togglefloating", f"address:{address}"])

				if width > 0 and height > 0:
					self._run_wm_command(["hyprctl", "dispatch", "resizeactive", "exact", str(width), str(height)])
			else:
				if self.mini_mode_wm_forced_floating and not self.mini_mode_wm_was_floating:
					self._run_wm_command(["hyprctl", "dispatch", "togglefloating", f"address:{address}"])
				self._reset_mini_mode_wm_tracking()

	def set_mini_mode(self) -> None:
		if self.gui.fullscreen:
			return

		self.inp.mouse_down = False
		self.inp.mouse_up = False
		self.inp.mouse_click = False

		is_wayland_standalone_wm = self._is_wayland_standalone_wm()
		is_floating_wayland_window = self._wayland_window_is_floating() if is_wayland_standalone_wm else None

		# Standalone Wayland WMs can report maximized flags while window is already floating.
		# Treat already-floating windows as non-maximized for mini-mode transitions.
		self.gui.mini_mode_return_maximized = self._window_is_maximized() and not bool(is_floating_wayland_window)
		if self.gui.mini_mode_return_maximized:
			sdl3.SDL_RestoreWindow(self.t_window)
			sdl3.SDL_SyncWindow(self.t_window)
			sdl3.SDL_PumpEvents()
			self.gui.maximized = False
			self.update_layout_do()

		if self.gui.mode == GuiMode.MAIN:
			self.old_window_position = get_window_position(self.t_window)
			saved_w = pointer(c_int(0))
			saved_h = pointer(c_int(0))
			sdl3.SDL_GetWindowSize(self.t_window, saved_w, saved_h)
			self.mini_mode_restore_size = (saved_w.contents.value, saved_h.contents.value)
			self.gui.save_size[0] = self.mini_mode_restore_size[0]
			self.gui.save_size[1] = self.mini_mode_restore_size[1]

		if self.prefs.mini_mode_on_top and not self.wayland:
			sdl3.SDL_SetWindowAlwaysOnTop(self.t_window, True)

		self.gui.mode = GuiMode.MINI
		self.gui.vis = 0
		self.gui.turbo = self.prefs.mini_mode_mode == MiniModeMode.SIGNAL
		self.gui.draw_vis4_top = False
		self.gui.level_update = self.prefs.mini_mode_mode == MiniModeMode.SIGNAL

		i_y = pointer(c_int(0))
		i_x = pointer(c_int(0))
		sdl3.SDL_GetWindowPosition(self.t_window, i_x, i_y)
		self.gui.save_position = (i_x.contents.value, i_y.contents.value)

		self.mini_mode.was_borderless = self.draw_border
		if not is_wayland_standalone_wm:
			sdl3.SDL_SetWindowBordered(self.t_window, False)

		size = (350, 429)
		if self.prefs.mini_mode_mode == MiniModeMode.MINI:
			size = (330, 330)
		if self.prefs.mini_mode_mode == MiniModeMode.LARGE:
			size = (420, 499)
		if self.prefs.mini_mode_mode == MiniModeMode.SQUARE_LARGE:
			size = (430, 430)
		if self.prefs.mini_mode_mode == MiniModeMode.TAB:
			size = (330, 80)
		if self.prefs.mini_mode_mode == MiniModeMode.SLATE:
			size = (350, 545)
			self.style_overlay.flush()
			self.thread_manager.ready("style")
		if self.prefs.mini_mode_mode == MiniModeMode.SIGNAL:
			size = (640, 460)

		self.logical_size[0] = size[0]
		self.logical_size[1] = size[1]

		min_size = (100, 80)
		sdl3.SDL_SetWindowMinimumSize(self.t_window, min_size[0], min_size[1])
		self._set_wayland_mini_mode_window_state(True, self.logical_size[0], self.logical_size[1])
		sdl3.SDL_SetWindowResizable(self.t_window, True)
		sdl3.SDL_SetWindowSize(self.t_window, self.logical_size[0], self.logical_size[1])
		if not is_wayland_standalone_wm:
			sdl3.SDL_SetWindowResizable(self.t_window, False)

		if self.mini_mode.save_position:
			sdl3.SDL_SetWindowPosition(self.t_window, self.mini_mode.save_position[0], self.mini_mode.save_position[1])

		self.gui.update_layout = True
		self.gui.request_frame()

	def restore_full_mode(self) -> None:
		logging.info("RESTORE FULL")
		i_y = pointer(c_int(0))
		i_x = pointer(c_int(0))
		sdl3.SDL_GetWindowPosition(self.t_window, i_x, i_y)
		self.mini_mode.save_position = [i_x.contents.value, i_y.contents.value]

		if not self.mini_mode.was_borderless:
			sdl3.SDL_SetWindowBordered(self.t_window, True)

		restore_size = self.mini_mode_restore_size or (self.gui.save_size[0], self.gui.save_size[1])
		self.logical_size[0] = restore_size[0]
		self.logical_size[1] = restore_size[1]

		sdl3.SDL_SetWindowPosition(self.t_window, self.gui.save_position[0], self.gui.save_position[1])


		sdl3.SDL_SetWindowResizable(self.t_window, True)
		sdl3.SDL_SetWindowSize(self.t_window, self.logical_size[0], self.logical_size[1])
		sdl3.SDL_SetWindowAlwaysOnTop(self.t_window, False)

		# if self.macos:
		# 	sdl3.SDLSetWindowMinimumSize(self.t_window, 560, 330)
		# else:
		if self.logical_size[0] != self.window_size[0]:
			sdl3.SDL_SetWindowMinimumSize(self.t_window, 560, 330)
		else:
			sdl3.SDL_SetWindowMinimumSize(self.t_window, round(560 * self.gui.scale), round(330 * self.gui.scale))

		self.restore_ignore_timer.set()  # Hacky

		self.gui.mode = GuiMode.MAIN
		self._set_wayland_mini_mode_window_state(False)

		sdl3.SDL_SyncWindow(self.t_window)
		sdl3.SDL_PumpEvents()
		sdl3.SDL_GetWindowSize(self.t_window, i_x, i_y)
		self.window_size[0] = i_x.contents.value
		self.window_size[1] = i_y.contents.value
		self.logical_size[0] = i_x.contents.value
		self.logical_size[1] = i_y.contents.value

		self.inp.mouse_down = False
		self.inp.mouse_up = False
		self.inp.mouse_click = False

		if self.gui.mini_mode_return_maximized:
			sdl3.SDL_MaximizeWindow(self.t_window)
			time.sleep(0.05)
			sdl3.SDL_PumpEvents()
			sdl3.SDL_GetWindowSize(self.t_window, i_x, i_y)
			self.logical_size[0] = i_x.contents.value
			self.logical_size[1] = i_y.contents.value
			self.gui.maximized = True
		self.gui.mini_mode_return_maximized = False
		self.mini_mode_restore_size = None

		#logging.info(self.window_size)

		self.gui.update_layout = True
		if self.prefs.art_bg:
			self.thread_manager.ready("style")

	# def visit_radio_site_show_test(self, p):
	# 	return "website_url" in self.prefs.radio_urls[p] and self.prefs.radio_urls[p].["website_url"]

	def visit_radio_site_deco(self, station: RadioStation) -> Decorator:
		if station.website_url:
			return Decorator(self.colours.menu_text, self.colours.menu_background, None)
		return Decorator(self.colours.menu_text_disabled, self.colours.menu_background, None)

	def visit_radio_station_site_deco(self, item: tuple[int, RadioStation]) -> Decorator:
		return self.visit_radio_site_deco(item[1])

	def radio_saved_panel_test(self, _unused) -> bool:
		return self.radiobox.tab == 0

	def save_to_radios(self, station: RadioStation) -> None:
		self.pctl.radio_playlists[self.pctl.radio_playlist_viewing].stations.append(station)
		self.toast(_("Added station to: ") + self.pctl.radio_playlists[self.pctl.radio_playlist_viewing].name)

	def create_artist_pl(self, artist: str, replace: bool = False) -> None:
		source_pl = self.pctl.active_playlist_viewing
		this_pl = self.pctl.active_playlist_viewing

		if self.pctl.multi_playlist[source_pl].parent_playlist_id:
			new = self.pctl.id_to_pl(self.pctl.multi_playlist[source_pl].parent_playlist_id)
			if new is None:
				# The original playlist is now gone
				self.pctl.multi_playlist[source_pl].parent_playlist_id = 0
			else:
				source_pl = new
				# replace = True

		playlist = []

		for item in self.pctl.multi_playlist[source_pl].playlist_ids:
			track = self.pctl.get_track(item)
			if artist in (track.artist, track.album_artist):
				playlist.append(item)

		if replace:
			self.pctl.multi_playlist[this_pl].playlist_ids[:] = playlist[:]
			self.pctl.multi_playlist[this_pl].title = _("Artist: ") + artist
			if self.prefs.album_mode:
				self.reload_albums()

			# Transfer playing track back to original playlist
			if self.pctl.multi_playlist[this_pl].parent_playlist_id:
				new = self.pctl.id_to_pl(self.pctl.multi_playlist[this_pl].parent_playlist_id)
				tr = self.pctl.playing_object()
				if new is not None and tr and self.pctl.active_playlist_playing == this_pl:
					if tr.index not in self.pctl.multi_playlist[this_pl].playlist_ids and tr.index in self.pctl.multi_playlist[source_pl].playlist_ids:
						logging.info("Transfer back playing")
						self.pctl.active_playlist_playing = source_pl
						self.pctl.playlist_playing_position = self.pctl.multi_playlist[source_pl].playlist_ids.index(tr.index)

			self.pctl.gen_codes[self.pctl.pl_to_id(this_pl)] = "s\"" + self.pctl.multi_playlist[source_pl].title + "\" a\"" + artist + "\""
		else:
			self.pctl.multi_playlist.append(
				self.pl_gen(
					title=_("Artist: ") + artist,
					playlist_ids=playlist,
					hide_title=False,
					parent=self.pctl.pl_to_id(source_pl)))

			self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[source_pl].title + "\" a\"" + artist + "\""

			self.pctl.switch_playlist(len(self.pctl.multi_playlist) - 1)

	def aa_sort_alpha(self) -> None:
		self.prefs.artist_list_sort_mode = "alpha"
		self.artist_list_box.saves.clear()

	def aa_sort_popular(self) -> None:
		self.prefs.artist_list_sort_mode = "popular"
		self.artist_list_box.saves.clear()

	def aa_sort_play(self) -> None:
		self.prefs.artist_list_sort_mode = "play"
		self.artist_list_box.saves.clear()

	def toggle_artist_list_style(self) -> None:
		if self.prefs.artist_list_style == 1:
			self.prefs.artist_list_style = 2
		else:
			self.prefs.artist_list_style = 1

	def toggle_artist_list_threshold(self) -> None:
		if self.prefs.artist_list_threshold > 0:
			self.prefs.artist_list_threshold = 0
		else:
			self.prefs.artist_list_threshold = 4
		self.artist_list_box.saves.clear()

	def toggle_artist_list_threshold_deco(self) -> Decorator:
		if self.prefs.artist_list_threshold == 0:
			return Decorator(self.colours.menu_text, self.colours.menu_background, _("Filter Small Artists"))
		# save = self.artist_list_box.saves.get(self.pctl.multi_playlist[self.pctl.active_playlist_viewing].uuid_int)
		# if save and save[5] == 0:
		# 	return Decorator(self.colours.menu_text_disabled, self.colours.menu_background, _("Include All Artists"))
		return Decorator(self.colours.menu_text, self.colours.menu_background, _("Include All Artists"))

	def verify_discogs(self) -> bool:
		return len(self.prefs.discogs_pat) == 40

	def save_discogs_artist_thumb(self, artist: str, filepath: str) -> None:
		logging.info("Searching discogs for artist image...")

		# Make artist name url safe
		artist = artist.replace("/", "").replace("\\", "").replace(":", "")

		# Search for Discogs artist id
		url = "https://api.discogs.com/database/search"
		r = requests.get(url, params={"query": artist, "type": "artist", "token": self.prefs.discogs_pat}, headers={"User-Agent": self.t_agent}, timeout=10)
		id = r.json()["results"][0]["id"]

		# Search artist info, get images
		url = "https://api.discogs.com/artists/" + str(id)
		r = requests.get(url, headers={"User-Agent": self.t_agent}, params={"token": self.prefs.discogs_pat}, timeout=10)
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

		response = urllib.request.urlopen(url, context=self.tls_context)
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

	def save_fanart_artist_thumb(self, mbid: str, filepath: str, preview: bool = False) -> None:
		logging.info("Searching fanart.tv for image...")
		#logging.info("mbid is " + mbid)
		r = requests.get("https://webservice.fanart.tv/v3/music/" + mbid + "?api_key=" + self.prefs.fatvap, timeout=5)
		#logging.info(r.json())
		thumblink = r.json()["artistthumb"][0]["url"]
		if preview:
			thumblink = thumblink.replace("/fanart/music", "/preview/music")

		response = urllib.request.urlopen(thumblink, timeout=10, context=self.tls_context)
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

			if self.prefs.fanart_notify:
				self.prefs.fanart_notify = False
				self.show_message(
					_("Notice: Artist image sourced from fanart.tv"),
					_("They encourage you to contribute at {link}").format(link="https://fanart.tv"), mode="link")
			logging.info("Found artist thumbnail from fanart.tv")

	def queue_pause_deco(self) -> Decorator:
		if self.pctl.pause_queue:
			return Decorator(self.colours.menu_text, self.colours.menu_background, _("Resume Queue"))
		return Decorator(self.colours.menu_text, self.colours.menu_background, _("Pause Queue"))

	# def finish_current_deco(self) -> Decorator:
	# 	colour = self.colours.menu_text
	# 	line = "Finish Playing Album"
	# 	if self.pctl.playing_object() is None:
	# 		colour = self.colours.menu_text_disabled
	# 	if self.pctl.force_queue and pctl.force_queue[0].album_stage == 1:
	# 		colour = self.colours.menu_text_disabled
	# 	return Decorator(self.colour, self.colours.menu_background, line)

	def art_metadata_overlay(self, right: float, bottom: float, showc: list[tuple[int, int, int, int, str]]) -> None:
		if not showc:
			return

		padding = 6 * self.gui.scale

		if not self.inp.key_shift_down:
			line = ""
			if showc[0] == 1:
				line += "E "
			elif showc[0] == 2:
				line += "N "
			else:
				line += "F "

			line += str(showc[2] + 1) + "/" + str(showc[1])

			y = bottom - 40 * self.gui.scale

			tag_width = self.ddt.get_text_w(line, 12) + 12 * self.gui.scale
			self.ddt.rect_a((right - (tag_width + padding), y), (tag_width, 18 * self.gui.scale), ColourRGBA(8, 8, 8, 255))
			self.ddt.text(((right) - (6 * self.gui.scale + padding), y, 1), line, ColourRGBA(200, 200, 200, 255), 12, bg=ColourRGBA(30, 30, 30, 255))
		else:  # Extended metadata
			line = ""
			if showc[0] == 1:
				line += "Embedded"
			elif showc[0] == 2:
				line += "Network"
			else:
				line += "File"

			y = bottom - 76 * self.gui.scale

			tag_width = self.ddt.get_text_w(line, 12) + 12 * self.gui.scale
			self.ddt.rect_a((right - (tag_width + padding), y), (tag_width, 18 * self.gui.scale), ColourRGBA(8, 8, 8, 255))
			self.ddt.text(((right) - (6 * self.gui.scale + padding), y, 1), line, ColourRGBA(200, 200, 200, 255), 12, bg=ColourRGBA(30, 30, 30, 255))

			y += 18 * self.gui.scale

			line = ""
			line += showc[4]
			line += " " + str(showc[3][0]) + "×" + str(showc[3][1])

			tag_width = self.ddt.get_text_w(line, 12) + 12 * self.gui.scale
			self.ddt.rect_a((right - (tag_width + padding), y), (tag_width, 18 * self.gui.scale), ColourRGBA(8, 8, 8, 255))
			self.ddt.text(((right) - (6 * self.gui.scale + padding), y, 1), line, ColourRGBA(200, 200, 200, 255), 12, bg=ColourRGBA(30, 30, 30, 255))

			y += 18 * self.gui.scale

			line = ""
			line += str(showc[2] + 1) + "/" + str(showc[1])

			tag_width = self.ddt.get_text_w(line, 12) + 12 * self.gui.scale
			self.ddt.rect_a((right - (tag_width + padding), y), (tag_width, 18 * self.gui.scale), ColourRGBA(8, 8, 8, 255))
			self.ddt.text(((right) - (6 * self.gui.scale + padding), y, 1), line, ColourRGBA(200, 200, 200, 255), 12, bg=ColourRGBA(30, 30, 30, 255))

	def artist_dl_deco(self) -> Decorator:
		if self.artist_info_box.status == "Ready":
			return Decorator(self.colours.menu_text_disabled, self.colours.menu_background, None)
		return Decorator(self.colours.menu_text, self.colours.menu_background, None)

	def station_browse(self) -> None:
		self.radiobox.active = True
		self.radiobox.edit_mode = False
		self.radiobox.add_mode = False
		self.radiobox.center = True
		self.radiobox.tab = 1

	def add_station(self) -> None:
		self.radiobox.active = True
		self.radiobox.edit_mode = True
		self.radiobox.add_mode = True
		self.radiobox.radio_field.text = ""
		self.radiobox.radio_field_title.text = ""
		self.radiobox.station_editing = None
		self.radiobox.center = True

	def rename_station(self, item: tuple[int, RadioStation]) -> None:
		station = item[1]
		self.radiobox.active = True
		self.radiobox.center = False
		self.radiobox.edit_mode = True
		self.radiobox.add_mode = False
		self.radiobox.radio_field.text = station.stream_url
		self.radiobox.radio_field_title.text = station.title if station.title is not None else ""
		self.radiobox.station_editing = station

	def remove_station(self, item: tuple[int, RadioStation]) -> None:
		index = item[0]
		del self.pctl.radio_playlists[self.pctl.radio_playlist_viewing].stations[index]

	def dismiss_dl(self) -> None:
		self.dl_mon.ready.clear()
		self.dl_mon.done.update(self.dl_mon.watching)
		self.dl_mon.watching.clear()

	def download_img(self, link: str, target_dir: str, track: TrackClass) -> None:
		try:
			response = urllib.request.urlopen(link, context=self.tls_context)
			info = response.info()
			if info.get_content_maintype() == "image":
				if info.get_content_subtype() == "jpeg":
					save_target = os.path.join(target_dir, "image.jpg")
					with open(save_target, "wb") as f:
						f.write(response.read())
					# self.clear_img_cache()
					self.clear_track_image_cache(track)

				elif info.get_content_subtype() == "png":
					save_target = os.path.join(target_dir, "image.png")
					with open(save_target, "wb") as f:
						f.write(response.read())
					# self.clear_img_cache()
					self.clear_track_image_cache(track)
				else:
					self.show_message(_("Image types other than PNG or JPEG are currently not supported"), mode="warning")
			else:
				self.show_message(_("The link does not appear to refer to an image file."), mode="warning")
			self.gui.image_downloading = False

		except Exception as e:
			logging.exception("Image download failed")
			self.show_message(_("Image download failed."), str(e), mode="warning")
			self.gui.image_downloading = False

	def display_you_heart(self, x: int, yy: int, just: int = 0) -> None:
		rect = [x - 1 * self.gui.scale, yy - 4 * self.gui.scale, 15 * self.gui.scale, 17 * self.gui.scale]
		self.gui.heart_fields.append(rect)
		self.fields.add(rect, self.update_playlist_call)
		if self.coll(rect) and not self.gui.track_box:
			self.gui.request_tracklist_redraw()
			w = self.ddt.get_text_w(_("You"), 13)
			xx = (x - w) - 5 * self.gui.scale

			if just == 1:
				xx += w + 15 * self.gui.scale

			ty = yy - 28 * self.gui.scale
			tx = xx
			if ty < self.gui.panelY + 5 * self.gui.scale:
				ty = self.gui.panelY + 5 * self.gui.scale
				tx -= 20 * self.gui.scale

		#	self.ddt.rect_r((xx - 1 * self.gui.scale, yy - 26 * self.gui.scale - 1 * self.gui.scale, w + 10 * self.gui.scale + 2 * self.gui.scale, 19 * self.gui.scale + 2 * self.gui.scale), [50, 50, 50, 255], True)
			self.ddt.rect((tx - 5 * self.gui.scale, ty, w + 20 * self.gui.scale, 24 * self.gui.scale), ColourRGBA(15, 15, 15, 255))
			self.ddt.rect((tx - 5 * self.gui.scale, ty, w + 20 * self.gui.scale, 24 * self.gui.scale), ColourRGBA(35, 35, 35, 255))
			self.ddt.text((tx + 5 * self.gui.scale, ty + 4 * self.gui.scale), _("You"), ColourRGBA(250, 250, 250, 255), 13, bg=ColourRGBA(15, 15, 15, 255))

		self.gui.heart_row_icon.render(x, yy, ColourRGBA(244, 100, 100, 255))

	def display_friend_heart(self, x: int, yy: int, name: str, just: int = 0) -> None:
		self.gui.heart_row_icon.render(x, yy, self.heart_colours.get(name))

		rect = [x - 1, yy - 4, 15 * self.gui.scale, 17 * self.gui.scale]
		self.gui.heart_fields.append(rect)
		self.fields.add(rect, self.update_playlist_call)
		if self.coll(rect) and not self.gui.track_box:
			self.gui.request_tracklist_redraw()
			w = self.ddt.get_text_w(name, 13)
			xx = (x - w) - 5 * self.gui.scale

			if just == 1:
				xx += w + 15 * self.gui.scale

			ty = yy - 28 * self.gui.scale
			tx = xx
			if ty < self.gui.panelY + 5 * self.gui.scale:
				ty = self.gui.panelY + 5 * self.gui.scale
				tx -= 20 * self.gui.scale

			self.ddt.rect((tx - 5 * self.gui.scale, ty, w + 20 * self.gui.scale, 24 * self.gui.scale), ColourRGBA(15, 15, 15, 255))
			self.ddt.rect((tx - 5 * self.gui.scale, ty, w + 20 * self.gui.scale, 24 * self.gui.scale), ColourRGBA(35, 35, 35, 255))
			self.ddt.text((tx + 5 * self.gui.scale, ty + 4 * self.gui.scale), name, ColourRGBA(250, 250, 250, 255), 13, bg=ColourRGBA(15, 15, 15, 255))

	def reload_scale(self, skip_render: bool = False) -> None:
		auto_scale(self.bag)

		scale = self.prefs.scale_want

		self.gui.scale = scale
		self.ddt.scale = self.gui.scale
		self.prime_fonts()
		self.ddt.clear_text_cache()
		if not skip_render:
			scale_assets(tauon=self, bag=self.bag, gui=self.gui, scale_want=scale, force=True)
		self.img_slide_update_gall(self.album_mode_art_size)

		for item in WhiteModImageAsset.assets:
			item.reload()
		for item in LoadImageAsset.assets:
			item.reload()
		for menu in Menu.instances:
			menu.rescale()

		self.bottom_bar1.__init__(self)
		self.bottom_bar_ao1.__init__(self)
		self.top_panel.__init__(self)
		self.view_box.__init__(self, reload=True)
		self.queue_box.recalc()
		self.playlist_box.recalc()

	def update_layout_do(self) -> None:
		window_size = self.window_size
		prefs = self.prefs
		dirs = self.dirs
		ddt = self.ddt
		gui = self.gui
		if prefs.scale_want != gui.scale:
			logging.info("Reload scale")
			self.reload_scale()

		w = window_size[0]
		h = window_size[1]

		if gui.switch_showcase_off:
			ddt.force_gray = False
			gui.switch_showcase_off = False
			self.exit_combo(restore=True)

		if self.draw_max_button and prefs.force_hide_max_button:
			self.draw_max_button = False

		if gui.theme_name != prefs.theme_name:
			gui.reload_theme = True
			prefs.theme = get_theme_number(dirs, prefs.theme_name)
			#logging.info("Config reload theme...")

		# Restore in case of error
		if gui.rspw < 30 * gui.scale:
			gui.rspw = 100 * gui.scale

		# Lock right side panel to full size if fully extended -----
		if prefs.side_panel_layout == 0 and not prefs.album_mode:
			max_w = round(
				((window_size[1] - gui.panelY - gui.panelBY - 17 * gui.scale) * gui.art_max_ratio_lock) + 17 * gui.scale)
			# 17 here is the art box inset value

			if not prefs.album_mode and gui.rspw > max_w - 12 * gui.scale and gui.side_drag:
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
			for item in self.tree_view_box.rows:
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

		# The art background draws underneath the UI, so panel fills are made
		# translucent to let it show through; strength maps to panel alpha
		colours = self.colours
		panel_colours = [
			(name, c) for name in colours.art_bg_panel_colours
			if (c := getattr(colours, name, None)) is not None]

		# Smaller UI furniture sitting on the panels also lets the art
		# through, but less so than the panels themselves
		element_colours = [
			(name, c) for name in colours.art_bg_element_colours
			if (c := getattr(colours, name, None)) is not None]

		# Menus, dialogs and their controls draw over other UI and must stay
		# readable; de-alias any that share an object with a colour being
		# made translucent before changing alphas
		modified_colours = panel_colours + element_colours
		for keep_name in ("menu_background", "toggle_box_on", "sys_tab_bg", "sys_tab_hl"):
			keep = getattr(colours, keep_name, None)
			if keep is not None and any(keep is c for _name, c in modified_colours):
				setattr(colours, keep_name, ColourRGBA(keep.r, keep.g, keep.b, keep.a))

		panel_alpha = 255
		element_alpha = 255
		if prefs.art_bg:
			panel_alpha = max(120, 255 - round(prefs.art_bg_opacity * 2.5))
			# Elements draw on top of the translucent panel fills, so their
			# translucency stacks with the panel's: with fill alpha `a` the
			# element region ends up (1 - a/255) as transparent as the bare
			# panel — e.g. 115 keeps ~55% extra opacity over the panel while
			# still letting the art through
			element_alpha = 115
		# Clamp against the theme's own alpha rather than assigning outright,
		# so a fill the theme deliberately made translucent stays that way
		for name, colour in panel_colours:
			colour.a = min(colours.base_alpha.get(name, 255), panel_alpha)
		# At frosted high strength the tracklist gets hard to read over busy
		# art; keep its panel a touch more opaque than the others
		if prefs.art_bg and prefs.art_bg_frosted and prefs.art_bg_stronger >= 3:
			colours.playlist_panel_background.a = min(
				colours.base_alpha.get("playlist_panel_background", 255), panel_alpha + 20)
		for name, colour in element_colours:
			colour.a = min(colours.base_alpha.get(name, 255), element_alpha)

		# The frosted looks let the art show through the visualizer backing
		# too (the vis fills draw with replace-blend so this doesn't stack)
		colours.vis_bg.a = element_alpha if prefs.art_bg_frosted else 255

		# The window-transparency styles set their own panel alphas at theme
		# (re)load; don't clobber them back to opaque here
		if not prefs.art_bg and prefs.transparent_mode:
			colours.apply_transparency(full=prefs.transparent_mode == 2)

		# -----

		# Adjust for for compact window sizes ----
		if (prefs.always_art_header or (w < 600 * gui.scale and not gui.rsp and prefs.art_in_top_panel)) and not prefs.album_mode:
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
		if w < 750 * gui.scale and prefs.album_mode:
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
				self.artist_info_box.get_data(self.artist_info_box.artist_on)
			gui.last_artist_panel_height = gui.artist_panel_height

		# if w / h == 16 / 9:
		#     logging.info("YEP")
		# elif w / h < 16 / 9:
		#     logging.info("too low")
		# else:
		#     logging.info("too high")
		#logging.info((w, h))

		# input.mouse_click = False

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
		mini_signal_vis = gui.mode == GuiMode.MINI and prefs.mini_mode_mode == MiniModeMode.SIGNAL

		if ((gui.combo_mode and gui.showcase_mode and prefs.showcase_vis)
				or (gui.custom_mode and gui.vis4_in_widget)) \
				and gui.mode != GuiMode.MINI and prefs.backend == Backend.PHAZOR:
			gui.vis = 4
			gui.turbo = True
		elif mini_signal_vis:
			gui.vis = 2 if prefs.backend == Backend.PHAZOR else 0
			gui.turbo = True
		elif gui.vis_want == 0:
			gui.turbo = False
			gui.vis = 0
		else:
			gui.vis = gui.vis_want
			if gui.vis > 0:
				gui.turbo = True

		# The spectrogram widget feeds from its own C path (get_spectrum_hires,
		# separate FFT buffers) so it runs alongside whichever gui.vis was chosen
		# above rather than replacing it — it just needs the vis thread active.
		if gui.custom_mode and gui.spectrogram_in_widget \
				and gui.mode != GuiMode.MINI and prefs.backend == Backend.PHAZOR:
			gui.turbo = True

		# Disable vis when in compact view
		if ((gui.mode == GuiMode.MINI and not mini_signal_vis) or gui.top_bar_mode2):  # or prefs.backend == Backend.GSTREAMER:
			if not gui.combo_mode:
				gui.vis = 0
				gui.turbo = False

		if gui.mode == GuiMode.MAIN:
			if not gui.maximized and not gui.lowered:
				gui.save_size[0] = self.logical_size[0]
				gui.save_size[1] = self.logical_size[1]

			self.bottom_bar1.update()

			# if system != "Windows":
			# 	if draw_border:
			# 		gui.panelY = 30 * gui.scale + 3 * gui.scale
			# 		self.top_panel.ty = 3 * gui.scale
			# 	else:
			# 		gui.panelY = 30 * gui.scale
			# 		self.top_panel.ty = 0

			if gui.set_bar and gui.set_mode:
				gui.playlist_top = gui.playlist_top_bk + gui.set_height - 6 * gui.scale
			else:
				gui.playlist_top = gui.playlist_top_bk

			if gui.artist_info_panel:
				gui.playlist_top += gui.artist_panel_height

			gui.offset_extra = 0
			if self.draw_border and not prefs.left_window_control:
				offset = 61 * gui.scale
				if not self.draw_min_button:
					offset -= 35 * gui.scale
				if self.draw_max_button:
					offset += 33 * gui.scale
				if gui.macstyle:
					offset = 24
					if self.draw_min_button:
						offset += 20
					if self.draw_max_button:
						offset += 20
					offset = round(offset * gui.scale)
				gui.offset_extra = offset

			gui.album_v_slide_value = round(50 * gui.scale)
			if gui.gallery_show_text:
				gui.album_h_gap = 30 * gui.scale
				gui.album_v_gap = 66 * gui.scale
			else:
				gui.album_h_gap = 30 * gui.scale
				gui.album_v_gap = 25 * gui.scale

			if prefs.thin_gallery_borders:
				if gui.gallery_show_text:
					gui.album_h_gap = 20 * gui.scale
					gui.album_v_gap = 55 * gui.scale
				else:
					gui.album_h_gap = 17 * gui.scale
					gui.album_v_gap = 15 * gui.scale

				gui.album_v_slide_value = round(45 * gui.scale)

			if prefs.increase_gallery_row_spacing:
				gui.album_v_gap = round(gui.album_v_gap * 1.3)

			gui.gallery_scroll_field_left = window_size[0] - round(40 * gui.scale)

			# gui.spec_rect[0] = window_size[0] - gui.offset_extra - 90
			gui.spec1_rec.x = round(window_size[0] - gui.offset_extra - 90 * gui.scale)

			# gui.spec_x = window_size[0] - gui.offset_extra - 90

			gui.spec2_rec.x = round(window_size[0] - gui.spec2_rec.w - 10 * gui.scale - gui.offset_extra)

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

			if gui.side_drag and self.inp.key_shift_down:
				gui.art_unlock_ratio = True
				gui.art_max_ratio_lock = 5

			gui.rspw = gui.pref_rspw
			if prefs.album_mode:
				gui.rspw = gui.pref_gallery_w

			# Limit the right side panel width to height of area
			if gui.rsp and prefs.side_panel_layout == 0:
				if prefs.album_mode:
					pass
				elif not gui.art_unlock_ratio:
					if gui.rsp_full_lock and not gui.side_drag:
						gui.rspw = window_size[0]

					gui.rspw = min(gui.rspw, window_size[1] - gui.panelY - gui.panelBY)

			# Determine how wide the playlist need to be
			gui.rsp_on_left = bool(gui.rsp and prefs.side_panel_left and not prefs.album_mode)
			gui.lsp_x = 0
			gui.rsp_x = window_size[0] - gui.rspw
			gui.rsp_split_x = gui.rsp_x

			gui.plw = window_size[0]
			gui.playlist_left = 0
			if gui.lsp:
				gui.plw -= gui.lspw
				gui.playlist_left += gui.lspw
			if gui.rsp and gui.rsp_on_left:
				gui.rsp_x = gui.playlist_left
				gui.rsp_split_x = gui.rsp_x + gui.rspw
				gui.plw -= gui.rspw
				gui.playlist_left += gui.rspw
			elif gui.rsp:
				gui.plw -= gui.rspw

			# Shrink side panel if playlist gets too small
			if window_size[0] > 100 and not gui.hide_tracklist_in_gallery and gui.plw < 300 and gui.rsp:
				l = 0
				if gui.lsp:
					l = gui.lspw

				gui.rspw = max(window_size[0] - l - 300, 110)
						# if prefs.album_mode and window_size[0] > 750 * gui.scale:
						#     gui.pref_gallery_w = gui.rspw

			# Determine how wide the playlist need to be (again)
			gui.rsp_on_left = bool(gui.rsp and prefs.side_panel_left and not prefs.album_mode)
			gui.lsp_x = 0
			gui.rsp_x = window_size[0] - gui.rspw
			gui.rsp_split_x = gui.rsp_x

			gui.plw = window_size[0]
			gui.playlist_left = 0
			if gui.lsp:
				gui.plw -= gui.lspw
				gui.playlist_left += gui.lspw
			if gui.rsp and gui.rsp_on_left:
				gui.rsp_x = gui.playlist_left
				gui.rsp_split_x = gui.rsp_x + gui.rspw
				gui.plw -= gui.rspw
				gui.playlist_left += gui.rspw
			elif gui.rsp:
				gui.plw -= gui.rspw

			if window_size[0] < 630 * gui.scale:
				gui.compact_bar = True
			else:
				gui.compact_bar = False

			gui.request_tracklist_redraw()

			# Tracklist sizing ----------------------------------------------------
			left = gui.playlist_left
			width = gui.plw

			center_mode = True
			if gui.lsp or gui.rsp or gui.set_mode:
				center_mode = False

			if gui.set_mode and window_size[0] < 600:
				center_mode = False

			gui.highlight_left = 0
			highlight_width = width

			inset_left = gui.highlight_left + 23 * gui.scale
			inset_width = highlight_width - 32 * gui.scale

			if gui.lsp and not gui.rsp:
				inset_width -= 10 * gui.scale

			if gui.lsp:
				inset_left -= 10 * gui.scale
				inset_width += 10 * gui.scale

			if gui.rsp_on_left:
				inset_left -= 11 * gui.scale
				inset_width += 6 * gui.scale

			if center_mode:
				if gui.set_mode:
					gui.highlight_left = int(pow((window_size[0] / gui.scale * 0.005), 2) * gui.scale)
				else:
					gui.highlight_left = int(pow((window_size[0] / gui.scale * 0.01), 2) * gui.scale)

				if window_size[0] < 600 * gui.scale:
					gui.highlight_left = 3 * gui.scale

				highlight_width -= gui.highlight_left * 2
				inset_left = gui.highlight_left + 18 * gui.scale
				inset_width = highlight_width - 25 * gui.scale

			if window_size[0] < 600 and gui.lsp:
				inset_width = highlight_width - 18 * gui.scale

			gui.tracklist_center_mode = center_mode
			gui.tracklist_inset_left = inset_left
			gui.tracklist_inset_width = inset_width
			gui.tracklist_highlight_left = gui.highlight_left
			gui.tracklist_highlight_width = highlight_width

			if prefs.album_mode and gui.hide_tracklist_in_gallery:
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

				gui.tracklist_texture_rect = sdl3.SDL_FRect(0, 0, gui.max_window_tex, gui.max_window_tex)
				renderer = self.renderer
				sdl3.SDL_DestroyTexture(gui.tracklist_texture)
				sdl3.SDL_RenderClear(renderer)
				gui.tracklist_texture = sdl3.SDL_CreateTexture(
					renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET,
					gui.max_window_tex,
					gui.max_window_tex)

				sdl3.SDL_SetRenderTarget(renderer, gui.tracklist_texture)
				sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
				sdl3.SDL_RenderClear(renderer)
				# Premultiplied src-over: the texture holds premultiplied
				# content (see creation site in main())
				sdl3.SDL_SetTextureBlendMode(gui.tracklist_texture, sdl3.SDL_ComposeCustomBlendMode(
					sdl3.SDL_BLENDFACTOR_ONE,
					sdl3.SDL_BLENDFACTOR_ONE_MINUS_SRC_ALPHA,
					sdl3.SDL_BLENDOPERATION_ADD,
					sdl3.SDL_BLENDFACTOR_ONE,
					sdl3.SDL_BLENDFACTOR_ONE_MINUS_SRC_ALPHA,
					sdl3.SDL_BLENDOPERATION_ADD,
				))

				# sdl3.SDL_SetRenderTarget(renderer, gui.main_texture)
				# sdl3.SDL_RenderClear(renderer)

				sdl3.SDL_DestroyTexture(gui.main_texture)
				gui.main_texture = sdl3.SDL_CreateTexture(
					renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET,
					gui.max_window_tex,
					gui.max_window_tex)
				sdl3.SDL_SetTextureBlendMode(gui.main_texture, sdl3.SDL_BLENDMODE_BLEND)
				sdl3.SDL_SetRenderTarget(renderer, gui.main_texture)
				sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
				sdl3.SDL_SetRenderTarget(renderer, gui.main_texture)
				sdl3.SDL_RenderClear(renderer)

				sdl3.SDL_DestroyTexture(gui.main_texture_overlay_temp)
				gui.main_texture_overlay_temp = sdl3.SDL_CreateTexture(
					renderer, sdl3.SDL_PIXELFORMAT_ARGB8888,
					sdl3.SDL_TEXTUREACCESS_TARGET, gui.max_window_tex,
					gui.max_window_tex)
				sdl3.SDL_SetTextureBlendMode(gui.main_texture_overlay_temp, sdl3.SDL_BLENDMODE_BLEND)
				sdl3.SDL_SetRenderTarget(renderer, gui.main_texture_overlay_temp)
				sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
				sdl3.SDL_SetRenderTarget(renderer, gui.main_texture_overlay_temp)
				sdl3.SDL_RenderClear(renderer)

			self.update_set()

		if prefs.art_bg:
			self.thread_manager.ready("style")

	def test_show_add_home_music(self) -> None:
		self.gui.add_music_folder_ready = True

		if self.music_directory is None:
			self.gui.add_music_folder_ready = False
			return

		music_path = os.path.normpath(str(self.music_directory))

		for item in self.pctl.multi_playlist:
			if any(os.path.normpath(path) == music_path for path in item.last_folder):
				self.gui.add_music_folder_ready = False
				break

	def active_menu(self) -> Menu | None:
		"""The context menu currently being shown, if any."""
		for menu in Menu.instances:
			if menu.active and Menu.switch == menu.id:
				return menu
		return None

	def menu_popup_for_window(self, window_id: int):
		"""Return the menu popup (main or submenu) owning window_id, else None."""
		for popup in (self.menu_popup, self.submenu_popup):
			if popup is not None and popup.visible and popup.window is not None and popup.window_id() == window_id:
				return popup
		return None

	def _destroy_secondary(self, popup) -> None:
		"""Destroy a SecondaryWindow, dropping its icon textures from the caches.

		Destroying (not hiding) removes the window as an OS event target so it
		can't keep an event grab; the per-renderer asset textures must be dropped
		first so nothing holds a dangling handle a future renderer could collide
		with.
		"""
		if popup is None:
			return
		if popup.renderer is not None:
			self._forget_renderer_textures(popup.renderer)
		popup.destroy()

	def close_submenu_popup(self) -> None:
		"""Destroy just the submenu popup window (the main menu stays open)."""
		if self.submenu_popup is None:
			return
		if self.active_pointer_window is self.submenu_popup:
			self.active_pointer_window = self.menu_popup
		self._destroy_secondary(self.submenu_popup)
		self.submenu_popup = None

	def close_menu_popup(self) -> None:
		"""Destroy both menu popup windows and reset main input."""
		if self.menu_popup is None and self.submenu_popup is None:
			return
		self._destroy_secondary(self.submenu_popup)
		self.submenu_popup = None
		self._destroy_secondary(self.menu_popup)
		self.menu_popup = None
		self.active_pointer_window = None
		self.refresh_main_mouse_position()

	def _forget_renderer_textures(self, renderer) -> None:
		from tauon.t_modules.t_window import renderer_key
		key = renderer_key(renderer)
		for asset in (*LoadImageAsset.assets, *WhiteModImageAsset.assets):
			alt = getattr(asset, "_alt_textures", None)
			if alt is not None:
				alt.pop(key, None)

	def refresh_main_mouse_position(self) -> None:
		"""Re-sync inp.mouse_position to the real cursor location in the main window.

		While a menu popup is open the cursor is over the popup, so the main
		window receives no motion events and inp.mouse_position goes stale. When
		the menu closes by clicking an item (no main-window motion follows) the
		main UI would keep that stale position until the mouse next moves. The
		global cursor position is focus-independent, so (global - main window
		origin) scaled points->pixels gives the correct main-window position
		regardless of where the (possibly compositor-repositioned) popup was.
		"""
		gx, gy = ctypes.c_float(0), ctypes.c_float(0)
		sdl3.SDL_GetGlobalMouseState(ctypes.byref(gx), ctypes.byref(gy))
		wx, wy = ctypes.c_int(0), ctypes.c_int(0)
		sdl3.SDL_GetWindowPosition(self.t_window, ctypes.byref(wx), ctypes.byref(wy))
		logical = self.bag.logical_size
		scale = (self.window_size[0] / logical[0]) if logical[0] else 1.0
		self.inp.mouse_position[0] = int((gx.value - wx.value) * scale)
		self.inp.mouse_position[1] = int((gy.value - wy.value) * scale)

	def draw_popup_menus(self) -> None:
		"""Render context menus, in their own popup window or inline.

		Replaces the inline `for instance in Menu.instances: instance.render()`
		pass. Each menu's render() is still called every frame (it drives click
		handling and close logic and is a no-op when inactive). A menu that fits
		in the window (menu.use_popup is False) is drawn inline in the main
		window as before; one that would spill outside is pointed at its own
		popup window(s) instead.
		"""
		from tauon.t_modules.t_window import SecondaryWindow

		menu = self.active_menu()

		# Inline menus (and the no-menu case) render straight into the main
		# window; any popup windows from a previous popup menu are torn down.
		if menu is None or not menu.use_popup:
			for instance in Menu.instances:
				instance.render()
			self.close_menu_popup()  # no-op if nothing is open
			return

		# While a menu is popped out the cursor is over the popup window, so
		# main-window motion events stop and inp.mouse_position would freeze.
		# Track the real cursor (in main-window coords) from the global pointer
		# so menu-item callbacks that read inp.mouse_position - e.g. positioning
		# the rename box - get a live value. The menu itself hit-tests against
		# the popup-local pointer, so this does not affect menu interaction.
		self.refresh_main_mouse_position()

		if self.menu_popup is None:
			self.menu_popup = SecondaryWindow(self, focusable=False)
			self.active_pointer_window = self.menu_popup

		popup = self.menu_popup
		w, h = menu.popup_size()

		# Bottom-anchored menus (e.g. the bottom-panel playback menu) open upward:
		# the anchor marks the menu's bottom edge, so the window top is anchor - h.
		main_top_y = menu.popup_anchor[1] - h if menu.popup_bottom_anchor else menu.popup_anchor[1]

		if not popup.show(w, h, menu.popup_anchor[0], main_top_y):
			# Popup unavailable (creation failed): fall back to drawing the menu
			# inline in the main window, anchored where it was requested.
			menu.popup_window = None
			menu.pos = [menu.popup_anchor[0], main_top_y]
			for instance in Menu.instances:
				instance.render()
			return

		# Active submenu: render it first, into its own window beside the parent
		# item, so a click on a submenu item is consumed before the main menu's
		# close logic resets the click flag. sub_active/sub_y_position reflect the
		# previous frame's main render (one-frame lag, as before).
		if menu.sub_active > -1:
			if self.submenu_popup is None:
				self.submenu_popup = SecondaryWindow(self, focusable=False)
			sub = self.submenu_popup
			sw, sh = menu.submenu_size()
			sx = menu.popup_anchor[0] + menu.w
			sy = main_top_y + menu.sub_y_position
			if sub.show(sw, sh, int(sx), int(sy)):
				sub.begin_frame()
				menu.popup_window = sub
				menu.render_submenu()
				menu.popup_window = None
				sub.end_frame()
		elif self.submenu_popup is not None:
			self.close_submenu_popup()

		# Main column.
		popup.begin_frame()
		menu.popup_window = popup
		for instance in Menu.instances:
			instance.render()
		menu.popup_window = None
		popup.end_frame()

		# The menu may have closed itself during render() (item clicked / esc).
		if not menu.active:
			self.close_menu_popup()

	def is_level_zero(self, include_menus: bool = True) -> bool:
		if include_menus:
			for menu in Menu.instances:
				if menu.active:
					return False

		return not self.gui.rename_folder_box \
			and not self.gui.track_box \
			and not self.rename_track_box.active \
			and not self.radiobox.active \
			and not self.pref_box.enabled \
			and not self.gui.quick_search_mode \
			and not self.gui.rename_playlist_box \
			and not self.search_over.active \
			and not self.milk_choose.active \
			and not self.gui.box_over \
			and not self.trans_edit_box.active

	def get_radio_art(self) -> None:
		if self.radiobox.loaded_url in self.radiobox.websocket_source_urls:
			return
		if "ggdrasil" in self.radiobox.playing_title:
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
						if self.pctl.radio_image_bin:
							self.pctl.radio_image_bin.close()
							self.pctl.radio_image_bin = None
						self.pctl.radio_image_bin = io.BytesIO(art_response.content)
						self.pctl.radio_image_bin.seek(0)
						self.radiobox.dummy_track.art_url_key = "ok"
				self.pctl.update_tag_history()
		elif "gensokyoradio.net" in self.radiobox.loaded_url:
			response = requests.get("https://gensokyoradio.net/api/station/playing/", timeout=10)

			if response.status_code == 200:
				d = json.loads(response.text)
				song_info = d.get("SONGINFO")
				if song_info:
					self.radiobox.dummy_track.artist = song_info.get("ARTIST", "")
					self.radiobox.dummy_track.title = song_info.get("TITLE", "")
					self.radiobox.dummy_track.album = song_info.get("ALBUM", "")

				misc = d.get("MISC")
				if misc:
					art = misc.get("ALBUMART")
					if art:
						art_url = "https://gensokyoradio.net/images/albums/500/" + art
						art_response = requests.get(art_url, timeout=10)
						if art_response.status_code == 200:
							if self.pctl.radio_image_bin:
								self.pctl.radio_image_bin.close()
								self.pctl.radio_image_bin = None
							self.pctl.radio_image_bin = io.BytesIO(art_response.content)
							self.pctl.radio_image_bin.seek(0)
							self.radiobox.dummy_track.art_url_key = "ok"
				self.pctl.update_tag_history()

		elif "radio.plaza.one" in self.radiobox.loaded_url:
			time.sleep(3)
			logging.info("Fetching plaza art")
			response = requests.get("https://api.plaza.one/status", timeout=10)
			if response.status_code == 200:
				d = json.loads(response.text)
				if "song" in d:
					tr = d["song"]["length"] - d["song"]["position"]
					tr += 1
					tr = max(tr, 10)
					self.pctl.radio_poll_timer.force_set(tr * -1)

					if "artist" in d["song"]:
						self.radiobox.dummy_track.artist = d["song"]["artist"]
					if "title" in d["song"]:
						self.radiobox.dummy_track.title = d["song"]["title"]
					if "album" in d["song"]:
						self.radiobox.dummy_track.album = d["song"]["album"]
					if "artwork_src" in d["song"]:
						art_url = d["song"]["artwork_src"]
						art_response = requests.get(art_url, timeout=10)
						if art_response.status_code == 200:
							if self.pctl.radio_image_bin:
								self.pctl.radio_image_bin.close()
								self.pctl.radio_image_bin = None
							self.pctl.radio_image_bin = io.BytesIO(art_response.content)
							self.pctl.radio_image_bin.seek(0)
							self.radiobox.dummy_track.art_url_key = "ok"
					self.pctl.update_tag_history()

		# Failure
		elif self.pctl.radio_image_bin:
			self.pctl.radio_image_bin.close()
			self.pctl.radio_image_bin = None

		self.gui.clear_image_cache_next += 1

	def auto_name_pl(self, target_pl: int) -> None:
		if not self.pctl.multi_playlist[target_pl].playlist_ids:
			return

		albums:  list[str] = []
		artists: list[str] = []
		parents: list[str] = []

		track = None

		for index in self.pctl.multi_playlist[target_pl].playlist_ids:
			track = self.pctl.get_track(index)
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

		self.pctl.multi_playlist[target_pl].title = nt

	def get_object(self, index: int) -> TrackClass:
		return self.pctl.master_library[index]

	def update_title_do(self) -> None:
		if self.pctl.playing_state != PlayingState.STOPPED:
			if len(self.pctl.track_queue) > 0:
				line = self.pctl.master_library[self.pctl.track_queue[self.pctl.queue_step]].artist + " - " + \
					self.pctl.master_library[self.pctl.track_queue[self.pctl.queue_step]].title
				# line += "   : :   Tauon Music Box"
				line = line.encode("utf-8")
				sdl3.SDL_SetWindowTitle(self.t_window, line)
		else:
			line = "Tauon Music Box"
			line = line.encode("utf-8")
			sdl3.SDL_SetWindowTitle(self.t_window, line)

	def open_encode_out(self) -> None:
		if not self.prefs.encoder_output.exists():
			self.prefs.encoder_output.mkdir()
		if self.windows:
			subprocess.Popen(["explorer", self.prefs.encoder_output])
		elif self.macos:
			subprocess.Popen(["open", self.prefs.encoder_output])
		else:
			subprocess.Popen(["xdg-open", self.prefs.encoder_output])

	def g_open_encode_out(self, _a, _b, _c) -> None:
		self.open_encode_out()

	def hide_set_bar(self) -> None:
		self.gui.set_bar = False
		self.gui.update_layout = True
		self.gui.request_tracklist_redraw()

	def show_set_bar(self) -> None:
		self.gui.set_bar = True
		self.gui.update_layout = True
		self.gui.request_tracklist_redraw()

	def force_album_view(self) -> None:
		self.toggle_album_mode(force_on=True)

	def enter_combo(self) -> None:
		if not self.gui.combo_mode:
			self.gui.combo_was_album = self.prefs.album_mode
			self.gui.showcase_mode = False
			self.gui.radio_view = False
			if self.prefs.album_mode:
				self.toggle_album_mode()
			if self.gui.rsp:
				self.gui.rsp = False
			self.gui.combo_mode = True
			self.gui.update_layout = True

	def exit_combo(self, restore: bool = False) -> None:
		if self.prefs.shuffle_lock and not restore:
			self.toggle_shuffle_layout()
			return
		if self.gui.combo_mode:
			if self.gui.combo_was_album and restore:
				self.force_album_view()
			self.gui.showcase_mode = False
			self.gui.radio_view = False
			if self.prefs.prefer_side:
				self.gui.rsp = True
			self.gui.update_layout = True
			self.gui.combo_mode = False
			self.gui.was_radio = False

	def enter_showcase_view(self, track_id: int | None = None, timed_lyrics_edit: bool = False) -> None:
		if not self.gui.combo_mode:
			self.enter_combo()
			self.gui.was_radio = False
		self.gui.timed_lyrics_edit_view = timed_lyrics_edit
		self.gui.showcase_mode = True
		self.gui.radio_view = False
		if track_id is None or self.pctl.playing_object() is None or self.pctl.playing_object().index == track_id:
			pass
		else:
			self.gui.force_showcase_index = track_id
		self.inp.mouse_click = False
		self.gui.update_layout = True

	def enter_radio_view(self) -> None:
		if not self.gui.combo_mode:
			self.enter_combo()
		self.gui.showcase_mode = False
		self.gui.radio_view = True
		self.inp.mouse_click = False
		self.gui.update_layout = True

	def enter_timed_lyrics_edit(self, track: TrackClass) -> None:
		self.enter_showcase_view(track.index, timed_lyrics_edit=True)

	def standard_size(self) -> None:
		self.prefs.album_mode = False
		self.gui.rsp = True
		self.window_size = self.window_default_size
		sdl3.SDL_SetWindowSize(self.t_window, c_int(self.logical_size[0]), c_int(self.logical_size[1]))

		self.gui.rspw = 80 + int(self.window_size[0] * 0.18)
		self.gui.update_layout = True
		self.album_mode_art_size = 130
		# self.clear_img_cache()

	def path_stem_to_playlist(self, path: str, title: str) -> None:
		"""Used with gallery power bar"""
		playlist = []

		# Hack for networked tracks
		if path.lstrip("/") == title:
			for item in self.pctl.multi_playlist[self.pctl.active_playlist_viewing].playlist_ids:
				if title == os.path.basename(self.pctl.master_library[item].parent_folder_path):
					playlist.append(item)
		else:
			for item in self.pctl.multi_playlist[self.pctl.active_playlist_viewing].playlist_ids:
				if path in self.pctl.master_library[item].parent_folder_path:
					playlist.append(item)

		self.pctl.multi_playlist.append(self.pl_gen(
			title=os.path.basename(title).upper(),
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))

		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "s\"" + self.pctl.multi_playlist[self.pctl.active_playlist_viewing].title + "\" f\"" + path + "\""

		self.pctl.switch_playlist(len(self.pctl.multi_playlist) - 1)

	def activate_info_box(self) -> None:
		self.fader.rise()
		self.pref_box.enabled = True

	def activate_radio_box(self) -> None:
		self.radiobox.active = True
		self.radiobox.radio_field.clear()
		self.radiobox.radio_field_title.clear()

	def new_playlist_colour_callback(self) -> ColourRGBA:
		if self.gui.radio_view:
			return ColourRGBA(120, 90, 245, 255)
		return ColourRGBA(237, 80, 221, 255)

	def new_playlist_deco(self) -> Decorator:
		text = _("New Radio List") if self.gui.radio_view else _("New Playlist")
		return Decorator(self.colours.menu_text, self.colours.menu_background, text)

	def clean_db_show_test(self, _unused: int) -> bool:
		return self.gui.suggest_clean_db

	def clean_db_fast(self) -> None:
		keys = set(self.pctl.master_library.keys())
		for pl in self.pctl.multi_playlist:
			keys -= set(pl.playlist_ids)
		for item in keys:
			self.pctl.purge_track(item, fast=True)
		self.show_message(_("Done! {N} old items were removed.").format(N=len(keys)), mode="done")
		self.gui.suggest_clean_db = False

	def clean_db_deco(self) -> Decorator:
		return Decorator(self.colours.menu_text, ColourRGBA(30, 150, 120, 255), _("Clean Database!"))

	def show_import_music(self, _unused: int) -> bool:
		return self.gui.add_music_folder_ready

	def import_music(self) -> None:
		pl = self.pl_gen(_("Music"))
		pl.last_folder = [str(self.music_directory)]
		self.pctl.multi_playlist.append(pl)
		load_order = LoadClass()
		load_order.target = str(self.music_directory)
		load_order.playlist = pl.uuid_int
		self.load_orders.append(load_order)
		self.pctl.switch_playlist(len(self.pctl.multi_playlist) - 1)
		self.gui.add_music_folder_ready = False

	def clip_aar_al(self, index: int) -> None:
		if self.pctl.master_library[index].album_artist == "":
			line = self.pctl.master_library[index].artist + " - " + self.pctl.master_library[index].album
		else:
			line = self.pctl.master_library[index].album_artist + " - " + self.pctl.master_library[index].album
		sdl3.SDL_SetClipboardText(line.encode("utf-8"))

	def ser_gen_thread(self, tr: TrackClass) -> None:
		s_artist = tr.artist
		s_title = tr.title

		if s_artist in self.prefs.lyrics_subs:
			s_artist = self.prefs.lyrics_subs[s_artist]
		if s_title in self.prefs.lyrics_subs:
			s_title = self.prefs.lyrics_subs[s_title]

		line = genius(s_artist, s_title, return_url=True)

		r = requests.head(line, timeout=10)

		if r.status_code != 404:
			webbrowser.open(line, new=2, autoraise=True)
			self.gui.message_box = False
		else:
			line = "https://genius.com/search?q=" + urllib.parse.quote(f"{s_artist} {s_title}")
			webbrowser.open(line, new=2, autoraise=True)
			self.gui.message_box = False

	def ser_gen(self, ref: MenuTrackRef, get_lyrics: bool = False) -> None:
		tr = self.pctl.get_track(ref.track_id)
		if len(tr.title) < 1:
			return

		self.show_message(_("Searching..."))

		shoot = threading.Thread(target=self.ser_gen_thread, args=[tr])
		shoot.daemon = True
		shoot.start()

	def ser_wiki(self, ref: MenuTrackRef) -> None:
		index = ref.track_id
		if len(self.pctl.master_library[index].artist) < 2:
			return
		line = "https://en.wikipedia.org/wiki/Special:Search?search=" + urllib.parse.quote(self.pctl.master_library[index].artist)
		webbrowser.open(line, new=2, autoraise=True)

	def clip_ar_tr(self, ref: MenuTrackRef) -> None:
		index = ref.track_id
		line = self.pctl.master_library[index].artist + " - " + self.pctl.master_library[index].title
		sdl3.SDL_SetClipboardText(line.encode("utf-8"))

	def tidal_copy_album(self, ref: MenuTrackRef) -> None:
		index = ref.track_id
		t = self.pctl.master_library.get(index)
		if t and t.file_ext == "TIDAL":
			id = t.tidal_album
			if id:
				url = "https://listen.tidal.com/album/" + str(id)
				copy_to_clipboard(url)

	def is_tidal_track(self, ref: MenuTrackRef) -> bool:
		return self.pctl.master_library[ref.track_id].file_ext == "TIDAL"

	def drop_tracks_to_new_playlist(self, track_list: list[int], _hidden: bool = False) -> None:
		pl = self.new_playlist(switch=False)
		albums = []
		artists = []
		for item in track_list:
			albums.append(self.pctl.get_track(self.pctl.default_playlist[item]).album)
			artists.append(self.pctl.get_track(self.pctl.default_playlist[item]).artist)
			self.pctl.multi_playlist[pl].playlist_ids.append(self.pctl.default_playlist[item])

		if len(track_list) > 1:
			if len(albums) > 0 and albums.count(albums[0]) == len(albums):
				track = self.pctl.get_track(self.pctl.default_playlist[track_list[0]])
				artist = track.artist
				if track.album_artist:
					artist = track.album_artist
				self.pctl.multi_playlist[pl].title = artist + " - " + albums[0][:50]

		elif len(track_list) == 1 and artists:
			self.pctl.multi_playlist[pl].title = artists[0]

		if self.tree_view_box.dragging_name:
			self.pctl.multi_playlist[pl].title = self.tree_view_box.dragging_name
		self.dropped_playlist = pl
		self.pctl.notify_database_changed()

	def queue_deco(self) -> Decorator:
		line_colour = self.colours.menu_text if len(self.pctl.force_queue) > 0 else self.colours.menu_text_disabled
		return Decorator(line_colour, self.colours.menu_background, None)

	def gstreamer_test(self, _unused) -> bool:
		# return True
		return self.prefs.backend == Backend.GSTREAMER

	def _build_search_results(
		self,
		query_text: str,
		*,
		all_folders: bool = False,
		cancel_check: Callable[[], bool] | None = None,
	) -> list[list[int | str | None]]:
		search_magic_local = search_magic
		search_magic_any_local = search_magic_any
		genre_correct_local = genre_correct
		get_year_from_string_local = get_year_from_string
		use_sep_genre_multi = self.prefs.sep_genre_multi
		search_string_cache = self.search_string_cache
		search_dia_string_cache = self.search_dia_string_cache
		search_field_cache = self.search_field_cache
		search_dia_field_cache = self.search_dia_field_cache
		pctl = self.pctl
		master_library = pctl.master_library
		multi_playlist = pctl.multi_playlist
		temp_results: list[list[int | str | None] | None] = []

		artists = {}
		albums = {}
		genres = {}
		metas = {}
		composers = {}
		years = {}
		tracks = set()

		br = 0
		o_text = query_text.lower().replace("-", "")
		if o_text in ("the", "and"):
			return []

		dia_mode = o_text.isascii()

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
		if self.use_cc and CJK_SEARCH_PATTERN.search(o_text):
			s2t, t2s = self._get_opencc_converters()
			if s2t and t2s:
				t_cn = s2t.convert(o_text)
				s_cn = t2s.convert(o_text)
				cn_mode = True

		s_text = o_text
		searched = set()
		s_text_nospace = s_text.replace(" ", "")

		for playlist in multi_playlist:
			for track in playlist.playlist_ids:
				if track in searched:
					continue
				searched.add(track)

				if cn_mode:
					s_text = o_text
					s_text_nospace = s_text.replace(" ", "")
					cache_string = search_string_cache.get(track)
					if cache_string:
						if search_magic_any_local(s_text, cache_string):
							pass
						elif search_magic_any_local(t_cn, cache_string):
							s_text = t_cn
							s_text_nospace = s_text.replace(" ", "")
						elif search_magic_any_local(s_cn, cache_string):
							s_text = s_cn
							s_text_nospace = s_text.replace(" ", "")

				if dia_mode:
					cache_string = search_dia_string_cache.get(track)
					if cache_string is not None and not search_magic_any_local(s_text, cache_string):
						continue
				else:
					cache_string = search_string_cache.get(track)
					if cache_string is not None and not search_magic_any_local(s_text, cache_string):
						continue

				t = master_library[track]
				fields = search_field_cache.get(track)
				if fields is None:
					title = t.title.lower().replace("-", "")
					artist = t.artist.lower().replace("-", "")
					album_artist = t.album_artist.lower().replace("-", "")
					composer = t.composer.lower().replace("-", "")
					date = t.date.lower().replace("-", "")
					album = t.album.lower().replace("-", "")
					genre = t.genre.lower().replace("-", "")
					genre_nospace = genre.replace(" ", "")
					filename = t.filename.lower().replace("-", "")
					sartist = (t.artist_sort if t.artist_sort is not None else "").lower()
					stem_raw = os.path.dirname(t.parent_folder_path)
					stem_search = stem_raw.lower().replace("-", "")
					lyrics = t.lyrics.lower().replace("-", "") + " " + t.synced.lower().replace("-", "")
					search_field_cache[track] = (
						title,
						artist,
						album_artist,
						composer,
						date,
						album,
						genre,
						genre_nospace,
						filename,
						sartist,
						stem_search,
						stem_raw,
						lyrics,
					)
				else:
					title, artist, album_artist, composer, date, album, genre, genre_nospace, filename, sartist, stem_search, stem_raw, lyrics = fields

				if cache_string is None:
					if not dia_mode:
						search_string_cache[track] = title + artist + album_artist + composer + date + album + genre + sartist + filename + stem_search + lyrics

					if cn_mode:
						cache_string = search_string_cache.get(track)
						if cache_string:
							if search_magic_any_local(s_text, cache_string):
								pass
							elif search_magic_any_local(t_cn, cache_string):
								s_text = t_cn
								s_text_nospace = s_text.replace(" ", "")
							elif search_magic_any_local(s_cn, cache_string):
								s_text = s_cn
								s_text_nospace = s_text.replace(" ", "")

				if dia_mode:
					dia_fields = search_dia_field_cache.get(track)
					if dia_fields is None:
						d_title = unidecode(title)
						d_artist = unidecode(artist)
						d_album_artist = unidecode(album_artist)
						d_composer = unidecode(composer)
						d_album = unidecode(album)
						d_filename = unidecode(filename)
						d_sartist = unidecode(sartist)
						d_lyrics = unidecode(lyrics)
						search_dia_field_cache[track] = (
							d_title,
							d_artist,
							d_album_artist,
							d_composer,
							d_album,
							d_filename,
							d_sartist,
							d_lyrics,
						)
					else:
						d_title, d_artist, d_album_artist, d_composer, d_album, d_filename, d_sartist, d_lyrics = dia_fields

					title = d_title
					artist = d_artist
					album_artist = d_album_artist
					composer = d_composer
					album = d_album
					filename = d_filename
					sartist = d_sartist
					lyrics = d_lyrics

					if cache_string is None:
						search_dia_string_cache[track] = title + artist + album_artist + composer + date + album + genre + sartist + filename + stem_search + lyrics

				if len(s_text) > 2 and s_text in stem_search:
					if stem_raw in metas:
						metas[stem_raw] += 2
					else:
						temp_results.append([5, stem_raw, track, playlist.uuid_int, 0])
						metas[stem_raw] = 2

				if s_text_nospace in genre_nospace:
					if "/" in genre or "," in genre or ";" in genre:
						for split in genre.replace(";", "/").replace(",", "/").split("/"):
							if s_text_nospace in split.replace(" ", ""):
								split = genre_correct_local(split)
								if use_sep_genre_multi:
									split += "+"
								if split in genres:
									genres[split] += 3
								else:
									temp_results.append([3, split, track, playlist.uuid_int, 0])
									genres[split] = 1
									if split.replace(" ", "") == genre_nospace:
										genres[split] += 10000
					else:
						name = genre_correct_local(t.genre)
						if name in genres:
							genres[name] += 3
						else:
							temp_results.append([3, name, track, playlist.uuid_int, 0])
							genres[name] = 1
							if s_text_nospace == genre_nospace:
								genres[name] += 10000

				if s_text in composer:
					if t.composer in composers:
						composers[t.composer] += 2
					else:
						temp_results.append([6, t.composer, track, playlist.uuid_int, 0])
						composers[t.composer] = 2

				if s_text in date:
					year = get_year_from_string_local(date)
					if year:
						if year in years:
							years[year] += 1
						else:
							temp_results.append([7, year, track, playlist.uuid_int, 0])
							years[year] = 1000

				if search_magic_local(s_text, title + " " + artist + " " + filename + " " + album + " " + sartist + " " + album_artist):
					if t.artists:
						for a in t.artists:
							a_lower = a.lower()
							if search_magic_local(s_text, a_lower):
								value = 1
								if a_lower.startswith(s_text):
									value = 5

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

					elif search_magic_local(s_text, artist + sartist):
						value = 1
						if artist.startswith(s_text):
							value = 10

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

					elif search_magic_local(s_text, album_artist):
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

					if search_magic_local(s_text, artist + sartist) or search_magic_local(s_text, album):
						if t.album in albums:
							albums[t.album] += 3
						else:
							temp_results.append([1, t.album, track, playlist.uuid_int, 0])
							albums[t.album] = 3

					elif search_magic_any_local(s_text, artist + sartist) and search_magic_any_local(s_text, album):
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
				else:
					val = search_magic_beefy(s_text, lyrics)
					if val > 90:
						if t not in tracks:
							temp_results.append([9, t.title, track, playlist.uuid_int, val-100])
							tracks.add(t)

				br += 1
				if br > 800:
					time.sleep(0.005)  # Throttle thread
					br = 0
					if cancel_check and cancel_check():
						break

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

		for i, item in enumerate(temp_results):
			if item[0] == 0:
				temp_results[i][4] = artists[item[1]]
			if item[0] == 1:
				temp_results[i][4] = albums[item[1]]
			if item[0] == 3:
				temp_results[i][4] = genres[item[1]]
			if item[0] == 5:
				temp_results[i][4] = metas[item[1]]
				if not all_folders and metas[item[1]] < 42:
					temp_results[i] = None
			if item[0] == 6:
				temp_results[i][4] = composers[item[1]]
			if item[0] == 7:
				temp_results[i][4] = years[item[1]]
			# 8 is playlists

		temp_results[:] = [item for item in temp_results if item is not None]
		results = sorted(temp_results, key=lambda x: x[4], reverse=True)

		i = 0
		for playlist in multi_playlist:
			if search_magic_local(s_text, playlist.title.lower()):
				item = [8, playlist.title, None, playlist.uuid_int, 100000]
				results.insert(0, item)
				i += 1
				if i > 3:
					break

		return results

	def _get_opencc_converters(self):
		"""Return thread-local OpenCC converters to avoid re-instantiation in hot paths."""
		if not self.use_cc:
			return None, None

		s2t = getattr(self._opencc_local, "s2t", None)
		t2s = getattr(self._opencc_local, "t2s", None)
		if s2t and t2s:
			return s2t, t2s

		try:
			s2t = opencc.OpenCC("s2t")
			t2s = opencc.OpenCC("t2s")
		except Exception:
			logging.exception("Failed to initialize OpenCC converters")
			self.use_cc = False
			return None, None

		self._opencc_local.s2t = s2t
		self._opencc_local.t2s = t2s
		return s2t, t2s

	def regenerate_playlist(self, pl: int = -1, silent: bool = False, id: int | None = None) -> None:
		if id is None and pl == -1:
			return

		if id is None:
			id = self.pctl.pl_to_id(pl)

		if pl == -1:
			pl = self.pctl.id_to_pl(id)
			if pl is None:
				return

		source_playlist = self.pctl.multi_playlist[pl].playlist_ids

		string = self.pctl.gen_codes.get(id)
		if not string:
			if not silent:
				self.show_message(_("This playlist has no generator"))
			return

		cmds, quotes, inquote = parse_generator(string)

		if inquote:
			self.gui.gen_code_errors = "close"
			return

		playlist = []
		selections: list[list[int]] = []
		errors = False
		selections_searched = 0
		search_results_cache: dict[tuple[str, bool], list[list[int | str | None]]] = {}

		def is_source_type(code: str | None) -> bool:
			return \
				code is None or \
				code == "" or \
				code.startswith((
					"self", "jelly", "plex", "tau", "air", "sal",
					"tpl", "tfa", "tft", "tar", "tmix"))

		def get_search_results(query: str, *, all_folders: bool = False) -> list[list[int | str | None]]:
			key = (query, all_folders)
			cached = search_results_cache.get(key)
			if cached is not None:
				return cached
			results = self._build_search_results(query, all_folders=all_folders)
			search_results_cache[key] = results
			return results

		def parse_minutes(value: str) -> float | None:
			if not value:
				return None
			try:
				return float(value) * 60
			except ValueError:
				return None

		#logging.info(cmds)
		#logging.info(quotes)

		self.pctl.regen_in_progress = True

		for i, cm in enumerate(cmds):
			quote = quotes[i]

			if cm.startswith("\"") and (cm.endswith((">", "<"))):
				cm_found = False

				for col in self.column_names:
					if quote.lower() == col.lower() or _(quote).lower() == col.lower():
						cm_found = True

						if cm[-1] == ">":
							self.sort_ass(0, invert=False, custom_list=playlist, custom_name=col)
						elif cm[-1] == "<":
							self.sort_ass(0, invert=True, custom_list=playlist, custom_name=col)
						break
				if cm_found:
					continue

			elif cm == "self":
				selections.append(self.pctl.multi_playlist[pl].playlist_ids)

			elif cm == "auto":
				pass

			elif cm.startswith("tpl\""):
				playlist.extend(self.tidal.playlist(quote, return_list=True))

			elif cm == "tfa":
				playlist.extend(self.tidal.fav_albums(return_list=True))

			elif cm == "tft":
				playlist.extend(self.tidal.fav_tracks(return_list=True))

			elif cm.startswith("tar\""):
				playlist.extend(self.tidal.artist(quote, return_list=True))

			elif cm.startswith("tmix\""):
				playlist.extend(self.tidal.mix(quote, return_list=True))

			elif cm == "plex":
				if not self.plex.scanning:
					playlist.extend(self.plex.get_albums(return_list=True))

			elif cm.startswith("jelly\""):
				if not self.jellyfin.scanning:
					playlist.extend(self.jellyfin.get_playlist(quote, return_list=True))

			elif cm == "jelly":
				if not self.jellyfin.scanning:
					playlist.extend(self.jellyfin.ingest_library(return_list=True))

			elif cm == "tau":
				if not self.tau.processing:
					playlist.extend(self.tau.get_playlist(self.pctl.multi_playlist[pl].title, return_list=True))

			elif cm == "air":
				if not self.subsonic.scanning:
					playlist.extend(self.subsonic.get_music3(return_list=True))

			elif cm == "a":
				if not selections and not selections_searched:
					for plist in self.pctl.multi_playlist:
						code = self.pctl.gen_codes.get(plist.uuid_int)
						if is_source_type(code):
							selections.append(plist.playlist_ids)

				temp = []
				for selection in selections:
					temp += selection

				playlist += list(OrderedDict.fromkeys(temp))
				selections.clear()

			elif cm == "cue":
				for i in reversed(range(len(playlist))):
					tr = self.pctl.get_track(playlist[i])
					if not tr.is_cue:
						del playlist[i]
				playlist = list(OrderedDict.fromkeys(playlist))

			elif cm == "today":
				d = datetime.date.today()
				for i in reversed(range(len(playlist))):
					tr = self.pctl.get_track(playlist[i])
					if tr.date[5:7] != f"{d:%m}" or tr.date[8:10] != f"{d:%d}":
						del playlist[i]
				playlist = list(OrderedDict.fromkeys(playlist))

			elif cm.startswith("com\""):
				for i in reversed(range(len(playlist))):
					tr = self.pctl.get_track(playlist[i])
					if quote not in tr.comment:
						del playlist[i]
				playlist = list(OrderedDict.fromkeys(playlist))

			elif cm.startswith("ext"):
				value = quote.upper()
				if value:
					if not selections:
						for plist in self.pctl.multi_playlist:
							selections.append(plist.playlist_ids)

					temp = []
					for selection in selections:
						for track in selection:
							tr = self.pctl.get_track(track)
							if tr.file_ext == value:
								temp.append(track)

					playlist += list(OrderedDict.fromkeys(temp))

			elif cm == "ypa":
				playlist = self.year_sort(0, playlist)

			elif cm == "tn":
				self.sort_track_2(0, playlist)

			elif cm == "ia>":
				playlist = self.gen_last_imported_folders(0, playlist)

			elif cm == "ia<":
				playlist = self.gen_last_imported_folders(0, playlist, reverse=False)

			elif cm == "m>":
				playlist = self.gen_last_modified(0, playlist)

			elif cm == "m<":
				playlist = self.gen_last_modified(0, playlist, reverse=False)

			elif cm in ("ly", "lyrics"):
				playlist = self.gen_lyrics(0, playlist)

			elif cm in ("l", "love", "loved"):
				playlist = self.gen_love(0, playlist)

			elif cm == "clr":
				selections.clear()

			elif cm in ("rv", "reverse"):
				playlist = self.gen_reverse(0, playlist)

			elif cm == "rva":
				playlist = self.gen_folder_reverse(0, playlist)

			elif cm == "rata>":

				playlist = self.gen_folder_top_rating(0, custom_list=playlist)

			elif cm == "rat>":
				def rat_key(track_id: int) -> int:
					return self.star_store.get_rating(track_id)

				playlist = sorted(playlist, key=rat_key, reverse=True)

			elif cm == "rat<":
				def rat_key(track_id: int) -> int:
					return self.star_store.get_rating(track_id)

				playlist = sorted(playlist, key=rat_key)

			elif cm[:4] == "rat=":
				value = cm[4:]
				try:
					value = float(value) * 2
					temp = []
					for item in playlist:
						if value == self.star_store.get_rating(item):
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
						if value > self.star_store.get_rating(item):
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
						if value < self.star_store.get_rating(item):
							temp.append(item)
					playlist = temp
				except Exception:
					logging.exception("Failed to get rating")
					errors = True

			elif cm == "rat":
				temp = []
				for item in playlist:
					# tr = pctl.get_track(item)
					if self.star_store.get_rating(item) > 0:
						temp.append(item)
				playlist = temp

			elif cm == "norat":
				temp = []
				for item in playlist:
					if self.star_store.get_rating(item) == 0:
						temp.append(item)
				playlist = temp

			elif cm == "d>":
				playlist = self.gen_sort_len(0, custom_list=playlist)

			elif cm == "d<":
				playlist = self.gen_sort_len(0, custom_list=playlist)
				playlist = list(reversed(playlist))

			elif cm[:2] == "d<":
				value = parse_minutes(cm[2:])
				if value is not None:
					for i in reversed(range(len(playlist))):
						tr = self.pctl.get_track(playlist[i])
						if not value > tr.length:
							del playlist[i]

			elif cm[:2] == "d>":
				value = parse_minutes(cm[2:])
				if value is not None:
					for i in reversed(range(len(playlist))):
						tr = self.pctl.get_track(playlist[i])
						if not value < tr.length:
							del playlist[i]

			elif cm == "path":
				self.sort_path_pl(0, custom_list=playlist)

			elif cm == "pa>":
				playlist = self.gen_folder_top(0, custom_list=playlist)

			elif cm == "pa<":
				playlist = self.gen_folder_top(0, custom_list=playlist)
				playlist = self.gen_folder_reverse(0, playlist)

			elif cm == "ad>":
				playlist = self.gen_folder_duration(0, custom_list=playlist)

			elif cm == "ad<":
				playlist = self.gen_folder_duration(0, custom_list=playlist, reverse=False)

			elif cm[:3] == "ad>":
				value = parse_minutes(cm[3:])
				if value is not None:
					temp: list[int] = []
					for album, duration in self.gen_folder_duration(0, get_sets=True, custom_list=playlist) or []:
						if duration > value:
							temp.extend(album)
					playlist = temp

			elif cm[:3] == "ad<":
				value = parse_minutes(cm[3:])
				if value is not None:
					temp: list[int] = []
					for album, duration in self.gen_folder_duration(0, get_sets=True, custom_list=playlist) or []:
						if duration < value:
							temp.extend(album)
					playlist = temp

			elif cm in ("pt>", "pc>"):
				playlist = self.gen_top_100(0, custom_list=playlist)

			elif cm in ("pt<", "pc<"):
				playlist = self.gen_top_100(0, custom_list=playlist)
				playlist = list(reversed(playlist))

			elif cm[:3] == "pt>":
				value = cm[3:]
				if value and value.isdigit():
					value = int(value)
					for i in reversed(range(len(playlist))):
						t_time = self.star_store.get(playlist[i])
						if t_time < value:
							del playlist[i]

			elif cm[:3] == "pt<":
				value = cm[3:]
				if value and value.isdigit():
					value = int(value)
					for i in reversed(range(len(playlist))):
						t_time = self.star_store.get(playlist[i])
						if t_time > value:
							del playlist[i]

			elif cm[:3] == "pc>":
				value = cm[3:]
				if value and value.isdigit():
					value = int(value)
					for i in reversed(range(len(playlist))):
						t_time = self.star_store.get(playlist[i])
						tr = self.pctl.get_track(playlist[i])
						# Use the same formula as for calculating Play count
						if tr.length < 1 or not value < t_time / (tr.length - 1):
							del playlist[i]

			elif cm[:3] == "pc<":
				value = cm[3:]
				if value and value.isdigit():
					value = int(value)
					for i in reversed(range(len(playlist))):
						t_time = self.star_store.get(playlist[i])
						tr = self.pctl.get_track(playlist[i])
						if tr.length > 0:
							# Use the same formula as for calculating Play count
							if not value > t_time / (tr.length - 1):
								del playlist[i]

			elif cm == "y<":
				playlist = self.gen_sort_date(0, False, playlist)

			elif cm == "y>":
				playlist = self.gen_sort_date(0, True, playlist)

			elif cm[:2] == "y=":
				value = cm[2:]
				if value:
					temp = []
					for item in playlist:
						if value in self.pctl.master_library[item].date:
							temp.append(item)
					playlist = temp

			elif cm[:3] == "y>=":
				value = cm[3:]
				if value and value.isdigit():
					value = int(value)
					temp = []
					for item in playlist:
						if self.pctl.master_library[item].date[:4].isdigit() and int(
								self.pctl.master_library[item].date[:4]) >= value:
							temp.append(item)
					playlist = temp

			elif cm[:3] == "y<=":
				value = cm[3:]
				if value and value.isdigit():
					value = int(value)
					temp = []
					for item in playlist:
						if self.pctl.master_library[item].date[:4].isdigit() and int(
								self.pctl.master_library[item].date[:4]) <= value:
							temp.append(item)
					playlist = temp

			elif cm[:2] == "y>":
				value = cm[2:]
				if value and value.isdigit():
					value = int(value)
					temp = []
					for item in playlist:
						if self.pctl.master_library[item].date[:4].isdigit() and int(self.pctl.master_library[item].date[:4]) > value:
							temp.append(item)
					playlist = temp

			elif cm[:2] == "y<":
				value = cm[2:]
				if value and value.isdigit():
					value = int(value)
					temp = []
					for item in playlist:
						if self.pctl.master_library[item].date[:4].isdigit() and int(self.pctl.master_library[item].date[:4]) < value:
							temp.append(item)
					playlist = temp

			elif cm in ("st", "rt", "r"):
				random.shuffle(playlist)

			elif cm in ("sf", "rf", "ra", "sa"):
				playlist = self.gen_folder_shuffle(0, custom_list=playlist)

			elif cm.startswith("n"):
				value = cm[1:]
				if value.isdigit():
					playlist = playlist[:int(value)]

			# SEARCH FOLDER
			elif cm.startswith("p\"") and len(cm) > 3:

				if not selections:
					for plist in self.pctl.multi_playlist:
						code = self.pctl.gen_codes.get(plist.uuid_int)
						if is_source_type(code):
							selections.append(plist.playlist_ids)

				results = get_search_results(quote, all_folders=True)
				found_name = ""
				for result in results:
					if result[0] == 5:
						found_name = result[1]
						break

				if not found_name or not isinstance(found_name, str):
					logging.info("No folder search result found")
					continue

				playlist += self.search_over.click_meta(found_name, get_list=True, search_lists=selections)

			# SEARCH GENRE
			elif (cm.startswith(('g"', 'gm"', 'g="'))) and len(cm) > 3:
				if not selections:
					for plist in self.pctl.multi_playlist:
						code = self.pctl.gen_codes.get(plist.uuid_int)
						if is_source_type(code):
							selections.append(plist.playlist_ids)

				g_search = quote.lower().replace("-", "")
				results = get_search_results(g_search)
				found_name = ""

				if cm.startswith("g=\""):
					for result in results:
						if result[0] == 3 and isinstance(result[1], str) and result[1].lower().replace("-", "") == g_search:
							found_name = result[1]
							break
				elif cm.startswith("g\"") or not self.prefs.sep_genre_multi:
					for result in results:
						if result[0] == 3 and isinstance(result[1], str):
							found_name = result[1]
							break
				elif cm.startswith("gm\""):
					for result in results:
						if result[0] == 3 and isinstance(result[1], str) and result[1].endswith("+"):
							found_name = result[1]
							break

				if not found_name:
					logging.warning("No genre search result found")
					continue

				playlist += self.search_over.click_genre(found_name, get_list=True, search_lists=selections)

			# SEARCH ARTIST
			elif cm.startswith("a\"") and len(cm) > 3 and cm != "auto":
				if not selections:
					for plist in self.pctl.multi_playlist:
						code = self.pctl.gen_codes.get(plist.uuid_int)
						if is_source_type(code):
							selections.append(plist.playlist_ids)

				results = get_search_results("artist " + quote)
				found_name = ""
				for result in results:
					if result[0] == 0:
						found_name = result[1]
						break

				if not found_name or not isinstance(found_name, str):
					logging.warning("No artist search result found")
					continue

				playlist += self.search_over.click_artist(found_name, get_list=True, search_lists=selections)

			elif cm.startswith("ff\""):
				for i in reversed(range(len(playlist))):
					tr = self.pctl.get_track(playlist[i])
					line = f"{tr.title} {tr.artist} {tr.album} {tr.fullpath} {tr.composer} {tr.comment} {tr.album_artist}".lower()

					if self.prefs.diacritic_search and all([ord(c) < 128 for c in quote]):
						line = str(unidecode(line))

					if not search_magic(quote.lower(), line):
						del playlist[i]

				playlist = list(OrderedDict.fromkeys(playlist))

			elif cm.startswith("fx\""):
				for i in reversed(range(len(playlist))):
					tr = self.pctl.get_track(playlist[i])
					line = " ".join(
						[tr.title, tr.artist, tr.album, tr.fullpath, tr.composer, tr.comment, tr.album_artist]).lower()
					if self.prefs.diacritic_search and all([ord(c) < 128 for c in quote]):
						line = str(unidecode(line))

					if search_magic(quote.lower(), line):
						del playlist[i]

			elif cm.startswith(('find"', 'f"', 'fs"')):
				if not selections:
					for plist in self.pctl.multi_playlist:
						code = self.pctl.gen_codes.get(plist.uuid_int)
						if is_source_type(code):
							selections.append(plist.playlist_ids)

				cooldown = 0
				dones = {}
				for selection in selections:
					for track_id in selection:
						if track_id not in dones:
							tr = self.pctl.get_track(track_id)

							if cm.startswith("fs\""):
								line = f"{tr.title}|{tr.artist}|{tr.album}|{tr.fullpath}|{tr.composer}|{tr.comment}|{tr.album_artist}".lower()
								if quote.lower() in line:
									playlist.append(track_id)
							else:
								line = f"{tr.title} {tr.artist} {tr.album} {tr.fullpath} {tr.composer} {tr.comment} {tr.album_artist}".lower()

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
				for p in self.pctl.multi_playlist:
					if p.title.lower() == pl_name.lower():
						target = p.playlist_ids
						break
				else:
					for p in self.pctl.multi_playlist:
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

		self.gui.gen_code_errors = errors
		if not playlist and not errors:
			self.gui.gen_code_errors = "empty"

		# Eliminate duplicates
		if playlist:
			playlist = list(dict.fromkeys(playlist))
		if self.gui.rename_playlist_box and (not playlist or cmds.count("a") > 1):
			pass
		else:
			source_playlist[:] = playlist[:]

		self.tree_view_box.clear_target_pl(0, id)
		self.pctl.regen_in_progress = False
		self.gui.request_tracklist_redraw()
		self.reload()
		self.dropped_playlist = pl
		self.pctl.notify_database_changed()

		#logging.info(cmds)

	def make_auto_sorting(self, pl: int) -> None:
		self.pctl.gen_codes[self.pctl.pl_to_id(pl)] = "self a path tn ypa auto"
		self.show_message(
			_("OK. This playlist will automatically sort on import from now on"),
			_("You remove or edit this behavior by going \"Misc...\" > \"Edit generator...\""), mode="done")

	def jellyfin_show_test(self, _unused: int) -> bool:
		return bool(self.prefs.jelly_password and self.prefs.jelly_username)

	def upload_jellyfin_playlist(self, pl: int) -> None:
		if self.jellyfin.scanning:
			return
		shooter(self.jellyfin.upload_playlist, [pl])

	def regen_playlist_async(self, pl: int) -> None:
		if self.pctl.regen_in_progress:
			self.show_message(_("A regen is already in progress..."))
			return
		shoot_dl = threading.Thread(target=self.regenerate_playlist, args=([pl]))
		shoot_dl.daemon = True
		shoot_dl.start()

	def forget_pl_import_folder(self, pl: int) -> None:
		self.pctl.multi_playlist[pl].last_folder = []

	def remove_duplicates(self, pl: int) -> None:
		playlist = []

		for item in self.pctl.multi_playlist[pl].playlist_ids:
			if item not in playlist:
				playlist.append(item)

		removed = len(self.pctl.multi_playlist[pl].playlist_ids) - len(playlist)
		if not removed:
			self.show_message(_("No duplicates were found"))
		else:
			self.show_message(_("{N} duplicates removed").format(N=removed), mode="done")

		self.pctl.multi_playlist[pl].playlist_ids[:] = playlist[:]

	def start_quick_add(self, pl: int) -> None:
		self.pctl.quick_add_target = self.pctl.pl_to_id(pl)
		self.show_message(
			_("You can now add/remove albums to this playlist by right clicking in gallery of any playlist"),
			_("To exit this mode, click \"Disengage\" from main MENU"))

	def prep_gal(self) -> None:
		self.albums = []
		folder = ""

		for index in self.pctl.default_playlist:
			if folder != self.pctl.master_library[index].parent_folder_name:
				self.albums.append([index, 0])
				folder = self.pctl.master_library[index].parent_folder_name

	def pl_gen(self,
		title:        str = "Default",
		playing:      int = 0,
		playlist_ids: list[int] | None = None,
		position:     int = 0,
		hide_title:   bool = False,
		selected:     int = 0,
		parent:       int = 0,
		hidden:       bool = False,
		notify:       bool = True, # Allows us to generate initial playlist before worker thread is ready
		playlist_file:str = "",
		auto_export:  bool = False,
		auto_import:  bool = False,
		relative_export: bool = False,
		export_type:  str = "xspf",
		file_size:    int = 0,

	) -> TauonPlaylist:
		"""Generate a TauonPlaylist

		Creates a default playlist when called without parameters
		"""
		if playlist_ids is None:
			playlist_ids = []
		if notify:
			self.pctl.notify_database_changed()

		#return copy.deepcopy([title, playing, playlist, position, hide_title, selected, uid_gen(), [], hidden, False, parent, False])
		return TauonPlaylist(title=title, playing=playing, playlist_ids=playlist_ids, position=position, hide_title=hide_title, selected=selected, uuid_int=uid_gen(), last_folder=[], hidden=hidden, locked=False, parent_playlist_id=parent, persist_time_positioning=False, playlist_file=playlist_file, file_size=file_size, auto_export=auto_export, auto_import=auto_import, export_type=export_type, relative_export=relative_export)

	def open_uri(self, uri: str) -> None:
		logging.info("OPEN URI")
		load_order = LoadClass()

		for w in range(len(self.pctl.multi_playlist)):
			if self.pctl.multi_playlist[w].title == "Default":
				load_order.playlist = self.pctl.multi_playlist[w].uuid_int
				break
		else:
			logging.warning("'Default' playlist not found, generating a new one!")
			self.pctl.multi_playlist.append(self.pl_gen())
			load_order.playlist = self.pctl.multi_playlist[len(self.pctl.multi_playlist) - 1].uuid_int
			self.pctl.switch_playlist(len(self.pctl.multi_playlist) - 1)

		load_order.target = str(urllib.parse.unquote(uri)).replace("file:///", "/").replace("\r", "")

		if self.gui.auto_play_import is False:
			load_order.play = True
			self.gui.auto_play_import = True

		self.load_orders.append(copy.deepcopy(load_order))
		self.gui.request_frame()

	def toast(self, text: str, duration: float = 1) -> None:
		self.gui.mode_toast_text = text
		self.gui.toast_length = duration
		self.toast_mode_timer.set()
		self.gui.frame_callback_list.append(TestTimer(duration + 0.2))

	def set_artist_preview(self, path: str, artist: str, x: int, y: int) -> None:
		m = min(round(500 * self.gui.scale), self.window_size[1] - (self.gui.panelY + self.gui.panelBY + 50 * self.gui.scale))
		self.artist_preview_render.load(path, box_size=(m, m))
		self.artist_preview_render.show = True
		ah = self.artist_preview_render.size[1]
		ay = round(y) - (ah // 2)
		if ay < self.gui.panelY + 20 * self.gui.scale:
			ay = self.gui.panelY + round(20 * self.gui.scale)
		if ay + ah > self.window_size[1] - (self.gui.panelBY + 5 * self.gui.scale):
			ay = self.window_size[1] - (self.gui.panelBY + ah + round(5 * self.gui.scale))
		self.gui.preview_artist = artist
		self.gui.preview_artist_location = (x + 15 * self.gui.scale, ay)

	def get_artist_preview(self, artist: str, x: int, y: int) -> None:
		# self.show_message(_("Loading artist image..."))

		self.gui.preview_artist_loading = artist
		self.artist_info_box.get_data(artist, force_dl=True)
		path = self.artist_info_box.get_data(artist, get_img_path=True)
		if not path:
			self.show_message(_("No artist image found."))
			if not self.prefs.enable_fanart_artist and not self.verify_discogs():
				self.show_message(_("No artist image found."), _("No providers are enabled in settings!"), mode="warning")
			self.gui.preview_artist_loading = ""
			return
		self.set_artist_preview(path, artist, x, y)
		self.gui.message_box = False
		self.gui.preview_artist_loading = ""

	def column_area_width(self) -> int:
		"""Width available to the tracklist columns. In custom mode this is the
		Tracklist widget's segment, not gui.plw — sizing runs from menu
		callbacks outside the widget's draw, where gui.plw holds the preset
		value."""
		wid = self.gui.plw
		if self.gui.custom_mode:
			rect = self.custom.tracklist_rect()
			if rect:
				wid = rect[2]
		elif self.gui.tracklist_center_mode:
			wid = self.gui.tracklist_highlight_width
		return wid - round(self.gui.pl_st_left * self.gui.scale)

	def update_set(self) -> None:
		"""This is used to scale columns when windows is resized or items added/removed"""
		wid = self.column_area_width()

		total = 0
		for item in self.gui.pl_st:
			if item[2] is False:
				total += item[1]
			else:
				wid -= item[1]

		wid = max(75, wid)

		for i in range(len(self.gui.pl_st)):
			if self.gui.pl_st[i][2] is False and total:
				self.gui.pl_st[i][1] = round((self.gui.pl_st[i][1] / total) * wid)  # + 1

	def auto_size_columns(self) -> None:
		fixed_n = 0

		wid = self.column_area_width()

		total = wid
		for item in self.gui.pl_st:

			if item[2]:
				fixed_n += 1

			if item[0] == "Lyrics":
				item[1] = round(50 * self.gui.scale)
				total  -= round(50 * self.gui.scale)

			if item[0] == "Rating":
				item[1] = round(80 * self.gui.scale)
				total  -= round(80 * self.gui.scale)

			if item[0] == "Album Art":
				item[1] = round(72 * self.gui.scale)
				total  -= round(72 * self.gui.scale)

			if item[0] == "Starline":
				item[1] = round(78 * self.gui.scale)
				total  -= round(78 * self.gui.scale)

			if item[0] == "Time" or item[0] == "ID":
				item[1] = round(58 * self.gui.scale)
				total  -= round(58 * self.gui.scale)

			if item[0] == "Codec":
				item[1] = round(58 * self.gui.scale)
				total  -= round(58 * self.gui.scale)

			if item[0] == "P" or item[0] == "S" or item[0] == "#":
				item[1] = round(32 * self.gui.scale)
				total  -= round(32 * self.gui.scale)

			if item[0] == "Date":
				item[1] = round(55 * self.gui.scale)
				total  -= round(55 * self.gui.scale)

			if item[0] == "Bitrate" or item[0] == "=/=":
				item[1] = round(67 * self.gui.scale)
				total  -= round(67 * self.gui.scale)

			if item[0] == "❤":
				item[1] = round(27 * self.gui.scale)
				total  -= round(27 * self.gui.scale)

		vr = len(self.gui.pl_st) - fixed_n

		if vr > 0 and total > 50:
			space = round(total / vr)

			for item in self.gui.pl_st:
				if not item[2]:
					item[1] = space

		self.gui.request_tracklist_redraw()
		self.update_set()

	def set_colour(self, colour: ColourRGBA) -> None:
		sdl3.SDL_SetRenderDrawColor(self.renderer, colour.r, colour.g, colour.b, colour.a)

	# 2025-02-02 - commented out as it was not used
	#def advance_theme() -> None:
	#	prefs.theme += 1
	#	gui.reload_theme = True

	def reload_metadata(self, input: int | list[TrackClass], keep_star: bool = True) -> None:
		# vacuum_playtimes(index)
		# return
		self.todo = []

		if isinstance(input, list):
			self.todo = input
		else:
			for k in self.pctl.default_playlist:
				if self.pctl.master_library[input].parent_folder_path == self.pctl.master_library[k].parent_folder_path:
					self.todo.append(self.pctl.master_library[k])

		for i in reversed(range(len(self.todo))):
			if self.todo[i].is_cue:
				del self.todo[i]

		for track in self.todo:
			self.search_string_cache.pop(track.index, None)
			self.search_dia_string_cache.pop(track.index, None)
			self.search_field_cache.pop(track.index, None)
			self.search_dia_field_cache.pop(track.index, None)

			#logging.info('Reloading Metadata for ' + track.filename)
			if keep_star:
				self.to_scan.append(track.index)
			else:
				# if keep_star:
				# 	star = self.star_store.full_get(track.index)
				# 	self.star_store.remove(track.index)

				self.pctl.master_library[track.index] = self.tag_scan(track)

				# if keep_star:
				# 	if star is not None and (star.playtime > 0 or star.flags or star.rating > 0):
				# 		self.star_store.merge(track.index, star)

				self.pctl.notify_database_changed()

		self.gui.request_tracklist_redraw()
		self.thread_manager.ready("worker")

	def menu_reload_metadata(self, ref: MenuTrackRef) -> None:
		self.reload_metadata(ref.track_id)

	def edit_generator_box(self, index: int) -> None:
		self.rename_playlist(index, generator=True)

	def pin_playlist_toggle(self, pl: int) -> None:
		self.pctl.multi_playlist[pl].hidden ^= True

	def pl_pin_deco(self, pl: int) -> Decorator:
		# if pctl.multi_playlist[pl].hidden == True and self.tab_menu.pos[1] >
		if self.pctl.multi_playlist[pl].hidden is True:
			return Decorator(self.colours.menu_text, self.colours.menu_background, _("Pin"))
		return Decorator(self.colours.menu_text, self.colours.menu_background, _("Unpin"))

	def pl_lock_deco(self, pl: int) -> Decorator:
		if self.pctl.multi_playlist[pl].locked is True:
			return Decorator(self.colours.menu_text, self.colours.menu_background, _("Unlock"))
		return Decorator(self.colours.menu_text, self.colours.menu_background, _("Lock"))

	def view_pl_is_locked(self, _unused) -> bool:
		return self.pctl.multi_playlist[self.pctl.active_playlist_viewing].locked

	def pl_is_locked(self, pl: int) -> bool:
		if not self.pctl.multi_playlist:
			return False
		return self.pctl.multi_playlist[pl].locked

	def lock_playlist_toggle(self, pl: int) -> None:
		self.pctl.multi_playlist[pl].locked ^= True

	def lock_colour_callback(self) -> ColourRGBA | None:
		if self.pctl.multi_playlist[self.gui.tab_menu_pl].locked:
			if self.colours.lm:
				return ColourRGBA(230, 180, 60, 255)
			return ColourRGBA(240, 190, 10, 255)
		return None

	def reload_metadata_selection(self) -> None:
		self.pctl.cargo = []
		for item in self.gui.shift_selection:
			self.pctl.cargo.append(self.pctl.default_playlist[item])

		for k in self.pctl.cargo:
			if self.pctl.master_library[k].is_cue is False:
				self.to_scan.append(k)
		self.thread_manager.ready("worker")

	def editor(self, index: int | None) -> None:
		todo: list[int] = []
		obs: list[TrackClass] = []

		if self.inp.key_shift_down and index is not None:
			todo = [index]
			obs = [self.pctl.master_library[index]]
		elif index is None:
			for item in self.gui.shift_selection:
				todo.append(self.pctl.default_playlist[item])
				obs.append(self.pctl.master_library[self.pctl.default_playlist[item]])
			if len(todo) > 0:
				index = todo[0]
		else:
			for k in self.pctl.default_playlist:
				if self.pctl.master_library[index].parent_folder_path == self.pctl.master_library[k].parent_folder_path:
					if self.pctl.master_library[k].is_cue is False:
						todo.append(k)
						obs.append(self.pctl.master_library[k])

		# Keep copy of play times
		old_stars: list[TrackClass | tuple[str, str, str] | StarRecord | None] = []
		for track in todo:
			item = []
			item.append(self.pctl.get_track(track))
			item.append(self.star_store.key(track))
			item.append(self.star_store.full_get(track))
			old_stars.append(item)

		file_line = ""
		for track in todo:
			file_line += ' "'
			file_line += self.pctl.master_library[track].fullpath
			file_line += '"'

		if self.windows:
			file_line = file_line.replace("/", "\\")

		prefix = ""
		app = self.prefs.tag_editor_target

		if self.windows and app:
			if app[0] != '"':
				app = '"' + app
			if app[-1] != '"':
				app = app + '"'

		app_switch = ""

		prefix = self.launch_prefix

		ok = whicher(self.prefs.tag_editor_target, self.flatpak_mode)

		if not ok:
			self.show_message(_("Tag editor app does not appear to be installed."), mode="warning")

			if self.flatpak_mode:
				self.show_message(
					_("App not found on host OR insufficient Flatpak permissions."),
					_(" For details, see {link}").format(link="https://github.com/Taiko2k/Tauon/wiki/Flatpak-Extra-Steps"),
					mode="bubble")

			return

		if "picard" in self.prefs.tag_editor_target:
			app_switch = " --d "

		line = prefix + app + app_switch + file_line

		self.show_message(
			self.prefs.tag_editor_name + " launched.", "Fields will be updated once application is closed.", mode="arrow")
		self.gui.request_frame()

		complete = subprocess.run(shlex.split(line), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

		if "picard" in self.prefs.tag_editor_target:
			r = complete.stderr.decode()
			for line in r.split("\n"):
				if "file._rename" in line and " Moving file " in line:
					a, b = line.split(" Moving file ")[1].split(" => ")
					a = a.strip("'").strip('"')
					b = b.strip("'").strip('"')

					for track in todo:
						if self.pctl.master_library[track].fullpath == a:
							self.pctl.master_library[track].fullpath = b
							self.pctl.master_library[track].filename = os.path.basename(b)
							logging.info("External Edit: File rename detected.")
							logging.info(f"    Renaming: {a}")
							logging.info(f"          To: {b}")
							break
					else:
						logging.warning("External Edit: A file rename was detected but track was not found.")

		self.gui.message_box = False
		self.reload_metadata(obs, keep_star=False)

		# Re apply playtime data in case file names change
		for item in old_stars:
			old_key: tuple[str, str, str] = item[1]
			old_value: StarRecord | None = item[2]

			if not old_value:  # ignore if there was no old playcount metadata
				continue

			new_key = self.star_store.object_key(item[0])
			new_value = self.star_store.full_get(item[0].index)

			if old_key == new_key:
				continue

			if new_value is None:
				new_value = StarRecord()

			new_value.playtime += old_value.playtime

			if old_key in self.star_store.db:
				del self.star_store.db[old_key]

			self.star_store.db[new_key] = new_value

		self.gui.request_tracklist_redraw()
		self.gui.request_frame()
		self.pctl.notify_database_changed()

	def launch_editor(self, ref: MenuTrackRef) -> bool | None:
		if self.snap_mode:
			self.show_message(_("Sorry, this feature isn't (yet) available with Snap."))
			return None

		if self.launch_editor_disable_test(ref):
			self.show_message(_("Cannot edit tags of a network track."))
			return None

		mini_t = threading.Thread(target=self.editor, args=[ref.track_id])
		mini_t.daemon = True
		mini_t.start()

	def launch_editor_selection_disable_test(self, _ref: object) -> bool:
		for position in self.gui.shift_selection:
			if self.pctl.get_track(self.pctl.default_playlist[position]).is_network:
				return True
		return False

	def launch_editor_selection(self, ref: object) -> None:
		if self.launch_editor_selection_disable_test(ref):
			self.show_message(_("Cannot edit tags of a network track."))
			return

		mini_t = threading.Thread(target=self.editor, args=[None])
		mini_t.daemon = True
		mini_t.start()

	def edit_deco(self, _ref: object) -> Decorator:
		if self.inp.key_shift_down or self.inp.key_shiftr_down:
			return Decorator(self.colours.menu_text, self.colours.menu_background, self.prefs.tag_editor_name + " (Single track)")
		return Decorator(self.colours.menu_text, self.colours.menu_background, _("Edit with ") + self.prefs.tag_editor_name)

	def launch_editor_disable_test(self, ref: MenuTrackRef) -> bool:
		return self.pctl.get_track(ref.track_id).is_network

	def show_lyrics_menu(self, ref: MenuTrackRef) -> None:
		self.gui.track_box = False
		self.enter_showcase_view(track_id=ref.track_id)
		self.inp.mouse_click = False

	def show_message(self, line1: str, line2: str ="", line3: str = "", mode: str = "info") -> None:
		self.gui.message_box = True
		self.gui.message_text = line1
		self.gui.message_mode = mode
		self.gui.message_subtext = line2
		self.gui.message_subtext2 = line3
		self.message_box_min_timer.set()
		match mode:
			case "done" | "confirm" | "arrow" | "download" | "bubble" | "link":
				logging.debug(f"Message: {line1} {line2} {line3}")
			case "info":
				logging.info(f"Message: {line1} {line2} {line3}")
			case "warning":
				logging.warning(f"Message: {line1} {line2} {line3}")
			case "error":
				logging.error(f"Message: {line1} {line2} {line3}")
			case _:
				logging.error(f"Unknown mode '{mode}' for message: {line1} {line2} {line3}")
		self.gui.request_frame()

	def start_remote(self) -> None:
		if not self.web_running:
			self.web_thread = threading.Thread(
				target=webserve2, args=[self.pctl, self.album_art_gen, self])
			self.web_thread.daemon = True
			self.web_thread.start()
			self.web_running = True

	def download_ffmpeg(self, _x) -> None:
		"""Download FFmpeg portable binary to User Data dir, supports x64 Windows and Linux"""
		self.preset_download_box.start(
			title=_("Downloading FFmpeg"),
			status=_("Starting download..."),
			cancel_detail=_("FFmpeg will not be installed."),
		)

		def go() -> None:
			if self.windows:
				url = "https://github.com/GyanD/codexffmpeg/releases/download/8.0.1/ffmpeg-8.0.1-essentials_build.zip"
				sha = "e2aaeaa0fdbc397d4794828086424d4aaa2102cef1fb6874f6ffd29c0b88b673"
			elif not self.macos:
				url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2026-03-02-13-06/ffmpeg-n8.0.1-66-g27b8d1a017-linux64-gpl-8.0.tar.xz"
				sha = "e6f31af6c1ef49ceec8361185d70283ea8ad6c8ceed652d5dee66ec174a11eea"
			with io.BytesIO() as f:
				try:
					with requests.get(url, stream=True, timeout=1800) as r: # Windows ffmpeg is 101MB, Linux 130MB, give it half an hour in case someone is willing to suffer it on a slow connection
						r.raise_for_status()
						dl = 0
						total_bytes = int(r.headers.get("Content-Length", 0))
						if self.windows:
							fallback_mb = 101
						elif not self.macos:
							fallback_mb = 130
						total_mb = round(total_bytes / 1000 / 1000) if total_bytes else fallback_mb

						for data in r.iter_content(chunk_size=65536):
							if self.preset_download_box.cancel_requested:
								self.preset_download_box.complete(
									status=_("FFmpeg download cancelled"),
									detail=_("FFmpeg was not installed."),
								)
								return
							if not data:
								continue
							dl += len(data)
							f.write(data)
							mb = dl / 1000 / 1000
							if total_bytes:
								progress = min(0.95, dl / total_bytes * 0.95)
							else:
								progress = min(0.95, mb / total_mb * 0.95)
							detail = f"{mb:.1f} / {total_mb:.1f} MB"
							self.preset_download_box.update(progress, _("Downloading FFmpeg..."), detail)
				except Exception as e:
					logging.exception("Download failed")
					self.preset_download_box.fail(_("Download failed"), f"{type(e).__name__}: {e}")
					return

				f.seek(0)
				self.preset_download_box.update(0.96, _("Verifying download..."))
				checksum = hashlib.sha256(f.read()).hexdigest()
				if checksum != sha:
					self.preset_download_box.fail(_("Download completed but checksum failed"))
					logging.error(f"Checksum was {checksum} but expected {sha}")
					return
				if self.preset_download_box.cancel_requested:
					self.preset_download_box.complete(
						status=_("FFmpeg download cancelled"),
						detail=_("FFmpeg was not installed."),
					)
					return
				self.preset_download_box.update(0.98, _("Extracting FFmpeg..."))
				f.seek(0)
				if self.windows:
					z = zipfile.ZipFile(f, mode="r")
					with z.open("ffmpeg-8.0.1-essentials_build/bin/ffmpeg.exe") as exe, (self.user_directory / "ffmpeg.exe").open("wb") as file:
						file.write(exe.read())

					with z.open("ffmpeg-8.0.1-essentials_build/bin/ffprobe.exe") as exe, (self.user_directory / "ffprobe.exe").open("wb") as file:
						file.write(exe.read())
				elif not self.macos:
					import tarfile

					output_dir = self.user_directory
					wanted = {"ffmpeg", "ffprobe"}

					with tarfile.open(fileobj=f, mode="r:xz") as tar:
						for member in tar.getmembers():
							if self.preset_download_box.cancel_requested:
								self.preset_download_box.complete(
									status=_("FFmpeg download cancelled"),
									detail=_("FFmpeg was not installed."),
								)
								return
							filename = Path(member.name).name

							if filename in wanted and member.isfile():
								member.name = filename  # strip directory structure
								tar.extract(member, path=output_dir)


			self.preset_download_box.complete(
				status=_("FFmpeg fetch complete"),
				toast_text=_("Download completed"),
			)

		shooter(go)

	def draw_rating_widget(
		self,
		x: int,
		y: int,
		n_track: TrackClass,
		album: bool = False,
		allow_input: bool = True,
		hint_only: bool = False,
	) -> None:
		rat = self.album_star_store.get_rating(n_track) if album else self.star_store.get_rating(n_track.index)
		display_rat = 0 if hint_only else rat

		rect = (x - round(5 * self.gui.scale), y - round(4 * self.gui.scale), round(80 * self.gui.scale), round(24 * self.gui.scale))
		boundary = 3 * self.gui.scale
		tracklist_top = self.gui.playlist_top + boundary
		tracklist_bottom = self.window_size[1] - self.gui.panelBY - boundary
		input_in_bounds = tracklist_top < self.inp.mouse_position[1] <= tracklist_bottom
		if allow_input and input_in_bounds:
			self.gui.heart_fields.append(rect)

		if allow_input and input_in_bounds and self.coll(rect) and (self.inp.mouse_click or (self.is_level_zero() and not self.inp.quick_drag)):
			self.gui.request_tracklist_redraw()
			pp = self.inp.mouse_position[0] - x

			if pp < 5 * self.gui.scale:
				rat = 0
			elif pp > 70 * self.gui.scale:
				rat = 10
			else:
				rat = pp // (self.gui.star_row_icon.w // 2)

			if self.inp.mouse_click:
				rat = min(rat, 10)
				if album:
					self.album_star_store.set_rating(n_track, rat)
				else:
					self.star_store.set_rating(n_track.index, rat, write=True)
				display_rat = rat

		# bg = self.colours.grey(40)
		bg = ColourRGBA(255, 255, 255, 17)
		fg = self.colours.grey(210)

		if self.gui.tracklist_bg_is_light:
			bg = ColourRGBA(0, 0, 0, 25)
			fg = self.colours.grey(70)

		playtime_stars = 0
		if self.prefs.rating_playtime_stars and not album and (hint_only or display_rat == 0):
			playtime_stars = star_count3(self.star_store.get(n_track.index), n_track.length)
			if self.gui.tracklist_bg_is_light:
				fg2 = alpha_blend(ColourRGBA(0, 0, 0, 70), self.ddt.text_background_colour)
			else:
				fg2 = alpha_blend(ColourRGBA(255, 255, 255, 50), self.ddt.text_background_colour)

		for ss in range(5):
			xx = x + ss * self.gui.star_row_icon.w

			if playtime_stars:
				if playtime_stars - 1 < ss * 2:
					self.gui.star_row_icon.render(xx, y, bg)
				elif playtime_stars - 1 == ss * 2:
					self.gui.star_row_icon.render(xx, y, bg)
					self.gui.star_half_row_icon.render(xx, y, fg2)
				else:
					self.gui.star_row_icon.render(xx, y, fg2)
			elif display_rat - 1 < ss * 2:
				self.gui.star_row_icon.render(xx, y, bg)
			elif display_rat - 1 == ss * 2:
				self.gui.star_row_icon.render(xx, y, bg)
				self.gui.star_half_row_icon.render(xx, y, fg)
			else:
				self.gui.star_row_icon.render(xx, y, fg)

	def standard_view_deco(self) -> Decorator:
		if self.prefs.album_mode or self.gui.combo_mode or not self.gui.rsp:
			line_colour = self.colours.menu_text
		else:
			line_colour = self.colours.menu_text_disabled
		return Decorator(line_colour, self.colours.menu_background, None)

	# def gallery_only_view(self) -> None:
	# 	if self.gui.show_playlist is False:
	# 		return
	# 	if not self.prefs.album_mode:
	# 		self.toggle_album_mode()
	# 	self.gui.show_playlist = False
	# 	self.gui.update_layout = True
	# 	self.gui.rspw = window_size[0]
	# 	self.gui.album_playlist_width = self.gui.playlist_width
	# 	#self.gui.playlist_width = -19

	def toggle_library_mode(self) -> None:
		if self.gui.set_mode:
			self.gui.set_mode = False
			# self.gui.set_bar = False
		else:
			self.gui.set_mode = True
			# self.gui.set_bar = True
		self.gui.update_layout = True

	def library_deco(self) -> Decorator:
		tc = self.colours.menu_text
		if self.gui.combo_mode or (self.gui.show_playlist is False and self.prefs.album_mode):
			tc = self.colours.menu_text_disabled

		if self.gui.set_mode:
			return Decorator(tc, self.colours.menu_background, _("Disable Columns"))
		return Decorator(tc, self.colours.menu_background, _("Enable Columns"))

	def break_deco(self) -> Decorator:
		tex = self.colours.menu_text
		if self.gui.combo_mode or (self.gui.show_playlist is False and self.prefs.album_mode):
			tex = self.colours.menu_text_disabled
		if not self.prefs.break_enable:
			tex = self.colours.menu_text_disabled

		if not self.pctl.multi_playlist[self.pctl.active_playlist_viewing].hide_title:
			return Decorator(tex, self.colours.menu_background, _("Disable Title Breaks"))
		return Decorator(tex, self.colours.menu_background, _("Enable Title Breaks"))

	def toggle_playlist_break(self) -> None:
		self.pctl.multi_playlist[self.pctl.active_playlist_viewing].hide_title ^= 1
		self.gui.request_tracklist_redraw()

	def pl_toggle_playlist_break(self, ref) -> None:
		self.pctl.multi_playlist[ref].hide_title ^= 1
		self.gui.request_tracklist_redraw()

	def transcode_single(self, item: list[tuple[int, str]], manual_directory: Path | None = None, manual_name: str | None = None) -> None:
		if manual_directory is not None:
			codec = "opus"
			output = manual_directory
			track = item
			self.core_use += 1
			bitrate = 48
		else:
			track = item[0]
			codec   = self.prefs.transcode_codec
			output  = self.prefs.encoder_output / item[1]
			bitrate = self.prefs.transcode_bitrate

		t = self.pctl.master_library[track]

		path = t.fullpath
		cleanup = False

		if t.is_network:
			while self.dl_use > 1:
				time.sleep(0.2)
			self.dl_use += 1
			try:
				url, params = self.pctl.get_url(t)
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
			self.dl_use -= 1

		if not os.path.isfile(path):
			self.show_message(_("Encoding warning: Missing one or more files"))
			self.core_use -= 1
			return

		out_line = encode_track_name(t)

		target_out = str(output / f"output{track}.{codec}")

		command = str(self.get_ffmpeg()) + " "

		if not t.is_cue:
			command += '-i "'
		else:
			command += "-ss " + str(t.start_time)
			command += " -t " + str(t.length)

			command += ' -i "'

		command += path.replace('"', '\\"')

		command += '" '
		if self.pctl.master_library[track].is_cue:
			if t.title:
				command += '-metadata title="' + t.title.replace('"', "").replace("'", "") + '" '
			if t.artist:
				command += '-metadata artist="' + t.artist.replace('"', "").replace("'", "") + '" '
			if t.album:
				command += '-metadata album="' + t.album.replace('"', "").replace("'", "") + '" '
			if t.track_number:
				command += '-metadata track="' + str(t.track_number).replace('"', "").replace("'", "") + '" '
			if t.date:
				command += '-metadata year="' + str(t.date).replace('"', "").replace("'", "") + '" '

		if codec != "flac":
			command += " -b:a " + str(bitrate) + "k -vn "

		command += '"' + target_out.replace('"', '\\"') + '"'

		# logging.info(shlex.split(command))
		startupinfo = None
		if self.windows:
			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

		if not self.windows:
			command = shlex.split(command)

		subprocess.call(command, stdout=subprocess.PIPE, shell=False, startupinfo=startupinfo)

		logging.info("FFmpeg finished")
		if codec == "opus" and self.prefs.transcode_opus_as:
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

		if self.prefs.transcode_inplace and not t.is_network and not t.is_cue:
			logging.info("MOVE AND REPLACE!")
			if os.path.isfile(final_out) and os.path.getsize(final_out) > 1000:
				new_name = os.path.join(t.parent_folder_path, final_name)
				logging.info(new_name)
				shutil.move(final_out, new_name)

				old_key  = self.star_store.key(track)
				old_star = self.star_store.full_get(track)

				try:
					send2trash(self.pctl.master_library[track].fullpath)
				except Exception:
					logging.exception("File trash error")

				if os.path.isfile(self.pctl.master_library[track].fullpath):
					try:
						os.remove(self.pctl.master_library[track].fullpath)
					except Exception:
						logging.exception("File delete error")

				self.pctl.master_library[track].fullpath = new_name
				self.pctl.master_library[track].file_ext = codec.upper()

				# Update and merge playtimes
				new_key = self.star_store.key(track)
				if old_star and (new_key != old_key):

					new_star = self.star_store.full_get(track)
					if new_star is None:
						new_star = StarRecord()

					new_star.playtime += old_star.playtime
					if old_star.rating > 0 and new_star.rating == 0:
						new_star.rating = old_star.rating

					if old_key in self.star_store.db:
						del self.star_store.db[old_key]

					self.star_store.db[new_key] = new_star

		self.gui.transcoding_batch_done += 1
		if cleanup:
			os.remove(path)
		self.core_use -= 1
		self.gui.request_frame()

	def cue_scan(self, content: str, tn: TrackClass) -> int | None:
		# Get length from backend

		lasttime = tn.length

		content = content.replace("\r", "")
		content = content.split("\n")

		#logging.info(content)

		cued: list[int] = []

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

				nt.index = self.pctl.master_count
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

				self.pctl.master_library[self.pctl.master_count] = nt

				cued.append(self.pctl.master_count)
				# loaded_paths_cache[filepath.replace('\\', '/')] = self.pctl.master_count
				# self.added.append(self.pctl.master_count)

				self.pctl.master_count += 1
				LENGTH = 0
				PERFORMER = ""
				TITLE = ""
				START = 0
				TN = 0

		self.added += reversed(cued)

		# bag.cue_list.append(filepath)
		return None

	def get_album_from_first_track(self, track_position: int, track_id: int | None = None, pl_number: int | None = None, pl_id: int | None = None) -> list[int]:
		if pl_number is None:
			pl_number = self.pctl.id_to_pl(pl_id) if pl_id else self.pctl.active_playlist_viewing

		playlist = self.pctl.multi_playlist[pl_number].playlist_ids

		if track_id is None:
			track_id = playlist[track_position]

		if playlist[track_position] != track_id:
			return []

		tracks = []
		album_parent_path = self.pctl.get_track(track_id).parent_folder_path

		i = track_position

		while i < len(playlist):
			if self.pctl.get_track(playlist[i]).parent_folder_path != album_parent_path:
				break

			tracks.append(playlist[i])
			i += 1

		return tracks

	def love_deco(self) -> Decorator:
		if self.love(False):
			return Decorator(self.colours.menu_text, self.colours.menu_background, _("Un-Love Track"))
		if self.pctl.playing_state in (PlayingState.PLAYING, PlayingState.PAUSED):
			return Decorator(self.colours.menu_text, self.colours.menu_background, _("Love Track"))
		return Decorator(self.colours.menu_text_disabled, self.colours.menu_background, _("Love Track"))

	def bar_love(self, notify: bool = False) -> None:
		shoot_love = threading.Thread(target=self.love, args=[True, None, False, notify])
		shoot_love.daemon = True
		shoot_love.start()

	def bar_love_notify(self) -> None:
		self.bar_love(notify=True)

	def select_love(self, notify: bool = False) -> None:
		selected = self.pctl.selected_in_playlist
		playlist = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].playlist_ids
		if -1 < selected < len(playlist):
			track_id = playlist[selected]

			shoot_love = threading.Thread(target=self.love, args=[True, track_id, False, notify])
			shoot_love.daemon = True
			shoot_love.start()

	def locate_artist(self) -> None:
		track = self.pctl.playing_object()
		if not track:
			return

		artist = track.artist
		if track.album_artist:
			artist = track.album_artist

		block_starts = []
		current = False
		for i in range(len(self.pctl.default_playlist)):
			track = self.pctl.get_track(self.pctl.default_playlist[i])
			if current is False:
				if artist in (track.artist, track.album_artist) or (track.artists is not None and artist in track.artists):
					block_starts.append(i)
					current = True
			elif (artist not in (track.artist, track.album_artist)) and not (
					track.artists is not None and artist in track.artists):
				current = False

		if block_starts:
			next = False
			for start in block_starts:

				if next:
					self.pctl.selected_in_playlist = start
					self.pctl.playlist_view_position = start
					self.gui.shift_selection.clear()
					break

				if self.pctl.selected_in_playlist == start:
					next = True
					continue

			else:
				self.pctl.selected_in_playlist = block_starts[0]
				self.pctl.playlist_view_position = block_starts[0]
				self.gui.shift_selection.clear()

			self.tree_view_box.show_track(self.pctl.get_track(self.pctl.default_playlist[self.pctl.selected_in_playlist]))
		else:
			self.show_message(_("No exact matching artist could be found in this playlist"))

		logging.debug("Position changed by artist locate")
		self.gui.request_tracklist_redraw()

	def goto_album(self, playlist_no: int, down: bool = False, force: bool = False) -> list | int | None:
		logging.debug("Position set by album locate")

		if self.core_timer.get() < 0.5:
			return None

		# ----
		w = self.gui.rspw
		if self.window_size[0] < 750 * self.gui.scale:
			w = self.window_size[0] - 20 * self.gui.scale
			if self.gui.lsp:
				w -= self.gui.lspw
		area_x = w + 38 * self.gui.scale
		row_len = int((area_x - self.gui.album_h_gap) / (self.album_mode_art_size + self.gui.album_h_gap))
		# Keep in step with render_gallery: the Gallery: Compact widget forces
		# the row length (set around this call by CustomLayout.gallery_locate).
		if self.gui.gallery_forced_row_len:
			row_len = self.gui.gallery_forced_row_len
		self.gui.last_row = row_len
		# ----

		px = 0
		row = 0
		re = 0

		for i in range(len(self.album_dex)):
			if i == len(self.album_dex) - 1:
				re = i
				break
			if self.album_dex[i + 1] - 1 > playlist_no - 1:
				re = i
				break
			row += 1
			if row > row_len - 1:
				row = 0
				px += self.album_mode_art_size + self.gui.album_v_gap

		# If the album is within the view port already, dont jump to it
		# (unless we really want to with force)
		if not force and self.gui.album_scroll_px + self.gui.album_v_slide_value < px < self.gui.album_scroll_px + self.window_size[1]:
			# Dont chance the view since its already in the view port
			# But if the album is just out of view on the bottom, bring it into view on to bottom row
			if self.window_size[1] > (self.album_mode_art_size + self.gui.album_v_gap) * 2:
				while not self.gui.album_scroll_px - 20 < px + (self.album_mode_art_size + self.gui.album_v_gap + 3) < self.gui.album_scroll_px + \
					self.window_size[1] - 40:
					self.gui.album_scroll_px += 1
		else:
			# Set the view to the calculated position
			self.gui.album_scroll_px = px
			self.gui.album_scroll_px -= self.gui.album_v_slide_value

			self.gui.album_scroll_px = max(self.gui.album_scroll_px, 0 - self.gui.album_v_slide_value)

		if len(self.album_dex) > 0:
			return self.album_dex[re]
		return 0

		self.gui.request_frame() # TODO(Martin): WTF Unreachable??
		return None

	def toggle_album_mode(self, force_on: bool = False) -> None:
		self.gui.gall_tab_enter = False

		if self.prefs.album_mode is True:
			self.prefs.album_mode = False
			# self.gui.album_playlist_width = self.gui.playlist_width
			# self.gui.old_album_pos = self.gui.album_scroll_px
			self.gui.rspw = self.gui.pref_rspw
			self.gui.rsp = self.prefs.prefer_side
			self.gui.album_tab_mode = False
		else:
			self.prefs.album_mode = True
			if self.gui.combo_mode:
				self.exit_combo()

			self.gui.rsp = True
			self.gui.rspw = self.gui.pref_gallery_w

		space = self.window_size[0] - self.gui.rspw
		if self.gui.lsp:
			space -= self.gui.lspw

		if self.prefs.album_mode and self.gui.set_mode and len(self.gui.pl_st) > 6 and space < 600 * self.gui.scale:
			self.gui.set_mode = False
			self.gui.request_tracklist_redraw()
			self.gui.update_layout = True

		self.reload_albums(quiet=True)

		# if self.pctl.active_playlist_playing == self.pctl.active_playlist_viewing:
		# 	self.goto_album(self.pctl.playlist_playing_position)

		if self.prefs.album_mode and self.pctl.selected_in_playlist < len(self.pctl.playing_playlist()):
			self.goto_album(self.pctl.selected_in_playlist)

	def toggle_gallery_keycontrol(self, always_exit: bool = False) -> None:
		if self.is_level_zero():
			if not self.prefs.album_mode:
				self.toggle_album_mode()
				self.gui.gall_tab_enter = True
				self.gui.album_tab_mode = True
				self.show_in_gal(self.pctl.selected_in_playlist, silent=True)
			elif self.gui.gall_tab_enter or always_exit:
				# Exit gallery and tab mode
				self.toggle_album_mode()
			else:
				self.gui.album_tab_mode ^= True
				if self.gui.album_tab_mode:
					self.show_in_gal(self.pctl.selected_in_playlist, silent=True)

	def check_auto_update_okay(self, code: str, pl: int | None = None) -> bool:
		try:
			cmds = shlex.split(code)
		except Exception:
			logging.exception("Malformed generator code!")
			return False
		return "auto" in cmds or (
			self.prefs.always_auto_update_playlists and
			self.pctl.active_playlist_playing != pl and
			"sf"     not in cmds and
			"rf"     not in cmds and
			"ra"     not in cmds and
			"sa"     not in cmds and
			"st"     not in cmds and
			"rt"     not in cmds and
			"plex"   not in cmds and
			"jelly"  not in cmds and
			"tau"    not in cmds and
			"air"    not in cmds and
			"sal"    not in cmds and
			"slt"    not in cmds and
			"spl\""  not in code and
			"tpl\""  not in code and
			"tar\""  not in code and
			"tmix\"" not in code and
			"r"      not in cmds)

	def rename_playlist(self, index, generator: bool = False) -> None:
		self.gui.rename_playlist_box = True
		self.rename_playlist_box.done_callback = None
		self.rename_playlist_box.edit_generator = False
		self.rename_playlist_box.playlist_index = index
		self.rename_playlist_box.x = self.inp.mouse_position[0]
		self.rename_playlist_box.y = self.inp.mouse_position[1]

		if generator:
			self.rename_playlist_box.y = self.window_size[1] // 2 - round(200 * self.gui.scale)
			self.rename_playlist_box.x = self.window_size[0] // 2 - round(250 * self.gui.scale)

		self.rename_playlist_box.y = min(self.rename_playlist_box.y, round(350 * self.gui.scale))

		if self.rename_playlist_box.y < self.gui.panelY:
			self.rename_playlist_box.y = self.gui.panelY + 10 * self.gui.scale

		if self.gui.radio_view:
			self.rename_text_area.set_text(self.pctl.radio_playlists[index].name)
		else:
			self.rename_text_area.set_text(self.pctl.multi_playlist[index].title)
		self.rename_text_area.highlight_all()
		self.gui.gen_code_errors = False

		if generator:
			self.rename_playlist_box.toggle_edit_gen()

	def gen_power2(self) -> list[PowerTag]:
		tags = {}  # [tag name]: (first position, number of times we saw it)
		tag_list = []

		last = "a"
		noise = 0

		def key(tag):
			return tags[tag][1]

		for position in self.album_dex:
			index = self.pctl.default_playlist[position]
			track = self.pctl.get_track(index)

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

		if noise > len(self.album_dex) / 2:
			#logging.info("Playlist is too noisy for power bar.")
			return []

		tag_list_sort = sorted(tag_list, key=key, reverse=True)

		max_tags = round((self.window_size[1] - self.gui.panelY - self.gui.panelBY - 10) // 30 * self.gui.scale)

		tag_list_sort = tag_list_sort[:max_tags]

		for i in reversed(range(len(tag_list))):
			if tag_list[i] not in tag_list_sort:
				del tag_list[i]

		h: list[PowerTag] = []

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

	def reload_albums(self, quiet: bool = False, return_playlist: int = -1, custom_list: list[int] | None = None) -> list[int]:
		if self.cm_clean_db:
			# Doing reload while things are being removed may cause crash
			return []

		dex = []
		current_folder = ""
		current_album = ""
		current_artist = ""
		current_date = ""
		current_title = ""

		if custom_list is not None:
			playlist = custom_list
		else:
			target_pl_no = self.pctl.active_playlist_viewing
			if return_playlist > -1:
				target_pl_no = return_playlist

			playlist = self.pctl.multi_playlist[target_pl_no].playlist_ids

		for i in range(len(playlist)):
			tr = self.pctl.master_library[playlist[i]]

			split = False
			if i == 0:
				split = True
			elif tr.parent_folder_path != current_folder and tr.date and tr.date != current_date:
				split = True
			elif self.prefs.gallery_combine_disc and "Disc" in tr.album and "Disc" in current_album and tr.album.split("Disc")[0].rstrip(" ") == current_album.split("Disc")[0].rstrip(" "):
				split = False
			elif self.prefs.gallery_combine_disc and "CD" in tr.album and "CD" in current_album and tr.album.split("CD")[0].rstrip() == current_album.split("CD")[0].rstrip():
				split = False
			elif self.prefs.gallery_combine_disc and "cd" in tr.album and "cd" in current_album and tr.album.split("cd")[0].rstrip() == current_album.split("cd")[0].rstrip():
				split = False
			elif tr.album and tr.album == current_album and self.prefs.gallery_combine_disc:
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

		if return_playlist > -1 or custom_list is not None:
			return dex

		# In-place so aliases stay live (pctl.album_dex is this same list —
		# purge_track clears it through that name to invalidate the index)
		self.album_dex[:] = dex
		self.album_dex_pl_uuid = self.pctl.multi_playlist[target_pl_no].uuid_int
		self.album_info_cache.clear()
		self.gui.request_frame()
		self.gui.request_tracklist_redraw()
		self.gui.update_layout = True

		if not quiet:
			self.goto_album(self.pctl.playlist_playing_position)

		# Generate POWER BAR
		self.gui.power_bar = self.gen_power2()
		self.gui.pt = 0
		return []

	def reload_backend(self) -> None:
		self.gui.backend_reloading = True
		logging.info("Reload backend...")
		wait = 0
		pre_state = self.pctl.stop(True)

		while self.pctl.playerCommandReady:
			time.sleep(0.01)
			wait += 1
			if wait > 20:
				break
		if self.thread_manager.player_lock.locked():
			try:
				self.thread_manager.player_lock.release()
			except RuntimeError as e:
				if str(e) == "release unlocked lock":
					logging.error("RuntimeError: Attempted to release already unlocked player_lock")  # noqa: TRY400
				else:
					logging.exception("Unknown RuntimeError trying to release player_lock")
			except Exception:
				logging.exception("Unknown error trying to release player_lock")

		self.pctl.playerCommand = "unload"
		self.pctl.playerCommandReady = True

		wait = 0
		while self.pctl.playerCommand != "done":
			time.sleep(0.01)
			wait += 1
			if wait > 200:
				break

		self.thread_manager.ready_playback()

		if pre_state == 1:
			self.pctl.revert()
		self.gui.backend_reloading = False

	def gen_chart(self) -> None:
		try:
			topchart = t_topchart.TopChart(self)

			tracks = []

			source_tracks = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].playlist_ids

			if self.prefs.topchart_sorts_played:
				source_tracks = self.gen_folder_top(0, custom_list=source_tracks)
				dex = self.reload_albums(quiet=True, custom_list=source_tracks)
			else:
				dex = self.reload_albums(quiet=True, return_playlist=self.pctl.active_playlist_viewing)

			for item in dex:
				tracks.append(self.pctl.get_track(source_tracks[item]))

			cascade = False
			if self.prefs.chart_cascade:
				cascade = (
					(self.prefs.chart_c1, self.prefs.chart_c2, self.prefs.chart_c3),
					(self.prefs.chart_d1, self.prefs.chart_d2, self.prefs.chart_d3))

			path = topchart.generate(
				tracks, self.prefs.chart_bg, self.prefs.chart_rows, self.prefs.chart_columns, self.prefs.chart_text,
				self.prefs.chart_font, self.prefs.chart_tile, cascade)

		except Exception:
			logging.exception("There was an error generating the chart")
			self.gui.generating_chart = False
			self.show_message(_("There was an error generating the chart"), _("Sorry!"), mode="error")
			return

		self.gui.generating_chart = False

		if path:
			self.open_file(path)
		else:
			self.show_message(_("There was an error generating the chart"), _("Sorry!"), mode="error")
			return

		self.show_message(_("Chart generated"), mode="done")

	def notify_song_fire(self, notification, delay: float, id) -> None:
		time.sleep(delay)
		notification.show()
		if id is None:
			return

		time.sleep(8)
		if id == self.gui.notify_main_id:
			notification.close()

	#def get_backend_time(self, path):
	#	self.pctl.time_to_get = path

	#	self.pctl.playerCommand = "time"
	#	self.pctl.playerCommandReady = True

	#	while self.pctl.playerCommand != "done":
	#		time.sleep(0.005)

	#	return self.pctl.time_to_get

	def get_love(self, track_object: TrackClass) -> bool:
		star = self.star_store.full_get(track_object.index)
		if star is None:
			return False

		return star.loved

	def get_love_index(self, index: int) -> bool:
		star = self.star_store.full_get(index)
		if star is None:
			return False

		return star.loved

	def get_love_timestamp_index(self, index: int) -> float:
		star = self.star_store.full_get(index)
		if star is None:
			return 0
		return star.loved_timestamp

	def maloja_get_scrobble_counts(self) -> None:
		if self.lastfm.scanning_scrobbles is True or not self.prefs.maloja_url:
			return

		url = self.prefs.maloja_url
		if not url.endswith("/"):
			url += "/"
		url += "apis/mlj_1/scrobbles"
		self.lastfm.scanning_scrobbles = True
		try:
			r = requests.get(url, timeout=10)

			if r.status_code != 200:
				self.show_message(_("There was an error with the Maloja server"), r.text, mode="warning")
				self.lastfm.scanning_scrobbles = False
				return
		except Exception:
			logging.exception("There was an error reaching the Maloja server")
			self.show_message(_("There was an error reaching the Maloja server"), mode="warning")
			self.lastfm.scanning_scrobbles = False
			return

		try:
			data = json.loads(r.text)
			l = data["list"]

			counts: dict[tuple[str, tuple[str, ...]], int] = {}

			for item in l:
				artists = item.get("artists")
				title = item.get("title")
				if title and artists:
					key = (title, tuple(artists))
					c = counts.get(key, 0)
					counts[key] = c + 1

			touched: list[int] = []

			for key, value in counts.items():
				title, artists = key
				artists = [x.lower() for x in artists]
				title = title.lower()
				for track in self.pctl.master_library.values():
					if track.artist.lower() in artists and track.title.lower() == title:
						if track.index in touched:
							track.lfm_scrobbles += value
						else:
							track.lfm_scrobbles = value
							touched.append(track.index)
			self.show_message(_("Scanning scrobbles complete"), mode="done")

		except Exception:
			logging.exception("There was an error parsing the data")
			self.show_message(_("There was an error parsing the data"), mode="warning")

		self.gui.request_tracklist_redraw()
		self.lastfm.scanning_scrobbles = False
		self.bg_save()

	def maloja_scrobble(self, track: TrackClass, timestamp: int = int(time.time())) -> bool | None:
		url = self.prefs.maloja_url

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
		d["key"] = self.prefs.maloja_key

		try:
			r = requests.post(url, json=d, timeout=10)
			if r.status_code != 200:
				self.show_message(_("There was an error submitting data to Maloja server"), r.text, mode="warning")
				return False
		except Exception:
			logging.exception("There was an error submitting data to Maloja server")
			self.show_message(_("There was an error submitting data to Maloja server"), mode="warning")
			return False
		return True

	def get_network_thumbnail_url(self, track_object: TrackClass) -> str | None:
		if track_object.file_ext == "TIDAL":
			return track_object.art_url_key
		if track_object.file_ext == "PLEX":
			url = self.plex.resolve_thumbnail(track_object.art_url_key)
			assert url is not None
			return url
		#if track_object.file_ext == "JELY":
		#	url = jellyfin.resolve_thumbnail(track_object.art_url_key)
		#	assert url is not None
		#	assert url
		#	return url
		if track_object.file_ext == "TAU":
			url = self.tau.resolve_picture(track_object.art_url_key)
			assert url
			return url
		return None

	def jellyfin_get_playlists_thread(self) -> None:
		if self.jellyfin.scanning:
			self.inp.mouse_click = False
			self.show_message(_("Job already in progress!"))
			return
		self.jellyfin.scanning = True
		shoot_dl = threading.Thread(target=self.jellyfin.get_playlists)
		shoot_dl.daemon = True
		shoot_dl.start()

	def jellyfin_get_library_thread(self) -> None:
		self.pref_box.close()
		save_prefs(bag=self.bag)
		if self.jellyfin.scanning:
			self.inp.mouse_click = False
			self.show_message(_("Job already in progress!"))
			return

		self.jellyfin.scanning = True
		shoot_dl = threading.Thread(target=self.jellyfin.ingest_library)
		shoot_dl.daemon = True
		shoot_dl.start()

	def plex_cancel_two_factor(self) -> None:
		self.plex.two_factor_required = False
		self.text_plex_2fa.text = ""
		self.plex.connected = False
		self.plex.resource = None
		self.plex.scanning = False
		self.gui.request_frame()

	def plex_get_album_thread(self) -> None:
		if self.plex.scanning:
			self.inp.mouse_click = False
			self.show_message(_("Already scanning!"))
			return

		# If the user has 2FA enabled, Plex may require a verification code.
		# In that case we keep the settings window open and prompt for the code.
		if self.plex.two_factor_required:
			code = self.text_plex_2fa.text.strip()
			if not code:
				self.show_message(_("Enter two-factor code"), mode="warning")
				return
			if not self.plex.connect(code=code):
				return
			self.text_plex_2fa.text = ""
		elif not self.plex.connect():
			return

		self.pref_box.close()
		save_prefs(bag=self.bag)
		self.plex.scanning = True

		shoot_dl = threading.Thread(target=self.plex.get_albums)
		shoot_dl.daemon = True
		shoot_dl.start()

	def sub_get_album_thread(self) -> None:
		self.pref_box.close()
		save_prefs(bag=self.bag)
		if self.subsonic.scanning:
			self.inp.mouse_click = False
			self.show_message(_("Already scanning!"))
			return
		self.subsonic.scanning = True

		shoot_dl = threading.Thread(target=self.subsonic.get_music3)
		shoot_dl.daemon = True
		shoot_dl.start()

	def track_number_process(self, line: str) -> str:
		line = str(line).split("/", 1)[0].lstrip("0")
		if self.prefs.dd_index and len(line) == 1:
			return "0" + line
		return line

	def tag_scan(self, nt: TrackClass) -> TrackClass | None:
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
				logging.error("File not found when executing getmtime!")  # noqa: TRY400
				nt.found = False
				return nt
			except Exception:
				logging.exception("Unknown error executing getmtime!")
				nt.found = False
				return nt

			for _mk in _MISC_TO_FIELD.values():
				setattr(nt, _mk, None)
			nt.file_ext = os.path.splitext(os.path.basename(nt.fullpath))[1][1:].upper()

			if nt.file_ext.lower() in self.formats.GME and self.gme:
				emu = ctypes.c_void_p()
				track_info = ctypes.POINTER(GMETrackInfo)()
				err = self.gme.gme_open_file(nt.fullpath.encode("utf-8"), ctypes.byref(emu), -1)
				#logging.error(err)
				if not err:
					n = nt.subtrack
					err = self.gme.gme_track_info(emu, byref(track_info), n)
					#logging.error(err)
					if not err:
						nt.length = track_info.contents.play_length / 1000
						nt.title = track_info.contents.song.decode("utf-8")
						nt.artist = track_info.contents.author.decode("utf-8")
						nt.album = track_info.contents.game.decode("utf-8")
						nt.comment = track_info.contents.comment.decode("utf-8")
						self.gme.gme_free_info(track_info)
					self.gme.gme_delete(emu)

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
			elif nt.file_ext in ("MOD", "IT", "XM", "S3M", "MPTM") and self.mpt:
				with Path(nt.fullpath).open("rb") as file:
					data = file.read()
				MOD1 = MOD.from_address(
					self.mpt.openmpt_module_create_from_memory(
						ctypes.c_char_p(data), ctypes.c_size_t(len(data)), None, None, None))
				nt.length  = self.mpt.openmpt_module_get_duration_seconds(byref(MOD1))
				nt.title   = self.mpt.openmpt_module_get_metadata(byref(MOD1), ctypes.c_char_p(b"title")).decode()
				nt.artist  = self.mpt.openmpt_module_get_metadata(byref(MOD1), ctypes.c_char_p(b"artist")).decode()
				nt.comment = self.mpt.openmpt_module_get_metadata(byref(MOD1), ctypes.c_char_p(b"message_raw")).decode()

				self.mpt.openmpt_module_destroy(byref(MOD1))
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
					nt.synced = audio.synced_lyrics
					if nt.length:
						nt.bitrate = int(nt.size / nt.length * 8 / 1024)
					nt.track_total = audio.track_total
					nt.disc_total = audio.disc_total
					nt.comment = audio.comment
					nt.cue_sheet = audio.cue_sheet
					copy_trackfile_metadata(nt, audio)
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
					if audio.tags:
						TrackFile.read_mutagen_tags(audio.tags, nt)
			elif nt.file_ext in ("OPUS", "OGG", "OGA"):
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
					nt.synced = audio.synced_lyrics
					nt.disc_number = audio.disc_number
					nt.track_total = audio.track_total
					nt.disc_total = audio.disc_total
					nt.comment = audio.comment
					copy_trackfile_metadata(nt, audio)
					if nt.bitrate == 0 and nt.length > 0:
						nt.bitrate = int(nt.size / nt.length * 8 / 1024)
			elif nt.file_ext == "APE":
				audio = mutagen.File(nt.fullpath)
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
					copy_trackfile_metadata(nt, audio)
			elif nt.file_ext in ("WV", "TTA"):
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
					copy_trackfile_metadata(nt, audio)
			else:
				# Use MUTAGEN
				try:
					if nt.file_ext.lower() in self.formats.VID:
						self.scan_ffprobe(nt)
						return nt

					try:
						audio = mutagen.File(nt.fullpath)
					except Exception:
						logging.exception("Mutagen scan failed, falling back to FFPROBE")
						self.scan_ffprobe(nt)
						return nt

					nt.samplerate = audio.info.sample_rate
					nt.bitrate = audio.info.bitrate // 1000
					nt.length = audio.info.length
					nt.size = os.path.getsize(nt.fullpath)

					if not nt.length:
						try:
							startupinfo = None
							if self.windows:
								startupinfo = subprocess.STARTUPINFO()
								startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
							result = subprocess.run([self.get_ffprobe(), "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", nt.fullpath], stdout=subprocess.PIPE, startupinfo=startupinfo, check=True)
							nt.length = float(result.stdout.decode())
						except Exception:
							logging.exception("FFPROBE couldn't supply a duration")

					TrackFile.read_mutagen_tags(audio.tags, nt)
				except Exception:
					logging.exception("Failed loading file through Mutagen")
					raise


			# Parse any multiple artists into list
			artists = nt.artist.split(";")
			if len(artists) > 1:
				for a in artists:
					a = a.strip()
					if a:
						if nt.artists is None:
							nt.artists = []
						if a not in nt.artists:
							nt.artists.append(a)
			find_synced_lyric_data(nt, reload=True) # populates track.synced if it succeeds
		except Exception:
			try:
				if Exception is UnicodeDecodeError:
					logging.exception(f"Unicode decode error on file: {nt.fullpath}")
				else:
					logging.exception(f"Error: Tag read failed on file: {nt.fullpath}")
			except Exception:
				logging.exception(f"Error printing error. Non utf8 not allowed: {nt.fullpath.encode('utf-8', 'surrogateescape').decode('utf-8', 'replace')}")
			return nt
		intern_track_strings(nt)
		if self.pctl.track_queue and nt.index == self.pctl.track_queue[self.pctl.queue_step]:
			self.lyrics_ren_mini.to_reload = True
		return nt

	def notify_song(self, notify_of_end: bool = False, delay: float = 0.0) -> None:
		if not self.de_notify_support:
			return

		if notify_of_end and self.prefs.end_setting != "stop":
			return

		if self.prefs.show_notifications and self.pctl.playing_object() is not None and not window_is_focused(self.t_window):
			if self.prefs.stop_notifications_mini_mode and self.gui.mode == GuiMode.MINI:
				return

			track = self.pctl.playing_object()

			if not track or not (track.title or track.artist or track.album or track.filename):
				return  # only display if we have at least one piece of metadata available

			#i_path = ""
			#try:
			#	if not notify_of_end:
			#		i_path = self.thumb_tracks.path(track)
			#except Exception:
			#	logging.exception(track.fullpath.encode("utf-8", "replace").decode("utf-8"))
			#	logging.error("Thumbnail error")

			top_line = track.title

			if self.prefs.notify_include_album:
				bottom_line = (track.artist + " | " + track.album).strip("| ")
			else:
				bottom_line = track.artist

			if not track.title:
				a, t = filename_to_metadata(clean_string(track.filename))
				if not track.artist:
					bottom_line = a
				top_line = t

			self.gui.notify_main_id = uid_gen()
			id = self.gui.notify_main_id

			if notify_of_end:
				bottom_line = "Tauon Music Box"
				top_line = (_("End of playlist"))
				id = None

			self.song_notification.update(top_line, bottom_line) #, i_path)
			self.notify_image = self.thumb_tracks.pixbuf(track)
			if self.notify_image:
				self.song_notification.set_image_from_pixbuf(self.notify_image)
			else:
				self.song_notification.update(top_line, bottom_line, None)

			shoot_dl = threading.Thread(target=self.notify_song_fire, args=([self.song_notification, delay, id]))
			shoot_dl.daemon = True
			shoot_dl.start()

	def test_auto_lyrics(self, track_object: TrackClass) -> None:
		if not track_object:
			return

		if self.prefs.auto_lyrics and not track_object.lyrics and track_object.index not in self.prefs.auto_lyrics_checked:
			if self.lyrics_check_timer.get() > 5 and self.pctl.playing_time > 1:
				result = self.get_lyric_wiki_silent(track_object)
				if result == "later":
					pass
				else:
					self.lyrics_check_timer.set()
					self.prefs.auto_lyrics_checked.append(track_object.index)

	def hit_discord(self) -> None:
		if not (self.prefs.discord_enable and self.prefs.discord_allow):
			return

		if not hasattr(self, "_discord_loop_guard_lock"):
			self._discord_loop_guard_lock = threading.Lock()
			self._discord_loop_guard_running = False

		with self._discord_loop_guard_lock:
			if self._discord_loop_guard_running:
				return
			self._discord_loop_guard_running = True
			self.prefs.discord_active = True

		try:
			discord_t = threading.Thread(target=self.discord_loop)
			discord_t.daemon = True
			discord_t.start()
		except Exception:
			with self._discord_loop_guard_lock:
				self._discord_loop_guard_running = False
				self.prefs.discord_active = False
			raise

	def _signal_discord(self) -> None:
		"""Ensure Discord RPC thread is running and wake it immediately.

		This starts the RPC thread if needed and sets the wakeup event so
		the background loop processes updates instantly.
		"""
		try:
			if not (self.prefs.discord_enable and self.prefs.discord_allow):
				return

			# Create and set the wakeup event immediately so the RPC thread can
			# observe it without the UI thread polling and sleeping.
			ev = self.__dict__.setdefault("_discord_wakeup_event", threading.Event())
			ev.set()

			try:
				self.hit_discord()
			except Exception:
				# hit_discord already logs on failure; nothing else to do here
				pass
		except Exception:
			logging.exception("Failed to signal Discord wakeup")

	def love(self, set: bool = True, track_id: int | None = None, no_delay: bool = False, notify: bool = False, sync: bool = True) -> bool | None:
		if track_id is None and len(self.pctl.track_queue) < 1:
			return False

		if track_id is not None and track_id < 0:
			return False

		if track_id is None:
			track_id = self.pctl.track_queue[self.pctl.queue_step]

		loved = False
		star = self.star_store.full_get(track_id)

		if star is not None and star.loved:
			loved = True

		if set is False:
			return loved

		# if len(lfm_username) > 0 and not lastfm.connected and not prefs.auto_lfm:
		#	 self.show_message(
		# 	"You have a last.fm account ready but it is not enabled.", 'info',
		# 	'Either connect, enable auto connect, or remove the account.')
		#	 return

		if star is None:
			star = StarRecord()

		loved ^= True

		if notify:
			self.gui.toast_love_object = self.pctl.get_track(track_id)
			self.gui.toast_love_added = loved
			self.toast_love_timer.set()
			self.gui.delay_frame(1.81)

		delay = 0.3
		if no_delay or not sync or not self.lastfm.details_ready():
			delay = 0

		star.loved_timestamp = time.time()

		if loved:
			time.sleep(delay)
			self.gui.request_frame()
			self.gui.request_tracklist_redraw()
			star.loved = True
			self.star_store.insert(track_id, star)
			if sync:
				if self.prefs.last_fm_token:
					try:
						self.lastfm.love(self.pctl.master_library[track_id].artist, self.pctl.master_library[track_id].title)
					except Exception:
						logging.exception("Failed updating last.fm love status")
						self.show_message(_("Failed updating last.fm love status"), mode="warning")
						star.loved = False
						self.star_store.insert(track_id, star)
						self.show_message(
							_("Error updating love to last.fm!"),
							_("Maybe check your internet connection and try again?"), mode="error")

				if self.pctl.master_library[track_id].file_ext == "JELY":
					self.jellyfin.favorite(self.pctl.master_library[track_id])
				if self.pctl.master_library[track_id].file_ext == "SUB":
					self.subsonic.star_track(self.pctl.master_library[track_id])
		else:
			time.sleep(delay)
			self.gui.request_frame()
			self.gui.request_tracklist_redraw()
			star.loved = False
			self.star_store.insert(track_id, star)
			if sync:
				if self.prefs.last_fm_token:
					try:
						self.lastfm.unlove(self.pctl.master_library[track_id].artist, self.pctl.master_library[track_id].title)
					except Exception:
						logging.exception("Failed updating last.fm love status")
						self.show_message(_("Failed updating last.fm love status"), mode="warning")
						star.loved = True
						self.star_store.insert(track_id, star)
				if self.pctl.master_library[track_id].file_ext == "JELY":
					self.jellyfin.favorite(self.pctl.master_library[track_id], un=True)
				if self.pctl.master_library[track_id].file_ext == "SUB":
					self.subsonic.unstar_track(self.pctl.master_library[track_id])

		self.gui.request_tracklist_redraw()
		self.gui.request_frame()
		if sync and self.pctl.mpris is not None:
			self.pctl.mpris.update(force=True)
		return None

	def line_render(self, n_track: TrackClass, p_track: TrackClass, y: int, this_line_playing, album_fade: int, start_x: int, width: int, style: int = 1, ry=None) -> None:
		timec   = self.colours.bar_time
		titlec  = self.colours.title_text
		indexc  = self.colours.index_text
		artistc = self.colours.artist_text
		albumc  = self.colours.album_text

		if this_line_playing is True:
			timec   = self.colours.time_text
			titlec  = self.colours.title_playing
			indexc  = self.colours.index_playing
			artistc = self.colours.artist_playing
			albumc  = self.colours.album_playing

		if n_track.found is False:
			timec   = self.colours.playlist_text_missing
			titlec  = self.colours.playlist_text_missing
			indexc  = self.colours.playlist_text_missing
			artistc = self.colours.playlist_text_missing
			albumc  = self.colours.playlist_text_missing

		# Over the art background, grey row text picks up a hint of the
		# art hue (hls_hue_mix passes coloured text through; no lightness
		# boost for row text). One averaged sample serves the whole
		# tracklist so every row tints the same way.
		so = self.style_overlay
		if so.tracklist_sample is not None:
			timec   = so.tint_from_sample(timec, so.tracklist_sample, 0.2)
			titlec  = so.tint_from_sample(titlec, so.tracklist_sample, 0.2)
			indexc  = so.tint_from_sample(indexc, so.tracklist_sample, 0.2)
			artistc = so.tint_from_sample(artistc, so.tracklist_sample, 0.2)
			albumc  = so.tint_from_sample(albumc, so.tracklist_sample, 0.2)

		artistoffset = 0
		indexLine = ""

		offset_font_extra = 0
		if self.gui.row_font_size > 14:
			offset_font_extra = 8

		# In windows (arial?) draws numbers too high (hack fix)
		num_y_offset = 0
		# if system == 'Windows':
		#    num_y_offset = 1

		if True or style == 1:
			# if not gui.rsp and not gui.combo_mode:
			#     width -= 10 * gui.scale

			dash = False
			if n_track.artist and self.colours.artist_text == self.colours.title_text:
				dash = True

			if n_track.title:
				line = self.track_number_process(n_track.track_number)
				indexLine = line

				if self.prefs.use_absolute_track_index and self.pctl.multi_playlist[self.pctl.active_playlist_viewing].hide_title:
					indexLine = str(p_track)
					if len(indexLine) > 3:
						indexLine += "  "

				line = ""

				if n_track.artist and not dash:
					line0 = n_track.artist

					artistoffset = self.ddt.text(
						(start_x + 27 * self.gui.scale, y),
						line0,
						alpha_mod(artistc, album_fade),
						self.gui.row_font_size,
						int(width / 2))

					line = n_track.title
				else:
					line += n_track.title
			else:
				line = \
					os.path.splitext(n_track.filename)[
						0]

			if p_track >= len(self.pctl.default_playlist):
				self.gui.request_tracklist_redraw()
				return

			index = self.pctl.default_playlist[p_track]
			star_x = 0
			total = self.star_store.get(index)

			if self.gui.star_mode == "line" and total > 0 and self.pctl.master_library[index].length > 0:
				ratio = total / self.pctl.master_library[index].length
				if ratio > 0.55:
					star_x = int(ratio * 4 * self.gui.scale)
					star_x = min(star_x, 60 * self.gui.scale)
					sp = y - 0 - self.gui.playlist_text_offset + int(self.gui.playlist_row_height / 2)
					if self.gui.playlist_row_height > 17 * self.gui.scale:
						sp -= 1

					lh = 1
					if self.gui.scale != 1:
						lh = 2

					colour = self.colours.star_line
					if this_line_playing and self.colours.star_line_playing is not None:
						colour = self.colours.star_line_playing

					self.ddt.rect(
						[
							width + start_x - star_x - 45 * self.gui.scale - offset_font_extra,
							sp,
							star_x + 3 * self.gui.scale,
							lh],
						alpha_mod(colour, album_fade))

					star_x += 6 * self.gui.scale

			show_rating_stars = self.gui.show_ratings or self.prefs.rating_playtime_stars
			if show_rating_stars:
				sx = round(width + start_x - round(40 * self.gui.scale) - offset_font_extra)
				sy = round(ry + (self.gui.playlist_row_height // 2) - round(7 * self.gui.scale))
				sx -= round(68 * self.gui.scale)

				self.draw_rating_widget(
					sx,
					sy,
					n_track,
					allow_input=self.gui.show_ratings,
					hint_only=not self.gui.show_ratings,
				)

				star_x += round(70 * self.gui.scale)

			if self.gui.show_hearts:
				xxx = star_x

				count = 0
				spacing = 6 * self.gui.scale

				yy = ry + (self.gui.playlist_row_height // 2) - (5 * self.gui.scale)
				if self.gui.scale == 1.25:
					yy += 1
				if xxx > 0:
					xxx += 3 * self.gui.scale

				if self.love(False, index):
					count = 1
					x = width + start_x - 52 * self.gui.scale - offset_font_extra - xxx
					self.f_store.store(self.display_you_heart, (x, yy))
					star_x += 18 * self.gui.scale

				for name in self.pctl.master_library[index].lfm_friend_likes:
					# Limit to number of hears to display
					if self.gui.star_mode == "none":
						if count > 6:
							break
					elif count > 4:
						break

					x = width + start_x - 52 * self.gui.scale - offset_font_extra - (self.gui.heart_row_icon.w + spacing) * count - xxx
					self.f_store.store(self.display_friend_heart, (x, yy, name))
					count += 1
					star_x += self.gui.heart_row_icon.w + spacing + 2

			# Draw track number/index
			display_queue = False

			if self.pctl.force_queue:
				marks = []
				album_type = False
				for i, item in enumerate(self.pctl.force_queue):
					if item.track_id == n_track.index and item.position == p_track and item.playlist_id == self.pctl.pl_to_id(
							self.pctl.active_playlist_viewing):
						if item.type == QueueType.TRACK:  # Only show mark if track type
							marks.append(i)
						# else:
						# 	album_type = True
						# 	marks.append(i)

				if marks:
					display_queue = True

			if display_queue:
				li = str(marks[0] + 1)
				if li == "1":
					li = "N"
					# if item.track_id == n_track.index and item.position == p_track and item.playlist_id == pctl.active_playlist_viewing
					if self.pctl.playing_ready() and n_track.index == self.pctl.track_queue[self.pctl.queue_step] \
					and p_track == self.pctl.playlist_playing_position:
						li = "R"
					# if album_type:
					# 	li = "A"

				# rect = (start_x + 3 * self.gui.scale, y - 1 * self.gui.scale, 5 * self.gui.scale, 5 * self.gui.scale)
				# self.ddt.rect_r(rect, [100, 200, 100, 255], True)
				if len(marks) > 1:
					li += " " + ("." * (len(marks) - 1))
					li = li[:5]

				# if album_type:
				# 	li += "🠗"

				colour = ColourRGBA(244, 200, 66, 255)
				if self.colours.lm:
					colour = ColourRGBA(220, 40, 40, 255)

				self.ddt.text(
					(start_x + 5 * self.gui.scale, y, 2),
					li, colour, self.gui.row_font_size + 200 - 1)
			elif len(indexLine) > 2:
				self.ddt.text(
					(start_x + 5 * self.gui.scale, y, 2), indexLine,
					alpha_mod(indexc, album_fade), self.gui.row_font_size)
			else:
				self.ddt.text(
					(start_x, y), indexLine,
					alpha_mod(indexc, album_fade), self.gui.row_font_size)

			if dash and n_track.artist and n_track.title:
				line = n_track.artist + " - " + n_track.title

			self.ddt.text(
				(start_x + 33 * self.gui.scale + artistoffset, y),
				line,
				alpha_mod(titlec, album_fade),
				self.gui.row_font_size,
				width - 71 * self.gui.scale - artistoffset - star_x - 20 * self.gui.scale)

			line = get_display_time(n_track.length)

			self.ddt.text(
				(width + start_x - (round(36 * self.gui.scale) + offset_font_extra),
				y + num_y_offset, 0), line,
				alpha_mod(timec, album_fade), self.gui.row_font_size)

			self.f_store.recall_all()

	def clear_img_cache(self, delete_disk: bool = True) -> None:
		self.album_art_gen.clear_cache()
		self.prefs.failed_artists.clear()
		self.gall_ren.key_list = []

		i = 0
		while len(self.gall_ren.queue) > 0:
			time.sleep(0.01)
			i += 1
			if i > 5 / 0.01:
				break

		for key, value in self.gall_ren.gall.items():
			sdl3.SDL_DestroyTexture(value[2])
		self.gall_ren.gall = {}

		if delete_disk:
			dirs = [self.g_cache_directory, self.n_cache_directory, self.e_cache_directory]
			for direc in dirs:
				if os.path.isdir(direc):
					for item in os.listdir(direc):
						path = os.path.join(direc, item)
						os.remove(path)

		self.prefs.failed_artists.clear()
		for key, value in self.artist_list_box.thumb_cache.items():
			if value:
				sdl3.SDL_DestroyTexture(value[0])
		self.artist_list_box.thumb_cache.clear()
		self.gui.request_frame()

	def clear_track_image_cache(self, track: TrackClass) -> None:
		self.gui.halt_image_rendering = True
		if self.gall_ren.queue:
			time.sleep(0.05)
		if self.gall_ren.queue:
			time.sleep(0.2)
		if self.gall_ren.queue:
			time.sleep(0.5)

		direc = os.path.join(self.g_cache_directory)
		if os.path.isdir(direc):
			for item in os.listdir(direc):
				n = item.split("-")
				if len(n) > 2 and n[2] == str(track.index):
					os.remove(os.path.join(direc, item))
					logging.info(f"Cleared cache thumbnail: {os.path.join(direc, item)}")

		keys = set()
		for key, value in self.gall_ren.gall.items():
			if key[0] == track:
				sdl3.SDL_DestroyTexture(value[2])
				if key not in keys:
					keys.add(key)
		for key in keys:
			del self.gall_ren.gall[key]
			if key in self.gall_ren.key_list:
				self.gall_ren.key_list.remove(key)

		self.gui.halt_image_rendering = False
		self.album_art_gen.clear_cache()

	def signal_handler(self, signum, frame) -> None:
		signal.signal(signum, signal.SIG_IGN) # ignore additional signals
		self.exit(reason="SIGINT received")

	def save_state(self) -> None:
		gui   = self.gui
		pctl  = self.pctl
		prefs = self.prefs
		view_prefs = prefs.view_prefs

		if self.bag.should_save_state:
			logging.info("Writing database to disk... ")
		else:
			logging.warning("Dev mode, not saving state... ")
			return

		view_prefs["update-title"] = prefs.update_title
		view_prefs["side-panel"] = prefs.prefer_side
		view_prefs["dim-art"] = prefs.dim_art
		# view_prefs['pl-follow'] = pl_follow
		view_prefs["scroll-enable"] = prefs.scroll_enable
		view_prefs["smooth-scroll-enable"] = prefs.smooth_scroll_enable
		view_prefs["smooth-scroll-speed"] = prefs.smooth_scroll_speed
		view_prefs["break-enable"] = prefs.break_enable
		view_prefs["append-date"] = prefs.append_date

		tauonplaylist_jar = []
		radioplaylist_jar = []
		tauonqueueitem_jar = []
		trackclass_jar = []
		for v in pctl.multi_playlist:
			tauonplaylist_jar.append(v.__dict__)
		for v in pctl.radio_playlists:
			radioplaylist_jar.append(v.__dict__)
		for v in pctl.force_queue:
			tauonqueueitem_jar.append(v.__dict__)
		for v in pctl.master_library.values():
			trackclass_jar.append({k: getattr(v, k) for k in v.__slots__})

		# Columns header-bar config is per custom-slot (stored in
		# custom_layouts.json). Persist the PRESET columns to state.p — while a
		# custom slot is active gui holds the slot's columns, so use the backup.
		_custom = getattr(self, "custom", None)
		if _custom is not None:
			_pcols = _custom.preset_columns_snapshot()
			if gui.custom_mode:
				# Flush any live column edits to the slot's json too.
				_custom.save_slots()
		else:
			_pcols = {"pl_st": gui.pl_st, "set_bar": gui.set_bar,
				"set_mode": gui.set_mode, "pl_st_left": gui.pl_st_left}

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
			pctl.default_playlist,  # not read from here (keep to avoid db version bump)
			None,  # pctl.playlist_playing_position,
			None,  # Was cue list
			"",  # radio_field.text,
			prefs.theme,
			self.folder_image_offsets,
			None,  # lfm_username,
			None,  # lfm_hash,
			self.latest_db_version,  # Used for upgrading
			view_prefs,
			gui.save_size,
			None,  # old side panel size
			0,  # save time (unused)
			gui.vis_want,  # gui.vis
			pctl.selected_in_playlist,
			self.album_mode_art_size,
			self.draw_border,
			prefs.enable_web,
			prefs.allow_remote,
			prefs.expose_web,
			None,  # prefs.enable_transcode, legacy slot kept for state.p compatibility
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
			_pcols["pl_st"],
			None,  # gui.set_mode,
			None,
			prefs.playlist_row_height,
			prefs.show_wiki,
			prefs.auto_extract,
			prefs.colour_from_image,
			_pcols["set_bar"],
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
			self.prefs.album_mode,
			None,  # gui.album_playlist_width
			prefs.transcode_opus_as,
			gui.star_mode if gui.star_mode == "line" else "none",
			prefs.prefer_side,  # gui.rsp,
			gui.lsp,
			gui.rspw,
			gui.pref_gallery_w,
			gui.pref_rspw,
			gui.show_hearts,
			prefs.monitor_downloads,  # 76
			gui.artist_info_panel,  # 77
			prefs.extract_to_music,  # 78
			self.lb.enable,
			None,  # lb.key,
			self.rename_files.text,
			self.rename_folder.text,
			prefs.use_jump_crossfade,
			prefs.use_transition_crossfade,
			prefs.show_notifications,
			prefs.true_shuffle,
			_pcols["set_mode"],
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
			None,  # was prefs.art_bg_always_blur
			prefs.failed_artists,
			prefs.artist_list,
			None,  # prefs.auto_sort,
			prefs.lyrics_enables,
			prefs.fanart_notify,
			None,  # legacy removed background mode slot,
			None,  # prefs.discogs_pat,
			prefs.mini_mode_mode,
			self.after_scan,
			gui.gallery_positions,
			prefs.chart_bg,
			prefs.left_panel_mode,
			gui.last_left_panel_mode,
			None, #prefs.gst_device,
			self.search_string_cache,
			self.search_dia_string_cache,
			pctl.gen_codes,
			gui.show_ratings,
			gui.show_album_ratings,
			prefs.radio_urls,
			gui.showcase_mode,  # gui.combo_mode,
			self.top_panel.prime_tab,
			self.top_panel.prime_side,
			prefs.sync_playlist,
			"",
			"",
			prefs.show_band,
			prefs.download_playlist,
			[],
			prefs.auto_rec,
			"",
			prefs.use_libre_fm,
			self.playlist_box.scroll_on,
			prefs.artist_list_sort_mode,
			prefs.phazor_device_selected,
			prefs.failed_background_artists,
			prefs.bg_flips,
			prefs.tray_show_title,
			prefs.artist_list_style,
			trackclass_jar,
			prefs.premium,
			gui.radio_view,
			radioplaylist_jar, # pctl.radio_playlists,
			pctl.radio_playlist_viewing,
			prefs.radio_thumb_bans,
			prefs.playlist_exports,
			prefs.show_chromecast,
			prefs.cache_list,
			prefs.shuffle_lock,
			prefs.album_shuffle_lock_mode,
			gui.was_radio,
			"",
			"",
			prefs.artist_list_threshold,
			prefs.tray_theme,
			prefs.row_title_format,
			prefs.row_title_genre,
			prefs.row_title_separator_type,  # No longer used
			prefs.replay_preamp,  # 181
			prefs.gallery_combine_disc,
			pctl.active_playlist_playing,  # 183
			prefs.milk,
			prefs.auto_milk,
			str(prefs.loaded_preset) if prefs.loaded_preset else None,  # 186 — as str, a pickled Path is OS-specific
			int(pctl.stop_mode),
			pctl.stop_ref,
			prefs.start_in_tray,  # 189
			gui.custom_mode,  # 190
			prefs.spectrogram_colour,  # 191
			_pcols["pl_st_left"],  # 192
			prefs.milk_cut_out,  # 193
			prefs.milk_favorite_presets,  # 194
			prefs.art_bg_frosted,  # 195
			prefs.replay_allow_compression,  # 196
		]

		try:
			with atomic_save(self.user_directory / "state.p.backup") as file:
				pickle.dump(save, file, protocol=pickle.HIGHEST_PROTOCOL)
			# if not pctl.running:
			with atomic_save(self.user_directory / "state.p") as file:
				pickle.dump(save, file, protocol=pickle.HIGHEST_PROTOCOL)

			old_position = self.old_window_position
			if not prefs.save_window_position:
				old_position = None

			save = [
				self.draw_border,
				gui.save_size,
				prefs.window_opacity,
				gui.scale,
				gui.maximized,
				old_position,
			]

			if not self.fs_mode:
				with atomic_save(self.user_directory / "window.p") as file:
					pickle.dump(save, file, protocol=pickle.HIGHEST_PROTOCOL)

			with atomic_save(self.user_directory / "lyrics_substitutions.json", "w") as file:
				json.dump(prefs.lyrics_subs, file)

			save_prefs(bag=self.bag)

			# Save playlists to export
			for pl, playlist in enumerate(pctl.multi_playlist):
				id = pctl.pl_to_id(pl)
				if id is None:
					continue
				if playlist.auto_export is False:
					continue

				# if the playlist should auto import, but it hasn't since the file was last changed
				if playlist.auto_import:
					target = pctl.resolve_full_playlist_path(playlist)
					path = Path(target)
					if path.exists():
						filesize = path.stat().st_size
						if filesize and filesize != playlist.file_size:
							logging.warning("Playlist has changed on disk - Skipping overwrite")
							logging.warning(f"-- {path}")
							continue

				self.export_playlist_box.run_export(id, warnings=False)

			logging.info("Done writing database")

		except PermissionError:
			logging.exception("Permission error encountered while writing database")
			self.show_message(_("Permission error encountered while writing database"), "error")
		except Exception:
			logging.exception("Unknown error encountered while writing database")

	def draw_linked_text(self, location: tuple[int, int], text: str, colour: list[int], font: int, force: bool = False, replace: str = "") -> tuple[int, int, str]:
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

		left = self.ddt.get_text_w(base, font)
		right = self.ddt.get_text_w(base + link_text, font)

		x = location[0]
		y = location[1]

		self.ddt.text((x, y), base, colour, font)
		self.ddt.text((x + left, y), link_text, self.colours.link_text, font)
		self.ddt.text((x + right, y), rest, colour, font)

		tweak = font
		while tweak > 100:
			tweak -= 100

		if self.gui.scale == 2:
			tweak *= 2
			tweak += 4
		elif self.gui.scale != 1:
			tweak = round(tweak * self.gui.scale)
			tweak += 2

		# self.ddt.line(x + left, y + tweak + 2, x + right, y + tweak + 2, alpha_mod(self.colours.link_text, 120))
		self.ddt.rect((x + left, y + tweak + 2, right - left, round(1 * self.gui.scale)), alpha_mod(self.colours.link_text, 120))

		return left, right - left, target_link

	def draw_linked_text2(self, x: int, y: int, text: str, colour: list[int], font: int, click: bool = False, replace: str = "") -> None:
		link_pa = self.draw_linked_text(
			(x, y), text, colour, font, replace=replace)
		link_rect = [x + link_pa[0], y, link_pa[1], 18 * self.gui.scale]
		if self.coll(link_rect):
			if not click:
				self.gui.cursor_want = 3
			if click:
				webbrowser.open(link_pa[2], new=2, autoraise=True)
		self.fields.add(link_rect)

	def link_activate(self, x: int, y: int, link_pa: str, click: bool | None = None) -> None:
		link_rect = [x + link_pa[0], y - 2 * self.gui.scale, link_pa[1], 20 * self.gui.scale]

		if click is None:
			click = self.inp.mouse_click

		self.fields.add(link_rect)
		if self.coll(link_rect):
			if not click:
				self.gui.cursor_want = 3
			if click:
				webbrowser.open(link_pa[2], new=2, autoraise=True)

	def trunc_line(self, line: str, font: str, px: int, dots: bool = True) -> str:
		"""This old function is slow and should be avoided"""
		if self.ddt.get_text_w(line, font) < px + 10:
			return line

		if dots:
			while self.ddt.get_text_w(line.rstrip(" ") + self.gui.trunk_end, font) > px:
				if len(line) == 0:
					return self.gui.trunk_end
				line = line[:-1]
			return line.rstrip(" ") + self.gui.trunk_end

		while self.ddt.get_text_w(line, font) > px:
			line = line[:-1]
			if len(line) < 2:
				break

		return line

	def right_trunc(self, line: str, font: str, px: int, dots: bool = True) -> str:
		if self.ddt.get_text_w(line, font) < px + 10:
			return line

		if dots:
			while self.ddt.get_text_w(line.rstrip(" ") + self.gui.trunk_end, font) > px:
				if len(line) == 0:
					return self.gui.trunk_end
				line = line[1:]
			return self.gui.trunk_end + line.rstrip(" ")

		while self.ddt.get_text_w(line, font) > px:
			# trunk = True
			line = line[1:]
			if len(line) < 2:
				break
		# if trunk and dots:
		#	 line = line.rstrip(" ") + self.gui.trunk_end
		return line

	# def trunc_line2(self, line, font, px):
	#	 trunk = False
	#	 p = self.ddt.get_text_w(line, font)
	#	 if p == 0 or p < px + 15:
	#		 return line
	#
	#	 tl = line[0:(int(px / p * len(line)) + 3)]
	#
	#	 if self.ddt.get_text_w(line.rstrip(" ") + self.gui.trunk_end, font) > px:
	#		 line = tl
	#
	#	 while self.ddt.get_text_w(line.rstrip(" ") + self.gui.trunk_end, font) > px + 10:
	#		 trunk = True
	#		 line = line[:-1]
	#		 if len(line) < 1:
	#			 break
	#
	#	 return line.rstrip(" ") + self.gui.trunk_end

	def sort_track_2(self, pl: int, custom_list: list[int] | None = None) -> None:
		current_folder = ""
		current_album = ""
		current_date = ""
		albums: list[int] = []
		playlist = self.pctl.multi_playlist[pl].playlist_ids if custom_list is None else custom_list

		for i in range(len(playlist)):
			tr = self.pctl.master_library[playlist[i]]
			track_date = (tr.rdat if tr.rdat is not None else tr.date)
			if i == 0:
				albums.append(i)
				current_folder = tr.parent_folder_path
				current_album = tr.album
				current_date = track_date
				current_artist = tr.album_artist
			elif tr.parent_folder_path != current_folder:
				if tr.album == current_album and tr.album and track_date == current_date and tr.disc_number \
						and tr.album_artist == current_artist \
						and os.path.dirname(tr.parent_folder_path) == os.path.dirname(current_folder):
					continue
				current_folder = tr.parent_folder_path
				current_album = tr.album
				current_date = track_date
				current_artist = tr.album_artist
				albums.append(i)

		i = 0
		while i < len(albums) - 1:
			playlist[albums[i]:albums[i + 1]] = sorted(playlist[albums[i]:albums[i + 1]], key=self.pctl.index_key)
			i += 1
		if len(albums) > 0:
			playlist[albums[i]:] = sorted(playlist[albums[i]:], key=self.pctl.index_key)

		self.gui.request_tracklist_redraw()

	def key_filepath(self, index: int) -> tuple[str, str]:
		track = self.pctl.master_library[index]
		return track.parent_folder_path.lower(), track.filename

	def key_fullpath(self, index: int) -> str:
		return self.pctl.master_library[index].fullpath.lower()

	#def key_filename(index: int):
	#	track = self.pctl.master_library[index]
	#	return track.filename

	def sort_path_pl(self, pl: int, custom_list: list[int] | None = None) -> None:
		target = self.pctl.multi_playlist[pl].playlist_ids if custom_list is None else custom_list

		if self.use_natsort and False:
			target[:] = natsort.os_sorted(target, key=self.key_fullpath)
		else:
			target.sort(key=self.key_filepath)

	def toggle_gimage(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.show_gimage
		self.prefs.show_gimage ^= True
		return None

	def toggle_chromecast(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.show_chromecast
		self.prefs.show_chromecast ^= True
		return None

	def toggle_transfer(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.show_transfer
		self.prefs.show_transfer ^= True

		if self.prefs.show_transfer:
			self.show_message(
				_("Warning! Using this function moves physical folders."),
				_("This menu entry appears after selecting 'copy'. See manual (github wiki) for more info."),
				mode="info")
		return None

	def toggle_rym(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.show_rym
		self.prefs.show_rym ^= True
		return None

	def show_rym_menu_item(self, _reference: object) -> bool:
		return self.prefs.show_rym

	def toggle_band(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.show_band
		self.prefs.show_band ^= True
		return None

	def show_band_menu_item(self, _reference: object) -> bool:
		return self.prefs.show_band

	def toggle_wiki(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.show_wiki
		self.prefs.show_wiki ^= True
		return None

	def show_wiki_menu_item(self, _reference: object) -> bool:
		return self.prefs.show_wiki

	# def toggle_show_discord(self, mode: int = 0) -> bool:
	# 	if mode == 1:
	# 	return self.prefs.discord_show
	# 	if self.prefs.discord_show is False and self.prefs.discord_allow is False:
	# 	self.show_message(_("Warning: pypresence package not installed"))
	# 	self.prefs.discord_show ^= True

	def toggle_gen(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.show_gen
		self.prefs.show_gen ^= True
		return None

	def show_gen_menu_item(self, _reference: object) -> bool:
		return self.prefs.show_gen

	def toggle_dim_albums(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.dim_art

		self.prefs.dim_art ^= True
		self.gui.request_tracklist_redraw()
		self.gui.request_frame()
		return None

	def toggle_gallery_combine(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.gallery_combine_disc

		self.prefs.gallery_combine_disc ^= True
		self.reload_albums()
		return None

	def toggle_gallery_click(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.gallery_single_click

		self.prefs.gallery_single_click ^= True
		return None

	def toggle_gallery_thin(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.thin_gallery_borders

		self.prefs.thin_gallery_borders ^= True
		self.gui.request_frame()
		self.update_layout_do()
		return None

	def toggle_gallery_row_space(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.increase_gallery_row_spacing

		self.prefs.increase_gallery_row_spacing ^= True
		self.gui.request_frame()
		self.update_layout_do()
		return None

	def toggle_galler_text(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.gui.gallery_show_text

		self.gui.gallery_show_text ^= True
		self.gui.request_frame()
		self.update_layout_do()

		# Jump to playing album
		if self.prefs.album_mode and self.gui.first_in_grid is not None:
			if self.gui.first_in_grid < len(self.pctl.default_playlist):
				self.goto_album(self.gui.first_in_grid, force=True)
		return None

	def toggle_card_style(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.use_card_style

		self.prefs.use_card_style ^= True
		self.gui.request_frame()
		return None

	def toggle_side_panel(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.prefer_side

		self.prefs.prefer_side ^= True
		self.gui.update_layout = True

		if self.prefs.album_mode or self.prefs.prefer_side is True:
			self.gui.rsp = True
		else:
			self.gui.rsp = False

		if self.prefs.prefer_side:
			self.gui.rspw = self.gui.pref_rspw
		return None

	# --- Background style: one mutually exclusive choice between the plain
	# theme, window transparency, auto-theming from art, and the album-art
	# backgrounds (settings → theme card)

	def _clear_background_style(self) -> None:
		"""Turn every background-style mode off (back to the base theme)"""
		if self.prefs.art_bg:
			self.prefs.art_bg = False
			self.style_overlay.flush()
			self.thread_manager.ready("style")
		if self.prefs.transparent_mode:
			self.prefs.transparent_mode = 0
			self.gui.reload_theme = True  # Restores panel alphas
		if self.prefs.colour_from_image:
			self.prefs.colour_from_image = False
			self.gui.theme_temp_current = -1
			self.gui.reload_theme = True
		self.gui.update_layout = True  # Removes panel translucency
		self.gui.request_frame()
		self.gui.request_tracklist_redraw()

	def set_bg_style_base(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return not self.prefs.art_bg and not self.prefs.transparent_mode and not self.prefs.colour_from_image
		self._clear_background_style()
		return None

	def set_bg_style_transparent_accent(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.transparent_mode == 1 and not self.prefs.art_bg and not self.prefs.colour_from_image
		self._clear_background_style()
		self.prefs.transparent_mode = 1
		self.gui.reload_theme = True
		return None

	def set_bg_style_full_transparent(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.transparent_mode == 2 and not self.prefs.art_bg and not self.prefs.colour_from_image
		self._clear_background_style()
		self.prefs.transparent_mode = 2
		self.gui.reload_theme = True
		return None

	def set_bg_style_colourise(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.colour_from_image and not self.prefs.art_bg
		self._clear_background_style()
		self.prefs.colour_from_image = True
		self.gui.theme_temp_current = -1
		self.gui.reload_theme = True
		return None

	def _set_art_bg(self, frosted: bool, stronger: int, fanart: bool = False) -> None:
		# Leaving the other background styles
		if self.prefs.transparent_mode:
			self.prefs.transparent_mode = 0
			self.gui.reload_theme = True
		if self.prefs.colour_from_image:
			self.prefs.colour_from_image = False
			self.gui.theme_temp_current = -1
			self.gui.reload_theme = True
		# The blur image only needs regenerating when the look or source
		# changes; strength is applied at draw time via panel translucency
		regenerate = (
			not self.prefs.art_bg
			or self.prefs.art_bg_frosted != frosted
			or self.prefs.enable_fanart_bg != fanart)
		self.prefs.art_bg = True
		self.prefs.art_bg_frosted = frosted
		self.prefs.art_bg_stronger = stronger
		self.prefs.enable_fanart_bg = fanart
		self.gui.update_layout = True  # Applies panel translucency at the new level
		if regenerate:
			self.style_overlay.flush()
			self.thread_manager.ready("style")
		self.gui.request_frame()

	def set_art_bg_clear(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.art_bg and not self.prefs.art_bg_frosted and not self.prefs.enable_fanart_bg
		self._set_art_bg(frosted=False, stronger=1)
		return None

	def set_art_bg_artist(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.art_bg and self.prefs.enable_fanart_bg
		self._set_art_bg(frosted=False, stronger=1, fanart=True)
		return None

	def set_art_bg_frosted_low(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.art_bg and self.prefs.art_bg_frosted \
				and not self.prefs.enable_fanart_bg and self.prefs.art_bg_stronger < 3
		self._set_art_bg(frosted=True, stronger=1)
		return None

	def set_art_bg_frosted_high(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.art_bg and self.prefs.art_bg_frosted \
				and not self.prefs.enable_fanart_bg and self.prefs.art_bg_stronger >= 3
		self._set_art_bg(frosted=True, stronger=3)
		return None

	def toggle_notifications(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.show_notifications

		self.prefs.show_notifications ^= True

		if self.prefs.show_notifications and not self.de_notify_support:
			self.show_message(_("Notifications for this DE not supported"), "", mode="warning")
		return None

	# def toggle_al_pref_album_artist(self, mode: int = 0) -> bool:
	# 	if mode == 1:
	# 		return self.prefs.artist_list_prefer_album_artist
	# 	self.prefs.artist_list_prefer_album_artist ^= True
	# 	self.artist_list_box.saves.clear()
	# 	return None

	def toggle_mini_lyrics(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.show_lyrics_side
		self.prefs.show_lyrics_side ^= True
		return None

	def toggle_showcase_vis(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.showcase_vis

		self.prefs.showcase_vis ^= True
		self.gui.update_layout = True
		return None

	# def toggle_force_subpixel(self, mode: int = 0) -> bool | None:
	# 	if mode == 1:
	# 		return self.prefs.force_subpixel_text != 0
	#
	# 	self.prefs.force_subpixel_text ^= True
	# 	self.ddt.force_subpixel_text = self.prefs.force_subpixel_text
	# 	self.ddt.clear_text_cache()

	# def toggle_queue(self, mode: int = 0) -> bool:
	#	 if mode == 1:
	#		 return self.prefs.show_queue
	#	 self.prefs.show_queue ^= True
	#	 self.prefs.show_queue ^= True

	def star_line_toggle(self, mode: int= 0) -> bool | None:
		if mode == 1:
			return self.gui.star_mode == "line"

		if self.gui.star_mode == "line":
			self.gui.star_mode = "none"
		else:
			self.gui.star_mode = "line"
			self.gui.show_ratings = False
			self.prefs.rating_playtime_stars = False

		self.gui.request_frame()
		self.gui.request_tracklist_redraw()
		return None

	def star_toggle(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.rating_playtime_stars

		self.prefs.rating_playtime_stars ^= True
		if self.prefs.rating_playtime_stars or self.gui.star_mode == "star":
			self.gui.star_mode = "none"

		# self.gui.show_ratings = False
		self.gui.request_frame()
		self.gui.request_tracklist_redraw()
		return None

	def heart_toggle(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.gui.show_hearts

		self.gui.show_hearts ^= True
		# self.gui.show_ratings = False

		self.gui.request_frame()
		self.gui.request_tracklist_redraw()
		return None

	def album_rating_toggle(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.gui.show_album_ratings

		self.gui.show_album_ratings ^= True
		self.gui.request_frame()
		self.gui.request_tracklist_redraw()
		return None

	def rating_toggle(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.gui.show_ratings

		self.gui.show_ratings ^= True

		if self.gui.show_ratings:
			# gui.show_hearts = False
			self.gui.star_mode = "none"
			self.prefs.rating_playtime_stars = True
			if not self.prefs.write_ratings:
				self.show_message(_("Note that ratings are stored in the local database and not written to tags."))

		self.gui.request_frame()
		self.gui.request_tracklist_redraw()
		return None

	def toggle_titlebar_line(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.update_title

		line = self.window_title
		sdl3.SDL_SetWindowTitle(self.t_window, line)
		self.prefs.update_title ^= True
		if self.prefs.update_title:
			self.update_title_do()
		return None

	def toggle_meta_persists_stop(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.meta_persists_stop
		self.prefs.meta_persists_stop ^= True
		return None

	def toggle_side_panel_layout(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.side_panel_layout == 1

		if self.prefs.side_panel_layout == 1:
			self.prefs.side_panel_layout = 0
		else:
			self.prefs.side_panel_layout = 1
		self.gui.update_layout = True
		self.gui.request_frame()
		return None

	def toggle_side_panel_side(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.side_panel_left
		self.prefs.side_panel_left ^= True
		self.gui.update_layout = True
		self.gui.request_frame()
		return None

	def toggle_meta_shows_selected(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.meta_shows_selected_always
		self.prefs.meta_shows_selected_always ^= True
		return None

	def scale1(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.ui_scale == 1

		self.prefs.ui_scale = 1
		self.pref_box.small_preset()

		if self.prefs.ui_scale != self.gui.scale:
			self.show_message(_("Change will be applied on restart."))
		return None

	def scale125(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.ui_scale == 1.25
		return None

		#self.prefs.ui_scale = 1.25
		#self.pref_box.large_preset()

		#if self.prefs.ui_scale != self.gui.scale:
		#	self.show_message(_("Change will be applied on restart."))
		#return None

	def toggle_use_tray(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.use_tray
		self.prefs.use_tray ^= True
		if not self.prefs.use_tray:
			self.prefs.min_to_tray = False
			self.hide_tray()
		else:
			self.show_tray()
		return None

	def toggle_text_tray(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.tray_show_title
		self.prefs.tray_show_title ^= True
		self.pctl.refresh_now_playing()
		return None

	def toggle_min_tray(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.min_to_tray
		self.prefs.min_to_tray ^= True
		return None

	def toggle_start_in_tray(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.start_in_tray
		self.prefs.start_in_tray ^= True
		return None

	def scale2(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.ui_scale == 2

		self.prefs.ui_scale = 2
		self.pref_box.small_preset()

		if self.prefs.ui_scale != self.gui.scale:
			self.show_message(_("Change will be applied on restart."))
		return None

	def toggle_borderless(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.draw_border

		self.gui.update_layout = True
		self.draw_border ^= True

		if self.draw_border:
			sdl3.SDL_SetWindowBordered(self.t_window, False)
		else:
			sdl3.SDL_SetWindowBordered(self.t_window, True)
		return None

	def toggle_rounded_corners(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.rounded_corners

		self.prefs.rounded_corners ^= True
		self.gui.request_frame()
		return None

	def toggle_break(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.break_enable ^ True
		self.prefs.break_enable ^= True
		self.gui.request_tracklist_redraw()
		return None

	def toggle_scroll(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return not self.prefs.scroll_enable

		self.prefs.scroll_enable ^= True
		self.gui.request_tracklist_redraw()
		self.gui.update_layout = True
		return None

	def toggle_smooth_scroll(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.smooth_scroll.enabled()

		if self.prefs.macos:
			return None

		self.prefs.smooth_scroll_enable ^= True
		self.gui.request_tracklist_redraw()
		self.gui.request_frame()
		return None

	def toggle_hide_bar(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.gui.set_bar ^ True
		self.gui.update_layout = True
		self.gui.set_bar ^= True
		self.show_message(_("Tip: You can also toggle this from a right-click context menu"))
		return None

	def toggle_append_total_time(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.append_total_time
		self.prefs.append_total_time ^= True
		self.gui.request_tracklist_redraw()
		self.gui.request_frame()
		return None

	def toggle_append_date(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.append_date
		self.prefs.append_date ^= True
		self.gui.request_tracklist_redraw()
		self.gui.request_frame()
		return None

	def toggle_true_shuffle(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.true_shuffle
		self.prefs.true_shuffle ^= True
		return None

	def toggle_auto_artist_dl(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.auto_dl_artist_data
		self.prefs.auto_dl_artist_data ^= True
		for artist, value in list(self.artist_list_box.thumb_cache.items()):
			if value is None:
				del self.artist_list_box.thumb_cache[artist]
		return None

	def toggle_scrobble_mark(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.scrobble_mark
		self.prefs.scrobble_mark ^= True
		return None

	def toggle_lfm_auto(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.auto_lfm
		self.prefs.auto_lfm ^= True
		if self.prefs.auto_lfm and not self.bag.last_fm_enable:
			self.show_message(_("Optional module python-pylast not installed"), mode="warning")
			self.prefs.auto_lfm = False
		# if prefs.auto_lfm:
		#     lastfm.hold = False
		# else:
		#     lastfm.hold = True
		return None

	def toggle_lb(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.lb.enable
		if not self.lb.enable and not self.prefs.lb_token:
			self.show_message(_("Can't enable this if there's no token."), mode="warning")
			return None
		self.lb.enable ^= True
		return None

	def toggle_maloja(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.maloja_enable
		if not self.prefs.maloja_url or not self.prefs.maloja_key:
			self.show_message(_("One or more fields are missing."), mode="warning")
			return None
		self.prefs.maloja_enable ^= True
		return None

	def toggle_ex_del(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.auto_del_zip
		self.prefs.auto_del_zip ^= True
		# if prefs.auto_del_zip is True:
		#     self.show_message("Caution! This function deletes things!", mode='info', "This could result in data loss if the process were to malfunction.")
		return None

	def toggle_dl_mon(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.monitor_downloads
		self.prefs.monitor_downloads ^= True
		return None

	def toggle_music_ex(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.extract_to_music
		self.prefs.extract_to_music ^= True
		return None

	def toggle_extract(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.auto_extract
		self.prefs.auto_extract ^= True
		if self.prefs.auto_extract is False:
			self.prefs.auto_del_zip = False
		return None

	def toggle_top_tabs(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.tabs_on_top
		self.prefs.tabs_on_top ^= True
		return None

	def toggle_guitar_chords(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.guitar_chords
		self.prefs.guitar_chords ^= True
		return None

	# def toggle_auto_lyrics(self, mode: int = 0) -> bool | None:
	# 	if mode == 1:
	# 		return self.prefs.auto_lyrics
	# 	self.prefs.auto_lyrics ^= True

	def switch_single(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.transcode_mode == "single"
		self.prefs.transcode_mode = "single"
		return None

	def switch_mp3(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.transcode_codec == "mp3"
		self.prefs.transcode_codec = "mp3"
		return None

	def switch_ogg(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.transcode_codec == "ogg"
		self.prefs.transcode_codec = "ogg"
		return None

	def switch_opus(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.transcode_codec == "opus"
		self.prefs.transcode_codec = "opus"
		return None

	def switch_opus_ogg(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.transcode_opus_as
		self.prefs.transcode_opus_as ^= True
		return None

	def toggle_transcode_output(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return not self.prefs.transcode_inplace
		self.prefs.transcode_inplace ^= True
		if self.prefs.transcode_inplace:
			self.gui.transcode_icon.colour = ColourRGBA(250, 20, 20, 255)
			self.show_message(
				_("DANGER! This will delete the original files. Keeping a backup is recommended in case of malfunction."),
				_("For safety, this setting will default to off. Embedded thumbnails are not kept so you may want to extract them first."),
				mode="warning")
		else:
			self.gui.transcode_icon.colour = ColourRGBA(239, 74, 157, 255)
		return None

	def toggle_transcode_inplace(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.transcode_inplace

		if self.gui.sync_progress:
			self.prefs.transcode_inplace = False
			return None

		self.prefs.transcode_inplace ^= True
		if self.prefs.transcode_inplace:
			self.gui.transcode_icon.colour = ColourRGBA(250, 20, 20, 255)
			self.show_message(
				_("DANGER! This will delete the original files. Keeping a backup is recommended in case of malfunction."),
				_("For safety, this setting will reset on restart. Embedded thumbnails are not kept so you may want to extract them first."),
				mode="warning")
		else:
			self.gui.transcode_icon.colour = ColourRGBA(239, 74, 157, 255)
		return None

	def switch_flac(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.transcode_codec == "flac"
		self.prefs.transcode_codec = "flac"
		return None

	def toggle_sbt(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.prefer_bottom_title
		self.prefs.prefer_bottom_title ^= True
		return None

	def toggle_bba(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.gui.bb_show_art
		self.gui.bb_show_art ^= True
		self.gui.update_layout = True
		return None

	def toggle_use_title(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.use_title
		self.prefs.use_title ^= True
		return None

	def switch_rg_off(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.replay_gain == 0
		self.prefs.replay_gain = 0
		self.request_replaygain_update()
		return None

	def switch_rg_track(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.replay_gain == 1
		self.prefs.replay_gain = 0 if self.prefs.replay_gain == 1 else 1
		self.request_replaygain_update()
		return None

	def switch_rg_album(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.replay_gain == 2
		self.prefs.replay_gain = 0 if self.prefs.replay_gain == 2 else 2
		self.request_replaygain_update()
		return None

	def switch_rg_auto(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.replay_gain == 3
		self.prefs.replay_gain = 0 if self.prefs.replay_gain == 3 else 3
		self.request_replaygain_update()
		return None

	def toggle_replaygain_compression(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.replay_allow_compression
		self.prefs.replay_allow_compression ^= True
		self.request_replaygain_update()
		return None

	def request_replaygain_update(self) -> None:
		self.pctl.playerCommand = "replaygain"
		self.pctl.playerCommandReady = True
		self.gui.request_frame()

	def toggle_jump_crossfade(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return bool(self.prefs.use_jump_crossfade)
		self.prefs.use_jump_crossfade ^= True
		return None

	def toggle_pause_fade(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return bool(self.prefs.use_pause_fade)
		self.prefs.use_pause_fade ^= True
		return None

	def toggle_transition_crossfade(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return bool(self.prefs.use_transition_crossfade)
		self.prefs.use_transition_crossfade ^= True
		return None

	def toggle_transition_gapless(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return not self.prefs.use_transition_crossfade
		self.prefs.use_transition_crossfade ^= True
		return None

	def toggle_eq(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.use_eq
		self.prefs.use_eq ^= True
		self.pctl.playerCommand = "seteq"
		self.pctl.playerCommandReady = True
		return None


	def drop_file(self, target: str) -> None:
		"""Deprecated, move to individual UI components"""
		i_x = self.inp.mouse_position[0]
		i_y = self.inp.mouse_position[1]
		self.gui.drop_playlist_target = 0
		#logging.info(event.drop)

		if i_y < self.gui.panelY and not self.gui.new_playlist_cooldown and self.gui.mode == GuiMode.MAIN:
			x = self.top_panel.tabs_left_x
			for tab in self.top_panel.shown_tabs:
				wid = self.top_panel.tab_text_spaces[tab] + self.top_panel.tab_extra_width

				if x < i_x < x + wid:
					self.gui.drop_playlist_target = tab
					self.tab_pulse.pulse()
					self.gui.request_frame()
					self.gui.pl_pulse = True
					logging.info("Direct drop")
					break

				x += wid
			else:
				logging.info("MISS")
				if self.gui.new_playlist_cooldown:
					self.gui.drop_playlist_target = self.pctl.active_playlist_viewing
				else:
					if not target.lower().endswith(".xspf"):
						self.gui.drop_playlist_target = self.new_playlist()
					self.gui.new_playlist_cooldown = True
		elif self.gui.lsp and self.gui.panelY < i_y < self.window_size[1] - self.gui.panelBY and self.gui.lsp_x < i_x < self.gui.lsp_x + self.gui.lspw and self.gui.mode == GuiMode.MAIN:
			y = self.gui.panelY
			y += 5 * self.gui.scale
			y += self.playlist_box.tab_h + self.playlist_box.gap

			for i, pl in enumerate(self.pctl.multi_playlist):
				if i_y < y:
					self.gui.drop_playlist_target = i
					self.tab_pulse.pulse()
					self.gui.request_frame()
					self.gui.pl_pulse = True
					logging.info("Direct drop")
					break
				y += self.playlist_box.tab_h + self.playlist_box.gap
			else:
				if self.gui.new_playlist_cooldown:
					self.gui.drop_playlist_target = self.pctl.active_playlist_viewing
				else:
					if not target.lower().endswith(".xspf"):
						self.gui.drop_playlist_target = self.new_playlist()
					self.gui.new_playlist_cooldown = True
		else:
			self.gui.drop_playlist_target = self.pctl.active_playlist_viewing

		load_order = LoadClass()
		load_order.target = target.replace("\\", "/")
		load_order.playlist = self.pctl.multi_playlist[self.gui.drop_playlist_target].uuid_int

		if self.flatpak_mode:
			if not os.path.exists(target):
				self.show_message(
					_("Could not access! Possible insufficient Flatpak permissions."),
					_(" For details, see {link}").format(link="https://github.com/Taiko2k/TauonMusicBox/wiki/Flatpak-Extra-Steps"),
					mode="bubble")
			elif target.startswith("/run/user/"):
				self.gui.message_box_confirm_reference = (copy.deepcopy(load_order),)
				self.gui.message_box_confirm_callback = lambda x: self.load_orders.append(x)
				self.gui.message_box_no_callback = lambda x: self.show_message(
						_("The target may be lost on reboot without necessary Flatpak permissions."),
					_(" For details, see {link}").format(link="https://github.com/Taiko2k/TauonMusicBox/wiki/Flatpak-Extra-Steps"),
					mode="bubble")
				self.show_message(_("Path may be transient! Continue? Press \"No\" for more information."),
					mode="confirm")
				self.gui.request_frame()
				self.inp.mouse_down = False
				self.inp.drag_mode = False
				return

		if os.path.isdir(load_order.target):
			self.quick_import_done.append(load_order.target)

			# if not pctl.multi_playlist[self.gui.drop_playlist_target].last_folder:
			self.pctl.multi_playlist[self.gui.drop_playlist_target].last_folder.append(load_order.target)
			reduce_paths(self.pctl.multi_playlist[self.gui.drop_playlist_target].last_folder)

		self.load_orders.append(copy.deepcopy(load_order))

		#logging.info('dropped: ' + str(dropped_file))
		self.gui.request_frame()
		self.inp.mouse_down = False
		self.inp.drag_mode = False

	def s_copy(self) -> None:
		# Copy tracks to internal clipboard
		# self.gui.lightning_copy = False
		# if self.inp.key_shift_down:
		self.gui.lightning_copy = True

		clip = copy_from_clipboard()
		if "file://" in clip:
			copy_to_clipboard("")

		self.pctl.cargo = []
		if self.pctl.default_playlist:
			for item in self.gui.shift_selection:
				self.pctl.cargo.append(self.pctl.default_playlist[item])

		if not self.pctl.cargo and -1 < self.pctl.selected_in_playlist < len(self.pctl.default_playlist):
			self.pctl.cargo.append(self.pctl.default_playlist[self.pctl.selected_in_playlist])

		self.copied_track = None

		if len(self.pctl.cargo) == 1:
			self.copied_track = self.pctl.cargo[0]

	def s_cut(self) -> None:
		self.s_copy()
		self.del_selected()

	def s_append(self, index: int) -> None:
		self.paste(playlist_no=index)

	def paste(self, playlist_no: int | None = None, track_id: int | None = None, target_position: int | None = None) -> None:
		clip = copy_from_clipboard()
		logging.info(clip)
		if "tidal.com/album/" in clip:
			logging.info(clip)
			num = clip.split("/")[-1].split("?")[0]
			if num and num.isnumeric():
				logging.info(num)
				self.tidal.append_album(num)
			clip = False

		elif "tidal.com/playlist/" in clip:
			logging.info(clip)
			num = clip.split("/")[-1].split("?")[0]
			self.tidal.playlist(num)
			clip = False

		elif "tidal.com/mix/" in clip:
			logging.info(clip)
			num = clip.split("/")[-1].split("?")[0]
			self.tidal.mix(num)
			clip = False

		elif "tidal.com/browse/track/" in clip:
			logging.info(clip)
			num = clip.split("/")[-1].split("?")[0]
			self.tidal.track(num)
			clip = False

		elif "tidal.com/browse/artist/" in clip:
			logging.info(clip)
			num = clip.split("/")[-1].split("?")[0]
			self.tidal.artist(num)
			clip = False

		found = False
		if clip:
			clip = clip.split("\n")
			for i, line in enumerate(clip):
				if line.startswith(("file://", "/")):
					target = str(urllib.parse.unquote(line)).replace("file://", "").replace("\r", "")
					load_order = LoadClass()
					load_order.target = target
					load_order.playlist = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].uuid_int

					if playlist_no is not None:
						load_order.playlist = self.pctl.pl_to_id(playlist_no)
					if target_position is not None:
						load_order.playlist_position = target_position

					self.load_orders.append(copy.deepcopy(load_order))
					found = True

		if not found:
			if playlist_no is None:
				if track_id is None:
					self.transfer(0, (2, 3))
				else:
					self.transfer(track_id, (2, 2))
			else:
				self.append_playlist(playlist_no)

		self.gui.request_tracklist_redraw()
	def do_exit_button(self) -> None:
		if self.inp.mouse_up or self.inp.ab_click:
			if self.gui.tray_active and self.prefs.min_to_tray:
				if self.inp.key_shift_down:
					self.exit("User clicked X button with shift key")
					return
				self.min_to_tray()
			elif self.gui.sync_progress and not self.gui.stop_sync:
				self.show_message(_("Stop the sync before exiting!"))
			else:
				self.exit("User clicked X button")

	def do_maximize_button(self) -> None:
		if self.gui.fullscreen:
			self.gui.fullscreen = False
			sdl3.SDL_SetWindowFullscreen(self.t_window, 0)
		elif self.gui.maximized:
			self.gui.maximized = False
			sdl3.SDL_RestoreWindow(self.t_window)
		else:
			self.gui.maximized = True
			sdl3.SDL_MaximizeWindow(self.t_window)

		self.inp.mouse_down = False
		self.inp.mouse_click = False
		self.inp.drag_mode = False

	def do_minimize_button(self) -> None:
		if self.macos:
			# hack
			sdl3.SDL_SetWindowBordered(self.t_window, True)
			sdl3.SDL_MinimizeWindow(self.t_window)
			sdl3.SDL_SetWindowBordered(self.t_window, False)
		else:
			sdl3.SDL_MinimizeWindow(self.t_window)

		self.inp.mouse_down = False
		self.inp.mouse_click = False
		self.inp.drag_mode = False

	def new_playlist(self, switch: bool = True) -> int | None:
		if self.gui.radio_view:
			self.pctl.radio_playlists.append(RadioPlaylist(uid=uid_gen(), name=_("New Radio List"), stations=[], scroll=0))
			return None

		title = self.gen_unique_pl_title(_("New Playlist"))

		self.top_panel.prime_side = 1
		self.top_panel.prime_tab = len(self.pctl.multi_playlist)

		self.pctl.multi_playlist.append(self.pl_gen(title=title))  # [title, 0, [], 0, 0, 0])
		if switch:
			self.pctl.switch_playlist(len(self.pctl.multi_playlist) - 1)
		return len(self.pctl.multi_playlist) - 1

	def toggle_enable_web(self, mode: int = 0) -> bool | None:
		prefs = self.prefs
		gui   = self.gui
		if mode == 1:
			return prefs.enable_web

		prefs.enable_web ^= True

		if prefs.enable_web and not gui.web_running:
			webThread = threading.Thread(
				target=webserve, args=[self.pctl, prefs, gui, self.album_art_gen, str(self.install_directory), self.strings, self])
			webThread.daemon = True
			webThread.start()
			self.show_message(_("Web server starting"), _("External connections will be accepted."), mode="done")

		elif prefs.enable_web is False:
			if self.radio_server is not None:
				self.radio_server.shutdown()
				gui.web_running = False

			time.sleep(0.25)
		return None

	def get_album_info(self, position: int, pl: int | None = None) -> tuple[bool, list[int], bool]:
		pctl     = self.pctl
		playlist = pctl.default_playlist
		prefs    = self.prefs
		if pl is not None:
			playlist = pctl.multi_playlist[pl].playlist_ids

		cache_key = (pctl.selected_in_playlist, pctl.playing_object(), pctl.playlist_playing_position)
		if self.album_info_cache_key != cache_key:  # Premature optimisation?
			self.album_info_cache.clear()
			self.album_info_cache_key = cache_key

		if position in self.album_info_cache:
			return self.album_info_cache[position]

		# album_dex is kept current while the preset gallery is on (album_mode)
		# or a custom-layout gallery widget is drawing (it rebuilds the dex per
		# playlist — see GalleryWidget._ensure_album_dex). In custom mode
		# album_mode is just whatever the previous preset left behind, so gate
		# on the dex's own playlist instead — otherwise every cache miss here
		# rebuilds the full album index (a whole-playlist scan per visible tile).
		viewing_pl = pctl.active_playlist_viewing if pl is None else pl
		if self.album_dex and viewing_pl == pctl.active_playlist_viewing and (
			prefs.album_mode
			or (self.gui.custom_mode and self.album_dex_pl_uuid == pctl.multi_playlist[viewing_pl].uuid_int)
		):
			dex = self.album_dex
		else:
			dex = self.reload_albums(custom_list=playlist)

		end = len(playlist)
		start = 0

		for i, p in enumerate(reversed(dex)):
			if p <= position:
				start = p
				break
			end = p

		album = list(range(start, end))

		playing = False
		select = False

		if pctl.selected_in_playlist in album:
			select = True

		if len(pctl.track_queue) > 0 and p < len(playlist):
			playing_track = pctl.track_queue[pctl.queue_step]
			if playing_track in playlist[start:end]:
				playing = True
				# If the album appears more than once in the playlist, only
				# highlight the instance the playing position is within
				viewing_pl = pctl.active_playlist_viewing if pl is None else pl
				pp = pctl.playlist_playing_position
				if (
					viewing_pl == pctl.active_playlist_playing
					and 0 <= pp < len(playlist)
					and playlist[pp] == playing_track
					and not start <= pp < end
				):
					playing = False

		self.album_info_cache[position] = playing, album, select
		return playing, album, select

	def set_tray_icons(self, force: bool = False) -> None:

		indicator_icon_play =    str(self.install_directory / "assets/svg/tray-indicator-play.svg")
		indicator_icon_pause =   str(self.install_directory / "assets/svg/tray-indicator-pause.svg")
		indicator_icon_default = str(self.install_directory / "assets/svg/tray-indicator-default.svg")

		if self.prefs.tray_theme == "gray":
			indicator_icon_play =    str(self.install_directory / "assets/svg/tray-indicator-play-g1.svg")
			indicator_icon_pause =   str(self.install_directory / "assets/svg/tray-indicator-pause-g1.svg")
			indicator_icon_default = str(self.install_directory / "assets/svg/tray-indicator-default-g1.svg")

		user_icon_dir = self.cache_directory / "icon-export"
		def install_tray_icon(src: str, name: str) -> None:
			alt = user_icon_dir / f"{name}.svg"
			if not alt.is_file() or force:
				if alt.exists():
					# Remove file first to avoid PermissionError on distributions like NixOS that use 444 for permissions
					# See https://github.com/Taiko2k/Tauon/issues/1615
					alt.unlink()
				shutil.copy(src, str(alt))

		if not user_icon_dir.is_dir():
			os.makedirs(user_icon_dir)

		install_tray_icon(indicator_icon_play, "tray-indicator-play")
		install_tray_icon(indicator_icon_pause, "tray-indicator-pause")
		install_tray_icon(indicator_icon_default, "tray-indicator-default")

	def get_tray_icon(self, name: str) -> str:
		return str(self.cache_directory / "icon-export" / f"{name}.svg")

	def test_ffmpeg(self) -> bool:
		if self.get_ffmpeg():
			return True
		if not self.macos:
			self.show_message(_("This feature requires FFmpeg. Should I download it for you? (~100 MB)"), mode="confirm")
			self.gui.message_box_confirm_callback = self.download_ffmpeg
			self.gui.message_box_no_callback = None
			self.gui.message_box_confirm_reference = (None,)
		else:
			self.show_message(_("FFmpeg could not be found"))
		return False

	def get_ffmpeg(self) -> Path | None:
		path = self.user_directory / "ffmpeg.exe"
		if self.windows and path.is_file():
			return path

		# macOS
		path = self.install_directory / "ffmpeg"
		if path.is_file():
			return path

		# Portable Linux
		path = self.user_directory / "ffmpeg"
		if path.is_file():
			return path

		path = shutil.which("ffmpeg")
		if path:
			return Path(path)
		return None

	def get_ffprobe(self) -> Path | None:
		path = self.user_directory / "ffprobe.exe"
		if self.windows and path.is_file():
			return path

		# macOS
		path = self.install_directory / "ffprobe"
		if path.is_file():
			return path

		# Portable Linux
		path = self.user_directory / "ffprobe"
		if path.is_file():
			return path

		path = shutil.which("ffprobe")
		if path:
			return Path(path)
		return None

	def bg_save(self) -> None:
		self.worker_save_state = True
		self.thread_manager.ready("worker")

	def exit(self, reason: str) -> None:
		logging.info(f"Shutting down. Reason: {reason}")
		if not sdl3.SDL_HideWindow(self.t_window):
			logging.warning(f"Failed to hide window during shutdown: {sdl3.SDL_GetError()}")
		elif not sdl3.SDL_SyncWindow(self.t_window):
			logging.warning(f"Timed out synchronizing hidden window during shutdown: {sdl3.SDL_GetError()}")
		sdl3.SDL_PumpEvents()
		self.pctl.running = False
		self.wake()

	def min_to_tray(self) -> None:
		sdl3.SDL_HideWindow(self.t_window)
		self.gui.mouse_unknown = True

	def request_raise(self) -> None:
		self.requested_raise = True
		self.wake()

	def raise_window(self) -> None:
		sdl3.SDL_ShowWindow(self.t_window)
		sdl3.SDL_RaiseWindow(self.t_window)
		sdl3.SDL_RestoreWindow(self.t_window)
		self.gui.lowered = False
		self.gui.request_frame()

	def focus_window(self) -> None:
		sdl3.SDL_RaiseWindow(self.t_window)

	def get_playing_playlist_id(self) -> int:
		return self.pctl.pl_to_id(self.pctl.active_playlist_playing)

	def wake(self) -> None:
		sdl3.SDL_PushEvent(ctypes.byref(self.dummy_event))



















				#ddt.rect_a((ar - round(25 * gui.scale), y), (round(25 * gui.scale), w), rpbc)
				#ddt.rect_a((ar - w, y), (w, h), rpbc)
				#ddt.rect_a((ar - round(50 * gui.scale), y + h), (round(50 * gui.scale), w), rpbc)

				# ddt.rect_a((x + round(25 * gui.scale), y), (round(25 * gui.scale), w), rpbc, True)
				# ddt.rect_a((x + round(4 * gui.scale), y + round(5 * gui.scale)), (math.floor(46 * gui.scale), w), rpbc, True)
				# ddt.rect_a((x + 50 * gui.scale - w, y), (w, 8 * gui.scale), rpbc, True)
				# ddt.rect_a((x + round(50 * gui.scale) - w, y + w), (w, round(4 * gui.scale)), rpbc, True)


























@dataclass
class Bag:
	"""Holder object for all configs"""

	mpt:                     CDLL | None
	gme:                     CDLL | None
	cf:                      Config
	colours:                 ColoursClass
	console:                 DConsole
	dirs:                    Directories
	prefs:                   Prefs
	formats:                 Formats
	renderer:                sdl3.LP_SDL_Renderer
	overlay_texture_texture: sdl3.LP_SDL_Texture
	fonts:                   Fonts
	tls_context:             ssl.SSLContext
	dev_mode:                bool
	macos:                   bool
	windows:                 bool
	phone:                   bool
	pump:                    bool
	snap_mode:               bool
	flatpak_mode:            bool
	smtc:                    bool
	draw_min_button:         bool
	draw_max_button:         bool
	last_fm_enable:          bool
	de_notify_support:       bool
	wayland:                 bool
	should_save_state:       bool
	desktop:                 str | None
	launch_prefix:           str
	platform_system:         str
	album_mode_art_size:     int
	master_count:            int
	playing_in_queue:        int
	playlist_playing:        int
	playlist_view_position:  int
	radio_playlist_viewing:  int
	selected_in_playlist:    int
	latest_db_version:       int
	volume:                  float
	log:                     LogHistoryHandler
	mac_close:               ColourRGBA
	mac_maximize:            ColourRGBA
	mac_minimize:            ColourRGBA
	track_queue:             list[int]
	logical_size:            list[int] # X Y
	window_size:             list[int] # X Y
	old_window_position:     tuple[int, int] # X Y res
	cue_list:                list[str]
	download_directories:    list[str]
	multi_playlist:          list[TauonPlaylist]
	radio_playlists:         list[RadioPlaylist]
	primary_stations:        list[RadioStation]
	p_force_queue:           list[TauonQueueItem]
	folder_image_offsets:    dict[str, int]
	gen_codes:               dict[int, str]
	master_library:          dict[int, TrackClass]
	loaded_asset_dc:         dict[str, WhiteModImageAsset | LoadImageAsset]
	default_playlist:        list[int] = field(default_factory=list[int])
	sm:                      CDLL | None = None
	nowplaying:              bool = False
	nowplaying_helper:       MacNowPlayingHelper | None = None
	song_notification:       None = None
	active_playlist_viewing: int = 0
	active_playlist_playing: int = 0
	loaded_stop_mode:        int = 0
	loaded_stop_ref:         tuple[str, str] | None = None

def is_module_loaded(module_name: str, object_name: str = "") -> bool:
	"""Check if a module is loaded, to determine which features we should enable

	See https://stackoverflow.com/a/30483269/8962143 for more details
	"""
	if object_name:
		return module_name in sys.modules and hasattr(sys.modules[module_name], object_name)
	return module_name in sys.modules

def get_cert_path(holder: Holder) -> str:
	if holder.pyinstaller_mode:
		return os.path.join(sys._MEIPASS, "certifi", "cacert.pem")
	# Running as script
	return certifi.where()

def setup_tls(holder: Holder) -> ssl.SSLContext:
	"""TLS setup (needed for frozen installs)

	This function has to be called BEFORE modules that init TLS context are imported or otherwise do so (like pylast - see https://github.com/Taiko2k/Tauon/issues/1442)
	"""
	# Set the TLS certificate path environment variable
	cert_path = get_cert_path(holder)
	logging.debug(f"Found TLS cert file at: {cert_path}")
	os.environ["SSL_CERT_FILE"] = cert_path
	os.environ["REQUESTS_CA_BUNDLE"] = cert_path

	# Create default TLS context
	return ssl.create_default_context(cafile=get_cert_path(holder))

def whicher(target: str, flatpak_mode: bool) -> bool | str | None:
	"""Detect and launch programs outside of flatpak sandbox"""
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


def no_padding() -> int:
	"""This will remove all padding"""
	return 0









# def pumper(bag: Bag) -> None:
# 	if bag.macos:
# 		return
# 	while bag.pump:
# 		time.sleep(0.005)
# 		sdl3.SDL_PumpEvents()

def save_prefs(bag: Bag) -> None:
	cf    = bag.cf
	prefs = bag.prefs
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

	cf.update_value("scrobble-jellyfin", prefs.scrobble_jellyfin)
	cf.update_value("scrobble-tidal", prefs.scrobble_tidal)
	cf.update_value("scrobble-subsonic", prefs.scrobble_subsonic)
	cf.update_value("scrobble-plex", prefs.scrobble_plex)

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
	cf.update_value("network-stream", prefs.network_stream)
	cf.update_value("stream-buffer-size", prefs.stream_buffer)
	cf.update_value("always-ffmpeg", prefs.always_ffmpeg)
	cf.update_value("volume-curve", prefs.volume_power)
	cf.update_value("jump-start-dl", prefs.jump_start)
	# cf.update_value("force-mono", prefs.mono)

	# cf.update_value("gst-output", prefs.gst_output)
	# cf.update_value("gst-use-custom-output", prefs.gst_use_custom_output)

	cf.update_value("separate-multi-genre", prefs.sep_genre_multi)

	cf.update_value("tag-editor-name", prefs.tag_editor_name)
	cf.update_value("tag-editor-target", prefs.tag_editor_target)

	cf.update_value("playback-follow-cursor", prefs.playback_follow_cursor)
	cf.update_value("back-restarts", prefs.back_restarts)
	cf.update_value("resume-on-advance", prefs.resume_on_jump)
	cf.update_value("end-queue-stop", prefs.stop_end_queue)
	cf.update_value("block-suspend", prefs.block_suspend)
	cf.update_value("allow-video-formats", prefs.allow_video_formats)

	cf.update_value("ui-scale", prefs.scale_want)
	cf.update_value("auto-scale", prefs.x_scale)
	cf.update_value("tracklist-y-text-offset", prefs.tracklist_y_text_offset)
	cf.update_value("theme-name", prefs.theme_name)
	cf.update_value("transparent-style", prefs.transparent_mode)
	cf.update_value("rounded-corners", prefs.rounded_corners)
	cf.update_value("rounded-corner-radius", prefs.corner_radius)
	cf.update_value("mac-style", prefs.macstyle)
	cf.update_value("allow-art-zoom", prefs.zoom_art)

	cf.update_value("scroll-gallery-by-row", prefs.gallery_row_scroll)
	cf.update_value("scroll-gallery-distance", prefs.gallery_scroll_wheel_px)
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
	cf.update_value("side-panel-style", prefs.side_panel_layout)
	cf.update_value("side-panel-left", prefs.side_panel_left)
	cf.update_value("side-lyrics-art", prefs.show_side_lyrics_art_panel)
	cf.update_value("side-lyrics-art-on-top", prefs.lyric_metadata_panel_top)
	cf.update_value("showcase-wide-art", prefs.showcase_wide_art)
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
	cf.update_value("tracklist-scrollbar-left", prefs.tracklist_scrollbar_left)
	cf.update_value("import-auto-sort", prefs.auto_sort)

	cf.update_value("encode-output-dir", prefs.custom_encoder_output)
	cf.update_value("sync-device-music-dir", prefs.sync_target)
	cf.update_value("add_download_directory", prefs.download_dir1)

	cf.update_value("autoscan_playlist_folder", prefs.autoscan_playlist_folder)
	cf.update_value("playlist_folder_path", prefs.playlist_folder_path)

	cf.update_value("save_lyrics_changes_to_files", prefs.save_lyrics_changes_to_files)
	cf.update_value("show_lyrics_save_menu", prefs.show_lyrics_save_menu)
	cf.update_value("use_lrc_instead", prefs.save_synced_to_lrc)
	cf.update_value("allow_overwrite_synced_with_static", prefs.allow_overwrite_synced_with_static)

	cf.update_value("synced_lyrics_editor_track_end_mode", prefs.synced_lyrics_editor_track_end_mode)

	cf.update_value("use-system-tray", prefs.use_tray)
	cf.update_value("use-gamepad", prefs.use_gamepad)
	cf.update_value("enable-remote-interface", prefs.enable_remote)
	cf.update_value("release-splash-version", prefs.release_splash_version)

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
	cf.update_value("enable-discord-rpc", prefs.discord_enable)
	cf.update_value("discord-card-layout",         prefs.discord_card_layout)
	cf.update_value("discord-member-list-display",  prefs.discord_member_list_display)
	cf.update_value("discord-clean-title",          prefs.discord_clean_title)
	cf.update_value("discord-lastfm-button",        prefs.discord_lastfm_button)
	cf.update_value("discord-show-tauon-button",    prefs.discord_show_tauon_button)
	cf.update_value("discord-keep-idle",            prefs.discord_keep_idle)
	cf.update_value("auto-search-lyrics", prefs.auto_lyrics)
	cf.update_value("shortcuts-ignore-keymap", prefs.use_scancodes)
	cf.update_value("alpha_key_activate_search", prefs.search_on_letter)
	cf.update_value("taskbar-status", prefs.taskbar_progress)

	cf.update_value("discogs-personal-access-token", prefs.discogs_pat)
	cf.update_value("listenbrainz-token", prefs.lb_token)
	cf.update_value("custom-listenbrainz-url", prefs.listenbrainz_url)

	cf.update_value("maloja-key", prefs.maloja_key)
	cf.update_value("maloja-url", prefs.maloja_url)
	cf.update_value("maloja-enable", prefs.maloja_enable)

	cf.update_value("tau-url", prefs.sat_url)

	cf.update_value("lastfm-pull-love", prefs.lastfm_pull_love)

	cf.update_value("broadcast-page-port", prefs.metadata_page_port)
	cf.update_value("chart-columns", prefs.chart_columns)
	cf.update_value("chart-rows", prefs.chart_rows)
	cf.update_value("chart-uses-text", prefs.chart_text)
	cf.update_value("chart-font", prefs.chart_font)
	cf.update_value("chart-sorts-top-played", prefs.topchart_sorts_played)

	if bag.dirs.config_directory.is_dir():
		cf.dump(str(bag.dirs.config_directory / "tauon.conf"))
	else:
		logging.error("Missing config directory")

def load_prefs(bag: Bag) -> None:
	cf    = bag.cf
	prefs = bag.prefs
	cf.reset()
	config_file = bag.dirs.config_directory / "tauon.conf"
	first_run = not config_file.is_file()
	cf.load(str(config_file))

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
		"Use Pipewire native only.")

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
	prefs.network_stream = cf.sync_add(
		"bool", "network-stream", prefs.network_stream,
		"Stream network tracks directly, buffering in memory, instead of downloading the full file first")
	prefs.stream_buffer = cf.sync_add(
		"int", "stream-buffer-size", prefs.stream_buffer,
		"Size of the in-memory file/stream buffer. In MB. Default: 50. (applies on track change)")
	prefs.tmp_cache = cf.sync_add(
		"bool", "cache-use-tmp", prefs.tmp_cache,
		"Use /tmp for cache. When enabled, above setting overridden to a small value. (applies on restart)")
	prefs.precache = cf.sync_add(
		"bool", "precache-local-files", prefs.precache,
		"Cache files from local sources too. (Useful for mounted network drives)")
	prefs.always_ffmpeg = cf.sync_add(
		"bool", "always-ffmpeg", prefs.always_ffmpeg,
		"Prefer decoding using FFmpeg. Fixes stuttering on Raspberry Pi OS.")
	prefs.volume_power = cf.sync_add(
		"int", "volume-curve", prefs.volume_power,
		"1=Linear volume control. Values above one give greater control bias over lower volume range. Default: 2")

	prefs.jump_start = cf.sync_add(
		"bool", "jump-start-dl", prefs.jump_start,
		"Start playing a network track before it has finished downloading")

	# prefs.mono = cf.sync_add("bool", "force-mono", prefs.mono, "This is a placeholder setting and currently has no effect.")

	# cf.br()
	# cf.add_text("[audio (gstreamer only)]")
	#
	# prefs.gst_output = cf.sync_add("string", "gst-output", prefs.gst_output, "GStreamer output pipeline specification. Only used with GStreamer backend.")
	# prefs.gst_use_custom_output = cf.sync_add("bool", "gst-use-custom-output", prefs.gst_use_custom_output, "Set this to true to apply any manual edits of the above string.")

	cf.br()
	cf.add_text("[locale]")
	prefs.ui_lang = cf.sync_add(
		"string", "display-language", prefs.ui_lang, "Override display language to use if "
		"available. E.g. \"en\", \"ja\", \"zh_CN\". "
		"Default: \"auto\"")
	# prefs.diacritic_search = cf.sync_add("bool", "decode-search", prefs.diacritic_search, "Allow searching of diacritics etc using ascii in search functions. (Disablng may speed up search)")
	cf.br()
	cf.add_text("[search]")
	prefs.sep_genre_multi = cf.sync_add(
		"bool", "separate-multi-genre", prefs.sep_genre_multi,
		"If true, the standard genre result will exclude results from multi-value tags. These will be included in a separate result.")

	cf.br()
	cf.add_text("[tag-editor]")
	if bag.windows:
		prefs.tag_editor_name = cf.sync_add("string", "tag-editor-name", "Picard", "Name to display in UI.")
		prefs.tag_editor_target = cf.sync_add(
			"string", "tag-editor-target",
			"C:\\Program Files\\MusicBrainz Picard\\picard.exe",
			"The path of the exe to run.")
	else:
		prefs.tag_editor_name = cf.sync_add("string", "tag-editor-name", "Picard", "Name to display in UI.")
		prefs.tag_editor_target = cf.sync_add(
			"string", "tag-editor-target", "picard",
			"The name of the binary to call.")
	prefs.save_synced_to_lrc = cf.sync_add(
		"bool", "use_lrc_instead", prefs.save_synced_to_lrc,
		"Save synced lyrics to separate .LRC files.")
	prefs.save_lyrics_changes_to_files = cf.sync_add(
		"bool", "save_lyrics_changes_to_files", prefs.save_lyrics_changes_to_files,
		"Save lyrics edits to tags when searching, clearing, pasting, or using the editor.")
	prefs.allow_overwrite_synced_with_static = cf.sync_add(
		"bool", "allow_overwrite_synced_with_static", prefs.allow_overwrite_synced_with_static,
		"When saving lyrics to metadata, allow static lyrics to overwrite existing synced lyrics.")
	prefs.show_lyrics_save_menu = cf.sync_add(
		"bool", "show_lyrics_save_menu", prefs.show_lyrics_save_menu,
		"Show the save lyrics dialog every time. (Even if this is False you can open it by right-clicking the save button.)")
	prefs.synced_lyrics_editor_track_end_mode = cf.sync_add(
		"string", "synced_lyrics_editor_track_end_mode", prefs.synced_lyrics_editor_track_end_mode,
		"What to do when you reach the end of the track in the lyrics editor. Can be either \"stop\", \"autosave\" or \"full save\"."
	)

	cf.br()
	cf.add_text("[playback]")
	prefs.playback_follow_cursor = cf.sync_add(
		"bool", "playback-follow-cursor", prefs.playback_follow_cursor,
		"When advancing, always play the track that is selected.")
	prefs.back_restarts = cf.sync_add(
		"bool", "back-restarts", prefs.back_restarts,
		"Pressing the back button restarts playing track on first press.")
	prefs.resume_on_jump = cf.sync_add(
		"bool", "resume-on-advance", prefs.resume_on_jump,
		"When paused, pressing back or next button starts playback.")
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
		for item in bag.formats.VID:
			if item not in bag.formats.DA:
				bag.formats.DA.add(item)

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
	prefs.transparent_mode = cf.sync_add("int", "transparent-style", prefs.transparent_mode, "0=opaque(default), 1=accents, 2=full")
	if first_run and prefs.macos:
		# Round by default on macOS where every other window has rounded corners
		prefs.rounded_corners = True
	prefs.rounded_corners = cf.sync_add(
		"bool", "rounded-corners", prefs.rounded_corners,
		"Round the window corners. Only applies when drawing own window decorations.")
	prefs.corner_radius = cf.sync_add(
		"int", "rounded-corner-radius", prefs.corner_radius, "Window corner radius in logical pixels")
	if prefs.corner_radius < 2 or prefs.corner_radius > 30:
		prefs.corner_radius = 10
		logging.warning("Invalid value for rounded-corner-radius")
	prefs.macstyle = cf.sync_add("bool", "mac-style", prefs.macstyle, "Use macOS style window buttons")
	prefs.zoom_art = cf.sync_add("bool", "allow-art-zoom", prefs.zoom_art)
	prefs.gallery_row_scroll = cf.sync_add("bool", "scroll-gallery-by-row", False)
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
		"In milliseconds. Negative values cause each line to display earlier and vice versa.")
	prefs.artist_list_prefer_album_artist = cf.sync_add(
		"bool", "artist-list-prefers-album-artist",
		prefs.artist_list_prefer_album_artist,
		"May require restart for change to take effect.")
	prefs.meta_persists_stop = cf.sync_add(
		"bool", "side-panel-info-persists", prefs.meta_persists_stop,
		"Show album art and metadata of last played track when stopped.")
	prefs.meta_shows_selected = cf.sync_add(
		"bool", "side-panel-info-selected", prefs.meta_shows_selected,
		"Show album art and metadata of selected track when stopped. (overrides above setting)")
	prefs.meta_shows_selected_always = cf.sync_add(
		"bool", "side-panel-info-selected-always",
		prefs.meta_shows_selected_always,
		"Show album art and metadata of selected track at all times. (overrides the above 2 settings)")
	prefs.stop_notifications_mini_mode = cf.sync_add(
		"bool", "mini-mode-avoid-notifications",
		prefs.stop_notifications_mini_mode,
		"Avoid sending track change notifications when in Mini Mode")
	prefs.hide_queue = cf.sync_add("bool", "hide-queue-when-empty", prefs.hide_queue)
	# prefs.show_playlist_list = cf.sync_add("bool", "show-playlist-list", prefs.show_playlist_list)

	prefs.art_in_top_panel = cf.sync_add(
		"bool", "enable-art-header-bar", prefs.art_in_top_panel,
		"Show art in top panel when window is narrow")
	prefs.always_art_header = cf.sync_add(
		"bool", "always-art-header-bar", prefs.always_art_header,
		"Show art in top panel at any size. (Requires enable-art-header-bar)")

	# prefs.center_bg = cf.sync_add("bool", "prefer-center-bg", prefs.center_bg, "Always center art for the background art function")
	prefs.side_panel_layout = cf.sync_add("int", "side-panel-style", prefs.side_panel_layout, "0:default, 1:centered")
	prefs.side_panel_left = cf.sync_add("bool", "side-panel-left", prefs.side_panel_left)
	prefs.show_side_lyrics_art_panel = cf.sync_add("bool", "side-lyrics-art", prefs.show_side_lyrics_art_panel)
	prefs.lyric_metadata_panel_top = cf.sync_add("bool", "side-lyrics-art-on-top", prefs.lyric_metadata_panel_top)
	prefs.showcase_wide_art = cf.sync_add("bool", "showcase-wide-art", prefs.showcase_wide_art)
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
		"Show playtime hint in stars")

	prefs.drag_to_unpin = cf.sync_add(
		"bool", "drag-tab-to-unpin", prefs.drag_to_unpin,
		"Dragging a tab off the top-panel un-pins it")

	cf.br()
	cf.add_text("[gallery]")
	prefs.thin_gallery_borders = cf.sync_add("bool", "gallery-thin-borders", prefs.thin_gallery_borders)
	prefs.increase_gallery_row_spacing = cf.sync_add("bool", "increase-row-spacing", prefs.increase_gallery_row_spacing)
	prefs.center_gallery_text = cf.sync_add("bool", "gallery-center-text", prefs.center_gallery_text)

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
	prefs.tracklist_scrollbar_left = cf.sync_add(
		"bool", "tracklist-scrollbar-left",
		prefs.tracklist_scrollbar_left,
		"Position the tracklist scroll bar on the left side instead of the right.")
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
		prefs.encoder_output = Path(prefs.custom_encoder_output)
	prefs.download_dir1 = cf.sync_add(
		"string", "add_download_directory", prefs.download_dir1,
		"Add another folder to monitor in addition to home downloads and music.")
	prefs.playlist_folder_path = cf.sync_add(
		"string", "playlist_folder_path", prefs.playlist_folder_path,
		"Default storage folder for playlists")
	prefs.autoscan_playlist_folder = cf.sync_add(
		"bool", "autoscan_playlist_folder", prefs.autoscan_playlist_folder,
		"Also auto-import new playlists from folder?")
	if prefs.download_dir1 and prefs.download_dir1 not in bag.download_directories:
		if os.path.isdir(prefs.download_dir1):
			bag.download_directories.append(prefs.download_dir1)
		else:
			logging.warning("Invalid download directory in config")

	cf.br()
	cf.add_text("[app]")
	prefs.enable_remote = cf.sync_add(
		"bool", "enable-remote-interface", prefs.enable_remote,
		"For use with Tauon Music Remote for Android")
	prefs.release_splash_version = cf.sync_add(
		"string", "release-splash-version", prefs.release_splash_version,
		"Records which one-time upgrade splash has already been shown.")
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
	prefs.discord_enable = cf.sync_add(
		"bool", "enable-discord-rpc", prefs.discord_enable,
		"Show track info in running Discord application")
	prefs.discord_card_layout = cf.sync_add(
		"string", "discord-card-layout", prefs.discord_card_layout,
		"Card layout: title_artist = Song title first, artist_title = Artist first")
	prefs.discord_member_list_display = cf.sync_add(
		"string", "discord-member-list-display", prefs.discord_member_list_display,
		"Controls what is shown in Discord member list: song or artist")
	prefs.discord_clean_title = cf.sync_add(
		"bool", "discord-clean-title", prefs.discord_clean_title,
		"Remove feat/remix/version suffixes in Discord title")
	prefs.discord_lastfm_button = cf.sync_add(
		"bool", "discord-lastfm-button", prefs.discord_lastfm_button,
		"Show Track Info button in Discord rich presence")
	prefs.discord_show_tauon_button = cf.sync_add(
		"bool", "discord-show-tauon-button", prefs.discord_show_tauon_button,
		"Show Tauon website button in Discord rich presence")
	prefs.discord_keep_idle = cf.sync_add(
		"bool", "discord-keep-idle", prefs.discord_keep_idle,
		"Keep Discord rich presence visible while playback is idle")
	if prefs.discord_card_layout not in ("title_artist", "artist_title"):
		prefs.discord_card_layout = "title_artist"
	if prefs.discord_member_list_display not in ("song", "artist"):
		prefs.discord_member_list_display = "artist"
	prefs.auto_lyrics = cf.sync_add(
		"bool", "auto-search-lyrics", prefs.auto_lyrics,
		"Automatically search internet for lyrics when display is wanted")

	prefs.use_scancodes = cf.sync_add(
		"bool", "shortcuts-ignore-keymap", prefs.use_scancodes,
		"When enabled, shortcuts will map to the physical keyboard layout")
	prefs.search_on_letter = cf.sync_add("bool", "alpha_key_activate_search", prefs.search_on_letter,
		"When enabled, pressing single letter keyboard key will activate the global search")

	prefs.taskbar_progress = cf.sync_add("bool", "taskbar-status", prefs.taskbar_progress,
		"When enabled, show playback progress on taskbar (supported DE only)")

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
	cf.add_text("[scrobbling]")
	cf.add_comment(
		"Allow Tauon to scrobble tracks played from a streaming service. Disable for "
		"services that already scrobble on their own to avoid double scrobbles.")
	prefs.scrobble_jellyfin = cf.sync_add("bool", "scrobble-jellyfin", prefs.scrobble_jellyfin)
	prefs.scrobble_tidal = cf.sync_add("bool", "scrobble-tidal", prefs.scrobble_tidal)
	prefs.scrobble_subsonic = cf.sync_add("bool", "scrobble-subsonic", prefs.scrobble_subsonic)
	prefs.scrobble_plex = cf.sync_add("bool", "scrobble-plex", prefs.scrobble_plex)


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
		"Optional bitrate subsonic should transcode to (Server may need to be configured for this). Set to 0 to disable transcoding.")

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


	#if bag.window_size[0] < (560 * prefs.scale_want) * 0.9 or bag.window_size[1] < (330 * prefs.scale_want) * 0.9:
	#	logging.info("Window overscale!")
	#	self.show_message(_("Detected unsuitable UI scaling."), _("Scaling setting reset to 1x"))
	#	prefs.scale_want = 1.0

def scale_assets(tauon: Tauon, bag: Bag, gui: GuiVar, scale_want: int, force: bool = False) -> None:
	asset_directory        = bag.dirs.asset_directory
	scaled_asset_directory = bag.dirs.scaled_asset_directory
	user_directory         = bag.dirs.user_directory
	svg_directory          = bag.dirs.svg_directory
	prefs = bag.prefs

	# Include the source icon count so adding an svg invalidates the cache
	# (the version alone misses icons added between releases / in dev).
	svg_count = len([f for f in os.listdir(svg_directory) if f.endswith(".svg")])
	key = f"{tauon.n_version},{scale_want},{svg_count}"
	keyfile = scaled_asset_directory / "key"
	render = True

	# Optimisation: don't rerender if we don't need to
	if not force and scaled_asset_directory.exists() and keyfile.exists():
		with open(keyfile) as f:
			c = f.read()
			if c == key:
				render = False

	if render:
		if scaled_asset_directory.exists():
			shutil.rmtree(scaled_asset_directory)
		scaled_asset_directory.mkdir()
		logging.info("Rendering icons...")
		render_icons(str(svg_directory), str(scaled_asset_directory), scale_want)
		with open(keyfile, "w", encoding="utf-8") as f:
			f.write(key)
		logging.info("Done rendering icons")
		tauon.reload_scale(skip_render=True)


	diff_ratio = scale_want / prefs.ui_scale
	prefs.ui_scale = scale_want
	prefs.scale_want = scale_want

	# Save user values
	column_backup = gui.pl_st
	rspw = gui.pref_rspw
	grspw = gui.pref_gallery_w
	row_h = prefs.playlist_row_height

	# gui.destroy_textures()
	gui.rescale()
	gui.update_layout = True

	# Scale saved values
	gui.pl_st = column_backup
	for item in gui.pl_st:
		item[1] *= diff_ratio
	gui.pref_rspw = rspw * diff_ratio
	gui.pref_gallery_w = grspw * diff_ratio
	prefs.playlist_row_height = round(row_h * diff_ratio)
	bag.album_mode_art_size = int(bag.album_mode_art_size * diff_ratio)


def clear_icon_cache(scaled_asset_directory: Path) -> None:
	if not scaled_asset_directory.exists() and not scaled_asset_directory.is_symlink():
		return
	logging.info("Clearing scaled icon cache for database upgrade")
	if scaled_asset_directory.is_dir() and not scaled_asset_directory.is_symlink():
		shutil.rmtree(scaled_asset_directory)
		return
	scaled_asset_directory.unlink()


def get_global_mouse() -> tuple[float, float]:
	i_y = pointer(c_float(0))
	i_x = pointer(c_float(0))
	sdl3.SDL_GetGlobalMouseState(i_x, i_y)
	return i_x.contents.value, i_y.contents.value

def get_window_position(t_window: sdl3.LP_SDL_Window) -> tuple[int, int]:
	i_y = pointer(c_int(0))
	i_x = pointer(c_int(0))
	sdl3.SDL_GetWindowPosition(t_window, i_x, i_y)
	return i_x.contents.value, i_y.contents.value

def ser_gimage(track_object: TrackClass) -> None:
	if track_object.artist and track_object.album:
		line = "https://www.google.com/search?tbm=isch&q=" + urllib.parse.quote(
			track_object.artist + " " + track_object.album)
		webbrowser.open(line, new=2, autoraise=True)

def year_s(plt: list[tuple[list[int], str, str]]) -> list[int]:
	sorted_temp = sorted(plt, key=lambda x: x[1])
	temp: list[int] = []

	for album in sorted_temp:
		temp += album[0]
	return temp



def csv_string(item: str) -> str:
	item = str(item)
	item.replace("\"", "\"\"")
	return f"\"{item}\""

def directory_size(path: str) -> int:
	total = 0
	for dirpath, dirname, filenames in os.walk(path):
		for file in filenames:
			path = os.path.join(dirpath, file)
			total += os.path.getsize(path)
	return total

def recode(text: str, enc: str) -> str:
	return text.encode("Latin-1", "ignore").decode(enc, "ignore")

def worker3(tauon: Tauon) -> None:
	while True:
		# time.sleep(0.04)

		# if tauon.thread_manager.exit_worker3:
		#     tauon.thread_manager.exit_worker3 = False
		#     return
		# time.sleep(1)

		tauon.gall_ren.worker_render()

def worker4(tauon: Tauon) -> None:
	gui = tauon.gui
	prefs = tauon.prefs
	pctl = tauon.pctl
	gui.style_worker_timer.set()
	while True:
		if prefs.art_bg or (gui.mode == GuiMode.MINI and prefs.mini_mode_mode == MiniModeMode.SLATE):
			tauon.style_overlay.worker()

		time.sleep(0.01)
		if pctl.playing_state != PlayingState.STOPPED and pctl.playing_time < 5:
			gui.style_worker_timer.set()
		if gui.style_worker_timer.get() > 5:
			return

def worker2(tauon: Tauon) -> None:
	search_over = tauon.search_over
	while True:
		tauon.worker2_lock.acquire()
		if search_over.search_text.text and not (len(search_over.search_text.text) == 1 and ord(search_over.search_text.text[0]) < 128):
			search_over.searched_text = search_over.search_text.text
			search_over.sip = True
			tauon.gui.request_frame()

			search_over.results = tauon._build_search_results(
				search_over.search_text.text,
				all_folders=search_over.all_folders,
				cancel_check=lambda: search_over.searched_text != search_over.search_text.text,
			)
			search_over.sip = False
			search_over.on = 0
			tauon.gui.request_frame()
			search_over.on = 0
			search_over.force_select = 0
			#logging.info(perf_timer.get())

def worker1(tauon: Tauon) -> None:
	bag   = tauon.bag
	gme   = tauon.gme
	gui   = tauon.gui
	pctl  = tauon.pctl
	prefs = tauon.prefs
	loaded_paths_cache = {}
	loaded_cue_cache = {}
	tauon.added = []

	def get_quoted_from_line(line: str) -> str:
		"""Extract quoted or unquoted string from a line

		e.g., 'FILE "01 - Track01.wav" WAVE' or 'TITLE Track01' or "PERFORMER 'Artist Name'"
		"""
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

	def add_from_cue(path: str) -> int | None:
		if not tauon.windows:  # Windows terminal doesn't like unicode
			logging.info(f"Reading CUE file: {path}")

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
			# files with multiple subtracks, but not multiple files that are individual tracks
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

			if files == 1 or files_with_subtracks > 1:
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
					line = line.removeprefix("REM ")

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
									if ".cue" not in item.lower() and item.split(".")[-1].lower() in bag.formats.DA:
										file_name = item
										file_path = os.path.join(os.path.dirname(path), file_name)
										logging.info(f"-- Source found at: {file_path}")
										break
							else:
								logging.error(f"-- Abort: Source file not found: {file_path}")
								return 1
						else:
							logging.error(f"-- Abort: Source file not found: {file_path}")
							return 1

				if line.startswith("TRACK "):
					line = line[6:]
					line = line.removesuffix("AUDIO")

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
					nt.parent_size = os.path.getsize(nt.fullpath)

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
				tauon.tag_scan(end_track)

				# Remove target track if already imported
				for i in reversed(range(len(tauon.added))):
					if pctl.get_track(tauon.added[i]).fullpath == end_track.fullpath:
						del tauon.added[i]

				# Update with proper length
				for track in reversed(cd):
					if last_end == None:
						last_end = end_track.length

					track.length = last_end - track.start_time
					track.samplerate = end_track.samplerate
					track.bitrate = end_track.bitrate
					track.bit_depth = end_track.bit_depth
					track.parent_length = end_track.length
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
					elif len(cds) <= 1:
						track.disc_number = ""
					else:
						track.disc_number = str(cdn + 1)

					if cue_disc_total:
						track.disc_total = cue_disc_total
					elif len(cds) <= 1:
						track.disc_total = ""
					else:
						track.disc_total = str(len(cds))


			# Add all tracks for import to playlist
			for cd in cds:
				for track in cd:
					pctl.master_library[track.index] = track
					if track.fullpath not in bag.cue_list:
						bag.cue_list.append(track.fullpath)
					loaded_paths_cache[track.fullpath] = track.index
					tauon.added.append(track.index)

		except Exception:
			logging.exception("Internal error processing CUE file")

	def pl_folder_autoscan() -> None:
		"""Rescan designated playlist folder for new playlists and import them"""
		if prefs.autoscan_playlist_folder:
			new_playlists = []
			for root, dirs, files in os.walk( prefs.playlist_folder_path ):
				for name in files:
					if Path( name.lower() ).suffix in [".m3u",".m3u8",".xspf"]:
						structure = ( os.path.join(root, name), name )
						new_playlists.append( structure )
			for filepath in new_playlists:
				can_import = True
				for already_existing_playlist in pctl.multi_playlist:
					if already_existing_playlist.playlist_file == filepath[0]:
						can_import = False
						logging.info(f"skipping {filepath[1]}: already loaded as {already_existing_playlist.title}")
				if can_import:
					add_file(filepath[0])
					logging.info(f"will import {filepath[0]}")

	def add_file(path: str, force_scan: bool = False, show_errors: bool = False) -> int | None:
		"""Import file from path - playlists, audio, zips etc"""
		try:
			Path(path).stat().st_size
		except FileNotFoundError:
			logging.error(f"File to import missing: {path}")
			if show_errors:
				tauon.show_message(
					_("Files missing or inaccessible"),
					_("If you're using Flatpak, you should probably follow this:"),
					"https://github.com/Taiko2k/Tauon/wiki/Flatpak-Extra-Steps#gui-way-using-flatseal",
					mode="link")
			return 0
		except PermissionError:
			logging.error(f"Bad permissions to import: {path}")
			if show_errors:
				tauon.show_message(
					_("Bad permissions"),
					_("We don't have permissions to access {file}").format(file=path),
					mode="error"
				)
			return 0
		except Exception:
			logging.exception(f"Unknown error importing: {path}")
			if show_errors:
				tauon.show_message(
					_("Can't import that"),
					_("We can't import the file {path} and we're not sure why.").format(path=path),
					mode="error"
				)

		for pl, playlist in enumerate( pctl.multi_playlist ):
			if path == playlist.playlist_file:
				if show_errors:
					temp = prefs.always_auto_update_playlists
					prefs.always_auto_update_playlists = True
					pctl.switch_playlist(pl)
					prefs.always_auto_update_playlists = temp
					# make sure that the file gets reloaded regardless of settings
				else:
					logging.error(f"File already associated with playlist \"{playlist.title}\"")
				return 0

		if os.path.splitext(path)[1][1:] in {"CUE", "cue"}:
			add_from_cue(path)
			return 0

		if path.lower().endswith(".xspf"):
			logging.info(f"Found XSPF file at: {path}")
			tauon.load_xspf(path)
			return 0

		if path.lower().endswith(".milk"):
			if t_visuals.milky_ready:
				tauon.milky.projectm.load_next = Path(path)

		if path.lower().endswith(".m3u") or path.lower().endswith(".m3u8"):
			tauon.load_m3u(path)
			return 0

		if path.endswith(".pls"):
			tauon.load_pls(path)
			return 0

		if os.path.splitext(path)[1][1:].lower() not in bag.formats.DA:
			if os.path.splitext(path)[1][1:].lower() in bag.formats.Archive:
				if not prefs.auto_extract:
					tauon.show_message(
						_("You attempted to drop an archive."),
						_('However the "extract archive" function is not enabled.'), mode="info")
				else:
					type = os.path.splitext(path)[1][1:].lower()
					split = os.path.splitext(path)
					target_dir = split[0]
					if prefs.extract_to_music and tauon.music_directory is not None:
						target_dir = os.path.join(str(tauon.music_directory), os.path.basename(target_dir))
					#logging.info(os.path.getsize(path))
					if os.path.getsize(path) > 4e+9:
						logging.warning("Archive file is large!")
						tauon.show_message(_("Skipping oversize zip file (>4GB)"))
						return 1
					if not os.path.isdir(target_dir) and not os.path.isfile(target_dir):
						if type == "zip":
							try:
								b = gui.to_got
								gui.to_got = "ex"
								gui.request_frame()
								zip_ref = zipfile.ZipFile(path, "r")

								zip_ref.extractall(target_dir)
								zip_ref.close()
							except RuntimeError as e:
								logging.exception("Zip error")
								gui.to_got = b
								if "encrypted" in e:
									tauon.show_message(
										_("Failed to extract zip archive."),
										_("The archive is encrypted. You'll need to extract it manually with the password."),
										mode="warning")
								else:
									tauon.show_message(
										_("Failed to extract zip archive."),
										_("Maybe archive is corrupted? Does disk have enough space and have write permission?"),
										mode="warning")
								return 1
							except Exception:
								logging.exception("Zip error 2")
								gui.to_got = b
								tauon.show_message(
									_("Failed to extract zip archive."),
									_("Maybe archive is corrupted? Does disk have enough space and have write permission?"),
									mode="warning")
								return 1

						elif type == "rar":
							b = gui.to_got
							try:
								gui.to_got = "ex"
								gui.request_frame()
								line = tauon.launch_prefix + "unrar x -y -p- " + shlex.quote(path) + " " + shlex.quote(
									target_dir) + os.sep
								result = subprocess.run(shlex.split(line), check=True)
								logging.info(result)
							except Exception:
								logging.exception("Failed to extract rar archive.")
								gui.to_got = b
								tauon.show_message(_("Failed to extract rar archive."), mode="warning")

								return 1

						elif type == "7z":
							b = gui.to_got
							try:
								gui.to_got = "ex"
								gui.request_frame()
								line = tauon.launch_prefix + "7z x -y " + shlex.quote(path) + " -o" + shlex.quote(
									target_dir) + os.sep
								result = subprocess.run(shlex.split(line), check=True)
								logging.info(result)
							except Exception:
								logging.exception("Failed to extract 7z archive.")
								gui.to_got = b
								tauon.show_message(_("Failed to extract 7z archive."), mode="warning")

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
							logging.info(f"Moving archive file to trash: {path}")
							try:
								send2trash(path)
							except Exception:
								logging.exception("Could not move archive to trash")
								tauon.show_message(_("Could not move archive to trash"), path, mode="info")

						gui.to_got = b
						gets(target_dir)
						tauon.quick_import_done.append(target_dir)
					# gets(target_dir)

			return 1

		gui.to_got += 1
		gui.request_frame()

		path = path.replace("\\", "/")

		if path in loaded_paths_cache:
			de = loaded_paths_cache[path]

			if pctl.master_library[de].fullpath in bag.cue_list:
				logging.info("File has an associated .cue file... Skipping")
				return None

			if pctl.master_library[de].file_ext.lower() in bag.formats.GME:
				# Skip cache for subtrack formats
				pass
			else:
				tauon.added.append(de)
				return None

		time.sleep(0.002)

		# audio = auto.File(path)

		nt = TrackClass()

		nt.index = pctl.master_count
		set_path(nt, path)

		def commit_track(nt: TrackClass) -> None:
			pctl.master_library[pctl.master_count] = nt
			tauon.added.append(pctl.master_count)

			if prefs.auto_sort or force_scan:
				tauon.tag_scan(nt)
			else:
				tauon.after_scan.append(nt)
				tauon.thread_manager.ready("worker")

			pctl.master_count += 1

		# nt = tauon.tag_scan(nt)
		if nt.cue_sheet:
			tauon.tag_scan(nt)
			tauon.cue_scan(nt.cue_sheet, nt)
			del nt
		elif nt.file_ext.lower() in bag.formats.GME and gme:
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
		return None

	def pre_get(direc: str) -> None:
		"""Count the approx number of files to be imported"""
		gui.to_get = 0
		for root, dirs, files in os.walk(direc):
			gui.to_get += len(files)
			if gui.im_cancel:
				return
			gui.request_frame()

	def gets(direc: str, force_scan: bool = False) -> None:
		if os.path.basename(direc) == "__MACOSX":
			return

		try:
			items_in_dir = os.listdir(direc)
			if tauon.use_natsort:
				items_in_dir = natsort.os_sorted(items_in_dir)
			else:
				items_in_dir.sort()
		except PermissionError:
			logging.exception("Permission error accessing one or more files")
			tauon.show_message(_("Permission error accessing one or more files"), mode="warning")
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

				if os.path.splitext(items_in_dir[q])[1][1:].lower() in bag.formats.DA:
					if len(items_in_dir[q]) > 2 and items_in_dir[q][0:2] == "._":
						continue

					add_file(os.path.join(direc, items_in_dir[q]).replace("\\", "/"), force_scan)
				elif os.path.splitext(items_in_dir[q])[1][1:] in {"CUE", "cue"}:
					add_from_cue(os.path.join(direc, items_in_dir[q]).replace("\\", "/"))

			if gui.im_cancel:
				return

	def cache_paths() -> tuple[dict, dict]:
		dic = {}
		dic2 = {}
		for key, value in pctl.master_library.items():
			if value.is_network:
				continue
			dic[value.fullpath.replace("\\", "/")] = key
			if value.is_cue:
				dic2[(value.fullpath.replace("\\", "/"), value.track_number)] = value
		return dic, dic2

	def upload_to_lrclib( upload: dict[ str, str | float ] ) -> bool:
		p, t = get_lrclib_challenge(tauon.t_agent)
		if p and t:
			logging.info("LRCLIB upload: step 1 (of 3) complete")
		else:
			tauon.lrclib_uploads = []
			tauon.show_message(
				_("Connection error"),
				_("We can't upload your lyrics because we can't connect to the server."),
				_("Are you offline?"),
				mode="error"
			)
			return False
		if tauon.windows:
			binary = str( tauon.install_directory / "lrclib-solver.exe" )
		else:
			binary = str( tauon.install_directory / "lrclib-solver" )

		try:
			nonce = subprocess.run(
				[binary, p, t],
				capture_output=True,
				text=True,
				check=True
			)
		except FileNotFoundError:
			tauon.lrclib_uploads = [] # fatal error should cancel all further uploads
			tauon.show_message(
				_("Something went wrong"),
				_("The following file is missing:"),
				binary,
				mode="error"
			)
			return False
		except PermissionError:
			tauon.lrclib_uploads = []
			tauon.show_message(
				_("Something went wrong"),
				_("We don't have the proper permissions to run the file:"),
				binary,
				mode="error"
			)
			return False
		except Exception:
			tauon.lrclib_uploads = []
			tauon.show_message(
				_("Something went wrong"),
				_("We can't upload your lyrics, and we don't know why."),
				mode="error"
			)
			logging.exception("Couldn't upload lyrics")
			return False
		logging.info("LRCLIB upload: step 2 (of 3) complete")
		publish_token = p + ":" + nonce.stdout.strip()
		h = {
			"User-Agent": tauon.t_agent,
			"X-Publish-Token": publish_token
		}
		r = requests.post("https://lrclib.net/api/publish", headers=h, json=upload, timeout=10)
		if r.status_code == 201:
			logging.info("LRCLIB upload: step 3 (of 3) complete")
		else:
			tauon.lrclib_uploads = []
			tauon.show_message(
				_("Something went wrong"),
				_("Lyrics upload failed with error code: ") + str(r.status_code),
				mode="error"
			)
		return r.status_code == 201


	#logging.info(pctl.master_library)

	active_timer = Timer()
	while True:
		if not tauon.after_scan:
			time.sleep(0.1)

		if tauon.after_scan \
		or tauon.playlist_autoscan \
		or tauon.load_orders \
		or tauon.artist_list_box.load \
		or tauon.artist_list_box.to_fetch \
		or tauon.gui.regen_single_id \
		or tauon.gui.regen_single > -1 \
		or tauon.pctl.after_import_flag \
		or tauon.worker_save_state \
		or tauon.move_jobs \
		or tauon.cm_clean_db \
		or tauon.transcode_list \
		or tauon.to_scan \
		or tauon.lrclib_uploads \
		or tauon.loaderCommandReady:
			active_timer.set()
		elif active_timer.get() > 5:
			return

		if tauon.after_scan:
			i = 0
			while tauon.after_scan:
				i += 1

				if i > 123:
					break

				tauon.tag_scan(tauon.after_scan[0])

				gui.request_frame()
				gui.request_tracklist_redraw()
				# time.sleep(0.001)
				if pctl.running:
					del tauon.after_scan[0]
				else:
					break

			gui.album_artist_dict.clear()

		if tauon.playlist_autoscan:
			pl_folder_autoscan()
			tauon.playlist_autoscan = False

		tauon.artist_list_box.worker()

		# Update smart playlists
		if gui.regen_single_id is not None:
			tauon.regenerate_playlist(pl=-1, silent=True, id=gui.regen_single_id)
			gui.regen_single_id = None

		# Update smart playlists
		if gui.regen_single > -1:
			target = gui.regen_single
			gui.regen_single = -1
			tauon.regenerate_playlist(target, silent=True)

		if pctl.after_import_flag and not tauon.after_scan and not tauon.search_over.active and not pctl.loading_in_progress:
			pctl.after_import_flag = False

			for i, plist in enumerate(pctl.multi_playlist):
				if pctl.pl_to_id(i) in pctl.gen_codes:
					code = pctl.gen_codes[pctl.pl_to_id(i)]
					try:
						if tauon.check_auto_update_okay(code, pl=i):
							if not tauon.pl_is_locked(i):
								logging.info(f"Reloading smart playlist: {plist.title}")
								tauon.regenerate_playlist(i, silent=True)
								time.sleep(0.02)
					except Exception:
						logging.exception("Failed to handle playlist")

			tauon.tree_view_box.clear_all()

		if tauon.worker_save_state and \
				not gui.pl_pulse and \
				not pctl.loading_in_progress and \
				not tauon.to_scan and not tauon.after_scan and \
				not tauon.plex.scanning and \
				not tauon.jellyfin.scanning and \
				not tauon.cm_clean_db and \
				not tauon.lastfm.scanning_friends and \
				not tauon.move_in_progress and \
				(gui.lowered or not window_is_focused(tauon.t_window) or not gui.mouse_in_window):
			tauon.save_state()
			bag.cue_list.clear()
			tauon.worker_save_state = False

		for i, upload in enumerate(tauon.lrclib_uploads):
			if upload_to_lrclib( upload ):
				del tauon.lrclib_uploads[i]
				gui.request_frame()
			else:
				tauon.lrclib_uploads.reverse() # if one is broken you can still try the others

		# Folder moving
		if len(tauon.move_jobs) > 0:
			gui.request_frame()
			tauon.move_in_progress = True
			job = tauon.move_jobs[0]
			del tauon.move_jobs[0]

			if job[0].strip("\\/") == job[1].strip("\\/"):
				tauon.show_message(_("Folder copy error."), _("The target and source are the same."), mode="info")
				gui.request_frame()
				tauon.move_in_progress = False
				continue

			try:
				shutil.copytree(job[0], job[1])
			except Exception:
				logging.exception("Failed to copy directory")
				tauon.move_in_progress = False
				gui.request_frame()
				tauon.show_message(_("The folder copy has failed!"), _("Some files may have been written."), mode="warning")
				continue

			if job[2] is True:
				try:
					shutil.rmtree(job[0])

				except Exception:
					logging.exception("Failed to delete directory")
					tauon.show_message(_("Something has gone horribly wrong!"), _("Could not delete {name}").format(name=job[0]), mode="error")
					gui.request_frame()
					tauon.move_in_progress = False
					return

				tauon.show_message(_("Folder move complete."), _("Folder name: {name}").format(name=job[3]), mode="done")
			else:
				tauon.show_message(_("Folder copy complete."), _("Folder name: {name}").format(name=job[3]), mode="done")

			tauon.move_in_progress = False
			tauon.load_orders.append(job[4])
			gui.request_frame()

		# Clean database
		if tauon.cm_clean_db is True:
			items_removed = 0

			# old_db = copy.deepcopy(pctl.master_library)
			gui.to_got = 0
			gui.to_get = len(pctl.master_library)
			tauon.search_over.results.clear()

			keys = set(pctl.master_library.keys())
			for index in keys:
				time.sleep(0.0001)
				track = pctl.master_library[index]
				gui.to_got += 1

				if gui.to_got % 100 == 0:
					gui.request_frame()

				if (prefs.remove_network_tracks is False and not track.is_network and not os.path.isfile(
						track.fullpath)) or \
						(prefs.remove_network_tracks is True and track.is_network):

					pctl.purge_track(index)
					items_removed += 1

			tauon.cm_clean_db = False
			tauon.show_message(
				_("Cleaning complete."),
				_("{N} items were removed from the database.").format(N=str(items_removed)), mode="done")
			if prefs.album_mode:
				tauon.reload_albums(True)
			if gui.combo_mode:
				tauon.reload_albums()

			gui.request_frame()
			gui.request_tracklist_redraw()
			pctl.notify_database_changed()

			tauon.search_dia_string_cache.clear()
			tauon.search_string_cache.clear()
			tauon.search_field_cache.clear()
			tauon.search_dia_field_cache.clear()
			tauon.search_over.results.clear()

			pctl.notify_database_changed()

		# FOLDER ENC
		if tauon.transcode_list:
			try:
				tauon.transcode_state = ""
				gui.request_frame()

				folder_items = tauon.transcode_list[0]

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

				logging.info(f"Transcoding folder: {folder_name}")

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
					cores = os.cpu_count()

					total = len(folder_items)
					gui.transcoding_batch_total = total
					gui.transcoding_batch_done = 0
					dones = []

					q = 0
					while True:
						if tauon.core_use < cores and q < len(folder_items):
							agg = [[folder_items[q], Path(folder_name)]]
							if agg not in dones:
								tauon.core_use += 1
								dones.append(agg)
								loaderThread = threading.Thread(target=tauon.transcode_single, args=agg)
								loaderThread.daemon = True
								loaderThread.start()

							q += 1
							gui.request_frame()
						time.sleep(0.05)
						if gui.tc_cancel:
							while tauon.core_use > 0:
								time.sleep(1)
							break
						if q == len(folder_items) and tauon.core_use == 0:
							gui.request_frame()
							break
				else:
					logging.error("Codec error")

				output_dir = prefs.encoder_output / folder_name
				if prefs.transcode_inplace:
					try:
						output_dir.unlink()
					except Exception:
						logging.exception("Encode folder not removed")
					tauon.reload_metadata(folder_items[0])
				else:
					tauon.album_art_gen.save_thumb(pctl.get_track(folder_items[0]), (1080, 1080), str(output_dir / "cover"))

				#logging.info(tauon.transcode_list[0])

				del tauon.transcode_list[0]
				tauon.transcode_state = ""
				gui.request_frame()
			except Exception:
				logging.exception("Transcode failed")
				tauon.transcode_state = "Transcode Error"
				time.sleep(0.2)
				tauon.show_message(_("Transcode failed."), _("An error was encountered."), mode="error")
				gui.request_frame()
				time.sleep(0.1)
				del tauon.transcode_list[0]

			if len(tauon.transcode_list) == 0:
				if gui.tc_cancel:
					gui.tc_cancel = False
					tauon.show_message(
						_("The transcode was canceled before completion."),
						_("Incomplete files will remain."),
						mode="warning")
				else:
					line = _("Press F9 to show output.")
					if prefs.transcode_codec == "flac":
						line = _("Note that any associated output picture is a thumbnail and not an exact copy.")
					if not gui.sync_progress:
						if not gui.message_box:
							tauon.show_message(_("Encoding complete."), line, mode="done")
						if tauon.de_notify_support:
							tauon.g_tc_notify.show()

		if tauon.to_scan:
			network_warn: bool = False
			while tauon.to_scan:
				track = tauon.to_scan[0]
				def clear_search_cache(track: int) -> None:
					# clear cached search data (user can search by lyrics immediately)
					tauon.search_string_cache.pop(track, None)
					tauon.search_dia_string_cache.pop(track, None)
					tauon.search_field_cache.pop(track, None)
					tauon.search_dia_field_cache.pop(track, None)
				star = tauon.star_store.full_get(track)
				tauon.star_store.remove(track)
				clear_search_cache(track)
				rescanned_track = tauon.tag_scan(pctl.master_library[track])
				if rescanned_track is None:
					del tauon.to_scan[0]
					gui.request_frame()
					network_warn = True
					continue
				pctl.master_library[track] = rescanned_track
				tauon.star_store.merge(track, star)
				tauon.lastfm.sync_pull_love(pctl.master_library[track])
				del tauon.to_scan[0]
				gui.request_frame()
			gui.album_artist_dict.clear()
			pctl.notify_database_changed()
			gui.request_tracklist_redraw()
			if network_warn:
				tauon.show_message(_("Some tracks could not be rescanned"), _("Rescanning network tracks is unsupported, please reimport your playlist instead."))

		if tauon.loaderCommandReady is True:
			for order in tauon.load_orders:
				if order.stage == 1:
					if tauon.loaderCommand == LoaderCommand.FOLDER:
						gui.to_get = 0
						gui.to_got = 0
						loaded_paths_cache, loaded_cue_cache = cache_paths()
						# pre_get(order.target)
						if order.force_scan:
							gets(order.target, force_scan=True)
						else:
							gets(order.target)
					elif tauon.loaderCommand == LoaderCommand.FILE:
						loaded_paths_cache, loaded_cue_cache = cache_paths()
						add_file(order.target, show_errors=True)
						# i think this meaans if it's manually dragged in

					if gui.im_cancel:
						gui.im_cancel = False
						gui.to_get = 0
						gui.to_got = 0
						tauon.load_orders.clear()
						tauon.added = []
						tauon.loaderCommand = LoaderCommand.DONE
						tauon.loaderCommandReady = False
						break

					tauon.loaderCommand = LoaderCommand.DONE
					#logging.info("LOAD ORDER")
					order.tracks = tauon.added

					# Double check for cue dupes
					for i in reversed(range(len(order.tracks))):
						if pctl.master_library[order.tracks[i]].fullpath in bag.cue_list:
							if pctl.master_library[order.tracks[i]].is_cue is False:
								del order.tracks[i]

					tauon.added = []
					order.stage = 2
					tauon.loaderCommandReady = False
					#logging.info("DONE LOADING")
					break

def visit_radio_site(station: RadioStation) -> None:
	if station.website_url:
		webbrowser.open(station.website_url, new=2, autoraise=True)

def visit_radio_station(item: tuple[int, RadioStation]) -> None:
	visit_radio_site(item[1])

def menu_is_open() -> bool:
	for menu in Menu.instances:
		if menu.active:
			return True
	return False

#def load_savefile(latest_db_version: float, user_directory: Path, bag: Bag, prefs: Prefs, gui: GuiVar) -> tuple[list[TrackClass], dict, dict]:
#	return after_scan, search_string_cache, search_dia_string_cache

#def setup_menus(tauon: Tauon) -> tuple[MenuIcon, MenuIcon, MenuIcon]:
#	bag   = tauon.bag
#	gui   = tauon.gui
#	inp   = tauon.inp
#	pctl  = tauon.pctl
#	prefs = tauon.prefs


#def main_loop(tauon: Tauon) -> None:
#	bag            = tauon.bag
#	ddt            = tauon.ddt
#	gui            = tauon.gui
#	inp            = tauon.inp
#	dirs           = tauon.dirs
#	pctl           = tauon.pctl
#	prefs          = tauon.prefs
#	colours        = tauon.colours
#	radiobox       = tauon.radiobox
#	renderer       = tauon.renderer
#	t_window       = tauon.t_window
#	pref_box       = tauon.pref_box
#	keymaps        = tauon.gui.keymaps
#	user_directory = tauon.dirs.user_directory
#	window_size    = tauon.window_size
#	logical_size   = tauon.logical_size
#	playlist_menu         = tauon.playlist_menu
#	radio_entry_menu      = tauon.radio_entry_menu
#	showcase_menu         = tauon.showcase_menu
#	center_info_menu      = tauon.center_info_menu
#	gallery_menu          = tauon.gallery_menu
#	artist_info_menu      = tauon.artist_info_menu
#	repeat_menu           = tauon.repeat_menu
#	shuffle_menu          = tauon.shuffle_menu
#	artist_list_menu      = tauon.artist_list_menu
#	lightning_menu        = tauon.lightning_menu
#	lsp_menu              = tauon.lsp_menu
#	folder_tree_menu      = tauon.folder_tree_menu
#	folder_tree_stem_menu = tauon.folder_tree_stem_menu
#	radio_context_menu    = tauon.radio_context_menu
#	tab_menu              = tauon.tab_menu
#	extra_tab_menu        = tauon.extra_tab_menu
#	track_menu            = tauon.track_menu
#	selection_menu        = tauon.selection_menu
#	folder_menu           = tauon.folder_menu
#	picture_menu          = tauon.picture_menu
#	mode_menu             = tauon.mode_menu
#	extra_menu            = tauon.extra_menu

def main(holder: Holder) -> None:
	from tauon.t_modules.t_run import main as run_main

	run_main(holder)



# type_enforced.Enforcer(sys.modules[__name__])
