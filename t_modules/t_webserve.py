
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

from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import ThreadingMixIn

def webserve(pctl, prefs, gui, album_art_gen, install_directory, strings, tauon):


    if prefs.enable_web is False:
        return 0
    # try:
    #     from flask import Flask, send_file, abort, request, jsonify, Response
    # except:
    #     print("Failed to load Flask")
    #     gui.show_message("Web server failed to start.", "Required dependency 'flask' was not found.", 'warning')
    #     return 0

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

            path = self.path.rstrip("/")

            if path == "/radio":
                self.send_file(install_directory + "/templates/radio.html", "text/html")

            elif path == "/assets/favicon.ico":
                self.send_file(install_directory + "/assets/favicon.ico", 'image/x-icon')
            elif path == "/radio.js":
                self.send_file(install_directory + "/templates/radio.js", "application/javascript")
            elif path == "/theme.css":
                self.send_file(install_directory + "/templates/theme.css", "text/css")

            elif path == "/radio/update_radio":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                print("HIT")

                if pctl.broadcast_active:
                    track = pctl.master_library[pctl.broadcast_index]
                    if track.length > 2:
                        position = pctl.broadcast_time / track.length
                    else:
                        position = 0
                    data = {"position": position,
                            "index": track.index,
                            "port": str(prefs.broadcast_port)}
                    data = json.dumps(data).replace(" ", "").encode()
                    print(data)
                    self.wfile.write(data)

                else:
                    data = {"position": 0,
                            "index": -1}
                    data = json.dumps(data).replace(" ", "").encode()
                    print(data)
                    self.wfile.write(data)

            elif path == "/radio/getpic":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                if pctl.broadcast_active:
                    index = pctl.broadcast_index
                    track = pctl.master_library[index]

                    # Lyrics ---
                    lyrics = ""
                    if prefs.radio_page_lyrics and track.lyrics != "":
                        lyrics = html.escape(track.lyrics).replace("\r\n", "\n").replace("\r", "\n").replace("\n",
                                                                                                             "<br>")

                    try:
                        base64 = album_art_gen.get_base64(track, (300, 300)).decode()

                        data = {
                            "index": index,
                            "image": base64,
                            "title": track.title,
                            "artist": track.artist,
                            "lyrics": lyrics}

                        data = json.dumps(data).replace(" ", "").encode()
                        print(data)
                        self.wfile.write(data)
                    except:
                        # Failed getting image
                        data = {
                            "index": index,
                            "image": "None",
                            "title": track.title,
                            "artist": track.artist,
                            "lyrics": lyrics}

                        data = json.dumps(data).replace(" ", "").encode()
                        print(data)
                        self.wfile.write(data)
                else:
                    # Broadcast is not active
                    data = {
                        "index": -1,
                        "image": "None",
                        "title": "",
                        "artist": "- - Broadcast Offline -",
                        "lyrics": ""}

                    data = json.dumps(data).replace(" ", "").encode()
                    print(data)
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

    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        pass

    httpd = ThreadedHTTPServer(("0.0.0.0", prefs.metadata_page_port), Server)
    httpd.serve_forever()
    httpd.server_close()

    #app = Flask(__name__)
    #
    # def shutdown_server():
    #     func = request.environ.get('werkzeug.server.shutdown')
    #     if func is None:
    #         raise RuntimeError('Not running with the Werkzeug Server')
    #     func()
    #
    # @app.route('/shutdown', methods=['POST'])
    # def shutdown():
    #     shutdown_server()
    #     gui.web_running = False
    #     gui.show_message(strings.web_server_stopped)
    #     return 'Server shutting down...'

    # @app.route('/stream.ogg',)
    # def broadcast_stream():
    #     ip = request.remote_addr
    #
    #     def generate(ip):
    #         id = random.random()
    #         position = max(chunker.master_count - 7, 1)
    #         for header in chunker.headers:
    #             yield header
    #         while True:
    #             if not pctl.broadcast_active:
    #                 return
    #             if 1 < position < chunker.master_count:
    #                 while 1 < position < chunker.master_count:
    #                     yield chunker.chunks[position]
    #                     position += 1
    #             else:
    #                 time.sleep(0.01)
    #                 chunker.clients[id] = (ip, time.time())
    #
    #     return Response(generate(ip), mimetype="audio/ogg")

    # @app.route('/radio/')
    # def radio():
    #     print("Radio Accessed")
    #     return send_file(install_directory + "/templates/radio.html" )
    #

    # @app.route('/radio/radio.js')
    # def radio_js():
    #     return send_file(install_directory + "/templates/radio.js")
    #
    # @app.route('/radio/theme.css')
    # def radio_css():
    #     return send_file(install_directory + "/templates/theme.css")

    # @app.route('/radio/update_radio', methods=['GET'])
    # def update_radio():
    #
    #     if pctl.broadcast_active:
    #         track = pctl.master_library[pctl.broadcast_index]
    #         if track.length > 2:
    #             position = pctl.broadcast_time / track.length
    #         else:
    #             position = 0
    #         return jsonify(position=position, index=track.index, port=str(prefs.broadcast_port))
    #     else:
    #         return jsonify(position=0, index=-1)

    # @app.route('/radio/getpic', methods=['GET'])
    # def get64pic_radio():
    #
    #     if pctl.broadcast_active:
    #         index = pctl.broadcast_index
    #         track = pctl.master_library[index]
    #
    #         # Lyrics ---
    #         lyrics = ""
    #         if prefs.radio_page_lyrics and track.lyrics != "":
    #             lyrics = html.escape(track.lyrics).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
    #
    #         try:
    #             base64 = album_art_gen.get_base64(track, (300, 300)).decode()
    #
    #             return jsonify(index=index, image=base64, title=track.title, artist=track.artist, lyrics=lyrics)
    #         except:
    #             return jsonify(index=index, image="None", title=track.title, artist=track.artist, lyrics=lyrics)
    #     else:
    #         return jsonify(index=-1, image="None", title="", artist="- - Broadcast Offline -", lyrics="")


    # @app.route('/favicon.ico')
    # def favicon():
    #     return send_file(install_directory + "/assets/favicon.ico", mimetype='image/x-icon')
    #
    # if prefs.expose_web is True:
    #     if pctl.system == "linux":
    #         app.run(host='0.0.0.0', port=prefs.metadata_page_port)
    #     else:
    #         app.run(host='127.0.0.1', port=prefs.metadata_page_port)
    # else:
    #     app.run(port=prefs.metadata_page_port)


def authserve(tauon):

    class Server(BaseHTTPRequestHandler):

        def do_GET(self):

            path = self.path
            if path.startswith("/spotredir"):
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                code = path.split("code=")
                if len(code) > 1:
                    code = code[1]
                    tauon.spot_ctl.paste_code(code)
                    self.wfile.write(b"You can close this now and return to Tauon Music Box")

            else:
                self.send_response(400)
                self.end_headers()

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
                        return
                    self.wfile.write(tauon.stream_proxy.chunks[position])
                    position += 1

                else:
                    time.sleep(0.01)

    httpd = HTTPServer(("localhost", 7812), Server)
    httpd.serve_forever()
    httpd.server_close()

