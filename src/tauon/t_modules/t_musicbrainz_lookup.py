# Copyright © 2026, Tauon contributors

"""Cancellable fingerprint lookup and release previews, without writes to files or DB."""

from __future__ import annotations

import copy
import os
import re
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from contextlib import contextmanager
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import TYPE_CHECKING, ParamSpec, TypeVar
from uuid import UUID

import requests

from tauon.t_modules.t_chromaprint import Chromaprint, ChromaprintCancelledError, ChromaprintError
from tauon.t_modules.t_lookup_cache import LookupCache, cache_key
from tauon.t_modules.t_tagedit import TagChanges, file_stamp

if TYPE_CHECKING:
	from collections.abc import Callable, Iterable, Iterator

	from tauon.t_modules.t_tagedit import TagDocument, TagEditSession

# Validation details are displayed by the editor.
# ruff: noqa: TRY003

LOOKUP_LIMIT = 5


class LookupCancelledError(Exception):
	pass


class MusicBrainzLookupError(Exception):
	pass


def acoustid_application_key(override: str = "") -> str:
	"""Resolve an environment key, a user override, or Tauon's bundled application key."""
	configured = os.environ.get("TAUON_ACOUSTID_API_KEY", "").strip() or override.strip()
	if configured:
		return configured
	# Light obfuscation avoids storing the application key as a plain string.
	return bytes(value ^ 0x51 for value in (0x3E, 0x13, 0x36, 0x16, 0x66, 0x09, 0x19, 0x38, 0x62, 0x21)).decode("ascii")


@dataclass
class FileMatch:
	path: Path
	duration: float
	track_number: int = 0
	disc_number: int = 0
	recordings: dict[str, float] = field(default_factory=dict)
	error: str = ""


@dataclass
class ReleaseTrack:
	id: str
	recording_id: str
	title: str
	artists: list[str]
	artist_ids: list[str]
	credit: str
	disc: int
	number: int
	total: int
	length: float = 0


@dataclass
class AlbumCandidate:
	id: str
	title: str
	artists: list[str]
	artist_ids: list[str]
	credit: str
	date: str
	original_date: str
	country: str
	format: str
	disambiguation: str
	release_group: str
	genres: list[str]
	discs: int
	tracks: list[ReleaseTrack]
	matches: dict[Path, int] = field(default_factory=dict)
	unmatched: dict[Path, str] = field(default_factory=dict)
	confidence: float = 0
	preview_loaded: bool = True
	supported_files: int = 0
	preview_error: str = ""
	requested_id: str = ""


@dataclass
class LookupResult:
	files: list[FileMatch]
	albums: list[AlbumCandidate]
	warnings: list[str] = field(default_factory=list)
	remaining_releases: list[str] = field(default_factory=list)
	remaining_albums: list[AlbumCandidate] = field(default_factory=list)


def artist_credit(credit: list) -> tuple[list[str], list[str], str]:
	artists, ids, parts = [], [], []
	for item in credit:
		if not isinstance(item, dict):
			continue
		artist = item.get("artist", {})
		name = item.get("name") or artist.get("name", "")
		if name:
			artists.append(name)
		if artist.get("id"):
			ids.append(artist["id"])
		parts.append(name + item.get("joinphrase", ""))
	return artists, ids, "".join(parts)


def parse_album(data: dict) -> AlbumCandidate:
	artists, ids, credit = artist_credit(data.get("artist-credit", []))
	group = data.get("release-group", {})
	tracks = []
	media = data.get("media", [])
	for medium in media:
		for item in medium.get("tracks", []):
			recording = item.get("recording", {})
			track_artists, track_ids, track_credit = artist_credit(
				item.get("artist-credit") or recording.get("artist-credit") or data.get("artist-credit", [])
			)
			tracks.append(
				ReleaseTrack(
					item["id"],
					recording.get("id", ""),
					item.get("title") or recording.get("title", ""),
					track_artists,
					track_ids,
					track_credit,
					int(medium.get("position", 1)),
					int(item.get("position", 0)),
					int(medium.get("track-count", len(medium.get("tracks", [])))),
					float(item.get("length") or recording.get("length") or 0) / 1000,
				)
			)
	genres = sorted(data.get("genres") or group.get("genres") or [], key=lambda item: -int(item.get("count", 0)))
	return AlbumCandidate(
		data["id"],
		data.get("title", ""),
		artists,
		ids,
		credit,
		data.get("date", ""),
		group.get("first-release-date", ""),
		data.get("country", ""),
		" / ".join(dict.fromkeys(medium.get("format", "Unknown") for medium in media)),
		data.get("disambiguation", ""),
		group.get("id", ""),
		[item["name"] for item in genres if item.get("name") and int(item.get("count", 0)) > 0],
		max((int(medium.get("position", 1)) for medium in media), default=1),
		tracks,
	)


def match_album(album: AlbumCandidate, files: list[FileMatch]) -> None:
	"""Match recording IDs one to one; refuse indistinguishable repeat occurrences."""
	edges = {}
	for index, source in enumerate(files):
		choices = []
		for position, track in enumerate(album.tracks):
			score = source.recordings.get(track.recording_id, 0)
			if not score or (track.length and abs(track.length - source.duration) > 15):
				continue
			number_match = source.track_number == track.number and (
				not source.disc_number or source.disc_number == track.disc
			)
			length_difference = abs(track.length - source.duration) if track.length else 0
			choices.append((position, score, number_match, length_difference))
		choices.sort(key=lambda item: (-item[1], -item[2], item[3]))
		if len(choices) > 1:
			first, second = choices[:2]
			if abs(first[1] - second[1]) < 0.01 and first[2] == second[2] and abs(first[3] - second[3]) < 1:
				album.unmatched[source.path] = "Ambiguous recording or repeated album track"
				continue
		edges[index] = [choice[0] for choice in choices]
	owners = {}

	def assign(index: int, seen: set[int]) -> bool:
		for position in edges.get(index, []):
			if position in seen:
				continue
			seen.add(position)
			if position not in owners or assign(owners[position], seen):
				owners[position] = index
				return True
		return False

	for index in sorted(edges, key=lambda item: len(edges[item])):
		assign(index, set())
	album.matches = {files[index].path: position for position, index in owners.items()}
	for source in files:
		if source.path not in album.matches:
			album.unmatched.setdefault(source.path, source.error or "No unique matching track in this edition")
	album.confidence = sum(
		source.recordings[album.tracks[album.matches[source.path]].recording_id]
		for source in files
		if source.path in album.matches
	)


def _metadata_keys(doc: TagDocument) -> dict[str, str]:
	if doc.family in ("ID3", "MP4"):
		prefix = "TXXX:" if doc.family == "ID3" else "----:com.apple.iTunes:"
		keys = {
			"musicbrainz_albumid": "MusicBrainz Album Id",
			"musicbrainz_releasegroupid": "MusicBrainz Release Group Id",
			"musicbrainz_artistid": "MusicBrainz Artist Id",
			"musicbrainz_albumartistid": "MusicBrainz Album Artist Id",
			"musicbrainz_releasetrackid": "MusicBrainz Release Track Id",
			"musicbrainz_trackid": "MusicBrainz Track Id",
		}
		keys = {name: prefix + title for name, title in keys.items()}
		if doc.family == "ID3":
			keys["musicbrainz_trackid"] = "UFID:http://musicbrainz.org"
		return keys
	return {
		name: name
		for name in (
			"musicbrainz_albumid",
			"musicbrainz_releasegroupid",
			"musicbrainz_artistid",
			"musicbrainz_albumartistid",
			"musicbrainz_releasetrackid",
			"musicbrainz_trackid",
		)
	}


def stage_album(session: TagEditSession, album: AlbumCandidate) -> int:
	if not album.preview_loaded:
		raise MusicBrainzLookupError("Load this album's track preview before applying its tags.")
	changes = {}
	for doc in session.documents:
		if doc.path not in album.matches:
			continue
		track = album.tracks[album.matches[doc.path]]
		main = {
			"title": track.title,
			"album": album.title,
			"artist": track.artists,
			"albumartist": album.artists,
			"tracknumber": f"{track.number}/{track.total}",
			"discnumber": f"{track.disc}/{album.discs}",
		}
		for name, date in (("date", album.date), ("originaldate", album.original_date)):
			if re.fullmatch(r"\d{4}(?:-\d{2}(?:-\d{2})?)?", date):
				main[name] = date[:4] if doc.family == "ID3" and doc.id3_version == 3 else date
		if album.genres:
			main["genre"] = album.genres
		keys = _metadata_keys(doc)
		values = {
			"musicbrainz_albumid": album.id,
			"musicbrainz_releasegroupid": album.release_group,
			"musicbrainz_artistid": track.artist_ids,
			"musicbrainz_albumartistid": album.artist_ids,
			"musicbrainz_releasetrackid": track.id,
			"musicbrainz_trackid": track.recording_id,
		}
		entries = {keys[name]: value for name, value in values.items() if value}
		entries[doc.resolve_key("artist_credit")] = track.credit
		entries[doc.resolve_key("albumartist_credit")] = album.credit
		changes[doc.path] = TagChanges(main=main, entries=entries)
	session.stage_tracks(changes)
	return len(changes)


_RATE_LOCKS = {service: threading.Lock() for service in ("musicbrainz", "acoustid")}
_LAST_REQUEST: dict[str, float] = {}
_MB_ARGS = ParamSpec("_MB_ARGS")
_MB_RESULT = TypeVar("_MB_RESULT")


@contextmanager
def request_slot(service: str, cancel: threading.Event | None = None) -> Iterator[None]:
	"""Share pacing between editor lookups and Tauon's existing MusicBrainz searches."""
	cancel = cancel if cancel is not None else threading.Event()
	lock = _RATE_LOCKS[service]
	while not lock.acquire(timeout=0.1):
		if cancel.is_set():
			raise LookupCancelledError
	try:
		if cancel.is_set():
			raise LookupCancelledError
		interval = 0.35 if service == "acoustid" else 1.05
		if cancel.wait(max(0, _LAST_REQUEST.get(service, 0) + interval - time.monotonic())):
			raise LookupCancelledError
		_LAST_REQUEST[service] = time.monotonic()
		yield
	finally:
		lock.release()


def musicbrainz_call(
	function: Callable[_MB_ARGS, _MB_RESULT], *args: _MB_ARGS.args, **kwargs: _MB_ARGS.kwargs
) -> _MB_RESULT:
	with request_slot("musicbrainz"):
		return function(*args, **kwargs)


def retry_delay(response: requests.Response, attempt: int) -> float:
	delay = float(2 ** (attempt + 1))
	value = getattr(response, "headers", {}).get("Retry-After")
	if not isinstance(value, str):
		return delay
	try:
		seconds = float(int(value)) if value.isdigit() else parsedate_to_datetime(value).timestamp() - time.time()
	except (ValueError, TypeError, OverflowError):
		return delay
	return max(delay, seconds)


class MusicBrainzLookup:
	def __init__(
		self,
		api_key: str,
		library: str,
		version: str,
		cancel: threading.Event,
		progress: Callable[[str], None],
		*,
		ffmpeg: str | Path | None = None,
		library_dirs: Iterable[Path] = (),
		cache: LookupCache | None = None,
		progress_fraction: Callable[[float], None] | None = None,
		results_ready: Callable[[LookupResult], None] | None = None,
		decode_audio: bool = True,
	) -> None:
		api_key = acoustid_application_key(api_key)
		self.ffmpeg = shutil.which(os.path.expanduser(str(ffmpeg or "ffmpeg")))
		if decode_audio and not self.ffmpeg:
			raise MusicBrainzLookupError(
				"FFmpeg was not found. Install FFmpeg or use Tauon's FFmpeg download in the application settings."
			)
		self.chromaprint = None
		if decode_audio:
			try:
				self.chromaprint = Chromaprint(library, (*library_dirs, Path(self.ffmpeg).parent))
			except ChromaprintError as error:
				raise MusicBrainzLookupError(str(error)) from error
		self.api_key, self.cancel, self.progress = api_key.strip(), cancel, progress
		self.cache = cache
		self.progress_fraction = progress_fraction
		self.results_ready = results_ready
		self.recording_releases: dict[str, dict[str, dict]] = {}
		self.worker_stop = threading.Event()
		self.http = requests.Session()
		self.http.headers["User-Agent"] = f"TauonMusicBox/{version} (https://github.com/Taiko2k/Tauon)"

	def _check_cancel(self) -> None:
		if self.cancel.is_set() or self.worker_stop.is_set():
			raise LookupCancelledError

	def _set_progress(self, fraction: float) -> None:
		self._check_cancel()
		if self.progress_fraction is not None:
			self.progress_fraction(max(0.0, min(1.0, fraction)))

	def _request(self, service: str, endpoint: str, params: dict) -> dict:
		url = ("https://api.acoustid.org/v2/" if service == "acoustid" else "https://musicbrainz.org/ws/2/") + endpoint
		self._check_cancel()
		key = cache_key([url, params])
		if self.cache is not None:
			cached = self.cache.get("request", key)
			self._check_cancel()
			if isinstance(cached, dict):
				return cached
		for attempt in range(3):
			self._check_cancel()
			try:
				with request_slot(service, self.cancel):
					response = (
						self.http.post(url, data=params, timeout=(5, 20))
						if service == "acoustid"
						else self.http.get(url, params=params, timeout=(5, 20))
					)
				if response.status_code in (429, 503) and attempt < 2:
					self.progress(f"{service}: busy, retrying…")
					if self.cancel.wait(retry_delay(response, attempt)):
						raise LookupCancelledError
					continue
				if response.status_code != 200 and not (service == "acoustid" and response.status_code == 400):
					raise MusicBrainzLookupError(f"{service} returned HTTP {response.status_code}.")
				data = response.json()
			except (requests.RequestException, ValueError) as error:
				raise MusicBrainzLookupError(
					f"Could not contact {service}. Check your connection and retry."
				) from error
			self._check_cancel()
			if not isinstance(data, dict):
				raise MusicBrainzLookupError(f"Invalid response from {service}.")
			if (
				self.cache is not None
				and response.status_code == 200
				and "error" not in data
				and (service != "acoustid" or data.get("status") == "ok")
			):
				self.cache.put("request", key, data)
			return data
		raise MusicBrainzLookupError(f"{service} is temporarily unavailable.")

	def fingerprint(self, path: Path) -> str:
		self._check_cancel()
		if self.chromaprint is None or self.ffmpeg is None:
			raise MusicBrainzLookupError("Audio decoding is unavailable for this metadata lookup.")
		stamp, key = None, None
		if self.cache is not None:
			try:
				stamp = file_stamp(path)
				key = cache_key(["chromaprint-test2-120s-mono11025-s16le-v1", str(path.resolve()), stamp])
			except OSError:
				pass
			if key is not None:
				cached = self.cache.get("fingerprint", key)
				self._check_cancel()
				if isinstance(cached, str):
					self._check_file_stamp(path, stamp)
					self.progress(f"Using cached fingerprint: {path.name}")
					return cached
		try:
			process = subprocess.Popen(
				[
					self.ffmpeg,
					"-nostdin",
					"-hide_banner",
					"-loglevel",
					"error",
					"-i",
					str(path),
					"-map",
					"0:a:0",
					"-t",
					"120",
					"-vn",
					"-sn",
					"-dn",
					"-ac",
					"1",
					"-ar",
					"11025",
					"-acodec",
					"pcm_s16le",
					"-f",
					"s16le",
					"pipe:1",
				],
				stdin=subprocess.DEVNULL,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
			)
		except OSError as error:
			raise MusicBrainzLookupError("Could not start FFmpeg to decode this audio file.") from error
		deadline = time.monotonic() + 120
		try:
			while True:
				self._check_cancel()
				if time.monotonic() > deadline:
					raise MusicBrainzLookupError("Fingerprint scan timed out.")
				try:
					stdout, _stderr = process.communicate(timeout=0.25)
					break
				except subprocess.TimeoutExpired:
					continue
		finally:
			if process.poll() is None:
				process.kill()
				process.communicate()
		self._check_cancel()
		if process.returncode != 0:
			raise MusicBrainzLookupError("FFmpeg could not decode this audio file.")
		try:
			fingerprint = self.chromaprint.fingerprint(stdout, self.cancel)
		except ChromaprintCancelledError as error:
			raise LookupCancelledError from error
		except ChromaprintError as error:
			raise MusicBrainzLookupError(str(error)) from error
		self._check_cancel()
		if key is not None:
			self._check_file_stamp(path, stamp)
			self.cache.put("fingerprint", key, fingerprint)
		return fingerprint

	@staticmethod
	def _check_file_stamp(path: Path, stamp: tuple[int, int, int, int]) -> None:
		try:
			unchanged = file_stamp(path) == stamp
		except OSError:
			unchanged = False
		if not unchanged:
			raise MusicBrainzLookupError(f"File changed during fingerprint scan: {path.name}. Reopen the editor.")

	def _recordings(self, duration: float, fingerprint: str) -> dict[str, float]:
		data = self._request(
			"acoustid",
			"lookup",
			{
				"client": self.api_key,
				"duration": max(1, round(duration)),
				"fingerprint": fingerprint,
				"meta": "recordings releasegroups releases",
				"format": "json",
			},
		)
		if data.get("status") != "ok":
			code = data.get("error", {}).get("code")
			if code in (4, 17):
				raise MusicBrainzLookupError(
					"AcoustID rejected the application API key. Check your configuration or environment override."
				)
			raise MusicBrainzLookupError(f"AcoustID lookup failed (error {code}).")
		matches, metadata = {}, {}
		for result in data.get("results", []):
			score = float(result.get("score", 0))
			if score < 0.8:
				continue
			for recording in result.get("recordings", []):
				try:
					recording_id = str(UUID(recording["id"]))
				except (ValueError, KeyError, TypeError):
					continue
				matches[recording_id] = max(score, matches.get(recording_id, 0))
				metadata.setdefault(recording_id, {}).update(self._acoustid_releases(recording))
		best = max(matches.values(), default=0)
		matches = dict(
			sorted(((key, score) for key, score in matches.items() if score >= best - 0.05), key=lambda item: -item[1])[
				:5
			]
		)
		for recording_id in matches:
			self.recording_releases.setdefault(recording_id, {}).update(metadata[recording_id])
		return matches

	@staticmethod
	def _acoustid_releases(recording: dict) -> dict[str, dict]:
		"""Normalize AcoustID release summaries; track lists still come from MusicBrainz."""
		groups = [*recording.get("releasegroups", []), {"releases": recording.get("releases", [])}]
		releases = {}
		for group in groups:
			for release in group.get("releases", []):
				try:
					release_id = str(UUID(release["id"]))
					date = release.get("date", "")
					if isinstance(date, dict):
						date = "-".join(
							f"{int(date[key]):0{4 if key == 'year' else 2}d}"
							for key in ("year", "month", "day")
							if key in date
						)
					artists = release.get("artists") or group.get("artists") or recording.get("artists", [])
					credit = [
						{
							"artist": artist,
							"name": artist.get("name", ""),
							"joinphrase": artist.get("joinphrase", " & " if index < len(artists) - 1 else ""),
						}
						for index, artist in enumerate(artists)
					]
					releases[release_id] = {
						"id": release_id,
						"title": release.get("title") or group.get("title", ""),
						"artist-credit": credit,
						"date": date,
						"country": release.get("country", ""),
						"release-group": {"id": group.get("id", "")},
					}
				except (ValueError, KeyError, TypeError):
					continue
		return releases

	def _candidates(self, files: list[FileMatch], warnings: list[str]) -> LookupResult:
		releases, release_sources = {}, {}
		for source in files:
			for recording_id in source.recordings:
				for release_id, metadata in self.recording_releases.get(recording_id, {}).items():
					releases[release_id] = metadata
					release_sources.setdefault(release_id, set()).add(recording_id)
		albums = []
		for release_id, metadata in releases.items():
			try:
				album = parse_album(metadata)
			except (ValueError, KeyError, TypeError):
				continue
			album.preview_loaded = False
			scores = [
				max((source.recordings.get(key, 0) for key in release_sources[release_id]), default=0)
				for source in files
			]
			album.supported_files = sum(score > 0 for score in scores)
			album.confidence = sum(scores)
			albums.append(album)
		albums.sort(key=lambda album: (-album.supported_files, -album.confidence, album.date, album.id))
		return LookupResult(
			files,
			albums[:LOOKUP_LIMIT],
			list(dict.fromkeys(warnings)),
			[album.id for album in albums[LOOKUP_LIMIT:]],
			albums[LOOKUP_LIMIT:],
		)

	def _publish(self, files: list[FileMatch], warnings: list[str]) -> None:
		self._check_cancel()
		if self.results_ready is not None:
			self.results_ready(copy.deepcopy(self._candidates(files, warnings)))

	def _scan_files(self, documents: list[TagDocument]) -> list[FileMatch]:
		files = []
		for doc in documents:

			def number(name: str, document: TagDocument = doc) -> int:
				value = document.main_value(name).split("/", 1)[0]
				return int(value) if value.isdigit() else 0

			files.append(FileMatch(doc.path, float(doc.audio.info.length), number("tracknumber"), number("discnumber")))

		def scan(doc: TagDocument) -> str:
			self._check_cancel()
			doc.ensure_unchanged()
			fingerprint = self.fingerprint(doc.path)
			doc.ensure_unchanged()
			return fingerprint

		pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="tauon-fingerprint")
		futures = {index: pool.submit(scan, doc) for index, doc in enumerate(documents[:2])}
		try:
			for index, source in enumerate(files):
				self._set_progress(0.5 * index / len(files))
				self.progress(f"Fingerprinting {index + 1}/{len(files)}: {source.path.name}")
				try:
					while True:
						self._check_cancel()
						try:
							fingerprint = futures[index].result(timeout=0.1)
							break
						except FutureTimeoutError:
							if futures[index].done():
								raise
							continue
					self._set_progress(0.5 * (index + 0.7) / len(files))
					self.progress(f"Identifying {index + 1}/{len(files)}: {source.path.name}")
					if index + 2 < len(documents):
						futures[index + 2] = pool.submit(scan, documents[index + 2])
					source.recordings = self._recordings(source.duration, fingerprint)
					if not source.recordings:
						source.error = "No confident fingerprint match"
				except (MusicBrainzLookupError, ValueError) as error:
					source.error = str(error)
					if "API key" in source.error:
						raise
				finally:
					futures.pop(index)
				if index + 2 < len(documents) and index + 2 not in futures:
					futures[index + 2] = pool.submit(scan, documents[index + 2])
				self._set_progress(0.5 * (index + 1) / len(files))
				self._publish(files, [])
			return files
		finally:
			if futures:
				self.worker_stop.set()
			pool.shutdown(wait=True, cancel_futures=True)

	def run(self, documents: list[TagDocument]) -> LookupResult:
		warnings = []
		try:
			self._set_progress(0.0)
			files = self._scan_files(documents)
			self._check_cancel()
			recordings = sorted(set().union(*(source.recordings for source in files)))
			missing = [recording_id for recording_id in recordings if not self.recording_releases.get(recording_id)]
			for index, recording_id in enumerate(missing):
				self._set_progress(0.5 + 0.25 * index / len(missing))
				self.progress(f"Finding album editions {index + 1}/{len(missing)}")
				offset = 0
				for _page in range(5):
					try:
						data = self._request(
							"musicbrainz",
							"release",
							{
								"recording": recording_id,
								"inc": "artist-credits+release-groups",
								"fmt": "json",
								"limit": 100,
								"offset": offset,
							},
						)
					except MusicBrainzLookupError as error:
						warnings.append(f"Album editions for recording {recording_id}: {error}")
						break
					releases = data.get("releases", [])
					for release in releases:
						try:
							release_id = str(UUID(release["id"]))
						except (ValueError, KeyError, TypeError):
							continue
						self.recording_releases.setdefault(recording_id, {})[release_id] = release
					offset += len(releases)
					self._publish(files, warnings)
					if not releases or offset >= int(data.get("release-count", offset)):
						break
				else:
					warnings.append("Edition search limited to the first five pages for a recording.")
				self._set_progress(0.5 + 0.25 * (index + 1) / len(missing))
			result = self._candidates(files, warnings)
			self._set_progress(0.75)
			for index, album in enumerate(list(result.albums)):
				self._fill_preview(result, album.id)
				self._set_progress(0.75 + 0.25 * (index + 1) / len(result.albums))
				if self.results_ready is not None:
					self.results_ready(copy.deepcopy(result))
			self._set_progress(1.0)
			return result
		finally:
			self.http.close()

	def load_preview(self, previous: LookupResult, release_id: str) -> LookupResult:
		result = copy.deepcopy(previous)
		try:
			self._set_progress(0.0)
			self._fill_preview(result, release_id)
			self._set_progress(1.0)
			return result
		finally:
			self.http.close()

	def _fill_preview(self, result: LookupResult, release_id: str) -> None:
		self._check_cancel()
		album = next(album for album in result.albums if album.id == release_id)
		if album.preview_loaded:
			return
		self.progress(f"Loading tracks: {album.title}")
		try:
			data = self._request(
				"musicbrainz",
				"release/" + release_id,
				{
					"inc": "recordings+artist-credits+release-groups+genres",
					"fmt": "json",
				},
			)
			loaded = parse_album(data)
			loaded.requested_id = release_id
			loaded.supported_files = album.supported_files
			match_album(loaded, result.files)
			result.albums[result.albums.index(album)] = loaded
		except (MusicBrainzLookupError, ValueError, KeyError, TypeError) as error:
			album.preview_error = str(error)

	def load_more(self, previous: LookupResult) -> LookupResult:
		result = copy.deepcopy(previous)
		try:
			self._set_progress(0.0)
			result.albums.extend(result.remaining_albums[:20])
			result.remaining_albums = result.remaining_albums[20:]
			result.remaining_releases = result.remaining_releases[20:]
			self._set_progress(1.0)
			return result
		finally:
			self.http.close()
