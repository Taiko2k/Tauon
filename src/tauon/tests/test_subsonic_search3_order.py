# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from tauon.t_modules.t_subsonic import SubsonicService

# OpenSubsonic servers are imported with one empty search3 query, which Navidrome answers grouped by album
# but in no particular order within an album. Navidrome also reports a synthetic "Album Artist/Album/..."
# path, so same named albums share a folder. https://github.com/Taiko2k/Tauon/issues/2375


class FakeTrack:
	def __init__(self) -> None:
		self.index = 0
		self.title = self.artist = self.album = self.album_artist = ""
		self.track_number = self.disc_number = self.date = ""
		self.length = 0
		self.modified_time = 0
		self.genre = ""
		self.genres: list[str] | None = None
		self.file_ext = ""
		self.fullpath = self.parent_folder_path = self.parent_folder_name = ""
		self.url_key: str | None = None
		self.art_url_key: str | None = None
		self.subsonic_folder_id: str | None = None
		self.is_network = False


class FakeStarStore:
	def get_rating(self, _index: int) -> int:
		return 0

	def set_rating(self, _index: int, _value: int) -> None:
		pass


def _song(album_id: str, album: str, disc: int, track: int) -> dict[str, Any]:
	"""One song as Navidrome's search3 serializes it, with its synthetic path"""
	return {
		"id": f"{album_id}-{disc}-{track}", "isDir": False, "title": f"Song {disc}-{track}",
		"album": album, "artist": "Adele", "displayAlbumArtist": "Adele",
		"track": track, "discNumber": disc, "year": 2008, "suffix": "flac",
		"path": f"Adele/{album}/{disc:02}-{track:02} - Song {track}.flac",
		"albumId": album_id, "parent": album_id, "coverArt": f"al-{album_id}",
	}


# Shuffled within each album, and the two "19" albums are different albums with the same folder path
SONGS = [
	_song("a19", "19", 1, 3), _song("a19", "19", 1, 1), _song("a19", "19", 1, 2),
	_song("a21", "21", 2, 1), _song("a21", "21", 1, 2), _song("a21", "21", 1, 1),
	_song("a19d", "19", 1, 2), _song("a19d", "19", 1, 1),
]


def _import(songs: list[dict[str, Any]]) -> tuple[list[int], dict[int, FakeTrack]]:
	def request_json(point: str, p: dict[str, Any] | None = None) -> tuple[int, dict[str, Any] | None]:
		assert point == "search3"
		offset, count = int(p["songOffset"]), int(p["songCount"])
		page = songs[offset:offset + count]
		return 200, {"subsonic-response": {"status": "ok", "searchResult3": {"song": page}}}

	def r(point: str, _p: dict[str, Any] | None = None, **_kwargs: object) -> dict[str, Any]:
		if point == "getIndexes":
			return {"subsonic-response": {"status": "ok", "openSubsonic": True, "indexes": {"index": [
				{"name": "A", "artist": [{"id": "ar1", "name": "Adele"}]}]}}}
		if point == "getStarred2":
			return {"subsonic-response": {"status": "ok", "starred2": {}}}
		raise AssertionError(point)

	tauon = SimpleNamespace(
		gui=SimpleNamespace(to_got=0, request_frame=lambda: None),
		pctl=SimpleNamespace(master_library={}, master_count=1),
		prefs=SimpleNamespace(subsonic_playlists=[], network_stream_bitrate=0),
		t_title="Tauon",
		star_store=FakeStarStore(),
		show_message=lambda *_args, **_kwargs: None,
		TrackClass=FakeTrack,
	)
	album_star_store = SimpleNamespace(get_rating_artist_title=lambda *_args: 0, set_rating_artist_title=lambda *_args: None)
	service = SubsonicService(tauon, album_star_store)
	service.r = r
	service._request_json = request_json  # noqa: SLF001
	return service.get_music3(return_list=True), tauon.pctl.master_library


def test_tracks_are_in_disc_and_track_order_within_albums() -> None:
	playlist, library = _import(SONGS)
	assert [library[i].url_key for i in playlist] == [
		"a19-1-1", "a19-1-2", "a19-1-3",
		"a21-1-1", "a21-1-2", "a21-2-1",
		"a19d-1-1", "a19d-1-2",
	]


def test_albums_sharing_a_folder_path_stay_apart() -> None:
	playlist, library = _import(SONGS)
	folders = {library[i].url_key.split("-")[0]: library[i].parent_folder_path for i in playlist}
	assert folders == {"a19": "Adele/19", "a21": "Adele/21", "a19d": "Adele/19 (2)"}
	# The track itself keeps its real (synthetic) location
	assert next(library[i] for i in playlist if library[i].url_key == "a19d-1-1").fullpath == "Adele/19/01-01 - Song 1.flac"


def test_albums_without_ids_are_grouped_by_folder() -> None:
	songs = [{k: v for k, v in s.items() if k != "albumId"} for s in SONGS[:6]]
	playlist, library = _import(songs)
	assert [library[i].url_key for i in playlist] == [
		"a19-1-1", "a19-1-2", "a19-1-3", "a21-1-1", "a21-1-2", "a21-2-1",
	]
	assert {library[i].parent_folder_path for i in playlist} == {"Adele/19", "Adele/21"}
