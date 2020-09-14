# Tauon Music Box - Phazor audio backend module

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


import ctypes
import time
import requests
import threading
from t_modules.t_extra import *
from hsaudiotag import auto

# todo - normal file into cue track


def player4(tauon):

    pctl = tauon.pctl
    gui = tauon.gui
    prefs = tauon.prefs

    print("Start PHAzOR backend...")

    state = 0
    player_timer = Timer()
    loaded_track = None
    fade_time = 400

    aud = ctypes.cdll.LoadLibrary(pctl.install_directory + "/lib/libphazor.so")
    aud.init()
    aud.set_volume(int(pctl.player_volume))


    class URLDownloader:

        def __init__(self):
            self.active_url = ""
            self.part = None
            self.dl_ready = False
            self.save_temp = ""
            self.alt = "b"

        def download_part(self, url, target, params):

            try:
                self.part = requests.get(url, stream=True, params=params)
            except:
                gui.show_message("Could not connect to server", mode="error")
                self.dl_ready = "Failure"
                return

            bitrate = 0
            a = 0
            z = 0

            with open(target, 'wb') as f:
                for chunk in self.part.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        a += 1
                        if a == 300:  # kilobyes~
                            self.dl_ready = True
                        if url != self.url:
                            self.part.close()
                            break

                        f.write(chunk)

                        z += 1
                        if z == 60:
                            z = 0
                            if bitrate == 0:
                                audio = auto.File(target)
                                bitrate = audio.bitrate
                            if bitrate > 0:
                                gui.update += 1
                                pctl.download_time = a * 1024 / (bitrate / 8) / 1000

            pctl.download_time = -1

            self.dl_ready = True

    dl = URLDownloader()

    def set_config():
        aud.config_set_dev_buffer(prefs.device_buffer)

    set_config()

    while True:

        time.sleep(0.016)

        # Level meter
        if state == 1 and gui.vis == 1:
            amp = aud.get_level_peak_l()
            l = (amp / 32767) * 12
            amp = aud.get_level_peak_r()
            r = (amp / 32767) * 12

            tauon.level_train.append((0, r, l))
            gui.level_update = True

        # Command processing
        if pctl.playerCommandReady:

            command = pctl.playerCommand
            pctl.playerCommandReady = False

            if command == "reload":
                set_config()

            if command == "url":
                pctl.download_time = 0
                w = 0
                while len(tauon.stream_proxy.chunks) < 200:
                    time.sleep(0.1)
                    w += 1
                    if w > 100:
                        print("Taking too long!")
                        tauon.stream_proxy.stop()
                        pctl.playerCommand = 'stop'
                        pctl.playerCommandReady = True
                        break
                else:
                    aud.start(pctl.url.encode(), 0)
                    state = 3
                    player_timer.hit()

            if command == "open":

                pctl.download_time = 0
                target_object = pctl.target_object
                target_path = target_object.fullpath

                if (tauon.spot_ctl.playing or tauon.spot_ctl.coasting) and not target_object.file_ext == "SPTY":
                    tauon.spot_ctl.control("stop")

                if target_object.is_network:

                    if target_object.file_ext == "SPTY":
                        tauon.level_train.clear()
                        if state > 0:
                            aud.stop()
                        state = 0
                        try:
                            tauon.spot_ctl.play_target(target_object.url_key)
                        except:
                            print("Failed to start Spotify track")
                            pctl.playerCommand = "stop"
                            pctl.playerCommandReady = True
                        continue

                    url = ""
                    params = None

                    try:
                        url, params = pctl.get_url(target_object)
                    except:
                        gui.show_message("Failed to query url", "Bad login? Server offline?", mode='info')
                        pctl.stop()
                        return

                    if url is None:
                        print(gui.show_message("Failed to query url", "Bad login? Server offline?", mode='info'))
                        pctl.stop()
                        return

                    dl.save_temp = prefs.cache_directory + "/" + dl.alt + "-temp.mp3"

                    if dl.alt == 'a':
                        dl.alt = 'b'
                    else:
                        dl.alt = 'a'

                    dl.url = url
                    dl.dl_ready = False

                    shoot_dl = threading.Thread(target=dl.download_part, args=([url, dl.save_temp, params]))
                    shoot_dl.daemon = True
                    shoot_dl.start()

                    while not dl.dl_ready:
                        time.sleep(0.02)
                    target_path = dl.save_temp

                # if not target_object.is_network and target_object.file_ext not in ("MP3", "FLAC", "OGG", "OPUS"):
                #     state = 0
                #     aud.stop()
                #     continue

                if not os.path.isfile(target_path):
                    target_object.found = False
                    if not target_object.is_network:
                        pctl.playing_state = 0
                        pctl.jump_time = 0
                        pctl.advance(inplace=True, play=True)
                    continue

                length = 0
                remain = 0
                position = 0
                if state == 1 and not pctl.start_time_target and not pctl.jump_time and \
                        loaded_track:

                    length = aud.get_length_ms() / 1000
                    position = aud.get_position_ms() / 1000
                    remain = length - position

                    # print("length: " + str(length))
                    # print("position: " + str(position))
                    # print("We are %s from end" % str(remain))

                if target_object.is_network and position:
                    length = target_object.length
                    remain = length - position

                if state == 1 and length and position and not pctl.start_time_target and not pctl.jump_time and \
                        loaded_track and 0 < remain < 5.5 and not loaded_track.is_cue:

                    print("Transition gapless mode")

                    aud.next(pctl.target_object.fullpath.encode(), int(pctl.start_time_target + pctl.jump_time) * 1000)
                    pctl.playing_time = 0

                    if remain > 0:
                        time.sleep(remain)

                    loaded_track = target_object

                else:
                    aud.start(target_path.encode(), int(pctl.start_time_target + pctl.jump_time) * 1000)
                    loaded_track = target_object
                    pctl.playing_time = 0
                    state = 1

                player_timer.set()
                pctl.jump_time = 0

            if command == "seek":
                if tauon.spot_ctl.coasting or tauon.spot_ctl.playing:
                    tauon.spot_ctl.control("seek", int(pctl.new_time * 1000))
                    pctl.playing_time = pctl.new_time
                elif state > 0:

                    if loaded_track.is_network and loaded_track.fullpath.endswith(".ogg"):
                        # The vorbis decoder doesn't like appended files
                        aud.start(dl.save_temp.encode(), int(pctl.new_time + pctl.start_time_target) * 1000)
                    else:
                        aud.seek(int((pctl.new_time + pctl.start_time_target) * 1000), prefs.pa_fast_seek)
                    pctl.playing_time = pctl.new_time
                pctl.decode_time = pctl.playing_time
            if command == "volume":
                if tauon.spot_ctl.coasting or tauon.spot_ctl.playing:
                    tauon.spot_ctl.control("volume", int(pctl.player_volume))
                else:
                    aud.ramp_volume(int(pctl.player_volume), 750)
            if command == "runstop":
                length = aud.get_length_ms() / 1000
                position = aud.get_position_ms() / 1000
                remain = length - position
                print("length: " + str(length))
                print("position: " + str(position))
                print("We are %s from end" % str(remain))
                time.sleep(2.5)
                command = "stop"
            if command == "stop":

                if pctl.player_volume > 5:
                    speed = fade_time / (int(pctl.player_volume) / 100)
                else:
                    speed = fade_time / (5 / 100)

                aud.ramp_volume(0, int(speed))
                time.sleep((fade_time + 10) / 1000)

                state = 0
                pctl.playing_time = 0
                aud.stop()
                aud.set_volume(int(pctl.player_volume))

                if pctl.playerSubCommand == "return":
                    pctl.playerSubCommand = "stopped"
                    pctl.playerCommandReady = True

            if command == "pauseon":

                if pctl.player_volume > 5:
                    speed = fade_time / (int(pctl.player_volume) / 100)
                else:
                    speed = fade_time / (5 / 100)

                aud.ramp_volume(0, int(speed))
                time.sleep((fade_time + 10) / 1000)
                aud.pause()
                state = 2

            if command == "pauseoff":
                if pctl.player_volume > 5:
                    speed = fade_time / (int(pctl.player_volume) / 100)
                else:
                    speed = fade_time / (5 / 100)

                aud.ramp_volume(int(pctl.player_volume), int(speed))
                aud.resume()
                player_timer.set()
                state = 1

            if command == "unload":
                aud.stop()
                aud.shutdown()
                pctl.playerCommand = "done"
                pctl.playerCommandReady = True
                break

        else:

            if state == 3:
                pctl.radio_progress()
                add_time = player_timer.hit()
                pctl.playing_time += add_time
                pctl.decode_time = pctl.playing_time

            if state == 1:

                add_time = player_timer.hit()
                if add_time > 2:
                    add_time = 2
                if add_time < 0:
                    add_time = 0

                pctl.playing_time += add_time
                pctl.decode_time = pctl.playing_time
                pctl.total_playtime += add_time
                tauon.lfm_scrobbler.update(add_time)
                if len(pctl.track_queue) > 0 and 2 > add_time > 0:
                    tauon.star_store.add(pctl.track_queue[pctl.queue_step], add_time)
                if pctl.playing_time > 1:
                    pctl.test_progress()

