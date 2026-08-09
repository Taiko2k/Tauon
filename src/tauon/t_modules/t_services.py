"""External service adapters and library statistics."""

from __future__ import annotations

import copy
import logging
import math
import os
from pathlib import Path
from typing import Any, Protocol

import requests

from tauon.t_modules.t_models import TrackClass
from tauon.t_modules.t_prefs import Prefs
from tauon.t_modules.t_subsonic import SubsonicService
from tauon.t_modules.t_state import GuiVar


class _ServicePlayer(Protocol):
	def __getattr__(self, name: str) -> Any: ...


class _ServiceApp(Protocol):
	gui: GuiVar
	pctl: _ServicePlayer
	prefs: Prefs

	def __getattr__(self, name: str) -> Any: ...
class AlbumStarStore:

	def __init__(self, tauon: _ServiceApp) -> None:
		self.db: dict[str, int] = {}
		self.subsonic: SubsonicService = SubsonicService(tauon=tauon, album_star_store=self)

	def get_key(self, track_object: TrackClass) -> str:
		artist = track_object.album_artist
		if not artist:
			artist = track_object.artist
		return artist + ":" + track_object.album

	def get_rating(self, track_object: TrackClass) -> int:
		return self.db.get(self.get_key(track_object), 0)

	def set_rating(self, track_object: TrackClass, rating: int) -> None:
		self.db[self.get_key(track_object)] = rating
		if track_object.file_ext == "SUB":
			self.db[self.get_key(track_object)] = math.ceil(rating / 2) * 2
			self.subsonic.set_album_rating(track_object, rating)

	def set_rating_artist_title(self, artist: str, album: str, rating: int) -> None:
		self.db[artist + ":" + album] = rating

	def get_rating_artist_title(self, artist: str, album: str) -> int:
		return self.db.get(artist + ":" + album, 0)
class PlexService:

	def __init__(self, tauon: _ServiceApp) -> None:
		self.tauon:    _ServiceApp = tauon
		self.gui:     GuiVar = tauon.gui
		self.pctl: _ServicePlayer = tauon.pctl
		self.prefs:    Prefs = tauon.prefs
		self.show_message    = tauon.show_message
		self.connected: bool = False
		self.resource        = None
		self.scanning:  bool = False
		self.two_factor_required: bool = False

	def connect(self, code: str | None = None) -> bool:
		if not self.prefs.plex_username or not self.prefs.plex_password or not self.prefs.plex_servername:
			self.show_message(_("Missing username, password and/or server name"), mode="warning")
			self.scanning = False
			return False

		try:
			from plexapi.exceptions import TwoFactorRequired
			from plexapi.myplex import MyPlexAccount
		except ModuleNotFoundError:
			logging.warning("Unable to import python-plexapi, plex support will be disabled.")
			self.scanning = False
			return False
		except Exception:
			logging.exception("Unknown error to import python-plexapi, plex support will be disabled.")
			self.show_message(_("Error importing python-plexapi"), mode="error")
			self.scanning = False
			return False

		try:
			account = MyPlexAccount(self.prefs.plex_username, self.prefs.plex_password, code=code)
			self.resource = account.resource(self.prefs.plex_servername).connect()  # returns a PlexServer instance
			self.connected = True
			self.two_factor_required = False
			return True
		except TwoFactorRequired:
			logging.info("PLEX two-factor authentication required")
			self.connected = False
			self.resource = None
			self.two_factor_required = True
			self.show_message(
				_("Two-factor authentication required"),
				_("Enter the verification code and try again."),
				mode="warning",
			)
			self.gui.request_frame()
			self.scanning = False
			return False
		except Exception:
			logging.exception("Error connecting to PLEX server, check login credentials and server accessibility.")
			self.show_message(
				_("Error connecting to PLEX server"),
				_("Try checking login credentials and that the server is accessible."), mode="error")
			self.scanning = False
			return False

	def resolve_stream(self, location: str):
		logging.info("Get plex stream")
		if not self.connected:
			self.connect()

		# return self.resource.url(location, True)
		return self.resource.library.fetchItem(location).getStreamURL()

	def resolve_thumbnail(self, location: str):
		if not self.connected:
			self.connect()
		if self.connected:
			return self.resource.url(location, True)
		return None

	def get_albums(self, return_list: bool = False) -> list[int] | None:
		self.gui.request_frame()
		self.scanning = True

		if not self.connected:
			self.connect()

		if not self.connected:
			self.scanning = False
			return []

		playlist: list[int] = []

		existing = {}
		for track_id, track in self.pctl.master_library.items():
			if track.is_network and track.file_ext == "PLEX":
				existing[track.url_key] = track_id

		albums = self.resource.library.section(self.prefs.plex_library).albums()
		self.gui.to_got = 0

		for album in albums:
			year = album.year
			album_artist = album.parentTitle
			album_title = album.title

			parent = (album_artist + " - " + album_title).strip("- ")

			for track in album.tracks():
				if not track.duration:
					logging.warning(f"Skipping track with invalid duration - {track.title} - {track.grandparentTitle}")
					continue

				id = self.pctl.master_count
				replace_existing = False

				e = existing.get(track.key)
				if e is not None:
					id = e
					replace_existing = True

				title = track.title
				track_artist = track.grandparentTitle
				duration = track.duration / 1000

				nt = TrackClass()
				nt.index = id
				nt.track_number = track.index
				nt.file_ext = "PLEX"
				nt.parent_folder_path = parent
				nt.parent_folder_name = parent
				nt.album_artist = album_artist
				nt.artist = track_artist
				nt.title = title
				nt.album = album_title
				nt.length = duration
				if hasattr(track, "locations") and track.locations:
					nt.fullpath = track.locations[0]

				nt.is_network = True

				if track.thumb:
					nt.art_url_key = track.thumb

				nt.url_key = track.key
				nt.date = str(year)

				self.pctl.master_library[id] = nt

				if not replace_existing:
					self.pctl.master_count += 1

				playlist.append(nt.index)

			self.gui.to_got += 1
			self.gui.request_frame()
			self.gui.request_tracklist_redraw()

		self.scanning = False

		if return_list:
			return playlist

		self.pctl.multi_playlist.append(self.tauon.pl_gen(title=_("PLEX Collection"), playlist_ids=playlist))
		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "plex path"
		self.pctl.switch_playlist(len(self.pctl.multi_playlist) - 1)
		return None
class TauService:
	def __init__(self, tauon: _ServiceApp) -> None:
		self.tauon:            _ServiceApp = tauon
		self.pctl:         _ServicePlayer = tauon.pctl
		self.prefs:            Prefs = tauon.prefs
		self.show_message            = tauon.show_message
		self.install_directory: Path = tauon.install_directory
		self.processing: bool        = False

	def resolve_stream(self, key: str) -> str:
		return "http://" + self.prefs.sat_url + ":7814/api1/file/" + key

	def resolve_picture(self, key: str) -> str:
		return "http://" + self.prefs.sat_url + ":7814/api1/pic/medium/" + key

	def get(self, point: str):
		url = "http://" + self.prefs.sat_url + ":7814/api1/"
		data = None
		try:
			r = requests.get(url + point, timeout=10)
			data = r.json()
		except Exception as e:
			logging.exception("Network error")
			self.show_message(_("Network error"), str(e), mode="error")
		return data

	def get_playlist(self, playlist_name: str | None = None, return_list: bool = False) -> list[int] | None:
		p = self.get("playlists")

		if not p or not p["playlists"]:
			self.processing = False
			return []

		if playlist_name is None:
			playlist_name = self.tauon.text_sat_playlist.text.strip()
		if not playlist_name:
			self.show_message(_("No playlist name"))
			return []

		id = None
		name = ""
		for pp in p["playlists"]:
			if pp["name"].lower() == playlist_name.lower():
				id = pp["id"]
				name = pp["name"]

		if id is None:
			self.show_message(_("Playlist not found on target"), mode="error")
			self.processing = False
			return []

		try:
			t = self.get("tracklist/" + id)
		except Exception:
			logging.exception("error getting tracklist")
			return []
		at = t["tracks"]

		exist = {}
		for k, v in self.pctl.master_library.items():
			if v.is_network and v.file_ext == "TAU":
				exist[v.url_key] = k

		playlist = []
		for item in at:
			replace_existing = True

			tid = item["id"]
			id = exist.get(str(tid))
			if id is None:
				id = self.pctl.master_count
				replace_existing = False

			nt = TrackClass()
			nt.index = id
			nt.title = item.get("title", "")
			nt.artist = item.get("artist", "")
			nt.album = item.get("album", "")
			nt.album_artist = item.get("album_artist", "")
			nt.length = int(item.get("duration", 0) / 1000)
			nt.track_number = item.get("track_number", 0)

			nt.fullpath = item.get("path", "")
			nt.filename = os.path.basename(nt.fullpath)
			nt.parent_folder_name = os.path.basename(os.path.dirname(nt.fullpath))
			nt.parent_folder_path = os.path.dirname(nt.fullpath)

			nt.url_key = str(tid)
			nt.art_url_key = str(tid)

			nt.is_network = True
			nt.file_ext = "TAU"
			self.pctl.master_library[id] = nt

			if not replace_existing:
				self.pctl.master_count += 1
			playlist.append(nt.index)

		if return_list:
			self.processing = False
			return playlist

		self.pctl.multi_playlist.append(self.tauon.pl_gen(title=name, playlist_ids=playlist))
		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "tau path tn"
		self.tauon.standard_sort(len(self.pctl.multi_playlist) - 1)
		self.pctl.switch_playlist(len(self.pctl.multi_playlist) - 1)
		self.processing = False
		return None
class GStats:
	def __init__(self, tauon: _ServiceApp) -> None:
		self.pctl       = tauon.pctl
		self.star_store = tauon.star_store
		self.last_db: int = 0
		self.last_pl: int = 0
		self.artist_list: list[tuple[str, int]] = []
		self.album_list:  list[tuple[str, int]] = []
		self.genre_list:  list[tuple[str, int]] = []
		self.genre_dict:   dict[str, list[int]] = {}

	def update(self, playlist: int) -> None:
		pt = 0

		if self.pctl.master_count != self.last_db or self.last_pl != playlist:
			self.last_db = self.pctl.master_count
			self.last_pl = playlist

			artists: dict[str, int] = {}

			for index in self.pctl.multi_playlist[playlist].playlist_ids:
				artist = self.pctl.master_library[index].artist

				if artist == "":
					artist = "<Artist Unspecified>"

				pt = int(self.star_store.get(index))
				if pt < 30:
					continue

				if artist in artists:
					artists[artist] += pt
				else:
					artists[artist] = pt

			art_list = artists.items()

			sorted_list = sorted(art_list, key=lambda x: x[1], reverse=True)

			self.artist_list = copy.deepcopy(sorted_list)

			genres: dict[str, int] = {}
			genre_dict: dict[str, list[int]] = {}

			for index in self.pctl.multi_playlist[playlist].playlist_ids:
				genre_r = self.pctl.master_library[index].genre

				pt = int(self.star_store.get(index))

				gn = []
				if "," in genre_r:
					for g in genre_r.split(","):
						g = g.rstrip(" ").lstrip(" ")
						if len(g) > 0:
							gn.append(g)
				elif ";" in genre_r:
					for g in genre_r.split(";"):
						g = g.rstrip(" ").lstrip(" ")
						if len(g) > 0:
							gn.append(g)
				elif "/" in genre_r:
					for g in genre_r.split("/"):
						g = g.rstrip(" ").lstrip(" ")
						if len(g) > 0:
							gn.append(g)
				elif " & " in genre_r:
					for g in genre_r.split(" & "):
						g = g.rstrip(" ").lstrip(" ")
						if len(g) > 0:
							gn.append(g)
				else:
					gn = [genre_r]

				pt = int(pt / len(gn))

				for genre in gn:
					if genre.lower() in {"", "other", "unknown", "misc"}:
						genre = "<Genre Unspecified>"
					if genre.lower() in {"jpop", "japanese pop"}:
						genre = "J-Pop"
					if genre.lower() in {"jrock", "japanese rock"}:
						genre = "J-Rock"
					if genre.lower() in {"alternative music", "alt-rock", "alternative", "alternrock", "alt"}:
						genre = "Alternative Rock"
					if genre.lower() in {"jpunk", "japanese punk"}:
						genre = "J-Punk"
					if genre.lower() in {"post rock", "post-rock"}:
						genre = "Post-Rock"
					if genre.lower() in {"video game", "game", "game music", "video game music", "game ost"}:
						genre = "Video Game Soundtrack"
					if genre.lower() in {"general soundtrack", "ost", "Soundtracks"}:
						genre = "Soundtrack"
					if genre.lower() in ("anime", "アニメ", "anime ost"):
						genre = "Anime Soundtrack"
					if genre.lower() in {"同人"}:
						genre = "Doujin"
					if genre.lower() in {"chill, chill out", "chill-out"}:
						genre = "Chillout"

					genre = genre.title()

					if len(genre) == 3 and genre[2] == "m":
						genre = genre.upper()

					if genre in genres:

						genres[genre] += pt
					else:
						genres[genre] = pt

					if genre in genre_dict:
						genre_dict[genre].append(index)
					else:
						genre_dict[genre] = [index]

			art_list = genres.items()
			sorted_list = sorted(art_list, key=lambda x: x[1], reverse=True)

			self.genre_list = copy.deepcopy(sorted_list)
			self.genre_dict = genre_dict

			# logging.info('\n-----------------------\n')

			g_albums: dict[str, int] = {}

			for index in self.pctl.multi_playlist[playlist].playlist_ids:
				album = self.pctl.master_library[index].album

				if album == "":
					album = "<Album Unspecified>"

				pt = int(self.star_store.get(index))

				if pt < 30:
					continue

				if album in g_albums:
					g_albums[album] += pt
				else:
					g_albums[album] = pt

			art_list = g_albums.items()

			sorted_list = sorted(art_list, key=lambda x: x[1], reverse=True)

			self.album_list = copy.deepcopy(sorted_list)
