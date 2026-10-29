# Copyright © 2026, Tauon contributors

from types import SimpleNamespace

import pytest

from tauon.t_modules.t_main import PlayerCtl, Tauon, TrackClass


@pytest.fixture
def library() -> Tauon:
	owner = object.__new__(Tauon)
	owner.pctl = object.__new__(PlayerCtl)
	owner.pctl.multi_playlist = [SimpleNamespace(uuid_int=100, title="Library", playlist_ids=[1, 2, 3])]
	owner.pctl.master_library = {}
	lyrics = {
		1: ("Walking down the midnight highway", ""),
		2: ("", "[ar:Someone]\n[00:12.34]Dancing <00:13.00>under the <00:13.50>neon rain\n[00:20.00]Ah"),
		3: ("", ""),
	}
	for index, (plain, synced) in lyrics.items():
		track = TrackClass()
		track.index = index
		track.title, track.artist, track.album = f"Song {index}", "Artist", "Album"
		track.filename = f"{index}.flac"
		track.lyrics, track.synced = plain, synced
		owner.pctl.master_library[index] = track
	owner.search_string_cache = {}
	owner.search_dia_string_cache = {}
	owner.search_field_cache = {}
	owner.search_dia_field_cache = {}
	owner.search_lyrics_cache = {}
	owner.use_cc = False
	owner.prefs = SimpleNamespace(sep_genre_multi=False, search_lyrics=True)
	return owner


def lyric_hits(owner: Tauon, query: str) -> set[int]:
	return {result[2] for result in owner._build_search_results(query) if result[0] == 9}  # noqa: SLF001


@pytest.mark.parametrize("warm", [False, True])
def test_lyrics_match_plain_and_synced(library: Tauon, warm: bool) -> None:
	if warm:
		library._build_search_results("unmatched")  # noqa: SLF001
	assert lyric_hits(library, "midnight highway") == {1}
	assert lyric_hits(library, "under the neon") == {2}


def test_lyrics_ignore_lrc_tags_and_short_queries(library: Tauon) -> None:
	assert lyric_hits(library, "someone") == set()
	assert lyric_hits(library, "00:12") == set()
	assert lyric_hits(library, "rain") == {2}
	assert lyric_hits(library, "ain") == set()


def test_lyrics_off_by_pref(library: Tauon) -> None:
	library.prefs.search_lyrics = False
	assert lyric_hits(library, "midnight highway") == set()
	assert library.search_lyrics_cache == {}


def test_lyrics_kept_out_of_persisted_caches(library: Tauon) -> None:
	library._build_search_results("midnight highway")  # noqa: SLF001
	assert all("midnight" not in text for text in library.search_string_cache.values())
	assert all("midnight" not in text for text in library.search_dia_string_cache.values())


def test_lyrics_edit_refreshes_cache(library: Tauon) -> None:
	assert lyric_hits(library, "midnight highway") == {1}
	library.pctl.master_library[1].lyrics = "Sailing over golden water"
	assert lyric_hits(library, "midnight highway") == set()
	assert lyric_hits(library, "golden water") == {1}
