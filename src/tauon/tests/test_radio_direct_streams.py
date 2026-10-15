# Copyright © 2026, Tauon contributors
"""Radio stations that FFmpeg plays directly: non-HTTP protocols, HLS, DASH and MPEG-TS."""

import os

os.environ["SDL_DISABLE_METADATA"] = "1"
os.environ["SDL_DOC_GENERATOR"] = "0"

from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from tauon.t_modules.t_extra import RadioStation, is_stream_url, normalise_stream_url
from tauon.t_modules.t_main import RadioBox

HLS_MEDIA = b"#EXTM3U\n#EXT-X-TARGETDURATION:2\n#EXTINF:2.0,\nseg000.ts\n"
HLS_MASTER = b"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=96000\nmedia.m3u8\n"


@pytest.mark.parametrize(("url", "expected"), [
	("http://a/stream", True),
	("HTTPS://a/stream", True),
	("rtsp://a/live", True),
	("rtmp://a/live/x", True),
	("mms://a/radio", True),
	("icy://a:8000/", True),
	("file:///music/a.mp3", False),
	("ftp://a/x.mp3", False),
	("/music/http://odd.mp3", False),
	("C:/Music/a.mp3", False),
	("stream", False),
])
def test_is_stream_url(url: str, expected: bool) -> None:
	assert is_stream_url(url) is expected


@pytest.mark.parametrize(("url", "expected"), [
	("icy://a:8000/live", "http://a:8000/live"),
	("ICY://a/", "http://a/"),
	("mms://a/radio", "mmsh://a/radio"),
	("rtsp://a/live", "rtsp://a/live"),
	("http://a/icy://", "http://a/icy://"),
])
def test_normalise_stream_url(url: str, expected: str) -> None:
	assert normalise_stream_url(url) == expected


def make_radiobox(files: dict[str, bytes] | None = None) -> RadioBox:
	box = RadioBox.__new__(RadioBox)
	files = files or {}
	box.tauon = MagicMock()
	box.tauon.fetch_small_file = Mock(side_effect=lambda url, limit=2000: files.get(url))
	box.tauon.stream_proxy.start_download = Mock(return_value=True)
	box.tauon.stream_proxy.download_running = False
	box.tauon.stream_proxy.encode_running = False
	box.tauon.stream_proxy.pump_running = False
	box.pctl = MagicMock()
	box.prefs = SimpleNamespace(auto_rec=False)
	box.gui = SimpleNamespace(request_frame=Mock())
	box.show_message = Mock()
	box.load_request_id = 1
	box.load_failed_timer = Mock()
	return box


@pytest.mark.parametrize(("url", "direct"), [
	("http://a/stream.mp3", False),
	("https://a/live?token=1", False),
	("http://a/live.m3u8?token=1", True),
	("http://a/manifest.mpd", True),
	("http://a/stream.ts", True),
	("rtsp://a/live", True),
	("rtmp://a/live/x", True),
	("mmsh://a/radio", True),
])
def test_plays_direct(url: str, direct: bool) -> None:
	assert make_radiobox().plays_direct(url) is direct


def test_m3u_suffix_ignores_query_string() -> None:
	box = make_radiobox()
	assert box.is_m3u("http://a/listen.m3u?sid=1")
	assert not box.is_m3u("http://a/m3u?x=.m3u")


def test_hls_playlist_resolves_to_itself() -> None:
	box = make_radiobox({"http://a/live.m3u8": HLS_MASTER})
	assert box.extract_stream_m3u("http://a/live.m3u8") == "http://a/live.m3u8"


def test_plain_m3u_resolves_through_to_hls() -> None:
	box = make_radiobox({
		"http://a/radio.m3u": b"#EXTM3U\n#EXTINF:-1,Test\nhls/master.m3u8\n",
		"http://a/hls/master.m3u8": HLS_MASTER,
	})
	assert box.extract_stream_m3u("http://a/radio.m3u") == "http://a/hls/master.m3u8"


def test_plain_m3u_can_list_non_http_stream() -> None:
	box = make_radiobox({"http://a/radio.m3u": b"\xef\xbb\xbfmms://b/radio\n"})
	assert box.extract_stream_m3u("http://a/radio.m3u") == "mmsh://b/radio"


def test_m3u_that_is_really_a_stream_fails_cleanly() -> None:
	box = make_radiobox()  # fetch_small_file returns None, as for an oversized body
	assert box.extract_stream_m3u("http://a/radio.m3u") is None


def start(box: RadioBox, url: str) -> None:
	box.start2(RadioStation(title="Test", stream_url=url), 1)


def test_http_stream_goes_through_proxy() -> None:
	box = make_radiobox()
	start(box, "icy://a:8000/live")
	assert box.run_proxy
	box.tauon.stream_proxy.start_download.assert_called_once_with("http://a:8000/live", 1)
	assert box.pctl.url == "http://127.0.0.1:7812"


@pytest.mark.parametrize(("station_url", "played_url"), [
	("rtsp://a/live", "rtsp://a/live"),
	("mms://a/radio", "mmsh://a/radio"),
	("http://a/live.m3u8", "http://a/live.m3u8"),
	("http://a/radio.m3u", "http://a/hls/master.m3u8"),
])
def test_direct_streams_bypass_proxy(station_url: str, played_url: str) -> None:
	box = make_radiobox({
		"http://a/live.m3u8": HLS_MEDIA,
		"http://a/radio.m3u": b"hls/master.m3u8\n",
		"http://a/hls/master.m3u8": HLS_MASTER,
	})
	start(box, station_url)
	assert not box.run_proxy
	box.tauon.stream_proxy.start_download.assert_not_called()
	assert box.pctl.url == played_url
	assert box.pctl.playerCommand == "url"
	box.show_message.assert_not_called()


def test_hls_without_m3u8_suffix_still_plays_direct() -> None:
	box = make_radiobox({"http://a/live.m3u": HLS_MEDIA})
	start(box, "http://a/live.m3u")
	assert not box.run_proxy
	assert box.pctl.url == "http://a/live.m3u"


def test_recording_warns_for_direct_streams() -> None:
	box = make_radiobox()
	box.prefs.auto_rec = True
	start(box, "rtsp://a/live")
	box.show_message.assert_called_once()


def test_rtsp_m3u_url_is_not_fetched_over_http() -> None:
	box = make_radiobox()
	start(box, "rtsp://a/live.m3u")
	box.tauon.fetch_small_file.assert_not_called()
	assert box.pctl.url == "rtsp://a/live.m3u"
