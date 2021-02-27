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
import shutil
from t_modules.t_extra import *
from hsaudiotag import auto


def player4(tauon):

    pctl = tauon.pctl
    gui = tauon.gui
    prefs = tauon.prefs

    print("Start PHAzOR backend...")

    # Get output device names
    if len(prefs.phazor_devices) < 2:
        try:
            import pulsectl
            pulse = pulsectl.Pulse('Tauon Music Box')
            sink_list = pulse.sink_list()
            for sink in sink_list:
                prefs.phazor_devices[sink.description] = sink.name
            pulse.close()
        except:
            print("Warning: Missing dependency Pulsectl")

    state = 0
    player_timer = Timer()
    loaded_track = None
    fade_time = 400

    aud = ctypes.cdll.LoadLibrary(pctl.install_directory + "/lib/libphazor.so")
    aud.init()
    aud.set_volume(int(pctl.player_volume))

    def calc_rg(track):

        if prefs.replay_gain == 0 and prefs.replay_preamp == 0:
            pctl.active_replaygain = 0
            return 0

        g = 0
        p = 1

        if track is not None:
            tg = track.misc.get("replaygain_track_gain")
            tp = track.misc.get("replaygain_track_peak")
            ag = track.misc.get("replaygain_album_gain")
            ap = track.misc.get("replaygain_album_peak")

            if prefs.replay_gain > 0:
                if (prefs.replay_gain == 1 and tg is not None) or (prefs.replay_gain == 2 and ag is None and tg is not None):
                    g = tg
                    if tp is not None:
                        p = tp
                elif ag is not None:
                    g = ag
                    if ap is not None:
                        p = ap

        # print("Replay gain")
        # print("GAIN: " + str(g))
        # print("PEAK: " + str(p))
        # print("FINAL: " + str(min(10 ** ((g + prefs.replay_preamp) / 20), 1 / p)))
        pctl.active_replaygain = g
        return min(10 ** ((g + prefs.replay_preamp) / 20), 1 / p)

    audio_cache = tauon.cache_directory + "/network-audio1"

    class DownloadObject:
        def __init__(self, track):
            self.timestamp = time.time()
            self.status = "prep"
            self.tauon_id = track.index
            self.filepath = audio_cache
            if not os.path.exists(self.filepath):
                os.makedirs(self.filepath)
            self.filepath += "/" + str(self.tauon_id) + ".mp3"
            if os.path.exists(self.filepath):
                os.remove(self.filepath)
            self.network_url = ""
            self.params = ""
            self.part = None
            self.cancel = False
            self.downloaded_duration = -1

        def download(self):
            print("Start download")
            try:
                self.part = requests.get(self.network_url, stream=True, params=self.params)

                if self.part.status_code == 404:
                    gui.show_message("Server: File not found", mode="error")
                    self.status = "error"
                    return
                elif self.part.status_code != 200:
                    gui.show_message("Server Error", mode="error")
                    self.status = "error"
                    return

            except:
                gui.show_message("Could not connect to server", mode="error")
                self.status = "error"
                return

            bitrate = 0
            a = 0
            z = 0

            with open(self.filepath, 'wb') as f:
                for chunk in self.part.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        a += 1
                        if a == 300:  # kilobyes~
                            self.status = "ready"
                        if self.cancel is True:
                            self.part.close()
                            self.status = "failed"
                            print("Abort download")
                            return

                        f.write(chunk)

                        z += 1
                        if z == 60:
                            z = 0
                            if bitrate == 0:
                                audio = auto.File(self.filepath)
                                bitrate = audio.bitrate
                            if bitrate > 0:
                                gui.update += 1
                                self.downloaded_duration = a * 1024 / (bitrate / 8) / 1000
                                #pctl.download_time = a * 1024 / (bitrate / 8) / 1000

            #pctl.download_time = -1

            self.status = "done"
            print("Download done")

    class DownloadManager:

        def __init__(self):
            self.items = {}
            if os.path.exists(audio_cache):
                shutil.rmtree(audio_cache)

        def get_filepath(self, track):
            return self.items[track.index].filepath

        def _prune(self):

            items = list(self.items.values())
            items.sort(key=lambda x: x.timestamp)
            for item in items:
                if item.status in ("ready", "prep"):
                    item.cancel = True
                elif item.status in ("failed", "error"):
                    print("prune failed item")
                    if os.path.exists(item.filepath):
                        os.remove(item.filepath)
                    del self.items[item.tauon_id]

            items = list(self.items.values())
            items.sort(key=lambda x: x.timestamp)
            items = items[:-25]
            for item in items:
                print("prune old item")
                if os.path.exists(item.filepath):
                    os.remove(item.filepath)
                del self.items[item.tauon_id]


        def request(self, track, t=0, whole=False):

            if track.index in self.items:
                item = self.items[track.index]

                if item.status == "ready":
                    if whole:
                        return "wait"
                    if t == 0:
                        return "go"
                    elif item.downloaded_duration > t + 20:
                        return "go"
                    elif t:
                        return "wait"

                if item.status == "done":
                    item.timestamp = time.time()
                    print("Use cached audio")
                    return "go"
                if item.status == "prep":
                    return "wait"
                if item.status == "error":
                    del self.items[track.index]
                    return "error"
                if item.status == "failed":
                    del self.items[track.index]

                if t:
                    print(item.status)
                    return "wait"

            self._prune()

            item = DownloadObject(track)

            try:
                item.network_url, item.params = pctl.get_url(target_object)
            except:
                return "error"

            self.items[track.index] = item
            shoot_dl = threading.Thread(target=item.download)
            shoot_dl.daemon = True
            shoot_dl.start()

            return "wait"

    dm = DownloadManager()


    class URLDownloader:

        def __init__(self):
            self.active_url = ""
            self.part = None
            self.dl_ready = False
            self.dl_running = False
            self.save_temp = ""
            self.alt = "b"

        def download_part(self, url, target, params, item):

            self.dl_running = True

            try:
                self.part = requests.get(url, stream=True, params=params)

                if self.part.status_code == 404:
                    gui.show_message("Server: File not found", mode="error")
                    self.dl_ready = "failure"
                    return
                elif self.part.status_code != 200:
                    gui.show_message("Server Error", mode="error")
                    self.dl_ready = "failure"
                    return

            except:
                gui.show_message("Could not connect to server", mode="error")
                self.dl_ready = "failure"
                return

            bitrate = 0
            a = 0
            z = 0

            if os.path.isfile(target):
                os.remove(target)

            with open(target, 'wb') as f:
                for chunk in self.part.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        a += 1
                        if a == 300:  # kilobyes~
                            self.dl_ready = True
                        if url != self.active_url:
                            self.part.close()
                            print("Abort download")
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
            self.dl_running = False

    dl = URLDownloader()

    def set_config():
        aud.config_set_dev_buffer(prefs.device_buffer)

        if prefs.phazor_device_selected != "Default":
            if prefs.phazor_device_selected in prefs.phazor_devices.values():
                aud.config_set_dev_name(prefs.phazor_device_selected.encode())
            else:
                print("Warning: Selected audio output is now missing. Defaulting to default.")
                aud.config_set_dev_name(None)
        else:
            aud.config_set_dev_name(None)

    set_config()

    while True:

        time.sleep(0.016)
        # Level meter
        if state == 1 and gui.vis == 1:
            amp = aud.get_level_peak_l()
            l = (amp / 32767) * 12
            amp = aud.get_level_peak_r()
            r = (amp / 32767) * 12

            tauon.level_train.append((0, l, r))
            gui.level_update = True

        # Command processing
        if pctl.playerCommandReady:

            command = pctl.playerCommand
            subcommand = pctl.playerSubCommand
            pctl.playerSubCommand = ""
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
                    aud.start(pctl.url.encode(), 0, 0, ctypes.c_float(calc_rg(None)))
                    state = 3
                    player_timer.hit()

            if command == "open":
                if state == 2:
                    aud.set_volume(int(pctl.player_volume))

                pctl.download_time = 0
                target_object = pctl.target_object
                target_path = target_object.fullpath

                if (tauon.spot_ctl.playing or tauon.spot_ctl.coasting) and not target_object.file_ext == "SPTY":
                    tauon.spot_ctl.control("stop")

                if target_object.is_network:

                    dl.dl_running = False

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

                    target_path = None
                    while True:
                        s = dm.request(target_object)
                        if s == "go":
                            target_path = dm.get_filepath(target_object)
                            break
                        elif s == "wait":
                            if pctl.playerCommandReady and pctl.playerCommand == "open":
                                break
                            #print("wait")
                            time.sleep(0.01)
                        else:
                            print("Abort for error")
                            break
                    if target_path is None:
                        continue
                    #
                    # url = ""
                    # params = None
                    #
                    # try:
                    #     url, params = pctl.get_url(target_object)
                    # except:
                    #     gui.show_message("Failed to query url", "Bad login? Server offline?", mode='info')
                    #     pctl.stop()
                    #     return
                    #
                    # if url is None:
                    #     print(gui.show_message("Failed to query url", "Bad login? Server offline?", mode='info'))
                    #     pctl.stop()
                    #     return
                    #
                    # dl.save_temp = prefs.cache_directory + "/" + dl.alt + "-temp.mp3"
                    #
                    # if dl.alt == 'a':
                    #     dl.alt = 'b'
                    # else:
                    #     dl.alt = 'a'
                    #
                    # dl.active_url = url
                    # dl.dl_ready = False
                    #
                    # shoot_dl = threading.Thread(target=dl.download_part, args=([url, dl.save_temp, params, target_object]))
                    # shoot_dl.daemon = True
                    # shoot_dl.start()
                    #
                    # while not dl.dl_ready:
                    #     time.sleep(0.02)
                    # target_path = dl.save_temp
                    #
                    # if dl.dl_ready == "failure":
                    #     state = 0
                    #     aud.stop()
                    #     continue
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
                elif not target_object.found:
                    pctl.reset_missing_flags()

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

                    if loaded_track.is_network:
                        length = loaded_track.length
                        remain = length - position

                fade = 0
                if state == 1 and length and position and not pctl.start_time_target and not pctl.jump_time and \
                        loaded_track and 0 < remain < 5.5 and not loaded_track.is_cue and subcommand != "now":

                    print("Transition gapless mode")

                    aud.next(target_path.encode(), int(pctl.start_time_target + pctl.jump_time) * 1000, ctypes.c_float(calc_rg(target_object)))
                    pctl.playing_time = pctl.jump_time

                    if remain > 0:
                        time.sleep(0.01)
                        remain -= 0.01
                        if pctl.playerCommandReady and pctl.playerCommand == "open":
                            break

                    loaded_track = target_object

                else:
                    if state == 1 and prefs.use_jump_crossfade:
                        fade = 1
                    aud.start(target_path.encode(), int(pctl.start_time_target + pctl.jump_time) * 1000, fade, ctypes.c_float(calc_rg(target_object)))
                    loaded_track = target_object
                    pctl.playing_time = pctl.jump_time
                    if pctl.jump_time:
                        while aud.get_result() == 0:
                            time.sleep(0.01)
                        aud.set_position_ms(int(pctl.jump_time * 1000))

                    # Restart track is failed to load (for some network tracks) (broken with gapless loading)
                    while True:
                        r = aud.get_result()
                        if r == 1:
                            break
                        if r == 2:
                            if loaded_track.is_network:
                                gui.buffering = True
                                while dm.request(loaded_track, whole=True) == "wait":
                                    time.sleep(0.05)
                                    if pctl.playerCommandReady:
                                        break
                                print("Retry start file")
                                aud.start(target_path.encode(), int(pctl.start_time_target + pctl.jump_time) * 1000,
                                          fade, ctypes.c_float(calc_rg(target_object)))
                                gui.buffering = False
                                player_timer.set()
                                break
                            else:
                                aud.stop()
                                gui.show_message("Error loading track", mode="warning")
                        time.sleep(0.05)

                    state = 1

                player_timer.set()
                pctl.jump_time = 0
                if loaded_track.length == 0 or loaded_track.file_ext.lower() in tauon.mod_formats:
                    i = 0
                    t = 0
                    while t == 0:
                        time.sleep(0.3)
                        t = aud.get_length_ms() / 1000
                        i += 1
                        if i > 9:
                            break
                    loaded_track.length = t
                    if loaded_track.length != 0:
                        pctl.playing_length = loaded_track.length
                        gui.pl_update += 1

            if command == "seek":
                if tauon.spot_ctl.coasting or tauon.spot_ctl.playing:
                    tauon.spot_ctl.control("seek", int(pctl.new_time * 1000))
                    pctl.playing_time = pctl.new_time
                elif state > 0:

                    if loaded_track.is_network:  # and loaded_track.fullpath.endswith(".ogg"):

                        was_playing = False
                        if state == 1:
                            was_playing = True
                            aud.pause()

                        abort = False
                        while True:
                            s = dm.request(loaded_track, t=pctl.new_time)
                            if s == "go":
                                break

                            if pctl.playerCommandReady:
                                abort = True
                                break

                            if s == "wait":
                                gui.buffering = True
                                print("Can't seek yet")
                                time.sleep(0.1)
                                continue
                            abort = True
                            break
                        gui.buffering = False
                        if abort:
                            continue

                        # The vorbis decoder doesn't like appended files
                        aud.start(dm.get_filepath(loaded_track).encode(), int(pctl.new_time + pctl.start_time_target) * 1000, 0, ctypes.c_float(calc_rg(loaded_track)))
                        while aud.get_result() == 0:
                            time.sleep(0.01)
                        aud.set_position_ms(int(pctl.new_time * 1000))
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
                # print("length: " + str(length))
                # print("position: " + str(position))
                # print("We are %s from end" % str(remain))
                time.sleep(3)
                command = "stop"

            if command == "stop":

                if prefs.use_pause_fade and state != 3:
                    if pctl.player_volume > 5:
                        speed = fade_time / (int(pctl.player_volume) / 100)
                    else:
                        speed = fade_time / (5 / 100)

                    aud.ramp_volume(0, int(speed))
                    time.sleep((fade_time + 100) / 1000)

                state = 0
                pctl.playing_time = 0
                aud.stop()
                time.sleep(0.1)
                aud.set_volume(int(pctl.player_volume))

                if subcommand == "return":
                    pctl.playerSubCommand = "stopped"
                    #pctl.playerCommandReady = True

            if command == "pauseon":
                if prefs.use_pause_fade:
                    if pctl.player_volume > 5:
                        speed = fade_time / (int(pctl.player_volume) / 100)
                    else:
                        speed = fade_time / (5 / 100)

                    aud.ramp_volume(0, int(speed))
                    time.sleep((fade_time + 100) / 1000)
                aud.pause()
                state = 2

            if command == "pauseoff":
                if prefs.use_pause_fade:
                    if pctl.player_volume > 5:
                        speed = fade_time / (int(pctl.player_volume) / 100)
                    else:
                        speed = fade_time / (5 / 100)

                    aud.ramp_volume(int(pctl.player_volume), int(speed))
                aud.resume()
                player_timer.set()
                state = 1

            if command == "unload":

                if prefs.use_pause_fade:
                    if pctl.player_volume > 5:
                        speed = fade_time / (int(pctl.player_volume) / 100)
                    else:
                        speed = fade_time / (5 / 100)

                    aud.ramp_volume(0, int(speed))
                    time.sleep((fade_time + 100) / 1000)

                aud.stop()
                aud.shutdown()

                if os.path.exists(audio_cache):
                    shutil.rmtree(audio_cache)

                pctl.playerCommand = "done"
                pctl.playerCommandReady = True
                break

        else:

            pctl.spot_test_progress()

            if state == 3:
                pctl.radio_progress()
                add_time = player_timer.hit()
                pctl.playing_time += add_time
                pctl.decode_time = pctl.playing_time

                buffering = aud.is_buffering()
                if gui.buffering != buffering:
                    gui.buffering = buffering
                    gui.update += 1


            if state == 1:

                if loaded_track.is_network and pctl.playing_time < 7:
                    if aud.get_result() == 2:
                        print("STALL, RETRY")
                        time.sleep(0.5)
                        pctl.playerCommandReady = True
                        pctl.playerCommand = "open"

                add_time = player_timer.hit()
                if add_time > 2:
                    add_time = 2
                if add_time < 0:
                    add_time = 0

                pctl.playing_time += add_time

                t = aud.get_position_ms() / 1000

                pctl.total_playtime += add_time

                if t:
                    pctl.decode_time = t - loaded_track.start_time
                else:
                    pctl.decode_time = pctl.playing_time

                #print((pctl.playing_time, pctl.decode_time))

                if pctl.playing_time < 3 and pctl.a_time < 3:
                    pctl.a_time = pctl.playing_time
                else:
                    pctl.a_time += add_time

                tauon.lfm_scrobbler.update(add_time)

                if len(pctl.track_queue) > 0 and 2 > add_time > 0:
                    tauon.star_store.add(pctl.track_queue[pctl.queue_step], add_time)
                if pctl.playing_time > 1:
                    pctl.test_progress()

