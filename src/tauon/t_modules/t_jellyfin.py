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
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

import requests

from tauon.t_modules.t_db_state import allocate_track_id
from tauon.t_modules.t_extra import StarRecord, Timer, with_url_scheme
from tauon.t_modules.t_remote_playlists import RemotePlaylist, RemotePlaylistSource
from tauon.t_modules.t_scrobble_queue import Outcome, http_outcome
from tauon.t_modules.t_server_sync import (
	JELLYFIN,
	LOVE,
	SCAN_CHANGES,
	SCAN_PROCESSING,
	LibraryCache,
	PlaylistGoneError,
	RemotePlaylistState,
	ScanCancelledError,
)

if TYPE_CHECKING:
	from collections.abc import Iterator
	from io import BytesIO

	from tauon.t_modules.t_extra import TauonPlaylist
	from tauon.t_modules.t_main import GuiVar, PlayerCtl, Tauon, TrackClass
	from tauon.t_modules.t_prefs import Prefs
	from tauon.t_modules.t_scrobble_queue import PendingScrobble
	from tauon.t_modules.t_server_sync import ServerEdit

# Library import is fetched in pages so each response stays small enough that
# a reverse proxy in front of the server won't time out generating it
ITEM_PAGE_SIZE = 200
# Pages requested at once. Most of an import is waiting on the server.
PARALLEL_PAGES = 4
ITEM_FETCH_TIMEOUT = (10, 600)  # (connect, read) seconds per page


# Fields needed to build a track from an audio item
TRACK_FIELDS = ["Genres", "DateCreated", "MediaSources", "People"]

# Seconds of overlap when asking what changed since the last fetch, for clock jitter
SINCE_MARGIN_S = 60
# Items without media details are small, so a big library can take far fewer requests
BARE_PAGE_SIZE = 1000
# More unknown tracks than this and a full import is quicker than fetching them by id
MISSING_LIMIT = 500


def iso_time(timestamp: float) -> str:
	return datetime.fromtimestamp(timestamp, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")



class Jellyfin(RemotePlaylistSource):
	code_prefix = "jelly"

	def __init__(self, tauon: Tauon) -> None:
		self.tauon: Tauon = tauon
		self.gui: GuiVar = tauon.gui
		self.pctl: PlayerCtl = tauon.pctl
		self.prefs: Prefs = tauon.prefs
		self.show_message = tauon.show_message

		self.scanning: bool = False
		# Set from the activity popover, the scan stops at its next page
		self.cancel_scan = False
		# Tracks the running scan expects, for the activity row's progress; 0 when unknown
		self.scan_total = 0
		self.scan_stage = ""
		self.connected = False

		self.accessToken = None
		self.userId = None
		self.currentId = None

		self.session_thread_active: bool = False
		self.session_status: int = 0
		self.session_item_id: int | None = None
		self.session_update_timer: Timer = Timer()
		self.session_last_item: dict[str, list[str] | bool | int | str] | None = None
		self.init_remote_playlists()

		self.lyrics_scan_lock = threading.Lock()
		self.lyrics_scan_pending: set[str] = set()
		self.lyrics_scan_checked: set[str] = set()

	@property
	def server_url(self) -> str:
		"""Return the Jellyfin server URL with trailing slashes stripped."""
		return self.prefs.jelly_server_url.rstrip("/")

	def _get_jellyfin_auth(self) -> str:
		auth_str = f"MediaBrowser Client={self.tauon.t_title}, Device={self.tauon.device}, DeviceId=-, Version={self.tauon.t_version}"
		if self.accessToken:
			auth_str += f", Token={self.accessToken}"
		return auth_str

	def _authenticate(self, debug: bool = False, quiet: bool = False) -> None:
		# Typed without http:// or https://, fill it in so the settings field shows what's used
		self.prefs.jelly_server_url = with_url_scheme(self.prefs.jelly_server_url, 8096)
		username = self.prefs.jelly_username
		password = self.prefs.jelly_password
		server = self.server_url

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
			if not quiet:
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
		elif quiet:
			logging.warning(f"Jellyfin auth failed: {response.status_code}")
		elif response.status_code == HTTPStatus.UNAUTHORIZED:
			self.show_message(_("401 Authentication failed"), _("Check username and password."), mode="warning")
		else:
			self.show_message(_("Jellyfin auth error"), f"{response.status_code} {response.text}", mode="warning")

	def test(self) -> None:
		self._authenticate(debug=True)

	def ping(self) -> bool:
		"""Quietly check the server and login, for the Add music box."""
		self.connected = False
		self._authenticate(quiet=True)
		return self.connected

	def list_libraries(self) -> list[RemotePlaylist] | None:
		"""The user's music libraries, or None if they couldn't be fetched."""
		if not self.connected or not self.accessToken:
			self._authenticate(quiet=True)
		if not self.connected:
			return None
		response = requests.get(
			f"{self.server_url}/UserViews", headers=self._headers(), params={"userId": self.userId}, timeout=(5, 30))
		if response.status_code == HTTPStatus.NOT_FOUND:
			# Servers before 10.9
			response = requests.get(f"{self.server_url}/Users/{self.userId}/Views", headers=self._headers(), timeout=(5, 30))
		if response.status_code != HTTPStatus.OK:
			logging.error(f"Error listing Jellyfin libraries: [{response.status_code}] {response.reason}")
			return None
		return [
			RemotePlaylist(id=item["Id"], name=item.get("Name") or item["Id"])
			for item in response.json().get("Items", [])
			if item.get("Id") and item.get("CollectionType") == "music"
		]

	def resolve_stream(self, stream_id: str) -> str | tuple[str, dict]:
		if not self.connected or not self.accessToken:
			self._authenticate()

		if not self.connected:
			return ""

		base_url = f"{self.server_url}/Audio/{stream_id}/stream"
		params = {
			"UserId": self.userId,
			"static": "true",
			"api_key": self.accessToken,
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
			"Authorization": self._get_jellyfin_auth(),
		}
		response = requests.get(f"{self.server_url}/Items/{track.art_url_key}/Images/Primary", headers=headers, timeout=10)
		if response.status_code == HTTPStatus.OK:
			return io.BytesIO(response.content)

		# An embedded image Jellyfin never extracted 404s, so try the album's cover
		if response.status_code == HTTPStatus.NOT_FOUND and track.art_url_key == track.url_key:
			album_id = self._album_cover_id(track.url_key, headers)
			if album_id:
				response = requests.get(f"{self.server_url}/Items/{album_id}/Images/Primary", headers=headers, timeout=10)
				if response.status_code == HTTPStatus.OK:
					return io.BytesIO(response.content)

		logging.error(f"Jellyfin album art api error: {response.status_code} {response.text}")
		return None

	def _album_cover_id(self, item_id: str, headers: dict[str, str]) -> str | None:
		"""Album id of an item, if that album has a cover."""
		try:
			response = requests.get(
				f"{self.server_url}/Items",
				headers=headers,
				params={"userId": self.userId, "ids": item_id, "enableImageTypes": ["Primary"]},
				timeout=10,
			)
			items = response.json().get("Items") if response.status_code == HTTPStatus.OK else None
		except Exception:
			logging.exception("Error looking up Jellyfin album cover")
			return None
		if not items or not items[0].get("AlbumPrimaryImageTag"):
			return None
		return items[0].get("AlbumId")

	def _timestamp_from_ticks(self, ticks: int) -> str:
		seconds, ticks = divmod(max(0, ticks), 10000000)
		return f"{seconds // 60:02d}:{seconds % 60:02d}.{ticks // 10000:03d}"

	def get_lyrics(self, track_object: TrackClass) -> tuple[str, str]:
		if not self.connected or not self.accessToken:
			self._authenticate()

		if not self.connected:
			return "", ""

		headers = {
			"Token": self.accessToken,
			"X-Application": "Tauon/1.0",
			"Authorization": self._get_jellyfin_auth(),
		}
		base_url = f"{self.server_url}/Audio/{track_object.url_key}/Lyrics"
		response = requests.get(base_url, headers=headers, timeout=10)

		if response.status_code != HTTPStatus.OK:
			# 404 just means the server has no lyrics for this track
			if response.status_code != HTTPStatus.NOT_FOUND:
				logging.error(f"Jellyfin lyrics api error: {response.status_code} {response.text}")
			return "", ""

		plain = []
		synced = []
		for line in response.json().get("Lyrics", []):
			text = str(line.get("Text") or "")
			plain.append(text)
			# Start is only present for synced (LRC) lyrics, in 100ns ticks
			if line.get("Start") is not None:
				synced.append(f"[{self._timestamp_from_ticks(int(line['Start']))}]{text}")
		return "\n".join(plain).strip(), "\n".join(synced).strip()

	def scan_lyrics(self, track_object: TrackClass) -> None:
		if not track_object.url_key or track_object.lyrics or track_object.synced:
			return

		with self.lyrics_scan_lock:
			if track_object.url_key in self.lyrics_scan_pending or track_object.url_key in self.lyrics_scan_checked:
				return
			self.lyrics_scan_pending.add(track_object.url_key)

		def worker() -> None:
			try:
				lyrics, synced = self.get_lyrics(track_object)
				if lyrics:
					track_object.lyrics = lyrics
					self.gui.lyrics_editor_update_now[0] = True
				if synced:
					track_object.synced = synced
					self.gui.lyrics_editor_update_now[1] = True
				if lyrics or synced:
					logging.info(f"Found lyrics from Jellyfin server for {track_object.artist} - {track_object.title}")
					self.gui.request_frame()
					self.tauon.lyrics_ren_mini.to_reload = True
					self.tauon.timed_lyrics_ren.index = -1
					self.pctl.notify_database_changed()
					self.pctl.refresh_now_playing(force=True)
			except Exception:
				logging.exception("Failed to scan lyrics from Jellyfin server")
			finally:
				with self.lyrics_scan_lock:
					self.lyrics_scan_pending.discard(track_object.url_key)
					self.lyrics_scan_checked.add(track_object.url_key)

		shoot = threading.Thread(target=worker)
		shoot.daemon = True
		shoot.start()

	def sync_configured(self) -> bool:
		return bool(self.prefs.jelly_username and self.prefs.jelly_server_url)

	def _ready(self) -> bool:
		"""Log in quietly when needed, for background requests."""
		if not self.connected or not self.accessToken:
			self._authenticate(quiet=True)
		return self.connected

	def _send(self, method: str, point: str, legacy: str | None = None, **kwargs: object) -> requests.Response:
		"""Make a request, trying the pre-10.9 path when the server doesn't know the current one."""
		response = requests.request(method, f"{self.server_url}/{point}", headers=self._headers(), timeout=(5, 30), **kwargs)
		if response.status_code == HTTPStatus.NOT_FOUND and legacy:
			response = requests.request(
				method, f"{self.server_url}/{legacy}", headers=self._headers(), timeout=(5, 30), **kwargs)
		if response.status_code == HTTPStatus.UNAUTHORIZED:
			# Log in again next time
			self.connected = False
		return response

	def push_edit(self, edit: ServerEdit) -> Outcome:
		"""Send a love as a favourite."""
		if edit.kind != LOVE:
			return Outcome.DROP
		if not self._ready():
			return Outcome.RETRY
		try:
			response = self._send(
				"POST" if edit.value else "DELETE", f"UserFavoriteItems/{edit.server_id}",
				legacy=f"Users/{self.userId}/FavoriteItems/{edit.server_id}", params={"userId": self.userId})
		except requests.RequestException as e:
			logging.warning(f"Could not reach the Jellyfin server: {e}")
			return Outcome.RETRY
		return http_outcome(response.status_code)

	def submit_scrobble(self, item: PendingScrobble) -> Outcome:
		"""Count a play on the server at the time it happened."""
		if not self._ready():
			return Outcome.RETRY
		try:
			response = self._send(
				"POST", f"UserPlayedItems/{item.server_id}", legacy=f"Users/{self.userId}/PlayedItems/{item.server_id}",
				params={"userId": self.userId, "datePlayed": iso_time(item.timestamp)})
		except requests.RequestException as e:
			logging.warning(f"Could not reach the Jellyfin server: {e}")
			return Outcome.RETRY
		return http_outcome(response.status_code)

	def fetch_remote_playlist(self, remote_id: str) -> RemotePlaylistState | None:
		"""A playlist and its tracks, adding any that aren't in the library yet. None if it couldn't be fetched."""
		if not self._ready():
			return None
		try:
			info = requests.get(
				f"{self.server_url}/Items", headers=self._headers(),
				params={"userId": self.userId, "ids": remote_id, "fields": ["Etag"]}, timeout=(5, 30))
			if info.status_code != HTTPStatus.OK:
				logging.error(f"Error fetching Jellyfin playlist: [{info.status_code}] {info.reason}")
				return None
			found = info.json().get("Items") or []
			if not found:
				raise PlaylistGoneError
			response = requests.get(
				f"{self.server_url}/Playlists/{remote_id}/Items", headers=self._headers(),
				params={"userId": self.userId, "fields": TRACK_FIELDS}, timeout=(5, 60))
		except requests.RequestException:
			logging.exception("Error fetching Jellyfin playlist")
			return None
		if response.status_code == HTTPStatus.NOT_FOUND:
			raise PlaylistGoneError
		if response.status_code != HTTPStatus.OK:
			logging.error(f"Error fetching Jellyfin playlist: [{response.status_code}] {response.reason}")
			return None

		existing = self._existing()
		server_ids: list[str] = []
		track_ids: list[int] = []
		kept: list[str] = []
		for item in response.json().get("Items", []):
			if not item.get("Id"):
				continue
			if item.get("Type") != "Audio":
				# Such as a music video, which Tauon can't hold but mustn't remove
				kept.append(item["Id"])
				continue
			track_id = existing.get(item["Id"])
			if track_id is None:
				# Not in the library yet, so add it from the playlist's own copy
				nt = self._store_track(item, existing)
				existing[item["Id"]] = track_id = nt.index
			server_ids.append(item["Id"])
			track_ids.append(track_id)
		# The Etag changes with every edit to the playlist
		return RemotePlaylistState(
			server_ids, track_ids, found[0].get("Etag") or "", found[0].get("Name") or "", kept=kept)

	def write_remote_playlist(
		self, remote_id: str, current: RemotePlaylistState, server_ids: list[str], name: str | None,
	) -> bool:
		"""Replace a playlist's tracks, and its name if given. Entries Tauon can't hold go at the end."""
		if not self._ready():
			return False
		server_ids = server_ids + [x for x in current.kept if x not in server_ids]
		body: dict[str, object] = {"Ids": server_ids}
		if name:
			body["Name"] = name
		try:
			response = requests.post(
				f"{self.server_url}/Playlists/{remote_id}", headers=self._headers(), json=body, timeout=(5, 60))
			if response.status_code in (HTTPStatus.NOT_FOUND, HTTPStatus.METHOD_NOT_ALLOWED):
				# Servers before 10.9 can't replace a playlist: empty it and add everything back
				return self._rewrite_playlist(remote_id, server_ids)
		except requests.RequestException:
			logging.exception("Error updating Jellyfin playlist")
			return False
		if response.status_code not in (HTTPStatus.OK, HTTPStatus.NO_CONTENT):
			logging.error(f"Error updating Jellyfin playlist: [{response.status_code}] {response.reason}")
			return False
		return True

	def _rewrite_playlist(self, remote_id: str, server_ids: list[str]) -> bool:
		response = requests.get(
			f"{self.server_url}/Playlists/{remote_id}/Items", headers=self._headers(),
			params={"userId": self.userId}, timeout=(5, 60))
		if response.status_code != HTTPStatus.OK:
			return False
		entries = [item["PlaylistItemId"] for item in response.json().get("Items", []) if item.get("PlaylistItemId")]
		# Chunked to keep the query string a sane length
		for i in range(0, len(entries), 100):
			response = requests.delete(
				f"{self.server_url}/Playlists/{remote_id}/Items", headers=self._headers(),
				params={"userId": self.userId, "entryIds": ",".join(entries[i:i + 100])}, timeout=(5, 60))
			if response.status_code not in (HTTPStatus.OK, HTTPStatus.NO_CONTENT):
				return False
		for i in range(0, len(server_ids), 100):
			response = requests.post(
				f"{self.server_url}/Playlists/{remote_id}/Items", headers=self._headers(),
				params={"userId": self.userId, "ids": ",".join(server_ids[i:i + 100])}, timeout=(5, 60))
			if response.status_code not in (HTTPStatus.OK, HTTPStatus.NO_CONTENT):
				return False
		return True

	def create_remote_playlist(self, name: str, server_ids: list[str]) -> str | None:
		"""Create a playlist, returning its id."""
		if not self._ready():
			return None
		try:
			response = requests.post(
				f"{self.server_url}/Playlists", headers=self._headers(),
				json={"Name": name, "Ids": server_ids, "UserId": self.userId, "MediaType": "Audio"}, timeout=(5, 60))
		except requests.RequestException:
			logging.exception("Error creating Jellyfin playlist")
			return None
		if response.status_code != HTTPStatus.OK:
			logging.error(f"Error creating Jellyfin playlist: [{response.status_code}] {response.reason}")
			return None
		logging.info("New Jellyfin playlist created")
		return response.json().get("Id")

	def _headers(self) -> dict[str, str]:
		return {
			"Token": self.accessToken,
			"X-Application": "Tauon/1.0",
			"Authorization": self._get_jellyfin_auth(),
		}

	def _list_playlists(self) -> list[RemotePlaylist] | None:
		if not self.connected or not self.accessToken:
			self._authenticate()
		if not self.connected:
			self.remote_playlists_error = _("Could not connect to the server")
			return None
		response = requests.get(
			f"{self.server_url}/Items",
			headers=self._headers(),
			params={
				"userId": self.userId,
				"includeItemTypes": ["Playlist"],
				"recursive": True,
				"fields": ["ChildCount"],
				"sortBy": "SortName",
				"sortOrder": "Ascending",
			},
			timeout=(5, 30),
		)
		if response.status_code != HTTPStatus.OK:
			logging.error(f"Error listing Jellyfin playlists: [{response.status_code}] {response.reason}")
			self.remote_playlists_error = f"[{response.status_code}] {response.reason}"
			return None
		return [
			RemotePlaylist(id=item["Id"], name=item.get("Name") or item["Id"], count=item.get("ChildCount") or 0)
			for item in response.json().get("Items", [])
			# Jellyfin playlists can hold video too
			if item.get("Id") and item.get("MediaType") != "Video"
		]

	def playlist_track_ids(self, playlist_id: str) -> list[int] | None:
		try:
			remote = self.fetch_remote_playlist(playlist_id)
		except PlaylistGoneError:
			return None
		return None if remote is None else remote.track_ids

	def _existing(self) -> dict[str, int]:
		"""Library ids of Jellyfin tracks, by item id."""
		return {
			track.url_key: track_id for track_id, track in self.pctl.master_library.items()
			if track.is_network and track.file_ext == "JELY"}

	def get_playlist(self, playlist_id: str) -> list[int] | None:
		"""Track ids for the jelly"<id>" generator code."""
		track_ids = self.playlist_track_ids(playlist_id)
		if track_ids is None:
			self.show_message(_("Error fetching Jellyfin playlist"), mode="warning")
		return track_ids

	def _store_track(self, track: dict, existing: dict[str, int]) -> TrackClass:
		"""Create or update the library track for an audio item."""
		track_id = existing.get(track.get("Id"))
		if track_id is not None:
			nt = self.pctl.get_track(track_id)
		else:
			nt = self.tauon.TrackClass()
			track_id = allocate_track_id(self.pctl)
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
		previous_art_key = nt.art_url_key
		has_embedded_image = any(
			stream.get("Type") == "EmbeddedImage"
			for source in track.get("MediaSources") or []
			for stream in source.get("MediaStreams") or []
		)
		if (track.get("ImageTags") or {}).get("Primary") or has_embedded_image:
			nt.art_url_key = nt.url_key
		elif track.get("AlbumPrimaryImageTag"):
			nt.art_url_key = track.get("AlbumId")
		else:
			nt.art_url_key = None
		if nt.art_url_key != previous_art_key:
			self.tauon.album_art_gen.source_cache.pop(nt.index, None)

		artists = track.get("Artists", [])
		nt.artist = "; ".join(artists)
		if len(artists) > 1:
			nt.artists = artists
		nt.album_artist = track.get("AlbumArtist", "")
		replay_gain = track.get("NormalizationGain", "")
		if replay_gain:
			nt.replaygain_track_gain = float(replay_gain)
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
					nt.codec = d.get("Codec", "")
					break
		except Exception:
			logging.exception("Jelly exception getting audio mediastream")

		try:
			nt.container = track.get("MediaSources")[0].get("Container", "").upper()
		except Exception:
			logging.exception("Jelly exception get container")

		user_data = track.get("UserData")
		if user_data:
			nt.server_plays = int(user_data.get("PlayCount") or 0)

		self.pctl.master_library[track_id] = nt
		return nt

	def favourite_tracks(self) -> list[int] | None:
		"""Track ids for the jellyfav generator code, or None if cancelled."""
		try:
			return self.ingest_library(return_list=True, extra={"filters": "IsFavorite"}) or []
		except ScanCancelledError:
			return None
		finally:
			self._scan_done()

	def favourite_albums(self) -> list[int] | None:
		"""Track ids for the jellyfavalb generator code, or None if cancelled."""
		try:
			return self._favourite_albums()
		except ScanCancelledError:
			return None
		finally:
			self._scan_done()

	def _scan_done(self) -> None:
		self.scanning = False
		self.cancel_scan = False
		self.scan_total = 0
		self.scan_stage = ""
		self.gui.request_frame()

	def _count_page(self, count: int) -> None:
		self.gui.to_got += count
		self.gui.request_frame()
		self.tauon.wake()

	def _favourite_albums(self) -> list[int]:
		if not self.connected or not self.accessToken:
			self._authenticate()
		if not self.connected:
			return []
		try:
			response = requests.get(
				f"{self.server_url}/Items",
				headers=self._headers(),
				params={
					"userId": self.userId, "includeItemTypes": ["MusicAlbum"],
					"recursive": True, "filters": "IsFavorite",
				},
				timeout=(5, 30),
			)
		except Exception:
			logging.exception("Error listing Jellyfin favourite albums")
			return []
		if response.status_code != HTTPStatus.OK:
			logging.error(f"Error listing Jellyfin favourite albums: [{response.status_code}] {response.reason}")
			return []
		album_ids = [item["Id"] for item in response.json().get("Items", []) if item.get("Id")]
		tracks: list[int] = []
		# Chunked to keep the query string a sane length
		for i in range(0, len(album_ids), 100):
			chunk = ",".join(album_ids[i:i + 100])
			tracks.extend(self.ingest_library(return_list=True, extra={"albumIds": chunk}) or [])
		return tracks

	def ingest_library(
		self, return_list: bool = False, parent_id: str | None = None, extra: dict[str, str] | None = None,
	) -> list[int] | None:
		"""Import every track, or only those in the library parent_id, or matching the extra query."""
		self.gui.request_frame()
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

		params: dict[str, object] = {
			"userId": self.userId,
			"fields": TRACK_FIELDS,
			"enableImages": True,
			"enableImageTypes": ["Primary"],
			"includeItemTypes": ["Audio"],
			"recursive": True,
			# Pages must come back in a stable order, otherwise items
			# could be missed or duplicated between requests
			"sortBy": "SortName",
			"sortOrder": "Ascending",
		}
		if parent_id:
			params["parentId"] = parent_id
		if extra:
			params.update(extra)

		try:
			items = self._parallel_items(params, ITEM_PAGE_SIZE)
		except ScanCancelledError:
			raise
		except requests.RequestException:
			logging.exception("Error connecting to Jellyfin for Import")
			self.show_message(_("Error connecting to Jellyfin for Import"), mode="error")
			self.scanning = False
			return None
		except OSError as e:
			logging.error(f"Error accessing Jellyfin: {e}")
			self.scanning = False
			self.show_message(_("Error accessing Jellyfin"), str(e), mode="warning")
			return None
		logging.info(f"Got {len(items)} of {self.scan_total} items")

		logging.info("Storing items...")
		self.scan_stage = SCAN_PROCESSING
		self.gui.request_frame()

		# filter audio items only
		audio_items = [item for item in items if item["Type"] == "Audio"]
		# sort by artist, then album, then track number
		sorted_items = sorted(
			audio_items,
			key=lambda item: (item.get("AlbumArtist", ""), item.get("Album", ""), item.get("IndexNumber", -1)),
		)
		# group by parent
		grouped_items = itertools.groupby(
			sorted_items, lambda item: (item.get("AlbumArtist", "") + " - " + item.get("Album", "")).strip("- ")
		)

		fav_status: dict[TrackClass, bool] = {}
		for parent, items in grouped_items:
			for track in items:
				nt = self._store_track(track, existing)
				playlist.append(nt.index)

				# Sync favorite
				star = self.tauon.star_store.full_get(nt.index)
				user_data = track.get("UserData")

				if user_data:
					fav_status[nt] = user_data.get("IsFavorite")

		logging.info("Jellyfin import complete")
		self.gui.request_frame()
		self.tauon.wake()

		# Sort before the playlist is shown, otherwise switch_playlist builds
		# the gallery from the unsorted order and it goes stale once sorted
		playlist.sort(key=lambda x: self.pctl.master_library[x].parent_folder_path)
		self.tauon.sort_track_2(0, playlist)
		self._set_favs(fav_status)

		self.scan_stage = ""
		if return_list:
			self.scanning = False
			return playlist

		self.pctl.multi_playlist.append(self.tauon.pl_gen(title=_("Jellyfin Collection"), playlist_ids=playlist))
		self.pctl.gen_codes[self.tauon.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "jelly"
		self.tauon.switch_playlist(len(self.pctl.multi_playlist) - 1)

		self.scanning = False
		self.gui.request_frame()
		self.tauon.wake()
		return None

	def _set_favs(self, d: dict[TrackClass, bool]) -> None:
		# An unsent love made here is newer than what the server says
		pending = self.tauon.server_sync.pending(JELLYFIN, LOVE)
		for tr, v in d.items():
			if tr.url_key in pending:
				continue
			star = self.tauon.star_store.full_get(tr.index)

			if v:
				if star is None:
					star = StarRecord()
				if not star.loved:
					star.loved = True
				self.tauon.star_store.insert(tr.index, star)
			elif star is not None and star.loved:
				# Only the love goes, hated and the rest stay
				self.tauon.star_store.insert(tr.index, replace(star, loved=False, loved_timestamp=0))

	def _server_time(self, response: requests.Response | None = None) -> float:
		"""The server's clock, from a response's Date header."""
		try:
			if response is None:
				response = requests.get(f"{self.server_url}/System/Info/Public", timeout=(5, 10))
			return parsedate_to_datetime(response.headers["Date"]).timestamp()
		except Exception:
			logging.debug("No Date header from Jellyfin, using our own clock")
			return time.time()

	def _parallel_items(self, params: dict[str, object], page_size: int) -> list[dict]:
		"""Fetch every page, a few at a time, counting them in the activity row. Raises OSError if one can't be fetched."""

		def fetch(start_index: int, count: bool) -> dict:
			if self.cancel_scan:
				raise ScanCancelledError
			response = requests.get(
				f"{self.server_url}/Items", headers=self._headers(), timeout=ITEM_FETCH_TIMEOUT,
				# Counting the whole library is slow on big ones, so only the first page asks
				params={**params, "startIndex": start_index, "limit": page_size, "enableTotalRecordCount": count})
			if response.status_code != HTTPStatus.OK:
				raise OSError(f"[{response.status_code}] {response.reason}")
			return response.json()

		first = fetch(0, True)
		total = first.get("TotalRecordCount", 0)
		self.scan_total = total
		pages = {0: first.get("Items", [])}
		self._count_page(len(pages[0]))
		# Step by what the server sent, in case it caps the page size
		stride = len(pages[0])
		with ThreadPoolExecutor(max_workers=PARALLEL_PAGES) as pool:
			futures = {
				pool.submit(fetch, start_index, False): start_index
				for start_index in (range(stride, total, stride) if stride else ())}
			try:
				for future in as_completed(futures):
					pages[futures[future]] = future.result().get("Items", [])
					self._count_page(len(pages[futures[future]]))
			except BaseException:
				pool.shutdown(cancel_futures=True)
				raise
		return [item for start_index in sorted(pages) for item in pages[start_index]]

	def _pages(self, params: dict[str, object], page_size: int = ITEM_PAGE_SIZE) -> Iterator[list[dict]]:
		"""Yield pages of items, raising OSError if one can't be fetched."""
		start_index = 0
		while True:
			if self.cancel_scan:
				raise ScanCancelledError
			# Only the first page counts the total, which is slow on big libraries
			page_params = {"sortBy": "SortName", "sortOrder": "Ascending", **params,
				"startIndex": start_index, "limit": page_size, "enableTotalRecordCount": start_index == 0}
			response = requests.get(
				f"{self.server_url}/Items", headers=self._headers(), params=page_params, timeout=ITEM_FETCH_TIMEOUT)
			if response.status_code != HTTPStatus.OK:
				raise OSError(f"Jellyfin returned [{response.status_code}] {response.reason}")
			data = response.json()
			page = data.get("Items", [])
			if start_index == 0:
				total = data.get("TotalRecordCount", 0)
			yield page
			start_index += len(page)
			if not page or start_index >= total:
				return

	def _items(self, params: dict[str, object], page_size: int = ITEM_PAGE_SIZE) -> list[dict]:
		return [item for page in self._pages(params, page_size) for item in page]

	def _server_key(self) -> str:
		"""Which server and user a library listing came from."""
		return f"{self.server_url}|{self.userId}"

	def _sorted(self, track_ids: list[int]) -> list[int]:
		"""Order library tracks the way a full import does."""
		library = self.pctl.master_library

		def number(text: object) -> int:
			try:
				return int(str(text).split("/", 1)[0])
			except ValueError:
				return -1

		track_ids.sort(key=lambda t: (library[t].album_artist, library[t].album, number(library[t].track_number)))
		track_ids.sort(key=lambda t: library[t].parent_folder_path)
		self.tauon.sort_track_2(0, track_ids)
		return track_ids

	def library_ids(self, code: str, parent_id: str | None = None) -> list[int] | None:
		"""Track ids for a library generator code, fetching only what changed since last time where possible.

		None if it failed or was cancelled, so the playlist keeps what it has.
		"""
		try:
			return self._library_ids(code, parent_id)
		except ScanCancelledError:
			logging.info("Jellyfin library scan cancelled")
			return None
		finally:
			self._scan_done()

	def _library_ids(self, code: str, parent_id: str | None) -> list[int] | None:
		sync = self.tauon.server_sync
		cache = sync.library_cache(code, self._server_key()) if self._ready() else None
		if cache is not None:
			self.scanning = True
			# The activity row shows this, which would otherwise be left over from another import
			self.gui.to_got = 0
			self.gui.request_frame()
			try:
				track_ids = self._library_delta(code, cache, parent_id)
			except ScanCancelledError:
				raise
			except Exception:
				logging.exception("Error updating the Jellyfin library, fetching all of it instead")
				track_ids = None
			finally:
				self.scanning = False
				self.scan_stage = ""
				self.gui.request_frame()
			if track_ids is not None:
				return track_ids

		started = self._server_time()
		track_ids = self.ingest_library(return_list=True, parent_id=parent_id)
		# Empty means it failed, or there's nothing worth remembering
		if not track_ids:
			return None
		server_ids = [self.pctl.master_library[t].url_key for t in track_ids]
		if cache is not None and parent_id is None:
			sync.purge_removed(JELLYFIN, cache.server_ids, server_ids)
		sync.store_library(code, LibraryCache("", server_ids, started, server=self._server_key()))
		return track_ids

	def _library_delta(self, code: str, cache: LibraryCache, parent_id: str | None) -> list[int] | None:
		"""Bring a cached library listing up to date, or None when it needs fetching in full.

		Metadata comes only for items saved since last time. Every item's id and user data come in a
		listing without media details, which finds removals and catches plays and favourites, as
		those don't count as saving the item. Plays sent with an earlier date are caught too.
		"""
		scope: dict[str, object] = {"userId": self.userId, "includeItemTypes": ["Audio"], "recursive": True}
		if parent_id:
			scope["parentId"] = parent_id
		full = {"fields": TRACK_FIELDS, "enableImages": True, "enableImageTypes": ["Primary"]}

		existing = self._existing()
		if any(x not in existing for x in cache.server_ids):
			# Tracks were removed here, such as by cleaning the database
			return None
		now = self._server_time()

		# Listed first, as it's what the activity row counts
		listed = [
			item for item in self._parallel_items(
				{"sortBy": "SortName", "sortOrder": "Ascending", **scope, "fields": [], "enableImages": False,
					"enableUserData": True}, BARE_PAGE_SIZE)
			if item.get("Id")]
		ids = [item["Id"] for item in listed]

		# Added or changed since last time; a rescan or tag edit saves the item again
		self.gui.to_got = 0
		self.scan_total = 0
		self.scan_stage = SCAN_CHANGES
		self.gui.request_frame()
		# A server rescan can re-save much of the library, so this may be most of an import
		changed = self._parallel_items(
			{"sortBy": "SortName", "sortOrder": "Ascending", **scope, **full,
				"minDateLastSaved": iso_time(cache.fetched - SINCE_MARGIN_S)}, ITEM_PAGE_SIZE)
		self.scan_stage = SCAN_PROCESSING
		self.gui.request_frame()
		for item in changed:
			if item.get("Type") == "Audio" and item.get("Id"):
				existing[item["Id"]] = self._store_track(item, existing).index

		# Saved before the margin but still unknown here, which shouldn't happen
		missing = [x for x in ids if x not in existing]
		if len(missing) > MISSING_LIMIT:
			return None
		for i in range(0, len(missing), 100):
			for item in self._items({"userId": self.userId, "ids": ",".join(missing[i:i + 100]), **full}):
				if item.get("Id"):
					existing[item["Id"]] = self._store_track(item, existing).index
		if parent_id is None:
			self.tauon.server_sync.purge_removed(JELLYFIN, cache.server_ids, ids)

		library = self.pctl.master_library
		favourites: dict[TrackClass, bool] = {}
		for item in listed:
			track_id = existing.get(item["Id"])
			user_data = item.get("UserData")
			if track_id is None or not user_data:
				continue
			library[track_id].server_plays = int(user_data.get("PlayCount") or 0)
			favourites[library[track_id]] = bool(user_data.get("IsFavorite"))
		self._set_favs(favourites)

		track_ids = self._sorted([existing[x] for x in ids if x in existing])
		self.gui.to_got = len(track_ids)
		self.tauon.server_sync.store_library(code, LibraryCache("", ids, now, server=self._server_key()))
		logging.info(f"Jellyfin library brought up to date: {len(changed)} of {len(ids)} tracks changed")
		return track_ids

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
			f"{self.server_url}/{point}",
			data=json.dumps(data),
			headers={
				"Token": self.accessToken,
				"X-Application": "Tauon/1.0",
				"Authorization": self._get_jellyfin_auth(),
				"Content-Type": "application/json",
			},
			timeout=10,
		)
