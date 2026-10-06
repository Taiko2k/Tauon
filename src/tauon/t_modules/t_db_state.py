# Copyright © 2026, Tauon contributors
"""Synchronization and reference repair for the music database."""

from __future__ import annotations

import copy
import logging
import threading
from dataclasses import asdict
from functools import wraps
from typing import TYPE_CHECKING, ParamSpec, TypeVar

from tauon.t_modules.t_extra import atomic_save

if TYPE_CHECKING:
	from collections.abc import Callable
	from pathlib import Path

	from tauon.t_modules.t_main import PlayerCtl, QueueBox

DATABASE_LOCK = threading.RLock()
STATE_SAVE_LOCK = threading.RLock()
P = ParamSpec("P")
R = TypeVar("R")


def database_write(function: Callable[P, R]) -> Callable[P, R]:
	"""Serialize multi-step mutations with state snapshot capture."""

	@wraps(function)
	def locked(*args: P.args, **kwargs: P.kwargs) -> R:
		with DATABASE_LOCK:
			return function(*args, **kwargs)

	return locked


def state_save(function: Callable[P, R]) -> Callable[P, R]:
	"""Prevent concurrent saves from sharing the same temporary file."""

	@wraps(function)
	def locked(*args: P.args, **kwargs: P.kwargs) -> R:
		with STATE_SAVE_LOCK:
			return function(*args, **kwargs)

	return locked


def allocate_track_id(pctl: PlayerCtl) -> int:
	"""Reserve an ID before scanning, without locking file or network I/O."""
	with DATABASE_LOCK:
		track_id = pctl.master_count
		pctl.master_count += 1
		return track_id


def snapshot_database(pctl: PlayerCtl, queue_box: QueueBox) -> tuple[dict[int, object], dict]:
	"""Detach references before capturing library membership.

	Atomic imports publish the library entry before publishing its ID. Removals
	and ID allocation take DATABASE_LOCK; ordinary readers do not.
	"""
	with DATABASE_LOCK, queue_box.auto_queue_lock:
		state = {
			2: pctl.playlist_playing_position,
			3: pctl.active_playlist_viewing,
			4: pctl.playlist_view_position,
			5: [copy.deepcopy(playlist.__dict__) for playlist in pctl.multi_playlist],
			7: pctl.track_queue[:],
			8: pctl.queue_step,
			9: pctl.default_playlist[:],
			23: pctl.selected_in_playlist,
			90: [asdict(item) for item in pctl.force_queue],
			165: [copy.deepcopy(playlist.__dict__) for playlist in pctl.radio_playlists],
			166: pctl.radio_playlist_viewing,
			183: pctl.active_playlist_playing,
		}
		auto_queue = queue_box.auto_queue_state()
		tracks = list(pctl.master_library.values())
		state[1] = pctl.master_count
	# Keep removed track objects alive until their captured references are saved.
	mutable = (dict, list, set, tuple)
	records = []
	for track in tracks:
		record = {}
		for name in track.__slots__:
			value = getattr(track, name)
			record[name] = copy.deepcopy(value) if isinstance(value, mutable) else value
		records.append(record)
	state[162] = records
	return state, auto_queue


def backup_state_before_repair(user_directory: Path) -> None:
	"""Keep the original state files when upgrading to database version 80."""
	for name in ("state.p", "state.p.backup"):
		source = user_directory / name
		backup = user_directory / f"{name}.bak80"
		if source.is_file() and not backup.exists():
			with atomic_save(backup) as file:
				file.write(source.read_bytes())


def repaired_position(ids: list[int], valid: set[int], position: int, *, empty: int = -1) -> int:
	"""Retain the selected occurrence when preceding missing IDs are removed."""
	if position < 0:
		return empty
	count = sum(track_id in valid for track_id in ids)
	if not count:
		return empty
	return min(sum(track_id in valid for track_id in ids[:position]), count - 1)


@database_write
def validate_and_repair_database(pctl: PlayerCtl) -> int:
	"""Remove dangling references, retaining valid duplicates and offline tracks."""
	valid = set(pctl.master_library)
	removed = 0
	positions = {}
	for index, playlist in enumerate(pctl.multi_playlist):
		ids = playlist.playlist_ids[:]
		positions[playlist.uuid_int] = ids
		playlist.selected = repaired_position(ids, valid, playlist.selected)
		playlist.position = repaired_position(ids, valid, playlist.position, empty=0)
		if index == pctl.active_playlist_viewing:
			playlist.selected = repaired_position(ids, valid, pctl.selected_in_playlist)
			playlist.position = repaired_position(ids, valid, pctl.playlist_view_position, empty=0)
		if index == pctl.active_playlist_playing:
			pctl.playlist_playing_position = repaired_position(ids, valid, pctl.playlist_playing_position)
		playlist.playlist_ids[:] = [track_id for track_id in ids if track_id in valid]
		removed += len(ids) - len(playlist.playlist_ids)

	ids = pctl.track_queue[:]
	current_missing = bool(ids) and (not 0 <= pctl.queue_step < len(ids) or ids[pctl.queue_step] not in valid)
	pctl.queue_step = repaired_position(ids, valid, pctl.queue_step, empty=0)
	pctl.track_queue[:] = [track_id for track_id in ids if track_id in valid]
	removed += len(ids) - len(pctl.track_queue)
	if current_missing:
		pctl.prefs.reload_state = None

	queue = []
	for item in pctl.force_queue:
		for entry in [item, *(item.tracks or [])]:
			ids = positions.get(entry.playlist_id)
			if ids is not None:
				entry.position = repaired_position(ids, valid, entry.position, empty=0)
		if item.tracks is not None:
			children = item.tracks
			item.tracks = [child for child in children if child.track_id in valid]
			removed += len(children) - len(item.tracks)
			if not item.tracks:
				removed += 1
				continue
			if item.track_id not in valid:
				item.track_id = item.tracks[0].track_id
				item.position = item.tracks[0].position
		elif item.track_id not in valid:
			removed += 1
			continue
		queue.append(item)
	pctl.force_queue[:] = queue

	if pctl.multi_playlist:
		last = len(pctl.multi_playlist) - 1
		pctl.active_playlist_viewing = max(0, min(pctl.active_playlist_viewing, last))
		pctl.active_playlist_playing = max(0, min(pctl.active_playlist_playing, last))
		playing_ids = pctl.multi_playlist[pctl.active_playlist_playing].playlist_ids
		pctl.playlist_playing_position = max(-1, min(pctl.playlist_playing_position, len(playing_ids) - 1))
		playlist = pctl.multi_playlist[pctl.active_playlist_viewing]
		pctl.default_playlist = playlist.playlist_ids
		pctl.selected_in_playlist = playlist.selected
		pctl.playlist_view_position = playlist.position
	else:
		pctl.default_playlist = []
		pctl.selected_in_playlist = -1
		pctl.playlist_view_position = 0
	pctl.master_count = max(pctl.master_count, max(valid, default=-1) + 1)
	pctl.shuffle_pools.clear()
	pctl.album_dex.clear()
	if removed:
		pctl.queue_box.auto_queue_position = None
		pctl.queue_box.auto_queue_playing = None
	logging.warning("Database repair removed %s missing track references", removed)
	return removed
