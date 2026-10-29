# Copyright © 2026, Tauon contributors
"""The Add Music box imports into its playlist, naming an untouched Default after the folder."""

import os

os.environ["SDL_DISABLE_METADATA"] = "1"
os.environ["SDL_DOC_GENERATOR"] = "0"

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tauon.t_modules.t_main import AddMusicBox, PlayerCtl, Tauon


def playlist(uuid: int, title: str = "Default", ids: list[int] | None = None, locked: bool = False) -> SimpleNamespace:
	return SimpleNamespace(uuid_int=uuid, title=title, playlist_ids=ids or [], locked=locked, last_folder=[])


def make_tauon(playlists: list[SimpleNamespace], music: Path | None) -> Tauon:
	tauon = Tauon.__new__(Tauon)
	tauon.gui = SimpleNamespace(request_frame=Mock())
	tauon.pctl = PlayerCtl.__new__(PlayerCtl)
	tauon.pctl.multi_playlist = playlists
	tauon.pctl.active_playlist_viewing = 0
	tauon.pctl.gen_codes = {}
	tauon.music_directory = music
	tauon.load_orders = []
	tauon.quick_import_done = []
	tauon.show_message = Mock()
	tauon.toast = Mock()
	return tauon


@pytest.fixture
def music(tmp_path: Path) -> Path:
	path = tmp_path / "Music"
	path.mkdir()
	return path


def make_box(tauon: Tauon, playlist_id: int = 1) -> AddMusicBox:
	box = AddMusicBox.__new__(AddMusicBox)
	box.tauon = tauon
	box.playlist_id = playlist_id
	return box


def test_import_music_fills_untitled_default(music: Path) -> None:
	tauon = make_tauon([playlist(1)], music)
	make_box(tauon)._import_music()
	assert [pl.title for pl in tauon.pctl.multi_playlist] == ["Music"]
	(order,) = tauon.load_orders
	assert (order.target, order.playlist, order.toast) == (str(music), 1, True)


@pytest.mark.parametrize("current", [
	playlist(1, ids=[5]),
	playlist(1, title="Road Trip"),
])
def test_import_music_keeps_playlist_name(music: Path, current: SimpleNamespace) -> None:
	title = current.title
	tauon = make_tauon([current], music)
	make_box(tauon)._import_music()
	assert [pl.title for pl in tauon.pctl.multi_playlist] == [title]
	assert tauon.load_orders[0].playlist == 1


def test_import_music_keeps_smart_default_name(music: Path) -> None:
	tauon = make_tauon([playlist(1)], music)
	tauon.pctl.gen_codes[1] = "a"
	make_box(tauon)._import_music()
	assert tauon.pctl.multi_playlist[0].title == "Default"


def test_folder_import_names_untitled_playlist_once(tmp_path: Path) -> None:
	jazz = tmp_path / "Jazz Albums"
	more = tmp_path / "More"
	jazz.mkdir()
	more.mkdir()
	tauon = make_tauon([playlist(1)], None)
	assert tauon.import_folder_to_playlist(str(jazz), 0, toast=True)
	assert tauon.import_folder_to_playlist(str(more), 0, toast=True)
	assert tauon.pctl.multi_playlist[0].title == "Jazz Albums"
	assert [order.target for order in tauon.load_orders] == [str(jazz), str(more)]


def test_locked_or_missing_folder_is_refused(tmp_path: Path) -> None:
	tauon = make_tauon([playlist(1, locked=True)], None)
	assert not tauon.import_folder_to_playlist(str(tmp_path), 0)
	tauon.pctl.multi_playlist[0].locked = False
	assert not tauon.import_folder_to_playlist(str(tmp_path / "gone"), 0)
	assert tauon.load_orders == []


@pytest.mark.parametrize(("count", "text"), [(0, "No music found"), (1, "Imported 1 track"), (42, "Imported 42 tracks")])
def test_toast_imported(count: int, text: str) -> None:
	tauon = make_tauon([playlist(1)], None)
	tauon.toast_imported(count)
	assert tauon.toast.call_args.args[0] == text


def test_box_offers_smart_playlist_only_with_other_tracks(music: Path) -> None:
	tauon = make_tauon([playlist(1), playlist(2, title="Empty")], music)
	box = make_box(tauon)
	assert [label for label, _painter, _action in box.options()] == ["Add music folder…", f"Import {music}"]
	tauon.pctl.multi_playlist[1].playlist_ids = [7]
	assert [label for label, _painter, _action in box.options()][-1] == "Smart Playlist"
	tauon.music_directory = None
	assert len(box.options()) == 2
