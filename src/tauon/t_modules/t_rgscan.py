# Copyright © 2026, Tauon contributors

"""ReplayGain 2.0 analysis with FFmpeg's ebur128 filter.

Each file is measured once. FFmpeg reports the momentary loudness of every
400 ms block (one per 100 ms), and the BS.1770 gating is redone here so the
blocks of all files can be pooled into one album loudness.
"""

from __future__ import annotations

import math
import os
import subprocess
import threading
from concurrent.futures import FIRST_EXCEPTION, ThreadPoolExecutor, wait
from dataclasses import dataclass
from typing import TYPE_CHECKING

from mutagen.oggopus import OggOpus

if TYPE_CHECKING:
	from collections.abc import Callable, Iterable
	from pathlib import Path

	from tauon.t_modules.t_tagedit import TagDocument

REFERENCE_LUFS = -18.0
R128_REFERENCE_LUFS = -23.0
ABSOLUTE_GATE = -70.0
RELATIVE_GATE = -10.0


class ScanCancelledError(Exception):
	pass


class ScanError(Exception):
	def __init__(self, path: Path, message: str) -> None:
		super().__init__(f"{path.name}: {message}")
		self.path = path


@dataclass
class Measurement:
	blocks: list[float]  # gating block loudness in LUFS
	peak: float          # linear true peak

	@property
	def loudness(self) -> float | None:
		return integrated_loudness(self.blocks)


def _energy(loudness: float) -> float:
	return 10 ** ((loudness + 0.691) / 10)


def _loudness(energy: float) -> float:
	return -0.691 + 10 * math.log10(energy)


def integrated_loudness(blocks: Iterable[float]) -> float | None:
	"""BS.1770 gated loudness of a set of blocks, or None if all are silent."""
	energies = [(block, _energy(block)) for block in blocks if block > ABSOLUTE_GATE]
	if not energies:
		return None
	gate = _loudness(sum(energy for _block, energy in energies) / len(energies)) + RELATIVE_GATE
	kept = [energy for block, energy in energies if block > gate]
	return _loudness(sum(kept) / len(kept)) if kept else None


def measure(ffmpeg: str, path: Path, cancel: threading.Event, processes: set, lock: threading.Lock) -> Measurement:
	command = [
		ffmpeg, "-nostdin", "-hide_banner", "-nostats", "-loglevel", "error",
		"-i", f"file:{path}", "-map", "0:a:0",
		"-af", "ebur128=peak=true:metadata=1,ametadata=mode=print:file=-",
		"-f", "null", "-",
	]
	with lock:
		if cancel.is_set():
			raise ScanCancelledError
		process = subprocess.Popen(
			command,
			stdin=subprocess.DEVNULL,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
		)
		processes.add(process)
	errors: list[bytes] = []
	reader = threading.Thread(target=lambda: errors.append(process.stderr.read()), daemon=True)
	reader.start()
	blocks: list[float] = []
	peak = 0.0
	try:
		for line in process.stdout:
			if line.startswith(b"lavfi.r128.M="):
				blocks.append(float(line[13:]))
			elif line.startswith(b"lavfi.r128.true_peak="):
				peak = max(peak, float(line[21:]))
		process.wait()
		reader.join()
	finally:
		with lock:
			processes.discard(process)
		if process.poll() is None:
			process.kill()
			process.wait()
	if cancel.is_set():
		raise ScanCancelledError
	if process.returncode != 0:
		message = b"".join(errors).decode("utf-8", "replace").strip().splitlines()
		raise ScanError(path, message[-1] if message else f"FFmpeg exited with code {process.returncode}")
	if not blocks:
		raise ScanError(path, "no audio was decoded")
	return Measurement(blocks, peak)


def measure_all(
	ffmpeg: str,
	paths: list[Path],
	cancel: threading.Event,
	progress: Callable[[int, Path], None] | None = None,
) -> dict[Path, Measurement]:
	"""Measure files in parallel; any failure stops the whole scan."""
	processes: set[subprocess.Popen] = set()
	lock = threading.Lock()
	results: dict[Path, Measurement] = {}

	def stop() -> None:
		cancel.set()
		with lock:
			for process in processes:
				process.kill()

	def run(path: Path) -> None:
		measurement = measure(ffmpeg, path, cancel, processes, lock)
		with lock:
			results[path] = measurement
			done = len(results)
		if progress is not None:
			progress(done, path)

	finished = threading.Event()

	def watch() -> None:
		# Kill running FFmpeg processes promptly when the caller cancels
		while not finished.wait(0.1):
			if cancel.is_set():
				stop()
				return

	threading.Thread(target=watch, daemon=True).start()
	try:
		with ThreadPoolExecutor(max_workers=max(1, min(4, os.cpu_count() or 1, len(paths)))) as pool:
			futures = [pool.submit(run, path) for path in paths]
			wait(futures, return_when=FIRST_EXCEPTION)
			failed = next((future for future in futures if future.done() and future.exception()), None)
			if failed is not None:
				stop()
				raise failed.exception()
	finally:
		finished.set()
	return results


def replaygain_entries(doc: TagDocument, track: Measurement, album: list[Measurement] | None) -> dict[str, str]:
	"""Tag entries to stage on `doc`; empty values remove a tag. Without `album`, album tags are left alone."""
	track_loudness = track.loudness
	album_loudness = None if album is None else integrated_loudness(block for item in album for block in item.blocks)
	if track_loudness is None or (album is not None and album_loudness is None):
		return {}
	if isinstance(doc.audio, OggOpus):
		# Opus players read R128 gains (Q7.8, -23 LUFS reference); stale RG tags would override them in Tauon
		values = {"R128_TRACK_GAIN": str(_q78(R128_REFERENCE_LUFS - track_loudness))}
		removed = ["REPLAYGAIN_TRACK_GAIN", "REPLAYGAIN_TRACK_PEAK"]
		if album is not None:
			values["R128_ALBUM_GAIN"] = str(_q78(R128_REFERENCE_LUFS - album_loudness))
			removed += ["REPLAYGAIN_ALBUM_GAIN", "REPLAYGAIN_ALBUM_PEAK"]
	else:
		values = {
			"REPLAYGAIN_TRACK_GAIN": f"{REFERENCE_LUFS - track_loudness:.2f} dB",
			"REPLAYGAIN_TRACK_PEAK": f"{track.peak:.6f}",
		}
		if album is not None:
			values["REPLAYGAIN_ALBUM_GAIN"] = f"{REFERENCE_LUFS - album_loudness:.2f} dB"
			values["REPLAYGAIN_ALBUM_PEAK"] = f"{max(item.peak for item in album):.6f}"
		removed = []
	entries: dict[str, str] = {}
	existing = list(doc.tags.keys())
	for name, value in values.items():
		key = _native_key(doc, name)
		for native in existing:
			# ID3 and MP4 keys are case sensitive; drop other spellings so one value remains
			if native != key and _tag_name(doc, native) == name.lower() and doc.family in ("ID3", "MP4"):
				entries[native] = ""
		native = doc.portable_key(key)
		if doc.text_values(native) != [value]:
			entries[key] = value
	removed_names = {name.lower() for name in removed}
	for native in existing:
		if _tag_name(doc, native) in removed_names:
			entries[native] = ""
	return entries


def _q78(gain: float) -> int:
	return max(-32768, min(32767, round(gain * 256)))


def _native_key(doc: TagDocument, name: str) -> str:
	if doc.family == "ID3":
		return "TXXX:" + name
	if doc.family == "MP4":
		# Tauon and iTunes-style readers expect the lower case freeform name
		return "----:com.apple.iTunes:" + name.lower()
	return name


def _tag_name(doc: TagDocument, native: str) -> str:
	if doc.family == "ID3":
		return native[5:].lower() if native.startswith("TXXX:") else ""
	if doc.family == "MP4":
		return native.split(":", 2)[-1].lower() if native.startswith("----:") else ""
	return native.lower()
