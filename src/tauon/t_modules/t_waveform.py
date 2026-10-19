# Copyright © 2026, Tauon contributors

"""Seek bar waveforms for the Feux panel.

WaveformCache decodes the playing track with FFmpeg on a worker thread and
reduces it to one RMS amplitude per BLOCK_S of audio, published as it goes
so the bar can reveal the waveform while the scan is still running. Results
live in memory only.

Needles animates the bar between the flat seek bar and the needle waveform,
one tween per needle, and coverage_quads draws a rect whose fractional edges
fade out at partial alpha, since SDL's rasterizer covers whole pixels only.
"""

from __future__ import annotations

import logging
import math
import os
import subprocess
import threading
import time
from array import array
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Tauon, TrackClass

BLOCK_S = 0.05
RATE = 8000
BLOCK_SAMPLES = round(RATE * BLOCK_S)
# Needle heights are linear amplitude relative to the track's loudest
# needle; CONTRAST > 1 deepens the quiet parts further. QUIET_REF keeps a
# near-silent track from being scaled up to full height.
CONTRAST = 1.0
QUIET_REF = 0.003
CACHE_LIMIT = 24
RETRY_S = 5.0          # wait before looking for a missing source again
READ_BYTES = 16000     # one second of decoded audio
FRAME_EVERY_S = 0.03   # throttle for the worker's redraw requests


def _sumprod(values: array) -> float:
	if hasattr(math, "sumprod"):
		return math.sumprod(values, values)
	return float(sum(v * v for v in values))


def block_rms(pcm: bytes) -> list[float]:
	"""RMS amplitude (1.0 = full scale) of each whole block of mono s16le
	audio in `pcm`."""
	samples = array("h")
	samples.frombytes(pcm[: len(pcm) - len(pcm) % 2])
	out = []
	for start in range(0, len(samples) - BLOCK_SAMPLES + 1, BLOCK_SAMPLES):
		block = samples[start:start + BLOCK_SAMPLES]
		out.append(math.sqrt(_sumprod(block) / BLOCK_SAMPLES) / 32768)
	return out


def normalise(values: list[float | None], contrast: float = CONTRAST) -> list[float | None]:
	"""Scale needle amplitudes to 0..1 against the loudest one known so far.
	Linear rather than dB: loud masters sit within a few dB of their peak
	throughout, which a log scale flattens into a solid block."""
	ref = max((v for v in values if v is not None), default=0.0)
	ref = max(ref, QUIET_REF)
	return [None if v is None else min(1.0, v / ref) ** contrast for v in values]


class Waveform:
	"""One track's block RMS, appended by the worker while the UI reads it."""

	def __init__(self, duration: float) -> None:
		self.rms: list[float] = []
		self.expected = math.ceil(duration / BLOCK_S) if duration > 0 else 0
		self.done = False
		self.failed = False
		self._spans: tuple[tuple, list[float | None]] | None = None

	@property
	def total(self) -> int:
		"""Blocks the track spans, 0 while that isn't known yet."""
		if self.expected:
			return self.expected
		return len(self.rms) if self.done else 0

	def span(self, a: float, b: float) -> float | None:
		"""RMS over the fraction [a, b) of the track, or None until every
		block in it has been decoded. An energy mean rather than the loudest
		block, which would lift every needle to its biggest beat."""
		total = self.total
		if self.failed or not total:
			return None
		first = min(int(a * total), total - 1)
		last = max(first + 1, math.ceil(b * total))
		rms = self.rms
		count = len(rms)
		if count < last and not self.done:
			return None
		if first >= count:
			return 0.0
		blocks = rms[first:min(last, count)]
		return math.sqrt(sum(v * v for v in blocks) / len(blocks))

	def spans(self, n: int) -> list[float | None]:
		"""span() for n equal needles, recomputed only as data arrives."""
		key = (n, len(self.rms), self.done, self.failed)
		if self._spans is None or self._spans[0] != key:
			self._spans = (key, [self.span(i / n, (i + 1) / n) for i in range(n)])
		return self._spans[1]


class _Job:
	def __init__(self, key: tuple, ffmpeg: str, source: str, start: float, length: float,
			waveform: Waveform) -> None:
		self.key = key
		self.ffmpeg = ffmpeg
		self.source = source
		self.start = start
		self.length = length
		self.waveform = waveform


class WaveformCache:
	"""In-memory waveforms, scanned on demand one track at a time.

	get() is cheap enough to call every frame: it answers from the cache, and
	only on a miss looks for a source and queues a scan. A newer request
	cancels the scan in progress, so it always follows the playing track.
	"""

	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.lock = threading.Lock()
		self.cond = threading.Condition(self.lock)
		self.cache: OrderedDict[tuple, Waveform] = OrderedDict()
		self.missing: dict[tuple, float] = {}
		self.pending: _Job | None = None
		self.thread: threading.Thread | None = None

	@staticmethod
	def key(track: TrackClass) -> tuple:
		return (track.fullpath, track.start_time, track.length, track.is_network)

	def get(self, track: TrackClass) -> Waveform | None:
		key = self.key(track)
		with self.lock:
			waveform = self.cache.get(key)
			if waveform is not None:
				self.cache.move_to_end(key)
				return waveform
			if time.monotonic() < self.missing.get(key, 0.0):
				return None

		source = self._source(track)
		ffmpeg = self.tauon.get_ffmpeg() if source else None
		if not source or not ffmpeg:
			with self.lock:
				self.missing[key] = time.monotonic() + RETRY_S
			return None

		waveform = Waveform(track.length)
		start = float(track.start_time) if track.is_cue or track.start_time else 0.0
		# A cue track at 0:00 still has to stop at its own end
		length = float(track.length) if start or track.is_cue else 0.0
		with self.lock:
			self.missing.pop(key, None)
			self.cache[key] = waveform
			while len(self.cache) > CACHE_LIMIT:
				self.cache.popitem(last=False)
			# A queued job that never started would leave its waveform empty for good
			replaced = self.pending
			if replaced is not None and self.cache.get(replaced.key) is replaced.waveform:
				del self.cache[replaced.key]
			self.pending = _Job(key, str(ffmpeg), source, start, length, waveform)
			if self.thread is None:
				self.thread = threading.Thread(target=self._run, name="waveform", daemon=True)
				self.thread.start()
			self.cond.notify()
		return waveform

	def _source(self, track: TrackClass) -> str | None:
		if track.is_network:
			cachement = getattr(self.tauon, "cachement", None)
			return cachement.get_local_instant(track) if cachement is not None else None
		return track.fullpath if os.path.isfile(track.fullpath) else None

	def _run(self) -> None:
		while True:
			with self.lock:
				while self.pending is None:
					self.cond.wait()
				job = self.pending
				self.pending = None
			try:
				self._scan(job)
			except Exception:
				logging.exception("Waveform scan failed")
				job.waveform.failed = True

	def _superseded(self) -> bool:
		return self.pending is not None

	def _drop(self, job: _Job) -> None:
		with self.lock:
			if self.cache.get(job.key) is job.waveform:
				del self.cache[job.key]

	def _scan(self, job: _Job) -> None:
		command = [job.ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error"]
		if job.start:
			command += ["-ss", f"{job.start:.3f}"]
		command += ["-i", job.source]
		if job.length:
			command += ["-t", f"{job.length:.3f}"]
		command += [
			"-map", "0:a:0", "-vn", "-sn", "-dn", "-threads", "1",
			"-ac", "1", "-ar", str(RATE), "-acodec", "pcm_s16le", "-f", "s16le", "pipe:1",
		]
		process = subprocess.Popen(
			command,
			stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE,
			stderr=subprocess.DEVNULL,
			creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
		)
		waveform = job.waveform
		carry = b""
		last_frame = 0.0
		try:
			while True:
				if self._superseded():
					self._drop(job)
					return
				chunk = process.stdout.read1(READ_BYTES)
				if not chunk:
					break
				carry += chunk
				whole = len(carry) - len(carry) % (BLOCK_SAMPLES * 2)
				if whole:
					waveform.rms.extend(block_rms(carry[:whole]))
					carry = carry[whole:]
					now = time.monotonic()
					if now - last_frame > FRAME_EVERY_S:
						last_frame = now
						self._redraw()
		finally:
			if process.poll() is None:
				process.kill()
			process.stdout.close()
			process.wait()
		if carry:
			# Pad the trailing partial block out to a whole one.
			waveform.rms.extend(block_rms(carry + bytes(BLOCK_SAMPLES * 2 - len(carry))))
		if process.returncode != 0 and not waveform.rms:
			waveform.failed = True
		waveform.done = True
		self._redraw()

	def _redraw(self) -> None:
		self.tauon.gui.request_frame()
		self.tauon.wake()


UNZIP = 0.25  # share of a tween spent opening or closing the gaps


def _ease_out(k: float) -> float:
	return 1 - (1 - k) ** 3


def _smooth(k: float) -> float:
	return k * k * (3 - 2 * k)


def _clamp(k: float) -> float:
	return 0.0 if k < 0 else 1.0 if k > 1 else k


class Needles:
	"""Per-needle tween between the flat bar and the waveform.

	A needle's state is (half height, gap) with gap 0 meaning it touches its
	neighbours, so a row of flat, gapless needles is the plain seek bar. When
	a needle's target changes it tweens from wherever it is now: opening
	the gap before rising, or settling before closing it.
	"""

	def __init__(self, duration: float = 0.8) -> None:
		self.duration = duration
		self.geometry: tuple | None = None
		self.snap = False
		self.fh: list[float] = []
		self.fg: list[float] = []
		self.th: list[float] = []
		self.tg: list[float] = []
		self.t0: list[float] = []

	def layout(self, n: int, flat: float, geometry: tuple) -> None:
		"""Size the needles. A geometry change (resize, rescale) snaps to the
		new targets instead of animating to them."""
		if geometry == self.geometry and n == len(self.th):
			return
		first = self.geometry is None
		self.geometry = geometry
		self.fh = [flat] * n
		self.fg = [0.0] * n
		self.th = [flat] * n
		self.tg = [0.0] * n
		self.t0 = [-math.inf] * n
		self.snap = not first

	def value(self, i: int, now: float) -> tuple[float, float]:
		k = _clamp((now - self.t0[i]) / self.duration)
		fh, fg, th, tg = self.fh[i], self.fg[i], self.th[i], self.tg[i]
		if k >= 1:
			return th, tg
		if tg > fg:
			gk, hk = _clamp(k / UNZIP), _clamp((k - UNZIP) / (1 - UNZIP))
		elif tg < fg:
			hk, gk = _clamp(k / (1 - UNZIP)), _clamp((k - (1 - UNZIP)) / UNZIP)
		else:
			hk = gk = k
		return fh + (th - fh) * _ease_out(hk), fg + (tg - fg) * _smooth(gk)

	def update(self, targets: list[tuple[float, float]], now: float) -> bool:
		"""Retarget changed needles; True while any needle is still moving."""
		snap = self.snap
		self.snap = False
		moving = False
		end = now - self.duration
		for i, (h, g) in enumerate(targets):
			if h != self.th[i] or g != self.tg[i]:
				if snap:
					self.fh[i], self.fg[i], self.t0[i] = h, g, -math.inf
				else:
					self.fh[i], self.fg[i] = self.value(i, now)
					self.t0[i] = now
				self.th[i], self.tg[i] = h, g
			if self.t0[i] > end:
				moving = True
		return moving


def _spans(a: float, b: float) -> list[tuple[int, int, float]]:
	"""Split [a, b] into pixel-aligned runs with the share of each covered."""
	if b <= a:
		return []
	fa = math.floor(a)
	if math.ceil(b) - fa <= 1:
		return [(fa, fa + 1, b - a)]
	out = []
	ia, ib = math.ceil(a), math.floor(b)
	if ia > a:
		out.append((fa, ia, ia - a))
	if ib > ia:
		out.append((ia, ib, 1.0))
	if b > ib:
		out.append((ib, ib + 1, b - ib))
	return out


def coverage_quads(x0: float, y0: float, x1: float, y1: float,
		rgba: tuple[float, float, float, float], vertices: list, indices: list) -> None:
	"""Append geometry filling [x0, x1] x [y0, y1], each partly covered edge
	pixel drawn at the alpha of its coverage."""
	r, g, b, a = rgba
	columns = _spans(x0, x1)
	for ya, yb, cy in _spans(y0, y1):
		for xa, xb, cx in columns:
			alpha = a * cx * cy
			if alpha <= 0:
				continue
			base = len(vertices)
			vertices += (
				(xa, ya, 0.0, 0.0, r, g, b, alpha),
				(xb, ya, 0.0, 0.0, r, g, b, alpha),
				(xb, yb, 0.0, 0.0, r, g, b, alpha),
				(xa, yb, 0.0, 0.0, r, g, b, alpha),
			)
			indices += (base, base + 1, base + 2, base, base + 2, base + 3)
