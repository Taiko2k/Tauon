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
from ctypes import *
import os.path
import time
import requests
from requests.models import PreparedRequest
import threading
import shutil
from t_modules.t_extra import *
import mutagen
import hashlib

def player4(tauon):

    pctl = tauon.pctl
    gui = tauon.gui
    prefs = tauon.prefs

    print("Start PHAzOR backend...")

    # # Get output device names
    # if len(prefs.phazor_devices) < 2 and not tauon.macos and not tauon.msys:
    #     try:
    #         import pulsectl
    #         pulse = pulsectl.Pulse('Tauon Music Box')
    #         sink_list = pulse.sink_list()
    #         for sink in sink_list:
    #             prefs.phazor_devices[sink.description] = sink.name
    #         pulse.close()
    #     except:
    #         print("Warning: Missing dependency Pulsectl")

    state = 0
    player_timer = Timer()
    loaded_track = None
    fade_time = 400

    aud = ctypes.cdll.LoadLibrary(pctl.install_directory + "/lib/libphazor.so")
    aud.init()

    aud.get_device.restype = ctypes.c_char_p

    aud.feed_raw.argtypes = (ctypes.c_int,ctypes.c_char_p)
    aud.feed_raw.restype = None
    tauon.aud = aud
    aud.set_volume(int(pctl.player_volume))

    bins1 = (ctypes.c_float * 24)()
    bins2 = (ctypes.c_float * 45)()

    aud.get_level_peak_l.restype = ctypes.c_float
    aud.get_level_peak_r.restype = ctypes.c_float

    active_timer = Timer()

    def scan_device():
        n = aud.scan_devices()
        devices = ["Default"]
        if n:
            for d in range(n):
                devices.append(aud.get_device(d).decode())
        prefs.phazor_devices = devices
        if prefs.phazor_device_selected not in devices:
            prefs.phazor_device_selected = devices[0]

    scan_device()

    class FFRun:
        def __init__(self):
            self.decoder = None

        def close(self):
            if self.decoder:
                self.decoder.terminate()
            self.decoder = None

        def start(self, uri, start_ms, samplerate):
            self.close()
            path = tauon.get_ffmpeg()
            if not path:
                tauon.test_ffmpeg()
                return 1
            cmd = [path]
            cmd += ["-loglevel", "quiet"]
            if start_ms > 0:
                cmd += ["-ss", f"{start_ms}ms"]
            cmd += ["-i", uri.decode(), "-acodec", "pcm_s16le", "-f", "s16le", "-ac", "2", "-ar", f"{samplerate}", "-"]
            startupinfo = None
            if tauon.msys:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            try:
                self.decoder = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, startupinfo=startupinfo)
            except:
                print("Error starting ffmpeg")
                return 1
            return 0

        def read(self, buffer: POINTER(c_char), max):
            if self.decoder:
                data = self.decoder.stdout.read(max)
                p = cast(buffer, POINTER(c_char * max))
                p.contents.value = data
                return len(data)
            return 0

    ff_run = FFRun()
    FUNCTYPE = CFUNCTYPE
    if tauon.msys:
        FUNCTYPE = WINFUNCTYPE
    start_callback = FUNCTYPE(c_int, c_char_p, c_int, c_int)(ff_run.start)
    read_callback = FUNCTYPE(c_int, c_void_p, c_int)(ff_run.read)
    close_callback = FUNCTYPE(c_void_p)(ff_run.close)
    aud.set_callbacks(start_callback, read_callback, close_callback)

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
                if prefs.replay_gain == 3 and tg is not None and ag is not None:
                    gens = pctl.gen_codes.get(tauon.pl_to_id(pctl.active_playlist_playing))
                    if pctl.random_mode or (gens and ("st" in gens or "rt" in gens or "r" in gens)):
                        g = tg
                        if tp is not None:
                            p = tp
                    else:
                        g = ag
                        if ap is not None:
                            p = ap
                elif (prefs.replay_gain == 1 and tg is not None) or (prefs.replay_gain == 2 and ag is None and tg is not None):
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
        if p == 0:
            print("Warning: detected replay gain peak of 0")
            return 1
        pctl.active_replaygain = g
        return min(10 ** ((g + prefs.replay_preamp) / 20), 1 / p)

    audio_cache = tauon.cache_directory + "/network-audio1"
    audio_cache2 = tauon.cache_directory + "/audio-cache"

    class Cachement:
        def __init__(self):
            self.direc = audio_cache2
            if prefs.tmp_cache and os.path.isdir("/tmp"):
                self.direc = "/tmp/TauonMusicBox/audio-cache"
            if not os.path.exists(self.direc):
                os.makedirs(self.direc)
            self.list = prefs.cache_list
            self.files = os.listdir(self.direc)
            self.get_now = None
            self.running = False
            self.ready = None
            self.error = None

        def get_key(self, track):
            if track.is_network:
                return hashlib.sha256((str(track.index) + track.url_key).encode()).hexdigest()
            else:
                return hashlib.sha256(track.fullpath.encode()).hexdigest()

        def get_file_cached_only(self, track):
            key = self.get_key(track)
            if key in self.files:
                path = os.path.join(self.direc, key)
                if os.path.isfile(path):
                    return path
            return None

        def get_file(self, track):
            # 0: file ready
            # 1: file downloading
            # 2: file not found
            if self.error == track:
                return 2, None

            key = self.get_key(track)
            path = os.path.join(self.direc, key)

            if self.running and self.get_now == track:
                return 1, path

            if key in self.files:
                if os.path.isfile(path):
                    tauon.console.print("got cached file")
                    self.files.remove(key)
                    self.files.append(key)  # bump to top of list
                    self.get_now = None
                    if not self.running:
                        shoot_dl = threading.Thread(target=self.run)
                        shoot_dl.daemon = True
                        shoot_dl.start()
                    return 0, path

            for codec in (".opus", ".ogg", ".flac", ".mp3"):
                idea = os.path.join(prefs.encoder_output, tauon.encode_folder_name(track), tauon.encode_track_name(track)) + codec
                if os.path.isfile(idea):
                    tauon.console.print("Found transcode")
                    return 0, idea

            self.get_now = track
            if not self.running:
                shoot_dl = threading.Thread(target=self.run)
                shoot_dl.daemon = True
                shoot_dl.start()
            return 1, path

        def run(self):
            self.running = True

            now = self.get_now
            self.get_now = None
            if now is not None:
                error = self.dl_file(now)
                if error:
                    self.error = now
                    self.running = False
                    return

            if self.get_now is None:
                i = 0
                while i < 10:
                    time.sleep(0.1)
                    i += 1
                    if self.get_now is not None:
                        self.running = False
                        return
                tauon.console.print("Precache next track")
                next = pctl.advance(dry=True)
                if next is not None:
                    self.dl_file(pctl.g(next))

            self.trim_cache()
            self.running = False
            return

        def trim_cache(self):
            # Remove untracked items
            for item in self.files:
                t = os.path.join(self.direc, item)
                if os.path.isfile(t) and item not in self.list:
                    os.remove(t)

            # Check total size
            limit = prefs.cache_limit
            if prefs.tmp_cache:
                limit = 10
            while True:
                s = 0
                for item in list(self.list):
                    t = os.path.join(self.direc, item)
                    if not os.path.exists(t):
                        self.list.remove(item)
                        continue
                    s += os.path.getsize(t)
                # Removed oldest items if over limit
                if s > limit * 1000 * 1000 and len(self.list) > 3:
                    t = os.path.join(self.direc, self.list[0])
                    os.remove(t)
                    del self.list[0]
                else:
                    break

        def dl_file(self, track):
            key = self.get_key(track)
            path = os.path.join(self.direc, key)
            if os.path.exists(path):
                if not os.path.isfile(path):
                    return 1
                if key in self.list:
                    return 0
                else:
                    os.remove(path)
            if not track.is_network:
                if not os.path.isfile(track.fullpath):
                    self.error = track
                    self.running = False
                    return 1

                tauon.console.print("start transfer")
                timer = Timer()
                target = open(path, "wb")
                source = open(track.fullpath, "rb")
                while True:
                    try:
                        data = source.read(128000)
                    except:
                        break
                    if len(data) > 0:
                        tauon.console.print(f"Caching file @ {int(len(data) / timer.hit() / 1000)} kbps")
                    else:
                        break
                    target.write(data)
                target.close()
                source.close()
                print("got file")
                self.files.append(key)
                self.list.append(key)
                return 0

            else:
                try:
                    tauon.console.print("Download file")
                    network_url, params = pctl.get_url(track)
                    part = requests.get(network_url, stream=True, params=params, timeout=(3, 10))

                    if part.status_code == 404:
                        gui.show_message("Server: File not found", mode="error")
                        self.error = track
                        return 1
                    elif part.status_code != 200:
                        gui.show_message("Server Error", mode="error")
                        self.error = track
                        return 1

                except:
                    gui.show_message("Could not connect to server", mode="error")
                    self.error = track
                    return 1

                a = 0
                length = 0
                cl = part.headers.get("Content-Length")
                if cl:
                    length = int(cl)
                    gui.buffering_text = "0%"


                timer = Timer()
                try:
                    with open(path, 'wb') as f:
                        for chunk in part.iter_content(chunk_size=1024):
                            if chunk:  # filter out keep-alive new chunks
                                a += 1
                                if a == 1500:  # kilobyes~
                                    self.ready = track
                                if a % 32 == 0:
                                    #time.sleep(0.03)
                                    tauon.console.print(f"Downloading file @ {round(32 / timer.hit())} kbps")
                                    if length:
                                        gui.update += 1
                                        if True: #a > 2000:
                                            gui.buffering_text = str(round(a * 1000 / length * 100)) + "%"
                                        else:
                                            gui.buffering_text = str(round(a / 2100 * 100)) + "%"

                                if self.get_now is not None and self.get_now != track:
                                    tauon.console.print("ABORT")
                                    return

                                # if self.cancel is True:
                                #     self.part.close()
                                #     self.status = "failed"
                                #     print("Abort download")
                                #     return

                                f.write(chunk)
                    tauon.console.print("DONE")
                    self.files.append(key)
                    self.list.append(key)
                except:
                    print("ERROR")
                    return 1
                return 0


    cachement = Cachement()
    tauon.cachement = cachement

    def set_config(set_device=False):
        #aud.config_set_dev_buffer(prefs.device_buffer)
        aud.config_set_fade_duration(prefs.cross_fade_time)
        aud.config_set_dev_name(prefs.phazor_device_selected.encode())
        if set_device:
            aud.pause()
            aud.resume()

        if prefs.always_ffmpeg:
            aud.config_set_always_ffmpeg(1)
        if prefs.volume_power < 0 or prefs.volume_power > 10:
            prefs.volume_power = 2
        aud.config_set_volume_power(prefs.volume_power)

    #aud.config_set_samplerate(prefs.samplerate)
    aud.config_set_resample_quality(prefs.resample)

    set_config()

    def run_vis():
        if gui.turbo:  # and pctl.playing_time > 0.5:
            if gui.vis == 2:
                p_spec = []
                aud.get_spectrum(24, bins1)
                bias = 1
                for b in list(bins1):
                    p_spec.append(int(b * 1.7 * bias))
                    bias += 0.04
                gui.spec = p_spec
                gui.level_update = True
                if pctl.playing_time > 0.5 and (pctl.playing_state == 1 or pctl.playing_state == 3):
                    gui.update_spec = 1
            elif gui.vis == 4:
                p_spec = []
                aud.get_spectrum(45, bins2)
                bias = 1
                for b in list(bins2):
                    p_spec.append(int(b * 2.0 * bias))
                    bias += 0.01
                gui.spec4_array = p_spec
                gui.level_update = True
                if pctl.playing_time > 0.5 and (pctl.playing_state == 1 or pctl.playing_state == 3):
                    gui.update_spec = 1

    stall_timer = Timer()
    wall_timer = Timer()

    def track(end=True, wall=False):

        run_vis()
        wall = True

        if end and loaded_track and loaded_track.is_network and pctl.playing_time < 7:
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

        pctl.total_playtime += add_time

        ##t = aud.get_position_ms() / 1000

        # if t and end:
        #     pctl.decode_time = t - loaded_track.start_time
        #     if abs(pctl.decode_time - pctl.playing_time) > 5:  # Eehh hack fix?
        #         pctl.decode_time = pctl.playing_time
        # else:
        #     pctl.decode_time = pctl.playing_time
        #
        # print((pctl.playing_time, pctl.decode_time))

        #if wall or tauon.spot_ctl.playing or wall_timer.get() < 2:
        pctl.playing_time += add_time
        # else:
        #     #new = t - loaded_track.start_time
        #     new = t - pctl.start_time
        #     if new != pctl.playing_time:
        #         stall_timer.set()
        #         pctl.playing_time = new
        #     elif stall_timer.get() > 2:
        #         print("STALL!")
        #         pctl.playing_time += add_time

        pctl.decode_time = pctl.playing_time

        if pctl.playing_time < 3 and pctl.a_time < 3:
            pctl.a_time = pctl.playing_time
        else:
            pctl.a_time += add_time

        tauon.lfm_scrobbler.update(add_time)

        if len(pctl.track_queue) > 0 and 2 > add_time > 0:
            tauon.star_store.add(pctl.track_queue[pctl.queue_step], add_time)
        if end and pctl.playing_time > 1:
            pctl.test_progress()

    chrome_update = 0
    chrome_cool_timer = Timer()
    chrome_mode = False

    def chrome_start(track, enqueue=False, t=0):
        track = pctl.g(track)
        # if track.is_cue:
        #     print("Error: CUE cast not supported")
        #     return
        if track.is_network:
            if track.file_ext == "SPTY":
                print("Error: Spotify cast not supported")
                return
            network_url, params = pctl.get_url(track)
            if params:
                req = PreparedRequest()
                req.prepare_url(network_url, params)
                network_url = req.url

            tauon.chrome.start(track.index, enqueue=enqueue, url=network_url, t=t)
        else:
            tauon.chrome.start(track.index, enqueue=enqueue, t=t)

    while True:

        time.sleep(0.016)
        if state == 2:
            time.sleep(0.05)
        if state != 0 or tauon.spot_ctl.playing or tauon.spot_ctl.coasting or tauon.chrome_mode:
            active_timer.set()
        if active_timer.get() > 7:
           aud.stop()
           aud.phazor_shutdown()
           break

        # Level meter
        if (state == 1 or state == 3) and gui.vis == 1:
            amp = aud.get_level_peak_l()
            l = amp * 12
            amp = aud.get_level_peak_r()
            r = amp * 12

            tauon.level_train.append((0, l, r))
            gui.level_update = True

        if chrome_mode:
            if pctl.playerCommandReady:
                command = pctl.playerCommand
                # print(command)
                subcommand = pctl.playerSubCommand
                pctl.playerSubCommand = ""
                pctl.playerCommandReady = False

                if command == "endchrome":
                    chrome_mode = False
                    state = 0
                    pctl.playing_time = 0
                    pctl.decode_time = 0
                    pctl.stop()
                    continue
                if command == "open":
                    target_object = pctl.target_object
                    if state == 1:
                        t, pid, s, d = tauon.chrome.update()
                        # print((t, d))
                        # print(d - t)

                        if d and t and 1 < d - t < 5:
                            # print("Enqueue next chromecast")
                            chrome_start(target_object.index, enqueue=True, t=pctl.start_time_target)
                            chrome_cool_timer.set()
                            time.sleep(d - t)
                            if pctl.commit:
                                pctl.advance(quiet=True, end=True)
                                pctl.commit = None
                            continue

                    chrome_start(target_object.index, t=pctl.start_time_target)
                    chrome_cool_timer.set()
                    if pctl.commit:
                        pctl.advance(quiet=True, end=True)
                        pctl.commit = None
                    state = 1
                if command == "pauseon":
                    tauon.chrome.pause()
                    state = 2
                if command == "pauseoff":
                    tauon.chrome.play()
                    state = 1
                if command == "volume":
                    tauon.chrome.volume(round(pctl.player_volume / 100, 3))
                    state = 1
                if command == "seek":
                    tauon.chrome.seek(float(round(pctl.new_time + pctl.start_time_target, 2)))
                    chrome_cool_timer.set()
                    pctl.playing_time = pctl.new_time
                    pctl.decode_time = pctl.playing_time
                if command == "stop":
                    state = 0
                    tauon.chrome.stop()

            if state == 1:

                if chrome_update > 0.8 and chrome_cool_timer.get() > 2.5:
                    t, pid, s, d = tauon.chrome.update()
                    pctl.playing_time = t - pctl.start_time_target
                    pctl.decode_time = t - pctl.start_time_target
                    player_timer.hit()
                    chrome_update = 0

                add_time = player_timer.hit()
                # pctl.playing_time += add_time
                # pctl.decode_time = pctl.playing_time
                chrome_update += add_time
                pctl.a_time += add_time

                pctl.test_progress()

            time.sleep(0.1)
            continue

        # Command processing
        if pctl.playerCommandReady:

            command = pctl.playerCommand
            subcommand = pctl.playerSubCommand
            pctl.playerSubCommand = ""
            pctl.playerCommandReady = False

            if command == "startchrome":
                aud.stop()
                if state == 1:
                    chrome_start(loaded_track.index, t=pctl.playing_time)
                chrome_mode = True

            if command == "reload":
                set_config()
            if command == "set-device":
                set_config(set_device=True)

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
                    aud.start(b"RAW FEED", 0, 0, ctypes.c_float(calc_rg(None)))
                    state = 3
                    player_timer.hit()

            if command == "open":
                if state == 2:
                    aud.set_volume(int(pctl.player_volume))

                stall_timer.set()
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

                    timer = Timer()
                    timer.set()
                    while True:
                        status, path = cachement.get_file(target_object)

                        if status == 0 or status == 2:
                            break
                        if timer.get() > 0.25 and gui.buffering is False:
                            gui.buffering_text = ""
                            gui.buffering = True
                            gui.update += 1
                            tauon.wake()
                        if cachement.ready == target_object and pctl.start_time_target + pctl.jump_time == 0:
                            break
                        time.sleep(0.05)
                        #print(status)

                    gui.buffering = False
                    gui.update += 1
                    tauon.wake()

                    if status == 2:
                        tauon.console.print("Could not locate resource")
                        target_object.found = False
                        pctl.playing_state = 0
                        pctl.jump_time = 0
                        #pctl.advance(inplace=True, play=True)
                        continue
                    target_path = path

                elif prefs.precache:
                    timer = Timer()
                    timer.set()
                    while True:
                        status, path = cachement.get_file(target_object)
                        if status == 0 or status == 2:
                            break
                        if timer.get() > 0.25 and gui.buffering is False:
                            gui.buffering_text = ""
                            gui.buffering = True
                            gui.update += 1
                            tauon.wake()

                        time.sleep(0.05)

                    gui.buffering = False
                    gui.update += 1
                    tauon.wake()

                    if status == 2:
                        target_object.found = False
                        pctl.playing_state = 0
                        pctl.jump_time = 0
                        pctl.advance(inplace=True, play=True)
                        continue
                    target_path = path

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

                    tauon.console.print(loaded_track.title + " -> " + target_object.title)
                    tauon.console.print(" --- length: " + str(length))
                    tauon.console.print(" --- position: " + str(position))
                    tauon.console.print(" --- We are %s from end" % str(remain))

                    if loaded_track.is_network or length == 0:
                        tauon.console.print("Phazor did not respond with a duration")
                        length = loaded_track.length
                        remain = length - position

                fade = 0
                error = False
                if state == 1 and length and position and not pctl.start_time_target and not pctl.jump_time and \
                        loaded_track and 0 < remain < 5.5 and not loaded_track.is_cue and subcommand != "now":

                    tauon.console.print("Transition gapless")

                    aud.next(target_path.encode(), int(pctl.start_time_target + pctl.jump_time) * 1000, ctypes.c_float(calc_rg(target_object)))

                    r_timer = Timer()
                    r_timer.set()
                    while r_timer.get() <= remain - prefs.device_buffer / 1000:
                        if pctl.commit:
                            track(end=False, wall=True)
                        time.sleep(0.016)
                        if pctl.playerCommandReady and pctl.playerCommand == "open":
                            print("JANK")
                            break

                    if pctl.commit is not None:
                        pctl.playing_time = 0
                        pctl.decode_time = 0
                        match = pctl.commit
                        pctl.advance(quiet=True, end=True)
                        pt = pctl.playing_object()
                        if pt and pt.index != match:
                            print("MISSFIRE")
                        elif pctl.playerCommandReady and pctl.playerCommand == "open":
                            pctl.playerCommandReady = False
                            pctl.playerCommand = ""

                    loaded_track = target_object
                    pctl.playing_time = pctl.jump_time

                else:
                    if pctl.commit:
                        pctl.advance(quiet=True, end=True)
                        pctl.commit = None
                        continue

                    if state == 1 and prefs.use_jump_crossfade:
                        fade = 1

                    tauon.console.print("Transition jump")

                    aud.start(target_path.encode(), int(pctl.start_time_target + pctl.jump_time) * 1000, fade, ctypes.c_float(calc_rg(target_object)))
                    loaded_track = target_object
                    pctl.playing_time = pctl.jump_time
                    if pctl.jump_time:
                        while aud.get_result() == 0:
                            time.sleep(0.016)
                            run_vis()
                        aud.set_position_ms(int(pctl.jump_time * 1000))

                    # Restart track is failed to load (for some network tracks) (broken with gapless loading)
                    while True:
                        r = aud.get_result()
                        if r == 1:
                            break
                        if r == 2:
                            if loaded_track.is_network:
                                gui.buffering = True
                                gui.buffering_text = ""

                                # while dm.request(loaded_track, whole=True) == "wait":
                                #     time.sleep(0.05)
                                #     if pctl.playerCommandReady:
                                #         break
                                print("Retry start file")
                                aud.start(target_path.encode(), int(pctl.start_time_target + pctl.jump_time) * 1000,
                                          fade, ctypes.c_float(calc_rg(target_object)))
                                gui.buffering = False
                                player_timer.set()
                                break
                            else:
                                aud.stop()
                                if not gui.message_box:
                                    gui.show_message("Error loading track", mode="warning")
                                error = True
                                break
                        time.sleep(0.016)
                        run_vis()

                    state = 1
                    if error:
                        state = 0

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

                pctl.commit = None
                stall_timer.set()
                wall_timer.force_set(3)

            if command == "seek":
                if tauon.spot_ctl.coasting or tauon.spot_ctl.playing:
                    tauon.spot_ctl.control("seek", int(pctl.new_time * 1000))
                    pctl.playing_time = pctl.new_time
                elif state > 0:

                    if loaded_track.is_network:  # and loaded_track.fullpath.endswith(".ogg"):

                        timer = Timer()
                        timer.set()
                        while True:
                            status, path = cachement.get_file(loaded_track)
                            if status == 0 or status == 2:
                                break
                            if timer.get() > 0.25 and gui.buffering is False:
                                gui.buffering_text = ""
                                gui.buffering = True
                                gui.update += 1
                                tauon.wake()

                            time.sleep(0.05)

                        gui.buffering = False
                        gui.update += 1
                        tauon.wake()

                        if status == 2:
                            loaded_track.found = False
                            pctl.playing_state = 0
                            pctl.jump_time = 0
                            pctl.stop()
                            continue

                        # The vorbis decoder doesn't like appended files
                        aud.start(path.encode(), int(pctl.new_time + pctl.start_time_target) * 1000, 0, ctypes.c_float(calc_rg(loaded_track)))
                        while aud.get_result() == 0:
                            time.sleep(0.01)
                    else:
                        aud.seek(int((pctl.new_time + pctl.start_time_target) * 1000), prefs.pa_fast_seek)

                    pctl.playing_time = pctl.new_time

                pctl.decode_time = pctl.playing_time
                wall_timer.set()

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
                stall_timer.set()
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
                aud.phazor_shutdown()

                if os.path.exists(audio_cache):
                    shutil.rmtree(audio_cache)

                pctl.playerCommand = "done"
                pctl.playerCommandReady = True
                break
        else:
            pctl.spot_test_progress()

            if state == 3:

                pctl.radio_progress()
                run_vis()

                add_time = player_timer.hit()
                pctl.playing_time += add_time
                pctl.decode_time = pctl.playing_time

                buffering = aud.is_buffering()
                if gui.buffering != buffering:
                    gui.buffering = buffering
                    gui.update += 1

            if state == 1:
                track()


