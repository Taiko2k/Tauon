"""Tauon Music Box - Subsonic/Airsonic Integration"""

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

import hashlib
import io
import json
import logging
import math
import os
import re
import secrets
import threading
import time
from typing import TYPE_CHECKING

import requests

from tauon.t_modules.t_extra import StarRecord

if TYPE_CHECKING:
	from io import BytesIO

	from tauon.t_modules.t_main import AlbumStarStore, GuiVar, PlayerCtl, StarStore, Tauon, TrackClass
	from tauon.t_modules.t_prefs import Prefs

class SubsonicService:

	def __init__(self, tauon: Tauon, album_star_store: AlbumStarStore) -> None:
		self.tauon: Tauon = tauon
		self.gui: GuiVar = tauon.gui
		self.pctl: PlayerCtl = tauon.pctl
		self.prefs: Prefs = tauon.prefs
		self.t_title: str = tauon.t_title
		self.star_store: StarStore = tauon.star_store
		self.album_star_store: AlbumStarStore = album_star_store
		self.show_message     = tauon.show_message
		self.playlists        = tauon.prefs.subsonic_playlists
		self.scanning: bool= False

	def r(self, point: str, p: dict[str, str] | None = None, binary: bool = False, get_url: bool = False):
		salt = secrets.token_hex(8)
		server = self.prefs.subsonic_server.rstrip("/") + "/"

		params = {
			"u": self.prefs.subsonic_user,
			"v": "1.13.0",
			"c": self.t_title,
			"f": "json",
		}

		if self.prefs.subsonic_password_plain:
			params["p"] = self.prefs.subsonic_password
		else:
			params["t"] = hashlib.md5((self.prefs.subsonic_password + salt).encode()).hexdigest()
			params["s"] = salt

		if p:
			params.update(p)

		point = "rest/" + point

		url = server + point

		if get_url:
			return url, params

		response = requests.get(url, params=params, timeout=10)

		if binary:
			return response.content

		# Some broken servers can send invalid JSON with control chars - remove them, see https://github.com/Taiko2k/Tauon/issues/1112
		CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
		control_chars = CONTROL_CHAR_RE.findall(response.text)
		if control_chars:
			clean_response = CONTROL_CHAR_RE.sub("", response.text)
			details = [f"U+{ord(c):04X}" for c in control_chars]
			logging.warning(f"Invalid control characters found in JSON response: {', '.join(details)}")
		else:
			clean_response = response.text

		try:
			d = json.loads(clean_response)
		except json.decoder.JSONDecodeError:
			logging.exception(f"Failed to decode subsonic response as json: {clean_response}")
			return None
		except Exception:
			logging.exception(f"Unknown error loading subsonic response: {clean_response}")
			return None
		# logging.info(d)

		if d["subsonic-response"]["status"] != "ok":
			self.show_message(_("Subsonic Error: ") + response.text, mode="warning")
			logging.error(f"Subsonic Error: {response.text}")

		return d

	def get_cover(self, track_object: TrackClass) -> BytesIO:
		response = self.r("getCoverArt", p={"id": track_object.art_url_key}, binary=True)
		try:
			response.decode("utf-8")
			raise ValueError(f"Expected binary data with an image but got a valid string: {response}")
		except UnicodeDecodeError:
			pass

		return io.BytesIO(response)

	def resolve_stream(self, key: str) -> (tuple[str, dict[str, str]] | bytes | Any | None):
		p = {"id": key}
		if self.prefs.network_stream_bitrate > 0:
			p["maxBitRate"] = self.prefs.network_stream_bitrate

		return self.r("stream", p=p, get_url=True)
		# logging.info(response.content)

	def listen(self, track_object: TrackClass, submit: bool = False) -> bool:

		try:
			a = self.r("scrobble", p={"id": track_object.url_key, "submission": submit})
		except Exception:
			logging.exception("Error connecting for scrobble on airsonic")
		return True

	def set_rating(self, track_object: TrackClass, rating) -> bool:
		try:
			a = self.r("setRating", p={"id": track_object.url_key, "rating": math.ceil(rating / 2)})
		except Exception:
			logging.exception("Error connect for set rating on airsonic")
		return True

	def set_album_rating(self, track_object: TrackClass, rating) -> bool:
		id = track_object.misc.get("subsonic-folder-id")
		if id is not None:
			try:
				a = self.r("setRating", p={"id": id, "rating": math.ceil(rating / 2)})
			except Exception:
				logging.exception("Error connect for set rating on airsonic")
		return True

	def star_track(self, track_object: TrackClass) -> bool:
		try:
			a = self.r("star", p={"id": track_object.url_key})
		except Exception:
			logging.exception('Error connect for star track on airsonic')
		return True

	def unstar_track(self, track_object: TrackClass) -> bool:
		try:
			a = self.r("unstar", p={"id": track_object.url_key})
		except Exception:
			logging.exception('Error connect for unstar track on airsonic')
		return True

	def star_album(self, track_object: TrackClass) -> bool:
		id = track_object.misc.get("subsonic-folder-id")
		if id is not None:
			try:
				a = self.r("star", p={"id": id})
			except Exception:
				logging.exception("Error connect for star Album on airsonic")
		return True

	def get_music3(self, return_list: bool = False) -> list[int] | None:
		self.scanning = True
		self.gui.to_got = 0

		existing: dict[str, int] = {}

		for track_id, track in self.pctl.master_library.items():
			if track.is_network and track.file_ext == "SUB":
				existing[track.url_key] = track_id

		try:
			a = self.r("getIndexes")
		except Exception:
			logging.exception("Error connecting to Airsonic server")
			self.show_message(_("Error connecting to Airsonic server"), mode="error")
			self.scanning = False
			return []
		if not a or "subsonic-response" not in a:
			logging.error("Invalid response from Airsonic getIndexes")
			self.show_message(_("Error connecting to Airsonic server"), mode="error")
			self.scanning = False
			return []

		# {'openSubsonic': True, 'serverVersion': '8', 'status': 'failed', 'type': 'lms', 'version': '1.16.0', 'error': {'code': 41, 'message': 'Token authentication not supported for LDAP users.'}}
		if "indexes" not in a["subsonic-response"]:
			self.scanning = False
			if "error" in a["subsonic-response"]:
				logging.debug(a["subsonic-response"])
				self.show_message(_("Error connecting to Airsonic server"), f'{a["subsonic-response"]["error"]["code"]}: {a["subsonic-response"]["error"]["message"]}', mode="error")
				return None
			logging.critical("Failed to find expected key 'indexes', report a bug with the log below!")
			logging.critical(a["subsonic-response"])
			self.show_message(_("Error connecting to Airsonic server"), "See console log for more details", mode="error")
			return None

		b = a["subsonic-response"]["indexes"]["index"]

		folders: list[tuple[str, str]] = []

		for letter in b:
			artists = letter["artist"]
			for artist in artists:
				folders.append((
					artist["id"],
					artist["name"],
				))

		playlist: list[int] = []
		songsets: list[tuple[TrackClass, str, str, int]] = []
		for i in range(len(folders)):
			songsets.append([])
		statuses = [0] * len(folders)
		#dupes = []
		liked_track_ids: list[int] = []

		def getsongs(index: int, folder_id: str, name: str, inner: bool = False, parent: dict[str, str | int] | None = None) -> None:
			try:
				d = self.r("getMusicDirectory", p={"id": folder_id})
				if "child" not in d["subsonic-response"]["directory"]:
					if not inner:
						statuses[index] = 2
					return

			except json.decoder.JSONDecodeError:
				logging.exception("Error reading Airsonic directory")
				if not inner:
					statuses[index] = 2
				self.show_message(_("Error reading Airsonic directory!"), mode="warning")
				return
			except Exception:
				logging.exception("Unknown Error reading Airsonic directory")
				return

			items = d["subsonic-response"]["directory"]["child"]

			self.gui.update = 2

			for item in items:
				#logging.debug(f"song: {item}")
				if item.get("isDir"):
					if "userRating" in item and "artist" in item:
						rating = item["userRating"]
						if self.album_star_store.get_rating_artist_title(item["artist"], item["title"]) == 0 and rating == 0:
							pass
						else:
							self.album_star_store.set_rating_artist_title(item["artist"], item["title"], int(rating * 2))

					getsongs(index, item["id"], item["title"], inner=True, parent=item)
					continue

				self.gui.to_got += 1
				song = item
				nt = self.tauon.TrackClass()

				if parent and "artist" in parent:
					nt.album_artist = parent["artist"]

				if "title" in song:
					nt.title = song["title"]
				if "artist" in song:
					nt.artist = song["artist"]
				if "album" in song:
					nt.album = song["album"]
				if "track" in song:
					nt.track_number = song["track"]
				if "year" in song:
					nt.date = str(song["year"])
				if "duration" in song:
					nt.length = song["duration"]

				nt.file_ext = "SUB"
				nt.parent_folder_name = name
				if "path" in song:
					nt.fullpath = song["path"]
					nt.parent_folder_path = os.path.dirname(song["path"])
				if "coverArt" in song:
					nt.art_url_key = song["coverArt"]
				nt.url_key = song["id"]
				nt.misc["subsonic-folder-id"] = folder_id
				nt.is_network = True

				rating = 0
				if "userRating" in song:
					rating = int(song["userRating"])

				songsets[index].append((nt, name, song["id"], rating))

			if inner:
				return
			statuses[index] = 2

		i = -1
		for id, name in folders:
			i += 1
			while statuses.count(1) > 3:
				time.sleep(0.1)

			statuses[i] = 1
			t = threading.Thread(target=getsongs, args=([i, id, name]))
			t.daemon = True
			t.start()

		while statuses.count(2) != len(statuses):
			time.sleep(0.1)

		try:
			a = self.r("getStarred2")
		except Exception:
			logging.exception("Error connecting to Airsonic server")
			self.show_message(_("Error connecting to Airsonic server"), mode="error")
			return []
		b = a["subsonic-response"]["starred2"]

		liked_tracks: list[str] = []

		for id in b["song"]:
			#print(id["id"])
			liked_tracks.append((
				id["id"]
				))

		for sset in songsets:
			for nt, name, song_id, rating in sset:
				id = self.pctl.master_count

				replace_existing = False
				ex = existing.get(song_id)
				if ex is not None:
					id = ex
					replace_existing = True

				nt.index = id
				self.pctl.master_library[id] = nt
				if not replace_existing:
					self.pctl.master_count += 1

				if nt.url_key in liked_tracks:
					liked_track_ids.append(nt.index)

				playlist.append(nt.index)

				if self.star_store.get_rating(nt.index) == 0 and rating == 0:
					pass
				else:
					self.star_store.set_rating(nt.index, rating * 2)

		def set_favs(d:list[int]) -> None:
			for track_id in d:
				if track_id == 0:
					continue

				star = self.tauon.star_store.full_get(track_id)
				if star is None:
					star = StarRecord()
				if not star.loved:
					star.loved = True
				self.tauon.star_store.insert(track_id, star)
		set_favs(liked_track_ids)

		self.scanning = False
		if return_list:
			return playlist

		self.pctl.multi_playlist.append(self.tauon.pl_gen(title=_("Airsonic Collection"), playlist_ids=playlist))
		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "air"
		self.pctl.switch_playlist(len(self.pctl.multi_playlist) - 1)
		return None
