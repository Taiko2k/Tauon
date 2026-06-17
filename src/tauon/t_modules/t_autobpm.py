"""Smart Mix - Background BPM and musical key analysis
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
	"""Analyses BPM, musical key and silence of audio tracks in a background thread.

	Follows the Single Responsibility Principle: this class only
	manages the analysis queue and worker thread lifecycle.
	All I/O side-effects (saving, notifying) are injected as callbacks.
	"""

	_ANALYSIS_DURATION_S: int = 30
	_HOP_SIZE: int = 512
	_WIN_SIZE: int = 512
	_KEY_WIN_SIZE: int = 4096
	_SAMPLE_RATE: int = 44100
	_BPM_MIN: float = 60.0
	_BPM_MAX: float = 200.0
	_SLEEP_BETWEEN_TRACKS: float = 0.1
	_SILENCE_THRESHOLD_DB: str = "-65dB"
	_SILENCE_MIN_DURATION: str = "0.3"

	# Krumhansl-Schmuckler key profiles (major and minor)
	_MAJOR_PROFILE = (6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
	                  2.52, 5.19, 2.39, 3.66, 2.29, 2.88)
	_MINOR_PROFILE = (6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
	                  2.54, 4.75, 3.98, 2.69, 3.34, 3.17)

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
		"""Queue all tracks without BPM or key and start the analysis thread."""
		count = 0
		with self._lock:
			for track_id, track in master_library.items():
				needs_bpm = getattr(track, "bpm", 0.0) == 0.0
				needs_key = getattr(track, "key", -1) < 0
				if needs_bpm or needs_key:
					self._queue.append(track_id)
					count += 1

		if count == 0:
			logging.info("t_autobpm: all tracks already have BPM and key")
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
		"""Queue a single newly imported track for analysis."""
		needs_bpm = getattr(track, "bpm", 0.0) == 0.0
		needs_key = getattr(track, "key", -1) < 0
		if not needs_bpm and not needs_key:
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
			if track is None:
				continue

			needs_bpm = getattr(track, "bpm", 0.0) == 0.0
			needs_key = getattr(track, "key", -1) < 0
			if not needs_bpm and not needs_key:
				continue

			filepath = str(getattr(track, "fullpath", ""))
			if not filepath or not Path(filepath).exists():
				continue

			bpm, key = self._analyse_file(filepath)

			if needs_bpm and bpm > 0:
				track.bpm = bpm
			if needs_key and key >= 0:
				track.key = key

			if bpm > 0 or key >= 0:
				name = Path(filepath).name
				logging.info(
					f"t_autobpm: {name} = {bpm} BPM, "
					f"key={key} ({self._key_name(key)})"
				)

			sil_start, sil_end = self._detect_silence(filepath)
			track.silence_start = sil_start
			track.silence_end = sil_end
			if sil_start > 0.5 or sil_end > 0.5:
				logging.info(
					f"t_autobpm: {Path(filepath).name} "
					f"silence start={sil_start}s end={sil_end}s"
				)

			self._safe_call(save_cb)
			time.sleep(self._SLEEP_BETWEEN_TRACKS)

		logging.info("t_autobpm: analysis thread finished")
		self._notify(notify_cb, "Smart Mix: BPM analysis complete", mode="done")

	@classmethod
	def _analyse_file(cls, filepath: str) -> tuple[float, int]:
		"""Analyse BPM and musical key in a single audio pass.

		Returns (bpm, key) where:
		  bpm: beats per minute (0.0 on failure)
		  key: 0-11 major (C to B), 12-23 minor (C to B), -1 on failure
		"""
		try:
			import aubio
			import numpy as np

			max_frames = int(cls._SAMPLE_RATE * cls._ANALYSIS_DURATION_S / cls._HOP_SIZE)
			src = aubio.source(filepath, cls._SAMPLE_RATE, cls._HOP_SIZE)
			actual_rate = src.samplerate

			# BPM detector
			tempo = aubio.tempo("default", cls._WIN_SIZE, cls._HOP_SIZE, actual_rate)

			# Chromagram for key detection
			pv = aubio.pvoc(cls._KEY_WIN_SIZE, cls._HOP_SIZE)
			n_bins = cls._KEY_WIN_SIZE // 2 + 1
			freqs = np.arange(n_bins) * actual_rate / cls._KEY_WIN_SIZE
			with np.errstate(divide="ignore", invalid="ignore"):
				midi = np.where(
					freqs > 0,
					12.0 * np.log2(np.maximum(freqs, 1e-10) / 440.0) + 69.0,
					-1.0,
				)
			valid = (freqs >= 27.5) & (freqs <= 4186.0)
			pc_map = (np.round(midi).astype(int)) % 12
			chroma = np.zeros(12, dtype=np.float64)
			beats: list[float] = []

			for _ in range(max_frames):
				samples, read = src()

				# BPM
				if tempo(samples):
					beats.append(tempo.get_last_s())

				# Chromagram
				spec = pv(samples)
				mag = spec.norm
				np.add.at(chroma, pc_map[valid], mag[valid])

				if read < cls._HOP_SIZE:
					break

			# --- BPM calculation ---
			bpm = 0.0
			if len(beats) >= 4:
				intervals = np.diff(beats)
				bpm = 60.0 / float(np.median(intervals))
				while bpm < cls._BPM_MIN:
					bpm *= 2
				while bpm > cls._BPM_MAX:
					bpm /= 2
				bpm = round(bpm, 1)

			# --- Key calculation (Krumhansl-Schmuckler) ---
			key = -1
			total = np.sum(chroma)
			if total > 0:
				chroma /= total
				maj = np.array(cls._MAJOR_PROFILE)
				min_ = np.array(cls._MINOR_PROFILE)
				maj /= maj.sum()
				min_ /= min_.sum()

				best_r = -2.0
				for root in range(12):
					for mode, prof in enumerate(
						[np.roll(maj, root), np.roll(min_, root)]
					):
						r = float(np.corrcoef(chroma, prof)[0, 1])
						if r > best_r:
							best_r = r
							key = root + mode * 12

			return bpm, key

		except Exception as e:
			logging.debug(f"t_autobpm: analysis failed for {filepath}: {e}")
			return 0.0, -1

	@classmethod
	def _detect_silence(cls, filepath: str) -> tuple[float, float]:
		"""Detect silence at the start and end of a track using ffmpeg.

		Returns (silence_start_sec, silence_end_sec).
		"""
		import subprocess
		import re
		try:
			result = subprocess.run(
				[
					"ffmpeg", "-i", filepath,
					"-af",
					f"silencedetect=noise={cls._SILENCE_THRESHOLD_DB}"
					f":d={cls._SILENCE_MIN_DURATION}",
					"-f", "null", "-",
				],
				capture_output=True,
				text=True,
				timeout=60,
			)
			output = result.stderr

			dur_match = re.search(r"Duration: (\d+):(\d+):([\d.]+)", output)
			if not dur_match:
				return 0.0, 0.0
			h, m, s = dur_match.groups()
			duration = int(h) * 3600 + int(m) * 60 + float(s)

			starts = [
				float(x)
				for x in re.findall(r"silence_start: ([\d.e+\-]+)", output)
			]
			ends = [
				float(x)
				for x in re.findall(r"silence_end: ([\d.e+\-]+)", output)
			]

			silence_start = 0.0
			if starts and starts[0] < 0.5 and ends:
				silence_start = ends[0]

			silence_end = 0.0
			if starts:
				last_start = starts[-1]
				if len(ends) < len(starts):
					silence_end = max(0.0, duration - last_start)
				elif ends and abs(ends[-1] - duration) < 1.5:
					silence_end = ends[-1] - last_start

			return round(silence_start, 2), round(silence_end, 2)

		except Exception as e:
			logging.debug(f"t_autobpm: silence detection failed for {filepath}: {e}")
			return 0.0, 0.0

	@staticmethod
	def _key_name(key: int) -> str:
		"""Return human-readable key name and Camelot position."""
		if key < 0:
			return "unknown"
		names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
		camelot = [8, 3, 10, 5, 12, 7, 2, 9, 4, 11, 6, 1,
		           5, 12, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10]
		mode = "min" if key >= 12 else "maj"
		letter = "A" if key >= 12 else "B"
		return f"{names[key % 12]} {mode} ({camelot[key]}{letter})"

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
# ---------------------------------------------------------------------------

_analyser = BpmAnalyser()
queue_library = _analyser.queue_library
queue_track = _analyser.queue_track
