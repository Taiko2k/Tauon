
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

import html
import time
import random
import json
import io

from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

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

    httpd = ThreadedHTTPServer(("0.0.0.0", prefs.metadata_page_port), Server)
    tauon.radio_server = httpd
    httpd.serve_forever()
    httpd.server_close()


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
    httpd = HTTPServer(("127.0.0.1", 7813), Server)
    httpd.serve_forever()
    httpd.server_close()


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

    httpd = HTTPServer(("localhost", 7812), Server)
    httpd.serve_forever()
    httpd.server_close()

