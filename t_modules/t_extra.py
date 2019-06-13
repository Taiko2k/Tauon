
# Tauon Music Box - Misc Functions Module

# Copyright © 2015-2019, Taiko2k captain(dot)gxj(at)gmail.com

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



# Test given proximity between two 2d points to given square
def point_proximity_test(a, b, p):
    return abs(a[0] - b[0]) < p and abs(a[1] - b[1]) < p


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

# Creates a string from number of bytes to X MB/kB etc
def get_filesize_string(file_bytes):
    if file_bytes < 1000:
        line = locale.str(file_bytes) + " Bytes"
    elif file_bytes < 1000000:
        file_kb = round(file_bytes / 1000, 2)
        line = locale.str(file_kb) + " KB"
    else:
        file_mb = round(file_bytes / 1000000, 2)
        line = locale.str(file_mb) + " MB"
    return line


# Estimates the perceived luminance of a colour
def test_lumi(c1):
    return 1 - (0.299 * c1[0] + 0.587 * c1[1] + 0.114 * c1[2]) / 255


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


# Converts string containing colour in format x,x,x,x(optional) to list
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


# Checks if the numbers in a list are the same
def checkEqual(lst):
    return not lst or lst.count(lst[0]) == len(lst)


# Gives a score from 0-7 based on number of seconds
def star_count(sec, dur):
    stars = 0
    if sec / dur > 0.95:
        stars += 1
    if sec > 60 * 15:
        stars += 1
    if sec > 60 * 30:
        stars += 1
    if sec > 60 * 60:
        stars += 1
    if sec > 60 * 60 * 2:
        stars += 1
    if sec > 60 * 60 * 5:
        stars += 1
    if sec > 60 * 60 * 10:
        stars += 1
    return stars


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


def hls_mod_add(source, h=0, l=0, s=0):
    c = colorsys.rgb_to_hls(source[0] / 255, source[1] / 255, source[2] / 255)
    colour = colorsys.hls_to_rgb(c[0] + h, min(max(c[1] + l, 0), 1), min(max(c[2] + l, 0), 1))
    return [int(colour[0] * 255), int(colour[1] * 255), int(colour[2] * 255), source[3]]


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
    print(path)
    print(ext)
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
                print("RAR archive has many files")
                print("   --- " + path)
                return 0
            if matches == 0:
                print("RAR archive does not appear to contain audio files")
                print("   --- " + path)
                return 0
            if count == 0:
                print("Archive has no files")
                print("   --- " + path)
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
                print("7z archive has many files")
                print("   --- " + path)
                return 0
            if matches == 0:
                print("7z archive does not appear to contain audio files")
                print("   --- " + path)
                return 0
            if count == 0:
                print("7z archive has no files")
                print("   --- " + path)
                return 0

        elif ext == "zip":

            zip_ref = zipfile.ZipFile(path, 'r')
            matches = 0
            count = 0
            print(zip_ref.namelist())
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
                print("Archive has no files")
                print("   --- " + path)
                return 0
            if count > 300:
                print("Zip archive has many files")
                print("   --- " + path)
                return 0
            if matches == 0:
                print("Zip archive does not appear to contain audio files")
                print("   --- " + path)
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


def get_artist_strip_feat(track_object):
    artist_name = track_object.artist
    if track_object.album_artist:
        if "feat." in artist_name.lower() or ", " in artist_name or "; " in artist_name or not artist_name:
            if track_object.album_artist.lower() != "va" and \
                    track_object.album_artist.lower() != "various artists":
                artist_name = track_object.album_artist
    return artist_name


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

