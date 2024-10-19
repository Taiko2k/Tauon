
# Tauon Music Box - Misc Functions Module

# Copyright © 2015-2020, Taiko2k captain(dot)gxj(at)gmail.com

#     This file is part of Tauon Music Box.
#
#     Tauon Music Box is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Tauon Music Box is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Lesser General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Tauon Music Box.  If not, see <http://www.gnu.org/licenses/>.


import time
import random
import colorsys
import subprocess
import os
import shlex
import zipfile
import glob
import locale
import re
import math
import threading
import urllib.parse
import gi
from gi.repository import GLib

def tmp_cache_dir():
    tmp_dir = GLib.get_tmp_dir()
    return os.path.join(tmp_dir, "TauonMusicBox")

# A seconds based timer
class Timer:
    def __init__(self, force=None):
        self.start = 0
        self.end = 0
        self.set()
        if force:
            self.force_set(force)

    def set(self):  # Reset
        self.start = time.monotonic()

    def hit(self):  # Return time and reset

        self.end = time.monotonic()
        elapsed = self.end - self.start
        self.start = time.monotonic()
        return elapsed

    def get(self):  # Return time only
        self.end = time.monotonic()
        return self.end - self.start

    def force_set(self, sec):
        self.start = time.monotonic()
        self.start -= sec


# Simple bool timer object
class TestTimer:
    def __init__(self, time):
        self.timer = Timer()
        self.time = time

    def test(self):
        return self.timer.get() > self.time

j_chars = "あおいえうんわらまやはなたさかみりひにちしきるゆむぬつすくれめへねてせけをろもほのとそこアイウエオンヲラマハナタサカミヒニチシキルユムフヌツスクレメヘネテセケロヨモホノトソコ"


# Test given proximity between two 2d points to given square
def point_proximity_test(a, b, p):
    return abs(a[0] - b[0]) < p and abs(a[1] - b[1]) < p

# Get distance between two points
def point_distance(a, b):
    return math.sqrt(abs(a[0] - b[0]) ** 2 + abs(b[1] - b[1]) ** 2)

# Removes whatever this is from a line, I forgot
def rm_16(line):
    if "ÿ þ" in line:
        for c in line:
            line = line[1:]
            if c == 'þ':
                break

        line = line[::2]
    return line


# Returns a string from seconds to a compact time format, e.g 2h:23
def get_display_time(seconds):
    result = divmod(int(seconds), 60)
    if result[0] > 99:
        result = divmod(result[0], 60)
        return str(result[0]) + 'h ' + str(result[1]).zfill(2)
    return str(result[0]).zfill(2) + ":" + str(result[1]).zfill(2)


def get_hms_time(seconds):
    m, s = divmod(round(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f'{h:d}:{m:02d}:{s:02d}'
    else:
        return f'{m:02d}:{s:02d}'

def hms_to_seconds(time_str):
    components = time_str.split(':')
    seconds = 0
    if len(components) == 1:  # If only seconds provided
        seconds = int(components[0])
    elif len(components) == 2:  # If minutes and seconds provided
        seconds = int(components[0]) * 60 + int(components[1])
    elif len(components) == 3:  # If hours, minutes, and seconds provided
        seconds = int(components[0]) * 3600 + int(components[1]) * 60 + int(components[2])
    return seconds

# Creates a string from number of bytes to X MB/kB etc with Locale adjustment
def get_filesize_string(file_bytes, rounding=2):
    if not file_bytes:
        return "0"
    if file_bytes < 1000:
        line = locale.str(file_bytes) + " B"
    elif file_bytes < 1000000:
        file_kb = round(file_bytes / 1000, rounding)
        line = locale.str(file_kb) + " KB"
    elif file_bytes < 1000000000:
        file_mb = round(file_bytes / 1000000, rounding)
        line = locale.str(file_mb) + " MB"
    else:
        file_mb = round(file_bytes / 1000000000, 1)
        line = locale.str(file_mb) + " GB"
    return line

def get_filesize_string_rounded(file_bytes):
    if not file_bytes:
        return "0"
    if file_bytes < 1000:
        line = str(round(file_bytes)) + " B"
    elif file_bytes < 1000000:
        file_kb = round(file_bytes / 1000)
        line = str(file_kb) + " KB"
    else:
        file_mb = round(file_bytes / 1000000, 1)
        line = str(file_mb) + " MB"
    return line

# Estimates the perceived luminance of a colour
def test_lumi(c1):
    return 1 - (0.299 * c1[0] + 0.587 * c1[1] + 0.114 * c1[2]) / 255

def rel_luminance(colour):
    r = colour[0] / 255
    g = colour[1] / 255
    b = colour[2] / 255

    if r < 0.03928:
        r /= 12.90
    else:
        r = ((r + 0.055) / 1.055) ** 2.4

    if g < 0.03928:
        g /= 12.90
    else:
        g = ((g + 0.055) / 1.055) ** 2.4

    if b < 0.03928:
        b /= 12.90
    else:
        b = ((b + 0.055) / 1.055) ** 2.4

    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(c1, c2):

    l1 = rel_luminance(c1)
    l2 = rel_luminance(c2)

    if l2 > l1:
        l2, l1 = l1, l2

    return (l1 + 0.05) / (l2 + 0.05)

# Gives the sum of first 3 elements in a list
def colour_value(c1):
    return c1[0] + c1[1] + c1[2]


# Performs alpha blending of one colour (rgba) onto another (rgb)
def alpha_blend(colour, base):
    alpha = colour[3] / 255
    return [int(alpha * colour[0] + (1 - alpha) * base[0]),
            int(alpha * colour[1] + (1 - alpha) * base[1]),
            int(alpha * colour[2] + (1 - alpha) * base[2]), 255]


# Change the alpha component of an RGBA list
def alpha_mod(colour, alpha):
    return [colour[0], colour[1], colour[2], alpha]


# Shift between two colours based on x where x is between 0 and limit
def colour_slide(a, b, x, x_limit):

    return (min(int(a[0] + ((b[0] - a[0]) * (x / x_limit))), 255),
     min(int(a[1] + ((b[1] - a[1]) * (x / x_limit))), 255),
     min(int(a[2] + ((b[2] - a[2]) * (x / x_limit))), 255), 255)


def hex_to_rgb(colour):
    colour = colour.strip("#")
    return list(int(colour[i:i + 2], 16) for i in (0, 2, 4)) + [255]


# Checks if all the numbers in a list are the same
def check_equal(lst):
    return not lst or lst.count(lst[0]) == len(lst)


# Check if the first 3 elements of a list are the same
def is_grey(lst):
    return lst[0] == lst[1] == lst[2]


# Gives a score from 0-7 based on number of seconds
def star_count(sec, dur):
    stars = 0
    if dur and sec / dur > 0.95:
        stars += 1
    if sec > 60 * 15:
        stars += 1
    if sec > 60 * 30:
        stars += 1
    if sec > 60 * 60:
        stars += 1
    if sec > 60 * 60 * 2:
        stars += 1
    if sec > 60 * 60 * 4:
        stars += 1
    if sec > 60 * 60 * 8:
        stars += 1
    if sec > 60 * 60 * 16:
        stars += 1
    return stars


def star_count3(sec, dur):
    stars = 0
    if dur and sec / dur > 0.95:
        stars += 1
    if dur and sec / dur > 1.95:
        stars += 1
    if sec > 60 * 5:
        stars += 1
    if sec > 60 * 10:
        stars += 1
    if sec > 60 * 15:
        stars += 1
    if sec > 60 * 20:
        stars += 1
    if sec > 60 * 30:
        stars += 1
    if sec > 60 * 60:
        stars += 1
    if sec > 60 * 60 * 1.5:
        stars += 1
    if sec > 60 * 60 * 1.75:
        stars += 1
    # if sec > 60 * 60 * 2:
    #     stars += 1
    return stars


# Gives a score from 0.0 - 1.0 based on number of seconds
def star_count2(sec):
    star = 0
    star += min(sec / (60 * 4), 0.2)
    star += min(sec / (60 * 60), 0.4)
    star += sec / (60 * 60 * 10)
    return float(round(min(star, 1), 1))


def search_magic(terms, evaluate):
    return all(word in evaluate for word in terms.split())


def search_magic_any(terms, evaluate):
    return any(word in evaluate for word in terms.split())


def random_colour(saturation, luminance):

    h = round(random.random(), 2)
    colour = colorsys.hls_to_rgb(h, luminance, saturation)
    return [int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255), 255]


def hsl_to_rgb(h, s, l):
    colour = colorsys.hls_to_rgb(h, l, s)
    return [int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255), 255]

def hls_to_rgb(h, l, s):
    colour = colorsys.hls_to_rgb(h, l, s)
    return [int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255), 255]

def rgb_to_hls(r, g, b):
    return colorsys.rgb_to_hls(r / 255, g / 255, b / 255)

def rgb_add_hls(source, h=0, l=0, s=0):
    c = colorsys.rgb_to_hls(source[0] / 255, source[1] / 255, source[2] / 255)
    colour = colorsys.hls_to_rgb(c[0] + h, min(max(c[1] + l, 0), 1), min(max(c[2] + s, 0), 1))
    return [int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255), source[3]]


def is_light(colour):
    return test_lumi(colour) < 0.2

class ColourGenCache:

    def __init__(self, saturation, luminance):

        self.saturation = saturation
        self.luminance = luminance
        self.store = {}

    def get(self, key):

        if key in self.store:
            return self.store[key]

        colour = random_colour(self.saturation, self.luminance)

        self.store[key] = colour
        return colour




def folder_file_scan(path, extensions):

    match = 0
    count = sum([len(files) for r, d, files in os.walk(path)])
    for ext in extensions:

        match += len(glob.glob(path + '/**/*.' + ext.lower(), recursive=True))

    if count == 0:
        return 0

    if count < 5 and match > 0:
        return 1

    return match / count


def is_ignorable_file(string):
    for s in [
        "Thumbs.db",
        ".log",
        "desktop.ini",
        "DS_Store",
        ".nfo",
        "yric"
    ]:
        if s in string:
            return True
    return False


# Pre-compile the regular expression pattern for dates starting with the year
date_pattern = re.compile(r'\b(?:\d{2}([/. -])\d{2}\1(\d{4})|\b(\d{4})([/. -])\d{2}\4\d{2}).*')

def get_year_from_string(s):
    # Search for the pattern in the string
    match = date_pattern.search(s)

    # Extract and return the year if a match is found
    if match:
        return match.group(2) if match.group(2) else match.group(3)

    return ""


# Example usage
example_string = "Event date: 2021-12-31."
print(get_year_from_string(example_string))  # Output: "2021"

def is_music_related(string):
    for s in [
        "Folder.jpg",
        "folder.jpg",
        "Cover.jpg",
        "cover.jpg",
        "AlbumArt",
        ".m3u",
        ".m3u8",
        ".cue",
        ".CUE",
    ]:
        if s in string:
            return True
    return False


# Get ratio of given file extensions in archive
def archive_file_scan(path, extensions, launch_prefix=""):

    ext = os.path.splitext(path)[1][1:].lower()
    # print(path)
    # print(ext)
    try:
        if ext == 'rar':
            matches = 0
            count = 0
            line = launch_prefix + "unrar lb -p- " + shlex.quote(path) + " " + shlex.quote(os.path.dirname(path)) + os.sep
            result = subprocess.run(shlex.split(line), stdout=subprocess.PIPE)
            file_list = result.stdout.decode("utf-8", 'ignore').split("\n")
            # print(file_list)
            for fi in file_list:
                for ty in extensions:
                    if fi[len(ty) * -1:].lower() == ty:
                        matches += 1
                        break
                    elif is_ignorable_file(fi):
                        count -= 1
                        break
                    elif is_music_related(fi):
                        matches += 5
                count += 1
            if count > 200:
                #print("RAR archive has many files")
                #print("   --- " + path)
                return 0
            if matches == 0:
                #print("RAR archive does not appear to contain audio files")
                #print("   --- " + path)
                return 0
            if count == 0:
                #print("Archive has no files")
                #print("   --- " + path)
                return 0

        elif ext == '7z':
            matches = 0
            count = 0
            line = launch_prefix + "7z l " + shlex.quote(path) # + " " + shlex.quote(os.path.dirname(path)) + os.sep
            result = subprocess.run(shlex.split(line), stdout=subprocess.PIPE)
            file_list = result.stdout.decode("utf-8", 'ignore').split("\n")
            # print(file_list)

            for fi in file_list:

                if '....A' not in fi:
                    continue
                for ty in extensions:
                    if fi[len(ty) * -1:].lower() == ty:
                        matches += 1
                        break
                    elif is_ignorable_file(fi):
                        count -= 1
                        break
                    elif is_music_related(fi):
                        matches += 5
                count += 1

            if count > 200:
                #print("7z archive has many files")
                #print("   --- " + path)
                return 0
            if matches == 0:
                #print("7z archive does not appear to contain audio files")
                #print("   --- " + path)
                return 0
            if count == 0:
                #print("7z archive has no files")
                #print("   --- " + path)
                return 0

        elif ext == "zip":

            zip_ref = zipfile.ZipFile(path, 'r')
            matches = 0
            count = 0
            #print(zip_ref.namelist())
            for fi in zip_ref.namelist():
                for ty in extensions:
                    if fi[len(ty) * -1:].lower() == ty:
                        matches += 1
                        break
                    elif is_ignorable_file(fi):
                        count -= 1
                        break
                    elif is_music_related(fi):
                        matches += 5
                count += 1
            if count == 0:
                #print("Archive has no files")
                #print("   --- " + path)
                return 0
            if count > 300:
                #print("Zip archive has many files")
                #print("   --- " + path)
                return 0
            if matches == 0:
                #print("Zip archive does not appear to contain audio files")
                #print("   --- " + path)
                return 0
        else:
            return 0

    except:
        print("Archive test error")

        return 0

    if count == 0:
        return 0

    ratio = matches / count
    if count < 5 and matches > 0:
        ratio = 100
    return ratio


def get_folder_size(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def filename_safe(text, sub=""):
    for cha in '/\\<>:"|?*':
        text = text.replace(cha, sub)
    return text.rstrip(" .")

def filename_to_metadata(filename):

    # Remove the file extension
    name_without_extension = filename.rsplit('.', 1)[0]

    # Remove leading track numbers if present
    name_without_track_number = re.sub(r'^\d{1,2}[. -]+', '', name_without_extension)

    # Split the filename on ' - ' to separate the artist and the title
    if ' - ' in name_without_track_number:
        artist, title = name_without_track_number.split(' - ', 1)
    else:
        # If ' - ' is not present, return the whole name as title and empty string as artist
        artist = ''
        title = name_without_track_number

    return artist, title


def get_artist_strip_feat(track_object):

    artist_name = track_object.artist #.lower()
    if track_object.album_artist:
        if "feat." in artist_name or "pres." in artist_name or ", " in artist_name or "; " in artist_name or not artist_name:
            if track_object.album_artist.lower() != "va" and \
                    track_object.album_artist.lower() != "various artists":
                artist_name = track_object.album_artist
    return artist_name

def get_artist_safe(track):

    if track:
        artist = track.album_artist
        if not artist:
            artist = track.artist
        artist = filename_safe(artist)
        artist = artist.split("feat")[0]
        artist = artist.split(", ")[0]
        artist = artist.split("; ")[0]
        return artist
    return ""

def get_split_artists(track):
    if 'artists' in track.misc:
        return track.misc['artists']
    artist = track.artist.split("feat")[0].strip()
    return re.split(r'; |, |& ', artist)

def coll_rect(rect1, rect2):

    if rect1[0] + rect1[2] < rect2[0] or \
            rect1[1] + rect1[3] < rect2[1] or \
            rect1[0] > rect2[0] + rect2[2] or \
            rect1[1] > rect2[1] + rect2[3]:
        return False
    return True


def commonprefix(l):

    cp = []
    ls = [p.split('/') for p in l]
    ml = min(len(p) for p in ls)

    for i in range(ml):

        s = set(p[i] for p in ls)
        if len(s) != 1:
            break

        cp.append(s.pop())

    return '/'.join(cp)


def fader_timer(time_point, start, duration, off=True, range=255):

    if time_point < start:
        fade = range
    elif time_point < start + duration:
        p = (time_point - start) / duration
        fade = int(range - (range * p))
    else:
        fade = 0

    return fade


id3_genre_dict = {
    0: "Blues",
    1: "Classic Rock",
    2: "Country",
    3: "Dance",
    4: "Disco",
    5: "Funk",
    6: "Grunge",
    7: "Hip-Hop",
    8: "Jazz",
    9: "Metal",
    10: "New Age",
    11: "Oldies",
    12: "Other",
    13: "Pop",
    14: "R&B",
    15: "Rap",
    16: "Reggae",
    17: "Rock",
    18: "Techno",
    19: "Industrial",
    20: "Alternative",
    21: "Ska",
    22: "Death Metal",
    23: "Pranks",
    24: "Soundtrack",
    25: "Euro-Techno",
    26: "Ambient",
    27: "Trip-Hop",
    28: "Vocal",
    29: "Jazz+Funk",
    30: "Fusion",
    31: "Trance",
    32: "Classical",
    33: "Instrumental",
    34: "Acid",
    35: "House",
    36: "Game",
    37: "Sound Clip",
    38: "Gospel",
    39: "Noise",
    40: "Alternative Rock",
    41: "Bass",
    42: "Soul",
    43: "Punk",
    44: "Space",
    45: "Meditative",
    46: "Instrumental Pop",
    47: "Instrumental Rock",
    48: "Ethnic",
    49: "Gothic",
    50: "Darkwave",
    51: "Techno-Industrial",
    52: "Electronic",
    53: "Pop-Folk",
    54: "Eurodance",
    55: "Dream",
    56: "Southern Rock",
    57: "Comedy",
    58: "Cult",
    59: "Gangsta Rap",
    60: "Top 40",
    61: "Christian Rap",
    62: "Pop/Funk",
    63: "Jungle",
    64: "Native American",
    65: "Cabaret",
    66: "New Wave",
    67: "Psychedelic",
    68: "Rave",
    69: "Showtunes",
    70: "Trailer",
    71: "Lo-Fi",
    72: "Tribal",
    73: "Acid Punk",
    74: "Acid Jazz",
    75: "Polka",
    76: "Retro",
    77: "Musical",
    78: "Rock & Roll",
    79: "Hard Rock",
    80: "Folk",
    81: "Folk-Rock",
    82: "National Folk",
    83: "Swing",
    84: "Fast Fusion",
    85: "Bebob",
    86: "Latin",
    87: "Revival",
    88: "Celtic",
    89: "Bluegrass",
    90: "Avantgarde",
    91: "Gothic Rock",
    92: "Progressive Rock",
    93: "Psychedelic Rock",
    94: "Symphonic Rock",
    95: "Slow Rock",
    96: "Big Band",
    97: "Chorus",
    98: "Easy Listening",
    99: "Acoustic",
    100: "Humour",
    101: "Speech",
    102: "Chanson",
    103: "Opera",
    104: "Chamber Music",
    105: "Sonata",
    106: "Symphony",
    107: "Booty Bass",
    108: "Primus",
    109: "Porn Groove",
    110: "Satire",
    111: "Slow Jam",
    112: "Club",
    113: "Tango",
    114: "Samba",
    115: "Folklore",
    116: "Ballad",
    117: "Power Ballad",
    118: "Rhythmic Soul",
    119: "Freestyle",
    120: "Duet",
    121: "Punk Rock",
    122: "Drum Solo",
    123: "A Cappella",
    124: "Euro-House",
    125: "Dance Hall",
    126: "Goa",
    127: "Drum & Bass",
    128: "Club-House",
    129: "Hardcore",
    130: "Terror",
    131: "Indie",
    132: "BritPop",
    133: "Negerpunk",
    134: "Polsk Punk",
    135: "Beat",
    136: "Christian Gangsta Rap",
    137: "Heavy Metal",
    138: "Black Metal",
    139: "Crossover",
    140: "Contemporary Christian",
    141: "Christian Rock",
    142: "Merengue",
    143: "Salsa",
    144: "Thrash Metal",
    145: "Anime",
    146: "JPop",
    147: "Synthpop",
    148: "Abstract",
    149: "Art Rock",
    150: "Baroque",
    151: "Bhangra",
    152: "Big Beat",
    153: "Breakbeat",
    154: "Chillout",
    155: "Downtempo",
    156: "Dub",
    157: "EBM",
    158: "Eclectic",
    159: "Electro",
    160: "Electroclash",
    161: "Emo",
    162: "Experimental",
    163: "Garage",
    164: "Global",
    165: "IDM",
    166: "Illbient",
    167: "Industro-Goth",
    168: "Jam Band",
    169: "Krautrock",
    170: "Leftfield",
    171: "Lounge",
    172: "Math Rock",
    173: "New Romantic",
    174: "Nu-Breakz",
    175: "Post-Punk",
    176: "Post-Rock",
    177: "Psytrance",
    178: "Shoegaze",
    179: "Space Rock",
    180: "Trop Rock",
    181: "World Music",
    182: "Neoclassical",
    183: "Audiobook",
    184: "Audio Theatre",
    185: "Neue Deutsche Welle",
    186: "Podcast",
    187: "Indie Rock",
    188: "G-Funk",
    189: "Dubstep",
    190: "Garage Rock",
    191: "Psybient",
    192: "Unknown",
}


class FunctionStore:
    # Stores functions and arguments for calling later

    def __init__(self):

        self.items = []

    def store(self, function, args=()):

        self.items.append((function, args))

    def recall_all(self):

        while self.items:
            item = self.items.pop()
            item[0](*item[1])



def grow_rect(rect, px):
    return rect[0] - px, rect[1] - px, rect[2] + px * 2, rect[3] + px * 2

# def get_hash(f_path, mode='sha256'):
#     h = hashlib.new(mode)
#     with open(f_path, 'rb') as file:
#         data = file.read()
#     h.update(data)
#     digest = h.hexdigest()
#     return digest

def subtract_rect(base, hole):  # Return 4 rects from 1 minus 1 inner (with overlaps)

    west = base[0], base[1], hole[0], base[3]
    north = base[0], base[1], base[2], hole[1] - base[1]
    east = base[0] + hole[0] + hole[2], base[1], base[2] - (hole[0] + hole[2]), base[3]
    south = base[0], hole[1] + hole[3], base[2], base[3] - hole[3] - 2

    return west, north, east, south

genre_corrections = [
    "J-Pop",
    "J-Rock",
    "K-Pop",
    "Hip Hop",
]

genre_corrections2 = [x.lower().replace("-", "").replace(" ", "") for x in genre_corrections]

def genre_correct(text):

    parsed = text.lower().replace("-", "").replace(" ", "").strip()
    if parsed.startswith("post"):
        return ("Post-" + parsed[4:]).title()
    if parsed in genre_corrections2:
        return genre_corrections[genre_corrections2.index(parsed)]
    return text.title().strip()


def reduce_paths(paths):  # in-place remove of redundant sub-paths from list of folder paths

    paths[:] = list(set(paths))[:]  # remove duplicates

    while "" in paths:
        paths.remove("")

    while True:
        remove_path = False
        for i in reversed(range(len(paths))):
            path = paths[i].rstrip("\\/")

            for b in reversed(range(len(paths))):
                path2 = paths[b].rstrip("\\/")

                if len(path) > len(path2) and path.startswith(path2) and path[len(path2)] in ("/", "\\"):
                    del paths[i]
                    remove_path = True
                    break

            if remove_path:
                break
        if not remove_path:
            break

def fit_box(inner, outer):
    scale = min(outer[0]/inner[0], outer[1]/inner[1])
    return round(inner[0] * scale), round(inner[1] * scale)


def seconds_to_day_hms(seconds, s_day, s_days):

    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if days == 1:
        return f"{str(int(days))} {s_day}, {str(int(hours))}:{str(int(minutes))}:{str(int(seconds))}"
    else:
        return f"{str(int(days))} {s_days}, {str(int(hours))}:{str(int(minutes)).zfill(2)}:{str(int(seconds)).zfill(2)}"


def shooter(func, args=()):
    shoot = threading.Thread(target=func, args=args)
    shoot.daemon = True
    shoot.start()


year_search = re.compile(r'\d{4}')

def d_date_display(track):
    if 'rdat' in track.misc:
        return str(track.date) + " → " + track.misc["rdat"]
    return str(track.date)

def d_date_display2(track):
    if 'rdat' in track.misc:
        return str(get_year_from_string(track.date)) + " → " + get_year_from_string(track.misc["rdat"])
    return str(get_year_from_string(track.date))

def process_odat(nt, odat):
    if odat and odat != nt.date and odat != nt.date[:4] and odat != nt.date[-4:] \
            and nt.date != odat[:4] and nt.date != odat[-4:]:
        if not nt.date:
            nt.date = odat
        else:
            nt.misc["rdat"] = nt.date
            nt.date = odat

def clean_string(s):
    return s.encode('utf-8', 'surrogatepass').decode('utf-8', 'replace')

def uri_parse(s):
    if s.startswith("file://"):
        s = str(urllib.parse.unquote(s)).replace("file://", "").replace("\r", "")
    return s

mac_styles = {
    "mac": None,
    "whitesur": None,
    "vimix": None,
    "sweet": None,
    "dracula": [[248, 58, 67, 255], [239, 251, 122, 255], [74, 254, 104, 255]],
    "nordic": None,
    "juno": None
}

def sleep_timeout(condition_function, time_limit=2):
    if condition_function():
        return
    timer = Timer()
    timer.set()
    while condition_function():
        time.sleep(0.01)
        if timer.get() > time_limit:
            break
