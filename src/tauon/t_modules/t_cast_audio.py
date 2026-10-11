# Copyright © 2026, Tauon contributors
from __future__ import annotations

import logging
import subprocess
import tempfile
import wave
from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING

from mutagen import MutagenError
from mutagen.mp4 import MP4

if TYPE_CHECKING:
	from tauon.t_modules.t_main import TrackClass


def audio_mime_type(file_ext: str) -> str:
	return {
		"FLAC": "audio/flac",
		"OGG": "audio/ogg",
		"OPUS": "audio/ogg",
		"OGA": "audio/ogg",
		"M4A": "audio/mp4",
		"MP4": "audio/mp4",
		"AAC": "audio/aac",
		"WAV": "audio/wav",
		"AIFF": "audio/aiff",
		"AIF": "audio/aiff",
	}.get(file_ext.upper(), "audio/mpeg")


def native_cast_mime_type(track: TrackClass) -> str | None:
	"""Return a MIME type only for formats the Cast receiver can decode."""
	ext = track.file_ext.upper()
	if ext in {"MP3", "OGG", "OPUS", "OGA"}:
		return audio_mime_type(ext)
	if ext == "FLAC" and track.samplerate <= 96000 and track.bit_depth <= 24:
		return "audio/flac"
	if ext == "WAV":
		try:
			with wave.open(track.fullpath, "rb") as audio:
				if audio.getsampwidth() == 2 and audio.getnchannels() <= 2 and audio.getframerate() <= 96000:
					return "audio/wav"
		except (OSError, EOFError, wave.Error):
			return None
	if ext in {"M4A", "MP4"}:
		try:
			codec = MP4(track.fullpath).info.codec
		except (OSError, MutagenError):
			logging.exception("Failed to read MPEG-4 codec for Chromecast")
			return None
		if codec in {"mp4a.40.2", "mp4a.40.5", "mp4a.40.29"}:
			return "audio/mp4"
	return None


class CastAudioCache:
	"""Keep a few seekable FLAC conversions for the current Cast session."""

	def __init__(self) -> None:
		self.directory: tempfile.TemporaryDirectory[str] | None = None
		self.files: OrderedDict[int, tuple[tuple[str, int, int], Path]] = OrderedDict()

	def get(self, track_id: int) -> Path | None:
		entry = self.files.get(track_id)
		return entry[1] if entry else None

	def prepare(self, track: TrackClass, ffmpeg: Path | None) -> Path:
		source = Path(track.fullpath)
		stat = source.stat()
		key = (str(source), stat.st_mtime_ns, stat.st_size)
		entry = self.files.get(track.index)
		if entry and entry[0] == key:
			self.files.move_to_end(track.index)
			return entry[1]
		if ffmpeg is None:
			raise FileNotFoundError("FFmpeg unavailable")  # noqa: TRY003
		if self.directory is None:
			self.directory = tempfile.TemporaryDirectory(prefix="tauon-cast-")
		target = Path(self.directory.name) / f"{track.index}.flac"
		# Convert the whole source so CUE offsets and the player's seek times still match.
		command = [
			str(ffmpeg),
			"-nostdin",
			"-v",
			"error",
			"-y",
			"-i",
			str(source),
			"-map",
			"0:a:0",
			"-vn",
			"-map_metadata",
			"-1",
			"-c:a",
			"flac",
			"-sample_fmt",
			"s32",
			"-bits_per_raw_sample",
			"24",
			"-ac",
			"2",
			"-ar",
			str(min(track.samplerate or 48000, 96000)),
			str(target),
		]
		try:
			subprocess.run(
				command,
				stdin=subprocess.DEVNULL,
				stdout=subprocess.DEVNULL,
				stderr=subprocess.PIPE,
				check=True,
				timeout=120,
			)
			if target.stat().st_size == 0:
				raise OSError("Empty Cast conversion")  # noqa: TRY003, TRY301
		except (OSError, subprocess.SubprocessError):
			target.unlink(missing_ok=True)
			self.files.pop(track.index, None)
			raise
		self.files[track.index] = (key, target)
		self.files.move_to_end(track.index)
		while len(self.files) > 3:
			track_id, old_entry = self.files.popitem(last=False)
			try:
				old_entry[1].unlink(missing_ok=True)
			except OSError:
				logging.debug("Cast file %s is still in use; retaining it until session cleanup", track_id)
		return target
