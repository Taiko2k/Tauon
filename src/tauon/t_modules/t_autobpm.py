"""Smart Mix - Background BPM analysis
Uses aubio to analyse the first 30s of audio.
Designed for slow CPUs: does not block the UI.
"""
from __future__ import annotations

import logging
import threading
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
	from tauon.t_modules.t_main import TrackClass


class BpmAnalyser:
	"""Analyses BPM of audio tracks in a background thread.

	Follows the Single Responsibility Principle: this class only
	manages the BPM analysis queue and worker thread lifecycle.
	All I/O side-effects (saving, notifying) are injected as callbacks.
	"""

	_ANALYSIS_DURATION_S: int = 30
	_HOP_SIZE: int = 256
	_WIN_SIZE: int = 512
	_SAMPLE_RATE: int = 44100
	_BPM_MIN: float = 60.0
	_BPM_MAX: float = 200.0
	_SLEEP_BETWEEN_TRACKS: float = 0.1

	def __init__(self) -> None:
		self._queue: deque[int] = deque()
		self._lock = threading.Lock()
		self._thread: threading.Thread | None = None

	# ------------------------------------------------------------------
	# Public interface
	# ------------------------------------------------------------------

	def queue_library(
		self,
		master_library: dict,
		save_cb: Callable | None = None,
		notify_cb: Callable | None = None,
	) -> None:
		"""Queue all tracks without BPM and start the analysis thread."""
		count = 0
		with self._lock:
			for track_id, track in master_library.items():
				if getattr(track, "bpm", 0.0) == 0.0:
					self._queue.append(track_id)
					count += 1

		if count == 0:
			logging.info("t_autobpm: all tracks already have BPM")
			return

		logging.info(f"t_autobpm: {count} tracks queued for analysis")
		self._start_thread(master_library, save_cb, notify_cb)

	def queue_track(
		self,
		track: TrackClass,
		master_library: dict,
		save_cb: Callable | None = None,
		notify_cb: Callable | None = None,
	) -> None:
		"""Queue a single newly imported track for BPM analysis."""
		if getattr(track, "bpm", 0.0) > 0:
			return

		track_id = next(
			(tid for tid, t in master_library.items() if t is track), None
		)
		if track_id is None:
			return

		with self._lock:
			if track_id not in self._queue:
				self._queue.append(track_id)

		self._start_thread(master_library, save_cb, notify_cb)

	# ------------------------------------------------------------------
	# Private helpers
	# ------------------------------------------------------------------

	def _start_thread(
		self,
		master_library: dict,
		save_cb: Callable | None,
		notify_cb: Callable | None,
	) -> None:
		"""Start the worker thread if it is not already running."""
		if self._thread is None or not self._thread.is_alive():
			self._thread = threading.Thread(
				target=self._worker,
				args=(master_library, save_cb, notify_cb),
				daemon=True,
				name="autobpm-worker",
			)
			self._thread.start()

	def _worker(
		self,
		master_library: dict,
		save_cb: Callable | None,
		notify_cb: Callable | None,
	) -> None:
		"""Process the analysis queue without saturating the CPU."""
		import time

		logging.info("t_autobpm: analysis thread started")
		self._notify(notify_cb, "Smart Mix: Analysing BPM in background...", mode="info")

		while self._queue:
			with self._lock:
				if not self._queue:
					break
				track_id = self._queue.popleft()

			track = master_library.get(track_id)
			if track is None or getattr(track, "bpm", 0.0) > 0:
				continue

			filepath = str(getattr(track, "fullpath", ""))
			if not filepath or not Path(filepath).exists():
				continue

			bpm = self._analyse_file(filepath)
			if bpm > 0:
				track.bpm = bpm
				logging.info(f"t_autobpm: {Path(filepath).name} = {bpm} BPM")
				self._safe_call(save_cb)

			time.sleep(self._SLEEP_BETWEEN_TRACKS)

		logging.info("t_autobpm: analysis thread finished")
		self._notify(notify_cb, "Smart Mix: BPM analysis complete", mode="done")

	@classmethod
	def _analyse_file(cls, filepath: str) -> float:
		"""Analyse a single audio file and return its BPM, or 0.0 on failure."""
		try:
			import aubio
			import numpy as np

			max_frames = int(cls._SAMPLE_RATE * cls._ANALYSIS_DURATION_S / cls._HOP_SIZE)
			src = aubio.source(filepath, cls._SAMPLE_RATE, cls._HOP_SIZE)
			actual_rate = src.samplerate
			tempo = aubio.tempo("default", cls._WIN_SIZE, cls._HOP_SIZE, actual_rate)
			beats: list[float] = []

			for _ in range(max_frames):
				samples, read = src()
				if tempo(samples):
					beats.append(tempo.get_last_s())
				if read < cls._HOP_SIZE:
					break

			if len(beats) < 4:
				return 0.0

			bpm = 60.0 / float(np.median(np.diff(beats)))
			while bpm < cls._BPM_MIN:
				bpm *= 2
			while bpm > cls._BPM_MAX:
				bpm /= 2
			return round(bpm, 1)

		except Exception as e:
			logging.debug(f"t_autobpm: failed analysing {filepath}: {e}")
			return 0.0

	@staticmethod
	def _safe_call(cb: Callable | None) -> None:
		"""Call a callback silently, ignoring any exceptions."""
		if cb:
			try:
				cb()
			except Exception:
				pass

	@staticmethod
	def _notify(cb: Callable | None, message: str, mode: str = "info") -> None:
		"""Send a UI notification silently, ignoring any exceptions."""
		if cb:
			try:
				cb(message, mode=mode)
			except Exception:
				pass


# ---------------------------------------------------------------------------
# Module-level singleton and convenience facade
# Keeps call sites in t_main.py unchanged while encapsulating all state.
# ---------------------------------------------------------------------------

_analyser = BpmAnalyser()
queue_library = _analyser.queue_library
queue_track = _analyser.queue_track
