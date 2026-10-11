# Copyright © 2026, Tauon contributors

"""Chromaprint's C API, with native buffer ownership and library discovery."""

from __future__ import annotations

import ctypes
import ctypes.util
import os
import sys
import threading
from array import array
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Iterable

# Validation details are displayed by the editor.
# ruff: noqa: TRY003

_CONTEXT_LOCK = threading.Lock()


class ChromaprintError(Exception):
	pass


class ChromaprintCancelledError(Exception):
	pass


class Chromaprint:
	def __init__(self, library: str = "", directories: Iterable[Path] = ()) -> None:
		if library.strip():
			candidates = [os.path.expanduser(library.strip())]
		else:
			names = (
				("libchromaprint.dll", "chromaprint.dll")
				if sys.platform == "win32"
				else ("libchromaprint.1.dylib", "libchromaprint.dylib")
				if sys.platform == "darwin"
				else ("libchromaprint.so.1", "libchromaprint.so")
			)
			locations = [*directories, Path(sys.executable).parent, Path(sys.prefix) / "lib"]
			frozen_root = getattr(sys, "_MEIPASS", None)
			if frozen_root:
				locations.insert(0, Path(frozen_root))
			if sys.platform == "darwin":
				locations.extend((Path("/opt/homebrew/lib"), Path("/usr/local/lib")))
			elif sys.platform == "win32":
				locations.extend(Path(item) for item in os.get_exec_path() if item)
			candidates = [str(folder / name) for folder in locations for name in names if (folder / name).is_file()]
			found = ctypes.util.find_library("chromaprint")
			if found:
				candidates.append(found)
			candidates.extend(names)
		for candidate in dict.fromkeys(candidates):
			try:
				if sys.platform == "win32" and Path(candidate).is_absolute():
					with os.add_dll_directory(str(Path(candidate).parent)):
						self.lib = ctypes.CDLL(candidate)
				else:
					self.lib = ctypes.CDLL(candidate)
				self._configure()
				break
			except (OSError, AttributeError):
				continue
		else:
			raise ChromaprintError(
				"Could not load the Chromaprint library. Install Chromaprint or set its library path in Lookup setup. "
				"The library and its dependencies must match Tauon's architecture."
			)

	def _configure(self) -> None:
		for name, arguments, result in (
			("chromaprint_new", [ctypes.c_int], ctypes.c_void_p),
			("chromaprint_free", [ctypes.c_void_p], None),
			("chromaprint_start", [ctypes.c_void_p, ctypes.c_int, ctypes.c_int], ctypes.c_int),
			("chromaprint_feed", [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int16), ctypes.c_int], ctypes.c_int),
			("chromaprint_finish", [ctypes.c_void_p], ctypes.c_int),
			("chromaprint_get_raw_fingerprint_size", [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)], ctypes.c_int),
			("chromaprint_get_fingerprint", [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)], ctypes.c_int),
			("chromaprint_dealloc", [ctypes.c_void_p], None),
		):
			function = getattr(self.lib, name)
			function.argtypes = arguments
			function.restype = result

	def fingerprint(self, pcm: bytes, cancel: threading.Event) -> str:
		"""Fingerprint mono, 11025 Hz, signed 16-bit little-endian decoded audio."""
		if not pcm or len(pcm) % 2:
			raise ChromaprintError("FFmpeg returned empty or incomplete PCM audio.")
		while not _CONTEXT_LOCK.acquire(timeout=0.1):
			if cancel.is_set():
				raise ChromaprintCancelledError
		context = None
		output = ctypes.c_void_p()
		try:
			if cancel.is_set():
				raise ChromaprintCancelledError
			context = self.lib.chromaprint_new(1)  # Default AcoustID algorithm (TEST2).
			if not context or not self.lib.chromaprint_start(context, 11025, 1):
				raise ChromaprintError("Could not initialize Chromaprint.")
			for offset in range(0, len(pcm), 65536):
				if cancel.is_set():
					raise ChromaprintCancelledError
				samples = array("h")
				samples.frombytes(pcm[offset : offset + 65536])
				if sys.byteorder != "little":
					samples.byteswap()
				buffer = (ctypes.c_int16 * len(samples)).from_buffer(samples)
				if not self.lib.chromaprint_feed(context, buffer, len(samples)):
					raise ChromaprintError("Chromaprint could not process this audio.")
			if cancel.is_set():
				raise ChromaprintCancelledError
			if not self.lib.chromaprint_finish(context):
				raise ChromaprintError("Chromaprint could not finish this fingerprint.")
			size = ctypes.c_int()
			if not self.lib.chromaprint_get_raw_fingerprint_size(context, ctypes.byref(size)) or size.value <= 0:
				raise ChromaprintError("This audio is too short to fingerprint.")
			if not self.lib.chromaprint_get_fingerprint(context, ctypes.byref(output)) or not output.value:
				raise ChromaprintError("Chromaprint returned an empty fingerprint.")
			try:
				fingerprint = ctypes.string_at(output).decode("ascii")
			except UnicodeDecodeError as error:
				raise ChromaprintError("Chromaprint returned an invalid fingerprint.") from error
			if not fingerprint:
				raise ChromaprintError("Chromaprint returned an empty fingerprint.")
			return fingerprint
		finally:
			if output.value:
				self.lib.chromaprint_dealloc(output)
			if context:
				self.lib.chromaprint_free(context)
			_CONTEXT_LOCK.release()
