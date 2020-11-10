# Tauon Music Box - Module for DBus interaction

# Copyright © 2015-2019, Taiko2k captain(dot)gxj(at)gmail.com

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


from gi.repository import GLib
import urllib.parse
from t_modules.t_extra import *


class Gnome:

    def __init__(self, tauon):

        self.bus_object = None
        self.tauon = tauon
        self.indicator_launched = False

    def focus(self):

        if self.bus_object is not None:
            try:
                # this is what gives us the multi media keys.
                dbus_interface = 'org.gnome.SettingsDaemon.MediaKeys'
                self.bus_object.GrabMediaPlayerKeys("TauonMusicBox", 0, dbus_interface=dbus_interface)
            except:
                # Error connecting to org.gnome.SettingsDaemon.MediaKeys
                pass

    def show_indicator(self):
        if not self.indicator_launched:
            try:
                self.start_indicator()
            except:
                self.tauon.gui.show_message("Failed to start indicator", mode="error")
        else:
            self.indicator.set_status(1)

    def hide_indicator(self):
        if self.indicator_launched:
            self.indicator.set_status(0)

    def start_indicator(self):

        pctl = self.tauon.pctl
        tauon = self.tauon

        import gi
        gi.require_version('AppIndicator3', '0.1')
        from gi.repository import Gtk
        from gi.repository import AppIndicator3

        icon_path = os.path.join(self.tauon.pctl.install_directory, "assets/svg/v4-f.svg")
        self.indicator = AppIndicator3.Indicator.new("Tauon", icon_path, AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)  # 1
        self.menu = Gtk.Menu()

        def restore(_):
            tauon.raise_window()

        def menu_quit(_):
            self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)  # 0
            tauon.exit()

        def play_pause(_):
            pctl.play_pause()
            #self.indicator.set_icon_full(os.path.abspath('assets/svg/v4-d.svg'), "test")

        def next(_):
            pctl.advance()

        def back(_):
            pctl.back()

        item = Gtk.MenuItem("Open Tauon Music Box")
        item.connect("activate", restore)
        item.show()
        self.menu.append(item)

        item = Gtk.SeparatorMenuItem()
        item.show()
        self.menu.append(item)

        item = Gtk.MenuItem("Play/Pause")
        item.connect("activate", play_pause)
        item.show()
        self.menu.append(item)

        item = Gtk.MenuItem("Next Track")
        item.connect("activate", next)
        item.show()
        self.menu.append(item)

        item = Gtk.MenuItem("Previous Track")
        item.connect("activate", back)
        item.show()
        self.menu.append(item)

        item = Gtk.SeparatorMenuItem()
        item.show()
        self.menu.append(item)

        item = Gtk.MenuItem("Quit")
        item.connect("activate", menu_quit)
        item.show()
        self.menu.append(item)

        self.menu.show()

        self.indicator.set_menu(self.menu)
        self.tauon.gui.tray_active = True
        self.indicator_launched = True

    def main(self):

        import dbus
        import dbus.service
        import dbus.mainloop.glib

        prefs = self.tauon.prefs
        gui = self.tauon.gui
        pctl = self.tauon.pctl
        tauon = self.tauon

        if prefs.use_tray:
            self.show_indicator()

        def on_mediakey(comes_from, what):

            if what == 'Play':
                self.tauon.inp.media_key = 'Play'
            elif what == 'Pause':
                self.tauon.inp.media_key = 'Pause'
            elif what == 'Stop':
                self.tauon.inp.media_key = 'Stop'
            elif what == 'Next':
                self.tauon.inp.media_key = 'Next'
            elif what == 'Previous':
                self.tauon.inp.media_key = 'Previous'
            elif what == 'Rewind':
                self.tauon.inp.media_key = 'Rewind'
            elif what == 'FastForward':
                self.tauon.inp.media_key = 'FastForward'
            elif what == 'Repeat':
                self.tauon.inp.media_key = 'Repeat'
            elif what == 'Shuffle':
                self.tauon.inp.media_key = 'Shuffle'

            if self.tauon.inp.media_key:
                gui.update = 1

        # set up the glib main loop.
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        if prefs.mkey:
            try:
                bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
                bus_object = bus.get_object('org.gnome.SettingsDaemon.MediaKeys',
                                            '/org/gnome/SettingsDaemon/MediaKeys')

                self.bus_object = bus_object

                # this is what gives us the multi media keys.
                dbus_interface = 'org.gnome.SettingsDaemon.MediaKeys'
                bus_object.GrabMediaPlayerKeys("TauonMusicBox", 0,
                                               dbus_interface=dbus_interface)

                # connect_to_signal registers our callback function.
                bus_object.connect_to_signal('MediaPlayerKeyPressed',
                                             on_mediakey)
            except:
                print("Could not connect to gnome media keys")

        # ----------

        # t_bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
        # t_bus_name = dbus.service.BusName('com.github.taiko2k.tauonmb', t_bus)  # This object must be kept alive
        #
        # class T(dbus.service.Object):
        #     @dbus.service.method("com.github.taiko2k.tauonmb",
        #                          in_signature='a{sv}', out_signature='')
        #     def start(self, options={}):
        #         print("START")
        #
        #     def __init__(self, object_path):
        #         dbus.service.Object.__init__(self, t_bus, object_path, bus_name=t_bus_name)
        #
        # pctl.sgl = T("/")

        # ----------
        if prefs.enable_mpris:
            try:
                bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
                bus_name = dbus.service.BusName('org.mpris.MediaPlayer2.tauon', bus)  # This object must be kept alive

                class MPRIS(dbus.service.Object):

                    def update(self, force=False):

                        changed = {}

                        if pctl.playing_state == 1 or pctl.playing_state == 3:
                            if self.player_properties['PlaybackStatus'] != 'Playing':
                                self.player_properties['PlaybackStatus'] = 'Playing'
                                changed['PlaybackStatus'] = self.player_properties['PlaybackStatus']
                        elif pctl.playing_state == 0:
                            if self.player_properties['PlaybackStatus'] != 'Stopped':
                                self.player_properties['PlaybackStatus'] = 'Stopped'
                                changed['PlaybackStatus'] = self.player_properties['PlaybackStatus']
                        elif pctl.playing_state == 2:
                            if self.player_properties['PlaybackStatus'] != 'Paused':
                                self.player_properties['PlaybackStatus'] = 'Paused'
                                changed['PlaybackStatus'] = self.player_properties['PlaybackStatus']

                        if pctl.player_volume / 100 != self.player_properties['Volume']:
                            self.player_properties['Volume'] = pctl.player_volume / 100
                            changed['Volume'] = self.player_properties['Volume']

                        if pctl.playing_object() is not None and (pctl.playing_object().index != self.playing_index or force):
                            track = pctl.playing_object()
                            self.playing_index = track.index
                            id = f"/com/tauon/{track.index}/{pctl.playlist_playing_position}"

                            d = {
                                'mpris:trackid': id,
                                'mpris:length': dbus.Int64(int(pctl.playing_length * 1000000)),
                                'xesam:album': track.album,
                                'xesam:albumArtist': dbus.Array([track.album_artist]),
                                'xesam:artist': dbus.Array([track.artist]),
                                'xesam:title': track.title,
                                'xesam:url': "file://" + urllib.parse.quote(track.fullpath),
                                'xesam:asText': track.lyrics,
                                'xesam:autoRating': star_count2(tauon.star_store.get(track.index)),
                                'xesam:composer': dbus.Array([track.composer]),
                                'tauon:loved': tauon.love(False, track.index),
                                # added by msmafra
                                'xesam:comment': dbus.Array([track.comment]),
                                'xesam:genre': dbus.Array([track.genre])

                            }

                            try:
                                i_path = tauon.thumb_tracks.path(track)
                                if i_path is not None:
                                    d['mpris:artUrl'] = 'file://' + urllib.parse.quote(i_path)
                            except Exception as e:
                                print(str(e))
                                print("Thumbnail error")
                                print(track.fullpath)

                            self.update_progress()

                            self.player_properties['Metadata'] = dbus.Dictionary(d, signature='sv')
                            changed['Metadata'] = self.player_properties['Metadata']

                            if pctl.playing_state == 3 and self.player_properties['CanPause'] is True:
                                self.player_properties['CanPause'] = False
                                self.player_properties['CanSeek'] = False
                                changed['CanPause'] = self.player_properties['CanPause']
                                changed['CanSeek'] = self.player_properties['CanSeek']
                            elif pctl.playing_state == 1 and self.player_properties['CanPause'] is False:
                                self.player_properties['CanPause'] = True
                                self.player_properties['CanSeek'] = True
                                changed['CanPause'] = self.player_properties['CanPause']
                                changed['CanSeek'] = self.player_properties['CanSeek']

                        if len(changed) > 0:
                            self.PropertiesChanged('org.mpris.MediaPlayer2.Player', changed, [])

                    def update_progress(self):
                        self.player_properties['Position'] = dbus.Int64(int(pctl.playing_time * 1000000))

                    def update_shuffle(self):
                        self.player_properties['Shuffle'] = pctl.random_mode
                        self.PropertiesChanged('org.mpris.MediaPlayer2.Player', {"Shuffle": pctl.random_mode}, [])

                    def update_loop(self):
                        self.player_properties['LoopStatus'] = self.get_loop_status()
                        self.PropertiesChanged('org.mpris.MediaPlayer2.Player', {"LoopStatus": self.get_loop_status()}, [])

                    def __init__(self, object_path):
                        # dbus.service.Object.__init__(self, bus_name, object_path)
                        dbus.service.Object.__init__(self, bus, object_path, bus_name=bus_name)

                        self.playing_index = -1

                        self.root_properties = {
                            'CanQuit': True,
                            #'Fullscreen'
                            #'CanSetFullscreen'
                            'CanRaise': True,
                            'HasTrackList': False,
                            'Identity': tauon.t_title,
                            'DesktopEntry': tauon.t_id,
                            'SupportedUriSchemes': dbus.Array([dbus.String("file")]),
                            'SupportedMimeTypes': dbus.Array([
                                 dbus.String("audio/mpeg"),
                                 dbus.String("audio/flac"),
                                 dbus.String("audio/ogg"),
                                 dbus.String("audio/m4a"),
                                 ])
                        }

                        self.player_properties = {
                            'PlaybackStatus': 'Stopped',
                            'LoopStatus': self.get_loop_status(),
                            'Rate': 1.0,
                            'Shuffle': pctl.random_mode,
                            'Volume': pctl.player_volume / 100,
                            'Position': 0,
                            'MinimumRate': 1.0,
                            'MaximumRate': 1.0,
                            'CanGoNext': True,
                            'CanGoPrevious': True,
                            'CanPlay': True,
                            'CanPause': True,
                            'CanSeek': True,
                            'CanControl': True
                        }

                    def get_loop_status(self):
                        if pctl.repeat_mode:
                            if pctl.album_repeat_mode:
                                return "Playlist"
                            return "Track"
                        return "None"

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2')
                    def Raise(self):
                        gui.request_raise = True

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2')
                    def Quit(self):
                        tauon.exit()

                    @dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
                                    in_signature='ss', out_signature='v')
                    def Get(self, interface_name, property_name):
                        if interface_name == 'org.mpris.MediaPlayer2':
                            #return self.GetAll(interface_name)[property_name]
                            return self.root_properties[property_name]
                        elif interface_name == 'org.mpris.MediaPlayer2.Player':
                            return self.player_properties[property_name]

                    @dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
                                    in_signature='s', out_signature='a{sv}')
                    def GetAll(self, interface_name):

                        if interface_name == 'org.mpris.MediaPlayer2':
                            return self.root_properties
                        elif interface_name == 'org.mpris.MediaPlayer2.Player':
                            return self.player_properties
                        else:
                            return {}

                    @dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE,
                                    in_signature='ssv', out_signature='')
                    def Set(self, interface_name, property_name, value):
                        if interface_name == 'org.mpris.MediaPlayer2.Player':
                            if property_name == "Volume":
                                pctl.player_volume = min(max(int(value * 100), 0), 100)
                                pctl.set_volume()
                                gui.update += 1
                            if property_name == "Shuffle":
                                pctl.random_mode = bool(value)
                                self.update_shuffle()
                                gui.update += 1
                            if property_name == "LoopStatus":
                                if value == "None":
                                    tauon.menu_repeat_off()
                                elif value == "Track":
                                    tauon.menu_set_repeat()
                                elif value == "Playlist":
                                    tauon.menu_album_repeat()
                                gui.update += 1

                        if interface_name == 'org.mpris.MediaPlayer2':
                            pass

                    @dbus.service.signal(dbus_interface=dbus.PROPERTIES_IFACE,
                                    signature='sa{sv}as')
                    def PropertiesChanged(self, interface_name, change, inval):
                        pass

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def Next(self):
                        pctl.advance()
                        pass

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def Previous(self):
                        pctl.back()
                        pass

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def Pause(self):
                        pctl.pause_only()

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def PlayPause(self):
                        if pctl.playing_state == 3:
                            pctl.stop()  # Stop if playing radio
                        else:
                            pctl.play_pause()

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def Stop(self):
                        pctl.stop()

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def Play(self):
                        pctl.play()

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def Seek(self, offset):
                        pctl.seek_time(pctl.playing_time + (offset / 1000000))

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def SetPosition(self, id, position):
                        pctl.seek_time(position / 1000000)

                        self.player_properties['Position'] = dbus.Int64(int(position))
                        self.Seeked(pctl.playing_time)

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def OpenUri(self, uri):
                        tauon.open_uri(uri)

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def LovePlaying(self):
                        if not tauon.love(set=False):
                            tauon.love(set=True, no_delay=True)
                            self.update(True)
                            gui.pl_update += 1

                    @dbus.service.method(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def UnLovePlaying(self):
                        if tauon.love(set=False):
                            tauon.love(set=True, no_delay=True)
                            self.update(True)
                            gui.pl_update += 1

                    @dbus.service.signal(dbus_interface='org.mpris.MediaPlayer2.Player')
                    def Seeked(self, position):
                        pass

                    def seek_do(self, seconds):
                        self.Seeked(dbus.Int64(int(seconds * 1000000)))

                pctl.mpris = MPRIS("/org/mpris/MediaPlayer2")

            except:
                print("MPRIS2 CONNECT FAILED")

        mainloop = GLib.MainLoop()
        mainloop.run()
