# Copyright © 2026, Tauon contributors

from __future__ import annotations

import builtins
import json
import time
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
import requests

from tauon.t_modules.t_extra import StarRecord, TauonPlaylist
from tauon.t_modules.t_jellyfin import Jellyfin
from tauon.t_modules.t_scrobble_queue import Outcome
from tauon.t_modules.t_server_sync import (
	JELLYFIN,
	LOVE,
	PLEX,
	RATING,
	SCAN_CHANGES,
	SUBSONIC,
	LibraryCache,
	PlaylistGoneError,
	PlaylistLink,
	RemotePlaylistState,
	ServerSync,
	keep_foreign,
	merge_playlists,
	parse_link,
	uses_server,
)
from tauon.t_modules.t_subsonic import SubsonicService

if TYPE_CHECKING:
	from collections.abc import Callable
	from pathlib import Path
	from typing import Any

builtins.__dict__.setdefault("_", lambda text: text)


@pytest.mark.parametrize(
	("base", "local", "remote", "expected"),
	[
		# Nothing changed
		(["a", "b"], ["a", "b"], ["a", "b"], ["a", "b"]),
		# Added here, added there
		(["a", "b"], ["a", "b", "c"], ["a", "b"], ["a", "b", "c"]),
		(["a", "b"], ["a", "b"], ["a", "x", "b"], ["a", "x", "b"]),
		# Removed on either side
		(["a", "b", "c"], ["a", "c"], ["a", "b", "c"], ["a", "c"]),
		(["a", "b", "c"], ["a", "b", "c"], ["b", "c"], ["b", "c"]),
		# Reordered here, added there: local order wins, the addition follows its remote neighbour
		(["a", "b", "c"], ["c", "b", "a"], ["a", "b", "c", "d"], ["c", "b", "a", "d"]),
		# A remote addition at the very start
		(["a", "b"], ["b", "a"], ["z", "a", "b"], ["z", "b", "a"]),
		# Both sides added and removed
		(["a", "b", "c"], ["a", "c", "l"], ["r", "a", "b"], ["r", "a", "l"]),
		# Duplicates collapse
		(["a"], ["a", "a", "b"], ["a", "a"], ["a", "b"]),
	],
)
def test_merge_playlists(base: list[str], local: list[str], remote: list[str], expected: list[str]) -> None:
	assert merge_playlists(base, local, remote) == expected


def test_keep_foreign_puts_local_files_back_after_their_neighbour() -> None:
	# 10 and 11 are local files, the rest are server tracks
	local = [10, 1, 2, 11, 3]
	assert keep_foreign(local, {10, 11}, [1, 4, 2, 3]) == [10, 1, 4, 2, 11, 3]
	# Their neighbour was removed: they go to the end
	assert keep_foreign(local, {10, 11}, [1, 3]) == [10, 1, 3, 11]
	assert keep_foreign(local, set(), [3, 2]) == [3, 2]


def test_parse_link() -> None:
	assert parse_link('jelly"abc"') == (JELLYFIN, "abc")
	assert parse_link('air"12"') == (SUBSONIC, "12")
	assert parse_link('plexpl"99"') == (PLEX, "99")
	# Libraries, favourites and codes with more commands aren't linked playlists
	assert parse_link('jellylib"abc"') is None
	assert parse_link("air") is None
	assert parse_link('air"12" s"Other"') is None
	assert parse_link('jelly"abc" a') is None
	assert parse_link('jelly""') is None
	assert parse_link(None) is None


def test_uses_server() -> None:
	assert uses_server("jelly")
	assert uses_server('airlib"3" ypa')
	assert uses_server('plexpl"9"')
	assert not uses_server("self a path")
	assert not uses_server("")


class FakeTrack:
	def __init__(self, index: int, file_ext: str = "", url_key: str = "") -> None:
		self.index = index
		self.file_ext = file_ext
		self.url_key = url_key
		self.is_network = bool(file_ext)


class FakeService:
	"""A server holding playlists in memory, recording what it was asked to do."""

	def __init__(self, library: dict[int, FakeTrack], service: str) -> None:
		self.library = library
		self.service = service
		self.playlists: dict[str, dict[str, object]] = {}
		self.writes: list[tuple[str, list[str], str | None]] = []
		self.edits: list[object] = []
		self.results: list[Outcome] = []
		self.fail_write = False
		self.configured = True
		self.counter = 0

	def sync_configured(self) -> bool:
		return self.configured

	def ping(self) -> bool:
		return True

	def track_id(self, server_id: str) -> int:
		for track in self.library.values():
			if track.url_key == server_id and track.file_ext == self.service:
				return track.index
		track = FakeTrack(max(self.library, default=0) + 1, self.service, server_id)
		self.library[track.index] = track
		return track.index

	def fetch_remote_playlist(self, remote_id: str) -> RemotePlaylistState | None:
		if remote_id not in self.playlists:
			raise PlaylistGoneError
		p = self.playlists[remote_id]
		ids = list(p["ids"])
		self.counter += 1
		return RemotePlaylistState(
			ids, [self.track_id(x) for x in ids], f"v{p['version']}", p["name"], p.get("readonly", False))

	def write_remote_playlist(self, remote_id: str, _current: RemotePlaylistState, ids: list[str], name: str | None) -> bool:
		self.writes.append((remote_id, list(ids), name))
		if self.fail_write:
			return False
		p = self.playlists[remote_id]
		p["ids"] = list(ids)
		p["version"] += 1
		if name:
			p["name"] = name
		return True

	def create_remote_playlist(self, name: str, ids: list[str]) -> str | None:
		remote_id = f"new{len(self.playlists)}"
		self.playlists[remote_id] = {"ids": list(ids), "name": name, "version": 1}
		return remote_id

	def push_edit(self, edit: object) -> Outcome:
		self.edits.append(edit)
		return self.results.pop(0) if self.results else Outcome.SENT


def make_playlist(title: str, ids: list[int], uuid: int = 1) -> TauonPlaylist:
	return TauonPlaylist(
		title=title, playing=0, playlist_ids=ids, position=0, hide_title=False, selected=0, uuid_int=uuid,
		last_folder=[], hidden=False, locked=False, parent_playlist_id=0, persist_time_positioning=False)


def make_sync(tmp_path: Path) -> tuple[ServerSync, SimpleNamespace, FakeService]:
	library: dict[int, FakeTrack] = {}
	pctl = SimpleNamespace(
		master_library=library, multi_playlist=[], gen_codes={}, get_track=library.__getitem__,
		regen_in_progress=False, notify_database_changed=lambda: None)
	jellyfin = FakeService(library, JELLYFIN)
	messages: list[tuple] = []
	tauon = SimpleNamespace(
		pctl=pctl, jellyfin=jellyfin, subsonic=FakeService(library, SUBSONIC), plex=FakeService(library, PLEX),
		gui=SimpleNamespace(regen_single_id=None, request_frame=lambda: None), thread_manager=SimpleNamespace(ready=lambda _name: None),
		show_message=lambda *args, **_kwargs: messages.append(args), messages=messages)
	sync = ServerSync(tauon, tmp_path / "server_sync.json")
	# No background thread in tests
	sync.start = lambda: None
	return sync, tauon, jellyfin


def tracks(tauon: SimpleNamespace, *keys: str, ext: str = JELLYFIN) -> list[int]:
	"""Library ids for server ids, adding the tracks."""
	return [tauon.jellyfin.track_id(k) if ext == JELLYFIN else tauon.subsonic.track_id(k) for k in keys]


def keys(tauon: SimpleNamespace, ids: list[int]) -> list[str]:
	return [tauon.pctl.master_library[i].url_key for i in ids]


def linked(tmp_path: Path, server: list[str], local: list[str] | None = None) -> tuple:
	"""A playlist linked to server playlist P, synced once so both sides agree."""
	sync, tauon, jellyfin = make_sync(tmp_path)
	jellyfin.playlists["P"] = {"ids": list(server), "name": "Mix", "version": 1}
	playlist = make_playlist("Mix", tracks(tauon, *(local if local is not None else server)))
	tauon.pctl.multi_playlist.append(playlist)
	tauon.pctl.gen_codes[playlist.uuid_int] = 'jelly"P"'
	playlist.playlist_ids[:] = sync.sync_playlist(0, JELLYFIN, "P")
	jellyfin.writes.clear()
	return sync, tauon, jellyfin, playlist


def test_first_sync_takes_the_server_copy(tmp_path: Path) -> None:
	sync, tauon, jellyfin, playlist = linked(tmp_path, ["a", "b"], local=["b", "x"])
	assert keys(tauon, playlist.playlist_ids) == ["a", "b"]
	assert jellyfin.writes == []
	assert sync.links[1].base == ["a", "b"]
	assert sync.links[1].stamp == "v1"


def test_local_edit_is_sent(tmp_path: Path) -> None:
	sync, tauon, jellyfin, playlist = linked(tmp_path, ["a", "b", "c"])
	playlist.playlist_ids[:] = tracks(tauon, "c", "a", "d")
	playlist.playlist_ids[:] = sync.sync_playlist(0, JELLYFIN, "P")
	assert jellyfin.writes == [("P", ["c", "a", "d"], None)]
	assert jellyfin.playlists["P"]["ids"] == ["c", "a", "d"]
	assert keys(tauon, playlist.playlist_ids) == ["c", "a", "d"]
	assert sync.links[1].base == ["c", "a", "d"]


def test_server_edit_is_taken(tmp_path: Path) -> None:
	sync, tauon, jellyfin, playlist = linked(tmp_path, ["a", "b"])
	jellyfin.playlists["P"].update(ids=["b", "z"], version=2)
	playlist.playlist_ids[:] = sync.sync_playlist(0, JELLYFIN, "P")
	assert jellyfin.writes == []
	assert keys(tauon, playlist.playlist_ids) == ["b", "z"]


def test_edits_on_both_sides_merge(tmp_path: Path) -> None:
	sync, tauon, jellyfin, playlist = linked(tmp_path, ["a", "b", "c"])
	playlist.playlist_ids[:] = tracks(tauon, "a", "c", "l")
	jellyfin.playlists["P"].update(ids=["a", "b", "c", "r"], version=2)
	playlist.playlist_ids[:] = sync.sync_playlist(0, JELLYFIN, "P")
	assert jellyfin.playlists["P"]["ids"] == ["a", "c", "l", "r"]
	assert keys(tauon, playlist.playlist_ids) == ["a", "c", "l", "r"]


def test_local_files_stay_in_a_linked_playlist(tmp_path: Path) -> None:
	sync, tauon, jellyfin, playlist = linked(tmp_path, ["a", "b"])
	local_file = FakeTrack(500)
	tauon.pctl.master_library[500] = local_file
	playlist.playlist_ids.insert(1, 500)
	result = sync.sync_playlist(0, JELLYFIN, "P")
	# Not sent, and not dropped either
	assert jellyfin.writes == []
	assert result[1] == 500
	assert keys(tauon, [result[0], result[2]]) == ["a", "b"]


def test_renames_go_both_ways(tmp_path: Path) -> None:
	sync, _tauon, jellyfin, playlist = linked(tmp_path, ["a"])
	playlist.title = "Renamed here"
	sync.sync_playlist(0, JELLYFIN, "P")
	assert jellyfin.writes == [("P", ["a"], "Renamed here")]
	assert sync.links[1].name == "Renamed here"

	jellyfin.playlists["P"].update(name="Renamed there", version=9)
	sync.sync_playlist(0, JELLYFIN, "P")
	assert playlist.title == "Renamed there"


def test_read_only_playlist_takes_the_server_copy_and_locks(tmp_path: Path) -> None:
	sync, tauon, jellyfin, playlist = linked(tmp_path, ["a", "b"])
	jellyfin.playlists["P"]["readonly"] = True
	playlist.playlist_ids[:] = tracks(tauon, "a")
	playlist.playlist_ids[:] = sync.sync_playlist(0, JELLYFIN, "P")
	assert jellyfin.writes == []
	assert keys(tauon, playlist.playlist_ids) == ["a", "b"]
	assert playlist.locked


def test_switching_off_sending_keeps_edits_local(tmp_path: Path) -> None:
	sync, tauon, jellyfin, playlist = linked(tmp_path, ["a", "b"])
	sync.toggle_push(0)
	playlist.playlist_ids[:] = tracks(tauon, "a")
	playlist.playlist_ids[:] = sync.sync_playlist(0, JELLYFIN, "P")
	assert jellyfin.writes == []
	assert keys(tauon, playlist.playlist_ids) == ["a", "b"]


def test_failed_write_keeps_the_base_for_a_retry(tmp_path: Path) -> None:
	sync, tauon, jellyfin, playlist = linked(tmp_path, ["a", "b"])
	jellyfin.fail_write = True
	playlist.playlist_ids[:] = tracks(tauon, "b", "a")
	result = sync.sync_playlist(0, JELLYFIN, "P")
	assert keys(tauon, result) == ["b", "a"]
	assert sync.links[1].base == ["a", "b"]
	assert tauon.messages


def test_deleted_server_playlist_unlinks(tmp_path: Path) -> None:
	sync, tauon, jellyfin, playlist = linked(tmp_path, ["a"])
	del jellyfin.playlists["P"]
	assert sync.sync_playlist(0, JELLYFIN, "P") is None
	assert 1 not in sync.links
	assert 1 not in tauon.pctl.gen_codes
	assert keys(tauon, playlist.playlist_ids) == ["a"]


def test_server_duplicates_alone_are_not_an_edit(tmp_path: Path) -> None:
	sync, _tauon, jellyfin, _playlist = linked(tmp_path, ["a", "a", "b"])
	sync.sync_playlist(0, JELLYFIN, "P")
	assert jellyfin.writes == []


def test_check_edits_waits_for_edits_to_settle(tmp_path: Path) -> None:
	sync, tauon, _jellyfin, playlist = linked(tmp_path, ["a", "b"])
	sync.check_edits()
	sync.check_edits()
	# Unchanged since the sync
	assert tauon.gui.regen_single_id is None

	playlist.playlist_ids.pop()
	sync.check_edits()
	# Still settling
	assert tauon.gui.regen_single_id is None
	sync.check_edits()
	assert tauon.gui.regen_single_id == playlist.uuid_int

	# Not asked again for the same state while the first try is recent
	tauon.gui.regen_single_id = None
	sync.check_edits()
	assert tauon.gui.regen_single_id is None


def test_upload_links_a_plain_playlist(tmp_path: Path) -> None:
	sync, tauon, jellyfin = make_sync(tmp_path)
	local_file = FakeTrack(500)
	tauon.pctl.master_library[500] = local_file
	playlist = make_playlist("Road trip", [*tracks(tauon, "a", "b"), 500])
	tauon.pctl.multi_playlist.append(playlist)
	sync.upload_playlist(0)
	assert jellyfin.playlists["new0"]["ids"] == ["a", "b"]
	assert tauon.pctl.gen_codes[1] == 'jelly"new0"'
	assert sync.links[1].base == ["a", "b"]


def test_upload_of_a_smart_playlist_makes_a_copy(tmp_path: Path) -> None:
	sync, tauon, jellyfin = make_sync(tmp_path)
	playlist = make_playlist("Smart", tracks(tauon, "a"))
	tauon.pctl.multi_playlist.append(playlist)
	tauon.pctl.gen_codes[1] = "jelly rat>"
	sync.upload_playlist(0)
	assert jellyfin.playlists["new0"]["ids"] == ["a"]
	assert tauon.pctl.gen_codes[1] == "jelly rat>"
	assert 1 not in sync.links


def test_edits_coalesce_and_persist(tmp_path: Path) -> None:
	sync, tauon, _jellyfin = make_sync(tmp_path)
	track = tauon.pctl.master_library[tracks(tauon, "a")[0]]
	sync.queue_edit(track, LOVE, 1)
	sync.queue_edit(track, LOVE, 0)
	# Jellyfin has no ratings
	sync.queue_edit(track, RATING, 8)
	assert [(e.kind, e.value) for e in sync.edits] == [(LOVE, 0)]
	assert sync.pending(JELLYFIN, LOVE) == {"a"}

	again = ServerSync(tauon, sync.path)
	again.load()
	assert again.edits == sync.edits
	assert json.loads(sync.path.read_text())["version"] == 1


def test_local_tracks_are_never_queued(tmp_path: Path) -> None:
	sync, _tauon, _jellyfin = make_sync(tmp_path)
	sync.queue_edit(FakeTrack(1), LOVE, 1)
	assert sync.edits == []


def test_flush_outcomes(tmp_path: Path) -> None:
	sync, tauon, jellyfin = make_sync(tmp_path)
	first, second = (tauon.pctl.master_library[i] for i in tracks(tauon, "a", "b"))
	sync.queue_edit(first, LOVE, 1)
	sync.queue_edit(second, LOVE, 1)

	jellyfin.results = [Outcome.DROP, Outcome.RETRY]
	sync.send_due()
	# The rejected one went, the other waits with a backoff
	assert [e.server_id for e in sync.edits] == ["b"]
	assert sync.backoff.retry_at[JELLYFIN] > 0

	sync.backoff.retry_at.clear()
	sync.send_due()
	assert sync.edits == []


def test_unconfigured_service_drops_its_edits(tmp_path: Path) -> None:
	sync, tauon, jellyfin = make_sync(tmp_path)
	sync.queue_edit(tauon.pctl.master_library[tracks(tauon, "a")[0]], LOVE, 1)
	jellyfin.configured = False
	sync.send_due()
	assert sync.edits == []
	assert jellyfin.edits == []


def test_links_survive_a_restart(tmp_path: Path) -> None:
	sync, tauon, _jellyfin, _playlist = linked(tmp_path, ["a", "b"])
	sync.toggle_refresh(0)
	again = ServerSync(tauon, sync.path)
	again.load()
	assert again.links == {1: PlaylistLink(JELLYFIN, "P", ["a", "b"], "v1", "Mix")}
	assert again.no_refresh == {1}


def make_subsonic(form_post: bool) -> tuple[SubsonicService, list[tuple[str, dict, bool]]]:
	calls: list[tuple[str, dict, bool]] = []
	service = SubsonicService.__new__(SubsonicService)
	service.form_post = form_post

	def r(point: str, p: dict | None = None, post: bool = False, **_kwargs: object) -> dict:
		calls.append((point, dict(p or {}), post))
		return {"subsonic-response": {"status": "ok"}}

	service.r = r
	return service, calls


def test_subsonic_rewrite_in_one_post() -> None:
	service, calls = make_subsonic(form_post=True)
	current = RemotePlaylistState(["a", "b", "a"], [1, 2, 1], "", "Mix")
	assert service.write_remote_playlist("7", current, ["b", "c"], "New")
	assert calls == [("updatePlaylist", {
		"playlistId": "7", "songIndexToRemove": ["0", "1", "2"], "songIdToAdd": ["b", "c"], "name": "New"}, True)]


def test_subsonic_rewrite_in_chunks_without_post() -> None:
	service, calls = make_subsonic(form_post=False)
	current = RemotePlaylistState([str(i) for i in range(150)], list(range(150)), "", "Mix")
	assert service.write_remote_playlist("7", current, [f"n{i}" for i in range(120)], None)
	removes = [c[1]["songIndexToRemove"] for c in calls if "songIndexToRemove" in c[1]]
	adds = [c[1]["songIdToAdd"] for c in calls if "songIdToAdd" in c[1]]
	# From the end, so the earlier indexes stay valid
	assert removes == [[str(i) for i in range(50, 150)], [str(i) for i in range(50)]]
	assert adds == [[f"n{i}" for i in range(100)], [f"n{i}" for i in range(100, 120)]]
	assert all(not post for _point, _p, post in calls)


def test_half_written_server_copy_is_not_merged(tmp_path: Path) -> None:
	sync, tauon, jellyfin, playlist = linked(tmp_path, ["a", "b", "c"])
	playlist.playlist_ids[:] = tracks(tauon, "c", "b", "a")
	jellyfin.fail_write = True
	sync.sync_playlist(0, JELLYFIN, "P")
	assert sync.links[1].unsure
	# The failed write left the server with only part of the list
	jellyfin.playlists["P"].update(ids=["c"], version=5)
	jellyfin.fail_write = False
	playlist.playlist_ids[:] = sync.sync_playlist(0, JELLYFIN, "P")
	assert jellyfin.playlists["P"]["ids"] == ["c", "b", "a"]
	assert keys(tauon, playlist.playlist_ids) == ["c", "b", "a"]
	assert not sync.links[1].unsure


def test_first_sync_takes_the_server_name_without_renaming_it(tmp_path: Path) -> None:
	sync, tauon, jellyfin = make_sync(tmp_path)
	jellyfin.playlists["P"] = {"ids": ["a"], "name": "Server name", "version": 1}
	playlist = make_playlist("Local name", tracks(tauon, "a"))
	tauon.pctl.multi_playlist.append(playlist)
	tauon.pctl.gen_codes[1] = 'jelly"P"'
	sync.sync_playlist(0, JELLYFIN, "P")
	assert jellyfin.writes == []
	assert playlist.title == "Server name"
	assert not sync.edited(playlist, sync.links[1])


def test_unlinked_server_playlist_is_adopted_and_its_edits_sent(tmp_path: Path) -> None:
	sync, tauon, jellyfin = make_sync(tmp_path)
	jellyfin.playlists["P"] = {"ids": ["a", "b"], "name": "Mix", "version": 1}
	playlist = make_playlist("Mix", tracks(tauon, "a", "b"))
	tauon.pctl.multi_playlist.append(playlist)
	tauon.pctl.gen_codes[1] = 'jelly"P"'
	sync.check_edits()
	assert sync.links[1].base == ["a", "b"]

	playlist.playlist_ids.pop()
	playlist.playlist_ids[:] = sync.sync_playlist(0, JELLYFIN, "P")
	assert jellyfin.playlists["P"]["ids"] == ["a"]


def test_startup_refresh_skips_locked_playlists(tmp_path: Path) -> None:
	sync, tauon, _jellyfin = make_sync(tmp_path)
	locked = make_playlist("Frozen", [], uuid=1)
	locked.locked = True
	readonly = make_playlist("Smart", [], uuid=2)
	readonly.locked = True
	tauon.pctl.multi_playlist += [locked, readonly]
	tauon.pctl.gen_codes.update({1: "jelly", 2: 'jelly"S"'})
	sync.links[2] = PlaylistLink(JELLYFIN, "S", [], readonly=True)
	asked = []

	def ready(_name: str) -> None:
		asked.append(tauon.gui.regen_single_id)
		tauon.gui.regen_single_id = None

	tauon.thread_manager.ready = ready
	sync.refresh_on_start()
	assert asked == [2]


def test_queued_edits_save_once_and_caches_live_apart(tmp_path: Path) -> None:
	sync, tauon, _jellyfin = make_sync(tmp_path)
	saves = []
	original = sync.save
	sync.save = lambda: (saves.append(1), original())
	first, second = (tauon.pctl.master_library[i] for i in tracks(tauon, "a", "b"))
	sync.queue_edits([(first, LOVE, 1), (second, LOVE, 1)])
	assert len(saves) == 1

	sync.store_library("jelly", LibraryCache("", ["a", "b"], 5))
	assert "caches" not in json.loads(sync.path.read_text())
	again = ServerSync(tauon, sync.path)
	again.load()
	assert again.caches["jelly"].server_ids == ["a", "b"]


def test_stalled_lists_servers_waiting_out_a_failure(tmp_path: Path) -> None:
	sync, tauon, jellyfin = make_sync(tmp_path)
	sync.queue_edit(tauon.pctl.master_library[tracks(tauon, "a")[0]], LOVE, 1)
	jellyfin.results = [Outcome.RETRY]
	sync.send_due()
	assert sync.stalled() == ["Jellyfin"]


def test_subsonic_owner_check_ignores_case() -> None:
	service = SubsonicService.__new__(SubsonicService)
	service.prefs = SimpleNamespace(subsonic_user="Kai")
	service._song_ids = lambda entries: [1 for _e in entries]  # noqa: SLF001
	service.r = lambda *_args, **_kwargs: {"subsonic-response": {"status": "ok", "playlist": {
		"id": "1", "name": "Mix", "owner": "kai", "entry": [{"id": "s1"}]}}}
	assert not service.fetch_remote_playlist("1").readonly


def test_jellyfin_write_keeps_entries_tauon_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
	service = Jellyfin.__new__(Jellyfin)
	service.connected, service.accessToken, service.userId = True, "token", "user"
	service.prefs = SimpleNamespace(jelly_server_url="https://jellyfin.example")
	service.tauon = SimpleNamespace(t_title="Tauon", device="Test", t_version="test")
	sent: list[Any] = []
	monkeypatch.setattr(
		"tauon.t_modules.t_jellyfin.requests.post",
		lambda _url, **kwargs: (sent.append(kwargs["json"]), SimpleNamespace(status_code=204))[1])
	current = RemotePlaylistState(["a", "b"], [1, 2], "e", "Mix", kept=["video"])
	assert service.write_remote_playlist("P", current, ["b"], None)
	assert sent == [{"Ids": ["b", "video"]}]


def test_jellyfin_unfavourite_keeps_the_rest_of_the_record() -> None:
	service = Jellyfin.__new__(Jellyfin)
	stars: dict[int, StarRecord] = {7: StarRecord(playtime=30, rating=4, loved=True, hated=True)}
	service.tauon = SimpleNamespace(
		server_sync=SimpleNamespace(pending=lambda *_args: set()),
		star_store=SimpleNamespace(full_get=stars.get, insert=stars.__setitem__))
	service._set_favs({FakeTrack(7, JELLYFIN, "x"): False})  # noqa: SLF001
	assert stars[7] == StarRecord(playtime=30, rating=4, loved=False, hated=True)


def test_library_cache_belongs_to_one_server(tmp_path: Path) -> None:
	sync, _tauon, _jellyfin = make_sync(tmp_path)
	sync.store_library("jelly", LibraryCache("", ["a"], 5, server="http://old:8096|u1"))
	assert sync.library_cache("jelly", "http://old:8096|u1").server_ids == ["a"]
	assert sync.library_cache("jelly", "http://new:8096|u2") is None


def test_jellyfin_delta_counts_the_listing(monkeypatch: pytest.MonkeyPatch) -> None:
	track = FakeTrack(1, JELLYFIN, "a")
	track.album_artist = track.album = track.track_number = track.parent_folder_path = ""
	library = {1: track}
	stored: list[LibraryCache] = []
	gui = SimpleNamespace(request_frame=lambda: None, to_got=0)
	service = Jellyfin.__new__(Jellyfin)
	service.connected, service.accessToken, service.userId, service.cancel_scan = True, "token", "user", False
	service.scan_stage = ""
	service.gui = gui
	service.pctl = SimpleNamespace(master_library=library)
	service.prefs = SimpleNamespace(jelly_server_url="https://jf.example")
	service.tauon = SimpleNamespace(
		t_title="Tauon", device="Test", t_version="test", wake=lambda: None, sort_track_2=lambda *_args: None,
		server_sync=SimpleNamespace(
			pending=lambda *_args: set(), purge_removed=lambda *_args: [],
			store_library=lambda _code, cache: stored.append(cache)),
		star_store=SimpleNamespace(full_get=lambda _index: None, insert=lambda *_args: None))
	monkeypatch.setattr(service, "_server_time", lambda *_args: 100)
	counts: list[int] = []

	def get(_url: str, *, params: dict[str, Any], **_kwargs: object) -> SimpleNamespace:
		counts.append((service.scan_stage, gui.to_got))
		# The listing has the one known track, nothing changed since last time
		items = [] if "minDateLastSaved" in params else [{"Id": "a", "UserData": {"PlayCount": 4}}]
		return SimpleNamespace(status_code=200, json=lambda: {"Items": items, "TotalRecordCount": len(items)})

	monkeypatch.setattr("tauon.t_modules.t_jellyfin.requests.get", get)
	cache = LibraryCache("", ["a"], 50, server="https://jf.example|user")
	assert service._library_delta("jelly", cache, None) == [1]  # noqa: SLF001
	# The changed items are counted on their own, after the listing
	assert counts == [("", 0), (SCAN_CHANGES, 0)]
	assert gui.to_got == 1
	assert library[1].server_plays == 4
	assert stored[0].server == "https://jf.example|user"


def test_background_regenerates_are_marked(tmp_path: Path) -> None:
	sync, tauon, _jellyfin, playlist = linked(tmp_path, ["a", "b"])
	sync.check_edits()
	playlist.playlist_ids.pop()
	sync.check_edits()
	sync.check_edits()
	assert tauon.gui.regen_single_id == playlist.uuid_int
	assert playlist.uuid_int in sync.background


def test_jellyfin_parallel_listing_counts_each_page_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
	gui = SimpleNamespace(request_frame=lambda: None, to_got=0)
	service = Jellyfin.__new__(Jellyfin)
	service.accessToken, service.cancel_scan, service.scan_total = "token", False, 0
	service.gui = gui
	service.prefs = SimpleNamespace(jelly_server_url="https://jf.example")
	service.tauon = SimpleNamespace(t_title="Tauon", device="Test", t_version="test", wake=lambda: None)
	counts: list[int] = []
	service._count_page = lambda count: counts.append(count)  # noqa: SLF001
	listing = [{"Id": str(i)} for i in range(250)]

	def get(_url: str, *, params: dict[str, Any], **_kwargs: object) -> SimpleNamespace:
		start, limit = params["startIndex"], params["limit"]
		# Later pages answer first
		time.sleep(0.01 * (250 - start) / 100)
		return SimpleNamespace(
			status_code=200, json=lambda: {"Items": listing[start:start + limit], "TotalRecordCount": len(listing)})

	monkeypatch.setattr("tauon.t_modules.t_jellyfin.requests.get", get)
	assert service._parallel_items({}, 100) == listing  # noqa: SLF001
	assert sorted(counts) == [50, 100, 100]
	assert service.scan_total == 250


def test_cancelling_a_background_scan_ends_the_startup_refresh(tmp_path: Path) -> None:
	sync, tauon, _jellyfin = make_sync(tmp_path)
	# Left over from a push cancelled earlier, which shouldn't stop this refresh
	sync.refresh_cancelled = True
	tauon.pctl.multi_playlist += [make_playlist(name, [], uuid=i) for i, name in enumerate(("A", "B", "C"), 1)]
	tauon.pctl.gen_codes.update({1: "jelly", 2: 'jellylib"x"', 3: 'jellylib"y"'})
	asked = []

	def ready(_name: str) -> None:
		asked.append(tauon.gui.regen_single_id)
		tauon.gui.regen_single_id = None
		sync.refresh_cancelled = len(asked) == 2

	tauon.thread_manager.ready = ready
	sync.refresh_on_start()
	assert asked == [1, 2]


def make_login_jellyfin(monkeypatch: pytest.MonkeyPatch) -> tuple[Jellyfin, list[str], dict[str, str]]:
	"""A server where each login revokes the token before it, as Jellyfin does for one device id."""
	server = {"token": "revoked-by-another-login"}
	logins: list[str] = []
	service = Jellyfin.__new__(Jellyfin)
	service.connected, service.accessToken, service.userId, service.cancel_scan = True, "stale", "user", False
	service.scan_total = 0
	service.gui = SimpleNamespace(request_frame=lambda: None, to_got=0)
	service.prefs = SimpleNamespace(jelly_server_url="http://jf.example", jelly_username="a", jelly_password="b")
	service.tauon = SimpleNamespace(t_title="Tauon", device="Test", t_version="test", t_agent="T", wake=lambda: None)
	service.show_message = lambda *_args, **_kwargs: None

	def post(_url: str, **_kwargs: object) -> SimpleNamespace:
		logins.append("login")
		server["token"] = f"token{len(logins)}"
		return SimpleNamespace(status_code=200, json=lambda: {"AccessToken": server["token"], "User": {"Id": "user"}})

	def get(_url: str, *, headers: dict[str, str], params: dict[str, Any], **_kwargs: object) -> SimpleNamespace:
		if server["token"] not in headers["Authorization"]:
			return SimpleNamespace(status_code=401, reason="Unauthorized")
		start = params["startIndex"]
		items = [{"Id": str(start)}]
		return SimpleNamespace(status_code=200, json=lambda: {"Items": items, "TotalRecordCount": 8})

	monkeypatch.setattr("tauon.t_modules.t_jellyfin.requests.post", post)
	monkeypatch.setattr("tauon.t_modules.t_jellyfin.requests.get", get)
	return service, logins, server


def test_jellyfin_logs_in_again_once_when_its_token_was_revoked(monkeypatch: pytest.MonkeyPatch) -> None:
	service, logins, _server = make_login_jellyfin(monkeypatch)
	assert len(service._parallel_items({}, 1)) == 8  # noqa: SLF001
	assert logins == ["login"]
	assert service.accessToken == "token1"


def test_jellyfin_threads_waiting_to_log_in_share_one_login(monkeypatch: pytest.MonkeyPatch) -> None:
	service, logins, _server = make_login_jellyfin(monkeypatch)
	service.connected, service.accessToken = False, None
	service._authenticate(quiet=True)  # noqa: SLF001
	service._authenticate(quiet=True)  # noqa: SLF001
	service._relogin("an older token")  # noqa: SLF001
	assert logins == ["login"]
	assert service.connected


def test_jellyfin_ping_keeps_a_working_token(monkeypatch: pytest.MonkeyPatch) -> None:
	service, logins, server = make_login_jellyfin(monkeypatch)
	service.accessToken = server["token"]
	monkeypatch.setattr(
		"tauon.t_modules.t_jellyfin.requests.get", lambda *_args, **_kwargs: SimpleNamespace(status_code=200))
	assert service.ping()
	assert logins == []


def asks_for_sync(sync: ServerSync, tauon: SimpleNamespace) -> bool:
	"""Whether the edit check asks for a sync once things have settled."""
	sync.check_edits()
	sync.check_edits()
	asked = tauon.gui.regen_single_id is not None
	tauon.gui.regen_single_id = None
	return asked


def test_first_link_wakes_the_sync_thread(tmp_path: Path) -> None:
	sync, tauon, jellyfin = make_sync(tmp_path)
	# Nothing linked and nothing to send: the thread sleeps until woken
	assert sync._next_wake() is None
	jellyfin.playlists["P"] = {"ids": ["a"], "name": "Mix", "version": 1}
	tauon.pctl.multi_playlist.append(make_playlist("Mix", []))
	tauon.pctl.gen_codes[1] = 'jelly"P"'
	sync.wake.clear()
	sync.sync_playlist(0, JELLYFIN, "P")
	assert sync.wake.is_set()
	assert sync._next_wake() is not None


def test_renamed_read_only_playlist_is_left_alone(tmp_path: Path) -> None:
	sync, tauon, jellyfin, playlist = linked(tmp_path, ["a", "b"])
	jellyfin.playlists["P"]["readonly"] = True
	playlist.playlist_ids[:] = sync.sync_playlist(0, JELLYFIN, "P")
	playlist.title = "Mine"
	assert not asks_for_sync(sync, tauon)


def test_a_name_the_server_changes_is_not_sent_again(tmp_path: Path) -> None:
	sync, tauon, jellyfin, playlist = linked(tmp_path, ["a", "b"])
	write = jellyfin.write_remote_playlist
	jellyfin.write_remote_playlist = lambda remote_id, current, ids, name: write(
		remote_id, current, ids, name.strip() if name else name)
	playlist.title = "Renamed "
	assert asks_for_sync(sync, tauon)
	playlist.playlist_ids[:] = sync.sync_playlist(0, JELLYFIN, "P")
	assert jellyfin.playlists["P"]["name"] == "Renamed"
	assert playlist.title == "Renamed"
	assert not asks_for_sync(sync, tauon)


def test_a_sync_that_changes_nothing_is_not_repeated(tmp_path: Path) -> None:
	sync, tauon, jellyfin, playlist = linked(tmp_path, ["a", "b"])
	# A server that takes the write but keeps its own name
	write = jellyfin.write_remote_playlist
	jellyfin.write_remote_playlist = lambda remote_id, current, ids, _name: write(remote_id, current, ids, None)
	playlist.title = "Renamed"
	assert asks_for_sync(sync, tauon)
	playlist.playlist_ids[:] = sync.sync_playlist(0, JELLYFIN, "P")
	assert playlist.title == "Mix"
	assert not asks_for_sync(sync, tauon)


def test_an_edit_made_during_a_sync_is_kept(tmp_path: Path) -> None:
	sync, tauon, jellyfin, playlist = linked(tmp_path, ["a", "b"])
	jellyfin.playlists["P"]["ids"] = ["a", "b", "r"]
	added, = tracks(tauon, "x")
	fetch = jellyfin.fetch_remote_playlist

	def slow_fetch(remote_id: str) -> RemotePlaylistState | None:
		# The user drops a track in and removes one while the server answers
		if added not in playlist.playlist_ids:
			playlist.playlist_ids.append(added)
			playlist.playlist_ids.pop(0)
		return fetch(remote_id)

	jellyfin.fetch_remote_playlist = slow_fetch
	playlist.playlist_ids[:] = sync.sync_playlist(0, JELLYFIN, "P")
	assert keys(tauon, playlist.playlist_ids) == ["b", "x", "r"]
	# What the server has is what both sides agreed on, so the edit still counts as one
	assert jellyfin.playlists["P"]["ids"] == ["a", "b", "r"]
	assert asks_for_sync(sync, tauon)
	playlist.playlist_ids[:] = sync.sync_playlist(0, JELLYFIN, "P")
	assert jellyfin.playlists["P"]["ids"] == ["b", "x", "r"]


def test_background_sync_failures_are_logged_not_shown(tmp_path: Path) -> None:
	sync, tauon, jellyfin, playlist = linked(tmp_path, ["a", "b"])
	tauon.regen_background = True
	jellyfin.fetch_remote_playlist = lambda _remote_id: None
	assert sync.sync_playlist(0, JELLYFIN, "P") is None
	assert tauon.messages == []
	# Asked for by the user, it says so
	tauon.regen_background = False
	assert sync.sync_playlist(0, JELLYFIN, "P") is None
	assert tauon.messages


def make_regenerator(code: str, track_ids: list[int]):  # noqa: ANN201
	from unittest.mock import Mock

	from tauon.t_modules.t_main import PlayerCtl, Tauon

	tauon = Tauon.__new__(Tauon)
	tauon.server_sync = SimpleNamespace(background=set(), sync_playlist=Mock(return_value=[9]))
	tauon.pctl = PlayerCtl.__new__(PlayerCtl)
	tauon.pctl.multi_playlist = [SimpleNamespace(uuid_int=100, title="Mix", playlist_ids=list(track_ids))]
	tauon.pctl.gen_codes = {100: code}
	tauon.pctl.master_library = {}
	tauon.pctl.regen_in_progress = False
	tauon.pctl.notify_database_changed = Mock()
	tauon.gui = SimpleNamespace(request_tracklist_redraw=Mock(), gen_code_errors=False)
	tauon.generator_box = SimpleNamespace(active=False)
	tauon.tree_view_box = SimpleNamespace(clear_target_pl=Mock())
	tauon.reload = Mock()
	tauon.regen_background = False
	tauon.jellyfin = SimpleNamespace(scanning=False)
	tauon.subsonic = SimpleNamespace(scanning=False, last_music=None)
	tauon.plex = SimpleNamespace(scanning=False)
	tauon.prefs = SimpleNamespace(subsonic_generator_cache=False)
	return tauon


@pytest.mark.parametrize(
	("code", "service"),
	[('jelly"P"', "jellyfin"), ("jelly", "jellyfin"), ('jellylib"L"', "jellyfin"), ("jellyfav", "jellyfin"),
		("air", "subsonic"), ('airlib"3"', "subsonic"), ("plex", "plex"), ('plexlib"2"', "plex")],
)
def test_regenerating_during_a_scan_keeps_the_playlist(code: str, service: str) -> None:
	tauon = make_regenerator(code, [1, 2, 3])
	getattr(tauon, service).scanning = True
	tauon.regenerate_playlist(0)
	# Emptied, a linked playlist would then be sent to the server empty
	assert tauon.pctl.multi_playlist[0].playlist_ids == [1, 2, 3]
	assert not tauon.pctl.regen_in_progress


def test_a_regenerate_that_raises_does_not_stay_in_progress() -> None:
	tauon = make_regenerator('jelly"P"', [1, 2, 3])
	tauon.server_sync.sync_playlist.side_effect = KeyError("DateCreated")
	tauon.regen_background = True
	tauon.regenerate_playlist(0)
	assert not tauon.pctl.regen_in_progress
	assert not tauon.regen_background
	assert tauon.pctl.multi_playlist[0].playlist_ids == [1, 2, 3]


def test_a_linked_playlist_regenerates_through_the_sync() -> None:
	tauon = make_regenerator('jelly"P"', [1, 2, 3])
	tauon.regenerate_playlist(0)
	assert tauon.pctl.multi_playlist[0].playlist_ids == [9]


def test_jellyfin_playlist_fetch_logs_in_again_when_its_token_was_revoked(monkeypatch: pytest.MonkeyPatch) -> None:
	service, logins, server = make_login_jellyfin(monkeypatch)
	service.pctl = SimpleNamespace(master_library={})

	def get(url: str, *, headers: dict[str, str], **_kwargs: object) -> SimpleNamespace:
		if server["token"] not in headers["Authorization"]:
			return SimpleNamespace(status_code=401, reason="Unauthorized")
		items = [] if url.endswith("/Playlists/P/Items") else [{"Id": "P", "Name": "Mix", "Etag": "e"}]
		return SimpleNamespace(status_code=200, json=lambda: {"Items": items})

	monkeypatch.setattr("tauon.t_modules.t_jellyfin.requests.get", get)
	remote = service.fetch_remote_playlist("P")
	assert remote is not None
	assert remote.name == "Mix"
	assert logins == ["login"]


def test_jellyfin_session_reporting_survives_a_failed_report(monkeypatch: pytest.MonkeyPatch) -> None:
	import requests

	service, _logins, _server = make_login_jellyfin(monkeypatch)

	def post(_url: str, **_kwargs: object) -> SimpleNamespace:
		raise requests.ConnectionError("down")

	monkeypatch.setattr("tauon.t_modules.t_jellyfin.requests.post", post)
	assert service.session_send("Sessions/Playing", {}) is False

	# Whatever ends the thread, it can be started again
	service.session_thread_active = True
	service._session_loop = lambda: 1 / 0  # noqa: SLF001
	service.session()
	assert service.session_thread_active is False


def test_jellyfin_play_counted_at_session_start_is_not_sent_again(monkeypatch: pytest.MonkeyPatch) -> None:
	service, _logins, server = make_login_jellyfin(monkeypatch)
	service.accessToken = server["token"]
	sent: list[str] = []
	monkeypatch.setattr(
		"tauon.t_modules.t_jellyfin.requests.request",
		lambda _method, url, **_kwargs: (sent.append(url), SimpleNamespace(status_code=200))[1])
	play = SimpleNamespace(server_id="a", timestamp=1000)

	# The server counted it when the session started
	service.session_counted = ("a", 900.0)
	assert service.submit_scrobble(play) is Outcome.SENT
	assert sent == []
	# The same track played again without a new session start, such as on repeat
	assert service.submit_scrobble(play) is Outcome.SENT
	assert len(sent) == 1
	# A play from before that session, or of another track, is sent
	service.session_counted = ("a", 2000.0)
	assert service.submit_scrobble(play) is Outcome.SENT
	service.session_counted = ("b", 900.0)
	assert service.submit_scrobble(play) is Outcome.SENT
	assert len(sent) == 3


def test_plex_reorder_passes_over_a_track_the_server_did_not_take() -> None:
	from tauon.t_modules.t_main import PlexService

	class Playlist:
		key = "/playlists/7"

		def __init__(self, keys: list[str]) -> None:
			self.keys = keys

		def items(self) -> list[SimpleNamespace]:
			return [SimpleNamespace(key=k, playlistItemID=f"e{k}") for k in self.keys]

		def addItems(self, _items: list) -> None:  # noqa: N802
			# The server takes 3 and quietly drops 9
			self.keys.append("/library/metadata/3")

	playlist = Playlist(["/library/metadata/1", "/library/metadata/2"])
	moves: list[str] = []

	def query(point: str, method: object = None) -> None:
		moved, _sep, after = point.partition("/move")
		key = moved.rsplit("/e", 1)[1]
		playlist.keys.remove(key)
		anchor = after.partition("=e")[2]
		playlist.keys.insert(playlist.keys.index(anchor) + 1 if anchor else 0, key)
		moves.append(point)

	service = PlexService.__new__(PlexService)
	service.connected = True
	service.resource = SimpleNamespace(
		_session=SimpleNamespace(put="put", delete="delete"), fetchItem=lambda _key: playlist,
		fetchItems=lambda keys: keys, query=query)
	wanted = ["/library/metadata/2", "/library/metadata/9", "/library/metadata/1", "/library/metadata/3"]
	current = RemotePlaylistState(list(playlist.keys), [1, 2], "", "Mix")
	assert service.write_remote_playlist("7", current, wanted, None)
	assert playlist.keys == ["/library/metadata/2", "/library/metadata/1", "/library/metadata/3"]


def with_purge(tauon: SimpleNamespace, ids: list[int]) -> tuple[SimpleNamespace, list[int]]:
	"""Put the tracks in a playlist and give the library a purge that records what it removed."""
	playlist = SimpleNamespace(playlist_ids=list(ids))
	tauon.pctl.multi_playlist.append(playlist)
	purged: list[int] = []

	def purge_track(track_id: int) -> None:
		tauon.pctl.master_library.pop(track_id, None)
		for pl in tauon.pctl.multi_playlist:
			pl.playlist_ids[:] = [i for i in pl.playlist_ids if i != track_id]
		purged.append(track_id)

	tauon.pctl.purge_track = purge_track
	return playlist, purged


def test_a_track_missing_from_one_listing_is_kept_and_marked_as_a_suspect(tmp_path: Path) -> None:
	sync, tauon, _jellyfin = make_sync(tmp_path)
	ids = tracks(tauon, "a", "b", "c")
	playlist, purged = with_purge(tauon, ids)
	suspects = sync.purge_removed(JELLYFIN, LibraryCache("", ["a", "b", "c"]), ["a", "c"])
	assert suspects == ["b"]
	assert purged == []
	assert ids[1] in tauon.pctl.master_library
	assert ids[1] in playlist.playlist_ids


def test_a_track_missing_from_two_listings_in_a_row_is_purged(tmp_path: Path) -> None:
	sync, tauon, _jellyfin = make_sync(tmp_path)
	ids = tracks(tauon, "a", "b", "c")
	playlist, purged = with_purge(tauon, ids)
	suspects = sync.purge_removed(JELLYFIN, LibraryCache("", ["a", "b", "c"]), ["a", "c"])
	# The next listing still lacks b
	previous = LibraryCache("", ["a", "c"], extra={"suspects": suspects})
	assert sync.purge_removed(JELLYFIN, previous, ["a", "c"]) == []
	assert purged == [ids[1]]
	assert ids[1] not in tauon.pctl.master_library
	assert playlist.playlist_ids == [ids[0], ids[2]]


def test_a_suspect_that_is_listed_again_is_not_purged_and_is_cleared(tmp_path: Path) -> None:
	sync, tauon, _jellyfin = make_sync(tmp_path)
	ids = tracks(tauon, "a", "b", "c")
	playlist, purged = with_purge(tauon, ids)
	previous = LibraryCache("", ["a", "c"], extra={"suspects": ["b"]})
	assert sync.purge_removed(JELLYFIN, previous, ["a", "b", "c"]) == []
	assert purged == []
	assert playlist.playlist_ids == ids


def test_jellyfin_change_only_refresh_remembers_a_track_the_listing_lacks(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
	sync, tauon, _jellyfin = make_sync(tmp_path)
	ids = tracks(tauon, "a", "b")
	with_purge(tauon, ids)
	for index in ids:
		track = tauon.pctl.master_library[index]
		track.album_artist = track.album = track.track_number = track.parent_folder_path = ""
	stored: list[LibraryCache] = []
	service = Jellyfin.__new__(Jellyfin)
	service.connected, service.accessToken, service.userId, service.cancel_scan = True, "token", "user", False
	service.scan_stage = ""
	service.gui = SimpleNamespace(request_frame=lambda: None, to_got=0)
	service.pctl = tauon.pctl
	service.prefs = SimpleNamespace(jelly_server_url="https://jf.example")
	sync.store_library = lambda _code, cache: stored.append(cache)
	service.tauon = SimpleNamespace(
		t_title="Tauon", device="Test", t_version="test", wake=lambda: None, sort_track_2=lambda *_args: None,
		server_sync=sync, star_store=SimpleNamespace(full_get=lambda _index: None, insert=lambda *_args: None))
	monkeypatch.setattr(service, "_server_time", lambda *_args: 100)

	def get(_url: str, *, params: dict[str, Any], **_kwargs: object) -> SimpleNamespace:
		# Nothing changed, and the full listing only has a
		items = [] if "minDateLastSaved" in params else [{"Id": "a", "UserData": {"PlayCount": 0}}]
		return SimpleNamespace(status_code=200, json=lambda: {"Items": items, "TotalRecordCount": len(items)})

	monkeypatch.setattr("tauon.t_modules.t_jellyfin.requests.get", get)
	cache = LibraryCache("", ["a", "b"], 50, server="https://jf.example|user")
	service._library_delta("jelly", cache, None)  # noqa: SLF001
	assert stored[0].extra["suspects"] == ["b"]
	assert ids[1] in tauon.pctl.master_library


def test_jellyfin_stream_of_an_unreachable_server_has_no_url() -> None:
	jellyfin = Jellyfin.__new__(Jellyfin)
	jellyfin.connected = False
	jellyfin.accessToken = None
	jellyfin._authenticate = lambda: None  # noqa: SLF001
	assert jellyfin.resolve_stream("abc") == ("", None)


class BareTrack:
	art_url_key = None
	file_ext = ""
	is_network = True
	url_key = None
	parent_folder_path = ""


def audio_item(item_id: str) -> dict[str, Any]:
	return {
		"Id": item_id, "Type": "Audio", "Name": item_id,
		"MediaSources": [{"Path": f"/m/{item_id}.flac", "Size": 1, "MediaStreams": []}],
		"DateCreated": "2024-01-01T00:00:00.0000000Z",
	}


def make_favourites_jellyfin(monkeypatch: pytest.MonkeyPatch) -> Jellyfin:
	service, _logins, _server = make_login_jellyfin(monkeypatch)
	service.scanning = False
	service.scan_stage = ""
	service.lyrics_scan_checked = set()
	service.tauon.star_store = SimpleNamespace(full_get=lambda _i: None, insert=lambda *_a: None)
	service.tauon.server_sync = SimpleNamespace(pending=lambda *_a: set())
	service.tauon.sort_track_2 = lambda *_a: None
	service.tauon.TrackClass = BareTrack
	service.tauon.album_art_gen = SimpleNamespace(source_cache={})
	library: dict[int, BareTrack] = {}
	service.pctl = SimpleNamespace(master_library=library, master_count=0, get_track=library.get)
	return service


def test_jellyfin_favourite_tracks_are_unknown_when_login_fails(monkeypatch: pytest.MonkeyPatch) -> None:
	service = make_favourites_jellyfin(monkeypatch)
	service.connected, service.accessToken = False, None
	service._authenticate = lambda *_a, **_k: None  # noqa: SLF001
	assert service.favourite_tracks() is None


def test_jellyfin_favourite_albums_are_unknown_when_login_fails(monkeypatch: pytest.MonkeyPatch) -> None:
	service = make_favourites_jellyfin(monkeypatch)
	service.connected, service.accessToken = False, None
	service._authenticate = lambda *_a, **_k: None  # noqa: SLF001
	assert service.favourite_albums() is None


def test_jellyfin_favourite_tracks_are_unknown_when_the_server_is_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
	service = make_favourites_jellyfin(monkeypatch)

	def get(*_args: object, **_kwargs: object) -> None:
		raise requests.ConnectionError("down")

	monkeypatch.setattr("tauon.t_modules.t_jellyfin.requests.get", get)
	assert service.favourite_tracks() is None


def test_jellyfin_favourite_albums_are_unknown_when_one_chunk_fails(monkeypatch: pytest.MonkeyPatch) -> None:
	service = make_favourites_jellyfin(monkeypatch)
	ids = [f"a{i}" for i in range(150)]

	def get(_url: str, *, params: dict[str, Any], **_kwargs: object) -> SimpleNamespace:
		if "albumIds" not in params:
			return SimpleNamespace(status_code=200, json=lambda: {"Items": [{"Id": i} for i in ids]})
		if params["albumIds"].split(",")[0] != "a0":
			raise requests.ConnectionError("down")
		return SimpleNamespace(status_code=200, json=lambda: {"Items": [audio_item("t1")], "TotalRecordCount": 1})

	monkeypatch.setattr("tauon.t_modules.t_jellyfin.requests.get", get)
	assert service.favourite_albums() is None


def subsonic_with_albums(get_album: Callable[[str], dict[str, Any]]) -> SubsonicService:
	service = SubsonicService.__new__(SubsonicService)
	service._song_ids = lambda entries: [e["id"] for e in entries]  # noqa: SLF001

	def r(point: str, p: dict[str, Any] | None = None, **_kwargs: object) -> dict[str, Any]:
		if point == "getStarred2":
			return {"subsonic-response": {"status": "ok", "starred2": {"album": [{"id": "1"}, {"id": "2"}]}}}
		return get_album(p["id"])

	service.r = r
	return service


def album_reply(song: str) -> dict[str, Any]:
	return {"subsonic-response": {"status": "ok", "album": {"song": [{"id": song}]}}}


def test_subsonic_favourite_albums_are_unknown_when_an_album_request_fails() -> None:
	def get_album(album_id: str) -> dict[str, Any]:
		if album_id == "1":
			return album_reply("s1")
		raise requests.ConnectionError("down")

	assert subsonic_with_albums(get_album).favourite_albums() is None


def test_subsonic_favourite_albums_skip_an_album_the_server_no_longer_has() -> None:
	def get_album(album_id: str) -> dict[str, Any]:
		if album_id == "1":
			return {"subsonic-response": {"status": "failed", "error": {"code": 70, "message": "not found"}}}
		return album_reply("s2")

	assert subsonic_with_albums(get_album).favourite_albums() == ["s2"]
