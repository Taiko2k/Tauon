from __future__ import annotations

import json
import logging
import subprocess
import threading
from pathlib import Path
from typing import Any
from collections.abc import Callable


class MacNowPlayingHelper:
	"""Spawn and communicate with the macOS Now Playing helper app.

	IPC is newline-delimited JSON over stdin/stdout.
	"""

	def __init__(
		self,
		executable: Path,
		on_media_key: Callable[[str], None],
		on_seek: Callable[[float], None] | None = None,
		on_seek_relative: Callable[[float], None] | None = None,
	) -> None:
		self.executable = executable
		self._on_media_key = on_media_key
		self._on_seek = on_seek
		self._on_seek_relative = on_seek_relative
		self._proc: subprocess.Popen[str] | None = None
		self._stdin_lock = threading.Lock()
		self._reader_thread: threading.Thread | None = None

	def start(self) -> bool:
		if self._proc is not None:
			return True
		try:
			self._proc = subprocess.Popen(
				[str(self.executable)],
				stdin=subprocess.PIPE,
				stdout=subprocess.PIPE,
				stderr=subprocess.DEVNULL,
				text=True,
				bufsize=1,
			)
		except Exception:
			logging.exception("Failed to start macOS Now Playing helper")
			self._proc = None
			return False

		self._reader_thread = threading.Thread(target=self._read_loop, name="TauonNowPlaying", daemon=True)
		self._reader_thread.start()
		return True

	def _read_loop(self) -> None:
		assert self._proc is not None
		assert self._proc.stdout is not None
		for line in self._proc.stdout:
			line = line.strip()
			if not line:
				continue
			try:
				msg = json.loads(line)
			except Exception:
				logging.debug(f"NowPlaying helper sent non-JSON line: {line!r}")
				continue

			if not isinstance(msg, dict):
				continue

			mtype = msg.get("type")
			if mtype == "media_key":
				name = msg.get("name")
				if isinstance(name, str):
					try:
						self._on_media_key(name)
					except Exception:
						logging.exception("Error handling media_key from NowPlaying helper")
			elif mtype == "seek":
				pos = msg.get("position")
				if isinstance(pos, (int, float)) and self._on_seek is not None:
					try:
						self._on_seek(float(pos))
					except Exception:
						logging.exception("Error handling seek from NowPlaying helper")
			elif mtype == "seek_relative":
				delta = msg.get("delta")
				if isinstance(delta, (int, float)) and self._on_seek_relative is not None:
					try:
						self._on_seek_relative(float(delta))
					except Exception:
						logging.exception("Error handling seek_relative from NowPlaying helper")

	def send(self, msg: dict[str, Any]) -> None:
		if self._proc is None or self._proc.stdin is None:
			return
		try:
			data = json.dumps(msg, ensure_ascii=False)
		except Exception:
			return
		with self._stdin_lock:
			try:
				self._proc.stdin.write(data + "\n")
				self._proc.stdin.flush()
			except Exception:
				# Helper may have exited.
				return

	def update(
		self,
		*,
		title: str,
		artist: str,
		album: str = "",
		art_path: str = "",
		state: int,
		duration: float | None = None,
		elapsed: float | None = None,
	) -> None:
		msg: dict[str, Any] = {
			"type": "update",
			"title": title,
			"artist": artist,
			"album": album,
			"art_path": art_path,
			"state": state,
		}
		if duration is not None:
			msg["duration"] = float(duration)
		if elapsed is not None:
			msg["elapsed"] = float(elapsed)
		self.send(msg)

	def clear(self) -> None:
		self.send({"type": "clear"})

	def stop(self) -> None:
		if self._proc is None:
			return
		try:
			self.send({"type": "quit"})
		except Exception:
			pass
		try:
			self._proc.terminate()
		except Exception:
			pass
		try:
			self._proc.wait(timeout=1.0)
		except Exception:
			pass
		self._proc = None
