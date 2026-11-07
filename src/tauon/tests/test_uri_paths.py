# Copyright © 2026, Tauon contributors
"""A % in a plain path is literal. Only URIs and encoded XSPF locations get decoded (#491)."""

import os

os.environ["SDL_DISABLE_METADATA"] = "1"
os.environ["SDL_DOC_GENERATOR"] = "0"

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tauon.t_modules.t_extra import uri_parse
from tauon.t_modules.t_main import Tauon

GVFS_FOLDER = "nfs:host=srv,prefix=%2Fmnt%2Fuser"


@pytest.mark.parametrize(("value", "expected"), [
	(f"/run/gvfs/{GVFS_FOLDER}/a.flac", f"/run/gvfs/{GVFS_FOLDER}/a.flac"),
	("/music/100%25 live.flac", "/music/100%25 live.flac"),
	("/music/a.flac\r", "/music/a.flac"),
	("file:///music/a%20b.flac", "/music/a b.flac"),
	("file:///run/gvfs/nfs:host=srv,prefix=%252Fmnt/a.flac\r", "/run/gvfs/nfs:host=srv,prefix=%2Fmnt/a.flac"),
	("https://example.com/a%20b.mp3", "https://example.com/a%20b.mp3"),
])
def test_uri_parse(value: str, expected: str) -> None:
	assert uri_parse(value) == expected


@pytest.mark.parametrize(("uri", "expected"), [
	(f"/run/gvfs/{GVFS_FOLDER}/a.flac", f"/run/gvfs/{GVFS_FOLDER}/a.flac"),
	("file:///music/a%20b.flac", "/music/a b.flac"),
])
def test_open_uri_target(uri: str, expected: str) -> None:
	tauon = Tauon.__new__(Tauon)
	tauon.pctl = SimpleNamespace(multi_playlist=[SimpleNamespace(title="Default", uuid_int=7)])
	tauon.gui = SimpleNamespace(auto_play_import=True, request_frame=Mock())
	tauon.load_orders = []
	tauon.open_uri(uri)
	assert tauon.load_orders[0].target == expected


def xspf_fullpath(tmp_path: Path, location: str) -> str:
	"""Import a one track XSPF playlist and return the track's resolved path."""
	tauon = Tauon.__new__(Tauon)
	tauon.gui = SimpleNamespace(auto_play_import=False, to_got=0)
	tauon.pctl = SimpleNamespace(master_library={}, master_count=0)
	tauon.show_message = Mock()
	tauon.tag_scan = lambda track: track
	playlist = tmp_path / "list.xspf"
	playlist.write_text(
		'<playlist xmlns="http://xspf.org/ns/0/"><trackList>'
		f"<track><location>{location}</location></track>"
		"</trackList></playlist>",
	)
	tracks, _stations, _name = tauon.parse_xspf(str(playlist))
	return tauon.pctl.master_library[tracks[0]].fullpath


def test_xspf_file_uri_is_decoded_once(tmp_path: Path) -> None:
	audio = tmp_path / GVFS_FOLDER / "a.flac"
	audio.parent.mkdir()
	audio.write_bytes(b"")
	assert xspf_fullpath(tmp_path, audio.as_uri()) == str(audio.resolve())


def test_xspf_plain_location_is_decoded_once(tmp_path: Path) -> None:
	audio = tmp_path / GVFS_FOLDER / "a b.flac"
	audio.parent.mkdir()
	audio.write_bytes(b"")
	# Same encoding as export_xspf
	location = f"{GVFS_FOLDER.replace('%', '%25').replace(':', '%3A').replace('=', '%3D').replace(',', '%2C')}/a%20b.flac"
	assert xspf_fullpath(tmp_path, location) == str(audio.resolve())


def test_xspf_stream_url_stays_encoded(tmp_path: Path) -> None:
	tauon = Tauon.__new__(Tauon)
	tauon.gui = SimpleNamespace(auto_play_import=False, to_got=0)
	tauon.pctl = SimpleNamespace(master_library={}, master_count=0)
	tauon.radiobox = SimpleNamespace(start=Mock())
	tauon.show_message = Mock()
	tauon.add_stations = Mock()
	playlist = tmp_path / "list.xspf"
	playlist.write_text(
		'<playlist xmlns="http://xspf.org/ns/0/"><trackList>'
		"<track><location>https://example.com/a%20b.mp3</location></track>"
		"</trackList></playlist>",
	)
	_tracks, stations, _name = tauon.parse_xspf(str(playlist))
	assert stations[0].stream_url == "https://example.com/a%20b.mp3"


def test_paste_keeps_plain_path_and_decodes_uri(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(
		"tauon.t_modules.t_main.copy_from_clipboard",
		lambda: f"/run/gvfs/{GVFS_FOLDER}/a.flac\r\nfile:///music/a%20b.flac",
	)
	tauon = Tauon.__new__(Tauon)
	tauon.pctl = SimpleNamespace(multi_playlist=[SimpleNamespace(uuid_int=7)], active_playlist_viewing=0)
	tauon.gui = SimpleNamespace(request_frame=Mock(), request_tracklist_redraw=Mock())
	tauon.load_orders = []
	tauon.paste()
	assert [order.target for order in tauon.load_orders] == [f"/run/gvfs/{GVFS_FOLDER}/a.flac", "/music/a b.flac"]
