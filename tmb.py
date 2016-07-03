# -*- coding: utf-8 -*-

# Tauon Music Box

# Copyright (c) 2015-2016, Taiko2k captain.gxj@gmail.com

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
# learning programming and python, as a result this code can be quite messy. No doubt I have
# written some things terribly wrong or inefficiently in places.
# I would highly recommend not using this project as an example on how to code cleanly or correctly.


# --------------------------------------------------------------------

import sys
import os
import pickle

t_version = "v1.4.4"
title = 'Tauon Music Box'
version_line = title + t_version
print(version_line)
print('Copyright (c) 2015-2016 Taiko2k captain.gxj@gmail.com\n')

server_port = 7590

if sys.platform == 'win32':
    system = 'windows'
    print("Detected platform: Windows")
elif sys.platform == 'darwin':
    system = 'mac'
    print("Detected platform: Max OS X")
else:
    system = 'linux'
    print("Detected platform: Linux")

working_directory = os.getcwd()
install_directory = sys.path[0]
install_directory = install_directory.replace('\\', '/')
if 'base_library' in install_directory:
    install_directory = os.path.dirname(install_directory)
user_directory = install_directory
transfer_target = user_directory + "/transfer.p"
# print("Working directory: " + working_directory)
# print('Argument List: ' + str(sys.argv))
# print('User directory: ' + user_directory)
print('Install directory: ' + install_directory)

encoder_output = user_directory + '/encoder/'
b_active_directory = install_directory.encode('utf-8')


try:
    open(user_directory + '/lock', 'x')
    pass
except:
    pickle.dump(sys.argv, open(user_directory + "/transfer.p", "wb"))
    # sys.exit()
    import socket
    print('There might already be an instance...')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = s.connect_ex(('127.0.0.1', server_port))
    s.close()

    if result == 0:
        print('Socket is already open')
        # import http.client
        #
        # pickle.dump(sys.argv, open(user_directory + "/transfer.p", "wb"))
        # print('sending notice')
        #
        # c = http.client.HTTPConnection('localhost', server_port)
        # c.request('POST', '/load', '{test}')
        # doc = c.getresponse().read()
        # print(doc)
        #pass
        sys.exit()

import time
import ctypes
import random
import fractions
import threading
import io
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

fast_bin_av = True

try:
    from fastbin import fast_display, fast_bin
except ImportError:
    fast_bin_av = False

locale.setlocale(locale.LC_ALL, "")

if system == 'windows':
    os.environ["PYSDL2_DLL_PATH"] = install_directory + "\\lib"
    from ctypes import windll, CFUNCTYPE, POINTER, c_int, c_void_p, byref
    import win32con, win32api, win32gui, atexit


import sdl2
from sdl2 import *
from sdl2.sdlttf import *
from sdl2.sdlimage import *

from PIL import Image
from PIL import ImageFilter

from hsaudiotag import auto
import stagger
from stagger.id3 import *
from tflac import Flac


class Timer:  # seconds
    def __init__(self):
        self.start = 0
        self.end = 0

    def set(self):  # Reset
        self.start = time.time()

    def hit(self):  # Return time and reset

        self.end = time.time()
        elapsed = self.end - self.start
        self.start = time.time()
        return elapsed

    def get(self):  # Return time only
        self.end = time.time()
        return self.end - self.start


cursor_blink_timer = Timer()
spec_decay_timer = Timer()
min_render_timer = Timer()
check_file_timer = Timer()
check_file_timer.set()


# GUI Variables -------------------------------------------------------------------------------------------
GUI_Mode = 1
input_text_mode = False

show_playlist = True

draw_border = False
resize_drag = [0, 0]
resize_mode = False
resize_size = [0, 0]

version = 0.8

block6 = False

playlist_panel = False

highlight_left_custom = 0
highlight_right_custom = 0

side_panel_text_align = 0
main_font = 'Koruri-Regular.ttf'  # 'DroidSansFallback.ttf'

album_mode = False
spec_smoothing = True

auto_play_import = False


offset_extra = 0

custom_line = "t;r65;o;l;r2;n;p0.33;a;p0.65;b"
custom_pro = custom_line.split(";")
custom_line_mode = False

highlight_x_offset = 0


old_album_pos = -55
old_side_pos = 200
album_dex = []
album_dex_l = []
album_artist_dict = {}
row_len = 5
last_row = 0
album_v_gap = 65
album_h_gap = 30
album_mode_art_size = 130
albums_to_render = 0
pre_cache = []

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
playlist_x_offset = 7

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
p_stay = 0

savetime = 0

l = 0
c_l = 0
m_l = 700
seek_bar_position = [window_size[0] - seek_bar_size[0] - volume_bar_right, 20]

compact_bar = False

# Playlist Panel
pl_view_offset = 0
pl_rect = (2,12,10,10)

theme = 5
themeChange = True
panelY = 78

side_panel_size = 178

row_font_size = 13


class ColoursClass:


    def grey(self, value):
        return [value, value, value, 255]

    def __init__(self):
        
        self.sep_line = self.grey(50)
        self.bb_line = self.grey(50)
        self.tb_line = self.grey(50)
        self.art_box = self.grey(20)
        
        self.volume_bar_background = self.grey(19)
        self.volume_bar_outline = self.grey(100)
        self.volume_bar_fill = self.grey(95)
        self.seek_bar_background = self.grey(28)
        self.seek_bar_outline = self.grey(100)
        self.seek_bar_fill = self.grey(110)

        self.tab_text_active = self.grey(170)
        self.tab_text = self.grey(140)
        self.tab_background = self.grey(14)
        self.tab_highlight = self.grey(18)
        self.tab_background_active = self.grey(27)

        self.title_text = [0, 125, 0, 255]
        self.index_text = self.title_text
        self.time_text = self.index_text
        self.artist_text = [50, 170, 5, 255]
        self.album_text = self.grey(50)
        
        self.index_playing = self.title_text
        self.artist_playing = [50, 170, 5, 255]
        self.album_playing = self.artist_text
        self.title_playing = self.title_text
        self.time_playing = self.grey(200)

        self.playlist_text_missing = self.grey(50)
        self.bar_time = self.title_text

        self.top_panel_background = self.grey(0)
        self.side_panel_background = self.top_panel_background
        self.playlist_panel_background = self.grey(4)
        self.bottom_panel_colour = self.grey(8)

        self.row_playing_highlight = self.grey(15)
        self.row_select_highlight = self.grey(15)

        self.side_bar_line1 = self.grey(175)
        self.side_bar_line2 = self.grey(155)
    
        self.mode_button_off = self.grey(20)
        self.mode_button_over = self.grey(40)
        self.mode_button_active = self.grey(120)

        self.media_buttons_over = self.grey(200)
        self.media_buttons_active = self.grey(150)
        self.media_buttons_off = self.grey(30)

        self.star_line = [140, 140, 0, 255]
        self.folder_title = [200, 200, 0, 255]
        self.folder_line = [140, 140, 0, 255]

        self.scroll_colour = [30, 30, 30, 255]

        self.level_green = [0, 100, 0, 255]
        self.level_red = [175, 0, 0, 255]
        self.level_yellow = [90, 90, 20, 255]

        self.vis_colour = self.title_text

colours = ColoursClass()

playlist_width = int(window_size[0] * 0.65) + 25

info_panel_position = (200, 15)
info_panel_vert_spacing = 20
info_panel_hor_spacing = 0

load_to = []

time_display_position_right = 200
time_display_position = [window_size[0] - time_display_position_right, 45]

repeat_click_off = False
random_click_off = False

scroll_enable = True
break_enable = True
dd_index = False

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
click_location = [200, 200]

volume_hit = False
seek_hit = False
seek_down = False

mouse_position = [0, 0]

k_input = True

key_shift_down = False
drag_mode = False
side_drag = False
clicked = False
# Player Variables----------------------------------------------------------------------------


DA_Formats = {'MP3', 'mp3', 'WAV', 'wav', 'OPUS', 'opus', 'FLAC', 'flac', 'APE', 'ape',
              'm4a', 'M4A', 'MP4', 'mp4', 'ogg', 'OGG', 'AAC', 'aac', 'tta', 'TTA'}

if system == 'windows':
    DA_Formats.add('wma')
    DA_Formats.add('WMA')


auto_stop = False


l_x = 0
# Buttons-----------------------------------------------------------------

Buttons = []
File_Buttons = []
Mode_Buttons = []

r = (130, 85, 10, 15)

dropped_file = []
cargo = []
default_player = 'BASS'
# ---------------------------------------------------------------------
# Player variables

pl_follow = False

dlevel = 0

olevel = 0

encoding_box = False
encoding_box_click = False

# List of encodings to show in the fix mojibake function
encodings = ['cp932', 'utf-8', 'big5hkscs', 'gbk']

track_box = False

genre_box = False
genre_box_pl = 0
genre_items = []

transcode_list = []
transcode_state = ""

taskbar_progress = False
QUE = []

playing_in_queue = 0
player_from = 'File'

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

LC_None = 0
LC_Done = 1
LC_Folder = 2
LC_File = 3

loaderCommand = LC_None
loaderCommandReady = False
paths_to_load = []
master_count = 0
items_loaded = []




volume = 100

pause_lock = False

folder_image_offsets = {}
db_version = 0

meidakey = 1
mediakeymode = 1


# A mode ------------

albums = []
album_position = 0

prefer_side = True
dim_art = False
append_date = True


class Prefs:

    def __init__(self):

        self.pause_fade_time = 400
        self.change_volume_fade_time = 400
        self.cross_fade_time = 700

        self.enable_web = True
        self.allow_remote = True
        self.expose_web = False
        
        self.enable_transcode = False
        self.show_rym = True


prefs = Prefs()


class GuiVar:

    def __init__(self):

        self.update = 2 # UPDATE
        self.turbo = False
        self.turbo_next = 0
        self.pl_update = 1
        self.lowered = False
        
        self.level_update = False
        self.level_time = Timer()
        self.level_peak = [0, 0]
        self.level = 0
        self.time_passed = 0

        self.vis = 2  # visualiser mode setting
        self.spec = None
        self.s_spec = [0] * 24
        self.update_spec = 0

gui = GuiVar()

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


class TrackClass():

    def __init__(self):

        self.index = 0
        self.fullpath = ""
        self.filename = ""
        self.parent_folder_path = ""
        self.parent_folder_name = ""
        self.file_ext = ""
        self.size = 0

        self.artist = ""
        self.title = ""
        self.length = 0
        self.bitrate = 0
        self.samplerate = 0
        self.album = ""
        self.date = ""
        self.track_number = ""
        self.start_time = 0
        self.is_cue = False
        self.genre = ""
        self.found = True


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
    gui.vis = save[22]
    playlist_selected = save[23]
    if save[24] != None:
        album_mode_art_size = save[24]
    if save[25] != None:
        draw_border = save[25]
    if save[26] != None:
        prefs.enable_web = save[26]
    if save[27] != None:
        prefs.allow_remote = save[27]
    if save[28] != None:
        prefs.expose_web = save[28]
    if save[29] != None:
        prefs.enable_transcode = save[29]
    if save[30] != None:
        prefs.show_rym = save[30]

except:
    print('Error loading save file')

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
            if 'taskbar-progress' in p:
                taskbar_progress = True
            if 'pause-fade-time' in p:
                prefs.pause_fade_time = num_from_line(p)
            if 'cross-fade-time' in p:
                prefs.cross_fade_time = num_from_line(p)
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
    scrobble_mark = True
    print("Warning: Missing config file")

try:
    star_lines = view_prefs['star-lines']
    update_title = view_prefs['update-title']
    split_line = view_prefs['split-line']
    prefer_side = view_prefs['side-panel']
    dim_art = view_prefs['dim-art']
    gui.turbo = view_prefs['level-meter']
    pl_follow = view_prefs['pl-follow']
    scroll_enable = view_prefs['scroll-enable']
    break_enable = view_prefs['break-enable']
    dd_index = view_prefs['dd-index']
    custom_line_mode = view_prefs['custom-line']
    thick_lines = view_prefs['thick-lines']
    append_date = view_prefs['append-date']
except:
    print("warning: error loading settings")


# if os.path.isdir("web"):
#     pass
# else:
#     print('Creating web cache folder')
#     os.makedirs("web")


if prefer_side is False:
    side_panel_enable = False


get_len = 0
get_len_filepath = ""


def get_len_backend(filepath):
    global pctl
    global get_len
    global get_len_filepath
    get_len_filepath = filepath
    pctl.playerCommand = 'getlen'
    pctl.playerCommandReady = True
    while pctl.playerCommand != 'got':
        time.sleep(0.05)
    return get_len


def get_filesize_string(file_bytes):
        if file_bytes < 1000:
            line = str(file_bytes) + " Bytes"
        elif file_bytes < 1000000:
            file_kb = round(file_bytes / 1000, 2)
            line = str(file_kb).rstrip('0').rstrip('.') + " KB"
        else:
            file_mb = round(file_bytes / 1000000, 2)
            line = str(file_mb).rstrip('0').rstrip('.') + " MB"
        return line


def get_display_time(seconds):

    result = divmod(int(seconds), 60)
    if result[0] > 99:
        result = divmod(result[0], 60)
        return str(result[0]) + 'h ' + str(result[1]).zfill(2)
    return str(result[0]).zfill(2) + ":" + str(result[1]).zfill(2)
        

class PlayerCtl:

    def __init__(self):

        # Database

        self.total_playtime = 0
        self.master_library = master_library
        self.star_library = star_library

        # Misc player control

        self.url = ""
        self.tag_meta = ""
        self.encoder_pause = 0

        # Playback

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
        self.left_time = 0
        self.left_index = 0
        self.player_volume = volume
        self.new_time = 0
        self.time_to_get = []
        self.a_time = 0
        self.b_time = 0

        # Broadcasting

        self.broadcast_active = False
        self.join_broadcast = False
        self.broadcast_playlist = 0
        self.broadcast_position = 0
        self.broadcast_index = 0
        self.broadcast_time = 0
        self.broadcast_last_time = 0
        self.broadcast_line = ""

    def playing_playlist(self):
        return self.multi_playlist[self.active_playlist_playing][2]

    def render_playlist(self):
        global gui

        if taskbar_progress and system == 'windows':
            global windows_progress
            windows_progress.update(True)
        gui.pl_update += 1

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

        if album_mode:
            goto_album(playlist_selected)
        return 0

    def set_volume(self):

        self.playerCommand = 'volume'
        self.playerCommandReady = True

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
            random_start = random.randrange(1,self.playing_length - 45 if self.playing_length > 50 else self.playing_length)
        else:
            random_start = 0

        self.playing_time = random_start
        self.target_open = pctl.master_library[self.track_queue[self.queue_step]].fullpath
        self.start_time = pctl.master_library[self.track_queue[self.queue_step]].start_time
        self.jump_time = random_start
        self.playerCommand = 'open'
        self.playerCommandReady = True
        self.playing_state = 1

        self.last_playing_time = random_start

        if update_title:
            update_title_do()

    def play_target(self):

        self.playing_time = 0
        self.target_open = pctl.master_library[self.track_queue[self.queue_step]].fullpath
        self.start_time = pctl.master_library[self.track_queue[self.queue_step]].start_time
        self.playerCommand = 'open'
        self.playerCommandReady = True
        self.playing_state = 1
        self.playing_length = pctl.master_library[self.track_queue[self.queue_step]].length
        self.last_playing_time = 0

        if update_title:
            update_title_do()

    def jump(self, index, pl_position=None):

        if len(self.track_queue) > 0:
            self.left_time = self.playing_time
            self.left_index = self.track_queue[self.queue_step]

        global playlist_hold
        global gui
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

        global gui
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

        self.render_playlist()

    def stop(self):
        self.playerCommand = 'stop'
        self.playerCommandReady = True
        if len(self.track_queue) > 0:
            self.left_time = self.playing_time
            self.left_index = self.track_queue[self.queue_step]
        self.playing_time = 0
        self.playing_state = 0
        self.render_playlist()
        global gui
        gui.update_spec = 0
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

        if len(self.track_queue) > 0:
            self.left_time = self.playing_time
            self.left_index = self.track_queue[self.queue_step]

        pctl.playing_length = 100
        pctl.playing_time = 0
        global gui

        gui.update_spec = 0

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
            line = pctl.master_library[pctl.track_queue[pctl.queue_step]].artist + " - " + \
                   pctl.master_library[pctl.track_queue[pctl.queue_step]].title
            line = line.encode('utf-8')
            SDL_SetWindowTitle(t_window, line)
    else:
        line = title
        line = line.encode('utf-8')
        SDL_SetWindowTitle(t_window, line)


class LastFMapi:
    API_SECRET = "18c471e5475e7e877b126843d447e855"
    connected = False
    hold = False
    API_KEY = "0eea8ea966ab2ca395731e2c3c22e81e"

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

    def get_bio(self, artist):
        if self.connected:

            artist_object = pylast.Artist(artist, self.network)
            bio = artist_object.get_bio_summary(language="en")
            return bio
        else:
            return ""

    def update(self, title, artist, album):
        if self.hold:
            return 0
        global message_box
        global message_box_text
        global pctl
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
            pctl.b_time -= 5000
            return 1


def get_backend_time(path):
    global pctl

    pctl.time_to_get = path

    pctl.playerCommand = 'time'
    pctl.playerCommandReady = True

    while pctl.playerCommand != 'done':
        time.sleep(0.005)

    return pctl.time_to_get


lastfm = LastFMapi()

# PLAYER---------------------------------------------------------------

def player():

    a_index = -1
    a_sc = False
    a_pt = False

    player_timer = Timer()
    broadcast_timer = Timer()
    current_volume = pctl.player_volume / 100

    if system == 'windows':
        bass_module = ctypes.WinDLL('bass')
        enc_module = ctypes.WinDLL('bassenc')
        mix_module = ctypes.WinDLL('bassmix')
        function_type = ctypes.WINFUNCTYPE
    elif system == 'mac':
        bass_module = ctypes.CDLL(install_directory + '/lib/libbass.dylib', mode=ctypes.RTLD_GLOBAL)
        enc_module = ctypes.CDLL(install_directory + '/lib/libbassenc.dylib', mode=ctypes.RTLD_GLOBAL)
        mix_module = ctypes.CDLL(install_directory + '/lib/libbassmix.dylib', mode=ctypes.RTLD_GLOBAL)
        function_type = ctypes.CFUNCTYPE
    else:
        bass_module = ctypes.CDLL(install_directory + '/lib/libbass.so', mode=ctypes.RTLD_GLOBAL)
        enc_module = ctypes.CDLL(install_directory + '/lib/libbassenc.so', mode=ctypes.RTLD_GLOBAL)
        mix_module = ctypes.CDLL(install_directory + '/lib/libbassmix.so', mode=ctypes.RTLD_GLOBAL)
        function_type = ctypes.CFUNCTYPE

    BASS_Init = function_type(ctypes.c_bool, ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p,
                              ctypes.c_void_p)(('BASS_Init', bass_module))

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

    BASS_Mixer_StreamCreate = function_type(ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_Mixer_StreamCreate', mix_module))
    BASS_Mixer_StreamAddChannel = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong)(
        ('BASS_Mixer_StreamAddChannel', mix_module))
    BASS_Mixer_ChannelRemove = function_type(ctypes.c_bool, ctypes.c_ulong)(
        ('BASS_Mixer_ChannelRemove', mix_module))
    BASS_Mixer_ChannelSetPosition = function_type(ctypes.c_bool, ctypes.c_ulong, ctypes.c_int64, ctypes.c_ulong)(
        ('BASS_Mixer_ChannelSetPosition', mix_module))

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
        BASS_PluginLoad(b'bassopus.dll', 0)
        BASS_PluginLoad(b'bassflac.dll', 0)
        BASS_PluginLoad(b'bass_ape.dll', 0)
        BASS_PluginLoad(b'bassenc.dll', 0)
        BASS_PluginLoad(b'bass_tta.dll', 0)
        BASS_PluginLoad(b'bassmix.dll', 0)
        BASS_PluginLoad(b'basswma.dll', 0)
    elif system == 'mac':
        b = install_directory.encode('utf-8')
        BASS_PluginLoad(b + b'/lib/libbassopus.dylib', 0)
        BASS_PluginLoad(b + b'/lib/libbassflac.dylib', 0)
        BASS_PluginLoad(b + b'/lib/libbass_ape.dylib', 0)
        BASS_PluginLoad(b + b'/lib/libbass_aac.dylib', 0)
        BASS_PluginLoad(b + b'/lib/libbassmix.dylib', 0)
    else:
        b = install_directory.encode('utf-8')
        BASS_PluginLoad(b + b'/lib/libbassopus.so', 0)
        BASS_PluginLoad(b + b'/lib/libbassflac.so', 0)
        BASS_PluginLoad(b + b'/lib/libbass_ape.so', 0)
        BASS_PluginLoad(b + b'/lib/libbass_aac.so', 0)
        BASS_PluginLoad(b + b'/lib/libbassmix.so', 0)

    BassInitSuccess = BASS_Init(-1, 44100, 0, 0, 0)
    if BassInitSuccess == True:
        print("Bass library initialised")

    player1_status = 'stopped'
    player2_status = 'stopped'

    last_level = [0, 0]

    while True:
        if gui.turbo is False:
            time.sleep(0.04)
        else:
            gui.turbo_next += 1

            if gui.vis == 2:
                time.sleep(0.018)
            else:
                time.sleep(0.02)

            if gui.turbo_next < 6 and pctl.playerCommandReady is not True:

                if player1_status != 'playing' and player2_status != 'playing':
                    gui.level = 0
                    continue

                # -----------
                if gui.vis == 2:
                    if gui.lowered:
                        continue

                    sp_handle = 0
                    if player1_status == 'playing':
                        sp_handle = handle1
                    elif player2_status == 'playing':
                        sp_handle = handle2
                    x = (ctypes.c_float * 512)()
                    # print(x)
                    ctypes.cast(x, ctypes.POINTER(ctypes.c_float))

                    BASS_ChannelGetData(sp_handle, x, 0x80000002)

                    # BASS_DATA_FFT256 = 0x80000000# -2147483648# 256 sample FFT
                    # BASS_DATA_FFT512 = 0x80000001# -2147483647# 512 FFT
                    # BASS_DATA_FFT1024 = 0x80000002# -2147483646# 1024 FFT
                    # BASS_DATA_FFT2048 = 0x80000003# -2147483645# 2048 FFT
                    # BASS_DATA_FFT4096 = 0x80000004# -2147483644# 4096 FFT
                    # BASS_DATA_FFT8192 = 0x80000005# -2147483643# 8192 FFT
                    # BASS_DATA_FFT16384 = 0x80000006# 16384 FFT
                    if not fast_bin_av:
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
                    else:
                        gui.spec = fast_bin(x)

                    # print(gui.spec)
                    if pctl.playing_time > 0.5 and pctl.playing_state == 1:
                        gui.update_spec = 1
                    # if pctl.playerCommand in ['open', 'stop']:
                    #     gui.update_spec = 0
                    gui.level_update = True
                    continue

                # -----------------------------------

                if gui.vis == 1:

                    if player1_status == 'playing':
                        gui.level = BASS_ChannelGetLevel(handle1)
                    elif player2_status == 'playing':
                        gui.level = BASS_ChannelGetLevel(handle2)

                    ppp = (bin(gui.level)[2:].zfill(32))
                    ppp1 = ppp[:16]
                    ppp2 = ppp[16:]
                    ppp1 = int(ppp1, 2)
                    ppp2 = int(ppp2, 2)
                    ppp1 = (ppp1 / 32768) * 11.1
                    ppp2 = (ppp2 / 32768) * 11.1

                    gui.time_passed += gui.level_time.hit()
                    if gui.time_passed > 1:
                        gui.time_passed = 0
                    while gui.time_passed > 0.019:
                        gui.level_peak[1] -= 0.4
                        if gui.level_peak[1] < 0:
                            gui.level_peak[1] = 0
                        gui.level_peak[0] -= 0.4
                        if gui.level_peak[0] < 0:
                            gui.level_peak[0] = 0
                        gui.time_passed -= 0.020

                    if ppp1 > gui.level_peak[0]:
                        gui.level_peak[0] = ppp1
                    if ppp2 > gui.level_peak[1]:
                        gui.level_peak[1] = ppp2

                    if int(gui.level_peak[0]) != int(last_level[0]) or int(gui.level_peak[1]) != int(last_level[1]):
                        gui.level_update = True
                    gui.level_update = True
                    last_level = copy.deepcopy(gui.level_peak)

                    continue

            else:
                gui.turbo_next = 0
                if pctl.playerCommand == 'open':
                    # gui.update += 1
                    gui.level_peak = [0, 0]

        if pctl.playing_state == 3 and player1_status == 'playing':

            # print(BASS_ChannelGetTags(handle1,4 ))
            pctl.tag_meta = BASS_ChannelGetTags(handle1, 5)
            if pctl.tag_meta is not None:
                pctl.tag_meta = pctl.tag_meta.decode('utf-8')[13:-2]
            else:
                pctl.tag_meta = BASS_ChannelGetTags(handle1, 2)
                if pctl.tag_meta is not None:
                    pctl.tag_meta = pctl.tag_meta.decode('utf-8')[6:]
                else:
                    pctl.tag_meta = ""

                    # time.sleep(0.5)

        if pctl.broadcast_active and pctl.encoder_pause == 0:
            pctl.broadcast_time += broadcast_timer.hit()

        if player1_status == 'playing' or player2_status == 'playing':

            add_time = player_timer.hit()
            pctl.playing_time += add_time

            if pctl.playing_state == 1:

                pctl.a_time += add_time
                pctl.total_playtime += add_time

                if a_index != pctl.track_queue[pctl.queue_step]:
                    pctl.a_time = 0
                    pctl.b_time = 0
                    a_index = pctl.track_queue[pctl.queue_step]
                    a_pt = False
                    a_sc = False
                if pctl.playing_time == 0 and a_sc is True:
                    print("Reset scrobble timer")
                    pctl.a_time = 0
                    pctl.b_time = 0
                    a_pt = False
                    a_sc = False
                if pctl.a_time > 10 and a_pt is False and pctl.master_library[a_index].length > 30:
                    a_pt = True

                    if lastfm.connected:
                        mini_t = threading.Thread(target=lastfm.update, args=(pctl.master_library[a_index].title,
                                                                              pctl.master_library[a_index].artist,
                                                                              pctl.master_library[a_index].album))
                        mini_t.daemon = True
                        mini_t.start()

                if pctl.a_time > 10 and a_pt:
                    pctl.b_time += add_time
                    if pctl.b_time > 20:
                        pctl.b_time = 0
                        if lastfm.connected:
                            mini_t = threading.Thread(target=lastfm.update, args=(pctl.master_library[a_index].title,
                                                                                  pctl.master_library[a_index].artist,
                                                                                  pctl.master_library[a_index].album))
                            mini_t.daemon = True
                            mini_t.start()

                if pctl.master_library[a_index].length > 30 and pctl.a_time > pctl.master_library[a_index].length \
                    * 0.50 and a_sc is False:
                    a_sc = True
                    if lastfm.connected:
                        gui.pl_update += 1
                        print(
                                "Scrobble " + pctl.master_library[a_index].title + " - " + pctl.master_library[a_index].artist)

                        mini_t = threading.Thread(target=lastfm.scrobble, args=(pctl.master_library[a_index].title,
                                                                              pctl.master_library[a_index].artist,
                                                                              pctl.master_library[a_index].album))
                        mini_t.daemon = True
                        mini_t.start()

                if a_sc is False and pctl.master_library[a_index].length > 30 and pctl.a_time > 240:
                    if lastfm.connected:
                        gui.pl_update += 1
                        print(
                                "Scrobble " + pctl.master_library[a_index].title + " - " + pctl.master_library[a_index].artist)

                        mini_t = threading.Thread(target=lastfm.scrobble, args=(pctl.master_library[a_index].title,
                                                                              pctl.master_library[a_index].artist,
                                                                              pctl.master_library[a_index].album))
                        mini_t.daemon = True
                        mini_t.start()
                    a_sc = True

            if pctl.playing_state == 1 and len(pctl.track_queue) > 0:
                index = pctl.track_queue[pctl.queue_step]
                key = pctl.master_library[index].title + pctl.master_library[index].filename
                if key in pctl.star_library:
                    if 3 > add_time > 0:
                        pctl.star_library[key] += add_time
                else:
                    pctl.star_library[key] = 0

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

            if pctl.playerCommand == "url":
                if player1_status != 'stopped':
                    BASS_ChannelStop(handle1)
                    player1_status = 'stopped'
                    BASS_StreamFree(handle1)
                if player2_status != 'stopped':
                    BASS_ChannelStop(handle2)
                    player2_status = 'stopped'
                    BASS_StreamFree(handle2)

                # fileline = str(datetime.datetime.now()) + ".ogg"

                handle1 = BASS_StreamCreateURL(pctl.url, 0, 0, down_func, 0)
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

                flag |= 0x200000

                BASS_Mixer_ChannelRemove(handle3)
                BASS_StreamFree(handle3)

                handle3 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)

                if pctl.bstart_time > 0:
                    bytes_position = BASS_ChannelSeconds2Bytes(handle3, pctl.bstart_time)
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
                    encstop = BASS_Encode_Stop(encoder)
                    channel3 = BASS_ChannelStop(handle3)
                    BASS_StreamFree(handle3)
                    # BASS_StreamFree(oldhandle)

            if pctl.playerCommand == 'encpause' and pctl.broadcast_active:

                if pctl.encoder_pause == 0:
                    BASS_ChannelPause(mhandle)
                    pctl.encoder_pause = 1
                else:
                    BASS_ChannelPlay(mhandle, True)
                    pctl.encoder_pause = 0

            if pctl.playerCommand == "encstop":
                encstop = BASS_Encode_Stop(encoder)
                channel3 = BASS_ChannelStop(handle3)
                BASS_StreamFree(handle3)
                pctl.broadcast_active = False

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

                if codec == "MP3":
                    if system == 'windows':
                        line = install_directory + "/encoder/lame.exe" + " -r -s 44100 -b " + bitrate + " -"
                    else:
                        line = "lame" + " -r -s 44100 -b " + bitrate + " -"

                    line = line.encode('utf-8')

                    encoder = BASS_Encode_Start(mhandle, line, 1, 0, 0)

                    line = "source:" + ice_pass
                    line = line.encode('utf-8')

                    BASS_Encode_CastInit(encoder, mount.encode('utf-8'), line, b"audio/mpeg", b"name", b"url",
                                         b"genre", b"", b"", int(bitrate), False)

                elif codec == "OGG":
                    if system == 'windows':
                        line = install_directory + "/encoder/oggenc2.exe" + " -r -b " + bitrate + " -"
                    else:
                        line = "oggenc" + " -r -b " + bitrate + " -"

                    line = line.encode('utf-8')
                    # print(line)

                    encoder = BASS_Encode_Start(mhandle, line, 1, 0, 0)

                    line = "source:" + ice_pass
                    line = line.encode('utf-8')

                    BASS_Encode_CastInit(encoder, mount.encode('utf-8'), line, b"application/ogg", b"name", b"url",
                                         b"genre", b"", b"", int(bitrate), False)

                elif codec == "OPUS":
                    if system == 'windows':
                        line = install_directory + "/encoder/opusenc.exe --raw --bitrate " + bitrate + " - - "
                    else:
                        line = "opusenc" + " --raw --bitrate " + bitrate + " - - "

                    line = line.encode('utf-8')
                    # print(line)

                    encoder = BASS_Encode_Start(mhandle, line, 1, 0, 0)

                    line = "source:" + ice_pass
                    line = line.encode('utf-8')

                    BASS_Encode_CastInit(encoder, mount.encode('utf-8'), line, b"application/ogg", b"name", b"url",
                                         b"genre", b"", b"", int(bitrate), False)

                channel1 = BASS_ChannelPlay(mhandle, True)

                # Trying to send the stream title here causes the stream to fail for some reason
                # line2 = pctl.broadcast_line.encode('utf-8')
                # BASS_Encode_CastSetTitle(encoder, line2,0)

                print(BASS_ErrorGetCode())

            # OPEN COMMAND
            if pctl.playerCommand == 'open' and pctl.target_open != '':

                pctl.playerCommand = ""

                if os.path.isfile(pctl.master_library[pctl.track_queue[pctl.queue_step]].fullpath):
                    pctl.master_library[pctl.track_queue[pctl.queue_step]].found = True
                else:
                    pctl.master_library[pctl.track_queue[pctl.queue_step]].found = False
                    gui.pl_update += 1
                    gui.update += 1
                    print("Missing File")
                    pctl.playerCommandReady = False
                    pctl.playing_state = 0
                    pctl.advance()
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

                    if pctl.bstart_time > 0:
                        bytes_position = BASS_ChannelSeconds2Bytes(handle3, pctl.bstart_time)
                        BASS_ChannelSetPosition(handle3, bytes_position, 0)

                    BASS_Mixer_StreamAddChannel(mhandle, handle3, 0)
                    channel1 = BASS_ChannelPlay(mhandle, True)

                player_timer.hit()
                # print(pctl.target_open)
                if system != 'windows':
                    pctl.target_open = pctl.target_open.encode('utf-8')
                    flag = 0
                else:
                    flag = 0x80000000

                # BASS_ASYNCFILE = 0x40000000
                flag |= 0x40000000

                if player1_status == 'stopped' and player2_status == 'stopped':
                    # print(BASS_ErrorGetCode())

                    handle1 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)
                    # print(BASS_ErrorGetCode())
                    channel1 = BASS_ChannelPlay(handle1, True)

                    # if pctl.broadcast_active:
                    #     BASS_Encode_SetChannel(encoder, handle1)

                    # print(BASS_ErrorGetCode())
                    BASS_ChannelSetAttribute(handle1, 2, current_volume)
                    # print(BASS_ErrorGetCode())
                    player1_status = 'playing'
                elif player1_status != 'stopped' and player2_status == 'stopped':
                    player1_status = 'stopping'
                    BASS_ChannelSlideAttribute(handle1, 2, 0, prefs.cross_fade_time)

                    handle2 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)
                    channel2 = BASS_ChannelPlay(handle2, True)

                    BASS_ChannelSetAttribute(handle2, 2, 0)
                    BASS_ChannelSlideAttribute(handle2, 2, current_volume, prefs.cross_fade_time)
                    player2_status = 'playing'
                elif player2_status != 'stopped' and player1_status == 'stopped':
                    player2_status = 'stopping'
                    BASS_ChannelSlideAttribute(handle2, 2, 0, prefs.cross_fade_time)

                    handle1 = BASS_StreamCreateFile(False, pctl.target_open, 0, 0, flag)
                    BASS_ChannelSetAttribute(handle1, 2, 0)
                    channel1 = BASS_ChannelPlay(handle1, True)

                    BASS_ChannelSlideAttribute(handle1, 2, current_volume, prefs.cross_fade_time)
                    player1_status = 'playing'

                else:
                    print('no case')

                if pctl.master_library[pctl.track_queue[pctl.queue_step]].length < 1:

                    if player1_status == 'playing':
                        blen = BASS_ChannelGetLength(handle1, 0)
                        tlen = BASS_ChannelBytes2Seconds(handle1, blen)
                        pctl.master_library[pctl.track_queue[pctl.queue_step]].length = tlen
                        pctl.playing_length = tlen
                    elif player2_status == 'playing':
                        blen = BASS_ChannelGetLength(handle2, 0)
                        tlen = BASS_ChannelBytes2Seconds(handle2, blen)
                        pctl.master_library[pctl.track_queue[pctl.queue_step]].length = tlen
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
                player_timer.hit()

            # PAUSE COMMAND
            elif pctl.playerCommand == 'pause':
                player_timer.hit()

                if pctl.join_broadcast and pctl.broadcast_active:
                    if player1_status == 'playing' or player2_status == 'playing':
                        BASS_ChannelPause(mhandle)
                    else:
                        BASS_ChannelPlay(mhandle, True)

                if player1_status == 'playing':
                    player1_status = 'paused'
                    BASS_ChannelSlideAttribute(handle1, 2, 0, prefs.pause_fade_time)
                    time.sleep(prefs.pause_fade_time / 1000 / 0.7)
                    channel1 = BASS_ChannelPause(handle1)
                elif player1_status == 'paused':
                    player1_status = 'playing'
                    channel1 = BASS_ChannelPlay(handle1, False)
                    BASS_ChannelSlideAttribute(handle1, 2, current_volume, prefs.pause_fade_time)
                if player2_status == 'playing':
                    player2_status = 'paused'
                    BASS_ChannelSlideAttribute(handle2, 2, 0, prefs.pause_fade_time)
                    time.sleep(prefs.pause_fade_time / 1000 / 0.7)
                    channel2 = BASS_ChannelPause(handle2)
                elif player2_status == 'paused':
                    player2_status = 'playing'
                    channel2 = BASS_ChannelPlay(handle2, False)
                    BASS_ChannelSlideAttribute(handle2, 2, current_volume, prefs.pause_fade_time)

            # UNLOAD PLAYER COMMAND
            elif pctl.playerCommand == 'unload':
                BASS_Free()
                print('BASS Unloaded')
                break

            # CHANGE VOLUME COMMAND
            elif pctl.playerCommand == 'volume':
                current_volume = pctl.player_volume / 100
                if player1_status == 'playing':
                    BASS_ChannelSlideAttribute(handle1, 2, current_volume, prefs.change_volume_fade_time)
                if player2_status == 'playing':
                    BASS_ChannelSlideAttribute(handle2, 2, current_volume, prefs.change_volume_fade_time)
            # STOP COMMAND
            elif pctl.playerCommand == 'stop':
                if player1_status != 'stopped':
                    player1_status = 'stopped'
                    BASS_ChannelSlideAttribute(handle1, 2, 0, prefs.pause_fade_time)
                    time.sleep(prefs.pause_fade_time / 1000)
                    channel1 = BASS_ChannelStop(handle1)
                    BASS_StreamFree(handle1)
                if player2_status != 'stopped':
                    player2_status = 'stopped'
                    BASS_ChannelSlideAttribute(handle2, 2, 0, prefs.pause_fade_time)
                    time.sleep(prefs.pause_fade_time / 1000)
                    channel2 = BASS_ChannelStop(handle2)
                    BASS_StreamFree(handle2)
            # SEEK COMMAND
            elif pctl.playerCommand == 'seek':

                if player1_status == 'playing' or player1_status == 'paused':

                    bytes_position = BASS_ChannelSeconds2Bytes(handle1, pctl.new_time + pctl.start_time)
                    BASS_ChannelSetPosition(handle1, bytes_position, 0)
                    BASS_ChannelPlay(handle1, False)
                elif player2_status == 'playing' or player2_status == 'paused':

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
            if player1_status == 'stopping':
                time.sleep(prefs.cross_fade_time / 1000)
                BASS_StreamFree(handle1)
                player1_status = 'stopped'
                # print('player1 stopped')
                channel1 = BASS_ChannelStop(handle1)
            if player2_status == 'stopping':
                time.sleep(prefs.cross_fade_time / 1000)
                BASS_StreamFree(handle2)
                player2_status = 'stopped'
                channel2 = BASS_ChannelStop(handle2)

    pctl.playerCommand = 'done'





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

elif system != 'mac':
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
                artist = pctl.master_library[index].artist
                pt = 0
                key = pctl.master_library[index].title + pctl.master_library[index].filename
                if artist == "":
                    artist = "<Artist Unspecified>"
                if key in pctl.star_library:
                    pt = int(pctl.star_library[key])

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
                gn = [pctl.master_library[index].genre]
                pt = 0

                key = pctl.master_library[index].title + pctl.master_library[index].filename
                if key in pctl.star_library:
                    pt = int(pctl.star_library[key])

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
                album = pctl.master_library[index].album
                pt = 0
                key = pctl.master_library[index].title + pctl.master_library[index].filename
                if album == "":
                    album = "<Album Unspecified>"

                if key in pctl.star_library:
                    pt = int(pctl.star_library[key])

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
window_title = title
window_title = window_title.encode('utf-8')


def load_font(name, size, ext=False):
    if ext:
        fontpath = name.encode('utf-8')
    else:
        b = install_directory
        b = b.encode('utf-8')
        c = name.encode('utf-8')
        fontpath = b + b'/gui/' + c

    return TTF_OpenFont(fontpath, size)


alt_font = 'DroidSansFallback.ttf' #'DroidSans.ttf'

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
#
# font11a = load_font('c:/Windows/Fonts/meiryob.ttc', 16, True)
# font13s = load_font('c:/Windows/Fonts/meiryob.ttc', 13, True)

font_dict = {}
font_dict[13] = (font6, font6b)
font_dict[11] = (font4, font4b)
font_dict[10] = (font3, font3b)
font_dict[12] = (font2, font2b)
font_dict[16] = (font1, font1b)
font_dict[14] = (font7, font7b)
# font_dict[116] = (font11a, font1)
# font_dict[113] = (font13s, font6)

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

icon = IMG_Load(b_active_directory + b"/gui/icon.png")

SDL_SetWindowIcon(t_window, icon)

#SDL_SetHint(SDL_HINT_RENDER_SCALE_QUALITY,b"1")


ttext = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_UNKNOWN, SDL_TEXTUREACCESS_TARGET, window_size[0], window_size[1])
SDL_SetRenderTarget(renderer, ttext)
# print(SDL_GetError())
SDL_SetRenderTarget(renderer, None)

abc = SDL_Rect(0, 0, window_size[0], window_size[1])
SDL_RenderCopy(renderer, ttext, None, abc)
gui.pl_update = 2

SDL_SetRenderDrawColor(renderer, colours.top_panel_background[0], colours.top_panel_background[1], colours.top_panel_background[2], colours.top_panel_background[3])
SDL_RenderClear(renderer)
SDL_RenderPresent(renderer)

fontb1 = load_font('NotoSansCJKjp-Bold.ttf', 12)

if system != 'windows':

    def hit_callback(win, point, data):

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

    class WinTask:



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
    if l[0] < r[0]:
        return False
    if l[1] < r[1]:
        return False
    if l[0] > r[0] + r[2]:
        return False
    if l[1] > r[1] + r[3]:
        return False
    return True


class Drawing:

    def __init__(self):
        self.sdl_rect = SDL_Rect(10, 10, 10, 10)
        self.text_width_p = pointer(c_int(0))

    def fast_fill_rect(self, x, y, w, h):
        self.sdl_rect.x = x
        self.sdl_rect.y = y
        self.sdl_rect.w = w
        self.sdl_rect.h = h
        SDL_RenderFillRect(renderer, self.sdl_rect)

    def rect(self, location, wh, colour, fill=False):

        self.sdl_rect.x = location[0]
        self.sdl_rect.y = location[1]
        self.sdl_rect.w = wh[0]
        self.sdl_rect.h = wh[1]

        if fill is True:
            SDL_SetRenderDrawColor(renderer, colour[0], colour[1], colour[2], colour[3])
            SDL_RenderFillRect(renderer, self.sdl_rect)
        else:
            SDL_SetRenderDrawColor(renderer, colour[0], colour[1], colour[2], colour[3])
            SDL_RenderDrawRect(renderer, self.sdl_rect)

    def rect_r(self, rect, colour, fill=False):
        self.rect((rect[0], rect[1]), (rect[2], rect[3]), colour, fill)
        
    def line(self, x1, y1, x2, y2, colour):

        SDL_SetRenderDrawColor(renderer, colour[0], colour[1], colour[2], colour[3])
        SDL_RenderDrawLine(renderer, x1, y1, x2, y2)

    def text_calc(self, text, font):

        TTF_SizeUTF8(font_dict[font][0], text.encode('utf-8'), self.text_width_p, None)
        return self.text_width_p.contents.value


draw = Drawing()


text_cache = []  # location, text, dst(sdl rect), c(texture)
calc_cache = []
ttc = {}
ttl = []


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
        ttl.append(key)

        # Delete oldest cached text if cache too big to avoid performance slowdowns
        if len(ttl) > 450:
            key = ttl[0]
            so = ttc[key]
            SDL_DestroyTexture(so[1])
            del ttc[key]
            del ttl[0]

        return dst.w


def draw_text(location, text, colour, font, max=1000):
    global text_cache
    return draw_text2(location, text, colour, font, max)


temp_dest = SDL_Rect(0, 0)


class GallClass:
    def __init__(self):
        self.gall = {}
        self.size = [album_mode_art_size, album_mode_art_size]
        self.queue = []

    def get_file_source(self, index):

        global album_art_gen

        sources = album_art_gen.get_sources(index)
        if len(sources) == 0:
            return False
        offset = album_art_gen.get_offset(pctl.master_library[index].fullpath,sources)
        return sources[offset]


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

    global album_art_gen
    album_art_gen.clear_cache()

    while len(gall_ren.queue) > 0:
        time.sleep(0.01)

    for key, value in gall_ren.gall.items():
        SDL_DestroyTexture(value[2])
    gall_ren.gall = {}

    global gui
    gui.update += 1

class ImageObject():

    def __init__(self):

        self.index = 0
        self.texture = None
        self.rect = None
        self.request_size = (0,0)
        self.original_size = (0,0)
        self.actual_size = (0,0)
        self.source = ""
        self.offset = 0
        self.stats = True


class AlbumArt():

    def __init__(self):
        self.image_types = {'jpg', 'JPG', 'jpeg', 'JPEG', 'PNG', 'png', 'BMP', 'bmp', 'GIF', 'gif'}
        self.art_folder_names = {'art', 'scans', 'scan', 'booklet', 'images', 'image', 'cover',
                                'covers', 'coverart', 'albumart', 'gallery', 'jacket', 'artwork',
                                'bonus', 'bk'}
        self.source_cache = {}
        self.image_cache = []
        self.current_wu = None

    def get_info(self, index):

        sources = self.get_sources(index)
        if len(sources) == 0:
            return False
        offset = self.get_offset(pctl.master_library[index].fullpath, sources)

        return [sources[offset][0], len(sources), offset]


    def get_sources(self, index):

        filepath = pctl.master_library[index].fullpath

        # Check if source list already exists, if not, make it
        if index in self.source_cache:
            return self.source_cache[index]
        else:
             pass

        source_list = [] #istag,

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
                tt.read()
                if tt.has_pic is True and len(tt.picture) > 30:
                    source_list.append([True, filepath])

        except:

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

    def fast_display(self,index,location,box,source,offset):

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

    def open_external(self,index):

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

    def cycle_offset(self,index):

        filepath = pctl.master_library[index].fullpath
        sources = self.get_sources(index)
        parent_folder = os.path.dirname(filepath)
        # Find cached offset
        if parent_folder in folder_image_offsets:
            # Advance the offset by one
            folder_image_offsets[parent_folder] += 1
            # Reset the offset if greater then number of images avaliable
            if folder_image_offsets[parent_folder] > len(sources) - 1:
                folder_image_offsets[parent_folder] = 0
        return 0


    def get_offset(self,filepath, source):

        # Check if folder offset already exsts, if not, make it
        parent_folder = os.path.dirname(filepath)

        if parent_folder in folder_image_offsets:

            # Reset the offset if greater then number of images avaliable
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
            tag.read()
            return tag.picture

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

    def display(self,index,location,box,fast=False):

        filepath = pctl.master_library[index].fullpath

        source = self.get_sources(index)
        if len(source) == 0:
            return False

        offset = self.get_offset(filepath, source)

        # Check if request matches previous
        if self.current_wu is not None and self.current_wu.source == source[offset][1] and \
                self.current_wu.request_size == box:
            self.render(self.current_wu,location)
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

            # Generate
            g = io.BytesIO()
            g.seek(0)
            im = Image.open(source_image)
            o_size = im.size
            if im.mode != "RGB":
                im = im.convert("RGB")
            im.thumbnail((box[0], box[1]), Image.ANTIALIAS)
            im.save(g, 'JPEG')
            g.seek(0)

            # im.thumbnail((50, 50), Image.ANTIALIAS)
            # pixels = im.getcolors(maxcolors=2500)
            # print(pixels)
            # pixels = sorted(pixels, key=lambda x: x[0], reverse=True)[:3]
            # colours.playlist_panel_background = [pixels[0][1][0], pixels[0][1][1], pixels[0][1][2], 255]
            # colours.row_select_highlight = [pixels[1][1][0], pixels[1][1][1], pixels[1][1][2], 255]
            # colours.title_text = [pixels[2][1][0], pixels[2][1][1], pixels[2][1][2], 255]
            # colours.artist_text = [pixels[2][1][0], pixels[2][1][1], pixels[2][1][2], 255]

            wop = sdl2.rw_from_object(g)
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
            unit.actual_size = (dst.w,dst.h)
            unit.source = source[offset][1]
            unit.offset = offset

            self.current_wu = unit
            self.image_cache.append(unit)

            self.render(unit, location)

            if len(self.image_cache) > 25:
                SDL_DestroyTexture(self.image_cache[0].texture)
                del self.image_cache[0]
        except:
            print("Image processing error")
            self.current_wu = None
            del self.source_cache[index][offset]
            return 1

        return 0

    def render(self,unit,location):

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


def trunc_line(line, font, px):
    trunk = False

    while draw.text_calc(line, font) > px:
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
    global pctl
    global default_playlist
    global enc_field

    todo = []

    if mode == 1:
        todo = [index]
    elif mode == 0:
        for b in range(len(default_playlist)):
            if pctl.master_library[default_playlist[b]].parent_folder_name == pctl.master_library[index].parent_folder_name:
                todo.append(default_playlist[b])

    for q in range(len(todo)):

        key = pctl.master_library[todo[q]].title + pctl.master_library[todo[q]].filename

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

        if key in pctl.star_library:
            newkey = pctl.master_library[todo[q]].title + pctl.master_library[todo[q]].filename
            if newkey not in pctl.star_library:
                pctl.star_library[newkey] = copy.deepcopy(pctl.star_library[key])
                # del pctl.star_library[key]


def transfer_tracks(index, mode, to):
    todo = []

    if mode == 0:
        todo = [index]
    elif mode == 1:
        for b in range(len(default_playlist)):
            if pctl.master_library[default_playlist[b]].parent_folder_name == pctl.master_library[index].parent_folder_name:
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


# -----------------------------
# LOADING EXTRA
control_line_bottom = 35

s_image1 = IMG_Load(b_active_directory + b'/gui/playw.png')
c1 = SDL_CreateTextureFromSurface(renderer, s_image1)
SDL_SetTextureColorMod(c1, colours.bottom_panel_colour[0], colours.bottom_panel_colour[1], colours.bottom_panel_colour[2])
dst1 = SDL_Rect(25, window_size[1] - control_line_bottom)
dst1.w = 14
dst1.h = 14

s_image2 = IMG_Load(b_active_directory + b'/gui/ffw.png')
c2 = SDL_CreateTextureFromSurface(renderer, s_image2)
SDL_SetTextureColorMod(c2, colours.bottom_panel_colour[0], colours.bottom_panel_colour[1], colours.bottom_panel_colour[2])
dst2 = SDL_Rect(240, window_size[1] - control_line_bottom)
dst2.w = 28
dst2.h = 14

s_image3 = IMG_Load(b_active_directory + b'/gui/bbw.png')
c3 = SDL_CreateTextureFromSurface(renderer, s_image3)
SDL_SetTextureColorMod(c3, colours.bottom_panel_colour[0], colours.bottom_panel_colour[1], colours.bottom_panel_colour[2])
dst3 = SDL_Rect(180, window_size[1] - control_line_bottom)
dst3.w = 28
dst3.h = 14

# s_image5 = IMG_Load(b_active_directory + b'/gui/rep.png')
# c5 = SDL_CreateTextureFromSurface(renderer, s_image5)
# dst3 = SDL_Rect(180, window_size[1] - control_line_bottom)
# dst3.w = 28
# dst3.h = 14

panelY = 30
panelBY = 51

bb_type = 0

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
class Menu:
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
        return [[170, 170, 170, 255], colours.bottom_panel_colour, None]

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
                draw.rect((self.pos[0], self.pos[1] + i * self.h), (self.w, self.h),
                          fx[1], True)

                # Detect if mouse is over this item
                rect = (self.pos[0], self.pos[1] + i * self.h, self.w, self.h - 1)
                fields.add(rect)

                if coll_point(mouse_position,
                              (self.pos[0], self.pos[1] + i * self.h, self.w, self.h - 1)):
                    draw.rect((self.pos[0], self.pos[1] + i * self.h), (self.w, self.h),
                              [colours.artist_text[0], colours.artist_text[1], colours.artist_text[2], 100], True)  # [15, 15, 15, 255]

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
                draw.rect((self.pos[0], self.pos[1] + i * self.h), (5, self.h),
                             colours.grey(40), True)

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
                        draw.rect((sub_pos[0], sub_pos[1] + w * self.h), (sub_w, self.h), fx[1], True)

                        # Detect if mouse is over this item
                        rect = (sub_pos[0], sub_pos[1] + w * self.h, sub_w, self.h - 1)
                        fields.add(rect)
                        if coll_point(mouse_position,
                                      (sub_pos[0], sub_pos[1] + w * self.h, sub_w, self.h - 1)):
                            draw.rect((sub_pos[0], sub_pos[1] + w * self.h), (sub_w, self.h),
                                      [colours.artist_text[0], colours.artist_text[1], colours.artist_text[2], 100], True)

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
                        draw_text((sub_pos[0] + 7, sub_pos[1] + 2 + w * self.h), label, fx[0],
                                  11)

                    # Render the menu outline
                    draw.rect(sub_pos, (sub_w, self.h * len(self.subs[self.sub_active])), colours.grey(40))

            if self.clicked:
                self.active = False
                self.clicked = False

            # Render the menu outline
            draw.rect(self.pos, (self.w, self.h * len(self.items)), colours.grey(40))

    def activate(self, in_reference=0, position=None):

        if position != None:
            self.pos = [position[0],position[1]]
        else:
            self.pos = [copy.deepcopy(mouse_position[0]),copy.deepcopy(mouse_position[1])]

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
    global gui
    global default_playlist
    default_playlist += cargo


def paste_deco():
    line_colour = colours.grey(50)

    if len(cargo) > 0:
        line_colour = [150, 150, 150, 255]

    return [line_colour, colours.bottom_panel_colour, None]

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
    pctl.multi_playlist.append(["New Playlist", 0, [], 0, 0, 0])


tab_menu.add_to_sub("Empty Playlist", 0, new_playlist)


def gen_top_100(index):
    global pctl

    def best(index):
        key = pctl.master_library[index].title + pctl.master_library[index].filename
        if pctl.master_library[index].length < 1:
            return 0
        if key in pctl.star_library:
            return int(pctl.star_library[key]) #/ pctl.master_library[index].length)
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

        if pctl.master_library[index].length < 1:
            return 0
        else:
            return int(pctl.master_library[index].length)

    playlist = copy.deepcopy(pctl.multi_playlist[index][2])
    playlist = sorted(playlist, key=length, reverse=True)

    pctl.multi_playlist.append(
            [pctl.multi_playlist[index][0] + " <Duration Sorted>", 0, copy.deepcopy(playlist), 0, 1, 0])


tab_menu.add_to_sub("Duration Sorted", 0, gen_sort_len, pass_ref=True)


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

    pctl.multi_playlist.append(
            [pctl.multi_playlist[index][0] + line, 0, copy.deepcopy(playlist), 0, 0, 0])

tab_menu.add_to_sub("Year Old->New", 0, gen_sort_date, pass_ref=True)


def gen_sort_date_new(index):
    gen_sort_date(index, True)

tab_menu.add_to_sub("Year New->Old", 0, gen_sort_date_new, pass_ref=True)


def gen_500_random(index):
    global pctl

    playlist = copy.deepcopy(pctl.multi_playlist[index][2])
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
        key = pctl.master_library[p].title + pctl.master_library[p].filename
        if key in pctl.star_library:
            if pctl.star_library[key] > 300:
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
    global gui
    global pctl
    global default_playlist

    del pctl.multi_playlist[index][2][:]
    if pctl.playlist_active == index:
        default_playlist = pctl.multi_playlist[index][2]
        reload_albums(quiet=True)

    # pctl.playlist_playing = 0

    gui.pl_update += 2


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
        if pctl.master_library[track].parent_folder_path not in paths:
            paths.append(pctl.master_library[track].parent_folder_path)

    for path in paths:
        folder = []
        for track in pctl.multi_playlist[pl][2]:
            if pctl.master_library[track].parent_folder_path == path:
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
    global gui
    global gui
    global message_box
    global message_box_text
    global mouse_click

    if len(pctl.multi_playlist) < 2:
        message_box = True
        message_box_text = "Make a new playlist first plz"
        mouse_click = False
        return

    gui.pl_update += 1
    gui.update += 1

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
    global gui
    pctl.multi_playlist[index][2] += cargo

    gui.pl_update += 1


def drop_deco():
    line_colour = colours.grey(50)

    if len(cargo) > 0:
        line_colour = [150, 150, 150, 255]

    return [line_colour, [0, 0, 0, 255], None]


tab_menu.add('Paste', append_playlist, paste_deco, pass_ref=True)


def append_current_playing(index):
    global gui
    global pctl
    if pctl.playing_state > 0 and len(pctl.track_queue) > 0:
        pctl.multi_playlist[index][2].append(pctl.track_queue[pctl.queue_step])
        gui.pl_update += 1


def sort_track_pl(pl):
    global pctl
    global pctl

    # REMOVEING FILES THAT HAVE CUE
    # print("need to check for cues")
    global cue_list

    deletes = []

    for t in range(len(pctl.multi_playlist[pl][2])):
        # print(pctl.master_library[pctl.multi_playlist[pl][2][t]]['cue'])
        for r in range(len(cue_list)):
            if cue_list[r] == pctl.master_library[pctl.multi_playlist[pl][2][t]].fullpath and \
                            pctl.master_library[pctl.multi_playlist[pl][2][t]].is_cue is False:
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
    parent = pctl.master_library[pctl.multi_playlist[pl][2][r]].parent_folder_name
    temp_map.append([pctl.multi_playlist[pl][2][r], pctl.master_library[pctl.multi_playlist[pl][2][r]].track_number])
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

        if parent == pctl.master_library[pctl.multi_playlist[pl][2][r]].parent_folder_name:
            temp_map.append(
                    [pctl.multi_playlist[pl][2][r], pctl.master_library[pctl.multi_playlist[pl][2][r]].track_number])
            r += 1

        else:
            temp_map = sorted(temp_map, key=keya)
            for i in range(len(temp_map)):
                pctl.multi_playlist[pl][2][s] = temp_map[i][0]
                s += 1
            parent = pctl.master_library[pctl.multi_playlist[pl][2][r]].parent_folder_name

            temp_map = []


tab_menu.add("Sort Tracks", sort_track_pl, pass_ref=True)

tab_menu.add("Append Playing", append_current_playing, pass_ref=True)


def get_playing_line():
    if 3 > pctl.playing_state > 0:
        title = pctl.master_library[pctl.track_queue[pctl.queue_step]].title
        artist = pctl.master_library[pctl.track_queue[pctl.queue_step]].artist
        return artist + " - " + title
    else:
        return 'Stoped'


def get_broadcast_line():
    if pctl.broadcast_active:
        title = pctl.master_library[pctl.broadcast_index].title
        artist = pctl.master_library[pctl.broadcast_index].artist
        return artist + " - " + title
    else:
        return 'No Title'


# Create track context menu
track_menu = Menu(140)


def open_license():
    target = os.path.join(install_directory, "license.txt")
    if system == "windows":
        os.startfile(target)
    elif system == 'mac':
        subprocess.call(['open', target])
    else:
        subprocess.call(["xdg-open", target])


def open_encode_out():
    if system == 'windows':
        line = r'explorer ' + encoder_output.replace("/", "\\")
        subprocess.Popen(line)
    else:
        line = encoder_output
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


track_menu.add('Open Folder', open_folder, pass_ref=True)


def remove_folder(index):
    global default_playlist

    for b in range(len(default_playlist) - 1, -1, -1):
        r_folder = pctl.master_library[index].parent_folder_name
        if pctl.master_library[default_playlist[b]].parent_folder_name == r_folder:
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
    r_folder = pctl.master_library[index].parent_folder_name
    for item in default_playlist:
        if r_folder == pctl.master_library[item].parent_folder_name:
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
                if pctl.master_library[default_playlist[b]].parent_folder_name == pctl.master_library[index].parent_folder_name:
                    cargo.append(default_playlist[b])
            if args[0] == 0:  # cut
                for b in reversed(range(len(default_playlist))):
                    if pctl.master_library[default_playlist[b]].parent_folder_name == pctl.master_library[index].parent_folder_name:
                        del default_playlist[b]

        elif args[1] == 3:  # playlist
            cargo += default_playlist
            if args[0] == 0:  # cut
                default_playlist = []

    elif args[0] == 2:  # Drop
        if args[1] == 1:  # Before

            insert = playlist_selected
            while insert > 0 and pctl.master_library[default_playlist[insert]].parent_folder_name == pctl.master_library[index].parent_folder_name:
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

    print(cargo)


def activate_track_box(index):
    global track_box
    global r_menu_index
    r_menu_index = index
    track_box = True


track_menu.add('Track Info...', activate_track_box, pass_ref=True)

track_menu.add_sub("Modify...", 120)
track_menu.add_sub("Insert/Remove...", 135)


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
    key = pctl.master_library[index].title + pctl.master_library[index].filename
    if key in pctl.star_library:
        del pctl.star_library[key]


track_menu.add_to_sub("Reset Play Count", 0, reset_play_count, pass_ref=True)


def reload_metadata(index):
    global todo
    global pctl
    global pctl

    todo = []
    for k in default_playlist:
        if pctl.master_library[index].parent_folder_name == pctl.master_library[k].parent_folder_name:
            if pctl.master_library[k].is_cue == False:
                todo.append(k)

    for track in todo:

        print('Reloading Metadate for ' + pctl.master_library[track].filename)
        key = pctl.master_library[track].title + pctl.master_library[track].filename
        star = 0

        if key in pctl.star_library:
            star = pctl.star_library[key]
            del pctl.star_library[key]

        audio = auto.File(pctl.master_library[track].fullpath)
        pctl.master_library[track].length = audio.duration
        pctl.master_library[track].title = rm_16(audio.title)
        pctl.master_library[track].artist = rm_16(audio.artist)
        pctl.master_library[track].album = rm_16(audio.album)
        pctl.master_library[track].track_number = str(audio.track)
        pctl.master_library[track].bitrate = audio.bitrate
        pctl.master_library[track].date = audio.year
        pctl.master_library[track].genre = rm_16(audio.genre)
        pctl.master_library[track].samplerate = audio.sample_rate


        key = pctl.master_library[track].title + pctl.master_library[track].filename
        pctl.star_library[key] = star


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
    global gui
    global gui
    global shift_selection
    global playlist_selected

    gui.update += 1
    gui.pl_update += 1

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

if prefs.enable_transcode:
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

    if len(pctl.master_library[index].artist) < 2:
        return
    line = "http://rateyourmusic.com/search?searchtype=a&searchterm=" + pctl.master_library[index].artist
    webbrowser.open(line, new=2, autoraise=True)

def clip_ar_al(index):
    line = pctl.master_library[index].artist + " - " + \
           pctl.master_library[index].album
    pyperclip.copy(line)

if prefs.show_rym:
    track_menu.add('Search Artist on RYM', ser_rym, pass_ref=True)
track_menu.add('Copy "Artist - Album"', clip_ar_al, pass_ref=True)


def clip_ar_tr(index):
    line = pctl.master_library[index].artist + " - " + \
           pctl.master_library[index].title

    pyperclip.copy(line)


track_menu.add('Copy "Artist - Track"', clip_ar_tr, pass_ref=True)


def queue_deco():
    line_colour = colours.grey(50)

    if len(pctl.force_queue) > 0:
        line_colour = [150, 150, 150, 255]

    return [line_colour, colours.bottom_panel_colour, None]


def broadcast_feature_deco():
    line_colour = colours.grey(50)

    if pctl.broadcast_active:
        line_colour = [150, 150, 150, 255]

    return [line_colour, colours.bottom_panel_colour, None]


def broadcast_select_track(index):
    global filepath
    global pctl

    if pctl.broadcast_active:
        filepath = pctl.master_library[pctl.broadcast_index].fullpath

        pctl.broadcast_index = index
        pctl.broadcast_playlist = copy.deepcopy(pctl.playlist_active)
        pctl.broadcast_position = default_playlist.index(pctl.broadcast_index)
        pctl.broadcast_time = 0
        pctl.target_open = pctl.master_library[pctl.broadcast_index].fullpath
        pctl.bstart_time = pctl.master_library[pctl.broadcast_index].start_time
        pctl.playerCommand = "encnext"
        pctl.playerCommandReady = True
        pctl.broadcast_line = pctl.master_library[pctl.broadcast_index].artist + " - " + \
                         pctl.master_library[pctl.broadcast_index].title


if default_player == 'BASS':
    track_menu.add('Broadcast This', broadcast_select_track, broadcast_feature_deco, pass_ref=True)

# Create top menu
x_menu = Menu(160)


def bass_features_deco():
    line_colour = colours.grey(150)
    if default_player != 'BASS':
        line_colour = colours.grey(20)
    return [line_colour, colours.bottom_panel_colour, None]



def toggle_dim_albums(mode=0):
    global dim_art
    global gui
    global gui

    if mode == 1:
        return dim_art

    dim_art ^= True
    gui.pl_update += 1
    gui.update += 1


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
    global album_mode_art_size

    album_mode = False
    side_panel_enable = True
    SDL_SetWindowSize(t_window, 670, 400)
    window_size = [670, 400]
    side_panel_size = 178
    update_layout = True
    album_mode_art_size = 130
    clear_img_cache()


def goto_album(playlist_no):

    global album_pos_px
    global album_dex

    px = 0
    row = 0

    for i in range(len(album_dex)):
        if album_dex[i] > playlist_no - 1:
            break
        row += 1
        if row > row_len - 1:

            row = 0
            px += album_mode_art_size + album_v_gap

    if album_pos_px - 20 < px < album_pos_px + window_size[1]:
        pass
    else:
        album_pos_px = px - 60 - album_mode_art_size - album_v_gap
        album_pos_px += 10

        if album_pos_px < 0 - 55:
            album_pos_px = 0 - 55


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

    reload_albums()

    goto_album(pctl.playlist_playing)


def activate_info_box():
    pref_box.enabled = True


x_menu.add("Go To Playing", pctl.show_current)

x_menu.add("Create Empty Playlist", new_playlist)

x_menu.add("Settings...", activate_info_box)

x_menu.add_sub("Database...", 120)


def export_stats():
    global pctl

    playlist_time = 0
    play_time = 0
    for index in pctl.multi_playlist[pctl.playlist_active][2]:
        playlist_time += int(pctl.master_library[index].length)
        key = pctl.master_library[index].title + pctl.master_library[index].filename
        if key in pctl.star_library:
            play_time += pctl.star_library[key]

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
    elif system == 'mac':
        subprocess.call(['open', target])
    else:
        subprocess.call(["xdg-open", target])


def export_database():
    global message_box
    global message_box_text

    xport = open('DatabaseExport.csv', 'wb')
    for num in range(master_count):
        line = []
        # print(str(pctl.master_library[num]))
        # continue
        # print(pctl.master_library[num])
        line.append(str(pctl.master_library[num].artist))
        line.append(str(pctl.master_library[num].title))
        line.append(str(pctl.master_library[num].album))
        line.append(str(pctl.master_library[num].track_number))
        if pctl.master_library[num].is_cue == False:
            line.append('FILE')
        else:
            line.append('CUE')
        line.append(str(pctl.master_library[num].length))
        line.append(str(pctl.master_library[num].date))
        line.append(pctl.master_library[num].genre)

        key = pctl.master_library[num].title + pctl.master_library[num].filename
        if key in pctl.star_library:
            line.append(str(int(pctl.star_library[key])))
        else:
            line.append('0')
        line.append(pctl.master_library[num].fullpath)

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
x_menu.add_to_sub("Reset Image Cache", 0, clear_img_cache)

# def test():
#     global message_box
#     global message_box_text
#     global pctl
#
#     found = 0
#     star2 = {}
#
#     for key, value in pctl.master_library.items():
#         ref = value.title + value.filename
#         if ref in pctl.star_library:
#             found += 1
#             star2[ref] = pctl.star_library[ref]
#
#     have = sum(star2.values())
#     total_pl = sum(pctl.star_library.values())
#
#     rem = len(pctl.star_library) - len(star2)
#
#     prec = ""
#     if total_pl != 0:
#         perc = str(int(have / total_pl * 100)) + "% listening time accounted for. "
#
#     if not key_shift_down:
#         message_box_text = "Warning: Will lose individual play count for tracks not imported. "
#         message_box_text += perc
#         message_box_text += str(rem) + " references will be forgotten. Hold shift and try again to apply."
#         message_box = True
#
#         return
#
#     else:
#         pass
#         # pctl.star_library = star2
#         # pctl.star_library total_pl - have


# x_menu.add_to_sub("Test", 0, test)


def reset_missing_flags():
    for index in default_playlist:
        pctl.master_library[index].found = True


# x_menu.add('Reset Missing Flags', reset_missing_flags)
x_menu.add_to_sub("Reset Missing Flags", 0, reset_missing_flags)


def toggle_broadcast():
    global pctl
    global message_box
    global message_box_text

    if system == 'windows' and not os.path.isfile(install_directory + "/encoder/oggenc2.exe") and not \
            os.path.isfile(install_directory + "/encoder/lame.exe") and not os.path.isfile(install_directory + "/encoder/opusenc.exe"):
        message_box = True
        message_box_text = "Missing Encoder. See readme file."
        return

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
    line_colour = colours.grey(150)
    if default_player != 'BASS':
        line_colour = colours.grey(20)
        return [line_colour, colours.bottom_panel_colour, None]
    if pctl.broadcast_active:
        return [[150, 150, 150, 255], [24, 25, 60, 255], "Stop Broadcast"]
    return [line_colour, colours.bottom_panel_colour, None]


if default_player == 'BASS' and os.path.isfile(os.path.join(install_directory, "config.txt")):
    x_menu.add("Start Broadcast", toggle_broadcast, broadcast_deco)


def clear_queue():
    global pctl
    pctl.force_queue = []


x_menu.add('Clear Queue', clear_queue, queue_deco)


x_menu.add_sub("Playback...", 120)


def play_pause_deco():
    line_colour = colours.grey(150)
    if pctl.playing_state == 1:
        return [line_colour, colours.bottom_panel_colour, "Pause"]
    if pctl.playing_state == 2:
        return [line_colour, colours.bottom_panel_colour, "Resume"]
    return [line_colour, colours.bottom_panel_colour, None]


def play_pause():
    if pctl.playing_state == 0:
        pctl.play()
    else:
        pctl.pause()

x_menu.add_to_sub('Play', 1, play_pause, play_pause_deco)


def stop():
    pctl.stop()

x_menu.add_to_sub('Stop/Eject', 1, stop)

x_menu.add_to_sub('Advance', 1, pctl.advance)
x_menu.add_to_sub('Back', 1, pctl.back)

def random_track():

    old = pctl.random_mode
    pctl.random_mode = True
    pctl.advance()
    pctl.random_mode = old

x_menu.add_to_sub('Random Track', 1, random_track)


def radio_random():

    pctl.advance(rr=True)

x_menu.add_to_sub('Radio Random', 1, radio_random)

x_menu.add_to_sub('Revert', 1, pctl.revert)



def repeat_deco():
    line_colour = colours.grey(150)
    if pctl.repeat_mode:
        return [line_colour, colours.bottom_panel_colour, "Disable Repeat"]
    return [line_colour, colours.bottom_panel_colour, None]


def toggle_repeat():
    pctl.repeat_mode ^= True

x_menu.add_to_sub('Enable Repeat', 1, toggle_repeat, repeat_deco)

def random_deco():
    line_colour = colours.grey(150)
    if pctl.random_mode:
        return [line_colour, colours.bottom_panel_colour, "Disable Random"]
    return [line_colour, colours.bottom_panel_colour, None]


def toggle_random():
    pctl.random_mode ^= True

x_menu.add_to_sub('Enable Random', 1, toggle_random, random_deco)

def toggle_level_meter(mode=0):
    global gui

    if mode == 1:
        return gui.turbo

    if gui.turbo is True:
        gui.vis = 0
        gui.turbo = False
    elif gui.turbo is False:
        gui.turbo = True
        gui.vis = 2


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
        bg = colours.bottom_panel_colour
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
    global gui
    global shift_selection

    gui.pl_update += 1
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
    global pctl
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
            global pctl

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
                if os.path.isfile(filepath) is True:

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

                    nt = TrackClass()
                    nt.index = master_count
                    nt.fullpath = filepath.replace('\\', '/')
                    nt.filename = filename
                    nt.parent_folder_path = os.path.dirname(filepath.replace('\\', '/'))
                    nt.parent_folder_name = os.path.splitext(os.path.basename(filepath))[0]
                    nt.file_ext = os.path.splitext(os.path.basename(filepath))[1][1:].upper()
                    
                    nt.artist = PERFORMER
                    nt.title = TITLE
                    nt.length = LENGTH
                    nt.bitrate = bitrate
                    nt.album = ALBUM
                    nt.date = DATE.replace('"', '')
                    nt.track_number = TN
                    nt.start_time = START
                    nt.is_cue = True
                    nt.samplerate = SAMPLERATE
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

    def add_file(path):
        #bm.get("add file start")
        global master_count
        global pctl
        global DA_Formats
        global to_got
        global pctl
        global auto_play_import

        if os.path.splitext(path)[1][1:] in {"CUE", 'cue'}:
            add_from_cue(path)
            return 0

        if os.path.splitext(path)[1][1:] not in DA_Formats:
            return 1

        global gui
        to_got += 1
        gui.update = 1


        path = path.replace('\\', '/')

        if path in loaded_pathes_cache:
            de = loaded_pathes_cache[path]
            if pctl.master_library[de].fullpath in cue_list:
                #bm.get("File has an associated .cue file... Skipping")
                return
            added.append(de)
            if auto_play_import:
                pctl.jump(copy.deepcopy(de))

                auto_play_import = False
            #bm.get("dupe track")
            return

        time.sleep(0.002)

        audio = auto.File(path)

        nt = TrackClass()
        
        nt.index = master_count
        nt.fullpath = path.replace('\\', '/')
        nt.filename = os.path.basename(path)
        nt.parent_folder_path = os.path.dirname(path.replace('\\', '/'))
        nt.parent_folder_name = get_end_folder(os.path.dirname(path))
        nt.file_ext = os.path.splitext(os.path.basename(path))[1][1:].upper()
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

        pctl.master_library[master_count] = nt
        added.append(master_count)
        master_count += 1
        #bm.get("fill entry")
        if auto_play_import:
            pctl.jump(master_count - 1)
            auto_play_import = False

    def pre_get(direc):
        global DA_Formats
        global to_get
        global gui

        items_in_dir = os.listdir(direc)
        for q in range(len(items_in_dir)):
            if os.path.isdir(os.path.join(direc, items_in_dir[q])):
                pre_get(os.path.join(direc, items_in_dir[q]))
        for q in range(len(items_in_dir)):
            if os.path.isdir(os.path.join(direc, items_in_dir[q])) is False:
                if os.path.splitext(items_in_dir[q])[1][1:] in DA_Formats:
                    to_get += 1
                    gui.update += 1



    def gets(direc):
        dupe = False
        global pctl
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
        for i in range(len(pctl.master_library)):
            dic[pctl.master_library[i].fullpath.replace('\\', '/')] = i
        return dic

    # print(pctl.master_library)

    global gui
    global transcode_list
    global transcode_state
    global default_player
    global album_art_gen

    while True:
        time.sleep(0.05)

        # FOLDER ENC
        if len(transcode_list) > 0:
            print(8)
            transcode_state = ""
            gui.update += 1

            folder_items = transcode_list[0]

            folder_name = pctl.master_library[folder_items[0]].artist + " - " + pctl.master_library[folder_items[0]].album

            if folder_name == " - ":
                folder_name = pctl.master_library[folder_items[0]].filename

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
                print(pctl.master_library[item].fullpath)
                command += '-i "'
                command += pctl.master_library[item].fullpath
                command += '" '

            command += '-filter_complex "[0:a:0][1:a:0] concat=n='
            command += str(len(folder_items))
            command += ':v=0:a=1[out]" -map "[out]" '
            command += full_wav_out

            print(4)
            if pctl.master_library[folder_items[0]].is_cue == True or len(folder_items) == 1:
                command = install_directory + '/encoder/ffmpeg -i "' + pctl.master_library[folder_items[0]].fullpath + '" ' + full_wav_out

                n_folder = []
                for i in reversed(range(len(folder_items))):
                    if pctl.master_library[folder_items[i]].fullpath != pctl.master_library[folder_items[0]].fullpath:
                        n_folder.append(folder_items[i])
                        del folder_items[i]
                print(2)
                if len(n_folder) > 0:
                    transcode_list.append(n_folder)

            print(command)

            transcode_state = "(Decoding)"
            gui.update += 1

            print(shlex.split(command))
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.call(shlex.split(command), stdout=subprocess.PIPE, shell=False, startupinfo=startupinfo)

            print('done ffmpeg')

            transcode_state = "(Encoding)"
            gui.update += 1

            command = install_directory + '/encoder/opusenc --bitrate ' + str(transcode_bitrate) +  ' ' + full_wav_out + ' ' + full_opus_out

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
            cu += 'PERFORMER "' + pctl.master_library[folder_items[0]].artist + '"\n'
            cu += 'TITLE "' + pctl.master_library[folder_items[0]].album + '"\n'
            cu += 'REM DATE "' + pctl.master_library[folder_items[0]].date + '"\n'
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
                cu += pctl.master_library[item].title
                cu += '"\n'

                cu += ' PERFORMER "'
                cu += pctl.master_library[item].artist
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

                if default_player == 'BASS' and pctl.master_library[item].is_cue is False:
                    tracklen = get_backend_time(pctl.master_library[item].fullpath)
                else:
                    tracklen = int(pctl.master_library[item].length)

                run_time += tracklen
                track += 1

            cue = open(output_dir + folder_name + ".cue", 'w', encoding="utf_8")
            cue.write(cu)
            cue.close()

            album_art_gen.save_thumb(folder_items[0], (720, 720), output_dir + folder_name)
            print('finish')

            del transcode_list[0]
            transcode_state = ""
            gui.update += 1

        while len(gall_ren.queue) > 0:

            # print("ready")

            index = gall_ren.queue[0]
            order = gall_ren.gall[index]

            source = gall_ren.get_file_source(index)

            # print(source)

            if source is False:
                order[0] = 0
                gall_ren.gall[index] = order
                del gall_ren.queue[0]
                continue

            try:
                if source[0] is True:
                    # print('tag')
                    source_image = io.BytesIO(album_art_gen.get_embed(index))

                else:
                    source_image = open(source[1], 'rb')

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

                gui.update += 1
                del source
                time.sleep(0.01)

            except:
                print('image error')
                order = [0, None, None, None]
                gall_ren.gall[index] = order

            del gall_ren.queue[0]

        if loaderCommandReady is True:
            if loaderCommand == LC_Folder:
                to_get = 0
                to_got = 0
                loaded_pathes_cache = cache_paths()
                pre_get(paths_to_load)
                gets(paths_to_load)
            elif loaderCommand == LC_File:
                loaded_pathes_cache = cache_paths()
                add_file(paths_to_load)

            loaderCommand = LC_Done
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
        if pctl.master_library[default_playlist[position]].parent_folder_name == pctl.master_library[default_playlist[current - 1]].parent_folder_name:
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
        if pctl.master_library[default_playlist[current]].parent_folder_name != pctl.master_library[default_playlist[current + 1]].parent_folder_name:
            break
        else:
            current += 1
    return playing, album


def get_folder_list(index):
    global pctl
    playlist = []

    for item in default_playlist:
        if pctl.master_library[item].parent_folder_name == pctl.master_library[index].parent_folder_name and \
                pctl.master_library[item].album == pctl.master_library[index].album:

            playlist.append(item)
    return list(set(playlist))


def reload_albums(quiet=False):
    global album_dex
    global side_panel_size
    global gui
    global gui
    global update_layout
    global album_pos_px
    global playlist_width
    global old_album_pos

    album_pos_px = old_album_pos

    current_folder = ""
    p = 0
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
            side_panel_size = window_size[0] - 300
            playlist_width = album_playlist_width
        else:
            side_panel_size = old_side_pos
    gui.update += 2
    gui.pl_update += 2
    update_layout = True
    goto_album(pctl.playlist_playing)


# ------------------------------------------------------------------------------------
# WEBSERVER

def webserv():
    if prefs.enable_web is False:
        return 0

    from flask import Flask, redirect, send_file, abort, request
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


    @app.route('/remote')
    def remote():

        if not prefs.allow_remote:
            abort(403)
            return (0)

        image_line = " "
        if pctl.playing_state > 0:

            image_line = '<img src="data:image/jpeg;base64,'
            bimage = album_art_gen.get_base64(pctl.track_queue[pctl.queue_step], (300, 300))
            if type(bimage) is list:
                image_line = "<br><br>&nbsp&nbsp&nbsp&nbsp&nbspNo Album Art"
            else:
                image_line += bimage.decode("utf-8")
                image_line += '" alt="No Album Art" style="float:left;" />'

        randomline = "Is Off"
        if pctl.random_mode:
            randomline = "is On"

        repeatline = "Is Off"
        if pctl.repeat_mode:
            repeatline = "is On"

        ppline = ""

        for i in range(len(pctl.multi_playlist)):

            if i == pctl.playlist_active:
                ppline += "<strong>" + pctl.multi_playlist[i][0] + "</strong> "
            else:
                ppline += pctl.multi_playlist[i][0] + " "


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

            line += pctl.master_library[default_playlist[i]].artist + " - " + pctl.master_library[default_playlist[i]].title
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
                                          pline=ppline,
                                          list=p_list,
                                          seekbar=seek_line
                                          )

    @app.route('/radio')
    def radio():
        global pctl
        image_line = '<img src="data:image/jpeg;base64,'
        bimage = album_art_gen.get_base64(pctl.broadcast_index, (300, 300))
        if type(bimage) is list:
            image_line = "<br><br>&nbsp&nbsp&nbsp&nbsp&nbspNo Album Art"
        else:
            image_line += bimage.decode("utf-8")
            image_line += '" alt="No Album Art" style="float:left;" />'

        return radio_template.substitute(play=get_broadcast_line(), image=image_line)

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

    @app.route('/load', methods=['POST', 'GET', 'DELETE'])
    def ex_load():
        global arg_queue
        print(request.method)
        print(request.get_data())
        print("Load ext")
        return "done"

    @app.route('/remote/back')
    def back():
        if not prefs.allow_remote:
            abort(403)
            return 0
        global pctl
        pctl.back()
        return redirect(request.referrer)

    @app.route('/remote/jump<int:indexno>')
    def jump(indexno):
        if not prefs.allow_remote:
            abort(403)
            return (0)
        global pctl
        pctl.jump(indexno)
        return redirect(request.referrer)

    @app.route('/remote/forward')
    def fw():
        if not prefs.allow_remote:
            abort(403)
            return (0)
        global pctl
        pctl.advance()
        return redirect(request.referrer)

    @app.route('/remote/pause')
    def pu():
        if not prefs.allow_remote:
            abort(403)
            return (0)
        global pctl
        pctl.pause()
        return redirect(request.referrer)

    @app.route('/remote/play')
    def pl():
        if not prefs.allow_remote:
            abort(403)
            return (0)
        global pctl
        pctl.play()

        return redirect(request.referrer)

    @app.route('/remote/stop')
    def st():
        if not prefs.allow_remote:
            abort(403)
            return (0)
        global pctl
        pctl.stop()
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

    @app.route('/remote/seek<int:per>')
    def seek(per):
        if not prefs.allow_remote:
            abort(403)
            return (0)

        global pctl

        if per > 100:
            per = 100

        pctl.new_time = pctl.playing_length / 100 * per
        pctl.playerCommand = 'seek'
        pctl.playerCommandReady = True
        pctl.playing_time = pctl.new_time

        return redirect(request.referrer)

    @app.route('/remote/random')
    def ran():
        if not prefs.allow_remote:
            abort(403)
            return (0)
        pctl.random_mode ^= True
        return redirect(request.referrer)

    @app.route('/remote/repeat')
    def rep():
        if not prefs.allow_remote:
            abort(403)
            return (0)
        pctl.repeat_mode ^= True
        return redirect(request.referrer)

    if prefs.expose_web is True:
        app.run(host='0.0.0.0 ', port=server_port)
    else:
        app.run(port=server_port)


if prefs.enable_web is True:
    webThread = threading.Thread(target=webserv)
    webThread.daemon = True
    webThread.start()

# --------------------------------------------------------------

def star_toggle(mode=0):
    global star_lines
    global gui
    global gui

    if mode == 1:
        return star_lines
    star_lines ^= True
    gui.update += 1
    gui.pl_update += 1


def split_toggle(mode=0):
    global split_line
    global gui
    global gui

    if mode == 1:
        return split_line
    split_line ^= True
    gui.update += 1
    gui.pl_update += 1


def toggle_titlebar_line(mode=0):
    global update_title
    if mode == 1:
        return update_title

    line = window_title
    SDL_SetWindowTitle(t_window, line)
    update_title ^= True


def toggle_borderless(mode=0):
    global draw_border
    if mode == 1:
        return draw_border

    draw_border ^= True
    if draw_border:
        SDL_SetWindowBordered(t_window, False)
    else:
        SDL_SetWindowBordered(t_window, True)

config_items = [
    ['Show playtime lines', star_toggle],
    ['Highlight artist name', split_toggle],
]



def toggle_break(mode=0):
    global break_enable
    global gui
    if mode == 1:
        return break_enable
    else:
        break_enable ^= True
        gui.pl_update += 1


def toggle_dd(mode=0):
    global dd_index
    global gui

    if mode == 1:
        return dd_index
    else:
        dd_index ^= True
        gui.pl_update += 1


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
    global gui
    global update_layout

    if mode == 1:
        return scroll_enable
    else:
        scroll_enable ^= True
        gui.pl_update += 1
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

    clear_text_cache()

    if mode == 1:
        return thick_lines
    else:
        thick_lines ^= True
        update_layout = True


def toggle_append_date(mode=0):
    global append_date
    global gui
    global gui

    if mode == 1:
        return append_date
    append_date ^= True
    gui.pl_update += 1
    gui.update += 1

def toggle_enable_web(mode=0):
    global prefs
    if mode == 1:
        return prefs.enable_web
    prefs.enable_web ^= True

def toggle_allow_remote(mode=0):
    global prefs
    if mode == 1:
        return prefs.allow_remote ^ True
    prefs.allow_remote ^= True
    
def toggle_expose_web(mode=0):
    global prefs
    if mode == 1:
        return prefs.expose_web
    prefs.expose_web ^= True
    
def toggle_transcode(mode=0):
    global prefs
    if mode == 1:
        return prefs.enable_transcode
    prefs.enable_transcode ^= True

def toggle_rym(mode=0):
    global prefs
    if mode == 1:
        return prefs.show_rym
    prefs.show_rym ^= True

config_items.append(['Show scrollbar', toggle_scroll])

config_items.append(['Break playlist by folders', toggle_break])

config_items.append(['Use double digit track indices', toggle_dd])

config_items.append(['Use thick rows', toggle_thick])

config_items.append(['Use custom line format', toggle_custom_line])

config_items.append(['Add release year to folder title', toggle_append_date])

config_items.append(['Force track advancing to open playlist', toggle_follow])

cursor = "|"
c_time = 0
c_blink = 0
key_shiftr_down = False
key_ctrl_down = False


class Over:
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

        self.tab_active = 4
        self.tabs = [
            ["Folder Import", self.files],
            ["Modules", self.funcs],
            ["Playlist Settings", self.config_v],
            ["View", self.config_b],
            ["Stats", self.stats],
            ["About", self.about]
        ]

    def funcs(self):

        x = self.box_x + self.item_x_offset
        y = self.box_y - 10

        y += 35
        self.toggle_square(x, y, toggle_enable_web, "Web interface*")
        y += 25
        self.toggle_square(x + 10, y, toggle_expose_web, "Allow external connections*")
        y += 25
        self.toggle_square(x + 10, y, toggle_allow_remote, "Disable remote control" + "  [localhost:" + str(server_port) + "/remote]")
        y += 35
        self.toggle_square(x, y, toggle_transcode, "Track Menu: Transcoding  (Folder to OPUS+CUE)*")
        self.button(x + 289, y-4, "Open output folder", open_encode_out)
        y += 25
        self.toggle_square(x, y, toggle_rym, "Track Menu: Search on RYM*")

        y = self.box_y + 220
        draw_text((x, y), "*Changes apply on restart", colours.grey(150), 11)

    def button(self, x, y, text, plug, width=0):

        w = width
        if w == 0:
            w = draw.text_calc(text, 11) + 10
        rect = (x, y, w, 20)
        draw.rect_r(rect, colours.grey(50))
        fields.add(rect)
        if coll_point(mouse_position, rect):
            draw.rect_r(rect, [40, 40, 40, 60], True)
            if self.click:
                plug()
        draw_text((x + int(w/2), rect[1] + 2, 2), text, [255, 255, 255, 140], 11)


    def toggle_square(self, x, y, function, text):

        draw_text((x + 20, y - 3), text, [255, 255, 255, 150], 11)
        draw.rect((x, y), (12, 12), [255, 255, 255, 13], True)
        draw.rect((x, y), (12, 12), [255, 255, 255, 16])
        if self.click and coll_point(mouse_position, (x - 20, y - 10, 180, 25)):
            function()
        if function(1):
            draw.rect((x + 3, y + 3), (6, 6), colours.folder_title, True)

    def config_b(self):

        global album_mode_art_size

        x = self.box_x + self.item_x_offset - 10
        y = self.box_y - 10

        x += 10
        y += 30

        draw_text((x, y), "Gallery art size:", colours.grey(200), 11)

        x += 90

        rect = (x,y,15,15)
        fields.add(rect)
        draw.rect_r(rect, [255,255,255,20], True)
        if coll_point(mouse_position, rect):
            draw.rect_r(rect, [255, 255, 255, 25], True)
            if self.click:
                if album_mode_art_size > 101:
                    album_mode_art_size -= 10
                    clear_img_cache()

        draw_text((x+4, y), "<", colours.grey(200), 11)

        x += 25

        draw.rect_r((x,y,40,15), [255,255,255,10], True)
        draw_text((x + 4, y), str(album_mode_art_size) + "px", colours.grey(200), 11)

        x +=  40 + 10

        rect = (x, y, 15, 15)
        fields.add(rect)
        draw.rect_r(rect, [255,255,255,20], True)
        if coll_point(mouse_position, rect):
            draw.rect_r(rect, [255, 255, 255, 25], True)
            if self.click:
                if album_mode_art_size < 350:
                    album_mode_art_size += 10
                    clear_img_cache()
        draw_text((x + 4, y), ">", colours.grey(200), 11)
        gall_ren.size = [album_mode_art_size, album_mode_art_size]

        y = self.box_y + 55
        x = self.box_x + self.item_x_offset

        self.toggle_square(x, y, toggle_borderless, "Borderless window")
        y += 30
        self.toggle_square(x, y, toggle_titlebar_line, "Show playing in titlebar")
        y += 30
        self.toggle_square(x, y, toggle_side_panel, "Show side panel")
        y += 30
        self.toggle_square(x, y, toggle_dim_albums, "Dim gallery when playing")
        y += 30
        if default_player == 'BASS':
            self.toggle_square(x, y, toggle_level_meter, "Show visualisation")

        # ----------

        x += 50
        y += 40
        self.button(x + 250, y, "Reset Layout", standard_size)
        x += 110
        self.button(x + 240, y, "Next Theme", advance_theme)


    def about(self):

        x = self.box_x + 110 + int((self.w - 110) / 2)
        y = self.box_y + 70

        draw_text((x, y, 2), "Tauon Music Box", colours.grey(200), 16)
        y += 32
        draw_text((x, y, 2), t_version, colours.grey(200), 12)
        y += 20
        draw_text((x, y, 2), "Copyright (c) 2015-2016 Taiko2k captain.gxj@gmail.com", colours.grey(200), 12)

        x = self.box_x + self.w - 115
        y = self.box_y + self.h - 35

        self.button(x, y, "License + Credits", open_license)

    def stats(self):

        x = self.box_x + self.item_x_offset - 10
        y = self.box_y - 10

        draw_text((x + 8 + 10 + 10, y + 40), "Tracks in Playlist:", colours.grey(200), 12)
        draw_text((x + 8 + 10 + 130, y + 40), '{:,}'.format(len(default_playlist)), colours.grey(200), 12)
        y += 20

        draw_text((x + 8 + 10 + 10, y + 40), "Playlist Length:", colours.grey(200), 12)

        playlist_time = 0
        for item in default_playlist:
            playlist_time += pctl.master_library[item].length

        line = str(datetime.timedelta(seconds=int(playlist_time)))

        draw_text((x + 8 + 10 + 130, y + 40), line, colours.grey(200), 12)
        y += 20
        draw_text((x + 8 + 10 + 10, y + 40), "Tracks in Database:", colours.grey(200), 12)
        draw_text((x + 8 + 10 + 130, y + 40), '{:,}'.format(master_count), colours.grey(200), 12)
        y += 20
        y += 20
        draw_text((x + 8 + 10 + 10, y + 40), "Total Playtime:", colours.grey(200), 12)
        draw_text((x + 8 + 10 + 130, y + 40), str(datetime.timedelta(seconds=int(pctl.total_playtime))), colours.grey(200), 14)

    def config_v(self):

        w = 370
        h = 220
        x = self.box_x + self.item_x_offset
        y = self.box_y

        x += 8
        y += 25
        y2 = y
        x2 = x
        for k in config_items:
            draw_text((x + 20, y - 3), k[0], [255, 255, 255, 150], 11)
            draw.rect((x, y), (12, 12), [255, 255, 255, 13], True)
            draw.rect((x, y), (12, 12), [255, 255, 255, 16])
            if self.click and coll_point(mouse_position, (x - 20, y - 10, 180 , 25)):
                k[1]()
            if k[1](1) is True:
                draw.rect((x + 3, y + 3), (6, 6), colours.folder_title, True)

            y += 30

            if y - y2 > 190:
                y = y2
                x += 205

    def inside(self):

        return coll_point(mouse_position, (self.box_x, self.box_y, self.w, self.h))

    def init2(self):

        self.init2done = True

        # Stats
        global pctl

        pctl.total_playtime = sum(pctl.star_library.values())

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

        draw.rect((self.box_x, self.box_y), (self.w, self.h), colours.top_panel_background, True)
        draw.rect((self.box_x, self.box_y), (self.w, self.h), colours.grey(50))
        draw.rect((self.box_x - 1, self.box_y - 1), (self.w + 2, self.h + 2), colours.grey(50))

        # temp
        if len(self.drives) < 1 and system == 'windows':
            raw_drives = win32api.GetLogicalDriveStrings()
            self.drives = raw_drives.split('\000')[:-1]

        current_tab = 0
        for item in self.tabs:

            box = [self.box_x + 1, self.box_y + 1 + (current_tab * 31), 110, 30]
            draw.rect_r(box, colours.tab_background, True)

            if current_tab == self.tab_active:
                colour = copy.deepcopy(colours.tab_background_active)
                colour[3] = 190
                draw.rect_r(box, colour, True)
            else:
                draw.rect_r(box, colours.tab_background, True)

            draw_text((box[0] + 55, box[1] + 7, 2), item[0], [200, 200, 200, 200], 12)

            if self.click and coll_point(mouse_position, box):
                self.tab_active = current_tab

            current_tab += 1

        draw.line(self.box_x + 110, self.box_y + 1, self.box_x + 110, self.box_y + self.h, colours.grey(50))

        self.tabs[self.tab_active][1]()

        self.click = False
        self.right_click = False

    def files(self):

        global dropped_file
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

        self.view_offset -= self.scroll * 2
        self.scroll = 0
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
            if extension.lower() in self.ext_colours:
                box_colour = self.ext_colours[extension.lower()]
            else:
                box_colour = [100 + random.randrange(154), 100 + random.randrange(154), 100 + random.randrange(154),
                              255]
                self.ext_colours[extension.lower()] = box_colour

            # HLT
            fields.add(row)
            if coll_point(mouse_position, row):
                draw.rect_r(row, [60, 60, 60, 60], True)
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
                draw.rect_r(box, [200, 168, 100, 255], True)
                draw_text((x + 14, y + (ix * 14)), "/", [200, 200, 200, 200], 12)
            else:
                draw_text((x + 14, y + (ix * 14)), extension[:7].upper(), [200, 200, 200, 200], 12)
                draw.rect_r(box, box_colour, True)

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
            draw.rect((x, y - 20), (50, 20), [40, 40, 40, 60], True)
            if self.click:
                self.current_path = os.path.dirname(self.current_path)
        draw.rect((x, y - 20), (50, 20), colours.grey(50))

        # Path display
        draw_text((x + 60, y - 18), self.current_path, [200, 200, 200, 200], 12)

        # windows drive picker
        if system == 'windows':
            drive_index = 0
            for drive in self.drives:
                box = (x + 100 + (20 * drive_index), y + 195, 19, 20)
                fields.add(box)
                if coll_point(mouse_position, box):
                    draw.rect_r(box, [60, 60, 60, 60], True)
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
        y2 = y


        if key_shift_down:
            y += 100
            draw_text((x + 300, y - 10), "Modify (use with caution)", [200, 200, 200, 200], 12)

            box = (x + 300, y + 7, 200, 20)
            if coll_point(mouse_position, box):
                draw.rect_r(box, [40, 40, 40, 60], True)
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

            draw.rect_r(box, colours.grey(50))
            fields.add(box)
            draw_text((box[0] + 100, box[1] + 2, 2), "Move single folder in folders up", [200, 200, 200, 200], 12)
        y = y2
        y += 0

        draw_text((x + 300, y - 10), "Import", [200, 200, 200, 200], 12)

        box = (x + 300, y + 7, 200, 20)
        if coll_point(mouse_position, box):
            draw.rect_r(box, [40, 40, 40, 60], True)
            if self.click:
                load_to.append(copy.deepcopy(pctl.playlist_active))
                dropped_file.append(copy.deepcopy(self.current_path))

        draw.rect_r(box, colours.grey(50))
        fields.add(box)
        draw_text((box[0] + 100, box[1] + 2, 2), "This folder to current playlist", [200, 200, 200, 200], 12)

        y += 25

        box = (x + 300, y + 7, 200, 20)
        if coll_point(mouse_position, box):
            draw.rect_r(box, [40, 40, 40, 60], True)
            if self.click:
                pctl.multi_playlist.append([os.path.basename(self.current_path), 0, [], 0, 0, 0])
                load_to.append(len(pctl.multi_playlist) - 1)
                dropped_file.append(copy.deepcopy(self.current_path))

        draw.rect_r(box, colours.grey(50))
        fields.add(box)
        draw_text((box[0] + 100, box[1] + 2, 2), "This folder to new playlist", [200, 200, 200, 200], 12)

        y += 25

        box = (x + 300, y + 7, 200, 20)
        if coll_point(mouse_position, box):
            draw.rect_r(box, [40, 40, 40, 60], True)
            if self.click:

                in_current = os.listdir(self.current_path)
                for item in in_current:

                    full_path = os.path.join(self.current_path, item)
                    if os.path.isdir(full_path):
                        pctl.multi_playlist.append([item, 0, [], 0, 0, 0])
                        load_to.append(len(pctl.multi_playlist) - 1)
                        dropped_file.append(full_path)

        draw.rect_r(box, colours.grey(50))
        fields.add(box)
        draw_text((box[0] + 100, box[1] + 2, 2), "Each subfolder as new playlist", [200, 200, 200, 200], 12)


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
                self.id.append(1) # += "1"
            else:
                self.id.append(0) # += "0"

        if self.last_id == self.id:
            return False

        else:
            return True

    def clear(self):

        self.field_array = []


fields = Fields()

pref_box = Over()

# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------


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
        global ttext
        global gui

        w = 0

        # Draw the background
        SDL_SetRenderTarget(renderer, ttext)
        rect = (0, panelY, playlist_width + 31, window_size[1])
        if side_panel_enable is False:
            rect = (0, panelY, window_size[0], window_size[1])
        draw.rect_r(rect, colours.playlist_panel_background, True)

        # Determine highlight size
        if not custom_line_mode:
            highlight_left = playlist_left
            highlight_right = playlist_width
        else:
            highlight_left = playlist_left - 20 + highlight_x_offset + highlight_left_custom
            highlight_right = playlist_width + 30 - highlight_right_custom - highlight_x_offset

        # Show notice if playlist empty
        if len(default_playlist) == 0:

            draw_text((int(playlist_width / 2) + 10, int((window_size[1] - panelY - panelBY) * 0.65), 2),
                      "Playlist is empty", colours.playlist_text_missing, 13)
            draw_text((int(playlist_width / 2) + 10, int((window_size[1] - panelY - panelBY) * 0.65 + 30), 2),
                      "Drag and drop files to import", colours.playlist_text_missing, 13)

        # Show notice if at end of playlist
        elif playlist_position > len(default_playlist) - 1:

            draw_text((int(playlist_width / 2) + 10, int(window_size[1] * 0.15), 2), "End of Playlist",
                      colours.playlist_text_missing, 13)

        # For every track in view
        for i in range(playlist_view_length + 1):

            p_track = i + playlist_position


            move_on_title = False

            if playlist_position < 0:
                playlist_position = 0
            if len(default_playlist) <= p_track:
                break

            n_track = pctl.master_library[default_playlist[p_track]]

            # Fade other tracks in album mode
            album_fade = 255
            if album_mode and pctl.playing_state != 0 and dim_art and \
                            n_track.parent_folder_name \
                            != pctl.master_library[pctl.track_queue[pctl.queue_step]].parent_folder_name:
                album_fade = 150

            # Folder Break Row
            if (p_track == 0 or n_track.parent_folder_name
                    != pctl.master_library[default_playlist[p_track - 1]].parent_folder_name) and \
                            pctl.multi_playlist[pctl.playlist_active][4] == 0 and break_enable:

                line = n_track.parent_folder_name

                if len(line) < 6 and "CD" in line:
                    line = n_track.album

                if append_date and n_track.date != "" and "20" not in line and "19" not in line and "18" not in line and "17" not in line:
                    line += " (" + n_track.date + ")"

                if thick_lines:
                    draw_text2((playlist_width + playlist_left,
                                playlist_row_height - 18 + playlist_top + playlist_row_height * w, 1), line,
                               alpha_mod(colours.folder_title, album_fade),
                               13, playlist_width)
                else:
                    draw_text2((playlist_width + playlist_left,
                                playlist_row_height - 16 + playlist_top + playlist_row_height * w, 1), line,
                               alpha_mod(colours.folder_title, album_fade),
                               11, playlist_width)

                draw.line(playlist_left, playlist_top + playlist_row_height - 1 + playlist_row_height * w,
                          playlist_width + playlist_left,
                          playlist_top + playlist_row_height - 1 + playlist_row_height * w, colours.folder_line)

                if playlist_hold is True and coll_point(mouse_position, (
                        playlist_left, playlist_top + 31 + playlist_row_height * w, playlist_width,
                        playlist_row_height)):

                    if mouse_up and key_shift_down:
                        move_on_title = True

                # Shade ever other line for folder row
                # if row_alt and w % 2 == 0:
                #     draw.rect((playlist_left, playlist_top + playlist_row_height * w),
                #               (playlist_width, playlist_row_height - 1), [0, 0, 0, 20], True)
                w += 1

            # Shade ever other line if option set
            # if row_alt and w % 2 == 0:
            #     draw.rect((playlist_left, playlist_top + playlist_row_height * w),
            #               (playlist_width, playlist_row_height - 1), [0, 0, 0, 20], True)

            # Test if line hit
            if (mouse_click or right_click or middle_click) and coll_point(mouse_position, (
                        playlist_left + 10, playlist_top + playlist_row_height * w, playlist_width - 10,
                        playlist_row_height - 1)) and mouse_position[1] < window_size[1] - panelBY:
                line_hit = True
            else:
                line_hit = False
            if scroll_enable and mouse_position[0] < 30:
                line_hit = False

            # Double click to play
            if key_shift_down is False and d_mouse_click and line_hit and p_track == playlist_selected:

                click_time -= 1.5
                pctl.jump(default_playlist[p_track], p_track)

                if album_mode:
                    goto_album(pctl.playlist_playing)

            # Check if index playing and highlight if true
            this_line_playing = False
            if len(pctl.track_queue) > 1 and pctl.track_queue[pctl.queue_step] == \
                    default_playlist[p_track]:
                draw.rect((highlight_left, playlist_top + playlist_row_height * w),
                          (highlight_right, playlist_row_height - 1), colours.row_playing_highlight, True)
                this_line_playing = True

            # Highlight blue if track is being broadcast
            if default_playlist[
                        p_track] == pctl.broadcast_index and pctl.broadcast_active and not pctl.join_broadcast:
                draw.rect((playlist_left, playlist_top + playlist_row_height * w),
                          (playlist_width, playlist_row_height - 1), [10, 20, 180, 70], True)

            # Add to queue on middle click
            if middle_click and line_hit:
                pctl.force_queue.append([default_playlist[p_track],
                                         p_track, pctl.playlist_active])

            # Highlight green if track in queue
            for item in pctl.force_queue:
                if default_playlist[p_track] == item[0] and item[1] == p_track:
                    draw.rect((playlist_left, playlist_top + playlist_row_height * w),
                              (playlist_width, playlist_row_height - 1), [30, 170, 30, 35],
                              True)

            # Make track the selection if right clicked
            if right_click and line_hit and not playlist_panel:
                if p_track not in shift_selection:
                    shift_selection = [p_track]

            if mouse_click and key_shift_down is False and line_hit:
                # shift_selection = []
                shift_selection = [p_track]
            if mouse_click and line_hit:
                quick_drag = True

            if (mouse_click and key_shift_down is False and line_hit or
                            playlist_selected == p_track):
                draw.rect((highlight_left, playlist_top + playlist_row_height * w),
                          (highlight_right, playlist_row_height - 1), colours.row_select_highlight, True)
                playlist_selected = p_track

            # Shift Move Selection
            if move_on_title or mouse_up and playlist_hold is True and coll_point(mouse_position, (
                    playlist_left, playlist_top + playlist_row_height * w, playlist_width, playlist_row_height)):

                if p_track != playlist_hold_position and p_track not in shift_selection:
                    if len(shift_selection) == 0:
                        temp_index = default_playlist[playlist_hold_position]

                        del default_playlist[playlist_hold_position]

                        if move_on_title:
                            if p_track < playlist_hold_position:
                                default_playlist.insert(p_track, temp_index)
                            else:
                                default_playlist.insert(p_track - 1, temp_index)

                        else:
                            if p_track < playlist_hold_position:
                                default_playlist.insert(p_track + 1, temp_index)
                            else:
                                default_playlist.insert(p_track, temp_index)

                        gui.pl_update += 1
                        playlist_selected = p_track

                    else:
                        count = 0
                        temp_ref = []
                        if move_on_title:
                            count -= 1
                        for a in range(0, p_track):
                            print(a)
                            if a not in shift_selection:
                                count += 1
                        for b in reversed(range(len(default_playlist))):
                            if b in shift_selection:
                                temp_ref.append(default_playlist[b])
                                del default_playlist[b]

                        for item in temp_ref:
                            default_playlist.insert(count + 1, item)
                        shift_selection = []

            if mouse_down and playlist_hold and coll_point(mouse_position, (
                    playlist_left, playlist_top + playlist_row_height * w, playlist_width,
                    playlist_row_height)) and playlist_hold_position != p_track:
                draw.line(playlist_left, playlist_top + playlist_row_height + playlist_row_height * w,
                          playlist_width + playlist_left,
                          playlist_top + playlist_row_height + playlist_row_height * w, [35, 45, 90, 255])

            # Shift click actions
            if mouse_click and line_hit and key_shift_down:

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
                draw.rect((highlight_left, playlist_top + playlist_row_height * w),
                          (highlight_right, playlist_row_height), colours.row_select_highlight, True)

            if right_click and line_hit and mouse_position[0] > playlist_left + 10 \
                    and not playlist_panel:

                track_menu.activate(default_playlist[p_track])

                playlist_selected = p_track

            # time.sleep(0.1)
            if custom_line_mode:

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

                offs = 0

                for item in cust:

                    if item[0] == 't':

                        line = get_display_time(n_track.length)
                        draw_text((item[1], playlist_text_offset + playlist_top + playlist_row_height * w,
                                   item[2]), line, alpha_mod(timec, album_fade), row_font_size)

                    elif item[0] == 'i':
                        line = str(n_track.track_number)
                        line = line.split("/", 1)[0]
                        if dd_index and len(line) == 1:
                            line = "0" + line
                        line += item[3]

                        draw_text((item[1], playlist_text_offset + playlist_top + playlist_row_height * w,
                                   item[2]), line, alpha_mod(indexc, album_fade), row_font_size)

                    elif item[0] == 'o':
                        key = n_track.title + \
                              n_track.filename
                        total = 0
                        ratio = 0
                        if (key in pctl.star_library) and pctl.star_library[key] != 0 and \
                                        n_track.length \
                                        != 0:
                            total = pctl.star_library[key]
                            ratio = total / n_track.length

                        line = str(int(ratio))
                        # if True:
                        #     if dd_index and len(line) == 1:
                        #         line = "0" + line

                        draw_text((item[1], playlist_text_offset + playlist_top + playlist_row_height * w,
                                   item[2]), line, alpha_mod(indexc, album_fade), row_font_size)

                    elif item[0] == 'c':
                        line = item[3]
                        draw_text((item[1], playlist_text_offset + playlist_top + playlist_row_height * w,
                                   item[2]), line, alpha_mod(titlec, album_fade), row_font_size)

                    elif item[0] == 'a':
                        line = n_track.artist

                        offs += draw_text2((item[1],
                                            playlist_text_offset + playlist_top + playlist_row_height * w,
                                            item[2]),
                                           line,
                                           alpha_mod(artistc, album_fade),
                                           row_font_size,
                                           item[3],
                                           1,
                                           default_playlist[p_track])

                    elif item[0] == 'n':
                        line = n_track.title

                        offs += draw_text2((item[1],
                                            playlist_text_offset + playlist_top + playlist_row_height * w,
                                            item[2]),
                                           line,
                                           alpha_mod(titlec, album_fade),
                                           row_font_size,
                                           item[3],
                                           2,
                                           default_playlist[p_track])

                    elif item[0] == 'b':
                        line = n_track.album

                        offs = draw_text2((item[1],
                                           playlist_text_offset + playlist_top + playlist_row_height * w,
                                           item[2]),
                                          line,
                                          alpha_mod(albumc, album_fade),
                                          row_font_size,
                                          item[3],
                                          3,
                                          default_playlist[p_track])

                    elif item[0] == 'd':
                        line = str(n_track.date)

                        offs = draw_text2((item[1],
                                           playlist_text_offset + playlist_top + playlist_row_height * w,
                                           item[2]),
                                          line,
                                          alpha_mod(albumc, album_fade),
                                          row_font_size,
                                          item[3],
                                          3,
                                          default_playlist[p_track])

                    elif item[0] == 's':

                        index = default_playlist[p_track]
                        key = pctl.master_library[index].title + pctl.master_library[index].filename
                        if star_lines and (key in pctl.star_library) and pctl.star_library[key] != 0 and \
                                        pctl.master_library[index].length != 0:
                            total = pctl.star_library[key]
                            ratio = total / pctl.master_library[index].length
                            if ratio > 15:
                                ratio = 15
                            if ratio > 0.55:
                                ratio = int(ratio * 4)

                                draw.line(item[1] - ratio,
                                          playlist_text_offset + playlist_top + 8 + playlist_row_height * w,
                                          item[1],
                                          playlist_text_offset + playlist_top + 8 + playlist_row_height * w,
                                          alpha_mod(colours.star_line, album_fade))

            if not custom_line_mode:

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
                if n_track.artist != "" or \
                                n_track.title != "":
                    line = str(n_track.track_number)
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

                    indexoffset += playlist_x_offset

                    if n_track.artist != "":
                        if split_line and colours.artist_text != colours.title_text:
                            line0 = n_track.artist

                            artistoffset = draw_text2((playlist_left + indexoffset,
                                                       playlist_text_offset + playlist_top + playlist_row_height * w),
                                                      line0,
                                                      alpha_mod(artistc, album_fade),
                                                      row_font_size,
                                                      int(playlist_width / 2),
                                                      1,
                                                      default_playlist[p_track])

                            line = n_track.title
                        else:
                            line += n_track.artist + " - " + \
                                    n_track.title
                    else:
                        line += n_track.title

                else:
                    line = \
                        os.path.splitext((n_track.filename))[
                            0]

                ratio = 0
                index = default_playlist[p_track]
                key = pctl.master_library[index].title + pctl.master_library[index].filename

                if star_lines and (key in pctl.star_library) and pctl.star_library[key] != 0 and pctl.master_library[
                        index].length != 0:
                    total = pctl.star_library[key]
                    ratio = total / pctl.master_library[index].length
                    if ratio > 0.55:
                        star_x = int(ratio * 4)
                        if star_x > 60:
                            star_x = 60
                        draw.line(playlist_width - playlist_x_offset + playlist_left - star_x - 40,
                                  playlist_text_offset + playlist_top + 8 + playlist_row_height * w,
                                  playlist_width - playlist_x_offset + playlist_left - 37,
                                  playlist_text_offset + playlist_top + 8 + playlist_row_height * w,
                                  alpha_mod(colours.star_line, album_fade))

                draw_text((playlist_left + playlist_x_offset,
                           playlist_text_offset + playlist_top + playlist_row_height * w), indexLine,
                          alpha_mod(indexc, album_fade), row_font_size)

                if artistoffset != 0:
                    artistoffset += 7

                draw_text2((playlist_left + indexoffset + artistoffset,
                            playlist_text_offset + playlist_top + playlist_row_height * w),
                           line,
                           alpha_mod(titlec, album_fade),
                           row_font_size,
                           playlist_width - 71 - artistoffset - ratio - 15,
                           2,
                           default_playlist[p_track])

                line = get_display_time(n_track.length)

                draw_text((playlist_width + playlist_left - playlist_x_offset,
                           playlist_text_offset + playlist_top + playlist_row_height * w, 1), line,
                          alpha_mod(timec, album_fade), row_font_size)

            w += 1
            if w > playlist_view_length:
                break

        if (right_click and playlist_top + 40 + playlist_row_height * w < mouse_position[1] < window_size[
            1] - 55 and
                    mouse_position[0] > playlist_left + 15):
            playlist_menu.activate()

        if mouse_wheel != 0 and window_size[1] - 50 > mouse_position[1] > 25 + playlist_top\
                and not (playlist_panel and coll_point(mouse_position, pl_rect)):

            if album_mode and mouse_position[0] > playlist_width + 40:
                pass
            else:
                mx = 4
                if playlist_view_length < 25:
                    mx = 3
                if thick_lines:
                    mx = 3
                playlist_position -= mouse_wheel * mx
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

    def cache_render(self):

        SDL_RenderCopy(renderer, ttext, None, abc)


playlist_render = StandardPlaylist()


# --------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------

# MAIN LOOP---------------------------------------------------------------------------

playlist_view_length = int(((window_size[1] - playlist_top) / 16) - 1)

running = True

boarder = 1

update_layout = True

event = SDL_Event()

print("Initialization Complete")

mouse_moved = False

power = 0
key_F7 = False

r_arg_queue = copy.deepcopy(sys.argv)
arg_queue = []
for item in r_arg_queue:
    if (os.path.isdir(item) or os.path.isfile(item)) and '.py' not in item and 'tmb.exe' not in item:
        arg_queue.append(item)

while running:

    # bm.get('main')

    if k_input:

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

    if not mouse_down:
        k_input = False
    clicked = False
    focused = False
    mouse_moved = False

    while SDL_PollEvent(ctypes.byref(event)) != 0:

        # print(event.type)

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
                    text_space = draw.text_calc(pctl.multi_playlist[w][0], 12)
                    x = starting_l + (spacing * w) + k
                    if x < i_x < x + text_space + 16:
                        load_to.append(copy.deepcopy(w))
                        print("Direct drop")
                        break
                    k += text_space
                else:
                    load_to.append(copy.deepcopy(pctl.playlist_active))
            else:
                load_to.append(copy.deepcopy(pctl.playlist_active))

            dropped_file_sdl = event.drop.file
            # print(dropped_file_sdl)
            # dropped_file.append(str(dropped_file_sdl.decode("utf-8")))
            dropped_file.append(str(urllib.parse.unquote(dropped_file_sdl.decode("utf-8"))))
            # print(urllib.parse.unquote(dropped_file_sdl.decode("utf-8")))

            # SDL_free(dropped_file_sdl)

            # print('dropped: ' + str(dropped_file))
            gui.update += 1

            mouse_down = False
            drag_mode = False
        elif event.type == 8192:
            gui.pl_update += 2
            gui.update += 2

        elif event.type == SDL_QUIT:
            power += 5
            running = False
            break
        elif event.type == SDL_TEXTEDITING:
            power += 5
            editline = event.edit.text
            editline = editline.decode("utf-8", 'ignore')
            k_input = True

        elif event.type == SDL_MOUSEMOTION:

            mouse_position[0] = event.motion.x
            mouse_position[1] = event.motion.y
            mouse_moved = True
        elif event.type == SDL_MOUSEBUTTONDOWN:
            k_input = True
            power += 5
            gui.update += 1
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
            # print(input_text)
        elif event.type == SDL_MOUSEWHEEL:
            k_input = True
            power += 5
            mouse_wheel += event.wheel.y
            gui.update += 1
        elif event.type == SDL_WINDOWEVENT:

            power += 5

            if event.window.event == SDL_WINDOWEVENT_FOCUS_GAINED:

                focused = True
                mouse_down = False
                gui.pl_update += 1
                gui.update += 1

                # Workaround for SDL bug 2610
                if SDL_GetWindowFlags(t_window) & SDL_WINDOW_MAXIMIZED:
                    SDL_RestoreWindow(t_window)
                    SDL_MaximizeWindow(t_window)
                elif SDL_GetWindowFlags(t_window) & SDL_WINDOW_FULLSCREEN_DESKTOP:

                    SDL_RestoreWindow(t_window)
                    SDL_SetWindowFullscreen(t_window, SDL_WINDOW_FULLSCREEN_DESKTOP)

            elif event.window.event == SDL_WINDOWEVENT_FOCUS_LOST:
                x_menu.active = False
                tab_menu.active = False
                track_menu.active = False
                playlist_menu.active = False
                playlist_panel = False
                gui.update += 1

            elif event.window.event == SDL_WINDOWEVENT_RESIZED:
                gui.update += 1
                window_size[0] = event.window.data1
                window_size[1] = event.window.data2
                update_layout = True

            elif event.window.event == SDL_WINDOWEVENT_MINIMIZED:
                gui.lowered = True
            elif event.window.event == SDL_WINDOWEVENT_RESTORED:
                gui.lowered = False

                gui.pl_update += 1
                gui.update += 1

                if update_title:
                    update_title_do()

            elif event.window.event == SDL_WINDOWEVENT_SHOWN:

                focused = True
                gui.pl_update += 1
                gui.update += 1

    if mouse_moved:
        if fields.test():
            gui.update += 1

    power += 1
    if resize_mode or scroll_hold:
        power += 3
    if side_drag:
        power += 2
    if gui.level_update:
        power = 6

    if power < 5:
        time.sleep(0.002)
        continue
    else:
        power = 0

    if gui.pl_update > 2:
        gui.pl_update = 2




    if check_file_timer.get() > 0.5:
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

        if len(arg_queue) > 0:
            i = 0
            while i < len(arg_queue):

                for w in range(len(pctl.multi_playlist)):
                    if pctl.multi_playlist[w][0] == "Default":
                        #del pctl.multi_playlist[w][2][:]
                        load_to.append(copy.deepcopy(w))
                        break
                else:
                    pctl.multi_playlist.append(["Default", 0, [], 0, 0, 0])
                    load_to.append(len(pctl.multi_playlist) - 1)
                    switch_playlist(len(pctl.multi_playlist) - 1)

                dropped_file.append(arg_queue[i])
                i += 1
            arg_queue = []
            auto_play_import = True
    if k_input:

        if mouse_click:
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
            if boarder == 0:
                boarder = 1
                SDL_SetWindowBordered(t_window, SDL_TRUE)

            elif boarder == 1:
                boarder = 0
                SDL_SetWindowBordered(t_window, SDL_FALSE)

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
            pctl.join_broadcast ^= True
            print("Join brodcast commands:" + str(pctl.join_broadcast))

        if key_F4:
            standard_size()

        if key_F7:
            # spec_smoothing ^= True
            # if draw_border:
            #     SDL_SetWindowBordered(t_window, True)
            #     draw_border = False
            # else:
            #     SDL_SetWindowBordered(t_window, False)
            #     draw_border = True

            # print(lastfm.get_bio(pctl.master_library[pctl.track_queue[pctl.queue_step]].artist))
            # show_playlist ^= True

            # b_info_bar ^= True
            # playlist_panel ^= True

            # key_F7 = False
            pass

        if key_F3:
            split_line ^= True
            gui.pl_update += 1
            gui.update += 1

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
        if (genre_box or playlist_panel) and mouse_click:
            mouse_click = False
            genre_box_click = True

        if radiobox and key_return_press:
            key_return_press = False
            key_return_press_w = True

        if mouse_wheel != 0:
            gui.update += 1
        if mouse_down is True:
            gui.update += 1

        if key_PGD:
            if len(default_playlist) > 10:
                playlist_position += playlist_view_length - 4
                if playlist_position > len(default_playlist):
                    playlist_position = len(default_playlist) - 2
                gui.pl_update += 1
        if key_PGU:
            if len(default_playlist) > 0:
                playlist_position -= playlist_view_length - 4
                if playlist_position < 0:
                    playlist_position = 0
                gui.pl_update += 1

        if mouse_click:
            n_click_time = time.time()
            if n_click_time - click_time < 0.7:
                d_mouse_click = True
            click_time = n_click_time

        if quick_search_mode is False and renamebox is False:

            if key_shiftr_down and key_right_press:
                key_right_press = False
                pctl.advance()
                # print('hit')
            if key_shiftr_down and key_left_press:
                key_left_press = False
                pctl.back()

            if key_shiftr_down and key_up_press:
                key_up_press = False
                pctl.player_volume += 3
                if pctl.player_volume > 100:
                    pctl.player_volume = 100
                pctl.set_volume()

            if key_shiftr_down and key_down_press:
                key_down_press = False
                if pctl.player_volume > 3:
                    pctl.player_volume -= 3
                else:
                    pctl.player_volume = 0
                pctl.set_volume()

            if key_slash_press:
                pctl.advance(rr=True)
            if key_period_press:
                pctl.random_mode ^= True
            if key_quote_hit:
                pctl.show_current()
            if key_comma_press:
                pctl.repeat_mode ^= True

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

    if focused is True:
        mouse_down = False



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


    if len(dropped_file) > 0:
        if loading_in_progress == False and len(items_loaded) == 0:
            loading_in_progress = True

            paths_to_load = dropped_file[0].replace('\\', '/')
            if os.path.isdir(paths_to_load):
                loaderCommand = LC_Folder
            else:
                loaderCommand = LC_File
            loaderCommandReady = True
            # print(dropped_file)
            del dropped_file[0]

    if loaderCommand == LC_Done:
        loaderCommand = LC_None
        gui.update += 1
        gui.pl_update += 2
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

        time_display_position[0] = window_size[0] - time_display_position_right

        highlight_x_offset = 0
        if scroll_enable and custom_line_mode:
            highlight_x_offset = 16


        random_button_position = window_size[0] - 90, 83


        if bb_type == 1:
            panelBY = 95
            seek_bar_position[0] = 0
            seek_bar_size[0] = window_size[0]
            seek_bar_size[1] = 11


        if thick_lines:
            playlist_row_height = 31
            playlist_text_offset = 6
            playlist_x_offset = 7
            row_font_size = 13
        else:
            playlist_row_height = 16
            playlist_text_offset = 0
            playlist_x_offset = 0
            row_font_size = 12

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

            gui.pl_update += 2

            playlist_view_length = int(((window_size[1] - playlist_top) / playlist_row_height) - 0) - 3

        if GUI_Mode == 1:
            SDL_DestroyTexture(ttext)
            gui.pl_update += 2



        ttext = SDL_CreateTexture(renderer, SDL_PIXELFORMAT_UNKNOWN, SDL_TEXTUREACCESS_TARGET, window_size[0], window_size[1])
        SDL_SetTextureBlendMode(ttext, SDL_BLENDMODE_BLEND)


        update_layout = False

    # -----------------------------------------------------
    # THEME SWITCHER--------------------------------------------------------------------
    if key_F2:
        themeChange = True
        theme += 1

    if themeChange is True:
        gui.pl_update += 2
        if theme > 25:
            theme = 0
        if theme > 0:
            theme_number = theme - 1
            try:
                theme_files = os.listdir(install_directory + '/theme')

                for i in range(len(theme_files)):
                    # print(theme_files[i])
                    if i == theme_number and 'ttheme' in theme_files[i]:
                        colours.__init__()
                        with open(install_directory + "/theme/" + theme_files[i], encoding="utf_8") as f:
                            content = f.readlines()
                            for p in content:
                                if "#" in p:
                                    continue
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
                                if 'bottom panel' in p:
                                    colours.bottom_panel_colour = get_colour_from_line(p)


                                    SDL_SetTextureColorMod(c1, colours.bottom_panel_colour[0], colours.bottom_panel_colour[1],
                                                           colours.bottom_panel_colour[2])
                                    SDL_SetTextureColorMod(c2, colours.bottom_panel_colour[0], colours.bottom_panel_colour[1],
                                                           colours.bottom_panel_colour[2])
                                    SDL_SetTextureColorMod(c3, colours.bottom_panel_colour[0], colours.bottom_panel_colour[1],
                                                           colours.bottom_panel_colour[2])
                        break
                else:
                    theme = 0
            except:
                message_box = True
                message_box_text = "Error loading theme file"

        if theme == 0:
            colours.__init__()

            SDL_SetTextureColorMod(c1, colours.bottom_panel_colour[0], colours.bottom_panel_colour[1], colours.bottom_panel_colour[2])
            SDL_SetTextureColorMod(c2, colours.bottom_panel_colour[0], colours.bottom_panel_colour[1], colours.bottom_panel_colour[2])
            SDL_SetTextureColorMod(c3, colours.bottom_panel_colour[0], colours.bottom_panel_colour[1], colours.bottom_panel_colour[2])


        themeChange = False

    # ---------------------------------------------------------------------------------------------------------
    # GUI DRAWING------
    # print(gui.update)

    if gui.update > 0 and gui.lowered != True and not resize_mode:
        if gui.update > 2:
            gui.update = 2

        SDL_SetRenderDrawColor(renderer, colours.top_panel_background[0], colours.top_panel_background[1], colours.top_panel_background[2], colours.top_panel_background[3])
        SDL_RenderClear(renderer)

        fields.clear()

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
            # Gallery view

            if album_mode:

                rect = [playlist_width + 31, panelY, window_size[0] - playlist_width - 31,
                        window_size[1] - panelY - panelBY - 0]
                draw.rect_r(rect, colours.side_panel_background, True)

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

                            albumtitle = colours.side_bar_line1 #grey(220)

                            if info[0] == 1 and pctl.playing_state != 0:
                                draw.rect((x - 12, y - 10), (album_mode_art_size + 24, album_mode_art_size + 60),
                                          [200, 200, 200, 15], True)

                            draw.rect((x, y), (album_mode_art_size, album_mode_art_size), [40, 40, 40, 50], True)

                            gall_ren.render(default_playlist[album_dex[album_on]], (x, y))

                            if info[0] != 1 and pctl.playing_state != 0 and dim_art:
                                draw.rect((x, y), (album_mode_art_size, album_mode_art_size), [0, 0, 0, 110], True)
                                albumtitle = colours.grey(150)

                            if mouse_click and not focused and coll_point(mouse_position, (
                            x, y, album_mode_art_size, album_mode_art_size + 40)) and panelY < mouse_position[1] < \
                                            window_size[1] - panelBY and \
                                    mouse_position[1] < b_info_y:

                                if info[0] == 1 and pctl.playing_state == 2:
                                    pctl.play()
                                elif info[0] == 1 and pctl.playing_state > 0:
                                    playlist_position = album_dex[album_on]
                                else:
                                    playlist_position = album_dex[album_on]
                                    pctl.jump(default_playlist[album_dex[album_on]], album_dex[album_on])

                                pctl.show_current()

                            c_index = default_playlist[album_dex[album_on]]
                            if c_index in album_artist_dict:
                                pass
                            else:
                                i = album_dex[album_on]
                                while i < len(default_playlist) - 1:
                                    if pctl.master_library[default_playlist[i]].parent_folder_name != pctl.master_library[default_playlist[album_dex[album_on]]].parent_folder_name:
                                        album_artist_dict[c_index] = pctl.master_library[default_playlist[album_dex[album_on]]].artist
                                        break
                                    if pctl.master_library[default_playlist[i]].artist != pctl.master_library[default_playlist[album_dex[album_on]]].artist:
                                        album_artist_dict[c_index] = "Various Artists"
                                        break
                                    i += 1
                                else:
                                    album_artist_dict[c_index] = pctl.master_library[default_playlist[album_dex[album_on]]].artist

                            line = album_artist_dict[c_index]

                            draw_text2((x, y + album_mode_art_size + 8),
                                       line,
                                       albumtitle,
                                       11,
                                       album_mode_art_size,
                                       3,
                                       default_playlist[album_dex[album_on]]
                                       )

                            line = pctl.master_library[default_playlist[album_dex[album_on]]].album
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

                draw.rect((0, 0), (window_size[0], panelY), colours.top_panel_background, True)

                if b_info_bar and window_size[1] > 700:
                    x = playlist_width + 31
                    w = window_size[0] - x
                    b_info_y = int(window_size[1] * 0.7)
                    b_info_y = window_size[1] - 250
                    y = b_info_y
                    h = window_size[1] - y - 51


                    if h < 5:
                        h = 5

                    draw.rect_r((x, y, w, h), colours.top_panel_background, True)
                    draw.rect_r((x, y, w, h), [255, 255, 255, 3], True)
                    draw.line(x, y, x + w, y, colours.grey(50))

                    box = h - 4 #- 10

                    album_art_gen.display(pctl.track_queue[pctl.queue_step],
                                          (window_size[0] - 0 - box, y + 2), (box, box))

                    draw_text((x + 11, y + 6), pctl.master_library[pctl.track_queue[pctl.queue_step]].artist, colours.grey(200), 16)

                    line =  pctl.master_library[pctl.track_queue[pctl.queue_step]].album
                    if pctl.master_library[pctl.track_queue[pctl.queue_step]].date != "":
                        line += " (" + pctl.master_library[pctl.track_queue[pctl.queue_step]].date + ")"

                    draw_text((x + 11, y + 29), line, colours.grey(200), 14)



                    # if pctl.track_queue[pctl.queue_step] not in album_dex_l:
                    #     album_dex_l = get_folder_list(pctl.track_queue[pctl.queue_step])
                    #
                    # pl_x = x + 50
                    # pl_y = y + 60
                    # row = 0
                    #
                    # for i in range(len(album_dex_l)):
                    #     draw_text((pl_x, pl_y), pctl.master_library[album_dex_l[i]].title, colours.grey(200), 14)
                    #     pl_y += 18
                    #
                    #     row += 1
                    #     if row > 5:
                    #         row = 0
                    #         pl_x += 400
                    #         pl_y = y + 60

                else:
                    b_info_y = window_size[1]

            # End of gallery view ^
            # --------------------------------------------------------------------------
            # Main Playlist:


            if len(items_loaded) > 0:
                pctl.multi_playlist[load_to[0]][2] += items_loaded
                del load_to[0]
                items_loaded = []
                gui.update += 1

            if show_playlist:

                # playlist hit test
                if coll_point(mouse_position, (playlist_left, playlist_top, playlist_width, window_size[1] - panelY - panelBY)) and not drag_mode and (
                                            mouse_click or mouse_wheel != 0 or right_click or middle_click or mouse_up or mouse_down):
                    gui.pl_update += 2

                # MAIN PLAYLIST

                if gui.pl_update > 0:

                    gui.pl_update -= 1

                    playlist_render.full_render()

                else:

                    playlist_render.cache_render()

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
                    if coll_point(mouse_position, (0, panelY, 28, ey - panelY)) and not playlist_panel and (mouse_down or right_click)\
                            and coll_point(click_location, (0, panelY, 28, ey - panelY)):

                        gui.pl_update += 1
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
                        gui.pl_update += 1
                        p_y = pointer(c_int(0))
                        p_x = pointer(c_int(0))
                        SDL_GetGlobalMouseState(p_x, p_y)
                        sbp = p_y.contents.value - (scroll_point - scroll_bpoint)
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

                    draw.rect((1, sbp), (14, sbl), colours.scroll_colour, True)

                    if (coll_point(mouse_position, (2, sbp, 20, sbl)) and mouse_position[0] != 0) or scroll_hold:
                        draw.rect((1, sbp), (14, sbl), [255, 255, 255, 11], True)

                # Switch Vis:

                if mouse_click and coll_point(mouse_position, (window_size[0] - 130 - offset_extra, 0, 130, panelY)):
                    if gui.vis == 0:
                        gui.vis = 1
                        gui.turbo = True
                    elif gui.vis == 1:
                        gui.vis = 2
                    elif gui.vis == 2:
                        gui.vis = 0
                        gui.turbo = False
                # --------------------------------------------
                # ALBUM ART

                if side_panel_enable:
                    if album_mode:
                        pass
                    else:

                        rect = [playlist_width + 31, panelY, window_size[0] - playlist_width - 30,
                                window_size[1] - panelY - panelBY]
                        draw.rect_r(rect, colours.side_panel_background, True)

                        showc = False

                        boxx = window_size[0] - playlist_width - 32 - 18
                        boxy = window_size[1] - 160
                        box = boxx

                        # CURRENT

                        if mouse_click and (coll_point(mouse_position, (
                            playlist_width + 40, panelY + boxx + 5, boxx, window_size[1] - boxx - 90))):

                            pctl.show_current()

                            # if album_mode:
                            #     goto_album(pctl.playlist_playing)
                            gui.update += 1

                        if len(pctl.track_queue) > 0:

                            if coll_point(mouse_position, (playlist_width + 40, 38, box, box)) and mouse_click is True:
                                album_art_gen.cycle_offset(pctl.track_queue[pctl.queue_step])

                            if coll_point(mouse_position, (
                                playlist_width + 40, 38, box, box)) and right_click is True and pctl.playing_state > 0:
                                album_art_gen.open_external(pctl.track_queue[pctl.queue_step])
                        if 3 > pctl.playing_state > 0:

                            if side_drag:

                                album_art_gen.display(pctl.track_queue[pctl.queue_step], (playlist_width + 40, 38),
                                                      (box, box), True)
                            else:
                                album_art_gen.display(pctl.track_queue[pctl.queue_step], (playlist_width + 40, 38), (box, box))


                            showc = album_art_gen.get_info(pctl.track_queue[pctl.queue_step])

                        draw.rect((playlist_width + 40, 38), (box + 1, box + 1), colours.art_box)

                        rect = (playlist_width + 40, 38, box, box)
                        fields.add(rect)

                        if showc is not False and coll_point(mouse_position, rect) \
                                and renamebox is False \
                                and radiobox is False \
                                and encoding_box is False \
                                and pref_box.enabled is False \
                                and rename_playlist_box is False \
                                and new_playlist_box is False \
                                and message_box is False \
                                and track_box is False \
                                and genre_box is False:

                            line = ""
                            if showc[0] is True:
                                line += 'A '
                            else:
                                line += 'E '
                            line += str(showc[2]+1) + "/" + str(showc[1])

                            xoff = 0
                            xoff = draw.text_calc(line, 12) + 12

                            draw.rect((playlist_width + 40 + box - xoff, 36 + box - 19), (xoff, 18),
                                      [0, 0, 0, 190], True)

                            draw_text((playlist_width + 40 + box - 6, 36 + box - 18, 1), line, [220, 220, 220, 220], 12)

                            # if pctl.master_library[pctl.track_queue[pctl.queue_step]].artist != "":
                            #     line = pctl.master_library[pctl.track_queue[pctl.queue_step]].album
                            #     if pctl.master_library[pctl.track_queue[pctl.queue_step]].date != "":
                            #         line += " (" + pctl.master_library[pctl.track_queue[pctl.queue_step]].date + ")"
                            #     xoff = text_calc(line, 13)[0] + 14
                            #     draw.rect((playlist_width + 41, 50), (xoff, 18),
                            #               [0, 0, 0, 200], True)
                            #     draw_text((playlist_width + 40 + 8, 50), line, [230, 230, 230, 230], 13)

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

                                    title = pctl.master_library[pctl.track_queue[pctl.queue_step]].title
                                    album = pctl.master_library[pctl.track_queue[pctl.queue_step]].album
                                    artist = pctl.master_library[pctl.track_queue[pctl.queue_step]].artist
                                    ext = pctl.master_library[pctl.track_queue[pctl.queue_step]].file_ext
                                    date = pctl.master_library[pctl.track_queue[pctl.queue_step]].date
                                    genre = pctl.master_library[pctl.track_queue[pctl.queue_step]].genre
                                    sample = str(pctl.master_library[pctl.track_queue[pctl.queue_step]].samplerate)

                                else:

                                    title = pctl.tag_meta

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
                                                          playing_info, colours.side_bar_line1, 12)

                                            if artist != "":
                                                playing_info = artist
                                                playing_info = trunc_line(playing_info, 11,
                                                                          window_size[0] - playlist_width - 54)
                                                draw_text((playlist_width + 30 + int(side_panel_size / 2), block1 + 17, 2),
                                                          playing_info, colours.side_bar_line2, 11)
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
                                                      colours.side_bar_line1, 11)

                                        if block3 == False:

                                            if album != "":
                                                playing_info = album
                                                playing_info = trunc_line(playing_info, 11,
                                                                          window_size[0] - playlist_width - 53)
                                                draw_text((playlist_width + 30 + int(side_panel_size / 2), block2, 2),
                                                          playing_info, colours.side_bar_line2, 11)

                                            if date != "":
                                                playing_info = date
                                                if genre != "":
                                                    playing_info += " | " + genre
                                                playing_info = trunc_line(playing_info, 11,
                                                                          window_size[0] - playlist_width - 53)
                                                draw_text((playlist_width + 30 + int(side_panel_size / 2), block2 + 18, 2),
                                                          playing_info, colours.side_bar_line2, 11)


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
                                                          line, colours.side_bar_line2, 11)
                                    # Topline
                                    elif pctl.broadcast_active != True:
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

                                        if gui.turbo:
                                            draw_text((window_size[0] - 104 - offset_extra, 8, 1), line, colours.side_bar_line1,
                                                      11)

                                        else:
                                            draw_text((window_size[0] - 15 - offset_extra, 8, 1), line, colours.side_bar_line1,
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
                                                draw_text((playlist_width + 39, block1 + 2), playing_info, colours.side_bar_line1,
                                                          13, max=side_panel_size - 20)

                                            if artist != "":
                                                playing_info = artist
                                                playing_info = trunc_line(playing_info, 11,
                                                                          window_size[0] - playlist_width - 54)
                                                draw_text((playlist_width + 39, block1 + 17 + 4), playing_info, colours.side_bar_line2,
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
                                            draw_text((playlist_width + 39, block1), line, colours.side_bar_line1, 11)

                                        if block3 == False:

                                            if album != "":
                                                playing_info = album
                                                playing_info = trunc_line(playing_info, 11,
                                                                          window_size[0] - playlist_width - 53)
                                                draw_text((playlist_width + 39, block2), playing_info, colours.side_bar_line2,
                                                          11)

                                            if date != "":
                                                playing_info = date
                                                if genre != "":
                                                    playing_info += " | " + genre
                                                playing_info = trunc_line(playing_info, 11,
                                                                          window_size[0] - playlist_width - 53)
                                                draw_text((playlist_width + 39, block2 + 18), playing_info, colours.side_bar_line2,
                                                          11)

                                            if ext != "":
                                                playing_info = ext  # + " | " + sample
                                                playing_info = trunc_line(playing_info, 11,
                                                                          window_size[0] - playlist_width - 53)
                                                draw_text((playlist_width + 39, block2 + 36), playing_info, colours.side_bar_line2,
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
                                                draw_text((playlist_width + 39, block2 + 35), line, colours.side_bar_line2, 11)


                if colours.tb_line != colours.playlist_panel_background and GUI_Mode == 1:
                    draw.line(0, panelY, window_size[0], panelY, colours.tb_line)

                # Seperation Line Drawing
                if side_panel_enable:

                    # Draw Highlight when draging
                    if side_drag is True:
                        draw.line(window_size[0] - side_panel_size + 1, panelY + 1, window_size[0] - side_panel_size + 1,
                                  window_size[1] - 50, colours.grey(50))

                    # Draw Highlight when mouse over
                    if draw_sep_hl:

                        draw.line(window_size[0] - side_panel_size + 1, panelY + 1, window_size[0] - side_panel_size + 1,
                                  window_size[1] - 50, [100, 100, 100, 70])
                        draw_sep_hl = False

                # Normal Drawing
                if side_panel_enable:
                    draw.line(playlist_width + 30, panelY + 1, playlist_width + 30, window_size[1] - 30, colours.sep_line)


                # New Bottom Bar

            # BOTTOM BAR!

            if GUI_Mode == 1:  # not compact_bar:

                draw.rect((0, window_size[1] - panelBY), (window_size[0], panelBY), colours.bottom_panel_colour, True)
                draw.rect(seek_bar_position, seek_bar_size, colours.seek_bar_background, True)

                if bb_type == 0:

                    draw.line(0, window_size[1] - panelBY, 299, window_size[1] - panelBY, colours.bb_line)
                    draw.line(299, window_size[1] - panelBY, 299, window_size[1] - panelBY + seek_bar_size[1], colours.bb_line)
                    draw.line(300, window_size[1] - panelBY + seek_bar_size[1], window_size[0], window_size[1] - panelBY + seek_bar_size[1], colours.bb_line)

                # Scrobble marker

                if scrobble_mark and lastfm.hold is False and lastfm.connected and pctl.playing_length > 0:
                    l_target = 0
                    if pctl.master_library[pctl.track_queue[pctl.queue_step]].length > 240 * 2:
                        l_target = 240
                    else:
                        l_target = int(pctl.master_library[pctl.track_queue[pctl.queue_step]].length * 0.50)
                    l_lead = l_target - pctl.a_time

                    if l_lead > 0 and pctl.master_library[pctl.track_queue[pctl.queue_step]].length > 30:
                        l_x = seek_bar_position[0] + int(
                            pctl.playing_time * seek_bar_size[0] / int(pctl.playing_length))
                        l_x += int(seek_bar_size[0] / int(pctl.playing_length) * l_lead)
                        draw.rect_r((l_x, seek_bar_position[1] + 13, 2, 2), [255, 0, 0, 100], True)
                        # seek_bar_size[1]

                # SEEK BAR------------------

                if pctl.playing_length > 0:
                    draw.rect((seek_bar_position[0], seek_bar_position[1]),
                              (int(pctl.playing_time * seek_bar_size[0] / pctl.playing_length), seek_bar_size[1]),
                              colours.seek_bar_fill, True)

                if mouse_click and coll_point(mouse_position, seek_bar_position + [seek_bar_size[0]] + [seek_bar_size[1] + 2] ):
                    volume_hit = True
                    seek_down = True
                if right_click and coll_point(mouse_position, seek_bar_position + [seek_bar_size[0]] + [seek_bar_size[1]+ 2]):
                    pctl.pause()
                    if pctl.playing_state == 0:
                        pctl.play()
                if coll_point(mouse_position, seek_bar_position + seek_bar_size):
                    clicked = True
                    if mouse_wheel != 0:
                        pctl.new_time = pctl.playing_time + (mouse_wheel * 3)
                        pctl.playing_time += mouse_wheel * 3
                        if pctl.new_time < 0:
                            pctl.new_time = 0
                            pctl.playing_time = 0
                        pctl.playerCommand = 'seek'
                        pctl.playerCommandReady = True

                        # pctl.playing_time = pctl.new_time

                if seek_down is True:
                    if mouse_position[0] == 0:
                        seek_down = False
                        seek_hit = True

                if (mouse_up and coll_point(mouse_position, seek_bar_position + seek_bar_size)
                        and coll_point(click_location, seek_bar_position + seek_bar_size)) or mouse_up and volume_hit or seek_hit:
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
                        pctl.new_time = pctl.playing_length / 100 * seek
                        # print('seek to:' + str(pctl.new_time))
                        pctl.playerCommand = 'seek'
                        pctl.playerCommandReady = True
                        pctl.playing_time = pctl.new_time
                        if system == 'windows'and taskbar_progress:
                            windows_progress.update(True)

                # Activate top menu if right clicked in top bar past tabs
                # if right_click and mouse_position[1] < panelY and mouse_position[0] > l + 50:
                #     x_menu.activate()

                # Volume Bar--------------------------------------------------------

                if mouse_click and coll_point(mouse_position, volume_bar_position + volume_bar_size) or \
                                volume_bar_being_dragged is True:
                    clicked = True
                    if mouse_click is True or volume_bar_being_dragged is True:
                        gui.update += 1
                        volume_bar_being_dragged = True
                        volgetX = mouse_position[0]
                        if volgetX > volume_bar_position[0] + volume_bar_size[0]:
                            volgetX = volume_bar_position[0] + volume_bar_size[0]
                        if volgetX < volume_bar_position[0]:
                            volgetX = volume_bar_position[0]
                        volgetX -= volume_bar_position[0]
                        pctl.player_volume = volgetX / volume_bar_size[0] * 100
                        if mouse_down is False:
                            volume_bar_being_dragged = False

                    pctl.player_volume = int(pctl.player_volume)
                    pctl.set_volume()

                # if mouse_wheel != 0 and coll_point(mouse_position, (
                #            volume_bar_position[0] - 15, volume_bar_position[1] - 10, volume_bar_size[0] + 30,
                #            volume_bar_size[1] + 20 )):
                if mouse_wheel != 0 and mouse_position[1] > seek_bar_position[1] + 4 and not coll_point(mouse_position,
                                                                                                        seek_bar_position + seek_bar_size):

                    if pctl.player_volume + (mouse_wheel * volume_bar_increment) < 1:
                        pctl.player_volume = 0
                    elif pctl.player_volume + (mouse_wheel * volume_bar_increment) > 100:
                        pctl.player_volume = 100
                    else:
                        pctl.player_volume += mouse_wheel * volume_bar_increment
                    pctl.player_volume = int(pctl.player_volume)
                    pctl.set_volume()

                if right_click and coll_point(mouse_position, (
                            volume_bar_position[0] - 15, volume_bar_position[1] - 10, volume_bar_size[0] + 30,
                            volume_bar_size[1] + 20)):
                    if pctl.player_volume > 0:
                        volume_store = pctl.player_volume
                        pctl.player_volume = 0
                    else:
                        pctl.player_volume = volume_store

                    pctl.set_volume()

                draw.rect(volume_bar_position, volume_bar_size, colours.volume_bar_background, True)  # 22
                draw.rect(volume_bar_position, (int(pctl.player_volume * volume_bar_size[0] / 100), volume_bar_size[1]),
                          colours.volume_bar_fill, True)

                if album_mode and pctl.playing_state > 0 and window_size[0] > 820:

                    title = pctl.master_library[pctl.track_queue[pctl.queue_step]].title
                    artist = pctl.master_library[pctl.track_queue[pctl.queue_step]].artist

                    line = ""
                    if title != "":
                        line += title
                    if artist != "":
                        if line != "":
                            line += "  -  "
                        line += artist
                    line = trunc_line(line, 13, window_size[0] - 710)
                    draw_text((seek_bar_position[0], seek_bar_position[1] + 22), line, colours.side_bar_line1, 13)  # fontb1
                    if mouse_click and coll_point(mouse_position, (
                        seek_bar_position[0] - 10, seek_bar_position[1] + 20, window_size[0] - 710, 30)):
                        pctl.show_current()
                        # if pctl.playing_state > 0:
                        #     goto_album(pctl.playlist_playing)
                        # else:
                        #     goto_album(playlist_selected)

            # TIME----------------------
            text_time = get_display_time(pctl.playing_time)

            draw_text((time_display_position[0] + 140 + 2, window_size[1] - 29 + 1), text_time, colours.time_playing,
                      12)

            bx = 35
            by = window_size[1] - 30


            # BUTTONS
            # bottom buttons

            if GUI_Mode == 1:

                box = panelBY - seek_bar_size[1]

                # album_art_gen.display(pctl.track_queue[pctl.queue_step],
                #                       (0, window_size[1] - panelBY + seek_bar_size[1]), (box, box))

                # PLAY---
                buttons_x_offset = 0
                if bb_type == 1:
                    buttons_x_offset = int(window_size[0] / 2) - 100
                    control_line_bottom = 55

                play_colour = colours.media_buttons_off
                pause_colour = colours.media_buttons_off
                stop_colour = colours.media_buttons_off
                forward_colour = colours.media_buttons_off
                back_colour = colours.media_buttons_off

                if pctl.playing_state == 1:
                    play_colour = colours.media_buttons_active

                if auto_stop:
                    stop_colour = colours.media_buttons_active

                if pctl.playing_state == 2:
                    pause_colour = colours.media_buttons_active
                    play_colour = colours.media_buttons_active
                elif pctl.playing_state == 3:
                    play_colour = colours.media_buttons_active

                rect = (buttons_x_offset + 25 - 15, window_size[1] - control_line_bottom - 13, 50, 40)
                fields.add(rect)
                if coll_point(mouse_position, rect):
                    play_colour = colours.media_buttons_over
                    if mouse_click:
                        pctl.play()
                    if right_click:
                        pctl.show_current()

                draw.rect((buttons_x_offset + 25, window_size[1] - control_line_bottom), (14, 14), play_colour, True)
                # draw.rect_r(rect,[255,0,0,255], True)
                SDL_RenderCopy(renderer, c1, None, dst1)

                # PAUSE---
                x = 75 + buttons_x_offset
                y = window_size[1] - control_line_bottom

                rect = (x - 15, y - 13, 50, 40)
                fields.add(rect)
                if coll_point(mouse_position, rect):
                    pause_colour = colours.media_buttons_over
                    if mouse_click:
                        pctl.pause()

                # draw.rect_r(rect,[255,0,0,255], True)
                draw.rect((x, y + 0), (4, 13), pause_colour, True)
                draw.rect((x + 10, y + 0), (4, 13), pause_colour, True)

                # STOP---
                x = 125 + buttons_x_offset
                rect = (x - 14, y - 13, 50, 40)
                fields.add(rect)
                if coll_point(mouse_position, rect):
                    stop_colour = colours.media_buttons_over
                    if mouse_click:
                        pctl.stop()
                    if right_click:
                        auto_stop ^= True

                draw.rect((x, y + 0), (13, 13), stop_colour, True)
                # draw.rect_r(rect,[255,0,0,255], True)

                # FORWARD---
                rect = (buttons_x_offset + 230, window_size[1] - control_line_bottom - 10, 50, 35)
                fields.add(rect)
                if coll_point(mouse_position, rect):
                    forward_colour = colours.media_buttons_over
                    if mouse_click:
                        pctl.advance()
                    if right_click:
                        pctl.random_mode ^= True
                    if middle_click:
                        pctl.advance(rr=True)
                draw.rect((buttons_x_offset + 240, window_size[1] - control_line_bottom), (28, 14), forward_colour, True)
                # draw.rect_r(rect,[255,0,0,255], True)
                SDL_RenderCopy(renderer, c2, None, dst2)

                # BACK---
                rect = (buttons_x_offset + 170, window_size[1] - control_line_bottom - 10, 50, 35)
                fields.add(rect)
                if coll_point(mouse_position, rect):
                    back_colour = colours.media_buttons_over
                    if mouse_click:
                        pctl.back()
                    if right_click:
                        pctl.repeat_mode ^= True
                    if middle_click:
                        pctl.revert()

                draw.rect((buttons_x_offset + 180, window_size[1] - control_line_bottom), (28, 14), back_colour, True)
                # draw.rect_r(rect,[255,0,0,255], True)
                SDL_RenderCopy(renderer, c3, None, dst3)

                if window_size[0] > 630:

                    # shuffle button

                    x = window_size[0] - 295
                    y = window_size[1] - 27

                    rect = (x - 9, y - 5, 65, 25)
                    fields.add(rect)

                    rpbc = colours.mode_button_off
                    if (mouse_click or right_click) and coll_point(mouse_position, rect):
                        pctl.random_mode ^= True

                        if pctl.random_mode == False:
                            random_click_off = True

                    if pctl.random_mode:
                        rpbc = colours.mode_button_active

                    elif coll_point(mouse_position, rect):
                        if random_click_off == True:
                            rpbc = colours.mode_button_off
                        elif pctl.random_mode is True:
                            rpbc = colours.mode_button_active
                        else:
                            rpbc = colours.mode_button_over
                    else:
                        random_click_off = False

                    y += 2

                    draw.rect((x, y), (25, 4), rpbc, True)

                    y += 8
                    draw.rect((x, y), (50, 4), rpbc, True)

                    #draw_text((x,y), "RANDOM", rpbc, 13)

                    # REPEAT
                    x = window_size[0] - 350
                    y = window_size[1] - 27

                    rpbc = colours.mode_button_off

                    rect = (x - 15, y - 5, 59, 25)
                    fields.add(rect)
                    if (mouse_click or right_click) and coll_point(mouse_position, rect):
                        pctl.repeat_mode ^= True

                        if pctl.repeat_mode == False:
                            repeat_click_off = True

                    if pctl.repeat_mode:
                        rpbc = colours.mode_button_active

                    elif coll_point(mouse_position, rect):
                        if repeat_click_off == True:
                            rpbc = colours.mode_button_off
                        elif pctl.repeat_mode is True:
                            rpbc = colours.mode_button_active
                        else:
                            rpbc = colours.mode_button_over
                    else:
                        repeat_click_off = False

                    #draw_text((x,y), "REPEAT", rpbc, 13)
                    y += 10
                    w = 4

                    draw.rect((x, y), (35, w), rpbc, True)
                    draw.rect((x + 35 - w, y - 8), (w, 8), rpbc, True)
                    draw.rect((x + 15, y - 8), (20, w), rpbc, True)



            # NEW TOP BAR

            if GUI_Mode == 1:

                rect = (0,0,window_size[0], panelY)
                draw.rect_r(rect, colours.top_panel_background, True)

                # MULTI PLAYLIST-----------------------

                l = 0

                starting_l = 8

                spacing = 17

                if tab_hold:
                    drag_mode = False

                # Need to test length
                k = 0
                for w in range(len(pctl.multi_playlist)):
                    k += draw.text_calc(pctl.multi_playlist[w][0], 12)
                k = starting_l + (spacing * (len(pctl.multi_playlist))) + k
                k += 40
                k += draw.text_calc(get_playing_line(), 12)

                draw_alt = False
                if k > window_size[0] - 180:
                    # rect = (starting_l, 0, 10, 29)
                    # draw.rect()

                    starting_l += 12
                    spacing = 0
                    draw_alt = True


                # Process each tab on top panel
                for w in range(len(pctl.multi_playlist)):

                    if draw_alt and w != pctl.playlist_active:
                        continue

                    text_space = draw.text_calc(pctl.multi_playlist[w][0], 12)

                    rect = (starting_l + (spacing * w) + l, 1, text_space + 16, 29)
                    fields.add(rect)

                    draw.rect((starting_l + (spacing * w) + l, 0), (text_space + 16, 30), colours.tab_background, True)

                    if not pl_follow and w == pctl.active_playlist_playing:
                        draw.rect((starting_l + (spacing * w) + l, 0), (text_space + 16, 30), [255, 255, 255, 7], True)

                    if (tab_menu.active is True and tab_menu.reference == w) or tab_menu.active is False and coll_point(
                            mouse_position, (starting_l + (spacing * w) + l, 1, text_space + 16, 29)):
                        draw.rect((starting_l + (spacing * w) + l, 0), (text_space + 16, 30), colours.tab_highlight, True)

                    if w == pctl.playlist_active:
                        draw.rect((starting_l + (spacing * w) + l, 0), (text_space + 16, 30), colours.tab_background_active, True)
                        text_space = draw_text((starting_l + (spacing * w) + 7 + l, r[1], r[2], r[3]),
                                               pctl.multi_playlist[w][0],
                                               colours.tab_text_active, 12)

                    else:
                        text_space = draw_text((starting_l + (spacing * w) + 7 + l, r[1], r[2], r[3]),
                                               pctl.multi_playlist[w][0],
                                               colours.tab_text, 12)

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
                        gui.pl_update += 1
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
                    gui.pl_update += 1

                # ------------
                # Copy of above code for arrow keys
                if (key_left_press or key_right_press) and len(pctl.multi_playlist) > 1:

                    gui.pl_update += 1
                    gui.update += 1

                    if key_left_press:
                        switch_playlist(-1, True)

                    if key_right_press:
                        switch_playlist(1, True)

                        # ----------------

                l += 10
                y = 8

                if draw_alt:
                    l += 12 + 5
                    x = starting_l + (spacing * len(pctl.multi_playlist)) + 9 + l
                    rect = [x - 8, y - 4, 60, 23]
                    fields.add(rect)
                    if playlist_panel:
                        draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]),
                                  "PLAYLIST", colours.grey(125), 12)
                        if coll_point(mouse_position, rect) and (mouse_click or right_click):
                            playlist_panel = False
                    else:
                        if coll_point(mouse_position, rect):
                            draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]),
                                      "PLAYLIST", colours.grey(125), 12)
                            if mouse_click:
                                playlist_panel = True
                        else:
                            draw_text(
                                (starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]),
                                "PLAYLIST", colours.grey(100), 12)
                    l += 67

                x = starting_l + (spacing * len(pctl.multi_playlist)) + 9 + l

                rect = [x - 8, y - 4, 50, 23]

                fields.add(rect)

                if x_menu.active:

                    draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "MENU", colours.grey(125), 12)
                    if coll_point(mouse_position, rect) and (mouse_click or right_click):
                        x_menu.active = False

                else:
                    if coll_point(mouse_position, rect):
                        draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "MENU", colours.grey(125), 12)
                        if mouse_click or right_click:
                            x_menu.activate(position=(x+20,panelY))
                    else:
                        draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "MENU", colours.grey(100), 12)



                l += 50

                x = starting_l + (spacing * len(pctl.multi_playlist)) + 9 + l
                y = 8
                rect = [x - 6, y - 4, 60, 23]

                fields.add(rect)

                if album_mode:

                    draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "GALLERY", colours.grey(125), 12)
                    if coll_point(mouse_position, rect) and mouse_click:
                        toggle_album_mode()

                else:
                    if coll_point(mouse_position, rect):
                        draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "GALLERY", colours.grey(125), 12)
                        if mouse_click:
                            toggle_album_mode()
                    else:
                        draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "GALLERY", colours.grey(100), 12)

                if lastfm.connected:
                    l += 62

                    x = starting_l + (spacing * len(pctl.multi_playlist)) + 9 + l
                    y = 8
                    rect = [x - 6, y - 4, 58, 23]

                    fields.add(rect)

                    if not lastfm.hold:

                        draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "LAST.FM", colours.grey(125), 12)
                        if coll_point(mouse_position, rect) and mouse_click:
                            lastfm.toggle()

                    else:
                        if coll_point(mouse_position, rect):
                            draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "LAST.FM", colours.grey(125), 12)
                            if mouse_click:
                                lastfm.toggle()
                        else:
                            draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5 + 10, r[1] - 1, r[2], r[3]), "LAST.FM", colours.grey(100), 12)
                    l += 20

                m_l = x + 60

                l += 75

                if pctl.broadcast_active is False:
                    if loading_in_progress:
                        draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5, r[1] - 1, r[2], r[3]),
                                  "Importing...  " + str(to_got) + "/" + str(to_get), [245, 205, 0, 255], 11)
                    elif len(transcode_list) > 0:
                        line = "Transcoding... " + str(len(transcode_list)) + " Remaining " + transcode_state

                        draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5, r[1] - 1, r[2], r[3]),
                                  line, [245, 205, 0, 255], 11)
                elif pctl.join_broadcast:
                    draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5, r[1] - 1, r[2], r[3]),
                              "Streaming", [60, 75, 220, 255], 11)
                    l += 97

                else:

                    if pctl.encoder_pause == 1:
                        draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5, r[1] - 1, r[2], r[3]),
                                  "Streaming Paused:", [220, 75, 60, 255], 11)
                        l += 97
                    else:
                        draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5, r[1] - 1, r[2], r[3]),
                                  "Now Streaming:", [60, 75, 220, 255], 11)
                        l += 85
                    line = pctl.master_library[pctl.broadcast_index].artist + " - " + pctl.master_library[pctl.broadcast_index].title
                    line = trunc_line(line, 11, window_size[0] - l - 195)

                    l += 35 + draw_text((starting_l + (spacing * len(pctl.multi_playlist)) + 4 + l - 5, r[1] - 1, r[2], r[3]), line,
                                colours.grey(130), 11)

                    x = l
                    y = 10
                    w = 90
                    h = 9

                    # if gui.turbo:
                    #     x -= 90

                    w2 = int(pctl.broadcast_time / int(pctl.master_library[pctl.broadcast_index].length) * 90)

                    draw.rect((x, y), (w2, h), [30, 25, 170, 255], True)
                    draw.rect((x, y), (w, h), colours.grey(30))

                    l -= 15
                    l -= 85
                # Top line
                if not album_mode and (block6 or (side_panel_enable is False and pctl.broadcast_active is not True and pctl.playing_state > 0)):
                    line = ""

                    if pctl.playing_state < 3:
                        title = pctl.master_library[pctl.track_queue[pctl.queue_step]].title
                        artist = pctl.master_library[pctl.track_queue[pctl.queue_step]].artist
                    else:
                        title = pctl.tag_meta

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

                    l_max = window_size[0] - m_l - 40


                    if gui.turbo:
                        draw_text((window_size[0] - 104 - offset_extra, 8, 1), line, colours.side_bar_line1,
                                  11, max=l_max - 75)

                    else:
                        draw_text((window_size[0] - 15 - offset_extra, 8, 1), line, colours.side_bar_line1,
                                  11, max=l_max)


            # Overlay GUI ----------------------


            if playlist_panel:

                pl_items_len = len(pctl.multi_playlist)
                pl_max_view_len = int((window_size[1] - panelY) / 16)
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

                x = 2
                y = panelY + 1
                w = 400
                h = pl_max_view_len * 14 + 4

                pl_rect = (x, y, w, h)
                draw.rect_r(pl_rect, colours.bottom_panel_colour, True)
                draw.rect_r(pl_rect, [60,60,60,255], False)

                if genre_box_click and not coll_point(mouse_position, pl_rect):
                    playlist_panel = False

                p = 0
                for i, item in enumerate(pctl.multi_playlist):

                    if i < pl_view_offset:
                        continue
                    if p >= pl_max_view_len:
                        break

                    rect = (x, y + 1 + p * 14, 13, 13)
                    fields.add(rect)
                    if coll_point(mouse_position, rect):
                        rect2 = (x, y + 1 +  p*14, w - 2, 13)
                        draw.rect_r(rect2, [40, 40, 40, 255], True)
                        draw_text2((x + 1, y - 1 + p * 14), "X", [220, 60, 60, 255], 12, 300)
                        if genre_box_click:
                            delete_playlist(i)
                    else:
                        draw_text2((x + 1, y - 1 + p * 14), "X", [70, 70, 70, 255], 12, 300)

                    rect = (x + 13, y + 1 +  p*14, w - 12, 13)
                    fields.add(rect)
                    if coll_point(mouse_position, rect) and not tab_menu.active:

                        draw.rect_r(rect, [40,40,40,255], True)
                        if genre_box_click:
                            switch_playlist(i)
                            playlist_panel = False

                    if tab_menu.active and tab_menu.reference == i:
                        draw.rect_r(rect, [40, 40, 40, 255], True)
                    if right_click and coll_point(mouse_position, rect):
                        tab_menu.activate(copy.deepcopy(i))


                    draw_text2((x+15,y - 1 + p*14), item[0], [110,110,110,255], 12, 300)
                    draw_text2((x + w - 5, y - 1 + p * 14, 1), str(len(item[2])), [80, 80, 80, 255], 12, 300)

                    p += 1




            if new_playlist_box is True:
                draw.rect((int(window_size[0] / 2) - (playlist_entry_box_half[0]),
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1]))),
                          (playlist_entry_box_size[0], playlist_entry_box_size[1]), colours.top_panel_background, True)
                draw.rect((int(window_size[0] / 2) - (playlist_entry_box_half[0]),
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1]))),
                          (playlist_entry_box_size[0], playlist_entry_box_size[1]), colours.grey(75))

                draw.rect((int(window_size[0] / 2) - (playlist_entry_box_half[0]) + 15,
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1])) + 30), (220, 19), colours.grey(50))
                NPN += input_text
                if key_backspace_press and len(NPN) > 0:
                    NPN = NPN[:-1]
                draw_text((int(window_size[0] / 2) - (playlist_entry_box_half[0]) + 9,
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1])) + 5,
                           playlist_entry_box_size[0] - 40, playlist_entry_box_size[1] - 95), "New Playlist:",
                          colours.side_bar_line2,
                          12)
                c_blink = 200
                draw_text((int(window_size[0] / 2) - (playlist_entry_box_half[0]) + 20,
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1])) + 30,
                           playlist_entry_box_size[0] - 40, playlist_entry_box_size[1] - 95), NPN + cursor,
                          colours.side_bar_line2, 12)
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
                draw.rect((int(window_size[0] / 2) - (playlist_entry_box_half[0]),
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1]))),
                          (playlist_entry_box_size[0], playlist_entry_box_size[1]), colours.top_panel_background, True)
                draw.rect((int(window_size[0] / 2) - (playlist_entry_box_half[0]),
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1]))),
                          (playlist_entry_box_size[0], playlist_entry_box_size[1]), colours.grey(75))

                draw.rect((int(window_size[0] / 2) - (playlist_entry_box_half[0]) + 15,
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1])) + 30), (220, 19), colours.grey(50))
                NPN += input_text
                if key_backspace_press and len(NPN) > 0:
                    NPN = NPN[:-1]
                draw_text((int(window_size[0] / 2) - (playlist_entry_box_half[0]) + 9,
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1])) + 5,
                           playlist_entry_box_size[0] - 40, playlist_entry_box_size[1] - 95), "Rename Playlist:",
                          colours.side_bar_line2,
                          12)
                c_blink = 200
                draw_text((int(window_size[0] / 2) - (playlist_entry_box_half[0]) + 20,
                           (int(window_size[1] / 2) - (playlist_entry_box_half[1])) + 30,
                           playlist_entry_box_size[0] - 40, playlist_entry_box_size[1] - 95), NPN + cursor,
                          colours.side_bar_line2, 12)
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

                w = draw.text_calc(message_box_text, 12) + 20
                if w < 210:
                    w = 210
                h = 20
                x = int(window_size[0] / 2) - int(w / 2)
                y = int(window_size[1] / 2) - int(h / 2)

                draw.rect((x, y), (w, h), colours.top_panel_background, True)
                draw.rect((x, y), (w, h), colours.grey(75))

                draw_text((x + int(w / 2), y + 2, 2), message_box_text, colours.grey(150), 12)

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

                draw.rect((x, y), (w, h), colours.top_panel_background, True)
                draw.rect((x, y), (w, h), colours.grey(75))

                lfm_password += input_text

                if key_backspace_press and len(lfm_password) > 0:
                    lfm_password = lfm_password[:-1]

                line = "Last FM Account Password: "

                for c in lfm_password:
                    line += "●"

                draw_text((x + 10, y + 7 + 20), line, colours.grey(150), 12)
                draw_text((x + 10, y + 7), "Please enter the following.", colours.grey(150), 12)

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

                draw.rect((x, y), (w, h), colours.top_panel_background, True)
                draw.rect((x, y), (w, h), colours.grey(75))

                lfm_username += input_text

                if key_backspace_press and len(lfm_username) > 0:
                    lfm_username = lfm_username[:-1]

                line = "Last FM Account Username: " + lfm_username

                draw_text((x + 10, y + 7 + 20), line, colours.grey(150), 12)
                draw_text((x + 10, y + 7), "Please enter the following then try again.  Press F8 at any time to reset.",
                          colours.grey(150), 12)

            if genre_box:

                w = 640
                h = 260
                x = int(window_size[0] / 2) - int(w / 2)
                y = int(window_size[1] / 2) - int(h / 2)

                box_rect = (x, y, w, h)

                if genre_box_click and not coll_point(mouse_position, box_rect):
                    genre_box = False

                draw.rect((x, y), (w, h), colours.top_panel_background, True)
                draw.rect((x, y), (w, h), colours.grey(75))

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
                        draw.rect((x, y), (110, 20), [255, 255, 255, 35], True)

                    fields.add(copy.deepcopy(item_rect))
                    if coll_point(mouse_position, item_rect):
                        draw.rect_r(item_rect, [255, 255, 255, 10], True)

                    draw.rect((x, y), (110, 20), colours.grey(25))
                    line = item[0][:20]
                    draw_text((x + 3, y + 2), line, colours.grey(175), 10)

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
                    draw.rect_r(ok_rect, [255, 255, 255, 8], True)
                draw.rect_r(ok_rect, colours.grey(50))
                draw_text((x + 14, y + 2), 'Generate', colours.grey(150), 10)

                if genre_box_click and coll_point(mouse_position, ok_rect):
                    print('ok')
                    playlist = []
                    for genre in genre_items:
                        playlist += stats_gen.genre_dict[genre]

                        for index in pctl.multi_playlist[genre_box_pl][2]:
                            if genre.lower() in pctl.master_library[index].parent_folder_path.lower().replace('-',
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

                # draw.rect((0,0),(window_size[0], window_size[1]), [0,0,0,120], True)

                draw.rect((x, y), (w, h), colours.top_panel_background, True)
                draw.rect((x, y), (w, h), colours.grey(75))

                if key_shift_down:

                    # y += 24

                    draw_text((x + 8 + 10, y + 40), "Secret Operations Menu:", colours.grey(200), 12)

                    y += 24
                    x += 15
                    files_to_purge = []

                    for item in os.listdir(pctl.master_library[r_menu_index].parent_folder_path):
                        if 'AlbumArt' in item or 'desktop.ini' in item or 'Folder.jpg' in item:
                            files_to_purge.append(os.path.join(pctl.master_library[r_menu_index].parent_folder_path, item))

                    line = "1. Purge potentially hidden image/ini files from folder (" + str(
                        len(files_to_purge)) + " Found)"
                    draw_text((x + 8 + 10, y + 40), line, colours.grey(200), 12)

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
                    draw.rect((x + w - 135 - 1, y + h - 125 - 1), (102, 102), colours.grey(30))
                    album_art_gen.display(r_menu_index, (x + w - 135, y + h - 125), (100, 100))
                    y -= 24

                    draw_text((x + 8 + 10, y + 40), "Title:", colours.grey(200), 12)
                    draw_text((x + 8 + 90, y + 40), pctl.master_library[r_menu_index].title, colours.grey(200), 12)

                    draw_text((x + w - 50, y + 40, 2), pctl.master_library[r_menu_index].file_ext, colours.grey(200), 12)

                    y += 15

                    draw_text((x + 8 + 10, y + 40), "Artist:", colours.grey(200), 12)
                    draw_text((x + 8 + 90, y + 40), pctl.master_library[r_menu_index].artist, colours.grey(200), 12)

                    y += 15

                    draw_text((x + 8 + 10, y + 40), "Album:", colours.grey(200), 12)
                    draw_text((x + 8 + 90, y + 40), pctl.master_library[r_menu_index].album, colours.grey(200),
                              12)

                    y += 23

                    draw_text((x + 8 + 10, y + 40), "Path:", colours.grey(200), 12)
                    draw_text((x + 8 + 90, y + 40), trunc_line(pctl.master_library[r_menu_index].fullpath, 12, 420),
                              colours.grey(200), 12)

                    y += 15

                    draw_text((x + 8 + 10, y + 40), "Samplerate:", colours.grey(200), 12)
                    draw_text((x + 8 + 90, y + 40), str(pctl.master_library[r_menu_index].samplerate), colours.grey(200), 12)

                    y += 15

                    draw_text((x + 8 + 10, y + 40), "Bitrate:", colours.grey(200), 12)
                    line =  str(pctl.master_library[r_menu_index].bitrate)
                    draw_text((x + 8 + 90, y + 40), line, colours.grey(200), 12)

                    y += 15

                    draw_text((x + 8 + 10, y + 40), "Duration:", colours.grey(200), 12)
                    line = time.strftime('%M:%S', time.gmtime(pctl.master_library[r_menu_index].length))
                    draw_text((x + 8 + 90, y + 40), line, colours.grey(200), 12)

                    y += 15

                    draw_text((x + 8 + 10, y + 40), "Filesize:", colours.grey(200), 12)
                    draw_text((x + 8 + 90, y + 40), get_filesize_string(pctl.master_library[r_menu_index].size), colours.grey(200), 12)


                    y += 23

                    draw_text((x + 8 + 10, y + 40), "Genre:", colours.grey(200), 12)
                    draw_text((x + 8 + 90, y + 40), pctl.master_library[r_menu_index].genre, colours.grey(200), 12)
                    y += 15

                    draw_text((x + 8 + 10, y + 40), "Date:", colours.grey(200), 12)
                    draw_text((x + 8 + 90, y + 40), str(pctl.master_library[r_menu_index].date), colours.grey(200), 12)

                    y += 23

                    key = pctl.master_library[r_menu_index].title + pctl.master_library[r_menu_index].filename
                    total = 0
                    ratio = 0
                    if (key in pctl.star_library) and pctl.star_library[key] != 0 and pctl.master_library[r_menu_index].length != 0:
                        total = pctl.star_library[key]
                        ratio = total / pctl.master_library[r_menu_index].length

                    draw_text((x + 8 + 10, y + 40), "Play Count:", colours.grey(200), 12)
                    draw_text((x + 8 + 90, y + 40), str(int(ratio)), colours.grey(200), 12)

                    y += 15

                    line = time.strftime('%H:%M:%S',
                                         time.gmtime(total))

                    draw_text((x + 8 + 10, y + 40), "Playtime:", colours.grey(200), 12)
                    draw_text((x + 8 + 90, y + 40), str(line), colours.grey(200), 12)

            if pref_box.enabled:
                pref_box.render()

            if renamebox:

                w = 420
                h = 220
                x = int(window_size[0] / 2) - int(w / 2)
                y = int(window_size[1] / 2) - int(h / 2)

                draw.rect((x, y), (w, h), colours.top_panel_background, True)
                draw.rect((x, y), (w, h), colours.grey(50))

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
                    if pctl.master_library[item].parent_folder_name == pctl.master_library[rename_index].parent_folder_name:
                        if pctl.master_library[item].is_cue == True:
                            warncue = True
                        else:
                            r_todo.append(item)

                draw_text((x + 10, y + 10,), "Physically rename all tracks in folder to format:", colours.grey(150), 12)
                draw_text((x + 14, y + 40,), NRN + cursor, colours.grey(150), 12)
                # c_blink = 200

                draw.rect((x + 8, y + 38), (300, 22), colours.grey(50))

                draw.rect((x + 8 + 300 + 10, y + 38), (80, 22), colours.grey(50))

                rect = (x + 8 + 300 + 10, y + 38, 80, 22)
                fields.add(rect)
                if coll_point(mouse_position, rect):
                    draw.rect((x + 8 + 300 + 10, y + 38), (80, 22), [50, 50, 50, 70], True)

                draw_text((x + 8 + 10 + 300 + 40, y + 40, 2), "WRITE (" + str(len(r_todo)) + ")", colours.grey(150), 12)

                draw_text((x + 10, y + 70,), "%n - Track Number", colours.grey(150), 12)
                draw_text((x + 10, y + 82,), "%a - Artist Name", colours.grey(150), 12)
                draw_text((x + 10, y + 94,), "%t - Track Title", colours.grey(150), 12)
                draw_text((x + 150, y + 70,), "%b - Album Title", colours.grey(150), 12)
                draw_text((x + 150, y + 82,), "%x - File Extension", colours.grey(150), 12)
                draw_text((x + 150, y + 94,), "%u - Use Underscores", colours.grey(150), 12)

                afterline = ""
                warn = False
                underscore = False

                for item in r_todo:
                    afterline = ""

                    if pctl.master_library[item].track_number == "" or pctl.master_library[item].artist == "" or \
                                    pctl.master_library[item].title == "" or pctl.master_library[item].album == "":
                        warn = True

                    set = 0
                    while set < len(NRN):
                        if NRN[set] == "%" and set < len(NRN) - 1:
                            set += 1
                            if NRN[set] == 'n':
                                if len(str(pctl.master_library[item].track_number)) < 2:
                                    afterline += "0"
                                afterline += str(pctl.master_library[item].track_number)
                            elif NRN[set] == 'a':
                                afterline += pctl.master_library[item].artist
                            elif NRN[set] == 't':
                                afterline += pctl.master_library[item].title
                            elif NRN[set] == 'b':
                                afterline += pctl.master_library[item].album
                            elif NRN[set] == 'x':
                                afterline += "." + pctl.master_library[item].file_ext.lower()
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
                          trunc_line("BEFORE:  " + pctl.master_library[rename_index].filename, 12, 390), colours.grey(150), 12)
                draw_text((x + 10, y + 135,), trunc_line("AFTER:     " + afterline, 12, 390), colours.grey(150), 12)

                if (len(NRN) > 3 and len(pctl.master_library[rename_index].filename) > 3 and afterline[-3:].lower() !=
                    pctl.master_library[rename_index].filename[-3:].lower()) or len(NRN) < 4:
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
                            time.sleep(1 + (prefs.pause_fade_time / 1000))

                        afterline = ""

                        set = 0
                        while set < len(NRN):
                            if NRN[set] == "%" and set < len(NRN) - 1:
                                set += 1
                                if NRN[set] == 'n':
                                    if len(str(pctl.master_library[item].track_number)) < 2:
                                        afterline += "0"
                                    afterline += str(pctl.master_library[item].track_number)
                                elif NRN[set] == 'a':
                                    afterline += pctl.master_library[item].artist
                                elif NRN[set] == 't':
                                    afterline += pctl.master_library[item].title
                                elif NRN[set] == 'b':
                                    afterline += pctl.master_library[item].album
                                elif NRN[set] == 'x':
                                    afterline += "." + pctl.master_library[item].file_ext.lower()
                            else:
                                afterline += NRN[set]
                            set += 1
                        if underscore:
                            afterline = afterline.replace(' ', "_")

                        for char in afterline:
                            if char in '\\/:*?"<>|':
                                afterline = afterline.replace(char, '')

                        oldname = pctl.master_library[item].filename
                        oldpath = pctl.master_library[item].fullpath

                        try:
                            print('Renaming...')

                            playt = 0
                            oldkey = pctl.master_library[item].title + pctl.master_library[item].filename
                            oldpath = pctl.master_library[item].fullpath

                            oldsplit = os.path.split(oldpath)

                            os.rename(pctl.master_library[item].fullpath, os.path.join(oldsplit[0], afterline))

                            pctl.master_library[item].fullpath = os.path.join(oldsplit[0], afterline)
                            pctl.master_library[item].filename = afterline

                            newkey = pctl.master_library[item].title + pctl.master_library[item].filename

                            if oldkey in pctl.star_library:
                                playt = pctl.star_library[oldkey]
                                del pctl.star_library[oldkey]
                            if newkey in pctl.star_library:
                                pctl.star_library[newkey] += playt
                            elif playt > 0:
                                pctl.star_library[newkey] = playt

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

                draw.rect((x, y), (w, h), colours.top_panel_background, True)
                draw.rect((x, y), (w, h), colours.grey(50))

                NXN += input_text

                if key_backspace_press and len(NXN) > 0:
                    NXN = NXN[:-1]

                if key_ctrl_down and key_v_press:
                    # NXN = r_window.clipboard_get()
                    NXN = pyperclip.paste()

                if key_esc_press or (mouse_click and not coll_point(mouse_position, (x, y, w, h))):
                    radiobox = False

                draw_text((x + 10, y + 10,), "Open HTTP Audio Stream", colours.grey(150), 12)
                draw_text((x + 14, y + 40,), NXN + cursor, colours.grey(150), 12)
                c_blink = 200

                draw.rect((x + 8, y + 38), (350, 22), colours.grey(50))

                rect = (x + 8 + 350 + 10, y + 38, 40, 22)
                fields.add(rect)

                if coll_point(mouse_position, rect):
                    draw.rect((x + 8 + 350 + 10, y + 38), (40, 22), [40, 40, 40, 60], True)

                draw.rect((x + 8 + 350 + 10, y + 38), (40, 22), colours.grey(50))
                draw_text((x + 8 + 10 + 350 + 10, y + 40), "GO", colours.grey(150), 12)

                if (key_return_press_w or (
                            mouse_click and coll_point(mouse_position,
                                                       (x + 8 + 350 + 10, y + 38, 40, 22)))) and 'http' in NXN:
                    pctl.url = NXN.encode('utf-8')
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

                draw.rect((search_box_location_x, window_size[1] - 90),
                          (quick_search_box_size[0], quick_search_box_size[1]), colours.bottom_panel_colour, True)
                draw.rect((search_box_location_x, window_size[1] - 90),
                          (quick_search_box_size[0], quick_search_box_size[1]), colours.grey(60))

                if len(input_text) > 0:
                    search_index = -1

                NSN += input_text

                if key_backspace_press and len(NSN) > 0:
                    NSN = NSN[:-1]
                c_blink = 200
                draw_text((search_box_location_x + 8, window_size[1] - 85), "SEARCH: " + NSN + cursor, colours.grey(125), 12)
                if key_esc_press:
                    new_playlist_box = False

                if len(input_text) > 0 or key_down_press is True:

                    gui.pl_update += 1

                    oi = search_index

                    while search_index < len(default_playlist) - 1:
                        search_index += 1
                        if search_index > len(default_playlist) - 1:
                            search_index = 0

                        search_terms = NSN.lower().split()
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
                            break

                    else:
                        search_index = oi

                if key_up_press is True:

                    gui.pl_update += 1
                    oi = search_index

                    while search_index > 1:
                        search_index -= 1
                        if search_index > len(default_playlist) - 1:
                            search_index = len(default_playlist) - 1
                        search_terms = NSN.lower().split()
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

                            break
                    else:
                        search_index = oi
                if key_return_press is True and search_index > -1:
                    gui.pl_update += 1
                    pctl.jump(default_playlist[search_index], search_index)
                    if album_mode:
                        goto_album(pctl.playlist_playing)

            else:

                if key_up_press:
                    shift_selection = []

                    pctl.show_selected()
                    gui.pl_update += 1

                    if playlist_selected > 0:
                        playlist_selected -= 1

                    if playlist_position > 0 and playlist_selected < playlist_position + 2:
                        playlist_position -= 1
                    if playlist_selected > len(default_playlist):
                        playlist_selected = len(default_playlist)

                if key_down_press and playlist_selected < len(default_playlist):
                    shift_selection = []
                    pctl.show_selected()
                    gui.pl_update += 1

                    if playlist_selected < len(default_playlist) - 1:
                        playlist_selected += 1

                    if playlist_position < len(
                            default_playlist) and playlist_selected > playlist_position + playlist_view_length - 3:
                        playlist_position += 1

                    if playlist_selected < 0:
                        playlist_selected = 0

                if key_return_press:
                    gui.pl_update += 1
                    if playlist_selected > len(default_playlist) - 1:
                        playlist_selected = 0
                        shift_selection = []
                    pctl.jump(default_playlist[playlist_selected], playlist_selected)
                    if album_mode:
                        goto_album(pctl.playlist_playing)

        # Unicode edit display---------------------
        if len(editline) > 0:
            ll = draw.text_calc(editline, 12)
            draw.rect((window_size[0] - ll - 10, 0), (ll + 15, 18), [0, 0, 0, 255], True)
            draw_text((window_size[0] - ll - 5, 3), editline, colours.grey(210), 12)

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

            draw.rect((x, y), (w, h), colours.top_panel_background, True)
            draw.rect((x, y), (w, h), colours.grey(75))

            draw_text((x + 105, y + 21), "Japanese text encoding correction.", colours.grey(190), 12)

            y += 20

            draw_text((x + 105, y + 21), "Select from list if correct shown:", colours.grey(190), 11)

            y -= 20
            x += 20
            y += 20

            if enc_field == "Artist":
                draw.rect((x, y), (60, 20), [80, 80, 80, 80], True)
            draw.rect((x, y), (60, 20), colours.grey(75))
            draw_text((x + 6, y + 2), "Artist", colours.grey(200), 12)
            if coll_point(mouse_position, (x, y, 60, 20)) and encoding_box_click:
                enc_field = "Artist"

            y += 25

            if enc_field == "Title":
                draw.rect((x, y), (60, 20), [80, 80, 80, 80], True)
            draw.rect((x, y), (60, 20), colours.grey(75))
            draw_text((x + 6, y + 2), "Title", colours.grey(200), 12)
            if coll_point(mouse_position, (x, y, 60, 20)) and encoding_box_click:
                enc_field = "Title"

            y += 25

            if enc_field == "Album":
                draw.rect((x, y), (60, 20), [80, 80, 80, 80], True)
            draw.rect((x, y), (60, 20), colours.grey(75))
            draw_text((x + 6, y + 2), "Album", colours.grey(200), 12)
            if coll_point(mouse_position, (x, y, 60, 20)) and encoding_box_click:
                enc_field = "Album"

            y += 25

            if enc_field == "All":
                draw.rect((x, y), (60, 20), [80, 80, 80, 80], True)
            draw.rect((x, y), (60, 20), colours.grey(75))
            draw_text((x + 6, y + 2), "All", colours.grey(200), 12)
            if coll_point(mouse_position, (x, y, 60, 20)) and encoding_box_click:
                enc_field = "All"

            y += 40

            if enc_setting == 1:
                draw.rect((x, y), (60, 20), [80, 80, 80, 80], True)
            draw.rect((x, y), (60, 20), colours.grey(75))
            draw_text((x + 6, y + 2), "Track", colours.grey(200), 12)
            if coll_point(mouse_position, (x, y, 60, 20)) and encoding_box_click:
                enc_setting = 1

            y += 25

            if enc_setting == 0:
                draw.rect((x, y), (60, 20), [80, 80, 80, 80], True)
            draw.rect((x, y), (60, 20), colours.grey(75))
            draw_text((x + 6, y + 2), "Folder", colours.grey(200), 12)
            if coll_point(mouse_position, (x, y, 60, 20)) and encoding_box_click:
                enc_setting = 0

            x += 80
            y -= 100
            w = 295
            h = 14

            y += 15

            for enco in encodings:

                artist = pctl.master_library[encoding_target].artist
                title = pctl.master_library[encoding_target].title
                album = pctl.master_library[encoding_target].album

                draw.rect((x, y), (w, h), colours.top_panel_background, True)

                rect = (x, y, w, h - 1)
                fields.add(rect)
                if coll_point(mouse_position, rect):
                    draw.rect((x, y), (w, h), colours.grey(50), True)
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

                draw_text((x + 5, y), line, colours.grey(150), 11)

                y += h
            draw.rect((x, y - (h * len(encodings))), (w, h * len(encodings)), colours.grey(50))

        if draw_border:

            rect = (window_size[0] - 55, window_size[1] - 35, 55 - 2, 35 - 2)
            fields.add(rect)
            if draw_border and coll_point(mouse_position, rect):
                draw_text((window_size[0] - 15, window_size[1] - 20), "↘", [200, 200, 200, 255], 16)

            rect = (window_size[0] - 65, 5, 35, 20)
            fields.add(rect)
            if coll_point(mouse_position, rect):
                draw.rect((window_size[0] - 65, 5), (35, 20), [70, 70, 70, 100], True)
                if mouse_click or ab_click:
                    SDL_MinimizeWindow(t_window)
                    mouse_down = False
                    mouse_click = False
                    drag_mode = False
            draw.rect((window_size[0] - 65, 5), (35, 20), colours.grey(40))

            rect = (window_size[0] - 25, 5, 20, 20)
            fields.add(rect)
            if coll_point(mouse_position, rect):
                draw.rect((window_size[0] - 25, 5), (20, 20), [80, 80, 80, 120], True)
                if mouse_click or ab_click:
                    running = False
            draw.rect((window_size[0] - 25, 5), (20, 20), colours.grey(40))

            draw.rect((0, 0), window_size, colours.grey(90))

        gui.update -= 1

        if gui.turbo:
            gui.level_update = True
        else:
            SDL_RenderPresent(renderer)

    if pctl.playing_state != 1 and gui.level_peak != [0, 0] and gui.turbo:

        gui.time_passed = gui.level_time.hit()
        if gui.time_passed > 1:
            gui.time_passed = 0
        while gui.time_passed > 0.020:
            gui.level_peak[1] -= 0.4
            if gui.level_peak[1] < 0:
                gui.level_peak[1] = 0
            gui.level_peak[0] -= 0.4
            if gui.level_peak[0] < 0:
                gui.level_peak[0] = 0
            gui.time_passed -= 0.020
        gui.level_update = True

    if gui.level_update is True and not resize_mode:
        gui.level_update = False

        # testing

        if gui.vis == 2 and gui.spec is not None:

            if gui.update_spec == 0 and pctl.playing_state != 2:
                time.sleep(0.01)
                for i in range(len(gui.spec)):
                    if gui.spec[i] > 0:
                        gui.spec[i] -= 1
                        gui.level_update = True
            if spec_smoothing:
                if not fast_bin_av:

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
                    gui.s_spec = fast_display(gui.spec,gui.s_spec)

                if pctl.playing_state == 0 and checkEqual(gui.s_spec):
                    gui.level_update = True
                    time.sleep(0.008)

            else:
                gui.s_spec = gui.spec
            x = window_size[0] - 20 - offset_extra - 70 - 0
            y = 5
            w = 72 + 24 - 6 - 10
            h = 20
            rect = (x, y, w, h)
            draw.rect_r(rect, colours.top_panel_background, True)
            draw.rect_r(rect, [255, 255, 255, 13], True)

            xx = 0
            on = 0

            SDL_SetRenderDrawColor(renderer, colours.vis_colour[0],
                                   colours.vis_colour[1], colours.vis_colour[2],
                                   colours.vis_colour[3])

            for item in gui.s_spec:

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
                draw.fast_fill_rect(xx+x, yy, 3, item)

                xx += 4

        if gui.vis == 1:

            offset_extra = 0
            if draw_border:
                offset_extra = 61

            x = window_size[0] - 20 - offset_extra
            y = 16
            w = 5
            s = 1
            # draw.rect((x - 70, y - 10), (80, 18), colours.grey(15), True)

            for t in range(12):

                if gui.level_peak[0] < t:
                    met = False
                else:
                    met = True
                if gui.level_peak[0] < 0.2:
                    met = False

                if t < 7:
                    cc = colours.level_green
                    if met is False:
                        cc = [0, 30, 0, 255]
                elif t < 10:
                    cc = colours.level_yellow
                    if met is False:
                        cc = [30, 30, 0, 255]
                else:
                    cc = colours.level_red
                    if met is False:
                        cc = [30, 0, 0, 255]

                if gui.level > 0 and pctl.playing_state > 0:
                    pass
                draw.rect(((x - (w * t) - (s * t)), y), (w, w), cc, True)

            y -= 7
            for t in range(12):

                if gui.level_peak[1] < t:
                    met = False
                else:
                    met = True
                if gui.level_peak[1] < 0.2:
                    met = False

                if t < 7:
                    cc = colours.level_green
                    if met is False:
                        cc = [0, 30, 0, 255]
                elif t < 10:
                    cc = colours.level_yellow
                    if met is False:
                        cc = [30, 40, 0, 255]
                else:
                    cc = colours.level_red
                    if met is False:
                        cc = [30, 0, 0, 255]

                if gui.level > 0 and pctl.playing_state > 0:
                    pass
                draw.rect(((x - (w * t) - (s * t)), y), (w, w), cc, True)

        SDL_RenderPresent(renderer)

    # print(pctl.playing_state)
    # -------------------------------------------------------------------------------------------
    # Broadcast control

    if pctl.broadcast_active and pctl.broadcast_time > pctl.master_library[pctl.broadcast_index].length and not pctl.join_broadcast:
        pctl.broadcast_position += 1
        print('next')
        if pctl.broadcast_position > len(pctl.multi_playlist[pctl.broadcast_playlist][2]) - 1:
            print('reset')
            pctl.broadcast_position = 0

        pctl.broadcast_index = pctl.multi_playlist[pctl.broadcast_playlist][2][pctl.broadcast_position]
        pctl.broadcast_time = 0
        pctl.target_open = pctl.master_library[pctl.broadcast_index].fullpath
        pctl.bstart_time = pctl.master_library[pctl.broadcast_index].start_time
        pctl.playerCommand = "encnext"
        pctl.playerCommandReady = True
        pctl.broadcast_line = pctl.master_library[pctl.broadcast_index].artist + " - " + pctl.master_library[pctl.broadcast_index].title

    if pctl.broadcast_active and pctl.broadcast_time != pctl.broadcast_last_time:
        pctl.broadcast_last_time = pctl.broadcast_time
        gui.update += 1
    if pctl.broadcast_active and pctl.broadcast_time == 0:
        gui.pl_update += 1

    # Playlist and pctl.track_queue

    if pctl.playing_state == 1 and pctl.playing_time + (
            prefs.cross_fade_time / 1000) + 0.5 >= pctl.playing_length and pctl.playing_time > 2:

        if auto_stop:
            pctl.stop()
            gui.update += 2
            auto_stop = False

        elif pctl.repeat_mode is True:

            pctl.playing_time = 0
            pctl.new_time = 0
            pctl.playerCommand = 'seek'
            pctl.playerCommandReady = True

        elif pctl.random_mode is False and len(default_playlist) - 2 > pctl.playlist_playing and \
                        pctl.master_library[default_playlist[pctl.playlist_playing]].is_cue is True \
                and pctl.master_library[default_playlist[pctl.playlist_playing + 1]].filename == \
                pctl.master_library[default_playlist[pctl.playlist_playing]].filename and int(
                pctl.master_library[default_playlist[pctl.playlist_playing]].track_number) == int(
                pctl.master_library[default_playlist[pctl.playlist_playing + 1]].track_number) - 1:
            print("CUE Gap-less")
            pctl.playlist_playing += 1
            pctl.queue_step += 1
            pctl.track_queue.append(default_playlist[pctl.playlist_playing])

            pctl.playing_state = 1
            pctl.playing_time = 0
            pctl.playing_length = pctl.master_library[pctl.track_queue[pctl.queue_step]].length
            pctl.start_time = pctl.master_library[pctl.track_queue[pctl.queue_step]].start_time

            gui.update += 1
            gui.pl_update += 1

        else:
            pctl.advance()
            pctl.playing_time = 0

    if taskbar_progress and system == 'windows' and pctl.playing_state == 1:
        windows_progress.update()

    if (pctl.playing_state == 1 or pctl.playing_state == 3) and gui.lowered is False:
        if int(pctl.playing_time) != int(pctl.last_playing_time):
            pctl.last_playing_time = pctl.playing_time
            gui.update = 1

    if len(pctl.track_queue) > 100 and pctl.queue_step > 1:
        del pctl.track_queue[0]
        pctl.queue_step -= 1

    # cursor blinker
    if c_blink > 0:
        c_blink -= 1
        c_time += cursor_blink_timer.hit()
        if c_time > 3:
            c_time = 0
        if c_time > 0.6:
            c_time = 0
            gui.update += 1
            if cursor == "|":
                cursor = ""
            elif cursor == "":
                cursor = "|"
        if input_text != "":
            c_time = 0
            cursor = "|"
            gui.update += 1

    if system == 'windows':

        if mouse_down is False:
            drag_mode = False

        if mouse_click and mouse_down and 1 < mouse_position[1] < 30 and m_l < mouse_position[0] < window_size[
                0] - 80 and drag_mode is False and clicked is False:

            drag_mode = True

            lm = copy.deepcopy(mouse_position)

        if mouse_up:
            drag_mode = False

        if drag_mode:
            # mp = win32api.GetCursorPos()

            p_x = pointer(c_int(0))
            p_y = pointer(c_int(0))
            SDL_GetGlobalMouseState(p_x,p_y)
            mp = [p_x.contents.value, p_y.contents.value]

            time.sleep(0.005)
            SDL_SetWindowPosition(t_window, mp[0] - lm[0], mp[1] - lm[1])

    # auto save
    if pctl.total_playtime - time_last_save > 600:
        print("Auto Save")
        pickle.dump(pctl.star_library, open(user_directory + "/star.p", "wb"))
        time_last_save = pctl.total_playtime

    if min_render_timer.get() > 60:
        min_render_timer.set()
        gui.pl_update += 1
        gui.update += 1

    if gui.lowered:
        time.sleep(0.1)

pctl.playerCommand = "unload"
pctl.playerCommandReady = True

print("writing database to disk")
pickle.dump(pctl.star_library, open(user_directory + "/star.p", "wb"))

view_prefs['star-lines'] = star_lines
view_prefs['update-title'] = update_title
view_prefs['split-line'] = split_line
view_prefs['side-panel'] = prefer_side
view_prefs['dim-art'] = dim_art
view_prefs['level-meter'] = gui.turbo
view_prefs['pl-follow'] = pl_follow
view_prefs['scroll-enable'] = scroll_enable
view_prefs['break-enable'] = break_enable
view_prefs['dd-index'] = dd_index
view_prefs['custom-line'] = custom_line_mode
view_prefs['thick-lines'] = thick_lines
view_prefs['append-date'] = append_date

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
        gui.vis,
        playlist_selected,
        album_mode_art_size,
        draw_border,
        prefs.enable_web,
        prefs.allow_remote,
        prefs.expose_web,
        prefs.enable_transcode,
        prefs.show_rym,
        None,
        None,
        None,
        None,
        None,
        None,
        None
        ]

pickle.dump(save, open(user_directory + "/state.p", "wb"))

if os.path.isfile(user_directory + '/lock'):
    os.remove(user_directory + '/lock')

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
