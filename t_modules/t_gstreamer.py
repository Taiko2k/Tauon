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
from gi.repository import GObject, Gst


def player3(tauon):  # GStreamer

    class GPlayer:

        def __init__(self, tauon):

            self.pctl = tauon.pctl
            self.lfm_scrobbler = tauon.lfm_scrobbler
            self.star_store = tauon.star_store
            self.gui = tauon.gui

            # This is used to keep track of time between callbacks to progress the seek bar etc
            self.player_timer = Timer()

            Gst.init([])
            self.mainloop = GLib.MainLoop()

            self.play_state = 0  # 0 is stopped, 1 is playing, 2 is paused
            self.pl = Gst.ElementFactory.make("playbin", "player")

            GLib.timeout_add(500, self.main_callback)

            self.pl.connect("about-to-finish", self.about_to_finish)

            self.mainloop.run()

        def check_duration(self):

            # This function is to be called when loading a track
            # If the duration of track is very small such as 0, query the backend for the duration

            current_track = self.pctl.master_library[self.pctl.track_queue[self.pctl.queue_step]]

            if current_track.length < 1:

                result = self.pl.query_duration(Gst.Format.TIME)
                print(result)
                if result[0] is True:
                    print("Updating track duration")
                    current_track.length = result[1] / Gst.SECOND

                else:  # still loading? I guess we wait.
                    time.sleep(1.5)
                    result = self.pl.query_duration(Gst.Format.TIME)
                    print(result)
                    if result[0] is True:
                        print("Updating track duration")
                        current_track.length = result[1] / Gst.SECOND

        def about_to_finish(self, player):
            print("Track about to finish")

        def main_callback(self):

            self.pctl.test_progress()  # This function triggers an advance if we are near end of track

            if self.pctl.playerCommandReady:
                if self.pctl.playerCommand == 'open' and self.pctl.target_open != '':

                    # Check if the file exists, mark it as missing if not
                    if os.path.isfile(self.pctl.target_object.fullpath):
                        self.pctl.target_object.found = True
                    else:
                        self.pctl.target_object.found = False
                        print("Missing File: " + self.pctl.target_object.fullpath)
                        self.pctl.playing_state = 0
                        self.pctl.jump_time = 0
                        self.pctl.advance(inplace=True, nolock=True)
                        GLib.timeout_add(19, self.main_callback)
                        return

                    # Determine time position of currently playing track
                    current_time = self.pl.query_position(Gst.Format.TIME)[1] / Gst.SECOND
                    current_duration = self.pl.query_duration(Gst.Format.TIME)[1] / Gst.SECOND
                    print("We are " + str(current_duration - current_time) + " seconds from end.")

                    # If we are close to the end of the track, try transition gaplessly
                    gapless = False
                    if self.play_state == 1 and self.pctl.start_time == 0 and self.pctl.jump_time == 0 and \
                            0.2 < current_duration - current_time < 4.5:
                        print("Use GStreamer Gapless transition")
                        gapless = True

                    # Otherwise we stop or if paused
                    else:
                        self.pl.set_state(Gst.State.READY)

                    self.play_state = 1
                    self.pl.set_property('uri', 'file://' + urllib.parse.quote(os.path.abspath(self.pctl.target_open)))
                    self.pl.set_property('volume', self.pctl.player_volume / 100)
                    self.pl.set_state(Gst.State.PLAYING)
                    if self.pctl.jump_time == 0:
                        self.pctl.playing_time = 0

                    time.sleep(0.1)  # Setting and querying position right away seems to fail, so wait a small moment

                    # Due to CUE sheets, the position to start is not always the beginning of the file
                    if self.pctl.start_time > 0 or self.pctl.jump_time > 0:
                        self.pl.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                            (self.pctl.start_time + self.pctl.jump_time) * Gst.SECOND)
                        self.pctl.playing_time = self.pctl.jump_time
                        self.gui.update = 1


                    if gapless:  # Hold thread while a gapless transition is in progress
                        t = 0
                        while self.pl.query_position(Gst.Format.TIME)[1] / Gst.SECOND >= current_time > 0:
                            time.sleep(0.1)
                            t += 1
                            if t > 40:
                                print("Gonna stop waiting...")  # Cant wait forever
                                break

                    self.pctl.jump_time = 0
                    time.sleep(0.15)
                    self.check_duration()

                    self.player_timer.hit()

                    # elif self.pctl.playerCommand == 'url':
                    #
                    #    # Stop if playing or paused
                    #    if self.play_state == 1 or self.play_state == 2:
                    #        self.pl.set_state(Gst.State.NULL)
                    #
                    #
                    #        self.pl.set_property('uri', self.pctl.url)
                    #        self.pl.set_property('volume', self.pctl.player_volume / 100)
                    #        self.pl.set_state(Gst.State.PLAYING)
                    #        self.play_state = 3
                    #        self.player_timer.hit()

                elif self.pctl.playerCommand == 'volume':
                    if self.play_state == 1:
                        self.pl.set_property('volume', self.pctl.player_volume / 100)

                elif self.pctl.playerCommand == 'stop':
                    if self.play_state > 0:
                        self.pl.set_state(Gst.State.READY)
                    self.play_state = 0

                elif self.pctl.playerCommand == 'seek':
                    if self.play_state > 0:
                        self.pl.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                            (self.pctl.new_time + self.pctl.start_time) * Gst.SECOND)

                elif self.pctl.playerCommand == 'pauseon':
                    self.player_timer.hit()
                    self.play_state = 2
                    self.pl.set_state(Gst.State.PAUSED)

                elif self.pctl.playerCommand == 'pauseoff':
                    self.player_timer.hit()
                    self.pl.set_state(Gst.State.PLAYING)
                    self.play_state = 1

                self.pctl.playerCommandReady = False

            if self.play_state == 1:

                # Get jump in time since last call
                add_time = self.player_timer.hit()

                # Limit the jump. (A huge jump in time could come if the user changes the system clock.)
                if add_time > 2:
                    add_time = 2
                if add_time < 0:
                    add_time = 0

                # Progress main seek head
                self.pctl.playing_time += add_time

                # We could get the seek bar to absolutely what the backend gives us... causes problems?
                # Like, if the playback stalls, the advance will never trigger, so we would need to detect that
                # then manually progress the playing time or trigger an advance.
                # This is what the BASS backend currently does.

                # self.pctl.playing_time = self.pctl.start_time + (self.pl.query_position(Gst.Format.TIME)[1] / Gst.SECOND)

                # Other things we need to progress such as scrobbling
                self.pctl.a_time += add_time
                self.pctl.total_playtime += add_time
                self.lfm_scrobbler.update(add_time)

                # Update track play count
                if len(self.pctl.track_queue) > 0 and 2 > add_time > 0:
                    self.star_store.add(self.pctl.track_queue[self.pctl.queue_step], add_time)

            # if self.play_state == 3:   #  URL Mode
            #    # Progress main seek head
            #    add_time = self.player_timer.hit()
            #    self.pctl.playing_time += add_time

            if not self.pctl.running:
                print("quit")
                if self.play_state > 0:
                    self.pl.set_state(Gst.State.NULL)
                    time.sleep(0.5)

                self.mainloop.quit()
                self.pctl.playerCommand = 'done'

            else:
                GLib.timeout_add(19, self.main_callback)

        def exit(self):
            self.pctl.playerCommand = 'done'

    player = GPlayer(tauon)

    # Notify main thread we have closed cleanly
    player.exit()

