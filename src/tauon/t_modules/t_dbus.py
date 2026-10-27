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
import select
import threading
import time
import urllib.parse
from typing import TYPE_CHECKING

import dbus
import dbus.mainloop.glib
import dbus.service

from gi.repository import GLib

from tauon.t_modules.t_enums import PlayingState  # noqa: E402
from tauon.t_modules.t_extra import filename_to_metadata, star_count2  # noqa: E402

if TYPE_CHECKING:
	from tauon.t_modules.t_main import GuiVar, PlayerCtl, Tauon


class MPRIS(dbus.service.Object):
	def __init__(self, object_path: str, tauon: Tauon) -> None:
		self.tauon: Tauon = tauon
		self.gui: GuiVar = tauon.gui
		self.pctl: PlayerCtl = tauon.pctl
		bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
		self.bus_name = dbus.service.BusName("org.mpris.MediaPlayer2.tauon", bus)  # This object must be kept alive

		# dbus.service.Object.__init__(self, bus_name, object_path)
		dbus.service.Object.__init__(self, bus, object_path, bus_name=self.bus_name)

		self.playing_index = -1
		self.last_playing_time: float = 0.0
		self.last_track_index: int = -1

		self.root_properties = {
			"CanQuit": True,
			#'Fullscreen'
			#'CanSetFullscreen'
			"CanRaise": True,
			"HasTrackList": False,
			"Identity": tauon.t_title,
			"DesktopEntry": tauon.t_id,
			"SupportedUriSchemes": dbus.Array([dbus.String("file")]),
			"SupportedMimeTypes": dbus.Array(
				[
					dbus.String("audio/mpeg"),
					dbus.String("audio/flac"),
					dbus.String("audio/ogg"),
					dbus.String("audio/m4a"),
				]
			),
		}

		self.player_properties = {
			"PlaybackStatus": "Stopped",
			"LoopStatus": self.get_loop_status(),
			"Rate": 1.0,
			"Shuffle": self.pctl.random_mode,
			"Volume": self.pctl.player_volume / 100,
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

	def update(self, force: bool = False) -> None:
		changed = {}

		if self.pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM):
			if self.player_properties["PlaybackStatus"] != "Playing":
				self.player_properties["PlaybackStatus"] = "Playing"
				changed["PlaybackStatus"] = self.player_properties["PlaybackStatus"]
		elif self.pctl.playing_state == PlayingState.STOPPED:
			if self.player_properties["PlaybackStatus"] != "Stopped":
				self.player_properties["PlaybackStatus"] = "Stopped"
				changed["PlaybackStatus"] = self.player_properties["PlaybackStatus"]
			self.player_properties["Position"] = dbus.Int64(0)
		elif self.pctl.playing_state == PlayingState.PAUSED:
			if self.player_properties["PlaybackStatus"] != "Paused":
				self.player_properties["PlaybackStatus"] = "Paused"
				changed["PlaybackStatus"] = self.player_properties["PlaybackStatus"]

		if self.pctl.player_volume / 100 != self.player_properties["Volume"]:
			self.player_properties["Volume"] = self.pctl.player_volume / 100
			changed["Volume"] = self.player_properties["Volume"]

		track = self.pctl.playing_object()
		if track is not None and (track.index != self.playing_index or force):
			self.playing_index = track.index
			id = f"/com/tauon/{track.index}/{abs(self.pctl.playlist_playing_position)}"
			if self.pctl.playing_state == PlayingState.URL_STREAM:
				id = "/com/tauon/radio"

			d = {
				"mpris:trackid": dbus.ObjectPath(id),
				"mpris:length": dbus.Int64(int(self.pctl.playing_length * 1000000)),
				"xesam:album": track.album,
				"xesam:albumArtist": dbus.Array([track.album_artist]),
				"xesam:artist": dbus.Array([track.artist]),
				"xesam:title": track.title,
				"xesam:asText": track.synced if track.synced else track.lyrics,
				"xesam:autoRating": star_count2(self.tauon.star_store.get(track.index)),
				"xesam:composer": dbus.Array([track.composer]),
				"tauon:loved": self.tauon.love(False, track.index),
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
				i_path = self.tauon.thumb_tracks.path(track)
				if i_path is not None:
					d["mpris:artUrl"] = "file://" + urllib.parse.quote(i_path)
			except Exception:
				logging.exception("Thumbnail error")
				logging.debug(track.fullpath.encode("utf-8", "replace").decode("utf-8"))

			self.update_progress()

			self.player_properties["Metadata"] = dbus.Dictionary(d, signature="sv")
			changed["Metadata"] = self.player_properties["Metadata"]

			if self.pctl.playing_state == PlayingState.URL_STREAM and self.player_properties["CanPause"] is True:
				self.player_properties["CanPause"] = False
				self.player_properties["CanSeek"] = False
				changed["CanPause"] = self.player_properties["CanPause"]
				changed["CanSeek"] = self.player_properties["CanSeek"]
			elif self.pctl.playing_state == PlayingState.PLAYING and self.player_properties["CanPause"] is False:
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
		if (
			self.pctl.repeat_mode
			and not self.pctl.album_repeat_mode
			and self.pctl.playing_object() is not None
			and self.last_track_index == self.pctl.playing_object().index
			and self.pctl.playing_time < self.last_playing_time
		):
			self.seek_do(self.pctl.playing_time)

		self.last_playing_time = self.pctl.playing_time
		self.last_track_index = self.pctl.playing_object().index

		self.player_properties["Position"] = dbus.Int64(int(self.pctl.playing_time * 1000000))

	def update_shuffle(self) -> None:
		self.player_properties["Shuffle"] = self.pctl.random_mode
		self.PropertiesChanged("org.mpris.MediaPlayer2.Player", {"Shuffle": self.pctl.random_mode}, [])

	def update_loop(self) -> None:
		self.player_properties["LoopStatus"] = self.get_loop_status()
		self.PropertiesChanged("org.mpris.MediaPlayer2.Player", {"LoopStatus": self.get_loop_status()}, [])

	def get_loop_status(self) -> str:
		if self.pctl.repeat_mode:
			if self.pctl.album_repeat_mode:
				return "Playlist"
			return "Track"
		return "None"

	@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2")
	def Raise(self) -> None:
		self.tauon.request_raise()

	@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2")
	def Quit(self) -> None:
		self.tauon.wake()
		self.tauon.exit("Exit request received from MPRIS2")

	@dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE, in_signature="ss", out_signature="v")
	def Get(self, interface_name: str, property_name: str) -> dict | None:
		if interface_name == "org.mpris.MediaPlayer2":
			# return self.GetAll(interface_name)[property_name]
			return self.root_properties[property_name]
		if interface_name == "org.mpris.MediaPlayer2.Player":
			return self.player_properties[property_name]
		return None

	@dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE, in_signature="s", out_signature="a{sv}")
	def GetAll(self, interface_name: str) -> dict:
		if interface_name == "org.mpris.MediaPlayer2":
			return self.root_properties
		if interface_name == "org.mpris.MediaPlayer2.Player":
			return self.player_properties
		return {}

	@dbus.service.method(dbus_interface=dbus.PROPERTIES_IFACE, in_signature="ssv", out_signature="")
	def Set(self, interface_name: str, property_name: str, value: str) -> None:
		if interface_name == "org.mpris.MediaPlayer2.Player":
			self.tauon.wake()
			if property_name == "Volume":
				self.pctl.player_volume = min(max(int(value * 100), 0), 100)
				self.pctl.set_volume()
				self.gui.request_frame()
			if property_name == "Shuffle":
				self.pctl.random_mode = bool(value)
				self.update_shuffle()
				self.gui.request_frame()
			if property_name == "LoopStatus":
				if value == "None":
					self.tauon.menu_repeat_off()
				elif value == "Track":
					self.tauon.menu_set_repeat()
				elif value == "Playlist":
					self.tauon.menu_album_repeat()
				self.gui.request_frame()

		if interface_name == "org.mpris.MediaPlayer2":
			pass

	@dbus.service.signal(dbus_interface=dbus.PROPERTIES_IFACE, signature="sa{sv}as")
	def PropertiesChanged(self, interface_name: str, change: dict, inval: list) -> None:
		pass

	@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
	def Next(self) -> None:
		self.tauon.wake()
		self.pctl.advance()

	@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
	def Previous(self) -> None:
		self.tauon.wake()
		self.pctl.back()

	@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
	def Pause(self) -> None:
		self.pctl.pause_only()

	@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
	def PlayPause(self) -> None:
		self.tauon.wake()
		if self.pctl.playing_state == PlayingState.URL_STREAM:
			self.pctl.stop()  # Stop if playing radio
		else:
			self.pctl.play_pause()

	@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
	def Stop(self) -> None:
		self.pctl.stop()

	@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
	def Play(self) -> None:
		self.tauon.wake()
		self.pctl.play()

	@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
	def Seek(self, offset: int) -> None:
		self.pctl.seek_time(self.pctl.playing_time + (offset / 1000000))

	@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
	def SetPosition(self, id: str, position: int) -> None:
		self.pctl.seek_time(position / 1000000)

		self.player_properties["Position"] = dbus.Int64(int(position))

	@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
	def OpenUri(self, uri: str) -> None:
		self.tauon.wake()
		self.tauon.open_uri(uri)

	@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
	def LovePlaying(self) -> None:
		if not self.tauon.love(set=False):
			self.tauon.love(set=True, no_delay=True)
			self.update(True)
			self.gui.request_tracklist_redraw()

	@dbus.service.method(dbus_interface="org.mpris.MediaPlayer2.Player")
	def UnLovePlaying(self) -> None:
		if self.tauon.love(set=False):
			self.tauon.love(set=True, no_delay=True)
			self.update(True)
			self.gui.request_tracklist_redraw()

	@dbus.service.signal(dbus_interface="org.mpris.MediaPlayer2.Player")
	def Seeked(self, position: str) -> None:
		pass

	def seek_do(self, seconds: str | float) -> None:
		self.Seeked(dbus.Int64(int(seconds * 1000000)))


PORTAL_NAME = "org.freedesktop.portal.Desktop"
PORTAL_PATH = "/org/freedesktop/portal/desktop"
PORTAL_INHIBIT_SUSPEND = 4


class SuspendInhibitor:
	"""Blocks automatic suspend while audio is playing.

	Prefers the XDG inhibit portal's Suspend flag, which leaves screen dimming
	and blanking alone. Falls back to a logind "idle" lock, which KDE also
	treats as a request to keep the screen on.
	"""

	def __init__(self) -> None:
		self.session_bus: dbus.SessionBus | None = None
		self.portal: dbus.Interface | None = None
		self.login: dbus.Interface | None = None
		self.portal_handle: str | None = None
		self.portal_match: dbus.connection.SignalMatch | None = None
		self.login_lock: dbus.types.UnixFd | None = None
		self.token_count: int = 0
		self.lock = threading.Lock()

	@property
	def available(self) -> bool:
		return self.portal is not None or self.login is not None

	def connect_portal(self) -> None:
		try:
			bus = dbus.SessionBus()
			portal_object = bus.get_object(PORTAL_NAME, PORTAL_PATH)
			# Only exported when a portal backend implements it
			portal_object.Get("org.freedesktop.portal.Inhibit", "version", dbus_interface=dbus.PROPERTIES_IFACE)
		except dbus.DBusException:
			logging.info("Inhibit portal unavailable, suspend blocking will use logind")
			return
		self.session_bus = bus
		self.portal = dbus.Interface(portal_object, dbus_interface="org.freedesktop.portal.Inhibit")

	def acquire(self) -> None:
		with self.lock:
			if self.portal_handle is not None or self.login_lock is not None:
				return
			if self.portal is not None:
				try:
					self.portal_inhibit()
					return
				except dbus.DBusException:
					logging.exception("Inhibit portal request failed, falling back to logind")
					self.drop_portal()
			self.login_inhibit()

	def release(self) -> None:
		with self.lock:
			if self.portal_handle is not None:
				try:
					request = self.session_bus.get_object(PORTAL_NAME, self.portal_handle)
					request.Close(dbus_interface="org.freedesktop.portal.Request")
				except dbus.DBusException:
					logging.exception("Failed to release the inhibit portal request")
				self.clear_portal_request()
			# logind drops the lock once its file descriptor is closed
			self.login_lock = None

	def login_inhibit(self) -> None:
		if self.login is not None:
			self.login_lock = self.login.Inhibit("idle", "Tauon Music Box", "Audio is playing", "block")

	def portal_inhibit(self) -> None:
		self.token_count += 1
		token = f"tauon_play_{self.token_count}"
		sender = self.session_bus.get_unique_name()[1:].replace(".", "_")
		path = f"{PORTAL_PATH}/request/{sender}/{token}"

		def on_response(response: int, results: dict) -> None:
			self.on_portal_response(path, response)

		# Subscribe before calling, so an immediate denial isn't missed
		self.portal_match = self.session_bus.add_signal_receiver(
			on_response,
			signal_name="Response",
			dbus_interface="org.freedesktop.portal.Request",
			path=path,
		)
		try:
			self.portal_handle = str(self.portal.Inhibit(
				"", dbus.UInt32(PORTAL_INHIBIT_SUSPEND), {"handle_token": token, "reason": "Audio is playing"}))
		except dbus.DBusException:
			self.clear_portal_request()
			raise

	def on_portal_response(self, path: str, response: int) -> None:
		# Success needs no action, the request stays open until closed
		if response == 0:
			return
		with self.lock:
			if self.portal_handle != path:
				return
			logging.warning(f"Inhibit portal denied the request ({response}), falling back to logind")
			self.drop_portal()
			self.login_inhibit()

	def clear_portal_request(self) -> None:
		if self.portal_match is not None:
			self.portal_match.remove()
			self.portal_match = None
		self.portal_handle = None

	def drop_portal(self) -> None:
		self.clear_portal_request()
		self.portal = None


class Gnome:
	def __init__(self, tauon: Tauon) -> None:
		self.bus_object = None
		self.tauon: Tauon = tauon
		self.resume_playback: bool = False
		self.thread: threading.Thread | None = None
		self.stopping: bool = False

	def stop(self, timeout: float = 2.0) -> None:
		"""Stop the D-Bus thread and wait for it to finish."""
		self.stopping = True
		if self.thread is not None and self.thread is not threading.current_thread():
			self.thread.join(timeout)

	def dispatch(self) -> None:
		"""Dispatch GLib's default main context. Main thread only.

		dbus-python's connections and the tray's GTK objects all run on this
		context, and GTK is only safe on the thread that dispatches it. SDL's
		tray pumps GTK from the main thread and assumes the context is driven
		there, so the main loop calls this every iteration instead of a second
		thread running GLib.MainLoop (which dispatched GTK off the main thread
		and crashed in cairo).
		"""
		context = GLib.MainContext.default()
		# A D-Bus message takes two passes: the socket watch reads it, then the
		# connection's dispatch source delivers it.
		for _ in range(8):
			if not context.iteration(False):
				break

	def focus(self) -> None:
		if self.bus_object is not None:
			try:
				# this is what gives us the multi media keys.
				dbus_interface = "org.gnome.SettingsDaemon.MediaKeys"
				self.bus_object.GrabMediaPlayerKeys("TauonMusicBox", 0, dbus_interface=dbus_interface)
			except Exception:
				logging.exception("Error connecting to org.gnome.SettingsDaemon.MediaKeys")

	def main(self) -> None:
		prefs = self.tauon.prefs
		gui = self.tauon.gui
		pctl = self.tauon.pctl
		tauon = self.tauon

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
				gui.request_frame()

		# set up the glib main loop.
		dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

		play_lock = SuspendInhibitor()
		play_lock.connect_portal()

		try:
			bus = dbus.Bus(dbus.Bus.TYPE_SYSTEM)
			bus_object = bus.get_object("org.freedesktop.login1", "/org/freedesktop/login1")

			iface = dbus.Interface(bus_object, dbus_interface="org.freedesktop.login1.Manager")

			tauon.sleep_lock = iface.Inhibit("sleep", "Tauon Music Box", "Pause music on sleep", "delay")
			tauon.shutdown_lock = iface.Inhibit("shutdown", "Tauon Music Box", "Save data to disk", "delay")
			play_lock.login = iface

			def PrepareForSleep(active: int) -> None:
				if active == 1 and tauon.sleep_lock is not None:
					logging.info("System is suspending!")
					if pctl.playing_state == PlayingState.URL_STREAM:
						pctl.stop(block=True)
						if prefs.resume_play_wake:
							pctl.playing_state = PlayingState.URL_STREAM
							self.resume_playback = True
					elif pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM):
						tauon.pctl.pause()
						if prefs.resume_play_wake:
							self.resume_playback = True
					del tauon.sleep_lock
					tauon.sleep_lock = None

				elif active == 0 and tauon.sleep_lock is None:
					tauon.sleep_lock = iface.Inhibit("sleep", "Tauon Music Box", "Pause music on sleep", "delay")
					if self.resume_playback:
						self.resume_playback = False
						if pctl.playing_state == PlayingState.URL_STREAM:
							pctl.playing_state = PlayingState.STOPPED
							time.sleep(4)
							pctl.play()
							logging.info("Resume Radio")
						else:
							pctl.play()

			def PrepareForShutdown(active: int) -> None:
				if active != 1:
					return
				logging.info("The system is shutting down!")
				tauon.quick_close = True
				tauon.exit("System shutdown signal received")

			iface.connect_to_signal("PrepareForSleep", PrepareForSleep)
			iface.connect_to_signal("PrepareForShutdown", PrepareForShutdown)

		except Exception:
			logging.exception("Failure to connect to login1")

		if play_lock.available:
			def update_play_lock() -> None:
				if prefs.block_suspend and pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM):
					play_lock.acquire()
				else:
					play_lock.release()

			tauon.play_lock = play_lock
			tauon.update_play_lock = update_play_lock

		# t_bus = dbus.Bus(dbus.Bus.TYPE_SESSION)
		# t_bus_name = dbus.service.BusName('com.github.taiko2k.tauonmb', t_bus)  # This object must be kept alive
		#
		# class T(dbus.service.Object):
		# @dbus.service.method(
		# "com.github.taiko2k.tauonmb",
		# in_signature='a{sv}', out_signature='')
		# def start(self, options={}) -> None:
		# logging.info("START")
		#
		# def __init__(self, object_path) -> None:
		# dbus.service.Object.__init__(self, t_bus, object_path, bus_name=t_bus_name)
		#
		# pctl.sgl = T("/")

		# ----------
		if prefs.enable_mpris:
			try:
				pctl.mpris = MPRIS("/org/mpris/MediaPlayer2", tauon)

			except Exception:
				logging.exception("MPRIS2 CONNECT FAILED")

		# The main thread dispatches the D-Bus sources (see dispatch). It idles
		# for up to a second when nothing is playing, so wake it as soon as a bus
		# socket has data, for prompt media keys and MPRIS calls.
		fds = []
		for get_bus in (dbus.SystemBus, dbus.SessionBus):
			try:
				fd = get_bus().get_unix_fd()
			except Exception:
				logging.exception("Could not get the bus socket to watch")
				continue
			if fd is not None:
				fds.append(fd)
		while not self.stopping:
			readable, _, _ = select.select(fds, [], [], 0.5)
			if readable:
				tauon.wake()
				# Let the main thread drain the socket before looking again
				time.sleep(0.03)
