
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
            elif path == "/assets/album-icon.png":
                self.send_file(install_directory + "/templates/theme.css", "text/css")
            elif path == "/assets/album-icon-small.png":
                self.send_file(install_directory + "/assets/album-icon-small.png", 'image/x-icon')
            elif path == "/assets/volume-down.png":
                self.send_file(install_directory + "/assets/volume-down.png", 'image/x-icon')
            elif path == "/assets/volume-up.png":
                self.send_file(install_directory + "/assets/volume-up.png", 'image/x-icon')


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
                        "artist": "- - Broadcast Offline -",
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


def stream_proxy(tauon):

    class Server(BaseHTTPRequestHandler):

        def do_GET(self):

            self.send_response(200)
            self.send_header("Content-type", "audio/ogg")
            self.end_headers()

            position = 0

            while True:
                if not tauon.stream_proxy.download_running:
                    return

                while position < tauon.stream_proxy.c:
                    if position not in tauon.stream_proxy.chunks:
                        print("The buffer was deleted too soon!")
                        return
                    self.wfile.write(tauon.stream_proxy.chunks[position])

                    position += 1

                else:
                    time.sleep(0.01)

    httpd = HTTPServer(("localhost", 7812), Server)
    httpd.serve_forever()
    httpd.server_close()

