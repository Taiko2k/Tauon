# Copyright © 2026, Tauon contributors

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tauon.t_modules import t_main


def make_lb(url: str = "") -> t_main.ListenBrainz:
	prefs = SimpleNamespace(enable_lb=True, lb_token="tok", listenbrainz_url=url)
	tauon = SimpleNamespace(bag=None, prefs=prefs, t_title="Tauon", n_version="1", show_message=Mock())
	return t_main.ListenBrainz(tauon)


def make_track(**kw: object) -> SimpleNamespace:
	base = {"title": "Karma Police", "artist": "Radiohead", "album": "OK Computer", "album_artist": "", "artists": [], "musicbrainz_recordingid": None}
	base.update(kw)
	return SimpleNamespace(**base)


def response(payload: dict) -> Mock:
	r = Mock()
	r.json.return_value = payload
	return r


@pytest.mark.parametrize(("loved", "score"), [(True, 1), (False, 0)])
def test_love_uses_tagged_recording_mbid(monkeypatch: pytest.MonkeyPatch, loved: bool, score: int) -> None:
	get, post = Mock(), Mock(return_value=response({}))
	monkeypatch.setattr(t_main.requests, "get", get)
	monkeypatch.setattr(t_main.requests, "post", post)

	assert make_lb().love(make_track(musicbrainz_recordingid="abc"), loved) is True

	get.assert_not_called()
	args, kwargs = post.call_args
	assert args[0] == "https://api.listenbrainz.org/1/feedback/recording-feedback"
	assert kwargs["json"] == {"recording_mbid": "abc", "score": score}
	assert kwargs["headers"] == {"Authorization": "Token tok"}


def test_love_looks_up_and_caches_mbid(monkeypatch: pytest.MonkeyPatch) -> None:
	get = Mock(return_value=response({"recording_mbid": "found"}))
	post = Mock(return_value=response({}))
	monkeypatch.setattr(t_main.requests, "get", get)
	monkeypatch.setattr(t_main.requests, "post", post)

	lb = make_lb("https://lb.example")
	track = make_track()
	assert lb.love(track) is True
	assert lb.love(track, False) is True

	get.assert_called_once()
	args, kwargs = get.call_args
	assert args[0] == "https://lb.example/1/metadata/lookup/"
	assert kwargs["params"] == {"artist_name": "Radiohead", "recording_name": "Karma Police", "release_name": "OK Computer"}
	assert post.call_args.kwargs["json"] == {"recording_mbid": "found", "score": 0}


def test_love_skips_unmatched_track(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(t_main.requests, "get", Mock(return_value=response({})))
	post = Mock()
	monkeypatch.setattr(t_main.requests, "post", post)

	assert make_lb().love(make_track()) is False
	post.assert_not_called()


@pytest.mark.parametrize(("enable", "token", "called"), [(True, "tok", True), (False, "tok", False), (True, "", False)])
def test_tauon_lb_love_respects_enable_and_token(enable: bool, token: str, called: bool) -> None:
	track = make_track()
	tauon = SimpleNamespace(
		lb=SimpleNamespace(enable=enable, love=Mock()), prefs=SimpleNamespace(lb_token=token),
		pctl=SimpleNamespace(master_library={5: track}), show_message=Mock(),
	)
	t_main.Tauon.lb_love(tauon, 5, True)
	if called:
		tauon.lb.love.assert_called_once_with(track, True)
	else:
		tauon.lb.love.assert_not_called()


def test_tauon_lb_love_warns_on_failure() -> None:
	tauon = SimpleNamespace(
		lb=SimpleNamespace(enable=True, love=Mock(side_effect=RuntimeError)), prefs=SimpleNamespace(lb_token="tok"),
		pctl=SimpleNamespace(master_library={5: make_track()}), show_message=Mock(),
	)
	t_main.Tauon.lb_love(tauon, 5, False)
	tauon.show_message.assert_called_once()
