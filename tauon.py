# -*- coding: utf-8 -*-

# Tauon Music Box

# Copyright © 2015-2017, Taiko2k captain(dot)gxj(at)gmail.com

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

# --------------------------------------------------------------------
# Preamble

# Welcome to the Tauon Music Box source code. I started this project when I was first
# learning python, as a result this code can be quite messy. No doubt I have
# written some things terribly wrong or inefficiently in places.
# I would highly recommend not using this project as an example on how to code cleanly or correctly.

# --------------------------------------------------------------------

# INDEX -------------------------------

# C-TC - TRACK CLASS + STATE LOADING
# C-IS - INIT SDL
# C-ML - MAIN LOOP START + INPUT HANDLING

# C-UL - LAYOUT UPDATING
# C-AR - ALBUM GALLERY RENDERING
# C-BB - BOTTOM PANEL RENDER
# C-TB - TOP PANEL RENDER CALL
# C-TD - TOP PANEL RENDER
# C-CM - ALBUM ART + TRACKS VIEW RENDER
# C-PR - PLAYLIST RENDER CALL

# C-PC - PLAYBACK CONTROL

# ---------------------------------------

import sys
import os
import pickle

t_version = "v2.6.5"
t_title = 'Tauon Music Box'
print(t_title)
print(t_version)
print('Copyright 2015-2017 Taiko2k captain.gxj@gmail.com\n')

# Detect platform
if sys.platform == 'win32':
    system = 'windows'
elif sys.platform == 'darwin':
    system = 'mac'
else:
    system = 'linux'

# Find directories
working_directory = os.getcwd()
install_directory = sys.path[0].replace('\\', '/')

# Workaround for Py-Installer
if 'base_library' in install_directory:
    install_directory = os.path.dirname(install_directory)

# Detect what folder should be used for user data
user_directory = install_directory
install_mode = False
if system == 'linux' and (install_directory[:5] == "/opt/" or install_directory[:5] == "/usr/"):
    
    user_directory = os.path.expanduser('~') + "/.tauonmb-user"
    install_mode = True

elif system == 'windows' and ('Program Files' in install_directory or
                                  os.path.isfile(install_directory + '\\unins000.exe')):

    user_directory = os.path.expanduser('~').replace("\\", '/') + "/Music/TauonMusicBox"
    print("User Directroy: ", end="")
    print(user_directory)
    install_mode = True

if install_mode:
    print("Running from installed location")
    print("User files and config location: " + user_directory)
    if not os.path.isdir(user_directory):
        print("User directory is missing... creating")
        os.makedirs(user_directory + "/encoder")
        import shutil
        shutil.copy(install_directory + "/config.txt", user_directory)
else:
    print("Running in portable mode")


transfer_target = user_directory + "/transfer.p"
# print("Working directory: " + working_directory)
# print('Argument List: ' + str(sys.argv))
print('Install directory: ' + install_directory)
config_directory = user_directory
cache_directory = os.path.join(user_directory, 'cache')
b_active_directory = install_directory.encode('utf-8')

# -------------------------------
# Single Instancing

if os.path.isfile('.gitignore') or os.path.isfile('multiinstance'):
    print("Dev mode, ignoring single instancing")
else:
    if system == 'windows':
        from win32event import CreateMutex
        from win32api import CloseHandle, GetLastError
        from winerror import ERROR_ALREADY_EXISTS


        class singleinstance:
            """ Limits application to single instance """

            def __init__(self):
                self.mutexname = "tauonmusicbox_{A0E858DF-985E-4907-B7FB-7D732C3FC3B9}"
                self.mutex = CreateMutex(None, False, self.mutexname)
                self.lasterror = GetLastError()

            def aleradyrunning(self):
                return (self.lasterror == ERROR_ALREADY_EXISTS)

            def __del__(self):
                if self.mutex:
                    CloseHandle(self.mutex)

        lock = singleinstance()

        if lock.aleradyrunning():
            print("Program is already running")
            pickle.dump(sys.argv, open(user_directory + "/transfer.p", "wb"))
            sys.exit()

    elif system == 'linux':

        import fcntl
        pid_file = os.path.join(user_directory, 'program.pid')
        fp = open(pid_file, 'w')
        try:
            fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            # another instance is running
            print("Program is already running")
            pickle.dump(sys.argv, open(user_directory + "/transfer.p", "wb"))
            sys.exit()

# ------------------------------------
# Continue startup

last_fm_enable = False

import time
import ctypes
import random
import threading
import io
import copy
import subprocess
import urllib.parse
import urllib.request
import datetime
try:
    import pylast
    last_fm_enable = True
except:
    print("PyLast moduel not found, last fm will be disabled.")
import shutil
import shlex
import math
import locale
import webbrowser
import base64
import re
import zipfile
import warnings
import struct
import colorsys
import html
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape
from ctypes import *
from PyLyrics import *

locale.setlocale(locale.LC_ALL, "")  # Fixes some formatting issue with datetime stuff

# Platform specific imports
if system == 'windows':
    os.environ["PYSDL2_DLL_PATH"] = install_directory + "\\lib"
    from ctypes import windll, CFUNCTYPE, POINTER, c_int, c_void_p, byref
    import win32con, win32api, win32gui, win32ui, atexit  # win32clipboard, pythoncom
elif system == 'linux':
    os.environ["SDL_VIDEO_X11_WMCLASS"] = t_title
    import gi
    gi.require_version('Notify', '0.7')
    from gi.repository import Notify

    Notify.init("Hello World")
    g_tc_notify = Notify.Notification.new("Tauon Music Box",
                                    "Transcoding has finished.")


# Other imports
from sdl2 import *
from sdl2.sdlimage import *
from PIL import Image
from hsaudiotag import auto
import stagger
from stagger.id3 import *
from t_tagscan import Flac
from t_tagscan import Opus
from t_tagscan import Ape
from t_tagscan import Wav
from t_extra import *

# Mute some stagger warnings
warnings.simplefilter('ignore', stagger.errors.EmptyFrameWarning)
warnings.simplefilter('ignore', stagger.errors.FrameWarning)

default_player = 1
gapless_type1 = False
running = True


# Check if BASS is present and fall back to Gstreamer if not
if system == 'linux' and (not os.path.isfile(install_directory + '/lib/libbass.so') or '-Gst' in sys.argv):
    print("BASS not found")
    try:
        import gi
        gi.require_version('Gst', '1.0')
        from gi.repository import GObject, Gst
        default_player = 2
        gapless_type1 = True
        print("Using fallback GStreamer")
    except:
        print("ERROR: gi.repository not found")
        default_player = 0

if system == 'linux':
    import cairo
    import gi
    gi.require_version('Pango', '1.0')
    gi.require_version('PangoCairo', '1.0')
    from gi.repository import Pango
    from gi.repository import PangoCairo


# Setting various timers

cursor_blink_timer = Timer()
animate_monitor_timer = Timer()
spec_decay_timer = Timer()
min_render_timer = Timer()
check_file_timer = Timer()
vis_rate_timer = Timer()
vis_decay_timer = Timer()
scroll_timer = Timer()
radio_meta_timer = Timer()
perf_timer = Timer()
quick_d_timer = Timer()
broadcast_update_timer = Timer()
broadcast_update_timer.set()
core_timer = Timer()
gallery_select_animate_timer = Timer()
search_clear_timer = Timer()
test_timer = Timer()
vis_update = False
# GUI Variables -------------------------------------------------------------------------------------------

# Variables now go in the gui, pctl, input and prefs class instances. The following just haven't been moved yet.

GUI_Mode = 1

worker_save_state = False

draw_border = False
resize_mode = False

block6 = False

playlist_panel = False
side_panel_text_align = 0

album_mode = False
spec_smoothing = True

auto_play_import = False
# gui.offset_extra = 0

old_album_pos = -55
old_side_pos = 200
album_dex = []
album_artist_dict = {}
row_len = 5
last_row = 0
album_v_gap = 66
album_h_gap = 30
album_mode_art_size = 160
combo_mode_art_size = 190
albums_to_render = 0

album_pos_px = 1
time_last_save = 0
window_default_size = [1100, 500]
window_size = window_default_size
b_info_y = int(window_size[1] * 0.7)  # For future possible panel below playlist
fullscreen = 0

volume_store = 50  # Used to save the previous volume when muted

# row_alt = False

to_get = 0  # Used to store temporary import count display
to_got = 0

editline = ""
side_panel_enable = True
quick_drag = False

radiobox = False
radio_field_text = "http://0.0.0.0:8000"
renamebox = False


# Playlist Panel
pl_view_offset = 0
pl_rect = (2, 12, 10, 10)

theme = 0
themeChange = True

scroll_enable = True
scroll_timer = Timer()
scroll_timer.set()
scroll_opacity = 0
break_enable = True
dd_index = False

source = None

album_playlist_width = 430

update_title = False
star_lines = False

playlist_hold_position = 0
playlist_hold = False
selection_stage = 0


shift_selection = []
# Control Variables--------------------------------------------------------------------------

mouse_down = False
right_down = False
click_location = [200, 200]
last_click_location = [0, 0]
mouse_position = [0, 0]

k_input = True
key_shift_down = False
drag_mode = False
side_drag = False
clicked = False

# Player Variables----------------------------------------------------------------------------

format_colours = {  # These are the colours used for the label icon in UI 'info box'
    "MP3": [255, 130, 80, 255],
    "FLAC": [156, 249, 79, 255],
    "M4A": [81, 220, 225, 255],
    "OGG": [244, 244, 78, 255],
    "WMA": [213, 79, 247, 255],
    "APE": [247, 79, 79, 255],
    "TTA": [94, 78, 244, 255],
    "OPUS": [247, 79, 146, 255],
    "AAC": [79, 247, 168, 255],
    "WV": [229, 23, 18, 255]
}

# These will be the extensions of files to be added when importing
DA_Formats = {'mp3', 'wav', 'opus', 'flac', 'ape',
              'm4a', 'ogg', 'aac', 'tta', 'wv', }

if system == 'windows':
    DA_Formats.add('wma')  # Bass on Linux does not support WMA



p_stopped = 0
p_playing = 1
p_stopping = 2
p_paused = 3

cargo = []

# ---------------------------------------------------------------------
# Player variables

pl_follow = False

# List of encodings to check for with the fix mojibake function
encodings = ['cp932', 'utf-8', 'big5hkscs', 'gbk']  # These are the most common for Japanese

track_box = False

transcode_list = []
transcode_state = ""

taskbar_progress = True
QUE = []

playing_in_queue = 0
draw_sep_hl = False

# -------------------------------------------------------------------------------
# Playlist Variables
playlist_position = 0
playlist_playing = -1
playlist_selected = -1

loading_in_progress = False

random_mode = False
repeat_mode = False

# Functions to generate empty playlist
# Playlist is [Name, playing, playlist, position, hide folder title, selected, uid, last_folder]

def pl_uid_gen():
    return random.randrange(100, 10000000)

def pl_gen(title='Default',
           playing=0,
           playlist=None,
           position=0,
           hide_title=0,
           selected=0):

    if playlist == None:
        playlist = []

    return copy.deepcopy([title, playing, playlist, position, hide_title, selected, pl_uid_gen(), ""])

multi_playlist = [pl_gen()] # Create default playlist

default_playlist = multi_playlist[0][2]
playlist_active = 0

rename_playlist_box = False
rename_index = 0

quick_search_mode = False
search_index = 0

lfm_password = ""
lfm_username = ""
lfm_hash = ""
# ----------------------------------------
# Playlist right click menu

r_menu_index = 0

# Library and loader Variables--------------------------------------------------------
master_library = {}

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

folder_image_offsets = {}
db_version = 0.0

media_key_mode = 0

albums = []
album_position = 0


class Prefs:    # Used to hold any kind of settings
    def __init__(self):
        self.colour_from_image = False
        self.dim_art = False
        self.prefer_side = True  # Saves whether side panel is shown or not
        self.pause_fade_time = 400
        self.change_volume_fade_time = 400
        self.cross_fade_time = 700
        self.volume_wheel_increment = 2
        self.encoder_output = user_directory + '/encoder/'
        self.rename_folder_template = "%a - %b"
        self.rename_tracks_template = "%n. %a - %t%x"

        self.enable_web = False
        self.allow_remote = True
        self.expose_web = False

        self.enable_transcode = True
        self.show_rym = False
        self.show_wiki = True
        self.prefer_bottom_title = True
        self.append_date = True

        self.transcode_codec = 'opus'
        self.transcode_mode = 'single'
        self.transcode_bitrate = 64

        self.line_style = 1
        self.device = 1
        self.device_name = ""

        self.cache_gallery = False
        self.gallery_row_scroll = False
        self.gallery_scroll_wheel_px = 90

        self.playlist_font_size = 15
        self.playlist_row_height = 20

        self.tag_editor_name = ""
        self.tag_editor_target = ""
        self.tag_editor_path = ""

        self.use_title = False
        self.auto_extract = False
        self.auto_del_zip = False
        self.pl_thumb = False

        self.windows_font_family = None
        self.windows_font_weight = 500
        self.windows_font_weight_bold = 600

        self.linux_font = "Noto Sans"
        self.linux_bold_font = "Noto Sans Bold"

        self.spec2_scroll = False

        self.spec2_p_base = [10, 10, 100]
        self.spec2_p_multiply = [0.5, 1, 1]

        self.spec2_base = [10, 10, 100]
        self.spec2_multiply = [0.5, 1, 1]
        self.spec2_colour_setting = 'custom'

        self.auto_lfm = False
        self.scrobble_mark = False
        self.enable_mpris = True
        
        self.server_port = 7590
        self.mkey = True
        self.replay_gain = 0  # 0=off 1=track 2=album
        self.radio_page_lyrics = False

        self.show_gimage = True
        self.end_setting = "stop"
        self.show_gen = False
        self.show_lyrics_side = True

        self.log_vol = False

        self.ui_scale = 1


prefs = Prefs()


class GuiVar:   # Use to hold any variables for use in relation to UI
    def update_layout(self):
        global update_layout
        update_layout = True

    def __init__(self):

        self.scale = prefs.ui_scale

        self.window_id = 0
        self.update = 2  # UPDATE
        self.turbo = False
        self.turbo_next = 0
        self.pl_update = 1
        self.lowered = False
        self.request_raise = False
        self.maximized = False

        self.message_box = False
        self.message_text = ""
        self.message_mode = 'info'
        self.message_subtext = ""


        self.save_size = [450, 310]
        self.show_playlist = True
        self.show_bottom_title = False
        self.show_top_title = True
        self.search_error = False

        self.level_update = False
        self.level_time = Timer()
        self.level_peak = [0, 0]
        self.level = 0
        self.time_passed = 0
        self.level_meter_colour_mode = 3

        self.vis = 2  # visualiser mode setting
        self.spec = None
        self.s_spec = [0] * 24
        self.update_spec = 0

        #self.spec_rect = [0, 5, 80, 20]  # x = 72 + 24 - 6 - 10

        self.spec_y = 5 * self.scale
        self.spec_w = 80 * self.scale
        self.spec_h = 20 * self.scale
        self.spec1_rec = SDL_Rect(0, self.spec_y, self.spec_w, self.spec_h)

        self.bar = SDL_Rect(10, 10, 3 * self.scale, 10)

        self.combo_mode = False
        self.showcase_mode = False
        self.display_time_mode = 0

        self.pl_text_real_height = 12
        self.pl_title_real_height = 11

        self.row_extra = 0
        self.test = False
        self.cursor_mode = 0

        self.light_mode = False
        self.draw_frame = False

        self.level_2_click = False
        self.universal_y_text_offset = 0

        self.star_text_y_offset = 0

        self.set_bar = False
        self.set_mode = False
        self.set_height = 25 * self.scale
        self.set_hold = -1
        self.set_label_hold = -1
        self.set_point = 0
        self.set_old = 0
        self.pl_st = [['Artist', 156, False], ['Title', 188, False], ['T', 40, True], ['Album', 153, False], ['P', 28, True], ['Starline', 86, True], ['Date', 48, True], ['Codec', 55, True], ['Time', 53, True]]

        self.panelBY = 51 * self.scale
        self.panelY = 30 * self.scale

        self.artboxY = self.panelY + (8 * self.scale)

        self.playlist_top = self.panelY + (8 * self.scale)
        self.playlist_top_bk = self.playlist_top
        self.offset_extra = 0
        self.scroll_hide_box = (0, self.panelY, 28, window_size[1] - self.panelBY - self.panelY)

        self.playlist_row_height = 16
        self.playlist_text_offset = 0
        self.row_font_size = 13
        self.compact_bar = False
        self.abc = None
        self.ttext = None
        self.side_panel_size = 80 + int(window_size[0] * 0.18)
        self.playlist_width = int(window_size[0] * 0.65) + 25

        self.set_load_old = False

        self.win_text = False
        self.cairo_text = False
        if system == 'windows':
            self.win_text = True
        elif system == "linux":
            self.cairo_text = True
        self.win_fore = [255, 255, 255, 255]

        self.trunk_end = "..." # "…"
        self.temp_themes = {}
        self.theme_temp_current = -1

        self.pl_title_y_offset = 0
        self.pl_title_font_offset = -1

        self.playlist_box_d_click = -1

        self.gallery_show_text = False
        self.bb_show_art = False
        self.show_stars = True

        self.spec2_y = 22 * self.scale
        self.spec2_w = 140 * self.scale
        self.spec2 = [0] * self.spec2_y
        self.spec2_phase = 0
        self.spec2_buffers = []
        self.spec2_tex = None
        self.spec2_rec = SDL_Rect(1230, 4 * self.scale, self.spec2_w, self.spec2_y)
        self.spec2_source = SDL_Rect(900, 4 * self.scale, self.spec2_w, self.spec2_y)
        self.spec2_dest = SDL_Rect(900, 4 * self.scale, self.spec2_w, self.spec2_y)
        self.spec2_position = 0
        self.spec2_timer = Timer()
        self.spec2_timer.set()

        self.level_w = 5 * self.scale
        self.level_y = 16 * self.scale
        self.level_s = 1 * self.scale
        self.level_ww = 79 * self.scale
        self.level_hh = 18 * self.scale
        self.spec_level_rec = SDL_Rect(0, self.level_y - 10 * self.scale, self.level_ww, self.level_hh)

        self.rename_folder_box = False

        self.present = False
        self.drag_source_position = (0, 0)
        self.album_tab_mode = False
        self.main_art_box = (0, 0, 10, 10)
        self.gall_tab_enter = False

        self.flag_special_cursor = False

        self.lightning_copy = False

        self.gallery_animate_highlight_on = 0

        self.seek_cur_show = False
        self.cur_time = "0"
        self.force_showcase_index = -1

        self.frame_callback_list = []
        
        self.playlist_left = 20 * self.scale
        self.image_downloading = False
        self.tc_cancel = False
        self.im_cancel = False
        self.force_search = False

        self.pl_pulse = False


gui = GuiVar()


# Functions for reading and setting play counts
class StarStore:

    def __init__(self):

        self.db = {}

    def key(self, index):
        return pctl.master_library[index].artist, pctl.master_library[index].title, pctl.master_library[index].filename

    def object_key(self, track):

        return track.artist, track.title, track.filename

    # Increments the play time
    def add(self, index, value):

        key = self.key(index)
        if key in self.db:
            self.db[key][0] += value
            if value < 0 and self.db[key][0] < 0:
                self.db[key][0] = 0
        else:
            self.db[key] = [value, ""]

    # Returns the track play time
    def get(self, index):

        key = self.key(index)
        if key in self.db:
            return self.db[key][0]
        else:
            return 0

    def get_by_object(self, track):

        key = self.object_key(track)
        if key in self.db:
            return self.db[key][0]
        else:
            return 0

    def get_total(self):

        return sum(item[0] for item in self.db.values())

    def full_get(self, index):

        key = self.key(index)
        if key in self.db:
            return self.db[key]
        else:
            return None

    def remove(self, index):

        key = self.key(index)
        if key in self.db:
            del self.db[key]

    def insert(self, index, object):

        key = self.key(index)
        self.db[key] = object


star_store = StarStore()


class Fonts:    # Used to hold font sizes (I forget to use this)

    def __init__(self):

        self.tabs = 211
        self.panel_title = 213

        self.side_panel_line1 = 214
        self.side_panel_line2 = 13

        self.bottom_panel_time = 212

        if system == 'windows':
            self.bottom_panel_time = 12  # The Arial bold font is too big so just leaving this as normal. (lazy)

fonts = Fonts()


class Input:    # Used to keep track of button states (or should be)

    def __init__(self):

        self.mouse_click = False
        self.level_2_enter = False


input = Input()


def update_set():   # This is used to scale columns when windows is resized or items added/removed

    wid = gui.playlist_width + 31 - 16
    total = 0
    for item in gui.pl_st:
        if item[2] is False:
            total += item[1]
        else:
            wid -= item[1]

    if wid <= 75:
        wid = 75

    for i in range(len(gui.pl_st)):
        if gui.pl_st[i][2] is False:
            gui.pl_st[i][1] = int(round((gui.pl_st[i][1] / total) * wid)) #+ 1


class ColoursClass:     # Used to store colour values for UI elements. These are changed for themes.
    def grey(self, value):
        return [value, value, value, 255]

    def alpha_grey(self, value):
        return [255, 255, 255, value]

    def grey_blend_bg(self, value):
        return alpha_blend((255, 255, 255, value), self.sys_background)

    def grey_blend_bg3(self, value):
        return alpha_blend((255, 255, 255, value), self.sys_background_3)

    def __init__(self):
        self.last_album = ""
        self.link_text = [100, 200, 252, 255]

        self.sep_line = self.grey(21)
        self.bb_line = self.grey(21)
        self.tb_line = self.grey(21)
        self.art_box = self.grey(24)

        self.volume_bar_background = self.grey(30)
        #self.volume_bar_outline = self.grey(100)
        self.volume_bar_fill = self.grey(125)
        self.seek_bar_background = self.grey(30)
        #self.seek_bar_outline = self.grey(100)
        self.seek_bar_fill = self.grey(80)

        self.tab_text_active = self.grey(230)
        self.tab_text = self.grey(215)
        self.tab_background = self.grey(25)
        self.tab_highlight = self.grey(40)
        self.tab_background_active = self.grey(45)

        self.title_text = [190, 190, 190, 255]
        self.index_text = self.grey(70)
        self.time_text = self.index_text
        self.artist_text = [195, 255, 104, 255]
        self.album_text = [245, 240, 90, 255]

        self.index_playing = self.grey(200)
        self.artist_playing = [195, 255, 104, 255]
        self.album_playing = [245, 240, 90, 255]
        self.title_playing = self.grey(210)

        self.time_playing = [180, 194, 107, 255]

        self.playlist_text_missing = self.grey(85)
        self.bar_time = self.grey(70)

        self.top_panel_background = self.grey(15)
        self.side_panel_background = self.grey(18)
        self.playlist_panel_background = self.grey(21)
        self.bottom_panel_colour = self.grey(15)

        self.row_playing_highlight = [255,255,255,4]
        self.row_select_highlight = [255,255,255,5]

        self.side_bar_line1 = self.grey(210)
        self.side_bar_line2 = self.grey(200)

        self.mode_button_off = self.grey(50)
        self.mode_button_over = self.grey(200)
        self.mode_button_active = self.grey(190)

        self.media_buttons_over = self.grey(220)
        self.media_buttons_active = self.grey(220)
        self.media_buttons_off = self.grey(55)

        self.star_line = [100, 100, 100, 255]
        self.folder_title = [120, 120, 120, 255]
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

        self.menu_background = self.grey(12)
        self.menu_highlight_background = None
        self.menu_text = [200, 200, 200, 255]
        self.menu_text_disabled = self.grey(50)

        self.gallery_highlight = self.artist_playing

        self.status_info_text = [245, 205, 0, 255]
        self.streaming_text = [220, 75, 60, 255]
        self.lyrics = self.grey(210)

        #self.post_config()

    def post_config(self):
        # Pre calculate alpha blend for spec background
        self.vis_bg[0] = int(0.05 * 255 + (1 - 0.05) * self.top_panel_background[0])
        self.vis_bg[1] = int(0.05 * 255 + (1 - 0.05) * self.top_panel_background[1])
        self.vis_bg[2] = int(0.05 * 255 + (1 - 0.05) * self.top_panel_background[2])

        self.sys_background = self.menu_background
        self.sys_background_2 = self.tab_background
        self.sys_background_3 = self.top_panel_background
        self.sys_background_4 = self.bottom_panel_colour
        self.sys_tab_bg = self.tab_background
        self.sys_tab_hl = self.tab_background_active
        self.toggle_box_on = self.folder_title
        if colour_value(self.toggle_box_on) < 150:
            self.toggle_box_on = [160, 160, 160, 255]
        self.time_sub = alpha_blend([255, 255, 255, 80], self.bottom_panel_colour)
        self.bar_title_text = self.side_bar_line1

        self.gallery_artist_line = alpha_mod(self.side_bar_line2, 130)

        self.status_text_normal = self.grey(100)
        self.status_text_over = self.grey(220)

        if self.menu_highlight_background is None:
            self.menu_highlight_background = [40, 40, 40, 255]
            #self.menu_highlight_background = alpha_blend((self.artist_text[0], self.artist_text[1], self.artist_text[2], 100), self.menu_background)

        # if gui.light_mode:  # Light mode was removed
        #     self.sys_background = self.grey(20)
        #     self.sys_background_2 = self.grey(25)
        #     self.sys_tab_bg = self.grey(25)
        #     self.sys_tab_hl = self.grey(45)
        #     self.sys_background_3 = self.grey(20)
        #     self.sys_background_4 = self.grey(19)
        #     self.toggle_box_on = self.tab_background_active
        #     self.time_sub = [0, 0, 0, 200]
        #     self.gallery_artist_line = self.grey(40)
        #     self.bar_title_text = self.grey(30)
        #     self.status_text_normal = self.grey(70)
        #     self.status_text_over = self.grey(40)
        #     self.status_info_text = [40, 40, 40, 255]



colours = ColoursClass()
colours.post_config()


# This is legacy. New settings are added straight to the save list (need to overhaul)
view_prefs = {

    'split-line': True,
    'update-title': False,
    'star-lines': False,
    'side-panel': True,
    'dim-art': False,
    'pl-follow': False,
    'scroll-enable': True
}


class TrackClass:   # This is the fundamental object/data structure of a track
    # C-TC
    def __init__(self):
        self.index = 0
        self.fullpath = ""
        self.filename = ""
        self.parent_folder_path = ""
        self.parent_folder_name = ""
        self.file_ext = ""
        self.size = 0
        self.modified_time = 0

        self.artist = ""
        self.album_artist = ""
        self.title = ""
        self.length = 0
        self.bitrate = 0
        self.samplerate = 0
        self.album = ""
        self.date = ""
        self.track_number = ""
        self.track_total = ""
        self.start_time = 0
        self.is_cue = False
        self.is_embed_cue = False
        self.cue_sheet = ""
        self.genre = ""
        self.found = True
        self.skips = 0
        self.comment = ""
        self.disc_number = ""
        self.disc_total = ""
        self.lyrics = ""
        self.album_gain = None
        self.track_gain = None


class LoadClass:    # Object for import track jobs (passed to worker thread)
    def __init__(self):
        self.target = ""
        self.playlist = 0  # Playlist UID
        self.tracks = []
        self.stage = 0
        self.playlist_position = None


url_saves = []
# -----------------------------------------------------
# STATE LOADING
# Loading of program data from previous run

try:
    star_store.db = pickle.load(open(user_directory + "/star.p", "rb"))

except:
    print('No existing star.p file')

try:
    state_file = open(user_directory + "/state.p", "rb")
    save = pickle.load(state_file)

    if save[63] is not None:
        prefs.ui_scale = save[63]
        gui.__init__()

    master_library = save[0]
    master_count = save[1]
    playlist_playing = save[2]
    playlist_active = save[3]
    playlist_position = save[4]
    multi_playlist = save[5]
    volume = save[6]
    QUE = save[7]
    playing_in_queue = save[8]
    default_playlist = save[9]
    playlist_playing = save[10]
    # cue_list = save[11]
    radio_field_text = save[12]
    theme = save[13]
    folder_image_offsets = save[14]
    lfm_username = save[15]
    lfm_hash = save[16]
    db_version = save[17]
    view_prefs = save[18]
    window_size = save[19]
    gui.side_panel_size = save[20]
    # savetime = save[21]
    gui.vis = save[22]
    playlist_selected = save[23]
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
    if save[31] is not None:
        combo_mode_art_size = save[31]
    if save[32] is not None:
        gui.maximized = save[32]
    if save[33] is not None:
        prefs.prefer_bottom_title = save[33]
    if save[34] is not None:
        gui.display_time_mode = save[34]
    # if save[35] is not None:
    #     prefs.transcode_mode = save[35]
    if save[36] is not None:
        prefs.transcode_codec = save[36]
    if save[37] is not None:
        prefs.transcode_bitrate = save[37]
    if save[38] is not None:
        prefs.line_style = save[38]
    if save[39] is not None:
        prefs.cache_gallery = save[39]
    if save[40] is not None:
        prefs.playlist_font_size = save[40]
    if save[41] is not None:
        prefs.use_title = save[41]
    if save[42] is not None:
        gui.pl_st = save[42]
        gui.set_load_old = True
    if save[43] is not None:
        gui.set_mode = save[43]
        gui.set_bar = gui.set_mode
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
    if save[52] is not None:
        gui.show_stars = save[52]
    if save[53] is not None:
        prefs.auto_lfm = save[53]
    if save[54] is not None:
        prefs.scrobble_mark = save[54]
    if save[55] is not None:
        prefs.replay_gain = save[55]
    if save[56] is not None:
        prefs.radio_page_lyrics = save[56]
    if save[57] is not None:
        prefs.show_gimage = save[57]
    if save[58] is not None:
        prefs.end_setting = save[58]
    if save[59] is not None:
        prefs.show_gen = save[59]
    if save[60] is not None:
        url_saves = save[60]
    if save[61] is not None:
        prefs.auto_del_zip = save[61]
    if save[62] is not None:
        gui.level_meter_colour_mode = save[62]
    if save[63] is not None:
        prefs.show_lyrics_side = save[63]

    state_file.close()
    del save


except:
    print('Error loading save file')
    if os.path.exists(cache_directory):
        print("clearing old cache")
        shutil.rmtree(cache_directory)
        time.sleep(0.01)
        os.makedirs(cache_directory)

# temporary
if window_size is None:
    window_size = window_default_size
    gui.side_panel_size = 200


def show_message(text, message_mode='info', subtext=""):
    gui.message_box = True
    gui.message_text = text
    gui.message_mode = message_mode
    gui.message_subtext = subtext
    gui.update = 1

def track_number_process(line):
    line = str(line).split("/", 1)[0].lstrip("0")
    if dd_index and len(line) == 1:
        return "0" + line
    return line


# Upgrading from older versions
if db_version > 0:

    if db_version <= 0.8:
        print("Updating database from version 0.8 to 0.9")
        for key, value in master_library.items():
            setattr(master_library[key], 'skips', 0)

    if db_version <= 0.9:
        print("Updating database from version 0.9 to 1.1")
        for key, value in master_library.items():
            setattr(master_library[key], 'comment', "")

    if db_version <= 1.1:
        print("Updating database from version 1.1 to 1.2")
        for key, value in master_library.items():
            setattr(master_library[key], 'album_artist', "")

    if db_version <= 1.2:
        print("Updating database to version 1.3")
        for key, value in master_library.items():
            setattr(master_library[key], 'disc_number', "")
            setattr(master_library[key], 'disc_total', "")

    if db_version <= 1.3:
        print("Updating database to version 1.4")
        for key, value in master_library.items():
            setattr(master_library[key], 'lyrics', "")
            setattr(master_library[key], 'track_total', "")
        show_message(
            "Upgrade complete. Note: New attributes such as disk number won't show for existing tracks (delete state.p to reset)")

    if db_version <= 1.4:
        print("Updating database to version 1.5")
        for playlist in multi_playlist:
            playlist.append(pl_uid_gen())

    if db_version <= 1.5:
        print("Updating database to version 1.6")
        for i in range(len(multi_playlist)):
            if len(multi_playlist[i]) == 7:
                multi_playlist[i].append("")

    if db_version <= 1.6:
        print("Updating preferences to 1.7")
        gui.show_stars = False
        if install_mode:
                shutil.copy(install_directory + "/config.txt", user_directory)
                print("Rewrote user config file")

    if db_version <= 1.7:
        print("Updating database to version 1.8")
        if install_mode:
                print(".... Overwriting user config file")
                shutil.copy(install_directory + "/config.txt", user_directory)

        try:
            print(".... Updating playtime database")

            old = star_store.db
            #perf_timer.set()
            old_total = sum(old.values())
            #print(perf_timer.get())
            print("Old total: ", end='')
            print(old_total)
            star_store.db = {}

            new = {}
            for track in master_library.values():
                key = track.title + track.filename
                if key in old:
                    n_value = [old[key], ""]
                    n_key = star_store.object_key(track)
                    star_store.db[n_key] = n_value

            print("New total: ", end='')
            #perf_timer.set()
            print(star_store.get_total())
            #print(perf_timer.get())
            diff = old_total - star_store.get_total()
            print(int(diff), end='')
            print(" Secconds could not be matched to tracks. Total playtime won't be affected")
            star_store.db[("", "", "LOST")] = [diff, ""]
            print("Upgrade Complete")
        except:
            print("Error upgrading database")
            show_message("Error loading old database, did the program not exit properly after updating? Oh well.")

    if db_version <= 1.8:
        print("Updating database to 1.9")
        for key, value in master_library.items():
            setattr(master_library[key], 'track_gain', None)
            setattr(master_library[key], 'album_gain', None)
        show_message(
            "Upgrade complete. Run a tag rescan if you want enable ReplayGain")

    if db_version <= 1.9:
        print("Updating database to version 2.0")
        for key, value in master_library.items():
            setattr(master_library[key], 'modified_time', 0)
        show_message(
            "Upgrade complete. New sorting option may require tag rescan.")


    if db_version <= 2.0:
        print("Updating database to version 2.1")
        for key, value in master_library.items():
            setattr(master_library[key], 'is_embed_cue', False)
            setattr(master_library[key], 'cue_sheet', "")
        show_message(
            "Updated to v2.6.3")

# Loading Config -----------------

# main_font = 'Koruri-Regular.ttf'  # these fonts are no longer used
# alt_font = 'DroidSansFallback.ttf'
# gui_font = 'Koruri-Semibold.ttf'
#light_font = 'Koruri-Light.ttf'

path = config_directory + "/config.txt"
if os.path.isfile(os.path.join(config_directory, "config.txt")):
    with open(path, encoding="utf_8") as f:
        content = f.read().splitlines()
        for p in content:
            if len(p) == 0:
                continue
            if p[0] == " " or p[0] == "#":
                continue
            if 'log-volume-scale=True' in p:
                prefs.log_vol = True
            if 'tag-editor-path=' in p:
                result = p.split('=')[1]
                prefs.tag_editor_path = result
            if 'tag-editor-program=' in p:
                result = p.split('=')[1]
                prefs.tag_editor_target = result
            if 'tag-editor-name=' in p:
                result = p.split('=')[1]
                prefs.tag_editor_name = result
            # if 'font-regular=' in p:
            #     result = p.split('=')[1]
            #     main_font = result
            # if 'font-fallback=' in p:
            #     result = p.split('=')[1]
            #     alt_font = result
            # if 'font-bold=' in p:
            #     result = p.split('=')[1]
            #     gui_font = result
            # if 'font-extra=' in p:
            #     result = p.split('=')[1]
            #     light_font = result
            if 'font-height-offset=' in p:
                result = p.split('=')[1]
                try:
                    gui.universal_y_text_offset = int(result)
                except:
                    print("Expected number")

            if 'linux-font-star-offset=' in p and system == 'linux':
                result = p.split('=')[1]
                try:
                    gui.star_text_y_offset = int(result)
                except:
                    print("Expected number")

            if 'windows-font-star-offset=' in p and system == 'windows':
                result = p.split('=')[1]
                try:
                    gui.star_text_y_offset = int(result)
                except:
                    print("Expected number")

            if 'scroll-gallery-wheel=' in p:
                result = p.split('=')[1]
                if result.isdigit() and -1000 < int(result) < 1000:
                    prefs.gallery_scroll_wheel_px = int(result)

            if 'scroll-gallery-row=True' in p:
                prefs.gallery_row_scroll = True

            if 'pause-fade-time=' in p:
                result = p.split('=')[1]
                if result.isdigit() and 50 < int(result) < 3000:
                    prefs.pause_fade_time = int(result)
            if 'cross-fade-time=' in p:
                result = p.split('=')[1]
                if result.isdigit() and 50 < int(result) < 3000:
                    prefs.cross_fade_time = int(result)
            # if 'scrobble-mark=True' in p:
            #     scrobble_mark = True

            if 'output-dir=' in p:

                prefs.encoder_output = p.split('=')[1]
                prefs.encoder_output = prefs.encoder_output.replace('\\', '/')
                if prefs.encoder_output[-1] != "/":
                    prefs.encoder_output += "/"

                print('Encode output: ' + prefs.encoder_output)

            # if 'windows-native-font-rendering=True' in p and system == 'windows':
            #     gui.win_text = True
            if 'windows-set-font-family=' in p:
                result = p.split('=')[1]
                prefs.windows_font_family = result
            if 'windows-font-use-bold=True' in p:
                result = p.split('=')[1]
                prefs.windows_font_weight = 700
                #prefs.windows_font_weight_bold = 700

            if 'linux-font=' in p:
                result = p.split('=')[1]
                prefs.linux_font = result
            if 'linux-bold-font=' in p:
                result = p.split('=')[1]
                prefs.linux_bold_font = result

            if 'vis-scroll=True' in p:
                prefs.spec2_scroll = True
            if 'vis-base-colour=' in p:
                result = p.split('=')[1]
                prefs.spec2_base = list(map(int, result.split(',')))
            if 'vis-colour-multiply=' in p:
                result = p.split('=')[1]
                prefs.spec2_multiply = list(map(float, result.split(',')))

            if 'rename-tracks-default=' in p:
                result = p.split('=')[1]
                prefs.rename_tracks_template = result
            if 'rename-folder-default=' in p:
                result = p.split('=')[1]
                prefs.rename_folder_template = result
            if 'linux-mpris-enable=False' in p:
                prefs.enable_mpris = False
            if 'mediakey=False' in p:
                prefs.mkey = False

else:
    print("Warning: Missing config file")


try:
    star_lines = view_prefs['star-lines']
    update_title = view_prefs['update-title']
    prefs.prefer_side = view_prefs['side-panel']
    prefs.dim_art = view_prefs['dim-art']
    gui.turbo = view_prefs['level-meter']
    pl_follow = view_prefs['pl-follow']
    scroll_enable = view_prefs['scroll-enable']
    break_enable = view_prefs['break-enable']
    dd_index = view_prefs['dd-index']
    # custom_line_mode = view_prefs['custom-line']
    #thick_lines = view_prefs['thick-lines']
    prefs.append_date = view_prefs['append-date']
except:
    print("warning: error loading settings")

if prefs.prefer_side is False:
    side_panel_enable = False

# get_len = 0
# get_len_filepath = ""


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


# This function takes a track object and scans metadata for it. (Filepath needs to be set)
def tag_scan(nt):

    if nt.is_embed_cue:
        return nt

    try:
        nt.modified_time = os.path.getmtime(nt.fullpath)
        if nt.file_ext == "FLAC":

            # print("get opus")
            audio = Flac(nt.fullpath)
            audio.read()

            # print(audio.title)

            nt.length = audio.length
            nt.title = audio.title
            nt.artist = audio.artist
            nt.album = audio.album
            nt.date = audio.date
            nt.samplerate = audio.sample_rate
            nt.size = os.path.getsize(nt.fullpath)
            nt.track_number = audio.track_number
            nt.genre = audio.genre
            nt.album_artist = audio.album_artist
            nt.disc_number = audio.disc_number
            nt.lyrics = audio.lyrics
            nt.bitrate = int(nt.size / nt.length * 8 / 1024)
            nt.track_total = audio.track_total
            nt.disk_total = audio.disc_total
            nt.comment = audio.comment
            nt.track_gain = audio.track_gain
            nt.album_gain = audio.album_gain
            nt.cue_sheet = audio.cue_sheet


            return nt

        elif nt.file_ext == "WAV":

            audio = Wav(nt.fullpath)
            audio.read()

            nt.samplerate = audio.sample_rate
            nt.length = audio.length

            return nt

        elif nt.file_ext == "OPUS" or nt.file_ext == "OGG":

            # print("get opus")
            audio = Opus(nt.fullpath)
            audio.read()

            # print(audio.title)

            nt.length = audio.length
            nt.title = audio.title
            nt.artist = audio.artist
            nt.album = audio.album
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
            nt.disk_total = audio.disc_total
            nt.comment = audio.comment
            nt.track_gain = audio.track_gain
            nt.album_gain = audio.album_gain
            if nt.bitrate == 0 and nt.length > 0:
                nt.bitrate = int(nt.size / nt.length * 8 / 1024)
            return nt

        elif nt.file_ext == "APE" or nt.file_ext == "WV" or nt.file_ext == "TTA":

            audio = Ape(nt.fullpath)
            audio.read()

            # print(audio.title)

            nt.length = audio.length
            nt.title = audio.title
            nt.artist = audio.artist
            nt.album = audio.album
            nt.date = audio.date
            nt.samplerate = audio.sample_rate
            nt.size = os.path.getsize(nt.fullpath)
            nt.track_number = audio.track_number
            nt.genre = audio.genre
            nt.album_artist = audio.album_artist
            nt.disc_number = audio.disc_number
            nt.lyrics = audio.lyrics
            nt.track_gain = audio.track_gain
            nt.album_gain = audio.album_gain
            if nt.length > 0:
                nt.bitrate = int(nt.size / nt.length * 8 / 1024)
            nt.track_total = audio.track_total
            nt.disk_total = audio.disc_total
            nt.comment = audio.comment

            if audio.found_tag is False:
                try:
                    tag = stagger.read_tag(nt.fullpath)
                    print("Tag Scan: Found ID3v2 tag")
                    nt.album_artist = tag.album_artist
                    nt.disc_number = str(tag.disc)
                    nt.disc_total = str(tag.disc_total)
                    nt.track_total = str(tag.track_total)
                    nt.title = tag.title
                    nt.artist = tag.artist
                    nt.album = tag.album
                    nt.genre = tag.genre
                    nt.date = tag.date
                except:
                    print("Tag Scan: Couldn't find ID3v2 tag or APE tag")

            return nt

        else:

            # Use HSAUDIOTAG
            audio = auto.File(nt.fullpath)

            nt.length = audio.duration
            nt.title = rm_16(audio.title)
            nt.artist = rm_16(audio.artist)
            nt.album = rm_16(audio.album)
            nt.track_number = str(audio.track)
            nt.bitrate = audio.bitrate
            nt.date = audio.year
            nt.genre = rm_16(audio.genre)
            nt.samplerate = audio.sample_rate
            nt.size = audio.size
            if audio.comment != "":
                if audio.comment[0:3] == '000':
                    pass
                elif len(audio.comment) > 4 and audio.comment[2] == '+':
                    pass
                else:
                    nt.comment = audio.comment

            if nt.file_ext == "MP3":
                tag = stagger.read_tag(nt.fullpath)
                nt.album_artist = tag.album_artist
                nt.disc_number = str(tag.disc)
                nt.disc_total = str(tag.disc_total)
                nt.track_total = str(tag.track_total)
                nt.genre = tag.genre
                nt.date = tag.date
                # if TXXX in tag:
                #     print(tag[TXXX])
                #     print(nt.fullpath)
                if TXXX in tag:
                    for item in tag[TXXX]:
                        if hasattr(item, 'description'):
                            if item.description == "replaygain_album_gain":
                                nt.album_gain = float(item.value.strip(" dB"))
                            if item.description == "replaygain_track_gain":
                                nt.track_gain = float(item.value.strip(" dB"))

                if USLT in tag:
                    lyrics = tag[USLT][0].text
                    if len(lyrics) > 30 and ".com" not in lyrics:
                        nt.lyrics = lyrics
                    elif len(lyrics) > 2:
                        print("Tag Scan: Possible spam found in lyric field")
                        print("     In file: " + nt.fullpath)
                        print("     Value: " + lyrics)

                if SYLT in tag:
                    print("Tag Scan: Found unhandled id3 field 'Synced Lyrics'")
                    print(tag[SYLT][0].text)

            return nt

    except stagger.errors.NoTagError as err:
        # print("Tag Scanner: " + str(err))
        # print("      In file: " + nt.fullpath)
        return nt
    except:

        print("Warning: Tag read error")
        return nt


# Main class that controls playback (play, pause, stepping, playlists, queue etc). Sends commands to backend.
class PlayerCtl:
    # C-PC
    def __init__(self):

        # Database

        self.total_playtime = 0
        self.master_library = master_library
        #self.star_library = star_library

        # Misc player control

        self.url = ""
        self.save_urls = url_saves
        self.tag_meta = ""
        self.encoder_pause = 0

        # Playback

        self.track_queue = QUE
        self.queue_step = playing_in_queue
        self.playing_time = 0
        self.playlist_playing = playlist_playing  # track in playlist that is playing
        self.target_open = ""
        self.target_object = None
        self.start_time = 0
        self.b_start_time = 0
        self.playerCommand = ""
        self.playerCommandReady = False
        self.playing_state = 0
        self.playing_length = 0
        self.jump_time = 0
        self.random_mode = random_mode
        self.repeat_mode = repeat_mode
        self.last_playing_time = 0
        self.multi_playlist = multi_playlist
        self.playlist_active = playlist_active  # view only
        self.active_playlist_playing = playlist_active  # playlist that is playing from
        self.force_queue = []
        self.left_time = 0
        self.left_index = 0
        self.player_volume = volume
        self.new_time = 0
        self.time_to_get = []
        self.a_time = 0
        self.b_time = 0
        self.playlist_backup = []
        self.active_replaygain = 0
        self.auto_stop = False

        # Broadcasting

        self.broadcast_active = False
        self.join_broadcast = False
        self.broadcast_playlist = 0
        self.broadcast_position = 0
        self.broadcast_index = 0
        self.broadcast_time = 0
        self.broadcast_last_time = 0
        self.broadcast_line = ""
        self.broadcast_clients = []

        self.record_stream = False
        self.record_title = ""

        # Bass

        self.bass_devices = []
        self.set_device = 0

        self.mpris = None

    def notify_update(self):

        if self.mpris is not None:
            self.mpris.update()

    def playing_playlist(self):
        return self.multi_playlist[self.active_playlist_playing][2]


    def playing_ready(self):
        return len(self.track_queue) > 0

    def render_playlist(self):

        if taskbar_progress and system == 'windows':
            global windows_progress
            windows_progress.update(True)
        gui.pl_update = 1

    def show_selected(self):

        if gui.playlist_view_length < 1:
            return 0

        global playlist_position
        global playlist_selected
        global shift_selection


        for i in range(len(self.multi_playlist[self.playlist_active][2])):

            if i == playlist_selected:

                if i < playlist_position:
                    playlist_position = i - random.randint(2, int((gui.playlist_view_length / 3) * 2) + int(
                        gui.playlist_view_length / 6))
                elif abs(playlist_position - i) > gui.playlist_view_length:
                    playlist_position = i
                    if i > 6:
                        playlist_position -= 5
                    if i > gui.playlist_view_length * 1 and i + (gui.playlist_view_length * 2) < len(
                            self.multi_playlist[self.playlist_active][2]) and i > 10:
                        playlist_position = i - random.randint(2, int(gui.playlist_view_length / 3) * 2)
                    break

        if gui.combo_mode:
            combo_pl_render.prep(True)

        self.render_playlist()

        return 0

    def g(self, index):

        return self.master_library[index]

    def playing_object(self):
        if len(self.track_queue) > 0:
            return self.master_library[self.track_queue[self.queue_step]]
        else:
            return None

    def show_current(self, select=True, playing=False, quiet=False, this_only=False, highlight=False, index=None):

        # print("show------")
        # print(select)
        # print(playing)
        # print(quiet)
        # print(this_only)
        # print(highlight)
        # print("--------")

        if len(self.track_queue) == 0:
            return 0

        track_index = self.track_queue[self.queue_step]
        if index is not None:
            track_index = index

        # Switch to source playlist
        if self.playlist_active != self.active_playlist_playing and (
                    track_index not in self.multi_playlist[self.playlist_active][2]):
            switch_playlist(self.active_playlist_playing)

        if gui.playlist_view_length < 1:
            return 0


        global playlist_position
        global playlist_selected
        global shift_selection

        for i in range(len(self.multi_playlist[self.playlist_active][2])):
            if len(self.track_queue) > 0 and self.multi_playlist[self.playlist_active][2][i] == track_index:

                if self.playlist_active == self.active_playlist_playing and track_index == \
                        self.multi_playlist[self.playlist_active][2][self.playlist_playing] and \
                        i != self.playlist_playing:
                    #continue
                    i = self.playlist_playing


                if select:
                    playlist_selected = i

                    # Make the found track the playing track
                    self.playlist_playing = i
                    self.active_playlist_playing = self.playlist_active

                if playing:
                    self.playlist_playing = i

                if not (quiet and self.playing_object().length < 15):

                    if i == playlist_position - 1 and playlist_position > 1:
                        playlist_position -= 1

                    elif playlist_position + gui.playlist_view_length - 2 == i and i < len(
                            self.multi_playlist[self.playlist_active][2]) - 5:
                        playlist_position += 3
                    elif i < playlist_position:
                        playlist_position = i - random.randint(2, int((gui.playlist_view_length / 3) * 2) + int(
                            gui.playlist_view_length / 6))
                    elif abs(playlist_position - i) > gui.playlist_view_length:
                        playlist_position = i
                        if i > 6:
                            playlist_position -= 5
                        if i > gui.playlist_view_length * 1 and i + (gui.playlist_view_length * 2) < len(
                                self.multi_playlist[self.playlist_active][2]) and i > 10:
                            playlist_position = i - random.randint(2, int(gui.playlist_view_length / 3) * 2)
                break
        else:  # Search other all other playlists
            if not this_only:
                for i, playlist in enumerate(self.multi_playlist):
                    if track_index in playlist[2]:

                        switch_playlist(i)
                        self.show_current(select, playing, quiet, this_only=True)
                        break

        if playlist_position < 0:
            playlist_position = 0
        if playlist_position > len(self.multi_playlist[self.playlist_active][2]) - 1:
            print("Run Over")

        if select:
            shift_selection = []

        self.render_playlist()

        if gui.combo_mode:
            combo_pl_render.prep(True)

        if album_mode and not quiet:
            if highlight:
                gui.gallery_animate_highlight_on = goto_album(playlist_selected)
                gallery_select_animate_timer.set()
            else:
                goto_album(playlist_selected)

        return 0

    def set_volume(self, notify=True):

        self.playerCommand = 'volume'
        self.playerCommandReady = True
        if notify:
            self.notify_update()

    def revert(self):

        if self.queue_step == 0:
            return

        prev = 0
        while len(self.track_queue) > prev + 1 and prev < 5:
            if self.track_queue[len(self.track_queue) - 1 - prev] == self.left_index:
                self.queue_step = len(self.track_queue) - 1 - prev
                self.jump_time = self.left_time
                self.playing_time = self.left_time
                break
            prev += 1
        else:
            self.queue_step -= 1
            self.jump_time = 0
            self.playing_time = 0

        self.target_open = pctl.master_library[self.track_queue[self.queue_step]].fullpath
        self.target_object = pctl.master_library[self.track_queue[self.queue_step]]
        self.start_time = pctl.master_library[self.track_queue[self.queue_step]].start_time
        self.playing_length = pctl.master_library[self.track_queue[self.queue_step]].length
        self.playerCommand = 'open'
        self.playerCommandReady = True
        self.playing_state = 1

        self.show_current()
        self.render_playlist()

    def play_target_rr(self):

        self.playing_length = pctl.master_library[self.track_queue[self.queue_step]].length

        if self.playing_length > 2:
            random_start = random.randrange(1, int(self.playing_length) - 45 if self.playing_length > 50 else int(
                self.playing_length))
        else:
            random_start = 0

        self.playing_time = random_start
        self.target_open = pctl.master_library[self.track_queue[self.queue_step]].fullpath
        self.target_object = pctl.master_library[self.track_queue[self.queue_step]]
        self.start_time = pctl.master_library[self.track_queue[self.queue_step]].start_time
        self.jump_time = random_start
        self.playerCommand = 'open'
        self.playerCommandReady = True
        self.playing_state = 1

        self.last_playing_time = random_start

        if update_title:
            update_title_do()

    def play_target(self, gapless=False):

        self.playing_time = 0
        # print(self.track_queue)
        self.target_open = pctl.master_library[self.track_queue[self.queue_step]].fullpath
        self.target_object = pctl.master_library[self.track_queue[self.queue_step]]
        self.start_time = pctl.master_library[self.track_queue[self.queue_step]].start_time
        if not gapless:
            self.playerCommand = 'open'
            self.playerCommandReady = True
        else:
            self.playerCommand = 'gapless'
        self.playing_state = 1
        self.playing_length = pctl.master_library[self.track_queue[self.queue_step]].length
        self.last_playing_time = 0

        if update_title:
            update_title_do()
        self.notify_update()

    def jump(self, index, pl_position=None):

        if len(self.track_queue) > 0:
            self.left_time = self.playing_time
            self.left_index = self.track_queue[self.queue_step]

            if self.playing_state == 1 and self.left_time > 5 and self.playing_length - self.left_time > 15 :
                pctl.master_library[self.left_index].skips += 1

        global playlist_hold
        gui.update_spec = 0
        self.active_playlist_playing = self.playlist_active
        self.track_queue.append(index)
        self.queue_step = len(self.track_queue) - 1
        playlist_hold = False
        self.play_target()

        if pl_position is not None:
            self.playlist_playing = pl_position


    def back(self):

        if len(self.track_queue) > 0:
            self.left_time = self.playing_time
            self.left_index = self.track_queue[self.queue_step]

        gui.update_spec = 0
        # Move up
        if self.random_mode is False and self.playlist_playing > 0:

            if len(self.track_queue) > 0 and self.playing_playlist()[self.playlist_playing] != self.track_queue[
                self.queue_step]:
                try:
                    self.playlist_playing = self.playing_playlist().index(self.track_queue[self.queue_step])
                except:
                    random_jump = random.randrange(len(self.playing_playlist()))
                    self.playlist_playing = random_jump

            self.playlist_playing -= 1
            self.track_queue.append(self.playing_playlist()[self.playlist_playing])
            self.queue_step = len(self.track_queue) - 1
            self.play_target()

        elif self.random_mode is True and self.queue_step > 0:
            self.queue_step -= 1
            self.play_target()
        else:
            print("BACK: NO CASE!")

        if self.playlist_active == self.active_playlist_playing:
            self.show_current(False, True)

        if album_mode:
            goto_album(self.playlist_playing)
        if gui.combo_mode and self.playlist_active == self.active_playlist_playing:
            self.show_current()

        self.render_playlist()
        self.notify_update()

    def stop(self, block=False, run=False):
        self.playerCommand = 'stop'
        if run:
            self.playerCommand = 'runstop'

        self.playerCommandReady = True
        self.record_stream = False
        if len(self.track_queue) > 0:
            self.left_time = self.playing_time
            self.left_index = self.track_queue[self.queue_step]
        previous_state = self.playing_state
        self.playing_time = 0
        self.playing_state = 0
        self.render_playlist()

        gui.update_spec = 0
        # gui.update_level = True  # Allows visualiser to enter decay sequence
        gui.update = True
        if update_title:
            update_title_do()  # Update title bar text

        if block:
            loop = 0
            while self.playerCommand != "stopped":
                time.sleep(0.03)
                if loop > 110:
                    break

        self.notify_update()
        return previous_state

    def pause(self):
        if self.playing_state == 3:
            return
        if self.playing_state == 1:
            self.playerCommand = 'pause'
            self.playing_state = 2
        elif self.playing_state == 2:
            self.playerCommand = 'pause'
            self.playing_state = 1
        self.playerCommandReady = True

        self.render_playlist()
        self.notify_update()

    def pause_only(self):
        if self.playing_state == 1:
            self.playerCommand = 'pause'
            self.playing_state = 2

            self.playerCommandReady = True
            self.render_playlist()
            self.notify_update()

    def play_pause(self):
        if self.playing_state > 0:
            self.pause()
        else:
            self.play()

    def seek_decimal(self, decimal):

        if self.playing_state == 1 or self.playing_state == 2:
            if decimal > 1:
                decimal = 1
            elif decimal < 0:
                decimal = 0
            self.new_time = pctl.playing_length * decimal
            # print('seek to:' + str(pctl.new_time))
            self.playerCommand = 'seek'
            self.playerCommandReady = True
            self.playing_time = self.new_time

            if system == 'windows' and taskbar_progress:
                windows_progress.update(True)

            if self.mpris is not None:
                self.mpris.seek_do(self.playing_time)

    def seek_time(self, new):

        if new > self.playing_length + 5:
            print("INVALID SEEK VALUE")
            pass

        if new < 0:
            new = 0

        self.new_time = new
        self.playing_time = new

        self.playerCommand = 'seek'
        self.playerCommandReady = True

        print("seek: " + str(new))

        if self.mpris is not None:
            self.mpris.seek_do(self.playing_time)

    def play(self):

        # Unpause if paused
        if self.playing_state == 2:
            self.playerCommand = 'pause'
            self.playerCommandReady = True
            self.playing_state = 1

        # If stopped...
        elif pctl.playing_state == 0:

            # If the queue is empty
            if self.track_queue == [] and len(self.multi_playlist[self.active_playlist_playing][2]) > 0:
                self.track_queue.append(self.multi_playlist[self.active_playlist_playing][2][0])
                self.queue_step = 0
                self.playlist_playing = 0
                self.active_playlist_playing = 0

                self.play_target()

            # If the queue is not empty, play?
            elif len(self.track_queue) > 0:
                self.play_target()

        self.render_playlist()
        self.notify_update()

    def test_progress(self):

        if self.playing_state == 1 and self.playing_time + (
                    prefs.cross_fade_time / 1000) + 0 >= self.playing_length and self.playing_time > 0.2:

            if self.playing_length == 0 and self.playing_time < 4:
                # If the length is unknown, allow backend some time to provide a duration
                pass
            else:

                if pctl.auto_stop:
                    self.stop(run=True)
                    gui.update += 2
                    pctl.auto_stop = False

                elif self.repeat_mode is True:

                    self.playing_time = 0
                    self.new_time = 0
                    self.playerCommand = 'seek'
                    self.playerCommandReady = True

                elif self.random_mode is False and len(default_playlist) > self.playlist_playing and \
                                self.master_library[default_playlist[self.playlist_playing]].is_cue is True \
                        and self.master_library[default_playlist[self.playlist_playing + 1]].filename == \
                                self.master_library[default_playlist[self.playlist_playing]].filename and int(
                    self.master_library[default_playlist[self.playlist_playing]].track_number) == int(
                    self.master_library[default_playlist[self.playlist_playing + 1]].track_number) - 1:
                    print("CUE Gap-less")
                    self.playlist_playing += 1
                    self.queue_step += 1
                    self.track_queue.append(default_playlist[self.playlist_playing])

                    self.playing_state = 1
                    self.playing_time = 0
                    self.playing_length = self.master_library[self.track_queue[self.queue_step]].length
                    self.start_time = self.master_library[self.track_queue[self.queue_step]].start_time

                    gui.update += 1
                    gui.pl_update = 1

                else:
                    if False:  # self.playing_time < self.playing_length:
                        print("advance gapless")
                        self.advance(quiet=True, gapless=True)
                    else:
                        print("advance normal")
                        self.advance(quiet=True)

                    self.playing_time = 0


    def advance(self, rr=False, quiet=False, gapless=False, inplace=False):

        # Temporary Workaround
        quick_d_timer.set()

        # Trim the history if it gets too long
        while len(self.track_queue) > 250:
            del self.track_queue[0]
            self.queue_step -= 1

        if len(self.track_queue) > 0:
            self.left_time = self.playing_time
            self.left_index = self.track_queue[self.queue_step]

        # Test to register skip (not currently used for anything)
        if self.playing_state == 1 and 1.2 < self.left_time < 45:
            pctl.master_library[self.left_index].skips += 1
            # print('skip registered')

        pctl.playing_length = 100
        pctl.playing_time = 0

        gui.update_spec = 0

        old = self.queue_step

        # Force queue (middle click on track)
        if len(self.force_queue) > 0:

            target_index = self.force_queue[0][0]
            self.active_playlist_playing = self.force_queue[0][2]
            if target_index not in self.playing_playlist():
                del self.force_queue[0]
                self.advance()
                return

            self.playlist_playing = self.force_queue[0][1]
            self.track_queue.append(target_index)
            self.queue_step = len(self.track_queue) - 1
            self.play_target()
            del self.force_queue[0]

        # Don't do anything if playlist is empty
        elif len(self.playing_playlist()) == 0:
            return 0

        # If random, jump to random track
        elif (self.random_mode or rr) and len(self.playing_playlist()) > 0:
            self.queue_step += 1
            if self.queue_step == len(self.track_queue):
                random_jump = random.randrange(len(self.playing_playlist()))
                self.playlist_playing = random_jump
                self.track_queue.append(self.playing_playlist()[random_jump])
            if rr:
                self.play_target_rr()
            else:
                self.play_target()
                # if album_mode:
                #     goto_album(self.playlist_playing)

            if inplace and self.queue_step > 1:
                del self.track_queue[old]
                self.queue_step -= 1


        # If not random mode, Step down 1 on the playlist
        elif self.random_mode is False and len(self.playing_playlist()) > 0:

            # Stop at end of playlist
            if self.playlist_playing == len(self.playing_playlist()) - 1:
                if prefs.end_setting == 'stop':
                    self.playing_state = 0
                    self.playerCommand = 'runstop'
                    self.playerCommandReady = True
                elif prefs.end_setting == 'advance':

                    if pctl.active_playlist_playing < len(pctl.multi_playlist) - 1 and \
                            len(pctl.multi_playlist[pctl.active_playlist_playing + 1][2]) > 0:
                        pctl.active_playlist_playing += 1
                        pctl.playlist_playing = -1
                        pctl.advance()
                    else:
                        self.playing_state = 0
                        self.playerCommand = 'runstop'
                        self.playerCommandReady = True

                elif prefs.end_setting == 'repeat':
                    pctl.playlist_playing = -1
                    pctl.advance()

                elif prefs.end_setting == 'cycle':

                    pctl.active_playlist_playing += 1

                    if pctl.active_playlist_playing > len(pctl.multi_playlist) - 1:
                        pctl.active_playlist_playing = 0

                        pctl.playlist_playing = -1
                        pctl.advance()
                    else:
                        self.playing_state = 0
                        self.playerCommand = 'runstop'
                        self.playerCommandReady = True

                gui.update += 3
            else:
                if self.playlist_playing > len(self.playing_playlist()) - 1:
                    self.playlist_playing = 0

                elif len(self.track_queue) > 0 and self.playing_playlist()[self.playlist_playing] != self.track_queue[
                    self.queue_step]:
                    try:
                        self.playlist_playing = self.playing_playlist().index(self.track_queue[self.queue_step])
                    except:
                        pass

                if len(self.playing_playlist()) == self.playlist_playing + 1:
                    return

                self.playlist_playing += 1
                self.track_queue.append(self.playing_playlist()[self.playlist_playing])
                self.queue_step = len(self.track_queue) - 1
                self.play_target(gapless=gapless)

        else:
            print("ADVANCE ERROR - NO CASE!")

        if self.playlist_active == self.active_playlist_playing:
            self.show_current(playing=True, quiet=quiet)

        # if album_mode:
        #     goto_album(self.playlist_playing)



        self.render_playlist()

        self.notify_update()

pctl = PlayerCtl()


def get_object(index):
    return pctl.master_library[index]

def update_title_do():

    if pctl.playing_state > 0:
        if len(pctl.track_queue) > 0:
            line = pctl.master_library[pctl.track_queue[pctl.queue_step]].artist + " - " + \
                   pctl.master_library[pctl.track_queue[pctl.queue_step]].title
            #line += "   : :   Tauon Music Box"
            line = line.encode('utf-8')
            SDL_SetWindowTitle(t_window, line)
    else:
        line = "Tauon Music Box"
        line = line.encode('utf-8')
        SDL_SetWindowTitle(t_window, line)


# Last.FM -----------------------------------------------------------------
class LastFMapi:
    API_SECRET = "18c471e5475e7e877b126843d447e855"
    connected = False
    hold = False
    API_KEY = "0eea8ea966ab2ca395731e2c3c22e81e"

    network = None

    def connect(self, m_notify=True):

        global lfm_password
        global lfm_username
        global lfm_hash

        if not last_fm_enable:
            return False

        if self.connected is True:
            if m_notify:
                show_message("Already connected to Last.fm")
            return True

        if lfm_username == "":
            show_message("No Last.fm account information.", "warning", "See Last.fm tab in settings.")
            return False

        if lfm_hash == "":
            if lfm_password == "":
                show_message("Missing Password.", 'warning', "See Last.fm tab in settings.")
                return False
            else:
                lfm_hash = pylast.md5(lfm_password)

        print('Attempting to connect to Last.fm network')

        try:
            # print(lfm_username)
            # print(lfm_hash)
            # print(lfm_password)

            self.network = pylast.LastFMNetwork(api_key=self.API_KEY, api_secret=
            self.API_SECRET, username=lfm_username, password_hash=lfm_hash)

            self.connected = True
            if m_notify:
                show_message("Connection to Last.fm was successful.", 'done')
            print('Connection to lastfm appears successful')
            return True
        except Exception as e:

            show_message("Error connecting to Last.fm network", "warning", str(e))
            print(e)
            return False

    def toggle(self):
        if self.connected:
            self.hold ^= True
        else:
            self.connect()

    def details_ready(self):
        if len(lfm_username) > 1 and len(lfm_username) > 1 and prefs.auto_lfm:
            return True
        else:
            return False

    def no_user_connect(self):

        try:
            self.network = pylast.LastFMNetwork(api_key=self.API_KEY, api_secret=
            self.API_SECRET)

            print('Connection appears successful')
            return True
        except Exception as e:
            show_message("Error communicating with Last.fm network", "warning", str(e))
            print(e)
            return False


    def artist_info(self, artist):

        if self.network is None:
            if self.no_user_connect() is False:
                return

        print(artist)
        if artist != "":
            l_artist = pylast.Artist(artist, self.network)
            #print(artist.get_bio_summary(language="en"))
            print(l_artist.get_bio_content())
            print(l_artist.get_cover_image())



    def scrobble(self, title, artist, album):
        if self.hold:
            return 0
        if prefs.auto_lfm:
            self.connect(False)

        timestamp = int(time.time())
        # lastfm_user = self.network.get_user(self.username)

        # Act
        try:
            if title != "" and artist != "":
                if album != "":
                    self.network.scrobble(artist=artist, title=title, album=album, timestamp=timestamp)
                else:
                    self.network.scrobble(artist=artist, title=title, timestamp=timestamp)
                print('Scrobbled')
            else:
                print("Not sent, incomplete metadata")
        except Exception as e:

            if 'retry' in str(e):
                print("Retrying...")
                time.sleep(12)

                try:
                    self.network.scrobble(artist=artist, title=title, timestamp=timestamp)
                    print('Scrobbled')
                    return 0
                except:
                    pass

            show_message("Error: Could not scrobble. ", 'warning', str(e))
            print(e)

    def get_bio(self, artist):
        #if self.connected:
        if self.network is None:
            self.no_user_connect()

        artist_object = pylast.Artist(artist, self.network)
        bio = artist_object.get_bio_summary(language="en")
        print(artist_object.get_cover_image())
        print("\n\n")
        print(bio)
        print("\n\n")
        print(artist_object.get_bio_content())
        return bio
        #else:
        #    return ""

    def love(self, artist, title):
        if prefs.auto_lfm:
            self.connect(False)
        if self.connected and artist != "" and title != "":
            track = self.network.get_track(artist, title)
            track.love()

    def unlove(self, artist, title):
        if prefs.auto_lfm:
            self.connect(False)
        if self.connected and artist != "" and title != "":
            track = self.network.get_track(artist, title)
            track.love()
            track.unlove()

    # The last.fm api is broken here

    # def user_love_to_playlist(self, username):
    #     if len(username) > 15:
    #         return
    #     if self.network is None:
    #         self.no_user_connect()
    #
    #     print("Lookup last.fm user " + username)
    #
    #     lastfm_user = self.network.get_user(username)
    #     #loved = lastfm_user.get_loved_tracks()
    #     print(lastfm_user.get_recent_tracks())


    def update(self, title, artist, album):
        if self.hold:
            return 0
        if prefs.auto_lfm:
            if self.connect(False) is False:
                prefs.auto_lfm = False

        # print('Updating Now Playing')
        try:
            if title != "" and artist != "":
                self.network.update_now_playing(
                    artist=artist, title=title, album=album)
                return 0
            else:
                print("Not sent, incomplete metadata")
        except Exception as e:

            print(e)
            if 'retry' in str(e):
                return 2
                show_message("Could not update Last.fm. ", 'warning', str(e))
            pctl.b_time -= 5000
            return 1


def get_backend_time(path):
    pctl.time_to_get = path

    pctl.playerCommand = 'time'
    pctl.playerCommandReady = True

    while pctl.playerCommand != 'done':
        time.sleep(0.005)

    return pctl.time_to_get


lastfm = LastFMapi()

def get_love(track_object):

    star = star_store.full_get(track_object.index)
    if star is None:
        return False

    if 'L' in star[1]:
        return True
    else:
        return False

def get_love_index(index):

    star = star_store.full_get(index)
    if star is None:
        return False

    if 'L' in star[1]:
        return True
    else:
        return False

def love(set=True):

    if len(pctl.track_queue) < 1:
        return False

    index = pctl.track_queue[pctl.queue_step]

    loved = False
    star = star_store.full_get(index)
    if star is not None:
        if 'L' in star[1]:
            loved = True

    if set is False:
        return loved

    loved ^= True

    if loved:
        star = [star[0], star[1] + "L"]
        lastfm.love(pctl.master_library[index].artist, pctl.master_library[index].title)
    else:
        star = [star[0], star[1].strip("L")]
        lastfm.unlove(pctl.master_library[index].artist, pctl.master_library[index].title)


    star_store.insert(index, star)
    gui.pl_update = 1


class LastScrob:

    def __init__(self):

        self.a_index = -1
        self.a_sc = False
        self.a_pt = False

    def update(self, add_time):

        if self.a_index != pctl.track_queue[pctl.queue_step]:
            pctl.a_time = 0
            pctl.b_time = 0
            self.a_index = pctl.track_queue[pctl.queue_step]
            self.a_pt = False
            self.a_sc = False
        if pctl.playing_time == 0 and self.a_sc is True:
            print("Reset scrobble timer")
            pctl.a_time = 0
            pctl.b_time = 0
            self.a_pt = False
            self.a_sc = False
        if pctl.a_time > 10 and self.a_pt is False and pctl.master_library[self.a_index].length > 30:
            self.a_pt = True

            if lastfm.connected or lastfm.details_ready():
                mini_t = threading.Thread(target=lastfm.update, args=(pctl.master_library[self.a_index].title,
                                                                      pctl.master_library[self.a_index].artist,
                                                                      pctl.master_library[self.a_index].album))
                mini_t.daemon = True
                mini_t.start()

        if pctl.a_time > 10 and self.a_pt:
            pctl.b_time += add_time
            if pctl.b_time > 20:
                pctl.b_time = 0
                if lastfm.connected or lastfm.details_ready():
                    mini_t = threading.Thread(target=lastfm.update, args=(pctl.master_library[self.a_index].title,
                                                                          pctl.master_library[self.a_index].artist,
                                                                          pctl.master_library[self.a_index].album))
                    mini_t.daemon = True
                    mini_t.start()

        if pctl.master_library[self.a_index].length > 30 and pctl.a_time > pctl.master_library[self.a_index].length \
                * 0.50 and self.a_sc is False:
            self.a_sc = True
            if lastfm.connected or lastfm.details_ready():
                gui.pl_update = 1
                print(
                    "Scrobble " + pctl.master_library[self.a_index].title + " - " + pctl.master_library[
                        self.a_index].artist)

                mini_t = threading.Thread(target=lastfm.scrobble, args=(pctl.master_library[self.a_index].title,
                                                                        pctl.master_library[self.a_index].artist,
                                                                        pctl.master_library[self.a_index].album))
                mini_t.daemon = True
                mini_t.start()

        if self.a_sc is False and pctl.master_library[self.a_index].length > 30 and pctl.a_time > 240:
            if lastfm.connected or lastfm.details_ready():
                gui.pl_update = 1
                print(
                    "Scrobble " + pctl.master_library[self.a_index].title + " - " + pctl.master_library[
                        self.a_index].artist)

                mini_t = threading.Thread(target=lastfm.scrobble, args=(pctl.master_library[self.a_index].title,
                                                                        pctl.master_library[self.a_index].artist,
                                                                        pctl.master_library[self.a_index].album))
                mini_t.daemon = True
                mini_t.start()
            self.a_sc = True

lfm_scrobbler = LastScrob()


def player3():  # Gstreamer

    player_timer = Timer()

    class GPlayer:

        def __init__(self):

            Gst.init([])
            self.mainloop = GObject.MainLoop()

            self.play_state = 0
            self.pl = Gst.ElementFactory.make("playbin", "player")

            GObject.timeout_add(500, self.test11)

            self.mainloop.run()

        def check_duration(self):

            # If the duration of track is unknown, query gst for it
            if pctl.master_library[pctl.track_queue[pctl.queue_step]].length < 1:

                result = self.pl.query_duration(Gst.Format.TIME)
                print(result)
                if result[0] is True:
                    print("Updating track duration")
                    pctl.master_library[pctl.track_queue[pctl.queue_step]].length = result[1] / Gst.SECOND
                else:
                    time.sleep(1.5)
                    result = self.pl.query_duration(Gst.Format.TIME)
                    print(result)
                    if result[0] is True:
                        print("Updating track duration")
                        pctl.master_library[pctl.track_queue[pctl.queue_step]].length = result[1] / Gst.SECOND

        # def about_to_finish(self, player):
        #
        #     print("End of track callback triggered")
        #     self.play_state = 0
        #     if pctl.playerCommand == 'gapless':
        #         player.set_property('uri', 'file://' + os.path.abspath(pctl.target_open))
        #         pctl.playing_time = 0
        #
        #         time.sleep(0.05)
        #         if pctl.start_time > 1:
        #             self.pl.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
        #                                 pctl.start_time * Gst.SECOND)
        #
        #         time.sleep(0.15)
        #         self.check_duration()

        def test11(self):

            pctl.test_progress()

            if pctl.playerCommandReady:
                if pctl.playerCommand == 'open' and pctl.target_open != '':

                    # Stop if playing or paused
                    if self.play_state == 1 or self.play_state == 2:
                        self.pl.set_state(Gst.State.NULL)

                    self.play_state = 1

                    self.pl.set_property('uri', 'file://' + os.path.abspath(pctl.target_open))

                    self.pl.set_property('volume', pctl.player_volume / 100)

                    self.pl.set_state(Gst.State.PLAYING)

                    time.sleep(0.1)

                    self.pl.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                        pctl.start_time * Gst.SECOND)

                    time.sleep(0.15)
                    self.check_duration()

                    # self.pl.connect("about-to-finish", self.about_to_finish)

                    player_timer.hit()

                    # elif pctl.playerCommand == 'url':
                    #
                    #    # Stop if playing or paused
                    #    if self.play_state == 1 or self.play_state == 2:
                    #        self.pl.set_state(Gst.State.NULL)
                    #
                    #
                    #        self.pl.set_property('uri', pctl.url)
                    #        self.pl.set_property('volume', pctl.player_volume / 100)
                    #        self.pl.set_state(Gst.State.PLAYING)
                    #        self.play_state = 3
                    #        player_timer.hit()

                elif pctl.playerCommand == 'volume':
                    if self.play_state == 1:
                        self.pl.set_property('volume', pctl.player_volume / 100)

                elif pctl.playerCommand == 'stop':
                    if self.play_state > 0:
                        self.pl.set_state(Gst.State.NULL)
                    self.play_state = 0

                elif pctl.playerCommand == 'seek':
                    if self.play_state > 0:
                        self.pl.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                            (pctl.new_time + pctl.start_time) * Gst.SECOND)
                elif pctl.playerCommand == 'pause':
                    player_timer.hit()
                    if self.play_state == 1:
                        self.play_state = 2
                        self.pl.set_state(Gst.State.PAUSED)
                    elif self.play_state == 2:
                        self.pl.set_state(Gst.State.PLAYING)
                        self.play_state = 1

                pctl.playerCommandReady = False

            if self.play_state == 1:
                # Progress main seek head
                add_time = player_timer.hit()
                pctl.playing_time += add_time

                lfm_scrobbler.update(add_time)

                # Update track play count
                if len(pctl.track_queue) > 0 and 3 > add_time > 0:

                    star_store.add(pctl.track_queue[pctl.queue_step], add_time)

            # if self.play_state == 3:   #  URL Mode
            #    # Progress main seek head
            #    add_time = player_timer.hit()
            #    pctl.playing_time += add_time

            if not running:
                print("quit")
                if self.play_state > 0:
                    self.pl.set_state(Gst.State.NULL)
                    time.sleep(0.5)

                self.mainloop.quit()
                pctl.playerCommand = 'done'

            else:
                GObject.timeout_add(25, self.test11)

    GPlayer()

    pctl.playerCommand = 'done'


def player():   # BASS

    player_timer = Timer()
    broadcast_timer = Timer()
    current_volume = pctl.player_volume / 100
    has_bass_ogg = True

    if system == 'windows':
        bass_module = ctypes.WinDLL('bass')
        enc_module = ctypes.WinDLL('bassenc')
        mix_module = ctypes.WinDLL('bassmix')
        fx_module = ctypes.WinDLL('bass_fx')
        # opus_module = ctypes.WinDLL('bassenc_opus')
        try:
            ogg_module = ctypes.WinDLL('bassenc_ogg')
        except:
            has_bass_ogg = False
        function_type = ctypes.WINFUNCTYPE
    elif system == 'mac':
        bass_module = ctypes.CDLL(install_directory + '/lib/libbass.dylib', mode=ctypes.RTLD_GLOBAL)
        enc_module = ctypes.CDLL(install_directory + '/lib/libbassenc.dylib', mode=ctypes.RTLD_GLOBAL)
        mix_module = ctypes.CDLL(install_directory + '/lib/libbassmix.dylib', mode=ctypes.RTLD_GLOBAL)
        ogg_module = ctypes.CDLL(install_directory + '/lib/libbassenc_ogg.dylib', mode=ctypes.RTLD_GLOBAL)
        function_type = ctypes.CFUNCTYPE
    else:
        bass_module = ctypes.CDLL(install_directory + '/lib/libbass.so', mode=ctypes.RTLD_GLOBAL)
        enc_module = ctypes.CDLL(install_directory + '/lib/libbassenc.so', mode=ctypes.RTLD_GLOBAL)
        mix_module = ctypes.CDLL(install_directory + '/lib/libbassmix.so', mode=ctypes.RTLD_GLOBAL)
        fx_module = ctypes.CDLL(install_directory + '/lib/libbass_fx.so', mode=ctypes.RTLD_GLOBAL)

        try:
            ogg_module = ctypes.CDLL(install_directory + '/lib/libbassenc_ogg.so', mode=ctypes.RTLD_GLOBAL)
        except:
            has_bass_ogg = False
        function_type = ctypes.CFUNCTYPE

    BASS_Init = function_type(ctypes.c_bool, ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
                              ctypes.c_void_p)(('BASS_Init', bass_module))

    BASS_FX_GetVersion = function_type(ctypes.c_ulong)(("BASS_FX_GetVersion", fx_module))

    BASS_StreamCreateFile = function_type(ctypes.c_ulong, ctypes.c_bool, ctypes.c_void_p, ctypes.c_int64,
                                          ctypes.c_int64, ctypes.c_ulong)(('BASS_StreamCreateFile', bass_module))
    BASS_Pause = function_type(ctypes.c_bool)(('BASS_Pause', bass_module))
    BASS_Stop = function_type(ctypes.c_bool)(('BASS_Stop', bass_module))
    BASS_Start = function_type(ctypes.c_bool)(('BASS_Start', bass_module))
    BASS_Free = function_type(ctypes.c_int)(('BASS_Free', bass_module))
    BASS_ChannelPause = function_type(ctypes.c_bool, ctypes.c_ulong)(('BASS_ChannelPause', bass_module))
    BASS_ChannelStop = function_type(ctypes.c_bool, ctypes.c_ulong)(('BASS_ChannelStop', bass_module))
    BASS_ChannelPlay = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_bool)(
        ('BASS_ChannelPlay', bass_module))
    BASS_ErrorGetCode = function_type(ctypes.c_int)(('BASS_ErrorGetCode', bass_module))
    BASS_SetConfig = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong)(('BASS_SetConfig', bass_module))
    BASS_GetConfig = function_type(ctypes.c_ulong, ctypes.c_ulong)(('BASS_GetConfig', bass_module))
    BASS_ChannelSlideAttribute = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_float,
                                               ctypes.c_ulong)(('BASS_ChannelSlideAttribute', bass_module))
    BASS_ChannelSetAttribute = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_float)(
        ('BASS_ChannelSetAttribute', bass_module))
    BASS_PluginLoad = function_type(ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong)(
        ('BASS_PluginLoad', bass_module))
    BASS_PluginFree = function_type(ctypes.c_bool, ctypes.c_ulong)(('BASS_PluginFree', bass_module))
    BASS_ChannelIsSliding = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_ChannelIsSliding', bass_module))
    BASS_ChannelSeconds2Bytes = function_type(ctypes.c_int64, ctypes.c_ulong, ctypes.c_double)(
        ('BASS_ChannelSeconds2Bytes', bass_module))
    BASS_ChannelSetPosition = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_int64, ctypes.c_ulong)(
        ('BASS_ChannelSetPosition', bass_module))
    BASS_StreamFree = function_type(ctypes.c_bool, ctypes.c_ulong)(('BASS_StreamFree', bass_module))
    BASS_ChannelGetLength = function_type(ctypes.c_int64, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_ChannelGetLength', bass_module))
    BASS_ChannelBytes2Seconds = function_type(ctypes.c_double, ctypes.c_ulong, ctypes.c_int64)(
        ('BASS_ChannelBytes2Seconds', bass_module))
    BASS_ChannelGetLevel = function_type(ctypes.c_ulong, ctypes.c_ulong)(('BASS_ChannelGetLevel', bass_module))
    BASS_ChannelGetData = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong)(
        ('BASS_ChannelGetData', bass_module))


    class BASS_BFX_VOLUME(ctypes.Structure):
        _fields_ = [('lChannel', ctypes.c_int),
                    ('fVolume', ctypes.c_float)
                    ]


    #BASS_FXSetParameters = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.POINTER(BASS_BFX_VOLUME))(
    BASS_FXSetParameters = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_void_p)(
        ('BASS_FXSetParameters', bass_module))

    BASS_ChannelSetFX = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_int)(
        ('BASS_ChannelSetFX', bass_module))

    SyncProc = function_type(None, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p)
    BASS_ChannelSetSync = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_int64, SyncProc,
                                        ctypes.c_void_p)(
        ('BASS_ChannelSetSync', bass_module))
    BASS_ChannelIsActive = function_type(ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_ChannelIsActive', bass_module))

    BASS_Mixer_StreamCreate = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_Mixer_StreamCreate', mix_module))
    BASS_Mixer_StreamAddChannel = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_Mixer_StreamAddChannel', mix_module))
    BASS_Mixer_ChannelRemove = function_type(ctypes.c_bool, ctypes.c_ulong)(
        ('BASS_Mixer_ChannelRemove', mix_module))
    BASS_Mixer_ChannelSetPosition = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_int64, ctypes.c_ulong)(
        ('BASS_Mixer_ChannelSetPosition', mix_module))
    BASS_Mixer_ChannelFlags = function_type(ctypes.c_int64, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_Mixer_ChannelFlags', mix_module))

    DownloadProc = function_type(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p)

    # BASS_StreamCreateURL = function_type(ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong,
    #        ctypes.c_ulong, DownloadProc, ctypes.c_void_p)(('BASS_StreamCreateURL', bass_module))
    BASS_StreamCreateURL = function_type(ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_ulong,
                                         DownloadProc, ctypes.c_void_p)(('BASS_StreamCreateURL', bass_module))
    BASS_ChannelGetTags = function_type(ctypes.c_char_p, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_ChannelGetTags', bass_module))


    def py_down(buffer, length, user):
        # if url_record:
        #
        #     p = create_string_buffer(length)
        #     ctypes.memmove(p, buffer, length)
        #
        #     f = open(record_path + fileline, 'ab')
        #     f.write(p)
        #     f.close
        return 0

    down_func = DownloadProc(py_down)

    EncodeClientProc = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_bool, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p)

    # def py_cmp_func(handle, channel, buffer, length):
    #     return 0
    #
    # cmp_func = EncodeProc(py_cmp_func)
    BASS_Encode_ServerInit = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, EncodeClientProc,
                           ctypes.c_void_p)(('BASS_Encode_ServerInit', enc_module))


    BASS_Encode_Start = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong,
                                      ctypes.c_bool, ctypes.c_void_p)(('BASS_Encode_Start', enc_module))
    BASS_Encode_CastInit = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_char_p,
                                         ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                                         ctypes.c_char_p, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_bool)(
        ('BASS_Encode_CastInit', enc_module))
    BASS_Encode_Stop = function_type(ctypes.c_bool, ctypes.c_ulong)(('BASS_Encode_Stop', enc_module))
    BASS_Encode_SetChannel = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_Encode_SetChannel', enc_module))
    BASS_Encode_CastSetTitle = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_bool)(
        ('BASS_Encode_CastSetTitle', enc_module))
    #
    # BASS_Encode_OPUS_Start = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p)(
    #     ('BASS_Encode_OPUS_Start', opus_module))
    if has_bass_ogg:
        BASS_Encode_OGG_Start = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong,
                                              ctypes.c_void_p, ctypes.c_void_p)(
            ('BASS_Encode_OGG_Start', ogg_module))
        BASS_Encode_OGG_StartFile = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong,
                                                  ctypes.c_void_p)(
            ('BASS_Encode_OGG_StartFile', ogg_module))

    class BASS_DEVICEINFO(ctypes.Structure):
        _fields_ = [('name', ctypes.c_char_p),
                    ('driver', ctypes.c_char_p),
                    ('flags', ctypes.c_ulong)
                    ]

    BASS_GetDeviceInfo = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.POINTER(BASS_DEVICEINFO))(
        ('BASS_GetDeviceInfo', bass_module))
    BASS_SetDevice = function_type(ctypes.c_bool, ctypes.c_ulong)(('BASS_SetDevice', bass_module))

    BASS_RecordGetDeviceInfo = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.POINTER(BASS_DEVICEINFO))(
        ('BASS_RecordGetDeviceInfo', bass_module))


    BASS_DEVICE_ENABLED = 1
    BASS_DEVICE_DEFAULT = 2
    BASS_DEVICE_INIT = 4

    BASS_DEVICE_ENABLED = 1
    BASS_DEVICE_DEFAULT = 2
    BASS_DEVICE_INIT = 4

    # BASS_DEVICE_TYPE_MASK = 0xff000000
    # BASS_DEVICE_TYPE_NETWORK = 0x01000000
    # BASS_DEVICE_TYPE_SPEAKERS = 0x02000000
    # BASS_DEVICE_TYPE_LINE = 0x03000000
    # BASS_DEVICE_TYPE_HEADPHONES = 0x04000000
    # BASS_DEVICE_TYPE_MICROPHONE = 0x05000000
    # BASS_DEVICE_TYPE_HEADSET = 0x06000000
    # BASS_DEVICE_TYPE_HANDSET = 0x07000000
    # BASS_DEVICE_TYPE_DIGITAL = 0x08000000
    # BASS_DEVICE_TYPE_SPDIF = 0x09000000
    # BASS_DEVICE_TYPE_HDMI = 0x0a000000
    # BASS_DEVICE_TYPE_DISPLAYPORT = 0x40000000


    BASS_MIXER_END = 0x10000
    BASS_SYNC_END = 2
    BASS_SYNC_MIXTIME = 0x40000000
    BASS_UNICODE = 0x80000000
    BASS_STREAM_DECODE = 0x200000
    BASS_ASYNCFILE = 0x40000000
    BASS_SAMPLE_FLOAT = 256
    BASS_STREAM_AUTOFREE = 0x40000
    BASS_MIXER_NORAMPIN = 0x800000
    BASS_MIXER_PAUSE = 0x20000

    BASS_DEVICE_DMIX = 0x2000

    BASS_CONFIG_ASYNCFILE_BUFFER = 45

    if system != 'windows':
        open_flag = 0
        BASS_SetConfig(BASS_CONFIG_ASYNCFILE_BUFFER, 128000)
    else:
        open_flag = BASS_UNICODE
    open_flag |= BASS_ASYNCFILE
    # open_flag |= BASS_STREAM_DECODE
    open_flag |= BASS_SAMPLE_FLOAT
    open_flag |= BASS_STREAM_AUTOFREE

    # gap1
    class BassGapless:
        def __init__(self):
            self.mixer = None
            self.source = None
            self.gap_next = None

    bass_gap = BassGapless()

    #global source

    def py_sync(handle, channel, data, user):

        print("SYNC")
        if bass_gap.gap_next is not None:

            bass_gap.source = BASS_StreamCreateFile(False, bass_gap.gap_next, 0, 0, open_flag | BASS_STREAM_DECODE)
            BASS_Mixer_StreamAddChannel(bass_gap.mixer, bass_gap.source, BASS_STREAM_AUTOFREE | BASS_MIXER_NORAMPIN)
            BASS_ChannelSetPosition(bass_gap.mixer, 0, 0)
            bass_gap.gap_next = None
        else:
            print("no next!")
        return 0

    EndSync = SyncProc(py_sync)


    if system == 'windows':
        # print(BASS_ErrorGetCode())
        BASS_PluginLoad(b'bassopus.dll', 0)
        BASS_PluginLoad(b'bassflac.dll', 0)
        BASS_PluginLoad(b'bass_ape.dll', 0)
        BASS_PluginLoad(b'bass_tta.dll', 0)
        BASS_PluginLoad(b'basswma.dll', 0)
        BASS_PluginLoad(b'basswv.dll', 0)
        BASS_PluginLoad(b'bassalac.dll', 0)

        # bassenc_opus
    elif system == 'mac':
        b = install_directory.encode('utf-8')
        BASS_PluginLoad(b + b'/lib/libbassopus.dylib', 0)
        BASS_PluginLoad(b + b'/lib/libbassflac.dylib', 0)
        BASS_PluginLoad(b + b'/lib/libbass_ape.dylib', 0)
        BASS_PluginLoad(b + b'/lib/libbass_aac.dylib', 0)
        BASS_PluginLoad(b + b'/lib/libbasswv.dylib', 0)
    else:
        b = install_directory.encode('utf-8')
        BASS_PluginLoad(b + b'/lib/libbassopus.so', 0)
        BASS_PluginLoad(b + b'/lib/libbassflac.so', 0)
        BASS_PluginLoad(b + b'/lib/libbass_ape.so', 0)
        BASS_PluginLoad(b + b'/lib/libbass_aac.so', 0)
        BASS_PluginLoad(b + b'/lib/libbass_tta.so', 0)
        BASS_PluginLoad(b + b'/lib/libbasswv.so', 0)
        BASS_PluginLoad(b + b'/lib/libbassalac.so', 0)


    BassInitSuccess = BASS_Init(-1, 48000, BASS_DEVICE_DMIX, gui.window_id, 0)
    if BassInitSuccess == True:
        print("Bass library initialised")


    a = 1
    if system == "linux":
        a = 2
    d_info = BASS_DEVICEINFO()
    while True:
        if not BASS_GetDeviceInfo(a, d_info):
            break
        name = d_info.name.decode('utf-8', 'ignore')
        flags = d_info.flags
        enabled = BASS_DEVICE_ENABLED & flags
        default = BASS_DEVICE_DEFAULT & flags
        current = BASS_DEVICE_INIT & flags

        # print((name, enabled, default, current))
        if current > 0:
            pctl.set_device = a
        pctl.bass_devices.append((name, enabled, default, current, a))
        # print(d_info.name.decode('utf-8'))
        a += 1

    #BASS_SetConfig(0, 1000)
    if prefs.log_vol:
        BASS_SetConfig(7, True)

    player1_status = p_stopped
    player2_status = p_stopped

    handle1 = None
    handle2 = None

    # last_level = [0, 0]

    x = (ctypes.c_float * 512)()
    ctypes.cast(x, ctypes.POINTER(ctypes.c_float))
    sp_handle = 0

    # print("--------------------")
    #
    # while True:
    #     if not BASS_RecordGetDeviceInfo(a, d_info):
    #         break
    #     name = d_info.name.decode('utf-8')
    #     print(name)
    #
    # print("--------------------")

    def broadcast_connect(handle, connect, client, headers, user):

        if connect is True:
            pctl.broadcast_clients.append(client.decode())
        else:
            pctl.broadcast_clients.remove(client.decode())
        print((connect, client))

        return True

    client_connect = EncodeClientProc(broadcast_connect)

    BASS_FX_GetVersion()

    def replay_gain(stream):
        pctl.active_replaygain = 0
        if prefs.replay_gain > 0 and pctl.target_object.track_gain is not None or pctl.target_object.album_gain is not None:
            gain = None
            if prefs.replay_gain == 1 and pctl.target_object.track_gain is not None:
                gain = pctl.target_object.track_gain
                print("Track ReplayGain")
            elif prefs.replay_gain == 2 and pctl.target_object.album_gain is not None:
                gain = pctl.target_object.album_gain
                print("Album ReplayGain")

            if gain is None and prefs.replay_gain == 2:
                print("Track ReplayGain Fallback")
                gain = pctl.target_object.track_gain
            if gain is None:
                return

            BASS_FX_BFX_VOLUME = 65539

            volfx = BASS_ChannelSetFX(stream, BASS_FX_BFX_VOLUME, 0)
            volparam = BASS_BFX_VOLUME(0, pow(10, gain / 20))

            BASS_FXSetParameters(volfx, ctypes.pointer(volparam))

            print("Using ReplayGain of " + str(gain))
            pctl.active_replaygain = round(gain, 2)


    while True:

        if gui.turbo is False:
            time.sleep(0.04)
        else:
            gui.turbo_next += 1

            if gui.vis == 2 or gui.vis == 3:
                time.sleep(0.018)
            else:
                # time.sleep(0.02)
                time.sleep(0.02)


            if gui.turbo_next < 6 and pctl.playerCommandReady is not True:

                if player1_status != p_playing and player2_status != p_playing:
                    gui.level = 0
                    continue

                # -----------
                if gui.vis == 2:

                    # # TEMPORARY
                    # continue

                    if gui.lowered:
                        continue

                    if player1_status == p_playing:
                        sp_handle = handle1
                    else:
                        sp_handle = handle2

                    BASS_ChannelGetData(sp_handle, x, 0x80000002)

                    # BASS_DATA_FFT256 = 0x80000000# -2147483648# 256 sample FFT
                    # BASS_DATA_FFT512 = 0x80000001# -2147483647# 512 FFT
                    # BASS_DATA_FFT1024 = 0x80000002# -2147483646# 1024 FFT
                    # BASS_DATA_FFT2048 = 0x80000003# -2147483645# 2048 FFT
                    # BASS_DATA_FFT4096 = 0x80000004# -2147483644# 4096 FFT
                    # BASS_DATA_FFT8192 = 0x80000005# -2147483643# 8192 FFT
                    # BASS_DATA_FFT16384 = 0x80000006# 16384 FFT

                    p_spec = []
                    BANDS = 24
                    b0 = 0
                    i = 0

                    while i < BANDS:
                        peak = 0
                        b1 = pow(2, i * 10.0 / (BANDS - 1))
                        if b1 > 511:
                            b1 = 511
                        if b1 <= b0:
                            b1 = b0 + 1
                        while b0 < b1 and b0 < 511:
                            if peak < x[1 + b0]:
                                peak = x[1 + b0]
                            b0 += 1

                        outp = math.sqrt(peak)
                        # print(int(outp*20))
                        p_spec.append(int(outp * 45))
                        i += 1
                    gui.spec = p_spec

                    # print(gui.spec)
                    if pctl.playing_time > 0.5 and pctl.playing_state == 1:
                        gui.update_spec = 1
                    # if pctl.playerCommand in ['open', 'stop']:
                    #     gui.update_spec = 0
                    gui.level_update = True
                    continue

                #------------------------------------
                elif gui.vis == 3:

                    if gui.lowered:
                        continue

                    if pctl.playing_time > 0.0 and (pctl.playing_state == 1 or pctl.playing_state == 3):
                        if player1_status == p_playing:
                            sp_handle = handle1
                        else:
                            sp_handle = handle2

                        BASS_ChannelGetData(sp_handle, x, 0x80000002)

                        #p_spec = []
                        BANDS = gui.spec2_y + 5
                        b0 = 0
                        i = 0

                        while i < BANDS:
                            peak = 0
                            b1 = pow(2, i * 10.0 / (BANDS - 1))
                            if b1 > 511:
                                b1 = 511
                            if b1 <= b0:
                                b1 = b0 + 1
                            while b0 < b1 and b0 < 511:
                                if peak < x[1 + b0]:
                                    peak = x[1 + b0]
                                b0 += 1

                            outp = math.sqrt(peak)
                            #print(outp)
                            if i < len(gui.spec2):
                                gui.spec2[i] += int(outp * 300)
                            else:
                                break
                            i += 1

                        gui.spec2_phase += 1
                        if gui.spec2_phase == 2:
                            gui.spec2_phase = 0
                            gui.spec2_buffers.append(copy.deepcopy(gui.spec2))
                            if len(gui.spec2_buffers) > 2:
                                del gui.spec2_buffers[0]
                                # print("Buffer Discard")

                            gui.spec2 = [0] * gui.spec2_y
                            #gui.update_spec = 1

                            #gui.level_update = True

                        #gui.level_update = True
                        continue


                    #gui.spec = p_spec

                # -----------------------------------

                elif gui.vis == 1:

                    if player1_status == p_playing:
                        gui.level = BASS_ChannelGetLevel(handle1)
                    elif player2_status == p_playing:
                        gui.level = BASS_ChannelGetLevel(handle2)

                    ppp2 = gui.level & 0x0000FFFF
                    ppp1 = (gui.level & 0xFFFF0000) >> 16

                    # print((ppp1, ppp2, " t: " + str(test_timer.hit())))

                    ppp1 = (ppp1 / 32768) * 11.1
                    ppp2 = (ppp2 / 32768) * 11.1

                    gui.time_passed += gui.level_time.hit()
                    if gui.time_passed > 1:
                        gui.time_passed = 0
                    while gui.time_passed > 0.019:
                        gui.level_peak[1] -= 0.35
                        if gui.level_peak[1] < 0:
                            gui.level_peak[1] = 0
                        gui.level_peak[0] -= 0.35
                        if gui.level_peak[0] < 0:
                            gui.level_peak[0] = 0
                        #gui.time_passed -= 0.020
                        gui.time_passed -= 0.020

                    if ppp1 > gui.level_peak[0]:
                        gui.level_peak[0] = ppp1
                    if ppp2 > gui.level_peak[1]:
                        gui.level_peak[1] = ppp2

                    # gui.level_peak[1] += random.randint(-100, 100) * 0.01
                    # gui.level_peak[0] += random.randint(-100, 100) * 0.01
                    #
                    # if int(gui.level_peak[0]) != int(last_level[0]) or int(gui.level_peak[1]) != int(last_level[1]):
                    #     #gui.level_update = True
                    #     pass
                    gui.level_update = True

                    # last_level = copy.deepcopy(gui.level_peak)
                    #print("hit")

                    continue

            else:
                gui.turbo_next = 0
                if pctl.playerCommand == 'open':
                    # gui.update += 1
                    gui.level_peak = [0, 0]

        if pctl.playing_state == 3 and player1_status == p_playing:
            if radio_meta_timer.get() > 3:
                radio_meta_timer.set()
                # print(BASS_ChannelGetTags(handle1,4 ))

                meta = BASS_ChannelGetTags(handle1, 5)
                if meta is not None:
                    meta = meta.decode('utf-8')
                else:
                    meta = BASS_ChannelGetTags(handle1, 2)
                    if meta is not None:
                        meta = pctl.tag_meta.decode('utf-8', 'ignore')
                    else:
                        meta = ""

                for tag in meta.split(";"):
                    if '=' in tag:
                        a, b = tag.split('=')
                        if a == 'StreamTitle':
                            pctl.tag_meta = b.rstrip("'").lstrip("'")
                            break
                else:
                    pctl.tag_meta = ""

                # print(pctl.tag_meta)

                if BASS_ChannelIsActive(handle1) == 0:
                    pctl.playing_state = 0
                    show_message("Stream stopped.", "info", "The stream either ended or the connection was lost")
                    player1_status = p_stopped
                    pctl.playing_time = 0
                    if pctl.record_stream:
                        pctl.record_stream = False
                        BASS_Encode_Stop(rec_handle)

                if pctl.record_stream and pctl.record_title != pctl.tag_meta:

                    print("Recording track split")
                    BASS_ErrorGetCode()
                    BASS_Encode_Stop(rec_handle)
                    title = '{:%Y-%m-%d %H-%M-%S} - '.format(datetime.datetime.now()) + pctl.tag_meta
                    line = "--quality 3"
                    file = prefs.encoder_output + title + ".ogg"
                    flag = 0
                    if len(pctl.tag_meta) > 6 and ' - ' in pctl.tag_meta:
                        fi = pctl.tag_meta.split(' - ')
                        if len(fi) == 2:
                            line += ' -t "' + fi[0].strip('"') + '"'
                            line += ' -a "' + fi[1].strip('"') + '"'
                    if system != 'windows':
                        file = file.encode('utf-8')
                        line = line.encode('utf-8')
                        flag = 0
                    else:
                        flag = 0x80000000

                    rec_handle = BASS_Encode_OGG_StartFile(handle1, line, flag, file)
                    pctl.record_title = pctl.tag_meta

                    print(file)
                    if BASS_ErrorGetCode() != 0:
                        show_message("Recording error.", "warning", "An unknown error occurred when splitting the track")


        if pctl.broadcast_active and pctl.encoder_pause == 0:
            pctl.broadcast_time += broadcast_timer.hit()
            if broadcast_update_timer.get() > 1:
                broadcast_update_timer.set()
                gui.update += 1


        if player1_status == p_playing or player2_status == p_playing:

            add_time = player_timer.hit()
            if add_time > 3:
                add_time = 0

            pctl.playing_time += add_time

            if pctl.playing_state == 1:

                pctl.a_time += add_time
                pctl.total_playtime += add_time

                lfm_scrobbler.update(add_time)

            # Trigger track advance once end of track is reached
            pctl.test_progress()


            if pctl.playing_state == 1 and len(pctl.track_queue) > 0 and 3 > add_time > 0:
                star_store.add(pctl.track_queue[pctl.queue_step], add_time)
                # index = pctl.track_queue[pctl.queue_step]
                # key = pctl.master_library[index].title + pctl.master_library[index].filename
                # if key in pctl.star_library:
                #     if 3 > add_time > 0:
                #         pctl.star_library[key] += add_time
                # else:
                #     pctl.star_library[key] = 0

        elif pctl.playerCommandReady is False and pctl.playing_state == 1:
            print("Missed play command, re-starting track")
            pctl.stop()
            pctl.play()


        if pctl.playerCommandReady:
            pctl.playerCommandReady = False

            if pctl.playerCommand == 'time':

                pctl.target_open = pctl.time_to_get
                if system != 'windows':
                    pctl.target_open = pctl.target_open.encode('utf-8')
                    flag = 0
                else:
                    flag = 0x80000000

                print(pctl.target_open)
                handle9 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)
                blen = BASS_ChannelGetLength(handle9, 0)
                tlen = BASS_ChannelBytes2Seconds(handle9, blen)
                pctl.time_to_get = tlen
                BASS_StreamFree(handle9)
                pctl.playerCommand = 'done'

            elif pctl.playerCommand == "setdev":

                print("Changeing output device")
                print(BASS_Init(pctl.set_device, 48000, BASS_DEVICE_DMIX, gui.window_id, 0))
                print(BASS_SetDevice(pctl.set_device))

            # if pctl.playerCommand == "monitor":
            #     pass

            if pctl.playerCommand == "url":
                if player1_status != p_stopped:
                    BASS_ChannelStop(handle1)
                    player1_status = p_stopped
                    BASS_StreamFree(handle1)
                if player2_status != p_stopped:
                    BASS_ChannelStop(handle2)
                    player2_status = p_stopped
                    BASS_StreamFree(handle2)

                # fileline = str(datetime.datetime.now()) + ".ogg"
                # print(BASS_ErrorGetCode())
                # print(pctl.url)
                bass_error = BASS_ErrorGetCode()
                handle1 = BASS_StreamCreateURL(pctl.url, 0, 0, down_func, 0)
                bass_error = BASS_ErrorGetCode()
                if bass_error == 40:
                    show_message("Stream error.", "warning", "Connection timeout")
                elif bass_error == 32:
                    show_message("Stream error.", "warning", "No internet connection")
                elif bass_error == 20:
                    show_message("Stream error.", "warning", "Bad URL")
                elif bass_error == 2:
                    show_message("Stream error.", "warning", "Could not open stream")
                elif bass_error == 41:
                    show_message("Stream error.", "warning", "Unknown file format")
                elif bass_error == 44:
                    show_message("Stream error.", "warning", "Unknown/unsupported codec")
                elif bass_error == -1:
                    show_message("Stream error.", "warning", "Its a mystery!!")
                elif bass_error != 0:
                    show_message("Stream error.", "warning", "Something went wrong... somewhere")
                if bass_error == 0:
                    BASS_ChannelSetAttribute(handle1, 2, current_volume)
                    BASS_ChannelPlay(handle1, True)
                    player1_status = p_playing
                    pctl.playing_time = 0
                    pctl.last_playing_time = 0
                    player_timer.hit()
                else:
                    pctl.playing_status = 0

            if pctl.playerCommand == 'record':
                if pctl.playing_state != 3:
                    print("ERROR! Stream not active")
                else:
                    title = '{:%Y-%m-%d %H-%M-%S} - '.format(datetime.datetime.now()) + pctl.tag_meta
                    line = "--quality 3"
                    file = prefs.encoder_output + title + ".ogg"
                    # if system == 'windows':
                    #     file = file.replace("/", '\\')
                    flag = 0
                    if len(pctl.tag_meta) > 6 and ' - ' in pctl.tag_meta:
                        fi = pctl.tag_meta.split(' - ')
                        if len(fi) == 2:
                            line += ' -t "' + fi[0].strip('"') + '"'
                            line += ' -a "' + fi[1].strip('"') + '"'

                    if system != 'windows':
                        file = file.encode('utf-8')
                        line = line.encode('utf-8')
                        flag = 0
                    else:
                        flag = 0x80000000

                        #print(line)

                    print(file)
                    #print(BASS_ErrorGetCode())

                    rec_handle = BASS_Encode_OGG_StartFile(handle1, line, flag, file)
                    #file.encode('utf-8')

                    #print(rec_handle)
                    #print(BASS_ErrorGetCode())
                    #print(BASS_ErrorGetCode())
                    pctl.record_stream = True
                    pctl.record_title = pctl.tag_meta

                    if rec_handle != 0 and BASS_ErrorGetCode() == 0:
                        show_message("Recording started.", "done", "Outputting as ogg to encoder directory, press F9 to show.")
                    else:
                        show_message("Recording Error.", "warning", "An unknown was encountered")
                        pctl.record_stream = False


            if pctl.playerCommand == 'cast-next':
                print("Next Enc Rec")

                if system != 'windows':
                    pctl.target_open = pctl.target_open.encode('utf-8')
                    flag = 0
                else:
                    flag = 0x80000000

                flag |= 0x200000

                BASS_Mixer_ChannelRemove(handle3)
                BASS_StreamFree(handle3)

                handle3 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)

                if pctl.b_start_time > 0:
                    bytes_position = BASS_ChannelSeconds2Bytes(handle3, pctl.b_start_time)
                    BASS_ChannelSetPosition(handle3, bytes_position, 0)

                BASS_Mixer_StreamAddChannel(mhandle, handle3, 0)

                # channel1 = BASS_ChannelPlay(handle3, True)
                channel1 = BASS_ChannelPlay(mhandle, True)

                broadcast_timer.hit()

                encerror = BASS_ErrorGetCode()
                print(encerror)
                print(pctl.broadcast_line)
                line = pctl.broadcast_line.encode('utf-8')
                BASS_Encode_CastSetTitle(encoder, line, 0)
                print(BASS_ErrorGetCode())
                if encerror != 0:
                    pctl.broadcast_active = False
                    BASS_Encode_Stop(encoder)
                    BASS_ChannelStop(handle3)
                    BASS_StreamFree(handle3)
                    # BASS_StreamFree(oldhandle)

            if pctl.playerCommand == 'encseek' and pctl.broadcast_active:

                print("seek")
                bytes_position = BASS_ChannelSeconds2Bytes(handle3, pctl.b_start_time + pctl.broadcast_time)
                BASS_ChannelSetPosition(handle3, bytes_position, 0)

                #BASS_ChannelPlay(handle1, False)

            if pctl.playerCommand == 'encpause' and pctl.broadcast_active:

                # Pause broadcast
                if pctl.encoder_pause == 0:
                    BASS_ChannelPause(mhandle)
                    pctl.encoder_pause = 1
                else:
                    BASS_ChannelPlay(mhandle, True)
                    pctl.encoder_pause = 0
                    # if pctl.encoder_pause == 0:
                    #     #BASS_ChannelPause(mhandle)
                    #     BASS_Mixer_ChannelFlags(mhandle, BASS_MIXER_PAUSE, BASS_MIXER_PAUSE)
                    #     pctl.encoder_pause = 1
                    # else:
                    #     #BASS_ChannelPlay(mhandle, True)
                    #     BASS_Mixer_ChannelFlags(mhandle, 0, BASS_MIXER_PAUSE)
                    #     pctl.encoder_pause = 0

            if pctl.playerCommand == "encstop":
                BASS_Encode_Stop(encoder)
                BASS_ChannelStop(handle3)
                BASS_StreamFree(handle3)
                pctl.broadcast_active = False


            if pctl.playerCommand == "encstart":

                port = "8000"
                bitrate = "128"

                path = config_directory + "/config.txt"
                with open(path, encoding="utf_8") as f:
                    content = f.read().splitlines()
                    for p in content:
                        if len(p) == 0:
                            continue
                        if p[0] == " " or p[0] == "#":
                            continue
                        if 'broadcast-port=' in p:
                            if len(p) < 40:
                                port = p.split('=')[1]
                        elif 'broadcast-bitrate=' in p:
                            bitrate = p.split('=')[1]



                pctl.broadcast_active = True
                print("starting encoder")

                if system != 'windows':
                    pctl.target_open = pctl.target_open.encode('utf-8')
                    flag = 0
                else:
                    flag = 0x80000000

                pctl.broadcast_time = 0

                broadcast_timer.hit()
                flag |= 0x200000
                # print(flag)

                print(pctl.target_open)

                handle3 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)

                mhandle = BASS_Mixer_StreamCreate(44100, 2, 0)

                BASS_Mixer_StreamAddChannel(mhandle, handle3, 0)

                channel1 = BASS_ChannelPlay(mhandle, True)

                BASS_ChannelSetAttribute(mhandle, 2, 0)

                print(BASS_ErrorGetCode())

                # encoder = BASS_Encode_Start(handle3, <lame.exe> --alt-preset standard - c:\output.mp3', 0, cmp_func, 0)
                # encoder = BASS_Encode_Start(handle3, <directory of encoder> -r -s 44100 -b 128 -", 1, 0, 0)

                # if codec == "MP3":
                #     if system == 'windows':
                #         line = user_directory + "/encoder/lame.exe" + " -r -s 44100 -b " + bitrate + " -"
                #     else:
                #         line = "lame" + " -r -s 44100 -b " + bitrate + " -"
                #
                #     line = line.encode('utf-8')
                #
                #     encoder = BASS_Encode_Start(mhandle, line, 1, 0, 0)
                #
                #     line = "source:" + ice_pass
                #     line = line.encode('utf-8')
                #
                #     result = BASS_Encode_CastInit(encoder, mount.encode('utf-8'), line, b"audio/mpeg", b"name", b"url",
                #                          b"genre", b"", b"", int(bitrate), False)

                if not has_bass_ogg:
                    show_message("Error: Missing bass_enc_ogg module, you may be using an outdated install")
                    pctl.broadcast_active = False
                    BASS_ChannelStop(handle3)
                    BASS_StreamFree(handle3)
                    pctl.playerCommand = ""
                    continue

                line = "--bitrate " + bitrate
                line = line.encode('utf-8')

                print(BASS_ErrorGetCode())

                encoder = BASS_Encode_OGG_Start(mhandle, line, 0, None, None)


                result = BASS_Encode_ServerInit(encoder, port.encode(), 32000, 32000, 2, client_connect, None)

                #result = BASS_Encode_CastInit(encoder, mount.encode('utf-8'), line, b"application/ogg", b"name", b"url", b"genre", b"", b"", int(bitrate), False)
                #b"application/ogg", b"name", b"url", b"genre", b"", b""

                if BASS_ErrorGetCode() == -1:
                    show_message("Server initialisation error.", "warning", "Sorry, something isn't working right.")
                channel1 = BASS_ChannelPlay(mhandle, True)
                print(encoder)
                print(pctl.broadcast_line)
                print("after set title")
                print(BASS_ErrorGetCode())
                line = pctl.broadcast_line.encode('utf-8')
                BASS_Encode_CastSetTitle(encoder, line, 0)
                # Trying to send the stream title here causes the stream to fail for some reason
                # line2 = pctl.broadcast_line.encode('utf-8')
                # BASS_Encode_CastSetTitle(encoder, line2,0)
                print("after set title")
                e = BASS_ErrorGetCode()
                if result != 0:
                    show_message("Server initiated successfully.", "done", "Listening on port " + port + ".")
                else:
                    show_message("Error staring broadcast.", 'warning', 'Error code ' + str(e) + ".")

                    pctl.playerCommand = "encstop"
                    pctl.playerCommandReady = True

                print(BASS_ErrorGetCode())

            # ----------------------------------------------------------------------------
            # STANDARD PLAYBACK

            # -----------------------------------------------------------------------------
            # -----------------------------------------------------------------------------
            # gap2
            # if pctl.playerCommand == 'open' and pctl.target_open != '':
            #
            #     pctl.playerCommand = ""
            #     if system != 'windows':
            #         target_file = pctl.target_open.encode('utf-8')
            #     else:
            #         target_file = pctl.target_open
            #
            #     if bass_gap.mixer is None:
            #         print(BASS_ErrorGetCode())
            #         print("create mixer")
            #         bass_gap.mixer = BASS_Mixer_StreamCreate(44100, 2, BASS_MIXER_END)
            #
            #         print("set sync")
            #         BASS_ChannelSetSync(bass_gap.mixer, BASS_SYNC_END | BASS_SYNC_MIXTIME, 0, EndSync, 0)
            #         print(BASS_ErrorGetCode())
            #
            #         print("create source")
            #         bass_gap.source = BASS_StreamCreateFile(False, target_file, 0, 0, open_flag | BASS_STREAM_DECODE)
            #         print(BASS_ErrorGetCode())
            #
            #         print("add source to mixer")
            #         BASS_Mixer_StreamAddChannel(bass_gap.mixer, bass_gap.source, BASS_STREAM_AUTOFREE)
            #         print(BASS_ErrorGetCode())
            #         print("play")
            #         BASS_ChannelPlay(bass_gap.mixer, False)
            #         print(BASS_ErrorGetCode())
            #
            #         player1_status = p_playing
            #     else:
            #         print("existing mixer")
            #         bass_gap.gap_next = target_file
            #
            #     player_timer.hit()
            #
            #
            # # SEEK COMMAND
            # elif pctl.playerCommand == 'seek':
            #     print("seek")
            #     print("get position")
            #     bytes_position = BASS_ChannelSeconds2Bytes(bass_gap.source, pctl.new_time + pctl.start_time)
            #     print(BASS_ErrorGetCode())
            #     print('set position')
            #     BASS_ChannelSetPosition(bass_gap.source, bytes_position, 0)
            #     print(BASS_ErrorGetCode())
            #     print("play")
            #     BASS_ChannelPlay(bass_gap.source, False)
            #     print(BASS_ErrorGetCode())
            #     pctl.playerCommand = ''
            #

            # -----------------------------------------------------------------------------

            # OPEN COMMAND
            if pctl.playerCommand == 'open' and pctl.target_open != '':

                pctl.playerCommand = ""
                if system != 'windows':
                    pctl.target_open = pctl.target_open.encode('utf-8')

                if os.path.isfile(pctl.master_library[pctl.track_queue[pctl.queue_step]].fullpath):
                    pctl.master_library[pctl.track_queue[pctl.queue_step]].found = True
                else:
                    pctl.master_library[pctl.track_queue[pctl.queue_step]].found = False
                    gui.pl_update = 1
                    gui.update += 1
                    print("Missing File: " + pctl.master_library[pctl.track_queue[pctl.queue_step]].fullpath)
                    pctl.playerCommandReady = False
                    pctl.playing_state = 0
                    pctl.advance(inplace=True)
                    continue

                if pctl.join_broadcast and pctl.broadcast_active:

                    if system != 'windows':
                        pctl.target_open = pctl.target_open.encode('utf-8')
                        flag = 0
                    else:
                        flag = 0x80000000
                    flag |= 0x200000

                    BASS_Mixer_ChannelRemove(handle3)
                    BASS_StreamFree(handle3)
                    handle3 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)

                    if pctl.b_start_time > 0:
                        bytes_position = BASS_ChannelSeconds2Bytes(handle3, pctl.b_start_time)
                        BASS_ChannelSetPosition(handle3, bytes_position, 0)

                    BASS_Mixer_StreamAddChannel(mhandle, handle3, 0)
                    channel1 = BASS_ChannelPlay(mhandle, True)

                player_timer.hit()
                # print(pctl.target_open)
                # if system != 'windows':
                #     pctl.target_open = pctl.target_open.encode('utf-8')
                #     flag = 0
                # else:
                #     flag = 0x80000000

                # BASS_ASYNCFILE = 0x40000000
                # flag |= 0x40000000

                if player1_status == p_stopped and player2_status == p_stopped:
                    # print(BASS_ErrorGetCode())
                    # print(pctl.target_open)
                    handle1 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, open_flag)
                    # print(BASS_ErrorGetCode())


                    BASS_ChannelSetAttribute(handle1, 2, current_volume)
                    replay_gain(handle1)

                    channel1 = BASS_ChannelPlay(handle1, True)

                    player1_status = p_playing

                elif player1_status != p_stopped and player2_status == p_stopped:
                    player1_status = p_stopping
                    BASS_ChannelSlideAttribute(handle1, 2, 0, prefs.cross_fade_time)


                    handle2 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, open_flag)

                    replay_gain(handle2)
                    channel2 = BASS_ChannelPlay(handle2, True)

                    BASS_ChannelSetAttribute(handle2, 2, 0)
                    BASS_ChannelSlideAttribute(handle2, 2, current_volume, prefs.cross_fade_time)
                    player2_status = p_playing
                elif player2_status != p_stopped and player1_status == p_stopped:
                    player2_status = p_stopping
                    BASS_ChannelSlideAttribute(handle2, 2, 0, prefs.cross_fade_time)


                    handle1 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, open_flag)
                    replay_gain(handle1)
                    BASS_ChannelSetAttribute(handle1, 2, 0)
                    channel1 = BASS_ChannelPlay(handle1, True)

                    BASS_ChannelSlideAttribute(handle1, 2, current_volume, prefs.cross_fade_time)
                    player1_status = p_playing

                else:
                    print('no case')

                if pctl.master_library[pctl.track_queue[pctl.queue_step]].length < 1:

                    if player1_status == p_playing:
                        blen = BASS_ChannelGetLength(handle1, 0)
                        tlen = BASS_ChannelBytes2Seconds(handle1, blen)
                        pctl.master_library[pctl.track_queue[pctl.queue_step]].length = tlen
                        pctl.playing_length = tlen
                    elif player2_status == p_playing:
                        blen = BASS_ChannelGetLength(handle2, 0)
                        tlen = BASS_ChannelBytes2Seconds(handle2, blen)
                        pctl.master_library[pctl.track_queue[pctl.queue_step]].length = tlen
                        pctl.playing_length = tlen
                if pctl.start_time > 0 or pctl.jump_time > 0:
                    if player1_status == p_playing:
                        bytes_position = BASS_ChannelSeconds2Bytes(handle1, pctl.start_time + pctl.jump_time)
                        BASS_ChannelSetPosition(handle1, bytes_position, 0)
                    elif player2_status == p_playing:
                        bytes_position = BASS_ChannelSeconds2Bytes(handle2, pctl.start_time + pctl.jump_time)
                        BASS_ChannelSetPosition(handle2, bytes_position, 0)

                # print(BASS_ErrorGetCode())
                # pctl.playing_time = 0
                pctl.last_playing_time = 0
                pctl.jump_time = 0
                player_timer.hit()

            # PAUSE COMMAND
            elif pctl.playerCommand == 'pause':
                player_timer.hit()

                if pctl.join_broadcast and pctl.broadcast_active:
                    if player1_status == p_playing or player2_status == p_playing:
                        BASS_ChannelPause(mhandle)
                    else:
                        BASS_ChannelPlay(mhandle, True)

                if player1_status == p_playing:
                    player1_status = p_paused
                    BASS_ChannelSlideAttribute(handle1, 2, 0, prefs.pause_fade_time)
                    time.sleep(prefs.pause_fade_time / 1000 / 0.7)
                    channel1 = BASS_ChannelPause(handle1)
                elif player1_status == p_paused:
                    player1_status = p_playing
                    channel1 = BASS_ChannelPlay(handle1, False)
                    BASS_ChannelSlideAttribute(handle1, 2, current_volume, prefs.pause_fade_time)
                if player2_status == p_playing:
                    player2_status = p_paused
                    BASS_ChannelSlideAttribute(handle2, 2, 0, prefs.pause_fade_time)
                    time.sleep(prefs.pause_fade_time / 1000 / 0.7)
                    channel2 = BASS_ChannelPause(handle2)
                elif player2_status == p_paused:
                    player2_status = p_playing
                    channel2 = BASS_ChannelPlay(handle2, False)
                    BASS_ChannelSlideAttribute(handle2, 2, current_volume, prefs.pause_fade_time)



            # CHANGE VOLUME COMMAND
            elif pctl.playerCommand == 'volume':
                current_volume = pctl.player_volume / 100
                if player1_status == p_playing:
                    BASS_ChannelSlideAttribute(handle1, 2, current_volume, prefs.change_volume_fade_time)
                if player2_status == p_playing:
                    BASS_ChannelSlideAttribute(handle2, 2, current_volume, prefs.change_volume_fade_time)
            # STOP COMMAND
            elif pctl.playerCommand == 'runstop':
                player1_status = p_stopped
                player2_status = p_stopped
                time.sleep(1.5)
                if handle1 is not None:
                    BASS_ChannelStop(handle1)
                if handle2 is not None:
                    BASS_ChannelStop(handle2)


            elif pctl.playerCommand == 'stop':
                if player1_status != p_stopped:
                    player1_status = p_stopped
                    BASS_ChannelSlideAttribute(handle1, 2, 0, prefs.pause_fade_time)
                    time.sleep(prefs.pause_fade_time / 1000)
                    channel1 = BASS_ChannelStop(handle1)
                    BASS_StreamFree(handle1)
                if player2_status != p_stopped:
                    player2_status = p_stopped
                    BASS_ChannelSlideAttribute(handle2, 2, 0, prefs.pause_fade_time)
                    time.sleep(prefs.pause_fade_time / 1000)
                    channel2 = BASS_ChannelStop(handle2)
                    BASS_StreamFree(handle2)
                pctl.playerCommand = 'stopped'
            # SEEK COMMAND
            elif pctl.playerCommand == 'seek':

                if player1_status == p_playing or player1_status == p_paused:

                    bytes_position = BASS_ChannelSeconds2Bytes(handle1, pctl.new_time + pctl.start_time)
                    BASS_ChannelSetPosition(handle1, bytes_position, 0)
                    BASS_ChannelPlay(handle1, False)
                elif player2_status == p_playing or player2_status == p_paused:

                    bytes_position = BASS_ChannelSeconds2Bytes(handle2, pctl.new_time + pctl.start_time)
                    BASS_ChannelSetPosition(handle2, bytes_position, 0)
                    BASS_ChannelPlay(handle2, False)

                pctl.playerCommand = ''

                if pctl.join_broadcast and pctl.broadcast_active:
                    print('b seek')
                    BASS_Mixer_ChannelSetPosition(handle3, bytes_position, 0)
                    BASS_ChannelPlay(mhandle, False)

            pctl.new_time = 0
            bytes_position = 0
            if player1_status == p_stopping:
                time.sleep(prefs.cross_fade_time / 1000)
                BASS_StreamFree(handle1)
                player1_status = p_stopped
                # print('player1 stopped')
                channel1 = BASS_ChannelStop(handle1)
            if player2_status == p_stopping:
                time.sleep(prefs.cross_fade_time / 1000)
                BASS_StreamFree(handle2)
                player2_status = p_stopped
                channel2 = BASS_ChannelStop(handle2)

            # UNLOAD PLAYER COMMAND
            elif pctl.playerCommand == 'unload':
                BASS_Free()
                print('BASS Unloaded')
                break

    pctl.playerCommand = 'done'

# if default_player == 'BASS':
#
#     playerThread = threading.Thread(target=player)
#     playerThread.daemon = True
#     playerThread.start()
#
# elif default_player == 'GTK':
#
#     playerThread = threading.Thread(target=player3)
#     playerThread.daemon = True
#     playerThread.start()

# --------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------
mediaKey = ''
mediaKey_pressed = False


def keyboard_hook():
    from collections import namedtuple

    KeyboardEvent = namedtuple('KeyboardEvent', ['event_type', 'key_code',
                                                 'scan_code', 'alt_pressed',
                                                 'time'])

    handlers = []

    def listen():
        # Adapted from http://www.hackerthreads.org/Topic-42395

        event_types = {win32con.WM_KEYDOWN: 'key down',
                       win32con.WM_KEYUP: 'key up',
                       0x104: 'key down',  # WM_SYSKEYDOWN, used for Alt key.
                       0x105: 'key up',  # WM_SYSKEYUP, used for Alt key.
                       }

        def low_level_handler(nCode, wParam, lParam):
            global mediaKey
            global mediaKey_pressed

            event = KeyboardEvent(event_types[wParam], lParam[0], lParam[1],
                                  lParam[2] == 32, lParam[3])

            if event[1] == 179 and event[0] == 'key down':
                mediaKey = 'play'
                mediaKey_pressed = True
            elif event[1] == 178 and event[0] == 'key down':
                mediaKey = 'stop'
                mediaKey_pressed = True
            elif event[1] == 177 and event[0] == 'key down':
                mediaKey = 'back'
                mediaKey_pressed = True
            elif event[1] == 176 and event[0] == 'key down':
                mediaKey = 'forward'
                mediaKey_pressed = True
            if mediaKey_pressed:
                gui.update += 1
            # Be a good neighbor and call the next hook.
            return windll.user32.CallNextHookEx(hook_id, nCode, wParam, lParam)

        # Our low level handler signature.
        CMPFUNC = CFUNCTYPE(c_int, c_int, c_int, POINTER(c_void_p))
        # Convert the Python handler into C pointer.
        pointer = CMPFUNC(low_level_handler)

        # Hook both key up and key down events for common keys (non-system).
        hook_id = windll.user32.SetWindowsHookExA(win32con.WH_KEYBOARD_LL, pointer,
                                                  win32api.GetModuleHandle(None), 0)

        # Register to remove the hook when the interpreter exits. Unfortunately a
        # try/finally block doesn't seem to work here.
        atexit.register(windll.user32.UnhookWindowsHookEx, hook_id)

        while True:
            msg = win32gui.GetMessage(None, 0, 0)
            win32gui.TranslateMessage(byref(msg))
            win32gui.DispatchMessage(byref(msg))
            time.sleep(5)

    listen()


x_hook = False
if system == 'windows':
    if prefs.mkey is True:
        print('Starting hook thread for Windows')
        keyboardHookThread = threading.Thread(target=keyboard_hook)
        keyboardHookThread.daemon = True
        keyboardHookThread.start()

elif system != 'mac':
    # de = os.environ.get('DESKTOP_SESSION')
    # if True or (prefs.mkey and ('gnome' in de or 'budgie-desktop' in de)):
    #     media_key_mode = 1
    # elif prefs.mkey and os.path.isfile(install_directory + "/pyxhook.py"):
    #     media_key_mode = 2


    #if True: # media_key_mode == 1 or prefs.enable_mpris:
    def gnome():


        from gi.repository import GObject
        import dbus
        import dbus.service
        import dbus.mainloop.glib


        def on_mediakey(comes_from, what):

            global mediaKey
            global mediaKey_pressed

            if what == 'Play':
                mediaKey = 'play'
                mediaKey_pressed = True
            elif what == 'Stop':
                mediaKey = 'stop'
                mediaKey_pressed = True
            elif what == 'Next':
                mediaKey = 'forward'
                mediaKey_pressed = True
            elif what == 'Previous':
                mediaKey = 'back'
                mediaKey_pressed = True
            if mediaKey_pressed:
                gui.update = 1

        # set up the glib main loop.
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        if prefs.mkey:
            try:
                bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
                bus_object = bus.get_object('org.gnome.SettingsDaemon.MediaKeys',
                                            '/org/gnome/SettingsDaemon/MediaKeys')

                # this is what gives us the multi media keys.
                dbus_interface = 'org.gnome.SettingsDaemon.MediaKeys'
                bus_object.GrabMediaPlayerKeys("TauonMusicBox", 0,
                                               dbus_interface=dbus_interface)

                # connect_to_signal registers our callback function.
                bus_object.connect_to_signal('MediaPlayerKeyPressed',
                                             on_mediakey)
            except:
                print("Could not connect to gnome media keys")
                global x_hook
                x_hook = True

        # ----------
        if prefs.enable_mpris:
            try:
                bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
                bus_name = dbus.service.BusName('org.mpris.MediaPlayer2.tauon')

                class MPRIS(dbus.service.Object):

                    def update(self):

                        changed = {}

                        if pctl.playing_state == 1:
                            if self.player_properties['PlaybackStatus'] != 'Playing':
                                self.player_properties['PlaybackStatus'] = 'Playing'
                                changed['PlaybackStatus'] = self.player_properties['PlaybackStatus']
                        elif pctl.playing_state == 0:
                            if self.player_properties['PlaybackStatus'] != 'Stopped':
                                self.player_properties['PlaybackStatus'] = 'Stopped'
                                changed['PlaybackStatus'] = self.player_properties['PlaybackStatus']
                        elif pctl.playing_state == 2:
                            if self.player_properties['PlaybackStatus'] != 'Paused':
                                self.player_properties['PlaybackStatus'] = 'Paused'
                                changed['PlaybackStatus'] = self.player_properties['PlaybackStatus']

                        if pctl.player_volume / 100 != self.player_properties['Volume']:
                            self.player_properties['Volume'] = pctl.player_volume / 100
                            changed['Volume'] = self.player_properties['Volume']

                        if pctl.playing_object().index != self.playing_index:
                            track = pctl.playing_object()
                            self.playing_index = track.index

                            d = {
                                'mpris:trackid': "/org/mpris/MediaPlayer2/TrackList/" + str(pctl.playlist_playing),
                                'mpris:length': dbus.Int64(int(pctl.playing_length * 1000000)),
                                'xesam:album': track.album,
                                'xesam:albumArtist': dbus.Array([track.album_artist]),
                                'xesam:artist': dbus.Array([track.artist]),
                                'xesam:title': track.title,


                            }

                            try:
                                i_path = thumb_tracks.path(track)
                                if i_path is not None:
                                    d['mpris:artUrl'] = 'file://' + i_path
                            except:

                                print("Thumbnail error")
                            self.player_properties['Metadata'] = dbus.Dictionary(d, signature='sv')
                            changed['Metadata'] = self.player_properties['Metadata']

                        if len(changed) > 0:
                            self.PropertiesChanged('org.mpris.MediaPlayer2.Player', changed, [])

                    def update_progress(self):
                        self.player_properties['Position'] = dbus.Int64(int(pctl.playing_time * 1000000))

                    def __init__(self, object_path):
                        dbus.service.Object.__init__(self, bus, object_path)

                        self.playing_index = -1

                        self.root_properties = {
                            'CanQuit': True,
                            #'Fullscreen'
                            #'CanSetFullscreen'
                            'CanRaise': True,
                            'HasTrackList': False,
                            'Identity': 'Tauon Music Box',
                            'DesktopEntry': 'tauonmb',
                            #'SupportedUriSchemes': ['file']
                            'SupportedUriSchemes': dbus.Array([dbus.String("file")]),
                            'SupportedMileTypes': dbus.Array([
                                 dbus.String("audio/mpeg"),
                                 dbus.String("audio/flac"),
                                 dbus.String("audio/ogg")
                                 ])
                        }

                        self.player_properties = {

                            'PlaybackStatus': 'Stopped',
                            #'LoopStatus'
                            'Rate': 1,
                            #'Shuffle':
                            'Volume': pctl.player_volume / 100,
                            'Position': 0,
                            'MinimumRate': 1,
                            'MaximumRate': 1,
                            'CanGoNext': True,
                            'CanGoPrevious': True,
                            'CanPlay': True,
                            'CanPause': True,
                            'CanSeek': True,
                            'CanControl': True

                        }

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2')
                    def Raise(self):
                        gui.request_raise = True

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2')
                    def Quit(self):
                        exit_func()

                    @dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
                                    in_signature='ss', out_signature='v')
                    def Get(self, interface_name, property_name):
                        if interface_name == 'org.mpris.MediaPlayer2':
                            #return self.GetAll(interface_name)[property_name]
                            return self.root_properties[property_name]
                        elif interface_name == 'org.mpris.MediaPlayer2.Player':
                            return self.player_properties[property_name]

                    @dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
                                    in_signature='s', out_signature='a{sv}')
                    def GetAll(self, interface_name):
                        #print(interface_name)
                        if interface_name == 'org.mpris.MediaPlayer2':
                            return self.root_properties
                        elif interface_name == 'org.mpris.MediaPlayer2.Player':
                            return self.player_properties
                        else:
                            return {}

                    @dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
                                    in_signature='ssv', out_signature='')
                    def Set(self, interface_name, property_name, value):
                        if interface_name == 'org.mpris.MediaPlayer2.Player':
                            if property_name == "Volume":
                                pctl.player_volume = min(max(int(value * 100), 0), 100)
                                pctl.set_volume()
                        if interface_name == 'org.mpris.MediaPlayer2':
                            pass

                    @dbus.service.signal(dbus_interface=dbus.PROPERTIES_IFACE,
                                    signature='sa{sv}as')
                    def PropertiesChanged(self, interface_name, change, inval):
                        pass


                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def Next(self):
                        pctl.advance()
                        pass

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def Previous(self):
                        pctl.back()
                        pass

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def Pause(self):
                        pctl.pause_only()
                        pass

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def PlayPause(self):
                        pctl.play_pause()

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def Stop(self):
                        pctl.stop()

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def Play(self):
                        pctl.play()

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def Seek(self, offset):
                        pctl.seek_time(pctl.playing_time + (offset / 1000000))

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def SetPosition(self, id, position):
                        pctl.seek_time(position / 1000000)
                        self.update_progress()
                        self.Seeked(pctl.playing_time)


                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def OpenUri(self, uri):
                        pass

                    @dbus.service.signal(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def Seeked(self, position):
                        pass

                    def seek_do(self, seconds):
                        self.Seeked(dbus.Int64(int(seconds * 1000000)))

                pctl.mpris = MPRIS("/org/mpris/MediaPlayer2")
            except:
                print("MPRIS2 CONNECT FAILED")

        mainloop = GObject.MainLoop()
        mainloop.run()

    try:

        gnomeThread = threading.Thread(target=gnome)
        gnomeThread.daemon = True
        gnomeThread.start()

    except:
        print("ERROR: Could not start Dbus thread")
        x_hook = True

    if x_hook is True: #media_key_mode == 2:

        import pyxhook

        def kbevent(event):
            if 170 < event.ScanCode < 175:
                global mediaKey
                global mediaKey_pressed

                if event.ScanCode == 172:
                    mediaKey = 'play'
                    mediaKey_pressed = True
                if event.ScanCode == 174:
                    mediaKey = 'stop'
                    mediaKey_pressed = True
                if event.ScanCode == 173:
                    mediaKey = 'back'
                    mediaKey_pressed = True
                if event.ScanCode == 171:
                    mediaKey = 'forward'
                    mediaKey_pressed = True
                if mediaKey_pressed:
                    gui.update = 1

        hookman = pyxhook.HookManager()
        hookman.KeyDown = kbevent
        hookman.HookKeyboard()
        hookman.start()
        print("Hooked to X server to get media keys")


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

        if master_count != self.last_db or self.last_pl != playlist:
            self.last_db = master_count
            self.last_pl = playlist

            artists = {}

            for index in pctl.multi_playlist[playlist][2]:
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

            for index in pctl.multi_playlist[playlist][2]:
                genre_r = pctl.master_library[index].genre

                pt = int(star_store.get(index))

                gn = []
                if ',' in genre_r:
                    for g in genre_r.split(","):
                        g = g.rstrip(" ").lstrip(" ")
                        if len(g) > 0:
                            gn.append(g)
                elif ';' in genre_r:
                    for g in genre_r.split(";"):
                        g = g.rstrip(" ").lstrip(" ")
                        if len(g) > 0:
                            gn.append(g)
                elif '/' in genre_r:
                    for g in genre_r.split("/"):
                        g = g.rstrip(" ").lstrip(" ")
                        if len(g) > 0:
                            gn.append(g)
                elif ' & ' in genre_r:
                    for g in genre_r.split(" & "):
                        g = g.rstrip(" ").lstrip(" ")
                        if len(g) > 0:
                            gn.append(g)
                else:
                    gn = [genre_r]

                pt = int(pt / len(gn))

                for genre in gn:

                    if genre.lower() in {"", 'other', 'unknown', 'misc'}:
                        genre = "<Genre Unspecified>"
                    if genre.lower() in {'jpop', 'japanese pop'}:
                        genre = 'J-Pop'
                    if genre.lower() in {'jrock', 'japanese rock'}:
                        genre = 'J-Rock'
                    if genre.lower() in {'alternative music', 'alt-rock', 'alternative', 'alternrock', 'alt'}:
                        genre = 'Alternative Rock'
                    if genre.lower() in {'jpunk', 'japanese punk'}:
                        genre = 'J-Punk'
                    if genre.lower() in {'post rock', 'post-rock'}:
                        genre = 'Post-Rock'
                    if genre.lower() in {'video game', 'game', 'game music', 'video game music', 'game ost'}:
                        genre = "Video Game Soundtrack"
                    if genre.lower() in {'general soundtrack', 'ost', 'Soundtracks'}:
                        genre = "Soundtrack"
                    if genre.lower() in ('anime', 'アニメ', 'anime ost'):
                        genre = 'Anime Soundtrack'
                    if genre.lower() in {'同人'}:
                        genre = 'Doujin'
                    if genre.lower() in {'chill, chill out', 'chill-out'}:
                        genre = 'Chillout'

                    genre = genre.title()

                    if len(genre) == 3 and genre[2] == 'm':
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

            # print('\n-----------------------\n')

            g_albums = {}

            for index in pctl.multi_playlist[playlist][2]:
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


stats_gen = GStats()

# -------------------------------------------------------------------------------------------
# initiate SDL2 --------------------------------------------------------------------C-IS-----

SDL_SetHint(SDL_HINT_VIDEO_ALLOW_SCREENSAVER, b'1')

SDL_Init(SDL_INIT_VIDEO)

#TTF_Init()

window_title = t_title
window_title = window_title.encode('utf-8')


cursor_hand = SDL_CreateSystemCursor(SDL_SYSTEM_CURSOR_HAND)
cursor_standard = SDL_CreateSystemCursor(SDL_SYSTEM_CURSOR_ARROW)
cursor_shift = SDL_CreateSystemCursor(SDL_SYSTEM_CURSOR_SIZEWE)
cursor_text = SDL_CreateSystemCursor(SDL_SYSTEM_CURSOR_IBEAM)

flags = SDL_WINDOW_HIDDEN | SDL_WINDOW_RESIZABLE

if gui.maximized:
    flags |= SDL_WINDOW_MAXIMIZED

if draw_border:
    flags = SDL_WINDOW_BORDERLESS | SDL_WINDOW_RESIZABLE

t_window = SDL_CreateWindow(window_title,
                            SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                            window_size[0], window_size[1],
                            flags)

# t_window = SDL_CreateShapedWindow(window_title,
#                              SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
#                              window_size[0], window_size[1],
#                              flags)

# print(SDL_GetError())
# print(SDL_GetError())

if system == 'windows':
    sss = SDL_SysWMinfo()
    SDL_GetWindowWMInfo(t_window, sss)
    gui.window_id = sss.info.win.window


try:
    SDL_SetHint(SDL_HINT_MOUSE_FOCUS_CLICKTHROUGH, b"1")
except:
    print("old version of SDL detected")

SDL_SetWindowMinimumSize(t_window, 450, 175)
# get window surface and set up renderer
#renderer = SDL_CreateRenderer(t_window, 0, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC)
renderer = SDL_CreateRenderer(t_window, 0, SDL_RENDERER_ACCELERATED)

# window_surface = SDL_GetWindowSurface(t_window)

SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND)

display_index = SDL_GetWindowDisplayIndex(t_window)
display_bounds = SDL_Rect(0, 0)
SDL_GetDisplayBounds(display_index, display_bounds)

icon = IMG_Load(b_active_directory + b"/gui/icon.png")

SDL_SetWindowIcon(t_window, icon)

SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY, "best".encode())


gui.ttext = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, window_size[0], window_size[1])


gui.spec2_tex = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, gui.spec2_w, gui.spec2_y)
gui.spec1_tex = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, gui.spec_w, gui.spec_h)
gui.spec_level_tex = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, gui.level_ww, gui.level_hh)


SDL_SetRenderTarget(renderer, None)

gui.main_texture = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, window_size[0], window_size[1])

SDL_SetRenderTarget(renderer, gui.main_texture)
SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
SDL_RenderClear(renderer)

gui.abc = SDL_Rect(0, 0, window_size[0], window_size[1])
gui.pl_update = 2

# SDL_SetRenderTarget(renderer, None)
# SDL_SetRenderDrawColor(renderer, colours.top_panel_background[0], colours.top_panel_background[1],
#                        colours.top_panel_background[2], colours.top_panel_background[3])
# SDL_RenderClear(renderer)
# SDL_RenderPresent(renderer)

# SDL_SetWindowOpacity(t_window, 0.98)

# m_surface = SDL_CreateRGBSurface(0, window_size[0], window_size[1], 32,0,0,0,0);
# #SDL_SetSurfaceBlendMode(m_surface, SDL_BLENDMODE_BLEND)
# #
# mode = SDL_WindowShapeMode()
# mode.mode = ShapeModeColorKey
# #
# mode.parameters.colorKey = SDL_Color(0, 0, 0)


if default_player == 1:

    playerThread = threading.Thread(target=player)
    playerThread.daemon = True
    playerThread.start()

elif default_player == 2:

    playerThread = threading.Thread(target=player3)
    playerThread.daemon = True
    playerThread.start()


if system == 'windows' and taskbar_progress:

    class WinTask:

        def __init__(self, ):
            self.start = time.time()
            self.updated_state = 0
            self.window_id = gui.window_id
            import comtypes.client as cc
            cc.GetModule("TaskbarLib.tlb")
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


    if os.path.isfile("TaskbarLib.tlb"):
        windows_progress = WinTask()
    else:
        taskbar_progress = False
        print("Could not find TaskbarLib.tlb")


# ---------------------------------------------------------------------------------------------
# ABSTRACT SDL DRAWING FUNCTIONS -----------------------------------------------------


def coll_point(l, r):
    # rect point collision detection
    return r[0] <= l[0] <= r[0] + r[2] and r[1] <= l[1] <= r[1] + r[3]


def rect_in(rect):
    return coll_point(mouse_position, rect)


class Drawing:
    def __init__(self):
        self.sdl_rect = SDL_Rect(10, 10, 10, 10)
        self.text_width_p = pointer(c_int(0))
        self.text_calc_cache = {}

    def fast_fill_rect(self, x, y, w, h):
        self.sdl_rect.x = x
        self.sdl_rect.y = y
        self.sdl_rect.w = w
        self.sdl_rect.h = h
        SDL_RenderFillRect(renderer, self.sdl_rect)

    def rect(self, location, wh, colour, fill=False, target=renderer):

        self.sdl_rect.x = location[0]
        self.sdl_rect.y = location[1]
        self.sdl_rect.w = wh[0]
        self.sdl_rect.h = wh[1]

        if fill is True:
            SDL_SetRenderDrawColor(target, colour[0], colour[1], colour[2], colour[3])
            SDL_RenderFillRect(target, self.sdl_rect)
        else:
            SDL_SetRenderDrawColor(target, colour[0], colour[1], colour[2], colour[3])
            SDL_RenderDrawRect(target, self.sdl_rect)

    def rect_r(self, rect, colour, fill=False, target=renderer):
        self.rect((rect[0], rect[1]), (rect[2], rect[3]), colour, fill, target)

    def line(self, x1, y1, x2, y2, colour):

        SDL_SetRenderDrawColor(renderer, colour[0], colour[1], colour[2], colour[3])
        SDL_RenderDrawLine(renderer, x1, y1, x2, y2)

    def text_calc(self, text, font, cache=True, height=False):

        if gui.win_text:
            xy = pretty_text.text_xy(text, font)
            if height:
                return xy[1]
            else:
                return xy[0]

        if gui.cairo_text:
            x, y = cairo_text.wh(text, font)
            if height:
                return y
            else:
                return x

    def button(self, text, x, y, w=None, h=None, font=212, fore_text=None, back_text=None, bg=None, fg=None, press=None):

        if w is None:
            w = self.text_calc(text, font) + 18 * gui.scale
        if h is None:
            h = 22 * gui.scale

        rect = (x, y, w, h)
        fields.add(rect)

        if fore_text is None:
            fore_text = colours.grey(210)
        if back_text is None:
            back_text = colours.grey(190)
        if bg is None:
            bg = alpha_blend([255, 255, 255, 9], colours.sys_background_3)
        if fg is None:
            fg = alpha_blend([255, 255, 255, 20], colours.sys_background_3)

        click = False

        if press is None:
            press = input.mouse_click

        if rect_in(rect):
            draw.rect_r(rect, fg, True)
            draw_text((rect[0] + int(rect[2] / 2), rect[1] + 2 * gui.scale, 2), text, fore_text, font,
                      bg=fg)
            if press:
                click = True
        else:
            draw.rect_r(rect, bg, True)
            draw_text((rect[0] + int(rect[2] / 2), rect[1] + 2 * gui.scale, 2), text, back_text, font,
                      bg=bg)
        return click


draw = Drawing()


#def track_box_entry(x, y, field_title, field_reference)


text_cache = []  # location, text, dst(sdl rect), c(texture)
calc_cache = []
ttc = {}
ttl = []


# m_renderer = SDL_CreateSoftwareRenderer(m_surface)
# draw.rect((0, 0), (window_size[0], window_size[1]), [255,255,255,255], True, m_renderer)
# draw.rect((0, 0), (8, 15), [0,0,0,0], True, m_renderer)
#
# SDL_SetWindowShape(t_window, m_surface, mode)


# m_surface = SDL_CreateRGBSurface(0, 500, 500, 32,0,0,0,0)
#
# s_renderer = SDL_CreateSoftwareRenderer(m_surface)
# print(SDL_GetError())
#
# #SDL_SetRenderTarget(renderer, m_surface)
# draw.rect_r((0,0,100,50), (0,0,0,0), True, target=s_renderer)
# draw.rect_r((0,50,100,50), (255,255,255,50), True, target=s_renderer)
# draw.rect_r((0,150,100,50), (0,0,0,255), True, target=s_renderer)
# draw.rect_r((0,200,100,50), (255,255,255,255), True, target=s_renderer)
# draw.rect_r((0,250,100,50), (255,255,255,0), True, target=s_renderer)
# #SDL_SetRenderTarget(renderer, None)
#
# mode = SDL_WindowShapeMode()
# mode.mode = ShapeModeDefault
# #mode.shape = m_surface
# #mode.parameters.colorKey = SDL_Color(0, 0, 0)
# print(SDL_GetError())
# SDL_SetWindowShape(t_window, m_surface, mode)
#
# print(SDL_GetError())

# Draw text function with enhanced performance via given search reference values
def clear_text_cache():
    global ttc
    global ttl

    for i in range(len(ttl)):
        key = ttl[i]
        so = ttc[key]
        SDL_DestroyTexture(so[1])

    del ttc
    del ttl
    ttc = {}
    ttl = []


if system == "linux":
    class CT:

        def __init__(self):
            self.surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0)
            self.context = cairo.Context(self.surf)
            self.layout = PangoCairo.create_layout(self.context)
            self.pctx = self.layout.get_context()
            fo = cairo.FontOptions()
            fo.set_antialias(cairo.ANTIALIAS_SUBPIXEL)

            PangoCairo.context_set_font_options(self.pctx, fo)

            self.f_dict = {}

            #self.test_layout = PangoCairo.create_layout(self.context)

        def prime_font(self, name, size, user_handle, y_off=0):

            self.f_dict[user_handle] = (name + " " + str(size), y_off)

        def wh(self, text, font):

            self.layout.set_font_description(Pango.FontDescription(self.f_dict[font][0]))

            self.layout.set_text(text, -1)

            return self.layout.get_pixel_size()


        def draw_text_cairo(self, location, text, colour, font, max_x, bg, align=0, max_y=None, wrap=False):

            if len(text) == 0:
                return 0

            key = (max_x, text, font, colour[0], colour[1], colour[2], colour[3], bg[0], bg[1], bg[2])
            global ttc

            x = location[0]
            y = location[1] + gui.universal_y_text_offset

            if key in ttc:
                sd = ttc[key]
                sd[0].x = x
                sd[0].y = y - sd[2]

                if align == 1:
                    sd[0].x = x - sd[0].w

                elif align == 2:
                    sd[0].x = sd[0].x - int(sd[0].w / 2)

                SDL_RenderCopy(renderer, sd[1], None, sd[0])

                return sd[0].w

            w, h = self.wh(text, font)

            if w < 1:
                return 0

            h += 4  # Compensate for characters that drop past the baseline, pango dosent seem to allow for this

            if wrap:
                h = int((w / max_x) * h) + h
                w = max_x + 1
            if max_y != None:
                h = max_y

            #perf_timer.set()

            data = ctypes.c_buffer(b" " * (h * (w * 4)))
            surf = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_RGB24, w, h)

            context = cairo.Context(surf)
            layout = PangoCairo.create_layout(context)
            #pctx = layout.get_context()


            if max_y != None:
                layout.set_ellipsize(Pango.EllipsizeMode.END)
                layout.set_width(max_x * 1000)  # x1000 seems to make it work, idy why
                layout.set_height(max_y * 1000)  # This doesn't seem to work


            # Antialias settings here dont any effect, fontconfg settings override it

            #fo = cairo.FontOptions()
            #fo.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
            #fo.set_antialias(cairo.ANTIALIAS_GRAY)
            #fo.set_subpixel_order(cairo.SUBPIXEL_ORDER_RGB)
            #PangoCairo.context_set_font_options(pctx, fo)

            context.rectangle(0, 0, w, h)
            context.set_source_rgb(bg[0] / 255, bg[1] / 255, bg[2] / 255)
            context.fill()
            context.set_source_rgb(colour[0] / 255, colour[1] / 255, colour[2] / 255)
            #context.translate(0,0)

            if font not in self.f_dict:
                print("Font not loaded: " + str(font))
                return 10

            layout.set_font_description(Pango.FontDescription(self.f_dict[font][0]))
            layout.set_text(text, -1)

            y_off = layout.get_baseline() / 1000
            # if b_off < 16:
            # print((y_off, text))
            # print(round(y_off - 16))
            y_off = round(y_off - 16)



            if y_off > 0:
                #y_off = 1
                pass
            else:
                y_off = 0

            y_off -= self.f_dict[font][1]

            #y_off = 0
            y -= y_off


            # te = layout.get_pixel_size()
            # if te.height > 30:
            #     print(te.height)



            #print(layout.get_extents())
            # print(text)
            # print(layout.get_pixel_extents()[1].y)

            PangoCairo.show_layout(context, layout)

            surface = SDL_CreateRGBSurfaceWithFormatFrom(ctypes.pointer(data), w, h, 32, w*4, SDL_PIXELFORMAT_RGB888)

            # Here the background colour is keyed out allowing lines to overlap slightly
            ke = SDL_MapRGB(surface.contents.format, bg[0], bg[1], bg[2])
            SDL_SetColorKey(surface, True, ke)

            c = SDL_CreateTextureFromSurface(renderer, surface)
            SDL_FreeSurface(surface)

            dst = SDL_Rect(x, y)
            dst.w = w
            dst.h = h

            if align == 1:
                dst.x = location[0] - dst.w

            elif align == 2:
                dst.x = dst.x - int(dst.w / 2)

            SDL_RenderCopy(renderer, c, None, dst)

            ttc[key] = [dst, c, y_off]
            ttl.append(key)
            if len(ttl) > 350:
                key = ttl[0]
                so = ttc[key]
                SDL_DestroyTexture(so[1])
                del ttc[key]
                del ttl[0]
            return dst.w

    cairo_text = CT()

    if gui.scale == 1:

        standard_font = prefs.linux_font #"Noto Sans"
        cairo_text.prime_font(standard_font, 10 - 2, 10)
        cairo_text.prime_font(standard_font, 11 - 2.5, 11)
        cairo_text.prime_font(standard_font, 12 - 3, 12)
        cairo_text.prime_font(standard_font, 13 - 3, 13)
        cairo_text.prime_font(standard_font, 14 - 4, 14)
        cairo_text.prime_font(standard_font, 15 - 4, 15)
        cairo_text.prime_font(standard_font, 16 - 4, 16)
        cairo_text.prime_font(standard_font, 17 - 5, 17)
        cairo_text.prime_font(standard_font, 18 - 6, 18)

        cairo_text.prime_font(standard_font, 12 - 3, 412)
        cairo_text.prime_font(standard_font, 13 - 3, 413)

        standard_font = prefs.linux_bold_font #"Noto Sans Bold"
        cairo_text.prime_font(standard_font, 10 - 3, 210)
        cairo_text.prime_font(standard_font, 11 - 3, 211)
        cairo_text.prime_font(standard_font, 12 - 3, 212)
        cairo_text.prime_font(standard_font, 13 - 3, 213)
        cairo_text.prime_font(standard_font, 14 - 3, 214)
        cairo_text.prime_font(standard_font, 15 - 3, 215)
        cairo_text.prime_font(standard_font, 16 - 3, 216)
        cairo_text.prime_font(standard_font, 17 - 3, 217)
        cairo_text.prime_font(standard_font, 28 - 3, 228)

    else:
        standard_font = prefs.linux_font  # "Noto Sans"
        cairo_text.prime_font(standard_font, 20 - 2, 10, 12)
        cairo_text.prime_font(standard_font, 21 - 2.5, 11, 12)
        cairo_text.prime_font(standard_font, 22 - 3, 12, 12)
        cairo_text.prime_font(standard_font, 23 - 3, 13, 17)
        cairo_text.prime_font(standard_font, 24 - 4, 14, 17)
        cairo_text.prime_font(standard_font, 25 - 4, 15, 17)
        cairo_text.prime_font(standard_font, 26 - 4, 16, 17)
        cairo_text.prime_font(standard_font, 27 - 5, 17, 17)
        cairo_text.prime_font(standard_font, 28 - 6, 18, 17)

        cairo_text.prime_font(standard_font, 22 - 3, 412, 13)
        cairo_text.prime_font(standard_font, 23 - 3, 413, 13)

        standard_font = prefs.linux_bold_font  # "Noto Sans Bold"
        cairo_text.prime_font(standard_font, 20 - 3, 210, 12)
        cairo_text.prime_font(standard_font, 21 - 3, 211, 12)
        cairo_text.prime_font(standard_font, 22 - 3, 212, 12)
        cairo_text.prime_font(standard_font, 23 - 3, 213, 12)
        cairo_text.prime_font(standard_font, 24 - 3, 214, 12)
        cairo_text.prime_font(standard_font, 25 - 3, 215, 12)
        cairo_text.prime_font(standard_font, 26 - 3, 216, 12)
        cairo_text.prime_font(standard_font, 27 - 3, 217, 12)
        cairo_text.prime_font(standard_font, 48 - 3, 228, 12)

    # standard_font = "Noto Sans Medium" #prefs.linux_bold_font
    # cairo_text.prime_font(standard_font, 13 - 3, 313)


def draw_text2(location, text, colour, font, maxx, field=0, index=0):

    return draw_text(location, text, colour, font, maxx)


def draw_text(location, text, colour, font, max=1000, bg=None):


    if gui.win_text:

        if text == "":
            return 1  # im not suuure why this needs to be 1 for the highlighting to work
        if bg == None:
            bg = gui.win_fore

        if colour[3] != 255:
            colour = alpha_blend(colour, bg)

        align = 0
        if len(location) > 2:
            if location[2] == 1:
                align = 1
            if location[2] == 2:
                align = 2
            if location[2] == 4:
                max_y = None
                if len(location) > 4:
                    max_y = location[4]

                pretty_text.draw(location[0], location[1], text, bg, colour, font, 0, True, location[3], max_y)
                return

        if max < 1000:
            text = trunc_line(text, font, max)

        return pretty_text.draw(location[0], location[1], text, bg, colour, font, align)

    elif gui.cairo_text:

        if text == "":
            return 0
        if bg == None:
            bg = gui.win_fore
        if colour[3] != 255:
            colour = alpha_blend(colour, bg)
        align = 0
        if len(location) > 2:
            if location[2] == 1:
                align = 1
            if location[2] == 2:
                align = 2
            if location[2] == 4:
                max_y = None
                if len(location) > 4:
                    max_y = location[4]
                return cairo_text.draw_text_cairo(location, text, colour, font, location[3], bg, max_y=max_y, wrap=True)

        if max < 1000:
            text = trunc_line(text, font, max)
        return cairo_text.draw_text_cairo(location, text, colour, font, max, bg, align)
    else:
        print("draw sdl")
        return draw_text_sdl(location, text, colour, font, max)

# Pretty Text

if system == 'windows':

    class RECT(ctypes.Structure):
        _fields_ = [('left', ctypes.c_long),
                    ('top', ctypes.c_long),
                    ('right', ctypes.c_long),
                    ('bottom', ctypes.c_long)
                    ]

    def RGB(r, g, b):
        return r | (g << 8) | (b << 16)

    def Wcolour(colour):
        return colour[0] | (colour[1] << 8) | (colour[2] << 16)

    def native_bmp_to_sdl(hdc, bitmap_handle, width, height):

        bmpheader = struct.pack("LHHHH", struct.calcsize("LHHHH"),
                                width, height, 1, 24) #w,h, planes=1, bitcount)
        c_bmpheader = ctypes.c_buffer(bmpheader)

        #3 bytes per pixel, pad lines to 4 bytes
        c_bits = ctypes.c_buffer(b" " * (height * ((width*3 + 3) & -4)))

        res = ctypes.windll.gdi32.GetDIBits(
            hdc, bitmap_handle, 0, height,
            c_bits, c_bmpheader,
            win32con.DIB_RGB_COLORS)
        if not res:
            raise IOError("native_bmp_to_pil failed: GetDIBits")

        # We need to keep c_bits pass else it may be garbage collected
        return SDL_CreateRGBSurfaceWithFormatFrom(ctypes.pointer(c_bits), width, height, 24, (width*3 + 3) & -4 , SDL_PIXELFORMAT_BGR24), c_bits


    class Win32Font:
        def __init__(self, name, height, weight=win32con.FW_NORMAL,
                     italic=False, underline=False):
            self.font = win32ui.CreateFont({
                'name': name, 'height': height,
                'weight': weight, 'italic': italic, 'underline': underline,}) #'charset': win32con.MAC_CHARSET})

            #create a compatible DC we can use to draw:
            self.desktopHwnd = win32gui.GetDesktopWindow()
            self.desktopDC = win32gui.GetWindowDC(self.desktopHwnd)

            self.mfcDC = win32ui.CreateDCFromHandle(self.desktopDC)
            self.drawDC = self.mfcDC.CreateCompatibleDC()

            #initialize it
            self.drawDC.SelectObject(self.font)

        def get_metrics(self, text):

            return self.drawDC.GetTextExtent(text)

        def renderText(self, text, bg, fg, wrap=False, max_x=100, max_y=None):

            self.drawDC.SetTextColor(Wcolour(fg))
            t = self.drawDC.GetSafeHdc()
            win32gui.SetBkMode(t, win32con.TRANSPARENT)

            #create the compatible bitmap:
            w,h = self.drawDC.GetTextExtent(text)
            #print(self.drawDC.GetTextFace())

            w += 1

            if wrap:
                h = int((w / max_x) * h) + h
                w = max_x + 1
            if max_y != None:

                h = max_y

            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(self.mfcDC, w, h)
            self.drawDC.SelectObject(saveBitMap)

            #draw it
            br = win32ui.CreateBrush(win32con.BS_SOLID, Wcolour(bg), 0)
            self.drawDC.FillRect((0, 0, w, h), br)

            #self.drawDC.DrawText(text, (0, 0, w, h), win32con.DT_LEFT)
            #windll.gdi32.TextOutW(t, 0, 0, "test", 5)

            if wrap:

                rect = RECT(0,0,0,0)
                rect.left = 0
                rect.right = max_x
                rect.top = 0
                rect.bottom = h

                windll.User32.DrawTextW(t, text, len(text), rect, win32con.DT_WORDBREAK)

            else:
                windll.gdi32.TextOutW(t, 0, 0, text, len(text))

            # rects = pointer(rect)
            # print(rects)

            #
            #print(text)
            #windll.gdi32.ExtTextOutW(t, 0, 0, None, rect, text, len(text), None)


            #convert to SDL surface
            im, c_bits = native_bmp_to_sdl(self.drawDC.GetSafeHdc(), saveBitMap.GetHandle(), w, h)

            #clean-up
            win32gui.DeleteObject(saveBitMap.GetHandle())

            return im, c_bits

        def __del__(self):
            self.mfcDC.DeleteDC()
            self.drawDC.DeleteDC()
            win32gui.ReleaseDC(self.desktopHwnd, self.desktopDC)
            win32gui.DeleteObject(self.font.GetSafeHandle())

        def __del__(self):
            win32gui.DeleteObject(self.font.GetSafeHandle())


    class PrettyText:

        def __init__(self):

            self.f_dict = {}
            self.y_offset_dict = {}

            self.cache = {}
            self.ca_li = []

        def prime_font(self, name, size, user_handle, weight=500, y_offset=0):

            self.f_dict[user_handle] = Win32Font(name, size, weight)
            self.y_offset_dict[user_handle] = y_offset

        def text_xy(self, text, font):

            if font == None or font not in self.f_dict:
                print("Missing Font")
                print(font)
                return

            return self.f_dict[font].get_metrics(text)

        def draw(self, x, y, text, bg, fg, font=None, align=0, wrap=False, max_x=100, max_y=None):

            y += self.y_offset_dict[font]

            key = (text, font, fg[0], fg[1], fg[2], fg[3], bg[1], bg[2], bg[3])
            if key in self.cache:

                sd = self.cache[key]
                sd[0].x = x
                sd[0].y = y

                if align == 1:
                    sd[0].x = x - sd[0].w

                elif align == 2:
                    sd[0].x = sd[0].x - int(sd[0].w / 2)

                #SDL_RenderCopy(renderer, sd[1], None, sd[0])
                SDL_RenderCopyEx(renderer, sd[1], None, sd[0], 0, None, SDL_FLIP_VERTICAL)

                return sd[0].w

            if font == None or font not in self.f_dict:
                print("Missing Font")
                print(font)
                return 0

            #perf_timer.set()

            f = self.f_dict[font]

            im, c_bits = f.renderText(text, bg, fg, wrap, max_x, max_y)
            #buff = io.BytesIO()

            #im.save(buff, format="BMP")
            #buff.seek(0)
            #wop = rw_from_object(buff)
            #s_image = IMG_Load_RW(wop, 0)
            s_image = im

            ke = SDL_MapRGB(s_image.contents.format, bg[0], bg[1], bg[2])
            SDL_SetColorKey(s_image, True, ke)

            c = SDL_CreateTextureFromSurface(renderer, s_image)

            tex_w = pointer(c_int(0))
            tex_h = pointer(c_int(0))
            SDL_QueryTexture(c, None, None, tex_w, tex_h)
            dst = SDL_Rect(x, y)
            dst.w = int(tex_w.contents.value)
            dst.h = int(tex_h.contents.value)
            SDL_FreeSurface(s_image)
            #im.close()

            if align == 1:
                dst.x = x - dst.w

            elif align == 2:
                dst.x = dst.x - int(dst.w / 2)

            #SDL_RenderCopy(renderer, c, None, dst)
            SDL_RenderCopyEx(renderer, c, None, dst, 0, None, SDL_FLIP_VERTICAL)

            #print(perf_timer.get())

            self.cache[key] = [dst, c]
            self.ca_li.append(key)
            if len(self.ca_li) > 350:
                SDL_DestroyTexture(self.cache[self.ca_li[0]][1])
                del self.cache[self.ca_li[0]]
                del self.ca_li[0]

            return dst.w

    pretty_text = PrettyText()

    menu_font = "Meiryo UI"
    if prefs.windows_font_family != None:
        standard_font = prefs.windows_font_family
    else:
        #standard_font = 'Meiryo'
        #standard_font = 'Koruri'
        #standard_font = "Franklin Gothic Medium"
        #if not os.path.isfile('C:\Windows\Fonts\meiryo.ttc'):
        standard_font = 'Arial'
        # standard_font = 'Tahoma'
        # standard_font = 'Segoe UI'
        # standard_font = 'Arial'


    semibold_font = standard_font
    standard_weight = prefs.windows_font_weight
    bold_weight = prefs.windows_font_weight_bold

    if standard_font == "Meiryo":

        pretty_text.prime_font(standard_font, 10 + 6, 10, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 11 + 6, 11, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 12 + 6, 12, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 13 + 6, 13, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 14 + 6, 14, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 15 + 6, 15, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 16 + 6, 16, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 17 + 6, 17, weight=standard_weight, y_offset=1)

        pretty_text.prime_font('Arial', 10 + 4, 210, weight=600, y_offset=1)
        pretty_text.prime_font('Arial', 11 + 3, 211, weight=600, y_offset=1)
        pretty_text.prime_font(semibold_font, 12 + 4, 212, weight=bold_weight, y_offset=1)
        pretty_text.prime_font(semibold_font, 13 + 5, 213, weight=bold_weight, y_offset=1)
        pretty_text.prime_font(semibold_font, 14 + 4, 214, weight=bold_weight, y_offset=1)
        pretty_text.prime_font(semibold_font, 15 + 4, 215, weight=bold_weight, y_offset=1)
        pretty_text.prime_font(semibold_font, 16 + 4, 216, weight=bold_weight, y_offset=1)
        pretty_text.prime_font(semibold_font, 28 + 4, 228, weight=bold_weight, y_offset=1)

        # pretty_text.prime_font("Meiryo UI", 14, 412, weight=500)
        # pretty_text.prime_font("Meiryo UI", 15, 413, weight=500)
        pretty_text.prime_font("Arial", 14 + 1, 412, weight=500, y_offset=1)
        pretty_text.prime_font("Arial", 15 + 1, 413, weight=500, y_offset=1)

    elif standard_font == "Tahoma":

        pretty_text.prime_font(standard_font, 10 + 4, 10, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 11 + 4, 11, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 12 + 4, 12, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 13 + 4, 13, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 14 + 4, 14, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 15 + 4, 15, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 16 + 4, 16, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 17 + 4, 17, weight=standard_weight, y_offset=1)

        pretty_text.prime_font(semibold_font, 10 + 2, 210, weight=600, y_offset=1)
        pretty_text.prime_font(semibold_font, 11 + 2, 211, weight=bold_weight, y_offset=1)
        pretty_text.prime_font(semibold_font, 12 + 2, 212, weight=bold_weight, y_offset=1)
        pretty_text.prime_font(semibold_font, 13 + 3, 213, weight=bold_weight, y_offset=1)
        pretty_text.prime_font(semibold_font, 14 + 2, 214, weight=bold_weight, y_offset=1)
        pretty_text.prime_font(semibold_font, 15 + 2, 215, weight=bold_weight, y_offset=1)
        pretty_text.prime_font(semibold_font, 16 + 2, 216, weight=bold_weight, y_offset=1)
        pretty_text.prime_font(semibold_font, 28 + 2, 228, weight=bold_weight, y_offset=1)

        # pretty_text.prime_font("Meiryo UI", 14, 412, weight=500)
        # pretty_text.prime_font("Meiryo UI", 15, 413, weight=500)
        pretty_text.prime_font("Arial", 14 + 1, 412, weight=500, y_offset=1)
        pretty_text.prime_font("Arial", 15 + 1, 413, weight=500, y_offset=1)

        gui.pl_title_y_offset = -3
        gui.pl_title_font_offset = -2


    elif standard_font == "Arial":

        pretty_text.prime_font(standard_font, 10 + 3, 10, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 11 + 3, 11, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 12 + 3, 12, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 13 + 3, 13, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 14 + 2, 14, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 15 + 2, 15, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 16 + 2, 16, weight=standard_weight, y_offset=1)
        pretty_text.prime_font(standard_font, 17 + 2, 17, weight=standard_weight, y_offset=1)

        pretty_text.prime_font(semibold_font, 10 + 3, 210, weight=600)
        pretty_text.prime_font('Arial', 11 + 3, 211, weight=600, y_offset=1)
        pretty_text.prime_font(semibold_font, 12 + 3, 212, weight=bold_weight, y_offset=0)
        pretty_text.prime_font(semibold_font, 13 + 3, 213, weight=bold_weight, y_offset=2)
        pretty_text.prime_font(semibold_font, 14 + 2, 214, weight=bold_weight)
        pretty_text.prime_font(semibold_font, 15 + 2, 215, weight=bold_weight)
        pretty_text.prime_font(semibold_font, 16 + 2, 216, weight=bold_weight)
        pretty_text.prime_font(semibold_font, 28 + 2, 228, weight=bold_weight)

        pretty_text.prime_font("Arial", 14 + 1, 412, weight=500, y_offset=1)
        pretty_text.prime_font("Arial", 15 + 1, 413, weight=500, y_offset=1)

        gui.pl_title_y_offset = -2
        gui.pl_title_font_offset = -1

    else: # Segoe UI


        pretty_text.prime_font(standard_font, 10 + 5, 10, weight=standard_weight, y_offset=0)
        pretty_text.prime_font(standard_font, 11 + 5, 11, weight=standard_weight, y_offset=0)
        pretty_text.prime_font(standard_font, 12 + 5, 12, weight=standard_weight, y_offset=0)
        pretty_text.prime_font(standard_font, 13 + 5, 13, weight=standard_weight, y_offset=0)
        pretty_text.prime_font(standard_font, 14 + 5, 14, weight=standard_weight, y_offset=0)
        pretty_text.prime_font(standard_font, 15 + 5, 15, weight=standard_weight, y_offset=0)
        pretty_text.prime_font(standard_font, 16 + 5, 16, weight=standard_weight, y_offset=-1)
        pretty_text.prime_font(standard_font, 17 + 5, 17, weight=standard_weight, y_offset=0)
        pretty_text.prime_font(semibold_font, 10 + 5, 210, weight=600)
        #pretty_text.prime_font('Arial', 11 + 4, 211, weight=600, y_offset=1)
        pretty_text.prime_font(semibold_font, 11 + 3, 211, weight=600, y_offset=1)
        pretty_text.prime_font(semibold_font, 12 + 4, 212, weight=bold_weight, y_offset=1)
        pretty_text.prime_font(semibold_font, 13 + 4, 213, weight=bold_weight, y_offset=0)
        pretty_text.prime_font(semibold_font, 14 + 4, 214, weight=bold_weight)
        pretty_text.prime_font(semibold_font, 15 + 4, 215, weight=bold_weight)
        pretty_text.prime_font(semibold_font, 16 + 4, 216, weight=bold_weight)
        pretty_text.prime_font(semibold_font, 28 + 4, 228, weight=bold_weight)

        pretty_text.prime_font(standard_font, 14 + 3, 412, weight=500, y_offset=-1)
        pretty_text.prime_font(standard_font, 15 + 4, 413, weight=500, y_offset=-1)

        gui.pl_title_y_offset = -1
        gui.pl_title_font_offset = -2

    # pretty_text.prime_font(menu_font, 14, 412, weight=500)
    # pretty_text.prime_font(menu_font, 15, 413, weight=500)


# pretty_text.draw(x, y + 1, word, colours.top_panel_background, bg)



# class LyricsRen:
#
#     def __init__(self):
#
#         self.index = -1
#         self.text = ""
#         self.colour = colours.lyrics
#         self.colour_sdl = SDL_Color(self.colour[0], self.colour[1], self.colour[2], self.colour[3])
#         self.tex_w = pointer(c_int(0))
#         self.tex_h = pointer(c_int(0))
#         self.font = 15
#         self.dst = SDL_Rect(1, 1)
#         self.texture = None
#
#         self.lyrics_position = 0
#
#     def generate(self, index, w):
#
#         self.text = pctl.master_library[index].lyrics
#         self.lyrics_position = 0
#
#         if self.text == "":
#             return
#         if self.texture is not None:
#             SDL_DestroyTexture(self.texture)
#
#         font_surface = TTF_RenderUTF8_Blended_Wrapped(font_dict[self.font][0], self.text.encode("utf-8"), self.colour_sdl, w)
#         self.texture = SDL_CreateTextureFromSurface(renderer, font_surface)
#         SDL_QueryTexture(self.texture, None, None, self.tex_w, self.tex_h)
#         self.dst.w = self.tex_w.contents.value
#         self.dst.h = self.tex_h.contents.value
#         SDL_FreeSurface(font_surface)
#
#     def render(self, index, x, y, w, h, p):
#
#         if index != self.index:
#             self.index = index
#             self.generate(index, w)
#
#         self.dst.x = x
#         self.dst.y = y
#
#         if self.texture is not None:
#             SDL_RenderCopy(renderer, self.texture, None, self.dst)


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

        draw_text((x, y, 4, w, 2000), self.text, colours.lyrics, 15, w, colours.side_panel_background)

# if gui.win_text or gui.cairo_text:
lyrics_ren_mini = LyricsRenMini()

class LyricsRenWin:

    def __init__(self):

        self.index = -1
        self.text = ""
        # self.colour = colours.side_bar_line1
        # self.colour_sdl = SDL_Color(self.colour[0], self.colour[1], self.colour[2], self.colour[3])
        # self.tex_w = pointer(c_int(0))
        # self.tex_h = pointer(c_int(0))
        # self.font = 15
        # self.dst = SDL_Rect(1, 1)
        # self.texture = None

        self.lyrics_position = 0

    def generate(self, index, w):

        self.text = pctl.master_library[index].lyrics
        self.lyrics_position = 0

        # if self.text == "":
        #     return
        # if self.texture is not None:
        #     SDL_DestroyTexture(self.texture)
        #
        # font_surface = TTF_RenderUTF8_Blended_Wrapped(font_dict[self.font][0], self.text.encode("utf-8"), self.colour_sdl, w)
        # self.texture = SDL_CreateTextureFromSurface(renderer, font_surface)
        # SDL_QueryTexture(self.texture, None, None, self.tex_w, self.tex_h)
        # self.dst.w = self.tex_w.contents.value
        # self.dst.h = self.tex_h.contents.value
        # SDL_FreeSurface(font_surface)

    def render(self, index, x, y, w, h, p):

        if index != self.index or self.text != pctl.master_library[index].lyrics:
            self.index = index
            self.generate(index, w)

        draw_text((x, y, 4, w, 2000), self.text, colours.lyrics, 17, w, colours.playlist_panel_background)

# if gui.win_text or gui.cairo_text:
lyrics_ren = LyricsRenWin()
# else:
#     lyrics_ren = LyricsRen()


def draw_linked_text(location, text, colour, font):
    base = ""
    link_text = ""
    rest = ""
    on_base = True
    for i in range(len(text)):
        if text[i:i + 7] == "http://" or text[i:i + 4] == "www." or text[i:i + 8] == "https://":
            on_base = False
        if on_base:
            base += text[i]
        else:
            if i == len(text) or text[i] in '\\) "\'':
                rest = text[i:]
                break
            else:
                link_text += text[i]

    left = draw.text_calc(base, font)
    right = draw.text_calc(base + link_text, font)

    x = location[0]
    y = location[1]

    draw_text((x, y), base, colour, font)
    draw_text((x + left, y), link_text, colours.link_text, font)
    draw_text((x + right, y), rest, colour, font)
    if gui.win_text:
        y += 1
    if gui.scale == 2:
        font *= 2
        font += 4
    draw.line(x + left, y + font + 2, x + right, y + font + 2, alpha_mod(colours.link_text, 120))

    return left, right - left, link_text



class TextBox:

    cursor = True

    def __init__(self):

        self.text = ""
        self.cursor_position = 0
        self.selection = 0
        self.down_lock = False

    def paste(self):

        if SDL_HasClipboardText():
            clip = SDL_GetClipboardText().decode('utf-8')

            if 'http://' in self.text and 'http://' in clip:
                self.text = ""

            clip = clip.rstrip(" ").lstrip(" ")
            clip = clip.replace('\n', ' ').replace('\r', '')

            self.eliminate_selection()
            self.text = self.text[0: len(self.text) - self.cursor_position] + clip + self.text[len(
                self.text) - self.cursor_position:]

    def copy(self):

        text = self.get_selection()
        if text != "":
            SDL_SetClipboardText(text.encode('utf-8'))

    def set_text(self, text):

        self.text = text
        self.cursor_position = 0
        self.selection = 0

    def clear(self):
        self.text = ""

    def eliminate_selection(self):
        if self.selection != self.cursor_position:
            if self.selection > self.cursor_position:
                self.text = self.text[0: len(self.text) - self.selection] + self.text[len(self.text) - self.cursor_position:]
                self.selection = self.cursor_position
            else:
                self.text = self.text[0: len(self.text) -  self.cursor_position] + self.text[len(self.text) - self.selection:]
                self.cursor_position = self.selection

    def get_selection(self, p=1):
        if self.selection != self.cursor_position:
            if p == 1:
                if self.selection > self.cursor_position:
                    return self.text[len(self.text) - self.selection : len(self.text) - self.cursor_position]

                else:
                    return self.text[len(self.text) -  self.cursor_position: len(self.text) - self.selection]
            if p == 0:
                return self.text[0: len(self.text) - max(self.cursor_position, self.selection)]
            if p == 2:
                return self.text[len(self.text) - min(self.cursor_position, self.selection):]

        else:
            return ""

    def draw(self, x, y, colour, active=True, secret=False, font=13, width=0, click=False, selection_height=18):

        # A little bit messy.
        # For now, this is set up so where 'width' is set > 0, the cursor position becomes editable,
        # otherwise it is fixed to end
        if click is False:
            click = input.mouse_click


        if width > 0 and active:

            rect = (x - 3, y - 2, width - 3, 21)

            # Activate Menu
            if coll_point(mouse_position, rect):
                if right_click or level_2_right_click:
                    field_menu.activate(self)

            if click and field_menu.active:
                # field_menu.click()
                click = False

            # Add text from input
            if input_text != "":
                self.eliminate_selection()
                self.text = self.text[0: len(self.text) - self.cursor_position] + input_text + self.text[len(self.text) - self.cursor_position:]

            # Handle backspace
            if key_backspace_press and len(self.text) > 0 and self.cursor_position < len(self.text):
                if self.selection != self.cursor_position:
                    self.eliminate_selection()
                else:
                    self.text = self.text[0:len(self.text) - self.cursor_position- 1] + self.text[len(self.text) - self.cursor_position:]
            elif key_backspace_press and len(self.get_selection()) > 0:
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
                clip = SDL_GetClipboardText().decode('utf-8')
                self.eliminate_selection()
                self.text = self.text[0: len(self.text) - self.cursor_position] + clip + self.text[len(
                    self.text) - self.cursor_position:]

            if key_ctrl_down and key_c_press:
                self.copy()

            if key_ctrl_down and key_x_press:
                if len(self.get_selection()) > 0:
                    text = self.get_selection()
                    if text != "":
                        SDL_SetClipboardText(text.encode('utf-8'))
                    self.eliminate_selection()


            # draw.rect_r(rect, [255, 50, 50, 80], True)
            if coll_point(mouse_position, rect) and not field_menu.active:
                gui.cursor_mode = 4
                SDL_SetCursor(cursor_text)
            elif gui.cursor_mode == 4:
                SDL_SetCursor(cursor_standard)

            if gui.cursor_mode == 4:
                gui.flag_special_cursor = True

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

            if rect_in((x - 15, y, width + 16, 19)):
                if click:
                    pre = 0
                    post = 0
                    if mouse_position[0] < x + 1:
                        self.cursor_position = len(self.text)
                    else:
                        for i in range(len(self.text)):
                            post = draw.text_calc(self.text[0:i+1], font)
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
                        post = draw.text_calc(self.text[0:i + 1], font)
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

            a = draw.text_calc(self.text[0: len(self.text) - self.cursor_position], font)
            # print("")
            # print(self.selection)
            # print(self.cursor_position)

            b = draw.text_calc(self.text[0: len(self.text) - self.selection], font)

            #rint((a, b))
            draw.rect_r([x + a, y, b - a, selection_height], [40, 120, 180, 255], True)

            if self.selection != self.cursor_position:
                inf_comp = 0
                if not gui.cairo_text:
                    inf_comp = 1
                space = draw_text((x, y), self.get_selection(0), colour, font)
                space += draw_text((x + space - inf_comp, y), self.get_selection(1), [240,240,240,255], font, bg=[40, 120, 180, 255],)
                draw_text((x + space - (inf_comp * 2), y), self.get_selection(2), colour, font)
            else:
                draw_text((x, y), self.text, colour, font)



            space = draw.text_calc(self.text[0: len(self.text) - self.cursor_position], font)



            if TextBox.cursor and self.selection == self.cursor_position:
                #draw.line(x + space, y + 2, x + space, y + 15, colour)
                draw.rect_r((x + space, y + 2, 1 * gui.scale, 14 * gui.scale), colour, True)

            if click:
                self.selection = self.cursor_position



        else:
            if active:
                self.text += input_text
                if input_text != "":
                    self.cursor = True
                if key_backspace_press and len(self.text) > 0:
                    self.text = self.text[:-1]
                if key_ctrl_down and key_v_press:
                    self.paste()

            if secret:
                space = draw_text((x, y), '●' * len(self.text), colour, font)
            else:
                space = draw_text((x, y), self.text, colour, font)

            if active and TextBox.cursor:
                xx = x + space + 1
                yy = y + 3
                #draw.line(xx, yy, xx, yy + 12, colour)
                draw.rect_r((xx, yy, 1 * gui.scale, 14 * gui.scale), colour, True)

        if active and editline != "" and editline != input_text:
            ex = draw_text((x + space + 4, y), editline, [240, 230, 230, 255], font)
            #draw.line(x + space + 4, y + 13, x + space + 4 + ex, y + 13, [245, 245, 245, 255])

        animate_monitor_timer.set()


rename_text_area = TextBox()
search_text = TextBox()
last_fm_user_field = TextBox()
last_fm_pass_field = TextBox()
rename_files = TextBox()
rename_files.text = prefs.rename_tracks_template
radio_field = TextBox()
radio_field.text = radio_field_text
rename_folder = TextBox()
rename_folder.text = prefs.rename_folder_template

temp_dest = SDL_Rect(0, 0)






class GallClass:
    def __init__(self, size=250, save_out=True):
        self.gall = {}
        self.size = size
        self.queue = []
        self.key_list = []
        self.save_out = save_out
        self.i = 0

    def get_file_source(self, index):

        global album_art_gen

        sources = album_art_gen.get_sources(index)

        if len(sources) == 0:
            return False
        offset = album_art_gen.get_offset(pctl.master_library[index].fullpath, sources)
        return sources[offset] + [offset]

    def worker_render(self):

        while len(self.queue) > 0:

            self.i += 1

            key = self.queue[0]
            order = self.gall[key]

            source = self.get_file_source(key[0])

            if source is False:
                order[0] = 0
                self.gall[key] = order
                del self.queue[0]
                continue

            img_name = str(self.size) + '-' + str(key[0]) + "-" + str(source[2])

            try:
                if prefs.cache_gallery and os.path.isfile(user_directory + "/cache/" + img_name + '.jpg'):
                    source_image = open(user_directory + "/cache/" + img_name + '.jpg', 'rb')
                    # print('load from cache')

                elif source[0] is True:
                    # print('tag')
                    source_image = io.BytesIO(album_art_gen.get_embed(key[0]))

                else:
                    source_image = open(source[1], 'rb')

                g = io.BytesIO()
                g.seek(0)
                # print('pro stage 1')
                im = Image.open(source_image)
                if im.mode != "RGB":
                    im = im.convert("RGB")
                im.thumbnail((self.size, self.size), Image.ANTIALIAS)

                im.save(g, 'BMP')
                if self.save_out and prefs.cache_gallery and not os.path.isfile(user_directory + "/cache/" + img_name + '.jpg'):
                    # print("no old found")
                    im.save(user_directory + "/cache/" + img_name + '.jpg', 'JPEG')

                g.seek(0)

                source_image.close()

                order = [2, g, None, None]
                self.gall[key] = order

                gui.update += 1
                if gui.combo_mode:
                    gui.pl_update = 1
                del source

                if not prefs.cache_gallery:
                    time.sleep(0.01)
                else:
                    time.sleep(0.002)

            except:
                print('Image load failed on track: ' + pctl.master_library[key[0]].fullpath)
                order = [0, None, None, None]
                self.gall[key] = order

            del self.queue[0]

        if self.i > 0:
            self.i = 0
            return True
        else:
            return False

    def render(self, index, location):

        # time.sleep(0.1)

        if (index, self.size) in self.gall:
            # print("old")

            order = self.gall[(index, self.size)]

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
                tex_w = pointer(c_int(self.size))
                tex_h = pointer(c_int(self.size))
                SDL_QueryTexture(c, None, None, tex_w, tex_h)
                dst = SDL_Rect(location[0], location[1])
                dst.w = int(tex_w.contents.value)
                dst.h = int(tex_h.contents.value)

                order[0] = 3
                order[1] = None
                order[2] = c
                order[3] = dst
                self.gall[(index, self.size)] = order

            if order[0] == 3:
                # ready

                order[3].x = location[0]
                order[3].y = location[1]
                order[3].x = int((self.size - order[3].w) / 2) + order[3].x
                order[3].y = int((self.size - order[3].h) / 2) + order[3].y
                SDL_RenderCopy(renderer, order[2], None, order[3])
                return True

        else:
            # Create new
            # stage, raw, texture, rect
            self.gall[(index, self.size)] = [1, None, None, None]
            self.queue.append((index, self.size))
            self.key_list.append((index, self.size))

            # Remove old images to conserve RAM usage
            if len(self.key_list) > 500:
                key = self.key_list[0]
                while key in self.queue:
                    self.queue.remove(key)
                if self.gall[key][2] is not None:
                    SDL_DestroyTexture(self.gall[key][2])
                del self.gall[key]
                del self.key_list[0]

        return False


gall_ren = GallClass(album_mode_art_size)

pl_thumbnail = GallClass(save_out=False)


class ThumbTracks:
    def __init__(self):
        pass

    def path(self, track):
        image_name = track.album
        if image_name == "":
            image_name = track.title
        if image_name == "":
            image_name = "noname"

        source = gall_ren.get_file_source(track.index)

        if source is False:
            print("NO ART")
            return None

        image_name += "-" + str(source[2])
        image_name = "".join([c for c in image_name if c.isalpha() or c.isdigit() or c == ' ']).rstrip()


        t_path = user_directory + "/cache/" + image_name + '.jpg'
        if os.path.isfile(t_path):
            return t_path

        #print(source[0])

        if source[0] is True:
        # print('tag')
            source_image = io.BytesIO(album_art_gen.get_embed(track.index))

        else:
            source_image = open(source[1], 'rb')

        if not os.path.isdir(cache_directory):
            os.makedirs(cache_directory)

        g = io.BytesIO()
        g.seek(0)
        # print('pro stage 1')
        im = Image.open(source_image)
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.thumbnail((250, 250), Image.ANTIALIAS)

        im.save(t_path, 'JPEG')
        source_image.close()

        return t_path


thumb_tracks = ThumbTracks()



def img_slide_update_combo(value):
    global combo_mode_art_size
    combo_mode_art_size = value
    clear_img_cache()

    # Update sizes
    if not gui.combo_mode:
        gall_ren.size = album_mode_art_size
    else:
        gall_ren.size = combo_mode_art_size
        combo_pl_render.prep()
        update_layout = True
        gui.pl_update = 1

def img_slide_update_gall(value):

    global album_mode_art_size
    album_mode_art_size = value
    clear_img_cache()

    # Update sizes
    if not gui.combo_mode:
        gall_ren.size = album_mode_art_size
    else:
        gall_ren.size = combo_mode_art_size
        combo_pl_render.prep()
        update_layout = True
        gui.pl_update = 1

def clear_img_cache():
    global album_art_gen
    album_art_gen.clear_cache()
    gall_ren.key_list = []
    while len(gall_ren.queue) > 0:
        time.sleep(0.01)

    for key, value in gall_ren.gall.items():
        SDL_DestroyTexture(value[2])
    gall_ren.gall = {}

    if prefs.cache_gallery:
        direc = os.path.join(user_directory, 'cache')
        if os.path.isdir(direc):
            shutil.rmtree(direc)
        os.makedirs(direc)

    gui.update += 1



class ImageObject():
    def __init__(self):
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


class AlbumArt():
    def __init__(self):
        self.image_types = {'jpg', 'JPG', 'jpeg', 'JPEG', 'PNG', 'png', 'BMP', 'bmp', 'GIF', 'gif'}
        self.art_folder_names = {'art', 'scans', 'scan', 'booklet', 'images', 'image', 'cover',
                                 'covers', 'coverart', 'albumart', 'gallery', 'jacket', 'artwork',
                                 'bonus', 'bk', 'cover artwork', 'cover art'}
        self.source_cache = {}
        self.image_cache = []
        self.current_wu = None

    def get_info(self, index):

        sources = self.get_sources(index)
        if len(sources) == 0:
            return None
        offset = self.get_offset(pctl.master_library[index].fullpath, sources)

        o_size = (0, 0)
        format = "ERROR"
        for item in self.image_cache:
            if item.index == index and item.offset == offset:
                o_size = item.original_size
                format = item.format
                break

        return [sources[offset][0], len(sources), offset, o_size, format]

    def get_sources(self, index):

        filepath = pctl.master_library[index].fullpath

        # Check if source list already exists, if not, make it
        if index in self.source_cache:
            return self.source_cache[index]
        else:
            pass

        source_list = []  # istag,

        try:
            direc = os.path.dirname(filepath)
            items_in_dir = os.listdir(direc)
        except:
            print("Error loading directroy")
            return []

        try:
            if '.mp3' in filepath or '.MP3' in filepath:
                tag = stagger.read_tag(filepath)

                try:
                    tt = tag[APIC][0]
                except:
                    tt = tag[PIC][0]

                if len(tt.data) > 30:
                    source_list.append([True, filepath])

            elif '.flac' in filepath or '.FLAC' in filepath:

                tt = Flac(filepath)
                tt.read(True)
                if tt.has_picture is True and len(tt.picture) > 30:
                    source_list.append([True, filepath])

            elif '.ape' in filepath or '.APE' in filepath:

                tt = Ape(filepath)
                tt.read()
                if tt.has_picture is True and len(tt.picture) > 30:
                    source_list.append([True, filepath])

                    # elif '.opus' in filepath or '.OPUS' in filepath or ".ogg" in filepath or ".OGG" in filepath:
                    #
                    #     tt = Opus(filepath)
                    #     tt.read()
                    #     print("test")
                    #     if tt.has_picture is True and len(tt.picture) > 30:
                    #         source_list.append([True, filepath])

        except:
            # raise
            pass

        for i in range(len(items_in_dir)):

            if os.path.splitext(items_in_dir[i])[1][1:] in self.image_types:
                dir_path = os.path.join(direc, items_in_dir[i]).replace('\\', "/")
                source_list.append([False, dir_path])

            elif os.path.isdir(os.path.join(direc, items_in_dir[i])) and \
                            items_in_dir[i].lower() in self.art_folder_names:

                subdirec = os.path.join(direc, items_in_dir[i])
                items_in_dir2 = os.listdir(subdirec)

                for y in range(len(items_in_dir2)):
                    if os.path.splitext(items_in_dir2[y])[1][1:] in self.image_types:
                        dir_path = os.path.join(subdirec, items_in_dir2[y]).replace('\\', "/")
                        source_list.append([False, dir_path])

        self.source_cache[index] = source_list

        return source_list

    def fast_display(self, index, location, box, source, offset):

        # Renders cached image only by given size for faster performance

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

        temp_dest.x = location[0]
        temp_dest.y = location[1]

        temp_dest.w = box[0]
        temp_dest.h = box[1]

        # correct aspect ratio if needed
        if unit.original_size[0] > unit.original_size[1]:
            temp_dest.w = box[0]
            temp_dest.h = int(temp_dest.h * (unit.original_size[1] / unit.original_size[0]))
        elif unit.original_size[0] < unit.original_size[1]:
            temp_dest.h = box[1]
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

    def open_external(self, index):

        source = self.get_sources(index)
        if len(source) == 0:
            return 0

        offset = self.get_offset(pctl.master_library[index].fullpath, source)

        if source[offset][0] is True:
            return 0

        if system == "windows":
            os.startfile(source[offset][1])
        elif system == 'mac':
            subprocess.call(["open", source[offset][1]])
        else:
            subprocess.call(["xdg-open", source[offset][1]])

        return 0

    def cycle_offset(self, index, reverse=False):

        filepath = pctl.master_library[index].fullpath
        sources = self.get_sources(index)
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

    def cycle_offset_reverse(self, index):
        self.cycle_offset(index, True)

    def get_offset(self, filepath, source):

        # Check if folder offset already exsts, if not, make it
        parent_folder = os.path.dirname(filepath)

        if parent_folder in folder_image_offsets:

            # Reset the offset if greater then number of images available
            if folder_image_offsets[parent_folder] > len(source) - 1:
                folder_image_offsets[parent_folder] = 0
        else:
            folder_image_offsets[parent_folder] = 0

        return folder_image_offsets[parent_folder]

    def get_embed(self, index):

        filepath = pctl.master_library[index].fullpath

        if pctl.master_library[index].file_ext == 'MP3':

            tag = stagger.read_tag(filepath)
            try:
                return tag[APIC][0].data
            except:
                return tag[PIC][0].data


        elif pctl.master_library[index].file_ext == 'FLAC':
            tag = Flac(filepath)
            tag.read(True)
            return tag.picture

        elif pctl.master_library[index].file_ext == 'APE':
            tag = Ape(filepath)
            tag.read()
            return tag.picture

            # elif pctl.master_library[index].file_ext == 'OPUS' or pctl.master_library[index].file_ext == 'OGG':
            #     tag = Opus(filepath)
            #     tag.read()
            #     return tag.picture

    def get_base64(self, index, size):

        filepath = pctl.master_library[index].fullpath
        sources = self.get_sources(index)

        if len(sources) == 0:
            return False

        offset = self.get_offset(filepath, sources)

        if sources[offset][0] == True:
            # Target is a embedded image
            source_image = io.BytesIO(self.get_embed(index))
        else:
            source_image = open(sources[offset][1], 'rb')

        im = Image.open(source_image)
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.thumbnail(size, Image.ANTIALIAS)
        buff = io.BytesIO()
        im.save(buff, format="JPEG")
        sss = base64.b64encode(buff.getvalue())
        return sss

    def save_thumb(self, index, size, save_path):

        filepath = pctl.master_library[index].fullpath
        sources = self.get_sources(index)

        if len(sources) == 0:
            return False

        offset = self.get_offset(filepath, sources)

        if sources[offset][0] is True:
            # Target is a embedded image
            source_image = io.BytesIO(self.get_embed(index))
        else:
            source_image = open(sources[offset][1], 'rb')

        im = Image.open(source_image)
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(save_path + '.jpg', 'JPEG')

    def display(self, index, location, box, fast=False):

        filepath = pctl.master_library[index].fullpath

        if prefs.colour_from_image and index != gui.theme_temp_current and box[0] != 115: #mark2233
            if pctl.master_library[index].album in gui.temp_themes:
                global colours
                colours = gui.temp_themes[pctl.master_library[index].album]

                gui.theme_temp_current = index

        source = self.get_sources(index)
        if len(source) == 0:
            return False

        offset = self.get_offset(filepath, source)

        # Check if request matches previous
        if self.current_wu is not None and self.current_wu.source == source[offset][1] and \
                        self.current_wu.request_size == box:
            self.render(self.current_wu, location)
            return 0

        if fast:
            return self.fast_display(index, location, box, source, offset)

        # Check if cached
        for unit in self.image_cache:
            if unit.index == index and unit.request_size == box and unit.offset == offset:
                self.render(unit, location)
                return 0

        # Render new...
        try:

            # Get source IO
            if source[offset][0] is True:
                # Target is a embedded image
                source_image = io.BytesIO(self.get_embed(index))
            else:
                source_image = open(source[offset][1], 'rb')


            # # Temporary Fix
            # quick_d_timer.set()

            # Generate
            g = io.BytesIO()
            g.seek(0)
            im = Image.open(source_image)
            o_size = im.size

            format = im.format
            if im.format == "JPEG":
                format = "JPG"

            # print(im.size)
            if im.mode != "RGB":
                im = im.convert("RGB")
            im.thumbnail((box[0], box[1]), Image.ANTIALIAS)
            im.save(g, 'BMP')
            g.seek(0)

            if prefs.colour_from_image and box[0] != 115 and index != gui.theme_temp_current: # and pctl.master_library[index].parent_folder_path != colours.last_album: #mark2233
                colours.last_album = pctl.master_library[index].parent_folder_path

                im.thumbnail((50, 50), Image.ANTIALIAS)
                pixels = im.getcolors(maxcolors=2500)
                # print(pixels)
                pixels = sorted(pixels, key=lambda x: x[0], reverse=True)[:]
                # print(pixels)

                min_colour_varience = 75

                x_colours = []
                for item in pixels:
                    colour = item[1]
                    for cc in x_colours:
                        if abs(colour[0] - cc[0]) < min_colour_varience and abs(
                                        colour[1] - cc[1]) < min_colour_varience and abs(
                                        colour[2] - cc[2]) < min_colour_varience:
                            # if abs(colour[0] - cc[0]) + abs(
                            #                 colour[1] - cc[1]) + abs(
                            #                 colour[2] - cc[2]) < min_colour_varience:
                            break
                    else:
                        x_colours.append(colour)

                # print(x_colours)

                colours.playlist_panel_background = x_colours[0] + (255,)
                if len(x_colours) > 1:
                    colours.side_panel_background = x_colours[1] + (255,)
                    if len(x_colours) > 2:
                        colours.title_text = x_colours[2] + (255,)
                        colours.title_playing = x_colours[2] + (255,)
                        if len(x_colours) > 3:
                            colours.artist_text = x_colours[3] + (255,)
                            colours.artist_playing = x_colours[3] + (255,)

                bg = 0
                ar = 0
                ti = 0

                print("")

                if colour_value(colours.playlist_panel_background) < 120:
                    print("Backgroud is dark")
                    bg = 1
                if colour_value(colours.playlist_panel_background) > 300:
                    print("Backgroud is Light")
                    bg = 2
                if colour_value(colours.title_text) < 190:
                    print("Title is dark")
                    ti = 1
                if colour_value(colours.title_text) > 300:
                    print("Title is Light")
                    ti = 2
                if colour_value(colours.artist_text) < 190:
                    print("Artist is dark")
                    ar = 1
                if colour_value(colours.artist_text) > 400:
                    print("Artist is Light")
                    ar = 2

                if bg == 2 and ti == 2:
                    # print("fix!")
                    colours.title_text = [40, 40, 40, 255]
                    colours.title_playing = [40, 40, 40, 255]

                if bg == 2 and ar == 2:
                    # print("fix!")
                    colours.artist_text = [20, 20, 20, 255]
                    colours.artist_playing = [20, 20, 20, 255]

                if bg == 1 and ti == 1:
                    # print("fix!")
                    colours.title_text = [200, 200, 200, 255]
                    colours.title_playing = [200, 200, 200, 255]

                if bg == 1 and ar == 1:
                    # print("fix!")
                    colours.artist_text = [170, 170, 170, 255]
                    colours.artist_playing = [170, 170, 170, 255]

                if (colour_value(colours.side_panel_background)) > 350:
                    colours.side_bar_line1 = [25, 25, 25, 255]
                    colours.side_bar_line2 = [35, 35, 35, 255]
                else:
                    colours.side_bar_line1 = [220, 220, 220, 255]
                    colours.side_bar_line2 = [205, 205, 205, 255]

                colours.album_text = colours.title_text
                colours.album_playing = colours.title_playing

                gui.pl_update = 1
                print("Bgr1: ", end="")
                print(colours.playlist_panel_background)
                print("Bgr2: ", end="")
                print(colours.side_panel_background)
                print("Txt1: ", end="")
                print(colours.artist_text)
                print("Txt2: ", end="")
                print(colours.title_text)

                print("Colours found: ", end="")
                print(len(x_colours))
                print("Background perceived lightness: ", end="")
                prcl = 100 - int(test_lumi(colours.playlist_panel_background) * 100)
                print(prcl, end="")
                print("%")

                if prcl > 45:
                    ce = alpha_blend([0, 0, 0, 180], colours.playlist_panel_background) #[40, 40, 40, 255]
                    colours.index_text = ce
                    colours.index_playing = ce
                    colours.time_text = ce
                    colours.bar_time = ce
                    colours.folder_title = ce
                    colours.star_line = [60, 60, 60, 255]
                    colours.row_select_highlight = [0, 0, 0, 30]
                    colours.row_playing_highlight = [0, 0, 0, 20]
                else:
                    ce = alpha_blend([255, 255, 255, 160], colours.playlist_panel_background) #[165, 165, 165, 255]
                    colours.index_text = ce
                    colours.index_playing = ce
                    colours.time_text = ce
                    colours.bar_time = ce
                    colours.folder_title = ce
                    colours.star_line = ce #[150, 150, 150, 255]
                    colours.row_select_highlight = [255, 255, 255, 12]
                    colours.row_playing_highlight = [255, 255, 255, 8]

                gui.temp_themes[pctl.master_library[index].album] = copy.deepcopy(colours)
                gui.theme_temp_current = index

            wop = rw_from_object(g)
            s_image = IMG_Load_RW(wop, 0)
            # print(IMG_GetError())
            c = SDL_CreateTextureFromSurface(renderer, s_image)

            tex_w = pointer(c_int(0))
            tex_h = pointer(c_int(0))

            SDL_QueryTexture(c, None, None, tex_w, tex_h)

            dst = SDL_Rect(location[0], location[1])
            dst.w = int(tex_w.contents.value)
            dst.h = int(tex_h.contents.value)

            # Clean uo
            SDL_FreeSurface(s_image)
            g.close()
            source_image.close()

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

            if len(self.image_cache) > 10:
                SDL_DestroyTexture(self.image_cache[0].texture)
                del self.image_cache[0]
            if prefs.colour_from_image and len(self.image_cache) > 2:
                SDL_DestroyTexture(self.image_cache[0].texture)
                del self.image_cache[0]

            # temp fix
            global move_on_title
            global playlist_hold
            global quick_drag
            quick_drag = False
            move_on_title = False
            playlist_hold = False


        except OSError as error:
            print("Image processing error: " + str(error))
            self.current_wu = None
            del self.source_cache[index][offset]
            return 1
        except:
            print("Image processing error")
            self.current_wu = None
            del self.source_cache[index][offset]
            return 1

        return 0

    def render(self, unit, location):

        rect = unit.rect

        rect.x = int((unit.request_size[0] - unit.actual_size[0]) / 2) + location[0]
        rect.y = int((unit.request_size[1] - unit.actual_size[1]) / 2) + location[1]

        SDL_RenderCopy(renderer, unit.texture, None, rect)

    def clear_cache(self):

        for unit in self.image_cache:
            SDL_DestroyTexture(unit.texture)

        self.image_cache = []
        self.source_cache = {}
        self.current_wu = None


album_art_gen = AlbumArt()


def trunc_line(line, font, px, dots=True):

    if draw.text_calc(line, font) < px + 10:
        return line

    if dots:
        while draw.text_calc(line.rstrip(" ") + gui.trunk_end, font) > px:
            if len(line) == 0:
                return gui.trunk_end
            line = line[:-1]
        return line.rstrip(" ") + gui.trunk_end

    else:
        while draw.text_calc(line, font) > px:
            # trunk = True
            line = line[:-1]
            if len(line) < 2:
                break
        # if trunk and dots:
        #     line = line.rstrip(" ") + gui.trunk_end
        return line

def right_trunc(line, font, px, dots=True):

    if draw.text_calc(line, font) < px + 10:
        return line

    if dots:
        while draw.text_calc(line.rstrip(" ") + gui.trunk_end, font) > px:
            if len(line) == 0:
                return gui.trunk_end
            line = line[1:]
        return gui.trunk_end + line.rstrip(" ")

    else:
        while draw.text_calc(line, font) > px:
            # trunk = True
            line = line[1:]
            if len(line) < 2:
                break
        # if trunk and dots:
        #     line = line.rstrip(" ") + gui.trunk_end
        return line

def trunc_line2(line, font, px):
    trunk = False
    p = draw.text_calc(line, font)
    if p == 0 or p < px + 15:
        return line

    tl = line[0:(int(px / p * len(line)) + 3)]

    if draw.text_calc(line.rstrip(" ") + gui.trunk_end, font) > px:
        line = tl

    while draw.text_calc(line.rstrip(" ") + gui.trunk_end, font) > px + 10:
        trunk = True
        line = line[:-1]
        if len(line) < 1:
            break

    return line.rstrip(" ") + gui.trunk_end



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

        if enc_field == 'All' or enc_field == 'Artist':
            line = pctl.master_library[todo[q]].artist
            line = line.encode("Latin-1", 'ignore')
            line = line.decode(enc, 'ignore')
            pctl.master_library[todo[q]].artist = line

        if enc_field == 'All' or enc_field == 'Album':
            line = pctl.master_library[todo[q]].album
            line = line.encode("Latin-1", 'ignore')
            line = line.decode(enc, 'ignore')
            pctl.master_library[todo[q]].album = line

        if enc_field == 'All' or enc_field == 'Title':
            line = pctl.master_library[todo[q]].title
            line = line.encode("Latin-1", 'ignore')
            line = line.decode(enc, 'ignore')
            pctl.master_library[todo[q]].title = line

        if old_star != None:
            star_store.insert(todo[q], old_star)

        # if key in pctl.star_library:
        #     newkey = pctl.master_library[todo[q]].title + pctl.master_library[todo[q]].filename
        #     if newkey not in pctl.star_library:
        #         pctl.star_library[newkey] = copy.deepcopy(pctl.star_library[key])
        #         # del pctl.star_library[key]


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

    pctl.multi_playlist[to][2] += todo


def prep_gal():
    global albums
    albums = []

    folder = ""

    for index in default_playlist:

        if folder != pctl.master_library[index].parent_folder_name:
            albums.append([index, 0])
            folder = pctl.master_library[index].parent_folder_name


def load_xspf(path):
    global master_count
    global to_got

    name = os.path.basename(path)[:-5]
    try:
        parser = ET.XMLParser(encoding="utf-8")
        e = ET.parse(path, parser).getroot()

        a = []

        b = {}
        if 'track' in e[0][0].tag:
            for track in e[0]:
                for item in track:
                    if 'title' in item.tag:
                        b['title'] = item.text
                    if 'location' in item.tag:
                        b['location'] = item.text
                    if 'creator' in item.tag:
                        b['artist'] = item.text
                    if 'album' in item.tag:
                        b['album'] = item.text
                    if 'duration' in item.tag:
                        b['duration'] = item.text

                a.append(copy.deepcopy(b))
                b = {}
                #         print(b)
                # print(a)

    except:
        show_message("Error importing XSPF playlist.", 'warning', "Sorry about that.")
        return

    playlist = []
    missing = 0

    if len(a) > 5000:
        to_got = 'xspfl'

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
        # First checking for a full filepath match
        # if 'location' in track and 'file:///' in track['location']:
        #     location = track['location'][8:]
        #     for key, value in pctl.master_library.items():
        #         if value.fullpath == location:
        #             if os.path.isfile(value.fullpath):
        #                 playlist.append(key)
        #                 found = True
        #                 break
        #     if found is True:
        #         continue
        if 'location' in track and 'file:///' == track['location'][:8]:

            location = track['location'][8:]
            if location in location_dict:
                playlist.append(location_dict[location])
                found = True

            if found is True:
                continue

        # Then check for title, artist, album metadata and filename match
        if 'location' in track and 'duration' in track and 'title' in track and 'artist' in track and 'album' in track:
            base = os.path.basename(track['location'])
            if base in base_names:
                for index, bn in r_base_names.items():
                    va = pctl.master_library[index]
                    if va.artist == track['artist'] and va.title == track['title'] and \
                                    va.album == track['album'] and os.path.isfile(va.fullpath) and \
                                    va.filename == base:
                        playlist.append(index)
                        found = True
                        break
                if found is True:
                    continue

        # Then check for title, artist and album metadata match
        if 'title' in track and 'artist' in track and 'album' in track and track['title'] in titles:
            for key, value in pctl.master_library.items():
                if value.artist == track['artist'] and value.title == track['title'] and \
                                value.album == track['album'] and os.path.isfile(value.fullpath):
                    playlist.append(key)
                    found = True
                    break
            if found is True:
                continue

        # Then check for just title and artist match
        if 'title' in track and 'artist' in track and track['title'] in titles:
            for key, value in pctl.master_library.items():
                if value.artist == track['artist'] and value.title == track['title'] and os.path.isfile(value.fullpath):
                    playlist.append(key)
                    found = True
                    break
            if found is True:
                continue

        # As a last resort for a live track, match a duration to within 1 second and file name
        if 'duration' in track and 'location' in track:
            base = os.path.basename(track['location'])
            for key, value in pctl.master_library.items():
                if value.filename == base:
                    if track['duration'].isdigit() and os.path.isfile(value.fullpath):
                        if abs(int(int(track['duration']) / 1000) - value.length) < 2:
                            playlist.append(key)
                            found = True
                            break
            if found is True:
                continue

        if ('location' in track and 'file:///' in track['location']) or 'title' in track:
            nt = TrackClass()
            nt.index = master_count
            nt.found = False

            if 'location' in track and 'file:///' in track['location']:
                location = track['location'][8:]
                nt.fullpath = location.replace('\\', '/')
                nt.filename = os.path.basename(location)
                nt.parent_folder_path = os.path.dirname(location.replace('\\', '/'))
                nt.parent_folder_name = os.path.splitext(os.path.basename(nt.parent_folder_path))[0]
                nt.file_ext = os.path.splitext(os.path.basename(location))[1][1:].upper()
                if os.path.isfile(location):
                    nt.found = True
                    missing -= 1
            elif 'album' in track:
                nt.parent_folder_name = track['album']
            if 'artist' in track:
                nt.artist = track['artist']
            if 'title' in track:
                nt.title = track['title']
            if 'duration' in track:
                nt.length = int(int(track['duration']) / 1000)
            if 'album' in track:
                nt.album = track['album']
            nt.is_cue = False
            if nt.found is True:
                nt = tag_scan(nt)

            pctl.master_library[master_count] = nt
            playlist.append(master_count)
            master_count += 1

        missing += 1

    if missing > 0:
        show_message('Failed to locate ' + str(missing) + ' out of ' + str(len(a)) + ' tracks.')
    # pctl.multi_playlist.append([name, 0, playlist, 0, 0, 0])
    pctl.multi_playlist.append(pl_gen(title=name,
                                      playlist=playlist))
    gui.update = 1


# gui.panelY = 30
# gui.panelBY = 51

bb_type = 0

# gui.scroll_hide_box = (0, gui.panelY, 28, window_size[1] - gui.panelBY - gui.panelY)

encoding_menu = False
enc_index = 0
enc_setting = 0
enc_field = 'All'

gen_menu = False

transfer_setting = 0

b_panel_size = 300
b_info_bar = False

class LoadImageAsset:
    def __init__(self, local_path):
        raw_image = IMG_Load(b_active_directory + local_path.encode('utf-8'))
        self.sdl_texture = SDL_CreateTextureFromSurface(renderer, raw_image)
        p_w = pointer(c_int(0))
        p_h = pointer(c_int(0))
        SDL_QueryTexture(self.sdl_texture, None, None, p_w, p_h)
        self.rect = SDL_Rect(0, 0, p_w.contents.value, p_h.contents.value)
        self.w = p_w.contents.value
        self.h = p_h.contents.value

    def render(self, x, y, colour=None):
        self.rect.x = x
        self.rect.y = y
        SDL_RenderCopy(renderer, self.sdl_texture, None, self.rect)

class WhiteModImageAsset:
    def __init__(self, local_path):
        raw_image = IMG_Load(b_active_directory + local_path.encode('utf-8'))
        self.sdl_texture = SDL_CreateTextureFromSurface(renderer, raw_image)
        self.colour = [255, 255, 255, 255]
        p_w = pointer(c_int(0))
        p_h = pointer(c_int(0))
        SDL_QueryTexture(self.sdl_texture, None, None, p_w, p_h)
        self.rect = SDL_Rect(0, 0, p_w.contents.value, p_h.contents.value)
        SDL_FreeSurface(raw_image)
        self.w = p_w.contents.value
        self.h = p_h.contents.value

    def render(self, x, y, colour):
        if colour != self.colour:
            SDL_SetTextureColorMod(self.sdl_texture, colour[0], colour[1], colour[2])
            self.colour = colour
        self.rect.x = x
        self.rect.y = y
        SDL_RenderCopy(renderer, self.sdl_texture, None, self.rect)


if gui.scale == 2:
    message_info_icon = LoadImageAsset("/gui/2x/notice.png")
    message_warning_icon = LoadImageAsset("/gui/2x/warning.png")
    message_tick_icon = LoadImageAsset("/gui/2x/done.png")
    message_arrow_icon = LoadImageAsset("/gui/2x/ext.png")
else:
    message_info_icon = LoadImageAsset("/gui/notice.png")
    message_warning_icon = LoadImageAsset("/gui/warning.png")
    message_tick_icon = LoadImageAsset("/gui/done.png")
    message_arrow_icon = LoadImageAsset("/gui/ext.png")


class ToolTip:

    def __init__(self):
        self.text = ""
        self.h = 21 * gui.scale
        self.w = 62 * gui.scale
        self.x = 0
        self.y = 0
        self.timer = Timer()
        self.trigger = 1.1
        self.font = 13
        self.called = False
        self.a = False

        self.ox = 0


    def test(self, x, y, text):

        if self.text != text:
            self.text = text
            #self.timer.set()
            self.a = False

            self.x = x
            self.y = y
            self.w = draw.text_calc(text, self.font) + 10

        self.called = True

        if self.a is False:
            self.timer.set()
            gui.frame_callback_list.append(TestTimer(self.trigger))
        self.a = True

    def render(self):

        if self.called is True:

            if self.timer.get() > self.trigger:

                draw.rect_r((self.x, self.y, self.w, self.h), colours.menu_background, True)
                draw.rect_r((self.x, self.y, self.w, self.h), colours.grey(50))
                draw_text((self.x + int(self.w / 2), self.y, 2), self.text, colours.grey(220), self.font)
            else:
                #gui.update += 1
                pass
        else:
            self.timer.set()
            self.a = False

        self.called = False

tool_tip = ToolTip()


# Right click context menu generator

class MenuIcon:

    def __init__(self, asset):

        self.asset = asset
        self.colour = [170, 170, 170, 255]
        self.base_asset = None
        self.colour_callback = None
        self.xoff = 0
        self.yoff = 0


class Menu:
    switch = 0
    count = switch + 1
    instances = []

    def __init__(self, width, show_icons=False):

        self.active = False
        self.clicked = False
        self.pos = [0, 0]
        self.vertical_size = 22 * gui.scale#20
        self.h = self.vertical_size
        self.w = width * gui.scale
        if gui.scale == 2:
            self.w += 15
        self.reference = 0
        self.items = []
        self.subs = []
        self.selected = -1
        self.up = False
        self.down = False
        self.font = 412
        self.show_icons = show_icons
        self.sub_arrow = MenuIcon(WhiteModImageAsset("/gui/sub.png"))

        self.id = Menu.count
        self.break_height = 4 * gui.scale
        Menu.count += 1

        self.sub_number = 0
        self.sub_active = -1
        Menu.instances.append(self)

    @staticmethod
    def deco():
        return [colours.menu_text, colours.menu_background, None]

    def click(self):
        self.clicked = True
        # cheap hack to prevent scroll bar from being activated when closing menu
        global click_location
        click_location = [0, 0]

    def add(self, title, func, render_func=None, no_exit=False, pass_ref=False, hint=None, icon=None, show_test=None):
        if render_func is None:
            render_func = self.deco
        self.items.append([title, False, func, render_func, no_exit, pass_ref, hint, icon, show_test])

    def br(self):
        self.items.append(None)

    def add_sub(self, title, width):
        self.items.append([title, True, self.sub_number, self.deco, width * gui.scale])
        self.sub_number += 1
        self.subs.append([])

    def add_to_sub(self, title, sub, func, render_func=None, no_exit=False, pass_ref=False, args=None):
        if render_func is None:
            render_func = self.deco
        item = [title, False, func, render_func, no_exit, pass_ref, args]
        self.subs[sub].append(item)

    def test_item_active(self, item):

        if item[1] is False and item[8] is not None:
            if item[8](1) is False:
                return False
        return True

    def render(self):
        if self.active:

            if Menu.switch != self.id:
                self.active = False
                return

            ytoff = 3
            y_run = self.pos[1]
            to_call = None

            if window_size[1] < 250 * gui.scale:
                self.h = 14 * gui.scale
                ytoff = -1 * gui.scale
            else:
                self.h = self.vertical_size

            for i in range(len(self.items)):
                if self.items[i] is None:

                    draw.rect((self.pos[0], y_run), (self.w, self.break_height),
                              colours.menu_background, True)
                    draw.rect((self.pos[0], y_run + 2 * gui.scale), (self.w, 2 * gui.scale),
                              [255, 255, 255, 13], True)
                    # Draw tab
                    draw.rect((self.pos[0], y_run), (4 * gui.scale, self.break_height),
                              colours.grey(30), True)
                    y_run += self.break_height
                    continue

                if self.test_item_active(self.items[i]) is False:
                    continue
                # if self.items[i][1] is False and self.items[i][8] is not None:
                #     if self.items[i][8](1) == False:
                #         continue

                # Get properties for menu item
                fx = self.items[i][3]()
                if fx[2] is not None:
                    label = fx[2]
                else:
                    label = self.items[i][0]

                # Draw item background, black by default
                draw.rect((self.pos[0], y_run), (self.w, self.h),
                          fx[1], True)
                bg = fx[1]

                # Detect if mouse is over this item
                selected = False
                rect = (self.pos[0], y_run, self.w, self.h - 1)
                fields.add(rect)

                if coll_point(mouse_position,
                              (self.pos[0], y_run, self.w, self.h - 1)):
                    draw.rect((self.pos[0], y_run), (self.w, self.h),
                              colours.menu_highlight_background,
                              True)  # [15, 15, 15, 255]
                    selected = True
                    bg = alpha_blend(colours.menu_highlight_background, bg)

                    # Call menu items callback if clicked
                    if self.clicked:

                        if self.items[i][1] is False:
                            to_call = i

                        else:
                            self.clicked = False
                            self.sub_active = self.items[i][2]

                # Draw tab
                draw.rect((self.pos[0], y_run), (4 * gui.scale, self.h),
                          colours.grey(30), True)

                # Draw Icon
                x = 12 * gui.scale
                if self.items[i][1] is False and self.show_icons:

                    icon = self.items[i][7]
                    if icon is not None:
                        if icon.base_asset is None:
                            # Colourise mode

                            colour = [50, 50, 50, 255]

                            if icon.colour_callback is not None and icon.colour_callback() is not None:
                                colour = icon.colour_callback()

                            elif selected:
                                colour = icon.colour

                            icon.asset.render(self.pos[0] + x + icon.xoff * gui.scale, y_run + 5 * gui.scale + icon.yoff * gui.scale, colour)

                        else:
                            # Pre-rendered mode
                            if selected:
                                icon.asset.render(self.pos[0] + x + icon.xoff * gui.scale, y_run + 5 * gui.scale + icon.yoff * gui.scale)
                            else:
                                icon.base_asset.render(self.pos[0] + x + icon.xoff * gui.scale, y_run + 5 * gui.scale + icon.yoff * gui.scale)

                if self.show_icons:
                    x += 25 * gui.scale

                # Draw arrow icon for sub menu
                if self.items[i][1] is True:
                    colour = [50, 50, 50, 255]
                    if selected:
                        colour = [150, 150, 150, 255]
                    if self.sub_active == self.items[i][2]:
                        colour = [150, 150, 150, 255]
                    self.sub_arrow.asset.render(self.pos[0] + self.w - 13, y_run + 7, colour)

                # Render the items label
                draw_text((self.pos[0] + x, y_run + ytoff), label, fx[0], self.font, bg=bg)

                # Render the items hint
                if len(self.items[i]) > 6 and self.items[i][6] != None:
                    colo = alpha_blend([255, 255, 255, 50], bg)
                    draw_text((self.pos[0] + self.w - 5, y_run + ytoff, 1), self.items[i][6],
                              colo, self.font, bg=bg)

                y_run += self.h
                # Render sub menu if active
                if self.sub_active > -1 and self.items[i][1] and self.sub_active == self.items[i][2]:

                    # sub_pos = [self.pos[0] + self.w, self.pos[1] + i * self.h]
                    sub_pos = [self.pos[0] + self.w, self.pos[1]]
                    sub_w = self.items[i][4]
                    fx = self.deco()

                    for w in range(len(self.subs[self.sub_active])):

                        # Item background
                        fx = self.subs[self.sub_active][w][3]()
                        draw.rect((sub_pos[0], sub_pos[1] + w * self.h), (sub_w, self.h), fx[1], True)

                        # Detect if mouse is over this item
                        rect = (sub_pos[0], sub_pos[1] + w * self.h, sub_w, self.h - 1)
                        fields.add(rect)
                        bg = colours.menu_background
                        if coll_point(mouse_position,
                                      (sub_pos[0], sub_pos[1] + w * self.h, sub_w, self.h - 1)):
                            draw.rect((sub_pos[0], sub_pos[1] + w * self.h), (sub_w, self.h),
                                      colours.menu_highlight_background,
                                      True)
                            bg = alpha_blend(colours.menu_highlight_background, bg)

                            # Call Callback
                            if self.clicked:

                                # If callback needs args
                                if self.subs[self.sub_active][w][6] is not None:
                                    self.subs[self.sub_active][w][2](self.reference, self.subs[self.sub_active][w][6])

                                # If callback just need ref
                                elif self.subs[self.sub_active][w][5]:
                                    self.subs[self.sub_active][w][2](self.reference)

                                else:
                                    self.subs[self.sub_active][w][2]()

                        # Get properties for menu item
                        fx = self.subs[self.sub_active][w][3]()
                        if fx[2] is not None:
                            label = fx[2]
                        else:
                            label = self.subs[self.sub_active][w][0]

                        # Render the items label
                        draw_text((sub_pos[0] + 8, sub_pos[1] + 2 + w * self.h), label, fx[0],
                                  self.font, bg=bg)

                        # Render the menu outline
                        # draw.rect(sub_pos, (sub_w, self.h * len(self.subs[self.sub_active])), colours.grey(40))


            # Process Click Actions
            if to_call is not None:

                if self.items[to_call][5]:
                    self.items[to_call][2](self.reference)
                else:
                    self.items[to_call][2]()


            if self.clicked or key_esc_press:
                self.active = False
                self.clicked = False


                # Render the menu outline
                # draw.rect(self.pos, (self.w, self.h * len(self.items)), colours.grey(40))

    def activate(self, in_reference=0, position=None):

        if position != None:
            self.pos = [position[0], position[1]]
        else:
            self.pos = [copy.deepcopy(mouse_position[0]), copy.deepcopy(mouse_position[1])]

        self.reference = in_reference
        Menu.switch = self.id
        self.sub_active = -1

        # Reposition the menu if it would otherwise intersect with window border
        if self.pos[0] + self.w > window_size[0]:
            self.pos[0] = self.pos[0] - self.w - 3 * gui.scale
        if self.pos[1] + len(self.items) * self.h > window_size[1]:
            #self.pos[1] -= len(self.items) * self.h
            self.pos[0] += 3 * gui.scale
            for i in range(len(self.items)):
                if self.items[i] is None:
                    self.pos[1] -= self.break_height
                elif self.test_item_active(self.items[i]) is False:
                    pass
                else:
                    self.pos[1] -= self.h
            if self.pos[1] < 30 * gui.scale:
                self.pos[1] = 30 * gui.scale
                self.pos[0] += 5 * gui.scale
        self.active = True


# Create empty area menu
playlist_menu = Menu(130)
showcase_menu = Menu(125)
cancel_menu = Menu(100)


def cancel_import():

    if transcode_list:
        del transcode_list[1:]
        gui.tc_cancel = True
    if loading_in_progress:
        gui.im_cancel = True


cancel_menu.add("Cancel", cancel_import)

def get_lyric_wiki(track_object):

    if track_object.artist == "" or track_object.title == "":
        show_message("Insufficient metadata to get lyrics", 'warning')

    print("Query Lyric Wiki...")
    try:
        track_object.lyrics = PyLyrics.getLyrics(track_object.artist, track_object.title)
    except:
        show_message("LyricWiki does not appear to have lyrics for this song")

    print("..Done")


def get_bio(track_object):

    if track_object.artist != "":
        lastfm.get_bio(track_object.artist)

showcase_menu.add('Search LyricWiki', get_lyric_wiki, pass_ref=True)


def paste_lyrics_deco():

    if SDL_HasClipboardText():
        line_colour = colours.menu_text
    else:
        line_colour = colours.menu_text_disabled

    return [line_colour, colours.menu_background, None]

def paste_lyrics(track_object):

    if SDL_HasClipboardText():
        clip = SDL_GetClipboardText()
        #print(clip)
        track_object.lyrics = clip.decode('utf-8')

    else:
        print('NO TEXT TO PASTE')

showcase_menu.add('Paste Lyrics', paste_lyrics, paste_lyrics_deco, pass_ref=True)


def copy_lyrics_deco():

    if gui.force_showcase_index >= 0:
        index = gui.force_showcase_index
        track = pctl.master_library[index]
    else:
        index = pctl.track_queue[pctl.queue_step]
        track = pctl.master_library[pctl.track_queue[pctl.queue_step]]

    if len(track.lyrics) > 0:
        line_colour = colours.menu_text
    else:
        line_colour = colours.menu_text_disabled

    return [line_colour, colours.menu_background, None]

def copy_lyrics(track_object):
    copy_to_clipboard(track_object.lyrics)

showcase_menu.add('Copy Lyrics', copy_lyrics, copy_lyrics_deco, pass_ref=True)



def clear_lyrics(track_object):
    track_object.lyrics = ""

def clear_lyrics_deco():

    if gui.force_showcase_index >= 0:
        index = gui.force_showcase_index
        track = pctl.master_library[index]
    else:
        index = pctl.track_queue[pctl.queue_step]
        track = pctl.master_library[pctl.track_queue[pctl.queue_step]]


    if track.lyrics != "":
        line_colour = colours.menu_text
    else:
        line_colour = colours.menu_text_disabled

    return [line_colour, colours.menu_background, None]

def split_lyrics(track_object):


    if track_object.lyrics != "":
        track_object.lyrics = track_object.lyrics.replace(". ", ". \n")
    else:
        pass


showcase_menu.add('Clear Lyrics', clear_lyrics, clear_lyrics_deco, pass_ref=True)
showcase_menu.add('Split Lines', split_lyrics, clear_lyrics_deco, pass_ref=True)


def save_embed_img():
    index = pctl.track_queue[pctl.queue_step]
    filepath = pctl.master_library[index].fullpath
    folder = pctl.master_library[index].parent_folder_path

    try:
        if '.mp3' in filepath or '.MP3' in filepath:
            tag = stagger.read_tag(filepath)
            try:
                tt = tag[APIC][0]
            except:
                try:
                    tt = tag[PIC][0]
                except:
                    show_message("Image save error.", 'warning', "No embedded album art found in MP3 file")
                    return
            pic = tt.data

        elif '.flac' in filepath.lower() or '.ape' in filepath.lower() or '.tta' in filepath.lower() or '.wv' in filepath.lower():

            tt = Flac(filepath)
            tt.read(True)
            if tt.has_picture is False:
                show_message("Image save error.", 'warning', "No embedded album art found in FLAC file")
                return
            pic = tt.picture

        source_image = io.BytesIO(pic)
        im = Image.open(source_image)
        print(im.format)
        # im.format
        source_image.close()

        ext = "." + im.format.lower()
        if im.format == "JPEG":
            ext = ".jpg"

        target = os.path.join(folder, "embed-" + str(im.height) + "px-" + str(index) + ext)
        if len(pic) > 30:
            with open(target, 'wb') as w:
                w.write(pic)
        open_folder(index)


    except:
        show_message("Image save error.", "warning", "A mysterious error occurred")

picture_menu = Menu(160)

def open_image_deco():

    info = album_art_gen.get_info(pctl.track_queue[pctl.queue_step])

    if info is None:
        return [colours.menu_text_disabled, colours.menu_background, None]

    if pctl.playing_state > 0 and info[0] is False:
        line_colour = colours.menu_text
    else:
        line_colour = colours.menu_text_disabled

    return [line_colour, colours.menu_background, None]

def open_image():

    if pctl.playing_state > 0 and pctl.track_queue:
        album_art_gen.open_external(pctl.track_queue[pctl.queue_step])

def extract_image_deco():

    info = album_art_gen.get_info(pctl.track_queue[pctl.queue_step])

    if info is None:
        return [colours.menu_text_disabled, colours.menu_background, None]

    if pctl.playing_state > 0 and info[0] is True:
        line_colour = colours.menu_text
    else:
        line_colour = colours.menu_text_disabled

    return [line_colour, colours.menu_background, None]


picture_menu.add("Open Image", open_image, open_image_deco)


def cycle_image_deco():

    info = album_art_gen.get_info(pctl.track_queue[pctl.queue_step])

    if pctl.playing_state != 0 and (info is not None and info[1] > 1):
        line_colour = colours.menu_text
    else:
        line_colour = colours.menu_text_disabled

    return [line_colour, colours.menu_background, None]


def cycle_offset():
    album_art_gen.cycle_offset(pctl.track_queue[pctl.queue_step])


def cycle_offset_b():
    album_art_gen.cycle_offset_reverse(pctl.track_queue[pctl.queue_step])


picture_menu.add("Next", cycle_offset, cycle_image_deco)
picture_menu.add("Previous", cycle_offset_b, cycle_image_deco)


picture_menu.add('Extract Image', save_embed_img, extract_image_deco)


def remove_embed_deco():
    info = album_art_gen.get_info(pctl.track_queue[pctl.queue_step])

    if info is None:
        return [colours.menu_text_disabled, colours.menu_background, None]

    if pctl.playing_state > 0 and info[0] is True and pctl.playing_object().file_ext == "MP3":
        line_colour = colours.menu_text
    else:
        line_colour = colours.menu_text_disabled

    return [line_colour, colours.menu_background, None]


def remove_embed_picture(index):
    tracks = get_like_folder(index)
    removed = 0
    pr = pctl.stop(True)
    for item in tracks:
        if "MP3" == pctl.master_library[item].file_ext:
            tag = stagger.read_tag(pctl.master_library[item].fullpath)
            remove = False
            try:
                del tag[APIC]
                print("Delete APIC successful")
                remove = True
            except:
                print("No APIC found")

            try:
                del tag[PIC]
                print("Delete PIC successful")
                remove = True
            except:
                print("No PIC found")

            if remove is True:
                tag.write()
                removed += 1

    if removed == 0:
        show_message("Image removal failed.", "warning")
        return
    elif removed == 1:
        show_message("Deleted embedded picture from file", 'done')
    else:
        show_message("Deleted embedded picture from " + str(removed) + " files", 'done')

    if pr == 1:
        pctl.revert()
    clear_img_cache()


picture_menu.add('Folder Purge Embedded', remove_embed_picture, remove_embed_deco, pass_ref=True)

def append_here():
    global cargo
    global default_playlist
    default_playlist += cargo


def paste_deco():
    line = "Paste"
    if len(cargo) > 0:
        line_colour = colours.menu_text
    else:
        line_colour = colours.menu_text_disabled

    if gui.lightning_copy:
        if key_shift_down:
            line = "Move to This Library"
        else:
            line = "Copy to This Library"

    return [line_colour, colours.menu_background, line]

def copy_deco():
    line = "Copy"

    if key_shift_down:
        line = "Copy Folder From Library"
    else:
        line = "Copy"


    return [colours.menu_text, colours.menu_background, line]


#playlist_menu.add('Paste', append_here, paste_deco)

def parse_template(string, track_object, up_ext=False):
    set = 0
    underscore = False
    output = ""

    while set < len(string):
        if string[set] == "%" and set < len(string) - 1:
            set += 1
            if string[set] == 'n':
                if len(str(track_object.track_number)) < 2:
                    output += "0"
                output += str(track_object.track_number)
            elif string[set] == 'a':
                if up_ext and track_object.album_artist != "": # Context of renaming a folder
                    output += track_object.album_artist
                else:
                    output += track_object.artist
            elif string[set] == 't':
                output += track_object.title
            elif string[set] == 'd':
                output += track_object.date
            elif string[set] == 'b':
                output += track_object.album
            elif string[set] == 'x':
                if up_ext:
                    output += track_object.file_ext.upper()
                else:
                    output += "." + track_object.file_ext.lower()
            elif string[set] == 'u':
                underscore = True
        else:
            output += string[set]
        set += 1

    output = output.rstrip(" -").lstrip(" -")

    if underscore:
        output = output.replace(' ', "_")

    # Attempt to ensure the output text is filename safe
    for char in output:
        if char in '\\/:*?"<>|':
            output = output.replace(char, '')

    return output

# Create playlist tab menu
tab_menu = Menu(160, show_icons=True)


def rename_playlist(index):
    global rename_playlist_box
    global rename_index

    rename_playlist_box = True
    rename_index = index
    rename_text_area.set_text(pctl.multi_playlist[index][0])


tab_menu.add('Rename', rename_playlist, pass_ref=True, hint="Ctrl+R")


def export_xspf(pl):
    if len(pctl.multi_playlist[pl][2]) < 1:
        show_message("There are no tracks in this playlist. Nothing to export")
        return

    direc = os.path.join(user_directory, 'playlists')
    if not os.path.exists(direc):
        os.makedirs(direc)
    target = os.path.join(direc, pctl.multi_playlist[pl][0] + '.xspf')

    xport = open(target, 'w', encoding='utf-8')
    xport.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    xport.write('<playlist version="1" xmlns="http://xspf.org/ns/0/">\n')
    xport.write('  <trackList>\n')

    for number in pctl.multi_playlist[pl][2]:
        track = pctl.master_library[number]
        xport.write('    <track>\n')
        if track.title != "":
            xport.write('      <title>' + escape(track.title) + '</title>\n')
        if track.is_cue is False and track.fullpath != "":
            xport.write('      <location>file:///' + escape(track.fullpath) + '</location>\n')
        if track.artist != "":
            xport.write('      <creator>' + escape(track.artist) + '</creator>\n')
        if track.album != "":
            xport.write('      <album>' + escape(track.album) + '</album>\n')
        xport.write('      <duration>' + str(track.length * 1000) + '</duration>\n')
        xport.write('    </track>\n')
    xport.write('  </trackList>\n')
    xport.write('</playlist>\n\n')
    xport.close()

    if system == 'windows':
        line = r'explorer /select,"%s"' % (
            target.replace("/", "\\"))
        subprocess.Popen(line)
    else:
        line = direc
        line += "/"
        if system == 'mac':
            subprocess.Popen(['open', line])
        else:
            subprocess.Popen(['xdg-open', line])


# tab_menu.add('Export XSPF', export_xspf, pass_ref=True)

def reload():
    if album_mode:
        reload_albums(quiet=True)
    elif gui.combo_mode:
        reload_albums(quiet=True)
        combo_pl_render.prep()


def clear_playlist(index):
    global default_playlist

    pctl.playlist_backup = copy.deepcopy(pctl.multi_playlist[index])

    del pctl.multi_playlist[index][2][:]
    if pctl.playlist_active == index:
        default_playlist = pctl.multi_playlist[index][2]
        reload()

    # pctl.playlist_playing = 0
    pctl.multi_playlist[index][3] = 0

    gui.pl_update = 1


def convert_playlist(pl):
    global transcode_list

    if system == 'windows':
        if not os.path.isfile(user_directory + '/encoder/ffmpeg.exe'):
            show_message("Error: Missing ffmpeg.exe from '/encoder' directory")
            return
        # if prefs.transcode_codec == 'ogg' and not os.path.isfile(install_directory + '/encoder/oggenc2.exe'):
        #     show_message("Error: Missing oggenc2.exe from '/encoder' directory")
        #     return
        if prefs.transcode_codec == 'mp3' and not os.path.isfile(user_directory + '/encoder/lame.exe'):
            show_message("Error: Missing lame.exe from '/encoder' directory")
            return
    else:
        if shutil.which('ffmpeg') is None:
            show_message("Error: ffmpeg does not appear to be installed")
            return
        if prefs.transcode_codec == 'mp3' and shutil.which('lame') is None:
            show_message("Error: LAME does not appear to be installed")
            return

    paths = []

    for track in pctl.multi_playlist[pl][2]:
        if pctl.master_library[track].parent_folder_path not in paths:
            paths.append(pctl.master_library[track].parent_folder_path)

    for path in paths:
        folder = []
        for track in pctl.multi_playlist[pl][2]:
            if pctl.master_library[track].parent_folder_path == path:
                folder.append(track)
                if prefs.transcode_codec == 'flac' and pctl.master_library[track].file_ext.lower() in ('mp3', 'opus',
                                                                                                       'm4a', 'mp4',
                                                                                                     'ogg', 'aac'):
                    show_message("This includes the conversion of a lossy codec to a lossless one!")

        transcode_list.append(folder)
        print(1)
        print(transcode_list)


def get_folder_tracks_local(pl_in):
    selection = []
    parent = os.path.normpath(pctl.master_library[default_playlist[pl_in]].parent_folder_path)
    while pl_in < len(default_playlist) and parent == os.path.normpath(pctl.master_library[default_playlist[pl_in]].parent_folder_path):
        selection.append(pl_in)
        pl_in += 1
    return selection


tab_menu.add('Clear', clear_playlist, pass_ref=True)


def move_playlist(source, dest):
    global default_playlist
    if dest > source:
        dest += 1

    active = pctl.multi_playlist[pctl.active_playlist_playing]
    view = pctl.multi_playlist[pctl.playlist_active]

    temp = pctl.multi_playlist[source]
    pctl.multi_playlist[source] = "old"
    pctl.multi_playlist.insert(dest, temp)
    pctl.multi_playlist.remove("old")

    pctl.active_playlist_playing = pctl.multi_playlist.index(active)
    pctl.playlist_active = pctl.multi_playlist.index(view)
    default_playlist = default_playlist = pctl.multi_playlist[pctl.playlist_active][2]


def delete_playlist(index):
    global default_playlist
    global playlist_position

    if rename_playlist_box:
        return

    gui.pl_update = 1
    gui.update += 1

    if len(pctl.multi_playlist) < 2:
        pctl.multi_playlist = []
        # pctl.multi_playlist.append(["Default", 0, [], 0, 0, 0])
        pctl.multi_playlist.append(pl_gen())
        print(pl_gen())
        print(pctl.multi_playlist)
        default_playlist = pctl.multi_playlist[0][2]
        return

    if index == pctl.playlist_active and len(pctl.multi_playlist) == 1:
        pctl.playlist_active = 0
        pctl.playlist_playing = 0
        default_playlist = []
        playlist_position = 0
    elif index == pctl.playlist_active and index > 0:
        pctl.playlist_active -= 1
        pctl.playlist_playing = pctl.multi_playlist[pctl.playlist_active][1]
        default_playlist = pctl.multi_playlist[pctl.playlist_active][2]
        playlist_position = pctl.multi_playlist[pctl.playlist_active][3]
    elif index < pctl.playlist_active and pctl.playlist_active > 0:
        pctl.playlist_active -= 1
    elif index == pctl.playlist_active == 0 and len(pctl.multi_playlist) > 1:
        pctl.playlist_playing = pctl.multi_playlist[pctl.playlist_active + 1][1]
        default_playlist = pctl.multi_playlist[pctl.playlist_active + 1][2]
        playlist_position = pctl.multi_playlist[pctl.playlist_active + 1][3]

    pctl.active_playlist_playing = pctl.playlist_active
    pctl.playlist_backup = pctl.multi_playlist[index]
    del pctl.multi_playlist[index]
    reload()


to_scan = []

def rescan_tags(pl):

    for track in pctl.multi_playlist[pl][2]:
        if pctl.master_library[track].is_cue is False:
            to_scan.append(track)
            # pctl.master_library[track] = tag_scan(pctl.master_library[track])

def re_import(pl):

    path = pctl.multi_playlist[pl][7]
    if path == "":
        return
    for i in reversed(range(len(pctl.multi_playlist[pl][2]))):
        if path.replace('\\', '/') in pctl.master_library[pctl.multi_playlist[pl][2][i]].parent_folder_path:
            del pctl.multi_playlist[pl][2][i]
    load_order = LoadClass()
    load_order.target = path
    load_order.playlist = pctl.multi_playlist[pl][6]
    load_orders.append(copy.deepcopy(load_order))


def s_append(index):
    paste(playlist=index)


def append_playlist(index):

    global cargo
    pctl.multi_playlist[index][2] += cargo

    gui.pl_update = 1
    reload()


def tryint(s):
    try:
        return int(s)
    except:
        return s

def index_key(index):
    s = str(pctl.master_library[index].track_number)
    #print(pctl.master_library[index].disc_number)
    if pctl.master_library[index].disc_number != "":
        if pctl.master_library[index].disc_number != "0":
            s = str(pctl.master_library[index].disc_number) + "d" + s
    if s == "":
        s = pctl.master_library[index].filename
    try:
        return [tryint(c) for c in re.split('([0-9]+)', s)]
    except:
        return "a"

def sort_track_2(pl, custom_list=None):
    current_folder = ""
    albums = []
    if custom_list is None:
        playlist = pctl.multi_playlist[pl][2]
    else:
        playlist = custom_list

    for i in range(len(playlist)):
        if i == 0:
            albums.append(i)
            current_folder = pctl.master_library[playlist[i]].parent_folder_name
        else:
            if pctl.master_library[playlist[i]].parent_folder_name != current_folder:
                current_folder = pctl.master_library[playlist[i]].parent_folder_name
                albums.append(i)


    i = 0
    while i < len(albums) - 1:
        playlist[albums[i]:albums[i + 1]] = sorted(playlist[albums[i]:albums[i + 1]], key=index_key)
        i += 1
    if len(albums) > 0:
        playlist[albums[i]:] = sorted(playlist[albums[i]:], key=index_key)



def sort_path_pl(pl):

    def path(index):
        return pctl.master_library[index].fullpath

    pctl.multi_playlist[pl][2].sort(key=path)

def append_current_playing(index):
    if pctl.playing_state > 0 and len(pctl.track_queue) > 0:
        pctl.multi_playlist[index][2].append(pctl.track_queue[pctl.queue_step])
        gui.pl_update = 1


def export_stats(pl):
    playlist_time = 0
    play_time = 0
    for index in pctl.multi_playlist[pl][2]:
        playlist_time += int(pctl.master_library[index].length)
        # key = pctl.master_library[index].title + pctl.master_library[index].filename
        # if key in pctl.star_library:
        #     play_time += pctl.star_library[key]
        play_time += star_store.get(index)

    stats_gen.update(pl)
    line = 'Playlist: ' + pctl.multi_playlist[pl][0] + "\r\n"
    line += 'Generated: ' + time.strftime("%c") + "\r\n"
    line += '\r\nTracks in playlist: ' + str(len(pctl.multi_playlist[pl][2]))
    line += '\r\n\r\nTotal Duration: ' + str(datetime.timedelta(seconds=int(playlist_time)))
    line += '\r\nTotal Playtime: ' + str(datetime.timedelta(seconds=int(play_time)))

    line += "\r\n\r\n-------------- Top Artists --------------------\r\n\r\n"

    ls = stats_gen.artist_list
    for i, item in enumerate(ls[:50]):
        line += str(i + 1) + ".\t" + stt2(item[1]) + "\t" + item[0] + "\r\n"

    line += "\r\n\r\n-------------- Top Albums --------------------\r\n\r\n"
    ls = stats_gen.album_list
    for i, item in enumerate(ls[:50]):
        line += str(i + 1) + ".\t" + stt2(item[1]) + "\t" + item[0] + "\r\n"
    line += "\r\n\r\n-------------- Top Genres --------------------\r\n\r\n"
    ls = stats_gen.genre_list
    for i, item in enumerate(ls[:50]):
        line += str(i + 1) + ".\t" + stt2(item[1]) + "\t" + item[0] + "\r\n"

    line = line.encode('utf-8')
    xport = open(user_directory + '/stats.txt', 'wb')
    xport.write(line)
    xport.close()
    target = os.path.join(user_directory, "stats.txt")
    if system == "windows":
        os.startfile(target)
    elif system == 'mac':
        subprocess.call(['open', target])
    else:
        subprocess.call(["xdg-open", target])


# def folder_year_sort(pl):
#
#     playlist = pctl.multi_playlist[pl][2]
#
#     current_folder = ""
#     album = []
#
#     for item in playlist:
#
#         if current_folder != pctl.master_library[playlist[i]].parent_folder_name:
#             current_folder = pctl.master_library[playlist[i]].parent_folder_name
#
#             album = []
#
#     print("done")
#     print(top)



def standard_sort(pl):
    sort_path_pl(pl)
    sort_track_2(pl)



def year_s(plt):

    sorted_temp = sorted(plt, key=lambda x: x[1])
    temp = []

    for album in sorted_temp:
        temp += album[0]
    return temp


def year_sort(pl):

    playlist = pctl.multi_playlist[pl][2]
    plt = []
    pl2 = []
    artist = ""

    p = 0
    while p < len(playlist):
        if get_object(playlist[p]).artist != artist:
            artist = get_object(playlist[p]).artist
            pl2 += year_s(plt)
            plt = []

        if p > len(playlist) - 2:
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
        # print(album)

    # We can't just assign the playlist because it may disconnect the 'pointer' default_playlist
    pctl.multi_playlist[pl][2][:] = pl2[:]


if gui.scale == 2:
    delete_icon = MenuIcon(WhiteModImageAsset('/gui/2x/del.png'))
else:
    delete_icon = MenuIcon(WhiteModImageAsset('/gui/del.png'))

def pl_toggle_playlist_break(ref):
    pctl.multi_playlist[ref][4] ^= 1
    gui.pl_update = 1

delete_icon.xoff = 3
delete_icon.colour = [249, 70, 70, 255]

tab_menu.add('Delete', delete_playlist, pass_ref=True, hint="Ctrl+W", icon=delete_icon)

tab_menu.br()

tab_menu.add_sub("Generate / Sort...", 133)
tab_menu.add("Sort Filepath", standard_sort, pass_ref=True)
tab_menu.add("Sort Year per Artist", year_sort, pass_ref=True)

# tab_menu.add('Transcode All Folders', convert_playlist, pass_ref=True)
# tab_menu.add('Rescan Tags', rescan_tags, pass_ref=True)
# tab_menu.add('Re-Import Last Folder', re_import, pass_ref=True)
# tab_menu.add('Export XSPF', export_xspf, pass_ref=True)
tab_menu.br()
#tab_menu.add('Paste Tracks', append_playlist, paste_deco, pass_ref=True)
tab_menu.add('Paste', s_append, pass_ref=True)
tab_menu.add("Append Playing", append_current_playing, pass_ref=True)
tab_menu.br()
# tab_menu.add("Sort Track Numbers", sort_track_2, pass_ref=True)
# tab_menu.add("Sort By Filepath", sort_path_pl, pass_ref=True)

tab_menu.add_sub("Misc...", 145)


tab_menu.add_to_sub("Export Playlist Stats", 1, export_stats, pass_ref=True)
tab_menu.add_to_sub('Transcode All', 1, convert_playlist, pass_ref=True)
tab_menu.add_to_sub('Rescan Tags', 1, rescan_tags, pass_ref=True)
tab_menu.add_to_sub('Re-Import Last Folder', 1, re_import, pass_ref=True)
tab_menu.add_to_sub('Export XSPF', 1, export_xspf, pass_ref=True)
tab_menu.add_to_sub("Toggle Breaks", 1, pl_toggle_playlist_break, pass_ref=True)

def new_playlist(switch=True):
    ex = 1
    title = "New Playlist"
    while ex < 100:
        for playlist in pctl.multi_playlist:
            if playlist[0] == title:
                ex += 1
                title = "New Playlist (" + str(ex) + ")"
                break
        else:
            break

    pctl.multi_playlist.append(pl_gen(title=title))  # [title, 0, [], 0, 0, 0])
    if switch:
        switch_playlist(len(pctl.multi_playlist) - 1)
    return len(pctl.multi_playlist) - 1


#tab_menu.add_to_sub("Empty Playlist", 0, new_playlist)

def best(index):
    #key = pctl.master_library[index].title + pctl.master_library[index].filename
    if pctl.master_library[index].length < 1:
        return 0
    return int(star_store.get(index))
    # if key in pctl.star_library:
    #     return int(pctl.star_library[key])  # / pctl.master_library[index].length)
    # else:
    #     return 0

def key_modified(index):
    return pctl.master_library[index].modified_time

def key_playcount(index):
    #key = pctl.master_library[index].title + pctl.master_library[index].filename
    if pctl.master_library[index].length < 1:
        return 0
    return star_store.get(index) / pctl.master_library[index].length
    # if key in pctl.star_library:
    #     return pctl.star_library[key] / pctl.master_library[index].length
    # else:
    #     return 0

def gen_top_100(index):


    playlist = copy.deepcopy(pctl.multi_playlist[index][2])
    playlist = sorted(playlist, key=best, reverse=True)

    # if len(playlist) > 1000:
    #     playlist = playlist[:1000]

    pctl.multi_playlist.append(pl_gen(title=pctl.multi_playlist[index][0] + " <Playtime Sorted>",
                               playlist=copy.deepcopy(playlist),
                               hide_title=1))
    #    [pctl.multi_playlist[index][0] + " <Playtime Sorted>", 0, copy.deepcopy(playlist), 0, 1, 0])


tab_menu.add_to_sub("Played Tracks", 0, gen_top_100, pass_ref=True)




def gen_folder_top(pl, get_sets=False):
    if len(pctl.multi_playlist[pl][2]) < 3:
        return

    sets = []
    se = []
    last = pctl.master_library[pctl.multi_playlist[pl][2][0]].parent_folder_path
    last_al = pctl.master_library[pctl.multi_playlist[pl][2][0]].album
    for track in pctl.multi_playlist[pl][2]:
        if last != pctl.master_library[track].parent_folder_path or last_al != pctl.master_library[track].album:
            last = pctl.master_library[track].parent_folder_path
            last_al = pctl.master_library[track].album
            sets.append(copy.deepcopy(se))
            se = []
        se.append(track)
    sets.append(copy.deepcopy(se))

    def best(folder):
        #print(folder)
        total_star = 0
        for item in folder:
            # key = pctl.master_library[item].title + pctl.master_library[item].filename
            # if key in pctl.star_library:
            #     total_star += int(pctl.star_library[key])
            total_star += int(star_store.get(item))
        #print(total_star)
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
    #     [pctl.multi_playlist[pl][0] + " <Most Played Albums>", 0, copy.deepcopy(playlist), 0, 0, 0])


    pctl.multi_playlist.append(pl_gen(title=pctl.multi_playlist[pl][0] + " <Most Played Albums>",
                                      playlist=copy.deepcopy(playlist),
                                      hide_title=0))

tab_menu.add_to_sub("Played Albums", 0, gen_folder_top, pass_ref=True)


def gen_lyrics(pl):
    playlist = []

    for item in pctl.multi_playlist[pl][2]:
        if pctl.master_library[item].lyrics != "":
            playlist.append(item)

    if len(playlist) > 0:
        pctl.multi_playlist.append(pl_gen(title="Tracks with lyrics",
                                          playlist=copy.deepcopy(playlist),
                                          hide_title=0))
    else:
        show_message("No tracks with lyrics were found.")


def gen_last_modified(index):

    playlist = copy.deepcopy(pctl.multi_playlist[index][2])
    playlist = sorted(playlist, key=key_modified, reverse=True)
    sort_track_2(0, playlist)

    pctl.multi_playlist.append(pl_gen(title=pctl.multi_playlist[index][0] + " <File modified>",
                               playlist=copy.deepcopy(playlist),
                               hide_title=0))



tab_menu.add_to_sub("File modified", 0, gen_last_modified, pass_ref=True)

def gen_love(pl):
    playlist = []

    for item in pctl.multi_playlist[pl][2]:
        if get_love_index(item):
            playlist.append(item)

    if len(playlist) > 0:
        #pctl.multi_playlist.append(["Interesting Comments", 0, copy.deepcopy(playlist), 0, 0, 0])
        pctl.multi_playlist.append(pl_gen(title="Loved",
                                          playlist=copy.deepcopy(playlist),
                                          hide_title=0))
    else:
        show_message("No loved tracks were found.")

def gen_comment(pl):
    playlist = []

    for item in pctl.multi_playlist[pl][2]:
        cm = pctl.master_library[item].comment
        if len(cm) > 20 and \
                        cm[0] != "0" and \
                        'http://' not in cm and \
                        'www.' not in cm and \
                        'Release' not in cm and \
                        'EAC' not in cm and \
                        '@' not in cm and \
                        '.com' not in cm and \
                        'ipped' not in cm and \
                        'ncoded' not in cm and \
                        'ExactA' not in cm and \
                        'WWW.' not in cm and \
                        cm[2] != "+" and \
                        cm[1] != "+":
            playlist.append(item)

    if len(playlist) > 0:
        #pctl.multi_playlist.append(["Interesting Comments", 0, copy.deepcopy(playlist), 0, 0, 0])
        pctl.multi_playlist.append(pl_gen(title="Interesting Comments",
                                          playlist=copy.deepcopy(playlist),
                                          hide_title=0))
    else:
        show_message("Nothing of interest was found.")


def gen_most_skip(pl):
    playlist = []
    for item in pctl.multi_playlist[pl][2]:
        if pctl.master_library[item].skips > 0:
            playlist.append(item)
    if len(playlist) == 0:
        show_message("Nothing to show right now.")
        return

    def worst(index):
        return pctl.master_library[index].skips

    playlist = sorted(playlist, key=worst, reverse=True)

    # pctl.multi_playlist.append(
    #     [pctl.multi_playlist[pl][0] + " <Most Skipped>", 0, copy.deepcopy(playlist), 0, 1, 0])


    pctl.multi_playlist.append(pl_gen(title=pctl.multi_playlist[pl][0] + " <Most Skipped>",
                                      playlist=copy.deepcopy(playlist),
                                      hide_title=1))

#tab_menu.add_to_sub("Most Skipped", 0, gen_most_skip, pass_ref=True)


def gen_sort_len(index):
    global pctl

    def length(index):

        if pctl.master_library[index].length < 1:
            return 0
        else:
            return int(pctl.master_library[index].length)

    playlist = copy.deepcopy(pctl.multi_playlist[index][2])
    playlist = sorted(playlist, key=length, reverse=True)

    # pctl.multi_playlist.append(
    #     [pctl.multi_playlist[index][0] + " <Duration Sorted>", 0, copy.deepcopy(playlist), 0, 1, 0])

    pctl.multi_playlist.append(pl_gen(title=pctl.multi_playlist[index][0] + " <Duration Sorted>",
                                      playlist=copy.deepcopy(playlist),
                                      hide_title=1))

tab_menu.add_to_sub("Duration", 0, gen_sort_len, pass_ref=True)


def gen_folder_duration(pl, get_sets=False):
    if len(pctl.multi_playlist[pl][2]) < 3:
        return

    sets = []
    se = []
    last = pctl.master_library[pctl.multi_playlist[pl][2][0]].parent_folder_path
    last_al = pctl.master_library[pctl.multi_playlist[pl][2][0]].album
    for track in pctl.multi_playlist[pl][2]:
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

    pctl.multi_playlist.append(pl_gen(title=pctl.multi_playlist[pl][0] + " <Longest Albums>",
                                      playlist=copy.deepcopy(playlist),
                                      hide_title=0))


tab_menu.add_to_sub("Album Duration", 0, gen_folder_duration, pass_ref=True)


def gen_sort_date(index, rev=False):
    global pctl

    def g_date(index):

        if pctl.master_library[index].date != "":
            return str(pctl.master_library[index].date)
        else:
            return "z"

    playlist = []
    lowest = 0
    highest = 0
    first = True

    for item in pctl.multi_playlist[index][2]:
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
                if year < lowest:
                    lowest = year
                if year > highest:
                    highest = year

    playlist = sorted(playlist, key=g_date, reverse=rev)

    line = " <Year Sorted>"
    if lowest != highest and lowest != 0 and highest != 0:
        if rev:
            line = " <" + str(highest) + "-" + str(lowest) + ">"
        else:
            line = " <" + str(lowest) + "-" + str(highest) + ">"

    # pctl.multi_playlist.append(
    #     [pctl.multi_playlist[index][0] + line, 0, copy.deepcopy(playlist), 0, 0, 0])

    pctl.multi_playlist.append(pl_gen(title=pctl.multi_playlist[index][0] + line,
                                      playlist=copy.deepcopy(playlist),
                                      hide_title=0))

tab_menu.add_to_sub("Year → Old-New", 0, gen_sort_date, pass_ref=True)


def gen_sort_date_new(index):
    gen_sort_date(index, True)


tab_menu.add_to_sub("Year → New-Old", 0, gen_sort_date_new, pass_ref=True)


def gen_500_random(index):
    global pctl

    playlist = copy.deepcopy(pctl.multi_playlist[index][2])
    playlist = list(set(playlist))
    random.shuffle(playlist)

    # pctl.multi_playlist.append(
    #     [pctl.multi_playlist[index][0] + " <Shuffled>", 0, copy.deepcopy(playlist), 0,
    #      1, 0])

    pctl.multi_playlist.append(pl_gen(title=pctl.multi_playlist[index][0] + " <Shuffled>",
                                      playlist=copy.deepcopy(playlist),
                                      hide_title=1))

tab_menu.add_to_sub("Shuffled Tracks", 0, gen_500_random, pass_ref=True)


def gen_folder_shuffle(index):
    folders = []
    dick = {}
    for track in pctl.multi_playlist[index][2]:
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

    # pctl.multi_playlist.append(
    #     [pctl.multi_playlist[index][0] + " <Shuffled Folders>", 0, copy.deepcopy(playlist), 0, 0, 0])

    pctl.multi_playlist.append(pl_gen(title=pctl.multi_playlist[index][0] + " <Shuffled Folders>",
                                      playlist=copy.deepcopy(playlist),
                                      hide_title=0))

tab_menu.add_to_sub("Shuffled Folders", 0, gen_folder_shuffle, pass_ref=True)


def gen_best_random(index):

    playlist = []

    for p in pctl.multi_playlist[index][2]:
        time = star_store.get(p)

        if time > 300:
            playlist.append(p)
        # key = pctl.master_library[p].title + pctl.master_library[p].filename
        # if key in pctl.star_library:
        #     if pctl.star_library[key] > 300:
        #         playlist.append(p)
    random.shuffle(playlist)
    # pctl.multi_playlist.append(
    #     [pctl.multi_playlist[index][0] + " <Random Played>", 0, copy.deepcopy(playlist), 0, 1, 0])
    if len(playlist) > 0:

        pctl.multi_playlist.append(pl_gen(title=pctl.multi_playlist[index][0] + " <Lucky Random>",
                                          playlist=copy.deepcopy(playlist),
                                          hide_title=1))

tab_menu.add_to_sub("Lucky Random", 0, gen_best_random, pass_ref=True)


def gen_reverse(index):
    playlist = list(reversed(pctl.multi_playlist[index][2]))

    # pctl.multi_playlist.append(
    #     [pctl.multi_playlist[index][0] + " <Reversed>", 0, copy.deepcopy(playlist), 0, pctl.multi_playlist[index][4],
    #      0])

    pctl.multi_playlist.append(pl_gen(title=pctl.multi_playlist[index][0] + " <Reversed>",
                                      playlist=copy.deepcopy(playlist),
                                      hide_title=pctl.multi_playlist[index][4]))

tab_menu.add_to_sub("Inverted", 0, gen_reverse, pass_ref=True)


def gen_dupe(index):
    playlist = pctl.multi_playlist[index][2]

    # pctl.multi_playlist.append(
    #     [pctl.multi_playlist[index][0], pctl.multi_playlist[index][1], copy.deepcopy(playlist),
    #      pctl.multi_playlist[index][3], pctl.multi_playlist[index][4], pctl.multi_playlist[index][5]])


    pctl.multi_playlist.append(pl_gen(title=pctl.multi_playlist[index][0],
                                      playing=pctl.multi_playlist[index][1],
                                      playlist=copy.deepcopy(playlist),
                                      position=pctl.multi_playlist[index][3],
                                      hide_title=pctl.multi_playlist[index][4],
                                      selected=pctl.multi_playlist[index][5]))

tab_menu.add_to_sub("Duplicate", 0, gen_dupe, pass_ref=True)


def gen_sort_path(index):
    def path(index):
        return pctl.master_library[index].fullpath

    playlist = copy.deepcopy(pctl.multi_playlist[index][2])
    playlist = sorted(playlist, key=path)

    # pctl.multi_playlist.append(
    #     [pctl.multi_playlist[index][0] + " <Filepath Sorted>", 0, copy.deepcopy(playlist), 0, 0, 0])

    pctl.multi_playlist.append(pl_gen(title=pctl.multi_playlist[index][0] + " <Filepath Sorted>",
                                      playlist=copy.deepcopy(playlist),
                                      hide_title=0))

# tab_menu.add_to_sub("Filepath", 1, gen_sort_path, pass_ref=True)


def gen_sort_artist(index):

    def artist(index):
        return pctl.master_library[index].artist

    playlist = copy.deepcopy(pctl.multi_playlist[index][2])
    playlist = sorted(playlist, key=artist)

    # pctl.multi_playlist.append(
    #     [pctl.multi_playlist[index][0] + " <Artist Sorted>", 0, copy.deepcopy(playlist), 0, 0, 0])

    pctl.multi_playlist.append(pl_gen(title=pctl.multi_playlist[index][0] + " <Artist Sorted>",
                                      playlist=copy.deepcopy(playlist),
                                      hide_title=0))

# tab_menu.add_to_sub("Artist → gui.abc", 0, gen_sort_artist, pass_ref=True)


def gen_sort_album(index):
    def album(index):
        return pctl.master_library[index].album

    playlist = copy.deepcopy(pctl.multi_playlist[index][2])
    playlist = sorted(playlist, key=album)

    # pctl.multi_playlist.append(
    #     [pctl.multi_playlist[index][0] + " <Album Sorted>", 0, copy.deepcopy(playlist), 0, 0, 0])

    pctl.multi_playlist.append(pl_gen(title=pctl.multi_playlist[index][0] + " <Album Sorted>",
                                      playlist=copy.deepcopy(playlist),
                                      hide_title=0))


# tab_menu.add_to_sub("Album → gui.abc", 0, gen_sort_album, pass_ref=True)
tab_menu.add_to_sub("Has Love", 0, gen_love, pass_ref=True)
tab_menu.add_to_sub("Has Comment", 0, gen_comment, pass_ref=True)
tab_menu.add_to_sub("Has Lyrics", 0, gen_lyrics, pass_ref=True)




def get_playing_line():
    if 3 > pctl.playing_state > 0:
        title = pctl.master_library[pctl.track_queue[pctl.queue_step]].title
        artist = pctl.master_library[pctl.track_queue[pctl.queue_step]].artist
        return artist + " - " + title
    else:
        return 'Stopped'


def get_broadcast_line():
    if pctl.broadcast_active:
        title = pctl.master_library[pctl.broadcast_index].title
        artist = pctl.master_library[pctl.broadcast_index].artist
        return artist + " - " + title
    else:
        return 'No Title'





def open_config():
    target = os.path.join(config_directory, "config.txt")
    if system == "windows":
        os.startfile(target)
    elif system == 'mac':
        subprocess.call(['open', target])
    else:
        subprocess.call(["xdg-open", target])


def open_license():
    target = os.path.join(install_directory, "license.txt")
    if os.path.isfile(os.path.join(install_directory, "LICENSE")):
        target = os.path.join(install_directory, "LICENSE")
    if os.path.isfile(os.path.join(install_directory, "LICENSE.txt")):
        target = os.path.join(install_directory, "LICENSE.txt")

    if system == "windows":
        os.startfile(target)
    elif system == 'mac':
        subprocess.call(['open', target])
    else:
        subprocess.call(["xdg-open", target])
        print(target)


def open_config_file():
    target = os.path.join(config_directory, "config.txt")
    if system == "windows":
        os.startfile(target)
    elif system == 'mac':
        subprocess.call(['open', target])
    else:
        subprocess.call(["xdg-open", target])


def open_encode_out():
    if system == 'windows':
        line = r'explorer ' + prefs.encoder_output.replace("/", "\\")
        subprocess.Popen(line)
    else:
        line = prefs.encoder_output
        line += "/"
        if system == 'mac':
            subprocess.Popen(['open', line])
        else:
            subprocess.Popen(['xdg-open', line])


def open_folder(index):
    if system == 'windows':
        line = r'explorer /select,"%s"' % (
            pctl.master_library[index].fullpath.replace("/", "\\"))
        subprocess.Popen(line)
    else:
        line = pctl.master_library[index].parent_folder_path
        line += "/"
        if system == 'mac':
            subprocess.Popen(['open', line])
        else:
            subprocess.Popen(['xdg-open', line])



def remove_folder(index):
    global default_playlist

    for b in range(len(default_playlist) - 1, -1, -1):
        r_folder = pctl.master_library[index].parent_folder_name
        if pctl.master_library[default_playlist[b]].parent_folder_name == r_folder:
            del default_playlist[b]

    reload()


def convert_folder(index):
    global default_playlist
    global transcode_list

    if system == 'windows':
        if not os.path.isfile(user_directory + '/encoder/ffmpeg.exe'):
            show_message("Error: Missing ffmpeg.exe from '/encoder' directory")
            return
            # if prefs.transcode_codec == 'opus' and not os.path.isfile(install_directory + '/encoder/opusenc.exe'):
            #     show_message("Error: Missing opusenc.exe from '/encoder' directory")
            return
        if prefs.transcode_codec == 'mp3' and not os.path.isfile(user_directory + '/encoder/lame.exe'):
            show_message("Error: Missing lame.exe from '/encoder' directory")
            return
        # if prefs.transcode_codec == 'ogg' and not os.path.isfile(user_directory + '/encoder/oggenc2.exe'):
        #     show_message("Error: Missing oggenc2.exe from '/encoder' directory")
        #     return
    else:
        if shutil.which('ffmpeg') is None:
            show_message("Error: ffmpeg does not appear to be installed")
            return
        if prefs.transcode_codec == 'mp3' and shutil.which('lame') is None:
            show_message("Error: LAME does not appear to be installed")
            return

    folder = []
    r_folder = pctl.master_library[index].parent_folder_path
    for item in default_playlist:
        if r_folder == pctl.master_library[item].parent_folder_path:
            folder.append(item)
            print(prefs.transcode_codec)
            print(pctl.master_library[item].file_ext)
            if prefs.transcode_codec == 'flac' and pctl.master_library[item].file_ext.lower() in ('mp3', 'opus',
                                                                                                  'mp4', 'ogg',
                                                                                                  'aac'):
                show_message("NO! Bad user!",
                             'warning', "Im not going to let you transcode a lossy codec to a lossless one!")

                return

    print(folder)
    transcode_list.append(folder)


def transfer(index, args):
    global cargo
    global default_playlist
    old_cargo = copy.deepcopy(cargo)

    if args[0] == 1 or args[0] == 0:  # copy
        if args[1] == 1:  # single track
            cargo.append(index)
            if args[0] == 0:  # cut
                del default_playlist[playlist_selected]

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

            insert = playlist_selected
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
            insert = playlist_selected

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


# Create combo album menu
combo_menu = Menu(130)
combo_menu.add('Open Folder', open_folder, pass_ref=True)

combo_menu.add("Copy Folder", temp_copy_folder, pass_ref=True)
combo_menu.add("Remove Folder", remove_folder, pass_ref=True)


def activate_track_box(index):
    global track_box
    global r_menu_index
    r_menu_index = index
    track_box = True

def menu_paste(position):
    paste(None, position)


# if system == 'windows':
#     class DROPFILES(ctypes.Structure):
#         _fields_ = (('pFiles', ctypes.wintypes.DWORD),
#                     ('pt', ctypes.wintypes.POINT),
#                     ('fNC', ctypes.wintypes.BOOL),
#                     ('fWide', ctypes.wintypes.BOOL))
#
#
#     def clip_files(file_list):
#         offset = ctypes.sizeof(DROPFILES)
#         length = sum(len(p) + 1 for p in file_list) + 1
#         size = offset + length * ctypes.sizeof(ctypes.c_wchar)
#         buf = (ctypes.c_char * size)()
#         df = DROPFILES.from_buffer(buf)
#         df.pFiles, df.fWide = offset, True
#         for path in file_list:
#             array_t = ctypes.c_wchar * (len(path) + 1)
#             path_buf = array_t.from_buffer(buf, offset)
#             path_buf.value = path
#             offset += ctypes.sizeof(path_buf)
#         stg = pythoncom.STGMEDIUM()
#         stg.set(pythoncom.TYMED_HGLOBAL, buf)
#         win32clipboard.OpenClipboard()
#         win32clipboard.EmptyClipboard()
#         try:
#             win32clipboard.SetClipboardData(win32clipboard.CF_HDROP,
#                                             stg.data)
#         finally:
#             win32clipboard.CloseClipboard()

def s_copy():

    # Copy tracks to internal clipboard
    gui.lightning_copy = False
    if key_shift_down:
        gui.lightning_copy = True

    global cargo
    cargo = []
    for item in shift_selection:
        cargo.append(default_playlist[item])

    # # Copy tracks to external clipboard
    # if 300 > len(cargo) > 0:
    #
    #     clips = []
    #     for i in range(len(cargo)):
    #         clips.append(os.path.abspath(pctl.master_library[cargo[i]].fullpath))
    #     clips = set(clips)
    #
    #     if system == 'windows':
    #         clip_files(clips)
    #     elif system == 'linux':
    #         if 'gnome' in os.environ.get('DESKTOP_SESSION'):
    #
    #             content = 'echo "copy\n'
    #             for i, item in enumerate(cargo):
    #                 content += "file://" + os.path.abspath(pctl.master_library[item].fullpath).strip("\n")
    #                 if i == len(cargo) - 1:
    #                     pass
    #                 else:
    #                     print("newline")
    #                     content += "\n"
    #
    #             #content += "\0"
    #             #content = content.encode()
    #
    #             command = content + '" | xclip -i -selection clipboard -t x-special/gnome-copied-files'
    #
    #
    #             print('hit')
    #         else:
    #             content = 'echo "'
    #             for item in cargo:
    #                 content += "file://" + os.path.abspath(pctl.master_library[item].fullpath) + "\n"
    #
    #             command = content + '" | xclip -i -selection clipboard -t text/uri-list'
    #             #command = command.encode()
    #
    #         print(command)
    #
    #         subprocess.call(command, shell=True)
    #         os.system(command)

    # print("COPY")
    # if len(cargo) > 0:
    #     if system == 'windows':
    #
    #         clips = []
    #         for i in range(len(cargo)):
    #             clips.append(os.path.abspath(pctl.master_library[cargo[i]].fullpath))
    #         clips = set(clips)
    #
    #         clip_files(clips)
    #
    #     if system == 'linux' and shutil.which('xclip'):
    #         if len(cargo) > 1000:
    #             return
    #         content = 'echo "'
    #         for item in cargo:
    #             content += "file://" + os.path.abspath(pctl.master_library[item].fullpath) + "\n"
    #
    #         command = content + '" | xclip -i -selection clipboard -t text/uri-list'
    #         print(command)
    #         subprocess.call(shlex.split(command), shell=True)
    #         os.system(command)

move_jobs = []
move_in_progress = False

def directory_size(path):
    total = 0
    for dirpath, dirname, filenames in os.walk(path):
        for file in filenames:
            path = os.path.join(dirpath, file)
            total += os.path.getsize(path)
    return total

def lightning_paste():

    move = True
    if not key_shift_down:
        move = False

    move_track = pctl.g(cargo[0])
    move_path = move_track.parent_folder_path

    match_track = pctl.g(default_playlist[shift_selection[0]])
    match_path = match_track.parent_folder_path

    if pctl.playing_state > 0 and move:
        if pctl.playing_object().parent_folder_path == move_path:
            pctl.stop(True)

    p = Path(match_path)
    s = list(p.parts)
    base = s[0]
    c = base
    del s[0]


    for level in s:
        upper = c
        c = os.path.join(c, level)

        t_artist = match_track.artist
        ta_artist = match_track.album_artist

        for g in r'[]/\;,><&*:%=+@!#^()|?^.':
            t_artist = t_artist.replace(c, '')

        for g in r'[]/\;,><&*:%=+@!#^()|?^.':
            ta_artist = ta_artist.replace(c, '')

        if (len(t_artist) > 0 and t_artist in level) or \
                (len(ta_artist) > 0 and ta_artist in level):

            print("found target artist level")
            print(t_artist)

            print("Upper folder is: " + upper)

            if not os.path.isdir(upper):
                show_message("The target directory is missing!", 'warning', upper)
                return

            if not os.path.isdir(move_path):
                show_message("The source directory is missing!", 'warning', move_path)
                return

            if directory_size(move_path) > 1500000000:
                show_message("Folder size safety limit reached! (1.5GB)", 'warning', move_path)
                return

            protect = ("", "Documents", "Music", "Desktop", "Downloads")
            for fo in protect:
                if move_path.strip('\\/') == os.path.join(os.path.expanduser('~'), fo).strip("\\/"):
                    show_message("Better not do anything to that folder!", 'warning', os.path.join(os.path.expanduser('~'), fo))
                    return

            artist = move_track.artist
            if move_track.album_artist != "":
                artist = move_track.album_artist

            for c in r'[]/\;,><&*:%=+@!#^()|?^.':
                artist = artist.replace(c, '')

            if artist == "":
                show_message("The track needs to have an artist name for this.")
                return



            artist_folder = os.path.join(upper, artist)

            print("Target will be: " + artist_folder)

            if os.path.isdir(artist_folder):
                print("The target artist folder already exists")
            else:
                print("Need to make artist folder")
                os.makedirs(artist_folder)

            print("The folder to be moved is: " + move_path)
            load_order = LoadClass()
            load_order.target = os.path.join(artist_folder, move_track.parent_folder_name)
            load_order.playlist = pctl.multi_playlist[pctl.playlist_active][6]

            insert = shift_selection[0]
            old_insert = insert
            while insert < len(default_playlist) and pctl.master_library[pctl.multi_playlist[pctl.playlist_active][2][insert]].parent_folder_name == \
                    pctl.master_library[pctl.multi_playlist[pctl.playlist_active][2][old_insert]].parent_folder_name:
                insert += 1

            load_order.playlist_position = insert



            move_jobs.append((move_path, os.path.join(artist_folder, move_track.parent_folder_name), move, move_track.parent_folder_name, load_order))

            break
    else:
        show_message("Could not find a folder with the artist's name to match level at.")
        return

    if album_mode:
        prep_gal()
        reload_albums()

    cargo.clear()

def paste(playlist=None, position=None):

    if gui.lightning_copy:
        try:
            lightning_paste()
        except OSError as e:
            show_message("An error was encountered", 'warning', str(e))

        return
    # items = None
    # if system == 'windows':
    #     clp = win32clipboard
    #     clp.OpenClipboard(None)
    #     rc = clp.EnumClipboardFormats(0)
    #     while rc:
    #         # try:
    #         #     format_name = clp.GetClipboardFormatName(rc)
    #         # except win32api.error:
    #         #     format_name = "?"
    #         # try:
    #         #     print("------")
    #         #     print("Format: " + str(rc))
    #         #     print("Name: " +  format_name)
    #         #     print("Raw: ", end="")
    #         #     print(clp.GetClipboardData(rc))
    #         #     print("Decode: " + clp.GetClipboardData(rc).decode('utf-8'))
    #         # except:
    #         #     print('error')
    #         if rc == 15:
    #             items = clp.GetClipboardData(rc)
    #
    #         rc = clp.EnumClipboardFormats(rc)
    #
    #     clp.CloseClipboard()
    #     print(items)
    #
    # elif system == 'linux' and shutil.which('xclip'):
    #
    #     #clip = SDL_GetClipboardText().decode('utf-8')
    #     command = "xclip -o -selection clipboard"
    #     p = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    #     clip = p.communicate()[0]
    #
    #     print(clip)
    #     clip = clip.decode().split('\n')
    #
    #     items = []
    #     for item in clip:
    #         if len(item) > 0 and (item[0] == '/' or 'file://' in item):
    #             if item[:6] == 'file:/':
    #                 item = item[6:] # = item.lstrip("file:/")
    #             if item[0] != "/":
    #                 item = "/" + item
    #             items.append(item)
    #
    #         else:
    #             items = None
    #             break
    #     print(items)
    # else:
    #     print("No CLIP")
    #     return
    #
    #
    # clips = []
    # cargs = []
    #
    # if items is not None:
    #     for i in range(len(cargo)):
    #         cargs.append(os.path.abspath(pctl.master_library[cargo[i]].fullpath))
    #     for i in range(len(items)):
    #         clips.append(os.path.abspath(items[i]))
    #
    # if (len(clips) > 0 and set(clips) == set(cargs)) or items is None:
    #     print('Matches clipboard, using internal copy')

    if playlist is None:
        if position is None:
            transfer(0, (2, 3))
        else:
            transfer(position, (2, 2))
    else:
        append_playlist(playlist)
    return

    # print('Importing from clipboard')
    # # print(clips)
    #
    # for item in clips:
    #     print("load item")
    #     print(item)
    #     load_order = LoadClass()
    #     load_order.target = item
    #     playlist_target = pctl.playlist_active
    #     if playlist is not None:
    #         playlist_target = playlist
    #     load_order.playlist = pctl.multi_playlist[playlist_target][6]
    #
    #     if position is not None:
    #         insert = pctl.multi_playlist[playlist_target][2].index(position)
    #         old_insert = insert
    #
    #         while insert < len(default_playlist) and pctl.master_library[pctl.multi_playlist[playlist_target][2][insert]].parent_folder_name == \
    #                 pctl.master_library[pctl.multi_playlist[playlist_target][2][old_insert]].parent_folder_name:
    #             insert += 1
    #
    #         load_order.playlist_position = insert
    #
    #     load_orders.append(copy.deepcopy(load_order))


def s_cut():
    s_copy()
    del_selected()

playlist_menu.add('Paste', paste)

def del_selected():
    global shift_selection
    global playlist_selected

    gui.update += 1
    gui.pl_update = 1

    if len(shift_selection) == 0:
        shift_selection = [playlist_selected]

    if len(default_playlist) == 0:
        return

    for item in reversed(shift_selection):
        if item > len(default_playlist) - 1:
            return
        del default_playlist[item]

    reload()

    if playlist_selected > len(default_playlist) - 1:
        playlist_selected = len(default_playlist) - 1

    shift_selection = [playlist_selected]

if gui.scale == 2:
    folder_icon = MenuIcon(WhiteModImageAsset('/gui/2x/folder.png'))
    info_icon = MenuIcon(WhiteModImageAsset('/gui/2x/info.png'))
else:
    folder_icon = MenuIcon(WhiteModImageAsset('/gui/folder.png'))
    info_icon = MenuIcon(WhiteModImageAsset('/gui/info.png'))
folder_icon.colour = [244, 220, 66, 255]
info_icon.colour = [61, 247, 163, 255]


def test_show(dummy):
    return album_mode

def show_in_gal(track):
    # goto_album(playlist_selected)
    gui.gallery_animate_highlight_on = goto_album(playlist_selected)
    gallery_select_animate_timer.set()



# Create track context menu
track_menu = Menu(195, show_icons=True) #175

track_menu.add('Open Folder', open_folder, pass_ref=True, icon=folder_icon)
track_menu.add('Track Info...', activate_track_box, pass_ref=True, icon=info_icon)
track_menu.add('Show  in Gallery', show_in_gal, pass_ref=True, show_test=test_show)

track_menu.add_sub("Meta...", 150)

track_menu.br()
#track_menu.add('Cut', s_cut, pass_ref=False)
#track_menu.add('Remove', del_selected)
track_menu.add('Copy', s_copy, copy_deco, pass_ref=False)
track_menu.add('Paste', menu_paste, paste_deco, pass_ref=True)
track_menu.br()

#track_menu.add_sub("Shift...", 135)


def rename_tracks(index):
    global track_box
    global rename_index
    global input_text
    global renamebox

    track_box = False
    rename_index = index
    renamebox = True
    input_text = ""


track_menu.add_to_sub("Rename Tracks...", 0, rename_tracks, pass_ref=True)


def delete_folder(index):

    track = pctl.master_library[index]

    old = track.parent_folder_path

    # if not key_shift_down and not key_shiftr_down:
    #     show_message("Are you sure you want to physically delete the folder? If so, press again while holding shift.")
    #     return


    if len(old) < 5:
        show_message("This folder path seems short, I don't wanna try delete that", 'warning')
        return

    if not os.path.exists(old):
        show_message("Error deleting folder. The folder seems to be missing.", 'warning', "It's gone! just gone!")
        return

    protect = ("", "Documents", "Music", "Desktop", "Downloads")

    for fo in protect:
        if old.strip('\\/') == os.path.join(os.path.expanduser('~'), fo).strip("\\/"):
            show_message("Woah, careful there!", 'warning', "I don't think we should delete that folder.")
            return

    if directory_size(old) > 1500000000:
        show_message("Folder size safety limit reached! (1.5GB)", 'warning', old)
        return

    try:


        if pctl.playing_state > 0 and os.path.normpath(
                pctl.master_library[pctl.track_queue[pctl.queue_step]].parent_folder_path) == os.path.normpath(old):
            pctl.stop(True)

        shutil.rmtree(old)

        for i in reversed(range(len(default_playlist))):

            if old == pctl.master_library[default_playlist[i]].parent_folder_path:
                del default_playlist[i]

        if not os.path.exists(old):
            show_message("Folder deleted.", 'done', old)
        else:
            show_message("Hmm, its still there", 'warning', old)

        if album_mode:
            prep_gal()
            reload_albums()

    except:
        show_message("Unable to comply.", 'warning', "Could not delete folder. Try check permissions.")


def rename_parent(index, template):

    #template = prefs.rename_folder_template
    template = template.strip("/\\")
    track = pctl.master_library[index]

    old = track.parent_folder_path
    #print(old)

    new = parse_template(template, track, up_ext=True)
    print(new)


    if len(new) < 1:
        show_message("Rename error.", 'warning', "The generated name is too short")
        return

    if len(old) < 5:
        show_message("Rename error.", 'warning', "This folder path seems short, I don't wanna try rename that")
        return

    if not os.path.exists(old):
        show_message("Rename Failed. The original folder is missing.", 'warning')
        return

    protect = ("", "Documents", "Music", "Desktop", "Downloads")

    for fo in protect:
        if os.path.normpath(old) == os.path.normpath(os.path.join(os.path.expanduser('~'), fo)):
            show_message("Woah, careful there!", 'warning', "I don't think we should rename that folder.")
            return

    print(track.parent_folder_path)
    re = os.path.dirname(track.parent_folder_path.rstrip("/\\"))
    print(re)
    new_parent_path = os.path.join(re, new)
    print(new_parent_path)

    pre_state = 0

    for key, object in pctl.master_library.items():

        if object.fullpath == "":
            continue


        if old == object.parent_folder_path:

            new_fullpath = os.path.join(new_parent_path, object.filename)

            if os.path.normpath(new_parent_path) == os.path.normpath(old):
                show_message("The folder already has that name.")
                return

            if os.path.exists(new_parent_path):
                show_message("Rename Failed.", 'warning', "A folder with that name already exists")
                return

            if key == pctl.track_queue[pctl.queue_step] and pctl.playing_state > 0:
                pre_state = pctl.stop(True)


            object.parent_folder_name = new
            object.parent_folder_path = new_parent_path
            object.fullpath = new_fullpath

        # Fix any other tracks paths that contain the old path
        if os.path.normpath(object.fullpath)[:len(old)] == os.path.normpath(old) \
                and os.path.normpath(object.fullpath)[len(old)] in ('/', '\\'):
            object.fullpath = os.path.join(new_parent_path, object.fullpath[len(old):].lstrip('\\/'))
            object.parent_folder_path = os.path.join(new_parent_path, object.parent_folder_path[len(old):].lstrip('\\/'))


    if new_parent_path is not None:
        try:
            os.rename(old, new_parent_path)
            print(new_parent_path)
        except:

            show_message("Rename Failed!", 'warning' "Something went wrong, sorry.")
            return

    show_message("Folder renamed.", 'done', "Renamed to: " + new)

    if pre_state == 1:
        pctl.revert()


def rename_folders(index):
    global track_box
    global rename_index
    global input_text

    track_box = False
    rename_index = index
    gui.rename_folder_box = True
    input_text = ""
    shift_selection.clear()

    global quick_drag
    global playlist_hold
    quick_drag = False
    playlist_hold = False

track_menu.add_to_sub("Modify Folder...", 0, rename_folders, pass_ref=True)


def move_folder_up(index, do=False):

    track = pctl.master_library[index]

    parent_folder = os.path.dirname(track.parent_folder_path)
    folder_name = track.parent_folder_name
    move_target = track.parent_folder_path
    upper_folder = os.path.dirname(parent_folder)

    if not os.path.exists(track.parent_folder_path):
        if do:
            show_message("Error shifting directory", 'warning', "The directory does not appear to exist")
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
        show_message("System Error!", 'warning', str(e))

    # Fix any other tracks paths that contain the old path
    old = track.parent_folder_path
    new_parent_path = os.path.join(upper_folder, folder_name)
    for key, object in pctl.master_library.items():

        if os.path.normpath(object.fullpath)[:len(old)] == os.path.normpath(old) \
                and os.path.normpath(object.fullpath)[len(old)] in ('/', '\\'):
            object.fullpath = os.path.join(new_parent_path, object.fullpath[len(old):].lstrip('\\/'))
            object.parent_folder_path = os.path.join(new_parent_path, object.parent_folder_path[len(old):].lstrip('\\/'))

            print(object.fullpath)
            print(object.parent_folder_path)

    if pre_state == 1:
        pctl.revert()


def clean_folder(index, do=False):

    track = pctl.master_library[index]
    folder = track.parent_folder_path
    found = 0
    to_purge = []
    if not os.path.isdir(folder):
        return 0
    try:
        for item in os.listdir(folder):
            if ('AlbumArt' == item[:8] and '.jpg' in item.lower()) \
                    or 'desktop.ini' == item\
                    or 'Thumbs.db' == item\
                    or '.DS_Store' == item:

                to_purge.append(item)
                found += 1
            elif "__MACOSX" == item and os.path.isdir(os.path.join(folder, item)):
                found += 1
                found += 1
                if do:
                    print("Deleting Folder: " + os.path.join(folder, item))
                    shutil.rmtree(os.path.join(folder, item))

        if do:
            for item in to_purge:
                if os.path.isfile(os.path.join(folder, item)):
                    print('Deleting File: ' + os.path.join(folder, item))
                    os.remove(os.path.join(folder, item))
            clear_img_cache()
    except Exception as e:
        #show_message(str(e))
        show_message("Error deleting files.", 'warning', "May not have permission or file may be set to read-only")
        return 0

    return found



def reset_play_count(index):

    star_store.remove(index)


#track_menu.add_to_sub("Reset Track Play Count", 0, reset_play_count, pass_ref=True)


def get_like_folder(index):
    tracks = []
    for k in default_playlist:

        if pctl.master_library[index].parent_folder_name == pctl.master_library[k].parent_folder_name:
            if pctl.master_library[k].is_cue is False:
                tracks.append(k)
    return tracks


def reload_metadata(index):
    global todo

    todo = []
    for k in default_playlist:

        if pctl.master_library[index].parent_folder_name == pctl.master_library[k].parent_folder_name:
            if pctl.master_library[k].is_cue == False:
                todo.append(k)

    for track in todo:

        print('Reloading Metadate for ' + pctl.master_library[track].filename)
        #key = pctl.master_library[track].title + pctl.master_library[track].filename
        star = star_store.full_get(track)
        star_store.remove(track)

        # if key in pctl.star_library:
        #     star = pctl.star_library[key]
        #     del pctl.star_library[key]

        pctl.master_library[track] = tag_scan(pctl.master_library[track])

        #key = pctl.master_library[track].title + pctl.master_library[track].filename
        #pctl.star_library[key] = star
        if star is not None and star[0] > 0:
            star_store.insert(track, star)

def reload_metadata_selection():

    cargo = []
    for item in shift_selection:
        cargo.append(default_playlist[item])

    todo = []

    for k in cargo:
        if pctl.master_library[k].is_cue == False:
            todo.append(k)

    for track in todo:

        print('Reloading Metadate for ' + pctl.master_library[track].filename)

        star = star_store.full_get(track)
        star_store.remove(track)
        pctl.master_library[track] = tag_scan(pctl.master_library[track])

        if star is not None and star[0] > 0:
            star_store.insert(track, star)



def editor(index):
    todo = []

    if index is None:
        for item in shift_selection:
            todo.append(default_playlist[item])
        if len(todo) > 0:
            index = todo[0]
    else:
        for k in default_playlist:
            if pctl.master_library[index].parent_folder_path == pctl.master_library[k].parent_folder_path:
                if pctl.master_library[k].is_cue == False:
                    todo.append(k)

    file_line = ""
    for track in todo:
        file_line += ' "'
        file_line += pctl.master_library[track].fullpath
        file_line += '"'

    if system == 'windows':
        file_line = file_line.replace("/", "\\")

    if system == 'windows':
        file_line = '"' + prefs.tag_editor_path.replace("/", "\\") + '"' + file_line
    else:
        file_line = prefs.tag_editor_target + file_line

    show_message(prefs.tag_editor_name + " launched.", 'arrow', "Fields will be updated once application is closed.")
    gui.update = 1

    subprocess.run(shlex.split(file_line))

    gui.message_box = False
    reload_metadata(index)
    gui.pl_update = 1
    gui.update = 1


def launch_editor(index):
    print(index)
    mini_t = threading.Thread(target=editor, args=[index])
    mini_t.daemon = True
    mini_t.start()

def launch_editor_selection(index):
    mini_t = threading.Thread(target=editor, args=[None])
    mini_t.daemon = True
    mini_t.start()

# track_menu.add('Reload Metadata', reload_metadata, pass_ref=True)
track_menu.add_to_sub("Reload Metadata", 0, reload_metadata, pass_ref=True)

if prefs.tag_editor_name != "":


    if system == 'windows' and len(prefs.tag_editor_path) > 1 and os.path.isfile(prefs.tag_editor_path):
        track_menu.add_to_sub("Edit tags with " + prefs.tag_editor_name, 0, launch_editor, pass_ref=True)

    elif system != 'windows' and len(prefs.tag_editor_target) > 1 and shutil.which(prefs.tag_editor_target) is not None:
        track_menu.add_to_sub("Edit tags with " + prefs.tag_editor_name, 0, launch_editor, pass_ref=True)


def recode(text, enc):
    return text.encode("Latin-1", 'ignore').decode(enc, 'ignore')

j_chars = "あおいえうんわらまやはなたさかみりひにちしきるゆむぬつすくれめへねてせけをろもほのとそこアイウエオンヲラマハナタサカミヒニチシキルユムフヌツスクレメヘネテセケロヨモホノトソコ"

def intel_moji(index):

    gui.pl_update += 1
    gui.update += 1

    track = pctl.master_library[index]

    lot = []

    for item in default_playlist:

        if track.album == pctl.master_library[item].album and \
            track.parent_folder_name == pctl.master_library[item].parent_folder_name:
            lot.append(item)

    lot = set(lot)


    l_artist = track.artist.encode("Latin-1", 'ignore')
    l_album = track.album.encode("Latin-1", 'ignore')
    detect = None

    if track.artist not in track.parent_folder_path:
        for enc in encodings:
            try:
                q_artist = l_artist.decode(enc,)
                if q_artist.strip(" ") in track.parent_folder_path.strip(" "):
                    detect = enc
                    break
            except:
                continue


    if detect is None and track.album not in track.parent_folder_path:
        for enc in encodings:
            try:
                q_album = l_album.decode(enc,)
                if q_album in track.parent_folder_path:
                    detect = enc
                    break
            except:
                continue

    for item in lot:
        t_track = pctl.master_library[item]

        if detect is None:
            for enc in encodings:
                test = recode(t_track.artist, enc)
                for cha in test:
                    if cha in j_chars:
                        detect = enc
                        print("This looks like Japanese: " + test)
                        break
                    if detect is not None:
                        break

        if detect is None:
            for enc in encodings:
                test = recode(t_track.title, enc)
                for cha in test:
                    if cha in j_chars:
                        detect = enc
                        print("This looks like Japanese: " + test)
                        break
                    if detect is not None:
                        break
        if detect is not None:
            break

    if detect is not None:
        print("Fix Mojibake: Detected encoding as: " + detect)
        for item in lot:
            track = pctl.master_library[item]
            #key = pctl.master_library[item].title + pctl.master_library[item].filename
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

    else:
        show_message("Autodetect failed")


track_menu.add_to_sub("Fix Mojibake", 0, intel_moji, pass_ref=True)
#track_menu.add_to_sub("Fix Mojibake Manual...", 0, activate_encoding_box, pass_ref=True)


# class Samples:
#     def __init__(self):
#         self.cache_directroy = os.path.join(user_directory, 'web') + "/"
#         self.auth = {}
#
#     def create_sample(self, index):
#
#         show_message("Generating link...")
#         if not os.path.exists(self.cache_directroy):
#             os.makedirs(self.cache_directroy)
#
#         agg = [index]
#         loaderThread = threading.Thread(target=self.next, args=agg)
#         loaderThread.daemon = True
#         loaderThread.start()
#
#     def next(self, index):
#
#         for key, value in self.auth.items():
#             if value == index:
#                 name = key
#                 filename = samples.cache_directroy + key
#                 if os.path.isfile(filename):
#                     copy_to_clipboard("http://localhost:" + str(prefs.server_port) + "/sample/" + key)
#                     show_message("Link copied to clipboard")
#                     return
#
#         name = str(index) + "-" + str(random.randrange(11111, 99999))
#         filename = samples.cache_directroy + name
#         if os.path.isfile(filename):
#             os.remove(filename)
#
#         self.auth[name] = index
#         transcode_single(index, self.cache_directroy, name)
#         copy_to_clipboard("http://localhost:7590/sample/" + name)
#         show_message("Done, link copied to clipboard")
#         if not prefs.expose_web:
#             show_message(
#                 "Done, link copied to clipboard. Note: Current configuration does not allow for external connections")


def sel_to_car():

    global default_playlist
    cargo = []

    for item in shift_selection:
        cargo.append(default_playlist[item])


# track_menu.add_to_sub("Copy Playlist", 1, transfer, pass_ref=True, args=[1, 3])
def cut_selection():
    sel_to_car()
    del_selected()

def clip_ar_al(index):
    line = pctl.master_library[index].artist + " - " + \
           pctl.master_library[index].album
    SDL_SetClipboardText(line.encode('utf-8'))

def clip_ar(index):
    if pctl.master_library[index].album_artist != "":
        line = pctl.master_library[index].album_artist
    else:
        line = pctl.master_library[index].artist
    SDL_SetClipboardText(line.encode('utf-8'))

def clip_title(index):

    n_track = pctl.master_library[index]

    if not prefs.use_title and n_track.album_artist != "" and n_track.album != "":
        line = n_track.album_artist + " - " + n_track.album
    else:
        line = n_track.parent_folder_name

    SDL_SetClipboardText(line.encode('utf-8'))

selection_menu = Menu(190, show_icons=False)
folder_menu = Menu(190, show_icons=True)

folder_menu.add('Open Folder', open_folder, pass_ref=True, icon=folder_icon)

if gui.scale == 2:
    mod_folder_icon = MenuIcon(WhiteModImageAsset('/gui/2x/mod_folder.png'))
else:
    mod_folder_icon = MenuIcon(WhiteModImageAsset('/gui/mod_folder.png'))

mod_folder_icon.colour = [229, 98, 98, 255]



folder_menu.add("Modify Folder...", rename_folders, pass_ref=True, icon=mod_folder_icon)

folder_menu.add("Rename Tracks...", rename_tracks, pass_ref=True)

if prefs.tag_editor_name != "":

    edit_icon = None
    # if prefs.tag_editor_name == "Picard":
    #     edit_icon = MenuIcon(LoadImageAsset('/gui/pic-l.png'))
    #     edit_icon.base_asset = LoadImageAsset('/gui/pic-d.png')
    #     edit_icon.xoff = 1
    #     edit_icon.yoff = -1

    if system == 'windows' and len(prefs.tag_editor_path) > 1 and os.path.isfile(prefs.tag_editor_path):
        selection_menu.add("Edit tags with " + prefs.tag_editor_name, launch_editor_selection, pass_ref=True, icon=edit_icon)
        folder_menu.add("Edit tags with " + prefs.tag_editor_name, launch_editor_selection, pass_ref=True,
                           icon=edit_icon)

    elif system != 'windows' and len(prefs.tag_editor_target) > 1 and shutil.which(prefs.tag_editor_target) is not None:
        selection_menu.add("Edit tags with " + prefs.tag_editor_name, launch_editor_selection, pass_ref=True, icon=edit_icon)
        folder_menu.add("Edit tags with " + prefs.tag_editor_name, launch_editor_selection, pass_ref=True,
                           icon=edit_icon)

def lightning_copy():
    s_copy()
    gui.lightning_copy = True

#selection_menu.br()

def toggle_transcode(mode=0):
    if mode == 1:
        return prefs.enable_transcode
    prefs.enable_transcode ^= True

if gui.scale == 2:
    transcode_icon = MenuIcon(WhiteModImageAsset('/gui/2x/transcode.png'))
else:
    transcode_icon = MenuIcon(WhiteModImageAsset('/gui/transcode.png'))

transcode_icon.colour = [239, 74, 157, 255]

folder_menu.add('Reload Metadata', reload_metadata_selection)
folder_menu.add('Transcode Folder', convert_folder, pass_ref=True, icon=transcode_icon, show_test=toggle_transcode)
folder_menu.br()

folder_menu.add('Copy Album Title', clip_title, pass_ref=True)
#selection_menu.add('Copy "Artist - Album"', clip_ar_al, pass_ref=True)
folder_menu.add('Copy Artist', clip_ar, pass_ref=True)
#selection_menu.br()
selection_menu.add('Reload Metadata', reload_metadata_selection)

selection_menu.br()
folder_menu.br()
#selection_menu.add('Copy Selection', sel_to_car)
folder_menu.add('Copy Folder From Library', lightning_copy)

selection_menu.add('Copy', s_copy)
selection_menu.add('Cut', s_cut)
selection_menu.add('Remove', del_selected)

folder_menu.add('Copy', s_copy)
folder_menu.add('Cut', s_cut)
folder_menu.add('Remove', del_selected)

def toggle_rym(mode=0):
    if mode == 1:
        return prefs.show_rym
    prefs.show_rym ^= True

def toggle_wiki(mode=0):
    if mode == 1:
        return prefs.show_wiki
    prefs.show_wiki ^= True

def toggle_gimage(mode=0):
    if mode == 1:
        return prefs.show_gimage
    prefs.show_gimage ^= True

def toggle_gen(mode=0):
    if mode == 1:
        return prefs.show_gen
    prefs.show_gen ^= True

def ser_rym(index):
    if len(pctl.master_library[index].artist) < 2:
        return
    line = "http://rateyourmusic.com/search?searchtype=a&searchterm=" + urllib.parse.quote(pctl.master_library[index].artist)
    webbrowser.open(line, new=2, autoraise=True)


def copy_to_clipboard(text):
    SDL_SetClipboardText(text.encode())

def copy_from_clipboard():
    return SDL_GetClipboardText().decode()


def clip_aar_al(index):
    if pctl.master_library[index].album_artist == "":
        line = pctl.master_library[index].artist + " - " + \
               pctl.master_library[index].album
    else:
        line = pctl.master_library[index].album_artist + " - " + \
               pctl.master_library[index].album
    SDL_SetClipboardText(line.encode('utf-8'))


def ser_gen(index):
    if len(pctl.master_library[index].title) < 1:
        return

    line = "https://genius.com/search?q=" + \
           urllib.parse.quote(pctl.master_library[index].artist + " " + pctl.master_library[index].title)
    webbrowser.open(line, new=2, autoraise=True)

def ser_wiki(index):
    if len(pctl.master_library[index].artist) < 2:
        return
    line = "http://en.wikipedia.org/wiki/Special:Search?search=" + \
           urllib.parse.quote(pctl.master_library[index].artist)
    webbrowser.open(line, new=2, autoraise=True)

def ser_gimage(index):
    track = pctl.master_library[index]
    line = "https://www.google.com/search?tbm=isch&q=" + urllib.parse.quote(track.artist + " " + track.album)
    webbrowser.open(line, new=2, autoraise=True)


track_menu.add('Search Images on Google', ser_gimage, pass_ref=True, show_test=toggle_gimage)

track_menu.add('Search Artist on Wikipedia', ser_wiki, pass_ref=True, show_test=toggle_wiki)

track_menu.add('Search Track on Genius', ser_gen, pass_ref=True, show_test=toggle_gen)

if gui.scale == 2:
    son_icon = MenuIcon(LoadImageAsset('/gui/2x/sonemic-g.png'))
    son_icon.base_asset = LoadImageAsset('/gui/2x/sonemic-gs.png')
else:
    son_icon = MenuIcon(LoadImageAsset('/gui/sonemic-g.png'))
    son_icon.base_asset = LoadImageAsset('/gui/sonemic-gs.png')
son_icon.xoff = 1
track_menu.add('Search Artist on Sonemic', ser_rym, pass_ref=True, icon=son_icon, show_test=toggle_rym)


# track_menu.add('Copy "Artist - Album"', clip_ar_al, pass_ref=True)



def clip_ar_tr(index):
    line = pctl.master_library[index].artist + " - " + \
           pctl.master_library[index].title

    SDL_SetClipboardText(line.encode('utf-8'))


track_menu.add('Copy "Artist - Album"', clip_aar_al, pass_ref=True)
track_menu.add('Copy "Artist - Track"', clip_ar_tr, pass_ref=True)


def queue_deco():
    if len(pctl.force_queue) > 0:
        line_colour = colours.menu_text
    else:
        line_colour = colours.menu_text_disabled

    return [line_colour, colours.menu_background, None]


def broadcast_feature_deco():
    if pctl.broadcast_active:
        line_colour = colours.menu_text
    else:
        line_colour = colours.menu_text_disabled

    return [line_colour, colours.menu_background, None]


def broadcast_select_track(index):
    if pctl.broadcast_active:
        pctl.broadcast_index = index
        pctl.broadcast_playlist = copy.deepcopy(pctl.playlist_active)
        pctl.broadcast_position = default_playlist.index(pctl.broadcast_index)
        pctl.broadcast_time = 0
        pctl.target_open = pctl.master_library[pctl.broadcast_index].fullpath
        pctl.b_start_time = pctl.master_library[pctl.broadcast_index].start_time
        pctl.playerCommand = "cast-next"
        pctl.playerCommandReady = True
        pctl.broadcast_line = pctl.master_library[pctl.broadcast_index].artist + " - " + \
                              pctl.master_library[pctl.broadcast_index].title

if prefs.enable_transcode or default_player == 1:
    track_menu.br()


track_menu.add('Transcode Folder', convert_folder, pass_ref=True, icon=transcode_icon, show_test=toggle_transcode)

if default_player == 1:
    track_menu.add('Broadcast This', broadcast_select_track, broadcast_feature_deco, pass_ref=True)

# Create top menu
x_menu = Menu(190, show_icons=True)
view_menu = Menu(170)
set_menu = Menu(150)
vis_menu = Menu(140)
field_menu = Menu(140)

def field_copy(text_field):
    text_field.copy()



def field_paste(text_field):
    text_field.paste()

def field_clear(text_field):
    text_field.clear()

field_menu.add("Copy", field_copy, pass_ref=True)
field_menu.add("Paste", field_paste, pass_ref=True)
field_menu.add("Clear", field_clear, pass_ref=True)


def vis_off():
    gui.vis = 0
    gui.turbo = False
vis_menu.add("Off", vis_off)

def level_on():
    if gui.vis == 1 and gui.turbo is True:
        gui.level_meter_colour_mode += 1
        if gui.level_meter_colour_mode > 4:
            gui.level_meter_colour_mode = 0

    gui.vis = 1
    gui.turbo = True
vis_menu.add("Level Meter", level_on)

def spec_on():
    gui.vis = 2
    gui.turbo = True
vis_menu.add("Spectrum Visualizer", spec_on)

def spec2_def():
    gui.vis = 3
    gui.turbo = True
    prefs.spec2_colour_setting = 'custom'
    gui.update_layout()
vis_menu.add("Spectrogram", spec2_def)

# def spec2_1():
#     gui.vis = 3
#     prefs.spec2_colour_setting = 'horizon'
#     gui.update_layout()
# vis_menu.add("Spectrogram: Horizon", spec2_1)
#
# def spec2_2():
#     gui.vis = 3
#     prefs.spec2_colour_setting = 'plasma'
#     gui.update_layout()
# vis_menu.add("Spectrogram: Plasma", spec2_2)
#
# def spec2_3():
#     gui.vis = 3
#     prefs.spec2_colour_setting = 'grey'
#     gui.update_layout()
# vis_menu.add("Spectrogram: Grey", spec2_3)

def sa_remove(h):
    if len(gui.pl_st) > 1:
        del gui.pl_st[h]
        gui.update_layout()
    else:
        show_message("Cannot remove the only column.")

def sa_artist():
    gui.pl_st.append(["Artist", 220, False])
    gui.update_layout()
def sa_title():
    gui.pl_st.append(["Title", 220, False])
    gui.update_layout()
def sa_album():
    gui.pl_st.append(["Album", 220, False])
    gui.update_layout()
def sa_track():
    gui.pl_st.append(["T", 25, True])
    gui.update_layout()
def sa_count():
    gui.pl_st.append(["P", 25, True])
    gui.update_layout()
def sa_time():
    gui.pl_st.append(["Time", 55, True])
    gui.update_layout()
def sa_date():
    gui.pl_st.append(["Date", 55, True])
    gui.update_layout()
def sa_genre():
    gui.pl_st.append(["Genre", 150, False])
    gui.update_layout()
def sa_file():
    gui.pl_st.append(["Filepath", 350, False])
    gui.update_layout()
def sa_codec():
    gui.pl_st.append(["Codec", 65, True])
    gui.update_layout()
def sa_bitrate():
    gui.pl_st.append(["Bitrate", 65, True])
    gui.update_layout()
def sa_lyrics():
    gui.pl_st.append(["Lyrics", 50, True])
    gui.update_layout()
def sa_star():
    gui.pl_st.append(["Starline", 80, True])
    gui.update_layout()
def sa_love():
    gui.pl_st.append(["❤", 25, True])
    gui.update_layout()

def key_love(index):
    return get_love_index(index)

def key_artist(index):
    return pctl.master_library[index].artist

def key_title(index):
    return pctl.master_library[index].title

def key_album(index):
    return pctl.master_library[index].album

def key_duration(index):
    return pctl.master_library[index].length

def key_date(index):
    return pctl.master_library[index].date

def key_genre(index):
    return pctl.master_library[index].genre

def key_t(index):
    return str(pctl.master_library[index].track_number)

def key_codec(index):
    return pctl.master_library[index].file_ext

def key_bitrate(index):
    return pctl.master_library[index].bitrate

def key_p(index):
    return pctl.master_library[index].bitrate

def key_hl(index):
    if len(pctl.master_library[index].lyrics) > 5:
        return 0
    else:
        return 1

def sort_ass(h, invert=False):
    global default_playlist
    global playlist_position

    name = gui.pl_st[h][0]
    key = None

    if name == "Artist":
        key = key_artist
    if name == "Title":
        key = key_title
    if name == "Album":
        key = key_album
    if name == "Time":
        key = key_duration
    if name == "Date":
        key = key_date
    if name == "Genre":
        key = key_genre
    if name == "T":
        key = key_t
    if name == "P":
        key = key_playcount
    if name == 'Starline':
        key = best
    if name == "Codec":
        key = key_codec
    if name == "Bitrate":
        key = key_bitrate
    if name == "Lyrics":
        key = key_hl
    if name == "❤":
        key = key_love

    if key is not None:
        playlist = pctl.multi_playlist[pctl.playlist_active][2]
        playlist.sort(key=key)

        if invert:
            playlist = list(reversed(playlist))

        pctl.multi_playlist[pctl.playlist_active][2] = playlist
        default_playlist = pctl.multi_playlist[pctl.playlist_active][2]

    playlist_position = 0
    gui.pl_update = 1


def sort_dec(h):
    sort_ass(h, True)


def hide_set_bar():
    gui.set_bar = False
    gui.update_layout()
    gui.pl_update = 1


set_menu.add("Sort Acceding", sort_ass, pass_ref=True)
set_menu.add("Sort Decending", sort_dec, pass_ref=True)
set_menu.br()
set_menu.add("Hide bar", hide_set_bar)
set_menu.br()
set_menu.add("+ Artist", sa_artist)
set_menu.add("+ Title", sa_title)
set_menu.add("+ Album", sa_album)
set_menu.add("+ Duration", sa_time)
set_menu.add("+ Date", sa_date)
set_menu.add("+ Genre", sa_genre)
set_menu.add("+ Track Number", sa_track)
set_menu.add("+ Play Count", sa_count)
set_menu.add("+ Codec", sa_codec)
set_menu.add("+ Bitrate", sa_bitrate)
set_menu.add("+ Has Lyrics", sa_lyrics)
set_menu.add("+ Filepath", sa_file)
set_menu.add("+ Starline", sa_star)
set_menu.add("+ Loved", sa_love)
set_menu.br()
set_menu.add("- Remove This", sa_remove, pass_ref=True)


def bass_features_deco():
    line_colour = colours.menu_text
    if default_player != 1:
        line_colour = colours.menu_text_disabled
    return [line_colour, colours.menu_background, None]


def toggle_dim_albums(mode=0):
    if mode == 1:
        return prefs.dim_art

    prefs.dim_art ^= True
    gui.pl_update = 1
    gui.update += 1

def toggle_galler_text(mode=0):
    if mode == 1:
        return gui.gallery_show_text

    gui.gallery_show_text ^= True
    gui.update += 1
    gui.update_layout()

def toggle_side_panel(mode=0):
    global side_panel_enable
    global update_layout
    global album_mode

    if mode == 1:
        return prefs.prefer_side

    prefs.prefer_side ^= True
    update_layout = True

    if album_mode:
        side_panel_enable = True
    elif prefs.prefer_side is True:
        side_panel_enable = True
    else:
        side_panel_enable = False
        # if side_panel_enable:
        #     gui.combo_mode = False


def toggle_combo_view(mode=0, showcase=False, off=False):
    global update_layout
    global side_panel_enable
    global old_side_pos

    if mode == 1:
        return gui.combo_mode

    if not off:
        if showcase:
            gui.showcase_mode = True
        else:
            if gui.combo_mode and gui.showcase_mode:
                gui.showcase_mode = False
                return
            gui.showcase_mode = False

    if gui.combo_mode is False:
        if not album_mode:
            old_side_pos = gui.side_panel_size
        gui.combo_mode = True
        reload_albums()

        # clear_img_cache()
        gall_ren.size = combo_mode_art_size
        combo_pl_render.prep(True)

        if album_mode:
            toggle_album_mode()
        if side_panel_enable:
            side_panel_enable = False
    else:
        gui.combo_mode = False
        # clear_img_cache()
        gall_ren.size = album_mode_art_size
        if prefs.prefer_side:
            side_panel_enable = True
        gui.side_panel_size = old_side_pos
    update_layout = True


# x_menu.add('Toggle Side panel', toggle_side_panel)


def standard_size():
    global album_mode
    global window_size
    global update_layout
    global side_panel_enable
    global album_mode_art_size

    album_mode = False
    side_panel_enable = True
    window_size = window_default_size
    SDL_SetWindowSize(t_window, window_size[0], window_size[1])

    gui.side_panel_size = 80 + int(window_size[0] * 0.18)
    update_layout = True
    album_mode_art_size = 130
    clear_img_cache()


def goto_album(playlist_no, down=False):
    global album_pos_px
    global album_dex

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



    if album_pos_px - 20 < px < album_pos_px + window_size[1]:
        pass
    else:
        album_pos_px = px - 60
        album_pos_px += 10

        if album_pos_px < 0 - 55:
            album_pos_px = 0 - 55

    if down:
        while not album_pos_px - 20 < px + (album_mode_art_size + album_v_gap + 3) < album_pos_px + window_size[1] - 40:

            album_pos_px += 1

    if len(album_dex) > 0:
        return album_dex[re]
    else:
        return 0

def toggle_album_mode(force_on=False):
    global album_mode
    global window_size
    global update_layout
    global side_panel_enable
    global old_side_pos
    global album_playlist_width
    global old_album_pos
    global album_pos_px
    global themeChange

    gui.gall_tab_enter = False

    if prefs.colour_from_image:
        #prefs.colour_from_image = False
        themeChange = True

    if gui.show_playlist is False:
        gui.show_playlist = True
        gui.playlist_width = album_playlist_width  # int(window_size[0] * 0.25)
        gui.side_panel_size = window_size[0] - gui.playlist_width
        if force_on:
            return

    if album_mode is True:

        album_mode = False
        album_playlist_width = gui.playlist_width
        old_album_pos = album_pos_px
        side_panel_enable = prefs.prefer_side
        gui.side_panel_size = old_side_pos
    else:
        if gui.combo_mode:
            toggle_combo_view(off=True)
        album_mode = True
        side_panel_enable = True

        old_side_pos = gui.side_panel_size

    if album_mode and gui.set_mode and len(gui.pl_st) > 7:
        gui.set_mode = False
        gui.set_bar = False
        gui.pl_update = True
        gui.update_layout()

    reload_albums()

    goto_album(pctl.playlist_playing)


def activate_info_box():
    fader.rise()
    pref_box.enabled = True


def activate_radio_box():
    global radiobox
    radiobox = True
# x_menu.add("Go To Playing", pctl.show_current)

if gui.scale == 2:
    add_icon = MenuIcon(WhiteModImageAsset('/gui/2x/new.png'))
else:
    add_icon = MenuIcon(WhiteModImageAsset('/gui/new.png'))
add_icon.xoff = 3
add_icon.yoff = 0
add_icon.colour = [237, 80 ,221, 255] #[230, 118, 195, 225]#[237, 75, 218, 255]

x_menu.add("New Playlist", new_playlist, icon=add_icon)

if default_player == 1:
    x_menu.add("Open Stream...", activate_radio_box, bass_features_deco)
x_menu.br()

if gui.scale == 2:
    settings_icon = MenuIcon(WhiteModImageAsset('/gui/2x/settings2.png'))
else:
    settings_icon = MenuIcon(WhiteModImageAsset('/gui/settings2.png'))
settings_icon.xoff = 0
settings_icon.yoff = 2
settings_icon.colour = [232, 200, 96, 255]#[230, 152, 118, 255]#[173, 255, 47, 255] #[198, 237, 56, 255]
x_menu.add("Settings...", activate_info_box, icon=settings_icon)
x_menu.add_sub("Database...", 190)
x_menu.br()

# x_menu.add('Toggle Side panel', toggle_combo_view, combo_deco)

def stt2(sec):
    days, rem = divmod(sec, 86400)
    hours, rem = divmod(rem, 3600)
    min, sec = divmod(rem, 60)

    s_day = str(days) + 'd'
    if s_day == '0d':
        s_day = "  "

    s_hours = str(hours) + 'h'
    if s_hours == '0h' and s_day == '  ':
        s_hours = "  "

    s_min = str(min) + 'm'

    return s_day.rjust(3) + ' ' + s_hours.rjust(3) + ' ' + s_min.rjust(3)

def export_database():
    xport = open(user_directory + '/DatabaseExport.csv', 'wb')
    for index, track in pctl.master_library.items():

        line = []
        # print(str(pctl.master_library[num]))
        # continue
        # print(pctl.master_library[num])
        line.append(str(track.artist))
        line.append(str(track.title))
        line.append(str(track.album))
        line.append(str(track.album_artist))
        line.append(str(track.track_number))
        if track.is_cue is False:
            line.append('FILE')
        else:
            line.append('CUE')
        line.append(str(track.length))
        line.append(str(track.date))
        line.append(track.genre)
        line.append(str(int(star_store.get_by_object(track))))
        line.append(track.fullpath)

        for g in range(len(line)):
            line[g] = line[g].encode('utf-8')

        # exporter.writerow(line)
        outline = b""
        for item in line:
            outline += '"'.encode('utf-8')
            outline += item
            outline += '",'.encode('utf-8')
        outline += '\r\n'.encode('utf-8')
        xport.write(outline)

    xport.close()
    show_message("Export complete.", 'done',  "Saved as 'DatabaseExport.csv'.")


def q_to_playlist():

    pctl.multi_playlist.append(pl_gen(title="Play History",
                                      playing=0,
                                      playlist=list(reversed(copy.deepcopy(pctl.track_queue))),
                                      position=0,
                                      hide_title=1,
                                      selected=0))



def scan_rym():

    data = copy_from_clipboard()

    if data[0:9] != "RYM Album":
        show_message("Could not find data in clipboard", 'info', 'You will need to copy the whole csv text from the RYM export data page')
    else:
        try:

            lines = data.split("\n")
            read = csv.DictReader(lines)
            albums = gen_folder_top(pctl.playlist_active, True)
            read = list(read)

            found = []
            not_found = []
            spe1 = []
            spe2 = []
            spe3 = []

            for album in albums:
                tracks = album[0]
                track = pctl.master_library[tracks[0]]

                for row in read:
                    o_name = (row[' First Name'] + " " + row['Last Name']).strip().replace("&amp;", '&')
                    a_name = row["Title"].replace("&amp;", '&').strip()

                    if o_name.lower() == track.artist.lower() and a_name.lower() in track.album.lower():
                        found += tracks
                        if album[1] > 60 * 60 * 1 and int(row['Rating']) < 5:
                            spe1 += tracks
                        elif album[1] > 60 * 60 * 2 and int(row['Rating']) < 6:
                            spe2 += tracks
                        elif album[1] > 60 * 60 * 4 and int(row['Rating']) < 7:
                            spe3 += tracks
                        break
                else:
                    not_found += tracks

            pctl.multi_playlist.append(pl_gen(title="RYM FOUND",
                                              playlist=copy.deepcopy(found),
                                              hide_title=0))

            pctl.multi_playlist.append(pl_gen(title="RYM NOT FOUND",
                                              playlist=copy.deepcopy(not_found),
                                              hide_title=0))
            if len(spe1) > 0:
                pctl.multi_playlist.append(pl_gen(title="UNDERRATED A",
                                                  playlist=copy.deepcopy(spe1),
                                                  hide_title=0))
            if len(spe2) > 0:
                pctl.multi_playlist.append(pl_gen(title="UNDERRATED B",
                                                  playlist=copy.deepcopy(spe2),
                                                  hide_title=0))
            if len(spe3) > 0:
                pctl.multi_playlist.append(pl_gen(title="UNDERRATED C",
                                                  playlist=copy.deepcopy(spe3),
                                                  hide_title=0))
        except:
            show_message("Sorry, something went wrong there", 'warning')


x_menu.add_to_sub("Export as CSV", 0, export_database)
if prefs.show_rym:
    x_menu.add_to_sub("Scan Playlist with RYM DB", 0, scan_rym)
x_menu.add_to_sub("Play History to Playlist", 0, q_to_playlist)
x_menu.add_to_sub("Reset Image Cache", 0, clear_img_cache)


def reset_missing_flags():
    for index in default_playlist:
        pctl.master_library[index].found = True


cm_clean_db = False


def clean_db():
    global cm_clean_db
    cm_clean_db = True


x_menu.add_to_sub("Find and Remove Dead Tracks", 0, clean_db)

# x_menu.add('Reset Missing Flags', reset_missing_flags)
x_menu.add_to_sub("Mark Missing as Found", 0, reset_missing_flags)


def toggle_broadcast():
    # if system == 'windows' and not os.path.isfile(install_directory + "/encoder/oggenc2.exe") and not \
    #         os.path.isfile(user_directory + "/encoder/lame.exe") and not os.path.isfile(
    #             install_directory + "/encoder/opusenc.exe"):
    #     show_message("Missing Encoder. See documentation.")
    #     return

    if pctl.broadcast_active is not True:
        if len(default_playlist) == 0:
            return 0
        pctl.broadcast_playlist = pctl.playlist_active
        pctl.broadcast_position = 0

        pctl.broadcast_index = pctl.multi_playlist[pctl.broadcast_playlist][2][pctl.broadcast_position]
        pctl.target_open = pctl.master_library[pctl.broadcast_index].fullpath
        pctl.broadcast_line = pctl.master_library[pctl.broadcast_index].artist + " - " + \
                              pctl.master_library[pctl.broadcast_index].title

        pctl.playerCommand = "encstart"
        pctl.playerCommandReady = True
    else:
        pctl.playerCommand = "encstop"
        pctl.playerCommandReady = True


def broadcast_deco():
    line_colour = colours.menu_text
    if default_player != 1:
        line_colour = colours.grey(20)
        return [line_colour, colours.menu_background, None]
    if pctl.broadcast_active:
        return [line_colour, colours.menu_background, "Stop Broadcast"] # [24, 25, 60, 255]
    return [line_colour, colours.menu_background, None]

def broadcast_colour():
    if pctl.broadcast_active:
        return [56, 189, 237, 255]
    else:
        return None


if default_player == 1 and os.path.isfile(os.path.join(config_directory, "config.txt")):
    if gui.scale == 2:
        broadcast_icon = MenuIcon(WhiteModImageAsset('/gui/2x/broadcast.png'))
    else:
        broadcast_icon = MenuIcon(WhiteModImageAsset('/gui/broadcast.png'))
    broadcast_icon.colour = [171, 102, 249, 255]#[182, 116, 223, 255]#[125, 249, 255, 255] #[56, 189, 237, 255]
    broadcast_icon.colour_callback = broadcast_colour
    x_menu.add("Start Broadcast", toggle_broadcast, broadcast_deco, icon=broadcast_icon)


def clear_queue():
    pctl.force_queue = []
    gui.pl_update = 1


#x_menu.add('Clear Queue', clear_queue, queue_deco)

# x_menu.add_sub("Playback...", 120)
extra_menu = Menu(175, show_icons=True)


def stop():
    pctl.stop()


# x_menu.add_to_sub('Stop/Eject', 1, stop)
# extra_menu.add('Stop/Eject', stop)

# x_menu.add_to_sub('Advance', 1, pctl.advance)
# x_menu.add_to_sub('Back', 1, pctl.back)

def random_track():
    old = pctl.random_mode
    pctl.random_mode = True
    pctl.advance()
    pctl.random_mode = old


extra_menu.add('Random Track', random_track, hint='COLON')


def radio_random():
    pctl.advance(rr=True)

if gui.scale == 2:
    radiorandom_icon = MenuIcon(WhiteModImageAsset('/gui/2x/radiorandom.png'))
else:
    radiorandom_icon = MenuIcon(WhiteModImageAsset('/gui/radiorandom.png'))
radiorandom_icon.xoff = 1
radiorandom_icon.yoff = 0
radiorandom_icon.colour = [153, 229, 133, 255]
extra_menu.add('Radio Random', radio_random, hint='/', icon=radiorandom_icon)

if gui.scale == 2:
    revert_icon = MenuIcon(WhiteModImageAsset('/gui/2x/revert.png'))
else:
    revert_icon = MenuIcon(WhiteModImageAsset('/gui/revert.png'))
revert_icon.xoff = 1
revert_icon.yoff = 0
revert_icon.colour = [229, 102, 59, 255]
extra_menu.add('Revert', pctl.revert, hint='SHIFT + /', icon=revert_icon)


def toggle_repeat():
    pctl.repeat_mode ^= True


# extra_menu.add('Toggle Repeat', toggle_repeat, hint='COMMA')


def toggle_random():
    pctl.random_mode ^= True


# extra_menu.add('Toggle Random', toggle_random, hint='PERIOD')
extra_menu.add('Clear Queue', clear_queue, queue_deco)

def love_deco():

    if love(False):
        return [colours.menu_text, colours.menu_background, "Un-Love Track"]
    else:
        if pctl.playing_state == 1 or pctl.playing_state == 2:
            return [colours.menu_text, colours.menu_background, "Love Track"]
        else:
            return [colours.menu_text_disabled, colours.menu_background, "Love Track"]


extra_menu.add('Love', love, love_deco)

def toggle_search():
    global quick_search_mode
    global input_text
    quick_search_mode ^= True
    search_text.text = ""
    input_text = ""

extra_menu.add('Search', toggle_search, hint='BACKSLASH')

def goto_playing_extra():
    pctl.show_current(highlight=True)

extra_menu.add("Go To Playing", goto_playing_extra, hint="QUOTE")


def toggle_auto_theme(mode=0):

    if mode == 1:
        return prefs.colour_from_image

    prefs.colour_from_image ^= True
    gui.theme_temp_current = -1
    global themeChange
    themeChange = True


def toggle_mini_lyrics(mode=0):

    if mode == 1:
        return prefs.show_lyrics_side

    prefs.show_lyrics_side ^= True


def toggle_level_meter(mode=0):

    if mode == 1:
        return gui.turbo

    if gui.turbo is True:
        gui.vis = 0
        gui.turbo = False
    elif gui.turbo is False:
        gui.turbo = True
        gui.vis = 2


def level_meter_special_2():

    gui.level_meter_colour_mode = 2




def advance_theme():
    global theme
    global themeChange
    theme += 1
    themeChange = True

def last_fm_menu_deco():
    if lastfm.connected:
        line = 'Stop Last.fm Scrobbling'
        bg = colours.menu_background
    else:
        line = 'Start Last.fm Scrobbling'
        bg = colours.menu_background
    if lastfm.hold:
        line = "Start Last.fm Scrobbling"
        bg = colours.menu_background
    return [colours.menu_text, bg, line]


def lastfm_colour():
    if lastfm.connected and not lastfm.hold:
        return [250, 50, 50, 255]
    else:
        return None


if gui.scale == 2:
    lastfm_icon = MenuIcon(WhiteModImageAsset('/gui/2x/as.png'))
    lastfm_icon.xoff = 0
else:
    lastfm_icon = MenuIcon(WhiteModImageAsset('/gui/as.png'))
    lastfm_icon.xoff = -1
lastfm_icon.yoff = 1

lastfm_icon.colour = [249, 70, 70, 255]#[250, 60, 60, 255]
lastfm_icon.colour_callback = lastfm_colour

if last_fm_enable:
    x_menu.add("LFM", lastfm.toggle, last_fm_menu_deco, icon=lastfm_icon)


def exit_func():
    global running
    running = False


x_menu.add("Exit", exit_func, hint="Alt+F4")


def switch_playlist(number, cycle=False):
    global default_playlist
    global playlist_position
    global playlist_selected
    global search_index
    global shift_selection

    gui.pl_update = 1
    search_index = 0
    gui.search_error = False
    if quick_search_mode:
        gui.force_search = True

    if pl_follow:
        pctl.multi_playlist[pctl.playlist_active][1] = copy.deepcopy(pctl.playlist_playing)

    if gui.showcase_mode and gui.combo_mode:
        view_standard()

    pctl.multi_playlist[pctl.playlist_active][2] = default_playlist
    pctl.multi_playlist[pctl.playlist_active][3] = playlist_position
    pctl.multi_playlist[pctl.playlist_active][5] = playlist_selected

    if cycle:
        pctl.playlist_active += number
    else:
        pctl.playlist_active = number

    while pctl.playlist_active > len(pctl.multi_playlist) - 1:
        pctl.playlist_active -= len(pctl.multi_playlist)
    while pctl.playlist_active < 0:
        pctl.playlist_active += len(pctl.multi_playlist)

    default_playlist = pctl.multi_playlist[pctl.playlist_active][2]
    playlist_position = pctl.multi_playlist[pctl.playlist_active][3]
    playlist_selected = pctl.multi_playlist[pctl.playlist_active][5]

    if pl_follow:
        pctl.playlist_playing = playlist_selected  # pctl.multi_playlist[pctl.playlist_active][1]
        pctl.playlist_playing = copy.deepcopy(pctl.multi_playlist[pctl.playlist_active][1])
        pctl.active_playlist_playing = pctl.playlist_active

    shift_selection = [playlist_selected]

    if album_mode:
        reload_albums(True)
        goto_album(playlist_position)

    if gui.combo_mode:
        reload_albums()
        combo_pl_render.pl_pos_px = 0
        combo_pl_render.prep(True)


def view_tracks():
    # if gui.show_playlist is False:
    #     gui.show_playlist = True
    if album_mode:
        toggle_album_mode()
    if gui.combo_mode:
        toggle_combo_view(off=True)
    if side_panel_enable:
        toggle_side_panel()


def view_standard_full():
    # if gui.show_playlist is False:
    #     gui.show_playlist = True

    if album_mode:
        toggle_album_mode()
    if gui.combo_mode:
        toggle_combo_view(off=True)
    if not side_panel_enable:
        toggle_side_panel()
    global update_layout
    update_layout = True
    gui.side_panel_size = window_size[0]


def view_standard_meta():
    # if gui.show_playlist is False:
    #     gui.show_playlist = True
    if album_mode:
        toggle_album_mode()
    if gui.combo_mode:
        toggle_combo_view(off=True)
    if not side_panel_enable:
        toggle_side_panel()
    global update_layout
    update_layout = True
    #gui.side_panel_size = 80 + int(window_size[0] * 0.18)


def view_standard():
    # if gui.show_playlist is False:
    #     gui.show_playlist = True
    if album_mode:
        toggle_album_mode()
    if gui.combo_mode:
        toggle_combo_view(off=True)
    if not side_panel_enable:
        toggle_side_panel()


def standard_view_deco():
    if album_mode or gui.combo_mode or not side_panel_enable:
        line_colour = colours.menu_text
    else:
        line_colour = colours.menu_text_disabled
    return [line_colour, colours.menu_background, None]


def gallery_only_view():
    if gui.show_playlist is False:
        return
    if not album_mode:
        toggle_album_mode()
    gui.show_playlist = False
    global album_playlist_width
    global update_layout
    update_layout = True
    gui.side_panel_size = window_size[0]
    album_playlist_width = gui.playlist_width
    gui.playlist_width = -19


def force_album_view():
    toggle_album_mode(True)

def switch_showcase(index=-1):

    if pctl.playing_object() is None or pctl.playing_object().index == index:
        pass
    else:
        gui.force_showcase_index = index
    if gui.combo_mode:
        toggle_combo_view()
    toggle_combo_view(showcase=True)

def toggle_library_mode():
    if gui.set_mode:
        gui.set_mode = False
        gui.set_bar = False
    else:
        gui.set_mode = True
        gui.set_bar = True
    gui.update_layout()

def library_deco():
    tc = colours.menu_text
    if gui.combo_mode or (gui.show_playlist is False and album_mode):
        tc = colours.menu_text_disabled

    if gui.set_mode:
        return [tc, colours.menu_background, "Disable Columns"]
    else:
        return [tc, colours.menu_background, 'Enable Columns']

def break_deco():
    tex = colours.menu_text
    if gui.combo_mode or (gui.show_playlist is False and album_mode):
        tex = colours.menu_text_disabled
    if not break_enable:
        tex = colours.menu_text_disabled


    if pctl.multi_playlist[pctl.playlist_active][4] == 0:
        return [tex, colours.menu_background, "Disable Title Breaks"]
    else:
        return [tex, colours.menu_background, 'Enable Title Breaks']

def toggle_playlist_break():
    pctl.multi_playlist[pctl.playlist_active][4] ^= 1
    gui.pl_update = 1

view_menu.add("Return to Standard", view_standard, standard_view_deco)
view_menu.add("Toggle Library Mode", toggle_library_mode, library_deco)
view_menu.add("Toggle Playlist Breaks", toggle_playlist_break, break_deco, hint="F1")
view_menu.br()
view_menu.add("Tracks", view_tracks, hint="MB5")
view_menu.add("Tracks + Side Panel", view_standard_meta)
#view_menu.add("Tracks + Full Art", view_standard_full)
view_menu.add("Tracks + Gallery", force_album_view, hint="MB4")
view_menu.add("Gallery Only", gallery_only_view)
view_menu.add("Art + Tracks", toggle_combo_view)
view_menu.add("Lyrics", switch_showcase)
# ---------------------------------------------------------------------------------------

core_use = 0


def transcode_single(item, manual_directroy=None, manual_name=None):
    global core_use

    if manual_directroy != None:
        codec = "opus"
        output = manual_directroy
        track = item
        core_use += 1
        bitrate = 48
    else:
        track = item[0]
        codec = prefs.transcode_codec
        output = prefs.encoder_output + item[1] + "/"
        bitrate = prefs.transcode_bitrate

    if not os.path.isfile(pctl.master_library[track].fullpath):
        show_message("Encoding warning: Missing one or more files")
        core_use -= 1
        return

    t = pctl.master_library[track]
    if t.is_cue:
        out_line = str(t.track_number) + ". "
        out_line += t.artist + " - " + t.title
        for c in r'[]/\;,><&*:%=+@!#^()|?^.':
            out_line = out_line.replace(c, '')

    else:
        out_line = os.path.splitext(pctl.master_library[track].filename)[0]

    target_out = output + 'output' + str(track) + "." + codec

    command = user_directory + "/encoder/ffmpeg "

    if system != 'windows':
        command = "ffmpeg "

    if not pctl.master_library[track].is_cue:
        command += '-i "'
        command += pctl.master_library[track].fullpath
    else:
        command += '-ss ' + str(pctl.master_library[track].start_time)
        command += ' -t ' + str(pctl.master_library[track].length)

        command += ' -i "'
        command += pctl.master_library[track].fullpath

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

    if codec != 'flac':
        command += " -b:a " + str(bitrate) + "k -vn "

    command += '"' + target_out + '"'

    # command += full_wav_out


    print(shlex.split(command))
    startupinfo = None
    if system == 'windows':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    subprocess.call(shlex.split(command), stdout=subprocess.PIPE, shell=False,
                    startupinfo=startupinfo)

    print("done")

    print(target_out)
    if manual_name is None:
        os.rename(target_out, output + out_line + "." + codec)
    else:
        os.rename(target_out, output + manual_name + "." + codec)
    core_use -= 1


# ---------------------
added = []

def cue_scan(content, tn):
    # Get length from backend
    # if lasttime == 0 and default_player == 1:
    #     lasttime = get_backend_time(filepath)
    lasttime = tn.length

    content = content.replace("\r", "")
    content = content.split("\n")

    #print(content)

    global master_count
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

        if 'REM DATE' in LINE:
            DATE = LINE[9:len(LINE) - 1]

        if 'REM GENRE' in LINE:
            GENRE = LINE[10:len(LINE) - 1]

        if 'TRACK ' in LINE:
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

        elif 'TRACK ' in LINE:

            pos = 0
            while LINE[pos] != 'K':
                pos += 1
                if pos > 15:
                    return 1
            TN = LINE[pos + 2:pos + 4]

            TN = int(TN)

            # try:
            #     bitrate = audio.info.bitrate
            # except:
            #     bitrate = 0

            if PERFORMER == "":
                PERFORMER = MAIN_PERFORMER

            nt = copy.deepcopy(tn) #TrackClass()

            nt.cue_sheet = ""
            nt.is_embed_cue = True

            nt.index = master_count
            # nt.fullpath = filepath.replace('\\', '/')
            # nt.filename = filename
            # nt.parent_folder_path = os.path.dirname(filepath.replace('\\', '/'))
            # nt.parent_folder_name = os.path.splitext(os.path.basename(filepath))[0]
            # nt.file_ext = os.path.splitext(os.path.basename(filepath))[1][1:].upper()

            nt.album_artist = MAIN_PERFORMER
            nt.artist = PERFORMER
            nt.genre = GENRE
            nt.title = TITLE
            nt.length = LENGTH
            # nt.bitrate = source_track.bitrate
            nt.album = ALBUM
            nt.date = DATE.replace('"', '')
            nt.track_number = TN
            nt.start_time = START
            nt.is_cue = True
            nt.size = 0  # source_track.size
            # nt.samplerate = source_track.samplerate
            if TN == 1:
                nt.size = os.path.getsize(nt.fullpath)

            pctl.master_library[master_count] = nt

            cued.append(master_count)
            # loaded_pathes_cache[filepath.replace('\\', '/')] = master_count
            #added.append(master_count)

            master_count += 1
            LENGTH = 0
            PERFORMER = ""
            TITLE = ""
            START = 0
            TN = 0

    added += reversed(cued)

    # cue_list.append(filepath)


# LOADER----------------------------------------------------------------------



def worker2():
    while True:

        time.sleep(0.07)


        gall_ren.worker_render()
        # if pl_thumbnail.worker_render():
        #     gui.pl_update += 1
        #     #gui.update = 1



def worker1():
    global cue_list
    global loaderCommand
    global loaderCommandReady
    global DA_Formats
    global master_count
    global home
    global loading_in_progress
    global added
    global to_get
    global to_got

    loaded_pathes_cache = {}
    added = []

    def get_end_folder(direc):

        for w in range(len(direc)):
            if direc[-w - 1] == '\\' or direc[-w - 1] == '/':
                direc = direc[-w:]
                return direc
        return None

    def add_from_cue(path):

        global added
        global master_count

        cued = []

        try:
            print("Reading CUE file: " + path)
        except:
            print("Error reading path")

        try:

            try:

                with open(path, encoding="utf_8") as f:
                    content = f.readlines()
            except:
                try:
                    with open(path, encoding="utf_16") as f:
                        content = f.readlines()
                        print("CUE: Detected encoding as UTF-16")
                except:
                    try:
                        with open(path, encoding='shiftjis') as f:
                            content = f.readlines()
                        print("CUE: Detected encoding as SHIFT-JIS")

                    except:
                        print("WARNING: Can't detect encoding of CUE file")
                        return 1

            f.close()

            # GET "FILE" LINE
            count = 0
            fileline = -1

            # print(content)

            for i in range(len(content)):
                if 'FILE "' in content[i]:
                    count += 1
                    fileline = i
                    if count > 1:
                        return 1

            if fileline == -1:
                return 1

            FILE = content[fileline]
            # print("FILELINE IS :" + FILE)

            filename = ""
            switch = 0
            for i in range(len(FILE)):
                if switch == 1 and FILE[i] == '"':
                    break

                if switch == 1:
                    filename += FILE[i]

                if FILE[i] == '"':
                    switch = 1

            filepath = os.path.dirname(path.replace('\\', '/')) + "/" + filename

            try:
                # print(filepath)
                if os.path.isfile(filepath) is True:

                    source_track = TrackClass()
                    source_track.fullpath = filepath
                    source_track = tag_scan(source_track)
                    lasttime = source_track.length

                else:
                    print("CUE: The referenced source file wasn't found. Searching for matching file name...")

                    for item in os.listdir(os.path.dirname(filepath)):
                        if os.path.splitext(item)[0] == os.path.splitext(os.path.basename(path))[
                                0] and "cue" not in item.lower():
                            filepath = os.path.dirname(filepath) + "/" + item
                            print("CUE: Source found")
                            break
                    else:
                        print("CUE: Source file not found")
                        return 1

                    source_track = TrackClass()
                    source_track.fullpath = filepath
                    source_track = tag_scan(source_track)
                    lasttime = source_track.length

            except:
                print("CUE Error: Unable to read file length")
                return 1

            # Get length from backend
            if lasttime == 0 and default_player == 1:
                lasttime = get_backend_time(filepath)

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

                if 'REM DATE' in LINE:
                    DATE = LINE[9:len(LINE) - 1]

                if 'REM GENRE' in LINE:
                    GENRE = LINE[10:len(LINE) - 1]

                if 'TRACK ' in LINE:
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

                elif 'TRACK ' in LINE:
                    pos = 0
                    while LINE[pos] != 'K':
                        pos += 1
                        if pos > 15:
                            return 1
                    TN = LINE[pos + 2:pos + 4]

                    TN = int(TN)

                    # try:
                    #     bitrate = audio.info.bitrate
                    # except:
                    #     bitrate = 0

                    if PERFORMER == "":
                        PERFORMER = MAIN_PERFORMER

                    nt = TrackClass()
                    nt.index = master_count
                    nt.fullpath = filepath.replace('\\', '/')
                    nt.filename = filename
                    nt.parent_folder_path = os.path.dirname(filepath.replace('\\', '/'))
                    nt.parent_folder_name = os.path.splitext(os.path.basename(filepath))[0]
                    nt.file_ext = os.path.splitext(os.path.basename(filepath))[1][1:].upper()

                    nt.album_artist = MAIN_PERFORMER
                    nt.artist = PERFORMER
                    nt.title = TITLE
                    nt.length = LENGTH
                    nt.genre = GENRE
                    nt.bitrate = source_track.bitrate
                    nt.album = ALBUM
                    nt.date = DATE.replace('"', '')
                    nt.track_number = TN
                    nt.start_time = START
                    nt.is_cue = True
                    nt.size = 0 #source_track.size
                    nt.samplerate = source_track.samplerate
                    if TN == 1:
                        nt.size = os.path.getsize(nt.fullpath)

                    pctl.master_library[master_count] = nt

                    cued.append(master_count)
                    loaded_pathes_cache[filepath.replace('\\', '/')] = master_count
                    # added.append(master_count)

                    master_count += 1
                    LENGTH = 0
                    PERFORMER = ""
                    TITLE = ""
                    START = 0
                    TN = 0

            added += reversed(cued)
            cue_list.append(filepath)

        except:
            print("Error in processing CUE file")
            raise

    def add_file(path):
        # bm.get("add file start")
        global master_count
        global DA_Formats
        global to_got
        global auto_play_import

        if os.path.splitext(path)[1][1:] in {"CUE", 'cue'}:
            add_from_cue(path)
            return 0

        if len(path) > 4 and os.path.split(path)[1][-5:].lower() == '.xspf':
            print('found XSPF file at: ' + path)
            load_xspf(path)
            return 0

        if os.path.splitext(path)[1][1:].lower() not in DA_Formats:
            if prefs.auto_extract and os.path.splitext(path)[1][1:].lower() == "zip":
                split = os.path.splitext(path)
                target_dir = split[0]
                print(os.path.getsize(path))
                if os.path.getsize(path) > 2e+9:
                    print("Zip file is large!")
                    show_message("Skipping oversize zip file (>2GB)")
                    return 1
                if not os.path.isdir(target_dir) and not os.path.isfile(target_dir):
                    try:
                        b = to_got
                        to_got = "ex"
                        gui.update += 1
                        zip_ref = zipfile.ZipFile(path, 'r')
                        zip_ref.extractall(target_dir)
                        zip_ref.close()
                    except RuntimeError as e:
                        to_got = b
                        if 'encrypted' in e:
                            show_message("Failed to extract zip archive.", 'warning',
                                         "The archive is encrypted. You'll need to extract it manually with the password.")
                        else:
                            show_message("Failed to extract zip archive.", 'warning',
                                         "Maybe archive is corrupted? Does disk have enough space and have write permission?")
                        return 1
                    except:
                        to_got = b
                        show_message("Failed to extract zip archive.", 'warning',  "Maybe archive is corrupted? Does disk have enough space and have write permission?")
                        return 1

                    upper = os.path.dirname(target_dir)
                    cont = os.listdir(target_dir)
                    new = upper + "/temporaryfolderd"
                    error = False
                    if len(cont) == 1 and os.path.isdir(split[0] + "/" + cont[0]):
                        print("one thing")
                        os.rename(target_dir, new)
                        try:
                            shutil.move(new + "/" + cont[0], upper)
                        except:
                            error = True
                        shutil.rmtree(new)
                        print(new)
                        target_dir = upper + "/" + cont[0]
                        if not os.path.isfile(target_dir):
                            print("ERROR!")

                    if prefs.auto_del_zip and not error:
                        print("Deleting zip file: " + path)
                        os.remove(path)

                    to_got = b
                    gets(target_dir)

            return 1

        to_got += 1
        gui.update = 1

        path = path.replace('\\', '/')

        if path in loaded_pathes_cache:
            de = loaded_pathes_cache[path]
            if pctl.master_library[de].fullpath in cue_list:
                # bm.get("File has an associated .cue file... Skipping")
                return
            added.append(de)
            if auto_play_import:
                pctl.jump(copy.deepcopy(de))

                auto_play_import = False
            # bm.get("dupe track")
            return

        time.sleep(0.002)

        # audio = auto.File(path)

        nt = TrackClass()

        nt.index = master_count
        nt.fullpath = path.replace('\\', '/')
        nt.filename = os.path.basename(path)
        nt.parent_folder_path = os.path.dirname(path.replace('\\', '/'))
        nt.parent_folder_name = get_end_folder(os.path.dirname(path))
        nt.file_ext = os.path.splitext(os.path.basename(path))[1][1:].upper()

        nt = tag_scan(nt)

        if nt.cue_sheet != "":
            cue_scan(nt.cue_sheet, nt)
            del nt

        else:

            pctl.master_library[master_count] = nt
            added.append(master_count)
            master_count += 1

        # bm.get("fill entry")
        if auto_play_import:
            pctl.jump(master_count - 1)
            auto_play_import = False

    def pre_get(direc):
        global DA_Formats
        global to_get

        items_in_dir = os.listdir(direc)
        for q in range(len(items_in_dir)):
            if os.path.isdir(os.path.join(direc, items_in_dir[q])):
                pre_get(os.path.join(direc, items_in_dir[q]))
            if gui.im_cancel:
                return
        for q in range(len(items_in_dir)):
            if os.path.isdir(os.path.join(direc, items_in_dir[q])) is False:
                if os.path.splitext(items_in_dir[q])[1][1:].lower() in DA_Formats:
                    to_get += 1
                    gui.update += 1
            if gui.im_cancel:
                return


    def gets(direc):

        global DA_Formats
        global master_count

        items_in_dir = os.listdir(direc)
        for q in range(len(items_in_dir)):
            if os.path.isdir(os.path.join(direc, items_in_dir[q])):
                gets(os.path.join(direc, items_in_dir[q]))
            if gui.im_cancel:
                return
        for q in range(len(items_in_dir)):
            if os.path.isdir(os.path.join(direc, items_in_dir[q])) is False:

                if os.path.splitext(items_in_dir[q])[1][1:].lower() in DA_Formats:
                    add_file(os.path.join(direc, items_in_dir[q]).replace('\\', '/'))

                elif os.path.splitext(items_in_dir[q])[1][1:] in {"CUE", 'cue'}:
                    add_from_cue(os.path.join(direc, items_in_dir[q]).replace('\\', '/'))
            if gui.im_cancel:
                return

    def cache_paths():
        dic = {}
        for key, value in pctl.master_library.items():
            dic[value.fullpath.replace('\\', '/')] = key
        return dic

    # print(pctl.master_library)

    global transcode_list
    global transcode_state
    global default_player
    global album_art_gen
    global cm_clean_db
    global to_got
    global to_get
    global move_in_progress

    while True:
        time.sleep(0.15)

        # Folder moving
        if len(move_jobs) > 0:
            gui.update += 1
            move_in_progress = True
            job = move_jobs[0]
            del move_jobs[0]

            if job[0].strip("\\/") == job[1].strip("\\/"):
                show_message("Folder copy error.", "info", "The target and source are the same.")
                gui.update += 1
                move_in_progress = False
                continue

            try:
                shutil.copytree(job[0], job[1])
            except:
                move_in_progress = False
                gui.update += 1
                show_message("The folder copy has failed!", 'warning', 'Some files may have been written.')
                continue

            if job[2] == True:
                try:
                    shutil.rmtree(job[0])

                except:
                    show_message("Something has gone horribly wrong!.", 'warning', "Could not delete " + job[0])
                    gui.update += 1
                    move_in_progress = False
                    return


                show_message("Folder move complete.", 'done', "Folder name: " + job[3])
            else:
                show_message("Folder copy complete.", 'done', "Folder name: " + job[3])



            move_in_progress = False
            load_orders.append(job[4])
            gui.update += 1




        # Clean database
        if cm_clean_db is True:
            items_removed = 0
            #old_db = copy.deepcopy(pctl.master_library)
            to_got = 0
            to_get = len(pctl.master_library)

            keys = set(pctl.master_library.keys())
            for index in keys:
                time.sleep(0.0001)
                track = pctl.master_library[index]
                to_got += 1
                if to_got % 100 == 0:
                    gui.update = 1
                if not os.path.isfile(track.fullpath):

                    for playlist in pctl.multi_playlist:
                        while index in playlist[2]:
                            album_dex.clear()
                            playlist[2].remove(index)

                    while index in pctl.track_queue:
                        pctl.track_queue.remove(index)
                        pctl.queue_step -= 1
                    del pctl.master_library[index]
                    items_removed += 1

            cm_clean_db = False
            show_message("Cleaning complete.", 'done', str(items_removed) + " items were removed from the database.")
            if album_mode:
                reload_albums(True)
            if gui.combo_mode:
                reload_albums()
                combo_pl_render.pl_pos_px = 0
                combo_pl_render.prep(True)
            gui.update = 1
            gui.pl_update = 1

        # FOLDER ENC
        if len(transcode_list) > 0:

            try:

                print(8)
                transcode_state = ""
                gui.update += 1

                folder_items = transcode_list[0]

                folder_name = pctl.master_library[folder_items[0]].artist + " - " + pctl.master_library[
                    folder_items[0]].album

                if folder_name == " - ":
                    folder_name = pctl.master_library[folder_items[0]].filename

                "".join([c for c in folder_name if c.isalpha() or c.isdigit() or c == ' ']).rstrip()

                if folder_name[-1:] == ' ':
                    folder_name = pctl.master_library[folder_items[0]].filename

                for c in r'[]/\;,><&*:%=+@!#^()|?^.':
                    folder_name = folder_name.replace(c, '')
                print(folder_name)

                if os.path.isdir(prefs.encoder_output + folder_name):
                    shutil.rmtree(prefs.encoder_output + folder_name)
                    # del transcode_list[0]
                    # continue

                os.makedirs(prefs.encoder_output + folder_name)

                working_folder = prefs.encoder_output + folder_name

                full_wav_out = '"' + prefs.encoder_output + 'output.wav"'
                full_wav_out_p = prefs.encoder_output + 'output.wav'
                full_target_out_p = prefs.encoder_output + 'output.' + prefs.transcode_codec
                full_target_out = '"' + prefs.encoder_output + 'output.' + prefs.transcode_codec + '"'

                if os.path.isfile(full_wav_out_p):
                    os.remove(full_wav_out_p)
                if os.path.isfile(full_target_out_p):
                    os.remove(full_target_out_p)

                if prefs.transcode_mode == 'single':  #  Previously there was a CUE option

                    if prefs.transcode_codec in ('opus', 'ogg', 'flac'):
                        global core_use
                        cores = os.cpu_count()

                        total = len(folder_items)
                        q = 0
                        while True:

                            if core_use < cores and q < len(folder_items):
                                core_use += 1
                                agg = [[folder_items[q], folder_name]]
                                loaderThread = threading.Thread(target=transcode_single, args=agg)
                                loaderThread.daemon = True
                                loaderThread.start()
                                # transcode_single([folder_items[q], folder_name])
                                q += 1
                            time.sleep(0.5)
                            if gui.tc_cancel:
                                while core_use > 0:
                                    time.sleep(1)
                                break
                            if q == len(folder_items) and core_use == 0:
                                break

                    else:
                        for item in folder_items:

                            if os.path.isfile(full_wav_out_p):
                                os.remove(full_wav_out_p)
                            if os.path.isfile(full_target_out_p):
                                os.remove(full_target_out_p)

                            command = user_directory + "/encoder/ffmpeg "

                            if system != 'windows':
                                command = "ffmpeg "

                            if not pctl.master_library[item].is_cue:
                                command += '-i "'
                                command += pctl.master_library[item].fullpath
                                command += '" '
                                command += full_wav_out
                                # command += ' -'
                            else:
                                command += '-ss ' + str(pctl.master_library[item].start_time)
                                command += ' -t ' + str(pctl.master_library[item].length)

                                command += ' -i "'
                                command += pctl.master_library[item].fullpath
                                command += '" '
                                command += full_wav_out

                                # command += " -"

                            transcode_state = "(Decoding)"
                            gui.update += 1

                            print(shlex.split(command))
                            startupinfo = None
                            if system == 'windows':
                                startupinfo = subprocess.STARTUPINFO()
                                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            subprocess.call(shlex.split(command), stdout=subprocess.PIPE, shell=False,
                                            startupinfo=startupinfo)
                            # out = subprocess.popen.communicate(shlex.split(command), stdout=subprocess.PIPE, shell=False,
                            #                 startupinfo=startupinfo)
                            # print(out)

                            print('Done transcoding track via ffmpeg')

                            transcode_state = "(Encoding)"
                            gui.update += 1

                            if prefs.transcode_codec == 'mp3':

                                #print("hit")

                                command = user_directory + '/encoder/lame --silent --abr ' + str(
                                    prefs.transcode_bitrate) + ' '

                                if system != 'windows':
                                    command = 'lame --silent --abr ' + str(prefs.transcode_bitrate) + ' '

                                if pctl.master_library[item].title != "":
                                    command += '--tt "' + pctl.master_library[item].title.replace('"', "").replace("'",

                                                                                                                   "") + '" '

                                if len(str(pctl.master_library[item].track_number)) < 4 and str(
                                        pctl.master_library[item].track_number).isdigit():
                                    command += '--tn ' + str(pctl.master_library[item].track_number) + ' '

                                if len(str(pctl.master_library[item].date)) == 4 and str(
                                        pctl.master_library[item].date).isdigit():
                                    command += '--ty ' + str(pctl.master_library[item].date) + ' '

                                if pctl.master_library[item].artist != "":
                                    command += '--ta "' + pctl.master_library[item].artist.replace('"', "").replace("'",
                                                                                                                    "") + '" '

                                if pctl.master_library[item].album != "":
                                    command += '--tl "' + pctl.master_library[item].album.replace('"', "").replace("'",
                                                                                                                   "") + '" '

                                command += full_wav_out + ' ' + full_target_out

                                print(shlex.split(command))
                                subprocess.call(shlex.split(command), stdout=subprocess.PIPE, startupinfo=startupinfo)
                                print('done')

                                os.remove(full_wav_out_p)
                                output_dir = prefs.encoder_output + folder_name + "/"

                                out_line = os.path.splitext(pctl.master_library[item].filename)[0]
                                if pctl.master_library[item].is_cue:
                                    out_line = str(pctl.master_library[item].track_number) + ". "
                                    out_line += pctl.master_library[item].artist + " - " + pctl.master_library[item].title

                                print(output_dir)
                                shutil.move(full_target_out_p, output_dir + out_line + "." + prefs.transcode_codec)

                                #print(command)

                    output_dir = prefs.encoder_output + folder_name + "/"
                    album_art_gen.save_thumb(folder_items[0], (1080, 1080), output_dir + folder_name)

                del transcode_list[0]
                transcode_state = ""
                gui.update += 1
            except:

                transcode_state = "Transcode Error"
                show_message("Encode failed.", 'warning', "An unknown error was encountered.")
                gui.update += 1
                time.sleep(2)
                del transcode_list[0]

            if len(transcode_list) == 0:
                if gui.tc_cancel:
                    gui.tc_cancel = False
                    show_message("The transcode was canceled before completion.", 'warning', "Incomplete files will remain.")
                else:
                    line = "Press F9 to show output."
                    if prefs.transcode_codec == 'flac':
                        line = "Note that any associated output picture is a thumbnail and not an exact copy."
                    show_message("Encoding complete.", 'done', line)
                    if system == 'linux' and not window_is_focused():

                        g_tc_notify.show()

        while len(to_scan) > 0:
            track = to_scan[0]
            pctl.master_library[track] = tag_scan(pctl.master_library[track])
            del to_scan[0]
            gui.update = 1

        if loaderCommandReady is True:


            for order in load_orders:
                if order.stage == 1:
                    if loaderCommand == LC_Folder:
                        to_get = 0
                        to_got = 0
                        loaded_pathes_cache = cache_paths()
                        pre_get(order.target)
                        gets(order.target)
                    elif loaderCommand == LC_File:
                        loaded_pathes_cache = cache_paths()
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
                    # print('ADDED: ' + str(added))
                    order.tracks = added

                    # Double check for cue dupes
                    for i in reversed(range(len(order.tracks))):
                        if pctl.master_library[order.tracks[i]].fullpath in cue_list:
                            if pctl.master_library[order.tracks[i]].is_cue is False:
                                del order.tracks[i]

                    added = []
                    order.stage = 2
                    loaderCommandReady = False
                    break


worker1Thread = threading.Thread(target=worker1)
worker1Thread.daemon = True
worker1Thread.start()

worker2Thread = threading.Thread(target=worker2)
worker2Thread.daemon = True
worker2Thread.start()


def get_album_info(position):

    if position > len(default_playlist) - 1:
        position -= 1
    current = position


    while position > 0:
        if pctl.master_library[default_playlist[position]].parent_folder_name == pctl.master_library[
                default_playlist[current - 1]].parent_folder_name:
            current -= 1
            continue
        else:
            break

    album = []
    playing = 0
    select = False
    while current < len(default_playlist) - 1:
        album.append(current)
        if len(pctl.track_queue) > 0 and default_playlist[current] == pctl.track_queue[pctl.queue_step]:
            playing = 1
        if current == playlist_selected:
            select = True
        if pctl.master_library[default_playlist[current]].parent_folder_name != pctl.master_library[
                default_playlist[current + 1]].parent_folder_name:
            break
        else:
            current += 1
    if len(album) == 0:
        album = [default_playlist[len(default_playlist) - 1]]
    return playing, album, select


def get_folder_list(index):
    playlist = []

    for item in default_playlist:
        if pctl.master_library[item].parent_folder_name == pctl.master_library[index].parent_folder_name and \
                        pctl.master_library[item].album == pctl.master_library[index].album:
            playlist.append(item)
    return list(set(playlist))




def gal_jump_select(up=False, num=1):
    global playlist_selected
    old_selected = playlist_selected
    old_num = num

    if up is False:
        on = playlist_selected

        while num > 0:
            while on < len(default_playlist) - 1 and pctl.master_library[
                default_playlist[on]].parent_folder_name == pctl.master_library[
                    default_playlist[playlist_selected]].parent_folder_name:
                on += 1
            playlist_selected = on
            num -= 1
    else:
        on = playlist_selected

        while num > 0:

            alb = get_album_info(playlist_selected)

            # if len(alb[1]) == 0:
            #     playlist_selected = len(default_playlist) - 1
            #     return
            if alb[1][0] > -1:
                on = alb[1][0] - 1

            playlist_selected = max(get_album_info(on)[1][0], 0)
            num -= 1

    if old_num > 1 and (playlist_selected >= len(default_playlist) - 1 or playlist_selected == 0):
        playlist_selected = old_selected

def reload_albums(quiet=False):
    global album_dex
    global update_layout
    global album_pos_px
    global old_album_pos

    album_pos_px = old_album_pos

    current_folder = ""
    album_dex = []

    for i in range(len(default_playlist)):
        if i == 0:
            album_dex.append(i)
            current_folder = pctl.master_library[default_playlist[i]].parent_folder_name
        else:
            if pctl.master_library[default_playlist[i]].parent_folder_name != current_folder:
                current_folder = pctl.master_library[default_playlist[i]].parent_folder_name
                album_dex.append(i)

    if quiet is False:
        if album_mode:
            gui.side_panel_size = window_size[0] - 300
            gui.playlist_width = album_playlist_width
        else:
            gui.side_panel_size = old_side_pos

    gui.update += 2
    gui.pl_update = 1
    update_layout = True
    goto_album(pctl.playlist_playing)


# ------------------------------------------------------------------------------------
# WEBSERVER

def webserv():
    if prefs.enable_web is False:

        return 0

    try:
        from flask import Flask, redirect, send_file, abort, request, jsonify, render_template

    except:
        print("Failed to load Flask")
        show_message("Web server failed to start.", 'warning', "Required dependency 'flask' was not found.")
        return 0



    app = Flask(__name__)

    @app.route('/radio/')
    def radio():
        print("Radio Accessed")
        return send_file(install_directory + "/templates/radio.html" )

    @app.route('/radio/radio.js')
    def radiojs():
        return send_file(install_directory + "/templates/radio.js")

    @app.route('/radio/jquery.js')
    def radiojq():
        return send_file(install_directory + "/templates/jquery.js")

    @app.route('/radio/theme.css')
    def radiocss():
        return send_file(install_directory + "/templates/theme.css")


    @app.route('/remote/')
    def remote2():
        if not prefs.allow_remote:
            abort(403)
            return 0
        print("Remote Accessed")
        return send_file(install_directory + "/templates/remote.html")

    @app.route('/remote/theme.css')
    def remotecss():
        return send_file(install_directory + "/templates/theme.css")

    @app.route('/remote/jquery.js')
    def remotejq():
        return send_file(install_directory + "/templates/jquery.js")

    @app.route('/remote/code.js')
    def remotejs():
        return send_file(install_directory + "/templates/code.js")

    @app.route('/remote/update', methods=['GET'])
    def update():
        track = pctl.playing_object()
        if track is not None:
            title = track.title
            artist = track.artist
            if pctl.playing_length > 2:
                position = pctl.playing_time / pctl.playing_length
            else:
                position = 0

        return jsonify(title=title, artist=artist, position=position, index=track.index, shuffle=pctl.random_mode,
                       repeat=pctl.repeat_mode)

    def get_folder_tracks_index(index):
        selection = []
        parent = os.path.normpath(pctl.master_library[index].parent_folder_path)
        for item in default_playlist:
            if parent == os.path.normpath(pctl.master_library[item].parent_folder_path):
                selection.append(item)
        return selection

    def get_album_tracks():
        selection = []
        current_folder = ""
        playing = False

        for i in reversed(range(len(default_playlist))):
            track = pctl.master_library[default_playlist[i]]
            if i == pctl.playlist_playing:
                playing = True
            if i == len(default_playlist) or track.parent_folder_name != current_folder:
                selection.append((track.index, track.artist, track.album, playing))
                current_folder = track.parent_folder_name
                playing = False

        return list(reversed(selection))

    @app.route('/remote/al', methods=['GET'])
    def albumlist():
        if not prefs.allow_remote:
            abort(403)
            return 0
        return jsonify(tracks=get_album_tracks())

    @app.route('/remote/tl', methods=['GET'])
    def tracklist():
        if not prefs.allow_remote:
            abort(403)
            return 0
        playing = pctl.playing_object()
        tracks = []
        if playing is not None:
            for item in get_folder_tracks_index(playing.index):
                track = pctl.master_library[item]
                tracks.append((track.index, track.artist, track.title, track.track_number))

        return jsonify(tracks=tracks)


    @app.route('/remote/getpic', methods=['GET'])
    def get64Pic():
        track = pctl.playing_object()

        if track is not None:
            try:
                index = track.index
                base64 = album_art_gen.get_base64(index, (300, 300)).decode()

                return jsonify(index=index, image=base64, title=track.title, artist=track.artist)
            except:
                return jsonify(index=index, image="None", title=track.title, artist=track.artist)
        else:
            return None

    @app.route('/radio/update_radio', methods=['GET'])
    def update_radio():

        if pctl.broadcast_active:
            track = pctl.master_library[pctl.broadcast_index]
            if track.length > 2:
                position = pctl.broadcast_time / track.length
            else:
                position = 0
            return jsonify(position=position, index=track.index)
        else:
            return jsonify(position=0, index=0)


    @app.route('/radio/getpic', methods=['GET'])
    def get64Pic_radio():

        if pctl.broadcast_active:
            index = pctl.broadcast_index
            track = pctl.master_library[index]


            # Lyrics ---
            lyrics = ""
            if prefs.radio_page_lyrics and track.lyrics != "":
                lyrics = html.escape(track.lyrics).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")

            try:
                index = track.index
                base64 = album_art_gen.get_base64(index, (300, 300)).decode()

                return jsonify(index=index, image=base64, title=track.title, artist=track.artist, lyrics=lyrics)
            except:
                return jsonify(index=index, image="None", title=track.title, artist=track.artist, lyrics=lyrics)
        else:
            return jsonify(index=-1, image="None", title="", artist="- - Broadcast Offline -", lyrics="")

    @app.route('/remote/command', methods=['POST'])
    def get_post_javascript_data():
        if not prefs.allow_remote:
            abort(403)
            return 0
        command = request.form['cmd']
        print(command)
        if command == "Play/Pause":
            if pctl.playing_state == 0 or pctl.playing_state == 2:
                pctl.play()
            else:
                pctl.pause()
        elif command == "Stop":
            pctl.stop()
        elif command == "Next":
            pctl.advance()
        elif command == "Back":
            pctl.back()
        elif command == "Shuffle":
            pctl.random_mode ^= True
        elif command == "Repeat":
            pctl.repeat_mode ^= True
        elif command[:5] == "Seek ":
            value = command[5:]
            try:
                value = float(value)
                if value < 0:
                    value = 0
                if value > 100:
                    value = 100
                pctl.new_time = pctl.playing_length / 100 * value
                pctl.playerCommand = 'seek'
                pctl.playerCommandReady = True
                pctl.playing_time = pctl.new_time
            except Exception as e:
                print(e)

        return command

    @app.route('/remote/jump<int:indexno>', methods=['GET'])
    def jump(indexno):
        if not prefs.allow_remote:
            abort(403)
            return 0
        pctl.jump(indexno)
        return "OK"


    @app.route('/favicon.ico')
    def favicon():
        return send_file(install_directory + "/gui/v2.ico", mimetype='image/vnd.microsoft.icon')

    @app.route('/remote/toggle-broadcast')
    def remote_toggle_broadcast():
        if not prefs.allow_remote:
            abort(403)
            return 0
        toggle_broadcast()
        pctl.join_broadcast = False
        return "Done"

    @app.route('/remote/sync-broadcast')
    def remote_toggle_sync():
        if not prefs.allow_remote:
            abort(403)
            return 0
        pctl.join_broadcast = True
        return "Done"

    @app.route('/remote/pl-up')
    def pl_up():
        if not prefs.allow_remote:
            abort(403)
            return 0
        global playlist_position
        global default_playlist
        playlist_position -= 24
        if playlist_position < 0:
            playlist_position = 0
        return redirect(request.referrer)

    @app.route('/remote/pl-down')
    def pl_down():
        if not prefs.allow_remote:
            abort(403)
            return 0
        global playlist_position
        global default_playlist
        playlist_position += 24
        if playlist_position > len(default_playlist) - 26:
            playlist_position = len(default_playlist) - 25
        return redirect(request.referrer)


    @app.route('/remote/upplaylist')
    def next_playlist():
        if not prefs.allow_remote:
            abort(403)
            return (0)
        switch_playlist(1, True)
        return redirect(request.referrer)

    @app.route('/remote/downplaylist')
    def back_playlist():
        if not prefs.allow_remote:
            abort(403)
            return (0)
        switch_playlist(-1, True)
        return redirect(request.referrer)

    @app.route('/remote/vdown')
    def vdown():
        if not prefs.allow_remote:
            abort(403)
            return (0)

        global pctl
        if pctl.player_volume > 20:
            pctl.player_volume -= 20
        else:
            pctl.player_volume = 0
        pctl.set_volume()

        return redirect(request.referrer)

    @app.route('/remote/vup')
    def vup():
        if not prefs.allow_remote:
            abort(403)
            return (0)
        global pctl
        pctl.player_volume += 20
        if pctl.player_volume > 100:
            pctl.player_volume = 100
        pctl.set_volume()

        return redirect(request.referrer)


    if prefs.expose_web is True:
        app.run(host='0.0.0.0 ', port=prefs.server_port)
    else:
        app.run(port=prefs.server_port)


if prefs.enable_web is True:
    webThread = threading.Thread(target=webserv)
    webThread.daemon = True
    webThread.start()


# --------------------------------------------------------------

def star_line_toggle(mode=0):
    global star_lines

    if mode == 1:
        return star_lines
    star_lines ^= True
    if star_lines:
        gui.show_stars = False
    gui.update += 1
    gui.pl_update = 1

def star_toggle(mode=0):

    if mode == 1:
        return gui.show_stars
    gui.show_stars ^= True
    if gui.show_stars:
        global star_lines
        star_lines = False

    gui.update += 1
    gui.pl_update = 1

def toggle_titlebar_line(mode=0):
    global update_title
    if mode == 1:
        return update_title

    line = window_title
    SDL_SetWindowTitle(t_window, line)
    update_title ^= True
    if update_title:
        update_title_do()

def toggle_scale(mode=0):

    if mode == 1:
        if prefs.ui_scale == 1:
            return False
        else:
            return True

    if prefs.ui_scale == 1:
        prefs.ui_scale = 2
    else:
        prefs.ui_scale = 1

    if prefs.ui_scale != gui.scale:
        show_message("Change will be applied on restart.")

def toggle_borderless(mode=0):
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

        # SDL_SetWindowBordered(t_window, False)
        # SDL_SetWindowBordered(t_window, True)


config_items = [
    ['Show playtime as lines', star_line_toggle],
    ['Show playtime as stars', star_toggle],
]


def toggle_break(mode=0):
    global break_enable
    if mode == 1:
        return break_enable ^ True
    else:
        break_enable ^= True
        gui.pl_update = 1


def toggle_dd(mode=0):
    global dd_index

    if mode == 1:
        return dd_index
    else:
        dd_index ^= True
        gui.pl_update = 1


def toggle_scroll(mode=0):
    global scroll_enable
    global update_layout

    if mode == 1:
        if scroll_enable:
            return False
        else:
            return True

    else:
        scroll_enable ^= True
        gui.pl_update = 1
        update_layout = True


def toggle_follow(mode=0):
    global pl_follow

    if mode == 1:
        return pl_follow
    else:
        pl_follow ^= True
    if pl_follow is True:
        if prefs.end_setting == 'advance' or prefs.end_setting == 'cycle':
            prefs.end_setting = 'stop'


def toggle_append_date(mode=0):
    if mode == 1:
        return prefs.append_date
    prefs.append_date ^= True
    gui.pl_update = 1
    gui.update += 1


def toggle_enable_web(mode=0):
    if mode == 1:
        return prefs.enable_web
    prefs.enable_web ^= True


def toggle_allow_remote(mode=0):
    if mode == 1:
        return prefs.allow_remote #^ True
    prefs.allow_remote ^= True

def toggle_radio_lyrics(mode=0):
    if mode == 1:
        return prefs.radio_page_lyrics
    prefs.radio_page_lyrics ^= True


def toggle_expose_web(mode=0):
    if mode == 1:
        return prefs.expose_web
    prefs.expose_web ^= True
    if prefs.expose_web:
        show_message("Caution! External network connections will be accepted.", 'info', "Leaving this setting enabled may pose security and/or privacy risks.")

def toggle_scrobble_mark(mode=0):
    if mode == 1:
        return prefs.scrobble_mark
    prefs.scrobble_mark ^= True

def toggle_lfm_auto(mode=0):
    if mode == 1:
        return prefs.auto_lfm
    prefs.auto_lfm ^= True



def toggle_cache(mode=0):
    if mode == 1:
        return prefs.cache_gallery
    if not prefs.cache_gallery:
        prefs.cache_gallery = True
        direc = os.path.join(user_directory, 'cache')
        if not os.path.exists(direc):
            os.makedirs(direc)
    else:
        prefs.cache_gallery = False


def toggle_ex_del(mode=0):
    if mode == 1:
        return prefs.auto_del_zip
    prefs.auto_del_zip ^= True
    if prefs.auto_del_zip is True:
        show_message("Caution! This function deletes things!", 'info', "This could result in data loss if the process were to malfunction.")


def toggle_extract(mode=0):
    if mode == 1:
        return prefs.auto_extract
    prefs.auto_extract ^= True
    if prefs.auto_extract is False:
        prefs.auto_del_zip = False


def switch_single(mode=0):
    if mode == 1:
        if prefs.transcode_mode == 'single':
            return True
        else:
            return False
    prefs.transcode_mode = 'single'


def switch_mp3(mode=0):
    if mode == 1:
        if prefs.transcode_codec == 'mp3':
            return True
        else:
            return False
    prefs.transcode_codec = 'mp3'


def switch_ogg(mode=0):
    if mode == 1:
        if prefs.transcode_codec == 'ogg':
            return True
        else:
            return False
    prefs.transcode_codec = 'ogg'


def switch_opus(mode=0):
    if mode == 1:
        if prefs.transcode_codec == 'opus':
            return True
        else:
            return False
    prefs.transcode_codec = 'opus'


def switch_flac(mode=0):
    if mode == 1:
        if prefs.transcode_codec == 'flac':
            return True
        else:
            return False
    prefs.transcode_codec = 'flac'


def toggle_sbt(mode=0):
    if mode == 1:
        return prefs.prefer_bottom_title
    prefs.prefer_bottom_title ^= True

def toggle_bba(mode=0):
    if mode == 1:
        return gui.bb_show_art
    gui.bb_show_art ^= True
    gui.update_layout()

def toggle_use_title(mode=0):
    if mode == 1:
        return prefs.use_title
    prefs.use_title ^= True

def switch_rg_off(mode=0):
    if mode == 1:
        return True if prefs.replay_gain == 0 else False
    prefs.replay_gain = 0

def switch_rg_track(mode=0):
    if mode == 1:
        return True if prefs.replay_gain == 1 else False
    prefs.replay_gain = 1

def switch_rg_album(mode=0):
    if mode == 1:
        return True if prefs.replay_gain == 2 else False
    prefs.replay_gain = 2



# config_items.append(['Hide scroll bar', toggle_scroll])

# config_items.append(['Turn off playlist title breaks', toggle_break])

config_items.append(['Use double digit track indices', toggle_dd])

# config_items.append(['Use custom line format [broken]', toggle_custom_line])

config_items.append(['Always use folder name as title', toggle_use_title])

config_items.append(['Add release year to folder title', toggle_append_date])

config_items.append(['Playback advances to open playlist', toggle_follow])

cursor = "|"
c_time = 0
c_blink = 0
key_shiftr_down = False
key_ctrl_down = False



class Over:
    def __init__(self):

        global window_size

        self.init2done = False
        if gui.scale == 2:
            self.about_image = LoadImageAsset('/gui/2x/v3-a.png')
            self.about_image2 = LoadImageAsset('/gui/2x/v3-b.png')
            self.about_image3 = LoadImageAsset('/gui/2x/v3-c.png')
        else:
            self.about_image = LoadImageAsset('/gui/v3-a.png')
            self.about_image2 = LoadImageAsset('/gui/v3-b.png')
            self.about_image3 = LoadImageAsset('/gui/v3-c.png')

        self.w = 650 * gui.scale
        self.h = 250 * gui.scale
        self.box_x = int(window_size[0] / 2) - int(self.w / 2)
        self.box_y = int(window_size[1] / 2) - int(self.h / 2)
        self.item_x_offset = 130 * gui.scale

        self.current_path = os.path.expanduser('~')
        self.ext_colours = {}
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

        self.tab_active = 2
        self.tabs = [
            #["Folder Import", self.files],
            ["Function", self.funcs],
            ["Audio", self.audio],
            ["Playlist", self.config_v],
            ["View", self.config_b],
            ["Transcode", self.codec_config],
            ["Last.fm", self.last_fm_box],
            ["Stats", self.stats],
            ["About", self.about]
        ]
    def audio(self):


        if default_player == 1:

            y = self.box_y + 35 * gui.scale
            x = self.box_x + 130 * gui.scale

            #draw_text((x, y - 22), "Backend", [130, 130, 130, 255], 12)
            # draw_text((x + 65, y - 22), "Bass Audio Library", [160, 160, 156, 255], 12)
            draw_text((x, y - 22 * gui.scale), "Bass Audio Library", [170, 170, 170, 255], 213)

            y = self.box_y + 70 * gui.scale
            x = self.box_x + 130 * gui.scale

            draw_text((x, y - 22 * gui.scale), "ReplayGain Mode", colours.grey_blend_bg(100), 12)

            y += 7 * gui.scale
            x += 10 * gui.scale

            self.toggle_square(x, y, switch_rg_off, "Off")
            y += 23 * gui.scale
            self.toggle_square(x, y, switch_rg_track, "Track Gain")
            y += 23 * gui.scale
            self.toggle_square(x, y, switch_rg_album, "Album Gain")

            y = self.box_y + 37 * gui.scale
            x = self.box_x + 385 * gui.scale

            draw_text((x, y - 22 * gui.scale), "Set audio output device", [160, 160, 160, 255], 212)
            # draw_text((x + 60, y - 20), "Takes effect on text change", [140, 140, 140, 255], 11)

            for item in pctl.bass_devices:
                rect = (x, y - 1 * gui.scale, 245 * gui.scale, 14)
                #draw.rect_r(rect, [0, 255, 0, 50])

                if self.click and coll_point(mouse_position, rect):
                    pctl.set_device = item[4]
                    pctl.playerCommandReady = True
                    pctl.playerCommand = "setdev"

                line = trunc_line(item[0], 10, 245 * gui.scale)
                if pctl.set_device == item[4]: #item[3] > 0:
                    draw_text((x, y), line, [140, 140, 140, 255], 10)
                else:
                    draw_text((x, y), line, [100, 100, 100, 255], 10)
                y += 14 * gui.scale

            y = self.box_y + 225 * gui.scale
            draw_text((x + 75 * gui.scale, y - 2 * gui.scale), "Settings apply on track change", colours.grey(100), 11)

        elif default_player == 2:

            y = self.box_y + 120 * gui.scale
            x = self.box_x + 375 * gui.scale
            draw_text((x, y - 22 * gui.scale, 2), "Gstreamer", [170, 170, 170, 255], 214)

    def funcs(self):

        x = self.box_x + self.item_x_offset
        y = self.box_y - 10 * gui.scale

        y += 35 * gui.scale
        self.toggle_square(x, y, toggle_enable_web,
                           "Web interface*")

        if toggle_enable_web(1):

            link_pa = draw_linked_text((x + 280 * gui.scale, y), "http://localhost:" + str(prefs.server_port) + "/remote", colours.grey_blend_bg3(190), 12)
            link_rect = [x + 280, y, link_pa[1], 18 * gui.scale]
            fields.add(link_rect)


            link_pa2 = draw_linked_text((x + 280 * gui.scale, y + 21 * gui.scale), "http://localhost:" + str(prefs.server_port) + "/radio", colours.grey_blend_bg3(190), 12)
            link_rect2 = [x + 280 * gui.scale, y + 21 * gui.scale, link_pa2[1], 20 * gui.scale]
            fields.add(link_rect2)

            if coll_point(mouse_position, link_rect):
                if gui.cursor_mode == 0 and not self.click:
                    SDL_SetCursor(cursor_hand)
                    gui.cursor_mode = 1
                if self.click:
                    webbrowser.open(link_pa[2], new=2, autoraise=True)

            elif coll_point(mouse_position, link_rect2):
                if gui.cursor_mode == 0 and not self.click:
                    SDL_SetCursor(cursor_hand)
                    gui.cursor_mode = 1
                if self.click:
                    webbrowser.open(link_pa2[2], new=2, autoraise=True)
            elif gui.cursor_mode == 1:
                gui.cursor_mode = 0
                SDL_SetCursor(cursor_standard)

        y += 25 * gui.scale
        self.toggle_square(x + 10 * gui.scale, y, toggle_expose_web, "Allow external connections*")
        y += 23 * gui.scale
        self.toggle_square(x + 10 * gui.scale, y, toggle_allow_remote, "Allow remote control")
        y += 23 * gui.scale
        self.toggle_square(x + 10 * gui.scale, y, toggle_radio_lyrics, "Show lyrics on radio page")
        #y += 35
        # self.toggle_square(x, y, toggle_transcode, "Track Menu: Transcoding  (Folder to OPUS+CUE)*")
        # self.button(x + 289, y-4, "Open output folder", open_encode_out)

        y -= (23 + 23 + 25) * gui.scale
        x1 = x
        y1 = y + 100 * gui.scale
        x += 280 * gui.scale

        y += 68 * gui.scale
        draw_text((x, y), "Show in track menu:", colours.grey(100), 11)
        y += 23 * gui.scale

        self.toggle_square(x, y, toggle_wiki, "Search artist on Wikipedia")
        y += 23 * gui.scale
        self.toggle_square(x, y, toggle_rym, "Search artist on Sonemic")
        y += 23 * gui.scale
        self.toggle_square(x, y, toggle_gimage, "Search images on Google")
        y += 23 * gui.scale
        self.toggle_square(x, y, toggle_gen, "Search track on Genius")

        x = x1
        y = y1

        y += 10 * gui.scale
        self.toggle_square(x, y, toggle_cache, "Cache gallery to disk")
        y += 25 * gui.scale
        self.toggle_square(x, y, toggle_extract, "Auto extract zip archives")
        y += 23 * gui.scale
        self.toggle_square(x + 10 * gui.scale, y, toggle_ex_del, "Delete archive after extraction")

        y = self.box_y + 220 * gui.scale
        draw_text((x, y - 2 * gui.scale), "* Applies on restart", colours.grey(100), 11)
        self.button(x + 410 * gui.scale, y - 4 * gui.scale, "Open config file", open_config_file)



    def button(self, x, y, text, plug, width=0):

        w = width
        if w == 0:
            w = draw.text_calc(text, 211) + 10 * gui.scale
        rect = (x, y, w, 20 * gui.scale)
        draw.rect_r(rect, colours.alpha_grey(11), True)
        fields.add(rect)
        if coll_point(mouse_position, rect):
            draw.rect_r(rect, [255, 255, 255, 15], True)
            draw_text((x + int(w / 2), rect[1] + 2 * gui.scale, 2), text, colours.grey_blend_bg(200), 211)
            if self.click:
                plug()
        else:
            draw_text((x + int(w / 2), rect[1] + 2 * gui.scale, 2), text, colours.grey_blend_bg(170), 211)

    def toggle_square(self, x, y, function, text):

        le = draw_text((x + 20 * gui.scale, y - 3 * gui.scale), text, colours.grey_blend_bg(170), 12)
        draw.rect((x, y), (12 * gui.scale, 12 * gui.scale), [255, 255, 255, 13], True)
        draw.rect((x, y), (12 * gui.scale, 12 * gui.scale), [255, 255, 255, 16])
        if self.click and coll_point(mouse_position, (x - 10 * gui.scale, y - 3 * gui.scale, le + 30 * gui.scale, 22 * gui.scale)):
            function()
        if function(1):
            draw.rect((x + 3 * gui.scale, y + 3 * gui.scale), (6 * gui.scale, 6 * gui.scale), colours.toggle_box_on, True)

    def last_fm_box(self):

        x = self.box_x + self.item_x_offset
        y = self.box_y + 20 * gui.scale
        draw_text((x + 20 * gui.scale, y - 3 * gui.scale), 'Last.fm account', colours.grey_blend_bg(140), 11)
        if lfm_username != "":
            line = "Current user: " + lfm_username
            draw_text((x + 130 * gui.scale, y - 3 * gui.scale), line, colours.grey_blend_bg(70), 11)

        rect = [x + 20 * gui.scale, y + 40 * gui.scale, 210 * gui.scale, 16 * gui.scale]
        rect2 = [x + 20 * gui.scale, y + 80 * gui.scale, 210 * gui.scale, 16 * gui.scale]
        if self.click:
            if coll_point(mouse_position, rect):
                self.lastfm_input_box = 0

            elif coll_point(mouse_position, rect2):
                self.lastfm_input_box = 1

        if key_tab:
            if self.lastfm_input_box == 0:
                self.lastfm_input_box = 1
            elif self.lastfm_input_box == 1:
                self.lastfm_input_box = 0
            else:
                self.lastfm_input_box = 0

        draw.rect_r(rect, colours.alpha_grey(10), True)
        draw.rect_r(rect2, colours.alpha_grey(10), True)

        bg = alpha_blend(colours.alpha_grey(10), colours.sys_background)

        if last_fm_user_field.text == "":
            draw_text((rect[0] + 9 * gui.scale, rect[1]), "Username", colours.grey_blend_bg(40), 11, bg=bg)
        if last_fm_pass_field.text == "":
            draw_text((rect2[0] + 9 * gui.scale, rect2[1]), "Password", colours.grey_blend_bg(40), 11, bg=bg)

        if self.lastfm_input_box == 0:
            last_fm_user_field.draw(x + 25 * gui.scale, y + 40 * gui.scale, colours.grey_blend_bg(180), active=True, font=12, width=210, click=self.click, selection_height=16)
        else:
            last_fm_user_field.draw(x + 25 * gui.scale, y + 40 * gui.scale, colours.grey_blend_bg(180), False, font=12)

        if self.lastfm_input_box == 1:
            last_fm_pass_field.draw(rect2[0] + 5 * gui.scale, rect2[1] - 1 * gui.scale, colours.grey_blend_bg(180), active=True, secret=True)
        else:
            last_fm_pass_field.draw(rect2[0] + 5 * gui.scale, rect2[1] - 1 * gui.scale, colours.grey_blend_bg(180), False, True)

        if key_return_press:
            self.update_lfm()

        y += 120 * gui.scale

        self.button(x + 50 * gui.scale, y, "Update", self.update_lfm, 65 * gui.scale)
        self.button(x + 130 * gui.scale, y, "Clear", self.clear_lfm, 65 * gui.scale)

        if not prefs.auto_lfm:
            x = self.box_x + 50 * gui.scale + int(self.w / 2)
            y += 85 * gui.scale
            draw_text((x,y, 2), "Events will only be sent once activated from MENU per session", colours.grey_blend_bg(90), 11)

        x = self.box_x + self.item_x_offset + 300 * gui.scale
        y = self.box_y + 20 * gui.scale + 40 * gui.scale

        self.toggle_square(x, y, toggle_lfm_auto, "Auto activate")
        y += 26 * gui.scale

        self.toggle_square(x, y, toggle_scrobble_mark, "Show scrobble marker")


    def clear_lfm(self):
        global lfm_hash
        global lfm_password
        global lfm_username
        lfm_hash = ""
        lfm_password = ""
        lfm_username = ""
        last_fm_user_field.text = ""
        last_fm_pass_field.text = ""
        self.lastfm_input_box = 0

    def update_lfm(self):

        global lfm_password
        global lfm_username
        global lfm_hash
        lfm_password = last_fm_pass_field.text
        lfm_username = last_fm_user_field.text
        lfm_hash = ""
        last_fm_pass_field.text = ""
        self.lastfm_input_box = 3
        # if lastfm.connect() is False:
        #     lfm_password = ""

    def codec_config(self):

        x = self.box_x + self.item_x_offset
        y = self.box_y - 5 * gui.scale

        y += 30 * gui.scale
        self.toggle_square(x, y, toggle_transcode, "Show in track menu")
        self.button(x + 370 * gui.scale, y - 4 * gui.scale, "Open output folder", open_encode_out)


        y += 40 * gui.scale
        self.toggle_square(x, y, switch_flac, "FLAC")
        y += 25 * gui.scale
        self.toggle_square(x, y, switch_opus, "OPUS")
        y += 25 * gui.scale
        self.toggle_square(x, y, switch_ogg, "OGG")
        y += 25 * gui.scale
        self.toggle_square(x, y, switch_mp3, "MP3  [slow, requires Lame]")

        if prefs.transcode_codec != 'flac':
            y += 35 * gui.scale

            prefs.transcode_bitrate = self.slide_control(x, y, "Bitrate", "kbs", prefs.transcode_bitrate, 32, 320, 8)

            y -= 1 * gui.scale
            x += 280 * gui.scale
            if (system == 'windows' and not os.path.isfile(user_directory + '/encoder/ffmpeg.exe')) or (
                    system != 'windows' and shutil.which('ffmpeg') is None):
                draw_text((x, y), "FFMPEG not detected!", [220, 110, 110, 255], 12)



    def config_b(self):

        global album_mode_art_size
        global combo_mode_art_size
        global update_layout

        x = self.box_x + self.item_x_offset - 10 * gui.scale
        y = self.box_y - 5 * gui.scale

        x += 10 * gui.scale
        y += 25 * gui.scale

        draw_text((x, y), "Gallery art size", colours.grey(180), 11)

        x += 110 * gui.scale


        album_mode_art_size = self.slide_control(x, y, None, "px", album_mode_art_size, 100, 400, 10, img_slide_update_gall)

        # ---------------


        x = self.box_x + self.item_x_offset - 10 * gui.scale
        x += 10 * gui.scale
        y += 25 * gui.scale

        draw_text((x, y), "Playlist art size", colours.grey(180), 11)

        x += 110 * gui.scale

        combo_mode_art_size = self.slide_control(x, y, None, "px", combo_mode_art_size, 50, 600, 10, img_slide_update_combo)


        y += 35 * gui.scale

        x = self.box_x + self.item_x_offset
        y1 = y

        draw_text((x, y), "Window", colours.grey_blend_bg(100), 12)
        y += 25 * gui.scale

        self.toggle_square(x, y, toggle_borderless, "Borderless window")

        if system == "linux":
            y += 28 * gui.scale
            self.toggle_square(x, y, toggle_scale, "2x UI scaling")

        y += 28 * gui.scale
        self.toggle_square(x, y, toggle_titlebar_line, "Show playing in titlebar")


        y += 28 * gui.scale
        y += 10 * gui.scale
        self.button(x + 80 * gui.scale, y, "Next Theme (F2)", advance_theme)
        #self.toggle_square(x, y, toggle_sbt, "Prefer track title in bottom panel")
        # ----------

        y = self.box_y - 5 * gui.scale
        x += 270 * gui.scale

        y += 28 * gui.scale


        draw_text((x, y), "Gallery", colours.grey_blend_bg(100), 12)

        y += 28 * gui.scale
        self.toggle_square(x, y, toggle_dim_albums, "Dim gallery when playing")
        y += 28 * gui.scale
        self.toggle_square(x, y, toggle_galler_text, "Show album title in gallery")

        y += 28 * gui.scale
        y += 28 * gui.scale
        draw_text((x, y), "Misc", colours.grey_blend_bg(100), 12)

        y += 28 * gui.scale


        if default_player == 1:
            self.toggle_square(x, y, toggle_level_meter, "Show visualisation")
            y += 28 * gui.scale


        self.toggle_square(x, y, toggle_mini_lyrics, "Show lyrics in side panel")
        y += 28 * gui.scale

        self.toggle_square(x, y, toggle_auto_theme, "Auto theme from album art")

        y += 28 * gui.scale

        #self.button(x, y, "Reset Layout", standard_size)
        #x += 100

        #x -= 100

        #y += 92
        #self.toggle_square(x, y, toggle_bba, "Show album art in bottom panel")

    def about(self):

        x = self.box_x + int(self.w * 0.3) + 65 * gui.scale  # 110 + int((self.w - 110) / 2)
        y = self.box_y + 81 * gui.scale
        gui.win_fore = colours.sys_background

        if pctl.playing_object() is not None and 'dream' in pctl.playing_object().genre.lower():
            self.about_image2.render(x - 100 * gui.scale, y - 10 * gui.scale)
        elif pctl.playing_object() is not None and 'gaze' in pctl.playing_object().genre.lower():
            self.about_image2.render(x - 100 * gui.scale, y - 10 * gui.scale)
        elif pctl.playing_object() is not None and 'ambient' in pctl.playing_object().genre.lower():
            self.about_image3.render(x - 100 * gui.scale, y - 10 * gui.scale)
        else:
            self.about_image.render(x - 100 * gui.scale, y - 10 * gui.scale)
        x += 20 * gui.scale
        y -= 10 * gui.scale

        draw_text((x, y), "Tauon Music Box", colours.grey(200), 216)
        y += 32 * gui.scale
        draw_text((x, y + 1 * gui.scale), t_version, colours.grey(190), 13)
        y += 20 * gui.scale
        draw_text((x, y), "Copyright © 2015-2017 Taiko2k captain.gxj@gmail.com", colours.grey(190), 13)
        y += 21 * gui.scale
        link_pa = draw_linked_text((x, y), "https://github.com/Taiko2k/tauonmb", colours.grey_blend_bg3(190), 12)
        link_rect = [x, y, link_pa[1], 18 * gui.scale]
        if coll_point(mouse_position, link_rect):
            if gui.cursor_mode == 0 and not self.click:
                SDL_SetCursor(cursor_hand)
                gui.cursor_mode = 1
            if self.click:
                webbrowser.open(link_pa[2], new=2, autoraise=True)
        elif gui.cursor_mode == 1:
            gui.cursor_mode = 0
            SDL_SetCursor(cursor_standard)
        fields.add(link_rect)

        x = self.box_x + self.w - 115 * gui.scale
        y = self.box_y + self.h - 35 * gui.scale

        self.button(x, y, "License + Credits", open_license)

    def stats(self):

        x = self.box_x + self.item_x_offset - 10 * gui.scale
        y = self.box_y - 10 * gui.scale

        x1 = x + (8 + 10 + 10) * gui.scale
        x2 = x1 + 120 * gui.scale
        y1 = y + 40 * gui.scale

        draw_text((x1, y1), "Tracks in playlist", colours.grey_blend_bg(100), 12)
        draw_text((x2, y1), '{:,}'.format(len(default_playlist)), colours.grey_blend_bg(190), 12)
        y1 += 20 * gui.scale

        draw_text((x1, y1), "Playlist length", colours.grey_blend_bg(100), 12)

        playlist_time = 0
        for item in default_playlist:
            playlist_time += pctl.master_library[item].length

        line = str(datetime.timedelta(seconds=int(playlist_time)))

        draw_text((x2, y1), line, colours.grey_blend_bg(190), 12)
        y1 += 35 * gui.scale
        draw_text((x1, y1), "Tracks in database", colours.grey_blend_bg(100), 12)
        draw_text((x2, y1), '{:,}'.format(len(pctl.master_library)), colours.grey_blend_bg(190), 12)
        y1 += 20 * gui.scale
        draw_text((x1, y1), "Total playtime", colours.grey_blend_bg(100), 12)
        draw_text((x2, y1), str(datetime.timedelta(seconds=int(pctl.total_playtime))),
                  colours.grey_blend_bg(190), 14)



        # Ratio bar
        if len(pctl.master_library) > 110 * gui.scale:
            x = self.box_x + 110 * gui.scale
            y = self.box_y + self.h - 7 * gui.scale

            full_rect = [x, y, self.w - 110 * gui.scale + 0, 7 * gui.scale]
            d = 0

            # Stats
            if self.last_db_size != len(pctl.master_library):
                self.last_db_size = len(pctl.master_library)
                self.ext_ratio = {}
                for key, value in pctl.master_library.items():
                    if value.file_ext in self.ext_ratio:
                        self.ext_ratio[value.file_ext] += 1
                    else:
                        self.ext_ratio[value.file_ext] = 1

            for key, value in self.ext_ratio.items():

                colour = [200, 200, 200 ,255]
                if key in format_colours:
                    colour = format_colours[key]

                colour = colorsys.rgb_to_hls(colour[0] / 255, colour[1] / 255, colour[2] / 255)
                colour = colorsys.hls_to_rgb(1 - colour[0], colour[1] * 0.8, colour[2] * 0.8)
                colour = [int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255), 255]

                h = int(round(value / len(pctl.master_library) * full_rect[2]))
                block_rect = [full_rect[0] + d, full_rect[1], h, full_rect[3]]


                draw.rect_r(block_rect, colour, True)
                d += h

                block_rect = (block_rect[0], block_rect[1], block_rect[2] - 1, block_rect[3])
                fields.add(block_rect)
                if coll_point(mouse_position, block_rect):
                    xx = block_rect[0] + int(block_rect[2] / 2)
                    if xx < x + 30 * gui.scale:
                        xx = x + 30 * gui.scale
                    if xx > self.box_x + self.w - 30 * gui.scale:
                        xx = self.box_x + self.w - 30 * gui.scale
                    draw_text((xx, self.box_y + self.h - 35 * gui.scale, 2), key, colours.grey_blend_bg(190), 13)


    def config_v(self):

        w = 370 * gui.scale
        h = 220 * gui.scale
        x = self.box_x + self.item_x_offset
        y = self.box_y

        # x += 8
        y += 25 * gui.scale
        y2 = y
        x2 = x
        for k in config_items:
            draw_text((x + 20 * gui.scale, y - 3 * gui.scale), k[0], colours.grey_blend_bg(170), 12)
            draw.rect((x, y), (12 * gui.scale, 12 * gui.scale), [255, 255, 255, 13], True)
            draw.rect((x, y), (12 * gui.scale, 12 * gui.scale), [255, 255, 255, 16])
            if self.click and coll_point(mouse_position, (x - 20, y - 5, 220, 24)):
                k[1]()
            if k[1](1) is True:
                draw.rect((x + 3 * gui.scale, y + 3 * gui.scale), (6 * gui.scale, 6 * gui.scale), colours.toggle_box_on, True)

            y += 25 * gui.scale

            if y - y2 > 190 * gui.scale:
                y = y2
                x += 205 * gui.scale


        y = self.box_y + 25 * gui.scale
        x = self.box_x + self.item_x_offset + 270 * gui.scale

        #y += 20

        prefs.playlist_font_size = self.slide_control(x, y, "Font Size", "", prefs.playlist_font_size, 12, 17)
        y += 25 * gui.scale
        prefs.playlist_row_height = self.slide_control(x, y, "Row Size", "px", prefs.playlist_row_height, 15, 45)
        y += 25 * gui.scale

        x += 65 * gui.scale
        self.button(x, y, "Default", self.small_preset, 124 * gui.scale)
        # x += 90
        # self.button(x, y, "Large Preset", self.large_preset, 80)

        y += 50 * gui.scale
        x -= 90 * gui.scale

        draw_text((x, y), "End of playlist action", colours.grey_blend_bg(100), 12)

        y += 25 * gui.scale
        self.toggle_square(x, y, self.set_playlist_stop, "Stop playback")
        y += 25 * gui.scale
        self.toggle_square(x, y, self.set_playlist_repeat, "Repeat playlist")
        #y += 25
        y -= 25 * gui.scale
        x += 120 * gui.scale
        self.toggle_square(x, y, self.set_playlist_advance, "Play next playlist")
        y += 25 * gui.scale
        self.toggle_square(x, y, self.set_playlist_cycle, "Cycle all playlists")

    def set_playlist_cycle(self, mode=0):
        if mode == 1:
            return True if prefs.end_setting == "cycle" else False
        prefs.end_setting = 'cycle'
        global pl_follow
        pl_follow = False

    def set_playlist_advance(self, mode=0):
        if mode == 1:
            return True if prefs.end_setting == "advance" else False
        prefs.end_setting = 'advance'
        global pl_follow
        pl_follow = False

    def set_playlist_stop(self, mode=0):
        if mode == 1:
            return True if prefs.end_setting == "stop" else False
        prefs.end_setting = 'stop'

    def set_playlist_repeat(self, mode=0):
        if mode == 1:
            return True if prefs.end_setting == "repeat" else False
        prefs.end_setting = 'repeat'


    def small_preset(self):

        prefs.playlist_row_height = 20 * gui.scale
        prefs.playlist_font_size = 15
        gui.update_layout()

    def large_preset(self):

        prefs.playlist_row_height = 31 * gui.scale
        prefs.playlist_font_size = 13
        gui.update_layout()

    def slide_control(self, x, y, label, units, value, lower_limit, upper_limit, step=1, callback=None):

        if label is not None:
            draw_text((x, y), label, colours.grey_blend_bg(170), 12)
            x += 65 * gui.scale
        y += 1 * gui.scale
        rect = (x, y, 33 * gui.scale, 15 * gui.scale)
        fields.add(rect)
        draw.rect_r(rect, [255, 255, 255, 20], True)
        abg = colours.grey(80)
        if coll_point(mouse_position, rect):

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

        dec_arrow.render(x + 1 * gui.scale, y, abg)

        x += 33 * gui.scale

        draw.rect_r((x, y, 58 * gui.scale, 15 * gui.scale), [255, 255, 255, 9], True)
        draw_text((x + 29 * gui.scale, y, 2), str(value) + units, colours.grey(180), 11)

        x += 58 * gui.scale

        rect = (x, y, 33 * gui.scale, 15 * gui.scale)
        fields.add(rect)
        draw.rect_r(rect, [255, 255, 255, 20], True)
        abg = colours.grey(80)
        if coll_point(mouse_position, rect):

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

        inc_arrow.render(x + 1 * gui.scale, y, abg)

        return value


    def style_up(self):
        prefs.line_style += 1
        if prefs.line_style > 5:
            prefs.line_style = 1

    def inside(self):

        return coll_point(mouse_position, (self.box_x, self.box_y, self.w, self.h))

    def init2(self):

        self.init2done = True

        pctl.total_playtime = star_store.get_total()

        # Files
        if len(self.drives) < 1 and system == 'windows':
            raw_drives = win32api.GetLogicalDriveStrings()
            self.drives = raw_drives.split('\000')[:-1]

    def render(self):

        if self.init2done is False:
            self.init2()

        if key_esc_press:
            self.enabled = False
            fader.fall()

        self.box_x = int(window_size[0] / 2) - int(self.w / 2)
        self.box_y = int(window_size[1] / 2) - int(self.h / 2)

        draw.rect((self.box_x - 5 * gui.scale, self.box_y - 5 * gui.scale), (self.w + 10 * gui.scale, self.h + 10 * gui.scale), colours.grey(50), True)
        draw.rect((self.box_x, self.box_y), (self.w, self.h), colours.sys_background, True)
        draw.rect((self.box_x, self.box_y), (110 * gui.scale, self.h), colours.sys_background_2, True)

        # draw.rect((self.box_x - 1, self.box_y - 1), (self.w + 2, self.h + 2), colours.grey(50))

        # temp
        if len(self.drives) < 1 and system == 'windows':
            raw_drives = win32api.GetLogicalDriveStrings()
            self.drives = raw_drives.split('\000')[:-1]

        current_tab = 0
        for item in self.tabs:

            if self.click and gui.message_box:
                gui.message_box = False

            box = [self.box_x, self.box_y + (current_tab * 30 * gui.scale), 110 * gui.scale, 30 * gui.scale]
            box2 = [self.box_x, self.box_y + (current_tab * 30 * gui.scale), 110 * gui.scale, 29 * gui.scale]
            fields.add(box2)
            # draw.rect_r(box, colours.tab_background, True)

            if self.click and coll_point(mouse_position, box2):
                self.tab_active = current_tab

            if current_tab == self.tab_active:
                colour = copy.deepcopy(colours.sys_tab_hl)
                #colour[3] = 190
                gui.win_fore = colour
                draw.rect_r(box, colour, True)
            else:
                gui.win_fore = colours.sys_tab_bg
                draw.rect_r(box, colours.sys_tab_bg, True)

            if coll_point(mouse_position, box2):
                draw.rect_r(box, [255, 255, 255, 10], True)

            # draw_text((box[0] + 55, box[1] + 7, 2), item[0], [200, 200, 200, 200], 12)
            if current_tab == self.tab_active:
                draw_text((box[0] + 55 * gui.scale, box[1] + 6 * gui.scale, 2), item[0], alpha_blend([240, 240, 240, 240], gui.win_fore), 213)
            else:
                draw_text((box[0] + 55 * gui.scale, box[1] + 6 * gui.scale, 2), item[0], alpha_blend([240, 240, 240, 100], gui.win_fore), 213)

            current_tab += 1

        # draw.line(self.box_x + 110, self.box_y + 1, self.box_x + 110, self.box_y + self.h, colours.grey(50))

        self.tabs[self.tab_active][1]()

        self.click = False
        self.right_click = False

        gui.win_fore = colours.sys_background




class Fields:
    def __init__(self):

        self.id = []
        self.last_id = []

        self.field_array = []
        self.force = False

    def add(self, rect):

        self.field_array.append(rect)

    def test(self):

        if self.force:
            self.force = False
            return True

        self.last_id = self.id
        # print(len(self.id))
        self.id = []

        for f in self.field_array:
            if coll_point(mouse_position, f):
                self.id.append(1)  # += "1"
            else:
                self.id.append(0)  # += "0"

        if self.last_id == self.id:
            return False

        else:
            return True

    def clear(self):

        self.field_array = []


fields = Fields()

pref_box = Over()


if gui.scale == 2:
    inc_arrow = WhiteModImageAsset("/gui/2x/inc.png")
    dec_arrow = WhiteModImageAsset("/gui/2x/dec.png")
    corner_icon = WhiteModImageAsset("/gui/2x/corner.png")
else:
    inc_arrow = WhiteModImageAsset("/gui/inc.png")
    dec_arrow = WhiteModImageAsset("/gui/dec.png")
    corner_icon = WhiteModImageAsset("/gui/corner.png")

# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------

class TopPanel:
    def __init__(self):

        self.height = gui.panelY
        self.ty = 0

        self.start_space_left = 8 * gui.scale
        self.start_space_compact_left = 25 * gui.scale

        self.tab_text_font = fonts.tabs #211 # 211
        self.tab_extra_width = 17 * gui.scale
        self.tab_text_start_space = 8 * gui.scale
        self.tab_text_y_offset = 8 * gui.scale
        self.tab_spacing = 0

        # if gui.scale > 1:
        #     self.tab_text_y_offset += 8

        self.ini_menu_space = 18 * gui.scale
        self.menu_space = 13 * gui.scale
        self.click_buffer = 4 * gui.scale

        # ---
        self.space_left = 0
        self.tab_hold = False  # !!
        self.tab_text_spaces = []
        self.tab_hold_index = 0
        self.index_playing = -1
        self.playing_title = ""
        self.drag_zone_start_x = 300 * gui.scale

        if gui.scale == 2:
            self.exit_button = WhiteModImageAsset('/gui/2x/ex.png')
        else:
            self.exit_button = WhiteModImageAsset('/gui/ex.png')

        self.adds = []

    def render(self):

        # C-TD
        global quick_drag
        global playlist_panel

        if quick_drag is True:
            gui.pl_update = 1

        # Draw the background
        draw.rect_r((0, 0, window_size[0], self.height + self.ty), colours.top_panel_background, True)

        # ?
        if self.tab_hold:
            drag_mode = False

        # Need to test length
        self.tab_text_spaces = []
        left_space_es = 0
        for i, item in enumerate(pctl.multi_playlist):
            le = draw.text_calc(pctl.multi_playlist[i][0], self.tab_text_font)
            self.tab_text_spaces.append(le)
            left_space_es += le + self.tab_extra_width + self.tab_spacing

        x = self.start_space_left
        y = self.ty


        # Calculate position for playing text and text
        offset = 15
        if draw_border:
            offset += 61
        if gui.turbo:
            offset += 90
            if gui.vis == 3:
                offset += 57

        # Generate title text if applicable
        if len(pctl.track_queue) > 0:
            index = pctl.track_queue[pctl.queue_step]
            if index != self.index_playing:
                line = ""
                title = pctl.master_library[index].title
                artist = pctl.master_library[index].artist
                if artist != "":
                    line += artist
                if title != "":
                    if line != "":
                        line += " - "
                    line += title
                line = trunc_line(line, 12, window_size[0] - offset - 290)
                self.playing_title = line
        else:
            self.playing_title = ""

        if pctl.playing_state < 3:
            p_text = self.playing_title
        else:
            p_text = pctl.tag_meta

        if pctl.playing_state > 0 and not pctl.broadcast_active and window_size[0] < 820:
            p_text_len = draw.text_calc(p_text, 11)
        else:
            p_text_len = 0

        right_space_es = p_text_len + offset

        if loading_in_progress or len(transcode_list) > 0 or pctl.broadcast_active:
            left_space_es += 300

        if window_size[0] - right_space_es - left_space_es < 190:
            draw_alt = True
        else:
            draw_alt = False

        if draw_alt:
            x = self.start_space_compact_left

        x_start = x

        # TAB INPUT PROCESSING
        for i, tab in enumerate(pctl.multi_playlist):

            if len(pctl.multi_playlist) != len(self.tab_text_spaces):
                break

            if draw_alt and i != pctl.playlist_active:
                continue

            tab_width = self.tab_text_spaces[i] + self.tab_extra_width

            # Detect mouse over and add tab to mouse over detection
            f_rect = [x, y + 1, tab_width - 1, self.height - 1]
            tab_hit = coll_point(mouse_position, f_rect)

            # Tab functions
            if tab_hit:

                # Click to change playlist
                if input.mouse_click:
                    gui.pl_update = 1
                    self.tab_hold = True
                    self.tab_hold_index = i
                    switch_playlist(i)

                # Drag to move playlist
                if mouse_up and i != self.tab_hold_index and self.tab_hold is True:

                    if key_shift_down:
                        pctl.multi_playlist[i][2] += pctl.multi_playlist[self.tab_hold_index][2]
                        pctl.playlist_backup = copy.deepcopy(pctl.multi_playlist[self.tab_hold_index])
                        delete_playlist(self.tab_hold_index)
                    else:
                        move_playlist(self.tab_hold_index, i)
                    self.tab_hold = False

                # Delete playlist on wheel click
                elif tab_menu.active is False and middle_click:
                    delete_playlist(i)
                    break

                # Activate menu on right click
                elif right_click:
                    tab_menu.activate(copy.deepcopy(i))

                # Quick drop tracks (red plus sign to indicate)
                elif quick_drag is True:
                    if mouse_up:
                        quick_drag = False
                        for item in shift_selection:
                            pctl.multi_playlist[i][2].append(default_playlist[item])
                        if len(shift_selection) > 0:
                            self.adds.append([pctl.multi_playlist[i][6], len(shift_selection), Timer()]) # ID, num, timer

            x += tab_width + self.tab_spacing

        x = x_start

        # Need to test length again
        self.tab_text_spaces = []
        left_space_es = 0
        for i, item in enumerate(pctl.multi_playlist):
            le = draw.text_calc(pctl.multi_playlist[i][0], self.tab_text_font)
            self.tab_text_spaces.append(le)
            left_space_es += le + self.tab_extra_width + self.tab_spacing

        # TAB DRAWING
        for i, tab in enumerate(pctl.multi_playlist):

            if len(pctl.multi_playlist) != len(self.tab_text_spaces):
                break

            if draw_alt and i != pctl.playlist_active:
                continue

            tab_width = self.tab_text_spaces[i] + self.tab_extra_width
            rect = [x, y, tab_width, self.height]

            # Detect mouse over and add tab to mouse over detection
            f_rect = [x, y + 1, tab_width - 1, self.height - 1]
            fields.add(f_rect)
            tab_hit = coll_point(mouse_position, f_rect)
            playing_hint = False
            active = False

            # Determine tab background colour
            if i == pctl.playlist_active:
                bg = colours.tab_background_active
                active = True
            elif (tab_menu.active is True and tab_menu.reference == i) or tab_menu.active is False and tab_hit and not self.tab_hold:
                bg = colours.tab_highlight
            elif i == pctl.active_playlist_playing:
                bg = colours.tab_background
                playing_hint = True
            else:
                bg = colours.tab_background

            # Draw tab background
            draw.rect_r(rect, bg, True)
            if playing_hint:
                draw.rect_r(rect, [255, 255, 255, 7], True)

            # Determine text colour
            if active:
                fg = colours.tab_text_active
            else:
                fg = colours.tab_text

            # Draw tab text
            draw_text((x + self.tab_text_start_space, y + self.tab_text_y_offset), tab[0], fg, self.tab_text_font, bg=bg)

            # Drop pulse
            if gui.pl_pulse and playlist_target == i:
                    if tab_pulse.render(x, y + self.height - 2, tab_width, 2, r=200, g=130) is False:
                        gui.pl_pulse = False

            # Drag to move playlist
            if tab_hit:
                if mouse_down and i != self.tab_hold_index and self.tab_hold is True:

                    if key_shift_down:
                        draw.rect_r((x, y + self.height - 2, tab_width, 2), [80, 160, 200, 255], True)
                    else:
                        if self.tab_hold_index < i:
                            draw.rect_r((x + tab_width - 2, y, 2, gui.panelY), [80, 160, 200, 255], True)
                        else:
                            draw.rect_r((x, y, 2, gui.panelY), [80, 160, 200, 255], True)

                elif quick_drag is True:
                    draw.rect_r((x, y + self.height - 2, tab_width, 2), [80, 200, 180, 255], True)

            if len(self.adds) > 0:
                for k in reversed(range(len(self.adds))):
                    if pctl.multi_playlist[i][6] == self.adds[k][0]:
                        if self.adds[k][2].get() > 0.3:
                            del self.adds[k]
                        else:
                            ay = y + 4
                            ay -= 6 * self.adds[k][2].get() / 0.3

                            draw_text((x + tab_width - 3, int(round(ay)), 1), '+' + str(self.adds[k][1]), [244, 212, 66, 255], 212)
                            gui.update += 1




            x += tab_width + self.tab_spacing

        # Quick drag single track onto bar to create new playlist
        if quick_drag and mouse_position[0] > x and mouse_position[1] < gui.panelY and quick_d_timer.get() > 1:
            #draw_text((x + 5, y - 3), '+', [200, 20, 40, 255], 12)
            draw.rect_r((x, y, 2, gui.panelY), [80, 200, 180, 255], True)

            if mouse_up:
                pl = new_playlist(False)
                for item in shift_selection:
                    pctl.multi_playlist[pl][2].append(default_playlist[item])

        # -------------
        # Other input
        if mouse_up:
            quick_drag = False
            self.tab_hold = False

        # Scroll anywhere on panel to change playlist
        if mouse_wheel != 0 and mouse_position[1] < self.height + 1 and len(pctl.multi_playlist) > 1:
            switch_playlist(mouse_wheel * -1, True)
            gui.pl_update = 1



        # ---------
        # Menu Bar

        x += self.ini_menu_space
        y += 8 * gui.scale
        #y += 7


        gui.win_fore = colours.top_panel_background

        # PLAYLIST -----------------------
        if draw_alt:
            word = "PLAYLIST"
            word_length = draw.text_calc(word, 212)
            rect = [x - self.click_buffer, self.ty + 1, word_length + self.click_buffer * 2, self.height - 1]
            hit = coll_point(mouse_position, rect)
            fields.add(rect)

            if hit and input.mouse_click:
                playlist_panel ^= True

            if playlist_panel or hit:
                bg = colours.status_text_over
            else:
                bg = colours.status_text_normal
            draw_text((x, y), word, bg, 212)
            x += self.menu_space + word_length

        # MENU -----------------------------

        word = "MENU"
        word_length = draw.text_calc(word, 212)
        rect = [x - self.click_buffer, self.ty + 1, word_length + self.click_buffer * 2, self.height - 1]
        hit = coll_point(mouse_position, rect)
        fields.add(rect)

        if hit and view_box.active:
            view_box.active = False
            x_menu.activate(position=(x + 12, self.height))
            gui.update += 1

        if hit and input.mouse_click:
            if x_menu.active:
                x_menu.active = False
            else:
                x_menu.activate(position=(x + 12, self.height))

        if x_menu.active or hit:
            bg = colours.status_text_over
        else:
            bg = colours.status_text_normal
        draw_text((x, y), word, bg, 212)

        # LAYOUT --------------------------------
        x += self.menu_space + word_length
        word = "VIEW"
        word_length = draw.text_calc(word, 12)
        rect = [x - self.click_buffer + 6, self.ty + 1, word_length - 6 + self.click_buffer * 2, self.height - 1 - 4]
        hit = coll_point(mouse_position, rect)
        fields.add(rect)

        if hit and x_menu.active:
            x_menu.active = False
            #view_menu.activate(position=(x + 12, self.height))
            view_box.activate(x - 80 * gui.scale)
            gui.update += 1

        if hit and input.mouse_click:
            if view_box.active:
                view_box.active = False
            else:
                view_box.activate(x - 80 * gui.scale)
            # if view_menu.active:
            #     view_menu.active = False
            # else:
            #     view_menu.activate(position=(x + 12, self.height))

        if view_menu.active or hit:
            bg = colours.status_text_over
        else:
            bg = colours.status_text_normal
        draw_text((x, y), word, bg, 212)

        # Status text
        x += self.menu_space + word_length + 5
        self.drag_zone_start_x = x
        status = True

        if loading_in_progress:

            bg = colours.status_info_text
            if to_got == 'xspf':
                text = "Importing XSPF playlist"
            elif to_got == 'xspfl':
                text = "Importing XSPF playlist. May take a while."
            elif to_got == 'ex':
                text = "Extracting Archive..."
            else:
                text = "Importing...  " + str(to_got) + "/" + str(to_get)
                if right_click and coll_point(mouse_position, [x, y, 180 * gui.scale, 18 * gui.scale]):
                    cancel_menu.activate(position=(x + 20 * gui.scale, y + 23 * gui.scale))
        elif move_in_progress:
            text = "File copy in progress..."
            bg = colours.status_info_text
        elif cm_clean_db and to_get > 0:
            per = str(int(to_got / to_get * 100))
            text = "Cleaning db...  " + per + "%"
            bg = [100, 200, 100, 255]
        elif len(to_scan) > 0:
            text = "Rescanning Tags...  " + str(len(to_scan)) + " Tracks Remaining"
            bg = [100, 200, 100, 255]
        elif transcode_list:
            # if key_ctrl_down and key_c_press:
            #     del transcode_list[1:]
            #     gui.tc_cancel = True
            if right_click and coll_point(mouse_position, [x, y, 180 * gui.scale, 18 * gui.scale]):
                cancel_menu.activate()

            text = "Transcoding... " + str(len(transcode_list)) + " Folder Remaining " + transcode_state
            if len(transcode_list) > 1:
                text = "Transcoding... " + str(len(transcode_list)) + " Folders Remaining " + transcode_state
            if not gui.tc_cancel:
                bg = colours.status_info_text
            else:
                text = "Stopping transcode..."
        elif pctl.join_broadcast and pctl.broadcast_active:
            text = "Streaming Synced"
            bg = [60, 75, 220, 255]  # colours.streaming_text
        elif pctl.encoder_pause == 1 and pctl.broadcast_active:
            text = "Streaming Paused"
            bg = colours.streaming_text
        else:
            status = False


        if status:
            x += draw_text((x, y), text, bg, 11)
            # x += draw.text_calc(text, 11)

        elif pctl.broadcast_active:
            text = "Now Streaming:"
            draw_text((x, y), text, [95, 110, 230, 255], 11) # [70, 85, 230, 255]
            x += draw.text_calc(text, 11) + 6

            text = pctl.master_library[pctl.broadcast_index].artist + " - " + pctl.master_library[
                pctl.broadcast_index].title
            trunc = window_size[0] - x - 150
            text = trunc_line(text, 11, trunc)
            draw_text((x, y), text, colours.grey(130), 11)
            x += draw.text_calc(text, 11) + 6

            x += 7
            progress = int(pctl.broadcast_time / int(pctl.master_library[pctl.broadcast_index].length) * 100)
            draw.rect((x, y + 4), (progress, 9), [65, 80, 220, 255], True)
            draw.rect((x, y + 4), (100, 9), colours.grey(30))

            if input.mouse_click and coll_point(mouse_position, (x, y, 90, 11)):
                newtime = ((mouse_position[0] - x) / 100) * pctl.master_library[pctl.broadcast_index].length
                pctl.broadcast_time = newtime
                pctl.playerCommand = 'encseek'
                pctl.playerCommandReady = True


            x += 110
            draw_text((x, y), str(len(pctl.broadcast_clients)), [70, 85, 230, 255], 11)

            self.drag_zone_start_x = x + 21

            if input.mouse_click and coll_point(mouse_position, (x-5, y-5, 20, 24)):
                line = ""
                input.mouse_click = False
                for client in pctl.broadcast_clients:
                    line += client.split(":")[0] + "  "

                if len(pctl.broadcast_clients) == 0:
                    show_message("There are currently no connected clients")
                elif len(pctl.broadcast_clients) == 1:
                    show_message("There is " + str(len(pctl.broadcast_clients)) + " inbound connection.", 'info',
                                 line)
                else:
                    show_message("There are " + str(len(pctl.broadcast_clients)) + " inbound connections.", 'info', line)



        if pctl.playing_state > 0 and not pctl.broadcast_active and gui.show_top_title:
            draw_text2((window_size[0] - offset, y - 1, 1), p_text, colours.side_bar_line1, 12,
                       window_size[0] - offset - x)


top_panel = TopPanel()


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

        if gui.scale == 2:
            self.play_button = WhiteModImageAsset('/gui/2x/play.png')
            self.forward_button = WhiteModImageAsset('/gui/2x/ff.png')
            self.back_button = WhiteModImageAsset('/gui/2x/bb.png')
        else:

            self.play_button = WhiteModImageAsset('/gui/play.png')
            self.forward_button = WhiteModImageAsset('/gui/ff.png')
            self.back_button = WhiteModImageAsset('/gui/bb.png')


        self.scrob_stick = 0

    # def set_mode2(self):
    #
    #     self.volume_bar_size[1] = 12
    #     self.seek_bar_position[0] = 0
    #     self.seek_bar_size[0] = window_size[0]
    #     self.seek_bar_size[1] = 12
    #     self.control_line_bottom = 27
    #     self.mode = 1
    #     self.update()

    def update(self):

        if self.mode == 0:
            self.volume_bar_position[0] = window_size[0] - (210 * gui.scale)
            self.volume_bar_position[1] = window_size[1] - (27 * gui.scale)
            self.seek_bar_position[1] = window_size[1] - gui.panelBY
            self.seek_bar_size[0] = window_size[0] - (300 * gui.scale)
            self.seek_bar_position[0] = 300 * gui.scale
            if gui.bb_show_art:
                self.seek_bar_position[0] = 300 + gui.panelBY
                self.seek_bar_size[0] = window_size[0] - 300 - gui.panelBY

        # elif self.mode == 1:
        #     self.volume_bar_position[0] = window_size[0] - 210
        #     self.volume_bar_position[1] = window_size[1] - 27
        #     self.seek_bar_position[1] = window_size[1] - gui.panelBY
        #     self.seek_bar_size[0] = window_size[0]

    def render(self):

        global volume_store
        global clicked
        global right_click

        draw.rect((0, window_size[1] - gui.panelBY), (window_size[0], gui.panelBY), colours.bottom_panel_colour, True)

        draw.rect(self.seek_bar_position, self.seek_bar_size, colours.seek_bar_background, True)


        right_offset = 0
        if gui.display_time_mode == 2:
            right_offset = 22 * gui.scale

        # if gui.light_mode:
        #     draw.line(0, window_size[1] - gui.panelBY, window_size[0], window_size[1] - gui.panelBY, colours.art_box)

        #FRAME
        # if gui.draw_frame:
        #     draw.line(0, window_size[1] - gui.panelBY, 299, window_size[1] - gui.panelBY, colours.bb_line)
        #     draw.line(299, window_size[1] - gui.panelBY, 299, window_size[1] - gui.panelBY + self.seek_bar_size[1],
        #               colours.bb_line)
        #     draw.line(300, window_size[1] - gui.panelBY + self.seek_bar_size[1], window_size[0],
        #               window_size[1] - gui.panelBY + self.seek_bar_size[1], colours.bb_line)

        # rect = [0, window_size[1] - gui.panelBY, self.seek_bar_position[0], gui.panelBY]
        # draw.rect_r(rect, [255, 255, 255, 5], True)

        # Scrobble marker

        if prefs.scrobble_mark and lastfm.hold is False and lastfm.connected and pctl.playing_length > 0:
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
                draw.rect_r((self.scrob_stick, self.seek_bar_position[1], 2, self.seek_bar_size[1]), [255, 0, 0, 70], True)


        # # MINI ALBUM ART
        # if gui.bb_show_art:
        #     rect = [self.seek_bar_position[0] - gui.panelBY, self.seek_bar_position[1], gui.panelBY, gui.panelBY]
        #     draw.rect_r(rect, [255, 255, 255, 8], True)
        #     if 3 > pctl.playing_state > 0:
        #         album_art_gen.display(pctl.track_queue[pctl.queue_step], (rect[0], rect[1]), (rect[2], rect[3]))

            #draw.rect_r(rect, [255, 255, 255, 20])

        # SEEK BAR------------------
        if pctl.playing_time < 1:
            self.seek_time = 0

        if input.mouse_click and coll_point(mouse_position,
                                      self.seek_bar_position + [self.seek_bar_size[0]] + [self.seek_bar_size[1] + 2]):
            self.seek_down = True
            self.volume_hit = True
        if right_click and coll_point(mouse_position,
                                      self.seek_bar_position + [self.seek_bar_size[0]] + [self.seek_bar_size[1] + 2]):
            pctl.pause()
            if pctl.playing_state == 0:
                pctl.play()

        fields.add(self.seek_bar_position + self.seek_bar_size)
        if coll_point(mouse_position, self.seek_bar_position + self.seek_bar_size):

            if middle_click and pctl.playing_state > 0:
                gui.seek_cur_show = True


            clicked = True
            if mouse_wheel != 0:
                pctl.seek_time(pctl.playing_time + (mouse_wheel * 3))

        if gui.seek_cur_show:
            gui.update += 1

            # fields.add([mouse_position[0] - 1, mouse_position[1] - 1, 1, 1])
            # draw.rect_r([mouse_position[0] - 1, mouse_position[1] - 1, 1, 1], [255,0,0,180], True)


            bargetX = mouse_position[0]
            if bargetX > self.seek_bar_position[0] + self.seek_bar_size[0]:
                bargetX = self.seek_bar_position[0] + self.seek_bar_size[0]
            if bargetX < self.seek_bar_position[0]:
                bargetX = self.seek_bar_position[0]
            bargetX -= self.seek_bar_position[0]
            seek = bargetX / self.seek_bar_size[0]
            gui.cur_time = get_display_time(pctl.playing_object().length * seek)

        if self.seek_down is True:
            if mouse_position[0] == 0:
                self.seek_down = False
                self.seek_hit = True


        if (mouse_up and coll_point(mouse_position, self.seek_bar_position + self.seek_bar_size)
            and coll_point(click_location,
                           self.seek_bar_position + self.seek_bar_size)) or mouse_up and self.volume_hit or self.seek_hit:

            self.volume_hit = False
            self.seek_down = False
            self.seek_hit = False

            bargetX = mouse_position[0]
            if bargetX > self.seek_bar_position[0] + self.seek_bar_size[0]:
                bargetX = self.seek_bar_position[0] + self.seek_bar_size[0]
            if bargetX < self.seek_bar_position[0]:
                bargetX = self.seek_bar_position[0]
            bargetX -= self.seek_bar_position[0]
            seek = bargetX / self.seek_bar_size[0]

            pctl.seek_decimal(seek)
            # print(seek)

            self.seek_time = pctl.playing_time

        if pctl.playing_length > 0:
            draw.rect((self.seek_bar_position[0], self.seek_bar_position[1]),
                      (int(self.seek_time * self.seek_bar_size[0] / pctl.playing_length),
                       self.seek_bar_size[1]),
                      colours.seek_bar_fill, True)

        if gui.seek_cur_show:

            if coll_point(mouse_position, [self.seek_bar_position[0] - 50, self.seek_bar_position[1] - 50, self.seek_bar_size[0] + 50, self.seek_bar_size[1] + 100]):
                if mouse_position[0] > self.seek_bar_position[0] - 1:
                    cur = [mouse_position[0] - 40, self.seek_bar_position[1] - 25, 42, 19]
                    draw.rect_r(cur, colours.grey(15), True)
                    # draw.rect_r(cur, colours.grey(80))
                    draw_text((mouse_position[0] - 40 + 3, self.seek_bar_position[1] - 24), gui.cur_time, colours.grey(180), 213,
                              bg=colours.grey(15))

                    draw.rect_r([mouse_position[0], self.seek_bar_position[1], 2, self.seek_bar_size[1]],
                                [100, 100, 20, 255], True)

            else:
                gui.seek_cur_show = False

        # Volume Bar --------------------------------------------------------


        if input.mouse_click and coll_point(mouse_position, (
            self.volume_bar_position[0] - right_offset, self.volume_bar_position[1], self.volume_bar_size[0],
            self.volume_bar_size[1] + 4)) or \
                        self.volume_bar_being_dragged is True:
            clicked = True

            if input.mouse_click is True or self.volume_bar_being_dragged is True:
                gui.update = 2


                self.volume_bar_being_dragged = True
                volgetX = mouse_position[0]
                if volgetX > self.volume_bar_position[0] + self.volume_bar_size[0] - right_offset:
                    volgetX = self.volume_bar_position[0] + self.volume_bar_size[0] - right_offset
                if volgetX < self.volume_bar_position[0] - right_offset:
                    volgetX = self.volume_bar_position[0] - right_offset
                volgetX -= self.volume_bar_position[0] - right_offset
                pctl.player_volume = volgetX / self.volume_bar_size[0] * 100

                # gui.side_panel_size += 1
                # gui.update_layout()

                # time.sleep(0.018)
                #time.sleep(0.014)
                time.sleep(0.02)
                #SDL_Delay(50)

                if mouse_down is False:
                    self.volume_bar_being_dragged = False
                    pctl.player_volume = int(pctl.player_volume)
                    pctl.set_volume(True)

            if mouse_down:
                pctl.player_volume = int(pctl.player_volume)
                pctl.set_volume(False)


        if mouse_wheel != 0 and mouse_position[1] > self.seek_bar_position[1] + 4 and not coll_point(mouse_position,
                                                                                                     self.seek_bar_position + self.seek_bar_size):

            if pctl.player_volume + (mouse_wheel * prefs.volume_wheel_increment) < 1:
                pctl.player_volume = 0
            elif pctl.player_volume + (mouse_wheel * prefs.volume_wheel_increment) > 100:
                pctl.player_volume = 100
            else:
                pctl.player_volume += mouse_wheel * prefs.volume_wheel_increment
            pctl.player_volume = int(pctl.player_volume)
            pctl.set_volume()

        if right_click and coll_point(mouse_position, (
                    self.volume_bar_position[0] - 15 * gui.scale, self.volume_bar_position[1] - 10 * gui.scale, self.volume_bar_size[0] + 30 * gui.scale,
                    self.volume_bar_size[1] + 20 * gui.scale)):
            if pctl.player_volume > 0:
                volume_store = pctl.player_volume
                pctl.player_volume = 0
            else:
                pctl.player_volume = volume_store

            pctl.set_volume()

        draw.rect((self.volume_bar_position[0] - right_offset, self.volume_bar_position[1]), self.volume_bar_size,
                  colours.volume_bar_background, True)  # 22
        draw.rect((self.volume_bar_position[0] - right_offset, self.volume_bar_position[1]),
                  (int(pctl.player_volume * self.volume_bar_size[0] / 100), self.volume_bar_size[1]),
                  colours.volume_bar_fill, True)


        fields.add(self.volume_bar_position + self.volume_bar_size)
        if pctl.active_replaygain != 0 and (coll_point(mouse_position, (
                    self.volume_bar_position[0], self.volume_bar_position[1], self.volume_bar_size[0],
                    self.volume_bar_size[1])) or self.volume_bar_being_dragged):


            if pctl.player_volume > 50:
                draw_text((self.volume_bar_position[0] + 8 * gui.scale, self.volume_bar_position[1] - 1 * gui.scale), str(pctl.active_replaygain) + " dB", colours.volume_bar_background,
                       11, bg=colours.volume_bar_fill)
            else:
                draw_text((self.volume_bar_position[0] + 85 * gui.scale, self.volume_bar_position[1] - 1 * gui.scale), str(pctl.active_replaygain) + " dB", colours.volume_bar_fill,
                       11, bg=colours.volume_bar_background)

        if gui.show_bottom_title and pctl.playing_state > 0 and window_size[0] > 820 * gui.scale:
            if pctl.playing_state < 3:
                title = pctl.master_library[pctl.track_queue[pctl.queue_step]].title
                artist = pctl.master_library[pctl.track_queue[pctl.queue_step]].artist

                line = ""
                if artist != "":
                    line += artist
                if title != "":
                    if line != "":
                        line += "  -  "
                    line += title
            else:
                line = pctl.tag_meta

            x = self.seek_bar_position[0] + 1
            mx = window_size[0] - 710 * gui.scale
            # if gui.bb_show_art:
            #     x += 10 * gui.scale
            #     mx -= gui.panelBY - 10

            line = trunc_line(line, 213, mx)
            draw_text((x, self.seek_bar_position[1] + 22 * gui.scale), line, colours.bar_title_text,
                      fonts.panel_title)
            if (input.mouse_click or right_click) and coll_point(mouse_position, (
                        self.seek_bar_position[0] - 10 * gui.scale, self.seek_bar_position[1] + 20 * gui.scale, window_size[0] - 710 * gui.scale, 30 * gui.scale)):
                if pctl.playing_state == 3:
                    copy_to_clipboard(pctl.tag_meta)
                    show_message("Text copied to clipboard")
                    if input.mouse_click or right_click:
                        input.mouse_click = False
                        right_click = False
                else:
                    pctl.show_current()

        # TIME----------------------

        x = window_size[0] - 57 * gui.scale
        y = window_size[1] - 29 * gui.scale

        rect = (x - 8 * gui.scale - right_offset, y - 3 * gui.scale, 60 * gui.scale + right_offset, 27 * gui.scale)
        # draw.rect_r(rect, [255, 0, 0, 40], True)
        if input.mouse_click and rect_in(rect):
            gui.display_time_mode += 1
            if gui.display_time_mode > 2:
                gui.display_time_mode = 0

        if gui.display_time_mode == 0:
            text_time = get_display_time(pctl.playing_time)
            draw_text((x + 1 * gui.scale, y), text_time, colours.time_playing,
                      fonts.bottom_panel_time)
        elif gui.display_time_mode == 1:
            if pctl.playing_state == 0:
                text_time = get_display_time(0)
            else:
                text_time = get_display_time(pctl.playing_length - pctl.playing_time)
            draw_text((x + 1 * gui.scale, y), text_time, colours.time_playing,
                      fonts.bottom_panel_time)
            draw_text((x - 5 * gui.scale, y), '-', colours.time_playing,
                      fonts.bottom_panel_time)
        elif gui.display_time_mode == 2:
            x -= 4
            text_time = get_display_time(pctl.playing_time)
            draw_text((x - 25 * gui.scale, y), text_time, colours.time_playing,
                      fonts.bottom_panel_time)
            draw_text((x + 10 * gui.scale, y), "/", colours.time_sub,
                      fonts.bottom_panel_time)
            text_time = get_display_time(pctl.playing_length)
            if pctl.playing_state == 0:
                text_time = get_display_time(0)
            elif pctl.playing_state == 3:
                text_time = "-- : --"
            draw_text((x + 17 * gui.scale, y), text_time, colours.time_sub,
                      fonts.bottom_panel_time)

        # BUTTONS
        # bottom buttons

        if GUI_Mode == 1:

            box = gui.panelBY - self.seek_bar_size[1]

            # PLAY---
            buttons_x_offset = 0

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
                    play_colour = [220, 50 ,50 , 255]




            rect = (buttons_x_offset + (10 * gui.scale), window_size[1] - self.control_line_bottom - (13 * gui.scale), 50 * gui.scale , 40 * gui.scale)
            fields.add(rect)
            if coll_point(mouse_position, rect):
                play_colour = colours.media_buttons_over
                if input.mouse_click:
                    pctl.play()
                if right_click:
                    pctl.show_current(highlight=True)
                # tool_tip.test(buttons_x_offset * gui.scale + 50 * gui.scale,
                #               window_size[1] - self.control_line_bottom - 20 * gui.scale, "Play")

            self.play_button.render(29 * gui.scale, window_size[1] - self.control_line_bottom, play_colour)
            # draw.rect_r(rect,[255,0,0,255], True)

            # PAUSE---
            x = (75 * gui.scale) + buttons_x_offset
            y = window_size[1] - self.control_line_bottom

            rect = (x - 15 * gui.scale, y - 13 * gui.scale, 50 * gui.scale, 40 * gui.scale)
            fields.add(rect)
            if coll_point(mouse_position, rect):
                pause_colour = colours.media_buttons_over
                if input.mouse_click:
                    pctl.pause()
                # tool_tip.test(x + 25 * gui.scale,
                #               window_size[1] - self.control_line_bottom - 20 * gui.scale, "Pause")


            # draw.rect_r(rect,[255,0,0,255], True)
            draw.rect((x, y + 0), (4 * gui.scale, 13 * gui.scale), pause_colour, True)
            draw.rect((x + 10 * gui.scale, y + 0), (4 * gui.scale, 13 * gui.scale), pause_colour, True)

            # STOP---
            x = 125 * gui.scale + buttons_x_offset
            rect = (x - 14 * gui.scale, y - 13 * gui.scale, 50 * gui.scale, 40 * gui.scale)
            fields.add(rect)
            if coll_point(mouse_position, rect):
                stop_colour = colours.media_buttons_over
                if input.mouse_click:
                    pctl.stop()
                if right_click:
                    pctl.auto_stop ^= True
                # tool_tip.test(x + gui.scale + 25 * gui.scale,
                #               window_size[1] - self.control_line_bottom - 20 * gui.scale, "Stop")

            draw.rect((x, y + 0), (13 * gui.scale, 13 * gui.scale), stop_colour, True)
            # draw.rect_r(rect,[255,0,0,255], True)

            # FORWARD---
            rect = (buttons_x_offset + 230 * gui.scale, window_size[1] - self.control_line_bottom - 10 * gui.scale, 50 * gui.scale, 35 * gui.scale)
            fields.add(rect)
            if coll_point(mouse_position, rect):
                forward_colour = colours.media_buttons_over
                if input.mouse_click:
                    pctl.advance()
                if right_click:
                    pctl.random_mode ^= True
                if middle_click:
                    pctl.advance(rr=True)
                #tool_tip.test(buttons_x_offset + 230 * gui.scale + 50 * gui.scale, window_size[1] - self.control_line_bottom - 20 * gui.scale, "Advance")

            self.forward_button.render(240 * gui.scale, 1 + window_size[1] - self.control_line_bottom, forward_colour)

            # draw.rect_r(rect,[255,0,0,255], True)

            # BACK---
            rect = (buttons_x_offset + 170 * gui.scale, window_size[1] - self.control_line_bottom - 10 * gui.scale, 50 * gui.scale, 35 * gui.scale)
            fields.add(rect)
            if coll_point(mouse_position, rect):
                back_colour = colours.media_buttons_over
                if input.mouse_click:
                    pctl.back()
                if right_click:
                    pctl.repeat_mode ^= True
                if middle_click:
                    pctl.revert()
                #tool_tip.test(buttons_x_offset + 170 * gui.scale + 50 * gui.scale,
                #              window_size[1] - self.control_line_bottom - 20 * gui.scale, "Back")

            self.back_button.render(180 * gui.scale, 1 + window_size[1] - self.control_line_bottom, back_colour)
            # draw.rect_r(rect,[255,0,0,255], True)


            # menu button

            x = window_size[0] - 252 * gui.scale - right_offset
            y = window_size[1] - 26 * gui.scale
            rpbc = colours.mode_button_off
            rect = (x - 9 * gui.scale, y - 5 * gui.scale, 40 * gui.scale, 25 * gui.scale)
            fields.add(rect)
            if coll_point(mouse_position, rect):
                if not extra_menu.active:
                    tool_tip.test(x, y - 28 * gui.scale, "Playback menu")
                rpbc = colours.mode_button_over
                if input.mouse_click:
                    extra_menu.activate(position=(x - 115 * gui.scale, y - 6 * gui.scale))
            if extra_menu.active:
                rpbc = colours.mode_button_active

            draw.rect((x, y), (24 * gui.scale, 2 * gui.scale), rpbc, True)
            y += 5 * gui.scale
            draw.rect((x, y), (24 * gui.scale, 2 * gui.scale), rpbc, True)
            y += 5 * gui.scale
            draw.rect((x, y), (24 * gui.scale, 2 * gui.scale), rpbc, True)

            if window_size[0] > 630 * gui.scale and self.mode == 0:

                # shuffle button
                x = window_size[0] - 318 * gui.scale - right_offset
                y = window_size[1] - 27 * gui.scale

                rect = (x - 5 * gui.scale, y - 5 * gui.scale, 60 * gui.scale, 25 * gui.scale)
                fields.add(rect)

                rpbc = colours.mode_button_off
                if (input.mouse_click or right_click) and coll_point(mouse_position, rect):
                    pctl.random_mode ^= True

                    if pctl.random_mode is False:
                        self.random_click_off = True

                if pctl.random_mode:
                    rpbc = colours.mode_button_active

                elif coll_point(mouse_position, rect):
                    tool_tip.test(x, y - 28 * gui.scale, "Shuffle")
                    if self.random_click_off is True:
                        rpbc = colours.mode_button_off
                    elif pctl.random_mode is True:
                        rpbc = colours.mode_button_active
                    else:
                        rpbc = colours.mode_button_over
                else:
                    self.random_click_off = False

                y += 3 * gui.scale

                draw.rect((x, y), (25 * gui.scale, 3 * gui.scale), rpbc, True)

                y += 5 * gui.scale
                draw.rect((x, y), (48 * gui.scale, 3 * gui.scale), rpbc, True)

                # REPEAT
                x = window_size[0] - 380 * gui.scale - right_offset
                y = window_size[1] - 27 * gui.scale

                rpbc = colours.mode_button_off

                rect = (x - 6 * gui.scale, y - 5 * gui.scale, 61 * gui.scale, 25 * gui.scale)
                fields.add(rect)
                if (input.mouse_click or right_click) and coll_point(mouse_position, rect):
                    pctl.repeat_mode ^= True

                    if pctl.repeat_mode is False:
                        self.repeat_click_off = True

                if pctl.repeat_mode:
                    rpbc = colours.mode_button_active

                elif coll_point(mouse_position, rect):
                    tool_tip.test(x, y - 28 * gui.scale, "Repeat")
                    if self.repeat_click_off is True:
                        rpbc = colours.mode_button_off
                    elif pctl.repeat_mode is True:
                        rpbc = colours.mode_button_active
                    else:
                        rpbc = colours.mode_button_over
                else:
                    self.repeat_click_off = False

                y += 3 * gui.scale
                w = 3 * gui.scale

                draw.rect((x + 25 * gui.scale, y), (25 * gui.scale, w), rpbc, True)
                draw.rect((x + 4 * gui.scale, y + 5 * gui.scale), (46 * gui.scale, w), rpbc, True)
                draw.rect((x + 50 * gui.scale - w, y), (w, 8 * gui.scale), rpbc, True)


bottom_bar1 = BottomBarType1()


def line_render(n_track, p_track, y, this_line_playing, album_fade, start_x, width, style=1):
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

    indexoffset = 0
    artistoffset = 0
    indexLine = ""

    offset_font_extra = 0
    if gui.row_font_size > 14:
        offset_font_extra = 8

    # In windows (arial?) draws numbers too high (hack fix)
    num_y_offset = 0
    if system == 'windows':
        num_y_offset = 1


    if True or style == 1:


        if not side_panel_enable and not gui.combo_mode:
            width -= 10 * gui.scale

        if n_track.artist != "" or \
                        n_track.title != "":
            line = track_number_process(n_track.track_number)

            indexLine = line
            line = ""

            if len(indexLine) > 2:
                indexoffset += (len(indexLine) * 5 - 15) * gui.scale

            if n_track.artist != "":
                line0 = n_track.artist
                artistoffset = draw_text2((start_x + 27  * gui.scale,
                                           y),
                                          line0,
                                          alpha_mod(artistc, album_fade),
                                          gui.row_font_size,
                                          int(width / 2),
                                          1,
                                          default_playlist[p_track])

                line = n_track.title
            else:
                line += n_track.title
        else:
            line = \
                os.path.splitext((n_track.filename))[
                    0]

        index = default_playlist[p_track]
        star_x = 0
        total = star_store.get(index)

        if star_lines and total > 0 and pctl.master_library[index].length > 0:
            #total = pctl.star_library[key]
            ratio = total / pctl.master_library[index].length
            if ratio > 0.55:
                star_x = int(ratio * 4 * gui.scale)
                if star_x > 60 * gui.scale:
                    star_x = 60 * gui.scale
                sp = y - 0 - gui.playlist_text_offset + int(gui.playlist_row_height / 2)
                if gui.playlist_row_height > 17 * gui.scale:
                    sp -= 1
                draw.rect_r([width + start_x - star_x - 45 * gui.scale - offset_font_extra,
                             sp,
                             star_x + 3 * gui.scale,
                             1
                             ], alpha_mod(colours.star_line, album_fade), True)

        if gui.show_stars and total > 0 and pctl.master_library[
            index].length != 0:

            stars = star_count(total, pctl.master_library[index].length)
            starl = "★" * stars
            star_x = draw_text((width + start_x - 42 * gui.scale - offset_font_extra,
                       y + gui.star_text_y_offset, 1), starl,
                      alpha_mod(indexc, album_fade), gui.row_font_size)


        if len(indexLine) > 2:

            draw_text((start_x + 5 * gui.scale,
                       y, 2), indexLine,
                      alpha_mod(indexc, album_fade), gui.row_font_size)

        else:

            draw_text((start_x,
                       y), indexLine,
                      alpha_mod(indexc, album_fade), gui.row_font_size)

        draw_text2((start_x + 33 * gui.scale + artistoffset,
                    y),
                   line,
                   alpha_mod(titlec, album_fade),
                   gui.row_font_size,
                   width - 71 * gui.scale - artistoffset - star_x - 20 * gui.scale,
                   2,
                   default_playlist[p_track])

        line = get_display_time(n_track.length)

        draw_text((width + start_x - 36 * gui.scale - offset_font_extra,
                   y + num_y_offset, 0), line,
                  alpha_mod(timec, album_fade), gui.row_font_size)


class StandardPlaylist:
    def __init__(self):
        pass

    def full_render(self):

        global highlght_left
        global highlight_right
        global playlist_position
        global playlist_hold
        global playlist_hold_position
        global playlist_selected
        global shift_selection

        global click_time
        global quick_drag
        global mouse_down
        global mouse_up
        global selection_stage

        if side_panel_enable or gui.set_mode:
            inset_left = 0
            inset_right = 0

            highlight_left = 0
            highlight_right = gui.playlist_width + 31 * gui.scale
            highlight_right = gui.playlist_width + 31 * gui.scale

        else:
            inset_left = 28 * gui.scale
            inset_right = 60 * gui.scale

            inset_left = gui.scale * int(pow((window_size[0] * 0.01), 2))
            inset_right = inset_left * 2

            highlight_left = inset_left + 5 * gui.scale
            highlight_right = gui.playlist_width + 31 * gui.scale - inset_right - 20 * gui.scale

        w = 0
        gui.row_extra = 0

        # Draw the background
        SDL_SetRenderTarget(renderer, gui.ttext)
        rect = (0, gui.panelY, gui.playlist_width + 31 * gui.scale, window_size[1])
        if side_panel_enable is False:
            rect = (0, gui.panelY, window_size[0], window_size[1])
        draw.rect_r(rect, colours.playlist_panel_background, True)

        if mouse_wheel != 0 and window_size[1] - gui.panelBY - 1 > mouse_position[
            1] > gui.panelY - 2 \
                and not (playlist_panel and coll_point(mouse_position, pl_rect)) and not (
            key_shift_down and track_box):

            if album_mode and mouse_position[0] > gui.playlist_width + 34 * gui.scale:
                pass
            else:
                mx = 4
                if gui.playlist_view_length < 25:
                    mx = 3
                # if thick_lines:
                #     mx = 3
                playlist_position -= mouse_wheel * mx
                # if gui.playlist_view_length > 15:
                #     playlist_position -= mouse_wheel
                if gui.playlist_view_length > 40:
                    playlist_position -= mouse_wheel

                if playlist_position > len(default_playlist):
                    playlist_position = len(default_playlist)
                if playlist_position < 1:
                    playlist_position = 0
                    edge_playlist.pulse()

        # Show notice if playlist empty

        if len(default_playlist) == 0:
            colour = alpha_mod(colours.index_text, 200)  # colours.playlist_text_missing


            draw_text((int(gui.playlist_width / 2) + 10 * gui.scale, int((window_size[1] - gui.panelY - gui.panelBY) * 0.65), 2),
                      "Playlist is empty", colour, 213, bg=colours.playlist_panel_background)
            draw_text((int(gui.playlist_width / 2) + 10 * gui.scale, int((window_size[1] - gui.panelY - gui.panelBY) * 0.65 + (30 * gui.scale)), 2),
                      "Drag and drop files to import", colour, 13, bg=colours.playlist_panel_background)

        # Show notice if at end of playlist
        elif playlist_position > len(default_playlist) - 1:
            colour = alpha_mod(colours.index_text, 200)
            draw_text((int(gui.playlist_width / 2) + 10 * gui.scale, int(window_size[1] * 0.18), 2), "End of Playlist",
                      colour, 213)

        # For every track in view
        for i in range(gui.playlist_view_length + 1):

            p_track = i + playlist_position

            move_on_title = False

            if playlist_position < 0:
                playlist_position = 0
            if len(default_playlist) <= p_track:
                break

            n_track = pctl.master_library[default_playlist[p_track]]

            # Fade other tracks in album mode
            album_fade = 255
            if album_mode and pctl.playing_state != 0 and prefs.dim_art and \
                            n_track.parent_folder_name \
                            != pctl.master_library[pctl.track_queue[pctl.queue_step]].parent_folder_name:
                album_fade = 150

            # Folder Break Row

            if (p_track == 0 or n_track.parent_folder_name
                != pctl.master_library[default_playlist[p_track - 1]].parent_folder_name) and \
                            pctl.multi_playlist[pctl.playlist_active][4] == 0 and break_enable:

                line = n_track.parent_folder_name

                if not prefs.pl_thumb:

                    if not prefs.use_title and n_track.album_artist != "" and n_track.album != "":
                        line = n_track.album_artist + " - " + n_track.album

                    if len(line) < 6 and "CD" in line:
                        line = n_track.album

                    if prefs.append_date and n_track.date != "" and "20" not in line and "19" not in line and "18" not in line and "17" not in line:
                        line += " (" + n_track.date + ")"

                    ex = highlight_right + highlight_left - 7 * gui.scale

                    gui.win_fore = colours.playlist_panel_background
                    height = (gui.playlist_top + gui.playlist_row_height * w) + (gui.playlist_row_height - gui.pl_title_real_height) + gui.pl_title_y_offset

                    # Draw highlight
                    if p_track in shift_selection and len(shift_selection) > 1:
                        gui.win_fore = alpha_blend(colours.row_select_highlight, colours.playlist_panel_background)
                        draw.rect((highlight_left, gui.playlist_top + gui.playlist_row_height * w),
                                  (highlight_right, gui.playlist_row_height), colours.row_select_highlight, True)


                    # Draw folder title
                    draw_text2((ex,
                                height, 1), line,
                               alpha_mod(colours.folder_title, album_fade),
                               gui.row_font_size + gui.pl_title_font_offset, gui.playlist_width - inset_left * 2)

                    # Draw separation line below title
                    draw.rect_r((highlight_left, gui.playlist_top + gui.playlist_row_height - 1 * gui.scale + gui.playlist_row_height * w, highlight_right, 1 * gui.scale), colours.folder_line, True)

                    gui.win_fore = colours.playlist_panel_background

                    if playlist_hold is True and coll_point(mouse_position, (
                            gui.playlist_left, gui.playlist_top + gui.playlist_row_height * w, gui.playlist_width,
                            gui.playlist_row_height)):

                        if mouse_up:  # and key_shift_down:
                            move_on_title = True

                    # Detect folder title click
                    if (input.mouse_click or right_click) and coll_point(mouse_position, (
                                highlight_left, gui.playlist_top + gui.playlist_row_height * w, highlight_right,
                                gui.playlist_row_height - 1)) and mouse_position[1] < window_size[1] - gui.panelBY:

                        # Play if double click:
                        if d_mouse_click and p_track in shift_selection and coll_point(last_click_location, (
                                    gui.playlist_left + 10, gui.playlist_top + gui.playlist_row_height * w, gui.playlist_width - 10,
                                    gui.playlist_row_height - 1)):
                            click_time -= 1.5
                            pctl.jump(default_playlist[p_track], p_track)

                            if album_mode:
                                goto_album(pctl.playlist_playing)

                        # Show selection menu if right clicked after select
                        if right_click:  # and len(shift_selection) > 1:
                            folder_menu.activate(default_playlist[p_track])
                            selection_stage = 2
                            gui.pl_update = 1

                            if p_track not in shift_selection:
                                shift_selection = []
                                playlist_selected = p_track
                                u = p_track
                                while u < len(default_playlist) and n_track.parent_folder_path == pctl.master_library[
                                    default_playlist[u]].parent_folder_path:
                                    shift_selection.append(u)
                                    u += 1

                        # Add folder to selection if clicked
                        if input.mouse_click:
                            quick_drag = True
                            gui.drag_source_position = copy.deepcopy(click_location)
                            playlist_hold = True
                            selection_stage = 1
                            temp = get_folder_tracks_local(p_track)
                            # if p_track not in shift_selection: # not key_shift_down:
                            #     shift_selection = []
                            playlist_selected = p_track

                            if len(shift_selection) > 0 and key_shift_down:
                                if p_track < shift_selection[0]:
                                    for item in reversed(temp):
                                        if item not in shift_selection:
                                            shift_selection.insert(0, item)
                                else:
                                    for item in temp:
                                        if item not in shift_selection:
                                            shift_selection.append(item)

                            else:
                                shift_selection = copy.deepcopy(temp)


                    # # Shade ever other line for folder row
                    # if True and #row_alt and w % 2 == 0:
                    #     draw.rect((gui.playlist_left, gui.playlist_top + gui.playlist_row_height * w),
                    #               (gui.playlist_width, gui.playlist_row_height - 1), [255, 255, 255, 10], True)


                    # Draw blue highlight insert line
                    if mouse_down and playlist_hold and coll_point(mouse_position, (
                            gui.playlist_left, gui.playlist_top + gui.playlist_row_height * w, gui.playlist_width,
                            gui.playlist_row_height - 1)) and p_track not in shift_selection:  # playlist_hold_position != p_track:

                        if len(shift_selection) > 1 or key_shift_down:

                            draw.rect_r(
                                [0, -1 + gui.playlist_top + gui.playlist_row_height * w + gui.playlist_row_height - 1,
                                 gui.playlist_width + 30, 3],
                                [135, 145, 190, 255], True)

                    w += 1
                else:

                    y = gui.playlist_top + gui.playlist_row_height * w
                    spaces = 5
                    w += spaces
                    hei = spaces * prefs.playlist_row_height

                    pl_thumbnail.size = hei - 15
                    pl_thumbnail.render(n_track.index, (gui.playlist_left, y + 5))


                if playlist_selected > p_track + 1:
                    gui.row_extra += 1

            # Shade ever other line if option set
            # if (row_alt or True) and w % 2 == 0:
            #     draw.rect((gui.playlist_left, gui.playlist_top + gui.playlist_row_height * w),
            #               (gui.playlist_width, gui.playlist_row_height - 1), [0, 0, 0, 20], True)

            # Get background colours for fonts
            gui.win_fore = colours.playlist_panel_background

            # Test if line hit
            line_over = False
            if coll_point(mouse_position, (
                        highlight_left, gui.playlist_top + gui.playlist_row_height * w, highlight_right,
                        gui.playlist_row_height - 1)) and mouse_position[1] < window_size[1] - gui.panelBY:
                line_over = True
                if (input.mouse_click or right_click or middle_click):
                    line_hit = True
                else:
                    line_hit = False
            else:
                line_hit = False
                line_over = False

            if scroll_enable and mouse_position[0] < 30:
                line_hit = False

            # Double click to play
            if key_shift_down is False and d_mouse_click and line_hit and p_track == playlist_selected and coll_point(
                    last_click_location, (
                                gui.playlist_left + 10, gui.playlist_top + gui.playlist_row_height * w, gui.playlist_width - 10,
                                gui.playlist_row_height - 1)):

                click_time -= 1.5
                pctl.jump(default_playlist[p_track], p_track)
                quick_drag = False
                mouse_down = False
                mouse_up = False

                if album_mode:
                    goto_album(pctl.playlist_playing)

            # Check if index playing and highlight if true
            this_line_playing = False
            this_line_selected = False

            if len(pctl.track_queue) > 0 and pctl.track_queue[pctl.queue_step] == \
                    default_playlist[p_track]:
                draw.rect((highlight_left, gui.playlist_top + gui.playlist_row_height * w),
                          (highlight_right, gui.playlist_row_height - 1), colours.row_playing_highlight, True)
                this_line_playing = True
                gui.win_fore = alpha_blend(colours.row_playing_highlight, gui.win_fore)

            # Highlight blue if track is being broadcast
            if default_playlist[
                p_track] == pctl.broadcast_index and pctl.broadcast_active:
                draw.rect((0, gui.playlist_top + gui.playlist_row_height * w),
                          (gui.playlist_width + 30, gui.playlist_row_height - 1), [40, 40, 190, 80], True)
                gui.win_fore = alpha_blend([40, 40, 190, 80], gui.win_fore)

            # Add to queue on middle click
            if middle_click and line_hit:
                pctl.force_queue.append([default_playlist[p_track],
                                         p_track, pctl.playlist_active])

            # Highlight green if track in queue
            for item in pctl.force_queue:
                if default_playlist[p_track] == item[0] and item[1] == p_track:
                    # draw.rect((gui.playlist_left, gui.playlist_top + gui.playlist_row_height * w),
                    #           (gui.playlist_width, gui.playlist_row_height - 1), [130, 220, 130, 30],
                    #           True)
                    draw.rect((highlight_left, gui.playlist_top + gui.playlist_row_height * w),
                              (highlight_right, gui.playlist_row_height - 1), [130, 220, 130, 30], True)
                    gui.win_fore = alpha_blend([130, 220, 130, 30], gui.win_fore)

            # Make track the selection if right clicked
            if right_click and line_hit and not playlist_panel:
                if p_track not in shift_selection:
                    shift_selection = [p_track]

            if input.mouse_click and line_hit and p_track not in shift_selection:  # key_shift_down is False and line_hit:
                # shift_selection = []
                shift_selection = [p_track]

            if mouse_up and line_over and not key_shift_down and point_proximity_test(gui.drag_source_position, mouse_position, 15): # and not playlist_hold:
                shift_selection = [p_track]
                playlist_selected = p_track
                gui.pl_update = 1

            if mouse_down and line_over and p_track in shift_selection and len(shift_selection) > 1:
                playlist_hold = True

            if input.mouse_click and line_hit:
                quick_drag = True
                gui.drag_source_position = copy.deepcopy(click_location)


            if (input.mouse_click and key_shift_down is False and line_hit or
                        playlist_selected == p_track):
                draw.rect((highlight_left, gui.playlist_top + gui.playlist_row_height * w),
                          (highlight_right, gui.playlist_row_height), colours.row_select_highlight, True)
                playlist_selected = p_track
                this_line_selected = True
                gui.win_fore = alpha_blend(colours.row_select_highlight, gui.win_fore)

                # if not key_shift_down:
                #     shift_selection = [playlist_selected]

            # Shift Move Selection
            if (move_on_title) or mouse_up and playlist_hold is True and coll_point(mouse_position, (
                    gui.playlist_left, gui.playlist_top + gui.playlist_row_height * w, gui.playlist_width, gui.playlist_row_height)):

                if len(shift_selection) > 1 or key_shift_down:
                    if p_track not in shift_selection: #p_track != playlist_hold_position and

                        if len(shift_selection) == 0:

                            ref = default_playlist[playlist_hold_position]
                            default_playlist[playlist_hold_position] = "old"
                            if move_on_title:
                                default_playlist.insert(p_track, "new")
                            else:
                                default_playlist.insert(p_track + 1, "new")
                            default_playlist.remove("old")
                            playlist_selected = default_playlist.index("new")
                            default_playlist[default_playlist.index("new")] = ref

                            gui.pl_update = 1


                        else:
                            ref = []
                            selection_stage = 2
                            for item in shift_selection:
                                ref.append(default_playlist[item])

                            for item in shift_selection:
                                default_playlist[item] = 'old'

                            for item in shift_selection:
                                if move_on_title:
                                    default_playlist.insert(p_track, "new")
                                else:
                                    default_playlist.insert(p_track + 1, "new")

                            for b in reversed(range(len(default_playlist))):
                                if default_playlist[b] == 'old':
                                    del default_playlist[b]
                            shift_selection = []
                            for b in range(len(default_playlist)):
                                if default_playlist[b] == 'new':
                                    shift_selection.append(b)
                                    default_playlist[b] = ref.pop(0)

                            playlist_selected = shift_selection[0]
                            gui.pl_update = 1

            # Blue drop line
            if mouse_down and playlist_hold and coll_point(mouse_position, (
                    gui.playlist_left, gui.playlist_top + gui.playlist_row_height * w, gui.playlist_width,
                    gui.playlist_row_height - 1)) and p_track not in shift_selection: #playlist_hold_position != p_track:

                if len(shift_selection) > 1 or key_shift_down:
                    draw.rect_r(
                        [0, -1 + gui.playlist_top + gui.playlist_row_height + gui.playlist_row_height * w, gui.playlist_width + 30, 3],
                        [135, 145, 190, 255], True)

            # Shift click actions
            if input.mouse_click and line_hit: # and key_shift_down:
                selection_stage = 2
                if p_track != playlist_selected:

                    start_s = p_track
                    end_s = playlist_selected
                    if end_s < start_s:
                        end_s, start_s = start_s, end_s
                    for y in range(start_s, end_s + 1):
                        if y not in shift_selection:
                            shift_selection.append(y)
                    shift_selection.sort()

                # else:
                playlist_hold = True
                playlist_hold_position = p_track

            # Multi Select Highlight
            if p_track in shift_selection and p_track != playlist_selected:
                draw.rect((highlight_left, gui.playlist_top + gui.playlist_row_height * w),
                          (highlight_right, gui.playlist_row_height), colours.row_select_highlight, True)
                this_line_selected = True
                gui.win_fore = alpha_blend(colours.row_select_highlight, gui.win_fore)

            if right_click and line_hit and mouse_position[0] > gui.playlist_left + 10 \
                    and not playlist_panel:

                if len(shift_selection) > 1:
                    selection_menu.activate(default_playlist[p_track])
                    selection_stage = 2
                else:
                    track_menu.activate(default_playlist[p_track])
                    gui.pl_update += 1

                playlist_selected = p_track

            if line_over:
                if mouse_up and selection_stage > 0:
                    selection_stage -= 1
                if mouse_up and selection_stage == 0 and len(shift_selection) > 1:
                    playlist_hold = False
                    shift_selection = []
                    gui.pl_update = 1

            if not gui.set_mode:

                line_render(n_track, p_track, gui.playlist_text_offset + gui.playlist_top + gui.playlist_row_height * w,
                            this_line_playing, album_fade, gui.playlist_left + inset_left, gui.playlist_width - inset_right, prefs.line_style)
            else:
                # NEE ---------------------------------------------------------

                # offset_font_extra = 0
                # if gui.row_font_size > 14:
                #     offset_font_extra = 8
                # offset_y_extra = 0
                # if gui.row_font_size > 13:
                #     offset_y_extra = 2
                #     if gui.row_font_size > 14:
                #         offset_y_extra = 3

                start = gui.playlist_left - 2 * gui.scale
                run = start
                for h, item in enumerate(gui.pl_st):

                    wid = item[1] - 20 * gui.scale
                    y = gui.playlist_text_offset + gui.playlist_top + gui.playlist_row_height * w
                    if run > gui.playlist_width + 24 * gui.scale:
                        break

                    if len(gui.pl_st) == h + 1:
                        wid -= 6 * gui.scale

                    if item[0] == "Starline":
                        #key = n_track.title + n_track.filename
                        total = star_store.get_by_object(n_track)
                        #total = playtime_penalty(n_track, total)
                        #if (key in pctl.star_library) and pctl.star_library[key] != 0 and n_track.length != 0 and wid > 0:
                        if total > 0 and n_track.length != 0 and wid > 0:
                            if gui.show_stars:

                                # re = 0
                                # if get_love(n_track):
                                #     re = draw_text((run + 6, y + gui.star_text_y_offset),
                                #           "❤",
                                #           [220, 90, 90, 255],
                                #           gui.row_font_size,
                                #           )
                                #     re += 4

                                text = star_count(total, n_track.length) * "★"

                                # if get_love(n_track):
                                #     text = text + " ❤"

                                colour = colours.index_text
                                if this_line_playing is True:
                                    colour = colours.index_playing
                                text = trunc_line(text, gui.row_font_size, wid + 7 * gui.scale, False)
                                draw_text((run + 6 * gui.scale, y + gui.star_text_y_offset),
                                          text,
                                          colour,
                                          gui.row_font_size,
                                          )
                            else:
                                #total = pctl.star_library[key]
                                ratio = total / n_track.length
                                if ratio > 0.55:
                                    star_x = int(ratio * (4 * gui.scale))
                                    if star_x > wid:
                                        star_x = wid
                                    sy = (gui.playlist_top + gui.playlist_row_height * w) + int(gui.playlist_row_height / 2)
                                    draw.rect_r((run + 4 * gui.scale, sy, star_x, 1 * gui.scale), colours.star_line)
                                    # draw.line(run + 4, sy, run + star_x + 4, sy,
                                    #           colours.star_line)

                    else:
                        text = ""
                        font = gui.row_font_size
                        colour = [200, 200, 200, 255]
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
                            if this_line_playing is True:
                                colour = colours.artist_playing
                        elif item[0] == "Album":
                            text = n_track.album
                            colour = colours.album_text
                            if this_line_playing is True:
                                colour = colours.album_playing
                        elif item[0] == "T":
                            text = track_number_process(n_track.track_number)
                            colour = colours.index_text
                            if this_line_playing is True:
                                colour = colours.index_playing
                        elif item[0] == "Date":
                            text = n_track.date
                            colour = colours.index_text
                            if this_line_playing is True:
                                colour = colours.index_playing
                        elif item[0] == "Filepath":
                            text = n_track.fullpath
                            colour = colours.index_text
                        elif item[0] == "Codec":
                            text = n_track.file_ext
                            colour = colours.index_text
                            if this_line_playing is True:
                                colour = colours.index_playing
                        elif item[0] == "Lyrics":
                            text = ""
                            if n_track.lyrics != "":
                                text = 'Y'
                            colour = colours.index_text
                            if this_line_playing is True:
                                colour = colours.index_playing
                        elif item[0] == "Genre":
                            text = n_track.genre
                            colour = colours.index_text
                            if this_line_playing is True:
                                colour = colours.index_playing
                        elif item[0] == "Bitrate":
                            text = str(n_track.bitrate)
                            if text == "0":
                                text = ""
                            colour = colours.index_text
                            if this_line_playing is True:
                                colour = colours.index_playing
                        elif item[0] == "Time":
                            text = get_display_time(n_track.length)
                            colour = colours.bar_time
                            #colour = colours.time_text
                            if this_line_playing is True:
                                colour = colours.time_text
                        elif item[0] == "❤":
                            if get_love(n_track):
                                text = "❤"
                                colour = [220, 90, 90, 255]
                                if standard_font == "Segoe UI":
                                    font -= 2
                                elif standard_font == 'Noto Sans Bold':
                                    y_off = 1
                                    font += 1
                            else:
                                text = ""
                            # if this_line_playing is True:
                            #     colour = colours.artist_playing
                        elif item[0] == "P":
                            #key = n_track.title + n_track.filename
                            ratio = 0
                            total = star_store.get_by_object(n_track)
                            #if (key in pctl.star_library) and pctl.star_library[key] != 0 and n_track.length != 0:
                            if total > 0 and n_track.length != 0:
                                # total = pctl.star_library[key]
                                if n_track.length > 15:
                                    total += 2
                                ratio = total / n_track.length

                            text = str(str(int(ratio)))
                            if text == "0":
                                text = ""
                            colour = colours.index_text
                            if this_line_playing is True:
                                colour = colours.index_playing

                        if prefs.dim_art and album_mode and \
                                n_track.parent_folder_name \
                                != pctl.master_library[pctl.track_queue[pctl.queue_step]].parent_folder_name:
                            colour = alpha_mod(colour, 150)
                        if n_track.found is False:
                            colour = colours.playlist_text_missing

                        #text = trunc_line(text, gui.row_font_size, wid)
                        text = trunc_line2(text, gui.row_font_size, wid)
                        draw_text((run + 6, y + y_off),
                                  text,
                                  colour,
                                  font,
                                  )
                    run += item[1]




            # -----------------------------------------------------------------


            w += 1
            if w > gui.playlist_view_length:
                break

        #


        if (right_click and gui.playlist_top + 40 + gui.playlist_row_height * w < mouse_position[1] < window_size[
            1] - 55 and not playlist_panel and
                            gui.playlist_width + gui.playlist_left > mouse_position[0] > gui.playlist_left + 15):
            playlist_menu.activate()

        SDL_SetRenderTarget(renderer, gui.main_texture)
        SDL_RenderCopy(renderer, gui.ttext, None, gui.abc)

        if mouse_down is False:
            playlist_hold = False

    def cache_render(self):

        SDL_RenderCopy(renderer, gui.ttext, None, gui.abc)


class ComboPlaylist:
    def __init__(self):

        self.pl_pos_px = 0
        self.pl_album_art_size = combo_mode_art_size
        self.v_buffer = 58 * gui.scale#60
        self.h_buffer = 70 * gui.scale

        self.mirror_cache = []
        self.last_dex = 0
        self.max_y = 0

        self.hit = True
        self.preped_row_size = 1

    def prep(self, goto=False):

        self.mirror_cache = []
        album_dex_on = 0
        pl_entry_on = 0
        pl_render_pos = 30 * gui.scale
        min = 0
        self.pl_album_art_size = combo_mode_art_size

        while True:

            if pl_entry_on > len(default_playlist) - 1:
                break

            if album_dex_on < len(album_dex) - 0:
                if album_dex[album_dex_on] == pl_entry_on:

                    album_dex_on += 1
                    # if goto and playlist_selected < pl_entry_on + 1:
                    if goto and pl_entry_on > playlist_selected:
                        if len(self.mirror_cache) > 0:
                            self.pl_pos_px = self.mirror_cache[-1:][0]
                            self.pl_pos_px -= 25 * gui.scale

                        else:
                            self.pl_pos_px = 0
                        self.prep()
                        return

                    if min > 0:
                        pl_render_pos += min

                    self.mirror_cache.append(pl_render_pos)

                    pl_render_pos += self.v_buffer

                    min = self.pl_album_art_size

            pl_entry_on += 1
            pl_render_pos += prefs.playlist_row_height
            min -= prefs.playlist_row_height

        self.max_y = pl_render_pos + 20 * gui.scale

        if goto and len(self.mirror_cache) > 0:
            self.pl_pos_px = self.mirror_cache[-1:][0] - 25 * gui.scale

    def full_render(self):
        # C-CM
        global click_time
        global playlist_selected
        global shift_selection
        global quick_drag

        if self.preped_row_size != gui.playlist_row_height:
            self.preped_row_size = gui.playlist_row_height
            self.prep()

        # Draw the background
        SDL_SetRenderTarget(renderer, gui.ttext)
        rect = (0, gui.panelY, gui.playlist_width + 31, window_size[1])
        if side_panel_enable is False:
            rect = (0, gui.panelY, window_size[0], window_size[1])
        draw.rect_r(rect, colours.playlist_panel_background, True)

        # Get scroll movement

        if gui.panelY < mouse_position[1] < window_size[1] - gui.panelBY:
            self.pl_pos_px -= mouse_wheel * 75 * gui.scale
            if self.pl_pos_px < 0:
                self.pl_pos_px = 0
            elif self.pl_pos_px > self.max_y:
                self.pl_pos_px = self.max_y
                # if key_shift_down:
                #     self.pl_pos_px -= mouse_wheel * 10000

        if key_PGU:
            self.pl_pos_px -= abs(window_size[1] - 80 * gui.scale)
        if key_PGD:
            self.pl_pos_px += abs(window_size[1] - 80 * gui.scale)

        # Set some things
        pl_render_pos = 30 * gui.scale
        pl_entry_on = 0
        render = False
        album_dex_on = 0
        min = 0

        i = 0
        for item in self.mirror_cache:

            if item > self.pl_pos_px - 2000 * gui.scale:
                pl_render_pos = self.mirror_cache[i]
                pl_entry_on = album_dex[i]
                album_dex_on = i
                break
            i += 1

        if (input.mouse_click or right_click) and mouse_position[1] < window_size[1] - gui.panelBY and \
                        mouse_position[1] > gui.panelY:
            self.hit = False

        while pl_render_pos < self.pl_pos_px + window_size[1] and \
                        pl_entry_on < len(default_playlist):

            if not render and pl_render_pos + self.pl_album_art_size + 200 * gui.scale > self.pl_pos_px:
                render = True

            index_on = default_playlist[pl_entry_on]
            track = pctl.master_library[index_on]

            if album_dex_on < len(album_dex) - 0:
                if album_dex[album_dex_on] == pl_entry_on:

                    if min > 0:
                        pl_render_pos += min

                    # print('test match')
                    # print(self.mirror_cache[album_dex_on])
                    # print(pl_render_pos)

                    pl_render_pos += self.v_buffer

                    album_dex_on += 1

                    if render:
                        y = pl_render_pos - self.pl_pos_px
                        x = 20 * gui.scale



                        # Draw album header
                        if break_enable:
                            x1 = 20 * gui.scale
                            y1 = y - 1 * gui.scale
                            x2 = gui.playlist_width + self.pl_album_art_size + 20 * gui.scale

                            if gui.scale == 2 or True:
                                y1 -= 25 * gui.scale  # hacky fix
                                if gui.scale == 2:
                                    draw.line(x1, y1 + 1, x2, y1 + 1, [50, 50, 50, 50])

                            draw.line(x1, y1, x2, y1, [50, 50, 50, 50])



                            right_space = 22 * gui.scale
                            right_position = window_size[0] - right_space

                            if len(track.date) > 1:
                                album = trunc_line(track.album, 17, window_size[0] - 120 * gui.scale)
                                w = draw.text_calc(album, 17) + 30 * gui.scale
                                draw.line(right_position - w + 10 * gui.scale, y1, right_position + 20 * gui.scale, y1, colours.playlist_panel_background)
                                if gui.scale == 2:
                                    draw.line(right_position - w + 10 * gui.scale, y1 + 1, right_position + 20 * gui.scale, y1 + 1,
                                              colours.playlist_panel_background)

                                draw_text((right_position, y1 - 20 * gui.scale, 1), album, colours.folder_title, 17)

                                draw_text((right_position, y1 - 0, 1), track.date, colours.folder_title, 14)
                            else:
                                album = trunc_line(track.album, 17, window_size[0] - 120 * gui.scale)
                                w = draw.text_calc(album, 17) + 30 * gui.scale
                                draw.line(right_position - w + 10 * gui.scale, y1, right_position + 20 * gui.scale, y1, colours.playlist_panel_background)
                                if gui.scale == 2:
                                    draw.line(right_position - w + 10 * gui.scale, y1 + 1, right_position + 20 * gui.scale,
                                              y1 + 1, colours.playlist_panel_background)
                                draw_text((right_position, y1 - 13 * gui.scale, 1), album, colours.folder_title, 17)



                        # Draw album art
                        a_rect = (x, y, self.pl_album_art_size, self.pl_album_art_size)
                        draw.rect_r(a_rect, [40, 40, 40, 50], True)
                        gall_ren.render(index_on, (x, y))

                        if right_click and coll_point(mouse_position, a_rect) and mouse_position[0] > 30 * gui.scale and \
                                        mouse_position[1] < window_size[1] - gui.panelBY - 10 * gui.scale:
                            combo_menu.activate(index_on, (mouse_position[0] + 5 * gui.scale, mouse_position[1] + 3 * gui.scale))

                    min = self.pl_album_art_size

            if render:

                x = self.pl_album_art_size + 20 * gui.scale
                y = pl_render_pos - self.pl_pos_px

                rect = [x, y, gui.playlist_width, prefs.playlist_row_height]
                s_rect = [x, y, gui.playlist_width - 15 * gui.scale, prefs.playlist_row_height - 1]
                fields.add(rect)
                # draw.rect_r(rect,[255,0,0,30], True)

                # Test if line hit
                line_hit = False
                if (input.mouse_click or right_click or middle_click) and coll_point(mouse_position, s_rect) and \
                                mouse_position[1] < window_size[1] - gui.panelBY and mouse_position[1] > gui.panelY:
                    line_hit = True
                    self.hit = True
                    quick_drag = True
                    gui.drag_source_position = copy.deepcopy(click_location)

                # Double click to play
                if d_mouse_click and line_hit and pl_entry_on == playlist_selected:
                    click_time -= 1.5
                    pctl.jump(default_playlist[pl_entry_on], pl_entry_on)

                # Test is line playing
                playing = False
                if len(pctl.track_queue) > 0 and pctl.track_queue[pctl.queue_step] == \
                        index_on:
                    playing = True
                    draw.rect_r(rect, colours.row_playing_highlight, True)

                # Make selected if clicked (we do this after the play click test thing)
                if line_hit:
                    playlist_selected = pl_entry_on
                    shift_selection = [playlist_selected]

                # Test if line selected
                this_line_selected = False
                if (pl_entry_on == playlist_selected and self.hit):
                    draw.rect_r(rect, colours.row_select_highlight, True)
                    this_line_selected = True

                # Calculate background after highlight
                if True:
                    if playing and this_line_selected:
                        gui.win_fore = alpha_blend(colours.row_select_highlight,
                                                   alpha_blend(colours.row_playing_highlight,
                                                               colours.playlist_panel_background))
                    elif playing and not this_line_selected:
                        gui.win_fore = alpha_blend(colours.row_playing_highlight, colours.playlist_panel_background)
                    elif this_line_selected:
                        gui.win_fore = alpha_blend(colours.row_select_highlight, colours.playlist_panel_background)
                    else:
                        gui.win_fore = colours.playlist_panel_background


                # Draw track text
                line_render(track, pl_entry_on, y + gui.playlist_text_offset, playing, 255, x + 17 * gui.scale, gui.playlist_width - 28 * gui.scale,
                            style=prefs.line_style)

                # Right click menu
                if right_click and line_hit:
                    track_menu.activate(index_on)
                    quick_drag = False

            # Move render position down for next track
            pl_entry_on += 1
            pl_render_pos += prefs.playlist_row_height
            min -= prefs.playlist_row_height


        # Set the render target back to window and render playlist texture
        SDL_SetRenderTarget(renderer, gui.main_texture)
        SDL_RenderCopy(renderer, gui.ttext, None, gui.abc)

    def cache_render(self):

        if input.mouse_click or right_click or middle_click:
            self.full_render()
            return
        # Render the cached playlist texture
        SDL_RenderCopy(renderer, gui.ttext, None, gui.abc)


combo_pl_render = ComboPlaylist()
playlist_render = StandardPlaylist()


class Showcase:

    def __init__(self):

        self.lastfm_artist = None
        self.artist_mode = False

    # def get_artist_info(self):
    #
    #     track = pctl.playing_object()
    #     if track is not None:
    #         artist = track.artist

    def render(self):

        draw.rect_r((0, gui.panelY, window_size[0], window_size[1] - gui.panelY), colours.playlist_panel_background, True)

        box = int(window_size[1] * 0.4 + 120)
        x = int(window_size[0] * 0.15)
        y = int((window_size[1] / 2) - (box / 2)) - 10

        if len(pctl.track_queue) < 1:
            return

        # if draw.button("Return", 20, gui.panelY + 5, bg=colours.grey(30)):
        #     pass

        if gui.force_showcase_index >= 0:
            if draw.button("Show playing", 25, gui.panelY + 20, bg=colours.grey(30)):
                gui.force_showcase_index = -1


        if gui.force_showcase_index >= 0:
            index = gui.force_showcase_index
            track = pctl.master_library[index]
        else:
            index = pctl.track_queue[pctl.queue_step]
            track = pctl.master_library[pctl.track_queue[pctl.queue_step]]

        # if self.artist_mode:
        #
        #     if track.artist == self.lastfm_artist:
        #
        #         return
        #
        # else:
        album_art_gen.display(index, (x, y), (box, box))
        if coll_point(mouse_position, (x, y, box, box)) and input.mouse_click is True:
            album_art_gen.cycle_offset(index)

        if track.lyrics == "":

            w = window_size[0] - (x + box) - 30
            x = int(x + box + (window_size[0] - x - box) / 2)

            y = int(window_size[1] / 2) - 60
            draw_text2((x, y, 2), track.artist, colours.side_bar_line1, 17, w)

            y += 45
            draw_text2((x, y, 2), track.title, colours.side_bar_line1, 228, w)

        else:
            x += box + int(window_size[0] * 0.15) + 20

            #y = 80
            x -= 100
            w = window_size[0] - x - 30


            if key_up_press:
                lyrics_ren.lyrics_position += 35
            if key_down_press:
                lyrics_ren.lyrics_position -= 35

            lyrics_ren.render(index,
                              x,
                              y + lyrics_ren.lyrics_position,
                              w,
                              int(window_size[1] - 100),
                              0)

        if gui.panelY < mouse_position[1] < window_size[1] - gui.panelBY:
            if mouse_wheel != 0:
                lyrics_ren.lyrics_position += mouse_wheel * 35
            if right_click:
                # track = pctl.playing_object()
                if track != None:
                    showcase_menu.activate(track)


showcase = Showcase()


class AlbumCard:

    def __init__(self):
        self.x = 100
        self.y = 100
        self.w = 350
        self.h = 500

        self.selected = 0
        self.active = False

    def activate(self, selected, x, y):

        self.selected = selected
        self.x = x
        self.y = y
        self.active = True

    def render(self):

        if not self.active:
            return

        bg = colours.sys_background_2

        tracks = get_album_info(self.selected)
        print(tracks)

        self.h = 25 + (16 * len(tracks[1]))

        c = colours.gallery_highlight
        c = [c[1], c[2], c[0], c[3]]
        draw.rect((self.x - 4 * gui.scale, self.y - 4 * gui.scale), (self.w + 8 * gui.scale, self.h + 8 * gui.scale),
                  c, True)

        #draw.rect_r([self.x - 2, self.y, self.w, self.h], bg, True)
        draw.rect_r([self.x, self.y, self.w, self.h], bg, True)

        y = self.y + 5

        for i, item in enumerate(tracks[1]):
            line_render(pctl.master_library[default_playlist[item]], item, y + (16 * i), False, 255, self.x + 10, self.w - 20)



album_card = AlbumCard()

class ColourPulse:

    def __init__(self, hue):
        self.timer = Timer()
        self.in_timer = Timer()
        self.out_timer = Timer()
        self.out_timer.start = 0
        self.active = False

        self.hue = hue

        self.max_sat = 0.75
        self.max_lumi = 0.45



    def get(self, hit, on):

        if on:
            rgb = colorsys.hls_to_rgb(self.hue, 0.15 + 0.4, 0.7)
            return [int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255), 255]

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


        lumi = 0
        sat = 0


        in_time = self.in_timer.get()
        out_time = self.out_timer.get()



        if self.active:
            if in_time < ani_time:
                gui.update = 2
                lumi = (in_time / ani_time) * self.max_lumi
            else:
                lumi = self.max_lumi

            if in_time < ani_time:
                sat = (in_time / ani_time) * self.max_sat
            else:
                sat = self.max_sat

        else:
            if out_time < ani_time:
                gui.update = 2
                lumi = self.max_lumi - ((out_time / ani_time) * self.max_lumi)
            else:
                lumi = 0

            if out_time < ani_time:
                sat = self.max_sat - ((out_time / ani_time) * self.max_sat)
            else:
                sat = 0

        lumi += 0.15


        rgb = colorsys.hls_to_rgb(self.hue, lumi, sat)
        return [int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255), 255]

class ViewBox:

    def __init__(self):
        self.x = 0
        self.y = gui.panelY
        self.w = 270 * gui.scale
        self.h = 95 * gui.scale
        self.active = False

        self.border = 3 * gui.scale

        if gui.scale == 1:
            self.tracks_img = WhiteModImageAsset("/gui/tracks.png")
            self.side_img = WhiteModImageAsset("/gui/tracks+side.png")
            self.gallery1_img = WhiteModImageAsset("/gui/gallery1.png")
            self.combo_img = WhiteModImageAsset("/gui/combo.png")
            self.lyrics_img = WhiteModImageAsset("/gui/lyrics.png")
            self.gallery2_img = WhiteModImageAsset("/gui/gallery2.png")
            self.col_img = WhiteModImageAsset("/gui/col.png")
        else:
            self.tracks_img = WhiteModImageAsset("/gui/2x/tracks.png")
            self.side_img = WhiteModImageAsset("/gui/2x/tracks+side.png")
            self.gallery1_img = WhiteModImageAsset("/gui/2x/gallery1.png")
            self.combo_img = WhiteModImageAsset("/gui/2x/combo.png")
            self.lyrics_img = WhiteModImageAsset("/gui/2x/lyrics.png")
            self.gallery2_img = WhiteModImageAsset("/gui/2x/gallery2.png")
            self.col_img = WhiteModImageAsset("/gui/2x/col.png")

        # self.tracks_colour = ColourPulse(0.0)
        # self.side_colour = ColourPulse(0.1)
        # self.gallery1_colour = ColourPulse(0.2)
        # self.combo_colour = ColourPulse(0.3)
        # self.lyrics_colour = ColourPulse(0.5)
        # self.gallery2_colour = ColourPulse(0.7)

        self.tracks_colour = ColourPulse(0.5)
        self.side_colour = ColourPulse(0.55)
        self.gallery1_colour = ColourPulse(0.6)
        self.combo_colour = ColourPulse(0.75)
        self.lyrics_colour = ColourPulse(0.7)
        self.gallery2_colour = ColourPulse(0.65)
        self.col_colour = ColourPulse(0.14)

        self.on_colour = [255, 190, 50, 255]
        self.over_colour = [255, 190, 50, 255]
        self.off_colour = colours.grey(40)

    def activate(self, x):
        self.x = x
        self.active = True

        self.tracks_colour.out_timer.force_set(10)
        self.side_colour.out_timer.force_set(10)
        self.gallery1_colour.out_timer.force_set(10)
        self.combo_colour.out_timer.force_set(10)
        self.lyrics_colour.out_timer.force_set(10)
        self.gallery2_colour.out_timer.force_set(10)
        self.col_colour.out_timer.force_set(10)

        self.tracks_colour.active = False
        self.side_colour.active = False
        self.gallery1_colour.active = False
        self.combo_colour.active = False
        self.lyrics_colour.active = False
        self.gallery2_colour.active = False
        self.col_colour.active = False

        gui.level_2_click = False
        gui.update = 2

    def button(self, x, y, asset, test, colour_get=None, name="Unknown"):

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
        if coll_point(mouse_position, rect):

            tool_tip.test(x + asset.w + 10 * gui.scale, y - 15 * gui.scale, name)

            col = True
            if gui.level_2_click:
                fun = test
            if colour_get is None:
                colour = self.over_colour

        if colour_get is not None:
            colour = colour_get.get(col, on)

        asset.render(x, y, colour)

        return fun

    def tracks(self, hit=False):

        if hit is False:
            return album_mode is False and \
                   gui.combo_mode is False and \
                   side_panel_enable is False
        view_tracks()

    def side(self, hit=False):

        if hit is False:
            return album_mode is False and \
                   gui.combo_mode is False and \
                   side_panel_enable is True
        view_standard_meta()

    def gallery1(self, hit=False):

        if hit is False:
            return album_mode is True and \
                   gui.combo_mode is False and \
                   gui.show_playlist is True
        force_album_view()

    def combo(self, hit=False):

        if hit is False:
            return album_mode is False and \
                   gui.combo_mode is True and \
                   gui.showcase_mode is False
        toggle_combo_view()

    def lyrics(self, hit=False):

        if hit is False:
            return album_mode is False and \
                   gui.combo_mode is True and \
                   gui.showcase_mode is True
        switch_showcase()

    def gallery2(self, hit=False):

        if hit is False:
            return album_mode is True and \
                   gui.combo_mode is False and \
                   gui.show_playlist is False
        gallery_only_view()

    def col(self, hit=False):

        if hit is False:
            return gui.set_mode
        toggle_library_mode()

    def render(self):

        rect = [self.x, self.y, self.w, self.h]

        if gui.level_2_click and not coll_point(mouse_position, rect):
            self.active = False
            gui.level_2_click = False
            return

        draw.rect_r(rect, colours.menu_background, True)

        draw.rect_r([self.x, self.y, self.border, self.h], colours.grey(30), True)
        draw.rect_r([self.x, self.y + self.h, self.w, self.border], colours.grey(30), True)
        draw.rect_r([self.x + self.w, self.y, self.border, self.h], colours.grey(30), True)

        x = self.x + 20 * gui.scale
        y = self.y + 15 * gui.scale

        func = None

        test = self.button(x, y, self.tracks_img, self.tracks, self.tracks_colour, "Tracks only")
        if test is not None:
            func = test

        x += 60 * gui.scale
        test = self.button(x, y, self.side_img, self.side, self.side_colour, "Tracks + Side bar")
        if test is not None:
            func = test

        x += 65 * gui.scale
        test = self.button(x, y, self.gallery1_img, self.gallery1, self.gallery1_colour, "Tracks + Gallery")
        if test is not None:
            func = test

        x = self.x + 21 * gui.scale
        y = self.y + 56 * gui.scale

        test = self.button(x, y, self.combo_img, self.combo, self.combo_colour, "Art + Tracks")
        if test is not None:
            func = test

        x += 63 * gui.scale
        test = self.button(x, y, self.lyrics_img, self.lyrics, self.lyrics_colour, "Art + Lyrics")
        if test is not None:
            func = test

        x += 68 * gui.scale
        test = self.button(x, y, self.gallery2_img, self.gallery2, self.gallery2_colour, "Gallery only")
        if test is not None:
            func = test

        test = self.button(x + 70 * gui.scale, y - 23 * gui.scale, self.col_img, self.col, self.col_colour, "Toggle columns")
        if test is not None:
            func = test

        if func is not None:
            func(True)
            self.active = False

        gui.level_2_click = False

view_box = ViewBox()


class GalleryJumper:

    def __init__(self):
        self.tags = []
        self.threshold = 8


    def calculate(self):

        #print(album_dex)

        self.tags = []
        def key(item):
            return len(item[0])

        for a, album in enumerate(album_dex):


            a1 = a - 25
            a2 = a + 25
            if a1 < 0:
                a1 = 1
            if a2 > len(album_dex) - 1:
                a2 = len(album_dex) - 1

            source = pctl.master_library[default_playlist[album]].parent_folder_path.replace("\\", "/")

            samples = album_dex[a1:a2]

            commons = []
            for q in samples:
                target = pctl.master_library[default_playlist[q]].parent_folder_path.replace("\\", "/")
                common_path = os.path.commonpath([source, target])
                #if pctl.master_library[default_playlist[q]].artist.lower() not in os.path.basename(target).lower():
                commons.append(common_path)


            counts = {i: commons.count(i) for i in commons}
            counts = list(counts.items())
            counts = sorted(counts, key=key)
            counts = list(reversed(counts))
            for i in reversed(range(len(counts))):
                if counts[i][1] < self.threshold:
                    del counts[i]

            #print(counts)

            if len(counts) == 0:
                continue

            #print("---")
            #print(self.tags[-1:][0][1])
            #print(counts[0][0])

            if len(self.tags) == 0 or self.tags[-1:][0][1] != os.path.basename(counts[0][0]):

                #print(self.tags[-1:][0][1])
                self.tags.append((album, os.path.basename(counts[0][0])))

        print(self.tags)
        print(len(self.tags))


gallery_jumper = GalleryJumper()


class Fader:

    def __init__(self):

        self.timer = Timer()
        self.timer.force_set(10)
        self.ani_duration = 0.3
        self.state = 0
        self.a = 0

    def render(self):

        if self.state == 0:
            t = self.timer.hit()
            self.a -= t / self.ani_duration
            self.a = max(0, self.a)
        if self.state == 1:
            t = self.timer.hit()
            self.a += t / self.ani_duration
            self.a = min(1, self.a)

        rect = [0, 0, window_size[0], window_size[1]]
        draw.rect_r(rect, [0, 0, 0, int(110 * self.a)], True)

        if not (self.a == 0 or self.a == 1):
            gui.update += 1

    def rise(self):

        self.state = 1
        self.timer.hit()

    def fall(self):

        self.state = 0
        self.timer.hit()

fader = Fader()

class EdgePulse:

    def __init__(self):

        self.timer = Timer()
        self.timer.force_set(10)
        self.ani_duration = 0.5

    def render(self, x, y, w, h, r=200, g=120, b=0):
        time = self.timer.get()
        if time < self.ani_duration:
            alpha = 255 - int(255 * (time / self.ani_duration))
            draw.rect_r((x, y, w, h), [r, g, b, alpha], True)
            gui.update = 2
            return True
        else:
            return False

    def pulse(self):
        self.timer.set()


edge_playlist = EdgePulse()
bottom_playlist = EdgePulse()
gallery_pulse_top = EdgePulse()
tab_pulse = EdgePulse()
lyric_side_top_pulse = EdgePulse()



def download_img(link, target_folder):
    try:
        response = urllib.request.urlopen(link)
        info = response.info()
        if info.get_content_maintype() == 'image':
            if info.get_content_subtype() == 'jpeg':
                save_target = os.path.join(target_dir, 'image.jpg')
                f = open(save_target, 'wb')
                f.write(response.read())
                f.close()
                clear_img_cache()

            elif info.get_content_subtype() == 'png':
                save_target = os.path.join(target_dir, 'image.png')
                f = open(save_target, 'wb')
                f.write(response.read())
                f.close()
                clear_img_cache()
            else:
                show_message("Image types other than PNG or JPEG are currently not supported", 'warning')
        else:
            show_message("The link does not appear to refer to an image file.", 'warning')
        gui.image_downloading = False


    except:
        show_message("Image download failed.", 'warning')
        gui.image_downloading = False

# Set SDL window drag areas
if system != 'windows':

    def hit_callback(win, point, data):

        if point.contents.y < 0 and point.contents.x > window_size[0]:
            return SDL_HITTEST_RESIZE_TOPRIGHT

        elif point.contents.y < 0 and point.contents.x < 1:
            return SDL_HITTEST_RESIZE_TOPLEFT

        elif draw_border and point.contents.y < 4 and point.contents.x < window_size[0] - 40:
            return SDL_HITTEST_RESIZE_TOP

        elif point.contents.y < 30 and top_panel.drag_zone_start_x < point.contents.x < window_size[0] - 80:

            if tab_menu.active: # or pctl.broadcast_active:
                return SDL_HITTEST_NORMAL
            return SDL_HITTEST_DRAGGABLE
        elif point.contents.x > window_size[0] - 20 and point.contents.y > window_size[1] - 20:
            return SDL_HITTEST_RESIZE_BOTTOMRIGHT
        elif point.contents.x < 5 and point.contents.y > window_size[1] - 5:
            return SDL_HITTEST_RESIZE_BOTTOMLEFT
        elif point.contents.y > window_size[1] - 7:
            return SDL_HITTEST_RESIZE_BOTTOM

        elif point.contents.x > window_size[0] - 4 and point.contents.y > 20:
            return SDL_HITTEST_RESIZE_RIGHT
        elif point.contents.x < 5:
            return SDL_HITTEST_RESIZE_LEFT

        else:
            return SDL_HITTEST_NORMAL


    c_hit_callback = SDL_HitTest(hit_callback)
    SDL_SetWindowHitTest(t_window, c_hit_callback, 0)
# --------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------

# MAIN LOOP---------------------------------------------------------------------------

gui.playlist_view_length = int(((window_size[1] - gui.playlist_top) / 16) - 1)

running = True
ab_click = False
d_border = 1

update_layout = True

event = SDL_Event()

mouse_moved = False

power = 0
key_F7 = False

r_arg_queue = copy.deepcopy(sys.argv)
arg_queue = []
for item in r_arg_queue:
    if (os.path.isdir(item) or os.path.isfile(item)) and '.py' not in item and 'tauon.exe' not in item:
        arg_queue.append(item)



sv = SDL_version()
SDL_GetVersion(sv)
sdl_version = sv.major * 100 + sv.minor * 10 + sv.patch
print("Using SDL verrsion: " + str(sv.major) + "." + str(sv.minor) + "." + str(sv.patch))
# time.sleep(13)
# C-ML
if default_player == 2:
    print("Using GStreamer as fallback. Some functions disabled")
elif default_player == 0:
    show_message("ERROR: No backend found", 'warning')

total = 0
if gui.set_load_old is False:
    for i in range(len(gui.pl_st) - 1):
        total += gui.pl_st[i][1]

    gui.pl_st[len(gui.pl_st) - 1][1] = gui.playlist_width + 31 - 16 - total


def update_layout_do():

    input.mouse_click = False
    if not gui.maximized:
        gui.save_size = copy.deepcopy(window_size)

    bottom_bar1.update()

    # if system != 'windows':
    #     if draw_border:
    #         gui.panelY = 30 * gui.scale + 3 * gui.scale
    #         top_panel.ty = 3 * gui.scale
    #     else:
    #         gui.panelY = 30 * gui.scale
    #         top_panel.ty = 0

    if gui.set_bar:
        gui.playlist_top = gui.playlist_top_bk + gui.set_height - 6 * gui.scale
    else:
        gui.playlist_top = gui.playlist_top_bk
    gui.offset_extra = 0
    if draw_border:
        gui.offset_extra = 61 * gui.scale

    global album_v_gap
    if gui.gallery_show_text:
        album_v_gap = 66 * gui.scale
    else:
        album_v_gap = 25 * gui.scale

    #gui.spec_rect[0] = window_size[0] - gui.offset_extra - 90
    gui.spec1_rec.x = window_size[0] - gui.offset_extra - 90 * gui.scale
    #gui.spec_x = window_size[0] - gui.offset_extra - 90

    gui.spec2_rec.x = window_size[0] - gui.spec2_rec.w - 10 * gui.scale - gui.offset_extra

    # if gui.vis == 3:
    #     if prefs.spec2_colour_setting == 'custom':
    #         prefs.spec2_base = prefs.spec2_p_base
    #         prefs.spec2_multiply = prefs.spec2_p_multiply
        # elif prefs.spec2_colour_setting == 'horizon':
        #     prefs.spec2_base = [10, 10, 100]
        #     prefs.spec2_multiply = [0.5, 1, 1]
        # elif prefs.spec2_colour_setting == 'plasma':
        #     prefs.spec2_base = [10, 10, 10]
        #     prefs.spec2_multiply = [2, 1.2, 5]
        # elif prefs.spec2_colour_setting == 'grey':
        #     prefs.spec2_base = [20, 20, 20]
        #     prefs.spec2_multiply = [1, 1, 1]

    gui.scroll_hide_box = (1 if not gui.maximized else 0, gui.panelY, 28 * gui.scale, window_size[1] - gui.panelBY - gui.panelY)

    if gui.combo_mode:
        gui.playlist_row_height = prefs.playlist_row_height #31
        gui.row_font_size = prefs.playlist_font_size
        gui.pl_text_real_height = draw.text_calc("Testあ9", gui.row_font_size, False, True)
        gui.playlist_text_offset = (int((gui.playlist_row_height - gui.pl_text_real_height) / 2))#6
         #13
        gui.scroll_hide_box = (window_size[0] - (28 * gui.scale) - 2 * gui.scale, gui.panelY, 28 * gui.scale, window_size[1] - gui.panelBY - gui.panelY)
    else:
        gui.scroll_hide_box = (1, gui.panelY, 28 * gui.scale, window_size[1] - gui.panelBY - gui.panelY)
        gui.playlist_row_height = prefs.playlist_row_height
        gui.playlist_text_offset = 0
        gui.row_font_size = prefs.playlist_font_size  # 13
        gui.pl_text_real_height = draw.text_calc("Testあ9", gui.row_font_size, False, True)
        gui.pl_title_real_height = draw.text_calc("Testあ9", gui.row_font_size + gui.pl_title_font_offset, False, True)
        gui.playlist_text_offset = (int((gui.playlist_row_height - gui.pl_text_real_height) / 2))
        # To improve
        if system == 'linux' and gui.scale == 1:
            gui.playlist_text_offset = int(round((gui.playlist_row_height + 0.5 - 0) / 2)) - 11 #* gui.scale
            #gui.playlist_text_offset = int(round((gui.playlist_row_height + 0.5 - 0) / 2)) - 11 #* gui.scale
        if system == 'windows':
            gui.playlist_text_offset -= 1

    # if gui.scale > 1:
    #     #gui.playlist_text_offset += 17
    #     #gui.playlist_row_height *= gui.scale
    #     pass

    gui.playlist_view_length = int(((window_size[1] - gui.panelBY - gui.playlist_top) / gui.playlist_row_height) - 1)

    if side_panel_enable is True:

        if gui.side_panel_size < 100 * gui.scale:
            gui.side_panel_size = 100 * gui.scale


        if gui.side_panel_size > window_size[1] - 77 * gui.scale and album_mode is not True:
            gui.side_panel_size = window_size[1] - 77 * gui.scale

        if gui.side_panel_size > window_size[0] - 300 * gui.scale and album_mode is True:
            gui.side_panel_size = window_size[0] - 300 * gui.scale


        if album_mode != True:
            gui.playlist_width = window_size[0] - gui.side_panel_size - 30 * gui.scale
        else:
            gui.side_panel_size = window_size[0] - gui.playlist_width - 30 * gui.scale

    else:
        gui.playlist_width = window_size[0] - 30 * gui.scale
        #gui.playlist_width = window_size[0] - 80 * gui.scale
        # if custom_line_mode:
        #     gui.playlist_width = window_size[0] - 30

    # tttt
    if gui.combo_mode:
        gui.playlist_width -= combo_pl_render.pl_album_art_size

    if window_size[0] < 630 * gui.scale:
        gui.compact_bar = True
    else:
        gui.compact_bar = False

    gui.abc = SDL_Rect(0, 0, window_size[0], window_size[1])

    if GUI_Mode == 2:
        SDL_DestroyTexture(gui.ttext)
        gui.panelBY = 30 * gui.scale
        gui.panelY = 0
        gui.playlist_top = 5 * gui.scale

        gui.pl_update = 1

        gui.playlist_view_length = int(((window_size[1] - gui.playlist_top) / gui.playlist_row_height) - 0) - 3

    if GUI_Mode == 1:
        SDL_DestroyTexture(gui.ttext)
        gui.pl_update = 1
    update_set()

    SDL_DestroyTexture(gui.main_texture)

    gui.ttext = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_UNKNOWN, SDL_TEXTUREACCESS_TARGET, window_size[0],
                              window_size[1])
    SDL_SetTextureBlendMode(gui.ttext, SDL_BLENDMODE_BLEND)
    SDL_SetRenderTarget(renderer, gui.ttext)
    SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
    SDL_RenderClear(renderer)

    gui.main_texture = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_UNKNOWN, SDL_TEXTUREACCESS_TARGET, window_size[0],
                              window_size[1])
    SDL_SetTextureBlendMode(gui.main_texture, SDL_BLENDMODE_NONE)
    SDL_SetRenderTarget(renderer, gui.main_texture)
    SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
    SDL_SetRenderTarget(renderer, gui.main_texture)
    SDL_RenderClear(renderer)



SDL_SetRenderTarget(renderer, None)
SDL_RenderClear(renderer)
SDL_RenderPresent(renderer)

SDL_ShowWindow(t_window)

# Clear spectogram texture
SDL_SetRenderTarget(renderer, gui.spec2_tex)
SDL_RenderClear(renderer)
draw.rect_r((0, 0, 1000, 1000), [7, 7, 7, 255], True)

SDL_SetRenderTarget(renderer, gui.spec1_tex)
SDL_RenderClear(renderer)
draw.rect_r((0, 0, 1000, 1000), [7, 7, 7, 255], True)

SDL_SetRenderTarget(renderer, gui.spec_level_tex)
SDL_RenderClear(renderer)
draw.rect_r((0, 0, 1000, 1000), [7, 7, 7, 255], True)

SDL_SetRenderTarget(renderer, None)

#SDL_RenderPresent(renderer)

#time.sleep(3)

class GetSDLInput:

    def __init__(self):
        self.i_y = pointer(c_int(0))
        self.i_x = pointer(c_int(0))

    def mouse(self):
        SDL_PumpEvents()
        SDL_GetMouseState(self.i_x, self.i_y)
        return self.i_x.contents.value, self.i_y.contents.value

gal_up = False
gal_down = False
gal_left = False
gal_right = False


get_sdl_input = GetSDLInput()

def window_is_focused():  # thread safe?
    if SDL_GetWindowFlags(t_window) & SDL_WINDOW_INPUT_FOCUS:
        return True
    return False


def save_state():

    print("Writing database to disk.")

    view_prefs['star-lines'] = star_lines
    view_prefs['update-title'] = update_title
    view_prefs['side-panel'] = prefs.prefer_side
    view_prefs['dim-art'] = prefs.dim_art
    view_prefs['level-meter'] = gui.turbo
    view_prefs['pl-follow'] = pl_follow
    view_prefs['scroll-enable'] = scroll_enable
    view_prefs['break-enable'] = break_enable
    view_prefs['dd-index'] = dd_index
    view_prefs['append-date'] = prefs.append_date

    save = [pctl.master_library,
            master_count,
            pctl.playlist_playing,
            pctl.playlist_active,
            playlist_position,
            pctl.multi_playlist,
            pctl.player_volume,
            pctl.track_queue,
            pctl.queue_step,
            default_playlist,
            pctl.playlist_playing,
            None, # Was cue list
            radio_field.text,
            theme,
            folder_image_offsets,
            lfm_username,
            lfm_hash,
            2.1,  # Version, used for upgrading
            view_prefs,
            gui.save_size,
            gui.side_panel_size,
            0,  # save time (unused)
            gui.vis,
            playlist_selected,
            album_mode_art_size,
            draw_border,
            prefs.enable_web,
            prefs.allow_remote,
            prefs.expose_web,
            prefs.enable_transcode,
            prefs.show_rym,
            combo_mode_art_size,
            gui.maximized,
            prefs.prefer_bottom_title,
            gui.display_time_mode,
            prefs.transcode_mode,
            prefs.transcode_codec,
            prefs.transcode_bitrate,
            prefs.line_style,
            prefs.cache_gallery,
            prefs.playlist_font_size,
            prefs.use_title,
            gui.pl_st,
            gui.set_mode,
            None,
            prefs.playlist_row_height,
            prefs.show_wiki,
            prefs.auto_extract,
            prefs.colour_from_image,
            gui.set_bar,
            gui.gallery_show_text,
            gui.bb_show_art,
            gui.show_stars,
            prefs.auto_lfm,
            prefs.scrobble_mark,
            prefs.replay_gain,
            prefs.radio_page_lyrics,
            prefs.show_gimage,
            prefs.end_setting,
            prefs.show_gen,
            pctl.save_urls,
            prefs.auto_del_zip,
            gui.level_meter_colour_mode,
            prefs.ui_scale,
            prefs.show_lyrics_side,
            None,
            None]

    pickle.dump(save, open(user_directory + "/state.p", "wb"))

# SDL_StartTextInput()
# SDL_SetHint(SDL_HINT_IME_INTERNAL_EDITING, b"1")
# SDL_EventState(SDL_SYSWMEVENT, 1)


while running:
    # bm.get('main')

    if k_input:
        d_mouse_click = False
        mouse4 = False
        mouse5 = False
        right_click = False
        level_2_right_click = False
        input.mouse_click = False
        middle_click = False
        mouse_up = False
        key_return_press = False
        key_ralt = False
        # key_space_press = False
        key_down_press = False
        key_up_press = False
        key_right_press = False
        key_left_press = False
        key_backslash_press = False
        key_esc_press = False
        key_F11 = False
        key_F8 = False
        key_F10 = False
        key_F2 = False
        key_F3 = False
        key_F4 = False
        key_F5 = False
        key_F6 = False
        # key_F7 = False
        key_F9 = False
        key_F1 = False
        key_PGU = False
        key_PGD = False
        key_del = False
        key_backspace_press = False
        # key_1_press = False
        # key_2_press = False
        # key_3_press = False
        # key_4_press = False
        # key_5_press = False
        key_c_press = False
        key_v_press = False
        key_f_press = False
        key_a_press = False
        key_w_press = False
        key_z_press = False
        key_x_press = False
        key_r_press = False
        key_dash_press = False
        key_eq_press = False
        key_slash_press = False
        key_period_press = False
        key_comma_press = False
        key_quote_hit = False
        key_col_hit = False
        key_tab = False
        key_tilde = False
        key_home_press = False
        key_end_press = False
        mouse_wheel = 0
        new_playlist_cooldown = False
        input_text = ''
        input.level_2_enter = False

    if not mouse_down:
        k_input = False

    clicked = False
    focused = False
    mouse_moved = False

    while SDL_PollEvent(ctypes.byref(event)) != 0:

        #print(event.type)

        # if event.type == SDL_SYSWMEVENT:
        #      print(event.syswm.msg.contents) # Not implemented

        if event.type == SDL_DROPTEXT:

            link = event.drop.file.decode()
            if pctl.playing_ready and 'http' in link:
                if system != 'windows' and sdl_version >= 204:
                    gmp = get_global_mouse()
                    gwp = get_window_position()
                    i_x = gmp[0] - gwp[0]
                    if i_x < 0:
                        i_x = 0
                    if i_x > window_size[0]:
                        i_x = window_size[0]
                    i_y = gmp[1] - gwp[1]
                    if i_y < 0:
                        i_y = 0
                    if i_y > window_size[1]:
                        i_y = window_size[1]
                else:
                    i_y = pointer(c_int(0))
                    i_x = pointer(c_int(0))

                    SDL_GetMouseState(i_x, i_y)
                    i_y = i_y.contents.value
                    i_x = i_x.contents.value

                if coll_point((i_x, i_y), gui.main_art_box):

                    print('Drop picture...')
                    print(link)
                    gui.image_downloading = True
                    track = pctl.playing_object()
                    target_dir = track.parent_folder_path

                    shoot_dl = threading.Thread(target=download_img, args=(link, target_dir))
                    shoot_dl.daemon = True
                    shoot_dl.start()

                    gui.update = True

        if event.type == SDL_DROPFILE:
            power += 5
            k = 0

            if system != 'windows' and sdl_version >= 204:
                gmp = get_global_mouse()
                gwp = get_window_position()
                i_x = gmp[0] - gwp[0]
                if i_x < 0:
                    i_x = 0
                if i_x > window_size[0]:
                    i_x = window_size[0]
                i_y = gmp[1] - gwp[1]
                if i_y < 0:
                    i_y = 0
                if i_y > window_size[1]:
                    i_y = window_size[1]
            else:
                i_y = pointer(c_int(0))
                i_x = pointer(c_int(0))

                SDL_GetMouseState(i_x, i_y)
                i_y = i_y.contents.value
                i_x = i_x.contents.value

            # print((i_x, i_y))
            playlist_target = 0
            #print(event.drop)

            if i_y < gui.panelY and not new_playlist_cooldown:
                x = top_panel.start_space_left
                for w in range(len(pctl.multi_playlist)):
                    wid = top_panel.tab_text_spaces[w] + top_panel.tab_extra_width

                    if x < i_x < x + wid:
                        playlist_target = w
                        tab_pulse.pulse()
                        gui.update += 1
                        gui.pl_pulse = True

                        print("Direct drop")
                        break
                    x += wid
                else:
                    print("MISS")
                    if new_playlist_cooldown:
                        playlist_target = pctl.playlist_active
                    else:
                        playlist_target = new_playlist()
                        new_playlist_cooldown = True

            else:
                playlist_target = pctl.playlist_active


            dropped_file_sdl = event.drop.file
            load_order = LoadClass()
            load_order.target = str(urllib.parse.unquote(dropped_file_sdl.decode("utf-8")))

            pctl.multi_playlist[playlist_target][7] = load_order.target

            load_order.playlist = pctl.multi_playlist[playlist_target][6]
            load_orders.append(copy.deepcopy(load_order))


            # print('dropped: ' + str(dropped_file))
            gui.update += 1

            mouse_down = False
            drag_mode = False
        elif event.type == 8192:
            gui.pl_update = 1
            gui.update += 2

        elif event.type == SDL_QUIT:
            power += 5
            running = False
            break
        elif event.type == SDL_TEXTEDITING:
            power += 5
            print("edit text")
            editline = event.edit.text
            editline = editline.decode("utf-8", 'ignore')
            k_input = True
            gui.update += 1

        elif event.type == SDL_MOUSEMOTION:

            mouse_position[0] = event.motion.x
            mouse_position[1] = event.motion.y
            mouse_moved = True
        elif event.type == SDL_MOUSEBUTTONDOWN:

            # mouse_position[0] = event.motion.x
            # mouse_position[1] = event.motion.y
            # print(mouse_position)
            #
            # mouse_moved = True

            k_input = True
            focused = True
            power += 5
            gui.update += 1

            if event.button.button == SDL_BUTTON_RIGHT:
                right_click = True
                right_down = True
            elif event.button.button == SDL_BUTTON_LEFT:

                if mouse_position[1] > 1 and mouse_position[0] > 1:
                    mouse_down = True

                input.mouse_click = True

                mouse_down = True
            elif event.button.button == SDL_BUTTON_MIDDLE:
                middle_click = True
                gui.update += 1
            elif event.button.button == SDL_BUTTON_X1:
                mouse4 = True
            elif event.button.button == SDL_BUTTON_X2:
                mouse5 = True
        elif event.type == SDL_MOUSEBUTTONUP:
            k_input = True
            power += 5
            gui.update += 1
            if event.button.button == SDL_BUTTON_RIGHT:
                right_down = False
            elif event.button.button == SDL_BUTTON_LEFT:

                mouse_down = False
                mouse_up = True
        elif event.type == SDL_KEYDOWN:
            k_input = True
            power += 5
            gui.update += 2
            if event.key.keysym.sym == SDLK_RETURN and len(editline) == 0:
                key_return_press = True
            # elif event.key.keysym.sym == SDLK_SPACE:
            #     key_space_press = True
            elif event.key.keysym.sym == SDLK_BACKSPACE:
                key_backspace_press = True
            elif event.key.keysym.sym == SDLK_DELETE:
                key_del = True
            elif event.key.keysym.sym == SDLK_ESCAPE:
                key_esc_press = True
            elif event.key.keysym.sym == SDLK_RALT:
                key_ralt = True
            elif event.key.keysym.sym == SDLK_F11:
                key_F11 = True
            elif event.key.keysym.sym == SDLK_F10:
                key_F10 = True
            elif event.key.keysym.sym == SDLK_F8:
                key_F8 = True
            elif event.key.keysym.sym == SDLK_F2:
                key_F2 = True
            elif event.key.keysym.sym == SDLK_F1:
                key_F1 = True
            elif event.key.keysym.sym == SDLK_F3:
                key_F3 = True
            elif event.key.keysym.sym == SDLK_F4:
                key_F4 = True
            elif event.key.keysym.sym == SDLK_F5:
                key_F5 = True
            elif event.key.keysym.sym == SDLK_F6:
                key_F6 = True
            elif event.key.keysym.sym == SDLK_F7:
                key_F7 = True
            elif event.key.keysym.sym == SDLK_F9:
                key_F9 = True
            elif event.key.keysym.sym == SDLK_PAGEUP:
                key_PGU = True
            elif event.key.keysym.sym == SDLK_PAGEDOWN:
                key_PGD = True
            elif event.key.keysym.sym == SDLK_v:
                key_v_press = True
            elif event.key.keysym.sym == SDLK_f:
                key_f_press = True
            elif event.key.keysym.sym == SDLK_a:
                key_a_press = True
            elif event.key.keysym.sym == SDLK_c:
                key_c_press = True
            elif event.key.keysym.sym == SDLK_w:
                key_w_press = True
            elif event.key.keysym.sym == SDLK_z:
                key_z_press = True
            elif event.key.keysym.sym == SDLK_x:
                key_x_press = True
            elif event.key.keysym.sym == SDLK_r:
                key_r_press = True
            elif event.key.keysym.sym == SDLK_BACKSLASH:
                key_backslash_press = True
            elif event.key.keysym.sym == SDLK_DOWN:
                key_down_press = True
            elif event.key.keysym.sym == SDLK_UP:
                key_up_press = True
            elif event.key.keysym.sym == SDLK_LEFT:
                key_left_press = True
            elif event.key.keysym.sym == SDLK_RIGHT:
                key_right_press = True
            # elif event.key.keysym.sym == SDLK_1:
            #     key_1_press = True
            # elif event.key.keysym.sym == SDLK_2:
            #     key_2_press = True
            # elif event.key.keysym.sym == SDLK_3:
            #     key_3_press = True
            # elif event.key.keysym.sym == SDLK_4:
            #     key_4_press = True
            # elif event.key.keysym.sym == SDLK_5:
            #     key_5_press = True
            elif event.key.keysym.sym == SDLK_MINUS:
                key_dash_press = True
            elif event.key.keysym.sym == SDLK_EQUALS:
                key_eq_press = True
            elif event.key.keysym.sym == SDLK_LSHIFT:
                key_shift_down = True
            elif event.key.keysym.sym == SDLK_RSHIFT:
                key_shiftr_down = True
            elif event.key.keysym.sym == SDLK_SLASH:
                key_slash_press = True
            elif event.key.keysym.sym == SDLK_PERIOD:
                key_period_press = True
            elif event.key.keysym.sym == SDLK_COMMA:
                key_comma_press = True
            elif event.key.keysym.sym == SDLK_QUOTE:
                key_quote_hit = True
            elif event.key.keysym.sym == SDLK_SEMICOLON:
                key_col_hit = True
            elif event.key.keysym.sym == SDLK_TAB:
                key_tab = True
            elif event.key.keysym.sym == SDLK_LCTRL:
                key_ctrl_down = True
            elif event.key.keysym.sym == SDLK_BACKQUOTE:
                key_tilde = True
            elif event.key.keysym.sym == SDLK_HOME:
                key_home_press = True
            elif event.key.keysym.sym == SDLK_END:
                key_end_press = True

        elif event.type == SDL_KEYUP:
            k_input = True
            power += 5
            gui.update += 2
            if event.key.keysym.sym == SDLK_LSHIFT:
                key_shift_down = False
            elif event.key.keysym.sym == SDLK_LCTRL:
                key_ctrl_down = False
            elif event.key.keysym.sym == SDLK_RSHIFT:
                key_shiftr_down = False
        elif event.type == SDL_TEXTINPUT:
            k_input = True
            power += 5
            input_text = event.text.text
            input_text = input_text.decode('utf-8')
            gui.update += 1
            # print(input_text)

        elif event.type == SDL_MOUSEWHEEL:
            k_input = True
            power += 6
            mouse_wheel += event.wheel.y
            gui.update += 1
        elif event.type == SDL_WINDOWEVENT:

            power += 5
            # print(event.window.event)

            if event.window.event == SDL_WINDOWEVENT_FOCUS_GAINED:

                focused = True
                mouse_down = False
                gui.pl_update = 1
                gui.update += 1

            elif event.window.event == SDL_WINDOWEVENT_FOCUS_LOST:
                for instance in Menu.instances:
                    instance.active = False

                gui.update += 1

            elif event.window.event == SDL_WINDOWEVENT_RESIZED:
                gui.update += 1
                window_size[0] = event.window.data1
                window_size[1] = event.window.data2
                update_layout = True
                gui.maximized = False
                # print('resize')

            # elif event.window.event == SDL_WINDOWEVENT_HIDDEN:
            #
            elif event.window.event == SDL_WINDOWEVENT_EXPOSED:
                # print("expose")
                gui.lowered = False

            elif event.window.event == SDL_WINDOWEVENT_MINIMIZED:
                gui.lowered = True

            elif event.window.event == SDL_WINDOWEVENT_RESTORED:
                gui.lowered = False

                gui.pl_update = 1
                gui.update += 1

                if update_title:
                    update_title_do()
                    # print("restore")

            elif event.window.event == SDL_WINDOWEVENT_SHOWN:
                focused = True
                gui.pl_update = 1
                gui.update += 1

            elif event.window.event == SDL_WINDOWEVENT_MAXIMIZED:
                gui.maximized = True
                update_layout = True
                gui.pl_update = 1
                gui.update += 1

    if mouse_moved:
        if fields.test():
            gui.update += 1

    if gui.request_raise:
        gui.request_raise = False
        if gui.lowered:
            SDL_RestoreWindow(t_window)
            SDL_RaiseWindow(t_window)
            gui.lowered = False

    # ----------------
    # This section of code controls the internal processing speed or 'frame-rate'.
    # It's a complete mess. And doesn't work the best. It's just hack on top of hack.

    power += 1

    if gui.frame_callback_list:
        i = len(gui.frame_callback_list) - 1
        while i >= 0:
            #print(gui.frame_callback_list[i])
            if gui.frame_callback_list[i].test():
                gui.update = 1
                power = 1000
                #print("FRAME CALLBACK")
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


    if mouse_wheel != 0 or k_input or gui.update > 0 or mouse_down or len(top_panel.adds) > 0: # or mouse_moved:
        power = 1000

    # if resize_mode or scroll_hold or album_scroll_hold:
    #     power += 3
    # if side_drag:
    #     power += 2


    if gui.level_update and not album_scroll_hold and not scroll_hold:
        power = 500

    if gui.vis == 3 and (pctl.playing_state == 1 or pctl.playing_state == 3):
        power = 500
        if len(gui.spec2_buffers) > 0 and gui.spec2_timer.get() > 0.04:
            gui.spec2_timer.set()
            #gui.spec2_timer.force_set(gui.spec2_timer.get() - 0.04)
            gui.level_update = True
            vis_update = True
        else:
            SDL_Delay(5)

    if not running:
        break


    if pctl.playing_state > 0 or pctl.broadcast_active:
        power += 400
    if power < 500:
        #time.sleep(0.003)
        #time.sleep(0.003)
        SDL_Delay(30)
        # if gui.lowered:
        #     time.sleep(0.2)
        if pctl.playing_state == 0 and len(load_orders) == 0 and gui.update == 0:
                SDL_WaitEventTimeout(None, 1000)

        continue

    else:
        power = 0

    if gui.pl_update > 2:
        gui.pl_update = 2

    new_playlist_cooldown = False

    if not k_input:
        time.sleep(0.006)
    # print(k_input)



    if check_file_timer.get() > 1.1:
        check_file_timer.set()
        if os.path.isfile(transfer_target):
            r_arg_queue = pickle.load(open(transfer_target, "rb"))
            os.remove(user_directory + "/transfer.p")
            arg_queue = []
            for item in r_arg_queue:
                if (os.path.isdir(item) or os.path.isfile(item)) and '.py' not in item:
                    arg_queue.append(item)
                    # SDL_RaiseWindow(t_window)
                    # SDL_RestoreWindow(t_window)

        if arg_queue:
            i = 0
            while i < len(arg_queue):
                load_order = LoadClass()

                for w in range(len(pctl.multi_playlist)):
                    if pctl.multi_playlist[w][0] == "Default":
                        load_order.playlist = pctl.multi_playlist[w][6] # copy.deepcopy(w)
                        break
                else:
                    # pctl.multi_playlist.append(["Default", 0, [], 0, 0, 0])
                    pctl.multi_playlist.append(pl_gen())
                    load_order.playlist = pctl.multi_playlist[len(pctl.multi_playlist) - 1][6]
                    switch_playlist(len(pctl.multi_playlist) - 1)

                load_order.target = arg_queue[i]
                load_orders.append(copy.deepcopy(load_order))

                i += 1
            arg_queue = []
            auto_play_import = True


    if mouse_down and not rect_in((2, 2, window_size[0] - 4, window_size[1] - 4)):
        if SDL_GetGlobalMouseState(None, None) == 0:

            mouse_down = False
            mouse_up = True
            quick_drag = False

    if k_input:

        if input.mouse_click or right_click:
            last_click_location = copy.deepcopy(click_location)
            click_location = copy.deepcopy(mouse_position)

        if key_F11:
            if fullscreen == 0:
                fullscreen = 1
                SDL_SetWindowFullscreen(t_window, SDL_WINDOW_FULLSCREEN_DESKTOP)
            elif fullscreen == 1:
                fullscreen = 0
                SDL_SetWindowFullscreen(t_window, 0)
        if fullscreen == 1 and key_esc_press:
            fullscreen = 0
            SDL_SetWindowFullscreen(t_window, 0)

        if key_F10:
            if d_border == 0:
                d_border = 1
                SDL_SetWindowBordered(t_window, SDL_TRUE)

            elif d_border == 1:
                d_border = 0
                SDL_SetWindowBordered(t_window, SDL_FALSE)

        if key_F8:
            pass

        # Disable keys for text cursor control
        if not gui.rename_folder_box and not renamebox and not rename_playlist_box and not radiobox and not pref_box.enabled:

            if key_tab:
                gui.album_tab_mode ^= True
                if not album_mode:
                    toggle_album_mode()
                    gui.gall_tab_enter = True
                elif gui.gall_tab_enter:
                    toggle_album_mode()

            if not quick_search_mode:
                if album_mode and gui.album_tab_mode:
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


            if key_del:
                del_selected()

            # Arrow keys to change playlist
            if (key_left_press or key_right_press) and len(pctl.multi_playlist) > 1 and not key_shiftr_down and not key_shift_down:
                gui.pl_update = 1
                gui.update += 1
                if key_left_press:
                    switch_playlist(-1, True)
                if key_right_press:
                    switch_playlist(1, True)

            if key_home_press:
                if key_shift_down or key_shiftr_down:
                    playlist_position = 0
                    playlist_selected = 0
                    gui.pl_update = 1
                else:
                    if pctl.playing_time < 4:
                        pctl.back()
                    else:
                        pctl.new_time = 0
                        pctl.playing_time = 0
                        pctl.playerCommand = 'seek'
                        pctl.playerCommandReady = True
            if key_end_press:
                if key_shift_down or key_shiftr_down:
                    n = len(default_playlist) - gui.playlist_view_length + 1
                    if n < 0:
                        n = 0
                    playlist_position = n
                    playlist_selected = len(default_playlist) - 1
                    gui.pl_update = 1
                else:
                    pctl.advance()

        if not quick_search_mode and not pref_box.enabled and not radiobox and not renamebox \
                and not gui.rename_folder_box \
                and not rename_playlist_box:

            if key_c_press and key_ctrl_down:
                gui.pl_update = 1
                s_copy()

            if key_x_press and key_ctrl_down:
                gui.pl_update = 1
                s_cut()

            if key_v_press and key_ctrl_down:
                gui.pl_update = 1
                paste()

        if key_return_press and (gui.rename_folder_box or renamebox or radiobox):
            key_return_press = False
            input.level_2_enter = True

        if key_F1:
            # Toggle force off folder break for viewed playlist
            pctl.multi_playlist[pctl.playlist_active][4] ^= 1
            gui.pl_update = 1

        if key_F5:
            show_message("This button doesn't do anything.")
            # pctl.playerCommand = 'encpause'
            # pctl.playerCommandReady = True

        if key_F6:
            pctl.join_broadcast ^= True
            print("Join brodcast commands:" + str(pctl.join_broadcast))

        if key_F4:
            #standard_size()
            if len(pctl.track_queue) > 0:
                quick_search_mode = True
                search_text.text = ""
                input_text = pctl.playing_object().artist

            #show_message("This function has been removed", 'info')

        if key_ctrl_down and key_z_press:
            if pctl.playlist_backup != []:
                pctl.multi_playlist.append(pctl.playlist_backup)
                pctl.playlist_backup = []
                # show_message("There is no undo, sorry.")
        if key_F9:
            open_encode_out()

        if key_tilde:
            playlist_panel ^= True

        if key_F7:

            show_message("You don't even know what this button could have done.", 'warning')

            gallery_jumper.calculate()

            # colours.level_1_bg = [0, 6, 30, 255]
            # colours.level_2_bg = [0, 6, 30, 255]
            # colours.level_3_bg = [0, 6, 30, 255]
            # colours.level_green = [10, 100, 255, 255]
            # colours.level_yellow = [10, 100, 255, 255]
            # colours.level_red = [110, 85, 255, 255]


            # gd = {}
            #
            # for item in default_playlist:
            #     genre = pctl.g(item).genre
            #     if genre != "":
            #         if genre in gd:
            #             gd[genre] += 1
            #         else:
            #             gd[genre] = 1
            #
            # gl = gd.items()
            # gl = list(reversed(sorted(gl, key=lambda x: x[1])))
            # print(gl)
            # print(sum(x[1] for x in gl))



            key_F7 = False


        if key_F3:
            prefs.colour_from_image ^= True
            if prefs.colour_from_image:
                show_message("Enabled auto theme")
            else:
                show_message("Disabled auto theme")
                themeChange = True
                gui.theme_temp_current = -1

        if mouse4:
            toggle_album_mode()
        if mouse5:
            toggle_side_panel()

        ab_click = False

        if key_a_press and key_ctrl_down:
            gui.pl_update = 1
            shift_selection = range(len(default_playlist))


        if key_w_press and key_ctrl_down:
            delete_playlist(pctl.playlist_active)

        if key_r_press and key_ctrl_down:
            rename_playlist(pctl.playlist_active)

        # Transfer click register to menus
        if input.mouse_click:
            for instance in Menu.instances:
                if instance.active:
                    instance.click()
                    input.mouse_click = False
                    ab_click = True

        if input.mouse_click and (radiobox or gui.rename_folder_box or rename_playlist_box or renamebox or view_box.active) and not gui.message_box:
            input.mouse_click = False
            gui.level_2_click = True

        if track_box and input.mouse_click:
            w = 540
            h = 240
            x = int(window_size[0] / 2) - int(w / 2)
            y = int(window_size[1] / 2) - int(h / 2)
            if rect_in([x, y, w, h]):
                input.mouse_click = False
                gui.level_2_click = True

        if pref_box.enabled:

            if pref_box.inside():
                if input.mouse_click:
                    pref_box.click = True
                    input.mouse_click = False
                if right_click:
                    right_click = False
                    pref_box.right_click = True

                pref_box.scroll = mouse_wheel
                mouse_wheel = 0
            else:
                if input.mouse_click:
                    pref_box.enabled = False
                    fader.fall()
                if right_click:
                    pref_box.enabled = False
                    fader.fall()
                if pref_box.lock is False:
                    pass

        if right_click:
            level_2_right_click = True

        if right_click and (radiobox or renamebox or rename_playlist_box or gui.rename_folder_box):
            right_click = False

        if combo_menu.active and right_click:
            combo_menu.active = False

        genre_box_click = False
        if playlist_panel and input.mouse_click:
            input.mouse_click = False
            genre_box_click = True

        if mouse_wheel != 0:
            gui.update += 1
        if mouse_down is True:
            gui.update += 1

        if key_PGD:
            if len(default_playlist) > 10:
                playlist_position += gui.playlist_view_length - 4
                if playlist_position > len(default_playlist):
                    playlist_position = len(default_playlist) - 2
                gui.pl_update = 1
        if key_PGU:
            if len(default_playlist) > 0:
                playlist_position -= gui.playlist_view_length - 4
                if playlist_position < 0:
                    playlist_position = 0
                gui.pl_update = 1



        if input.mouse_click:
            n_click_time = time.time()
            if n_click_time - click_time < 0.42:
                d_mouse_click = True
            click_time = n_click_time

        if quick_search_mode is False and renamebox is False and gui.rename_folder_box is False and rename_playlist_box is False and not pref_box.enabled:

            if (key_shiftr_down or key_shift_down) and key_right_press:
                key_right_press = False
                pctl.advance()
                # print('hit')
            if (key_shiftr_down or key_shift_down) and key_left_press:
                key_left_press = False
                pctl.back()

            if (key_shiftr_down or key_shift_down) and key_up_press:
                key_up_press = False
                pctl.player_volume += 3
                if pctl.player_volume > 100:
                    pctl.player_volume = 100
                pctl.set_volume()

            if (key_shiftr_down or key_shift_down) and key_down_press:
                key_down_press = False
                if pctl.player_volume > 3:
                    pctl.player_volume -= 3
                else:
                    pctl.player_volume = 0
                pctl.set_volume()

            if not radiobox:
                if key_slash_press:
                    if key_shiftr_down or key_shift_down:
                        pctl.revert()
                    else:
                        pctl.advance(rr=True)
                if key_period_press:
                    pctl.random_mode ^= True
                if key_quote_hit:
                    if key_ctrl_down:
                        if pctl.queue_step > 1:
                            pctl.show_current(index=pctl.track_queue[pctl.queue_step - 1])
                    else:
                        pctl.show_current()
                if key_comma_press:
                    pctl.repeat_mode ^= True
                if key_col_hit:
                    random_track()

            if key_dash_press:
                pctl.new_time = pctl.playing_time - 15
                pctl.playing_time -= 15
                if pctl.new_time < 0:
                    pctl.new_time = 0
                    pctl.playing_time = 0
                pctl.playerCommand = 'seek'
                pctl.playerCommandReady = True

            if key_eq_press:
                pctl.new_time = pctl.playing_time + 15
                pctl.playing_time += 15
                pctl.playerCommand = 'seek'
                pctl.playerCommandReady = True

    # if mouse_position[1] < 1:
    #     mouse_down = False

    if mouse_down is False:
        scroll_hold = False

    # if focused is True:
    #     mouse_down = False

    if mediaKey_pressed:
        if mediaKey == 'play':
            if pctl.playing_state == 0:
                pctl.play()
            else:
                pctl.pause()
        elif mediaKey == 'stop':
            pctl.stop()
        elif mediaKey == 'forward':
            pctl.advance()
        elif mediaKey == 'back':
            pctl.back()
        mediaKey_pressed = False

    if len(load_orders) > 0:
        loading_in_progress = True
        if loaderCommand == LC_None:
            for order in load_orders:
                if order.stage == 0:
                    order.traget = order.target.replace('\\', '/')
                    order.stage = 1
                    if os.path.isdir(order.traget):
                        loaderCommand = LC_Folder
                    else:
                        loaderCommand = LC_File
                        if '.xspf' in order.traget:
                            to_got = 'xspf'
                            to_get = 0
                        else:
                            to_got = 1
                            to_get = 1
                    loaderCommandReady = True
                    break
    elif loading_in_progress is True:
        loading_in_progress = False
        #save_state()
        worker_save_state = True


    if loaderCommand == LC_Done:
        loaderCommand = LC_None
        gui.update += 1
        # gui.pl_update = 1
        # loading_in_progress = False

    if update_layout:

        update_layout_do()
        # update layout
        # C-UL
        update_layout = False

    if worker_save_state and not gui.pl_pulse:
        save_state()
        cue_list.clear()
        worker_save_state = False

    # -----------------------------------------------------
    # THEME SWITCHER--------------------------------------------------------------------
    if key_F2:
        themeChange = True
        gui.theme_temp_current = -1
        gui.temp_themes.clear()
        theme += 1

    if themeChange is True:
        gui.light_mode = False
        gui.draw_frame = False
        gui.pl_update = 1
        if theme > 25:
            theme = 0
        if theme > 0:
            theme_number = theme - 1
            try:
                theme_files = os.listdir(install_directory + '/theme')
                theme_files.sort()
                #print(theme_files)

                for i in range(len(theme_files)):
                    # print(theme_files[i])
                    if i == theme_number and 'ttheme' in theme_files[i]:
                        colours.__init__()
                        with open(install_directory + "/theme/" + theme_files[i], encoding="utf_8") as f:
                            content = f.readlines()
                            print("Applying external theme: " + theme_files[i].split(".")[0])
                            for p in content:
                                if "#" in p:
                                    continue
                                if 'draw-frame' in p:
                                    gui.draw_frame = True
                                if 'light-theme-mode' in p:
                                    gui.light_mode = True
                                    print("light mode")
                                if 'gallery highlight' in p:
                                    colours.gallery_highlight = get_colour_from_line(p)
                                if 'index playing' in p:
                                    colours.index_playing = get_colour_from_line(p)
                                if 'time playing' in p:
                                    colours.time_text = get_colour_from_line(p)
                                if 'artist playing' in p:
                                    colours.artist_playing = get_colour_from_line(p)
                                if 'album line' in p:
                                    colours.album_text = get_colour_from_line(p)
                                if 'album playing' in p:
                                    colours.album_playing = get_colour_from_line(p)
                                if 'player background' in p:
                                    colours.top_panel_background = get_colour_from_line(p)
                                if 'side panel' in p:
                                    colours.side_panel_background = get_colour_from_line(p)
                                if 'playlist panel' in p:
                                    colours.playlist_panel_background = get_colour_from_line(p)
                                if 'track line' in p:
                                    colours.title_text = get_colour_from_line(p)
                                if 'track missing' in p:
                                    colours.playlist_text_missing = get_colour_from_line(p)
                                if 'playing highlight' in p:
                                    colours.row_playing_highlight = get_colour_from_line(p)
                                if 'track time' in p:
                                    colours.bar_time = get_colour_from_line(p)
                                if 'fav line' in p:
                                    colours.star_line = get_colour_from_line(p)
                                if 'folder title' in p:
                                    colours.folder_title = get_colour_from_line(p)
                                if 'folder line' in p:
                                    colours.folder_line = get_colour_from_line(p)
                                if 'buttons off' in p:
                                    colours.media_buttons_off = get_colour_from_line(p)
                                if 'buttons over' in p:
                                    colours.media_buttons_over = get_colour_from_line(p)
                                if 'buttons active' in p:
                                    colours.media_buttons_active = get_colour_from_line(p)
                                if 'playing time' in p:
                                    colours.time_playing = get_colour_from_line(p)
                                if 'track index' in p:
                                    colours.index_text = get_colour_from_line(p)
                                if 'track playing' in p:
                                    colours.title_playing = get_colour_from_line(p)
                                if 'select highlight' in p:
                                    colours.row_select_highlight = get_colour_from_line(p)
                                if 'track artist' in p:
                                    colours.artist_text = get_colour_from_line(p)
                                if 'tab active line' in p:
                                    colours.tab_text_active = get_colour_from_line(p)
                                if 'tab line' in p:
                                    colours.tab_text = get_colour_from_line(p)
                                if 'tab background' in p:
                                    colours.tab_background = get_colour_from_line(p)
                                if 'tab over' in p:
                                    colours.tab_highlight = get_colour_from_line(p)
                                if 'tab active background' in p:
                                    colours.tab_background_active = get_colour_from_line(p)
                                if 'title info' in p:
                                    colours.side_bar_line1 = get_colour_from_line(p)
                                if 'extra info' in p:
                                    colours.side_bar_line2 = get_colour_from_line(p)
                                if 'scroll bar' in p:
                                    colours.scroll_colour = get_colour_from_line(p)
                                if 'seek bar' in p:
                                    colours.seek_bar_fill = get_colour_from_line(p)
                                if 'seek bg' in p:
                                    colours.seek_bar_background = get_colour_from_line(p)
                                if 'volume bar' in p:
                                    colours.volume_bar_fill = get_colour_from_line(p)
                                if 'volume bg' in p:
                                    colours.volume_bar_background = get_colour_from_line(p)
                                if 'mode off' in p:
                                    colours.mode_button_off = get_colour_from_line(p)
                                if 'mode over' in p:
                                    colours.mode_button_over = get_colour_from_line(p)
                                if 'mode on' in p:
                                    colours.mode_button_active = get_colour_from_line(p)
                                if 'art border' in p:
                                    colours.art_box = get_colour_from_line(p)
                                if 'sep line' in p:
                                    colours.sep_line = get_colour_from_line(p)
                                if 'bb line' in p:
                                    colours.bb_line = get_colour_from_line(p)
                                if 'tb line' in p:
                                    colours.tb_line = get_colour_from_line(p)
                                if 'music vis' in p:
                                    colours.vis_colour = get_colour_from_line(p)
                                if 'menu background' in p:
                                    colours.menu_background = get_colour_from_line(p)
                                if 'menu text' in p:
                                    colours.menu_text = get_colour_from_line(p)
                                if 'menu disable' in p:
                                    colours.menu_text_disabled = get_colour_from_line(p)
                                if 'menu highlight' in p:
                                    colours.menu_highlight_background = get_colour_from_line(p)
                                if 'lyrics showcase' in p:
                                    colours.lyrics = get_colour_from_line(p)
                                if 'bottom panel' in p:
                                    colours.bottom_panel_colour = get_colour_from_line(p)
                                    colours.menu_background = colours.bottom_panel_colour

                            colours.post_config()
                            # temp
                            colours.menu_highlight_background = [40, 40, 40, 255]

                        break
                else:
                    theme = 0
            except:
                show_message("Error loading theme file", 'warning')

        if theme == 0:
            print("Applying default theme: Mindaro")
            colours.__init__()
            colours.post_config()

        themeChange = False
        gui.win_fore = colours.playlist_panel_background

    # ---------------------------------------------------------------------------------------------------------
    # GUI DRAWING------
    # print(gui.update)
    # print(gui.lowered)

    if gui.update > 0 and gui.lowered != True and not resize_mode:
        if gui.update > 2:
            gui.update = 2

        SDL_SetRenderTarget(renderer, None)
        SDL_SetRenderDrawColor(renderer, colours.top_panel_background[0], colours.top_panel_background[1],
                               colours.top_panel_background[2], colours.top_panel_background[3])
        SDL_RenderClear(renderer)
        SDL_SetRenderTarget(renderer, gui.main_texture)


        # perf_timer.set()

        fields.clear()
        gui.flag_special_cursor = False

        if GUI_Mode == 1 or GUI_Mode == 2:

            #if gui.win_text:
            gui.win_fore = colours.playlist_panel_background

            # Side Bar Draging----------

            if mouse_down is not True:
                side_drag = False

            rect = (window_size[0] - gui.side_panel_size - 5 * gui.scale, gui.panelY, 12 * gui.scale, window_size[1] - 90 * gui.scale)
            fields.add(rect)


            if (coll_point(mouse_position,
                           (window_size[0] - gui.side_panel_size - 5 * gui.scale, gui.panelY, 12 * gui.scale,
                            window_size[1] - 90 * gui.scale)) or side_drag is True) \
                    and renamebox is False \
                    and radiobox is False \
                    and rename_playlist_box is False \
                    and gui.message_box is False \
                    and pref_box.enabled is False \
                    and track_box is False \
                    and not gui.rename_folder_box \
                    and extra_menu.active is False\
                    and (side_panel_enable or album_mode)\
                    and not x_menu.active \
                    and not view_menu.active \
                    and not track_menu.active \
                    and not tab_menu.active \
                    and not selection_menu.active\
                    and not view_box.active \
                    and not folder_menu.active:


                #update_layout = True


                if side_drag != True:
                    draw_sep_hl = True

                if input.mouse_click:
                    side_drag = True

                if gui.cursor_mode == 0:
                    gui.cursor_mode = 2
                    SDL_SetCursor(cursor_shift)

            elif not side_drag and gui.cursor_mode == 2:
                SDL_SetCursor(cursor_standard)
                gui.cursor_mode = 0

            # side drag update
            if side_drag is True:
                gui.side_panel_size = window_size[0] - mouse_position[0]
                if album_mode and gui.side_panel_size < album_mode_art_size + 50 * gui.scale:
                    gui.side_panel_size = album_mode_art_size + 50 * gui.scale
                gui.update_layout()
                #update_layout_do()

            if gui.show_playlist:
                if gui.side_panel_size < 100 * gui.scale:
                    gui.side_panel_size = 100 * gui.scale
                if gui.side_panel_size > window_size[1] - 77 * gui.scale and album_mode is not True:
                    gui.side_panel_size = window_size[1] - 77 * gui.scale

                if album_mode is True:
                    if gui.side_panel_size > window_size[0] - 300 * gui.scale:
                        gui.side_panel_size = window_size[0] - 300 * gui.scale
                    gui.playlist_width = window_size[0] - gui.side_panel_size - 30 * gui.scale

            # ALBUM GALLERY RENDERING:
            # Gallery view
            # C-AR

            if album_mode:

                if gal_right:
                    gal_right = False
                    gal_jump_select(False, 1)
                    goto_album(playlist_selected)
                    playlist_position = playlist_selected
                    gui.pl_update = 1

                if gal_down:
                    gal_down = False
                    gal_jump_select(False, row_len)
                    goto_album(playlist_selected, down=True)
                    playlist_position = playlist_selected
                    gui.pl_update = 1

                if gal_left:
                    gal_left = False
                    gal_jump_select(True, 1)
                    goto_album(playlist_selected)
                    playlist_position = playlist_selected
                    gui.pl_update = 1

                if gal_up:
                    gal_up = False
                    gal_jump_select(True, row_len)
                    goto_album(playlist_selected)
                    playlist_position = playlist_selected
                    gui.pl_update = 1


                if not gui.show_playlist:
                    rect = [0, gui.panelY, window_size[0],
                            window_size[1] - gui.panelY - gui.panelBY - 0]
                    draw.rect_r(rect, colours.side_panel_background, True)
                else:
                    rect = [gui.playlist_width + 31 * gui.scale, gui.panelY, window_size[0] - gui.playlist_width - 31 * gui.scale,
                            window_size[1] - gui.panelY - gui.panelBY - 0]
                    draw.rect_r(rect, colours.side_panel_background, True)

                area_x = window_size[0] - gui.playlist_width + 20 * gui.scale

                row_len = int((area_x - album_h_gap) / (album_mode_art_size + album_h_gap))

                # print(row_len)

                compact = 40 * gui.scale
                a_offset = 7 * gui.scale

                l_area = gui.playlist_width + 35 * gui.scale
                r_area = window_size[0] - l_area
                c_area = int((window_size[0] - l_area) / 2) + l_area

                gui.win_fore = colours.side_panel_background

                if row_len == 0:
                    row_len = 1
                dev = int((r_area - compact) / (row_len + 0))

                render_pos = 0
                album_on = 0
                if mouse_position[0] > gui.playlist_width + 35 * gui.scale and mouse_position[1] < window_size[1] - gui.panelBY:
                    if prefs.gallery_row_scroll:
                        album_pos_px -= mouse_wheel * (album_mode_art_size + album_v_gap)  # 90
                    else:
                        album_pos_px -= mouse_wheel * prefs.gallery_scroll_wheel_px

                    if album_pos_px < -55:
                        album_pos_px = -55
                        gallery_pulse_top.pulse()


                gallery_pulse_top.render(gui.playlist_width + 30 * gui.scale, gui.panelY + 1, window_size[0] - gui.playlist_width + 30 * gui.scale, 2)


                # ----
                rect = (
                window_size[0] - (33 * gui.scale if not gui.maximized else 32 * gui.scale), gui.panelY, 31 * gui.scale, window_size[1] - gui.panelBY - gui.panelY)
                # draw.rect_r(rect, [255,0,0,5], True)

                fields.add(rect)
                if coll_point(mouse_position, rect):
                    draw_text((rect[0] + 10 * gui.scale, (int((rect[1] + rect[3]) * 0.25))), "▲",
                              alpha_mod(colours.side_bar_line2, 150), 13)
                    draw_text((rect[0] + 10 * gui.scale, (int((rect[1] + rect[3]) * 0.75))), "▼",
                              alpha_mod(colours.side_bar_line2, 150), 13)

                if right_click:

                    if coll_point(mouse_position, rect):
                        per = (mouse_position[1] - gui.panelY - 25 * gui.scale) / (window_size[1] - gui.panelBY - gui.panelY)
                        if per > 100:
                            per = 100
                        if per < 0:
                            per = 0
                        album_pos_px = int((len(album_dex) / row_len) * (album_mode_art_size + album_v_gap) * per) - 50 * gui.scale

                if mouse_down:
                    # rect = (window_size[0] - 30, gui.panelY, 30, window_size[1] - gui.panelBY - gui.panelY)
                    if coll_point(mouse_position, rect):
                        # if mouse_position[1] > window_size[1] / 2:
                        #     album_pos_px += 30
                        # else:
                        #     album_pos_px -= 30
                        album_scroll_hold = True
                        tt = scroll_timer.hit()
                        if tt > 1:
                            mv = 0
                        else:
                            mv = int(tt * 1500 * gui.scale)
                            if mv < 30:
                                if mouse_position[1] > (rect[1] + rect[3]) * 0.5:
                                    album_pos_px += mv
                                else:
                                    album_pos_px -= mv
                else:
                    album_scroll_hold = False

                if last_row != row_len:
                    last_row = row_len

                    goto_album(pctl.playlist_playing)

                # Process inputs first
                if input.mouse_click or right_click:
                    while render_pos < album_pos_px + window_size[1]:

                        if b_info_bar and render_pos > album_pos_px + b_info_y:
                            break

                        if render_pos < album_pos_px - album_mode_art_size - album_v_gap:
                            # Skip row
                            render_pos += album_mode_art_size + album_v_gap
                            album_on += row_len
                        else:
                            # render row
                            y = render_pos - album_pos_px
                            row_x = 0
                            for a in range(row_len):
                                if album_on > len(album_dex) - 1:
                                    break

                                x = (l_area + dev * a) - int(album_mode_art_size / 2) + int(dev / 2) + int(
                                    compact / 2) - a_offset

                                if album_dex[album_on] > len(default_playlist):
                                    break

                                if coll_point(mouse_position, (
                                        x, y, album_mode_art_size, album_mode_art_size + 40 * gui.scale)) and gui.panelY < mouse_position[
                                    1] < window_size[1] - gui.panelBY:

                                    info = get_album_info(album_dex[album_on])

                                    if input.mouse_click:


                                        if info[0] == 1 and pctl.playing_state == 2:
                                            pctl.play()
                                        elif info[0] == 1 and pctl.playing_state > 0:
                                            playlist_position = album_dex[album_on]
                                        else:
                                            playlist_position = album_dex[album_on]
                                            pctl.jump(default_playlist[album_dex[album_on]], album_dex[album_on])

                                        pctl.show_current()

                                    else:
                                        playlist_selected = album_dex[album_on]
                                        playlist_position = playlist_selected
                                        shift_selection = [playlist_selected]
                                        if gui.show_playlist:
                                            pctl.render_playlist()
                                        # else:
                                        #     acy = y
                                        #     #acx = x + album_mode_art_size + 15 * gui.scale
                                        #     acx = x + album_mode_art_size + 15 * gui.scale
                                        #     album_card.activate(playlist_selected, acx, acy)


                                album_on += 1

                            if album_on > len(album_dex):
                                break
                            render_pos += album_mode_art_size + album_v_gap



                render_pos = 0
                album_on = 0

                # Render album grid
                while render_pos < album_pos_px + window_size[1]:

                    if b_info_bar and render_pos > album_pos_px + b_info_y:
                        break

                    if render_pos < album_pos_px - album_mode_art_size - album_v_gap:
                        # Skip row
                        render_pos += album_mode_art_size + album_v_gap
                        album_on += row_len
                    else:
                        # render row
                        y = render_pos - album_pos_px

                        row_x = 0

                        for a in range(row_len):

                            if album_on > len(album_dex) - 1:
                                break

                            x = (l_area + dev * a) - int(album_mode_art_size / 2) + int(dev / 2) + int(
                                compact / 2) - a_offset

                            if album_dex[album_on] > len(default_playlist):
                                break
                            info = get_album_info(album_dex[album_on])

                            #artisttitle = colours.side_bar_line2
                            albumtitle = colours.side_bar_line1  # grey(220)




                            if info[0] == 1 and pctl.playing_state != 0:
                                draw.rect((x - 4, y - 4), (album_mode_art_size + 8, album_mode_art_size + 8),
                                          colours.gallery_highlight, True)
                                draw.rect((x, y), (album_mode_art_size, album_mode_art_size),
                                          colours.side_panel_background, True)

                            # Draw selection
                            if gui.album_tab_mode and info[2] is True:

                                c = colours.gallery_highlight
                                c = [c[1], c[2], c[0], c[3]]
                                draw.rect((x - 4, y - 4), (album_mode_art_size + 8, album_mode_art_size + 8),
                                          c, True) #[150, 80, 222, 255]
                                draw.rect((x, y), (album_mode_art_size, album_mode_art_size),
                                          colours.side_panel_background, True)

                            # Draw selection animation
                            if gui.gallery_animate_highlight_on == album_dex[album_on] and gallery_select_animate_timer.get() < 1.5:

                                t = gallery_select_animate_timer.get()
                                c = colours.gallery_highlight
                                if t < 0.2:
                                    a = int(255 * (t / 0.2))
                                elif t < 0.5:
                                    a = 255
                                else:
                                    a = int(255 - 255 * (t - 0.5))


                                c = [c[1], c[2], c[0], a]
                                draw.rect((x - 5, y - 5), (album_mode_art_size + 10, album_mode_art_size + 10),
                                          c, True) #[150, 80, 222, 255]
                                draw.rect((x, y), (album_mode_art_size, album_mode_art_size),
                                          colours.side_panel_background, True)
                                gui.update += 1


                            # Draw back colour
                            draw.rect((x, y), (album_mode_art_size, album_mode_art_size), [40, 40, 40, 50], True)

                            # Draw faint outline
                            draw.rect((x - 1 * gui.scale, y - 1 * gui.scale), (album_mode_art_size + 2 * gui.scale, album_mode_art_size + 2 * gui.scale),
                                      [255, 255, 255, 11])

                            # Draw album art
                            if gall_ren.render(default_playlist[album_dex[album_on]], (x, y)) is False and gui.gallery_show_text is False:

                                draw_text((x + int(album_mode_art_size / 2), y + album_mode_art_size - 22 * gui.scale, 2),
                                           pctl.master_library[default_playlist[album_dex[album_on]]].parent_folder_name,
                                           colours.gallery_artist_line,
                                           13,
                                           album_mode_art_size - 10 * gui.scale,
                                           )

                            if gui.album_tab_mode:
                                if info[2] is False and info[0] != 1:
                                    draw.rect((x, y), (album_mode_art_size, album_mode_art_size), [0, 0, 0, 110], True)
                                    albumtitle = colours.grey(150)

                            else:
                                if info[0] != 1 and pctl.playing_state != 0 and prefs.dim_art:
                                    draw.rect((x, y), (album_mode_art_size, album_mode_art_size), [0, 0, 0, 110], True)
                                    albumtitle = colours.grey(150)


                            c_index = default_playlist[album_dex[album_on]]

                            if c_index in album_artist_dict:
                                pass
                            else:
                                i = album_dex[album_on]
                                if pctl.master_library[default_playlist[i]].album_artist != "":
                                    album_artist_dict[c_index] = pctl.master_library[default_playlist[i]].album_artist
                                else:
                                    while i < len(default_playlist) - 1:
                                        if pctl.master_library[default_playlist[i]].parent_folder_name != \
                                                pctl.master_library[
                                                    default_playlist[album_dex[album_on]]].parent_folder_name:
                                            album_artist_dict[c_index] = pctl.master_library[
                                                default_playlist[album_dex[album_on]]].artist
                                            break
                                        if pctl.master_library[default_playlist[i]].artist != pctl.master_library[
                                            default_playlist[album_dex[album_on]]].artist:
                                            album_artist_dict[c_index] = "Various Artists"

                                            break
                                        i += 1
                                    else:
                                        album_artist_dict[c_index] = pctl.master_library[
                                            default_playlist[album_dex[album_on]]].artist

                            if gui.gallery_show_text:
                                line = album_artist_dict[c_index]
                                line2 = pctl.master_library[default_playlist[album_dex[album_on]]].album

                                if line2 == "":

                                    draw_text2((x, y + album_mode_art_size + 9 * gui.scale),
                                               line,
                                               colours.gallery_artist_line,
                                               11,
                                               album_mode_art_size - 5 * gui.scale,
                                               3,
                                               default_playlist[album_dex[album_on]]
                                               )
                                else:

                                    draw_text2((x, y + album_mode_art_size + 8 * gui.scale),
                                               line2,
                                               albumtitle,
                                               212,
                                               album_mode_art_size,
                                               3,
                                               default_playlist[album_dex[album_on]]
                                               )

                                    draw_text2((x, y + album_mode_art_size + (10 + 14)  * gui.scale),
                                               line,
                                               colours.gallery_artist_line,
                                               11,
                                               album_mode_art_size - 5 * gui.scale,
                                               3,
                                               default_playlist[album_dex[album_on]]
                                               )

                            album_on += 1

                        if album_on > len(album_dex):
                            break
                        render_pos += album_mode_art_size + album_v_gap

                draw.rect((0, 0), (window_size[0], gui.panelY), colours.top_panel_background, True)

                if gui.show_playlist is False:
                    album_card.render()

                # if gui.album_tab_mode:
                #     draw.rect_r([l_area - 4, gui.panelY, r_area + 4, 2], [80, 70, 220, 255], True)


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
                            if playlist[6] == order.playlist:
                                target_pl = p
                                break
                        else:
                            del load_orders[i]
                            print("Error: Target playlist lost")
                            break

                        # print(order.tracks)
                        if order.playlist_position is not None:
                            print(order.playlist_position)
                            #pctl.multi_playlist[target_pl][2] = order.tracks
                            pctl.multi_playlist[target_pl][2][order.playlist_position:order.playlist_position] = order.tracks
                        else:
                            pctl.multi_playlist[target_pl][2] += order.tracks

                        gui.update += 2
                        gui.pl_update += 2
                        reload()
                        del load_orders[i]
                        break

            if gui.show_playlist:

                # playlist hit test
                if coll_point(mouse_position, (
                gui.playlist_left, gui.playlist_top, gui.playlist_width, window_size[1] - gui.panelY - gui.panelBY)) and not drag_mode and (
                                            input.mouse_click or mouse_wheel != 0 or right_click or middle_click or mouse_up or mouse_down):
                    gui.pl_update = 1

                if gui.combo_mode and mouse_wheel != 0:
                    gui.pl_update = 1

                # MAIN PLAYLIST
                # C-PR

                if gui.set_bar:
                    rect = [0, gui.panelY, gui.playlist_width + 31 * gui.scale, gui.set_height]
                    start = 16 * gui.scale
                    run = 0
                    in_grip = False

                    if not mouse_down and gui.set_hold != -1:
                        gui.set_hold = -1

                    for h, item in enumerate(gui.pl_st):
                        box = (start + run, rect[1], item[1], rect[3])
                        grip = (start + run, rect[1], 3 * gui.scale, rect[3])
                        m_grip = (grip[0] - 4 * gui.scale, grip[1], grip[2] + 8 * gui.scale, grip[3])
                        l_grip = (grip[0] + 9 * gui.scale, grip[1], box[2] - 9 * gui.scale, grip[3])
                        fields.add(m_grip)


                        if coll_point(mouse_position, l_grip):
                            if mouse_up and gui.set_label_hold != -1:
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
                                    print("MOVE")
                                    break

                                gui.set_label_hold = -1

                            if input.mouse_click:
                                gui.set_label_hold = h
                            if right_click:
                                set_menu.activate(h)

                        if h != 0:
                            if coll_point(mouse_position, m_grip):
                                in_grip = True
                                if input.mouse_click:

                                    gui.set_hold = h
                                    gui.set_point = mouse_position[0]
                                    gui.set_old = gui.pl_st[h - 1][1]
                            if mouse_down and gui.set_hold == h:
                                gui.pl_st[h - 1][1] = gui.set_old + (mouse_position[0] - gui.set_point)
                                if gui.pl_st[h - 1][1] < 25:
                                    gui.pl_st[h - 1][1] = 25

                                gui.update = 1
                                gui.pl_update = 1

                                total = 0
                                for i in range(len(gui.pl_st) - 1):
                                    total += gui.pl_st[i][1]
                                gui.pl_st[len(gui.pl_st) - 1][1] = gui.playlist_width + 31 - 16 - total

                        run += item[1]

                    if not mouse_down:
                        gui.set_label_hold = -1
                    # print(in_grip)
                    if in_grip and not x_menu.active and not view_menu.active and not tab_menu.active:
                        if gui.cursor_mode == 0 or True:
                            gui.cursor_mode = 2
                            SDL_SetCursor(cursor_shift)
                    else:
                        if gui.cursor_mode == 2 and mouse_position[1] < 50:
                            SDL_SetCursor(cursor_standard)
                            gui.cursor_mode = 0

                if gui.pl_update > 0:

                    gui.pl_update -= 1
                    if gui.combo_mode:
                        if gui.showcase_mode:
                            showcase.render()
                        else:
                            combo_pl_render.full_render()
                    else:
                        playlist_render.full_render()

                else:
                    if gui.combo_mode:
                        if gui.showcase_mode:
                            showcase.render()
                        else:
                            combo_pl_render.cache_render()
                    else:
                        playlist_render.cache_render()

                if gui.set_bar and not gui.combo_mode:
                    rect = [0, gui.panelY, gui.playlist_width + 31 * gui.scale, gui.set_height]
                    draw.rect_r(rect, [30, 30, 30, 255], True)

                    start = 16 * gui.scale
                    run = 0
                    for item in gui.pl_st:
                        box = (start + run, rect[1], item[1], rect[3])
                        grip = (start + run, rect[1], 3 * gui.scale, rect[3])
                        draw.rect_r(grip, [255, 255, 255, 14], True)

                        line = trunc_line(item[0], 12, box[2] - 13 * gui.scale, False)
                        gui.win_fore = [30, 30, 30, 255]
                        draw_text((box[0] + 10 * gui.scale, gui.panelY + 4 * gui.scale), line, [240, 240, 240, 255], 12)
                        run += box[2]

                # ------------------------------------------------
                # Scroll Bar

                # if not scroll_enable:
                fields.add(gui.scroll_hide_box)
                if (coll_point(mouse_position, gui.scroll_hide_box) or scroll_hold or quick_search_mode) and not playlist_panel:  # or scroll_opacity > 0:
                    scroll_opacity = 255

                    if not gui.combo_mode:
                        sy = 31 * gui.scale
                        ey = window_size[1] - (30 + 22) * gui.scale

                        if len(default_playlist) < 50:
                            sbl = 85 * gui.scale
                            if len(default_playlist) == 0:
                                sbp = gui.panelY
                        else:
                            sbl = 105 * gui.scale

                        fields.add((2 * gui.scale, sbp, 20 * gui.scale, sbl))
                        if coll_point(mouse_position, (0, gui.panelY, 28 * gui.scale, ey - gui.panelY)) and not playlist_panel and (
                            mouse_down or right_click) \
                                and coll_point(click_location, (0, gui.panelY, 28 * gui.scale, ey - gui.panelY)):

                            gui.pl_update = 1
                            if right_click:

                                sbp = mouse_position[1] - int(sbl / 2)
                                if sbp + sbl > ey:
                                    sbp = ey - sbl
                                elif sbp < gui.panelY:
                                    sbp = gui.panelY
                                per = (sbp - gui.panelY) / (ey - gui.panelY - sbl)
                                playlist_position = int(len(default_playlist) * per)

                                if playlist_position < 0:
                                    playlist_position = 0

                                # if playlist_position == len(default_playlist):
                                #     print("END")

                            elif mouse_position[1] < sbp:
                                playlist_position -= 2
                            elif mouse_position[1] > sbp + sbl:
                                playlist_position += 2
                            elif input.mouse_click:

                                p_y = pointer(c_int(0))
                                p_x = pointer(c_int(0))
                                SDL_GetGlobalMouseState(p_x, p_y)

                                scroll_hold = True
                                scroll_point = p_y.contents.value  # mouse_position[1]
                                scroll_bpoint = sbp

                        if not mouse_down:
                            scroll_hold = False


                        if scroll_hold and not input.mouse_click:
                            gui.pl_update = 1
                            p_y = pointer(c_int(0))
                            p_x = pointer(c_int(0))
                            SDL_GetGlobalMouseState(p_x, p_y)

                            sbp = p_y.contents.value - (scroll_point - scroll_bpoint)
                            if sbp + sbl > ey:
                                sbp = ey - sbl
                            elif sbp < gui.panelY:
                                sbp = gui.panelY
                            per = (sbp - gui.panelY) / (ey - gui.panelY - sbl)
                            playlist_position = int(len(default_playlist) * per)


                        else:
                            if len(default_playlist) > 0:
                                per = playlist_position / len(default_playlist)
                                sbp = int((ey - gui.panelY - sbl) * per) + gui.panelY + 1

                        # if (coll_point(mouse_position, (2, sbp, 20, sbl)) and mouse_position[
                        #     0] != 0) or scroll_hold:
                        #     scroll_opacity = 255
                        draw.rect((0, gui.panelY), (18 * gui.scale, window_size[1] - gui.panelY - gui.panelBY), [18, 18, 18, 255], True)
                        draw.rect((1, sbp), (15 * gui.scale, sbl), alpha_mod(colours.scroll_colour, scroll_opacity), True)

                        if (coll_point(mouse_position, (2 * gui.scale, sbp, 20 * gui.scale, sbl)) and mouse_position[0] != 0) or scroll_hold:
                            draw.rect((1 * gui.scale, sbp), (15 * gui.scale, sbl), [255, 255, 255, 11], True)
                    else:
                        # Combo mode scroll:
                        sy = 31 * gui.scale
                        ey = window_size[1] - (30 + 22) * gui.scale

                        sbl = 105 * gui.scale



                        fields.add((window_size[0] - (2 - 20) * gui.scale, sbp, 20 * gui.scale, sbl))
                        if coll_point(mouse_position, (window_size[0] - 28 * gui.scale, gui.panelY, 28 * gui.scale, ey - gui.panelY)) and not playlist_panel and (
                                    mouse_down or right_click) \
                                and coll_point(click_location, (window_size[0] - 28 * gui.scale, gui.panelY, 28 * gui.scale, ey - gui.panelY)):

                            gui.pl_update = 1
                            if right_click:

                                sbp = mouse_position[1] - int(sbl / 2)
                                if sbp + sbl > ey:
                                    sbp = ey - sbl
                                elif sbp < gui.panelY:
                                    sbp = gui.panelY
                                per = (sbp - gui.panelY) / (ey - gui.panelY - sbl)
                                combo_pl_render.pl_pos_px = int(combo_pl_render.max_y * per)
                                #
                                # # if playlist_position < 0:
                                # #     playlist_position = 0
                            elif mouse_position[1] < sbp:
                                combo_pl_render.pl_pos_px -= 30 * gui.scale
                            elif mouse_position[1] > sbp + sbl:
                                combo_pl_render.pl_pos_px += 30 * gui.scale
                            elif input.mouse_click:

                                p_y = pointer(c_int(0))
                                p_x = pointer(c_int(0))
                                SDL_GetGlobalMouseState(p_x, p_y)

                                scroll_hold = True
                                scroll_point = p_y.contents.value  # mouse_position[1]
                                scroll_bpoint = sbp

                        if not mouse_down:
                            scroll_hold = False

                        if scroll_hold and not input.mouse_click:
                            gui.pl_update = 1
                            p_y = pointer(c_int(0))
                            p_x = pointer(c_int(0))
                            SDL_GetGlobalMouseState(p_x, p_y)
                            sbp = p_y.contents.value - (scroll_point - scroll_bpoint)
                            if sbp + sbl > ey:
                                sbp = ey - sbl
                            elif sbp < gui.panelY:
                                sbp = gui.panelY
                            per = (sbp - gui.panelY) / (ey - gui.panelY - sbl)
                            # playlist_position = int(len(default_playlist) * per)
                            combo_pl_render.pl_pos_px = int(combo_pl_render.max_y * per)
                            combo_pl_render.last_dex = 0



                        else:

                            if combo_pl_render.max_y > 0:
                                per = combo_pl_render.pl_pos_px / combo_pl_render.max_y
                                sbp = int((ey - gui.panelY - sbl) * per) + gui.panelY + 1

                        draw.rect((window_size[0] - 17 * gui.scale, gui.panelY), (17 * gui.scale, window_size[1] - gui.panelY - gui.panelBY), [18, 18, 18, 255], True)
                        draw.rect((window_size[0] - 14 * gui.scale, sbp), (15 * gui.scale, sbl), colours.scroll_colour, True)


                        if (coll_point(mouse_position, (window_size[0] - (2 - 20) * gui.scale, sbp, 20 * gui.scale, sbl)) and mouse_position[0] != 0) or scroll_hold:
                            draw.rect((window_size[0] - (1 - 15) * gui.scale, sbp), (15 * gui.scale, sbl), [255, 255, 255, 11], True)

                # Switch Vis:
                if right_click and coll_point(mouse_position, (window_size[0] - 150 * gui.scale - gui.offset_extra, 0, 140 * gui.scale , gui.panelY)):
                    vis_menu.activate(None, (window_size[0] - 150 * gui.scale, 30 * gui.scale))

                if input.mouse_click and coll_point(mouse_position, (window_size[0] - 130 * gui.scale  - gui.offset_extra, 0, 120 * gui.scale , gui.panelY)):
                    if gui.vis == 0:
                        gui.vis = 1
                        gui.turbo = True
                    elif gui.vis == 1:
                        gui.vis = 2
                    elif gui.vis == 2:
                        gui.vis = 3
                    elif gui.vis == 3:
                        gui.vis = 0
                        gui.turbo = False


                edge_playlist.render(0, gui.panelY + 1, gui.playlist_width + 30 * gui.scale, 2 * gui.scale)
                bottom_playlist.render(0, window_size[1] - gui.panelBY - 2 * gui.scale, gui.playlist_width + 30 * gui.scale, 2 * gui.scale)
                # --------------------------------------------
                # ALBUM ART

                if side_panel_enable:
                    if album_mode:
                        pass
                    else:

                        rect = [gui.playlist_width + 31 * gui.scale, gui.panelY, window_size[0] - gui.playlist_width - 30 * gui.scale,
                                window_size[1] - gui.panelY - gui.panelBY]
                        draw.rect_r(rect, colours.side_panel_background, True)

                        showc = False

                        boxx = window_size[0] - gui.playlist_width - 50 * gui.scale
                        boxy = window_size[1] - 160 * gui.scale
                        box = boxx
                        x = gui.playlist_width + 40 * gui.scale
                        gui.main_art_box = (x, gui.artboxY, box, box)

                        # Input of section below album art
                        if (coll_point(mouse_position, (
                                x, gui.panelY + boxx + 5 * gui.scale, boxx, window_size[1] - boxx - 90 * gui.scale))):

                            # Click area to jump to current track
                            if input.mouse_click:
                                pctl.show_current()
                                gui.update += 1

                            # Scroll area to scroll lyrics
                            if mouse_wheel != 0 and prefs.show_lyrics_side and pctl.track_queue and pctl.master_library[pctl.track_queue[pctl.queue_step]].lyrics != "":
                                lyrics_ren_mini.lyrics_position += mouse_wheel * 21 * gui.scale
                                if lyrics_ren_mini.lyrics_position > 0:
                                    lyrics_ren_mini.lyrics_position = 0
                                    lyric_side_top_pulse.pulse()


                                gui.update += 1

                            # Right click to show lyric menu
                            if right_click and prefs.show_lyrics_side and pctl.track_queue and 3 > pctl.playing_state > 0:
                                gui.force_showcase_index = -1
                                showcase_menu.activate(pctl.master_library[pctl.track_queue[pctl.queue_step]])

                        # Render lyrics if available
                        if prefs.show_lyrics_side and pctl.track_queue \
                                and pctl.master_library[pctl.track_queue[pctl.queue_step]].lyrics != "" \
                                and 3 > pctl.playing_state > 0 \
                                and 38 * gui.scale + box + 133 * gui.scale < window_size[1] + 52 * gui.scale:

                            lyrics_ren_mini.render(pctl.track_queue[pctl.queue_step], x,
                                                   gui.main_art_box[1] + gui.main_art_box[
                                                       3] + 10 + lyrics_ren_mini.lyrics_position,
                                                   gui.side_panel_size - 10,
                                                   2000, 0)
                            draw.rect_r((gui.playlist_width + 31 * gui.scale, gui.panelY, window_size[0] - gui.playlist_width - 30 * gui.scale,
                                         gui.main_art_box[3] + 17), colours.side_panel_background, True)

                        lyric_side_top_pulse.render(x, gui.main_art_box[1] + gui.main_art_box[3] + 5, window_size[0] - gui.playlist_width - 30 * gui.scale, 2)

                        # Input for album art
                        if len(pctl.track_queue) > 0:

                            # Cycle images
                            if coll_point(mouse_position, gui.main_art_box) and input.mouse_click is True:
                                album_art_gen.cycle_offset(pctl.track_queue[pctl.queue_step])

                            # Open image externally
                            # if coll_point(mouse_position, gui.main_art_box) and right_click is True and pctl.playing_state > 0 and not key_shift_down:
                            #     album_art_gen.open_external(pctl.track_queue[pctl.queue_step])

                        # Draw image downloading indicator
                        if gui.image_downloading:
                            draw_text((x + int(box/2), 38 * gui.scale + int(box/2), 2), "Fetching image...", colours.side_bar_line1, 14)
                            gui.update = 2

                        # Draw the album art. If side bar is being dragged set quick draw flag
                        showc = None
                        if 3 > pctl.playing_state > 0:

                            if side_drag:

                                album_art_gen.display(pctl.track_queue[pctl.queue_step], (x, 38 * gui.scale),
                                                      (box, box), True)
                            else:
                                album_art_gen.display(pctl.track_queue[pctl.queue_step], (x, 38 * gui.scale), (box, box))

                            showc = album_art_gen.get_info(pctl.track_queue[pctl.queue_step])

                        draw.rect((x, 38 * gui.scale), (box + 1 * gui.scale, box + 1 * gui.scale), colours.art_box)



                        rect = gui.main_art_box
                        fields.add(rect)

                        if right_click and coll_point(mouse_position, rect):
                            picture_menu.activate()

                        # Draw picture metadata
                        if showc is not None and coll_point(mouse_position, rect) \
                                and renamebox is False \
                                and radiobox is False \
                                and pref_box.enabled is False \
                                and rename_playlist_box is False \
                                and gui.message_box is False \
                                and track_box is False:

                            # if right_click and showc[0] is True:
                            #     #if pctl.playing_object().file_ext == "MP3":
                            #     #    picture_menu2.activate(pctl.track_queue[pctl.queue_step])
                            #     #else:
                            #     #print(showc)
                            #     picture_menu.activate()

                            if not key_shift_down:

                                line = ""
                                if showc[0] is True:
                                    line += 'E '
                                else:
                                    line += 'F '

                                line += str(showc[2] + 1) + "/" + str(showc[1])
                                y = box + 11 * gui.scale

                                xoff = 0
                                xoff = draw.text_calc(line, 12) + 12 * gui.scale

                                draw.rect((x + box - xoff, y), (xoff, 18 * gui.scale),
                                          [8, 8, 8, 255], True)

                                draw_text((x + box - 6 * gui.scale, y, 1), line, [200, 200, 200, 255], 12, bg=[30, 30, 30, 255])

                            else:   # Extended metadata

                                # if right_click:
                                #     if pctl.playing_object().file_ext == "MP3":
                                #         picture_menu2.activate(pctl.track_queue[pctl.queue_step])
                                line = ""
                                if showc[0] is True:
                                    line += 'Embedded'
                                else:
                                    line += 'File'

                                #line += str(showc[2] + 1) + "/" + str(showc[1])
                                y = 36 * gui.scale + box - 61 * gui.scale

                                xoff = 0
                                xoff = draw.text_calc(line, 12) + 12 * gui.scale

                                draw.rect((x + box - xoff, y), (xoff, 18 * gui.scale),
                                          [8, 8, 8, 255], True)

                                draw_text((x + box - 6 * gui.scale, y, 1), line, [200, 200, 200, 255], 12, bg=[30, 30, 30, 255])

                                y += 18 * gui.scale

                                line = ""
                                line += showc[4]
                                line += " " +  str(showc[3][1]) + 'vr'
                                xoff = 0
                                xoff = draw.text_calc(line, 12) + 12 * gui.scale

                                draw.rect((x + box - xoff, y), (xoff, 18 * gui.scale),
                                          [8, 8, 8, 255], True)
                                draw_text((x + box - 6 * gui.scale, y, 1), line, [200, 200, 200, 255], 12,
                                          bg=[30, 30, 30, 255])

                                y += 18 * gui.scale

                                line = ""
                                line += str(showc[2] + 1) + "/" + str(showc[1])
                                xoff = 0
                                xoff = draw.text_calc(line, 12) + 12 * gui.scale

                                draw.rect((x + box - xoff, y), (xoff, 18 * gui.scale),
                                          [8, 8, 8, 255], True)
                                draw_text((x + box - 6, y, 1), line, [200, 200, 200, 255], 12,
                                          bg=[30, 30, 30, 255])

                        # Draw track metadata
                        if pctl.playing_state > 0:
                            if len(pctl.track_queue) > 0:
                                if prefs.show_lyrics_side and pctl.master_library[pctl.track_queue[pctl.queue_step]].lyrics != "" \
                                        and pctl.playing_state != 3:
                                    pass

                                else:

                                    gui.win_fore = colours.side_panel_background

                                    block3 = False
                                    block4 = False
                                    block5 = False
                                    block6 = False

                                    t_title = ""
                                    album = ""
                                    artist = ""
                                    ext = ""
                                    date = ""
                                    #sample = ""

                                    if pctl.playing_state < 3:

                                        t_title = pctl.master_library[pctl.track_queue[pctl.queue_step]].title
                                        album = pctl.master_library[pctl.track_queue[pctl.queue_step]].album
                                        artist = pctl.master_library[pctl.track_queue[pctl.queue_step]].artist
                                        ext = pctl.master_library[pctl.track_queue[pctl.queue_step]].file_ext
                                        date = pctl.master_library[pctl.track_queue[pctl.queue_step]].date
                                        genre = pctl.master_library[pctl.track_queue[pctl.queue_step]].genre

                                    else:

                                        t_title = pctl.tag_meta

                                    if side_panel_text_align == 1:
                                        pass

                                    else:
                                        # -------------------------------

                                        if 38 * gui.scale + box + 130 * gui.scale > window_size[1] + 52 * gui.scale:
                                            block6 = True
                                        if block6 != True:
                                            if 38 * gui.scale + box + 134 * gui.scale > window_size[1] + 37 * gui.scale:
                                                block5 = True

                                            if 38 * gui.scale + box + 126 * gui.scale > window_size[1] + 10 * gui.scale:
                                                block4 = True
                                            if 38 * gui.scale + box + 126 * gui.scale > window_size[1] - 39 * gui.scale:
                                                block3 = True

                                            if 38 * gui.scale + box + 126 * gui.scale + 2 * gui.scale > window_size[1] \
                                                    - 70 * gui.scale:

                                                block1 = 38 * gui.scale + box + 20 * gui.scale
                                                block2 = window_size[1] - (70 - 36 - 2) * gui.scale

                                            else:
                                                block1 = 38 * gui.scale + box + 20 * gui.scale
                                                block2 = 38 * gui.scale + box + 90 * gui.scale

                                            if block4 is False:

                                                if block3 is True:
                                                    block1 -= 14

                                                if t_title != "":
                                                    playing_info = t_title
                                                    playing_info = trunc_line(playing_info, fonts.side_panel_line1,
                                                                              window_size[0] - gui.playlist_width - 53 * gui.scale)
                                                    draw_text((x - 1 * gui.scale, block1 + 2 * gui.scale), playing_info, colours.side_bar_line1,
                                                              fonts.side_panel_line1, max=gui.side_panel_size - 32 * gui.scale)

                                                if artist != "":
                                                    playing_info = artist
                                                    draw_text((x - 1 * gui.scale, block1 + (17 + 6) * gui.scale),
                                                              playing_info,
                                                              colours.side_bar_line2,
                                                              fonts.side_panel_line2,
                                                              max=gui.side_panel_size - 32 * gui.scale)
                                            else:
                                                block1 -= 14 * gui.scale

                                                line = ""
                                                if artist != "":
                                                    line += artist
                                                if t_title != "":
                                                    if line != "":
                                                        line += " - "
                                                    line += t_title
                                                line = trunc_line(line, 15, window_size[0] - gui.playlist_width - 53 * gui.scale)
                                                draw_text((x - 1 * gui.scale, block1), line, colours.side_bar_line1, 15, max=gui.side_panel_size - 32 * gui.scale)

                                            if block3 == False:

                                                if album != "":
                                                    playing_info = album
                                                    draw_text((x - 1 * gui.scale, block2), playing_info, colours.side_bar_line2,
                                                              14, max=gui.side_panel_size - 32 * gui.scale)

                                                if date != "":
                                                    playing_info = date
                                                    if genre != "":
                                                        playing_info += " | " + genre
                                                    playing_info = trunc_line(playing_info, 13,
                                                                              window_size[0] - gui.playlist_width - 53 * gui.scale)
                                                    draw_text((x - 1 * gui.scale, block2 + 18 * gui.scale), playing_info, colours.side_bar_line2,
                                                              13)

                                                if ext != "":
                                                    playing_info = ext  # + " | " + sample
                                                    # playing_info = trunc_line(playing_info, 12,
                                                    #                           window_size[0] - gui.playlist_width - 53)
                                                    draw_text((x - 1 * gui.scale, block2 + 36 * gui.scale), playing_info, colours.side_bar_line2,
                                                              12, max=gui.side_panel_size - 32 * gui.scale)
                                            else:
                                                if block5 != True:
                                                    line = ""
                                                    if album != "":
                                                        line += album
                                                    if line != "":
                                                        line += " | "
                                                    if date != "":
                                                        line += date + " | "
                                                    line += ext

                                                    draw_text((x - 1 * gui.scale, block2 + 32 * gui.scale), line,
                                                              colours.side_bar_line2, 14,
                                                              max=gui.side_panel_size - 32 * gui.scale)

                # Seperation Line Drawing
                if side_panel_enable:

                    # Draw Highlight when mouse over
                    if draw_sep_hl:
                        draw.line(window_size[0] - gui.side_panel_size + 1 * gui.scale, gui.panelY + 1 * gui.scale,
                                  window_size[0] - gui.side_panel_size + 1 * gui.scale,
                                  window_size[1] - 50 * gui.scale, [100, 100, 100, 70])
                        draw_sep_hl = False

                # Normal Drawing
                if side_panel_enable and gui.draw_frame:
                    draw.line(gui.playlist_width + 30 * gui.scale, gui.panelY + 1 * gui.scale, gui.playlist_width + 30 * gui.scale, window_size[1] - 30 * gui.scale,
                              colours.sep_line)


            # Title position logic
            if album_mode:
                gui.show_bottom_title = True
                gui.show_top_title = False
            elif gui.combo_mode:
                if window_size[0] > 860 * gui.scale:
                    gui.show_bottom_title = prefs.prefer_bottom_title
                    gui.show_top_title = not gui.show_bottom_title
                else:
                    gui.show_bottom_title = False
                    gui.show_top_title = True
            else:
                if not side_panel_enable:
                    if window_size[0] > 840 * gui.scale:
                        gui.show_bottom_title = prefs.prefer_bottom_title
                        gui.show_top_title = not gui.show_bottom_title
                    else:
                        gui.show_bottom_title = False
                        gui.show_top_title = True
                else:
                    if not block6:
                        gui.show_bottom_title = False
                        gui.show_top_title = False
                    elif window_size[0] > 840 * gui.scale:
                        gui.show_bottom_title = prefs.prefer_bottom_title
                        gui.show_top_title = not gui.show_bottom_title
                    else:
                        gui.show_bottom_title = False
                        gui.show_top_title = True

            # BOTTOM BAR!
            # C-BB

            gui.win_fore = colours.bottom_panel_colour

            bottom_bar1.render()

            # NEW TOP BAR
            # C-TBR

            if gui.draw_frame:
                draw.line(0, gui.panelY, window_size[0], gui.panelY, colours.tb_line)

            if GUI_Mode == 1:
                top_panel.render()

            # Overlay GUI ----------------------

            if playlist_panel:

                pl_items_len = len(pctl.multi_playlist)
                pl_max_view_len = int((window_size[1] - gui.panelY) / 16)
                if pl_max_view_len < 1:
                    pl_max_view_len = 1
                if pl_max_view_len > pl_items_len:
                    pl_max_view_len = pl_items_len

                if coll_point(mouse_position, pl_rect):
                    pl_view_offset -= mouse_wheel * 2
                if pl_view_offset < 0:
                    pl_view_offset = 0
                if pl_view_offset > pl_items_len - pl_max_view_len:
                    pl_view_offset = pl_items_len - pl_max_view_len

                x = 5 * gui.scale
                y = gui.panelY + 5 * gui.scale
                w = 400 * gui.scale
                rh = 25 * gui.scale
                h = pl_max_view_len * rh + 5 * gui.scale

                pl_rect = (x, y, w, h)
                draw.rect((x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale), colours.grey(50), True)
                draw.rect_r(pl_rect, colours.bottom_panel_colour, True)
                gui.win_fore = colours.bottom_panel_colour

                if genre_box_click and not coll_point(mouse_position, pl_rect):
                    playlist_panel = False


                p = 0
                for i, item in enumerate(pctl.multi_playlist):

                    if i < pl_view_offset:
                        continue
                    if p >= pl_max_view_len:
                        break

                    ty = (p * rh) + y

                    x_rect = (x, ty, rh - 1, rh - 1)
                    fields.add(x_rect)

                    if coll_point(mouse_position, x_rect) and not tab_menu.active:
                        draw_text2((x + int(rh / 2), ty + int(rh / 2) - 10 * gui.scale, 2), "✖", [225, 50, 50, 255], 15, 300 * gui.scale)
                        if genre_box_click:
                            delete_playlist(i)
                    else:
                        draw_text2((x + int(rh / 2), ty + int(rh / 2) - 10 * gui.scale, 2), "✖", [50, 50, 50, 255], 15, 300 * gui.scale)

                    y_rect = (x + rh, ty, 27 * gui.scale, rh - 1 * gui.scale)
                    fields.add(y_rect)

                    playing_in = False
                    if i == pctl.active_playlist_playing and pctl.playing_state > 0:
                        if len(pctl.track_queue) > 0 and pctl.track_queue[pctl.queue_step] in item[2]:
                            draw_text2((x + rh + 15 * gui.scale, ty + int(rh / 2) - 10 * gui.scale, 2), "▶ ", [200, 200, 100, 255], 15, 300 * gui.scale)
                            playing_in = True
                        else:
                            draw_text2((x + rh + 15 * gui.scale, ty + int(rh / 2) - 10 * gui.scale, 2), "▶ ", [50, 50, 50, 255], 15, 300 * gui.scale)
                    elif pctl.playing_state > 0 and len(pctl.track_queue) > 0 and pctl.track_queue[pctl.queue_step] in item[2]:
                        draw_text2((x + rh + 15, ty + int(rh / 2) - 10, 2), "▶ ", [50, 50, 50, 255], 15, 300)
                        playing_in = True

                    if not playing_in and coll_point(mouse_position, y_rect) and pctl.playing_state > 0:
                        draw_text2((x + rh + 15 * gui.scale, ty + int(rh / 2) - 10 * gui.scale, 2), "+ ", [80, 170, 80, 255], 15, 300 * gui.scale)
                        if genre_box_click:
                            append_current_playing(i)
                    elif coll_point(mouse_position, y_rect) and playing_in:
                        if genre_box_click:
                            pctl.active_playlist_playing = i
                            pctl.playlist_playing = item[2].index(pctl.track_queue[pctl.queue_step])


                    t_rect = (x + rh + 30 * gui.scale, ty, w - rh - 30 * gui.scale, rh - 1 * gui.scale)
                    fields.add(t_rect)

                    if coll_point(mouse_position, t_rect) and not tab_menu.active:
                        if not tab_menu.active:
                            draw.rect_r(t_rect, [30, 30, 30, 255], True)
                        gui.win_fore = [30, 30, 30, 255]
                        if genre_box_click:
                            if i == gui.playlist_box_d_click and quick_d_timer.get() < 0.6 and len(item[2]) > 0:
                                gui.playlist_box_d_click = -1
                                pctl.jump(item[2][0], 0)

                            switch_playlist(i)
                            gui.playlist_box_d_click = copy.deepcopy(i)
                            quick_d_timer.set()
                        if right_click and coll_point(mouse_position, t_rect):
                            tab_menu.activate(copy.deepcopy(i), mouse_position)

                    if tab_menu.active and tab_menu.reference == i:
                        draw.rect_r(t_rect, [30, 30, 30, 255], True)
                        gui.win_fore = [30, 30, 30, 255]

                    line = item[0]
                    line = trunc_line(line, 14, 300)
                    if i == pctl.playlist_active:
                        draw_text((x + rh + 35 * gui.scale, ty + int(rh / 2) - 10 * gui.scale), line, [170, 170, 170, 255], 14)
                    else:
                        draw_text((x + rh + 35 * gui.scale, ty + int(rh / 2) - 10 * gui.scale), line, [100, 100, 100, 255], 14)


                    if len(item[2]) == 0:
                        line = "Empty"
                    elif len(item[2]) == 1:
                        line = '1 Track'
                    else:
                        line = str(len(item[2])) + " Tracks"

                    draw_text((w - 4 * gui.scale, ty + int(rh / 2) - 10 * gui.scale, 1), line, [80, 80, 80, 80], 12)

                    gui.win_fore = colours.bottom_panel_colour


                    p += 1

            if rename_playlist_box:

                if gui.level_2_click:
                    input.mouse_click = True
                gui.level_2_click = False

                rect = [0, 0, 250 * gui.scale, 60 * gui.scale]
                rect[0] = int(window_size[0] / 2) - int(rect[2] / 2)
                rect[1] = int(window_size[1] / 2) - rect[3]

                draw.rect((rect[0] - 2 * gui.scale, rect[1] - 2 * gui.scale), (rect[2] + 4 * gui.scale, rect[3] + 4 * gui.scale), colours.grey(60), True)
                draw.rect_r(rect, colours.sys_background_3, True)
                draw.rect((rect[0] + 15 * gui.scale, rect[1] + 30 * gui.scale), (220 * gui.scale, 19 * gui.scale), colours.alpha_grey(10), True)
                gui.win_fore = colours.sys_background_3

                rename_text_area.draw(rect[0] + 20 * gui.scale, rect[1] + 30 * gui.scale, colours.alpha_grey(150), width=220 * gui.scale)

                draw_text((rect[0] + 17 * gui.scale, rect[1] + 5 * gui.scale), "Rename Playlist", colours.grey(180), 12)

                if (key_esc_press and len(editline) == 0) or ((input.mouse_click or right_click) and not rect_in(rect)):
                    rename_playlist_box = False
                    if len(rename_text_area.text) > 0:
                        pctl.multi_playlist[rename_index][0] = rename_text_area.text
                elif key_return_press:
                    rename_playlist_box = False
                    key_return_press = False
                    if len(rename_text_area.text) > 0:
                        pctl.multi_playlist[rename_index][0] = rename_text_area.text

            if track_box:
                if key_return_press or right_click or key_esc_press or key_backspace_press or key_backslash_press:
                    track_box = False
                    if gui.cursor_mode == 1:
                        gui.cursor_mode = 0
                        SDL_SetCursor(cursor_standard)
                    key_return_press = False

                if gui.level_2_click:
                    input.mouse_click = True
                gui.level_2_click = False

                tc = pctl.master_library[r_menu_index]

                w = 540 * gui.scale
                h = 240 * gui.scale
                comment_mode = 0

                if len(tc.comment) > 0:
                    h += 22 * gui.scale
                    w += 25 * gui.scale
                    if draw.text_calc(tc.comment, 12) > 330 * gui.scale or "\n" in tc.comment:
                        h += 80 * gui.scale
                        w += 30 * gui.scale
                        comment_mode = 1

                x = int(window_size[0] / 2) - int(w / 2)
                y = int(window_size[1] / 2) - int(h / 2)

                x1 = x + 18 * gui.scale
                x2 = x + 98 * gui.scale



                draw.rect((x - 3 * gui.scale, y - 3 * gui.scale), (w + 6 * gui.scale, h + 6 * gui.scale), colours.grey(75), True)
                draw.rect((x, y), (w, h), colours.sys_background_3, True)
                gui.win_fore = colours.sys_background_3

                if input.mouse_click and not rect_in([x, y, w, h]):
                    track_box = False
                    if gui.cursor_mode == 1:
                        gui.cursor_mode = 0
                        SDL_SetCursor(cursor_standard)


                else:
                    art_size = 115 * gui.scale

                    if comment_mode == 1:
                        album_art_gen.display(r_menu_index, (x + w - 135 * gui.scale, y + 105 * gui.scale), (art_size, art_size)) # Mirror this size in auto theme #mark2233
                    else:
                        album_art_gen.display(r_menu_index, (x + w - 135 * gui.scale, y + h - 135 * gui.scale), (art_size, art_size))

                    y -= 24 * gui.scale
                    y1 = y + (40 * gui.scale)


                    rect = [x1, y1 + (2 * gui.scale), 350 * gui.scale, 14 * gui.scale]
                    fields.add(rect)
                    if rect_in(rect):
                        draw_text((x1, y1), "Title", colours.grey_blend_bg3(200), 212)
                        if input.mouse_click:
                            show_message("Title copied to clipboard")
                            copy_to_clipboard(pctl.master_library[r_menu_index].title)
                            input.mouse_click = False
                    else:
                        draw_text((x1, y1), "Title", colours.grey_blend_bg3(140), 212)
                        #
                    draw_text((x2, y1 - (3 * gui.scale)), trunc_line(pctl.master_library[r_menu_index].title, 15, w - 190 * gui.scale)
                              , colours.grey_blend_bg3(200), 15)
                    #y += 4


                    ext_rect = [x + w - 38 * gui.scale, y + 44 * gui.scale, 38 * gui.scale, 12 * gui.scale]

                    line = pctl.master_library[r_menu_index].file_ext
                    ex_colour = [130, 130, 130, 255]

                    if line in format_colours:
                        ex_colour = format_colours[line]

                    draw.rect_r(ext_rect, ex_colour, True)
                    draw_text((x + w - 35 * gui.scale, y + 42 * gui.scale), line, alpha_blend([10, 10, 10, 235], ex_colour) , 211, bg=ex_colour)

                    if pctl.master_library[r_menu_index].is_cue:
                        ext_rect[1] += 16 * gui.scale
                        colour = [218, 222, 73, 255]
                        if pctl.master_library[r_menu_index].is_embed_cue:
                            colour = [252, 199, 55, 255]
                        draw.rect_r(ext_rect, colour, True)
                        draw_text((x + w - 35 * gui.scale, y + (42 + 16) * gui.scale), "CUE", alpha_blend([10, 10, 10, 235], colour), 211, bg=colour)


                    y1 += 16 * gui.scale


                    rect = [x1, y1 + (2 * gui.scale), 350 * gui.scale, 14 * gui.scale]
                    fields.add(rect)
                    if rect_in(rect):
                        draw_text((x1, y1), "Artist", colours.grey_blend_bg3(200), 212)
                        if input.mouse_click:
                            show_message("Artist field copied to clipboard")
                            copy_to_clipboard(pctl.master_library[r_menu_index].artist)
                            input.mouse_click = False
                    else:
                        draw_text((x1, y1), "Artist", colours.grey_blend_bg3(140), 212)

                    draw_text((x2, y1 - (2 * gui.scale)), trunc_line(pctl.master_library[r_menu_index].artist, 13, 420 * gui.scale),
                              colours.grey_blend_bg3(200), 13)

                    y1 += 16 * gui.scale

                    rect = [x1, y1 + (2 * gui.scale), 350 * gui.scale, 14 * gui.scale]
                    fields.add(rect)
                    if rect_in(rect):
                        draw_text((x1, y1), "Album", colours.grey_blend_bg3(200), 212)
                        if input.mouse_click:
                            show_message("Album field copied to clipboard")
                            copy_to_clipboard(pctl.master_library[r_menu_index].album)
                            input.mouse_click = False
                    else:
                        draw_text((x1, y1), "Album", colours.grey_blend_bg3(140), 212)

                    draw_text((x2, y1 - 2), trunc_line(pctl.master_library[r_menu_index].album, 13, 420 * gui.scale),
                              colours.grey_blend_bg3(200),
                              13)

                    y1 += (23 + 3) * gui.scale

                    rect = [x1, y1 + 2, 450 * gui.scale, 14 * gui.scale]
                    fields.add(rect)
                    if rect_in(rect):
                        draw_text((x1, y1), "Path", colours.grey_blend_bg3(200), 212)
                        if input.mouse_click:
                            show_message("File path copied to clipboard")
                            copy_to_clipboard(pctl.master_library[r_menu_index].fullpath)
                            input.mouse_click = False
                    else:
                        draw_text((x1, y1), "Path", colours.grey_blend_bg3(140), 212)
                    draw_text((x2, y1), trunc_line(pctl.master_library[r_menu_index].fullpath, 210, 425 * gui.scale),
                              colours.grey_blend_bg3(170), 210)

                    y1 += 15 * gui.scale

                    if pctl.master_library[r_menu_index].samplerate != 0:
                        draw_text((x1, y1), "Samplerate", colours.grey_blend_bg3(140), 212)
                        line = str(pctl.master_library[r_menu_index].samplerate) + " Hz"
                        draw_text((x2, y1), line, colours.grey_blend_bg3(200), 12)

                    y1 += 15 * gui.scale

                    if pctl.master_library[r_menu_index].bitrate not in (0, "", "0"):
                        draw_text((x1, y1), "Bitrate", colours.grey_blend_bg3(140), 212)
                        line = str(pctl.master_library[r_menu_index].bitrate)
                        if pctl.master_library[r_menu_index].file_ext in ('FLAC', 'OPUS', 'APE', 'WV'):
                            line = "~" + line
                        line += " kbps"
                        draw_text((x2, y1), line, colours.grey_blend_bg3(200), 12)

                    # -----------
                    if pctl.master_library[r_menu_index].artist != pctl.master_library[r_menu_index].album_artist != "":
                        x += 170 * gui.scale
                        rect = [x + 7 * gui.scale, y1 + (2 * gui.scale), 160 * gui.scale, 14 * gui.scale]
                        fields.add(rect)
                        if rect_in(rect):
                            draw_text((x + (8 + 75) * gui.scale, y1, 1), "Album Artist", colours.grey_blend_bg3(200), 212)
                            if input.mouse_click:
                                show_message("Album artist copied to clipboard")
                                copy_to_clipboard(pctl.master_library[r_menu_index].album_artist)
                                input.mouse_click = False
                        else:
                            draw_text((x + (8 + 75) * gui.scale, y1, 1), "Album Artist", colours.grey_blend_bg3(140), 212)
                        draw_text((x + (8 + 90)  * gui.scale, y1),
                                  trunc_line(pctl.master_library[r_menu_index].album_artist, 212, 270 * gui.scale),
                                  colours.grey_blend_bg3(200), 12)
                        x -= 170 * gui.scale

                    y1 += 15 * gui.scale

                    rect = [x1, y1, 150 * gui.scale, 16 * gui.scale]
                    fields.add(rect)
                    if rect_in(rect):
                        draw_text((x1, y1), "Duration", colours.grey_blend_bg3(200), 212)
                        if input.mouse_click:
                            copy_to_clipboard(time.strftime('%M:%S', time.gmtime(pctl.master_library[r_menu_index].length)).lstrip("0"))
                            show_message("Duration copied to clipboard")
                            input.mouse_click = False
                    else:
                        draw_text((x1, y1), "Duration", colours.grey_blend_bg3(140), 212)
                    line = time.strftime('%M:%S', time.gmtime(pctl.master_library[r_menu_index].length))
                    draw_text((x2, y1), line, colours.grey_blend_bg3(200), 12)

                    # -----------
                    if pctl.master_library[r_menu_index].track_total not in ("", "0"):
                        x += 170 * gui.scale
                        line = str(pctl.master_library[r_menu_index].track_number) + " of " + str(
                            pctl.master_library[r_menu_index].track_total)
                        draw_text((x + (8 + 75) * gui.scale, y1, 1), "Track", colours.grey_blend_bg3(140), 212)
                        draw_text((x + (8 + 90)  * gui.scale, y1), line,
                                  colours.grey_blend_bg3(200), 12)
                        x -= 170 * gui.scale

                    y1 += 15 * gui.scale
                    #print(pctl.master_library[r_menu_index].size)
                    if pctl.master_library[r_menu_index].size != 0:
                        draw_text((x1, y1), "File size", colours.grey_blend_bg3(140), 212)
                        draw_text((x2, y1), get_filesize_string(pctl.master_library[r_menu_index].size),
                                  colours.grey_blend_bg3(200), 12)

                    # -----------
                    if pctl.master_library[r_menu_index].disc_total not in ("", "0", 0):
                        x += 170 * gui.scale
                        line = str(pctl.master_library[r_menu_index].disc_number) + " of " + str(
                            pctl.master_library[r_menu_index].disc_total)
                        draw_text((x + (8 + 75) * gui.scale, y1, 1), "Disc", colours.grey_blend_bg3(140), 212)
                        draw_text((x + (8 + 90) * gui.scale, y1), line,
                                  colours.grey_blend_bg3(200), 12)
                        x -= 170 * gui.scale

                    y1 += 23 * gui.scale

                    rect = [x1, y1 + (2 * gui.scale), 150 * gui.scale, 14 * gui.scale]
                    fields.add(rect)
                    if rect_in(rect):
                        draw_text((x1, y1), "Genre", colours.grey_blend_bg3(200), 212)
                        if input.mouse_click:
                            show_message("Genre field copied to clipboard")
                            copy_to_clipboard(pctl.master_library[r_menu_index].genre)
                            input.mouse_click = False
                    else:
                        draw_text((x1, y1), "Genre", colours.grey_blend_bg3(140), 212)
                    line = trunc_line(pctl.master_library[r_menu_index].genre, 12, 290)
                    draw_text((x2, y1), line, colours.grey_blend_bg3(200),
                              12)

                    y1 += 15 * gui.scale

                    rect = [x1, y1 + (2 * gui.scale), 150 * gui.scale, 14 * gui.scale]
                    fields.add(rect)
                    if rect_in(rect):
                        draw_text((x1, y1), "Date", colours.grey_blend_bg3(200), 212)
                        if input.mouse_click:
                            show_message("Date field copied to clipboard")
                            copy_to_clipboard(pctl.master_library[r_menu_index].date)
                            input.mouse_click = False
                    else:
                        draw_text((x1, y1), "Date", colours.grey_blend_bg3(140), 212)
                    draw_text((x2, y1), str(pctl.master_library[r_menu_index].date),
                              colours.grey_blend_bg3(200), 12)


                    y1 += 23 * gui.scale

                    total = star_store.get(r_menu_index)
                    ratio = 0

                    if total > 0 and pctl.master_library[
                        r_menu_index].length != 0:
                        ratio = total / pctl.master_library[r_menu_index].length

                    draw_text((x1, y1), "Play count", colours.grey_blend_bg3(140), 212)
                    draw_text((x2, y1), str(int(ratio)), colours.grey_blend_bg3(200), 12)

                    y1 += 15 * gui.scale

                    rect = [x1, y1, 150, 14]

                    if rect_in(rect) and key_shift_down and mouse_wheel != 0:
                        star_store.add(r_menu_index, 60 * mouse_wheel)

                    line = time.strftime('%H:%M:%S',
                                         time.gmtime(total))

                    draw_text((x1, y1), "Play time", colours.grey_blend_bg3(140), 212)
                    draw_text((x2, y1), str(line), colours.grey_blend_bg3(200), 12)



                    # -------
                    if pctl.master_library[r_menu_index].lyrics != "":

                        if draw.button("Lyrics", x1 + 200 * gui.scale, y1 - 10 * gui.scale):
                            track_box = False
                            switch_showcase(r_menu_index)
                            input.mouse_click = False


                    if len(tc.comment) > 0:
                        y1 += 20 * gui.scale
                        rect = [x1, y1 + (2 * gui.scale), 60 * gui.scale, 14 * gui.scale]
                        #draw.rect_r((x2, y1, 335, 10), [255, 20, 20, 255])
                        fields.add(rect)
                        if rect_in(rect):
                            draw_text((x1, y1), "Comment", colours.grey_blend_bg3(200), 212)
                            if input.mouse_click:
                                show_message("Comment copied to clipboard")
                                copy_to_clipboard(pctl.master_library[r_menu_index].comment)
                                input.mouse_click = False
                        else:
                            draw_text((x1, y1), "Comment", colours.grey_blend_bg3(140), 212)
                        # draw_text((x1, y1), "Comment", colours.grey_blend_bg3(140), 12)

                        if "\n" not in tc.comment and ('http://' in tc.comment or 'www.' in tc.comment or 'https://' in tc.comment) and draw.text_calc(
                                tc.comment, 12) < 335 * gui.scale:

                            # line1, line2 = tc.comment.split("\n")
                            #
                            # if len(line2) > 0:
                            #
                            #     link_pa = draw_linked_text((x2, y1 + 13 * gui.scale), line1, colours.grey_blend_bg3(200), 12)
                            #     link_rect2 = [x + 98 * gui.scale + link_pa[0], y1 + 13 - 2 * gui.scale, link_pa[1], 20 * gui.scale]

                            link_pa = draw_linked_text((x2, y1), tc.comment, colours.grey_blend_bg3(200), 12)
                            link_rect = [x + 98 * gui.scale + link_pa[0], y1 - 2 * gui.scale, link_pa[1], 20 * gui.scale]

                            fields.add(link_rect)
                            if coll_point(mouse_position, link_rect):
                                if gui.cursor_mode == 0 and not input.mouse_click:
                                    SDL_SetCursor(cursor_hand)
                                    gui.cursor_mode = 1
                                if input.mouse_click:
                                    # if gui.cursor_mode == 1:
                                    #     gui.cursor_mode = 0
                                    #     SDL_SetCursor(cursor_standard)
                                    webbrowser.open(link_pa[2], new=2, autoraise=True)
                                    track_box = True
                            elif gui.cursor_mode == 1:
                                gui.cursor_mode = 0
                                SDL_SetCursor(cursor_standard)

                        elif comment_mode == 1:
                            draw_text((x + 18 * gui.scale, y1 + 18 * gui.scale, 4, w - 36 * gui.scale, 90 * gui.scale), tc.comment, colours.grey_blend_bg3(200), 12)
                        else:
                            draw_text((x2, y1), tc.comment, colours.grey_blend_bg3(200), 12)

            fader.render()
            if pref_box.enabled:
                # rect = [0, 0, window_size[0], window_size[1]]
                # draw.rect_r(rect, [0, 0, 0, 90], True)
                pref_box.render()

            if gui.rename_folder_box:

                if gui.level_2_click:
                    input.mouse_click = True
                gui.level_2_click = False

                w = 500 * gui.scale
                h = 127 * gui.scale
                x = int(window_size[0] / 2) - int(w / 2)
                y = int(window_size[1] / 2) - int(h / 2)

                draw.rect((x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale), colours.grey(80), True)
                draw.rect((x, y), (w, h), colours.sys_background_3, True)

                if key_esc_press or ((input.mouse_click or right_click) and not coll_point(mouse_position, (x, y, w, h))):
                    gui.rename_folder_box = False

                p = draw_text((x + 10 * gui.scale, y + 9 * gui.scale,), "Folder Modification", colours.grey(195), 213)

                rename_folder.draw(x + 14 * gui.scale, y + 40 * gui.scale, colours.alpha_grey(190), width=300)

                draw.rect((x + 8 * gui.scale, y + 38 * gui.scale), (300 * gui.scale, 22 * gui.scale), colours.grey(50))

                if draw.button("Rename", x + (8 + 300 + 10) * gui.scale, y + 38 * gui.scale, 80 * gui.scale) or input.level_2_enter:
                    rename_parent(rename_index, rename_folder.text)
                    gui.rename_folder_box = False
                    input.mouse_click = False

                if draw.button("Delete", x + (8 + 300 + 10) * gui.scale, y + 11 * gui.scale, 80 * gui.scale, fore_text=colours.grey(255), fg=[180, 60, 60, 255]):
                    delete_folder(rename_index)
                    gui.rename_folder_box = False
                    input.mouse_click = False

                if move_folder_up(rename_index):
                    if draw.button("Compact", x + 408 * gui.scale, y + 38 * gui.scale, 80 * gui.scale):
                        move_folder_up(rename_index, True)
                        input.mouse_click = False

                to_clean = clean_folder(rename_index)
                if to_clean > 0:
                    if draw.button("Clean (" + str(to_clean) + ")", x + 408 * gui.scale, y + 11 * gui.scale, 80 * gui.scale):
                        clean_folder(rename_index, True)
                        input.mouse_click = False

                draw_text((x + 10 * gui.scale, y + 65 * gui.scale,), "PATH", colours.grey(100), 212)
                line = os.path.dirname(pctl.master_library[rename_index].parent_folder_path.rstrip("\\/")).replace("\\", "/") + "/"
                line = right_trunc(line, 12, 420 * gui.scale)
                draw_text((x + 60 * gui.scale, y + 65 * gui.scale,), line, colours.grey(170), 211)

                draw_text((x + 10 * gui.scale, y + 83 * gui.scale), "OLD", colours.grey(100), 212)
                line = trunc_line(pctl.master_library[rename_index].parent_folder_name, 12, 420 * gui.scale)
                draw_text((x + 60 * gui.scale, y + 83 * gui.scale), line, colours.grey(170), 211)

                draw_text((x + 10 * gui.scale, y + 101 * gui.scale), "NEW", colours.grey(100), 212)
                line = trunc_line(parse_template(rename_folder.text, pctl.master_library[rename_index], up_ext=True), 12, 420 * gui.scale)
                draw_text((x + 60 * gui.scale, y + 101 * gui.scale), line, colours.grey(170), 211)


            if renamebox:

                if gui.level_2_click:
                    input.mouse_click = True
                gui.level_2_click = False

                w = 420 * gui.scale
                h = 210 * gui.scale
                x = int(window_size[0] / 2) - int(w / 2)
                y = int(window_size[1] / 2) - int(h / 2)

                draw.rect((x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale), colours.grey(50), True)
                draw.rect((x, y), (w, h), colours.sys_background_3, True)

                if key_esc_press or ((input.mouse_click or right_click) and not coll_point(mouse_position, (x, y, w, h))):
                    renamebox = False

                r_todo = []
                warncue = False

                for item in default_playlist:
                    if pctl.master_library[item].parent_folder_name == pctl.master_library[
                                rename_index].parent_folder_name:
                        if pctl.master_library[item].is_cue is True:
                            warncue = True
                        else:
                            r_todo.append(item)

                draw_text((x + 10 * gui.scale, y + 8 * gui.scale,), "File Renaming", colours.grey(195), 213)
                # draw_text((x + 14, y + 40,), NRN + cursor, colours.grey(150), 12)
                rename_files.draw(x + 14 * gui.scale, y + 40 * gui.scale, colours.alpha_grey(150), width=300)
                NRN = rename_files.text
                # c_blink = 200

                draw.rect((x + 8 * gui.scale, y + 38 * gui.scale), (300 * gui.scale, 22 * gui.scale), colours.grey(50))


                draw_text((x + 10 * gui.scale, y + 70 * gui.scale,), "%n - Track Number", colours.grey(175), 12)
                draw_text((x + 10 * gui.scale, y + 82 * gui.scale,), "%a - Artist Name", colours.grey(175), 12)
                draw_text((x + 10 * gui.scale, y + 94 * gui.scale,), "%t - Track Title", colours.grey(175), 12)
                draw_text((x + 150 * gui.scale, y + 70 * gui.scale,), "%b - Album Title", colours.grey(175), 12)
                draw_text((x + 150 * gui.scale, y + 82 * gui.scale,), "%d - Date/Year", colours.grey(175), 12)
                draw_text((x + 150 * gui.scale, y + 94 * gui.scale,), "%u - Use Underscores", colours.grey(175), 12)
                draw_text((x + 290 * gui.scale, y + 70 * gui.scale,), "%x - File Extension", colours.grey(175), 12)

                afterline = ""
                warn = False
                underscore = False

                for item in r_todo:

                    if pctl.master_library[item].track_number == "" or pctl.master_library[item].artist == "" or \
                                    pctl.master_library[item].title == "" or pctl.master_library[item].album == "":
                        warn = True

                    afterline = parse_template(NRN, pctl.master_library[item])

                    if item == rename_index:
                        break

                draw_text((x + 10 * gui.scale, y + 120 * gui.scale), "BEFORE", colours.grey(120), 12)
                line = trunc_line(pctl.master_library[rename_index].filename, 12, 335)
                draw_text((x + 67 * gui.scale, y + 120 * gui.scale), line, colours.grey(170), 12)

                draw_text((x + 10 * gui.scale, y + 135 * gui.scale,), "AFTER", colours.grey(120), 12)
                draw_text((x + 67 * gui.scale, y + 135 * gui.scale,), trunc_line(afterline, 12, 335), colours.grey(170), 12)

                if (len(NRN) > 3 and len(pctl.master_library[rename_index].filename) > 3 and afterline[-3:].lower() !=
                    pctl.master_library[rename_index].filename[-3:].lower()) or len(NRN) < 4:
                    draw_text((x + 10 * gui.scale, y + 155 * gui.scale,), "Warning: This will change the file extension", [245, 100, 100, 255],
                              13)

                if '%t' not in NRN and '%n' not in NRN:
                    draw_text((x + 10 * gui.scale, y + 170 * gui.scale,), "Warning: The filename might not be unique", [245, 100, 100, 255],
                              13)
                if warn:
                    draw_text((x + 10 * gui.scale, y + 185 * gui.scale,), "Warning: File has incomplete metadata", [245, 100, 100, 255], 13)
                if warncue:
                    draw_text((x + 10 * gui.scale, y + 185 * gui.scale,), "Error: Folder contains tracks from a CUE sheet",
                              [245, 100, 100, 255], 13)


                label = "Write (" + str(len(r_todo)) + ")"
                if warncue:
                    label = "ERROR"

                if draw.button(label, x + (8 + 300 + 10) * gui.scale, y + 38 * gui.scale, 80 * gui.scale) or input.level_2_enter:
                    input.mouse_click = False
                    total_todo = len(r_todo)
                    pre_state = 0

                    for item in r_todo:

                        if pctl.playing_state > 0 and item == pctl.track_queue[pctl.queue_step]:
                            pre_state = pctl.stop(True)

                        afterline = parse_template(NRN, pctl.master_library[item])

                        oldname = pctl.master_library[item].filename
                        oldpath = pctl.master_library[item].fullpath

                        try:
                            print('Renaming...')

                            star = star_store.full_get(item)
                            star_store.remove(item)

                            oldpath = pctl.master_library[item].fullpath

                            oldsplit = os.path.split(oldpath)

                            os.rename(pctl.master_library[item].fullpath, os.path.join(oldsplit[0], afterline))

                            pctl.master_library[item].fullpath = os.path.join(oldsplit[0], afterline)
                            pctl.master_library[item].filename = afterline

                            if star is not None:
                                star_store.insert(item, star)

                        except:
                            total_todo -= 1

                    renamebox = False
                    print('Done')
                    if pre_state == 1:
                        pctl.revert()


                    if total_todo != len(r_todo):
                        show_message("Error.  " + str(total_todo) + "/" + str(len(r_todo)) + " filenames written.", 'warning')

                    else:
                        show_message("Rename complete.", 'done', str(total_todo) + "/" + str(len(r_todo)) + " filenames were written.")




            if radiobox:

                s1 = 16 * gui.scale
                sh = s1 * len(pctl.save_urls)

                w = 450 * gui.scale
                h = 103 * gui.scale + sh
                x = int(window_size[0] / 2) - int(w / 2)
                y = int(window_size[1] / 2) - int(h / 2)

                draw.rect((x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale), colours.grey(50), True)
                draw.rect((x, y), (w, h), colours.sys_background_3, True)

                if key_esc_press or (gui.level_2_click and not coll_point(mouse_position, (x, y, w, h))):
                    radiobox = False

                draw_text((x + 10 * gui.scale, y + 8 * gui.scale,), "Open HTTP Audio Stream", colours.grey(200), 213)
                #gui.win_fore = colours.sys_background_3

                y1 = y
                y += 30 * gui.scale

                to_del = None

                for i, item in enumerate(pctl.save_urls):
                    rect = (x + 13 * gui.scale, y, 380 * gui.scale, s1-1 * gui.scale)
                    if coll_point(mouse_position, rect):
                        if gui.level_2_click:
                            pass

                    draw_text((x + 13 * gui.scale, y), item, colours.grey(150), 12, 330 * gui.scale)

                    rect = (x + (17 + 330) * gui.scale, y, 40 * gui.scale, 14 * gui.scale)
                    fields.add(rect)
                    if coll_point(mouse_position, rect):
                        draw.rect_r(rect, [40, 40, 40, 60], True)
                        if gui.level_2_click:
                            to_del = i

                    draw.rect_r(rect, [50, 50, 50, 75], True)
                    draw_text((rect[0] + 20 * gui.scale, rect[1] + -1 * gui.scale, 2), "Del", colours.grey(180), 211)


                    rect = (x + (17 + 380) * gui.scale, y, 40 * gui.scale, 14 * gui.scale)
                    fields.add(rect)
                    if coll_point(mouse_position, rect):
                        draw.rect_r(rect, [40, 40, 40, 60], True)
                        if gui.level_2_click:
                            radio_field.text = item


                    draw.rect_r(rect, [50, 50, 50, 75], True)
                    draw_text((rect[0] + 20 * gui.scale, rect[1] + -1 * gui.scale, 2), "Sel", colours.grey(180), 211)


                    y += s1

                if to_del is not None:
                    del pctl.save_urls[to_del]


                y = y1 + sh

                radio_field.draw(x + 14 * gui.scale, y + 40 * gui.scale, colours.grey_blend_bg3(170), width=380 * gui.scale, click=gui.level_2_click)

                draw.rect((x + 8 * gui.scale, y + 38 * gui.scale), (380 * gui.scale, 22 * gui.scale), colours.grey(50))

                draw.button("GO", x + (8 + 380 + 10) * gui.scale, y + 38 * gui.scale, 40 * gui.scale)

                if draw.button("Save", x + 337 * gui.scale, y + 70 * gui.scale, 50 * gui.scale, press=gui.level_2_click):
                    pctl.save_urls.append(radio_field.text)

                if (input.level_2_enter or (
                            gui.level_2_click and
                            coll_point(mouse_position, (x + (8 + 380 + 10) *
                                gui.scale, y + 38 * gui.scale, 40 * gui.scale, 22 * gui.scale)))):
                    if 'youtube.' in radio_field.text or 'youtu.be' in radio_field.text:
                        radiobox = False
                        show_message("Sorry, youtube links are not supported.")
                    elif "http://" in radio_field.text or "https://" in radio_field.text \
                            or "ftp://" in radio_field.text:
                        print("Start radio")
                        pctl.url = radio_field.text.encode('utf-8')
                        pctl.playing_state = 0
                        pctl.record_stream = False
                        pctl.playerCommand = "url"
                        pctl.playerCommandReady = True
                        pctl.playing_state = 3
                        pctl.playing_time = 0
                        pctl.playing_length = 0

                    elif radio_field.text == "":
                        pass
                    else:
                        print("Radio fail")
                        radiobox = False
                        gui.update = 1
                        show_message("Could not validate URL.", 'info',
                                     "Make sure the URL starts with 'http://' or 'ftp://'.")

                x -= 230 * gui.scale
                # y += 30
                rect = (x + 277 * gui.scale, y + 70 * gui.scale, 50 * gui.scale, 22 * gui.scale)
                fields.add(rect)

                if pctl.playing_state == 3:

                    if coll_point(mouse_position, rect):
                        if gui.level_2_click:
                            pctl.playerCommand = 'record'
                            pctl.playerCommandReady = True
                        draw.rect((rect[0], rect[1]), (rect[2], rect[3]), alpha_blend([255, 255, 255, 20],
                                                                                      colours.sys_background_3), True)
                        draw_text((rect[0] + 7 * gui.scale, rect[1] + 3 * gui.scale), "Rec", colours.grey(210), 212)
                        draw_text((rect[0] + 34 * gui.scale, rect[1] + 2 * gui.scale), "●", [230, 20, 20, 255], 212)
                    else:
                        draw.rect((rect[0], rect[1]), (rect[2], rect[3]), alpha_blend([255, 255, 255, 9],
                                                                                      colours.sys_background_3), True)
                        draw_text((rect[0] + 7 * gui.scale, rect[1] + 3 * gui.scale), "Rec", colours.grey(190), 212)
                        draw_text((rect[0] + 34 * gui.scale, rect[1] + 2 * gui.scale), "●", [220, 20, 20, 255], 212)
                else:
                    if coll_point(mouse_position, rect):
                        if gui.level_2_click:
                            radiobox = False
                            show_message("A stream needs to be playing first.")
                    draw.rect((rect[0], rect[1]), (rect[2], rect[3]), alpha_blend([255, 255, 255, 7],
                                                                                  colours.sys_background_3), True)
                    draw_text((rect[0] + 7 * gui.scale, rect[1] + 3 * gui.scale), "Rec", colours.grey(150), 212)
                    draw_text((rect[0] + 34 * gui.scale, rect[1] + 2 * gui.scale), "●", [200, 15, 15, 255], 212)

                gui.level_2_click = False

            if gui.message_box:
                if input.mouse_click or key_return_press or right_click or key_esc_press or key_backspace_press \
                        or key_backslash_press:
                    gui.message_box = False
                    key_return_press = False

                w1 = draw.text_calc(gui.message_text, 15) + 74 * gui.scale
                w2 = draw.text_calc(gui.message_subtext, 12) + 74 * gui.scale
                w = max(w1, w2)

                if w < 210 * gui.scale:
                    w = 210 * gui.scale

                h = 60 * gui.scale
                x = int(window_size[0] / 2) - int(w / 2)
                y = int(window_size[1] / 2) - int(h / 2)

                draw.rect((x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale),
                          colours.grey(55), True)
                draw.rect((x, y), (w, h), colours.sys_background_3, True)

                if gui.message_mode == 'info':
                    message_info_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(message_info_icon.h / 2) - 1)
                elif gui.message_mode == 'warning':
                    message_warning_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(message_info_icon.h / 2) - 1)
                elif gui.message_mode == 'done':
                    message_tick_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(message_info_icon.h / 2) - 1)
                elif gui.message_mode == 'arrow':
                    message_arrow_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(message_info_icon.h / 2) - 1)

                if len(gui.message_subtext) > 0:
                    draw_text((x + 62 * gui.scale, y + 9 * gui.scale), gui.message_text, colours.grey(190), 15)
                    draw_text((x + 63, y + (9 + 22) * gui.scale), gui.message_subtext, colours.grey(190), 12)
                else:
                    draw_text((x + 62 * gui.scale, y + 18 * gui.scale), gui.message_text, colours.grey(190), 15)

            # SEARCH
            if (key_backslash_press or (key_ctrl_down and key_f_press)) and quick_search_mode is False:
                quick_search_mode = True
                if search_clear_timer.get() > 3:
                    search_text.text = ""
                input_text = ""
            elif ((key_backslash_press or (key_ctrl_down and key_f_press)) or (
                        key_esc_press and len(editline) == 0)) or input.mouse_click and quick_search_mode is True:
                quick_search_mode = False
                search_text.text = ""

            if quick_search_mode is True:

                rect2 = [0, window_size[1] - 85 * gui.scale, 420 * gui.scale, 25 * gui.scale]
                rect = [0, window_size[1] - 125 * gui.scale, 420 * gui.scale, 65 * gui.scale]
                rect[0] = int(window_size[0] / 2) - int(rect[2] / 2)
                rect2[0] = rect[0]

                draw.rect_r((rect[0] - 2, rect[1] - 2, rect[2] + 4, rect[3] + 4), [200,90,2,255], True)

                gui.win_fore = colours.sys_background_4
                draw.rect_r(rect, colours.sys_background_4, True)

                if len(input_text) > 0:
                    search_index = -1

                if len(search_text.text) == 0:
                    gui.search_error = False

                if len(search_text.text) != 0 and search_text.text[0] == '/':
                    # if "/love" in search_text.text:
                    #     line = "last.fm loved tracks from user. Format: /love <username>"
                    # else:
                    line = "Folder filter mode. Enter path segment."
                    draw_text((rect[0] + 23 * gui.scale, window_size[1] - 84 * gui.scale), line, colours.grey(100), 11)
                else:
                    line = "Use UP / DOWN to navigate results. SHIFT + RETURN to show all."
                    draw_text((rect[0] + int(rect[2] / 2), window_size[1] - 84 * gui.scale, 2), line,
                              colours.grey(100), 11)

                    # draw_text((rect[0] + int(rect[2] / 2), window_size[1] - 118 * gui.scale, 2), "Find",
                    #           colours.grey(90), 214)

                # if len(pctl.track_queue) > 0:

                    # if input_text == 'A':
                    #     search_text.text = pctl.playing_object().artist
                    #     input_text = ""

                if gui.search_error:
                    draw.rect_r([rect[0], rect[1], rect[2], 30 * gui.scale], [180, 40, 40, 255], True)
                    gui.win_fore = [180, 40, 40, 255] #alpha_blend([255,0,0,25], gui.win_fore)
                # if key_backspace_press:
                #     gui.search_error = False

                search_text.draw(rect[0] + 8 * gui.scale, rect[1] + 4 * gui.scale, colours.grey(230), font=213)

                if (key_shift_down or (len(search_text.text) > 0 and search_text.text[0] == '/')) and key_return_press:
                    key_return_press = False
                    playlist = []
                    if len(search_text.text) > 0:
                        if search_text.text[0] == '/':

                            if search_text.text.lower() == "/random" or search_text.text.lower() == "/shuffle":
                                gen_500_random(pctl.playlist_active)
                            elif search_text.text.lower() == "/top" or search_text.text.lower() == "/most":
                                gen_top_100(pctl.playlist_active)
                            elif search_text.text.lower() == "/length" or search_text.text.lower() == "/duration"\
                                    or search_text.text.lower() == "/len":
                                gen_sort_len(pctl.playlist_active)

                            else:

                                if search_text.text[-1] == "/":
                                    t_title = search_text.text.replace('/', "")
                                else:
                                    search_text.text = search_text.text.replace('/', "")
                                    t_title = search_text.text
                                search_text.text = search_text.text.lower()
                                for item in default_playlist:
                                    if search_text.text in pctl.master_library[item].parent_folder_path.lower():
                                        playlist.append(item)
                                if len(playlist) > 0:

                                    pctl.multi_playlist.append(pl_gen(title=t_title,
                                                                      playlist=copy.deepcopy(playlist)))
                                    switch_playlist(len(pctl.multi_playlist) - 1)

                        else:
                            search_terms = search_text.text.lower().split()
                            for item in default_playlist:
                                line = pctl.master_library[item].title.lower() + \
                                       pctl.master_library[item].artist.lower() \
                                       + pctl.master_library[item].album.lower() + \
                                       pctl.master_library[item].filename.lower()
                                if all(word in line for word in search_terms):
                                    playlist.append(item)
                            if len(playlist) > 0:
                                pctl.multi_playlist.append(pl_gen(title="Search Results",
                                                                  playlist=copy.deepcopy(playlist)))
                                switch_playlist(len(pctl.multi_playlist) - 1)
                        search_text.text = ""
                        quick_search_mode = False

                if (len(input_text) > 0 and not gui.search_error) or key_down_press is True or key_backspace_press\
                        or gui.force_search:

                    gui.pl_update = 1

                    if gui.force_search:
                        search_index = 0



                    if key_backspace_press:
                        search_index = 0

                    if len(search_text.text) > 0 and search_text.text[0] != "/":
                        oi = search_index

                        while search_index < len(default_playlist) - 1:
                            search_index += 1
                            if search_index > len(default_playlist) - 1:
                                search_index = 0

                            search_terms = search_text.text.lower().split()
                            line = pctl.master_library[default_playlist[search_index]].title.lower() + \
                                pctl.master_library[default_playlist[search_index]].artist.lower() \
                                + pctl.master_library[default_playlist[search_index]].album.lower() + \
                                pctl.master_library[default_playlist[search_index]].filename.lower()

                            if all(word in line for word in search_terms):

                                playlist_selected = search_index
                                if len(default_playlist) > 10 and search_index > 10:
                                    playlist_position = search_index - 7
                                else:
                                    playlist_position = 0

                                if gui.combo_mode:
                                    pctl.show_selected()
                                gui.search_error = False

                                break

                        else:
                            search_index = oi
                            if len(input_text) > 0 or gui.force_search:
                                gui.search_error = True
                            if key_down_press:
                                bottom_playlist.pulse()

                        gui.force_search = False

                if key_up_press is True:

                    gui.pl_update = 1
                    oi = search_index

                    while search_index > 1:
                        search_index -= 1
                        if search_index > len(default_playlist) - 1:
                            search_index = len(default_playlist) - 1
                        search_terms = search_text.text.lower().split()
                        line = pctl.master_library[default_playlist[search_index]].title.lower() + \
                            pctl.master_library[default_playlist[search_index]].artist.lower() \
                            + pctl.master_library[default_playlist[search_index]].album.lower() + \
                            pctl.master_library[default_playlist[search_index]].filename.lower()

                        if all(word in line for word in search_terms):

                            playlist_selected = search_index
                            if len(default_playlist) > 10 and search_index > 10:
                                playlist_position = search_index - 7
                            else:
                                playlist_position = 0
                            if gui.combo_mode:
                                pctl.show_selected()
                            break
                    else:
                        search_index = oi

                        edge_playlist.pulse()

                if key_return_press is True and search_index > -1:
                    gui.pl_update = 1
                    pctl.jump(default_playlist[search_index], search_index)
                    if album_mode:
                        goto_album(pctl.playlist_playing)
                    quick_search_mode = False
                    search_clear_timer.set()

            else:

                if key_up_press:
                    shift_selection = []

                    pctl.show_selected()
                    gui.pl_update = 1

                    if playlist_selected > 0:
                        playlist_selected -= 1

                    if playlist_position > 0 and playlist_selected < playlist_position + 2:
                        playlist_position -= 1
                    if playlist_selected > len(default_playlist):
                        playlist_selected = len(default_playlist)

                if key_down_press and playlist_selected < len(default_playlist):
                    shift_selection = []
                    pctl.show_selected()
                    gui.pl_update = 1

                    if playlist_selected < len(default_playlist) - 1:
                        playlist_selected += 1

                    if playlist_position < len(
                            default_playlist) and playlist_selected > playlist_position + gui.playlist_view_length - 3 - gui.row_extra:
                        playlist_position += 1

                    if playlist_selected < 0:
                        playlist_selected = 0

                if key_return_press and not pref_box.enabled and not radiobox:
                    gui.pl_update = 1
                    if playlist_selected > len(default_playlist) - 1:
                        playlist_selected = 0
                        shift_selection = []
                    pctl.jump(default_playlist[playlist_selected], playlist_selected)
                    if album_mode:
                        goto_album(pctl.playlist_playing)

        elif GUI_Mode == 3:

            album_art_gen.display(pctl.track_queue[pctl.queue_step],
                                  (0, 0), (window_size[1], window_size[1]))

        # Render Menus-------------------------------
        for instance in Menu.instances:
            instance.render()

        if view_box.active:
            view_box.render()

        tool_tip.render()

        if gui.cursor_mode == 4 and gui.flag_special_cursor is False:
            gui.cursor_mode = 0
            SDL_SetCursor(cursor_standard)

        if draw_border:

            rect = (window_size[0] - 55 * gui.scale, window_size[1] - 35 * gui.scale, 53 * gui.scale, 33 * gui.scale)
            fields.add(rect)

            rect = (window_size[0] - 65 * gui.scale, 1 * gui.scale, 35 * gui.scale, 28 * gui.scale)
            draw.rect((rect[0], rect[1]), (rect[2] + 1 * gui.scale, rect[3]), [0, 0, 0, 50], True)
            fields.add(rect)
            if coll_point(mouse_position, rect):
                draw.rect((rect[0], rect[1]), (rect[2] + 1 * gui.scale, rect[3]), [70, 70, 70, 100], True)
                draw.rect((rect[0] + 11 * gui.scale, rect[1] + 16 * gui.scale), (14 * gui.scale, 3 * gui.scale),
                          [160, 160, 160, 160], True)
                if input.mouse_click or ab_click:
                    SDL_MinimizeWindow(t_window)
                    mouse_down = False
                    input.mouse_click = False
                    drag_mode = False
            else:
                draw.rect((rect[0] + 11 * gui.scale, rect[1] + 16 * gui.scale), (14 * gui.scale, 3 * gui.scale),
                          [120, 120, 120, 45], True)

            rect = (window_size[0] - 29 * gui.scale, 1 * gui.scale, 26 * gui.scale, 28 * gui.scale)
            draw.rect((rect[0], rect[1]), (rect[2] + 1, rect[3]), [0, 0, 0, 50], True)
            fields.add(rect)
            if coll_point(mouse_position, rect):
                draw.rect((rect[0], rect[1]), (rect[2] + 1 * gui.scale, rect[3]), [80, 80, 80, 120], True)
                top_panel.exit_button.render(rect[0] + 8 * gui.scale, rect[1] + 8 * gui.scale, colours.artist_playing)
                if input.mouse_click or ab_click:
                    running = False
            else:
                top_panel.exit_button.render(rect[0] + 8 * gui.scale, rect[1] + 8 * gui.scale, [40, 40, 40, 255])

            if not fullscreen:

                corner_icon.render(window_size[0] - corner_icon.w, window_size[1] - corner_icon.h, [40, 40, 40, 160])

                colour = [30, 30, 30, 255]
                draw.rect_r((0, 0, window_size[0], 1 * gui.scale), colour, True)
                draw.rect_r((0, 0, 1 * gui.scale, window_size[1]), colour, True)
                draw.rect_r((0, window_size[1] - 1 * gui.scale, window_size[0], 1 * gui.scale), colour, True)
                draw.rect_r((window_size[0] - 1 * gui.scale, 0, 1 * gui.scale, window_size[1]), colour, True)

        # Drag icon next to cursor
        if quick_drag and mouse_down and not point_proximity_test(gui.drag_source_position, mouse_position, 15):
            i_x, i_y = get_sdl_input.mouse()
            gui.drag_source_position = [0, 0]
            if window_size[1] - gui.panelBY > i_y > gui.panelY:
                if len(shift_selection) == 1:
                    draw.rect_r((i_x + 20, i_y + 1, 10, 10), [150, 150, 235, 240], True)
                else:
                    draw.rect_r((i_x + 20, i_y + 1, 10, 25), [150, 150, 235, 240], True)

            gui.update += 1

        gui.update -= 1
        gui.present = True



        SDL_SetRenderTarget(renderer, None)
        SDL_RenderCopy(renderer, gui.main_texture, None, gui.abc)

        if gui.turbo:
            gui.level_update = True

    if gui.vis == 1 and pctl.playing_state != 1 and gui.level_peak != [0, 0] and gui.turbo:

        # print(gui.level_peak)
        gui.time_passed = gui.level_time.hit()
        if gui.time_passed > 1:
            gui.time_passed = 0
        while gui.time_passed > 0.01:
            gui.level_peak[1] -= 0.5
            if gui.level_peak[1] < 0:
                gui.level_peak[1] = 0
            gui.level_peak[0] -= 0.5
            if gui.level_peak[0] < 0:
                gui.level_peak[0] = 0
            gui.time_passed -= 0.020

        gui.level_update = True

    if gui.level_update is True and not resize_mode:
        gui.level_update = False

        SDL_SetRenderTarget(renderer, None)
        if not gui.present:

            SDL_RenderCopy(renderer, gui.main_texture, None, gui.abc)
            gui.present = True

        if gui.vis == 3:
            # Scrolling spectrogram

            # if not vis_update:
            #     print("No UPDATE " + str(random.randint(1,50)))
            if len(gui.spec2_buffers) > 0 and gui.spec2_timer.get() > 0.04:
                #gui.spec2_timer.force_set(gui.spec2_timer.get() - 0.04)
                gui.spec2_timer.set()
                vis_update = True


            if len(gui.spec2_buffers) > 0 and vis_update:
                vis_update = False
                #print(test_timer.hit())

                SDL_SetRenderTarget(renderer, gui.spec2_tex)
                for i, value in enumerate(gui.spec2_buffers[0]):

                    draw.rect_r([gui.spec2_position, i, 1, 1],
                                [min(255, prefs.spec2_base[0] + int(value * prefs.spec2_multiply[0])),
                                 min(255, prefs.spec2_base[1] + int(value * prefs.spec2_multiply[1])),
                                 min(255, prefs.spec2_base[2] + int(value * prefs.spec2_multiply[2])),
                                 255], True)

                del gui.spec2_buffers[0]


                gui.spec2_position += 1

                if gui.spec2_position > gui.spec2_w - 1:
                    gui.spec2_position = 0


                SDL_SetRenderTarget(renderer, None)


            #
            # else:
            #     print("animation stall" + str(random.randint(1, 10)))

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
                draw.rect_r((gui.spec2_rec.x, gui.spec2_rec.y, gui.spec2_rec.w, gui.spec2_rec.h), [0, 0, 0, 90], True)

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

                    if pctl.playing_state == 0 and checkEqual(gui.s_spec):
                        gui.level_update = True
                        time.sleep(0.008)
                else:
                    gui.s_spec = gui.spec
            else:
                pass

            if not gui.test:

                SDL_SetRenderTarget(renderer, gui.spec1_tex)

                # draw.rect_r(gui.spec_rect, colours.top_panel_background, True)
                draw.rect_r((0, 0, gui.spec_w, gui.spec_h), colours.vis_bg, True)

                # xx = 0
                gui.bar.x = 0
                on = 0

                SDL_SetRenderDrawColor(renderer, colours.vis_colour[0],
                                       colours.vis_colour[1], colours.vis_colour[2],
                                       colours.vis_colour[3])

                for item in gui.s_spec:

                    if on > 19:
                        break
                    on += 1

                    item -= 1

                    if item < 1:
                        gui.bar.x += 4 * gui.scale
                        continue

                    if item > 20:
                        item = 20

                    if gui.scale == 2:
                        item *= gui.scale

                    gui.bar.y = 0 + gui.spec_h - item
                    gui.bar.h = item

                    SDL_RenderFillRect(renderer, gui.bar)

                    gui.bar.x += 4 * gui.scale

                if pref_box.enabled:
                    draw.rect_r((0, 0, gui.spec_w, gui.spec_h), [0, 0, 0, 90], True)

                SDL_SetRenderTarget(renderer, None)
                SDL_RenderCopy(renderer, gui.spec1_tex, None, gui.spec1_rec)

        if gui.vis == 1:

            SDL_SetRenderTarget(renderer, gui.spec_level_tex)

            x = window_size[0] - 20 * gui.scale - gui.offset_extra
            y = gui.level_y
            w = gui.level_w
            s = gui.level_s

            y = 0

            gui.spec_level_rec.x = x - 70 * gui.scale
            draw.rect((0, 0), (79 * gui.scale, 18 * gui.scale), colours.grey(10),
                      True)

            x = gui.level_ww - 9 * gui.scale
            y = 10 * gui.scale

            if (gui.level_peak[0] > 0 or gui.level_peak[1] > 0) and pctl.playing_state != 1:
                gui.level_update = True
                time.sleep(0.016)
                # print(vis_decay_timer.get())
                # vis_decay_timer.set()
                pass

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
                draw.rect(((x - (w * t) - (s * t)), y), (w, w), cc, True)

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
                draw.rect(((x - (w * t) - (s * t)), y), (w, w), cc, True)

            SDL_SetRenderTarget(renderer, None)
            SDL_RenderCopy(renderer, gui.spec_level_tex, None, gui.spec_level_rec)


    if gui.present:
        SDL_SetRenderTarget(renderer, None)
        SDL_RenderPresent(renderer)

        gui.present = False

    # -------------------------------------------------------------------------------------------
    # Misc things to update every tick

    # Broadcast control
    if pctl.broadcast_active and pctl.broadcast_time > pctl.master_library[
            pctl.broadcast_index].length and not pctl.join_broadcast:
        pctl.broadcast_position += 1
        print('next')
        if pctl.broadcast_position > len(pctl.multi_playlist[pctl.broadcast_playlist][2]) - 1:
            print('reset')
            pctl.broadcast_position = 0

        pctl.broadcast_index = pctl.multi_playlist[pctl.broadcast_playlist][2][pctl.broadcast_position]
        pctl.broadcast_time = 0
        pctl.target_open = pctl.master_library[pctl.broadcast_index].fullpath
        pctl.b_start_time = pctl.master_library[pctl.broadcast_index].start_time
        pctl.playerCommand = "cast-next"
        pctl.playerCommandReady = True
        pctl.broadcast_line = pctl.master_library[pctl.broadcast_index].artist + " - " + pctl.master_library[
            pctl.broadcast_index].title

    elif pctl.join_broadcast and pctl.broadcast_active:
        pctl.broadcast_index = pctl.track_queue[pctl.queue_step]
        pctl.broadcast_time = pctl.playing_time

    if pctl.broadcast_active and pctl.broadcast_time != pctl.broadcast_last_time:
        pctl.broadcast_last_time = pctl.broadcast_time
        gui.update += 1
    if pctl.broadcast_active and pctl.broadcast_time == 0:
        gui.pl_update = 1

    # Update progress indicator on Windows task bar
    if taskbar_progress and system == 'windows' and pctl.playing_state == 1:
        windows_progress.update()

    # Update d-bus metadata on Linux
    if pctl.playing_state == 1 and pctl.mpris is not None:
        pctl.mpris.update_progress()

    # GUI time ticker update
    if (pctl.playing_state == 1 or pctl.playing_state == 3) and gui.lowered is False:
        if int(pctl.playing_time) != int(pctl.last_playing_time):
            pctl.last_playing_time = pctl.playing_time
            bottom_bar1.seek_time = pctl.playing_time
            gui.update = 1

    if system == 'windows':

        if mouse_down is False:
            drag_mode = False

        if input.mouse_click and mouse_down and 1 < mouse_position[1] < 30 and top_panel.drag_zone_start_x < \
                mouse_position[0] < window_size[0] - 80 * gui.scale and drag_mode is False and clicked is False:
            
            drag_mode = True
            lm = copy.deepcopy(mouse_position)

        if mouse_up:
            drag_mode = False

        if drag_mode:
            p_x = pointer(c_int(0))
            p_y = pointer(c_int(0))
            SDL_GetGlobalMouseState(p_x, p_y)
            mp = [p_x.contents.value, p_y.contents.value]

            time.sleep(0.005)
            SDL_SetWindowPosition(t_window, mp[0] - lm[0], mp[1] - lm[1])

    # Auto save play times to disk
    if pctl.total_playtime - time_last_save > 600:
        print("Auto Save")
        pickle.dump(star_store.db, open(user_directory + "/star.p", "wb"))
        time_last_save = pctl.total_playtime

    # Always render at least one frame per minute (to avoid SDL bugs I guess)
    if min_render_timer.get() > 60:
        min_render_timer.set()
        gui.pl_update = 1
        gui.update += 1

    # Save power if the window is minimized
    if gui.lowered:
        time.sleep(0.2)

SDL_DestroyWindow(t_window)

pctl.playerCommand = "unload"
pctl.playerCommandReady = True

pickle.dump(star_store.db, open(user_directory + "/star.p", "wb"))
date = datetime.date.today()
pickle.dump(star_store.db, open(user_directory + "/star.p.backup" + str(date.month), "wb"))

save_state()

print("unloading SDL")
IMG_Quit()
SDL_QuitSubSystem(SDL_INIT_EVERYTHING)
SDL_Quit()
print("SDL unloaded")

if system == "linux":
    if media_key_mode == 2:
        hookman.cancel()

exit_timer = Timer()
exit_timer.set()
while pctl.playerCommand != 'done':
    time.sleep(0.2)
    if exit_timer.get() > 3:
        break

print("bye")
