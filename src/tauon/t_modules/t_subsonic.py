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
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import requests

from tauon.t_modules.t_db_state import allocate_track_id
from tauon.t_modules.t_extra import StarRecord, with_url_scheme
from tauon.t_modules.t_remote_playlists import RemotePlaylist, RemotePlaylistSource
from tauon.t_modules.t_scrobble_queue import Outcome
from tauon.t_modules.t_server_sync import (
	LOVE,
	RATING,
	SUBSONIC,
	LibraryCache,
	PlaylistGoneError,
	RemotePlaylistState,
	ScanCancelledError,
)

if TYPE_CHECKING:
	from io import BytesIO
	from typing import Any

	from tauon.t_modules.t_main import AlbumStarStore, GuiVar, PlayerCtl, StarStore, Tauon, TrackClass
	from tauon.t_modules.t_prefs import Prefs
	from tauon.t_modules.t_scrobble_queue import PendingScrobble
	from tauon.t_modules.t_server_sync import ServerEdit

# Some broken servers send invalid JSON with control chars, see https://github.com/Taiko2k/Tauon/issues/1112
CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
# Songs per playlist request when the server can't take a POST body, keeping the URL short
PLAYLIST_CHUNK = 100


class SubsonicService(RemotePlaylistSource):
	code_prefix = "air"

	def __init__(self, tauon: Tauon, album_star_store: AlbumStarStore) -> None:
		self.tauon: Tauon = tauon
		self.gui: GuiVar = tauon.gui
		self.pctl: PlayerCtl = tauon.pctl
		self.prefs: Prefs = tauon.prefs
		self.t_title: str = tauon.t_title
		self.star_store: StarStore = tauon.star_store
		self.album_star_store: AlbumStarStore = album_star_store
		self.show_message = tauon.show_message
		self.scanning: bool = False
		# Set from the activity popover, the scan stops after the folders being read
		self.cancel_scan = False
		# Tracks the running scan expects, for the activity row's progress; 0 when unknown
		self.scan_total = 0
		# Songs on the server, from Navidrome's scan status
		self.server_song_count = 0
		self.last_music: list[int] | None = None
		# Whether the last full import read everything
		self.import_complete = False
		self.form_post: bool | None = None
		self.lyrics_scan_lock = threading.Lock()
		self.lyrics_scan_pending: set[str] = set()
		self.lyrics_scan_checked: set[str] = set()
		self.init_remote_playlists()


	def _as_list(self, value):
		"""Subsonic can return a dict instead of a list for single-item collections."""
		if value is None:
			return []
		if isinstance(value, list):
			return value
		return [value]

	def _created_time(self, created: str) -> float:
		"""Convert a Subsonic `created` timestamp to epoch seconds. Returns 0 if it can't be parsed."""
		try:
			dt = datetime.fromisoformat(str(created))
		except ValueError:
			return 0
		return (dt if dt.tzinfo else dt.replace(tzinfo=UTC)).timestamp()

	def _number(self, value: object) -> int:
		try:
			return int(value)
		except (TypeError, ValueError):
			return 0

	def _float(self, value: object) -> float | None:
		try:
			number = float(value)
		except (TypeError, ValueError):
			return None
		return number if math.isfinite(number) else None

	def _replaygain_pair(self, gain: object, peak: object) -> tuple[float | None, float | None]:
		gain = self._float(gain)
		peak = self._float(peak)
		if peak is not None and peak <= 0:
			peak = None
		# Some servers send zeros for untagged files instead of omitting them
		if gain == 0 and peak is None:
			gain = None
		return gain, peak

	def _apply_song_extras(self, nt: TrackClass, song: dict) -> None:
		"""Copy OpenSubsonic comment, MBIDs and ReplayGain from a song onto a track."""
		comment = song.get("comment")
		if isinstance(comment, str) and comment:
			nt.comment = comment

		mbid = song.get("musicBrainzId")
		if isinstance(mbid, str) and mbid:
			nt.musicbrainz_recordingid = mbid
		artist_ids = [
			artist["musicBrainzId"] for artist in self._as_list(song.get("artists"))
			if isinstance(artist, dict) and isinstance(artist.get("musicBrainzId"), str) and artist["musicBrainzId"]
		]
		if artist_ids:
			nt.musicbrainz_artistids = artist_ids

		rg = song.get("replayGain")
		if isinstance(rg, dict):
			nt.replaygain_track_gain, nt.replaygain_track_peak = self._replaygain_pair(
				rg.get("trackGain"), rg.get("trackPeak"))
			nt.replaygain_album_gain, nt.replaygain_album_peak = self._replaygain_pair(
				rg.get("albumGain"), rg.get("albumPeak"))

		nt.server_plays = self._number(song.get("playCount"))

	def _separate_albums(self, tracks: list[tuple[TrackClass, object]]) -> None:
		"""Give each album its own parent_folder_path, as Tauon groups albums by folder.

		Servers like Navidrome report a synthetic "Album Artist/Album/..." path, so two albums that share
		a name and artist (editions, duplicates) would otherwise land in one folder and merge.
		"""
		owners: dict[str, list[object]] = {}
		for nt, album_id in tracks:
			ids = owners.setdefault(nt.parent_folder_path, [])
			if album_id not in ids:
				ids.append(album_id)

		for nt, album_id in tracks:
			n = owners[nt.parent_folder_path].index(album_id)
			if n:
				nt.parent_folder_path = f"{nt.parent_folder_path} ({n + 1})"

	def _request_json(self, point: str, p: dict[str, str] | None = None) -> tuple[int, dict | None]:
		"""Make a request, returning the HTTP status alongside the decoded body.

		Unlike r(), this reports the status code and never shows the user an error, so callers can
		tell a missing endpoint or a rate limit apart from a server that's actually broken.
		"""
		url, params = self.r(point, p=p, get_url=True)
		response = requests.get(url, params=params, timeout=10)
		try:
			return response.status_code, json.loads(CONTROL_CHAR_RE.sub("", response.text))
		except json.decoder.JSONDecodeError:
			return response.status_code, None

	def _endpoint_exists(self, point: str, p: dict[str, str] | None = None) -> bool:
		"""Test whether the server implements an endpoint. Servers that don't route it return 404."""
		try:
			status, _d = self._request_json(point, p=p)
		except Exception:
			# Assume it exists so a transient failure gets reported by the normal path instead
			logging.exception(f"Error probing Subsonic endpoint {point}")
			return True
		return status != 404

	def _throttle_delay(self, status: int, d: dict | None) -> float | None:
		"""Seconds to wait before retrying a throttled request, or None if this wasn't a throttle."""
		if status != 429:
			return None
		detail = ""
		if isinstance(d, dict):
			detail = str(d.get("detail", ""))
		match = re.search(r"(\d+)\s*second", detail)
		if match:
			# Honour what the server actually asked for, capping only absurd values. Retrying sooner
			# than this just earns another 429, so the caller gives up rather than polling.
			return min(float(match.group(1)) + 1, 3600)
		return 10.0

	def _request_with_retry(
		self,
		point: str,
		p: dict[str, str] | None = None,
		attempts: int = 4,
		budget: float = 120.0,
	) -> tuple[int, dict | None] | None:
		"""Request an endpoint, waiting out rate limits within a bounded budget.

		Returns None once the server has throttled us past that budget, so callers report a failure
		instead of blocking the scan indefinitely.
		"""
		waited = 0.0

		for attempt in range(attempts):
			status, d = self._request_json(point, p=p)
			delay = self._throttle_delay(status, d)
			if delay is None:
				return status, d

			if attempt == attempts - 1 or waited + delay > budget:
				break

			logging.info(f"Rate limited on {point}, waiting {delay}s")
			time.sleep(delay)
			waited += delay

		logging.error(f"Giving up on {point}, rate limited after waiting {waited}s")
		return None

	def _list_albums(self, scope: dict[str, str] | None = None) -> list[tuple[str, str]]:
		"""Page through every album on the server via getAlbumList2.

		Used in place of folder browsing on servers without getMusicDirectory.
		"""
		albums: list[tuple[str, str]] = []
		seen: set[str] = set()
		duplicates = 0
		offset = 0
		size = 500  # The Subsonic spec caps a single page at 500

		while True:
			# Everything here is guarded, as escaping this would leave the scan flag stuck on
			try:
				result = self._request_with_retry(
					"getAlbumList2", p={"type": "alphabeticalByName", "size": size, "offset": offset, **(scope or {})},
				)
				if result is None:
					self.show_message(
						_("Error listing albums from Subsonic server"), "Rate limited", mode="error")
					return albums

				_status, d = result
				if not d or "subsonic-response" not in d:
					logging.error(f"Invalid response from Subsonic getAlbumList2: {d}")
					self.show_message(_("Error listing albums from Subsonic server"), mode="error")
					return albums

				subsonic_response = d["subsonic-response"]
				if subsonic_response.get("status") != "ok":
					logging.error(f"Subsonic getAlbumList2 failed: {subsonic_response.get('error')}")
					self.show_message(_("Error listing albums from Subsonic server"), mode="error")
					return albums

				# A missing key is a legitimately empty library, but the wrong type is a broken
				# server. Don't quietly turn that into an empty playlist.
				album_list = subsonic_response.get("albumList2", {})
				if not isinstance(album_list, dict):
					logging.error(f"Unexpected albumList2 from Subsonic server: {album_list!r}")
					self.show_message(_("Error listing albums from Subsonic server"), mode="error")
					return albums

				page = self._as_list(album_list.get("album"))

				for album in page:
					if not isinstance(album, dict):
						logging.warning(f"Skipping malformed album entry from Subsonic server: {album!r}")
						continue
					album_id = album.get("id")
					if album_id is None:
						continue
					# Servers page this by a non unique sort key, so the same album can come back on
					# two pages. Taking it twice would import every one of its tracks twice.
					if album_id in seen:
						duplicates += 1
						continue
					seen.add(album_id)
					albums.append((album_id, album.get("name", "")))

				if len(page) < size:
					break
				offset += size
			except Exception:
				logging.exception("Error listing albums from Subsonic server")
				self.show_message(_("Error listing albums from Subsonic server"), mode="error")
				return albums

		if duplicates:
			# Paging shifted under us, so some albums may equally have been skipped
			logging.warning(f"Subsonic server returned {duplicates} duplicate albums while paging")

		return albums

	def _search3_songs(self, scope: dict[str, str] | None = None) -> list[tuple[TrackClass, str, str, int]] | None:
		"""Fetch every song with an empty search3 query. Returns None if that doesn't work on this server."""
		songs: list[tuple[TrackClass, str, str, int]] = []
		seen: set[str] = set()
		album_ids: dict[str, object] = {}

		def fetch(offset: int, count: int) -> list[dict] | None:
			try:
				result = self._request_with_retry(
					"search3",
					p={
						"query": '""', "songCount": count, "songOffset": offset, "artistCount": 0, "albumCount": 0,
						**(scope or {}),
					},
				)
			except Exception:
				logging.exception("Error paging songs with search3")
				return None
			if result is None:
				return None

			_status, d = result
			response = d.get("subsonic-response", {}) if isinstance(d, dict) else {}
			if response.get("status") != "ok":
				logging.warning(f"search3 sync failed, falling back to folder scan: {response.get('error')}")
				return None
			return self._as_list(response.get("searchResult3", {}).get("song"))

		first = fetch(0, 500)
		if first is None:
			return None
		# Some servers send fewer than 500 songs per page, so step by the first page's size
		stride = len(first)
		offset = stride
		pages = [first]
		done = False

		with ThreadPoolExecutor(max_workers=4) as pool:
			while True:
				for i, page in enumerate(pages):
					new = [s for s in page if isinstance(s, dict) and s.get("id") and s["id"] not in seen]
					# A server that ignores songOffset keeps sending the same page
					if not new:
						done = True
						break
					if len(page) < stride and any(pages[i + 1:]):
						logging.warning("search3 returned a short page mid-library, falling back to folder scan")
						return None
					self._add_search3_songs(new, seen, songs, album_ids)

				self.gui.request_frame()
				if done:
					break
				if self.cancel_scan:
					raise ScanCancelledError
				pages = list(pool.map(lambda o: fetch(o, stride), [offset + n * stride for n in range(4)]))
				if any(page is None for page in pages):
					return None
				offset += 4 * stride

		if not songs:
			logging.info("search3 returned no songs, falling back to folder scan")
			return None

		# Songs come back in no particular order within an album, so keep albums in the order the
		# server listed them and put each one's tracks in disc and track order
		album_order: dict[object, int] = {}
		for song in songs:
			album_order.setdefault(album_ids[song[2]], len(album_order))
		songs.sort(key=lambda song: (
			album_order[album_ids[song[2]]],
			self._number(song[0].disc_number),
			self._number(song[0].track_number),
		))
		self._separate_albums([(song[0], album_ids[song[2]]) for song in songs])
		return songs

	def _add_search3_songs(
		self, new: list[dict], seen: set[str], songs: list[tuple[TrackClass, str, str, int]],
		album_ids: dict[str, object],
	) -> None:
		for song in new:
			seen.add(song["id"])
			self.gui.to_got += 1
			nt = self.tauon.TrackClass()

			album_artists = [
				artist["name"] for artist in self._as_list(song.get("albumArtists"))
				if isinstance(artist, dict) and artist.get("name")
			]
			nt.album_artist = song.get("displayAlbumArtist") or " / ".join(album_artists)
			if "title" in song:
				nt.title = song["title"]
			if "artist" in song:
				nt.artist = song["artist"]
			if "album" in song:
				nt.album = song["album"]
			if "track" in song:
				nt.track_number = song["track"]
			if "discNumber" in song:
				nt.disc_number = song["discNumber"]
			if "year" in song:
				nt.date = str(song["year"])
			if "duration" in song:
				nt.length = song["duration"]
			if "created" in song:
				nt.modified_time = self._created_time(song["created"])
			genre_names = [
				g["name"] for g in self._as_list(song.get("genres")) if isinstance(g, dict) and g.get("name")
			]
			if genre_names:
				if len(genre_names) > 1:
					nt.genres = genre_names
				nt.genre = " / ".join(genre_names)

			name = song.get("album", "")
			nt.file_ext = "SUB"
			nt.parent_folder_name = name
			if "path" in song:
				nt.fullpath = song["path"]
				nt.parent_folder_path = os.path.dirname(song["path"])
				nt.parent_folder_name = os.path.basename(nt.parent_folder_path) or name
			if "coverArt" in song:
				nt.art_url_key = song["coverArt"]
			nt.url_key = song["id"]
			nt.subsonic_folder_id = song.get("parent")
			nt.is_network = True
			self._apply_song_extras(nt, song)

			album_ids[song["id"]] = song.get("albumId") or (nt.parent_folder_path, name)
			songs.append((nt, name, song["id"], int(song.get("userRating", 0))))

	def _response(self, d: dict | None) -> dict | None:
		"""The subsonic-response body if the request succeeded, else None."""
		response = d.get("subsonic-response") if isinstance(d, dict) else None
		if not isinstance(response, dict) or response.get("status") != "ok":
			logging.error(f"Subsonic request failed: {response.get('error') if isinstance(response, dict) else d}")
			return None
		return response

	def _list_playlists(self) -> list[RemotePlaylist] | None:
		response = self._response(self.r("getPlaylists", show_errors=False))
		if response is None:
			self.remote_playlists_error = _("Could not connect to the server")
			return None
		return [
			RemotePlaylist(
				id=str(p["id"]),
				name=p.get("name") or str(p["id"]),
				count=self._number(p.get("songCount")),
				# Navidrome marks smart playlists read-only, and adds validUntil once they've been evaluated.
				# Other users' playlists can be read-only too, hence the owner check.
				smart=bool(p.get("validUntil")) or (
					p.get("readonly") is True and p.get("owner") == self.prefs.subsonic_user),
			)
			for p in self._as_list((response.get("playlists") or {}).get("playlist"))
			if isinstance(p, dict) and p.get("id") is not None
		]

	def playlist_track_ids(self, playlist_id: str) -> list[int] | None:
		try:
			remote = self.fetch_remote_playlist(playlist_id)
		except PlaylistGoneError:
			return None
		return None if remote is None else remote.track_ids

	def sync_configured(self) -> bool:
		return bool(self.prefs.subsonic_server and self.prefs.subsonic_user)

	def _outcome(self, point: str, p: dict[str, object]) -> Outcome:
		try:
			d = self.r(point, p=p, show_errors=False)
		except requests.RequestException as e:
			logging.warning(f"Could not reach the Subsonic server: {e}")
			return Outcome.RETRY
		except Exception:
			logging.exception(f"Error sending {point} to Subsonic")
			return Outcome.RETRY
		response = d.get("subsonic-response") if isinstance(d, dict) else None
		if not isinstance(response, dict):
			return Outcome.RETRY
		if response.get("status") == "ok":
			return Outcome.SENT
		error = response.get("error") or {}
		logging.warning(f"Subsonic {point} failed: {error}")
		# 10: missing parameter, 70: not found
		return Outcome.DROP if error.get("code") in (10, 70) else Outcome.RETRY

	def push_edit(self, edit: ServerEdit) -> Outcome:
		"""Send a love as a star, or a rating in whole stars."""
		if edit.kind == LOVE:
			return self._outcome("star" if edit.value else "unstar", {"id": edit.server_id})
		return self._outcome("setRating", {"id": edit.server_id, "rating": math.ceil(edit.value / 2)})

	def _supports_form_post(self) -> bool:
		"""Whether the server takes parameters in a POST body (OpenSubsonic formPost)."""
		if self.form_post is None:
			try:
				response = self._response(self.r("getOpenSubsonicExtensions", show_errors=False)) or {}
			except Exception:
				logging.exception("Error listing OpenSubsonic extensions")
				return False
			self.form_post = any(
				isinstance(e, dict) and e.get("name") == "formPost"
				for e in self._as_list(response.get("openSubsonicExtensions")))
		return self.form_post

	def fetch_remote_playlist(self, remote_id: str) -> RemotePlaylistState | None:
		"""A playlist and its songs, adding any that aren't in the library yet. None if it couldn't be fetched."""
		try:
			d = self.r("getPlaylist", p={"id": remote_id}, show_errors=False)
		except Exception:
			logging.exception("Error fetching Subsonic playlist")
			return None
		response = d.get("subsonic-response") if isinstance(d, dict) else None
		if not isinstance(response, dict):
			return None
		if response.get("status") != "ok":
			if (response.get("error") or {}).get("code") == 70:
				raise PlaylistGoneError
			logging.error(f"Error fetching Subsonic playlist: {response.get('error')}")
			return None
		playlist = response.get("playlist") or {}
		entries = [e for e in self._as_list(playlist.get("entry")) if isinstance(e, dict) and e.get("id")]
		owner = playlist.get("owner")
		# Navidrome marks smart playlists and other users' playlists read-only
		# Logins aren't case sensitive, so neither is the owner
		readonly = playlist.get("readonly") is True or bool(playlist.get("validUntil")) or bool(
			owner and str(owner).casefold() != self.prefs.subsonic_user.casefold())
		return RemotePlaylistState(
			[str(e["id"]) for e in entries], self._song_ids(entries), str(playlist.get("changed") or ""),
			playlist.get("name") or "", readonly)

	def _update_playlist(self, p: dict[str, object], post: bool = False) -> bool:
		try:
			return self._response(self.r("updatePlaylist", p=p, show_errors=False, post=post)) is not None
		except Exception:
			logging.exception("Error updating Subsonic playlist")
			return False

	def write_remote_playlist(
		self, remote_id: str, current: RemotePlaylistState, server_ids: list[str], name: str | None,
	) -> bool:
		"""Replace a playlist's songs by removing every entry and adding the new list, as there's no reorder."""
		count = len(current.server_ids)
		if self._supports_form_post():
			p: dict[str, object] = {
				"playlistId": remote_id, "songIndexToRemove": [str(i) for i in range(count)], "songIdToAdd": server_ids}
			if name:
				p["name"] = name
			return self._update_playlist(p, post=True)

		# Removing from the end keeps the earlier indexes valid between requests
		batches: list[dict[str, object]] = [
			{"songIndexToRemove": [str(i) for i in range(max(0, end - PLAYLIST_CHUNK), end)]}
			for end in range(count, 0, -PLAYLIST_CHUNK)]
		batches += [
			{"songIdToAdd": server_ids[i:i + PLAYLIST_CHUNK]} for i in range(0, len(server_ids), PLAYLIST_CHUNK)]
		if name:
			batches.insert(0, {"name": name})
		return all(self._update_playlist({"playlistId": remote_id, **batch}) for batch in batches)

	def create_remote_playlist(self, name: str, server_ids: list[str]) -> str | None:
		"""Create a playlist, returning its id."""
		post = self._supports_form_post()
		first, rest = (server_ids, []) if post else (server_ids[:PLAYLIST_CHUNK], server_ids[PLAYLIST_CHUNK:])
		try:
			response = self._response(
				self.r("createPlaylist", p={"name": name, "songId": first}, show_errors=False, post=post))
			if response is None:
				return None
			playlist_id = (response.get("playlist") or {}).get("id")
			if not playlist_id:
				# Before API 1.14 the new playlist isn't returned, so find the newest with that name
				listed = self._response(self.r("getPlaylists", show_errors=False)) or {}
				matches = [
					p for p in self._as_list((listed.get("playlists") or {}).get("playlist"))
					if isinstance(p, dict) and p.get("name") == name and p.get("id") is not None]
				if not matches:
					return None
				playlist_id = max(matches, key=lambda p: str(p.get("created") or ""))["id"]
		except Exception:
			logging.exception("Error creating Subsonic playlist")
			return None
		for i in range(0, len(rest), PLAYLIST_CHUNK):
			if not self._update_playlist({"playlistId": playlist_id, "songIdToAdd": rest[i:i + PLAYLIST_CHUNK]}):
				return None
		return str(playlist_id)

	def library_stamp(self) -> str | None:
		"""Changes whenever the library might have, or None when the server can't tell."""
		try:
			d = self.r("getScanStatus", show_errors=False)
			response = d.get("subsonic-response") if isinstance(d, dict) else None
			status = (response or {}).get("scanStatus") or {}
			if status.get("scanning"):
				return None
			self.server_song_count = self._number(status.get("count"))
			if status.get("lastScan"):
				# Navidrome
				return f"scan:{status['lastScan']}:{status.get('count')}"
			d = self.r("getIndexes", show_errors=False)
			response = d.get("subsonic-response") if isinstance(d, dict) else None
			modified = ((response or {}).get("indexes") or {}).get("lastModified")
		except Exception:
			logging.exception("Error checking the Subsonic library for changes")
			return None
		return f"index:{modified}" if modified else None

	def library_ids(self, code: str, music_folder: str | None = None) -> list[int] | None:
		"""Track ids for a library generator code, reusing the last listing while the server reports no changes.

		None if it failed or was cancelled, so the playlist keeps what it has.
		"""
		try:
			return self._library_ids(code, music_folder)
		except ScanCancelledError:
			logging.info("Subsonic library scan cancelled")
			return None
		finally:
			self.scanning = False
			self.cancel_scan = False
			self.scan_total = 0
			self.gui.request_frame()

	def _library_ids(self, code: str, music_folder: str | None) -> list[int] | None:
		sync = self.tauon.server_sync
		stamp = self.library_stamp()
		# After library_stamp, as connecting fills in a missing scheme
		server = f"{self.prefs.subsonic_server}|{self.prefs.subsonic_user}"
		cache = sync.library_cache(code, server)
		if stamp and cache is not None and cache.stamp == stamp:
			track_ids = sync.library_ids(SUBSONIC, cache.server_ids)
			if track_ids is not None:
				logging.info("Subsonic library unchanged, reusing the last listing")
				starred = self._starred()
				if starred is not None:
					self._apply_stars(track_ids, {str(s.get("id")) for s in self._as_list(starred.get("song"))})
				if not music_folder:
					self.last_music = track_ids
				return track_ids

		# The server's count covers every folder
		self.scan_total = 0 if music_folder else self.server_song_count
		track_ids = self.get_music3(return_list=True, music_folder=music_folder)
		if not track_ids:
			return None
		if not self.import_complete:
			return track_ids
		server_ids = [self.pctl.master_library[t].url_key for t in track_ids]
		if cache is not None and not music_folder:
			sync.purge_removed(SUBSONIC, cache.server_ids, server_ids)
		sync.store_library(code, LibraryCache(stamp or "", server_ids, server=server))
		return track_ids

	def _apply_stars(self, track_ids: list[int], starred: set[str]) -> None:
		"""Match loves to the server's stars, except where an unsent edit made here is newer."""
		pending = self.tauon.server_sync.pending(SUBSONIC, LOVE)
		for track_id in track_ids:
			track = self.pctl.master_library[track_id]
			if track.url_key in pending:
				continue
			star = self.star_store.full_get(track_id)
			if track.url_key in starred:
				if star is None:
					star = StarRecord()
				if not star.loved:
					star.loved = True
					self.star_store.insert(track_id, star)
			elif star is not None and star.loved:
				self.star_store.insert(track_id, StarRecord(star.playtime, star.rating))

	def _song_ids(self, entries: list) -> list[int]:
		"""Tauon track ids for song entries, adding any that aren't in the library yet."""
		entries = [e for e in entries if isinstance(e, dict) and e.get("id")]
		existing: dict[str, int] = {}
		for track_id, track in self.pctl.master_library.items():
			if track.is_network and track.file_ext == "SUB":
				existing[track.url_key] = track_id

		# Songs that aren't in the library yet (it was never imported, or changed since) get added
		missing = list({e["id"]: e for e in entries if e["id"] not in existing}.values())
		songs: list[tuple[TrackClass, str, str, int]] = []
		self._add_search3_songs(missing, set(), songs, {})
		for nt, _album, song_id, rating in songs:
			nt.index = allocate_track_id(self.pctl)
			self.pctl.master_library[nt.index] = nt
			existing[song_id] = nt.index
			if rating:
				self.star_store.set_rating(nt.index, rating * 2)

		return [existing[e["id"]] for e in entries]

	def ping(self) -> bool:
		"""Quietly check the server and login, for the Add music box."""
		try:
			return self._response(self.r("ping", show_errors=False)) is not None
		except Exception:
			logging.exception("Error pinging Subsonic server")
			return False

	def list_libraries(self) -> list[RemotePlaylist] | None:
		"""The server's music folders, or None if they couldn't be fetched."""
		response = self._response(self.r("getMusicFolders", show_errors=False))
		if response is None:
			return None
		return [
			RemotePlaylist(id=str(f["id"]), name=f.get("name") or str(f["id"]))
			for f in self._as_list((response.get("musicFolders") or {}).get("musicFolder"))
			if isinstance(f, dict) and f.get("id") is not None
		]

	def _starred(self) -> dict | None:
		try:
			response = self._response(self.r("getStarred2", show_errors=False))
		except Exception:
			logging.exception("Error fetching Subsonic starred items")
			return None
		return None if response is None else response.get("starred2") or {}

	def favourite_tracks(self) -> list[int] | None:
		"""Track ids for the airfav generator code."""
		starred = self._starred()
		if starred is None:
			return None
		return self._song_ids(self._as_list(starred.get("song")))

	def favourite_albums(self) -> list[int] | None:
		"""Track ids for the airfavalb generator code."""
		starred = self._starred()
		if starred is None:
			return None
		songs: list = []
		for album in self._as_list(starred.get("album")):
			if not isinstance(album, dict) or album.get("id") is None:
				continue
			try:
				response = self._response(self.r("getAlbum", p={"id": album["id"]}, show_errors=False))
			except Exception:
				logging.exception("Error fetching Subsonic album")
				continue
			if response is not None:
				songs.extend(self._as_list((response.get("album") or {}).get("song")))
		return self._song_ids(songs)

	def r(
		self,
		point: str,
		p: dict[str, str] | None = None,
		binary: bool = False,
		get_url: bool = False,
		show_errors: bool = True,
		post: bool = False,
	):
		salt = secrets.token_hex(8)
		# Typed without http:// or https://, fill it in so the settings field shows what's used. 4533 is Navidrome's.
		self.prefs.subsonic_server = with_url_scheme(self.prefs.subsonic_server, 4533)
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

		response = requests.post(url, data=params, timeout=30) if post else requests.get(url, params=params, timeout=10)

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

		subsonic_response = d["subsonic-response"]
		if subsonic_response["status"] != "ok":
			if show_errors:
				self.show_message(_("Subsonic Error: ") + response.text, mode="warning")
				logging.error(f"Subsonic Error: {response.text}")
			else:
				logging.debug(f"Subsonic request failed for {point}: {subsonic_response.get('error')}")

		return d

	def _timestamp_from_milliseconds(self, milliseconds: int) -> str:
		milliseconds = max(0, milliseconds)
		minutes = milliseconds // 60000
		seconds = (milliseconds % 60000) // 1000
		remainder = milliseconds % 1000
		return f"{minutes:02d}:{seconds:02d}.{remainder:03d}"

	def _plain_from_structured_lyrics(self, structured_lyrics: dict) -> str:
		lines = []
		for line in self._as_list(structured_lyrics.get("line")):
			if not isinstance(line, dict):
				continue
			value = line.get("value")
			if value is not None:
				lines.append(str(value))
		return "\n".join(lines).strip()

	def _lrc_from_structured_lyrics(self, structured_lyrics: dict) -> str:
		try:
			offset = int(float(structured_lyrics.get("offset", 0)))
		except (TypeError, ValueError):
			offset = 0

		lines = []
		for line in self._as_list(structured_lyrics.get("line")):
			if not isinstance(line, dict):
				continue
			value = line.get("value")
			if value is None or "start" not in line:
				continue
			try:
				start = int(float(line["start"]) - offset)
			except (TypeError, ValueError):
				continue
			lines.append(f"[{self._timestamp_from_milliseconds(start)}]{value}")
		return "\n".join(lines).strip()

	def _lyrics_from_structured_response(self, response: dict | None) -> tuple[str, str]:
		if not response:
			return "", ""

		subsonic_response = response.get("subsonic-response", {})
		if subsonic_response.get("status") != "ok":
			return "", ""

		lyrics_list = subsonic_response.get("lyricsList", {})
		structured_lyrics = self._as_list(lyrics_list.get("structuredLyrics"))
		main_lyrics = [
			lyrics for lyrics in structured_lyrics
			if isinstance(lyrics, dict) and lyrics.get("kind", "main") == "main"
		]
		structured_lyrics = main_lyrics or [lyrics for lyrics in structured_lyrics if isinstance(lyrics, dict)]

		for lyrics in structured_lyrics:
			if lyrics.get("synced"):
				plain = self._plain_from_structured_lyrics(lyrics)
				synced = self._lrc_from_structured_lyrics(lyrics)
				if synced:
					return plain, synced

		for lyrics in structured_lyrics:
			plain = self._plain_from_structured_lyrics(lyrics)
			if plain:
				return plain, ""

		return "", ""

	def _lyrics_from_legacy_response(self, response: dict | None) -> tuple[str, str]:
		if not response:
			return "", ""

		subsonic_response = response.get("subsonic-response", {})
		if subsonic_response.get("status") != "ok":
			return "", ""

		lyrics = subsonic_response.get("lyrics", {})
		if isinstance(lyrics, dict):
			return str(lyrics.get("value") or "").strip(), ""
		if isinstance(lyrics, str):
			return lyrics.strip(), ""
		return "", ""

	def get_lyrics(self, track_object: TrackClass) -> tuple[str, str]:
		if track_object.url_key:
			try:
				response = self.r("getLyricsBySongId", p={"id": track_object.url_key}, show_errors=False)
				lyrics, synced = self._lyrics_from_structured_response(response)
				if lyrics or synced:
					return lyrics, synced
			except Exception:
				logging.exception("Error connecting for OpenSubsonic lyrics")

		if track_object.artist and track_object.title:
			try:
				response = self.r(
					"getLyrics",
					p={"artist": track_object.artist, "title": track_object.title},
					show_errors=False,
				)
				return self._lyrics_from_legacy_response(response)
			except Exception:
				logging.exception("Error connecting for Subsonic lyrics")

		return "", ""

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
					logging.info(f"Found lyrics from Subsonic server for {track_object.artist} - {track_object.title}")
					self.gui.request_frame()
					self.tauon.lyrics_ren_mini.to_reload = True
					self.tauon.timed_lyrics_ren.index = -1
					self.pctl.notify_database_changed()
					self.pctl.refresh_now_playing(force=True)
			except Exception:
				logging.exception("Failed to scan lyrics from Subsonic server")
			finally:
				with self.lyrics_scan_lock:
					self.lyrics_scan_pending.discard(track_object.url_key)
					self.lyrics_scan_checked.add(track_object.url_key)

		thread = threading.Thread(target=worker)
		thread.daemon = True
		thread.start()

	def get_cover(self, track_object: TrackClass) -> BytesIO:
		response = self.r("getCoverArt", p={"id": track_object.art_url_key}, binary=True)
		try:
			response.decode("utf-8")
			raise ValueError(f"Expected binary data with an image but got a valid string: {response}")
		except UnicodeDecodeError:
			pass

		return io.BytesIO(response)

	def resolve_stream(self, key: str) -> tuple[str, dict[str, str]] | bytes | Any | None:
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

	def submit_scrobble(self, item: PendingScrobble) -> Outcome:
		"""Count a play on the server at the time it happened."""
		try:
			response = self.r(
				"scrobble", p={"id": item.server_id, "submission": "true", "time": str(item.timestamp * 1000)},
				show_errors=False)
		except requests.RequestException as e:
			logging.warning(f"Could not reach the Subsonic server: {e}")
			return Outcome.RETRY
		except Exception:
			logging.exception("Error connecting for scrobble on airsonic")
			return Outcome.RETRY
		if not response:
			return Outcome.RETRY
		subsonic_response = response["subsonic-response"]
		if subsonic_response.get("status") == "ok":
			return Outcome.SENT
		error = subsonic_response.get("error", {})
		logging.warning(f"Subsonic scrobble failed: {error}")
		# 10: missing parameter, 70: song no longer on the server
		return Outcome.DROP if error.get("code") in (10, 70) else Outcome.RETRY

	def set_album_rating(self, track_object: TrackClass, rating: int) -> bool:
		id = track_object.subsonic_folder_id
		if id is not None:
			try:
				a = self.r("setRating", p={"id": id, "rating": math.ceil(rating / 2)})
			except Exception:
				logging.exception("Error connect for set rating on airsonic")
		return True

	def star_album(self, track_object: TrackClass) -> bool:
		id = track_object.subsonic_folder_id
		if id is not None:
			try:
				a = self.r("star", p={"id": id})
			except Exception:
				logging.exception("Error connect for star Album on airsonic")
		return True

	def get_music3(self, return_list: bool = False, music_folder: str | None = None) -> list[int] | None:
		"""Import the whole library, or only the music folder with that id."""
		scope = {"musicFolderId": music_folder} if music_folder else {}
		self.scanning = True
		self.import_complete = False
		self.gui.to_got = 0

		existing: dict[str, int] = {}

		for track_id, track in self.pctl.master_library.items():
			if track.is_network and track.file_ext == "SUB":
				existing[track.url_key] = track_id

		try:
			a = self.r("getIndexes", p=scope)
		except Exception:
			logging.exception("Error connecting to Airsonic server")
			self.show_message(_("Error connecting to Subsonic server"), mode="error")
			self.scanning = False
			return []
		if not a or "subsonic-response" not in a:
			logging.error("Invalid response from Airsonic getIndexes")
			self.show_message(_("Error connecting to Subsonic server"), mode="error")
			self.scanning = False
			return []

		# {'openSubsonic': True, 'serverVersion': '8', 'status': 'failed', 'type': 'lms', 'version': '1.16.0', 'error': {'code': 41, 'message': 'Token authentication not supported for LDAP users.'}}
		if "indexes" not in a["subsonic-response"]:
			self.scanning = False
			if "error" in a["subsonic-response"]:
				logging.debug(a["subsonic-response"])
				self.show_message(
					_("Error connecting to Subsonic server"),
					f"{a['subsonic-response']['error']['code']}: {a['subsonic-response']['error']['message']}",
					mode="error",
				)
				return None
			logging.critical("Failed to find expected key 'indexes', report a bug with the log below!")
			logging.critical(a["subsonic-response"])
			self.show_message(
				_("Error connecting to Subsonic server"), "See console log for more details", mode="error"
			)
			return None

		indexes = self._as_list(a["subsonic-response"]["indexes"].get("index"))

		folders: list[tuple[str, str]] = []

		for letter in indexes:
			artists = self._as_list(letter.get("artist"))
			for artist in artists:
				folders.append(
					(
						artist["id"],
						artist["name"],
					)
				)

		# OpenSubsonic servers return the whole library for an empty search3 query
		search3_songs = None
		if a["subsonic-response"].get("openSubsonic"):
			search3_songs = self._search3_songs(scope)
		if search3_songs is not None:
			logging.info(f"Read {len(search3_songs)} songs with search3")
			folders = []

		# Some servers (notably Funkwhale) don't implement the folder browsing endpoints at all, as a
		# folder hierarchy doesn't match how they store music. Walk albums by tag instead on those.
		# https://github.com/Taiko2k/Tauon/issues/2336
		tag_mode = bool(folders) and not self._endpoint_exists("getMusicDirectory", p={"id": folders[0][0]})
		if tag_mode:
			logging.info("Server has no getMusicDirectory, falling back to scanning albums by tag")
			folders = self._list_albums(scope)

		playlist: list[int] = []
		songsets: list[tuple[TrackClass, str, str, int]] = []
		for i in range(len(folders)):
			songsets.append([])
		if search3_songs is not None:
			songsets.append(search3_songs)
		statuses = [0] * len(folders)
		# Folders that couldn't be read, so the import is incomplete
		unread: list[str] = []

		def getsongs(
			index: int, folder_id: str, name: str, inner: bool = False, parent: dict[str, str | int] | None = None
		) -> None:
			try:
				d = self.r("getMusicDirectory", p={"id": folder_id})
				if "child" not in d["subsonic-response"]["directory"]:
					if not inner:
						statuses[index] = 2
					return

			except json.decoder.JSONDecodeError:
				logging.exception("Error reading Airsonic directory")
				unread.append(folder_id)
				if not inner:
					statuses[index] = 2
				self.show_message(_("Error reading Subsonic directory!"), mode="warning")
				return
			except Exception:
				logging.exception("Unknown Error reading Airsonic directory")
				unread.append(folder_id)
				if not inner:
					statuses[index] = 2
				return

			items = self._as_list(d["subsonic-response"]["directory"].get("child"))

			self.gui.request_frame()

			for item in items:
				if item.get("isDir"):
					if "userRating" in item and "artist" in item:
						rating = item["userRating"]
						if (
							self.album_star_store.get_rating_artist_title(item["artist"], item["title"]) == 0
							and rating == 0
						):
							pass
						else:
							self.album_star_store.set_rating_artist_title(
								item["artist"], item["title"], int(rating * 2)
							)

					getsongs(index, item["id"], item["title"], inner=True, parent=item)
					continue
				self.gui.to_got += 1
				song = item
				#logging.debug(item)
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
				if "created" in song:
					nt.modified_time = self._created_time(song["created"])
				# [{'name': 'Pop'}, {'name': 'Rap'}, {'name': 'Rock'}]
				if song.get("genres"):
					genres: dict[str, str] = song["genres"]
					genre_names = [g["name"] for g in genres if g.get("name")]
					if not genre_names:
						logging.warning(f"Failed to parse genres from subsonic, got: {genres}")
					if len(genres) > 1:
						nt.genres = genre_names
					nt.genre = " / ".join(genre_names)

				nt.file_ext = "SUB"
				nt.parent_folder_name = name
				if "path" in song:
					nt.fullpath = song["path"]
					nt.parent_folder_path = os.path.dirname(song["path"])
				if "coverArt" in song:
					nt.art_url_key = song["coverArt"]
				nt.url_key = song["id"]
				nt.subsonic_folder_id = folder_id
				nt.is_network = True
				self._apply_song_extras(nt, song)

				rating = 0
				if "userRating" in song:
					rating = int(song["userRating"])

				songsets[index].append((nt, name, song["id"], rating))

			if inner:
				return
			statuses[index] = 2

		failed_albums: list[str] = []
		failed_albums_lock = threading.Lock()

		def album_failed(album_id: str) -> None:
			"""Warn once that the import is incomplete, rather than quietly dropping albums."""
			with failed_albums_lock:
				first = not failed_albums
				failed_albums.append(album_id)
			if first:
				self.show_message(
					_("Some albums could not be read from the server"),
					"See console log for more details",
					mode="warning",
				)

		def getalbum(index: int, album_id: str, name: str) -> None:
			"""Fetch one album's tracks by tag, for servers without folder browsing."""
			try:
				result = self._request_with_retry("getAlbum", p={"id": album_id})
				if result is None:
					logging.error(f"Gave up reading album {album_id!r}, server kept rate limiting us")
					album_failed(album_id)
					return

				_status, d = result
				if not d or "album" not in d.get("subsonic-response", {}):
					logging.error(f"Failed to read album {album_id!r} from Subsonic server: {d}")
					album_failed(album_id)
					return

				album = d["subsonic-response"]["album"]
				album_artist = album.get("artist", "")
				album_mbid = album.get("musicBrainzId")
				if not isinstance(album_mbid, str):
					album_mbid = ""
				# Only albums carry genres here, tracks don't, so every track takes the album's
				genre_names = [
					g["name"] for g in self._as_list(album.get("genres"))
					if isinstance(g, dict) and g.get("name")
				]

				self.gui.request_frame()

				for song in self._as_list(album.get("song")):
					self.gui.to_got += 1
					nt = self.tauon.TrackClass()

					nt.album_artist = album_artist
					if "title" in song:
						nt.title = song["title"]
					if "artist" in song:
						nt.artist = song["artist"]
					if "album" in song:
						nt.album = song["album"]
					if "track" in song:
						nt.track_number = song["track"]
					if "discNumber" in song:
						nt.disc_number = song["discNumber"]
					if "year" in song:
						nt.date = str(song["year"])
					if "duration" in song:
						nt.length = song["duration"]
					if "created" in song:
						nt.modified_time = self._created_time(song["created"])
					if genre_names:
						if len(genre_names) > 1:
							nt.genres = genre_names
						nt.genre = " / ".join(genre_names)

					nt.file_ext = "SUB"
					nt.parent_folder_name = name
					if "path" in song:
						nt.fullpath = song["path"]
						nt.parent_folder_path = os.path.dirname(song["path"])
						nt.parent_folder_name = os.path.basename(nt.parent_folder_path) or name
					if "coverArt" in song:
						nt.art_url_key = song["coverArt"]
					nt.url_key = song["id"]
					# subsonic_folder_id is deliberately left unset. It holds a folder id, and album
					# ids aren't interchangeable with it, so album star/rating cleanly no-op instead
					# of acting on an unrelated item.
					nt.is_network = True
					self._apply_song_extras(nt, song)
					if album_mbid:
						nt.musicbrainz_albumid = album_mbid

					songsets[index].append((nt, name, song["id"], 0))
			except Exception:
				logging.exception("Error reading album from Subsonic server")
				album_failed(album_id)
			finally:
				statuses[index] = 2

		fetch = getalbum if tag_mode else getsongs

		i = -1
		for folder_id, name in folders:
			i += 1
			while statuses.count(1) > 3:
				time.sleep(0.1)
			if self.cancel_scan:
				break

			statuses[i] = 1
			t = threading.Thread(target=fetch, args=([i, folder_id, name]))
			t.daemon = True
			t.start()

		# Once cancelled, only wait for the folders already being read
		while statuses.count(1) or (not self.cancel_scan and statuses.count(2) != len(statuses)):
			time.sleep(0.1)
		if self.cancel_scan:
			raise ScanCancelledError

		if tag_mode:
			self._separate_albums([(song[0], folders[i][0]) for i, sset in enumerate(songsets) for song in sset])

		try:
			a = self.r("getStarred2")
		except Exception:
			logging.exception("Error connecting to Airsonic server")
			self.show_message(_("Error connecting to Subsonic server"), mode="error")
			self.scanning = False
			return []

		# None when the stars couldn't be read, so loves are left alone
		liked_tracks: set[str] | None = None
		starred2 = a.get("subsonic-response", {}).get("starred2") if isinstance(a, dict) else None
		if isinstance(starred2, dict):
			liked_tracks = {song["id"] for song in self._as_list(starred2.get("song")) if song.get("id")}
		# An unsent rating made here is newer than the server's
		pending_ratings = self.tauon.server_sync.pending(SUBSONIC, RATING)

		for sset in songsets:
			for nt, name, song_id, rating in sset:
				id = existing.get(song_id)
				if id is None:
					id = allocate_track_id(self.pctl)

				nt.index = id
				self.pctl.master_library[id] = nt

				playlist.append(nt.index)

				if nt.url_key in pending_ratings or (self.star_store.get_rating(nt.index) == 0 and rating == 0):
					pass
				else:
					self.star_store.set_rating(nt.index, rating * 2)

		if liked_tracks is not None:
			self._apply_stars(playlist, liked_tracks)

		self.import_complete = not failed_albums and not unread
		self.scanning = False
		if not music_folder:
			self.last_music = playlist
		if return_list:
			return playlist

		self.pctl.multi_playlist.append(self.tauon.pl_gen(title=_("Subsonic Collection"), playlist_ids=playlist))
		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "air"
		self.pctl.switch_playlist(len(self.pctl.multi_playlist) - 1)
		return None
