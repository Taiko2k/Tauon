"""Tauon Music Box - Module for DBus interaction"""

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

from __future__ import annotations

import logging
import time
import urllib.parse
from typing import TYPE_CHECKING

import gi

# TODO(Martin): Bump to 4.0 - https://github.com/Taiko2k/Tauon/issues/1316
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib

from tauon.t_modules.t_extra import filename_to_metadata, star_count2

if TYPE_CHECKING:
	from gi.repository import AppIndicator3

	from tauon.t_modules.t_main import Tauon


class Gnome:

	def __init__(self, tauon: Tauon) -> None:
		self.bus_object = None
		self.tauon = tauon
		self.indicator_launched = False
		self.indicator_mode = 0
		self.update_tray_text = None
		self.tray_text = ""
		self.resume_playback = False
		self.last_playing_time: float = 0.0
		self.last_track_index: int = -1

		tauon.set_tray_icons()

	def focus(self) -> None:
		if self.bus_object is not None:
			try:
				# this is what gives us the multi media keys.
				dbus_interface = "org.gnome.SettingsDaemon.MediaKeys"
				self.bus_object.GrabMediaPlayerKeys("TauonMusicBox", 0, dbus_interface=dbus_interface)
			except Exception:
				logging.exception("Error connecting to org.gnome.SettingsDaemon.MediaKeys")

	def show_indicator(self) -> None:
		if not self.indicator_launched:
			try:
				self.start_indicator()
			except Exception:
				logging.exception("Failed to start indicator")
				self.tauon.show_message(_("Failed to start indicator"), mode="error")
		else:
			self.indicator.set_status(1)

	def hide_indicator(self) -> None:
		if self.indicator_launched:
			self.indicator.set_status(0)

	def indicator_play(self) -> None:
		if self.indicator_launched:
			self.indicator.set_icon_full(self.tauon.get_tray_icon("tray-indicator-play"), "playing")

	def indicator_pause(self) -> None:
		if self.indicator_launched:
			self.indicator.set_icon_full(self.tauon.get_tray_icon("tray-indicator-pause"), "paused")

	def indicator_stop(self) -> None:
		if self.indicator_launched:
			self.indicator.set_icon_full(self.tauon.get_tray_icon("tray-indicator-default"), "default")

	def start_indicator(self) -> None:
		pctl = self.tauon.pctl
		tauon = self.tauon

		import gi
		# TODO(Martin): Get rid of this - https://github.com/Taiko2k/Tauon/issues/1316
		gi.require_version("Gtk", "3.0")
		from gi.repository import Gtk

		try:
			gi.require_version("AyatanaAppIndicator3", "0.1")
			from gi.repository import AyatanaAppIndicator3 as AppIndicator3
		except Exception:
			logging.exception("Failed to load AyatanaAppIndicator3")
			gi.require_version("AppIndicator3", "0.1")
			from gi.repository import AppIndicator3


		self.indicator = AppIndicator3.Indicator.new("Tauon", self.tauon.get_tray_icon("tray-indicator-default"), AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
		self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)  # 1
		self.indicator.set_title(tauon.t_title)
		self.menu = Gtk.Menu()

		def restore(_) -> None:
			tauon.raise_window()

		def menu_quit(_) -> None:
			logging.info("Exit via tray")
			tauon.exit("Exit received from app indicator")
			self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)  # 0

		def play_pause(_) -> None:
			pctl.play_pause()

		def next(_) -> None:
			pctl.advance()

		def back(_) -> None:
			pctl.back()

		def update() -> None:
			# This is done polling style in a single thread because calling
			# from a different thread seems to cause text to sometimes stall

			while True:

				time.sleep(0.25)
				if tauon.tray_releases <= 0:
					tauon.tray_lock.acquire()
				tauon.tray_releases -= 1

				if pctl.playing_state in (1, 3):
					if self.indicator_mode != 1:
						self.indicator_mode = 1
						self.indicator_play()
				elif pctl.playing_state == 2:
					if self.indicator_mode != 2:
						self.indicator_mode = 2
						self.indicator_pause()
				elif self.indicator_mode != 0:
					self.indicator_mode = 0
					self.indicator_stop()

				text = ""
				if self.tauon.prefs.tray_show_title:
					tr = pctl.playing_object()
					if tr and tr.title and tr.artist:
						text = tr.artist + " - " + tr.title
					elif tr and tr.filename:
						text = tr.filename

					if pctl.playing_state == 0:
						text = ""

				if self.indicator_launched and text != self.tray_text:
					if text:
						self.indicator.set_label(" " + text, text)
						self.indicator.set_title(text)
					else:
						self.indicator.set_label("", "")
						self.indicator.set_title(tauon.t_title)
					self.tray_text = text

		item = Gtk.MenuItem(label=tauon.strings.menu_open_tauon)
		item.connect("activate", restore)
		item.show()
		self.menu.append(item)

		item = Gtk.SeparatorMenuItem()
		item.show()
		self.menu.append(item)

		item = Gtk.MenuItem(label=tauon.strings.menu_play_pause)
		item.connect("activate", play_pause)
		item.show()
		self.menu.append(item)

		item = Gtk.MenuItem(label=tauon.strings.menu_next)
		item.connect("activate", next)
		item.show()
		self.menu.append(item)

		item = Gtk.MenuItem(label=tauon.strings.menu_previous)
		item.connect("activate", back)
		item.show()
		self.menu.append(item)

		item = Gtk.SeparatorMenuItem()
		item.show()
		self.menu.append(item)

		item = Gtk.MenuItem(label=tauon.strings.menu_quit)
		item.connect("activate", menu_quit)
		item.show()
		self.menu.append(item)

		self.menu.show()

		self.indicator.set_menu(self.menu)

		self.indicator.connect("scroll-event", self.scroll)

		self.tauon.gui.tray_active = True
		self.indicator_launched = True

		import threading
		shoot = threading.Thread(target=update)
		shoot.daemon = True
		shoot.start()

	def scroll(self, indicator: AppIndicator3.Indicator, steps: int, direction: int) -> None:
		if direction == Gdk.ScrollDirection.UP:
			self.tauon.pctl.player_volume += 4
			self.tauon.pctl.player_volume = min(self.tauon.pctl.player_volume, 100)
			self.tauon.pctl.set_volume()
		if direction == Gdk.ScrollDirection.DOWN:
			if self.tauon.pctl.player_volume > 4:
				self.tauon.pctl.player_volume -= 4
			else:
				self.tauon.pctl.player_volume = 0
			self.tauon.pctl.set_volume()
		self.tauon.gui.update += 1

	def main(self) -> None:
		import dbus
		import dbus.mainloop.glib
		import dbus.service

		prefs = self.tauon.prefs
		gui = self.tauon.gui
		pctl = self.tauon.pctl
		tauon = self.tauon

		if prefs.use_tray:
			self.show_indicator()

		def on_mediakey(comes_from: str, what: str) -> None:
			if what == "Play":
				self.tauon.inp.media_key = "Play"
			elif what == "Pause":
				self.tauon.inp.media_key = "Pause"
			elif what == "Stop":
				self.tauon.inp.media_key = "Stop"
			elif what == "Next":
				self.tauon.inp.media_key = "Next"
			elif what == "Previous":
				self.tauon.inp.media_key = "Previous"
			elif what == "Rewind":
				self.tauon.inp.media_key = "Rewind"
			elif what == "FastForward":
				self.tauon.inp.media_key = "FastForward"
			elif what == "Repeat":
				self.tauon.inp.media_key = "Repeat"
			elif what == "Shuffle":
				self.tauon.inp.media_key = "Shuffle"

			if self.tauon.inp.media_key:
				gui.update = 1

		try:
			# set up the glib main loop.
			dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

			bus = dbus.Bus(dbus.Bus.TYPE_SYSTEM)
			bus_object = bus.get_object(
				"org.freedesktop.login1",
				"/org/freedesktop/login1")

			iface = dbus.Interface(
				bus_object,
				dbus_interface="org.freedesktop.login1.Manager")

			tauon.sleep_lock = iface.Inhibit("sleep", "Tauon Music Box", "Pause music on sleep", "delay")
			tauon.shutdown_lock = iface.Inhibit("shutdown", "Tauon Music Box", "Save data to disk", "delay")

			def update_play_lock() -> None:
				if prefs.block_suspend:
					if pctl.playing_state in (1, 3) and tauon.play_lock is None:
						tauon.play_lock = iface.Inhibit("idle", "Tauon Music Box", "Audio is playing", "block")
					elif pctl.playing_state not in (1, 3) and tauon.play_lock is not None:
						del tauon.play_lock
						tauon.play_lock = None
				elif tauon.play_lock is not None:
					del tauon.play_lock
					tauon.play_lock = None

			tauon.update_play_lock = update_play_lock

			def PrepareForSleep(active: int) -> None:
				if active == 1 and tauon.sleep_lock is not None:
					logging.info("System is suspending!")
					if pctl.playing_state == 3 and not tauon.spot_ctl.coasting:
						pctl.stop(block=True)
						if prefs.resume_play_wake:
							pctl.playing_state = 3
							self.resume_playback = True
					elif pctl.playing_state in (1, 3):
						tauon.pctl.pause()
						if prefs.resume_play_wake:
							self.resume_playback = True
					del tauon.sleep_lock
					tauon.sleep_lock = None

				elif active == 0 and tauon.sleep_lock is None:
					tauon.sleep_lock = iface.Inhibit("sleep", "Tauon Music Box", "Pause music on sleep", "delay")
					if self.resume_playback:
						self.resume_playback = False
						if pctl.playing_state == 3:
							pctl.playing_state = 0
							time.sleep(4)
							pctl.play()
							logging.info("Resume Radio")
						else:
							pctl.play()

			def PrepareForShutdown(active: int) -> None:
				logging.info("The system is shutting down!")
				tauon.quick_close = True
				tauon.exit("System shutdown signal received")

			iface.connect_to_signal("PrepareForSleep", PrepareForSleep)
			iface.connect_to_signal("PrepareForShutdown", PrepareForShutdown)


		except Exception:
			logging.exception("Failure to connect to login1")


		# t_bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
		# t_bus_name = dbus.service.BusName('com.github.taiko2k.tauonmb', t_bus)  # This object must be kept alive
		#
		# class T(dbus.service.Object):
		#	 @dbus.service.method(
		#		"com.github.taiko2k.tauonmb",
		#		in_signature='a{sv}', out_signature='')
		#	 def start(self, options={}) -> None:
		#		 logging.info("START")
		#
		#	 def __init__(self, object_path) -> None:
		#		 dbus.service.Object.__init__(self, t_bus, object_path, bus_name=t_bus_name)
		#
		# pctl.sgl = T("/")

		# ----------
		if prefs.enable_mpris:
			try:
				bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
				bus_name = dbus.service.BusName("org.mpris.MediaPlayer2.tauon", bus)  # This object must be kept alive

				class MPRIS(dbus.service.Object):

					def update(self, force: bool = False) -> None:
						changed = {}

						if pctl.playing_state in (1, 3):
							if self.player_properties["PlaybackStatus"] != "Playing":
								self.player_properties["PlaybackStatus"] = "Playing"
								changed["PlaybackStatus"] = self.player_properties["PlaybackStatus"]
						elif pctl.playing_state == 0:
							if self.player_properties["PlaybackStatus"] != "Stopped":
								self.player_properties["PlaybackStatus"] = "Stopped"
								changed["PlaybackStatus"] = self.player_properties["PlaybackStatus"]
						elif pctl.playing_state == 2:
							if self.player_properties["PlaybackStatus"] != "Paused":
								self.player_properties["PlaybackStatus"] = "Paused"
								changed["PlaybackStatus"] = self.player_properties["PlaybackStatus"]

						if pctl.player_volume / 100 != self.player_properties["Volume"]:
							self.player_properties["Volume"] = pctl.player_volume / 100
							changed["Volume"] = self.player_properties["Volume"]

						track = pctl.playing_object()
						if track is not None and (track.index != self.playing_index or force):
							self.playing_index = track.index
							id = f"/com/tauon/{track.index}/{abs(pctl.playlist_playing_position)}"
							if pctl.playing_state == 3:
								id = "/com/tauon/radio"

							d = {
								"mpris:trackid": dbus.ObjectPath(id),
								"mpris:length": dbus.Int64(int(pctl.playing_length * 1000000)),
								"xesam:album": track.album,
								"xesam:albumArtist": dbus.Array([track.album_artist]),
								"xesam:artist": dbus.Array([track.artist]),
								"xesam:title": track.title,
								"xesam:asText": track.lyrics,
								"xesam:autoRating": star_count2(tauon.star_store.get(track.index)),
								"xesam:composer": dbus.Array([track.composer]),
								"tauon:loved": tauon.love(False, track.index),
								# added by msmafra
								"xesam:comment": dbus.Array([track.comment]),
								"xesam:genre": dbus.Array([track.genre]),

							}
							if not track.title:
								a, t = filename_to_metadata(track.filename)
								if not track.artist:
									d["xesam:artist"] = dbus.Array([a])
								d["xesam:title"] = t

							try:
								d["xesam:url"] = "file://" + urllib.parse.quote(track.fullpath)
							except Exception:
								logging.exception("Uri encode error")

							try:
								i_path = tauon.thumb_tracks.path(track)
								if i_path is not None:
									d["mpris:artUrl"] = "file://" + urllib.parse.quote(i_path)
							except Exception:
								logging.exception("Thumbnail error")
								logging.debug(track.fullpath.encode("utf-8", "replace").decode("utf-8"))

							self.update_progress()

							self.player_properties["Metadata"] = dbus.Dictionary(d, signature="sv")
							changed["Metadata"] = self.player_properties["Metadata"]

							if pctl.playing_state == 3 and self.player_properties["CanPause"] is True:
								self.player_properties["CanPause"] = False
								self.player_properties["CanSeek"] = False
								changed["CanPause"] = self.player_properties["CanPause"]
								changed["CanSeek"] = self.player_properties["CanSeek"]
							elif pctl.playing_state == 1 and self.player_properties["CanPause"] is False:
								self.player_properties["CanPause"] = True
								self.player_properties["CanSeek"] = True
								changed["CanPause"] = self.player_properties["CanPause"]
								changed["CanSeek"] = self.player_properties["CanSeek"]

						if len(changed) > 0:
							try:
								self.PropertiesChanged("org.mpris.MediaPlayer2.Player", changed, [])
							except Exception:
								logging.exception("Error updating MPRIS")
								logging.debug(changed)
								if track is not None:
									logging.debug(track.fullpath)

					def update_progress(self) -> None:
						if pctl.repeat_mode and not pctl.album_repeat_mode and self.last_track_index == pctl.playing_object().index and pctl.playing_time < self.last_playing_time:
							self.seek_do(pctl.playing_time)

						self.last_playing_time = pctl.playing_time
						self.last_track_index = pctl.playing_object().index
						
						self.player_properties["Position"] = dbus.Int64(int(pctl.playing_time * 1000000))

					def update_shuffle(self) -> None:
						self.player_properties["Shuffle"] = pctl.random_mode
						self.PropertiesChanged("org.mpris.MediaPlayer2.Player", {"Shuffle": pctl.random_mode}, [])

					def update_loop(self) -> None:
						self.player_properties["LoopStatus"] = self.get_loop_status()
						self.PropertiesChanged("org.mpris.MediaPlayer2.Player", {"LoopStatus": self.get_loop_status()}, [])

					def __init__(self, object_path: str) -> None:
						# dbus.service.Object.__init__(self, bus_name, object_path)
						dbus.service.Object.__init__(self, bus, object_path, bus_name=bus_name)

						self.playing_index = -1

						self.root_properties = {
							"CanQuit": True,
							#'Fullscreen'
							#'CanSetFullscreen'
							"CanRaise": True,
							"HasTrackList": False,
							"Identity": tauon.t_title,
							"DesktopEntry": tauon.t_id,
							"SupportedUriSchemes": dbus.Array([dbus.String("file")]),
							"SupportedMimeTypes": dbus.Array([
								dbus.String("audio/mpeg"),
								dbus.String("audio/flac"),
								dbus.String("audio/ogg"),
								dbus.String("audio/m4a"),
							]),
						}

						self.player_properties = {
							"PlaybackStatus": "Stopped",
							"LoopStatus": self.get_loop_status(),
							"Rate": 1.0,
							"Shuffle": pctl.random_mode,
							"Volume": pctl.player_volume / 100,
							"Position": dbus.Int64(0),
							"MinimumRate": 1.0,
							"MaximumRate": 1.0,
							"CanGoNext": True,
							"CanGoPrevious": True,
							"CanPlay": True,
							"CanPause": True,
							"CanSeek": True,
							"CanControl": True,
							"Metadata": dbus.Dictionary({}, signature="sv"),
						}

					def get_loop_status(self) -> str:
						if pctl.repeat_mode:
							if pctl.album_repeat_mode:
								return "Playlist"
							return "Track"
						return "None"

					@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2")
					def Raise(self) -> None:
						gui.request_raise = True
						tauon.wake()

					@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2")
					def Quit(self) -> None:
						tauon.wake()
						tauon.exit("Exit request received from MPRIS2")

					@dbus.service.method(
						dbus_interface=dbus.PROPERTIES_IFACE,
						in_signature="ss", out_signature="v")
					def Get(self, interface_name: str, property_name: str) -> dict | None:
						if interface_name == "org.mpris.MediaPlayer2":
							#return self.GetAll(interface_name)[property_name]
							return self.root_properties[property_name]
						if interface_name == "org.mpris.MediaPlayer2.Player":
							return self.player_properties[property_name]
						return None

					@dbus.service.method(
						dbus_interface=dbus.PROPERTIES_IFACE,
						in_signature="s", out_signature="a{sv}")
					def GetAll(self, interface_name: str) -> dict:

						if interface_name == "org.mpris.MediaPlayer2":
							return self.root_properties
						if interface_name == "org.mpris.MediaPlayer2.Player":
							return self.player_properties
						return {}

					@dbus.service.method(
						dbus_interface=dbus.PROPERTIES_IFACE,
						in_signature="ssv", out_signature="")
					def Set(self, interface_name: str, property_name: str, value: str) -> None:
						if interface_name == "org.mpris.MediaPlayer2.Player":
							tauon.wake()
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

						if interface_name == "org.mpris.MediaPlayer2":
							pass

					@dbus.service.signal(
						dbus_interface=dbus.PROPERTIES_IFACE,
						signature="sa{sv}as")
					def PropertiesChanged(self, interface_name: str, change: dict, inval: list) -> None:
						pass

					@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
					def Next(self) -> None:
						tauon.wake()
						pctl.advance()

					@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
					def Previous(self) -> None:
						tauon.wake()
						pctl.back()

					@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
					def Pause(self) -> None:
						pctl.pause_only()

					@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
					def PlayPause(self) -> None:
						tauon.wake()
						if pctl.playing_state == 3:
							pctl.stop()  # Stop if playing radio
						else:
							pctl.play_pause()

					@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
					def Stop(self) -> None:
						pctl.stop()

					@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
					def Play(self) -> None:
						tauon.wake()
						pctl.play()

					@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
					def Seek(self, offset: int) -> None:
						pctl.seek_time(pctl.playing_time + (offset / 1000000))

					@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
					def SetPosition(self, id: int, position: str) -> None:
						pctl.seek_time(position / 1000000)

						self.player_properties["Position"] = dbus.Int64(int(position))
						self.Seeked(pctl.playing_time)

					@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
					def OpenUri(self, uri: str) -> None:
						tauon.wake()
						tauon.open_uri(uri)

					@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
					def LovePlaying(self) -> None:
						if not tauon.love(set=False):
							tauon.love(set=True, no_delay=True)
							self.update(True)
							gui.pl_update += 1

					@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
					def UnLovePlaying(self) -> None:
						if tauon.love(set=False):
							tauon.love(set=True, no_delay=True)
							self.update(True)
							gui.pl_update += 1

					@dbus.service.signal(dbus_interface="org.mpris.MediaPlayer2.Player")
					def Seeked(self, position: str) -> None:
						pass

					def seek_do(self, seconds: str) -> None:
						self.Seeked(dbus.Int64(int(seconds * 1000000)))

				pctl.mpris = MPRIS("/org/mpris/MediaPlayer2")

			except Exception:
				logging.exception("MPRIS2 CONNECT FAILED")

		mainloop = GLib.MainLoop()
		mainloop.run()
