# Copyright © 2026, Tauon contributors
"""Radio stations imported from M3U, PLS and XSPF playlist files."""

import os

os.environ["SDL_DISABLE_METADATA"] = "1"
os.environ["SDL_DOC_GENERATOR"] = "0"

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import pytest

from tauon.t_modules.t_extra import decode_playlist_text
from tauon.t_modules.t_main import Tauon


def make_tauon() -> Tauon:
	tauon = Tauon.__new__(Tauon)
	tauon.gui = SimpleNamespace(auto_play_import=False, to_got=0)
	tauon.pctl = SimpleNamespace(master_library={}, master_count=0)
	tauon.radiobox = SimpleNamespace(start=Mock())
	tauon.show_message = Mock()
	tauon.add_stations = Mock()
	return tauon


def stations_of(tauon: Tauon) -> list[tuple[str, str]]:
	tauon.add_stations.assert_called_once()
	return [(s.title, s.stream_url) for s in tauon.add_stations.call_args.args[0]]


# decode_playlist_text

def test_decode_strips_utf8_bom() -> None:
	assert decode_playlist_text("﻿http://a/stream".encode()) == "http://a/stream"


def test_decode_falls_back_to_cp1252() -> None:
	assert decode_playlist_text("Café Radio – Jazz".encode("cp1252")) == "Café Radio – Jazz"


def test_decode_falls_back_to_latin1_for_bytes_cp1252_lacks() -> None:
	assert decode_playlist_text(b"Radio \x81") == "Radio \x81"


# M3U

@pytest.mark.parametrize("suffix", [".m3u", ".m3u8"])
def test_m3u_with_bom_keeps_first_url(tmp_path: Path, suffix: str) -> None:
	path = tmp_path / f"stations{suffix}"
	path.write_bytes("﻿http://a/one\nhttp://a/two\n".encode())
	tracks, stations = make_tauon().parse_m3u(str(path))
	assert tracks == []
	assert [s.stream_url for s in stations] == ["http://a/one", "http://a/two"]


def test_m3u_in_cp1252_imports_with_title(tmp_path: Path) -> None:
	path = tmp_path / "stations.m3u"
	path.write_bytes("#EXTM3U\n#EXTINF:-1,Café FM\nhttp://a/cafe\n".encode("cp1252"))
	tauon = make_tauon()
	_tracks, stations = tauon.parse_m3u(str(path))
	assert [(s.title, s.stream_url) for s in stations] == [("Café FM", "http://a/cafe")]
	tauon.show_message.assert_not_called()


# PLS

PLS = """[playlist]
NumberOfEntries=2
File1=http://a/one
Title1=One
File2=http://a/two
Title2=Two
"""


def test_pls_imports_stations_in_order(tmp_path: Path) -> None:
	path = tmp_path / "radio.pls"
	path.write_text(PLS)
	tauon = make_tauon()
	tauon.load_pls(str(path))
	assert stations_of(tauon) == [("One", "http://a/one"), ("Two", "http://a/two")]
	assert tauon.add_stations.call_args.args[1] == "radio.pls"


def test_pls_with_bom_and_cp1252(tmp_path: Path) -> None:
	path = tmp_path / "radio.pls"
	path.write_bytes(b"\xef\xbb\xbf" + b"[playlist]\r\nFile1=http://a/one\r\nTitle1=Caf\xc3\xa9\r\n")
	tauon = make_tauon()
	tauon.load_pls(str(path))
	assert stations_of(tauon) == [("Café", "http://a/one")]

	path.write_bytes("[playlist]\nFile1=http://a/one\nTitle1=Café\n".encode("cp1252"))
	tauon = make_tauon()
	tauon.load_pls(str(path))
	assert stations_of(tauon) == [("Café", "http://a/one")]


def test_linked_pls_merges_into_one_radio_playlist(tmp_path: Path) -> None:
	path = tmp_path / "radio.pls"
	path.write_text("[playlist]\nFile1=http://a/one\nTitle1=One\nFile2=http://a/more.pls\nFile3=http://a/three\nTitle3=Three\n")
	tauon = make_tauon()
	tauon.fetch_small_file = Mock(return_value=b"[playlist]\nFile1=http://b/linked\nTitle1=Linked\nFile2=http://b/deeper.pls\n")
	tauon.load_pls(str(path))
	assert stations_of(tauon) == [
		("One", "http://a/one"),
		("Linked", "http://b/linked"),
		("Three", "http://a/three"),
	]
	# Only one level of links is followed
	tauon.fetch_small_file.assert_called_once_with("http://a/more.pls")


def fake_response(chunks: list[bytes], headers: dict[str, str] | None = None) -> MagicMock:
	response = MagicMock()
	response.__enter__.return_value = response
	response.headers = headers or {}
	response.iter_content.return_value = iter(chunks)
	return response


def test_fetch_small_file_without_content_length() -> None:
	with patch("tauon.t_modules.t_main.requests.get", return_value=fake_response([b"[playlist]\n", b"File1=http://a\n"])):
		assert make_tauon().fetch_small_file("http://a/x.pls") == b"[playlist]\nFile1=http://a\n"


def test_fetch_small_file_rejects_large_or_endless_body() -> None:
	def endless():
		while True:
			yield b"x" * 1024

	with patch("tauon.t_modules.t_main.requests.get", return_value=fake_response(endless())):
		assert make_tauon().fetch_small_file("http://a/stream.pls") is None


def test_fetch_small_file_http_error() -> None:
	response = fake_response([b"not found"])
	response.raise_for_status.side_effect = Exception("404")
	with patch("tauon.t_modules.t_main.requests.get", return_value=response):
		assert make_tauon().fetch_small_file("http://a/missing.pls") is None


# XSPF

def write_xspf(tmp_path: Path, body: str, name: str = "list.xspf") -> str:
	path = tmp_path / name
	path.write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<playlist version="1" xmlns="http://xspf.org/ns/0/">{body}</playlist>')
	return str(path)


def test_xspf_stations_keep_order_and_own_titles(tmp_path: Path) -> None:
	path = write_xspf(tmp_path, """
		<title>My Radios</title>
		<info>http://example.com/list</info>
		<trackList>
			<track><location>http://a/one</location><title>One</title></track>
			<track><location>http://a/two</location><title>Two</title><info>http://two.example</info></track>
			<track><location>http://a/three</location></track>
		</trackList>""")
	tauon = make_tauon()
	tauon.gui.auto_play_import = True
	playlist, stations, name = tauon.parse_xspf(path)
	assert playlist == []
	assert name == "My Radios"
	assert [(s.title, s.stream_url) for s in stations] == [
		("One", "http://a/one"),
		("Two", "http://a/two"),
		("My Radios", "http://a/three"),
	]
	assert [s.website_url for s in stations] == ["http://example.com/list", "http://two.example", "http://example.com/list"]
	assert tauon.radiobox.start.call_args.args[0] is stations[0]


def test_xspf_station_title_falls_back_to_file_name(tmp_path: Path) -> None:
	path = write_xspf(tmp_path, "<trackList><track><location>http://a/one</location></track></trackList>", name="Favourites.xspf")
	_playlist, stations, _name = make_tauon().parse_xspf(path)
	assert stations[0].title == "Favourites"


def test_xspf_track_without_location_does_not_crash(tmp_path: Path) -> None:
	path = write_xspf(tmp_path, """
		<title/>
		<info/>
		<trackList>
			<track><title>Cue track</title><creator>Artist</creator></track>
			<track><location>http://a/one</location><title>One</title></track>
		</trackList>""")
	tauon = make_tauon()
	playlist, stations, name = tauon.parse_xspf(path)
	assert name == ""
	assert [(s.title, s.stream_url) for s in stations] == [("One", "http://a/one")]
	assert len(playlist) == 1
	track = tauon.pctl.master_library[playlist[0]]
	assert (track.artist, track.title, track.found) == ("Artist", "Cue track", False)


# Non-HTTP stations

def test_non_http_stations_import_from_every_format(tmp_path: Path) -> None:
	m3u = tmp_path / "list.m3u"
	m3u.write_text("#EXTINF:-1,Live\nrtsp://a/live\nnotes.txt\n")
	_tracks, stations = make_tauon().parse_m3u(str(m3u))
	assert [(s.title, s.stream_url) for s in stations] == [("Live", "rtsp://a/live")]

	pls = tmp_path / "list.pls"
	pls.write_text("[playlist]\nFile1=rtmp://a/live/x\nTitle1=Flash\nFile2=/music/local.mp3\n")
	tauon = make_tauon()
	tauon.load_pls(str(pls))
	assert stations_of(tauon) == [("Flash", "rtmp://a/live/x")]

	xspf = write_xspf(tmp_path, "<trackList><track><location>mms://a/radio</location><title>Old</title></track></trackList>")
	playlist, stations, _name = make_tauon().parse_xspf(xspf)
	assert playlist == []
	assert [(s.title, s.stream_url) for s in stations] == [("Old", "mms://a/radio")]
