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
from gi.repository import Gst
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

            # This is used to keep track of time between callbacks to progress the seek bar
            self.player_timer = Timer()

            # This is used to keep note of what state of playing we should be in
            self.play_state = 0  # 0 is stopped, 1 is playing, 2 is paused

            # Initiate GSteamer
            Gst.init([])
            self.mainloop = GLib.MainLoop()

            # Get list of available audio device
            pctl.gst_devices = ["Auto", "PulseAudio", "ALSA", "JACK"]
            if tauon.snap_mode:
                pctl.gst_devices.remove("JACK")
                pctl.gst_devices.remove("ALSA")
            pctl.gst_outputs.clear()
            dm = Gst.DeviceMonitor()
            dm.start()
            for device in dm.get_devices():
                if device.get_device_class() == "Audio/Sink":
                    element = device.create_element(None)
                    type_name = element.get_factory().get_name()
                    device_name = element.props.device
                    display_name = device.get_display_name()

                    # This is used by the UI to present list of options to the user in audio settings
                    pctl.gst_outputs[display_name] = (type_name, device_name)
                    pctl.gst_devices.append(display_name)

            dm.stop()

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
            # bus.connect('message::warning', self.on_message)
            # bus.connect('message::eos', self.on_message)

            # Variables used with network downloading
            self.temp_id = "a"
            self.url = None
            self.dl_ready = False
            self.temp_path = ""  # Full path + filename


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

            # Start GLib mainloop
            self.mainloop.run()

        # # Used to get spectrum data and pass onto UI
        def on_message(self, bus, msg):
            struct = msg.get_structure()
            # print(struct.get_name())
            # print(struct.to_string())

            if self.play_state == 3 and struct.get_name() == "GstMessageTag":
                data = struct.get_value("taglist").get_string("title")
                if data[0]:
                    pctl.tag_meta = data[1]

            elif struct.get_name() == "GstMessageError":
                if "Connection" in struct.get_value("debug"):
                    gui.show_message("Connection error", mode="info")
            elif struct.get_name() == 'GstMessageBuffering':
                buff_percent = struct.get_value("buffer-percent")

                if buff_percent < 100 and (self.play_state == 1 or self.play_state == 3):
                    self.playbin.set_state(Gst.State.PAUSED)

                elif buff_percent == 100 and (self.play_state == 1 or self.play_state == 3):
                    self.playbin.set_state(Gst.State.PLAYING)

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


        def main_callback(self):

            # This is the main callback function to be triggered continuously as long as application is running
            if self.play_state == 1:
                pctl.test_progress()  # This function triggers an advance if we are near end of track

            if self.play_state == 3:
                pctl.radio_progress()

            if pctl.playerCommandReady:
                pctl.playerCommandReady = False

                # Here we process commands from the main thread/module

                # Possible commands:

                # open: Start playback of a file
                #  (Path given by pctl.target_open at position pctl.start_time_target + pctl.jump_time)
                # stop: Stop playback (OK to unload file from memory)
                # runstop: Stop playback but let finish if we are near the end of the file
                # pauseon: Pause playback (be ready to resume)
                # pauseoff: Resume playback if paused
                # volume: Set (and remember) the volume specified by pctl.player_volume (0 to 100)
                # seek: Seek to position given by pctl.new_time + pctl.start_time (don't resume playback if paused)
                # url: Start playback of a shoutcast/icecast stream. URL specified by pctl.url (todo)
                # suspend: Pause and disconnect from output device (not used, playbin automatically does this)
                # unload: Cleanup and exit
                # done: Tell the main thread we finished doing a special request it was waiting for (such as unload)
                # encstart: Start broadcasting given track at start time (same way as open)
                # cast-next: Switch broadcasting to given track at start time (same way as open)

                # Note that functions such as gapless playback are entirely implemented on this side.
                # We wont be told, we just guess when we need to do them and hold loop until we are done.
                # Advance will be called early for gapless, currently allotted 5 seconds (can we reduce this somehow?)
                # Concepts such as advance and back are not used on this side.

                # Todo: Visualisers
                # Uhhh, this is a bit of a can of worms. What we want to do is constantly get binned spectrum data
                # and pass it to the UI (in certain formats).
                # Specifically, current format used with BASS module is:
                # - An FFT of (a current segment of?) raw sample data
                # - Non-complex (magnitudes of the first half of the FFT are returned)
                # - 1024 samples (returns 512 values)
                # - Combined left and right channels (mono)
                # - Binned to particular numbers of bins and passed onto UI after some scaling and truncating
                # There's also a level meter which just takes peak "level" (scaled in someway perhaps)

                # Todo: User settings
                # prefs.use_transition_crossfade (if true, fade rather than transition gaplessly at end of file) todo
                # prefs.use_jump_crossfade (if true and not end of file, fade rather than switch instantly) todo
                # prefs.use_pause_fade (if true, fade when pausing, rather than pausing instantly) todo
                url = None
                if pctl.playerCommand == 'open' and pctl.target_object:

                    # Check if the file exists, mark it as missing if not
                    if pctl.target_object.is_network:
                        try:
                            url, params = pctl.get_url(pctl.target_object)
                        except:
                            time.sleep(0.1)
                            gui.show_message("Connection error", "Bad login? Server offline?", mode='info')
                            pctl.stop()
                            pctl.playerCommand = ""
                            self.main_callback()
                            return


                    elif os.path.isfile(pctl.target_object.fullpath):
                        # File exists so continue
                        pctl.target_object.found = True
                    else:
                        # File does not exist, trigger an advance
                        pctl.target_object.found = False
                        tauon.console.print("Missing File: " + pctl.target_object.fullpath, 2)
                        pctl.playing_state = 0
                        pctl.jump_time = 0
                        pctl.advance(inplace=True, nolock=True)
                        GLib.timeout_add(19, self.main_callback)
                        return

                    gapless = False
                    current_time = 0
                    current_duration = 0

                    if pctl.target_object.is_network:

                        if params:
                            self.url = url + ".view?" + urllib.parse.urlencode(params)
                        else:
                            self.url = url

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

                    if url:
                        self.playbin.set_property('uri',
                                                  self.url)
                    else:
                        # Play file on disk
                        self.playbin.set_property('uri', 'file://' + urllib.parse.quote(os.path.abspath(pctl.target_open)))
                    self._vol.set_property('volume', pctl.player_volume / 100)
                    self.playbin.set_state(Gst.State.PLAYING)
                    if pctl.jump_time == 0:
                        pctl.playing_time = 0

                    time.sleep(0.1)  # Setting and querying position right away seems to fail, so wait a small moment

                    # The position to start is not always the beginning of the file, so seek to position
                    if pctl.start_time_target > 0 or pctl.jump_time > 0:
                        self.playbin.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                            (pctl.start_time_target + pctl.jump_time) * Gst.SECOND)
                        pctl.playing_time = 0
                        gui.update = 1

                    if gapless:  # Hold thread while a gapless transition is in progress
                        t = 0
                        while self.playbin.query_position(Gst.Format.TIME)[1] / Gst.SECOND >= current_time > 0:

                            time.sleep(0.1)
                            t += 1

                            if self.playbin.get_state(0).state != Gst.State.PLAYING:
                                break

                            if t > 50:
                                print("Gonna stop waiting...")  # Cant wait forever
                                break

                            if pctl.playerCommand == 'open' and pctl.playerCommandReady:
                                # Cancel the gapless transition
                                self.playbin.set_state(Gst.State.READY)
                                time.sleep(0.1)
                                GLib.timeout_add(19, self.main_callback)
                                return


                    pctl.jump_time = 0
                    time.sleep(0.15)
                    self.check_duration()
                    self.player_timer.hit()

                # elif pctl.playerCommand == 'encstart':
                #     print("Start Gstreamer broadcast")
                #     self.b_playbin.set_property('uri', 'file://' + urllib.parse.quote(os.path.abspath(pctl.target_open)))
                #     self.b_playbin.set_state(Gst.State.PLAYING)
                #     pctl.broadcast_active = True
                #
                # elif pctl.playerCommand == 'cast-next':
                #     print("castt next")
                #     self.playbin.set_state(Gst.State.READY)
                #     time.sleep(0.15)
                #     self.b_playbin.set_property('uri', 'file://' + urllib.parse.quote(os.path.abspath(pctl.target_open)))
                #     self.b_playbin.set_state(Gst.State.PLAYING)

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
                    if self.play_state == 1 or self.play_state == 3:
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
                    if self.play_state > 0:
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
