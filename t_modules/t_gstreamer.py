# Tauon Music Box - GStreamer backend Module

# Copyright © 2018-2019, Taiko2k captain(dot)gxj(at)gmail.com

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
from t_modules.t_extra import Timer
import gi
from gi.repository import GLib
gi.require_version('Gst', '1.0')
from gi.repository import Gst


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

            # Create main "playbin" pipeline thingy for simple playback
            self.pl = Gst.ElementFactory.make("playbin", "player")

            # Set callback for the main callback loop
            GLib.timeout_add(500, self.main_callback)

            # self.pl.connect("about-to-finish", self.about_to_finish)

            self.mainloop.run()

        def check_duration(self):

            # This function is to be called when loading a track to query for a duration of track
            # in case the tagger failed to calculate a length for the track when imported.

            # Get current playing track object from player
            current_track = pctl.playing_object()

            if current_track is not None and current_track.length < 1:

                result = self.pl.query_duration(Gst.Format.TIME)

                if result[0] is True:
                    current_track.length = result[1] / Gst.SECOND

                else:  # still loading? I guess we wait and try again.
                    time.sleep(1.5)
                    result = self.pl.query_duration(Gst.Format.TIME)

                    if result[0] is True:
                        current_track.length = result[1] / Gst.SECOND


        def main_callback(self):

            # This is the main callback function to be triggered continuously as long as application is running

            pctl.test_progress()  # This function triggers an advance if we are near end of track

            if pctl.playerCommandReady:
                pctl.playerCommandReady = False

                # Here we process commands from the main thread/module

                # Possible commands:

                # open: Start playback of a file
                #  (Path given by pctl.target_open at position pctl.start_time_target + pctl.jump_time)
                # stop: Stop playback (OK to unload file from memory)
                # runstop: Stop playback but let finish if we are near the end of the file (todo)
                # pauseon: Pause playback (be ready to resume)
                # pauseoff: Resume playback if paused
                # volume: Set (and remember) the volume specified by pctl.player_volume (0 to 100)
                # seek: Seek to position given by pctl.new_time + pctl.start_time (don't resume playback if paused)
                # url: Start playback of a shoutcast/icecast stream. URL specified by pctl.url (todo)
                # suspend: Pause and disconnect from output device (not used, playbin automatically does this)
                # unload: Cleanup and exit
                # done: Tell the main thread we finished doing a special request it was waiting for (such as unload)

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

                if pctl.playerCommand == 'open' and pctl.target_open != '':

                    # Check if the file exists, mark it as missing if not
                    if os.path.isfile(pctl.target_object.fullpath):
                        # File exists so continue
                        pctl.target_object.found = True
                    else:
                        # File does not exist, trigger an advance
                        pctl.target_object.found = False
                        print("Missing File: " + pctl.target_object.fullpath)
                        pctl.playing_state = 0
                        pctl.jump_time = 0
                        pctl.advance(inplace=True, nolock=True)
                        GLib.timeout_add(19, self.main_callback)
                        return

                    gapless = False
                    current_time = 0
                    current_duration = 0

                    if self.play_state != 0:
                        # Determine time position of currently playing track
                        current_time = self.pl.query_position(Gst.Format.TIME)[1] / Gst.SECOND
                        current_duration = self.pl.query_duration(Gst.Format.TIME)[1] / Gst.SECOND
                        print("We are " + str(current_duration - current_time) + " seconds from end.")

                    # If we are close to the end of the track, try transition gaplessly
                    if self.play_state == 1 and pctl.start_time_target == 0 and pctl.jump_time == 0 and \
                            0.2 < current_duration - current_time < 5.5:
                        print("Use GStreamer Gapless transition")
                        gapless = True

                    # If we are not supposed to be playing, stop (crossfade todo)
                    else:
                        self.pl.set_state(Gst.State.READY)

                    self.play_state = 1
                    self.pl.set_property('uri', 'file://' + urllib.parse.quote(os.path.abspath(pctl.target_open)))
                    self.pl.set_property('volume', pctl.player_volume / 100)
                    self.pl.set_state(Gst.State.PLAYING)
                    if pctl.jump_time == 0:
                        pctl.playing_time = 0

                    time.sleep(0.1)  # Setting and querying position right away seems to fail, so wait a small moment

                    # The position to start is not always the beginning of the file, so seek to position
                    if pctl.start_time_target > 0 or pctl.jump_time > 0:
                        self.pl.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                            (pctl.start_time_target + pctl.jump_time) * Gst.SECOND)
                        pctl.playing_time = 0
                        gui.update = 1

                    if gapless:  # Hold thread while a gapless transition is in progress
                        t = 0
                        while self.pl.query_position(Gst.Format.TIME)[1] / Gst.SECOND >= current_time > 0:
                            time.sleep(0.1)
                            t += 1

                            if self.pl.get_state(0).state != Gst.State.PLAYING:
                                break

                            if t > 40:
                                print("Gonna stop waiting...")  # Cant wait forever
                                break

                    pctl.jump_time = 0
                    time.sleep(0.15)
                    self.check_duration()

                    self.player_timer.hit()

                # elif pctl.playerCommand == 'url': (todo)
                #
                #    # Stop if playing or paused
                #    if self.play_state == 1 or self.play_state == 2:
                #        self.pl.set_state(Gst.State.NULL)
                #
                #    # Open URL stream
                #    self.pl.set_property('uri', pctl.url)
                #    self.pl.set_property('volume', pctl.player_volume / 100)
                #    self.pl.set_state(Gst.State.PLAYING)
                #    self.play_state = 3
                #    self.player_timer.hit()

                elif pctl.playerCommand == 'volume':
                    if self.play_state == 1:
                        self.pl.set_property('volume', pctl.player_volume / 100)

                elif pctl.playerCommand == 'stop':
                    if self.play_state > 0:
                        self.pl.set_state(Gst.State.READY)
                    self.play_state = 0

                elif pctl.playerCommand == 'seek':
                    if self.play_state > 0:
                        self.pl.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                            (pctl.new_time + pctl.start_time_target) * Gst.SECOND)

                elif pctl.playerCommand == 'pauseon':
                    self.player_timer.hit()
                    self.play_state = 2
                    self.pl.set_state(Gst.State.PAUSED)

                elif pctl.playerCommand == 'pauseoff':
                    self.player_timer.hit()
                    self.pl.set_state(Gst.State.PLAYING)
                    self.play_state = 1

            if self.play_state == 1:

                # Get jump in time since last call
                add_time = self.player_timer.hit()

                # Limit the jump. Timer is monotonic, but we'll double check, just in case.
                if add_time > 2:
                    add_time = 2
                if add_time < 0:
                    add_time = 0

                # Progress main seek head
                if self.pl.get_state(0).state == Gst.State.PLAYING:
                    pctl.playing_time = max(0, (self.pl.query_position(Gst.Format.TIME)[1] / Gst.SECOND) -
                                                 pctl.start_time_target)
                    pctl.decode_time = pctl.playing_time  # A difference isn't discerned in this module

                else:
                    # We're supposed to be playing but it's not? Give it a push I guess.
                    self.pl.set_state(Gst.State.PLAYING)
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
                print("unloading gstreamer")
                if self.play_state > 0:
                    self.pl.set_state(Gst.State.NULL)
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

