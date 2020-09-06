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
from t_modules.t_extra import *

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

    while True:

        time.sleep(0.016)

        # Level meter
        if state == 1 and gui.vis == 1:
            amp = aud.get_level_peak_l()
            l = (amp / 32767) * 12
            amp = aud.get_level_peak_r()
            r = (amp / 32767) * 12

            tauon.level_train.append((time.time() + 0.12, r, l))
            gui.level_update = True

        # Command processing
        if pctl.playerCommandReady:

            command = pctl.playerCommand
            pctl.playerCommandReady = False

            if command == "open":

                if pctl.target_object.file_ext not in ("MP3", "FLAC", "OGG", "OPUS"):
                    state = 0
                    aud.stop()
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

                if state == 1 and length and position and not pctl.start_time_target and not pctl.jump_time and \
                        loaded_track and 0 < remain < 5.5 and not loaded_track.is_cue:

                    print("Gapless mode")

                    aud.next(pctl.target_object.fullpath.encode(), int(pctl.start_time_target + pctl.jump_time) * 1000)
                    pctl.playing_time = 0

                    if remain > 0:
                        time.sleep(remain)

                    loaded_track = pctl.target_object

                else:
                    aud.start(pctl.target_object.fullpath.encode(), int(pctl.start_time_target + pctl.jump_time) * 1000)
                    loaded_track = pctl.target_object
                    pctl.playing_time = 0
                    state = 1

                player_timer.set()
                pctl.jump_time = 0

            if command == "seek":
                aud.seek(int((pctl.new_time + pctl.start_time_target) * 1000), prefs.pa_fast_seek)  # ms, fast_seek
                pctl.playing_time = pctl.new_time
                pctl.decode_time = pctl.playing_time
            if command == "volume":
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

            if state == 1:

                add_time = player_timer.hit()
                if add_time > 2:
                    print("Add time error!")
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

