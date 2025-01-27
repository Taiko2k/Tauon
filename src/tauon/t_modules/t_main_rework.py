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
