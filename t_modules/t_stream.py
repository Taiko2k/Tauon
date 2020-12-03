# Tauon Music Box - URL stream download and encoding module

# Copyright © 2020, Taiko2k captain(dot)gxj(at)gmail.com

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

import urllib.request
import threading
import time
import subprocess
import os
import fcntl
import datetime
import io
from t_modules.t_extra import filename_safe

class StreamEnc:

    def __init__(self, tauon):
        self.tauon = tauon
        self.download_running = False
        self.encode_running = False

        self.download_process = False
        self.abort = False

        self.s_name = ""
        self.s_bitrate = ""
        self.s_genre = ""
        self.s_description = ""
        self.s_mime = ""
        self.s_format = ""

        self.chunks = {}
        self.c = 0

    def stop(self):
        self.abort = True
        self.tauon.radiobox.loaded_url = None

    def start_download(self, url):

        self.abort = True

        while self.download_running:
            time.sleep(0.01)
        while self.encode_running:
            time.sleep(0.01)

        self.__init__(self.tauon)

        def NiceToICY(self):
            class InterceptedHTTPResponse:
                pass

            line = self.fp.readline().replace(b"ICY 200 OK\r\n", b"HTTP/1.0 200 OK\r\n")
            InterceptedSelf = InterceptedHTTPResponse()
            InterceptedSelf.fp = io.BufferedReader(io.BytesIO(line))
            InterceptedSelf.debuglevel = self.debuglevel
            InterceptedSelf._close_conn = self._close_conn
            return ORIGINAL_HTTP_CLIENT_READ_STATUS(InterceptedSelf)

        ORIGINAL_HTTP_CLIENT_READ_STATUS = urllib.request.http.client.HTTPResponse._read_status
        urllib.request.http.client.HTTPResponse._read_status = NiceToICY

        try:
            r = urllib.request.Request(url)
            r.add_header('Icy-MetaData', '1')
            print("Open URL.....")
            r = urllib.request.urlopen(r)
            print("URL opened.")

        except:
            print("Connection failed")
            return False

        self.download_process = threading.Thread(target=self.run_download, args=([r]))
        self.download_process.daemon = True
        self.download_process.start()

        self.download_running = True
        return True

    def encode(self):

        self.encode_running = True

        try:

            while self.c < 20:
                if self.abort:
                    self.encode_running = False
                    return
                time.sleep(0.05)

            ext = ".opus"
            rate = "48000"
            codec = self.tauon.prefs.radio_record_codec.upper()
            if codec == "OGG":
                ext = ".ogg"
                rate = "44100"
            if codec == "MP3":
                ext = ".mp3"
                rate = "44100"
            if codec == "FLAC":
                ext = ".flac"
                rate = "44100"

            target_file = os.path.join(self.tauon.cache_directory, "stream" + ext)
            if os.path.isfile(target_file):
                os.remove(target_file)

            cmd = ['ffmpeg', "-i", "pipe:0", "-acodec", "pcm_s16le", "-f", "s16le", "-ac", "2", "-ar", rate, "-"]

            decoder = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            fcntl.fcntl(decoder.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

            position = 0
            old_metadata = self.tauon.radiobox.song_key

            ##cmd = ["opusenc", "--raw", "--raw-rate", "48000", "-", target_file]
            cmd = ["ffmpeg", "-f", "s16le", "-ar", rate, "-ac", "2", "-i", "pipe:0", target_file]
            encoder = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

            while True:

                if self.abort:
                    decoder.terminate()
                    encoder.terminate()
                    time.sleep(0.1)
                    try:
                        decoder.kill()
                    except:
                        pass
                    try:
                        encoder.kill()
                    except:
                        pass

                    if os.path.exists(target_file):
                        if os.path.getsize(target_file) > 256000:

                            print("Save file")
                            save_file = '{:%Y-%m-%d %H-%M-%S} - '.format(datetime.datetime.now())
                            save_file += filename_safe(old_metadata)
                            save_file = save_file.strip() + ext
                            save_file = os.path.join(self.tauon.prefs.encoder_output, save_file)
                            if os.path.exists(save_file):
                                os.remove(save_file)
                            os.rename(target_file, save_file)
                        else:
                            print("Discard small file")
                            os.remove(target_file)

                    self.encode_running = False
                    return

                if old_metadata != self.tauon.radiobox.song_key:
                    if self.c < 400 and not old_metadata:
                        old_metadata = self.tauon.radiobox.song_key
                    elif not os.path.exists(target_file) or os.path.getsize(target_file) < 100000:
                        old_metadata = self.tauon.radiobox.song_key
                    else:
                        print("Split and save file")
                        encoder.stdin.close()
                        try:
                            encoder.wait(timeout=4)
                        except:
                            pass
                        try:
                            encoder.kill()
                        except:
                            pass
                        if os.path.exists(target_file):
                            if os.path.getsize(target_file) > 256000:
                                save_file = '{:%Y-%m-%d %H-%M-%S} - '.format(datetime.datetime.now())
                                save_file += filename_safe(old_metadata)
                                save_file = save_file.strip() + ext
                                save_file = os.path.join(self.tauon.prefs.encoder_output, save_file)
                                if os.path.exists(save_file):
                                    os.remove(save_file)
                                if not os.path.exists(self.tauon.prefs.encoder_output):
                                    os.makedirs(self.tauon.prefs.encoder_output)
                                os.rename(target_file, save_file)
                            else:
                                print("Discard small file")
                                os.remove(target_file)
                        encoder = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

                raw_audio = decoder.stdout.read(1000000)
                if raw_audio:
                    encoder.stdin.write(raw_audio)

                if position < self.c:
                    chunk = self.chunks[position]
                    position += 1
                    decoder.stdin.write(chunk)
                else:
                    time.sleep(0.005)

        except:
            print("Encoder thread crashed!")
            #raise
            self.encode_running = False
            return

    def run_download(self, r):

        h = r.info()

        self.s_name = h.get("icy-name")
        metaint = h.get("icy-metaint")
        self.s_bitrate = h.get("icy-br")
        self.s_genre = h.get("icy-genre")
        self.s_description = h.get("icy-description")
        self.s_mime = h.get("Content-Type")

        print(self.s_mime)
        if self.s_mime == "audio/mpeg":
            self.s_format = "MP3"
        if self.s_mime == "audio/ogg":
            self.s_format = "OGG"
        if self.s_mime == "audio/aac":
            self.s_format = "AAC"
        if self.s_mime == "audio/aacp":
            self.s_format = "AAC+"

        test_done = 0

        icy = False
        m_remain = 0
        m = 0
        if metaint and int(metaint) > 0:
            m = int(metaint)
            m_remain = m
            icy = True

        maybe = b""

        if self.tauon.prefs.auto_rec:
            self.download_process = threading.Thread(target=self.encode)
            self.download_process.daemon = True
            self.download_process.start()

        try:
            while True:

                chunk = r.read(256)

                if self.abort:
                    r.close()
                    print("Abort stream connection")
                    self.download_running = False
                    return

                if chunk:
                    if not icy or m_remain > len(chunk):
                        # We're sure its data Its data, send it on
                        self.chunks[self.c] = chunk
                        # Delete old data
                        d = self.c - (30000)
                        if d in self.chunks:
                            del self.chunks[d]

                        test_done += len(chunk)
                        self.c += 1
                        m_remain -= len(chunk)

                        continue
                    else:
                        # It may contain the metadata block, put it aside
                        maybe += chunk

                # Try to extract ICY tag
                if maybe:
                    data1 = maybe[:m_remain]
                    inter = maybe[m_remain:]

                    # Read the metadata length byte
                    if inter:
                        special = inter[0]
                        follow = special * 16

                        if len(inter) < follow + 2:
                            # Not enough data yet
                            continue

                        text = inter[1:follow + 1]
                        data2 = inter[follow + 1:]

                        self.chunks[self.c] = data1 + data2
                        # Delete old data
                        d = self.c - 512
                        if d in self.chunks:
                            del self.chunks[d]

                        self.c += 1

                        test_done += len(data1)
                        test_done = 0

                        m_remain = m - len(data2)
                        test_done += len(data2)
                        maybe = b""

                        try:
                            meta = text.decode().rstrip("\x00")
                            for tag in meta.split(";"):
                                if '=' in tag:
                                    a, b = tag.split('=')
                                    if a == 'StreamTitle':
                                        #print("Set meta")
                                        self.tauon.pctl.tag_meta = b.rstrip("'").lstrip("'")
                                        break
                        except:
                            r.close()
                            self.download_running = False
                            self.tauon.gui.show_message("Data malformation detected. Stream aborted.", mode='error')
                            raise
        except:
            print("Stream download thread crashed!")
            self.download_running = False
            return