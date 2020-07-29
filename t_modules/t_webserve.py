
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
import requests

def webserve(pctl, prefs, gui, album_art_gen, install_directory, strings):

    if prefs.enable_web is False:
        return 0
    try:
        from flask import Flask, redirect, send_file, abort, request, jsonify, render_template, Response, stream_with_context
    except:
        print("Failed to load Flask")
        gui.show_message("Web server failed to start.", "Required dependency 'flask' was not found.", 'warning')
        return 0

    gui.web_running = True
    app = Flask(__name__)

    def shutdown_server():
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

    @app.route('/shutdown', methods=['POST'])
    def shutdown():
        shutdown_server()
        gui.web_running = False
        gui.show_message(strings.web_server_stopped)
        return 'Server shutting down...'

    @app.route('/radio/')
    def radio():
        print("Radio Accessed")
        return send_file(install_directory + "/templates/radio.html" )


    @app.route('/radio/radio.js')
    def radio_js():
        return send_file(install_directory + "/templates/radio.js")

    @app.route('/radio/jquery.js')
    def radio_jq():
        return send_file(install_directory + "/templates/jquery.js")

    @app.route('/radio/theme.css')
    def radio_css():
        return send_file(install_directory + "/templates/theme.css")

    @app.route('/radio/update_radio', methods=['GET'])
    def update_radio():

        if pctl.broadcast_active:
            track = pctl.master_library[pctl.broadcast_index]
            if track.length > 2:
                position = pctl.broadcast_time / track.length
            else:
                position = 0
            return jsonify(position=position, index=track.index, port=str(prefs.broadcast_port))
        else:
            return jsonify(position=0, index=-1)

    @app.route('/radio/getpic', methods=['GET'])
    def get64pic_radio():

        if pctl.broadcast_active:
            index = pctl.broadcast_index
            track = pctl.master_library[index]

            # Lyrics ---
            lyrics = ""
            if prefs.radio_page_lyrics and track.lyrics != "":
                lyrics = html.escape(track.lyrics).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")

            try:
                base64 = album_art_gen.get_base64(track, (300, 300)).decode()

                return jsonify(index=index, image=base64, title=track.title, artist=track.artist, lyrics=lyrics)
            except:
                return jsonify(index=index, image="None", title=track.title, artist=track.artist, lyrics=lyrics)
        else:
            return jsonify(index=-1, image="None", title="", artist="- - Broadcast Offline -", lyrics="")


    @app.route('/favicon.ico')
    def favicon():
        return send_file(install_directory + "/assets/favicon.ico", mimetype='image/x-icon')

    if prefs.expose_web is True:
        if pctl.system == "linux":
            app.run(host='0.0.0.0', port=prefs.metadata_page_port)
        else:
            app.run(host='127.0.0.1', port=prefs.metadata_page_port)
    else:
        app.run(port=prefs.metadata_page_port)


def authserve(tauon):

    from flask import Flask, abort, request

    app = Flask(__name__)

    @app.route('/spotredir')
    def favicon():
        code = request.args.get('code')
        if code:
            tauon.spot_ctl.paste_code(code)
            return "You can close this now and return to Tauon Music Box"
        abort(400)

    app.run(port=7811)
