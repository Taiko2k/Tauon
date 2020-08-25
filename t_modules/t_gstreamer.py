# Tauon Music Box - GStreamer backend Module

# Copyright © 2018-2020, Taiko2k captain(dot)gxj(at)gmail.com

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


import time
import urllib.parse
import os
#import re
from t_modules.t_extra import Timer
import gi
from gi.repository import GLib

gi.require_version('Gst', '1.0')
gi.require_version('GstController', '1.0')
from gi.repository import Gst, GstController
from t_modules.t_extra import get_folder_size
import threading
import requests
import urllib.parse
from hsaudiotag import auto

def player3(tauon):  # GStreamer

    pctl = tauon.pctl
    lfm_scrobbler = tauon.lfm_scrobbler
    star_store = tauon.star_store
    gui = tauon.gui
    prefs = tauon.prefs

    class GPlayer:

        def __init__(self):

            print("Init GStreamer...")

            # This is used to keep track of time between callbacks.
            self.player_timer = Timer()

            # Store the track object that is currently playing
            self.loaded_track = None

            # This is used to keep note of what state of playing we should be in
            self.play_state = 0  # 0 is stopped, 1 is playing, 2 is paused

            # Initiate GSteamer
            Gst.init([])
            self.mainloop = GLib.MainLoop()

            # Populate list of output devices with defaults
            outputs = {}
            devices = ["PulseAudio", "ALSA", "JACK",]
            if tauon.snap_mode:  # Snap permissions don't support these by default
                devices.remove("JACK")
                devices.remove("ALSA")

            # Get list of available audio device
            # self.dm = Gst.DeviceMonitor()
            # self.dm.start()
            # for device in self.dm.get_devices():
            #     if device.get_device_class() == "Audio/Sink":
            #         print("----")
            #         print(device)
            #         element = device.create_element(None)
            #         print(element.get_factory().get_name())
            #         print(device.get_display_name())
            #         type_name = element.get_factory().get_name()
            #         if hasattr(element.props, "device"):
            #             print("HAS")
            #             device_name = element.props.device
            #             display_name = device.get_display_name()
            #
            #             # This is used by the UI to present list of options to the user in audio settings
            #             outputs[display_name] = (type_name, device_name)
            #             devices.append(display_name)

            # dm.stop()  # Causes a segfault sometimes
            pctl.gst_outputs = outputs
            pctl.gst_devices = devices

            # Create main "playbin" pipeline for playback
            self.playbin = Gst.ElementFactory.make("playbin", "player")

            # Create custom output bin from user preferences
            if not prefs.gst_use_custom_output:
                prefs.gst_output = prefs.gen_gst_out()

            self._output = Gst.parse_bin_from_description(
                prefs.gst_output, ghost_unlinked_pads=True)

            # Create a bin for the audio pipeline
            self._sink = Gst.ElementFactory.make("bin", "sink")
            self._sink.add(self._output)

            # Spectrum -------------------------
            # Cant seem to figure out how to process these magnitudes in a way that looks good

            # self.spectrum = Gst.ElementFactory.make("spectrum", "spectrum")
            # self.spectrum.set_property('bands', 20)
            # self.spectrum.set_property('interval', 10000000)
            # self.spectrum.set_property('threshold', -100)
            # self.spectrum.set_property('post-messages', True)
            # self.spectrum.set_property('message-magnitude', True)
            #
            # self.playbin.set_property('audio-filter', self.spectrum)
            # # ------------------------------------

            # # Level Meter -------------------------
            self.level = Gst.ElementFactory.make("level", "level")
            self.level.set_property('interval', 20000000)
            self.playbin.set_property('audio-filter', self.level)
            # # ------------------------------------

            self._eq = Gst.ElementFactory.make("equalizer-10bands", "eq")
            self._vol = Gst.ElementFactory.make("volume", "volume")

            self._sink.add(self._eq)
            self._sink.add(self._vol)

            self._eq.link(self._vol)
            self._vol.link(self._output)

            # Set the equalizer based on user preferences
            for i, level in enumerate(prefs.eq):
                if prefs.use_eq:
                    self._eq.set_property("band" + str(i), level * -1)
                else:
                    self._eq.set_property("band" + str(i), 0.0)

            # Set up sink pad for the intermediate bin via the
            # first element (volume)
            ghost = Gst.GhostPad.new("sink", self._eq.get_static_pad("sink"))
            self._sink.add_pad(ghost)

            # Connect the playback bin to to the intermediate bin sink pad
            self.playbin.set_property("audio-sink", self._sink)

            # The pipeline should look something like this -
            # (player) -> [(eq) -> (volume) -> (output)]

            # Create controller for pause/resume volume fading
            self.c_source = GstController.InterpolationControlSource()
            self.c_source.set_property('mode', GstController.InterpolationMode.LINEAR)
            self.c_binding = GstController.DirectControlBinding.new(self._vol, "volume", self.c_source)
            self._vol.add_control_binding(self.c_binding)

            # Set callback for the main callback loop
            GLib.timeout_add(50, self.main_callback)

            self.playbin.connect("about-to-finish", self.about_to_finish)  # Not used

            # Setup bus and select what types of messages we want to listen for
            bus = self.playbin.get_bus()
            bus.add_signal_watch()
            bus.connect('message::element', self.on_message)
            bus.connect('message::buffering', self.on_message)
            bus.connect('message::error', self.on_message)
            bus.connect('message::tag', self.on_message)
            bus.connect('message::warning', self.on_message)
            # bus.connect('message::eos', self.on_message)

            # Variables used with network downloading
            self.temp_id = "a"
            self.url = None
            self.dl_ready = True
            self.using_cache = False
            self.temp_path = ""  # Full path + filename
            # self.level_train = []
            self.seek_timer = Timer()
            self.seek_timer.force_set(10)
            self.buffering = False
            # Other
            self.end_timer = Timer()

            # Start GLib mainloop
            self.mainloop.run()

        def about_to_finish(self, bin):
            self.end_timer.set()

        def on_message(self, bus, msg):
            struct = msg.get_structure()
            #print(struct.get_name())
            #print(struct.to_string())

            name = struct.get_name()

            if name == "GstMessageError":

                if "_is_dead" in struct.to_string():
                    # Looks like PulseAudio was reset. Need to restart playback.

                    self.playbin.set_state(Gst.State.NULL)

                    if tauon.stream_proxy.download_running:
                        tauon.stream_proxy.stop()
                    else:
                        self.playbin.set_state(Gst.State.PLAYING)
                        tries = 0
                        while tries < 10:
                            time.sleep(0.03)
                            r = self.playbin.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                                         (pctl.start_time_target + pctl.playing_time) * Gst.SECOND)
                            if r:
                                break
                            tries += 1

            if self.play_state == 3 and name == "GstMessageTag":

                data = struct.get_value("taglist").get_string("title")
                data2 = struct.get_value("taglist").get_string("artist")
                data3 = struct.get_value("taglist").get_string("year")
                data4 = struct.get_value("taglist").get_string("album")
                # print(struct.to_string())
                if data[0]:
                    pctl.tag_meta = ""
                    line = ""
                    line = data[1]
                    if data2[0]:
                        line = data2[1] + " - " + line

                    pctl.found_tags = {}

                    pctl.found_tags["title"] = data[1]
                    if data2[0]:
                        pctl.found_tags["artist"] = data2[1]
                    if data3[0]:
                        pctl.found_tags["year"] = str(data3[1])
                    if data4[0]:
                        pctl.found_tags["album"] = data4[1]

                    pctl.tag_meta = line
                    print("Found tag: " + line)

            elif name == "GstMessageError":
                if "Connection" in struct.get_value("debug"):
                    gui.show_message("Connection error", mode="info")
            elif name == 'GstMessageBuffering':

                if pctl.playing_state == 3:
                    buff_percent = struct.get_value("buffer-percent")

                    if buff_percent == 0 and (self.play_state == 1 or self.play_state == 3):
                        self.playbin.set_state(Gst.State.PAUSED)
                        self.buffering = True
                        print("Buffering...")

                    elif self.buffering and buff_percent == 100 and (self.play_state == 1 or self.play_state == 3):
                        self.playbin.set_state(Gst.State.PLAYING)
                        self.buffering = False
                        print("Buffered")

            if gui.vis == 1 and name == 'level':

                data = struct.get_value("peak")
                ts = struct.get_value("timestamp")
                # print(data)
                r = (10 ** (data[0] / 20)) * 11.6
                if len(data) == 1:
                    l = r
                else:
                    l = (10 ** (data[1] / 20)) * 11.6

                td = (ts / 1000000000) - (self.playbin.query_position(Gst.Format.TIME)[1] / Gst.SECOND)
                t = time.time()
                rt = t + td
                if td > 0:
                    for item in tauon.level_train:
                        if rt < item[0]:
                            tauon.level_train.clear()
                            # print("FF")
                            break
                    tauon.level_train.append((rt, r, l))

            # if name == 'spectrum':
            #     struct_str = struct.to_string()
            #     magnitude_str = re.match(r'.*magnitude=\(float\){(.*)}.*', struct_str)
            #     if magnitude_str:
            #         magnitude = map(float, magnitude_str.group(1).split(','))
            #
            #         l = list(magnitude)
            #         k = []
            #         #print(l)
            #         for a in l[0:20]:
            #             #v = ??
            #             k.append()
            #         print(k)
            #         gui.spec = k
            #         #print(k)
            #         gui.level_update = True
            #
            # return True


        def check_duration(self):

            # This function is to be called when loading a track to query for a duration of track
            # in case the tagger failed to calculate a length for the track when imported.

            # Get current playing track object from player
            current_track = pctl.playing_object()

            if current_track is not None and current_track.length < 1:

                result = self.playbin.query_duration(Gst.Format.TIME)

                if result[0] is True:
                    current_track.length = result[1] / Gst.SECOND

                else:  # still loading? I guess we wait and try again.
                    time.sleep(1.5)
                    result = self.playbin.query_duration(Gst.Format.TIME)

                    if result[0] is True:
                        current_track.length = result[1] / Gst.SECOND

        def download_part(self, url, target, params, id):

            #   GStreamer can't seek some types of HTTP sources.
            #
            #   To work around this, when a seek is requested by the user, this
            #   function facilitates the download of the URL in whole, then loaded
            #   into GStreamer as a complete file to provide at least some manner of seeking
            #   ability for the user. (User must wait for full download)
            #
            #   (Koel and Airsonic MP3 sources are exempt from this as seeking does work with them)
            #
            #   A better solution might be to download file externally then feed the audio data
            #   into GStreamer as it downloads. This still would have the issue that the whole file
            #   must have been downloaded before a seek could begin.
            #
            #   With the old BASS backend, this was done with the file on disk being constantly
            #   appended to. Unfortunately GStreamer doesn't support playing files in this manner.

            try:
                part = requests.get(url, stream=True, params=params)
            except:
                gui.show_message("Could not connect to server", mode="error")
                self.dl_ready = True
                return

            bitrate = 0

            a = 0
            z = 0
            # print(target)
            f = open(target, "wb")
            for chunk in part.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    a += 1
                    # if a == 300:  # kilobyes~
                    #     self.dl_ready = True

                    if id != self.id:
                        part.close()
                        f.close()
                        os.remove(target)
                        return
                        # break

                    f.write(chunk)

                    # Periodically update download the progress indicator
                    z += 1
                    if id == self.id:
                        if z == 60:
                            z = 0
                            if bitrate == 0:
                                audio = auto.File(target)
                                bitrate = audio.bitrate

                            if bitrate > 0:
                                gui.update += 1
                                pctl.download_time = a * 1024 / (bitrate / 8) / 1000
            f.close()
            pctl.download_time = -1

            self.dl_ready = True

        def main_callback(self):

            if not pctl.playerCommandReady and pctl.playing_state == 0:
                tauon.tm.player_lock.acquire()

            if gui.vis == 1:
                if pctl.playing_state == 1:
                    gui.level_update = True
            # Level meter visualiser
            ##if gui.vis == 1:
                # if pctl.playing_state == 1:
                #     gui.level_update = True
                #     while self.level_train and self.level_train[0][0] < time.time():
                #
                #         l = self.level_train[0][1]
                #         r = self.level_train[0][2]
                #
                #         if r > gui.level_peak[0]:
                #             gui.level_peak[0] = r
                #         if l > gui.level_peak[1]:
                #             gui.level_peak[1] = l
                #
                #         del self.level_train[0]
                #
                #     gui.level_peak[1] -= 0.30
                #     gui.level_peak[0] -= 0.30
                #
                # else:
                #     self.level_train.clear()

            # This is the main callback function to be triggered continuously as long as application is running
            if self.play_state == 1 and pctl.playing_time > 1 and not pctl.playerCommandReady:

                pctl.test_progress()  # This function triggers an advance if we are near end of track

                success, state, pending = self.playbin.get_state(3 * Gst.SECOND)
                if state != Gst.State.PLAYING:
                    time.sleep(0.5)

                    print("Stall...")

            if self.play_state == 3:
                pctl.radio_progress()

            if not pctl.playerCommandReady:
                pctl.spot_test_progress()

            if pctl.playerCommandReady:
                command = pctl.playerCommand
                pctl.playerCommandReady = False

                # Here we process commands from the main thread/module

                # Possible commands:

                # open:     Start playback of a file
                #           Path given by pctl.target_open at position pctl.start_time_target + pctl.jump_time
                # stop:     Stop playback (Implies release file)
                # runstop:  Stop playback but let finish if we are near the end of the file
                # pauseon:  Pause playback (be ready to resume)
                # pauseoff: Resume playback if paused
                # volume:   Set to the volume specified by pctl.player_volume (0 to 100)
                # seek:     Seek to position given by pctl.new_time + pctl.start_time (don't resume playback if paused)
                # url:      Start playback of a shoutcast/icecast stream. URL specified by pctl.url
                #           todo: start recording if pctl.record_stream  (rec button is current disabled for GST in UI)
                #                 encode to OGG and output file to prefs.encoder_output
                #                 automatically name files and split on metadata change
                # unload:   Stop, cleanup and exit thread
                # done:     Tell the main thread we finished doing a special request it was waiting for (such as unload)

                # Todo: Visualisers (Hard)
                # Ideally we would want the same visual effect as the old BASS based visualisers.
                # What we want to do is constantly get binned spectrum data and pass it to the UI.
                # Specifically, format used with BASS module is:
                # - An FFT of sample data with Hanning window applied
                # - 1024 samples (returns first half, 512 values)
                # - Non-complex (magnitudes)
                # - Combined left and right channels
                # - Binned to particular numbers of bars and passed onto UI after some scaling and truncating

                pctl.download_time = 0
                url = None
                if command == 'open' and pctl.target_object:
                    # print("Start track")
                    track = pctl.target_object

                    if (tauon.spot_ctl.playing or tauon.spot_ctl.coasting) and not track.file_ext == "SPTY":
                        tauon.spot_ctl.control("stop")

                    if tauon.stream_proxy.download_running:
                        tauon.stream_proxy.stop()

                    # Check if the file exists, mark it as missing if not
                    if track.is_network:

                        if track.file_ext == "SPTY":
                            tauon.level_train.clear()
                            if self.play_state > 0:
                                self.playbin.set_state(Gst.State.READY)
                            self.play_state = 0
                            try:
                                tauon.spot_ctl.play_target(track.url_key)
                            except:
                                print("Failed to start Spotify track")
                                pctl.playerCommand = "stop"
                                pctl.playerCommandReady = True

                            GLib.timeout_add(19, self.main_callback)

                            return

                        try:
                            url, params = pctl.get_url(track)
                            self.urlparams = url, params
                        except:
                            time.sleep(0.1)
                            gui.show_message("Connection error", "Bad login? Server offline?", mode='info')
                            pctl.stop()
                            pctl.playerCommand = ""
                            self.main_callback()
                            return

                    # If the target is a file, check that is exists
                    elif os.path.isfile(track.fullpath):
                        track.found = True
                    else:
                        # File does not exist, force trigger an advance
                        pctl.target_object.found = False
                        tauon.console.print("Missing File: " + track.fullpath, 2)
                        pctl.playing_state = 0
                        pctl.jump_time = 0
                        pctl.advance(inplace=True, nolock=True)
                        GLib.timeout_add(19, self.main_callback)
                        pctl.playerCommandReady = False
                        return

                    gapless = False
                    current_time = 0
                    current_duration = 0

                    if track.is_network:
                        if params:
                            self.url = url + ".view?" + urllib.parse.urlencode(params)
                        else:
                            self.url = url

                    if self.play_state != 0:
                        # Determine time position of currently playing track
                        current_time = self.playbin.query_position(Gst.Format.TIME)[1] / Gst.SECOND
                        current_duration = self.playbin.query_duration(Gst.Format.TIME)[1] / Gst.SECOND
                        # print("We are " + str(current_duration - current_time) + " seconds from end.")

                    # If we are close to the end of the track, try transition gaplessly
                    if self.play_state == 1 and pctl.start_time_target == 0 and pctl.jump_time == 0 and \
                            current_duration - current_time < 5.5 and not pctl.playerSubCommand == 'now' \
                            and self.end_timer.get() > 3:

                        gapless = True

                        if self.play_state == 1 and self.loaded_track and self.loaded_track.is_network:
                            # Gst may report wrong length for network tracks, use known length instead
                            if pctl.playing_time < self.loaded_track.length - 4:
                                gapless = False


                    # We're not at the end of the last track so reset the pipeline
                    if not gapless:
                        self.playbin.set_state(Gst.State.NULL)
                        tauon.level_train.clear()

                    pctl.playerSubCommand = ""
                    self.play_state = 1

                    self.save_temp = tauon.temp_audio + "/" + str(track.index) + "-audio"
                    # shoot_dl = threading.Thread(target=self.download_part,
                    #                             args=([url, self.save_temp, params, track.url_key]))
                    # shoot_dl.daemon = True
                    # shoot_dl.start()
                    self.using_cache = False

                    self.id = track.url_key
                    if url:
                        # self.playbin.set_property('uri',
                        #                           'file://' + urllib.parse.quote(os.path.abspath(self.save_temp)))

                        if self.dl_ready and os.path.exists(self.save_temp):
                            self.using_cache = True
                            self.playbin.set_property('uri',
                                                      'file://' + urllib.parse.quote(os.path.abspath(self.save_temp)))
                        else:
                            self.playbin.set_property('uri', self.url)
                    else:
                        # Play file on disk
                        self.playbin.set_property('uri', 'file://' + urllib.parse.quote(os.path.abspath(track.fullpath)))

                    if pctl.start_time_target > 0:
                        self.playbin.set_property('volume', 0.0)
                    else:
                        self.playbin.set_property('volume', pctl.player_volume / 100)

                    self.playbin.set_state(Gst.State.PLAYING)
                    if pctl.jump_time == 0 and not pctl.playerCommand == "seek":
                        pctl.playing_time = 0

                    # The position to start is not always the beginning of the file, so seek to position
                    if pctl.start_time_target > 0 or pctl.jump_time > 0:

                        tries = 0
                        while tries < 150:
                            time.sleep(0.03)
                            r = self.playbin.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                                (pctl.start_time_target + pctl.jump_time) * Gst.SECOND)
                            if r:
                                break
                            tries += 1
                            if tries > 2:
                                print("Seek failed, retrying...")
                                print(tries)

                        pctl.playing_time = 0
                        gui.update = 1

                        self.playbin.set_property('volume', pctl.player_volume / 100)

                    if gapless:  # Hold thread while a gapless transition is in progress
                        t = 0
                        # print("Gapless go")
                        while self.playbin.query_position(Gst.Format.TIME)[1] / Gst.SECOND >= current_time > 0:

                            time.sleep(0.02)
                            t += 1

                            if self.playbin.get_state(0).state != Gst.State.PLAYING:
                                break

                            if t > 250:
                                print("Gonna stop waiting...")  # Cant wait forever
                                break

                            if pctl.playerCommand == 'open' and pctl.playerCommandReady:
                                # Cancel the gapless transition
                                self.playbin.set_state(Gst.State.NULL)
                                time.sleep(0.1)
                                GLib.timeout_add(19, self.main_callback)
                                pctl.playerCommandReady = False
                                return


                    add_time = max(min(self.player_timer.hit(), 3), 0)
                    if self.loaded_track:
                        star_store.add(self.loaded_track.index, add_time)

                    self.loaded_track = track

                    pctl.jump_time = 0
                    #time.sleep(1)
                    add_time = self.player_timer.hit()
                    if add_time > 2:
                        add_time = 2
                    if add_time < 0:
                        add_time = 0
                    pctl.playing_time += add_time
                    pctl.decode_time = pctl.playing_time

                    if self.loaded_track:
                        star_store.add(self.loaded_track.index, add_time)

                    # self.check_duration()
                    self.player_timer.hit()

                elif command == 'url':

                    # Stop if playing or paused
                    if self.play_state == 1 or self.play_state == 2 or self.play_state == 3:
                        self.playbin.set_state(Gst.State.NULL)
                        time.sleep(0.1)

                    w = 0
                    while len(tauon.stream_proxy.chunks) < 50:
                        time.sleep(0.01)
                        w += 1
                        if w > 500:
                            print("Taking too long!")
                            tauon.stream_proxy.stop()
                            pctl.playerCommand = 'stop'
                            pctl.playerCommandReady = True
                            break
                    else:
                        # Open URL stream
                        self.playbin.set_property('uri', pctl.url)
                        self.playbin.set_property('volume', pctl.player_volume / 100)
                        self.buffering = False
                        self.playbin.set_state(Gst.State.PLAYING)
                        self.play_state = 3
                        self.player_timer.hit()

                elif command == 'seteq':
                    for i, level in enumerate(prefs.eq):
                        if prefs.use_eq:
                            self._eq.set_property("band" + str(i), level * -1)
                        else:
                            self._eq.set_property("band" + str(i), 0.0)

                elif command == 'volume':

                    if tauon.spot_ctl.coasting or tauon.spot_ctl.playing:
                        tauon.spot_ctl.control("volume", int(pctl.player_volume))

                    elif self.play_state == 1 or self.play_state == 3:

                        success, current_time = self.playbin.query_position(Gst.Format.TIME)
                        self.playbin.set_state(Gst.State.PLAYING)

                        if success and False:
                            start = current_time + ((100 / 1000) * Gst.SECOND)
                            end = current_time + ((600 / 1000) * Gst.SECOND)
                            self.c_source.set(start, self._vol.get_property('volume') / 10)
                            self.c_source.set(end, (pctl.player_volume / 100) / 10)
                            time.sleep(0.5)
                            self.c_source.unset_all()
                        else:
                            self.playbin.set_property('volume', pctl.player_volume / 100)

                elif command == 'runstop':

                    if self.play_state != 0:
                        # Determine time position of currently playing track
                        current_time = self.playbin.query_position(Gst.Format.TIME)[1] / Gst.SECOND
                        current_duration = self.playbin.query_duration(Gst.Format.TIME)[1] / Gst.SECOND
                        if current_duration - current_time < 5.5:
                            pass
                        else:
                            self.playbin.set_state(Gst.State.READY)
                    else:
                        self.playbin.set_state(Gst.State.READY)
                    self.play_state = 0
                    pctl.playerSubCommand = "stopped"

                elif command == 'stop':
                    if self.play_state > 0:

                        if prefs.use_pause_fade:
                            success, current_time = self.playbin.query_position(Gst.Format.TIME)
                            if success:
                                start = current_time + (150 / 1000 * Gst.SECOND)
                                end = current_time + (prefs.pause_fade_time / 1000 * Gst.SECOND)
                                self.c_source.set(start, (pctl.player_volume / 100) / 10)
                                self.c_source.set(end, 0.0)
                                time.sleep(prefs.pause_fade_time / 1000)
                                time.sleep(0.05)
                                self.c_source.unset_all()

                        self.playbin.set_state(Gst.State.NULL)
                        time.sleep(0.1)
                        self._vol.set_property("volume", pctl.player_volume / 100)

                    self.play_state = 0
                    pctl.playerSubCommand = "stopped"

                elif command == 'seek':
                    self.seek_timer.set()
                    if tauon.spot_ctl.coasting or tauon.spot_ctl.playing:
                        tauon.spot_ctl.control("seek", int(pctl.new_time * 1000))
                        pctl.playing_time = pctl.new_time
                        
                    elif self.play_state > 0:
                        if not self.using_cache and pctl.target_object.is_network and \
                                not pctl.target_object.file_ext == "KOEL" and \
                                not (pctl.target_object.file_ext == "SUB" and pctl.target_object.fullpath.endswith("mp3")):

                            if not os.path.exists(tauon.temp_audio):
                                os.makedirs(tauon.temp_audio)

                            listing = os.listdir(tauon.temp_audio)
                            full = [os.path.join(tauon.temp_audio, x) for x in listing]
                            size = get_folder_size(tauon.temp_audio) / 1000000
                            print(f"Audio cache size is {size}MB")
                            if size > 120:
                                oldest_file = min(full, key=os.path.getctime)
                                print("Cache full, delete oldest cached file")
                                os.remove(oldest_file)

                            pctl.playing_time = 0
                            self.playbin.set_state(Gst.State.NULL)
                            self.dl_ready = False
                            url, params = self.urlparams
                            shoot_dl = threading.Thread(target=self.download_part,
                                                        args=([url, self.save_temp, params, pctl.target_object.url_key]))
                            shoot_dl.daemon = True
                            shoot_dl.start()
                            pctl.playerCommand = ""
                            while not self.dl_ready:
                                # print("waiting...")
                                time.sleep(0.25)
                                if pctl.playerCommandReady and pctl.playerCommand != "seek":
                                    print("BREAK!")
                                    self.main_callback()
                                    return

                            self.playbin.set_property('uri', 'file://' + urllib.parse.quote(
                                os.path.abspath(self.save_temp)))
                            #time.sleep(0.05)
                            self.playbin.set_state(Gst.State.PLAYING)
                            self.using_cache = True
                            time.sleep(0.1)

                        self.playbin.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                                 (pctl.new_time + pctl.start_time_target) * Gst.SECOND)

                        # It may take a moment for seeking to update when streaming, so for better UI feedback we'll
                        # update the seek indicator immediately and hold the thread for a moment
                        if pctl.target_object.is_network:
                            pctl.playing_time = pctl.new_time + pctl.start_time_target
                            pctl.decode_time = pctl.playing_time
                            time.sleep(0.25)


                elif command == 'pauseon':
                    self.player_timer.hit()
                    self.play_state = 2

                    if prefs.use_pause_fade:
                        success, current_time = self.playbin.query_position(Gst.Format.TIME)
                        if success:
                            start = current_time + (150 / 1000 * Gst.SECOND)
                            end = current_time + (prefs.pause_fade_time / 1000 * Gst.SECOND)
                            self.c_source.set(start, (pctl.player_volume / 100) / 10)
                            self.c_source.set(end, 0.0)
                            time.sleep(prefs.pause_fade_time / 1000)
                            self.c_source.unset_all()

                    self.playbin.set_state(Gst.State.PAUSED)

                elif command == 'pauseoff':
                    self.player_timer.hit()

                    if not prefs.use_pause_fade:
                        self.playbin.set_state(Gst.State.PLAYING)

                    else:
                        self._vol.set_property("volume", 0.0)
                        success, current_time = self.playbin.query_position(Gst.Format.TIME)
                        self.playbin.set_state(Gst.State.PLAYING)
                        if success:
                            start = current_time + (150 / 1000 * Gst.SECOND)
                            end = current_time + ((prefs.pause_fade_time / 1000) * Gst.SECOND)
                            self.c_source.set(start, 0.0)
                            self.c_source.set(end, (pctl.player_volume / 100) / 10)
                            time.sleep(prefs.pause_fade_time / 1000)
                            time.sleep(0.05)
                            self.c_source.unset_all()

                    self._vol.set_property("volume", pctl.player_volume / 100)


                    self.play_state = 1

                elif command == 'unload':
                    if self.play_state > 0:
                        self.playbin.set_state(Gst.State.NULL)
                        time.sleep(0.05)
                    print("unload")
                    self.mainloop.quit()
                    pctl.playerCommand = 'done'
                    print("return")
                    return

            if self.play_state == 3:
                if self.playbin.get_state(0).state == Gst.State.PLAYING:
                    add_time = self.player_timer.hit()
                    if add_time > 2:
                        add_time = 2
                    if add_time < 0:
                        add_time = 0
                    pctl.playing_time += add_time
                    pctl.decode_time = pctl.playing_time

            if self.play_state == 1:

                # Get jump in time since last call
                add_time = self.player_timer.hit()

                # Limit the jump.
                if add_time > 2:
                    add_time = 2
                if add_time < 0:
                    add_time = 0

                # # Progress main seek head
                if self.playbin.get_state(0).state == Gst.State.PLAYING and self.seek_timer.get() > 1 and not pctl.playerCommandReady:

                    pctl.playing_time += add_time

                    p = max(0, (self.playbin.query_position(Gst.Format.TIME)[1] / Gst.SECOND) -
                                                 pctl.start_time_target)

                    if abs(pctl.playing_time - p) > 1.5:
                        pctl.playing_time = p

                    pctl.decode_time = pctl.playing_time  # A difference isn't discerned in this module

                else:
                    # We're supposed to be playing but it's not? Give it a push I guess.
                    #self.playbin.set_state(Gst.State.PLAYING)
                    pctl.playing_time += add_time
                    pctl.decode_time = pctl.playing_time

                # Other things we need to progress such as scrobbling
                if pctl.playing_time < 3 and pctl.a_time < 3:
                    pctl.a_time = pctl.playing_time
                else:
                    pctl.a_time += add_time

                pctl.total_playtime += add_time
                lfm_scrobbler.update(add_time)  # This handles other scrobblers such as listenbrainz also

                # Update track total playtime
                if len(pctl.track_queue) > 0 and 2 > add_time > 0:
                    star_store.add(pctl.track_queue[pctl.queue_step], add_time)

            if not pctl.running:
                # print("unloading gstreamer")
                if self.play_state > 0:
                    self.playbin.set_state(Gst.State.NULL)
                    time.sleep(0.5)

                self.mainloop.quit()
                pctl.playerCommand = 'done'

            else:
                if gui.vis == 1:
                    GLib.timeout_add(19, self.main_callback)
                else:
                    GLib.timeout_add(100, self.main_callback)

        def exit(self):
            print("GStreamer unloaded")
            pctl.playerCommand = 'done'

    player = GPlayer()

    # try:
    #     player.dm.stop()
    # except:
    #     pass

    # Notify main thread we have closed cleanly
    player.exit()
