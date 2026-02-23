"""Tauon Music Box - Jellyin client API module"""

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
import itertools
import json
import logging
import threading
import time
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

import requests

from tauon.t_modules.t_extra import StarRecord, Timer

if TYPE_CHECKING:
	from io import BytesIO

	from tauon.t_modules.t_extra import TauonPlaylist
	from tauon.t_modules.t_main import GuiVar, PlayerCtl, Tauon, TrackClass
	from tauon.t_modules.t_prefs import Prefs


class Jellyfin:
	def __init__(self, tauon: Tauon) -> None:
		self.tauon: Tauon = tauon
		self.gui: GuiVar = tauon.gui
		self.pctl: PlayerCtl = tauon.pctl
		self.prefs: Prefs = tauon.prefs
		self.show_message = tauon.show_message

		self.scanning: bool = False
		self.connected = False

		self.accessToken = None
		self.userId = None
		self.currentId = None

		self.session_thread_active: bool = False
		self.session_status: int = 0
		self.session_item_id: int | None = None
		self.session_update_timer: Timer = Timer()
		self.session_last_item: dict[str, list[str] | bool | int | str] | None = None
		self.playlists = []

	def _get_jellyfin_auth(self) -> str:
		auth_str = f"MediaBrowser Client={self.tauon.t_title}, Device={self.tauon.device}, DeviceId=-, Version={self.tauon.t_version}"
		if self.accessToken:
			auth_str += f", Token={self.accessToken}"
		return auth_str

	def _authenticate(self, debug: bool = False) -> None:
		username = self.prefs.jelly_username
		password = self.prefs.jelly_password
		server = self.prefs.jelly_server_url

		try:
			response = requests.post(
				f"{server}/Users/AuthenticateByName",
				headers={
					"Content-type": "application/json",
					"X-Application": self.tauon.t_agent,
					"Authorization": self._get_jellyfin_auth(),
				},
				data=json.dumps({"username": username, "Pw": password}),
				timeout=(5, 10),
			)
		except Exception:
			logging.exception(
				f"{_('Could not establish connection to server.')} {_('Check server is running and URL is correct.')}"
			)
			self.show_message(
				_("Could not establish connection to server."),
				_("Check server is running and URL is correct."),
				mode="error",
			)
			return

		if response.status_code == HTTPStatus.OK:
			info = response.json()
			self.accessToken = info["AccessToken"]
			self.userId = info["User"]["Id"]
			self.connected = True
			if debug:
				self.show_message(_("Connection and authorisation successful"), mode="done")
		elif response.status_code == HTTPStatus.UNAUTHORIZED:
			self.show_message(_("401 Authentication failed"), _("Check username and password."), mode="warning")
		else:
			self.show_message(_("Jellyfin auth error"), f"{response.status_code} {response.text}", mode="warning")

	def test(self) -> None:
		self._authenticate(debug=True)

	def resolve_stream(self, stream_id: str) -> str | tuple[str, dict]:
		if not self.connected or not self.accessToken:
			self._authenticate()

		if not self.connected:
			return ""

		base_url = f"{self.prefs.jelly_server_url}/Audio/{stream_id}/stream"
		# headers = {
		# "Token": self.accessToken,
		# "X-Application": "Tauon/1.0",
		# "x-emby-authorization": self._get_jellyfin_auth(),
		# }
		params = {
			"UserId": self.userId,
			"static": "true",
		}

		if self.prefs.network_stream_bitrate > 0:
			params["MaxStreamingBitrate"] = self.prefs.network_stream_bitrate

		if not self.session_thread_active:
			shoot = threading.Thread(target=self.session)
			shoot.daemon = True
			shoot.start()

		return base_url, params

	def get_cover(self, track: TrackClass) -> BytesIO | None:
		if not self.connected or not self.accessToken:
			self._authenticate()

		if not self.connected:
			return None

		if not track.art_url_key:
			return None

		headers = {
			"Token": self.accessToken,
			"X-Application": "Tauon/1.0",
			"x-emby-authorization": self._get_jellyfin_auth(),
		}
		params = {}
		base_url = f"{self.prefs.jelly_server_url}/Items/{track.art_url_key}/Images/Primary"
		response = requests.get(base_url, headers=headers, params=params, timeout=10)

		if response.status_code == HTTPStatus.OK:
			return io.BytesIO(response.content)
		logging.error(f"Jellyfin album art api error: {response.status_code} {response.text}")
		return None

	def favorite(self, track: TrackClass, un: bool = False) -> None:
		try:
			if not self.connected or not self.accessToken:
				self._authenticate()

			if not self.connected:
				return

			headers = {
				"Token": self.accessToken,
				"X-Application": "Tauon/1.0",
				"x-emby-authorization": self._get_jellyfin_auth(),
			}

			params = {}
			base_url = f"{self.prefs.jelly_server_url}/Users/{self.userId}/FavoriteItems/{track.url_key}"
			if un:
				response = requests.delete(base_url, headers=headers, params=params, timeout=10)
			else:
				response = requests.post(base_url, headers=headers, params=params, timeout=10)

			if response.status_code == HTTPStatus.OK:
				return
			logging.error("Jellyfin fav api error")

		except Exception:
			logging.exception("Failed to submit favorite to Jellyfin server")

	def upload_playlist(self, pl: int) -> None:
		if not self.connected or not self.accessToken:
			self._authenticate()
		if not self.connected:
			return

		codes = self.pctl.gen_codes.get(self.pctl.multi_playlist[pl].uuid_int, "")

		ids = []
		for t in self.pctl.multi_playlist[pl].playlist_ids:
			track = self.pctl.get_track(t)
			if track.url_key not in ids and track.file_ext == "JELY":
				ids.append(track.url_key)

		if 'jelly"' not in codes:
			response = requests.post(
				f"{self.prefs.jelly_server_url}/Playlists",
				data={},
				headers={
					"Token": self.accessToken,
					"X-Application": "Tauon/1.0",
					"x-emby-authorization": self._get_jellyfin_auth(),
					"Content-Type": "text/json",
				},
				params={
					"UserId": self.userId,
					"Name": self.pctl.multi_playlist[pl].title,
					"Ids": ",".join(ids),
					"MediaType": "Music",
				},
				timeout=10,
			)

			playlist_id = response.json()["Id"]
			self.pctl.gen_codes[self.pctl.multi_playlist[pl].uuid_int] = f'jelly"{playlist_id}"'
			logging.info("New jellyfin playlist created")

		else:
			code = codes.split(" ")[0]
			if not code.startswith('jelly"'):
				return
			code = code[6:-1]
			if '"' in code or not code:
				return

			# upload difference
			response = requests.get(
				f"{self.prefs.jelly_server_url}/Playlists/{code}/Items",
				headers={
					"Token": self.accessToken,
					"X-Application": "Tauon/1.0",
					"x-emby-authorization": self._get_jellyfin_auth(),
				},
				params={
					"UserId": self.userId,
				},
				timeout=10,
			)
			if response.status_code != HTTPStatus.OK:
				logging.error("error")
				return

			d_ids = []
			for item in response.json()["Items"]:
				d_ids.append(item["PlaylistItemId"])

			response = requests.delete(
				f"{self.prefs.jelly_server_url}/Playlists/{code}/Items",
				headers={
					"Token": self.accessToken,
					"X-Application": "Tauon/1.0",
					"x-emby-authorization": self._get_jellyfin_auth(),
				},
				params={
					"UserId": self.userId,
					"EntryIds": ",".join(d_ids),
				},
				timeout=10,
			)

			if response.status_code not in (200, 204):
				logging.error("error2")
				return

			response = requests.post(
				f"{self.prefs.jelly_server_url}/Playlists/{code}/Items",
				data={},
				headers={
					"Token": self.accessToken,
					"X-Application": "Tauon/1.0",
					"x-emby-authorization": self._get_jellyfin_auth(),
					"Content-Type": "text/json",
				},
				params={
					"UserId": self.userId,
					"Ids": ",".join(ids),
				},
				timeout=10,
			)
		logging.info("DONE")

	def get_playlist(self, playlist_id: str, name: str = "", return_list: bool = False) -> list | None:
		if not self.connected or not self.accessToken:
			self._authenticate()
		if not self.connected:
			return []
		response = requests.get(
			f"{self.prefs.jelly_server_url}/Playlists/{playlist_id}/Items",
			headers={
				"Token": self.accessToken,
				"X-Application": "Tauon/1.0",
				"x-emby-authorization": self._get_jellyfin_auth(),
			},
			params={
				"UserId": self.userId,
			},
			timeout=10,
		)

		existing = {}
		for track_id, track in self.pctl.master_library.items():
			if track.is_network and track.file_ext == "JELY":
				existing[track.url_key] = track_id

		playlist: list[int] = []
		for item in response.json()["Items"]:
			track_id = existing.get(item["Id"])
			if track_id is not None:
				playlist.append(track_id)

		if return_list:
			return playlist

		self.scanning = False
		self.pctl.multi_playlist.append(self.tauon.pl_gen(title=name, playlist_ids=playlist))
		self.pctl.gen_codes[self.tauon.pl_to_id(len(self.pctl.multi_playlist) - 1)] = f'jelly"{playlist_id}"'
		return None

	def get_playlists(self) -> None:
		if not self.playlists:
			self.ingest_library(return_list=True)
		if not self.connected:
			return

		for p in self.playlists:
			found = False
			for pp in self.pctl.multi_playlist:
				if f'jelly"{p["Id"]}"' in self.pctl.gen_codes.get(pp.uuid_int, ""):
					found = True
					break
			if found:
				continue

			# Get Playlist
			response = requests.get(
				f"{self.prefs.jelly_server_url}/Playlists/{p['Id']}/Items",
				headers={
					"Token": self.accessToken,
					"X-Application": "Tauon/1.0",
					"x-emby-authorization": self._get_jellyfin_auth(),
				},
				params={
					"UserId": self.userId,
				},
				timeout=10,
			)

			existing = {}
			for track_id, track in self.pctl.master_library.items():
				if track.is_network and track.file_ext == "JELY":
					existing[track.url_key] = track_id

			playlist: list[int] = []
			for item in response.json()["Items"]:
				track_id = existing.get(item["Id"])
				if track_id is not None:
					playlist.append(track_id)

			self.scanning = False
			self.pctl.multi_playlist.append(self.tauon.pl_gen(title=p["Name"], playlist_ids=playlist))
			self.pctl.gen_codes[self.tauon.pl_to_id(len(self.pctl.multi_playlist) - 1)] = f'jelly"{p["Id"]}"'

	def ingest_library(self, return_list: bool = False) -> list[int] | None:
		self.gui.update += 1
		self.scanning = True
		self.gui.to_got = 0

		logging.info("Prepare for Jellyfin library import...")

		if not self.connected or not self.accessToken:
			self._authenticate()

		if not self.connected:
			self.scanning = False
			if not return_list:
				self.show_message(_("Error connecting to Jellyfin"))
			return []

		playlist: list[int] = []

		# This code is to identify if a track has already been imported
		existing: dict[str, int] = {}
		for track_id, track in self.pctl.master_library.items():
			if track.is_network and track.file_ext == "JELY":
				existing[track.url_key] = track_id

		logging.info("Get items...")

		try:
			response = requests.get(
				f"{self.prefs.jelly_server_url}/Items",
				headers={
					"Token": self.accessToken,
					"X-Application": "Tauon/1.0",
					"x-emby-authorization": self._get_jellyfin_auth(),
				},
				params={
					"userId": self.userId,
					"fields": ["Genres", "DateCreated", "MediaSources", "People"],
					"enableImages": False,
					"includeItemTypes": ["Audio", "Playlist"],
					"recursive": True,
				},
				# Someone had a local setup with 36k songs where sync took 31s,
				# so let's wait a nice while before timing out
				timeout=self.prefs.jelly_timeout,
				# stream=True,
			)

		except Exception:
			logging.exception("Error connecting to Jellyfin for Import")
			self.show_message(_("Error connecting to Jellyfin for Import"), mode="error")
			self.scanning = False
			return None

		if response.status_code == HTTPStatus.OK:
			logging.info("Connection successful, storing items...")

			# filter audio items only
			audio_items = list(filter(lambda item: item["Type"] == "Audio", response.json()["Items"]))
			playlist_items = list(filter(lambda item: item["Type"] == "Playlist", response.json()["Items"]))
			self.playlists = playlist_items
			# sort by artist, then album, then track number
			sorted_items = sorted(
				audio_items,
				key=lambda item: (item.get("AlbumArtist", ""), item.get("Album", ""), item.get("IndexNumber", -1)),
			)
			# group by parent
			grouped_items = itertools.groupby(
				sorted_items, lambda item: (item.get("AlbumArtist", "") + " - " + item.get("Album", "")).strip("- ")
			)
		else:
			logging.error(f"Error accessing Jellyfin: [{response.status_code}] {response.reason}")
			self.scanning = False
			self.show_message(_("Error accessing Jellyfin"), f"[{response.status_code}] {response.reason}", mode="warning")
			return None

		fav_status: dict[TrackClass, bool] = {}
		for parent, items in grouped_items:
			for track in items:
				track_id = self.pctl.master_count  # id here is tauons track_id for the track
				existing_track = existing.get(track.get("Id"))
				replace_existing = existing_track is not None
				# logging.info(track.items())
				if replace_existing:
					track_id = existing_track
					nt = self.pctl.get_track(track_id)
				else:
					nt = self.tauon.TrackClass()
				nt.index = track_id  # this is tauons track id
				try:
					nt.fullpath = track.get("MediaSources")[0]["Path"]
				except Exception:
					logging.exception("Jelly exception on get path")
				nt.filename = Path(nt.fullpath).name
				nt.parent_folder_path = str(Path(nt.fullpath).parent)
				nt.parent_folder_name = Path(nt.parent_folder_path).name
				nt.file_ext = "JELY"
				try:
					nt.size = track.get("MediaSources")[0]["Size"]
				except Exception:
					logging.exception("Jelly exception on get size")
				nt.modified_time = time.mktime(
					time.strptime(track.get("DateCreated").rsplit(".", 1)[0], "%Y-%m-%dT%H:%M:%S")
				)

				nt.is_network = True
				nt.url_key = track.get("Id")
				nt.art_url_key = None
				if track.get("AlbumPrimaryImageTag", False):
					nt.art_url_key = track.get("AlbumId")
				else:
					for source in track.get("MediaSources"):
						if any(stream.get("Type") == "EmbeddedImage" for stream in source.get("MediaStreams", [])):
							nt.art_url_key = nt.url_key
				# logging.debug(f"Found EmbeddedImage in MediaStreams.")

				artists = track.get("Artists", [])
				nt.artist = "; ".join(artists)
				if len(artists) > 1:
					nt.misc["artists"] = artists
				nt.album_artist = track.get("AlbumArtist", "")
				replay_gain = track.get("NormalizationGain", "")
				if replay_gain:
					nt.misc["replaygain_track_gain"] = float(replay_gain)
				nt.title = track.get("Name", "")
				nt.composer = "; ".join(d["Name"] for d in track.get("People", []) if d["Type"] == "Composer")
				nt.length = track.get("RunTimeTicks", 0) / 10000000  # needs to be in seconds
				nt.album = track.get("Album", "")
				nt.date = str(track.get("ProductionYear", ""))
				nt.track_number = str(track.get("IndexNumber", ""))
				genres = track.get("Genres", [])
				nt.genre = "; ".join(genres)
				nt.disc_number = str(track.get("ParentIndexNumber", ""))

				try:
					for d in track.get("MediaSources")[0]["MediaStreams"]:
						if d["Type"] == "Audio":
							nt.bitrate = round(d.get("BitRate", 0) / 1000)
							nt.samplerate = round(d.get("SampleRate", 0))
							nt.bit_depth = d.get("BitDepth", 0)
							nt.comment = d.get("Comment", "")
							nt.misc["codec"] = d.get("Codec", "")
							break
				except Exception:
					logging.exception("Jelly exception getting audio mediastream")

				try:
					nt.misc["container"] = track.get("MediaSources")[0].get("Container", "").upper()
				except Exception:
					logging.exception("Jelly exception get container")

				self.pctl.master_library[track_id] = nt
				if not replace_existing:
					self.pctl.master_count += 1
				playlist.append(nt.index)

				# Sync favorite
				star = self.tauon.star_store.full_get(nt.index)
				user_data = track.get("UserData")

				if user_data:
					fav_status[nt] = user_data.get("IsFavorite")

		logging.info("Jellyfin import complete")
		self.gui.update += 1
		self.tauon.wake()

		def set_favs(d: dict[TrackClass, bool]) -> None:
			for tr, v in d.items():
				star = self.tauon.star_store.full_get(tr.index)

				if v:
					if star is None:
						star = StarRecord()
					if not star.loved:
						star.loved = True
					self.tauon.star_store.insert(tr.index, star)
				elif star is None:
					pass
				else:
					star = StarRecord(star.playtime, star.rating)
					self.tauon.star_store.insert(tr.index, star)

		if return_list:
			playlist.sort(key=lambda x: self.pctl.master_library[x].parent_folder_path)
			self.tauon.sort_track_2(0, playlist)
			set_favs(fav_status)
			self.scanning = False
			return playlist

		self.pctl.multi_playlist.append(self.tauon.pl_gen(title=_("Jellyfin Collection"), playlist_ids=playlist))
		self.pctl.gen_codes[self.tauon.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "jelly"
		self.tauon.switch_playlist(len(self.pctl.multi_playlist) - 1)

		playlist.sort(key=lambda x: self.pctl.master_library[x].parent_folder_path)
		self.tauon.sort_track_2(0, playlist)
		set_favs(fav_status)
		self.scanning = False
		self.gui.update += 1
		self.tauon.wake()
		return None

	def session_item(self, track: TrackClass) -> dict[str, list[str] | bool | int | str]:
		return {
			"QueueableMediaTypes": ["Audio"],
			"CanSeek": True,
			"ItemId": track.url_key,
			"IsPaused": self.pctl.playing_state == 2,
			"IsMuted": self.pctl.player_volume == 0,
			"PositionTicks": int(self.pctl.playing_time * 10000000),
			"PlayMethod": "DirectStream",
			"PlaySessionId": "0",
		}

	def session(self) -> None:
		if not self.connected:
			return

		self.session_thread_active = True

		while True:
			time.sleep(1)
			track = self.pctl.playing_object()
			if track is None:
				# logging.debug("Jellyfin playing track is None, skipping loop")
				continue

			if track.file_ext != "JELY" or (self.session_status == 0 and self.pctl.playing_state == 0):
				if self.session_status != 0:
					data = self.session_last_item
					self.session_send("Sessions/Playing/Stopped", data)
					self.session_status = 0
				self.session_thread_active = False
				return

			if (self.session_status == 0 or self.session_item_id != track.index) and self.pctl.playing_state == 1:
				data = self.session_item(track)
				self.session_send("Sessions/Playing", data)
				self.session_update_timer.set()
				self.session_status = 1
				self.session_item_id = track.index
				self.session_last_item = data
			elif self.session_status == 1 and self.session_update_timer.get() >= 10:
				data = self.session_item(track)
				data["EventName"] = "TimeUpdate"
				self.session_send("Sessions/Playing/Progress", data)
				self.session_update_timer.set()
			elif self.session_status in (1, 2) and self.pctl.playing_state in (0, 3):
				data = self.session_last_item
				self.session_send("Sessions/Playing/Stopped", data)
				self.session_status = 0
			elif self.session_status == 1 and self.pctl.playing_state == 2:
				data = self.session_item(track)
				data["EventName"] = "Pause"
				self.session_send("Sessions/Playing/Progress", data)
				self.session_update_timer.set()
				self.session_status = 2
			elif self.session_status == 2 and self.pctl.playing_state == 1:
				data = self.session_item(track)
				data["EventName"] = "Unpause"
				self.session_send("Sessions/Playing/Progress", data)
				self.session_update_timer.set()
				self.session_status = 1

	def session_send(self, point: str, data: dict | None) -> None:
		response = requests.post(
			f"{self.prefs.jelly_server_url}/{point}",
			data=json.dumps(data),
			headers={
				"Token": self.accessToken,
				"X-Application": "Tauon/1.0",
				"x-emby-authorization": self._get_jellyfin_auth(),
				"Content-Type": "application/json",
			},
			timeout=10,
		)
