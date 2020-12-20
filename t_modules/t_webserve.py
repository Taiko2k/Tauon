
# Tauon Music Box - Web interface module

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
import fcntl
import html
import time
import random
import json
import io
import os
import subprocess
from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from t_modules.t_extra import Timer

def webserve(pctl, prefs, gui, album_art_gen, install_directory, strings, tauon):

    if prefs.enable_web is False:
        return 0

    def get_broadcast_track():
        if pctl.broadcast_active is False:
            return None, None
        delay = 6
        tr = None
        t = time.time()
        for item in reversed(pctl.broadcast_update_train):
            if 20 > t - item[2] > delay:
                tr = item
                break
        if tr is None:
            return None, None
        else:
            return tr[0], tr[1]


    chunker = tauon.chunker
    gui.web_running = True

    class Server(BaseHTTPRequestHandler):

        def send_file(self, path, mime):
            self.send_response(200)
            self.send_header("Content-type", mime)
            self.end_headers()

            with open(path, "rb") as f:
                self.wfile.write(f.read())

        def do_GET(self):

            path = self.path

            # print(self.headers)

            if path == "/radio/":
                self.send_response(302)
                self.send_header('Location', "/radio")
                self.end_headers()

            elif path == "/radio":
                self.send_file(install_directory + "/templates/radio.html", "text/html")
            elif path == "/favicon.ico":
                self.send_file(install_directory + "/assets/favicon.ico", 'image/x-icon')
            elif path == "/radio/radio.js":
                self.send_file(install_directory + "/templates/radio.js", "application/javascript")
            elif path == "/radio/theme.css":
                self.send_file(install_directory + "/templates/theme.css", "text/css")
            elif path == "/radio/logo-bg.png":
                self.send_file(install_directory + "/templates/logo-bg.png", 'image/png')

            elif path == "/radio/update_radio":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                track_id, p = get_broadcast_track()
                if track_id is not None:

                    track = pctl.master_library[track_id]
                    if track.length > 2:
                        position = p / track.length
                    else:
                        position = 0
                    data = {"position": position,
                            "index": track.index,
                            "port": str(prefs.broadcast_port)}
                    data = json.dumps(data).replace(" ", "").encode()
                    self.wfile.write(data)

                else:
                    data = {"position": 0,
                            "index": -1}
                    data = json.dumps(data).replace(" ", "").encode()
                    self.wfile.write(data)

            elif path == "/radio/getpic":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                track_id, p = get_broadcast_track()

                if track_id is not None:

                    track = pctl.master_library[track_id]

                    # Lyrics ---
                    lyrics = ""

                    if prefs.radio_page_lyrics:
                        lyrics = tauon.synced_to_static_lyrics.get(track)
                        lyrics = html.escape(lyrics).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
                    try:
                        base64 = album_art_gen.get_base64(track, (300, 300)).decode()

                        data = {
                            "index": track_id,
                            "image": base64,
                            "title": track.title,
                            "artist": track.artist,
                            "album": track.album,
                            "lyrics": lyrics}

                        data = json.dumps(data).encode()
                        self.wfile.write(data)
                    except:
                        # Failed getting image
                        data = {
                            "index": track_id,
                            "image": "None",
                            "title": track.title,
                            "artist": track.artist,
                            "album": track.album,
                            "lyrics": lyrics}

                        data = json.dumps(data).encode()
                        self.wfile.write(data)
                else:
                    # Broadcast is not active
                    data = {
                        "index": -1,
                        "image": "None",
                        "title": "",
                        "artist": "- - Broadcast Offline - -",
                        "album": "",
                        "lyrics": ""}

                    data = json.dumps(data).encode()
                    self.wfile.write(data)

            elif path == "/stream.ogg":

                ip = self.client_address[0]

                self.send_response(200)
                self.send_header("Content-type", "audio/ogg")
                self.end_headers()

                position = max(chunker.master_count - 7, 1)
                id = random.random()

                for header in chunker.headers:
                    self.wfile.write(header)
                while True:
                    if not pctl.broadcast_active:
                        return
                    if 1 < position < chunker.master_count:
                        while 1 < position < chunker.master_count:
                            if not pctl.broadcast_active:
                                return
                            self.wfile.write(chunker.chunks[position])
                            position += 1
                    else:
                        time.sleep(0.01)
                        chunker.clients[id] = (ip, time.time())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"404 Not found")

    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        pass

    try:
        httpd = ThreadedHTTPServer(("0.0.0.0", prefs.metadata_page_port), Server)
        tauon.radio_server = httpd
        httpd.serve_forever()
        httpd.server_close()
    except OSError:
        print("Not starting radio page server, already running?")


def webserve2(pctl, prefs, gui, album_art_gen, install_directory, strings, tauon):

    play_timer = Timer()

    class Server(BaseHTTPRequestHandler):

        def run_command(self, callback):
            self.send_response(200)
            #self.send_header("Content-type", "application/json")
            self.end_headers()
            callback()
            self.wfile.write(b"OK")

        def parse_trail(self, text):

            params = {}
            both = text.split("?")
            levels = both[0].split("/")
            if len(both) > 1:
                pairs = both[2].split("&")
                for p in pairs:
                    aa, bb = p.split("=")
                    params[aa] = bb

            return levels, params

        def get_track(self, track_position, playlist_index=None, track=None, album_id=-1):
            if track is None:
                if playlist_index is None:
                    playlist = pctl.multi_playlist[pctl.active_playlist_playing][2]
                else:
                    playlist = pctl.multi_playlist[playlist_index][2]
                track_id = playlist[track_position]
                track = pctl.g(track_id)

            data = {}
            data["title"] = track.title
            data["artist"] = track.artist
            data["album"] = track.album
            data["album_artist"] = track.album_artist
            if not track.album_artist:
                data["album_artist"] = track.artist
            data["duration"] = int(track.length * 1000)
            data["id"] = track.index
            data["position"] = track_position
            data["album_id"] = album_id
            data["track_number"] = str(track.track_number).lstrip("0")

            return data

        def send_file(self, path, mime):

            range_req = False
            start = 0
            end = 0

            if "Range" in self.headers:
                range_req = True
                b = self.headers["Range"].split("=")[1]
                start, end = b.split("-")
                start = int(start)

            with open(path, "rb") as f:

                f.seek(0, 2)
                length = f.tell()
                f.seek(0, 0)

                l = str(length)

                remain = length - start

                if range_req:
                    self.send_response(206)
                    self.send_header("Content-type", mime)
                    self.send_header("Content-Range", f"bytes={start}-/{l}")
                    self.send_header("Content-Length", str(remain))
                    f.seek(start)

                else:
                    self.send_response(200)
                    self.send_header("Content-type", mime)
                    self.send_header("Content-Length", l)

                self.end_headers()

                while True:
                    data = f.read(5000)
                    if not data:
                        break
                    self.wfile.write(data)

        def do_GET(self):

            path = self.path

            if path.startswith("/api1/pic/small/"):
                value = path[16:]
                if value.isalnum() and int(value) in pctl.master_library:
                    track = pctl.g(int(value))
                    raw = album_art_gen.save_thumb(track, (75, 75), "")
                    if raw:
                        self.send_response(200)
                        self.send_header("Content-type", "image/jpg")
                        self.end_headers()
                        self.wfile.write(raw.read())
                    else:
                        self.send_response(404)
                        self.end_headers()
                        self.wfile.write(b"No image found")

                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"Invalid parameter")

            if path.startswith("/api1/pic/medium/"):
                value = path[17:]
                if value.isalnum() and int(value) in pctl.master_library:
                    track = pctl.g(int(value))
                    raw = album_art_gen.save_thumb(track, (1000, 1000), "")
                    if raw:
                        self.send_response(200)
                        self.send_header("Content-type", "image/jpg")
                        self.end_headers()
                        self.wfile.write(raw.read())
                    else:
                        self.send_response(404)
                        self.end_headers()
                        self.wfile.write(b"No image found")

                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"Invalid parameter")

            # elif path.startswith("/api1/stream/"):
            #     param = path[13:]
            #
            #     if param.isdigit() and int(param) in pctl.master_library:
            #         track = pctl.master_library[int(param)]
            #         mime = "audio/mpeg"
            #         #mime = "audio/ogg"
            #         self.send_response(200)
            #         self.send_header("Content-type", mime)
            #         self.end_headers()
            #
            #         cmd = ["ffmpeg", "-i", track.fullpath, "-c:a", "libopus", "-f", "ogg", "-"]
            #         #cmd = ["ffmpeg", "-i", track.fullpath, "-c:a", "libvorbis", "-f", "ogg", "-"]
            #         #cmd = ["ffmpeg", "-i", track.fullpath, "-c:a", "libmp3lame", "-f", "mp3", "-"]
            #         encoder = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            #         while True:
            #             data = encoder.stdout.read(1024)
            #             if data:
            #                 self.wfile.write(data)
            elif path.startswith("/api1/playinghit/"):
                param = path[17:]
                if param.isdigit() and int(param) in pctl.master_library:
                    t = play_timer.hit()
                    if 0 < t < 5:
                        tauon.star_store.add(int(param), t)

                self.send_response(200)
                self.send_header("Content-type", "image/jpg")
                self.end_headers()
                self.wfile.write(b"OK")

            elif path.startswith("/api1/file/"):
                param = path[11:]

                #print(self.headers)
                play_timer.hit()

                if param.isdigit() and int(param) in pctl.master_library:
                    track = pctl.master_library[int(param)]
                    mime = "audio/mpeg"
                    if track.file_ext == "FLAC":
                        mime = "audio/flac"
                    if track.file_ext == "OGG" or track.file_ext == "OPUS" or track.file_ext == "OGA":
                        mime = "audio/ogg"
                    if track.file_ext == "M4A":
                        mime = "audio/mp4"
                    self.send_file(track.fullpath, mime)

            elif path.startswith("/api1/start/"):

                levels, _ = self.parse_trail(path)
                if len(levels) == 5:
                    playlist = levels[3]
                    position = levels[4]
                    if playlist.isdigit() and position.isdigit():
                        position = int(position)
                        playlist = int(playlist)
                        pl = tauon.id_to_pl(int(playlist))
                        if pl is not None and pl < len(pctl.multi_playlist):
                            playlist = pctl.multi_playlist[pl][2]
                            if position < len(playlist):
                                tauon.switch_playlist(pl, cycle=False, quiet=True)
                                pctl.jump(playlist[position], position)

                self.send_response(200)
                self.send_header("Content-type", "image/jpg")
                self.end_headers()
                self.wfile.write(b"OK")

            elif path == "/api1/play":
                self.run_command(tauon.pctl.play)
            elif path == "/api1/pause":
                self.run_command(tauon.pctl.pause_only)
            elif path == "/api1/next":
                self.run_command(tauon.pctl.advance)
            elif path == "/api1/back":
                self.run_command(tauon.pctl.back)
            elif path == "/api1/shuffle":
                self.run_command(tauon.toggle_random)
            elif path == "/api1/repeat":
                self.run_command(tauon.toggle_repeat)
            elif path == "/api1/version":
                data = {"version": 1}
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                data = json.dumps(data).encode()
                self.wfile.write(data)

            elif path == "/api1/playlists":

                l = []
                for item in pctl.multi_playlist:
                    p = {}
                    p["name"] = item[0]
                    p["id"] = str(item[6])
                    p["count"] = len(item[2])
                    l.append(p)
                data = {"playlists": l}
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                data = json.dumps(data).encode()
                self.wfile.write(data)

            elif path.startswith("/api1/albumtracks/"):
                # Get tracks that appear in an album /albumtracks/plid/albumid
                levels, _ = self.parse_trail(path)
                l = []
                if len(levels) == 5 and levels[3].isdigit() and levels[4].isdigit():
                    pl = tauon.id_to_pl(int(levels[3]))
                    if pl is not None:
                        _, album, _ = tauon.get_album_info(int(levels[4]), pl)
                        # print(album)
                        for p in album:
                            l.append(self.get_track(p, pl, album_id=int(levels[4])))

                data = {"tracks": l}
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                data = json.dumps(data).encode()
                self.wfile.write(data)

            elif path.startswith("/api1/trackposition/"):
                # get track /trackposition/plid/playlistposition
                levels, _ = self.parse_trail(path)
                if len(levels) == 5 and levels[3].isdigit() and levels[4].isdigit():
                    pl = tauon.id_to_pl(int(levels[3]))
                    if pl:  # todo handle None

                        data = self.get_track(int(levels[4]), pl)

                        playlist = pctl.multi_playlist[pl][2]
                        p = int(levels[4])
                        track = pctl.g(playlist[p])
                        while True:
                            if p < 0 or pctl.g(playlist[p]).parent_folder_path != track.parent_folder_path:
                                p += 1
                                break
                            p -= 1
                        data["album_id"] = p

                        self.send_response(200)
                        self.send_header("Content-type", "application/json")
                        self.end_headers()
                        data = json.dumps(data).encode()
                        self.wfile.write(data)

            elif path.startswith("/api1/seek1k/"):
                key = path[13:]
                if key.isdigit():
                    pctl.seek_decimal(int(key) / 1000)

                self.send_response(200)
                self.send_header("Content-type", "image/jpg")
                self.end_headers()
                self.wfile.write(b"OK")

            elif path.startswith("/api1/tracklist/"):
                # Return all tracks in a playlist /tracklist/plid
                key = path[16:]
                l = []
                if key.isdigit():
                    pl = tauon.id_to_pl(int(key))
                    if pl is not None and pl < len(pctl.multi_playlist):
                        playlist = pctl.multi_playlist[pl][2]
                        parent = ""
                        album_id = 0
                        for i, id in enumerate(playlist):
                            tr = pctl.g(id)
                            if i == 0:
                                parent = tr.parent_folder_path
                            elif parent != tr.parent_folder_path:
                                parent = tr.parent_folder_path
                                album_id = i

                            l.append(self.get_track(i, pl, album_id=album_id))

                data = {"tracks": l}
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                data = json.dumps(data).encode()
                self.wfile.write(data)

            elif path.startswith("/api1/albums/"):
                # Returns lists of tracks that are start of albums /albums/plid
                key = path[13:]
                l = []
                if key.isdigit():
                    pl = tauon.id_to_pl(int(key))
                    if pl is not None:
                        dex = tauon.reload_albums(True, pl)
                        # print(dex)
                        for a in dex:
                            l.append(self.get_track(a, pl, album_id=a))

                data = {"albums": l}
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                data = json.dumps(data).encode()
                self.wfile.write(data)

            elif path == "/api1/status":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                data = {
                    "status": "stopped",
                    "shuffle": pctl.random_mode == True,
                    "repeat": pctl.repeat_mode == True,
                    "progress": 0,
                    "playlist": str(tauon.get_playing_playlist_id()),
                    "playlist_length": len(pctl.multi_playlist[pctl.active_playlist_playing][2])
                }
                if pctl.playing_state == 1:
                    data["status"] = "playing"
                if pctl.playing_state == 2:
                    data["status"] = "paused"
                track = pctl.playing_object()
                if track:
                    data["id"] = track.index
                    data["title"] = track.title
                    data["artist"] = track.artist
                    data["album"] = track.album
                    data["progress"] = int(round(pctl.playing_time * 1000))
                    data["track"] = self.get_track(0, 0, track)

                p = pctl.playlist_playing_position
                data["position"] = p
                data["album_id"] = 0
                playlist = pctl.playing_playlist()

                if p < len(playlist):
                    while True:
                        if p < 0 or pctl.g(playlist[p]).parent_folder_path != track.parent_folder_path:
                            p += 1
                            break
                        p -= 1
                    data["album_id"] = p

                data = json.dumps(data).encode()
                self.wfile.write(data)

            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"404 Not found")

    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        pass

    try:
        httpd = ThreadedHTTPServer(("0.0.0.0", 7814), Server)
        httpd.serve_forever()
        httpd.server_close()
    except OSError:
        print("Not starting web api server, already running?")


def controller(tauon):
    import base64
    class Server(BaseHTTPRequestHandler):
        def do_GET(self):

            path = self.path
            if path == "/playpause/":
                if tauon.pctl.playing_state == 0:
                    tauon.pctl.play()
                else:
                    tauon.pctl.pause()
            if path == "/play/":
                tauon.pctl.play()
            if path == "/pause/":
                tauon.pctl.pause_only()
            if path == "/stop/":
                tauon.pctl.stop()
            if path == "/next/":
                tauon.pctl.advance()
            if path == "/previous/":
                tauon.pctl.back()
            if path == "/shuffle/":
                tauon.toggle_random()
            if path == "/repeat/":
                tauon.toggle_repeat()
            if path.startswith("/open/"):
                rest = path[6:]
                path = base64.urlsafe_b64decode(rest.encode()).decode()
                tauon.open_uri(path)

            self.send_response(200)
            self.end_headers()

    print("Start controller server")
    try:
        httpd = HTTPServer(("127.0.0.1", 7813), Server)
        httpd.serve_forever()
        httpd.server_close()
    except OSError:
        print("Not starting controller server, already running?")


def authserve(tauon):

    class Server(BaseHTTPRequestHandler):

        def do_GET(self):
            code = ""
            path = self.path
            if path.startswith("/spotredir"):
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                code = path.split("code=")
                if len(code) > 1:
                    code = code[1]
                    self.wfile.write(b"You can close this now and return to Tauon Music Box")

            else:
                self.send_response(400)
                self.end_headers()

            if code:
                tauon.spot_ctl.paste_code(code)

    httpd = HTTPServer(("127.0.0.1", 7811), Server)
    httpd.serve_forever()
    httpd.server_close()

import struct
class VorbisMonitor():

    def __init__(self):

        self.tauon = None
        self.reset()
        self.enable = True
        self.synced = False
        self.buffer = io.BytesIO()
        self.tries = 0

    def reset(self, tries=0):
        self.enable = True
        self.synced = False
        self.buffer = io.BytesIO()
        self.tries = tries

    def input(self, data):

        if not self.enable:
            return

        b = self.buffer
        b.seek(0, io.SEEK_END)
        b.write(data)

        # Check theres enough data to decode header
        b.seek(0, io.SEEK_END)
        l = b.tell()
        if l < 128:
            print("Not enough data to parse vorbis")
            return

        # Get page length
        b.seek(0, io.SEEK_SET)
        ogg = b.read(4)

        if not ogg == b"OggS":
            f = data.find(b"Oggs")
            self.reset(self.tries)
            if f > -1:
                print("Ogg stream synced")
                data = data[f:]
                b = self.buffer
                b.write(data)
            else:
                self.tries += 1
                if self.tries > 100:
                    print("Giving up looking for OGG pages")
                    self.enable = False
                return

            # self.enable = False
            # return

        b.seek(0, io.SEEK_SET)
        header = struct.unpack('<4sBBqIIiB', b.read(27))
        segs = struct.unpack('B' * header[7], b.read(header[7]))

        length = 0
        for s in segs:
            length += s

        length += 27 + header[7]

        if l > length:
            h = b.read(7)
            # print(h)
            if h == b"\x03vorbis" or h == b"OpusTag":
                if h == b"OpusTag":
                    b.seek(1, io.SEEK_CUR)

                vendor_length = int.from_bytes(b.read(4), byteorder='little')
                vendor = int.from_bytes(b.read(vendor_length), byteorder='little')
                comment_list_length = int.from_bytes(b.read(4), byteorder='little')

                found_tags = {}
                for i in range(comment_list_length):
                    comment_length = int.from_bytes(b.read(4), byteorder='little')
                    comment = b.read(comment_length)

                    key, value = comment.decode().split("=", 1)

                    if key == "title":
                        found_tags["title"] = value
                    if key == "artist":
                        found_tags["artist"] = value
                    if key == "year":
                        found_tags["year"] = value
                    if key == "album":
                        found_tags["album"] = value

                line = ""
                if "title" in found_tags:
                    line += found_tags["title"]
                    if "artist" in found_tags:
                        line = found_tags["artist"] + " - " + line

                if self.tauon.radiobox.loaded_url not in self.tauon.radiobox.websocket_source_urls:
                    self.tauon.pctl.found_tags = found_tags
                    self.tauon.pctl.tag_meta = line

                print("Found vorbis comment")
                print(line)

            # Consume page from buffer
            b.seek(length, io.SEEK_SET)
            new = io.BytesIO()
            new.write(b.read())
            self.buffer = new


vb = VorbisMonitor()

def stream_proxy(tauon):

    class Server(BaseHTTPRequestHandler):

        def do_GET(self):

            self.send_response(200)
            self.send_header("Content-type", "audio/ogg")
            self.end_headers()

            position = 0
            vb.reset()
            vb.tauon = tauon

            while True:
                if not tauon.stream_proxy.download_running:
                    return

                while position < tauon.stream_proxy.c:
                    if position not in tauon.stream_proxy.chunks:
                        print("The buffer was deleted too soon!")
                        return

                    self.wfile.write(tauon.stream_proxy.chunks[position])

                    if tauon.prefs.backend == 4:
                        vb.input(tauon.stream_proxy.chunks[position])

                    position += 1

                else:
                    time.sleep(0.01)

    httpd = HTTPServer(("127.0.0.1", 7812), Server)
    httpd.serve_forever()
    httpd.server_close()

