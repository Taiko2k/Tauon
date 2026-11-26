# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

# gi (PyGObject) is a Linux-only dependency, stub it like conftest stubs tauon_native
if "gi" not in sys.modules:
	sys.modules["gi"] = MagicMock(name="gi")
	sys.modules["gi.repository"] = MagicMock(name="gi.repository")

from tauon.t_modules.t_jellyfin import Jellyfin
from tauon.t_modules.t_main import Tauon, TrackClass

# Two Jellyfin albums that share artist, name and year are still different
# albums. The item's AlbumId tells them apart where the name, date and folder
# heuristics cannot. https://github.com/Taiko2k/Tauon/issues/1678


def _track(track_id: int, album_id: str, folder: str, album: str, number: str) -> TrackClass:
	nt = TrackClass()
	nt.index = track_id
	nt.is_network = True
	nt.file_ext = "JELY"
	nt.url_key = f"{album_id}-t{number}"
	nt.jellyfin_album_id = album_id
	nt.parent_folder_path = folder
	nt.parent_folder_name = folder.rsplit("/", 1)[-1]
	nt.album = album
	nt.album_artist = "Adele"
	nt.date = "2008"
	nt.disc_number = "1"
	nt.track_number = number
	return nt


def _sortable(library: dict[int, TrackClass]) -> SimpleNamespace:
	sortable = SimpleNamespace(
		gui=SimpleNamespace(request_tracklist_redraw=lambda: None),
		pctl=SimpleNamespace(
			master_library=library,
			multi_playlist=[],
			index_key=lambda i: (int(library[i].disc_number or 1), int(library[i].track_number or 0)),
		),
	)
	sortable.sort_album_tracks = lambda playlist, pause=False: Tauon.sort_album_tracks(sortable, playlist, pause)
	return sortable


def test_same_named_albums_in_sibling_folders_stay_apart() -> None:
	library = dict(enumerate([
		_track(0, "al1", "Adele/19", "19", "1"),
		_track(1, "al1", "Adele/19", "19", "2"),
		_track(2, "al2", "Adele/19 (Deluxe)", "19", "1"),
		_track(3, "al2", "Adele/19 (Deluxe)", "19", "2"),
	]))
	playlist = [0, 1, 2, 3]
	Tauon.sort_track_2(_sortable(library), 0, playlist)
	assert [library[i].url_key for i in playlist] == ["al1-t1", "al1-t2", "al2-t1", "al2-t2"]


def test_same_named_albums_sharing_a_folder_stay_apart() -> None:
	service = Jellyfin.__new__(Jellyfin)
	library = dict(enumerate([
		_track(0, "al1", "Adele/19", "19", "1"),
		_track(1, "al1", "Adele/19", "19", "2"),
		_track(2, "al2", "Adele/19", "19", "1"),
		_track(3, "al2", "Adele/19", "19", "2"),
	]))
	Jellyfin._separate_albums(service, [(t, t.jellyfin_album_id) for t in library.values()])  # noqa: SLF001

	playlist = [0, 1, 2, 3]
	Tauon.sort_track_2(_sortable(library), 0, playlist)
	assert [library[i].url_key for i in playlist] == ["al1-t1", "al1-t2", "al2-t1", "al2-t2"]
	assert {library[i].parent_folder_path for i in playlist} == {"Adele/19", "Adele/19 (2)"}


def test_tracks_without_album_ids_keep_folder_grouping() -> None:
	library = dict(enumerate([
		_track(0, None, "Adele/19", "19", "1"),
		_track(1, None, "Adele/19 (Deluxe)", "19", "2"),
	]))
	for t in library.values():
		t.jellyfin_album_id = None
	playlist = [0, 1]
	Tauon.sort_track_2(_sortable(library), 0, playlist)
	assert playlist == [0, 1]
	assert library[0].parent_folder_path == "Adele/19"
