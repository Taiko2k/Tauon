# Copyright © 2026, Tauon contributors
"""The Add Music box imports into its playlist, naming an untouched Default after the folder,
and pulls remote server sources in through generator codes."""

import os

os.environ["SDL_DISABLE_METADATA"] = "1"
os.environ["SDL_DOC_GENERATOR"] = "0"

from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from unittest.mock import Mock

import pytest

from tauon.t_modules.t_main import AddMusicBox, PlayerCtl, RemoteServer, Tauon
from tauon.t_modules.t_remote_playlists import RemotePlaylist


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
	box.gui = tauon.gui
	box.playlist_id = playlist_id
	box.active = True
	box.click = False
	box._generation = 0
	box.libraries = {}
	return box


def remote_tauon(playlists: list[SimpleNamespace]) -> Tauon:
	tauon = make_tauon(playlists, None)
	tauon.wake = Mock()
	tauon.pctl.switch_playlist = Mock()
	tauon.gen_unique_pl_title = lambda title: title
	tauon.pl_gen = lambda title: playlist(99, title=title)
	return tauon


def server(**kwargs) -> RemoteServer:
	return RemoteServer("jellyfin", "Jellyfin", 10, lambda: True, lambda: True, **kwargs)


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


def test_box_options(music: Path) -> None:
	tauon = make_tauon([playlist(1), playlist(2, title="Other", ids=[7])], music)
	box = make_box(tauon)
	assert [label for label, _painter, _action in box.options()] == ["Pick folder…", f"Import {music}", "Remote server"]
	tauon.music_directory = None
	assert [label for label, _painter, _action in box.options()] == ["Pick folder…", "Remote server"]


def test_remote_source_fills_empty_default() -> None:
	tauon = remote_tauon([playlist(1)])
	make_box(tauon)._add('jellylib"abc"', "Jellyfin · Music")
	assert [pl.title for pl in tauon.pctl.multi_playlist] == ["Jellyfin · Music"]
	assert tauon.pctl.gen_codes == {1: 'jellylib"abc"'}
	assert tauon.gui.regen_single_id == 1


@pytest.mark.parametrize("current", [
	playlist(1, ids=[5]),
	playlist(1, locked=True),
])
def test_remote_source_gets_a_new_playlist(current: SimpleNamespace) -> None:
	tauon = remote_tauon([current])
	make_box(tauon)._add("airfav", "Subsonic · Favourite tracks")
	assert [pl.title for pl in tauon.pctl.multi_playlist] == [current.title, "Subsonic · Favourite tracks"]
	assert tauon.pctl.gen_codes == {99: "airfav"}
	tauon.pctl.switch_playlist.assert_called_once_with(1)


def test_remote_source_with_a_generator_keeps_it() -> None:
	tauon = remote_tauon([playlist(1)])
	tauon.pctl.gen_codes[1] = "a"
	make_box(tauon)._add("plex", "PLEX")
	assert tauon.pctl.gen_codes == {1: "a", 99: "plex"}


def test_remote_source_already_added_is_refreshed() -> None:
	tauon = remote_tauon([playlist(1, ids=[3]), playlist(2, title="Mine", ids=[4])])
	tauon.pctl.gen_codes[2] = 'tpl"x"'
	make_box(tauon)._add('tpl"x"', "Mine")
	assert len(tauon.pctl.multi_playlist) == 2
	tauon.pctl.switch_playlist.assert_called_once_with(1)
	assert tauon.gui.regen_single_id == 2


def test_server_options_keep_library_with_one_or_none() -> None:
	box = make_box(remote_tauon([playlist(1)]))
	jelly = server(
		everything="jelly", libraries=lambda: [], library_code="jellylib",
		playlists=lambda: [], playlist_code="jelly", favourites=[("Favourite tracks", "jellyfav")])
	labels = lambda: [label for label, _painter, _action in box.server_options(jelly)]  # noqa: E731
	expected = ["Everything", "Pick library…", "Pick playlist…", "Favourite tracks"]
	# Not fetched yet, none, or just one: the picker says which
	assert labels() == expected
	box.libraries["jellyfin"] = []
	assert labels() == expected
	box.libraries["jellyfin"] = [RemotePlaylist("a", "Music")]
	assert labels() == expected
	# Without library support there's no tile
	assert "Pick library…" not in [label for label, _p, _a in box.server_options(server(everything="plex"))]


def test_server_with_only_playlists_opens_the_picker() -> None:
	box = make_box(remote_tauon([playlist(1)]))
	box._open_picker = Mock()
	box._open_server(server(playlists=lambda: [], playlist_code="tau"))
	box._open_picker.assert_called_once_with("playlist", direct=True)


@pytest.mark.parametrize(("code", "okay"), [
	('airlib"3"', False),
	("airfavalb", False),
	("jellyfav", False),
	('jellylib"x"', False),
	('plexlib"1"', False),
	('plexpl"9"', False),
	('tau"12"', False),
	("tfa", False),
	('a"Tauon"', True),
])
def test_remote_codes_skip_auto_update(code: str, okay: bool) -> None:
	tauon = make_tauon([playlist(1)], None)
	tauon.prefs = SimpleNamespace(always_auto_update_playlists=True)
	tauon.pctl.active_playlist_playing = 5
	assert tauon.check_auto_update_okay(code, pl=0) is okay


def test_settings_button_opens_on_the_server() -> None:
	tauon = remote_tauon([playlist(1)])
	tauon.pref_box = SimpleNamespace(close=Mock())
	tauon.bag = None
	box = make_box(tauon)
	box.status = {}
	box._servers = [server(everything="jelly", playlists=lambda: [], playlist_code="jelly")]
	box._check = Mock()
	with mock.patch("tauon.t_modules.t_main.save_prefs"), mock.patch("threading.Thread"):
		box.open_server("jellyfin")
	tauon.pref_box.close.assert_called_once()
	assert (box.active, box.page, box.server.key) == (True, "server", "jellyfin")
	# Back goes to the server list, checking each again
	with mock.patch("threading.Thread"):
		box.back()
	assert box.page == "servers"
	assert box.status["jellyfin"] == "checking"


def test_settings_button_needs_server_details() -> None:
	tauon = remote_tauon([playlist(1)])
	tauon.pref_box = SimpleNamespace(close=Mock())
	box = make_box(tauon)
	box.active = False
	box._servers = [RemoteServer("plex", "PLEX", 5, lambda: False, lambda: True, everything="plex")]
	box.open_server("plex")
	tauon.pref_box.close.assert_not_called()
	assert not box.active


@pytest.mark.parametrize(("state", "opens"), [("checking", True), ("ok", True), ("fail", False), ("setup", False)])
def test_server_click_opens_while_checking(state: str, opens: bool) -> None:
	box = make_box(remote_tauon([playlist(1)]))
	box.status = {"jellyfin": state}
	box._open_server = Mock()
	box._open_settings = Mock()
	box._pick_server(server(everything="jelly"))
	assert box._open_server.called is opens
	assert box._open_settings.called is not opens
