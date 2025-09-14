"""Tauon Music Box - Spotify module"""

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


from __future__ import annotations

import io
import logging
import os
import subprocess
import time
import webbrowser
from typing import TYPE_CHECKING

import requests

from tauon.t_modules.t_draw import QuickThumbnail
from tauon.t_modules.t_extra import Timer

if TYPE_CHECKING:
	from tekore._auth.refreshing import RefreshingCredentials
	from tekore._client.full import Spotify
	from tekore._model.album.full import FullAlbum

	from tauon.t_modules.t_main import Strings, Tauon, TrackClass

tekore_imported = False
try:
	import tekore as tk
except ModuleNotFoundError:
	logging.warning("Unable to import Tekore, Spotify support will be disabled.")
except Exception:
	logging.exception("Unkown error trying to import Tekore, Spotify support will be disabled.")
else:
	tekore_imported = True

class SpotCtl:

	def __init__(self, tauon: Tauon) -> None:
		self.tauon                   = tauon
		self.strings                 = tauon.strings
		self.show_message            = tauon.show_message
		self.start_timer             = Timer()
		self.status:             int = 0
		self.spotify: Spotify | None = None
		self.loaded_art:         str = ""
		self.playing:           bool = False
		self.coasting:          bool = False
		self.paused:            bool = False
		self.token = None
		self.cred: RefreshingCredentials | None = None
		self.started_once:                 bool = False
		# https://developer.spotify.com/documentation/web-api/concepts/redirect_uri
		self.redirect_uri:                  str = "http://127.0.0.1:7811/spotredir"
		self.current_imports:              dict = {}
		self.spotify_com:                  bool = False
		self.sender = None
		self.cache_saved_albums:      list[str] = []
		self.scope:              str = "user-read-private user-read-playback-position streaming user-modify-playback-state user-library-modify user-library-read user-read-currently-playing user-read-playback-state playlist-read-private playlist-modify-private playlist-modify-public"
		self.launching_spotify: bool = False
		self.preparing_spotify: bool = False
		self.progress_timer:   Timer = Timer()
		self.update_timer:     Timer = Timer()

		self.token_path = self.tauon.user_directory / "spot-token-pkce"
		self.pkce_code = None
		self.local: bool = True
		self.country = None

		self.coast_context: str = ""

	def prep_cred(self) -> RefreshingCredentials:
		if not tekore_imported:
			self.show_message(_("Dependency Tekore not found"), mode="warning")
		rc = tk.RefreshingCredentials
		secret = self.tauon.prefs.spot_secret
		if not secret or len(self.tauon.prefs.spot_secret) != 32:
			secret = None
		return rc(client_id=self.tauon.prefs.spot_client, client_secret=secret, redirect_uri=self.redirect_uri)

	def connect(self) -> None:
		if not self.tauon.prefs.spotify_token or not self.tauon.prefs.spot_mode:
			return
		if len(self.tauon.prefs.spot_client) != 32:
			return
		if self.cred is None:
			self.cred = self.prep_cred()
		if self.spotify is None:
			if self.token is None:
				self.load_token()
			if self.token:
				logging.info("Init spotify support")
				self.sender = tk.RetryingSender(retries=3)
				self.spotify = tk.Spotify(self.token, sender=self.sender)
				self.country = self.spotify.current_user().country

	def paste_code(self, code: str) -> None:
		if self.cred is None:
			self.cred = self.prep_cred()

		if self.pkce_code:
			self.token = self.cred.request_pkce_token(code.strip().strip("\n"), self.pkce_code)
		else:
			self.token = self.cred.request_user_token(code.strip().strip("\n"))


		if self.token:
			self.save_token()
			self.show_message(self.strings.spotify_account_connected, mode="done")
		self.tauon.prefs.spot_mode = True

	def save_token(self) -> None:

		if self.token:
			f = self.token_path.open("w", encoding="utf-8")
			f.write(str(self.token.refresh_token))
			f.close()
			self.tauon.prefs.spotify_token = str(self.token.refresh_token)

	def load_token(self) -> None:
		if self.token_path.is_file():
			f = self.token_path.open()
			self.tauon.prefs.spotify_token = f.read().replace("\n", "").strip()
			f.close()

		if self.tauon.prefs.spotify_token:

			secret = self.tauon.prefs.spot_secret
			if not secret or len(self.tauon.prefs.spot_secret) != 32:
				secret = None

			try:
				if secret:
					self.token = tk.refresh_user_token(self.tauon.prefs.spot_client, secret, self.tauon.prefs.spotify_token)
				else:
					self.token = tk.refresh_pkce_token(self.tauon.prefs.spot_client, self.tauon.prefs.spotify_token)
			except Exception:
				logging.exception("FAILED TO LOAD TOKEN")
				raise
				self.show_message(_("Please re-authenticate Spotify in settings"))
				self.tauon.prefs.spotify_token = ""
		else:
			self.show_message(_("Please authenticate Spotify in settings"))

	def delete_token(self) -> None:
		self.tauon.prefs.spotify_token = ""
		self.token = None
		if self.token_path.exists():
			self.token_path.unlink()

	def auth(self) -> None:
		if not tekore_imported:
			self.show_message(
				_("python-tekore not installed"),
				_("If you installed via AUR, you'll need to install this optional dependency, then restart Tauon."), mode="error")
			return
		if len(self.tauon.prefs.spot_client) != 32:
			self.show_message(_("Invalid client ID. See Spotify tab in settings."), mode="error")
			return
		if self.cred is None:
			self.cred = self.prep_cred()

		secret = self.tauon.prefs.spot_secret
		if not secret or len(self.tauon.prefs.spot_secret) != 32:
			secret = None

		if not secret:
			logging.info("Using PKCE auth")
			url, self.pkce_code = self.cred.pkce_user_authorisation(scope=self.scope)
		else:
			logging.info("Using user auth")
			self.pkce_code = None
			url = self.cred.user_authorisation_url(scope=self.scope)
		webbrowser.open(url, new=2, autoraise=True)

	def control(self, command: str, param: str | int | None = None) -> None:
		if not self.spotify:
			return

		try:
			if command == "pause" and (self.playing or self.coasting) and not self.paused:
				self.spotify.playback_pause()
				self.paused = True
				self.start_timer.set()
			elif command == "stop" and (self.playing or self.coasting):
				self.paused = False
				self.playing = False
				self.coasting = False
				self.spotify.playback_pause()
				self.start_timer.set()
			elif command == "resume" and (self.coasting or self.playing) and self.paused:
				self.spotify.playback_resume()
				self.paused = False
				self.progress_timer.set()
				self.start_timer.set()
			elif param is None:
				logging.error(f"Passed a command {command} requiring a parameter but did not pass the parameter!")
				return
			elif command == "volume" and type(param) is int:
				self.spotify.playback_volume(param)
			elif command == "seek" and type(param) is int:
				self.spotify.playback_seek(param)
				self.start_timer.set()
			elif command == "next" and type(param) is str:
				self.spotify.playback_next(param)
				#self.start_timer.set()
			elif command == "previous" and type(param) is str:
				self.spotify.playback_previous(param)
				#self.start_timer.set()
			else:
				logging.error(f"Passed an invalid command {command}!")
				return

		except Exception as e:
			logging.exception("Control failure")
			#logging.info(repr(e))
			if "No active device found" in repr(e):
				try:
					tr = self.tauon.pctl.playing_object()
					if command == "resume" and tr and tr.file_ext == "SPTY" and tr.url_key:
						self.show_message("Resuming Spotify playback")
						p = self.tauon.pctl.playing_time
						self.play_target(tr.url_key, p)
						self.tauon.gui.message_box = False
						self.tauon.gui.update += 1
						return
				except Exception:
					logging.exception("Control failure handling failure")
				self.show_message(_("It looks like there are no more active Spotify devices"))

	def get_username(self) -> str | None:
		self.connect()
		if not self.spotify:
			return None
		c = self.spotify.current_user()
		if c and c.id:
			return c.id
		return None

	def add_album_to_library(self, url: str) -> None:
		self.connect()
		if not self.spotify:
			return

		id = url.strip("/").split("/")[-1]

		try:
			self.spotify.saved_albums_add([id])
			if url not in self.cache_saved_albums:
				self.cache_saved_albums.append(url)
		except Exception:
			logging.exception("Error saving album")

	def remove_album_from_library(self, url: str) -> None:

		self.connect()
		if not self.spotify:
			return
		id = url.strip("/").split("/")[-1]

		try:
			self.spotify.saved_albums_delete([id])
			if url in self.cache_saved_albums:
				self.cache_saved_albums.remove(url)
		except Exception:
			logging.exception("Error removing album")

	def get_album_url_from_local(self, track_object: TrackClass) -> str | None:

		if "spotify-album-url" in track_object.misc:
			return track_object.misc["spotify-album-url"]

		self.connect()
		if not self.spotify:
			return None

		results = self.spotify.search(track_object.artist + " " + track_object.album, types=("album",), limit=1)
		for album in results[0].items:
			if "spotify" in album.external_urls:
				return album.external_urls["spotify"]

		return None

	def get_artist_url_from_local(self, track_object: TrackClass) -> str | None:

		if "spotify-artist-url" in track_object.misc:
			return track_object.misc["spotify-artist-url"]

		self.connect()
		if not self.spotify:
			return None

		results = self.spotify.search(track_object.artist, types=("artist",), limit=1) #+ " " + track_object.album
		for artist in results[0].items:
			if "spotify" in artist.external_urls:
				if artist.name.lower() not in track_object.artist.lower():
					return None
				return artist.external_urls["spotify"]

		return None

	def import_all_playlists(self) -> None:

		self.spotify_com = True

		playlists = self.get_playlist_list()
		if playlists:
			for item in playlists:
				self.playlist(item[1], silent=True)
				self.tauon.gui.update += 1
				time.sleep(0.1)

		self.spotify_com = False
		if not playlists:
			self.show_message(self.strings.spotify_need_enable)
			return
		self.show_message(self.strings.spotify_import_complete, mode="done")

	def get_playlist_list(self) -> list[tuple[str, str]] | None:
		self.connect()
		if not self.spotify:
			self.show_message(self.strings.spotify_need_enable)
			return None

		playlists: list[tuple[str, str]] = []
		results = self.spotify.playlists(self.spotify.current_user().id)
		pages = self.spotify.all_pages(results)
		for page in pages:
			items = page.items
			for item in items:
#				if item is None:
#					logging.debug("Playlist item is None?")
#					continue
				name = item.name
				url = item.external_urls["spotify"]
				playlists.append((name, url))

		return playlists

	def search(self, text: str) -> list[TrackClass] | None:
		self.connect()
		if not self.spotify:
			return None

		results = self.spotify.search(
			text,
			types=("artist", "album", "track"),
			limit=20,
		)

		finds = []

		self.tauon.quickthumbnail.queue.clear()

		if results[0]:
			for i, album in enumerate(results[0].items[1:]):
				if hasattr(album, "album"):
					album = album.album

				img = QuickThumbnail(self.tauon)
				img.url = album.images[-1].url
				img.size = round(50 * self.tauon.gui.scale)
				self.tauon.quickthumbnail.items.append(img)
				if i < 10:
					self.tauon.quickthumbnail.queue.append(img)
				try:
					self.tauon.gall_ren.lock.release()
				except Exception:
					logging.exception("Failed releasing lock!")

				finds.append((11, (album.name, album.artists[0].name), album.external_urls["spotify"], 0, 0, img))

			for artist in results[1].items[0:1]:
				finds.insert(1, (10, artist.name, artist.external_urls["spotify"], 0, 0, None))
			for artist in results[1].items[1:2]:
				finds.insert(11, (10, artist.name, artist.external_urls["spotify"], 0, 0, None))

			for track in results[2].items[0:1]:
				finds.insert(2, (12, (track.name, track.artists[0].name), track.external_urls["spotify"], 0, 0, None))
			for track in results[2].items[5:6]:
				finds.insert(8, (12, (track.name, track.artists[0].name), track.external_urls["spotify"], 0, 0, None))

		return finds


	def search_track(self, track: TrackClass | None) -> None:
		"""Search track on Spotify - returning results is unimplemented"""
		if track is None:
			return

		self.connect()
		if not self.spotify:
			return

		if track.artist and track.title:
			results = self.spotify.search(
				track.artist + " " + track.title,
				types=("track",),
				limit=1,
			)

	def prime_device(self) -> bool | int | None:
		self.connect()
		if not self.spotify:
			return None

		logging.info("Get devices...")
		devices = self.spotify.playback_devices()
		logging.info("Devices found:")
		for device in devices:
			logging.info(f" -- Device name: {device.name}, type: {device.type}, is active: {device.is_active}")

		if devices:
			pass
		else:
			logging.warning("No spotify devices found")

		if not devices:
			return False
		for d in devices:
			if d.is_active:
				return None
		for d in devices:
			if not d.is_restricted:
				return d.id
		return None

	def transfer_to_tauon(self, wait: int = 7) -> None:
		self.preparing_spotify = True
		self.connect()
		if not self.spotify:
			self.preparing_spotify = False
			return

		time.sleep(wait)
		p = self.spotify.playback()
		if not p or not p.is_playing:
			self.show_message(_("Nothing playing"))
			self.preparing_spotify = False
			return

		devices = self.spotify.playback_devices()
		for d in devices:
			if d.name == "Tauon Music Box":
				self.spotify.playback_transfer(d.id, True)
				logging.info("Found Tauon Spotify player")
				break
		else:
			self.show_message(_("Error - Tauon device not found"))

		self.preparing_spotify = False

	def play_target(self, id: int, force_new_device: bool = False, start_time: int | None = 0, start_callback=None):

		start_time = None if not start_time else int(start_time * 1000)

		self.coasting = False
		self.connect()
		if not self.spotify:
			self.preparing_spotify = False
			self.show_message(
				_("Error. You may need to click Authorise in Settings > Accounts > Spotify."), mode="warning")
			return

		logging.info("Want play spotify target " + str(id))
		# Sort devices
		start_new_device = False
		done = False

		logging.info("Get devices...")
		devices = self.spotify.playback_devices()
		logging.info("Devices found:")
		if devices:
			for device in devices:
				logging.info(f" -- Device name: {device.name}, type: {device.type}, is active: {device.is_active}")

		d_id = None
		if not devices or force_new_device:
			logging.info("No devices found...")
			start_new_device = True
		else:
			for device in devices:
				if not device.is_restricted and device.is_active:
					logging.info("Choosing the active device: " + device.name)
					d_id = device.id
					break
			else:
				for device in devices:
					if not device.is_restricted:
						logging.info("Found a device, but its not active...")
						logging.info("Try start track on: " + device.name)
						d_id = device.id

						self.spotify.playback_transfer(device.id)
						time.sleep(0.2)
						self.spotify.playback_start_tracks([id], device_id=d_id, position_ms=start_time)
						tries = 0
						while True:
							result = self.spotify.playback_currently_playing()
							if result and result.is_playing:
								done = True
								self.progress_timer.set()
								logging.info("Looks like starting on that device worked...")
								break
							time.sleep(1)
							tries += 1
							logging.info("Not playing on that inactive device yet, waiting...")
							if tries > 5:
								break

					if d_id or start_new_device or done:
						break

		if not d_id and not start_new_device:
			logging.info("Internal logic error, aborting.")
			return


		#if self.tauon.pctl.playing_state == 1 and self.playing and self.tauon.pctl.playing_time
		#try:
		if start_new_device:
			#if not force_new_device:
			logging.info("Launch new device...")

			self.tauon.gui.update += 1

			logging.info("Initiate device...")
			if self.tauon.prefs.launch_spotify_web:
				logging.info("Open web player...")
				self.launching_spotify = True
				webbrowser.open("https://open.spotify.com/", new=2, autoraise=False)
				tries = 0
				while True:
					time.sleep(2)
					if tries == 0:
						self.tauon.focus_window()
					devices = self.spotify.playback_devices()
					if devices:
						self.progress_timer.set()
						self.spotify.playback_start_tracks([id], device_id=devices[0].id, position_ms=start_time)
						break
					tries += 1
					if tries > 13:
						self.tauon.pctl.stop()
						self.show_message(self.strings.spotify_error_starting, mode="error")
						self.launching_spotify = False
						self.preparing_spotify = False
						self.tauon.gui.update += 1
						return
			else:

				if self.tauon.prefs.launch_spotify_local:
					self.preparing_spotify = True
					logging.info("Queue start librespot...")
					self.tauon.thread_manager.ready_playback()
					self.tauon.pctl.playerCommand = "spotcon"
					self.tauon.pctl.playerCommandReady = True
					if start_callback:
						logging.info("Callback start librespot")
						start_callback()

					#self.tauon.pctl.playing_state = 3
				elif self.tauon.msys:
					self.launching_spotify = True
					p = os.getenv("APPDATA") + "\\Spotify\\Spotify.exe"
					if not os.path.isfile(p):
						self.launching_spotify = False
						self.preparing_spotify = False
						logging.info("Spotify app exe not found, aborting.")
						return
					subprocess.Popen([p])
					logging.info("Launching spotify app exe")
					time.sleep(3)
				else:
					self.launching_spotify = True
					subprocess.run(["xdg-open", "spotify:track"], check=True)
					time.sleep(3)
					logging.info("Launched spotify app via URI")

				time.sleep(0.5)
				tries = 0

				while True:
					logging.info("Waiting for device ready... try: " + str(tries + 1))
					devices = self.spotify.playback_devices()
					if devices and tries < 13:
						logging.info("Devices found:")
						for device in devices:
							logging.info(f" -- Device name: {device.name}, type: {device.type}, is active: {device.is_active}")

						if not self.tauon.prefs.launch_spotify_local:
							self.tauon.focus_window()
						time.sleep(0.5)
						logging.info(f"Selecting device: {devices[0].name}")

						logging.info("Attempt start track...")
						try:
							self.spotify.playback_start_tracks([id], device_id=devices[0].id, position_ms=start_time)
						except Exception:
							logging.exception("Failed to start playback!")
							time.sleep(1)
							tries += 2
							continue
						while True:
							result = self.spotify.playback_currently_playing()
							if result and result.is_playing:
								done = True
								self.progress_timer.set()
								logging.info("Looks like its playing now")
								break
							time.sleep(1)
							tries += 1
							logging.info("Not playing yet, waiting...")
							if tries > 13:
								break

					if done:
						break
					tries += 1
					if tries > 13:
						logging.info("Too many retries, aborting.")
						self.tauon.pctl.stop()
						self.show_message(self.strings.spotify_error_starting, mode="error")
						self.launching_spotify = False
						self.preparing_spotify = False
						self.tauon.gui.update += 1
						return
					time.sleep(1)

			self.launching_spotify = False
			self.preparing_spotify = False
			self.tauon.gui.update += 1

		elif not done:
			#logging.info(d_id)
			logging.info("A ready device is present...")
			try:
				self.progress_timer.set()
				okay = False

				# Check conditions for a proper transition
				if self.playing:
					#logging.info("already playing")
					result = self.spotify.playback_currently_playing()
					if result and result.item and result.is_playing:
						remain = result.item.duration_ms - result.progress_ms
						if 1400 < remain < 3500:
							logging.info("We are close to the end of the current track, queuing next.")
							self.spotify.playback_queue_add("spotify:track:" + id,  device_id=d_id)
							okay = True
							logging.info("Waiting for remainder of track...")
							time.sleep(remain / 1000)
							self.progress_timer.set()
							time.sleep(2)
							result = self.spotify.playback_currently_playing()
							if not (result and result.item and result.is_playing):
								logging.info("The queue transition failed")
								okay = False

				# Force a transition
				if not okay:
					logging.info("Starting track on live device.")
					self.spotify.playback_start_tracks([id], device_id=d_id, position_ms=start_time)

			# except tk.client.decor.error.InternalServerError:
			#	 self.show_message("Spotify server error. Maybe try again later.")
			#	 return
			except Exception as e:
				logging.exception("Start track on device failed, aborting")
				self.launching_spotify = False
				self.preparing_spotify = False
				self.show_message("Spotify error, try again?", str(e), mode="warning")
				return

		# except Exception as e:
		#	 logging.exception("Failure. Do you have playback started somewhere?")
		#	 self.show_message("Error. Do you have playback started somewhere?", mode="error")
		logging.info("Done")
		self.playing = True
		self.started_once = True
		self.launching_spotify = False
		self.preparing_spotify = False
		self.start_timer.set()
		self.tauon.pctl.playing_time = 0
		self.tauon.pctl.decode_time = 0
		self.tauon.gui.pl_update += 1
		self.tauon.thread_manager.ready_playback()


	def get_library_albums(self, return_list: bool = False) -> list | None:
		self.connect()
		if not self.spotify:
			self.spotify_com = False
			self.show_message(self.strings.spotify_need_enable)
			return []

		albums = self.spotify.saved_albums()

		playlist = []
		self.update_existing_import_list()
		self.cache_saved_albums.clear()

		pages = self.spotify.all_pages(albums)

		for page in pages:
			for a in page.items:
				self.load_album(a.album, playlist)

				if a.album.external_urls["spotify"] not in self.cache_saved_albums:
					self.cache_saved_albums.append(a.album.external_urls["spotify"])

		if return_list:
			return playlist

		self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title=self.strings.spotify_albums, playlist_ids=playlist))
		self.tauon.pctl.gen_codes[self.tauon.pl_to_id(len(self.tauon.pctl.multi_playlist) - 1)] = "sal"
		self.spotify_com = False

	def append_track(self, url: str, playlist_number: int | None = None) -> None:

		self.connect()
		if not self.spotify:
			return

		if url.startswith("spotify:track:"):
			id = url[14:]
		else:
			url = url.split("?")[0]
			id = url.strip("/").split("/")[-1]

		if playlist_number is None:
			playlist_number = self.tauon.pctl.active_playlist_viewing

		track = self.spotify.track(id, market=self.country)
		tr = self.load_track(track)
		self.tauon.pctl.master_library[tr.index] = tr
		self.tauon.pctl.multi_playlist[playlist_number].playlist_ids.append(tr.index)
		self.tauon.gui.pl_update += 1

	def append_album(self, url: str, playlist_number: int | None = None, return_list: bool = False) -> list | None:

		self.connect()
		if not self.spotify:
			return []

		if url.startswith("spotify:album:"):
			id = url[14:]
		else:
			url = url.split("?")[0]
			id = url.strip("/").split("/")[-1]

		album = self.spotify.album(id)
		playlist: list[int] = []
		self.update_existing_import_list()
		self.load_album(album, playlist)

		if return_list:
			return playlist

		if playlist_number is None:
			playlist_number = self.tauon.pctl.active_playlist_viewing

		self.tauon.pctl.multi_playlist[playlist_number].playlist_ids.extend(playlist)
		self.tauon.gui.pl_update += 1
		return None

	def playlist(self, url: str, return_list: bool = False, silent: bool = False) -> list[int] | None:

		self.connect()
		if not self.spotify:
			return []

		if url.startswith("spotify:playlist:"):
			id = url[17:]
		else:
			url = url.split("?")[0]
			if len(url) != 22:
				id = url.strip("/").split("/")[-1]
			else:
				id = url

		if len(id) != 22:
			logging.error("ID Error")
			if return_list:
				return []
			return None

		p = self.spotify.playlist(id, market=self.country)
		playlist: list[int] = []
		self.update_existing_import_list()
		pages = self.spotify.all_pages(p.tracks)
		for page in pages:
			for item in page.items:
				if type(item.track) == tk.model.FullPlaylistTrack:
					nt = self.load_track(item.track, include_album_url=True)
					self.tauon.pctl.master_library[nt.index] = nt
					playlist.append(nt.index)

		if return_list:
			return playlist

		title = p.name + " by " + p.owner.display_name
		if p.name in ("Discover Weekly", "Release Radar"):
			#self.tauon.pctl.multi_playlist[len(self.tauon.pctl.multi_playlist) - 1].hide_title = True
			title = p.name
		self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title=title, playlist_ids=playlist))

		self.tauon.pctl.gen_codes[self.tauon.pl_to_id(len(self.tauon.pctl.multi_playlist) - 1)] = f"spl\"{id}\""
		if not silent:
			self.tauon.switch_playlist(len(self.tauon.pctl.multi_playlist) - 1)

	# def rec_playlist(self, artist_url: str, track_url: str) -> None:
	#
	# 	self.connect()
	# 	if not self.spotify:
	# 		return
	#
	# 	id = artist_url.strip("/").split("/")[-1]
	# 	track_ids = None
	# 	if track_url:
	# 		track_ids = [track_url.strip("/").split("/")[-1]]
	# 	artist = self.spotify.artist(id)
	# 	recs = self.spotify.recommendations(artist_ids=[id], track_ids=track_ids, limit=25, market=self.country)
	# 	playlist = []
	# 	self.update_existing_import_list()
	# 	for t in recs.tracks:
	# 		nt = self.load_track(t, update_master_count=True, include_album_url=True)
	# 		self.tauon.pctl.master_library[nt.index] = nt
	# 		playlist.append(nt.index)
	#
	# 	self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title=artist.name + " Recs", playlist_ids=playlist))
	# 	self.tauon.switch_playlist(len(self.tauon.pctl.multi_playlist) - 1)
	# 	self.tauon.gui.message_box = False

	def artist_playlist(self, url: str) -> None:
		self.connect()
		if not self.spotify:
			return
		id = url.strip("/").split("/")[-1]
		artist = self.spotify.artist(id)
		artist_albums = self.spotify.artist_albums(id, limit=50, include_groups=["album"])
		playlist: list[int] = []
		self.update_existing_import_list()

		for a in artist_albums.items:
			full_album = self.spotify.album(a.id)
			self.load_album(full_album, playlist)

		self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title=artist.name, playlist_ids=playlist))
		self.tauon.switch_playlist(len(self.tauon.pctl.multi_playlist) - 1)
		self.tauon.gui.message_box = False

		artist_albums = self.spotify.artist_albums(id, limit=50, include_groups=["single"])
		playlist: list[int] = []
		self.update_existing_import_list()

		for a in artist_albums.items:
			full_album = self.spotify.album(a.id)
			self.load_album(full_album, playlist)

		self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title=artist.name + " Singles", playlist_ids=playlist))
		self.tauon.gui.message_box = False

	def album_playlist(self, url: str) -> None:
		l = self.append_album(url, return_list=True)
		self.tauon.pctl.multi_playlist.append(
			self.tauon.pl_gen(
				title=f"{self.tauon.pctl.get_track(l[0]).artist} - {self.tauon.pctl.get_track(l[0]).album}",
				playlist_ids=l,
				hide_title=False),
		)
		self.tauon.switch_playlist(len(self.tauon.pctl.multi_playlist) - 1)

	def update_existing_import_list(self) -> None:
		self.current_imports.clear()
		for tr in self.tauon.pctl.master_library.values():
			if "spotify-track-url" in tr.misc:
				self.current_imports[tr.misc["spotify-track-url"]] = tr

	def create_playlist(self, name: str) -> str | None:
		logging.info("Create new spotify playlist")
		self.connect()
		if not self.spotify:
			return None

		try:
			user = self.spotify.current_user()
			playlist = self.spotify.playlist_create(user.id, name, True)
			return playlist.id
		except Exception:
			logging.exception("Failed to create playlist")
			return None

	def upload_playlist(self, playlist_id: str, track_urls: list[str]) -> None:
		self.connect()
		if not self.spotify:
			return

		try:
			uris = []
			for url in track_urls:
				uris.append("spotify:track:" + url.strip("/").split("/")[-1])

			self.spotify.playlist_clear(playlist_id)
			time.sleep(0.05)
			with self.spotify.chunked(True):
				self.spotify.playlist_add(playlist_id, uris)
		except Exception:
			logging.exception("Spotify upload error!")
			self.show_message(_("Spotify upload error!"), mode="error")

	def load_album(self, album: FullAlbum, playlist: list[int] | None):
		#a = item
		album_url = album.external_urls["spotify"]
		art_url = album.images[0].url
		album_name = album.name
		total_tracks = album.total_tracks
		date = album.release_date
		album_artist = album.artists[0].name
		id = album.id
		parent = (album_artist + " - " + album_name).strip("- ")

		# logging.info(a.release_date, a.name)
		for track in album.tracks.items:

			pr = None
			if "spotify" in track.external_urls:
				pr = self.current_imports.get(track.external_urls["spotify"])
			if pr:
				new = False
				nt = pr
			else:
				new = True
				nt = self.tauon.TrackClass()
				nt.index = self.tauon.pctl.master_count

			nt.is_network = True
			nt.file_ext = "SPTY"
			nt.url_key = track.id
			if track.artists and "spotify" in track.artists[0].external_urls:
				nt.misc["spotify-artist-url"] = track.artists[0].external_urls["spotify"]
			nt.misc["spotify-album-url"] = album_url
			if "spotify" in track.external_urls:
				nt.misc["spotify-track-url"] = track.external_urls["spotify"]
			nt.artist = track.artists[0].name
			nt.album_artist = album_artist
			nt.date = date
			nt.album = album_name
			nt.disc_number = track.disc_number
			#nt.disc_total =
			nt.length = track.duration_ms / 1000
			nt.title = track.name
			nt.track_number = track.track_number
			nt.track_total = total_tracks
			nt.art_url_key = art_url
			nt.parent_folder_path = parent
			nt.parent_folder_name = parent
			if new:
				self.tauon.pctl.master_count += 1
				self.tauon.pctl.master_library[nt.index] = nt
			playlist.append(nt.index)



	def load_track(self, track: TrackClass, update_master_count: bool = True, include_album_url: bool = False) -> TrackClass:
		if "spotify" in track.external_urls:
			pr = self.current_imports.get(track.external_urls["spotify"])

		else:
			pr = False

		if pr:
			new = False
			nt = pr
		else:
			new = True
			nt = self.tauon.TrackClass()
			nt.index = self.tauon.pctl.master_count

		nt.found = False
		if track.is_playable is True or track.is_playable is None:
			nt.found = True
		nt.is_network = True
		nt.file_ext = "SPTY"
		nt.url_key = track.id
		#if new:
		if "spotify" in track.artists[0].external_urls:
			nt.misc["spotify-artist-url"] = track.artists[0].external_urls["spotify"]
		if include_album_url and "spotify-album-url" not in nt.misc:
			if "spotify" in track.album.external_urls:
				nt.misc["spotify-album-url"] = track.album.external_urls["spotify"]
		if "spotify" in track.external_urls:
			nt.misc["spotify-track-url"] = track.external_urls["spotify"]
		if track.artists[0].name:
			nt.artist = track.artists[0].name
		if track.album.artists:
			nt.album_artist = track.album.artists[0].name
		if track.album.release_date:
			nt.date = track.album.release_date
		nt.album = track.album.name
		nt.disc_number = track.disc_number
		nt.length = track.duration_ms / 1000
		nt.title = track.name
		nt.track_number = track.track_number
		# nt.track_total = total_tracks
		if track.album.images:
			nt.art_url_key = track.album.images[0].url
		parent = (nt.album_artist + " - " + nt.album).strip("- ")
		nt.parent_folder_path = parent
		nt.parent_folder_name = parent

		if update_master_count and new:
			self.tauon.pctl.master_count += 1

		return nt

	def like_track(self, tract_object: TrackClass) -> None:
		self.connect()
		if not self.spotify:
			return
		track_url = tract_object.misc.get("spotify-track-url", False)
		if track_url:
			id = track_url.strip("/").split("/")[-1]
			results = self.spotify.saved_tracks_contains([id])
			if not results or results[0] is False:
				self.spotify.saved_tracks_add([id])
				tract_object.misc["spotify-liked"] = True
				self.show_message(self.strings.spotify_like_added, mode="done")
				return
			self.show_message(self.strings.spotify_already_liked)
			return

	def unlike_track(self, tract_object: TrackClass) -> None:
		self.connect()
		if not self.spotify:
			return
		track_url = tract_object.misc.get("spotify-track-url", False)
		if track_url:
			id = track_url.strip("/").split("/")[-1]
			results = self.spotify.saved_tracks_contains([id])
			if not results or results[0] is True:
				self.spotify.saved_tracks_delete([id])
				tract_object.misc.pop("spotify-liked", None)
				self.show_message(self.strings.spotify_un_liked, mode="done")
				return
			self.show_message(self.strings.spotify_already_un_liked)
			return

	def get_library_likes(self, return_list: bool = False) -> list | None:
		self.connect()
		if not self.spotify:
			self.spotify_com = False
			self.show_message(self.strings.spotify_need_enable)
			return []

		self.update_existing_import_list()
		tracks = self.spotify.saved_tracks(market=self.country)

		playlist = []

		for tr in self.tauon.pctl.master_library.values():
			tr.misc.pop("spotify-liked", None)

		pages = self.spotify.all_pages(tracks)
		for page in pages:
			for item in page.items:
				nt = self.load_track(item.track)
				self.tauon.pctl.master_library[nt.index] = nt
				playlist.append(nt.index)
				nt.misc["spotify-liked"] = True

		if return_list:
			return playlist

		for p in self.tauon.pctl.multi_playlist:
			if p.title == self.tauon.strings.spotify_likes:
				p.playlist_ids[:] = playlist[:]
				self.spotify_com = False
				return None

		self.tauon.pctl.multi_playlist.append(
			self.tauon.pl_gen(title=self.tauon.strings.spotify_likes, playlist_ids=playlist))
		self.tauon.pctl.gen_codes[self.tauon.pl_to_id(len(self.tauon.pctl.multi_playlist) - 1)] = "slt"
		self.tauon.switch_playlist(len(self.tauon.pctl.multi_playlist) - 1)
		self.spotify_com = False
		return None

	def monitor(self) -> None:
		tr = self.tauon.pctl.playing_object()
		result = None

		# Detect if playback has resumed
		if self.playing and self.paused:
			result = self.spotify.playback_currently_playing()
			if result and result.is_playing:
				self.paused = False
				self.progress_timer.set()
				self.tauon.pctl.playing_state = 1
				self.tauon.gui.update += 1

		# Detect is playback has been modified
		elif self.playing and self.start_timer.get() > 4 and self.tauon.pctl.playing_time + 5 < tr.length:

			if not result:
				result = self.spotify.playback_currently_playing()

			# Playback has been stopped?
			if (result is None or result.item is None) or tr is None:
				self.playing = False
				self.tauon.pctl.stop()
				return
			# Playback has been paused?
			if tr and result and not result.is_playing:
				self.paused = True
				self.tauon.pctl.playing_state = 2
				self.tauon.gui.update += 1
				return
			# Something else is now playing? If so, switch into coast mode
			if result.item.name != tr.title:
				self.tauon.pctl.playing_state = 3
				self.playing = False
				self.coasting = True
				self.coast_update(result)
				self.tauon.gui.pl_update += 2
				return

			p = result.progress_ms
			if p is not None:
				#if abs(self.tauon.pctl.playing_time - (p / 1000)) > 0.4:
					# logging.info("DESYNC")
					# logging.info(abs(self.tauon.pctl.playing_time - (p / 1000)))
				self.tauon.pctl.playing_time = p / 1000
				self.tauon.pctl.decode_time = self.tauon.pctl.playing_time
				# else:
				#	 logging.info("SYNCED")

	def update(self, start: bool = False) -> None:

		if self.playing:
			self.coasting = False
			return

		self.connect()
		if not self.spotify:
			return

		result = self.spotify.playback_currently_playing()
		self.tauon.thread_manager.ready_playback()

		if self.playing or (not self.coasting and not start):
			return

		try:
			self.tauon.thread_manager.player_lock.release()
		except Exception:
			logging.exception("Failed to release lock")

		if result is None or result.is_playing is False:
			if self.coasting:

				if self.tauon.pctl.radio_image_bin:
					self.loaded_art = ""
					self.tauon.pctl.radio_image_bin.close()
					self.tauon.pctl.radio_image_bin = None
					self.tauon.dummy_track.artist = ""
					self.tauon.dummy_track.date = ""
					self.tauon.dummy_track.title = ""
					self.tauon.dummy_track.album = ""
					self.tauon.dummy_track.art_url_key = ""
					self.tauon.gui.clear_image_cache_next = True
					self.paused = True

			else:
				self.show_message(self.strings.spotify_not_playing)
			return

		self.coasting = True
		self.started_once = True
		self.tauon.pctl.playing_state = 3

		if result.is_playing:
			self.paused = False
		else:
			self.paused = True

		self.coast_update(result)

	def append_playing(self, playlist_number: int) -> None:
		if not self.coasting:
			return
		tr = self.tauon.pctl.playing_object()
		if tr and "spotify-track-url" in tr.misc:
			self.append_track(tr.misc["spotify-track-url"], playlist_number=playlist_number)

	def coast_update(self, result: dict | None) -> None:

		if result is None or result.item is None:
			logging.info("Spotify returned unknown")
			return

		self.tauon.dummy_track.artist = result.item.artists[0].name
		self.tauon.dummy_track.title = result.item.name
		self.tauon.dummy_track.album = result.item.album.name
		self.tauon.dummy_track.date = result.item.album.release_date
		self.tauon.dummy_track.file_ext = "Spotify"

		self.progress_timer.set()
		self.update_timer.set()

		d = result.item.duration_ms
		if d is not None:
			self.tauon.pctl.playing_length = d / 1000

		p = result.progress_ms
		if p is not None:
			self.tauon.pctl.playing_time = p / 1000

		self.tauon.pctl.decode_time = self.tauon.pctl.playing_time

		art_url = result.item.album.images[0].url
		self.tauon.dummy_track.url_key = result.item.id
		self.tauon.dummy_track.misc["spotify-album-url"] = result.item.album.external_urls["spotify"]
		self.tauon.dummy_track.misc["spotify-track-url"] = result.item.external_urls["spotify"]

		if art_url and self.loaded_art != art_url:
			self.loaded_art = art_url
			art_response = requests.get(art_url, timeout=10)
			if self.tauon.pctl.radio_image_bin:
				self.tauon.pctl.radio_image_bin.close()
				self.tauon.pctl.radio_image_bin = None
			self.tauon.pctl.radio_image_bin = io.BytesIO(art_response.content)
			self.tauon.pctl.radio_image_bin.seek(0)
			self.tauon.dummy_track.art_url_key = "ok"
			self.tauon.gui.clear_image_cache_next = True

		self.tauon.gui.update += 2
		self.tauon.gui.pl_update += 1

	def import_context(self) -> None:
		self.connect()
		if not self.spotify:
			return
		result = self.spotify.playback_currently_playing()
		if not result or not result.context:
			self.show_message(_("No Spotify context found"))
			return

		if result.context.type == "playlist":
				self.playlist(result.context.uri)

		if result.context.type == "album":
				self.album_playlist(result.context.uri)

		if result.context.type == "artist":
				self.artist_playlist(result.context.uri)

		self.tauon.gui.pl_update += 1
