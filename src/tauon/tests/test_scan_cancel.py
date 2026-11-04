# Copyright © 2026, Tauon contributors

from __future__ import annotations

import builtins
import time
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from tauon.t_modules import t_main
from tauon.t_modules.t_activity import IMPLICIT_COLOUR, ActivityPopover, collect_activities
from tauon.t_modules.t_jellyfin import Jellyfin
from tauon.t_modules.t_server_sync import SCAN_CHANGES, SCAN_PROCESSING, ScanCancelledError
from tauon.t_modules.t_subsonic import SubsonicService

if TYPE_CHECKING:
	from typing import Any

builtins.__dict__.setdefault("_", lambda text: text)


def make_jellyfin(monkeypatch: pytest.MonkeyPatch, pages: int) -> tuple[Jellyfin, list[int], list[str]]:
	stored: list[str] = []
	tauon = SimpleNamespace(
		gui=SimpleNamespace(request_frame=lambda: None, to_got=0),
		pctl=SimpleNamespace(master_library={}),
		prefs=SimpleNamespace(jelly_server_url="https://jellyfin.example"),
		show_message=lambda *_args, **_kwargs: None, wake=lambda: None,
		server_sync=SimpleNamespace(
			library_cache=lambda _code, _server: None, store_library=lambda code, _cache: stored.append(code)),
		t_title="Tauon", device="Test", t_version="test",
	)
	service = Jellyfin(tauon)
	service.connected, service.accessToken, service.userId = True, "token", "user"
	monkeypatch.setattr(service, "_server_time", lambda *_args: 0)
	requested: list[int] = []

	def get(_url: str, *, params: dict[str, Any], **_kwargs: object) -> SimpleNamespace:
		requested.append(params["startIndex"])
		# The user cancels while the first page is loading
		service.cancel_scan = True
		items = [{"Id": f"{params['startIndex']}", "Type": "Audio"}]
		return SimpleNamespace(status_code=200, json=lambda: {"Items": items, "TotalRecordCount": pages})

	monkeypatch.setattr("tauon.t_modules.t_jellyfin.requests.get", get)
	monkeypatch.setattr("tauon.t_modules.t_jellyfin.ITEM_PAGE_SIZE", 1)
	return service, requested, stored


def test_cancelled_jellyfin_scan_stops_at_the_next_page(monkeypatch: pytest.MonkeyPatch) -> None:
	service, requested, stored = make_jellyfin(monkeypatch, pages=50)
	assert service.library_ids("jelly") is None
	assert requested == [0]
	# Nothing remembered, and ready for the next scan
	assert stored == []
	assert not service.scanning
	assert not service.cancel_scan


def test_cancelled_jellyfin_favourites_keep_the_playlist(monkeypatch: pytest.MonkeyPatch) -> None:
	service, _requested, _stored = make_jellyfin(monkeypatch, pages=50)
	assert service.favourite_tracks() is None
	assert not service.cancel_scan


def test_cancelled_subsonic_scan_returns_nothing() -> None:
	service = SubsonicService.__new__(SubsonicService)
	service.gui = SimpleNamespace(request_frame=lambda: None)
	service.scanning = True
	service.cancel_scan = True
	service.library_stamp = lambda: None
	service.server_song_count = 0
	service.prefs = SimpleNamespace(subsonic_server="http://music.example", subsonic_user="kai")
	service.tauon = SimpleNamespace(server_sync=SimpleNamespace(library_cache=lambda _code, _server: None))

	def get_music3(**_kwargs: object) -> list[int]:
		raise ScanCancelledError

	service.get_music3 = get_music3
	assert service.library_ids("air") is None
	assert not service.scanning
	assert not service.cancel_scan


def test_plex_tracks_are_paged_and_stop_when_cancelled() -> None:
	service = t_main.PlexService.__new__(t_main.PlexService)
	service.cancel_scan = False
	starts: list[int] = []

	def search_tracks(**kwargs: int) -> list[int]:
		starts.append(kwargs["container_start"])
		return list(range(t_main.PLEX_PAGE_SIZE))

	section = SimpleNamespace(searchTracks=search_tracks)

	def read_until_cancelled() -> None:
		for seen, _track in enumerate(service._section_tracks(section), 1):  # noqa: SLF001
			if seen == t_main.PLEX_PAGE_SIZE + 1:
				service.cancel_scan = True

	with pytest.raises(ScanCancelledError):
		read_until_cancelled()
	assert starts == [0, t_main.PLEX_PAGE_SIZE]


def test_plex_paging_ends_on_a_short_page() -> None:
	service = t_main.PlexService.__new__(t_main.PlexService)
	service.cancel_scan = False
	pages = [list(range(t_main.PLEX_PAGE_SIZE)), [1, 2]]
	section = SimpleNamespace(searchTracks=lambda **_kwargs: pages.pop(0))
	assert len(list(service._section_tracks(section))) == t_main.PLEX_PAGE_SIZE + 2  # noqa: SLF001


def test_failed_server_fetch_keeps_the_generated_playlist() -> None:
	playlist = [1]
	assert t_main.Tauon.extend_or_fail(playlist, None)
	assert not t_main.Tauon.extend_or_fail(playlist, [2, 3])
	assert playlist == [1, 2, 3]


def test_popover_cancel_flags_the_server() -> None:
	jellyfin = SimpleNamespace(cancel_scan=False)
	popover = ActivityPopover.__new__(ActivityPopover)
	sync = SimpleNamespace(refresh_cancelled=False)
	popover.tauon = SimpleNamespace(
		gui=SimpleNamespace(request_frame=lambda: None), jellyfin=jellyfin, regen_background=False, server_sync=sync)
	popover.cancel("jellyfin")
	assert jellyfin.cancel_scan
	# An import the user asked for doesn't stop the startup refresh waiting behind it
	assert not sync.refresh_cancelled


def test_popover_cancel_of_a_background_scan_stops_the_refresh() -> None:
	popover = ActivityPopover.__new__(ActivityPopover)
	sync = SimpleNamespace(refresh_cancelled=False)
	popover.tauon = SimpleNamespace(
		gui=SimpleNamespace(request_frame=lambda: None), jellyfin=SimpleNamespace(cancel_scan=False),
		regen_background=True, server_sync=sync)
	popover.cancel("jellyfin")
	assert sync.refresh_cancelled


def test_jellyfin_import_pages_in_parallel_keep_their_order(monkeypatch: pytest.MonkeyPatch) -> None:
	service, _requested, _stored = make_jellyfin(monkeypatch, pages=0)
	service.tauon.TrackClass = t_main.TrackClass
	service.tauon.sort_track_2 = lambda *_args: None
	service.tauon.star_store = SimpleNamespace(full_get=lambda _index: None, insert=lambda *_args: None)
	service.tauon.album_art_gen = SimpleNamespace(source_cache={})
	service.tauon.server_sync.pending = lambda *_args: set()
	service.pctl.master_count = 1
	totals: list[bool] = []

	def get(_url: str, *, params: dict[str, Any], **_kwargs: object) -> SimpleNamespace:
		start = params["startIndex"]
		totals.append(params["enableTotalRecordCount"])
		# Later pages answer first
		time.sleep(0.02 * (5 - start))
		item = {
			"Id": f"t{start}", "Type": "Audio", "Name": f"t{start}", "AlbumArtist": "A", "Album": "B",
			"IndexNumber": start, "DateCreated": "2026-01-01T00:00:00.000Z",
			"MediaSources": [{"Path": f"/m/{start}.flac", "Size": 1, "MediaStreams": []}]}
		return SimpleNamespace(status_code=200, json=lambda: {"Items": [item], "TotalRecordCount": 5})

	monkeypatch.setattr("tauon.t_modules.t_jellyfin.requests.get", get)
	track_ids = service.ingest_library(return_list=True)
	assert [service.pctl.master_library[t].url_key for t in track_ids] == ["t0", "t1", "t2", "t3", "t4"]
	# Only the first page asks for the slow total
	assert totals.count(True) == 1
	assert service.gui.to_got == 5
	assert service.scan_total == 5


def activity_tauon(regen_background: bool) -> SimpleNamespace:
	idle = SimpleNamespace(scanning=False)
	return SimpleNamespace(
		gui=SimpleNamespace(to_got=10, im_cancel=False, sync_progress="", buffering=False),
		pctl=SimpleNamespace(loading_in_progress=False), cm_clean_db=False, after_scan=[], playlist_autoscan=False,
		move_in_progress=False, to_scan=[], plex=idle, subsonic=idle,
		jellyfin=SimpleNamespace(scanning=True, cancel_scan=False, scan_total=40), chrome_mode=False, transcode_list=[],
		lrclib_uploads=[], lastfm=SimpleNamespace(scanning_friends=False, scanning_loves=False, scanning_scrobbles=False),
		lfm_scrobbler=SimpleNamespace(queue=[]), scrobble_warning_timer=SimpleNamespace(get=lambda: 300),
		server_sync=SimpleNamespace(stalled=list), listen_alongers={}, regen_background=regen_background)


def test_background_refresh_shows_grey() -> None:
	row = collect_activities(activity_tauon(regen_background=True))[0]
	assert row.implicit
	assert row.title == "Updating JELLYFIN library…"
	assert row.colour == IMPLICIT_COLOUR
	# Still cancellable and counted
	assert row.cancel
	assert row.detail == "10 of 40 tracks"


def test_import_the_user_asked_for_keeps_its_colour() -> None:
	row = collect_activities(activity_tauon(regen_background=False))[0]
	assert not row.implicit
	assert row.title == "Accessing JELLYFIN library…"
	assert row.colour != IMPLICIT_COLOUR


def test_changed_tracks_are_counted_on_their_own() -> None:
	tauon = activity_tauon(regen_background=True)
	tauon.jellyfin.scan_stage = SCAN_CHANGES
	row = collect_activities(tauon)[0]
	assert row.detail == "10 of 40 changed tracks"
	assert row.progress == 0.25
	assert row.cancel


def test_processing_has_no_bar_and_cant_be_cancelled() -> None:
	tauon = activity_tauon(regen_background=True)
	tauon.jellyfin.scan_stage = SCAN_PROCESSING
	row = collect_activities(tauon)[0]
	assert row.detail == "Processing tracks…"
	assert row.progress is None
	assert not row.cancel
