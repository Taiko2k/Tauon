# Copyright © 2026, Tauon contributors

from __future__ import annotations

import builtins
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from tauon.t_modules.t_jellyfin import Jellyfin
from tauon.t_modules.t_main import PlayerCtl, Prefs
from tauon.t_modules.t_phazor import Cachement
from tauon.t_modules.t_subsonic import SubsonicService

if TYPE_CHECKING:
	from pathlib import Path

builtins.__dict__.setdefault("_", lambda text: text)


def make_pctl(setting: int) -> PlayerCtl:
	pctl = PlayerCtl.__new__(PlayerCtl)
	pctl.prefs = SimpleNamespace(
		jelly_stream_bitrate=setting, subsonic_stream_bitrate=setting, plex_stream_bitrate=setting,
		jelly_stream_format="mp3", subsonic_stream_format="mp3")
	return pctl


def track(file_ext: str = "JELY", bitrate: int = 0) -> SimpleNamespace:
	return SimpleNamespace(file_ext=file_ext, bitrate=bitrate, is_network=True, index=5, url_key="abc")


def test_it_defaults_to_the_original_file() -> None:
	assert Prefs.jelly_stream_bitrate == Prefs.subsonic_stream_bitrate == Prefs.plex_stream_bitrate == 0
	assert make_pctl(0).transcode_bitrate(track()) == 0


@pytest.mark.parametrize("file_ext", ["JELY", "SUB", "PLEX"])
def test_servers_that_can_transcode_use_the_setting(file_ext: str) -> None:
	assert make_pctl(128).transcode_bitrate(track(file_ext)) == 128


@pytest.mark.parametrize("file_ext", ["TIDAL", "TAU", ""])
def test_other_sources_keep_the_original(file_ext: str) -> None:
	assert make_pctl(128).transcode_bitrate(track(file_ext)) == 0


def test_each_server_has_its_own_setting() -> None:
	pctl = make_pctl(0)
	pctl.prefs.subsonic_stream_bitrate = 192
	assert pctl.transcode_bitrate(track("SUB")) == 192
	assert pctl.transcode_bitrate(track("JELY")) == 0
	assert pctl.transcode_bitrate(track("PLEX")) == 0


def test_a_track_already_smaller_is_not_converted() -> None:
	pctl = make_pctl(128)
	assert pctl.transcode_bitrate(track(bitrate=96)) == 0
	assert pctl.transcode_bitrate(track(bitrate=128)) == 0
	assert pctl.transcode_bitrate(track(bitrate=320)) == 128


def make_jellyfin() -> Jellyfin:
	jellyfin = object.__new__(Jellyfin)
	jellyfin.connected, jellyfin.accessToken, jellyfin.userId = True, "secret", "user"
	jellyfin.prefs = SimpleNamespace(jelly_server_url="https://jf.example/")
	jellyfin.session_thread_active = True
	return jellyfin


def test_jellyfin_asks_for_a_new_conversion_per_quality() -> None:
	jellyfin = make_jellyfin()
	url, params = jellyfin.resolve_stream("song", 128)
	assert url == "https://jf.example/Audio/song/stream.mp3"
	assert "static" not in params
	assert params["audioCodec"] == "mp3"
	assert params["audioBitRate"] == 128000
	assert params["playSessionId"] != jellyfin.resolve_stream("song", 96)[1]["playSessionId"]


def test_jellyfin_asks_for_a_new_conversion_per_track() -> None:
	jellyfin = make_jellyfin()
	first = jellyfin.resolve_stream("first", 128)[1]["playSessionId"]
	assert first != jellyfin.resolve_stream("second", 128)[1]["playSessionId"]


def test_jellyfin_original_is_static() -> None:
	url, params = make_jellyfin().resolve_stream("song")
	assert url == "https://jf.example/Audio/song/stream"
	assert params["static"] == "true"


def test_subsonic_asks_for_mp3_in_kbps() -> None:
	service = SubsonicService.__new__(SubsonicService)
	service.r = lambda _point, p, **_kwargs: ("url", p)
	assert service.resolve_stream("song", 128)[1] == {"id": "song", "format": "mp3", "maxBitRate": 128}
	assert service.resolve_stream("song")[1] == {"id": "song"}


def test_format_defaults_to_mp3_and_is_per_server() -> None:
	assert Prefs.jelly_stream_format == Prefs.subsonic_stream_format == "mp3"
	pctl = make_pctl(128)
	pctl.prefs.jelly_stream_format = "opus"
	assert pctl.transcode_format(track("JELY")) == "opus"
	assert pctl.transcode_format(track("SUB")) == "mp3"
	assert pctl.transcode_format(track("PLEX")) == "mp3"
	# A hand edited config can't request anything else
	pctl.prefs.jelly_stream_format = "wav"
	assert pctl.transcode_format(track("JELY")) == "mp3"


def test_jellyfin_opus_is_ogg_with_its_own_conversion() -> None:
	jellyfin = make_jellyfin()
	url, params = jellyfin.resolve_stream("song", 96, "opus")
	assert url == "https://jf.example/Audio/song/stream.ogg"
	assert params["audioCodec"] == "opus"
	assert params["playSessionId"] != jellyfin.resolve_stream("song", 96, "mp3")[1]["playSessionId"]


def test_subsonic_asks_for_the_chosen_format() -> None:
	service = SubsonicService.__new__(SubsonicService)
	service.r = lambda _point, p, **_kwargs: ("url", p)
	assert service.resolve_stream("song", 96, "opus")[1] == {"id": "song", "format": "opus", "maxBitRate": 96}


def test_only_the_download_path_transcodes() -> None:
	pctl = make_pctl(128)
	seen: list[int] = []
	pctl.tauon = SimpleNamespace(jellyfin=SimpleNamespace(
		scan_lyrics=lambda _track: None, resolve_stream=lambda _key, bitrate, _format: seen.append(bitrate) or ("u", {})))
	pctl.get_url(track())
	pctl.get_url(track(), transcode=True)
	assert seen == [0, 128]


def test_cache_keeps_each_quality_apart_and_prefers_the_original() -> None:
	cache = Cachement.__new__(Cachement)
	cache.files = []
	cache.pctl = make_pctl(0)
	item = track()
	original = cache.get_key(item)
	cache.pctl.prefs.jelly_stream_bitrate = 128
	low = cache.get_key(item)
	cache.pctl.prefs.jelly_stream_bitrate = 96
	lower = cache.get_key(item)
	cache.pctl.prefs.jelly_stream_format = "opus"
	opus = cache.get_key(item)
	assert len({original, low, lower, opus}) == 4
	cache.files = [original]
	assert cache.get_key(item) == original


@pytest.mark.parametrize(
	("status", "content_type"),
	[(500, "text/plain"), (200, "application/json"), (200, "text/xml; charset=UTF-8")],
)
def test_a_failed_transcode_is_reported_and_not_cached(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: int, content_type: str,
) -> None:
	messages: list[tuple] = []
	cache = Cachement.__new__(Cachement)
	cache.direc, cache.files, cache.list, cache.error = str(tmp_path), [], [], None
	cache.ready = None
	cache.gui = SimpleNamespace(buffering_text="", request_frame=lambda: None)
	cache.prefs = SimpleNamespace(jump_start=True)
	cache.show_message = lambda *args, **_kwargs: messages.append(args)
	cache.pctl = make_pctl(128)
	cache.pctl.buffering_percent = 0
	cache.pctl.get_url = lambda _track, transcode: ("http://server/stream", {})
	item = track()
	monkeypatch.setattr(
		"tauon.t_modules.t_phazor.requests.get",
		lambda *_args, **_kwargs: SimpleNamespace(status_code=status, headers={"Content-Type": content_type}))
	assert cache.dl_file(item) == 1
	assert cache.error is item
	assert cache.files == []
	assert "transcode" in messages[0][0]
	assert list(tmp_path.iterdir()) == []


def test_a_new_download_forgets_an_earlier_one_was_ready(tmp_path: Path) -> None:
	cache = Cachement.__new__(Cachement)
	cache.direc, cache.files, cache.error, cache.get_now = str(tmp_path), [], None, None
	cache.running = True
	cache.pctl = make_pctl(128)
	cache.tauon = SimpleNamespace(encode_folder_name=lambda _track: "a", encode_track_name=lambda _track: "b")
	cache.prefs = SimpleNamespace(encoder_output=str(tmp_path))
	item = track()
	cache.ready = item
	assert cache.get_file(item)[0] == 1
	assert cache.ready is None
	assert cache.get_now is item
