# Copyright © 2026, Tauon contributors

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tauon.t_modules import t_generator as gen
from tauon.t_modules.t_main import PlayerCtl, Tauon

LIBRARY = [5, 1, 4, 2, 6, 3]


def make_tauon(code: str = "", *, ignore_the: bool = True) -> Tauon:
	tauon = Tauon.__new__(Tauon)
	tauon.prefs = SimpleNamespace(sort_ignore_the=ignore_the)
	tauon.pctl = PlayerCtl.__new__(PlayerCtl)
	tauon.pctl.multi_playlist = [
		SimpleNamespace(uuid_int=100, title="My Library", playlist_ids=LIBRARY[:], pre_sort_ids=[], locked=False),
		SimpleNamespace(uuid_int=200, title="Sorted", playlist_ids=[], pre_sort_ids=[], locked=False),
	]
	tauon.pctl.gen_codes = {200: code}
	tauon.pctl.master_library = {}
	for track_id, artist, album_artist in (
		(1, "The Beatles", ""),
		(2, "abba", ""),
		(3, "Guest", "Various Artists"),
		(4, "Cream", ""),
		(5, "Theatre of Tragedy", ""),
		(6, "The Beatles", ""),
	):
		tauon.pctl.master_library[track_id] = SimpleNamespace(index=track_id, artist=artist, album_artist=album_artist)
	tauon.gui = SimpleNamespace(request_tracklist_redraw=Mock())
	tauon.generator_box = SimpleNamespace(active=False)
	tauon.tree_view_box = SimpleNamespace(clear_target_pl=Mock())
	tauon.undo = SimpleNamespace(bk_order=Mock())
	tauon.pctl.notify_database_changed = Mock()
	tauon.reload = Mock()
	tauon.reload_albums = Mock()
	tauon.show_message = Mock()
	return tauon


def regenerate(code: str, *, ignore_the: bool = True) -> list[int]:
	tauon = make_tauon(f's"My Library" a {code}', ignore_the=ignore_the)
	tauon.regenerate_playlist(1)
	assert tauon.gui.gen_code_errors is False
	return tauon.pctl.multi_playlist[1].playlist_ids


@pytest.mark.parametrize(("code", "ignore_the", "expected"), [
	# Beatles under B; 1 and 6 keep their source order
	("ar>", True, [2, 1, 6, 4, 3, 5]),
	("ar<", True, [5, 3, 4, 1, 6, 2]),
	# "Theatre" is not "The ", so it stays under T either way
	("ar>", False, [2, 4, 3, 1, 6, 5]),
	# Track 3 sorts by its album artist; the rest fall back to artist
	("aa>", True, [2, 1, 6, 4, 5, 3]),
	("aa<", True, [3, 5, 4, 1, 6, 2]),
	("aa>", False, [2, 4, 1, 6, 5, 3]),
])
def test_artist_sort_codes(code: str, ignore_the: bool, expected: list[int]) -> None:
	assert regenerate(code, ignore_the=ignore_the) == expected


def test_artist_sort_name() -> None:
	tauon = make_tauon()
	assert tauon.artist_sort_name("The Beatles") == "beatles"
	assert tauon.artist_sort_name("the the") == "the"
	assert tauon.artist_sort_name("The") == "the"
	assert tauon.artist_sort_name("Theatre") == "theatre"
	tauon.prefs.sort_ignore_the = False
	assert tauon.artist_sort_name("The Beatles") == "the beatles"


def test_menu_sort_is_one_off() -> None:
	tauon = make_tauon()
	tauon.sort_by_album_artist_menu(0)
	playlist = tauon.pctl.multi_playlist[0]
	assert playlist.playlist_ids == [2, 1, 6, 4, 5, 3]
	assert playlist.pre_sort_ids == LIBRARY
	assert 100 not in tauon.pctl.gen_codes
	tauon.undo.bk_order.assert_called_once_with(0)


def test_menu_sort_respects_lock() -> None:
	tauon = make_tauon()
	tauon.pctl.multi_playlist[0].locked = True
	tauon.sort_by_artist_menu(0)
	assert tauon.pctl.multi_playlist[0].playlist_ids == LIBRARY
	tauon.show_message.assert_called_once()


def test_toggle_refreshes_artist_list() -> None:
	tauon = make_tauon()
	tauon.artist_list_box = SimpleNamespace(saves={100: object()})
	assert tauon.toggle_sort_ignore_the(1) is True
	tauon.toggle_sort_ignore_the()
	assert tauon.prefs.sort_ignore_the is False
	assert tauon.artist_list_box.saves == {}


@pytest.mark.parametrize(("token", "kind_id", "value"), [
	("ar>", "sort_artist", "Artist, A-Z"),
	("ar<", "sort_artist", "Artist, Z-A"),
	("aa>", "sort_album_artist", "Album artist, A-Z"),
])
def test_editor_knows_artist_sorts(token: str, kind_id: str, value: str) -> None:
	step = gen.parse_step(token)
	assert step.kind is not None
	assert step.kind.id == kind_id
	assert step.category == gen.SORT
	assert step.value == value
	assert step.rebuilt(dir="<" if token.endswith(">") else ">") == token[:2] + ("<" if token.endswith(">") else ">")
