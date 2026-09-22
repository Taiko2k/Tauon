# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from tauon.t_modules import t_lyrics, t_main


def test_genius_return_url_normalizes_input() -> None:
	url = t_lyrics.genius("Beyoncé feat. Jay-Z", "Déjà Vu (feat. X)", return_url=True)
	assert url == "https://genius.com/Beyonce-Deja-Vu-lyrics"


class LyricFetchTimer:
	def get(self) -> int:
		return 0

	def set(self) -> None:
		pass

	def force_set(self, _value: int) -> None:
		pass


def make_tauon(enabled_sources: list[str]) -> SimpleNamespace:
	return SimpleNamespace(
		lyrics_ren=SimpleNamespace(lyrics_position=-1),
		prefs=SimpleNamespace(
			lyrics_enables=enabled_sources,
			lyrics_subs={},
			save_lyrics_changes_to_files=False,
			save_synced_to_lrc=False,
			show_lyrics_side=False,
		),
		lyrics_fetch_timer=LyricFetchTimer(),
		show_message=Mock(),
		t_agent="Tauon/Test",
		search_string_cache={},
		search_dia_string_cache={},
		search_field_cache={},
		search_dia_field_cache={},
		gui=SimpleNamespace(
			lyrics_editor_update_now=[False, False],
			timed_lyrics_edit_view=False,
			message_box=True,
			showcase_mode=False,
			request_frame=Mock(),
		),
		write_lyrics=Mock(),
		timed_lyrics_ren=SimpleNamespace(index=4),
		pctl=SimpleNamespace(notify_database_changed=Mock()),
		now_searching="searching",
	)


def test_lyric_search_prioritizes_synced_sources_and_apis(monkeypatch: pytest.MonkeyPatch) -> None:
	source_calls = Mock()
	static_scraper = Mock(return_value=("scraped static lyrics", ""))
	synced_scraper = Mock(return_value=("later static lyrics", "[00:01.00]Synced lyrics"))
	static_api = Mock(return_value=("API static lyrics", ""))
	synced_api = Mock(return_value=("preferred static lyrics", ""))
	source_calls.attach_mock(static_scraper, "static_scraper")
	source_calls.attach_mock(synced_scraper, "synced_scraper")
	source_calls.attach_mock(static_api, "static_api")
	source_calls.attach_mock(synced_api, "synced_api")
	monkeypatch.setattr(t_main, "lyric_sources", {
		"Static scraper": static_scraper,
		"Synced scraper": synced_scraper,
		"Static API": static_api,
		"Synced API": synced_api,
	})
	monkeypatch.setattr(t_main, "provides_synced", {"Synced scraper", "Synced API"})
	monkeypatch.setattr(t_main, "uses_scraping", {"Static scraper", "Synced scraper"})

	track = SimpleNamespace(index=1, artist="Artist", title="Title", lyrics="", synced="")
	tauon = make_tauon(["Static API", "Static scraper", "Synced scraper", "Synced API"])
	t_main.Tauon.get_lyric_fire(tauon, track)

	assert track.lyrics == "preferred static lyrics"
	assert track.synced == "[00:01.00]Synced lyrics"
	assert source_calls.mock_calls == [
		call.synced_api("Artist", "Title", user_agent="Tauon/Test"),
		call.synced_scraper("Artist", "Title", user_agent="Tauon/Test"),
	]
	assert tauon.now_searching == "success"


def test_lyric_search_uses_api_before_unneeded_scraper(monkeypatch: pytest.MonkeyPatch) -> None:
	static_scraper = Mock(return_value=("scraped static lyrics", ""))
	static_api = Mock(return_value=("API static lyrics", ""))
	monkeypatch.setattr(t_main, "lyric_sources", {
		"Static scraper": static_scraper,
		"Static API": static_api,
	})
	monkeypatch.setattr(t_main, "provides_synced", set())
	monkeypatch.setattr(t_main, "uses_scraping", {"Static scraper"})

	track = SimpleNamespace(index=1, artist="Artist", title="Title", lyrics="", synced="")
	tauon = make_tauon(["Static scraper", "Static API"])
	t_main.Tauon.get_lyric_fire(tauon, track)

	assert track.lyrics == "API static lyrics"
	static_api.assert_called_once_with("Artist", "Title", user_agent="Tauon/Test")
	static_scraper.assert_not_called()
