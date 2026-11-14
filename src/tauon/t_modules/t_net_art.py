# Copyright © 2026, Taiko2k captain(dot)gxj(at)gmail.com

"""Network artwork downloads.

Each image is downloaded once, however many places want it at the same time,
and saved to the network art cache. The next track's art can also be fetched
ahead, once the playing track's audio is buffered enough. Art wanted on screen
goes first, and a prefetch that is no longer wanted is called off.
"""
from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
import urllib.error
from typing import TYPE_CHECKING, Any

import requests

if TYPE_CHECKING:
	from collections.abc import Callable, Iterable

	from tauon.t_modules.t_main import TrackClass

# How long a failure holds off another try: a missing image, an unreachable server
IMAGE_RETRY_S = 120
SERVER_RETRY_S = 60
MAX_ART_BYTES = 64 * 1000 * 1000

NETWORK_ERRORS = (requests.ConnectionError, requests.Timeout, urllib.error.URLError, TimeoutError)

# fetch() result while a download is still going
PENDING: Any = object()


class FetchCancelled(Exception):  # noqa: N818
	"""A prefetch was called off"""


def read_body(response: requests.Response, cancelled: Callable[[], bool] | None = None, chunk_size: int = 65536) -> bytes:
	"""Read a streamed response, stopping between chunks if cancelled"""
	buf = bytearray()
	for chunk in response.iter_content(chunk_size):
		if cancelled is not None and cancelled():
			raise FetchCancelled
		buf += chunk
		if len(buf) > MAX_ART_BYTES:
			raise ValueError("Artwork too large")
	return bytes(buf)


def wants_net_art(track: TrackClass | None) -> bool:
	"""Whether track's art comes from the network art cache"""
	return bool(
		track is not None and getattr(track, "is_network", False)
		and getattr(track, "art_url_key", "") and getattr(track, "file_ext", "") != "RADIO")


class _Job:
	__slots__ = ("cancel", "cancelled", "done", "key", "prefetch", "result", "spawned", "title")

	def __init__(self, key: str, prefetch: bool, title: str) -> None:
		self.key = key
		self.prefetch = prefetch  # only a prefetch can be called off
		self.spawned = False  # started by a non-blocking fetch (the UI thread)
		self.cancel: str = ""  # why it's being called off
		self.cancelled = False
		self.done = threading.Event()
		self.result: str | None = None
		self.title = title


class NetArtFetcher:
	MAX_SPAWNED = 2  # downloads non-blocking fetches may have going at once

	def __init__(
		self, cache_dir: str, download: Callable[[TrackClass, Callable[[], bool]], bytes | None],
		on_ready: Callable[[], None] | None = None,
	) -> None:
		"""download(track, cancelled) returns the image bytes, or None if the server has none.
		It should check cancelled() as it reads, raising FetchCancelled (read_body does)."""
		self.cache_dir = cache_dir
		self.download = download
		self.on_ready = on_ready
		self.lock = threading.Lock()
		self.jobs: dict[str, _Job] = {}
		self.failed: dict[str, float] = {}  # art key -> when it last failed
		self.server_failed: dict[str, float] = {}  # file_ext -> when it last couldn't be reached
		# Prefetch of the next track's art
		self.target: TrackClass | None = None
		self.gate_open = False  # the playing track's audio is buffered enough
		self.prefetch_job: _Job | None = None

	def cache_path(self, key: str) -> str:
		return os.path.join(self.cache_dir, hashlib.md5(key.encode()).hexdigest()[:12])

	@staticmethod
	def _title(track: TrackClass) -> str:
		return getattr(track, "title", "") or getattr(track, "art_url_key", "?")

	def _held_off(self, track: TrackClass) -> bool:
		"""A recent failure means not trying again yet. Call with the lock held."""
		now = time.monotonic()
		t = self.failed.get(track.art_url_key)
		if t is not None and now - t < IMAGE_RETRY_S:
			return True
		t = self.server_failed.get(track.file_ext)
		return t is not None and now - t < SERVER_RETRY_S

	def _cancel_prefetch(self, keep: str | None, reason: str) -> None:
		"""Call off the prefetch unless it's for keep. Call with the lock held."""
		job = self.prefetch_job
		if job is not None and job.prefetch and job.key != keep and not job.cancel:
			job.cancel = reason

	def fetch(self, track: TrackClass, block: bool = True, grace: float = 0.0) -> str | None:
		"""Path of track's cached art, downloading it if needed, or None if there is none.

		A download of it already going is joined rather than started again. block=False
		is for the UI thread: the download runs on a thread, waited on for up to grace
		seconds when it's started here, and PENDING is returned while it's going.
		"""
		key = track.art_url_key
		path = self.cache_path(key)
		while True:
			with self.lock:
				if os.path.isfile(path):
					return path
				job = self.jobs.get(key)
				started = job is None
				if job is not None:
					if job.prefetch:
						job.prefetch = False  # wanted on screen now, so it can't be called off
						logging.info(f"Art prefetch: '{job.title}' now wanted on screen, carrying on")
				else:
					if self._held_off(track):
						return None
					# Fast skipping mustn't start a download per track from the UI thread;
					# ask again on a later frame once one is done
					if not block and sum(j.spawned for j in self.jobs.values()) >= self.MAX_SPAWNED:
						return PENDING
					job = _Job(key, False, self._title(track))
					job.spawned = not block
					self.jobs[key] = job
					self._cancel_prefetch(key, "art on screen first")
			if started and block:
				self._run(job, track)
			elif started:
				self._spawn(job, track)
			if block:
				job.done.wait()
			else:
				if started and grace > 0:
					job.done.wait(grace)
				if not job.done.is_set() or job.cancelled:
					return PENDING
			if job.cancelled:
				continue  # called off just before we joined it; fetch it ourselves
			return job.result

	def _spawn(self, job: _Job, track: TrackClass) -> None:
		shoot = threading.Thread(target=self._run, args=(job, track), name="net-art")
		shoot.daemon = True
		shoot.start()

	def _should_stop(self, job: _Job) -> bool:
		with self.lock:
			return bool(job.cancel) and job.prefetch

	def _run(self, job: _Job, track: TrackClass) -> None:
		path = self.cache_path(job.key)
		server_down = False
		try:
			data = self.download(track, lambda: self._should_stop(job))
			if data:
				temp = path + ".part"
				with open(temp, "wb") as f:
					f.write(data)
				os.replace(temp, path)  # never seen half written
				job.result = path
		except FetchCancelled:
			job.cancelled = True
		except Exception as e:
			if isinstance(e, NETWORK_ERRORS):
				# The server, not just this image: hold off the rest of its artwork for a while
				logging.warning(f"Couldn't reach the server for artwork, trying again later: {e}")
				server_down = True
			else:
				logging.exception(f"Failed to download artwork for '{job.title}'")
		finally:
			with self.lock:
				now = time.monotonic()
				if job.result:
					self.failed.pop(job.key, None)
					self.server_failed.pop(track.file_ext, None)
				elif not job.cancelled:
					self.failed[job.key] = now
					if server_down:
						self.server_failed[track.file_ext] = now
				if self.jobs.get(job.key) is job:
					del self.jobs[job.key]
				if self.prefetch_job is job:
					self.prefetch_job = None
				was_prefetch = job.prefetch
			if was_prefetch:
				if job.cancelled:
					logging.info(f"Art prefetch: stopped '{job.title}' ({job.cancel})")
				elif job.result:
					logging.info(f"Art prefetch: ready '{job.title}'")
			job.done.set()
			# A spawned job's end also frees a slot something may be waiting on
			if (job.result or job.spawned) and self.on_ready is not None:
				self.on_ready()
			self._try_prefetch()

	# Prefetch

	def set_prefetch(self, target: TrackClass | None, needed: Iterable[TrackClass | None] = ()) -> None:
		"""Set the track whose art to fetch ahead, once open_gate() says the audio
		allows it. needed: tracks whose art is wanted now (the one playing, the one
		opening), so a prefetch of it carries on. Any other prefetch is called off."""
		keep = {t.art_url_key for t in needed if wants_net_art(t)}
		if not wants_net_art(target):
			target = None
		with self.lock:
			job = self.prefetch_job
			if job is not None and job.prefetch and job.key in keep:
				job.prefetch = False  # it's the art on screen now
				logging.info(f"Art prefetch: '{job.title}' now playing, carrying on")
			if target is not self.target:
				self.target = target
				self.gate_open = False
			self._cancel_prefetch(target.art_url_key if target is not None else None, "no longer next")

	def gate_waiting(self) -> bool:
		return self.target is not None and not self.gate_open

	def open_gate(self) -> None:
		"""The playing track's audio is buffered enough to start the prefetch"""
		with self.lock:
			if self.gate_open:
				return
			self.gate_open = True
		self._try_prefetch()

	def _try_prefetch(self) -> None:
		with self.lock:
			track = self.target
			if track is None or not self.gate_open or self.prefetch_job is not None:
				return
			# Art wanted on screen goes first; this is tried again when it's done
			if any(not j.prefetch for j in self.jobs.values()):
				return
			key = track.art_url_key
			if os.path.isfile(self.cache_path(key)) or self._held_off(track):
				self.target = None
				return
			job = _Job(key, True, self._title(track))
			self.jobs[key] = job
			self.prefetch_job = job
		logging.info(f"Art prefetch: start '{job.title}'")
		self._spawn(job, track)
