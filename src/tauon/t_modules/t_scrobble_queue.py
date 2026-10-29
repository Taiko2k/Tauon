"""Scrobbles waiting to be sent, optionally kept on disk so they survive offline spells and restarts."""

# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

from __future__ import annotations

import json
import logging
import threading
from contextlib import suppress
from dataclasses import asdict, dataclass, field, fields
from enum import Enum, auto
from typing import TYPE_CHECKING

from tauon.t_modules.t_extra import atomic_save, get_artist_strip_feat

if TYPE_CHECKING:
	from collections.abc import Iterable, Iterator
	from pathlib import Path

	from tauon.t_modules.t_main import TrackClass

QUEUE_FILENAME = "scrobble_queue.json"
QUEUE_VERSION = 1

# Service tags
LASTFM = "lfm"
LIBREFM = "libre"
LISTENBRAINZ = "lb"
MALOJA = "maloja"
SUBSONIC = "air"

SERVICE_NAMES = {
	LASTFM: "Last.fm", LIBREFM: "Libre.fm", LISTENBRAINZ: "ListenBrainz", MALOJA: "Maloja", SUBSONIC: "Subsonic"}


class Outcome(Enum):
	SENT = auto()
	RETRY = auto()  # Offline, server trouble, rate limited or a credentials problem
	DROP = auto()  # The service will never accept it


@dataclass
class PendingScrobble:
	"""One play waiting for one service, as plain data so it outlives the library entry."""

	service: str
	timestamp: int  # When it was played, unix seconds
	artist: str
	title: str
	album: str = ""
	album_artist: str = ""
	duration: int = 0
	track_number: str = ""
	artist_mbids: list[str] = field(default_factory=list)
	release_mbid: str = ""
	recording_mbid: str = ""
	track_mbid: str = ""
	server_id: str = ""  # Subsonic song id
	track_id: int | None = None  # Library index, for syncing loves after sending
	saved: bool = field(default=False, compare=False, repr=False)  # Mirrored to disk

	def to_dict(self) -> dict[str, object]:
		data = asdict(self)
		del data["saved"]
		return data

	@classmethod
	def from_dict(cls, data: dict[str, object]) -> PendingScrobble:
		known = {f.name for f in fields(cls)} - {"saved"}
		item = cls(**{key: value for key, value in data.items() if key in known})
		if not isinstance(item.service, str) or not isinstance(item.artist, str) or not isinstance(item.title, str):
			raise TypeError
		item.timestamp = int(item.timestamp)
		return item


def pending_from_track(track: TrackClass, service: str, timestamp: int) -> PendingScrobble:
	# Maloja splits artists itself, the others want the main one
	artist = track.artist if service == MALOJA else get_artist_strip_feat(track)
	artist_ids = track.musicbrainz_artistids
	return PendingScrobble(
		service=service,
		timestamp=timestamp,
		artist=artist or "",
		title=track.title or "",
		album=track.album or "",
		album_artist=track.album_artist or "",
		duration=int(track.length or 0),
		track_number=str(track.track_number or ""),
		artist_mbids=[artist_ids] if isinstance(artist_ids, str) else list(artist_ids or []),
		release_mbid=track.musicbrainz_albumid or "",
		recording_mbid=track.musicbrainz_recordingid or "",
		track_mbid=track.musicbrainz_trackid or "",
		server_id=track.url_key if service == SUBSONIC else "",
		track_id=track.index,
	)


def track_number_int(text: str) -> int | None:
	"""Leading number of a tag like "3" or "3/12"."""
	try:
		return int(text.split("/", 1)[0])
	except ValueError:
		return None


def http_outcome(status: int) -> Outcome:
	if 200 <= status < 300:
		return Outcome.SENT
	if status in (401, 403, 408, 429) or status >= 500:
		return Outcome.RETRY
	return Outcome.DROP


class ScrobbleQueue:
	"""Thread-safe list of pending scrobbles. Items marked saved are mirrored to disk on every change."""

	def __init__(self, path: Path) -> None:
		self.path = path
		self.lock = threading.RLock()
		self.items: list[PendingScrobble] = []
		self.on_disk: list[dict[str, object]] = []

	def __len__(self) -> int:
		return len(self.items)

	def __iter__(self) -> Iterator[PendingScrobble]:
		with self.lock:
			return iter(list(self.items))

	def load(self) -> None:
		"""Merge in scrobbles saved by an earlier session."""
		if not self.path.exists():
			return
		try:
			entries = json.loads(self.path.read_text(encoding="utf-8"))["scrobbles"]
		except Exception:
			logging.exception("Could not read the scrobble queue, moving it aside")
			with suppress(OSError):
				self.path.replace(self.path.with_name(self.path.name + ".bad"))
			return

		loaded: list[PendingScrobble] = []
		for entry in entries:
			try:
				item = PendingScrobble.from_dict(entry)
			except (TypeError, ValueError, AttributeError):
				logging.warning(f"Skipping a malformed queued scrobble: {entry!r}")
				continue
			item.saved = True
			loaded.append(item)

		with self.lock:
			present = {(item.service, item.timestamp, item.artist, item.title) for item in self.items}
			self.items[:0] = [item for item in loaded if (item.service, item.timestamp, item.artist, item.title) not in present]
			self.on_disk = entries
			self.save()
		if loaded:
			logging.info(f"Loaded {len(loaded)} unsent scrobbles")

	def save(self) -> None:
		with self.lock:
			payload = [item.to_dict() for item in self.items if item.saved]
			if payload == self.on_disk:
				return
			try:
				with atomic_save(self.path, "w") as file:
					json.dump({"version": QUEUE_VERSION, "scrobbles": payload}, file, ensure_ascii=False)
			except OSError:
				logging.exception("Could not save the scrobble queue")
				return
			self.on_disk = payload

	def add(self, item: PendingScrobble, keep: bool) -> None:
		with self.lock:
			item.saved = keep
			self.items.append(item)
			self.save()

	def pending(self, service: str, limit: int | None = None) -> list[PendingScrobble]:
		"""The oldest scrobbles waiting for one service."""
		with self.lock:
			return [item for item in self.items if item.service == service][:limit]

	def services(self) -> list[str]:
		with self.lock:
			return list(dict.fromkeys(item.service for item in self.items))

	def counts(self) -> dict[str, int]:
		with self.lock:
			counts: dict[str, int] = {}
			for item in self.items:
				counts[item.service] = counts.get(item.service, 0) + 1
			return counts

	def remove(self, done: Iterable[PendingScrobble]) -> None:
		done_ids = {id(item) for item in done}
		if not done_ids:
			return
		with self.lock:
			self.items = [item for item in self.items if id(item) not in done_ids]
			self.save()

	def clear(self) -> None:
		with self.lock:
			self.items.clear()
			self.save()

	def keep_all(self) -> None:
		"""Save everything waiting, for when the setting is switched on."""
		with self.lock:
			for item in self.items:
				item.saved = True
			self.save()
