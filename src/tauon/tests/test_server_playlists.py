# Copyright © 2026, Taiko2k captain(dot)gxj(at)gmail.com

from __future__ import annotations

import builtins
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from tauon.t_modules.t_jellyfin import Jellyfin
from tauon.t_modules.t_remote_playlists import RemotePlaylist
from tauon.t_modules.t_subsonic import SubsonicService

if TYPE_CHECKING:
	from typing import Any

# Importing server playlists (Navidrome smart playlists among them) from the settings picker.
# https://github.com/Taiko2k/Tauon/issues/1038


@pytest.fixture(autouse=True)
def _translation(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(builtins, "_", lambda text: text, raising=False)


class FakeTrack:
	def __init__(self) -> None:
		self.index = 0
		self.title = self.artist = self.album = self.album_artist = ""
		self.track_number = self.disc_number = self.date = ""
		self.length = 0
		self.modified_time = 0
		self.genre = ""
		self.file_ext = ""
		self.fullpath = self.parent_folder_path = self.parent_folder_name = ""
		self.url_key: str | None = None
		self.art_url_key: str | None = None
		self.is_network = False


class FakePlaylist:
	def __init__(self, title: str, playlist_ids: list[int], uuid_int: int) -> None:
		self.title = title
		self.playlist_ids = playlist_ids
		self.uuid_int = uuid_int


def _tauon(library: dict[int, FakeTrack]) -> SimpleNamespace:
	multi_playlist: list[FakePlaylist] = []
	messages: list[tuple[Any, ...]] = []
	regenerated: list[int] = []

	def pl_gen(title: str, playlist_ids: list[int]) -> FakePlaylist:
		return FakePlaylist(title, playlist_ids, 1000 + len(multi_playlist))

	pctl = SimpleNamespace(
		master_library=library, master_count=100, multi_playlist=multi_playlist, gen_codes={},
		get_track=library.__getitem__, notify_database_changed=lambda: None)
	return SimpleNamespace(
		gui=SimpleNamespace(
			to_got=0, update_layout=False, request_frame=lambda: None, request_tracklist_redraw=lambda: None),
		pctl=pctl,
		prefs=SimpleNamespace(
			jelly_server_url="https://jellyfin.example/", subsonic_user="", network_stream_bitrate=0),
		t_title="Tauon",
		device="Test",
		t_version="test",
		TrackClass=FakeTrack,
		star_store=SimpleNamespace(set_rating=lambda *_args: None, full_get=lambda _index: None),
		album_art_gen=SimpleNamespace(source_cache={}),
		show_message=lambda *args, **_kwargs: messages.append(args),
		messages=messages,
		wake=lambda: None,
		reload=lambda: None,
		pl_gen=pl_gen,
		pl_to_id=lambda index: multi_playlist[index].uuid_int,
		regenerate_playlist=lambda index, **_kwargs: regenerated.append(index),
		regenerated=regenerated,
	)


def _existing(library: dict[int, FakeTrack], track_id: int, key: str, ext: str) -> None:
	nt = FakeTrack()
	nt.index = track_id
	nt.url_key = key
	nt.file_ext = ext
	nt.is_network = True
	library[track_id] = nt


def _subsonic(responses: dict[str, dict[str, Any]], library: dict[int, FakeTrack] | None = None) -> SubsonicService:
	tauon = _tauon({} if library is None else library)
	service = SubsonicService(tauon, SimpleNamespace())

	def r(point: str, p: dict[str, Any] | None = None, **_kwargs: object) -> dict[str, Any]:
		key = point if p is None else f"{point}:{p['id']}"
		return {"subsonic-response": {"status": "ok", **responses[key]}}

	service.r = r
	return service


def _song(song_id: str) -> dict[str, Any]:
	return {"id": song_id, "title": f"Song {song_id}", "album": "Album", "artist": "Artist", "path": f"A/Album/{song_id}.flac"}


def test_subsonic_lists_playlists_and_marks_smart_ones() -> None:
	service = _subsonic({"getPlaylists": {"playlists": {"playlist": [
		{"id": "1", "name": "Lo-Fi", "songCount": 42, "validUntil": "2026-10-19T10:00:00Z", "readonly": True},
		{"id": "2", "name": "Mixtape", "songCount": 3, "readonly": False, "owner": "me"},
		# Smart, but not evaluated yet: Navidrome leaves out validUntil and reports no songs
		{"id": "3", "name": "Rock", "songCount": 0, "readonly": True, "owner": "me"},
		# Someone else's playlist is read-only without being smart
		{"id": "4", "name": "Theirs", "songCount": 5, "readonly": True, "owner": "someone"},
	]}}})
	service.prefs.subsonic_user = "me"
	service.fetch_playlist_list()
	assert service.remote_playlists == [
		RemotePlaylist("1", "Lo-Fi", 42, smart=True),
		RemotePlaylist("2", "Mixtape", 3, smart=False),
		RemotePlaylist("3", "Rock", 0, smart=True),
		RemotePlaylist("4", "Theirs", 5, smart=False),
	]
	assert not service.remote_playlists_loading
	assert not service.remote_playlists_error


def test_subsonic_single_playlist_comes_back_as_a_dict() -> None:
	service = _subsonic({"getPlaylists": {"playlists": {"playlist": {"id": "7", "name": "Only"}}}})
	service.fetch_playlist_list()
	assert service.remote_playlists == [RemotePlaylist("7", "Only")]


def test_subsonic_list_failure_keeps_the_previous_list() -> None:
	service = _subsonic({})
	service.remote_playlists = [RemotePlaylist("1", "Old")]
	service.r = lambda *_args, **_kwargs: {"subsonic-response": {"status": "failed", "error": {"code": 40}}}
	service.fetch_playlist_list()
	assert service.remote_playlists == [RemotePlaylist("1", "Old")]
	assert service.remote_playlists_error


def test_subsonic_playlist_reuses_library_tracks_and_adds_missing_ones_in_order() -> None:
	library: dict[int, FakeTrack] = {}
	_existing(library, 5, "b", "SUB")
	# A Jellyfin track with the same key mustn't be picked up
	_existing(library, 6, "a", "JELY")
	service = _subsonic({"getPlaylist:pl": {"playlist": {"entry": [_song("a"), _song("b"), _song("c"), _song("a")]}}}, library)

	track_ids = service.playlist_track_ids("pl")

	assert [library[i].url_key for i in track_ids] == ["a", "b", "c", "a"]
	assert track_ids[1] == 5
	assert track_ids[0] == track_ids[3] != 6
	added = library[track_ids[0]]
	assert added.file_ext == "SUB"
	assert added.is_network
	assert added.title == "Song a"


def test_import_creates_a_generator_playlist() -> None:
	service = _subsonic({"getPlaylist:pl": {"playlist": {"entry": [_song("a"), _song("b"), _song("a")]}}})
	service.import_playlists([RemotePlaylist("pl", "Lo-Fi")])

	pctl = service.pctl
	assert len(pctl.multi_playlist) == 1
	playlist = pctl.multi_playlist[0]
	assert playlist.title == "Lo-Fi"
	# Duplicates dropped, as regenerating would
	assert [pctl.master_library[i].url_key for i in playlist.playlist_ids] == ["a", "b"]
	assert pctl.gen_codes[playlist.uuid_int] == 'air"pl"'
	assert service.tauon.messages == []
	assert service.imported_playlist("pl") == 0


def test_importing_again_regenerates_instead_of_duplicating() -> None:
	service = _subsonic({"getPlaylist:pl": {"playlist": {"entry": [_song("a")]}}})
	service.import_playlists([RemotePlaylist("pl", "Lo-Fi")])
	# The user added a sort to the generator; it should still be found and kept
	pctl = service.pctl
	pctl.gen_codes[pctl.multi_playlist[0].uuid_int] = 'air"pl" a>'
	service.import_playlists([RemotePlaylist("pl", "Lo-Fi")])

	assert len(pctl.multi_playlist) == 1
	assert service.tauon.regenerated == [0]


def test_similar_ids_are_not_confused() -> None:
	service = _subsonic({})
	pctl = service.pctl
	pctl.multi_playlist.append(FakePlaylist("Other", [], 1))
	pctl.gen_codes[1] = 'air"12"'
	assert service.imported_playlist("1") is None
	assert service.imported_playlist("12") == 0


def test_failed_import_is_reported_and_creates_nothing() -> None:
	service = _subsonic({})
	service.r = lambda *_args, **_kwargs: None
	service.remote_playlists_busy.add("pl")
	service.import_playlists([RemotePlaylist("pl", "Lo-Fi")])

	assert service.pctl.multi_playlist == []
	assert "pl" not in service.remote_playlists_busy
	assert service.tauon.messages


def test_import_all_fetches_the_list_first() -> None:
	service = _subsonic({
		"getPlaylists": {"playlists": {"playlist": [{"id": "1", "name": "One"}, {"id": "2", "name": "Two"}]}},
		"getPlaylist:1": {"playlist": {"entry": [_song("a")]}},
		"getPlaylist:2": {"playlist": {"entry": [_song("b")]}},
	})
	service.import_all_playlists()

	assert [p.title for p in service.pctl.multi_playlist] == ["One", "Two"]
	assert not service.remote_playlists_busy
	# Counts follow what was actually imported
	assert [p.count for p in service.remote_playlists] == [1, 1]
	assert service.tauon.messages[-1] == ("Imported 2 playlists",)

	service.import_all_playlists()
	assert len(service.pctl.multi_playlist) == 2
	assert service.tauon.messages[-1] == ("Updated 2 playlists",)


def _item(item_id: str) -> dict[str, Any]:
	return {
		"Id": item_id,
		"Type": "Audio",
		"Name": f"Song {item_id}",
		"DateCreated": "2026-01-01T00:00:00.000Z",
		"MediaSources": [{"Path": f"/music/Album/{item_id}.flac", "Size": 100, "MediaStreams": []}],
	}


def _jellyfin(monkeypatch: pytest.MonkeyPatch, library: dict[int, FakeTrack], responses: dict[str, list[dict]]) -> Jellyfin:
	service = Jellyfin(_tauon(library))
	service.connected = True
	service.accessToken = "token"
	service.userId = "user"

	def get(url: str, **_kwargs: object) -> SimpleNamespace:
		items = responses[url.removeprefix("https://jellyfin.example/")]
		return SimpleNamespace(status_code=200, json=lambda: {"Items": items})

	monkeypatch.setattr("tauon.t_modules.t_jellyfin.requests.get", get)
	return service


def test_jellyfin_lists_audio_playlists(monkeypatch: pytest.MonkeyPatch) -> None:
	service = _jellyfin(monkeypatch, {}, {"Items": [
		{"Id": "p1", "Name": "Road trip", "ChildCount": 12, "MediaType": "Audio"},
		{"Id": "p2", "Name": "Films", "MediaType": "Video"},
	]})
	service.fetch_playlist_list()
	assert service.remote_playlists == [RemotePlaylist("p1", "Road trip", 12)]


def test_jellyfin_playlist_no_longer_needs_the_library_imported(monkeypatch: pytest.MonkeyPatch) -> None:
	library: dict[int, FakeTrack] = {}
	_existing(library, 5, "b", "JELY")
	service = _jellyfin(monkeypatch, library, {"Playlists/p1/Items": [_item("a"), _item("b"), {"Id": "v", "Type": "Video"}]})

	track_ids = service.playlist_track_ids("p1")

	assert [library[i].url_key for i in track_ids] == ["a", "b"]
	assert track_ids[1] == 5
	added = library[track_ids[0]]
	assert added.file_ext == "JELY"
	assert added.title == "Song a"


def test_import_waits_for_a_running_library_import() -> None:
	service = _subsonic({})
	service.scanning = True
	service.start_import_playlists([RemotePlaylist("pl", "Lo-Fi")])
	service.start_import_all_playlists()
	assert not service.remote_playlists_busy
	assert not service.remote_playlists_loading
	assert len(service.tauon.messages) == 2
