"""Tauon application launch and runtime orchestration."""

from __future__ import annotations

import builtins
import colorsys
import copy
import ctypes
import datetime
import gc as gbc
import gettext
import importlib
import json
import locale as py_locale
import logging
import math
import os
import pickle
import shutil
import signal
import sys
import threading
import time
import urllib.request
import webbrowser
from ctypes import c_char_p, c_double, c_int, c_void_p, pointer
from pathlib import Path
from typing import TYPE_CHECKING

import musicbrainzngs
import sdl3
from unidecode import unidecode

from tauon.t_modules import t_visuals
from tauon.t_modules.t_config import Config
from tauon.t_modules.t_custom import (
	AlbumflowWidget,
	GridGalleryWidget,
	SPECTRO_PRESETS as CL_SPECTRO_PRESETS,
	STACK_COUNTS as CL_STACK_COUNTS,
	TEMPLATES as CL_TEMPLATES,
	WIDGET_SPECS as CL_WIDGET_SPECS,
)
from tauon.t_modules.t_db_migrate import database_migrate, migrate_star_store_71
from tauon.t_modules.t_enums import Backend, GuiMode, LoaderCommand, MiniModeMode, PlayingState, QueueType, StopMode
from tauon.t_modules.t_extra import (
	TestTimer,
	Timer,
	alpha_blend,
	alpha_mod,
	atomic_save,
	clean_string,
	coll_point,
	colour_value,
	d_date_display,
	get_filesize_string,
	grow_rect,
	mac_styles,
	point_distance,
	point_proximity_test,
	shooter,
	test_lumi,
	tmp_cache_dir,
	window_is_focused,
)
from tauon.t_modules.t_input import (
	SCROLL_ANIMATION_FRAME_INTERVAL,
	SCROLL_PHYSICS_MIN_PIXELS,
	TOUCH_LOGIC_COOL_GESTURE_PIXELS_TO_SKIP_TRACK,
	TOUCH_LOGIC_TAP_VS_LONG_NS,
	XcursorImage,
	copy_to_clipboard,
	field_clear,
	field_copy,
	field_paste,
)
from tauon.t_modules.t_lyrics_ui import TimedLyricsEdit
from tauon.t_modules.t_models import (
	ColourRGBA,
	Directories,
	Formats,
	RadioPlaylist,
	RadioStation,
	StarRecord,
	TauonPlaylist,
	TauonQueueItem,
	TrackClass,
	intern_track_strings,
	queue_item_gen,
	uid_gen,
)
from tauon.t_modules.t_nowplaying_macos import MacNowPlayingHelper
from tauon.t_modules.t_panels import MetaBox
from tauon.t_modules.t_playlist import StandardPlaylist
from tauon.t_modules.t_menu import Menu, MenuItem, close_all_menus
from tauon.t_modules.t_overlays import NagBox
from tauon.t_modules.t_prefs import Prefs
from tauon.t_modules.t_scrobble import pylast
from tauon.t_modules.t_state import ColoursClass, Decorator, DConsole, Fonts, GuiVar, LoadImageAsset, MenuIcon, MenuTrackRef, WhiteModImageAsset, asset_loader
from tauon.t_modules.t_templates import encode_folder_name, parse_template2
from tauon.t_modules.t_text import TextBox
from tauon.t_modules.t_themeload import load_theme
from tauon.t_modules.t_settings import auto_scale, get_theme_name, get_theme_number, get_themes
from tauon.t_modules.t_visuals import get_renderer_name, renderer_name_supports_milkdrop, Showcase
from tauon.t_modules.t_webserve import controller, webserve

from tauon.t_modules.t_main import (
	Bag,
	GMETrackInfo,
	Tauon,
	clear_icon_cache,
	get_global_mouse,
	get_window_position,
	is_module_loaded,
	load_prefs,
	menu_is_open,
	save_prefs,
	scale_assets,
	setup_tls,
	visit_radio_site,
	visit_radio_station,
	whicher,
	worker1,
	worker2,
	worker3,
	worker4,
	macos,
	platform_system,
	windows,
	win_ver,
)
try:
	from tauon.t_modules.t_main import Chrome
except ImportError:
	pass

if TYPE_CHECKING:
	from collections.abc import Callable
	from ctypes import CDLL

	from tauon.t_modules.t_bootstrap import Holder


def main(holder: Holder) -> None:
	if sys.platform in ("linux", "win32", "darwin"):
		import gi

		from gi.repository import GLib

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
	log                    = holder.log
	logging.info(f"Window size: {window_size}; Logical size: {logical_size}")
	renderer_name = get_renderer_name(renderer)
	if renderer_name is not None:
		logging.info(f"SDL renderer: {renderer_name}")
	if not renderer_name_supports_milkdrop(renderer_name):
		logging.warning("SDL renderer is not OpenGL; disabling Milkdrop visualizer")
		t_visuals.milky_ready = False
		if not t_visuals.milky_error:
			t_visuals.milky_error = "SDL renderer is not OpenGL"

	tls_context = setup_tls(holder)
	last_fm_enable = is_module_loaded("pylast")
	if last_fm_enable:
		# pyLast needs to be reimported AFTER setup_tls(), else pyinstaller breaks
		importlib.reload(pylast)

	discord_allow = is_module_loaded("pypresence", "ActivityType")
	#ctypes = sys.modules.get("ctypes")  # Fetch from loaded modules

	if sys.platform == "win32" and windows:
		font_folder = str(install_directory / "fonts")
		if os.path.isdir(font_folder):
			logging.info(f"Fonts directory:           {font_folder}")

			fc = ctypes.cdll.LoadLibrary("libfontconfig-1.dll")
			fc.FcConfigReference.restype = ctypes.c_void_p
			fc.FcConfigReference.argtypes = (ctypes.c_void_p,)
			fc.FcConfigAppFontAddDir.argtypes = (ctypes.c_void_p, ctypes.c_char_p)
			config = ctypes.c_void_p()
			config.contents = fc.FcConfigGetCurrent()
			fc.FcConfigAppFontAddDir(config.value, font_folder.encode())

	# Detect what desktop environment we are in to enable specific features
	desktop = os.environ.get("XDG_CURRENT_DESKTOP")
	# de_notify_support = desktop == 'GNOME' or desktop == 'KDE'
	de_notify_support = False
	draw_min_button = True
	draw_max_button = True
	left_window_control = False

	detect_macstyle = False
	gtk_settings: Gtk.Settings | None = None
	mac_close = ColourRGBA(253, 70, 70, 255)
	mac_maximize = ColourRGBA(254, 176, 36, 255)
	mac_minimize = ColourRGBA(42, 189, 49, 255)
	try:
		# TODO(Martin): Bump to 4.0 - https://github.com/Taiko2k/Tauon/issues/1316
		gi.require_version("Gtk", "3.0")
		from gi.repository import Gtk

		gtk_settings = Gtk.Settings().get_default()
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
	scaled_asset_directory = user_directory / "scaled-icons"

	music_directory = Path("~").expanduser() / "Music"
	if not music_directory.is_dir():
		music_directory = Path("~").expanduser() / "music"

	download_directory = Path("~").expanduser() / "Downloads"

	## Detect if we are installed or running portable
	##   * Linux is set depending on which directory we're launching from
	##   * Windows is assumed always installed
	##   * macOS is assumed always installed
	##   * Any of the above can be overriden by creating a file called 'portable' in the install directory
	## TODO(Martin): This code is partially duped in __main__.py
	install_mode = False
	flatpak_mode = False
	snap_mode = False
	# We do not have any fancy directory detection unlike on Linux, so just assume installed mode
	if macos or windows:
		install_mode = True
	# Override to Portable mode if necessary
	if (install_directory / "portable").is_file():
		install_mode = False
	elif str(install_directory).startswith(("/opt/", "/usr/", "/app/", "/snap/", "/nix/store/")):
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

	logging.info(f"Platform: {sys.platform}")

	if pyinstaller_mode:
		logging.info("Pyinstaller mode")

	# If we're installed, use home data locations
	if install_mode:
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
	else:
		logging.info("Running in portable mode")
		config_directory = user_directory

	milkdrop_preset_load_log = user_directory / "milkdrop-preset-load.log"
	if milkdrop_preset_load_log.exists():
		try:
			milkdrop_preset_load_log.unlink()
			logging.info("Removed previous Milkdrop preset load log: %s", milkdrop_preset_load_log)
		except Exception:
			logging.exception("Failed to remove previous Milkdrop preset load log: %s", milkdrop_preset_load_log)

	if not (user_directory / "state.p").is_file() and cache_directory.is_dir():
		logging.info("Clearing old cache directory")
		logging.info(cache_directory)
		shutil.rmtree(str(cache_directory))

	n_cache_dir = cache_directory / "network"
	e_cache_dir = cache_directory / "export"
	g_cache_dir = cache_directory / "gallery"
	a_cache_dir = cache_directory / "artist"
	r_cache_dir = cache_directory / "radio-thumbs"
	b_cache_dir = user_directory  / "artist-backgrounds"

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
		logging.debug(f"Override music to: {music_directory}")

	if os.getenv("XDG_DOWNLOAD_DIR"):
		download_directory = Path(os.getenv("XDG_DOWNLOAD_DIR"))
		logging.debug(f"Override downloads to: {download_directory}")

	if music_directory:
		music_directory = Path(os.path.expandvars(music_directory))
	if download_directory:
		download_directory = Path(os.path.expandvars(download_directory))

	if not music_directory.is_dir():
		music_directory = None

	locale_directory = install_directory / "locale"
	if flatpak_mode:
		locale_directory = Path("/app/share/locale")
	#elif str(install_directory).startswith(("/opt/", "/usr/")):
	#	locale_directory = Path("/usr/share/locale")

	dirs = Directories(
		install_directory=install_directory,
		svg_directory=svg_directory,
		asset_directory=asset_directory,
		scaled_asset_directory=scaled_asset_directory,
		locale_directory=locale_directory,
		user_directory=user_directory,
		config_directory=config_directory,
		cache_directory=cache_directory,
		home_directory=home_directory,
		music_directory=music_directory,
		download_directory=download_directory,
		n_cache_directory=n_cache_dir,
		e_cache_directory=e_cache_dir,
		g_cache_directory=g_cache_dir,
		a_cache_directory=a_cache_dir,
		r_cache_directory=r_cache_dir,
		b_cache_directory=b_cache_dir,
	)

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

	launch_prefix = ""
	if flatpak_mode:
		launch_prefix = "flatpak-spawn --host "

	if not macos:
		icon = sdl3.IMG_Load(str(asset_directory / "icon-64.png").encode())
		sdl3.SDL_SetWindowIcon(t_window, icon)

	if not phone:
		if window_size[0] != logical_size[0]:
			sdl3.SDL_SetWindowMinimumSize(t_window, 560, 330)
		else:
			sdl3.SDL_SetWindowMinimumSize(t_window, round(560 * scale), round(330 * scale))

	max_window_tex = 1000
	if window_size[0] > max_window_tex or window_size[1] > max_window_tex:
		while window_size[0] > max_window_tex:
			max_window_tex += 1000
		while window_size[1] > max_window_tex:
			max_window_tex += 1000

	main_texture = sdl3.SDL_CreateTexture(
		renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET, max_window_tex,
		max_window_tex)
	main_texture_overlay_temp = sdl3.SDL_CreateTexture(
		renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET,
		max_window_tex, max_window_tex)

	overlay_texture_texture = sdl3.SDL_CreateTexture(renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET, 300, 300)
	sdl3.SDL_SetTextureBlendMode(overlay_texture_texture, sdl3.SDL_BLENDMODE_BLEND)
	sdl3.SDL_SetRenderTarget(renderer, overlay_texture_texture)
	sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
	sdl3.SDL_RenderClear(renderer)
	sdl3.SDL_SetRenderTarget(renderer, None)

	tracklist_texture = sdl3.SDL_CreateTexture(
		renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET, max_window_tex,
		max_window_tex)
	tracklist_texture_rect = sdl3.SDL_FRect(0, 0, max_window_tex, max_window_tex)
	# The tracklist texture is built over a transparent clear, so its content
	# is effectively premultiplied (translucent panel fills, premultiplied
	# text textures); composite it src-over in premultiplied form —
	# SDL_BLENDMODE_BLEND would multiply by alpha a second time
	sdl3.SDL_SetTextureBlendMode(tracklist_texture, sdl3.SDL_ComposeCustomBlendMode(
		sdl3.SDL_BLENDFACTOR_ONE,
		sdl3.SDL_BLENDFACTOR_ONE_MINUS_SRC_ALPHA,
		sdl3.SDL_BLENDOPERATION_ADD,
		sdl3.SDL_BLENDFACTOR_ONE,
		sdl3.SDL_BLENDFACTOR_ONE_MINUS_SRC_ALPHA,
		sdl3.SDL_BLENDOPERATION_ADD,
	))

	sdl3.SDL_SetRenderTarget(renderer, None)

	# Paint main texture
	sdl3.SDL_SetRenderTarget(renderer, main_texture)
	sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)

	sdl3.SDL_SetRenderTarget(renderer, main_texture_overlay_temp)
	sdl3.SDL_SetTextureBlendMode(main_texture_overlay_temp, sdl3.SDL_BLENDMODE_BLEND)
	sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
	sdl3.SDL_RenderClear(renderer)



	# sdl3.SDL_SetRenderTarget(renderer, None)
	# sdl3.SDL_SetRenderDrawColor(renderer, 7, 7, 7, 255)
	# sdl3.SDL_RenderClear(renderer)
	# #sdl3.SDL_RenderPresent(renderer)

	# sdl3.SDL_SetWindowOpacity(t_window, window_opacity)

	loaded_asset_dc: dict[str, WhiteModImageAsset | LoadImageAsset] = {}
	# loading_image = asset_loader(bag, bag.loaded_asset_dc, "loading.png")

	if maximized:
		i_x = pointer(c_int(0))
		i_y = pointer(c_int(0))

		time.sleep(0.02)
		sdl3.SDL_PumpEvents()
		sdl3.SDL_GetWindowSize(t_window, i_x, i_y)
		logical_size[0] = i_x.contents.value
		logical_size[1] = i_y.contents.value
		sdl3.SDL_GetWindowSizeInPixels(t_window, i_x, i_y)
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

	# Detect locale for translations
	try:
		py_locale.setlocale(py_locale.LC_ALL, "")
	except Exception:
		logging.exception("SET LOCALE ERROR")

	wayland = True
	if os.environ.get("SDL_VIDEODRIVER") != "wayland":
		wayland = False
		os.environ["GDK_BACKEND"] = "x11"

	vis_update = False


	# Player Variables----------------------------------------------------------------------------
	Archive_Formats = {"zip"}

	if whicher("unrar", flatpak_mode):
		Archive_Formats.add("rar")

	if whicher("7z", flatpak_mode):
		Archive_Formats.add("7z")

	MOD_Formats = {"xm", "mod", "s3m", "it", "mptm", "umx", "okt", "mtm", "669", "far", "wow", "dmf", "med", "mt2", "ult"}
	GME_Formats = {"ay", "gbs", "gym", "hes", "kss", "nsf", "nsfe", "sap", "spc", "vgm", "vgz"}
	formats = Formats(
		colours = {
			"MP3":   ColourRGBA(255, 130, 80,  255),  # Burnt orange
			"FLAC":  ColourRGBA(156, 249, 79,  255),  # Bright lime green
			"M4A":   ColourRGBA(81,  220, 225, 255),  # Soft cyan
			"AIFF":  ColourRGBA(81,  220, 225, 255),  # Soft cyan
			"OGG":   ColourRGBA(244, 244, 78,  255),  # Light yellow
			"OGA":   ColourRGBA(244, 244, 78,  255),  # Light yellow
			"WMA":   ColourRGBA(213, 79,  247, 255),  # Magenta
			"APE":   ColourRGBA(247, 79,  79,  255),  # Deep pink
			"TTA":   ColourRGBA(94,  78,  244, 255),  # Purple
			"OPUS":  ColourRGBA(247, 79,  146, 255),  # Pink
			"AAC":   ColourRGBA(79,  247, 168, 255),  # Teal
			"WV":    ColourRGBA(229, 23,  18,  255),  # Deep red
			"PLEX":  ColourRGBA(229, 160, 13,  255),  # Orange-brown
			"TAU":   ColourRGBA(111, 98,  190, 255),  # Lavender
			"SUB":   ColourRGBA(235, 140, 20,  255),  # Golden yellow
			"TIDAL": ColourRGBA(0,   0,   0,   255),  # Black
			"JELY":  ColourRGBA(190, 100, 210, 255),  # Fuchsia
			"XM":    ColourRGBA(50,  50,  50,  255),  # Grey
			"MOD":   ColourRGBA(50,  50,  50,  255),  # Grey
			"S3M":   ColourRGBA(50,  50,  50,  255),  # Grey
			"IT":    ColourRGBA(50,  50,  50,  255),  # Grey
			"MPTM":  ColourRGBA(50,  50,  50,  255),  # Grey
			"AY":    ColourRGBA(237, 212, 255, 255),  # Pastel purple
			"GBS":   ColourRGBA(255, 165, 0,   255),  # Vibrant orange
			"GYM":   ColourRGBA(0,   191, 255, 255),  # Bright blue
			"HES":   ColourRGBA(176, 224, 230, 255),  # Light blue-green
			"KSS":   ColourRGBA(255, 255, 153, 255),  # Bright yellow
			"NSF":   ColourRGBA(255, 140, 0,   255),  # Deep orange
			"NSFE":  ColourRGBA(255, 140, 0,   255),  # Deep orange
			"SAP":   ColourRGBA(152, 255, 152, 255),  # Light green
			"SPC":   ColourRGBA(255, 128, 0,   255),  # Bright orange
			"VGM":   ColourRGBA(0,   128, 255, 255),  # Deep blue
			"VGZ":   ColourRGBA(0,   128, 255, 255),  # Deep blue
		},
		VID = {"mp4", "webm"},
		MOD = MOD_Formats,
		GME = GME_Formats,
		DA = {
			"mp3", "wav", "opus", "flac", "ape", "aiff",
			"m4a", "m4b", "ogg", "oga", "aac", "tta", "wv", "wma",
		} | MOD_Formats | GME_Formats,
		Archive = Archive_Formats,
	)

	# Library and loader Variables--------------------------------------------------------
	db_version: float = 0.0
	latest_db_version: float = 79

	rename_files_previous = ""
	rename_folder_previous = ""

	radio_playlists: list[RadioPlaylist] = [RadioPlaylist(uid=uid_gen(), name="Default", stations=[])]

	fonts = Fonts()
	colours = ColoursClass()
	colours.post_config()

	mpt: CDLL | None = None
	p = ctypes.util.find_library("openmpt") # Linux
	p = p or ctypes.util.find_library("libopenmpt-0") # Windows
	try:
		if p:
			mpt = ctypes.cdll.LoadLibrary(p)
		elif windows:
			mpt = ctypes.cdll.LoadLibrary("libopenmpt-0.dll")
		else:
			mpt = ctypes.cdll.LoadLibrary("libopenmpt.so.0")

		mpt.openmpt_module_create_from_memory.restype = c_void_p
		mpt.openmpt_module_get_metadata.restype = c_char_p
		mpt.openmpt_module_get_duration_seconds.restype = c_double
	except Exception:
		logging.exception("Failed to load libopenmpt!")

	gme: CDLL | None = None
	p = ctypes.util.find_library("gme") # Linux
	p = p or ctypes.util.find_library("libgme") # Windows
	try:
		if p:
			gme = ctypes.cdll.LoadLibrary(p)
		elif windows:
			gme = ctypes.cdll.LoadLibrary("libgme.dll")
		else:
			gme = ctypes.cdll.LoadLibrary("libgme.so.0")

		gme.gme_free_info.argtypes = [ctypes.POINTER(GMETrackInfo)]
		gme.gme_track_info.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.POINTER(GMETrackInfo)), ctypes.c_int]
		gme.gme_track_info.restype = ctypes.c_char_p
		gme.gme_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
		gme.gme_open_file.restype = ctypes.c_char_p
	except Exception:
		logging.exception("Cannot find libgme")

	force_subpixel_text = False
	if gtk_settings and gtk_settings.get_property("gtk-xft-rgba") == "rgb":
		force_subpixel_text = True
	encoder_output = user_directory / "encoder" if music_directory is None else music_directory / "encode-output"
	power_save = False
	if macos or phone:
		power_save = True

	# TODO(Taiko): This is legacy. New settings are added straight to the save list (need to overhaul)
	view_prefs = {
		"split-line": True,
		"update-title": False,
		"star-lines": False,
		"side-panel": True,
		"dim-art": False,
		"pl-follow": False,
		"scroll-enable": True,
		"smooth-scroll-enable": False,
		"smooth-scroll-speed": 1.0,
	}

	prefs = Prefs(
		view_prefs=view_prefs,
		power_save=power_save,
		encoder_output=encoder_output,
		force_subpixel_text=force_subpixel_text,
		macos=macos,
		macstyle=macos or detect_macstyle,
		left_window_control=macos or left_window_control,
		phone=phone,
		discord_allow=discord_allow,
		desktop=desktop,
		window_opacity=window_opacity,
		ui_scale=scale,
	)
	prefs.theme = get_theme_number(dirs, prefs.theme_name)

	bag = Bag(
		cf=Config(),
		dev_mode=dev_mode,
		gme=gme,
		mpt=mpt,
		colours=colours,
		console=DConsole(),
		dirs=dirs,
		prefs=prefs,
		fonts=fonts,
		formats=formats,
		renderer=renderer,
		#sdl_syswminfo=sss,
		pump=True,
		wayland=wayland,
		# de_notify_support = desktop == 'GNOME' or desktop == 'KDE'
		de_notify_support=False,
		log=log,
		draw_min_button=draw_min_button,
		draw_max_button=draw_max_button,
		download_directories=[],
		overlay_texture_texture=overlay_texture_texture,
		smtc=False,
		macos=macos,
		mac_close=mac_close,
		mac_maximize=mac_maximize,
		mac_minimize=mac_minimize,
		windows=windows,
		phone=phone,
		should_save_state=True,
		old_window_position=old_window_position,
		desktop=desktop,
		platform_system=platform_system,
		last_fm_enable=last_fm_enable,
		launch_prefix=launch_prefix,
		latest_db_version=latest_db_version,
		flatpak_mode=flatpak_mode,
		snap_mode=snap_mode,
		master_count=0,
		playing_in_queue=0,
		playlist_playing=-1,
		playlist_view_position=0,
		selected_in_playlist=-1,
		album_mode_art_size=int(200 * scale),
		primary_stations=[],
		tls_context=tls_context,
		track_queue=[],
		volume=75,
		multi_playlist=[],
		cue_list=[],
		p_force_queue=[],
		logical_size=logical_size,
		window_size=window_size,
		gen_codes={},
		master_library={},
		loaded_asset_dc=loaded_asset_dc,
		radio_playlist_viewing=0,
		radio_playlists=radio_playlists,
		folder_image_offsets={},
	)
	del radio_playlists

	# If scaled-icons directory exists, use it even for initial loading
	if (user_directory / "scaled-icons").exists() and bag.prefs.ui_scale != 1:
		bag.dirs.scaled_asset_directory = user_directory / "scaled-icons"

	gui = GuiVar(
		bag=bag,
		tracklist_texture_rect=tracklist_texture_rect,
		tracklist_texture=tracklist_texture,
		main_texture_overlay_temp=main_texture_overlay_temp,
		main_texture=main_texture,
		max_window_tex=max_window_tex,
	)
	del max_window_tex

	inp = gui.inp
	keymaps = gui.keymaps
	# GUI Variables -------------------------------------------------------------------------------------------
	# Variables now go in the gui, pctl, input and prefs class instances. The following just haven't been moved yet
	# -----------------------------------------------------
	# STATE LOADING
	# Loading of program data from previous run
	gbc.disable()

	if (user_directory / "lyrics_substitutions.json").is_file():
		try:
			with (user_directory / "lyrics_substitutions.json").open() as f:
				prefs.lyrics_subs = json.load(f)
		except FileNotFoundError:
			logging.error("No existing lyrics_substitutions.json file")  # noqa: TRY400
		except Exception:
			logging.exception("Unknown error loading lyrics_substitutions.json")

	perf_timer = Timer()
	perf_timer.set()

	bag.primary_stations.append(RadioStation(
		title="SomaFM Groove Salad",
		stream_url="https://ice3.somafm.com/groovesalad-128-mp3",
		country="USA",
		website_url="https://somafm.com/groovesalad",
		icon="https://somafm.com/logos/120/groovesalad120.png"))

	bag.primary_stations.append(RadioStation(
		title="SomaFM PopTron",
		stream_url="https://ice3.somafm.com/poptron-128-mp3",
		country="USA",
		website_url="https://somafm.com/poptron/",
		icon="https://somafm.com/logos/120/poptron120.jpg"))

	bag.primary_stations.append(RadioStation(
		title="SomaFM Vaporwaves",
		stream_url="https://ice4.somafm.com/vaporwaves-128-mp3",
		country="USA",
		website_url="https://somafm.com/vaporwaves",
		icon="https://somafm.com/img3/vaporwaves400.png"))

	bag.primary_stations.append(RadioStation(
		title="DKFM Shoegaze Radio",
		stream_url="https://kathy.torontocast.com:2005/stream",
		country="Canada",
		website_url="https://decayfm.com",
		icon="https://cdn-profiles.tunein.com/s193842/images/logod.png"))

	for station in bag.primary_stations:
		bag.radio_playlists[0].stations.append(station)

	# shoot_pump = threading.Thread(target=pumper, args=(bag,))
	# shoot_pump.daemon = True
	# shoot_pump.start()

	#after_scan, search_string_cache, search_dia_string_cache = load_savefile(latest_db_version, user_directory, bag, prefs, gui)
	after_scan: list[TrackClass] = []
	search_string_cache          = {}
	search_dia_string_cache      = {}
	state_path1 = user_directory / "state.p"
	state_path2 = user_directory / "state.p.backup"
	# Legacy TrackClass.misc dicts pulled from pre-v79 saves, keyed by track
	# index. Distributed into the new __slots__ fields by the v79 migration.
	legacy_track_misc: dict[int, dict] = {}
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
			if len(save) > 63 and save[63] is not None:
				prefs.ui_scale = save[63]
				# prefs.ui_scale = 1.3
				# gui.__init__()

			if len(save) > 0 and save[0] is not None:
				bag.master_library = save[0]
				# try: # TODO(Taiko): remove me before release!
				# 	from watchpoints import watch
				# 	def logchange3(frame, elem, exec_info):
				# 		logging.warning(f"Master library was modified! @ {exec_info}")
				#
				# 	watch(bag.master_library, callback=logchange3)
				# except Exception:
				# 	logging.exception("Module Watchpoints not found")
			bag.master_count = save[1]
			# try: # TODO(Taiko): remove me before release!
			# 	from watchpoints import watch
			# 	def logchange2(frame, elem, exec_info):
			# 		logging.warning(f"Master count was modified! @ {exec_info}")
			#
			# 	watch(bag.master_count, callback=logchange2)
			# except Exception:
			# 	logging.exception("Module Watchpoints not found")

			bag.playlist_playing = save[2]
			bag.active_playlist_viewing = save[3]
			bag.playlist_view_position = save[4]
			if len(save) > 5 and save[5] is not None:
				if db_version > 68:
					bag.multi_playlist = []
					tauonplaylist_jar = save[5]
					for i, d in enumerate(tauonplaylist_jar):
						p = TauonPlaylist(**d)
						bag.multi_playlist.append(p)

						# try:  # TODO(Taiko): remove me before release!
						# 	from watchpoints import watch
						# 	def logchange(frame, elem, exec_info):
						# 		logging.warning(f"A playlist was modified! @ {exec_info}")
						# 	watch(p.playlist_ids, callback=logchange)
						# except Exception:
						# 	logging.exception("Module Watchpoints not found")

						if i == bag.active_playlist_viewing:
							bag.default_playlist = p.playlist_ids
				else:
					bag.multi_playlist = save[5]
			bag.volume = save[6]
			bag.track_queue = save[7]
			bag.playing_in_queue = save[8]
			# bag.default_playlist = save[9]  # value is now set above
			# bag.playlist_playing = save[10]
			# cue_list = save[11]
			# radio_field_text = save[12]
			prefs.theme = save[13]
			bag.folder_image_offsets = save[14]
			# lfm_username = save[15]
			# lfm_hash = save[16]
			prefs.view_prefs = save[18]
			# window_size = save[19]
			gui.save_size = copy.copy(save[19])
			gui.rspw = save[20]
			# savetime = save[21]
			gui.vis_want = save[22]
			bag.selected_in_playlist = save[23]
			if len(save) > 24 and save[24] is not None:
				bag.album_mode_art_size = save[24]
			if len(save) > 25 and save[25] is not None:
				draw_border = save[25]
			if len(save) > 26 and save[26] is not None:
				prefs.enable_web = save[26]
			if len(save) > 27 and save[27] is not None:
				prefs.allow_remote = save[27]
			if len(save) > 28 and save[28] is not None:
				prefs.expose_web = save[28]
			# save[29] stored prefs.enable_transcode in older versions; transcode folder is now always shown
			if len(save) > 30 and save[30] is not None:
				prefs.show_rym = save[30]
			# if len(save) > 31 and save[31] is not None:
			#	 combo_mode_art_size = save[31]
			if len(save) > 32 and save[32] is not None:
				gui.maximized = save[32]
			if len(save) > 33 and save[33] is not None:
				prefs.prefer_bottom_title = save[33]
			if len(save) > 34 and save[34] is not None:
				gui.display_time_mode = save[34]
			# if len(save) > 35 and save[35] is not None:
			#	 prefs.transcode_mode = save[35]
			if len(save) > 36 and save[36] is not None:
				prefs.transcode_codec = save[36]
			if len(save) > 37 and save[37] is not None:
				prefs.transcode_bitrate = save[37]
			# if len(save) > 38 and save[38] is not None:
			#	 prefs.line_style = save[38]
			# if len(save) > 39 and save[39] is not None:
			#	 prefs.cache_gallery = save[39]
			if len(save) > 40 and save[40] is not None:
				prefs.playlist_font_size = save[40]
			if len(save) > 41 and save[41] is not None:
				prefs.use_title = save[41]
			if len(save) > 42 and save[42] is not None:
				gui.pl_st = save[42]
			# if len(save) > 43 and save[43] is not None:
			#	 gui.set_mode = save[43]
			#	 gui.set_bar = gui.set_mode
			if len(save) > 45 and save[45] is not None:
				prefs.playlist_row_height = save[45]
			if len(save) > 46 and save[46] is not None:
				prefs.show_wiki = save[46]
			if len(save) > 47 and save[47] is not None:
				prefs.auto_extract = save[47]
			if len(save) > 48 and save[48] is not None:
				prefs.colour_from_image = save[48]
			if len(save) > 49 and save[49] is not None:
				gui.set_bar = save[49]
			if len(save) > 50 and save[50] is not None:
				gui.gallery_show_text = save[50]
			if len(save) > 51 and save[51] is not None:
				gui.bb_show_art = save[51]
			# if len(save) > 52 and save[52] is not None:
			#	 gui.show_stars = save[52]
			if len(save) > 53 and save[53] is not None:
				prefs.auto_lfm = save[53]
			if len(save) > 54 and save[54] is not None:
				prefs.scrobble_mark = save[54]
			if len(save) > 55 and save[55] is not None:
				prefs.replay_gain = save[55]
			# if len(save) > 56 and save[56] is not None:
			#	 prefs.radio_page_lyrics = save[56]
			if len(save) > 57 and save[57] is not None:
				prefs.show_gimage = save[57]
			if len(save) > 58 and save[58] is not None:
				prefs.end_setting = save[58]
			if len(save) > 59 and save[59] is not None:
				prefs.show_gen = save[59]
			# if len(save) > 60 and save[60] is not None:
			#	 url_saves = save[60]
			if len(save) > 61 and save[61] is not None:
				prefs.auto_del_zip = save[61]
			if len(save) > 62 and save[62] is not None:
				gui.level_meter_colour_mode = save[62]
			if len(save) > 64 and save[64] is not None:
				prefs.show_lyrics_side = save[64]
			# if len(save) > 65 and save[65] is not None:
			#	 prefs.last_device = save[65]
			if len(save) > 66 and save[66] is not None:
				gui.restart_album_mode = save[66]
			if len(save) > 67 and save[67] is not None:
				gui.album_playlist_width = save[67]
			if len(save) > 68 and save[68] is not None:
				prefs.transcode_opus_as = save[68]
			if len(save) > 69 and save[69] is not None:
				gui.star_mode = save[69]
				if gui.star_mode == "star":
					gui.star_mode = "none"
					prefs.rating_playtime_stars = True
			if len(save) > 70 and save[70] is not None:
				gui.rsp = save[70]
			if len(save) > 71 and save[71] is not None:
				gui.lsp = save[71]
			if len(save) > 72 and save[72] is not None:
				gui.rspw = save[72]
			if len(save) > 73 and save[73] is not None:
				gui.pref_gallery_w = save[73]
			if len(save) > 74 and save[74] is not None:
				gui.pref_rspw = save[74]
			if len(save) > 75 and save[75] is not None:
				gui.show_hearts = save[75]
			if len(save) > 76 and save[76] is not None:
				prefs.monitor_downloads = save[76]
			if len(save) > 77 and save[77] is not None:
				gui.artist_info_panel = save[77]
			if len(save) > 78 and save[78] is not None:
				prefs.extract_to_music = save[78]
			if len(save) > 79 and save[79] is not None:
				prefs.enable_lb = save[79]
			# if len(save) > 80 and save[80] is not None:
			#	 prefs.lb_token = save[80]
			#	 if prefs.lb_token is None:
			#		 prefs.lb_token = ""
			if len(save) > 81 and save[81] is not None:
				rename_files_previous = save[81]
			if len(save) > 82 and save[82] is not None:
				rename_folder_previous = save[82]
			if len(save) > 83 and save[83] is not None:
				prefs.use_jump_crossfade = save[83]
			if len(save) > 84 and save[84] is not None:
				prefs.use_transition_crossfade = save[84]
			if len(save) > 85 and save[85] is not None:
				prefs.show_notifications = save[85]
			# if len(save) > 86 and save[86] is not None:
			#	 prefs.true_shuffle = save[86]
			if len(save) > 87 and save[87] is not None:
				gui.remember_library_mode = save[87]
			# if len(save) > 88 and save[88] is not None:
			#	 prefs.show_queue = save[88]
			# if len(save) > 89 and save[89] is not None:
			#	 prefs.show_transfer = save[89]
			if len(save) > 90 and save[90] is not None:
				if db_version > 68:
					tauonqueueitem_jar = save[90]
					for d in tauonqueueitem_jar:
						nt = TauonQueueItem(**d)
						bag.p_force_queue.append(nt)
				else:
					bag.p_force_queue = save[90]
			if len(save) > 91 and save[91] is not None:
				prefs.use_pause_fade = save[91]
			if len(save) > 92 and save[92] is not None:
				prefs.append_total_time = save[92]
			if len(save) > 93 and save[93] is not None:
				prefs.backend = save[93]  # moved to config file
			if len(save) > 94 and save[94] is not None:
				prefs.album_shuffle_mode = save[94]
			if len(save) > 95 and save[95] is not None:
				prefs.album_repeat_mode = save[95]
			# if len(save) > 96 and save[96] is not None:
			#	prefs.finish_current = save[96]
			if len(save) > 97 and save[97] is not None:
				prefs.reload_state = save[97]
			# if len(save) > 98 and save[98] is not None:
			#	prefs.reload_play_state = save[98]
			if len(save) > 99 and save[99] is not None:
				prefs.last_fm_token = save[99]
			if len(save) > 100 and save[100] is not None:
				prefs.last_fm_username = save[100]
			# if len(save) > 101 and save[101] is not None:
			#	prefs.use_card_style = save[101]
			# if len(save) > 102 and save[102] is not None:
			#	prefs.auto_lyrics = save[102]
			if len(save) > 103 and save[103] is not None:
				prefs.auto_lyrics_checked = save[103]
			if len(save) > 104 and save[104] is not None:
				prefs.show_side_art = save[104]
			if len(save) > 105 and save[105] is not None:
				prefs.window_opacity = save[105]
			if len(save) > 106 and save[106] is not None:
				prefs.gallery_single_click = save[106]
			if len(save) > 107 and save[107] is not None:
				prefs.tabs_on_top = save[107]
			if len(save) > 108 and save[108] is not None:
				prefs.showcase_vis = save[108]
			if len(save) > 109 and save[109] is not None:
				prefs.spec2_colour_mode = save[109]
			# if len(save) > 110 and save[110] is not None:
			#	prefs.device_buffer = save[110]
			if len(save) > 111 and save[111] is not None:
				prefs.use_eq = save[111]
			if len(save) > 112 and save[112] is not None:
				prefs.eq = save[112]
			if len(save) > 113 and save[113] is not None:
				prefs.bio_large = save[113]
			if len(save) > 114 and save[114] is not None:
				prefs.discord_show = save[114]
			if len(save) > 115 and save[115] is not None:
				prefs.min_to_tray = save[115]
			if len(save) > 116 and save[116] is not None:
				prefs.guitar_chords = save[116]
			if len(save) > 117 and save[117] is not None:
				prefs.playback_follow_cursor = save[117]
			if len(save) > 118 and save[118] is not None:
				prefs.art_bg = save[118]
			if len(save) > 119 and save[119] is not None:
				prefs.random_mode = save[119]
			if len(save) > 120 and save[120] is not None:
				prefs.repeat_mode = save[120]
			if len(save) > 121 and save[121] is not None:
				prefs.art_bg_stronger = save[121]
			if len(save) > 123 and save[123] is not None:
				prefs.failed_artists = save[123]
			if len(save) > 124 and save[124] is not None:
				prefs.artist_list = save[124]
			if len(save) > 125 and save[125] is not None:
				prefs.auto_sort = save[125]
			if len(save) > 126 and save[126] is not None:
				prefs.lyrics_enables = save[126]
			if len(save) > 127 and save[127] is not None:
				prefs.fanart_notify = save[127]
			if len(save) > 129 and save[129] is not None:
				prefs.discogs_pat = save[129]
			if len(save) > 130 and save[130] is not None:
				prefs.mini_mode_mode = save[130]
			if len(save) > 131 and save[131] is not None:
				after_scan = save[131]
			if len(save) > 132 and save[132] is not None:
				gui.gallery_positions = save[132]
			if len(save) > 133 and save[133] is not None:
				prefs.chart_bg = save[133]
			if len(save) > 134 and save[134] is not None:
				prefs.left_panel_mode = save[134]
			if len(save) > 135 and save[135] is not None:
				gui.last_left_panel_mode = save[135]
			# if len(save) > 136 and save[136] is not None:
			#	prefs.gst_device = save[136]
			if len(save) > 137 and save[137] is not None:
				search_string_cache = save[137]
			if len(save) > 138 and save[138] is not None:
				search_dia_string_cache = save[138]
			if len(save) > 139 and save[139] is not None:
				bag.gen_codes = save[139]
			if len(save) > 140 and save[140] is not None:
				gui.show_ratings = save[140]
			if len(save) > 141 and save[141] is not None:
				gui.show_album_ratings = save[141]
			if len(save) > 142 and save[142] is not None:
				prefs.radio_urls = save[142]
			if len(save) > 143 and save[143] is not None:
				gui.restore_showcase_view = save[143]
			if len(save) > 144 and save[144] is not None:
				gui.saved_prime_tab = save[144]
			if len(save) > 145 and save[145] is not None:
				gui.saved_prime_direction = save[145]
			if len(save) > 146 and save[146] is not None:
				prefs.sync_playlist = save[146]
			if len(save) > 149 and save[149] is not None:
				prefs.show_band = save[149]
			if len(save) > 150 and save[150] is not None:
				prefs.download_playlist = save[150]
			if len(save) > 152 and save[152] is not None:
				prefs.auto_rec = save[152]
			if len(save) > 154 and save[154] is not None:
				prefs.use_libre_fm = save[154]
			if len(save) > 155 and save[155] is not None:
				prefs.old_playlist_box_position = save[155]
			if len(save) > 156 and save[156] is not None:
				prefs.artist_list_sort_mode = save[156]
			if len(save) > 157 and save[157] is not None:
				prefs.phazor_device_selected = save[157]
			if len(save) > 158 and save[158] is not None:
				prefs.failed_background_artists = save[158]
			if len(save) > 159 and save[159] is not None:
				prefs.bg_flips = save[159]
			if len(save) > 160 and save[160] is not None:
				prefs.tray_show_title = save[160]
			if len(save) > 161 and save[161] is not None:
				prefs.artist_list_style = save[161]
			if len(save) > 162 and save[162] is not None:
				trackclass_jar = save[162]
				collect_legacy_misc = 0 < db_version <= 78  # noqa: PLR2004
				for d in trackclass_jar:
					nt = TrackClass()
					for k, v in d.items():
						try:
							setattr(nt, k, v)
						except AttributeError:
							pass
					# Pre-v79 saves stored extended metadata in a "misc" dict,
					# which is no longer a TrackClass attribute. Hold onto it so
					# the v79 migration can spread it into the new fields.
					if collect_legacy_misc and "misc" in d:
						legacy_track_misc[nt.index] = d["misc"]
					intern_track_strings(nt)
					bag.master_library[nt.index] = nt
			if len(save) > 163 and save[163] is not None:
				prefs.premium = save[163]
			if len(save) > 164 and save[164] is not None:
				gui.restore_radio_view = save[164]
			if len(save) > 165 and save[165] is not None:
				if db_version > 69:
					bag.radio_playlists = []
					radioplaylist_jar = save[165]
					for d in radioplaylist_jar:
						nt = RadioPlaylist(**d)
						bag.radio_playlists.append(nt)
				else:
					bag.radio_playlists = save[165]
			if len(save) > 166 and save[166] is not None:
				bag.radio_playlist_viewing = save[166]
			if len(save) > 167 and save[167] is not None:
				prefs.radio_thumb_bans = save[167]
			if len(save) > 168 and save[168] is not None:
				prefs.playlist_exports = save[168]
			if len(save) > 169 and save[169] is not None:
				prefs.show_chromecast = save[169]
			if len(save) > 170 and save[170] is not None:
				prefs.cache_list = save[170]
			if len(save) > 171 and save[171] is not None:
				prefs.shuffle_lock = save[171]
			if len(save) > 172 and save[172] is not None:
				prefs.album_shuffle_lock_mode = save[172]
			if len(save) > 173 and save[173] is not None:
				gui.was_radio = save[173]
			if len(save) > 176 and save[176] is not None:
				prefs.artist_list_threshold = save[176]
			if len(save) > 177 and save[177] is not None:
				prefs.tray_theme = save[177]
			if len(save) > 178 and save[178] is not None:
				prefs.row_title_format = save[178]
			if len(save) > 179 and save[179] is not None:
				prefs.row_title_genre = save[179]
			if len(save) > 180 and save[180] is not None:
				prefs.row_title_separator_type = save[180]
			if len(save) > 181 and save[181] is not None:
				prefs.replay_preamp = save[181]
			if len(save) > 182 and save[182] is not None:
				prefs.gallery_combine_disc = save[182]
			if len(save) > 183 and save[183] is not None:
				bag.active_playlist_playing = save[183]
			if len(save) > 184 and save[184] is not None:
				prefs.milk = save[184]
			if len(save) > 185 and save[185] is not None:
				prefs.auto_milk = save[185]
			if len(save) > 186 and save[186] is not None:
				# Stored as str since v77 (pre-77 saves pickled a Path); Path()
				# normalises either form to the runtime type.
				prefs.loaded_preset = Path(save[186])
			if len(save) > 187 and save[187] is not None:
				bag.loaded_stop_mode = save[187]
			if len(save) > 188 and save[188] is not None:
				bag.loaded_stop_ref = save[188]
			if len(save) > 189 and save[189] is not None:
				prefs.start_in_tray = save[189]
			if len(save) > 190 and save[190] is not None:
				# Resume in the Custom Layout view. The layout itself loads
				# lazily (ensure_slot -> load_slots) on the first render.
				gui.custom_mode = save[190]
			if len(save) > 191 and save[191] is not None:
				prefs.spectrogram_colour = save[191]
			if len(save) > 192 and save[192] is not None:
				gui.pl_st_left = save[192]
			if len(save) > 193 and save[193] is not None:
				prefs.milk_cut_out = save[193]
			if len(save) > 194 and save[194] is not None:
				prefs.milk_favorite_presets = save[194]
			if len(save) > 195 and save[195] is not None:
				prefs.art_bg_frosted = save[195]
			if len(save) > 196 and save[196] is not None:
				prefs.replay_allow_compression = save[196]

			del save
			break

		except IndexError:
			logging.exception("Index error")
			break
		except Exception:
			logging.exception("Failed to load save file")

	core_timer = Timer()
	core_timer.set()
	logging.info(f"Database loaded in {round(perf_timer.get(), 3)} seconds.")

	perf_timer.set()
	keys = set(bag.master_library.keys())
	for pl in bag.multi_playlist:
		if db_version > 68 or db_version == 0:
			keys -= set(pl.playlist_ids)
		else:
			keys -= set(pl[2])
	if len(keys) > 5000:
		gui.suggest_clean_db = True
	# logging.info(f"Database scanned in {round(perf_timer.get(), 3)} seconds.")

	# bag.pump = False
	# shoot_pump.join()

	# temporary
	if window_size is None:
		window_size = window_default_size
		gui.rspw = 200

	# The queue and its position are persisted separately. An interrupted save
	# or a queue edited during shutdown can leave the position out of range.
	# Keep an empty queue at its neutral position instead of turning it into -1.
	if bag.track_queue:
		bag.playing_in_queue = max(0, min(bag.playing_in_queue, len(bag.track_queue) - 1))
	else:
		bag.playing_in_queue = 0

	shoot = threading.Thread(target=keymaps.load)
	shoot.daemon = True
	shoot.start()

	# Loading Config -----------------


	if download_directory.is_dir():
		bag.download_directories.append(str(download_directory))

	if music_directory is not None and music_directory.is_dir():
		bag.download_directories.append(str(music_directory))

	load_prefs(bag)
	show_upgrade_splash = False
	if prefs.release_splash_version != NagBox.SPLASH_VERSION:
		show_upgrade_splash = db_version > 0
		prefs.release_splash_version = NagBox.SPLASH_VERSION
	save_prefs(bag)

	# Temporary
	if 0 < db_version <= 34:
		prefs.theme_name = get_theme_name(dirs, prefs.theme)
	if 0 < db_version <= 66:
		prefs.device_buffer = 80
	if 0 < db_version <= 53:
		logging.info("Resetting fonts to defaults")
		prefs.linux_font = "Noto Sans"
		prefs.linux_font_semibold = "Noto Sans Medium"
		prefs.linux_font_bold = "Noto Sans Bold"
		save_prefs(bag)

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

	# sss = SDL_SysWMinfo()
	# SDL_GetWindowWMInfo(t_window, sss)

	if prefs.use_gamepad:
		sdl3.SDL_InitSubSystem(sdl3.SDL_INIT_GAMEPAD)

	if bag.windows and win_ver >= 10:
		#logging.info(sss.info.win.window)
		SMTC_path = install_directory / "lib" / "TauonSMTC.dll"
		if SMTC_path.exists():
			try:
				bag.sm = ctypes.cdll.LoadLibrary(str(SMTC_path))

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
					gui.request_frame()
					tauon.wake()

				close_callback = ctypes.WINFUNCTYPE(ctypes.c_void_p, ctypes.c_int)(SMTC_button_callback)
				bag.smtc = bag.sm.init(close_callback) == 0
			except Exception:
				logging.exception("Failed to load TauonSMTC.dll - Media keys will not work!")
		else:
			logging.warning("Failed to load TauonSMTC.dll - Media keys will not work!")

	if bag.macos:
		# macOS Now Playing helper (native app) - communicates over stdin/stdout JSON lines.
		helper_exe: Path | None = None
		candidate_paths: list[Path] = []
		env_helper = os.environ.get("TAUON_NOWPLAYING_HELPER", "").strip()
		if env_helper:
			candidate_paths.append(Path(env_helper))
		candidate_paths.extend(
			[
				install_directory
				/ "lib"
				/ "TauonNowPlaying.app"
				/ "Contents"
				/ "MacOS"
				/ "TauonNowPlaying",
				# Development tree default (src/nowplaying/build)
				Path(__file__).resolve().parents[2]
				/ "nowplaying"
				/ "build"
				/ "TauonNowPlaying.app"
				/ "Contents"
				/ "MacOS"
				/ "TauonNowPlaying",
			]
		)

		for candidate in candidate_paths:
			try:
				if candidate.exists() and candidate.is_file() and os.access(candidate, os.X_OK):
					helper_exe = candidate
					break
			except Exception:
				logging.debug(f"Failed validating Now Playing helper candidate: {candidate}")

		if helper_exe is None:
			logging.debug("Now Playing helper not found; macOS media keys disabled")
		else:
			def _mac_media_key(name: str) -> None:
				logging.debug(f"NowPlaying sent key: {name}")
				# Reuse existing media key input handling.
				if name in {"PlayPause", "Play"}:
					inp.media_key = "Play"
				elif name == "Pause":
					inp.media_key = "Pause"
				elif name == "Next":
					inp.media_key = "Next"
				elif name == "Previous":
					inp.media_key = "Previous"
				elif name == "Stop":
					inp.media_key = "Stop"
				else:
					return
				gui.request_frame()
				tauon.wake()

			def _mac_seek_abs(seconds: float) -> None:
				try:
					tauon.pctl.seek_time(float(seconds))
				except Exception:
					logging.exception("Failed to seek via macOS Now Playing")
				else:
					gui.request_frame()
					tauon.wake()

			def _mac_seek_rel(delta: float) -> None:
				try:
					tauon.pctl.seek_time(tauon.pctl.playing_time + float(delta))
				except Exception:
					logging.exception("Failed to seek relative via macOS Now Playing")
				else:
					gui.request_frame()
					tauon.wake()

			bag.nowplaying_helper = MacNowPlayingHelper(
				executable=helper_exe,
				on_media_key=_mac_media_key,
				on_seek=_mac_seek_abs,
				on_seek_relative=_mac_seek_rel,
			)
			bag.nowplaying = bool(bag.nowplaying_helper.start())
			if bag.nowplaying:
				logging.info(f"Now Playing helper started: {helper_exe}")
			else:
				bag.nowplaying_helper = None

	try:
		prefs.update_title  = prefs.view_prefs["update-title"]
		prefs.prefer_side   = prefs.view_prefs["side-panel"]
		prefs.dim_art       = False  # view_prefs['dim-art']
		#pl_follow          = view_prefs['pl-follow']
		prefs.scroll_enable = prefs.view_prefs["scroll-enable"]
		prefs.smooth_scroll_enable = prefs.view_prefs.get("smooth-scroll-enable", False)
		prefs.smooth_scroll_speed = float(prefs.view_prefs.get("smooth-scroll-speed", 1.0))
		prefs.smooth_scroll_speed = min(max(prefs.smooth_scroll_speed, 0.25), 10.0)
		if "break-enable" in prefs.view_prefs:
			prefs.break_enable = prefs.view_prefs["break-enable"]
		else:
			logging.warning("break-enable not found in view_prefs[] when trying to load settings! First run?")
		#custom_line_mode  = view_prefs['custom-line']
		#thick_lines       = view_prefs['thick-lines']
		if "append-date" in prefs.view_prefs:
			prefs.append_date = prefs.view_prefs["append-date"]
		else:
			logging.warning("append-date not found in view_prefs[] when trying to load settings! First run?")
	except KeyError:
		logging.exception("Failed to load settings - pref not found!")
	except Exception:
		logging.exception("Failed to load settings!")

	if prefs.prefer_side is False:
		gui.rsp = False

	mpt: CDLL | None = None
	p = ctypes.util.find_library("openmpt") # Linux
	p = p or ctypes.util.find_library("libopenmpt-0") # Windows
	try:
		if p:
			mpt = ctypes.cdll.LoadLibrary(p)
		elif windows:
			mpt = ctypes.cdll.LoadLibrary("libopenmpt-0.dll")
		else:
			mpt = ctypes.cdll.LoadLibrary("libopenmpt.so.0")

		mpt.openmpt_module_create_from_memory.restype = c_void_p
		mpt.openmpt_module_get_metadata.restype = c_char_p
		mpt.openmpt_module_get_duration_seconds.restype = c_double
	except Exception:
		logging.exception("Failed to load libopenmpt!")

	gme: CDLL | None = None
	p = ctypes.util.find_library("gme") # Linux
	p = p or ctypes.util.find_library("libgme") # Windows
	try:
		if p:
			gme = ctypes.cdll.LoadLibrary(p)
		elif windows:
			gme = ctypes.cdll.LoadLibrary("libgme.dll")
		else:
			gme = ctypes.cdll.LoadLibrary("libgme.so.0")

		gme.gme_free_info.argtypes = [ctypes.POINTER(GMETrackInfo)]
		gme.gme_track_info.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.POINTER(GMETrackInfo)), ctypes.c_int]
		gme.gme_track_info.restype = ctypes.c_char_p
		gme.gme_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
		gme.gme_open_file.restype = ctypes.c_char_p

	except Exception:
		logging.exception("Cannot find libgme")

	tauon = Tauon(
		holder=holder,
		bag=bag,
		gui=gui,
	)
	if show_upgrade_splash:
		prefs.show_nag = True

	try:
		if tauon.prefs.discord_enable and tauon.prefs.discord_allow:
			try:
				tauon._signal_discord()
			except Exception:
				tauon.hit_discord()
	except Exception:
		logging.exception("Failed to start Discord RPC at startup")

	if tauon.windows:
		if not (tauon.install_directory / "lrclib-solver.exe").exists():
			logging.warning("lrclib-solver not found, uploading lyrics to LRCLIB will not be possible")
	else:
		if not (tauon.install_directory / "lrclib-solver").exists():
			logging.warning("lrclib-solver not found, uploading lyrics to LRCLIB will not be possible")

	if db_version > 0 and db_version < latest_db_version:
		clear_icon_cache(bag.dirs.scaled_asset_directory)

	auto_scale(bag)
	scale_assets(tauon, bag, gui, prefs.scale_want)

	tauon.after_scan              = after_scan
	tauon.search_string_cache     = search_string_cache
	tauon.search_dia_string_cache = search_dia_string_cache
	signal.signal(signal.SIGINT, tauon.signal_handler)
	pctl = tauon.pctl
	try:
		pctl.stop_mode = StopMode(bag.loaded_stop_mode)
	except ValueError:
		logging.warning(f"Invalid saved stop_mode value: {bag.loaded_stop_mode}")
		pctl.stop_mode = StopMode.OFF
	pctl.stop_ref = bag.loaded_stop_ref if pctl.stop_mode != StopMode.OFF else None
	if bag.multi_playlist:
		pctl.multi_playlist = bag.multi_playlist
		pctl.default_playlist = bag.default_playlist
	else:
		pctl.multi_playlist = [tauon.pl_gen(notify=False)]
		pctl.default_playlist = pctl.multi_playlist[0].playlist_ids
	notify_database_changed = pctl.notify_database_changed

	lastfm = tauon.lastfm
	lb = tauon.lb

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
				tauon.star_store.db = pickle.load(file)
				# Test if we truly have StarRecord in the DB file
				# If we have something else, it's likely an older DB format,
				# in which case we try migrating it
				for key, old_record in tauon.star_store.db.items():
					if not isinstance(old_record, StarRecord):
						migrate_star_store_71(tauon)

		except Exception:
			logging.exception("Unknown error loading star.p file")

	album_star_path = user_directory / "album-star.p"
	if album_star_path.is_file():
		try:
			with album_star_path.open("rb") as file:
				tauon.album_star_store.db = pickle.load(file)
		except Exception:
			logging.exception("Unknown error loading album-star.p file")
	else:
		logging.warning("Album star database file is missing, first run? Will create one anew!")

	# Run upgrades if we're behind the current DB standard
	if db_version > 0 and db_version < latest_db_version:
		logging.warning(f"Current DB version {db_version} was lower than latest {latest_db_version}, running migrations!")
		try:
			pctl.master_library, pctl.multi_playlist, pctl.force_queue, prefs.theme, prefs, gui, pctl.gen_codes, pctl.radio_playlists = database_migrate(
				tauon=tauon,
				db_version=db_version,
				master_library=pctl.master_library,
				legacy_track_misc=legacy_track_misc,
				install_mode=install_mode,
				multi_playlist=pctl.multi_playlist,
				install_directory=install_directory,
				a_cache_dir=a_cache_dir,
				cache_directory=cache_directory,
				config_directory=config_directory,
				user_directory=user_directory,
				gui=gui,
				gen_codes=pctl.gen_codes,
				prefs=prefs,
				radio_playlists=pctl.radio_playlists,
				theme=prefs.theme,
				p_force_queue=pctl.force_queue,
			)
			# Immediately write down migrations to prevent later crashes from throwing things out of alignment
			tauon.save_state()
		except ValueError:
			logging.exception("That should not happen")
			sys.exit(42)
		except Exception:
			logging.exception("Unknown error running database migration!")
			sys.exit(42)

	if not macos and not tauon.windows:
		from gi.repository import Notify

		try:
			Notify.init("Tauon Music Box")
			tauon.g_tc_notify = Notify.Notification.new(
				"Tauon Music Box",
				"Transcoding has finished.")
			value = GLib.Variant("s", t_id)
			tauon.g_tc_notify.set_hint("desktop-entry", value)

			tauon.g_tc_notify.add_action(
				"action_click",
				"Open Output Folder",
				tauon.g_open_encode_out,
				None,
			)
			tauon.de_notify_support = True
		except Exception:
			logging.exception("Failed init notifications")

		if tauon.de_notify_support:
			tauon.song_notification = Notify.Notification.new("Next track notification")
			value = GLib.Variant("s", t_id)
			tauon.song_notification.set_hint("desktop-entry", value)

	# TODO(Martin): Get rid of this and define it properly
	tauon.deco.get_themes = get_themes
	tauon.deco.renderer = renderer

	if prefs.backend != Backend.PHAZOR:
		prefs.backend = Backend.PHAZOR

	chrome_loaded = is_module_loaded("tauon.t_modules.t_chrome", "Chrome")
	if chrome_loaded:
		tauon.chrome = Chrome(tauon)

	if not macos and not tauon.windows:
		try:
			gnome_thread = threading.Thread(target=tauon.gnome.main)
			gnome_thread.daemon = True
			gnome_thread.start()
		except Exception:
			logging.exception("Could not start Dbus thread")

	if sys.platform == "win32":
		if win_ver < 10:
			logging.warning("Unsupported Windows version older than W10, hooking media keys the old way without SMTC!")
			import keyboard

			def key_callback(event) -> None:
				if event.event_type == "down":
					if event.scan_code == -179:
						inp.media_key = "Play"
					elif event.scan_code == -178:
						inp.media_key = "Stop"
					elif event.scan_code == -177:
						inp.media_key = "Previous"
					elif event.scan_code == -176:
						inp.media_key = "Next"
					gui.request_frame()
					tauon.wake()

			keyboard.hook_key(-179, key_callback)
			keyboard.hook_key(-178, key_callback)
			keyboard.hook_key(-177, key_callback)
			keyboard.hook_key(-176, key_callback)

	# -------------------------------------------------------------------------------------------
	# initiate SDL3 --------------------------------------------------------------------C-IS-----

	if not tauon.windows and "XCURSOR_THEME" in os.environ and "XCURSOR_SIZE" in os.environ:
		try:
			try:
				xcu = ctypes.cdll.LoadLibrary("libXcursor.so.1")
			except Exception:
				logging.exception("Failed to load libXcursor.so, will try libXcursor.so")
				xcu = ctypes.cdll.LoadLibrary("libXcursor.so")
			xcu.XcursorLibraryLoadImage.restype = ctypes.POINTER(XcursorImage)

			def get_xcursor(name: str) -> sdl3.LP_SDL_Cursor:
				if "XCURSOR_THEME" not in os.environ:
					raise ValueError("Missing XCURSOR_THEME in env")
				if "XCURSOR_SIZE" not in os.environ:
					raise ValueError("Missing XCURSOR_SIZE in env")
				xcursor_theme = os.environ["XCURSOR_THEME"]
				xcursor_size = os.environ["XCURSOR_SIZE"]
				c1 = xcu.XcursorLibraryLoadImage(c_char_p(name.encode()), c_char_p(xcursor_theme.encode()), c_int(int(xcursor_size))).contents
				sdl3.SDL_surface = sdl3.SDL_CreateSurfaceFrom(c1.width, c1.height, sdl3.SDL_PIXELFORMAT_ARGB8888, c1.pixels, c1.width * 4)
				cursor = sdl3.SDL_CreateColorCursor(sdl3.SDL_surface, round(c1.xhot), round(c1.yhot))
				xcu.XcursorImageDestroy(ctypes.byref(c1))
				sdl3.SDL_DestroySurface(sdl3.SDL_surface)
				return cursor

			cursor_br_corner = get_xcursor("se-resize")
			cursor_right_side = get_xcursor("right_side")
			cursor_top_side = get_xcursor("top_side")
			cursor_left_side = get_xcursor("left_side")
			cursor_bottom_side = get_xcursor("bottom_side")

			if sdl3.SDL_GetCurrentVideoDriver() == b"wayland":
				cursor_standard = get_xcursor("left_ptr")
				cursor_text = get_xcursor("xterm")
				cursor_shift = get_xcursor("sb_h_double_arrow")
				cursor_hand = get_xcursor("hand2")
				sdl3.SDL_SetCursor(cursor_standard)

		except Exception:
			logging.exception("Error loading xcursor")


	if not maximized and gui.maximized:
		sdl3.SDL_MaximizeWindow(t_window)

	# logging.error(sdl3.SDL_GetError())

	props = sdl3.SDL_GetWindowProperties(t_window)

	if tauon.windows:
		gui.window_id = sdl3.SDL_GetPointerProperty(props, sdl3.SDL_PROP_WINDOW_WIN32_HWND_POINTER, None)
		#gui.window_id = sss.info.win.window

	ddt = tauon.ddt
	ddt.scale = gui.scale
	ddt.force_subpixel_text = prefs.force_subpixel_text

	tauon.prime_fonts()

	text_box_canvas_rect = sdl3.SDL_FRect(0, 0, round(2000 * gui.scale), round(40 * gui.scale))
	text_box_canvas_hide_rect = sdl3.SDL_FRect(0, 0, round(2000 * gui.scale), round(40 * gui.scale))
	text_box_canvas = sdl3.SDL_CreateTexture(
		renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET, round(text_box_canvas_rect.w), round(text_box_canvas_rect.h))
	sdl3.SDL_SetTextureBlendMode(text_box_canvas, sdl3.SDL_BLENDMODE_BLEND)

	tauon.rename_files.text = prefs.rename_tracks_template
	if rename_files_previous:
		tauon.rename_files.text = rename_files_previous

	tauon.rename_folder.text = prefs.rename_folder_template
	if rename_folder_previous:
		tauon.rename_folder.text = rename_folder_previous

	# gui.scroll_hide_box = (0, gui.panelY, 28, window_size[1] - gui.panelBY - gui.panelY)

	#cctest = ColourPulse2(tauon)

	#setup_menus(tauon)
	playlist_menu         = tauon.playlist_menu
	radio_entry_menu      = tauon.radio_entry_menu
	showcase_menu         = tauon.showcase_menu
	center_info_menu      = tauon.center_info_menu
	gallery_menu          = tauon.gallery_menu
	artist_info_menu      = tauon.artist_info_menu
	repeat_menu           = tauon.repeat_menu
	shuffle_menu          = tauon.shuffle_menu
	artist_list_menu      = tauon.artist_list_menu
	lightning_menu        = tauon.lightning_menu
	lsp_menu              = tauon.lsp_menu
	folder_tree_menu      = tauon.folder_tree_menu
	folder_tree_stem_menu = tauon.folder_tree_stem_menu
	radio_context_menu    = tauon.radio_context_menu
	tab_menu              = tauon.tab_menu
	extra_tab_menu        = tauon.extra_tab_menu
	track_menu            = tauon.track_menu
	selection_menu        = tauon.selection_menu
	folder_menu           = tauon.folder_menu
	picture_menu          = tauon.picture_menu
	milky_menu            = tauon.milky_menu
	mode_menu             = tauon.mode_menu
	extra_menu            = tauon.extra_menu

	# . Menu entry: A side panel view layout
	lsp_menu.add(MenuItem(_("Playlists + Queue"), tauon.enable_playlist_list, disable_test=tauon.lsp_menu_test_playlist))
	lsp_menu.add(MenuItem(_("Queue"), tauon.enable_queue_panel, disable_test=tauon.lsp_menu_test_queue))
	# . Menu entry: Side panel view layout showing a list of artists with thumbnails
	lsp_menu.add(MenuItem(_("Artist List"), tauon.enable_artist_list, disable_test=tauon.lsp_menu_test_artist))
	# . Menu entry: A side panel view layout. Alternative name: Folder Tree
	lsp_menu.add(MenuItem(_("Folder Navigator"), tauon.enable_folder_list, disable_test=tauon.lsp_menu_test_tree))

	# Custom Layout edit context menu (native Menu system). Built once; its items
	# act on tauon.custom.menu_target, set when the menu is activated on right
	# click in edit mode.
	cm = tauon.custom
	if cm.menu is None:
		cl_menu = Menu(tauon, 155)
		cm.menu = cl_menu

		cl_menu.add_sub(_("Add Vertical Stack"), 60)
		_cl_sub_v = cl_menu.sub_number - 1
		for _n in CL_STACK_COUNTS:
			cl_menu.add_to_sub(_cl_sub_v, MenuItem(str(_n), cm._menu_add_stack, args=("v", _n)))

		cl_menu.add_sub(_("Add Horizontal Stack"), 60)
		_cl_sub_h = cl_menu.sub_number - 1
		for _n in CL_STACK_COUNTS:
			cl_menu.add_to_sub(_cl_sub_h, MenuItem(str(_n), cm._menu_add_stack, args=("h", _n)))

		cl_menu.add_sub(_("Add Tabbed Switcher"), 60)
		_cl_sub_tabs = cl_menu.sub_number - 1
		for _n in CL_STACK_COUNTS:
			cl_menu.add_to_sub(_cl_sub_tabs, MenuItem(str(_n), cm._menu_add_tabs, args=_n))

		cl_menu.add_sub(_("Add…"), 180)
		_cl_sub_add = cl_menu.sub_number - 1
		# Label this submenu "Replace…" when the target segment already has a
		# widget, "Add…" when it's an empty slot.
		def _add_or_replace_label() -> Decorator:
			text = _("Replace…") if cm._t_has_widget() else _("Add…")
			return Decorator(cl_menu.colours.menu_text, cl_menu.colours.menu_background, text)
		cl_menu.items[-1].render_func = _add_or_replace_label
		for _spec in CL_WIDGET_SPECS:
			cl_menu.add_to_sub(_cl_sub_add, MenuItem(
				_spec.name, cm._menu_add_widget, args=_spec.kind,
				disable_test=(lambda k=_spec.kind: cm.kind_disabled(k))))

		cl_menu.add(MenuItem(_("Remove"), cm._menu_remove_widget, show_test=cm._t_has_widget))
		cl_menu.add(MenuItem(_("Remove Stack"), cm._menu_remove_stack))
		cl_menu.br()
		cl_menu.add_sub(_("Layout…"), 175)
		_cl_sub_layout = cl_menu.sub_number - 1
		cl_menu.add_to_sub(_cl_sub_layout, MenuItem(_("Lock Vertical"), cm._menu_lock_v, show_test=cm._t_unlocked_v, no_exit=True))
		cl_menu.add_to_sub(_cl_sub_layout, MenuItem(_("Unlock Vertical"), cm._menu_lock_v, show_test=cm._t_locked_v, no_exit=True))
		cl_menu.add_to_sub(_cl_sub_layout, MenuItem(_("Lock Horizontal"), cm._menu_lock_h, show_test=cm._t_unlocked_h, no_exit=True))
		cl_menu.add_to_sub(_cl_sub_layout, MenuItem(_("Unlock Horizontal"), cm._menu_lock_h, show_test=cm._t_locked_h, no_exit=True))
		cl_menu.add_to_sub(_cl_sub_layout, MenuItem(_("Inset Square"), cm._menu_lock_aspect, show_test=cm._t_aspect_off, no_exit=True))
		cl_menu.add_to_sub(_cl_sub_layout, MenuItem(_("Remove Inset Square"), cm._menu_lock_aspect, show_test=cm._t_aspect_on, no_exit=True))
		cl_menu.add_to_sub(_cl_sub_layout, MenuItem(_("Square Max"), cm._menu_square_max, show_test=cm._t_square_off, no_exit=True))
		cl_menu.add_to_sub(_cl_sub_layout, MenuItem(_("Remove Square Max"), cm._menu_square_max, show_test=cm._t_square_on, no_exit=True))
		cl_menu.add_incrementor_to_sub(_cl_sub_layout, _("Gutter"), cm._menu_gutter_value, cm._menu_gutter_minus, cm._menu_gutter_plus)
		cl_menu.add_incrementor_to_sub(_cl_sub_layout, _("Padding"), cm._menu_padding_value, cm._menu_padding_minus, cm._menu_padding_plus)
		cl_menu.add_to_sub(_cl_sub_layout, MenuItem(_("Border"), cm._menu_border, show_test=cm._t_border_off, no_exit=True))
		cl_menu.add_to_sub(_cl_sub_layout, MenuItem(_("Remove Border"), cm._menu_border, show_test=cm._t_border_on, no_exit=True))
		cl_menu.add_to_sub(_cl_sub_layout, MenuItem(_("Make Stack Resizable"), cm._menu_stack_resizable, show_test=cm._t_stack_resizable_off, no_exit=True))
		cl_menu.add_to_sub(_cl_sub_layout, MenuItem(_("Make Stack Not Resizable"), cm._menu_stack_resizable, show_test=cm._t_stack_resizable_on, no_exit=True))
		cl_menu.br()
		cl_menu.add_sub(_("Load Template…"), 185)
		_cl_sub_t = cl_menu.sub_number - 1
		for _name in CL_TEMPLATES:
			cl_menu.add_to_sub(_cl_sub_t, MenuItem(_name, cm._menu_template, args=_name))
		cl_menu.add(MenuItem(_("Rename Layout…"), cm._menu_rename))
		cl_menu.add(MenuItem(_("Delete Slot"), cm._menu_delete_slot))
		cl_menu.add(MenuItem(_("New Slot"), cm._menu_new_slot))

	# Corner layout menu: opened by the corner layout/edit button (drawn after
	# the panel button by the TopPanel normally; by the custom engine while in
	# custom mode, where the panel button is hidden). Mirrors the View Switcher
	# options (same labels as its tooltips), plus the custom-layout edit toggle.
	layout_menu = Menu(tauon, 200, show_icons=True)
	tauon.layout_menu = layout_menu

	def _layout_menu_pick(name: str) -> Callable[[], None]:
		def cb() -> None:
			# Same dispatch as the View Switcher buttons: any option other than
			# Custom Layout exits custom mode first.
			if name != "custom_layout" and gui.custom_mode:
				tauon.custom.exit_mode()
			getattr(tauon.view_box, name)(True)
		return cb

	def _layout_menu_icon_colour(name: str, colour: ColourRGBA) -> Callable[[], ColourRGBA | None]:
		# Hold the icon's accent colour while its layout is the active view
		# (heart-icon pattern) — same detection the View Switcher buttons use:
		# test(False) plus the custom-mode override (in custom mode only the
		# Custom Layout entry counts as on).
		def cb() -> ColourRGBA | None:
			on = getattr(tauon.view_box, name)(False) and not gui.custom_mode
			if on:
				if colours.lm:
					return ColourRGBA(63, 63, 63, 255)  # match ViewBox light-mode "high"
				return colour
			return None
		return cb

	for _vb_name, _vb_label, _vb_icon, _vb_xoff, _vb_colour in (
		("side_normal", _("Tracks + Art"), "tracks+side-menu.png", 0, ColourRGBA(76, 183, 229, 255)),
		("side_reversed", _("Tracks + Art (Reversed)"), "tracks+side-menu-reversed.png", 0, ColourRGBA(76, 183, 229, 255)),
		("gallery1", _("Tracks + Gallery"), "gallery1-menu.png", 0, ColourRGBA(76, 137, 229, 255)),
		("tracks", _("Tracks"), "tracks-menu.png", 1, ColourRGBA(76, 229, 229, 255)),
		("lyrics", _("Art + Lyrics"), "lyrics-menu.png", 1, ColourRGBA(107, 76, 229, 255)),
		("radio", _("Radio"), "radio-view-menu.png", 1, ColourRGBA(92, 86, 255, 255)),
	):
		_vb_menu_icon = MenuIcon(asset_loader(bag, bag.loaded_asset_dc, _vb_icon, True))
		_vb_menu_icon.colour = _vb_colour
		_vb_menu_icon.colour_callback = _layout_menu_icon_colour(_vb_name, _vb_colour)
		_vb_menu_icon.xoff = _vb_xoff
		_vb_menu_icon.yoff = 1
		layout_menu.add(MenuItem(_vb_label, _layout_menu_pick(_vb_name), icon=_vb_menu_icon))

	# Custom layout slots: one entry per slot (any number), named by the slot
	# (rename / template loads set names; unnamed empty slots read "Empty
	# Slot"), same glyph with a cycled per-slot accent. Picking the
	# already-active slot toggles custom mode off; picking another switches to
	# it. The slot section is rebuilt (tauon.rebuild_layout_menu) whenever
	# slots are created, deleted or renamed.
	def _layout_menu_pick_custom(slot: int) -> Callable[[], None]:
		def cb() -> None:
			if gui.custom_mode and tauon.custom.active_slot == slot:
				tauon.custom.exit_mode()
			else:
				tauon.custom.enter(slot)
		return cb

	def _layout_menu_custom_colour(slot: int, colour: ColourRGBA) -> Callable[[], ColourRGBA | None]:
		def cb() -> ColourRGBA | None:
			if gui.custom_mode and tauon.custom.active_slot == slot:
				if colours.lm:
					return ColourRGBA(63, 63, 63, 255)
				return colour
			return None
		return cb

	def _edit_mode_deco() -> Decorator:
		# The menu only opens while not in edit mode (the corner button exits edit
		# mode directly), so this entry always reads "Enter Edit Mode".
		text = _("Exit Edit Mode") if gui.custom_edit else _("Enter Edit Mode")
		return Decorator(colours.menu_text, colours.menu_background, text)

	_layout_menu_head = list(layout_menu.items)  # the fixed preset entries above
	_slot_accents = (
		ColourRGBA(170, 225, 90, 255),   # lime
		ColourRGBA(230, 85, 210, 255),   # magenta
		ColourRGBA(255, 160, 70, 255),   # orange
		ColourRGBA(85, 205, 235, 255),   # cyan
		ColourRGBA(255, 110, 120, 255),  # coral
		ColourRGBA(235, 200, 80, 255),   # gold
		ColourRGBA(165, 105, 255, 255),  # violet
		ColourRGBA(100, 145, 255, 255),  # blue
	)

	def rebuild_layout_menu() -> None:
		layout_menu.items[:] = _layout_menu_head
		for _slot in range(len(tauon.custom.slots)):
			_slot_colour = _slot_accents[_slot % len(_slot_accents)]
			_slot_icon = MenuIcon(asset_loader(bag, bag.loaded_asset_dc, "custom-layout-menu.png", True))
			_slot_icon.colour = _slot_colour
			_slot_icon.colour_callback = _layout_menu_custom_colour(_slot, _slot_colour)
			_slot_icon.xoff = 1
			_slot_icon.yoff = 1
			layout_menu.add(MenuItem(
				tauon.custom.slot_title(_slot), _layout_menu_pick_custom(_slot), icon=_slot_icon))
		layout_menu.br()
		layout_menu.add(MenuItem(_("Enter Edit Mode"), tauon.custom.toggle_edit, _edit_mode_deco,
			disable_test=lambda: not gui.custom_mode))

	tauon.rebuild_layout_menu = rebuild_layout_menu
	# Slot names/count are needed for the entries, so load the slots now
	# (cheap; also restores the last-active slot early).
	if not tauon.custom._loaded:
		tauon.custom.load_slots()
	rebuild_layout_menu()

	# Right-click menu for the Spectrogram widget: colour presets.
	spectrogram_menu = Menu(tauon, 150)
	tauon.spectrogram_menu = spectrogram_menu

	# Top-level menu items are invoked as func() with no arguments (MenuItem
	# ``args`` only applies to submenu items), so bind the preset index in a
	# closure per item.
	def _spectro_set_colour(index: int) -> Callable[[], None]:
		def cb() -> None:
			prefs.spectrogram_colour = index
			gui.request_frame()
		return cb

	def _spectro_preset_check(index: int) -> Callable[[], bool]:
		return lambda: prefs.spectrogram_colour == index

	for _i, _sp in enumerate(CL_SPECTRO_PRESETS):
		spectrogram_menu.add(MenuItem(
			_sp[0], _spectro_set_colour(_i), check_test=_spectro_preset_check(_i)))

	# Per-instance display options for Albumflow.
	albumflow_menu = Menu(tauon, 150)
	tauon.albumflow_menu = albumflow_menu
	albumflow_menu.add(MenuItem(
		_("Stacks"),
		AlbumflowWidget.menu_toggle_stacks,
		check_test=AlbumflowWidget.menu_stacks_value,
	))
	albumflow_menu.add(MenuItem(
		_("CD"),
		AlbumflowWidget.menu_set_cd,
		check_test=AlbumflowWidget.menu_cd_value,
	))
	albumflow_menu.add(MenuItem(
		_("Vinyl"),
		AlbumflowWidget.menu_set_vinyl,
		check_test=AlbumflowWidget.menu_vinyl_value,
	))

	# Right-click (background) menu for the Album Grid widget. The incrementor
	# callbacks are classmethods reading GridGalleryWidget.menu_target, which
	# the widget sets when it opens the menu.
	gallery_grid_menu = Menu(tauon, 190)
	tauon.gallery_grid_menu = gallery_grid_menu
	gallery_grid_menu.add_incrementor(
		_("Albums per row"),
		GridGalleryWidget.menu_per_row_value,
		GridGalleryWidget.menu_per_row_minus,
		GridGalleryWidget.menu_per_row_plus)
	gallery_grid_menu.add_incrementor(
		_("Spacing"),
		GridGalleryWidget.menu_spacing_value,
		GridGalleryWidget.menu_spacing_minus,
		GridGalleryWidget.menu_spacing_plus)
	gallery_grid_menu.add_incrementor(
		_("Row spacing"),
		GridGalleryWidget.menu_v_spacing_value,
		GridGalleryWidget.menu_v_spacing_minus,
		GridGalleryWidget.menu_v_spacing_plus)

	def _grid_titles_deco() -> Decorator:
		text = _("Hide Titles") if GridGalleryWidget.menu_titles_value() else _("Show Titles")
		return Decorator(colours.menu_text, colours.menu_background, text)

	gallery_grid_menu.add(MenuItem(_("Hide Titles"), GridGalleryWidget.menu_toggle_titles, _grid_titles_deco))

	# Right-click (background) menu for the gallery — the preset album view and
	# the Gallery: Classic widget (the Compact grid has its own menu). Holds the
	# gallery settings, moved here from Settings > View.
	gallery_settings_menu = Menu(tauon, 210)
	tauon.gallery_settings_menu = gallery_settings_menu

	def _gal_size_value(ref=None) -> int:
		return int(tauon.album_mode_art_size)

	def _gal_size_step(direction: int) -> Callable[..., None]:
		def cb(ref=None) -> None:
			new = min(400, max(70, int(tauon.album_mode_art_size) + 10 * direction))
			if new != tauon.album_mode_art_size:
				tauon.img_slide_update_gall(new)
				gui.request_frame()
		return cb

	gallery_settings_menu.add_incrementor(
		_("Thumbnail size"), _gal_size_value, _gal_size_step(-1), _gal_size_step(1))

	def _gal_toggle_titles(ref=None) -> None:
		tauon.toggle_galler_text()

	gallery_settings_menu.add(MenuItem(_("Show titles"), _gal_toggle_titles,
		check_test=lambda: gui.gallery_show_text))

	def _gal_toggle_center(ref=None) -> None:
		prefs.center_gallery_text ^= True
		gui.request_frame()

	gallery_settings_menu.add(MenuItem(_("Center title text"), _gal_toggle_center,
		check_test=lambda: prefs.center_gallery_text))

	def _gal_toggle_click(ref=None) -> None:
		tauon.toggle_gallery_click()

	gallery_settings_menu.add(MenuItem(_("Single click to play"), _gal_toggle_click,
		check_test=lambda: tauon.toggle_gallery_click(1)))

	def _gal_toggle_row_scroll(ref=None) -> None:
		prefs.gallery_row_scroll ^= True

	gallery_settings_menu.add(MenuItem(_("Scroll by row"), _gal_toggle_row_scroll,
		check_test=lambda: prefs.gallery_row_scroll))

	def _gal_toggle_combine(ref=None) -> None:
		tauon.toggle_gallery_combine()

	gallery_settings_menu.add(MenuItem(_("Combine multi-discs"), _gal_toggle_combine,
		check_test=lambda: tauon.toggle_gallery_combine(1)))

	# Mirror the shared gallery display toggles onto the Gallery: Compact menu.
	# These are global prefs (not per-instance), so the same callbacks apply.
	gallery_grid_menu.add(MenuItem(_("Center title text"), _gal_toggle_center,
		check_test=lambda: prefs.center_gallery_text))
	gallery_grid_menu.add(MenuItem(_("Single click to play"), _gal_toggle_click,
		check_test=lambda: tauon.toggle_gallery_click(1)))
	gallery_grid_menu.add(MenuItem(_("Scroll by row"), _gal_toggle_row_scroll,
		check_test=lambda: prefs.gallery_row_scroll))
	gallery_grid_menu.add(MenuItem(_("Combine multi-discs"), _gal_toggle_combine,
		check_test=lambda: tauon.toggle_gallery_combine(1)))

	def _gal_toggle_thin(ref=None) -> None:
		tauon.toggle_gallery_thin()

	gallery_settings_menu.add(MenuItem(_("Prefer thinner padding"), _gal_toggle_thin,
		check_test=lambda: tauon.toggle_gallery_thin(1),
		show_test=lambda ref=None: tauon.album_mode_art_size < 160))

	repeat_menu.add(MenuItem(_("Repeat OFF"), tauon.menu_repeat_off))
	repeat_menu.add(MenuItem(_("Repeat Track"), tauon.menu_set_repeat))
	repeat_menu.add(MenuItem(_("Repeat Album"), tauon.menu_album_repeat))
	repeat_menu.add(MenuItem(_("A/B Repeat"), tauon.menu_ab_repeat, tauon.menu_ab_repeat_deco))

	shuffle_menu.add(MenuItem(_("Shuffle Lockdown"), tauon.toggle_shuffle_layout))
	shuffle_menu.add(MenuItem(_("Shuffle Lockdown Albums"), tauon.toggle_shuffle_layout_albums))
	shuffle_menu.br()
	shuffle_menu.add(MenuItem(_("Shuffle OFF"), tauon.menu_shuffle_off))
	shuffle_menu.add(MenuItem(_("Shuffle Tracks"), tauon.menu_set_random))
	shuffle_menu.add(MenuItem(_("Random Albums"), tauon.menu_album_random))

	artist_info_menu.add(MenuItem(_("Close Panel"), tauon.artist_info_panel_close))

	gui.filter_icon.colour = ColourRGBA(43, 213, 255, 255)
	gui.filter_icon.xoff = 1

	gui.folder_icon.colour = ColourRGBA(244, 220, 66, 255)
	gui.info_icon.colour = ColourRGBA(61, 247, 163, 255)

	folder_tree_stem_menu.add(MenuItem(_("Open Folder"), tauon.open_folder_stem, pass_ref=True, icon=gui.folder_icon))
	folder_tree_menu.add(MenuItem(_("Open Folder"), tauon.menu_open_folder, pass_ref=True, pass_ref_deco=True, icon=gui.folder_icon, disable_test=tauon.menu_open_folder_disable_test))

	lightning_menu.add(MenuItem(_("Filter to New Playlist"), tauon.tag_to_new_playlist, pass_ref=True, icon=gui.filter_icon))
	folder_tree_menu.add(MenuItem(_("Filter to New Playlist"), tauon.folder_to_new_playlist_by_track_id, pass_ref=True, icon=gui.filter_icon))
	folder_tree_stem_menu.add(MenuItem(_("Filter to New Playlist"), tauon.stem_to_new_playlist, pass_ref=True, icon=gui.filter_icon))
	folder_tree_stem_menu.add(MenuItem(_("Rescan Folder"), tauon.re_import3, pass_ref=True))
	folder_tree_menu.add(MenuItem(_("Rescan Folder"), tauon.re_import4, pass_ref=True))
	lightning_menu.add(MenuItem(_("Move Playing Folder Here"), tauon.move_playing_folder_to_tag, pass_ref=True))

	folder_tree_stem_menu.add(MenuItem(_("Move Playing Folder Here"), tauon.move_playing_folder_to_tree_stem, pass_ref=True))

	folder_tree_stem_menu.br()

	folder_tree_stem_menu.add(MenuItem(_("Collapse All"), tauon.collapse_tree, tauon.collapse_tree_deco))

	folder_tree_stem_menu.add(MenuItem(_("lock"), tauon.lock_folder_tree, tauon.lock_folder_tree_deco))
	# folder_tree_menu.add("lock", lock_folder_tree, tauon.lock_folder_tree_deco)

	gallery_menu.add(MenuItem(_("Open Folder"), tauon.menu_open_folder, pass_ref=True, pass_ref_deco=True, icon=gui.folder_icon, disable_test=tauon.menu_open_folder_disable_test))
	gallery_menu.add(MenuItem(_("Show in Playlist"), tauon.show_in_playlist))
	gallery_menu.add_sub(_("Image…"), 160)
	gallery_menu.add(MenuItem(_("Add Album to Queue"), tauon.menu_add_album_to_queue, pass_ref=True))
	gallery_menu.add(MenuItem(_("Enqueue Album Next"), tauon.add_album_to_queue_fc, pass_ref=True))

	tauon.cancel_menu.add(MenuItem(_("Cancel"), tauon.cancel_import))

	def add_showcase_lyrics_items(menu: Menu) -> None:
		"""Add the shared lyrics items (fresh MenuItems per menu)"""
		menu.add(MenuItem(_("Search for Lyrics"), tauon.get_lyric_wiki, tauon.search_lyrics_deco, pass_ref=True, pass_ref_deco=True))
		menu.add(MenuItem(_("Search GuitarParty"), tauon.guitar_chords.search_guitarparty, pass_ref=True, show_test=tauon.chord_lyrics_paste_show_test))
		menu.add(MenuItem(_("Paste Chord Lyrics"), tauon.guitar_chords.paste_chord_lyrics, pass_ref=True, show_test=tauon.chord_lyrics_paste_show_test))
		menu.add(MenuItem(_("Clear Chord Lyrics"), tauon.guitar_chords.clear_chord_lyrics, pass_ref=True, show_test=tauon.chord_lyrics_paste_show_test))

		menu.add(MenuItem(_("Show Lyrics"), tauon.toggle_lyrics, tauon.toggle_lyrics_deco, pass_ref=True, pass_ref_deco=True,
			check_test=tauon.toggle_lyrics_check))
		menu.add(MenuItem(_("Prefer Synced"), tauon.toggle_synced_lyrics, tauon.toggle_synced_lyrics_deco, pass_ref=True, pass_ref_deco=True,
			check_test=lambda: tauon.prefs.prefer_synced_lyrics))
		menu.add(MenuItem(_("Lyrics Editor"), tauon.enter_timed_lyrics_edit, tauon.edit_lyrics_deco, pass_ref=True, pass_ref_deco=True))
		misc_sub = menu.sub_number
		menu.add_sub(_("Misc…"), 150)
		menu.add_to_sub(misc_sub, MenuItem(_("Substitute Search..."), tauon.show_sub_search, pass_ref=True))
		menu.add_to_sub(misc_sub, MenuItem(_("Paste Lyrics"), tauon.paste_lyrics, tauon.paste_lyrics_deco, pass_ref=True))
		menu.add_to_sub(misc_sub, MenuItem(_("Copy Lyrics"), tauon.copy_lyrics, tauon.copy_lyrics_deco, pass_ref=True, pass_ref_deco=True))
		menu.add_to_sub(misc_sub, MenuItem(_("Clear Lyrics"), tauon.clear_lyrics, tauon.clear_lyrics_deco, pass_ref=True, pass_ref_deco=True))
		menu.add_to_sub(misc_sub, MenuItem(_("Clear Synced Lyrics"), tauon.clear_synced_lyrics, pass_ref=True, disable_test=tauon.clear_synced_lyrics_disable_test, pass_ref_deco=True))
		menu.add_to_sub(misc_sub, MenuItem(_("Toggle art panel"), tauon.toggle_side_art, tauon.toggle_side_art_deco, show_test=tauon.lyrics_in_side_show))
		menu.add_to_sub(misc_sub, MenuItem(_("Toggle art position"),
			tauon.toggle_lyrics_panel_position, tauon.toggle_lyrics_panel_position_deco, show_test=tauon.lyrics_in_side_show))

	add_showcase_lyrics_items(showcase_menu)

	# Showcase view's own background menu: the lyrics items plus showcase
	# layout settings ("Show Showcase Visualiser" moved here from
	# Settings > View)
	showcase_view_menu = tauon.showcase_view_menu
	add_showcase_lyrics_items(showcase_view_menu)
	showcase_view_menu.br()
	showcase_view_menu.add(MenuItem(
		_("Enable Wide Mode"),
		tauon.toggle_showcase_wide_art,
		tauon.toggle_showcase_wide_art_deco,
		pass_ref=True,
		pass_ref_deco=True,
	))
	showcase_view_menu.add(MenuItem(
		_("Show Showcase Visualiser"), tauon.toggle_showcase_vis,
		check_test=lambda: tauon.toggle_showcase_vis(1),
		show_test=lambda _ref=None: prefs.backend == Backend.PHAZOR))

	center_info_menu.add(MenuItem(_("Search for Lyrics"), tauon.get_lyric_wiki, tauon.search_lyrics_deco, pass_ref=True, pass_ref_deco=True))
	center_info_menu.add(MenuItem(_("Show Lyrics"), tauon.toggle_lyrics, tauon.toggle_lyrics_deco, pass_ref=True, pass_ref_deco=True,
		check_test=tauon.toggle_lyrics_check))
	center_info_menu.add(MenuItem(_("Prefer Synced Lyrics"), tauon.toggle_synced_lyrics, tauon.toggle_synced_lyrics_deco, pass_ref=True, pass_ref_deco=True,
		check_test=lambda: tauon.prefs.prefer_synced_lyrics))
	center_info_menu.add(MenuItem(_("Lyrics Editor"), tauon.enter_timed_lyrics_edit, tauon.edit_lyrics_deco, pass_ref=True, pass_ref_deco=True))

	center_info_menu.add_sub(_("Misc…"), 150)
	center_info_menu.add_to_sub(0, MenuItem(_("Substitute Search..."), tauon.show_sub_search, pass_ref=True))
	center_info_menu.add_to_sub(0, MenuItem(_("Paste Lyrics"), tauon.paste_lyrics, tauon.paste_lyrics_deco, pass_ref=True))
	center_info_menu.add_to_sub(0, MenuItem(_("Copy Lyrics"), tauon.copy_lyrics, tauon.copy_lyrics_deco, pass_ref=True, pass_ref_deco=True))
	center_info_menu.add_to_sub(0, MenuItem(_("Clear Lyrics"), tauon.clear_lyrics, tauon.clear_lyrics_deco, pass_ref=True, pass_ref_deco=True))
	center_info_menu.add_to_sub(0, MenuItem(_("Clear Synced Lyrics"), tauon.clear_synced_lyrics, pass_ref=True, disable_test=tauon.clear_synced_lyrics_disable_test, pass_ref_deco=True))
	center_info_menu.add_to_sub(0, MenuItem(_("Toggle art panel"), tauon.toggle_side_art, tauon.toggle_side_art_deco, show_test=tauon.lyrics_in_side_show))
	center_info_menu.add_to_sub(0, MenuItem(_("Toggle art position"),
		tauon.toggle_lyrics_panel_position, tauon.toggle_lyrics_panel_position_deco, show_test=tauon.lyrics_in_side_show))

	picture_menu.add(MenuItem(_("Open Image"), tauon.open_image, tauon.open_image_deco, pass_ref=True, pass_ref_deco=True, disable_test=tauon.open_image_disable_test))
	# Next and previous pictures
	picture_menu.add(MenuItem(_("Next Image"), tauon.cycle_offset, tauon.cycle_image_deco, pass_ref=True, pass_ref_deco=True))
	#picture_menu.add(_("Previous"), tauon.cycle_offset_back, tauon.cycle_image_deco, pass_ref=True, pass_ref_deco=True)

	# Extract embedded artwork from file
	picture_menu.add(MenuItem(_("Extract Image"), tauon.save_embed_img, tauon.extract_image_deco, pass_ref=True, pass_ref_deco=True, disable_test=tauon.save_embed_img_disable_test))

	picture_menu.add(
		MenuItem(_("Delete Image File"), tauon.delete_track_image, tauon.delete_track_image_deco, pass_ref=True,
		pass_ref_deco=True, icon=gui.delete_icon))

	picture_menu.add(MenuItem(_("Quick-Fetch Cover Art"), tauon.download_art1_fire, tauon.dl_art_deco, pass_ref=True, pass_ref_deco=True, disable_test=tauon.download_art1_fire_disable_test))
	# picture_menu.add(_('Search Google for Images'), tauon.ser_gimage, tauon.search_image_deco, pass_ref=True, pass_ref_deco=True, show_test=tauon.toggle_gimage)

	# picture_menu.add(_('Toggle art box'), tauon.toggle_side_art, tauon.toggle_side_art_deco)

	picture_menu.add(MenuItem(_("Search for Lyrics"), tauon.get_lyric_wiki, tauon.search_lyrics_deco, pass_ref=True, pass_ref_deco=True))
	picture_menu.add(MenuItem(_("Show Lyrics"), tauon.toggle_lyrics, tauon.toggle_lyrics_deco, pass_ref=True, pass_ref_deco=True,
		check_test=tauon.toggle_lyrics_check))
	# ("Centered metadata side panel" switch moved here from Settings > View;
	# hidden in showcase where the side panel layout doesn't apply)
	picture_menu.add(MenuItem(
		_("Use Centered Style"), tauon.toggle_side_panel_layout,
		check_test=lambda: tauon.toggle_side_panel_layout(1),
		show_test=lambda _ref: not gui.showcase_mode))

	# ("Zoom album art to fit" switch moved here from Settings > View. This
	# menu also serves the custom layout Art Box widget.)
	def menu_toggle_zoom_art(ref=None) -> None:
		prefs.zoom_art ^= True
		tauon.album_art_gen.clear_cache()
		gui.request_frame()

	picture_menu.add(MenuItem(
		_("Zoom Art to Fit"), menu_toggle_zoom_art,
		check_test=lambda: prefs.zoom_art))

	picture_menu.br()
	picture_menu.add(MenuItem(
		_("Enable Wide Mode"),
		tauon.toggle_showcase_wide_art,
		tauon.toggle_showcase_wide_art_deco,
		pass_ref=True,
		pass_ref_deco=True,
		show_test=tauon.showcase_mode_show_test,
	))
	if t_visuals.milky_ready:
		picture_menu.add(MenuItem(_("MilkDrop Visualiser"), tauon.toggle_milky, pass_ref=True,
			check_test=lambda: prefs.milk))
	milky_menu.add(MenuItem(_("MilkDrop Visualiser"), tauon.toggle_milky, pass_ref=True,
		check_test=lambda: prefs.milk))
	milky_menu.add(MenuItem(_("Auto Cycle"), tauon.toggle_milky_auto, pass_ref=True,
		check_test=lambda: prefs.auto_milk))
	milky_menu.add(MenuItem(_("Cut Out"), tauon.toggle_milk_cut_out, pass_ref=True,
		check_test=lambda: prefs.milk_cut_out))
	milky_menu.add(MenuItem(_("Favorite This Preset"), tauon.toggle_milk_preset_favorite, pass_ref=True,
		check_test=tauon.milk_preset_is_favorite))
	milky_menu.add(MenuItem(_("Choose Preset"), tauon.open_milk_preset_chooser, pass_ref=True))
	milky_menu.add(MenuItem(
		_("Enable Wide Mode"),
		tauon.toggle_showcase_wide_art,
		tauon.toggle_showcase_wide_art_deco,
		pass_ref=True,
		pass_ref_deco=True,
		show_test=tauon.showcase_mode_show_test,
	))
	milky_menu.add(MenuItem(_("Open Preset Folder"), tauon.open_preset_folder, pass_ref=True))

	milky_menu.br()
	milky_menu.add(MenuItem(_("Show Lyrics"), tauon.toggle_lyrics, tauon.toggle_lyrics_deco, pass_ref=True, pass_ref_deco=True,
		check_test=tauon.toggle_lyrics_check))


	gallery_menu.add_to_sub(0, MenuItem(_("Next"), tauon.menu_cycle_offset, tauon.cycle_image_gal_deco, pass_ref=True, pass_ref_deco=True))
	gallery_menu.add_to_sub(0, MenuItem(_("Previous"), tauon.cycle_offset_back, tauon.cycle_image_gal_deco, pass_ref=True, pass_ref_deco=True))
	gallery_menu.add_to_sub(0, MenuItem(_("Open Image"), tauon.menu_open_image, tauon.menu_open_image_deco, pass_ref=True, pass_ref_deco=True, disable_test=tauon.menu_open_image_disable_test))
	gallery_menu.add_to_sub(0, MenuItem(_("Extract Image"), tauon.menu_save_embed_img, tauon.menu_extract_image_deco, pass_ref=True, pass_ref_deco=True, disable_test=tauon.menu_save_embed_img_disable_test))
	gallery_menu.add_to_sub(0, MenuItem(_("Delete Image <combined>"), tauon.menu_delete_track_image, tauon.menu_delete_track_image_deco, pass_ref=True, pass_ref_deco=True)) #, icon=delete_icon)
	gallery_menu.add_to_sub(0, MenuItem(_("Quick-Fetch Cover Art"), tauon.menu_download_art1_fire, tauon.menu_dl_art_deco, pass_ref=True, pass_ref_deco=True, disable_test=tauon.menu_download_art1_fire_disable_test))
	# playlist_menu.add('Paste', append_here, paste_deco)

	tab_menu.add(MenuItem(_("Rename"), tauon.rename_playlist, pass_ref=True, hint="Ctrl+R"))
	tab_menu.add(MenuItem(_("Pin"), tauon.pin_playlist_toggle, tauon.pl_pin_deco, pass_ref=True, pass_ref_deco=True))

	tauon.radio_tab_menu.add(MenuItem(_("Rename"), tauon.rename_playlist, pass_ref=True, hint="Ctrl+R"))

	lock_asset = asset_loader(bag, bag.loaded_asset_dc, "lock.png", True)
	lock_icon = MenuIcon(lock_asset)
	lock_icon.base_asset_mod = asset_loader(bag, bag.loaded_asset_dc, "unlock.png", True)
	lock_icon.colour = ColourRGBA(240, 190, 10, 255)
	lock_icon.colour_callback = tauon.lock_colour_callback
	lock_icon.xoff = 4
	lock_icon.yoff = -1

	tab_menu.add(MenuItem(_("Lock"), tauon.lock_playlist_toggle, tauon.pl_lock_deco,
		pass_ref=True, pass_ref_deco=True, icon=lock_icon, show_test=inp.test_shift))

	# Clear playlist
	tab_menu.add(MenuItem(_("Clear"), tauon.clear_playlist, pass_ref=True, disable_test=tauon.test_pl_tab_locked, pass_ref_deco=True))

	gui.delete_icon.xoff = 3
	gui.delete_icon.colour = ColourRGBA(249, 70, 70, 255)

	tab_menu.add(MenuItem(_("Delete"),
		pctl.delete_playlist_force, pass_ref=True, hint="Ctrl+W", icon=gui.delete_icon, disable_test=tauon.test_pl_tab_locked, pass_ref_deco=True))
	tauon.radio_tab_menu.add(MenuItem(_("Delete"),
		pctl.delete_playlist_force, pass_ref=True, hint="Ctrl+W", icon=gui.delete_icon, disable_test=tauon.test_pl_tab_locked, pass_ref_deco=True))

	service_asset = asset_loader(bag, bag.loaded_asset_dc, "playlist.png", True)
	jell_icon = MenuIcon(service_asset)
	jell_icon.colour = ColourRGBA(190, 100, 210, 255)
	jell_icon.xoff = 5
	jell_icon.yoff = 2

	tab_menu.br()

	extra_tab_menu.add(MenuItem(_("New Playlist"), tauon.new_playlist, icon=gui.add_icon))

	tab_menu.add(MenuItem(_("Upload"),
		tauon.upload_jellyfin_playlist, pass_ref=True, pass_ref_deco=True, icon=jell_icon, show_test=tauon.jellyfin_show_test))

	tab_menu.add(MenuItem(_("Regenerate"), tauon.regen_playlist_async, tauon.regenerate_deco, pass_ref=True, pass_ref_deco=True, hint="Alt+R"))
	tab_menu.add_sub(_("Generate…"), 150)
	tab_menu.add(MenuItem(_("Edit Generator..."), tauon.edit_generator_box, pass_ref=True))
	tab_menu.add_sub(_("Sort…"), 170)
	extra_tab_menu.add_sub(_("From Current…"), 133)
	# tab_menu.add(_("Sort by Filepath"), standard_sort, pass_ref=True, disable_test=test_pl_tab_locked, pass_ref_deco=True)
	# tab_menu.add(_("Sort Track Numbers"), tauon.sort_track_2, pass_ref=True)
	# tab_menu.add(_("Sort Year per Artist"), year_sort, pass_ref=True)

	tab_menu.add_to_sub(1, MenuItem(_("Sort by Imported Tracks"), tauon.imported_sort, pass_ref=True))
	tab_menu.add_to_sub(1, MenuItem(_("Sort by Imported Folders"), tauon.imported_sort_folders, pass_ref=True))
	tab_menu.add_to_sub(1, MenuItem(_("Sort by Filepath"), tauon.standard_sort, pass_ref=True))
	tab_menu.add_to_sub(1, MenuItem(_("Sort Track Numbers"), tauon.sort_track_2, pass_ref=True))
	tab_menu.add_to_sub(1, MenuItem(_("Sort Year per Artist"), tauon.year_sort, pass_ref=True))
	tab_menu.add_to_sub(1, MenuItem(_("Make Playlist Auto-Sorting"), tauon.make_auto_sorting, pass_ref=True))

	tab_menu.br()

	tab_menu.add(MenuItem(_("Rescan Folder"), pctl.re_import2, tauon.rescan_deco, pass_ref=True, pass_ref_deco=True))

	tab_menu.add(MenuItem(_("Paste"), tauon.s_append, tauon.paste_deco, pass_ref=True))
	tab_menu.add(MenuItem(_("Append Playing"), tauon.append_current_playing, tauon.append_deco, pass_ref=True))
	tab_menu.br()

	# tab_menu.add("Sort By Filepath", tauon.sort_path_pl, pass_ref=True)

	tab_menu.add(MenuItem(_("Import/Export…"), tauon.export_playlist_box.activate, pass_ref=True))

	tab_menu.add(MenuItem(_("Toggle Grouping"), tauon.pl_toggle_playlist_break, pass_ref=True))
	tab_menu.add_sub(_("Misc…"), 175)
	tab_menu.add_to_sub(2, MenuItem(_("Export Playlist Stats"), tauon.export_stats, pass_ref=True))
	tab_menu.add_to_sub(2, MenuItem(_("Export Albums CSV"), tauon.export_playlist_albums, pass_ref=True))
	tab_menu.add_to_sub(2, MenuItem(_("Transcode All"), tauon.convert_playlist, pass_ref=True))
	tab_menu.add_to_sub(2, MenuItem(_("Rescan Tags"), tauon.rescan_tags, pass_ref=True))
	# tab_menu.add_to_sub(_('Forget Import Folder'), 2, tauon.forget_pl_import_folder, rescan_deco, pass_ref=True, pass_ref_deco=True)
	# tab_menu.add_to_sub(_('Re-Import Last Folder'), 1, tauon.re_import, pass_ref=True)
	# tab_menu.add_to_sub(_('Quick Export XSPF'), 2, tauon.export_xspf, pass_ref=True)
	# tab_menu.add_to_sub(_('Quick Export M3U'), 2, tauon.export_m3u, pass_ref=True)
	tab_menu.add_to_sub(2, MenuItem(_("Engage Gallery Quick Add"), tauon.start_quick_add, pass_ref=True))
	tab_menu.add_to_sub(2, MenuItem(_("Set as Sync Playlist"), tauon.set_sync_playlist, tauon.sync_playlist_deco, pass_ref_deco=True, pass_ref=True))
	tab_menu.add_to_sub(2, MenuItem(_("Set as Downloads Playlist"), tauon.set_download_playlist, tauon.set_download_deco, pass_ref_deco=True, pass_ref=True))
	tab_menu.add_to_sub(2, MenuItem(_("Set podcast mode"), tauon.set_podcast_playlist, tauon.set_podcast_deco, pass_ref_deco=True, pass_ref=True))
	tab_menu.add_to_sub(2, MenuItem(_("Remove Duplicates"), tauon.remove_duplicates, pass_ref=True))

	# tab_menu.add_to_sub("Empty Playlist", 0, new_playlist)

	tab_menu.add_to_sub(0, MenuItem(_("Top Played Tracks"), tauon.gen_top_100, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("Top Played Tracks"), tauon.gen_top_100, pass_ref=True))

	tab_menu.add_to_sub(0, MenuItem(_("Top Played Albums"), tauon.gen_folder_top, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("Top Played Albums"), tauon.gen_folder_top, pass_ref=True))

	tab_menu.add_to_sub(0, MenuItem(_("Top Rated Tracks"), tauon.gen_top_rating, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("Top Rated Tracks"), tauon.gen_top_rating, pass_ref=True))

	tab_menu.add_to_sub(0, MenuItem(_("Top Rated Albums"), tauon.gen_folder_top_rating, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("Top Rated Albums"), tauon.gen_folder_top_rating, pass_ref=True))

	tab_menu.add_to_sub(0, MenuItem(_("File Modified"),tauon. gen_last_modified, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("File Modified"), tauon.gen_last_modified, pass_ref=True))

	# tab_menu.add_to_sub(_("File Path"), 0, stauon.tandard_sort, pass_ref=True)
	# extra_tab_menu.add_to_sub(_("File Path"), 0, tauon.standard_sort, pass_ref=True)

	tab_menu.add_to_sub(0, MenuItem(_("Longest Tracks"), tauon.gen_sort_len, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("Longest Tracks"), tauon.gen_sort_len, pass_ref=True))

	tab_menu.add_to_sub(0, MenuItem(_("Longest Albums"), tauon.gen_folder_duration, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("Longest Albums"), tauon.gen_folder_duration, pass_ref=True))

	tab_menu.add_to_sub(0, MenuItem(_("Year by Oldest"), tauon.gen_sort_date, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("Year by Oldest"), tauon.gen_sort_date, pass_ref=True))

	tab_menu.add_to_sub(0, MenuItem(_("Year by Latest"), tauon.gen_sort_date_new, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("Year by Latest"), tauon.gen_sort_date_new, pass_ref=True))

	# tab_menu.add_to_sub(_("Year by Artist"), 0, tauon.year_sort, pass_ref=True)
	# extra_tab_menu.add_to_sub(_("Year by Artist"), 0, tauon.year_sort, pass_ref=True)

	tab_menu.add_to_sub(0, MenuItem(_("Shuffled Tracks"), tauon.gen_500_random, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("Shuffled Tracks"), tauon.gen_500_random, pass_ref=True))

	tab_menu.add_to_sub(0, MenuItem(_("Shuffled Albums"), tauon.gen_folder_shuffle, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("Shuffled Albums"), tauon.gen_folder_shuffle, pass_ref=True))

	tab_menu.add_to_sub(0, MenuItem(_("Lucky Random"), tauon.gen_best_random, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("Lucky Random"), tauon.gen_best_random, pass_ref=True))

	tab_menu.add_to_sub(0, MenuItem(_("Reverse Tracks"), tauon.gen_reverse, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("Reverse Tracks"), tauon.gen_reverse, pass_ref=True))

	tab_menu.add_to_sub(0, MenuItem(_("Reverse Albums"), tauon.gen_folder_reverse, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("Reverse Albums"), tauon.gen_folder_reverse, pass_ref=True))

	tab_menu.add_to_sub(0, MenuItem(_("Duplicate"), tauon.gen_dupe, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("Duplicate"), tauon.gen_dupe, pass_ref=True))

	# tab_menu.add_to_sub("Filepath", 1, tauon.gen_sort_path, pass_ref=True)
	# tab_menu.add_to_sub("Artist → gui.abc", 0, tauon.gen_sort_artist, pass_ref=True)
	# tab_menu.add_to_sub("Album → gui.abc", 0, tauon.gen_sort_album, pass_ref=True)
	tab_menu.add_to_sub(0, MenuItem(_("Loved"), tauon.gen_love, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("Loved"), tauon.gen_love, pass_ref=True))
	tab_menu.add_to_sub(0, MenuItem(_("Has Comment"), tauon.gen_comment, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("Has Comment"), tauon.gen_comment, pass_ref=True))
	tab_menu.add_to_sub(0, MenuItem(_("Has Lyrics"), tauon.gen_lyrics, pass_ref=True))
	extra_tab_menu.add_to_sub(0, MenuItem(_("Has Lyrics"), tauon.gen_lyrics, pass_ref=True))

	playlist_menu.add(MenuItem(_("Paste"), tauon.paste, tauon.paste_deco))

	track_menu.add(MenuItem(_("Open Folder"), tauon.menu_open_folder, pass_ref=True, pass_ref_deco=True, icon=gui.folder_icon, disable_test=tauon.menu_open_folder_disable_test))
	track_menu.add(MenuItem(_("Track Info…"), tauon.activate_track_box, pass_ref=True, icon=gui.info_icon))

	gui.heartx_icon.colour = ColourRGBA(55, 55, 55, 255)
	gui.heartx_icon.xoff = 1
	gui.heartx_icon.yoff = 0
	gui.heartx_icon.colour_callback = tauon.heart_xmenu_colour

	# Mark track as 'liked'
	track_menu.add(MenuItem(_("Love"), tauon.love_index, tauon.love_decox, pass_ref=True, pass_ref_deco=True, icon=gui.heartx_icon))

	track_menu.add(MenuItem(_("Add to Queue"), tauon.add_to_queue, pass_ref=True, hint="MB3"))

	track_menu.add(MenuItem(_("↳ After Current Track"), tauon.add_to_queue_next, pass_ref=True, show_test=inp.test_shift))

	track_menu.add(MenuItem(_("Show in Gallery"), tauon.menu_show_in_gal, pass_ref=True, show_test=tauon.test_show))

	track_menu.add_sub(_("Meta…"), 160)

	track_menu.br()
	# track_menu.add('Cut', s_cut, pass_ref=False)
	# track_menu.add('Remove', del_selected)
	track_menu.add(MenuItem(_("Copy"), tauon.s_copy, pass_ref=False))

	# track_menu.add(_('Paste + Transfer Folder'), tauon.lightning_paste, pass_ref=False, show_test=tauon.lightning_move_test)

	track_menu.add(MenuItem(_("Paste"), tauon.menu_paste, tauon.paste_deco, pass_ref=True))

	track_menu.add(MenuItem(_("Delete Track File"), tauon.delete_track, pass_ref=True, icon=gui.delete_icon, show_test=inp.test_shift))

	track_menu.br()

	# gui.rename_tracks_icon.colour = ColourRGBA(244, 241, 66, 255)
	# gui.rename_tracks_icon.colour = ColourRGBA(204, 255, 66, 255)
	gui.rename_tracks_icon.colour = ColourRGBA(204, 100, 205, 255)
	gui.rename_tracks_icon.xoff = 1
	track_menu.add_to_sub(0, MenuItem(_("Rename Tracks…"), tauon.rename_track_box.activate, tauon.rename_tracks_deco, pass_ref=True,
		pass_ref_deco=True, icon=gui.rename_tracks_icon, disable_test=tauon.rename_track_box.disable_test))

	track_menu.add_to_sub(0, MenuItem(_("Edit fields…"), tauon.activate_trans_editor))

	gui.mod_folder_icon.colour = ColourRGBA(229, 98, 98, 255)
	track_menu.add_to_sub(0, MenuItem(_("Modify Folder…"), tauon.rename_folders, pass_ref=True, pass_ref_deco=True, icon=gui.mod_folder_icon, disable_test=tauon.rename_folders_disable_test))


	# track_menu.add_to_sub("Reset Track Play Count", 0, tauon.reset_play_count, pass_ref=True)

	# track_menu.add('Reload Metadata', tauon.reload_metadata, pass_ref=True)
	track_menu.add_to_sub(0, MenuItem(_("Rescan Tags"), tauon.menu_reload_metadata, pass_ref=True))

	mbp_icon = MenuIcon(asset_loader(bag, bag.loaded_asset_dc, "mbp-g.png"))
	mbp_icon.base_asset = asset_loader(bag, bag.loaded_asset_dc, "mbp-gs.png")

	mbp_icon.xoff = 2
	mbp_icon.yoff = -1

	if gui.scale == 1.25:
		mbp_icon.yoff = 0

	edit_icon = None
	if prefs.tag_editor_name == "Picard":
		edit_icon = mbp_icon

	track_menu.add_to_sub(0, MenuItem(_("Edit with"), tauon.launch_editor, pass_ref=True, pass_ref_deco=True, icon=edit_icon, render_func=tauon.edit_deco, disable_test=tauon.launch_editor_disable_test))
	track_menu.add_to_sub(0, MenuItem(_("Lyrics..."), tauon.show_lyrics_menu, pass_ref=True))
	track_menu.add_to_sub(0, MenuItem(_("Fix Mojibake"), tauon.intel_moji, pass_ref=True))
	track_menu.add_to_sub(0, MenuItem(_("Look Out the Window"), tauon.dream_room.toggle))
	# track_menu.add_to_sub("Copy Playlist", 1, transfer, pass_ref=True, args=[1, 3])

	folder_menu.add(MenuItem(_("Open Folder"), tauon.menu_open_folder, pass_ref=True, pass_ref_deco=True, icon=gui.folder_icon, disable_test=tauon.menu_open_folder_disable_test))

	folder_menu.add(MenuItem(_("Modify Folder…"), tauon.rename_folders, pass_ref=True, pass_ref_deco=True, icon=gui.mod_folder_icon, disable_test=tauon.rename_folders_disable_test))
	folder_tree_menu.add(MenuItem(_("Modify Folder…"), tauon.rename_folders, pass_ref=True, pass_ref_deco=True, icon=gui.mod_folder_icon, disable_test=tauon.rename_folders_disable_test))
	# folder_menu.add(_("Add Album to Queue"), tauon.add_album_to_queue, pass_ref=True)
	folder_menu.add(MenuItem(_("Add Album to Queue"), tauon.menu_add_album_to_queue, pass_ref=True))
	folder_menu.add(MenuItem(_("Enqueue Album Next"), tauon.add_album_to_queue_fc, pass_ref=True))

	gallery_menu.add(MenuItem(_("Modify Folder…"), tauon.rename_folders, pass_ref=True, pass_ref_deco=True, icon=gui.mod_folder_icon, disable_test=tauon.rename_folders_disable_test))

	folder_menu.add(MenuItem(_("Rename Tracks…"), tauon.rename_track_box.activate, tauon.rename_tracks_deco,
		pass_ref=True, pass_ref_deco=True, icon=gui.rename_tracks_icon, disable_test=tauon.rename_track_box.disable_test))
	folder_tree_menu.add(MenuItem(_("Rename Tracks…"), tauon.rename_track_box.activate, pass_ref=True, pass_ref_deco=True, icon=gui.rename_tracks_icon, disable_test=tauon.rename_track_box.disable_test))

	if not tauon.snap_mode:
		folder_menu.add(MenuItem(_("Edit with"), tauon.launch_editor_selection, pass_ref=True,
			pass_ref_deco=True, icon=edit_icon, render_func=tauon.edit_deco, disable_test=tauon.launch_editor_selection_disable_test))

	folder_tree_menu.add(MenuItem(_("Add Album to Queue"), tauon.menu_add_album_to_queue, pass_ref=True))
	folder_tree_menu.add(MenuItem(_("Enqueue Album Next"), tauon.add_album_to_queue_fc, pass_ref=True))

	folder_tree_menu.br()
	folder_tree_menu.add(MenuItem(_("Collapse All"), tauon.collapse_tree, tauon.collapse_tree_deco))
	folder_tree_menu.add(MenuItem(_("lock"), tauon.lock_folder_tree, tauon.lock_folder_tree_deco))

	# selection_menu.br()

	gui.transcode_icon.colour = ColourRGBA(239, 74, 157, 255)
	folder_menu.add(MenuItem(_("Rescan Tags"), tauon.menu_reload_metadata, pass_ref=True))
	folder_menu.add(MenuItem(_("Edit fields…"), tauon.activate_trans_editor))
	folder_menu.add(MenuItem(_("Vacuum Playtimes"), tauon.vacuum_playtimes, pass_ref=True, show_test=inp.test_shift))
	folder_menu.add(MenuItem(_("Transcode Folder"), tauon.convert_folder, tauon.transcode_deco, pass_ref=True, icon=gui.transcode_icon))
	gallery_menu.add(MenuItem(_("Transcode Folder"), tauon.convert_folder, tauon.transcode_deco, pass_ref=True, icon=gui.transcode_icon))
	folder_menu.br()

	# Copy album title text to clipboard
	folder_menu.add(MenuItem(_('Copy "Artist - Album"'), tauon.clip_title, pass_ref=True))

	# Copy artist name text to clipboard
	# folder_menu.add(_('Copy "Artist"'), clip_ar, pass_ref=True)

	selection_menu.add(MenuItem(_("Add to queue"), tauon.add_selected_to_queue_multi, tauon.selection_queue_deco))
	selection_menu.br()
	selection_menu.add(MenuItem(_("Rescan Tags"), tauon.reload_metadata_selection))
	selection_menu.add(MenuItem(_("Edit fields…"), tauon.activate_trans_editor))
	selection_menu.add(MenuItem(_("Edit with "), tauon.launch_editor_selection, pass_ref=True, pass_ref_deco=True, icon=edit_icon, render_func=tauon.edit_deco, disable_test=tauon.launch_editor_selection_disable_test))

	selection_menu.br()
	folder_menu.br()

	# It's complicated
	# folder_menu.add(_('Copy Folder From Library'), lightning_copy)

	selection_menu.add(MenuItem(_("Copy"), tauon.s_copy))
	selection_menu.add(MenuItem(_("Cut"), tauon.s_cut))
	selection_menu.add(MenuItem(_("Remove"), tauon.del_selected))
	selection_menu.add(MenuItem(_("Delete Files"), tauon.force_del_selected, show_test=inp.test_shift, icon=gui.delete_icon))

	folder_menu.add(MenuItem(_("Copy"), tauon.s_copy))
	gallery_menu.add(MenuItem(_("Copy"), tauon.s_copy))
	# folder_menu.add(_('Cut'), s_cut)
	# folder_menu.add(_('Paste + Transfer Folder'), tauon.lightning_paste, pass_ref=False, show_test=tauon.lightning_move_test)
	# gallery_menu.add(_('Paste + Transfer Folder'), tauon.lightning_paste, pass_ref=False, show_test=tauon.lightning_move_test)
	folder_menu.add(MenuItem(_("Remove"), tauon.del_selected))
	gallery_menu.add(MenuItem(_("Remove"), tauon.del_selected))

	track_menu.add(MenuItem(_("Search Artist on Wikipedia"), tauon.ser_wiki, pass_ref=True, show_test=tauon.show_wiki_menu_item))
	track_menu.add(MenuItem(_("Search Track on Genius"), tauon.ser_gen, pass_ref=True, show_test=tauon.show_gen_menu_item))

	son_icon = MenuIcon(asset_loader(bag, bag.loaded_asset_dc, "sonemic-g.png"))
	son_icon.base_asset = asset_loader(bag, bag.loaded_asset_dc, "sonemic-gs.png")

	son_icon.xoff = 1
	track_menu.add(MenuItem(_("Search Artist on Sonemic"), tauon.ser_rym, pass_ref=True, icon=son_icon, show_test=tauon.show_rym_menu_item))

	band_icon = MenuIcon(asset_loader(bag, bag.loaded_asset_dc, "band.png", True))
	band_icon.xoff = 0
	band_icon.yoff = 1
	band_icon.colour = ColourRGBA(96, 147, 158, 255)

	track_menu.add(MenuItem(_("Search Artist on Bandcamp"), tauon.ser_band, pass_ref=True, icon=band_icon, show_test=tauon.show_band_menu_item))

	# Copy metadata to clipboard
	# track_menu.add(_('Copy "Artist - Album"'), tauon.clip_aar_al, pass_ref=True)
	track_menu.add(MenuItem(_('Copy "Artist - Track"'), tauon.clip_ar_tr, pass_ref=True))
	track_menu.add(MenuItem(_("Copy TIDAL Album URL"), tauon.tidal_copy_album, show_test=tauon.is_tidal_track, pass_ref=True))

	track_menu.br()
	track_menu.add(MenuItem(_("Transcode Folder"), tauon.convert_folder, tauon.transcode_deco, pass_ref=True, icon=gui.transcode_icon))

	# Layout submenu: the columns toggles plus the tracklist settings, moved
	# here from Settings > Tracklist. (ViewBox.col stays as the shared columns
	# implementation — the toggle-columns keybind uses it too.)
	def menu_toggle_columns(ref=None) -> None:
		tauon.view_box.col(True)

	def _columns_off_test(ref=None) -> bool:
		return not gui.set_mode

	def _columns_on_test(ref=None) -> bool:
		return gui.set_mode

	def menu_toggle_set_bar(ref=None) -> None:
		gui.set_bar ^= True
		gui.update_layout = True
		gui.request_tracklist_redraw()

	def _bar_deco() -> Decorator:
		text = _("Hide Bar") if gui.set_bar else _("Show Bar")
		return Decorator(colours.menu_text, colours.menu_background, text)

	def _tl_toggle_left_align() -> None:
		prefs.row_title_format = 1 if prefs.row_title_format == 2 else 2
		gui.request_frame()
		gui.request_tracklist_redraw()

	def _tl_toggle_genre() -> None:
		prefs.row_title_genre ^= True
		gui.request_frame()
		gui.request_tracklist_redraw()

	def _tl_toggle_scrollbar_left() -> None:
		prefs.tracklist_scrollbar_left ^= True
		gui.request_frame()
		gui.request_tracklist_redraw()

	def _tl_stepper(attr: str, lo: int, hi: int) -> tuple[Callable, Callable, Callable]:
		def value(ref=None) -> int:
			return getattr(prefs, attr)
		def step(direction: int) -> Callable[..., None]:
			def cb(ref=None) -> None:
				new = min(hi, max(lo, getattr(prefs, attr) + direction))
				if new != getattr(prefs, attr):
					setattr(prefs, attr, new)
					gui.update_layout = True
					gui.request_tracklist_redraw()
			return cb
		return value, step(-1), step(1)

	def add_layout_sub(menu: Menu) -> None:
		"""Append the tracklist Layout submenu to ``menu`` (fresh MenuItems per
		menu; the callbacks/decos are shared closures above)."""
		menu.add_sub(_("Layout"), 190)
		sub = menu.sub_number - 1
		menu.add_to_sub(sub, MenuItem(_("Show Columns"), menu_toggle_columns, show_test=_columns_off_test))
		menu.add_to_sub(sub, MenuItem(_("Hide Columns"), menu_toggle_columns, show_test=_columns_on_test))
		menu.add_to_sub(sub, MenuItem(_("Hide Bar"), menu_toggle_set_bar, _bar_deco,
			no_exit=True, disable_test=lambda: not gui.set_mode))

		def toggle_item(label: str, func: Callable, get_state: Callable[[], bool | None]) -> None:
			def cb(ref=None) -> None:
				func()
			# no_exit: checkbox-style toggles keep the submenu open (the state
			# box flips in place), like the custom-layout Layout… submenu toggles.
			menu.add_to_sub(sub, MenuItem(label, cb, check_test=get_state, no_exit=True))

		toggle_item(_("Loves"), tauon.heart_toggle, lambda: tauon.heart_toggle(1))
		toggle_item(_("Track ratings"), tauon.rating_toggle, lambda: tauon.rating_toggle(1))
		toggle_item(_("Album ratings"), tauon.album_rating_toggle, lambda: tauon.album_rating_toggle(1))
		toggle_item(_("Star hints"), tauon.star_toggle, lambda: tauon.star_toggle(1))
		toggle_item(_("Playcount lines"), tauon.star_line_toggle, lambda: tauon.star_line_toggle(1))
		toggle_item(_("Left align"), _tl_toggle_left_align, lambda: prefs.row_title_format == 2)
		toggle_item(_("Genre"), _tl_toggle_genre, lambda: prefs.row_title_genre)
		toggle_item(_("Year"), tauon.toggle_append_date, lambda: tauon.toggle_append_date(1))
		toggle_item(_("Duration"), tauon.toggle_append_total_time, lambda: tauon.toggle_append_total_time(1))
		toggle_item(_("Scroll bar on left"), _tl_toggle_scrollbar_left, lambda: prefs.tracklist_scrollbar_left)

		menu.add_incrementor_to_sub(sub, _("Font size"), *_tl_stepper("playlist_font_size", 12, 17))
		menu.add_incrementor_to_sub(sub, _("Row height"), *_tl_stepper("playlist_row_height", 15, 45))
		menu.add_incrementor_to_sub(sub, _("Text baseline"), *_tl_stepper("tracklist_y_text_offset", -10, 10))

		menu.add_to_sub(sub, MenuItem(_("Thin default"), lambda: tauon.pref_box.small_preset()))
		menu.add_to_sub(sub, MenuItem(_("Thick default"), lambda: tauon.pref_box.large_preset()))

		# Optional search-provider items in the track menu, moved here from
		# Settings > Function ("Track menu extras")
		toggle_item(_("Wikipedia artist search"), tauon.toggle_wiki, lambda: tauon.toggle_wiki(1))
		toggle_item(_("Sonemic artist search"), tauon.toggle_rym, lambda: tauon.toggle_rym(1))
		toggle_item(_("Bandcamp artist search"), tauon.toggle_band, lambda: tauon.toggle_band(1))
		toggle_item(_("Genius track search"), tauon.toggle_gen, lambda: tauon.toggle_gen(1))

	add_layout_sub(track_menu)
	folder_menu.br()
	add_layout_sub(folder_menu)


	# Create top menu
	x_menu          = tauon.x_menu
	view_menu       = tauon.view_menu
	set_menu        = tauon.set_menu
	set_menu_hidden = tauon.set_menu_hidden
	window_menu     = tauon.window_menu
	field_menu      = tauon.field_menu

	tauon.stop_menu.add(MenuItem(_("Always stop after album"), tauon.stop_mode_album_persist))
	tauon.stop_menu.add(MenuItem(_("Always stop after track"), tauon.stop_mode_track_persist))
	tauon.stop_menu.add(MenuItem(_("Stop after album"), tauon.stop_mode_album))
	tauon.stop_menu.add(MenuItem(_("Stop after track"), tauon.stop_mode_track))
	tauon.stop_menu.add(MenuItem(_("Continue Play"), tauon.stop_mode_off))

	window_menu.add(MenuItem(
		_("Show Tabs"), tauon.toggle_top_tabs, no_exit=True,
		check_test=lambda: tauon.toggle_top_tabs(1)))
	window_menu.br()
	# Top-panel visualiser mode (radio items; was its own right-click menu
	# over the visualiser area)
	window_menu.add(MenuItem(_("Off"), tauon.vis_off, no_exit=True,
		check_test=lambda: gui.vis_want == 0))
	window_menu.add(MenuItem(_("Level Meter"), tauon.level_on, no_exit=True,
		check_test=lambda: gui.vis_want == 1))
	window_menu.add(MenuItem(_("Spectrum Visualizer"), tauon.spec_on, no_exit=True,
		check_test=lambda: gui.vis_want == 2))
	window_menu.br()
	window_menu.add(MenuItem(_("Minimize"), tauon.do_minimize_button))
	window_menu.add(MenuItem(_("Maximize"), tauon.do_maximize_button))
	window_menu.add(MenuItem(_("Exit"),     tauon.do_exit_button))

	# Copy text
	field_menu.add(MenuItem(_("Copy"), field_copy, pass_ref=True))
	# Paste text
	field_menu.add(MenuItem(_("Paste"), field_paste, pass_ref=True))
	# Clear text
	field_menu.add(MenuItem(_("Clear"), field_clear, pass_ref=True))

	# Mark for translation
	_("Time")
	_("Filepath")

	# set_menu.add(MenuItem(_("Sort Ascending"), tauon.sort_ass, pass_ref=True, disable_test=tauon.view_pl_is_locked, pass_ref_deco=True))
	# set_menu.add(MenuItem(_("Sort Descending"), tauon.sort_dec, pass_ref=True, disable_test=tauon.view_pl_is_locked, pass_ref_deco=True))
	# set_menu.br()

	set_menu_hidden.add(MenuItem(_("Show bar"), tauon.show_set_bar))

	tauon.sa_regen_menu()

	gui.add_icon.xoff = 3
	gui.add_icon.yoff = 0
	gui.add_icon.colour = ColourRGBA(237, 80, 221, 255)
	gui.add_icon.colour_callback = tauon.new_playlist_colour_callback

	x_menu.add(MenuItem(_("New Playlist"), tauon.new_playlist, tauon.new_playlist_deco, icon=gui.add_icon))

	x_menu.add(MenuItem(_("Clean Database!"), tauon.clean_db_fast, tauon.clean_db_deco, show_test=tauon.clean_db_show_test))

	# x_menu.add(_("Internet Radio…"), activate_radio_box)

	x_menu.add(MenuItem(_("Import Music Folder"), tauon.import_music, show_test=tauon.show_import_music))

	x_menu.br()

	gui.settings_icon.xoff = 0
	gui.settings_icon.yoff = 2
	gui.settings_icon.colour = ColourRGBA(232, 200, 96, 255)  # [230, 152, 118, 255]#[173, 255, 47, 255] #[198, 237, 56, 255]
	# gui.settings_icon.colour = ColourRGBA(180, 140, 255, 255)
	x_menu.add(MenuItem(_("Settings"), tauon.activate_info_box, icon=gui.settings_icon))
	x_menu.add_sub(_("Database…"), 190)

	if tauon.dev_mode:
		def dev_mode_enable_save_state() -> None:
			bag.should_save_state = True
			tauon.show_message(_("Enabled saving state"))

		def dev_mode_disable_save_state() -> None:
			bag.should_save_state = False
			tauon.show_message(_("Disabled saving state"))

		x_menu.add_sub(_("Dev Mode"), 190)
		x_menu.add_to_sub(1, MenuItem(_("Enable Saving State"), tauon.dev_mode_enable_save_state))
		x_menu.add_to_sub(1, MenuItem(_("Disable Saving State"), tauon.dev_mode_disable_save_state))

	x_menu.br()

	# x_menu.add('Toggle Side panel', tauon.toggle_combo_view, tauon.combo_deco)

	x_menu.add_to_sub(0, MenuItem(_("Export as CSV"), tauon.export_database))
	x_menu.add_to_sub(0, MenuItem(_("Reload All Folders"), pctl.rescan_all_folders))
	x_menu.add_to_sub(0, MenuItem(_("Play History to Playlist"), tauon.q_to_playlist))
	x_menu.add_to_sub(0, MenuItem(_("Reset Image Cache"), tauon.clear_img_cache))
	x_menu.add_to_sub(0, MenuItem(_("Clear Artist Cache"), tauon.clear_artist_cache))

	x_menu.add_to_sub(0, MenuItem(_("Remove Network Tracks"), tauon.clean_db2))
	x_menu.add_to_sub(0, MenuItem(_("Remove Missing Tracks"), tauon.clean_db))
	x_menu.add_to_sub(0, MenuItem(_("Import FMPS Ratings"), tauon.import_fmps))
	x_menu.add_to_sub(0, MenuItem(_("Import POPM Ratings"), tauon.import_popm))
	x_menu.add_to_sub(0, MenuItem(_("Reset User Ratings"), tauon.clear_ratings))
	x_menu.add_to_sub(0, MenuItem(_("Find Incomplete Albums"), tauon.find_incomplete))
	x_menu.add_to_sub(0, MenuItem(_("Mark Missing as Found"), pctl.reset_missing_flags, show_test=inp.test_shift))

	if tauon.chrome:
		x_menu.add_sub(_("Chromecast…"), 220)
		shooter(tauon.cast_search2)

	tauon.chrome_menu = x_menu

	#x_menu.add(_("Cast…"), cast_search, cast_deco)


	mode_menu.add(MenuItem(_("Tab"), tauon.set_mini_mode_D))
	mode_menu.add(MenuItem(_("Mini"), tauon.set_mini_mode_A1))
	# mode_menu.add(_('Mini Mode Large'), tauon.set_mini_mode_A2)
	mode_menu.add(MenuItem(_("Signal"), tauon.set_mini_mode_E))
	mode_menu.add(MenuItem(_("Slate"), tauon.set_mini_mode_C1))
	mode_menu.add(MenuItem(_("Square"), tauon.set_mini_mode_B1))
	mode_menu.add(MenuItem(_("Square Large"), tauon.set_mini_mode_B2))

	mode_menu.br()
	mode_menu.add(MenuItem(_("Copy Title to Clipboard"), tauon.copy_bb_metadata))

	extra_menu.add_sub(_("Mini Mode"), 175)
	extra_menu.add_to_sub(0, MenuItem(_("Tab"), tauon.set_mini_mode_D))
	extra_menu.add_to_sub(0, MenuItem(_("Mini"), tauon.set_mini_mode_A1))
	extra_menu.add_to_sub(0, MenuItem(_("Signal"), tauon.set_mini_mode_E))
	extra_menu.add_to_sub(0, MenuItem(_("Slate"), tauon.set_mini_mode_C1))
	extra_menu.add_to_sub(0, MenuItem(_("Square"), tauon.set_mini_mode_B1))
	extra_menu.add_to_sub(0, MenuItem(_("Square Large"), tauon.set_mini_mode_B2))

	extra_menu.add(MenuItem(_("Random Track"), tauon.random_track, hint=";"))

	gui.radiorandom_icon.xoff = 1
	gui.radiorandom_icon.yoff = 0
	gui.radiorandom_icon.colour = ColourRGBA(153, 229, 133, 255)
	extra_menu.add(MenuItem(_("Radio Random"), tauon.radio_random, hint="/", icon=gui.radiorandom_icon))

	gui.revert_icon.xoff = 1
	gui.revert_icon.yoff = 0
	gui.revert_icon.colour = ColourRGBA(229, 102, 59, 255)
	extra_menu.add(MenuItem(_("Revert"), pctl.revert, hint="Shift+/", icon=gui.revert_icon))

	# extra_menu.add('Toggle Repeat', tauon.toggle_repeat, hint='COMMA')


	# extra_menu.add('Toggle Random', tauon.toggle_random, hint='PERIOD')
	extra_menu.add(MenuItem(_("Clear Queue"), tauon.clear_queue, tauon.queue_deco, hint="Alt+Shift+Q"))

	gui.heart_icon.colour = ColourRGBA(245, 60, 60, 255)
	gui.heart_icon.xoff = 3
	gui.heart_icon.yoff = 0

	if gui.scale == 1.25:
		gui.heart_icon.yoff = 1

	gui.heart_icon.colour_callback = tauon.heart_menu_colour
	extra_menu.add(MenuItem(_("Love"), tauon.bar_love_notify, tauon.love_deco, icon=gui.heart_icon))
	extra_menu.add(MenuItem(_("Global Search"), tauon.activate_search_overlay, hint="Ctrl+G"))
	extra_menu.add(MenuItem(_("Locate Artist"), tauon.locate_artist))
	extra_menu.add(MenuItem(_("Go To Playing"), tauon.goto_playing_extra, hint="'"))

	extra_menu.br()

	theme_files = os.listdir(str(tauon.install_directory / "theme"))
	theme_files.sort()

	lastfm_icon = MenuIcon(gui.last_fm_icon)

	if gui.scale in (2, 1.25):
		lastfm_icon.xoff = 0
	else:
		lastfm_icon.xoff = -1

	lastfm_icon.yoff = 1

	lastfm_icon.colour = ColourRGBA(249, 70, 70, 255)
	lastfm_icon.colour_callback = tauon.lastfm_colour

	lb_icon = MenuIcon(asset_loader(bag, bag.loaded_asset_dc, "lb-g.png"))
	lb_icon.base_asset = asset_loader(bag, bag.loaded_asset_dc, "lb-gs.png")

	lb_icon.mode_callback = tauon.lb_mode

	lb_icon.xoff = 3
	lb_icon.yoff = -1

	if gui.scale == 1.25:
		lb_icon.yoff = 0

	if prefs.auto_lfm:
		listen_icon = lastfm_icon
	elif tauon.lb.enable:
		listen_icon = lb_icon
	else:
		listen_icon = None

	x_menu.add(MenuItem("LFM", tauon.lastfm.toggle, tauon.last_fm_menu_deco, icon=listen_icon, show_test=tauon.lastfm_menu_test))
	#x_menu.add(MenuItem(_("Synced Lyrics Editor"), tauon.view_box.activate_synced_lyric_editor)) #show_test=tauon.exit_shuffle_layout))
	#x_menu.add(MenuItem(_("Donate"), open_donate_link))
	x_menu.add(MenuItem(_("Online Manual"), tauon.open_manual_link))
	x_menu.add(MenuItem(_("Show Release Notes"), tauon.nagbox.show))
	x_menu.add(MenuItem(_("Exit"), tauon.exit, hint="Alt+F4", set_ref="User clicked menu exit button", pass_ref=+True))
	x_menu.add(MenuItem(_("Disengage Quick Add"), tauon.stop_quick_add, show_test=tauon.show_stop_quick_add))
	x_menu.add(MenuItem(_("Exit Shuffle Lockdown"), tauon.toggle_shuffle_layout, tauon.toggle_shuffle_layout_deco, show_test=tauon.exit_shuffle_layout))


	gui.pt_on = Timer()
	gui.pt_off = Timer()
	gui.pt = 0

	# ------------------------------------------------------------------------------------
	# WEBSERVER
	if prefs.enable_web is True:
		webThread = threading.Thread(
			target=webserve, args=[pctl, prefs, gui, tauon.album_art_gen, str(tauon.install_directory), tauon.strings, tauon])
		webThread.daemon = True
		webThread.start()

	ctlThread = threading.Thread(target=controller, args=[tauon])
	ctlThread.daemon = True
	ctlThread.start()

	if prefs.enable_remote:
		tauon.start_remote()
		tauon.remote_limited = False
	# --------------------------------------------------------------

	pref_box = tauon.pref_box
	radiobox = tauon.radiobox

	radio_entry_menu.add(MenuItem(_("Visit Website"), visit_radio_site, tauon.visit_radio_site_deco, pass_ref=True, pass_ref_deco=True))
	radio_entry_menu.add(MenuItem(_("Save"), tauon.save_to_radios, pass_ref=True))

	artist_list_menu.add(MenuItem(_("Filter to New Playlist"), tauon.create_artist_pl, pass_ref=True, icon=gui.filter_icon))
	artist_list_menu.add_sub(_("View..."), 140)
	artist_list_menu.add_to_sub(0, MenuItem(_("Sort Alphabetically"), tauon.aa_sort_alpha))
	artist_list_menu.add_to_sub(0, MenuItem(_("Sort by Popularity"), tauon.aa_sort_popular))
	artist_list_menu.add_to_sub(0, MenuItem(_("Sort by Playtime"), tauon.aa_sort_play))
	artist_list_menu.add_to_sub(0, MenuItem(_("Toggle Thumbnails"), tauon.toggle_artist_list_style))
	artist_list_menu.add_to_sub(0, MenuItem(_("Toggle Filter"), tauon.toggle_artist_list_threshold, tauon.toggle_artist_list_threshold_deco))

	artist_info_menu.add(MenuItem(_("Download Artist Data"), tauon.artist_info_box.manual_dl, tauon.artist_dl_deco, show_test=tauon.test_artist_dl))
	artist_info_menu.add(MenuItem(_("Clear Bio"), tauon.flush_artist_bio, pass_ref=True, show_test=inp.test_shift))
	radio_context_menu.add(MenuItem(_("Edit..."), tauon.rename_station, pass_ref=True))
	radio_context_menu.add(
		MenuItem(_("Visit Website"), visit_radio_station, tauon.visit_radio_station_site_deco, pass_ref=True, pass_ref_deco=True))
	radio_context_menu.add(MenuItem(_("Remove"), tauon.remove_station, pass_ref=True))

	tauon.dl_menu.add(MenuItem(_("Dismiss"), tauon.dismiss_dl))

	# Set SDL window drag areas
	# if system != "Windows":

	c_hit_callback = sdl3.SDL_HitTest(tauon.hit_callback)
	sdl3.SDL_SetWindowHitTest(t_window, c_hit_callback, 0)

	# --------------------------------------------------------------------------------------------

	# caster = threading.Thread(target=enc, args=[tauon])
	# caster.daemon = True
	# caster.start()

	tauon.thread_manager.ready_playback()

	try:
		tauon.thread_manager.d["caster"] = [lambda: x, [tauon], None]
	except Exception:
		logging.exception("Failed to cast")

	tauon.thread_manager.d["worker"]  = [worker1, [tauon], None]
	tauon.thread_manager.d["search"]  = [worker2, [tauon], None]
	tauon.thread_manager.d["gallery"] = [worker3, [tauon], None]
	tauon.thread_manager.d["style"]   = [worker4, [tauon], None]
	tauon.thread_manager.d["radio-thumb"] = [tauon.radio_thumb_gen.loader, [], None]

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

	d_border = 1

	mouse_moved = False

	for item in sys.argv[1:]:
		if (
			(os.path.isdir(item) or os.path.isfile(item) or "file://" in item)
			and not item.endswith(".py")
			and not item.endswith(".exe")
			and not item.endswith("tauonmb")
			and not item.startswith("-")
		):
			tauon.open_uri(item)

	sdl_version = sdl3.SDL_GetVersion()
	logging.info(f"Using SDL version: {sdl_version!s}")

	# C-ML
	# if prefs.backend == Backend.GSTREAMER:
	#     logging.warning("Using GStreamer as fallback. Some functions disabled")
	if prefs.backend == Backend.NONE:
		tauon.show_message(_("ERROR: No backend found"), mode="error")

	# SDL_RenderClear(renderer)
	# SDL_RenderPresent(renderer)

	# SDL_ShowWindow(t_window)

	# Clear spectogram texture
	sdl3.SDL_SetRenderTarget(renderer, gui.spec2_tex)
	sdl3.SDL_RenderClear(renderer)
	ddt.rect((0, 0, 1000, 1000), ColourRGBA(7, 7, 7, 255))

	sdl3.SDL_SetRenderTarget(renderer, gui.spec1_tex)
	sdl3.SDL_RenderClear(renderer)
	ddt.rect((0, 0, 1000, 1000), ColourRGBA(7, 7, 7, 255))

	sdl3.SDL_SetRenderTarget(renderer, gui.spec_level_tex)
	sdl3.SDL_RenderClear(renderer)
	ddt.rect((0, 0, 1000, 1000), ColourRGBA(7, 7, 7, 255))

	sdl3.SDL_SetRenderTarget(renderer, None)

	# sdl3.SDL_RenderPresent(renderer)

	# time.sleep(3)

	sdl3.SDL_StartTextInput(t_window)
	active_touch = tauon.touch_input_tracker

	# SDL_SetHint(SDL_HINT_IME_INTERNAL_EDITING, b"1")
	# SDL_EventState(SDL_SYSWMEVENT, 1)
	tauon.test_show_add_home_music()

	if gui.restart_album_mode:
		tauon.toggle_album_mode(force_on=True)

	if gui.remember_library_mode:
		tauon.toggle_library_mode()

	if prefs.reload_play_state and prefs.reload_state and prefs.reload_state[0] == PlayingState.PLAYING:
		pctl.jump_time = prefs.reload_state[1]
		pctl.play()
	elif not prefs.reload_play_state:
		prefs.reload_state = None

	pctl.refresh_now_playing()

	prefs.theme = get_theme_number(dirs, prefs.theme_name)

	if pctl.pl_to_id(pctl.active_playlist_viewing) in gui.gallery_positions:
		gui.album_scroll_px = gui.gallery_positions[pctl.pl_to_id(pctl.active_playlist_viewing)]

	for playlist in pctl.multi_playlist:
		pctl.try_reload_playlist_from_file(playlist, False)
	tauon.playlist_autoscan = True
	tauon.thread_manager.ready("worker")

	# Hold the splash/loading screen for a minimum duration
	# while tauon.core_timer.get() < 0.5:
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
						sub_icon_space = 25
						break
				for sub_item in menu.subs[item.sub_menu_number]:
					test_width = math.ceil(ddt.get_text_w(sub_item.title, menu.font) / gui.scale) + sub_icon_space + 23
					ww = max(test_width, ww)

				item.sub_menu_width = max(ww, item.sub_menu_width)

		menu.w = max(w, menu.w)

	if gui.restore_showcase_view:
		tauon.enter_showcase_view()
	if gui.restore_radio_view:
		tauon.enter_radio_view()

	if bag.macos:
		try:
			from tauon.t_modules.t_macos_menubar import MacMenuBar
		except ModuleNotFoundError:
			logging.warning("Unable to import PyObjC menubar support, macOS menus will be unavailable.")
		except Exception:
			logging.exception("Failed to initialise macOS menubar support.")
		else:
			tauon.macos_menu_bar = MacMenuBar(tauon)
			tauon.macos_menu_bar.install()

	# pctl.switch_playlist(len(pctl.multi_playlist) - 1)

	sdl3.SDL_SetRenderTarget(renderer, overlay_texture_texture)

	block_size = 3

	x = 0
	y = 0
	while y < 300:
		x = 0
		while x < 300:
			ddt.rect((x, y, 1, 1), ColourRGBA(0, 0, 0, 70))
			ddt.rect((x + 2, y + 0, 1, 1), ColourRGBA(0, 0, 0, 70))
			ddt.rect((x + 2, y + 2, 1, 1), ColourRGBA(0, 0, 0, 70))
			ddt.rect((x + 0, y + 2, 1, 1), ColourRGBA(0, 0, 0, 70))

			x += block_size
		y += block_size

	tauon.sync_target.text = prefs.sync_target
	sdl3.SDL_SetRenderTarget(renderer, None)

	if tauon.windows:
		sdl3.SDL_SetWindowResizable(t_window, True)  # Not sure why this is needed

	# Generate theme buttons
	tauon.pref_box.refresh_theme_presets()

	pctl.total_playtime = tauon.star_store.get_total()

	# MAIN LOOP
	# main_loop(tauon)

	event = sdl3.SDL_Event()

	# ---------------------------------------------------------------------
	# Player variables
	draw_sep_hl = False

	# Playlist Panel
	scroll_opacity = 0

	row_len = 5
	b_info_y = int(window_size[1] * 0.7)  # For future possible panel below playlist

	gal_up = False
	gal_down = False
	gal_left = False
	gal_right = False

	scroll_hold = False
	album_scroll_hold = False
	scroll_point = 0
	scroll_bpoint = 0
	sbl = 50
	sbp = 100

	time_last_save = 0
	spec_smoothing = True  # TODO(Martin): Always true
	resize_mode = False  # TODO(Martin): Always false
	reset_render = False
	c_yax = 0
	c_yax_timer = Timer()
	c_xax = 0
	c_xax_timer = Timer()
	c_xay = 0
	c_xay_timer = Timer()
	rt = 0
	ggc = 2
	pl_bg = None
	if (tauon.user_directory / "bg.png").exists():
		pl_bg = LoadImageAsset(
			scaled_asset_directory=tauon.dirs.scaled_asset_directory,
			path=str(tauon.user_directory / "bg.png"),
			is_full_path=True,
		)

	playlist_render = StandardPlaylist(tauon, pl_bg)
	tauon.playlist_render = playlist_render  # exposed for the Custom Layout Tracklist widget
	meta_box = MetaBox(tauon)
	tauon.meta_box = meta_box  # exposed for the Custom Layout metadata/lyrics widgets
	showcase = Showcase(tauon, TimedLyricsEdit(tauon=tauon))
	tauon.showcase = showcase  # exposed for the Custom Layout Sticks visualiser widget

	def render_gallery() -> None:
		"""Render the album gallery grid (art tiles, scrolling, input handling and
		the power tag bar). Extracted verbatim from the main-loop album-mode block
		so the Custom Layout's Album Gallery widget can reuse it. Geometry derives
		from gui.rspw / gui.panelY / gui.panelBY / window_size, so a caller places
		it by pointing those at a target rect (the preset path calls it with them
		untouched, so preset rendering is byte-identical).
		"""
		nonlocal gal_up, gal_down, gal_left, gal_right, row_len
		try:
			# Arrow key input
			if gal_right:
				gal_right = False
				tauon.gal_jump_select(False, 1)
				tauon.goto_album(pctl.selected_in_playlist)
				pctl.playlist_view_position = pctl.selected_in_playlist
				logging.debug("Position changed by gallery key press")
				gui.request_tracklist_redraw()
			if gal_down:
				gal_down = False
				tauon.gal_jump_select(False, row_len)
				tauon.goto_album(pctl.selected_in_playlist, down=True)
				pctl.playlist_view_position = pctl.selected_in_playlist
				logging.debug("Position changed by gallery key press")
				gui.request_tracklist_redraw()
			if gal_left:
				gal_left = False
				tauon.gal_jump_select(True, 1)
				tauon.goto_album(pctl.selected_in_playlist)
				pctl.playlist_view_position = pctl.selected_in_playlist
				logging.debug("Position changed by gallery key press")
				gui.request_tracklist_redraw()
			if gal_up:
				gal_up = False
				tauon.gal_jump_select(True, row_len)
				tauon.goto_album(pctl.selected_in_playlist)
				pctl.playlist_view_position = pctl.selected_in_playlist
				logging.debug("Position changed by gallery key press")
				gui.request_tracklist_redraw()

			w = gui.rspw

			if window_size[0] < 750 * gui.scale:
				w = window_size[0] - 20 * gui.scale
				if gui.lsp:
					w -= gui.lspw

			# Gallery: Compact reframes the window to the segment and applies its
			# own uniform margins below — the narrow-window left inset would
			# double up on the left and be missing from the top/right.
			if gui.gallery_forced_row_len:
				w = gui.rspw

			x = window_size[0] - w
			# sx = x
			# sw = w
			h = window_size[1] - gui.panelY - gui.panelBY

			if not gui.show_playlist and inp.mouse_click:
				left = gui.playlist_left

				if (
					left < inp.mouse_position[0] < left + 20 * gui.scale
					and window_size[1] - gui.panelBY > inp.mouse_position[1] > gui.panelY
				):
					tauon.toggle_album_mode()
					inp.mouse_click = False
					inp.mouse_down = False

			rect = [x, gui.panelY, w, h]
			if not gui.show_playlist and x > gui.playlist_left:
				ddt.rect([gui.playlist_left, gui.panelY, x - gui.playlist_left, h], colours.gallery_background)
			ddt.rect(rect, colours.gallery_background)

			# Tiles at the scroll edges render partially outside the gallery
			# area; clip so they can't draw over (or show through) the panels
			# above and below. Reset in the finally below.
			gallery_clip = sdl3.SDL_Rect(round(x), round(gui.panelY), round(w), round(h))
			sdl3.SDL_SetRenderClipRect(tauon.renderer, ctypes.byref(gallery_clip))

			# ddt.rect_r(rect, [255, 0, 0, 200], True)

			area_x = w + 38 * gui.scale
			# area_x = w - 40 * gui.scale

			row_len = int((area_x - gui.album_h_gap) / (tauon.album_mode_art_size + gui.album_h_gap))

			# The Album Grid widget forces the row length (its art size is derived
			# from it, so the width formula above can land one off). 0 in presets.
			if gui.gallery_forced_row_len:
				row_len = gui.gallery_forced_row_len

			# logging.info(row_len)

			compact = 40 * gui.scale
			if gui.custom_mode:
				compact -= 30 * gui.scale
			a_offset = 7 * gui.scale

			l_area = x
			r_area = w
			# c_area = r_area // 2 + l_area

			ddt.text_background_colour = colours.gallery_background

			line1_colour = colours.gallery_artist_line
			line2_colour = colours.grey(240)  # colours.side_bar_line1

			if colours.side_panel_background != colours.gallery_background:
				line2_colour = ColourRGBA(240, 240, 240, 255)
				line1_colour = alpha_mod(ColourRGBA(20, 220, 220, 255), 120)

			if test_lumi(colours.gallery_background) < 0.5 or (prefs.use_card_style and colours.lm):
				line1_colour = colours.grey(80)
				line2_colour = colours.grey(40)

			if row_len == 0:
				row_len = 1

			dev = int((r_area - compact) / (row_len + 0))

			# Gallery: Compact (forced row length): the centred preset formula
			# below leaves asymmetric outer margins (~h_gap/2 - 2px left,
			# ~h_gap/2 + 12px right); the grid instead lays tiles on a uniform
			# float pitch inset by gallery_grid_margin on each side, so the
			# left and right margins match.
			grid_edge = False
			grid_margin = 0
			if gui.gallery_forced_row_len:
				grid_edge = True
				grid_margin = gui.gallery_grid_margin
				dev = (r_area - grid_margin * 2 + gui.album_h_gap) / row_len
			# The grid draws the title lines slightly closer to the art (the row
			# pitch is unchanged — the text just sits higher within it). 0 = preset.
			text_lift = round(5 * gui.scale) if grid_edge else 0
			artist_lift = round(6 * gui.scale) if grid_edge else 0

			render_pos = 0
			album_on = 0

			max_scroll = round(
				(math.ceil((len(tauon.album_dex)) / row_len) - 1)
				* (tauon.album_mode_art_size + gui.album_v_gap)
			) - round(50 * gui.scale)

			# Mouse wheel scrolling. The momentum channel key is per Gallery:
			# Compact instance (swapped in around this call) so several
			# galleries scroll independently; the preset key in gallery_scroll_key
			# is the default.
			scroll_key = gui.gallery_scroll_key
			gallery_scroll_area = (window_size[0] - w, gui.panelY, w, window_size[1] - gui.panelBY - gui.panelY)
			touch_scroll = inp.touch_scroll_y != 0 and coll_point(inp.touch_position, gallery_scroll_area)
			use_smooth_gallery = (
				tauon.smooth_scroll.enabled()
				or touch_scroll
				or tauon.smooth_scroll.active(scroll_key)
			)
			row_gallery_scroll = prefs.gallery_row_scroll and not use_smooth_gallery and not touch_scroll
			if (
				not tauon.search_over.active
				and not radiobox.active
				and inp.mouse_position[0] > window_size[0] - w
				and gui.panelY < inp.mouse_position[1] < window_size[1] - gui.panelBY
			):
				if inp.mouse_wheel != 0:
					tauon.scroll_gallery_hide_timer.set()
					gui.frame_callback_list.append(TestTimer(0.9))

				if use_smooth_gallery and inp.mouse_wheel != 0:
					tauon.smooth_scroll.add_wheel_motion(scroll_key, -inp.mouse_wheel, prefs.gallery_scroll_wheel_px)
				elif row_gallery_scroll:
					gui.album_scroll_px -= inp.mouse_wheel * (
						tauon.album_mode_art_size + gui.album_v_gap
					)  # 90
				else:
					gui.album_scroll_px -= inp.mouse_wheel * prefs.gallery_scroll_wheel_px


				if inp.touch_released:
					tauon.smooth_scroll.release_touch("gallery")
				elif touch_scroll:
					tauon.smooth_scroll.apply_touch_drag("gallery", -inp.touch_scroll_y)

				if use_smooth_gallery:
					gui.album_scroll_px += tauon.smooth_scroll.step_motion(scroll_key)

				if gui.album_scroll_px < round(gui.album_v_slide_value * -1):
					gui.album_scroll_px = round(gui.album_v_slide_value * -1)
					if tauon.album_dex:
						tauon.gallery_pulse_top.pulse()

				if gui.album_scroll_px > max_scroll:
					gui.album_scroll_px = max_scroll
					gui.album_scroll_px = max(gui.album_scroll_px, round(gui.album_v_slide_value * -1))
			elif inp.touch_released:
				tauon.smooth_scroll.release_touch("gallery")
				if tauon.smooth_scroll.active("gallery"):
					gui.album_scroll_px += tauon.smooth_scroll.step_motion("gallery")
					if gui.album_scroll_px < round(gui.album_v_slide_value * -1):
						gui.album_scroll_px = round(gui.album_v_slide_value * -1)
					if gui.album_scroll_px > max_scroll:
						gui.album_scroll_px = max_scroll
						gui.album_scroll_px = max(gui.album_scroll_px, round(gui.album_v_slide_value * -1))
			elif touch_scroll:
				tauon.scroll_gallery_hide_timer.set()
				gui.frame_callback_list.append(TestTimer(0.9))
				tauon.smooth_scroll.apply_touch_drag("gallery", -inp.touch_scroll_y)
				gui.album_scroll_px += tauon.smooth_scroll.step_motion("gallery")
				if gui.album_scroll_px < round(gui.album_v_slide_value * -1):
					gui.album_scroll_px = round(gui.album_v_slide_value * -1)
				if gui.album_scroll_px > max_scroll:
					gui.album_scroll_px = max_scroll
					gui.album_scroll_px = max(gui.album_scroll_px, round(gui.album_v_slide_value * -1))

			if tauon.smooth_scroll.active(scroll_key) and not touch_scroll and not inp.touch_released and not (
				not tauon.search_over.active
				and not radiobox.active
				and inp.mouse_position[0] > window_size[0] - w
				and gui.panelY < inp.mouse_position[1] < window_size[1] - gui.panelBY
			):
				gui.album_scroll_px += tauon.smooth_scroll.step_motion(scroll_key)
				if gui.album_scroll_px < round(gui.album_v_slide_value * -1):
					gui.album_scroll_px = round(gui.album_v_slide_value * -1)
				if gui.album_scroll_px > max_scroll:
					gui.album_scroll_px = max_scroll
					gui.album_scroll_px = max(gui.album_scroll_px, round(gui.album_v_slide_value * -1))

			rect = (
				gui.gallery_scroll_field_left,
				gui.panelY,
				window_size[0] - gui.gallery_scroll_field_left - 2,
				h,
			)

			card_mode = False
			if prefs.use_card_style and colours.lm and gui.gallery_show_text:
				card_mode = True

			rect = (window_size[0] - 40 * gui.scale, gui.panelY, 38 * gui.scale, h)
			tauon.fields.add(rect)

			# Show scroll area
			if (
				tauon.coll(rect)
				or tauon.gallery_scroll.held
				or tauon.scroll_gallery_hide_timer.get() < 0.9
				or gui.album_tab_mode
			):
				if tauon.gallery_scroll.held:
					while len(tauon.gall_ren.queue) > 2:
						tauon.gall_ren.queue.pop()

				# Draw power bar button
				if gui.pt == 0 and gui.power_bar is not None and len(gui.power_bar) > 3:
					rect = (
						window_size[0] - (15 + 20) * gui.scale,
						gui.panelY + 3 * gui.scale,
						18 * gui.scale,
						24 * gui.scale,
					)
					tauon.fields.add(rect)
					colour = ColourRGBA(255, 255, 255, 35)
					if colours.lm:
						colour = ColourRGBA(0, 0, 0, 30)
					if tauon.coll(rect) and not tauon.gallery_scroll.held:
						colour = ColourRGBA(255, 220, 100, 245)
						if colours.lm:
							colour = ColourRGBA(250, 100, 0, 255)
						if inp.mouse_click:
							gui.pt = 1

					gui.power_bar_icon.render(
						rect[0] + round(5 * gui.scale), rect[1] + round(3 * gui.scale), colour
					)

				# Draw scroll bar
				if gui.pt == 0:
					gui.album_scroll_px = (
						tauon.gallery_scroll.draw(
							window_size[0] - 16 * gui.scale,
							gui.panelY,
							15 * gui.scale,
							window_size[1] - (gui.panelY + gui.panelBY),
							gui.album_scroll_px + gui.album_v_slide_value,
							max_scroll + gui.album_v_slide_value,
							jump_distance=1400 * gui.scale,
							r_click=inp.right_click,
							extend_field=15 * gui.scale,
						)
						- gui.album_v_slide_value
					)

			if gui.last_row != row_len:
				gui.last_row = row_len

				if pctl.selected_in_playlist < len(pctl.playing_playlist()):
					tauon.goto_album(pctl.selected_in_playlist)
				# else:
				# 	tauon.goto_album(pctl.playlist_playing_position)

			extend = 0
			if card_mode:  # gui.gallery_show_text:
				extend = 40 * gui.scale

			# Process inputs first
			if (
				inp.mouse_click or inp.right_click or inp.middle_click or inp.mouse_down or inp.mouse_up
			) and pctl.default_playlist:
				while render_pos < gui.album_scroll_px + window_size[1]:
					if gui.b_info_bar and render_pos > gui.album_scroll_px + b_info_y:
						break

					if render_pos < gui.album_scroll_px - tauon.album_mode_art_size - gui.album_v_gap:
						# Skip row
						render_pos += tauon.album_mode_art_size + gui.album_v_gap
						album_on += row_len
					else:
						# render row
						y = render_pos - gui.album_scroll_px
						row_x = 0
						for a in range(row_len):
							if album_on > len(tauon.album_dex) - 1:
								break

							if grid_edge:
								x = l_area + grid_margin + int(dev * a)
							else:
								x = (
									(l_area + dev * a)
									- int(tauon.album_mode_art_size / 2)
									+ int(dev / 2)
									+ int(compact / 2)
									- a_offset
								)

							if tauon.album_dex[album_on] >= len(pctl.default_playlist):
								break

							rect = (
								x,
								y,
								tauon.album_mode_art_size,
								tauon.album_mode_art_size + extend * gui.scale,
							)
							# tauon.fields.add(rect)
							m_in = (
								tauon.coll(rect)
								and gui.panelY < inp.mouse_position[1] < window_size[1] - gui.panelBY
							)

							# if m_in:
							#     ddt.rect_r((x - 7, y - 7, tauon.album_mode_art_size + 14, tauon.album_mode_art_size + extend + 55), [80, 80, 80, 80], True)

							# Quick drag and drop
							if (
								inp.mouse_up
								and (gui.playlist_hold and m_in)
								and not gui.side_drag
								and gui.shift_selection
							):
								info = tauon.get_album_info(tauon.album_dex[album_on])
								if info[1]:
									track_position = info[1][0]

									if track_position > gui.shift_selection[0]:
										track_position = info[1][-1] + 1

									ref = []
									for item in gui.shift_selection:
										ref.append(pctl.default_playlist[item])

									for item in gui.shift_selection:
										pctl.default_playlist[item] = "old"

									for item in gui.shift_selection:
										pctl.default_playlist.insert(track_position, "new")

									for b in reversed(range(len(pctl.default_playlist))):
										if pctl.default_playlist[b] == "old":
											del pctl.default_playlist[b]
									gui.shift_selection = []
									for b in range(len(pctl.default_playlist)):
										if pctl.default_playlist[b] == "new":
											gui.shift_selection.append(b)
											pctl.default_playlist[b] = ref.pop(0)

									pctl.selected_in_playlist = gui.shift_selection[0]
									gui.request_tracklist_redraw()
									gui.playlist_hold = False

									tauon.reload_albums(True)
									pctl.notify_database_changed()
							elif not gui.side_drag and tauon.is_level_zero():
								if (
									coll_point(inp.click_location, rect)
									and gui.panelY < inp.mouse_position[1] < window_size[1] - gui.panelBY
								):
									info = tauon.get_album_info(tauon.album_dex[album_on])

									if m_in and inp.mouse_up and prefs.gallery_single_click:
										if (
											tauon.is_level_zero()
											and gui.d_click_ref == tauon.album_dex[album_on]
										):
											if info[0] == 1 and pctl.playing_state == PlayingState.PAUSED:
												pctl.play()
											elif (
												info[0] == 1 and pctl.playing_state != PlayingState.STOPPED
											):
												pctl.playlist_view_position = tauon.album_dex[album_on]
												logging.debug("Position changed by gallery click")
											else:
												pctl.playlist_view_position = tauon.album_dex[album_on]
												logging.debug("Position changed by gallery click")
												pctl.jump(
													pctl.default_playlist[tauon.album_dex[album_on]],
													tauon.album_dex[album_on],
												)
											pctl.show_current()
									elif inp.mouse_down and not m_in:
										info = tauon.get_album_info(tauon.album_dex[album_on])
										inp.quick_drag = True
										if (
											not tauon.pl_is_locked(pctl.active_playlist_viewing)
											or inp.key_shift_down
										):
											gui.playlist_hold = True
										gui.shift_selection = info[1]
										gui.request_tracklist_redraw()
										inp.click_location = [0, 0]

							if m_in:
								info = tauon.get_album_info(tauon.album_dex[album_on])
								if inp.mouse_click:
									if prefs.gallery_single_click:
										gui.d_click_ref = tauon.album_dex[album_on]
									else:
										if (
											tauon.d_click_timer.get() < 0.5
											and gui.d_click_ref == tauon.album_dex[album_on]
										):
											if info[0] == 1 and pctl.playing_state == PlayingState.PAUSED:
												pctl.play()
											elif (
												info[0] == 1 and pctl.playing_state != PlayingState.STOPPED
											):
												pctl.playlist_view_position = tauon.album_dex[album_on]
												logging.debug("Position changed by gallery click")
											else:
												pctl.playlist_view_position = tauon.album_dex[album_on]
												logging.debug("Position changed by gallery click")
												pctl.jump(
													pctl.default_playlist[tauon.album_dex[album_on]],
													tauon.album_dex[album_on],
												)
										else:
											gui.d_click_ref = tauon.album_dex[album_on]
											tauon.d_click_timer.set()

										pctl.playlist_view_position = tauon.album_dex[album_on]
										logging.debug("Position changed by gallery click")
										pctl.selected_in_playlist = tauon.album_dex[album_on]
										gui.request_tracklist_redraw()
								elif inp.middle_click and tauon.is_level_zero():
									# Middle click to add album to queue
									if inp.key_ctrl_down:
										# Add to queue ungrouped
										album = tauon.get_album_info(tauon.album_dex[album_on])[1]
										for item in album:
											pctl.force_queue.append(
												queue_item_gen(
													pctl.default_playlist[item],
													item,
													pctl.pl_to_id(pctl.active_playlist_viewing),
												)
											)
										tauon.queue_timer_set(plural=True)
										if prefs.stop_end_queue:
											pctl.stop_mode = StopMode.OFF
									else:
										# Add to queue grouped
										tauon.add_album_to_queue(
											pctl.default_playlist[tauon.album_dex[album_on]],
											tauon.album_dex[album_on],
											pctl.pl_to_id(pctl.active_playlist_viewing),
										)
								elif inp.right_click:
									if pctl.quick_add_target:
										pl = pctl.id_to_pl(pctl.quick_add_target)
										if pl is not None:
											parent = pctl.get_track(
												pctl.default_playlist[tauon.album_dex[album_on]]
											).parent_folder_path
											# remove from target pl
											if (
												pctl.default_playlist[tauon.album_dex[album_on]]
												in pctl.multi_playlist[pl].playlist_ids
											):
												for i in reversed(
													range(len(pctl.multi_playlist[pl].playlist_ids))
												):
													if (
														pctl.get_track(
															pctl.multi_playlist[pl].playlist_ids[i]
														).parent_folder_path
														== parent
													):
														del pctl.multi_playlist[pl].playlist_ids[i]
											else:
												# add
												for i in range(len(pctl.default_playlist)):
													if (
														pctl.get_track(
															pctl.default_playlist[i]
														).parent_folder_path
														== parent
													):
														pctl.multi_playlist[pl].playlist_ids.append(
															pctl.default_playlist[i]
														)
										tauon.reload_albums(True)
									else:
										pctl.selected_in_playlist = tauon.album_dex[album_on]
										# playlist_position = pctl.playlist_selected
										gui.shift_selection = [pctl.selected_in_playlist]
										gallery_menu.activate(MenuTrackRef(
											pctl.default_playlist[pctl.selected_in_playlist],
											pctl.selected_in_playlist,
											pctl.pl_to_id(pctl.active_playlist_viewing),
										))

										gui.shift_selection = []
										u = pctl.selected_in_playlist
										while (
											u < len(pctl.default_playlist)
											and pctl.master_library[
												pctl.default_playlist[u]
											].parent_folder_path
											== pctl.master_library[
												pctl.default_playlist[pctl.selected_in_playlist]
											].parent_folder_path
										):
											gui.shift_selection.append(u)
											u += 1
										pctl.render_playlist()

							album_on += 1

						if album_on > len(tauon.album_dex):
							break
						render_pos += tauon.album_mode_art_size + gui.album_v_gap

			# Right-click on the gallery background: settings menu. Runs after
			# the album input pass, so a right-click on a tile has already
			# activated gallery_menu (making is_level_zero False). The right
			# ~40px strip is the scroll-bar hotzone (right-click there jumps
			# the scroll). The Compact grid widget has its own menu instead.
			if (
				inp.right_click
				and not gui.gallery_forced_row_len
				and tauon.is_level_zero()
				and window_size[0] - w < inp.mouse_position[0] < window_size[0] - 40 * gui.scale
				and gui.panelY < inp.mouse_position[1] < window_size[1] - gui.panelBY
			):
				inp.right_click = False
				gallery_settings_menu.activate()

			render_pos = 0
			album_on = 0
			album_count = 0

			if not pref_box.enabled or inp.mouse_wheel != 0:
				gui.first_in_grid = None

			# Render album grid
			while render_pos < gui.album_scroll_px + window_size[1] and pctl.default_playlist:
				if gui.b_info_bar and render_pos > gui.album_scroll_px + b_info_y:
					break

				if render_pos < gui.album_scroll_px - tauon.album_mode_art_size - gui.album_v_gap:
					# Skip row
					render_pos += tauon.album_mode_art_size + gui.album_v_gap
					album_on += row_len
				else:
					# render row
					y = render_pos - gui.album_scroll_px

					row_x = 0

					if (
						y > window_size[1] - gui.panelBY - 30 * gui.scale
						and window_size[1] < 340 * gui.scale
					):
						break
					# if y >

					for a in range(row_len):
						if album_on > len(tauon.album_dex) - 1:
							break

						if grid_edge:
							x = l_area + grid_margin + int(dev * a)
						else:
							x = (
								(l_area + dev * a)
								- int(tauon.album_mode_art_size / 2)
								+ int(dev / 2)
								+ int(compact / 2)
								- a_offset
							)

						if tauon.album_dex[album_on] >= len(pctl.default_playlist):
							break

						track = pctl.master_library[pctl.default_playlist[tauon.album_dex[album_on]]]

						info = tauon.get_album_info(tauon.album_dex[album_on])
						album = info[1]
						# info = (0, 0, 0)

						# rect = (x, y, tauon.album_mode_art_size, tauon.album_mode_art_size + extend * gui.scale)
						# tauon.fields.add(rect)
						# m_in = tauon.coll(rect) and gui.panelY < inp.mouse_position[1] < window_size[1] - gui.panelBY

						if (
							gui.first_in_grid is None and y > gui.panelY
						):  # This marks what track is the first in the grid
							gui.first_in_grid = tauon.album_dex[album_on]

						# artisttitle = colours.side_bar_line2
						# albumtitle = colours.side_bar_line1  # grey(220)

						if card_mode:
							ddt.text_background_colour = colours.grey(250)
							tauon.drop_shadow.render(
								x + 3 * gui.scale,
								y + 3 * gui.scale,
								tauon.album_mode_art_size + 11 * gui.scale,
								tauon.album_mode_art_size + 45 * gui.scale + 13 * gui.scale,
							)
							ddt.rect(
								(
									x,
									y,
									tauon.album_mode_art_size,
									tauon.album_mode_art_size + 45 * gui.scale,
								),
								colours.grey(250),
							)

						# White background needs extra border
						if colours.lm and not card_mode:
							ddt.rect_a(
								(x - 2, y - 2),
								(tauon.album_mode_art_size + 4, tauon.album_mode_art_size + 4),
								colours.grey(200),
							)

						if a == row_len - 1:
							gui.gallery_scroll_field_left = max(
								x + tauon.album_mode_art_size, window_size[0] - round(50 * gui.scale)
							)

						# Skip if the selection highlight is drawn over this album,
						# so the two highlights don't show at the same time
						selection_highlight_shown = (
							(gui.album_tab_mode or gallery_menu.active) and info[2] is True
						)
						highlight_border = round(3 * gui.scale)
						if info[0] == 1 and not selection_highlight_shown and (
							pctl.playing_state in (PlayingState.PLAYING, PlayingState.PAUSED)
						):
							ddt.rect_a(
								(x - highlight_border, y - highlight_border),
								(tauon.album_mode_art_size + highlight_border * 2, tauon.album_mode_art_size + highlight_border * 2),
								colours.gallery_highlight,
							)
							# ddt.rect_a((x, y), (tauon.album_mode_art_size, tauon.album_mode_art_size),
							#            colours.gallery_background, True)

						# Draw quick add highlight
						if pctl.quick_add_target:
							pl = pctl.id_to_pl(pctl.quick_add_target)
							if (
								pl is not None
								and pctl.default_playlist[tauon.album_dex[album_on]]
								in pctl.multi_playlist[pl].playlist_ids
							):
								c = ColourRGBA(110, 233, 90, 255)
								if colours.lm:
									c = ColourRGBA(66, 244, 66, 255)
								ddt.rect_a(
									(x - highlight_border, y - highlight_border),
									(tauon.album_mode_art_size + highlight_border * 2, tauon.album_mode_art_size + highlight_border * 2),
									c,
								)

						# Draw transcode highlight
						if tauon.transcode_list and os.path.isdir(prefs.encoder_output):
							tr = False

							if encode_folder_name(track) in os.listdir(prefs.encoder_output):
								tr = True
							else:
								for folder in tauon.transcode_list:
									if (
										pctl.get_track(folder[0]).parent_folder_path
										== track.parent_folder_path
									):
										tr = True
										break
							if tr:
								c = ColourRGBA(244, 212, 66, 255)
								if colours.lm:
									c = ColourRGBA(244, 64, 244, 255)
								ddt.rect_a(
									(x - highlight_border, y - highlight_border),
									(tauon.album_mode_art_size + highlight_border * 2, tauon.album_mode_art_size + highlight_border * 2),
									c,
								)
								# ddt.rect_a((x, y), (tauon.album_mode_art_size, tauon.album_mode_art_size),
								#            colours.gallery_background, True)

						# Draw selection

						if (gui.album_tab_mode or gallery_menu.active) and info[2] is True:
							c = colours.gallery_highlight
							c = ColourRGBA(c.g, c.b, c.r, c.a)
							ddt.rect_a(
								(x - highlight_border, y - highlight_border),
								(tauon.album_mode_art_size + highlight_border * 2, tauon.album_mode_art_size + highlight_border * 2),
								c,
							)  # [150, 80, 222, 255]
							# ddt.rect_a((x, y), (tauon.album_mode_art_size, tauon.album_mode_art_size),
							#            colours.gallery_background, True)

						# Draw selection animation
						if (
							gui.gallery_animate_highlight_on == tauon.album_dex[album_on]
							and tauon.gallery_select_animate_timer.get() < 1.5
						):
							t = tauon.gallery_select_animate_timer.get()
							c = colours.gallery_highlight
							if t < 0.2:
								a = int(255 * (t / 0.2))
							elif t < 0.5:
								a = 255
							else:
								a = int(255 - 255 * (t - 0.5))

							c = ColourRGBA(c.g, c.b, c.r, a)
							animate_border = round(3 * gui.scale)
							ddt.rect_a(
								(x - animate_border, y - animate_border),
								(tauon.album_mode_art_size + animate_border * 2, tauon.album_mode_art_size + animate_border * 2),
								c,
							)  # [150, 80, 222, 255]

							gui.request_frame()

						# Draw faint outline
						ddt.rect(
							(x - 1, y - 1, tauon.album_mode_art_size + 2, tauon.album_mode_art_size + 2),
							ColourRGBA(255, 255, 255, 11),
						)

						if gui.album_tab_mode or gallery_menu.active:
							if info[2] is False and info[0] != 1 and not colours.lm:
								ddt.rect_a(
									(x, y),
									(tauon.album_mode_art_size, tauon.album_mode_art_size),
									ColourRGBA(0, 0, 0, 110),
								)
								albumtitle = colours.grey(160)

						elif info[0] != 1 and pctl.playing_state != PlayingState.STOPPED and prefs.dim_art:
							ddt.rect_a(
								(x, y),
								(tauon.album_mode_art_size, tauon.album_mode_art_size),
								ColourRGBA(0, 0, 0, 110),
							)
							albumtitle = colours.grey(160)

						# Determine meta info
						singles = False
						artists = 0
						last_album = ""
						last_artist = ""
						s = 0
						ones = 0
						for id in album:
							tr = pctl.get_track(pctl.default_playlist[id])
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
						back_colour = ColourRGBA(40, 40, 40, 50)
						if colours.lm:
							back_colour = ColourRGBA(10, 10, 10, 15)

						back_colour = alpha_blend(ColourRGBA(10, 10, 10, 15), colours.gallery_background)

						ddt.rect_a(
							(x, y), (tauon.album_mode_art_size, tauon.album_mode_art_size), back_colour
						)

						# Draw album art
						if singles:
							dia = math.sqrt(tauon.album_mode_art_size * tauon.album_mode_art_size * 2)
							ran = dia * 0.25
							off = (dia - ran) / 2
							albs = min(len(album), 5)
							spacing = ran / (albs - 1)
							size = round(tauon.album_mode_art_size * 0.5)

							i = 0
							for p in album[:albs]:
								pp = spacing * i
								pp += off
								xx = pp / math.sqrt(2)

								xx -= size / 2
								drawn_art = tauon.gall_ren.render(
									pctl.get_track(pctl.default_playlist[p]),
									(x + xx, y + xx),
									size=size,
									force_offset=0,
								)
								if not drawn_art:
									g = 50 + round(100 / albs) * i
									ddt.rect((x + xx, y + xx, size, size), ColourRGBA(g, g, g, 100))
								drawn_art = True
								i += 1
						else:
							album_count += 1
							if (album_count * 1.5) + 10 > tauon.gall_ren.limit:
								tauon.gall_ren.limit = round((album_count * 1.5) + 30)
							drawn_art = tauon.gall_ren.render(track, (x, y))

						# Determine mouse collision
						rect = (
							x,
							y,
							tauon.album_mode_art_size,
							tauon.album_mode_art_size + extend * gui.scale,
						)
						m_in = (
							tauon.coll(rect)
							and gui.panelY < inp.mouse_position[1] < window_size[1] - gui.panelBY
						)
						tauon.fields.add(rect)

						# Draw mouse-over highlight
						if (not gallery_menu.active and m_in) or (gallery_menu.active and info[2]):
							if tauon.is_level_zero():
								ddt.rect(rect, ColourRGBA(255, 255, 255, 10))

						if drawn_art is False and gui.gallery_show_text is False:
							ddt.text(
								(
									x + int(tauon.album_mode_art_size / 2),
									y + tauon.album_mode_art_size - 22 * gui.scale,
									2,
								),
								pctl.master_library[
									pctl.default_playlist[tauon.album_dex[album_on]]
								].parent_folder_name,
								colours.gallery_artist_line,
								13,
								tauon.album_mode_art_size - 15 * gui.scale,
								bg=alpha_blend(back_colour, colours.gallery_background),
							)

						if prefs.art_bg and drawn_art:
							rect = sdl3.SDL_FRect(
								round(x), round(y), tauon.album_mode_art_size, tauon.album_mode_art_size
							)
							if rect.y < gui.panelY:
								diff = round(gui.panelY - rect.y)
								rect.y += diff
								rect.h -= diff
							elif (rect.y + rect.h) > window_size[1] - gui.panelBY:
								diff = round((rect.y + rect.h) - (window_size[1] - gui.panelBY))
								rect.h -= diff

							if rect.h > 0:
								tauon.style_overlay.hole_punches.append(rect)

						# # Drag over highlight
						# if inp.quick_drag and gui.playlist_hold and inp.mouse_down:
						# 	rect = (x, y, tauon.album_mode_art_size, tauon.album_mode_art_size + extend * gui.scale)
						# 	m_in = tauon.coll(rect) and gui.panelY < inp.mouse_position[1] < window_size[1] - gui.panelBY
						# 	if m_in:
						# 		ddt.rect_a((x, y), (tauon.album_mode_art_size, tauon.album_mode_art_size), [120, 10, 255, 100], True)

						if gui.gallery_show_text:
							c_index = pctl.default_playlist[tauon.album_dex[album_on]]
							if c_index in gui.album_artist_dict:
								pass
							else:
								i = tauon.album_dex[album_on]
								if pctl.master_library[pctl.default_playlist[i]].album_artist:
									gui.album_artist_dict[c_index] = pctl.master_library[
										pctl.default_playlist[i]
									].album_artist
								else:
									while i < len(pctl.default_playlist):
										if (
											pctl.master_library[pctl.default_playlist[i]].parent_folder_name
											!= pctl.master_library[
												pctl.default_playlist[tauon.album_dex[album_on]]
											].parent_folder_name
										):
											gui.album_artist_dict[c_index] = pctl.master_library[
												pctl.default_playlist[tauon.album_dex[album_on]]
											].artist
											break
										if (
											pctl.master_library[pctl.default_playlist[i]].artist
											!= pctl.master_library[
												pctl.default_playlist[tauon.album_dex[album_on]]
											].artist
										):
											gui.album_artist_dict[c_index] = _("Various Artists")
											break
										i += 1
									else:
										gui.album_artist_dict[c_index] = pctl.master_library[
											pctl.default_playlist[tauon.album_dex[album_on]]
										].artist

							line = gui.album_artist_dict[c_index]
							line2 = pctl.master_library[
								pctl.default_playlist[tauon.album_dex[album_on]]
							].album
							if singles:
								line2 = pctl.master_library[
									pctl.default_playlist[tauon.album_dex[album_on]]
								].parent_folder_name
								if artists > 1:
									line = _("Various Artists")

							text_align = 0
							if prefs.center_gallery_text:
								x += tauon.album_mode_art_size // 2
								text_align = 2
							elif card_mode:
								x += round(6 * gui.scale)

							if card_mode:
								if line2 == "":
									ddt.text(
										(x, y + tauon.album_mode_art_size + 8 * gui.scale, text_align),
										line,
										line1_colour,
										310,
										tauon.album_mode_art_size - 18 * gui.scale,
									)
								else:
									ddt.text(
										(x, y + tauon.album_mode_art_size + 7 * gui.scale, text_align),
										line2,
										line2_colour,
										311,
										tauon.album_mode_art_size - 18 * gui.scale,
									)

									ddt.text(
										(
											x,
											y + tauon.album_mode_art_size + (10 + 14) * gui.scale,
											text_align,
										),
										line,
										line1_colour,
										10,
										tauon.album_mode_art_size - 18 * gui.scale,
									)
							elif line2 == "":
								ddt.text(
									(x, y + tauon.album_mode_art_size + 9 * gui.scale - text_lift, text_align),
									line,
									line1_colour,
									311,
									tauon.album_mode_art_size - 5 * gui.scale,
								)
							else:
								ddt.text(
									(x, y + tauon.album_mode_art_size + 8 * gui.scale - text_lift, text_align),
									line2,
									line2_colour,
									211 if grid_edge else 212,
									tauon.album_mode_art_size - (round(5 * gui.scale) if grid_edge else 0),
								)

								ddt.text(
									(x, y + tauon.album_mode_art_size + (10 + 14) * gui.scale - artist_lift, text_align),
									line,
									line1_colour,
									311,
									tauon.album_mode_art_size - 5 * gui.scale,
								)

						album_on += 1

					if album_on > len(tauon.album_dex):
						break
					render_pos += tauon.album_mode_art_size + gui.album_v_gap

			# POWER TAG BAR --------------

			if gui.pt > 0:  # gui.pt > 0 or (gui.power_bar is not None and len(gui.power_bar) > 1):
				top = gui.panelY
				run_y = top + 1

				hot_r = (window_size[0] - 47 * gui.scale, top, 45 * gui.scale, h)
				tauon.fields.add(hot_r)

				if gui.pt == 0:  # mouse moves in
					if tauon.coll(hot_r) and window_is_focused(t_window):
						gui.pt_on.set()
						gui.pt = 1
				elif gui.pt == 1:  # wait then trigger if stays, reset if goes out
					if not tauon.coll(hot_r):
						gui.pt = 0
					elif gui.pt_on.get() > 0.2:
						gui.pt = 2

						off = 0
						for item in gui.power_bar:
							item.ani_timer.force_set(off)
							off -= 0.005

				elif gui.pt == 2:  # wait to turn off
					if tauon.coll(hot_r):
						gui.pt_off.set()
					if gui.pt_off.get() > 0.6 and not lightning_menu.active:
						gui.pt = 3

						off = 0
						for item in gui.power_bar:
							item.ani_timer.force_set(off)
							off -= 0.01

				done = True
				# Animate tags on
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
						gui.request_frame()

				# Keep draw loop running while on
				if gui.pt > 0:
					gui.request_frame()

				# Draw tags

				block_h = round(27 * gui.scale)
				block_gap = 1 * gui.scale
				if gui.scale == 1.25:
					block_gap = 1

				if tauon.coll(hot_r) or gui.pt > 0:
					for i, item in enumerate(gui.power_bar):
						if run_y + block_h > top + h:
							break

						rect = [window_size[0] - item.peak_x, run_y, 7 * gui.scale, block_h]
						i_rect = [window_size[0] - 36 * gui.scale, run_y, 34 * gui.scale, block_h]
						tauon.fields.add(i_rect)

						if (
							tauon.coll(i_rect)
							or (lightning_menu.active and lightning_menu.reference == item)
						) and item.peak_x == 9 * gui.scale:
							if (
								not lightning_menu.active
								or lightning_menu.reference == item
								or inp.right_click
							):
								minx = 100 * gui.scale
								maxx = minx * 2

								ww = ddt.get_text_w(item.name, 213)

								w = max(minx, ww)
								w = min(maxx, w)

								ddt.rect(
									(rect[0] - w - 25 * gui.scale, run_y, w + 26 * gui.scale, block_h),
									ColourRGBA(230, 230, 230, 255),
								)
								ddt.text(
									(rect[0] - 10 * gui.scale, run_y + 5 * gui.scale, 1),
									item.name,
									ColourRGBA(5, 5, 5, 255),
									213,
									w,
									bg=ColourRGBA(230, 230, 230, 255),
								)

								if inp.mouse_click:
									tauon.goto_album(item.position)
								if inp.right_click:
									lightning_menu.activate(
										item,
										position=(
											window_size[0] - 180 * gui.scale,
											rect[1] + rect[3] + 5 * gui.scale,
										),
									)
								if inp.middle_click:
									tauon.path_stem_to_playlist(item.path, item.name)

						ddt.rect(rect, item.colour)
						run_y += block_h + block_gap

			tauon.gallery_pulse_top.render(
				window_size[0] - gui.rspw, gui.panelY, gui.rspw - round(16 * gui.scale), 20 * gui.scale
			)
		except Exception:
			logging.exception("Gallery render error!")
		finally:
			sdl3.SDL_SetRenderClipRect(tauon.renderer, None)
		# END POWER BAR ------------------------

	tauon.gallery_render = render_gallery  # exposed for the Custom Layout Album Gallery widget

	def update_tracklist_scrollbar_lock(hitbox) -> bool:
		"""The tracklist scroll bar's interaction lock (moved verbatim from the
		input phase of the main loop): while the pointer is in the bar's hitbox
		and pressed, the bar owns interaction — unless the pointer is over an
		album-rating star (gui.album_rating_hover), in which case the bar
		yields. Updates gui.scrollbar_interaction_lock and gui.scrollbar_active
		(read by the playlist body input, e.g. to disable rating input while
		scrolling); returns the suppressed-by-album-rating flag. Shared with
		the Custom Layout Tracklist widget, which passes its segment's hitbox.
		"""
		scrollbar_pointer_in_area = tauon.coll(hitbox)
		if not scrollbar_pointer_in_area:
			gui.scrollbar_interaction_lock = False
		elif (
			not gui.album_rating_hover
			and (
				inp.mouse_click
				or inp.right_click
				or (inp.mouse_down and coll_point(inp.click_location, hitbox))
			)
		):
			gui.scrollbar_interaction_lock = True
		gui.scrollbar_active = scroll_hold or gui.scrollbar_interaction_lock
		return (
			gui.album_rating_hover
			and not scroll_hold
			and not gui.scrollbar_interaction_lock
		)

	tauon.tracklist_scrollbar_lock = update_tracklist_scrollbar_lock  # for the Tracklist widget

	def render_tracklist_scrollbar(left, plw, top, bottom, ey) -> None:
		"""The tracklist scroll bar: auto-hide (shows on hover / while
		scrolling), thumb drag, continuous click-slide above/below the thumb,
		right-click jump, and the album-rating suppression. Moved verbatim from
		the main loop with the geometry parameterized: left/plw = tracklist
		left edge/width, top/bottom = the bar's vertical span, ey = the thumb
		travel limit (the preset passes its historical window-based value).
		The Custom Layout Tracklist widget calls this with segment geometry.
		Thumb state (scroll_hold etc.) is the shared main-loop state — only one
		tracklist bar exists at a time (preset and widget never run together).
		"""
		nonlocal scroll_hold, scroll_point, scroll_bpoint, sbp, sbl
		width = 15 * gui.scale

		# When the columns header bar is shown, drop the scroll bar (and its
		# auto-hide/hover field) below the header so it doesn't overlap it. Only
		# the top moves; the thumb travel simply shrinks from the top.
		if gui.set_bar and gui.set_mode:
			top += gui.set_height

		if gui.set_mode and prefs.left_align_album_artist_title:
			width = 11 * gui.scale
		scroll_hitbox_width = 28 * gui.scale
		if prefs.tracklist_scrollbar_left:
			x = left + 1 * gui.scale
			scroll_hitbox_x = x - 1 * gui.scale
		else:
			x = left + plw - width - 3 * gui.scale
			scroll_hitbox_x = x + width + 1 * gui.scale - scroll_hitbox_width

		gui.scroll_hide_box = (
			scroll_hitbox_x,
			top,
			scroll_hitbox_width,
			bottom - top,
		)

		scrollbar_hidden_by_album_rating = (
			gui.album_rating_hover
			and not scroll_hold
			and not gui.scrollbar_interaction_lock
		)
		if not scrollbar_hidden_by_album_rating:
			tauon.fields.add(gui.scroll_hide_box)
		if not scrollbar_hidden_by_album_rating and not prefs.show_nag and (
			tauon.scroll_hide_timer.get() < 0.9 or (
				(tauon.coll(gui.scroll_hide_box) or scroll_hold or gui.quick_search_mode)
				and not menu_is_open()
				and not pref_box.enabled
				and not gui.rename_playlist_box
				and gui.layer_focus == 0
				and gui.show_playlist
				and not tauon.search_over.active
			)
		):
			scroll_opacity = 255

			if not gui.combo_mode:
				if len(pctl.default_playlist) < 50:
					sbl = 85 * gui.scale
					if len(pctl.default_playlist) == 0:
						sbp = top
				else:
					sbl = 105 * gui.scale

				tauon.fields.add((scroll_hitbox_x, sbp, scroll_hitbox_width, sbl))
				if (
					tauon.coll((scroll_hitbox_x, top, scroll_hitbox_width, ey - top))
					and (inp.mouse_down or inp.right_click)
					and coll_point(inp.click_location, (scroll_hitbox_x, top, scroll_hitbox_width, ey - top))
				):
					gui.request_tracklist_redraw()
					if inp.right_click:
						sbp = inp.mouse_position[1] - int(sbl / 2)
						if sbp + sbl > ey:
							sbp = ey - sbl
						elif sbp < top:
							sbp = top
						per = (sbp - top) / (ey - top - sbl)
						pctl.playlist_view_position = int(len(pctl.default_playlist) * per)
						gui.playlist_scroll_pixels = 0
						logging.debug("Position set by scroll bar (right click)")
						pctl.playlist_view_position = max(pctl.playlist_view_position, 0)

					elif inp.mouse_click:
						if inp.mouse_position[1] < sbp:
							gui.scroll_direction = -1
						elif inp.mouse_position[1] > sbp + sbl:
							gui.scroll_direction = 1
						else:
							tauon.input_sdl.mouse_capture_want = True

							scroll_hold = True
							scroll_point = inp.mouse_position[1]
							scroll_bpoint = sbp
					else:
						if sbp < inp.mouse_position[1] < sbp + sbl:
							gui.scroll_direction = 0
						pctl.playlist_view_position += gui.scroll_direction * 2
						gui.playlist_scroll_pixels = 0
						logging.debug("Position set by scroll bar (slide)")
						pctl.playlist_view_position = max(pctl.playlist_view_position, 0)
						pctl.playlist_view_position = min(
							pctl.playlist_view_position, len(pctl.default_playlist)
						)

						if sbp + sbl > ey:
							sbp = ey - sbl
						elif sbp < top:
							sbp = top

				if not inp.mouse_down:
					scroll_hold = False

				if scroll_hold and not inp.mouse_click:
					gui.request_tracklist_redraw()
					tauon.input_sdl.mouse_capture_want = True

					sbp = inp.mouse_position[1] - (scroll_point - scroll_bpoint)
					if sbp + sbl > ey:
						sbp = ey - sbl
					elif sbp < top:
						sbp = top
					per = (sbp - top) / (ey - top - sbl)
					pctl.playlist_view_position = int(len(pctl.default_playlist) * per)
					gui.playlist_scroll_pixels = 0
					logging.debug("Position set by scroll bar (drag)")

				elif len(pctl.default_playlist) > 0:
					per = (pctl.playlist_view_position + (gui.playlist_scroll_pixels / max(gui.playlist_row_height, 1))) / len(pctl.default_playlist)
					sbp = int((ey - top - sbl) * per) + top + 1

				bg = ColourRGBA(255, 255, 255, 6)
				fg = colours.scroll_colour

				if colours.lm:
					bg = ColourRGBA(200, 200, 200, 100)
					fg = ColourRGBA(100, 100, 100, 200)

				ddt.rect_a((x, top), (width + 1 * gui.scale, bottom - top), bg)
				ddt.rect_a((x + 1, sbp), (width, sbl), alpha_mod(fg, scroll_opacity))

				if (
					tauon.coll((scroll_hitbox_x, sbp, scroll_hitbox_width, sbl)) and inp.mouse_position[0] != 0
				) or scroll_hold:
					ddt.rect_a((x + 1 * gui.scale, sbp), (width, sbl), ColourRGBA(255, 255, 255, 19))

	tauon.tracklist_scrollbar_render = render_tracklist_scrollbar  # for the Tracklist widget

	def render_column_bar_input() -> None:
		# Columns (set mode) header-bar INPUT: grip resize, label drag/sort,
		# right-click menus. Reads gui.playlist_left/plw/panelY so it can run
		# against either the preset layout or a Tracklist widget's segment.
		top = gui.panelY
		if gui.artist_info_panel and not gui.custom_mode:
			top += gui.artist_panel_height

		if gui.set_mode and not gui.set_bar:
			left = gui.playlist_left
			rect = [left, top, gui.plw, 12 * gui.scale]
			if inp.right_click and tauon.coll(rect):
				tauon.set_menu_hidden.activate()
				inp.right_click = False

		width = gui.plw
		if gui.set_bar and gui.set_mode:
			left = gui.playlist_left

			if gui.tracklist_center_mode:
				left = gui.tracklist_inset_left - round(20 * gui.scale)
				width = gui.tracklist_inset_width + round(20 * gui.scale)

			rect = [left, top, width, gui.set_height]
			start = left + gui.pl_st_left * gui.scale
			run = 0
			in_grip = False

			if not inp.mouse_down and gui.set_hold != -1:
				gui.set_hold = -1

			for h, item in enumerate(gui.pl_st):
				box = (start + run, rect[1], item[1], rect[3])
				grip = (start + run, rect[1], 3 * gui.scale, rect[3])
				m_grip = (grip[0] - 4 * gui.scale, grip[1], grip[2] + 8 * gui.scale, grip[3])
				l_grip = (grip[0] + 9 * gui.scale, grip[1], box[2] - 14 * gui.scale, grip[3])
				tauon.fields.add(m_grip)

				if tauon.coll(l_grip):
					if inp.mouse_up and gui.set_label_hold != -1:
						if point_distance(inp.mouse_position, gui.set_label_point) < 8 * gui.scale:
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
									tauon.sort_ass(h)
								else:
									tauon.sort_ass(h, True)
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

								gui.request_tracklist_redraw()
								gui.set_label_hold = -1
								# logging.info("MOVE")
								break

							gui.set_label_hold = -1

					if inp.mouse_click:
						gui.set_label_hold = h
						gui.set_label_point = copy.deepcopy(inp.mouse_position)
					if inp.right_click:
						tauon.set_menu.reference = h
						tauon.sa_regen_menu()
						tauon.set_menu.activate(h)

				if h == 0:
					# The first grip has no column to its left; it instead
					# drags the leading inset (gui.pl_st_left), shifting the
					# whole column block left/right.
					if tauon.coll(m_grip):
						in_grip = True
						if inp.mouse_click:
							gui.set_hold = 0
							gui.set_point = inp.mouse_position[0]
							gui.set_old = gui.pl_st_left

					if inp.mouse_down and gui.set_hold == 0:
						# pl_st_left is stored pre-scale, so convert the pixel
						# drag delta back to base units.
						gui.pl_st_left = gui.set_old + (inp.mouse_position[0] - gui.set_point) / gui.scale
						# Keep a small minimum so the grip stays grabbable and
						# doesn't slip off the left edge of the window.
						gui.pl_st_left = max(gui.pl_st_left, 2)

						gui.request_frame()

						total = 0
						for i in range(len(gui.pl_st) - 1):
							total += gui.pl_st[i][1]

						wid = gui.plw - round(gui.pl_st_left * gui.scale)
						if gui.tracklist_center_mode:
							wid = gui.tracklist_highlight_width - round(gui.pl_st_left * gui.scale)
						gui.pl_st[len(gui.pl_st) - 1][1] = wid - total
				else:
					if tauon.coll(m_grip):
						in_grip = True
						if inp.mouse_click:
							gui.set_hold = h
							gui.set_point = inp.mouse_position[0]
							gui.set_old = gui.pl_st[h - 1][1]

					if inp.mouse_down and gui.set_hold == h:
						gui.pl_st[h - 1][1] = gui.set_old + (inp.mouse_position[0] - gui.set_point)
						gui.pl_st[h - 1][1] = max(gui.pl_st[h - 1][1], 25)

						gui.request_frame()
						# gui.pl_update = 1

						total = 0
						for i in range(len(gui.pl_st) - 1):
							total += gui.pl_st[i][1]

						wid = gui.plw - round(gui.pl_st_left * gui.scale)
						if gui.tracklist_center_mode:
							wid = gui.tracklist_highlight_width - round(gui.pl_st_left * gui.scale)
						gui.pl_st[len(gui.pl_st) - 1][1] = wid - total

				run += item[1]

			# A right-click on the bar was handled above (column menu on a label,
			# otherwise ignored); consume it so the tracklist body beneath the bar
			# doesn't also treat it as a track right-click. In the preset the bar
			# sits above the rows so this is a no-op; in the Custom Layout Tracklist
			# widget the bar and body share the segment.
			if inp.right_click and tauon.coll(rect):
				inp.right_click = False

			if not inp.mouse_down:
				gui.set_label_hold = -1
			# logging.info(in_grip)
			if gui.set_label_hold == -1:
				if (
					in_grip
					and not tauon.x_menu.active
					and not tauon.view_menu.active
					and not tab_menu.active
					and not tauon.set_menu.active
				):
					gui.cursor_want = 1
				if gui.set_hold != -1:
					gui.cursor_want = 1
					gui.pl_update_on_drag = True
	tauon.column_bar_input = render_column_bar_input

	def render_column_bar_draw() -> None:
		# Columns (set mode) header-bar DRAWING (and the hover strip that
		# re-shows a hidden bar). Must run AFTER the tracklist body so it sits
		# on top; the widget calls it post-body, the preset does the same.
		top = gui.panelY
		if gui.artist_info_panel and not gui.custom_mode:
			top += gui.artist_panel_height

		if not gui.set_bar and gui.set_mode and not gui.combo_mode:
			width = gui.plw
			left = gui.playlist_left
			if gui.tracklist_center_mode:
				left = gui.tracklist_highlight_left
				width = gui.tracklist_highlight_width
			rect = [left, top, width, gui.set_height // 2.5]
			tauon.fields.add(rect)
			gui.delay_frame(0.26)

			if tauon.coll(rect) and gui.bar_hover_timer.get() > 0.25:
				ddt.rect(rect, colours.column_bar_background)
				if inp.mouse_click:
					gui.set_bar = True
					tauon.update_layout_do()
			if not tauon.coll(rect):
				gui.bar_hover_timer.set()

		if gui.set_bar and gui.set_mode and not gui.combo_mode:
			x = gui.playlist_left

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

			# At low art strength the surrounding panels are fairly opaque
			# and the (translucent) bar reads too bright against them; add
			# an extra layer. High strength keeps the lighter look.
			if gui.have_art_bg and prefs.art_bg_stronger < 3:
				if gui.tracklist_center_mode:
					ddt.rect((0, top, window_size[0], gui.set_height), c_bar_background)
				else:
					ddt.rect(rect, c_bar_background)

			start = x + gui.pl_st_left * gui.scale
			c_width = width - gui.pl_st_left * gui.scale

			# The column cells below re-fill the (translucent) bar colour on
			# top of the base fill; give the lead-in strip before the first
			# column the same second layer so it doesn't read brighter
			ddt.rect((x, top, start - x, gui.set_height), c_bar_background)

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

				if tauon.coll(box) and gui.set_label_hold != -1:
					bg = ColourRGBA(39, 39, 39, 255)

				if i == gui.set_label_hold:
					bg = ColourRGBA(22, 22, 22, 255)

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
					gui.heart_row_icon.render(
						box[0] + 9 * gui.scale, top + 8 * gui.scale, colours.column_bar_text
					)
				else:
					ddt.text(
						(box[0] + 10 * gui.scale, top + 4 * gui.scale),
						line,
						colours.column_bar_text,
						312,
						bg=bg,
						max_w=box[2] - 25 * gui.scale,
					)

				run += box[2]

			t = gui.column_sort_ani_timer.get()
			if t < 0.30:
				gui.request_frame()
				x = round(gui.column_sort_ani_x - 22 * gui.scale)
				p = t / 0.30

				if gui.column_sort_ani_direction == 1:
					y = top + 8 * p + 3 * gui.scale
					gui.column_sort_down_icon.render(x, round(y), ColourRGBA(255, 255, 255, 90))
				else:
					p = 1 - p
					y = top + 8 * p + 2 * gui.scale
					gui.column_sort_up_icon.render(x, round(y), ColourRGBA(255, 255, 255, 90))
	tauon.column_bar_draw = render_column_bar_draw

	render_heartbeat_timer = Timer()
	loop_pace_timer = Timer()

	tauon.set_tray_icons()
	if prefs.use_tray or "--tray" in sys.argv:
		tauon.show_tray()

	if (prefs.start_in_tray and prefs.use_tray) or "--tray" in sys.argv:
		tauon.min_to_tray()

	while pctl.running:
		# Pace the loop to the display refresh rate: sleep off whatever part of
		# the frame budget wasn't already consumed by work, a vsync-blocked
		# present or an idle event wait. All frame-rate pacing lives here.
		excess = tauon.frame_pace() - loop_pace_timer.get()
		if excess > 0:
			time.sleep(excess)
		loop_pace_timer.set()

		tauon.update_sdl_tray()
		# bm.get('main')
		# time.sleep(100)

		if inp.k_input:
			keymaps.hits.clear()

			inp.d_mouse_click = False
			inp.right_click = False
			inp.level_2_right_click = False
			inp.middle_click = False
			inp.mouse_up = False
			inp.key_return_press = False
			inp.key_down_press = False
			inp.key_up_press = False
			inp.key_right_press = False
			inp.key_left_press = False
			inp.key_esc_press = False
			inp.key_del = False
			inp.backspace_press = 0
			inp.key_backspace_press = False
			inp.key_tab_press = False
			inp.key_c_press = False
			inp.key_v_press = False
			inp.key_a_press = False
			inp.key_s_press = False
			inp.key_z_press = False
			inp.key_x_press = False
			inp.key_home_press = False
			inp.key_end_press = False
			inp.mouse_wheel = 0
			inp.mouse_wheel_precise = False
			inp.touch_scroll_y = 0
			inp.touch_released = False
			pref_box.scroll = 0
			gui.new_playlist_cooldown = False
			inp.input_text = ""
			inp.level_2_enter = False

			mouse_enter_window = False
			gui.mouse_in_window = True
			if inp.key_focused:
				inp.key_focused -= 1

		# f not inp.mouse_down:
		inp.k_input = False
		inp.global_clicked = False
		focused = False
		mouse_moved = False
		gui.level_2_click = False
		inp.mouse_click = False
		# gui.update = 2

		while sdl3.SDL_PollEvent(ctypes.byref(event)) != 0:
			# if event.type == sdl3.SDL_SYSWMEVENT:
			#      logging.info(event.syswm.msg.contents) # Not implemented by pysdl2

			if event.type == sdl3.SDL_EVENT_GAMEPAD_ADDED:
				if not prefs.use_gamepad:
					continue
				if sdl3.SDL_IsGamepad(event.gdevice.which):
					sdl3.SDL_OpenGamepad(event.gdevice.which)
					try:
						logging.info(
							f"Found game controller: {sdl3.SDL_GetGamepadNameForID(event.gdevice.which).decode()}"
						)
					except Exception:
						logging.exception("Error getting game controller")
			elif event.type == sdl3.SDL_EVENT_GAMEPAD_AXIS_MOTION:
				if not prefs.use_gamepad:
					continue
				if event.gaxis.axis == sdl3.SDL_GAMEPAD_AXIS_LEFT_TRIGGER:
					rt = event.gaxis.value > 5000
				elif event.gaxis.axis == sdl3.SDL_GAMEPAD_AXIS_LEFTY:
					if event.gaxis.value < -10000:
						new = -1
					elif event.gaxis.value > 10000:
						new = 1
					else:
						new = 0
					if new != c_yax:
						c_yax_timer.force_set(1)
						c_yax = new
						gui.request_frame()
				elif event.gaxis.axis == sdl3.SDL_GAMEPAD_AXIS_RIGHTX:
					if event.gaxis.value < -15000:
						new = -1
					elif event.gaxis.value > 15000:
						new = 1
					else:
						new = 0
					if new != c_xax:
						c_xax_timer.force_set(1)
						c_xax = new
						gui.request_frame()
				elif event.gaxis.axis == sdl3.SDL_GAMEPAD_AXIS_RIGHTY:
					if event.gaxis.value < -15000:
						new = -1
					elif event.gaxis.value > 15000:
						new = 1
					else:
						new = 0
					if new != c_xay:
						c_xay_timer.force_set(1)
						c_xay = new
						gui.request_frame()
			elif event.type == sdl3.SDL_EVENT_GAMEPAD_BUTTON_DOWN:
				if not prefs.use_gamepad:
					continue
				inp.k_input = True
				gui.request_frame()
				# print(event.gbutton.button)
				if event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER:
					if rt:
						tauon.toggle_random()
					else:
						pctl.advance()
				elif event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_LEFT_SHOULDER:
					if rt:
						tauon.toggle_repeat()
					else:
						pctl.back()
				elif event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_SOUTH:
					if rt:
						pctl.show_current(highlight=True)
					elif (
						pctl.playing_ready()
						and pctl.active_playlist_playing == pctl.active_playlist_viewing
						and pctl.selected_ready()
						and pctl.default_playlist[pctl.selected_in_playlist] == pctl.playing_object().index
					):
						pctl.play_pause()
					else:
						inp.key_return_press = True
				elif event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_WEST:
					if rt:
						tauon.random_track()
					else:
						tauon.toggle_gallery_keycontrol(always_exit=True)
				elif event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_NORTH:
					if rt:
						pctl.advance(rr=True)
					else:
						pctl.play_pause()
				elif event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_EAST:
					if rt:
						pctl.revert()
					elif tauon.is_level_zero():
						pctl.stop()
					else:
						inp.key_esc_press = True
				elif event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_DPAD_UP:
					inp.key_up_press = True
				elif event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_DPAD_DOWN:
					inp.key_down_press = True
				elif event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_DPAD_LEFT:
					if gui.album_tab_mode:
						inp.key_left_press = True
					elif (tauon.is_level_zero() or gui.quick_search_mode) and not gui.timed_lyrics_editing_now:
						pctl.cycle_playlist_pinned(1)
				elif event.gbutton.button == sdl3.SDL_GAMEPAD_BUTTON_DPAD_RIGHT:
					if gui.album_tab_mode:
						inp.key_right_press = True
					elif (tauon.is_level_zero() or gui.quick_search_mode) and not gui.timed_lyrics_editing_now:
						pctl.cycle_playlist_pinned(-1)
			elif event.type == sdl3.SDL_EVENT_RENDER_TARGETS_RESET:
				if not tauon.windows:
					reset_render = True
				gui.request_tracklist_redraw()
				gui.request_frame()
			elif event.type == sdl3.SDL_EVENT_DROP_TEXT:

				link = event.drop.data.decode("utf-8", errors="surrogateescape")
				# logging.info(link)

				if pctl.playing_ready() and link.startswith("http"):
					if sdl3.SDL_version >= 204:
						gmp = get_global_mouse()
						gwp = get_window_position(t_window)
						i_x = gmp[0] - gwp[0]
						i_x = max(i_x, 0)
						i_x = min(i_x, window_size[0])
						i_y = gmp[1] - gwp[1]
						i_y = max(i_y, 0)
						i_y = min(i_y, window_size[1])
					else:
						i_y = pointer(c_int(0))
						i_x = pointer(c_int(0))

						sdl3.SDL_GetMouseState(i_x, i_y)
						i_y = i_y.contents.value / logical_size[0] * window_size[0]
						i_x = i_x.contents.value / logical_size[0] * window_size[0]

					if coll_point((i_x, i_y), gui.main_art_box):
						logging.info("Drop picture...")
						# logging.info(link)
						gui.image_downloading = True
						track = pctl.playing_object()
						target_dir = track.parent_folder_path

						shoot_dl = threading.Thread(target=tauon.download_img, args=(link, target_dir, track))
						shoot_dl.daemon = True
						shoot_dl.start()

						gui.request_frame()

				elif link.startswith("file:///"):
					link = link.replace("\r", "")
					for line in link.split("\n"):
						target = str(urllib.parse.unquote(line)).replace("file:///", "/")
						tauon.drop_file(target)
			elif event.type == sdl3.SDL_EVENT_DROP_BEGIN:
				gui.ext_drop_mode = True
			elif event.type == sdl3.SDL_EVENT_DROP_POSITION:
				inp.mouse_position[0] = int(event.drop.x / logical_size[0] * window_size[0])
				inp.mouse_position[1] = int(event.drop.y / logical_size[0] * window_size[0])
				mouse_moved = True
				gui.mouse_unknown = False
				gui.ext_drop_mode = True
				gui.request_tracklist_redraw()
				gui.request_frame()
			elif event.type == sdl3.SDL_EVENT_DROP_COMPLETE:
				gui.ext_drop_mode = False
			elif event.type == sdl3.SDL_EVENT_DROP_FILE:
				gui.ext_drop_mode = False
				dropped_file_sdl = event.drop.data
				inp.mouse_position[0] = int(event.drop.x / logical_size[0] * window_size[0])
				inp.mouse_position[1] = int(event.drop.y / logical_size[0] * window_size[0])
				logging.info(f"Dropped data: {dropped_file_sdl}")
				target = (
					str(urllib.parse.unquote(dropped_file_sdl.decode("utf-8", errors="surrogateescape")))
					.replace("file:///", "/")
					.replace("\r", "")
				)
				# logging.info(target)
				tauon.drop_file(target)

			elif event.type == sdl3.SDL_EVENT_QUIT:

				if gui.tray_active and prefs.min_to_tray and not inp.key_shift_down:
					tauon.min_to_tray()
				else:
					tauon.exit("Window received exit signal")
					break
			elif event.type == sdl3.SDL_EVENT_TEXT_EDITING:
				# logging.info("edit text")
				gui.editline = event.edit.text
				# logging.info(gui.editline)
				gui.editline = gui.editline.decode("utf-8", "ignore")
				inp.k_input = True
				gui.request_frame()

			elif event.type == sdl3.SDL_EVENT_MOUSE_MOTION:
				mp = tauon.menu_popup_for_window(event.motion.windowID)
				if mp is not None:
					# Motion inside a menu popup (main or submenu): track it in that
					# window's own local pixel space and mark it the active pointer
					# window. It must never touch the main window's mouse_position.
					mp.last_local = (int(event.motion.x * mp.scale), int(event.motion.y * mp.scale))
					tauon.active_pointer_window = mp
					gui.request_frame()
				elif event.motion.windowID == sdl3.SDL_GetWindowID(tauon.t_window):
					inp.mouse_position[0] = int(event.motion.x / logical_size[0] * window_size[0])
					inp.mouse_position[1] = int(event.motion.y / logical_size[0] * window_size[0])
					mouse_moved = True
					gui.mouse_unknown = False
					# Pointer is over the main window, not a menu popup, so no menu
					# popup is the active pointer window - prevents a popup menu from
					# hit-testing against a stale popup-local position.
					tauon.active_pointer_window = None
				# else: motion from a hidden/closed popup or other window - ignore.
			elif event.type == sdl3.SDL_EVENT_MOUSE_BUTTON_DOWN:
				inp.k_input = True
				focused = True
				gui.request_frame()
				gui.mouse_in_window = True

				if ggc == 2:  # dont click on first full frame
					continue

				# Route button events for visible menu popups the same way as motion.
				# A press inside either popup (main or submenu) drives the menu
				# normally. A press anywhere else dismisses the menu but is allowed
				# to fall through to the main UI - matching the original in-window
				# menus, where clicking away also activated whatever was under the
				# cursor (e.g. the companion view switcher). close_all_menus()
				# deactivates the menu first, so the click-transfer block below
				# won't feed the click to a now-closed menu. Menus dismissed here
				# are flagged so a toggle button under the cursor doesn't treat
				# the same click as "open again".
				for menu in Menu.instances:
					menu.click_dismissed = False
				if tauon.menu_popup is not None and tauon.menu_popup.visible \
						and tauon.menu_popup_for_window(event.button.windowID) is None:
					for menu in Menu.instances:
						if menu.active:
							menu.click_dismissed = True
					close_all_menus()
					tauon.close_menu_popup()

				if event.button.button == sdl3.SDL_BUTTON_RIGHT:
					inp.right_click = True
					inp.right_down = True
					# logging.info("RIGHT DOWN")
				elif event.button.button == sdl3.SDL_BUTTON_LEFT:
					# logging.info("LEFT DOWN")

					# if inp.mouse_position[1] > 1 and inp.mouse_position[0] > 1:
					#     inp.mouse_down = True

					inp.mouse_click = True

					inp.mouse_down = True
				elif event.button.button == sdl3.SDL_BUTTON_MIDDLE:
					inp.middle_click = True
					gui.request_frame()
				elif event.button.button == sdl3.SDL_BUTTON_X1:
					keymaps.hits.append("MB4")
				elif event.button.button == sdl3.SDL_BUTTON_X2:
					keymaps.hits.append("MB5")
			elif event.type == sdl3.SDL_EVENT_MOUSE_BUTTON_UP:
				inp.k_input = True
				gui.request_frame()
				if event.button.button == sdl3.SDL_BUTTON_RIGHT:
					inp.right_down = False
				elif event.button.button == sdl3.SDL_BUTTON_LEFT:
					# Only a release on the main window records a main-window mouse-up; a
					# release inside the menu popup uses popup-local coords and must not
					# drive main drag logic or corrupt mouse_up_position.
					if inp.mouse_down and event.button.windowID == sdl3.SDL_GetWindowID(tauon.t_window):
						inp.mouse_up = True
						inp.mouse_up_position[0] = event.motion.x / logical_size[0] * window_size[0]
						inp.mouse_up_position[1] = event.motion.y / logical_size[0] * window_size[0]

					inp.mouse_down = False
					gui.request_frame()
			elif event.type == sdl3.SDL_EVENT_KEY_DOWN:
				if inp.key_focused != 0:
					continue
				inp.k_input = True
				gui.request_frame()
				if prefs.use_scancodes:
					keymaps.hits.append(event.key.scancode)
				else:
					keymaps.hits.append(event.key.key)

				if prefs.use_scancodes:
					if event.key.scancode == sdl3.SDL_SCANCODE_V:
						inp.key_v_press = True
					elif event.key.scancode == sdl3.SDL_SCANCODE_A:
						inp.key_a_press = True
					elif event.key.scancode == sdl3.SDL_SCANCODE_S:
						inp.key_s_press = True
					elif event.key.scancode == sdl3.SDL_SCANCODE_C:
						inp.key_c_press = True
					elif event.key.scancode == sdl3.SDL_SCANCODE_Z:
						inp.key_z_press = True
					elif event.key.scancode == sdl3.SDL_SCANCODE_X:
						inp.key_x_press = True
				elif event.key.key == sdl3.SDLK_V:
					inp.key_v_press = True
				elif event.key.key == sdl3.SDLK_A:
					inp.key_a_press = True
				elif event.key.key == sdl3.SDLK_S:
					inp.key_s_press = True
				elif event.key.key == sdl3.SDLK_C:
					inp.key_c_press = True
				elif event.key.key == sdl3.SDLK_Z:
					inp.key_z_press = True
				elif event.key.key == sdl3.SDLK_X:
					inp.key_x_press = True

				if (event.key.key in (sdl3.SDLK_RETURN, sdl3.SDLK_RETURN2) and len(gui.editline) == 0) or (
					event.key.key == sdl3.SDLK_KP_ENTER and len(gui.editline) == 0
				):
					inp.key_return_press = True
				elif event.key.key == sdl3.SDLK_TAB:
					inp.key_tab_press = True
				elif event.key.key == sdl3.SDLK_BACKSPACE:
					inp.backspace_press += 1
					inp.key_backspace_press = True
				elif event.key.key == sdl3.SDLK_DELETE:
					inp.key_del = True
				elif event.key.key == sdl3.SDLK_RALT:
					inp.key_ralt = True
				elif event.key.key == sdl3.SDLK_LALT:
					inp.key_lalt = True
				elif event.key.key == sdl3.SDLK_DOWN:
					inp.key_down_press = True
				elif event.key.key == sdl3.SDLK_UP:
					inp.key_up_press = True
				elif event.key.key == sdl3.SDLK_LEFT:
					inp.key_left_press = True
				elif event.key.key == sdl3.SDLK_RIGHT:
					inp.key_right_press = True
				elif event.key.key == sdl3.SDLK_LSHIFT:
					inp.key_shift_down = True
				elif event.key.key == sdl3.SDLK_RSHIFT:
					inp.key_shiftr_down = True
				elif event.key.key == sdl3.SDLK_LCTRL:
					inp.key_ctrl_down = True
				elif event.key.key == sdl3.SDLK_RCTRL:
					inp.key_rctrl_down = True
				elif event.key.key == sdl3.SDLK_HOME:
					inp.key_home_press = True
				elif event.key.key == sdl3.SDLK_END:
					inp.key_end_press = True
				elif event.key.key == sdl3.SDLK_LGUI:
					if macos:
						inp.key_ctrl_down = True
					else:
						inp.key_meta = True
						inp.key_focused = 1

			elif event.type == sdl3.SDL_EVENT_KEY_UP:
				inp.k_input = True
				gui.request_frame()
				if event.key.key == sdl3.SDLK_LSHIFT:
					inp.key_shift_down = False
				elif event.key.key == sdl3.SDLK_LCTRL:
					inp.key_ctrl_down = False
				elif event.key.key == sdl3.SDLK_RCTRL:
					inp.key_rctrl_down = False
				elif event.key.key == sdl3.SDLK_RSHIFT:
					inp.key_shiftr_down = False
				elif event.key.key == sdl3.SDLK_RALT:
					gui.album_tab_mode = False
					inp.key_ralt = False
				elif event.key.key == sdl3.SDLK_LALT:
					gui.album_tab_mode = False
					inp.key_lalt = False
				elif event.key.key == sdl3.SDLK_LGUI:
					if macos:
						inp.key_ctrl_down = False
					else:
						inp.key_meta = False
						inp.key_focused = 1

			elif event.type == sdl3.SDL_EVENT_TEXT_INPUT:
				inp.k_input = True
				inp.input_text += event.text.text.decode("utf-8")

				gui.request_frame()
				# logging.info(inp.input_text)

			elif event.type == sdl3.SDL_EVENT_MOUSE_WHEEL:
				inp.k_input = True
				now = time.monotonic()
				wheel_before = inp.mouse_wheel
				raw_scroll_y = event.wheel.y
				integer_scroll_y = event.wheel.integer_y
				smooth_enabled = tauon.smooth_scroll.enabled()
				precise_input = smooth_enabled and (macos or raw_scroll_y != integer_scroll_y)
				scroll_y = raw_scroll_y if smooth_enabled else float(integer_scroll_y)
				event_mode = "precise-smooth" if precise_input else "smooth" if smooth_enabled else "line"
				if event_mode != inp.scroll_debug_last_mode or now - inp.scroll_debug_last_log > 1.0:
					# logging.debug(
					# 	"Wheel event mode=%s raw_y=%.3f integer_y=%d scroll_y=%.3f smooth_enabled=%s precise_input=%s speed=%.3f wheel_before=%.3f mouse=(%d,%d)",
					# 	event_mode,
					# 	raw_scroll_y,
					# 	integer_scroll_y,
					# 	scroll_y,
					# 	smooth_enabled,
					# 	precise_input,
					# 	tauon.smooth_scroll.speed(),
					# 	wheel_before,
					# 	inp.mouse_position[0],
					# 	inp.mouse_position[1],
					# )
					inp.scroll_debug_last_mode = event_mode
					inp.scroll_debug_last_log = now
				inp.mouse_wheel += scroll_y
				# if logging.getLogger().isEnabledFor(logging.DEBUG):
				# 	logging.debug(
				# 		"Wheel event accumulate mode=%s scroll_y=%.3f wheel_after=%.3f",
				# 		event_mode,
				# 		scroll_y,
				# 		inp.mouse_wheel,
				# 	)
				inp.mouse_wheel_precise = precise_input
				inp.trackpad_scroll_mode_until = 0.0

				gui.request_frame()
			# this is where tap and scroll and rightclick and dragndrop happens
			# use active_touch to track because i cant be bothered figuring out the systems we already have lol
			elif event.type == sdl3.SDL_EVENT_FINGER_DOWN:
				if inp.active_touch_id is None:
					inp.active_touch_id = event.tfinger.fingerID
				if event.tfinger.fingerID == inp.active_touch_id:
					inp.mouse_click = False
					inp.mouse_down = False
					# those two have to be canceled until we're sure we want them
					inp.mouse_up = False
					inp.k_input = True
					inp.touch_active = True
					active_touch.is_down = True
					active_touch.time_started_ns = time.monotonic_ns()
					inp.touch_released = False
					inp.touch_position[0] = int(event.tfinger.x * window_size[0])
					active_touch.x = int(event.tfinger.x * window_size[0])
					inp.touch_position[1] = int(event.tfinger.y * window_size[1])
					active_touch.y = int(event.tfinger.y * window_size[1])
					active_touch.start_position_px = (inp.touch_position[0], inp.touch_position[1])
					tauon.smooth_scroll.start_location = active_touch.start_position_px
					gui.request_frame()
				elif active_touch.is_down and active_touch.duration_so_far_ns < 100 * 1000000:
					active_touch.is_gesture = True
			elif event.type == sdl3.SDL_EVENT_FINGER_MOTION:
				# i assume here that nobody can keep their finger totally steady
				# if i'm wrong, touch states will need to be evaluated in a separate section
				if inp.active_touch_id is None:
					inp.active_touch_id = event.tfinger.fingerID
				if event.tfinger.fingerID == inp.active_touch_id:
					if active_touch.is_gesture:
						pass
					else:
						inp.k_input = True
						inp.touch_active = True
						inp.touch_position[0] = int(event.tfinger.x * window_size[0])
						active_touch.x = int(event.tfinger.x * window_size[0])
						inp.touch_position[1] = int(event.tfinger.y * window_size[1])
						active_touch.y = int(event.tfinger.y * window_size[1])
						active_touch.duration_so_far_ns = time.monotonic_ns() - active_touch.time_started_ns

						if active_touch.is_scroll:
							# regular scrolling
							inp.touch_scroll_y += event.tfinger.dy * window_size[1]
							mouse_moved = True
							gui.request_tracklist_redraw()

						elif active_touch.has_moved or abs(inp.touch_position[1] - active_touch.start_position_px[1]) > SCROLL_PHYSICS_MIN_PIXELS*gui.scale:
							# if touch position has MOVED,
							active_touch.has_moved = True
							if active_touch.duration_so_far_ns < TOUCH_LOGIC_TAP_VS_LONG_NS:
								# it could be a scroll input
								active_touch.is_scroll = True
								inp.touch_scroll_y += inp.touch_position[1] - active_touch.start_position_px[1]
								mouse_moved = True
							elif active_touch.is_rightclick:
								# or it could be switching from right click to dragndrop
								active_touch.is_rightclick = False
								active_touch.is_dragndrop = True
								gui.set_drag_source()
								inp.mouse_down = True
								inp.mouse_up = False
								inp.mouse_click = True
								mouse_moved = True

						elif active_touch.duration_so_far_ns > TOUCH_LOGIC_TAP_VS_LONG_NS and not (active_touch.is_rightclick or active_touch.is_dragndrop):
							# if it HASN'T moved in the given time, it's at least a rightclick
							active_touch.start_position_px = (inp.touch_position[0], inp.touch_position[1])
							active_touch.is_rightclick = True

						gui.request_frame()
			elif event.type in (sdl3.SDL_EVENT_FINGER_UP, sdl3.SDL_EVENT_FINGER_CANCELED):
				if event.tfinger.fingerID == inp.active_touch_id:
					inp.k_input = True
					inp.touch_active = False
					inp.mouse_up = True
					inp.touch_position[0] = int(event.tfinger.x * window_size[0])
					inp.touch_position[1] = int(event.tfinger.y * window_size[1])
					inp.active_touch_id = None
					if not active_touch.is_gesture:
						if not active_touch.was_gesture:
							if active_touch.is_rightclick:
								inp.right_click = True
							elif active_touch.is_dragndrop:
								inp.mouse_down = False
							elif active_touch.is_scroll:
								inp.touch_released = True
							else:
								inp.mouse_click = True
						active_touch.reset()
					else:
						if inp.touch_position[0] - active_touch.start_position_px[0] > TOUCH_LOGIC_COOL_GESTURE_PIXELS_TO_SKIP_TRACK:
							pctl.advance()
						elif inp.touch_position[0] - active_touch.start_position_px[0] < -TOUCH_LOGIC_COOL_GESTURE_PIXELS_TO_SKIP_TRACK:
							pctl.back()
						else:
							pctl.play_pause()
						gest = active_touch.was_gesture
						active_touch.reset()
						if not gest:
							active_touch.was_gesture = True
					gui.request_frame()
				else: # bugfix regarding the order you lift off your fingers during gesture
					if active_touch.is_gesture:
						active_touch.was_gesture = True
			elif event.type >= sdl3.SDL_EVENT_WINDOW_FIRST and event.type <= sdl3.SDL_EVENT_WINDOW_LAST:
				# logging.info(event.type)

				# These handlers all act on the main window (resize, focus,
				# layout, etc.). Ignore window events from secondary windows such
				# as the menu popup - otherwise e.g. a popup resize fires
				# WINDOW_RESIZED and overwrites the main window's logical_size,
				# corrupting all main-window mouse-coordinate scaling.
				if event.window.windowID != sdl3.SDL_GetWindowID(tauon.t_window):
					continue

				if event.type == sdl3.SDL_EVENT_WINDOW_FOCUS_GAINED:
					# logging.info("sdl3.SDL_WINDOWEVENT_FOCUS_GAINED")

					if not macos and not tauon.windows:
						tauon.gnome.focus()
					inp.k_input = True

					mouse_enter_window = True
					focused = True
					gui.lowered = False
					inp.key_focused = 1
					inp.mouse_down = False
					gui.album_tab_mode = False
					gui.request_tracklist_redraw()
					gui.request_frame()

				elif event.type == sdl3.SDL_EVENT_WINDOW_FOCUS_LOST:
					# The menu popup is non-focusable, so showing it never steals
					# focus from the main window; a FOCUS_LOST here is a genuine
					# app deactivation, so close any open menu (and hide its popup
					# so it does not linger over other apps).
					close_all_menus()
					tauon.close_menu_popup()  # no-op if nothing is open
					inp.key_focused = 1
					gui.request_frame()

				elif event.type == sdl3.SDL_EVENT_WINDOW_CLOSE_REQUESTED:
					# Alt+F4 / taskbar-close arrive as a close request on the main
					# window. SDL never promotes that to SDL_EVENT_QUIT while an
					# SDL tray icon is active (the app is expected to decide close
					# behaviour itself, e.g. minimize-to-tray), so the close
					# request must be handled here directly.
					if gui.tray_active and prefs.min_to_tray and not inp.key_shift_down:
						tauon.min_to_tray()
					else:
						tauon.exit("Main window received close request")
						break

				elif event.type == sdl3.SDL_EVENT_WINDOW_DISPLAY_CHANGED:
					# sdl3.SDL_WINDOWEVENT_DISPLAY_CHANGED logs new display ID as data1 (0 or 1 or 2...), it not width, and data 2 is always 0
					pass
				elif event.type == sdl3.SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED:
					i_x = pointer(c_int(0))
					i_y = pointer(c_int(0))
					sdl3.SDL_GetWindowSizeInPixels(t_window, i_x, i_y)
					window_size[0] = i_x.contents.value
					window_size[1] = i_y.contents.value
					auto_scale(bag)
					gui.update_layout = True
					gui.request_frame()
				elif event.type == sdl3.SDL_EVENT_WINDOW_RESIZED:
					# sdl3.SDL_WINDOWEVENT_RESIZED logs width to data1 and height to data2
					# if event.window.data1 < 500:
					# 	logging.error("Window width is less than 500, grrr why does this happen, stupid bug")
					# 	sdl3.SDL_SetWindowSize(t_window, logical_size[0], logical_size[1])
					# elif tauon.restore_ignore_timer.get() > 1:  # Hacky
					# 	gui.update = 2

					# 	logical_size[0] = event.window.data1
					# 	logical_size[1] = event.window.data2

					# 	if gui.mode != GuiMode.MINI:
					# 		logical_size[0] = max(300, logical_size[0])
					# 		logical_size[1] = max(300, logical_size[1])

					gui.request_frame()
					logical_size[0] = event.window.data1
					logical_size[1] = event.window.data2
					# auto_scale(bag)
					# gui.update_layout = True

				elif event.type == sdl3.SDL_EVENT_WINDOW_MOUSE_ENTER:
					# logging.info("ENTER")
					mouse_enter_window = True
					gui.mouse_in_window = True
					gui.request_frame()

				# elif event.type == sdl3.SDL_WINDOWEVENT_HIDDEN:
				#
				elif event.type == sdl3.SDL_EVENT_WINDOW_EXPOSED:
					# logging.info("expose")
					gui.lowered = False

				elif event.type == sdl3.SDL_EVENT_WINDOW_MINIMIZED:
					gui.lowered = True
					# if prefs.min_to_tray:
					# 	tray.down()
					# tauon.thread_manager.sleep()

				elif event.type == sdl3.SDL_EVENT_WINDOW_RESTORED:
					gui.lowered = False
					gui.maximized = False
					gui.request_tracklist_redraw()
					gui.request_frame()

					if prefs.update_title:
						tauon.update_title_do()
						# logging.info("restore")

				elif event.type == sdl3.SDL_EVENT_WINDOW_SHOWN:
					focused = True
					gui.request_tracklist_redraw()
					gui.request_frame()

				# elif event.type == sdl3.SDL_WINDOWEVENT_FOCUS_GAINED:
				#     logging.info("FOCUS GAINED")
				#     # input.mouse_enter_event = True
				#     # gui.update += 1
				#     # inp.k_input = True

				elif event.type == sdl3.SDL_EVENT_WINDOW_MAXIMIZED:
					if gui.mode != GuiMode.MINI:  # TODO(Taiko): workaround. sdl bug? gives event on window size set
						gui.maximized = True
					gui.update_layout = True
					gui.request_tracklist_redraw()
					gui.request_frame()

				elif event.type == sdl3.SDL_EVENT_WINDOW_MOUSE_LEAVE:
					gui.mouse_in_window = False
					gui.request_frame()

		if mouse_moved and tauon.fields.test():
			gui.request_frame()

		# if tauon.thread_manager.sleeping:
		#     if not gui.lowered:
		#         tauon.thread_manager.wake()
		if gui.lowered:
			gui.update = False
		# ----------------
		# This section decides whether this iteration runs the full frame body.
		# run_frame is recomputed from scratch every pass; anything that wants
		# processing or rendering this iteration sets it. Frame-rate pacing is
		# handled centrally at the top of the loop.
		# if not gui.pl_update and gui.rendered_playlist_position != pctl.playlist_view_position:
		#     logging.warning("The playlist failed to render at the latest position!!!!")

		run_frame = False

		if pctl.playerCommandReady and tauon.thread_manager.player_lock.locked():
			try:
				tauon.thread_manager.player_lock.release()
			except RuntimeError as e:
				if str(e) == "release unlocked lock":
					logging.error("RuntimeError: Attempted to release already unlocked player_lock")  # noqa: TRY400
				else:
					logging.exception("Unknown RuntimeError trying to release player_lock")
			except Exception:
				logging.exception("Unknown exception trying to release player_lock")

		if gui.frame_callback_list:
			i = len(gui.frame_callback_list) - 1
			while i >= 0:
				if gui.frame_callback_list[i].test():
					gui.request_frame()
					run_frame = True
					del gui.frame_callback_list[i]
				i -= 1

		# Dream Room (F7): keep frames flowing while the 3D scene animates.
		# Only meaningful in the main GUI mode.
		if tauon.dream_room.active:
			if gui.mode != GuiMode.MAIN:
				tauon.dream_room.close_instant()
			else:
				gui.request_frame()
				run_frame = True

		# Milkdrop preset chooser: keep frames flowing so hover tracking on the
		# overlay stays live (the visualiser underneath is animating anyway).
		if tauon.milk_choose.active:
			if gui.mode != GuiMode.MAIN:
				tauon.milk_choose.close()
			else:
				gui.request_frame()
				run_frame = True

		if tauon.animate_monitor_timer.get() < 1 or tauon.load_orders:
			if tauon.cursor_blink_timer.get() > 0.65:
				tauon.cursor_blink_timer.set()
				TextBox.cursor ^= True
				gui.request_frame()

			if inp.k_input:
				tauon.cursor_blink_timer.set()
				TextBox.cursor = True

			run_frame = True

		if inp.mouse_wheel or inp.k_input or gui.pl_update or gui.update or tauon.top_panel.adds:  # or mouse_moved:
			run_frame = True

		if not tauon.smooth_scroll.enabled():
			tauon.smooth_scroll.reset_disabled_motion()

		if tauon.smooth_scroll.any_active():
			run_frame = True
			gui.request_tracklist_redraw()
			gui.request_frame()
			now = time.monotonic()
			if tauon.scroll_animation_deadline <= 0:
				tauon.scroll_animation_deadline = now + SCROLL_ANIMATION_FRAME_INTERVAL
			elif now - tauon.scroll_animation_deadline > SCROLL_ANIMATION_FRAME_INTERVAL * 4:
				tauon.scroll_animation_deadline = now + SCROLL_ANIMATION_FRAME_INTERVAL

			frame_wait = tauon.scroll_animation_deadline - now
			if frame_wait > 0:
				time.sleep(frame_wait)
				now = time.monotonic()
			while tauon.scroll_animation_deadline <= now:
				tauon.scroll_animation_deadline += SCROLL_ANIMATION_FRAME_INTERVAL
		else:
			tauon.scroll_animation_deadline = 0.0

		if prefs.art_bg and tauon.core_timer.get() < 3:
			run_frame = True

		if (inp.mouse_down or active_touch.is_scroll or active_touch.is_dragndrop) and mouse_moved:
			run_frame = True
			if gui.update_on_drag:
				gui.request_frame()
			if gui.pl_update_on_drag:
				gui.request_tracklist_redraw()

		if pctl.wake_past_time and tauon.get_real_time() > pctl.wake_past_time:
			pctl.wake_past_time = 0
			run_frame = True
			gui.request_frame()

		# The level_update partial-present path (top-panel spectrum/level meter)
		# re-arms itself every iteration while playing, so it presents at the
		# loop rate — the central pacer caps that at the display refresh rate.
		if gui.level_update and not album_scroll_hold and not scroll_hold:
			run_frame = True

		if not pctl.running:
			break

		if tauon.requested_raise:
			tauon.raise_window()
			tauon.requested_raise = False

		if tauon.requested_tray_destruct:
			#logging.debug("Destroying tray as it was requested")
			tauon.destroy_sdl_tray()
			tauon.requested_tray_destruct = False
		if tauon.requested_tray:
			#logging.debug("Creating tray as it was requested")
			tauon.init_sdl_tray()
			tauon.requested_tray = False

		# Keep the frame body (seek-bar time tick, housekeeping) running while
		# something is playing; drawing stays gated on gui.update. Paused counts
		# as idle so the loop can drop into the deep-sleep wait below.
		if pctl.playing_state not in (PlayingState.STOPPED, PlayingState.PAUSED):
			run_frame = True

		# Keep the scrolling spectrogram rendering every frame; the central
		# pacer holds that at the display refresh rate.
		if gui.spectrogram_in_widget \
				and pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM):
			gui.request_frame()
			run_frame = True

		if prefs.milk and render_heartbeat_timer.get() > 5:
			# workaround for invis window bug?
			gui.request_tracklist_redraw()
			gui.request_frame()
			run_frame = True
			render_heartbeat_timer.set()

		if not run_frame:
			if (
				(pctl.playing_state in (PlayingState.STOPPED, PlayingState.PAUSED))
				and not tauon.load_orders
				and not gui.update
				and not tauon.gall_ren.queue
				and not tauon.transcode_list
				and not gui.frame_callback_list
			):
				pass
			else:
				tauon.sleep_timer.set()
			if tauon.sleep_timer.get() > 2:
				sdl3.SDL_WaitEventTimeout(None, 1000)
			continue

		gui.new_playlist_cooldown = False

		if prefs.auto_extract and prefs.monitor_downloads:
			tauon.dl_mon.scan()

		if inp.mouse_down and not tauon.coll((2, 2, window_size[0] - 4, window_size[1] - 4)):
			# logging.info(sdl3.SDL_GetMouseState(None, None))
			if sdl3.SDL_GetGlobalMouseState(None, None) == 0:
				inp.mouse_down = False
				inp.mouse_up = True
				inp.quick_drag = False

		# logging.info(window_size)
		# if window_size[0] / window_size[1] == 16 / 9:
		#     logging.info('OK')
		# if window_size[0] / window_size[1] > 16 / 9:
		#     logging.info("A")

		if inp.key_meta:
			inp.input_text = ""
			inp.k_input = False
			inp.key_return_press = False
			inp.key_tab_press = False

		if inp.k_input:
			if inp.mouse_click or inp.right_click or inp.mouse_up:
				inp.last_click_location = copy.deepcopy(inp.click_location)
				inp.click_location = copy.deepcopy(inp.mouse_position)

			if inp.key_focused != 0:
				keymaps.hits.clear()

				# inp.d_mouse_click = False
				# inp.right_click = False
				# inp.level_2_right_click = False
				# inp.mouse_click = False
				# inp.middle_click = False
				inp.mouse_up = False
				inp.key_return_press = False
				inp.key_down_press = False
				inp.key_up_press = False
				inp.key_right_press = False
				inp.key_left_press = False
				inp.key_esc_press = False
				inp.key_del = False
				inp.backspace_press = 0
				inp.key_backspace_press = False
				inp.key_tab_press = False
				inp.key_c_press = False
				inp.key_v_press = False
				# inp.key_f_press = False
				inp.key_a_press = False
				inp.key_s_press = False
				# inp.key_t_press = False
				inp.key_z_press = False
				inp.key_x_press = False
				inp.key_home_press = False
				inp.key_end_press = False
				inp.mouse_wheel = 0
				inp.mouse_wheel_precise = False
				inp.touch_scroll_y = 0
				inp.touch_released = False
				pref_box.scroll = 0
				inp.input_text = ""
				inp.level_2_enter = False

		if c_yax != 0:
			if c_yax_timer.get() >= 0:
				if c_yax == -1:
					inp.key_up_press = True
				if c_yax == 1:
					inp.key_down_press = True
				c_yax_timer.force_set(-0.01)
				gui.delay_frame(0.02)
				inp.k_input = True
		if c_xax != 0:
			if c_xax_timer.get() >= 0:
				if c_xax == 1:
					pctl.seek_time(pctl.playing_time + 2)
				if c_xax == -1:
					pctl.seek_time(pctl.playing_time - 2)
				c_xax_timer.force_set(-0.01)
				gui.delay_frame(0.02)
				inp.k_input = True
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
				inp.k_input = True

		text_entry_shortcuts_blocked = (
			gui.rename_folder_box
			or tauon.rename_track_box.active
			or gui.rename_playlist_box
			or radiobox.active
			or pref_box.enabled
			or tauon.trans_edit_box.active
			or gui.timed_lyrics_editing_now
			or tauon.export_playlist_box.active
		)

		if inp.k_input and inp.key_focused == 0:
			if text_entry_shortcuts_blocked and keymaps.hits:
				escape_pressed = keymaps.test("escape")
				keymaps.hits.clear()
				if escape_pressed:
					inp.key_esc_press = True
			elif gui.timed_lyrics_editing_now:
				keymaps.hits.clear()
			if keymaps.hits:
				n = 1
				while n < 10:
					if keymaps.test(f"jump-playlist-{n}"):
						if len(pctl.multi_playlist) > n - 1:
							pctl.switch_playlist(n - 1)
					n += 1

				if keymaps.test("cycle-playlist-left"):
					if gui.album_tab_mode and inp.key_left_press:
						pass
					elif tauon.is_level_zero() or gui.quick_search_mode:
						pctl.cycle_playlist_pinned(1)
				if keymaps.test("cycle-playlist-right"):
					if gui.album_tab_mode and inp.key_right_press:
						pass
					elif tauon.is_level_zero() or gui.quick_search_mode:
						pctl.cycle_playlist_pinned(-1)

				if keymaps.test("toggle-console"):
					tauon.console.toggle()

				if keymaps.test("toggle-fullscreen"):
					if not gui.fullscreen and gui.mode != GuiMode.MINI:
						gui.fullscreen = True
						sdl3.SDL_SetWindowFullscreenMode(t_window, None)
						sdl3.SDL_SetWindowFullscreen(t_window, True)
					elif gui.fullscreen:
						gui.fullscreen = False
						sdl3.SDL_SetWindowFullscreen(t_window, False)

				if keymaps.test("playlist-toggle-breaks"):
					# Toggle force off folder break for viewed playlist
					pctl.multi_playlist[pctl.active_playlist_viewing].hide_title ^= 1
					gui.request_tracklist_redraw()

				if keymaps.test("find-playing-artist"):
					# standard_size()
					if len(pctl.track_queue) > 0:
						gui.quick_search_mode = True
						tauon.search_over.search_text.text = ""
						inp.input_text = pctl.playing_object().artist

				if keymaps.test("show-encode-folder"):
					tauon.open_encode_out()

				if keymaps.test("toggle-left-panel"):
					gui.lsp ^= True
					tauon.update_layout_do()

				if keymaps.test("toggle-last-left-panel"):
					tauon.toggle_left_last()
					tauon.update_layout_do()

				if keymaps.test("escape"):
					inp.key_esc_press = True

			if inp.key_ctrl_down:
				gui.request_tracklist_redraw()

			if mouse_enter_window:
				inp.key_return_press = False

			if gui.fullscreen and inp.key_esc_press:
				gui.fullscreen = False
				sdl3.SDL_SetWindowFullscreen(t_window, 0)

			# Disable keys for text cursor control
			if not text_entry_shortcuts_blocked:
				# On macOS, the key labeled Delete reports as BACKSPACE in SDL.
				# Require Command+Backspace here so plain Backspace keeps its normal meaning.
				macos_delete_shortcut = macos and inp.key_ctrl_down and inp.key_backspace_press and not gui.quick_search_mode

				if not gui.quick_search_mode and not tauon.search_over.active:
					if (
						prefs.album_mode
						and gui.album_tab_mode
						and not inp.key_ctrl_down
						and not inp.key_meta
						and not inp.key_lalt
					):
						if inp.key_left_press:
							gal_left = True
							inp.key_left_press = False
						if inp.key_right_press:
							gal_right = True
							inp.key_right_press = False
						if inp.key_up_press:
							gal_up = True
							inp.key_up_press = False
						if inp.key_down_press:
							gal_down = True
							inp.key_down_press = False

				if not tauon.search_over.active:
					if inp.key_del or macos_delete_shortcut:
						close_all_menus()
						tauon.del_selected()

					# Arrow keys to change playlist
					if (inp.key_left_press or inp.key_right_press) and len(pctl.multi_playlist) > 1:
						gui.request_tracklist_redraw()
						gui.request_frame()

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
					gui.request_tracklist_redraw()

				if keymaps.test("goto-bottom"):
					n = len(pctl.default_playlist) - gui.playlist_view_length + 1
					n = max(n, 0)
					pctl.playlist_view_position = n
					logging.debug("Position changed by key")
					pctl.selected_in_playlist = len(pctl.default_playlist) - 1
					gui.request_tracklist_redraw()

			if not text_entry_shortcuts_blocked and not tauon.search_over.active and not gui.box_over:
				if gui.quick_search_mode:
					if keymaps.test("add-to-queue") and pctl.selected_ready():
						tauon.add_selected_to_queue()
						inp.input_text = ""
				else:
					if inp.key_c_press and inp.key_ctrl_down:
						gui.request_tracklist_redraw()
						tauon.s_copy()

					if inp.key_x_press and inp.key_ctrl_down:
						gui.request_tracklist_redraw()
						tauon.s_cut()

					if inp.key_v_press and inp.key_ctrl_down:
						gui.request_tracklist_redraw()
						tauon.paste()

					if keymaps.test("playpause"):
						pctl.play_pause()

			if inp.key_return_press and (gui.rename_folder_box or tauon.rename_track_box.active or radiobox.active):
				inp.key_return_press = False
				inp.level_2_enter = True

			if inp.key_ctrl_down and inp.key_z_press and not text_entry_shortcuts_blocked:
				tauon.undo.undo()

			if keymaps.test("quit"):
				tauon.exit("Quit keyboard shortcut pressed")

			if keymaps.test("testkey"):  # F7: unused
				pass

			if gui.mode == GuiMode.MAIN:
				if keymaps.test("toggle-auto-theme"):
					# Background styles are mutually exclusive; go through the
					# setters so the other modes get cleared
					if prefs.colour_from_image:
						tauon.set_bg_style_base()
						tauon.show_message(_("Disabled auto theme"))
					else:
						tauon.set_bg_style_colourise()
						tauon.show_message(_("Enabled auto theme"))

				if keymaps.test("transfer-playtime-to"):
					if (
						len(pctl.cargo) == 1
						and tauon.copied_track is not None
						and -1 < pctl.selected_in_playlist < len(pctl.default_playlist)
					):
						fr = pctl.get_track(tauon.copied_track)
						to = pctl.get_track(pctl.default_playlist[pctl.selected_in_playlist])

						fr_s = tauon.star_store.full_get(fr.index)
						to_s = tauon.star_store.full_get(to.index)

						fr_scr = fr.lfm_scrobbles
						to_scr = to.lfm_scrobbles

						tauon.undo.bk_playtime_transfer(fr, fr_s, fr_scr, to, to_s, to_scr)

						if to_s is None:
							to_s = StarRecord()
						if fr_s is None:
							fr_s = StarRecord()

						new = StarRecord()

						new.playtime = fr_s.playtime + to_s.playtime
						new.rating = fr_s.rating
						if to_s.rating > 0 and fr_s.rating == 0:
							new.rating = to_s.rating  # keep target rating
						to.lfm_scrobbles = fr.lfm_scrobbles

						tauon.star_store.remove(fr.index)
						tauon.star_store.remove(to.index)
						if new.playtime or new.rating:
							tauon.star_store.insert(to.index, new)

						tauon.copied_track = None
						gui.request_tracklist_redraw()
						logging.info("Transferred track stats!")
					elif tauon.copied_track is None:
						tauon.show_message(_("First select a source track by copying it into clipboard"))

				if keymaps.test("toggle-gallery"):
					tauon.toggle_album_mode()

				if keymaps.test("toggle-right-panel"):
					if gui.combo_mode:
						tauon.exit_combo()
					elif not prefs.album_mode:
						tauon.toggle_side_panel()
					else:
						tauon.toggle_album_mode()

				if keymaps.test("toggle-minimode"):
					tauon.set_mini_mode()
					gui.request_frame()

				if keymaps.test("cycle-layouts"):
					tauon.view_box.cycle()

				if keymaps.test("cycle-layouts-reverse"):
					tauon.view_box.cycle(reverse=True)

				if keymaps.test("toggle-columns"):
					tauon.view_box.col(True)

				if keymaps.test("toggle-artistinfo"):
					tauon.view_box.artist_info(True)

				if keymaps.test("toggle-showcase"):
					tauon.view_box.lyrics(True)

				if keymaps.test("toggle-gallery-keycontrol"):
					tauon.toggle_gallery_keycontrol()

				if keymaps.test("toggle-show-art"):
					tauon.toggle_side_art()

			elif gui.mode == GuiMode.MINI:
				if keymaps.test("toggle-minimode"):
					tauon.restore_full_mode()
					gui.request_frame()

			inp.ab_click = False

			if keymaps.test("new-playlist"):
				tauon.new_playlist()

			if keymaps.test("edit-generator"):
				tauon.edit_generator_box(pctl.active_playlist_viewing)

			if keymaps.test("new-generator-playlist"):
				tauon.new_playlist()
				tauon.edit_generator_box(pctl.active_playlist_viewing)

			if keymaps.test("delete-playlist"):
				pctl.delete_playlist(pctl.active_playlist_viewing)

			if keymaps.test("delete-playlist-force"):
				pctl.delete_playlist(pctl.active_playlist_viewing, force=True)

			if keymaps.test("rename-playlist"):
				if gui.radio_view:
					tauon.rename_playlist(pctl.radio_playlist_viewing)
				else:
					tauon.rename_playlist(pctl.active_playlist_viewing)
				tauon.rename_playlist_box.x = 60 * gui.scale
				tauon.rename_playlist_box.y = 60 * gui.scale

			# Dream Room: while the camera is out, intercept input before any
			# menu/box consumer so a click reliably flies it back in, and the
			# UI on the little monitor doesn't react to the muted mouse.
			if tauon.dream_room.active:
				tauon.dream_room.handle_input()

			# Milkdrop preset chooser: capture then mute the pointer before any
			# other consumer so clicks never leak through the overlay.
			if tauon.milk_choose.active:
				tauon.milk_choose.handle_input()

			# Transfer click register to menus
			if inp.mouse_click:
				for instance in Menu.instances:
					if instance.active:
						instance.click()
						inp.mouse_click = False
						inp.ab_click = True
				if tauon.view_box.active:
					tauon.view_box.clicked = True

			if inp.mouse_click and (
				prefs.show_nag
				or gui.box_over
				or radiobox.active
				or tauon.search_over.active
				or gui.rename_folder_box
				or gui.rename_playlist_box
				or tauon.rename_track_box.active
				or tauon.view_box.active
				or tauon.trans_edit_box.active
			):  # and not gui.message_box:
				inp.mouse_click = False
				gui.level_2_click = True
			else:
				gui.level_2_click = False

			if gui.track_box and inp.mouse_click:
				w = 540
				h = 240
				x = int(window_size[0] / 2) - int(w / 2)
				y = int(window_size[1] / 2) - int(h / 2)
				if tauon.coll([x, y, w, h]):
					inp.mouse_click = False
					gui.level_2_click = True

			if inp.right_click:
				inp.level_2_right_click = True

			if pref_box.enabled:
				if pref_box.inside():
					if inp.mouse_click:  # and not gui.message_box:
						pref_box.click = True
						inp.mouse_click = False
					if inp.right_click:
						inp.right_click = False
						pref_box.right_click = True

					pref_box.scroll = inp.mouse_wheel
					inp.mouse_wheel = 0
				else:
					if inp.mouse_click:
						inp.mouse_click = False
						pref_box.close()
					if inp.right_click:
						inp.right_click = False
						pref_box.close()
					if pref_box.lock is False:
						pass

			if inp.right_click and (
				radiobox.active
				or tauon.rename_track_box.active
				or gui.rename_playlist_box
				or gui.rename_folder_box
				or tauon.search_over.active
			):
				inp.right_click = False

			if inp.mouse_wheel != 0:
				gui.request_frame()
			if inp.mouse_down is True:
				gui.request_frame()

			if keymaps.test("pagedown"):  # key_PGD:
				if len(pctl.default_playlist) > 10:
					pctl.playlist_view_position += gui.playlist_view_length - 4
					if pctl.playlist_view_position >= len(pctl.default_playlist):
						pctl.playlist_view_position = len(pctl.default_playlist) - 2
					gui.request_tracklist_redraw()
					pctl.selected_in_playlist = pctl.playlist_view_position
					logging.debug("Position changed by page key")
					gui.shift_selection.clear()
			if keymaps.test("pageup"):
				if len(pctl.default_playlist) > 0:
					pctl.playlist_view_position -= gui.playlist_view_length - 4
					pctl.playlist_view_position = max(pctl.playlist_view_position, 0)
					gui.request_tracklist_redraw()
					pctl.selected_in_playlist = pctl.playlist_view_position
					logging.debug("Position changed by page key")
					gui.shift_selection.clear()

			if (
				gui.quick_search_mode is False
				and tauon.rename_track_box.active is False
				and gui.rename_folder_box is False
				and gui.rename_playlist_box is False
				and not pref_box.enabled
				and not radiobox.active
			):
				if keymaps.test("info-playing"):
					playing_track = pctl.playing_object()
					if playing_track is not None and playing_track.index in pctl.master_library:
						tauon.show_track_box(playing_track.index)

				if keymaps.test("info-show"):
					if pctl.selected_ready():
						tauon.show_track_box(pctl.get_track(pctl.default_playlist[pctl.selected_in_playlist]).index)

				# These need to be disabled when text fields are active
				if (
					not tauon.search_over.active
					and not gui.box_over
					and not radiobox.active
					and not gui.rename_folder_box
					and not tauon.rename_track_box.active
					and not gui.rename_playlist_box
					and not tauon.trans_edit_box.active
					and not gui.timed_lyrics_editing_now
				):
					if keymaps.test("advance"):
						inp.key_right_press = False
						pctl.advance()

					if keymaps.test("previous"):
						inp.key_left_press = False
						pctl.back()

					if inp.key_a_press and inp.key_ctrl_down:
						gui.request_tracklist_redraw()
						gui.shift_selection = list(range(len(pctl.default_playlist)))

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

					if keymaps.test("shift-down") and len(pctl.default_playlist) > 0:
						gui.request_tracklist_redraw()
						if pctl.selected_in_playlist > len(pctl.default_playlist) - 1:
							pctl.selected_in_playlist = 0

						if not gui.shift_selection:
							gui.shift_selection.append(pctl.selected_in_playlist)
						if pctl.selected_in_playlist < len(pctl.default_playlist) - 1:
							r = pctl.selected_in_playlist
							pctl.selected_in_playlist += 1
							if pctl.selected_in_playlist not in gui.shift_selection:
								gui.shift_selection.append(pctl.selected_in_playlist)
							else:
								gui.shift_selection.remove(r)

					if keymaps.test("shift-up") and pctl.selected_in_playlist > -1:
						gui.request_tracklist_redraw()
						pctl.selected_in_playlist = min(pctl.selected_in_playlist, len(pctl.default_playlist) - 1)

						if not gui.shift_selection:
							gui.shift_selection.append(pctl.selected_in_playlist)
						if pctl.selected_in_playlist > 0:
							r = pctl.selected_in_playlist
							pctl.selected_in_playlist -= 1
							if pctl.selected_in_playlist not in gui.shift_selection:
								gui.shift_selection.insert(0, pctl.selected_in_playlist)
							else:
								gui.shift_selection.remove(r)

					if keymaps.test("toggle-shuffle"):
						# pctl.random_mode ^= True
						tauon.toggle_random()

					if keymaps.test("goto-playing"):
						pctl.show_current()
					if keymaps.test("goto-previous"):
						if pctl.queue_step > 1:
							pctl.show_current(index=pctl.track_queue[pctl.queue_step - 1])

					if keymaps.test("toggle-repeat"):
						tauon.toggle_repeat()

					if keymaps.test("random-track"):
						tauon.random_track()

					if keymaps.test("random-album"):
						tauon.random_album()

					if keymaps.test("opacity-up"):
						prefs.window_opacity += 0.05
						prefs.window_opacity = min(prefs.window_opacity, 1)
						sdl3.SDL_SetWindowOpacity(t_window, prefs.window_opacity)

					if keymaps.test("opacity-down"):
						prefs.window_opacity -= 0.05
						prefs.window_opacity = max(prefs.window_opacity, 0.30)
						sdl3.SDL_SetWindowOpacity(t_window, prefs.window_opacity)

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
						tauon.bar_love(notify=True)

					if keymaps.test("love-selected"):
						tauon.select_love(notify=True)

					if keymaps.test("search-lyrics-selected"):
						if pctl.selected_ready():
							track = pctl.get_track(pctl.default_playlist[pctl.selected_in_playlist])
							if track.lyrics:
								tauon.show_message(_("Track already has lyrics"))
							else:
								tauon.get_lyric_wiki(track)

					if keymaps.test("substitute-search-selected"):
						if pctl.selected_ready():
							tauon.show_sub_search(pctl.get_track(pctl.default_playlist[pctl.selected_in_playlist]))

					if keymaps.test("global-search"):
						tauon.activate_search_overlay()

					if keymaps.test("add-to-queue") and pctl.selected_ready():
						tauon.add_selected_to_queue()

					if keymaps.test("clear-queue"):
						tauon.clear_queue()

					if keymaps.test("regenerate-playlist"):
						tauon.regenerate_playlist(pctl.active_playlist_viewing)

			if keymaps.test("cycle-theme"):
				gui.reload_theme = True
				gui.theme_temp_current = -1
				gui.temp_themes.clear()
				prefs.theme += 1

			if keymaps.test("cycle-theme-reverse"):
				gui.theme_temp_current = -1
				gui.temp_themes.clear()
				pref_box.previous_theme()

			if keymaps.test("reload-theme"):
				gui.reload_theme = True

		# if inp.mouse_position[1] < 1:
		#     inp.mouse_down = False

		if inp.mouse_down is False:
			scroll_hold = False

		# if focused is True:
		#     inp.mouse_down = False

		if inp.media_key:
			if inp.media_key == "Play":
				pctl.play_pause()
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
				tauon.toggle_repeat()
			elif inp.media_key == "Shuffle":
				tauon.toggle_random()

			inp.media_key = ""

		if len(tauon.load_orders) > 0:
			pctl.loading_in_progress = True
			pctl.after_import_flag = True
			tauon.thread_manager.ready("worker")
			if tauon.loaderCommand == LoaderCommand.NONE:
				# Filter out files matching CUE filenames
				# This isn't the only mechanism that does this. This one helps in the situation
				# where the user drags and drops multiple files at onec. CUEs in folders are handled elsewhere
				if len(tauon.load_orders) > 1:
					for order in tauon.load_orders:
						if order.stage == 0 and order.target.endswith(".cue"):
							for order2 in tauon.load_orders:
								if (
									not order2.target.endswith(".cue")
									and os.path.splitext(order2.target)[0] == os.path.splitext(order.target)[0]
									and os.path.isfile(order2.target)
								):
									order2.stage = -1
					for i in reversed(range(len(tauon.load_orders))):
						order = tauon.load_orders[i]
						if order.stage == -1:
							del tauon.load_orders[i]

				# Prepare loader thread with load order
				for order in tauon.load_orders:
					if order.stage == 0:
						order.target = order.target.replace("\\", "/")
						order.stage = 1
						if os.path.isdir(order.target):
							tauon.loaderCommand = LoaderCommand.FOLDER
						else:
							tauon.loaderCommand = LoaderCommand.FILE
							if order.target.endswith(".xspf"):
								gui.to_got = "xspf"
								gui.to_get = 0
							else:
								gui.to_got = 1
								gui.to_get = 1
						tauon.loaderCommandReady = True
						tauon.thread_manager.ready("worker")
						break

		elif pctl.loading_in_progress is True:
			pctl.loading_in_progress = False
			pctl.notify_database_changed()

		if tauon.loaderCommand == LoaderCommand.DONE:
			tauon.loaderCommand = LoaderCommand.NONE
			gui.request_frame()
			# gui.pl_update = 1
			# pctl.loading_in_progress = False

		if gui.update_layout:
			tauon.update_layout_do()
			gui.update_layout = False

		# if tauon.worker_save_state and\
		# 		not gui.pl_pulse and\
		# 		not pctl.loading_in_progress and\
		# 		not tauon.to_scan and\
		# 		not tauon.plex.scanning and\
		# 		not tauon.cm_clean_db and\
		# 		not tauon.lastfm.scanning_friends and\
		# 		not tauon.move_in_progress:
		# 	tauon.save_state()
		# 	cue_list.clear()
		# 	tauon.worker_save_state = False

		# -----------------------------------------------------
		# THEME SWITCHER--------------------------------------------------------------------

		if gui.reload_theme is True:
			gui.request_tracklist_redraw()
			theme_files = get_themes(dirs)

			if prefs.theme > len(theme_files):  # sic
				prefs.theme = 0

			if prefs.theme > 0:
				theme_number = prefs.theme - 1
				try:
					colours.column_colours.clear()
					colours.column_colours_playing.clear()

					theme_item = theme_files[theme_number]

					gui.theme_name = theme_item[1]
					colours.lm = False
					colours.__init__()

					load_theme(colours, Path(theme_item[0]))
					tauon.deco.load(colours.deco)
					logging.info(f"Applying theme: {gui.theme_name}")

					if colours.lm:
						gui.info_icon.colour = ColourRGBA(60, 60, 60, 255)
					else:
						gui.info_icon.colour = ColourRGBA(61, 247, 163, 255)

					if colours.lm:
						gui.folder_icon.colour = ColourRGBA(255, 190, 80, 255)
					else:
						gui.folder_icon.colour = ColourRGBA(244, 220, 66, 255)

					if colours.lm:
						gui.settings_icon.colour = ColourRGBA(85, 187, 250, 255)
					else:
						gui.settings_icon.colour = ColourRGBA(232, 200, 96, 255)

					if colours.lm:
						gui.radiorandom_icon.colour = ColourRGBA(120, 200, 120, 255)
					else:
						gui.radiorandom_icon.colour = ColourRGBA(153, 229, 133, 255)

				except Exception:
					logging.exception("Error loading theme file")
					tauon.show_message(_("Error loading theme file"), "", mode="warning")

			if prefs.theme == 0:
				gui.theme_name = "Mindaro"
				logging.info("Applying default theme: Mindaro")
				colours.lm = False
				colours.__init__()
				colours.post_config()
				tauon.deco.unload()

			if prefs.transparent_mode:
				colours.apply_transparency(full=prefs.transparent_mode == 2)

			prefs.theme_name = gui.theme_name

			# logging.info("Theme number: " + str(prefs.theme))
			gui.reload_theme = False
			ddt.text_background_colour = colours.playlist_panel_background
			# Re-apply art-bg panel translucency to the fresh colour objects
			gui.update_layout = True

			# With Colourise active, scan the current track's art over the
			# freshly loaded theme right away instead of waiting for album
			# art to next be drawn (cached temp themes embed the previous
			# base theme, so drop them)
			if prefs.colour_from_image:
				gui.theme_temp_current = -1
				gui.temp_themes.clear()
				colourise_track = pctl.playing_object()
				if colourise_track:
					tauon.album_art_gen.display(colourise_track, (0, 0), (50, 50), theme_only=True)

		# ---------------------------------------------------------------------------------------------------------
		# GUI DRAWING------
		# logging.info(gui.update)
		# logging.info(gui.lowered)
		if gui.mode == GuiMode.MINI:
			gui.pl_update = False

		if gui.pl_update and not gui.update:
			gui.request_frame()

		if gui.update and not resize_mode:
			# Flip the request flag off at the start of the frame: any
			# request_frame() made while drawing means "render another frame
			# after this one".
			gui.update = False
			tauon.gall_ren.new_frame()
			ddt.new_frame()

			if reset_render:
				logging.info("Reset render targets!")
				tauon.clear_img_cache(delete_disk=False)
				ddt.clear_text_cache()
				tauon.destroy_corner_textures()
				for item in WhiteModImageAsset.assets:
					item.reload()
				reset_render = False

			sdl3.SDL_SetRenderTarget(renderer, None)
			sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_NONE)
			sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
			sdl3.SDL_RenderClear(renderer)
			sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)
			sdl3.SDL_RenderClear(renderer)
			sdl3.SDL_SetRenderTarget(renderer, gui.main_texture)
			sdl3.SDL_RenderClear(renderer)

			# Blurred album art background: drawn first so all panels and
			# text composite on top of it (panel colours are made translucent
			# in update_layout_do while this is active)
			gui.have_art_bg = prefs.art_bg and gui.mode == GuiMode.MAIN
			if gui.have_art_bg:
				tauon.style_overlay.display(background=True)

			# tauon.perf_timer.set()
			gui.update_on_drag = False
			gui.pl_update_on_drag = False

			# inp.mouse_position[0], inp.mouse_position[1] = tauon.input_sdl.mouse()
			gui.showed_title = False

			if (
				not gui.ext_drop_mode
				and not gui.mouse_in_window
				and not tauon.bottom_bar1.volume_bar_being_dragged
				and not tauon.bottom_bar1.volume_hit
				and not tauon.bottom_bar1.seek_hit
			):
				inp.mouse_position[0] = -300.0
				inp.mouse_position[1] = -300.0

			if gui.clear_image_cache_next:
				gui.clear_image_cache_next -= 1
				tauon.album_art_gen.clear_cache()
				tauon.style_overlay.radio_meta = None
				if prefs.art_bg:
					tauon.thread_manager.ready("style")

			tauon.fields.clear()
			gui.cursor_want = 0

			gui.layer_focus = 0

			if inp.mouse_click or inp.mouse_wheel or inp.right_click:
				inp.mouse_position[0], inp.mouse_position[1] = tauon.input_sdl.mouse()

			if inp.mouse_click:
				n_click_time = time.time()
				if n_click_time - gui.click_time < 0.42:
					inp.d_mouse_click = True
				gui.click_time = n_click_time

				# Don't register bottom level click when closing message box
				if (
					gui.message_box
					and pref_box.enabled
					and not inp.key_focused
					and not tauon.coll(tauon.message_box.get_rect())
				):
					inp.mouse_click = False
					gui.message_box = False

			# Enable the garbage collector (since we disabled it during startup)
			if ggc > 0:
				if ggc == 2:
					ggc = 1
				elif ggc == 1:
					ggc = 0
					gbc.enable()
					# logging.info("Enabling garbage collecting")

			# Custom Layout System: handle edit/interaction input early and consume
			# the events so the underlying UI doesn't also react. Inert when off.
			# MAIN mode only: the mouse it neutralises is restored in
			# custom.render(), which mini mode never reaches — running here in
			# mini mode left the mini modes with no mouse input at all.
			if gui.custom_mode and gui.mode == GuiMode.MAIN:
				tauon.custom.handle_input()

			# Dream Room: keep muting the mouse every frame (motion-only frames
			# skip the input block above), so hover doesn't leak to the hidden
			# full-size UI. Click/key exit is handled early, before menu consumers.
			if tauon.dream_room.active:
				tauon.dream_room.handle_input()

			if tauon.milk_choose.active:
				tauon.milk_choose.handle_input()

			if gui.mode == GuiMode.MAIN:
				ddt.text_background_colour = colours.playlist_panel_background
				playlist_render.update_album_rating_hover()

				# Side Bar Draging----------

				if not inp.mouse_down:
					gui.side_drag = False

				side_drag_x = gui.rsp_split_x - 5 * gui.scale
				if not gui.rsp_on_left:
					side_drag_x = gui.rsp_split_x + 4 * gui.scale
					if prefs.scroll_enable:
						side_drag_x = gui.rsp_split_x - 1 * gui.scale
				rect = (
					side_drag_x,
					gui.panelY,
					12 * gui.scale,
					window_size[1] - gui.panelY - gui.panelBY,
				)
				tauon.fields.add(rect)
				tracklist_scroll_top = gui.panelY
				if gui.artist_info_panel:
					tracklist_scroll_top += gui.artist_panel_height
				if gui.set_bar and gui.set_mode:
					# Match render_tracklist_scrollbar: the bar starts below the
					# columns header, so its side-drag-blocking hitbox must too.
					tracklist_scroll_top += gui.set_height
				tracklist_scrollbar_width = 15 * gui.scale
				if gui.set_mode and prefs.left_align_album_artist_title:
					tracklist_scrollbar_width = 11 * gui.scale
				tracklist_scroll_hitbox_width = 28 * gui.scale
				if prefs.tracklist_scrollbar_left:
					tracklist_scrollbar_x = gui.playlist_left + 1 * gui.scale
					tracklist_scroll_hitbox_left = tracklist_scrollbar_x - 1 * gui.scale
				else:
					tracklist_scrollbar_x = gui.playlist_left + gui.plw - tracklist_scrollbar_width - 3 * gui.scale
					tracklist_scroll_hitbox_left = tracklist_scrollbar_x + tracklist_scrollbar_width + 1 * gui.scale - tracklist_scroll_hitbox_width
				tracklist_scroll_hitbox = (
					tracklist_scroll_hitbox_left,
					tracklist_scroll_top,
					tracklist_scroll_hitbox_width,
					window_size[1] - gui.panelBY - tracklist_scroll_top,
				)
				scroll_bar_held = (
					scroll_hold
					or tauon.mini_lyrics_scroll.held
					or tauon.playlist_panel_scroll.held
					or tauon.artist_info_scroll.held
					or tauon.device_scroll.held
					or tauon.artist_list_scroll.held
					or tauon.gallery_scroll.held
					or tauon.tree_view_scroll.held
					or tauon.radio_view_scroll.held
				)
				scroll_bar_suppressed_by_album_rating = update_tracklist_scrollbar_lock(tracklist_scroll_hitbox)
				scroll_bar_blocks_side_drag = (
					scroll_bar_held
					or (tauon.coll(tracklist_scroll_hitbox) and not scroll_bar_suppressed_by_album_rating)
				)
				if scroll_bar_held:
					gui.side_drag = False

				if (
					(tauon.coll(rect) or gui.side_drag is True)
					and tauon.rename_track_box.active is False
					and radiobox.active is False
					and gui.rename_playlist_box is False
					and gui.message_box is False
					and prefs.show_nag is False
					and pref_box.enabled is False
					and gui.track_box is False
					and not gui.rename_folder_box
					and not gui.timed_lyrics_editing_now
					and not Menu.active
					and (gui.rsp or prefs.album_mode)
					and not scroll_bar_blocks_side_drag
					and gui.layer_focus == 0
					and gui.show_playlist
				):
					if gui.side_drag is True:
						draw_sep_hl = True
						# gui.update += 1
						gui.update_on_drag = True

					if inp.mouse_click:
						gui.side_drag = True
						gui.side_bar_drag_source = inp.mouse_position[0]
						gui.side_bar_drag_original = gui.rspw

					if not inp.quick_drag:
						gui.cursor_want = 1

				# side drag update
				if gui.side_drag:
					if gui.rsp_on_left:
						offset = inp.mouse_position[0] - gui.side_bar_drag_source
					else:
						offset = gui.side_bar_drag_source - inp.mouse_position[0]

					target = gui.side_bar_drag_original + offset

					# Snap to album mode position if close
					if not prefs.album_mode and prefs.side_panel_layout == 1:
						if abs(target - gui.pref_gallery_w) < 35 * gui.scale:
							target = gui.pref_gallery_w

					# Reset max ratio if drag drops below ratio width
					if prefs.side_panel_layout == 0:
						if target < round((window_size[1] - gui.panelY - gui.panelBY) * gui.art_aspect_ratio):
							gui.art_max_ratio_lock = gui.art_aspect_ratio

						max_w = round(
							((window_size[1] - gui.panelY - gui.panelBY - 17 * gui.scale) * gui.art_max_ratio_lock)
							+ 17 * gui.scale
						)
						# 17 here is the art box inset value

					else:
						max_w = window_size[0]

					if not prefs.album_mode and target > max_w - 12 * gui.scale:
						target = max_w
						gui.rspw = target
						gui.rsp_full_lock = True

					else:
						gui.rspw = target
						gui.rsp_full_lock = False

					if prefs.album_mode:
						pass
						# gui.rspw = target

					if prefs.album_mode and gui.rspw < tauon.album_mode_art_size + 50 * gui.scale:
						target = tauon.album_mode_art_size + 50 * gui.scale

					# Prevent side bar getting too small
					target = max(target, 120 * gui.scale)

					# Remember size for this view mode
					if not prefs.album_mode:
						gui.pref_rspw = target
					else:
						gui.pref_gallery_w = target

					tauon.update_layout_do()

				# ALBUM GALLERY RENDERING:
				# Gallery view
				# C-AR

				if prefs.album_mode and not gui.custom_mode:
					# In custom mode the Album Gallery widget calls render_gallery()
					# itself (with the geometry vars pointed at its segment); running
					# the preset path too would fight it — each call recomputes
					# row_len from different geometry, so gui.last_row ping-pongs and
					# goto_album() re-locates (and resets the scroll) every frame.
					render_gallery()

				# End of gallery view
				# --------------------------------------------------------------------------
				# Main Playlist:
				if len(tauon.load_orders) > 0:
					for i, order in enumerate(tauon.load_orders):
						if order.stage == 2:
							target_pl = 0

							# Sort the tracks by track number
							tauon.sort_track_2(None, order.tracks)

							for p, playlist in enumerate(pctl.multi_playlist):
								if playlist.uuid_int == order.playlist:
									target_pl = p
									break
							else:
								del tauon.load_orders[i]
								logging.error("Target playlist lost")
								break

							if order.replace_stem:
								for ii, id in reversed(list(enumerate(pctl.multi_playlist[target_pl].playlist_ids))):
									pfp = pctl.get_track(id).parent_folder_path
									if pfp.startswith(order.target.replace("\\", "/")):
										if pfp.rstrip("/\\") == order.target.rstrip("/\\") or (
											len(pfp) > len(order.target)
											and pfp[len(order.target.rstrip("/\\"))] in ("/", "\\")
										):
											del pctl.multi_playlist[target_pl].playlist_ids[ii]

							# logging.info(order.tracks)
							if order.playlist_position is not None:
								# logging.info(order.playlist_position)
								pctl.multi_playlist[target_pl].playlist_ids[
									order.playlist_position : order.playlist_position
								] = order.tracks
							# else:

							else:
								pctl.multi_playlist[target_pl].playlist_ids += order.tracks

							pctl.update_shuffle_pool(pctl.multi_playlist[target_pl].uuid_int)

							gui.request_frame()
							gui.request_tracklist_redraw()
							if order.notify and gui.message_box and len(tauon.load_orders) == 1:
								tauon.show_message(_("Rescan folders complete."), mode="done")
							tauon.reload()
							tauon.tree_view_box.clear_target_pl(target_pl)

							if order.play and order.tracks:
								for p, plst in enumerate(pctl.multi_playlist):
									if order.tracks[0] in plst.playlist_ids:
										target_pl = p
										break

								pctl.switch_playlist(target_pl)

								pctl.active_playlist_playing = pctl.active_playlist_viewing

								# If already in playlist, delete latest add
								if pctl.multi_playlist[target_pl].title == "Default":
									if pctl.default_playlist.count(order.tracks[0]) > 1:
										for q in reversed(range(len(pctl.default_playlist))):
											if pctl.default_playlist[q] == order.tracks[0]:
												del pctl.default_playlist[q]
												break

								pctl.jump(order.tracks[0], pl_position=pctl.default_playlist.index(order.tracks[0]))

								pctl.show_current(True, True, True, True, True)

							del tauon.load_orders[i]

							# Are there more orders for this playlist?
							# If not, decide on a name for the playlist
							for item in tauon.load_orders:
								if item.playlist == order.playlist:
									break
							else:
								if _("New Playlist") in pctl.multi_playlist[target_pl].title:
									tauon.auto_name_pl(target_pl)

								if prefs.auto_sort:
									if pctl.multi_playlist[target_pl].locked:
										tauon.show_message(_("Auto sort skipped because playlist is locked."))
									else:
										logging.info("Auto sorting")
										tauon.standard_sort(target_pl)
										tauon.year_sort(target_pl)

							if not tauon.load_orders:
								pctl.loading_in_progress = False
								pctl.notify_database_changed()
								gui.auto_play_import = False
								gui.album_artist_dict.clear()
							break

				# The custom layout owns the complete main canvas.  Its widgets render
				# their own tracklists, controls and panels below, so do not draw any
				# of the hidden preset playlist chrome first.
				if gui.show_playlist and not gui.custom_mode:
					# playlist hit test
					if (
						tauon.coll(
							(gui.playlist_left, gui.playlist_top, gui.plw, window_size[1] - gui.panelY - gui.panelBY)
						)
						and not inp.drag_mode
						and (
							inp.mouse_click
							or inp.mouse_wheel != 0
							or inp.right_click
							or inp.middle_click
							or inp.mouse_up
							or inp.mouse_down
						)
					):
						gui.request_tracklist_redraw()

					if gui.combo_mode and inp.mouse_wheel != 0:
						gui.request_tracklist_redraw()

					# MAIN PLAYLIST
					# C-PR

					if not gui.custom_mode:
						render_column_bar_input()

					# heart field test
					if gui.heart_fields:
						for field in gui.heart_fields:
							tauon.fields.add(field, tauon.update_playlist_call)

					if not gui.showcase_mode:
						showcase.timed_lyrics_edit.continuous = False

					if gui.pl_update:
						gui.rendered_playlist_position = pctl.playlist_view_position

						# Flip the request flag off at the start of the render: any
						# request_tracklist_redraw() made during it means "render
						# the tracklist again next frame".
						gui.pl_update = False
						if gui.combo_mode:
							if gui.radio_view:
								tauon.radio_view.render()
							elif gui.showcase_mode:
								showcase.render()

							# else:
							#     combo_pl_render.full_render()
						else:
							gui.heart_fields.clear()
							ddt.begin_tracklist_count()
							playlist_render.full_render()
							ddt.end_tracklist_count()
					elif gui.combo_mode:
						if gui.radio_view:
							tauon.radio_view.render()
						elif gui.showcase_mode:
							showcase.render()
						# else:
						#     combo_pl_render.cache_render()
					else:
						playlist_render.cache_render()

					rect = (gui.playlist_left, gui.panelY, gui.plw, window_size[1] - (gui.panelBY + gui.panelY))

					if gui.ext_drop_mode and tauon.coll(rect):
						ddt.rect_si(rect, ColourRGBA(80, 200, 180, 255), round(3 * gui.scale))
					tauon.fields.add(rect)

					if prefs.shuffle_lock and inp.key_esc_press and tauon.is_level_zero():
						tauon.toggle_shuffle_layout()
						inp.key_esc_press = False
					elif gui.combo_mode and inp.key_esc_press and tauon.is_level_zero():
						tauon.exit_combo()

					if not gui.custom_mode:
						render_column_bar_draw()

					# Window menu (covers the whole empty top-panel area,
					# including the visualiser at the far right)
					if (
						inp.right_click
						and tauon.top_panel.tabs_right_x < inp.mouse_position[0]
						and inp.mouse_position[1] < gui.panelY
						and inp.mouse_position[0] < window_size[0] - gui.offset_extra
					):
						tauon.window_menu.activate(None, (inp.mouse_position[0], 30 * gui.scale))

					elif (
						inp.middle_click
						and tauon.top_panel.tabs_right_x < inp.mouse_position[0]
						and inp.mouse_position[1] < gui.panelY
						and inp.mouse_position[0] > tauon.top_panel.tabs_right_x
						and inp.mouse_position[0] < window_size[0] - gui.offset_extra
					):
						tauon.do_minimize_button()

					# edge_playlist.render(gui.playlist_left, gui.panelY, gui.plw, 2 * gui.scale)

					tauon.bottom_playlist2.render(
						gui.playlist_left, window_size[1] - gui.panelBY, gui.plw, 25 * gui.scale, bottom=True
					)
					# --------------------------------------------
					# ALBUM ART

					# Right side panel drawing

					# Custom layouts are composited later in the frame and own their
					# complete canvas.  Drawing the preset right-side panel here is not
					# visible, but its ArtBox path clears its target every frame, which
					# breaks MilkDrop's persistent render buffer in a custom widget.
					if gui.rsp and not prefs.album_mode and not gui.custom_mode:
						gui.showing_l_panel = False
						target_track = pctl.show_object()
						rsp_x = gui.rsp_x

						if inp.middle_click:
							if tauon.coll(
								(
									rsp_x,
									gui.panelY,
									gui.rspw,
									window_size[1] - gui.panelY - gui.panelBY,
								)
							):
								if (target_track and target_track.lyrics and prefs.show_lyrics_side) or (
									prefs.show_lyrics_side
									and prefs.prefer_synced_lyrics
									and target_track is not None
									and tauon.timed_lyrics_ren.generate(target_track)
								):
									prefs.show_lyrics_side ^= True
									prefs.side_panel_layout = 1
								elif prefs.side_panel_layout == 0:
									if (target_track and target_track.lyrics and not prefs.show_lyrics_side) or (
										prefs.prefer_synced_lyrics
										and target_track is not None
										and tauon.timed_lyrics_ren.generate(target_track)
									):
										prefs.show_lyrics_side = True
										prefs.side_panel_layout = 1
									else:
										prefs.side_panel_layout = 1
								else:
									prefs.side_panel_layout = 0

						if (
							prefs.show_lyrics_side
							and prefs.prefer_synced_lyrics
							and target_track is not None
							and tauon.timed_lyrics_ren.generate(target_track)
						):
							if prefs.show_side_lyrics_art_panel:
								gui.l_panel_h = round(200 * gui.scale)
								gui.l_panel_y = window_size[1] - (gui.panelBY + gui.l_panel_h)
								gui.showing_l_panel = True

								if not prefs.lyric_metadata_panel_top:
									tauon.timed_lyrics_ren.render(
										target_track.index,
										rsp_x + 9 * gui.scale,
										gui.panelY,
										side_panel=True,
										w=gui.rspw,
										h=window_size[1] - gui.panelY - gui.panelBY - gui.l_panel_h,
									)
									meta_box.l_panel(rsp_x, gui.l_panel_y, gui.rspw, gui.l_panel_h, target_track)
								else:
									tauon.timed_lyrics_ren.render(
										target_track.index,
										rsp_x + 9 * gui.scale,
										gui.panelY + gui.l_panel_h,
										side_panel=True,
										w=gui.rspw,
										h=window_size[1] - gui.panelY - gui.panelBY - gui.l_panel_h,
									)
									meta_box.l_panel(rsp_x, gui.panelY, gui.rspw, gui.l_panel_h, target_track)
							else:
								tauon.timed_lyrics_ren.render(
									target_track.index,
									rsp_x + 9 * gui.scale,
									gui.panelY,
									side_panel=True,
									w=gui.rspw,
									h=window_size[1] - gui.panelY - gui.panelBY,
								)

								if inp.right_click and tauon.coll(
									(
										rsp_x,
										gui.panelY,
										gui.rspw,
										window_size[1] - (gui.panelBY + gui.panelY),
									)
								):
									center_info_menu.activate(target_track)
						elif (
							prefs.show_lyrics_side
							and target_track is not None
							and target_track.lyrics
							and gui.rspw > 192 * gui.scale
						):
							if prefs.show_side_lyrics_art_panel:
								gui.l_panel_h = round(200 * gui.scale)
								gui.l_panel_y = window_size[1] - (gui.panelBY + gui.l_panel_h)
								gui.showing_l_panel = True

								if not prefs.lyric_metadata_panel_top:
									meta_box.lyrics(
										rsp_x,
										gui.panelY,
										gui.rspw,
										window_size[1] - gui.panelY - gui.panelBY - gui.l_panel_h,
										target_track,
									)
									meta_box.l_panel(rsp_x, gui.l_panel_y, gui.rspw, gui.l_panel_h, target_track)
								else:
									meta_box.lyrics(
										rsp_x,
										gui.panelY + gui.l_panel_h,
										gui.rspw,
										window_size[1] - (gui.panelY + gui.panelBY + gui.l_panel_h),
										target_track,
									)

									meta_box.l_panel(
										rsp_x,
										gui.panelY,
										gui.rspw,
										gui.l_panel_h,
										target_track,
										top_border=False,
									)
							else:
								meta_box.lyrics(
									rsp_x,
									gui.panelY,
									gui.rspw,
									window_size[1] - gui.panelY - gui.panelBY,
									target_track,
								)

						elif prefs.side_panel_layout == 0:
							boxw = gui.rspw
							available_h = max(0, window_size[1] - gui.panelY - gui.panelBY)
							boxh = min(gui.rspw, available_h)

							if prefs.show_side_art:
								meta_box.draw(
									rsp_x,
									gui.panelY + boxh,
									gui.rspw,
									available_h - boxh,
									track=target_track,
								)

								tauon.art_box.draw(rsp_x, gui.panelY, boxw, boxh, target_track=target_track)

							else:
								meta_box.draw(
									rsp_x,
									gui.panelY,
									gui.rspw,
									window_size[1] - gui.panelY - gui.panelBY,
									track=target_track,
								)

						elif prefs.side_panel_layout == 1:
							h = window_size[1] - (gui.panelY + gui.panelBY)
							x = rsp_x
							y = gui.panelY
							w = gui.rspw

							if not gui.have_art_bg:
								ddt.clear_rect((x, y, w, h))
							ddt.rect((x, y, w, h), colours.side_panel_background)
							tauon.test_auto_lyrics(target_track)
							# Draw lyrics if available
							if (
								prefs.show_lyrics_side and target_track and target_track.lyrics
							):  # and not prefs.show_side_art:
								# meta_box.lyrics(x, y, w, h, target_track)
								if inp.right_click and tauon.coll((x, y, w, h)) and target_track:
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
								text_y = (
									y
									+ by
									+ boxy
									+ ((h - bby) // 2)
									- 44 * gui.scale
									- round((h - bby - 94 * gui.scale) * 0.08)
								)

								small_mode = False
								if window_size[1] < 550 * gui.scale:
									small_mode = True
									text_y = y + by + boxy + ((h - bby) // 2) - 38 * gui.scale

								text_x = x + w // 2

								if prefs.show_side_art:
									gui.art_drawn_rect = None
									default_border = (bx, by, boxx, boxy)
									coll_border = default_border

									tauon.art_box.draw(
										bx_wide,
										by,
										box_wide_w,
										boxy,
										target_track=target_track,
										tight_border=True,
										default_border=default_border,
										draw_background=False,
									)

									if gui.art_drawn_rect:
										coll_border = gui.art_drawn_rect

									if inp.right_click and tauon.coll((x, y, w, h)) and not tauon.coll(coll_border):
										if tauon.is_level_zero(include_menus=False) and target_track:
											center_info_menu.activate(target_track)

								else:
									text_y = y + round(h * 0.40)
									if inp.right_click and tauon.coll((x, y, w, h)) and target_track:
										center_info_menu.activate(target_track)

								ww = w - 25 * gui.scale

								gui.showed_title = True

								if target_track:
									ddt.text_background_colour = colours.side_panel_background

									if pctl.playing_state == PlayingState.URL_STREAM and not radiobox.dummy_track.title:
										title = pctl.tag_meta
									else:
										title = target_track.title
										if not title:
											title = clean_string(target_track.filename)

									if small_mode:
										ddt.text(
											(text_x, text_y - 15 * gui.scale, 2),
											target_track.artist,
											colours.side_bar_line1,
											315,
											max_w=ww,
										)

										ddt.text(
											(text_x, text_y + 12 * gui.scale, 2),
											title,
											colours.side_bar_line1,
											216,
											max_w=ww,
										)

										line = " | ".join(
											filter(None, (target_track.album, target_track.date, target_track.genre))
										)
										ddt.text(
											(text_x, text_y + 35 * gui.scale, 2),
											line,
											colours.side_bar_line2,
											313,
											max_w=ww,
										)

									else:
										ddt.text(
											(text_x, text_y - 15 * gui.scale, 2),
											target_track.artist,
											colours.side_bar_line1,
											317,
											max_w=ww,
										)

										ddt.text(
											(text_x, text_y + 17 * gui.scale, 2),
											title,
											colours.side_bar_line1,
											218,
											max_w=ww,
										)

										line = " | ".join(
											filter(None, (target_track.album, target_track.date, target_track.genre))
										)
										ddt.text(
											(text_x, text_y + 45 * gui.scale, 2),
											line,
											colours.side_bar_line2,
											314,
											max_w=ww,
										)

					# Separation Line Drawing
					if gui.rsp and not gui.custom_mode:
						# Draw Highlight when mouse over
						if draw_sep_hl:
							sep_x = gui.rsp_split_x + 1 * gui.scale
							if gui.rsp_on_left or prefs.scroll_enable:
								sep_x = gui.rsp_split_x - 1 * gui.scale
							ddt.line(
								sep_x,
								gui.panelY + 1 * gui.scale,
								sep_x,
								window_size[1] - 50 * gui.scale,
								ColourRGBA(100, 100, 100, 70),
							)
							draw_sep_hl = False

				if (gui.artist_info_panel and not gui.combo_mode and not gui.custom_mode) and not (
					window_size[0] < 750 * gui.scale and prefs.album_mode
				):
					tauon.artist_info_box.draw(gui.playlist_left, gui.panelY, gui.plw, gui.artist_panel_height)

				# In custom mode the layout engine renders these panels (queue,
				# playlist list, artist list, folder navigator) as widgets; skip the
				# standard left side panel to avoid double-rendering the same objects.
				if gui.lsp and not gui.combo_mode and not gui.custom_mode:
					# left side panel
					h_estimate = (
						(tauon.playlist_box.tab_h + tauon.playlist_box.gap) * gui.scale * len(pctl.multi_playlist)
					) + 13 * gui.scale
					panel_x = gui.lsp_x

					full = window_size[1] - (gui.panelY + gui.panelBY)
					half = round(full / 2)

					gui.pl_box_h = full

					panel_rect = (panel_x, gui.panelY, gui.lspw, gui.pl_box_h)
					tauon.fields.add(panel_rect)

					if gui.force_side_on_drag and not inp.quick_drag and not tauon.coll(panel_rect):
						gui.force_side_on_drag = False
						tauon.update_layout_do()

					if (
						inp.quick_drag
						and not coll_point(gui.drag_source_position_persist, panel_rect)
						and not point_proximity_test(gui.drag_source_position, inp.mouse_position, 10 * gui.scale)
					):
						gui.force_side_on_drag = True
						if inp.mouse_up:
							tauon.update_layout_do()

					if prefs.left_panel_mode == "folder view" and not gui.force_side_on_drag:
						tauon.tree_view_box.render(panel_x, gui.panelY, gui.lspw, gui.pl_box_h)
					elif prefs.left_panel_mode == "artist list" and not gui.force_side_on_drag:
						tauon.artist_list_box.render(*panel_rect)
					else:
						preview_queue = False
						if (
							inp.quick_drag
							and tauon.coll(panel_rect)
							and not pctl.force_queue
							and prefs.show_playlist_list
							and prefs.hide_queue
						):
							preview_queue = True

						if pctl.force_queue or preview_queue or not prefs.hide_queue:
							if h_estimate < half:
								gui.pl_box_h = h_estimate
							else:
								gui.pl_box_h = half

							if preview_queue:
								gui.pl_box_h = round(full * 5 / 6)

						if prefs.left_panel_mode != "queue":
							tauon.playlist_box.draw(panel_x, gui.panelY, gui.lspw, gui.pl_box_h)
						else:
							gui.pl_box_h = 0

						if pctl.force_queue or preview_queue or not prefs.show_playlist_list or not prefs.hide_queue:
							tauon.queue_box.draw(panel_x, gui.panelY + gui.pl_box_h, gui.lspw, full - gui.pl_box_h)

							if prefs.show_playlist_list and gui.pl_box_h:
								# Separator line at the playlist list / queue seam
								rect = (panel_x, gui.panelY + gui.pl_box_h, gui.lspw, round(gui.scale * 2))
								ddt.rect(rect, ColourRGBA(0, 0, 0, 255))
								ddt.rect(rect, alpha_blend(ColourRGBA(255, 255, 255, 11), colours.queue_background))
						elif prefs.left_panel_mode == "queue":
							text = _("Queue is Empty")
							rect = (panel_x, gui.panelY + gui.pl_box_h, gui.lspw, full - gui.pl_box_h)
							ddt.rect(rect, colours.queue_background)
							ddt.text_background_colour = colours.queue_background
							ddt.text(
								(panel_x + (gui.lspw // 2), gui.panelY + gui.pl_box_h + 15 * gui.scale, 2),
								text,
								alpha_mod(colours.index_text, 200),
								212,
							)

				# ------------------------------------------------
				# Scroll Bar

				# if not prefs.scroll_enable:
				top = gui.panelY
				if gui.artist_info_panel:
					top += gui.artist_panel_height

				edge_top = top
				if gui.set_bar and gui.set_mode:
					edge_top += gui.set_height
				if not gui.custom_mode:
					tauon.edge_playlist2.render(gui.playlist_left, edge_top, gui.plw, 25 * gui.scale)

				if not gui.custom_mode:
					render_tracklist_scrollbar(
						gui.playlist_left, gui.plw, top,
						window_size[1] - gui.panelBY,
						window_size[1] - (30 + 22) * gui.scale)

				# NEW TOP BAR
				# C-TBR

				# In custom mode the layout engine renders the Top Panel widget
				# itself (reframed); skip the standard one to avoid double-rendering
				# the same stateful TopPanel object.
				if gui.mode == GuiMode.MAIN and not gui.custom_mode:
					tauon.top_panel.render()

				# RENDER EXTRA FRAME DOUBLE
				if colours.lm and not gui.custom_mode:
					if gui.lsp and not gui.combo_mode and not gui.compact_artist_list:
						ddt.rect(
							(
								gui.lsp_x + gui.lspw - 6 * gui.scale,
								gui.panelY,
								6 * gui.scale,
								round(window_size[1] - gui.panelY - gui.panelBY),
							),
							colours.grey(200),
						)
						ddt.rect(
							(
								gui.lsp_x + gui.lspw - 5 * gui.scale,
								gui.panelY - 1,
								4 * gui.scale,
								round(window_size[1] - gui.panelY - gui.panelBY) + 1,
							),
							colours.grey(245),
						)
					if gui.rsp and gui.show_playlist:
						w = gui.rsp_split_x
						ddt.rect(
							(
								w - round(3 * gui.scale),
								gui.panelY,
								6 * gui.scale,
								round(window_size[1] - gui.panelY - gui.panelBY),
							),
							colours.grey(200),
						)
						ddt.rect(
							(
								w - round(2 * gui.scale),
								gui.panelY - 1,
								4 * gui.scale,
								round(window_size[1] - gui.panelY - gui.panelBY) + 1,
							),
							colours.grey(245),
						)
					if gui.queue_frame_draw is not None:
						if gui.lsp:
							ddt.rect(
								(gui.lsp_x, gui.queue_frame_draw, gui.lspw - 6 * gui.scale, 6 * gui.scale), colours.grey(200)
							)
							ddt.rect(
								(gui.lsp_x, gui.queue_frame_draw + 1 * gui.scale, gui.lspw - 5 * gui.scale, 4 * gui.scale),
								colours.grey(250),
							)

						gui.queue_frame_draw = None

				# BOTTOM BAR!
				# C-BB

				ddt.text_background_colour = colours.bottom_panel_colour

				# In custom mode the layout engine renders the Playback panel widget
				# itself (reframed); skip the standard bottom bar to avoid
				# double-rendering the same stateful bar object.
				if gui.custom_mode:
					pass
				elif prefs.shuffle_lock:
					tauon.bottom_bar_ao1.render()
				else:
					tauon.bottom_bar1.render()

				# (The blurred art background is now drawn at the start of the
				# frame, underneath the UI, rather than composited over it here)
				tauon.style_overlay.hole_punches.clear()

				# Custom Layout System: composite over the standard layout once
				# panel rendering is done. Overlays (toasts, menus, dialogs) below
				# still draw on top. Inert unless custom mode is active.
				if gui.custom_mode:
					tauon.custom.render()

					# The window menu is normally opened in the standard top-panel
					# input pass, which is skipped in custom mode — and
					# custom.handle_input() neutralised the click earlier in the
					# frame, only restoring it inside custom.render() above. Handle
					# it here (view mode only): the empty Header Bar widget area
					# right of the tabs (segment coords + reframed tabs_right_x),
					# plus the visualiser strip, which is drawn over the layout at
					# the window's far right (absolute coords).
					if not gui.custom_edit and inp.right_click:
						over_vis = tauon.coll(
							(window_size[0] - 130 * gui.scale - gui.offset_extra, 0, 125 * gui.scale, gui.panelY)
						) and not gui.top_bar_mode2
						tpr = tauon.custom.top_panel_rect()
						over_panel = tpr is not None and tauon.coll((
							tpr[0] + tauon.top_panel.tabs_right_x, tpr[1],
							tpr[2] - tauon.top_panel.tabs_right_x, tpr[3]))
						if over_vis or over_panel:
							tauon.window_menu.activate(None, (inp.mouse_position[0], inp.mouse_position[1]))
							inp.right_click = False

				if gui.set_mode:
					if (
						tauon.rename_track_box.active is False
						and radiobox.active is False
						and gui.rename_playlist_box is False
						and gui.message_box is False
						and pref_box.enabled is False
						and gui.track_box is False
						and not gui.rename_folder_box
						and not gui.timed_lyrics_editing_now
						and not Menu.active
						and not tauon.artist_info_scroll.held
					):
						tauon.columns_tool_tip.render()
					else:
						tauon.columns_tool_tip.show = False

				# Overlay GUI ----------------------

				if gui.rename_playlist_box:
					tauon.rename_playlist_box.render()

				if gui.preview_artist:
					border = round(4 * gui.scale)
					ddt.rect(
						(
							gui.preview_artist_location[0] - border,
							gui.preview_artist_location[1] - border,
							tauon.artist_preview_render.size[0] + border * 2,
							tauon.artist_preview_render.size[0] + border * 2,
						),
						ColourRGBA(20, 20, 20, 255),
					)

					tauon.artist_preview_render.draw(gui.preview_artist_location[0], gui.preview_artist_location[1])
					if inp.mouse_click or inp.right_click or inp.mouse_wheel:
						gui.preview_artist = ""

				if gui.track_box:
					if (
						inp.key_return_press
						or inp.right_click
						or inp.key_esc_press
						or inp.backspace_press
						or keymaps.test("quick-find")
					):
						gui.track_box = False

						inp.key_return_press = False

					if gui.level_2_click:
						inp.mouse_click = True
					gui.level_2_click = False

					tc = pctl.master_library[gui.track_box_track_id]

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

					# if inp.key_shift_down:
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
						(x - 3 * gui.scale, y - 3 * gui.scale),
						(w + 6 * gui.scale, h + 6 * gui.scale),
						colours.box_border,
					)
					ddt.rect_a((x, y), (w, h), colours.box_background)
					ddt.text_background_colour = colours.box_background

					if inp.mouse_click and not tauon.coll([x, y, w, h]):
						gui.track_box = False
					else:
						art_size = int(115 * gui.scale)

						# if not tc.is_network: # Don't draw album art if from network location for better performance
						if comment_mode == 1:
							tauon.album_art_gen.display(
								tc, (int(x + w - 135 * gui.scale), int(y + 105 * gui.scale)), (art_size, art_size)
							)  # Mirror this size in auto theme #mark2233
						else:
							tauon.album_art_gen.display(
								tc, (int(x + w - 135 * gui.scale), int(y + h - 135 * gui.scale)), (art_size, art_size)
							)

						y -= int(24 * gui.scale)
						y1 = int(y + (40 * gui.scale))

						ext_rect = [
							x + w - round(38 * gui.scale),
							y + round(44 * gui.scale),
							round(38 * gui.scale),
							round(12 * gui.scale),
						]

						line = tc.file_ext
						ex_colour = ColourRGBA(130, 130, 130, 255)
						if line in tauon.formats.colours:
							ex_colour = tauon.formats.colours[line]

						if tc.file_ext in ("JELY", "TIDAL"):
							e_colour = ColourRGBA(130, 130, 130, 255)
							if tc.container is not None:
								line = tc.container.upper()
								if line in tauon.formats.colours:
									e_colour = tauon.formats.colours[line]

								ddt.rect(ext_rect, e_colour)
								colour = alpha_blend(ColourRGBA(10, 10, 10, 235), e_colour)
								if colour_value(e_colour) < 180:
									colour = alpha_blend(ColourRGBA(200, 200, 200, 235), e_colour)
								ddt.text(
									(int(x + w - 35 * gui.scale), round(y + (41) * gui.scale)),
									line,
									colour,
									211,
									bg=e_colour,
								)
								ext_rect[1] += 16 * gui.scale
								y += 16 * gui.scale

						ddt.rect(ext_rect, ex_colour)
						colour = alpha_blend(ColourRGBA(10, 10, 10, 235), ex_colour)
						if colour_value(ex_colour) < 180:
							colour = alpha_blend(ColourRGBA(200, 200, 200, 235), ex_colour)
						ddt.text(
							(int(x + w - 35 * gui.scale), round(y + 41 * gui.scale)),
							tc.file_ext,
							colour,
							211,
							bg=ex_colour,
						)

						if tc.is_cue:
							ext_rect[1] += 16 * gui.scale
							colour = ColourRGBA(218, 222, 73, 255)
							if tc.is_embed_cue:
								colour = ColourRGBA(252, 199, 55, 255)
							ddt.rect(ext_rect, colour)
							ddt.text(
								(int(x + w - 35 * gui.scale), int(y + (41 + 16) * gui.scale)),
								"CUE",
								alpha_blend(ColourRGBA(10, 10, 10, 235), colour),
								211,
								bg=colour,
							)

						rect = [x1, y1 + int(2 * gui.scale), 450 * gui.scale, 14 * gui.scale]
						tauon.fields.add(rect)
						if tauon.coll(rect):
							ddt.text((x1, y1), _("Title"), key_colour_on, 212)
							if inp.mouse_click:
								tauon.show_message(_("Copied text to clipboard"))
								copy_to_clipboard(tc.title)
								inp.mouse_click = False
						else:
							ddt.text((x1, y1), _("Title"), key_colour_off, 212)
						q = ddt.text(
							(x2, y1 - int(2 * gui.scale)), tc.title, value_colour, 314, max_w=w - 170 * gui.scale
						)

						if tauon.coll(rect):
							tauon.ex_tool_tip(x2 + 185 * gui.scale, y1, q, tc.title, 314)

						y1 += int(16 * gui.scale)

						rect = [x1, y1 + (2 * gui.scale), 450 * gui.scale, 14 * gui.scale]
						tauon.fields.add(rect)
						if tauon.coll(rect):
							ddt.text((x1, y1), _("Artist"), key_colour_on, 212)
							if inp.mouse_click:
								tauon.show_message(_("Copied text to clipboard"))
								copy_to_clipboard(tc.artist)
								inp.mouse_click = False
						else:
							ddt.text((x1, y1), _("Artist"), key_colour_off, 212)

						q = ddt.text(
							(x2, y1 - (1 * gui.scale)), tc.artist, value_colour, value_font_a, max_w=390 * gui.scale
						)

						if tauon.coll(rect):
							tauon.ex_tool_tip(x2 + 185 * gui.scale, y1, q, tc.artist, value_font_a)

						y1 += int(16 * gui.scale)

						rect = [x1, y1 + (2 * gui.scale), 450 * gui.scale, 14 * gui.scale]
						tauon.fields.add(rect)
						if tauon.coll(rect):
							ddt.text((x1, y1), _("Album"), key_colour_on, 212)
							if inp.mouse_click:
								tauon.show_message(_("Copied text to clipboard"))
								copy_to_clipboard(tc.album)
								inp.mouse_click = False
						else:
							ddt.text((x1, y1), _("Album"), key_colour_off, 212)

						q = ddt.text(
							(x2, y1 - 1 * gui.scale), tc.album, value_colour, value_font_a, max_w=390 * gui.scale
						)

						if tauon.coll(rect):
							tauon.ex_tool_tip(x2 + 185 * gui.scale, y1, q, tc.album, value_font_a)

						y1 += int(26 * gui.scale)

						rect = [x1, y1, 450 * gui.scale, 16 * gui.scale]
						tauon.fields.add(rect)
						path = tc.fullpath
						if tauon.windows:
							path = path.replace("/", "\\")
						if tauon.coll(rect):
							ddt.text((x1, y1), _("Path"), key_colour_on, 212)
							if inp.mouse_click:
								tauon.show_message(_("Copied text to clipboard"))
								copy_to_clipboard(path)
								inp.mouse_click = False
						else:
							ddt.text((x1, y1), _("Path"), key_colour_off, 212)

						q = ddt.text(
							(x2, y1 - int(3 * gui.scale)), clean_string(path), path_colour, 210, max_w=425 * gui.scale
						)

						if tauon.coll(rect):
							gui.frame_callback_list.append(TestTimer(0.71))
							if tauon.track_box_path_tool_timer.get() > 0.7:
								tauon.ex_tool_tip(x2 + 185 * gui.scale, y1, q, clean_string(tc.fullpath), 210)
						else:
							tauon.track_box_path_tool_timer.set()

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
							line += " kbps"
							ddt.text((x2, y1), line, value_colour, 312)

						# -----------
						if tc.artist != tc.album_artist:
							x += int(170 * gui.scale)
							rect = [x + 7 * gui.scale, y1 + (2 * gui.scale), 220 * gui.scale, 14 * gui.scale]
							tauon.fields.add(rect)
							if tauon.coll(rect):
								ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Album Artist"), key_colour_on, 212)
								if inp.mouse_click:
									tauon.show_message(_("Copied text to clipboard"))
									copy_to_clipboard(tc.album_artist)
									inp.mouse_click = False
							else:
								ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Album Artist"), key_colour_off, 212)

							q = ddt.text(
								(x + (8 + 88) * gui.scale, y1),
								tc.album_artist,
								value_colour,
								value_font,
								max_w=120 * gui.scale,
							)
							if tauon.coll(rect):
								tauon.ex_tool_tip(x2 + 185 * gui.scale, y1, q, tc.album_artist, value_font)

							x -= int(170 * gui.scale)

						y1 += int(15 * gui.scale)

						rect = [x1, y1, 150 * gui.scale, 16 * gui.scale]
						tauon.fields.add(rect)
						if tauon.coll(rect):
							ddt.text((x1, y1), _("Duration"), key_colour_on, 212)
							if inp.mouse_click:
								copy_to_clipboard(time.strftime("%M:%S", time.gmtime(tc.length)).lstrip("0"))
								tauon.show_message(_("Copied text to clipboard"))
								inp.mouse_click = False
						else:
							ddt.text((x1, y1), _("Duration"), key_colour_off, 212)
						line = time.strftime("%M:%S", time.gmtime(tc.length))
						ddt.text((x2, y1), line, value_colour, value_font)

						# -----------
						if tc.track_total not in ("", "0"):
							x += int(170 * gui.scale)
							line = str(tc.track_number) + _(" of ") + str(tc.track_total)
							ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Track"), key_colour_off, 212)
							ddt.text((x + (8 + 88) * gui.scale, y1), line, value_colour, value_font)
							x -= int(170 * gui.scale)

						y1 += int(15 * gui.scale)
						# logging.info(tc.size)
						if tc.is_cue and (tc.parent_length if tc.parent_length is not None else 0) > 0 and (tc.parent_size if tc.parent_size is not None else 0) > 0:
							ddt.text((x1, y1), _("File size"), key_colour_off, 212, max_w=70 * gui.scale)
							estimate = (tc.length / tc.parent_length) * tc.parent_size
							line = f"≈{get_filesize_string(estimate, rounding=0)} / {get_filesize_string(tc.parent_size)}"
							ddt.text((x2, y1), line, value_colour, value_font)

						elif tc.size != 0:
							ddt.text((x1, y1), _("File size"), key_colour_off, 212, max_w=70 * gui.scale)
							ddt.text((x2, y1), get_filesize_string(tc.size), value_colour, value_font)

						# -----------
						if tc.disc_total not in ("", "0", 0):
							x += int(170 * gui.scale)
							line = str(tc.disc_number) + _(" of ") + str(tc.disc_total)
							ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Disc"), key_colour_off, 212)
							ddt.text((x + (8 + 88) * gui.scale, y1), line, value_colour, value_font)
							x -= int(170 * gui.scale)

						y1 += int(23 * gui.scale)

						rect = [x1, y1 + (2 * gui.scale), 150 * gui.scale, 14 * gui.scale]
						tauon.fields.add(rect)
						if tauon.coll(rect):
							ddt.text((x1, y1), _("Genre"), key_colour_on, 212)
							if inp.mouse_click:
								tauon.show_message(_("Copied text to clipboard"))
								copy_to_clipboard(tc.genre)
								inp.mouse_click = False
						else:
							ddt.text((x1, y1), _("Genre"), key_colour_off, 212)
						ddt.text((x2, y1), tc.genre, value_colour, value_font, max_w=290 * gui.scale)

						y1 += int(15 * gui.scale)

						rect = [x1, y1 + (2 * gui.scale), 150 * gui.scale, 14 * gui.scale]
						tauon.fields.add(rect)
						if tauon.coll(rect):
							ddt.text((x1, y1), _("Date"), key_colour_on, 212)
							if inp.mouse_click:
								tauon.show_message(_("Copied text to clipboard"))
								copy_to_clipboard(tc.date)
								inp.mouse_click = False
						else:
							ddt.text((x1, y1), _("Date"), key_colour_off, 212)
						ddt.text((x2, y1), d_date_display(tc), value_colour, value_font)

						if tc.composer and tc.composer != tc.artist:
							x += int(170 * gui.scale)
							rect = [x + 7 * gui.scale, y1 + (2 * gui.scale), 220 * gui.scale, 14 * gui.scale]
							tauon.fields.add(rect)
							if tauon.coll(rect):
								ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Composer"), key_colour_on, 212)
								if inp.mouse_click:
									tauon.show_message(_("Copied text to clipboard"))
									copy_to_clipboard(tc.album_artist)
									inp.mouse_click = False
							else:
								ddt.text((x + (8 + 75) * gui.scale, y1, 1), _("Composer"), key_colour_off, 212)
							q = ddt.text(
								(x + (8 + 88) * gui.scale, y1),
								tc.composer,
								value_colour,
								value_font,
								max_w=120 * gui.scale,
							)
							if tauon.coll(rect):
								tauon.ex_tool_tip(x2 + 185 * gui.scale, y1, q, tc.composer, value_font_a)

							x -= int(170 * gui.scale)

						y1 += int(23 * gui.scale)

						total = tauon.star_store.get(gui.track_box_track_id)

						ratio = 0

						if total > 0 and pctl.master_library[gui.track_box_track_id].length > 1:
							ratio = total / (tc.length - 1)

						ddt.text((x1, y1), _("Play count"), key_colour_off, 212, max_w=70 * gui.scale)
						ddt.text((x2, y1), str(int(ratio)), value_colour, value_font)

						y1 += int(15 * gui.scale)

						rect = [x1, y1, 150, 14]

						if tauon.coll(rect) and inp.key_shift_down and inp.mouse_wheel != 0:
							tauon.star_store.add(gui.track_box_track_id, 60 * inp.mouse_wheel)

						line = time.strftime("%H:%M:%S", time.gmtime(total))

						ddt.text((x1, y1), _("Play time"), key_colour_off, 212, max_w=70 * gui.scale)
						ddt.text((x2, y1), str(line), value_colour, value_font)

						# -------
						if tc.lyrics:
							if pctl.draw.button(_("Lyrics"), x1 + 200 * gui.scale, y1 - 10 * gui.scale):
								prefs.show_lyrics_showcase = True
								gui.track_box = False
								tauon.enter_showcase_view(track_id=gui.track_box_track_id)
								inp.mouse_click = False

						if len(tc.comment) > 0:
							y1 += 20 * gui.scale
							rect = [x1, y1 + (2 * gui.scale), 60 * gui.scale, 14 * gui.scale]
							# ddt.rect_r((x2, y1, 335, 10), [255, 20, 20, 255])
							tauon.fields.add(rect)
							if tauon.coll(rect):
								ddt.text((x1, y1), _("Comment"), key_colour_on, 212)
								if inp.mouse_click:
									tauon.show_message(_("Copied text to clipboard"))
									copy_to_clipboard(tc.comment)
									inp.mouse_click = False
							else:
								ddt.text((x1, y1), _("Comment"), key_colour_off, 212)
							# ddt.draw_text((x1, y1), "Comment", key_colour_off, 12)

							if (
								"\n" not in tc.comment
								and ("http://" in tc.comment or "www." in tc.comment or "https://" in tc.comment)
								and ddt.get_text_w(tc.comment, 12) < 335 * gui.scale
							):
								link_pa = tauon.draw_linked_text((x2, y1), tc.comment, value_colour, 12)
								link_rect = [
									x + 98 * gui.scale + link_pa[0],
									y1 - 2 * gui.scale,
									link_pa[1],
									20 * gui.scale,
								]

								tauon.fields.add(link_rect)
								if tauon.coll(link_rect):
									if not inp.mouse_click:
										gui.cursor_want = 3
									if inp.mouse_click:
										webbrowser.open(link_pa[2], new=2, autoraise=True)
										gui.track_box = True

							elif comment_mode == 1:
								ddt.text(
									(x + 18 * gui.scale, y1 + 18 * gui.scale, 4, w - 36 * gui.scale, 90 * gui.scale),
									tc.comment,
									value_colour,
									12,
								)
							else:
								ddt.text((x2, y1), tc.comment, value_colour, 12)

				if tauon.draw_border and gui.mode != GuiMode.MINI:
					tool_rect = [window_size[0] - 110 * gui.scale, 2, 95 * gui.scale, 45 * gui.scale]
					if prefs.left_window_control:
						tool_rect[0] = 0
					tauon.fields.add(tool_rect)
					if not gui.top_bar_mode2 or tauon.coll(tool_rect):
						tauon.draw_window_tools()

					if not gui.fullscreen and not gui.maximized:
						tauon.draw_window_border()

				tauon.fader.render()
				if pref_box.enabled:
					# rect = [0, 0, window_size[0], window_size[1]]
					# ddt.rect_r(rect, [0, 0, 0, 90], True)
					pref_box.render()
				elif not Path(tauon.prefs.playlist_folder_path).is_dir():
					tauon.prefs.playlist_folder_path = ""
					prefs.autoscan_playlist_folder = False

				if gui.rename_folder_box:
					if gui.level_2_click:
						inp.mouse_click = True

					gui.level_2_click = False

					w = 500 * gui.scale
					h = 127 * gui.scale
					x = int(window_size[0] / 2) - int(w / 2)
					y = int(window_size[1] / 2) - int(h / 2)

					ddt.rect_a(
						(x - 2 * gui.scale, y - 2 * gui.scale),
						(w + 4 * gui.scale, h + 4 * gui.scale),
						colours.box_border,
					)
					ddt.rect_a((x, y), (w, h), colours.box_background)

					ddt.text_background_colour = colours.box_background

					if inp.key_esc_press or (
						(inp.mouse_click or inp.right_click or inp.level_2_right_click) and not tauon.coll((x, y, w, h))
					):
						gui.rename_folder_box = False

					p = ddt.text(
						(x + 10 * gui.scale, y + 9 * gui.scale), _("Folder Modification"), colours.box_title_text, 213
					)
					input_h = 23 * gui.scale

					if tauon.rename_folder.text != prefs.rename_folder_template and pctl.draw.button(
						_("Default"), x + (300 - 63) * gui.scale, y + 11 * gui.scale, 70 * gui.scale, input_h
					):
						tauon.rename_folder.set_text(prefs.rename_folder_template)
						tauon.rename_folder.offset = 0

					tauon.rename_folder.draw(
						x + 14 * gui.scale,
						y + 41 * gui.scale,
						colours.box_input_text,
						width=300 * gui.scale,
					)

					ddt.rect_s(
						(x + 8 * gui.scale, y + 38 * gui.scale, 300 * gui.scale, 22 * gui.scale),
						colours.box_text_border,
						1 * gui.scale,
					)

					if (
						pctl.draw.button(
							_("Rename"),
							x + (8 + 300 + 10) * gui.scale,
							y + 38 * gui.scale,
							80 * gui.scale,
							input_h,
							tooltip=_("Renames the physical folder based on the template"),
						)
						or inp.level_2_enter
					):
						tauon.rename_parent(gui.rename_index, tauon.rename_folder.text)
						gui.rename_folder_box = False
						inp.mouse_click = False

					text = _("Trash")
					tt = _("Moves folder to system trash")
					if inp.key_shift_down:
						text = _("Delete")
						tt = _("Physically deletes folder from disk")
					if pctl.draw.button(
						text,
						x + (8 + 300 + 10) * gui.scale,
						y + 11 * gui.scale,
						80 * gui.scale,
						input_h,
						text_highlight_colour=colours.grey(255),
						background_highlight_colour=ColourRGBA(180, 60, 60, 255),
						press=inp.mouse_up,
						tooltip=tt,
					):
						if inp.key_shift_down:
							tauon.delete_folder(gui.rename_index, True)
						else:
							tauon.delete_folder(gui.rename_index)
						gui.rename_folder_box = False
						inp.mouse_click = False

					if tauon.move_folder_up(gui.rename_index):
						if pctl.draw.button(
							_("Raise"),
							x + 408 * gui.scale,
							y + 38 * gui.scale,
							80 * gui.scale,
							tooltip=_("Moves folder up 2 levels and deletes the old container folder"),
						):
							tauon.move_folder_up(gui.rename_index, True)
							inp.mouse_click = False

					to_clean = tauon.clean_folder(gui.rename_index)
					if to_clean > 0:
						if pctl.draw.button(
							"Clean (" + str(to_clean) + ")",
							x + 408 * gui.scale,
							y + 11 * gui.scale,
							80 * gui.scale,
							tooltip=_("Deletes some unnecessary files from folder"),
						):
							tauon.clean_folder(gui.rename_index, True)
							inp.mouse_click = False

					ddt.text((x + 10 * gui.scale, y + 65 * gui.scale), _("PATH"), colours.box_text_label, 212)
					line = (
						os.path.dirname(pctl.master_library[gui.rename_index].parent_folder_path.rstrip("\\/")).replace(
							"\\", "/"
						)
						+ "/"
					)
					line = tauon.right_trunc(line, 12, 420 * gui.scale)
					line = clean_string(line)
					ddt.text((x + 60 * gui.scale, y + 65 * gui.scale), line, colours.grey(220), 211)

					ddt.text((x + 10 * gui.scale, y + 83 * gui.scale), _("OLD"), colours.box_text_label, 212)
					line = pctl.master_library[gui.rename_index].parent_folder_name
					line = clean_string(line)
					ddt.text(
						(x + 60 * gui.scale, y + 83 * gui.scale), line, colours.grey(220), 211, max_w=420 * gui.scale
					)

					ddt.text((x + 10 * gui.scale, y + 101 * gui.scale), _("NEW"), colours.box_text_label, 212)
					line = parse_template2(tauon.rename_folder.text, pctl.master_library[gui.rename_index])
					ddt.text(
						(x + 60 * gui.scale, y + 101 * gui.scale), line, colours.grey(220), 211, max_w=420 * gui.scale
					)

				if tauon.rename_track_box.active:
					tauon.rename_track_box.render()

				if tauon.sub_lyrics_box.active:
					tauon.sub_lyrics_box.render()

				if tauon.export_playlist_box.active:
					tauon.export_playlist_box.render()

				if tauon.trans_edit_box.active:
					tauon.trans_edit_box.render()

				if radiobox.active:
					radiobox.render()

				tauon.milk_choose.render()

				if gui.message_box:
					tauon.message_box.render()

				tauon.preset_download_box.render()

				if prefs.show_nag:
					tauon.nagbox.draw()

				# SEARCH
				# if inp.key_ctrl_down and inp.key_v_press:
				# 	tauon.search_over.active = True

				tauon.search_over.render()
				search_over = tauon.search_over

				if keymaps.test("quick-find") and gui.quick_search_mode is False:
					if not tauon.search_over.active and not gui.box_over:
						gui.quick_search_mode = True
					if tauon.search_clear_timer.get() > 3:
						search_over.search_text.text = ""
					inp.input_text = ""
				elif (keymaps.test("quick-find") or (inp.key_esc_press and len(gui.editline) == 0)) or (
					inp.mouse_click and gui.quick_search_mode is True
				):
					gui.quick_search_mode = False
					search_over.search_text.text = ""

				# if (key_backslash_press or (inp.key_ctrl_down and key_f_press)) and gui.quick_search_mode is False:
				# 	if not tauon.search_over.active:
				# 		gui.quick_search_mode = True
				# 	if tauon.search_clear_timer.get() > 3:
				# 		search_over.search_text.text = ""
				# 	input_text = ""
				# elif ((key_backslash_press or (inp.key_ctrl_down and key_f_press)) or (
				# 		inp.key_esc_press and len(gui.editline) == 0)) or input.mouse_click and gui.quick_search_mode is True:
				# 	gui.quick_search_mode = False
				# 	search_over.search_text.text = ""

				if gui.quick_search_mode is True:
					rect2 = [0, window_size[1] - 85 * gui.scale, 420 * gui.scale, 25 * gui.scale]
					rect = [0, window_size[1] - 125 * gui.scale, 420 * gui.scale, 65 * gui.scale]
					rect[0] = int(window_size[0] / 2) - int(rect[2] / 2)
					rect2[0] = rect[0]

					ddt.rect(
						(rect[0] - 2, rect[1] - 2, rect[2] + 4, rect[3] + 4), colours.box_border
					)  # [220, 100, 5, 255]
					# ddt.rect_r((rect[0], rect[1], rect[2], rect[3]), [255,120,5,255], True)

					ddt.text_background_colour = colours.box_background
					# ddt.text_background_colour = ColourRGBA(255,120,5,255)
					# ddt.text_background_colour = ColourRGBA(220,100,5,255)
					ddt.rect(rect, colours.box_background)

					if len(inp.input_text) > 0:
						gui.search_index = -1

					if inp.backspace_press and search_over.search_text.text == "":
						gui.quick_search_mode = False

					if len(search_over.search_text.text) == 0:
						gui.search_error = False

					if len(search_over.search_text.text) != 0 and search_over.search_text.text[0] == "/":
						# if "/love" in search_over.search_text.text:
						#     line = "last.fm loved tracks from user. Format: /love <username>"
						# else:
						line = _("Folder filter mode. Enter path segment.")
						ddt.text(
							(rect[0] + 23 * gui.scale, window_size[1] - 87 * gui.scale),
							line,
							ColourRGBA(220, 220, 220, 100),
							312,
						)
					else:
						line = _("UP / DOWN to navigate. SHIFT + RETURN for new playlist.")
						if len(search_over.search_text.text) == 0:
							line = _("Quick find")
						ddt.text(
							(rect[0] + int(rect[2] / 2), window_size[1] - 87 * gui.scale, 2),
							line,
							colours.box_text_label,
							312,
						)

						# ddt.draw_text((rect[0] + int(rect[2] / 2), window_size[1] - 118 * gui.scale, 2), "Find",
						#           colours.grey(90), 214)

					# if len(pctl.track_queue) > 0:

					# if inp.input_text == 'A':
					#     search_text.text = pctl.playing_object().artist
					#     inp.input_text = ""

					if gui.search_error:
						ddt.rect([rect[0], rect[1], rect[2], 30 * gui.scale], ColourRGBA(180, 40, 40, 255))
						ddt.text_background_colour = ColourRGBA(
							180, 40, 40, 255
						)  # alpha_blend(ColourRGBA(255,0,0,25), ddt.text_background_colour)
					# if input.backspace_press:
					#     gui.search_error = False

					search_over.search_text.draw(
						rect[0] + 8 * gui.scale, rect[1] + 6 * gui.scale, colours.grey(250), font=213
					)

					if (
						inp.key_shift_down
						or (len(search_over.search_text.text) > 0 and search_over.search_text.text[0] == "/")
					) and inp.key_return_press:
						inp.key_return_press = False
						playlist = []
						if len(search_over.search_text.text) > 0:
							if search_over.search_text.text[0] == "/":
								if (
									search_over.search_text.text.lower() == "/random"
									or search_over.search_text.text.lower() == "/shuffle"
								):
									tauon.gen_500_random(pctl.active_playlist_viewing)
								elif (
									search_over.search_text.text.lower() == "/top"
									or search_over.search_text.text.lower() == "/most"
								):
									tauon.gen_top_100(pctl.active_playlist_viewing)
								elif (
									search_over.search_text.text.lower() == "/length"
									or search_over.search_text.text.lower() == "/duration"
									or search_over.search_text.text.lower() == "/len"
								):
									tauon.gen_sort_len(pctl.active_playlist_viewing)
								else:
									if search_over.search_text.text[-1] == "/":
										tt_title = search_over.search_text.text.replace("/", "")
									else:
										search_over.search_text.text = search_over.search_text.text.replace("/", "")
										tt_title = search_over.search_text.text
									search_over.search_text.text = search_over.search_text.text.lower()
									for item in pctl.default_playlist:
										if (
											search_over.search_text.text
											in pctl.master_library[item].parent_folder_path.lower()
										):
											playlist.append(item)
									if len(playlist) > 0:
										pctl.multi_playlist.append(
											tauon.pl_gen(title=tt_title, playlist_ids=copy.deepcopy(playlist))
										)
										pctl.switch_playlist(len(pctl.multi_playlist) - 1)

							else:
								search_terms = search_over.search_text.text.lower().split()
								for item in pctl.default_playlist:
									tr = pctl.get_track(item)
									line = " ".join(
										[
											tr.title,
											tr.artist,
											tr.album,
											tr.fullpath,
											tr.composer,
											tr.comment,
											tr.album_artist,
											(tr.artist_sort if tr.artist_sort is not None else ""),
										]
									).lower()

									# if prefs.diacritic_search and all([ord(c) < 128 for c in search_over.search_text.text]):
									#     line = str(unidecode(line))

									if all(word in line for word in search_terms):
										playlist.append(item)
								if len(playlist) > 0:
									pctl.multi_playlist.append(
										tauon.pl_gen(title=_("Search Results"), playlist_ids=copy.deepcopy(playlist))
									)
									pctl.gen_codes[pctl.pl_to_id(len(pctl.multi_playlist) - 1)] = (
										's"'
										+ pctl.multi_playlist[pctl.active_playlist_viewing].title
										+ '" f"'
										+ search_over.search_text.text
										+ '"'
									)
									pctl.switch_playlist(len(pctl.multi_playlist) - 1)
							search_over.search_text.text = ""
							gui.quick_search_mode = False

					if (
						(len(inp.input_text) > 0 and not gui.search_error)
						or inp.key_down_press is True
						or inp.backspace_press
						or gui.force_search
					):
						gui.request_tracklist_redraw()

						if gui.force_search:
							gui.search_index = 0

						if inp.backspace_press:
							gui.search_index = 0

						if len(search_over.search_text.text) > 0 and search_over.search_text.text[0] != "/":
							oi = gui.search_index

							while gui.search_index < len(pctl.default_playlist) - 1:
								gui.search_index += 1
								if gui.search_index > len(pctl.default_playlist) - 1:
									gui.search_index = 0

								search_terms = search_over.search_text.text.lower().split()
								tr = pctl.get_track(pctl.default_playlist[gui.search_index])
								line = " ".join(
									[
										tr.title,
										tr.artist,
										tr.album,
										tr.fullpath,
										tr.composer,
										tr.comment,
										tr.album_artist,
										(tr.artist_sort if tr.artist_sort is not None else ""),
									]
								).lower()

								# if prefs.diacritic_search and all([ord(c) < 128 for c in search_over.search_text.text]):
								#     line = str(unidecode(line))

								if all(word in line for word in search_terms):
									pctl.selected_in_playlist = gui.search_index
									if len(pctl.default_playlist) > 10 and gui.search_index > 10:
										pctl.playlist_view_position = gui.search_index - 7
										logging.debug("Position changed by search")
									else:
										pctl.playlist_view_position = 0

									if gui.combo_mode:
										pctl.show_selected()
									gui.search_error = False

									break

							else:
								gui.search_index = oi
								if len(inp.input_text) > 0 or gui.force_search:
									gui.search_error = True
								if inp.key_down_press:
									tauon.bottom_playlist2.pulse()

							gui.force_search = False

					if (
						inp.key_up_press is True
						and not inp.key_shiftr_down
						and not inp.key_shift_down
						and not inp.key_ctrl_down
						and not inp.key_rctrl_down
						and not inp.key_meta
						and not inp.key_lalt
						and not inp.key_ralt
					):
						gui.request_tracklist_redraw()
						oi = gui.search_index

						while gui.search_index > 1:
							gui.search_index -= 1
							gui.search_index = min(gui.search_index, len(pctl.default_playlist) - 1)
							search_terms = search_over.search_text.text.lower().split()
							line = (
								pctl.master_library[pctl.default_playlist[gui.search_index]].title.lower()
								+ pctl.master_library[pctl.default_playlist[gui.search_index]].artist.lower()
								+ pctl.master_library[pctl.default_playlist[gui.search_index]].album.lower()
								+ pctl.master_library[pctl.default_playlist[gui.search_index]].filename.lower()
							)

							if prefs.diacritic_search and all([ord(c) < 128 for c in search_over.search_text.text]):
								line = str(unidecode(line))

							if all(word in line for word in search_terms):
								pctl.selected_in_playlist = gui.search_index
								if len(pctl.default_playlist) > 10 and gui.search_index > 10:
									pctl.playlist_view_position = gui.search_index - 7
									logging.debug("Position changed by search")
								else:
									pctl.playlist_view_position = 0
								if gui.combo_mode:
									pctl.show_selected()
								break
						else:
							gui.search_index = oi
							tauon.edge_playlist2.pulse()

					if inp.key_return_press is True and gui.search_index > -1:
						gui.request_tracklist_redraw()
						pctl.jump(pctl.default_playlist[gui.search_index], gui.search_index)
						if prefs.album_mode:
							tauon.goto_album(pctl.playlist_playing_position)
						gui.quick_search_mode = False
						tauon.search_clear_timer.set()
				elif not tauon.search_over.active:
					if inp.key_up_press and (
						(
							not inp.key_shiftr_down
							and not inp.key_shift_down
							and not inp.key_ctrl_down
							and not inp.key_rctrl_down
							and not inp.key_meta
							and not inp.key_lalt
							and not inp.key_ralt
						)
						or (keymaps.test("shift-up"))
					):
						pctl.show_selected()
						gui.request_tracklist_redraw()

						if not keymaps.test("shift-up"):
							if pctl.selected_in_playlist > 0:
								pctl.selected_in_playlist -= 1
							gui.shift_selection = []

						if (
							pctl.playlist_view_position > 0
							and pctl.selected_in_playlist < pctl.playlist_view_position + 2
						):
							pctl.playlist_view_position -= 1
							logging.debug("Position changed by key up")

							tauon.scroll_hide_timer.set()
							gui.frame_callback_list.append(TestTimer(0.9))

						pctl.selected_in_playlist = min(pctl.selected_in_playlist, len(pctl.default_playlist))
						tauon.sync_track_box_to_selected()

					if pctl.selected_in_playlist < len(pctl.default_playlist) and (
						(
							inp.key_down_press
							and not inp.key_shiftr_down
							and not inp.key_shift_down
							and not inp.key_ctrl_down
							and not inp.key_rctrl_down
							and not inp.key_meta
							and not inp.key_lalt
							and not inp.key_ralt
						)
						or keymaps.test("shift-down")
					):
						pctl.show_selected()
						gui.request_tracklist_redraw()

						if not keymaps.test("shift-down"):
							if pctl.selected_in_playlist < len(pctl.default_playlist) - 1:
								pctl.selected_in_playlist += 1
							gui.shift_selection = []

						if (
							pctl.playlist_view_position < len(pctl.default_playlist)
							and pctl.selected_in_playlist
							> pctl.playlist_view_position + gui.playlist_view_length - 3 - gui.row_extra
						):
							pctl.playlist_view_position += 1
							logging.debug("Position changed by key down")

							tauon.scroll_hide_timer.set()
							gui.frame_callback_list.append(TestTimer(0.9))

						pctl.selected_in_playlist = max(pctl.selected_in_playlist, 0)
						tauon.sync_track_box_to_selected()

					if (
						inp.key_return_press
						and not pref_box.enabled
						and not radiobox.active
						and not tauon.trans_edit_box.active
						and not gui.timed_lyrics_editing_now
						and not (gui.showcase_mode and gui.timed_lyrics_edit_view)
					):
						gui.request_tracklist_redraw()
						if pctl.selected_in_playlist > len(pctl.default_playlist) - 1:
							pctl.selected_in_playlist = 0
							gui.shift_selection = []
						if pctl.default_playlist:
							pctl.jump(pctl.default_playlist[pctl.selected_in_playlist], pctl.selected_in_playlist)
							if prefs.album_mode:
								tauon.goto_album(pctl.playlist_playing_position)
				tauon.touch_input_tracker.draw_update()
			elif gui.mode == GuiMode.MINI:
				if (inp.key_shift_down and inp.mouse_click) or inp.middle_click:
					if prefs.mini_mode_mode == MiniModeMode.TAB:
						prefs.mini_mode_mode = MiniModeMode.SQUARE
						size = (int(330 * gui.scale), int(330 * gui.scale))
					else:
						prefs.mini_mode_mode = MiniModeMode.TAB
						size = (int(320 * gui.scale), int(90 * gui.scale))

					logical_size[0] = size[0]
					logical_size[1] = size[1]
					window_size[0] = size[0]
					window_size[1] = size[1]

					tauon._set_wayland_mini_mode_window_state(True, size[0], size[1], reset_tracking=False)
					sdl3.SDL_SetWindowMinimumSize(t_window, size[0], size[1])
					sdl3.SDL_SetWindowSize(t_window, size[0], size[1])

				if prefs.mini_mode_mode == MiniModeMode.SLATE:
					tauon.mini_mode3.render()
				elif prefs.mini_mode_mode == MiniModeMode.SIGNAL:
					tauon.mini_mode_signal.render()
				elif prefs.mini_mode_mode == MiniModeMode.TAB:
					tauon.mini_mode2.render()
				else:
					tauon.mini_mode.render()

			t = tauon.toast_love_timer.get()
			if t < 1.8 and gui.toast_love_object is not None:
				track = gui.toast_love_object

				ww = gui.playlist_left or 0

				rect = (ww + 5 * gui.scale, gui.panelY + 5 * gui.scale, 235 * gui.scale, 39 * gui.scale)
				tauon.fields.add(rect)

				if tauon.coll(rect):
					tauon.toast_love_timer.force_set(10)
				else:
					ddt.rect(grow_rect(rect, 2 * gui.scale), colours.box_border)
					ddt.rect(rect, colours.queue_card_background)

					# fqo = copy.copy(pctl.force_queue[-1])

					ddt.text_background_colour = colours.queue_card_background

					if gui.toast_love_added:
						text = _("Loved track")
						gui.heart_notify_icon.render(
							rect[0] + 9 * gui.scale, rect[1] + 8 * gui.scale, ColourRGBA(250, 100, 100, 255)
						)
					else:
						text = _("Un-Loved track")
						gui.heart_notify_break_icon.render(
							rect[0] + 9 * gui.scale, rect[1] + 7 * gui.scale, ColourRGBA(150, 150, 150, 255)
						)

					ddt.text_background_colour = colours.queue_card_background
					ddt.text((rect[0] + 42 * gui.scale, rect[1] + 3 * gui.scale), text, colours.box_text, 313)
					ddt.text(
						(rect[0] + 42 * gui.scale, rect[1] + 20 * gui.scale),
						f"{track.track_number}. {track.artist} - {track.title}".strip(".- "),
						colours.box_text_label,
						13,
						max_w=rect[2] - 50 * gui.scale,
					)

			t = tauon.queue_add_timer.get()
			if t < 2.5 and gui.toast_queue_object:
				track = pctl.get_track(gui.toast_queue_object.track_id)

				ww = gui.playlist_left or 0
				if tauon.search_over.active:
					ww = window_size[0] // 2 - (215 * gui.scale // 2)

				rect = (ww + 5 * gui.scale, gui.panelY + 5 * gui.scale, 215 * gui.scale, 39 * gui.scale)
				tauon.fields.add(rect)

				if tauon.coll(rect):
					tauon.queue_add_timer.force_set(10)
				elif len(pctl.force_queue) > 0:
					fqo = copy.copy(pctl.force_queue[-1])

					ddt.rect(grow_rect(rect, 2 * gui.scale), colours.box_border)
					ddt.rect(rect, colours.queue_card_background)

					ddt.text_background_colour = colours.queue_card_background
					top_text = _("Track")
					if gui.queue_toast_plural:
						top_text = "Album"
						fqo.type = QueueType.ALBUM
					if pctl.force_queue[-1].type == QueueType.ALBUM:
						top_text = "Album"

					tauon.queue_box.draw_card(
						rect[0] - 8 * gui.scale,
						0,
						160 * gui.scale,
						210 * gui.scale,
						rect[1] + 1 * gui.scale,
						track,
						fqo,
						True,
						False,
					)

					ddt.text_background_colour = colours.queue_card_background
					ddt.text(
						(rect[0] + rect[2] - 50 * gui.scale, rect[1] + 3 * gui.scale, 2),
						f"{top_text} added",
						colours.box_text_label,
						11,
					)
					ddt.text(
						(rect[0] + rect[2] - 50 * gui.scale, rect[1] + 15 * gui.scale, 2),
						"to queue",
						colours.box_text_label,
						11,
					)

			t = tauon.toast_mode_timer.get()
			if t < gui.toast_length:
				wid = ddt.get_text_w(gui.mode_toast_text, 313)
				wid = max(round(68 * gui.scale), wid)

				ww = round(7 * gui.scale)
				if gui.playlist_left and not gui.combo_mode:
					ww += gui.playlist_left

				rect = (ww + 8 * gui.scale, gui.panelY + 15 * gui.scale, wid + 20 * gui.scale, 25 * gui.scale)
				tauon.fields.add(rect)

				if tauon.coll(rect):
					tauon.toast_mode_timer.force_set(10)
				else:
					ddt.rect(grow_rect(rect, round(2 * gui.scale)), colours.grey(60))
					ddt.rect(rect, colours.queue_card_background)

					ddt.text_background_colour = colours.queue_card_background
					ddt.text(
						(rect[0] + (rect[2] // 2), rect[1] + 4 * gui.scale, 2),
						gui.mode_toast_text,
						colours.grey(230),
						313,
					)

			# Render Menus-------------------------------
			tauon.draw_popup_menus()

			if tauon.view_box.active:
				tauon.view_box.render()

			tauon.tool_tip.render()
			tauon.tool_tip2.render()

			if tauon.console.fps_only:
				tauon.console.diagnostic_tick()
				fps_rect = (
					window_size[0] - 90 * gui.scale,
					40 * gui.scale,
					70 * gui.scale,
					22 * gui.scale,
				)
				ddt.rect(fps_rect, ColourRGBA(0, 0, 0, 245))
				ddt.text(
					(fps_rect[0] + 8 * gui.scale, fps_rect[1] + 4 * gui.scale),
					f"{tauon.console.diagnostic_fps()} FPS",
					ColourRGBA(120, 120, 120, 255),
					311,
					bg=ColourRGBA(5, 5, 5, 255),
				)

			if tauon.console.show:
				rect = (20 * gui.scale, 40 * gui.scale, 580 * gui.scale, 200 * gui.scale)
				ddt.rect(rect, ColourRGBA(0, 0, 0, 245))

				tauon.console.fps.tick()
				fps_rect = (rect[0] + rect[2] + 8 * gui.scale, rect[1], 70 * gui.scale, 22 * gui.scale)
				ddt.rect(fps_rect, ColourRGBA(0, 0, 0, 245))
				ddt.text(
					(fps_rect[0] + 8 * gui.scale, fps_rect[1] + 4 * gui.scale),
					f"{int(round(tauon.console.fps.get()))} FPS",
					ColourRGBA(120, 120, 120, 255),
					311,
					bg=ColourRGBA(5, 5, 5, 255),
				)

				if pctl.playing_state == PlayingState.PLAYING:
					gui.delay_frame(0.05)

				yy = rect[3] + 15 * gui.scale
				u = False
				for record in reversed(tauon.log.log_history):
					if yy < rect[1] + 5 * gui.scale:
						break

					text_colour = ColourRGBA(60, 255, 60, 255)
					message = tauon.log.format(record)

					t = record.created
					d = time.time() - t
					dt = time.localtime(t)

					fade = 255
					if d > 2:
						fade = 200

					text_colour = ColourRGBA(120, 120, 120, fade)
					if record.levelno == 10:
						text_colour = ColourRGBA(80, 80, 80, fade)
					if record.levelno == 30:
						text_colour = ColourRGBA(230, 190, 90, fade)
					if record.levelno == 40:
						text_colour = ColourRGBA(255, 120, 90, fade)
					if record.levelno == 50:
						text_colour = ColourRGBA(255, 90, 90, fade)

					time_colour = ColourRGBA(255, 80, 160, fade)

					w = ddt.text(
						(rect[0] + 10 * gui.scale, yy),
						time.strftime("%H:%M:%S", dt),
						time_colour,
						311,
						rect[2] - 60 * gui.scale,
						bg=ColourRGBA(5, 5, 5, 255),
					)

					ddt.text(
						(w + rect[0] + 17 * gui.scale, yy),
						message,
						text_colour,
						311,
						rect[2] - 60 * gui.scale,
						bg=ColourRGBA(5, 5, 5, 255),
					)
					yy -= 14 * gui.scale
				if u:
					gui.delay_frame(5)

				if pctl.draw.button("Copy", rect[0] + rect[2] - 55 * gui.scale, rect[1] + rect[3] - 30 * gui.scale):
					text = ""
					for record in tauon.log.log_history[-50:]:
						t = record.created
						dt = time.localtime(t)
						text += time.strftime("%H:%M:%S", dt) + " " + tauon.log.format(record) + "\n"
					copy_to_clipboard(text)
					tauon.show_message(_("Lines copied to clipboard"), mode="done")

				# Track stream/buffer status graph
				try:
					s_aud = tauon.aud
					if s_aud is not None and hasattr(s_aud, "get_stream_stats"):
						colour_buffered = ColourRGBA(45, 110, 220, 255)
						colour_decoded = ColourRGBA(50, 200, 110, 255)
						colour_position = ColourRGBA(255, 80, 160, 255)
						colour_pcm = ColourRGBA(240, 180, 60, 255)
						colour_meta = ColourRGBA(150, 95, 220, 255)
						colour_behind = ColourRGBA(58, 64, 90, 255)
						colour_track = ColourRGBA(38, 38, 44, 255)
						colour_text = ColourRGBA(140, 140, 150, 255)
						text_bg = ColourRGBA(5, 5, 5, 255)

						gx = rect[0]
						gy = rect[1] + rect[3] + 6 * gui.scale
						gw = rect[2]
						gh = 66 * gui.scale
						ddt.rect((gx, gy, gw, gh), ColourRGBA(0, 0, 0, 245))

						bar_x = round(gx + 10 * gui.scale)
						bar_w = round(gw - 20 * gui.scale)
						bar_y = round(gy + 8 * gui.scale)
						bar_h = round(13 * gui.scale)

						s_size = ctypes.c_longlong(0)
						s_start = ctypes.c_longlong(0)
						s_end = ctypes.c_longlong(0)
						s_pos = ctypes.c_longlong(0)
						s_meta = ctypes.c_longlong(0)
						s_net = ctypes.c_int(0)
						s_eof = ctypes.c_int(0)
						s_active = s_aud.get_stream_stats(
							ctypes.byref(s_size), ctypes.byref(s_start), ctypes.byref(s_end),
							ctypes.byref(s_pos), ctypes.byref(s_meta), ctypes.byref(s_net), ctypes.byref(s_eof))

						pcm_ms = s_aud.get_buffered_ms() if hasattr(s_aud, "get_buffered_ms") else 0

						# Byte map of the file, in playback order: playhead,
						# then decoded-but-not-yet-played (the PCM buffer
						# contents), then buffered data waiting on the decoder
						ddt.rect((bar_x, bar_y, bar_w, bar_h), colour_track)
						if s_active and s_size.value > 0:

							def stream_graph_x(v: int) -> int:
								return round(bar_x + bar_w * min(max(v / s_size.value, 0.0), 1.0))

							# Estimate the playhead's byte offset by rewinding
							# the decode position by the PCM buffer's duration
							# at the track's average audio byte rate
							pos_byte = s_pos.value
							if pctl.playing_length > 0:
								audio_bytes = max(s_size.value - s_meta.value, 1)
								pos_byte = s_pos.value - round(pcm_ms / 1000 * (audio_bytes / pctl.playing_length))
							pos_byte = min(max(pos_byte, s_start.value, s_meta.value), s_pos.value)

							window_x = stream_graph_x(s_start.value)
							window_e = stream_graph_x(s_end.value)
							decode_x = stream_graph_x(s_pos.value)
							play_x = stream_graph_x(pos_byte)

							# Already played but still kept in memory for quick back-seeks
							if play_x > window_x:
								ddt.rect((window_x, bar_y, play_x - window_x, bar_h), colour_behind)
							# Decoded ahead of playback (matches the PCM bar below)
							if decode_x > play_x:
								ddt.rect((play_x, bar_y, decode_x - play_x, bar_h), colour_decoded)
							# Downloaded, waiting on the decoder
							if window_e > decode_x:
								ddt.rect((decode_x, bar_y, window_e - decode_x, bar_h), colour_buffered)
							# Leading metadata block (tags/embedded art)
							if s_meta.value > 0:
								meta_x = stream_graph_x(s_meta.value)
								if meta_x > bar_x:
									ddt.rect((bar_x, bar_y, meta_x - bar_x, bar_h), colour_meta)
							# Playhead
							ddt.rect(
								(play_x, round(bar_y - 2 * gui.scale),
									max(round(1 * gui.scale), 1), round(bar_h + 4 * gui.scale)),
								colour_position)

						# Decoded PCM buffer fill (holds up to ~5s of audio)
						pcm_y = round(bar_y + bar_h + 6 * gui.scale)
						pcm_h = round(5 * gui.scale)
						ddt.rect((bar_x, pcm_y, bar_w, pcm_h), colour_track)
						ddt.rect((bar_x, pcm_y, round(bar_w * min(pcm_ms / 5000, 1.0)), pcm_h), colour_pcm)

						# Legend and numbers (values quantised to limit text cache churn)
						ty = pcm_y + pcm_h + 5 * gui.scale
						lx = bar_x
						for swatch, label in (
							(colour_position, _("Position")),
							(colour_meta, _("Metadata")),
							(colour_decoded, _("Decoded")),
							(colour_buffered, _("Buffered")),
							(colour_pcm, _("PCM {n}ms").format(n=pcm_ms - pcm_ms % 100)),
						):
							# Text y is relative to the baseline area; glyph caps sit
							# roughly 4-13px (scaled) below it, centre the swatch on that
							ddt.rect((round(lx), round(ty + 5 * gui.scale), round(7 * gui.scale), round(7 * gui.scale)), swatch)
							lw = ddt.text((lx + 11 * gui.scale, ty), label, colour_text, 311, bg=text_bg) or 0
							lx += lw + 20 * gui.scale

						if s_active:
							line = "NET" if s_net.value else "LOCAL"
							if s_size.value > 0:
								line += f"  {(s_end.value - s_start.value) / 1000000:.1f} / {s_size.value / 1000000:.1f} MB"
							if s_eof.value:
								line += "  EOF"
						else:
							line = _("No stream")
						stream_feeder = getattr(tauon, "stream_feeder", None)
						if stream_feeder is not None and stream_feeder.speed > 0:
							line += f"  |  {stream_feeder.speed / 1000:.0f} kB/s"
						ddt.text((bar_x + bar_w, ty, 1), line, colour_text, 311, bg=text_bg)
				except Exception:
					logging.exception("Stream status graph failed")

			if gui.cursor_is != gui.cursor_want:
				gui.cursor_is = gui.cursor_want

				if gui.cursor_is == 0:
					sdl3.SDL_SetCursor(gui.cursor_standard)
				elif gui.cursor_is == 1:
					sdl3.SDL_SetCursor(gui.cursor_shift)
				elif gui.cursor_is == 2:
					sdl3.SDL_SetCursor(gui.cursor_text)
				elif gui.cursor_is == 3:
					sdl3.SDL_SetCursor(gui.cursor_hand)
				elif gui.cursor_is == 4:
					sdl3.SDL_SetCursor(gui.cursor_br_corner)
				elif gui.cursor_is == 8:
					sdl3.SDL_SetCursor(gui.cursor_right_side)
				elif gui.cursor_is == 9:
					sdl3.SDL_SetCursor(gui.cursor_top_side)
				elif gui.cursor_is == 10:
					sdl3.SDL_SetCursor(gui.cursor_left_side)
				elif gui.cursor_is == 11:
					sdl3.SDL_SetCursor(gui.cursor_bottom_side)
				elif gui.cursor_is == 12:
					# Vertical-resize cursor (NS) — used by the Custom Layout boundaries.
					sdl3.SDL_SetCursor(gui.cursor_ns)

			tauon.input_sdl.test_capture_mouse()
			tauon.input_sdl.mouse_capture_want = False

			# # Quick view
			# quick_view_box.render()

			# Drag icon next to cursor
			if (
				inp.quick_drag
				and inp.mouse_down
				and not point_proximity_test(gui.drag_source_position, inp.mouse_position, 15 * gui.scale)
			):
				i_x, i_y = tauon.input_sdl.mouse()
				gui.drag_source_position = (0, 0)

				block_size = round(10 * gui.scale)
				x_offset = round(20 * gui.scale)
				y_offset = round(1 * gui.scale)

				if len(gui.shift_selection) == 1:  # Single track
					ddt.rect((i_x + x_offset, i_y + y_offset, block_size, block_size), ColourRGBA(160, 140, 235, 240))
				elif inp.key_ctrl_down:  # Add to queue undrouped
					small_block = round(6 * gui.scale)
					spacing = round(2 * gui.scale)
					ddt.rect((i_x + x_offset, i_y + y_offset, small_block, small_block), ColourRGBA(160, 140, 235, 240))
					ddt.rect(
						(i_x + x_offset + spacing + small_block, i_y + y_offset, small_block, small_block),
						ColourRGBA(160, 140, 235, 240),
					)
					ddt.rect(
						(i_x + x_offset, i_y + y_offset + spacing + small_block, small_block, small_block),
						ColourRGBA(160, 140, 235, 240),
					)
					ddt.rect(
						(
							i_x + x_offset + spacing + small_block,
							i_y + y_offset + spacing + small_block,
							small_block,
							small_block,
						),
						ColourRGBA(160, 140, 235, 240),
					)
					ddt.rect(
						(
							i_x + x_offset,
							i_y + y_offset + spacing + small_block + spacing + small_block,
							small_block,
							small_block,
						),
						ColourRGBA(160, 140, 235, 240),
					)
					ddt.rect(
						(
							i_x + x_offset + spacing + small_block,
							i_y + y_offset + spacing + small_block + spacing + small_block,
							small_block,
							small_block,
						),
						ColourRGBA(160, 140, 235, 240),
					)

				else:  # Multiple tracks
					long_block = round(25 * gui.scale)
					ddt.rect((i_x + x_offset, i_y + y_offset, block_size, long_block), ColourRGBA(160, 140, 235, 240))

				# gui.update += 1
				gui.update_on_drag = True

			# Drag pl tab next to cursor
			if (
				(tauon.playlist_box.drag)
				and inp.mouse_down
				and not point_proximity_test(gui.drag_source_position, inp.mouse_position, 10 * gui.scale)
			):
				i_x, i_y = tauon.input_sdl.mouse()
				gui.drag_source_position = (0, 0)
				ddt.rect(
					(i_x + 20 * gui.scale, i_y + 3 * gui.scale, int(50 * gui.scale), int(15 * gui.scale)),
					ColourRGBA(50, 50, 50, 225),
				)
				# ddt.rect_r((i_x + 20 * gui.scale, i_y + 1 * gui.scale, int(60 * gui.scale), int(15 * gui.scale)), [240, 240, 240, 255], True)
				# ddt.draw_text((i_x + 75 * gui.scale, i_y - 0 * gui.scale, 1), pctl.multi_playlist[tauon.playlist_box.drag_on].title, ColourRGBA(30, 30, 30, 255), 212, bg=[240, 240, 240, 255])
			if tauon.radio_view.drag and not point_proximity_test(
				tauon.radio_view.click_point, inp.mouse_position, round(4 * gui.scale)
			):
				ddt.rect(
					(
						inp.mouse_position[0] + round(8 * gui.scale),
						inp.mouse_position[1] - round(8 * gui.scale),
						48 * gui.scale,
						14 * gui.scale,
					),
					colours.grey(70),
				)
			if (gui.set_label_hold != -1) and inp.mouse_down:
				gui.update_on_drag = True

				if not point_proximity_test(gui.set_label_point, inp.mouse_position, 3):
					i_x, i_y = tauon.input_sdl.mouse()
					gui.set_label_point = (0, 0)

					w = ddt.get_text_w(gui.pl_st[gui.set_label_hold][0], 212)
					w = max(w, 45 * gui.scale)
					ddt.rect(
						(i_x + 25 * gui.scale, i_y + 1 * gui.scale, w + int(20 * gui.scale), int(15 * gui.scale)),
						ColourRGBA(240, 240, 240, 255),
					)
					ddt.text(
						(i_x + 25 * gui.scale + w + int(20 * gui.scale) - 4 * gui.scale, i_y - 0 * gui.scale, 1),
						gui.pl_st[gui.set_label_hold][0],
						ColourRGBA(30, 30, 30, 255),
						212,
						bg=ColourRGBA(240, 240, 240, 255),
					)

			inp.input_text = ""

			# logging.info("FRAME " + str(tauon.core_timer.get()))
			gui.present = True

			sdl3.SDL_SetRenderTarget(renderer, None)
			if tauon.dream_room.active:
				# Dream Room: compose the frame as a 3D scene with the UI on a
				# monitor instead of blitting it fullscreen
				tauon.dream_room.render()
			else:
				sdl3.SDL_RenderTexture(renderer, gui.main_texture, None, gui.tracklist_texture_rect)

			if gui.turbo:
				gui.level_update = True

		# if gui.vis == 1 and pctl.playing_state != PlayingState.PLAYING and gui.level_peak != [0, 0] and gui.turbo:
		# 	# logging.info(gui.level_peak)
		# 	gui.time_passed = gui.level_time.hit()
		# 	if gui.time_passed > 1:
		# 		gui.time_passed = 0
		# 	while gui.time_passed > 0.01:
		# 		gui.level_peak[1] -= 0.5
		# 		if gui.level_peak[1] < 0:
		# 			gui.level_peak[1] = 0
		# 		gui.level_peak[0] -= 0.5
		# 		if gui.level_peak[0] < 0:
		# 			gui.level_peak[0] = 0
		# 		gui.time_passed -= 0.020
		# 	gui.level_update = True

		# gui.turbo = True
		# gui.vis = 5
		# gui.level_update = True

		if gui.level_update is True and not resize_mode and gui.mode != GuiMode.MINI and not tauon.dream_room.active:
			gui.level_update = False

			sdl3.SDL_SetRenderTarget(renderer, None)
			if not gui.present:
				sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_NONE)
				sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
				sdl3.SDL_RenderClear(renderer)
				sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)
				sdl3.SDL_RenderTexture(renderer, gui.main_texture, None, gui.tracklist_texture_rect)
				gui.present = True

			if gui.vis == 5:
				# milky
				pass

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

					sdl3.SDL_SetRenderTarget(renderer, gui.spec2_tex)
					# Replace-blend: vis_bg may be translucent (frosted art
					# bg) and old column pixels must not show through it
					sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_NONE)
					for i, value in enumerate(gui.spec2_buffers[0]):
						ddt.rect([gui.spec2_position, i, 1, 1], colours.vis_bg)
					sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)

					del gui.spec2_buffers[0]

					gui.spec2_position += 1

					if gui.spec2_position > gui.spec2_w - 1:
						gui.spec2_position = 0

					sdl3.SDL_SetRenderTarget(renderer, None)

				#
				# else:
				#     logging.info("animation stall" + str(random.randint(1, 10)))

				if prefs.spec2_scroll:
					gui.spec2_source.x = 0
					gui.spec2_source.y = 0
					gui.spec2_source.w = gui.spec2_position
					gui.spec2_dest.x = gui.spec2_rec.x + gui.spec2_rec.w - gui.spec2_position
					gui.spec2_dest.w = gui.spec2_position
					sdl3.SDL_RenderTexture(renderer, gui.spec2_tex, gui.spec2_source, gui.spec2_dest)

					gui.spec2_source.x = gui.spec2_position
					gui.spec2_source.y = 0
					gui.spec2_source.w = gui.spec2_rec.w - gui.spec2_position
					gui.spec2_dest.x = gui.spec2_rec.x
					gui.spec2_dest.w = gui.spec2_rec.w - gui.spec2_position
					sdl3.SDL_RenderTexture(renderer, gui.spec2_tex, gui.spec2_source, gui.spec2_dest)
				else:
					sdl3.SDL_RenderTexture(renderer, gui.spec2_tex, None, gui.spec2_rec)

				if pref_box.enabled:
					# ddt.rect((gui.spec2_rec.x, gui.spec2_rec.y, gui.spec2_rec.w, gui.spec2_rec.h), ColourRGBA(0, 0, 0, 90))
					logging.info("spectrogram box")
					ddt.rect((gui.spec2_rec.x, gui.spec2_rec.y, gui.spec2_rec.w, gui.spec2_rec.h), colours.vis_bg)

			if gui.vis == 4 and gui.draw_vis4_top:
				showcase.render_vis(True)
				# gui.level_update = False

			if gui.vis == 2 and gui.spec is not None:
				# Standard spectrum visualiser
				if gui.update_spec == 0 and pctl.playing_state != PlayingState.PAUSED:
					if tauon.vis_decay_timer.get() > 0.007:  # Controls speed of decay after stop
						tauon.vis_decay_timer.set()
						for i in range(len(gui.spec)):
							if gui.s_spec[i] > 0:
								if gui.spec[i] > 0:
									gui.spec[i] -= 1
								gui.level_update = True
					else:
						gui.level_update = True

				if tauon.vis_rate_timer.get() > 0.027:  # Limit the change rate #to 60 fps
					tauon.vis_rate_timer.set()

					if spec_smoothing and pctl.playing_state != PlayingState.STOPPED:
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

					else:
						gui.s_spec = gui.spec
				else:
					pass

				if not gui.test:
					sdl3.SDL_SetRenderTarget(renderer, gui.spec1_tex)

					# Replace-blend: vis_bg may be translucent (frosted art
					# bg) and the texture persists between frames
					sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_NONE)
					ddt.rect((0, 0, gui.spec_w, gui.spec_h), colours.vis_bg)
					sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)

					# xx = 0
					gui.bar.x = 0
					on = 0

					sdl3.SDL_SetRenderDrawColor(
						renderer, colours.vis_colour.r, colours.vis_colour.g, colours.vis_colour.b, colours.vis_colour.a
					)

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

						sdl3.SDL_RenderFillRect(renderer, gui.bar)

						gui.bar.x += round(4 * gui.scale)

					if tauon.pref_box.enabled:
						ddt.rect((0, 0, gui.spec_w, gui.spec_h), ColourRGBA(0, 0, 0, 90))

					sdl3.SDL_SetRenderTarget(renderer, None)
					sdl3.SDL_RenderTexture(renderer, gui.spec1_tex, None, gui.spec1_rec)

			if gui.vis == 1:
				if prefs.backend == Backend.GSTREAMER or True:
					if pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM):
						# gui.level_update = True
						while tauon.level_train and tauon.level_train[0][0] < time.time():
							l = tauon.level_train[0][1]
							r = tauon.level_train[0][2]

							gui.level_peak[0] = max(r, gui.level_peak[0])
							gui.level_peak[1] = max(l, gui.level_peak[1])

							del tauon.level_train[0]

					else:
						tauon.level_train.clear()

				sdl3.SDL_SetRenderTarget(renderer, gui.spec_level_tex)

				x = window_size[0] - 20 * gui.scale - gui.offset_extra
				y = gui.level_y
				w = gui.level_w
				s = gui.level_s

				y = 0

				gui.spec_level_rec.x = round(x - 70 * gui.scale)
				# Frosted art bg: translucent backing (replace-blend, since
				# the texture persists between frames)
				level_bg = colours.grey(10)
				if gui.have_art_bg and prefs.art_bg_frosted:
					level_bg = ColourRGBA(10, 10, 10, 115)
				sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_NONE)
				ddt.rect_a((0, 0), (79 * gui.scale, 18 * gui.scale), level_bg)
				sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)

				x = round(gui.level_ww - 9 * gui.scale)
				y = 10 * gui.scale

				if prefs.backend == Backend.GSTREAMER or True:
					if gui.level_peak[0] > 0 or gui.level_peak[1] > 0:
						# gui.level_update = True
						if pctl.playing_time < 1:
							gui.delay_frame(0.032)

						if pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM):
							t = gui.level_decay_timer.hit()
							decay = 14 * t
							gui.level_peak[1] -= decay
							gui.level_peak[0] -= decay
						elif pctl.playing_state in (PlayingState.STOPPED, PlayingState.PAUSED):
							gui.level_update = True
							t = gui.level_decay_timer.hit()
							decay = 16 * t
							gui.level_peak[1] -= decay
							gui.level_peak[0] -= decay

				for t in range(12):
					met = False if gui.level_peak[0] < t else True
					if gui.level_peak[0] < 0.2:
						met = False
					if gui.level_meter_colour_mode == 1:
						if not met:
							cc = ColourRGBA(15, 10, 20, 255)
						else:
							cc = colorsys.hls_to_rgb(0.68 + (t * 0.015), 0.4, 0.7)
							cc = ColourRGBA(int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)
					elif gui.level_meter_colour_mode == 2:
						if not met:
							cc = ColourRGBA(11, 11, 13, 255)
						else:
							cc = colorsys.hls_to_rgb(0.63 - (t * 0.015), 0.4, 0.7)
							cc = ColourRGBA(int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)
					elif gui.level_meter_colour_mode == 3:
						if not met:
							cc = ColourRGBA(12, 6, 0, 255)
						else:
							cc = colorsys.hls_to_rgb(0.11 - (t * 0.010), 0.4, 0.7 + (t * 0.02))
							cc = ColourRGBA(int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)
					elif gui.level_meter_colour_mode == 4:
						if not met:
							cc = ColourRGBA(10, 10, 10, 255)
						else:
							cc = colorsys.hls_to_rgb(0.3 - (t * 0.03), 0.4, 0.7 + (t * 0.02))
							cc = ColourRGBA(int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)
					elif t < 7:
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
					if gui.level > 0 and pctl.playing_state != PlayingState.STOPPED:
						pass
					ddt.rect_a(((x - (w * t) - (s * t)), y), (w, w), cc)

				y -= 7 * gui.scale
				for t in range(12):
					met = not gui.level_peak[1] < t
					if gui.level_peak[1] < 0.2:
						met = False

					if gui.level_meter_colour_mode == 1:
						if not met:
							cc = ColourRGBA(15, 10, 20, 255)
						else:
							cc = colorsys.hls_to_rgb(0.68 + (t * 0.015), 0.4, 0.7)
							cc = ColourRGBA(int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)

					elif gui.level_meter_colour_mode == 2:
						if not met:
							cc = ColourRGBA(11, 11, 13, 255)
						else:
							cc = colorsys.hls_to_rgb(0.63 - (t * 0.015), 0.4, 0.7)
							cc = ColourRGBA(int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)

					elif gui.level_meter_colour_mode == 3:
						if not met:
							cc = ColourRGBA(12, 6, 0, 255)
						else:
							cc = colorsys.hls_to_rgb(0.11 - (t * 0.010), 0.4, 0.7 + (t * 0.02))
							cc = ColourRGBA(int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)

					elif gui.level_meter_colour_mode == 4:
						if not met:
							cc = ColourRGBA(10, 10, 10, 255)
						else:
							cc = colorsys.hls_to_rgb(0.3 - (t * 0.03), 0.4, 0.7 + (t * 0.02))
							cc = ColourRGBA(int(cc[0] * 255), int(cc[1] * 255), int(cc[2] * 255), 255)

					elif t < 7:
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

					if gui.level > 0 and pctl.playing_state != PlayingState.STOPPED:
						pass
					ddt.rect_a(((x - (w * t) - (s * t)), y), (w, w), cc)

				sdl3.SDL_SetRenderTarget(renderer, None)
				sdl3.SDL_RenderTexture(renderer, gui.spec_level_tex, None, gui.spec_level_rec)

		if gui.present:
			sdl3.SDL_SetRenderTarget(renderer, None)
			tauon.render_rounded_corners()
			sdl3.SDL_RenderPresent(renderer)

			gui.present = False

		# -------------------------------------------------------------------------------------------
		# Misc things to update every tick

		# Update d-bus metadata on Linux
		if (pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM)) and pctl.mpris is not None:
			pctl.mpris.update_progress()

		# GUI time ticker update
		if (pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM)) and gui.lowered is False:
			if int(pctl.playing_time) != int(pctl.last_playing_time):
				pctl.last_playing_time = pctl.playing_time
				tauon.bottom_bar1.seek_time = pctl.playing_time
				if not prefs.power_save or window_is_focused(tauon.t_window):
					gui.request_frame()

		# Auto save play times to disk
		if pctl.total_playtime - time_last_save > 600:
			try:
				if bag.should_save_state:
					logging.info("Auto save playtime")
					with atomic_save(user_directory / "star.p") as file:
						pickle.dump(tauon.star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)
				else:
					logging.info("Dev mode, skip auto saving playtime")
			except PermissionError:
				logging.exception("Permission error encountered while writing database")
				tauon.show_message(_("Permission error encountered while writing database"), "error")
			except Exception:
				logging.exception("Unknown error encountered while writing database")
			time_last_save = pctl.total_playtime

		# Always render at least one frame per minute (to avoid SDL bugs I guess)
		if tauon.min_render_timer.get() > 60:
			tauon.min_render_timer.set()
			gui.request_tracklist_redraw()
			gui.request_frame()

		# Save power if the window is minimized
		if gui.lowered:
			time.sleep(0.2)

	# Send scrobble if pending
	if tauon.lfm_scrobbler.queue and not tauon.lfm_scrobbler.running:
		tauon.lfm_scrobbler.start_queue()
		logging.info("Sending scrobble before close...")

	if gui.mode == GuiMode.MAIN:
		tauon.old_window_position = get_window_position(t_window)

	sdl3.SDL_DestroyTexture(gui.main_texture)
	sdl3.SDL_DestroyTexture(gui.tracklist_texture)
	sdl3.SDL_DestroyTexture(gui.spec2_tex)
	sdl3.SDL_DestroyTexture(gui.spec1_tex)
	sdl3.SDL_DestroyTexture(gui.spec_level_tex)
	ddt.clear_text_cache()
	tauon.clear_img_cache(False)

	sdl3.SDL_DestroyWindow(t_window)

	pctl.playerCommand = "unload"
	pctl.playerCommandReady = True

	if prefs.reload_play_state and pctl.playing_state in (PlayingState.PLAYING, PlayingState.PAUSED):
		logging.info("Saving play state...")
		prefs.reload_state = (pctl.playing_state, pctl.playing_time)
	else:
		prefs.reload_state = None

	if bag.should_save_state:
		with atomic_save(user_directory / "star.p") as file:
			pickle.dump(tauon.star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)
		with atomic_save(user_directory / "album-star.p") as file:
			pickle.dump(tauon.album_star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)

	gui.gallery_positions[pctl.pl_to_id(pctl.active_playlist_viewing)] = gui.album_scroll_px
	tauon.save_state()

	date = datetime.date.today()
	if bag.should_save_state:
		with atomic_save(user_directory / "star.p.backup") as file:
			pickle.dump(tauon.star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)
		with atomic_save(user_directory / f"star.p.backup{date.month!s}") as file:
			pickle.dump(tauon.star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)

	if tauon.stream_proxy and tauon.stream_proxy.download_running:
		logging.info("Stopping stream...")
		tauon.stream_proxy.stop()
		time.sleep(2)

	try:
		if tauon.thread_manager.player_lock.locked():
			tauon.thread_manager.player_lock.release()
	except RuntimeError as e:
		if str(e) == "release unlocked lock":
			logging.error("RuntimeError: Attempted to release already unlocked player_lock")  # noqa: TRY400
		else:
			logging.exception("Unknown RuntimeError trying to release player_lock")
	except Exception:
		logging.exception("Unknown error trying to release player_lock")

	if tauon.radio_server is not None:
		try:
			tauon.radio_server.server_close()
		except Exception:
			logging.exception("Failed to close radio server")

	if sys.platform == "win32":
		if pctl.smtc:
			pctl.sm.unload()
	elif sys.platform == "darwin":
		if getattr(bag, "nowplaying_helper", None) is not None:
			try:
				bag.nowplaying_helper.stop()
			except Exception:
				logging.exception("Failed to stop macOS Now Playing helper")
	elif tauon.de_notify_support:
		try:
			tauon.song_notification.close()
			tauon.g_tc_notify.close()
			Notify.uninit()
		except Exception:
			logging.exception("uninit notification error")

	try:
		tauon.instance_lock.close()
	except Exception:
		logging.exception("No lock object to close")

	# sdl3.IMG_Quit()
	# sdl3.SDL_QuitSubSystem(sdl3.SDL_INIT_EVERYTHING)
	sdl3.SDL_Quit()
	# logging.info("SDL unloaded")

	exit_timer = Timer()
	exit_timer.set()

	if not tauon.quick_close:
		while tauon.thread_manager.check_playback_running():
			time.sleep(0.2)
			if exit_timer.get() > 2:
				logging.warning("Phazor unload timeout")
				break

		while tauon.lfm_scrobbler.running:
			time.sleep(0.2)
			tauon.lfm_scrobbler.running = False
			if exit_timer.get() > 15:
				logging.warning("Scrobble wait timeout")
				break

	if tauon.sleep_lock is not None:
		del tauon.sleep_lock
	if tauon.shutdown_lock is not None:
		del tauon.shutdown_lock
	if tauon.play_lock is not None:
		del tauon.play_lock

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
