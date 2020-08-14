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

print("GST 1")

gi.require_version('Gst', '1.0')
from gi.repository import Gst
from t_modules.t_extra import get_folder_size
import threading
import requests
import urllib.parse
from hsaudiotag import auto


print("GST 2")



def player3(tauon):  # GStreamer

    pctl = tauon.pctl
    lfm_scrobbler = tauon.lfm_scrobbler
    star_store = tauon.star_store
    gui = tauon.gui
    prefs = tauon.prefs



    class GPlayer:

        def __init__(self):

            print("GST 3")

            # This is used to keep track of time between callbacks to progress the seek bar
            self.player_timer = Timer()

            self.loaded_track = None

            # This is used to keep note of what state of playing we should be in
            self.play_state = 0  # 0 is stopped, 1 is playing, 2 is paused

            # Initiate GSteamer
            Gst.init([])
            self.mainloop = GLib.MainLoop()

            print("GST 4")

            # Get list of available audio device

            devices = []
            outputs = {}

            devices = ["Auto", "PulseAudio", "ALSA", "JACK"]
            if tauon.snap_mode:
                devices.remove("JACK")
                devices.remove("ALSA")



            dm = Gst.DeviceMonitor()
            dm.start()
            for device in dm.get_devices():
                if device.get_device_class() == "Audio/Sink":
                    element = device.create_element(None)
                    type_name = element.get_factory().get_name()
                    device_name = element.props.device
                    display_name = device.get_display_name()

                    # This is used by the UI to present list of options to the user in audio settings
                    outputs[display_name] = (type_name, device_name)
                    devices.append(display_name)

            dm.stop()
            pctl.gst_outputs = outputs
            pctl.gst_devices = devices

            # Create main "playbin" pipeline for playback
            self.playbin = Gst.ElementFactory.make("playbin", "player")

            # Create output bin
            if not prefs.gst_use_custom_output:
                prefs.gst_output = prefs.gen_gst_out()

            self._output = Gst.parse_bin_from_description(
                prefs.gst_output, ghost_unlinked_pads=True)

            # Create a bin for the audio pipeline
            self._sink = Gst.ElementFactory.make("bin", "sink")
            self._sink.add(self._output)

            print("GST 5")
            # # Spectrum -------------------------
            # # This kind of works, but is a different result to that of the bass backend.
            # # This seems linear and also less visually appealing.
            #
            # self.spectrum = Gst.ElementFactory.make("spectrum", "spectrum")
            # self.spectrum.set_property('bands', 280)
            # self.spectrum.set_property('interval', 10000000)
            # self.spectrum.set_property('post-messages', True)
            # self.spectrum.set_property('message-magnitude', True)
            #
            # self.playbin.set_property('audio-filter', self.spectrum)
            # # ------------------------------------

            # # Level -------------------------
            # # This kind of works, but is a different result to that of the bass backend.
            # # This seems linear and also less visually appealing.
            #
            self.level = Gst.ElementFactory.make("level", "level")
            self.level.set_property('interval', 20000000)
            self.playbin.set_property('audio-filter', self.level)
            # # ------------------------------------

            # Create volume element
            self._vol = Gst.ElementFactory.make("volume", "volume")
            self._sink.add(self._vol)
            self._vol.link(self._output)

            # Set up sink pad for the intermediate bin via the
            #  first element (volume)
            ghost = Gst.GhostPad.new(
                "sink", self._vol.get_static_pad("sink"))

            self._sink.add_pad(ghost)

            # Connect the playback bin to to the intermediate bin sink pad
            self.playbin.set_property("audio-sink", self._sink)

            # The pipeline should look something like this -
            # (player) -> [(volume) -> (output)]

            # Set callback for the main callback loop
            GLib.timeout_add(50, self.main_callback)

            # self.playbin.connect("about-to-finish", self.about_to_finish)  # Not used by anything

            # # Enable bus to get spectrum messages
            bus = self.playbin.get_bus()
            bus.add_signal_watch()
            bus.connect('message::element', self.on_message)
            bus.connect('message::buffering', self.on_message)
            bus.connect('message::error', self.on_message)
            bus.connect('message::tag', self.on_message)
            bus.connect('message::warning', self.on_message)
            #bus.connect('message::eos', self.on_message)

            # Variables used with network downloading
            self.temp_id = "a"
            self.url = None
            self.dl_ready = True
            self.using_cache = False
            self.temp_path = ""  # Full path + filename

            print("GST 6")
            # # Broadcasting pipeline ------------
            #
            # # This works, but only for one track, switching tracks seems to be a more complicated process.
            #
            # self.b_playbin = Gst.ElementFactory.make("playbin", "player")
            #
            # # Create output bin
            # # Using tcpserversink seems to mostly work with the html5 player, though an HTTP server may be preferred.
            # self._b_output = Gst.parse_bin_from_description(
            #    "audioconvert ! vorbisenc ! oggmux ! tcpserversink port=8000", ghost_unlinked_pads=True)
            #    #"autoaudiosink", ghost_unlinked_pads=True)
            #
            # # Connect the playback bin to to the output bin
            # self.b_playbin.set_property("audio-sink", self._b_output)
            # # ----------------------------------------


            self.level_train = []
            # Start GLib mainloop
            self.mainloop.run()


        # # Used to get spectrum data and pass onto UI
        def on_message(self, bus, msg):
            struct = msg.get_structure()
            # print(struct.get_name())
            # print(struct.to_string())

            name = struct.get_name()
            
            if name == "GstMessageError":
                print(struct.to_string())

            if self.play_state == 3 and name == "GstMessageTag":
                data = struct.get_value("taglist").get_string("title")
                if data[0]:
                    pctl.tag_meta = data[1]

            elif name == "GstMessageError":
                if "Connection" in struct.get_value("debug"):
                    gui.show_message("Connection error", mode="info")
            elif name == 'GstMessageBuffering':
                buff_percent = struct.get_value("buffer-percent")

                if buff_percent < 100 and (self.play_state == 1 or self.play_state == 3):
                    self.playbin.set_state(Gst.State.PAUSED)

                elif buff_percent == 100 and (self.play_state == 1 or self.play_state == 3):
                    self.playbin.set_state(Gst.State.PLAYING)

            if gui.vis == 1 and name == 'level':

                data = struct.get_value("peak")
                ts = struct.get_value("timestamp")
                #print(data)
                r = (10 ** (data[0] / 20)) * 11.6
                if len(data) == 1:
                    l = r
                else:
                    l = (10 ** (data[1] / 20)) * 11.6

                td = (ts / 1000000000) - (self.playbin.query_position(Gst.Format.TIME)[1] / Gst.SECOND)
                t = time.time()
                rt = t + td
                if td > 0:
                    for item in self.level_train:
                        if rt < item[0]:
                            self.level_train.clear()
                            #print("FF")
                            break
                    self.level_train.append((rt, r, l))

            return True

            # if struct.get_name() == 'spectrum':
        #         struct_str = struct.to_string()
        #         magnitude_str = re.match(r'.*magnitude=\(float\){(.*)}.*', struct_str)
        #         if magnitude_str:
        #             magnitude = map(float, magnitude_str.group(1).split(','))
        #
        #             l = list(magnitude)
        #             k = []
        #             for a in l[:23]:
        #                 k.append(a + 60)
        #             gui.spec = k
        #             #print(k)
        #             gui.level_update = True


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

            # Level meter visualiser
            if gui.vis == 1:

                if pctl.playing_state == 1:
                    gui.level_update = True
                    while self.level_train and self.level_train[0][0] < time.time():

                        l = self.level_train[0][1]
                        r = self.level_train[0][2]

                        if r > gui.level_peak[0]:
                            gui.level_peak[0] = r
                        if l > gui.level_peak[1]:
                            gui.level_peak[1] = l

                        del self.level_train[0]

                    gui.level_peak[1] -= 0.30
                    gui.level_peak[0] -= 0.30

                else:
                    self.level_train.clear()

            # This is the main callback function to be triggered continuously as long as application is running
            if self.play_state == 1 and pctl.playing_time > 1 and not pctl.playerCommandReady:
                pctl.test_progress()  # This function triggers an advance if we are near end of track

            if self.play_state == 3:
                pctl.radio_progress()

            if not pctl.playerCommandReady:
                pctl.spot_test_progress()

            if pctl.playerCommandReady:
                pctl.playerCommandReady = False

                # Here we process commands from the main thread/module

                # Possible commands:

                # open:     Start playback of a file
                #           Path given by pctl.target_open at position pctl.start_time_target + pctl.jump_time
                #           todo: use a crossfade from previous if self.playerSubCommand != "now"
                #                 of duration prefs.cross_fade_time (but still use gapless if near end of track)
                # stop:     Stop playback (Implies release file)
                #           todo: use a fade if prefs.use_pause_fade of duration prefs.pause_fade_time
                # runstop:  Stop playback but let finish if we are near the end of the file
                # pauseon:  Pause playback (be ready to resume)
                #           todo: use a fade if prefs.use_pause_fade of duration prefs.pause_fade_time
                # pauseoff: Resume playback if paused
                #           todo: use a fade if prefs.use_pause_fade of duration prefs.pause_fade_time
                # volume:   Set to the volume specified by pctl.player_volume (0 to 100)
                #           todo: use a fade of duration prefs.change_volume_fade_time
                # seek:     Seek to position given by pctl.new_time + pctl.start_time (don't resume playback if paused)
                # url:      Start playback of a shoutcast/icecast stream. URL specified by pctl.url
                #           todo: start recording if pctl.record_stream  (rec button is current disabled for GST in UI)
                #                 encode to OGG and output file to prefs.encoder_output
                #                 automatically name files and split on metadata change
                # unload:   Stop, cleanup and exit thread
                # done:     Tell the main thread we finished doing a special request it was waiting for (such as unload)
                #
                # encstart:  todo: Start a icecast/shoutcast style HTTP stream
                #                  Given file from pctl.target_open
                #                  Starting position given by pctl.b_start_time
                #                  Title given by pctl.broadcast_line
                #                  INCREMENT pctl.broadcast_time with time
                # encseek:   todo: Seek to postion pctl.b_start_time + pctl.broadcast_time
                # cast-next: todo: Switch stream to given track (same as encstart but with existing stream)
                # encstop:   todo: Stop and shut-down HTTP stream

                # Note: Although the BASS side supports end of track crossfade setting, I don't think this is necessary
                #       going forward as gapless is almost always preferable.

                # Tip: When performing actions that take a small measure of time, you can simply block the thread until
                #      done.

                # Todo: Visualisers (Hard)
                # Ideally we would want the same visual effect as the BASS based visualisers.
                # What we want to do is constantly get binned spectrum data and pass it to the UI (in certain formats).
                # Specifically, current format used with BASS module is:
                # - An FFT of (a current segment of?) raw sample data
                # - Non-complex (magnitudes of the first half of the FFT are returned)
                # - 1024 samples (returns 512 values)
                # - Combined left and right channels
                # - Binned to particular numbers of bins and passed onto UI after some scaling and truncating
                # There's also a level meter which just takes peak "level" (scaled in someway perhaps)

                pctl.download_time = 0
                url = None
                if pctl.playerCommand == 'open' and pctl.target_object:

                    track = pctl.target_object

                    if (tauon.spot_ctl.playing or tauon.spot_ctl.coasting) and not track.file_ext == "SPTY":
                        tauon.spot_ctl.control("stop")

                    # Check if the file exists, mark it as missing if not
                    if track.is_network:

                        if track.file_ext == "SPTY":
                            if self.play_state > 0:
                                self.playbin.set_state(Gst.State.READY)
                            self.play_state = 0
                            tauon.spot_ctl.play_target(track.url_key)
                            GLib.timeout_add(19, self.main_callback)
                            pctl.playerCommandReady = False
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


                    elif os.path.isfile(track.fullpath):
                        # File exists so continue
                        track.found = True
                    else:
                        # File does not exist, trigger an advance
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

                        #print(self.url)

                    if self.play_state != 0:
                        # Determine time position of currently playing track
                        current_time = self.playbin.query_position(Gst.Format.TIME)[1] / Gst.SECOND
                        current_duration = self.playbin.query_duration(Gst.Format.TIME)[1] / Gst.SECOND
                        #print("We are " + str(current_duration - current_time) + " seconds from end.")

                    # If we are close to the end of the track, try transition gaplessly
                    if self.play_state == 1 and pctl.start_time_target == 0 and pctl.jump_time == 0 and \
                            0.2 < current_duration - current_time < 5.5 and not pctl.playerSubCommand == 'now':
                        #print("Use GStreamer Gapless transition")
                        gapless = True

                    # If we are not supposed to be playing, stop (crossfade todo)
                    else:
                        self.playbin.set_state(Gst.State.READY)

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
                        self._vol.set_property('volume', 0.0)
                    else:
                        self._vol.set_property('volume', pctl.player_volume / 100)
                    #if pctl.start_time_target == 0:

                    self.playbin.set_state(Gst.State.PLAYING)
                    if pctl.jump_time == 0:
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

                        self._vol.set_property('volume', pctl.player_volume / 100)


                    if gapless:  # Hold thread while a gapless transition is in progress
                        t = 0

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
                                self.playbin.set_state(Gst.State.READY)
                                time.sleep(0.1)
                                GLib.timeout_add(19, self.main_callback)
                                pctl.playerCommandReady = False
                                return


                    add_time = max(min(self.player_timer.hit(), 3), 0)
                    if self.loaded_track:
                        star_store.add(self.loaded_track.index, add_time)

                    pctl.jump_time = 0
                    time.sleep(0.15)

                    self.loaded_track = track

                    self.check_duration()
                    self.player_timer.hit()

                elif pctl.playerCommand == 'encstart':
                    print("Start Gstreamer broadcast")

                    #self.b_pipe.set_state(Gst.State.PLAYING)
                    self.b_playbin.set_property('uri', 'file://' + urllib.parse.quote(os.path.abspath(pctl.target_open)))
                    self.b_playbin.set_state(Gst.State.PLAYING)

                    pctl.broadcast_active = True

                elif pctl.playerCommand == 'cast-next':
                    self.b_playbin.set_state(Gst.State.NULL)
                    print("castt next")
                    time.sleep(0.3)
                    # self.playbin.set_state(Gst.State.READY)
                    #time.sleep(0.15)
                    self.b_playbin.set_property('uri', 'file://' + urllib.parse.quote(os.path.abspath(pctl.target_open)))
                    self.b_playbin.set_state(Gst.State.PLAYING)

                elif pctl.playerCommand == 'url':

                    # Stop if playing or paused
                    if self.play_state == 1 or self.play_state == 2 or self.play_state == 3:
                        self.playbin.set_state(Gst.State.READY)
                        time.sleep(0.1)

                    # Open URL stream
                    self.playbin.set_property('uri', pctl.url)
                    self.playbin.set_property('volume', pctl.player_volume / 100)
                    time.sleep(0.1)
                    self.playbin.set_state(Gst.State.PLAYING)
                    self.play_state = 3
                    self.player_timer.hit()


                elif pctl.playerCommand == 'volume':

                    if tauon.spot_ctl.coasting or tauon.spot_ctl.playing:
                        tauon.spot_ctl.control("volume", int(pctl.player_volume))

                    elif self.play_state == 1 or self.play_state == 3:
                        self.playbin.set_property('volume', pctl.player_volume / 100)

                elif pctl.playerCommand == 'runstop':

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
                    pctl.playerCommand = "stopped"

                elif pctl.playerCommand == 'stop':

                    if self.play_state > 0:
                        self.playbin.set_state(Gst.State.READY)
                    self.play_state = 0
                    pctl.playerCommand = "stopped"

                elif pctl.playerCommand == 'seek':

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
                            time.sleep(0.2)


                elif pctl.playerCommand == 'pauseon':
                    self.player_timer.hit()
                    self.play_state = 2
                    self.playbin.set_state(Gst.State.PAUSED)

                elif pctl.playerCommand == 'pauseoff':
                    self.player_timer.hit()
                    self.playbin.set_state(Gst.State.PLAYING)
                    self.play_state = 1

                elif pctl.playerCommand == 'unload':
                    if self.play_state > 0:
                        self.playbin.set_state(Gst.State.NULL)
                        time.sleep(0.5)

                    self.mainloop.quit()
                    pctl.playerCommand = 'done'
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

                # Limit the jump. Timer is monotonic, but we'll double check, just in case.
                if add_time > 2:
                    add_time = 2
                if add_time < 0:
                    add_time = 0

                # Progress main seek head
                if self.playbin.get_state(0).state == Gst.State.PLAYING:
                    pctl.playing_time = max(0, (self.playbin.query_position(Gst.Format.TIME)[1] / Gst.SECOND) -
                                                 pctl.start_time_target)
                    pctl.decode_time = pctl.playing_time  # A difference isn't discerned in this module

                else:
                    # We're supposed to be playing but it's not? Give it a push I guess.
                    self.playbin.set_state(Gst.State.PLAYING)
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
                GLib.timeout_add(19, self.main_callback)

        def exit(self):
            pctl.playerCommand = 'done'

    player = GPlayer()

    # Notify main thread we have closed cleanly
    player.exit()
