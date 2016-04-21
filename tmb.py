# -*- coding: utf-8 -*-

#    Tauon Music Box

#    Copyright (c) 2015, Taiko2k captain.gxj@gmail.com
# 
#    Permission to use, copy, modify, and/or distribute this software for any
#    purpose with or without fee is hereby granted, provided that the above
#    copyright notice and this permission notice appear in all copies.
# 
#    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
#    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
#    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
#    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
#    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
#    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
#    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE

# --------------------------------------------------------------------
# Preamble

# Welcome to the Tauon Music Box source code. I started this project when I was first
# learning programming and python, as a result this code can be quite messy, no doubt I have
# written some things terribly wrong or inefficiently in places.
# I would highly recommend not using this project as an example on how to code cleanly


# --------------------------------------------------------------------

import os
import time
import sys
import ctypes
import random
import fractions
import threading
import io
import pickle
import copy
import subprocess
import urllib.parse
import datetime
import pylast
import shutil
import shlex
import math
import locale
import webbrowser
import pyperclip
import base64


from ctypes import *

t_version = "v1.3.4"
version_line = "Tauon Music Box " + t_version
print(version_line)
print('Copyright (c) 2015 Taiko2k captain.gxj@gmail.com\n')


locale.setlocale(locale.LC_ALL, "")

if sys.platform == 'win32':
    system = 'windows'
    print("Detected platform: Windows")
else:
    system = 'not-windows'
    print("Detected platform: Linux")

working_directory = os.getcwd()
print("Working directory: " + working_directory)
print('Argument List: ' + str(sys.argv))
install_directory = sys.path[0]
install_directory = install_directory.replace('\\', '/')
if 'base_library' in install_directory:
    install_directory = os.path.dirname(install_directory)
print('Install directory: ' + install_directory)
user_directory = install_directory
print('User directory: ' + user_directory)
encoder_output = user_directory + '/encoder/'


b_active_directroy = install_directory.encode('utf-8')


if system == 'windows':
    os.environ["PYSDL2_DLL_PATH"] = install_directory + "\\lib"
    from ctypes import windll, CFUNCTYPE, POINTER, c_int, c_void_p, byref
    import win32con, win32api, win32gui, atexit
# else:
#     from Xlib import display


import sdl2
from sdl2 import *
from sdl2.sdlttf import *
from sdl2.sdlimage import *

from PIL import Image
from PIL import ImageFilter

from hsaudiotag import auto
import stagger
from stagger.id3 import *

# if system != 'windows':
#     def mousepos():
#         mouse_data = display.Display().screen().root.query_pointer()._data
#         return mouse_data["root_x"], mouse_data["root_y"]


class Timer3(object):
    def __init__(self):
        self.start = time.time()

    def set(self):
        self.start = time.time()
        return self

    def get(self):
        self.end = time.time()
        self.secs = self.end - self.start
        return self.secs


spec_decay_timer = Timer3()

min_render_timer = Timer3()


class Timer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.start = time.time()

    def get(self, text):
        end = time.time()
        secs = end - self.start
        msecs = secs * 1000  # millisecs
        self.start = time.time()
        if self.verbose:
            print(text + ": " + str(msecs))
        else:
            return msecs


class Timer2(object):
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.start = time.time()

    def get(self):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000  # millisecs
        self.start = time.time()
        if self.verbose:
            print(str(self.msecs))
        return self.msecs


bm = Timer(True)

# GUI Variables -------------------------------------------------------------------------------------------
GUI_Mode = 1
input_text_mode = False

draw_border = False
resize_drag = [0, 0]
resize_mode = False
resize_size = [0, 0]

version = 0.8

block6 = False

highlight_left_custom = 0
highlight_right_custom = 0

sspec = [0] * 24

side_panel_text_align = 0
# print(sspec)
main_font = 'DroidSansFallback.ttf'

album_mode = False
spec = None
spec_smoothing = True

auto_play_import = False

update_spec = 0
vis = 2
offset_extra = 0

custom_line = "t;r65;o;l;r2;n;p0.33;a;p0.65;b"
custom_pro = custom_line.split(";")
custom_line_mode = False

highlight_x_offset = 0


old_album_pos = -55
old_side_pos = 200
album_dex = []
row_len = 5
last_row = 0
album_v_gap = 65
album_h_gap = 30
album_mode_art_size = 130
albums_to_render = 0
pre_cache = []

reset_playing = False
transcode_bitrate = 64
album_pos_px = 1
time_last_save = 0
window_size = [720, 380]
b_info_y = int(window_size[1] * 0.7)
fullscreen = 0

volume_bar_size = [120, 15]
volume_bar_right = 20
volume_bar_position = [window_size[0] - volume_bar_size[0] - volume_bar_right, 45]

volume_bar_being_dragged = False
volume_bar_increment = 2

volume_store = 50

playlist_row_height = 16
playlist_text_offset = 0
row_alt = False
thick_lines = True
playlist_line_x_offset = 7

to_get = 0
to_got = 0

seek_bar_size = [220, 15]
seek_bar_right = 20
seek_bar_being_dragged = False

editline = ""
side_panel_enable = True
quick_drag = False
scrobble_mark = False
radiobox = False
NXN = "http://"
NRN = "%n. %a - %t%x"

renamebox = False
rename_index = 199
p_stay = 0

savetime = 0

a_time = 0
b_time = 0
a_index = -1
a_pt = False
a_sc = False

l = 0
c_l = 0
m_l = 700
level_peak = [0, 0]
seek_bar_position = [window_size[0] - seek_bar_size[0] - volume_bar_right, 20]

broadcast = False
join_broadcast = False
broadcast_playlist = 0
broadcast_position = 0
broadcast_index = 0
broadcast_time = 0
broadcast_last_time = 0

WHITE = [255, 255, 255, 255]
BLACK = [0, 0, 0, 255]
GREY1 = [25, 25, 25, 255]
GREY2 = [50, 50, 50, 255]
GREY3 = [75, 75, 75, 255]
GREY4 = [100, 100, 100, 255]
GREY5 = [125, 125, 125, 255]
GREY6 = [150, 150, 150, 255]
GREY7 = [175, 175, 175, 255]
GREY8 = [200, 200, 200, 255]
GREEN4 = [0, 100, 0, 255]
GREEN5 = [0, 125, 0, 255]
GREEN6 = [0, 150, 0, 255]
GREEN7 = [0, 175, 0, 255]
RED5 = [175, 0, 0, 255]
YELLOW5 = [90, 90, 20, 255]


def GREY(value):
    return [value, value, value, 255]


compact_bar = False
seek_bg = [28, 28, 28, 255]
sep_line = [16, 16, 16, 255]
bb_line = [50, 50, 50, 255]
tb_line = [50, 50, 50, 255]
theme = 5
themeChange = True
panelY = 78
bh = [20, 4, 45, 255]
tag_meta = ""
side_panel_size = 178
background = BLACK
side_panel_bg = background
BPanel = [4, 4, 4, 255]
lineON = GREEN5
lineOFF = GREY2
linePlaying = lineON
lineBGplaying = [15, 15, 15, 255]
lineBGSelect = [15, 15, 15, 255]
artist_colour = lineON

bottom_panel_colour = [8, 8, 8, 255]

side_bar_line1 = GREY(175)
side_bar_line2 = GREY(155)

stepctloff = GREY(20)
stepctlover = GREY(40)
stepctlon = GREY(120)

art_box = GREY(20)

timeColour = lineON
indexColour = timeColour
starLineColour = [140, 140, 0, 255]
lineColour = [50, 50, 50, 255]
folderTitleColour = [200, 200, 0, 255]
folderLineColour = [140, 140, 0, 255]

ButtonsOver = GREY(200)
ButtonsActive = GREY(150)

playlist_line_active = GREY(170)
playlist_line = GREY(140)
playlist_bg = [14, 14, 14, 255]
playlist_over = [18, 18, 18, 255]
playlist_bg_active = [27, 27, 27, 255]

ButtonsBG = [30, 30, 30, 255]

ModeButtonHit = [24, 0, 70, 255]

PlayingTimeColour = GREY8
MCountColour = GREY8

volume_bar_bg = [19, 19, 19, 255]
volume_bar_outline_colour = GREY4
volume_bar_fill_colour = [95, 95, 95, 255]
seek_bar_outline_colour = GREY4
seek_bar_fill_colour = GREY(110)

ExtInfoColour = GREY4

index_playing_cl = indexColour
time_playing_cl = indexColour
artist_playing_cl = artist_colour
album_cl = lineColour
album_playing = artist_colour

enable_transcode = False

playlist_top = 120
playlist_width = int(window_size[0] * 0.65) + 25
playlist_left = 20

UPDATE_RENDER = 5
UPDATE_LEVEL = False

info_panel_position = (200, 15)
info_panel_vert_spacing = 20
info_panel_hor_spacing = 0

load_to = []

time_display_position_right = 200
time_display_position = [window_size[0] - time_display_position_right, 45]

URL = ""

repeat_click_off = False
random_click_off = False


scroll_enable = True
break_enable = True
dd_index = False

scroll_colour = [30, 30, 30, 255]
album_playlist_left = 600
album_playlist_width = 430
album_colour_cache = {}

lastmouse = [0, 0]
labelrender = None
update_title = False
star_lines = True

tab_hold = False
tab_hold_index = 0
playlist_hold_position = 0
playlist_hold = False
shift_select = 0
shift_selected = False
shift_range = range(0, 0)

shift_selection = []
# Control Variables--------------------------------------------------------------------------

mouse_down = False
right_down = False

volume_hit = False
seek_hit = False
seek_down = False

mouse_position = [0, 0]

key_shift_down = False
dragmode = False
side_drag = False
clicked = False
# Player Variables----------------------------------------------------------------------------

volume = 100
DA_Formats = {'MP3', 'mp3', 'WAV', 'wav', 'OPUS', 'opus', 'FLAC', 'flac', 'APE', 'ape',
              'm4a', 'M4A', 'MP4', 'mp4', 'ogg', 'OGG', 'AAC', 'aac', 'tta', 'TTA'}

url_record = True
record_split = True
record_path = "Radio/"
auto_stop = False
encpause = 0

l_x = 0
# Buttons-----------------------------------------------------------------

Buttons = []
File_Buttons = []
Mode_Buttons = []

r = (130, 85, 10, 15)

droped_file = []
cargo = []
default_player = 'BASS'
loaded_player = ""
# ---------------------------------------------------------------------
# Player variables

pl_follow = False
time_to_get = []

turbo = False
turbonext = 0
level = 0
# avlevel = [0,0,0,0]
# maxl = 0
dlevel = 0

olevel = 0

change_volume_fade_time = 400
pause_fade_time = 400
cross_fade_time = 700

encoding_box = False
encoding_box_click = False

# List of encodings to show in the fix mojibake function
encodings = ['cp932', 'utf-8', 'big5hkscs', 'gbk']

track_box = False
total_playtime = 0

genre_box = False
genre_box_pl = 0
genre_items = []

transcode_list = []
transcode_state = ""

taskbar_progress = False
QUE = []

playing_in_queue = 0
player_from = 'File'

new_time = 0

split_line = True
line0 = ""

draw_sep_hl = False
# -------------------------------------------------------------------------------
# Playlist Variables
album_gal = False

playlist_position = 0
playlist_playing = -1
playlist_selected = -1

playlist_view_length = 50
loading_in_progress = False

random_mode = False
repeat_mode = False
random_button_position = window_size[0] - 90, 83
direct_jump = False

broadcast_line = ""

# [Name, playing, playlist, position, hide folder title, selected]
multi_playlist = [['Default', 0, [], 0, 0, 0]]

default_playlist = multi_playlist[0][2]
playlist_active = 0

playlist_entry_box_size = [250, 60]

playlist_entry_box_half = [int(playlist_entry_box_size[0] / 2), int(playlist_entry_box_size[1] / 2)]
NPN = ""
NSN = ""
search_box_location_x = 0
quick_search_box_size = [400, 25]
new_playlist_box = False
rename_playlist_box = False
rename_index = 0

quick_search_mode = False
search_index = 0

lfm_user_box = False
lfm_pass_box = False
message_box = False
message_box_text = ""
lfm_password = ""
lfm_username = ""
lfm_hash = ""
# ----------------------------------------
# Playlist right click menu

r_menu_index = 0

# Library and loader Variables--------------------------------------------------------
master_library = {}
star_library = {}
cue_list = []

loaderCommand = ""
loaderCommandReady = False
paths_to_load = []
master_count = 0
items_loaded = []

p_start = 0
p_end = 0

b_start = 0
b_end = 0

c_start = 0
c_end = 0

pause_lock = False

folder_image_offsets = {}
db_version = 0

meidakey = 1
mediakeymode = 1

enable_web = False
allow_remote = False
expose_web = False

# A mode ------------

albums = []
album_position = 0

prefer_side = True
dim_art = True

view_prefs = {

    'split-line': True,
    'update-title': False,
    'star-lines': True,
    'side-panel': True,
    'dim-art': True,
    'pl-follow': False,
    'scroll-enable': True

}


def num_from_line(line):
    number = ""
    for ch in line:
        if ch.isdigit():
            number += ch
    number = int(number)
    if number < 50:
        number = 50
    if number > 5000:
        number = 5000
    return number


# -----------------------------------------------------
# STATE LOADING

try:
    star_library = pickle.load(open(user_directory + "/star.p", "rb"))
except:
    print('No existing star.p file')

try:
    save = pickle.load(open(user_directory + "/state.p", "rb"))
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
    cue_list = save[11]
    NXN = save[12]
    theme = save[13]
    folder_image_offsets = save[14]
    lfm_username = save[15]
    lfm_hash = save[16]
    db_version = save[17]
    view_prefs = save[18]
    window_size = save[19]
    side_panel_size = save[20]
    savetime = save[21]
    vis = save[22]
    playlist_selected = save[23]


except:
    print('No existing save file')

# temporary
if window_size is None:
    window_size = [500, 300]
    side_panel_size = 200

# LOADING CONFIG
player_config = "BASS"


path = install_directory + "/config.txt"
if os.path.isfile(os.path.join(install_directory, "config.txt")):
    with open(path, encoding="utf_8") as f:
        content = f.readlines()
        for p in content:
            if p[0] == " " or p[0] == "#":
                continue

            if 'mediakey' in p:
                mediakeymode = int(p[9:-1])
            if 'seek-pause-lock' in p:
                pause_lock = True
            if 'enable-web' in p:
                enable_web = True
            if 'expose-web' in p:
                expose_web = True
            if 'taskbar-progress' in p:
                taskbar_progress = True
            if 'allow-remote' in p:
                allow_remote = True
            if 'pause-fade-time' in p:
                pause_fade_time = num_from_line(p)
            if 'cross-fade-time' in p:
                cross_fade_time = num_from_line(p)
            if 'draw-border' in p:
                draw_border = True
            if 'scrobble-mark' in p:
                scrobble_mark = True
            if 'custom-highlight-left' in p:
                highlight_left_custom = int(p.split(":")[1])
            if 'custom-highlight-right' in p:
                highlight_right_custom = int(p.split(":")[1])
            if 'opus-bitrate:' in p:
                transcode_bitrate = p[13:-1]
            if 'output-dir:' in p:
                encoder_output = p[11:-1]
                encoder_output = encoder_output.replace('\\', '/')
                if encoder_output[-1] != "/":
                    encoder_output += "/"

                print('Encode output: ' + encoder_output)
            if 'enable-transcode' in p:
                enable_transcode = True
            if 'custom-format:' in p:
                custom_line = p[15:-1]
                custom_pro = custom_line.split(";")

                try:
                    transcode_bitrate = int(transcode_bitrate)
                    if transcode_bitrate < 8:
                        transcode_bitrate = 8
                    elif transcode_bitrate > 510:
                        trancode_bitrate = 510
                except:
                    transcode_bitrate = 48
else:
    enable_transcode = True
    scrobble_mark = True
    print("Warning: Missing config file")

try:
    star_lines = view_prefs['star-lines']
    update_title = view_prefs['update-title']
    split_line = view_prefs['split-line']
    prefer_side = view_prefs['side-panel']
    dim_art = view_prefs['dim-art']
    turbo = view_prefs['level-meter']
    pl_follow = view_prefs['pl-follow']
    scroll_enable = view_prefs['scroll-enable']
    break_enable = view_prefs['break-enable']
    dd_index = view_prefs['dd-index']
    custom_line_mode = view_prefs['custom-line']
    thick_lines = view_prefs['thick-lines']
except:
    print("warning: error loading settings")


# if os.path.isdir("web"):
#     pass
# else:
#     print('Creating web cache folder')
#     os.makedirs("web")


if prefer_side is False:
    side_panel_enable = False


def b_timer():
    global b_start
    global b_end
    b_end = time.time()
    elapsed = b_end - b_start
    b_start = time.time()
    return elapsed


def p_timer():
    global p_start
    global p_end
    p_end = time.time()
    elapsed = p_end - p_start
    p_start = time.time()
    return elapsed


def c_timer():
    global c_start
    global c_end
    c_end = time.time()
    elapsed = c_end - c_start
    c_start = time.time()
    return elapsed


get_len = 0
get_len_filepath = ""


def get_len_backend(filepath):
    global playerCommand
    global playerCommandReady
    global get_len
    global get_len_filepath
    get_len_filepath = filepath
    playerCommand = 'getlen'
    playerCommandReady = True
    while playerCommand != 'got':
        time.sleep(0.05)
    return get_len


def get_display_time(seconds):

    result = divmod(int(seconds), 60)
    if result[0] > 99:
        result = divmod(result[0], 60)
        return str(result[0]) + 'h ' + str(result[1]).zfill(2)
    return str(result[0]).zfill(2) + ":" + str(result[1]).zfill(2)


class PlayerCtl():
    def __init__(self):
        self.track_queue = QUE
        self.queue_step = playing_in_queue
        self.playing_time = 0
        self.playlist_playing = playlist_playing  # track in playlist that is playing
        self.target_open = ""
        self.start_time = 0
        self.bstart_time = 0
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

    def playing_playlist(self):
        return self.multi_playlist[self.active_playlist_playing][2]

    def render_playlist(self):
        global renplay

        if taskbar_progress and system == 'windows':
            global windows_progress
            windows_progress.update(True)
        renplay += 1

    def show_selected(self):

        if playlist_view_length < 1:
            return 0

        global playlist_position
        global playlist_selected
        global shift_selection

        for i in range(len(self.multi_playlist[self.playlist_active][2])):

            if i == playlist_selected:

                if i < playlist_position:
                    playlist_position = i - random.randint(2, int((playlist_view_length / 3) * 2) + int(
                            playlist_view_length / 6))
                elif abs(playlist_position - i) > playlist_view_length:
                    playlist_position = i
                    if i > 6:
                        playlist_position -= 5
                    if i > playlist_view_length * 1 and i + (playlist_view_length * 2) < len(
                            self.multi_playlist[self.playlist_active][2]) and i > 10:
                        playlist_position = i - random.randint(2, int(playlist_view_length / 3) * 2)
                    break

        self.render_playlist()

        return 0


    def show_current(self, select=True, playing=False):


        # Switch to source playlist
        if self.playlist_active != self.active_playlist_playing and (
                self.track_queue[self.queue_step] not in self.multi_playlist[self.playlist_active][2]):
            switch_playlist(self.active_playlist_playing)

        if playlist_view_length < 1:
            return 0

        global playlist_position
        global playlist_selected
        global shift_selection

        for i in range(len(self.multi_playlist[self.playlist_active][2])):
            if len(self.track_queue) > 1 and self.multi_playlist[self.playlist_active][2][i] == self.track_queue[
                    self.queue_step]:

                if select:
                    playlist_selected = i
                if playing:
                    self.playlist_playing = i

                if i == playlist_position - 1 and playlist_position > 1:
                    playlist_position -= 1
                elif playlist_position + playlist_view_length - 2 == i and i < len(
                        self.multi_playlist[self.playlist_active][2]) - 5:
                    playlist_position += 3
                elif i < playlist_position:
                    playlist_position = i - random.randint(2, int((playlist_view_length / 3) * 2) + int(
                            playlist_view_length / 6))
                elif abs(playlist_position - i) > playlist_view_length:
                    playlist_position = i
                    if i > 6:
                        playlist_position -= 5
                    if i > playlist_view_length * 1 and i + (playlist_view_length * 2) < len(
                            self.multi_playlist[self.playlist_active][2]) and i > 10:
                        playlist_position = i - random.randint(2, int(playlist_view_length / 3) * 2)
                    break

            if playlist_position < 0:
                playlist_position = 0
            if select:
                shift_selection = []


        self.render_playlist()
        return 0

    def set_volume(self):

        self.playerCommand = 'volume'
        self.playerCommandReady = True

    def play_target_rr(self):

        self.playing_length = master_library[self.track_queue[self.queue_step]]['length']
        if self.playing_length > 2:
            random_start = random.randrange(1,self.playing_length - 45 if self.playing_length > 50 else self.playing_length)
        else:
            random_start = 0

        self.playing_time = random_start
        self.target_open = master_library[self.track_queue[self.queue_step]]['filepath']
        self.start_time = master_library[self.track_queue[self.queue_step]]['starttime']
        self.jump_time = random_start
        self.playerCommand = 'open'
        self.playerCommandReady = True
        self.playing_state = 1

        self.last_playing_time = random_start

        if update_title:
            update_title_do()

    def play_target(self):

        self.playing_time = 0
        self.target_open = master_library[self.track_queue[self.queue_step]]['filepath']
        self.start_time = master_library[self.track_queue[self.queue_step]]['starttime']
        self.playerCommand = 'open'
        self.playerCommandReady = True
        self.playing_state = 1
        self.playing_length = master_library[self.track_queue[self.queue_step]]['length']
        self.last_playing_time = 0

        if update_title:
            update_title_do()

    def jump(self, index, pl_position=None):

        global playlist_hold
        global update_spec
        update_spec = 0
        self.active_playlist_playing = self.playlist_active
        self.track_queue.append(index)
        self.queue_step = len(self.track_queue) - 1
        playlist_hold = False
        self.play_target()

        if pl_position is not None:
            self.playlist_playing = pl_position

    def back(self):

        global update_spec
        update_spec = 0
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

        self.render_playlist()

    def stop(self):
        self.playerCommand = 'stop'
        self.playerCommandReady = True
        self.playing_time = 0
        self.playing_state = 0
        self.render_playlist()
        global update_spec
        update_spec = 0
        if update_title:
            update_title_do()

    def pause(self):

        if self.playing_state == 1:
            self.playerCommand = 'pause'
            self.playing_state = 2
        elif self.playing_state == 2:
            self.playerCommand = 'pause'
            self.playing_state = 1
        self.playerCommandReady = True

        self.render_playlist()

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
                self.track_queue.append(self.multi_playlist[self.active_playlist_playing][2])
                self.queue_step = 0
                self.playlist_playing = 0
                self.active_playlist_playing = 0
                self.play_target()

            # If the queue is not empty, play?
            elif len(self.track_queue) > 0:
                self.play_target()

        self.render_playlist()

    def advance(self, rr=False):

        pctl.playing_length = 100
        pctl.playing_time = 0
        global update_spec


        update_spec = 0

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
            if album_mode:
                goto_album(self.playlist_playing)

        # If not random, Step down 1 on the playlist
        elif self.random_mode is False and len(self.playing_playlist()) > 0:

            # Stop at end of playlist
            if self.playlist_playing == len(self.playing_playlist()) - 1:
                self.playing_state = 0
                self.playerCommand = 'stop'
                self.playerCommandReady = True
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
                self.play_target()

        else:
            print("ADVANCE: NO CASE!")

        if self.playlist_active == self.active_playlist_playing:
            self.show_current(playing=True)

        if album_mode:
            goto_album(self.playlist_playing)


        self.render_playlist()


pctl = PlayerCtl()


def get_colour_from_line(cline):
    colour = ["", "", "", ""]

    mode = 0

    for i in cline:

        if i.isdigit():
            colour[mode] += i
        elif i == ',':
            mode += 1

    for b in range(len(colour)):
        if colour[b] == "":
            colour[b] = "255"
        colour[b] = int(colour[b])

    return colour


def checkEqual(lst):
    return not lst or lst.count(lst[0]) == len(lst)


def alpha_mod(colour, alpha):
    return [colour[0], colour[1], colour[2], alpha]


def rm_16(line):
    if "ÿ þ" in line:
        for c in line:
            line = line[1:]
            if c == 'þ':
                break

        line = line[::2]
    return line


# Last.FM -----------------------------------------------------------------

def update_title_do():
    global pctl
    if pctl.playing_state > 0:
        if len(pctl.track_queue) > 0:
            line = master_library[pctl.track_queue[pctl.queue_step]]['artist'] + " - " + \
                   master_library[pctl.track_queue[pctl.queue_step]]['title']
            line = line.encode('utf-8')
            SDL_SetWindowTitle(t_window, line)
    else:
        line = "Tauon Music Box"
        line = line.encode('utf-8')
        SDL_SetWindowTitle(t_window, line)


class LastFMapi:
    API_SECRET = "18c471e5475e7e877b126843d447e"
    connected = False
    hold = False
    API_KEY = "0eea8ea966ab2ca395731e2c3c22e81e"
    API_SECRET += "855"

    network = None

    def connect(self):

        global lfm_user_box
        global lfm_password
        global lfm_username
        global lfm_hash
        global lfm_pass_box
        global message_box
        global message_box_text

        if self.connected is True:
            message_box = True
            message_box_text = "Already Connected"
            return 0

        if lfm_username == "":
            lfm_user_box = True
            return False

        if lfm_hash == "":
            if lfm_password == "":
                lfm_pass_box = True
                return False
            else:
                lfm_hash = pylast.md5(lfm_password)

        print('Attempting to connect to last.fm network')

        try:
            self.network = pylast.LastFMNetwork(api_key=self.API_KEY, api_secret=
            self.API_SECRET, username=lfm_username, password_hash=lfm_hash)

            self.connected = True
            message_box = True
            message_box_text = "Connected"
            print('Connection appears successful')
        except Exception as e:
            message_box = True
            message_box_text = "Error: " + str(e)
            print(e)

    def toggle(self):
        if self.connected:
            self.hold ^= True
        else:
            self.connect()

    def scrobble(self, title, artist, album):
        if self.hold:
            return 0

        global message_box
        global message_box_text
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
                time.sleep(3)

                try:
                    self.network.scrobble(artist=artist, title=title, timestamp=timestamp)
                    print('Scrobbled')
                    return 0
                except:
                    pass

            message_box = True
            message_box_text = "Error: " + str(e)
            print(e)

    def update(self, title, artist, album):
        if self.hold:
            return 0
        global message_box
        global message_box_text
        global b_time
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
            message_box = True
            message_box_text = "Error: " + str(e)
            b_time -= 5000
            return 1


def get_backend_time(path):
    global pctl
    global pctl
    global time_to_get

    time_to_get = path

    pctl.playerCommand = 'time'
    pctl.playerCommandReady = True

    while pctl.playerCommand != 'done':
        time.sleep(0.005)

    return time_to_get


lastfm = LastFMapi()




# PLAYER---------------------------------------------------------------
level_time = Timer2()


def player():
    global default_player
    global loaded_player
    global pctl
    global volume
    global pause_fade_time
    global change_volume_fade_time
    global new_time
    global turbonext
    global level
    global turbo
    global UPDATE_RENDER
    global broadcast
    global broadcast_time
    global URL
    global tag_meta
    global broadcast_line
    global url_record
    global record_split
    global record_path
    global b_time
    global broadcast_position
    global renplay
    global reset_playing
    global a_time
    global a_index
    global a_sc
    global a_pt
    global encpause
    global join_broadcast
    global total_playtime
    global time_to_get
    global level_peak
    global UPDATE_LEVEL
    global level_time
    global lowered

    fileout = ""
    thisfile = ""
    fileline = "output"

    current_volume = volume / 100

    if default_player == 'BASS':
        if system == 'windows':
            bass_module = ctypes.WinDLL('bass')
            enc_module = ctypes.WinDLL('bassenc')
            mix_module = ctypes.WinDLL('bassmix')
            function_type = ctypes.WINFUNCTYPE
        else:
            bass_module = ctypes.CDLL(install_directory + '/lib/libbass.so', mode=ctypes.RTLD_GLOBAL)
            enc_module = ctypes.CDLL(install_directory + '/lib/libbassenc.so', mode=ctypes.RTLD_GLOBAL)
            mix_module = ctypes.CDLL(install_directory + '/lib/libbassmix.so', mode=ctypes.RTLD_GLOBAL)
            function_type = ctypes.CFUNCTYPE

        loaded_player = 'BASS'

        BASS_Init = function_type(ctypes.c_bool, ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
                                  ctypes.c_void_p)(('BASS_Init', bass_module))
        BASS_StreamCreateFile = function_type(ctypes.c_ulong, ctypes.c_bool, ctypes.c_void_p, ctypes.c_int64,
                                              ctypes.c_int64, ctypes.c_ulong)(('BASS_StreamCreateFile', bass_module))
        BASS_ChannelPlay = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_bool)(
                ('BASS_ChannelPlay', bass_module))
        BASS_ChannelGetData = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong)(
                ('BASS_ChannelGetData', bass_module))
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

        BASS_Mixer_StreamCreate = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong)(
                ('BASS_Mixer_StreamCreate', mix_module))
        BASS_Mixer_StreamAddChannel = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong)(
                ('BASS_Mixer_StreamAddChannel', mix_module))
        BASS_Mixer_ChannelRemove = function_type(ctypes.c_bool, ctypes.c_ulong)(
                ('BASS_Mixer_ChannelRemove', mix_module))
        BASS_Mixer_ChannelSetPosition = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_int64, ctypes.c_ulong)(
                ('BASS_Mixer_ChannelSetPosition', mix_module))

        DownloadProc = function_type(c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p)

        # BASS_StreamCreateURL = function_type(ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_ulong, DownloadProc, ctypes.c_void_p)(('BASS_StreamCreateURL', bass_module))
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

        #
        # def py_cmp_func(handle, channel, buffer, length):
        #     return 0
        #
        # cmp_func = EncodeProc(py_cmp_func)

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

        if system == 'windows':
            bass_plugin1 = BASS_PluginLoad(b'bassopus.dll', 0)
            bass_plugin2 = BASS_PluginLoad(b'bassflac.dll', 0)
            bass_plugin3 = BASS_PluginLoad(b'bass_ape.dll', 0)
            bass_plugin4 = BASS_PluginLoad(b'bassenc.dll', 0)
            bass_plugin5 = BASS_PluginLoad(b'bass_tta.dll', 0)
            bass_plugin6 = BASS_PluginLoad(b'bassmix.dll', 0)
        else:
            b = install_directory.encode('utf-8')
            bass_plugin1 = BASS_PluginLoad(b + b'/lib/libbassopus.so', 0)
            bass_plugin2 = BASS_PluginLoad(b + b'/lib/libbassflac.so', 0)
            bass_plugin3 = BASS_PluginLoad(b + b'/lib/libbass_ape.so', 0)
            bass_plugin4 = BASS_PluginLoad(b + b'/lib/libbass_aac.so', 0)
            bass_plugin5 = BASS_PluginLoad(b + b'/lib/libbassmix.so', 0)

        BassInitSuccess = BASS_Init(-1, 44100, 0, 0, 0)
        if BassInitSuccess == True:
            print("Bass library initialised")

        current_channel = 0
        player1_status = 'stopped'
        player2_status = 'stopped'

        last_level = [0, 0]
        time_passed = 0
        phase = 0

        global vis
        global spec
        global update_spec
        global sspec

        while True:
            if turbo is False:
                time.sleep(0.04)
            else:
                turbonext += 1

                if vis == 2:
                    time.sleep(0.018)
                else:
                    time.sleep(0.02)

                if turbonext < 6 and pctl.playerCommandReady is not True:

                    if player1_status != 'playing' and player2_status != 'playing':
                        level = 0
                        continue

                    # -----------
                    if vis == 2:
                        if lowered:
                            continue

                        sp_handle = 0
                        if player1_status == 'playing':
                            sp_handle = handle1
                        elif player2_status == 'playing':
                            sp_handle = handle2
                        x = (ctypes.c_float * 512)()
                        # print(x)
                        ctypes.cast(x, ctypes.POINTER(ctypes.c_float))

                        BASS_ChannelGetData(sp_handle, x, 0x80000002)  # 0x80000000)
                        # BASS_ChannelGetData(sp_handle,x,0x80000002) # 0x80000000)

                        # BASS_DATA_FFT256 = 0x80000000# -2147483648# 256 sample FFT
                        # BASS_DATA_FFT512 = 0x80000001# -2147483647# 512 FFT
                        # BASS_DATA_FFT1024 = 0x80000002# -2147483646# 1024 FFT
                        # BASS_DATA_FFT2048 = 0x80000003# -2147483645# 2048 FFT
                        # BASS_DATA_FFT4096 = 0x80000004# -2147483644# 4096 FFT
                        # BASS_DATA_FFT8192 = 0x80000005# -2147483643# 8192 FFT
                        # BASS_DATA_FFT16384 = 0x80000006# 16384 FFT

                        pspec = []
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
                            pspec.append(int(outp * 45))
                            i += 1

                        spec = pspec
                        # print(spec)
                        if pctl.playing_time > 0.5 and pctl.playing_state == 1:
                            update_spec = 1
                        # if pctl.playerCommand in ['open', 'stop']:
                        #     update_spec = 0
                        UPDATE_LEVEL = True
                        continue

                    # -----------------------------------

                    if vis == 1:

                        if player1_status == 'playing':
                            level = BASS_ChannelGetLevel(handle1)
                        elif player2_status == 'playing':
                            level = BASS_ChannelGetLevel(handle2)

                        ppp = (bin(level)[2:].zfill(32))
                        ppp1 = ppp[:16]
                        ppp2 = ppp[16:]
                        ppp1 = int(ppp1, 2)
                        ppp2 = int(ppp2, 2)
                        ppp1 = (ppp1 / 32768) * 11.1
                        ppp2 = (ppp2 / 32768) * 11.1

                        time_passed += level_time.get()
                        if time_passed > 1000:
                            time_passed = 0
                        while time_passed > 19:
                            level_peak[1] -= 0.4
                            if level_peak[1] < 0:
                                level_peak[1] = 0
                            level_peak[0] -= 0.4
                            if level_peak[0] < 0:
                                level_peak[0] = 0
                            time_passed -= 20

                        if ppp1 > level_peak[0]:
                            level_peak[0] = ppp1
                        if ppp2 > level_peak[1]:
                            level_peak[1] = ppp2

                        if int(level_peak[0]) != int(last_level[0]) or int(level_peak[1]) != int(last_level[1]):
                            UPDATE_LEVEL = True
                        UPDATE_LEVEL = True
                        last_level = copy.deepcopy(level_peak)

                        continue

                else:
                    turbonext = 0
                    if pctl.playerCommand == 'open':
                        # UPDATE_RENDER += 1
                        level_peak = [0, 0]

            if pctl.playing_state == 3 and player1_status == 'playing':

                # print(BASS_ChannelGetTags(handle1,4 ))
                tag_meta = BASS_ChannelGetTags(handle1, 5)
                if tag_meta != None:
                    tag_meta = tag_meta.decode('utf-8')[13:-2]
                else:
                    tag_meta = BASS_ChannelGetTags(handle1, 2)
                    if tag_meta != None:
                        tag_meta = tag_meta.decode('utf-8')[6:]
                    else:
                        tag_meta = ""

                        # time.sleep(0.5)

            if broadcast and encpause == 0:
                broadcast_time += b_timer()

            if player1_status == 'playing' or player2_status == 'playing':

                add_time = p_timer()
                pctl.playing_time += add_time

                if pctl.playing_state == 1:

                    a_time += add_time
                    total_playtime += add_time

                    if a_index != pctl.track_queue[pctl.queue_step]:
                        a_time = 0
                        b_time = 0
                        a_index = pctl.track_queue[pctl.queue_step]
                        a_pt = False
                        a_sc = False
                    if pctl.playing_time == 0 and a_sc is True:
                        print("Reset scrobble timer")
                        a_time = 0
                        b_time = 0
                        a_pt = False
                        a_sc = False
                    if a_time > 10 and a_pt is False and master_library[a_index]['length'] > 30:
                        a_pt = True

                        if lastfm.connected:
                            mini_t = threading.Thread(target=lastfm.update, args=(master_library[a_index]['title'],
                                                                                  master_library[a_index]['artist'],
                                                                                  master_library[a_index]['album']))
                            mini_t.daemon = True
                            mini_t.start()

                    if a_time > 10 and a_pt:
                        b_time += add_time
                        if b_time > 20:
                            b_time = 0
                            if lastfm.connected:
                                mini_t = threading.Thread(target=lastfm.update, args=(master_library[a_index]['title'],
                                                                                      master_library[a_index]['artist'],
                                                                                      master_library[a_index]['album']))
                                mini_t.daemon = True
                                mini_t.start()


                    if master_library[a_index]['length'] > 30 and a_time > master_library[a_index][
                        'length'] * 0.50 and a_sc is False:
                        a_sc = True
                        if lastfm.connected:
                            renplay += 1
                            print(
                                    "Scrobble " + master_library[a_index]['title'] + " - " + master_library[a_index][
                                        'artist'])

                            mini_t = threading.Thread(target=lastfm.scrobble, args=(master_library[a_index]['title'],
                                                                                  master_library[a_index]['artist'],
                                                                                  master_library[a_index]['album']))
                            mini_t.daemon = True
                            mini_t.start()

                    if a_sc is False and master_library[a_index]['length'] > 30 and a_time > 240:
                        if lastfm.connected:
                            renplay += 1
                            print(
                                    "Scrobble " + master_library[a_index]['title'] + " - " + master_library[a_index][
                                        'artist'])

                            mini_t = threading.Thread(target=lastfm.scrobble, args=(master_library[a_index]['title'],
                                                                                  master_library[a_index]['artist'],
                                                                                  master_library[a_index]['album']))
                            mini_t.daemon = True
                            mini_t.start()
                        a_sc = True

                if pctl.playing_state == 1 and len(pctl.track_queue) > 0:
                    index = pctl.track_queue[pctl.queue_step]
                    key = master_library[index]['title'] + master_library[index]['filename']
                    if key in star_library:
                        if 3 > add_time > 0:
                            star_library[key] += add_time
                    else:
                        star_library[key] = 0

            if pctl.playerCommandReady:
                pctl.playerCommandReady = False

                if pctl.playerCommand == 'time':

                    pctl.target_open = time_to_get
                    if system != 'windows':
                        pctl.target_open = pctl.target_open.encode('utf-8')
                        flag = 0
                    else:
                        flag = 0x80000000

                    print(pctl.target_open)
                    handle9 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)
                    blen = BASS_ChannelGetLength(handle9, 0)
                    tlen = BASS_ChannelBytes2Seconds(handle9, blen)
                    time_to_get = tlen
                    BASS_StreamFree(handle9)
                    pctl.playerCommand = 'done'

                if pctl.playerCommand == "url":
                    if player1_status != 'stopped':
                        BASS_ChannelStop(handle1)
                        player1_status = 'stopped'
                        BASS_StreamFree(handle1)
                    if player2_status != 'stopped':
                        BASS_ChannelStop(handle2)
                        player2_status = 'stopped'
                        BASS_StreamFree(handle2)

                    fileline = str(datetime.datetime.now()) + ".ogg"

                    handle1 = BASS_StreamCreateURL(URL, 0, 0, down_func, 0)
                    # print(BASS_ErrorGetCode())
                    BASS_ChannelSetAttribute(handle1, 2, current_volume)
                    channel1 = BASS_ChannelPlay(handle1, True)
                    player1_status = 'playing'
                    pctl.playing_time = 0

                if pctl.playerCommand == 'encnext':
                    print("Next Enc Rec")

                    if system != 'windows':
                        pctl.target_open = pctl.target_open.encode('utf-8')
                        flag = 0
                    else:
                        flag = 0x80000000

                    # oldhandle = handle3
                    flag = flag | 0x200000

                    BASS_Mixer_ChannelRemove(handle3)
                    BASS_StreamFree(handle3)

                    handle3 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)

                    if pctl.bstart_time > 0:
                        bytes_position = BASS_ChannelSeconds2Bytes(handle3, pctl.bstart_time)
                        BASS_ChannelSetPosition(handle3, bytes_position, 0)

                    BASS_Mixer_StreamAddChannel(mhandle, handle3, 0)

                    # channel1 = BASS_ChannelPlay(handle3, True)
                    channel1 = BASS_ChannelPlay(mhandle, True)


                    encerror = BASS_ErrorGetCode()
                    print(encerror)
                    print(broadcast_line)
                    line = broadcast_line.encode('utf-8')
                    BASS_Encode_CastSetTitle(encoder, line, 0)
                    print(BASS_ErrorGetCode())
                    if encerror != 0:
                        broadcast = False
                        encstop = BASS_Encode_Stop(encoder)
                        channel3 = BASS_ChannelStop(handle3)
                        BASS_StreamFree(handle3)
                        # BASS_StreamFree(oldhandle)

                if pctl.playerCommand == 'encpause' and broadcast:

                    if encpause == 0:
                        BASS_ChannelPause(mhandle)
                        encpause = 1
                    else:
                        BASS_ChannelPlay(mhandle, True)
                        encpause = 0

                if pctl.playerCommand == "encstop":
                    encstop = BASS_Encode_Stop(encoder)
                    channel3 = BASS_ChannelStop(handle3)
                    BASS_StreamFree(handle3)
                    broadcast = False

                if pctl.playerCommand == "encstart":

                    mount = ""
                    ice_pass = ""
                    codec = ""
                    bitrate = ""

                    path = install_directory + "/config.txt"
                    with open(path, encoding="utf_8") as f:
                        content = f.readlines()
                        for p in content:
                            if p[0] == " " or p[0] == "#":
                                continue
                            if 'icecast-mount:' in p:
                                mount = p[14:-1]

                            elif 'icecast-pass:' in p:
                                ice_pass = p[13:-1]
                            elif 'icecast-codec:' in p:
                                codec = p[14:-1]
                            elif 'icecase-bitrate:' in p:
                                bitrate = p[16:-1]

                        print(mount)
                        print(ice_pass)
                        print(codec)
                        print(bitrate)

                    broadcast = True
                    print("starting encoder")

                    if system != 'windows':
                        pctl.target_open = pctl.target_open.encode('utf-8')
                        flag = 0
                    else:
                        flag = 0x80000000

                    broadcast_time = 0

                    b_timer()
                    flag = flag | 0x200000
                    # print(flag)

                    handle3 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)

                    mhandle = BASS_Mixer_StreamCreate(44100, 2, 0)

                    BASS_Mixer_StreamAddChannel(mhandle, handle3, 0)

                    channel1 = BASS_ChannelPlay(mhandle, True)

                    BASS_ChannelSetAttribute(mhandle, 2, 0)

                    print(BASS_ErrorGetCode())

                    # encoder = BASS_Encode_Start(handle3, <lame.exe> --alt-preset standard - c:\output.mp3', 0, cmp_func, 0)
                    # encoder = BASS_Encode_Start(handle3, <directory of encoder> -r -s 44100 -b 128 -", 1, 0, 0)

                    if system != 'windows':
                        encbin = ""
                    else:
                        encbin = '.exe'

                    if codec == "MP3":
                        line = install_directory + "/encoder/lame" + encbin + " -r -s 44100 -b " + bitrate + " -"
                        line = line.encode('utf-8')

                        encoder = BASS_Encode_Start(mhandle, line, 1, 0, 0)

                        line = "source:" + ice_pass
                        line = line.encode('utf-8')

                        BASS_Encode_CastInit(encoder, mount.encode('utf-8'), line, b"audio/mpeg", b"name", b"url",
                                             b"genre", b"", b"", int(bitrate), False)

                    elif codec == "OGG":
                        line = install_directory + "/encoder/oggenc2" + encbin + " -r -b " + bitrate + " -"
                        line = line.encode('utf-8')
                        # print(line)

                        encoder = BASS_Encode_Start(mhandle, line, 1, 0, 0)

                        line = "source:" + ice_pass
                        line = line.encode('utf-8')

                        BASS_Encode_CastInit(encoder, mount.encode('utf-8'), line, b"application/ogg", b"name", b"url",
                                             b"genre", b"", b"", int(bitrate), False)

                    channel1 = BASS_ChannelPlay(mhandle, True)

                    # Trying to send the stream title here causes the stream to fail for some reason
                    # line2 = broadcast_line.encode('utf-8')
                    # BASS_Encode_CastSetTitle(encoder, line2,0)

                    print(BASS_ErrorGetCode())

                # OPEN COMMAND
                if pctl.playerCommand == 'open' and pctl.target_open != '':

                    pctl.playerCommand = ""

                    if os.path.isfile(master_library[pctl.track_queue[pctl.queue_step]]['filepath']):
                        master_library[pctl.track_queue[pctl.queue_step]]['found'] = True
                    else:
                        master_library[pctl.track_queue[pctl.queue_step]]['found'] = False
                        renplay += 1
                        UPDATE_RENDER += 1
                        print("Missing File")
                        pctl.playerCommandReady = False
                        pctl.playing_state = 0
                        pctl.advance()
                        continue

                    if join_broadcast and broadcast:

                        if system != 'windows':
                            pctl.target_open = pctl.target_open.encode('utf-8')
                            flag = 0
                        else:
                            flag = 0x80000000
                        flag = flag | 0x200000

                        BASS_Mixer_ChannelRemove(handle3)
                        BASS_StreamFree(handle3)
                        handle3 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)

                        if pctl.bstart_time > 0:
                            bytes_position = BASS_ChannelSeconds2Bytes(handle3, pctl.bstart_time)
                            BASS_ChannelSetPosition(handle3, bytes_position, 0)

                        BASS_Mixer_StreamAddChannel(mhandle, handle3, 0)
                        channel1 = BASS_ChannelPlay(mhandle, True)

                    p_timer()
                    # print(pctl.target_open)
                    if system != 'windows':
                        pctl.target_open = pctl.target_open.encode('utf-8')
                        flag = 0
                    else:
                        flag = 0x80000000

                    # BASS_ASYNCFILE = 0x40000000
                    flag = flag | 0x40000000

                    if player1_status == 'stopped' and player2_status == 'stopped':
                        # print(BASS_ErrorGetCode())

                        handle1 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)
                        # print(BASS_ErrorGetCode())
                        channel1 = BASS_ChannelPlay(handle1, True)

                        # if broadcast:
                        #     BASS_Encode_SetChannel(encoder, handle1)

                        # print(BASS_ErrorGetCode())
                        BASS_ChannelSetAttribute(handle1, 2, current_volume)
                        # print(BASS_ErrorGetCode())
                        player1_status = 'playing'
                    elif player1_status != 'stopped' and player2_status == 'stopped':
                        player1_status = 'stopping'
                        BASS_ChannelSlideAttribute(handle1, 2, 0, cross_fade_time)

                        handle2 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)
                        channel2 = BASS_ChannelPlay(handle2, True)

                        BASS_ChannelSetAttribute(handle2, 2, 0)
                        BASS_ChannelSlideAttribute(handle2, 2, current_volume, cross_fade_time)
                        player2_status = 'playing'
                    elif player2_status != 'stopped' and player1_status == 'stopped':
                        player2_status = 'stopping'
                        BASS_ChannelSlideAttribute(handle2, 2, 0, cross_fade_time)

                        handle1 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)
                        BASS_ChannelSetAttribute(handle1, 2, 0)
                        channel1 = BASS_ChannelPlay(handle1, True)

                        BASS_ChannelSlideAttribute(handle1, 2, current_volume, cross_fade_time)
                        player1_status = 'playing'

                    else:
                        print('no case')

                    if master_library[pctl.track_queue[pctl.queue_step]]['length'] < 1:

                        if player1_status == 'playing':
                            blen = BASS_ChannelGetLength(handle1, 0)
                            tlen = BASS_ChannelBytes2Seconds(handle1, blen)
                            master_library[pctl.track_queue[pctl.queue_step]]['length'] = tlen
                            pctl.playing_length = tlen
                        elif player2_status == 'playing':
                            blen = BASS_ChannelGetLength(handle2, 0)
                            tlen = BASS_ChannelBytes2Seconds(handle2, blen)
                            master_library[pctl.track_queue[pctl.queue_step]]['length'] = tlen
                            pctl.playing_length = tlen
                    if pctl.start_time > 0 or pctl.jump_time > 0:
                        if player1_status == 'playing':
                            bytes_position = BASS_ChannelSeconds2Bytes(handle1, pctl.start_time + pctl.jump_time)
                            BASS_ChannelSetPosition(handle1, bytes_position, 0)
                        elif player2_status == 'playing':
                            bytes_position = BASS_ChannelSeconds2Bytes(handle2, pctl.start_time + pctl.jump_time)
                            BASS_ChannelSetPosition(handle2, bytes_position, 0)

                    # print(BASS_ErrorGetCode())
                    #pctl.playing_time = 0
                    pctl.last_playing_time = 0
                    pctl.jump_time = 0
                    p_timer()

                # PAUSE COMMAND
                elif pctl.playerCommand == 'pause':
                    p_timer()

                    if join_broadcast and broadcast:
                        if player1_status == 'playing' or player2_status == 'playing':
                            BASS_ChannelPause(mhandle)
                        else:
                            BASS_ChannelPlay(mhandle, True)

                    if player1_status == 'playing':
                        player1_status = 'paused'
                        BASS_ChannelSlideAttribute(handle1, 2, 0, pause_fade_time)
                        time.sleep(pause_fade_time / 1000 / 0.7)
                        channel1 = BASS_ChannelPause(handle1)
                    elif player1_status == 'paused':
                        player1_status = 'playing'
                        channel1 = BASS_ChannelPlay(handle1, False)
                        BASS_ChannelSlideAttribute(handle1, 2, current_volume, pause_fade_time)
                    if player2_status == 'playing':
                        player2_status = 'paused'
                        BASS_ChannelSlideAttribute(handle2, 2, 0, pause_fade_time)
                        time.sleep(pause_fade_time / 1000 / 0.7)
                        channel2 = BASS_ChannelPause(handle2)
                    elif player2_status == 'paused':
                        player2_status = 'playing'
                        channel2 = BASS_ChannelPlay(handle2, False)
                        BASS_ChannelSlideAttribute(handle2, 2, current_volume, pause_fade_time)

                # UNLOAD PLAYER COMMAND
                elif pctl.playerCommand == 'unload':
                    BASS_Free()
                    print('BASS Unloaded')
                    break

                # CHANGE VOLUME COMMAND
                elif pctl.playerCommand == 'volume':
                    current_volume = volume / 100
                    if player1_status == 'playing':
                        BASS_ChannelSlideAttribute(handle1, 2, current_volume, change_volume_fade_time)
                    if player2_status == 'playing':
                        BASS_ChannelSlideAttribute(handle2, 2, current_volume, change_volume_fade_time)
                # STOP COMMAND
                elif pctl.playerCommand == 'stop':
                    if player1_status != 'stopped':
                        player1_status = 'stopped'
                        BASS_ChannelSlideAttribute(handle1, 2, 0, pause_fade_time)
                        time.sleep(pause_fade_time / 1000)
                        channel1 = BASS_ChannelStop(handle1)
                        BASS_StreamFree(handle1)
                    if player2_status != 'stopped':
                        player2_status = 'stopped'
                        BASS_ChannelSlideAttribute(handle2, 2, 0, pause_fade_time)
                        time.sleep(pause_fade_time / 1000)
                        channel2 = BASS_ChannelStop(handle2)
                        BASS_StreamFree(handle2)
                # SEEK COMMAND
                elif pctl.playerCommand == 'seek':

                    if player1_status == 'playing' or player1_status == 'paused':

                        bytes_position = BASS_ChannelSeconds2Bytes(handle1, new_time + pctl.start_time)
                        BASS_ChannelSetPosition(handle1, bytes_position, 0)
                        BASS_ChannelPlay(handle1, False)
                    elif player2_status == 'playing' or player2_status == 'paused':

                        bytes_position = BASS_ChannelSeconds2Bytes(handle2, new_time + pctl.start_time)
                        BASS_ChannelSetPosition(handle2, bytes_position, 0)
                        BASS_ChannelPlay(handle2, False)

                    pctl.playerCommand = ''

                    if join_broadcast and broadcast:
                        print('b seek')
                        BASS_Mixer_ChannelSetPosition(handle3, bytes_position, 0)
                        BASS_ChannelPlay(mhandle, False)

                new_time = 0
                bytes_position = 0
                if player1_status == 'stopping':
                    time.sleep(cross_fade_time / 1000)
                    BASS_StreamFree(handle1)
                    player1_status = 'stopped'
                    # print('player1 stopped')
                    channel1 = BASS_ChannelStop(handle1)
                if player2_status == 'stopping':
                    time.sleep(cross_fade_time / 1000)
                    BASS_StreamFree(handle2)
                    player2_status = 'stopped'
                    channel2 = BASS_ChannelStop(handle2)

    pctl.playerCommand = 'done'
    # -------------------------------------------------------------------


playerThread = threading.Thread(target=player)
playerThread.daemon = True
playerThread.start()


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
            time.sleep(1)

    listen()


if system == 'windows':
    if mediakeymode != 0:
        print('Starting hook thread for Windows')
        keyboardHookThread = threading.Thread(target=keyboard_hook)
        keyboardHookThread.daemon = True
        keyboardHookThread.start()
else:
    if mediakeymode == 1:
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

            # set up the glib main loop.
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
            bus_object = bus.get_object('org.gnome.SettingsDaemon',
                                        '/org/gnome/SettingsDaemon/MediaKeys')

            # this is what gives us the multi media keys.
            dbus_interface = 'org.gnome.SettingsDaemon.MediaKeys'
            bus_object.GrabMediaPlayerKeys("MyMultimediaThingy", 0,
                                           dbus_interface=dbus_interface)

            # connect_to_signal registers our callback function.
            bus_object.connect_to_signal('MediaPlayerKeyPressed',
                                         on_mediakey)

            # and we start the main loop.
            mainloop = GObject.MainLoop()
            mainloop.run()


        gnomeThread = threading.Thread(target=gnome)
        gnomeThread.daemon = True
        gnomeThread.start()

    elif mediakeymode == 2:
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


        hookman = pyxhook.HookManager()
        hookman.KeyDown = kbevent
        hookman.HookKeyboard()
        hookman.start()


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
                artist = master_library[index]['artist']
                pt = 0
                key = master_library[index]['title'] + master_library[index]['filename']
                if artist == "":
                    artist = "<Artist Unspecified>"
                if key in star_library:
                    pt = int(star_library[key])

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
                genre_r = master_library[index]['genre']
                gn = [master_library[index]['genre']]
                pt = 0

                key = master_library[index]['title'] + master_library[index]['filename']
                if key in star_library:
                    pt = int(star_library[key])

                if ',' in genre_r:
                    [x.strip() for x in genre_r.split(',')]
                elif '/' in genre_r:
                    [x.strip() for x in genre_r.split('/')]
                elif ';' in genre_r:
                    [x.strip() for x in genre_r.split(';')]
                elif '\\' in genre_r:
                    [x.strip() for x in genre_r.split(';')]
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

            albums = {}

            for index in pctl.multi_playlist[playlist][2]:
                album = master_library[index]['album']
                pt = 0
                key = master_library[index]['title'] + master_library[index]['filename']
                if album == "":
                    album = "<Album Unspecified>"

                if key in star_library:
                    pt = int(star_library[key])

                if pt < 30:
                    continue

                if album in albums:
                    albums[album] += pt
                else:
                    albums[album] = pt

            art_list = albums.items()

            sorted_list = sorted(art_list, key=lambda x: x[1], reverse=True)

            # for item in sorted_list[:50]:
            #     print(item[0])
            self.album_list = copy.deepcopy(sorted_list)


stats_gen = GStats()



# -------------------------------------------------------------------------------------------
# initiate SDL2 ------------------------------------------------------------------------------

SDL_Init(SDL_INIT_VIDEO)
TTF_Init()
window_title = "Tauon Music Box"
window_title = window_title.encode('utf-8')


def load_font(name, size):
    b = install_directory
    b = b.encode('utf-8')
    c = name.encode('utf-8')
    fontpath = b + b'/gui/' + c

    return TTF_OpenFont(fontpath, size)


alt_font = 'DroidSans.ttf'

font1 = load_font(main_font, 16)
font1b = load_font(alt_font, 16)


font2 = load_font(main_font, 12)
font2b = load_font(alt_font, 12)

font3 = load_font(main_font, 10)
font3b = load_font(alt_font, 10)

font4 = load_font(main_font, 11)
font4b = load_font(alt_font, 11)

font6 = load_font(main_font, 13)
font6b = load_font(alt_font, 13)

font7 = load_font(main_font, 14)
font7b = load_font(alt_font, 14)

font_dict = {}
font_dict[13] = (font6, font6b)
font_dict[11] = (font4, font4b)
font_dict[10] = (font3, font3b)
font_dict[12] = (font2, font2b)
font_dict[16] = (font1, font1b)
font_dict[14] = (font7, font7b)

flags = SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE

if draw_border:
    flags = SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE | SDL_WINDOW_BORDERLESS

t_window = SDL_CreateWindow(window_title,
                            SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                            window_size[0], window_size[1],
                            flags)
# print(SDL_GetError())

SDL_SetWindowMinimumSize(t_window,450,175)
# get window surface and set up renderer
renderer = SDL_CreateRenderer(t_window, 0, SDL_RENDERER_ACCELERATED)

window_surface = SDL_GetWindowSurface(t_window)

SDL_SetRenderDrawBlendMode(renderer, SDL_BLENDMODE_BLEND)

display_index = SDL_GetWindowDisplayIndex(t_window)
display_bounds = SDL_Rect(0, 0)
SDL_GetDisplayBounds(display_index, display_bounds)

icon = IMG_Load(b_active_directroy + b"/gui/icon.png")

SDL_SetWindowIcon(t_window, icon)

# SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY,b"2")


ttext = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_UNKNOWN, SDL_TEXTUREACCESS_TARGET, window_size[0], window_size[1])
SDL_SetRenderTarget(renderer, ttext)
# print(SDL_GetError())
SDL_SetRenderTarget(renderer, None)

abc = SDL_Rect(0, 0, window_size[0], window_size[1])
SDL_RenderCopy(renderer, ttext, None, abc)
renplay = 2

SDL_SetRenderDrawColor(renderer, background[0], background[1], background[2], background[3])
SDL_RenderClear(renderer)
SDL_RenderPresent(renderer)

fontb1 = load_font('NotoSansCJKjp-Bold.ttf', 12)

if system != 'windows':

    def hit_callback(win,point,data):


        if point.contents.y < 0 and point.contents.x > window_size[0]:
            return SDL_HITTEST_RESIZE_TOPRIGHT

        elif point.contents.y < 0 and point.contents.x < 1:
            return SDL_HITTEST_RESIZE_TOPLEFT

        elif point.contents.y < 0:
            return SDL_HITTEST_RESIZE_TOP

        elif point.contents.y < 30 and m_l < point.contents.x < window_size[0] - 90:
            return SDL_HITTEST_DRAGGABLE
        elif point.contents.x > window_size[0] - 40 and point.contents.y > window_size[1] - 30:
            return SDL_HITTEST_RESIZE_BOTTOMRIGHT
        elif point.contents.x < 5 and point.contents.y > window_size[1] - 5:
            return SDL_HITTEST_RESIZE_BOTTOMLEFT
        elif point.contents.y > window_size[1] - 5:
            return SDL_HITTEST_RESIZE_BOTTOM

        elif point.contents.x > window_size[0] - 1:
            return SDL_HITTEST_RESIZE_RIGHT
        elif point.contents.x <  5:
            return SDL_HITTEST_RESIZE_LEFT

        else:
            return SDL_HITTEST_NORMAL

    c_hit_callback = SDL_HitTest(hit_callback)
    SDL_SetWindowHitTest(t_window, c_hit_callback, 0)


if system == 'windows' and taskbar_progress:

    class WinTask():
        def __init__(self, ):
            self.start = time.time()
            self.updated_state = 0
            global t_window
            sss = SDL_SysWMinfo()
            SDL_GetWindowWMInfo(t_window, sss)
            self.window_id = sss.info.win.window
            import comtypes.client as cc
            cc.GetModule("TaskbarLib.tlb")
            import comtypes.gen.TaskbarLib as tbl
            self.taskbar = cc.CreateObject(
                    "{56FDF344-FD6D-11d0-958A-006097C9A090}",
                    interface=tbl.ITaskbarList3)
            self.taskbar.HrInit()

        def get(self):
            self.end = time.time()
            self.secs = self.end - self.start
            self.msecs = self.secs
            return self.msecs

        def reset(self):
            self.start = time.time()

        def update(self, force=False):
            if self.get() > 2 or force:
                self.reset()

                global pctl

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
    if l[0] < r[0]:
        return False
    if l[1] < r[1]:
        return False
    if l[0] > r[0] + r[2]:
        return False
    if l[1] > r[1] + r[3]:
        return False
    return True


def draw_line(x1, y1, x2, y2, colour):
    global renderer
    SDL_SetRenderDrawColor(renderer, colour[0], colour[1], colour[2], colour[3])
    SDL_RenderDrawLine(renderer, x1, y1, x2, y2)


def draw_rect(location, wh, colour, fill=False):
    global renderer
    a = SDL_Rect(location[0], location[1], wh[0], wh[1])

    if fill == True:
        SDL_SetRenderDrawColor(renderer, colour[0], colour[1], colour[2], colour[3])
        SDL_RenderFillRect(renderer, a)
    else:
        SDL_SetRenderDrawColor(renderer, colour[0], colour[1], colour[2], colour[3])
        SDL_RenderDrawRect(renderer, a)


text_cache = []  # location, text, dst(sdl rect), c(texture)
calc_cache = []


def text_calc(text, font):
    text_utf = text.encode('utf-8')
    tex_w = pointer(c_int(0))

    TTF_SizeUTF8(font_dict[font][0], text_utf, tex_w, None)
    xlen = tex_w.contents.value

    return [xlen, 2]


ttc = {}
ttl = []


# Draw text function with enhanced performance via given search reference values


def draw_text2(location, text, colour, font, maxx, field=0, index=0):

    # draw_text(location,trunc_line(text,font,maxx),colour,font)

    if len(text) == 0:
        return 0
    key = (maxx, text, colour[0], colour[1], colour[2], colour[3])

    global ttc

    if key in ttc:
        sd = ttc[key]
        sd[0].x = location[0]
        sd[0].y = location[1]

        if len(location) > 2 and location[2] == 1:
            sd[0].x = location[0] - sd[0].w

        elif len(location) > 2 and location[2] == 2:
            sd[0].x = sd[0].x - int(sd[0].w / 2)

        SDL_RenderCopy(renderer, sd[1], None, sd[0])

        return sd[0].w
    # Render a new text texture and cache it
    else:

        tex_w = pointer(c_int(0))
        tex_h = pointer(c_int(0))
        colour_sdl = SDL_Color(colour[0], colour[1], colour[2], colour[3])
        text_utf = text.encode('utf-8')

        trunc = False

        while True: #and (len(location) < 3 or location[2] == 0):
            if len(text_utf) < 3:
                break
            TTF_SizeUTF8(font_dict[font][0], text_utf, tex_w, None)
            xlen = tex_w.contents.value
            if xlen <= maxx:
                break
            text_utf = text_utf[:-2]
            trunc = True

        if trunc:
            text_utf += "…".encode('utf-8')

        back = False
        for ch in range(len(text)):

            if not TTF_GlyphIsProvided(font_dict[font][0], ord(text[ch])):
                if TTF_GlyphIsProvided(font_dict[font][1], ord(text[ch])):
                    back = True
                    break

        if back:
            font_surface = TTF_RenderUTF8_Blended(font_dict[font][1], text_utf, colour_sdl)
        else:
            font_surface = TTF_RenderUTF8_Blended(font_dict[font][0], text_utf, colour_sdl)

        c = SDL_CreateTextureFromSurface(renderer, font_surface)
        SDL_SetTextureAlphaMod(c, colour[3])
        dst = SDL_Rect(location[0], location[1])
        SDL_QueryTexture(c, None, None, tex_w, tex_h)
        dst.w = tex_w.contents.value
        dst.h = tex_h.contents.value

        # Set text alignment
        if len(location) > 2 and location[2] == 1:
            dst.x = dst.x - dst.w
        elif len(location) > 2 and location[2] == 2:
            dst.x = dst.x - int(dst.w / 2)

        SDL_RenderCopy(renderer, c, None, dst)
        SDL_FreeSurface(font_surface)

        ttc[key] = [dst, c]
        if not text[0].isdigit():
            ttl.append(key)

        # Delete oldest cached text if cache too big to avoid performance slowdowns
        if len(ttl) > 200:
            key = ttl[0]
            so = ttc[key]
            SDL_DestroyTexture(so[1])
            del ttc[key]
            del ttl[0]


        return dst.w


def draw_text(location, text, colour, font, max=1000):
    global text_cache
    return draw_text2(location, text, colour, font, max)



art_cache = []

source_cache = []

temp_dest = SDL_Rect(0, 0)

blur_cache = [(0, 0), (0, 0), "", 0, None]
tag_bc = ""
is_tag = 0
b_location = ""
b_ready = False
b_source_info = []
b_texture = ""

preloaded = []


# Experimental image blur function, not used


# def blur_bg(location, size, source, dex):
#     global b_texture
#     global b_ready
#     global loaderCommandReady
#     global loaderCommand
#     global b_source_info
#     global b_location
#     global is_tag
# 
#     if source[0] != is_tag or b_location != source[1]:
#         b_ready = False
#         b_source_info = source
# 
#         loaderCommand = 'bbg'
#         loaderCommandReady = True
# 
#         is_tag = source[0]
#         b_location = source[1]
# 
#         return 0
# 
#     if b_ready:
#         dst = SDL_Rect(location[0], location[1])
#         dst.w = size[0]
#         dst.h = size[1]
#         SDL_RenderCopy(renderer, b_texture, None, dst)


class GallClass:
    def __init__(self):
        self.gall = {}
        self.size = [album_mode_art_size, album_mode_art_size]
        self.queue = []

    def get_file_source(self, index):

        filepath = master_library[index]['filepath']
        parent_folder = os.path.dirname(filepath)

        # Add parent folder to offset cache
        if parent_folder in folder_image_offsets:
            pass
        else:
            folder_image_offsets[parent_folder] = 1

        offset = folder_image_offsets[parent_folder]

        pics = []

        try:
            if '.mp3' in filepath or '.MP3' in filepath:
                tag = stagger.read_tag(filepath)
                try:
                    tt = tag[APIC][0].data
                except:
                    tt = tag[PIC][0].data
                if len(tt) > 30:
                    pics.append("TAG")

                    if offset == 1:
                        return ["TAG", tt]
                else:
                    pics.append(None)
            else:
                pics.append(None)

        except:
            pics.append(None)
        try:
            direc = os.path.dirname(filepath)
            items_in_dir = os.listdir(direc)
        except:
            print("Directory error")
            return [None]

        for i in range(len(items_in_dir)):

            if os.path.splitext(items_in_dir[i])[1][1:] in {'jpg', 'JPG', 'jpeg', 'JPEG', 'PNG', 'png', 'BMP', 'bmp'}:
                dir_path = os.path.join(direc, items_in_dir[i])
                dir_path = dir_path.replace('\\', "/")
                # print(dir_path)
                pics.append(dir_path)

            elif os.path.isdir(os.path.join(direc, items_in_dir[i])) and \
                            items_in_dir[i].lower() in {'art', 'scans', 'scan', 'booklet', 'images', 'image', 'cover',
                                                        'covers',
                                                        'coverart', 'albumart', 'gallery', 'jacket', 'artwork', 'bonus',
                                                        'bk'}:

                subdirec = os.path.join(direc, items_in_dir[i])
                items_in_dir2 = os.listdir(subdirec)

                for y in range(len(items_in_dir2)):
                    if os.path.splitext(items_in_dir2[y])[1][1:] in {'jpg', 'JPG', 'jpeg', 'JPEG', 'PNG', 'png', 'BMP',
                                                                     'bmp'}:
                        dir_path = os.path.join(subdirec, items_in_dir2[y])
                        dir_path = dir_path.replace('\\', "/")
                        # print(dir_path)
                        pics.append(dir_path)

        if pics == [None]:
            return [None]

        # print(pics)
        # print(offset)

        while offset > len(pics) - 1:
            offset -= 1

        if pics[0] == None:
            offset -= 1
            if offset == 0:
                offset = len(pics) - 1

        return [pics[offset]]

    def render(self, index, location):

        # time.sleep(0.1)

        if index in self.gall:
            # print("old")

            order = self.gall[index]

            if order[0] == 0:
                # print('broken')
                # broken
                return

            if order[0] == 1:
                # not done yet
                return

            if order[0] == 2:
                # print('pro stage 2')
                # finish processing
                wop = sdl2.rw_from_object(order[1])
                s_image = IMG_Load_RW(wop, 0)
                c = SDL_CreateTextureFromSurface(renderer, s_image)
                SDL_FreeSurface(s_image)
                tex_w = pointer(c_int(self.size[0]))
                tex_h = pointer(c_int(self.size[1]))

                SDL_QueryTexture(c, None, None, tex_w, tex_h)

                dst = SDL_Rect(location[0], location[1])

                dst.w = int(tex_w.contents.value)
                dst.h = int(tex_h.contents.value)

                order[0] = 3
                order[1] = None
                order[2] = c
                order[3] = dst

                self.gall[index] = order

            if order[0] == 3:
                # ready
                order[3].x = location[0]
                order[3].y = location[1]

                order[3].x = int((self.size[0] - order[3].w) / 2) + order[3].x
                order[3].y = int((self.size[1] - order[3].h) / 2) + order[3].y

                SDL_RenderCopy(renderer, order[2], None, order[3])

                return

        else:
            # Create new
            # stage, raw, texture, rect
            self.gall[index] = [1, None, None, None]
            self.queue.append(index)
            # print(self.queue)


gall_ren = GallClass()

def clear_img_cache():

    global source_cache
    global art_cache

    for index, item in enumerate(art_cache, start=0):

        if art_cache[index][1] != 1 and art_cache[index][1] != 2:
            SDL_DestroyTexture(art_cache[index][1])

    source_cache = []
    art_cache = []

    for key, value in gall_ren.gall.items():
        SDL_DestroyTexture(value[2])
    gall_ren.gall = {}

    global UPDATE_RENDER
    UPDATE_RENDER += 1


def display_album_art(index, location, size, mode='NONE', offset=0, save_path=""):
    # Warning: This function is a nightmare, don't even attempt to understand

    if mode == 'cacheonly':
        return 0

    global folder_image_offsets
    global source_cache
    global preloaded
    global art_cache
    global albums_to_render

    filepath = master_library[index]['filepath']

    if len(art_cache) > 25 and albums_to_render < 1:
        if art_cache[0][1] != 1 and art_cache[0][1] != 2:
            SDL_DestroyTexture(art_cache[0][1])
        del art_cache[0]
        del source_cache[0]

    # Add parent folder to offset cache
    parent_folder = os.path.dirname(filepath)
    if parent_folder in folder_image_offsets:
        pass
    else:
        folder_image_offsets[parent_folder] = 1

    if mode == "OFFSET":
        folder_image_offsets[parent_folder] += 1
        return 0

    # Find album art locations for music file if not already added
    new = 1
    for a in range(len(source_cache)):
        if source_cache[a][0] == filepath:
            source_index = a
            new = 0
            break

    if new == 1:
        pics = [filepath]

        try:
            if '.mp3' in filepath or '.MP3' in filepath:
                tag = stagger.read_tag(filepath)

                try:
                    tt = tag[APIC][0]
                except:
                    tt = tag[PIC][0]

                if len(tt.data) > 30:
                    pics.append("TAG")
                else:
                    pics.append(None)
            else:
                pics.append(None)

        except:
            pics.append(None)

        try:

            direc = os.path.dirname(filepath)
            items_in_dir = os.listdir(direc)
        except:
            print("Directory error")
            return [0, 1, False]

        for i in range(len(items_in_dir)):

            if os.path.splitext(items_in_dir[i])[1][1:] in {'jpg', 'JPG', 'jpeg', 'JPEG', 'PNG', 'png', 'BMP', 'bmp'}:
                dir_path = os.path.join(direc, items_in_dir[i])
                dir_path = dir_path.replace('\\', "/")
                # print(dir_path)
                pics.append(dir_path)

            elif os.path.isdir(os.path.join(direc, items_in_dir[i])) and \
                            items_in_dir[i].lower() in {'art', 'scans', 'scan', 'booklet', 'images', 'image', 'cover',
                                                        'covers',
                                                        'coverart', 'albumart', 'gallery', 'jacket', 'artwork', 'bonus',
                                                        'bk'}:

                subdirec = os.path.join(direc, items_in_dir[i])
                items_in_dir2 = os.listdir(subdirec)

                for y in range(len(items_in_dir2)):
                    if os.path.splitext(items_in_dir2[y])[1][1:] in {'jpg', 'JPG', 'jpeg', 'JPEG', 'PNG', 'png', 'BMP',
                                                                     'bmp'}:
                        dir_path = os.path.join(subdirec, items_in_dir2[y])
                        dir_path = dir_path.replace('\\', "/")
                        # print(dir_path)
                        pics.append(dir_path)

        source_cache.append(pics)
        source_index = len(source_cache) - 1

    if folder_image_offsets[parent_folder] > len(source_cache[source_index]) - 1:
        folder_image_offsets[parent_folder] = 1

    if source_cache[source_index][folder_image_offsets[parent_folder]] is None and len(source_cache[source_index]) == 2:
        return [0, 1, False]
    elif source_cache[source_index][folder_image_offsets[parent_folder]] is None:
        folder_image_offsets[parent_folder] += 1

    # Open mode
    if mode == "OPEN":
        if source_cache[source_index][folder_image_offsets[parent_folder]] == "TAG":
            return 0
        else:
            if system == "windows":
                os.startfile(source_cache[source_index][folder_image_offsets[parent_folder]])
            else:
                subprocess.call(["xdg-open", source_cache[source_index][folder_image_offsets[parent_folder]]])
            return 0

    elif mode == "RETURN":
        if source_cache[source_index][folder_image_offsets[parent_folder]] == "TAG":
            return 1, filepath
        else:
            if system == "windows":
                return 0, filepath, source_cache[source_index][folder_image_offsets[parent_folder]]

    # Render cached
    fast_found = []
    for q in range(len(art_cache)):

        if mode == 'save':
            break

        if art_cache[q][0] == index and art_cache[q][1] is None:
            return 0, 1, False
        elif art_cache[q][0] == index and art_cache[q][1] is 1:

            return 0, 1, False
        elif art_cache[q][0] == index and art_cache[q][1] is 2:

            wop = sdl2.rw_from_object(art_cache[q][6])
            s_image = IMG_Load_RW(wop, 0)
            # print(IMG_GetError())
            c = SDL_CreateTextureFromSurface(renderer, s_image)

            tex_w = pointer(c_int(size[0]))
            tex_h = pointer(c_int(size[1]))

            SDL_QueryTexture(c, None, None, tex_w, tex_h)

            dst = SDL_Rect(location[0], location[1])

            dst.w = int(tex_w.contents.value)
            dst.h = int(tex_h.contents.value)

            art_cache[q][6].close()

            art_cache[q] = [index, c, dst, size, location, folder_image_offsets[os.path.dirname(filepath)], None, None,
                            None, size]
            # cached_offsets.append( folder_image_offsets[os.path.dirname(filepath)] )

            SDL_FreeSurface(s_image)

            return [0, 1, False]


        # elif art_cache[q][0] == filepath and art_cache[q][3] == size and art_cache[q][4] == location and art_cache[q][5] == folder_image_offsets[os.path.dirname(filepath)]:
        elif art_cache[q][0] == index and art_cache[q][9] == size and art_cache[q][5] == folder_image_offsets[
            os.path.dirname(filepath)]:

            temp_dest.x = location[0]
            temp_dest.y = location[1]
            temp_dest.w = art_cache[q][2].w
            temp_dest.h = art_cache[q][2].h

            temp_dest.x = int((size[0] - temp_dest.w) / 2) + temp_dest.x
            temp_dest.y = int((size[1] - temp_dest.h) / 2) + temp_dest.y

            SDL_RenderCopy(renderer, art_cache[q][1], None, temp_dest)

            # print(source_cache[source_index])
            if len(source_cache[source_index]) > 1 and source_cache[source_index][1] is None:
                return [len(source_cache[source_index]) - 2, art_cache[q][5], False]
            else:
                return [len(source_cache[source_index]) - 1, art_cache[q][5], True]
        # fast mode

        elif art_cache[q][0] == index and mode == 'fast' and art_cache[q][5] == folder_image_offsets[
            os.path.dirname(filepath)]:
            fast_found.append(q)

    if len(fast_found) > 0:

        bx = 0
        q = 0
        for i in fast_found:
            if art_cache[i][2].w > bx:
                bx = art_cache[i][2].w
                q = i

        temp_dest.x = location[0]
        temp_dest.y = location[1]

        temp_dest.w = size[0]
        temp_dest.h = size[1]

        # correct aspect ratio if needed
        if art_cache[q][3][0] > art_cache[q][3][1]:
            temp_dest.w = size[0]
            temp_dest.h = int(temp_dest.h * (art_cache[q][3][1] / art_cache[q][3][0]))
        elif art_cache[q][3][0] < art_cache[q][3][1]:
            temp_dest.h = size[1]
            temp_dest.w = int(temp_dest.h * (art_cache[q][3][0] / art_cache[q][3][1]))

        # prevent scaling larger than original image size
        if temp_dest.w > art_cache[q][3][0] or temp_dest.h > art_cache[q][3][1]:
            temp_dest.w = art_cache[q][3][0]
            temp_dest.h = art_cache[q][3][1]

        # center the image
        temp_dest.x = int((size[0] - temp_dest.w) / 2) + temp_dest.x
        temp_dest.y = int((size[1] - temp_dest.h) / 2) + temp_dest.y

        # render the image
        SDL_RenderCopy(renderer, art_cache[q][1], None, temp_dest)

        # print(source_cache[source_index])
        if len(source_cache[source_index]) > 1 and source_cache[source_index][1] is None:
            return [len(source_cache[source_index]) - 2, art_cache[q][5], False]
        else:
            return [len(source_cache[source_index]) - 1, art_cache[q][5], True]

    # Render new
    try:

        if mode == 'cacheonly':
            art_cache.append([index, 1, None, size, location, folder_image_offsets[os.path.dirname(filepath)], None,
                              source_cache[source_index][folder_image_offsets[parent_folder]], [], size])
            albums_to_render += 1
            return 0
        if source_cache[source_index][folder_image_offsets[parent_folder]] == "TAG":

            tag = stagger.read_tag(filepath)
            # tt = tag[APIC][0]
            try:
                artwork = tag[APIC][0].data
            except:
                artwork = tag[PIC][0].data

            source_image = io.BytesIO(artwork)
        else:
            source_image = open(source_cache[source_index][folder_image_offsets[parent_folder]], 'rb')

        if mode == 'save':

            im = Image.open(source_image)
            if im.mode != "RGB":
                im = im.convert("RGB")
            im.thumbnail(size, Image.ANTIALIAS)
            if save_path == "":
                #im.save('web/' + str(index) + '.jpg', 'JPEG')
                buff = io.BytesIO()
                im.save(buff, format="JPEG")
                sss = base64.b64encode(buff.getvalue())
                return sss
            else:
                im.save(save_path + '.jpg', 'JPEG')
            return 0

        g = io.BytesIO()
        g.seek(0)
        im = Image.open(source_image)
        o_size = im.size
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.thumbnail(size, Image.ANTIALIAS)
        # g = open("test.jpg", 'wb')

        im.save(g, 'JPEG')
        g.seek(0)

        wop = sdl2.rw_from_object(g)
        s_image = IMG_Load_RW(wop, 0)
        # print(IMG_GetError())
        c = SDL_CreateTextureFromSurface(renderer, s_image)

        tex_w = pointer(c_int(size[0]))
        tex_h = pointer(c_int(size[1]))

        SDL_QueryTexture(c, None, None, tex_w, tex_h)

        dst = SDL_Rect(location[0], location[1])

        dst.w = int(tex_w.contents.value)
        dst.h = int(tex_h.contents.value)

        art_cache.append(
                [index, c, dst, o_size, location, folder_image_offsets[os.path.dirname(filepath)], None, None, None,
                 size])
        # cached_offsets.append( folder_image_offsets[os.path.dirname(filepath)] )

        SDL_FreeSurface(s_image)
        g.close()
        source_image.close()

        dst.x = int((size[0] - dst.w) / 2) + dst.x
        dst.y = int((size[1] - dst.h) / 2) + dst.y

        SDL_RenderCopy(renderer, c, None, dst)

    except:

        art_cache.append([index, None])
        # cached_offsets.append( folder_image_offsets[os.path.dirname(filepath)] )
        print(sys.exc_info()[0])

        # print(source_cache)


        return [0, 1, False]

    if source_cache[source_index][1] == "TAG":
        return [len(source_cache[source_index]) - 1, folder_image_offsets[parent_folder], True]
    else:
        return [len(source_cache[source_index]) - 2, folder_image_offsets[parent_folder], False]


def trunc_line(line, font, px):
    trunk = False

    while text_calc(line, font)[0] > px:
        trunk = True
        line = line[:-2]
        if len(line) < 10:
            break
    if trunk is True:
        line += "…"
    return line


click_time = time.time()
scroll_hold = False
scroll_point = 0
scroll_bpoint = 0
sbl = 50
sbp = 100


def fix_encoding(index, mode, enc):
    global master_library
    global default_playlist
    global star_library
    global enc_field

    todo = []

    if mode == 1:
        todo = [index]
    elif mode == 0:
        for b in range(len(default_playlist)):
            if master_library[default_playlist[b]]['parent'] == master_library[index]['parent']:
                todo.append(default_playlist[b])

    for q in range(len(todo)):

        key = master_library[todo[q]]['title'] + master_library[todo[q]]['filename']

        if enc_field == 'All' or enc_field == 'Artist':
            line = master_library[todo[q]]['artist']
            line = line.encode("Latin-1", 'ignore')
            line = line.decode(enc, 'ignore')
            master_library[todo[q]]['artist'] = line

        if enc_field == 'All' or enc_field == 'Album':
            line = master_library[todo[q]]['album']
            line = line.encode("Latin-1", 'ignore')
            line = line.decode(enc, 'ignore')
            master_library[todo[q]]['album'] = line

        if enc_field == 'All' or enc_field == 'Title':
            line = master_library[todo[q]]['title']
            line = line.encode("Latin-1", 'ignore')
            line = line.decode(enc, 'ignore')
            master_library[todo[q]]['title'] = line

        if key in star_library:
            newkey = master_library[todo[q]]['title'] + master_library[todo[q]]['filename']
            if newkey not in star_library:
                star_library[newkey] = copy.deepcopy(star_library[key])
                # del star_library[key]


def transfer_tracks(index, mode, to):
    todo = []

    if mode == 0:
        todo = [index]
    elif mode == 1:
        for b in range(len(default_playlist)):
            if master_library[default_playlist[b]]['parent'] == master_library[index]['parent']:
                todo.append(default_playlist[b])
    elif mode == 2:
        todo = default_playlist

    pctl.multi_playlist[to][2] += todo


def prep_gal():
    global albums
    albums = []

    folder = ""

    for index in default_playlist:

        if folder != master_library[index]['parent']:
            albums.append([index, 0])
            folder = master_library[index]['parent']


# -----------------------------
# LOADING EXTRA
control_line_bottom = 35

s_image1 = IMG_Load(b_active_directroy + b'/gui/playw.png')
c1 = SDL_CreateTextureFromSurface(renderer, s_image1)
SDL_SetTextureColorMod(c1, bottom_panel_colour[0], bottom_panel_colour[1], bottom_panel_colour[2])
dst1 = SDL_Rect(25, window_size[1] - control_line_bottom)
dst1.w = 14
dst1.h = 14

s_image2 = IMG_Load(b_active_directroy + b'/gui/ffw.png')
c2 = SDL_CreateTextureFromSurface(renderer, s_image2)
SDL_SetTextureColorMod(c2, bottom_panel_colour[0], bottom_panel_colour[1], bottom_panel_colour[2])
dst2 = SDL_Rect(240, window_size[1] - control_line_bottom)
dst2.w = 28
dst2.h = 14

s_image3 = IMG_Load(b_active_directroy + b'/gui/bbw.png')
c3 = SDL_CreateTextureFromSurface(renderer, s_image3)
SDL_SetTextureColorMod(c3, bottom_panel_colour[0], bottom_panel_colour[1], bottom_panel_colour[2])
dst3 = SDL_Rect(180, window_size[1] - control_line_bottom)
dst3.w = 28
dst3.h = 14



panelY = 30
panelBY = 51 #51



playlist_top = 38

r = (130, 8, 10, 15)

seek_bar_position = [300, window_size[1] - panelBY]
seek_bar_size = [window_size[0] - 10, 15]
volume_bar_size = [135, 15]

encoding_menu = False
enc_index = 0
enc_setting = 0
enc_field = 'All'

gen_menu = False

transfer_setting = 0

b_panel_size = 300
b_info_bar = False

playlist_left = 20
playlist_top = panelY + 8


highlight_left = playlist_left - highlight_x_offset
highlight_right = playlist_width + highlight_x_offset

# Menu Generator Class, used for top bar menu, track right click menu etc
class Menu():
    switch = 0
    count = switch + 1

    def __init__(self, width):

        self.active = False
        self.clicked = False
        self.pos = [0, 0]
        self.h = 20
        self.w = width
        self.reference = 0
        self.items = []
        self.subs = []

        self.id = Menu.count
        Menu.count += 1

        self.sub_number = 0
        self.sub_active = -1

    @staticmethod
    def deco():
        return [[170, 170, 170, 255], bottom_panel_colour, None]

    def click(self):
        self.clicked = True

    def add(self, title, func, render_func=None, no_exit=False, pass_ref=False):
        if render_func is None:
            render_func = self.deco
        self.items.append([title, False, func, render_func, no_exit, pass_ref])

    def add_sub(self, title, width):
        self.items.append([title, True, self.sub_number, self.deco, width])
        self.sub_number += 1
        self.subs.append([])

    def add_to_sub(self, title, sub, func, render_func=None, no_exit=False, pass_ref=False, args=None):
        if render_func is None:
            render_func = self.deco
        item = [title, False, func, render_func, no_exit, pass_ref, args]
        self.subs[sub].append(item)

    def render(self):
        if self.active:

            ytoff = 2

            if window_size[1] < 250:
                self.h = 14
                ytoff = -1
            else:
                self.h = 20

            if Menu.switch != self.id:
                self.active = False
                return

            for i in range(len(self.items)):

                # Get properties for menu item
                fx = self.items[i][3]()
                if fx[2] is not None:
                    label = fx[2]
                else:
                    label = self.items[i][0]

                # Draw item background, black by default
                draw_rect((self.pos[0], self.pos[1] + i * self.h), (self.w, self.h),
                          fx[1], True)

                # Detect if mouse is over this item
                rect = (self.pos[0], self.pos[1] + i * self.h, self.w, self.h - 1)
                fields.add(rect)

                if coll_point(mouse_position,
                              (self.pos[0], self.pos[1] + i * self.h, self.w, self.h - 1)):
                    draw_rect((self.pos[0], self.pos[1] + i * self.h), (self.w, self.h),
                              [artist_colour[0], artist_colour[1], artist_colour[2], 100], True)  # [15, 15, 15, 255]

                    # Call menu items callback if clicked
                    if self.clicked:
                        if self.items[i][1] is False:
                            if self.items[i][5]:
                                self.items[i][2](self.reference)
                            else:
                                self.items[i][2]()
                        else:
                            self.clicked = False
                            self.sub_active = self.items[i][2]

                # Draw tab
                draw_rect((self.pos[0], self.pos[1] + i * self.h), (5, self.h),
                             GREY(40), True)

                # Render the items label
                draw_text((self.pos[0] + 7 + 5, self.pos[1] + ytoff + i * self.h), label, fx[0], 11)

                # Render sub menu if active
                if self.sub_active > -1 and self.items[i][1] and self.sub_active == self.items[i][2]:

                    # sub_pos = [self.pos[0] + self.w, self.pos[1] + i * self.h]
                    sub_pos = [self.pos[0] + self.w, self.pos[1]]
                    sub_w = self.items[i][4]
                    fx = self.deco()

                    for w in range(len(self.subs[self.sub_active])):

                        # Item background
                        fx = self.subs[self.sub_active][w][3]()
                        draw_rect((sub_pos[0], sub_pos[1] + w * self.h), (sub_w, self.h), fx[1], True)

                        # Detect if mouse is over this item
                        rect = (sub_pos[0], sub_pos[1] + w * self.h, sub_w, self.h - 1)
                        fields.add(rect)
                        if coll_point(mouse_position,
                                      (sub_pos[0], sub_pos[1] + w * self.h, sub_w, self.h - 1)):
                            draw_rect((sub_pos[0], sub_pos[1] + w * self.h), (sub_w, self.h),
                                      [artist_colour[0], artist_colour[1], artist_colour[2], 100], True)

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

                        # Render the items label
                        draw_text((sub_pos[0] + 7, sub_pos[1] + 2 + w * self.h), self.subs[self.sub_active][w][0], fx[0],
                                  11)

                    # Render the menu outline
                    draw_rect(sub_pos, (sub_w, self.h * len(self.subs[self.sub_active])), GREY(40))

            if self.clicked:
                self.active = False
                self.clicked = False

            # Render the menu outline
            draw_rect(self.pos, (self.w, self.h * len(self.items)), GREY(40))

    def activate(self, in_reference=0, position=None):
        if position != None:
            self.pos = position
        else:
            self.pos = copy.deepcopy(mouse_position)

        self.reference = in_reference
        Menu.switch = self.id
        self.sub_active = -1

        # Reposition the menu if it would otherwise intersect with window border
        if self.pos[0] + self.w > window_size[0]:
            self.pos[0] = self.pos[0] - self.w - 3
        if self.pos[1] + len(self.items) * self.h > window_size[1]:
            self.pos[1] -= len(self.items) * self.h
            self.pos[0] += 3
        self.active = True


# Create empty area menu
playlist_menu = Menu(95)


def append_here():
    global cargo
    global renplay
    global default_playlist
    default_playlist += cargo


def paste_deco():
    line_colour = GREY(50)

    if len(cargo) > 0:
        line_colour = [150, 150, 150, 255]

    return [line_colour, bottom_panel_colour, None]

playlist_menu.add('Paste', append_here, paste_deco)

# Create playlist tab menu
tab_menu = Menu(120)

tab_menu.add_sub("New Playlist...", 100)


def new_playlist():
    # global NPN
    # global new_playlist_box
    # new_playlist_box = True
    # NPN = ""

    global pctl
    pctl.multi_playlist.append(["Playlist", 0, [], 0, 0, 0])


tab_menu.add_to_sub("Empty Playlist", 0, new_playlist)


def gen_top_100(index):
    global pctl

    def best(index):
        key = master_library[index]['title'] + master_library[index]['filename']
        if master_library[index]['length'] < 1:
            return 0
        if key in star_library:
            return int(star_library[key]) #/ master_library[index]['length'])
        else:
            return 0

    playlist = copy.deepcopy(pctl.multi_playlist[index][2])
    playlist = sorted(playlist, key=best, reverse=True)

    # if len(playlist) > 1000:
    #     playlist = playlist[:1000]

    pctl.multi_playlist.append(
            [pctl.multi_playlist[index][0] + " <Playtime Sorted>", 0, copy.deepcopy(playlist), 0, 1, 0])


tab_menu.add_to_sub("Most Listened", 0, gen_top_100, pass_ref=True)


def gen_sort_len(index):
    global pctl

    def length(index):

        if master_library[index]['length'] < 1:
            return 0
        else:
            return int(master_library[index]['length'])

    playlist = copy.deepcopy(pctl.multi_playlist[index][2])
    playlist = sorted(playlist, key=length, reverse=True)


    pctl.multi_playlist.append(
            [pctl.multi_playlist[index][0] + " <Duration Sorted>", 0, copy.deepcopy(playlist), 0, 1, 0])


tab_menu.add_to_sub("Duration Sorted", 0, gen_sort_len, pass_ref=True)



def gen_500_random(index):
    global pctl

    # playlist = []
    playlist = copy.deepcopy(pctl.multi_playlist[index][2])
    # if len(pctl.multi_playlist[index][2]) > 1:
    #     for y in range(500):
    #         random_index = random.randrange(len(pctl.multi_playlist[index][2]))
    #         playlist.append(pctl.multi_playlist[index][2][random_index])

    playlist = list(set(playlist))
    random.shuffle(playlist)

    pctl.multi_playlist.append(
            [pctl.multi_playlist[index][0] + " <Shuffled>", 0, copy.deepcopy(playlist), 0,
             1, 0])


tab_menu.add_to_sub("Shuffled", 0, gen_500_random, pass_ref=True)


def gen_best_random(index):
    global pctl

    playlist = []

    for p in pctl.multi_playlist[index][2]:
        key = master_library[p]['title'] + master_library[p]['filename']
        if key in star_library:
            if star_library[key] > 300:
                playlist.append(p)
    random.shuffle(playlist)
    pctl.multi_playlist.append(
            [pctl.multi_playlist[index][0] + " <Random Played>", 0, copy.deepcopy(playlist), 0, 1, 0])


tab_menu.add_to_sub("Random Played", 0, gen_best_random, pass_ref=True)


def activate_genre_box(index):
    global genre_box
    global genre_items
    global genre_box_pl
    genre_items = []
    genre_box_pl = index
    genre_box = True


tab_menu.add_to_sub("Genre...", 0, activate_genre_box, pass_ref=True)


def rename_playlist(index):
    global pctl
    global rename_playlist_box
    global rename_index
    global NPN

    rename_playlist_box = True
    rename_index = index
    NPN = ""


tab_menu.add('Rename Playlist', rename_playlist, pass_ref=True)


def clear_playlist(index):
    global renplay
    global pctl
    global default_playlist

    del pctl.multi_playlist[index][2][:]
    if pctl.playlist_active == index:
        default_playlist = pctl.multi_playlist[index][2]
    # pctl.playlist_playing = 0
    renplay += 2


def convert_playlist(pl):
    global transcode_list
    global message_box
    global message_box_text

    if os.path.isfile(install_directory + '/encoder/ffmpeg.exe') and os.path.isfile(install_directory + '/encoder/opusenc.exe') or \
                    os.path.isfile(install_directory + '/encoder/ffmpeg') and os.path.isfile(install_directory + '/encoder/opusenc') or system != 'windows':
        pass
    else:
        message_box = True
        message_box_text = "Prerequisites not met, see readme file"
        return

    paths = []

    for track in pctl.multi_playlist[pl][2]:
        if master_library[track]['directory'] not in paths:
            paths.append(master_library[track]['directory'])

    for path in paths:
        folder = []
        for track in pctl.multi_playlist[pl][2]:
            if master_library[track]['directory'] == path:
                folder.append(track)
        transcode_list.append(folder)
        print(1)
        print(transcode_list)


# tab_menu.add('Transcode Folders', convert_playlist, pass_ref=True)

tab_menu.add('Clear Playlist', clear_playlist, pass_ref=True)


def delete_playlist(index):
    global pctl
    global pctl
    global default_playlist
    global playlist_position
    global renplay
    global UPDATE_RENDER
    global message_box
    global message_box_text
    global mouse_click

    if len(pctl.multi_playlist) < 2:
        message_box = True
        message_box_text = "Make a new playlist first plz"
        mouse_click = False
        return

    renplay += 1
    UPDATE_RENDER += 1

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
    del pctl.multi_playlist[index]
    if album_mode:
        reload_albums()


tab_menu.add('Delete Playlist', delete_playlist, pass_ref=True)


def append_playlist(index):
    global cargo
    global pctl
    global renplay
    pctl.multi_playlist[index][2] += cargo

    renplay += 1


def drop_deco():
    line_colour = GREY(50)

    if len(cargo) > 0:
        line_colour = [150, 150, 150, 255]

    return [line_colour, [0, 0, 0, 255], None]


tab_menu.add('Paste', append_playlist, paste_deco, pass_ref=True)


def append_current_playing(index):
    global renplay
    global pctl
    if pctl.playing_state > 0 and len(pctl.track_queue) > 0:
        pctl.multi_playlist[index][2].append(pctl.track_queue[pctl.queue_step])
        renplay += 1


def sort_track_pl(pl):
    global master_library
    global pctl

    # REMOVEING FILES THAT HAVE CUE
    # print("need to check for cues")
    global cue_list

    deletes = []

    for t in range(len(pctl.multi_playlist[pl][2])):
        # print(master_library[pctl.multi_playlist[pl][2][t]]['cue'])
        for r in range(len(cue_list)):
            if cue_list[r] == master_library[pctl.multi_playlist[pl][2][t]]['filepath'] and \
                            master_library[pctl.multi_playlist[pl][2][t]][
                                'cue'] == "NO":
                print("FOUND CUE TO DELETE")
                deletes.append(pctl.multi_playlist[pl][2][t])

    p = len(pctl.multi_playlist[pl][2])
    p -= 1
    while p > -1:
        if pctl.multi_playlist[pl][2][p] in deletes:
            del pctl.multi_playlist[pl][2][p]
        p -= 1

    # -----

    if len(pctl.multi_playlist[pl][2]) < 1:
        return (1)

    s = 0
    r = 0
    temp_map = []
    parent = master_library[pctl.multi_playlist[pl][2][r]]['parent']
    temp_map.append([pctl.multi_playlist[pl][2][r], master_library[pctl.multi_playlist[pl][2][r]]['tracknumber']])
    r += 1

    def keya(lis):
        try:
            if '/' in lis[1] or "\\" in lis[1]:
                return float(fractions.Fraction(lis[1]))
            if lis[1].isdigit():
                return float(lis[1])
            else:
                return 0
        except:
            return 0

    while True:
        if r > len(pctl.multi_playlist[pl][2]) - 1:

            temp_map = sorted(temp_map, key=keya)

            for p in range(len(temp_map)):
                pctl.multi_playlist[pl][2][s] = temp_map[p][0]
                s += 1

            break

        if parent == master_library[pctl.multi_playlist[pl][2][r]]['parent']:
            temp_map.append(
                    [pctl.multi_playlist[pl][2][r], master_library[pctl.multi_playlist[pl][2][r]]['tracknumber']])
            r += 1

        else:
            temp_map = sorted(temp_map, key=keya)
            for i in range(len(temp_map)):
                pctl.multi_playlist[pl][2][s] = temp_map[i][0]
                s += 1
            parent = master_library[pctl.multi_playlist[pl][2][r]]['parent']

            temp_map = []


tab_menu.add("Sort Tracks", sort_track_pl, pass_ref=True)

tab_menu.add("Append Playing", append_current_playing, pass_ref=True)


def get_playing_line():
    if 3 > pctl.playing_state > 0:
        title = master_library[pctl.track_queue[pctl.queue_step]]['title']
        artist = master_library[pctl.track_queue[pctl.queue_step]]['artist']
        return artist + " - " + title
    else:
        return 'Stoped'


def get_broadcast_line():
    if broadcast:
        title = master_library[broadcast_index]['title']
        artist = master_library[broadcast_index]['artist']
        return artist + " - " + title
    else:
        return 'No Title'


# Create track context menu
track_menu = Menu(140)


def open_folder(index):
    if system == 'windows':
        line = r'explorer /select,"%s"' % (
            master_library[index]['filepath'].replace("/", "\\"))
        subprocess.Popen(line)
    else:
        line = master_library[index]['directory']
        line += "/"
        subprocess.Popen(['xdg-open', line])


track_menu.add('Open Folder', open_folder, pass_ref=True)


def remove_folder(index):
    global default_playlist

    for b in range(len(default_playlist) - 1, -1, -1):
        r_folder = master_library[index]['parent']
        if master_library[default_playlist[b]]['parent'] == r_folder:
            del default_playlist[b]

    if album_mode:
        reload_albums()


def convert_folder(index):
    global default_playlist
    global transcode_list
    global message_box
    global message_box_text

    if os.path.isfile(install_directory + '/encoder/ffmpeg.exe') and os.path.isfile(
                    install_directory + '/encoder/opusenc.exe') or \
                    os.path.isfile(install_directory + '/encoder/ffmpeg') and os.path.isfile(
                        install_directory + '/encoder/opusenc') or system != 'windows':
        pass
    else:
        message_box = True
        message_box_text = "Prerequisites not met, see readme file"
        return

    folder = []
    r_folder = master_library[index]['parent']
    for item in default_playlist:
        if r_folder == master_library[item]['parent']:
            folder.append(item)

    print(folder)
    transcode_list.append(folder)


def transfer(index, args):
    global cargo
    global default_playlist

    if args[0] == 1 or args[0] == 0:  # copy
        if args[1] == 1:  # single track
            cargo.append(index)
            if args[0] == 0:  # cut
                del default_playlist[playlist_selected]

        elif args[1] == 2:  # folder
            for b in range(len(default_playlist)):
                if master_library[default_playlist[b]]['parent'] == master_library[index]['parent']:
                    cargo.append(default_playlist[b])
            if args[0] == 0:  # cut
                for b in reversed(range(len(default_playlist))):
                    if master_library[default_playlist[b]]['parent'] == master_library[index]['parent']:
                        del default_playlist[b]

        elif args[1] == 3:  # playlist
            cargo += default_playlist
            if args[0] == 0:  # cut
                default_playlist = []

    elif args[0] == 2:  # Drop
        if args[1] == 1:  # Before

            insert = playlist_selected
            while insert > 0 and master_library[default_playlist[insert]]['parent'] == master_library[index]['parent']:
                insert -= 1
                if insert == 0:
                    break
            else:
                insert += 1

            while len(cargo) > 0:
                default_playlist.insert(insert, cargo.pop())

        elif args[1] == 2:  # After
            insert = playlist_selected

            while insert < len(default_playlist) and master_library[default_playlist[insert]]['parent'] == \
                    master_library[index]['parent']:
                insert += 1

            while len(cargo) > 0:
                default_playlist.insert(insert, cargo.pop())
        elif args[1] == 3:  # End
            default_playlist += cargo
            # cargo = []

    print(cargo)


def activate_track_box(index):
    global track_box
    global r_menu_index
    r_menu_index = index
    track_box = True


track_menu.add('Track Info...', activate_track_box, pass_ref=True)

track_menu.add_sub("Modify...", 120)
track_menu.add_sub("Insert/Remove...", 125)


def rename_tracks(index):
    global track_box
    global rename_index
    global input_text
    global renamebox

    track_box = False
    rename_index = index
    renamebox = True
    input_text = ""


track_menu.add_to_sub("Rename Tracks", 0, rename_tracks, pass_ref=True)


def reset_play_count(index):
    global key
    key = master_library[index]['title'] + master_library[index]['filename']
    if key in star_library:
        del star_library[key]


track_menu.add_to_sub("Reset Play Count", 0, reset_play_count, pass_ref=True)


def reload_metadata(index):
    global todo
    global star_library
    global master_library

    todo = []
    for k in default_playlist:
        if master_library[index]['parent'] == master_library[k]['parent']:
            if master_library[k]['cue'] == 'NO':
                todo.append(k)

    for track in todo:

        print('Reloading Metadate for ' + master_library[track]['filename'])
        key = master_library[track]['title'] + master_library[track]['filename']
        star = 0

        if key in star_library:
            star = star_library[key]
            del star_library[key]

        audio = auto.File(master_library[track]['filepath'])
        master_library[track]['length'] = audio.duration
        master_library[track]['title'] = rm_16(audio.title)
        master_library[track]['artist'] = rm_16(audio.artist)
        master_library[track]['album'] = rm_16(audio.album)
        master_library[track]['tracknumber'] = str(audio.track)
        master_library[track]['bitrate'] = audio.bitrate
        master_library[track]['date'] = audio.year
        master_library[track]['genre'] = rm_16(audio.genre)
        master_library[track]['sample'] = audio.sample_rate

        key = master_library[track]['title'] + master_library[track]['filename']
        star_library[key] = star


def activate_encoding_box(index):
    global encoding_box
    global encoding_target

    encoding_box = True
    encoding_target = index


# track_menu.add('Reload Metadata', reload_metadata, pass_ref=True)
track_menu.add_to_sub("Reload Metadata", 0, reload_metadata, pass_ref=True)
track_menu.add_to_sub("Fix Mojibake...", 0, activate_encoding_box, pass_ref=True)


def sel_to_car():
    global cargo
    global default_playlist
    cargo = []

    for item in shift_selection:
        cargo.append(default_playlist[item])


# track_menu.add('Copy Selected', sel_to_car)


def del_selected():
    global UPDATE_RENDER
    global renplay
    global shift_selection
    global playlist_selected

    UPDATE_RENDER += 1
    renplay += 1

    if len(default_playlist) == 0:
        return

    for item in reversed(shift_selection):
        if item > len(default_playlist) - 1:
            return
        del default_playlist[item]

    if album_mode:
        reload_albums()

    if playlist_selected > len(default_playlist) - 1:
        playlist_selected = len(default_playlist) - 1

    shift_selection = [playlist_selected]


# track_menu.add('Remove Folder', remove_folder, pass_ref=True)
# track_menu.add('Remove Selected', del_selected)

if enable_transcode:
    track_menu.add('Transcode Folder', convert_folder, pass_ref=True)

# track_menu.add_sub("Move/Cut...", 90)
# track_menu.add_to_sub("Move Track", 0, transfer, pass_ref=True, args=[0, 1])
# track_menu.add_to_sub("Move Folder", 0, transfer, pass_ref=True, args=[0, 2])
# track_menu.add_to_sub("Move Playlist", 0, transfer, pass_ref=True, args=[0, 3])
# track_menu.add_to_sub("Copy Playlist", 1, transfer, pass_ref=True, args=[1, 3])
# track_menu.add_sub("Copy/Remove", 90)

# track_menu.add_to_sub("Copy Track", 1, transfer, pass_ref=True, args=[1, 1])


# track_menu.add_to_sub("Copy Playlist", 1, transfer, pass_ref=True, args=[1, 3])


track_menu.add_to_sub('Remove Folder', 1, remove_folder, pass_ref=True)
track_menu.add_to_sub('Remove Selected', 1, del_selected)
track_menu.add_to_sub('Copy Selected', 1, sel_to_car)
track_menu.add_to_sub("Copy Folder", 1, transfer, pass_ref=True, args=[1, 2])
track_menu.add_to_sub("Copy & Remove Folder", 1, transfer, pass_ref=True, args=[0, 2])
track_menu.add_to_sub("Insert Before", 1, transfer, paste_deco, pass_ref=True, args=[2, 1])
track_menu.add_to_sub("Insert After", 1, transfer, paste_deco, pass_ref=True, args=[2, 2])
track_menu.add_to_sub("Insert End", 1, transfer, paste_deco, pass_ref=True, args=[2, 3])


def ser_rym(index):

    if len(master_library[index]['artist']) < 2:
        return
    line = "http://rateyourmusic.com/search?searchtype=a&searchterm=" + master_library[index]['artist']
    webbrowser.open(line, new=2, autoraise=True)

def clip_ar_al(index):
    line = master_library[index]['artist'] + " - " + \
           master_library[index]['album']
    pyperclip.copy(line)

track_menu.add('Search Artist on RYM', ser_rym, pass_ref=True)
track_menu.add('Copy "Artist - Album"', clip_ar_al, pass_ref=True)


def clip_ar_tr(index):
    line = master_library[index]['artist'] + " - " + \
           master_library[index]['title']

    pyperclip.copy(line)


track_menu.add('Copy "Artist - Track"', clip_ar_tr, pass_ref=True)


# def activate_encoding_box(index):
#     global encoding_box
#     global encoding_target
# 
#     encoding_box = True
#     encoding_target = index


# track_menu.add("Fix Mojibake...", activate_encoding_box, pass_ref=True)


def queue_deco():
    line_colour = GREY(50)

    if len(pctl.force_queue) > 0:
        line_colour = [150, 150, 150, 255]

    return [line_colour, bottom_panel_colour, None]


def broadcast_feature_deco():
    line_colour = GREY(50)

    if broadcast:
        line_colour = [150, 150, 150, 255]

    return [line_colour, bottom_panel_colour, None]


def broadcast_select_track(index):
    global filepath
    global broadcast_index
    global broadcast_playlist
    global broadcast_position
    global broadcast_time
    global pctl
    global pctl
    global pctl
    global pctl
    global broadcast_line

    if broadcast:
        filepath = master_library[broadcast_index]['filepath']

        broadcast_index = index
        broadcast_playlist = copy.deepcopy(pctl.playlist_active)
        broadcast_position = default_playlist.index(broadcast_index)
        broadcast_time = 0
        b_timer()
        pctl.target_open = master_library[broadcast_index]['filepath']
        pctl.bstart_time = master_library[broadcast_index]['starttime']
        pctl.playerCommand = "encnext"
        pctl.playerCommandReady = True
        broadcast_line = master_library[broadcast_index]['artist'] + " - " + \
                         master_library[broadcast_index]['title']


if default_player == 'BASS':
    track_menu.add('Broadcast This', broadcast_select_track, broadcast_feature_deco, pass_ref=True)

# Create top menu
x_menu = Menu(160)


def bass_features_deco():
    line_colour = GREY6
    if default_player != 'BASS':
        line_colour = GREY(20)
    return [line_colour, bottom_panel_colour, None]


def toggle_dim_albums(mode=0):
    global dim_art
    global UPDATE_RENDER
    global renplay

    if mode == 1:
        return dim_art

    dim_art ^= True
    renplay += 1
    UPDATE_RENDER += 1


def toggle_side_panel(mode=0):
    global side_panel_enable
    global update_layout
    global album_mode
    global prefer_side

    if mode == 1:
        return prefer_side

    prefer_side ^= True
    update_layout = True

    if album_mode:
        side_panel_enable = True
    elif prefer_side is True:
        side_panel_enable = True
    else:
        side_panel_enable = False


# x_menu.add('Toggle Side panel', toggle_side_panel)


def standard_size():
    global album_mode
    global window_size
    global update_layout
    global side_panel_enable
    global side_panel_size

    album_mode = False
    side_panel_enable = True
    SDL_SetWindowSize(t_window, 670, 400)
    window_size = [670, 400]
    side_panel_size = 178
    update_layout = True


def goto_album(playlist_no):

    global album_pos_px
    global album_dex

    old = album_pos_px

    px = 0
    row = 0

    for i in range(len(album_dex)):
        if album_dex[i] > playlist_no:
            break
        row += 1
        if row > row_len - 1:
            row = 0
            px += album_mode_art_size + album_v_gap

    album_pos_px = px - 60 - album_mode_art_size - album_v_gap
    album_pos_px += 10

    if album_pos_px < 500:
        album_pos_px = -55

    if abs(old - album_pos_px) < window_size[1] / 2:
        album_pos_px = old


def toggle_album_mode():
    global album_mode
    global window_size
    global update_layout
    global side_panel_enable
    global side_panel_size
    global old_side_pos
    global album_playlist_width
    global old_album_pos
    global album_pos_px
    global playlist_width

    if album_mode is True:
        album_mode = False
        album_playlist_width = playlist_width
        old_album_pos = album_pos_px
        side_panel_enable = prefer_side
        side_panel_size = old_side_pos
    else:
        album_mode = True
        side_panel_enable = True
        old_side_pos = side_panel_size

    # if window_size[0] < 900:
    #     SDL_SetWindowSize(t_window, 1110, 590)
    #     window_size = [1110, 590]
    #     update_layout = True

    reload_albums()

    goto_album(pctl.playlist_playing)


#x_menu.add('Toggle Gallery View', toggle_album_mode)

# x_menu.add('Reset Layout', standard_size)


def activate_info_box():
    pref_box.enabled = True


x_menu.add("Go To Playing", pctl.show_current)

x_menu.add("Create Empty Playlist", new_playlist)

x_menu.add("Settings...", activate_info_box)



x_menu.add_sub("Database....", 120)


def export_stats():
    global master_library

    playlist_time = 0
    play_time = 0
    for index in pctl.multi_playlist[pctl.playlist_active][2]:
        playlist_time += int(master_library[index]['length'])
        key = master_library[index]['title'] + master_library[index]['filename']
        if key in star_library:
            play_time += star_library[key]

    stats_gen.update(pctl.playlist_active)
    line = 'Stats for playlist: ' + pctl.multi_playlist[pctl.playlist_active][0] + "\r\n"
    line += 'Generated on ' + time.strftime("%c") + "\r\n"
    line += '\r\nTracks in playlist: ' + str(len(pctl.multi_playlist[pctl.playlist_active][2]))
    line += '\r\nTotal Duration: ' + str(datetime.timedelta(seconds=int(playlist_time)))
    line += '\r\nTotal Playtime: ' + str(datetime.timedelta(seconds=int(play_time)))

    line += "\r\n\r\n\r\nTop Artists -----------------------------------\r\n\r\n"

    ls = stats_gen.artist_list
    for item in ls[:15]:
        line += item[0] + "\r\n"
    line += "\r\n\r\nTop Albums -----------------------------------\r\n\r\n"
    ls = stats_gen.album_list
    for item in ls[:15]:
        line += item[0] + "\r\n"
    line += "\r\n\r\nTop Genres -----------------------------------\r\n\r\n"
    ls = stats_gen.genre_list
    for item in ls[:15]:
        line += item[0] + "\r\n"

    line = line.encode('utf-8')
    xport = open('stats.txt', 'wb')
    xport.write(line)
    xport.close()
    target = os.path.join(install_directory, "stats.txt")
    if system == "windows":
        os.startfile(target)
    else:
        subprocess.call(["xdg-open", target])


def export_database():
    global message_box
    global message_box_text

    xport = open('DatabaseExport.csv', 'wb')
    for num in range(master_count):
        line = []
        # print(str(master_library[num]))
        # continue
        # print(master_library[num])
        line.append(str(master_library[num]['artist']))
        line.append(str(master_library[num]['title']))
        line.append(str(master_library[num]['album']))
        line.append(str(master_library[num]['tracknumber']))
        if master_library[num]['cue'] == 'NO':
            line.append('FILE')
        else:
            line.append('CUE')
        line.append(str(master_library[num]['length']))
        line.append(str(master_library[num]['date']))
        line.append(master_library[num]['genre'])

        key = master_library[num]['title'] + master_library[num]['filename']
        if key in star_library:
            line.append(str(int(star_library[key])))
        else:
            line.append('0')
        line.append(master_library[num]['filepath'])

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
    message_box_text = "Done. Saved as 'DatabaseExport.csv'"
    message_box = True


x_menu.add_to_sub("Export as CSV", 0, export_database)
x_menu.add_to_sub("Get Playlist Readout", 0, export_stats)
x_menu.add_to_sub("Reset image cache", 0, clear_img_cache)

def test():
    global message_box
    global message_box_text
    global star_library

    found = 0
    star2 = {}

    for key, value in master_library.items():
        ref = value['title'] + value['filename']
        if ref in star_library:
            found += 1
            star2[ref] = star_library[ref]

    have = sum(star2.values())
    total_pl = sum(star_library.values())

    rem = len(star_library) - len(star2)

    prec = ""
    if total_pl != 0:
        perc = str(int(have / total_pl * 100)) + "% listening time accounted for. "

    if not key_shift_down:
        message_box_text = "Warning: Will lose individual play count for tracks not imported. "
        message_box_text += perc
        message_box_text += str(rem) + " references will be forgotten. Hold shift and try again to apply."
        message_box = True

        return

    else:
        pass
        # star_library = star2
        # star_library total_pl - have


# x_menu.add_to_sub("Test", 0, test)


def reset_missing_flags():
    for index in default_playlist:
        master_library[index]['found'] = True


# x_menu.add('Reset Missing Flags', reset_missing_flags)
x_menu.add_to_sub("Reset missing flags", 0, reset_missing_flags)


def toggle_broadcast():
    global pctl
    global pctl
    global pctl
    global broadcast_playlist
    global broadcast_index
    global broadcast_line

    if broadcast is not True:
        if len(default_playlist) == 0:
            return 0
        broadcast_playlist = pctl.playlist_active
        broadcast_position = 0

        broadcast_index = pctl.multi_playlist[broadcast_playlist][2][broadcast_position]
        pctl.target_open = master_library[broadcast_index]['filepath']
        broadcast_line = master_library[broadcast_index]['artist'] + " - " + \
                         master_library[broadcast_index]['title']

        pctl.playerCommand = "encstart"
        pctl.playerCommandReady = True
    else:
        pctl.playerCommand = "encstop"
        pctl.playerCommandReady = True


def broadcast_deco():
    line_colour = GREY6
    if default_player != 'BASS':
        line_colour = GREY(20)
        return [line_colour, bottom_panel_colour, None]
    if broadcast:
        return [[150, 150, 150, 255], [24, 25, 60, 255], "Stop Broadcast"]
    return [line_colour, bottom_panel_colour, None]


if default_player == 'BASS' and os.path.isfile(os.path.join(install_directory, "config.txt")):
    x_menu.add("Start Broadcast", toggle_broadcast, broadcast_deco)


def clear_queue():
    global pctl
    pctl.force_queue = []


x_menu.add('Clear Queue', clear_queue, queue_deco)


def toggle_level_meter(mode=0):
    global turbo
    global vis
    if mode == 1:
        return turbo

    if turbo is True:
        vis = 0
        turbo = False
    elif turbo is False:
        turbo = True
        vis = 2


# if default_player == 'BASS':
#     x_menu.add("Toggle Level Meter", toggle_level_meter, bass_features_deco)


def advance_theme():
    global theme
    global themeChange
    theme += 1
    themeChange = True


# x_menu.add("Next Theme", advance_theme)


def activate_radio_box():
    global radiobox
    radiobox = True


if default_player == 'BASS':
    x_menu.add("Open Stream...", activate_radio_box, bass_features_deco)


# def activate_info_box():
#     pref_box.enabled = True
#
#
# x_menu.add("Stats/Config...", activate_info_box)


def last_fm_menu_deco():
    if lastfm.connected:
        line = 'Lastfm Scrobbling is Active'
        bg = [20, 60 , 20, 255]
    else:
        line = 'Engage Lastfm Scrobbling'
        bg = bottom_panel_colour
    if lastfm.hold:
        line = "Scrobbling Has Stopped"
        bg = [60, 30 , 30, 255]
    return [[150, 150, 150, 255], bg, line]


x_menu.add("LFM", lastfm.toggle, last_fm_menu_deco)


def exit_func():
    global running
    running = False


x_menu.add("Exit", exit_func)


def switch_playlist(number, cycle=False):
    global pctl
    global default_playlist
    global playlist_position
    global playlist_selected
    global search_index
    global renplay
    global shift_selection

    renplay += 1
    search_index = 0

    if pl_follow:
        pctl.multi_playlist[pctl.playlist_active][1] = copy.deepcopy(pctl.playlist_playing)

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

    # pctl.playlist_playing = pctl.multi_playlist[pctl.playlist_active][1]
    default_playlist = pctl.multi_playlist[pctl.playlist_active][2]
    playlist_position = pctl.multi_playlist[pctl.playlist_active][3]
    playlist_selected = pctl.multi_playlist[pctl.playlist_active][5]

    if pl_follow:
        pctl.playlist_playing = playlist_selected  # pctl.multi_playlist[pctl.playlist_active][1]
        pctl.playlist_playing = copy.deepcopy(pctl.multi_playlist[pctl.playlist_active][1])
        pctl.active_playlist_playing = pctl.playlist_active
        # 
        # print(pctl.playlist_playing)

    # playlist_selected = playlist_position + 5
    # if playlist_selected > len(default_playlist):
    #     playlist_selected = 0
    shift_selection = [playlist_selected]

    if album_mode:
        reload_albums(True)
        goto_album(playlist_position)


# ---------------------------------------------------------------------------------------


# LOADER----------------------------------------------------------------------
added = []


def loader():
    global master_library
    global cue_list
    global loaderCommand
    global loaderCommandReady
    global paths_to_load
    global DA_Formats
    global master_count
    global home
    global items_loaded
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

        cued = []

        try:
            print("Reading CUE file: " + path)
        except:
            print("Error reading path")

        try:

            global master_count
            global master_library

            try:

                with open(path, encoding="utf_8") as f:
                    content = f.readlines()
            except:
                print("Thats not right")
                try:
                    with open(path, encoding="utf_16") as f:
                        content = f.readlines()

                except:
                    print("Wrong again")
                    try:
                        with open(path) as f:
                            content = f.readlines()

                    except:
                        print("Cant detect encoding of CUE file")
                        return 1

            f.close()
            # print(content)

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

            # print("CUE FILE TARGET: " + filename)
            filepath = os.path.dirname(path.replace('\\', '/')) + "/" + filename
            # print("CUE FILE FILEPATH: " + filepath)

            try:
                # print(filepath)
                if os.path.isfile(filepath) == True:

                    audio = auto.File(filepath)
                    SAMPLERATE = 0
                    try:
                        SAMPLERATE = audio.sample_rate
                    except:
                        print("cant read samplerate")
                    lasttime = audio.duration

                else:
                    print("Trying to find file...")

                    for item in os.listdir(os.path.dirname(filepath)):
                        if os.path.splitext(item)[0] == os.path.splitext(os.path.basename(path))[
                            0] and "cue" not in item.lower():
                            filepath = os.path.dirname(filepath) + "/" + item
                            break
                    audio = auto.File(filepath)
                    print(filepath)
                    SAMPLERATE = audio.sample_rate
                    lasttime = audio.duration

                    print("Found matching file name")

            except:
                print("UNABLE TO READ FILE LENGTH")
                return 1

            # Get length from backend
            if lasttime == 0 and default_player == 'BASS':
                lasttime = get_backend_time(filepath)

            LENGTH = 0
            PERFORMER = ""
            TITLE = ""
            START = 0
            DATE = ""
            ALBUM = ""
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

                    try:
                        bitrate = audio.info.bitrate
                    except:
                        bitrate = 0

                    if PERFORMER == "":
                        PERFORMER = MAIN_PERFORMER

                    master_library[master_count] = {'Number': master_count,
                                                    'filepath': filepath.replace('\\', '/'),
                                                    'filename': filename,
                                                    'directory': os.path.dirname(filepath.replace('\\', '/')),
                                                    'parent': os.path.splitext(os.path.basename(filepath))[0],
                                                    # 'parent': get_end_folder(os.path.dirname(filepath)),
                                                    'ext': os.path.splitext(os.path.basename(filepath))[1][1:].upper(),
                                                    'artist': PERFORMER,
                                                    'title': TITLE,
                                                    'length': LENGTH,
                                                    'bitrate': bitrate,
                                                    'album': ALBUM,
                                                    'date': DATE,
                                                    'tracknumber': TN,
                                                    'starttime': START,
                                                    'cue': "YES",
                                                    'date': "",
                                                    'genre': "",
                                                    'found': True,
                                                    'sample': SAMPLERATE
                                                    }
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

    def add_file(path):
        #bm.get("add file start")
        global master_count
        global master_library
        global DA_Formats
        global to_got
        global pctl
        global auto_play_import

        if os.path.splitext(path)[1][1:] in {"CUE", 'cue'}:
            add_from_cue(path)
            return 0

        if os.path.splitext(path)[1][1:] not in DA_Formats:
            return 1

        global UPDATE_RENDER
        to_got += 1
        UPDATE_RENDER = 1


        path = path.replace('\\', '/')

        if path in loaded_pathes_cache:
            de = loaded_pathes_cache[path]
            if master_library[de]['filepath'] in cue_list:
                #bm.get("File has an associated .cue file... Skipping")
                return
            added.append(de)
            if auto_play_import:
                pctl.jump(copy.deepcopy(de))
                print('hit')
                auto_play_import = False
            #bm.get("dupe track")
            return
        print('hit2')
        time.sleep(0.002)

        #bm.get("done dupe check")

        # print('NORMAL FILE PATH: ' +  path.replace('\\', '/') )
        master_library[master_count] = {'Number': master_count,
                                        'filepath': path.replace('\\', '/'),
                                        'filename': os.path.basename(path),
                                        'directory': os.path.dirname(path.replace('\\', '/')),
                                        'parent': get_end_folder(os.path.dirname(path)),
                                        'ext': os.path.splitext(os.path.basename(path))[1][1:].upper(),
                                        'artist': "",
                                        'title': "",
                                        'length': 0,
                                        'bitrate': 0,
                                        'album': "",
                                        'date': "",
                                        'tracknumber': "",
                                        'starttime': 0,
                                        'cue': "NO",
                                        'date': "",
                                        'genre': "",
                                        'found': True,
                                        'sample': 0
                                        }
        #bm.get("create entry")

        if master_library[master_count]['ext'] == 'MP3' or True:
            audio = auto.File(path)

            master_library[master_count]['length'] = audio.duration
            master_library[master_count]['title'] = rm_16(audio.title)
            master_library[master_count]['artist'] = rm_16(audio.artist)
            master_library[master_count]['album'] = rm_16(audio.album)
            master_library[master_count]['tracknumber'] = str(audio.track)
            master_library[master_count]['bitrate'] = audio.bitrate
            master_library[master_count]['date'] = audio.year
            master_library[master_count]['genre'] = rm_16(audio.genre)
            master_library[master_count]['sample'] = audio.sample_rate

        added.append(master_count)
        master_count += 1
        #bm.get("fill entry")
        if auto_play_import:
            pctl.jump(master_count - 1)
            auto_play_import = False

    def pre_get(direc):
        global DA_Formats
        global to_get
        global UPDATE_RENDER

        items_in_dir = os.listdir(direc)
        for q in range(len(items_in_dir)):
            if os.path.isdir(os.path.join(direc, items_in_dir[q])):
                pre_get(os.path.join(direc, items_in_dir[q]))
        for q in range(len(items_in_dir)):
            if os.path.isdir(os.path.join(direc, items_in_dir[q])) is False:
                if os.path.splitext(items_in_dir[q])[1][1:] in DA_Formats:
                    to_get += 1
                    UPDATE_RENDER += 1



    def gets(direc):
        dupe = False
        global master_library
        global DA_Formats
        global master_count

        items_in_dir = os.listdir(direc)
        for q in range(len(items_in_dir)):
            if os.path.isdir(os.path.join(direc, items_in_dir[q])):
                gets(os.path.join(direc, items_in_dir[q]))
        for q in range(len(items_in_dir)):
            if os.path.isdir(os.path.join(direc, items_in_dir[q])) is False:

                if os.path.splitext(items_in_dir[q])[1][1:] in DA_Formats:
                    add_file(os.path.join(direc, items_in_dir[q]).replace('\\', '/'))

                elif os.path.splitext(items_in_dir[q])[1][1:] in {"CUE", 'cue'}:
                    add_from_cue(os.path.join(direc, items_in_dir[q]).replace('\\', '/'))

    def cache_paths():
        dic = {}
        for i in range(len(master_library)):
            dic[master_library[i]['filepath'].replace('\\', '/')] = i
        return dic

    # print(master_library)
    global albums_to_render
    global display_album_art
    global UPDATE_RENDER
    global art_cache
    global transcode_list
    global transcode_state
    global default_player


    while True:
        time.sleep(0.05)

        # FOLDER ENC
        if len(transcode_list) > 0:
            print(8)
            transcode_state = ""
            UPDATE_RENDER += 1

            folder_items = transcode_list[0]

            folder_name = master_library[folder_items[0]]['artist'] + " - " + master_library[folder_items[0]]['album']

            if folder_name == " - ":
                folder_name = master_library[folder_items[0]]['filename']

            "".join([c for c in folder_name if c.isalpha() or c.isdigit() or c == ' ']).rstrip()

            for c in r'[]/\;,><&*:%=+@!#^()|?^.':
                folder_name = folder_name.replace(c, '')

            if os.path.isdir(encoder_output + folder_name):
                del transcode_list[0]
                continue

            print(folder_name)


            os.makedirs(encoder_output + folder_name)

            working_folder = encoder_output + folder_name

            full_wav_out = '"' + encoder_output + 'output.wav"'
            full_opus_out = '"' + encoder_output + 'output.opus"'
            full_wav_out_p = encoder_output + 'output.wav'
            full_opus_out_p = encoder_output + 'output.opus'

            if os.path.isfile(full_wav_out_p):
                os.remove(full_wav_out_p)
            if os.path.isfile(full_opus_out_p):
                os.remove(full_opus_out_p)

            print(1)
            print(full_wav_out)
            print(full_opus_out)

            command = install_directory + "/encoder/ffmpeg "

            if system != 'windows':
                command = "ffmpeg "

            for item in folder_items:
                print(master_library[item]['filepath'])
                command += '-i "'
                command += master_library[item]['filepath']
                command += '" '

            command += '-filter_complex "[0:a:0][1:a:0] concat=n='
            command += str(len(folder_items))
            command += ':v=0:a=1[out]" -map "[out]" '
            command += full_wav_out

            print(4)
            if master_library[folder_items[0]]['cue'] == 'YES' or len(folder_items) == 1:
                command = install_directory + '/encoder/ffmpeg -i "' + master_library[folder_items[0]]['filepath'] + '" ' + full_wav_out

                n_folder = []
                for i in reversed(range(len(folder_items))):
                    if master_library[folder_items[i]]['filepath'] != master_library[folder_items[0]]['filepath']:
                        n_folder.append(folder_items[i])
                        del folder_items[i]
                print(2)
                if len(n_folder) > 0:
                    transcode_list.append(n_folder)

            print(command)

            transcode_state = "(Decoding)"
            UPDATE_RENDER += 1

            print(shlex.split(command))
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.call(shlex.split(command), stdout=subprocess.PIPE, shell=False, startupinfo=startupinfo)

            print('done ffmpeg')

            transcode_state = "(Encoding)"
            UPDATE_RENDER += 1

            command = install_directory + '/encoder/opusenc --bitrate ' + str(transcode_bitrate) +  ' ' + full_wav_out + ' ' + full_opus_out
            #' output.wav output.opus'

            if system != 'windows':
                command = 'opusenc --bitrate ' + str(transcode_bitrate) +  ' ' + full_wav_out + ' ' + full_opus_out

            print(shlex.split(command))
            subprocess.call(shlex.split(command), stdout=subprocess.PIPE, startupinfo=startupinfo)
            print('done')

            os.remove(full_wav_out_p)
            output_dir = encoder_output + folder_name + "/"
            print(output_dir)
            print(output_dir + folder_name + ".opus")
            shutil.move(full_opus_out_p, output_dir + folder_name + ".opus")

            cu = ""
            cu += 'PERFORMER "' + master_library[folder_items[0]]['artist'] + '"\n'
            cu += 'TITLE "' + master_library[folder_items[0]]['album'] + '"\n'
            cu += 'REM DATE "' + master_library[folder_items[0]]['date'] + '"\n'
            cu += 'FILE "' + folder_name + ".opus" + '" WAVE\n'

            run_time = 0
            track = 1

            for item in folder_items:

                cu += 'TRACK '
                if track < 10:
                    cu += '0'
                cu += str(track)
                cu += ' AUDIO\n'

                cu += ' TITLE "'
                cu += master_library[item]['title']
                cu += '"\n'

                cu += ' PERFORMER "'
                cu += master_library[item]['artist']
                cu += '"\n'

                cu += ' INDEX 01 '

                m, s = divmod(run_time, 60)
                s, ms = divmod(s, 1)
                ms = int(round(ms, 2) * 100)

                if ms < 10:
                    ms = '0' + str(ms)
                else:
                    ms = str(ms)

                if m < 10:
                    m = '0' + str(int(m))
                else:
                    m = str(int(m))

                if s < 10:
                    s = '0' + str(int(s))
                else:
                    s = str(int(s))

                cu += m + ":" + s + ":" + ms + "\n"

                if default_player == 'BASS' and master_library[item]['cue'] != 'YES':
                    tracklen = get_backend_time(master_library[item]['filepath'])
                else:
                    tracklen = int(master_library[item]['length'])

                run_time += tracklen
                track += 1

            cue = open(output_dir + folder_name + ".cue", 'w', encoding="utf_8")
            cue.write(cu)
            cue.close()

            display_album_art(folder_items[0], [0, 0], [500, 500], mode='save',
                              save_path=output_dir + folder_name)
            print('finish')

            del transcode_list[0]
            transcode_state = ""
            UPDATE_RENDER += 1

        while len(gall_ren.queue) > 0:

            # print("ready")

            index = gall_ren.queue[0]
            order = gall_ren.gall[index]

            source = gall_ren.get_file_source(index)

            # print(source)

            if source[0] == None:
                order[0] = 0
                gall_ren.gall[index] = order
                del gall_ren.queue[0]
                continue

            try:
                if source[0] == "TAG":
                    # print('tag')
                    source_image = io.BytesIO(source[1])


                else:
                    source_image = open(source[0], 'rb')

                g = io.BytesIO()
                g.seek(0)
                # print('pro stage 1')
                im = Image.open(source_image)
                if im.mode != "RGB":
                    im = im.convert("RGB")
                im.thumbnail(gall_ren.size, Image.ANTIALIAS)

                im.save(g, 'JPEG')
                g.seek(0)

                source_image.close()

                order = [2, g, None, None]
                gall_ren.gall[index] = order

                UPDATE_RENDER += 1

                time.sleep(0.01)

            except:
                print('image error')
                order = [0, None, None, None]
                gall_ren.gall[index] = order

            del gall_ren.queue[0]

            try:
                pass
            # try:
            #     for i in range(len(art_cache)):
            #         if art_cache[i][1] == 1:
            #             # rendercore
            # 
            #             filepath = master_library[art_cache[i][0]]['filepath']
            # 
            #             if art_cache[i][7] == "TAG":
            #                 tag = stagger.read_tag(filepath)
            #                 # tt = tag[APIC][0]
            #                 try:
            #                     artwork = tag[APIC][0].data
            #                 except:
            #                     artwork = tag[PIC][0].data
            #                 source_image = io.BytesIO(artwork)
            #             else:
            #                 source_image = open(art_cache[i][7], 'rb')
            # 
            #             g = io.BytesIO()
            #             g.seek(0)
            #             print('hit')
            #             time.sleep(0.6)
            #             im = Image.open(source_image)
            #             if im.mode != "RGB":
            #                 im = im.convert("RGB")
            #             im.thumbnail(art_cache[i][3], Image.ANTIALIAS)
            # 
            # 
            #             im.save(g, 'JPEG')
            #             g.seek(0)
            # 
            #             art_cache[i][6] = g
            #             source_image.close()
            #             art_cache[i][1] = 2
            # 
            #             albums_to_render -= 1
            #             UPDATE_RENDER += 2
            #             time.sleep(0.02)
            except:

                # art_cache[i] = [art_cache[i][0],None]
                pass

        if loaderCommandReady is True:
            if loaderCommand == 'import folder':
                to_get = 0
                to_got = 0
                loaded_pathes_cache = cache_paths()
                pre_get(paths_to_load)
                gets(paths_to_load)
            elif loaderCommand == 'import file':
                loaded_pathes_cache = cache_paths()
                add_file(paths_to_load)
            # elif loaderCommand == 'bbg':
            #     global b_source_info
            #     global b_texture
            #     global b_ready
            #
            #     print("loader here")
            #
            #     if b_source_info[0] == 1:
            #         tag = stagger.read_tag(b_source_info[1])
            #         try:
            #             tt = tag[APIC][0]
            #         except:
            #             tt = tag[PIC][0]
            #         artwork = tt.data
            #         source_image = io.BytesIO(artwork)
            #     else:
            #         source_image = open(b_source_info[2], 'rb')
            #
            #     im = Image.open(source_image)
            #     im.thumbnail([300, 300], Image.ANTIALIAS)
            #
            #     ix = im.filter(ImageFilter.GaussianBlur(40))
            #     print("got this far")
            #
            #     g = io.BytesIO()
            #     g.seek(0)
            #
            #     ix.save(g, 'JPEG')
            #     g.seek(0)
            #     wop = sdl2.rw_from_object(g)
            #     s_image = IMG_Load_RW(wop, 0)
            #     # print(IMG_GetError())
            #     if b_texture != "":
            #         SDL_DestroyTexture(b_texture)
            #     b_texture = SDL_CreateTextureFromSurface(renderer, s_image)
            #     SDL_FreeSurface(s_image)
            #     g.close()
            #
            #     loaderCommand = ""
            #     loaderCommandReady = False
            #     b_ready = True
            #     continue

            loaderCommand = 'done file'
            # print('ADDED: ' + str(added))
            items_loaded = added
            added = []
            loaderCommandReady = False
            loading_in_progress = False


loaderThread = threading.Thread(target=loader)
loaderThread.daemon = True
loaderThread.start()


def get_album_info(position):
    current = position

    while position > 0:
        if master_library[default_playlist[position]]['parent'] == master_library[default_playlist[current - 1]][
            'parent']:
            current -= 1
            continue
        else:
            break

    album = []
    playing = 0
    while current < len(default_playlist) - 1:
        album.append(current)
        if len(pctl.track_queue) > 0 and default_playlist[current] == pctl.track_queue[pctl.queue_step]:
            playing = 1
        if master_library[default_playlist[current]]['parent'] != master_library[default_playlist[current + 1]][
            'parent']:
            break
        else:
            current += 1
    return playing, album


def reload_albums(quiet=False):
    global album_dex
    global side_panel_size
    global UPDATE_RENDER
    global renplay
    global update_layout
    global album_pos_px
    global playlist_width
    global old_album_pos

    album_pos_px = old_album_pos

    album_dex = []

    current_folder = ""
    for i in range(len(default_playlist)):
        if i == 0:
            album_dex.append(i)
            current_folder = master_library[default_playlist[i]]['parent']

        else:

            if master_library[default_playlist[i]]['parent'] != current_folder:
                current_folder = master_library[default_playlist[i]]['parent']
                album_dex.append(i)

    if quiet is False:
        if album_mode:
            side_panel_size = window_size[0] - 300
            playlist_width = album_playlist_width
        else:
            side_panel_size = old_side_pos
    UPDATE_RENDER += 2
    renplay += 2
    update_layout = True
    goto_album(pctl.playlist_playing)


# ------------------------------------------------------------------------------------

# WEBSERVER

def webserv():
    if enable_web is False:
        return 0

    from flask import Flask, redirect, send_file, abort
    from string import Template

    app = Flask(__name__)

    remote_template = Template("""<!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <title>TMB Remote</title>

    <style>
    body {background-color:#1A1A1A;
    font-family:sans-serif;
    }
    p {
    color:#D1D1D1;
    font-family:sans-serif;
     }
    a {
    color:#D1D1D1;
    font-family:sans-serif;
     }
    l {
    color:#737373;
    font-family:sans-serif;
    font-size: 85%;
     }
    </style>

    </head>

    <body>

    <div style="width:100%;">
    <div style="float:left; width:50%;">

    <p>


    <a href="/remote/downplaylist">Previous Playlist </a> &nbsp
    $pline  &nbsp
    <a href="/remote/upplaylist">Next Playlist</a>
    <br><br> <br> &nbsp; &nbsp; &nbsp;Now Playing: $play

    $image

    <br> <br> <br><br> <br> <br><br> <br> <br><br> <br> <br> <br> <br> <br> <br>
    <a href="/remote/pause">Pause</a>
    <a href="/remote/play">Play</a>
    <a href="/remote/stop">Stop</a>
    &nbsp;
    <a href="/remote/back">Back</a>
    <a href="/remote/forward">Forward</a>

    <br> <br>
    <a href="/remote/random">Random</a>  $isran
    <br> <br>
    <a href="/remote/repeat">Repeat</a> $isrep

    <br> <br>
    <a href="/remote/vup">Vol +</a>
    <a href="/remote/vdown">Vol -</a>
    &nbsp; &nbsp;
    <br><br> Seek [ $seekbar ]
    <br>

    <br>
    <a href="/remote">Reload</a>


    </div>
    <div style="float:left; ">

    <br><br>
    <a href="/remote/pl-up" STYLE="text-decoration: none">Up</a>
    <br><br>
    $list
    <br>
    <a href="/remote/pl-down" STYLE="text-decoration: none">Down</a>

    </p>
    </div>
    </div>

    </body>

    </html>
    """)

    radio_template = Template("""<!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <title>Radio Album Art</title>

    <style>
    body {background-color:#1A1A1A;
    font-family:sans-serif;
    }
    p {
    color:#D1D1D1;
    font-family:sans-serif;
     }
    </style>
    </head>

    <body>
    <br>
    <p><br> <br> <br>
    $image
    <br> <br>  &nbsp; &nbsp; &nbsp; $play
    </p>
    </body>

    </html>
    """)

    # /album_art/<int:indexno>.jpg')
    @app.route('/profile')
    def profile():
        abort(403)
        return (0)
        # page = """<!DOCTYPE html>
        # <html>
        # <head>
        # <meta charset="UTF-8">
        # <title>Profile</title>
        # 
        # <style>
        # body {background-color:# 1A1A1A;
        # font-family:sans-serif;
        # }
        # p {
        # color:# D1D1D1;
        # font-family:sans-serif;
        #  }
        # </style>
        # </head>
        # 
        # <body>
        # <p>
        # test
        # <br> <br>
        # </p>
        # """
        # 
        # stats_gen.update(pctl.playlist_active)
        # alb = stats_gen.album_list
        # for item in alb:
        #     if alb[0] == 'Unknown Album':
        #         del alb[item]
        #         break
        # alb = alb[:25]
        # on = 0
        # for item in alb:
        # 
        #     for index in pctl.multi_playlist[pctl.playlist_active][2]:
        #         if item[0] == master_library[index]['album']:
        #             page += '<img src="/album_index/' + str(index) + '.jpg" alt="No Album Art" style="width:150px;height:150px">'
        #             break
        #     if on > 5:
        #         on = 0
        #         page += "<p><br></p>"
        #     on += 1
        # 
        # page += """
        # </body>
        # 
        # </html>
        # """
        # return page

    @app.route('/remote')
    def remote():

        if not allow_remote:
            abort(403)
            return (0)

        image_line = " "
        if pctl.playing_state > 0:

            image_line = '<img src="data:image/jpeg;base64,'
            bimage = display_album_art(pctl.track_queue[pctl.queue_step], (0, 0), (300, 300), mode='save')
            if type(bimage) is list:
                image_line = "<br><br>&nbsp&nbsp&nbsp&nbsp&nbspNo Album Art"
            else:
                image_line += bimage.decode("utf-8")
                image_line += '" alt="No Album Art" style="float:left;" />'
            # image_line = '<img src="/album_art/' + str(
            #         pctl.track_queue[pctl.queue_step]) + '.jpg" alt="No Album Art" style="float:left;" >'

        randomline = "Is Off"
        if pctl.random_mode:
            randomline = "is On"

        repeatline = "Is Off"
        if pctl.repeat_mode:
            repeatline = "is On"

        playlist_line = ""

        for i in range(len(pctl.multi_playlist)):

            if i == pctl.playlist_active:
                playlist_line += "<strong>" + pctl.multi_playlist[i][0] + "</strong> "
            else:
                playlist_line += pctl.multi_playlist[i][0] + " "


        p_list = "<l>"
        i = playlist_position
        while i < playlist_position + 25:
            if i > len(default_playlist) - 1:
                break



            line = "\n"
            line += '<a href="/remote/jump'
            line += str(default_playlist[i]) + '"'
            line += ' STYLE="text-decoration: none; color:#8c8c8c ">'
            if default_playlist[i] == pctl.track_queue[pctl.queue_step]:
                line += "▶  "
            else:
                line += str(i + 1) + ".  "

            line += master_library[default_playlist[i]]['artist'] + " - " + master_library[default_playlist[i]]['title']
            line += '</a>'
            line += "<br>"
            p_list += line
            i += 1
        p_list += "</l>"

        seek_line = ""
        i = 0
        while i < 100:
            seek_line += '<a href="/remote/seek'
            seek_line += str(i)
            seek_line += '" STYLE="text-decoration: none">-</a>'
            i += 3

        return remote_template.substitute(play=get_playing_line(),
                                          image=image_line,
                                          isran=randomline,
                                          isrep=repeatline,
                                          pline=playlist_line,
                                          list=p_list,
                                          seekbar=seek_line
                                          )

    @app.route('/radio')
    def radio():
        global broadcast_index
        image_line = '<img src="data:image/jpeg;base64,'
        bimage = display_album_art(broadcast_index, (0, 0), (300, 300), mode='save')
        if type(bimage) is list:
            image_line = "<br><br>&nbsp&nbsp&nbsp&nbsp&nbspNo Album Art"
        else:
            image_line += bimage.decode("utf-8")
            image_line += '" alt="No Album Art" style="float:left;" />'

        return radio_template.substitute(play=get_broadcast_line(), image=image_line)

    @app.route('/remote/pl-up')
    def pl_up():
        if not allow_remote:
            abort(403)
            return 0
        global playlist_position
        global default_playlist
        playlist_position -= 24
        if playlist_position < 0:
            playlist_position = 0
        return redirect('/remote', code=302)

    @app.route('/remote/pl-down')
    def pl_down():
        if not allow_remote:
            abort(403)
            return 0
        global playlist_position
        global default_playlist
        playlist_position += 24
        if playlist_position > len(default_playlist) - 26:
            playlist_position = len(default_playlist) - 25
        return redirect('/remote', code=302)


    @app.route('/remote/back')
    def back():
        if not allow_remote:
            abort(403)
            return 0
        global pctl
        pctl.back()
        return redirect('/remote', code=302)


    @app.route('/remote/jump<int:indexno>')
    def jump(indexno):
        if not allow_remote:
            abort(403)
            return (0)
        global pctl
        pctl.jump(indexno)
        return redirect('/remote', code=302)

    @app.route('/remote/forward')
    def fw():
        if not allow_remote:
            abort(403)
            return (0)
        global pctl
        pctl.advance()
        return redirect('/remote', code=302)

    @app.route('/remote/pause')
    def pu():
        if not allow_remote:
            abort(403)
            return (0)
        global pctl
        pctl.pause()
        return redirect('/remote', code=302)

    @app.route('/remote/play')
    def pl():
        if not allow_remote:
            abort(403)
            return (0)
        global pctl
        pctl.play()

        return redirect('/remote', code=302)

    @app.route('/remote/stop')
    def st():
        if not allow_remote:
            abort(403)
            return (0)
        global pctl
        pctl.stop()
        return redirect('/remote', code=302)

    @app.route('/remote/upplaylist')
    def next_playlist():
        if not allow_remote:
            abort(403)
            return (0)
        switch_playlist(1, True)
        return redirect('/remote', code=302)

    @app.route('/remote/downplaylist')
    def back_playlist():
        if not allow_remote:
            abort(403)
            return (0)
        switch_playlist(-1, True)
        return redirect('/remote', code=302)

    @app.route('/remote/vdown')
    def vdown():
        if not allow_remote:
            abort(403)
            return (0)
        global volume
        if volume > 20:
            volume -= 20
        else:
            volume = 0
        pctl.set_volume()

        return redirect('/remote', code=302)

    @app.route('/remote/vup')
    def vup():
        if not allow_remote:
            abort(403)
            return (0)
        global volume
        volume += 20
        if volume > 100:
            volume = 100
        pctl.set_volume()

        return redirect('/remote', code=302)

    @app.route('/remote/seek<int:per>')
    def seek(per):
        if not allow_remote:
            abort(403)
            return (0)
        global new_time
        global pctl

        if per > 100:
            per = 100

        new_time = pctl.playing_length / 100 * per
        pctl.playerCommand = 'seek'
        pctl.playerCommandReady = True
        pctl.playing_time = new_time

        return redirect('/remote', code=302)

    @app.route('/remote/random')
    def ran():
        if not allow_remote:
            abort(403)
            return (0)
        global pctl
        pctl.random_mode ^= True
        return redirect('/remote', code=302)

    @app.route('/remote/repeat')
    def rep():
        if not allow_remote:
            abort(403)
            return (0)
        global pctl
        pctl.repeat_mode ^= True
        return redirect('/remote', code=302)

    # @app.route('/album_art/<int:indexno>.jpg')
    # def get_play_image(indexno):
    #     if not allow_remote:
    #         abort(403)
    #         return (0)
    #     filename = "web/" + str(pctl.track_queue[pctl.queue_step]) + ".jpg"
    #     if not os.path.isfile(filename):
    #         display_album_art(pctl.track_queue[pctl.queue_step], (0, 0), (300, 300), mode='save')
    #
    #     return send_file(filename, mimetype='image/jpg')

    # @app.route('/album_index/<int:indexno>.jpg')
    # def get_album_image(indexno):
    #     if not allow_remote:
    #         abort(403)
    #         return (0)
    #     filename = "web/" + str(indexno) + ".jpg"
    #     if not os.path.isfile(filename):
    #         print((display_album_art(indexno, (0, 0), (150, 150), mode='save')))
    #
    #     return send_file(filename, mimetype='image/jpg')

    # @app.route('/get_image.jpg')
    # def get_image():
    #     global boradcast_index
    #     filename = "web/" + str(broadcast_index) + ".jpg"
    #     if not os.path.isfile(filename):
    #         display_album_art(broadcast_index, (0, 0), (300, 300), mode='save')
    #
    #     return send_file(filename, mimetype='image/jpg')

    if expose_web is True:
        app.run(host='0.0.0.0 ')
    else:
        app.run()


if enable_web is True:
    webThread = threading.Thread(target=webserv)
    webThread.daemon = True
    webThread.start()


# --------------------------------------------------------------

def star_toggle(mode=0):
    global star_lines
    global UPDATE_RENDER
    global renplay

    if mode == 1:
        return star_lines
    star_lines ^= True
    UPDATE_RENDER += 1
    renplay += 1


def split_toggle(mode=0):
    global split_line
    global UPDATE_RENDER
    global renplay

    if mode == 1:
        return split_line
    split_line ^= True
    UPDATE_RENDER += 1
    renplay += 1

def toggle_titlebar_line(mode=0):
    global update_title
    if mode == 1:
        return update_title

    line = window_title
    SDL_SetWindowTitle(t_window, line)
    update_title ^= True


config_items = [
    ['Show Side Panel', toggle_side_panel],
    ['Show Playtime Line', star_toggle],
    ['Highlight Artist Name', split_toggle],
    ['Show Playing in Titlebar', toggle_titlebar_line],
    ['Dim Gallery When Playing', toggle_dim_albums]
]
if default_player == 'BASS':
    config_items.append(['Show Visualisation', toggle_level_meter])


def toggle_break(mode=0):
    global break_enable
    global renplay
    if mode == 1:
        return break_enable
    else:
        break_enable ^= True
        renplay += 1


def toggle_dd(mode=0):
    global dd_index
    global renplay

    if mode == 1:
        return dd_index
    else:
        dd_index ^= True
        renplay += 1


def toggle_custom_line(mode=0):
    global custom_line_mode
    global update_layout

    if mode == 1:
        return custom_line_mode
    else:
        custom_line_mode ^= True
        update_layout = True


def toggle_scroll(mode=0):
    global scroll_enable
    global renplay
    global update_layout

    if mode == 1:
        return scroll_enable
    else:
        scroll_enable ^= True
        renplay += 1
        update_layout = True


def toggle_follow(mode=0):
    global pl_follow

    if mode == 1:
        return pl_follow
    else:
        pl_follow ^= True


def toggle_thick(mode=0):
    global thick_lines
    global update_layout

    if mode == 1:
        return thick_lines
    else:
        thick_lines ^= True
        update_layout = True


config_items.append(['Player Follows Playlist', toggle_follow])

config_items.append(['Enable Scrollbar', toggle_scroll])

config_items.append(['Enable Folder Break', toggle_break])

config_items.append(['Show Double Digits', toggle_dd])

config_items.append(['Use Thick Rows', toggle_thick])

config_items.append(['Use Custom Line Format', toggle_custom_line])

cursor = "|"
c_time = 0
c_blink = 0
key_shiftr_down = False
key_ctrl_down = False


def draw_rect_r(rect, colour, fill=False):
    draw_rect((rect[0], rect[1]), (rect[2], rect[3]), colour, fill)


class Over():
    def __init__(self):

        global window_size

        self.init2done = False

        self.w = 650
        self.h = 250
        self.box_x = int(window_size[0] / 2) - int(self.w / 2)
        self.box_y = int(window_size[1] / 2) - int(self.h / 2)
        self.item_x_offset = 130

        self.current_path = os.path.expanduser('~')
        self.ext_colours = {}
        self.view_offset = 0

        self.enabled = False
        self.click = False
        self.right_click = False
        self.scroll = 0
        self.lock = False

        self.drives = []

        self.tab_active = 2
        self.tabs = [
            ["Folder Import", self.files],
            ["Configure", self.config_v],
            ["Stats", self.stats],
            ["About", self.about]
        ]

    def about(self):

        x = self.box_x + 110 + int((self.w - 110) / 2)
        y = self.box_y + 70

        draw_text((x, y, 2), "Tauon Music Box", GREY8, 16)
        y += 32
        draw_text((x, y, 2), t_version, GREY8, 12)
        y += 20
        draw_text((x, y, 2), "Copyright (c) 2015 Taiko2k captain.gxj@gmail.com", GREY8, 12)

        x = self.box_x + self.w - 115
        y = self.box_y + self.h - 35

        draw_rect((x, y), (101, 22), GREY2)
        fields.add((x, y, 101, 22))
        if coll_point(mouse_position, (x, y, 101, 22)):
            draw_rect((x, y), (101, 22), [40, 40, 40, 60], True)
            if self.click:
                target = os.path.join(install_directory, "license.txt")
                if system == "windows":
                    os.startfile(target)
                else:
                    subprocess.call(["xdg-open", target])

        draw_text((x + 6, y + 2), "License + Credits", [255, 255, 255, 140], 12)

    def stats(self):

        x = self.box_x + self.item_x_offset - 10
        y = self.box_y - 10

        draw_text((x + 8 + 10 + 10, y + 40), "Tracks in Playlist:", GREY8, 12)
        draw_text((x + 8 + 10 + 130, y + 40), '{:,}'.format(len(default_playlist)), GREY8, 12)
        y += 20

        draw_text((x + 8 + 10 + 10, y + 40), "Playlist Length:", GREY8, 12)

        playlist_time = 0
        for item in default_playlist:
            playlist_time += master_library[item]['length']

        line = str(datetime.timedelta(seconds=int(playlist_time)))

        draw_text((x + 8 + 10 + 130, y + 40), line, GREY8, 12)
        y += 20
        draw_text((x + 8 + 10 + 10, y + 40), "Tracks in Database:", GREY8, 12)
        draw_text((x + 8 + 10 + 130, y + 40), '{:,}'.format(master_count), GREY8, 12)
        y += 20
        y += 20
        draw_text((x + 8 + 10 + 10, y + 40), "Total Playtime:", GREY8, 12)
        draw_text((x + 8 + 10 + 130, y + 40), str(datetime.timedelta(seconds=int(total_playtime))), GREY8, 14)

    def config_v(self):

        w = 370
        h = 220
        x = self.box_x + self.item_x_offset
        y = self.box_y

        x += 8
        y += 20
        y2 = y
        x2 = x
        for k in config_items:
            draw_text((x, y), k[0], [255, 255, 255, 150], 12)
            draw_rect((x + 150, y - 2), (70, 20), [255, 255, 255, 13], True)
            if self.click and coll_point(mouse_position, (x + 140 - 5, y - 4 - 2, 70 + 10, 20 + 8)):
                k[1]()
            if k[1](1) == True:
                draw_rect((x + 150 + 40, y - 2), (30, 20), [255, 255, 255, 46], True)
            else:
                draw_rect((x + 150, y - 2), (30, 20), [255, 255, 255, 22], True)

            y += 30

            if y - y2 > 150:
                y = y2
                x += 260

        x = x2
        x -= 130
        y2 += 190

        draw_rect((x + 240, y2), (80, 22), GREY2)

        rect = (x + 240, y2, 80, 22)
        fields.add(rect)

        if coll_point(mouse_position, rect):
            draw_rect((x + 240, y2), (80, 22), [40, 40, 40, 60], True)
            if self.click:
                standard_size()

        draw_text((x + 240 + 6, y2 + 2), "Reset Layout", [255, 255, 255, 140], 12)

        x += 140

        rect = (x + 240, y2, 80, 22)
        fields.add(rect)

        draw_rect((x + 240, y2), (80, 22), GREY2)

        if coll_point(mouse_position, (x + 240, y2, 80, 22)):
            draw_rect((x + 240, y2), (80, 22), [40, 40, 40, 60], True)
            if self.click:
                advance_theme()

        draw_text((x + 240 + 6, y2 + 2), "Next Theme", [255, 255, 255, 140], 12)

    def inside(self):

        return coll_point(mouse_position, (self.box_x, self.box_y, self.w, self.h))

    def init2(self):

        self.init2done = True

        # Stats
        global total_playtime

        total_playtime = sum(star_library.values())

        # Files
        if len(self.drives) < 1 and system == 'windows':
            raw_drives = win32api.GetLogicalDriveStrings()
            self.drives = raw_drives.split('\000')[:-1]

    def render(self):

        if self.init2done is False:
            self.init2()

        if key_esc_press:
            self.enabled = False

        self.box_x = int(window_size[0] / 2) - int(self.w / 2)
        self.box_y = int(window_size[1] / 2) - int(self.h / 2)

        draw_rect((self.box_x, self.box_y), (self.w, self.h), background, True)
        draw_rect((self.box_x, self.box_y), (self.w, self.h), GREY2)
        draw_rect((self.box_x - 1, self.box_y - 1), (self.w + 2, self.h + 2), GREY2)

        # temp
        if len(self.drives) < 1 and system == 'windows':
            raw_drives = win32api.GetLogicalDriveStrings()
            self.drives = raw_drives.split('\000')[:-1]

        current_tab = 0
        for item in self.tabs:

            box = [self.box_x + 1, self.box_y + 1 + (current_tab * 31), 110, 30]
            draw_rect_r(box, playlist_bg, True)

            if current_tab == self.tab_active:
                colour = copy.deepcopy(playlist_bg_active)
                colour[3] = 190
                draw_rect_r(box, colour, True)
            else:
                draw_rect_r(box, playlist_bg, True)

            draw_text((box[0] + 55, box[1] + 7, 2), item[0], [200, 200, 200, 200], 12)

            if self.click and coll_point(mouse_position, box):
                self.tab_active = current_tab

            current_tab += 1

        draw_line(self.box_x + 110, self.box_y + 1, self.box_x + 110, self.box_y + self.h, GREY2)

        self.tabs[self.tab_active][1]()

        self.click = False
        self.right_click = False

    def files(self):

        global droped_file
        global load_to

        self.lock = True

        x = self.box_x + self.item_x_offset + 10
        y = self.box_y + 30

        items_in_folder = os.listdir(self.current_path)

        # order folders first
        a = []
        b = []
        for item in items_in_folder:
            full_path = os.path.join(self.current_path, item)
            if os.path.isfile(full_path):
                b.append(item)
            else:
                a.append(item)
        items_in_folder = a + b

        items_len = len(items_in_folder)

        ic = 0
        ix = 0

        max_view_len = 12

        y += 5

        self.view_offset -= self.scroll
        if self.view_offset < 0:
            self.view_offset = 0
        if self.view_offset > items_len - max_view_len:
            self.view_offset = items_len - max_view_len

        if items_len == 0:
            draw_text((x + 75, y + 50), "Folder is Empty", [200, 200, 200, 200], 12)

        # start file list
        while ic < items_len:

            if ic < self.view_offset:
                ic += 1
                continue

            box = [x, y + 5 + (ix * 14), 8, 8]

            row = [x, y + 2 + (ix * 14), 280, 13]

            # FIND PROPERTIES
            full_path = os.path.join(self.current_path, items_in_folder[ic])
            type = 0
            if os.path.isfile(full_path):
                type = 1
            extension = os.path.splitext(items_in_folder[ic])[1][1:]
            if extension == "":
                extension = "file"

            # COLOUR BOX
            box_colour = []
            if extension.lower() in self.ext_colours:
                box_colour = self.ext_colours[extension.lower()]
            else:
                box_colour = [100 + random.randrange(154), 100 + random.randrange(154), 100 + random.randrange(154),
                              255]
                self.ext_colours[extension.lower()] = box_colour

            # HLT
            fields.add(row)
            if coll_point(mouse_position, row):
                draw_rect_r(row, [60, 60, 60, 60], True)
                if self.click and type == 0:
                    newdir = full_path
                    try:
                        os.listdir(newdir)
                        self.current_path = newdir
                    except:
                        pass

            # FILE NAME
            line = trunc_line(items_in_folder[ic], 12, 150)
            draw_text((x + 65, y + (ix * 14)), line, [200, 200, 200, 200], 12)

            # TYPE NAME + SIZE
            if type == 0:
                draw_rect_r(box, [200, 168, 100, 255], True)
                draw_text((x + 14, y + (ix * 14)), "FLD", [200, 200, 200, 200], 12)
            else:
                draw_text((x + 14, y + (ix * 14)), extension[:7].upper(), [200, 200, 200, 200], 12)
                draw_rect_r(box, box_colour, True)

                file_bytes = os.path.getsize(full_path)
                if file_bytes < 1000:
                    line = str(file_bytes) + " B"
                elif file_bytes < 1000000:
                    file_kb = file_bytes / 1000
                    line = str(int(file_kb)) + " KB"
                else:
                    file_mb = file_bytes / 1000000
                    line = str(int(file_mb)) + " MB"
                draw_text((x + row[2] - 5, y + (ix * 14), 1), line, [200, 200, 200, 200], 12)

            ic += 1
            ix += 1
            if ic - self.view_offset > max_view_len:
                break

        # Reset xy for more drawing
        x = self.box_x + self.item_x_offset + 10
        y = self.box_y + 30

        # UP Box
        rect = (x, y - 20, 50, 20)
        fields.add(rect)
        if coll_point(mouse_position, rect):
            draw_rect((x, y - 20), (50, 20), [40, 40, 40, 60], True)
            if self.click:
                self.current_path = os.path.dirname(self.current_path)
        draw_rect((x, y - 20), (50, 20), GREY2)

        # Path display
        draw_text((x + 60, y - 18), self.current_path, [200, 200, 200, 200], 12)

        # windows drive picker
        if system == 'windows':
            drive_index = 0
            for drive in self.drives:
                box = (x + 100 + (20 * drive_index), y + 195, 19, 20)
                fields.add(box)
                if coll_point(mouse_position, box):
                    draw_rect_r(box, [60, 60, 60, 60], True)
                    if self.click:
                        try:
                            os.listdir(drive)
                            self.current_path = drive
                        except:
                            pass
                draw_text((box[0] + 3, box[1] + 2), drive, [200, 200, 200, 200], 12)
                drive_index += 1

        # Buttons
        y += 14

        draw_text((x + 300, y - 10), "Modify (use with caution) (hold shift)", [200, 200, 200, 200], 12)

        box = (x + 300, y + 7, 180, 20)
        if key_shift_down and coll_point(mouse_position, box):
            draw_rect_r(box, [40, 40, 40, 60], True)
            if self.click:

                # get folders
                folders = []
                for item in os.listdir(self.current_path):
                    folder_path = os.path.join(self.current_path, item)
                    if os.path.isdir(folder_path):
                        folders.append(item)



                for item in folders:
                    folder_path = os.path.join(self.current_path, item)
                    items_in_folder = os.listdir(folder_path)
                    if len(items_in_folder) == 1 and os.path.isdir(os.path.join(folder_path, items_in_folder[0])):
                        target_path = os.path.join(folder_path, items_in_folder[0])

                        if item == items_in_folder[0]:
                            print('same')
                            os.rename(target_path, target_path + "RMTEMP")
                            shutil.move(target_path + "RMTEMP", self.current_path)
                            shutil.rmtree(folder_path)
                            os.rename(folder_path + "RMTEMP", folder_path)
                        else:
                            print('diferent')
                            shutil.move(target_path, self.current_path)
                            shutil.rmtree(folder_path)
                            os.rename(os.path.join(self.current_path, items_in_folder[0]), folder_path)

        draw_rect_r(box, GREY2)
        fields.add(box)
        draw_text((box[0] + 90, box[1] + 2, 2), "Move single folder in folders up", [200, 200, 200, 200], 12)

        y += 50

        draw_text((x + 300, y - 10), "Import", [200, 200, 200, 200], 12)

        box = (x + 300, y + 7, 180, 20)
        if coll_point(mouse_position, box):
            draw_rect_r(box, [40, 40, 40, 60], True)
            if self.click:
                load_to.append(copy.deepcopy(pctl.playlist_active))
                droped_file.append(copy.deepcopy(self.current_path))

        draw_rect_r(box, GREY2)
        fields.add(box)
        draw_text((box[0] + 90, box[1] + 2, 2), "Folder to current playlist", [200, 200, 200, 200], 12)

        y += 25

        box = (x + 300, y + 7, 180, 20)
        if coll_point(mouse_position, box):
            draw_rect_r(box, [40, 40, 40, 60], True)
            if self.click:
                pctl.multi_playlist.append([os.path.basename(self.current_path), 0, [], 0, 0, 0])
                load_to.append(len(pctl.multi_playlist) - 1)
                droped_file.append(copy.deepcopy(self.current_path))

        draw_rect_r(box, GREY2)
        fields.add(box)
        draw_text((box[0] + 90, box[1] + 2, 2), "Folder to new playlist", [200, 200, 200, 200], 12)

        y += 25

        box = (x + 300, y + 7, 180, 20)
        if coll_point(mouse_position, box):
            draw_rect_r(box, [40, 40, 40, 60], True)
            if self.click:

                in_current = os.listdir(self.current_path)
                for item in in_current:

                    full_path = os.path.join(self.current_path, item)
                    if os.path.isdir(full_path):
                        pctl.multi_playlist.append([item, 0, [], 0, 0, 0])
                        load_to.append(len(pctl.multi_playlist) - 1)
                        droped_file.append(full_path)

        draw_rect_r(box, GREY2)
        fields.add(box)
        draw_text((box[0] + 90, box[1] + 2, 2), "Each folder as new playlist", [200, 200, 200, 200], 12)


class Fields():
    def __init__(self):

        self.id = ""
        self.last_id = ""

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
        self.id = ""

        for f in self.field_array:
            if coll_point(mouse_position, f):
                self.id += "1"
            else:
                self.id += "0"

        if self.last_id == self.id:
            return False
        else:
            return True

    def clear(self):

        self.field_array = []


fields = Fields()

pref_box = Over()





# MAIN LOOP---------------------------------------------------------------------------

playlist_view_length = int(((window_size[1] - playlist_top) / 16) - 1)

running = True
lowered = False
boarder = 1

update_layout = True

event = SDL_Event()

print("Initialization Complete")

mouse_moved = False

power = 0
key_F7 = False

i = 1
while i < len(sys.argv):

    for w in range(len(pctl.multi_playlist)):
        if pctl.multi_playlist[w][0] == "Default":
            del pctl.multi_playlist[w][2][:]
            load_to.append(copy.deepcopy(w))
            break
    else:
        pctl.multi_playlist.append(["Default", 0, [], 0, 0, 0])
        load_to.append(len(pctl.multi_playlist) - 1)
        switch_playlist(len(pctl.multi_playlist) - 1)

    if i == 1:
        auto_play_import = True

    droped_file.append(sys.argv[i])
    i += 1

while running:

    # bm.get('main')

    d_mouse_click = False
    mouse4 = False
    mouse5 = False
    right_click = False
    mouse_click = False
    middle_click = False
    mouse_up = False
    key_return_press = False
    key_ralt = False
    key_space_press = False
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
    key_F1 = False
    key_PGU = False
    key_PGD = False
    key_del = False
    key_backspace_press = False
    key_1_press = False
    # key_2_press = False
    # key_3_press = False
    # key_4_press = False
    # key_5_press = False
    key_v_press = False
    key_f_press = False
    key_dash_press = False
    key_eq_press = False
    key_slash_press = False
    key_period_press = False
    key_comma_press = False
    key_quote_hit = False
    key_return_press_w = False
    mouse_wheel = 0
    input_text = ''
    clicked = False
    focused = False
    mouse_moved = False


    while SDL_PollEvent(ctypes.byref(event)) != 0:


        if event.type == SDL_DROPFILE:
            power += 5
            k = 0
            i_y = pointer(c_int(0))
            i_x = pointer(c_int(0))
            SDL_GetMouseState(i_x, i_y)
            i_y = i_y.contents.value
            i_x = i_x.contents.value

            if i_y < panelY:
                for w in range(len(pctl.multi_playlist)):
                    text_space = text_calc(pctl.multi_playlist[w][0], 12)[0]
                    x = starting_l + (spacing * w) + k
                    if x < i_x < x + text_space:
                        load_to.append(copy.deepcopy(w))
                        print("hit 1")
                        print(w)
                        break
                    k += text_space
                else:
                    load_to.append(copy.deepcopy(pctl.playlist_active))
            else:
                load_to.append(copy.deepcopy(pctl.playlist_active))

            droped_file_sdl = event.drop.file
            # print(droped_file_sdl)
            # droped_file.append(str(droped_file_sdl.decode("utf-8")))
            droped_file.append(str(urllib.parse.unquote(droped_file_sdl.decode("utf-8"))))
            # print(urllib.parse.unquote(droped_file_sdl.decode("utf-8")))

            # SDL_free(droped_file_sdl)

            # print('Droped: ' + str(droped_file))
            UPDATE_RENDER += 1

            mouse_down = False
            dragmode = False
        elif event.type == 8192:
            renplay += 2
            UPDATE_RENDER += 2

        elif event.type == SDL_QUIT:
            power += 5
            running = False
            break
        elif event.type == SDL_TEXTEDITING:
            power += 5
            editline = event.edit.text
            editline = editline.decode("utf-8", 'ignore')

        elif event.type == SDL_MOUSEMOTION:

            mouse_position[0] = event.motion.x
            mouse_position[1] = event.motion.y
            mouse_moved = True
        elif event.type == SDL_MOUSEBUTTONDOWN:
            power += 5
            UPDATE_RENDER += 1
            if event.button.button == SDL_BUTTON_RIGHT:
                right_click = True
                right_down = True
            elif event.button.button == SDL_BUTTON_LEFT:

                if mouse_position[1] > 1 and mouse_position[0] > 1:
                    mouse_down = True
                mouse_click = True
                mouse_down = True
            elif event.button.button == SDL_BUTTON_MIDDLE:
                middle_click = True
                UPDATE_RENDER += 1
            elif event.button.button == SDL_BUTTON_X1:
                mouse4 = True
            elif event.button.button == SDL_BUTTON_X2:
                mouse5 = True
        elif event.type == SDL_MOUSEBUTTONUP:
            power += 5
            UPDATE_RENDER += 1
            if event.button.button == SDL_BUTTON_RIGHT:
                right_down = False
            elif event.button.button == SDL_BUTTON_LEFT:

                mouse_down = False
                mouse_up = True
        elif event.type == SDL_KEYDOWN:
            power += 5
            UPDATE_RENDER += 2
            if event.key.keysym.sym == SDLK_RETURN and len(editline) == 0:
                key_return_press = True
            elif event.key.keysym.sym == SDLK_SPACE:
                key_space_press = True
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
            elif event.key.keysym.sym == SDLK_PAGEUP:
                key_PGU = True
            elif event.key.keysym.sym == SDLK_PAGEDOWN:
                key_PGD = True
            elif event.key.keysym.sym == SDLK_v:
                key_v_press = True
            elif event.key.keysym.sym == SDLK_f:
                key_f_press = True
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
            elif event.key.keysym.sym == SDLK_1:
                key_1_press = True
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

            elif event.key.keysym.sym == SDLK_LCTRL:
                key_ctrl_down = True
        elif event.type == SDL_KEYUP:
            power += 5
            UPDATE_RENDER += 2
            if event.key.keysym.sym == SDLK_LSHIFT:
                key_shift_down = False
            elif event.key.keysym.sym == SDLK_LCTRL:
                key_ctrl_down = False
            elif event.key.keysym.sym == SDLK_RSHIFT:
                key_shiftr_down = False
        elif event.type == SDL_TEXTINPUT:
            power += 5
            input_text = event.text.text
            input_text = input_text.decode('utf-8')
            # print(input_text)
        elif event.type == SDL_MOUSEWHEEL:
            power += 5
            mouse_wheel += event.wheel.y
            UPDATE_RENDER += 1
        elif event.type == SDL_WINDOWEVENT:

            power += 5

            if event.window.event == SDL_WINDOWEVENT_FOCUS_GAINED:

                focused = True
                mouse_down = False
                renplay += 1
                UPDATE_RENDER += 1

                # Workaround for SDL bug 2610
                if SDL_GetWindowFlags(t_window) & SDL_WINDOW_MAXIMIZED:
                    SDL_RestoreWindow(t_window)
                    SDL_MaximizeWindow(t_window)
                elif SDL_GetWindowFlags(t_window) & SDL_WINDOW_FULLSCREEN_DESKTOP:

                    SDL_RestoreWindow(t_window)
                    SDL_SetWindowFullscreen(t_window, SDL_WINDOW_FULLSCREEN_DESKTOP)

            if event.window.event == SDL_WINDOWEVENT_RESIZED:
                UPDATE_RENDER += 1
                window_size[0] = event.window.data1
                window_size[1] = event.window.data2
                update_layout = True

            elif event.window.event == SDL_WINDOWEVENT_MINIMIZED:
                lowered = True
            elif event.window.event == SDL_WINDOWEVENT_RESTORED:
                lowered = False

                renplay += 1
                UPDATE_RENDER += 1

                if update_title:
                    update_title_do()

            elif event.window.event == SDL_WINDOWEVENT_SHOWN:

                focused = True
                renplay += 1
                UPDATE_RENDER += 1

    power += 1
    if dragmode or resize_mode or scroll_hold:
        power += 3
    if side_drag:
        power += 2
    if UPDATE_LEVEL:
        power = 6

    if power < 5:
        time.sleep(0.007)
        continue
    else:
        power = 0

    if renplay > 2:
        renplay = 2

    if fields.test():
        UPDATE_RENDER += 1

    # if key_F1:
    #     print(get_backend_time(master_library[pctl.track_queue[pctl.queue_step]]['filepath']))

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
        if boarder == 0:
            boarder = 1
            SDL_SetWindowBordered(t_window, SDL_TRUE)

        elif boarder == 1:
            boarder = 0
            SDL_SetWindowBordered(t_window, SDL_FALSE)
    if key_F3:
        split_line ^= True
        renplay += 1
        UPDATE_RENDER += 1

    if mouse4:
        toggle_album_mode()
    if mouse5:
        toggle_side_panel()

    ab_click = False

    if pref_box.enabled:

        if pref_box.inside():
            if mouse_click:
                pref_box.click = True
                mouse_click = False
            if right_click:
                right_click = False
                pref_box.right_click = True

            pref_box.scroll = mouse_wheel
            mouse_wheel = 0
        else:
            if mouse_click:
                pref_box.enabled = False
            if right_click:
                pref_box.enabled = False
            if pref_box.lock is False:
                pass

    # Transfer click register to menus
    if x_menu.active is True and mouse_click:
        x_menu.click()
        mouse_click = False
        ab_click = True

    if playlist_menu.active and mouse_click:
        playlist_menu.click()
        mouse_click = False
        ab_click = True

    if track_menu.active is True and mouse_click:
        track_menu.click()
        mouse_click = False
        ab_click = True

    if tab_menu.active is True and mouse_click:
        tab_menu.click()
        mouse_click = False
        ab_click = True

    if encoding_box is True and mouse_click:
        encoding_box_click = True
        mouse_click = False
        ab_click = True
    else:
        encoding_box_click = False

    genre_box_click = False
    if genre_box and mouse_click:
        mouse_click = False
        genre_box_click = True

    if radiobox and key_return_press:
        key_return_press = False
        key_return_press_w = True

    if mouse_wheel != 0:
        UPDATE_RENDER += 1
    if mouse_down is True:
        UPDATE_RENDER += 1

    if key_PGD:
        if len(default_playlist) > 10:
            playlist_position += playlist_view_length - 4
            if playlist_position > len(default_playlist):
                playlist_position = len(default_playlist) - 2
            renplay += 1
    if key_PGU:
        if len(default_playlist) > 0:
            playlist_position -= playlist_view_length - 4
            if playlist_position < 0:
                playlist_position = 0
            renplay += 1

    if mouse_click:
        n_click_time = time.time()
        if n_click_time - click_time < 0.7:
            d_mouse_click = True
        click_time = n_click_time

    # if mouse_position[1] < 1:
    #     mouse_down = False

    if mouse_down is False:
        scroll_hold = False

    if focused is True:
        mouse_down = False

    if key_F8:
        lfm_hash = ""
        lfm_password = ""
        lfm_username = ""
        message_box = True
        message_box_text = "Account Info Reset"

    if key_del:
        del_selected()

    if key_F1:
        toggle_album_mode()

    if key_F5:
        pctl.playerCommand = 'encpause'
        pctl.playerCommandReady = True

    if key_F6:
        join_broadcast ^= True
        print("Join brodcast commands:" + str(join_broadcast))

    if key_F4:
        standard_size()

    if key_comma_press:
        pctl.repeat_mode ^= True


    if key_dash_press:
        new_time = pctl.playing_time - 15
        pctl.playing_time -= 15
        if new_time < 0:
            new_time = 0
            pctl.playing_time = 0
        pctl.playerCommand = 'seek'
        pctl.playerCommandReady = True

    if key_eq_press:
        new_time = pctl.playing_time + 15
        pctl.playing_time += 15
        pctl.playerCommand = 'seek'
        pctl.playerCommandReady = True

    if key_F7:
        # spec_smoothing ^= True
        # key_F7 = False
        #print((display_album_art(1, (0, 0), (150, 150), mode='save')))
        # if draw_border:
        #     SDL_SetWindowBordered(t_window, True)
        #     draw_border = False
        # else:
        #     SDL_SetWindowBordered(t_window, False)
        #     draw_border = True
        message_box = True
        message_box_text = str(sys.argv)

        key_F7 = False

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

    if key_shiftr_down and key_right_press:
        key_right_press = False
        pctl.advance()
        # print('hit')
    if key_shiftr_down and key_left_press:
        key_left_press = False
        pctl.back()

    if key_slash_press:
        pctl.advance(rr=True)
        pctl.random_mode ^= True
    if key_period_press:
        pctl.random_mode ^= True



    if key_quote_hit:
        pctl.show_current()

    if len(droped_file) > 0:
        if loading_in_progress == False and len(items_loaded) == 0:
            loading_in_progress = True

            paths_to_load = droped_file[0].replace('\\', '/')
            if os.path.isdir(paths_to_load):
                loaderCommand = 'import folder'
            else:
                loaderCommand = 'import file'
            loaderCommandReady = True
            # print(droped_file)
            del droped_file[0]
    if loaderCommand == 'done file':
        loaderCommand = ""
        UPDATE_RENDER += 1
        renplay += 2
        loading_in_progress = False

    if update_layout:
        # update layout

        mouse_click = False

        volume_bar_position[0] = window_size[0] - 210
        volume_bar_position[1] = window_size[1] - 27
        seek_bar_position[1] = window_size[1] - panelBY
        seek_bar_size[0] = window_size[0] - 300

        dst1.y = window_size[1] - control_line_bottom
        dst2.y = window_size[1] - control_line_bottom
        dst3.y = window_size[1] - control_line_bottom
        # time_display_position = [window_size[0] - 10, 8]

        time_display_position[0] = window_size[0] - time_display_position_right

        # if album_mode and b_info_bar:
        #     playlist_view_length = int(((window_size[1] - 38 - playlist_top - b_panel_size) / 16) - 4)
        # else:


        highlight_x_offset = 0
        if scroll_enable and custom_line_mode:
            highlight_x_offset = 16



        # playlist_view_length = int(((window_size[1] - playlist_top) / 16) - 4)

        random_button_position = window_size[0] - 90, 83

        if thick_lines:
            playlist_row_height = 31
            playlist_text_offset = 6
            playlist_line_x_offset = 7
        else:
            playlist_row_height = 16
            playlist_text_offset = 0
            playlist_line_x_offset = 0

        playlist_view_length = int(((window_size[1] - panelBY - playlist_top) / playlist_row_height) - 1)

        if side_panel_enable is True:

            if side_panel_size < 100:
                side_panel_size = 100
            if side_panel_size > window_size[1] - 77 and album_mode is not True:
                side_panel_size = window_size[1] - 77

            if side_panel_size > window_size[0] - 300 and album_mode is True:
                side_panel_size = window_size[0] - 300

            if album_mode != True:
                playlist_width = window_size[0] - side_panel_size - 30
            else:
                side_panel_size = window_size[0] - playlist_width - 30
        else:
            playlist_width = window_size[0] - 43
            if custom_line_mode:
                playlist_width = window_size[0] - 30


        #tttt


        if window_size[0] < 630:
            compact_bar = True
        else:
            compact_bar = False

        if custom_line_mode:

            x = playlist_width + 10 + 18
            al = 1
            cust = []
            r_res = 100

            for a in range(len(custom_pro)):

                if custom_pro[a][0] == 't':

                    cust.append(['t', copy.deepcopy(x), copy.deepcopy(al)])

                elif custom_pro[a][0] == 'r':

                    add = int(custom_pro[a][1:])
                    if al == 1:
                        add *= -1
                    # print(add)
                    x += add

                elif custom_pro[a][0] == 'l':
                    al = 0
                    r_res = x
                    x = 0
                    if scroll_enable:
                        x += 16

                elif custom_pro[a][0] == 'i':
                    ex = custom_pro[a][1:]
                    cust.append(['i', copy.deepcopy(x), copy.deepcopy(al), ex])

                elif custom_pro[a][0] == 'c':
                    ex = custom_pro[a][1:]
                    cust.append(['c', copy.deepcopy(x), copy.deepcopy(al), copy.deepcopy(ex)])

                elif custom_pro[a][0] == 'p':
                    de = float(custom_pro[a][1:])
                    x = int(playlist_width * de)

                elif custom_pro[a][0] == 'a':
                    res = 500
                    if len(custom_pro) > a + 2:
                        if custom_pro[a + 1][0] == 'p':
                            de = float(custom_pro[a + 1][1:])
                            res = int(playlist_width * de)
                            res -= x + 20
                        else:
                            res = r_res - x - 25

                    cust.append(['a', copy.deepcopy(x), copy.deepcopy(al), res])

                elif custom_pro[a][0] == 'n':
                    res = 500
                    if len(custom_pro) > a + 2:
                        if custom_pro[a + 1][0] == 'p':
                            de = float(custom_pro[a + 1][1:])
                            res = int(playlist_width * de)
                            res -= x + 20
                        else:
                            res = r_res - x - 25
                    cust.append(['n', copy.deepcopy(x), copy.deepcopy(al), res])

                elif custom_pro[a][0] == 'b':
                    res = 500
                    if len(custom_pro) > a + 2:
                        if custom_pro[a + 1][0] == 'p':
                            de = float(custom_pro[a + 1][1:])
                            res = int(playlist_width * de)
                            res -= x + 20
                        else:
                            res = r_res - x

                    else:
                        res = r_res - x - 25

                    cust.append(['b', copy.deepcopy(x), copy.deepcopy(al), res])

                elif custom_pro[a][0] == 'd':
                    res = 500
                    if len(custom_pro) > a + 2:
                        if custom_pro[a + 1][0] == 'p':
                            de = float(custom_pro[a + 1][1:])
                            res = int(playlist_width * de)
                            res -= x + 20
                        else:
                            res = r_res - x

                    else:
                        res = r_res - x - 25

                    cust.append(['d', copy.deepcopy(x), copy.deepcopy(al), res])

                elif custom_pro[a][0] == 's':

                    le = custom_pro[a][1:]
                    if le == "":
                        le = 25
                    else:
                        le = int(le)
                    cust.append(['s', copy.deepcopy(x), copy.deepcopy(al), le])

                elif custom_pro[a][0] == 'o':
                    cust.append(['o', copy.deepcopy(x), copy.deepcopy(al)])

        abc = SDL_Rect(0, 0, window_size[0], window_size[1])

        if GUI_Mode == 2:
            SDL_DestroyTexture(ttext)
            panelBY = 30
            panelY = 0
            playlist_top = 5

            renplay += 2

            playlist_view_length = int(((window_size[1] - playlist_top) / playlist_row_height) - 0) - 3

        if GUI_Mode == 1:
            SDL_DestroyTexture(ttext)
            renplay += 2

        ttext = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_UNKNOWN, SDL_TEXTUREACCESS_TARGET, window_size[0], window_size[1])
        SDL_SetTextureBlendMode(ttext, SDL_BLENDMODE_BLEND)


        update_layout = False

    # -----------------------------------------------------
    # THEME SWITCHER--------------------------------------------------------------------
    if key_F2:
        themeChange = True
        theme += 1

    if themeChange is True:
        renplay += 2
        if theme > 25:
            theme = 0
        if theme > 0:
            theme_number = theme - 1
            try:
                theme_files = os.listdir(install_directory + '/theme')

                for i in range(len(theme_files)):
                    # print(theme_files[i])
                    if i == theme_number and 'ttheme' in theme_files[i]:
                        with open(install_directory + "/theme/" + theme_files[i], encoding="utf_8") as f:
                            content = f.readlines()
                            for p in content:
                                if "#" in p:
                                    continue
                                if 'index playing' in p:
                                    index_playing_cl = get_colour_from_line(p)
                                if 'time playing' in p:
                                    time_playing_cl = get_colour_from_line(p)
                                if 'artist playing' in p:
                                    artist_playing_cl = get_colour_from_line(p)
                                if 'album line' in p:
                                    album_cl = get_colour_from_line(p)
                                if 'album playing' in p:
                                    album_playing = get_colour_from_line(p)
                                if 'player background' in p:
                                    background = get_colour_from_line(p)
                                if 'side panel' in p:
                                    side_panel_bg = get_colour_from_line(p)
                                if 'playlist panel' in p:
                                    BPanel = get_colour_from_line(p)
                                if 'track line' in p:
                                    lineON = get_colour_from_line(p)
                                if 'track missing' in p:
                                    lineOFF = get_colour_from_line(p)
                                if 'playing highlight' in p:
                                    lineBGplaying = get_colour_from_line(p)
                                if 'track time' in p:
                                    timeColour = get_colour_from_line(p)
                                if 'fav line' in p:
                                    starLineColour = get_colour_from_line(p)
                                if 'folder title' in p:
                                    folderTitleColour = get_colour_from_line(p)
                                if 'folder line' in p:
                                    folderLineColour = get_colour_from_line(p)
                                if 'buttons off' in p:
                                    ButtonsBG = get_colour_from_line(p)
                                if 'buttons over' in p:
                                    ButtonsOverG = get_colour_from_line(p)
                                if 'buttons active' in p:
                                    ButtonsActive = get_colour_from_line(p)
                                if 'playing time' in p:
                                    PlayingTimeColour = get_colour_from_line(p)
                                if 'track index' in p:
                                    indexColour = get_colour_from_line(p)
                                if 'track playing' in p:
                                    linePlaying = get_colour_from_line(p)
                                if 'select highlight' in p:
                                    lineBGSelect = get_colour_from_line(p)
                                if 'track artist' in p:
                                    artist_colour = get_colour_from_line(p)
                                if 'tab active line' in p:
                                    playlist_line_active = get_colour_from_line(p)
                                if 'tab line' in p:
                                    playlist_line = get_colour_from_line(p)
                                if 'tab background' in p:
                                    playlist_bg = get_colour_from_line(p)
                                if 'tab over' in p:
                                    playlist_over = get_colour_from_line(p)
                                if 'tab active background' in p:
                                    playlist_bg_active = get_colour_from_line(p)
                                if 'title info' in p:
                                    side_bar_line1 = get_colour_from_line(p)
                                if 'extra info' in p:
                                    side_bar_line2 = get_colour_from_line(p)
                                if 'scroll bar' in p:
                                    scroll_colour = get_colour_from_line(p)
                                if 'seek bar' in p:
                                    seek_bar_fill_colour = get_colour_from_line(p)
                                if 'seek bg' in p:
                                    seek_bg = get_colour_from_line(p)
                                if 'volume bar' in p:
                                    volume_bar_fill_colour = get_colour_from_line(p)
                                if 'volume bg' in p:
                                    volume_bar_bg = get_colour_from_line(p)
                                if 'mode off' in p:
                                    stepctloff = get_colour_from_line(p)
                                if 'mode over' in p:
                                    stepctlover = get_colour_from_line(p)
                                if 'mode on' in p:
                                    stepctlon = get_colour_from_line(p)
                                if 'art border' in p:
                                    art_box = get_colour_from_line(p)
                                if 'sep line' in p:
                                    sep_line = get_colour_from_line(p)
                                if 'bb line' in p:
                                    bb_line = get_colour_from_line(p)
                                if 'tb line' in p:
                                    tb_line = get_colour_from_line(p)
                                if 'bottom panel' in p:
                                    bottom_panel_colour = get_colour_from_line(p)

                                    SDL_SetTextureColorMod(c1, bottom_panel_colour[0], bottom_panel_colour[1],
                                                           bottom_panel_colour[2])
                                    SDL_SetTextureColorMod(c2, bottom_panel_colour[0], bottom_panel_colour[1],
                                                           bottom_panel_colour[2])
                                    SDL_SetTextureColorMod(c3, bottom_panel_colour[0], bottom_panel_colour[1],
                                                           bottom_panel_colour[2])
                        break
                else:
                    theme = 0
            except:
                message_box = True
                message_box_text = "Error loading theme file"

        if theme == 0:
            background = BLACK
            side_panel_bg = background
            BPanel = GREY(5)
            lineON = GREEN5
            lineOFF = GREY2
            lineBGplaying = [15, 15, 15, 255]
            timeColour = lineON
            starLineColour = [140, 140, 0, 255]
            folderTitleColour = [200, 200, 0, 255]
            folderLineColour = [140, 140, 0, 255]
            ButtonsBG = GREY(30)
            PlayingTimeColour = GREY8
            indexColour = timeColour
            linePlaying = lineON
            lineBGSelect = [15, 15, 15, 255]
            bottom_panel_colour = [8, 8, 8, 255]
            artist_colour = [50, 170, 5, 255]
            art_box = GREY(20)

            playlist_line_active = GREY(170)
            playlist_line = GREY(140)
            playlist_bg = [14, 14, 14, 255]
            playlist_over = [18, 18, 18, 255]
            playlist_bg_active = [27, 27, 27, 255]

            SDL_SetTextureColorMod(c1, bottom_panel_colour[0], bottom_panel_colour[1], bottom_panel_colour[2])
            SDL_SetTextureColorMod(c2, bottom_panel_colour[0], bottom_panel_colour[1], bottom_panel_colour[2])
            SDL_SetTextureColorMod(c3, bottom_panel_colour[0], bottom_panel_colour[1], bottom_panel_colour[2])

            side_bar_line1 = GREY(175)
            side_bar_line2 = GREY(155)
            ButtonsOver = GREY(200)
            ButtonsActive = GREY(150)

            seek_bar_fill_colour = GREY(110)  # 4
            seek_bar_outline_colour = [45, 45, 45, 255]
            volume_bar_outline_colour = [45, 45, 45, 255]
            volume_bar_fill_colour = GREY(95)
            scroll_colour = [30, 30, 30, 255]
            volume_bar_bg = [19, 19, 19, 255]
            seek_bg = [28, 28, 28, 255]
            sep_line = [16, 16, 16, 255]
            bb_line = [50, 50, 50, 255]
            tb_line = [50, 50, 50, 255]

            stepctloff = GREY(20)
            stepctlover = GREY(40)
            stepctlon = GREY(120)

            index_playing_cl = indexColour
            time_playing_cl = indexColour
            artist_playing_cl = artist_colour
            album_cl = lineON
            album_playing = artist_colour

        themeChange = False

    # ---------------------------------------------------------------------------------------------------------
    # GUI DRAWING------
    # print(UPDATE_RENDER)

    if UPDATE_RENDER > 0 and lowered != True and not resize_mode:
        if UPDATE_RENDER > 2:
            UPDATE_RENDER = 2

        SDL_SetRenderDrawColor(renderer, background[0], background[1], background[2], background[3])
        SDL_RenderClear(renderer)

        fields.clear()



        # rect = [1, 1, window_size[0] - 2, panelY + 20]
        # fields.add(rect)


        if GUI_Mode == 1 or GUI_Mode == 2:

            # Side Bar Draging----------

            if mouse_down is not True:
                side_drag = False

            rect = (window_size[0] - side_panel_size - 5, panelY, 15, window_size[1] - 90)
            fields.add(rect)

            if (coll_point(mouse_position,
                           (window_size[0] - side_panel_size - 5, panelY, 15, window_size[1] - 90)) or side_drag is True) \
                    and renamebox is False \
                    and radiobox is False \
                    and encoding_box is False \
                    and rename_playlist_box is False \
                    and new_playlist_box is False \
                    and message_box is False \
                    and pref_box.enabled is False \
                    and track_box is False \
                    and genre_box is False:

                update_layout = True

                if side_drag != True:
                    draw_sep_hl = True

                if mouse_click:
                    side_drag = True

            if side_drag is True:
                side_panel_size = window_size[0] - mouse_position[0]

            if side_panel_size < 100:
                side_panel_size = 100
            if side_panel_size > window_size[1] - 77 and album_mode is not True:
                side_panel_size = window_size[1] - 77

            if album_mode is True:
                if side_panel_size > window_size[0] - 300:
                    side_panel_size = window_size[0] - 300
                playlist_width = window_size[0] - side_panel_size - 30


            # ALBUM GALLERY RENDERING:
            if album_mode:

                rect = [playlist_width + 31, panelY, window_size[0] - playlist_width - 31,
                        window_size[1] - panelY - panelBY - 1]
                draw_rect_r(rect, side_panel_bg, True)

                # if b_info_bar:
                #     BPanel = background

                area_x = window_size[0] - playlist_width + 20

                row_len = int((area_x - album_h_gap) / (album_mode_art_size + album_h_gap))

                # print(row_len)

                compact = 40
                a_offset = 7

                l_area = playlist_width + 35
                r_area = window_size[0] - l_area
                c_area = int((window_size[0] - l_area) / 2) + l_area

                if row_len == 0:
                    row_len = 1
                dev = int((r_area - compact) / (row_len + 0))

                render_pos = 0
                album_on = 0
                if mouse_position[0] > playlist_width + 35 and mouse_position[1] < window_size[1] - panelBY:
                    album_pos_px -= mouse_wheel * 90

                if last_row != row_len:
                    last_row = row_len

                    goto_album(pctl.playlist_playing)

                render_new = False

                while render_pos < album_pos_px + window_size[1]:

                    if b_info_bar and render_pos - album_pos_px > b_info_y:
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

                            albumtitle = GREY(220)

                            if info[0] == 1 and pctl.playing_state != 0:
                                draw_rect((x - 12, y - 10), (album_mode_art_size + 24, album_mode_art_size + 60),
                                          [200, 200, 200, 15], True)

                            draw_rect((x, y), (album_mode_art_size, album_mode_art_size), [40, 40, 40, 50], True)

                            gall_ren.render(default_playlist[album_dex[album_on]], (x, y))

                            if info[0] != 1 and pctl.playing_state != 0 and dim_art:
                                draw_rect((x, y), (album_mode_art_size, album_mode_art_size), [0, 0, 0, 110], True)
                                albumtitle = GREY(150)

                            if mouse_click and not focused and coll_point(mouse_position, (
                            x, y, album_mode_art_size, album_mode_art_size + 40)) and panelY < mouse_position[1] < \
                                            window_size[1] - panelBY:

                                if info[0] == 1 and pctl.playing_state == 2:
                                    pctl.play()
                                elif info[0] == 1 and pctl.playing_state > 0:
                                    playlist_position = album_dex[album_on]
                                else:
                                    playlist_position = album_dex[album_on]
                                    pctl.jump(default_playlist[album_dex[album_on]], album_dex[album_on])

                                pctl.show_current()

                            line = master_library[default_playlist[album_dex[album_on]]]['artist']
                            draw_text2((x, y + album_mode_art_size + 8),
                                       line,
                                       albumtitle,
                                       11,
                                       album_mode_art_size,
                                       3,
                                       default_playlist[album_dex[album_on]]
                                       )

                            line = master_library[default_playlist[album_dex[album_on]]]['album']
                            draw_text2((x, y + album_mode_art_size + 10 + 13),
                                       line,
                                       albumtitle,
                                       12,
                                       album_mode_art_size - 5,
                                       3,
                                       default_playlist[album_dex[album_on]]
                                       )

                            album_on += 1

                        if album_on > len(album_dex):
                            break
                        render_pos += album_mode_art_size + album_v_gap

                draw_rect((0, 0), (window_size[0], panelY), background, True)

                # if b_info_bar:
                #     x = playlist_width + 31
                #     w = window_size[0] - x
                #     b_info_y = int(window_size[1] * 0.7)
                #     y = b_info_y
                #     h = window_size[1] - y - 51
                #
                #     if h < 5:
                #         h = 5
                #
                #     draw_rect_r((x, y, w, h), background, True)
                #     draw_rect_r((x, y, w, h), [255, 255, 255, 3], True)
                #     draw_line(x, y, x + w, y, GREY(50))
                #
                #     box = h - 20
                #
                #     showc = display_album_art(pctl.track_queue[pctl.queue_step],
                #                               (window_size[0] - 15 - box, y + 10), (box, box))



            if True:

                if len(items_loaded) > 0:
                    pctl.multi_playlist[load_to[0]][2] += items_loaded
                    del load_to[0]
                    items_loaded = []
                    UPDATE_RENDER += 1

                w = 0

                # playlist hit test
                if coll_point(mouse_position, (playlist_left, playlist_top, playlist_width, window_size[1] - panelY - panelBY)) and not dragmode and (
                                            mouse_click or mouse_wheel != 0 or right_click or middle_click or mouse_up or mouse_down):
                    renplay += 2


                if renplay > 0:

                    renplay -= 1

                    SDL_SetRenderTarget(renderer, ttext)
                    rect = (0, panelY, playlist_width + 31, window_size[1])
                    if side_panel_enable is False:
                        rect = (0, panelY, window_size[0], window_size[1])
                    draw_rect_r(rect, BPanel, True)

                    if not custom_line_mode:
                        highlight_left = playlist_left
                        highlight_right = playlist_width
                    else:
                        highlight_left = playlist_left - 20 + highlight_x_offset + highlight_left_custom
                        highlight_right = playlist_width + 30 - highlight_right_custom - highlight_x_offset


                    if len(default_playlist) == 0:

                        draw_text((int(playlist_width / 2) + 10, int((window_size[1] - panelY - panelBY) * 0.65), 2), "Playlist is empty", lineOFF, 13 )
                        draw_text((int(playlist_width / 2) + 10, int((window_size[1] - panelY - panelBY) * 0.65 + 30), 2), "Drag and drop files to import", lineOFF, 13 )

                    elif playlist_position > len(default_playlist) - 1:

                        draw_text((int(playlist_width / 2) + 10, int(window_size[1] * 0.15), 2), "End of Playlist", lineOFF, 13 )


                    for i in range(playlist_view_length + 1):

                        move_on_title = False

                        if playlist_position < 0:
                            playlist_position = 0
                        if len(default_playlist) <= i + playlist_position:
                            break

                        # fade other tracks in ablbum mode
                        albumfade = 255
                        if album_mode and pctl.playing_state != 0 and dim_art and \
                                        master_library[default_playlist[i + playlist_position]][
                                            'parent'] != master_library[pctl.track_queue[pctl.queue_step]]['parent']:
                            albumfade = 150

                        if row_alt and w % 2 == 0:
                            draw_rect((playlist_left, playlist_top + playlist_row_height * w),
                                      (playlist_width, playlist_row_height - 1), [0, 0, 0, 30], True)
                        # Folder Break
                        if (i + playlist_position == 0 or master_library[default_playlist[i + playlist_position]][
                            'parent'] != master_library[default_playlist[i + playlist_position - 1]]['parent']) and \
                                        pctl.multi_playlist[pctl.playlist_active][4] == 0 and break_enable:

                            line = master_library[default_playlist[i + playlist_position]]['parent']
                            if thick_lines:
                                draw_text((playlist_width + playlist_left,
                                           playlist_row_height - 16 + playlist_top + playlist_row_height * w, 1), line,
                                          alpha_mod(folderTitleColour, albumfade),
                                          11)
                            else:
                                draw_text((playlist_width + playlist_left,
                                           playlist_row_height - 16 + playlist_top + playlist_row_height * w, 1), line,
                                          alpha_mod(folderTitleColour, albumfade),
                                          11)
                            draw_line(playlist_left, playlist_top + playlist_row_height - 1 + playlist_row_height * w,
                                      playlist_width + playlist_left,
                                      playlist_top + playlist_row_height - 1 + playlist_row_height * w, folderLineColour)

                            if playlist_hold is True and coll_point(mouse_position, (
                            playlist_left, playlist_top + 31 + playlist_row_height * w, playlist_width,
                            playlist_row_height)):
                                # draw_line(playlist_left, playlist_top + 15 + playlist_row_height * w, playlist_width + playlist_left,
                                #       playlist_top + 15 + playlist_row_height * w, [35, 45, 90, 255])
                                if mouse_up and key_shift_down:
                                    move_on_title = True

                            w += 1

                        # test if line hit
                        if (mouse_click or right_click or middle_click) and coll_point(mouse_position, (
                            playlist_left + 10, playlist_top + playlist_row_height * w, playlist_width,
                            playlist_row_height - 1)) and mouse_position[1] < window_size[1] - panelBY:
                            line_hit = True
                        else:
                            line_hit = False
                        if scroll_enable and mouse_position[0] < 30:
                            line_hit = False

                        if key_shift_down is False and d_mouse_click and line_hit and i + playlist_position == playlist_selected:

                            click_time -= 1.5
                            pctl.jump(default_playlist[i + playlist_position], i + playlist_position)

                            if album_mode:
                                goto_album(pctl.playlist_playing)

                        this_line_playing = False

                        if len(pctl.track_queue) > 1 and pctl.track_queue[pctl.queue_step] == \
                                default_playlist[i + playlist_position]: # and i + playlist_position == pctl.playlist_playing:
                            draw_rect((highlight_left, playlist_top + playlist_row_height * w),
                                      (highlight_right, playlist_row_height - 1), lineBGplaying, True)
                            this_line_playing = True

                        # if (i + playlist_position) % 2 == 0:
                        #     draw_rect((playlist_left, playlist_top + playlist_row_height * w), (playlist_width, playlist_row_height - 1), [0,0,0,20], True)

                        if default_playlist[i + playlist_position] == broadcast_index and broadcast and not join_broadcast:
                            draw_rect((playlist_left, playlist_top + playlist_row_height * w),
                                      (playlist_width, playlist_row_height - 1), [10, 20, 180, 70], True)

                        if middle_click and line_hit:
                            pctl.force_queue.append([default_playlist[i + playlist_position],
                                                     i + playlist_position, pctl.playlist_active])

                        for item in pctl.force_queue:
                            if default_playlist[i + playlist_position] == item[0] and item[1] == i + playlist_position:
                                draw_rect((playlist_left, playlist_top + playlist_row_height * w),
                                          (playlist_width, playlist_row_height - 1), [30, 170, 30, 35],
                                          True)

                        if right_click and line_hit:
                            if i + playlist_position not in shift_selection:
                                shift_selection = [i + playlist_position]

                        if mouse_click and key_shift_down is False and line_hit:
                            # shift_selection = []
                            shift_selection = [i + playlist_position]
                        if mouse_click and line_hit:
                            quick_drag = True

                        if (mouse_click and key_shift_down is False and line_hit or
                                    playlist_selected == i + playlist_position):
                            draw_rect((highlight_left, playlist_top + playlist_row_height * w),
                                      (highlight_right, playlist_row_height - 1), lineBGSelect, True)
                            playlist_selected = i + playlist_position

                        # Shift Move Selection
                        if move_on_title or mouse_up and playlist_hold is True and coll_point(mouse_position, (
                        playlist_left, playlist_top + playlist_row_height * w, playlist_width, playlist_row_height)):

                            if i + playlist_position != playlist_hold_position and i + playlist_position not in shift_selection:
                                if len(shift_selection) == 0:
                                    temp_index = default_playlist[playlist_hold_position]

                                    del default_playlist[playlist_hold_position]

                                    if move_on_title:
                                        if i + playlist_position < playlist_hold_position:
                                            default_playlist.insert(i + playlist_position, temp_index)
                                        else:
                                            default_playlist.insert(i + playlist_position - 1, temp_index)

                                    else:
                                        if i + playlist_position < playlist_hold_position:
                                            default_playlist.insert(i + playlist_position + 1, temp_index)
                                        else:
                                            default_playlist.insert(i + playlist_position, temp_index)

                                    renplay += 1
                                    playlist_selected = i + playlist_position

                                else:
                                    count = 0
                                    temp_ref = []
                                    if move_on_title:
                                        count -= 1
                                    for a in range(0, i + playlist_position):
                                        print(a)
                                        if a not in shift_selection:
                                            count += 1
                                    for b in reversed(range(len(default_playlist))):
                                        if b in shift_selection:
                                            temp_ref.append(default_playlist[b])
                                            del default_playlist[b]

                                    for c in temp_ref:
                                        default_playlist.insert(count + 1, c)
                                    shift_selection = []

                        if mouse_down and playlist_hold and coll_point(mouse_position, (
                        playlist_left, playlist_top + playlist_row_height * w, playlist_width,
                        playlist_row_height)) and playlist_hold_position != i + playlist_position:
                            draw_line(playlist_left, playlist_top + playlist_row_height + playlist_row_height * w,
                                      playlist_width + playlist_left,
                                      playlist_top + playlist_row_height + playlist_row_height * w, [35, 45, 90, 255])

                        # Shift click actions
                        if mouse_click and line_hit and key_shift_down:

                            if i + playlist_position != playlist_selected:

                                start_s = i + playlist_position
                                end_s = playlist_selected
                                if end_s < start_s:
                                    end_s, start_s = start_s, end_s
                                for y in range(start_s, end_s + 1):
                                    if y not in shift_selection:
                                        shift_selection.append(y)
                                shift_selection.sort()

                            # else:
                            playlist_hold = True
                            playlist_hold_position = i + playlist_position

                        # Multi Select Highlight
                        if i + playlist_position in shift_selection and i + playlist_position != playlist_selected:
                            draw_rect((highlight_left, playlist_top + playlist_row_height * w),
                                      (highlight_right, playlist_row_height), lineBGSelect, True)

                        if right_click and line_hit and mouse_position[0] > playlist_left + 10:
                            track_menu.activate(default_playlist[i + playlist_position])

                            playlist_selected = i + playlist_position

                        # time.sleep(0.1)
                        if custom_line_mode:

                            timec = timeColour
                            titlec = lineON
                            indexc = indexColour
                            artistc = artist_colour
                            albumc = album_cl

                            if this_line_playing is True:
                                timec = time_playing_cl
                                titlec = linePlaying
                                indexc = index_playing_cl
                                artistc = artist_playing_cl
                                albumc = album_playing

                            if master_library[default_playlist[i + playlist_position]]['found'] is False:
                                timec = lineOFF
                                titlec = lineOFF
                                indexc = lineOFF
                                artistc = lineOFF
                                albumc = lineOFF

                            offs = 0

                            for item in cust:

                                if item[0] == 't':
                                    lineTime = timeColour
                                    lineColour = lineON
                                    line = get_display_time(master_library[default_playlist[i + playlist_position]]['length'])
                                    draw_text((item[1], playlist_text_offset + playlist_top + playlist_row_height * w,
                                               item[2]), line, alpha_mod(timec, albumfade), 12)

                                elif item[0] == 'i':
                                    line = str(master_library[default_playlist[i + playlist_position]]['tracknumber'])
                                    line = line.split("/", 1)[0]
                                    if dd_index and len(line) == 1:
                                        line = "0" + line
                                    line += item[3]

                                    draw_text((item[1], playlist_text_offset + playlist_top + playlist_row_height * w,
                                               item[2]), line, alpha_mod(indexc, albumfade), 12)

                                elif item[0] == 'o':
                                    key = master_library[default_playlist[i + playlist_position]]['title'] + \
                                          master_library[default_playlist[i + playlist_position]]['filename']
                                    total = 0
                                    ratio = 0
                                    if (key in star_library) and star_library[key] != 0 and \
                                                    master_library[default_playlist[i + playlist_position]][
                                                        'length'] != 0:
                                        total = star_library[key]
                                        ratio = total / master_library[default_playlist[i + playlist_position]]['length']

                                    line = str(int(ratio))
                                    # if True:
                                    #     if dd_index and len(line) == 1:
                                    #         line = "0" + line

                                    draw_text((item[1], playlist_text_offset + playlist_top + playlist_row_height * w,
                                               item[2]), line, alpha_mod(indexc, albumfade), 12)

                                elif item[0] == 'c':
                                    line = item[3]
                                    draw_text((item[1], playlist_text_offset + playlist_top + playlist_row_height * w,
                                               item[2]), line, alpha_mod(titlec, albumfade), 12)

                                elif item[0] == 'a':
                                    line = master_library[default_playlist[i + playlist_position]]['artist']

                                    offs += draw_text2((item[1],
                                                        playlist_text_offset + playlist_top + playlist_row_height * w,
                                                        item[2]),
                                                       line,
                                                       alpha_mod(artistc, albumfade),
                                                       12,
                                                       item[3],
                                                       1,
                                                       default_playlist[i + playlist_position])

                                elif item[0] == 'n':
                                    line = master_library[default_playlist[i + playlist_position]]['title']

                                    offs += draw_text2((item[1],
                                                        playlist_text_offset + playlist_top + playlist_row_height * w,
                                                        item[2]),
                                                       line,
                                                       alpha_mod(titlec, albumfade),
                                                       12,
                                                       item[3],
                                                       2,
                                                       default_playlist[i + playlist_position])

                                elif item[0] == 'b':
                                    line = master_library[default_playlist[i + playlist_position]]['album']

                                    offs = draw_text2((item[1],
                                                       playlist_text_offset + playlist_top + playlist_row_height * w,
                                                       item[2]),
                                                      line,
                                                      alpha_mod(albumc, albumfade),
                                                      12,
                                                      item[3],
                                                      3,
                                                      default_playlist[i + playlist_position])

                                elif item[0] == 'd':
                                    line = str(master_library[default_playlist[i + playlist_position]]['date'])

                                    offs = draw_text2((item[1],
                                                       playlist_text_offset + playlist_top + playlist_row_height * w,
                                                       item[2]),
                                                      line,
                                                      alpha_mod(albumc, albumfade),
                                                      12,
                                                      item[3],
                                                      3,
                                                      default_playlist[i + playlist_position])

                                elif item[0] == 's':

                                    ratio = 0

                                    index = default_playlist[i + playlist_position]
                                    key = master_library[index]['title'] + master_library[index]['filename']
                                    if star_lines and (key in star_library) and star_library[key] != 0 and \
                                                    master_library[index][
                                                        'length'] != 0:
                                        total = star_library[key]
                                        ratio = total / master_library[index]['length']
                                        if ratio > 15:
                                            ratio = 15
                                        if ratio > 0.55:
                                            ratio = int(ratio * 4)

                                            draw_line(item[1] - ratio,
                                                      playlist_text_offset + playlist_top + 8 + playlist_row_height * w,
                                                      item[1],
                                                      playlist_text_offset + playlist_top + 8 + playlist_row_height * w,
                                                      alpha_mod(starLineColour, albumfade))

                        if not custom_line_mode:
                            lineTime = timeColour
                            lineColour = lineON

                            timec = timeColour
                            titlec = lineON
                            indexc = indexColour
                            artistc = artist_colour
                            albumc = album_cl

                            if this_line_playing is True:
                                timec = time_playing_cl
                                titlec = linePlaying
                                indexc = index_playing_cl
                                artistc = artist_playing_cl
                                albumc = album_playing

                            if master_library[default_playlist[i + playlist_position]]['found'] is False:
                                timec = lineOFF
                                titlec = lineOFF
                                indexc = lineOFF
                                artistc = lineOFF
                                albumc = lineOFF

                            indexoffset = 0
                            artistoffset = 0
                            indexLine = ""
                            if master_library[default_playlist[i + playlist_position]]['artist'] != "" or \
                                            master_library[default_playlist[i + playlist_position]]['title'] != "":
                                line = str(master_library[default_playlist[i + playlist_position]]['tracknumber'])
                                line = line.split("/", 1)[0]
                                if len(line) > 0:
                                    line += ". "
                                if dd_index and len(line) == 3:
                                    line = "0" + line
                                if len(line) == 3:
                                    line += "  "

                                if len(line) > 1:
                                    indexoffset = 21

                                indexLine = line

                                line = ""
                                if dd_index:
                                    indexoffset += 2

                                indexoffset += playlist_line_x_offset

                                if master_library[default_playlist[i + playlist_position]]['artist'] != "":
                                    if split_line and artist_colour != lineON:
                                        line0 = master_library[default_playlist[i + playlist_position]]['artist']

                                        artistoffset = draw_text2((playlist_left + indexoffset,
                                                                   playlist_text_offset + playlist_top + playlist_row_height * w),
                                                                  line0,
                                                                  alpha_mod(artistc, albumfade),
                                                                  12,
                                                                  300,
                                                                  1,
                                                                  default_playlist[i + playlist_position])

                                        line = master_library[default_playlist[i + playlist_position]]['title']
                                    else:
                                        line += master_library[default_playlist[i + playlist_position]]['artist'] + " - " + \
                                                master_library[default_playlist[i + playlist_position]]['title']
                                else:
                                    line += master_library[default_playlist[i + playlist_position]]['title']

                            else:
                                line = \
                                os.path.splitext((master_library[default_playlist[i + playlist_position]]['filename']))[
                                    0]
                            trunk = False

                            ratio = 0
                            index = default_playlist[i + playlist_position]
                            key = master_library[index]['title'] + master_library[index]['filename']
                            if star_lines and (key in star_library) and star_library[key] != 0 and master_library[index][
                                'length'] != 0:
                                total = star_library[key]
                                ratio = total / master_library[index]['length']
                                if ratio > 15:
                                    ratio = 15
                                if ratio > 0.55:
                                    ratio = int(ratio * 4)

                                    draw_line(playlist_width - playlist_line_x_offset + playlist_left - ratio - 40,
                                              playlist_text_offset + playlist_top + 8 + playlist_row_height * w,
                                              playlist_width - playlist_line_x_offset + playlist_left - 37,
                                              playlist_text_offset + playlist_top + 8 + playlist_row_height * w,
                                              alpha_mod(starLineColour, albumfade))

                            draw_text((playlist_left + playlist_line_x_offset,
                                       playlist_text_offset + playlist_top + playlist_row_height * w), indexLine,
                                      alpha_mod(indexc, albumfade), 12)

                            if artistoffset != 0:
                                artistoffset += 7

                            draw_text2((playlist_left + indexoffset + artistoffset,
                                        playlist_text_offset + playlist_top + playlist_row_height * w),
                                       line,
                                       alpha_mod(titlec, albumfade),
                                       12,
                                       playlist_width - 71 - artistoffset - ratio,
                                       2,
                                       default_playlist[i + playlist_position])

                            line = get_display_time(master_library[default_playlist[i + playlist_position]]['length'])

                            draw_text((playlist_width + playlist_left - playlist_line_x_offset,
                                       playlist_text_offset + playlist_top + playlist_row_height * w, 1), line,
                                      alpha_mod(timec, albumfade), 12)

                        w += 1
                        if w > playlist_view_length:
                            break

                    if (right_click and playlist_top + 40 + playlist_row_height * w < mouse_position[1] < window_size[
                        1] - 55 and
                                mouse_position[0] > playlist_left + 15):
                        playlist_menu.activate()

                    if mouse_wheel != 0 and window_size[1] - 50 > mouse_position[1] > 25 + playlist_top:

                        if album_mode and mouse_position[0] > playlist_width + 40:
                            pass
                        else:

                            playlist_position -= mouse_wheel * 3
                            # if playlist_view_length > 15:
                            #     playlist_position -= mouse_wheel
                            if playlist_view_length > 40:
                                playlist_position -= mouse_wheel

                            if playlist_position > len(default_playlist):
                                playlist_position = len(default_playlist)
                            if playlist_position < 1:
                                playlist_position = 0

                SDL_SetRenderTarget(renderer, None)
                SDL_RenderCopy(renderer, ttext, None, abc)

                if mouse_down is False:
                    playlist_hold = False

                # ------------------------------------------------
                # Scroll Bar



                if scroll_enable:

                    sy = 31
                    ey = window_size[1] - 30 - 22



                    if len(default_playlist) < 50:
                        sbl = 85
                        if len(default_playlist) == 0:
                            sbp = panelY
                    else:
                        sbl = 70

                    fields.add((2, sbp, 20, sbl))
                    if coll_point(mouse_position, (0, panelY, 28, ey - panelY)) and (mouse_down or right_click):

                        renplay += 1
                        if right_click:
                            sbp = mouse_position[1] - int(sbl/2)
                            if sbp + sbl > ey:
                                sbp = ey - sbl
                            elif sbp < panelY:
                                sbp = panelY
                            per = (sbp - panelY) / (ey - panelY - sbl)
                            playlist_position = int(len(default_playlist) * per)

                            if playlist_position < 0:
                                playlist_position = 0
                        elif mouse_position[1] < sbp:
                            playlist_position -= 2
                        elif mouse_position[1] > sbp + sbl:
                            playlist_position += 2
                        elif mouse_click:


                            p_y = pointer(c_int(0))
                            p_x = pointer(c_int(0))
                            SDL_GetGlobalMouseState(p_x,p_y)

                            scroll_hold = True
                            scroll_point = p_y.contents.value #mouse_position[1]
                            scroll_bpoint = sbp

                    if not mouse_down:
                        scroll_hold = False

                    if scroll_hold and not mouse_click:
                        renplay += 1
                        p_y = pointer(c_int(0))
                        p_x = pointer(c_int(0))
                        SDL_GetGlobalMouseState(p_x,p_y)
                        sbp = p_y.contents.value - (scroll_point - scroll_bpoint) #mouse_position[1] - (scroll_point - scroll_bpoint)
                        if sbp + sbl > ey:
                            sbp = ey - sbl
                        elif sbp < panelY:
                            sbp = panelY
                        per = (sbp - panelY) / (ey - panelY - sbl)
                        playlist_position = int(len(default_playlist) * per)


                    else:
                        if len(default_playlist) > 0:
                            per = playlist_position / len(default_playlist)
                            sbp = int((ey - panelY - sbl) * per) + panelY + 1

                    draw_rect((1, sbp), (14, sbl), scroll_colour, True)

                    if (coll_point(mouse_position, (2, sbp, 20, sbl)) and mouse_position[0] != 0) or scroll_hold:
                        draw_rect((1, sbp), (14, sbl), [255, 255, 255, 11], True)

                # Switch Vis:

                if mouse_click and coll_point(mouse_position, (window_size[0] - 130 - offset_extra, 0, 130, panelY)):
                    if vis == 0:
                        vis = 1
                        turbo = True
                    elif vis == 1:
                        vis = 2
                    elif vis == 2:
                        vis = 0
                        turbo = False
                # --------------------------------------------
                # ALBUM ART

                if side_panel_enable:
                    if album_mode:
                        pass
                        # if b_info_bar:
                        #     # draw_rect((0,window_size[1] - b_panel_size - panelBY), (playlist_width + 31, b_panel_size), background, True)
                        #     showc = display_album_art(pctl.track_queue[pctl.queue_step], (20, window_size[1] - panelBY - b_panel_size + 20), ( b_panel_size - 30, b_panel_size - 30))
                    else:

                        rect = [playlist_width + 31, panelY, window_size[0] - playlist_width - 30,
                                window_size[1] - panelY - panelBY]
                        draw_rect_r(rect, side_panel_bg, True)

                        showc = []

                        boxx = window_size[0] - playlist_width - 32 - 18
                        boxy = window_size[1] - 160
                        box = boxx

                        # CURRENT

                        if mouse_click and (coll_point(mouse_position, (
                            playlist_width + 40, panelY + boxx + 5, boxx, window_size[1] - boxx - 90))):

                            pctl.show_current()

                            if album_mode:
                                goto_album(pctl.playlist_playing)
                            UPDATE_RENDER += 1

                        if len(pctl.track_queue) > 0:

                            # Bluring of sidebar background, not fully implemented, uncomment these 3 lines to enable.

                            # nt = display_album_art(master_library[pctl.track_queue[pctl.queue_step]]['filepath'], (0,0), (0,0), mode="RETURN", offset=1)
                            # blur_bg( (playlist_width + 32, 32), (316,316),nt,0 )
                            # draw_rect( (playlist_width + 32, 32), (316,316), [0,0,0,210], True )

                            if coll_point(mouse_position, (playlist_width + 40, 38, box, box)) and mouse_click is True:
                                display_album_art(pctl.track_queue[pctl.queue_step], (0, 0), (0, 0),
                                                  mode="OFFSET", offset=1)

                            if coll_point(mouse_position, (
                                playlist_width + 40, 38, box, box)) and right_click is True and pctl.playing_state > 0:
                                display_album_art(pctl.track_queue[pctl.queue_step], (0, 0), (0, 0), mode="OPEN")
                        if 3 > pctl.playing_state > 0:

                            if side_drag:

                                showc = display_album_art(pctl.track_queue[pctl.queue_step],
                                                          (playlist_width + 40, 38), (box, box), mode="fast")

                            else:
                                showc = display_album_art(pctl.track_queue[pctl.queue_step],
                                                          (playlist_width + 40, 38), (box, box))
                        draw_rect((playlist_width + 40, 38), (box + 1, box + 1), art_box)

                        rect = (playlist_width + 40, 38, box, box)
                        fields.add(rect)

                        if len(showc) > 1 and showc[0] > 0 and coll_point(mouse_position, rect) \
                                and renamebox is False \
                                and radiobox is False \
                                and encoding_box is False \
                                and pref_box.enabled is False \
                                and rename_playlist_box is False \
                                and new_playlist_box is False \
                                and message_box is False \
                                and track_box is False \
                                and genre_box is False:

                            if showc[2] is False:
                                showc[1] -= 1

                            line = ""
                            if showc[2] is True and showc[1] == 1:
                                line += 'A '
                            else:
                                line += 'E '
                            line += str(showc[1]) + "/" + str(showc[0])

                            xoff = 0
                            # if len(line) > 5:
                            #     xoff = (len(line) - 5) * 6
                            xoff = text_calc(line, 12)[0] + 12


                            draw_rect((playlist_width + 40 + box - xoff, 36 + box - 19), (xoff, 18),
                                      [0, 0, 0, 190], True)

                            draw_text((playlist_width + 40 + box - 6, 36 + box - 18, 1), line, [220, 220, 220, 220], 12)

                        if pctl.playing_state > 0:
                            if len(pctl.track_queue) > 0:

                                block3 = False
                                block4 = False
                                block5 = False
                                block6 = False

                                title = ""
                                album = ""
                                artist = ""
                                ext = ""
                                date = ""
                                sample = ""

                                if pctl.playing_state < 3:

                                    title = master_library[pctl.track_queue[pctl.queue_step]]['title']
                                    album = master_library[pctl.track_queue[pctl.queue_step]]['album']
                                    artist = master_library[pctl.track_queue[pctl.queue_step]]['artist']
                                    ext = master_library[pctl.track_queue[pctl.queue_step]]['ext']
                                    date = master_library[pctl.track_queue[pctl.queue_step]]['date']
                                    genre = master_library[pctl.track_queue[pctl.queue_step]]['genre']
                                    sample = str(master_library[pctl.track_queue[pctl.queue_step]]['sample'])
                                else:

                                    title = tag_meta

                                if side_panel_text_align == 1:

                                    # --------------------------------
                                    if 38 + box + 126 > window_size[1] + 52:
                                        block6 = True
                                    if block6 != True:
                                        if 38 + box + 126 > window_size[1] + 37:
                                            block5 = True

                                        if 38 + box + 126 > window_size[1] + 10:
                                            block4 = True
                                        if 38 + box + 126 > window_size[1] - 31:
                                            block3 = True

                                        if 38 + box + 126 > window_size[1] - 70:

                                            block1 = 38 + box + 20
                                            block2 = window_size[1] - 70 - 36

                                        else:
                                            block1 = int((window_size[1] - 38 - box - panelBY) / 2) + 38 + box - 50
                                            block2 = int((window_size[1] - 38 - box - panelBY) / 2) + 38 + box + 5

                                        if block4 is False:

                                            if block3 is True:
                                                block1 -= 14

                                            if title != "":
                                                playing_info = title
                                                playing_info = trunc_line(playing_info, 12,
                                                                          window_size[0] - playlist_width - 53)
                                                draw_text((playlist_width + 30 + int(side_panel_size / 2), block1, 2),
                                                          playing_info, side_bar_line1, 12)

                                            if artist != "":
                                                playing_info = artist
                                                playing_info = trunc_line(playing_info, 11,
                                                                          window_size[0] - playlist_width - 54)
                                                draw_text((playlist_width + 30 + int(side_panel_size / 2), block1 + 17, 2),
                                                          playing_info, side_bar_line2, 11)
                                        else:
                                            block1 -= 14

                                            line = ""
                                            if artist != "":
                                                line += artist
                                            if title != "":
                                                if line != "":
                                                    line += " - "
                                                line += title
                                            line = trunc_line(line, 11, window_size[0] - playlist_width - 53)
                                            draw_text((playlist_width + 30 + int(side_panel_size / 2), block1, 2), line,
                                                      side_bar_line1, 11)

                                        if block3 == False:

                                            if album != "":
                                                playing_info = album
                                                playing_info = trunc_line(playing_info, 11,
                                                                          window_size[0] - playlist_width - 53)
                                                draw_text((playlist_width + 30 + int(side_panel_size / 2), block2, 2),
                                                          playing_info, side_bar_line2, 11)

                                            if date != "":
                                                playing_info = date
                                                if genre != "":
                                                    playing_info += " | " + genre
                                                playing_info = trunc_line(playing_info, 11,
                                                                          window_size[0] - playlist_width - 53)
                                                draw_text((playlist_width + 30 + int(side_panel_size / 2), block2 + 18, 2),
                                                          playing_info, side_bar_line2, 11)


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
                                                line = trunc_line(line, 11, window_size[0] - playlist_width - 53)
                                                draw_text((playlist_width + 30 + int(side_panel_size / 2), block2 + 35, 2),
                                                          line, side_bar_line2, 11)
                                    # Topline
                                    elif broadcast != True:
                                        line = ""
                                        if artist != "":
                                            line += artist
                                        if title != "":
                                            if line != "":
                                                line += " - "
                                            line += title
                                        # line = trunc_line(line, 11, window_size[0] - playlist_width - 53)
                                        offset_extra = 0
                                        if draw_border:
                                            offset_extra = 61

                                        if turbo:
                                            draw_text((window_size[0] - 104 - offset_extra, 8, 1), line, side_bar_line1,
                                                      11)

                                        else:
                                            draw_text((window_size[0] - 15 - offset_extra, 8, 1), line, side_bar_line1,
                                                      11)



                                else:
                                    # -------------------------------

                                    if 38 + box + 126 > window_size[1] + 52:
                                        block6 = True
                                    if block6 != True:
                                        if 38 + box + 126 > window_size[1] + 37:
                                            block5 = True

                                        if 38 + box + 126 > window_size[1] + 10:
                                            block4 = True
                                        if 38 + box + 126 > window_size[1] - 39:
                                            block3 = True

                                        if 38 + box + 126 > window_size[1] - 70:

                                            block1 = 38 + box + 20
                                            block2 = window_size[1] - 70 - 36

                                        else:
                                            block1 = 38 + box + 20
                                            block2 = 38 + box + 90

                                        if block4 is False:

                                            if block3 is True:
                                                block1 -= 14

                                            if title != "":
                                                playing_info = title
                                                playing_info = trunc_line(playing_info, 12,
                                                                          window_size[0] - playlist_width - 53)
                                                draw_text((playlist_width + 39, block1 + 2), playing_info, side_bar_line1,
                                                          13, max=side_panel_size - 20)

                                            if artist != "":
                                                playing_info = artist
                                                playing_info = trunc_line(playing_info, 11,
                                                                          window_size[0] - playlist_width - 54)
                                                draw_text((playlist_width + 39, block1 + 17 + 4), playing_info, side_bar_line2,
                                                          12)
                                        else:
                                            block1 -= 14

                                            line = ""
                                            if artist != "":
                                                line += artist
                                            if title != "":
                                                if line != "":
                                                    line += " - "
                                                line += title
                                            line = trunc_line(line, 11, window_size[0] - playlist_width - 53)
                                            draw_text((playlist_width + 39, block1), line, side_bar_line1, 11)

                                        if block3 == False:

                                            if album != "":
                                                playing_info = album
                                                playing_info = trunc_line(playing_info, 11,
                                                                          window_size[0] - playlist_width - 53)
                                                draw_text((playlist_width + 39, block2), playing_info, side_bar_line2,
                                                          11)

                                            if date != "":
                                                playing_info = date
                                                if genre != "":
                                                    playing_info += " | " + genre
                                                playing_info = trunc_line(playing_info, 11,
                                                                          window_size[0] - playlist_width - 53)
                                                draw_text((playlist_width + 39, block2 + 18), playing_info, side_bar_line2,
                                                          11)

                                            if ext != "":
                                                playing_info = ext  # + " | " + sample
                                                playing_info = trunc_line(playing_info, 11,
                                                                          window_size[0] - playlist_width - 53)
                                                draw_text((playlist_width + 39, block2 + 36), playing_info, side_bar_line2,
                                                          11)
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
                                                line = trunc_line(line, 11, window_size[0] - playlist_width - 53)
                                                draw_text((playlist_width + 39, block2 + 35), line, side_bar_line2, 11)
                                    # Topline
                                    # elif broadcast != True:
                                    #     line = ""
                                    #     if artist != "":
                                    #         line += artist
                                    #     if title != "":
                                    #         if line != "":
                                    #             line += " - "
                                    #         line += title
                                    #     # line = trunc_line(line, 11, window_size[0] - playlist_width - 53)
                                    #     offset_extra = 0
                                    #     if draw_border:
                                    #         offset_extra = 61
                                    #
                                    #     l_max = window_size[0] - m_l - 10
                                    #
                                    #
                                    #     if turbo:
                                    #         draw_text((window_size[0] - 104 - offset_extra, 8, 1), line, side_bar_line1,
                                    #                   11, max=l_max - 75)
                                    #
                                    #     else:
                                    #         draw_text((window_size[0] - 15 - offset_extra, 8, 1), line, side_bar_line1,
                                    #                   11, max=l_max)

                # else:
                #     if broadcast != True and pctl.playing_state > 0:
                #         if pctl.playing_state < 3:
                #             title = master_library[pctl.track_queue[pctl.queue_step]]['title']
                #             artist = master_library[pctl.track_queue[pctl.queue_step]]['artist']
                #         else:
                #             title = tag_meta
                #         line = ""
                #         if artist != "":
                #             line += artist
                #         if title != "":
                #             if line != "":
                #                 line += " - "
                #             line += title
                #         offset_extra = 0
                #         if draw_border:
                #             offset_extra = 61
                #
                #         # line = trunc_line(line, 11, window_size[0] - playlist_width - 53)
                #         l_max = window_size[0] - m_l - 10
                #         if turbo:
                #             draw_text((window_size[0] - 100 - offset_extra, 8, 1), line, side_bar_line1, 11, max=l_max - 75)
                #         else:
                #             draw_text((window_size[0] - 15 - offset_extra, 8, 1), line, side_bar_line1, 11, max=l_max)

                if tb_line != BPanel and GUI_Mode == 1:
                    draw_line(0, panelY, window_size[0], panelY, tb_line)

                # Seperation Line Drawing
                if side_panel_enable:

                    # Draw Highlight when draging
                    if side_drag is True:
                        draw_line(window_size[0] - side_panel_size + 1, panelY + 1, window_size[0] - side_panel_size + 1,
                                  window_size[1] - 50, GREY(50))

                    # Draw Highlight when mouse over
                    if draw_sep_hl:

                        draw_line(window_size[0] - side_panel_size + 1, panelY + 1, window_size[0] - side_panel_size + 1,
                                  window_size[1] - 50, [100, 100, 100, 70])
                        draw_sep_hl = False

                # Normal Drawing
                if side_panel_enable:
                    draw_line(playlist_width + 30, panelY + 1, playlist_width + 30, window_size[1] - 30, sep_line)


                # New Bottom Bar

                # BOTTOM BAR!

                if GUI_Mode == 1:  # not compact_bar:

                    draw_rect((0, window_size[1] - panelBY), (window_size[0], panelBY), bottom_panel_colour, True)
                    draw_rect(seek_bar_position, seek_bar_size, seek_bg, True)

                    draw_line(0, window_size[1] - panelBY, 299, window_size[1] - panelBY, bb_line)
                    draw_line(299, window_size[1] - panelBY, 299, window_size[1] - panelBY + seek_bar_size[1], bb_line)
                    draw_line(300, window_size[1] - panelBY + seek_bar_size[1], window_size[0], window_size[1] - panelBY + seek_bar_size[1], bb_line)

                    # Scrobble marker

                    if scrobble_mark and lastfm.hold is False and lastfm.connected and pctl.playing_length > 0:
                        l_target = 0
                        if master_library[pctl.track_queue[pctl.queue_step]]['length'] > 240 * 2:
                            l_target = 240
                        else:
                            l_target = int(master_library[pctl.track_queue[pctl.queue_step]]['length'] * 0.50)
                        l_lead = l_target - a_time

                        if l_lead > 0 and master_library[pctl.track_queue[pctl.queue_step]]['length'] > 30:
                            l_x = seek_bar_position[0] + int(
                                pctl.playing_time * seek_bar_size[0] / int(pctl.playing_length))
                            l_x += int(seek_bar_size[0] / int(pctl.playing_length) * l_lead)
                            draw_rect_r((l_x, seek_bar_position[1] + 13, 2, 2), [255, 0, 0, 100], True)
                            # seek_bar_size[1]

                    # SEEK BAR------------------

                    if pctl.playing_length > 0:
                        draw_rect((seek_bar_position[0], seek_bar_position[1]),
                                  (int(pctl.playing_time * seek_bar_size[0] / pctl.playing_length), seek_bar_size[1]),
                                  seek_bar_fill_colour, True)

                    if mouse_click and coll_point(mouse_position, seek_bar_position + seek_bar_size):
                        volume_hit = True
                        seek_down = True
                    if right_click and coll_point(mouse_position, seek_bar_position + seek_bar_size):
                        pctl.pause()
                        if pctl.playing_state == 0:
                            pctl.play()
                    if coll_point(mouse_position, seek_bar_position + seek_bar_size):
                        clicked = True
                        if mouse_wheel != 0:
                            new_time = pctl.playing_time + (mouse_wheel * 3)
                            pctl.playing_time += mouse_wheel * 3
                            if new_time < 0:
                                new_time = 0
                                pctl.playing_time = 0
                            pctl.playerCommand = 'seek'
                            pctl.playerCommandReady = True

                            # pctl.playing_time = new_time

                    if seek_down is True:
                        if mouse_position[0] == 0:
                            seek_down = False
                            seek_hit = True

                    if (mouse_up and coll_point(mouse_position,
                                                seek_bar_position + seek_bar_size)) or mouse_up and volume_hit or seek_hit:
                        volume_hit = False
                        seek_down = False
                        seek_hit = False

                        bargetX = mouse_position[0]
                        if bargetX > seek_bar_position[0] + seek_bar_size[0]:
                            bargetX = seek_bar_position[0] + seek_bar_size[0]
                        if bargetX < seek_bar_position[0]:
                            bargetX = seek_bar_position[0]
                        bargetX -= seek_bar_position[0]
                        seek = bargetX / seek_bar_size[0] * 100
                        # print(seek)
                        if pctl.playing_state == 1 or (pctl.playing_state == 2 and pause_lock is False):
                            new_time = pctl.playing_length / 100 * seek
                            # print('seek to:' + str(new_time))
                            pctl.playerCommand = 'seek'
                            pctl.playerCommandReady = True
                            pctl.playing_time = new_time
                            if system == 'windows'and taskbar_progress:
                                windows_progress.update(True)
                                # elif pctl.playing_state == 2:
                                #     new_time = pctl.playing_length / 100 * seek
                                #     reset_playing = True

                    # Activate top menu if right clicked in top bar past tabs
                    # if right_click and mouse_position[1] < panelY and mouse_position[0] > l + 50:
                    #     x_menu.activate()

                    # Volume Bar--------------------------------------------------------

                    if mouse_click and coll_point(mouse_position, volume_bar_position + volume_bar_size) or \
                                    volume_bar_being_dragged is True:
                        clicked = True
                        if mouse_click is True or volume_bar_being_dragged is True:
                            UPDATE_RENDER += 1
                            volume_bar_being_dragged = True
                            volgetX = mouse_position[0]
                            if volgetX > volume_bar_position[0] + volume_bar_size[0]:
                                volgetX = volume_bar_position[0] + volume_bar_size[0]
                            if volgetX < volume_bar_position[0]:
                                volgetX = volume_bar_position[0]
                            volgetX -= volume_bar_position[0]
                            volume = volgetX / volume_bar_size[0] * 100
                            if mouse_down is False:
                                volume_bar_being_dragged = False

                        volume = int(volume)
                        pctl.set_volume()

                    # if mouse_wheel != 0 and coll_point(mouse_position, (
                    #            volume_bar_position[0] - 15, volume_bar_position[1] - 10, volume_bar_size[0] + 30,
                    #            volume_bar_size[1] + 20 )):
                    if mouse_wheel != 0 and mouse_position[1] > seek_bar_position[1] + 4 and not coll_point(mouse_position,
                                                                                                            seek_bar_position + seek_bar_size):

                        if volume + (mouse_wheel * volume_bar_increment) < 1:
                            volume = 0
                        elif volume + (mouse_wheel * volume_bar_increment) > 100:
                            volume = 100
                        else:
                            volume += mouse_wheel * volume_bar_increment
                        volume = int(volume)
                        pctl.set_volume()

                    if right_click and coll_point(mouse_position, (
                                volume_bar_position[0] - 15, volume_bar_position[1] - 10, volume_bar_size[0] + 30,
                                volume_bar_size[1] + 20)):
                        if volume > 0:
                            volume_store = volume
                            volume = 0
                        else:
                            volume = volume_store

                        pctl.set_volume()

                    draw_rect(volume_bar_position, volume_bar_size, volume_bar_bg, True)  # 22
                    draw_rect(volume_bar_position, (int(volume * volume_bar_size[0] / 100), volume_bar_size[1]),
                              volume_bar_fill_colour, True)

                    if album_mode and pctl.playing_state > 0 and window_size[0] > 820:

                        title = master_library[pctl.track_queue[pctl.queue_step]]['title']
                        artist = master_library[pctl.track_queue[pctl.queue_step]]['artist']

                        line = ""
                        if title != "":
                            line += title
                        if artist != "":
                            if line != "":
                                line += "  -  "
                            line += artist
                        line = trunc_line(line, 13, window_size[0] - 710)
                        draw_text((seek_bar_position[0], seek_bar_position[1] + 22), line, side_bar_line1, 13)  # fontb1
                        if mouse_click and coll_point(mouse_position, (
                            seek_bar_position[0] - 10, seek_bar_position[1] + 20, window_size[0] - 710, 30)):
                            pctl.show_current()
                            if pctl.playing_state > 0:
                                goto_album(pctl.playlist_playing)
                            else:
                                goto_album(playlist_selected)

                # TIME----------------------
                text_time = get_display_time(pctl.playing_time)

                draw_text((time_display_position[0] + 140 + 2, window_size[1] - 29 + 1), text_time, PlayingTimeColour,
                          12)

                bx = 35
                by = window_size[1] - 30


                # BUTTONS
                # bottom buttons

                if GUI_Mode == 1:

                    # PLAY---


                    play_colour = ButtonsBG
                    pause_colour = ButtonsBG
                    stop_colour = ButtonsBG
                    forward_colour = ButtonsBG
                    back_colour = ButtonsBG

                    if pctl.playing_state == 1:
                        play_colour = ButtonsActive

                    if auto_stop:
                        stop_colour = ButtonsActive

                    if pctl.playing_state == 2:
                        pause_colour = ButtonsActive
                        play_colour = ButtonsActive
                    elif pctl.playing_state == 3:
                        play_colour = ButtonsActive

                    rect = (25 - 15, window_size[1] - control_line_bottom - 13, 50, 40)
                    fields.add(rect)
                    if coll_point(mouse_position, rect):
                        play_colour = ButtonsOver
                        if mouse_click:
                            pctl.play()
                        if right_click:
                            pctl.show_current()
                            if album_mode:
                                goto_album(pctl.playlist_playing)
                    draw_rect((25, window_size[1] - control_line_bottom), (14, 14), play_colour, True)
                    # draw_rect_r(rect,[255,0,0,255], True)
                    SDL_RenderCopy(renderer, c1, None, dst1)

                    # PAUSE---
                    x = 75
                    y = window_size[1] - control_line_bottom

                    rect = (x - 15, y - 13, 50, 40)
                    fields.add(rect)
                    if coll_point(mouse_position, rect):
                        pause_colour = ButtonsOver
                        if mouse_click:
                            pctl.pause()

                    # draw_rect_r(rect,[255,0,0,255], True)
                    draw_rect((x, y + 0), (4, 13), pause_colour, True)
                    draw_rect((x + 10, y + 0), (4, 13), pause_colour, True)

                    # STOP---
                    x = 125
                    rect = (x - 14, y - 13, 50, 40)
                    fields.add(rect)
                    if coll_point(mouse_position, rect):
                        stop_colour = ButtonsOver
                        if mouse_click:
                            pctl.stop()
                        if right_click:
                            auto_stop ^= True

                    draw_rect((x, y + 0), (13, 13), stop_colour, True)
                    # draw_rect_r(rect,[255,0,0,255], True)

                    # FORWARD---
                    rect = (230, window_size[1] - control_line_bottom - 10, 50, 35)
                    fields.add(rect)
                    if coll_point(mouse_position, rect):
                        forward_colour = ButtonsOver
                        if mouse_click:
                            pctl.advance()
                        if right_click:
                            pctl.random_mode ^= True
                        if middle_click:
                            pctl.advance(rr=True)
                    draw_rect((240, window_size[1] - control_line_bottom), (28, 14), forward_colour, True)
                    # draw_rect_r(rect,[255,0,0,255], True)
                    SDL_RenderCopy(renderer, c2, None, dst2)

                    # BACK---
                    rect = (170, window_size[1] - control_line_bottom - 10, 50, 35)
                    fields.add(rect)
                    if coll_point(mouse_position, rect):
                        back_colour = ButtonsOver
                        if mouse_click:
                            pctl.back()
                        if right_click:
                            pctl.repeat_mode ^= True

                    draw_rect((180, window_size[1] - control_line_bottom), (28, 14), back_colour, True)
                    # draw_rect_r(rect,[255,0,0,255], True)
                    SDL_RenderCopy(renderer, c3, None, dst3)

                    if window_size[0] > 630:

                        x = window_size[0] - 295
                        y = window_size[1] - 27

                        rect = (x - 9, y - 5, 65, 25)
                        fields.add(rect)

                        rpbc = stepctloff
                        if (mouse_click or right_click) and coll_point(mouse_position, rect):
                            pctl.random_mode ^= True

                            if pctl.random_mode == False:
                                random_click_off = True

                        if pctl.random_mode:
                            rpbc = stepctlon

                        elif coll_point(mouse_position, rect):
                            if random_click_off == True:
                                rpbc = stepctloff
                            elif pctl.random_mode is True:
                                rpbc = stepctlon
                            else:
                                rpbc = stepctlover
                        else:
                            random_click_off = False

                        y += 2

                        draw_rect((x, y), (25, 4), rpbc, True)

                        y += 8
                        draw_rect((x, y), (50, 4), rpbc, True)

                        #draw_text((x,y), "RANDOM", rpbc, 13)

                        # REPEAT
                        x = window_size[0] - 350
                        y = window_size[1] - 27

                        rpbc = stepctloff

                        rect = (x - 15, y - 5, 59, 25)
                        fields.add(rect)
                        if (mouse_click or right_click) and coll_point(mouse_position, rect):
                            pctl.repeat_mode ^= True

                            if pctl.repeat_mode == False:
                                repeat_click_off = True

                        if pctl.repeat_mode:
                            rpbc = stepctlon

                        elif coll_point(mouse_position, rect):
                            if repeat_click_off == True:
                                rpbc = stepctloff
                            elif pctl.repeat_mode is True:
                                rpbc = stepctlon
                            else:
                                rpbc = stepctlover
                        else:
                            repeat_click_off = False

                        #draw_text((x,y), "REPEAT", rpbc, 13)
                        y += 10
                        w = 4

                        draw_rect((x, y), (35, w), rpbc, True)
                        draw_rect((x + 35 - w, y - 8), (w, 8), rpbc, True)
                        draw_rect((x + 15, y - 8), (20, w), rpbc, True)



                # NEW TOP BAR

                if GUI_Mode == 1:

                    rect = (0,0,window_size[0], panelY)
                    draw_rect_r(rect, background, True)

                    # MULTI PLAYLIST-----------------------

                    l = 0

                    starting_l = 8

                    spacing = 17

                    if tab_hold:
                        dragmode = False

                    # Need to test length
                    k = 0
                    for w in range(len(pctl.multi_playlist)):
                        k += text_calc(pctl.multi_playlist[w][0], 12)[0]
                    k = starting_l + (spacing * (len(pctl.multi_playlist))) + k
                    k += 40
                    k += text_calc(get_playing_line(), 12)[0]

                    draw_alt = False
                    if k > window_size[0] - 120:
                        # rect = (starting_l, 0, 10, 29)
                        # draw_rect()

                        starting_l += 20
                        spacing = 0
                        draw_alt = True

                    # Process each tab on top panel
                    for w in range(len(pctl.multi_playlist)):

                        if draw_alt and w != pctl.playlist_active:
                            continue

                        text_space = text_calc(pctl.multi_playlist[w][0], 12)[0]

                        rect = (starting_l + (spacing * w) + l, 1, text_space + 16, 29)
                        fields.add(rect)

                        draw_rect((starting_l + (spacing * w) + l, 0), (text_space + 16, 30), playlist_bg, True)

                        if not pl_follow and w == pctl.active_playlist_playing:
                            draw_rect((starting_l + (spacing * w) + l, 0), (text_space + 16, 30), [255, 255, 255, 7], True)

                        if (tab_menu.active is True and tab_menu.reference == w) or tab_menu.active is False and coll_point(
                                mouse_position, (starting_l + (spacing * w) + l, 1, text_space + 16, 29)):
                            draw_rect((starting_l + (spacing * w) + l, 0), (text_space + 16, 30), playlist_over, True)

                        if w == pctl.playlist_active:
                            draw_rect((starting_l + (spacing * w) + l, 0), (text_space + 16, 30), playlist_bg_active, True)
                            text_space = draw_text((starting_l + (spacing * w) + 7 + l, r[1], r[2], r[3]),
                                                   pctl.multi_playlist[w][0],
                                                   playlist_line_active, 12)



                        else:
                            text_space = draw_text((starting_l + (spacing * w) + 7 + l, r[1], r[2], r[3]),
                                                   pctl.multi_playlist[w][0],
                                                   playlist_line, 12)

                        pl_coll = False

                        if coll_point(mouse_position, (starting_l + (spacing * w) + l, 1, text_space + 16, 30)):
                            pl_coll = True
                            if mouse_up and tab_hold and tab_hold_index != w:
                                pctl.multi_playlist[w], pctl.multi_playlist[tab_hold_index] = pctl.multi_playlist[
                                                                                                  tab_hold_index], \
                                                                                              pctl.multi_playlist[w]

                                pctl.playlist_active = w

                            if right_click:
                                tab_menu.activate(copy.deepcopy(w))

                            if quick_drag is True:
                                draw_text((starting_l + text_space + (spacing * w) + 7 + l, r[1] - 8, r[2], r[3]), '+',
                                          [200, 20, 40, 255], 12)

                                if mouse_up:
                                    quick_drag = False
                                    if len(shift_selection) > 1:
                                        for item in shift_selection:
                                            pctl.multi_playlist[w][2].append(default_playlist[item])
                                    else:
                                        pctl.multi_playlist[w][2].append(default_playlist[shift_selection[0]])

                        if mouse_click and pl_coll and not key_shift_down:
                            # print('Switching Playlist')
                            renplay += 1
                            tab_hold = True
                            tab_hold_index = w

                            switch_playlist(w)

                        elif tab_menu.active is False and loading_in_progress is False and (
                            middle_click or (key_shift_down and mouse_click)) and coll_point(
                                mouse_position, (starting_l + (spacing * w) + l, r[1], r[2] + text_space, r[3])) and len(
                                pctl.multi_playlist) > 1:
                            delete_playlist(w)

                            break

                        l += text_space

                    c_l = starting_l + (spacing * (len(pctl.multi_playlist))) + l

                    if mouse_up:
                        quick_drag = False

                    if not mouse_down:
                        tab_hold = False


                    if mouse_wheel != 0 and coll_point(mouse_position, (0, 0, window_size[0], 30)) and len(
                            pctl.multi_playlist) > 1:
                        switch_playlist(mouse_wheel * -1, True)
                        renplay += 1

                    # ------------
                    # Copy of above code for arrow keys
                    if (key_left_press or key_right_press) and len(pctl.multi_playlist) > 1:

                        renplay += 1
                        UPDATE_RENDER += 1

                        if key_left_press:
                            switch_playlist(-1, True)

                        if key_right_press:
                            switch_playlist(1, True)

                            # ----------------

                    l += 10

                    if draw_alt:
                        l += 20

                    x = starting_l + (spacing * len(pctl.multi_playlist)) + 9 + l
                    y = 8
                    rect = [x - 8, y - 4, 50, 23]

                    fields.add(rect)

                    if x_menu.active:

                        draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "MENU", GREY5, 12)
                        if coll_point(mouse_position, rect) and (mouse_click or right_click):
                            x_menu.active = False

                    else:
                        if coll_point(mouse_position, rect):
                            draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "MENU", GREY5, 12)
                            if mouse_click or right_click:
                                x_menu.activate(position=(x+20,panelY))
                        else:
                            draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "MENU", GREY4, 12)



                    l += 50

                    x = starting_l + (spacing * len(pctl.multi_playlist)) + 9 + l
                    y = 8
                    rect = [x - 6, y - 4, 60, 23]

                    fields.add(rect)

                    if album_mode:

                        draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "GALLERY", GREY5, 12)
                        if coll_point(mouse_position, rect) and mouse_click:
                            toggle_album_mode()

                    else:
                        if coll_point(mouse_position, rect):
                            draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "GALLERY", GREY5, 12)
                            if mouse_click:
                                toggle_album_mode()
                        else:
                            draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "GALLERY", GREY4, 12)



                    if lastfm.connected:
                        l += 62

                        x = starting_l + (spacing * len(pctl.multi_playlist)) + 9 + l
                        y = 8
                        rect = [x - 6, y - 4, 58, 23]

                        fields.add(rect)

                        if not lastfm.hold:
                            #draw_rect_r(rect, [70,70,70,70], True)
                            draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "LAST.FM", GREY5, 12)
                            if coll_point(mouse_position, rect) and mouse_click:
                                lastfm.toggle()

                        else:
                            if coll_point(mouse_position, rect):
                                draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "LAST.FM", GREY5, 12)
                                if mouse_click:
                                    lastfm.toggle()
                            else:
                                draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "LAST.FM", GREY4, 12)
                        l += 20

                    m_l = x + 60

                    l += 75

                    if broadcast is False:
                        if loading_in_progress:
                            draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5, r[1] - 1, r[2], r[3]),
                                      "Importing...  " + str(to_got) + "/" + str(to_get), [245, 205, 0, 255], 11)
                        elif len(transcode_list) > 0:
                            line = "Transcoding... " + str(len(transcode_list)) + " Remaining " + transcode_state

                            draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5, r[1] - 1, r[2], r[3]),
                                      line, [245, 205, 0, 255], 11)
                    elif join_broadcast:
                        draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5, r[1] - 1, r[2], r[3]),
                                  "Streaming", [60, 75, 220, 255], 11)
                        l += 97


                    else:

                        if encpause == 1:
                            draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5, r[1] - 1, r[2], r[3]),
                                      "Streaming Paused:", [220, 75, 60, 255], 11)
                            l += 97
                        else:
                            draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5, r[1] - 1, r[2], r[3]),
                                      "Now Streaming:", [60, 75, 220, 255], 11)
                            l += 85
                        line = master_library[broadcast_index]['artist'] + " - " + master_library[broadcast_index]['title']
                        line = trunc_line(line, 11, window_size[0] - l - 195)

                        draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5, r[1] - 1, r[2], r[3]), line,
                                  GREY(130), 11)

                        x = window_size[0] - 100
                        y = 10
                        w = 90
                        h = 9

                        if turbo:
                            x -= 90

                        w2 = int(broadcast_time / int(master_library[broadcast_index]['length']) * 90)

                        draw_rect((x, y), (w2, h), [30, 25, 170, 255], True)
                        draw_rect((x, y), (w, h), GREY(30))

                        l -= 15
                        l -= 85
                    # Topline
                    if block6 or (side_panel_enable is False and broadcast is not True and pctl.playing_state > 0):
                        line = ""

                        if pctl.playing_state < 3:
                            title = master_library[pctl.track_queue[pctl.queue_step]]['title']
                            artist = master_library[pctl.track_queue[pctl.queue_step]]['artist']
                        else:
                            title = tag_meta

                        if artist != "":
                            line += artist
                        if title != "":
                            if line != "":
                                line += " - "
                            line += title
                        # line = trunc_line(line, 11, window_size[0] - playlist_width - 53)
                        offset_extra = 0
                        if draw_border:
                            offset_extra = 61

                        l_max = window_size[0] - m_l - 10


                        if turbo:
                            draw_text((window_size[0] - 104 - offset_extra, 8, 1), line, side_bar_line1,
                                      11, max=l_max - 75)

                        else:
                            draw_text((window_size[0] - 15 - offset_extra, 8, 1), line, side_bar_line1,
                                      11, max=l_max)


            # Overlay GUI ----------------------

            if new_playlist_box is True:
                draw_rect((int(window_size[0] / 2) - (playlist_entry_box_half[0]),
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1]))),
                          (playlist_entry_box_size[0], playlist_entry_box_size[1]), background, True)
                draw_rect((int(window_size[0] / 2) - (playlist_entry_box_half[0]),
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1]))),
                          (playlist_entry_box_size[0], playlist_entry_box_size[1]), GREY3)

                draw_rect((int(window_size[0] / 2) - (playlist_entry_box_half[0]) + 15,
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1])) + 30), (220, 19), GREY2)
                NPN += input_text
                if key_backspace_press and len(NPN) > 0:
                    NPN = NPN[:-1]
                draw_text((int(window_size[0] / 2) - (playlist_entry_box_half[0]) + 9,
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1])) + 5,
                           playlist_entry_box_size[0] - 40, playlist_entry_box_size[1] - 95), "New Playlist:",
                          side_bar_line2,
                          12)
                c_blink = 200
                draw_text((int(window_size[0] / 2) - (playlist_entry_box_half[0]) + 20,
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1])) + 30,
                           playlist_entry_box_size[0] - 40, playlist_entry_box_size[1] - 95), NPN + cursor,
                          side_bar_line2, 12)
                if (key_esc_press and len(editline) == 0) or mouse_click or right_click:

                    new_playlist_box = False
                elif key_return_press:
                    new_playlist_box = False
                    key_return_press = False
                    if len(NPN) > 0:
                        pctl.multi_playlist.append([NPN, 0, [], 0, 0, 0])
                    # else:
                    #     pctl.multi_playlist.append(["Playlist", 0, [], 0, 0, 0])

            if rename_playlist_box is True:
                draw_rect((int(window_size[0] / 2) - (playlist_entry_box_half[0]),
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1]))),
                          (playlist_entry_box_size[0], playlist_entry_box_size[1]), background, True)
                draw_rect((int(window_size[0] / 2) - (playlist_entry_box_half[0]),
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1]))),
                          (playlist_entry_box_size[0], playlist_entry_box_size[1]), GREY3)

                draw_rect((int(window_size[0] / 2) - (playlist_entry_box_half[0]) + 15,
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1])) + 30), (220, 19), GREY2)
                NPN += input_text
                if key_backspace_press and len(NPN) > 0:
                    NPN = NPN[:-1]
                draw_text((int(window_size[0] / 2) - (playlist_entry_box_half[0]) + 9,
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1])) + 5,
                           playlist_entry_box_size[0] - 40, playlist_entry_box_size[1] - 95), "Rename Playlist:",
                          side_bar_line2,
                          12)
                c_blink = 200
                draw_text((int(window_size[0] / 2) - (playlist_entry_box_half[0]) + 20,
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1])) + 30,
                           playlist_entry_box_size[0] - 40, playlist_entry_box_size[1] - 95), NPN + cursor,
                          side_bar_line2, 12)
                if (key_esc_press and len(editline) == 0) or mouse_click or right_click:

                    rename_playlist_box = False
                elif key_return_press:
                    rename_playlist_box = False
                    key_return_press = False
                    if len(NPN) > 0:
                        pctl.multi_playlist[rename_index][0] = NPN

            if message_box:
                if mouse_click or key_return_press or right_click or key_esc_press or key_backspace_press or key_backslash_press:
                    message_box = False
                    key_return_press = False

                w = text_calc(message_box_text, 12)[0] + 20
                if w < 210:
                    w = 210
                h = 20
                x = int(window_size[0] / 2) - int(w / 2)
                y = int(window_size[1] / 2) - int(h / 2)

                draw_rect((x, y), (w, h), background, True)
                draw_rect((x, y), (w, h), GREY3)

                draw_text((x + int(w / 2), y + 2, 2), message_box_text, GREY6, 12)

            if lfm_pass_box:
                if key_esc_press:
                    lfm_pass_box = False
                if key_return_press:
                    lfm_pass_box = False
                    key_return_press = False
                    lastfm.connect()

                w = 400
                h = 50
                x = int(window_size[0] / 2) - int(w / 2)
                y = int(window_size[1] / 2) - int(h / 2)

                draw_rect((x, y), (w, h), background, True)
                draw_rect((x, y), (w, h), GREY3)

                lfm_password += input_text

                if key_backspace_press and len(lfm_password) > 0:
                    lfm_password = lfm_password[:-1]

                line = "Last FM Account Password: "

                for c in lfm_password:
                    line += "●"

                draw_text((x + 10, y + 7 + 20), line, GREY6, 12)
                draw_text((x + 10, y + 7), "Please enter the following.", GREY6, 12)

            if lfm_user_box:
                if key_return_press:
                    lfm_user_box = False
                    lfm_pass_box = True
                    key_return_press = False
                if key_esc_press:
                    lfm_user_box = False

                w = 400
                h = 50
                x = int(window_size[0] / 2) - int(w / 2)
                y = int(window_size[1] / 2) - int(h / 2)

                draw_rect((x, y), (w, h), background, True)
                draw_rect((x, y), (w, h), GREY3)

                lfm_username += input_text

                if key_backspace_press and len(lfm_username) > 0:
                    lfm_username = lfm_username[:-1]

                line = "Last FM Account Username: " + lfm_username

                draw_text((x + 10, y + 7 + 20), line, GREY6, 12)
                draw_text((x + 10, y + 7), "Please enter the following and try again.  Press F8 at any time to reset.",
                          GREY6, 12)

            if genre_box:

                w = 640
                h = 260
                x = int(window_size[0] / 2) - int(w / 2)
                y = int(window_size[1] / 2) - int(h / 2)

                box_rect = (x, y, w, h)

                if genre_box_click and not coll_point(mouse_position, box_rect):
                    genre_box = False

                draw_rect((x, y), (w, h), background, True)
                draw_rect((x, y), (w, h), GREY3)

                stats_gen.update(genre_box_pl)

                oy = int(window_size[1] / 2) - int(h / 2)
                x += 20

                y += 20
                dd = 0
                selection_list = stats_gen.genre_list  # [:40]
                for i in reversed(range(len(selection_list))):
                    if len(stats_gen.genre_dict[selection_list[i][0]]) < 50:
                        del selection_list[i]
                        continue

                for item in selection_list:
                    if item[0] == '<Genre Unspecified>':
                        selection_list.remove(item)
                        break

                selection_list = selection_list[:40
                                 ]
                for item in selection_list:

                    item_rect = [x, y, 110, 20]

                    if genre_box_click and coll_point(mouse_position, (x - 5, y - 2, 110 + 10, 20 + 4)):
                        if item[0] in genre_items:
                            genre_items.remove(item[0])
                        else:
                            genre_items.append(item[0])

                    if item[0] in genre_items:
                        draw_rect((x, y), (110, 20), [255, 255, 255, 35], True)

                    fields.add(copy.deepcopy(item_rect))
                    if coll_point(mouse_position, item_rect):
                        draw_rect_r(item_rect, [255, 255, 255, 10], True)

                    draw_rect((x, y), (110, 20), GREY1)
                    line = item[0][:20]
                    draw_text((x + 3, y + 2), line, GREY7, 10)

                    y += 25
                    if y > oy + h - 50:
                        y = oy + 20
                        x += 122

                x = int(window_size[0] / 2) - int(w / 2)
                y = int(window_size[1] / 2) - int(h / 2)
                x = x + w - 100
                y = y + h - 35
                w = 70
                h = 20

                ok_rect = (x, y, w, h)
                fields.add(ok_rect)
                if coll_point(mouse_position, ok_rect):
                    draw_rect_r(ok_rect, [255, 255, 255, 8], True)
                draw_rect_r(ok_rect, GREY2)
                draw_text((x + 14, y + 2), 'Generate', GREY6, 10)

                if genre_box_click and coll_point(mouse_position, ok_rect):
                    print('ok')
                    playlist = []
                    for genre in genre_items:
                        playlist += stats_gen.genre_dict[genre]

                        for index in pctl.multi_playlist[genre_box_pl][2]:
                            if genre.lower() in master_library[index]['directory'].lower().replace('-',
                                                                                                   '') and index not in playlist:
                                playlist.append(index)
                    line = pctl.multi_playlist[genre_box_pl][0] + ": " + ' + '.join(genre_items)
                    pctl.multi_playlist.append([line, 0, copy.deepcopy(playlist), 0, 0, 0])
                    genre_box = False
                    switch_playlist(len(pctl.multi_playlist) - 1)

            if track_box:
                if mouse_click or key_return_press or right_click or key_esc_press or key_backspace_press or key_backslash_press:
                    track_box = False
                    key_return_press = False
                w = 540
                h = 240
                x = int(window_size[0] / 2) - int(w / 2)
                y = int(window_size[1] / 2) - int(h / 2)

                # draw_rect((0,0),(window_size[0], window_size[1]), [0,0,0,120], True)

                draw_rect((x, y), (w, h), background, True)
                draw_rect((x, y), (w, h), GREY3)

                if key_shift_down:

                    # y += 24

                    draw_text((x + 8 + 10, y + 40), "Secret Operations Menu:", GREY8, 12)

                    y += 24
                    x += 15
                    files_to_purge = []

                    for item in os.listdir(master_library[r_menu_index]['directory']):
                        if 'AlbumArt' in item or 'desktop.ini' in item or 'Folder.jpg' in item:
                            files_to_purge.append(os.path.join(master_library[r_menu_index]['directory'], item))

                    line = "1. Purge potentially hidden image/ini files from folder (" + str(
                        len(files_to_purge)) + " Found)"
                    draw_text((x + 8 + 10, y + 40), line, GREY8, 12)

                    if key_1_press:
                        for item in files_to_purge:
                            print('PHYSICALLY DELETING FILE: ' + item)
                            try:
                                # print(item)
                                os.remove(item)
                                print(" Item Removed Successfully")
                            except:
                                print(" Error in removing file")

                    time.sleep(0.2)

                else:
                    draw_rect((x + w - 135 - 1, y + h - 125 - 1), (102, 102), GREY(30))
                    display_album_art(r_menu_index, (x + w - 135, y + h - 125), (100, 100))
                    y -= 24

                    draw_text((x + 8 + 10, y + 40), "Title:", GREY8, 12)
                    draw_text((x + 8 + 90, y + 40), master_library[r_menu_index]['title'], GREY8, 12)

                    y += 15

                    draw_text((x + 8 + 10, y + 40), "Artist:", GREY8, 12)
                    draw_text((x + 8 + 90, y + 40), master_library[r_menu_index]['artist'], GREY8, 12)

                    y += 15

                    draw_text((x + 8 + 10, y + 40), "Album:", GREY8, 12)
                    draw_text((x + 8 + 90, y + 40), master_library[r_menu_index]['album'], GREY8,
                              12)

                    y += 23

                    draw_text((x + 8 + 10, y + 40), "Path:", GREY8, 12)
                    draw_text((x + 8 + 90, y + 40), trunc_line(master_library[r_menu_index]['filepath'], 12, 420),
                              GREY8, 12)

                    y += 23

                    draw_text((x + 8 + 10, y + 40), "Samplerate:", GREY8, 12)
                    draw_text((x + 8 + 90, y + 40), str(master_library[r_menu_index]['sample']), GREY8, 12)

                    y += 15

                    draw_text((x + 8 + 10, y + 40), "Bitrate:", GREY8, 12)
                    draw_text((x + 8 + 90, y + 40), str(master_library[r_menu_index]['bitrate']), GREY8, 12)

                    y += 15

                    draw_text((x + 8 + 10, y + 40), "Length:", GREY8, 12)
                    line = time.strftime('%M:%S', time.gmtime(master_library[r_menu_index]['length']))
                    draw_text((x + 8 + 90, y + 40), line, GREY8, 12)

                    y += 23

                    draw_text((x + 8 + 10, y + 40), "Genre:", GREY8, 12)
                    draw_text((x + 8 + 90, y + 40), master_library[r_menu_index]['genre'], GREY8, 12)
                    y += 15

                    draw_text((x + 8 + 10, y + 40), "Release Date:", GREY8, 12)
                    draw_text((x + 8 + 90, y + 40), str(master_library[r_menu_index]['date']), GREY8, 12)

                    y += 23

                    key = master_library[r_menu_index]['title'] + master_library[r_menu_index]['filename']
                    total = 0
                    ratio = 0
                    if (key in star_library) and star_library[key] != 0 and master_library[r_menu_index][
                            'length'] != 0:
                        total = star_library[key]
                        ratio = total / master_library[r_menu_index]['length']

                    draw_text((x + 8 + 10, y + 40), "Play Count:", GREY8, 12)
                    draw_text((x + 8 + 90, y + 40), str(int(ratio)), GREY8, 12)

                    y += 15

                    line = time.strftime('%H:%M:%S',
                                         time.gmtime(total))

                    draw_text((x + 8 + 10, y + 40), "Playtime:", GREY8, 12)
                    draw_text((x + 8 + 90, y + 40), str(line), GREY8, 12)

            if pref_box.enabled:
                pref_box.render()

            if renamebox:

                w = 420
                h = 220
                x = int(window_size[0] / 2) - int(w / 2)
                y = int(window_size[1] / 2) - int(h / 2)

                draw_rect((x, y), (w, h), background, True)
                draw_rect((x, y), (w, h), GREY2)

                # NRN = rename_in.update()
                NRN += input_text
                c_blink = 200

                if key_backspace_press and len(NRN) > 0:
                    NRN = NRN[:-1]

                if key_ctrl_down and key_v_press:
                    NRN = pyperclip.paste()

                if key_esc_press or (mouse_click and not coll_point(mouse_position, (x, y, w, h))):
                    renamebox = False

                r_todo = []
                warncue = False

                for item in default_playlist:
                    if master_library[item]['parent'] == master_library[rename_index]['parent']:
                        if master_library[item]['cue'] == "YES":
                            warncue = True
                        else:
                            r_todo.append(item)

                draw_text((x + 10, y + 10,), "Physically rename all tracks in folder to format:", GREY6, 12)
                draw_text((x + 14, y + 40,), NRN + cursor, GREY6, 12)
                # c_blink = 200

                draw_rect((x + 8, y + 38), (300, 22), GREY2)

                draw_rect((x + 8 + 300 + 10, y + 38), (80, 22), GREY2)

                rect = (x + 8 + 300 + 10, y + 38, 80, 22)
                fields.add(rect)
                if coll_point(mouse_position, rect):
                    draw_rect((x + 8 + 300 + 10, y + 38), (80, 22), [50, 50, 50, 70], True)

                draw_text((x + 8 + 10 + 300 + 40, y + 40, 2), "WRITE (" + str(len(r_todo)) + ")", GREY6, 12)

                draw_text((x + 10, y + 70,), "%n - Track Number", GREY6, 12)
                draw_text((x + 10, y + 82,), "%a - Artist Name", GREY6, 12)
                draw_text((x + 10, y + 94,), "%t - Track Title", GREY6, 12)
                draw_text((x + 150, y + 70,), "%b - Album Title", GREY6, 12)
                draw_text((x + 150, y + 82,), "%x - File Extension", GREY6, 12)
                draw_text((x + 150, y + 94,), "%u - Use Underscores", GREY6, 12)

                afterline = ""
                warn = False
                underscore = False

                for item in r_todo:
                    afterline = ""

                    if master_library[item]['tracknumber'] == "" or master_library[item]['artist'] == "" or \
                                    master_library[item]['title'] == "" or master_library[item]['album'] == "":
                        warn = True

                    set = 0
                    while set < len(NRN):
                        if NRN[set] == "%" and set < len(NRN) - 1:
                            set += 1
                            if NRN[set] == 'n':
                                if len(str(master_library[item]['tracknumber'])) < 2:
                                    afterline += "0"
                                afterline += str(master_library[item]['tracknumber'])
                            elif NRN[set] == 'a':
                                afterline += master_library[item]['artist']
                            elif NRN[set] == 't':
                                afterline += master_library[item]['title']
                            elif NRN[set] == 'b':
                                afterline += master_library[item]['album']
                            elif NRN[set] == 'x':
                                afterline += "." + master_library[item]['ext'].lower()
                            elif NRN[set] == 'u':
                                underscore = True
                        else:
                            afterline += NRN[set]
                        set += 1
                    if underscore:
                        afterline = afterline.replace(' ', "_")

                    if item == rename_index:
                        break

                draw_text((x + 10, y + 120,),
                          trunc_line("BEFORE:  " + master_library[rename_index]['filename'], 12, 390), GREY6, 12)
                draw_text((x + 10, y + 135,), trunc_line("AFTER:     " + afterline, 12, 390), GREY6, 12)

                if (len(NRN) > 3 and len(master_library[rename_index]['filename']) > 3 and afterline[-3:].lower() !=
                    master_library[rename_index]['filename'][-3:].lower()) or len(NRN) < 4:
                    draw_text((x + 10, y + 160,), "Warning: This will change the file extention", [200, 60, 60, 255],
                              12)

                if '%t' not in NRN or '%n' not in NRN:
                    draw_text((x + 10, y + 175,), "Warning: The filename might not be unique", [200, 60, 60, 255],
                              12)
                if warn:
                    draw_text((x + 10, y + 190,), "Warning: File has incomplete metadata", [200, 60, 60, 255], 12)
                if warncue:
                    draw_text((x + 10, y + 190,), "Warning: Folder contains tracks from a CUE sheet",
                              [200, 60, 60, 255], 12)

                if mouse_click and coll_point(mouse_position, (x + 8 + 300 + 10, y + 38, 80, 22)):

                    total_todo = len(r_todo)

                    for item in r_todo:

                        if pctl.playing_state > 0 and item == pctl.track_queue[pctl.queue_step]:
                            pctl.playerCommand = 'stop'
                            pctl.playerCommandReady = True
                            pctl.playing_state = 0
                            time.sleep(1 + (pause_fade_time / 1000))

                        afterline = ""

                        set = 0
                        while set < len(NRN):
                            if NRN[set] == "%" and set < len(NRN) - 1:
                                set += 1
                                if NRN[set] == 'n':
                                    if len(str(master_library[item]['tracknumber'])) < 2:
                                        afterline += "0"
                                    afterline += str(master_library[item]['tracknumber'])
                                elif NRN[set] == 'a':
                                    afterline += master_library[item]['artist']
                                elif NRN[set] == 't':
                                    afterline += master_library[item]['title']
                                elif NRN[set] == 'b':
                                    afterline += master_library[item]['album']
                                elif NRN[set] == 'x':
                                    afterline += "." + master_library[item]['ext'].lower()
                            else:
                                afterline += NRN[set]
                            set += 1
                        if underscore:
                            afterline = afterline.replace(' ', "_")

                        for char in afterline:
                            if char in '\\/:*?"<>|':
                                afterline = afterline.replace(char, '')

                        oldname = master_library[item]['filename']
                        oldpath = master_library[item]['filepath']

                        try:
                            print('Renaming...')

                            playt = 0
                            oldkey = master_library[item]['title'] + master_library[item]['filename']
                            oldpath = master_library[item]['filepath']

                            oldsplit = os.path.split(oldpath)

                            os.rename(master_library[item]['filepath'], os.path.join(oldsplit[0], afterline))

                            master_library[item]['filepath'] = os.path.join(oldsplit[0], afterline)
                            master_library[item]['filename'] = afterline

                            newkey = master_library[item]['title'] + master_library[item]['filename']

                            if oldkey in star_library:
                                playt = star_library[oldkey]
                                del star_library[oldkey]
                            if newkey in star_library:
                                star_library[newkey] += playt
                            elif playt > 0:
                                star_library[newkey] = playt

                        except:
                            total_todo -= 1

                    renamebox = False
                    print('Done')
                    message_box = True
                    if total_todo != len(r_todo):
                        message_box_text = "Error.  " + str(total_todo) + "/" + str(len(r_todo)) + " filenames written"
                    else:
                        message_box_text = "Done.  " + str(total_todo) + "/" + str(len(r_todo)) + " filenames written"

            if radiobox:
                w = 420
                h = 87
                x = int(window_size[0] / 2) - int(w / 2)
                y = int(window_size[1] / 2) - int(h / 2)

                draw_rect((x, y), (w, h), background, True)
                draw_rect((x, y), (w, h), GREY2)

                NXN += input_text

                if key_backspace_press and len(NXN) > 0:
                    NXN = NXN[:-1]

                if key_ctrl_down and key_v_press:
                    # NXN = r_window.clipboard_get()
                    NXN = pyperclip.paste()

                if key_esc_press or (mouse_click and not coll_point(mouse_position, (x, y, w, h))):
                    radiobox = False

                draw_text((x + 10, y + 10,), "Open HTTP Audio Stream", GREY6, 12)
                draw_text((x + 14, y + 40,), NXN + cursor, GREY6, 12)
                c_blink = 200

                draw_rect((x + 8, y + 38), (350, 22), GREY2)

                rect = (x + 8 + 350 + 10, y + 38, 40, 22)
                fields.add(rect)

                if coll_point(mouse_position, rect):
                    draw_rect((x + 8 + 350 + 10, y + 38), (40, 22), [40, 40, 40, 60], True)

                draw_rect((x + 8 + 350 + 10, y + 38), (40, 22), GREY2)
                draw_text((x + 8 + 10 + 350 + 10, y + 40), "GO", GREY6, 12)

                if (key_return_press_w or (
                            mouse_click and coll_point(mouse_position,
                                                       (x + 8 + 350 + 10, y + 38, 40, 22)))) and 'http' in NXN:
                    URL = NXN.encode('utf-8')
                    radiobox = False
                    pctl.playing_state = 0
                    pctl.playerCommand = "url"
                    pctl.playerCommandReady = True
                    pctl.playing_state = 3

                input_text = ""
            # SEARCH
            if (key_backslash_press or (key_ctrl_down and key_f_press)) and quick_search_mode is False:
                quick_search_mode = True
                NSN = ""
                input_text = ""
            elif ((key_backslash_press or (key_ctrl_down and key_f_press)) or (
                    key_esc_press and len(editline) == 0)) or mouse_click and quick_search_mode is True:
                quick_search_mode = False
                NSN = ""

            if quick_search_mode is True:

                if key_ctrl_down and key_v_press:
                    try:
                        # NSN += r_window.clipboard_get()
                        NSN += pyperclip.paste()
                    except:
                        print("Clipboard Error")

                search_box_location_x = int(window_size[0] / 2) - int(quick_search_box_size[0] / 2)

                draw_rect((search_box_location_x, window_size[1] - 90),
                          (quick_search_box_size[0], quick_search_box_size[1]), bottom_panel_colour, True)
                draw_rect((search_box_location_x, window_size[1] - 90),
                          (quick_search_box_size[0], quick_search_box_size[1]), GREY(60))

                if len(input_text) > 0:
                    search_index = -1

                NSN += input_text

                if key_backspace_press and len(NSN) > 0:
                    NSN = NSN[:-1]
                c_blink = 200
                draw_text((search_box_location_x + 8, window_size[1] - 85), "SEARCH: " + NSN + cursor, GREY5, 12)
                if key_esc_press:
                    new_playlist_box = False

                if len(input_text) > 0 or key_down_press is True:

                    renplay += 1

                    oi = search_index

                    while search_index < len(default_playlist) - 1:
                        search_index += 1
                        if search_index > len(default_playlist) - 1:
                            search_index = 0

                        search_terms = NSN.lower().split()
                        line = master_library[default_playlist[search_index]]['title'].lower() + \
                               master_library[default_playlist[search_index]]['artist'].lower() \
                               + master_library[default_playlist[search_index]]['album'].lower() + \
                               master_library[default_playlist[search_index]]['filename'].lower()

                        if all(word in line for word in search_terms):

                            playlist_selected = search_index
                            if len(default_playlist) > 10 and search_index > 10:
                                playlist_position = search_index - 7
                            else:
                                playlist_position = 0
                            break

                    else:
                        search_index = oi

                if key_up_press is True:

                    renplay += 1
                    oi = search_index

                    while search_index > 1:
                        search_index -= 1
                        if search_index > len(default_playlist) - 1:
                            search_index = len(default_playlist) - 1
                        search_terms = NSN.lower().split()
                        line = master_library[default_playlist[search_index]]['title'].lower() + \
                               master_library[default_playlist[search_index]]['artist'].lower() \
                               + master_library[default_playlist[search_index]]['album'].lower() + \
                               master_library[default_playlist[search_index]]['filename'].lower()

                        if all(word in line for word in search_terms):

                            playlist_selected = search_index
                            if len(default_playlist) > 10 and search_index > 10:
                                playlist_position = search_index - 7
                            else:
                                playlist_position = 0

                            break
                    else:
                        search_index = oi
                if key_return_press is True and search_index > -1:
                    renplay += 1
                    pctl.jump(default_playlist[search_index], search_index)

            else:

                if key_up_press:
                    shift_selection = []

                    pctl.show_selected()
                    renplay += 1

                    if playlist_selected > 0:
                        playlist_selected -= 1

                    if playlist_position > 0 and playlist_selected < playlist_position + 2:
                        playlist_position -= 1
                    if playlist_selected > len(default_playlist):
                        playlist_selected = len(default_playlist)



                if key_down_press and playlist_selected < len(default_playlist):
                    shift_selection = []
                    pctl.show_selected()
                    renplay += 1

                    if playlist_selected < len(default_playlist) - 1:
                        playlist_selected += 1


                    if playlist_position < len(
                            default_playlist) and playlist_selected > playlist_position + playlist_view_length - 3:
                        playlist_position += 1

                    if playlist_selected < 0:
                        playlist_selected = 0

                if key_return_press:
                    renplay += 1
                    if playlist_selected > len(default_playlist) - 1:
                        playlist_selected = 0
                        shift_selection = []
                    pctl.jump(default_playlist[playlist_selected], playlist_selected)

        # Unicode edit display---------------------
        if len(editline) > 0:
            ll = text_calc(editline, 12)[0]
            draw_rect((window_size[0] - ll - 10, 0), (ll + 15, 18), BLACK, True)
            draw_text((window_size[0] - ll - 5, 3), editline, GREY(210), 12)

        # Render Menus-------------------------------
        x_menu.render()
        track_menu.render()
        tab_menu.render()
        playlist_menu.render()

        if encoding_box:
            if key_return_press or right_click or key_esc_press or key_backspace_press or key_backslash_press:
                encoding_box = False

            w = 420
            h = 200
            x = int(window_size[0] / 2) - int(w / 2)
            y = int(window_size[1] / 2) - int(h / 2)

            if encoding_box_click and not coll_point(mouse_position, (x, y, w, h)):
                encoding_box = False

            draw_rect((x, y), (w, h), background, True)
            draw_rect((x, y), (w, h), GREY3)

            draw_text((x + 105, y + 21), "Japanese text encoding correction.", GREY(190), 12)

            y += 20

            draw_text((x + 105, y + 21), "Select from list if correct shown:", GREY(190), 11)

            y -= 20
            x += 20
            y += 20

            if enc_field == "Artist":
                draw_rect((x, y), (60, 20), [80, 80, 80, 80], True)
            draw_rect((x, y), (60, 20), GREY3)
            draw_text((x + 6, y + 2), "Artist", GREY8, 12)
            if coll_point(mouse_position, (x, y, 60, 20)) and encoding_box_click:
                enc_field = "Artist"

            y += 25

            if enc_field == "Title":
                draw_rect((x, y), (60, 20), [80, 80, 80, 80], True)
            draw_rect((x, y), (60, 20), GREY3)
            draw_text((x + 6, y + 2), "Title", GREY8, 12)
            if coll_point(mouse_position, (x, y, 60, 20)) and encoding_box_click:
                enc_field = "Title"

            y += 25

            if enc_field == "Album":
                draw_rect((x, y), (60, 20), [80, 80, 80, 80], True)
            draw_rect((x, y), (60, 20), GREY3)
            draw_text((x + 6, y + 2), "Album", GREY8, 12)
            if coll_point(mouse_position, (x, y, 60, 20)) and encoding_box_click:
                enc_field = "Album"

            y += 25

            if enc_field == "All":
                draw_rect((x, y), (60, 20), [80, 80, 80, 80], True)
            draw_rect((x, y), (60, 20), GREY3)
            draw_text((x + 6, y + 2), "All", GREY8, 12)
            if coll_point(mouse_position, (x, y, 60, 20)) and encoding_box_click:
                enc_field = "All"

            y += 40

            if enc_setting == 1:
                draw_rect((x, y), (60, 20), [80, 80, 80, 80], True)
            draw_rect((x, y), (60, 20), GREY3)
            draw_text((x + 6, y + 2), "Track", GREY8, 12)
            if coll_point(mouse_position, (x, y, 60, 20)) and encoding_box_click:
                enc_setting = 1

            y += 25

            if enc_setting == 0:
                draw_rect((x, y), (60, 20), [80, 80, 80, 80], True)
            draw_rect((x, y), (60, 20), GREY3)
            draw_text((x + 6, y + 2), "Folder", GREY8, 12)
            if coll_point(mouse_position, (x, y, 60, 20)) and encoding_box_click:
                enc_setting = 0

            x += 80
            y -= 100
            w = 295
            h = 14

            y += 15

            for enco in encodings:

                artist = master_library[encoding_target]['artist']
                title = master_library[encoding_target]['title']
                album = master_library[encoding_target]['album']

                draw_rect((x, y), (w, h), background, True)

                rect = (x, y, w, h - 1)
                fields.add(rect)
                if coll_point(mouse_position, rect):
                    draw_rect((x, y), (w, h), GREY2, True)
                    if encoding_box_click:
                        fix_encoding(encoding_target, enc_setting, enco)
                        encoding_box = False
                if enc_field == "Artist" or enc_field == "All":
                    artist = artist.encode("Latin-1", 'ignore')
                    artist = artist.decode(enco, 'ignore')
                if enc_field == "Title" or enc_field == "All":
                    title = title.encode("Latin-1", 'ignore')
                    title = title.decode(enco, 'ignore')

                if enc_field == "Album" or enc_field == "All":
                    album = album.encode("Latin-1", 'ignore')
                    album = album.decode(enco, 'ignore')
                line = artist + " - " + title + " - " + album
                line = trunc_line(line, 11, w - 5)

                draw_text((x + 5, y), line, GREY6, 11)

                y += h
            draw_rect((x, y - (h * len(encodings))), (w, h * len(encodings)), GREY2)

        if draw_border:

            rect = (window_size[0] - 55, window_size[1] - 35, 55 - 2, 35 - 2)
            fields.add(rect)
            if draw_border and coll_point(mouse_position, rect):
                draw_text((window_size[0] - 15, window_size[1] - 20), "↘", [200, 200, 200, 255], 16)

            rect = (window_size[0] - 65, 5, 35, 20)
            fields.add(rect)
            if coll_point(mouse_position, rect):
                draw_rect((window_size[0] - 65, 5), (35, 20), [70, 70, 70, 100], True)
                if mouse_click or ab_click:
                    SDL_MinimizeWindow(t_window)
                    mouse_down = False
                    mouse_click = False
                    dragmode = False
            draw_rect((window_size[0] - 65, 5), (35, 20), GREY(40))

            rect = (window_size[0] - 25, 5, 20, 20)
            fields.add(rect)
            if coll_point(mouse_position, rect):
                draw_rect((window_size[0] - 25, 5), (20, 20), [80, 80, 80, 120], True)
                if mouse_click or ab_click:
                    running = False
            draw_rect((window_size[0] - 25, 5), (20, 20), GREY(40))

            draw_rect((0, 0), (window_size), GREY(90))

        UPDATE_RENDER -= 1

        if turbo:
            UPDATE_LEVEL = True
        else:
            SDL_RenderPresent(renderer)

    if pctl.playing_state != 1 and level_peak != [0, 0] and turbo:

        time_passed = level_time.get()
        if time_passed > 1000:
            time_passed = 0
        while time_passed > 20:
            level_peak[1] -= 0.4
            if level_peak[1] < 0:
                level_peak[1] = 0
            level_peak[0] -= 0.4
            if level_peak[0] < 0:
                level_peak[0] = 0
            time_passed -= 20
        UPDATE_LEVEL = True

    if UPDATE_LEVEL is True and not resize_mode:
        UPDATE_LEVEL = False

        # testing
        if vis == 2 and spec != None:

            if update_spec == 0 and pctl.playing_state != 2:
                time.sleep(0.01)
                for i in range(len(spec)):
                    if spec[i] > 0:
                        spec[i] -= 1
                        UPDATE_LEVEL = True
            if spec_smoothing:

                for i in range(len(spec)):
                    if spec[i] > sspec[i]:
                        sspec[i] += 1
                        if abs(spec[i] - sspec[i]) > 4:
                            sspec[i] += 1
                        if abs(spec[i] - sspec[i]) > 6:
                            sspec[i] += 1
                        if abs(spec[i] - sspec[i]) > 8:
                            sspec[i] += 1

                    elif spec[i] == sspec[i]:
                        pass
                    elif spec[i] < sspec[i] > 0:
                        sspec[i] -= 1
                        if abs(spec[i] - sspec[i]) > 4:
                            sspec[i] -= 1
                        if abs(spec[i] - sspec[i]) > 6:
                            sspec[i] -= 1
                        if abs(spec[i] - sspec[i]) > 8:
                            sspec[i] -= 1

                if pctl.playing_state == 0 and checkEqual(sspec):
                    UPDATE_LEVEL = True
                    time.sleep(0.008)

            else:
                sspec = spec
            x = window_size[0] - 20 - offset_extra - 70 - 0
            y = 5
            w = 72 + 24 - 6 - 10
            h = 20
            rect = (x, y, w, h)
            draw_rect_r(rect, background, True)
            draw_rect_r(rect, [255, 255, 255, 13], True)

            xx = 0
            on = 0

            # for i in range(len(sspec)):
            for item in sspec:
                # item = sspec[i]
                if on > 19:
                    break
                on += 1

                if item > 0:
                    item -= 1

                if item < 1:
                    xx += 4
                    continue

                if item > 20:
                    item = 20

                yy = y + h - item
                rect = (xx + x, yy, 3, item)
                # if coll_point(mouse_position,(xx+x,y,3,h)):
                #     sspec[i] = (20 - (mouse_position[1] - y)) + 2
                #     if i > 0:
                #         sspec[i-1] = (20 - (mouse_position[1] - y))
                #     if i < 19:
                #         sspec[i+1] = (20 - (mouse_position[1] - y))

                draw_rect_r(rect, PlayingTimeColour, True)
                xx += 4

        if vis == 1:

            offset_extra = 0
            if draw_border:
                offset_extra = 61

            x = window_size[0] - 20 - offset_extra
            y = 16
            w = 5
            s = 1
            # draw_rect((x - 70, y - 10), (80, 18), GREY(15), True)

            for t in range(12):

                if level_peak[0] < t:
                    met = False
                else:
                    met = True
                if level_peak[0] < 0.2:
                    met = False

                if t < 7:
                    cc = GREEN4
                    if met is False:
                        cc = [0, 30, 0, 255]
                elif t < 10:
                    cc = YELLOW5
                    if met is False:
                        cc = [30, 30, 0, 255]
                else:
                    cc = RED5
                    if met is False:
                        cc = [30, 0, 0, 255]

                if level > 0 and pctl.playing_state > 0:
                    pass
                draw_rect(((x - (w * t) - (s * t)), y), (w, w), cc, True)

            y -= 7
            for t in range(12):

                if level_peak[1] < t:
                    met = False
                else:
                    met = True
                if level_peak[1] < 0.2:
                    met = False

                if t < 7:
                    cc = GREEN4
                    if met is False:
                        cc = [0, 30, 0, 255]
                elif t < 10:
                    cc = YELLOW5
                    if met is False:
                        cc = [30, 40, 0, 255]
                else:
                    cc = RED5
                    if met is False:
                        cc = [30, 0, 0, 255]

                if level > 0 and pctl.playing_state > 0:
                    pass
                draw_rect(((x - (w * t) - (s * t)), y), (w, w), cc, True)

        SDL_RenderPresent(renderer)

    # print(pctl.playing_state)
    # -------------------------------------------------------------------------------------------
    # Broadcast control


    if broadcast and broadcast_time > master_library[broadcast_index]['length'] and not join_broadcast:
        broadcast_position += 1
        print('next')
        if broadcast_position > len(pctl.multi_playlist[broadcast_playlist][2]) - 1:
            print('reset')
            broadcast_position = 0

        broadcast_index = pctl.multi_playlist[broadcast_playlist][2][broadcast_position]
        broadcast_time = 0
        b_timer()
        pctl.target_open = master_library[broadcast_index]['filepath']
        pctl.bstart_time = master_library[broadcast_index]['starttime']
        pctl.playerCommand = "encnext"
        pctl.playerCommandReady = True
        broadcast_line = master_library[broadcast_index]['artist'] + " - " + master_library[broadcast_index]['title']

    if broadcast and broadcast_time != broadcast_last_time:
        broadcast_last_time = broadcast_time
        UPDATE_RENDER += 1
    if broadcast and broadcast_time == 0:
        renplay += 1

    # Playlist and pctl.track_queue

    if pctl.playing_state == 1 and pctl.playing_time + (
        cross_fade_time / 1000) + 0.5 >= pctl.playing_length and pctl.playing_time > 2:

        if auto_stop:
            pctl.stop()
            UPDATE_RENDER += 2
            auto_stop = False

        elif pctl.repeat_mode is True:

            pctl.playing_time = 0
            new_time = 0
            pctl.playerCommand = 'seek'
            pctl.playerCommandReady = True

        elif pctl.random_mode is False and len(default_playlist) - 2 > pctl.playlist_playing and \
                        master_library[default_playlist[pctl.playlist_playing]][
                            'cue'] == "YES" and master_library[default_playlist[pctl.playlist_playing + 1]][
            'filename'] == \
                master_library[default_playlist[pctl.playlist_playing]]['filename'] and int(
                master_library[default_playlist[pctl.playlist_playing]]['tracknumber']) == int(
                master_library[default_playlist[pctl.playlist_playing + 1]]['tracknumber']) - 1:
            print("CUE Gapless")
            pctl.playlist_playing += 1
            pctl.queue_step += 1
            pctl.track_queue.append(default_playlist[pctl.playlist_playing])

            pctl.playing_state = 1
            pctl.playing_time = 0
            pctl.playing_length = master_library[pctl.track_queue[pctl.queue_step]]['length']

            UPDATE_RENDER += 1
            renplay += 1


        else:
            pctl.advance()
            pctl.playing_time = 0


    if taskbar_progress and system == 'windows' and pctl.playing_state == 1:
        windows_progress.update()

    if (pctl.playing_state == 1 or pctl.playing_state == 3) and lowered is False:
        if int(pctl.playing_time) != int(pctl.last_playing_time):
            pctl.last_playing_time = pctl.playing_time
            UPDATE_RENDER = 1

    if len(pctl.track_queue) > 100 and pctl.queue_step > 1:
        del pctl.track_queue[0]
        pctl.queue_step -= 1

    # cursor blinker
    if c_blink > 0:
        c_blink -= 1
        c_time += c_timer()
        if c_time > 3:
            c_time = 0
        if c_time > 0.6:
            c_time = 0
            UPDATE_RENDER += 1
            if cursor == "|":
                cursor = ""
            elif cursor == "":
                cursor = "|"
        if input_text != "":
            c_time = 0
            cursor = "|"
            UPDATE_RENDER += 1

    if system == 'windows':

        if mouse_down is False:
            dragmode = False


        if mouse_click and mouse_down and 1 < mouse_position[1] < 30 and m_l < mouse_position[0] < window_size[
            0] - 80 and dragmode is False and clicked is False:

            dragmode = True

            lm = copy.deepcopy(mouse_position)

        if mouse_up:
            dragmode = False

        if dragmode:
            #mp = win32api.GetCursorPos()

            p_x = pointer(c_int(0))
            p_y = pointer(c_int(0))
            SDL_GetGlobalMouseState(p_x,p_y)
            mp = [p_x.contents.value, p_y.contents.value]

            time.sleep(0.005)
            SDL_SetWindowPosition(t_window, mp[0] - lm[0], mp[1] - lm[1])

    # auto save
    if total_playtime - time_last_save > 600:
        print("Auto Save")
        pickle.dump(star_library, open(user_directory + "/star.p", "wb"))
        time_last_save = total_playtime

    if min_render_timer.get() > 60:
        min_render_timer.set()
        renplay += 1
        UPDATE_RENDER += 1

    if lowered:
        time.sleep(0.1)

pctl.playerCommand = "unload"
pctl.playerCommandReady = True

print("writing database to disk")
pickle.dump(star_library, open(user_directory + "/star.p", "wb"))

view_prefs['star-lines'] = star_lines
view_prefs['update-title'] = update_title
view_prefs['split-line'] = split_line
view_prefs['side-panel'] = prefer_side
view_prefs['dim-art'] = dim_art
view_prefs['level-meter'] = turbo
view_prefs['pl-follow'] = pl_follow
view_prefs['scroll-enable'] = scroll_enable
view_prefs['break-enable'] = break_enable
view_prefs['dd-index'] = dd_index
view_prefs['custom-line'] = custom_line_mode
view_prefs['thick-lines'] = thick_lines

save = [master_library,
        master_count,
        pctl.playlist_playing,
        pctl.playlist_active,
        playlist_position,
        pctl.multi_playlist,
        volume,
        pctl.track_queue,
        pctl.queue_step,
        default_playlist,
        pctl.playlist_playing,
        cue_list,
        NXN,
        theme,
        folder_image_offsets,
        lfm_username,
        lfm_hash,
        version,
        view_prefs,
        window_size,
        side_panel_size,
        savetime,
        vis,
        playlist_selected,
        None,
        None,
        None
        ]

pickle.dump(save, open(user_directory + "/state.p", "wb"))
# r_window.destroy()
if system == 'windows':

    print("unloading SDL")
    SDL_DestroyWindow(t_window)
    IMG_Quit()
    TTF_Quit()
    SDL_QuitSubSystem(SDL_INIT_EVERYTHING)
    SDL_Quit()
    print("SDL unloaded")

else:
    print("Skipping closing SDL cleanly")
    hookman.cancel()

while pctl.playerCommand != 'done':
    time.sleep(0.2)

print("bye")
