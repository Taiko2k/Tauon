# Tauon Music Box - OGG Broadcasting module

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


import subprocess
import time
import io
import shlex
import fcntl, os
from t_modules.t_extra import Timer

def enc(tauon):

    pctl = tauon.pctl
    prefs = tauon.prefs

    class Enc:
        def __init__(self):
            self.encoder = None
            self.decoder = None

            self.raw_buffer = io.BytesIO()
            self.raw_buffer_size = 0

            self.output_buffer = io.BytesIO()
            self.output_buffer_size = 0

            self.temp_buffer = io.BytesIO()
            self.temp_buffer_size = 0

            self.stream_time = Timer()
            self.bytes_sent = 0

            self.track_bytes_sent = 0

            self.dry = 0

        def get_decode_command(self, target, start):
            s = start
            s, ms = divmod(s, 1)
            m, ss = divmod(s, 60)
            hh, mm = divmod(m, 60)
            ms *= 10
            t = f"{str(int(hh)).zfill(2)}:{str(int(mm)).zfill(2)}:{str(int(ss)).zfill(2)}.{str(round(ms))}"

            return ['ffmpeg', "-loglevel", "quiet", "-i", target, "-ss", t, "-acodec", "pcm_s16le", "-f", "s16le", "-ac", "2", "-ar",  # -re
                    "48000", "-"]

        def main(self):

            while True:
                if not pctl.broadcast_active and not pctl.broadcastCommandReady:
                    return
                if pctl.broadcastCommandReady:
                    command = pctl.broadcastCommand
                    pctl.playerCommand = ""
                    pctl.broadcastCommandReady = False

                    if command == "encstop":
                        # print("Stopping broadcast...")
                        pctl.broadcast_active = False
                        time.sleep(1)
                        self.decoder.terminate()
                        self.encoder.terminate()
                        self.encoder = None
                        self.decoder = None
                        self.track_bytes_sent = 0
                        self.output_buffer_size = 0
                        self.raw_buffer = io.BytesIO()
                        self.output_buffer = io.BytesIO()
                        self.temp_buffer = io.BytesIO()
                        self.dry = 0
                        self.bytes_sent = 0
                        self.stream_time.set()
                        tauon.chunker.chunks.clear()
                        tauon.chunker.headers.clear()
                        tauon.chunker.master_count = 0
                        print("Broadcast stopped")

                        pctl.broadcast_time = 0

                    if command == "encstart":
                        # print("Start broadcast...")
                        target = pctl.target_open
                        # print(f"URI = {target}")
                        pctl.broadcast_active = True
                        # print("Start encoder")
                        #cmd = shlex.split("opusenc --raw --raw-rate 48000 - -")
                        cmd = ["ffmpeg", "-loglevel", "quiet", "-f", "s16le", "-ar", "48000", "-ac", "2", "-i", "pipe:0", '-f', "opus", "-c:a", "libopus", "pipe:1"]
                        # cmd = shlex.split("oggenc --raw --raw-rate 48000 -")
                        self.encoder = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                        fcntl.fcntl(self.encoder.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

                        # print("Begin decode of file")
                        cmd = self.get_decode_command(target, pctl.b_start_time)
                        # print(cmd)
                        self.decoder = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                        time.sleep(0.1)
                        self.stream_time.force_set(6)
                        print("Broadcast started")

                    if command == "cast-next":
                        target = pctl.target_open
                        # print(f"URI = {target}")

                        self.decoder.terminate()
                        cmd = self.get_decode_command(target, 0)
                        self.decoder = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                        time.sleep(0.1)
                        # print("started next")
                        self.track_bytes_sent = 0

                    if command == "encseek":
                        target = pctl.target_open
                        start = pctl.b_start_time + pctl.broadcast_seek_position
                        # print(f"URI = {target}")
                        self.decoder.terminate()
                        cmd = self.get_decode_command(target, start)
                        self.decoder = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                        time.sleep(0.1)
                        # print("started next")
                        self.track_bytes_sent = pctl.broadcast_seek_position * (48000 * (16 / 8) * 2)

                if self.decoder:

                    pctl.broadcast_time = self.track_bytes_sent / (48000 * (16 / 8) * 2)

                    st = self.stream_time.get()
                    ss = self.bytes_sent / (48000 * (16 / 8) * 2)
                    #print((st, ss))

                    if ss < st:
                        # We owe:
                        owed_seconds = st - ss
                        owed_bytes = owed_seconds * (48000 * (16 / 8) * 2)

                        while owed_bytes > 0:
                            #print("PUMP")
                            # Pump data out of decoder
                            data = self.decoder.stdout.read(int(48000 * (16 / 8) * 2))
                            #print(data)
                            if not data:
                                self.dry += 1

                                if owed_seconds > 0.1 and self.dry > 2:
                                    #print("SILENCE")
                                    data = b"\x00" * 19200
                                else:
                                    break
                            else:
                                self.dry = 0
                            self.raw_buffer.write(data)
                            self.raw_buffer_size += len(data)
                            self.bytes_sent += len(data)
                            self.track_bytes_sent += len(data)
                            owed_bytes -= len(data)
                            break

                    if not data:
                        #print("No more decoded data...")
                        time.sleep(0.01)

                    # Push data into encoder
                    if self.raw_buffer_size > 0:
                        self.raw_buffer.seek(0)
                        data = self.raw_buffer.read(self.raw_buffer_size)
                        self.encoder.stdin.write(data)

                        # Reset the buffer
                        self.raw_buffer_size = 0
                        self.raw_buffer.seek(0)

                    # Receive encoded data
                    data = self.encoder.stdout.read()
                    if data:
                        #print("WRITE")
                        self.output_buffer.write(data)
                        self.output_buffer_size += len(data)

                    # Split OGG pages
                    if self.output_buffer_size > 12000:

                        self.output_buffer.seek(6)
                        gp = self.output_buffer.read(8)
                        gp = int.from_bytes(gp, 'big')


                        self.output_buffer.seek(26)
                        cont = self.output_buffer.read(1)
                        cont = int.from_bytes(cont, 'big')
                        #print(f"{cont} segments")
                        total = cont
                        while cont:
                            value = self.output_buffer.read(1)
                            value = int.from_bytes(value, 'big')
                            #print(f"value {value}")
                            cont -= 1
                            total += value

                        total += 27

                        self.output_buffer.seek(0, 2)
                        # self.output_buffer.seek(0)
                        # print(self.output_buffer.read(4))
                        # self.output_buffer.seek(0, 2)

                        if self.output_buffer_size >= total:
                            # Extract the first complete page
                            self.output_buffer.seek(0)
                            page = self.output_buffer.read(total)

                            # Save the page
                            if gp == 0:
                                tauon.chunker.headers.append(page)
                            else:
                                tauon.chunker.chunks[tauon.chunker.master_count] = page
                            tauon.chunker.master_count += 1
                            d = tauon.chunker.master_count - 30
                            if d > 1:
                                del tauon.chunker.chunks[d]

                            # print(f"Received page {tauon.chunker.master_count}")

                            # Reset the buffer with the remainder
                            self.temp_buffer.seek(0)
                            self.temp_buffer.write(self.output_buffer.read())
                            self.temp_buffer.seek(0)
                            del self.output_buffer
                            self.output_buffer = io.BytesIO()
                            self.output_buffer.seek(0)
                            self.output_buffer.write(self.temp_buffer.read())
                            self.output_buffer_size = self.output_buffer.tell()
                            del self.temp_buffer
                            self.temp_buffer = io.BytesIO()

    en = Enc()
    en.main()
