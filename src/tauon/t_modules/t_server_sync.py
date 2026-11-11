"""Tauon Music Box - Two-way sync of playlists, loves and ratings with Jellyfin, Subsonic and Plex"""

# Copyright © 2026, Taiko2k captain(dot)gxj(at)gmail.com

#     This file is part of Tauon Music Box.
#
#     Tauon Music Box is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Tauon Music Box is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Lesser General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Tauon Music Box.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import annotations

import json
import logging
import threading
import time
from collections import Counter
from contextlib import suppress
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING

from tauon.t_modules.t_db_state import DATABASE_LOCK
from tauon.t_modules.t_extra import atomic_save
from tauon.t_modules.t_scrobble_queue import Outcome, RetryBackoff

if TYPE_CHECKING:
	from pathlib import Path

	from tauon.t_modules.t_extra import TauonPlaylist
	from tauon.t_modules.t_jellyfin import Jellyfin
	from tauon.t_modules.t_main import PlexService, Tauon, TrackClass
	from tauon.t_modules.t_subsonic import SubsonicService

SYNC_FILENAME = "server_sync.json"
# Library listings live apart, so saving a love doesn't rewrite them
CACHE_FILENAME = "server_library.json"
SYNC_VERSION = 1

# Services, named by the file_ext of their tracks
JELLYFIN = "JELY"
SUBSONIC = "SUB"
PLEX = "PLEX"
SERVICE_NAMES = {JELLYFIN: "Jellyfin", SUBSONIC: "Subsonic", PLEX: "Plex"}

# Generator code of a server playlist is prefix"<id>"
PLAYLIST_CODES = {JELLYFIN: "jelly", SUBSONIC: "air", PLEX: "plexpl"}
# Generator commands that fetch from a server
# What a scan is doing once it's past its first listing, for the activity row
SCAN_CHANGES = "changes"
SCAN_PROCESSING = "processing"
SERVER_COMMANDS = ("jelly", "air", "plex")

# Edit kinds
LOVE = "love"
RATING = "rating"


class PlaylistGoneError(Exception):
	"""The server playlist no longer exists."""


class ScanCancelledError(Exception):
	"""A library scan was cancelled from the activity popover."""


@dataclass
class ServerEdit:
	"""A love (value 0 or 1) or a rating (0 to 10) waiting to be sent to a server."""

	service: str
	server_id: str
	kind: str
	value: int


@dataclass
class RemotePlaylistState:
	"""A server playlist as just fetched."""

	server_ids: list[str]  # Entries in server order, duplicates included
	track_ids: list[int]  # Library ids for server_ids
	stamp: str  # Changes whenever the playlist does
	name: str
	readonly: bool = False
	# Entries Tauon can't hold, such as videos, which writes must keep
	kept: list[str] = field(default_factory=list)


@dataclass
class PlaylistLink:
	"""A playlist's server ids and name as both sides agreed at the last sync."""

	service: str
	remote_id: str
	base: list[str]
	stamp: str = ""
	name: str = ""
	readonly: bool = False
	# A write failed partway, so the server's copy may be half written and isn't merged from
	unsure: bool = False


@dataclass
class LibraryCache:
	"""A library listing, reused while the server reports no changes."""

	stamp: str
	server_ids: list[str]
	fetched: float = 0  # Server time the listing was taken, for asking what changed since
	extra: dict[str, object] = field(default_factory=dict)
	server: str = ""  # Server and user it came from, so switching servers doesn't reuse it


def merge_playlists[T](base: list[T], local: list[T], remote: list[T]) -> list[T]:
	"""Three-way merge of server ids, or of track ids.

	Removals from either side win, additions from both are kept, and the local order wins.
	A remote addition goes after the remote entry it follows, or at the end if it was added there.
	"""
	base_set = set(base)
	removed = (base_set - set(local)) | (base_set - set(remote))
	merged = [x for x in dict.fromkeys(local) if x not in removed]
	present = set(merged)
	# Whether anything kept comes after each remote entry
	kept_after = [False] * len(remote)
	for i in range(len(remote) - 2, -1, -1):
		kept_after[i] = kept_after[i + 1] or remote[i + 1] in present
	previous: T | None = None
	for i, x in enumerate(remote):
		if x in present:
			previous = x
			continue
		if x in base_set:
			# Removed here
			continue
		if not kept_after[i]:
			merged.append(x)
		else:
			merged.insert(merged.index(previous) + 1 if previous is not None else 0, x)
		present.add(x)
		previous = x
	return merged


def keep_foreign(local: list[int], foreign: set[int], merged: list[int]) -> list[int]:
	"""Put back tracks that can't go on the server, after the track they followed."""
	if not foreign:
		return merged
	after: dict[int | None, list[int]] = {}
	anchor: int | None = None
	for track_id in local:
		if track_id in foreign:
			after.setdefault(anchor, []).append(track_id)
		else:
			anchor = track_id
	result = after.pop(None, [])
	for track_id in merged:
		result.append(track_id)
		result.extend(after.pop(track_id, []))
	# The track they followed was removed
	for track_ids in after.values():
		result.extend(track_ids)
	return result


def parse_link(code: str | None) -> tuple[str, str] | None:
	"""The service and playlist id when a generator code is a single server playlist."""
	if not code:
		return None
	code = code.strip()
	for service, prefix in PLAYLIST_CODES.items():
		if code.startswith(prefix + '"') and code.endswith('"') and code.count('"') == 2:
			remote_id = code[len(prefix) + 1:-1]
			if remote_id:
				return service, remote_id
	return None


def uses_server(code: str | None) -> bool:
	return bool(code) and any(part.startswith(SERVER_COMMANDS) for part in code.split())


class ServerSync:
	"""Keeps loves, ratings and linked playlists in step with media servers.

	A linked playlist is one whose generator code is a single server playlist. Regenerating it
	merges both sides. A background thread sends queued edits and spots linked playlists edited
	here, which it regenerates once the edits settle.
	"""

	CHECK_INTERVAL_S = 5
	PUSH_RETRY_S = 5 * 60

	def __init__(self, tauon: Tauon, path: Path) -> None:
		self.tauon = tauon
		self.path = path
		self.cache_path = path.with_name(CACHE_FILENAME)
		self.lock = threading.RLock()
		self.edits: list[ServerEdit] = []
		self.links: dict[int, PlaylistLink] = {}
		self.caches: dict[str, LibraryCache] = {}
		# Playlist ids opted out in the tab menu
		self.no_push: set[int] = set()
		self.no_refresh: set[int] = set()
		self.on_disk: dict[str, object] | None = None
		self.wake = threading.Event()
		self.thread: threading.Thread | None = None
		self.backoff = RetryBackoff()
		# Per linked playlist: its contents at the last check, and the last state sent and when
		self.seen: dict[int, tuple[tuple[int, ...], str]] = {}
		self.tried: dict[int, tuple[tuple[tuple[int, ...], str], float]] = {}
		self.startup_pending = False
		# Playlists this asked to regenerate, so their scans show as background work
		self.background: set[int] = set()
		# Set when a background scan is cancelled, so the startup refresh doesn't carry on with the next playlist
		self.refresh_cancelled = False

	def service(self, name: str) -> Jellyfin | SubsonicService | PlexService | None:
		attribute = {JELLYFIN: "jellyfin", SUBSONIC: "subsonic", PLEX: "plex"}.get(name)
		return getattr(self.tauon, attribute) if attribute else None

	# Storage

	@staticmethod
	def _read(path: Path) -> dict | None:
		if not path.exists():
			return None
		try:
			return json.loads(path.read_text(encoding="utf-8"))
		except Exception:
			logging.exception(f"Could not read {path.name}, moving it aside")
			with suppress(OSError):
				path.replace(path.with_name(path.name + ".bad"))
			return None

	def load(self) -> None:
		data = self._read(self.path) or {}
		try:
			edits = [ServerEdit(**e) for e in data.get("edits", [])]
			links = {int(k): PlaylistLink(**v) for k, v in data.get("links", {}).items()}
			no_push = {int(x) for x in data.get("no_push", [])}
			no_refresh = {int(x) for x in data.get("no_refresh", [])}
			caches = {k: LibraryCache(**v) for k, v in (self._read(self.cache_path) or {}).get("caches", {}).items()}
		except (TypeError, ValueError, AttributeError):
			logging.exception("Malformed server sync state, starting afresh")
			return
		with self.lock:
			self.edits[:0] = edits
			self.links.update(links)
			self.caches.update(caches)
			self.no_push |= no_push
			self.no_refresh |= no_refresh
			if data:
				self.on_disk = self._payload()

	def _payload(self) -> dict[str, object]:
		return {
			"version": SYNC_VERSION,
			"edits": [asdict(e) for e in self.edits],
			"links": {str(k): asdict(v) for k, v in self.links.items()},
			"no_push": sorted(self.no_push),
			"no_refresh": sorted(self.no_refresh),
		}

	def save(self) -> None:
		with self.lock:
			payload = self._payload()
			if payload == self.on_disk:
				return
			try:
				with atomic_save(self.path, "w") as file:
					json.dump(payload, file, ensure_ascii=False)
			except OSError:
				logging.exception("Could not save the server sync state")
				return
			self.on_disk = payload

	def start(self) -> None:
		"""Start the background thread, after load()."""
		with self.lock:
			if self.thread is None:
				self.thread = threading.Thread(target=self._run, daemon=True)
				self.thread.start()
		self.wake.set()

	def _run(self) -> None:
		while True:
			self.wake.wait(self._next_wake())
			self.wake.clear()
			try:
				self.send_due()
			except Exception:
				logging.exception("Error sending server edits")
			try:
				if self.startup_pending:
					self.startup_pending = False
					self.refresh_on_start()
				self.check_edits()
			except Exception:
				logging.exception("Error checking server playlists")

	def _next_wake(self) -> float | None:
		with self.lock:
			due = [self.backoff.next_in({e.service for e in self.edits})]
			if self.links:
				due.append(self.CHECK_INTERVAL_S)
		due = [d for d in due if d is not None]
		return max(0.5, min(due)) if due else None

	# Loves and ratings

	def queue_edit(self, track: TrackClass, kind: str, value: int) -> None:
		self.queue_edits([(track, kind, value)])

	def queue_edits(self, changes: list[tuple[TrackClass, str, int]]) -> None:
		"""Queue loves or ratings to send, saving once."""
		new: list[ServerEdit] = []
		for track, kind, value in changes:
			service = track.file_ext
			if service not in SERVICE_NAMES or not track.is_network or not track.url_key:
				continue
			# Jellyfin has no ratings, Plex has no loves
			if (kind == RATING and service == JELLYFIN) or (kind == LOVE and service == PLEX):
				continue
			new.append(ServerEdit(service, track.url_key, kind, int(value)))
		if not new:
			return
		replaced = {(e.service, e.server_id, e.kind) for e in new}
		with self.lock:
			# The latest change to an item is all the server needs
			self.edits = [e for e in self.edits if (e.service, e.server_id, e.kind) not in replaced]
			self.edits.extend(new)
			self.save()
		for service in {e.service for e in new}:
			self.backoff.retry_now(service)
		self.start()

	def stalled(self) -> list[str]:
		"""Names of servers with edits waiting out a failed send."""
		with self.lock:
			services = dict.fromkeys(e.service for e in self.edits)
		return [SERVICE_NAMES[s] for s in services if self.backoff.waiting(s)]

	def pending(self, service: str, kind: str) -> set[str]:
		"""Server ids with an unsent edit, which imports leave alone so they don't undo it."""
		with self.lock:
			return {e.server_id for e in self.edits if e.service == service and e.kind == kind}

	def send_due(self) -> None:
		with self.lock:
			services = list(dict.fromkeys(e.service for e in self.edits))
		for service in services:
			if self.backoff.waiting(service):
				continue
			if self._flush(service):
				self.backoff.succeeded(service)
				continue
			delay = self.backoff.failed(service)
			self.tauon.gui.request_frame()
			logging.info(f"Unsent edits for {SERVICE_NAMES[service]}, retrying in {delay}s")

	def _flush(self, service: str) -> bool:
		"""Send one service's edits. False if some should be retried later."""
		target = self.service(service)
		if target is None or not target.sync_configured():
			with self.lock:
				dropped = [e for e in self.edits if e.service == service]
				self.edits = [e for e in self.edits if e.service != service]
				self.save()
			logging.warning(f"Dropping {len(dropped)} unsent edit(s): {SERVICE_NAMES[service]} is no longer set up")
			return True
		while True:
			with self.lock:
				edit = next((e for e in self.edits if e.service == service), None)
			if edit is None:
				return True
			try:
				result = target.push_edit(edit)
			except Exception:
				logging.exception(f"Error sending an edit to {SERVICE_NAMES[service]}")
				result = Outcome.RETRY
			if result is Outcome.RETRY:
				return False
			if result is Outcome.DROP:
				logging.warning(f"{SERVICE_NAMES[service]} rejected {edit}, dropping it")
			with self.lock:
				# By identity: a newer edit to the same item may have arrived while this one was sent
				self.edits = [e for e in self.edits if e is not edit]
				self.save()

	# Linked playlists

	def link_code(self, service: str, remote_id: str) -> str:
		return f'{PLAYLIST_CODES[service]}"{remote_id}"'

	def unlink(self, playlist_id: int) -> None:
		with self.lock:
			self.links.pop(playlist_id, None)
			self.no_push.discard(playlist_id)
			self.seen.pop(playlist_id, None)
			self.tried.pop(playlist_id, None)
			self.save()

	def sync_playlist(self, pl: int, service: str, remote_id: str) -> list[int] | None:
		"""Merge a linked playlist with the server's copy, sending local edits.

		Returns the playlist's new track ids, or None to leave it as it is.
		"""
		pctl = self.tauon.pctl
		playlist = pctl.multi_playlist[pl]
		playlist_id = playlist.uuid_int
		target = self.service(service)
		name = SERVICE_NAMES[service]
		# Edits made here while the server is being asked are put back at the end
		snapshot = list(playlist.playlist_ids)
		# Asked for by the edit check or the startup refresh, which mustn't interrupt with messages
		quiet = bool(getattr(self.tauon, "regen_background", False))

		try:
			remote = target.fetch_remote_playlist(remote_id)
		except PlaylistGoneError:
			self.unlink(playlist_id)
			pctl.gen_codes.pop(playlist_id, None)
			self.tauon.show_message(
				_("This playlist was deleted on {service}").format(service=name),
				_("It's kept here as an ordinary playlist."))
			return None
		if remote is None:
			if quiet:
				logging.warning(f"Could not fetch playlist {playlist.title} from {name}")
			else:
				self.tauon.show_message(_("Error fetching {service} playlist").format(service=name), mode="warning")
			return None

		local_tracks = [pctl.get_track(t) for t in snapshot]
		local = list(dict.fromkeys(t.url_key for t in local_tracks if t.file_ext == service and t.url_key))
		foreign = {t.index for t in local_tracks if t.file_ext != service or not t.url_key}
		known = {t.url_key: t.index for t in local_tracks if t.file_ext == service}
		known.update(zip(remote.server_ids, remote.track_ids, strict=True))
		remote_ids = list(dict.fromkeys(remote.server_ids))

		link = self.links.get(playlist_id)
		if link is None or link.service != service or link.remote_id != remote_id:
			link = self.adopt(playlist, service, remote_id)
		pushing = playlist_id not in self.no_push and not remote.readonly
		new_name = None
		if not pushing:
			merged = remote_ids
			if remote.name and remote.name != link.name:
				playlist.title = remote.name
		else:
			# After a failed write the server may hold half of it, so only the edits made here count
			merged = merge_playlists(link.base, local, link.base if link.unsure else remote_ids)
			if playlist.title not in (link.name, remote.name):
				new_name = playlist.title
			elif remote.name and remote.name != link.name:
				playlist.title = remote.name

		# Duplicates on the server aren't an edit: Tauon playlists can't hold them
		if pushing and (merged != remote_ids or new_name):
			if not target.write_remote_playlist(remote_id, remote, merged, new_name):
				if quiet:
					logging.warning(f"Could not update playlist {playlist.title} on {name}")
				else:
					self.tauon.show_message(
						_("Couldn't update the playlist on {service}").format(service=name), mode="warning")
				# The base stays put and the server's copy isn't trusted, so the next sync tries again
				with self.lock:
					link.unsure = True
					self.save()
				ids = [known[x] for x in merged if x in known]
				return self._with_later_edits(playlist, snapshot, keep_foreign(snapshot, foreign, ids))
			logging.info(f"Sent playlist {playlist.title} to {name}")
			# Fetch it back to take on whatever the server made of it, such as dropped duplicates
			with suppress(PlaylistGoneError):
				remote = target.fetch_remote_playlist(remote_id) or RemotePlaylistState(
					merged, [known[x] for x in merged if x in known], "", new_name or remote.name, remote.readonly,
					remote.kept)
			known.update(zip(remote.server_ids, remote.track_ids, strict=True))
			merged = list(dict.fromkeys(remote.server_ids))
			# The server may have changed the name it was sent, or ignored it. Its name is the
			# agreed one, or the difference would count as an edit made here for ever.
			if new_name and remote.name:
				playlist.title = remote.name

		if remote.readonly:
			playlist.locked = True
		with self.lock:
			self.links[playlist_id] = PlaylistLink(
				service, remote_id, merged, remote.stamp, remote.name or playlist.title, remote.readonly)
			self.save()
		ids = [known[x] for x in merged if x in known]
		return self._with_later_edits(playlist, snapshot, keep_foreign(snapshot, foreign, ids))

	@staticmethod
	def _with_later_edits(playlist: TauonPlaylist, snapshot: list[int], result: list[int]) -> list[int]:
		"""Carry over edits made to a playlist while it was being synced, which the next check sends."""
		current = list(playlist.playlist_ids)
		if current == snapshot:
			return result
		return merge_playlists(snapshot, current, result)

	def local_ids(self, playlist: TauonPlaylist, service: str) -> list[str]:
		"""A playlist's tracks from one server, as server ids."""
		library = self.tauon.pctl.master_library
		local = []
		for track_id in playlist.playlist_ids:
			track = library.get(track_id)
			if track is not None and track.file_ext == service and track.url_key:
				local.append(track.url_key)
		return list(dict.fromkeys(local))

	def adopt(self, playlist: TauonPlaylist, service: str, remote_id: str) -> PlaylistLink:
		"""Link a server playlist that has no sync record, taking it as it is here now as the agreed copy.

		Playlists imported before syncing existed, or whose record was lost, then keep the edits
		made here after this point.
		"""
		link = PlaylistLink(service, remote_id, self.local_ids(playlist, service), "", playlist.title)
		with self.lock:
			self.links[playlist.uuid_int] = link
			self.save()
		# The thread sleeps until woken while there's nothing linked
		self.wake.set()
		return link

	def edited(self, playlist: TauonPlaylist, link: PlaylistLink) -> bool:
		"""Whether a linked playlist differs here from how it was left at the last sync."""
		return link.unsure or playlist.title != link.name or self.local_ids(playlist, link.service) != link.base

	def check_edits(self) -> None:
		"""Regenerate linked playlists that were edited here, once the edits have settled."""
		tauon = self.tauon
		pctl = tauon.pctl
		if pctl.regen_in_progress or tauon.gui.regen_single_id is not None:
			return
		for playlist in list(pctl.multi_playlist):
			playlist_id = playlist.uuid_int
			found = parse_link(pctl.gen_codes.get(playlist_id))
			if found is None:
				continue
			link = self.links.get(playlist_id)
			if link is None or (link.service, link.remote_id) != found:
				# Not synced yet, such as one imported before syncing existed
				self.adopt(playlist, *found)
				continue
			# Nothing made here can be sent, and a read-only one takes the server's copy
			if playlist_id in self.no_push or link.readonly:
				continue
			state = (tuple(playlist.playlist_ids), playlist.title)
			last = self.seen.get(playlist_id)
			self.seen[playlist_id] = state
			# Wait until it stops changing, so a drag or a run of deletes goes as one
			if state != last or not self.edited(playlist, link):
				continue
			tried = self.tried.get(playlist_id)
			if tried and tried[0] == state and time.time() - tried[1] < self.PUSH_RETRY_S:
				continue
			self.tried[playlist_id] = (state, time.time())
			logging.info(f"Playlist {playlist.title} was edited, syncing it with {SERVICE_NAMES[link.service]}")
			self.background.add(playlist_id)
			tauon.gui.regen_single_id = playlist_id
			tauon.thread_manager.ready("worker")
			return

	def upload_service(self, pl: int) -> str | None:
		"""The set-up server that most of a playlist's tracks come from."""
		pctl = self.tauon.pctl
		counts = Counter(
			track.file_ext for track in map(pctl.get_track, pctl.multi_playlist[pl].playlist_ids)
			if track.is_network and track.file_ext in SERVICE_NAMES)
		for service, _count in counts.most_common():
			if self.service(service).sync_configured():
				return service
		return None

	def upload_playlist(self, pl: int) -> None:
		"""Create a server copy of a playlist, linking the two unless it's a smart playlist."""
		pctl = self.tauon.pctl
		service = self.upload_service(pl)
		if service is None:
			self.tauon.show_message(_("None of these tracks are from a server"))
			return
		name = SERVICE_NAMES[service]
		playlist = pctl.multi_playlist[pl]
		tracks = [pctl.get_track(t) for t in playlist.playlist_ids]
		server_ids = list(dict.fromkeys(t.url_key for t in tracks if t.file_ext == service and t.url_key))
		skipped = len({t.index for t in tracks if t.file_ext != service})
		target = self.service(service)

		remote_id = target.create_remote_playlist(playlist.title, server_ids)
		if remote_id is None:
			self.tauon.show_message(_("Couldn't create the playlist on {service}").format(service=name), mode="warning")
			return
		note = _("{N} tracks from elsewhere were left out").format(N=skipped) if skipped else ""
		if pctl.gen_codes.get(playlist.uuid_int):
			self.tauon.show_message(
				_("Uploaded a copy to {service}").format(service=name),
				_("It's a smart playlist, so later changes stay here.") + (" " + note if note else ""), mode="done")
			return
		try:
			remote = target.fetch_remote_playlist(remote_id)
		except PlaylistGoneError:
			remote = None
		with self.lock:
			pctl.gen_codes[playlist.uuid_int] = self.link_code(service, remote_id)
			base = list(dict.fromkeys(remote.server_ids)) if remote else server_ids
			self.links[playlist.uuid_int] = PlaylistLink(
				service, remote_id, base, remote.stamp if remote else "", (remote and remote.name) or playlist.title)
			self.save()
		self.start()
		self.tauon.show_message(
			_("Uploaded to {service}").format(service=name),
			note or _("Edits made here are sent to the server."), mode="done")

	def toggle_push(self, pl: int) -> None:
		playlist_id = self.tauon.pctl.multi_playlist[pl].uuid_int
		with self.lock:
			if playlist_id in self.no_push:
				self.no_push.discard(playlist_id)
				# Changes made while it was off are pushed by the next check
				self.tried.pop(playlist_id, None)
			else:
				self.no_push.add(playlist_id)
			self.save()

	def toggle_refresh(self, pl: int) -> None:
		playlist_id = self.tauon.pctl.multi_playlist[pl].uuid_int
		with self.lock:
			self.no_refresh ^= {playlist_id}
			self.save()

	def is_linked(self, pl: int) -> bool:
		pctl = self.tauon.pctl
		playlist_id = pctl.multi_playlist[pl].uuid_int
		return parse_link(pctl.gen_codes.get(playlist_id)) is not None

	# Library listings

	def library_cache(self, code: str, server: str) -> LibraryCache | None:
		"""The last listing for a code, if it came from this server and user."""
		with self.lock:
			cache = self.caches.get(code)
		return cache if cache is not None and cache.server == server else None

	def store_library(self, code: str, cache: LibraryCache) -> None:
		with self.lock:
			self.caches[code] = cache
			try:
				with atomic_save(self.cache_path, "w") as file:
					json.dump({"version": SYNC_VERSION, "caches": {k: asdict(v) for k, v in self.caches.items()}}, file)
			except OSError:
				logging.exception("Could not save the server library listings")

	def library_ids(self, service: str, server_ids: list[str]) -> list[int] | None:
		"""Library ids for server ids, or None if any are missing from the library."""
		existing = {
			track.url_key: track_id for track_id, track in self.tauon.pctl.master_library.items()
			if track.file_ext == service and track.is_network}
		try:
			return [existing[x] for x in server_ids]
		except KeyError:
			return None

	def purge_removed(self, service: str, cache: LibraryCache, new: list[str]) -> list[str]:
		"""Drop tracks that have been missing from two full listings in a row.

		One listing can miss a track that is still on the server, such as when the server's order
		shifts between pages during a rescan. A purge takes the track out of every playlist, and
		from a linked one that goes on to the server. Returns the tracks missing for the first
		time, for the new cache to remember in extra["suspects"].
		"""
		listed = set(new)
		suspects = [x for x in dict.fromkeys(cache.server_ids) if x not in listed]
		previous = cache.extra.get("suspects") if isinstance(cache.extra, dict) else None
		gone = {x for x in previous if x not in listed} if isinstance(previous, list) else set()
		if not gone:
			return suspects
		pctl = self.tauon.pctl
		with DATABASE_LOCK:
			track_ids = [
				track_id for track_id, track in pctl.master_library.items()
				if track.file_ext == service and track.is_network and track.url_key in gone]
			for track_id in track_ids:
				pctl.purge_track(track_id)
		if track_ids:
			logging.info(f"Removed {len(track_ids)} tracks that are no longer on {SERVICE_NAMES[service]}")
			pctl.notify_database_changed()
		return suspects

	# Startup refresh

	def refresh_on_start(self) -> None:
		"""Regenerate server playlists in turn, skipping servers that can't be reached."""
		tauon = self.tauon
		pctl = tauon.pctl
		reachable: dict[str, bool] = {}
		self.refresh_cancelled = False
		for playlist in list(pctl.multi_playlist):
			playlist_id = playlist.uuid_int
			code = pctl.gen_codes.get(playlist_id)
			if not uses_server(code) or playlist_id in self.no_refresh:
				continue
			# Locked by the user. Read-only server playlists are locked here too, and still follow the server.
			link = self.links.get(playlist_id)
			if playlist.locked and not (link and link.readonly):
				continue
			parts = code.split()
			wanted = [
				service for command, service in zip(SERVER_COMMANDS, (JELLYFIN, SUBSONIC, PLEX), strict=True)
				if any(part.startswith(command) for part in parts)]
			ok = True
			for service in wanted:
				if service not in reachable:
					target = self.service(service)
					reachable[service] = bool(target.sync_configured()) and bool(target.ping())
				ok = ok and reachable[service]
			if not ok:
				continue
			while pctl.regen_in_progress or tauon.gui.regen_single_id is not None:
				time.sleep(0.5)
			if self.refresh_cancelled:
				logging.info("Startup refresh of server playlists cancelled")
				break
			logging.info(f"Refreshing server playlist {playlist.title}")
			self.background.add(playlist_id)
			tauon.gui.regen_single_id = playlist_id
			tauon.thread_manager.ready("worker")
			time.sleep(0.5)
		# Don't treat the refreshed contents as edits made here
		self.seen.clear()
