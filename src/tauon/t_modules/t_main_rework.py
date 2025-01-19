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

if TYPE_CHECKING:
	from tauon.t_modules.t_bootstrap import Holder

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

from tauon.t_modules import t_bootstrap
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
#from tauon.t_modules.guitar_chords import GuitarChords

class LoadImageAsset:
	assets: list[LoadImageAsset] = []

	def __init__(self, *, scaled_asset_directory: Path, path: str, is_full_path: bool = False, reload: bool = False, scale_name: str = "") -> None:
		if not reload:
			self.assets.append(self)

		self.path = path
		self.scale_name = scale_name
		self.scaled_asset_directory: Path = scaled_asset_directory

		raw_image = IMG_Load(self.path.encode())
		self.sdl_texture = SDL_CreateTextureFromSurface(renderer, raw_image)

		p_w = pointer(c_int(0))
		p_h = pointer(c_int(0))
		SDL_QueryTexture(self.sdl_texture, None, None, p_w, p_h)

		if is_full_path:
			SDL_SetTextureAlphaMod(self.sdl_texture, prefs.custom_bg_opacity)

		self.rect = SDL_Rect(0, 0, p_w.contents.value, p_h.contents.value)
		SDL_FreeSurface(raw_image)
		self.w = p_w.contents.value
		self.h = p_h.contents.value

	def reload(self) -> None:
		SDL_DestroyTexture(self.sdl_texture)
		if self.scale_name:
			self.path = str(self.scaled_asset_directory / self.scale_name)
		self.__init__(scaled_asset_directory=scaled_asset_directory, path=self.path, reload=True, scale_name=self.scale_name)

	def render(self, x: int, y: int, colour=None) -> None:
		self.rect.x = round(x)
		self.rect.y = round(y)
		SDL_RenderCopy(renderer, self.sdl_texture, None, self.rect)

class WhiteModImageAsset:
	assets: list[WhiteModImageAsset] = []

	def __init__(self, *, scaled_asset_directory: Path, path: str, reload: bool = False, scale_name: str = ""):
		if not reload:
			self.assets.append(self)
		self.path = path
		self.scale_name = scale_name
		self.scaled_asset_directory: Path = scaled_asset_directory

		raw_image = IMG_Load(path.encode())
		self.sdl_texture = SDL_CreateTextureFromSurface(renderer, raw_image)
		self.colour = [255, 255, 255, 255]
		p_w = pointer(c_int(0))
		p_h = pointer(c_int(0))
		SDL_QueryTexture(self.sdl_texture, None, None, p_w, p_h)
		self.rect = SDL_Rect(0, 0, p_w.contents.value, p_h.contents.value)
		SDL_FreeSurface(raw_image)
		self.w = p_w.contents.value
		self.h = p_h.contents.value

	def reload(self) -> None:
		SDL_DestroyTexture(self.sdl_texture)
		if self.scale_name:
			self.path = str(self.scaled_asset_directory / self.scale_name)
		self.__init__(scaled_asset_directory=scaled_asset_directory, path=self.path, reload=True, scale_name=self.scale_name)

	def render(self, x: int, y: int, colour) -> None:
		if colour != self.colour:
			SDL_SetTextureColorMod(self.sdl_texture, colour[0], colour[1], colour[2])
			SDL_SetTextureAlphaMod(self.sdl_texture, colour[3])
			self.colour = colour
		self.rect.x = round(x)
		self.rect.y = round(y)
		SDL_RenderCopy(renderer, self.sdl_texture, None, self.rect)

class DConsole:
	"""GUI console with logs"""

	def __init__(self) -> None:
		self.show:     bool      = False

	def toggle(self) -> None:
		"""Toggle the GUI console with logs on and off"""
		self.show ^= True

class GuiVar:
	"""Use to hold any variables for use in relation to UI"""

	def update_layout(self) -> None:
		global update_layout
		update_layout = True

	def show_message(self, line1: str, line2: str = "", line3: str = "", mode: str = "info") -> None:
		show_message(line1, line2, line3, mode=mode)

	def delay_frame(self, t):
		self.frame_callback_list.append(TestTimer(t))

	def destroy_textures(self):
		SDL_DestroyTexture(self.spec4_tex)
		SDL_DestroyTexture(self.spec1_tex)
		SDL_DestroyTexture(self.spec2_tex)
		SDL_DestroyTexture(self.spec_level_tex)

	# def test_text_input(self):
	#	 if self.text_input_request and not self.text_input_active:
	#		 SDL_StartTextInput()
	#		 self.update += 1
	#	 if not self.text_input_request and self.text_input_active:
	#		 SDL_StopTextInput()
	#	 self.text_input_request = False

	def rescale(self):
		self.spec_y = int(round(5 * self.scale))
		self.spec_w = int(round(80 * self.scale))
		self.spec_h = int(round(20 * self.scale))
		self.spec1_rec = SDL_Rect(0, self.spec_y, self.spec_w, self.spec_h)

		self.spec4_y = int(round(200 * self.scale))
		self.spec4_w = int(round(322 * self.scale))
		self.spec4_h = int(round(100 * self.scale))
		self.spec4_rec = SDL_Rect(0, self.spec4_y, self.spec4_w, self.spec4_h)

		self.bar = SDL_Rect(10, 10, round(3 * self.scale), 10)  # spec bar bin
		self.bar4 = SDL_Rect(10, 10, round(3 * self.scale), 10)  # spec bar bin
		self.set_height = round(25 * self.scale)
		self.panelBY = round(51 * self.scale)
		self.panelY = round(30 * self.scale)
		self.panelY2 = round(30 * self.scale)
		self.playlist_top = self.panelY + (8 * self.scale)
		self.playlist_top_bk = self.playlist_top
		self.scroll_hide_box = (0, self.panelY, 28, window_size[1] - self.panelBY - self.panelY)

		self.spec2_y = int(round(22 * self.scale))
		self.spec2_w = int(round(140 * self.scale))
		self.spec2 = [0] * self.spec2_y
		self.spec2_phase = 0
		self.spec2_buffers = []
		self.spec2_rec = SDL_Rect(1230, round(4 * self.scale), self.spec2_w, self.spec2_y)
		self.spec2_source = SDL_Rect(900, round(4 * self.scale), self.spec2_w, self.spec2_y)
		self.spec2_dest = SDL_Rect(900, round(4 * self.scale), self.spec2_w, self.spec2_y)
		self.spec2_position = 0
		self.spec2_timer = Timer()
		self.spec2_timer.set()

		self.level_w = 5 * self.scale
		self.level_y = 16 * self.scale
		self.level_s = 1 * self.scale
		self.level_ww = round(79 * self.scale)
		self.level_hh = round(18 * self.scale)
		self.spec_level_rec = SDL_Rect(
			0, round(self.level_y - 10 * self.scale), round(self.level_ww),round(self.level_hh))

		self.spec2_tex = SDL_CreateTexture(
					renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, self.spec2_w, self.spec2_y)
		self.spec4_tex = SDL_CreateTexture(
					renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, self.spec4_w, self.spec4_y)
		self.spec1_tex = SDL_CreateTexture(
					renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, self.spec_w, self.spec_h)
		self.spec_level_tex = SDL_CreateTexture(
					renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, self.level_ww, self.level_hh)
		SDL_SetTextureBlendMode(self.spec4_tex, SDL_BLENDMODE_BLEND)
		self.artist_panel_height = 320 * self.scale
		self.last_artist_panel_height = self.artist_panel_height

		self.window_control_hit_area_w = 100 * self.scale
		self.window_control_hit_area_h = 30 * self.scale

	def __init__(self, prefs: Prefs):

		self.scale = prefs.ui_scale

		self.window_id = 0
		self.update = 2  # UPDATE
		self.turbo = True
		self.turbo_next = 0
		self.pl_update = 1
		self.lowered = False
		self.request_raise = False
		self.maximized = False

		self.message_box = False
		self.message_text = ""
		self.message_mode = "info"
		self.message_subtext = ""
		self.message_subtext2 = ""
		self.message_box_confirm_reference = None
		self.message_box_use_reference = True
		self.message_box_confirm_callback = None

		self.save_size = [450, 310]
		self.show_playlist = True
		self.show_bottom_title = False
		# self.show_top_title = True
		self.search_error = False

		self.level_update = False
		self.level_time = Timer()
		self.level_peak: list[float] = [0, 0]
		self.level = 0
		self.time_passed = 0
		self.level_meter_colour_mode = 3

		self.vis = 0  # visualiser mode actual
		self.vis_want = 2  # visualiser mode setting
		self.spec = None
		self.s_spec = [0] * 24
		self.s4_spec = [0] * 45
		self.update_spec = 0

		# self.spec_rect = [0, 5, 80, 20]  # x = 72 + 24 - 6 - 10

		self.spec4_array = []

		self.draw_spec4 = False

		self.combo_mode = False
		self.showcase_mode = False
		self.display_time_mode = 0

		self.pl_text_real_height = 12
		self.pl_title_real_height = 11

		self.row_extra = 0
		self.test = False
		self.light_mode = False

		self.level_2_click = False
		self.universal_y_text_offset = 0

		self.star_text_y_offset = 0
		if system == "Windows":
			self.star_text_y_offset = -2

		self.set_bar = True
		self.set_mode = False
		self.set_hold = -1
		self.set_label_hold = -1
		self.set_label_point = (0, 0)
		self.set_point = 0
		self.set_old = 0
		self.pl_st = [
			["Artist", 156, False], ["Title", 188, False], ["T", 40, True], ["Album", 153, False],
			["P", 28, True], ["Starline", 86, True], ["Date", 48, True], ["Codec", 55, True],
			["Time", 53, True]]

		for item in self.pl_st:
			item[1] = item[1] * self.scale

		self.offset_extra: int = 0

		self.playlist_row_height: int = 16
		self.playlist_text_offset: int = 0
		self.row_font_size: int = 13
		self.compact_bar = False
		self.tracklist_texture_rect = tracklist_texture_rect
		self.tracklist_texture = tracklist_texture

		self.trunk_end = "..."  # "…"
		self.temp_themes = {}
		self.theme_temp_current = -1

		self.pl_title_y_offset = 0
		self.pl_title_font_offset = -1

		self.playlist_box_d_click = -1

		self.gallery_show_text = True
		self.bb_show_art = False

		self.rename_folder_box = False

		self.present = False
		self.drag_source_position = (0, 0)
		self.drag_source_position_persist = (0, 0)
		self.album_tab_mode = False
		self.main_art_box = (0, 0, 10, 10)
		self.gall_tab_enter = False

		self.lightning_copy = False

		self.gallery_animate_highlight_on = 0

		self.seek_cur_show = False
		self.cur_time = "0"
		self.force_showcase_index = -1

		self.frame_callback_list = []

		self.playlist_left = None
		self.image_downloading = False
		self.tc_cancel = False
		self.im_cancel = False
		self.force_search = False

		self.pl_pulse = False

		self.view_name = "S"
		self.restart_album_mode = False

		self.dtm3_index = -1
		self.dtm3_cum = 0
		self.dtm3_total = 0
		self.previous_playlist_id = ""

		self.star_mode = "line"
		self.heart_fields = []
		self.show_ratings = False

		self.web_running = False

		self.rsp = True
		if phone:
			self.rsp = False
		self.rspw = round(300 * self.scale)
		self.lsp = False
		self.lspw = round(220 * self.scale)
		self.plw = None

		self.pref_rspw = 300

		self.pref_gallery_w = 600

		self.artist_info_panel = False

		self.show_hearts = True

		self.cursor_is = 0
		self.cursor_want = 0
		# 0 standard
		# 1 drag horizontal
		# 2 text
		# 3 hand

		self.power_bar = None
		self.gallery_scroll_field_left = 1
		self.combo_was_album = False

		self.gallery_positions = {}

		self.remember_library_mode = False

		self.first_in_grid = None

		self.art_aspect_ratio = 1
		self.art_drawn_rect = None
		self.art_unlock_ratio = False
		self.art_max_ratio_lock = 1
		self.side_bar_drag_source = 0
		self.side_bar_drag_original = 0

		self.scroll_direction = 0
		self.add_music_folder_ready = False

		self.playlist_current_visible_tracks = 0
		self.playlist_current_visible_tracks_id = 0

		self.theme_name = ""
		self.rename_playlist_box = False
		self.queue_frame_draw = None  # Set when need draw frame later

		self.mode = 1

		self.save_position = [0, 0]

		self.draw_vis4_top = False
		# self.vis_4_colour = [0,0,0,255]
		self.vis_4_colour = None

		self.layer_focus = 0
		self.tab_menu_pl = 0

		self.tool_tip_lock_off_f = False
		self.tool_tip_lock_off_b = False

		self.auto_play_import = False

		self.transcoding_batch_total = 0
		self.transcoding_bach_done = 0

		self.seek_bar_rect = (0, 0, 0, 0)
		self.volume_bar_rect = (0, 0, 0, 0)

		self.mini_mode_return_maximized = False

		self.opened_config_file = False

		self.notify_main_id = None

		self.halt_image_rendering = False
		self.generating_chart = False

		self.top_bar_mode2 = False
		self.mode_toast_text = ""

		self.rescale()
		# self.smooth_scrolling = False

		self.compact_artist_list = False

		self.rsp_full_lock = False

		self.album_scroll_px = album_v_slide_value
		self.queue_toast_plural = False
		self.reload_theme = False
		self.theme_number = 0
		self.toast_queue_object: TauonQueueItem | None = None
		self.toast_love_object = None
		self.toast_love_added = True

		self.force_side_on_drag = False
		self.last_left_panel_mode = "playlist"
		self.showing_l_panel = False

		self.downloading_bass = False
		self.d_click_ref = -1

		self.max_window_tex = max_window_tex
		self.main_texture = main_texture
		self.main_texture_overlay_temp = main_texture_overlay_temp

		self.preview_artist = ""
		self.preview_artist_location = (0, 0)
		self.preview_artist_loading = ""
		self.mouse_left_window = False

		self.rendered_playlist_position = 0

		self.console = console
		self.show_album_ratings = False
		self.gen_code_errors = False

		self.regen_single = -1
		self.regen_single_id = None

		self.tracklist_bg_is_light = False
		self.clear_image_cache_next = 0

		self.column_d_click_timer = Timer(10)
		self.column_d_click_on = -1
		self.column_sort_ani_timer = Timer(10)
		self.column_sort_down_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "sort-down.png", True)
		self.column_sort_up_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "sort-up.png", True)
		self.column_sort_ani_direction = 1
		self.column_sort_ani_x = 0

		self.restore_showcase_view = False
		self.restore_radio_view = False

		self.tracklist_center_mode = False
		self.tracklist_inset_left = 0
		self.tracklist_inset_width = 0
		self.tracklist_highlight_width = 0
		self.tracklist_highlight_left = 0

		self.hide_tracklist_in_gallery = False

		self.saved_prime_tab = 0
		self.saved_prime_direction = 0

		self.stop_sync = False
		self.sync_progress = ""
		self.sync_speed = ""

		self.bar_hover_timer = Timer()

		self.level_decay_timer = Timer()

		self.showed_title = False

		self.to_get = 0
		self.to_got = 0
		self.switch_showcase_off = False

		self.backend_reloading = False

		self.spot_info_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "spot-info.png", True)
		self.tray_active = False
		self.buffering = False
		self.buffering_text = ""

		self.update_on_drag = False
		self.pl_update_on_drag = False
		self.drop_playlist_target = 0
		self.discord_status = "Standby"
		self.mouse_unknown = False
		self.macstyle = prefs.macstyle
		if macos or detect_macstyle:
			self.macstyle = True
		self.radio_view = False
		self.window_size = window_size
		self.box_over = False
		self.suggest_clean_db = False
		self.style_worker_timer = Timer()

		self.shuffle_was_showcase = False
		self.shuffle_was_random = True
		self.shuffle_was_repeat = False

		self.was_radio = False
		self.fullscreen = False
		self.mouse_in_window = True

		self.write_tag_in_progress = False
		self.tag_write_count = 0
		# self.text_input_request = False
		# self.text_input_active = False
		self.center_blur_pixel = (0, 0, 0)

class StarStore:
	def __init__(self) -> None:
		self.db = {}

	def key(self, track_id: int) -> tuple[str, str, str]:
		track_object = pctl.master_library[track_id]
		return track_object.artist, track_object.title, track_object.filename

	def object_key(self, track: TrackClass) -> tuple[str, str, str]:
		return track.artist, track.title, track.filename

	def add(self, index: int, value):
		"""Increments the play time"""
		track_object = pctl.master_library[index]

		if after_scan:
			if track_object in after_scan:
				return

		key = track_object.artist, track_object.title, track_object.filename

		if key in self.db:
			self.db[key][0] += value
			if value < 0 and self.db[key][0] < 0:
				self.db[key][0] = 0
		else:
			self.db[key] = [value, "", 0, 0]  # Playtime in s, flags, rating, love timestamp

	def get(self, index: int):
		"""Returns the track play time"""
		if index < 0:
			return 0
		return self.db.get(self.key(index), (0,))[0]

	def get_rating(self, index: int):
		"""Returns the track user rating"""
		key = self.key(index)
		if key in self.db:
			# self.db[key]
			return self.db[key][2]
		return 0

	def set_rating(self, index: int, value: int, write: bool = False) -> None:
		"""Sets the track user rating"""
		key = self.key(index)
		if key not in self.db:
			self.db[key] = self.new_object()
		self.db[key][2] = value

		tr = pctl.get_track(index)
		if tr.file_ext == "SUB":
			self.db[key][2] = math.ceil(value / 2) * 2
			shooter(subsonic.set_rating, (tr, value))

		if prefs.write_ratings and write:
			logging.info("Writing rating..")
			assert value <= 10
			assert value >= 0

			if tr.file_ext == "OGG" or tr.file_ext == "OPUS":
				tag = mutagen.oggvorbis.OggVorbis(tr.fullpath)
				if value == 0:
					if "FMPS_RATING" in tag:
						del tag["FMPS_RATING"]
						tag.save()
				else:
					tag["FMPS_RATING"] = [f"{value / 10:.2f}"]
					tag.save()

			elif tr.file_ext == "MP3":
				tag = mutagen.id3.ID3(tr.fullpath)

				# if True:
				#	 if value == 0:
				#		 tag.delall("POPM")
				#	 else:
				#		 p_rating = 0
				#
				#	 tag.add(mutagen.id3.POPM(email="Windows Media Player 9 Series", rating=int))

				if value == 0:
					changed = False
					frames = tag.getall("TXXX")
					for i in reversed(range(len(frames))):
						if frames[i].desc.lower() == "fmps_rating":
							changed = True
					if changed:
						tag.delall("TXXX:FMPS_RATING")
						tag.save()
				else:
					changed = False
					frames = tag.getall("TXXX")
					for i in reversed(range(len(frames))):
						if frames[i].desc.lower() == "fmps_rating":
							frames[i].text = f"{value / 10:.2f}"
							changed = True
					if not changed:
						tag.add(
							mutagen.id3.TXXX(
								encoding=mutagen.id3.Encoding.UTF8, text=f"{value / 10:.2f}",
								desc="FMPS_RATING"))
					tag.save()

			elif tr.file_ext == "FLAC":
				audio = mutagen.flac.FLAC(tr.fullpath)
				tags = audio.tags
				if value == 0:
					if "FMPS_Rating" in tags:
						del tags["FMPS_Rating"]
						audio.save()
				else:
					tags["FMPS_Rating"] = f"{value / 10:.2f}"
					audio.save()

			tr.misc["FMPS_Rating"] = float(value / 10)
			if value == 0:
				del tr.misc["FMPS_Rating"]

	def new_object(self):
		return [0, "", 0, 0]

	def get_by_object(self, track: TrackClass):

		return self.db.get(self.object_key(track), (0,))[0]

	def get_total(self):

		return sum(item[0] for item in self.db.values())

	def full_get(self, index: int):
		return self.db.get(self.key(index))

	def remove(self, index: int):
		key = self.key(index)
		if key in self.db:
			del self.db[key]

	def insert(self, index: int, object):
		key = self.key(index)
		self.db[key] = object

	def merge(self, index: int, object):
		if object is None or object == self.new_object():
			return
		key = self.key(index)
		if key not in self.db:
			self.db[key] = object
		else:
			self.db[key][0] += object[0]
			self.db[key][2] = object[2]
			for cha in object[1]:
				if cha not in self.db[key][1]:
					self.db[key][1] += cha

class AlbumStarStore:

	def __init__(self) -> None:
		self.db = {}

	def get_key(self, track_object: TrackClass) -> str:
		artist = track_object.album_artist
		if not artist:
			artist = track_object.artist
		return artist + ":" + track_object.album

	def get_rating(self, track_object: TrackClass):
		return self.db.get(self.get_key(track_object), 0)

	def set_rating(self, track_object: TrackClass, rating):
		self.db[self.get_key(track_object)] = rating
		if track_object.file_ext == "SUB":
			self.db[self.get_key(track_object)] = math.ceil(rating / 2) * 2
			subsonic.set_album_rating(track_object, rating)

	def set_rating_artist_title(self, artist: str, album: str, rating):
		self.db[artist + ":" + album] = rating

	def get_rating_artist_title(self, artist: str, album: str):
		return self.db.get(artist + ":" + album, 0)

class Fonts:
	"""Used to hold font sizes (I forget to use this)"""

	def __init__(self):
		self.tabs = 211
		self.panel_title = 213

		self.side_panel_line1 = 214
		self.side_panel_line2 = 13

		self.bottom_panel_time = 212

		# if system == 'Windows':
		#	 self.bottom_panel_time = 12  # The Arial bold font is too big so just leaving this as normal. (lazy)

class Input:
	"""Used to keep track of button states (or should be)"""

	def __init__(self) -> None:
		self.mouse_click = False
		# self.right_click = False
		self.level_2_enter = False
		self.key_return_press = False
		self.key_tab_press = False
		self.backspace_press = 0

		self.media_key = ""

	def m_key_play(self) -> None:
		self.media_key = "Play"
		gui.update += 1

	def m_key_pause(self) -> None:
		self.media_key = "Pause"
		gui.update += 1

	def m_key_stop(self) -> None:
		self.media_key = "Stop"
		gui.update += 1

	def m_key_next(self) -> None:
		self.media_key = "Next"
		gui.update += 1

	def m_key_previous(self) -> None:
		self.media_key = "Previous"
		gui.update += 1

class KeyMap:

	def __init__(self):

		self.hits = []  # The keys hit this frame
		self.maps = {}  # Loaded from input.txt

	def load(self):

		path = config_directory / "input.txt"
		with path.open(encoding="utf_8") as f:
			content = f.read().splitlines()
			for p in content:
				if len(p) == 0 or len(p) > 100:
					continue
				if p[0] == " " or p[0] == "#":
					continue

				items = p.split()
				if 1 < len(items) < 5:
					function = items[0]

					if items[1] in ("MB4", "MB5"):
						key = items[1]
					else:
						if prefs.use_scancodes:
							key = SDL_GetScancodeFromName(items[1].encode())
						else:
							key = SDL_GetKeyFromName(items[1].encode())
						if key == 0:
							continue

					mod = []

					if len(items) > 2:
						mod.append(items[2].lower())
					if len(items) > 3:
						mod.append(items[3].lower())

					if function in self.maps:
						self.maps[function].append((key, mod))
					else:
						self.maps[function] = [(key, mod)]

	def test(self, function):

		if not self.hits:
			return False
		if function not in self.maps:
			return False

		for code, mod in self.maps[function]:

			if code in self.hits:

				ctrl = (key_ctrl_down or key_rctrl_down) * 1
				shift = (key_shift_down or key_shiftr_down) * 10
				alt = (key_lalt or key_ralt) * 100

				if ctrl + shift + alt == ("ctrl" in mod) * 1 + ("shift" in mod) * 10 + ("alt" in mod) * 100:
					return True

		return False

class ColoursClass:
	"""Used to store colour values for UI elements

	These are changed for themes
	"""

	def grey(self, value: int) -> list[int]:
		return [value, value, value, 255]

	def alpha_grey(self, value: int) -> list[int]:
		return [255, 255, 255, value]

	def grey_blend_bg(self, value: int) -> list[int]:
		return alpha_blend((255, 255, 255, value), self.box_background)

	def __init__(self) -> None:

		self.deco = None
		self.column_colours = {}
		self.column_colours_playing = {}

		self.last_album = ""
		self.link_text = [100, 200, 252, 255]

		self.tb_line = self.grey(21)  # not currently used
		self.art_box = self.grey(24)

		self.volume_bar_background = self.grey(30)
		self.volume_bar_fill = self.grey(125)
		self.seek_bar_background = self.grey(30)
		self.seek_bar_fill = self.grey(80)

		self.tab_text_active = self.grey(230)
		self.tab_text = self.grey(215)
		self.tab_background = self.grey(25)
		self.tab_highlight = self.grey(40)
		self.tab_background_active = self.grey(45)

		self.title_text = [190, 190, 190, 255]
		self.index_text = self.grey(70)
		self.time_text = self.grey(180)
		self.artist_text = [195, 255, 104, 255]
		self.album_text = [245, 240, 90, 255]

		self.index_playing = self.grey(190)
		self.artist_playing = [195, 255, 104, 255]
		self.album_playing = [245, 240, 90, 255]
		self.title_playing = self.grey(230)

		self.time_playing = [180, 194, 107, 255]

		self.playlist_text_missing = self.grey(85)
		self.bar_time = self.grey(70)

		self.top_panel_background = self.grey(15)
		self.status_text_over = rgb_add_hls(self.top_panel_background, 0, 0.83, 0)
		self.status_text_normal = rgb_add_hls(self.top_panel_background, 0, 0.30, -0.15)

		self.side_panel_background = self.grey(18)
		self.gallery_background = self.side_panel_background
		self.playlist_panel_background = self.grey(21)
		self.bottom_panel_colour = self.grey(15)

		self.row_playing_highlight = [255, 255, 255, 4]
		self.row_select_highlight = [255, 255, 255, 5]

		self.side_bar_line1 = self.grey(230)
		self.side_bar_line2 = self.grey(210)

		self.mode_button_off = self.grey(50)
		self.mode_button_over = self.grey(200)
		self.mode_button_active = self.grey(190)

		self.media_buttons_over = self.grey(220)
		self.media_buttons_active = self.grey(220)
		self.media_buttons_off = self.grey(55)

		self.star_line = [100, 100, 100, 255]
		self.star_line_playing = None
		self.folder_title = [130, 130, 130, 255]
		self.folder_line = [40, 40, 40, 255]

		self.scroll_colour = [45, 45, 45, 255]

		self.level_1_bg = [0, 30, 0, 255]
		self.level_2_bg = [30, 30, 0, 255]
		self.level_3_bg = [30, 0, 0, 255]
		self.level_green = [20, 120, 20, 255]
		self.level_red = [190, 30, 30, 255]
		self.level_yellow = [135, 135, 30, 255]

		self.vis_colour = self.grey(200)
		self.vis_bg = [0, 0, 0, 255]

		self.menu_background = None  # self.grey(12)
		self.menu_highlight_background = None
		self.menu_text = [230, 230, 230, 255]
		self.menu_text_disabled = self.grey(50)
		self.menu_icons = [255, 255, 255, 25]
		self.menu_tab = self.grey(30)

		self.gallery_highlight = self.artist_playing

		self.status_info_text = [245, 205, 0, 255]
		self.streaming_text = [220, 75, 60, 255]
		self.lyrics = self.grey(245)

		self.corner_button = [255, 255, 255, 50]  # [60, 60, 60, 255]
		self.corner_button_active = [255, 255, 255, 230]  # [230, 230, 230, 255]

		self.window_buttons_bg = [0, 0, 0, 50]
		self.window_buttons_bg_over = [255, 255, 255, 10]  # [80, 80, 80, 120]
		self.window_buttons_icon_over = (255, 255, 255, 60)
		self.window_button_icon_off = (255, 255, 255, 40)
		self.window_button_x_on = None
		self.window_button_x_off = self.window_button_icon_off

		self.message_box_bg = self.grey(0)
		self.message_box_text = self.grey(230)

		self.sys_title = self.grey(220)
		self.sys_title_strong = self.grey(230)
		self.lm = False

		self.pluse_colour = [244, 212, 66, 255]

		self.mini_mode_background = [19, 19, 19, 255]
		self.mini_mode_border = [45, 45, 45, 255]
		self.mini_mode_text_1 = [255, 255, 255, 240]
		self.mini_mode_text_2 = [255, 255, 255, 77]

		self.queue_drag_indicator_colour = [200, 50, 240, 255]

		self.playlist_box_background: list[int] = self.side_panel_background

		self.bar_title_text = None

		self.corner_icon = [40, 40, 40, 255]
		self.queue_background = None  # self.side_panel_background #self.grey(18) # 18
		self.queue_card_background = self.grey(23)

		self.column_bar_background = [30, 30, 30, 255]
		self.column_grip = [255, 255, 255, 14]
		self.column_bar_text = [240, 240, 240, 255]

		self.window_frame = [30, 30, 30, 255]

		self.box_background: list[int] = [16, 16, 16, 255]
		self.box_border = rgb_add_hls(self.box_background, 0, 0.17, 0)
		self.box_text_border = rgb_add_hls(self.box_background, 0, 0.1, 0)
		self.box_text_label = rgb_add_hls(self.box_background, 0, 0.32, -0.1)
		self.box_sub_highlight = rgb_add_hls(self.box_background, 0, 0.07, -0.05)  # 58, 47, 85
		self.box_check_border = [255, 255, 255, 18]

		self.box_title_text = self.grey(245)
		self.box_text = self.grey(240)
		self.box_sub_text = self.grey_blend_bg(225)
		self.box_input_text = self.grey(225)
		self.box_button_text_highlight = self.grey(250)
		self.box_button_text = self.grey(225)
		self.box_button_background = alpha_blend([255, 255, 255, 11], self.box_background)
		self.box_thumb_background = None
		self.box_button_background_highlight = alpha_blend([255, 255, 255, 20], self.box_background)

		self.artist_bio_background = [27, 27, 27, 255]
		self.artist_bio_text = [230, 230, 230, 255]

	def post_config(self):

		if self.box_thumb_background is None:
			self.box_thumb_background = alpha_mod(self.box_button_background, 175)

		# Pre calculate alpha blend for spec background
		self.vis_bg[0] = int(0.05 * 255 + (1 - 0.05) * self.top_panel_background[0])
		self.vis_bg[1] = int(0.05 * 255 + (1 - 0.05) * self.top_panel_background[1])
		self.vis_bg[2] = int(0.05 * 255 + (1 - 0.05) * self.top_panel_background[2])

		self.message_box_bg = self.box_background
		self.sys_tab_bg = self.tab_background
		self.sys_tab_hl = self.tab_background_active
		self.toggle_box_on = self.folder_title
		self.toggle_box_on = [255, 150, 100, 255]
		self.toggle_box_on = self.artist_playing
		if colour_value(self.toggle_box_on) < 150:
			self.toggle_box_on = [160, 160, 160, 255]
		# self.time_sub = [255, 255, 255, 80]#alpha_blend([255, 255, 255, 80], self.bottom_panel_colour)

		self.time_sub = rgb_add_hls(self.bottom_panel_colour, 0, 0.29, 0)

		if test_lumi(self.bottom_panel_colour) < 0.2:
			# self.time_sub = [0, 0, 0, 80]
			self.time_sub = rgb_add_hls(self.bottom_panel_colour, 0, -0.15, -0.3)
		elif test_lumi(self.bottom_panel_colour) < 0.8:
			self.time_sub = [255, 255, 255, 135]
		# self.time_sub = self.mode_button_off

		if self.bar_title_text is None:
			self.bar_title_text = self.side_bar_line1

		self.gallery_artist_line = alpha_mod(self.side_bar_line2, 120)

		if self.menu_highlight_background is None:
			self.menu_highlight_background = [40, 40, 40, 255]

		if not self.queue_background:
			self.queue_background = self.side_panel_background

		if test_lumi(self.queue_background) > 0.8:
			self.queue_card_background = alpha_blend([255, 255, 255, 10], self.queue_background)

		if self.menu_background is None and not self.lm:
			self.menu_background = self.bottom_panel_colour

		self.message_box_text = self.box_text
		self.message_box_border = self.box_border

		if self.window_button_x_on is None:
			self.window_button_x_on = self.artist_playing

		if test_lumi(self.column_bar_background) < 0.4:
			self.column_bar_text = [40, 40, 40, 200]
			self.column_grip = [255, 255, 255, 20]

	def light_mode(self):

		self.lm = True
		self.star_line_playing = [255, 255, 255, 255]
		self.sys_tab_bg = self.grey(25)
		self.sys_tab_hl = self.grey(45)
		# self.box_background = self.grey(30)
		self.toggle_box_on = self.tab_background_active
		# if colour_value(self.tab_background_active) < 250:
		#	self.toggle_box_on = [255, 255, 255, 200]

		# self.time_sub = [0, 0, 0, 200]
		self.gallery_artist_line = self.grey(40)
		# self.bar_title_text = self.grey(30)
		self.status_text_normal = self.grey(70)
		self.status_text_over = self.grey(40)
		self.status_info_text = [40, 40, 40, 255]

		# self.bar_title_text = self.grey(255)
		self.vis_bg = [235, 235, 235, 255]
		# self.menu_background = [240, 240, 240, 250]
		# self.menu_text = self.grey(40)
		# self.menu_text_disabled = self.grey(180)
		# self.menu_highlight_background = [200, 200, 200, 250]
		if self.menu_background is None:
			self.menu_background = [15, 15, 15, 250]
		if not self.menu_icons:
			self.menu_icons = [0, 0, 0, 40]

		# self.menu_background = [40, 40, 40, 250]
		# self.menu_text = self.grey(220)
		# self.menu_text_disabled = self.grey(120)
		# self.menu_highlight_background = [120, 80, 220, 250]

		self.corner_button = self.grey(160)
		self.corner_button_active = self.grey(35)
		# self.window_buttons_bg = [0, 0, 0, 5]
		self.message_box_bg = [245, 245, 245, 255]
		self.message_box_text = self.grey(20)
		self.message_box_border = self.grey(40)
		self.gallery_background = self.grey(230)
		self.gallery_artist_line = self.grey(40)
		self.pluse_colour = [212, 66, 244, 255]

		# view_box.off_colour = self.grey(200)

class TrackClass:
	"""This is the fundamental object/data structure of a track"""

	def __init__(self) -> None:
		self.index:              int = 0
		self.subtrack:           int = 0
		self.fullpath:           str = ""
		self.filename:           str = ""
		self.parent_folder_path: str = ""
		self.parent_folder_name: str = ""
		self.file_ext:           str = ""
		self.size:               int = 0
		self.modified_time:      float = 0

		self.is_network:   bool = False
		self.url_key:      str = ""
		self.art_url_key:  str = ""

		self.artist:       str = ""
		self.album_artist: str = ""
		self.title:        str = ""
		self.composer:     str = ""
		self.length:     float = 0
		self.bitrate:      int = 0
		self.samplerate:   int = 0
		self.bit_depth:    int = 0
		self.album:        str = ""
		self.date:         str = ""
		self.track_number: str = ""
		self.track_total:  str = ""
		self.start_time:   int = 0
		self.is_cue:       bool = False
		self.is_embed_cue: bool = False
		self.cue_sheet:    str = ""
		self.genre:        str = ""
		self.found:        bool = True
		self.skips:        int = 0
		self.comment:      str = ""
		self.disc_number:  str = ""
		self.disc_total:   str = ""
		self.lyrics:       str = ""

		self.lfm_friend_likes = set()
		self.lfm_scrobbles: int = 0
		self.misc: list = {}

class LoadClass:
	"""Object for import track jobs (passed to worker thread)"""

	def __init__(self) -> None:
		self.target:            str = ""
		self.playlist:          int = 0  # Playlist UID
		self.tracks:            list[TrackClass] = []
		self.stage:             int = 0
		self.playlist_position: int | None = None
		self.replace_stem:      bool = False
		self.notify:            bool = False
		self.play:              bool = False
		self.force_scan:        bool = False

class GetSDLInput:

	def __init__(self):
		self.i_y = pointer(c_int(0))
		self.i_x = pointer(c_int(0))

		self.mouse_capture_want = False
		self.mouse_capture = False

	def mouse(self):
		SDL_PumpEvents()
		SDL_GetMouseState(self.i_x, self.i_y)
		return int(self.i_x.contents.value / logical_size[0] * window_size[0]), int(
			self.i_y.contents.value / logical_size[0] * window_size[0])

	def test_capture_mouse(self):
		if not self.mouse_capture and self.mouse_capture_want:
			SDL_CaptureMouse(SDL_TRUE)
			self.mouse_capture = True
		elif self.mouse_capture and not self.mouse_capture_want:
			SDL_CaptureMouse(SDL_FALSE)
			self.mouse_capture = False

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

class PlayerCtl:
	"""Main class that controls playback (play, pause, stepping, playlists, queue etc). Sends commands to backend."""

	# C-PC
	def __init__(self, prefs: Prefs):
		#self.tauon =
		self.running:           bool = True
		self.prefs:             Prefs = prefs
		self.install_directory: Path  = install_directory

		# Database

		self.master_count = master_count
		self.total_playtime: float = 0
		self.master_library = master_library
		# Lets clients know when to invalidate cache
		self.db_inc = random.randint(0, 10000)
		# self.star_library = star_library
		self.LoadClass = LoadClass

		self.gen_codes = gen_codes

		self.shuffle_pools = {}
		self.after_import_flag = False
		self.quick_add_target = None

		self.album_mbid_release_cache = {}
		self.album_mbid_release_group_cache = {}
		self.mbid_image_url_cache = {}

		# Misc player control

		self.url: str = ""
		# self.save_urls = url_saves
		self.tag_meta: str = ""
		self.found_tags = {}
		self.encoder_pause = 0

		# Playback

		self.track_queue = track_queue
		self.queue_step = playing_in_queue
		self.playing_time = 0
		self.playlist_playing_position = playlist_playing  # track in playlist that is playing
		if self.playlist_playing_position is None:
			self.playlist_playing_position = -1
		self.playlist_view_position = playlist_view_position
		self.selected_in_playlist = selected_in_playlist
		self.target_open = ""
		self.target_object = None
		self.start_time = 0
		self.b_start_time = 0
		self.playerCommand = ""
		self.playerSubCommand = ""
		self.playerCommandReady = False
		self.playing_state:    int = 0
		self.playing_length: float = 0
		self.jump_time = 0
		self.random_mode = prefs.random_mode
		self.repeat_mode = prefs.repeat_mode
		self.album_repeat_mode = prefs.album_repeat_mode
		self.album_shuffle_mode = prefs.album_shuffle_mode
		# self.album_shuffle_pool = []
		# self.album_shuffle_id = ""
		self.last_playing_time = 0
		self.multi_playlist = multi_playlist
		self.active_playlist_viewing: int = playlist_active  # the playlist index that is being viewed
		self.active_playlist_playing: int = playlist_active  # the playlist index that is playing from
		self.force_queue: list[TauonQueueItem] = p_force_queue
		self.pause_queue: bool = False
		self.left_time = 0
		self.left_index = 0
		self.player_volume: float = volume
		self.new_time = 0
		self.time_to_get = []
		self.a_time = 0
		self.b_time = 0
		# self.playlist_backup = []
		self.active_replaygain = 0
		self.auto_stop = False

		self.record_stream = False
		self.record_title = ""

		# Bass

		self.bass_devices = []
		self.set_device = 0

		self.gst_devices = []  # Display names
		self.gst_outputs = {}  # Display name : (sink, device)
		#TODO(Martin) : Fix this by moving the class to root of the module
		self.mpris: Gnome.main.MPRIS | None = None
		self.tray_update = None
		self.eq = [0] * 2  # not used
		self.enable_eq = True  # not used

		self.playing_time_int = 0  # playing time but with no decimel

		self.windows_progress = None

		self.finish_transition = False
		# self.queue_target = 0
		self.start_time_target = 0

		self.decode_time = 0
		self.download_time = 0

		self.radio_meta_on = ""

		self.radio_scrobble_trip = True
		self.radio_scrobble_timer = Timer()

		self.radio_image_bin = None
		self.radio_rate_timer = Timer(2)
		self.radio_poll_timer = Timer(2)

		self.volume_update_timer = Timer()
		self.wake_past_time = 0

		self.regen_in_progress = False
		self.notify_in_progress = False

		self.radio_playlists = radio_playlists
		self.radio_playlist_viewing = radio_playlist_viewing
		self.tag_history = {}

		self.commit: int | None = None
		self.spot_playing = False

		self.buffering_percent = 0



	def notify_change(self) -> None:
		self.db_inc += 1
		tauon.bg_save()

	def update_tag_history(self) -> None:
		if prefs.auto_rec:
			self.tag_history[radiobox.song_key] = {
				"title": radiobox.dummy_track.title,
				"artist": radiobox.dummy_track.artist,
				"album": radiobox.dummy_track.album,
				# "image": self.radio_image_bin
			}

	def radio_progress(self) -> None:
		if radiobox.loaded_url and "radio.plaza.one" in radiobox.loaded_url and self.radio_poll_timer.get() > 0:
			self.radio_poll_timer.force_set(-10)
			response = requests.get("https://api.plaza.one/status", timeout=10)

			if response.status_code == 200:
				d = json.loads(response.text)
				if "song" in d and "artist" in d["song"] and "title" in d["song"]:
					self.tag_meta = d["song"]["artist"] + " - " + d["song"]["title"]

		if self.tag_meta:
			if self.radio_rate_timer.get() > 7 and self.radio_meta_on != self.tag_meta:
				self.radio_rate_timer.set()
				self.radio_scrobble_trip = False
				self.radio_meta_on = self.tag_meta

				radiobox.dummy_track.art_url_key = ""
				radiobox.dummy_track.title = ""
				radiobox.dummy_track.date = ""
				radiobox.dummy_track.artist = ""
				radiobox.dummy_track.album = ""
				radiobox.dummy_track.lyrics = ""
				radiobox.dummy_track.date = ""

				tags = self.found_tags
				if "title" in tags:
					radiobox.dummy_track.title = tags["title"]
					if "artist" in tags:
						radiobox.dummy_track.artist = tags["artist"]
					if "year" in tags:
						radiobox.dummy_track.date = tags["year"]
					if "album" in tags:
						radiobox.dummy_track.album = tags["album"]

				elif self.tag_meta.count(
						"-") == 1 and ":" not in self.tag_meta and "advert" not in self.tag_meta.lower():
					artist, title = self.tag_meta.split("-")
					radiobox.dummy_track.title = title.strip()
					radiobox.dummy_track.artist = artist.strip()

				if self.tag_meta:
					radiobox.song_key = self.tag_meta
				else:
					radiobox.song_key = radiobox.dummy_track.artist + " - " + radiobox.dummy_track.title

				self.update_tag_history()
				if radiobox.loaded_url not in radiobox.websocket_source_urls:
					self.radio_image_bin = None
				logging.info("NEXT RADIO TRACK")

				try:
					get_radio_art()
				except Exception:
					logging.exception("Get art error")

				self.notify_update(mpris=False)
				if self.mpris:
					self.mpris.update(force=True)

				lfm_scrobbler.listen_track(radiobox.dummy_track)
				lfm_scrobbler.start_queue()

			if self.radio_scrobble_trip is False and self.radio_scrobble_timer.get() > 45:
				self.radio_scrobble_trip = True
				lfm_scrobbler.scrob_full_track(copy.deepcopy(radiobox.dummy_track))

	def update_shuffle_pool(self, pl_id: int) -> None:
		new_pool = copy.deepcopy(self.multi_playlist[id_to_pl(pl_id)].playlist_ids)
		random.shuffle(new_pool)
		self.shuffle_pools[pl_id] = new_pool
		logging.info("Refill shuffle pool")

	def notify_update_fire(self) -> None:
		if self.mpris is not None:
			self.mpris.update()
		if tauon.update_play_lock is not None:
			tauon.update_play_lock()
		# if self.tray_update is not None:
		#	 self.tray_update()
		self.notify_in_progress = False

	def notify_update(self, mpris: bool = True) -> None:
		tauon.tray_releases += 1
		if tauon.tray_lock.locked():
			try:
					tauon.tray_lock.release()
			except RuntimeError as e:
				if str(e) == "release unlocked lock":
					logging.error("RuntimeError: Attempted to release already unlocked tray_lock")
				else:
					logging.exception("Unknown RuntimeError trying to release tray_lock")
			except Exception:
				logging.exception("Failed to release tray_lock")

		if mpris and smtc:
			tr = self.playing_object()
			if tr:
				state = 0
				if self.playing_state == 1:
					state = 1
				if self.playing_state == 2:
					state = 2
				image_path = ""
				try:
					image_path = tauon.thumb_tracks.path(tr)
				except Exception:
					logging.exception("Failed to set image_path from thumb_tracks.path")

				if image_path is None:
					image_path = ""

				image_path = image_path.replace("/", "\\")
				#logging.info(image_path)

				sm.update(
					state, tr.title.encode("utf-16"), len(tr.title), tr.artist.encode("utf-16"), len(tr.artist),
					image_path.encode("utf-16"), len(image_path))


		if self.mpris is not None and mpris is True:
			while self.notify_in_progress:
				time.sleep(0.01)
			self.notify_in_progress = True
			shoot = threading.Thread(target=self.notify_update_fire)
			shoot.daemon = True
			shoot.start()
		if prefs.art_bg or (gui.mode == 3 and prefs.mini_mode_mode == 5):
			tauon.thread_manager.ready("style")

	def get_url(self, track_object: TrackClass) -> tuple[str | None, dict | None] | None:
		if track_object.file_ext == "TIDAL":
			return tauon.tidal.resolve_stream(track_object), None
		if track_object.file_ext == "PLEX":
			return plex.resolve_stream(track_object.url_key), None

		if track_object.file_ext == "JELY":
			return jellyfin.resolve_stream(track_object.url_key)

		if track_object.file_ext == "KOEL":
			return koel.resolve_stream(track_object.url_key)

		if track_object.file_ext == "SUB":
			return subsonic.resolve_stream(track_object.url_key)

		if track_object.file_ext == "TAU":
			return tau.resolve_stream(track_object.url_key), None

		return None, None

	def playing_playlist(self) -> list[int] | None:
		return self.multi_playlist[self.active_playlist_playing].playlist_ids

	def playing_ready(self) -> bool:
		return len(self.track_queue) > 0

	def selected_ready(self) -> bool:
		return default_playlist and self.selected_in_playlist < len(default_playlist)

	def render_playlist(self) -> None:
		if taskbar_progress and msys and self.windows_progress:
			self.windows_progress.update(True)
		gui.pl_update = 1

	def show_selected(self) -> int:
		if gui.playlist_view_length < 1:
			return 0

		global shift_selection

		for i in range(len(self.multi_playlist[self.active_playlist_viewing].playlist_ids)):

			if i == self.selected_in_playlist:

				if i < self.playlist_view_position:
					self.playlist_view_position = i - random.randint(2, int((gui.playlist_view_length / 3) * 2) + int(gui.playlist_view_length / 6))
					logging.debug("Position changed show selected (a)")
				elif abs(self.playlist_view_position - i) > gui.playlist_view_length:
					self.playlist_view_position = i
					logging.debug("Position changed show selected (b)")
					if i > 6:
						self.playlist_view_position -= 5
						logging.debug("Position changed show selected (c)")
					if i > gui.playlist_view_length * 1 and i + (gui.playlist_view_length * 2) < len(
							self.multi_playlist[self.active_playlist_viewing].playlist_ids) and i > 10:
						self.playlist_view_position = i - random.randint(2, int(gui.playlist_view_length / 3) * 2)
						logging.debug("Position changed show selected (d)")
					break

		self.render_playlist()

		return 0

	def get_track(self, track_index: int) -> TrackClass:
		"""Get track object by track_index"""
		return self.master_library[track_index]

	def get_track_in_playlist(self, track_index: int, playlist_index: int) -> TrackClass:
		"""Get track object by playlist_index and track_index"""
		if playlist_index == -1:
			playlist_index = self.active_playlist_viewing
		try:
			playlist = self.multi_playlist[playlist_index].playlist
			return self.get_track(playlist[track_index])
		except IndexError:
			logging.exception("Failed getting track object by playlist_index and track_index!")
		except Exception:
			logging.exception("Unknown error getting track object by playlist_index and track_index!")
		return None

	def show_object(self) -> None:
		"""The track to show in the metadata side panel"""
		target_track = None

		if self.playing_state == 3:
			return radiobox.dummy_track

		if 3 > self.playing_state > 0:
			target_track = self.playing_object()

		elif self.playing_state == 0 and prefs.meta_shows_selected:
			if -1 < self.selected_in_playlist < len(self.multi_playlist[self.active_playlist_viewing].playlist_ids):
				target_track = self.get_track(self.multi_playlist[self.active_playlist_viewing].playlist_ids[self.selected_in_playlist])

		elif self.playing_state == 0 and prefs.meta_persists_stop:
			target_track = self.master_library[self.track_queue[self.queue_step]]

		if prefs.meta_shows_selected_always:
			if -1 < self.selected_in_playlist < len(self.multi_playlist[self.active_playlist_viewing].playlist_ids):
				target_track = self.get_track(self.multi_playlist[self.active_playlist_viewing].playlist_ids[self.selected_in_playlist])

		return target_track

	def playing_object(self) -> TrackClass | None:

		if self.playing_state == 3:
			return radiobox.dummy_track

		if len(self.track_queue) > 0:
			return self.master_library[self.track_queue[self.queue_step]]
		return None

	def title_text(self) -> str:
		line = ""
		track = self.playing_object()
		if track:
			title = track.title
			artist = track.artist

			if not title:
				line = clean_string(track.filename)
			else:
				if artist != "":
					line += artist
				if title != "":
					if line != "":
						line += "  -  "
					line += title

			if self.playing_state == 3 and not title and not artist:
				return self.tag_meta

		return line

	def show(self) -> int | None:
		global shift_selection

		if not self.track_queue:
			return 0
		return None

	def show_current(
		self, select: bool = True, playing: bool = True, quiet: bool = False, this_only: bool = False, highlight: bool = False,
		index: int | None = None, no_switch: bool = False, folder_list: bool = True,
	) -> int | None:

		# logging.info("show------")
		# logging.info(select)
		# logging.info(playing)
		# logging.info(quiet)
		# logging.info(this_only)
		# logging.info(highlight)
		# logging.info("--------")
		logging.debug("Position set by show playing")

		global shift_selection

		if tauon.spot_ctl.coasting:
			sptr = tauon.dummy_track.misc.get("spotify-track-url")
			if sptr:

				for p in default_playlist:
					tr = self.get_track(p)
					if tr.misc.get("spotify-track-url") == sptr:
						index = tr.index
						break
				else:
					for i, pl in enumerate(self.multi_playlist):
						for p in pl.playlist_ids:
							tr = self.get_track(p)
							if tr.misc.get("spotify-track-url") == sptr:
								index = tr.index
								switch_playlist(i)
								break
						else:
							continue
						break
					else:
						return None

		if not self.track_queue:
			return 0

		track_index = self.track_queue[self.queue_step]
		if index is not None:
			track_index = index

		# Switch to source playlist
		if not no_switch:
			if self.active_playlist_viewing != self.active_playlist_playing and (
					track_index not in self.multi_playlist[self.active_playlist_viewing].playlist_ids):
				switch_playlist(self.active_playlist_playing)

		if gui.playlist_view_length < 1:
			return 0

		for i in range(len(self.multi_playlist[self.active_playlist_viewing].playlist_ids)):
			if self.multi_playlist[self.active_playlist_viewing].playlist_ids[i] == track_index:

				if self.playlist_playing_position < len(self.multi_playlist[self.active_playlist_viewing].playlist_ids) and \
						self.active_playlist_viewing == self.active_playlist_playing and track_index == \
						self.multi_playlist[self.active_playlist_viewing].playlist_ids[self.playlist_playing_position] and \
						i != self.playlist_playing_position:
					# continue
					i = self.playlist_playing_position

				if select:
					self.selected_in_playlist = i

				if playing:
					# Make the found track the playing track
					self.playlist_playing_position = i
					self.active_playlist_playing = self.active_playlist_viewing

				vl = gui.playlist_view_length
				if self.multi_playlist[self.active_playlist_viewing].uuid_int == gui.playlist_current_visible_tracks_id:
					vl = gui.playlist_current_visible_tracks

				if not (
						quiet and self.playing_object().length < 15):  # or (abs(self.playlist_view_position - i) < vl - 1)):

					# Align to album if in view range (and folder titles are active)
					ap = get_album_info(i)[1][0]

					if not (quiet and self.playlist_view_position <= i <= self.playlist_view_position + vl) and (
					not abs(i - ap) > vl - 2) and not self.multi_playlist[self.active_playlist_viewing].hide_title:
						self.playlist_view_position = ap

					# Move to a random offset ---

					elif i == self.playlist_view_position - 1 and self.playlist_view_position > 1:
						self.playlist_view_position -= 1

					# Move a bit if its just out of range
					elif self.playlist_view_position + vl - 2 == i and i < len(
							self.multi_playlist[self.active_playlist_viewing].playlist_ids) - 5:
						self.playlist_view_position += 3

					# We know its out of range if above view postion
					elif i < self.playlist_view_position:
						self.playlist_view_position = i - random.randint(2, int((
							gui.playlist_view_length / 3) * 2) + int(gui.playlist_view_length / 6))

					# If its below we need to test if its in view. If playing track in view, don't jump
					elif abs(self.playlist_view_position - i) >= vl:
						self.playlist_view_position = i
						if i > 6:
							self.playlist_view_position -= 5
						if i > gui.playlist_view_length and i + (gui.playlist_view_length * 2) < len(
								self.multi_playlist[self.active_playlist_viewing].playlist_ids) and i > 10:
							self.playlist_view_position = i - random.randint(2,
								int(gui.playlist_view_length / 3) * 2)

				break

		else:  # Search other all other playlists
			if not this_only:
				for i, playlist in enumerate(self.multi_playlist):
					if track_index in playlist.playlist_ids:
						switch_playlist(i, quiet=True)
						self.show_current(select, playing, quiet, this_only=True, index=track_index)
						break

		self.playlist_view_position = max(self.playlist_view_position, 0)

		# if self.playlist_view_position > len(self.multi_playlist[self.active_playlist_viewing].playlist_ids) - 1:
		#	 logging.info("Run Over")

		if select:
			shift_selection = []

		self.render_playlist()

		if album_mode and not quiet:
			if highlight:
				gui.gallery_animate_highlight_on = goto_album(self.selected_in_playlist)
				gallery_select_animate_timer.set()
			else:
				goto_album(self.selected_in_playlist)

		if prefs.left_panel_mode == "artist list" and gui.lsp and not quiet:
			artist_list_box.locate_artist(self.playing_object())

		if folder_list and prefs.left_panel_mode == "folder view" and gui.lsp and not quiet and not tree_view_box.lock_pl:
			tree_view_box.show_track(self.playing_object())

		return 0

	def toggle_mute(self) -> None:
		global volume_store
		if self.player_volume > 0:
			volume_store = self.player_volume
			self.player_volume = 0
		else:
			self.player_volume = volume_store

		self.set_volume()

	def set_volume(self, notify: bool = True) -> None:

		if (tauon.spot_ctl.coasting or tauon.spot_ctl.playing) and not tauon.spot_ctl.local and mouse_down:
			# Rate limit network volume change
			t = self.volume_update_timer.get()
			if t < 0.3:
				return

		self.volume_update_timer.set()
		self.playerCommand = "volume"
		self.playerCommandReady = True
		if notify:
			self.notify_update()

	def revert(self) -> None:

		if self.queue_step == 0:
			return

		prev = 0
		while len(self.track_queue) > prev + 1 and prev < 5:
			if self.track_queue[len(self.track_queue) - 1 - prev] == self.left_index:
				self.queue_step = len(self.track_queue) - 1 - prev
				self.jump_time = self.left_time
				self.playing_time = self.left_time
				self.decode_time = self.left_time
				break
			prev += 1
		else:
			self.queue_step -= 1
			self.jump_time = 0
			self.playing_time = 0
			self.decode_time = 0

		if not len(self.track_queue) > self.queue_step >= 0:
			logging.error("There is no previous track?")
			return

		self.target_open = self.master_library[self.track_queue[self.queue_step]].fullpath
		self.target_object = self.master_library[self.track_queue[self.queue_step]]
		self.start_time = self.master_library[self.track_queue[self.queue_step]].start_time
		self.start_time_target = self.start_time
		self.playing_length = self.master_library[self.track_queue[self.queue_step]].length
		self.playerCommand = "open"
		self.playerCommandReady = True
		self.playing_state = 1

		if tauon.stream_proxy.download_running:
			tauon.stream_proxy.stop()

		self.show_current()
		self.render_playlist()

	def deduct_shuffle(self, track_id: int) -> None:
		if self.multi_playlist and self.random_mode:
			pl = self.multi_playlist[self.active_playlist_playing]
			id = pl.uuid_int

			if id not in self.shuffle_pools:
				self.update_shuffle_pool(pl.uuid_int)

			pool = self.shuffle_pools[id]
			if not pool:
				del self.shuffle_pools[id]
				self.update_shuffle_pool(pl.uuid_int)
			pool = self.shuffle_pools[id]

			if track_id in pool:
				pool.remove(track_id)


	def play_target_rr(self) -> None:
		tauon.thread_manager.ready_playback()
		self.playing_length = self.master_library[self.track_queue[self.queue_step]].length

		if self.playing_length > 2:
			random_start = random.randrange(1, int(self.playing_length) - 45 if self.playing_length > 50 else int(
				self.playing_length))
		else:
			random_start = 0

		self.playing_time = random_start
		self.target_open = self.master_library[self.track_queue[self.queue_step]].fullpath
		self.target_object = self.master_library[self.track_queue[self.queue_step]]
		self.start_time = self.master_library[self.track_queue[self.queue_step]].start_time
		self.start_time_target = self.start_time
		self.jump_time = random_start
		self.playerCommand = "open"
		if not prefs.use_jump_crossfade:
			self.playerSubCommand = "now"
		self.playerCommandReady = True
		self.playing_state = 1
		radiobox.loaded_station = None

		if tauon.stream_proxy.download_running:
			tauon.stream_proxy.stop()

		if update_title:
			update_title_do()

		self.deduct_shuffle(self.target_object.index)

	def play_target(self, gapless: bool = False, jump: bool = False) -> None:

		tauon.thread_manager.ready_playback()

		#logging.info(self.track_queue)
		self.playing_time = 0
		self.decode_time = 0
		target = self.master_library[self.track_queue[self.queue_step]]
		self.target_open = target.fullpath
		self.target_object = target
		self.start_time = target.start_time
		self.start_time_target = self.start_time
		self.playing_length = target.length
		self.last_playing_time = 0
		self.commit = None
		radiobox.loaded_station = None

		if tauon.stream_proxy and tauon.stream_proxy.download_running:
			tauon.stream_proxy.stop()

		if self.multi_playlist[self.active_playlist_playing].persist_time_positioning:
			t = target.misc.get("position", 0)
			if t:
				self.playing_time = 0
				self.decode_time = 0
				self.jump_time = t

		self.playerCommand = "open"
		if jump:  # and not prefs.use_jump_crossfade:
			self.playerSubCommand = "now"

		self.playerCommandReady = True

		self.playing_state = 1
		self.update_change()
		self.deduct_shuffle(target.index)

	def update_change(self) -> None:
		if update_title:
			update_title_do()
		self.notify_update()
		hit_discord()
		self.render_playlist()

		if lfm_scrobbler.a_sc:
			lfm_scrobbler.a_sc = False
			self.a_time = 0

		lfm_scrobbler.start_queue()

		if (album_mode or not gui.rsp) and (gui.theme_name == "Carbon" or prefs.colour_from_image):
			target = self.playing_object()
			if target and prefs.colour_from_image and target.parent_folder_path == colours.last_album:
				return

			album_art_gen.display(target, (0, 0), (50, 50), theme_only=True)

	def jump(self, index: int, pl_position: int = None, jump: bool = True) -> None:
		lfm_scrobbler.start_queue()
		self.auto_stop = False

		if self.force_queue and not self.pause_queue:
			if self.force_queue[0].uuid_int == 1: # TODO(Martin): How can the UUID be 1 when we're doing a random on 1-1m except for massive chance? Is that the point?
				if self.get_track(self.force_queue[0].track_id).parent_folder_path != self.get_track(index).parent_folder_path:
					del self.force_queue[0]

		if len(self.track_queue) > 0:
			self.left_time = self.playing_time
			self.left_index = self.track_queue[self.queue_step]

			if self.playing_state == 1 and self.left_time > 5 and self.playing_length - self.left_time > 15:
				self.master_library[self.left_index].skips += 1

		global playlist_hold
		gui.update_spec = 0
		self.active_playlist_playing = self.active_playlist_viewing
		self.track_queue.append(index)
		self.queue_step = len(self.track_queue) - 1
		playlist_hold = False
		self.play_target(jump=jump)

		if pl_position is not None:
			self.playlist_playing_position = pl_position

		gui.pl_update = 1

	def back(self) -> None:
		if self.playing_state < 3 and prefs.back_restarts and self.playing_time > 6:
			self.seek_time(0)
			self.render_playlist()
			return

		if tauon.spot_ctl.coasting:
			tauon.spot_ctl.control("previous")
			tauon.spot_ctl.update_timer.set()
			self.playing_time = -2
			self.decode_time = -2
			return

		if len(self.track_queue) > 0:
			self.left_time = self.playing_time
			self.left_index = self.track_queue[self.queue_step]

		gui.update_spec = 0
		# Move up
		if self.random_mode is False and len(self.playing_playlist()) > self.playlist_playing_position > 0:

			if len(self.track_queue) > 0 and self.playing_playlist()[self.playlist_playing_position] != \
					self.track_queue[
						self.queue_step]:

				try:
					p = self.playing_playlist().index(self.track_queue[self.queue_step])
				except Exception:
					logging.exception("Failed to change playing_playlist")
					p = random.randrange(len(self.playing_playlist()))
				if p is not None:
					self.playlist_playing_position = p

			self.playlist_playing_position -= 1
			self.track_queue.append(self.playing_playlist()[self.playlist_playing_position])
			self.queue_step = len(self.track_queue) - 1
			self.play_target(jump=True)

		elif self.random_mode is True and self.queue_step > 0:
			self.queue_step -= 1
			self.play_target(jump=True)
		else:
			logging.info("BACK: NO CASE!")
			self.show_current()

		if self.active_playlist_viewing == self.active_playlist_playing:
			self.show_current(False, True)

		if album_mode:
			goto_album(self.playlist_playing_position)
		if gui.combo_mode and self.active_playlist_viewing == self.active_playlist_playing:
			self.show_current()

		self.render_playlist()
		self.notify_update()
		notify_song()
		lfm_scrobbler.start_queue()
		gui.pl_update += 1

	def stop(self, block: bool = False, run : bool = False) -> None:

		self.playerCommand = "stop"
		if run:
			self.playerCommand = "runstop"
		if block:
			self.playerSubCommand = "return"

		self.playerCommandReady = True

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

		self.record_stream = False
		if len(self.track_queue) > 0:
			self.left_time = self.playing_time
			self.left_index = self.track_queue[self.queue_step]
		previous_state = self.playing_state
		self.playing_time = 0
		self.decode_time = 0
		self.playing_state = 0
		self.render_playlist()

		gui.update_spec = 0
		# gui.update_level = True  # Allows visualiser to enter decay sequence
		gui.update = True
		if update_title:
			update_title_do()  # Update title bar text

		if tauon.stream_proxy and tauon.stream_proxy.download_running:
			tauon.stream_proxy.stop()

		if block:
			loop = 0
			sleep_timeout(lambda: self.playerSubCommand != "stopped", 2)
			if tauon.stream_proxy.download_running:
				sleep_timeout(lambda: tauon.stream_proxy.download_running, 2)

		if tauon.spot_ctl.playing or tauon.spot_ctl.coasting:
			logging.info("Spotify stop")
			tauon.spot_ctl.control("stop")

		self.notify_update()
		lfm_scrobbler.start_queue()
		return previous_state

	def pause(self) -> None:

		if tauon.spotc and tauon.spotc.running and tauon.spot_ctl.playing:
			if self.playing_state == 1:
				self.playerCommand = "pauseon"
				self.playerCommandReady = True
			elif self.playing_state == 2:
				self.playerCommand = "pauseoff"
				self.playerCommandReady = True

		if self.playing_state == 3:
			if tauon.spot_ctl.coasting:
				if tauon.spot_ctl.paused:
					tauon.spot_ctl.control("resume")
				else:
					tauon.spot_ctl.control("pause")
			return

		if tauon.spot_ctl.playing:
			if self.playing_state == 2:
				tauon.spot_ctl.control("resume")
				self.playing_state = 1
			elif self.playing_state == 1:
				tauon.spot_ctl.control("pause")
				self.playing_state = 2
			self.render_playlist()
			return

		if self.playing_state == 1:
			self.playerCommand = "pauseon"
			self.playing_state = 2
		elif self.playing_state == 2:
			self.playerCommand = "pauseoff"
			self.playing_state = 1
			notify_song()

		self.playerCommandReady = True

		self.render_playlist()
		self.notify_update()

	def pause_only(self) -> None:
		if self.playing_state == 1:
			self.playerCommand = "pauseon"
			self.playing_state = 2

			self.playerCommandReady = True
			self.render_playlist()
			self.notify_update()

	def play_pause(self) -> None:
		if self.playing_state == 3:
			self.stop()
		elif self.playing_state > 0:
			self.pause()
		else:
			self.play()

	def seek_decimal(self, decimal: int) -> None:
		# if self.commit:
		#	 return
		if self.playing_state in (1, 2) or (self.playing_state == 3 and tauon.spot_ctl.coasting):
			if decimal > 1:
				decimal = 1
			elif decimal < 0:
				decimal = 0
			self.new_time = self.playing_length * decimal
			#logging.info('seek to:' + str(self.new_time))
			self.playerCommand = "seek"
			self.playerCommandReady = True
			self.playing_time = self.new_time

			if msys and taskbar_progress and self.windows_progress:
				self.windows_progress.update(True)

			if self.mpris is not None:
				self.mpris.seek_do(self.playing_time)

	def seek_time(self, new: float) -> None:
		# if self.commit:
		#	 return
		if self.playing_state in (1, 2) or (self.playing_state == 3 and tauon.spot_ctl.coasting):

			if new > self.playing_length - 0.5:
				self.advance()
				return

			if new < 0.4:
				new = 0

			self.new_time = new
			self.playing_time = new

			self.playerCommand = "seek"
			self.playerCommandReady = True

			if self.mpris is not None:
				self.mpris.seek_do(self.playing_time)

	def play(self) -> None:

		if tauon.spot_ctl.playing:
			if self.playing_state == 2:
				self.play_pause()
			return

		# Unpause if paused
		if self.playing_state == 2:
			self.playerCommand = "pauseoff"
			self.playerCommandReady = True
			self.playing_state = 1
			self.notify_update()

		# If stopped
		elif self.playing_state == 0:

			if radiobox.loaded_station:
				radiobox.start(radiobox.loaded_station)
				return

			# If the queue is empty
			if self.track_queue == [] and len(self.multi_playlist[self.active_playlist_playing].playlist_ids) > 0:
				self.track_queue.append(self.multi_playlist[self.active_playlist_playing].playlist_ids[0])
				self.queue_step = 0
				self.playlist_playing_position = 0
				self.active_playlist_playing = 0

				self.play_target()

			# If the queue is not empty, play?
			elif len(self.track_queue) > 0:
				self.play_target()

		self.render_playlist()

	def spot_test_progress(self) -> None:
		if self.playing_state in (1, 2) and tauon.spot_ctl.playing:
			th = 5  # the rate to poll the spotify API
			if self.playing_time > self.playing_length:
				th = 1
			if not tauon.spot_ctl.paused:
				if tauon.spot_ctl.start_timer.get() < 0.5:
					tauon.spot_ctl.progress_timer.set()
					return
				add_time = tauon.spot_ctl.progress_timer.get()
				if add_time > 5:
					add_time = 0
				self.playing_time += add_time
				self.decode_time = self.playing_time
				# self.test_progress()
				tauon.spot_ctl.progress_timer.set()
				if len(self.track_queue) > 0 and 2 > add_time > 0:
					star_store.add(self.track_queue[self.queue_step], add_time)
			if tauon.spot_ctl.update_timer.get() > th:
				tauon.spot_ctl.update_timer.set()
				shooter(tauon.spot_ctl.monitor)
			else:
				self.test_progress()

		elif self.playing_state == 3 and tauon.spot_ctl.coasting:
			th = 7
			if self.playing_time > self.playing_length or self.playing_time < 2.5:
				th = 1
			if tauon.spot_ctl.update_timer.get() < th:
				if not tauon.spot_ctl.paused:
					self.playing_time += tauon.spot_ctl.progress_timer.get()
					self.decode_time = self.playing_time
				tauon.spot_ctl.progress_timer.set()

			else:
				tauon.spot_ctl.update_timer.set()
				tauon.spot_ctl.update()

	def purge_track(self, track_id: int, fast: bool = False) -> None:
		"""Remove a track from the database"""
		# Remove from all playlists
		if not fast:
			for playlist in self.multi_playlist:
				while track_id in playlist.playlist:
					album_dex.clear()
					playlist.playlist.remove(track_id)
		# Stop if track is playing track
		if self.track_queue and self.track_queue[self.queue_step] == track_id and self.playing_state != 0:
			self.stop(block=True)
		# Remove from playback history
		while track_id in self.track_queue:
			self.track_queue.remove(track_id)
			self.queue_step -= 1
		# Remove track from force queue
		for i in reversed(range(len(self.force_queue))):
			if self.force_queue[i].track_id == track_id:
				del self.force_queue[i]
		del self.master_library[track_id]

	def test_progress(self) -> None:
		# Fuzzy reload lastfm for rescrobble
		if lfm_scrobbler.a_sc and self.playing_time < 1:
			lfm_scrobbler.a_sc = False
			self.a_time = 0

		# Update the UI if playing time changes a whole number
		# next_round = int(self.playing_time)
		# if self.playing_time_int != next_round:
		#	 #if not prefs.power_save:
		#	 #gui.update += 1
		#	 self.playing_time_int = next_round

		gap_extra = 2  # 2

		if tauon.spot_ctl.playing or tauon.chrome_mode:
			gap_extra = 3

		if msys and taskbar_progress and self.windows_progress:
			self.windows_progress.update(True)

		if self.commit is not None:
			return

		if self.playing_state == 1 and self.multi_playlist[self.active_playlist_playing].persist_time_positioning:
			tr = self.playing_object()
			if tr:
				tr.misc["position"] = self.decode_time

		if self.playing_state == 1 and self.decode_time + gap_extra >= self.playing_length and self.decode_time > 0.2:

			# Allow some time for spotify playing time to update?
			if tauon.spot_ctl.playing and tauon.spot_ctl.start_timer.get() < 3:
				return

			# Allow some time for backend to provide a length
			if self.playing_time < 6 and self.playing_length == 0:
				return
			if not tauon.spot_ctl.playing and self.a_time < 2:
				return

			self.decode_time = 0

			pp = self.playing_playlist()

			if self.auto_stop:  # and not self.force_queue and not (self.force_queue and self.pause_queue):
				self.stop(run=True)
				if self.force_queue or (not self.force_queue and not self.random_mode and not self.repeat_mode):
					self.advance(play=False)
				gui.update += 2
				self.auto_stop = False

			elif self.force_queue and not self.pause_queue:
				id = self.advance(end=True, quiet=True, dry=True)
				if id is not None:
					self.start_commit(id)
					return
				self.advance(end=True, quiet=True)



			elif self.repeat_mode is True:

				if self.album_repeat_mode:

					if self.playlist_playing_position > len(pp) - 1:
						self.playlist_playing_position = 0  # Hack fix, race condition bug?

					ti = self.get_track(pp[self.playlist_playing_position])

					i = self.playlist_playing_position

					# Test if next track is in same folder
					if i + 1 < len(pp):
						nt = self.get_track(pp[i + 1])
						if ti.parent_folder_path == nt.parent_folder_path:
							# The next track is in the same folder
							# so advance normally
							self.advance(quiet=True, end=True)
							return

					# We need to backtrack to see where the folder begins
					i -= 1
					while i >= 0:
						nt = self.get_track(pp[i])
						if ti.parent_folder_path != nt.parent_folder_path:
							i += 1
							break
						i -= 1
					i = max(i, 0)

					self.selected_in_playlist = i
					shift_selection = [i]

					self.jump(pp[i], i, jump=False)

				elif prefs.playback_follow_cursor and self.playing_ready() \
						and self.multi_playlist[self.active_playlist_viewing].playlist[
					self.selected_in_playlist] != self.playing_object().index \
						and -1 < self.selected_in_playlist < len(default_playlist):

					logging.info("Repeat follow cursor")

					self.playing_time = 0
					self.decode_time = 0
					self.active_playlist_playing = self.active_playlist_viewing
					self.playlist_playing_position = self.selected_in_playlist

					self.track_queue.append(default_playlist[self.selected_in_playlist])
					self.queue_step = len(self.track_queue) - 1
					self.play_target(jump=False)
					self.render_playlist()
					lfm_scrobbler.start_queue()

				else:
					id = self.track_queue[self.queue_step]
					self.commit = id
					target = self.get_track(id)
					self.target_open = target.fullpath
					self.target_object = target
					self.start_time = target.start_time
					self.start_time_target = self.start_time
					self.playerCommand = "open"
					self.playerSubCommand = "repeat"
					self.playerCommandReady = True

					#self.render_playlist()
					lfm_scrobbler.start_queue()

					# Reload lastfm for rescrobble
					if lfm_scrobbler.a_sc:
						lfm_scrobbler.a_sc = False
						self.a_time = 0

			elif self.random_mode is False and len(pp) > self.playlist_playing_position + 1 and \
					self.master_library[pp[self.playlist_playing_position]].is_cue is True \
					and self.master_library[pp[self.playlist_playing_position + 1]].filename == \
					self.master_library[pp[self.playlist_playing_position]].filename and int(
				self.master_library[pp[self.playlist_playing_position]].track_number) == int(
				self.master_library[pp[self.playlist_playing_position + 1]].track_number) - 1:

				#  not (self.force_queue and not self.pause_queue) and \

				# We can shave it closer
				if not self.playing_time + 0.1 >= self.playing_length:
					return

				logging.info("Do transition CUE")
				self.playlist_playing_position += 1
				self.queue_step += 1
				self.track_queue.append(pp[self.playlist_playing_position])
				self.playing_state = 1
				self.playing_time = 0
				self.decode_time = 0
				self.playing_length = self.master_library[self.track_queue[self.queue_step]].length
				self.start_time = self.master_library[self.track_queue[self.queue_step]].start_time
				self.start_time_target = self.start_time
				lfm_scrobbler.start_queue()

				gui.update += 1
				gui.pl_update = 1

				if update_title:
					update_title_do()
				self.notify_update()
			else:
				# self.advance(quiet=True, end=True)

				id = self.advance(quiet=True, end=True, dry=True)
				if id is not None and not tauon.spot_ctl.playing:
					#logging.info("Commit")
					self.start_commit(id)
					return

				self.advance(quiet=True, end=True)
				self.playing_time = 0
				self.decode_time = 0

	def start_commit(self, commit_id: int, repeat: bool = False) -> None:
		self.commit = commit_id
		target = self.get_track(commit_id)
		self.target_open = target.fullpath
		self.target_object = target
		self.start_time = target.start_time
		self.start_time_target = self.start_time
		self.playerCommand = "open"
		if repeat:
			self.playerSubCommand = "repeat"
		self.playerCommandReady = True

	def advance(
		self, rr: bool = False, quiet: bool = False, inplace: bool = False, end: bool = False,
		force: bool = False, play: bool = True, dry: bool = False,
	) -> int | None:
		# Spotify remote control mode
		if not dry and tauon.spot_ctl.coasting:
			tauon.spot_ctl.control("next")
			tauon.spot_ctl.update_timer.set()
			self.playing_time = -2
			self.decode_time = -2
			return None

		# Temporary Workaround for UI block causing unwanted dragging
		if not dry:
			quick_d_timer.set()

		if prefs.show_current_on_transition:
			quiet = False

		# Trim the history if it gets too long
		while len(self.track_queue) > 250:
			self.queue_step -= 1
			del self.track_queue[0]

		# Save info about the track we are leaving
		if not dry and len(self.track_queue) > 0:
			self.left_time = self.playing_time
			self.left_index = self.track_queue[self.queue_step]

		# Test to register skip (not currently used for anything)
		if not dry and self.playing_state == 1 and 1 < self.left_time < 45:
			self.master_library[self.left_index].skips += 1
			#logging.info('skip registered')

		if not dry:
			self.playing_time = 0
			self.decode_time = 0
			self.playing_length = 100
			gui.update_spec = 0

		old = self.queue_step
		end_of_playlist = False

		# Force queue (middle click on track)
		if len(self.force_queue) > 0 and not self.pause_queue:

			q = self.force_queue[0]
			target_index = q.track_id

			if q.type == 1:
				# This is an album type

				if q.album_stage == 0:
					# We have not started playing the album yet
					# So we go to that track
					# (This is a copy of the track code, but we don't delete the item)

					if not dry:

						pl = id_to_pl(q.playlist_id)
						if pl is not None:
							self.active_playlist_playing = pl

						if target_index not in self.playing_playlist():
							del self.force_queue[0]
							self.advance()
							return None

					if dry:
						return target_index

					self.playlist_playing_position = q.position
					self.track_queue.append(target_index)
					self.queue_step = len(self.track_queue) - 1
					# self.queue_target = len(self.track_queue) - 1
					if play:
						self.play_target(jump=not end)

					#  Set the flag that we have entered the album
					self.force_queue[0].album_stage = 1

					# This code is mirrored below -------
					ok_continue = True

					# Check if we are at end of playlist
					pl = self.multi_playlist[self.active_playlist_playing].playlist_ids
					if self.playlist_playing_position > len(pl) - 3:
						ok_continue = False

					# Check next song is in album
					if ok_continue and self.get_track(pl[self.playlist_playing_position + 1]).parent_folder_path != self.get_track(target_index).parent_folder_path:
						ok_continue = False

					# -----------


				elif q.album_stage == 1:
					# We have previously started playing this album

					# Check to see if we still are:
					ok_continue = True

					if self.get_track(target_index).parent_folder_path != self.playing_object().parent_folder_path:
						# Remember to set jumper check this too (leave album if we jump to some other track, i.e. double click))
						ok_continue = False

					pl = self.multi_playlist[self.active_playlist_playing].playlist_ids

					# Check next song is in album
					if ok_continue:

						# Check if we are at end of playlist, or already at end of album
						if self.playlist_playing_position >= len(pl) - 1 or (self.playlist_playing_position < len(
								pl) - 1 and \
								self.get_track(pl[self.playlist_playing_position + 1]).parent_folder_path != self.get_track(
							target_index).parent_folder_path):

							if dry:
								return None

							del self.force_queue[0]
							self.advance()
							return None


						# Check if 2 songs down is in album, remove entry in queue if not
						if self.playlist_playing_position < len(pl) - 2 and \
								self.get_track(pl[self.playlist_playing_position + 2]).parent_folder_path != self.get_track(
							target_index).parent_folder_path:
							ok_continue = False

					# if ok_continue:
					# We seem to be still in the album. Step down one and play
					if not dry:
						self.playlist_playing_position += 1

					if len(pl) <= self.playlist_playing_position:
						if dry:
							return None
						logging.info("END OF PLAYLIST!")
						del self.force_queue[0]
						self.advance()
						return None

					if dry:
						return pl[self.playlist_playing_position + 1]
					self.track_queue.append(pl[self.playlist_playing_position])
					self.queue_step = len(self.track_queue) - 1
					# self.queue_target = len(self.track_queue) - 1
					if play:
						self.play_target(jump=not end)

				if not ok_continue:
					# It seems this item has expired, remove it and call advance again

					if dry:
						return None

					logging.info("Remove expired album from queue")
					del self.force_queue[0]

					if q.auto_stop:
						self.auto_stop = True
					if prefs.stop_end_queue and not self.force_queue:
						self.auto_stop = True

					if queue_box.scroll_position > 0:
						queue_box.scroll_position -= 1

						# self.advance()
						# return

			else:
				# This is track type
				pl = id_to_pl(q.playlist_id)
				if not dry and pl is not None:
					self.active_playlist_playing = pl

				if target_index not in self.playing_playlist():
					if dry:
						return None
					del self.force_queue[0]
					self.advance()
					return None

				if dry:
					return target_index

				self.playlist_playing_position = q.position
				self.track_queue.append(target_index)
				self.queue_step = len(self.track_queue) - 1
				# self.queue_target = len(self.track_queue) - 1
				if play:
					self.play_target(jump=not end)
				del self.force_queue[0]
				if q.auto_stop:
					self.auto_stop = True
				if prefs.stop_end_queue and not self.force_queue:
					self.auto_stop = True
				if queue_box.scroll_position > 0:
					queue_box.scroll_position -= 1

		# Stop if playlist is empty
		elif len(self.playing_playlist()) == 0:
			if dry:
				return None
			self.stop()
			return 0

		# Playback follow cursor
		elif prefs.playback_follow_cursor and self.playing_ready() \
				and self.multi_playlist[self.active_playlist_viewing].playlist_ids[
			self.selected_in_playlist] != self.playing_object().index \
				and -1 < self.selected_in_playlist < len(default_playlist):

			if dry:
				return default_playlist[self.selected_in_playlist]

			self.active_playlist_playing = self.active_playlist_viewing
			self.playlist_playing_position = self.selected_in_playlist

			self.track_queue.append(default_playlist[self.selected_in_playlist])
			self.queue_step = len(self.track_queue) - 1
			if play:
				self.play_target(jump=not end)

		# If random, jump to random track
		elif (self.random_mode or rr) and len(self.playing_playlist()) > 0 and not (
				self.album_shuffle_mode or prefs.album_shuffle_lock_mode):
			# self.queue_step += 1
			new_step = self.queue_step + 1

			if new_step == len(self.track_queue):

				if self.album_repeat_mode and self.repeat_mode:
					# Album shuffle mode
					pp = self.playing_playlist()
					k = self.playlist_playing_position
					# ti = self.get_track(pp[k])
					ti = self.master_library[self.track_queue[self.queue_step]]

					if ti.index not in pp:
						if dry:
							return None
						logging.info("No tracks to repeat!")
						return 0

					matches = []
					for i, p in enumerate(pp):

						if self.get_track(p).parent_folder_path == ti.parent_folder_path:
							matches.append((i, p))

					if matches:
						# Avoid a repeat of same track
						if len(matches) > 1 and (k, ti.index) in matches:
							matches.remove((k, ti.index))

						i, p = random.choice(matches)  # not used

						if prefs.true_shuffle:

							id = ti.parent_folder_path

							while True:
								if id in self.shuffle_pools:

									pool = self.shuffle_pools[id]

									if not pool:
										del self.shuffle_pools[id]  # Trigger a refill
										continue

									ref = pool.pop()
									if dry:
										pool.append(ref)
										return ref[1]
									# ref = random.choice(pool)
									# pool.remove(ref)

									if ref[1] not in pp:  # Check track still in the live playlist
										logging.info("Track not in pool")
										continue

									i, p = ref  # Find position of reference in playlist
									break

								# Refill the pool
								random.shuffle(matches)
								self.shuffle_pools[id] = matches
								logging.info("Refill folder shuffle pool")

						self.playlist_playing_position = i
						self.track_queue.append(p)

				else:
					# Normal select from playlist

					if prefs.true_shuffle:
						# True shuffle avoids repeats by using a pool

						pl = self.multi_playlist[self.active_playlist_playing]
						id = pl.uuid_int

						while True:

							if id in self.shuffle_pools:

								pool = self.shuffle_pools[id]

								if not pool:
									del self.shuffle_pools[id]  # Trigger a refill
									continue

								ref = pool.pop()
								if dry:
									pool.append(ref)
									return ref
								# ref = random.choice(pool)
								# pool.remove(ref)

								if ref not in pl.playlist_ids:  # Check track still in the live playlist
									continue

								random_jump = pl.playlist_ids.index(ref)  # Find position of reference in playlist
								break

							# Refill the pool
							self.update_shuffle_pool(pl.uuid_int)

					else:
						random_jump = random.randrange(len(self.playing_playlist()))  # not used

					self.playlist_playing_position = random_jump
					self.track_queue.append(self.playing_playlist()[random_jump])

			if inplace and self.queue_step > 1:
				del self.track_queue[self.queue_step]
			else:
				if dry:
					return self.track_queue[new_step]
				self.queue_step = new_step

			if rr:
				if dry:
					return None
				self.play_target_rr()
			elif play:
				self.play_target(jump=not end)


		# If not random mode, Step down 1 on the playlist
		elif self.random_mode is False and len(self.playing_playlist()) > 0:

			# Stop at end of playlist
			if self.playlist_playing_position == len(self.playing_playlist()) - 1:
				if dry:
					return None
				if prefs.end_setting == "stop":
					self.playing_state = 0
					self.playerCommand = "runstop"
					self.playerCommandReady = True
					end_of_playlist = True

				elif prefs.end_setting in ("advance", "cycle"):

					# If at end playlist and not cycle mode, stop playback
					if self.active_playlist_playing == len(
							self.multi_playlist) - 1 and prefs.end_setting != "cycle":
						self.playing_state = 0
						self.playerCommand = "runstop"
						self.playerCommandReady = True
						end_of_playlist = True

					else:

						p = self.active_playlist_playing
						for i in range(len(self.multi_playlist)):

							k = (p + i + 1) % len(self.multi_playlist)

							# Skip a playlist if empty
							if not (self.multi_playlist[k].playlist_ids):
								continue

							# Skip a playlist if hidden
							if self.multi_playlist[k].hidden and prefs.tabs_on_top:
								continue

							# Set found playlist as playing the first track
							self.active_playlist_playing = k
							self.playlist_playing_position = -1
							self.advance(end=end, force=True, play=play)
							break

						else:
							# Restart current if no other eligible playlist found
							self.playlist_playing_position = -1
							self.advance(end=end, force=True, play=play)

						return None

				elif prefs.end_setting == "repeat":
					self.playlist_playing_position = -1
					self.advance(end=end, force=True, play=play)
					return None

				gui.update += 3

			else:
				if self.playlist_playing_position > len(self.playing_playlist()) - 1:
					if dry:
						return None
					self.playlist_playing_position = 0

				elif not force and len(self.track_queue) > 0 and self.playing_playlist()[
					self.playlist_playing_position] != self.track_queue[
					self.queue_step]:
					try:
						if dry:
							return None
						self.playlist_playing_position = self.playing_playlist().index(
							self.track_queue[self.queue_step])
					except Exception:
						logging.exception("Failed to set playlist_playing_position")

				if len(self.playing_playlist()) == self.playlist_playing_position + 1:
					return None

				if dry:
					return self.playing_playlist()[self.playlist_playing_position + 1]
				self.playlist_playing_position += 1
				self.track_queue.append(self.playing_playlist()[self.playlist_playing_position])

				# logging.info("standand advance")
				# self.queue_target = len(self.track_queue) - 1
				# if end:
				#	 self.play_target_gapless(jump= not end)
				# else:
				self.queue_step = len(self.track_queue) - 1
				if play:
					self.play_target(jump=not end)

		elif self.random_mode and (self.album_shuffle_mode or prefs.album_shuffle_lock_mode):

			# Album shuffle mode
			logging.info("Album shuffle mode")

			po = self.playing_object()

			redraw = False

			# Checks
			if po is not None and len(self.playing_playlist()) > 0:

				# If we at end of playlist, we'll go to a new album
				if len(self.playing_playlist()) == self.playlist_playing_position + 1:
					redraw = True
				# If the next track is a new album, go to a new album
				elif po.parent_folder_path != self.get_track(
						self.playing_playlist()[self.playlist_playing_position + 1]).parent_folder_path:
					redraw = True
				# Always redraw on press in album shuffle lockdown
				if prefs.album_shuffle_lock_mode and not end:
					redraw = True

				if not redraw:
					if dry:
						return self.playing_playlist()[self.playlist_playing_position + 1]
					self.playlist_playing_position += 1
					self.track_queue.append(self.playing_playlist()[self.playlist_playing_position])
					self.queue_step = len(self.track_queue) - 1
					# self.queue_target = len(self.track_queue) - 1
					if play:
						self.play_target(jump=not end)

				else:

					if dry:
						return None
					albums = []
					current_folder = ""
					for i in range(len(self.playing_playlist())):
						if i == 0:
							albums.append(i)
							current_folder = self.master_library[self.playing_playlist()[i]].parent_folder_path
						elif self.master_library[self.playing_playlist()[i]].parent_folder_path != current_folder:
							current_folder = self.master_library[self.playing_playlist()[i]].parent_folder_path
							albums.append(i)

					random.shuffle(albums)

					for a in albums:
						if self.get_track(self.playing_playlist()[a]).parent_folder_path != self.playing_object().parent_folder_path:
							self.playlist_playing_position = a
							self.track_queue.append(self.playing_playlist()[a])
							self.queue_step = len(self.track_queue) - 1
							# self.queue_target = len(self.track_queue) - 1
							if play:
								self.play_target(jump=not end)
							break
						a = 0
						self.playlist_playing_position = a
						self.track_queue.append(self.playing_playlist()[a])
						self.queue_step = len(self.track_queue) - 1
						if play:
							self.play_target(jump=not end)
						# logging.info("THERE IS ONLY ONE ALBUM IN THE PLAYLIST")
						# self.stop()

		else:
			logging.error("ADVANCE ERROR - NO CASE!")

		if dry:
			return None

		if self.active_playlist_viewing == self.active_playlist_playing:
			self.show_current(quiet=quiet)
		elif prefs.auto_goto_playing:
			self.show_current(quiet=quiet, this_only=True, playing=False, highlight=True, no_switch=True)

		# if album_mode:
		#	 goto_album(self.playlist_playing)

		self.render_playlist()

		if tauon.spot_ctl.playing and end_of_playlist:
			tauon.spot_ctl.control("stop")

		self.notify_update()
		lfm_scrobbler.start_queue()
		if play:
			notify_song(end_of_playlist, delay=1.3)
		return None

	def reset_missing_flags(self) -> None:
		for value in self.master_library.values():
			value.found = True
		gui.pl_update += 1

class LastFMapi:
	API_SECRET = "6e433964d3ff5e817b7724d16a9cf0cc"
	connected = False
	API_KEY = "bfdaf6357f1dddd494e5bee1afe38254"
	scanning_username = ""

	network = None
	lastfm_network = None
	tries = 0

	scanning_friends = False
	scanning_loves = False
	scanning_scrobbles = False

	def __init__(self) -> None:
		self.sg = None
		self.url = None

	def get_network(self) -> LibreFMNetwork:
		if prefs.use_libre_fm:
			return pylast.LibreFMNetwork
		return pylast.LastFMNetwork

	def auth1(self) -> None:
		if not last_fm_enable:
			show_message(_("Optional module python-pylast not installed"), mode="warning")
			return
		# This is step one where the user clicks "login"

		if self.network is None:
			self.no_user_connect()

		self.sg = pylast.SessionKeyGenerator(self.network)
		self.url = self.sg.get_web_auth_url()
		show_message(_("Web auth page opened"), _("Once authorised click the 'done' button."), mode="arrow")
		webbrowser.open(self.url, new=2, autoraise=True)

	def auth2(self) -> None:

		# This is step 2 where the user clicks "Done"

		if self.sg is None:
			show_message(_("You need to log in first"))
			return

		try:
			# session_key = self.sg.get_web_auth_session_key(self.url)
			session_key, username = self.sg.get_web_auth_session_key_username(self.url)
			prefs.last_fm_token = session_key
			self.network = self.get_network()(api_key=self.API_KEY, api_secret=
			self.API_SECRET, session_key=prefs.last_fm_token)
			# user = self.network.get_authenticated_user()
			# username = user.get_name()
			prefs.last_fm_username = username

		except Exception as e:
			if "Unauthorized Token" in str(e):
				logging.exception("Not authorized")
				show_message(_("Error - Not authorized"), mode="error")
			else:
				logging.exception("Unknown error")
				show_message(_("Error"), _("Unknown error."), mode="error")

		if not toggle_lfm_auto(mode=1):
			toggle_lfm_auto()

	def auth3(self) -> None:
		"""This is used for 'logout'"""
		prefs.last_fm_token = None
		prefs.last_fm_username = ""
		show_message(_("Logout will complete on app restart."))

	def connect(self, m_notify: bool = True) -> bool | None:

		if not last_fm_enable:
			return False

		if self.connected is True:
			if m_notify:
				show_message(_("Already connected to Last.fm"))
			return True

		if prefs.last_fm_token is None:
			show_message(_("No Last.Fm account registered"), _("Authorise an account in settings"), mode="info")
			return None

		logging.info("Attempting to connect to Last.fm network")

		try:

			self.network = self.get_network()(
				api_key=self.API_KEY, api_secret=self.API_SECRET, session_key=prefs.last_fm_token)  # , username=lfm_username, password_hash=lfm_hash)

			self.connected = True
			if m_notify:
				show_message(_("Connection to Last.fm was successful."), mode="done")

			logging.info("Connection to lastfm appears successful")
			return True

		except Exception as e:
			logging.exception("Error connecting to Last.fm network")
			show_message(_("Error connecting to Last.fm network"), str(e), mode="warning")
			return False

	def toggle(self) -> None:
		prefs.scrobble_hold ^= True

	def details_ready(self) -> bool:
		if prefs.last_fm_token:
			return True
		return False

	def last_fm_only_connect(self) -> bool:
		if not last_fm_enable:
			return False
		try:
			self.lastfm_network = pylast.LastFMNetwork(api_key=self.API_KEY, api_secret=self.API_SECRET)
			logging.info("Connection appears successful")
			return True

		except Exception as e:
			logging.exception("Error communicating with Last.fm network")
			show_message(_("Error communicating with Last.fm network"), str(e), mode="warning")
			return False

	def no_user_connect(self) -> bool:
		if not last_fm_enable:
			return False
		try:
			self.network = self.get_network()(api_key=self.API_KEY, api_secret=self.API_SECRET)
			logging.info("Connection appears successful")
			return True

		except Exception as e:
			logging.exception("Error communicating with Last.fm network")
			show_message(_("Error communicating with Last.fm network"), str(e), mode="warning")
			return False

	def get_all_scrobbles_estimate_time(self) -> float | None:

		if not self.connected:
			self.connect(False)
		if not self.connected or not prefs.last_fm_username:
			return None

		user = pylast.User(prefs.last_fm_username, self.network)
		total = user.get_playcount()

		if total:
			return 0.04364 * total
		return 0

	def get_all_scrobbles(self) -> None:

		if not self.connected:
			self.connect(False)
		if not self.connected or not prefs.last_fm_username:
			return

		try:
			self.scanning_scrobbles = True
			self.network.enable_rate_limit()
			user = pylast.User(prefs.last_fm_username, self.network)
			# username = user.get_name()
			perf_timer.set()
			tracks = user.get_recent_tracks(None)

			counts = {}

			# Count up the unique pairs
			for track in tracks:
				key = (str(track.track.artist), str(track.track.title))
				c = counts.get(key, 0)
				counts[key] = c + 1

			touched = []

			# Add counts to matching tracks
			for key, value in counts.items():
				artist, title = key
				artist = artist.lower()
				title = title.lower()

				for track in pctl.master_library.values():
					t_artist = track.artist.lower()
					artists = [x.lower() for x in get_split_artists(track)]
					if t_artist == artist or artist in artists or (
							track.album_artist and track.album_artist.lower() == artist):
						if track.title.lower() == title:
							if track.index in touched:
								track.lfm_scrobbles += value
							else:
								track.lfm_scrobbles = value
								touched.append(track.index)
		except Exception:
			logging.exception("Scanning failed. Try again?")
			gui.pl_update += 1
			self.scanning_scrobbles = False
			show_message(_("Scanning failed. Try again?"), mode="error")
			return

		logging.info(perf_timer.get())
		gui.pl_update += 1
		self.scanning_scrobbles = False
		tauon.bg_save()
		show_message(_("Scanning scrobbles complete"), mode="done")

	def artist_info(self, artist: str):

		if self.lastfm_network is None:
			if self.last_fm_only_connect() is False:
				return False, "", ""

		try:
			if artist != "":
				l_artist = pylast.Artist(
					artist.replace("/", "").replace("\\", "").replace(" & ", " and ").replace("&", " "),
					self.lastfm_network)
				bio = l_artist.get_bio_content()
				# cover_link = l_artist.get_cover_image()
				mbid = l_artist.get_mbid()
				url = l_artist.get_url()

				return True, bio, "", mbid, url
		except Exception:
			logging.exception("last.fm get artist info failed")

		return False, "", "", "", ""

	def artist_mbid(self, artist: str):

		if self.lastfm_network is None:
			if self.last_fm_only_connect() is False:
				return ""

		try:
			if artist != "":
				l_artist = pylast.Artist(
					artist.replace("/", "").replace("\\", "").replace(" & ", " and ").replace("&", " "),
					self.lastfm_network)
				mbid = l_artist.get_mbid()
				return mbid
		except Exception:
			logging.exception("last.fm get artist mbid info failed")

		return ""

	def sync_pull_love(self, track_object: TrackClass) -> None:
		if not prefs.lastfm_pull_love or not (track_object.artist and track_object.title):
			return
		if not last_fm_enable:
			return
		if prefs.auto_lfm:
			self.connect(False)
		if not self.connected:
			return

		try:
			track = self.network.get_track(track_object.artist, track_object.title)
			if not track:
				logging.error("Get love: track not found")
				return
			track.username = prefs.last_fm_username

			remote_loved = track.get_userloved()

			if track_object.title != track.get_correction() or track_object.artist != track.get_artist().get_correction():
				logging.warning(f"Pylast/lastfm bug workaround. API thought {track_object.artist} - {track_object.title} loved status was: {remote_loved}")
				return

			if remote_loved is None:
				logging.error("Error getting loved status")
				return

			local_loved = love(set=False, track_id=track_object.index, notify=False, sync=False)

			if remote_loved != local_loved:
				love(set=True, track_id=track_object.index, notify=False, sync=False)
		except Exception:
			logging.exception("Failed to pull love")

	def scrobble(self, track_object: TrackClass, timestamp: float | None = None) -> bool:
		if not last_fm_enable:
			return True
		if prefs.scrobble_hold:
			return True
		if prefs.auto_lfm:
			self.connect(False)

		if timestamp is None:
			timestamp = int(time.time())

		# lastfm_user = self.network.get_user(self.username)

		title = track_object.title
		album = track_object.album
		artist = get_artist_strip_feat(track_object)
		album_artist = track_object.album_artist

		logging.info("Submitting scrobble...")

		# Act
		try:
			if title != "" and artist != "":
				if album != "":
					if album_artist and album_artist != artist:
						self.network.scrobble(
							artist=artist, title=title, album=album, album_artist=album_artist, timestamp=timestamp)
					else:
						self.network.scrobble(artist=artist, title=title, album=album, timestamp=timestamp)
				else:
					self.network.scrobble(artist=artist, title=title, timestamp=timestamp)
				# logging.info('Scrobbled')

				# Pull loved status

				self.sync_pull_love(track_object)


			else:
				logging.warning("Not sent, incomplete metadata")

		except Exception as e:
			logging.exception("Failed to Scrobble!")
			if "retry" in str(e):
				logging.warning("Retrying in a couple seconds...")
				time.sleep(7)

				try:
					self.network.scrobble(artist=artist, title=title, timestamp=timestamp)
					# logging.info('Scrobbled')
					return True
				except Exception:
					logging.exception("Failed to retry!")

			# show_message(_("Error: Could not scrobble. ", str(e), mode='warning')
			logging.error("Error connecting to last.fm")
			scrobble_warning_timer.set()
			gui.update += 1
			gui.delay_frame(5)

			return False
		return True

	def get_bio(self, artist: str) -> str:

		if self.lastfm_network is None:
			if self.last_fm_only_connect() is False:
				return ""

		artist_object = pylast.Artist(artist, self.lastfm_network)
		bio = artist_object.get_bio_summary(language="en")
		# logging.info(artist_object.get_cover_image())
		# logging.info("\n\n")
		# logging.info(bio)
		# logging.info("\n\n")
		# logging.info(artist_object.get_bio_content())
		return bio
		# else:
		#	return ""

	def love(self, artist: str, title: str):

		if not self.connected and prefs.auto_lfm:
			self.connect(False)
			prefs.scrobble_hold = True
		if self.connected and artist != "" and title != "":
			track = self.network.get_track(artist, title)
			track.love()

	def unlove(self, artist: str, title: str):
		if not last_fm_enable:
			return
		if not self.connected and prefs.auto_lfm:
			self.connect(False)
			prefs.scrobble_hold = True
		if self.connected and artist != "" and title != "":
			track = self.network.get_track(artist, title)
			track.love()
			track.unlove()

	def clear_friends_love(self) -> None:

		count = 0
		for index, tr in pctl.master_library.items():
			count += len(tr.lfm_friend_likes)
			tr.lfm_friend_likes.clear()

		show_message(_("Removed {N} loves.").format(N=count))

	def get_friends_love(self):
		if not last_fm_enable:
			return
		self.scanning_friends = True

		try:
			username = prefs.last_fm_username
			logging.info(f"Username is {username}")

			if not username:
				self.scanning_friends = False
				show_message(_("There was an error, try re-log in"))
				return

			if self.network is None:
				self.no_user_connect()

			self.network.enable_rate_limit()
			lastfm_user = self.network.get_user(username)
			friends = lastfm_user.get_friends(limit=None)
			show_message(_("Getting friend data..."), _("This may take a very long time."), mode="info")
			for friend in friends:
				self.scanning_username = friend.name
				logging.info("Getting friend loves: " + friend.name)

				try:
					loves = friend.get_loved_tracks(limit=None)
				except Exception:
					logging.exception("Failed to get_loved_tracks!")

				for track in loves:
					title = track.track.title.casefold()
					artist = track.track.artist.name.casefold()
					for index, tr in pctl.master_library.items():

						if tr.title.casefold() == title and tr.artist.casefold() == artist:
							tr.lfm_friend_likes.add(friend.name)
							logging.info("MATCH")
							logging.info("     " + artist + " - " + title)
							logging.info("      ----- " + friend.name)

		except Exception:
			logging.exception("There was an error getting friends loves")
			show_message(_("There was an error getting friends loves"), "", mode="warning")

		self.scanning_friends = False

	def dl_love(self) -> None:
		if not last_fm_enable:
			return
		username = prefs.last_fm_username
		show_message(_("Scanning loved tracks for: {username}").format(username=username), mode="info")
		self.scanning_username = username

		if not username:
			show_message(_("No username found"), mode="error")
			return

		if len(username) > 25:
			logging.error("Aborted due to long username")
			return

		self.scanning_loves = True

		logging.info("Connect for friend scan")

		try:
			if self.network is None:
				self.no_user_connect()

			self.network.enable_rate_limit()
			logging.info("Get user...")
			lastfm_user = self.network.get_user(username)
			tracks = lastfm_user.get_loved_tracks(limit=None)

			matches = 0
			updated = 0

			for track in tracks:
				title = track.track.title.casefold()
				artist = track.track.artist.name.casefold()

				for index, tr in pctl.master_library.items():
					if tr.title.casefold() == title and tr.artist.casefold() == artist:
						matches += 1
						logging.info("MATCH:")
						logging.info("     " + artist + " - " + title)
						star = star_store.full_get(index)
						if star is None:
							star = star_store.new_object()
						if "L" not in star[1]:
							updated += 1
							logging.info("     NEW LOVE")
							star[1] += "L"

						star_store.insert(index, star)

			self.scanning_loves = False
			if len(tracks) == 0:
				show_message(_("User has no loved tracks."))
				return
			if matches > 0 and updated == 0:
				show_message(_("{N} matched tracks are up to date.").format(N=str(matches)))
				return
			if matches > 0 and updated > 0:
				show_message(_("{N} tracks matched. {T} were updated.").format(N=str(matches), T=str(updated)))
				return
			show_message(_("Of {N} loved tracks, no matches were found in local db").format(N=str(len(tracks))))
			return
		except Exception:
			logging.exception("This doesn't seem to be working :(")
			show_message(_("This doesn't seem to be working :("), mode="error")
		self.scanning_loves = False

	def update(self, track_object: TrackClass) -> int | None:
		if not last_fm_enable:
			return None
		if prefs.scrobble_hold:
			return 0
		if prefs.auto_lfm:
			if self.connect(False) is False:
				prefs.auto_lfm = False
		else:
			return 0

		# logging.info('Updating Now Playing')

		title = track_object.title
		album = track_object.album
		artist = get_artist_strip_feat(track_object)

		try:
			if title != "" and artist != "":
				self.network.update_now_playing(
					artist=artist, title=title, album=album)
				return 0
			logging.error("Not sent, incomplete metadata")
			return 0
		except Exception as e:
			logging.exception("Error connecting to last.fm.")
			if "retry" in str(e):
				return 2
				# show_message(_("Could not update Last.fm. ", str(e), mode='warning')
			pctl.b_time -= 5000
			return 1

class ListenBrainz:

	def __init__(self, prefs: Prefs):

		self.enable = prefs.enable_lb
		# self.url = "https://api.listenbrainz.org/1/submit-listens"

	def url(self):
		url = prefs.listenbrainz_url
		if not url:
			url = "https://api.listenbrainz.org/"
		if not url.endswith("/"):
			url += "/"
		return url + "1/submit-listens"

	def listen_full(self, track_object: TrackClass, time) -> bool:

		if self.enable is False:
			return True
		if prefs.scrobble_hold is True:
			return True
		if prefs.lb_token is None:
			show_message(_("ListenBrainz is enabled but there is no token."), _("How did this even happen."), mode="error")

		title = track_object.title
		album = track_object.album
		artist = get_artist_strip_feat(track_object)

		if title == "" or artist == "":
			return True

		data = {"listen_type": "single", "payload": []}
		metadata = {"track_name": title, "artist_name": artist}

		additional = {}

		# MusicBrainz Artist IDs
		if "musicbrainz_artistids" in track_object.misc:
			additional["artist_mbids"] = track_object.misc["musicbrainz_artistids"]

		# MusicBrainz Release ID
		if "musicbrainz_albumid" in track_object.misc:
			additional["release_mbid"] = track_object.misc["musicbrainz_albumid"]

		# MusicBrainz Recording ID
		if "musicbrainz_recordingid" in track_object.misc:
			additional["recording_mbid"] = track_object.misc["musicbrainz_recordingid"]

		# MusicBrainz Track ID
		if "musicbrainz_trackid" in track_object.misc:
			additional["track_mbid"] = track_object.misc["musicbrainz_trackid"]

		if additional:
			metadata["additional_info"] = additional

		# logging.info(additional)
		data["payload"].append({"track_metadata": metadata})
		data["payload"][0]["listened_at"] = time

		r = requests.post(self.url(), headers={"Authorization": "Token " + prefs.lb_token}, data=json.dumps(data), timeout=10)
		if r.status_code != 200:
			show_message(_("There was an error submitting data to ListenBrainz"), r.text, mode="warning")
			return False
		return True

	def listen_playing(self, track_object: TrackClass) -> None:
		if self.enable is False:
			return
		if prefs.scrobble_hold is True:
			return
		if prefs.lb_token is None:
			show_message(_("ListenBrainz is enabled but there is no token."), _("How did this even happen."), mode="error")
		title = track_object.title
		album = track_object.album
		artist = get_artist_strip_feat(track_object)

		if title == "" or artist == "":
			return

		data = {"listen_type": "playing_now", "payload": []}
		metadata = {"track_name": title, "artist_name": artist}

		additional = {}

		# MusicBrainz Artist IDs
		if "musicbrainz_artistids" in track_object.misc:
			additional["artist_mbids"] = track_object.misc["musicbrainz_artistids"]

		# MusicBrainz Release ID
		if "musicbrainz_albumid" in track_object.misc:
			additional["release_mbid"] = track_object.misc["musicbrainz_albumid"]

		# MusicBrainz Recording ID
		if "musicbrainz_recordingid" in track_object.misc:
			additional["recording_mbid"] = track_object.misc["musicbrainz_recordingid"]

		# MusicBrainz Track ID
		if "musicbrainz_trackid" in track_object.misc:
			additional["track_mbid"] = track_object.misc["musicbrainz_trackid"]

		if track_object.track_number:
			try:
				additional["tracknumber"] = str(int(track_object.track_number))
			except Exception:
				logging.exception("Error trying to get track_number")

		if track_object.length:
			additional["duration"] = str(int(track_object.length))

		additional["media_player"] = t_title
		additional["submission_client"] = t_title
		additional["media_player_version"] = str(n_version)

		metadata["additional_info"] = additional
		data["payload"].append({"track_metadata": metadata})
		# data["payload"][0]["listened_at"] = int(time.time())

		r = requests.post(self.url(), headers={"Authorization": "Token " + prefs.lb_token}, data=json.dumps(data), timeout=10)
		if r.status_code != 200:
			show_message(_("There was an error submitting data to ListenBrainz"), r.text, mode="warning")
			logging.error("There was an error submitting data to ListenBrainz")
			logging.error(r.status_code)
			logging.error(r.json())

	def paste_key(self):

		text = copy_from_clipboard()
		if text == "":
			show_message(_("There is no text in the clipboard"), mode="error")
			return

		if prefs.listenbrainz_url:
			prefs.lb_token = text
			return

		if len(text) == 36 and text[8] == "-":
			prefs.lb_token = text
		else:
			show_message(_("That is not a valid token."), mode="error")

	def clear_key(self):

		prefs.lb_token = ""
		save_prefs()
		self.enable = False

class LastScrob:

	def __init__(self):

		self.a_index = -1
		self.a_sc = False
		self.a_pt = False
		self.queue = []
		self.running = False

	def start_queue(self):

		self.running = True
		mini_t = threading.Thread(target=self.process_queue)
		mini_t.daemon = True
		mini_t.start()

	def process_queue(self):

		time.sleep(0.4)

		while self.queue:

			try:
				tr = self.queue.pop()

				gui.pl_update = 1
				logging.info("Submit Scrobble " + tr[0].artist + " - " + tr[0].title)

				success = True

				if tr[2] == "lfm" and prefs.auto_lfm and (lastfm.connected or lastfm.details_ready()):
					success = lastfm.scrobble(tr[0], tr[1])
				elif tr[2] == "lb" and lb.enable:
					success = lb.listen_full(tr[0], tr[1])
				elif tr[2] == "maloja":
					success = maloja_scrobble(tr[0], tr[1])
				elif tr[2] == "air":
					success = subsonic.listen(tr[0], submit=True)
				elif tr[2] == "koel":
					success = koel.listen(tr[0], submit=True)

				if not success:
					logging.info("Re-queue scrobble")
					self.queue.append(tr)
					time.sleep(10)
					break

			except Exception:
				logging.exception("SCROBBLE QUEUE ERROR")

		if not self.queue:
			scrobble_warning_timer.force_set(1000)

		self.running = False

	def update(self, add_time):

		if pctl.queue_step > len(pctl.track_queue) - 1:
			logging.info("Queue step error 1")
			return

		if self.a_index != pctl.track_queue[pctl.queue_step]:
			pctl.a_time = 0
			pctl.b_time = 0
			self.a_index = pctl.track_queue[pctl.queue_step]
			self.a_pt = False
			self.a_sc = False
		if pctl.playing_time == 0 and self.a_sc is True:
			logging.info("Reset scrobble timer")
			pctl.a_time = 0
			pctl.b_time = 0
			self.a_pt = False
			self.a_sc = False

		if pctl.a_time > 6 and self.a_pt is False and pctl.master_library[self.a_index].length > 30:
			self.a_pt = True
			self.listen_track(pctl.master_library[self.a_index])
			# if prefs.auto_lfm and (lastfm.connected or lastfm.details_ready()) and not prefs.scrobble_hold:
			#	 mini_t = threading.Thread(target=lastfm.update, args=([pctl.master_library[self.a_index]]))
			#	 mini_t.daemon = True
			#	 mini_t.start()
			#
			# if lb.enable and not prefs.scrobble_hold:
			#	 mini_t = threading.Thread(target=lb.listen_playing, args=([pctl.master_library[self.a_index]]))
			#	 mini_t.daemon = True
			#	 mini_t.start()

		if pctl.a_time > 6 and self.a_pt:
			pctl.b_time += add_time
			if pctl.b_time > 20:
				pctl.b_time = 0
				self.listen_track(pctl.master_library[self.a_index])

		send_full = False
		if pctl.master_library[self.a_index].length > 30 and pctl.a_time > pctl.master_library[self.a_index].length \
				* 0.50 and self.a_sc is False:
			self.a_sc = True
			send_full = True

		if self.a_sc is False and pctl.master_library[self.a_index].length > 30 and pctl.a_time > 240:
			self.a_sc = True
			send_full = True

		if send_full:
			self.scrob_full_track(pctl.master_library[self.a_index])

	def listen_track(self, track_object: TrackClass):
		# logging.info("LISTEN")

		if track_object.is_network:
			if track_object.file_ext == "SUB":
				subsonic.listen(track_object, submit=False)

		if not prefs.scrobble_hold:
			if prefs.auto_lfm and (lastfm.connected or lastfm.details_ready()):
				mini_t = threading.Thread(target=lastfm.update, args=([track_object]))
				mini_t.daemon = True
				mini_t.start()

			if lb.enable:
				mini_t = threading.Thread(target=lb.listen_playing, args=([track_object]))
				mini_t.daemon = True
				mini_t.start()

	def scrob_full_track(self, track_object: TrackClass):
		# logging.info("SCROBBLE")
		track_object.lfm_scrobbles += 1
		gui.pl_update += 1

		if track_object.is_network:
			if track_object.file_ext == "SUB":
				self.queue.append((track_object, int(time.time()), "air"))
			if track_object.file_ext == "KOEL":
				self.queue.append((track_object, int(time.time()), "koel"))

		if not prefs.scrobble_hold:
			if prefs.auto_lfm and (lastfm.connected or lastfm.details_ready()):
				self.queue.append((track_object, int(time.time()), "lfm"))
			if lb.enable:
				self.queue.append((track_object, int(time.time()), "lb"))
			if prefs.maloja_url and prefs.maloja_enable:
				self.queue.append((track_object, int(time.time()), "maloja"))

class Strings:

	def __init__(self):
		self.spotify_likes = _("Spotify Likes")
		self.spotify_albums = _("Spotify Albums")
		self.spotify_un_liked = _("Track removed from liked tracks")
		self.spotify_already_un_liked = _("Track was already un-liked")
		self.spotify_already_liked = _("Track is already liked")
		self.spotify_like_added = _("Track added to liked tracks")
		self.spotify_account_connected = _("Spotify account connected")
		self.spotify_not_playing = _("This Spotify account isn't currently playing anything")
		self.spotify_error_starting = _("Error starting Spotify")
		self.spotify_request_auth = _("Please authorise Spotify in settings!")
		self.spotify_need_enable = _("Please authorise and click the enable toggle first!")
		self.spotify_import_complete = _("Spotify import complete")

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

	def __init__(self):
		self.master_count = 0
		self.chunks = {}
		self.header = None
		self.headers = []
		self.h2 = None

		self.clients = {}

class MenuIcon:

	def __init__(self, asset):
		self.asset = asset
		self.colour = [170, 170, 170, 255]
		self.base_asset = None
		self.base_asset_mod = None
		self.colour_callback = None
		self.mode_callback = None
		self.xoff = 0
		self.yoff = 0

class MenuItem:
	__slots__ = [
		"title",           # 0
		"is_sub_menu",     # 1
		"func",            # 2
		"render_func",     # 3
		"no_exit",         # 4
		"pass_ref",        # 5
		"hint",            # 6
		"icon",            # 7
		"show_test",       # 8
		"pass_ref_deco",   # 9
		"disable_test",    # 10
		"set_ref",         # 11
		"args",            # 12
		"sub_menu_number", # 13
		"sub_menu_width",  # 14
	]
	def __init__(
		self, title, func, render_func=None, no_exit=False, pass_ref=False, hint=None, icon=None, show_test=None,
		pass_ref_deco=False, disable_test=None, set_ref=None, is_sub_menu=False, args=None, sub_menu_number=None, sub_menu_width=0,
	):
		self.title = title
		self.is_sub_menu = is_sub_menu
		self.func = func
		self.render_func = render_func
		self.no_exit = no_exit
		self.pass_ref = pass_ref
		self.hint = hint
		self.icon = icon
		self.show_test = show_test
		self.pass_ref_deco = pass_ref_deco
		self.disable_test = disable_test
		self.set_ref = set_ref
		self.args = args
		self.sub_menu_number = sub_menu_number
		self.sub_menu_width = sub_menu_width

class ThreadManager:

	def __init__(self):

		self.worker1:  Thread | None = None  # Artist list, download monitor, folder move, importing, db cleaning, transcoding
		self.worker2:  Thread | None = None  # Art bg, search
		self.worker3:  Thread | None = None  # Gallery rendering
		self.playback: Thread | None = None
		self.player_lock:       Lock = threading.Lock()

		self.d: dict = {}

	def ready(self, type):
		if self.d[type][2] is None or not self.d[type][2].is_alive():
			shoot = threading.Thread(target=self.d[type][0], args=self.d[type][1])
			shoot.daemon = True
			shoot.start()
			self.d[type][2] = shoot

	def ready_playback(self) -> None:
		if self.playback is None or not self.playback.is_alive():
			if prefs.backend == 4:
				self.playback = threading.Thread(target=player4, args=[tauon])
			# elif prefs.backend == 2:
			#     from tauon.t_modules.t_gstreamer import player3
			#     self.playback = threading.Thread(target=player3, args=[tauon])
			self.playback.daemon = True
			self.playback.start()

	def check_playback_running(self) -> bool:
		if self.playback is None:
			return False
		return self.playback.is_alive()

class Menu:
	"""Right click context menu generator"""

	switch = 0
	count = switch + 1
	instances: list[Menu] = []
	active = False

	def rescale(self):
		self.vertical_size = round(self.base_v_size * gui.scale)
		self.h = self.vertical_size
		self.w = self.request_width * gui.scale
		if gui.scale == 2:
			self.w += 15

	def __init__(self, tauon: Tauon, width: int, show_icons: bool = False) -> None:
		self.tauon = tauon
		self.base_v_size = 22
		self.active = False
		self.request_width: int = width
		self.close_next_frame = False
		self.clicked = False
		self.pos = [0, 0]
		self.rescale()

		self.reference = 0
		self.items: list[MenuItem] = []
		self.subs: list[list[MenuItem]] = []
		self.selected = -1
		self.up = False
		self.down = False
		self.font = 412
		self.show_icons: bool = show_icons
		self.sub_arrow = MenuIcon(asset_loader(scaled_asset_directory, loaded_asset_dc, "sub.png", True))

		self.id = Menu.count
		self.break_height = round(4 * gui.scale)

		Menu.count += 1

		self.sub_number = 0
		self.sub_active = -1
		self.sub_y_postion = 0
		Menu.instances.append(self)

	@staticmethod
	def deco(_=_):
		return [colours.menu_text, colours.menu_background, None]

	def click(self) -> None:
		self.clicked = True
		# cheap hack to prevent scroll bar from being activated when closing menu
		global click_location
		click_location = [0, 0]

	def add(self, menu_item: MenuItem) -> None:
		if menu_item.render_func is None:
			menu_item.render_func = self.deco
		self.items.append(menu_item)

	def br(self) -> None:
		self.items.append(None)

	def add_sub(self, title: str, width: int, show_test=None) -> None:
		self.items.append(MenuItem(title, self.deco, sub_menu_width=width, show_test=show_test, is_sub_menu=True, sub_menu_number=self.sub_number))
		self.sub_number += 1
		self.subs.append([])

	def add_to_sub(self, sub_menu_index: int, menu_item: MenuItem) -> None:
		if menu_item.render_func is None:
			menu_item.render_func = self.deco
		self.subs[sub_menu_index].append(menu_item)

	def test_item_active(self, item):
		if item.show_test is not None:
			if item.show_test(1) is False:
				return False
		return True

	def is_item_disabled(self, item):
		if item.disable_test is not None:
			if item.pass_ref_deco:
				return item.disable_test(self.reference)
			return item.disable_test()

	def render_icon(self, x, y, icon, selected, fx):

		if colours.lm:
			selected = True

		if icon is not None:

			x += icon.xoff * gui.scale
			y += icon.yoff * gui.scale

			colour = None

			if icon.base_asset is None:
				# Colourise mode

				if icon.colour_callback is not None:  # and icon.colour_callback() is not None:
					colour = icon.colour_callback()

				elif selected and fx[0] != colours.menu_text_disabled:
					colour = icon.colour

				if colour is None and icon.base_asset_mod:
					colour = colours.menu_icons
					# if colours.lm:
					#	 colour = [160, 160, 160, 255]
					icon.base_asset_mod.render(x, y, colour)
					return

				if colour is None:
					# colour = [145, 145, 145, 70]
					colour = colours.menu_icons  # [255, 255, 255, 35]
					# colour = [50, 50, 50, 255]

				icon.asset.render(x, y, colour)

			else:
				if not is_grey(colours.menu_background):
					return  # Since these are currently pre-rendered greyscale, they are
					# Incompatible with coloured backgrounds. Fix TODO
				if selected and fx[0] == colours.menu_text_disabled:
					icon.base_asset.render(x, y)
					return

				# Pre-rendered mode
				if icon.mode_callback is not None:
					if icon.mode_callback():
						icon.asset.render(x, y)
					else:
						icon.base_asset.render(x, y)
				elif selected:
					icon.asset.render(x, y)
				else:
					icon.base_asset.render(x, y)

	def render(self):
		if self.active:

			if Menu.switch != self.id:
				self.active = False

				for menu in Menu.instances:
					if menu.active:
						break
				else:
					Menu.active = False

				return

			# ytoff = 3
			y_run = round(self.pos[1])
			to_call = None

			# if window_size[1] < 250 * gui.scale:
			#	 self.h = round(14 * gui.scale)
			#	 ytoff = -1 * gui.scale
			# else:
			self.h = self.vertical_size
			ytoff = round(self.h * 0.71 - 13 * gui.scale)

			x_run = self.pos[0]

			for i in range(len(self.items)):
				#logging.info(self.items[i])

				# Draw menu break
				if self.items[i] is None:

					if is_light(colours.menu_background):
						break_colour = rgb_add_hls(colours.menu_background, 0, -0.1, -0.1)
					else:
						break_colour = rgb_add_hls(colours.menu_background, 0, 0.06, 0)

					rect = (x_run, y_run, self.w, self.break_height - 1)
					if coll(rect):
						self.clicked = False

					ddt.rect_a((x_run, y_run), (self.w, self.break_height), colours.menu_background)

					ddt.rect_a((x_run, y_run + 2 * gui.scale), (self.w, 2 * gui.scale), break_colour)

					# Draw tab
					ddt.rect_a((x_run, y_run), (4 * gui.scale, self.break_height), colours.menu_tab)
					y_run += self.break_height

					continue

				if self.test_item_active(self.items[i]) is False:
					continue
				# if self.items[i][1] is False and self.items[i][8] is not None:
				#	 if self.items[i][8](1) == False:
				#		 continue

				# Get properties for menu item
				if self.items[i].render_func is not None:
					if self.items[i].pass_ref_deco:
						fx = self.items[i].render_func(self.reference)
					else:
						fx = self.items[i].render_func()
				else:
					fx = self.deco()

				if fx[2] is not None:
					label = fx[2]
				else:
					label = self.items[i].title

				# Show text as disabled if disable_test() passes
				if self.is_item_disabled(self.items[i]):
					fx[0] = colours.menu_text_disabled

				# Draw item background, black by default
				ddt.rect_a((x_run, y_run), (self.w, self.h), fx[1])
				bg = fx[1]

				# Detect if mouse is over this item
				selected = False
				rect = (x_run, y_run, self.w, self.h - 1)
				fields.add(rect)

				if coll_point(mouse_position, (x_run, y_run, self.w, self.h - 1)):
					ddt.rect_a((x_run, y_run), (self.w, self.h), colours.menu_highlight_background)  # [15, 15, 15, 255]
					selected = True
					bg = alpha_blend(colours.menu_highlight_background, bg)

					# Call menu items callback if clicked
					if self.clicked:

						if self.items[i].is_sub_menu is False:
							to_call = i
							if self.items[i].set_ref is not None:
								self.reference = self.items[i].set_ref
							global mouse_down
							mouse_down = False

						else:
							self.clicked = False
							self.sub_active = self.items[i].sub_menu_number
							self.sub_y_postion = y_run

				# Draw tab
				ddt.rect_a((x_run, y_run), (4 * gui.scale, self.h), colours.menu_tab)

				# Draw Icon
				x = 12 * gui.scale
				if self.items[i].is_sub_menu is False and self.show_icons:
					icon = self.items[i].icon
					self.render_icon(x_run + x, y_run + 5 * gui.scale, icon, selected, fx)

				if self.show_icons:
					x += 25 * gui.scale

				# Draw arrow icon for sub menu
				if self.items[i].is_sub_menu is True:

					if is_light(bg) or colours.lm:
						colour = rgb_add_hls(bg, 0, -0.6, -0.1)
					else:
						colour = rgb_add_hls(bg, 0, 0.1, 0)

					if self.sub_active == self.items[i].func:
						if is_light(bg) or colours.lm:
							colour = rgb_add_hls(bg, 0, -0.8, -0.1)
						else:
							colour = rgb_add_hls(bg, 0, 0.40, 0)

					# colour = [50, 50, 50, 255]
					# if selected:
					#	 colour = [150, 150, 150, 255]
					# if self.sub_active == self.items[i][2]:
					#	 colour = [150, 150, 150, 255]
					self.sub_arrow.asset.render(x_run + self.w - 13 * gui.scale, y_run + 7 * gui.scale, colour)

				# Render the items label
				ddt.text((x_run + x, y_run + ytoff), label, fx[0], self.font, max_w=self.w - (x + 9 * gui.scale), bg=bg)

				# Render the items hint
				if self.items[i].hint != None:

					if is_light(bg) or colours.lm:
						hint_colour = rgb_add_hls(bg, 0, -0.30, -0.3)
					else:
						hint_colour = rgb_add_hls(bg, 0, 0.15, 0)

					# colo = alpha_blend([255, 255, 255, 50], bg)
					ddt.text((x_run + self.w - 5, y_run + ytoff, 1), self.items[i].hint, hint_colour, self.font, bg=bg)

				y_run += self.h

				if y_run > window_size[1] - self.h:
					direc = 1
					if self.pos[0] > window_size[0] // 2:
						direc = -1
					x_run += self.w * direc
					y_run = self.pos[1]

				# Render sub menu if active
				if self.sub_active > -1 and self.items[i].is_sub_menu and self.sub_active == self.items[i].sub_menu_number:

					# sub_pos = [x_run + self.w, self.pos[1] + i * self.h]
					sub_pos = [x_run + self.w, self.sub_y_postion]
					sub_w = self.items[i].sub_menu_width * gui.scale

					if sub_pos[0] + sub_w > window_size[0]:
						sub_pos[0] = x_run - sub_w
						if view_box.active:
							sub_pos[0] -= view_box.w

					fx = self.deco()

					minY = window_size[1] - self.h * len(self.subs[self.sub_active]) - 15 * gui.scale
					sub_pos[1] = min(sub_pos[1], minY)

					xoff = 0
					for i in self.subs[self.sub_active]:
						if i.icon is not None:
							xoff = 24 * gui.scale
							break

					for w in range(len(self.subs[self.sub_active])):

						if self.subs[self.sub_active][w].show_test is not None:
							if not self.subs[self.sub_active][w].show_test(self.reference):
								continue

						# Get item colours
						if self.subs[self.sub_active][w].render_func is not None:
							if self.subs[self.sub_active][w].pass_ref_deco:
								fx = self.subs[self.sub_active][w].render_func(self.reference)
							else:
								fx = self.subs[self.sub_active][w].render_func()

						# Item background
						ddt.rect_a((sub_pos[0], sub_pos[1] + w * self.h), (sub_w, self.h), fx[1])

						# Detect if mouse is over this item
						rect = (sub_pos[0], sub_pos[1] + w * self.h, sub_w, self.h - 1)
						fields.add(rect)
						this_select = False
						bg = colours.menu_background
						if coll_point(mouse_position, (sub_pos[0], sub_pos[1] + w * self.h, sub_w, self.h - 1)):
							ddt.rect_a((sub_pos[0], sub_pos[1] + w * self.h), (sub_w, self.h), colours.menu_highlight_background)
							bg = alpha_blend(colours.menu_highlight_background, bg)
							this_select = True

							# Call Callback
							if self.clicked and not self.is_item_disabled(self.subs[self.sub_active][w]):

								# If callback needs args
								if self.subs[self.sub_active][w].args is not None:
									self.subs[self.sub_active][w].func(self.reference, self.subs[self.sub_active][w].args)

								# If callback just need ref
								elif self.subs[self.sub_active][w].pass_ref:
									self.subs[self.sub_active][w].func(self.reference)

								else:
									self.subs[self.sub_active][w].func()

						if fx[2] is not None:
							label = fx[2]
						else:
							label = self.subs[self.sub_active][w].title

						# Show text as disabled if disable_test() passes
						if self.is_item_disabled(self.subs[self.sub_active][w]):
							fx[0] = colours.menu_text_disabled

						# Render sub items icon
						icon = self.subs[self.sub_active][w].icon
						self.render_icon(sub_pos[0] + 11 * gui.scale, sub_pos[1] + w * self.h + 5 * gui.scale, icon, this_select, fx)

						# Render the items label
						ddt.text(
							(sub_pos[0] + 10 * gui.scale + xoff, sub_pos[1] + ytoff + w * self.h), label, fx[0], self.font, bg=bg)

						# Draw tab
						ddt.rect_a((sub_pos[0], sub_pos[1] + w * self.h), (4 * gui.scale, self.h), colours.menu_tab)

						# Render the menu outline
						# ddt.rect_a(sub_pos, (sub_w, self.h * len(self.subs[self.sub_active])), colours.grey(40))

			# Process Click Actions
			if to_call is not None:

				if not self.is_item_disabled(self.items[to_call]):
					if self.items[to_call].pass_ref:
						self.items[to_call].func(self.reference)
					else:
						self.items[to_call].func()

			if self.clicked or key_esc_press or self.close_next_frame:
				self.close_next_frame = False
				self.active = False
				self.clicked = False

				last_click_location[0] = 0
				last_click_location[1] = 0

				for menu in Menu.instances:
					if menu.active:
						break
				else:
					Menu.active = False

				# Render the menu outline
				# ddt.rect_a(self.pos, (self.w, self.h * len(self.items)), colours.grey(40))

	def activate(self, in_reference=0, position=None):

		Menu.active = True

		if position != None:
			self.pos = [position[0], position[1]]
		else:
			self.pos = [copy.deepcopy(mouse_position[0]), copy.deepcopy(mouse_position[1])]

		self.reference = in_reference
		Menu.switch = self.id
		self.sub_active = -1

		# Reposition the menu if it would otherwise intersect with far edge of window
		if not position:
			if self.pos[0] + self.w > window_size[0]:
				self.pos[0] -= round(self.w + 3 * gui.scale)

		# Get height size of menu
		full_h = 0
		shown_h = 0
		for item in self.items:
			if item is None:
				full_h += self.break_height
				shown_h += self.break_height
			else:
				full_h += self.h
				if self.test_item_active(item) is True:
					shown_h += self.h

		# Flip menu up if would intersect with bottom of window
		if self.pos[1] + full_h > window_size[1]:
			self.pos[1] -= shown_h

			# Prevent moving outside top of window
			if self.pos[1] < gui.panelY:
				self.pos[1] = gui.panelY
				self.pos[0] += 5 * gui.scale

		self.active = True

class GallClass:
	def __init__(self, size=250, save_out=True):
		self.gall = {}
		self.size = size
		self.queue = []
		self.key_list = []
		self.save_out = save_out
		self.i = 0
		self.lock = threading.Lock()
		self.limit = 60

	def get_file_source(self, track_object: TrackClass):

		global album_art_gen

		sources = album_art_gen.get_sources(track_object)

		if len(sources) == 0:
			return False, 0

		offset = album_art_gen.get_offset(track_object.fullpath, sources)
		return sources[offset], offset

	def worker_render(self):

		self.lock.acquire()
		# time.sleep(0.1)

		if search_over.active:
			while QuickThumbnail.queue:
				img = QuickThumbnail.queue.pop(0)
				response = urllib.request.urlopen(img.url, context=ssl_context)
				source_image = io.BytesIO(response.read())
				img.read_and_thumbnail(source_image, img.size, img.size)
				source_image.close()
				gui.update += 1

		while len(self.queue) > 0:

			source_image = None

			if gui.halt_image_rendering:
				self.queue.clear()
				break

			self.i += 1

			try:
				# key = self.queue[0]
				key = self.queue.pop(0)
			except Exception:
				logging.exception("thumb queue empty")
				break

			if key not in self.gall:
				order = [1, None, None, None]
				self.gall[key] = order
			else:
				order = self.gall[key]

			size = key[1]

			slow_load = False
			cache_load = False

			try:

				if True:
					offset = 0
					parent_folder = key[0].parent_folder_path
					if parent_folder in folder_image_offsets:
						offset = folder_image_offsets[parent_folder]
					img_name = str(key[2]) + "-" + str(size) + "-" + str(key[0].index) + "-" + str(offset)
					if prefs.cache_gallery and os.path.isfile(os.path.join(g_cache_dir, img_name + ".jpg")):
						source_image = open(os.path.join(g_cache_dir, img_name + ".jpg"), "rb")
						# logging.info('load from cache')
						cache_load = True
					else:
						slow_load = True

				if slow_load:

					source, c_offset = self.get_file_source(key[0])

					if source is False:
						order[0] = 0
						self.gall[key] = order
						# del self.queue[0]
						continue

					img_name = str(key[2]) + "-" + str(size) + "-" + str(key[0].index) + "-" + str(c_offset)

					# gall_render_last_timer.set()

					if prefs.cache_gallery and os.path.isfile(os.path.join(g_cache_dir, img_name + ".jpg")):
						source_image = open(os.path.join(g_cache_dir, img_name + ".jpg"), "rb")
						logging.info("slow load image")
						cache_load = True

					# elif source[0] == 1:
					#	 #logging.info('tag')
					#	 source_image = io.BytesIO(album_art_gen.get_embed(key[0]))
					#
					# elif source[0] == 2:
					#	 try:
					#		 url = get_network_thumbnail_url(key[0])
					#		 response = urllib.request.urlopen(url)
					#		 source_image = response
					#	 except Exception:
					#		 logging.exception("IMAGE NETWORK LOAD ERROR")
					# else:
					#	 source_image = open(source[1], 'rb')
					source_image = album_art_gen.get_source_raw(0, 0, key[0], subsource=source)

				g = io.BytesIO()
				g.seek(0)

				if cache_load:
					g.write(source_image.read())

				else:
					error = False
					try:
						# Process image
						im = Image.open(source_image)
						if im.mode != "RGB":
							im = im.convert("RGB")
						im.thumbnail((size, size), Image.Resampling.LANCZOS)
					except Exception:
						logging.exception("Failed to work with thumbnail")
						im = album_art_gen.get_error_img(size)
						error = True

					im.save(g, "BMP")

					if not error and self.save_out and prefs.cache_gallery and not os.path.isfile(
							os.path.join(g_cache_dir, img_name + ".jpg")):
						im.save(os.path.join(g_cache_dir, img_name + ".jpg"), "JPEG", quality=95)

				g.seek(0)

				# source_image.close()

				order = [2, g, None, None]
				self.gall[key] = order

				gui.update += 1
				if source_image:
					source_image.close()
					source_image = None
				# del self.queue[0]

				time.sleep(0.001)

			except Exception:
				logging.exception("Image load failed on track: " + key[0].fullpath)
				order = [0, None, None, None]
				self.gall[key] = order
				gui.update += 1
				# del self.queue[0]

			if size < 150:
				random.shuffle(self.queue)

		if self.i > 0:
			self.i = 0
			return True
		return False

	def render(self, track: TrackClass, location, size=None, force_offset=None) -> bool | None:
		if gallery_load_delay.get() < 0.5:
			return None

		x = round(location[0])
		y = round(location[1])

		# time.sleep(0.1)
		if size is None:
			size = self.size

		size = round(size)

		# offset = self.get_offset(pctl.master_library[index].fullpath, self.get_sources(index))
		if track.parent_folder_path in folder_image_offsets:
			offset = folder_image_offsets[track.parent_folder_path]
		else:
			offset = 0

		if force_offset is not None:
			offset = force_offset

		key = (track, size, offset)

		if key in self.gall:
			#logging.info("old")

			order = self.gall[key]

			if order[0] == 0:
				# broken
				return False

			if order[0] == 1:
				# not done yet
				return False

			if order[0] == 2:
				# finish processing

				wop = rw_from_object(order[1])
				s_image = IMG_Load_RW(wop, 0)
				c = SDL_CreateTextureFromSurface(renderer, s_image)
				SDL_FreeSurface(s_image)
				tex_w = pointer(c_int(size))
				tex_h = pointer(c_int(size))
				SDL_QueryTexture(c, None, None, tex_w, tex_h)
				dst = SDL_Rect(x, y)
				dst.w = int(tex_w.contents.value)
				dst.h = int(tex_h.contents.value)


				order[0] = 3
				order[1].close()
				order[1] = None
				order[2] = c
				order[3] = dst
				self.gall[(track, size, offset)] = order

			if order[0] == 3:
				# ready

				order[3].x = x
				order[3].y = y
				order[3].x = int((size - order[3].w) / 2) + order[3].x
				order[3].y = int((size - order[3].h) / 2) + order[3].y
				SDL_RenderCopy(renderer, order[2], None, order[3])

				if (track, size, offset) in self.key_list:
					self.key_list.remove((track, size, offset))
				self.key_list.append((track, size, offset))

				# Remove old images to conserve RAM usage
				if len(self.key_list) > self.limit:
					gui.update += 1
					key = self.key_list[0]
					# while key in self.queue:
					#	 self.queue.remove(key)
					if self.gall[key][2] is not None:
						SDL_DestroyTexture(self.gall[key][2])
					del self.gall[key]
					del self.key_list[0]

				return True

		else:
			if key not in self.queue:
				self.queue.append(key)
				if self.lock.locked():
					try:
						self.lock.release()
					except RuntimeError as e:
						if str(e) == "release unlocked lock":
							logging.error("RuntimeError: Attempted to release already unlocked lock")
						else:
							logging.exception("Unknown RuntimeError trying to release lock")
					except Exception:
						logging.exception("Unknown error trying to release lock")
		return False

class ThumbTracks:
	def __init__(self) -> None:
		pass

	def path(self, track: TrackClass) -> str:
		source, offset = tauon.gall_ren.get_file_source(track)

		if source is False:  # No art
			return None

		image_name = track.album + track.parent_folder_path + str(offset)
		image_name = hashlib.md5(image_name.encode("utf-8", "replace")).hexdigest()

		t_path = os.path.join(e_cache_dir, image_name + ".jpg")

		if os.path.isfile(t_path):
			return t_path

		source_image = album_art_gen.get_source_raw(0, 0, track, subsource=source)

		with Image.open(source_image) as im:
			if im.mode != "RGB":
				im = im.convert("RGB")
			im.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
			im.save(t_path, "JPEG")
		source_image.close()
		return t_path

class Tauon:
	"""Root class for everything Tauon"""
	def __init__(self, holder: Holder):

		self.t_title = holder.t_title
		self.t_version = holder.t_version
		self.t_agent = holder.t_agent
		self.t_id = holder.t_id
		self.desktop: str | None = desktop
		self.device = socket.gethostname()

		#TODO(Martin) : Fix this by moving the class to root of the module
		self.cachement: player4.Cachement | None = None
		self.dummy_event: SDL_Event = SDL_Event()
		self.translate = _
		self.strings: Strings = strings
		self.pctl:  PlayerCtl = pctl
		self.lfm_scrobbler: LastScrob = lfm_scrobbler
		self.star_store:    StarStore = star_store
		self.gui:  GuiVar = gui
		self.prefs: Prefs = prefs
		self.cache_directory:          Path = cache_directory
		self.user_directory:    Path | None = user_directory
		self.music_directory:   Path | None = music_directory
		self.locale_directory:         Path = locale_directory
		self.worker_save_state:        bool = False
		self.launch_prefix:             str = launch_prefix
		self.whicher = whicher
		self.load_orders: list[LoadClass] = load_orders
		self.switch_playlist = None
		self.open_uri = open_uri
		self.love = love
		self.snap_mode = snap_mode
		self.console = console
		self.msys = msys
		self.TrackClass = TrackClass
		self.pl_gen = pl_gen
		self.gall_ren = GallClass(album_mode_art_size)
		self.QuickThumbnail = QuickThumbnail
		self.thumb_tracks = ThumbTracks()
		self.pl_to_id = pl_to_id
		self.id_to_pl = id_to_pl
		self.chunker = Chunker()
		self.thread_manager: ThreadManager = ThreadManager()
		self.stream_proxy = None
		self.stream_proxy = StreamEnc(self)
		self.level_train: list[list[float]] = []
		self.radio_server = None
		self.mod_formats = MOD_Formats
		self.listen_alongers = {}
		self.encode_folder_name = encode_folder_name
		self.encode_track_name = encode_track_name

		self.tray_lock = threading.Lock()
		self.tray_releases = 0

		self.play_lock = None
		self.update_play_lock = None
		self.sleep_lock = None
		self.shutdown_lock = None
		self.quick_close = False

		self.copied_track = None
		self.macos = macos
		self.aud: CDLL | None = None

		self.recorded_songs = []

		self.chrome_mode = False
		self.web_running = False
		self.web_thread = None
		self.remote_limited = True
		self.enable_librespot = shutil.which("librespot")

		#TODO(Martin) : Fix this by moving the class to root of the module
		self.spotc: player4.LibreSpot | None = None
		self.librespot_p = None
		self.MenuItem = MenuItem
		self.tag_scan = tag_scan

		self.gme_formats = GME_Formats

		self.spot_ctl: SpotCtl = SpotCtl(self)
		self.tidal: Tidal = Tidal(self)
		self.chrome: Chrome | None = None
		self.chrome_menu: Menu | None = None

		self.ssl_context = ssl_context

	def start_remote(self) -> None:

		if not self.web_running:
			self.web_thread = threading.Thread(
				target=webserve2, args=[pctl, prefs, gui, album_art_gen, str(install_directory), strings, tauon])
			self.web_thread.daemon = True
			self.web_thread.start()
			self.web_running = True

	def download_ffmpeg(self, x):
		def go():
			url = "https://github.com/GyanD/codexffmpeg/releases/download/5.0.1/ffmpeg-5.0.1-essentials_build.zip"
			sha = "9e00da9100ae1bba22b1385705837392e8abcdfd2efc5768d447890d101451b5"
			show_message(_("Starting download..."))
			try:
				f = io.BytesIO()
				r = requests.get(url, stream=True, timeout=1800) # ffmpeg is 77MB, give it half an hour in case someone is willing to suffer it on a slow connection

				dl = 0
				for data in r.iter_content(chunk_size=4096):
					dl += len(data)
					f.write(data)
					mb = round(dl / 1000 / 1000)
					if mb > 90:
						break
					if mb % 5 == 0:
						show_message(_("Downloading... {N}/80MB").format(N=mb))

			except Exception as e:
				logging.exception("Download failed")
				show_message(_("Download failed"), str(e), mode="error")

			f.seek(0)
			if hashlib.sha256(f.read()).hexdigest() != sha:
				show_message(_("Download completed but checksum failed"), mode="error")
				return
			show_message(_("Download completed.. extracting"))
			f.seek(0)
			z = zipfile.ZipFile(f, mode="r")
			exe = z.open("ffmpeg-5.0.1-essentials_build/bin/ffmpeg.exe")
			with (user_directory / "ffmpeg.exe").open("wb") as file:
				file.write(exe.read())

			exe = z.open("ffmpeg-5.0.1-essentials_build/bin/ffprobe.exe")
			with (user_directory / "ffprobe.exe").open("wb") as file:
				file.write(exe.read())

			exe.close()
			show_message(_("FFMPEG fetch complete"), mode="done")

		shooter(go)

	def set_tray_icons(self, force: bool = False):

		indicator_icon_play =    str(pctl.install_directory / "assets/svg/tray-indicator-play.svg")
		indicator_icon_pause =   str(pctl.install_directory / "assets/svg/tray-indicator-pause.svg")
		indicator_icon_default = str(pctl.install_directory / "assets/svg/tray-indicator-default.svg")

		if prefs.tray_theme == "gray":
			indicator_icon_play =    str(pctl.install_directory / "assets/svg/tray-indicator-play-g1.svg")
			indicator_icon_pause =   str(pctl.install_directory / "assets/svg/tray-indicator-pause-g1.svg")
			indicator_icon_default = str(pctl.install_directory / "assets/svg/tray-indicator-default-g1.svg")

		user_icon_dir = self.cache_directory / "icon-export"
		def install_tray_icon(src: str, name: str) -> None:
			alt = user_icon_dir / f"{name}.svg"
			if not alt.is_file() or force:
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
		if msys:
			show_message(_("This feature requires FFMPEG. Shall I can download that for you? (80MB)"), mode="confirm")
			gui.message_box_confirm_callback = self.download_ffmpeg
			gui.message_box_confirm_reference = (None,)
		else:
			show_message(_("FFMPEG could not be found"))
		return False

	def get_ffmpeg(self) -> str | None:
		logging.debug(f"Looking for ffmpeg in PATH: {os.environ.get('PATH')}")
		p = shutil.which("ffmpeg")
		if p:
			return p
		p = str(user_directory / "ffmpeg.exe")
		if msys and os.path.isfile(p):
			return p
		return None

	def get_ffprobe(self) -> str | None:
		p = shutil.which("ffprobe")
		if p:
			return p
		p = str(user_directory / "ffprobe.exe")
		if msys and os.path.isfile(p):
			return p
		return None

	def bg_save(self) -> None:
		self.worker_save_state = True
		tauon.thread_manager.ready("worker")

	def exit(self, reason: str) -> None:
		logging.info("Shutting down. Reason: " + reason)
		pctl.running = False
		self.wake()

	def min_to_tray(self) -> None:
		SDL_HideWindow(t_window)
		gui.mouse_unknown = True

	def raise_window(self) -> None:
		SDL_ShowWindow(t_window)
		SDL_RaiseWindow(t_window)
		SDL_RestoreWindow(t_window)
		gui.lowered = False
		gui.update += 1

	def focus_window(self) -> None:
		SDL_RaiseWindow(t_window)

	def get_playing_playlist_id(self) -> int:
		return pl_to_id(pctl.active_playlist_playing)

	def wake(self) -> None:
		SDL_PushEvent(ctypes.byref(self.dummy_event))

class PlexService:

	def __init__(self):
		self.connected = False
		self.resource = None
		self.scanning = False

	def connect(self):

		if not prefs.plex_username or not prefs.plex_password or not prefs.plex_servername:
			show_message(_("Missing username, password and/or server name"), mode="warning")
			self.scanning = False
			return

		try:
			from plexapi.myplex import MyPlexAccount
		except ModuleNotFoundError:
			logging.warning("Unable to import python-plexapi, plex support will be disabled.")
		except Exception:
			logging.exception("Unknown error to import python-plexapi, plex support will be disabled.")
			show_message(_("Error importing python-plexapi"), mode="error")
			self.scanning = False
			return

		try:
			account = MyPlexAccount(prefs.plex_username, prefs.plex_password)
			self.resource = account.resource(prefs.plex_servername).connect()  # returns a PlexServer instance
		except Exception:
			logging.exception("Error connecting to PLEX server, check login credentials and server accessibility.")
			show_message(
				_("Error connecting to PLEX server"),
				_("Try checking login credentials and that the server is accessible."), mode="error")
			self.scanning = False
			return

		# from plexapi.server import PlexServer
		# baseurl = 'http://localhost:32400'
		# token = ''

		# self.resource = PlexServer(baseurl, token)

		self.connected = True

	def resolve_stream(self, location):
		logging.info("Get plex stream")
		if not self.connected:
			self.connect()

		# return self.resource.url(location, True)
		return self.resource.library.fetchItem(location).getStreamURL()

	def resolve_thumbnail(self, location):

		if not self.connected:
			self.connect()
		if self.connected:
			return self.resource.url(location, True)
		return None

	def get_albums(self, return_list=False):

		gui.update += 1
		self.scanning = True

		if not self.connected:
			self.connect()

		if not self.connected:
			self.scanning = False
			return []

		playlist = []

		existing = {}
		for track_id, track in pctl.master_library.items():
			if track.is_network and track.file_ext == "PLEX":
				existing[track.url_key] = track_id

		albums = self.resource.library.section("Music").albums()
		gui.to_got = 0

		for album in albums:
			year = album.year
			album_artist = album.parentTitle
			album_title = album.title

			parent = (album_artist + " - " + album_title).strip("- ")

			for track in album.tracks():

				if not track.duration:
					logging.warning("Skipping track with invalid duration - " + track.title + " - " + track.grandparentTitle)
					continue

				id = pctl.master_count
				replace_existing = False

				e = existing.get(track.key)
				if e is not None:
					id = e
					replace_existing = True

				title = track.title
				track_artist = track.grandparentTitle
				duration = track.duration / 1000

				nt = TrackClass()
				nt.index = id
				nt.track_number = track.index
				nt.file_ext = "PLEX"
				nt.parent_folder_path = parent
				nt.parent_folder_name = parent
				nt.album_artist = album_artist
				nt.artist = track_artist
				nt.title = title
				nt.album = album_title
				nt.length = duration
				if hasattr(track, "locations") and track.locations:
					nt.fullpath = track.locations[0]

				nt.is_network = True

				if track.thumb:
					nt.art_url_key = track.thumb

				nt.url_key = track.key
				nt.date = str(year)

				pctl.master_library[id] = nt

				if not replace_existing:
					pctl.master_count += 1

				playlist.append(nt.index)

			gui.to_got += 1
			gui.update += 1
			gui.pl_update += 1

		self.scanning = False

		if return_list:
			return playlist

		pctl.multi_playlist.append(pl_gen(title=_("PLEX Collection"), playlist_ids=playlist))
		pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "plex path"
		switch_playlist(len(pctl.multi_playlist) - 1)

class SubsonicService:

	def __init__(self):
		self.scanning = False
		self.playlists = prefs.subsonic_playlists

	def r(self, point, p=None, binary: bool = False, get_url: bool = False):
		salt = secrets.token_hex(8)
		server = prefs.subsonic_server.rstrip("/") + "/"

		params = {
			"u": prefs.subsonic_user,
			"v": "1.13.0",
			"c": t_title,
			"f": "json",
		}

		if prefs.subsonic_password_plain:
			params["p"] = prefs.subsonic_password
		else:
			params["t"] = hashlib.md5((prefs.subsonic_password + salt).encode()).hexdigest()
			params["s"] = salt

		if p:
			params.update(p)

		point = "rest/" + point

		url = server + point

		if get_url:
			return url, params

		response = requests.get(url, params=params, timeout=10)

		if binary:
			return response.content

		d = json.loads(response.text)
		# logging.info(d)

		if d["subsonic-response"]["status"] != "ok":
			show_message(_("Subsonic Error: ") + response.text, mode="warning")
			logging.error("Subsonic Error: " + response.text)

		return d

	def get_cover(self, track_object: TrackClass):
		response = self.r("getCoverArt", p={"id": track_object.art_url_key}, binary=True)
		return io.BytesIO(response)

	def resolve_stream(self, key):

		p = {"id": key}
		if prefs.network_stream_bitrate > 0:
			p["maxBitRate"] = prefs.network_stream_bitrate

		return self.r("stream", p={"id": key}, get_url=True)
		# logging.info(response.content)

	def listen(self, track_object: TrackClass, submit: bool = False):

		try:
			a = self.r("scrobble", p={"id": track_object.url_key, "submission": submit})
		except Exception:
			logging.exception("Error connecting for scrobble on airsonic")
		return True

	def set_rating(self, track_object: TrackClass, rating):

		try:
			a = self.r("setRating", p={"id": track_object.url_key, "rating": math.ceil(rating / 2)})
		except Exception:
			logging.exception("Error connect for set rating on airsonic")
		return True

	def set_album_rating(self, track_object: TrackClass, rating):
		id = track_object.misc.get("subsonic-folder-id")
		if id is not None:
			try:
				a = self.r("setRating", p={"id": id, "rating": math.ceil(rating / 2)})
			except Exception:
				logging.exception("Error connect for set rating on airsonic")
		return True

	def get_music3(self, return_list: bool = False):

		self.scanning = True
		gui.to_got = 0

		existing = {}

		for track_id, track in pctl.master_library.items():
			if track.is_network and track.file_ext == "SUB":
				existing[track.url_key] = track_id

		try:
			a = self.r("getIndexes")
		except Exception:
			logging.exception("Error connecting to Airsonic server")
			show_message(_("Error connecting to Airsonic server"), mode="error")
			self.scanning = False
			return []

		b = a["subsonic-response"]["indexes"]["index"]

		folders = []

		for letter in b:
			artists = letter["artist"]
			for artist in artists:
				folders.append((
					artist["id"],
					artist["name"],
				))

		playlist = []

		songsets = []
		for i in range(len(folders)):
			songsets.append([])
		statuses = [0] * len(folders)
		dupes = []

		def getsongs(index, folder_id, name: str, inner: bool = False, parent=None):

			try:
				d = self.r("getMusicDirectory", p={"id": folder_id})
				if "child" not in d["subsonic-response"]["directory"]:
					if not inner:
						statuses[index] = 2
					return

			except json.decoder.JSONDecodeError:
				logging.exception("Error reading Airsonic directory")
				if not inner:
					statuses[index] = 2
				show_message(_("Error reading Airsonic directory!"), mode="warning")
				return
			except Exception:
				logging.exception("Unknown Error reading Airsonic directory")

			items = d["subsonic-response"]["directory"]["child"]

			gui.update = 2

			for item in items:

				if item["isDir"]:

					if "userRating" in item and "artist" in item:
						rating = item["userRating"]
						if album_star_store.get_rating_artist_title(item["artist"], item["title"]) == 0 and rating == 0:
							pass
						else:
							album_star_store.set_rating_artist_title(item["artist"], item["title"], int(rating * 2))

					getsongs(index, item["id"], item["title"], inner=True, parent=item)
					continue

				gui.to_got += 1
				song = item
				nt = TrackClass()

				if parent and "artist" in parent:
					nt.album_artist = parent["artist"]

				if "title" in song:
					nt.title = song["title"]
				if "artist" in song:
					nt.artist = song["artist"]
				if "album" in song:
					nt.album = song["album"]
				if "track" in song:
					nt.track_number = song["track"]
				if "year" in song:
					nt.date = str(song["year"])
				if "duration" in song:
					nt.length = song["duration"]

				nt.file_ext = "SUB"
				nt.parent_folder_name = name
				if "path" in song:
					nt.fullpath = song["path"]
					nt.parent_folder_path = os.path.dirname(song["path"])
				if "coverArt" in song:
					nt.art_url_key = song["id"]
				nt.url_key = song["id"]
				nt.misc["subsonic-folder-id"] = folder_id
				nt.is_network = True

				rating = 0
				if "userRating" in song:
					rating = int(song["userRating"])

				songsets[index].append((nt, name, song["id"], rating))

			if inner:
				return
			statuses[index] = 2

		i = -1
		for id, name in folders:
			i += 1
			while statuses.count(1) > 3:
				time.sleep(0.1)

			statuses[i] = 1
			t = threading.Thread(target=getsongs, args=([i, id, name]))
			t.daemon = True
			t.start()

		while statuses.count(2) != len(statuses):
			time.sleep(0.1)

		for sset in songsets:
			for nt, name, song_id, rating in sset:

				id = pctl.master_count

				replace_existing = False
				ex = existing.get(song_id)
				if ex is not None:
					id = ex
					replace_existing = True

				nt.index = id
				pctl.master_library[id] = nt
				if not replace_existing:
					pctl.master_count += 1

				playlist.append(nt.index)

				if star_store.get_rating(nt.index) == 0 and rating == 0:
					pass
				else:
					star_store.set_rating(nt.index, rating * 2)

		self.scanning = False
		if return_list:
			return playlist

		pctl.multi_playlist.append(pl_gen(title=_("Airsonic Collection"), playlist_ids=playlist))
		pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "air"
		switch_playlist(len(pctl.multi_playlist) - 1)

	# def get_music2(self, return_list=False):
	#
	#	 self.scanning = True
	#	 gui.to_got = 0
	#
	#	 existing = {}
	#
	#	 for track_id, track in pctl.master_library.items():
	#		 if track.is_network and track.file_ext == "SUB":
	#			 existing[track.url_key] = track_id
	#
	#	 try:
	#		 a = self.r("getIndexes")
	#	 except Exception:
	#		 show_message(_("Error connecting to Airsonic server"), mode="error")
	#		 self.scanning = False
	#		 return []
	#
	#	 b = a["subsonic-response"]["indexes"]["index"]
	#
	#	 folders = []
	#
	#	 for letter in b:
	#		 artists = letter["artist"]
	#		 for artist in artists:
	#			 folders.append((
	#				 artist["id"],
	#				 artist["name"]
	#			 ))
	#
	#	 playlist = []
	#
	#	 def get(folder_id, name):
	#
	#		 try:
	#			 d = self.r("getMusicDirectory", p={"id": folder_id})
	#			 if "child" not in d["subsonic-response"]["directory"]:
	#				 return
	#
	#		 except json.decoder.JSONDecodeError:
	#			 logging.error("Error reading Airsonic directory")
	#			 show_message(_("Error reading Airsonic directory!)", mode="warning")
	#			 return
	#
	#		 items = d["subsonic-response"]["directory"]["child"]
	#
	#		 gui.update = 1
	#
	#		 for item in items:
	#
	#			 gui.to_got += 1
	#
	#			 if item["isDir"]:
	#				 get(item["id"], item["title"])
	#				 continue
	#
	#			 song = item
	#			 id = pctl.master_count
	#
	#			 replace_existing = False
	#			 ex = existing.get(song["id"])
	#			 if ex is not None:
	#				 id = ex
	#				 replace_existing = True
	#
	#			 nt = TrackClass()
	#
	#			 if "title" in song:
	#				 nt.title = song["title"]
	#			 if "artist" in song:
	#				 nt.artist = song["artist"]
	#			 if "album" in song:
	#				 nt.album = song["album"]
	#			 if "track" in song:
	#				 nt.track_number = song["track"]
	#			 if "year" in song:
	#				 nt.date = str(song["year"])
	#			 if "duration" in song:
	#				 nt.length = song["duration"]
	#
	#			 # if "bitRate" in song:
	#			 #	 nt.bitrate = song["bitRate"]
	#
	#			 nt.file_ext = "SUB"
	#
	#			 nt.index = id
	#
	#			 nt.parent_folder_name = name
	#			 if "path" in song:
	#				 nt.fullpath = song["path"]
	#				 nt.parent_folder_path = os.path.dirname(song["path"])
	#
	#			 if "coverArt" in song:
	#				 nt.art_url_key = song["id"]
	#
	#			 nt.url_key = song["id"]
	#			 nt.is_network = True
	#
	#			 pctl.master_library[id] = nt
	#
	#			 if not replace_existing:
	#				 pctl.master_count += 1
	#
	#			 playlist.append(nt.index)
	#
	#	 for id, name in folders:
	#		 get(id, name)
	#
	#	 self.scanning = False
	#	 if return_list:
	#		 return playlist
	#
	#	 pctl.multi_playlist.append(pl_gen(title="Airsonic Collection", playlist_ids=playlist))
	#	 pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "air"
	#	 switch_playlist(len(pctl.multi_playlist) - 1)

class STray:

	def __init__(self) -> None:
		self.active = False

	def up(self, systray: SysTrayIcon):
		SDL_ShowWindow(t_window)
		SDL_RaiseWindow(t_window)
		SDL_RestoreWindow(t_window)
		gui.lowered = False

	def down(self) -> None:
		if self.active:
			SDL_HideWindow(t_window)

	def advance(self, systray: SysTrayIcon) -> None:
		pctl.advance()

	def back(self, systray: SysTrayIcon) -> None:
		pctl.back()

	def pause(self, systray: SysTrayIcon) -> None:
		pctl.play_pause()

	def track_stop(self, systray: SysTrayIcon) -> None:
		pctl.stop()

	def on_quit_callback(self, systray: SysTrayIcon) -> None:
		tauon.exit("Exit called from tray.")

	def start(self) -> None:
		menu_options = (("Show", None, self.up),
						("Play/Pause", None, self.pause),
						("Stop", None, self.track_stop),
						("Forward", None, self.advance),
						("Back", None, self.back))
		self.systray = SysTrayIcon(
			str(install_directory / "assets" / "icon.ico"), "Tauon Music Box",
			menu_options, on_quit=self.on_quit_callback)
		self.systray.start()
		self.active = True
		gui.tray_active = True

	def stop(self) -> None:
		self.systray.shutdown()
		self.active = False

class GStats:
	def __init__(self):

		self.last_db = 0
		self.last_pl = 0
		self.artist_list = []
		self.album_list = []
		self.genre_list = []
		self.genre_dict = {}

	def update(self, playlist):

		pt = 0

		if pctl.master_count != self.last_db or self.last_pl != playlist:
			self.last_db = pctl.master_count
			self.last_pl = playlist

			artists = {}

			for index in pctl.multi_playlist[playlist].playlist_ids:
				artist = pctl.master_library[index].artist

				if artist == "":
					artist = "<Artist Unspecified>"

				pt = int(star_store.get(index))
				if pt < 30:
					continue

				if artist in artists:
					artists[artist] += pt
				else:
					artists[artist] = pt

			art_list = artists.items()

			sorted_list = sorted(art_list, key=lambda x: x[1], reverse=True)

			self.artist_list = copy.deepcopy(sorted_list)

			genres = {}
			genre_dict = {}

			for index in pctl.multi_playlist[playlist].playlist_ids:
				genre_r = pctl.master_library[index].genre

				pt = int(star_store.get(index))

				gn = []
				if "," in genre_r:
					for g in genre_r.split(","):
						g = g.rstrip(" ").lstrip(" ")
						if len(g) > 0:
							gn.append(g)
				elif ";" in genre_r:
					for g in genre_r.split(";"):
						g = g.rstrip(" ").lstrip(" ")
						if len(g) > 0:
							gn.append(g)
				elif "/" in genre_r:
					for g in genre_r.split("/"):
						g = g.rstrip(" ").lstrip(" ")
						if len(g) > 0:
							gn.append(g)
				elif " & " in genre_r:
					for g in genre_r.split(" & "):
						g = g.rstrip(" ").lstrip(" ")
						if len(g) > 0:
							gn.append(g)
				else:
					gn = [genre_r]

				pt = int(pt / len(gn))

				for genre in gn:

					if genre.lower() in {"", "other", "unknown", "misc"}:
						genre = "<Genre Unspecified>"
					if genre.lower() in {"jpop", "japanese pop"}:
						genre = "J-Pop"
					if genre.lower() in {"jrock", "japanese rock"}:
						genre = "J-Rock"
					if genre.lower() in {"alternative music", "alt-rock", "alternative", "alternrock", "alt"}:
						genre = "Alternative Rock"
					if genre.lower() in {"jpunk", "japanese punk"}:
						genre = "J-Punk"
					if genre.lower() in {"post rock", "post-rock"}:
						genre = "Post-Rock"
					if genre.lower() in {"video game", "game", "game music", "video game music", "game ost"}:
						genre = "Video Game Soundtrack"
					if genre.lower() in {"general soundtrack", "ost", "Soundtracks"}:
						genre = "Soundtrack"
					if genre.lower() in ("anime", "アニメ", "anime ost"):
						genre = "Anime Soundtrack"
					if genre.lower() in {"同人"}:
						genre = "Doujin"
					if genre.lower() in {"chill, chill out", "chill-out"}:
						genre = "Chillout"

					genre = genre.title()

					if len(genre) == 3 and genre[2] == "m":
						genre = genre.upper()

					if genre in genres:

						genres[genre] += pt
					else:
						genres[genre] = pt

					if genre in genre_dict:
						genre_dict[genre].append(index)
					else:
						genre_dict[genre] = [index]

			art_list = genres.items()
			sorted_list = sorted(art_list, key=lambda x: x[1], reverse=True)

			self.genre_list = copy.deepcopy(sorted_list)
			self.genre_dict = genre_dict

			# logging.info('\n-----------------------\n')

			g_albums = {}

			for index in pctl.multi_playlist[playlist].playlist_ids:
				album = pctl.master_library[index].album

				if album == "":
					album = "<Album Unspecified>"

				pt = int(star_store.get(index))

				if pt < 30:
					continue

				if album in g_albums:
					g_albums[album] += pt
				else:
					g_albums[album] = pt

			art_list = g_albums.items()

			sorted_list = sorted(art_list, key=lambda x: x[1], reverse=True)

			self.album_list = copy.deepcopy(sorted_list)

class Drawing:

	def button(
		self, text, x, y, w=None, h=None, font=212, text_highlight_colour=None, text_colour=None,
		background_colour=None, background_highlight_colour=None, press=None, tooltip=""):

		if w is None:
			w = ddt.get_text_w(text, font) + 18 * gui.scale
		if h is None:
			h = 22 * gui.scale

		rect = (x, y, w, h)
		fields.add(rect)

		if text_highlight_colour is None:
			text_highlight_colour = colours.box_button_text_highlight
		if text_colour is None:
			text_colour = colours.box_button_text
		if background_colour is None:
			background_colour = colours.box_button_background
		if background_highlight_colour is None:
			background_highlight_colour = colours.box_button_background_highlight

		click = False

		if press is None:
			press = inp.mouse_click

		if coll(rect):
			if tooltip:
				tool_tip.test(x + 15 * gui.scale, y - 28 * gui.scale, tooltip)
			ddt.rect(rect, background_highlight_colour)

			# if background_highlight_colour[3] != 255:
			#	 background_highlight_colour = None

			ddt.text(
				(rect[0] + int(rect[2] / 2), rect[1] + 2 * gui.scale, 2), text, text_highlight_colour, font, bg=background_highlight_colour)
			if press:
				click = True
		else:
			ddt.rect(rect, background_colour)
			if background_highlight_colour[3] != 255:
				background_colour = None
			ddt.text(
				(rect[0] + int(rect[2] / 2), rect[1] + 2 * gui.scale, 2), text, text_colour, font, bg=background_colour)
		return click

class DropShadow:

	def __init__(self, gui: GuiVar):
		self.readys = {}
		self.underscan = int(15 * gui.scale)
		self.radius = 4
		self.grow = 2 * gui.scale
		self.opacity = 90

	def prepare(self, w, h):
		fh = h + self.underscan
		fw = w + self.underscan

		im = Image.new("RGBA", (round(fw), round(fh)), 0x00000000)
		draw = ImageDraw.Draw(im)
		draw.rectangle(((self.underscan, self.underscan), (w + 2, h + 2)), fill="black")

		im = im.filter(ImageFilter.GaussianBlur(self.radius))

		g = io.BytesIO()
		g.seek(0)
		im.save(g, "PNG")
		g.seek(0)

		wop = rw_from_object(g)
		s_image = IMG_Load_RW(wop, 0)
		c = SDL_CreateTextureFromSurface(renderer, s_image)
		SDL_SetTextureAlphaMod(c, self.opacity)

		tex_w = pointer(c_int(0))
		tex_h = pointer(c_int(0))
		SDL_QueryTexture(c, None, None, tex_w, tex_h)

		dst = SDL_Rect(0, 0)
		dst.w = int(tex_w.contents.value)
		dst.h = int(tex_h.contents.value)

		SDL_FreeSurface(s_image)
		g.close()
		im.close()

		unit = (dst, c)
		self.readys[(w, h)] = unit

	def render(self, x, y, w, h):
		if (w, h) not in self.readys:
			self.prepare(w, h)

		unit = self.readys[(w, h)]
		unit[0].x = round(x) - round(self.underscan)
		unit[0].y = round(y) - round(self.underscan)
		SDL_RenderCopy(renderer, unit[1], None, unit[0])

class LyricsRenMini:

	def __init__(self):
		self.index = -1
		self.text = ""

		self.lyrics_position = 0

	def generate(self, index, w):
		self.text = pctl.master_library[index].lyrics
		self.lyrics_position = 0

	def render(self, index, x, y, w, h, p):
		if index != self.index or self.text != pctl.master_library[index].lyrics:
			self.index = index
			self.generate(index, w)

		colour = colours.side_bar_line1

		# if key_ctrl_down:
		#	 if mouse_wheel < 0:
		#		 prefs.lyrics_font_size += 1
		#	 if mouse_wheel > 0:
		#		 prefs.lyrics_font_size -= 1

		ddt.text((x, y, 4, w), self.text, colour, prefs.lyrics_font_size, w - (w % 2), colours.side_panel_background)

class LyricsRen:

	def __init__(self):

		self.index = -1
		self.text = ""

		self.lyrics_position = 0

	def test_update(self, track_object: TrackClass):

		if track_object.index != self.index or self.text != track_object.lyrics:
			self.index = track_object.index
			self.text = track_object.lyrics
			self.lyrics_position = 0

	def render(self, x, y, w, h, p):

		colour = colours.lyrics
		if test_lumi(colours.gallery_background) < 0.5:
			colour = colours.grey(40)

		ddt.text((x, y, 4, w), self.text, colour, 17, w, colours.playlist_panel_background)

class TimedLyricsToStatic:

	def __init__(self):
		self.cache_key = None
		self.cache_lyrics = ""

	def get(self, track: TrackClass):
		if track.lyrics:
			return track.lyrics
		if track.is_network:
			return ""
		if track == self.cache_key:
			return self.cache_lyrics
		data = find_synced_lyric_data(track)

		if data is None:
			self.cache_lyrics = ""
			self.cache_key = track
			return ""
		text = ""

		for line in data:
			if len(line) < 10:
				continue

			if line[0] != "[" or line[9] != "]" or ":" not in line or "." not in line:
				continue

			text += line.split("]")[-1].rstrip("\n") + "\n"

		self.cache_lyrics = text
		self.cache_key = track
		return text

class TimedLyricsRen:

	def __init__(self):

		self.index = -1

		self.scanned = {}
		self.ready = False
		self.data = []

		self.scroll_position = 0

	def generate(self, track: TrackClass) -> bool | None:

		if self.index == track.index:
			return self.ready

		self.ready = False
		self.index = track.index
		self.scroll_position = 0
		self.data.clear()

		data = find_synced_lyric_data(track)
		if data is None:
			return None

		for line in data:
			if len(line) < 10:
				continue

			if line[0] != "[" or "]" not in line or ":" not in line or "." not in line:
				continue

			try:

				text = line.split("]")[-1].rstrip("\n")
				t = line

				while t[0] == "[" and t[9] == "]" and ":" in t and "." in t:

					a = t.lstrip("[")
					t = t.split("]")[1] + "]"

					a = a.split("]")[0]
					mm, b = a.split(":")
					ss, ms = b.split(".")

					s = int(mm) * 60 + int(ss)
					if len(ms) == 2:
						s += int(ms) / 100
					elif len(ms) == 3:
						s += int(ms) / 1000

					self.data.append((s, text))

					if len(t) < 10:
						break
			except Exception:
				logging.exception("Failed generating timed lyrics")
				continue

		self.data = sorted(self.data, key=lambda x: x[0])
		# logging.info(self.data)

		self.ready = True
		return True

	def render(self, index: int, x: int, y: int, side_panel: bool = False, w: int = 0, h: int = 0) -> bool | None:

		if index != self.index:
			self.ready = False
			self.generate(pctl.master_library[index])

		if right_click and x and y and coll((x, y, w, h)):
			showcase_menu.activate(pctl.master_library[index])

		if not self.ready:
			return False

		if mouse_wheel and (pctl.playing_state != 1 or pctl.track_queue[pctl.queue_step] != index):
			if side_panel:
				if coll((x, y, w, h)):
					self.scroll_position += int(mouse_wheel * 30 * gui.scale)
			else:
				self.scroll_position += int(mouse_wheel * 30 * gui.scale)

		line_active = -1
		last = -1

		highlight = True

		if side_panel:
			bg = colours.top_panel_background
			font_size = 15
			spacing = round(17 * gui.scale)
		else:
			bg = colours.playlist_panel_background
			font_size = 17
			spacing = round(23 * gui.scale)

		test_time = get_real_time()

		if pctl.track_queue[pctl.queue_step] == index:

			for i, line in enumerate(self.data):
				if line[0] < test_time:
					last = i

				if line[0] > test_time:
					pctl.wake_past_time = line[0]
					line_active = last
					break
			else:
				line_active = len(self.data) - 1

			if pctl.playing_state == 1:
				self.scroll_position = (max(0, line_active)) * spacing * -1

		yy = y + self.scroll_position

		for i, line in enumerate(self.data):

			if 0 < yy < window_size[1]:

				colour = colours.lyrics
				if test_lumi(colours.gallery_background) < 0.5:
					colour = colours.grey(40)

				if i == line_active and highlight:
					colour = [255, 210, 50, 255]
					if colours.lm:
						colour = [180, 130, 210, 255]

				h = ddt.text((x, yy, 4, w - 20 * gui.scale), line[1], colour, font_size, w - 20 * gui.scale, bg)
				yy += max(h - round(6 * gui.scale), spacing)
			else:
				yy += spacing
		return None

class TextBox2:
	cursor = True

	def __init__(self) -> None:

		self.text: str = ""
		self.cursor_position = 0
		self.selection = 0
		self.offset = 0
		self.down_lock = False
		self.paste_text = ""

	def paste(self) -> None:

		if SDL_HasClipboardText():
			clip = SDL_GetClipboardText().decode("utf-8")
			self.paste_text = clip

	def copy(self) -> None:

		text = self.get_selection()
		if not text:
			text = self.text
		if text != "":
			SDL_SetClipboardText(text.encode("utf-8"))

	def set_text(self, text: str) -> None:

		self.text = text
		if self.cursor_position > len(text):
			self.cursor_position = 0
			self.selection = 0
		else:
			self.selection = self.cursor_position

	def clear(self) -> None:
		self.text = ""
		#self.cursor_position = 0
		self.selection = self.cursor_position

	def highlight_all(self) -> None:

		self.selection = len(self.text)
		self.cursor_position = 0

	def eliminate_selection(self) -> None:
		if self.selection != self.cursor_position:
			if self.selection > self.cursor_position:
				self.text = self.text[0: len(self.text) - self.selection] + self.text[len(self.text) - self.cursor_position:]
				self.selection = self.cursor_position
			else:
				self.text = self.text[0: len(self.text) - self.cursor_position] + self.text[len(self.text) - self.selection:]
				self.cursor_position = self.selection

	def get_selection(self, p: int = 1) -> str:
		if self.selection != self.cursor_position:
			if p == 1:
				if self.selection > self.cursor_position:
					return self.text[len(self.text) - self.selection: len(self.text) - self.cursor_position]

				return self.text[len(self.text) - self.cursor_position: len(self.text) - self.selection]
			if p == 0:
				return self.text[0: len(self.text) - max(self.cursor_position, self.selection)]
			if p == 2:
				return self.text[len(self.text) - min(self.cursor_position, self.selection):]

		else:
			return ""

	def draw(
			self, x, y, colour, active=True, secret=False, font=13, width=0, click=False, selection_height=18, big=False):

		# A little bit messy
		# For now, this is set up so where 'width' is set > 0, the cursor position becomes editable,
		# otherwise it is fixed to end

		SDL_SetRenderTarget(renderer, text_box_canvas)
		SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE)
		SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)

		text_box_canvas_rect.x = 0
		text_box_canvas_rect.y = 0
		SDL_RenderFillRect(renderer, text_box_canvas_rect)

		SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND)

		selection_height *= gui.scale

		if click is False:
			click = inp.mouse_click
		if mouse_down:
			gui.update = 2  # TODO, more elegant fix

		rect = (x - 3, y - 2, width - 3, 21 * gui.scale)
		select_rect = (x - 20 * gui.scale, y - 2, width + 20 * gui.scale, 21 * gui.scale)

		fields.add(rect)

		# Activate Menu
		if coll(rect):
			if right_click or level_2_right_click:
				field_menu.activate(self)

		if width > 0 and active:

			if click and field_menu.active:
				# field_menu.click()
				click = False

			# Add text from input
			if input_text != "":
				self.eliminate_selection()
				self.text = self.text[0: len(self.text) - self.cursor_position] + input_text + self.text[len(
					self.text) - self.cursor_position:]

			def g():
				if len(self.text) == 0 or self.cursor_position == len(self.text):
					return None
				return self.text[len(self.text) - self.cursor_position - 1]

			def g2():
				if len(self.text) == 0 or self.cursor_position == 0:
					return None
				return self.text[len(self.text) - self.cursor_position]

			def d():
				self.text = self.text[0: len(self.text) - self.cursor_position - 1] + self.text[len(
					self.text) - self.cursor_position:]
				self.selection = self.cursor_position

			# Ctrl + Backspace to delete word
			if inp.backspace_press and (key_ctrl_down or key_rctrl_down) and \
					self.cursor_position == self.selection and len(self.text) > 0 and self.cursor_position < len(
				self.text):
				while g() == " ":
					d()
				while g() != " " and g() != None:
					d()

			# Ctrl + left to move cursor back a word
			elif (key_ctrl_down or key_rctrl_down) and key_left_press:
				while g() == " ":
					self.cursor_position += 1
					if not key_shift_down:
						self.selection = self.cursor_position
				while g() != None and g() not in " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~":
					self.cursor_position += 1
					if not key_shift_down:
						self.selection = self.cursor_position
					if g() == " ":
						self.cursor_position -= 1
						if not key_shift_down:
							self.selection = self.cursor_position
						break

			# Ctrl + right to move cursor forward a word
			elif (key_ctrl_down or key_rctrl_down) and key_right_press:
				while g2() == " ":
					self.cursor_position -= 1
					if not key_shift_down:
						self.selection = self.cursor_position
				while g2() != None and g2() not in " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~":
					self.cursor_position -= 1
					if not key_shift_down:
						self.selection = self.cursor_position
					if g2() == " ":
						self.cursor_position += 1
						if not key_shift_down:
							self.selection = self.cursor_position
						break

			# Handle normal backspace
			elif inp.backspace_press and len(self.text) > 0 and self.cursor_position < len(self.text):
				while inp.backspace_press and len(self.text) > 0 and self.cursor_position < len(self.text):
					if self.selection != self.cursor_position:
						self.eliminate_selection()
					else:
						self.text = self.text[0:len(self.text) - self.cursor_position - 1] + self.text[len(
							self.text) - self.cursor_position:]
					inp.backspace_press -= 1
			elif inp.backspace_press and len(self.get_selection()) > 0:
				self.eliminate_selection()

			# Left and right arrow keys to move cursor
			if key_right_press:
				if self.cursor_position > 0:
					self.cursor_position -= 1
				if not key_shift_down and not key_shiftr_down:
					self.selection = self.cursor_position

			if key_left_press:
				if self.cursor_position < len(self.text):
					self.cursor_position += 1
				if not key_shift_down and not key_shiftr_down:
					self.selection = self.cursor_position

			if self.paste_text:
				if "http://" in self.text and "http://" in self.paste_text:
					self.text = ""

				self.paste_text = self.paste_text.rstrip(" ").lstrip(" ")
				self.paste_text = self.paste_text.replace("\n", " ").replace("\r", "")

				self.eliminate_selection()
				self.text = self.text[0: len(self.text) - self.cursor_position] + self.paste_text + self.text[len(
					self.text) - self.cursor_position:]
				self.paste_text = ""

			# Paste via ctrl-v
			if key_ctrl_down and key_v_press:
				clip = SDL_GetClipboardText().decode("utf-8")
				self.eliminate_selection()
				self.text = self.text[0: len(self.text) - self.cursor_position] + clip + self.text[len(
					self.text) - self.cursor_position:]

			if key_ctrl_down and key_c_press:
				self.copy()

			if key_ctrl_down and key_x_press:
				if len(self.get_selection()) > 0:
					text = self.get_selection()
					if text != "":
						SDL_SetClipboardText(text.encode("utf-8"))
					self.eliminate_selection()

			if key_ctrl_down and key_a_press:
				self.cursor_position = 0
				self.selection = len(self.text)

			# ddt.rect(rect, [255, 50, 50, 80], True)
			if coll(rect) and not field_menu.active:
				gui.cursor_want = 2

			# Delete key to remove text in front of cursor
			if key_del:
				if self.selection != self.cursor_position:
					self.eliminate_selection()
				else:
					self.text = self.text[0:len(self.text) - self.cursor_position] + self.text[len(
						self.text) - self.cursor_position + 1:]
					if self.cursor_position > 0:
						self.cursor_position -= 1
					self.selection = self.cursor_position

			if key_home_press:
				self.cursor_position = len(self.text)
				if not key_shift_down and not key_shiftr_down:
					self.selection = self.cursor_position
			if key_end_press:
				self.cursor_position = 0
				if not key_shift_down and not key_shiftr_down:
					self.selection = self.cursor_position

			width -= round(15 * gui.scale)
			t_len = ddt.get_text_w(self.text, font)
			if active and editline and editline != input_text:
				t_len += ddt.get_text_w(editline, font)
			if not click and not self.down_lock:
				cursor_x = ddt.get_text_w(self.text[:len(self.text) - self.cursor_position], font)
				if self.cursor_position == 0 or cursor_x < self.offset + round(
						15 * gui.scale) or cursor_x > self.offset + width:
					if t_len > width:
						self.offset = t_len - width

						if cursor_x < self.offset:
							self.offset = cursor_x - round(15 * gui.scale)

							self.offset = max(self.offset, 0)
					else:
						self.offset = 0

			x -= self.offset

			if coll(select_rect):  # coll((x - 15, y, width + 16, selection_height + 1)):
				# ddt.rect_r((x - 15, y, width + 16, 19), [50, 255, 50, 50], True)
				if click:
					pre = 0
					post = 0
					if mouse_position[0] < x + 1:
						self.cursor_position = len(self.text)
					else:
						for i in range(len(self.text)):
							post = ddt.get_text_w(self.text[0:i + 1], font)
							# pre_half = int((post - pre) / 2)

							if x + pre - 0 <= mouse_position[0] <= x + post + 0:
								diff = post - pre
								if mouse_position[0] >= x + pre + int(diff / 2):
									self.cursor_position = len(self.text) - i - 1
								else:
									self.cursor_position = len(self.text) - i
								break
							pre = post
						else:
							self.cursor_position = 0
					self.selection = 0
					self.down_lock = True

			if mouse_up:
				self.down_lock = False
			if self.down_lock:
				pre = 0
				post = 0
				text = self.text
				if secret:
					text = "●" * len(self.text)
				if mouse_position[0] < x + 1:
					self.selection = len(text)
				else:

					for i in range(len(text)):
						post = ddt.get_text_w(text[0:i + 1], font)
						# pre_half = int((post - pre) / 2)

						if x + pre - 0 <= mouse_position[0] <= x + post + 0:
							diff = post - pre

							if mouse_position[0] >= x + pre + int(diff / 2):
								self.selection = len(text) - i - 1

							else:
								self.selection = len(text) - i

							break
						pre = post

					else:
						self.selection = 0

			text = self.text[0: len(self.text) - self.cursor_position]
			if secret:
				text = "●" * len(text)
			a = ddt.get_text_w(text, font)

			text = self.text[0: len(self.text) - self.selection]
			if secret:
				text = "●" * len(text)
			b = ddt.get_text_w(text, font)

			top = y
			if big:
				top -= 12 * gui.scale

			ddt.rect([a, 0, b - a, selection_height], [40, 120, 180, 255])

			if self.selection != self.cursor_position:
				inf_comp = 0
				text = self.get_selection(0)
				if secret:
					text = "●" * len(text)
				space = ddt.text((0, 0), text, colour, font)
				text = self.get_selection(1)
				if secret:
					text = "●" * len(text)
				space += ddt.text((0 + space - inf_comp, 0), text, [240, 240, 240, 255], font, bg=[40, 120, 180, 255])
				text = self.get_selection(2)
				if secret:
					text = "●" * len(text)
				ddt.text((0 + space - (inf_comp * 2), 0), text, colour, font)
			else:
				text = self.text
				if secret:
					text = "●" * len(text)
				ddt.text((0, 0), text, colour, font)

			text = self.text[0: len(self.text) - self.cursor_position]
			if secret:
				text = "●" * len(text)
			space = ddt.get_text_w(text, font)

			if TextBox.cursor and self.selection == self.cursor_position:
				# ddt.line(x + space, y + 2, x + space, y + 15, colour)

				ddt.rect((0 + space, 0 + 2, 1 * gui.scale, 14 * gui.scale), colour)

			if click:
				self.selection = self.cursor_position

		else:
			width -= round(15 * gui.scale)
			text = self.text
			if secret:
				text = "●" * len(text)
			t_len = ddt.get_text_w(text, font)
			ddt.text((0, 0), text, colour, font)
			self.offset = 0
			if coll(rect) and not field_menu.active:
				gui.cursor_want = 2

		if active and editline != "" and editline != input_text:
			ex = ddt.text((space + round(4 * gui.scale), 0), editline, [240, 230, 230, 255], font)
			tw, th = ddt.get_text_wh(editline, font, max_x=2000)
			ddt.rect((space + round(4 * gui.scale), th + round(2 * gui.scale), ex, round(1 * gui.scale)), [245, 245, 245, 255])

			rect = SDL_Rect(pixel_to_logical(x + space + tw + (5 * gui.scale)), pixel_to_logical(y + th + 4 * gui.scale), 1, 1)
			SDL_SetTextInputRect(rect)

		animate_monitor_timer.set()

		text_box_canvas_hide_rect.x = 0
		text_box_canvas_hide_rect.y = 0

		# if self.offset:
		SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE)

		text_box_canvas_hide_rect.w = round(self.offset)
		SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
		SDL_RenderFillRect(renderer, text_box_canvas_hide_rect)

		text_box_canvas_hide_rect.w = round(t_len)
		text_box_canvas_hide_rect.x = round(self.offset + width + round(5 * gui.scale))
		SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
		SDL_RenderFillRect(renderer, text_box_canvas_hide_rect)

		SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND)
		SDL_SetRenderTarget(renderer, gui.main_texture)

		text_box_canvas_rect.x = round(x)
		text_box_canvas_rect.y = round(y)
		SDL_RenderCopy(renderer, text_box_canvas, None, text_box_canvas_rect)

class TextBox:
	cursor = True

	def __init__(self) -> None:

		self.text = ""
		self.cursor_position = 0
		self.selection = 0
		self.down_lock = False

	def paste(self) -> None:

		if SDL_HasClipboardText():
			clip = SDL_GetClipboardText().decode("utf-8")

			if "http://" in self.text and "http://" in clip:
				self.text = ""

			clip = clip.rstrip(" ").lstrip(" ")
			clip = clip.replace("\n", " ").replace("\r", "")

			self.eliminate_selection()
			self.text = self.text[0: len(self.text) - self.cursor_position] + clip + self.text[len(
				self.text) - self.cursor_position:]

	def copy(self) -> None:

		text = self.get_selection()
		if not text:
			text = self.text
		if text != "":
			SDL_SetClipboardText(text.encode("utf-8"))

	def set_text(self, text):

		self.text = text
		self.cursor_position = 0
		self.selection = 0

	def clear(self) -> None:
		self.text = ""

	def highlight_all(self) -> None:

		self.selection = len(self.text)
		self.cursor_position = 0

	def highlight_none(self) -> None:
		self.selection = 0
		self.cursor_position = 0

	def eliminate_selection(self) -> None:
		if self.selection != self.cursor_position:
			if self.selection > self.cursor_position:
				self.text = self.text[0: len(self.text) - self.selection] + self.text[
					len(self.text) - self.cursor_position:]
				self.selection = self.cursor_position
			else:
				self.text = self.text[0: len(self.text) - self.cursor_position] + self.text[
					len(self.text) - self.selection:]
				self.cursor_position = self.selection

	def get_selection(self, p: int = 1):
		if self.selection != self.cursor_position:
			if p == 1:
				if self.selection > self.cursor_position:
					return self.text[len(self.text) - self.selection: len(self.text) - self.cursor_position]

				return self.text[len(self.text) - self.cursor_position: len(self.text) - self.selection]
			if p == 0:
				return self.text[0: len(self.text) - max(self.cursor_position, self.selection)]
			if p == 2:
				return self.text[len(self.text) - min(self.cursor_position, self.selection):]

		else:
			return ""

	def draw(
		self, x: int, y: int, colour: list[int], active: bool = True, secret: bool = False,
		font: int = 13, width: int = 0, click: bool = False, selection_height: int = 18, big: bool = False):

		# A little bit messy
		# For now, this is set up so where 'width' is set > 0, the cursor position becomes editable,
		# otherwise it is fixed to end

		selection_height *= gui.scale

		if click is False:
			click = inp.mouse_click

		if width > 0 and active:

			rect = (x - 3, y - 2, width - 3, 21 * gui.scale)
			select_rect = (x - 20 * gui.scale, y - 2, width + 20 * gui.scale, 21 * gui.scale)
			if big:
				rect = (x - 3, y - 15 * gui.scale, width - 3, 35 * gui.scale)
				select_rect = (x - 50 * gui.scale, y - 15 * gui.scale, width + 50 * gui.scale, 35 * gui.scale)

			# Activate Menu
			if coll(rect):
				if right_click or level_2_right_click:
					field_menu.activate(self)

			if click and field_menu.active:
				# field_menu.click()
				click = False

			# Add text from input
			if input_text != "":
				self.eliminate_selection()
				self.text = self.text[0: len(self.text) - self.cursor_position] + input_text + self.text[
					len(self.text) - self.cursor_position:]

			def g():
				if len(self.text) == 0 or self.cursor_position == len(self.text):
					return None
				return self.text[len(self.text) - self.cursor_position - 1]

			def g2():
				if len(self.text) == 0 or self.cursor_position == 0:
					return None
				return self.text[len(self.text) - self.cursor_position]

			def d():
				self.text = self.text[0: len(self.text) - self.cursor_position - 1] + self.text[
					len(self.text) - self.cursor_position:]
				self.selection = self.cursor_position

			# Ctrl + Backspace to delete word
			if inp.backspace_press and (key_ctrl_down or key_rctrl_down) and \
					self.cursor_position == self.selection and len(self.text) > 0 and self.cursor_position < len(
				self.text):
				while g() == " ":
					d()
				while g() != " " and g() != None:
					d()

			# Ctrl + left to move cursor back a word
			elif (key_ctrl_down or key_rctrl_down) and key_left_press:
				while g() == " ":
					self.cursor_position += 1
					if not key_shift_down:
						self.selection = self.cursor_position
				while g() != None and g() not in " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~":
					self.cursor_position += 1
					if not key_shift_down:
						self.selection = self.cursor_position
					if g() == " ":
						self.cursor_position -= 1
						if not key_shift_down:
							self.selection = self.cursor_position
						break

			# Ctrl + right to move cursor forward a word
			elif (key_ctrl_down or key_rctrl_down) and key_right_press:
				while g2() == " ":
					self.cursor_position -= 1
					if not key_shift_down:
						self.selection = self.cursor_position
				while g2() != None and g2() not in " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~":
					self.cursor_position -= 1
					if not key_shift_down:
						self.selection = self.cursor_position
					if g2() == " ":
						self.cursor_position += 1
						if not key_shift_down:
							self.selection = self.cursor_position
						break

			# Handle normal backspace
			elif inp.backspace_press and len(self.text) > 0 and self.cursor_position < len(self.text):
				while inp.backspace_press and len(self.text) > 0 and self.cursor_position < len(self.text):
					if self.selection != self.cursor_position:
						self.eliminate_selection()
					else:
						self.text = self.text[0:len(self.text) - self.cursor_position - 1] + self.text[
							len(self.text) - self.cursor_position:]
					inp.backspace_press -= 1
			elif inp.backspace_press and len(self.get_selection()) > 0:
				self.eliminate_selection()

			# Left and right arrow keys to move cursor
			if key_right_press:
				if self.cursor_position > 0:
					self.cursor_position -= 1
				if not key_shift_down and not key_shiftr_down:
					self.selection = self.cursor_position

			if key_left_press:
				if self.cursor_position < len(self.text):
					self.cursor_position += 1
				if not key_shift_down and not key_shiftr_down:
					self.selection = self.cursor_position

			# Paste via ctrl-v
			if key_ctrl_down and key_v_press:
				clip = SDL_GetClipboardText().decode("utf-8")
				self.eliminate_selection()
				self.text = self.text[0: len(self.text) - self.cursor_position] + clip + self.text[len(
					self.text) - self.cursor_position:]

			if key_ctrl_down and key_c_press:
				self.copy()

			if key_ctrl_down and key_x_press:
				if len(self.get_selection()) > 0:
					text = self.get_selection()
					if text != "":
						SDL_SetClipboardText(text.encode("utf-8"))
					self.eliminate_selection()

			if key_ctrl_down and key_a_press:
				self.cursor_position = 0
				self.selection = len(self.text)

			# ddt.rect_r(rect, [255, 50, 50, 80], True)
			if coll(rect) and not field_menu.active:
				gui.cursor_want = 2

			fields.add(rect)

			# Delete key to remove text in front of cursor
			if key_del:
				if self.selection != self.cursor_position:
					self.eliminate_selection()
				else:
					self.text = self.text[0:len(self.text) - self.cursor_position] + self.text[len(
						self.text) - self.cursor_position + 1:]
					if self.cursor_position > 0:
						self.cursor_position -= 1
					self.selection = self.cursor_position

			if key_home_press:
				self.cursor_position = len(self.text)
				if not key_shift_down and not key_shiftr_down:
					self.selection = self.cursor_position
			if key_end_press:
				self.cursor_position = 0
				if not key_shift_down and not key_shiftr_down:
					self.selection = self.cursor_position

			if coll(select_rect):
				# ddt.rect_r((x - 15, y, width + 16, 19), [50, 255, 50, 50], True)
				if click:
					pre = 0
					post = 0
					if mouse_position[0] < x + 1:
						self.cursor_position = len(self.text)
					else:
						for i in range(len(self.text)):
							post = ddt.get_text_w(self.text[0:i + 1], font)
							# pre_half = int((post - pre) / 2)

							if x + pre - 0 <= mouse_position[0] <= x + post + 0:
								diff = post - pre
								if mouse_position[0] >= x + pre + int(diff / 2):
									self.cursor_position = len(self.text) - i - 1
								else:
									self.cursor_position = len(self.text) - i
								break
							pre = post
						else:
							self.cursor_position = 0
					self.selection = 0
					self.down_lock = True

			if mouse_up:
				self.down_lock = False
			if self.down_lock:
				pre = 0
				post = 0
				if mouse_position[0] < x + 1:

					self.selection = len(self.text)
				else:

					for i in range(len(self.text)):
						post = ddt.get_text_w(self.text[0:i + 1], font)
						# pre_half = int((post - pre) / 2)

						if x + pre - 0 <= mouse_position[0] <= x + post + 0:
							diff = post - pre

							if mouse_position[0] >= x + pre + int(diff / 2):
								self.selection = len(self.text) - i - 1

							else:
								self.selection = len(self.text) - i

							break
						pre = post

					else:
						self.selection = 0

			a = ddt.get_text_w(self.text[0: len(self.text) - self.cursor_position], font)
			# logging.info("")
			# logging.info(self.selection)
			# logging.info(self.cursor_position)

			b = ddt.get_text_w(self.text[0: len(self.text) - self.selection], font)

			# rint((a, b))

			top = y
			if big:
				top -= 12 * gui.scale

			ddt.rect([x + a, top, b - a, selection_height], [40, 120, 180, 255])

			if self.selection != self.cursor_position:
				inf_comp = 0
				space = ddt.text((x, y), self.get_selection(0), colour, font)
				space += ddt.text(
					(x + space - inf_comp, y), self.get_selection(1), [240, 240, 240, 255], font,
					bg=[40, 120, 180, 255])
				ddt.text((x + space - (inf_comp * 2), y), self.get_selection(2), colour, font)
			else:
				ddt.text((x, y), self.text, colour, font)

			space = ddt.get_text_w(self.text[0: len(self.text) - self.cursor_position], font)

			if TextBox.cursor and self.selection == self.cursor_position:
				# ddt.line(x + space, y + 2, x + space, y + 15, colour)

				if big:
					# ddt.rect_r((xx + 1 , yy - 12 * gui.scale, 2 * gui.scale, 27 * gui.scale), colour, True)
					ddt.rect((x + space, y - 15 * gui.scale + 2, 1 * gui.scale, 30 * gui.scale), colour)
				else:
					ddt.rect((x + space, y + 2, 1 * gui.scale, 14 * gui.scale), colour)

			if click:
				self.selection = self.cursor_position

		else:
			if active:
				self.text += input_text
				if input_text != "":
					self.cursor = True

				while inp.backspace_press and len(self.text) > 0:
					self.text = self.text[:-1]
					inp.backspace_press -= 1

				if key_ctrl_down and key_v_press:
					self.paste()

			if secret:
				space = ddt.text((x, y), "●" * len(self.text), colour, font)
			else:
				space = ddt.text((x, y), self.text, colour, font)

			if active and TextBox.cursor:
				xx = x + space + 1
				yy = y + 3
				if big:
					ddt.rect((xx + 1, yy - 12 * gui.scale, 2 * gui.scale, 27 * gui.scale), colour)
				else:
					ddt.rect((xx, yy, 1 * gui.scale, 14 * gui.scale), colour)

		if active and editline != "" and editline != input_text:
			ex = ddt.text((x + space + round(4 * gui.scale), y), editline, [240, 230, 230, 255], font)
			tw, th = ddt.get_text_wh(editline, font, max_x=2000)
			ddt.rect((x + space + round(4 * gui.scale), (y + th) - round(4 * gui.scale), ex, round(1 * gui.scale)),
				[245, 245, 245, 255])

			rect = SDL_Rect(pixel_to_logical(x + space + tw + 5 * gui.scale), pixel_to_logical(y + th + 4 * gui.scale), 1, 1)
			SDL_SetTextInputRect(rect)

		animate_monitor_timer.set()

class ImageObject:
	def __init__(self) -> None:
		self.index = 0
		self.texture = None
		self.rect = None
		self.request_size = (0, 0)
		self.original_size = (0, 0)
		self.actual_size = (0, 0)
		self.source = ""
		self.offset = 0
		self.stats = True
		self.format = ""

class AlbumArt:
	def __init__(self):
		self.image_types = {"jpg", "JPG", "jpeg", "JPEG", "PNG", "png", "BMP", "bmp", "GIF", "gif", "jxl", "JXL"}
		self.art_folder_names = {
			"art", "scans", "scan", "booklet", "images", "image", "cover",
			"covers", "coverart", "albumart", "gallery", "jacket", "artwork",
			"bonus", "bk", "cover artwork", "cover art"}
		self.source_cache: dict[int, list[tuple[int, str]]] = {}
		self.image_cache: list[ImageObject] = []
		self.current_wu = None

		self.blur_texture = None
		self.blur_rect = None
		self.loaded_bg_type = 0

		self.download_in_progress = False
		self.downloaded_image = None
		self.downloaded_track = None

		self.base64cache = (0, 0, "")
		self.processing64on = None

		self.bin_cached = (None, None, None)  # track, subsource, bin

		self.embed_cached = (None, None)

	def async_download_image(self, track: TrackClass, subsource: list[tuple[int, str]]) -> None:

		self.downloaded_image = album_art_gen.get_source_raw(0, 0, track, subsource=subsource)
		self.downloaded_track = track
		self.download_in_progress = False
		gui.update += 1

	def get_info(self, track_object: TrackClass) -> list[tuple[str, int, int, int, str]]:

		sources = self.get_sources(track_object)
		if len(sources) == 0:
			return None

		offset = self.get_offset(track_object.fullpath, sources)

		o_size = (0, 0)
		format = "ERROR"

		for item in self.image_cache:
			if item.index == track_object.index and item.offset == offset:
				o_size = item.original_size
				format = item.format
				break

		else:
			# Hacky fix
			# A quirk is the index stays of the cached image
			# This workaround can be done since (currently) cache has max size of 1
			if self.image_cache:
				o_size = self.image_cache[0].original_size
				format = self.image_cache[0].format

		return [sources[offset][0], len(sources), offset, o_size, format]

	def get_sources(self, tr: TrackClass) -> list[tuple[int, str]]:

		filepath = tr.fullpath
		ext = tr.file_ext

		# Check if source list already exists, if not, make it
		if tr.index in self.source_cache:
			return self.source_cache[tr.index]

		source_list: list[tuple[int, str]] = []  # istag,

		# Source type the is first element in list
		# 0 = File
		# 1 = Embedded in tag
		# 2 = Network location

		if tr.is_network:
			# Add url if network target
			if tr.art_url_key:
				source_list.append([2, tr.art_url_key])
		else:
			# Check for local image files
			direc = os.path.dirname(filepath)
			try:
				items_in_dir = os.listdir(direc)
			except FileNotFoundError:
				logging.warning(f"Failed to find directory: {direc}")
				return []
			except Exception:
				logging.exception(f"Unknown error loading directory: {direc}")
				return []

		# Check for embedded image
		try:
			pic = self.get_embed(tr)
			if pic:
				source_list.append([1, filepath])
		except Exception:
			logging.exception("Failed to get embedded image")

		if not tr.is_network:

			dirs_in_dir = [
				subdirec for subdirec in items_in_dir if
				os.path.isdir(os.path.join(direc, subdirec)) and subdirec.lower() in self.art_folder_names]

			ins = len(source_list)
			for i in range(len(items_in_dir)):
				if os.path.splitext(items_in_dir[i])[1][1:] in self.image_types:
					dir_path = os.path.join(direc, items_in_dir[i]).replace("\\", "/")
					# The image name "Folder" is likely desired to be prioritised over other names
					if os.path.splitext(os.path.basename(dir_path))[0] in ("Folder", "folder", "Cover", "cover"):
						source_list.insert(ins, [0, dir_path])
					else:
						source_list.append([0, dir_path])

			for i in range(len(dirs_in_dir)):
				subdirec = os.path.join(direc, dirs_in_dir[i])
				items_in_dir2 = os.listdir(subdirec)

				for y in range(len(items_in_dir2)):
					if os.path.splitext(items_in_dir2[y])[1][1:] in self.image_types:
						dir_path = os.path.join(subdirec, items_in_dir2[y]).replace("\\", "/")
						source_list.append([0, dir_path])

		self.source_cache[tr.index] = source_list

		return source_list

	def get_error_img(self, size: float) -> ImageFile:
		im = Image.open(str(install_directory / "assets" / "load-error.png"))
		im.thumbnail((size, size), Image.Resampling.LANCZOS)
		return im

	def fast_display(self, index, location, box, source: list[tuple[int, str]], offset) -> int:
		"""Renders cached image only by given size for faster performance"""

		found_unit = None
		max_h = 0

		for unit in self.image_cache:
			if unit.source == source[offset][1]:
				if unit.actual_size[1] > max_h:
					max_h = unit.actual_size[1]
					found_unit = unit

		if found_unit == None:
			return 1

		unit = found_unit

		temp_dest.x = round(location[0])
		temp_dest.y = round(location[1])

		temp_dest.w = unit.original_size[0]  # round(box[0])
		temp_dest.h = unit.original_size[1]  # round(box[1])

		bh = round(box[1])
		bw = round(box[0])

		if prefs.zoom_art:
			temp_dest.w, temp_dest.h = fit_box((unit.original_size[0], unit.original_size[1]), box)
		else:

			# Constrain image to given box
			if temp_dest.w > bw:
				temp_dest.w = bw
				temp_dest.h = int(bw * (unit.original_size[1] / unit.original_size[0]))

			if temp_dest.h > bh:
				temp_dest.h = bh
				temp_dest.w = int(temp_dest.h * (unit.original_size[0] / unit.original_size[1]))

			# prevent scaling larger than original image size
			if temp_dest.w > unit.original_size[0] or temp_dest.h > unit.original_size[1]:
				temp_dest.w = unit.original_size[0]
				temp_dest.h = unit.original_size[1]

		# center the image
		temp_dest.x = int((box[0] - temp_dest.w) / 2) + temp_dest.x
		temp_dest.y = int((box[1] - temp_dest.h) / 2) + temp_dest.y

		# render the image
		SDL_RenderCopy(renderer, unit.texture, None, temp_dest)
		style_overlay.hole_punches.append(temp_dest)

		gui.art_drawn_rect = (temp_dest.x, temp_dest.y, temp_dest.w, temp_dest.h)

		return 0

	def open_external(self, track_object: TrackClass) -> int:

		index = track_object.index

		source = self.get_sources(track_object)
		if len(source) == 0:
			return 0

		offset = self.get_offset(track_object.fullpath, source)

		if track_object.is_network:
			show_message(_("Saving network images not implemented"))
			return 0
		if source[offset][0] > 0:
			pic = album_art_gen.get_embed(track_object)
			if not pic:
				show_message(_("Image save error."), _("No embedded album art."), mode="warning")
				return 0

			source_image = io.BytesIO(pic)
			im = Image.open(source_image)
			source_image.close()

			ext = "." + im.format.lower()
			if im.format == "JPEG":
				ext = ".jpg"
			target = str(cache_directory / "open-image")
			if not os.path.exists(target):
				os.makedirs(target)
			target = os.path.join(target, "embed-" + str(im.height) + "px-" + str(track_object.index) + ext)

			if len(pic) > 30:
				with open(target, "wb") as w:
					w.write(pic)

		else:
			target = source[offset][1]

		if system == "Windows" or msys:
			os.startfile(target)
		elif macos:
			subprocess.call(["open", target])
		else:
			subprocess.call(["xdg-open", target])

		return 0

	def cycle_offset(self, track_object: TrackClass, reverse: bool = False) -> int:

		filepath = track_object.fullpath
		sources = self.get_sources(track_object)
		if len(sources) == 0:
			return 0
		parent_folder = os.path.dirname(filepath)
		# Find cached offset
		if parent_folder in folder_image_offsets:

			if reverse:
				folder_image_offsets[parent_folder] -= 1
			else:
				folder_image_offsets[parent_folder] += 1

			folder_image_offsets[parent_folder] %= len(sources)
		return 0

	def cycle_offset_reverse(self, track_object: TrackClass) -> None:
		self.cycle_offset(track_object, True)

	def get_offset(self, filepath: str, source: list[tuple[int, str]]) -> int:

		# Check if folder offset already exsts, if not, make it
		parent_folder = os.path.dirname(filepath)

		if parent_folder in folder_image_offsets:

			# Reset the offset if greater than number of images available
			if folder_image_offsets[parent_folder] > len(source) - 1:
				folder_image_offsets[parent_folder] = 0
		else:
			folder_image_offsets[parent_folder] = 0

		return folder_image_offsets[parent_folder]

	def get_embed(self, track: TrackClass):

		# cached = self.embed_cached
		# if cached[0] == track:
		#	#logging.info("used cached")
		#	return cached[1]

		filepath = track.fullpath

		# Use cached file if present
		if prefs.precache and tauon.cachement:
			path = tauon.cachement.get_file_cached_only(track)
			if path:
				filepath = path

		pic = None

		if track.file_ext == "MP3":
			try:
				tag = mutagen.id3.ID3(filepath)
				frame = tag.getall("APIC")
				if frame:
					pic = frame[0].data
			except Exception:
				logging.exception(f"Failed to get tags on file: {filepath}")

			if pic is not None and len(pic) < 30:
				pic = None

		elif track.file_ext == "FLAC":
			with Flac(filepath) as tag:
				tag.read(True)
				if tag.has_picture and len(tag.picture) > 30:
					pic = tag.picture

		elif track.file_ext == "APE":
			with Ape(filepath) as tag:
				tag.read()
				if tag.has_picture and len(tag.picture) > 30:
					pic = tag.picture

		elif track.file_ext == "M4A":
			with M4a(filepath) as tag:
				tag.read(True)
				if tag.has_picture and len(tag.picture) > 30:
					pic = tag.picture

		elif track.file_ext == "OPUS" or track.file_ext == "OGG" or track.file_ext == "OGA":
			with Opus(filepath) as tag:
				tag.read()
				if tag.has_picture and len(tag.picture) > 30:
					with io.BytesIO(base64.b64decode(tag.picture)) as a:
						a.seek(0)
						image = parse_picture_block(a)
					pic = image

		# self.embed_cached = (track, pic)
		return pic

	def get_source_raw(self, offset: int, sources: list[tuple[int, str]] | int, track: TrackClass, subsource: list[tuple[int, str]] | None = None):

		source_image = None

		if subsource is None:
			subsource = sources[offset]

		if subsource[0] == 1:
			# Target is a embedded image\\\
			pic = self.get_embed(track)
			assert pic
			source_image = io.BytesIO(pic)

		elif subsource[0] == 2:
			try:
				if track.file_ext == "RADIO" or track.file_ext == "Spotify":
					if pctl.radio_image_bin:
						return pctl.radio_image_bin

				cached_path = os.path.join(n_cache_dir, hashlib.md5(track.art_url_key.encode()).hexdigest()[:12])
				if os.path.isfile(cached_path):
					source_image = open(cached_path, "rb")
				else:
					if track.file_ext == "SUB":
						source_image = subsonic.get_cover(track)
					elif track.file_ext == "JELY":
						source_image = jellyfin.get_cover(track)
					else:
						response = urllib.request.urlopen(get_network_thumbnail_url(track), context=ssl_context)
						source_image = io.BytesIO(response.read())
					if source_image:
						with Path(cached_path).open("wb") as file:
							file.write(source_image.read())
						source_image.seek(0)

			except Exception:
				logging.exception("Failed to get source")

		else:
			source_image = open(subsource[1], "rb")

		return source_image

	def get_base64(self, track: TrackClass, size):

		# Wait if an identical track is already being processed
		if self.processing64on == track:
			t = 0
			while True:
				if self.processing64on is None:
					break
				time.sleep(0.05)
				t += 1
				if t > 20:
					break

		cahced = self.base64cache
		if track == cahced[0] and size == cahced[1]:
			return cahced[2]

		self.processing64on = track

		filepath = track.fullpath
		sources = self.get_sources(track)

		if len(sources) == 0:
			self.processing64on = None
			return False

		offset = self.get_offset(filepath, sources)

		# Get source IO
		source_image = self.get_source_raw(offset, sources, track)

		if source_image is None:
			self.processing64on = None
			return ""

		im = Image.open(source_image)
		if im.mode != "RGB":
			im = im.convert("RGB")
		im.thumbnail(size, Image.Resampling.LANCZOS)
		buff = io.BytesIO()
		im.save(buff, format="JPEG")
		sss = base64.b64encode(buff.getvalue())

		self.base64cache = (track, size, sss)
		self.processing64on = None
		return sss

	def get_background(self, track: TrackClass) -> BytesIO | BufferedReader | None:
		#logging.info("Find background...")
		# Determine artist name to use
		artist = get_artist_safe(track)
		if not artist:
			return None

		# Check cache for existing image
		path = os.path.join(b_cache_dir, artist)
		if os.path.isfile(path):
			logging.info("Load cached background")
			return open(path, "rb")

		# Try last.fm background
		path = artist_info_box.get_data(artist, get_img_path=True)
		if os.path.isfile(path):
			logging.info("Load cached background lfm")
			return open(path, "rb")

		# Check we've not already attempted a search for this artist
		if artist in prefs.failed_background_artists:
			return None

		# Get artist MBID
		try:
			s = musicbrainzngs.search_artists(artist, limit=1)
			artist_id = s["artist-list"][0]["id"]
		except Exception:
			logging.exception(f"Failed to find artist MBID for: {artist}")
			prefs.failed_background_artists.append(artist)
			return None

		# Search fanart.tv for background
		try:

			r = requests.get(
				"https://webservice.fanart.tv/v3/music/" \
				+ artist_id + "?api_key=" + prefs.fatvap, timeout=(4, 10))

			artlink = r.json()["artistbackground"][0]["url"]

			response = urllib.request.urlopen(artlink, context=ssl_context)
			info = response.info()

			assert info.get_content_maintype() == "image"

			t = io.BytesIO()
			t.seek(0)
			t.write(response.read())
			t.seek(0, 2)
			l = t.tell()
			t.seek(0)

			assert l > 1000

			# Cache image for future use
			path = os.path.join(a_cache_dir, artist + "-ftv-full.jpg")
			with open(path, "wb") as f:
				f.write(t.read())
			t.seek(0)
			return t

		except Exception:
			logging.exception(f"Failed to find fanart background for: {artist}")
			if not gui.artist_info_panel:
				artist_info_box.get_data(artist)
				path = artist_info_box.get_data(artist, get_img_path=True)
				if os.path.isfile(path):
					logging.debug("Downloaded background lfm")
					return open(path, "rb")


			prefs.failed_background_artists.append(artist)
			return None

	def get_blur_im(self, track: TrackClass) -> BytesIO | bool | None:

		source_image = None
		self.loaded_bg_type = 0
		if prefs.enable_fanart_bg:
			source_image = self.get_background(track)
			if source_image:
				self.loaded_bg_type = 1

		if source_image is None:
			filepath = track.fullpath
			sources = self.get_sources(track)

			if len(sources) == 0:
				return False

			offset = self.get_offset(filepath, sources)

			source_image = self.get_source_raw(offset, sources, track)

		if source_image is None:
			return None

		im = Image.open(source_image)

		ox_size = im.size[0]
		oy_size = im.size[1]

		format = im.format
		if im.format == "JPEG":
			format = "JPG"

		#logging.info(im.size)
		if im.mode != "RGB":
			im = im.convert("RGB")

		ratio = window_size[0] / ox_size
		ratio += 0.2

		if (oy_size * ratio) - ((oy_size * ratio) // 4) < window_size[1]:
			logging.info("Adjust bg vertical")
			ratio = window_size[1] / (oy_size - (oy_size // 4))
			ratio += 0.2

		new_x = round(ox_size * ratio)
		new_y = round(oy_size * ratio)

		im = im.resize((new_x, new_y))

		if self.loaded_bg_type == 1:
			artist = get_artist_safe(track)
			if artist and artist in prefs.bg_flips:
				im = im.transpose(Image.FLIP_LEFT_RIGHT)

		if (ox_size < 500 or prefs.art_bg_always_blur) or gui.mode == 3:
			blur = prefs.art_bg_blur
			if prefs.mini_mode_mode == 5 and gui.mode == 3:
				blur = 160
				pix = im.getpixel((new_x // 2, new_y // 4 * 3))
				pixel_sum = sum(pix) / (255 * 3)
				if pixel_sum > 0.6:
					enhancer = ImageEnhance.Brightness(im)
					deduct = 1 - ((pixel_sum - 0.6) * 1.5)
					im = enhancer.enhance(deduct)
					logging.info(deduct)

				gui.center_blur_pixel = im.getpixel((new_x // 2, new_y // 4 * 3))

			im = im.filter(ImageFilter.GaussianBlur(blur))


		gui.center_blur_pixel = im.getpixel((new_x // 2, new_y // 2))

		g = io.BytesIO()
		g.seek(0)

		a_channel = Image.new("L", im.size, 255)  # 'L' 8-bit pixels, black and white
		im.putalpha(a_channel)

		im.save(g, "PNG")
		g.seek(0)

		# source_image.close()

		return g

	def save_thumb(self, track_object: TrackClass, size: tuple[int, int], save_path: str, png=False, zoom=False):

		filepath = track_object.fullpath
		sources = self.get_sources(track_object)

		if len(sources) == 0:
			logging.error("Error thumbnailing; no source images found")
			return False

		offset = self.get_offset(filepath, sources)
		source_image = self.get_source_raw(offset, sources, track_object)

		im = Image.open(source_image)
		if im.mode != "RGB":
			im = im.convert("RGB")

		if not zoom:
			im.thumbnail(size, Image.Resampling.LANCZOS)
		else:
			w, h = im.size
			if w != h:
				m = min(w, h)
				im = im.crop((
					(w - m) / 2,
					(h - m) / 2,
					(w + m) / 2,
					(h + m) / 2,
				))

			im = im.resize(size, Image.Resampling.LANCZOS)

		if not save_path:
			g = io.BytesIO()
			g.seek(0)
			if png:
				im.save(g, "PNG")
			else:
				im.save(g, "JPEG")
			g.seek(0)
			return g

		if png:
			im.save(save_path + ".png", "PNG")
		else:
			im.save(save_path + ".jpg", "JPEG")

	def display(self, track: TrackClass, location, box, fast: bool = False, theme_only: bool = False) -> int | None:
		index = track.index
		filepath = track.fullpath

		if prefs.colour_from_image and track.album != gui.theme_temp_current and box[0] != 115:
			if track.album in gui.temp_themes:
				global colours
				colours = gui.temp_themes[track.album]
				gui.theme_temp_current = track.album

		source = self.get_sources(track)

		if len(source) == 0:
			return 1

		offset = self.get_offset(filepath, source)

		if not theme_only:
			# Check if request matches previous
			if self.current_wu is not None and self.current_wu.source == source[offset][1] and \
					self.current_wu.request_size == box:
				self.render(self.current_wu, location)
				return 0

			if fast:
				return self.fast_display(track, location, box, source, offset)

			# Check if cached
			for unit in self.image_cache:
				if unit.index == index and unit.request_size == box and unit.offset == offset:
					self.render(unit, location)
					return 0

		close = True
		# Render new
		try:
			# Get source IO
			if source[offset][0] == 1:
				# Target is a embedded image
				# source_image = io.BytesIO(self.get_embed(track))
				source_image = self.get_source_raw(0, 0, track, source[offset])

			elif source[offset][0] == 2:
				idea = prefs.encoder_output / encode_folder_name(track) / "cover.jpg"
				if idea.is_file():
					source_image = idea.open("rb")
				else:
					try:
						close = False
						# We want to download the image asynchronously as to not block the UI
						if self.downloaded_image and self.downloaded_track == track:
							source_image = self.downloaded_image

						elif self.download_in_progress:
							return 0

						else:
							self.download_in_progress = True
							shoot_dl = threading.Thread(
								target=self.async_download_image,
								args=([track, source[offset]]))
							shoot_dl.daemon = True
							shoot_dl.start()

							# We'll block with a small timeout to avoid unwanted flashing between frames
							s = 0
							while self.download_in_progress:
								s += 1
								time.sleep(0.01)
								if s > 20:  # 200 ms
									break

							if self.downloaded_track != track:
								return None

							assert self.downloaded_image
							source_image = self.downloaded_image


					except Exception:
						logging.exception("IMAGE NETWORK LOAD ERROR")
						raise

			else:
				# source_image = open(source[offset][1], 'rb')
				source_image = self.get_source_raw(0, 0, track, source[offset])

			# Generate
			g = io.BytesIO()
			g.seek(0)
			im = Image.open(source_image)
			o_size = im.size

			format = im.format

			try:
				if im.format == "JPEG":
					format = "JPG"

				if im.mode != "RGB":
					im = im.convert("RGB")
			except Exception:
				logging.exception("Failed to convert image")
				if theme_only:
					source_image.close()
					g.close()
					return None
				im = Image.open(str(install_directory / "assets" / "load-error.png"))
				o_size = im.size


			if not theme_only:

				if prefs.zoom_art:
					new_size = fit_box(o_size, box)
					try:
						im = im.resize(new_size, Image.Resampling.LANCZOS)
					except Exception:
						logging.exception("Failed to resize image")
						im = Image.open(str(install_directory / "assets" / "load-error.png"))
						o_size = im.size
						new_size = fit_box(o_size, box)
						im = im.resize(new_size, Image.Resampling.LANCZOS)
				else:
					try:
						im.thumbnail((box[0], box[1]), Image.Resampling.LANCZOS)
					except Exception:
						logging.exception("Failed to convert image to thumbnail")
						im = Image.open(str(install_directory / "assets" / "load-error.png"))
						o_size = im.size
						im.thumbnail((box[0], box[1]), Image.Resampling.LANCZOS)
				im.save(g, "BMP")
				g.seek(0)

			# Processing for "Carbon" theme
			if track == pctl.playing_object() and gui.theme_name == "Carbon" and track.parent_folder_path != colours.last_album:

				# Find main image colours
				try:
					im.thumbnail((50, 50), Image.Resampling.LANCZOS)
				except Exception:
					logging.exception("theme gen error")
					source_image.close()
					g.close()
					return None
				pixels = im.getcolors(maxcolors=2500)
				pixels = sorted(pixels, key=lambda x: x[0], reverse=True)[:]
				colour = pixels[0][1]

				# Try and find a colour that is not grayscale
				for c in pixels:
					cc = c[1]
					av = sum(cc) / 3
					if abs(cc[0] - av) > 10 or abs(cc[1] - av) > 10 or abs(cc[2] - av) > 10:
						colour = cc
						break

				h_colour = rgb_to_hls(colour[0], colour[1], colour[2])

				l = .51
				s = .44

				hh = h_colour[0]
				if 0.14 < hh < 0.3:  # Yellow and green are hard to read text on, so lower the luminance for those
					l = .45
				if check_equal(colour):  # Default to theme purple if source colour was grayscale
					hh = 0.72

				colours.bottom_panel_colour = hls_to_rgb(hh, l, s)
				colours.last_album = track.parent_folder_path

			# Processing for "Auto-theme" setting
			if prefs.colour_from_image and box[0] != 115 and track.album != gui.theme_temp_current \
					and track.album not in gui.temp_themes:  # and pctl.master_library[index].parent_folder_path != colours.last_album: #mark2233
				colours.last_album = track.parent_folder_path

				colours = copy.deepcopy(colours)

				im.thumbnail((50, 50), Image.Resampling.LANCZOS)
				pixels = im.getcolors(maxcolors=2500)
				#logging.info(pixels)
				pixels = sorted(pixels, key=lambda x: x[0], reverse=True)[:]
				#logging.info(pixels)

				min_colour_varience = 75

				x_colours = []
				for item in pixels:
					colour = item[1]
					for cc in x_colours:
						if abs(
							colour[0] - cc[0]) < min_colour_varience and abs(
							colour[1] - cc[1]) < min_colour_varience and abs(
							colour[2] - cc[2]) < min_colour_varience:
							break
					else:
						x_colours.append(colour)

				#logging.info(x_colours)
				colours.playlist_panel_bg = colours.side_panel_background
				colours.playlist_box_background = colours.side_panel_background

				colours.playlist_panel_background = x_colours[0] + (255,)
				if len(x_colours) > 1:
					colours.side_panel_background = x_colours[1] + (255,)
					colours.playlist_box_background = colours.side_panel_background
					if len(x_colours) > 2:
						colours.title_text = x_colours[2] + (255,)
						colours.title_playing = x_colours[2] + (255,)
						if len(x_colours) > 3:
							colours.artist_text = x_colours[3] + (255,)
							colours.artist_playing = x_colours[3] + (255,)
							if len(x_colours) > 4:
								colours.playlist_box_background = x_colours[4] + (255,)

				colours.queue_background = colours.side_panel_background
				# Check artist text colour
				if contrast_ratio(colours.artist_text, colours.playlist_panel_background) < 1.9:

					black = [25, 25, 25, 255]
					white = [220, 220, 220, 255]

					con_b = contrast_ratio(black, colours.playlist_panel_background)
					con_w = contrast_ratio(white, colours.playlist_panel_background)

					choice = black
					if con_w > con_b:
						choice = white

					colours.artist_text = choice
					colours.artist_playing = choice

				# Check title text colour
				if contrast_ratio(colours.title_text, colours.playlist_panel_background) < 1.9:

					black = [60, 60, 60, 255]
					white = [180, 180, 180, 255]

					con_b = contrast_ratio(black, colours.playlist_panel_background)
					con_w = contrast_ratio(white, colours.playlist_panel_background)

					choice = black
					if con_w > con_b:
						choice = white

					colours.title_text = choice
					colours.title_playing = choice

				if test_lumi(colours.side_panel_background) < 0.50:
					colours.side_bar_line1 = [25, 25, 25, 255]
					colours.side_bar_line2 = [35, 35, 35, 255]
				else:
					colours.side_bar_line1 = [250, 250, 250, 255]
					colours.side_bar_line2 = [235, 235, 235, 255]

				colours.album_text = colours.title_text
				colours.album_playing = colours.title_playing

				gui.pl_update = 1

				prcl = 100 - int(test_lumi(colours.playlist_panel_background) * 100)

				if prcl > 45:
					ce = alpha_blend([0, 0, 0, 180], colours.playlist_panel_background)  # [40, 40, 40, 255]
					colours.index_text = ce
					colours.index_playing = ce
					colours.time_text = ce
					colours.bar_time = ce
					colours.folder_title = ce
					colours.star_line = [60, 60, 60, 255]
					colours.row_select_highlight = [0, 0, 0, 30]
					colours.row_playing_highlight = [0, 0, 0, 20]
					colours.gallery_background = rgb_add_hls(colours.playlist_panel_background, 0, -0.03, -0.03)
				else:
					ce = alpha_blend([255, 255, 255, 160], colours.playlist_panel_background)  # [165, 165, 165, 255]
					colours.index_text = ce
					colours.index_playing = ce
					colours.time_text = ce
					colours.bar_time = ce
					colours.folder_title = ce
					colours.star_line = ce  # [150, 150, 150, 255]
					colours.row_select_highlight = [255, 255, 255, 12]
					colours.row_playing_highlight = [255, 255, 255, 8]
					colours.gallery_background = rgb_add_hls(colours.playlist_panel_background, 0, 0.03, 0.03)

				gui.temp_themes[track.album] = copy.deepcopy(colours)
				colours = gui.temp_themes[track.album]
				gui.theme_temp_current = track.album

			if theme_only:
				source_image.close()
				g.close()
				return None

			wop = rw_from_object(g)
			s_image = IMG_Load_RW(wop, 0)
			#logging.error(IMG_GetError())

			c = SDL_CreateTextureFromSurface(renderer, s_image)

			tex_w = pointer(c_int(0))
			tex_h = pointer(c_int(0))

			SDL_QueryTexture(c, None, None, tex_w, tex_h)

			dst = SDL_Rect(round(location[0]), round(location[1]))
			dst.w = int(tex_w.contents.value)
			dst.h = int(tex_h.contents.value)

			# Clean uo
			SDL_FreeSurface(s_image)
			source_image.close()
			g.close()
			# if close:
			#	 source_image.close()

			unit = ImageObject()
			unit.index = index
			unit.texture = c
			unit.rect = dst
			unit.request_size = box
			unit.original_size = o_size
			unit.actual_size = (dst.w, dst.h)
			unit.source = source[offset][1]
			unit.offset = offset
			unit.format = format

			self.current_wu = unit
			self.image_cache.append(unit)

			self.render(unit, location)

			if len(self.image_cache) > 5 or (prefs.colour_from_image and len(self.image_cache) > 1):
				SDL_DestroyTexture(self.image_cache[0].texture)
				del self.image_cache[0]

			# temp fix
			global move_on_title
			global playlist_hold
			global quick_drag
			quick_drag = False
			move_on_title = False
			playlist_hold = False

		except Exception:
			logging.exception("Image load error")
			logging.error("-- Associated track: " + track.fullpath)

			self.current_wu = None
			try:
				del self.source_cache[index][offset]
			except Exception:
				logging.exception(" -- Error, no source cache?")

			return 1

		return 0

	def render(self, unit, location) -> None:

		rect = unit.rect

		gui.art_aspect_ratio = unit.actual_size[0] / unit.actual_size[1]

		rect.x = round(int((unit.request_size[0] - unit.actual_size[0]) / 2) + location[0])
		rect.y = round(int((unit.request_size[1] - unit.actual_size[1]) / 2) + location[1])

		style_overlay.hole_punches.append(rect)

		SDL_RenderCopy(renderer, unit.texture, None, rect)

		gui.art_drawn_rect = (rect.x, rect.y, rect.w, rect.h)

	def clear_cache(self) -> None:

		for unit in self.image_cache:
			SDL_DestroyTexture(unit.texture)

		self.image_cache.clear()
		self.source_cache.clear()
		self.current_wu = None
		self.downloaded_track = None

		self.base64cahce = (0, 0, "")
		self.processing64on = None
		self.bin_cached = (None, None, None)
		self.loading_bin = (None, None)
		self.embed_cached = (None, None)

		gui.temp_themes.clear()
		gui.theme_temp_current = -1
		colours.last_album = ""

class StyleOverlay:

	def __init__(self):

		self.min_on_timer = Timer()
		self.fade_on_timer = Timer(0)
		self.fade_off_timer = Timer()

		self.stage = 0

		self.im = None

		self.a_texture = None
		self.a_rect = None

		self.b_texture = None
		self.b_rect = None

		self.a_type = 0
		self.b_type = 0

		self.window_size = None
		self.parent_path = None

		self.hole_punches = []
		self.hole_refills = []

		self.go_to_sleep = False

		self.current_track_album = "none"
		self.current_track_id = -1

	def worker(self) -> None:

		if self.stage == 0:

			if (gui.mode == 3 and prefs.mini_mode_mode == 5):
				pass
			elif prefs.bg_showcase_only and not gui.combo_mode:
				return

			if pctl.playing_ready() and self.min_on_timer.get() > 0:

				track = pctl.playing_object()

				self.window_size = copy.copy(window_size)
				self.parent_path = track.parent_folder_path
				self.current_track_id = track.index
				self.current_track_album = track.album

				try:
					self.im = album_art_gen.get_blur_im(track)
				except Exception:
					logging.exception("Blur blackground error")
					raise
					#logging.debug(track.fullpath)

				if self.im is None or self.im is False:
					if self.a_texture:
						self.stage = 2
						self.fade_off_timer.set()
						self.go_to_sleep = True
						return
					self.flush()
					self.min_on_timer.force_set(-4)
					return

				self.stage = 1
				gui.update += 1
				return

	def flush(self):

		if self.a_texture is not None:
			SDL_DestroyTexture(self.a_texture)
			self.a_texture = None
		if self.b_texture is not None:
			SDL_DestroyTexture(self.b_texture)
			self.b_texture = None
		self.min_on_timer.force_set(-0.2)
		self.parent_path = "None"
		self.stage = 0
		tauon.thread_manager.ready("worker")
		gui.style_worker_timer.set()
		gui.delay_frame(0.25)
		gui.update += 1

	def display(self) -> None:

		if self.min_on_timer.get() < 0:
			return

		if self.stage == 1:

			wop = rw_from_object(self.im)
			s_image = IMG_Load_RW(wop, 0)

			c = SDL_CreateTextureFromSurface(renderer, s_image)

			tex_w = pointer(c_int(0))
			tex_h = pointer(c_int(0))

			SDL_QueryTexture(c, None, None, tex_w, tex_h)

			dst = SDL_Rect(round(-40, 0))
			dst.w = int(tex_w.contents.value)
			dst.h = int(tex_h.contents.value)

			# Clean uo
			SDL_FreeSurface(s_image)
			self.im.close()

			# SDL_SetTextureAlphaMod(c, 10)
			self.fade_on_timer.set()

			if self.a_texture is not None:
				self.b_texture = self.a_texture
				self.b_rect = self.a_rect
				self.b_type = self.a_type

			self.a_texture = c
			self.a_rect = dst
			self.a_type = album_art_gen.loaded_bg_type

			self.stage = 2
			self.radio_meta = None

			gui.update += 1

		if self.stage == 2:
			track = pctl.playing_object()

			if pctl.playing_state == 3 and not tauon.spot_ctl.coasting:
				if self.radio_meta != pctl.tag_meta:
					self.radio_meta = pctl.tag_meta
					self.current_track_id = -1
					self.stage = 0

			elif not self.go_to_sleep and self.b_texture is None and self.current_track_id != track.index:
				self.radio_meta = None
				if not track.album:
					self.stage = 0
				else:
					self.current_track_id = track.index
					if (
							self.parent_path != pctl.playing_object().parent_folder_path or self.current_track_album != pctl.playing_object().album):
						self.stage = 0

		if gui.mode == 3 and prefs.mini_mode_mode == 5:
			pass
		elif prefs.bg_showcase_only:
			if not gui.combo_mode:
				return

		t = self.fade_on_timer.get()
		SDL_SetRenderTarget(renderer, gui.main_texture_overlay_temp)
		SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
		SDL_RenderClear(renderer)

		if self.a_texture is not None:
			if self.window_size != window_size:
				self.flush()

		if self.b_texture is not None:

			self.b_rect.y = 0 - self.b_rect.h // 4
			if self.b_type == 1:
				self.b_rect.y = 0

			if t < 0.4:

				SDL_RenderCopy(renderer, self.b_texture, None, self.b_rect)

			else:
				SDL_DestroyTexture(self.b_texture)
				self.b_texture = None
				self.b_rect = None

		if self.a_texture is not None:

			self.a_rect.y = 0 - self.a_rect.h // 4
			if self.a_type == 1:
				self.a_rect.y = 0

			if t < 0.4:
				fade = round(t / 0.4 * 255)
				gui.update += 1

			else:
				fade = 255

			if self.go_to_sleep:
				t = self.fade_off_timer.get()
				gui.update += 1

				if t < 1:
					fade = 255
				elif t < 1.4:
					fade = 255 - round((t - 1) / 0.4 * 255)
				else:
					self.go_to_sleep = False
					self.flush()
					return

			if prefs.bg_showcase_only and not (prefs.mini_mode_mode == 5 and gui.mode == 3):
				tb = SDL_Rect(0, 0, window_size[0], gui.panelY)
				bb = SDL_Rect(0, window_size[1] - gui.panelBY, window_size[0], gui.panelBY)
				self.hole_punches.append(tb)
				self.hole_punches.append(bb)

			# Center image
			if window_size[0] < 900 * gui.scale:
				self.a_rect.x = (window_size[0] // 2) - self.a_rect.w // 2
			else:
				self.a_rect.x = -40

			SDL_SetRenderTarget(renderer, gui.main_texture_overlay_temp)

			SDL_SetTextureAlphaMod(self.a_texture, fade)
			SDL_RenderCopy(renderer, self.a_texture, None, self.a_rect)

			SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_NONE)

			SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
			for rect in self.hole_punches:
				SDL_RenderFillRect(renderer, rect)

			SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND)

			SDL_SetRenderTarget(renderer, gui.main_texture)
			opacity = prefs.art_bg_opacity
			if prefs.mini_mode_mode == 5 and gui.mode == 3:
				opacity = 255

			SDL_SetTextureAlphaMod(gui.main_texture_overlay_temp, opacity)
			SDL_RenderCopy(renderer, gui.main_texture_overlay_temp, None, None)

			SDL_SetRenderTarget(renderer, gui.main_texture)

		else:
			SDL_SetRenderTarget(renderer, gui.main_texture)

class ToolTip:

	def __init__(self) -> None:
		self.text = ""
		self.h = 24 * gui.scale
		self.w = 62 * gui.scale
		self.x = 0
		self.y = 0
		self.timer = Timer()
		self.trigger = 1.1
		self.font = 13
		self.called = False
		self.a = False

	def test(self, x, y, text):

		if self.text != text or x != self.x or y != self.y:
			self.text = text
			# self.timer.set()
			self.a = False

			self.x = x
			self.y = y
			self.w = ddt.get_text_w(text, self.font) + 20 * gui.scale

		self.called = True

		if self.a is False:
			self.timer.set()
			gui.frame_callback_list.append(TestTimer(self.trigger))
		self.a = True

	def render(self) -> None:

		if self.called is True:

			if self.timer.get() > self.trigger:

				ddt.rect((self.x, self.y, self.w, self.h), colours.box_button_background)
				# ddt.rect((self.x, self.y, self.w, self.h), colours.grey(45))
				ddt.text(
					(self.x + int(self.w / 2), self.y + 4 * gui.scale, 2), self.text,
					colours.menu_text, self.font, bg=colours.box_button_background)
			else:
				# gui.update += 1
				pass
		else:
			self.timer.set()
			self.a = False

		self.called = False

class ToolTip3:

	def __init__(self) -> None:
		self.x = 0
		self.y = 0
		self.text = ""
		self.font = None
		self.show = False
		self.width = 0
		self.height = 24 * gui.scale
		self.timer = Timer()
		self.pl_position = 0
		self.click_exclude_point = (0, 0)

	def set(self, x, y, text, font, rect):

		y -= round(11 * gui.scale)
		if self.show == False or self.y != y or x != self.x or self.pl_position != pctl.playlist_view_position:
			self.timer.set()

		if point_proximity_test(self.click_exclude_point, mouse_position, 20 * gui.scale):
			self.timer.set()
			return

		if inp.mouse_click:
			self.click_exclude_point = copy.copy(mouse_position)
			self.timer.set()
			return

		self.x = x
		self.y = y
		self.text = text
		self.font = font
		self.show = True
		self.rect = rect
		self.pl_position = pctl.playlist_view_position

	def render(self):

		if not self.show:
			return

		if not point_proximity_test(self.click_exclude_point, mouse_position, 20 * gui.scale):
			self.click_exclude_point = (0, 0)

		if not coll(
				self.rect) or inp.mouse_click or gui.level_2_click or self.pl_position != pctl.playlist_view_position:
			self.show = False

		gui.frame_callback_list.append(TestTimer(0.02))

		if self.timer.get() < 0.6:
			return

		w = ddt.get_text_w(self.text, 312) + self.height
		x = self.x  # - int(self.width / 2)
		y = self.y
		h = self.height

		border = 1 * gui.scale

		ddt.rect((x - border, y - border, w + border * 2, h + border * 2), colours.grey(60))
		ddt.rect((x, y, w, h), colours.menu_background)
		p = ddt.text(
			(x + int(w / 2), y + 3 * gui.scale, 2), self.text, colours.menu_text, 312, bg=colours.menu_background)

		if not coll(self.rect):
			self.show = False

class RenameTrackBox:

	def __init__(self):

		self.active = False
		self.target_track_id = None
		self.single_only = False

	def activate(self, track_id):

		self.active = True
		self.target_track_id = track_id
		if key_shift_down or key_shiftr_down:
			self.single_only = True
		else:
			self.single_only = False

	def disable_test(self, track_id):
		if key_shift_down or key_shiftr_down:
			single_only = True
		else:
			single_only = False

		if not single_only:
			for item in default_playlist:
				if pctl.master_library[item].parent_folder_path == pctl.master_library[track_id].parent_folder_path:

					if pctl.master_library[item].is_network is True:
						return True
		return False

	def render(self):

		if not self.active:
			return

		if gui.level_2_click:
			inp.mouse_click = True
		gui.level_2_click = False

		w = 420 * gui.scale
		h = 155 * gui.scale
		x = int(window_size[0] / 2) - int(w / 2)
		y = int(window_size[1] / 2) - int(h / 2)

		ddt.rect_a((x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale), colours.box_border)
		ddt.rect_a((x, y), (w, h), colours.box_background)
		ddt.text_background_colour = colours.box_background

		if key_esc_press or ((inp.mouse_click or right_click or level_2_right_click) and not coll((x, y, w, h))):
			rename_track_box.active = False

		r_todo = []

		# Find matching folder tracks in playlist
		if not self.single_only:
			for item in default_playlist:
				if pctl.master_library[item].parent_folder_path == pctl.master_library[
					self.target_track_id].parent_folder_path:

					# Close and display error if any tracks are not single local files
					if pctl.master_library[item].is_network is True:
						rename_track_box.active = False
						show_message(_("Cannot rename"), _("One or more tracks is from a network location!"), mode="info")
					if pctl.master_library[item].is_cue is True:
						rename_track_box.active = False
						show_message(_("This function does not support renaming CUE Sheet tracks."))
					else:
						r_todo.append(item)
		else:
			r_todo = [self.target_track_id]

		ddt.text((x + 10 * gui.scale, y + 8 * gui.scale), _("Track Renaming"), colours.grey(230), 213)

		# if draw.button("Default", x + 230 * gui.scale, y + 8 * gui.scale,
		if rename_files.text != prefs.rename_tracks_template and draw.button(
			_("Default"), x + w - 85 * gui.scale, y + h - 35 * gui.scale, 70 * gui.scale):
			rename_files.text = prefs.rename_tracks_template

		# ddt.draw_text((x + 14, y + 40,), NRN + cursor, colours.grey(150), 12)
		rename_files.draw(x + 14 * gui.scale, y + 39 * gui.scale, colours.box_input_text, width=300)
		NRN = rename_files.text

		ddt.rect_s(
			(x + 8 * gui.scale, y + 36 * gui.scale, 300 * gui.scale, 22 * gui.scale), colours.box_text_border, 1 * gui.scale)

		afterline = ""
		warn = False
		underscore = False

		for item in r_todo:

			if pctl.master_library[item].track_number == "" or pctl.master_library[item].artist == "" or \
					pctl.master_library[item].title == "" or pctl.master_library[item].album == "":
				warn = True

			if item == self.target_track_id:
				afterline = parse_template2(NRN, pctl.master_library[item])

		ddt.text((x + 10 * gui.scale, y + 68 * gui.scale), _("BEFORE"), colours.box_text_label, 212)
		line = trunc_line(pctl.master_library[self.target_track_id].filename, 12, 335)
		ddt.text((x + 70 * gui.scale, y + 68 * gui.scale), line, colours.grey(210), 211, max_w=340)

		ddt.text((x + 10 * gui.scale, y + 83 * gui.scale), _("AFTER"), colours.box_text_label, 212)
		ddt.text((x + 70 * gui.scale, y + 83 * gui.scale), afterline, colours.grey(210), 211, max_w=340)

		if (len(NRN) > 3 and len(pctl.master_library[self.target_track_id].filename) > 3 and afterline[-3:].lower() !=
			pctl.master_library[self.target_track_id].filename[-3:].lower()) or len(NRN) < 4 or "." not in afterline[-5:]:
			ddt.text(
				(x + 10 * gui.scale, y + 108 * gui.scale), _("Warning: This may change the file extension"),
				[245, 90, 90, 255],
				13)

		colour_warn = [143, 186, 65, 255]
		if not unique_template(NRN):
			ddt.text(
				(x + 10 * gui.scale, y + 123 * gui.scale), _("Warning: The filename might not be unique"),
				[245, 90, 90, 255],
				13)
		if warn:
			ddt.text(
				(x + 10 * gui.scale, y + 135 * gui.scale), _("Warning: A track has incomplete metadata"),
				[245, 90, 90, 255],
				13)
			colour_warn = [180, 60, 60, 255]

		label = _("Write") + " (" + str(len(r_todo)) + ")"

		if draw.button(
			label, x + (8 + 300 + 10) * gui.scale, y + 36 * gui.scale, 80 * gui.scale,
			text_highlight_colour=colours.grey(255), background_highlight_colour=colour_warn,
			tooltip=_("Physically renames all the tracks in the folder")) or inp.level_2_enter:

			inp.mouse_click = False
			total_todo = len(r_todo)
			pre_state = 0

			for item in r_todo:

				if pctl.playing_state > 0 and item == pctl.track_queue[pctl.queue_step]:
					pre_state = pctl.stop(True)

				try:

					afterline = parse_template2(NRN, pctl.master_library[item], strict=True)

					oldname = pctl.master_library[item].filename
					oldpath = pctl.master_library[item].fullpath

					logging.info("Renaming...")

					star = star_store.full_get(item)
					star_store.remove(item)

					oldpath = pctl.master_library[item].fullpath

					oldsplit = os.path.split(oldpath)

					if os.path.exists(os.path.join(oldsplit[0], afterline)):
						logging.error("A file with that name already exists")
						total_todo -= 1
						continue

					if not afterline:
						logging.error("Rename Error")
						total_todo -= 1
						continue

					if "." in afterline and not afterline.split(".")[0]:
						logging.error("A file does not have a target filename")
						total_todo -= 1
						continue

					os.rename(pctl.master_library[item].fullpath, os.path.join(oldsplit[0], afterline))

					pctl.master_library[item].fullpath = os.path.join(oldsplit[0], afterline)
					pctl.master_library[item].filename = afterline

					search_string_cache.pop(item, None)
					search_dia_string_cache.pop(item, None)

					if star is not None:
						star_store.insert(item, star)

				except Exception:
					logging.exception("Rendering error")
					total_todo -= 1

			rename_track_box.active = False
			logging.info("Done")
			if pre_state == 1:
				pctl.revert()

			if total_todo != len(r_todo):
				show_message(
					_("Rename complete."),
					_("{N} / {T} filenames were written.")
					.format(N=str(total_todo), T=str(len(r_todo))), mode="warning")
			else:
				show_message(
					_("Rename complete."),
					_("{N} / {T} filenames were written.")
					.format(N=str(total_todo), T=str(len(r_todo))), mode="done")
			pctl.notify_change()

class TransEditBox:

	def __init__(self):
		self.active = False
		self.active_field = 1
		self.selected = []
		self.playlist = -1

	def render(self):

		if not self.active:
			return

		if gui.level_2_click:
			inp.mouse_click = True
		gui.level_2_click = False

		w = 500 * gui.scale
		h = 255 * gui.scale
		x = int(window_size[0] / 2) - int(w / 2)
		y = int(window_size[1] / 2) - int(h / 2)

		ddt.rect_a((x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale), colours.box_border)
		ddt.rect_a((x, y), (w, h), colours.box_background)
		ddt.text_background_colour = colours.box_background

		if key_esc_press or ((inp.mouse_click or right_click or level_2_right_click) and not coll((x, y, w, h))):
			self.active = False

		select = list(set(shift_selection))
		if not select and pctl.selected_ready():
			select = [pctl.selected_in_playlist]

		titles = [pctl.get_track(default_playlist[s]).title for s in select]
		artists = [pctl.get_track(default_playlist[s]).artist for s in select]
		albums = [pctl.get_track(default_playlist[s]).album for s in select]
		album_artists = [pctl.get_track(default_playlist[s]).album_artist for s in select]

		#logging.info(select)
		if select != self.selected or pctl.active_playlist_viewing != self.playlist:
			#logging.info("reset")
			self.selected = select
			self.playlist = pctl.active_playlist_viewing
			edit_album.clear()
			edit_artist.clear()
			edit_title.clear()
			edit_album_artist.clear()

			if len(select) == 0:
				return

			tr = pctl.get_track(default_playlist[select[0]])
			edit_title.set_text(tr.title)

			if check_equal(artists):
				edit_artist.set_text(artists[0])

			if check_equal(albums):
				edit_album.set_text(albums[0])

			if check_equal(album_artists):
				edit_album_artist.set_text(album_artists[0])

		x += round(20 * gui.scale)
		y += round(18 * gui.scale)

		ddt.text((x, y), _("Simple tag editor"), colours.box_title_text, 215)

		if draw.button(_("?"), x + 440 * gui.scale, y):
			show_message(
				_("Press Enter in each field to apply its changes to local database."),
				_("When done, press WRITE TAGS to save to tags in actual files. (Optional but recommended)"),
				mode="info")

		y += round(24 * gui.scale)
		ddt.text((x, y), _("Number of tracks selected: {N}").format(N=len(select)), colours.box_title_text, 313)

		y += round(24 * gui.scale)

		if inp.key_tab_press:
			if key_shift_down or key_shiftr_down:
				self.active_field -= 1
			else:
				self.active_field += 1

		if self.active_field < 0:
			self.active_field = 3
		if self.active_field == 4:
			self.active_field = 0
			if len(select) > 1:
				self.active_field = 1

		def field_edit(x, y, label, field_number, names, text_box):
			changed = 0
			ddt.text((x, y), label, colours.box_text_label, 11)
			y += round(16 * gui.scale)
			rect1 = (x, y, round(370 * gui.scale), round(17 * gui.scale))
			fields.add(rect1)
			if (coll(rect1) and inp.mouse_click) or (inp.key_tab_press and self.active_field == field_number):
				self.active_field = field_number
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			tc = colours.box_input_text
			if names and check_equal(names) and text_box.text == names[0]:
				h, l, s = rgb_to_hls(tc[0], tc[1], tc[2])
				l *= 0.7
				tc = hls_to_rgb(h, l, s)
			else:
				changed = 1
			if not (names and check_equal(names)) and not text_box.text:
				changed = 0
				ddt.text((x + round(2 * gui.scale), y), _("<Multiple selected>"), colours.box_text_label, 12)
			text_box.draw(x + round(3 * gui.scale), y, tc, self.active_field == field_number, width=370 * gui.scale)
			if changed:
				ddt.text((x + 377 * gui.scale, y - 1 * gui.scale), "⮨", colours.box_title_text, 214)
			return changed

		changed = 0
		if len(select) == 1:
			changed = field_edit(x, y, _("Track title"), 0, titles, edit_title)
		y += round(40 * gui.scale)
		changed += field_edit(x, y, _("Album name"), 1, albums, edit_album)
		y += round(40 * gui.scale)
		changed += field_edit(x, y, _("Artist name"), 2, artists, edit_artist)
		y += round(40 * gui.scale)
		changed += field_edit(x, y, _("Album-artist name"), 3, album_artists, edit_album_artist)

		y += round(40 * gui.scale)
		for s in select:
			tr = pctl.get_track(default_playlist[s])
			if tr.is_network:
				ddt.text((x, y), _("Editing network tracks is not recommended!"), [245, 90, 90, 255], 312)

		if inp.key_return_press:

			gui.pl_update += 1
			if self.active_field == 0 and len(select) == 1:
				for s in select:
					tr = pctl.get_track(default_playlist[s])
					star = star_store.full_get(tr.index)
					star_store.remove(tr.index)
					tr.title = edit_title.text
					star_store.merge(tr.index, star)

			if self.active_field == 1:
				for s in select:
					tr = pctl.get_track(default_playlist[s])
					tr.album = edit_album.text
			if self.active_field == 2:
				for s in select:
					tr = pctl.get_track(default_playlist[s])
					star = star_store.full_get(tr.index)
					star_store.remove(tr.index)
					tr.artist = edit_artist.text
					star_store.merge(tr.index, star)
			if self.active_field == 3:
				for s in select:
					tr = pctl.get_track(default_playlist[s])
					tr.album_artist = edit_album_artist.text
			tauon.bg_save()


		ww = ddt.get_text_w(_("WRITE TAGS"), 212) + round(48 * gui.scale)
		if gui.write_tag_in_progress:
			text = f"{gui.tag_write_count}/{len(select)}"
		text = _("WRITE TAGS")
		if draw.button(text, (x + w) - ww, y - round(0) * gui.scale):
			if changed:
				show_message(_("Press enter on fields to apply your changes first!"))
				return

			if gui.write_tag_in_progress:
				return

			def write_tag_go():


				for s in select:
					tr = pctl.get_track(default_playlist[s])

					if tr.is_network:
						show_message(_("Writing to a network track is not applicable!"), mode="error")
						gui.write_tag_in_progress = True
						return
					if tr.is_cue:
						show_message(_("Cannot write CUE sheet types!"), mode="error")
						gui.write_tag_in_progress = True
						return

					muta = mutagen.File(tr.fullpath, easy=True)

					def write_tag(track: TrackClass, muta, field_name_tauon, field_name_muta):
						item = muta.get(field_name_muta)
						if item and len(item) > 1:
							show_message(_("Cannot handle multi-field! Please use external tag editor"), mode="error")
							return 0
						if not getattr(tr, field_name_tauon):  # Want delete tag field
							if item:
								del muta[field_name_muta]
						else:
							muta[field_name_muta] = getattr(tr, field_name_tauon)
						return 1

					write_tag(tr, muta, "artist", "artist")
					write_tag(tr, muta, "album", "album")
					write_tag(tr, muta, "title", "title")
					write_tag(tr, muta, "album_artist", "albumartist")

					muta.save()
					gui.tag_write_count += 1
					gui.update += 1
				tauon.bg_save()
				if not gui.message_box:
					show_message(_("{N} files rewritten").format(N=gui.tag_write_count), mode="done")
				gui.write_tag_in_progress = False
			if not gui.write_tag_in_progress:
				gui.tag_write_count = 0
				gui.write_tag_in_progress = True
				shooter(write_tag_go)

class TransEditBox:

	def __init__(self):
		self.active = False
		self.active_field = 1
		self.selected = []
		self.playlist = -1

	def render(self):

		if not self.active:
			return

		if gui.level_2_click:
			inp.mouse_click = True
		gui.level_2_click = False

		w = 500 * gui.scale
		h = 255 * gui.scale
		x = int(window_size[0] / 2) - int(w / 2)
		y = int(window_size[1] / 2) - int(h / 2)

		ddt.rect_a((x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale), colours.box_border)
		ddt.rect_a((x, y), (w, h), colours.box_background)
		ddt.text_background_colour = colours.box_background

		if key_esc_press or ((inp.mouse_click or right_click or level_2_right_click) and not coll((x, y, w, h))):
			self.active = False

		select = list(set(shift_selection))
		if not select and pctl.selected_ready():
			select = [pctl.selected_in_playlist]

		titles = [pctl.get_track(default_playlist[s]).title for s in select]
		artists = [pctl.get_track(default_playlist[s]).artist for s in select]
		albums = [pctl.get_track(default_playlist[s]).album for s in select]
		album_artists = [pctl.get_track(default_playlist[s]).album_artist for s in select]

		#logging.info(select)
		if select != self.selected or pctl.active_playlist_viewing != self.playlist:
			#logging.info("reset")
			self.selected = select
			self.playlist = pctl.active_playlist_viewing
			edit_album.clear()
			edit_artist.clear()
			edit_title.clear()
			edit_album_artist.clear()

			if len(select) == 0:
				return

			tr = pctl.get_track(default_playlist[select[0]])
			edit_title.set_text(tr.title)

			if check_equal(artists):
				edit_artist.set_text(artists[0])

			if check_equal(albums):
				edit_album.set_text(albums[0])

			if check_equal(album_artists):
				edit_album_artist.set_text(album_artists[0])

		x += round(20 * gui.scale)
		y += round(18 * gui.scale)

		ddt.text((x, y), _("Simple tag editor"), colours.box_title_text, 215)

		if draw.button(_("?"), x + 440 * gui.scale, y):
			show_message(
				_("Press Enter in each field to apply its changes to local database."),
				_("When done, press WRITE TAGS to save to tags in actual files. (Optional but recommended)"),
				mode="info")

		y += round(24 * gui.scale)
		ddt.text((x, y), _("Number of tracks selected: {N}").format(N=len(select)), colours.box_title_text, 313)

		y += round(24 * gui.scale)

		if inp.key_tab_press:
			if key_shift_down or key_shiftr_down:
				self.active_field -= 1
			else:
				self.active_field += 1

		if self.active_field < 0:
			self.active_field = 3
		if self.active_field == 4:
			self.active_field = 0
			if len(select) > 1:
				self.active_field = 1

		def field_edit(x, y, label, field_number, names, text_box):
			changed = 0
			ddt.text((x, y), label, colours.box_text_label, 11)
			y += round(16 * gui.scale)
			rect1 = (x, y, round(370 * gui.scale), round(17 * gui.scale))
			fields.add(rect1)
			if (coll(rect1) and inp.mouse_click) or (inp.key_tab_press and self.active_field == field_number):
				self.active_field = field_number
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			tc = colours.box_input_text
			if names and check_equal(names) and text_box.text == names[0]:
				h, l, s = rgb_to_hls(tc[0], tc[1], tc[2])
				l *= 0.7
				tc = hls_to_rgb(h, l, s)
			else:
				changed = 1
			if not (names and check_equal(names)) and not text_box.text:
				changed = 0
				ddt.text((x + round(2 * gui.scale), y), _("<Multiple selected>"), colours.box_text_label, 12)
			text_box.draw(x + round(3 * gui.scale), y, tc, self.active_field == field_number, width=370 * gui.scale)
			if changed:
				ddt.text((x + 377 * gui.scale, y - 1 * gui.scale), "⮨", colours.box_title_text, 214)
			return changed

		changed = 0
		if len(select) == 1:
			changed = field_edit(x, y, _("Track title"), 0, titles, edit_title)
		y += round(40 * gui.scale)
		changed += field_edit(x, y, _("Album name"), 1, albums, edit_album)
		y += round(40 * gui.scale)
		changed += field_edit(x, y, _("Artist name"), 2, artists, edit_artist)
		y += round(40 * gui.scale)
		changed += field_edit(x, y, _("Album-artist name"), 3, album_artists, edit_album_artist)

		y += round(40 * gui.scale)
		for s in select:
			tr = pctl.get_track(default_playlist[s])
			if tr.is_network:
				ddt.text((x, y), _("Editing network tracks is not recommended!"), [245, 90, 90, 255], 312)

		if inp.key_return_press:

			gui.pl_update += 1
			if self.active_field == 0 and len(select) == 1:
				for s in select:
					tr = pctl.get_track(default_playlist[s])
					star = star_store.full_get(tr.index)
					star_store.remove(tr.index)
					tr.title = edit_title.text
					star_store.merge(tr.index, star)

			if self.active_field == 1:
				for s in select:
					tr = pctl.get_track(default_playlist[s])
					tr.album = edit_album.text
			if self.active_field == 2:
				for s in select:
					tr = pctl.get_track(default_playlist[s])
					star = star_store.full_get(tr.index)
					star_store.remove(tr.index)
					tr.artist = edit_artist.text
					star_store.merge(tr.index, star)
			if self.active_field == 3:
				for s in select:
					tr = pctl.get_track(default_playlist[s])
					tr.album_artist = edit_album_artist.text
			tauon.bg_save()


		ww = ddt.get_text_w(_("WRITE TAGS"), 212) + round(48 * gui.scale)
		if gui.write_tag_in_progress:
			text = f"{gui.tag_write_count}/{len(select)}"
		text = _("WRITE TAGS")
		if draw.button(text, (x + w) - ww, y - round(0) * gui.scale):
			if changed:
				show_message(_("Press enter on fields to apply your changes first!"))
				return

			if gui.write_tag_in_progress:
				return

			def write_tag_go():


				for s in select:
					tr = pctl.get_track(default_playlist[s])

					if tr.is_network:
						show_message(_("Writing to a network track is not applicable!"), mode="error")
						gui.write_tag_in_progress = True
						return
					if tr.is_cue:
						show_message(_("Cannot write CUE sheet types!"), mode="error")
						gui.write_tag_in_progress = True
						return

					muta = mutagen.File(tr.fullpath, easy=True)

					def write_tag(track: TrackClass, muta, field_name_tauon, field_name_muta):
						item = muta.get(field_name_muta)
						if item and len(item) > 1:
							show_message(_("Cannot handle multi-field! Please use external tag editor"), mode="error")
							return 0
						if not getattr(tr, field_name_tauon):  # Want delete tag field
							if item:
								del muta[field_name_muta]
						else:
							muta[field_name_muta] = getattr(tr, field_name_tauon)
						return 1

					write_tag(tr, muta, "artist", "artist")
					write_tag(tr, muta, "album", "album")
					write_tag(tr, muta, "title", "title")
					write_tag(tr, muta, "album_artist", "albumartist")

					muta.save()
					gui.tag_write_count += 1
					gui.update += 1
				tauon.bg_save()
				if not gui.message_box:
					show_message(_("{N} files rewritten").format(N=gui.tag_write_count), mode="done")
				gui.write_tag_in_progress = False
			if not gui.write_tag_in_progress:
				gui.tag_write_count = 0
				gui.write_tag_in_progress = True
				shooter(write_tag_go)

class SubLyricsBox:

	def __init__(self):

		self.active = False
		self.target_track = None
		self.active_field = 1

	def activate(self, track: TrackClass):

		self.active = True
		gui.box_over = True
		self.target_track = track

		sub_lyrics_a.text = prefs.lyrics_subs.get(self.target_track.artist, "")
		sub_lyrics_b.text = prefs.lyrics_subs.get(self.target_track.title, "")

		if not sub_lyrics_a.text:
			sub_lyrics_a.text = self.target_track.artist
		if not sub_lyrics_b.text:
			sub_lyrics_b.text = self.target_track.title

	def render(self):

		if not self.active:
			return

		if gui.level_2_click:
			inp.mouse_click = True
		gui.level_2_click = False

		w = 400 * gui.scale
		h = 155 * gui.scale
		x = int(window_size[0] / 2) - int(w / 2)
		y = int(window_size[1] / 2) - int(h / 2)

		ddt.rect_a((x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale), colours.box_border)
		ddt.rect_a((x, y), (w, h), colours.box_background)
		ddt.text_background_colour = colours.box_background

		if key_esc_press or ((inp.mouse_click or right_click or level_2_right_click) and not coll((x, y, w, h))):
			self.active = False
			gui.box_over = False

			if sub_lyrics_a.text and sub_lyrics_a.text != self.target_track.artist:
				prefs.lyrics_subs[self.target_track.artist] = sub_lyrics_a.text
			elif self.target_track.artist in prefs.lyrics_subs:
				del prefs.lyrics_subs[self.target_track.artist]

			if sub_lyrics_b.text and sub_lyrics_b.text != self.target_track.title:
				prefs.lyrics_subs[self.target_track.title] = sub_lyrics_b.text
			elif self.target_track.title in prefs.lyrics_subs:
				del prefs.lyrics_subs[self.target_track.title]

		ddt.text((x + 10 * gui.scale, y + 8 * gui.scale), _("Substitute Lyric Search"), colours.grey(230), 213)

		y += round(35 * gui.scale)
		x += round(23 * gui.scale)

		xx = x
		xx += ddt.text(
			(x + round(0 * gui.scale), y + round(0 * gui.scale)), _("Substitute"), colours.box_text_label, 212)
		xx += round(6 * gui.scale)
		ddt.text((xx, y + round(0 * gui.scale)), self.target_track.artist, colours.box_sub_text, 312)

		y += round(19 * gui.scale)
		xx = x
		xx += ddt.text((xx + round(0 * gui.scale), y + round(0 * gui.scale)), _("with"), colours.box_text_label, 212)
		xx += round(6 * gui.scale)
		rect1 = (xx, y, round(250 * gui.scale), round(17 * gui.scale))
		fields.add(rect1)
		ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
		if (coll(rect1) and inp.mouse_click) or (inp.key_tab_press and self.active_field == 2):
			self.active_field = 1
			inp.key_tab_press = False

		sub_lyrics_a.draw(
			xx + round(4 * gui.scale), y, colours.box_input_text, self.active_field == 1,
			width=rect1[2] - 8 * gui.scale)

		y += round(28 * gui.scale)

		xx = x
		xx += ddt.text(
			(x + round(0 * gui.scale), y + round(0 * gui.scale)), _("Substitute"), colours.box_text_label, 212)
		xx += round(6 * gui.scale)
		ddt.text((xx, y + round(0 * gui.scale)), self.target_track.title, colours.box_sub_text, 312)

		y += round(19 * gui.scale)
		xx = x
		xx += ddt.text((xx + round(0 * gui.scale), y + round(0 * gui.scale)), _("with"), colours.box_text_label, 212)
		xx += round(6 * gui.scale)
		rect1 = (xx, y, round(250 * gui.scale), round(16 * gui.scale))
		fields.add(rect1)
		if (coll(rect1) and inp.mouse_click) or (inp.key_tab_press and self.active_field == 1):
			self.active_field = 2
		# ddt.rect(rect1, [40, 40, 40, 255], True)
		ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
		sub_lyrics_b.draw(
			xx + round(4 * gui.scale), y, colours.box_input_text, self.active_field == 2, width=rect1[2] - 8 * gui.scale)

class ExportPlaylistBox:

	def __init__(self):

		self.active = False
		self.id = None
		self.directory_text_box = TextBox2()
		self.default = {
			"path": str(music_directory) if music_directory else str(user_directory / "playlists"),
			"type": "xspf",
			"relative": False,
			"auto": False,
		}

	def activate(self, playlist):

		self.active = True
		gui.box_over = True
		self.id = pl_to_id(playlist)

		# Prune old enteries
		ids = []
		for playlist in pctl.multi_playlist:
			ids.append(playlist.uuid_int)
		for key in list(prefs.playlist_exports.keys()):
			if key not in ids:
				del prefs.playlist_exports[key]

	def render(self) -> None:
		if not self.active:
			return

		w = 500 * gui.scale
		h = 220 * gui.scale
		x = int(window_size[0] / 2) - int(w / 2)
		y = int(window_size[1] / 2) - int(h / 2)

		ddt.rect_a((x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale), colours.box_border)
		ddt.rect_a((x, y), (w, h), colours.box_background)
		ddt.text_background_colour = colours.box_background

		if key_esc_press or ((inp.mouse_click or gui.level_2_click or right_click or level_2_right_click) and not coll(
				(x, y, w, h))):
			self.active = False
			gui.box_over = False

		current = prefs.playlist_exports.get(self.id)
		if not current:
			current = copy.copy(self.default)

		ddt.text((x + 10 * gui.scale, y + 8 * gui.scale), _("Export Playlist"), colours.grey(230), 213)

		x += round(15 * gui.scale)
		y += round(25 * gui.scale)

		ddt.text((x, y + 8 * gui.scale), _("Save directory"), colours.grey(230), 11)
		y += round(30 * gui.scale)

		rect1 = (x, y, round(450 * gui.scale), round(16 * gui.scale))
		fields.add(rect1)
		# ddt.rect(rect1, [40, 40, 40, 255], True)
		ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
		self.directory_text_box.text = current["path"]
		self.directory_text_box.draw(
			x + round(4 * gui.scale), y, colours.box_input_text, True,
			width=rect1[2] - 8 * gui.scale, click=gui.level_2_click)
		current["path"] = self.directory_text_box.text

		y += round(30 * gui.scale)
		if pref_box.toggle_square(x, y, current["type"] == "xspf", "XSPF", gui.level_2_click):
			current["type"] = "xspf"
		if pref_box.toggle_square(x + round(80 * gui.scale), y, current["type"] == "m3u", "M3U", gui.level_2_click):
			current["type"] = "m3u"
		# pref_box.toggle_square(x + round(160 * gui.scale), y, False, "PLS", gui.level_2_click)
		y += round(35 * gui.scale)
		current["relative"] = pref_box.toggle_square(
			x, y, current["relative"], _("Use relative paths"),
			gui.level_2_click)
		y += round(60 * gui.scale)
		current["auto"] = pref_box.toggle_square(x, y, current["auto"], _("Auto-export"), gui.level_2_click)

		y += round(0 * gui.scale)
		ww = ddt.get_text_w(_("Export"), 211)
		x = ((int(window_size[0] / 2) - int(w / 2)) + w) - (ww + round(40 * gui.scale))

		prefs.playlist_exports[self.id] = current

		if draw.button(_("Export"), x, y, press=gui.level_2_click):
			self.run_export(current, self.id, warnings=True)

	def run_export(self, current, id, warnings=True) -> None:
		logging.info("Export playlist")
		path = current["path"]
		if not os.path.isdir(path):
			if warnings:
				show_message(_("Directory does not exist"), mode="warning")
			return
		target = ""
		if current["type"] == "xspf":
			target = export_xspf(id_to_pl(id), direc=path, relative=current["relative"], show=False)
		if current["type"] == "m3u":
			target = export_m3u(id_to_pl(id), direc=path, relative=current["relative"], show=False)

		if warnings and target != 1:
			show_message(_("Playlist exported"), target, mode="done")

class KoelService:

	def __init__(self) -> None:
		self.connected: bool = False
		self.resource = None
		self.scanning:  bool = False
		self.server:     str = ""

		self.token:      str = ""

	def connect(self) -> None:

		logging.info("Connect to koel...")
		if not prefs.koel_username or not prefs.koel_password or not prefs.koel_server_url:
			show_message(_("Missing username, password and/or server URL"), mode="warning")
			self.scanning = False
			return

		if self.token:
			self.connected = True
			logging.info("Already authorised")
			return

		password = prefs.koel_password
		username = prefs.koel_username
		server = prefs.koel_server_url
		self.server = server

		target = server + "/api/me"

		headers = {
			"Accept": "application/json",
			"Content-Type": "application/json",
		}
		body = {
			"email": username,
			"password": password,
		}

		try:
			r = requests.post(target, json=body, headers=headers, timeout=10)
		except Exception:
			logging.exception("Could not establish connection")
			gui.show_message(_("Could not establish connection"), mode="error")
			return

		if r.status_code == 200:
			# logging.info(r.json())
			self.token = r.json()["token"]
			if self.token:
				logging.info("GOT KOEL TOKEN")
				self.connected = True

			else:
				logging.info("AUTH ERROR")

		else:
			error = ""
			j = r.json()
			if "message" in j:
				error = j["message"]

			gui.show_message(_("Could not establish connection/authorisation"), error, mode="error")


	def resolve_stream(self, id: str) -> tuple[str, dict[str, str]]:

		if not self.connected:
			self.connect()

		if prefs.network_stream_bitrate > 0:
			target = f"{self.server}/api/{id}/play/1/{prefs.network_stream_bitrate}"
		else:
			target = f"{self.server}/api/{id}/play/0/0"
		params = {"jwt-token": self.token }

		# if prefs.network_stream_bitrate > 0:
		#	 target = f"{self.server}/api/play/{id}/1/{prefs.network_stream_bitrate}"
		# else:
		#target = f"{self.server}/api/play/{id}/0/0"
		#target = f"{self.server}/api/{id}/play"

		#params = {"token": self.token, }

		#target = f"{self.server}/api/download/songs"
		#params["songs"] = [id,]
		logging.info(target)
		logging.info(urllib.parse.urlencode(params))

		return target, params

	def listen(self, track_object: TrackClass, submit: bool = False) -> None:
		if submit:
			try:
				target = self.server + "/api/interaction/play"
				headers = {
					"Authorization": "Bearer " + self.token,
					"Accept": "application/json",
					"Content-Type": "application/json",
				}

				r = requests.post(target, headers=headers, json={"song": track_object.url_key}, timeout=10)
				# logging.info(r.status_code)
				# logging.info(r.text)
			except Exception:
				logging.exception("error submitting listen to koel")

	def get_albums(self, return_list: bool = False) -> list[int] | None:

		gui.update += 1
		self.scanning = True

		if not self.connected:
			self.connect()

		if not self.connected:
			self.scanning = False
			return []

		playlist = []

		target = self.server + "/api/data"
		headers = {
			"Authorization": "Bearer " + self.token,
			"Accept": "application/json",
			"Content-Type": "application/json",
		}

		r = requests.get(target, headers=headers, timeout=10)
		data = r.json()

		artists = data["artists"]
		albums = data["albums"]
		songs = data["songs"]

		artist_ids = {}
		for artist in artists:
			id = artist["id"]
			if id not in artist_ids:
				artist_ids[id] = artist["name"]

		album_ids = {}
		covers = {}
		for album in albums:
			id = album["id"]
			if id not in album_ids:
				album_ids[id] = album["name"]
				if "cover" in album:
					covers[id] = album["cover"]

		existing = {}

		for track_id, track in pctl.master_library.items():
			if track.is_network and track.file_ext == "KOEL":
				existing[track.url_key] = track_id

		for song in songs:

			id = pctl.master_count
			replace_existing = False

			e = existing.get(song["id"])
			if e is not None:
				id = e
				replace_existing = True

			nt = TrackClass()

			nt.title = song["title"]
			nt.index = id
			if "track" in song and song["track"] is not None:
				nt.track_number = song["track"]
			if "disc" in song and song["disc"] is not None:
				nt.disc = song["disc"]
			nt.length = float(song["length"])

			nt.artist = artist_ids.get(song["artist_id"], "")
			nt.album = album_ids.get(song["album_id"], "")
			nt.parent_folder_name = (nt.artist + " - " + nt.album).strip("- ")
			nt.parent_folder_path = nt.album + "/" + nt.parent_folder_name

			nt.art_url_key = covers.get(song["album_id"], "")
			nt.url_key = song["id"]

			nt.is_network = True
			nt.file_ext = "KOEL"

			pctl.master_library[id] = nt

			if not replace_existing:
				pctl.master_count += 1

			playlist.append(nt.index)

		self.scanning = False

		if return_list:
			return playlist

		pctl.multi_playlist.append(pl_gen(title=_("Koel Collection"), playlist_ids=playlist))
		pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "koel path tn"
		standard_sort(len(pctl.multi_playlist) - 1)
		switch_playlist(len(pctl.multi_playlist) - 1)

class TauService:
	def __init__(self) -> None:
		self.processing = False

	def resolve_stream(self, key: str) -> str:
		return "http://" + prefs.sat_url + ":7814/api1/file/" + key

	def resolve_picture(self, key: str) -> str:
		return "http://" + prefs.sat_url + ":7814/api1/pic/medium/" + key

	def get(self, point: str):
		url = "http://" + prefs.sat_url + ":7814/api1/"
		data = None
		try:
			r = requests.get(url + point, timeout=10)
			data = r.json()
		except Exception as e:
			logging.exception("Network error")
			show_message(_("Network error"), str(e), mode="error")
		return data

	def get_playlist(self, playlist_name: str | None = None, return_list: bool = False) -> list[int] | None:

		p = self.get("playlists")

		if not p or not p["playlists"]:
			self.processing = False
			return []

		if playlist_name is None:
			playlist_name = text_sat_playlist.text.strip()
		if not playlist_name:
			show_message(_("No playlist name"))
			return []

		id = None
		name = ""
		for pp in p["playlists"]:
			if pp["name"].lower() == playlist_name.lower():
				id = pp["id"]
				name = pp["name"]

		if id is None:
			show_message(_("Playlist not found on target"), mode="error")
			self.processing = False
			return []

		try:
			t = self.get("tracklist/" + id)
		except Exception:
			logging.exception("error getting tracklist")
			return []
		at = t["tracks"]

		exist = {}
		for k, v in pctl.master_library.items():
			if v.is_network and v.file_ext == "TAU":
				exist[v.url_key] = k

		playlist = []
		for item in at:
			replace_existing = True

			tid = item["id"]
			id = exist.get(str(tid))
			if id is None:
				id = pctl.master_count
				replace_existing = False

			nt = TrackClass()
			nt.index = id
			nt.title = item.get("title", "")
			nt.artist = item.get("artist", "")
			nt.album = item.get("album", "")
			nt.album_artist = item.get("album_artist", "")
			nt.length = int(item.get("duration", 0) / 1000)
			nt.track_number = item.get("track_number", 0)

			nt.fullpath = item.get("path", "")
			nt.filename = os.path.basename(nt.fullpath)
			nt.parent_folder_name = os.path.basename(os.path.dirname(nt.fullpath))
			nt.parent_folder_path = os.path.dirname(nt.fullpath)

			nt.url_key = str(tid)
			nt.art_url_key = str(tid)

			nt.is_network = True
			nt.file_ext = "TAU"
			pctl.master_library[id] = nt

			if not replace_existing:
				pctl.master_count += 1
			playlist.append(nt.index)

		if return_list:
			self.processing = False
			return playlist

		pctl.multi_playlist.append(pl_gen(title=name, playlist_ids=playlist))
		pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "tau path tn"
		standard_sort(len(pctl.multi_playlist) - 1)
		switch_playlist(len(pctl.multi_playlist) - 1)
		self.processing = False

class SearchOverlay:

	def __init__(self):

		self.active = False
		self.search_text = TextBox()

		self.results = []
		self.searched_text = ""
		self.on = 0
		self.force_select = -1
		self.old_mouse = [0, 0]
		self.sip = False
		self.delay_enter = False
		self.last_animate_time = 0
		self.animate_timer = Timer(100)
		self.input_timer = Timer(100)
		self.all_folders = False
		self.spotify_mode = False

	def clear(self):
		self.search_text.text = ""
		self.results.clear()
		self.searched_text = ""
		self.on = 0
		self.all_folders = False

	def click_artist(self, name, get_list=False, search_lists=None):

		playlist = []

		if search_lists is None:
			search_lists = []
			for pl in pctl.multi_playlist:
				search_lists.append(pl.playlist_ids)

		for pl in search_lists:
			for item in pl:
				tr = pctl.master_library[item]
				n = name.lower()
				if tr.artist.lower() == n \
						or tr.album_artist.lower() == n \
						or ("artists" in tr.misc and name in tr.misc["artists"]):
					if item not in playlist:
						playlist.append(item)

		if get_list:
			return playlist

		pctl.multi_playlist.append(pl_gen(
			title=_("Artist: ") + name,
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))

		if gui.combo_mode:
			exit_combo()
		switch_playlist(len(pctl.multi_playlist) - 1)
		pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "a\"" + name + "\""

		inp.key_return_press = False

	def click_year(self, name, get_list: bool = False):

		playlist = []
		for pl in pctl.multi_playlist:
			for item in pl.playlist_ids:
				if name in pctl.master_library[item].date:
					if item not in playlist:
						playlist.append(item)

		if get_list:
			return playlist

		pctl.multi_playlist.append(pl_gen(
			title=_("Year: ") + name,
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))

		if gui.combo_mode:
			exit_combo()

		switch_playlist(len(pctl.multi_playlist) - 1)

		inp.key_return_press = False

	def click_composer(self, name: str, get_list: bool = False):

		playlist = []
		for pl in pctl.multi_playlist:
			for item in pl.playlist_ids:
				if pctl.master_library[item].composer.lower() == name.lower():
					if item not in playlist:
						playlist.append(item)

		if get_list:
			return playlist

		pctl.multi_playlist.append(pl_gen(
			title=_("Composer: ") + name,
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))

		if gui.combo_mode:
			exit_combo()

		switch_playlist(len(pctl.multi_playlist) - 1)

		inp.key_return_press = False

	def click_meta(self, name: str, get_list: bool = False, search_lists=None):

		if search_lists is None:
			search_lists = []
			for pl in pctl.multi_playlist:
				search_lists.append(pl.playlist_ids)

		playlist = []
		for pl in search_lists:
			for item in pl:
				if name in pctl.master_library[item].parent_folder_path:
					if item not in playlist:
						playlist.append(item)

		if get_list:
			return playlist

		pctl.multi_playlist.append(pl_gen(
			title=os.path.basename(name).upper(),
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))

		if gui.combo_mode:
			exit_combo()

		switch_playlist(len(pctl.multi_playlist) - 1)

		pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "p\"" + name + "\""

		inp.key_return_press = False

	def click_genre(self, name: str, get_list: bool = False, search_lists=None):

		playlist = []

		if search_lists is None:
			search_lists = []
			for pl in pctl.multi_playlist:
				search_lists.append(pl.playlist_ids)

		include_multi = False
		if name.endswith("+") or not prefs.sep_genre_multi:
			name = name.rstrip("+")
			include_multi = True

		for pl in search_lists:
			for item in pl:
				track = pctl.master_library[item]
				if track.genre.lower().replace("-", "") == name.lower().replace("-", ""):
					if item not in playlist:
						playlist.append(item)
				elif include_multi and ("/" in track.genre or "," in track.genre or ";" in track.genre):
					for split in track.genre.replace(",", "/").replace(";", "/").split("/"):
						split = split.strip()
						if name.lower().replace("-", "") == split.lower().replace("-", ""):
							if item not in playlist:
								playlist.append(item)

		if get_list:
			return playlist

		pctl.multi_playlist.append(pl_gen(
			title=_("Genre: ") + name,
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))

		if gui.combo_mode:
			exit_combo()

		switch_playlist(len(pctl.multi_playlist) - 1)

		if include_multi:
			pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "gm\"" + name + "\""
		else:
			pctl.gen_codes[pl_to_id(len(pctl.multi_playlist) - 1)] = "g=\"" + name + "\""

		inp.key_return_press = False

	def click_album(self, index):

		pctl.jump(index)
		if gui.combo_mode:
			exit_combo()

		pctl.show_current()

		inp.key_return_press = False

	def render(self):
		global input_text
		if self.active is False:

			# Activate search overlay on key presses
			if prefs.search_on_letter and input_text != "" and gui.layer_focus == 0 and \
					not key_lalt and not key_ralt and \
					not key_ctrl_down and not radiobox.active and not rename_track_box.active and \
					not quick_search_mode and not pref_box.enabled and not gui.rename_playlist_box \
					and not gui.rename_folder_box and input_text.isalnum() and not gui.box_over \
					and not trans_edit_box.active:

				# Divert to artist list if mouse over
				if gui.lsp and prefs.left_panel_mode == "artist list" and 2 < mouse_position[0] < gui.lspw \
						and gui.panelY < mouse_position[1] < window_size[1] - gui.panelBY:
					artist_list_box.locate_artist_letter(input_text)
					return

				activate_search_overlay()
				self.old_mouse = copy.deepcopy(mouse_position)

		if self.active:

			x = 0
			y = 0
			w = window_size[0]
			h = window_size[1]

			if keymaps.test("add-to-queue"):
				input_text = ""

			if inp.backspace_press:
				# self.searched_text = ""
				# self.results.clear()

				if len(self.search_text.text) - inp.backspace_press < 1:
					self.active = False
					self.search_text.text = ""
					self.results.clear()
					self.searched_text = ""
					return

			if key_esc_press:
				if self.delay_enter:
					self.delay_enter = False
				else:
					self.active = False
					self.search_text.text = ""
					self.results.clear()
					self.searched_text = ""
					return

			if gui.level_2_click and mouse_position[0] > 350 * gui.scale:
				self.active = False
				self.search_text.text = ""

			mouse_change = False
			if not point_proximity_test(self.old_mouse, mouse_position, 25):
				mouse_change = True
			# mouse_change = True

			ddt.rect((x, y, w, h), [3, 3, 3, 235])
			ddt.text_background_colour = [12, 12, 12, 255]


			input_text_x = 80 * gui.scale
			highlight_x = 30 * gui.scale
			thumbnail_rx = 100 * gui.scale
			text_lx = 120 * gui.scale

			s_font = 15
			s_b_font = 214
			b_font = 215

			if window_size[0] < 400 * gui.scale:
				input_text_x = 30 * gui.scale
				highlight_x = 4 * gui.scale
				thumbnail_rx = 65 * gui.scale
				text_lx = 80 * gui.scale
				s_font = 415
				s_b_font = 514
				d_font = 515

			#album_art_size_s = 0 * gui.scale

			# Search active animation
			if self.sip:
				x = round(15 * gui.scale)
				y = x
				s = round(7 * gui.scale)
				g = round(4 * gui.scale)

				t = self.animate_timer.get()
				if abs(t - self.last_animate_time) > 0.3:
					self.animate_timer.set()
					t = 0

				self.last_animate_time = t

				for item in range(4):
					a = 100
					if round(t * 14) % 4 == item:
						a = 255
					if self.spotify_mode:
						colour = (145, 245, 78, a)
					else:
						colour = (140, 100, 255, a)

					ddt.rect((x, y, s, s), colour)
					x += g + s

				gui.update += 1

			# No results found message
			elif not self.results and len(self.search_text.text) > 1:
				if self.input_timer.get() > 0.5 and not self.sip:
					ddt.text((window_size[0] // 2, 200 * gui.scale, 2), _("No results found"), [250, 250, 250, 255], 216,
						bg=[12, 12, 12, 255])

			# Spotify search text
			if prefs.spot_mode and not self.spotify_mode:
				text = _("Press Tab key to switch to Spotify search")
				ddt.text((window_size[0] // 2, window_size[1] - 30 * gui.scale, 2), text, [250, 250, 250, 255], 212,
					bg=[12, 12, 12, 255])

			self.search_text.draw(input_text_x, 60 * gui.scale, [230, 230, 230, 255], True, False, 30,
				window_size[0] - 100, big=True, click=gui.level_2_click, selection_height=30)

			if inp.key_tab_press:
				search_over.spotify_mode ^= True
				self.sip = True
				search_over.searched_text = search_over.search_text.text
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

			if input_text or key_backspace_press:
				self.input_timer.set()

				gui.update += 1
			elif self.input_timer.get() >= 0.20 and \
					(len(search_over.search_text.text) > 1 or (len(search_over.search_text.text) == 1 and ord(search_over.search_text.text) > 128)) \
					and search_over.search_text.text != search_over.searched_text:
				self.sip = True
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

			if self.input_timer.get() < 10:
				gui.frame_callback_list.append(TestTimer(0.1))

			yy = 110 * gui.scale

			if key_down_press:

				self.force_select += 1
				if self.force_select > 4:
					self.on = self.force_select - 4
				self.force_select = min(self.force_select, len(self.results) - 1)
				self.old_mouse = copy.deepcopy(mouse_position)

			if key_up_press:

				if self.force_select > -1:
					self.force_select -= 1
					self.force_select = max(self.force_select, 0)

					if self.force_select < self.on + 4:
						self.on = self.force_select - 4
						self.on = max(self.on, 0)

				self.old_mouse = copy.deepcopy(mouse_position)

			if mouse_wheel == -1:
				self.on += 1
				self.force_select += 1
			if mouse_wheel == 1 and self.on > -1:
				self.on -= 1
				self.force_select -= 1

			enter = False

			if self.delay_enter and not self.sip and self.search_text.text == self.searched_text:
				enter = True
				self.delay_enter = False

			elif inp.key_return_press:
				if self.results:
					enter = True
					self.delay_enter = False
				elif self.sip or self.input_timer.get() < 0.25:
					self.delay_enter = True
				else:
					enter = True
					self.delay_enter = False

			inp.key_return_press = False

			bar_colour = [140, 80, 240, 255]
			track_in_bar_colour = [244, 209, 66, 255]

			self.on = max(self.on, 0)
			self.on = min(len(self.results) - 1, self.on)

			full_count = 0

			sec = False

			p = -1

			if self.on > 4:
				p += self.on - 4
			p = self.on - 1
			clear = False

			for i, item in enumerate(self.results):

				p += 1

				if p > len(self.results) - 1:
					break

				item: list[int] = self.results[p]

				fade = 1
				selected = self.on
				if self.force_select > -1:
					selected = self.force_select

				#logging.info(selected)

				if selected != p:
					fade = 0.8

				start = yy

				n = item[0]

				names = {
					0: "Artist",
					1: "Album",
					2: "Track",
					3: "Genre",
					5: "Folder",
					6: "Composer",
					7: "Year",
					8: "Playlist",
					10: "Artist",
					11: "Album",
					12: "Track",
				}
				type_colours = {
					0: [250, 140, 190, 255],  # Artist
					1: [250, 140, 190, 255],  # Album
					2: [250, 220, 190, 255],  # Track
					3: [240, 240, 160, 255],  # Genre
					5: [250, 100, 50, 255],   # Folder
					6: [180, 250, 190, 255],  # Composer
					7: [250, 50, 140, 255],   # Year
					8: [100, 210, 250, 255],  # Playlist
					10: [145, 245, 78, 255],  # Spotify Artist
					11: [130, 237, 69, 255],  # Spotify Album
					12: [200, 255, 150, 255], # Spotify Track
				}
				if n not in names:
					name = "NYI"
					colour = [255, 255, 255, 255]
				else:
					name = names[n]
					colour = type_colours[n]
					colour[3] = int(colour[3] * fade)

				pad = round(4 * gui.scale)
				height = round(25 * gui.scale)
				if n in (1, 11):
					height = round(50 * gui.scale)
				album_art_size = height


				# Selection bar
				s_rect = (highlight_x, yy, 600 * gui.scale, height + pad + pad - 1)
				fields.add(s_rect)
				if fade == 1:
					ddt.rect((highlight_x, yy + pad, 4 * gui.scale, height), bar_colour)
				if n in (2,):
					if key_ctrl_down and item[2] in default_playlist:
						ddt.rect((highlight_x + round(5 * gui.scale), yy + pad, 4 * gui.scale, height), track_in_bar_colour)

				# Type text
				if n in (0, 3, 5, 6, 7, 8, 10, 12):
					ddt.text((thumbnail_rx, yy + pad + round(3 * gui.scale), 1), names[n], type_colours[n], 214)

				# Thumbnail
				if n in (1, 2):
					thl = thumbnail_rx - album_art_size
					ddt.rect((thl, yy + pad, album_art_size, album_art_size), [50, 50, 50, 150])
					tauon.gall_ren.render(pctl.get_track(item[2]), (thl, yy + pad), album_art_size)
					if fade != 1:
						ddt.rect((thl, yy + pad, album_art_size, album_art_size), [0, 0, 0, 70])
				if n in (11,):
					thl = thumbnail_rx - album_art_size
					ddt.rect((thl, yy + pad, album_art_size, album_art_size), [50, 50, 50, 150])
					# tauon.gall_ren.render(pctl.get_track(item[2]), (50 * gui.scale, yy + 5), 50 * gui.scale)
					if not item[5].draw(thumbnail_rx - album_art_size, yy + pad):
						if tauon.gall_ren.lock.locked():
							try:
								tauon.gall_ren.lock.release()
							except RuntimeError as e:
								if str(e) == "release unlocked lock":
									logging.error("RuntimeError: Attempted to release already unlocked gall_ren_lock")
								else:
									logging.exception("Unknown RuntimeError trying to release gall_ren_lock")
							except Exception:
								logging.exception("Unknown error trying to release gall_ren_lock")

				# Result text
				if n in (0, 5, 6, 7, 8, 10):  # Bold
					xx = ddt.text((text_lx, yy + pad + round(3 * gui.scale)), item[1], [255, 255, 255, int(255 * fade)], b_font)
				if n in (3,):  # Genre
					xx = ddt.text((text_lx, yy + pad + round(3 * gui.scale)), item[1].rstrip("+"), [255, 255, 255, int(255 * fade)], b_font)
					if item[1].endswith("+"):
						ddt.text(
							(xx + text_lx + 13 * gui.scale, yy + pad + round(3 * gui.scale)), _("(Include multi-tag results)"),
							[255, 255, 255, int(255 * fade) // 2], 313)
				if n == 11:  # Spotify Album
					xx = ddt.text((text_lx, yy + round(5 * gui.scale)), item[1][0], [255, 255, 255, int(255 * fade)], s_b_font)
					artist = item[1][1]
					ddt.text((text_lx + 5 * gui.scale, yy + 30 * gui.scale), _("BY"), [250, 240, 110, int(255 * fade)], 212)
					xx += 8 * gui.scale
					xx += ddt.text((text_lx + 30 * gui.scale, yy + 30 * gui.scale), artist, [250, 250, 250, int(255 * fade)], s_font)
				if n in (12,):  # Spotify Track
					yyy = yy
					yyy += round(6 * gui.scale)
					xx = ddt.text((text_lx, yyy), item[1][0], [255, 255, 255, int(255 * fade)], s_font)
					xx += 9 * gui.scale
					ddt.text((xx + text_lx, yyy), _("BY"), [250, 160, 110, int(255 * fade)], 212)
					xx += 25 * gui.scale
					xx += ddt.text((xx + text_lx, yyy), item[1][1], [255, 255, 255, int(255 * fade)], s_b_font)
				if n in (2, ):  # Track
					yyy = yy
					yyy += round(6 * gui.scale)
					track = pctl.master_library[item[2]]
					if track.artist == track.title == "":
						text = os.path.splitext(track.filename)[0]
						xx = ddt.text((text_lx, yyy + pad), text, [255, 255, 255, int(255 * fade)], s_font)
					else:
						xx = ddt.text((text_lx, yyy), item[1], [255, 255, 255, int(255 * fade)], s_font)
						xx += 9 * gui.scale
						ddt.text((xx + text_lx, yyy), _("BY"), [250, 160, 110, int(255 * fade)], 212)
						xx += 25 * gui.scale
						artist = track.artist
						xx += ddt.text((xx + text_lx, yyy), artist, [255, 255, 255, int(255 * fade)], s_b_font)
						if track.album:
							xx += 9 * gui.scale
							xx += ddt.text((xx + text_lx, yyy), _("FROM"), [120, 120, 120, int(255 * fade)], 212)
							xx += 8 * gui.scale
							xx += ddt.text((xx + text_lx, yyy), track.album, [80, 80, 80, int(255 * fade)], 212)

				if n in (1,):  # Two line album
					track = pctl.master_library[item[2]]
					artist = track.album_artist
					if not artist:
						artist = track.artist

					xx = ddt.text((text_lx, yy + pad + round(5 * gui.scale)), item[1], [255, 255, 255, int(255 * fade)], s_b_font)

					ddt.text((text_lx + 5 * gui.scale, yy + 30 * gui.scale), _("BY"), [250, 240, 110, int(255 * fade)], 212)
					xx += 8 * gui.scale
					xx += ddt.text((text_lx + 30 * gui.scale, yy + 30 * gui.scale), artist, [250, 250, 250, int(255 * fade)], s_font)


				yy += height + pad + pad

				show = False
				go = False
				extend = False
				if coll(s_rect) and mouse_change:
					if self.force_select != p:
						self.force_select = p
						gui.update = 2

					if gui.level_2_click:
						if key_ctrl_down:
							extend = True
						else:
							go = True
							clear = True


					if level_2_right_click:
						show = True
						clear = True

				if enter and key_shift_down and fade == 1:
					show = True
					clear = True

				elif enter and fade == 1:
					if key_shift_down or key_shiftr_down:
						show = True
						clear = True
					else:
						go = True
						clear = True

				if extend:
					match n:
						case 0:
							default_playlist.extend(self.click_artist(item[1], get_list=True))
						case 1:
							for k, pl in enumerate(pctl.multi_playlist):
								if item[2] in pl.playlist_ids:
									default_playlist.extend(
										get_album_from_first_track(pl.playlist_ids.index(item[2]), item[2], k))
									break
						case 2:
							default_playlist.append(item[2])
						case 3:
							default_playlist.extend(self.click_genre(item[1], get_list=True))
						case 5:
							default_playlist.extend(self.click_meta(item[1], get_list=True))
						case 6:
							default_playlist.extend(self.click_composer(item[1], get_list=True))
						case 7:
							default_playlist.extend(self.click_year(item[1], get_list=True))
						case 8:
							default_playlist.extend(pctl.multi_playlist[pl].playlist_ids)
						case 12:
							tauon.spot_ctl.append_track(item[2])
							reload_albums()

					gui.pl_update += 1
				elif show:
					match n:
						case 0 | 1 | 2 | 3 | 5 | 6 | 7 | 10:
							pctl.show_current(index=item[2], playing=False)
							if album_mode:
								show_in_gal(0)
						case 8:
							pl = id_to_pl(item[3])
							if pl:
								switch_playlist(pl)

				elif go:
					match n:
						case 0:
							self.click_artist(item[1])
						case 10:
							show_message(_("Searching for albums by artist: ") + item[1], _("This may take a moment"))
							shoot = threading.Thread(target=tauon.spot_ctl.artist_playlist, args=([item[2]]))
							shoot.daemon = True
							shoot.start()
						case 1 | 2:
							self.click_album(item[2])
							pctl.show_current(index=item[2])
							pctl.playlist_view_position = pctl.selected_in_playlist
						case 3:
							self.click_genre(item[1])
						case 5:
							self.click_meta(item[1])
						case 6:
							self.click_composer(item[1])
						case 7:
							self.click_year(item[1])
						case 8:
							pl = id_to_pl(item[3])
							if pl:
								switch_playlist(pl)
						case 11:
							tauon.spot_ctl.album_playlist(item[2])
							reload_albums()
						case 12:
							tauon.spot_ctl.append_track(item[2])
							reload_albums()

				if n in (2,) and keymaps.test("add-to-queue") and fade == 1:
					queue_object = queue_item_gen(
						item[2],
						pctl.multi_playlist[id_to_pl(item[3])].playlist_ids.index(item[2]),
						item[3])
					pctl.force_queue.append(queue_object)
					queue_timer_set(queue_object=queue_object)

				# ----

				# ---
				if i > 40:
					break
				if yy > window_size[1] - (100 * gui.scale):
					break

				continue

			if clear:
				self.active = False
				self.search_text.text = ""
				self.results.clear()
				self.searched_text = ""

class MessageBox:

	def __init__(self):
		pass

	def get_rect(self):

		w1 = ddt.get_text_w(gui.message_text, 15) + 74 * gui.scale
		w2 = ddt.get_text_w(gui.message_subtext, 12) + 74 * gui.scale
		w3 = ddt.get_text_w(gui.message_subtext2, 12) + 74 * gui.scale
		w = max(w1, w2, w3)

		w = max(w, 210 * gui.scale)

		h = round(60 * gui.scale)
		if gui.message_subtext2:
			h += round(15 * gui.scale)

		x = int(window_size[0] / 2) - int(w / 2)
		y = int(window_size[1] / 2) - int(h / 2)

		return x, y, w, h

	def render(self):

		if inp.mouse_click or inp.key_return_press or right_click or key_esc_press or inp.backspace_press \
				or keymaps.test("quick-find") or (k_input and message_box_min_timer.get() > 1.2):

			if not key_focused and message_box_min_timer.get() > 0.4:
				gui.message_box = False
				gui.update += 1
				inp.key_return_press = False

		x, y, w, h = self.get_rect()

		ddt.rect_a((x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale),
			colours.box_text_border)
		ddt.rect_a((x, y), (w, h), colours.message_box_bg)

		ddt.text_background_colour = colours.message_box_bg

		if gui.message_mode == "info":
			message_info_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(message_info_icon.h / 2) - 1)
		elif gui.message_mode == "warning":
			message_warning_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(message_info_icon.h / 2) - 1)
		elif gui.message_mode == "done":
			message_tick_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(message_info_icon.h / 2) - 1)
		elif gui.message_mode == "arrow":
			message_arrow_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(message_info_icon.h / 2) - 1)
		elif gui.message_mode == "download":
			message_download_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(message_info_icon.h / 2) - 1)
		elif gui.message_mode == "error":
			message_error_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(message_error_icon.h / 2) - 1)
		elif gui.message_mode == "bubble":
			message_bubble_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(message_bubble_icon.h / 2) - 1)
		elif gui.message_mode == "link":
			message_info_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(message_bubble_icon.h / 2) - 1)
		elif gui.message_mode == "confirm":
			message_info_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(message_info_icon.h / 2) - 1)
			ddt.text((x + 62 * gui.scale, y + 9 * gui.scale), gui.message_text, colours.message_box_text, 15)
			if draw.button("Yes", (w // 2 + x) - 70 * gui.scale, y + 32 * gui.scale, w=60*gui.scale):
				gui.message_box_confirm_callback(*gui.message_box_confirm_reference)
			if draw.button("No", (w // 2 + x) + 25 * gui.scale, y + 32 * gui.scale, w=60*gui.scale):
				gui.message_box = False
			return

		if gui.message_subtext:
			ddt.text((x + 62 * gui.scale, y + 11 * gui.scale), gui.message_text, colours.message_box_text, 15)
			if gui.message_mode == "bubble" or gui.message_mode == "link":
				link_pa = draw_linked_text((x + 63 * gui.scale, y + (9 + 22) * gui.scale), gui.message_subtext,
					colours.message_box_text, 12)
				link_activate(x + 63 * gui.scale, y + (9 + 22) * gui.scale, link_pa)
			else:
				ddt.text((x + 63 * gui.scale, y + (9 + 22) * gui.scale), gui.message_subtext, colours.message_box_text,
					12)

			if gui.message_subtext2:
				ddt.text((x + 63 * gui.scale, y + (9 + 42) * gui.scale), gui.message_subtext2, colours.message_box_text,
					12)

		else:
			ddt.text((x + 62 * gui.scale, y + 20 * gui.scale), gui.message_text, colours.message_box_text, 15)

class NagBox:
	def __init__(self):
		self.wiggle_timer = Timer(10)

	def draw(self):
		w = 485 * gui.scale
		h = 165 * gui.scale
		x = int(window_size[0] / 2) - int(w / 2)
		# if self.wiggle_timer.get() < 0.5:
		#     gui.update += 1
		#     x += math.sin(core_timer.get() * 40) * 4
		y = int(window_size[1] / 2) - int(h / 2)

		# xx = x - round(8 * gui.scale)
		# hh = 0.0 #349 / 360
		# while xx < x + w + round(8 * gui.scale):
		#     re = [xx, y - round(8 * gui.scale), 3, h + round(8 * gui.scale) + round(8 * gui.scale)]
		#     hh -= 0.0007
		#     c = hsl_to_rgb(hh, 0.9, 0.7)
		#     #c = hsl_to_rgb(hh, 0.63, 0.43)
		#     ddt.rect(re, c)
		#     xx += 3

		ddt.rect_a((x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale),
			colours.box_text_border)
		ddt.rect_a((x, y), (w, h), colours.message_box_bg)

		# if gui.level_2_click and not coll((x, y, w, h)):
		#     if core_timer.get() < 2:
		#         self.wiggle_timer.set()
		#     else:
		#         prefs.show_nag = False
		#
		#     gui.update += 1

		ddt.text_background_colour = colours.message_box_bg

		x += round(10 * gui.scale)
		y += round(13 * gui.scale)
		ddt.text((x, y), _("Welcome to v7.2.0!"), colours.message_box_text, 212)
		y += round(20 * gui.scale)

		link_pa = draw_linked_text(
			(x, y),
			_("You can check out the release notes on the https://") + "github.com/Taiko2k/TauonMusicBox/releases",
			colours.message_box_text, 12, replace=_("Github release page."))
		link_activate(x, y, link_pa, click=gui.level_2_click)

		heart_notify_icon.render(x + round(425 * gui.scale), y + round(80 * gui.scale), [255, 90, 90, 255])

		y += round(30 * gui.scale)
		ddt.text((x, y), _("New supporter bonuses!"), colours.message_box_text, 212)

		y += round(20 * gui.scale)

		ddt.text((x, y), _("A new supporter bonus theme is now available! Check it out at the above link!"),
			colours.message_box_text, 12)
		# link_activate(x, y, link_pa, click=gui.level_2_click)

		y += round(20 * gui.scale)
		ddt.text((x, y), _("Your support means a lot! Love you!"), colours.message_box_text, 12)

		y += round(30 * gui.scale)

		if draw.button("Close", x, y, press=gui.level_2_click):
			prefs.show_nag = False
			# show_message("Oh... :( 💔")
		# if draw.button("Show supporter page", x + round(304 * gui.scale), y, background_colour=[60, 140, 60, 255], background_highlight_colour=[60, 150, 60, 255], press=gui.level_2_click):
		#     webbrowser.open("https://github.com/sponsors/Taiko2k", new=2, autoraise=True)
		# prefs.show_nag = False
		# if draw.button("I already am!", x + round(360), y, press=gui.level_2_click):
		#     show_message("Oh hey, thanks! :)")
		#     prefs.show_nag = False

class PowerTag:

	def __init__(self):
		self.name = "BLANK"
		self.path = ""
		self.position = 0
		self.colour = None

		self.peak_x = 0
		self.ani_timer = Timer()
		self.ani_timer.force_set(10)

class Over:
	def __init__(self):

		global window_size

		self.init2done = False

		self.about_image = asset_loader(scaled_asset_directory, loaded_asset_dc, "v4-a.png")
		self.about_image2 = asset_loader(scaled_asset_directory, loaded_asset_dc, "v4-b.png")
		self.about_image3 = asset_loader(scaled_asset_directory, loaded_asset_dc, "v4-c.png")
		self.about_image4 = asset_loader(scaled_asset_directory, loaded_asset_dc, "v4-d.png")
		self.about_image5 = asset_loader(scaled_asset_directory, loaded_asset_dc, "v4-e.png")
		self.about_image6 = asset_loader(scaled_asset_directory, loaded_asset_dc, "v4-f.png")
		self.title_image = asset_loader(scaled_asset_directory, loaded_asset_dc, "title.png", True)

		# self.tab_width = round(115 * gui.scale)
		self.w = 100
		self.h = 100

		self.box_x = 100
		self.box_y = 100
		self.item_x_offset = round(25 * gui.scale)

		self.current_path = os.path.expanduser("~")
		self.view_offset = 0
		self.ext_ratio = {}
		self.last_db_size = -1

		self.enabled = False
		self.click = False
		self.right_click = False
		self.scroll = 0
		self.lock = False

		self.drives = []

		self.temp_lastfm_user = ""
		self.temp_lastfm_pass = ""
		self.lastfm_input_box = 0

		self.func_page = 0
		self.tab_active = 0
		self.tabs = [
			[_("Function"), self.funcs],
			[_("Audio"), self.audio],
			[_("Tracklist"), self.config_v],
			[_("Theme"), self.theme],
			[_("Window"), self.config_b],
			[_("View"), self.view2],
			[_("Transcode"), self.codec_config],
			[_("Lyrics"), self.lyrics],
			[_("Accounts"), self.last_fm_box],
			[_("Stats"), self.stats],
			[_("About"), self.about],
		]

		self.stats_timer = Timer()
		self.stats_timer.force_set(1000)
		self.stats_pl_timer = Timer()
		self.stats_pl_timer.force_set(1000)
		self.total_albums = 0
		self.stats_pl = 0
		self.stats_pl_albums = 0
		self.stats_pl_length = 0

		self.ani_cred = 0
		self.cred_page = 0
		self.ani_fade_on_timer = Timer(force=10)
		self.ani_fade_off_timer = Timer(force=10)

		self.device_scroll_bar_position = 0

		self.lyrics_panel = False
		self.account_view = 0
		self.view_view = 0
		self.chart_view = 0
		self.eq_view = False
		self.rg_view = False
		self.sync_view = False

		self.account_text_field = -1

		self.themes = []
		self.view_supporters = False
		self.key_box = TextBox2()
		self.key_box_focused = False

	def theme(self, x0, y0, w0, h0):

		global album_mode_art_size
		global update_layout

		y = y0 + 13 * gui.scale
		x = x0 + 25 * gui.scale

		ddt.text_background_colour = colours.box_background
		ddt.text((x, y), _("Theme"), colours.box_text_label, 12)

		y += 25 * gui.scale

		self.toggle_square(x, y, toggle_auto_bg, _("Use album art as background"))

		y += 23 * gui.scale

		old = prefs.enable_fanart_bg
		prefs.enable_fanart_bg = self.toggle_square(x + 10 * gui.scale, y, prefs.enable_fanart_bg,
													_("Prefer artist backgrounds"))
		if prefs.enable_fanart_bg and prefs.enable_fanart_bg != old:
			if not prefs.auto_dl_artist_data:
				prefs.auto_dl_artist_data = True
				show_message(_("Also enabling 'auto-fech artist data' to scrape last.fm."), _("You can toggle this back off under Settings > Function"))
		y += 23 * gui.scale

		self.toggle_square(x + 10 * gui.scale, y, toggle_auto_bg_strong, _("Stronger"))
		# self.toggle_square(x + 10 * gui.scale, y, toggle_auto_bg_strong1, _("Lo"))
		# self.toggle_square(x + 54 * gui.scale, y, toggle_auto_bg_strong2, _("Md"))
		# self.toggle_square(x + 105 * gui.scale, y, toggle_auto_bg_strong3, _("Hi"))

		#y += 23 * gui.scale
		self.toggle_square(x + 120 * gui.scale, y, toggle_auto_bg_blur, _("Blur"))

		y += 23 * gui.scale
		self.toggle_square(x + 10 * gui.scale, y, toggle_auto_bg_showcase, _("Showcase only"))

		y += 23 * gui.scale
		# prefs.center_bg = self.toggle_square(x + 10 * gui.scale, y, prefs.center_bg, _("Always center"))
		prefs.showcase_overlay_texture = self.toggle_square(
			x + 20 * gui.scale, y, prefs.showcase_overlay_texture, _("Pattern style"))

		y += 25 * gui.scale

		self.toggle_square(x, y, toggle_auto_theme, _("Auto-theme from album art"))

		y += 55 * gui.scale

		square = round(8 * gui.scale)
		border = round(4 * gui.scale)
		outer_border = round(2 * gui.scale)

		# theme_files = get_themes()
		xx = x
		yy = y
		hover_name = None
		for c, theme_name, theme_number in self.themes:

			if theme_name == gui.theme_name:
				rect = [
					xx - outer_border, yy - outer_border, border * 2 + square * 2 + outer_border * 2,
					border * 2 + square * 2 + outer_border * 2]
				ddt.rect(rect, colours.box_text_label)

			rect = [xx, yy, border * 2 + square * 2, border * 2 + square * 2]
			ddt.rect(rect, [5, 5, 5, 255])

			rect = grow_rect(rect, 3)
			fields.add(rect)
			if coll(rect):
				hover_name = theme_name
				if self.click:
					global theme
					theme = theme_number
					gui.reload_theme = True

			c1 = c.playlist_panel_background
			c2 = c.artist_playing
			c3 = c.title_playing
			c4 = c.bottom_panel_colour

			if theme_name == "Carbon":
				c1 = c.title_playing
				c2 = c.playlist_panel_background
				c3 = c.top_panel_background

			if theme_name == "Lavender Light":
				c1 = c.tab_background_active

			if theme_name == "Neon Love":
				c2 = c.artist_text
				c4 = [118, 85, 194, 255]
				c1 = c4

			if theme_name == "Sky":
				c2 = c.artist_text

			if theme_name == "Sunken":
				c2 = c.title_text
				c3 = c.artist_text
				c4 = [59, 115, 109, 255]
				c1 = c4

			if c2 == c3 and colour_value(c1) < 200:
				rect = [(xx + border + square) - (square // 2), (yy + border + square) - (square // 2), square, square]
				ddt.rect(rect, c2)
			else:

				# tl
				rect = [xx + border, yy + border, square, square]
				ddt.rect(rect, c1)

				# tr
				rect = [xx + border + square, yy + border, square, square]
				ddt.rect(rect, c2)

				# bl
				rect = [xx + border, yy + border + square, square, square]
				ddt.rect(rect, c3)

				# br
				rect = [xx + border + square, yy + border + square, square, square]
				ddt.rect(rect, c4)

			yy += round(27 * gui.scale)
			if yy > y + 40 * gui.scale:
				yy = y
				xx += round(27 * gui.scale)

		name = gui.theme_name
		if hover_name:
			name = hover_name
		ddt.text((x, y - 23 * gui.scale), name, colours.box_text_label, 214)
		if gui.theme_name == "Neon Love" and not hover_name:
			x += 95 * gui.scale
			y -= 23 * gui.scale
			# x += 165 * gui.scale
			# y += -19 * gui.scale

			link_pa = draw_linked_text((x, y),
			_("Based on") + " " + "https://love.holllo.cc/", colours.box_text_label, 312, replace="love.holllo.cc")
			link_activate(x, y, link_pa, click=self.click)

	def rg(self, x0, y0, w0, h0):
		y = y0 + 55 * gui.scale
		x = x0 + 130 * gui.scale

		if self.button(x - 110 * gui.scale, y + 180 * gui.scale, _("Return"), width=75 * gui.scale):
			self.rg_view = False

		y = y0 + round(15 * gui.scale)
		x = x0 + round(50 * gui.scale)

		ddt.text((x, y), _("ReplayGain"), colours.box_text_label, 14)
		y += round(25 * gui.scale)

		self.toggle_square(x, y, switch_rg_off, _("Off"))
		self.toggle_square(x + round(80 * gui.scale), y, switch_rg_auto, _("Auto"))
		y += round(22 * gui.scale)
		self.toggle_square(x, y, switch_rg_album, _("Preserve album dynamics"))
		y += round(22 * gui.scale)
		self.toggle_square(x, y, switch_rg_track, _("Tracks equal loudness"))

		y += round(25 * gui.scale)
		ddt.text((x, y), _("Will only have effect if ReplayGain metadata is present."), colours.box_text_label, 12)
		y += round(26 * gui.scale)

		ddt.text((x, y), _("Pre-amp"), colours.box_text_label, 14)
		y += round(26 * gui.scale)

		sw = round(170 * gui.scale)
		sh = round(2 * gui.scale)

		slider = (x, y, sw, sh)

		gh = round(14 * gui.scale)
		gw = round(8 * gui.scale)
		grip = [0, y - (gh // 2), gw, gh]

		grip[0] = x

		bp = prefs.replay_preamp + 15

		grip[0] += (bp / 30 * sw)

		m1 = (x, y, sh, sh * 2)
		m2 = ((x + sw // 2), y, sh, sh * 2)
		m3 = ((x + sw), y, sh, sh * 2)

		if coll(grow_rect(slider, 15)) and mouse_down:
			bp = (mouse_position[0] - x) / sw * 30
			gui.update += 1

		bp = round(bp)
		bp = max(bp, 0)
		bp = min(bp, 30)
		prefs.replay_preamp = bp - 15

		# grip[0] += (bp / 30 * sw)

		ddt.rect(slider, colours.box_text_border)
		ddt.rect(m1, colours.box_text_border)
		ddt.rect(m2, colours.box_text_border)
		ddt.rect(m3, colours.box_text_border)
		ddt.rect(grip, colours.box_text_label)

		text = f"{prefs.replay_preamp} dB"
		if prefs.replay_preamp > 0:
			text = "+" + text

		colour = colours.box_sub_text
		if prefs.replay_preamp == 0:
			colour = colours.box_text_label
		ddt.text((x + sw + round(14 * gui.scale), y - round(8 * gui.scale)), text, colour, 11)
		#logging.info(prefs.replay_preamp)

		y += round(18 * gui.scale)
		ddt.text(
			(x, y, 4, 310 * gui.scale, 300 * gui.scale),
			_("Lower pre-amp values improve normalisation but will require a higher system volume."),
			colours.box_text_label, 12)

	def eq(self, x0, y0, w0, h0):

		y = y0 + 55 * gui.scale
		x = x0 + 130 * gui.scale

		if self.button(x - 110 * gui.scale, y + 180 * gui.scale, _("Return"), width=75 * gui.scale):
			self.eq_view = False

		base_dis = 160 * gui.scale
		center = base_dis // 2
		width = 25 * gui.scale

		range = 12

		self.toggle_square(x - 90 * gui.scale, y - 35 * gui.scale, toggle_eq, _("Enable"))

		ddt.text((x - 17 * gui.scale, y + 2 * gui.scale), "+", colours.grey(130), 16)
		ddt.text((x - 17 * gui.scale, y + base_dis - 15 * gui.scale), "-", colours.grey(130), 16)

		for i, q in enumerate(prefs.eq):

			bar = [x, y, width, base_dis]

			ddt.rect(bar, [255, 255, 255, 20])

			bar[0] -= 2 * gui.scale
			bar[1] -= 10 * gui.scale
			bar[2] += 4 * gui.scale
			bar[3] += 20 * gui.scale

			if coll(bar):

				if mouse_down:
					target = mouse_position[1] - y - center
					target = (target / center) * range
					target = min(target, range)
					target = max(target, range * -1)
					if -0.1 < target < 0.1:
						target = 0

					prefs.eq[i] = target

					pctl.playerCommand = "seteq"
					pctl.playerCommandReady = True

				if self.right_click:
					prefs.eq[i] = 0
					pctl.playerCommand = "seteq"
					pctl.playerCommandReady = True

			start = (q / range) * center

			bar = [x, y + center, width, start]

			ddt.rect(bar, [100, 200, 100, 255])

			x += round(29 * gui.scale)

	def audio(self, x0, y0, w0, h0):

		global mouse_down

		ddt.text_background_colour = colours.box_background
		y = y0 + 40 * gui.scale
		x = x0 + 20 * gui.scale

		if self.eq_view:
			self.eq(x0, y0, w0, h0)
			return

		if self.rg_view:
			self.rg(x0, y0, w0, h0)
			return

		colour = colours.box_sub_text

		# if system == "Linux":
		if not phazor_exists(tauon.pctl):
			x += round(20 * gui.scale)
			ddt.text((x, y - 25 * gui.scale), _("PHAzOR DLL not found!"), colour, 213)

		elif prefs.backend == 4:

			y = y0 + round(20 * gui.scale)
			x = x0 + 20 * gui.scale

			x += round(2 * gui.scale)

			self.toggle_square(x, y, toggle_pause_fade, _("Use fade on pause/stop"))
			y += round(23 * gui.scale)
			self.toggle_square(x, y, toggle_jump_crossfade, _("Use fade on track jump"))
			y += round(23 * gui.scale)
			prefs.back_restarts = self.toggle_square(x, y, prefs.back_restarts, _("Back restarts to beginning"))

			y += round(40 * gui.scale)
			if self.button(x, y, _("ReplayGain")):
				mouse_down = False
				self.rg_view = True

			y += round(45 * gui.scale)
			prefs.precache = self.toggle_square(x, y, prefs.precache, _("Cache local files (for smb/nfs)"))
			y += round(23 * gui.scale)
			old = prefs.tmp_cache
			prefs.tmp_cache = self.toggle_square(x, y, prefs.tmp_cache ^ True, _("Use persistent network cache")) ^ True
			if old != prefs.tmp_cache and tauon.cachement:
				tauon.cachement.__init__()

			y += round(22 * gui.scale)
			ddt.text((x + round(22 * gui.scale), y), _("Cache size"), colours.box_text, 312)
			y += round(18 * gui.scale)
			prefs.cache_limit = int(
				self.slide_control(
					x + round(22 * gui.scale), y, None, _(" GB"), prefs.cache_limit / 1000, 0.5,
					1000, 0.5) * 1000)

			y += round(30 * gui.scale)
			# prefs.device_buffer = self.slide_control(x + round(270 * gui.scale), y, _("Output buffer"), 'ms',
			#                                          prefs.device_buffer, 10,
			#                                          500, 10, self.reload_device)

			# if prefs.device_buffer > 100:
			#     prefs.pa_fast_seek = True
			# else:
			#     prefs.pa_fast_seek = False

			y = y0 + 37 * gui.scale
			x = x0 + 270 * gui.scale
			ddt.text_background_colour = colours.box_background
			ddt.text((x, y - 22 * gui.scale), _("Set audio output device"), colours.box_text_label, 212)

			if platform_system == "Linux":
				old = prefs.pipewire
				prefs.pipewire = self.toggle_square(x + round(gui.scale * 110), self.box_y + self.h - 50 * gui.scale,
															prefs.pipewire, _("PipeWire (unstable)"))
				prefs.pipewire = self.toggle_square(x, self.box_y + self.h - 50 * gui.scale,
															prefs.pipewire ^ True, _("PulseAudio")) ^ True
				if old != prefs.pipewire:
					show_message(_("Please restart Tauon for this change to take effect"))

			old = prefs.avoid_resampling
			prefs.avoid_resampling = self.toggle_square(x, self.box_y + self.h - 27 * gui.scale, prefs.avoid_resampling, _("Avoid resampling"))
			if prefs.avoid_resampling != old:
				pctl.playerCommand = "reload"
				pctl.playerCommandReady = True
				if not old:
					show_message(
						_("Tip: To get samplerate to DAC you may need to check some settings, see:"),
						"https://github.com/Taiko2k/Tauon/wiki/Audio-Specs", mode="link")

			self.device_scroll_bar_position -= pref_box.scroll
			self.device_scroll_bar_position = max(self.device_scroll_bar_position, 0)
			if self.device_scroll_bar_position > len(prefs.phazor_devices) - 11 > 11:
				self.device_scroll_bar_position = len(prefs.phazor_devices) - 11

			if len(prefs.phazor_devices) > 13:
				self.device_scroll_bar_position = device_scroll.draw(
					x + 250 * gui.scale, y, 11, 180,
					self.device_scroll_bar_position,
					len(prefs.phazor_devices) - 11, click=self.click)

			i = 0
			reload = False
			for name in prefs.phazor_devices:

				if i < self.device_scroll_bar_position:
					continue
				if y > self.box_y + self.h - 40 * gui.scale:
					break

				rect = (x, y + 4 * gui.scale, 245 * gui.scale, 13)

				if self.click and coll(rect):
					prefs.phazor_device_selected = name
					reload = True

				line = trunc_line(name, 10, 245 * gui.scale)

				fields.add(rect)

				if prefs.phazor_device_selected == name:
					ddt.text((x, y), line, colours.box_sub_text, 10)
					ddt.text((x - 12 * gui.scale, y + 1 * gui.scale), ">", colours.box_sub_text, 213)
				elif coll(rect):
					ddt.text((x, y), line, colours.box_sub_text, 10)
				else:
					ddt.text((x, y), line, colours.box_text_label, 10)
				y += 14 * gui.scale
				i += 1

			if reload:
				pctl.playerCommand = "set-device"
				pctl.playerCommandReady = True

	def reload_device(self, _):

		pctl.playerCommand = "reload"
		pctl.playerCommandReady = True

	def toggle_lyrics_view(self):
		self.lyrics_panel ^= True

	def lyrics(self, x0, y0, w0, h0):

		x = x0 + 25 * gui.scale
		y = y0 - 10 * gui.scale
		y += 30 * gui.scale

		ddt.text_background_colour = colours.box_background

		# self.toggle_square(x, y, toggle_auto_lyrics, _("Auto search lyrics"))
		if prefs.auto_lyrics:
			if prefs.auto_lyrics_checked:
				if self.button(x, y, _("Reset failed list")):
					prefs.auto_lyrics_checked.clear()
			y += 30 * gui.scale


		#self.toggle_square(x, y, toggle_guitar_chords, _("Enable chord lyrics"))

		y += 40 * gui.scale
		ddt.text((x, y), _("Sources:"), colours.box_text_label, 11)
		y += 23 * gui.scale

		for name in lyric_sources.keys():
			enabled = name in prefs.lyrics_enables
			title = _(name)
			if name in uses_scraping:
				title += "*"
			new = self.toggle_square(x, y, enabled, title)
			y += round(23 * gui.scale)
			if new != enabled:
				if enabled:
					prefs.lyrics_enables.clear()
				else:
					prefs.lyrics_enables.append(name)

		y += round(6 * gui.scale)
		ddt.text((x + 12 * gui.scale, y), _("*Uses scraping. Enable at your own discretion."), colours.box_text_label, 11)
		y += 20 * gui.scale
		ddt.text((x + 12 * gui.scale, y), _("Tip: The order enabled will be the order searched."), colours.box_text_label, 11)
		y += 20 * gui.scale

	def view2(self, x0, y0, w0, h0):

		x = x0 + 25 * gui.scale
		y = y0 + 20 * gui.scale

		ddt.text_background_colour = colours.box_background

		ddt.text((x, y), _("Metadata side panel"), colours.box_text_label, 12)

		y += 25 * gui.scale
		self.toggle_square(x, y, toggle_side_panel_layout, _("Use centered style"))
		y += 25 * gui.scale
		old = prefs.zoom_art
		prefs.zoom_art = self.toggle_square(x, y, prefs.zoom_art, _("Zoom album art to fit"))
		if prefs.zoom_art != old:
			album_art_gen.clear_cache()

		global album_mode_art_size
		global update_layout
		y += 35 * gui.scale
		ddt.text((x, y), _("Gallery"), colours.box_text_label, 12)

		y += 25 * gui.scale
		# self.toggle_square(x, y, toggle_dim_albums, "Dim gallery when playing")
		self.toggle_square(x, y, toggle_gallery_click, _("Single click to play"))
		y += 25 * gui.scale
		self.toggle_square(x, y, toggle_gallery_combine, _("Combine multi-discs"))
		y += 25 * gui.scale
		self.toggle_square(x, y, toggle_galler_text, _("Show titles"))
		y += 25 * gui.scale
		# self.toggle_square(x, y, toggle_gallery_row_space, _("Increase row spacing"))
		# y += 25 * gui.scale
		prefs.center_gallery_text = self.toggle_square(
			x + round(10 * gui.scale), y, prefs.center_gallery_text, _("Center alignment"))

		y += 30 * gui.scale

		# y += 25 * gui.scale

		x -= 80 * gui.scale
		x += ddt.get_text_w(_("Thumbnail size"), 312)
		# x += 20 * gui.scale

		if album_mode_art_size < 160:
			self.toggle_square(x + 235 * gui.scale, y + 2 * gui.scale, toggle_gallery_thin, _("Prefer thinner padding"))

		# ddt.text((x, y), _("Gallery art size"), colours.grey(220), 11)

		album_mode_art_size = self.slide_control(
			x + 25 * gui.scale, y, _("Thumbnail size"), "px", album_mode_art_size, 70, 400, 10, img_slide_update_gall)

	def funcs(self, x0, y0, w0, h0):

		x = x0 + 25 * gui.scale
		y = y0 - 10 * gui.scale

		ddt.text_background_colour = colours.box_background

		if self.func_page == 0:

			y += 23 * gui.scale

			self.toggle_square(
				x, y, toggle_enable_web, _("Enable Listen Along"), subtitle=_("Start server for remote web playback"))

			if toggle_enable_web(1):

				link_pa2 = draw_linked_text(
					(x + 300 * gui.scale, y - 1 * gui.scale),
					f"http://localhost:{prefs.metadata_page_port!s}/listenalong",
					colours.grey_blend_bg(190), 13)
				link_rect2 = [x + 300 * gui.scale, y - 1 * gui.scale, link_pa2[1], 20 * gui.scale]
				fields.add(link_rect2)

				if coll(link_rect2):
					if not self.click:
						gui.cursor_want = 3

					if self.click:
						webbrowser.open(link_pa2[2], new=2, autoraise=True)

			y += 38 * gui.scale

			old = gui.artist_info_panel
			new = self.toggle_square(
				x, y, gui.artist_info_panel,
				_("Show artist info panel"),
				subtitle=_("You can also toggle this with ctrl+o"))
			if new != old:
				view_box.artist_info(True)

			y += 38 * gui.scale

			self.toggle_square(
				x, y, toggle_auto_artist_dl,
				_("Auto fetch artist data"),
				subtitle=_("Downloads data in background when artist panel is open"))

			y += 38 * gui.scale
			prefs.always_auto_update_playlists = self.toggle_square(
				x, y, prefs.always_auto_update_playlists,
				_("Auto regenerate playlists"),
				subtitle=_("Generated playlists reload when re-entering"))

			y += 38 * gui.scale
			self.toggle_square(
				x, y, toggle_top_tabs, _("Tabs in top panel"),
				subtitle=_("Uncheck to disable the tab pin function"))

			y += 45 * gui.scale
			# y += 30 * gui.scale

			wa = ddt.get_text_w(_("Open config file"), 211) + 10 * gui.scale
			# wb = ddt.get_text_w(_("Open keymap file"), 211) + 10 * gui.scale
			wc = ddt.get_text_w(_("Open data folder"), 211) + 10 * gui.scale

			ww = max(wa, wc)

			self.button(x, y, _("Open config file"), open_config_file, width=ww)
			bg = None
			if gui.opened_config_file:
				bg = [90, 50, 130, 255]
				self.button(x + ww + wc + 25 * gui.scale, y, _("Reload"), reload_config_file, bg=bg)

			self.button(x + wa + round(20 * gui.scale), y, _("Open data folder"), open_data_directory, ww)

		elif self.func_page == 1:
			y += 23 * gui.scale
			ddt.text((x, y), _("Enable/Disable track context menu functions:"), colours.box_text_label, 11)
			y += 25 * gui.scale

			self.toggle_square(x, y, toggle_wiki, _("Wikipedia artist search"))
			y += 23 * gui.scale
			self.toggle_square(x, y, toggle_rym, _("Sonemic artist search"))
			y += 23 * gui.scale
			self.toggle_square(x, y, toggle_band, _("Bandcamp artist page search"))
			# y += 23 * gui.scale
			# self.toggle_square(x, y, toggle_gimage, _("Google image search"))
			y += 23 * gui.scale
			self.toggle_square(x, y, toggle_gen, _("Genius track search"))
			y += 23 * gui.scale
			self.toggle_square(x, y, toggle_transcode, _("Transcode folder"))

			y += 28 * gui.scale

			x = x0 + self.item_x_offset

			ddt.text((x, y), _("End of playlist action"), colours.box_text_label, 12)

			y += 25 * gui.scale
			wa = ddt.get_text_w(_("Stop playback"), 13) + 10 * gui.scale
			wb = ddt.get_text_w(_("Repeat playlist"), 13) + 10 * gui.scale
			wc = max(wa, wb) + 20 * gui.scale

			self.toggle_square(x, y, self.set_playlist_stop, _("Stop playback"))
			y += 25 * gui.scale
			self.toggle_square(x, y, self.set_playlist_repeat, _("Repeat playlist"))
			# y += 25
			y -= 25 * gui.scale
			x += wc
			self.toggle_square(x, y, self.set_playlist_advance, _("Play next playlist"))
			y += 25 * gui.scale
			self.toggle_square(x, y, self.set_playlist_cycle, _("Cycle all playlists"))

		elif self.func_page == 2:
			y += 23 * gui.scale
			# ddt.text((x, y), _("Auto download monitor and archive extractor"), colours.box_text_label, 11)
			# y += 25 * gui.scale
			self.toggle_square(
				x, y, toggle_extract, _("Extract archives"),
				subtitle=_("Extracts zip archives on drag and drop"))
			y += 38 * gui.scale
			self.toggle_square(
				x + 10 * gui.scale, y, toggle_dl_mon, _("Enable download monitor"),
				subtitle=_("One click import new archives and folders from downloads folder"))
			y += 38 * gui.scale
			self.toggle_square(x + 10 * gui.scale, y, toggle_ex_del, _("Trash archive after extraction"))
			y += 23 * gui.scale
			self.toggle_square(x + 10 * gui.scale, y, toggle_music_ex, _("Always extract to Music folder"))

			y += 38 * gui.scale
			if not msys:
				self.toggle_square(x, y, toggle_use_tray, _("Show icon in system tray"))

				y += 25 * gui.scale
				self.toggle_square(x + round(10 * gui.scale), y, toggle_min_tray, _("Close to tray"))

				y += 25 * gui.scale
				self.toggle_square(x + round(10 * gui.scale), y, toggle_text_tray, _("Show title text"))

				old = prefs.tray_theme
				if not self.toggle_square(x + round(190 * gui.scale), y, prefs.tray_theme == "gray", _("Monochrome")):
					prefs.tray_theme = "pink"
				else:
					prefs.tray_theme = "gray"
				if prefs.tray_theme != old:
					tauon.set_tray_icons(force=True)
					show_message(_("Restart Tauon for change to take effect"))

			else:
				self.toggle_square(x, y, toggle_min_tray, _("Close to tray"))



		elif self.func_page == 4:
			y += 23 * gui.scale
			prefs.use_gamepad = self.toggle_square(
				x, y, prefs.use_gamepad, _("Enable use of gamepad as input"),
				subtitle=_("Change requires restart"))
			y += 37 * gui.scale

		elif self.func_page == 3:
			y += 23 * gui.scale
			old = prefs.enable_remote
			prefs.enable_remote = self.toggle_square(
				x, y, prefs.enable_remote, _("Enable remote control"),
				subtitle=_("Change requires restart"))
			y += 37 * gui.scale

			if prefs.enable_remote and prefs.enable_remote != old:
				show_message(
					_("Notice: This API is not security hardened."),
					_("Only enable in a trusted LAN and do not expose port (7814) to the internet"),
					mode="warning")

			old = prefs.block_suspend
			prefs.block_suspend = self.toggle_square(
				x, y, prefs.block_suspend, _("Block suspend"),
				subtitle=_("Prevent system suspend during playback"))
			y += 37 * gui.scale
			old = prefs.block_suspend
			prefs.resume_play_wake = self.toggle_square(
				x, y, prefs.resume_play_wake, _("Resume from suspend"),
				subtitle=_("Continue playback when waking from sleep"))

			y += 37 * gui.scale
			old = prefs.auto_rec
			prefs.auto_rec = self.toggle_square(
				x, y, prefs.auto_rec, _("Record Radio"),
				subtitle=_("Record and split songs when playing internet radio"))
			if prefs.auto_rec != old and prefs.auto_rec:
				show_message(
					_("Tracks will now be recorded. Restart any playback for change to take effect."),
					_("Tracks will be saved to \"Saved Radio Tracks\" playlist."),
					mode="info")

			if tauon.update_play_lock is None:
				prefs.block_suspend = False
				# if flatpak_mode:
				#     show_message("Sandbox support not implemented")
			elif old != prefs.block_suspend:
				tauon.update_play_lock()

			y += 37 * gui.scale
			ddt.text((x, y), "Discord", colours.box_text_label, 11)
			y += 25 * gui.scale
			old = prefs.discord_enable
			prefs.discord_enable = self.toggle_square(x, y, prefs.discord_enable, _("Enable Discord Rich Presence"))

			if flatpak_mode:
				if self.button(x + 215 * gui.scale, y, _("?")):
					show_message(
						_("For troubleshooting Discord RP"),
						"https://github.com/Taiko2k/TauonMusicBox/wiki/Discord-RP", mode="link")

			if prefs.discord_enable and not old:
				if snap_mode:
					show_message(_("Sorry, this feature is unavailable with snap"), mode="error")
					prefs.discord_enable = False
				elif not discord_allow:
					show_message(_("Missing dependency python-pypresence"))
					prefs.discord_enable = False
				else:
					hit_discord()

			if old and not prefs.discord_enable:
				if prefs.discord_active:
					prefs.disconnect_discord = True

			y += 22 * gui.scale
			text = _("Disabled")
			if prefs.discord_enable:
				text = gui.discord_status
			ddt.text((x, y), _("Status: {state}").format(state=text), colours.box_text, 11)

		# Switcher
		pages = 5
		x = x0 + round(18 * gui.scale)
		y = (y0 + h0) - round(29 * gui.scale)
		ww = round(40 * gui.scale)

		for p in range(pages):
			if self.button2(x, y, str(p + 1), width=ww, center_text=True, force_on=self.func_page == p):
				self.func_page = p
			x += ww

		# self.button(x, y, _("Open keymap file"), open_keymap_file, width=wc)

	def button(self, x, y, text, plug=None, width=0, bg=None):

		w = width
		if w == 0:
			w = ddt.get_text_w(text, 211) + round(10 * gui.scale)

		h = round(20 * gui.scale)
		border_size = round(2 * gui.scale)

		rect = (round(x), round(y), round(w), round(h))
		rect2 = (rect[0] - border_size, rect[1] - border_size, rect[2] + border_size * 2, rect[3] + border_size * 2)

		if bg is None:
			bg = colours.box_background

		real_bg = bg
		hit = False

		ddt.rect(rect2, colours.box_check_border)
		ddt.rect(rect, bg)

		fields.add(rect)
		if coll(rect):
			ddt.rect(rect, [255, 255, 255, 15])
			real_bg = alpha_blend([255, 255, 255, 15], bg)
			ddt.text((x + int(w / 2), rect[1] + 1 * gui.scale, 2), text, colours.box_title_text, 211, bg=real_bg)
			if self.click:
				hit = True
				if plug is not None:
					plug()
		else:
			ddt.text((x + int(w / 2), rect[1] + 1 * gui.scale, 2), text, colours.box_sub_text, 211, bg=real_bg)

		return hit

	def button2(self, x, y, text, width=0, center_text=False, force_on=False):
		w = width
		if w == 0:
			w = ddt.get_text_w(text, 211) + 10 * gui.scale
		rect = (x, y, w, 20 * gui.scale)

		bg_colour = colours.box_button_background
		real_bg = bg_colour

		ddt.rect(rect, bg_colour)
		fields.add(rect)
		hit = False

		text_position = (x + int(7 * gui.scale), rect[1] + 1 * gui.scale)
		if center_text:
			text_position = (x + rect[2] // 2, rect[1] + 1 * gui.scale, 2)

		if coll(rect) or force_on:
			ddt.rect(rect, colours.box_button_background_highlight)
			bg_colour = colours.box_button_background
			real_bg = alpha_blend(colours.box_button_background_highlight, bg_colour)
			ddt.text(text_position, text, colours.box_button_text_highlight, 211, bg=real_bg)
			if self.click and not force_on:
				hit = True
		else:
			ddt.text(text_position, text, colours.box_button_text, 211, bg=real_bg)
		return hit

	def toggle_square(self, x, y, function, text: str , click: bool = False, subtitle: str = "") -> bool:

		x = round(x)
		y = round(y)

		border = round(2 * gui.scale)
		gap = round(2 * gui.scale)
		inner_square = round(6 * gui.scale)

		full_w = border * 2 + gap * 2 + inner_square

		if subtitle:
			le = ddt.text((x + 20 * gui.scale, y - 1 * gui.scale), text, colours.box_text, 13)
			se = ddt.text((x + 20 * gui.scale, y + 14 * gui.scale), subtitle, colours.box_text_label, 13)
			hit_rect = (x - 10 * gui.scale, y - 3 * gui.scale, max(le, se) + 30 * gui.scale, 34 * gui.scale)
			y += round(8 * gui.scale)

		else:
			le = ddt.text((x + 20 * gui.scale, y - 1 * gui.scale), text, colours.box_text, 13)
			hit_rect = (x - 10 * gui.scale, y - 3 * gui.scale, le + 30 * gui.scale, 22 * gui.scale)

		# Border outline
		ddt.rect_a((x, y), (full_w, full_w), colours.box_check_border)
		# Inner background
		ddt.rect_a(
			(x + border, y + border), (gap * 2 + inner_square, gap * 2 + inner_square),
			alpha_blend([255, 255, 255, 14], colours.box_background))

		# Check if box clicked
		clicked = False
		if (self.click or click) and coll(hit_rect):
			clicked = True

		# There are two mode, function type, and passthrough bool type
		active = False
		if type(function) is bool:
			active = function
		else:
			active = function(1)

		if clicked:
			if type(function) is bool:
				active ^= True
			else:
				function()
				active = function(1)

		# Draw inner check mark if enabled
		if active:
			ddt.rect_a((x + border + gap, y + border + gap), (inner_square, inner_square), colours.toggle_box_on)

		return active

	def last_fm_box(self, x0, y0, w0, h0):

		x = x0 + round(20 * gui.scale)
		y = y0 + round(15 * gui.scale)

		ddt.text_background_colour = colours.box_background

		text = "Last.fm"
		if prefs.use_libre_fm:
			text = "Libre.fm"
		if self.button2(x, y, text, width=84 * gui.scale):
			self.account_view = 1
		self.toggle_square(x + 105 * gui.scale, y + 2 * gui.scale, toggle_lfm_auto, _("Enable"))

		y += 28 * gui.scale

		if self.button2(x, y, "ListenBrainz", width=84 * gui.scale):
			self.account_view = 2
		self.toggle_square(x + 105 * gui.scale, y + 2 * gui.scale, toggle_lb, _("Enable"))

		y += 28 * gui.scale

		if self.button2(x, y, "Maloja", width=84 * gui.scale):
			self.account_view = 9
		self.toggle_square(x + 105 * gui.scale, y + 2 * gui.scale, toggle_maloja, _("Enable"))

		# if self.button2(x, y, "Discogs", width=84*gui.scale):
		#     self.account_view = 3

		y += 28 * gui.scale

		if self.button2(x, y, "fanart.tv", width=84 * gui.scale):
			self.account_view = 4

		y += 28 * gui.scale
		y += 28 * gui.scale

		y += 15 * gui.scale

		if key_shift_down and self.button2(x + round(95 * gui.scale), y, "koel", width=84 * gui.scale):
			self.account_view = 6

		if self.button2(x, y, "Jellyfin", width=84 * gui.scale):
			self.account_view = 10

		if self.button2(x + round(95 * gui.scale), y, "TIDAL", width=84 * gui.scale):
			self.account_view = 12

		y += 28 * gui.scale

		if self.button2(x, y, "Airsonic", width=84 * gui.scale):
			self.account_view = 7

		if self.button2(x + round(95 * gui.scale), y, "PLEX", width=84 * gui.scale):
			self.account_view = 5

		y += 28 * gui.scale

		if self.button2(x, y, "Spotify", width=84 * gui.scale):
			self.account_view = 8

		if self.button2(x + round(95 * gui.scale), y, "Satellite", width=84 * gui.scale):
			self.account_view = 11

		if self.account_view in (9, 2):
			self.toggle_square(
				x0 + 230 * gui.scale, y + 2 * gui.scale, toggle_scrobble_mark,
				_("Show threshold marker"))

		x = x0 + 230 * gui.scale
		y = y0 + round(20 * gui.scale)

		if self.account_view == 12:
			ddt.text((x, y), "TIDAL", colours.box_sub_text, 213)

			y += round(30 * gui.scale)

			if os.path.isfile(tauon.tidal.save_path):
				if self.button2(x, y, _("Logout"), width=84 * gui.scale):
					tauon.tidal.logout()
			elif tauon.tidal.login_stage == 0:
				if self.button2(x, y, _("Login"), width=84 * gui.scale):
					# webThread = threading.Thread(target=authserve, args=[tauon])
					# webThread.daemon = True
					# webThread.start()
					# time.sleep(0.1)
					tauon.tidal.login1()
			else:
				ddt.text(
					(x + 0 * gui.scale, y), _("Copy the full URL of the resulting 'oops' page"), colours.box_text_label, 11)
				y += round(25 * gui.scale)
				if self.button2(x, y, _("Paste Redirect URL"), width=84 * gui.scale):
					text = copy_from_clipboard()
					if text:
						tauon.tidal.login2(text)

			if os.path.isfile(tauon.tidal.save_path):
				y += round(30 * gui.scale)
				ddt.text((x + 0 * gui.scale, y), _("Paste TIDAL URL's into Tauon using ctrl+v"), colours.box_text_label, 11)
				y += round(30 * gui.scale)
				if self.button(x, y, _("Import Albums")):
					show_message(_("Fetching playlist..."))
					shooter(tauon.tidal.fav_albums)

				y += round(30 * gui.scale)
				if self.button(x, y, _("Import Tracks")):
					show_message(_("Fetching playlist..."))
					shooter(tauon.tidal.fav_tracks)

		if self.account_view == 11:
			ddt.text((x, y), "Tauon Satellite", colours.box_sub_text, 213)

			y += round(30 * gui.scale)

			field_width = round(245 * gui.scale)
			ddt.text((x + 0 * gui.scale, y), _("IP"), colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 0
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_sat_url.text = prefs.sat_url
			text_sat_url.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 0,
				width=rect1[2] - 8 * gui.scale, click=self.click)
			prefs.sat_url = text_sat_url.text.strip()

			y += round(25 * gui.scale)

			y += round(30 * gui.scale)

			field_width = round(245 * gui.scale)
			ddt.text((x + 0 * gui.scale, y), _("Playlist name"), colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 1
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_sat_playlist.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 1,
				width=rect1[2] - 8 * gui.scale, click=self.click)

			y += round(25 * gui.scale)

			if self.button(x, y, _("Get playlist")):
				if tau.processing:
					show_message(_("An operation is already running"))
				else:
					shooter(tau.get_playlist())

		elif self.account_view == 9:

			ddt.text((x, y), _("Maloja Server"), colours.box_sub_text, 213)
			if self.button(x + 260 * gui.scale, y, _("?")):
				show_message(
					_("Maloja is a self-hosted scrobble server."),
					_("See here to learn more: {link}").format(link="https://github.com/krateng/maloja"), mode="link")

			if inp.key_tab_press:
				self.account_text_field += 1
				if self.account_text_field > 2:
					self.account_text_field = 0

			field_width = round(245 * gui.scale)

			y += round(25 * gui.scale)
			ddt.text(
				(x + 0 * gui.scale, y), _("Server URL"),
				colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 0
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_maloja_url.text = prefs.maloja_url
			text_maloja_url.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 0,
				width=rect1[2] - 8 * gui.scale, click=self.click)
			prefs.maloja_url = text_maloja_url.text.strip()

			y += round(23 * gui.scale)
			ddt.text(
				(x + 0 * gui.scale, y), _("API Key"),
				colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 1
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_maloja_key.text = prefs.maloja_key
			text_maloja_key.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 1,
				width=rect1[2] - 8 * gui.scale, click=self.click)
			prefs.maloja_key = text_maloja_key.text.strip()

			y += round(35 * gui.scale)

			if self.button(x, y, _("Test connectivity")):

				if not prefs.maloja_url or not prefs.maloja_key:
					show_message(_("One or more fields is missing."))
				else:
					url = prefs.maloja_url
					if not url.endswith("/mlj_1"):
						if not url.endswith("/"):
							url += "/"
						url += "apis/mlj_1"
					url += "/test"

					try:
						r = requests.get(url, params={"key": prefs.maloja_key}, timeout=10)
						if r.status_code == 403:
							show_message(_("Connection appeared successful but the API key was invalid"), mode="warning")
						elif r.status_code == 200:
							show_message(_("Connection to Maloja server was successful."), mode="done")
						else:
							show_message(_("The Maloja server returned an error"), r.text, mode="warning")
					except Exception:
						logging.exception("Could not communicate with the Maloja server")
						show_message(_("Could not communicate with the Maloja server"), mode="warning")

			y += round(30 * gui.scale)

			ws = ddt.get_text_w(_("Get scrobble counts"), 211) + 10 * gui.scale
			wcc = ddt.get_text_w(_("Clear"), 211) + 15 * gui.scale
			if self.button(x, y, _("Get scrobble counts")):
				shooter(maloja_get_scrobble_counts)
			self.button(x + ws + round(12 * gui.scale), y, _("Clear"), self.clear_scrobble_counts, width=wcc)

		if self.account_view == 8:

			ddt.text((x, y), "Spotify", colours.box_sub_text, 213)

			prefs.spot_mode = self.toggle_square(x + 80 * gui.scale, y + 2 * gui.scale, prefs.spot_mode, _("Enable"))
			y += round(30 * gui.scale)

			if self.button(x, y, _("View setup instructions")):
				webbrowser.open("https://github.com/Taiko2k/Tauon/wiki/Spotify", new=2, autoraise=True)

			field_width = round(245 * gui.scale)

			y += round(26 * gui.scale)

			ddt.text(
				(x + 0 * gui.scale, y), _("Client ID"),
				colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 0
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_spot_client.text = prefs.spot_client
			text_spot_client.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 0,
				width=rect1[2] - 8 * gui.scale, click=self.click)
			prefs.spot_client = text_spot_client.text.strip()

			y += round(19 * gui.scale)
			ddt.text(
				(x + 0 * gui.scale, y), _("Client Secret"),
				colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 1
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_spot_secret.text = prefs.spot_secret
			text_spot_secret.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 1,
				width=rect1[2] - 8 * gui.scale, click=self.click)
			prefs.spot_secret = text_spot_secret.text.strip()

			y += round(27 * gui.scale)

			if prefs.spotify_token:
				if self.button(x, y, _("Forget Account")):
					tauon.spot_ctl.delete_token()
					tauon.spot_ctl.cache_saved_albums.clear()
					prefs.spot_username = ""
					if not prefs.launch_spotify_local:
						prefs.spot_password = ""
			elif self.button(x, y, _("Authorise")):
				webThread = threading.Thread(target=authserve, args=[tauon])
				webThread.daemon = True
				webThread.start()
				time.sleep(0.1)

				tauon.spot_ctl.auth()

			y += round(31 * gui.scale)
			prefs.launch_spotify_web = self.toggle_square(
				x, y, prefs.launch_spotify_web,
				_("Prefer launching web player"))

			y += round(24 * gui.scale)

			old = prefs.launch_spotify_local
			prefs.launch_spotify_local = self.toggle_square(
				x, y, prefs.launch_spotify_local,
				_("Enable local audio playback"))

			if prefs.launch_spotify_local and not tauon.enable_librespot:
				show_message(_("Librespot not installed?"))
				prefs.launch_spotify_local = False


		if self.account_view == 7:

			ddt.text((x, y), _("Airsonic/Subsonic network streaming"), colours.box_sub_text, 213)

			if inp.key_tab_press:
				self.account_text_field += 1
				if self.account_text_field > 2:
					self.account_text_field = 0

			field_width = round(245 * gui.scale)

			y += round(25 * gui.scale)
			ddt.text((x + 0 * gui.scale, y), _("Username / Email"), colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 0
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_air_usr.text = prefs.subsonic_user
			text_air_usr.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 0,
				width=rect1[2] - 8 * gui.scale, click=self.click)
			prefs.subsonic_user = text_air_usr.text

			y += round(23 * gui.scale)
			ddt.text((x + 0 * gui.scale, y), _("Password"), colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 1
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_air_pas.text = prefs.subsonic_password
			text_air_pas.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 1,
				width=rect1[2] - 8 * gui.scale, click=self.click, secret=True)
			prefs.subsonic_password = text_air_pas.text

			y += round(23 * gui.scale)
			ddt.text((x + 0 * gui.scale, y), _("Server URL"), colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 2
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_air_ser.text = prefs.subsonic_server
			text_air_ser.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 2,
				width=rect1[2] - 8 * gui.scale, click=self.click)
			prefs.subsonic_server = text_air_ser.text

			y += round(40 * gui.scale)
			self.button(x, y, _("Import music to playlist"), sub_get_album_thread)

			y += round(35 * gui.scale)
			prefs.subsonic_password_plain = self.toggle_square(
				x, y, prefs.subsonic_password_plain,
				_("Use plain text authentication"),
				subtitle=_("Needed for Nextcloud Music"))

		if self.account_view == 10:

			ddt.text((x, y), _("Jellyfin network streaming"), colours.box_sub_text, 213)

			if inp.key_tab_press:
				self.account_text_field += 1
				if self.account_text_field > 2:
					self.account_text_field = 0

			field_width = round(245 * gui.scale)

			y += round(25 * gui.scale)
			ddt.text((x + 0 * gui.scale, y), _("Username"), colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 0
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_jelly_usr.text = prefs.jelly_username
			text_jelly_usr.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 0,
				width=rect1[2] - 8 * gui.scale, click=self.click)
			prefs.jelly_username = text_jelly_usr.text

			y += round(23 * gui.scale)
			ddt.text((x + 0 * gui.scale, y), _("Password"), colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 1
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_jelly_pas.text = prefs.jelly_password
			text_jelly_pas.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 1,
				width=rect1[2] - 8 * gui.scale, click=self.click, secret=True)
			prefs.jelly_password = text_jelly_pas.text

			y += round(23 * gui.scale)
			ddt.text((x + 0 * gui.scale, y), _("Server URL"), colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 2
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_jelly_ser.text = prefs.jelly_server_url
			text_jelly_ser.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 2,
				width=rect1[2] - 8 * gui.scale, click=self.click)
			prefs.jelly_server_url = text_jelly_ser.text

			y += round(30 * gui.scale)

			self.button(x, y, _("Import music to playlist"), jellyfin_get_library_thread)

			y += round(30 * gui.scale)
			if self.button(x, y, _("Import playlists")):
				found = False
				for item in pctl.gen_codes.values():
					if item.startswith("jelly"):
						found = True
						break
				if not found:
					gui.show_message(_("Run music import first"))
				else:
					jellyfin_get_playlists_thread()

			y += round(35 * gui.scale)
			if self.button(x, y, _("Test connectivity")):
				jellyfin.test()

		if self.account_view == 6:

			ddt.text((x, y), _("koel network streaming"), colours.box_sub_text, 213)

			if inp.key_tab_press:
				self.account_text_field += 1
				if self.account_text_field > 2:
					self.account_text_field = 0

			field_width = round(245 * gui.scale)

			y += round(25 * gui.scale)
			ddt.text((x + 0 * gui.scale, y), _("Username / Email"), colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 0
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_koel_usr.text = prefs.koel_username
			text_koel_usr.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 0,
				width=rect1[2] - 8 * gui.scale, click=self.click)
			prefs.koel_username = text_koel_usr.text

			y += round(23 * gui.scale)
			ddt.text((x + 0 * gui.scale, y), _("Password"), colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 1
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_koel_pas.text = prefs.koel_password
			text_koel_pas.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 1,
				width=rect1[2] - 8 * gui.scale, click=self.click, secret=True)
			prefs.koel_password = text_koel_pas.text

			y += round(23 * gui.scale)
			ddt.text((x + 0 * gui.scale, y), _("Server URL"), colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 2
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_koel_ser.text = prefs.koel_server_url
			text_koel_ser.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 2,
				width=rect1[2] - 8 * gui.scale, click=self.click)
			prefs.koel_server_url = text_koel_ser.text

			y += round(40 * gui.scale)

			self.button(x, y, _("Import music to playlist"), koel_get_album_thread)

		if self.account_view == 5:

			ddt.text((x, y), _("PLEX network streaming"), colours.box_sub_text, 213)

			if inp.key_tab_press:
				self.account_text_field += 1
				if self.account_text_field > 2:
					self.account_text_field = 0

			field_width = round(245 * gui.scale)

			y += round(25 * gui.scale)
			ddt.text((x + 0 * gui.scale, y), _("Username / Email"), colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 0
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_plex_usr.text = prefs.plex_username
			text_plex_usr.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 0,
				width=rect1[2] - 8 * gui.scale, click=self.click)
			prefs.plex_username = text_plex_usr.text

			y += round(23 * gui.scale)
			ddt.text((x + 0 * gui.scale, y), _("Password"), colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 1
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_plex_pas.text = prefs.plex_password
			text_plex_pas.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 1,
				width=rect1[2] - 8 * gui.scale, click=self.click, secret=True)
			prefs.plex_password = text_plex_pas.text

			y += round(23 * gui.scale)
			ddt.text((x + 0 * gui.scale, y), _("Server name"), colours.box_text_label, 11)
			y += round(19 * gui.scale)
			rect1 = (x + 0 * gui.scale, y, field_width, round(17 * gui.scale))
			fields.add(rect1)
			if coll(rect1) and (self.click or level_2_right_click):
				self.account_text_field = 2
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			text_plex_ser.text = prefs.plex_servername
			text_plex_ser.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, self.account_text_field == 2,
				width=rect1[2] - 8 * gui.scale, click=self.click)
			prefs.plex_servername = text_plex_ser.text

			y += round(40 * gui.scale)
			self.button(x, y, _("Import music to playlist"), plex_get_album_thread)

		if self.account_view == 4:

			ddt.text((x, y), "fanart.tv", colours.box_sub_text, 213)

			y += 25 * gui.scale
			ddt.text(
				(x + 0 * gui.scale, y, 4, 270 * gui.scale, 600),
				_("Fanart.tv can be used for sourcing of artist images and cover art."),
				colours.box_text_label, 11)
			y += 17 * gui.scale

			y += 22 * gui.scale
			# . Limited space available. Limit 55 chars
			link_pa2 = draw_linked_text(
				(x + 0 * gui.scale, y),
				_("They encourage you to contribute at {link}").format(link="https://fanart.tv"),
				colours.box_text_label, 11)
			link_activate(x, y, link_pa2)

			y += 35 * gui.scale
			prefs.enable_fanart_cover = self.toggle_square(
				x, y, prefs.enable_fanart_cover,
				_("Cover art (Manual only)"))
			y += 25 * gui.scale
			prefs.enable_fanart_artist = self.toggle_square(
				x, y, prefs.enable_fanart_artist,
				_("Artist images (Automatic)"))
			#y += 25 * gui.scale
			# prefs.enable_fanart_bg = self.toggle_square(x, y, prefs.enable_fanart_bg,
			#                                             _("Artist backgrounds (Automatic)"))
			y += 25 * gui.scale
			x += 23 * gui.scale
			if self.button(x, y, _("Flip current")):
				if key_shift_down:
					prefs.bg_flips.clear()
					show_message(_("Reset flips"), mode="done")
				else:
					tr = pctl.playing_object()
					artist = get_artist_safe(tr)
					if artist:
						if artist not in prefs.bg_flips:
							prefs.bg_flips.add(artist)
						else:
							prefs.bg_flips.remove(artist)
					style_overlay.flush()
					show_message(_("OK"), mode="done")

		# if self.account_view == 3:
		#
		#     ddt.text((x, y), 'Discogs', colours.box_sub_text, 213)
		#
		#     y += 25 * gui.scale
		#     hh = ddt.text((x + 0 * gui.scale, y, 4, 260 * gui.scale, 300 * gui.scale), _("Discogs can be used for sourcing artist images. For this you will need a \"Personal Access Token\".\n\nYou can generate one with a Discogs account here:"),
		#              colours.box_text_label, 11)
		#
		#
		#     y += hh
		#     #y += 15 * gui.scale
		#     link_pa2 = draw_linked_text((x + 0 * gui.scale, y), "https://www.discogs.com/settings/developers",colours.box_text_label, 12)
		#     link_rect2 = [x + 0 * gui.scale, y, link_pa2[1], 20 * gui.scale]
		#     fields.add(link_rect2)
		#     if coll(link_rect2):
		#         if not self.click:
		#             gui.cursor_want = 3
		#         if self.click:
		#             webbrowser.open(link_pa2[2], new=2, autoraise=True)
		#
		#     y += 40 * gui.scale
		#     if self.button(x, y, _("Paste Token")):
		#
		#         text = copy_from_clipboard()
		#         if text == "":
		#             show_message(_("There is no text in the clipboard", mode='error')
		#         elif len(text) == 40:
		#             prefs.discogs_pat = text
		#
		#             # Reset caches -------------------
		#             prefs.failed_artists.clear()
		#             artist_list_box.to_fetch = ""
		#             for key, value in artist_list_box.thumb_cache.items():
		#                 if value:
		#                     SDL_DestroyTexture(value[0])
		#             artist_list_box.thumb_cache.clear()
		#             artist_list_box.to_fetch = ""
		#
		#             direc = os.path.join(a_cache_dir)
		#             if os.path.isdir(direc):
		#                 for item in os.listdir(direc):
		#                     if "-lfm.txt" in item:
		#                         os.remove(os.path.join(direc, item))
		#             # -----------------------------------
		#
		#         else:
		#             show_message(_("That is not a valid token", mode='error')
		#     y += 30 * gui.scale
		#     if self.button(x, y, _("Clear")):
		#         if not prefs.discogs_pat:
		#             show_message(_("There wasn't any token saved.")
		#         prefs.discogs_pat = ""
		#         save_prefs()
		#
		#     y += 30 * gui.scale
		#     if prefs.discogs_pat:
		#         ddt.text((x + 0 * gui.scale, y - 0 * gui.scale), prefs.discogs_pat, colours.box_input_text, 211)
		#

		if self.account_view == 1:

			text = "Last.fm"
			if prefs.use_libre_fm:
				text = "Libre.fm"

			ddt.text((x, y), text, colours.box_sub_text, 213)

			ww = ddt.get_text_w(_("Username:"), 212)
			ddt.text((x + 65 * gui.scale, y - 0 * gui.scale), _("Username:"), colours.box_text_label, 212)
			ddt.text(
				(x + ww + 65 * gui.scale + 7 * gui.scale, y - 0 * gui.scale), prefs.last_fm_username,
				colours.box_sub_text, 213)

			y += 25 * gui.scale

			if prefs.last_fm_token is None:
				ww = ddt.get_text_w(_("Login"), 211) + 10 * gui.scale
				ww2 = ddt.get_text_w(_("Done"), 211) + 40 * gui.scale
				self.button(x, y, _("Login"), lastfm.auth1)
				self.button(x + ww + 10 * gui.scale, y, _("Done"), lastfm.auth2)

				if prefs.last_fm_token is None and lastfm.url is None:
					prefs.use_libre_fm = self.toggle_square(
						x + ww + ww2, y + round(1 * gui.scale), prefs.use_libre_fm, _("Use LibreFM"))

				y += 25 * gui.scale
				ddt.text(
					(x + 2 * gui.scale, y, 4, 270 * gui.scale, 300 * gui.scale),
					_("Click login to open the last.fm web authorisation page and follow prompt. Then return here and click \"Done\"."),
					colours.box_text_label, 11, max_w=270 * gui.scale)

			else:
				self.button(x, y, _("Forget account"), lastfm.auth3)

			x = x0 + 230 * gui.scale
			y = y0 + round(130 * gui.scale)

			# self.toggle_square(x, y, toggle_scrobble_mark, "Show scrobble marker")

			wa = ddt.get_text_w(_("Get user loves"), 211) + 10 * gui.scale
			wb = ddt.get_text_w(_("Clear local loves"), 211) + 10 * gui.scale
			wc = ddt.get_text_w(_("Get friend loves"), 211) + 10 * gui.scale
			ws = ddt.get_text_w(_("Get scrobble counts"), 211) + 10 * gui.scale
			wcc = ddt.get_text_w(_("Clear"), 211) + 15 * gui.scale
			# wd = ddt.get_text_w(_("Clear friend loves"),211) + 10 * gui.scale
			ww = max(wa, wb, wc, ws)

			self.button(x, y, _("Get user loves"), self.get_user_love, width=ww)
			self.button(x + ww + round(12 * gui.scale), y, _("Clear"), self.clear_local_loves, width=wcc)

			# y += 26 * gui.scale
			# self.button(x, y, _("Clear local loves"), self.clear_local_loves, width=ww)

			y += 26 * gui.scale

			self.button(x, y, _("Get friend loves"), self.get_friend_love, width=ww)
			self.button(x + ww + round(12 * gui.scale), y, _("Clear"), lastfm.clear_friends_love, width=wcc)

			y += 26 * gui.scale
			self.button(x, y, _("Get scrobble counts"), self.get_scrobble_counts, width=ww)
			self.button(x + ww + round(12 * gui.scale), y, _("Clear"), self.clear_scrobble_counts, width=wcc)


			y += 33 * gui.scale

			old = prefs.lastfm_pull_love
			prefs.lastfm_pull_love = self.toggle_square(
				x, y, prefs.lastfm_pull_love,
				_("Pull love on scrobble/rescan"))
			if old != prefs.lastfm_pull_love and prefs.lastfm_pull_love:
				show_message(_("Note that this will overwrite the local loved status if different to last.fm status"))

			y += 25 * gui.scale

			self.toggle_square(
				x, y, toggle_scrobble_mark,
				_("Show threshold marker"))

		if self.account_view == 2:

			ddt.text((x, y), "ListenBrainz", colours.box_sub_text, 213)

			y += 30 * gui.scale
			self.button(x, y, _("Paste Token"), lb.paste_key)

			self.button(x + ddt.get_text_w(_("Paste Token"), 211) + 21 * gui.scale, y, _("Clear"), lb.clear_key)

			y += 35 * gui.scale

			if prefs.lb_token:
				line = prefs.lb_token
				ddt.text((x + 0 * gui.scale, y - 0 * gui.scale), line, colours.box_input_text, 212)

			y += 25 * gui.scale
			link_pa2 = draw_linked_text((x + 0 * gui.scale, y), "https://listenbrainz.org/profile/",
										colours.box_sub_text, 12)
			link_rect2 = [x + 0 * gui.scale, y, link_pa2[1], 20 * gui.scale]
			fields.add(link_rect2)

			if coll(link_rect2):
				if not self.click:
					gui.cursor_want = 3

				if self.click:
					webbrowser.open(link_pa2[2], new=2, autoraise=True)

	def clear_local_loves(self):

		if not key_shift_down:
			show_message(
				_("This will mark all tracks in local database as unloved!"),
				_("Press button again while holding shift key if you're sure you want to do that."),
				mode="warning")
			return

		for key, star in star_store.db.items():
			star[1] = star[1].replace("L", "")
			star_store.db[key] = star

		gui.pl_update += 1
		show_message(_("Cleared all loves"), mode="done")

	def get_scrobble_counts(self):

		if not key_shift_down:
			t = lastfm.get_all_scrobbles_estimate_time()
			if not t:
				show_message(_("Error, not  connected to last.fm"))
				return
			show_message(
				_("Warning: This process will take approximately {T} minutes to complete.").format(T=(t // 60)),
				_("Press again while holding Shift if you understand"), mode="warning")
			return

		if not lastfm.scanning_friends and not lastfm.scanning_scrobbles and not lastfm.scanning_loves:
			shoot_dl = threading.Thread(target=lastfm.get_all_scrobbles)
			shoot_dl.daemon = True
			shoot_dl.start()
		else:
			show_message(_("A process is already running. Wait for it to finish."))

	def clear_scrobble_counts(self):

		for track in pctl.master_library.values():
			track.lfm_scrobbles = 0

		show_message(_("Cleared all scrobble counts"), mode="done")

	def get_friend_love(self):

		if not key_shift_down:
			show_message(
				_("Warning: This process can take a long time to complete! (up to an hour or more)"),
				_("This feature is not recommended for accounts that have many friends."),
				_("Press again while holding Shift if you understand"), mode="warning")
			return

		if not lastfm.scanning_friends and not lastfm.scanning_scrobbles and not lastfm.scanning_loves:
			logging.info("Launch friend love thread")
			shoot_dl = threading.Thread(target=lastfm.get_friends_love)
			shoot_dl.daemon = True
			shoot_dl.start()
		else:
			show_message(_("A process is already running. Wait for it to finish."))

	def get_user_love(self):

		if not lastfm.scanning_friends and not lastfm.scanning_scrobbles and not lastfm.scanning_loves:
			shoot_dl = threading.Thread(target=lastfm.dl_love)
			shoot_dl.daemon = True
			shoot_dl.start()
		else:
			show_message(_("A process is already running. Wait for it to finish."))

	def codec_config(self, x0, y0, w0, h0):

		x = x0 + round(25 * gui.scale)
		y = y0

		y += 20 * gui.scale
		ddt.text_background_colour = colours.box_background

		if self.sync_view:

			pl = None
			if prefs.sync_playlist:
				pl = id_to_pl(prefs.sync_playlist)
			if pl is None:
				prefs.sync_playlist = None

			y += 5 * gui.scale
			if prefs.sync_playlist:
				ww = ddt.text((x, y), _("Selected playlist:") + "    ", colours.box_text_label, 11)
				ddt.text((x + ww, y), pctl.multi_playlist[pl].title, colours.box_sub_text, 12, 400 * gui.scale)
			else:
				ddt.text((x, y), _("No sync playlist selected!"), colours.box_text_label, 11)

			y += 25 * gui.scale
			ww = ddt.text((x, y), _("Path to device music folder:   "), colours.box_text_label, 11)
			y += 20 * gui.scale

			rect1 = (x + 0 * gui.scale, y, round(450 * gui.scale), round(17 * gui.scale))
			fields.add(rect1)
			ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))
			sync_target.draw(
				x + round(4 * gui.scale), y, colours.box_input_text, not gui.sync_progress,
				width=rect1[2] - 8 * gui.scale, click=self.click)

			rect = [x + rect1[2] + 11 * gui.scale, y - 2 * gui.scale, 15 * gui.scale, 19 * gui.scale]
			fields.add(rect)
			colour = colours.box_text_label
			if coll(rect):
				colour = [225, 160, 0, 255]
				if self.click:
					paths = auto_get_sync_targets()
					if paths:
						sync_target.text = paths[0]
						show_message(_("A mounted music folder was found!"), mode="done")
					else:
						show_message(
							_("Could not auto-detect mounted device path."),
							_("Make sure the device is mounted and path is accessible."))

			power_bar_icon.render(rect[0], rect[1], colour)
			y += 30 * gui.scale

			prefs.sync_deletes = self.toggle_square(x, y, prefs.sync_deletes, _("Delete all other folders in target"))
			y += 25 * gui.scale
			prefs.bypass_transcode = self.toggle_square(
				x, y, prefs.bypass_transcode ^ True,
				_("Transcode files")) ^ True
			y += 25 * gui.scale
			prefs.smart_bypass = self.toggle_square(
				x + round(10 * gui.scale), y, prefs.smart_bypass ^ True,
				_("Bypass low bitrate")) ^ True
			y += 30 * gui.scale

			text = _("Start Transcode and Sync")
			ww = ddt.get_text_w(text, 211) + 25 * gui.scale
			if prefs.bypass_transcode:
				text = _("Start Sync")

			xx = (rect1[0] + (rect1[2] // 2)) - (ww // 2)
			if gui.stop_sync:
				self.button(xx, y, _("Stopping..."), width=ww)
			elif not gui.sync_progress:
				if self.button(xx, y, text, width=ww):
					if pl is not None:
						auto_sync(pl)
					else:
						show_message(
							_("Select a source playlist"),
							_("Right click tab > Misc... > Set as sync playlist"))
			elif self.button(xx, y, _("Stop"), width=ww):
				gui.stop_sync = True
				gui.sync_progress = _("Aborting Sync")

			y += 60 * gui.scale

			if self.button(x, y, _("Return"), width=round(75 * gui.scale)):
				self.sync_view = False

			if self.button(x + 485 * gui.scale, y, _("?")):
				show_message(
					_("See here for detailed instructions"),
					"https://github.com/Taiko2k/Tauon/wiki/Transcode-and-Sync", mode="link")

			return

		# ----------

		ddt.text((x, y + 13 * gui.scale), _("Output codec setting:"), colours.box_text_label, 11)

		ww = ddt.get_text_w(_("Open output folder"), 211) + 25 * gui.scale
		self.button(x0 + w0 - ww, y - 4 * gui.scale, _("Open output folder"), open_encode_out)

		ww = ddt.get_text_w(_("Sync..."), 211) + 25 * gui.scale
		if self.button(x0 + w0 - ww, y + 25 * gui.scale, _("Sync...")):
			self.sync_view = True

		y += 40 * gui.scale
		self.toggle_square(x, y, switch_flac, "FLAC")
		y += 25 * gui.scale
		self.toggle_square(x, y, switch_opus, "OPUS")
		if prefs.transcode_codec == "opus":
			self.toggle_square(x + 120 * gui.scale, y, switch_opus_ogg, _("Save opus as .ogg extension"))
		y += 25 * gui.scale
		self.toggle_square(x, y, switch_ogg, "OGG Vorbis")
		y += 25 * gui.scale

		# if not flatpak_mode:
		self.toggle_square(x, y, switch_mp3, "MP3")
		# if prefs.transcode_codec == 'mp3' and not shutil.which("lame"):
		#     ddt.draw_text((x + 90 * gui.scale, y - 3 * gui.scale), "LAME not detected!", [220, 110, 110, 255], 12)

		if prefs.transcode_codec != "flac":
			y += 35 * gui.scale

			prefs.transcode_bitrate = self.slide_control(x, y, _("Bitrate"), "kbs", prefs.transcode_bitrate, 32, 320, 8)

			y -= 1 * gui.scale
			x += 280 * gui.scale

		x = x0 + round(20 * gui.scale)
		y = y0 + 215 * gui.scale

		self.toggle_square(x, y, toggle_transcode_output, _("Save to output folder"))
		y += 25 * gui.scale
		self.toggle_square(x, y, toggle_transcode_inplace, _("Save and overwrite files inplace"))

	def devance_theme(self):
		global theme

		theme -= 1
		gui.reload_theme = True
		if theme < 0:
			theme = len(get_themes())

	def config_b(self, x0, y0, w0, h0):

		global album_mode_art_size
		global update_layout

		ddt.text_background_colour = colours.box_background
		x = x0 + round(25 * gui.scale)
		y = y0 + round(20 * gui.scale)

		# ddt.text((x, y), _("Window"),colours.box_text_label, 12)

		if system == "Linux":
			self.toggle_square(x, y, toggle_notifications, _("Emit track change notifications"))

		y += 25 * gui.scale
		self.toggle_square(x, y, toggle_borderless, _("Draw own window decorations"))

		# y += 25 * gui.scale
		# prefs.save_window_position = self.toggle_square(x, y, prefs.save_window_position,
		#                                                 _("Restore window position on restart"))

		y += 25 * gui.scale
		if not draw_border:
			self.toggle_square(x, y, toggle_titlebar_line, _("Show playing in titlebar"))

		#y += 25 * gui.scale
		# if system != 'windows' and (flatpak_mode or snap_mode):
		#     self.toggle_square(x, y, toggle_force_subpixel, _("Enable RGB text antialiasing"))

		y += 25 * gui.scale
		old = prefs.mini_mode_on_top
		prefs.mini_mode_on_top = self.toggle_square(x, y, prefs.mini_mode_on_top, _("Mini-mode always on top"))
		if wayland and prefs.mini_mode_on_top and prefs.mini_mode_on_top != old:
			show_message(_("Always-on-top feature not yet implemented for Wayland mode"), _("You can enable the x11 setting below as a workaround"))

		y += 25 * gui.scale
		self.toggle_square(x, y, toggle_level_meter, _("Top-panel visualiser"))

		y += 25 * gui.scale
		if prefs.backend == 4:
			self.toggle_square(x, y, toggle_showcase_vis, _("Showcase visualisation"))

		y += round(30 * gui.scale)
		# if not msys:
		# y += round(15 * gui.scale)

		ddt.text((x, y), _("UI scale for HiDPI displays"), colours.box_text_label, 12)

		y += round(25 * gui.scale)

		sw = round(200 * gui.scale)
		sh = round(2 * gui.scale)

		slider = (x, y, sw, sh)

		gh = round(14 * gui.scale)
		gw = round(8 * gui.scale)
		grip = [0, y - (gh // 2), gw, gh]

		grip[0] = x
		grip[0] += ((prefs.scale_want - 0.5) / 3 * sw)

		m1 = (x + ((1.0 - 0.5) / 3 * sw), y, sh, sh * 2)
		m2 = (x + ((2.0 - 0.5) / 3 * sw), y, sh, sh * 2)
		m3 = (x + ((3.0 - 0.5) / 3 * sw), y, sh, sh * 2)

		if coll(grow_rect(slider, round(16 * gui.scale))) and mouse_down:
			prefs.scale_want = ((mouse_position[0] - x) / sw * 3) + 0.5
			prefs.x_scale = False
			gui.update_on_drag = True
		prefs.scale_want = max(prefs.scale_want, 0.5)
		prefs.scale_want = min(prefs.scale_want, 3.5)
		prefs.scale_want = round(round(prefs.scale_want / 0.05) * 0.05, 2)
		if prefs.scale_want == 0.95 or prefs.scale_want == 1.05:
			prefs.scale_want = 1.0
		if prefs.scale_want == 1.95 or prefs.scale_want == 2.05:
			prefs.scale_want = 2.0
		if prefs.scale_want == 2.95 or prefs.scale_want == 3.05:
			prefs.scale_want = 3.0

		text = str(prefs.scale_want)
		if len(text) == 3:
			text += "0"
		text += "x"

		if prefs.x_scale:
			text = "auto"

		font = 13
		if not prefs.x_scale and (prefs.scale_want == 1.0 or prefs.scale_want == 2.0 or prefs.scale_want == 3.0):
			font = 313

		ddt.text((x + sw + round(14 * gui.scale), y - round(8 * gui.scale)), text, colours.box_sub_text, font)
		# ddt.text((x + sw + round(14 * gui.scale), y + round(10 * gui.scale)), _("Restart app to apply any changes"), colours.box_text_label, 11)

		ddt.rect(slider, colours.box_text_border)
		ddt.rect(m1, colours.box_text_border)
		ddt.rect(m2, colours.box_text_border)
		ddt.rect(m3, colours.box_text_border)
		ddt.rect(grip, colours.box_text_label)

		y += round(23 * gui.scale)
		self.toggle_square(x, y, self.toggle_x_scale, _("Auto scale"))

		if prefs.scale_want != gui.scale:
			gui.update += 1
			if not mouse_down:
				gui.update_layout()

		y += round(25 * gui.scale)
		if not msys and not macos:
			x11_path = str(user_directory / "x11")
			x11 = os.path.exists(x11_path)
			old = x11
			x11 = self.toggle_square(x, y, x11, _("Prefer x11 when running in Wayland"))
			if old is False and x11 is True:
				with open(x11_path, "a"):
					pass
			elif old is True and x11 is False:
				os.remove(x11_path)

	def toggle_x_scale(self, mode=0):
		if mode == 1:
			return prefs.x_scale
		prefs.x_scale ^= True
		auto_scale()
		gui.update_layout()

	def about(self, x0, y0, w0, h0):

		x = x0 + int(w0 * 0.3) - 10 * gui.scale
		y = y0 + 85 * gui.scale

		ddt.text_background_colour = colours.box_background

		icon_rect = (x - 110 * gui.scale, y - 15 * gui.scale, self.about_image.w, self.about_image.h)

		genre = ""
		if pctl.playing_object() is not None:
			genre = pctl.playing_object().genre.lower()

			if any(s in genre for s in ["ock", "lt"]):
				self.about_image2.render(icon_rect[0], icon_rect[1])
			elif any(s in genre for s in ["kpop", "k-pop", "anime"]):
				self.about_image6.render(icon_rect[0], icon_rect[1])
			elif any(s in genre for s in ["syn", "pop"]):
				self.about_image3.render(icon_rect[0], icon_rect[1])
			elif any(s in genre for s in ["tro", "cid"]):
				self.about_image4.render(icon_rect[0], icon_rect[1])
			elif any(s in genre for s in ["uture"]):
				self.about_image5.render(icon_rect[0], icon_rect[1])
			else:
				genre = ""

		if not genre:
			self.about_image.render(icon_rect[0], icon_rect[1])

		x += 20 * gui.scale
		y -= 10 * gui.scale

		self.title_image.render(x - 1, y, alpha_mod(colours.box_sub_text, 240))

		credit_pages = 5

		if self.click and coll(icon_rect) and self.ani_cred == 0:
			self.ani_cred = 1
			self.ani_fade_on_timer.set()

		fade = 0

		if self.ani_cred == 1:
			t = self.ani_fade_on_timer.get()
			fade = round(t / 0.7 * 255)
			fade = min(fade, 255)

			if t > 0.7:
				self.ani_cred = 2
				self.cred_page += 1
				if self.cred_page > credit_pages:
					self.cred_page = 0
				self.ani_fade_on_timer.set()

			gui.update = 2

		if self.ani_cred == 2:

			t = self.ani_fade_on_timer.get()
			fade = 255 - round(t / 0.7 * 255)
			fade = max(fade, 0)
			if t > 0.7:
				self.ani_cred = 0

			gui.update = 2

		y += 32 * gui.scale

		block_y = y - 10 * gui.scale

		if self.cred_page == 0:

			ddt.text((x, y - 6 * gui.scale), t_version, colours.box_text_label, 313)
			y += 19 * gui.scale
			ddt.text((x, y), "Copyright © 2015-2024 Taiko2k captain.gxj@gmail.com", colours.box_sub_text, 13)

			y += 19 * gui.scale
			link_pa = draw_linked_text(
				(x, y), "https://tauonmusicbox.rocks", colours.box_sub_text, 12,
				replace="tauonmusicbox.rocks")
			link_rect = [x, y, link_pa[1], 18 * gui.scale]
			if coll(link_rect):
				if not self.click:
					gui.cursor_want = 3
				if self.click:
					webbrowser.open(link_pa[2], new=2, autoraise=True)

			fields.add(link_rect)

			y += 27 * gui.scale
			ddt.text((x, y), _("This program comes with absolutely no warranty."), colours.box_text_label, 12)
			y += 16 * gui.scale
			link_gpl = "https://www.gnu.org/licenses/gpl-3.0.html"
			link_pa = draw_linked_text(
				(x, y), _("See the {link} license for details.").format(link=link_gpl),
				colours.box_text_label, 12, replace="GNU GPLv3+")
			link_rect = [x + link_pa[0], y, link_pa[1], 18 * gui.scale]
			if coll(link_rect):
				if not self.click:
					gui.cursor_want = 3
				if self.click:
					webbrowser.open(link_pa[2], new=2, autoraise=True)
			fields.add(link_rect)

		elif self.cred_page == 1:

			y += 15 * gui.scale

			ddt.text((x, y + 1 * gui.scale), _("Created by"), colours.box_text_label, 13)
			ddt.text((x + 120 * gui.scale, y + 1 * gui.scale), "Taiko2k", colours.box_sub_text, 13)

			y += 40 * gui.scale
			link_pa = draw_linked_text(
				(x, y), "https://github.com/Taiko2k/Tauon/graphs/contributors",
				colours.box_sub_text, 12, replace=_("Contributors"))
			link_rect = [x, y, link_pa[1], 18 * gui.scale]
			if coll(link_rect):
				if not self.click:
					gui.cursor_want = 3
				if self.click:
					webbrowser.open(link_pa[2], new=2, autoraise=True)
			fields.add(link_rect)


		elif self.cred_page == 2:
			xx = x + round(160 * gui.scale)
			xxx = x + round(240 * gui.scale)
			ddt.text((x, y), _("Open source software used"), colours.box_text_label, 13)
			font = 12
			spacing = round(18 * gui.scale)
			y += spacing
			ddt.text((x, y), "Simple DirectMedia Layer", colours.box_sub_text, font)
			ddt.text((xx, y), "zlib", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://www.libsdl.org/", colours.box_sub_text, font, click=self.click, replace="libsdl.org")

			y += spacing
			ddt.text((x, y), "Cairo Graphics", colours.box_sub_text, font)
			ddt.text((xx, y), "MPL", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://www.cairographics.org/", colours.box_sub_text, font, click=self.click, replace="cairographics.org")

			y += spacing
			ddt.text((x, y), "Pango", colours.box_sub_text, font)
			ddt.text((xx, y), "LGPL", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://pango.gnome.org/", colours.box_sub_text, font, click=self.click, replace="pango.gnome.org")

			y += spacing
			ddt.text((x, y), "FFmpeg", colours.box_sub_text, font)
			ddt.text((xx, y), "GPL", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://ffmpeg.org/", colours.box_sub_text, font, click=self.click, replace="ffmpeg.org")

			y += spacing
			ddt.text((x, y), "Pillow", colours.box_sub_text, font)
			ddt.text((xx, y), "PIL License", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://python-pillow.org/", colours.box_sub_text, font, click=self.click, replace="python-pillow.org")


		elif self.cred_page == 4:
			xx = x + round(140 * gui.scale)
			xxx = x + round(240 * gui.scale)
			ddt.text((x, y), _("Open source software used (cont'd)"), colours.box_text_label, 13)
			font = 12
			spacing = round(18 * gui.scale)
			y += spacing
			ddt.text((x, y), "PySDL2", colours.box_sub_text, font)
			ddt.text((xx, y), _("Public Domain"), colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://github.com/marcusva/py-sdl2", colours.box_sub_text, font, click=self.click, replace="github")

			y += spacing
			ddt.text((x, y), "Tekore", colours.box_sub_text, font)
			ddt.text((xx, y), "MIT", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://github.com/felix-hilden/tekore", colours.box_sub_text, font, click=self.click, replace="github")

			y += spacing
			ddt.text((x, y), "pyLast", colours.box_sub_text, font)
			ddt.text((xx, y), "Apache 2.0", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://github.com/pylast/pylast", colours.box_sub_text, font, click=self.click, replace="github")

			y += spacing
			ddt.text((x, y), "Noto Sans font", colours.box_sub_text, font)
			ddt.text((xx, y), "Apache 2.0", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://fonts.google.com/specimen/Noto+Sans", colours.box_sub_text, font, click=self.click, replace="fonts.google.com")

			# y += spacing
			# ddt.text((x, y), "Stagger", colours.box_sub_text, font)
			# ddt.text((xx, y), "BSD 2-Clause", colours.box_text_label, font)
			# d"raw_linked_text2(xxx, y, "https://github.com/staggerpkg/stagger", colours.box_sub_text, font, click=self.click, replace="github")

			y += spacing
			ddt.text((x, y), "KISS FFT", colours.box_sub_text, font)
			ddt.text((xx, y), "New BSD License", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://github.com/mborgerding/kissfft", colours.box_sub_text, font, click=self.click, replace="github")

		elif self.cred_page == 3:
			xx = x + round(130 * gui.scale)
			xxx = x + round(240 * gui.scale)
			ddt.text((x, y), _("Open source software used (cont'd)"), colours.box_text_label, 13)
			font = 12
			spacing = round(18 * gui.scale)
			y += spacing
			ddt.text((x, y), "libFLAC", colours.box_sub_text, font)
			ddt.text((xx, y), "New BSD License", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://xiph.org/flac/", colours.box_sub_text, font, click=self.click, replace="xiph.org")

			y += spacing
			ddt.text((x, y), "libvorbis", colours.box_sub_text, font)
			ddt.text((xx, y), "BSD License", colours.box_text_label, font)
			draw_linked_text2(xxx, y, "https://xiph.org/vorbis/", colours.box_sub_text, font, click=self.click, replace="xiph.org")

			y += spacing
			ddt.text((x, y), "opusfile", colours.box_sub_text, font)
			ddt.text((xx, y), "New BSD license", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://opus-codec.org/", colours.box_sub_text, font, click=self.click, replace="opus-codec.org")

			y += spacing
			ddt.text((x, y), "mpg123", colours.box_sub_text, font)
			ddt.text((xx, y), "LGPL 2.1", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://www.mpg123.de/", colours.box_sub_text, font, click=self.click, replace="mpg123.de")

			y += spacing
			ddt.text((x, y), "Secret Rabbit Code", colours.box_sub_text, font)
			ddt.text((xx, y), "BSD 2-Clause", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "http://www.mega-nerd.com/SRC/index.html", colours.box_sub_text, font, click=self.click, replace="mega-nerd.com")

			y += spacing
			ddt.text((x, y), "libopenmpt", colours.box_sub_text, font)
			ddt.text((xx, y), "New BSD License", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://lib.openmpt.org/libopenmpt", colours.box_sub_text, font, click=self.click, replace="lib.openmpt.org")

		elif self.cred_page == 5:
			xx = x + round(130 * gui.scale)
			xxx = x + round(240 * gui.scale)
			ddt.text((x, y), _("Open source software used (cont'd)"), colours.box_text_label, 13)
			font = 12
			spacing = round(18 * gui.scale)
			y += spacing
			ddt.text((x, y), "Mutagen", colours.box_sub_text, font)
			ddt.text((xx, y), "GPLv2+", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://github.com/quodlibet/mutagen", colours.box_sub_text, font, click=self.click, replace="github")

			y += spacing
			ddt.text((x, y), "unidecode", colours.box_sub_text, font)
			ddt.text((xx, y), "GPL-2.0+", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://github.com/avian2/unidecode", colours.box_sub_text, font, click=self.click, replace="github")

			y += spacing
			ddt.text((x, y), "pypresence", colours.box_sub_text, font)
			ddt.text((xx, y), "MIT", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://github.com/qwertyquerty/pypresence", colours.box_sub_text, font, click=self.click, replace="github")

			y += spacing
			ddt.text((x, y), "musicbrainzngs", colours.box_sub_text, font)
			ddt.text((xx, y), "Simplified BSD", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://github.com/alastair/python-musicbrainzngs", colours.box_sub_text, font, click=self.click, replace="github")

			y += spacing
			ddt.text((x, y), "Send2Trash", colours.box_sub_text, font)
			ddt.text((xx, y), "New BSD License", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://github.com/arsenetar/send2trash", colours.box_sub_text, font, click=self.click, replace="github")

			y += spacing
			ddt.text((x, y), "GTK/PyGObject", colours.box_sub_text, font)
			ddt.text((xx, y), "LGPLv2.1+", colours.box_text_label, font)
			draw_linked_text2(
				xxx, y, "https://gitlab.gnome.org/GNOME/pygobject", colours.box_sub_text, font, click=self.click, replace="gitlab.gnome.org")

		ddt.rect((x, block_y, 369 * gui.scale, 140 * gui.scale), alpha_mod(colours.box_background, fade))

		y = y0 + h0 - round(33 * gui.scale)
		x = x0 + w0 - 0 * gui.scale

		w = max(ddt.get_text_w(_("Credits"), 211), ddt.get_text_w(_("Next"), 211))
		x -= w + round(40 * gui.scale)

		text = _("Credits")
		if self.cred_page != 0:
			text = _("Next")
		if self.button(x, y, text, width=w + round(25 * gui.scale)):
			self.ani_cred = 1
			self.ani_fade_on_timer.set()

	def topchart(self, x0, y0, w0, h0):

		x = x0 + round(25 * gui.scale)
		y = y0 + 20 * gui.scale

		ddt.text_background_colour = colours.box_background

		ddt.text((x, y), _("Chart Grid Generator"), colours.box_text, 214)

		y += 25 * gui.scale
		ww = ddt.text((x, y), _("Target playlist:   "), colours.box_sub_text, 312)
		ddt.text(
			(x + ww, y), pctl.multi_playlist[pctl.active_playlist_viewing].title, colours.box_text_label, 12,
			400 * gui.scale)
		# x -= 210 * gui.scale

		y += 30 * gui.scale

		if prefs.chart_cascade:
			if prefs.chart_d1:
				prefs.chart_c1 = self.slide_control(x, y, _("Level 1"), "", prefs.chart_c1, 2, 20, 1, width=35)
			y += 22 * gui.scale
			if prefs.chart_d2:
				prefs.chart_c2 = self.slide_control(x, y, _("Level 2"), "", prefs.chart_c2, 2, 20, 1, width=35)
			y += 22 * gui.scale
			if prefs.chart_d3:
				prefs.chart_c3 = self.slide_control(x, y, _("Level 3"), "", prefs.chart_c3, 2, 20, 1, width=35)

			y -= 44 * gui.scale
			x += 133 * gui.scale
			prefs.chart_d1 = self.slide_control(x, y, _("by"), "", prefs.chart_d1, 0, 10, 1, width=35)
			y += 22 * gui.scale
			prefs.chart_d2 = self.slide_control(x, y, _("by"), "", prefs.chart_d2, 0, 10, 1, width=35)
			y += 22 * gui.scale
			prefs.chart_d3 = self.slide_control(x, y, _("by"), "", prefs.chart_d3, 0, 10, 1, width=35)
			x -= 133 * gui.scale

		else:

			prefs.chart_rows = self.slide_control(x, y, _("Rows"), "", prefs.chart_rows, 1, 100, 1, width=35)
			y += 22 * gui.scale
			prefs.chart_columns = self.slide_control(x, y, _("Columns"), "", prefs.chart_columns, 1, 100, 1, width=35)
			y += 22 * gui.scale

		y += 35 * gui.scale
		x += 5 * gui.scale

		prefs.chart_cascade = self.toggle_square(x, y, prefs.chart_cascade, _("Cascade style"))
		y += 25 * gui.scale
		prefs.chart_tile = self.toggle_square(x, y, prefs.chart_tile ^ True, _("Use padding")) ^ True

		y -= 25 * gui.scale
		x += 170 * gui.scale

		prefs.chart_text = self.toggle_square(x, y, prefs.chart_text, _("Include album titles"))
		y += 25 * gui.scale
		prefs.topchart_sorts_played = self.toggle_square(x, y, prefs.topchart_sorts_played, _("Sort by top played"))

		x = x0 + 15 * gui.scale + 320 * gui.scale
		y = y0 + 100 * gui.scale

		# . Limited width. Max 13 chars
		if self.button(x, y, _("Randomise BG")):

			r = round(random.random() * 40)
			g = round(random.random() * 40)
			b = round(random.random() * 40)

			prefs.chart_bg = [r, g, b]

			d = random.randrange(0, 4)

			if d == 1:
				c = 5 + round(random.random() * 20)
				prefs.chart_bg = [c, c, c]

		x += 100 * gui.scale
		y -= 20 * gui.scale

		display_colour = (prefs.chart_bg[0], prefs.chart_bg[1], prefs.chart_bg[2], 255)

		rect = (x, y, 70 * gui.scale, 70 * gui.scale)
		ddt.rect(rect, display_colour)

		ddt.rect_s(rect, (50, 50, 50, 255), round(1 * gui.scale))

		# x = self.box_x + self.item_x_offset + 200 * gui.scale
		# y = self.box_y + 180 * gui.scale

		x = x0 + 260 * gui.scale
		y = y0 + 180 * gui.scale

		dex = reload_albums(quiet=True, return_playlist=pctl.active_playlist_viewing)

		x = x0 + round(110 * gui.scale)
		y = y0 + 240 * gui.scale

		# . Limited width. Max 9 chars
		if self.button(x, y, _("Generate"), width=80 * gui.scale):
			if gui.generating_chart:
				show_message(_("Be patient!"))
			elif not prefs.chart_font:
				show_message(_("No font set in config"), mode="error")
			else:
				shoot = threading.Thread(target=gen_chart)
				shoot.daemon = True
				shoot.start()
				gui.generating_chart = True

		x += round(95 * gui.scale)
		if gui.generating_chart:
			ddt.text((x, y + round(1 * gui.scale)), _("Generating..."), colours.box_text_label, 12)
		else:

			count = prefs.chart_rows * prefs.chart_columns
			if prefs.chart_cascade:
				count = prefs.chart_c1 * prefs.chart_d1 + prefs.chart_c2 * prefs.chart_d2 + prefs.chart_c3 * prefs.chart_d3

			line = _("{N} Album chart").format(N=str(count))

			ww = ddt.text((x, y + round(1 * gui.scale)), line, colours.box_text_label, 12)

			if len(dex) < count:
				ddt.text(
					(x + ww + round(10 * gui.scale), y + 1 * gui.scale), _("Not enough albums in the playlist!"),
					[255, 120, 125, 255], 12)

		x = x0 + round(20 * gui.scale)
		y = y0 + 240 * gui.scale

		# . Limited width. Max 8 chars
		if self.button(x, y, _("Return"), width=75 * gui.scale):
			self.chart_view = 0

	def stats(self, x0, y0, w0, h0):

		x = x0 + 10 * gui.scale
		y = y0

		if self.chart_view == 1:
			self.topchart(x0, y0, w0, h0)
			return

		ww = ddt.get_text_w(_("Chart generator..."), 211) + 30 * gui.scale
		if system == "Linux" and self.button(x0 + w0 - ww, y + 15 * gui.scale, _("Chart generator...")):
			self.chart_view = 1

		ddt.text_background_colour = colours.box_background
		lt_font = 312
		lt_colour = colours.box_text_label

		w1 = ddt.get_text_w(_("Tracks in playlist"), 12)
		w2 = ddt.get_text_w(_("Albums in playlist"), 12)
		w3 = ddt.get_text_w(_("Playlist duration"), 12)
		w4 = ddt.get_text_w(_("Tracks in database"), 12)
		w5 = ddt.get_text_w(_("Total albums"), 12)
		w6 = ddt.get_text_w(_("Total playtime"), 12)

		x1 = x + (8 + 10 + 10) * gui.scale
		x2 = x1 + max(w1, w2, w3, w4, w5, w6) + 20 * gui.scale
		y1 = y + 50 * gui.scale

		if self.stats_pl != pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int or self.stats_pl_timer.get() > 5:
			self.stats_pl = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int
			self.stats_pl_timer.set()

			album_names = set()
			folder_names = set()
			count = 0

			for track_id in default_playlist:
				tr = pctl.get_track(track_id)

				if not tr.album:
					if tr.parent_folder_path not in folder_names:
						count += 1
					folder_names.add(tr.parent_folder_path)
				else:
					if tr.parent_folder_path not in folder_names and tr.album not in album_names:
						count += 1
					folder_names.add(tr.parent_folder_path)
					album_names.add(tr.album)

			self.stats_pl_albums = count

			self.stats_pl_length = 0
			for item in default_playlist:
				self.stats_pl_length += pctl.master_library[item].length

		line = seconds_to_day_hms(self.stats_pl_length, strings.day, strings.days)

		ddt.text((x1, y1), _("Tracks in playlist"), lt_colour, lt_font)
		ddt.text((x2, y1), py_locale.format_string("%d", len(default_playlist), True), colours.box_sub_text, 12)
		y1 += 20 * gui.scale
		ddt.text((x1, y1), _("Albums in playlist"), lt_colour, lt_font)
		ddt.text((x2, y1), str(self.stats_pl_albums), colours.box_sub_text, 12)
		y1 += 20 * gui.scale
		ddt.text((x1, y1), _("Playlist duration"), lt_colour, lt_font)

		ddt.text((x2, y1), line, colours.box_sub_text, 12)

		if self.stats_timer.get() > 5:
			album_names = set()
			folder_names = set()
			count = 0

			for pl in pctl.multi_playlist:
				for track_id in pl.playlist_ids:
					tr = pctl.get_track(track_id)

					if not tr.album:
						if tr.parent_folder_path not in folder_names:
							count += 1
						folder_names.add(tr.parent_folder_path)
					else:
						if tr.parent_folder_path not in folder_names and tr.album not in album_names:
							count += 1
						folder_names.add(tr.parent_folder_path)
						album_names.add(tr.album)

			self.total_albums = count

			self.stats_timer.set()

		y1 += 40 * gui.scale
		ddt.text((x1, y1), _("Tracks in database"), lt_colour, lt_font)
		ddt.text((x2, y1), py_locale.format_string("%d", len(pctl.master_library), True), colours.box_sub_text, 12)
		y1 += 20 * gui.scale
		ddt.text((x1, y1), _("Total albums"), lt_colour, lt_font)
		ddt.text((x2, y1), str(self.total_albums), colours.box_sub_text, 12)

		y1 += 20 * gui.scale
		ddt.text((x1, y1), _("Total playtime"), lt_colour, lt_font)
		ddt.text((x2, y1), seconds_to_day_hms(pctl.total_playtime, strings.day, strings.days), colours.box_sub_text, 15)

		# Ratio bar
		if len(pctl.master_library) > 115 * gui.scale:
			x = x0
			y = y0 + h0 - 7 * gui.scale

			full_rect = [x, y, w0, 7 * gui.scale]
			d = 0

			# Stats
			try:
				if self.last_db_size != len(pctl.master_library):
					self.last_db_size = len(pctl.master_library)
					self.ext_ratio = {}
					for key, value in pctl.master_library.items():
						if value.file_ext in self.ext_ratio:
							self.ext_ratio[value.file_ext] += 1
						else:
							self.ext_ratio[value.file_ext] = 1

				for key, value in self.ext_ratio.items():

					colour = [200, 200, 200, 255]
					if key in format_colours:
						colour = format_colours[key]

					colour = colorsys.rgb_to_hls(colour[0] / 255, colour[1] / 255, colour[2] / 255)
					colour = colorsys.hls_to_rgb(1 - colour[0], colour[1] * 0.8, colour[2] * 0.8)
					colour = [int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255), 255]

					h = int(round(value / len(pctl.master_library) * full_rect[2]))
					block_rect = [full_rect[0] + d, full_rect[1], h, full_rect[3]]

					ddt.rect(block_rect, colour)
					d += h

					block_rect = (block_rect[0], block_rect[1], block_rect[2] - 1, block_rect[3])
					fields.add(block_rect)
					if coll(block_rect):
						xx = block_rect[0] + int(block_rect[2] / 2)
						xx = max(xx, x + 30 * gui.scale)
						xx = min(xx, x0 + w0 - 30 * gui.scale)
						ddt.text((xx, y0 + h0 - 35 * gui.scale, 2), key, colours.grey_blend_bg(220), 13)

						if self.click:
							gen_codec_pl(key)
			except Exception:
				logging.exception("Error draw ext bar")

	def config_v(self, x0, y0, w0, h0):

		ddt.text_background_colour = colours.box_background

		x = x0 + self.item_x_offset
		y = y0 + 17 * gui.scale

		self.toggle_square(x, y, rating_toggle, _("Track ratings"))
		y += round(25 * gui.scale)
		self.toggle_square(x, y, album_rating_toggle, _("Album ratings"))
		y += round(35 * gui.scale)

		self.toggle_square(x, y, heart_toggle, "     ")
		heart_row_icon.render(x + round(23 * gui.scale), y + round(2 * gui.scale), colours.box_text)
		rect = (x, y + round(2 * gui.scale), 40 * gui.scale, 15 * gui.scale)
		fields.add(rect)
		if coll(rect):
			ex_tool_tip(x + round(45 * gui.scale), y - 20 * gui.scale, 0, _("Show track loves"), 12)

		x += (55 * gui.scale)
		self.toggle_square(x, y, star_toggle, "     ")
		star_row_icon.render(x + round(22 * gui.scale), y + round(0 * gui.scale), colours.box_text)
		rect = (x, y + round(2 * gui.scale), 40 * gui.scale, 15 * gui.scale)
		fields.add(rect)
		if coll(rect):
			ex_tool_tip(x + round(35 * gui.scale), y - 20 * gui.scale, 0, _("Represent playtime as stars"), 12)

		x += (55 * gui.scale)
		self.toggle_square(x, y, star_line_toggle, "     ")
		ddt.rect(
			(x + round(21 * gui.scale), y + round(6 * gui.scale), round(15 * gui.scale), round(1 * gui.scale)),
			colours.box_text)
		rect = (x, y + round(2 * gui.scale), 40 * gui.scale, 15 * gui.scale)
		fields.add(rect)
		if coll(rect):
			ex_tool_tip(x + round(35 * gui.scale), y - 20 * gui.scale, 0, _("Represent playcount as lines"), 12)

		x = x0 + self.item_x_offset

		# y += round(25 * gui.scale)

		# self.toggle_square(x, y, star_line_toggle, _('Show playtime lines'))
		y += round(15 * gui.scale)

		# if gui.show_ratings:
		#     x += round(10 * gui.scale)
		# #self.toggle_square(x, y, star_toggle, _('Show playtime stars'))
		# if gui.show_ratings:
		#     x -= round(10 * gui.scale)


		y += round(25 * gui.scale)

		if self.toggle_square(x, y, prefs.row_title_format == 2, _("Left align title style")):
			prefs.row_title_format = 2
		else:
			prefs.row_title_format = 1

		y += round(25 * gui.scale)

		prefs.row_title_genre = self.toggle_square(x + round(10 * gui.scale), y, prefs.row_title_genre, _("Show album genre"))
		y += round(25 * gui.scale)

		self.toggle_square(x, y, toggle_append_date, _("Show album release year"))
		y += round(25 * gui.scale)

		self.toggle_square(x, y, toggle_append_total_time, _("Show album duration"))
		y += round(35 * gui.scale)

		if self.toggle_square(x, y, prefs.row_title_separator_type == 0, " - "):
			prefs.row_title_separator_type = 0
		if self.toggle_square(x + round(55 * gui.scale), y,  prefs.row_title_separator_type == 1, " ‒ "):
			prefs.row_title_separator_type = 1
		if self.toggle_square(x + round(110 * gui.scale), y,  prefs.row_title_separator_type == 2, " ⦁ "):
			prefs.row_title_separator_type = 2
		x = x0 + 330 * gui.scale
		y = y0 + 25 * gui.scale

		prefs.playlist_font_size = self.slide_control(x, y, _("Font Size"), "", prefs.playlist_font_size, 12, 17)
		y += 25 * gui.scale
		prefs.playlist_row_height = self.slide_control(x, y, _("Row Size"), "px", prefs.playlist_row_height, 15, 45)
		y += 25 * gui.scale
		prefs.tracklist_y_text_offset = self.slide_control(
			x, y, _("Baseline offset"), "px", prefs.tracklist_y_text_offset, -10, 10)
		y += 25 * gui.scale

		x += 65 * gui.scale
		self.button(x, y, _("Thin default"), self.small_preset, 124 * gui.scale)
		y += 27 * gui.scale
		self.button(x, y, _("Thick default"), self.large_preset, 124 * gui.scale)


	def set_playlist_cycle(self, mode=0):
		if mode == 1:
			return True if prefs.end_setting == "cycle" else False
		prefs.end_setting = "cycle"
		# global pl_follow
		# pl_follow = False

	def set_playlist_advance(self, mode=0):
		if mode == 1:
			return True if prefs.end_setting == "advance" else False
		prefs.end_setting = "advance"
		# global pl_follow
		# pl_follow = False

	def set_playlist_stop(self, mode=0):
		if mode == 1:
			return True if prefs.end_setting == "stop" else False
		prefs.end_setting = "stop"

	def set_playlist_repeat(self, mode=0):
		if mode == 1:
			return True if prefs.end_setting == "repeat" else False
		prefs.end_setting = "repeat"

	def small_preset(self):

		prefs.playlist_row_height = round(22 * prefs.ui_scale)
		prefs.playlist_font_size = 15
		prefs.tracklist_y_text_offset = 0
		gui.update_layout()

	def large_preset(self):

		prefs.playlist_row_height = round(27 * prefs.ui_scale)
		prefs.playlist_font_size = 15
		gui.update_layout()

	def slide_control(self, x, y, label, units, value, lower_limit, upper_limit, step=1, callback=None, width=58):

		width = round(width * gui.scale)

		if label is not None:
			ddt.text((x + 55 * gui.scale, y, 1), label, colours.box_text, 312)
			x += 65 * gui.scale
		y += 1 * gui.scale
		rect = (x, y, 33 * gui.scale, 15 * gui.scale)
		fields.add(rect)
		ddt.rect(rect, colours.box_button_background)
		abg = [255, 255, 255, 40]
		if coll(rect):

			if self.click:
				if value > lower_limit:
					value -= step
					gui.update_layout()
					if callback is not None:
						callback(value)

			if mouse_down:
				abg = [230, 120, 20, 255]
			else:
				abg = [220, 150, 20, 255]

		if colour_value(colours.box_background) > 300:
			abg = colours.box_sub_text

		dec_arrow.render(x + 1 * gui.scale, y, abg)

		x += 33 * gui.scale

		ddt.rect((x, y, width, 15 * gui.scale), alpha_mod(colours.box_button_background, 120))
		ddt.text((x + width / 2, y, 2), str(value) + units, colours.box_sub_text, 312)

		x += width

		rect = (x, y, 33 * gui.scale, 15 * gui.scale)
		fields.add(rect)
		ddt.rect(rect, colours.box_button_background)
		abg = [255, 255, 255, 40]
		if coll(rect):

			if self.click:
				if value < upper_limit:
					value += step
					gui.update_layout()
					if callback is not None:
						callback(value)
			if mouse_down:
				abg = [230, 120, 20, 255]
			else:
				abg = [220, 150, 20, 255]

		if colour_value(colours.box_background) > 300:
			abg = colours.box_sub_text

		inc_arrow.render(x + 1 * gui.scale, y, abg)

		return value

	# def style_up(self):
	#     prefs.line_style += 1
	#     if prefs.line_style > 5:
	#         prefs.line_style = 1

	def inside(self):

		return coll((self.box_x, self.box_y, self.w, self.h))

	def init2(self):

		self.init2done = True

	def close(self):
		self.enabled = False
		fader.fall()
		if gui.opened_config_file:
			reload_config_file()

	def render(self):

		if self.init2done is False:
			self.init2()

		if key_esc_press:
			self.close()

		tab_width = 115 * gui.scale

		side_width = 115 * gui.scale
		header_width = 0

		top_mode = False
		if window_size[0] < 700 * gui.scale:
			top_mode = True
			side_width = 0 * gui.scale
			header_width = round(48 * gui.scale)  # 48

		content_width = round(545 * gui.scale)
		content_height = round(275 * gui.scale)  # 275
		full_width = content_width
		full_height = content_height

		full_width += side_width
		full_height += header_width

		x = int(window_size[0] / 2) - int(full_width / 2)
		y = int(window_size[1] / 2) - int(full_height / 2)

		self.box_x = x
		self.box_y = y
		self.w = full_width
		self.h = full_height

		border_colour = colours.box_border

		ddt.rect(
			(x - 5 * gui.scale, y - 5 * gui.scale, full_width + 10 * gui.scale, full_height + 10 * gui.scale), border_colour)
		ddt.rect_a((x, y), (full_width, full_height), colours.box_background)

		current_tab = 0
		tab_height = round(24 * gui.scale)  # 30

		tab_bg = colours.sys_tab_bg
		tab_hl = colours.sys_tab_hl
		tab_text = rgb_add_hls(tab_bg, 0, 0.3, -0.15)
		if is_light(tab_bg):
			h, l, s = rgb_to_hls(tab_bg[0], tab_bg[1], tab_bg[2])
			l = 0.1
			tab_text = hls_to_rgb(h, l, s)
		tab_over = alpha_mod(rgb_add_hls(tab_bg, 0, 0.5, 0), 13)

		if top_mode:

			xx = x
			yy = y
			tab_width = 90 * gui.scale

			ddt.rect_a((x, y), (full_width, header_width), tab_bg)

			for item in self.tabs:

				if self.click and gui.message_box:
					gui.message_box = False

				box = [xx, yy, tab_width, tab_height]
				box2 = [xx, yy, tab_width, tab_height - 1]
				fields.add(box2)

				if self.click and coll(box2):
					self.tab_active = current_tab
					self.lyrics_panel = False

				if current_tab == self.tab_active:
					colour = copy.deepcopy(colours.sys_tab_hl)
					ddt.text_background_colour = colour
					ddt.rect(box, colour)
				else:
					ddt.text_background_colour = tab_bg
					ddt.rect(box, tab_bg)

				if coll(box2):
					ddt.rect(box, tab_over)

				alpha = 100
				if current_tab == self.tab_active:
					alpha = 240

				ddt.text((xx + (tab_width // 2), yy + 4 * gui.scale, 2), item[0], tab_text, 212)

				current_tab += 1
				xx += tab_width
				if current_tab == 6:
					yy += round(24 * gui.scale)  # 30
					xx = x

		else:

			ddt.rect_a((x, y), (tab_width, full_height), tab_bg)

			for item in self.tabs:

				if self.click and gui.message_box:
					if not coll(message_box.get_rect()):
						gui.message_box = False
					else:
						inp.mouse_click = True
						self.click = False

				box = [x, y + (current_tab * tab_height), tab_width, tab_height]
				box2 = [x, y + (current_tab * tab_height), tab_width, tab_height - 1]
				fields.add(box2)

				if self.click and coll(box2):
					self.tab_active = current_tab
					self.lyrics_panel = False

				if current_tab == self.tab_active:
					bg_colour = copy.deepcopy(colours.sys_tab_hl)
					ddt.text_background_colour = bg_colour
					ddt.rect(box, bg_colour)
				else:
					ddt.text_background_colour = tab_bg
					ddt.rect(box, tab_bg)

				if coll(box2):
					ddt.rect(box, tab_over)

				yy = box[1] + 4 * gui.scale

				if current_tab == self.tab_active:
					ddt.text(
						(box[0] + (tab_width // 2), yy, 2), item[0], alpha_blend(colours.tab_text_active, ddt.text_background_colour), 213)
				else:
					ddt.text(
						(box[0] + (tab_width // 2), yy, 2), item[0], tab_text, 213)

				current_tab += 1

		# ddt.line(x + 110, self.box_y + 1, self.box_x + 110, self.box_y + self.h, colours.grey(50))

		self.tabs[self.tab_active][1](x + side_width, y + header_width, content_width, content_height)

		self.click = False
		self.right_click = False

		ddt.text_background_colour = colours.box_background

class Fields:
	def __init__(self):

		self.id = []
		self.last_id = []

		self.field_array = []
		self.force = False

	def add(self, rect, callback=None):

		self.field_array.append((rect, callback))

	def test(self):

		if self.force:
			self.force = False
			return True

		self.last_id = self.id
		#logging.info(len(self.id))
		self.id = []

		for f in self.field_array:
			if coll(f[0]):
				self.id.append(1)  # += "1"
				if f[1] is not None:  # Call callback if present
					f[1]()
			else:
				self.id.append(0)  # += "0"

		if self.last_id == self.id:
			return False

		return True

	def clear(self):

		self.field_array = []

class TopPanel:
	def __init__(self):

		self.height = gui.panelY
		self.ty = 0

		self.start_space_left = round(46 * gui.scale)
		self.start_space_compact_left = 46 * gui.scale

		self.tab_text_font = fonts.tabs
		self.tab_extra_width = round(17 * gui.scale)
		self.tab_text_start_space = 8 * gui.scale
		self.tab_text_y_offset = 7 * gui.scale
		self.tab_spacing = 0

		self.ini_menu_space = 17 * gui.scale  # 17
		self.menu_space = 17 * gui.scale
		self.click_buffer = 4 * gui.scale

		self.tabs_right_x = 0  # computed for drag and drop code elsewhere (hacky)
		self.tabs_left_x = 1

		self.prime_tab = gui.saved_prime_tab
		self.prime_side = gui.saved_prime_direction  # 0=left, 1=right
		self.shown_tabs = []

		# ---
		self.space_left = 0
		self.tab_text_spaces = []
		self.index_playing = -1
		self.drag_zone_start_x = 300 * gui.scale

		self.exit_button = asset_loader(scaled_asset_directory, loaded_asset_dc, "ex.png", True)
		self.maximize_button = asset_loader(scaled_asset_directory, loaded_asset_dc, "max.png", True)
		self.restore_button = asset_loader(scaled_asset_directory, loaded_asset_dc, "restore.png", True)
		self.restore_button = asset_loader(scaled_asset_directory, loaded_asset_dc, "restore.png", True)
		self.playlist_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "playlist.png", True)
		self.return_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "return.png", True)
		self.artist_list_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "artist-list.png", True)
		self.folder_list_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "folder-list.png", True)
		self.dl_button = asset_loader(scaled_asset_directory, loaded_asset_dc, "dl.png", True)
		self.overflow_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "overflow.png", True)

		self.drag_slide_timer = Timer(100)
		self.tab_d_click_timer = Timer(10)
		self.tab_d_click_ref = None

		self.adds = []

	def left_overflow_switch_playlist(self, pl):
		self.prime_side = 0
		self.prime_tab = pl
		switch_playlist(pl)

	def right_overflow_switch_playlist(self, pl):
		self.prime_side = 1
		self.prime_tab = pl
		switch_playlist(pl)

	def render(self):

		# C-TD
		global quick_drag
		global update_layout

		hh = gui.panelY2
		yy = gui.panelY - hh
		self.height = hh

		if quick_drag is True:
			# gui.pl_update = 1
			gui.update_on_drag = True

		# Draw the background
		ddt.rect((0, 0, window_size[0], gui.panelY), colours.top_panel_background)

		if prefs.shuffle_lock and not gui.compact_bar:
			colour = [250, 250, 250, 255]
			if colours.lm:
				colour = [10, 10, 10, 255]
			text = _("Tauon Music Box SHUFFLE!")
			if prefs.album_shuffle_lock_mode:
				text = _("Tauon Music Box ALBUM SHUFFLE!")
			ddt.text((window_size[0] // 2, 8 * gui.scale, 2), text, colour, 212, bg=colours.top_panel_background)
		if gui.top_bar_mode2:
			tr = pctl.playing_object()
			if tr:
				album_art_gen.display(tr, (window_size[0] - gui.panelY - 1, 0), (gui.panelY, gui.panelY))
				if loading_in_progress or \
						to_scan or \
						cm_clean_db or \
						lastfm.scanning_friends or \
						after_scan or \
						move_in_progress or \
						plex.scanning or \
						transcode_list or tauon.spot_ctl.launching_spotify or tauon.spot_ctl.spotify_com or subsonic.scanning or \
						koel.scanning or gui.sync_progress or lastfm.scanning_scrobbles:
					ddt.rect(
						(window_size[0] - (gui.panelY + 20), gui.panelY - gui.panelY2, gui.panelY + 25, gui.panelY2),
						colours.top_panel_background)

				maxx = window_size[0] - (gui.panelY + 30 * gui.scale)
				title_colour = colours.grey(249)
				if colours.lm:
					title_colour = colours.grey(30)
				title = tr.title
				if not title:
					title = tr.filename
				artist = tr.artist

				if pctl.playing_state == 3 and not radiobox.dummy_track.title:
					title = pctl.tag_meta
					artist = radiobox.loaded_url  # pctl.url

				ddt.text_background_colour = colours.top_panel_background

				ddt.text((round(14 * gui.scale), round(15 * gui.scale)), title, title_colour, 215, max_w=maxx)
				ddt.text((round(14 * gui.scale), round(40 * gui.scale)), artist, colours.grey(120), 315, max_w=maxx)

		wwx = 0
		if prefs.left_window_control and not gui.compact_bar:
			if gui.macstyle:
				wwx = 24
				# wwx = round(64 * gui.scale)
				if draw_min_button:
					wwx += 20
				if draw_max_button:
					wwx += 20
				wwx = round(wwx * gui.scale)
			else:
				wwx = 26
				# wwx = round(90 * gui.scale)
				if draw_min_button:
					wwx += 35
				if draw_max_button:
					wwx += 33
				wwx = round(wwx * gui.scale)

		rect = (wwx + 9 * gui.scale, yy + 4 * gui.scale, 34 * gui.scale, 25 * gui.scale)
		fields.add(rect)

		if coll(rect) and not prefs.shuffle_lock:
			if inp.mouse_click:

				if gui.combo_mode:
					gui.switch_showcase_off = True
				else:
					gui.lsp ^= True

				update_layout = True
				gui.update += 1
			if mouse_down and quick_drag:
				gui.lsp = True
				update_layout = True
				gui.update += 1

			if middle_click:
				toggle_left_last()
				update_layout = True
				gui.update += 1

			if right_click:
				# prefs.artist_list ^= True
				lsp_menu.activate(position=(5 * gui.scale, gui.panelY))
				update_layout_do()

		colour = colours.corner_button  # [230, 230, 230, 255]

		if gui.lsp:
			colour = colours.corner_button_active
		if gui.combo_mode:
			colour = colours.corner_button
			if coll(rect):
				colour = colours.corner_button_active

		if not prefs.shuffle_lock:
			if gui.combo_mode:
				self.return_icon.render(wwx + 14 * gui.scale, yy + 8 * gui.scale, colour)
			elif prefs.left_panel_mode == "artist list":
				self.artist_list_icon.render(wwx + 13 * gui.scale, yy + 8 * gui.scale, colour)
			elif prefs.left_panel_mode == "folder view":
				self.folder_list_icon.render(wwx + 14 * gui.scale, yy + 8 * gui.scale, colour)
			else:
				self.playlist_icon.render(wwx + 13 * gui.scale, yy + 8 * gui.scale, colour)

		# if prefs.artist_list:
		#     self.artist_list_icon.render(13 * gui.scale, yy + 8 * gui.scale, colour)
		# else:
		#     self.playlist_icon.render(13 * gui.scale, yy + 8 * gui.scale, colour)

		if playlist_box.drag:
			drag_mode = False

		# Need to test length
		self.tab_text_spaces = []

		if gui.radio_view:
			for item in pctl.radio_playlists:
				le = ddt.get_text_w(item["name"], self.tab_text_font)
				self.tab_text_spaces.append(le)
		else:
			for i, item in enumerate(pctl.multi_playlist):
				le = ddt.get_text_w(pctl.multi_playlist[i].title, self.tab_text_font)
				self.tab_text_spaces.append(le)

		x = self.start_space_left + wwx
		y = yy  # self.ty

		# Calculate position for playing text and text
		offset = 15 * gui.scale
		if draw_border and not prefs.left_window_control:
			offset += 61 * gui.scale
			if draw_max_button:
				offset += 61 * gui.scale
		if gui.turbo:
			offset += 90 * gui.scale
			if gui.vis == 3:
				offset += 57 * gui.scale
		if gui.top_bar_mode2:
			offset = 0

		p_text_len = 180 * gui.scale
		right_space_es = p_text_len + offset

		x_start = x

		if playlist_box.drag and not gui.radio_view:
			if mouse_up:
				if mouse_up_position[0] > (gui.lspw if gui.lsp else 0) and mouse_up_position[1] > gui.panelY:
					playlist_box.drag = False
					if prefs.drag_to_unpin:
						if playlist_box.drag_source == 0:
							pctl.multi_playlist[playlist_box.drag_on].hidden = True
						else:
							pctl.multi_playlist[playlist_box.drag_on].hidden = False
					gui.update += 1
			gui.update_on_drag = True

		# List all tabs eligible to be shown
		#logging.info("-------------")
		ready_tabs = []
		show_tabs = []

		if prefs.tabs_on_top or gui.radio_view:
			if gui.radio_view:
				for i, tab in enumerate(pctl.radio_playlists):
					ready_tabs.append(i)
				self.prime_tab = min(self.prime_tab, len(pctl.radio_playlists) - 1)
			else:
				for i, tab in enumerate(pctl.multi_playlist):
					# Skip if hide flag is set
					if tab.hidden:
						continue
					ready_tabs.append(i)
				self.prime_tab = min(self.prime_tab, len(pctl.multi_playlist) - 1)
			max_w = window_size[0] - (x + right_space_es + round(34 * gui.scale))

			left_tabs = []
			right_tabs = []
			if prefs.shuffle_lock:
				for p in ready_tabs:
					left_tabs.append(p)

			else:
				for p in ready_tabs:
					if p < self.prime_tab:
						left_tabs.append(p)

				for p in ready_tabs:
					if p > self.prime_tab:
						right_tabs.append(p)
				left_tabs.reverse()

			run = max_w

			if self.prime_tab in ready_tabs:
				size = self.tab_text_spaces[self.prime_tab] + self.tab_extra_width
				if size < run:
					show_tabs.append(self.prime_tab)
					run -= size

			if self.prime_side == 0:
				for tab in right_tabs:
					size = self.tab_text_spaces[tab] + self.tab_extra_width
					if size < run:
						show_tabs.append(tab)
						run -= size
					else:
						break
				for tab in left_tabs:
					size = self.tab_text_spaces[tab] + self.tab_extra_width
					if size < run:
						show_tabs.insert(0, tab)
						run -= size
					else:
						break
			else:
				for tab in left_tabs:
					size = self.tab_text_spaces[tab] + self.tab_extra_width
					if size < run:
						show_tabs.insert(0, tab)
						run -= size
					else:
						break
				for tab in right_tabs:
					size = self.tab_text_spaces[tab] + self.tab_extra_width
					if size < run:
						show_tabs.append(tab)
						run -= size
					else:
						break

			# for tab in show_tabs:
			#     logging.info(pctl.multi_playlist[tab].title)
			#logging.info("---")
			left_overflow = [x for x in left_tabs if x not in show_tabs]
			right_overflow = [x for x in right_tabs if x not in show_tabs]
			self.shown_tabs = show_tabs

			if left_overflow:
				hh = round(20 * gui.scale)
				rect = [x, y + (self.height - hh), 17 * gui.scale, hh]
				ddt.rect(rect, colours.tab_background)
				self.overflow_icon.render(rect[0] + round(3 * gui.scale), rect[1] + round(4 * gui.scale), colours.tab_text)

				x += 17 * gui.scale
				x_start = x

				if inp.mouse_click and coll(rect):
					overflow_menu.items.clear()
					for tab in reversed(left_overflow):
						if gui.radio_view:
							overflow_menu.add(
								MenuItem(pctl.radio_playlists[tab]["name"], self.left_overflow_switch_playlist,
								pass_ref=True, set_ref=tab))
						else:
							overflow_menu.add(
								MenuItem(pctl.multi_playlist[tab].title, self.left_overflow_switch_playlist,
								pass_ref=True, set_ref=tab))
					overflow_menu.activate(0, (rect[0], rect[1] + rect[3]))

			xx = x + (max_w - run)  # + round(6 * gui.scale)
			self.tabs_left_x = x_start

			if right_overflow:
				hh = round(20 * gui.scale)
				rect = [xx, y + (self.height - hh), 17 * gui.scale, hh]
				ddt.rect(rect, colours.tab_background)
				self.overflow_icon.render(
					rect[0] + round(3 * gui.scale), rect[1] + round(4 * gui.scale),
					colours.tab_text)
				if inp.mouse_click and coll(rect):
					overflow_menu.items.clear()
					for tab in right_overflow:
						if gui.radio_view:
							overflow_menu.add(
								MenuItem(
									pctl.radio_playlists[tab]["name"], self.left_overflow_switch_playlist, pass_ref=True, set_ref=tab))
						else:
							overflow_menu.add(
								MenuItem(
									pctl.multi_playlist[tab].title, self.left_overflow_switch_playlist, pass_ref=True, set_ref=tab))
					overflow_menu.activate(0, (rect[0], rect[1] + rect[3]))

			if gui.radio_view:
				if not mouse_down and pctl.radio_playlist_viewing not in show_tabs and pctl.radio_playlist_viewing in ready_tabs:
					if pctl.radio_playlist_viewing < self.prime_tab:
						self.prime_side = 0
					elif pctl.radio_playlist_viewing > self.prime_tab:
						self.prime_side = 1
					self.prime_tab = pctl.radio_playlist_viewing
					gui.update += 1
			elif not mouse_down and pctl.active_playlist_viewing not in show_tabs and pctl.active_playlist_viewing in ready_tabs:
				if pctl.active_playlist_viewing < self.prime_tab:
					self.prime_side = 0
				elif pctl.active_playlist_viewing > self.prime_tab:
					self.prime_side = 1
				self.prime_tab = pctl.active_playlist_viewing
				gui.update += 1

			if playlist_box.drag and mouse_position[0] > xx and mouse_position[1] < gui.panelY:
				gui.update += 1
				if 0.5 < self.drag_slide_timer.get() < 1 and show_tabs and right_overflow:
					self.drag_slide_timer.set()
					self.prime_side = 1
					self.prime_tab = right_overflow[0]
				if self.drag_slide_timer.get() > 1:
					self.drag_slide_timer.set()
			if playlist_box.drag and mouse_position[0] < x and mouse_position[1] < gui.panelY:
				gui.update += 1
				if 0.5 < self.drag_slide_timer.get() < 1 and show_tabs and left_overflow:
					self.drag_slide_timer.set()
					self.prime_side = 0
					self.prime_tab = left_overflow[0]
				if self.drag_slide_timer.get() > 1:
					self.drag_slide_timer.set()

		# TAB INPUT PROCESSING
		target = pctl.multi_playlist
		if gui.radio_view:
			target = pctl.radio_playlists
		for i, tab in enumerate(target):

			if not gui.radio_view:
				if not prefs.tabs_on_top or prefs.shuffle_lock:
					break

				if len(pctl.multi_playlist) != len(self.tab_text_spaces):
					break

			if i not in show_tabs:
				continue

			# Determine the tab width
			tab_width = self.tab_text_spaces[i] + self.tab_extra_width

			# Save the far right boundary of the tabs (hacky)
			self.tabs_right_x = x + tab_width

			# Detect mouse over and add tab to mouse over detection
			f_rect = [x, y + 1, tab_width - 1, self.height - 1]
			tab_hit = coll(f_rect)

			# Tab functions
			if tab_hit:
				if not gui.radio_view:
					# Double click to play
					if mouse_up and pl_to_id(i) == self.tab_d_click_ref == pl_to_id(pctl.active_playlist_viewing) and \
							self.tab_d_click_timer.get() < 0.25 and point_distance(
								last_click_location, mouse_up_position) < 5 * gui.scale:

						if pctl.playing_state == 2 and pctl.active_playlist_playing == i:
							pctl.play()
						elif pctl.selected_ready() and (pctl.playing_state != 1 or pctl.active_playlist_playing != i):
							pctl.jump(default_playlist[pctl.selected_in_playlist], pl_position=pctl.selected_in_playlist)
					if mouse_up:
						self.tab_d_click_timer.set()
						self.tab_d_click_ref = pl_to_id(i)

				# Click to change playlist
				if inp.mouse_click:
					gui.pl_update = 1
					playlist_box.drag = True
					playlist_box.drag_source = 0
					playlist_box.drag_on = i
					if gui.radio_view:
						pctl.radio_playlist_viewing = i
					else:
						switch_playlist(i)
					set_drag_source()

				# Drag to move playlist
				if mouse_up and playlist_box.drag and coll_point(mouse_up_position, f_rect):

					if gui.radio_view:
						move_radio_playlist(playlist_box.drag_on, i)
					else:
						if playlist_box.drag_source == 1:
							pctl.multi_playlist[playlist_box.drag_on].hidden = False

						if i != playlist_box.drag_on:

							# # Reveal the tab in case it has been hidden
							# pctl.multi_playlist[playlist_box.drag_on].hidden = False

							if key_shift_down:
								pctl.multi_playlist[i].playlist_ids += pctl.multi_playlist[playlist_box.drag_on].playlist_ids
								delete_playlist(playlist_box.drag_on, check_lock=True, force=True)
							else:
								move_playlist(playlist_box.drag_on, i)

					playlist_box.drag = False
					gui.update += 1

				# Delete playlist on wheel click
				elif tab_menu.active is False and middle_click:
					# delete_playlist(i)
					delete_playlist_ask(i)
					break

				# Activate menu on right click
				elif right_click:
					if gui.radio_view:
						radio_tab_menu.activate(copy.deepcopy(i))
					else:
						tab_menu.activate(copy.deepcopy(i))
					gui.tab_menu_pl = i

				# Quick drop tracks
				elif quick_drag is True and mouse_up:
					self.tab_d_click_ref = -1
					self.tab_d_click_timer.force_set(100)
					if (pctl.gen_codes.get(pl_to_id(i)) and "self" not in pctl.gen_codes[pl_to_id(i)]):
						clear_gen_ask(pl_to_id(i))
					quick_drag = False
					modified = False
					gui.pl_update += 1

					for item in shift_selection:
						pctl.multi_playlist[i].playlist_ids.append(default_playlist[item])
						modified = True
					if len(shift_selection) > 0:
						modified = True
						self.adds.append(
							[pctl.multi_playlist[i].uuid_int, len(shift_selection), Timer()])  # ID, num, timer

					if modified:
						pctl.after_import_flag = True
						pctl.notify_change()
						pctl.update_shuffle_pool(pctl.multi_playlist[i].uuid_int)
						tree_view_box.clear_target_pl(i)
						tauon.thread_manager.ready("worker")

				if mouse_up and radio_view.drag:
					pctl.radio_playlists[i]["items"].append(radio_view.drag)
					toast(_("Added station to: ") + pctl.radio_playlists[i]["name"])

					radio_view.drag = None

			x += tab_width + self.tab_spacing

		# Test dupelicate tab function
		if playlist_box.drag:
			rect = (0, x, self.height, window_size[0])
			fields.add(rect)

		if mouse_up and playlist_box.drag and mouse_position[0] > x and mouse_position[1] < self.height:
			if gui.radio_view:
				pass
			elif key_ctrl_down:
				gen_dupe(playlist_box.drag_on)

			else:
				if playlist_box.drag_source == 1:
					pctl.multi_playlist[playlist_box.drag_on].hidden = False

				move_playlist(playlist_box.drag_on, i)
			playlist_box.drag = False

		# Need to test length again
		# Need to test length
		self.tab_text_spaces = []

		if gui.radio_view:
			for item in pctl.radio_playlists:
				le = ddt.get_text_w(item["name"], self.tab_text_font)
				self.tab_text_spaces.append(le)
		else:
			for i, item in enumerate(pctl.multi_playlist):
				le = ddt.get_text_w(pctl.multi_playlist[i].title, self.tab_text_font)
				self.tab_text_spaces.append(le)

		# Reset X draw position
		x = x_start
		bar_highlight_size = round(2 * gui.scale)

		# TAB DRAWING
		shown = []
		for i, tab in enumerate(target):

			if not gui.radio_view:
				if not prefs.tabs_on_top or prefs.shuffle_lock:
					break

				if len(pctl.multi_playlist) != len(self.tab_text_spaces):
					break

			# if tab.hidden is True:
			#     continue

			if i not in show_tabs:
				continue

			# if window_size[0] - x - (self.tab_text_spaces[i] + self.tab_extra_width) < right_space_es:
			#     break

			shown.append(i)

			tab_width = self.tab_text_spaces[i] + self.tab_extra_width
			rect = [x, y, tab_width, self.height]

			# Detect mouse over and add tab to mouse over detection
			f_rect = [x, y + 1, tab_width - 1, self.height - 1]
			fields.add(f_rect)
			tab_hit = coll(f_rect)
			playing_hint = False
			active = False

			# Determine tab background colour
			if not gui.radio_view:
				if i == pctl.active_playlist_viewing:
					bg = colours.tab_background_active
					active = True
				elif (
						tab_menu.active is True and tab_menu.reference == i) or (tab_menu.active is False and tab_hit and not playlist_box.drag):
					bg = colours.tab_highlight
				elif i == pctl.active_playlist_playing:
					bg = colours.tab_background
					playing_hint = True
				else:
					bg = colours.tab_background
			elif pctl.radio_playlist_viewing == i:
				bg = colours.tab_background_active
				active = True
			else:
				bg = colours.tab_background

			# Draw tab background
			ddt.rect(rect, bg)
			if playing_hint:
				ddt.rect(rect, [255, 255, 255, 7])

			# Determine text colour
			if active:
				fg = colours.tab_text_active
			else:
				fg = colours.tab_text

			# Draw tab text
			if gui.radio_view:
				text = tab["name"]
			else:
				text = tab.title
			ddt.text((x + self.tab_text_start_space, y + self.tab_text_y_offset), text, fg, self.tab_text_font, bg=bg)

			# Drop pulse
			if gui.pl_pulse and gui.drop_playlist_target == i:
				if tab_pulse.render(x, y + self.height - bar_highlight_size, tab_width, bar_highlight_size, r=200,
									g=130) is False:
					gui.pl_pulse = False

			# Drag to move playlist
			if tab_hit:
				if mouse_down and i != playlist_box.drag_on and playlist_box.drag is True:

					if key_shift_down:
						ddt.rect((x, y + self.height - bar_highlight_size, tab_width, bar_highlight_size), [80, 160, 200, 255])
					elif playlist_box.drag_on < i:
						ddt.rect((x + tab_width - bar_highlight_size, y, bar_highlight_size, gui.panelY2), [80, 160, 200, 255])
					else:
						ddt.rect((x, y, bar_highlight_size, gui.panelY2), [80, 160, 200, 255])

				elif quick_drag is True and pl_is_mut(i):
					ddt.rect((x, y + self.height - bar_highlight_size, tab_width, bar_highlight_size), [80, 200, 180, 255])
			# Drag yellow line highlight if single track already in playlist
			elif quick_drag and not point_proximity_test(gui.drag_source_position, mouse_position, 15 * gui.scale):
				for item in shift_selection:
					if item < len(default_playlist) and default_playlist[item] in tab.playlist_ids:
						ddt.rect((x, y + self.height - bar_highlight_size, tab_width, bar_highlight_size), [190, 160, 20, 255])
						break
			# Drag red line highlight if playlist is generator playlist
			if quick_drag and not point_proximity_test(gui.drag_source_position, mouse_position, 15 * gui.scale):
				if not pl_is_mut(i):
					ddt.rect((x, y + self.height - bar_highlight_size, tab_width, bar_highlight_size), [200, 70, 50, 255])

			if not gui.radio_view:
				if len(self.adds) > 0:
					for k in reversed(range(len(self.adds))):
						if pctl.multi_playlist[i].uuid_int == self.adds[k][0]:
							if self.adds[k][2].get() > 0.3:
								del self.adds[k]
							else:
								ay = y + 4
								ay -= 6 * self.adds[k][2].get() / 0.3

								ddt.text(
									(x + tab_width - 3, int(round(ay)), 1), "+" + str(self.adds[k][1]), colours.pluse_colour, 212, bg=bg)
								gui.update += 1

			x += tab_width + self.tab_spacing

		# Quick drag single track onto bar to create new playlist function and indicator
		if prefs.tabs_on_top:
			if quick_drag and mouse_position[0] > x and mouse_position[1] < gui.panelY and quick_d_timer.get() > 1:
				ddt.rect((x, y, 2 * gui.scale, gui.panelY2), [80, 200, 180, 255])

				if mouse_up:
					drop_tracks_to_new_playlist(shift_selection)

			# Draw end drag tab indicator
			if playlist_box.drag and mouse_position[0] > x and mouse_position[1] < gui.panelY:
				if key_ctrl_down:
					ddt.rect((x, y, 2 * gui.scale, gui.panelY2), [255, 190, 0, 255])
				else:
					ddt.rect((x, y, 2 * gui.scale, gui.panelY2), [80, 160, 200, 255])

		if prefs.tabs_on_top and right_overflow:
			x += 24 * gui.scale
			self.tabs_right_x += 24 * gui.scale

		# -------------
		# Other input
		if mouse_up:
			quick_drag = False
			playlist_box.drag = False
			radio_view.drag = None

		# Scroll anywhere on panel to cycle playlist
		# (This is a bit complicated because we need to skip over hidden playlists)
		if mouse_wheel != 0 and 1 < mouse_position[1] < gui.panelY + 1 and len(pctl.multi_playlist) > 1 and mouse_position[0] > 5:

			cycle_playlist_pinned(mouse_wheel)

			gui.pl_update = 1
			if not prefs.tabs_on_top:
				if pctl.active_playlist_viewing not in shown:  # and not gui.lsp:
					gui.mode_toast_text = _(pctl.multi_playlist[pctl.active_playlist_viewing].title)
					toast_mode_timer.set()
					gui.frame_callback_list.append(TestTimer(1))
				else:
					toast_mode_timer.force_set(10)
					gui.mode_toast_text = ""
		# ---------
		# Menu Bar

		x += self.ini_menu_space
		y += 7 * gui.scale
		ddt.text_background_colour = colours.top_panel_background

		# MENU -----------------------------

		word = _("MENU")
		word_length = ddt.get_text_w(word, 212)
		rect = [x - self.click_buffer, yy + self.ty + 1, word_length + self.click_buffer * 2, self.height - 1]
		hit = coll(rect)
		fields.add(rect)

		if (x_menu.active or hit) and not tab_menu.active:
			bg = colours.status_text_over
		else:
			bg = colours.status_text_normal
		ddt.text((x, y), word, bg, 212)

		if hit and inp.mouse_click:
			if x_menu.active:
				x_menu.active = False
			else:
				xx = x
				if x > window_size[0] - (210 * gui.scale):
					xx = window_size[0] - round(210 * gui.scale)
				x_menu.activate(position=(xx + round(12 * gui.scale), gui.panelY))
				view_box.activate(xx)

		# if True:
		#     border = round(3 * gui.scale)
		#     border_colour = colours.grey(30)
		#     rect = (5 * gui.scale, gui.panelY, round(90 * gui.scale), round(25 * gui.scale))
		#

		dl = len(dl_mon.ready)
		watching = len(dl_mon.watching)

		if (dl > 0 or watching > 0) and core_timer.get() > 2 and prefs.auto_extract and prefs.monitor_downloads:
			x += 52 * gui.scale
			rect = (x - 5 * gui.scale, y - 2 * gui.scale, 30 * gui.scale, 23 * gui.scale)
			fields.add(rect)

			if coll(rect):
				colour = colours.corner_button_active
				# if colours.lm:
				#     colour = [40, 40, 40, 255]
				if dl > 0 or watching > 0:
					if right_click:
						dl_menu.activate(position=(mouse_position[0], gui.panelY))
				if dl > 0:
					if inp.mouse_click:
						pln = 0
						for item in dl_mon.ready:
							load_order = LoadClass()
							load_order.target = item
							pln = pctl.active_playlist_viewing
							load_order.playlist = pctl.multi_playlist[pln].uuid_int

							for i, pl in enumerate(pctl.multi_playlist):
								if prefs.download_playlist is not None:
									if pl.uuid_int == prefs.download_playlist:
										load_order.playlist = pl.uuid_int
										pln = i
										break
							else:
								for i, pl in enumerate(pctl.multi_playlist):
									if pl.title.lower() == "downloads":
										load_order.playlist = pl.uuid_int
										pln = i
										break

							load_orders.append(copy.deepcopy(load_order))

						if len(dl_mon.ready) > 0:
							dl_mon.ready.clear()
							switch_playlist(pln)

							pctl.playlist_view_position = len(default_playlist)
							logging.debug("Position changed by track import")
							gui.update += 1
				else:
					colour = colours.corner_button  # [60, 60, 60, 255]
					# if colours.lm:
					#     colour = [180, 180, 180, 255]
					if inp.mouse_click:
						inp.mouse_click = False
						show_message(
							_("It looks like something is being downloaded..."), _("Let's check back later..."), mode="info")


			else:
				colour = colours.corner_button  # [60, 60, 60, 255]
				if colours.lm:
					# colour = [180, 180, 180, 255]
					if dl_mon.ready:
						colour = colours.corner_button_active  # [60, 60, 60, 255]

			self.dl_button.render(x, y + 1 * gui.scale, colour)
			if dl > 0:
				ddt.text((x + 18 * gui.scale, y - 4 * gui.scale), str(dl), colours.pluse_colour, 209)  # [244, 223, 66, 255]
				# [166, 244, 179, 255]

		# LAYOUT --------------------------------
		x += self.menu_space + word_length

		self.drag_zone_start_x = x - 5 * gui.scale
		status = True

		if loading_in_progress:

			bg = colours.status_info_text
			if to_got == "xspf":
				text = _("Importing XSPF playlist")
			elif to_got == "xspfl":
				text = _("Importing XSPF playlist...")
			elif to_got == "ex":
				text = _("Extracting Archive...")
			else:
				text = _("Importing...  ") + str(to_got)  # + "/" + str(to_get)
				if right_click and coll([x, y, 180 * gui.scale, 18 * gui.scale]):
					cancel_menu.activate(position=(x + 20 * gui.scale, y + 23 * gui.scale))
		elif after_scan:
			# bg = colours.status_info_text
			bg = [100, 200, 100, 255]
			text = _("Scanning Tags...  {N} remaining").format(N=str(len(after_scan)))
		elif move_in_progress:
			text = _("File copy in progress...")
			bg = colours.status_info_text
		elif cm_clean_db and to_get > 0:
			per = str(int(to_got / to_get * 100))
			text = _("Cleaning db...  ") + per + "%"
			bg = [100, 200, 100, 255]
		elif to_scan:
			text = _("Rescanning Tags...  {N} remaining").format(N=str(len(to_scan)))
			bg = [100, 200, 100, 255]
		elif plex.scanning:
			text = _("Accessing PLEX library...")
			if gui.to_got:
				text += f" {gui.to_got}"
			bg = [229, 160, 13, 255]
		elif tauon.spot_ctl.launching_spotify:
			text = _("Launching Spotify...")
			bg = [30, 215, 96, 255]
		elif tauon.spot_ctl.preparing_spotify:
			text = _("Preparing Spotify Playback...")
			bg = [30, 215, 96, 255]
		elif tauon.spot_ctl.spotify_com:
			text = _("Accessing Spotify library...")
			bg = [30, 215, 96, 255]
		elif subsonic.scanning:
			text = _("Accessing AIRSONIC library...")
			if gui.to_got:
				text += f" {gui.to_got}"
			bg = [58, 194, 224, 255]
		elif koel.scanning:
			text = _("Accessing KOEL library...")
			bg = [111, 98, 190, 255]
		elif jellyfin.scanning:
			text = _("Accessing JELLYFIN library...")
			bg = [90, 170, 240, 255]
		elif tauon.chrome_mode:
			text = _("Chromecast Mode")
			bg = [207, 94, 219, 255]
		elif gui.sync_progress and not transcode_list:
			text = gui.sync_progress
			bg = [100, 200, 100, 255]
			if right_click and coll([x, y, 280 * gui.scale, 18 * gui.scale]):
				cancel_menu.activate(position=(x + 20 * gui.scale, y + 23 * gui.scale))
		elif transcode_list and gui.tc_cancel:
			bg = [150, 150, 150, 255]
			text = _("Stopping transcode...")
		elif lastfm.scanning_friends or lastfm.scanning_loves:
			text = _("Scanning: ") + lastfm.scanning_username
			bg = [200, 150, 240, 255]
		elif lastfm.scanning_scrobbles:
			text = _("Scanning Scrobbles...")
			bg = [219, 88, 18, 255]
		elif gui.buffering:
			text = _("Buffering... ")
			text += gui.buffering_text
			bg = [18, 180, 180, 255]

		elif lfm_scrobbler.queue and scrobble_warning_timer.get() < 260:
			text = _("Network error. Will try again later.")
			bg = [250, 250, 250, 255]
			last_fm_icon.render(x - 4 * gui.scale, y + 4 * gui.scale, [250, 40, 40, 255])
			x += 21 * gui.scale
		elif tauon.listen_alongers:
			new = {}
			for ip, timer in tauon.listen_alongers.items():
				if timer.get() < 6:
					new[ip] = timer
			tauon.listen_alongers = new

			text = _("{N} listening along").format(N=len(tauon.listen_alongers))
			bg = [40, 190, 235, 255]
		else:
			status = False

		if status:
			x += ddt.text((x, y), text, bg, 311)
			# x += ddt.get_text_w(text, 11)
		# TODO list listenieng clients
		elif transcode_list:
			bg = colours.status_info_text
			# if key_ctrl_down and key_c_press:
			#     del transcode_list[1:]
			#     gui.tc_cancel = True
			if right_click and coll([x, y, 280 * gui.scale, 18 * gui.scale]):
				cancel_menu.activate(position=(x + 20 * gui.scale, y + 23 * gui.scale))

			w = 100 * gui.scale
			x += ddt.text((x, y), _("Transcoding"), bg, 311) + 8 * gui.scale

			if gui.transcoding_batch_total:

				# c1 = [40, 40, 40, 255]
				# c2 = [60, 60, 60, 255]
				# c3 = [130, 130, 130, 255]
				#
				# if colours.lm:
				#     c1 = [100, 100, 100, 255]
				#     c2 = [130, 130, 130, 255]
				#     c3 = [180, 180, 180, 255]

				c1 = [40, 40, 40, 255]
				c2 = [100, 59, 200, 200]
				c3 = [150, 70, 200, 255]

				if colours.lm:
					c1 = [100, 100, 100, 255]
					c2 = [170, 140, 255, 255]
					c3 = [230, 170, 255, 255]

				yy = y + 4 * gui.scale
				h = 9 * gui.scale
				box = [x, yy, w, h]
				# ddt.rect_r(box, [100, 100, 100, 255])
				ddt.rect(box, c1)

				done = round(gui.transcoding_bach_done / gui.transcoding_batch_total * 100)
				doing = round(core_use / gui.transcoding_batch_total * 100)

				ddt.rect([x, yy, done, h], c3)
				ddt.rect([x + done, yy, doing, h], c2)

			x += w + 8 * gui.scale

			if gui.sync_progress:
				text = gui.sync_progress
			else:
				text = _("{N} Folder Remaining {T}").format(N=str(len(transcode_list)), T=transcode_state)
				if len(transcode_list) > 1:
					text = _("{N} Folders Remaining {T}").format(N=str(len(transcode_list)), T=transcode_state)

			x += ddt.text((x, y), text, bg, 311) + 8 * gui.scale


		if colours.lm:
			colours.tb_line = colours.grey(200)
			ddt.rect((0, int(gui.panelY - 1 * gui.scale), window_size[0], int(1 * gui.scale)), colours.tb_line)

class BottomBarType1:
	def __init__(self):

		self.mode = 0

		self.seek_time = 0

		self.seek_down = False
		self.seek_hit = False
		self.volume_hit = False
		self.volume_bar_being_dragged = False
		self.control_line_bottom = 35 * gui.scale
		self.repeat_click_off = False
		self.random_click_off = False

		self.seek_bar_position = [300 * gui.scale, window_size[1] - gui.panelBY]
		self.seek_bar_size = [window_size[0] - (300 * gui.scale), 15 * gui.scale]
		self.volume_bar_size = [135 * gui.scale, 14 * gui.scale]
		self.volume_bar_position = [0, 45 * gui.scale]

		self.play_button = asset_loader(scaled_asset_directory, loaded_asset_dc, "play.png", True)
		self.forward_button = asset_loader(scaled_asset_directory, loaded_asset_dc, "ff.png", True)
		self.back_button = asset_loader(scaled_asset_directory, loaded_asset_dc, "bb.png", True)
		self.repeat_button = asset_loader(scaled_asset_directory, loaded_asset_dc, "tauon_repeat.png", True)
		self.repeat_button_off = asset_loader(scaled_asset_directory, loaded_asset_dc, "tauon_repeat_off.png", True)
		self.shuffle_button_off = asset_loader(scaled_asset_directory, loaded_asset_dc, "tauon_shuffle_off.png", True)
		self.shuffle_button = asset_loader(scaled_asset_directory, loaded_asset_dc, "tauon_shuffle.png", True)
		self.repeat_button_a = asset_loader(scaled_asset_directory, loaded_asset_dc, "tauon_repeat_a.png", True)
		self.shuffle_button_a = asset_loader(scaled_asset_directory, loaded_asset_dc, "tauon_shuffle_a.png", True)

		self.buffer_shard = asset_loader(scaled_asset_directory, loaded_asset_dc, "shard.png", True)

		self.scrob_stick = 0

	def update(self):

		if self.mode == 0:
			self.volume_bar_position[0] = window_size[0] - (210 * gui.scale)
			self.volume_bar_position[1] = window_size[1] - (27 * gui.scale)
			self.seek_bar_position[1] = window_size[1] - gui.panelBY

			seek_bar_x = 300 * gui.scale
			if window_size[0] < 600 * gui.scale:
				seek_bar_x = 250 * gui.scale

			self.seek_bar_size[0] = window_size[0] - seek_bar_x
			self.seek_bar_position[0] = seek_bar_x

			# if gui.bb_show_art:
			#     self.seek_bar_position[0] = 300 + gui.panelBY
			#     self.seek_bar_size[0] = window_size[0] - 300 - gui.panelBY

			# self.seek_bar_position[0] = 0
			# self.seek_bar_size[0] = window_size[0]

	def render(self):

		global volume_store
		global clicked
		global right_click

		ddt.rect_a((0, window_size[1] - gui.panelBY), (window_size[0], gui.panelBY), colours.bottom_panel_colour)

		ddt.rect_a(self.seek_bar_position, self.seek_bar_size, colours.seek_bar_background)

		right_offset = 0
		if gui.display_time_mode >= 2:
			right_offset = 22 * gui.scale

		if window_size[0] < 670 * gui.scale:
			right_offset -= 90 * gui.scale
		# Scrobble marker

		if prefs.scrobble_mark and (
				prefs.auto_lfm or lb.enable or prefs.maloja_enable) and not prefs.scrobble_hold and pctl.playing_length > 0 and 3 > pctl.playing_state > 0:
			if pctl.master_library[pctl.track_queue[pctl.queue_step]].length > 240 * 2:
				l_target = 240
			else:
				l_target = int(pctl.master_library[pctl.track_queue[pctl.queue_step]].length * 0.50)
			l_lead = l_target - pctl.a_time

			if l_lead > 0 and pctl.master_library[pctl.track_queue[pctl.queue_step]].length > 30:
				l_x = self.seek_bar_position[0] + int(math.ceil(
					pctl.playing_time * self.seek_bar_size[0] / int(pctl.playing_length)))
				l_x += int(math.ceil(self.seek_bar_size[0] / int(pctl.playing_length) * l_lead))

				if abs(self.scrob_stick - l_x) < 2:
					l_x = self.scrob_stick
				else:
					self.scrob_stick = l_x
				ddt.rect((self.scrob_stick, self.seek_bar_position[1], 2 * gui.scale, self.seek_bar_size[1]), [240, 10, 10, 80])

		# # MINI ALBUM ART
		# if gui.bb_show_art:
		#     rect = [self.seek_bar_position[0] - gui.panelBY, self.seek_bar_position[1], gui.panelBY, gui.panelBY]
		#     ddt.rect_r(rect, [255, 255, 255, 8], True)
		#     if 3 > pctl.playing_state > 0:
		#         album_art_gen.display(pctl.track_queue[pctl.queue_step], (rect[0], rect[1]), (rect[2], rect[3]))

		# ddt.rect_r(rect, [255, 255, 255, 20])

		# SEEK BAR------------------
		if pctl.playing_time < 1:
			self.seek_time = 0

		if inp.mouse_click and coll_point(
			mouse_position,
			self.seek_bar_position + [self.seek_bar_size[0]] + [
			self.seek_bar_size[1] + 2]):
			self.seek_down = True
			self.volume_hit = True
		if right_click and coll_point(
			mouse_position, self.seek_bar_position + [self.seek_bar_size[0]] + [self.seek_bar_size[1] + 2]):
			pctl.pause()
			if pctl.playing_state == 0:
				pctl.play()

		fields.add(self.seek_bar_position + self.seek_bar_size)
		if coll(self.seek_bar_position + self.seek_bar_size):

			if middle_click and pctl.playing_state > 0:
				gui.seek_cur_show = True

			clicked = True
			if mouse_wheel != 0:
				pctl.seek_time(pctl.playing_time + (mouse_wheel * 3))

		if gui.seek_cur_show:
			gui.update += 1

			# fields.add([mouse_position[0] - 1, mouse_position[1] - 1, 1, 1])
			# ddt.rect_r([mouse_position[0] - 1, mouse_position[1] - 1, 1, 1], [255,0,0,180], True)

			bargetX = mouse_position[0]
			bargetX = min(bargetX, self.seek_bar_position[0] + self.seek_bar_size[0])
			bargetX = max(bargetX, self.seek_bar_position[0])
			bargetX -= self.seek_bar_position[0]
			seek = bargetX / self.seek_bar_size[0]
			gui.cur_time = get_display_time(pctl.playing_object().length * seek)

		if self.seek_down is True:
			if mouse_position[0] == 0:
				self.seek_down = False
				self.seek_hit = True

		if (mouse_up and coll(self.seek_bar_position + self.seek_bar_size) and coll_point(
			last_click_location, self.seek_bar_position + self.seek_bar_size)
			and coll_point(
				click_location, self.seek_bar_position + self.seek_bar_size)) or (mouse_up and self.volume_hit) or self.seek_hit:

			self.volume_hit = False
			self.seek_down = False
			self.seek_hit = False

			bargetX = mouse_position[0]
			bargetX = min(bargetX, self.seek_bar_position[0] + self.seek_bar_size[0])
			bargetX = max(bargetX, self.seek_bar_position[0])
			bargetX -= self.seek_bar_position[0]
			seek = bargetX / self.seek_bar_size[0]

			pctl.seek_decimal(seek)
			#logging.info(seek)

			self.seek_time = pctl.playing_time

		if radiobox.load_connecting or gui.buffering:
			x = self.seek_bar_position[0] - round(26 - gui.scale)
			y = self.seek_bar_position[1]
			while x < self.seek_bar_position[0] + self.seek_bar_size[0]:
				offset = (math.floor(((core_timer.get() * 1) % 1) * 13) / 13) * self.buffer_shard.w
				gui.delay_frame(0.01)

				# colour = colours.seek_bar_fill
				h, l, s = rgb_to_hls(
					colours.seek_bar_background[0], colours.seek_bar_background[1], colours.seek_bar_background[2])
				l = min(1, l + 0.05)
				colour = hls_to_rgb(h, l, s)
				colour[3] = colours.seek_bar_background[3]

				self.buffer_shard.render(x + offset, y, colour)
				x += self.buffer_shard.w

			ddt.rect(
				(self.seek_bar_position[0] - self.buffer_shard.w, y, self.buffer_shard.w, self.buffer_shard.h),
				colours.bottom_panel_colour)

		if pctl.playing_length > 0:

			if pctl.download_time != 0:

				if pctl.download_time == -1:
					pctl.download_time = pctl.playing_length

				colour = (255, 255, 255, 10)
				if gui.theme_name == "Lavender Light" or gui.theme_name == "Carbon":
					colour = (255, 255, 255, 40)

				gui.seek_bar_rect = (
					self.seek_bar_position[0], self.seek_bar_position[1],
					int(pctl.download_time * self.seek_bar_size[0] / pctl.playing_length),
					self.seek_bar_size[1])
				ddt.rect(gui.seek_bar_rect, colour)

			gui.seek_bar_rect = (
				self.seek_bar_position[0], self.seek_bar_position[1],
				int(self.seek_time * self.seek_bar_size[0] / pctl.playing_length),
				self.seek_bar_size[1])
			ddt.rect(gui.seek_bar_rect, colours.seek_bar_fill)

		if gui.seek_cur_show:

			if coll(
				[self.seek_bar_position[0] - 50, self.seek_bar_position[1] - 50, self.seek_bar_size[0] + 50, self.seek_bar_size[1] + 100]):
				if mouse_position[0] > self.seek_bar_position[0] - 1:
					cur = [mouse_position[0] - 40, self.seek_bar_position[1] - 25, 42, 19]
					ddt.rect(cur, colours.grey(15))
					# ddt.rect_r(cur, colours.grey(80))
					ddt.text(
						(mouse_position[0] - 40 + 3, self.seek_bar_position[1] - 24), gui.cur_time,
						colours.grey(180), 213,
						bg=colours.grey(15))

					ddt.rect(
						[mouse_position[0], self.seek_bar_position[1], 2, self.seek_bar_size[1]],
						[100, 100, 20, 255])

			else:
				gui.seek_cur_show = False

		if gui.buffering and pctl.buffering_percent:
			ddt.rect_a((self.seek_bar_position[0], self.seek_bar_position[1] + self.seek_bar_size[1] - round(3 * gui.scale)), (self.seek_bar_size[0] * pctl.buffering_percent / 100, round(3 * gui.scale)), [255, 255, 255, 50])
		# Volume mouse wheel control -----------------------------------------
		if mouse_wheel != 0 and mouse_position[1] > self.seek_bar_position[1] + 4 and not coll_point(
			mouse_position, self.seek_bar_position + self.seek_bar_size):

			pctl.player_volume += mouse_wheel * prefs.volume_wheel_increment
			if pctl.player_volume < 1:
				pctl.player_volume = 0
			elif pctl.player_volume > 100:
				pctl.player_volume = 100

			pctl.player_volume = int(pctl.player_volume)
			pctl.set_volume()

		# Volume Bar 2 ------------------------------------------------
		if window_size[0] < 670 * gui.scale:
			x = window_size[0] - right_offset - 207 * gui.scale
			y = window_size[1] - round(14 * gui.scale)

			rect = (x - 8 * gui.scale, y - 17 * gui.scale, 55 * gui.scale, 23 * gui.scale)
			# ddt.rect(rect, [255,255,255,25])
			if coll(rect) and mouse_down:
				gui.update_on_drag = True

			h_rect = (x - 6 * gui.scale, y - 17 * gui.scale, 4 * gui.scale, 23 * gui.scale)
			if coll(h_rect) and mouse_down:
				pctl.player_volume = 0

			step = round(1 * gui.scale)
			min_h = round(4 * gui.scale)
			spacing = round(5 * gui.scale)

			if right_click and coll((h_rect[0], h_rect[1], h_rect[2] + 50 * gui.scale, h_rect[3])):
				if right_click:
					pctl.toggle_mute()

			for bar in range(8):

				h = min_h + bar * step
				rect = (x, y - h, 3 * gui.scale, h)
				h_rect = (x - 1 * gui.scale, y - 17 * gui.scale, 4 * gui.scale, 23 * gui.scale)

				if coll(h_rect):
					if mouse_down or mouse_up:
						gui.update_on_drag = True

						if bar == 0:
							pctl.player_volume = 5
						if bar == 1:
							pctl.player_volume = 10
						if bar == 2:
							pctl.player_volume = 20
						if bar == 3:
							pctl.player_volume = 30
						if bar == 4:
							pctl.player_volume = 45
						if bar == 5:
							pctl.player_volume = 55
						if bar == 6:
							pctl.player_volume = 70
						if bar == 7:
							pctl.player_volume = 100

						pctl.set_volume()

				colour = colours.mode_button_off

				if bar == 0 and pctl.player_volume > 0:
					colour = colours.mode_button_active
				elif bar == 1 and pctl.player_volume >= 10:
					colour = colours.mode_button_active
				elif bar == 2 and pctl.player_volume >= 20:
					colour = colours.mode_button_active
				elif bar == 3 and pctl.player_volume >= 30:
					colour = colours.mode_button_active
				elif bar == 4 and pctl.player_volume >= 45:
					colour = colours.mode_button_active
				elif bar == 5 and pctl.player_volume >= 55:
					colour = colours.mode_button_active
				elif bar == 6 and pctl.player_volume >= 70:
					colour = colours.mode_button_active
				elif bar == 7 and pctl.player_volume >= 95:
					colour = colours.mode_button_active

				ddt.rect(rect, colour)
				x += spacing

		# Volume Bar --------------------------------------------------------
		else:
			if (inp.mouse_click and coll((
					self.volume_bar_position[0] - right_offset, self.volume_bar_position[1], self.volume_bar_size[0],
					self.volume_bar_size[1] + 4))) or \
					self.volume_bar_being_dragged is True:
				clicked = True

				if inp.mouse_click is True or self.volume_bar_being_dragged is True:
					gui.update = 2

					self.volume_bar_being_dragged = True
					volgetX = mouse_position[0]
					volgetX = min(volgetX, self.volume_bar_position[0] + self.volume_bar_size[0] - right_offset)
					volgetX = max(volgetX, self.volume_bar_position[0] - right_offset)
					volgetX -= self.volume_bar_position[0] - right_offset
					pctl.player_volume = volgetX / self.volume_bar_size[0] * 100

					time.sleep(0.02)

					if mouse_down is False:
						self.volume_bar_being_dragged = False
						pctl.player_volume = int(pctl.player_volume)
						pctl.set_volume(True)

				if mouse_down:
					pctl.player_volume = int(pctl.player_volume)
					pctl.set_volume(False)

			if right_click and coll((
					self.volume_bar_position[0] - 15 * gui.scale, self.volume_bar_position[1] - 10 * gui.scale,
					self.volume_bar_size[0] + 30 * gui.scale,
					self.volume_bar_size[1] + 20 * gui.scale)):

				if pctl.player_volume > 0:
					volume_store = pctl.player_volume
					pctl.player_volume = 0
				else:
					pctl.player_volume = volume_store

				pctl.set_volume()

			ddt.rect_a(
				(self.volume_bar_position[0] - right_offset, self.volume_bar_position[1]),
				self.volume_bar_size, colours.volume_bar_background)  # 22

			gui.volume_bar_rect = (
				self.volume_bar_position[0] - right_offset, self.volume_bar_position[1],
				int(pctl.player_volume * self.volume_bar_size[0] / 100), self.volume_bar_size[1])

			ddt.rect(gui.volume_bar_rect, colours.volume_bar_fill)

			fields.add(self.volume_bar_position + self.volume_bar_size)
			if pctl.active_replaygain != 0 and (coll((
				self.volume_bar_position[0], self.volume_bar_position[1], self.volume_bar_size[0],
				self.volume_bar_size[1])) or self.volume_bar_being_dragged):

				if pctl.player_volume > 50:
					ddt.text(
						(self.volume_bar_position[0] - right_offset + 8 * gui.scale,
						self.volume_bar_position[1] - 1 * gui.scale), str(pctl.active_replaygain) + " dB",
						colours.volume_bar_background,
						11, bg=colours.volume_bar_fill)
				else:
					ddt.text(
						(self.volume_bar_position[0] - right_offset + 85 * gui.scale,
						self.volume_bar_position[1] - 1 * gui.scale), str(pctl.active_replaygain) + " dB",
						colours.volume_bar_fill,
						11, bg=colours.volume_bar_background)

		gui.show_bottom_title = gui.showed_title ^ True
		if not prefs.hide_bottom_title:
			gui.show_bottom_title = True

		if gui.show_bottom_title and pctl.playing_state > 0 and window_size[0] > 820 * gui.scale:
			line = pctl.title_text()

			x = self.seek_bar_position[0] + 1
			mx = window_size[0] - 710 * gui.scale
			# if gui.bb_show_art:
			#     x += 10 * gui.scale
			#     mx -= gui.panelBY - 10

			# line = trunc_line(line, 213, mx)
			ddt.text(
				(x, self.seek_bar_position[1] + 24 * gui.scale), line, colours.bar_title_text,
				fonts.panel_title, max_w=mx)

		if (inp.mouse_click or right_click) and coll((
				self.seek_bar_position[0] - 10 * gui.scale, self.seek_bar_position[1] + 20 * gui.scale,
				window_size[0] - 710 * gui.scale, 30 * gui.scale)):
			# if pctl.playing_state == 3:
			#     copy_to_clipboard(pctl.tag_meta)
			#     show_message("Copied text to clipboard")
			#     if input.mouse_click or right_click:
			#         input.mouse_click = False
			#         right_click = False
			# else:
			if inp.mouse_click and pctl.playing_state != 3:
				pctl.show_current()

			if pctl.playing_ready() and not gui.fullscreen:

				if right_click:
					mode_menu.activate()

				if d_click_timer.get() < 0.3 and inp.mouse_click:
					set_mini_mode()
					gui.update += 1
					return
				d_click_timer.set()

		# TIME----------------------

		x = window_size[0] - 57 * gui.scale
		y = window_size[1] - 29 * gui.scale

		r_start = x - 10 * gui.scale
		if gui.display_time_mode in (2, 3):
			r_start -= 20 * gui.scale
		rect = (r_start, y - 3 * gui.scale, 80 * gui.scale, 27 * gui.scale)
		# ddt.rect_r(rect, [255, 0, 0, 40], True)
		if inp.mouse_click and coll(rect):
			gui.display_time_mode += 1
			if gui.display_time_mode > 3:
				gui.display_time_mode = 0

		if gui.display_time_mode == 0:
			text_time = get_display_time(pctl.playing_time)
			ddt.text(
				(x + 1 * gui.scale, y), text_time, colours.time_playing,
				fonts.bottom_panel_time)
		elif gui.display_time_mode == 1:
			if pctl.playing_state == 0:
				text_time = get_display_time(0)
			else:
				text_time = get_display_time(pctl.playing_length - pctl.playing_time)
			ddt.text(
				(x + 1 * gui.scale, y), text_time, colours.time_playing,
				fonts.bottom_panel_time)
			ddt.text(
				(x - 5 * gui.scale, y), "-", colours.time_playing,
				fonts.bottom_panel_time)
		elif gui.display_time_mode == 2:

			# colours.time_sub = alpha_blend([255, 255, 255, 80], colours.bottom_panel_colour)

			x -= 4
			text_time = get_display_time(pctl.playing_time)
			ddt.text(
				(x - 25 * gui.scale, y), text_time, colours.time_playing,
				fonts.bottom_panel_time)

			offset1 = 10 * gui.scale

			if system == "Windows":
				offset1 += 2 * gui.scale

			offset2 = offset1 + 7 * gui.scale

			ddt.text(
				(x + offset1, y), "/", colours.time_sub,
				fonts.bottom_panel_time)
			text_time = get_display_time(pctl.playing_length)
			if pctl.playing_state == 0:
				text_time = get_display_time(0)
			elif pctl.playing_state == 3:
				text_time = "-- : --"
			ddt.text(
				(x + offset2, y), text_time, colours.time_sub,
				fonts.bottom_panel_time)

		elif gui.display_time_mode == 3:

			# colours.time_sub = alpha_blend([255, 255, 255, 80], colours.bottom_panel_colour)

			track = pctl.playing_object()
			if track and track.index != gui.dtm3_index:

				gui.dtm3_cum = 0
				gui.dtm3_total = 0
				run = True
				collected = []
				for item in default_playlist:
					if pctl.master_library[item].parent_folder_path == track.parent_folder_path:
						if item not in collected:
							collected.append(item)
							gui.dtm3_total += pctl.master_library[item].length
							if item == track.index:
								run = False
							if run:
								gui.dtm3_cum += pctl.master_library[item].length
				gui.dtm3_index = track.index

			x -= 4
			text_time = get_display_time(gui.dtm3_cum + pctl.playing_time)

			ddt.text(
				(x - 25 * gui.scale, y), text_time, colours.time_playing,
				fonts.bottom_panel_time)

			offset1 = 10 * gui.scale
			if system == "Windows":
				offset1 += 2 * gui.scale
			offset2 = offset1 + 7 * gui.scale

			ddt.text(
				(x + offset1, y), "/", colours.time_sub,
				fonts.bottom_panel_time)
			text_time = get_display_time(gui.dtm3_total)
			if pctl.playing_state == 0:
				text_time = get_display_time(0)
			elif pctl.playing_state == 3:
				text_time = "-- : --"
			ddt.text(
				(x + offset2, y), text_time, colours.time_sub,
				fonts.bottom_panel_time)

		# BUTTONS
		# bottom buttons

		if gui.mode == 1:

			# PLAY---
			buttons_x_offset = 0
			compact = False
			if window_size[0] < 650 * gui.scale:
				compact = True

			play_colour = colours.media_buttons_off
			pause_colour = colours.media_buttons_off
			stop_colour = colours.media_buttons_off
			forward_colour = colours.media_buttons_off
			back_colour = colours.media_buttons_off

			if pctl.playing_state == 1:
				play_colour = colours.media_buttons_active

			if pctl.auto_stop:
				stop_colour = colours.media_buttons_active

			if pctl.playing_state == 2 or (tauon.spot_ctl.coasting and tauon.spot_ctl.paused):
				pause_colour = colours.media_buttons_active
				play_colour = colours.media_buttons_active
			elif pctl.playing_state == 3:
				play_colour = colours.media_buttons_active
				if tauon.stream_proxy.encode_running:
					play_colour = [220, 50, 50, 255]

			if not compact or (compact and pctl.playing_state != 1):
				rect = (
				buttons_x_offset + (10 * gui.scale), window_size[1] - self.control_line_bottom - (13 * gui.scale),
				50 * gui.scale, 40 * gui.scale)
				fields.add(rect)
				if coll(rect):
					play_colour = colours.media_buttons_over
					if inp.mouse_click:
						if compact and pctl.playing_state == 1:
							pctl.pause()
						elif pctl.playing_state == 1 or tauon.spot_ctl.coasting:
							pctl.show_current(highlight=True)
						else:
							pctl.play()
						inp.mouse_click = False
					tool_tip2.test(33 * gui.scale, y - 35 * gui.scale, _("Play, RC: Go to playing"))

					if right_click:
						pctl.show_current(highlight=True)

				self.play_button.render(29 * gui.scale, window_size[1] - self.control_line_bottom, play_colour)
				# ddt.rect_r(rect,[255,0,0,255], True)

			# PAUSE---
			if compact:
				buttons_x_offset = -46 * gui.scale

			x = (75 * gui.scale) + buttons_x_offset
			y = window_size[1] - self.control_line_bottom

			if not compact or (compact and pctl.playing_state == 1):

				rect = (x - 15 * gui.scale, y - 13 * gui.scale, 50 * gui.scale, 40 * gui.scale)
				fields.add(rect)
				if coll(rect) and not (pctl.playing_state == 3 and not tauon.spot_ctl.coasting):
					pause_colour = colours.media_buttons_over
					if inp.mouse_click:
						pctl.pause()
					if right_click:
						pctl.show_current(highlight=True)
					tool_tip2.test(x, y - 35 * gui.scale, _("Pause"))

				# ddt.rect_r(rect,[255,0,0,255], True)
				ddt.rect_a((x, y + 0), (4 * gui.scale, 13 * gui.scale), pause_colour)
				ddt.rect_a((x + 10 * gui.scale, y + 0), (4 * gui.scale, 13 * gui.scale), pause_colour)

			# STOP---
			x = 125 * gui.scale + buttons_x_offset
			rect = (x - 14 * gui.scale, y - 13 * gui.scale, 50 * gui.scale, 40 * gui.scale)
			fields.add(rect)
			if coll(rect):
				stop_colour = colours.media_buttons_over
				if inp.mouse_click:
					pctl.stop()
				if right_click:
					pctl.auto_stop ^= True
				tool_tip2.test(x, y - 35 * gui.scale, _("Stop, RC: Toggle auto-stop"))

			ddt.rect_a((x, y + 0), (13 * gui.scale, 13 * gui.scale), stop_colour)
			# ddt.rect_r(rect,[255,0,0,255], True)

			if compact:
				buttons_x_offset -= 5 * gui.scale

			# FORWARD---
			rect = (buttons_x_offset + 230 * gui.scale, window_size[1] - self.control_line_bottom - 10 * gui.scale,
					50 * gui.scale, 35 * gui.scale)
			fields.add(rect)
			if coll(rect) and not (pctl.playing_state == 3 and not tauon.spot_ctl.coasting):
				forward_colour = colours.media_buttons_over
				if inp.mouse_click:
					pctl.advance()
					gui.tool_tip_lock_off_f = True
				if right_click:
					# pctl.random_mode ^= True
					toggle_random()
					gui.tool_tip_lock_off_f = True
					# if window_size[0] < 600 * gui.scale:
					# . Shuffle set to on
					gui.mode_toast_text = _("Shuffle On")
					if not pctl.random_mode:
						# . Shuffle set to off
						gui.mode_toast_text = _("Shuffle Off")
					toast_mode_timer.set()
					gui.delay_frame(1)
				if middle_click:
					pctl.advance(rr=True)
					gui.tool_tip_lock_off_f = True
				# tool_tip.test(buttons_x_offset + 230 * gui.scale + 50 * gui.scale, window_size[1] - self.control_line_bottom - 20 * gui.scale, "Advance")
				# if not gui.tool_tip_lock_off_f:
				#     tool_tip2.test(x + 45 * gui.scale, y - 35 * gui.scale, _("Forward, RC: Toggle shuffle, MC: Radio random"))
			else:
				gui.tool_tip_lock_off_f = False

			self.forward_button.render(
				buttons_x_offset + 240 * gui.scale, 1 + window_size[1] - self.control_line_bottom, forward_colour)

			# ddt.rect_r(rect,[255,0,0,255], True)

			# BACK---
			rect = (buttons_x_offset + 170 * gui.scale, window_size[1] - self.control_line_bottom - 10 * gui.scale,
					50 * gui.scale, 35 * gui.scale)
			fields.add(rect)
			if coll(rect) and not (pctl.playing_state == 3 and not tauon.spot_ctl.coasting):
				back_colour = colours.media_buttons_over
				if inp.mouse_click:
					pctl.back()
					gui.tool_tip_lock_off_b = True
				if right_click:
					toggle_repeat()
					gui.tool_tip_lock_off_b = True
					# if window_size[0] < 600 * gui.scale:
					# . Repeat set to on
					gui.mode_toast_text = _("Repeat On")
					if not pctl.repeat_mode:
						# . Repeat set to off
						gui.mode_toast_text = _("Repeat Off")
					toast_mode_timer.set()
					gui.delay_frame(1)
				if middle_click:
					pctl.revert()
					gui.tool_tip_lock_off_b = True
				if not gui.tool_tip_lock_off_b:
					tool_tip2.test(x, y - 35 * gui.scale, _("Back, RC: Toggle repeat, MC: Revert"))
			else:
				gui.tool_tip_lock_off_b = False

			self.back_button.render(buttons_x_offset + 180 * gui.scale, 1 + window_size[1] - self.control_line_bottom,
									back_colour)
			# ddt.rect_r(rect,[255,0,0,255], True)

			# menu button

			x = window_size[0] - 252 * gui.scale - right_offset
			y = window_size[1] - round(26 * gui.scale)
			rpbc = colours.mode_button_off
			rect = (x - 9 * gui.scale, y - 5 * gui.scale, 40 * gui.scale, 25 * gui.scale)
			fields.add(rect)
			if coll(rect):
				if not extra_menu.active:
					tool_tip.test(x, y - 28 * gui.scale, _("Playback menu"))
				rpbc = colours.mode_button_over
				if inp.mouse_click:
					extra_menu.activate(position=(x - 115 * gui.scale, y - 6 * gui.scale))
				elif right_click:
					mode_menu.activate(position=(x - 115 * gui.scale, y - 6 * gui.scale))
			if extra_menu.active:
				rpbc = colours.mode_button_active

			spacing = round(5 * gui.scale)
			ddt.rect_a((x, y), (24 * gui.scale, 2 * gui.scale), rpbc)
			y += spacing
			ddt.rect_a((x, y), (24 * gui.scale, 2 * gui.scale), rpbc)
			y += spacing
			ddt.rect_a((x, y), (24 * gui.scale, 2 * gui.scale), rpbc)

			if self.mode == 0 and window_size[0] > 530 * gui.scale:

				# shuffle button
				x = window_size[0] - 318 * gui.scale - right_offset
				y = window_size[1] - 27 * gui.scale

				rect = (x - 5 * gui.scale, y - 5 * gui.scale, 60 * gui.scale, 25 * gui.scale)
				fields.add(rect)

				rpbc = colours.mode_button_off
				off = True
				if (inp.mouse_click or right_click) and coll(rect):

					if inp.mouse_click:
						# pctl.random_mode ^= True
						toggle_random()
						if pctl.random_mode is False:
							self.random_click_off = True
					else:
						shuffle_menu.activate(position=(x + 30 * gui.scale, y - 7 * gui.scale))

				if pctl.random_mode:
					rpbc = colours.mode_button_active
					off = False
					if coll(rect):
						tool_tip.test(x, y - 28 * gui.scale, _("Shuffle"))
				elif coll(rect):
					tool_tip.test(x, y - 28 * gui.scale, _("Shuffle"))
					if self.random_click_off is True:
						rpbc = colours.mode_button_off
					elif pctl.random_mode is True:
						rpbc = colours.mode_button_active
					else:
						rpbc = colours.mode_button_over
				else:
					self.random_click_off = False

				# Keep hover highlight on if menu is open
				if shuffle_menu.active and not pctl.random_mode:
					rpbc = colours.mode_button_over

				#self.shuffle_button.render(x + round(1 * gui.scale), y + round(1 * gui.scale), rpbc)

				#y += round(3 * gui.scale)
				#ddt.rect_a((x, y), (25 * gui.scale, 3 * gui.scale), rpbc)

				if pctl.album_shuffle_mode:
					self.shuffle_button_a.render(x + round(1 * gui.scale), y + round(1 * gui.scale), rpbc)
				elif off:
					self.shuffle_button_off.render(x + round(1 * gui.scale), y + round(1 * gui.scale), rpbc)
				else:
					self.shuffle_button.render(x + round(1 * gui.scale), y + round(1 * gui.scale), rpbc)

					#ddt.rect_a((x + 25 * gui.scale, y), (23 * gui.scale, 3 * gui.scale), rpbc)

				#y += round(5 * gui.scale)
				#ddt.rect_a((x, y), (48 * gui.scale, 3 * gui.scale), rpbc)

				# REPEAT
				x = window_size[0] - round(380 * gui.scale) - right_offset
				y = window_size[1] - round(27 * gui.scale)

				rpbc = colours.mode_button_off
				off = True

				rect = (x - 6 * gui.scale, y - 5 * gui.scale, 61 * gui.scale, 25 * gui.scale)
				fields.add(rect)
				if (inp.mouse_click or right_click) and coll(rect):

					if inp.mouse_click:
						toggle_repeat()
						if pctl.repeat_mode is False:
							self.repeat_click_off = True
					else:  # right click
						repeat_menu.activate(position=(x + 30 * gui.scale, y - 7 * gui.scale))
						# pctl.album_repeat_mode ^= True
						# if not pctl.repeat_mode:
						#     self.repeat_click_off = True

				if pctl.repeat_mode:
					rpbc = colours.mode_button_active
					off = False
					if coll(rect):
						if pctl.album_repeat_mode:
							tool_tip.test(x, y - 28 * gui.scale, _("Repeat album"))
						else:
							tool_tip.test(x, y - 28 * gui.scale, _("Repeat track"))
				elif coll(rect):

					# Tooltips. But don't show tooltips if menus open
					if not repeat_menu.active and not shuffle_menu.active:
						if pctl.album_repeat_mode:
							tool_tip.test(x, y - 28 * gui.scale, _("Repeat album"))
						else:
							tool_tip.test(x, y - 28 * gui.scale, _("Repeat track"))

					if self.repeat_click_off is True:
						rpbc = colours.mode_button_off
					elif pctl.repeat_mode is True:
						rpbc = colours.mode_button_active
					else:
						rpbc = colours.mode_button_over
				else:
					self.repeat_click_off = False

				# Keep hover highlight on if menu is open
				if repeat_menu.active and not pctl.repeat_mode:
					rpbc = colours.mode_button_over

				rpbc = alpha_blend(rpbc, colours.bottom_panel_colour)  # bake in alpha in case of overlap

				y += round(3 * gui.scale)
				w = round(3 * gui.scale)
				y = round(y)
				x = round(x)

				ar = x + round(50 * gui.scale)
				h = round(5 * gui.scale)

				if pctl.album_repeat_mode:
					self.repeat_button_a.render(ar - round(45 * gui.scale), y - round(2 * gui.scale), rpbc)
					#ddt.rect_a((x + round(4 * gui.scale), y), (round(25 * gui.scale), w), rpbc)
				elif off:
					self.repeat_button_off.render(ar - round(45 * gui.scale), y - round(2 * gui.scale), rpbc)
				else:
					self.repeat_button.render(ar - round(45 * gui.scale), y - round(2 * gui.scale), rpbc)
				#ddt.rect_a((ar - round(25 * gui.scale), y), (round(25 * gui.scale), w), rpbc)
				#ddt.rect_a((ar - w, y), (w, h), rpbc)
				#ddt.rect_a((ar - round(50 * gui.scale), y + h), (round(50 * gui.scale), w), rpbc)

				# ddt.rect_a((x + round(25 * gui.scale), y), (round(25 * gui.scale), w), rpbc, True)
				# ddt.rect_a((x + round(4 * gui.scale), y + round(5 * gui.scale)), (math.floor(46 * gui.scale), w), rpbc, True)
				# ddt.rect_a((x + 50 * gui.scale - w, y), (w, 8 * gui.scale), rpbc, True)
				# ddt.rect_a((x + round(50 * gui.scale) - w, y + w), (w, round(4 * gui.scale)), rpbc, True)

class BottomBarType_ao1:
	def __init__(self):

		self.mode = 0

		self.seek_time = 0

		self.seek_down = False
		self.seek_hit = False
		self.volume_hit = False
		self.volume_bar_being_dragged = False
		self.control_line_bottom = 35 * gui.scale
		self.repeat_click_off = False
		self.random_click_off = False

		self.seek_bar_position = [300 * gui.scale, window_size[1] - gui.panelBY]
		self.seek_bar_size = [window_size[0] - (300 * gui.scale), 15 * gui.scale]
		self.volume_bar_size = [135 * gui.scale, 14 * gui.scale]
		self.volume_bar_position = [0, 45 * gui.scale]

		self.play_button = asset_loader(scaled_asset_directory, loaded_asset_dc, "play.png", True)
		self.forward_button = asset_loader(scaled_asset_directory, loaded_asset_dc, "ff.png", True)
		self.back_button = asset_loader(scaled_asset_directory, loaded_asset_dc, "bb.png", True)

		self.scrob_stick = 0

	def update(self):

		if self.mode == 0:
			self.volume_bar_position[0] = window_size[0] - (210 * gui.scale)
			self.volume_bar_position[1] = window_size[1] - (27 * gui.scale)
			self.seek_bar_position[1] = window_size[1] - gui.panelBY

			seek_bar_x = 300 * gui.scale
			if window_size[0] < 600 * gui.scale:
				seek_bar_x = 250 * gui.scale

			self.seek_bar_size[0] = window_size[0] - seek_bar_x
			self.seek_bar_position[0] = seek_bar_x

			# if gui.bb_show_art:
			#     self.seek_bar_position[0] = 300 + gui.panelBY
			#     self.seek_bar_size[0] = window_size[0] - 300 - gui.panelBY

			# self.seek_bar_position[0] = 0
			# self.seek_bar_size[0] = window_size[0]

	def render(self):

		global volume_store
		global clicked
		global right_click

		ddt.rect_a((0, window_size[1] - gui.panelBY), (window_size[0], gui.panelBY), colours.bottom_panel_colour)

		right_offset = 0
		if gui.display_time_mode >= 2:
			right_offset = 22 * gui.scale

		if window_size[0] < 670 * gui.scale:
			right_offset -= 90 * gui.scale

		# # MINI ALBUM ART
		# if gui.bb_show_art:
		#     rect = [self.seek_bar_position[0] - gui.panelBY, self.seek_bar_position[1], gui.panelBY, gui.panelBY]
		#     ddt.rect_r(rect, [255, 255, 255, 8], True)
		#     if 3 > pctl.playing_state > 0:
		#         album_art_gen.display(pctl.track_queue[pctl.queue_step], (rect[0], rect[1]), (rect[2], rect[3]))

		# ddt.rect_r(rect, [255, 255, 255, 20])

		# Volume mouse wheel control -----------------------------------------
		if mouse_wheel != 0 and mouse_position[1] > self.seek_bar_position[1] + 4 and not coll_point(
			mouse_position, self.seek_bar_position + self.seek_bar_size):

			pctl.player_volume += mouse_wheel * prefs.volume_wheel_increment
			if pctl.player_volume < 1:
				pctl.player_volume = 0
			elif pctl.player_volume > 100:
				pctl.player_volume = 100

			pctl.player_volume = int(pctl.player_volume)
			pctl.set_volume()

		# mode menu
		if right_click:
			if mouse_position[0] > 190 * gui.scale and \
					mouse_position[1] > window_size[1] - gui.panelBY and \
					mouse_position[0] < window_size[0] - 190 * gui.scale:
				mode_menu.activate()

		# Volume Bar 2 ------------------------------------------------
		if True:
			x = window_size[0] - right_offset - 120 * gui.scale
			y = window_size[1] - round(21 * gui.scale)

			if gui.compact_bar:
				x -= 90 * gui.scale

			rect = (x - 8 * gui.scale, y - 17 * gui.scale, 55 * gui.scale, 23 * gui.scale)
			# ddt.rect(rect, [255,255,255,25])
			if coll(rect) and mouse_down:
				gui.update_on_drag = True

			h_rect = (x - 6 * gui.scale, y - 17 * gui.scale, 4 * gui.scale, 23 * gui.scale)
			if coll(h_rect) and mouse_down:
				pctl.player_volume = 0

			step = round(1 * gui.scale)
			min_h = round(4 * gui.scale)
			spacing = round(5 * gui.scale)

			if right_click and coll((h_rect[0], h_rect[1], h_rect[2] + 50 * gui.scale, h_rect[3])):
				if right_click:
					if pctl.player_volume > 0:
						volume_store = pctl.player_volume
						pctl.player_volume = 0
					else:
						pctl.player_volume = volume_store

					pctl.set_volume()

			for bar in range(8):

				h = min_h + bar * step
				rect = (x, y - h, 3 * gui.scale, h)
				h_rect = (x - 1 * gui.scale, y - 17 * gui.scale, 4 * gui.scale, 23 * gui.scale)

				if coll(h_rect):
					if mouse_down:
						gui.update_on_drag = True

						if bar == 0:
							pctl.player_volume = 5
						if bar == 1:
							pctl.player_volume = 10
						if bar == 2:
							pctl.player_volume = 20
						if bar == 3:
							pctl.player_volume = 30
						if bar == 4:
							pctl.player_volume = 45
						if bar == 5:
							pctl.player_volume = 55
						if bar == 6:
							pctl.player_volume = 70
						if bar == 7:
							pctl.player_volume = 100

						pctl.set_volume()

				colour = colours.mode_button_off

				if bar == 0 and pctl.player_volume > 0:
					colour = colours.mode_button_active
				elif bar == 1 and pctl.player_volume >= 10:
					colour = colours.mode_button_active
				elif bar == 2 and pctl.player_volume >= 20:
					colour = colours.mode_button_active
				elif bar == 3 and pctl.player_volume >= 30:
					colour = colours.mode_button_active
				elif bar == 4 and pctl.player_volume >= 45:
					colour = colours.mode_button_active
				elif bar == 5 and pctl.player_volume >= 55:
					colour = colours.mode_button_active
				elif bar == 6 and pctl.player_volume >= 70:
					colour = colours.mode_button_active
				elif bar == 7 and pctl.player_volume >= 95:
					colour = colours.mode_button_active

				ddt.rect(rect, colour)
				x += spacing

		# TIME----------------------

		x = window_size[0] - 57 * gui.scale
		y = window_size[1] - 35 * gui.scale

		r_start = x - 10 * gui.scale
		if gui.display_time_mode in (2, 3):
			r_start -= 20 * gui.scale
		rect = (r_start, y - 3 * gui.scale, 80 * gui.scale, 27 * gui.scale)
		# ddt.rect_r(rect, [255, 0, 0, 40], True)
		if inp.mouse_click and coll(rect):
			gui.display_time_mode += 1
			if gui.display_time_mode > 3:
				gui.display_time_mode = 0

		if gui.display_time_mode == 0:
			text_time = get_display_time(pctl.playing_time)
			ddt.text((x + 1 * gui.scale, y), text_time, colours.time_playing, fonts.bottom_panel_time)
		elif gui.display_time_mode == 1:
			if pctl.playing_state == 0:
				text_time = get_display_time(0)
			else:
				text_time = get_display_time(pctl.playing_length - pctl.playing_time)
			ddt.text((x + 1 * gui.scale, y), text_time, colours.time_playing, fonts.bottom_panel_time)
			ddt.text((x - 5 * gui.scale, y), "-", colours.time_playing, fonts.bottom_panel_time)
		elif gui.display_time_mode == 2:

			colours.time_sub = alpha_blend([255, 255, 255, 80], colours.bottom_panel_colour)

			x -= 4
			text_time = get_display_time(pctl.playing_time)
			ddt.text((x - 25 * gui.scale, y), text_time, colours.time_playing, fonts.bottom_panel_time)

			offset1 = 10 * gui.scale

			if system == "Windows":
				offset1 += 2 * gui.scale

			offset2 = offset1 + 7 * gui.scale

			ddt.text((x + offset1, y), "/", colours.time_sub, fonts.bottom_panel_time)
			text_time = get_display_time(pctl.playing_length)
			if pctl.playing_state == 0:
				text_time = get_display_time(0)
			elif pctl.playing_state == 3:
				text_time = "-- : --"
			ddt.text((x + offset2, y), text_time, colours.time_sub, fonts.bottom_panel_time)

		elif gui.display_time_mode == 3:

			colours.time_sub = alpha_blend([255, 255, 255, 80], colours.bottom_panel_colour)

			track = pctl.playing_object()
			if track and track.index != gui.dtm3_index:

				gui.dtm3_cum = 0
				gui.dtm3_total = 0
				run = True
				collected = []
				for item in default_playlist:
					if pctl.master_library[item].parent_folder_path == track.parent_folder_path:
						if item not in collected:
							collected.append(item)
							gui.dtm3_total += pctl.master_library[item].length
							if item == track.index:
								run = False
							if run:
								gui.dtm3_cum += pctl.master_library[item].length
				gui.dtm3_index = track.index

			x -= 4
			text_time = get_display_time(gui.dtm3_cum + pctl.playing_time)

			ddt.text((x - 25 * gui.scale, y), text_time, colours.time_playing, fonts.bottom_panel_time)

			offset1 = 10 * gui.scale
			if system == "Windows":
				offset1 += 2 * gui.scale
			offset2 = offset1 + 7 * gui.scale

			ddt.text((x + offset1, y), "/", colours.time_sub, fonts.bottom_panel_time)
			text_time = get_display_time(gui.dtm3_total)
			if pctl.playing_state == 0:
				text_time = get_display_time(0)
			elif pctl.playing_state == 3:
				text_time = "-- : --"
			ddt.text((x + offset2, y), text_time, colours.time_sub, fonts.bottom_panel_time)

		# BUTTONS
		# bottom buttons

		if gui.mode == 1:

			# PLAY---
			buttons_x_offset = 0
			compact = False
			if window_size[0] < 650 * gui.scale:
				compact = True

			play_colour = colours.media_buttons_off
			pause_colour = colours.media_buttons_off
			stop_colour = colours.media_buttons_off
			forward_colour = colours.media_buttons_off
			back_colour = colours.media_buttons_off

			if pctl.playing_state == 1:
				play_colour = colours.media_buttons_active

			if pctl.auto_stop:
				stop_colour = colours.media_buttons_active

			if pctl.playing_state == 2:
				pause_colour = colours.media_buttons_active
				play_colour = colours.media_buttons_active
			elif pctl.playing_state == 3:
				play_colour = colours.media_buttons_active
				if pctl.record_stream:
					play_colour = [220, 50, 50, 255]

			if not compact or (compact and pctl.playing_state != 2):
				rect = (
				buttons_x_offset + (10 * gui.scale), window_size[1] - self.control_line_bottom - (13 * gui.scale),
				50 * gui.scale, 40 * gui.scale)
				fields.add(rect)
				if coll(rect):
					play_colour = colours.media_buttons_over
					if inp.mouse_click:
						if compact and pctl.playing_state == 1:
							pctl.pause()
						elif pctl.playing_state == 1:
							pctl.show_current(highlight=True)
						else:
							pctl.play()
						inp.mouse_click = False
					tool_tip2.test(33 * gui.scale, y - 35 * gui.scale, _("Play, RC: Go to playing"))

					if right_click:
						pctl.show_current(highlight=True)

				self.play_button.render(29 * gui.scale, window_size[1] - self.control_line_bottom, play_colour)
				# ddt.rect_r(rect,[255,0,0,255], True)

			# PAUSE---
			if compact:
				buttons_x_offset = -46 * gui.scale

			x = (75 * gui.scale) + buttons_x_offset
			y = window_size[1] - self.control_line_bottom

			if not compact or (compact and pctl.playing_state == 2):

				rect = (x - 15 * gui.scale, y - 13 * gui.scale, 50 * gui.scale, 40 * gui.scale)
				fields.add(rect)
				if coll(rect) and pctl.playing_state != 3:
					pause_colour = colours.media_buttons_over
					if inp.mouse_click:
						pctl.pause()
					if right_click:
						pctl.show_current(highlight=True)
					tool_tip2.test(x, y - 35 * gui.scale, _("Pause"))

				# ddt.rect_r(rect,[255,0,0,255], True)
				ddt.rect_a((x, y + 0), (4 * gui.scale, 13 * gui.scale), pause_colour)
				ddt.rect_a((x + 10 * gui.scale, y + 0), (4 * gui.scale, 13 * gui.scale), pause_colour)

			# FORWARD---
			rect = (buttons_x_offset + 125 * gui.scale, window_size[1] - self.control_line_bottom - 10 * gui.scale,
					50 * gui.scale, 35 * gui.scale)
			fields.add(rect)
			if coll(rect) and pctl.playing_state != 3:
				forward_colour = colours.media_buttons_over
				if inp.mouse_click:
					pctl.advance()
					gui.tool_tip_lock_off_f = True
				if right_click:
					# pctl.random_mode ^= True
					toggle_random()
					gui.tool_tip_lock_off_f = True
					# if window_size[0] < 600 * gui.scale:
					# . Shuffle set to on
					gui.mode_toast_text = _("Shuffle On")
					if not pctl.random_mode:
						# . Shuffle set to off
						gui.mode_toast_text = _("Shuffle Off")
					toast_mode_timer.set()
					gui.delay_frame(1)
				if middle_click:
					pctl.advance(rr=True)
					gui.tool_tip_lock_off_f = True
				# tool_tip.test(buttons_x_offset + 230 * gui.scale + 50 * gui.scale, window_size[1] - self.control_line_bottom - 20 * gui.scale, "Advance")
				# if not gui.tool_tip_lock_off_f:
				#     tool_tip2.test(x + 45 * gui.scale, y - 35 * gui.scale, _("Forward, RC: Toggle shuffle, MC: Radio random"))
			else:
				gui.tool_tip_lock_off_f = False

			self.forward_button.render(
				buttons_x_offset + 125 * gui.scale,
				1 + window_size[1] - self.control_line_bottom, forward_colour)

class MiniMode:
	def __init__(self):
		self.save_position = None
		self.was_borderless = True
		self.volume_timer = Timer()
		self.volume_timer.force_set(100)

		self.left_slide = asset_loader(scaled_asset_directory, loaded_asset_dc, "left-slide.png", True)
		self.right_slide = asset_loader(scaled_asset_directory, loaded_asset_dc, "right-slide.png", True)
		self.repeat = asset_loader(scaled_asset_directory, loaded_asset_dc, "repeat-mini-mode.png", True)
		self.shuffle = asset_loader(scaled_asset_directory, loaded_asset_dc, "shuffle-mini-mode.png", True)

		self.shuffle_fade_timer = Timer(100)
		self.repeat_fade_timer = Timer(100)

	def render(self):
		# We only set seek_r and seek_w if track is currently on, but use it anyway later, so make sure it exists
		if 'seek_r' not in locals():
			seek_r = [0, 0, 0, 0]
			seek_w = 0

		w = window_size[0]
		h = window_size[1]

		y1 = w
		if w == h:
			y1 -= 79 * gui.scale

		h1 = h - y1

		# Draw background
		bg = colours.mini_mode_background
		# bg = [250, 250, 250, 255]

		ddt.rect((0, 0, w, h), bg)
		ddt.text_background_colour = bg

		detect_mouse_rect = (3, 3, w - 6, h - 6)
		fields.add(detect_mouse_rect)
		mouse_in = coll(detect_mouse_rect)

		# Play / Pause when right clicking below art
		if right_click:  # and mouse_position[1] > y1:
			pctl.play_pause()

		# Volume change on scroll
		if mouse_wheel != 0:
			self.volume_timer.set()

			pctl.player_volume += mouse_wheel * prefs.volume_wheel_increment * 3
			if pctl.player_volume < 1:
				pctl.player_volume = 0
			elif pctl.player_volume > 100:
				pctl.player_volume = 100

			pctl.player_volume = int(pctl.player_volume)
			pctl.set_volume()

		track = pctl.playing_object()

		control_hit_area = (3, y1 - 15 * gui.scale, w - 6, h1 - 3 + 15 * gui.scale)
		mouse_in_area = coll(control_hit_area)
		fields.add(control_hit_area)

		ddt.rect((0, 0, w, w), (0, 0, 0, 45))
		if track is not None:

			# Render album art
			album_art_gen.display(track, (0, 0), (w, w))

			line1c = colours.mini_mode_text_1
			line2c = colours.mini_mode_text_2

			if h == w and mouse_in_area:
				# ddt.pretty_rect = (0, 260 * gui.scale, w, 100 * gui.scale)
				ddt.rect((0, y1, w, h1), [0, 0, 0, 220])
				line1c = [255, 255, 255, 240]
				line2c = [255, 255, 255, 77]

			# Double click bottom text to return to full window
			text_hit_area = (60 * gui.scale, y1 + 4, 230 * gui.scale, 50 * gui.scale)

			if coll(text_hit_area):
				if inp.mouse_click:
					if d_click_timer.get() < 0.3:
						restore_full_mode()
						gui.update += 1
						return
					d_click_timer.set()

			# Draw title texts
			line1 = track.artist
			line2 = track.title

			# Calculate seek bar position
			seek_w = int(w * 0.70)

			seek_r = [(w - seek_w) // 2, y1 + 58 * gui.scale, seek_w, 6 * gui.scale]
			seek_r_hit = [seek_r[0], seek_r[1] - 4 * gui.scale, seek_r[2], seek_r[3] + 8 * gui.scale]

			if w != h or mouse_in_area:

				if not line1 and not line2:
					ddt.text((w // 2, y1 + 18 * gui.scale, 2), track.filename, line1c, 214, window_size[0] - 30 * gui.scale)
				else:

					ddt.text((w // 2, y1 + 10 * gui.scale, 2), line1, line2c, 514, window_size[0] - 30 * gui.scale)

					ddt.text((w // 2, y1 + 31 * gui.scale, 2), line2, line1c, 414, window_size[0] - 30 * gui.scale)

				# Test click to seek
				if mouse_up and coll(seek_r_hit):

					click_x = mouse_position[0]
					click_x = min(click_x, seek_r[0] + seek_r[2])
					click_x = max(click_x, seek_r[0])
					click_x -= seek_r[0]

					if click_x < 6 * gui.scale:
						click_x = 0
					seek = click_x / seek_r[2]

					pctl.seek_decimal(seek)

				# Draw progress bar background
				ddt.rect(seek_r, [255, 255, 255, 32])

				# Calculate and draw bar foreground
				progress_w = 0
				if pctl.playing_length > 1:
					progress_w = pctl.playing_time * seek_w / pctl.playing_length
				seek_colour = [210, 210, 210, 255]
				if gui.theme_name == "Carbon":
					seek_colour = colours.bottom_panel_colour

				if pctl.playing_state != 1:
					seek_colour = [210, 40, 100, 255]

				seek_r[2] = progress_w

				if self.volume_timer.get() < 0.9:
					progress_w = pctl.player_volume * (seek_w - (4 * gui.scale)) / 100
					gui.update += 1
					seek_colour = [210, 210, 210, 255]
					seek_r[2] = progress_w
					seek_r[0] += 2 * gui.scale
					seek_r[1] += 2 * gui.scale
					seek_r[3] -= 4 * gui.scale

				ddt.rect(seek_r, seek_colour)

		left_area = (1, y1, seek_r[0] - 1, 45 * gui.scale)
		right_area = (seek_r[0] + seek_w, y1, seek_r[0] - 2, 45 * gui.scale)

		fields.add(left_area)
		fields.add(right_area)

		hint = 0
		if coll(control_hit_area):
			hint = 30
		if coll(left_area):
			hint = 240
		if hint and not prefs.shuffle_lock:
			self.left_slide.render(16 * gui.scale, y1 + 17 * gui.scale, [255, 255, 255, hint])

		hint = 0
		if coll(control_hit_area):
			hint = 30
		if coll(right_area):
			hint = 240
		if hint:
			self.right_slide.render(window_size[0] - self.right_slide.w - 16 * gui.scale, y1 + 17 * gui.scale,
									[255, 255, 255, hint])

		# Shuffle

		shuffle_area = (seek_r[0] + seek_w, seek_r[1] - 10 * gui.scale, 50 * gui.scale, 30 * gui.scale)
		# fields.add(shuffle_area)
		# ddt.rect_r(shuffle_area, [255, 0, 0, 100], True)

		if coll(control_hit_area) and not prefs.shuffle_lock:
			colour = [255, 255, 255, 20]
			if inp.mouse_click and coll(shuffle_area):
				# pctl.random_mode ^= True
				toggle_random()
			if pctl.random_mode:
				colour = [255, 255, 255, 190]

			sx = seek_r[0] + seek_w + 12 * gui.scale
			sy = seek_r[1] - 2 * gui.scale
			self.shuffle.render(sx, sy, colour)


			# sx = seek_r[0] + seek_w + 8 * gui.scale
			# sy = seek_r[1] - 1 * gui.scale
			# ddt.rect_a((sx, sy), (14 * gui.scale, 2 * gui.scale), colour)
			# sy += 4 * gui.scale
			# ddt.rect_a((sx, sy), (28 * gui.scale, 2 * gui.scale), colour)

		shuffle_area = (seek_r[0] - 41 * gui.scale, seek_r[1] - 10 * gui.scale, 40 * gui.scale, 30 * gui.scale)
		if coll(control_hit_area) and not prefs.shuffle_lock:
			colour = [255, 255, 255, 20]
			if inp.mouse_click and coll(shuffle_area):
				toggle_repeat()
			if pctl.repeat_mode:
				colour = [255, 255, 255, 190]


			sx = seek_r[0] - 36 * gui.scale
			sy = seek_r[1] - 1 * gui.scale
			self.repeat.render(sx, sy, colour)


			# sx = seek_r[0] - 39 * gui.scale
			# sy = seek_r[1] - 1 * gui.scale

			#tw = 2 * gui.scale
			# ddt.rect_a((sx + 15 * gui.scale, sy), (13 * gui.scale, tw), colour)
			# ddt.rect_a((sx + 4 * gui.scale, sy + 4 * gui.scale), (25 * gui.scale, tw), colour)
			# ddt.rect_a((sx + 30 * gui.scale - tw, sy), (tw, 6 * gui.scale), colour)


		# Forward and back clicking
		if inp.mouse_click:
			if coll(left_area) and not prefs.shuffle_lock:
				pctl.back()
			if coll(right_area):
				pctl.advance()

		# Show exit/min buttons when mosue over
		tool_rect = [window_size[0] - 110 * gui.scale, 2, 108 * gui.scale, 45 * gui.scale]
		if prefs.left_window_control:
			tool_rect[0] = 0
		fields.add(tool_rect)
		if coll(tool_rect):
			draw_window_tools()

		if w != h:
			ddt.rect_s((1, 1, w - 2, h - 2), colours.mini_mode_border, 1 * gui.scale)
			if gui.scale == 2:
				ddt.rect_s((2, 2, w - 4, h - 4), colours.mini_mode_border, 1 * gui.scale)

class MiniMode2:

	def __init__(self):

		self.save_position = None
		self.was_borderless = True
		self.volume_timer = Timer()
		self.volume_timer.force_set(100)

		self.left_slide = asset_loader(scaled_asset_directory, loaded_asset_dc, "left-slide.png", True)
		self.right_slide = asset_loader(scaled_asset_directory, loaded_asset_dc, "right-slide.png", True)

	def render(self):

		w = window_size[0]
		h = window_size[1]

		x1 = h

		# Draw background
		ddt.rect((0, 0, w, h), colours.mini_mode_background)
		ddt.text_background_colour = colours.mini_mode_background

		detect_mouse_rect = (2, 2, w - 4, h - 4)
		fields.add(detect_mouse_rect)
		mouse_in = coll(detect_mouse_rect)

		# Play / Pause when right clicking below art
		if right_click:  # and mouse_position[1] > y1:
			pctl.play_pause()

		# Volume change on scroll
		if mouse_wheel != 0:
			self.volume_timer.set()

			pctl.player_volume += mouse_wheel * prefs.volume_wheel_increment * 3
			if pctl.player_volume < 1:
				pctl.player_volume = 0
			elif pctl.player_volume > 100:
				pctl.player_volume = 100

			pctl.player_volume = int(pctl.player_volume)
			pctl.set_volume()

		track = pctl.playing_object()

		if track is not None:

			# Render album art
			album_art_gen.display(track, (0, 0), (h, h))

			text_hit_area = (x1, 0, w, h)

			if coll(text_hit_area):
				if inp.mouse_click:
					if d_click_timer.get() < 0.3:
						restore_full_mode()
						gui.update += 1
						return
					d_click_timer.set()

			# Draw title texts
			line1 = track.artist
			line2 = track.title

			if not line1 and not line2:

				ddt.text(
					(x1 + 15 * gui.scale, 44 * gui.scale), track.filename, colours.grey(150), 315,
					window_size[0] - x1 - 30 * gui.scale)
			else:

				# if ddt.get_text_w(line2, 215) > window_size[0] - x1 - 30 * gui.scale:
				#     ddt.text((x1 + 15 * gui.scale, 19 * gui.scale), line2, colours.grey(249), 413,
				#              window_size[0] - x1 - 35 * gui.scale)
				#
				#     ddt.text((x1 + 15 * gui.scale, 43 * gui.scale), line1, colours.grey(110), 513,
				#              window_size[0] - x1 - 35 * gui.scale)
				# else:

				ddt.text(
					(x1 + 15 * gui.scale, 18 * gui.scale), line2, colours.grey(249), 514,
					window_size[0] - x1 - 30 * gui.scale)

				ddt.text(
					(x1 + 15 * gui.scale, 43 * gui.scale), line1, colours.grey(110), 514,
					window_size[0] - x1 - 30 * gui.scale)

		# Show exit/min buttons when mosue over
		tool_rect = [window_size[0] - 110 * gui.scale, 2, 108 * gui.scale, 45 * gui.scale]
		if prefs.left_window_control:
			tool_rect[0] = 0
		fields.add(tool_rect)
		if coll(tool_rect):
			draw_window_tools()

		# Seek bar
		bg_rect = (h, h - round(5 * gui.scale), w - h, round(5 * gui.scale))
		ddt.rect(bg_rect, [255, 255, 255, 18])

		if pctl.playing_state > 0:

			hit_rect = h - 5 * gui.scale, h - 12 * gui.scale, w - h + 5 * gui.scale, 13 * gui.scale

			if coll(hit_rect) and mouse_up:
				p = (mouse_position[0] - h) / (w - h)

				if p < 0 or mouse_position[0] - h < 6 * gui.scale:
					pctl.seek_time(0)
				elif p > .96:
					pctl.advance()
				else:
					pctl.seek_decimal(p)

			if pctl.playing_length:
				seek_rect = (
					h, h - round(5 * gui.scale), round((w - h) * (pctl.playing_time / pctl.playing_length)),
					round(5 * gui.scale))
				colour = colours.artist_text
				if gui.theme_name == "Carbon":
					colour = colours.bottom_panel_colour
				if pctl.playing_state != 1:
					colour = [210, 40, 100, 255]
				ddt.rect(seek_rect, colour)

class MiniMode3:

	def __init__(self):

		self.save_position = None
		self.was_borderless = True
		self.volume_timer = Timer()
		self.volume_timer.force_set(100)

		self.left_slide = asset_loader(scaled_asset_directory, loaded_asset_dc, "left-slide.png", True)
		self.right_slide = asset_loader(scaled_asset_directory, loaded_asset_dc, "right-slide.png", True)

		self.shuffle_fade_timer = Timer(100)
		self.repeat_fade_timer = Timer(100)

	def render(self):
		# We only set seek_r and seek_w if track is currently on, but use it anyway later, so make sure it exists
		if 'seek_r' not in locals():
			seek_r = [0, 0, 0, 0]
			seek_w = 0
			volume_r = [0, 0, 0, 0]
			volume_w = 0

		w = window_size[0]
		h = window_size[1]

		y1 = w #+ 10 * gui.scale
		# if w == h:
		#     y1 -= 79 * gui.scale

		h1 = h - y1

		# Draw background
		bg = colours.mini_mode_background
		bg = [0, 0, 0, 0]
		# bg = [250, 250, 250, 255]

		ddt.rect((0, 0, w, h), bg)

		style_overlay.display()

		transit = False
		#ddt.text_background_colour = list(gui.center_blur_pixel) + [255,] #bg
		if style_overlay.fade_on_timer.get() < 0.4 or style_overlay.stage != 2:
			ddt.alpha_bg = True
			transit = True

		detect_mouse_rect = (3, 3, w - 6, h - 6)
		fields.add(detect_mouse_rect)
		mouse_in = coll(detect_mouse_rect)

		# Play / Pause when right clicking below art
		if right_click:  # and mouse_position[1] > y1:
			pctl.play_pause()

		# Volume change on scroll
		if mouse_wheel != 0:
			self.volume_timer.set()

			pctl.player_volume += mouse_wheel * prefs.volume_wheel_increment * 3
			if pctl.player_volume < 1:
				pctl.player_volume = 0
			elif pctl.player_volume > 100:
				pctl.player_volume = 100

			pctl.player_volume = int(pctl.player_volume)
			pctl.set_volume()

		track = pctl.playing_object()

		control_hit_area = (3, y1 - 15 * gui.scale, w - 6, h1 - 3 + 15 * gui.scale)
		mouse_in_area = coll(control_hit_area)
		fields.add(control_hit_area)

		#ddt.rect((0, 0, w, w), (0, 0, 0, 45))
		if track is not None:

			# Render album art

			wid = (w // 2) + round(60 * gui.scale)
			ins = (window_size[0] - wid) / 2
			off = round(4 * gui.scale)

			drop_shadow.render(ins + off, ins + off, wid + off * 2, wid + off * 2)
			ddt.rect((ins, ins, wid, wid), [20, 20, 20, 255])
			album_art_gen.display(track, (ins, ins), (wid, wid))

			line1c = [255, 255, 255, 255] #colours.mini_mode_text_1
			line2c = [255, 255, 255, 255] #colours.mini_mode_text_2

			# if h == w and mouse_in_area:
			#     # ddt.pretty_rect = (0, 260 * gui.scale, w, 100 * gui.scale)
			#     ddt.rect((0, y1, w, h1), [0, 0, 0, 220])
			#     line1c = [255, 255, 255, 240]
			#     line2c = [255, 255, 255, 77]

			# Double click bottom text to return to full window
			text_hit_area = (60 * gui.scale, y1 + 4, 230 * gui.scale, 50 * gui.scale)

			if coll(text_hit_area):
				if inp.mouse_click:
					if d_click_timer.get() < 0.3:
						restore_full_mode()
						gui.update += 1
						return
					d_click_timer.set()

			# Draw title texts
			line1 = track.artist
			line2 = track.title
			key = None
			if not line1 and not line2:
				if not ddt.alpha_bg:
					key = (track.filename, 214, style_overlay.current_track_id)
				ddt.text(
					(w // 2, y1 + 18 * gui.scale, 2), track.filename, line1c, 214,
					window_size[0] - 30 * gui.scale, real_bg=not transit, key=key)
			else:

				if not ddt.alpha_bg:
					key = (line1, 515, style_overlay.current_track_id)
				ddt.text(
					(w // 2, y1 + 5 * gui.scale, 2), line1, line2c, 515,
					window_size[0] - 30 * gui.scale, real_bg=not transit, key=key)
				if not ddt.alpha_bg:
					key = (line2, 415, style_overlay.current_track_id)
				ddt.text(
					(w // 2, y1 + 31 * gui.scale, 2), line2, line1c, 415,
					window_size[0] - 30 * gui.scale, real_bg=not transit, key=key)

			y1 += round(10 * gui.scale)

			# Calculate seek bar position
			seek_w = int(w * 0.80)

			seek_r = [(w - seek_w) // 2, y1 + 58 * gui.scale, seek_w, 9 * gui.scale]
			seek_r_hit = [seek_r[0], seek_r[1] - 5 * gui.scale, seek_r[2], seek_r[3] + 12 * gui.scale]

			if w != h or mouse_in_area:


				# Test click to seek
				if mouse_up and coll(seek_r_hit):

					click_x = mouse_position[0]
					click_x = min(click_x, seek_r[0] + seek_r[2])
					click_x = max(click_x, seek_r[0])
					click_x -= seek_r[0]

					if click_x < 6 * gui.scale:
						click_x = 0
					seek = click_x / seek_r[2]

					pctl.seek_decimal(seek)

				# Draw progress bar background
				ddt.rect(seek_r, [255, 255, 255, 32])

				# Calculate and draw bar foreground
				progress_w = 0
				if pctl.playing_length > 1:
					progress_w = pctl.playing_time * seek_w / pctl.playing_length
				seek_colour = [210, 210, 210, 255]
				if gui.theme_name == "Carbon":
					seek_colour = colours.bottom_panel_colour

				if pctl.playing_state != 1:
					seek_colour = [210, 40, 100, 255]

				seek_r[2] = progress_w

			ddt.rect(seek_r, seek_colour)



			volume_w = int(w * 0.50)
			volume_r = [(w - volume_w) // 2, y1 + 80 * gui.scale, volume_w, 6 * gui.scale]
			volume_r_hit = [volume_r[0], volume_r[1] - 5 * gui.scale, volume_r[2], volume_r[3] + 10 * gui.scale]

			# Test click to volume
			if (mouse_up or mouse_down) and coll(volume_r_hit):
				gui.update_on_drag = True
				click_x = mouse_position[0]
				click_x = min(click_x, volume_r[0] + volume_r[2])
				click_x = max(click_x, volume_r[0])
				click_x -= volume_r[0]

				if click_x < 6 * gui.scale:
					click_x = 0
				volume = click_x / volume_r[2]

				pctl.player_volume = int(volume * 100)
				pctl.set_volume()

			ddt.rect(volume_r, [255, 255, 255, 32])

			#if self.volume_timer.get() < 0.9:
			progress_w = pctl.player_volume * (volume_w - (4 * gui.scale)) / 100
			volume_colour = [210, 210, 210, 255]
			volume_r[2] = progress_w
			volume_r[0] += 2 * gui.scale
			volume_r[1] += 2 * gui.scale
			volume_r[3] -= 4 * gui.scale

			ddt.rect(volume_r, volume_colour)


		left_area = (1, y1, volume_r[0] - 1, 45 * gui.scale)
		right_area = (volume_r[0] + volume_w, y1, volume_r[0] - 2, 45 * gui.scale)

		fields.add(left_area)
		fields.add(right_area)

		hint = 0
		if True: #coll(control_hit_area):
			hint = 30
		if coll(left_area):
			hint = 240
		if hint and not prefs.shuffle_lock:
			self.left_slide.render(16 * gui.scale, y1 + 10 * gui.scale, [255, 255, 255, hint])

		hint = 0
		if True: #coll(control_hit_area):
			hint = 30
		if coll(right_area):
			hint = 240
		if hint:
			self.right_slide.render(
				window_size[0] - self.right_slide.w - 16 * gui.scale, y1 + 10 * gui.scale, [255, 255, 255, hint])

		# Shuffle
		shuffle_area = (volume_r[0] + volume_w, volume_r[1] - 10 * gui.scale, 50 * gui.scale, 30 * gui.scale)
		# fields.add(shuffle_area)
		# ddt.rect_r(shuffle_area, [255, 0, 0, 100], True)

		if True: #coll(control_hit_area) and not prefs.shuffle_lock:
			colour = [255, 255, 255, 20]
			if inp.mouse_click and coll(shuffle_area):
				# pctl.random_mode ^= True
				toggle_random()
			if pctl.random_mode:
				colour = [255, 255, 255, 190]

			sx = volume_r[0] + volume_w + 12 * gui.scale
			sy = volume_r[1] - 3 * gui.scale
			mini_mode.shuffle.render(sx, sy, colour)

			#
			# sx = volume_r[0] + volume_w + 8 * gui.scale
			# sy = volume_r[1] - 1 * gui.scale
			# ddt.rect_a((sx, sy), (14 * gui.scale, 2 * gui.scale), colour)
			# sy += 4 * gui.scale
			# ddt.rect_a((sx, sy), (28 * gui.scale, 2 * gui.scale), colour)

		shuffle_area = (volume_r[0] - 41 * gui.scale, volume_r[1] - 10 * gui.scale, 40 * gui.scale, 30 * gui.scale)
		if True: #coll(control_hit_area) and not prefs.shuffle_lock:
			colour = [255, 255, 255, 20]
			if inp.mouse_click and coll(shuffle_area):
				toggle_repeat()
			if pctl.repeat_mode:
				colour = [255, 255, 255, 190]

			sx = volume_r[0] - 39 * gui.scale
			sy = volume_r[1] - 1 * gui.scale
			mini_mode.repeat.render(sx, sy, colour)

			# sx = volume_r[0] - 39 * gui.scale
			# sy = volume_r[1] - 1 * gui.scale
			#
			# tw = 2 * gui.scale
			# ddt.rect_a((sx + 15 * gui.scale, sy), (13 * gui.scale, tw), colour)
			# ddt.rect_a((sx + 4 * gui.scale, sy + 4 * gui.scale), (25 * gui.scale, tw), colour)
			# ddt.rect_a((sx + 30 * gui.scale - tw, sy), (tw, 6 * gui.scale), colour)

		# Forward and back clicking
		if inp.mouse_click:
			if coll(left_area) and not prefs.shuffle_lock:
				pctl.back()
			if coll(right_area):
				pctl.advance()

		search_over.render()


		# Show exit/min buttons when mosue over
		tool_rect = [window_size[0] - 110 * gui.scale, 2, 108 * gui.scale, 45 * gui.scale]
		if prefs.left_window_control:
			tool_rect[0] = 0
		fields.add(tool_rect)
		if coll(tool_rect):
			draw_window_tools()


		# if w != h:
		#     ddt.rect_s((1, 1, w - 2, h - 2), colours.mini_mode_border, 1 * gui.scale)
		#     if gui.scale == 2:
		#         ddt.rect_s((2, 2, w - 4, h - 4), colours.mini_mode_border, 1 * gui.scale)
		ddt.alpha_bg = False

class StandardPlaylist:
	def __init__(self):
		pass

	def full_render(self):

		global highlight_left
		global highlight_right

		global playlist_hold
		global playlist_hold_position
		global shift_selection

		global click_time
		global quick_drag
		global mouse_down
		global mouse_up
		global selection_stage

		global r_menu_index
		global r_menu_position

		left = gui.playlist_left
		width = gui.plw

		highlight_width = gui.tracklist_highlight_width
		highlight_left = gui.tracklist_highlight_left
		inset_width = gui.tracklist_inset_width
		inset_left = gui.tracklist_inset_left
		center_mode = gui.tracklist_center_mode

		w = 0
		gui.row_extra = 0
		cv = 0  # update gui.playlist_current_visible_tracks

		# Draw the background
		SDL_SetRenderTarget(renderer, gui.tracklist_texture)
		SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
		SDL_RenderClear(renderer)

		rect = (left, gui.panelY, width, window_size[1])
		ddt.rect(rect, colours.playlist_panel_background)

		# This draws an optional background image
		if pl_bg:
			x = (left + highlight_width) - (pl_bg.w + round(60 * gui.scale))
			pl_bg.render(x, window_size[1] - gui.panelBY - pl_bg.h)
			ddt.pretty_rect = (x, window_size[1] - gui.panelBY - pl_bg.h, pl_bg.w, pl_bg.h)
			ddt.alpha_bg = True
		else:
			xx = left + inset_left + inset_width
			if center_mode:
				xx -= round(15 * gui.scale)
			deco.draw(ddt, xx, window_size[1] - gui.panelBY, pretty_text=True)

		# Mouse wheel scrolling
		if mouse_wheel != 0 and window_size[1] - gui.panelBY - 1 > mouse_position[
			1] > gui.panelY - 2 and gui.playlist_left < mouse_position[0] < gui.playlist_left + gui.plw \
				and not (coll(pl_rect)) and not search_over.active and not radiobox.active:

			# Set scroll speed
			mx = 4

			if gui.playlist_view_length < 25:
				mx = 3
			if gui.playlist_view_length < 10:
				mx = 2
			pctl.playlist_view_position -= mouse_wheel * mx

			if gui.playlist_view_length > 40:
				pctl.playlist_view_position -= mouse_wheel

			#if mouse_wheel:
				#logging.debug("Position changed by mouse wheel scroll: " + str(mouse_wheel))

			pctl.playlist_view_position = min(pctl.playlist_view_position, len(default_playlist))
				#logging.debug("Position changed by range bound")
			if pctl.playlist_view_position < 1:
				pctl.playlist_view_position = 0
				if default_playlist:
					# edge_playlist.pulse()
					edge_playlist2.pulse()

			scroll_hide_timer.set()
			gui.frame_callback_list.append(TestTimer(0.9))

		# Show notice if playlist empty
		if len(default_playlist) == 0:
			colour = alpha_mod(colours.index_text, 200)  # colours.playlist_text_missing

			top_a = gui.panelY
			if gui.artist_info_panel:
				top_a += gui.artist_panel_height

			b = window_size[1] - top_a - gui.panelBY
			half = int(top_a + (b * 0.60))

			if pl_bg:
				rect = (left + int(width / 2) - 80 * gui.scale, half - 10 * gui.scale,
						190 * gui.scale, 60 * gui.scale)
				ddt.pretty_rect = rect
				ddt.alpha_bg = True

			ddt.text(
				(left + int(width / 2) + 10 * gui.scale, half, 2),
				_("Playlist is empty"), colour, 213, bg=colours.playlist_panel_background)
			ddt.text(
				(left + int(width / 2) + 10 * gui.scale, half + 30 * gui.scale, 2),
				_("Drag and drop files to import"), colour, 13, bg=colours.playlist_panel_background)

			ddt.pretty_rect = None
			ddt.alpha_bg = False

		# Show notice if at end of playlist
		elif pctl.playlist_view_position > len(default_playlist) - 1:
			colour = alpha_mod(colours.index_text, 200)

			top_a = gui.panelY
			if gui.artist_info_panel:
				top_a += gui.artist_panel_height

			b = window_size[1] - top_a - gui.panelBY
			half = int(top_a + (b * 0.17))

			if pl_bg:
				rect = (left + int(width / 2) - 60 * gui.scale, half - 5 * gui.scale,
						140 * gui.scale, 30 * gui.scale)
				ddt.pretty_rect = rect
				ddt.alpha_bg = True

			ddt.text(
				(left + int(width / 2) + 10 * gui.scale, half, 2), _("End of Playlist"),
				colour, 213)

			ddt.pretty_rect = None
			ddt.alpha_bg = False

			# line = "Contains " + str(len(default_playlist)) + ' track'
			# if len(default_playlist) > 1:
			#     line += "s"
			#
			# ddt.draw_text((left + int(width / 2) + 10 * gui.scale, half + 24 * gui.scale, 2), line,
			#           colour, 12)

		# Process Input

		# type (0 is track, 1 is fold title), track_position, track_object, box, input_box,
		list_items = []
		number = 0

		for i in range(gui.playlist_view_length + 1):

			track_position = i + pctl.playlist_view_position

			# Make sure the view position is valid
			pctl.playlist_view_position = max(pctl.playlist_view_position, 0)

			# Break if we are at end of playlist
			if len(default_playlist) <= track_position or number > gui.playlist_view_length:
				break

			track_object = pctl.get_track(default_playlist[track_position])
			track_id = track_object.index
			move_on_title = False

			line_y = gui.playlist_top + gui.playlist_row_height * number

			track_box = (
				left + highlight_left, line_y, highlight_width,
				gui.playlist_row_height - 1)

			input_box = (track_box[0] + 30 * gui.scale, track_box[1] + 1, track_box[2] - 36 * gui.scale, track_box[3])

			# Are folder titles enabled?
			if not pctl.multi_playlist[pctl.active_playlist_viewing].hide_title and break_enable:
				# Is this track from a different folder than the last?
				if track_position == 0 or track_object.parent_folder_path != pctl.get_track(
						default_playlist[track_position - 1]).parent_folder_path:
					# Make folder title

					highlight = False
					drag_highlight = False

					# Shift selection highlight
					if (track_position in shift_selection and len(shift_selection) > 1):
						highlight = True

					# Tracks have been dropped?
					if playlist_hold is True and coll(input_box):
						if mouse_up:
							move_on_title = True

					# Ignore click in ratings box
					click_title = (inp.mouse_click or right_click or middle_click) and coll(input_box)
					if click_title and gui.show_album_ratings:
						if mouse_position[0] > (input_box[0] + input_box[2]) - 80 * gui.scale:
							click_title = False

					# Detect folder title click
					if click_title and mouse_position[1] < window_size[1] - gui.panelBY:

						gui.pl_update += 1
						# Add folder to queue if middle click
						if middle_click and is_level_zero():
							if key_ctrl_down:  # Add as ungrouped tracks
								i = track_position
								parent = pctl.get_track(default_playlist[i]).parent_folder_path
								while i < len(default_playlist) and parent == pctl.get_track(
										default_playlist[i]).parent_folder_path:
									pctl.force_queue.append(queue_item_gen(default_playlist[i], i, pl_to_id(
										pctl.active_playlist_viewing)))
									i += 1
								queue_timer_set(plural=True)
								if prefs.stop_end_queue:
									pctl.auto_stop = False

							else:  # Add as grouped album
								add_album_to_queue(track_id, track_position)
							pctl.selected_in_playlist = track_position
							shift_selection = [pctl.selected_in_playlist]
							gui.pl_update += 1

						# Play if double click:
						if d_mouse_click and track_position in shift_selection and coll_point(
							last_click_location, (input_box)):
							click_time -= 1.5
							pctl.jump(track_id, track_position)
							line_hit = False
							inp.mouse_click = False

							if album_mode:
								goto_album(pctl.playlist_playing_position)

						# Show selection menu if right clicked after select
						if right_click:
							folder_menu.activate(track_id)
							r_menu_position = track_position
							selection_stage = 2
							gui.pl_update = 1

							if track_position not in shift_selection:
								shift_selection = []
								pctl.selected_in_playlist = track_position
								u = track_position
								while u < len(default_playlist) and track_object.parent_folder_path == \
										pctl.master_library[
											default_playlist[u]].parent_folder_path:
									shift_selection.append(u)
									u += 1

						# Add folder to selection if clicked
						if inp.mouse_click and not (
								scroll_enable and mouse_position[0] < 30 * gui.scale) and not side_drag:

							quick_drag = True
							set_drag_source()

							if not pl_is_locked(pctl.active_playlist_viewing) or key_shift_down:
								playlist_hold = True

							selection_stage = 1
							temp = get_folder_tracks_local(track_position)
							pctl.selected_in_playlist = track_position

							if len(shift_selection) > 0 and key_shift_down:
								if track_position < shift_selection[0]:
									for item in reversed(temp):
										if item not in shift_selection:
											shift_selection.insert(0, item)
								else:
									for item in temp:
										if item not in shift_selection:
											shift_selection.append(item)

							else:
								shift_selection = copy.copy(temp)

					# Should draw drag highlight?

					if mouse_down and playlist_hold and coll(input_box) and track_position not in shift_selection:

						if len(shift_selection) < 2 and not key_shift_down:
							pass
						else:
							drag_highlight = True

					# Something to do with quick search, I forgot
					if pctl.selected_in_playlist > track_position + 1:
						gui.row_extra += 1

					list_items.append(
						(1, track_position, track_object, track_box, input_box, highlight, number, drag_highlight, False))
					number += 1

			if number > gui.playlist_view_length:
				break

			# Standard track ---------------------------------------------------------------------
			playing = False

			highlight = False
			drag_highlight = False
			line_y = gui.playlist_top + gui.playlist_row_height * number

			track_box = (
				left + highlight_left, line_y, highlight_width,
				gui.playlist_row_height - 1)

			input_box = (track_box[0] + 30 * gui.scale, track_box[1] + 1, track_box[2] - 36 * gui.scale, track_box[3])

			# Test if line has mouse over or been clicked
			line_over = False
			line_hit = False
			if coll(input_box) and mouse_position[1] < window_size[1] - gui.panelBY:
				line_over = True
				if (inp.mouse_click or right_click or (middle_click and is_level_zero())):
					line_hit = True
					gui.pl_update += 1

				else:
					line_hit = False
			else:
				line_hit = False
				line_over = False

			# Prevent click if near scroll bar
			if scroll_enable and mouse_position[0] < 30:
				line_hit = False

			# Double click to play
			if key_shift_down is False and d_mouse_click and line_hit and track_position == pctl.selected_in_playlist and coll_point(
					last_click_location, input_box):

				pctl.jump(track_id, track_position)

				click_time -= 1.5
				quick_drag = False
				mouse_down = False
				mouse_up = False
				line_hit = False

				if album_mode:
					goto_album(pctl.playlist_playing_position)

			if len(pctl.track_queue) > 0 and pctl.track_queue[pctl.queue_step] == track_id:
				if track_position == pctl.playlist_playing_position and pctl.active_playlist_viewing == pctl.active_playlist_playing:
					this_line_playing = True

			# Add to queue on middle click
			if middle_click and line_hit:
				pctl.force_queue.append(
					queue_item_gen(track_id,
					track_position, pl_to_id(pctl.active_playlist_viewing)))
				pctl.selected_in_playlist = track_position
				shift_selection = [pctl.selected_in_playlist]
				gui.pl_update += 1
				queue_timer_set()
				if prefs.stop_end_queue:
					pctl.auto_stop = False

			# Deselect multiple if one clicked on and not dragged (mouse up is probably a bit of a hacky way of doing it)
			if len(shift_selection) > 1 and mouse_up and line_over and not key_shift_down and not key_ctrl_down and point_proximity_test(
					gui.drag_source_position, mouse_position, 15):  # and not playlist_hold:
				shift_selection = [track_position]
				pctl.selected_in_playlist = track_position
				gui.pl_update = 1
				gui.update = 2

			# # Begin drag block selection
			# if mouse_down and line_over and track_position in shift_selection and len(shift_selection) > 1:
			#     if not pl_is_locked(pctl.active_playlist_viewing):
			#         playlist_hold = True
			#     elif key_shift_down:
			#         playlist_hold = True

			# Begin drag single track
			if inp.mouse_click and line_hit and not side_drag:
				quick_drag = True
				set_drag_source()

			# Shift Move Selection
			if move_on_title or (mouse_up and playlist_hold is True and coll((
					left + highlight_left, line_y, highlight_width, gui.playlist_row_height))):

				if len(shift_selection) > 1 or key_shift_down:
					if track_position not in shift_selection:  # p_track != playlist_hold_position and

						if len(shift_selection) == 0:

							ref = default_playlist[playlist_hold_position]
							default_playlist[playlist_hold_position] = "old"
							if move_on_title:
								default_playlist.insert(track_position, "new")
							else:
								default_playlist.insert(track_position + 1, "new")
							default_playlist.remove("old")
							pctl.selected_in_playlist = default_playlist.index("new")
							default_playlist[default_playlist.index("new")] = ref

							gui.pl_update = 1


						else:
							ref = []
							selection_stage = 2
							for item in shift_selection:
								ref.append(default_playlist[item])

							for item in shift_selection:
								default_playlist[item] = "old"

							for item in shift_selection:
								if move_on_title:
									default_playlist.insert(track_position, "new")
								else:
									default_playlist.insert(track_position + 1, "new")

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

						reload_albums(True)
						pctl.notify_change()

			# Test show drag indicator
			if mouse_down and playlist_hold and coll(input_box) and track_position not in shift_selection:
				if len(shift_selection) > 1 or key_shift_down:
					drag_highlight = True

			# Right click menu activation
			if right_click and line_hit and mouse_position[0] > gui.playlist_left + 10:

				if len(shift_selection) > 1 and track_position in shift_selection:
					selection_menu.activate(default_playlist[track_position])
					selection_stage = 2
				else:
					r_menu_index = default_playlist[track_position]
					r_menu_position = track_position
					track_menu.activate(default_playlist[track_position])
					gui.pl_update += 1
					gui.update += 1

					if track_position not in shift_selection:
						pctl.selected_in_playlist = track_position
						shift_selection = [pctl.selected_in_playlist]

			if line_over and inp.mouse_click:

				if track_position in shift_selection:
					pass
				else:
					selection_stage = 2
					if key_shift_down:
						start_s = track_position
						end_s = pctl.selected_in_playlist
						if end_s < start_s:
							end_s, start_s = start_s, end_s
						for y in range(start_s, end_s + 1):
							if y not in shift_selection:
								shift_selection.append(y)
						shift_selection.sort()
						pctl.selected_in_playlist = track_position
					elif key_ctrl_down:
						shift_selection.append(track_position)
					else:
						pctl.selected_in_playlist = track_position
						shift_selection = [pctl.selected_in_playlist]

				if not pl_is_locked(pctl.active_playlist_viewing) or key_shift_down:
					playlist_hold = True
					playlist_hold_position = track_position

			# Activate drag if shift key down
			if quick_drag and pl_is_locked(pctl.active_playlist_viewing) and mouse_down:
				if key_shift_down:
					playlist_hold = True
				else:
					playlist_hold = False

			# Multi Select Highlight
			if track_position in shift_selection or track_position == pctl.selected_in_playlist:
				highlight = True

			if pctl.playing_state != 3 and len(pctl.track_queue) > 0 and pctl.track_queue[pctl.queue_step] == \
					default_playlist[track_position]:
				if track_position == pctl.playlist_playing_position and pctl.active_playlist_viewing == pctl.active_playlist_playing:
					playing = True

			list_items.append(
				(0, track_position, track_object, track_box, input_box, highlight, number, drag_highlight, playing))
			number += 1

			if number > gui.playlist_view_length:
				break
		# ---------------------------------------------------------------------------------------

		# For every track in view
		# for i in range(gui.playlist_view_length + 1):
		gui.tracklist_bg_is_light = test_lumi(colours.playlist_panel_background) < 0.55

		for type, track_position, tr, track_box, input_box, highlight, number, drag_highlight, playing in list_items:

			line_y = gui.playlist_top + gui.playlist_row_height * number

			ddt.text_background_colour = colours.playlist_panel_background

			if type == 1:

				# Is type ALBUM TITLE
				separator = " - "
				if prefs.row_title_separator_type == 1:
					separator = " ‒ "
				if prefs.row_title_separator_type == 2:
					separator = " ⦁ "

				date = ""
				duration = ""

				line = tr.parent_folder_name

				# Use folder name if mixed/singles?
				if len(default_playlist) > track_position + 1 and pctl.get_track(
						default_playlist[track_position + 1]).album != tr.album and \
						pctl.get_track(default_playlist[track_position + 1]).parent_folder_path == tr.parent_folder_path:
					line = tr.parent_folder_name
				else:

					if tr.album_artist != "" and tr.album != "":
						line = tr.album_artist + separator + tr.album

						if prefs.left_align_album_artist_title and not True:
							album_artist_mode = True
							line = tr.album

					if len(line) < 6 and "CD" in line:
						line = tr.album

					if prefs.append_date and year_search.search(tr.date):
						year = d_date_display2(tr)
						if not year:
							year = d_date_display(tr)
						date = "(" + year + ")"

					if line.endswith(")"):
						b = line.split("(")
						if len(b) > 1 and len(b[1]) <= 11:

							match = year_search.search(b[1])

							if match:
								line = b[0]
								date = "(" + b[1]

					elif line.startswith("("):

						b = line.split(")")
						if len(b) > 1 and len(b[0]) <= 11:

							match = year_search.search(b[0])

							if match:
								line = b[1]
								date = b[0] + ")"

					if "(" in line and year_search.search(line):
						date = ""

				line = line.replace(" - ", separator)

				qq = 0
				d_date = date
				title_line = line

				# Calculate folder duration

				q = track_position

				total_time = 0
				while q < len(default_playlist):

					if pctl.get_track(default_playlist[q]).parent_folder_path != tr.parent_folder_path:
						break

					total_time += pctl.get_track(default_playlist[q]).length

					q += 1
					qq += 1

				if qq > 1:
					duration = " [ " + get_display_time(total_time) + " ]" # Hair space inside brackets for better visual spacing

				if prefs.append_total_time:
					date += duration

				ex = left + highlight_left + highlight_width - 7 * gui.scale

				height = line_y + gui.playlist_row_height - 19 * gui.scale  # gui.pl_title_y_offset

				star_offset = 0
				if gui.show_album_ratings:
					star_offset = round(72 * gui.scale)
					ex -= star_offset
					draw_rating_widget(ex + 6 * gui.scale, height, tr, album=True)

				light_offset = 0
				if colours.lm:
					light_offset = 3 * gui.scale
				ex -= light_offset

				if qq > 1:
					ex += 1 * gui.scale

				ddt.text_background_colour = colours.playlist_panel_background

				if gui.scale == 2:
					height += 1

				if highlight:
					ddt.text_background_colour = alpha_blend(
						colours.row_select_highlight,
						colours.playlist_panel_background)
					ddt.rect_a(
						(left + highlight_left, gui.playlist_top + gui.playlist_row_height * number),
						(highlight_width, gui.playlist_row_height), colours.row_select_highlight)


				#logging.info(d_date) # date of album release / release year
				#logging.info(tr.parent_folder_name) # folder name
				#logging.info(tr.album)
				#logging.info(tr.artist)
				#logging.info(tr.album_artist)
				#logging.info(tr.genre)



				if prefs.row_title_format == 2:

					separator = " | "

					start_offset = round(15 * gui.scale)
					xx = left + highlight_left + start_offset
					ww = highlight_width

					was = False
					run = 0
					duration = get_display_time(total_time)
					colour = colours.folder_title
					colour = [colour[0], colour[1], colour[2], max(colour[3] - 50, 0)]

					if prefs.append_total_time and duration:
						was = True
						run += ddt.text(
							(ex - run, height, 1), duration, colour,
							gui.row_font_size + gui.pl_title_font_offset)
					if d_date:
						if was:
							run += ddt.text(
								(ex - run, height, 1), separator, colour,
								gui.row_font_size + gui.pl_title_font_offset)
						was = True
						run += ddt.text(
							(ex - run, height, 1), d_date.rstrip(")").lstrip("("), colour,
							gui.row_font_size + gui.pl_title_font_offset)
					if tr.genre and prefs.row_title_genre:
						if was:
							run += ddt.text(
								(ex - run, height, 1), separator, colour,
								gui.row_font_size + gui.pl_title_font_offset)
						was = True
						run += ddt.text(
							(ex - run, height, 1), tr.genre, colour,
							gui.row_font_size + gui.pl_title_font_offset)


					w2 = ddt.text((xx, height), title_line, colours.folder_title, gui.row_font_size + gui.pl_title_font_offset, max_w=ww - (start_offset + run + round(10 * gui.scale)))




				else:
					date_w = 0
					if date:
						date_w = ddt.text(
							(ex, height, 1), date, colours.folder_title,
							gui.row_font_size + gui.pl_title_font_offset)
						date_w += 4 * gui.scale
						if qq > 1:
							date_w -= 1 * gui.scale

					aa = 0

					ft_width = ddt.get_text_w(line, gui.row_font_size + gui.pl_title_font_offset)

					left_align = highlight_width - date_w - 13 * gui.scale - light_offset

					left_align -= star_offset

					extra = aa

					left_align -= extra

					if ft_width > left_align:
						date_w += 19 * gui.scale
						ddt.text(
							(left + highlight_left + 8 * gui.scale + extra, height), line,
							colours.folder_title,
							gui.row_font_size + gui.pl_title_font_offset,
							highlight_width - date_w - extra - star_offset)

					else:
						ddt.text(
							(ex - date_w, height, 1), line,
							colours.folder_title,
							gui.row_font_size + gui.pl_title_font_offset)

				# -----

				# Draw separation line below title
				ddt.rect(
					(left + highlight_left, line_y + gui.playlist_row_height - 1 * gui.scale, highlight_width,
					1 * gui.scale), colours.folder_line)

				# Draw blue highlight insert line
				if drag_highlight:
					ddt.rect(
						[left + highlight_left, line_y + gui.playlist_row_height - 1 * gui.scale,
						highlight_width, 3 * gui.scale], [135, 145, 190, 255])

				continue

			# Draw playing highlight
			if playing:
				ddt.rect(track_box, colours.row_playing_highlight)
				ddt.text_background_colour = alpha_blend(colours.row_playing_highlight, ddt.text_background_colour)

			if tr.file_ext == "SPTY":
				# if not tauon.spot_ctl.started_once:
				#     ddt.rect((track_box[0], track_box[1], track_box[2], track_box[3] + 1), [40, 190, 40, 20])
				#     ddt.text_background_colour = alpha_blend([40, 190, 40, 20], ddt.text_background_colour)
				ddt.rect((track_box[0] + track_box[2] - round(2 * gui.scale), track_box[1] + round(2 * gui.scale), round(2 * gui.scale), track_box[3] - round(3 * gui.scale)), [40, 190, 40, 230])


			# Blue drop line
			if drag_highlight:  # playlist_hold_position != p_track:

				ddt.rect(
					[left + highlight_left, line_y + gui.playlist_row_height - 1 * gui.scale, highlight_width,
					3 * gui.scale], [125, 105, 215, 255])

			# Highlight
			if highlight:
				ddt.rect_a(
					(left + highlight_left, line_y), (highlight_width, gui.playlist_row_height),
					colours.row_select_highlight)

				ddt.text_background_colour = alpha_blend(colours.row_select_highlight, ddt.text_background_colour)

			if track_position > 0 and track_position < len(default_playlist) and tr.disc_number != "" and tr.disc_number != "0" and tr.album and tr.disc_number != pctl.get_track(default_playlist[track_position - 1]).disc_number \
					and tr.album == pctl.get_track(default_playlist[track_position - 1]).album and tr.parent_folder_path == pctl.get_track(default_playlist[track_position - 1]).parent_folder_path:
				# Draw disc change line
				ddt.rect(
					(left + highlight_left, line_y + 0 * gui.scale, highlight_width,
					1 * gui.scale), colours.folder_line)

			if not gui.set_mode:

				line_render(
					tr, track_position, gui.playlist_text_offset + line_y,
					playing, 255, left + inset_left, inset_width, 1, line_y)

			else:
				# NEE ---------------------------------------------------------
				n_track = tr
				p_track = track_position
				this_line_playing = playing

				start = 18 * gui.scale

				if center_mode:
					start = inset_left

				elif gui.lsp:
					start += gui.lspw

				run = start
				end = start + gui.plw

				if center_mode:
					end = highlight_width + start

				# gui.tracklist_center_mode = center_mode
				# gui.tracklist_inset_left = inset_left - round(20 * gui.scale)
				# gui.tracklist_inset_width = inset_width + round(20 * gui.scale)

				for h, item in enumerate(gui.pl_st):

					wid = item[1] - 20 * gui.scale
					y = gui.playlist_text_offset + gui.playlist_top + gui.playlist_row_height * number
					ry = gui.playlist_top + gui.playlist_row_height * number

					if run > end - 50 * gui.scale:
						break

					if len(gui.pl_st) == h + 1:
						wid -= 6 * gui.scale

					if item[0] == "Rating":
						if wid > 50 * gui.scale:
							yy = ry + (gui.playlist_row_height // 2) - (6 * gui.scale)
							draw_rating_widget(run + 4 * gui.scale, yy, n_track)

					if item[0] == "Starline":

						total = star_store.get_by_object(n_track)

						if total > 0 and n_track.length != 0 and wid > 0:
							if gui.star_mode == "star":

								star = star_count(total, n_track.length) - 1
								rr = 0
								if star > -1:
									if gui.tracklist_bg_is_light:
										colour = alpha_blend([0, 0, 0, 200], ddt.text_background_colour)
									else:
										colour = alpha_blend([255, 255, 255, 50], ddt.text_background_colour)

									sx = run + 6 * gui.scale
									sy = ry + (gui.playlist_row_height // 2) - (6 * gui.scale)
									for count in range(8):
										if star < count or rr > wid + round(6 * gui.scale):
											break
										star_pc_icon.render(sx, sy, colour)
										sx += round(13) * gui.scale
										rr += round(13) * gui.scale

							else:

								ratio = total / n_track.length
								if ratio > 0.55:
									star_x = int(ratio * (4 * gui.scale))
									star_x = min(star_x, wid)

									colour = colours.star_line
									if playing and colours.star_line_playing is not None:
										colour = colours.star_line_playing

									sy = (gui.playlist_top + gui.playlist_row_height * number) + int(
										gui.playlist_row_height / 2)
									ddt.rect((run + 4 * gui.scale, sy, star_x, 1 * gui.scale), colour)

					else:
						text = ""
						font = gui.row_font_size
						colour = [200, 200, 200, 255]
						norm_colour = colour
						y_off = 0
						if item[0] == "Title":
							colour = colours.title_text
							if n_track.title != "":
								text = n_track.title
							else:
								text = n_track.filename
							#     colour = colours.index_playing
							if this_line_playing is True:
								colour = colours.title_playing

						elif item[0] == "Artist":
							text = n_track.artist
							colour = colours.artist_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.artist_playing
						elif item[0] == "Album":
							text = n_track.album
							colour = colours.album_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.album_playing
						elif item[0] == "Album Artist":
							text = n_track.album_artist
							if not text and prefs.column_aa_fallback_artist:
								text = n_track.artist
							colour = colours.artist_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.artist_playing
						elif item[0] == "Composer":
							text = n_track.composer
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "Comment":
							text = n_track.comment.replace("\n", " ").replace("\r", " ")
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "S":
							if n_track.lfm_scrobbles > 0:
								text = str(n_track.lfm_scrobbles)

							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "#":

							if prefs.use_absolute_track_index and pctl.multi_playlist[pctl.active_playlist_viewing].hide_title:
								text = str(p_track)
							else:
								text = track_number_process(n_track.track_number)

							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "Date":
							text = n_track.date
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "Filepath":
							text = clean_string(n_track.fullpath)
							colour = colours.index_text
							norm_colour = colour
						elif item[0] == "Filename":
							text = clean_string(n_track.filename)
							colour = colours.index_text
							norm_colour = colour
						elif item[0] == "Disc":
							text = str(n_track.disc_number)
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "Codec":
							text = n_track.file_ext
							if text == "JELY" and "container" in tr.misc:
								text = tr.misc["container"]
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "Lyrics":
							text = ""
							if n_track.lyrics != "":
								text = "Y"
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "CUE":
							text = ""
							if n_track.is_cue:
								text = "Y"
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "Genre":
							text = n_track.genre
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "Bitrate":
							text = str(n_track.bitrate)
							if text == "0":
								text = ""

							ex = n_track.file_ext
							if n_track.misc.get("container") is not None:
								ex = n_track.misc.get("container")
							if ex == "FLAC" or ex == "WAV" or ex == "APE":
								text = str(round(n_track.samplerate / 1000, 1)).rstrip("0").rstrip(".") + "|" + str(
									n_track.bit_depth)
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "Time":
							text = get_display_time(n_track.length)
							colour = colours.bar_time
							norm_colour = colour
							# colour = colours.time_text
							if this_line_playing is True:
								colour = colours.time_text
						elif item[0] == "❤":
							# col love
							u = 5 * gui.scale
							yy = ry + (gui.playlist_row_height // 2) - (5 * gui.scale)
							if gui.scale == 1.25:
								yy += 1

							if get_love(n_track):

								j = 0  # justify right
								if run < start + 100 * gui.scale:
									j = 1  # justify left
								display_you_heart(run + 6 * gui.scale, yy, j)
								u += 18 * gui.scale

							if "spotify-liked" in n_track.misc:
								j = 0  # justify right
								if run < start + 100 * gui.scale:
									j = 1  # justify left
								display_spot_heart(run + u, yy, j)
								u += 18 * gui.scale

							count = 0
							for name in n_track.lfm_friend_likes:
								spacing = 6 * gui.scale
								if u + (heart_row_icon.w + spacing) * count > wid + 7 * gui.scale:
									break

								x = run + u + (heart_row_icon.w + spacing) * count

								j = 0  # justify right
								if run < start + 100 * gui.scale:
									j = 1  # justify left

								display_friend_heart(x, yy, name, j)
								count += 1

							# if n_track.track_number == 1 or n_track.track_number == "1":
							#     ss = wid - (wid % 15)
							#     tauon.gall_ren.render(n_track, (run, y), ss)


						elif item[0] == "P":
							ratio = 0
							total = star_store.get_by_object(n_track)
							if total > 0 and n_track.length > 2:
								if n_track.length > 15:
									total += 2
								ratio = total / (n_track.length - 1)

							text = str(str(int(ratio)))
							if text == "0":
								text = ""
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing

						if prefs.dim_art and album_mode and \
								n_track.parent_folder_name \
								!= pctl.master_library[pctl.track_queue[pctl.queue_step]].parent_folder_name:
							colour = alpha_mod(colour, 150)
						if n_track.found is False:
							colour = colours.playlist_text_missing

						if text:
							if item[0] in colours.column_colours:
								colour = colours.column_colours[item[0]]

							if this_line_playing and item[0] in colours.column_colours_playing:
								colour = colours.column_colours_playing[item[0]]

							if run + 6 * gui.scale + wid > end:
								wid = end - run - 40 * gui.scale
								if center_mode:
									wid += 25 * gui.scale

							wid = max(0, wid)

							# # Hacky. Places a dark background behind light text for readability over mascot
							# if pl_bg and gui.set_mode and colour_value(norm_colour) < 400 and not colours.lm:
							#     w, h = ddt.get_text_wh(text, font, wid)
							#     quick_box = [run + round(5 * gui.scale), y + y_off, w + round(2 * gui.scale), h]
							#     if coll_rect((left + width - pl_bg.w - 60 * gui.scale, window_size[1] - gui.panelBY - pl_bg.h, pl_bg.w, pl_bg.h), quick_box):
							#         quick_box = (run, ry, item[1], gui.playlist_row_height)
							#         ddt.rect(quick_box, [0, 0, 0, 40], True)
							#         ddt.rect(quick_box, alpha_mod(colours.playlist_panel_background, 150), True)

							ddt.text(
								(run + 6 * gui.scale, y + y_off),
								text,
								colour,
								font,
								max_w=wid)

							if ddt.was_truncated:
								#logging.info(text)
								rect = (run, y, wid - 1, gui.playlist_row_height - 1)
								gui.heart_fields.append(rect)

								if coll(rect):
									columns_tool_tip.set(run - 7 * gui.scale, y, text, font, rect)

					run += item[1]

			# -----------------------------------------------------------------
			# Count the number if visable tracks (used by Show Current function)
			if gui.playlist_top + gui.playlist_row_height * w > window_size[0] - gui.panelBY - gui.playlist_row_height:
				pass
			else:
				cv += 1

			# w += 1
			# if w > gui.playlist_view_length:
			#     break

		# This is a bit hacky since its only generated after drawing
		# Used to keep track of how many tracks are actually in view
		gui.playlist_current_visible_tracks = cv
		gui.playlist_current_visible_tracks_id = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int

		if (right_click and gui.playlist_top + 5 * gui.scale + gui.playlist_row_height * len(list_items) <
				mouse_position[1] < window_size[
					1] - 55 and width + left > mouse_position[0] > gui.playlist_left + 15):
			playlist_menu.activate()

		SDL_SetRenderTarget(renderer, gui.main_texture)
		SDL_RenderCopy(renderer, gui.tracklist_texture, None, gui.tracklist_texture_rect)

		if mouse_down is False:
			playlist_hold = False

		ddt.pretty_rect = None
		ddt.alpha_bg = False

	def cache_render(self):

		SDL_RenderCopy(renderer, gui.tracklist_texture, None, gui.tracklist_texture_rect)

class ArtBox:

	def __init__(self):
		pass

	def draw(self, x, y, w, h, target_track=None, tight_border=False, default_border=None):

		# Draw a background for whole area
		ddt.rect((x, y, w, h), colours.side_panel_background)
		# ddt.rect_r((x, y, w ,h), [255, 0, 0, 200], True)

		# We need to find the size of the inner square for the artwork
		# box = min(w, h)

		box_w = w
		box_h = h

		box_w -= 17 * gui.scale  # Inset the square a bit
		box_h -= 17 * gui.scale  # Inset the square a bit

		box_x = x + ((w - box_w) // 2)
		box_y = y + ((h - box_h) // 2)

		# And position the square
		rect = (box_x, box_y, box_w, box_h)
		gui.main_art_box = rect

		# Draw the album art. If side bar is being dragged set quick draw flag
		showc = None
		result = 1

		if target_track:  # Only show if song playing or paused
			result = album_art_gen.display(target_track, (rect[0], rect[1]), (box_w, box_h), side_drag)
			showc = album_art_gen.get_info(target_track)

		# Draw faint border on album art
		if tight_border:
			if result == 0 and gui.art_drawn_rect:
				border = gui.art_drawn_rect
				ddt.rect_s(gui.art_drawn_rect, colours.art_box, 1 * gui.scale)
			elif default_border:
				border = default_border
				ddt.rect_s(default_border, colours.art_box, 1 * gui.scale)
			else:
				border = rect
		else:
			ddt.rect_s(rect, colours.art_box, 1 * gui.scale)
			border = rect

		fields.add(border)

		# Draw image downloading indicator
		if gui.image_downloading:
			ddt.text(
				(x + int(box_w / 2), 38 * gui.scale + int(box_h / 2), 2), _("Fetching image..."),
				colours.side_bar_line1,
				14, bg=colours.side_panel_background)
			gui.update = 2

		# Input for album art
		if target_track:

			# Cycle images on click

			if coll(gui.main_art_box) and inp.mouse_click is True and key_focused == 0:

				album_art_gen.cycle_offset(target_track)

				if pctl.mpris:
					pctl.mpris.update(force=True)

		# Activate picture context menu on right click
		if tight_border and gui.art_drawn_rect:
			if right_click and coll(gui.art_drawn_rect) and target_track:
				picture_menu.activate(in_reference=target_track)
		elif right_click and coll(rect) and target_track:
			picture_menu.activate(in_reference=target_track)

		# Draw picture metadata
		if showc is not None and coll(border) \
			and rename_track_box.active is False \
			and radiobox.active is False \
			and pref_box.enabled is False \
			and gui.rename_playlist_box is False \
			and gui.message_box is False \
			and track_box is False \
			and gui.layer_focus == 0:

			padding = 6 * gui.scale

			xw = box_x + box_w
			yh = box_y + box_h
			if tight_border and gui.art_drawn_rect and gui.art_drawn_rect[2] > 50 * gui.scale:
				xw = gui.art_drawn_rect[0] + gui.art_drawn_rect[2]
				yh = gui.art_drawn_rect[1] + gui.art_drawn_rect[3]

			art_metadata_overlay(xw, yh, showc)


class ScrollBox:

	def __init__(self):

		self.held = False
		self.slide_hold = False
		self.source_click_y = 0
		self.source_bar_y = 0
		self.direction_lock = -1
		self.d_position = 0

	def draw(
		self, x, y, w, h, value, max_value, force_dark_theme=False, click=None, r_click=False, jump_distance=4, extend_field=0):

		if max_value < 2:
			return 0

		if click is None:
			click = inp.mouse_click

		bar_height = round(90 * gui.scale)

		if h > 400 * gui.scale and max_value < 20:
			bar_height = round(180 * gui.scale)

		bg = [255, 255, 255, 7]
		fg = [255, 255, 255, 30]
		fg_h = [255, 255, 255, 40]
		fg_off = [255, 255, 255, 15]

		if colours.lm and not force_dark_theme:
			bg = [0, 0, 0, 15]
			fg_off = [0, 0, 0, 30]
			fg = [0, 0, 0, 60]
			fg_h = [0, 0, 0, 70]

		ddt.rect((x, y, w, h), bg)

		half = bar_height // 2

		ratio = value / max_value

		mi = y + half
		mo = y + h - half
		distance = mo - mi
		position = int(round(distance * ratio))

		fw = w + extend_field
		fx = x - extend_field

		if coll((fx, y, fw, h)):

			if mouse_down:
				gui.update += 1

			if r_click:
				p = mouse_position[1] - half - y
				p = max(0, p)

				range = h - bar_height
				p = min(p, range)

				per = p / range

				value = int(round(max_value * per))

				ratio = value / max_value

				mi = y + half
				mo = y + h - half
				distance = mo - mi
				position = int(round(distance * ratio))

			in_bar = False
			if coll((x, mi + position - half, w, bar_height)):
				in_bar = True
				if click:
					self.held = True

					# p_y = pointer(c_int(0))
					# SDL_GetGlobalMouseState(None, p_y)
					get_sdl_input.mouse_capture_want = True
					self.source_click_y = mouse_position[1]
					self.source_bar_y = position

			if pctl.playlist_view_position < 0:
				pctl.playlist_view_position = 0


			elif mouse_down and not self.held:

				if click and not in_bar:
					self.slide_hold = True
					self.direction_lock = 1
					if mouse_position[1] - y < position:
						self.direction_lock = 0

					self.d_position = value / max_value

				if self.slide_hold:
					if (self.direction_lock == 1 and mouse_position[1] - y < position + half) or \
							(self.direction_lock == 0 and mouse_position[1] - y > position + half):
						pass
					else:

						tt = scroll_timer.hit()
						if tt > 0.1:
							tt = 0

						flip = -1
						if self.direction_lock:
							flip = 1

						self.d_position = min(max(self.d_position + (((tt * jump_distance) / max_value) * flip), 0), 1)

			else:
				self.slide_hold = False

		if (self.held and mouse_up) or not mouse_down:
			self.held = False

		if self.held and not window_is_focused():
			self.held = False

		if self.held:
			get_sdl_input.mouse_capture_want = True
			new_y = mouse_position[1]
			gui.update += 1

			offset = new_y - self.source_click_y

			position = self.source_bar_y + offset

			position = max(position, 0)
			position = min(position, distance)

			ratio = position / distance
			value = int(round(max_value * ratio))

		colour = fg_off
		rect = (x, mi + position - half, w, bar_height)
		fields.add(rect)
		if coll(rect):
			colour = fg
		if self.held:
			colour = fg_h

		ddt.rect(rect, colour)

		if self.slide_hold:
			return round(max_value * self.d_position)

		return value


class RadioBox:

	def __init__(self):

		self.active = False
		self.station_editing = None
		self.edit_mode = True
		self.add_mode = False
		self.radio_field_active = 1
		self.radio_field = TextBox2()
		self.radio_field_title = TextBox2()
		self.radio_field_search = TextBox2()

		self.x = 1
		self.y = 1
		self.w = 1
		self.h = 1
		self.center = False

		self.scroll_position = 0
		self.scroll = ScrollBox()

		self.dummy_track = TrackClass()
		self.dummy_track.index = -2
		self.dummy_track.is_network = True
		self.dummy_track.art_url_key = ""  # radio"
		self.dummy_track.file_ext = "RADIO"
		self.playing_title = ""

		self.proxy_started = False
		self.loaded_url = None
		self.loaded_station = None
		self.load_connecting = False
		self.load_failed = False
		self.searching = False
		self.load_failed_timer = Timer()
		self.right_clicked_station = None
		self.right_clicked_station_p = None
		self.click_point = (0, 0)

		self.song_key = ""

		self.drag = None

		self.tab = 0
		self.temp_list = []

		self.hosts = None
		self.host = None

		self.search_menu = Menu(170)
		self.search_menu.add(MenuItem(_("Search Tag"), self.search_tag, pass_ref=True))
		self.search_menu.add(MenuItem(_("Search Country Code"), self.search_country, pass_ref=True))
		self.search_menu.add(MenuItem(_("Search Title"), self.search_title, pass_ref=True))

		self.websocket = None
		self.ws_interval = 4.5
		self.websocket_source_urls = ("https://listen.moe/kpop/stream", "https://listen.moe/stream")
		self.run_proxy = True

	def parse_vorbis_okay(self):
		return (
			self.loaded_url not in self.websocket_source_urls) and \
			"radio.plaza.one" not in self.loaded_url and \
			"gensokyoradio.net" not in self.loaded_url

	def search_country(self, text):

		if len(text) == 2 and text.isalpha():
			self.search_radio_browser(
				"/json/stations/search?countrycode=" + text + "&order=votes&limit=250&reverse=true")
		else:
			self.search_radio_browser(
				"/json/stations/search?country=" + text + "&order=votes&limit=250&reverse=true")

	def search_tag(self, text):

		text = text.lower()
		self.search_radio_browser("/json/stations/search?order=votes&limit=250&reverse=true&tag=" + text)

	def search_title(self, text):

		text = text.lower()
		self.search_radio_browser("/json/stations/search?order=votes&limit=250&reverse=true&name=" + text)

	def is_m3u(self, url):
		return url.lower().endswith(".m3u") or url.lower().endswith(".m3u8")

	def extract_stream_m3u(self, url, recursion_limit=5):
		if recursion_limit <= 0:
			return None
		logging.info("Fetching M3U...")

		try:
			response = requests.get(url, timeout=10)
			if response.status_code != 200:
				logging.error(f"M3U Fetch error code: {response.status_code}")
				return None

			content = response.text
			lines = content.strip().split("\n")

			for line in lines:
				line = line.strip()
				if not line.startswith("#") and len(line) > 0:
					if self.is_m3u(line):
						next_url = urllib.parse.urljoin(url, line)
						return self.extract_stream_m3u(next_url, recursion_limit - 1)
					return urllib.parse.urljoin(url, line)

			return None

		except Exception:
			logging.exception("Failed to extract M3U")
			return None

	def start(self, item):
		url = item["stream_url"]
		logging.info("Start radio")
		logging.info(url)
		if self.is_m3u(url):
			url = self.extract_stream_m3u(url)
			logging.info(f"Extracted URL is: {url}")
			if not url:
				logging.info("Failed to extract stream from M3U")
				return

		if self.load_connecting:
			return

		if tauon.spot_ctl.playing or tauon.spot_ctl.coasting:
			tauon.spot_ctl.control("stop")

		try:
			self.websocket.close()
			logging.info("Websocket closed")
		except Exception:
			logging.exception("No socket to close?")

		self.playing_title = ""
		self.playing_title = item["title"]
		self.dummy_track.art_url_key = ""
		self.dummy_track.title = ""
		self.dummy_track.artist = ""
		self.dummy_track.album = ""
		self.dummy_track.date = ""
		pctl.radio_meta_on = ""

		album_art_gen.clear_cache()

		if not tauon.test_ffmpeg():
			prefs.auto_rec = False
			return

		self.run_proxy = True
		if url.endswith(".ts"):
			self.run_proxy = False

		if self.run_proxy and not self.proxy_started and prefs.backend != 4:
			shoot = threading.Thread(target=stream_proxy, args=[tauon])
			shoot.daemon = True
			shoot.start()
			self.proxy_started = True

		# pctl.url = url
		pctl.url = f"http://127.0.0.1:{7812}"
		if not self.run_proxy:
			pctl.url = item["stream_url"]
		self.loaded_url = None
		pctl.tag_meta = ""
		pctl.radio_meta_on = ""
		pctl.found_tags = {}
		self.song_key = ""
		pctl.playing_time = 0
		pctl.decode_time = 0
		self.loaded_station = item

		if tauon.stream_proxy.download_running:
			tauon.stream_proxy.abort = True

		self.load_connecting = True
		self.load_failed = False

		shoot = threading.Thread(target=self.start2, args=[url])
		shoot.daemon = True
		shoot.start()

	def start2(self, url):

		if self.run_proxy and not tauon.stream_proxy.start_download(url):
			self.load_failed_timer.set()
			self.load_failed = True
			self.load_connecting = False
			gui.update += 1
			logging.error("Starting radio failed")
			# show_message(_("Failed to establish a connection"), mode="error")
			return

		self.loaded_url = url
		pctl.playing_state = 0
		pctl.record_stream = False
		pctl.playerCommand = "url"
		pctl.playerCommandReady = True
		pctl.playing_state = 3
		pctl.playing_time = 0
		pctl.decode_time = 0
		pctl.playing_length = 0
		tauon.thread_manager.ready_playback()
		hit_discord()

		if tauon.update_play_lock is not None:
			tauon.update_play_lock()

		time.sleep(0.1)
		self.load_connecting = False
		self.load_failed = False
		gui.update += 1

		wss = ""
		if url == "https://listen.moe/kpop/stream":
			wss = "wss://listen.moe/kpop/gateway_v2"
		if url == "https://listen.moe/stream":
			wss = "wss://listen.moe/gateway_v2"
		if wss:
			logging.info("Connecting to Listen.moe")
			import websocket
			import _thread as th

			def send_heartbeat(ws):
				#logging.info(self.ws_interval)
				time.sleep(self.ws_interval)
				ws.send("{\"op\":9}")
				logging.info("Send heatbeat")

			def on_message(ws, message):
				logging.info(message)
				d = json.loads(message)
				if d["op"] == 10:
					shoot = threading.Thread(target=send_heartbeat, args=[ws])
					shoot.daemon = True
					shoot.start()

				if d["op"] == 0:
					self.ws_interval = d["d"]["heartbeat"] / 1000
					ws.send("{\"op\":9}")

				if d["op"] == 1:
					try:

						found_tags = {}
						found_tags["title"] = d["d"]["song"]["title"]
						if d["d"]["song"]["artists"]:
							found_tags["artist"] = d["d"]["song"]["artists"][0]["name"]
						line = ""
						if "title" in found_tags:
							line += found_tags["title"]
							if "artist" in found_tags:
								line = found_tags["artist"] + " - " + line

						pctl.found_tags = found_tags
						pctl.tag_meta = line

						filename = d["d"]["song"]["albums"][0]["image"]
						fulllink = "https://cdn.listen.moe/covers/" + filename

						#logging.info(fulllink)
						art_response = requests.get(fulllink, timeout=10)
						#logging.info(art_response.status_code)

						if art_response.status_code == 200:
							if pctl.radio_image_bin:
								pctl.radio_image_bin.close()
								pctl.radio_image_bin = None
							pctl.radio_image_bin = io.BytesIO(art_response.content)
							pctl.radio_image_bin.seek(0)
							radiobox.dummy_track.art_url_key = "ok"
							logging.info("Got new art")


					except Exception:
						logging.exception("No image")
						if pctl.radio_image_bin:
							pctl.radio_image_bin.close()
							pctl.radio_image_bin = None
					gui.clear_image_cache_next += 1
					gui.update += 1

			def on_error(ws, error):
				logging.error(error)

			def on_close(ws):
				logging.info("### closed ###")

			def on_open(ws):
				def run(*args):
					pass
					# for i in range(3):
					#     time.sleep(4.5)
					#     ws.send("{\"op\":9}")
					# time.sleep(10)
					# ws.close()
					#logging.info("thread terminating...")

				th.start_new_thread(run, ())

			# websocket.enableTrace(True)
			#logging.info(wss)
			ws = websocket.WebSocketApp(wss,
										on_message=on_message,
										on_error=on_error)
			ws.on_open = on_open
			self.websocket = ws
			shoot = threading.Thread(target=ws.run_forever)
			shoot.daemon = True
			shoot.start()

	def delete_radio_entry(self, item):
		for i, saved in enumerate(prefs.radio_urls):
			if saved["stream_url"] == item["stream_url"] and saved["title"] == item["title"]:
				del prefs.radio_urls[i]

	def delete_radio_entry_after(self, item):
		p = radiobox.right_clicked_station_p
		del prefs.radio_urls[p + 1:]

	def edit_entry(self, item):
		radio = item
		self.radio_field_title.text = radio["title"]
		self.radio_field.text = radio["stream_url"]

	def browser_get_hosts(self):

		import socket
		"""
		Get all base urls of all currently available radiobrowser servers

		Returns:
		list: a list of strings

		"""
		hosts = []
		# get all hosts from DNS
		ips = socket.getaddrinfo(
			"all.api.radio-browser.info", 80, 0, 0, socket.IPPROTO_TCP)
		for ip_tupple in ips:
			try:
				ip = ip_tupple[4][0]

				# do a reverse lookup on every one of the ips to have a nice name for it
				host_addr = socket.gethostbyaddr(ip)
				# add the name to a list if not already in there
				if host_addr[0] not in hosts:
					hosts.append(host_addr[0])
			except Exception:
				logging.exception("IPv4 lookup fail")

		# sort list of names
		hosts.sort()
		# add "https://" in front to make it an url
		return list(map(lambda x: "https://" + x, hosts))

	def search_page(self):

		y = self.y
		x = self.x
		w = self.w
		h = self.h

		yy = y + round(40 * gui.scale)

		width = round(330 * gui.scale)
		rect = (x + 8 * gui.scale, yy - round(2 * gui.scale), width, 22 * gui.scale)
		fields.add(rect)
		# if (coll(rect) and gui.level_2_click) or (input.key_tab_press and self.radio_field_active == 2):
		#     self.radio_field_active = 1
		#     input.key_tab_press = False
		if not self.radio_field_search.text and not editline:
			ddt.text((x + 14 * gui.scale, yy), _("Search text…"), colours.box_text_label, 312)
		self.radio_field_search.draw(
			x + 14 * gui.scale, yy, colours.box_input_text,
			active=True,
			width=width, click=gui.level_2_click)

		ddt.rect_s(rect, colours.box_text_border, 1 * gui.scale)

		if draw.button(
			_("Search"), x + width + round(21 * gui.scale), yy - round(3 * gui.scale),
			press=gui.level_2_click, w=round(80 * gui.scale)) or inp.level_2_enter:

			text = self.radio_field_search.text.replace("/", "").replace(":", "").replace("\\", "").replace(".", "").replace(
				"-", "").upper()
			text = urllib.parse.quote(text)
			if len(text) > 1:
				self.search_menu.activate(text, position=(x + width + round(21 * gui.scale), yy + round(20 * gui.scale)))
		if draw.button(_("Get Top Voted"), x + round(8 * gui.scale), yy + round(30 * gui.scale), press=gui.level_2_click):
			self.search_radio_browser("/json/stations?order=votes&limit=250&reverse=true")

		ww = ddt.get_text_w(_("Get Top Voted"), 212)
		if key_shift_down:
			if draw.button(_("Developer Picks"), x + ww + round(35 * gui.scale), yy + round(30 * gui.scale), press=gui.level_2_click):
				self.temp_list.clear()

				radio = {}
				radio["title"] = "Nightwave Plaza"
				radio["stream_url_unresolved"] = "https://radio.plaza.one/ogg"
				radio["stream_url"] = "https://radio.plaza.one/ogg"
				radio["website_url"] = "https://plaza.one/"
				radio["icon"] = "https://plaza.one/icons/apple-touch-icon.png"
				radio["country"] = "Japan"
				self.temp_list.append(radio)

				radio = {}
				radio["title"] = "Gensokyo Radio"
				radio["stream_url_unresolved"] = " https://stream.gensokyoradio.net/GensokyoRadio-enhanced.m3u"
				radio["stream_url"] = "https://stream.gensokyoradio.net/1"
				radio["website_url"] = "https://gensokyoradio.net/"
				radio["icon"] = "https://gensokyoradio.net/favicon.ico"
				radio["country"] = "Japan"
				self.temp_list.append(radio)

				radio = {}
				radio["title"] = "Listen.moe | Jpop"
				radio["stream_url_unresolved"] = "https://listen.moe/stream"
				radio["stream_url"] = "https://listen.moe/stream"
				radio["website_url"] = "https://listen.moe/"
				radio["icon"] = "https://avatars.githubusercontent.com/u/26034028?s=200&v=4"
				radio["country"] = "Japan"
				self.temp_list.append(radio)

				radio = {}
				radio["title"] = "Listen.moe | Kpop"
				radio["stream_url_unresolved"] = "https://listen.moe/kpop/stream"
				radio["stream_url"] = "https://listen.moe/kpop/stream"
				radio["website_url"] = "https://listen.moe/"
				radio["icon"] = "https://avatars.githubusercontent.com/u/26034028?s=200&v=4"
				radio["country"] = "Korea"

				self.temp_list.append(radio)

				radio = {}
				radio["title"] = "HBR1 Dream Factory | Ambient"
				radio["stream_url_unresolved"] = "http://radio.hbr1.com:19800/ambient.ogg"
				radio["stream_url"] = "http://radio.hbr1.com:19800/ambient.ogg"
				radio["website_url"] = "http://www.hbr1.com/"
				self.temp_list.append(radio)

				radio = {}
				radio["title"] = "Yggdrasil Radio | Anime & Jpop"
				radio["stream_url_unresolved"] = "http://shirayuki.org:9200/"
				radio["stream_url"] = "http://shirayuki.org:9200/"
				radio["website_url"] = "https://yggdrasilradio.net/"
				self.temp_list.append(radio)

				for station in primary_stations:
					self.temp_list.append(station)

	def search_radio_browser(self, param):
		if self.searching:
			return
		self.searching = True
		shoot = threading.Thread(target=self.search_radio_browser2, args=[param])
		shoot.daemon = True
		shoot.start()

	def search_radio_browser2(self, param):

		if not self.hosts:
			self.hosts = self.browser_get_hosts()
		if not self.host:
			self.host = random.choice(self.hosts)

		uri = self.host + param
		req = urllib.request.Request(uri)
		req.add_header("User-Agent", t_agent)
		req.add_header("Content-Type", "application/json")
		response = urllib.request.urlopen(req, context=ssl_context)
		data = response.read()
		data = json.loads(data.decode())
		self.parse_data(data)
		self.searching = False

	def parse_data(self, data):

		self.temp_list.clear()

		for station in data:
			radio: dict[str, int | str] = {}
			#logging.info(station)
			radio["title"] = station["name"]
			radio["stream_url_unresolved"] = station["url"]
			radio["stream_url"] = station["url_resolved"]
			radio["icon"] = station["favicon"]
			radio["country"] = station["country"]
			if radio["country"] == "The Russian Federation":
				radio["country"] = "Russia"
			elif radio["country"] == "The United States Of America":
				radio["country"] = "USA"
			elif radio["country"] == "The United Kingdom Of Great Britain And Northern Ireland":
				radio["country"] = "United Kingdom"
			elif radio["country"] == "Islamic Republic Of Iran":
				radio["country"] = "Iran"
			elif len(station["country"]) > 20:
				radio["country"] = station["countrycode"]
			radio["website_url"] = station["homepage"]
			if "homepage" in station:
				radio["website_url"] = station["homepage"]
			self.temp_list.append(radio)
		gui.update += 1

	def render(self) -> None:

		if self.edit_mode:
			w = round(510 * gui.scale)
			h = round(120 * gui.scale)  # + sh

			self.w = w
			self.h = h
			# self.x = x
			# self.y = y
			width = w
			if self.center:
				x = int(window_size[0] / 2) - int(w / 2)
				y = int(window_size[1] / 2) - int(h / 2)
				yy = y
				self.y = y
				self.x = x
			else:
				yy = self.y
				y = self.y
				x = self.x
			ddt.rect_a((x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale), colours.box_border)
			ddt.rect_a((x, y), (w, h), colours.box_background)
			ddt.text_background_colour = colours.box_background
			if key_esc_press or (gui.level_2_click and not coll((x, y, w, h))):
				self.active = False

			if self.add_mode:
				ddt.text((x + 10 * gui.scale, yy + 8 * gui.scale), _("Add Station"), colours.box_title_text, 213)
			else:
				ddt.text((x + 10 * gui.scale, yy + 8 * gui.scale), _("Edit Station"), colours.box_title_text, 213)

			self.saved()
			return

		w = round(510 * gui.scale)
		h = round(356 * gui.scale)  # + sh
		x = int(window_size[0] / 2) - int(w / 2)
		y = int(window_size[1] / 2) - int(h / 2)

		self.w = w
		self.h = h
		self.x = x
		self.y = y

		yy = y

		ddt.rect_a((x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale), colours.box_border)
		ddt.rect_a((x, y), (w, h), colours.box_background)

		ddt.text_background_colour = colours.box_background

		if key_esc_press or (gui.level_2_click and not coll((x, y, w, h))):
			self.active = False

		ddt.text((x + 10 * gui.scale, yy + 8 * gui.scale), _("Station Browser"), colours.box_title_text, 213)

		# ---
		if self.load_connecting:
			ddt.text((x + 495 * gui.scale, yy + 8 * gui.scale, 1), _("Connecting..."), colours.box_title_text, 311)
		elif self.load_failed:
			ddt.text((x + 495 * gui.scale, yy + 8 * gui.scale, 1), _("Failed to connect!"), colours.box_title_text, 311)
			if self.load_failed_timer.get() > 3:
				gui.delay_frame(0.2)
				self.load_failed = False

		elif self.searching:
			ddt.text((x + 495 * gui.scale, yy + 8 * gui.scale, 1), _("Searching..."), colours.box_title_text, 311)
		elif pctl.playing_state == 3:

			text = ""
			if tauon.stream_proxy.s_format:
				text = str(tauon.stream_proxy.s_format)
			if tauon.stream_proxy.s_bitrate and tauon.stream_proxy.s_bitrate.isnumeric():
				text += " " + tauon.stream_proxy.s_bitrate + _("kbps")

			ddt.text((x + 495 * gui.scale, yy + 8 * gui.scale, 1), text, colours.box_title_text, 311)
			# if tauon.stream_proxy.s_format:
			#     ddt.text((x + 425 * gui.scale, yy + 8 * gui.scale,), tauon.stream_proxy.s_format, colours.box_title_text, 311)
			# if tauon.stream_proxy.s_bitrate:
			#     ddt.text((x + 454 * gui.scale, yy + 8 * gui.scale,), tauon.stream_proxy.s_bitrate + "kbps", colours.box_title_text, 311)

		# --- ----------------------------------------------------------------------
		if self.tab == 1:
			self.search_page()
		elif self.tab == 0:
			self.saved()
		self.draw_list()
		# self.footer()
		return

	def saved(self):
		y = self.y
		x = self.x
		w = self.w
		h = self.h

		yy = y + round(40 * gui.scale)

		width = round(370 * gui.scale)

		rect = (x + 8 * gui.scale, yy - round(2 * gui.scale), width, 22 * gui.scale)
		fields.add(rect)
		if (coll(rect) and gui.level_2_click) or (inp.key_tab_press and self.radio_field_active == 2):
			self.radio_field_active = 1
			inp.key_tab_press = False
		if not self.radio_field_title.text and not (self.radio_field_active == 1 and editline):
			ddt.text((x + 14 * gui.scale, yy), _("Name / Title"), colours.box_text_label, 312)
		self.radio_field_title.draw(x + 14 * gui.scale, yy, colours.box_input_text,
									active=self.radio_field_active == 1,
									width=width, click=gui.level_2_click)

		ddt.rect_s(rect, colours.box_text_border, 1 * gui.scale)

		yy += round(30 * gui.scale)

		rect = (x + 8 * gui.scale, yy - round(2 * gui.scale), width, 22 * gui.scale)
		ddt.rect_s(rect, colours.box_text_border, 1 * gui.scale)
		fields.add(rect)
		if (coll(rect) and gui.level_2_click) or (inp.key_tab_press and self.radio_field_active == 1):
			self.radio_field_active = 2
			inp.key_tab_press = False

		if not self.radio_field.text and not (self.radio_field_active == 2 and editline):
			ddt.text((x + 14 * gui.scale, yy), _("Raw Stream URL http://example.stream:1234"), colours.box_text_label, 312)
		self.radio_field.draw(
			x + 14 * gui.scale, yy, colours.box_input_text, active=self.radio_field_active == 2,
			width=width, click=gui.level_2_click)

		if draw.button(_("Save"), x + width + round(21 * gui.scale), yy - round(20 * gui.scale), press=gui.level_2_click):

			if not self.radio_field.text:
				show_message(_("Enter a stream URL"))
			elif "http://" in self.radio_field.text or "https://" in self.radio_field.text:
				radio = self.station_editing
				if self.add_mode:
					radio: dict[str, int | str] = {}
				radio["title"] = self.radio_field_title.text
				radio["stream_url"] = self.radio_field.text
				radio["website_url"] = ""

				if self.add_mode:
					pctl.radio_playlists[pctl.radio_playlist_viewing]["items"].append(radio)
				self.active = False

			else:
				show_message(_("Could not validate URL. Must start with https:// or http://"))

	def draw_list(self):

		x = self.x
		y = self.y
		w = self.w
		h = self.h

		if self.drag:
			gui.update_on_drag = True

		yy = y + round(100 * gui.scale)
		x += round(10 * gui.scale)

		radio_list = prefs.radio_urls
		if self.tab == 1:
			radio_list = self.temp_list

		rect = (x, y, w, h)
		if coll(rect):
			self.scroll_position += mouse_wheel * -1
		self.scroll_position = max(self.scroll_position, 0)
		self.scroll_position = min(self.scroll_position, len(radio_list) // 2 - 7)

		if len(radio_list) // 2 > 9:
			self.scroll_position = self.scroll.draw(
				(x + w) - round(35 * gui.scale), yy, round(15 * gui.scale),
				round(210 * gui.scale), self.scroll_position,
				len(radio_list) // 2 - 7, True, click=gui.level_2_click)

		self.scroll_position = max(self.scroll_position, 0)

		p = self.scroll_position * 2
		offset = 0
		to_delete = None
		swap = None

		while True:

			if p > len(radio_list) - 1:
				break

			xx = x + offset
			item = radio_list[p]

			rect = (xx, yy, round(233 * gui.scale), round(40 * gui.scale))
			fields.add(rect)

			bg = colours.box_background
			text_colour = colours.box_input_text

			playing = pctl.playing_state == 3 and self.loaded_url == item["stream_url"]

			if playing:
				# bg = colours.box_sub_highlight
				# ddt.rect(rect, bg, True)

				bg = colours.tab_background_active
				text_colour = colours.tab_text_active
				ddt.rect(rect, bg)

			if radio_view.drag:
				if item == radio_view.drag:
					text_colour = colours.box_sub_text
					bg = [255, 255, 255, 10]
					ddt.rect(rect, bg)
			elif (radio_entry_menu.active and radio_entry_menu.reference == p) or \
					((not radio_entry_menu.active and coll(rect)) and not playing):
				text_colour = colours.box_sub_text
				bg = [255, 255, 255, 10]
				ddt.rect(rect, bg)

			if coll(rect):

				if gui.level_2_click:
					# self.drag = p
					# self.click_point = copy.copy(mouse_position)
					radio_view.drag = item
					radio_view.click_point = copy.copy(mouse_position)
				if mouse_up:  # gui.level_2_click:
					gui.update += 1
					# if self.drag is not None and p != self.drag:
					#     swap = p
					if point_proximity_test(radio_view.click_point, mouse_position, round(4 * gui.scale)):
						self.start(item)
				if middle_click:
					to_delete = p
				if level_2_right_click:
					self.right_clicked_station = item
					self.right_clicked_station_p = p
					radio_entry_menu.activate(item)

			bg = alpha_blend(bg, colours.box_background)

			boxx = round(32 * gui.scale)
			toff = boxx + round(10 * gui.scale)
			if item["title"]:
				ddt.text(
					(xx + toff, yy + round(3 * gui.scale)), item["title"], text_colour, 212, bg=bg,
					max_w=rect[2] - (15 * gui.scale + toff))
			else:
				ddt.text(
					(xx + toff, yy + round(3 * gui.scale)), item["stream_url"], text_colour, 212, bg=bg,
					max_w=rect[2] - (15 * gui.scale + toff))

			country = item.get("country")
			if country:
				ddt.text(
					(xx + toff, yy + round(18 * gui.scale)), country, text_colour, 11, bg=bg,
					max_w=rect[2] - (15 * gui.scale + toff))

			b_rect = (xx + round(4 * gui.scale), yy + round(4 * gui.scale), boxx, boxx)
			ddt.rect(b_rect, colours.box_thumb_background)
			radio_thumb_gen.draw(item, b_rect[0], b_rect[1], b_rect[2])

			if offset == 0:
				offset = rect[2] + round(4 * gui.scale)
			else:
				offset = 0
				yy += round(43 * gui.scale)

			if yy > y + 300 * gui.scale:
				break

			p += 1

		# if to_delete is not None:
		#     del radio_list[to_delete]
		#
		# if mouse_up and self.drag and mouse_position[1] > yy + round(22 * gui.scale):
		#     swap = len(radio_list)

		# if self.drag and not point_proximity_test(self.click_point, mouse_position, round(4 * gui.scale)):
		#     ddt.rect((
		#              mouse_position[0] + round(8 * gui.scale), mouse_position[1] - round(8 * gui.scale), 45 * gui.scale,
		#              13 * gui.scale), colours.grey(70))

		# if swap is not None:
		#
		#     old = radio_list[self.drag]
		#     radio_list[self.drag] = None
		#
		#     if swap > self.drag:
		#         swap += 1
		#
		#     radio_list.insert(swap, old)
		#     radio_list.remove(None)
		#
		#     self.drag = None
		#     gui.update += 1

		# if not mouse_down:
		#     self.drag = None

	def footer(self):

		y = self.y
		x = self.x + round(15 * gui.scale)
		w = self.w
		h = self.h

		yy = y + round(328 * gui.scale)
		if pctl.playing_state == 3 and not prefs.auto_rec:
			old = prefs.auto_rec
			if not old and pref_box.toggle_square(
				x, yy, prefs.auto_rec, _("Record and auto split songs"),
				click=gui.level_2_click):
				show_message(_("Please stop playback first before toggling this setting"))
		elif pctl.playing_state == 3:
			old = prefs.auto_rec
			if old and not pref_box.toggle_square(
				x, yy, prefs.auto_rec, _("Record and auto split songs"),
				click=gui.level_2_click):
				show_message(_("Please stop playback first to end current recording"))

		else:
			old = prefs.auto_rec
			prefs.auto_rec = pref_box.toggle_square(
				x, yy, prefs.auto_rec, _("Record and auto split songs"),
				click=gui.level_2_click)
			if prefs.auto_rec != old and prefs.auto_rec:
				show_message(
					_("Tracks will now be recorded."),
					_("Tip: You can press F9 to view the output folder."), mode="info")

		if self.tab == 0:
			if draw.button(
				_("Browse"), (x + w) - round(130 * gui.scale), yy - round(3 * gui.scale),
				press=gui.level_2_click, w=round(100 * gui.scale)):
				self.tab = 1
		elif self.tab == 1:
			if draw.button(
				_("Saved"), (x + w) - round(130 * gui.scale), yy - round(3 * gui.scale),
				press=gui.level_2_click, w=round(100 * gui.scale)):
				self.tab = 0
		gui.level_2_click = False

class RenamePlaylistBox:

	def __init__(self):

		self.x = 300
		self.y = 300
		self.playlist_index = 0

		self.edit_generator = False

	def toggle_edit_gen(self):

		self.edit_generator ^= True
		if self.edit_generator:

			if len(rename_text_area.text) > 0:
				pctl.multi_playlist[self.playlist_index].title = rename_text_area.text

			pl = self.playlist_index
			id = pl_to_id(pl)

			text = pctl.gen_codes.get(id)
			if not text:
				text = ""

			rename_text_area.set_text(text)
			rename_text_area.highlight_none()

			gui.regen_single = rename_playlist_box.playlist_index
			tauon.thread_manager.ready("worker")


		else:
			rename_text_area.set_text(pctl.multi_playlist[self.playlist_index].title)
			rename_text_area.highlight_none()
			# rename_text_area.highlight_all()

	def render(self):

		if gui.level_2_click:
			inp.mouse_click = True
		gui.level_2_click = False

		if inp.key_tab_press:
			self.toggle_edit_gen()

		text_w = ddt.get_text_w(rename_text_area.text, 315)
		min_w = max(250 * gui.scale, text_w + 50 * gui.scale)

		rect = [self.x, self.y, min_w, 37 * gui.scale]
		bg = [40, 40, 40, 255]
		if self.edit_generator:
			bg = [70, 50, 100, 255]
		ddt.text_background_colour = bg

		# Draw background
		ddt.rect(rect, bg)

		# Draw text entry
		rename_text_area.draw(
			rect[0] + 10 * gui.scale, rect[1] + 8 * gui.scale, colours.alpha_grey(250),
			width=350 * gui.scale, font=315)

		# Draw accent
		rect2 = [self.x, self.y + rect[3] - 4 * gui.scale, min_w, 4 * gui.scale]
		ddt.rect(rect2, [255, 255, 255, 60])

		if self.edit_generator:
			pl = self.playlist_index
			id = pl_to_id(pl)
			pctl.gen_codes[id] = rename_text_area.text

			if input_text or key_backspace_press:
				gui.regen_single = rename_playlist_box.playlist_index
				tauon.thread_manager.ready("worker")

				# regenerate_playlist(rename_playlist_box.playlist_index)
			# if gui.gen_code_errors:
			#     del_icon.render(rect[0] + rect[2] - 21 * gui.scale, rect[1] + 10 * gui.scale, (255, 70, 70, 255))
			ddt.text_background_colour = [4, 4, 4, 255]
			hint_rect = [rect[0], rect[1] + round(50 * gui.scale), round(560 * gui.scale), round(300 * gui.scale)]

			if hint_rect[0] + hint_rect[2] > window_size[0]:
				hint_rect[0] = window_size[0] - hint_rect[2]

			ddt.rect(hint_rect, [0, 0, 0, 245])
			xx0 = hint_rect[0] + round(15 * gui.scale)
			xx = hint_rect[0] + round(25 * gui.scale)
			xx2 = hint_rect[0] + round(85 * gui.scale)
			yy = hint_rect[1] + round(10 * gui.scale)

			text_colour = [150, 150, 150, 255]
			title_colour = text_colour
			code_colour = [250, 250, 250, 255]
			hint_colour = [110, 110, 110, 255]

			title_font = 311
			code_font = 311
			hint_font = 310

			# ddt.pretty_rect = hint_rect

			ddt.text(
				(xx0, yy), _("Type codes separated by spaces. Codes will be executed left to right."), text_colour, title_font)
			yy += round(18 * gui.scale)
			ddt.text((xx0, yy), _("Select sources: (default: all playlists)"), title_colour, title_font)
			yy += round(14 * gui.scale)
			ddt.text((xx, yy), "s\"name\"", code_colour, code_font)
			ddt.text((xx2, yy), _("Select source playlist by name"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "self", code_colour, code_font)
			ddt.text((xx2, yy), _("Select playlist itself"), hint_colour, hint_font)

			yy += round(16 * gui.scale)
			ddt.text((xx0, yy), _("Add tracks from sources: (at least 1 required)"), title_colour, title_font)
			yy += round(14 * gui.scale)

			ddt.text((xx, yy), "a\"name\"", code_colour, code_font)
			ddt.text((xx2, yy), _("Search artist name"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "g\"genre\"", code_colour, code_font)
			ddt.text((xx2, yy), _("Search genre"), hint_colour, hint_font)
			# yy += round(12 * gui.scale)
			# ddt.text((xx, yy), "p\"text\"", code_colour, code_font)
			# ddt.text((xx2, yy), "Search filepath segment", hint_colour, hint_font)

			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "f\"terms\"", code_colour, code_font)
			ddt.text((xx2, yy), _("Find / Search / Path"), hint_colour, hint_font)

			# yy += round(12 * gui.scale)
			# ddt.text((xx, yy), "ext\"flac\"", code_colour, code_font)
			# ddt.text((xx2, yy), "Search by file type", hint_colour, hint_font)

			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "a", code_colour, code_font)
			ddt.text((xx2, yy), _("Add all tracks"), hint_colour, hint_font)

			yy += round(16 * gui.scale)
			ddt.text((xx0, yy), _("Filters"), title_colour, title_font)
			yy += round(14 * gui.scale)
			ddt.text((xx, yy), "n123", code_colour, code_font)
			ddt.text((xx2, yy), _("Limit to number of tracks"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "y>1999", code_colour, code_font)
			ddt.text((xx2, yy), _("Year: >, <, ="), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "pc>5", code_colour, code_font)
			ddt.text((xx2, yy), _("Play count: >, <"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "d>120", code_colour, code_font)
			ddt.text((xx2, yy), _("Duration (seconds): >, <"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "rat>3.5", code_colour, code_font)
			ddt.text((xx2, yy), _("Track rating 0-5: >, <, ="), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "l", code_colour, code_font)
			ddt.text((xx2, yy), _("Loved tracks"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "ly", code_colour, code_font)
			ddt.text((xx2, yy), _("Has lyrics"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "ff\"terms\"", code_colour, code_font)
			ddt.text((xx2, yy), _("Search and keep"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "fx\"terms\"", code_colour, code_font)
			ddt.text((xx2, yy), _("Search and exclude"), hint_colour, hint_font)

			# yy += round(12 * gui.scale)
			# ddt.text((xx, yy), "com\"text\"", code_colour, code_font)
			# ddt.text((xx2, yy), "Search in comment", hint_colour, hint_font)
			# yy += round(12 * gui.scale)

			xx += round(260 * gui.scale)
			xx2 += round(260 * gui.scale)
			xx0 += round(260 * gui.scale)
			yy = hint_rect[1] + round(10 * gui.scale)
			yy += round(18 * gui.scale)

			# yy += round(16 * gui.scale)
			ddt.text((xx0, yy), _("Sorters"), title_colour, title_font)
			yy += round(14 * gui.scale)

			ddt.text((xx, yy), "st", code_colour, code_font)
			ddt.text((xx2, yy), _("Shuffle tracks"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "ra", code_colour, code_font)
			ddt.text((xx2, yy), _("Shuffle albums"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "y>", code_colour, code_font)
			ddt.text((xx2, yy), _("Year: >, <"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "d>", code_colour, code_font)
			ddt.text((xx2, yy), _("Duration: >, <"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "pt>", code_colour, code_font)
			ddt.text((xx2, yy), _("Track Playtime: >, <"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "pa>", code_colour, code_font)
			ddt.text((xx2, yy), _("Album playtime: >, <"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "rv", code_colour, code_font)
			ddt.text((xx2, yy), _("Invert tracks"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "rva", code_colour, code_font)
			ddt.text((xx2, yy), _("Invert albums"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "rat>", code_colour, code_font)
			ddt.text((xx2, yy), _("Track rating: >, <"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "rata>", code_colour, code_font)
			ddt.text((xx2, yy), _("Album rating: >, <"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "m>", code_colour, code_font)
			ddt.text((xx2, yy), _("Modification date: >, <"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "path", code_colour, code_font)
			ddt.text((xx2, yy), _("Filepath"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "tn", code_colour, code_font)
			ddt.text((xx2, yy), _("Track number per album"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "ypa", code_colour, code_font)
			ddt.text((xx2, yy), _("Year per artist"), hint_colour, hint_font)
			yy += round(12 * gui.scale)
			ddt.text((xx, yy), "\"artist\">", code_colour, code_font)
			ddt.text((xx2, yy), _("Sort by column name: >, <"), hint_colour, hint_font)

			yy += round(16 * gui.scale)
			ddt.text((xx0, yy), _("Special"), title_colour, title_font)
			yy += round(14 * gui.scale)
			ddt.text((xx, yy), "auto", code_colour, code_font)
			ddt.text((xx2, yy), _("Automatically reload on imports"), hint_colour, hint_font)

			yy += round(24 * gui.scale)
			# xx += round(80 * gui.scale)
			xx2 = xx
			xx2 += ddt.text((xx2, yy), _("Status:"), [90, 90, 90, 255], 212) + round(6 * gui.scale)
			if rename_text_area.text:
				if gui.gen_code_errors:
					if gui.gen_code_errors == "playlist":
						ddt.text((xx2, yy), _("Playlist not found"), [255, 100, 100, 255], 212)
					elif gui.gen_code_errors == "empty":
						ddt.text((xx2, yy), _("Result is empty"), [250, 190, 100, 255], 212)
					elif gui.gen_code_errors == "close":
						ddt.text((xx2, yy), _("Close quotation..."), [110, 110, 110, 255], 212)
					else:
						ddt.text((xx2, yy), "...", [255, 100, 100, 255], 212)
				else:
					ddt.text((xx2, yy), _("OK"), [100, 255, 100, 255], 212)
			else:
				ddt.text((xx2, yy), _("Disabled"), [110, 110, 110, 255], 212)

		# ddt.pretty_rect = None

		# If enter or click outside of box: save and close
		if inp.key_return_press or (key_esc_press and len(editline) == 0) \
				or ((inp.mouse_click or level_2_right_click) and not coll(rect)):
			gui.rename_playlist_box = False

			if self.edit_generator:
				pass
			elif len(rename_text_area.text) > 0:
				if gui.radio_view:
					pctl.radio_playlists[self.playlist_index]["name"] = rename_text_area.text
				else:
					pctl.multi_playlist[self.playlist_index].title = rename_text_area.text
			inp.key_return_press = False

class PlaylistBox:

	def recalc(self):
		self.tab_h = round(25 * gui.scale)
		self.gap = round(2 * gui.scale)

		self.text_offset = 2 * gui.scale
		if gui.scale == 1.25:
			self.text_offset = 3

	def __init__(self):

		self.scroll_on = prefs.old_playlist_box_position
		self.drag = False
		self.drag_source = 0
		self.drag_on = -1

		self.adds = []

		self.indicate_w = round(2 * gui.scale)

		self.lock_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "lock-corner.png", True)
		self.pin_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "dia-pin.png", True)
		self.gen_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "gen-gear.png", True)
		self.spot_icon = asset_loader(scaled_asset_directory, loaded_asset_dc, "spot-playlist.png", True)


		# if gui.scale == 1.25:
		self.tab_h = 0
		self.gap = 0

		self.text_offset = 2 * gui.scale
		self.recalc()

	def draw(self, x, y, w, h):

		global quick_drag

		# ddt.rect_r((x, y, w, h), colours.side_panel_background, True)
		ddt.rect((x, y, w, h), colours.playlist_box_background)
		ddt.text_background_colour = colours.playlist_box_background

		max_tabs = (h - 10 * gui.scale) // (self.gap + self.tab_h)

		tab_title_colour = [230, 230, 230, 255]

		bg_lumi = test_lumi(colours.playlist_box_background)
		light_mode = False

		if bg_lumi < 0.55:
			light_mode = True
			tab_title_colour = [20, 20, 20, 255]

		dark_mode = False
		if bg_lumi > 0.8:
			dark_mode = True

		if light_mode:
			indicate_w = round(3 * gui.scale)
		else:
			indicate_w = round(2 * gui.scale)

		show_scroll = False
		tab_start = x + 10 * gui.scale

		if window_size[0] < 700 * gui.scale:
			tab_start = x + 4 * gui.scale

		if mouse_wheel != 0 and coll((x, y, w, h)):
			self.scroll_on -= mouse_wheel

		self.scroll_on = min(self.scroll_on, len(pctl.multi_playlist) - max_tabs + 1)

		self.scroll_on = max(self.scroll_on, 0)

		if len(pctl.multi_playlist) > max_tabs:
			show_scroll = True
		else:
			self.scroll_on = 0

		if show_scroll:
			tab_start += 15 * gui.scale

		if colours.lm:
			w -= round(6 * gui.scale)
		tab_width = w - tab_start  # - 0 * gui.scale

		# Draw scroll bar
		if show_scroll:
			self.scroll_on = playlist_panel_scroll.draw(x + 2, y + 1, 15 * gui.scale, h, self.scroll_on,
														len(pctl.multi_playlist) - max_tabs + 1)

		draw_pin_indicator = False  # prefs.tabs_on_top

		# if not gui.album_tab_mode:
		#     if key_left_press or key_right_press:
		#         if pctl.active_playlist_viewing < self.scroll_on:
		#             self.scroll_on = pctl.active_playlist_viewing
		#         elif pctl.active_playlist_viewing + 1 > self.scroll_on + max_tabs:
		#             self.scroll_on = (pctl.active_playlist_viewing - max_tabs) + 1

		# Process inputs
		delete_pl = None
		tab_on = 0
		yy = y + 5 * gui.scale
		for i, pl in enumerate(pctl.multi_playlist):

			if tab_on >= max_tabs:
				break
			if i < self.scroll_on:
				continue

			# if not pl.hidden and i in tabs_on_top:
			#     continue

			tab_on += 1

			if coll((tab_start, yy - 1, tab_width, (self.tab_h + 1))):
				if right_click:
					if gui.radio_view:
						radio_tab_menu.activate(i, mouse_position)
					else:
						tab_menu.activate(i, mouse_position)
					gui.tab_menu_pl = i

				if tab_menu.active is False and middle_click:
					delete_pl = i
					# delete_playlist(i)
					# break

				if mouse_up and self.drag and coll_point(mouse_up_position, (tab_start, yy - 1, tab_width, (self.tab_h + 1))):

					# If drag from top bar to side panel, make hidden
					if self.drag_source == 0 and prefs.drag_to_unpin:
						pctl.multi_playlist[self.drag_on].hidden = True

					# Move playlist tab
					if i != self.drag_on and not point_proximity_test(gui.drag_source_position, mouse_position, 10 * gui.scale):
						if key_shift_down:
							pctl.multi_playlist[i].playlist_ids += pctl.multi_playlist[self.drag_on].playlist_ids
							delete_playlist(self.drag_on, force=True)
						else:
							move_playlist(self.drag_on, i)

					gui.update += 1

				# Double click to play
				if mouse_up and pl_to_id(i) == top_panel.tab_d_click_ref == pl_to_id(pctl.active_playlist_viewing) and \
					top_panel.tab_d_click_timer.get() < 0.25 and \
					point_distance(last_click_location, mouse_up_position) < 5 * gui.scale:

					if pctl.playing_state == 2 and pctl.active_playlist_playing == i:
						pctl.play()
					elif pctl.selected_ready() and (pctl.playing_state != 1 or pctl.active_playlist_playing != i):
						pctl.jump(default_playlist[pctl.selected_in_playlist], pl_position=pctl.selected_in_playlist)
				if mouse_up:
					top_panel.tab_d_click_timer.set()
					top_panel.tab_d_click_ref = pl_to_id(i)

				if not draw_pin_indicator:
					if inp.mouse_click:
						switch_playlist(i)
						self.drag_on = i
						self.drag = True
						self.drag_source = 1
						set_drag_source()

				# Process input of dragging tracks onto tab
				if quick_drag is True and mouse_up:
					top_panel.tab_d_click_ref = -1
					top_panel.tab_d_click_timer.force_set(100)
					if (pctl.gen_codes.get(pl_to_id(i)) and "self" not in pctl.gen_codes[pl_to_id(i)]):
						clear_gen_ask(pl_to_id(i))
					quick_drag = False
					modified = False
					gui.pl_update += 1

					for item in shift_selection:
						pctl.multi_playlist[i].playlist_ids.append(default_playlist[item])
						modified = True
					if len(shift_selection) > 0:
						self.adds.append(
							[pctl.multi_playlist[i].uuid_int, len(shift_selection), Timer()])  # ID, num, timer
						modified = True
					if modified:
						pctl.after_import_flag = True
						tauon.thread_manager.ready("worker")
						pctl.notify_change()
						pctl.update_shuffle_pool(pctl.multi_playlist[i].uuid_int)
						tree_view_box.clear_target_pl(i)

			# Toggle hidden flag on click
			if draw_pin_indicator and inp.mouse_click and coll(
					(tab_start + 5 * gui.scale, yy + 3 * gui.scale, 25 * gui.scale, 26 * gui.scale)):
				pl.hidden ^= True

			yy += self.tab_h + self.gap

		# Draw tabs
		# delete_pl = None
		tab_on = 0
		yy = y + 5 * gui.scale
		for i, pl in enumerate(pctl.multi_playlist):

			# if yy + self.tab_h > y + h:
			#     break
			if tab_on >= max_tabs:
				break
			if i < self.scroll_on:
				continue

			tab_on += 1

			name = pl.title
			hidden = pl.hidden

			# Background is insivible by default (for hightlighting if selected)
			bg = [0, 0, 0, 0]

			# Highlight if playlist selected (viewing)
			if i == pctl.active_playlist_viewing or (tab_menu.active and tab_menu.reference == i):
				# bg = [255, 255, 255, 25]

				# Adjust highlight for different background brightnesses
				bg = rgb_add_hls(colours.playlist_box_background, 0, 0.06, 0)
				if light_mode:
					bg = [0, 0, 0, 25]

			# Highlight target playlist when tragging tracks over
			if coll(
				(tab_start + 50 * gui.scale, yy - 1, tab_width - 50 * gui.scale, (self.tab_h + 1))) and quick_drag and not (
				pctl.gen_codes.get(pl_to_id(i)) and "self" not in pctl.gen_codes[pl_to_id(i)]):
				# bg = [255, 255, 255, 15]
				bg = rgb_add_hls(colours.playlist_box_background, 0, 0.04, 0)
				if light_mode:
					bg = [0, 0, 0, 16]

			# Get actual bg from blend for text bg
			real_bg = alpha_blend(bg, colours.playlist_box_background)

			# Draw highlight
			ddt.rect((tab_start, yy - round(1 * gui.scale), tab_width, self.tab_h), bg)

			# Draw title text
			text_start = 10 * gui.scale
			if draw_pin_indicator:
				# text_start = 40 * gui.scale
				text_start = 32 * gui.scale

			if pctl.gen_codes.get(pl_to_id(i), "")[:3] in ["sal", "slt", "spl"]:
				text_start = 28 * gui.scale
				self.spot_icon.render(tab_start + round(7 * gui.scale), yy + round(3 * gui.scale), alpha_mod(tab_title_colour, 170))

			if not pl.hidden and prefs.tabs_on_top:
				cl = [255, 255, 255, 25]

				if light_mode:
					cl = [0, 0, 0, 40]

				xx = tab_start + tab_width - self.lock_icon.w
				self.lock_icon.render(xx, yy, cl)

			text_max_w = tab_width - text_start - 15 * gui.scale
			# if indicator_run_x:
			#     text_max_w = tab_width - (indicator_run_x + text_start + 17 * gui.scale + slide)
			ddt.text(
				(tab_start + text_start, yy + self.text_offset), name, tab_title_colour, 211, max_w=text_max_w, bg=real_bg)

			# Is mouse collided with tab?
			hit = coll((tab_start + 50 * gui.scale, yy - 1, tab_width - 50 * gui.scale, (self.tab_h + 1)))

			# if not prefs.tabs_on_top:
			if i == pctl.active_playlist_playing:

				indicator_colour = colours.title_playing
				if colours.lm:
					indicator_colour = colours.seek_bar_fill

				ddt.rect((tab_start + 0 - 2 * gui.scale, yy - round(1 * gui.scale), indicate_w, self.tab_h), indicator_colour)

			# # If mouse over
			if hit:
				# Draw indicator for dragging tracks
				if quick_drag and pl_is_mut(i):
					ddt.rect((tab_start + tab_width - self.indicate_w, yy, self.indicate_w, self.tab_h), [80, 200, 180, 255])

				# Draw indicators for moving tab
				if self.drag and i != self.drag_on and not point_proximity_test(
					gui.drag_source_position, mouse_position, 10 * gui.scale):
					if key_shift_down:
						ddt.rect(
							(tab_start + tab_width - 4 * gui.scale, yy, self.indicate_w, self.tab_h),
							[80, 160, 200, 255])
					elif i < self.drag_on:
						ddt.rect((tab_start, yy - self.indicate_w, tab_width, self.indicate_w), [80, 160, 200, 255])
					else:
						ddt.rect((tab_start, yy + (self.tab_h - self.indicate_w), tab_width, self.indicate_w), [80, 160, 200, 255])

			elif quick_drag and not point_proximity_test(gui.drag_source_position, mouse_position, 15 * gui.scale):
				for item in shift_selection:
					if len(default_playlist) > item and default_playlist[item] in pl.playlist_ids:
						ddt.rect((tab_start + tab_width - self.indicate_w, yy, self.indicate_w, self.tab_h), [190, 170, 20, 255])
						break
			# Drag red line highlight if playlist is generator playlist
			if quick_drag and not point_proximity_test(gui.drag_source_position, mouse_position, 15 * gui.scale):
				if not pl_is_mut(i):
					ddt.rect((tab_start + tab_width - self.indicate_w, yy, self.indicate_w, self.tab_h), [200, 70, 50, 255])

			# Draw effect of adding tracks to playlist
			if len(self.adds) > 0:
				for k in reversed(range(len(self.adds))):
					if pctl.multi_playlist[i].uuid_int == self.adds[k][0]:
						if self.adds[k][2].get() > 0.3:
							del self.adds[k]
						else:
							ay = yy + 4 * gui.scale
							ay -= 6 * gui.scale * self.adds[k][2].get() / 0.3

							ddt.text(
								(tab_start + tab_width - 10 * gui.scale, int(round(ay)), 1),
								"+" + str(self.adds[k][1]), colours.pluse_colour, 212, bg=real_bg)
							gui.update += 1

							ddt.rect(
								(tab_start + tab_width, yy, self.indicate_w, self.tab_h - self.indicate_w),
								[244, 212, 66, int(255 * self.adds[k][2].get() / 0.3) * -1])

			yy += self.tab_h + self.gap

		if delete_pl is not None:
			# delete_playlist(delete_pl)
			delete_playlist_ask(delete_pl)
			gui.update += 1

		# Create new playlist if drag in blank space after tabs
		rect = (x, yy, w - 10 * gui.scale, h - (yy - y))
		fields.add(rect)

		if coll(rect):
			if quick_drag:
				ddt.rect((tab_start, yy, tab_width, self.indicate_w), [80, 160, 200, 255])
				if mouse_up:
					drop_tracks_to_new_playlist(shift_selection)

			if right_click:
				extra_tab_menu.activate(pctl.active_playlist_viewing)

			# Move tab to end playlist if dragged past end
			if self.drag:
				if mouse_up:
					if key_ctrl_down:
						# Duplicate playlist on ctrl
						gen_dupe(playlist_box.drag_on)
						gui.update += 2
						self.drag = False
					else:
						# If drag from top bar to side panel, make hidden
						if self.drag_source == 0 and prefs.drag_to_unpin:
							pctl.multi_playlist[self.drag_on].hidden = True

						move_playlist(self.drag_on, i)
						gui.update += 2
						self.drag = False
				elif key_ctrl_down:
					ddt.rect((tab_start, yy, tab_width, self.indicate_w), [255, 190, 0, 255])
				else:
					ddt.rect((tab_start, yy, tab_width, self.indicate_w), [80, 160, 200, 255])

class ArtistList:

	def __init__(self):

		self.tab_h = round(60 * gui.scale)
		self.thumb_size = round(55 * gui.scale)

		self.current_artists = []
		self.current_album_counts = {}
		self.current_artist_track_counts = {}

		self.thumb_cache = {}

		self.to_fetch = ""
		self.to_fetch_mbid_a = ""

		self.scroll_position = 0

		self.id_to_load = ""

		self.d_click_timer = Timer()
		self.d_click_ref = -1

		self.click_ref = -1
		self.click_highlight_timer = Timer()

		self.saves = {}

		self.load = False

		self.shown_letters = []

		self.hover_on = "NONE"
		self.hover_timer = Timer(10)

		self.sample_tracks = {}

	def load_img(self, artist):

		filepath = artist_info_box.get_data(artist, get_img_path=True)

		if filepath and os.path.isfile(filepath):

			try:
				g = io.BytesIO()
				g.seek(0)

				im = Image.open(filepath)

				w, h = im.size
				if w != h:
					m = min(w, h)
					im = im.crop((
						round((w - m) / 2),
						round((h - m) / 2),
						round((w + m) / 2),
						round((h + m) / 2),
					))

				im.thumbnail((self.thumb_size, self.thumb_size), Image.Resampling.LANCZOS)

				im.save(g, "PNG")
				g.seek(0)

				wop = rw_from_object(g)
				s_image = IMG_Load_RW(wop, 0)
				texture = SDL_CreateTextureFromSurface(renderer, s_image)
				SDL_FreeSurface(s_image)
				tex_w = pointer(c_int(0))
				tex_h = pointer(c_int(0))
				SDL_QueryTexture(texture, None, None, tex_w, tex_h)
				sdl_rect = SDL_Rect(0, 0)
				sdl_rect.w = int(tex_w.contents.value)
				sdl_rect.h = int(tex_h.contents.value)

				self.thumb_cache[artist] = [texture, sdl_rect]
			except Exception:
				logging.exception("Artist thumbnail processing error")
				self.thumb_cache[artist] = None

		elif artist in prefs.failed_artists:
			self.thumb_cache[artist] = None
		elif not self.to_fetch:

			if prefs.auto_dl_artist_data:
				self.to_fetch = artist
				tauon.thread_manager.ready("worker")

			else:
				self.thumb_cache[artist] = None

	def worker(self):

		if self.load:

			if after_scan:
				return

			self.prep()
			self.load = False
			return

		if self.to_fetch:

			if get_lfm_wait_timer.get() < 2:
				return

			artist = self.to_fetch
			f_artist = filename_safe(artist)
			filename = f_artist + "-lfm.png"
			filename2 = f_artist + "-lfm.txt"
			filename3 = f_artist + "-ftv.jpg"
			filename4 = f_artist + "-dcg.jpg"
			filepath = os.path.join(a_cache_dir, filename)
			filepath2 = os.path.join(a_cache_dir, filename2)
			filepath3 = os.path.join(a_cache_dir, filename3)
			filepath4 = os.path.join(a_cache_dir, filename4)
			got_image = False
			try:
				# Lookup artist info on last.fm
				logging.info("lastfm lookup artist: " + artist)
				mbid = lastfm.artist_mbid(artist)
				get_lfm_wait_timer.set()
				# if data[0] is not False:
				#     #cover_link = data[2]
				#     text = data[1]
				#
				#     if not os.path.exists(filepath2):
				#         f = open(filepath2, 'w', encoding='utf-8')
				#         f.write(text)
				#         f.close()

				if mbid and prefs.enable_fanart_artist:
					save_fanart_artist_thumb(mbid, filepath3, preview=True)
					got_image = True

			except Exception:
				logging.exception("Failed to find image from fanart.tv")

			if not got_image and verify_discogs():
				try:
					save_discogs_artist_thumb(artist, filepath4)
				except Exception:
					logging.exception("Failed to find image from discogs")

			if os.path.exists(filepath3) or os.path.exists(filepath4):
				gui.update += 1
			elif artist not in prefs.failed_artists:
				logging.error("Failed fetching: " + artist)
				prefs.failed_artists.append(artist)

			self.to_fetch = ""

	def prep(self):
		self.scroll_position = 0

		curren_pl_no = id_to_pl(self.id_to_load)
		if curren_pl_no is None:
			return
		current_pl = pctl.multi_playlist[curren_pl_no]

		all = []
		artist_parents = {}
		counts = {}
		play_time = {}
		filtered = 0
		b = 0

		try:

			for item in current_pl.playlist_ids:
				b += 1
				if b % 100 == 0:
					time.sleep(0.001)

				track = pctl.get_track(item)

				if "artists" in track.misc:
					artists = track.misc["artists"]
				else:
					if prefs.artist_list_prefer_album_artist and track.album_artist:
						artists = track.album_artist
					else:
						artists = get_artist_strip_feat(track)

					artists = [x.strip() for x in artists.split(";")]

				pp = 0
				if prefs.artist_list_sort_mode == "play":
					pp = star_store.get(item)

				for artist in artists:

					if artist:

						# Add play time
						if prefs.artist_list_sort_mode == "play":
							p = play_time.get(artist, 0)
							play_time[artist] = p + pp

						# Get a sample track for fallback art
						if artist not in self.sample_tracks:
							self.sample_tracks[artist] = track

						# Confirm to final list if appeared at least 5 times
						# if artist not in all:
						if artist not in counts:
							counts[artist] = 0
						counts[artist] += 1
						if artist not in all:
							if counts[artist] > prefs.artist_list_threshold or len(current_pl.playlist_ids) < 1000:
								all.append(artist)
							else:
								filtered += 1

						if artist not in artist_parents:
							artist_parents[artist] = []
						if track.parent_folder_path not in artist_parents[artist]:
							artist_parents[artist].append(track.parent_folder_path)

			current_album_counts = artist_parents

			if prefs.artist_list_sort_mode == "popular":
				all.sort(key=counts.get, reverse=True)
			elif prefs.artist_list_sort_mode == "play":
				all.sort(key=play_time.get, reverse=True)
			else:
				all.sort(key=lambda y: y.lower().removeprefix("the "))

		except Exception:
			logging.exception("Album scan failure")
			time.sleep(4)
			return

		# Artist-list, album-counts, scroll-position, playlist-length, number ignored
		save = [all, current_album_counts, 0, len(current_pl.playlist_ids), counts, filtered]

		# Scroll to playing artist
		scroll = 0
		if pctl.playing_ready():
			track = pctl.playing_object()
			for i, item in enumerate(save[0]):
				if item == track.artist or item == track.album_artist:
					scroll = i
					break
		save[2] = scroll

		viewing_pl_id = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int
		if viewing_pl_id in self.saves:
			self.saves[viewing_pl_id][2] = self.scroll_position # TODO(Martin): Is saves a list[TauonPlaylist] here? If so, [2] should be .playlist_ids

		self.saves[current_pl.uuid_int] = save
		gui.update += 1

	def locate_artist_letter(self, text):

		if not text or prefs.artist_list_sort_mode != "alpha":
			return

		letter = text[0].lower()
		letter_upper = letter.upper()
		for i, item in enumerate(self.current_artists):
			if item.startswith(("the ", "The ")):
				if len(item) > 4 and (item[4] == letter or item[4] == letter_upper):
					self.scroll_position = i
					break
			elif item and (item[0] == letter or item[0] == letter_upper):
				self.scroll_position = i
				break

		viewing_pl_id = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int
		if pctl.multi_playlist[pctl.active_playlist_viewing].parent_playlist_id:
			viewing_pl_id = pctl.multi_playlist[pctl.active_playlist_viewing].parent_playlist_id
		if viewing_pl_id in self.saves:
			self.saves[viewing_pl_id][2] = self.scroll_position

	def locate_artist(self, track: TrackClass):

		for i, item in enumerate(self.current_artists):
			if item == track.artist or item == track.album_artist or (
					"artists" in track.misc and item in track.misc["artists"]):
				self.scroll_position = i
				break

		viewing_pl_id = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int
		if viewing_pl_id in self.saves:
			self.saves[viewing_pl_id][2] = self.scroll_position

	def draw_card_text_only(self, artist, x, y, w, area, thin_mode, line1_colour, line2_colour, light_mode, bg):

		album_mode = False
		for albums in self.current_album_counts.values():
			if len(albums) > 1:
				album_mode = True
				break

		if not album_mode:
			count = self.current_artist_track_counts[artist]
			if count > 1:
				text = _("{N} tracks").format(N=str(count))
			else:
				text = _("{N} track").format(N=str(count))
		else:
			album_count = len(self.current_album_counts[artist])
			if album_count > 1:
				text = _("{N} tracks").format(N=str(album_count))
			else:
				text = _("{N} track").format(N=str(album_count))

		if gui.preview_artist_loading == artist:
			# . Max 20 chars. Alt: Downloading image, Loading image
			text = _("Downloading data...")

		x_text = round(10 * gui.scale)
		artist_font = 313
		count_font = 312
		extra_text_space = 0
		ddt.text(
			(x_text, y + round(2 * gui.scale)), artist, line1_colour, artist_font,
			extra_text_space + w - x_text - 30 * gui.scale, bg=bg)
		# ddt.text((x_text, y + self.tab_h // 2 - 2 * gui.scale), text, line2_colour, count_font,
		#          extra_text_space + w - x_text - 15 * gui.scale, bg=bg)

	def draw_card_with_thumbnail(self, artist, x, y, w, area, thin_mode, line1_colour, line2_colour, light_mode, bg):

		if artist not in self.thumb_cache:
			self.load_img(artist)

		thumb_x = round(x + 10 * gui.scale)
		x_text = x + self.thumb_size + 19 * gui.scale
		artist_font = 513
		count_font = 312
		extra_text_space = 0
		if thin_mode:
			thumb_x = round(x + 10 * gui.scale)
			x_text = x + self.thumb_size + 17 * gui.scale
			artist_font = 211
			count_font = 311
			extra_text_space = 135 * gui.scale
			thin_mode = True
			area = (4 * gui.scale, y, w - 7 * gui.scale, self.tab_h - 2)
			fields.add(area)

		back_colour = [30, 30, 30, 255]
		back_colour_2 = [27, 27, 27, 255]
		border_colour = [60, 60, 60, 255]
		# if colours.lm:
		#     back_colour = [200, 200, 200, 255]
		#     back_colour_2 = [240, 240, 240, 255]
		#     border_colour = [160, 160, 160, 255]
		rect = (thumb_x, round(y), self.thumb_size, self.thumb_size)

		if thin_mode and coll(area) and is_level_zero() and y + self.tab_h < window_size[1] - gui.panelBY:
			tab_rect = (x, y - round(2 * gui.scale), round(190 * gui.scale), self.tab_h - round(1 * gui.scale))

			for r in subtract_rect(tab_rect, rect):
				r = SDL_Rect(r[0], r[1], r[2], r[3])
				style_overlay.hole_punches.append(r)

			ddt.rect(tab_rect, back_colour_2)
			bg = back_colour_2

		ddt.rect(rect, back_colour)
		ddt.rect(rect, border_colour)

		fields.add(rect)
		if coll(rect) and is_level_zero(True):
			self.hover_any = True

			hover_delay = 0.5
			if gui.compact_artist_list:
				hover_delay = 2

			if gui.preview_artist != artist:
				if self.hover_on != artist:
					self.hover_on = artist
					gui.preview_artist = ""
					self.hover_timer.set()
					gui.delay_frame(hover_delay)
				elif self.hover_timer.get() > hover_delay and not gui.preview_artist_loading:
					gui.preview_artist = ""
					path = artist_info_box.get_data(artist, get_img_path=True)
					if not path:
						gui.preview_artist_loading = artist
						shoot = threading.Thread(
							target=get_artist_preview,
							args=((artist, round(thumb_x + self.thumb_size), round(y))))
						shoot.daemon = True
						shoot.start()

					if path:
						set_artist_preview(path, artist, round(thumb_x + self.thumb_size), round(y))

			if inp.mouse_click:
				self.hover_timer.force_set(-2)
				gui.delay_frame(2 + hover_delay)

		drawn = False
		if artist in self.thumb_cache:
			thumb = self.thumb_cache[artist]
			if thumb is not None:
				thumb[1].x = thumb_x
				thumb[1].y = round(y)
				SDL_RenderCopy(renderer, thumb[0], None, thumb[1])
				drawn = True
				if prefs.art_bg:
					rect = SDL_Rect(thumb_x, round(y), self.thumb_size, self.thumb_size)
					if (rect.y + rect.h) > window_size[1] - gui.panelBY:
						diff = (rect.y + rect.h) - (window_size[1] - gui.panelBY)
						rect.h -= round(diff)
					style_overlay.hole_punches.append(rect)
		if not drawn:
			track = self.sample_tracks.get(artist)
			if track:
				tauon.gall_ren.render(track, (round(thumb_x), round(y)), self.thumb_size)

		if thin_mode:
			text = artist[:2].title()
			if text not in self.shown_letters:
				ww = ddt.get_text_w(text, 211)
				ddt.rect(
					(thumb_x + round(1 * gui.scale), y + self.tab_h - 20 * gui.scale, ww + 5 * gui.scale, 13 * gui.scale),
					[20, 20, 20, 255])
				ddt.text(
					(thumb_x + 3 * gui.scale, y + self.tab_h - 23 * gui.scale), text, [240, 240, 240, 255], 210,
					bg=[20, 20, 20, 255])
				self.shown_letters.append(text)

		# Draw labels
		if not thin_mode or (coll(area) and is_level_zero() and y + self.tab_h < window_size[1] - gui.panelBY):

			album_mode = False
			for albums in self.current_album_counts.values():
				if len(albums) > 1:
					album_mode = True
					break

			if not album_mode:
				count = self.current_artist_track_counts[artist]
				if count > 1:
					text = _("{N} tracks").format(N=str(count))
				else:
					text = _("{N} track").format(N=str(count))
			else:
				album_count = len(self.current_album_counts[artist])
				if album_count > 1:
					text = _("{N} tracks").format(N=str(album_count))
				else:
					text = _("{N} track").format(N=str(album_count))

			if gui.preview_artist_loading == artist:
				# . Max 20 chars. Alt: Downloading image, Loading image
				text = _("Downloading data...")

			ddt.text(
				(x_text, y + self.tab_h // 2 - 19 * gui.scale), artist, line1_colour, artist_font,
				extra_text_space + w - x_text - 30 * gui.scale, bg=bg)
			ddt.text(
				(x_text, y + self.tab_h // 2 - 2 * gui.scale), text, line2_colour, count_font,
				extra_text_space + w - x_text - 15 * gui.scale, bg=bg)

	def draw_card(self, artist, x, y, w):

		area = (4 * gui.scale, y, w - 26 * gui.scale, self.tab_h - 2)
		if prefs.artist_list_style == 2:
			area = (4 * gui.scale, y, w - 26 * gui.scale, self.tab_h - 1)

		fields.add(area)

		light_mode = False
		line1_colour = [235, 235, 235, 255]
		line2_colour = [255, 255, 255, 120]
		fade_max = 50

		thin_mode = False
		if gui.compact_artist_list:
			thin_mode = True
			line2_colour = [115, 115, 115, 255]

		elif test_lumi(colours.side_panel_background) < 0.55 and not thin_mode:
			light_mode = True
			fade_max = 20
			line1_colour = [35, 35, 35, 255]
			line2_colour = [100, 100, 100, 255]

		# Fade on click
		bg = colours.side_panel_background
		if not thin_mode:

			if coll(area) and is_level_zero(
					True):  # or pctl.get_track(default_playlist[pctl.playlist_view_position]).artist == artist:
				ddt.rect(area, [50, 50, 50, 50])
				bg = alpha_blend([50, 50, 50, 50], colours.side_panel_background)
			else:

				fade = 0
				t = self.click_highlight_timer.get()
				if self.click_ref == artist and (t < 2.2 or artist_list_menu.active):

					if t < 1.9 or artist_list_menu.active:
						fade = fade_max
					else:
						fade = fade_max - round((t - 1.9) / 0.3 * fade_max)

					gui.update += 1
					ddt.rect(area, [50, 50, 50, fade])

				bg = alpha_blend([50, 50, 50, fade], colours.side_panel_background)

		if prefs.artist_list_style == 1:
			self.draw_card_with_thumbnail(artist, x, y, w, area, thin_mode, line1_colour, line2_colour, light_mode, bg)
		else:
			self.draw_card_text_only(artist, x, y, w, area, thin_mode, line1_colour, line2_colour, light_mode, bg)

		if coll(area) and mouse_position[1] < window_size[1] - gui.panelBY:
			if inp.mouse_click:
				if self.click_ref != artist:
					pctl.playlist_view_position = 0
					pctl.selected_in_playlist = 0
				self.click_ref = artist

				double_click = False
				if self.d_click_timer.get() < 0.4 and self.d_click_ref == artist:
					double_click = True

				self.click_highlight_timer.set()

				if pctl.multi_playlist[pctl.active_playlist_viewing].parent_playlist_id and \
						pctl.multi_playlist[pctl.active_playlist_viewing].title.startswith("Artist:"):
					create_artist_pl(artist, replace=True)


				blocks = []
				current_block = []

				in_artist = False
				this_artist = artist.casefold()
				last_ref = None
				on = 0

				for i in range(len(default_playlist)):
					track = pctl.get_track(default_playlist[i])
					if track.artist.casefold() == this_artist or track.album_artist.casefold() == this_artist or (
							"artists" in track.misc and artist in track.misc["artists"]):
						# Matchin artist
						if not in_artist:
							in_artist = True
							last_ref = track
							current_block.append(i)

						elif (last_ref and track.album != last_ref.album) or track.parent_folder_path != last_ref.parent_folder_path:
							current_block.append(i)
							last_ref = track
					# Not matching
					elif in_artist:
						blocks.append(current_block)
						current_block = []
						in_artist = False

				if current_block:
					blocks.append(current_block)
					current_block = []

				#logging.info(blocks)
				# return

				# block_starts = []
				# current = False
				# for i in range(len(default_playlist)):
				#     track = pctl.get_track(default_playlist[i])
				#     if current is False:
				#         if track.artist == artist or track.album_artist == artist or (
				#                 'artists' in track.misc and artist in track.misc['artists']):
				#             block_starts.append(i)
				#             current = True
				#     else:
				#         if track.artist != artist and track.album_artist != artist or (
				#                 'artists' in track.misc and artist in track.misc['artists']):
				#             current = False
				#
				# if not block_starts:
				#     logging.info("No matching artists found in playlist")
				#     return

				if not blocks:
					return

				#select = block_starts[0]

				# if len(block_starts) > 1:
				#     if -1 < pctl.selected_in_playlist < len(default_playlist):
				#         if pctl.selected_in_playlist in block_starts:
				#             scroll_hide_timer.set()
				#             gui.frame_callback_list.append(TestTimer(0.9))
				#             if block_starts[-1] == pctl.selected_in_playlist:
				#                 pass
				#             else:
				#                 select = block_starts[block_starts.index(pctl.selected_in_playlist) + 1]

				gui.pl_update += 1

				self.click_highlight_timer.set()

				select = blocks[0][0]

				if double_click:
					# Stat first artist track in playlist

					pctl.jump(default_playlist[select], pl_position=select)
					pctl.playlist_view_position = select
					pctl.selected_in_playlist = select
					shift_selection.clear()
					self.d_click_timer.force_set(10)
				else:
					# Goto next artist section in playlist
					c = pctl.selected_in_playlist
					next = False
					track = pctl.get_track_in_playlist(c, -1)
					if track is None:
						logging.error("Index out of range!")
						pctl.selected_in_playlist = 0
						return
					if track.artist.casefold != artist.casefold:
						pctl.selected_in_playlist = 0
						pctl.playlist_view_position = 0
					if len(blocks) == 1:
						block = blocks[0]
						if len(block) > 1:
							if c < block[0] or c >= block[-1]:
								select = block[0]
								toast(_("First of artist's albums ({N} albums)")
									.format(N=len(block)))
							else:
								select = block[-1]
								toast(_("Last of artist's albums ({N} albums)")
									.format(N=len(block)))
					else:
						select = None
						for bb, block in enumerate(blocks):
							for i, al in enumerate(block):
								if al <= c:
									continue
								next = True
								if i == 0:
									select = al
									if len(block) > 1:
										toast(_("Start of location {N} of {T} ({Nb} albums)")
											.format(N=bb + 1, T=len(blocks), Nb=len(block)))
									else:
										toast(_("Location {N} of {T}")
											.format(N=bb + 1, T=len(blocks)))
									break

							if next and not select:
								select = block[-1]
								if len(block) > 1:
									toast(_("End of location {N} of {T} ({Nb} albums)")
										.format(N=bb + 1, T=len(blocks), Nb=len(block)))
								else:
									toast(_("Location {N} of {T}")
										.format(N=bb, T=len(blocks)))
								break
							if select:
								break
					if not select:
						select = blocks[0][0]
						if len(blocks[0]) > 1:
							if len(blocks) > 1:
								toast(_("Start of location 1 of {N} ({Nb} albums)")
									.format(N=len(blocks), Nb=len(blocks[0])))
							else:
								toast(_("Location 1 of {N} ({Nb} albums)")
									.format(N=len(blocks), Nb=len(blocks[0])))
						else:
							toast(_("Location 1 of {N}")
								.format(N=len(blocks)))

					pctl.playlist_view_position = select
					pctl.selected_in_playlist = select
					self.d_click_ref = artist
					self.d_click_timer.set()
					if album_mode:
						goto_album(select)

			if middle_click:
				self.click_ref = artist
				self.click_highlight_timer.set()
				create_artist_pl(artist)

			if right_click:
				self.click_ref = artist
				self.click_highlight_timer.set()

				artist_list_menu.activate(in_reference=artist)

	def render(self, x, y, w, h):

		if prefs.artist_list_style == 1:
			self.tab_h = round(60 * gui.scale)
		else:
			self.tab_h = round(22 * gui.scale)

		viewing_pl_id = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int

		# use parent playlst is set
		if pctl.multi_playlist[pctl.active_playlist_viewing].parent_playlist_id:

			# test if parent still exists
			new = id_to_pl(pctl.multi_playlist[pctl.active_playlist_viewing].parent_playlist_id)
			if new is None or not pctl.multi_playlist[pctl.active_playlist_viewing].title.startswith("Artist:"):
				pctl.multi_playlist[pctl.active_playlist_viewing].parent_playlist_id = ""
			else:
				viewing_pl_id = pctl.multi_playlist[pctl.active_playlist_viewing].parent_playlist_id

		if viewing_pl_id in self.saves:
			self.current_artists = self.saves[viewing_pl_id][0]
			self.current_album_counts = self.saves[viewing_pl_id][1]
			self.current_artist_track_counts = self.saves[viewing_pl_id][4]
			self.scroll_position = self.saves[viewing_pl_id][2]

			if self.saves[viewing_pl_id][3] != len(pctl.multi_playlist[id_to_pl(viewing_pl_id)].playlist_ids):
				del self.saves[viewing_pl_id]
				return

		else:

			# if self.current_pl != viewing_pl_id:
			self.id_to_load = viewing_pl_id
			if not self.load:
				# self.prep()
				self.current_artists = []
				self.current_album_counts = []
				self.current_artist_track_counts = {}
				self.load = True
				tauon.thread_manager.ready("worker")

		area = (x, y, w, h)
		area2 = (x + 1, y, w - 3, h)

		ddt.rect(area, colours.side_panel_background)
		ddt.text_background_colour = colours.side_panel_background

		if coll(area) and mouse_wheel:
			mx = 1
			if prefs.artist_list_style == 2:
				mx = 3
			self.scroll_position -= mouse_wheel * mx
		self.scroll_position = max(self.scroll_position, 0)

		range = (h // self.tab_h) - 1

		whole_rage = math.floor(h // self.tab_h)

		if range > 4 and self.scroll_position > len(self.current_artists) - range:
			self.scroll_position = len(self.current_artists) - range

		if len(self.current_artists) <= whole_rage:
			self.scroll_position = 0

		fields.add(area2)
		scroll_x = x + w - 18 * gui.scale
		if colours.lm:
			scroll_x = x + w - 22 * gui.scale
		if (coll(area2) or artist_list_scroll.held) and not pref_box.enabled:
			scroll_width = 15 * gui.scale
			inset = 0
			if gui.compact_artist_list:
				pass
				# scroll_width = round(6 * gui.scale)
				# scroll_x += round(9 * gui.scale)
			else:
				self.scroll_position = artist_list_scroll.draw(
					scroll_x, y + 1, scroll_width, h, self.scroll_position,
					len(self.current_artists) - range, r_click=right_click,
					jump_distance=35, extend_field=6 * gui.scale)

		if not self.current_artists:
			text = _("No artists in playlist")

			if default_playlist:
				text = _("Artist threshold not met")
			if self.load:
				text = _("Loading Artist List...")
				if loading_in_progress or transcode_list or after_scan:
					text = _("Busy...")

			ddt.text(
				(x + w // 2, y + (h // 7), 2), text, alpha_mod(colours.side_bar_line2, 100), 212,
				max_w=w - 17 * gui.scale)

		yy = y + 12 * gui.scale

		i = int(self.scroll_position)

		if viewing_pl_id in self.saves:
			self.saves[viewing_pl_id][2] = self.scroll_position

		prefetch_mode = False
		prefetch_distance = 22

		self.shown_letters.clear()

		self.hover_any = False

		for i, artist in enumerate(self.current_artists[i:], start=i):

			if not prefetch_mode:
				self.draw_card(artist, x, round(yy), w)

				yy += self.tab_h

				if yy - y > h - 24 * gui.scale:
					prefetch_mode = True
					continue

			if prefetch_mode:
				if prefs.artist_list_style == 2:
					break
				prefetch_distance -= 1
				if prefetch_distance < 1:
					break
				if artist not in self.thumb_cache:
					self.load_img(artist)
					break

		if not self.hover_any:
			gui.preview_artist = ""
			self.hover_timer.force_set(10)
			artist_preview_render.show = False
			self.hover_on = False

class TreeView:

	def __init__(self):

		self.trees = {}  # Per playlist tree
		self.rows = []  # For display (parsed from tree)
		self.rows_id = ""

		self.opens = {}  # Folders clicks to show per playlist

		self.scroll_positions = {}

		# Recursive gen_rows vars
		self.count = 0
		self.depth = 0

		self.background_processing = False
		self.d_click_timer = Timer(100)
		self.d_click_id = ""

		self.menu_selected = ""
		self.folder_colour_cache = {}
		self.dragging_name = ""

		self.force_opens = []
		self.click_drag_source = None

		self.tooltip_on = ""
		self.tooltip_timer = Timer(10)

		self.lock_pl = None

		# self.bold_colours = ColourGenCache(0.6, 0.7)

	def clear_all(self):
		self.rows_id = ""
		self.trees.clear()

	def collapse_all(self):
		pl_id = pl_to_id(pctl.active_playlist_viewing)

		if self.lock_pl:
			pl_id = self.lock_pl

		opens = self.opens.get(pl_id)
		if opens is None:
			opens = []
			self.opens[pl_id] = opens

		opens.clear()
		self.rows_id = ""

	def clear_target_pl(self, pl_number, pl_id=None):

		if pl_id is None:
			pl_id = pl_to_id(pl_number)

		if gui.lsp and prefs.left_panel_mode == "folder view":

			if pl_id in self.trees:
				if not self.background_processing:
					self.background_processing = True
					shoot_dl = threading.Thread(target=self.gen_tree, args=[pl_id])
					shoot_dl.daemon = True
					shoot_dl.start()
		elif pl_id in self.trees:
			del self.trees[pl_id]

	def show_track(self, track: TrackClass) -> None:

		if track is None:
			return

		# Get tree and opened folder data for this playlist
		pl_id = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int
		opens = self.opens.get(pl_id)
		if opens is None:
			opens = []
			self.opens[pl_id] = opens

		tree = self.trees.get(pl_id)
		if not tree:
			return

		scroll_position = self.scroll_positions.get(pl_id)
		if scroll_position is None:
			scroll_position = 0

		# Clear all opened folders
		opens.clear()

		# Set every folder in path as opened
		path = ""
		crumbs = track.parent_folder_path.split("/")[1:]
		for c in crumbs:
			path += "/" + c
			opens.append(path)

		# Regenerate row display
		self.gen_rows(tree, opens)

		# Locate and set scroll position to playing folder
		for i, row in enumerate(self.rows):
			if row[1] + "/" + row[0] == track.parent_folder_path:

				scroll_position = i - 5
				scroll_position = max(scroll_position, 0)
				break

		max_scroll = len(self.rows) - ((window_size[0] - (gui.panelY + gui.panelBY)) // round(22 * gui.scale))
		scroll_position = min(scroll_position, max_scroll)
		scroll_position = max(scroll_position, 0)

		self.scroll_positions[pl_id] = scroll_position

		gui.update_layout()
		gui.update += 1

	def get_pl_id(self):
		if self.lock_pl:
			return self.lock_pl
		return pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int

	def render(self, x, y, w, h):

		global quick_drag

		pl_id = self.get_pl_id()

		tree = self.trees.get(pl_id)

		# Generate tree data if not done yet
		if tree is None:
			if not self.background_processing:
				self.background_processing = True
				shoot_dl = threading.Thread(target=self.gen_tree, args=[pl_id])
				shoot_dl.daemon = True
				shoot_dl.start()

			self.playlist_id_on = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int

		opens = self.opens.get(pl_id)
		if opens is None:
			opens = []
			self.opens[pl_id] = opens

		scroll_position = self.scroll_positions.get(pl_id)
		if scroll_position is None:
			scroll_position = 0

		area = (x, y, w, h)
		fields.add(area)
		ddt.rect(area, colours.side_panel_background)
		ddt.text_background_colour = colours.side_panel_background

		if self.background_processing and self.rows_id != pl_id:
			ddt.text(
				(x + w // 2, y + (h // 7), 2), _("Loading Folder Tree..."), alpha_mod(colours.side_bar_line2, 100),
				212, max_w=w - 17 * gui.scale)
			return

		# if not tree or not self.rows:
		#     ddt.text((x + w // 2, y + (h // 7), 2), _("Folder Tree"), alpha_mod(colours.side_bar_line2, 100),
		#              212, max_w=w - 17 * gui.scale)
		#     return
		if not tree:
			ddt.text(
				(x + w // 2, y + (h // 7), 2), _("Folder Tree"), alpha_mod(colours.side_bar_line2, 100),
				212, max_w=w - 17 * gui.scale)
			return

		if self.rows_id != pl_id:
			if not self.background_processing:
				self.gen_rows(tree, opens)
				self.rows_id = pl_id
				max_scroll = len(self.rows) - (h // round(22 * gui.scale))
				scroll_position = min(scroll_position, max_scroll)

			else:
				return

		if not self.rows:
			ddt.text(
				(x + w // 2, y + (h // 7), 2), _("Folder Tree"), alpha_mod(colours.side_bar_line2, 100),
				212, max_w=w - 17 * gui.scale)
			return

		yy = y + round(11 * gui.scale)
		xx = x + round(22 * gui.scale)

		spacing = round(21 * gui.scale)
		max_scroll = len(self.rows) - (h // round(22 * gui.scale))

		mouse_in = coll(area)

		# Mouse wheel scrolling
		if mouse_in and mouse_wheel:
			scroll_position += mouse_wheel * -2
			scroll_position = max(scroll_position, 0)
			scroll_position = min(scroll_position, max_scroll)

		focused = is_level_zero()

		# Draw scroll bar
		if mouse_in or tree_view_scroll.held:
			scroll_position = tree_view_scroll.draw(
				x + w - round(12 * gui.scale), y + 1, round(11 * gui.scale), h,
				scroll_position,
				max_scroll, r_click=right_click, jump_distance=40)

		self.scroll_positions[pl_id] = scroll_position

		# Draw folder rows
		playing_track = pctl.playing_object()
		max_w = w - round(45 * gui.scale)

		light_mode = test_lumi(colours.side_panel_background) < 0.5
		semilight_mode = test_lumi(colours.side_panel_background) < 0.8

		for i, item in enumerate(self.rows):

			if i < scroll_position:
				continue

			if yy > y + h - spacing:
				break

			target = item[1] + "/" + item[0]

			inset = item[2] * round(10 * gui.scale)
			rect = (xx + inset - round(15 * gui.scale), yy, max_w - inset + round(15 * gui.scale), spacing - 1)
			fields.add(rect)

			# text_colour = [255, 255, 255, 100]
			text_colour = rgb_add_hls(colours.side_panel_background, 0, 0.35, -0.15)

			box_colour = [200, 100, 50, 255]

			if semilight_mode:
				text_colour = [255, 255, 255, 180]

			if light_mode:
				text_colour = [0, 0, 0, 200]

			full_folder_path = item[1] + "/" + item[0]

			# Hold highlight while menu open
			if (folder_tree_menu.active or folder_tree_stem_menu.active) and full_folder_path == self.menu_selected:
				text_colour = [255, 255, 255, 170]
				if semilight_mode:
					text_colour = (255, 255, 255, 255)
				if light_mode:
					text_colour = [0, 0, 0, 255]

			# Hold highlight while dragging folder
			if quick_drag and not point_proximity_test(gui.drag_source_position, mouse_position, 15):
				if shift_selection:
					if pctl.get_track(pctl.multi_playlist[id_to_pl(pl_id)].playlist_ids[shift_selection[0]]).fullpath.startswith(
							full_folder_path + "/") and self.dragging_name and item[0].endswith(self.dragging_name):
						text_colour = (255, 255, 255, 230)
						if semilight_mode:
							text_colour = (255, 255, 255, 255)
						if light_mode:
							text_colour = [0, 0, 0, 255]

			# Set highlight colours if folder is playing
			if 0 < pctl.playing_state < 3 and playing_track:
				if playing_track.parent_folder_path == full_folder_path or full_folder_path + "/" in playing_track.fullpath:
					text_colour = [255, 255, 255, 225]
					box_colour = [140, 220, 20, 255]
					if semilight_mode:
						text_colour = (255, 255, 255, 255)
					if light_mode:
						text_colour = [0, 0, 0, 255]

			if right_click:
				mouse_in = coll(rect) and is_level_zero(False)
			else:
				mouse_in = coll(rect) and focused and not (
							quick_drag and not point_proximity_test(gui.drag_source_position, mouse_position, 15))

			if mouse_in and not tree_view_scroll.held:

				if middle_click:
					stem_to_new_playlist(full_folder_path)

				elif right_click:

					if item[3]:

						for p, id in enumerate(pctl.multi_playlist[id_to_pl(pl_id)].playlist_ids):
							if msys:
								if pctl.get_track(id).fullpath.startswith(target.lstrip("/")):
									folder_tree_menu.activate(in_reference=id)
									self.menu_selected = full_folder_path
									break
							elif pctl.get_track(id).fullpath.startswith(target):
								folder_tree_menu.activate(in_reference=id)
								self.menu_selected = full_folder_path
								break
					elif msys:
						folder_tree_stem_menu.activate(in_reference=full_folder_path.lstrip("/"))
						self.menu_selected = full_folder_path.lstrip("/")
					else:
						folder_tree_stem_menu.activate(in_reference=full_folder_path)
						self.menu_selected = full_folder_path

				elif inp.mouse_click:
					# quick_drag = True

					if not self.click_drag_source:
						self.click_drag_source = item
						set_drag_source()

				elif mouse_up and self.click_drag_source == item:
					# Click tree level folder to open/close branch

					if target not in opens:
						opens.append(target)
					else:
						for s in reversed(range(len(opens))):
							if opens[s].startswith(target):
								del opens[s]

					if item[3]:

						# Locate the first track of folder in playlist
						track_id = None
						for p, id in enumerate(default_playlist):
							if msys:
								if pctl.get_track(id).fullpath.startswith(target.lstrip("/")):
									track_id = id
									break
							elif pctl.get_track(id).fullpath.startswith(target):
								track_id = id
								break
						else:  # Fallback to folder name if full-path not found (hack for networked items)
							for p, id in enumerate(default_playlist):
								if pctl.get_track(id).parent_folder_name == item[0]:
									track_id = id
									break

						if track_id is not None:
							# Single click base folder to locate in playlist
							if self.d_click_timer.get() > 0.5 or self.d_click_id != target:
								pctl.show_current(select=True, index=track_id, no_switch=True, highlight=True, folder_list=False)
								self.d_click_timer.set()
								self.d_click_id = target

							# Double click base folder to play
							else:
								pctl.jump(track_id)

					# Regenerate display rows after clicking
					self.gen_rows(tree, opens)

			# Highlight folder text on mouse over
			if (mouse_in and not mouse_down) or item == self.click_drag_source:
				text_colour = (255, 255, 255, 235)
				if semilight_mode:
					text_colour = (255, 255, 255, 255)
				if light_mode:
					text_colour = [0, 0, 0, 255]

			# Render folder name text
			if item[4] > 50:
				font = 514
				text_label_colour = text_colour  # self.bold_colours.get(full_folder_path)
			else:
				font = 414
				text_label_colour = text_colour

			if mouse_in:
				tw = ddt.get_text_w(item[0], font)

				if self.tooltip_on != item:
					self.tooltip_on = item
					self.tooltip_timer.set()
					gui.frame_callback_list.append(TestTimer(0.6))

				if tw > max_w - inset and self.tooltip_on == item and self.tooltip_timer.get() >= 0.6:
					rect = (xx + inset, yy - 2 * gui.scale, tw + round(20 * gui.scale), 20 * gui.scale)
					ddt.rect(rect, ddt.text_background_colour)
					ddt.text((xx + inset, yy), item[0], text_label_colour, font)
				else:
					ddt.text((xx + inset, yy), item[0], text_label_colour, font, max_w=max_w - inset)
			else:
				ddt.text((xx + inset, yy), item[0], text_label_colour, font, max_w=max_w - inset)

			# # Draw inset bars
			# for m in range(item[2] + 1):
			#     if m == 0:
			#         continue
			#     colour = (255, 255, 255, 20)
			#     if semilight_mode:
			#         colour = (255, 255, 255, 30)
			#     if light_mode:
			#         colour = (0, 0, 0, 60)
			#
			#     if i > 0 and self.rows[i - 1][2] == m - 1:  # the top one needs to be slightly lower lower
			#         ddt.rect((x + (12 * m) + 2, yy - round(1 * gui.scale), round(1 * gui.scale), round(17 * gui.scale)), colour, True)
			#     else:
			#         ddt.rect((x + (12 * m) + 2, yy - round(5 * gui.scale), round(1 * gui.scale), round(21 * gui.scale)), colour, True)

			if prefs.folder_tree_codec_colours:
				box_colour = self.folder_colour_cache.get(full_folder_path)
				if box_colour is None:
					box_colour = (150, 150, 150, 255)

			# Draw indicator box and +/- icons next to folder name
			if item[3]:
				rect = (xx + inset - round(9 * gui.scale), yy + round(7 * gui.scale), round(4 * gui.scale),
						round(4 * gui.scale))
				if light_mode or semilight_mode:
					border = round(1 * gui.scale)
					ddt.rect((rect[0] - border, rect[1] - border, rect[2] + border * 2, rect[3] + border * 2), [0, 0, 0, 150])
				ddt.rect(rect, box_colour)

			elif True:
				if not mouse_in or tree_view_scroll.held:
					# text_colour = [255, 255, 255, 50]
					text_colour = rgb_add_hls(colours.side_panel_background, 0, 0.2, -0.10)
					if semilight_mode:
						text_colour = [255, 255, 255, 70]
					if light_mode:
						text_colour = [0, 0, 0, 70]
				if target in opens:
					ddt.text((xx + inset - round(7 * gui.scale), yy + round(1 * gui.scale), 2), "-", text_colour, 19)
				else:
					ddt.text((xx + inset - round(7 * gui.scale), yy + round(1 * gui.scale), 2), "+", text_colour, 19)

			yy += spacing

		if self.click_drag_source and not point_proximity_test(gui.drag_source_position, mouse_position, 15) and \
			default_playlist is pctl.multi_playlist[id_to_pl(pl_id)].playlist_ids:
			quick_drag = True
			global playlist_hold
			playlist_hold = True

			self.dragging_name = self.click_drag_source[0]
			logging.info(self.dragging_name)

			if "/" in self.dragging_name:
				self.dragging_name = os.path.basename(self.dragging_name)

			shift_selection.clear()
			set_drag_source()
			for p, id in enumerate(pctl.multi_playlist[id_to_pl(pl_id)].playlist_ids):
				if msys:
					if pctl.get_track(id).fullpath.startswith(
							self.click_drag_source[1].lstrip("/") + "/" + self.click_drag_source[0] + "/"):
						shift_selection.append(p)
				elif pctl.get_track(id).fullpath.startswith(f"{self.click_drag_source[1]}/{self.click_drag_source[0]}/"):
					shift_selection.append(p)
			self.click_drag_source = None

		if self.dragging_name and not quick_drag:
			self.dragging_name = ""
		if not mouse_down:
			self.click_drag_source = None

	def gen_row(self, tree_point, path, opens):

		for item in tree_point:
			p = path + "/" + item[1]
			self.count += 1
			enter_level = False
			if len(tree_point) > 1 or path in self.force_opens:  # Ignore levels that are only a single folder wide

				if path in opens or self.depth == 0 or path in self.force_opens:  # Only show if parent stem is open, but always show the root displayed folders

					# If there is a single base folder in subfolder, combine the path and show it in upper level
					if len(item[0]) == 1 and len(item[0][0][0]) == 1 and len(item[0][0][0][0][0]) == 0:
						self.rows.append(
							[item[1] + "/" + item[0][0][1] + "/" + item[0][0][0][0][1], path, self.depth, True, len(item[0])])
					elif len(item[0]) == 1 and len(item[0][0][0]) == 0:
						self.rows.append([item[1] + "/" + item[0][0][1], path, self.depth, True, len(item[0])])

					# Add normal base folder type
					else:
						self.rows.append([item[1], path, self.depth, len(item[0]) == 0, len(item[0])])  # Folder name, folder path, depth, is bottom

					# If folder is open and has only one subfolder, mark that subfolder as open
					if len(item[0]) == 1 and (p in opens or p in self.force_opens):
						self.force_opens.append(p + "/" + item[0][0][1])

				self.depth += 1
				enter_level = True

			self.gen_row(item[0], p, opens)

			if enter_level:
				self.depth -= 1

	def gen_rows(self, tree, opens):
		self.count = 0
		self.depth = 0
		self.rows.clear()
		self.force_opens.clear()

		self.gen_row(tree, "", opens)

		gui.update_layout()
		gui.update += 1

	def gen_tree(self, pl_id):
		pl_no = id_to_pl(pl_id)
		if pl_no is None:
			return

		playlist = pctl.multi_playlist[pl_no].playlist_ids
		# Generate list of all unique folder paths
		paths = []
		z = 5000
		for p in playlist:

			z += 1
			if z > 1000:
				time.sleep(0.01)  # Throttle thread
				z = 0
			track = pctl.get_track(p)
			path = track.parent_folder_path
			if path not in paths:
				paths.append(path)
				self.folder_colour_cache[path] = format_colours.get(track.file_ext)

		# Genterate tree from folder paths
		tree = []
		news = []
		for path in paths:
			z += 1
			if z > 5000:
				time.sleep(0.01)  # Throttle thread
				z = 0
			split_path = path.split("/")
			on = tree
			for level in split_path:
				if not level:
					continue
				# Find if level already exists
				for sub_level in on:
					if sub_level[1] == level:
						on = sub_level[0]
						break
				else:  # Create new level
					new = [[], level]
					news.append(new)
					on.append(new)
					on = new[0]

		self.trees[pl_id] = tree
		self.rows_id = ""
		self.background_processing = False
		gui.update += 1
		tauon.wake()

class QueueBox:

	def recalc(self):
		self.tab_h = 34 * gui.scale
	def __init__(self):

		self.dragging = None
		self.fq = []
		self.drag_start_y = 0
		self.drag_start_top = 0
		self.tab_h = 0
		self.scroll_position = 0
		self.right_click_id = None
		self.d_click_ref = None
		self.recalc()

		queue_menu.add(MenuItem(_("Remove This"), self.right_remove_item, show_test=self.queue_remove_show))
		queue_menu.add(MenuItem(_("Play Now"), self.play_now, show_test=self.queue_remove_show))
		queue_menu.add(MenuItem("Auto-Stop Here", self.toggle_auto_stop, self.toggle_auto_stop_deco, show_test=self.queue_remove_show))

		queue_menu.add(MenuItem("Pause Queue", self.toggle_pause, queue_pause_deco))
		queue_menu.add(MenuItem(_("Clear Queue"), clear_queue, queue_deco, hint="Alt+Shift+Q"))

		queue_menu.add(MenuItem(_("↳ Except for This"), self.clear_queue_crop, show_test=self.except_for_this_show_test))

		queue_menu.add(MenuItem(_("Queue to New Playlist"), self.make_as_playlist, queue_deco))
		# queue_menu.add("Finish Playing Album", finish_current, finish_current_deco)

	def except_for_this_show_test(self, _):
		return self.queue_remove_show(_) and test_shift(_)

	def make_as_playlist(self):

		if pctl.force_queue:
			playlist = []
			for item in pctl.force_queue:

				if item.type == 0:
					playlist.append(item.track_id)
				else:

					pl = id_to_pl(item.playlist_id)
					if pl is None:
						logging.info("Lost the target playlist")
						continue

					pp = pctl.multi_playlist[pl].playlist_ids

					i = item.position  # = pctl.playlist_playing_position + 1

					parts = []
					album_parent_path = pctl.get_track(item.track_id).parent_folder_path

					while i < len(pp):
						if pctl.get_track(pp[i]).parent_folder_path != album_parent_path:
							break

						parts.append((pp[i], i))
						i += 1

					for part in parts:
						playlist.append(part[0])

			pctl.multi_playlist.append(
				pl_gen(
					title=_("Queued Tracks"),
					playlist_ids=copy.deepcopy(playlist),
					hide_title=False))

	def drop_tracks_insert(self, insert_position):

		global quick_drag

		if not shift_selection:
			return

		# remove incomplete album from queue
		if insert_position == 0 and pctl.force_queue and pctl.force_queue[0].album_stage == 1:
			split_queue_album(pctl.force_queue[0].uuid_int)

		playlist_index = pctl.active_playlist_viewing
		playlist_id = pl_to_id(pctl.active_playlist_viewing)

		main_track_position = shift_selection[0]
		main_track_id = default_playlist[main_track_position]
		quick_drag = False

		if len(shift_selection) > 1:

			# if shift selection contains only same folder
			for position in shift_selection:
				if pctl.get_track(default_playlist[position]).parent_folder_path != pctl.get_track(
						main_track_id).parent_folder_path or key_ctrl_down:
					break
			else:
				# Add as album type
				pctl.force_queue.insert(
					insert_position, queue_item_gen(main_track_id, main_track_position, playlist_id, 1))
				return

		if len(shift_selection) == 1:
			pctl.force_queue.insert(insert_position, queue_item_gen(main_track_id, main_track_position, playlist_id))
		else:
			# Add each track
			for position in reversed(shift_selection):
				pctl.force_queue.insert(
					insert_position, queue_item_gen(default_playlist[position], position, playlist_id))

	def clear_queue_crop(self):

		save = False
		for item in pctl.force_queue:
			if item.uuid_int == self.right_click_id:
				save = item
				break

		clear_queue()
		if save:
			pctl.force_queue.append(save)

	def play_now(self):

		queue_item = None
		queue_index = 0
		for i, item in enumerate(pctl.force_queue):
			if item.uuid_int == self.right_click_id:
				queue_item = item
				queue_index = i
				break
		else:
			return

		del pctl.force_queue[queue_index]
		# [trackid, position, pl_id, type, album_stage, uid_gen(), auto_stop]

		if pctl.force_queue and pctl.force_queue[0].album_stage == 1:
			split_queue_album(None)

		target_track_id = queue_item.track_id

		pl = id_to_pl(queue_item.playlist_id)
		if pl is not None:
			pctl.active_playlist_playing = pl

		if target_track_id not in pctl.playing_playlist():
			pctl.advance()
			return

		pctl.jump(target_track_id, queue_item.position)

		if queue_item.type == 1:  # is album type
			queue_item.album_stage = 1  # set as partway playing
			pctl.force_queue.insert(0, queue_item)

	def toggle_auto_stop(self) -> None:

		for item in pctl.force_queue:
			if item.uuid_int == self.right_click_id:
				item.auto_stop ^= True
				break

	def toggle_auto_stop_deco(self):

		enabled = False
		for item in pctl.force_queue:
			if item.uuid_int == self.right_click_id:
				if item.auto_stop:
					enabled = True
					break

		if enabled:
			return [colours.menu_text, colours.menu_background, _("Cancel Auto-Stop")]
		return [colours.menu_text, colours.menu_background, _("Auto-Stop")]

	def queue_remove_show(self, id: int) -> bool:

		if self.right_click_id is not None:
			return True
		return False

	def right_remove_item(self) -> None:

		if self.right_click_id is None:
			show_message(_("Eh?"))

		for u in reversed(range(len(pctl.force_queue))):
			if pctl.force_queue[u].uuid_int == self.right_click_id:
				del pctl.force_queue[u]
				gui.pl_update += 1
				break
		else:
			show_message(_("Looks like it's gone now anyway"))

	def toggle_pause(self) -> None:
		pctl.pause_queue ^= True

	def draw_card(
		self,
		x: int, y: int,
		w: int, h: int,
		yy: int,
		track: TrackClass, fqo: TauonQueueItem,
		draw_back: bool = False, draw_album_indicator: bool = True,
	) -> None:

		# text_colour = [230, 230, 230, 255]
		bg = colours.queue_background

		# if fq[i].type == 0:

		rect = (x + 13 * gui.scale, yy, w - 28 * gui.scale, self.tab_h)

		if draw_back:
			ddt.rect(rect, colours.queue_card_background)
			bg = colours.queue_card_background

		text_colour1 = rgb_add_hls(bg, 0, 0.28, -0.15)  # [255, 255, 255, 70]
		text_colour2 = [255, 255, 255, 230]
		if test_lumi(bg) < 0.2:
			text_colour1 = [0, 0, 0, 130]
			text_colour2 = [0, 0, 0, 230]

		tauon.gall_ren.render(track, (rect[0] + 4 * gui.scale, rect[1] + 4 * gui.scale), round(28 * gui.scale))

		ddt.rect((rect[0] + 4 * gui.scale, rect[1] + 4 * gui.scale, 26, 26), [0, 0, 0, 6])

		line = track.album
		if fqo.type == 0:
			line = track.title

		if not line:
			line = clean_string(track.filename)

		line2y = yy + 14 * gui.scale

		artist_line = track.artist
		if fqo.type == 1 and track.album_artist:
			artist_line = track.album_artist

		if fqo.type == 0 and not artist_line:
			line2y -= 7 * gui.scale

		ddt.text(
			(rect[0] + (40 * gui.scale), yy - 1 * gui.scale), artist_line, text_colour1, 210,
			max_w=rect[2] - 60 * gui.scale, bg=bg)

		ddt.text(
			(rect[0] + (40 * gui.scale), line2y), line, text_colour2, 211,
			max_w=rect[2] - 60 * gui.scale, bg=bg)

		if draw_album_indicator:
			if fqo.type == 1:
				if fqo.album_stage == 0:
					ddt.rect((rect[0] + rect[2] - 5 * gui.scale, rect[1], 5 * gui.scale, rect[3]), [220, 130, 20, 255])
				else:
					ddt.rect((rect[0] + rect[2] - 5 * gui.scale, rect[1], 5 * gui.scale, rect[3]), [140, 220, 20, 255])

			if fqo.auto_stop:
				xx = rect[0] + rect[2] - 9 * gui.scale
				if fqo.type == 1:
					xx -= 11 * gui.scale
				ddt.rect((xx, rect[1] + 5 * gui.scale, 7 * gui.scale, 7 * gui.scale), [230, 190, 0, 255])

	def draw(self, x: int, y: int, w: int, h: int):

		yy = y

		yy += round(4 * gui.scale)

		sep_colour = alpha_blend([255, 255, 255, 11], colours.queue_background)

		if y > gui.panelY + 10 * gui.scale:  # Draw fancy light mode border
			gui.queue_frame_draw = y
		# else:
		#     if not colours.lm:
		#         ddt.rect((x, y, w, 3 * gui.scale),  colours.queue_background, True)

		yy += round(3 * gui.scale)

		box_rect = (x, yy - 6 * gui.scale, w, h)
		ddt.rect(box_rect, colours.queue_background)
		ddt.text_background_colour = colours.queue_background

		if coll(box_rect) and quick_drag and not pctl.force_queue:
			ddt.rect(box_rect, [255, 255, 255, 2])
			ddt.text_background_colour = alpha_blend([255, 255, 255, 2], ddt.text_background_colour)

		# if y < gui.panelY * 2:
		#     ddt.rect((x, y - 3 * gui.scale, w, 30 * gui.scale), colours.queue_background, True)

		if h > 40 * gui.scale:
			if not pctl.force_queue:
				if quick_drag:
					text = _("Add to Queue")
				else:
					text = _("Queue")
				ddt.text((x + (w // 2), y + 15 * gui.scale, 2), text, alpha_mod(colours.index_text, 200), 212)

		qb_right_click = 0

		if coll(box_rect):
			# Update scroll position
			self.scroll_position += mouse_wheel * -1
			self.scroll_position = max(self.scroll_position, 0)

			if right_click:
				qb_right_click = 1

		# text_colour = [255, 255, 255, 91]
		text_colour = rgb_add_hls(colours.queue_background, 0, 0.3, -0.15)
		if test_lumi(colours.queue_background) < 0.2:
			text_colour = [0, 0, 0, 200]

		line = _("Up Next:")
		if pctl.force_queue:
			# line = "Queue"
			ddt.text((x + (10 * gui.scale), yy + 2 * gui.scale), line, text_colour, 211)

		yy += 7 * gui.scale

		if len(pctl.force_queue) < 3:
			self.scroll_position = 0

		# Draw square dots to indicate view has been scrolled down
		if self.scroll_position > 0:
			ds = 3 * gui.scale
			gp = 4 * gui.scale

			ddt.rect((x + int(w / 2), yy, ds, ds), [230, 190, 0, 255])
			ddt.rect((x + int(w / 2), yy + gp, ds, ds), [230, 190, 0, 255])
			ddt.rect((x + int(w / 2), yy + gp + gp, ds, ds), [230, 190, 0, 255])

		# Draw pause icon
		if pctl.pause_queue:
			ddt.rect((x + w - 24 * gui.scale, yy + 2 * gui.scale, 3 * gui.scale, 9 * gui.scale), [230, 190, 0, 255])
			ddt.rect((x + w - 19 * gui.scale, yy + 2 * gui.scale, 3 * gui.scale, 9 * gui.scale), [230, 190, 0, 255])

		yy += 6 * gui.scale

		yy += 10 * gui.scale

		i = 0

		# Get new copy of queue if not dragging
		if not self.dragging:
			self.fq = copy.deepcopy(pctl.force_queue)
		else:
			# gui.update += 1
			gui.update_on_drag = True

		# End drag if mouse not in correct state for it
		if not mouse_down and not mouse_up:
			self.dragging = None

		if not queue_menu.active:
			self.right_click_id = None

		fq = self.fq

		list_top = yy

		i = self.scroll_position

		# Limit scroll distance
		if i > len(fq):
			self.scroll_position = len(fq)
			i = self.scroll_position

		showed_indicator = False
		list_extends = False
		x1 = x + 13 * gui.scale  # highlight position
		w1 = w - 28 * gui.scale - 10 * gui.scale

		while i < len(fq) + 1:

			# Stop drawing if past window
			if yy > window_size[1] - gui.panelBY - gui.panelY - (50 * gui.scale):
				list_extends = True
				break

			# Calculate drag collision box. Special case for first and last which extend out in y direction
			h_rect = (x + 13 * gui.scale, yy, w - 28 * gui.scale, self.tab_h + 3 * gui.scale)
			if i == len(fq):
				h_rect = (x + 13 * gui.scale, yy, w - 28 * gui.scale, self.tab_h + 3 * gui.scale + 1000 * gui.scale)
			if i == 0:
				h_rect = (
				0, yy - 1000 * gui.scale, w - 28 * gui.scale + 10000, self.tab_h + 3 * gui.scale + 1000 * gui.scale)

			if self.dragging is not None and coll(h_rect) and mouse_up:

				ob = None
				for u in reversed(range(len(pctl.force_queue))):

					if pctl.force_queue[u].uuid_int == self.dragging:
						ob = pctl.force_queue[u]
						pctl.force_queue[u] = None
						break

				else:
					self.dragging = None

				if self.dragging:
					pctl.force_queue.insert(i, ob)
					self.dragging = None

				for u in reversed(range(len(pctl.force_queue))):
					if pctl.force_queue[u] is None:
						del pctl.force_queue[u]
						gui.pl_update += 1
						continue

					# Reset album in flag if not first item
					if pctl.force_queue[u].album_stage == 1:
						if u != 0:
							pctl.force_queue[u].album_stage = 0

				inp.mouse_click = False
				self.draw(x, y, w, h)
				return

			if i > len(fq) - 1:
				break

			track = pctl.get_track(fq[i].track_id)

			rect = (x + 13 * gui.scale, yy, w - 28 * gui.scale, self.tab_h)

			if inp.mouse_click and coll(rect):

				self.dragging = fq[i].uuid_int
				self.drag_start_y = mouse_position[1]
				self.drag_start_top = yy

				if d_click_timer.get() < 1:

					if self.d_click_ref == fq[i].uuid_int:

						pl = id_to_pl(fq[i].uuid_int)
						if pl is not None:
							switch_playlist(pl)

						pctl.show_current(playing=False, highlight=True, index=fq[i].track_id)
						self.d_click_ref = None
				# else:
				self.d_click_ref = fq[i].uuid_int

				d_click_timer.set()

			if self.dragging and coll(h_rect):
				yy += self.tab_h
				yy += 4 * gui.scale

			if qb_right_click and coll(rect):
				self.right_click_id = fq[i].uuid_int
				qb_right_click = 2

			if middle_click and coll(rect):
				pctl.force_queue.remove(fq[i])
				gui.pl_update += 1

			if fq[i].uuid_int == self.dragging:
				# ddt.rect_r(rect, [22, 22, 22, 255], True)
				pass
			else:

				db = False
				if fq[i].uuid_int == self.right_click_id:
					db = True

				self.draw_card(x, y, w, h, yy, track, fq[i], db)

				# Drag tracks from main playlist and insert ------------
				if quick_drag:

					if x < mouse_position[0] < x + w:

						y1 = yy - 4 * gui.scale
						y2 = y1
						h1 = self.tab_h // 2
						if i == 0:
							# Extend up if first element
							y1 -= 5 * gui.scale
							h1 += 10 * gui.scale

						insert_position = None

						if y1 < mouse_position[1] < y1 + h1:
							ddt.rect((x1, yy - 2 * gui.scale, w1, 2 * gui.scale), colours.queue_drag_indicator_colour)
							showed_indicator = True

							if mouse_up:
								insert_position = i

						elif y2 < mouse_position[1] < y2 + self.tab_h + 5 * gui.scale:
							ddt.rect(
								(x1, yy + self.tab_h + 2 * gui.scale, w1, 2 * gui.scale),
								colours.queue_drag_indicator_colour)
							showed_indicator = True

							if mouse_up:
								insert_position = i + 1

						if insert_position is not None:
							self.drop_tracks_insert(insert_position)

				# -----------------------------------------
				yy += self.tab_h
				yy += 4 * gui.scale

			i += 1

		# Show drag marker if mouse holding below list
		if quick_drag and not list_extends and not showed_indicator and fq and mouse_position[
			1] > yy - 4 * gui.scale and coll(box_rect):
			yy -= self.tab_h
			yy -= 4 * gui.scale
			ddt.rect((x1, yy + self.tab_h + 2 * gui.scale, w1, 2 * gui.scale), colours.queue_drag_indicator_colour)
			yy += self.tab_h
			yy += 4 * gui.scale

		yy += 15 * gui.scale
		if fq:
			ddt.rect((x, yy, w, 3 * gui.scale), sep_colour)
		yy += 11 * gui.scale

		# Calculate total queue duration
		duration = 0
		tracks = 0

		for item in fq:
			if item.type == 0:
				duration += pctl.get_track(item.track_id).length
				tracks += 1
			else:
				pl = id_to_pl(item.playlist_id)
				if pl is not None:
					playlist = pctl.multi_playlist[pl].playlist_ids
					i = item.position

					album_parent_path = pctl.get_track(item.track_id).parent_folder_path

					playing_track = pctl.playing_object()

					if pl == pctl.active_playlist_playing \
					and item.album_stage \
					and playing_track and playing_track.parent_folder_path == album_parent_path:
						i = pctl.playlist_playing_position + 1

					if item.track_id not in playlist:
						continue
					if i > len(playlist) - 1:
						continue
					if playlist[i] != item.track_id:
						i = playlist.index(item.track_id)

					while i < len(playlist):
						if pctl.get_track(playlist[i]).parent_folder_path != album_parent_path:
							break

						duration += pctl.get_track(playlist[i]).length
						tracks += 1
						i += 1

		# Show total duration text "n Tracks [0:00:00]"
		if tracks and fq:
			if tracks < 2:
				line = _("{N} Track").format(N=str(tracks)) + " [" + get_hms_time(duration) + "]"
				ddt.text((x + 12 * gui.scale, yy), line, text_colour, 11.5, bg=colours.queue_background)
			else:
				line = _("{N} Tracks").format(N=str(tracks)) + " [" + get_hms_time(duration) + "]"
				ddt.text((x + 12 * gui.scale, yy), line, text_colour, 11.5, bg=colours.queue_background)



		if self.dragging:

			fqo = None
			for item in fq:
				if item.uuid_int == self.dragging:
					fqo = item
					break
			else:
				self.dragging = False

			if self.dragging:
				yyy = self.drag_start_top + (mouse_position[1] - self.drag_start_y)
				yyy = max(yyy, list_top)
				track = pctl.get_track(fqo.track_id)
				self.draw_card(x, y, w, h, yyy, track, fqo, draw_back=True)

		# Drag and drop tracks from main playlist into queue
		if quick_drag and mouse_up and coll(box_rect) and shift_selection:
			self.drop_tracks_insert(len(fq))

		# Right click context menu in blank space
		if qb_right_click:
			if qb_right_click == 1:
				self.right_click_id = None
			queue_menu.activate(position=mouse_position)

class MetaBox:

	def l_panel(self, x, y, w, h, track, top_border=True):

		if not track:
			return

		border_colour = [255, 255, 255, 30]
		line1_colour = [255, 255, 255, 235]
		line2_colour = [255, 255, 255, 200]
		if test_lumi(colours.gallery_background) < 0.55:
			border_colour = [0, 0, 0, 30]
			line1_colour = [0, 0, 0, 200]
			line2_colour = [0, 0, 0, 230]

		rect = (x, y, w, h)

		ddt.rect(rect, colours.gallery_background)
		if top_border:
			ddt.rect((x, y, w, round(1 * gui.scale)), border_colour)
		else:
			ddt.rect((x, y + h - round(1 * gui.scale), w, round(1 * gui.scale)), border_colour)

		ddt.text_background_colour = colours.gallery_background

		insert = round(9 * gui.scale)
		border = round(2 * gui.scale)

		compact_mode = False
		if w < h * 1.9:
			compact_mode = True

		art_rect = [x + insert - 2 * gui.scale, y + insert, h - insert * 2 + 1 * gui.scale,
					h - insert * 2 + 1 * gui.scale]

		if compact_mode:
			art_rect[0] = x + round(w / 2 - art_rect[2] / 2) - round(1 * gui.scale)  # - border

		border_rect = (
		art_rect[0] - border, art_rect[1] - border, art_rect[2] + (border * 2), art_rect[3] + (border * 2))

		if (inp.mouse_click or right_click) and is_level_zero(False):
			if coll(border_rect):
				if inp.mouse_click:
					album_art_gen.cycle_offset(target_track)
				if right_click:
					picture_menu.activate(in_reference=target_track)
			elif coll(rect):
				if inp.mouse_click:
					pctl.show_current()
				if right_click:
					showcase_menu.activate(track)

		ddt.rect(border_rect, border_colour)
		ddt.rect(art_rect, colours.gallery_background)
		album_art_gen.display(track, (art_rect[0], art_rect[1]), (art_rect[2], art_rect[3]))

		fields.add(border_rect)
		if coll(border_rect) and is_level_zero(True):
			showc = album_art_gen.get_info(target_track)
			art_metadata_overlay(
				art_rect[0] + art_rect[2] + 2 * gui.scale, art_rect[1] + art_rect[3] + 12 * gui.scale, showc)

		if not compact_mode:
			text_x = border_rect[0] + border_rect[2] + round(10 * gui.scale)
			max_w = w - (border_rect[2] + 28 * gui.scale)
			yy = y + round(15 * gui.scale)

			ddt.text((text_x, yy), track.title, line1_colour, 316, max_w=max_w)
			yy += round(20 * gui.scale)
			ddt.text((text_x, yy), track.artist, line2_colour, 14, max_w=max_w)
			yy += round(30 * gui.scale)
			ddt.text((text_x, yy), track.album, line2_colour, 14, max_w=max_w)
			yy += round(20 * gui.scale)
			ddt.text((text_x, yy), track.date, line2_colour, 14, max_w=max_w)

			gui.showed_title = True

	def lyrics(self, x, y, w, h, track: TrackClass):

		ddt.rect((x, y, w, h), colours.side_panel_background)
		ddt.text_background_colour = colours.side_panel_background

		if not track:
			return

		# Test for show lyric menu on right ckick
		if coll((x + 10, y, w - 10, h)):
			if right_click:  # and 3 > pctl.playing_state > 0:
				gui.force_showcase_index = -1
				showcase_menu.activate(track)

		# Test for scroll wheel input
		if mouse_wheel != 0 and coll((x + 10, y, w - 10, h)):
			lyrics_ren_mini.lyrics_position += mouse_wheel * 30 * gui.scale
			if lyrics_ren_mini.lyrics_position > 0:
				lyrics_ren_mini.lyrics_position = 0
				lyric_side_top_pulse.pulse()

			gui.update += 1

		tw, th = ddt.get_text_wh(track.lyrics + "\n", 15, w - 50 * gui.scale, True)

		oth = th

		th -= h
		th += 25 * gui.scale  # Empty space buffer at end

		if lyrics_ren_mini.lyrics_position * -1 > th:
			lyrics_ren_mini.lyrics_position = th * -1
			if oth > h:
				lyric_side_bottom_pulse.pulse()

		scroll_w = 15 * gui.scale
		if gui.maximized:
			scroll_w = 17 * gui.scale

		lyrics_ren_mini.lyrics_position = mini_lyrics_scroll.draw(
			x + w - 17 * gui.scale, y, scroll_w, h,
			lyrics_ren_mini.lyrics_position * -1, th,
			jump_distance=160 * gui.scale) * -1

		margin = 10 * gui.scale
		if colours.lm:
			margin += 1 * gui.scale

		lyrics_ren_mini.render(
			pctl.track_queue[pctl.queue_step], x + margin,
			y + lyrics_ren_mini.lyrics_position + 13 * gui.scale,
			w - 50 * gui.scale,
			None, 0)

		ddt.rect((x, y + h - 1, w, 1), colours.side_panel_background)

		lyric_side_top_pulse.render(x, y, w - round(17 * gui.scale), 16 * gui.scale)
		lyric_side_bottom_pulse.render(x, y + h, w - round(17 * gui.scale), 15 * gui.scale, bottom=True)

	def draw(self, x, y, w, h, track=None):

		ddt.rect((x, y, w, h), colours.side_panel_background)

		if not track:
			return

		# Test for show lyric menu on right ckick
		if coll((x + 10, y, w - 10, h)):
			if right_click:  # and 3 > pctl.playing_state > 0:
				gui.force_showcase_index = -1
				showcase_menu.activate(track)

		if pctl.playing_state == 0:
			if not prefs.meta_persists_stop and not prefs.meta_shows_selected and not prefs.meta_shows_selected_always:
				return

		if h < 15:
			return

		# Check for lyrics if auto setting
		test_auto_lyrics(track)

		# # Draw lyrics if avaliable
		# if prefs.show_lyrics_side and pctl.track_queue \
		#             and track.lyrics != "" and h > 45 * gui.scale and w > 200 * gui.scale:
		#
		#     self.lyrics(x, y, w, h, track)

		# Draw standard metadata
		if len(pctl.track_queue) > 0:

			if pctl.playing_state == 0:
				if not prefs.meta_persists_stop and not prefs.meta_shows_selected and not prefs.meta_shows_selected_always:
					return

			ddt.text_background_colour = colours.side_panel_background

			if coll((x + 10, y, w - 10, h)):
				# Click area to jump to current track
				if inp.mouse_click:
					pctl.show_current()
					gui.update += 1

			title = ""
			album = ""
			artist = ""
			ext = ""
			date = ""
			genre = ""

			margin = x + 10 * gui.scale
			if colours.lm:
				margin += 2 * gui.scale

			text_width = w - 25 * gui.scale
			tr = None

			# if pctl.playing_state < 3:

			if pctl.playing_state == 0 and prefs.meta_persists_stop:
				tr = pctl.master_library[pctl.track_queue[pctl.queue_step]]
			if pctl.playing_state == 0 and prefs.meta_shows_selected:

				if -1 < pctl.selected_in_playlist < len(pctl.multi_playlist[pctl.active_playlist_viewing].playlist_ids):
					tr = pctl.get_track(pctl.multi_playlist[pctl.active_playlist_viewing].playlist_ids[pctl.selected_in_playlist])

			if prefs.meta_shows_selected_always and pctl.playing_state != 3:
				if -1 < pctl.selected_in_playlist < len(pctl.multi_playlist[pctl.active_playlist_viewing].playlist_ids):
					tr = pctl.get_track(pctl.multi_playlist[pctl.active_playlist_viewing].playlist_ids[pctl.selected_in_playlist])

			if tr is None:
				tr = pctl.playing_object()
			if tr is None:
				return

			title = tr.title
			album = tr.album
			artist = tr.artist
			ext = tr.file_ext
			if ext == "JELY":
				ext = "Jellyfin"
				if "container" in tr.misc:
					ext = tr.misc.get("container", "") + " | Jellyfin"
			if tr.lyrics:
				ext += ","
			date = tr.date
			genre = tr.genre

			if not title and not artist:
				title = pctl.tag_meta

			if h > 58 * gui.scale:

				block_y = y + 7 * gui.scale

				if not prefs.show_side_art:
					block_y += 3 * gui.scale

				if title != "":
					ddt.text(
						(margin, block_y + 2 * gui.scale), title, colours.side_bar_line1, fonts.side_panel_line1,
						max_w=text_width)
				if artist != "":
					ddt.text(
						(margin, block_y + 23 * gui.scale), artist, colours.side_bar_line2, fonts.side_panel_line2,
						max_w=text_width)

				gui.showed_title = True

				if h > 140 * gui.scale:

					block_y = y + 80 * gui.scale
					if artist != "":
						ddt.text(
							(margin, block_y), album, colours.side_bar_line2,
							fonts.side_panel_line2, max_w=text_width)

					if not genre == date == "":
						line = date
						if genre != "":
							if line != "":
								line += " | "
							line += genre

						ddt.text(
							(margin, block_y + 20 * gui.scale), line, colours.side_bar_line2,
							fonts.side_panel_line2, max_w=text_width)

					if ext != "":
						if ext == "SPTY":
							ext = "Spotify"
						if ext == "RADIO":
							ext = radiobox.playing_title
						sp = ddt.text(
							(margin, block_y + 40 * gui.scale), ext, colours.side_bar_line2,
							fonts.side_panel_line2, max_w=text_width)

						if tr and tr.lyrics:
							if draw_internel_link(
								margin + sp + 6 * gui.scale, block_y + 40 * gui.scale, "Lyrics", colours.side_bar_line2, fonts.side_panel_line2):
								prefs.show_lyrics_showcase = True
								enter_showcase_view(track_id=tr.index)

class PictureRender:

	def __init__(self):
		self.show = False
		self.path = ""

		self.image_data = None
		self.texture = None
		self.sdl_rect = None
		self.size = (0, 0)

	def load(self, path, box_size=None):

		if not os.path.isfile(path):
			logging.warning("NO PICTURE FILE TO LOAD")
			return

		g = io.BytesIO()
		g.seek(0)

		im = Image.open(path)
		if box_size is not None:
			im.thumbnail(box_size, Image.Resampling.LANCZOS)

		im.save(g, "BMP")
		g.seek(0)
		self.image_data = g
		logging.info("Save BMP to memory")
		self.size = im.size[0], im.size[1]

	def draw(self, x, y):

		if self.show is False:
			return

		if self.image_data is not None:
			if self.texture is not None:
				SDL_DestroyTexture(self.texture)

			# Convert raw image to sdl texture
			#logging.info("Create Texture")
			wop = rw_from_object(self.image_data)
			s_image = IMG_Load_RW(wop, 0)
			self.texture = SDL_CreateTextureFromSurface(renderer, s_image)
			SDL_FreeSurface(s_image)
			tex_w = pointer(c_int(0))
			tex_h = pointer(c_int(0))
			SDL_QueryTexture(self.texture, None, None, tex_w, tex_h)
			self.sdl_rect = SDL_Rect(round(x), round(y))
			self.sdl_rect.w = int(tex_w.contents.value)
			self.sdl_rect.h = int(tex_h.contents.value)
			self.image_data = None

		if self.texture is not None:
			self.sdl_rect.x = round(x)
			self.sdl_rect.y = round(y)
			SDL_RenderCopy(renderer, self.texture, None, self.sdl_rect)
			style_overlay.hole_punches.append(self.sdl_rect)

class PictureRender:

	def __init__(self):
		self.show = False
		self.path = ""

		self.image_data = None
		self.texture = None
		self.sdl_rect = None
		self.size = (0, 0)

	def load(self, path, box_size=None):

		if not os.path.isfile(path):
			logging.warning("NO PICTURE FILE TO LOAD")
			return

		g = io.BytesIO()
		g.seek(0)

		im = Image.open(path)
		if box_size is not None:
			im.thumbnail(box_size, Image.Resampling.LANCZOS)

		im.save(g, "BMP")
		g.seek(0)
		self.image_data = g
		logging.info("Save BMP to memory")
		self.size = im.size[0], im.size[1]

	def draw(self, x, y):

		if self.show is False:
			return

		if self.image_data is not None:
			if self.texture is not None:
				SDL_DestroyTexture(self.texture)

			# Convert raw image to sdl texture
			#logging.info("Create Texture")
			wop = rw_from_object(self.image_data)
			s_image = IMG_Load_RW(wop, 0)
			self.texture = SDL_CreateTextureFromSurface(renderer, s_image)
			SDL_FreeSurface(s_image)
			tex_w = pointer(c_int(0))
			tex_h = pointer(c_int(0))
			SDL_QueryTexture(self.texture, None, None, tex_w, tex_h)
			self.sdl_rect = SDL_Rect(round(x), round(y))
			self.sdl_rect.w = int(tex_w.contents.value)
			self.sdl_rect.h = int(tex_h.contents.value)
			self.image_data = None

		if self.texture is not None:
			self.sdl_rect.x = round(x)
			self.sdl_rect.y = round(y)
			SDL_RenderCopy(renderer, self.texture, None, self.sdl_rect)
			style_overlay.hole_punches.append(self.sdl_rect)

class RadioThumbGen:
	def __init__(self):
		self.cache = {}
		self.requests = []
		self.size = 100

	def loader(self):

		while self.requests:
			item = self.requests[0]
			del self.requests[0]
			station = item[0]
			size = item[1]
			key = (station["title"], size)
			src = None
			filename = filename_safe(station["title"])

			cache_path = os.path.join(r_cache_dir, filename + ".jpg")
			if os.path.isfile(cache_path):
				src = open(cache_path, "rb")
			else:
				cache_path = os.path.join(r_cache_dir, filename + ".png")
				if os.path.isfile(cache_path):
					src = open(cache_path, "rb")
				else:
					cache_path = os.path.join(r_cache_dir, filename)
					if os.path.isfile(cache_path):
						src = open(cache_path, "rb")

			if src:
				pass
				#logging.info("found cached")
			elif station.get("icon") and station["icon"] not in prefs.radio_thumb_bans:
				try:
					r = requests.get(station.get("icon"), headers={"User-Agent": t_agent}, timeout=5, stream=True)
					if r.status_code != 200 or int(r.headers.get("Content-Length", 0)) > 2000000:
						raise Exception("Error get radio thumb")
				except Exception:
					logging.exception("error get radio thumb")
					self.cache[key] = [0]
					if station.get("icon") and station.get("icon") not in prefs.radio_thumb_bans:
						prefs.radio_thumb_bans.append(station.get("icon"))
					continue
				src = io.BytesIO()
				length = 0
				for chunk in r.iter_content(1024):
					src.write(chunk)
					length += len(chunk)
					if length > 2000000:
						scr = None
				if src is None:
					self.cache[key] = [0]
					if station.get("icon") and station.get("icon") not in prefs.radio_thumb_bans:
						prefs.radio_thumb_bans.append(station.get("icon"))
					continue
				src.seek(0)
				with open(cache_path, "wb") as f:
					f.write(src.read())
				src.seek(0)
			else:
				# logging.info("no icon")
				self.cache[key] = [0]
				continue

			try:
				im = Image.open(src)
				if im.mode != "RGBA":
					im = im.convert("RGBA")
			except Exception:
				logging.exception("malform get radio thumb")
				self.cache[key] = [0]
				if station.get("icon") and station.get("icon") not in prefs.radio_thumb_bans:
					prefs.radio_thumb_bans.append(station.get("icon"))
				continue
			if src is not None:
				src.close()

			im = im.resize((size, size), Image.Resampling.LANCZOS)
			g = io.BytesIO()
			g.seek(0)
			im.save(g, "PNG")
			g.seek(0)
			wop = rw_from_object(g)
			s_image = IMG_Load_RW(wop, 0)
			self.cache[key] = [2, None, None, s_image]
			gui.update += 1

	def draw(self, station, x, y, w):
		if not station.get("title"):
			return 0
		key = (station["title"], w)

		r = self.cache.get(key)
		if r is None:
			if len(self.requests) < 3:
				self.requests.append((station, w))
				tauon.thread_manager.ready("radio-thumb")
			return 0
		if r[0] == 2:
			texture = SDL_CreateTextureFromSurface(renderer, r[3])
			SDL_FreeSurface(r[3])
			tex_w = pointer(c_int(0))
			tex_h = pointer(c_int(0))
			SDL_QueryTexture(texture, None, None, tex_w, tex_h)
			sdl_rect = SDL_Rect(0, 0)
			sdl_rect.w = int(tex_w.contents.value)
			sdl_rect.h = int(tex_h.contents.value)
			r[2] = texture
			r[1] = sdl_rect
			r[0] = 1
		if r[0] == 1:
			r[1].x = round(x)
			r[1].y = round(y)
			SDL_RenderCopy(renderer, r[2], None, r[1])
			return 1
		return 0

class RadioThumbGen:
	def __init__(self):
		self.cache = {}
		self.requests = []
		self.size = 100

	def loader(self):

		while self.requests:
			item = self.requests[0]
			del self.requests[0]
			station = item[0]
			size = item[1]
			key = (station["title"], size)
			src = None
			filename = filename_safe(station["title"])

			cache_path = os.path.join(r_cache_dir, filename + ".jpg")
			if os.path.isfile(cache_path):
				src = open(cache_path, "rb")
			else:
				cache_path = os.path.join(r_cache_dir, filename + ".png")
				if os.path.isfile(cache_path):
					src = open(cache_path, "rb")
				else:
					cache_path = os.path.join(r_cache_dir, filename)
					if os.path.isfile(cache_path):
						src = open(cache_path, "rb")

			if src:
				pass
				#logging.info("found cached")
			elif station.get("icon") and station["icon"] not in prefs.radio_thumb_bans:
				try:
					r = requests.get(station.get("icon"), headers={"User-Agent": t_agent}, timeout=5, stream=True)
					if r.status_code != 200 or int(r.headers.get("Content-Length", 0)) > 2000000:
						raise Exception("Error get radio thumb")
				except Exception:
					logging.exception("error get radio thumb")
					self.cache[key] = [0]
					if station.get("icon") and station.get("icon") not in prefs.radio_thumb_bans:
						prefs.radio_thumb_bans.append(station.get("icon"))
					continue
				src = io.BytesIO()
				length = 0
				for chunk in r.iter_content(1024):
					src.write(chunk)
					length += len(chunk)
					if length > 2000000:
						scr = None
				if src is None:
					self.cache[key] = [0]
					if station.get("icon") and station.get("icon") not in prefs.radio_thumb_bans:
						prefs.radio_thumb_bans.append(station.get("icon"))
					continue
				src.seek(0)
				with open(cache_path, "wb") as f:
					f.write(src.read())
				src.seek(0)
			else:
				# logging.info("no icon")
				self.cache[key] = [0]
				continue

			try:
				im = Image.open(src)
				if im.mode != "RGBA":
					im = im.convert("RGBA")
			except Exception:
				logging.exception("malform get radio thumb")
				self.cache[key] = [0]
				if station.get("icon") and station.get("icon") not in prefs.radio_thumb_bans:
					prefs.radio_thumb_bans.append(station.get("icon"))
				continue
			if src is not None:
				src.close()

			im = im.resize((size, size), Image.Resampling.LANCZOS)
			g = io.BytesIO()
			g.seek(0)
			im.save(g, "PNG")
			g.seek(0)
			wop = rw_from_object(g)
			s_image = IMG_Load_RW(wop, 0)
			self.cache[key] = [2, None, None, s_image]
			gui.update += 1

	def draw(self, station, x, y, w):
		if not station.get("title"):
			return 0
		key = (station["title"], w)

		r = self.cache.get(key)
		if r is None:
			if len(self.requests) < 3:
				self.requests.append((station, w))
				tauon.thread_manager.ready("radio-thumb")
			return 0
		if r[0] == 2:
			texture = SDL_CreateTextureFromSurface(renderer, r[3])
			SDL_FreeSurface(r[3])
			tex_w = pointer(c_int(0))
			tex_h = pointer(c_int(0))
			SDL_QueryTexture(texture, None, None, tex_w, tex_h)
			sdl_rect = SDL_Rect(0, 0)
			sdl_rect.w = int(tex_w.contents.value)
			sdl_rect.h = int(tex_h.contents.value)
			r[2] = texture
			r[1] = sdl_rect
			r[0] = 1
		if r[0] == 1:
			r[1].x = round(x)
			r[1].y = round(y)
			SDL_RenderCopy(renderer, r[2], None, r[1])
			return 1
		return 0

class Showcase:

	def __init__(self):

		self.lastfm_artist = None
		self.artist_mode = False

	def render(self):

		global right_click

		box = int(window_size[1] * 0.4 + 120 * gui.scale)
		box = min(window_size[0] // 2, box)

		hide_art = False
		if window_size[0] < 900 * gui.scale:
			hide_art = True

		x = int(window_size[0] * 0.15)
		y = int((window_size[1] / 2) - (box / 2)) - 10 * gui.scale

		if hide_art:
			box = 45 * gui.scale
		elif window_size[1] / window_size[0] > 0.7:
			x = int(window_size[0] * 0.07)

		bbg = rgb_add_hls(colours.playlist_panel_background, 0, 0.05, 0)  # [255, 255, 255, 18]
		bfg = rgb_add_hls(colours.playlist_panel_background, 0, 0.09, 0)  # [255, 255, 255, 30]
		bft = colours.grey(235)
		bbt = colours.grey(200)

		t1 = colours.grey(250)

		gui.vis_4_colour = None
		light_mode = False
		if colours.lm:
			bbg = colours.vis_colour
			bfg = alpha_blend([255, 255, 255, 60], colours.vis_colour)
			bft = colours.grey(250)
			bbt = colours.grey(245)
		elif prefs.art_bg and prefs.bg_showcase_only:
			bbg = [255, 255, 255, 18]
			bfg = [255, 255, 255, 30]
			bft = [255, 255, 255, 250]
			bbt = [255, 255, 255, 200]

		if test_lumi(colours.playlist_panel_background) < 0.7:
			light_mode = True
			t1 = colours.grey(30)
			gui.vis_4_colour = [40, 40, 40, 255]

		ddt.rect((0, gui.panelY, window_size[0], window_size[1] - gui.panelY), colours.playlist_panel_background)

		if prefs.bg_showcase_only and prefs.art_bg:
			style_overlay.display()

			# Draw textured background
			if not light_mode and not colours.lm and prefs.showcase_overlay_texture:
				rect = SDL_Rect()
				rect.x = 0
				rect.y = 0
				rect.w = 300
				rect.h = 300

				xx = 0
				yy = 0
				while yy < window_size[1]:
					xx = 0
					while xx < window_size[0]:
						rect.x = xx
						rect.y = yy
						SDL_RenderCopy(renderer, overlay_texture_texture, None, rect)
						xx += 300
					yy += 300

		if prefs.bg_showcase_only and prefs.art_bg:
			ddt.alpha_bg = True
			ddt.force_gray = True

		# if not prefs.shuffle_lock:
		#     if draw.button(_("Return"), 25 * gui.scale, window_size[1] - gui.panelBY - 40 * gui.scale,
		#                    text_highlight_colour=bft, text_colour=bbt, backgound_colour=bbg,
		#                    background_highlight_colour=bfg):
		#         gui.switch_showcase_off = True
		#         gui.update += 1
		#         gui.update_layout()

		# ddt.force_gray = True

		if pctl.playing_state == 3 and not radiobox.dummy_track.title:

			if not pctl.tag_meta:
				y = int(window_size[1] / 2) - 60 - gui.scale
				ddt.text((window_size[0] // 2, y, 2), pctl.url, colours.side_bar_line2, 317)
			else:
				w = window_size[0] - (x + box) - 30 * gui.scale
				x = int((window_size[0]) / 2)

				y = int(window_size[1] / 2) - 60 - gui.scale
				ddt.text((x, y, 2), pctl.tag_meta, colours.side_bar_line1, 216, w)

		else:

			if len(pctl.track_queue) < 1:
				ddt.alpha_bg = False
				return

			# if draw.button("Return", 20, gui.panelY + 5, bg=colours.grey(30)):
			#     pass

			if prefs.bg_showcase_only and prefs.art_bg:
				ddt.alpha_bg = True
				ddt.force_gray = True

			if gui.force_showcase_index >= 0:
				if draw.button(
					_("Playing"), 25 * gui.scale, gui.panelY + 20 * gui.scale, text_highlight_colour=bft,
					text_colour=bbt, background_colour=bbg, background_highlight_colour=bfg):
					gui.force_showcase_index = -1
					ddt.force_gray = False

			if gui.force_showcase_index >= 0:
				index = gui.force_showcase_index
				track = pctl.master_library[index]
			else:

				if pctl.playing_state == 3:
					track = radiobox.dummy_track
				else:
					index = pctl.track_queue[pctl.queue_step]
					track = pctl.master_library[index]

			if not hide_art:

				# Draw frame around art box
				# drop_shadow.render(x + 5 * gui.scale, y + 5 * gui.scale, box + 10 * gui.scale, box + 10 * gui.scale)
				ddt.rect(
					(x - round(2 * gui.scale), y - round(2 * gui.scale), box + round(4 * gui.scale),
					box + round(4 * gui.scale)), [60, 60, 60, 135])
				ddt.rect((x, y, box, box), colours.playlist_panel_background)
				rect = SDL_Rect(round(x), round(y), round(box), round(box))
				style_overlay.hole_punches.append(rect)

				# Draw album art in box
				album_art_gen.display(track, (x, y), (box, box))

				# Click art to cycle
				if coll((x, y, box, box)):
					if inp.mouse_click is True:
						album_art_gen.cycle_offset(track)
					if right_click:
						picture_menu.activate(in_reference=track)
						right_click = False

			# Check for lyrics if auto setting
			test_auto_lyrics(track)

			gui.draw_vis4_top = False

			if gui.panelY < mouse_position[1] < window_size[1] - gui.panelBY:
				if mouse_wheel != 0:
					lyrics_ren.lyrics_position += mouse_wheel * 35 * gui.scale
				if right_click:
					# track = pctl.playing_object()
					if track != None:
						showcase_menu.activate(track)

			gcx = x + box + int(window_size[0] * 0.15) + 10 * gui.scale
			gcx -= 100 * gui.scale

			timed_ready = False
			if True and prefs.show_lyrics_showcase:
				timed_ready = timed_lyrics_ren.generate(track)

			if timed_ready and track.lyrics:

				# if not prefs.guitar_chords or guitar_chords.test_ready_status(track) != 1:
				#
				#     line = _("Prefer synced")
				#     if prefs.prefer_synced_lyrics:
				#         line = _("Prefer static")
				#     if draw.button(line, 25 * gui.scale, window_size[1] - gui.panelBY - 70 * gui.scale,
				#                    text_highlight_colour=bft, text_colour=bbt, background_colour=bbg,
				#                    background_highlight_colour=bfg):
				#         prefs.prefer_synced_lyrics ^= True

				timed_ready = prefs.prefer_synced_lyrics

			#if prefs.guitar_chords and track.title and prefs.show_lyrics_showcase and guitar_chords.render(track, gcx, y):
			#	if not guitar_chords.auto_scroll:
			#		if draw.button(
			#			_("Auto-Scroll"), 25 * gui.scale, window_size[1] - gui.panelBY - 70 * gui.scale,
			#			text_highlight_colour=bft, text_colour=bbt, background_colour=bbg,
			#			background_highlight_colour=bfg):
			#			guitar_chords.auto_scroll = True

			if True and prefs.show_lyrics_showcase and timed_ready:
				w = window_size[0] - (x + box) - round(30 * gui.scale)
				timed_lyrics_ren.render(track.index, gcx, y, w=w)

			elif track.lyrics == "" or not prefs.show_lyrics_showcase:

				w = window_size[0] - (x + box) - round(30 * gui.scale)
				x = int(x + box + (window_size[0] - x - box) / 2)

				if hide_art:
					x = window_size[0] // 2

				# x = int((window_size[0]) / 2)
				y = int(window_size[1] / 2) - round(60 * gui.scale)

				if prefs.showcase_vis and prefs.backend == 1:
					y -= round(30 * gui.scale)

				if track.artist == "" and track.title == "":

					ddt.text((x, y, 2), clean_string(track.filename), t1, 216, w)

				else:

					ddt.text((x, y, 2), track.artist, t1, 20, w)

					y += round(48 * gui.scale)

					if window_size[0] < 700 * gui.scale:
						if len(track.title) < 30:
							ddt.text((x, y, 2), track.title, t1, 220, w)
						elif len(track.title) < 40:
							ddt.text((x, y, 2), track.title, t1, 217, w)
						else:
							ddt.text((x, y, 2), track.title, t1, 213, w)

					elif len(track.title) < 35:
						ddt.text((x, y, 2), track.title, t1, 220, w)
					elif len(track.title) < 50:
						ddt.text((x, y, 2), track.title, t1, 219, w)
					else:
						ddt.text((x, y, 2), track.title, t1, 216, w)

				gui.spec4_rec.x = x - (gui.spec4_rec.w // 2)
				gui.spec4_rec.y = y + round(50 * gui.scale)

				if prefs.showcase_vis and window_size[1] > 369 and not search_over.active and not (
						tauon.spot_ctl.coasting or tauon.spot_ctl.playing):

					if gui.message_box or not is_level_zero(include_menus=True):
						self.render_vis()
					else:
						gui.draw_vis4_top = True

			else:
				x += box + int(window_size[0] * 0.15) + 10 * gui.scale
				x -= 100 * gui.scale
				w = window_size[0] - x - 30 * gui.scale

				if key_up_press and not (key_ctrl_down or key_shift_down or key_shiftr_down):
					lyrics_ren.lyrics_position += 35 * gui.scale
				if key_down_press and not (key_ctrl_down or key_shift_down or key_shiftr_down):
					lyrics_ren.lyrics_position -= 35 * gui.scale

				lyrics_ren.test_update(track)
				tw, th = ddt.get_text_wh(lyrics_ren.text + "\n", 17, w, True)

				lyrics_ren.lyrics_position = max(lyrics_ren.lyrics_position, th * -1 + 100 * gui.scale)
				lyrics_ren.lyrics_position = min(lyrics_ren.lyrics_position, 70 * gui.scale)

				lyrics_ren.render(
					x,
					y + lyrics_ren.lyrics_position,
					w,
					int(window_size[1] - 100 * gui.scale),
					0)
		ddt.alpha_bg = False
		ddt.force_gray = False

	def render_vis(self, top=False):

		SDL_SetRenderTarget(renderer, gui.spec4_tex)
		SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
		SDL_RenderClear(renderer)

		bx = 0
		by = 50 * gui.scale

		if gui.vis_4_colour is not None:
			SDL_SetRenderDrawColor(
				renderer, gui.vis_4_colour[0], gui.vis_4_colour[1], gui.vis_4_colour[2], gui.vis_4_colour[3])

		if (pctl.playing_time < 0.5 and (pctl.playing_state == 1 or pctl.playing_state == 3)) or (
				pctl.playing_state == 0 and gui.spec4_array.count(0) != len(gui.spec4_array)):
			gui.update = 2
			gui.level_update = True

			for i in range(len(gui.spec4_array)):
				gui.spec4_array[i] -= 0.1
				gui.spec4_array[i] = max(gui.spec4_array[i], 0)

		if not top and (pctl.playing_state == 1 or pctl.playing_state == 3):
			gui.update = 2

		slide = 0.7
		for i, bar in enumerate(gui.spec4_array):

			# We wont draw higher bars that may not move
			if i > 40:
				break

			# Scale input amplitude to pixel distance (Applying a slight exponentional)
			dis = (2 + math.pow(bar / (2 + slide), 1.5))
			slide -= 0.03  # Set a slight bias for higher bars

			# Define colour for bar
			if gui.vis_4_colour is None:
				set_colour(
					hsl_to_rgb(
						0.7 + min(0.15, (bar / 150)) + pctl.total_playtime / 300, min(0.9, 0.7 + (dis / 300)),
						min(0.9, 0.7 + (dis / 600))))

			# Define bar size and draw
			gui.bar4.x = int(bx)
			gui.bar4.y = round(by - dis * gui.scale)
			gui.bar4.w = round(2 * gui.scale)
			gui.bar4.h = round(dis * 2 * gui.scale)

			SDL_RenderFillRect(renderer, gui.bar4)

			# Set distance between bars
			bx += 8 * gui.scale

		if top:
			SDL_SetRenderTarget(renderer, None)
		else:
			SDL_SetRenderTarget(renderer, gui.main_texture)

		# SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND)
		SDL_RenderCopy(renderer, gui.spec4_tex, None, gui.spec4_rec)

class ColourPulse2:
	"""Animates colour between two colours"""
	def __init__(self):

		self.timer = Timer()
		self.in_timer = Timer()
		self.out_timer = Timer()
		self.out_timer.start = 0
		self.active = False

	def get(self, hit, on, off, low_hls, high_hls):

		if on:
			return high_hls
			# rgb = colorsys.hls_to_rgb(high_hls[0], high_hls[1], high_hls[2])
			# return [int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255), 255]
		if off:
			return low_hls
			# rgb = colorsys.hls_to_rgb(low_hls[0], low_hls[1], low_hls[2])
			# return [int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255), 70]

		ani_time = 0.15

		if hit is True and self.active is False:
			self.active = True
			self.in_timer.set()

			out_time = self.out_timer.get()
			if out_time < ani_time:
				self.in_timer.force_set(ani_time - out_time)

		elif hit is False and self.active is True:
			self.active = False
			self.out_timer.set()

			in_time = self.in_timer.get()
			if in_time < ani_time:
				self.out_timer.force_set(ani_time - in_time)

		pro = 0.5
		if self.active:
			time = self.in_timer.get()
			if time <= 0:
				pro = 0
			elif time >= ani_time:
				pro = 1
			else:
				pro = time / ani_time
				gui.update = 2
		else:
			time = self.out_timer.get()
			if time <= 0:
				pro = 1
			elif time >= ani_time:
				pro = 0
			else:
				pro = 1 - (time / ani_time)
				gui.update = 2

		return colour_slide(low_hls, high_hls, pro, 1)


class ViewBox:

	def __init__(self, reload=False):
		self.x = 0
		self.y = gui.panelY
		self.w = 52 * gui.scale
		self.h = 260 * gui.scale  # 257
		self.active = False

		self.border = 3 * gui.scale

		self.tracks_img = asset_loader(scaled_asset_directory, loaded_asset_dc, "tracks.png", True)
		self.side_img = asset_loader(scaled_asset_directory, loaded_asset_dc, "tracks+side.png", True)
		self.gallery1_img = asset_loader(scaled_asset_directory, loaded_asset_dc, "gallery1.png", True)
		self.gallery2_img = asset_loader(scaled_asset_directory, loaded_asset_dc, "gallery2.png", True)
		self.combo_img = asset_loader(scaled_asset_directory, loaded_asset_dc, "combo.png", True)
		self.lyrics_img = asset_loader(scaled_asset_directory, loaded_asset_dc, "lyrics.png", True)
		self.gallery2_img = asset_loader(scaled_asset_directory, loaded_asset_dc, "gallery2.png", True)
		self.radio_img = asset_loader(scaled_asset_directory, loaded_asset_dc, "radio.png", True)
		self.col_img = asset_loader(scaled_asset_directory, loaded_asset_dc, "col.png", True)
		# self.artist_img = asset_loader(scaled_asset_directory, loaded_asset_dc, "artist.png", True)

		# _ .15 0
		self.tracks_colour = ColourPulse2()  # (0.5) # .5 .6 .75
		self.side_colour = ColourPulse2()  # (0.55) # .55 .6 .75
		self.gallery1_colour = ColourPulse2()  # (0.6) # .6 .6 .75
		self.radio_colour = ColourPulse2()  # (0.6) # .6 .6 .75
		# self.combo_colour = ColourPulse(0.75)
		self.lyrics_colour = ColourPulse2()  # (0.7)
		# self.gallery2_colour = ColourPulse(0.65)
		self.col_colour = ColourPulse2()  # (0.14)
		self.artist_colour = ColourPulse2()  # (0.2)

		self.on_colour = [255, 190, 50, 255]
		self.over_colour = [255, 190, 50, 255]
		self.off_colour = colours.grey(40)

		if not reload:
			gui.combo_was_album = False

	def activate(self, x):
		self.x = x
		self.active = True
		self.clicked = False

		self.tracks_colour.out_timer.force_set(10)
		self.side_colour.out_timer.force_set(10)
		self.gallery1_colour.out_timer.force_set(10)
		self.radio_colour.out_timer.force_set(10)
		# self.combo_colour.out_timer.force_set(10)
		self.lyrics_colour.out_timer.force_set(10)
		# self.gallery2_colour.out_timer.force_set(10)
		self.col_colour.out_timer.force_set(10)
		self.artist_colour.out_timer.force_set(10)

		self.tracks_colour.active = False
		self.side_colour.active = False
		self.gallery1_colour.active = False
		self.radio_colour.active = False
		# self.combo_colour.active = False
		self.lyrics_colour.active = False
		# self.gallery2_colour.active = False
		self.col_colour.active = False
		self.artist_colour.active = False

		self.col_force_off = False

		# gui.level_2_click = False
		gui.update = 2

	def button(self, x, y, asset, test, colour_get=None, name="Unknown", animate=True, low=0, high=0):

		on = test()
		rect = [x - 8 * gui.scale,
				y - 8 * gui.scale,
				asset.w + 16 * gui.scale,
				asset.h + 16 * gui.scale]
		fields.add(rect)

		if on:
			colour = self.on_colour

		else:
			colour = self.off_colour

		fun = None
		col = False
		if coll(rect):

			tool_tip.test(x + asset.w + 10 * gui.scale, y - 15 * gui.scale, name)

			col = True
			if gui.level_2_click:
				fun = test
			if colour_get is None:
				colour = self.over_colour

		colour = colour_get.get(col, on, not on and not animate, low, high)

		# if "+" in name:
		#
		#     colour = cctest.get(col, on, [0, 0.2, 0.0], [0, 0.8, 0.8])

		# if not on and not animate:
		#     colour = self.off_colour

		asset.render(x, y, colour)

		return fun

	def tracks(self, hit=False):

		if hit is False:
			return album_mode is False and \
				gui.combo_mode is False and \
				gui.rsp is False

		if not (album_mode is False and \
			gui.combo_mode is False and \
			gui.rsp is False):
			if x_menu.active:
				x_menu.close_next_frame = True

		view_tracks()

	def side(self, hit=False):

		if hit is False:
			return album_mode is False and \
				gui.combo_mode is False and \
				gui.rsp is True
		if not (album_mode is False and \
			gui.combo_mode is False and \
			gui.rsp is True):
			if x_menu.active:
				x_menu.close_next_frame = True

		view_standard_meta()

	def gallery1(self, hit: bool = False) -> bool | None:

		if hit is False:
			return album_mode is True  # and gui.show_playlist is True

		if album_mode and not gui.combo_mode:
			gui.hide_tracklist_in_gallery ^= True
			gui.rspw = gui.pref_gallery_w
			gui.update_layout()
			# x_menu.active = False
			x_menu.close_next_frame = True
			# Menu.active = False
			return None

		if x_menu.active:
			x_menu.close_next_frame = True

		force_album_view()

	def radio(self, hit=False):

		if hit is False:
			return gui.radio_view

		if not gui.radio_view:
			enter_radio_view()
		else:
			exit_combo(restore=True)

		if x_menu.active:
			x_menu.close_next_frame = True

	def lyrics(self, hit=False):

		if hit is False:
			return gui.showcase_mode

		if not gui.showcase_mode:
			if gui.radio_view:
				gui.was_radio = True
			enter_showcase_view()

		elif gui.was_radio:
			enter_radio_view()
		else:
			exit_combo(restore=True)
		if x_menu.active:
			x_menu.close_next_frame = True

	def col(self, hit=False):

		if hit is False:
			return gui.set_mode

		if not gui.set_mode:
			if gui.combo_mode:
				exit_combo()

		if album_mode and gui.plw < 550 * gui.scale:
			toggle_album_mode()

		toggle_library_mode()

	def artist_info(self, hit=False):

		if hit is False:
			return gui.artist_info_panel

		gui.artist_info_panel ^= True
		gui.update_layout()

	def render(self):

		if prefs.shuffle_lock:
			self.active = False
			self.clicked = False
			return

		if not self.active:
			return

		# rect = [self.x, self.y, self.w, self.h]
		# if x_menu.clicked or inp.mouse_click:
		if self.clicked:
			gui.level_2_click = True
		self.clicked = False

		x = self.x - 40 * gui.scale

		vr = [x, gui.panelY, self.w, self.h]
		# vr = [x, gui.panelY, 52 * gui.scale, 220 * gui.scale]

		border_colour = colours.menu_tab  # colours.grey(30)
		if colours.lm:
			ddt.rect((vr[0], vr[1], vr[2] + round(4 * gui.scale), vr[3]), border_colour)
		else:
			ddt.rect(
				(vr[0] - round(4 * gui.scale), vr[1], vr[2] + round(8 * gui.scale),
				vr[3] + round(4 * gui.scale)), border_colour)
		ddt.rect(vr, colours.menu_background)

		x += 7 * gui.scale
		y = gui.panelY + 14 * gui.scale

		func = None

		# low = (0, .15, 0)
		# low = (0, .40, 0)
		# low = rgb_to_hls(*alpha_blend(colours.menu_icons, colours.menu_background)[:3])  # fix me
		low = alpha_blend(colours.menu_icons, colours.menu_background)

		# if colours.lm:
		#     low = (0, 0.5, 0)

		# ----
		#logging.info(hls_to_rgb(.55, .6, .75))
		high = [76, 183, 229, 255]  # (.55, .6, .75)
		if colours.lm:
			# high = (.55, .75, .75)
			high = [63, 63, 63, 255]

		test = self.button(x, y, self.side_img, self.side, self.side_colour, _("Tracks + Art"), low=low, high=high)
		if test is not None:
			func = test

		# ----

		y += 40 * gui.scale

		high = [76, 137, 229, 255]  # (.6, .6, .75)
		if colours.lm:
			# high = (.6, .80, .85)
			high = [63, 63, 63, 255]

		if gui.hide_tracklist_in_gallery:
			test = self.button(
				x - round(1 * gui.scale), y, self.gallery2_img, self.gallery1, self.gallery1_colour,
				_("Gallery"), low=low, high=high)
		else:
			test = self.button(
				x, y, self.gallery1_img, self.gallery1, self.gallery1_colour, _("Gallery"), low=low, high=high)
		if test is not None:
			func = test

		# ---

		y += 40 * gui.scale

		high = [76, 229, 229, 255]
		if colours.lm:
			# high = (.5, .7, .65)
			high = [63, 63, 63, 255]

		test = self.button(
			x + 3 * gui.scale, y, self.tracks_img, self.tracks, self.tracks_colour, _("Tracks only"),
			low=low, high=high)
		if test is not None:
			func = test

		# ---

		y += 45 * gui.scale

		high = [107, 76, 229, 255]
		if colours.lm:
			# high = (.7, .75, .75)
			high = [63, 63, 63, 255]

		test = self.button(
			x + 4 * gui.scale, y, self.lyrics_img, self.lyrics, self.lyrics_colour,
			_("Showcase + Lyrics"), low=low, high=high)
		if test is not None:
			func = test

		# --

		y += 40 * gui.scale

		high = [92, 86, 255, 255]
		if colours.lm:
			# high = (.7, .75, .75)
			high = [63, 63, 63, 255]

		test = self.button(
			x + 3 * gui.scale, y, self.radio_img, self.radio, self.radio_colour, _("Radio"), low=low, high=high)
		if test is not None:
			func = test

		# --

		y += 45 * gui.scale

		high = [229, 205, 76, 255]
		if colours.lm:
			# high = (.9, .75, .65)
			high = [63, 63, 63, 255]

		test = self.button(
			x + 5 * gui.scale, y, self.col_img, self.col, self.col_colour, _("Toggle columns"), False, low=low, high=high)
		if test is not None:
			func = test

		# --

		# y += 41 * gui.scale
		#
		# high = [198, 229, 76, 255]
		# if colours.lm:
		#     #high = (.2, .6, .75)
		#     high = [63, 63, 63, 255]
		#
		# if gui.scale == 1.25:
		#     x-= 1
		#
		# test = self.button(x + 2 * gui.scale, y, self.artist_img, self.artist_info, self.artist_colour, _("Toggle artist info"), False, low=low, high=high)
		# if test is not None:
		#     func = test

		if func is not None:
			func(True)

		if gui.level_2_click and coll(vr):
			x_menu.clicked = False

		gui.level_2_click = False
		if not x_menu.active:
			self.active = False

class DLMon:

	def __init__(self):

		self.ticker = Timer()
		self.ticker.force_set(8)

		self.watching = {}
		self.ready = set()
		self.done = set()

	def scan(self):

		if len(self.watching) == 0:
			if self.ticker.get() < 10:
				return
		elif self.ticker.get() < 2:
			return

		self.ticker.set()

		for downloads in download_directories:

			for item in os.listdir(downloads):

				path = os.path.join(downloads, item)

				if path in self.done:
					continue

				if path in self.ready and not os.path.exists(path):
					del self.ready[path]
					continue

				if path in self.watching and not os.path.exists(path):
					del self.watching[path]
					continue

				# stamp = os.stat(path)[stat.ST_MTIME]
				try:
					stamp = os.path.getmtime(path)
				except Exception:
					logging.exception(f"Failed to scan item at {path}")
					self.done.add(path)
					continue

				min_age = (time.time() - stamp) / 60
				ext = os.path.splitext(path)[1][1:].lower()

				if msys and "TauonMusicBox" in path:
					continue

				if min_age < 240 and os.path.isfile(path) and ext in Archive_Formats:
					size = os.path.getsize(path)
					#logging.info("Check: " + path)
					if path in self.watching:
						# Check if size is stable, then scan for audio files
						#logging.info("watching...")
						if size == self.watching[path] and size != 0:
							#logging.info("scan")
							del self.watching[path]

							# Check if folder to extract to exists
							split = os.path.splitext(path)
							target_dir = split[0]
							if prefs.extract_to_music and music_directory is not None:
								target_dir = os.path.join(str(music_directory), os.path.basename(target_dir))

							if os.path.exists(target_dir):
								pass
								#logging.info("Target folder for archive already exists")

							elif archive_file_scan(path, DA_Formats, launch_prefix) >= 0.4:
								self.ready.add(path)
								gui.update += 1
								#logging.info("Archive detected as music")
							else:
								pass
								#logging.info("Archive rejected as music")
							self.done.add(path)
						else:
							#logging.info("update.")
							self.watching[path] = size
					else:
						self.watching[path] = size
						#logging.info("add.")

				elif min_age < 60 \
				and os.path.isdir(path) \
				and path not in quick_import_done \
				and "encode-output" not in path:
					try:
						size = get_folder_size(path)
					except FileNotFoundError:
						logging.warning(f"Failed to find watched folder {path}, deleting from watchlist")
						if path in self.watching:
							del self.watching[path]
						continue
					except Exception:
						logging.exception("Unknown error getting folder size")
					if path in self.watching:
						# Check if size is stable, then scan for audio files
						if size == self.watching[path]:
							del self.watching[path]
							if folder_file_scan(path, DA_Formats) > 0.5:

								# Check if folder not already imported
								imported = False
								for pl in pctl.multi_playlist:
									for i in pl.playlist_ids:
										if path.replace("\\", "/") == pctl.master_library[i].fullpath[:len(path)]:
											imported = True
										if imported:
											break
									if imported:
										break
								else:
									self.ready.add(path)
								gui.update += 1
							self.done.add(path)
						else:
							self.watching[path] = size
					else:
						self.watching[path] = size
				else:
					self.done.add(path)

		if len(self.ready) > 0:
			temp = set()
			#logging.info(quick_import_done)
			#logging.info(self.ready)
			for item in self.ready:
				if item not in quick_import_done:
					if os.path.exists(path):
						temp.add(item)
				# else:
				#     logging.info("FILE IMPORTED")
			self.ready = temp

		if len(self.watching) > 0:
			gui.update += 1

class Fader:

	def __init__(self):

		self.total_timer = Timer()
		self.timer = Timer()
		self.ani_duration = 0.3
		self.state = 0  # 0 = Want off, 1 = Want fade on
		self.a = 0  # The fade progress (0-1)

	def render(self):

		if self.total_timer.get() > self.ani_duration:
			self.a = self.state
		elif self.state == 0:
			t = self.timer.hit()
			self.a -= t / self.ani_duration
			self.a = max(0, self.a)
		elif self.state == 1:
			t = self.timer.hit()
			self.a += t / self.ani_duration
			self.a = min(1, self.a)

		rect = [0, 0, window_size[0], window_size[1]]
		ddt.rect(rect, [0, 0, 0, int(110 * self.a)])

		if not (self.a == 0 or self.a == 1):
			gui.update += 1

	def rise(self):

		self.state = 1
		self.timer.hit()
		self.total_timer.set()

	def fall(self):

		self.state = 0
		self.timer.hit()
		self.total_timer.set()

class EdgePulse:

	def __init__(self):

		self.timer = Timer()
		self.timer.force_set(10)
		self.ani_duration = 0.5

	def render(self, x, y, w, h, r=200, g=120, b=0) -> bool:
		r = colours.pluse_colour[0]
		g = colours.pluse_colour[1]
		b = colours.pluse_colour[2]
		time = self.timer.get()
		if time < self.ani_duration:
			alpha = 255 - int(255 * (time / self.ani_duration))
			ddt.rect((x, y, w, h), [r, g, b, alpha])
			gui.update = 2
			return True
		return False

	def pulse(self):
		self.timer.set()


class EdgePulse2:

	def __init__(self):

		self.timer = Timer()
		self.timer.force_set(10)
		self.ani_duration = 0.22

	def render(self, x, y, w, h, bottom=False) -> bool | None:

		time = self.timer.get()
		if time < self.ani_duration:

			if bottom:
				if mouse_wheel > 0:
					self.timer.force_set(10)
					return None
			elif mouse_wheel < 0:
				self.timer.force_set(10)
				return None

			alpha = 30 - int(25 * (time / self.ani_duration))
			h_off = (h // 5) * (time / self.ani_duration) * 4

			if colours.lm:
				colour = (0, 0, 0, alpha)
			else:
				colour = (255, 255, 255, alpha)

			if not bottom:
				ddt.rect((x, y, w, h - h_off), colour)
			else:
				ddt.rect((x, y - (h - h_off), w, h - h_off), colour)
			gui.update = 2
			return True
		return False

	def pulse(self):
		self.timer.set()

class Undo:

	def __init__(self):

		self.e = []

	def undo(self):

		if not self.e:
			show_message(_("There are no more steps to undo."))
			return

		job = self.e.pop()

		if job[0] == "playlist":
			pctl.multi_playlist.append(job[1])
			switch_playlist(len(pctl.multi_playlist) - 1)
		elif job[0] == "tracks":

			uid = job[1]
			li = job[2]

			for i, playlist in enumerate(pctl.multi_playlist):
				if playlist.uuid_int == uid:
					pl = playlist.playlist_ids
					switch_playlist(i)
					break
			else:
				logging.info("No matching playlist ID to restore tracks to")
				return

			for i, ref in reversed(li):

				if i > len(pl):
					logging.error("restore track error - playlist not correct length")
					continue
				pl.insert(i, ref)

				if not pctl.playlist_view_position < i < pctl.playlist_view_position + gui.playlist_view_length:
					pctl.playlist_view_position = i
					logging.debug("Position changed by undo")
		elif job[0] == "ptt":
			j, fr, fr_s, fr_scr, so, to_s, to_scr = job
			star_store.insert(fr.index, fr_s)
			star_store.insert(to.index, to_s)
			to.lfm_scrobbles = to_scr
			fr.lfm_scrobbles = fr_scr

		gui.pl_update = 1

	def bk_playlist(self, pl_index: int) -> None:

		self.e.append(("playlist", pctl.multi_playlist[pl_index]))

	def bk_tracks(self, pl_index: int, indis) -> None:

		uid = pctl.multi_playlist[pl_index].uuid_int
		self.e.append(("tracks", uid, indis))

	def bk_playtime_transfer(self, fr, fr_s, fr_scr, so, to_s, to_scr) -> None:
		self.e.append(("ptt", fr, fr_s, fr_scr, so, to_s, to_scr))
