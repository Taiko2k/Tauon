"""Tauon Music Box - Phazor audio backend module"""

# Copyright © 2020, Taiko2k captain(dot)gxj(at)gmail.com

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

import ctypes
import logging
import sys
from http import HTTPStatus

if sys.platform == "win32":
	from ctypes import WINFUNCTYPE
import hashlib
import importlib.machinery
import math
import os.path
import shutil
import subprocess
import sysconfig
import tempfile
import threading
import time
from ctypes import CFUNCTYPE, POINTER, c_char, c_char_p, c_int, c_void_p, cast
from pathlib import Path
from typing import TYPE_CHECKING

import requests
from requests.models import PreparedRequest

from tauon.t_modules.t_enums import PlayerState, PlayingState
from tauon.t_modules.t_extra import Timer, shooter, tmp_cache_dir

if TYPE_CHECKING:
	from ctypes import CDLL

	from tauon.t_modules.t_main import GuiVar, PlayerCtl, Tauon, TrackClass
	from tauon.t_modules.t_prefs import Prefs


class FFRun:
	def __init__(self, tauon: Tauon) -> None:
		self.tauon: Tauon = tauon
		self.decoder = None

	def close(self) -> None:
		if self.decoder:
			self.decoder.terminate()
			if self.decoder.stdin:
				logging.debug("Closing STDIN in FFrun")
				self.decoder.stdin.close()
			if self.decoder.stdout:
				logging.debug("Closing STDOUT in FFrun")
				self.decoder.stdout.close()
			if self.decoder.stderr:
				logging.debug("Closing STDERR in FFrun")
				self.decoder.stderr.close()
			self.decoder.wait()  # Ensure the process fully terminates
		self.decoder = None

	def start(self, uri: bytes, start_ms: int, samplerate: int) -> int:
		self.close()
		ffmpeg_path = self.tauon.get_ffmpeg()
		if ffmpeg_path is None:
			self.tauon.test_ffmpeg()
			return 1
		path = str(ffmpeg_path)
		cmd = [path]
		cmd += ["-loglevel", "quiet"]
		if start_ms > 0:
			cmd += ["-ss", f"{start_ms}ms"]
		cmd += ["-i", uri.decode(), "-acodec", "pcm_s16le", "-f", "s16le", "-ac", "2", "-ar", f"{samplerate}", "-"]
		startupinfo = None
		if sys.platform == "win32":
			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		try:
			self.decoder = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, startupinfo=startupinfo)
		except Exception:
			logging.exception("Failed to start FFmpeg")
			return 1
		return 0

	def read(self, buffer: int, maximum: int) -> int:
		if self.decoder:
			data = self.decoder.stdout.read(maximum)
			p = cast(buffer, POINTER(c_char * maximum))
			p.contents.value = data
			return len(data)
		return 0


class StreamFeeder:
	"""Feeds network audio data into the PHAzOR in-memory stream buffer.

	Implements the producer half of phazor's network byte stream. Polls the
	library for the wanted byte offset, performs HTTP range requests and
	pushes data in as it becomes available. When the decoder seeks outside
	the buffered window, phazor requests a new offset and the feeder
	responds with a new range request.
	"""

	def __init__(self, tauon: Tauon, aud: CDLL) -> None:
		self.tauon = tauon
		self.pctl = tauon.pctl
		self.aud = aud
		self.session = requests.Session()
		self.enabled = True
		self.speed = 0.0  # measured download rate in bytes/sec, 0 when not downloading
		self._speed_bytes = 0
		self._speed_t0 = time.monotonic()
		# Pending request to also save a fully-streamed track to the disk cache
		self._cache_lock = threading.Lock()
		self._cache_request: tuple[TrackClass, str] | None = None
		# Prefetch of the upcoming track's first few MB
		self.prefetch_bytes = 3 * 1000 * 1000
		self._prefetch_session = requests.Session()  # separate from the main loop's
		self._prefetch_lock = threading.Lock()
		self._prefetch_target: TrackClass | None = None  # track to prefetch
		self._prefetch_url: str | None = None  # url of the held prefetch data
		self._prefetch_data: bytes = b""
		self._prefetch_size: int = -1  # full file size if known
		self._prefetch_done: bool = False
		self._prefetching: bool = False
		try:
			aud.net_generation.restype = ctypes.c_int
			aud.net_get_url.restype = ctypes.c_char_p
			aud.net_want.restype = ctypes.c_longlong
			aud.net_want.argtypes = (ctypes.c_int,)
			aud.net_feed.restype = ctypes.c_int
			aud.net_feed.argtypes = (ctypes.c_int, ctypes.c_longlong, ctypes.c_char_p, ctypes.c_int)
			aud.net_set_size.restype = None
			aud.net_set_size.argtypes = (ctypes.c_int, ctypes.c_longlong)
			aud.net_eof.restype = None
			aud.net_eof.argtypes = (ctypes.c_int,)
			aud.net_fail.restype = None
			aud.net_fail.argtypes = (ctypes.c_int,)
			aud.net_set_seekable.restype = None
			aud.net_set_seekable.argtypes = (ctypes.c_int, ctypes.c_int)
			aud.set_load_net.restype = None
			aud.set_load_net.argtypes = (ctypes.c_int,)
		except AttributeError:
			logging.warning("This PHAzOR build does not support network streaming")
			self.enabled = False
			return
		shoot = threading.Thread(target=self._run)
		shoot.daemon = True
		shoot.start()

	def _speed_tick(self, n: int) -> None:
		"""Account n downloaded bytes towards the measured rate"""
		now = time.monotonic()
		self._speed_bytes += n
		elapsed = now - self._speed_t0
		if elapsed >= 0.5:
			self.speed = self._speed_bytes / elapsed
			self._speed_bytes = 0
			self._speed_t0 = now

	def _speed_idle(self) -> None:
		"""Not downloading; the rate is meaningless right now"""
		self.speed = 0.0
		self._speed_bytes = 0
		self._speed_t0 = time.monotonic()

	def request_cache(self, track: TrackClass, url: str) -> None:
		"""Ask the feeder to also save this stream to the disk cache if it
		downloads fully and contiguously. Matched to the stream by URL."""
		with self._cache_lock:
			self._cache_request = (track, url)

	def set_prefetch(self, track: TrackClass | None) -> None:
		"""Set the upcoming track whose start should be prefetched once the
		current stream finishes downloading. Passing a different track (or
		None) discards any previously prefetched data."""
		with self._prefetch_lock:
			if track is self._prefetch_target:
				return
			self._prefetch_target = track
			self._prefetch_url = None
			self._prefetch_data = b""
			self._prefetch_size = -1
			self._prefetch_done = False

	def _resolve_stream_url(self, track: TrackClass) -> str | None:
		"""Resolve a track to a single streamable http(s) URL, or None"""
		try:
			network_url, params = self.pctl.get_url(track)
		except Exception:
			logging.exception("Prefetch: failed to resolve URL")
			return None
		if not isinstance(network_url, str) or not network_url.startswith("http"):
			return None
		if params:
			req = PreparedRequest()
			req.prepare_url(network_url, params)
			return req.url
		return network_url

	def _prefetch_worker(self, track: TrackClass) -> None:
		"""Fetch the first prefetch_bytes of the upcoming track into memory"""
		title = getattr(track, "title", None) or getattr(track, "filename", "?")
		url = None
		data = b""
		size = -1
		try:
			# Skip if it is already fully cached on disk
			cachement = self.tauon.cachement
			if cachement is not None and cachement.get_local_instant(track) is not None:
				logging.info(f"Prefetch: skip '{title}' (already cached)")
				return
			url = self._resolve_stream_url(track)
			if not url:
				logging.info(f"Prefetch: skip '{title}' (no streamable URL)")
				return
			logging.info(f"Prefetch: start '{title}' (up to {self.prefetch_bytes // 1000} KB)")
			resp = self._prefetch_session.get(
				url, headers={"Range": f"bytes=0-{self.prefetch_bytes - 1}"}, stream=True, timeout=(5, 30))
			try:
				if resp.status_code != HTTPStatus.PARTIAL_CONTENT:
					# Without range support we cannot resume after the prefetch,
					# so prefetching would not help
					logging.info(f"Prefetch: skip '{title}' (no range support, status {resp.status_code})")
					return
				total = resp.headers.get("Content-Range", "").rpartition("/")[2]
				if total.isdigit():
					size = int(total)
				buf = bytearray()
				for chunk in resp.iter_content(65536):
					# Abandon if the target changed (queue edit / skip)
					with self._prefetch_lock:
						if self._prefetch_target is not track:
							logging.info(f"Prefetch: abort '{title}' (target changed) after {len(buf) // 1000} KB")
							return
					buf += chunk
					if len(buf) >= self.prefetch_bytes:
						break
				data = bytes(buf)
			finally:
				resp.close()
		except Exception:
			logging.exception(f"Prefetch: download failed for '{title}'")
			return
		finally:
			with self._prefetch_lock:
				if self._prefetch_target is track and url and data:
					self._prefetch_url = url
					self._prefetch_data = data
					self._prefetch_size = size
					self._prefetch_done = True
					logging.info(f"Prefetch: ready '{title}' ({len(data) // 1000} KB of {size // 1000 if size > 0 else '?'} KB)")
				self._prefetching = False

	def _maybe_start_prefetch(self) -> None:
		"""Kick off a background prefetch of the upcoming track if pending"""
		with self._prefetch_lock:
			if self._prefetching or self._prefetch_done:
				return
			track = self._prefetch_target
			if track is None or not getattr(track, "is_network", False):
				return
			self._prefetching = True
		shoot = threading.Thread(target=self._prefetch_worker, args=(track,))
		shoot.daemon = True
		shoot.start()

	def _cache_open(self, track: TrackClass):  # noqa: ANN202 - returns (file, temp, final) or None
		"""Open a temp file in the cache dir for teeing a stream to disk"""
		try:
			cachement = self.tauon.cachement
			if cachement is None:
				return None
			key = cachement.get_key(track)
			if key in cachement.files:
				return None  # already cached
			final_path = os.path.join(cachement.direc, key)
			if os.path.isfile(final_path):
				return None
			fd, temp = tempfile.mkstemp(dir=cachement.direc, suffix=".part")
			return os.fdopen(fd, "wb"), temp, final_path
		except Exception:
			logging.exception("Stream cache: could not open temp file")
			return None

	def _cache_commit(self, track: TrackClass, temp_path: str, final_path: str, size: int) -> None:
		"""Move a completed temp file into the cache and register it with Cachement"""
		try:
			cachement = self.tauon.cachement
			os.replace(temp_path, final_path)
			key = os.path.basename(final_path)
			if key not in cachement.files:
				cachement.files.append(key)
			if key not in cachement.list:
				cachement.list.append(key)
			cachement.trim_cache()
			logging.info(f"Cached streamed track to disk ({size} bytes)")
		except Exception:
			logging.exception("Stream cache: finalize failed")
			try:
				os.remove(temp_path)
			except OSError:
				pass

	def _run(self) -> None:
		aud = self.aud
		gen = -1
		resp = None
		offset = 0
		size = -1
		pending = b""
		no_range = False
		retries = 0

		# Disk-cache tee state for the current stream
		cache_file = None
		cache_temp = None
		cache_final = None
		cache_track = None
		cache_offset = 0  # contiguous bytes written from offset 0
		cache_ok = False

		def close_response() -> None:
			nonlocal resp, pending
			if resp is not None:
				try:
					resp.close()
				except Exception:
					logging.exception("Stream: error closing response")
				resp = None
			pending = b""

		def cache_reset() -> None:
			nonlocal cache_file, cache_temp, cache_final, cache_track, cache_offset, cache_ok
			cache_file = None
			cache_temp = None
			cache_final = None
			cache_track = None
			cache_offset = 0
			cache_ok = False

		def cache_discard() -> None:
			# Abandon an incomplete tee and delete its temp file
			nonlocal cache_file, cache_temp
			if cache_file is not None:
				try:
					cache_file.close()
				except Exception:
					logging.exception("Stream cache: close error")
				if cache_temp:
					try:
						os.remove(cache_temp)
					except OSError:
						pass
			cache_reset()

		def cache_commit() -> None:
			# The whole file was streamed contiguously; persist it
			nonlocal cache_file
			if cache_file is None:
				return
			try:
				cache_file.close()
			except Exception:
				logging.exception("Stream cache: close error")
			self._cache_commit(cache_track, cache_temp, cache_final, cache_offset)
			cache_reset()

		while True:
			try:
				g = aud.net_generation()
				if g == -1:
					close_response()
					cache_discard()
					gen = -1
					self._speed_idle()
					time.sleep(0.04)
					continue
				if g != gen:
					# A new stream was opened
					close_response()
					cache_discard()
					gen = g
					size = -1
					no_range = False
					retries = 0
					# Adopt a pending cache request if it matches this stream
					req = None
					with self._cache_lock:
						if self._cache_request is not None:
							req = self._cache_request
							self._cache_request = None
					try:
						url0 = aud.net_get_url().decode()
					except Exception:
						url0 = ""
					if req is not None and req[1] == url0:
						opened = self._cache_open(req[0])
						if opened is not None:
							cache_file, cache_temp, cache_final = opened
							cache_track = req[0]
							cache_offset = 0
							cache_ok = True

					# Inject prefetched bytes for this stream, if we have them
					inj = None
					with self._prefetch_lock:
						if self._prefetch_done and self._prefetch_data and self._prefetch_url == url0:
							inj_title = getattr(self._prefetch_target, "title", None) or "?"
							inj = (self._prefetch_data, self._prefetch_size)
							self._prefetch_url = None
							self._prefetch_data = b""
							self._prefetch_done = False
							self._prefetch_target = None
					if inj is not None:
						pdata, psize = inj
						if psize > 0:
							aud.net_set_size(gen, psize)
							size = psize
						fpos = 0
						while fpos < len(pdata):
							fed0 = aud.net_feed(gen, fpos, pdata[fpos:], len(pdata) - fpos)
							if fed0 <= 0:
								break
							if cache_file is not None and cache_ok and fpos == cache_offset:
								try:
									cache_file.write(pdata[fpos:fpos + fed0])
									cache_offset += fed0
								except Exception:
									logging.exception("Stream cache: prefetch write error")
									cache_discard()
							fpos += fed0
						offset = fpos
						if offset > 0:
							logging.info(f"Prefetch: used '{inj_title}' (injected {offset // 1000} KB into the stream)")

				want = aud.net_want(gen)
				if want == -2:
					close_response()
					continue
				if want == -1:
					# Buffered through to end of file. If the whole file came
					# down contiguously, persist it to the disk cache.
					close_response()
					self._speed_idle()
					if cache_file is not None and cache_ok and size > 0 and cache_offset >= size:
						cache_commit()
					# Current track is fully buffered; prefetch the next one
					self._maybe_start_prefetch()
					time.sleep(0.05)
					continue

				if pending and offset == want:
					pass  # previous chunk is still waiting to be accepted
				elif resp is None or offset != want:
					# (Re)open the request at the wanted offset
					close_response()
					if no_range and want > 0:
						logging.error("Stream: server does not support range requests")
						aud.net_fail(gen)
						continue
					url = aud.net_get_url().decode()
					try:
						resp = self.session.get(
							url, headers={"Range": f"bytes={want}-"}, stream=True, timeout=(5, 30))
					except Exception:
						logging.exception("Stream: request failed")
						retries += 1
						if retries > 3:
							aud.net_fail(gen)
							retries = 0
						else:
							time.sleep(0.5)
						continue
					code = resp.status_code
					if code == HTTPStatus.PARTIAL_CONTENT:
						total = resp.headers.get("Content-Range", "").rpartition("/")[2]
						if total.isdigit():
							size = int(total)
							aud.net_set_size(gen, size)
					elif code == HTTPStatus.OK and want == 0:
						# Server ignored the range header; play linearly
						no_range = True
						aud.net_set_seekable(gen, 0)
						cl = resp.headers.get("Content-Length", "")
						if cl.isdigit():
							size = int(cl)
							aud.net_set_size(gen, size)
					else:
						logging.error(f"Stream: server returned status {code}")
						close_response()
						aud.net_fail(gen)
						continue
					offset = want
					# Don't tee files larger than the cache limit to disk
					if cache_file is not None and size > 0:
						limit_b = max(self.tauon.prefs.cache_limit, 0) * 1000 * 1000
						if limit_b and size > limit_b:
							cache_discard()

				if not pending:
					try:
						chunk = resp.raw.read(65536)
					except Exception:
						logging.exception("Stream: read failed")
						close_response()
						retries += 1
						if retries > 3:
							aud.net_fail(gen)
							retries = 0
						time.sleep(0.2)
						continue
					if not chunk:
						# End of response body
						close_response()
						if size < 0 or offset >= size:
							aud.net_eof(gen)
							# Whole file streamed contiguously, persist it
							if cache_file is not None and cache_ok and cache_offset == offset:
								cache_commit()
							else:
								cache_discard()
						else:
							# Connection ended early, resume from current offset
							retries += 1
							if retries > 3:
								aud.net_fail(gen)
								retries = 0
							else:
								time.sleep(0.2)
						continue
					retries = 0
					pending = chunk

				fed = aud.net_feed(gen, offset, pending, len(pending))
				if fed in (-1, -2):
					# Stream gone, or a seek redirected the wanted offset
					close_response()
					continue
				if fed == 0:
					# Buffer is full, wait for the player to consume some
					self._speed_tick(0)
					time.sleep(0.05)
					continue
				# Tee contiguous bytes to the disk cache, if enabled. A seek
				# (offset no longer matching the write head) makes a complete
				# file impossible, so the tee is abandoned.
				if cache_file is not None and cache_ok:
					if offset == cache_offset:
						try:
							cache_file.write(pending[:fed])
							cache_offset += fed
						except Exception:
							logging.exception("Stream cache: write error")
							cache_discard()
					else:
						cache_discard()
				offset += fed
				self._speed_tick(fed)
				pending = pending[fed:] if fed < len(pending) else b""
				if size > 0:
					self.pctl.buffering_percent = min(100, int(offset * 100 / size))
			except Exception:
				logging.exception("Stream feeder error")
				close_response()
				time.sleep(0.5)


class Cachement:
	def __init__(self, tauon: Tauon) -> None:
		# fmt:off
		self.tauon        = tauon
		self.gui          = tauon.gui
		self.pctl         = tauon.pctl
		self.prefs        = tauon.prefs
		self.show_message = tauon.show_message
		self.audio_cache  = tauon.cache_directory / "network-audio1"
		self.audio_cache2 = tauon.cache_directory / "audio-cache"
		# fmt:on
		self.direc = str(self.audio_cache2)
		if self.prefs.tmp_cache:
			self.direc = os.path.join(tmp_cache_dir(), "audio-cache")
		if not Path(self.direc).exists():
			os.makedirs(self.direc)
		self.list: list[str] = self.prefs.cache_list
		self.files = os.listdir(self.direc)
		self.get_now = None
		self.running = False
		self.ready = None
		self.error = None

	def get_key(self, track: TrackClass) -> str:
		if track.is_network:
			return hashlib.sha256((str(track.index) + track.url_key).encode()).hexdigest()
		return hashlib.sha256(track.fullpath.encode()).hexdigest()

	def get_file_cached_only(self, track: TrackClass) -> str | None:
		key = self.get_key(track)
		if key in self.files:
			path = Path(self.direc) / key
			if path.is_file():
				return str(path)
		return None

	def get_local_instant(self, track: TrackClass) -> str | None:
		"""Return a complete cached file or existing transcode for this track, if any"""
		path = self.get_file_cached_only(track)
		if path:
			return path
		for codec in (".opus", ".ogg", ".flac", ".mp3"):
			idea = (
				os.path.join(
					self.prefs.encoder_output, self.tauon.encode_folder_name(track), self.tauon.encode_track_name(track)
				)
				+ codec
			)
			if os.path.isfile(idea):
				return idea
		return None

	def get_file(self, track: TrackClass) -> tuple[int, str | None]:
		# 0: file ready
		# 1: file downloading
		# 2: file not found
		if self.error == track:
			return 2, None

		key = self.get_key(track)
		path = os.path.join(self.direc, key)

		if self.running and self.get_now == track:
			return 1, path

		if key in self.files and os.path.isfile(path):
			logging.info("Got cached file")
			self.files.remove(key)
			self.files.append(key)  # bump to top of list
			self.get_now = None
			if not self.running:
				shoot_dl = threading.Thread(target=self.run)
				shoot_dl.daemon = True
				shoot_dl.start()
			return 0, path

		# disable me for debugging
		for codec in (".opus", ".ogg", ".flac", ".mp3"):
			idea = (
				os.path.join(
					self.prefs.encoder_output, self.tauon.encode_folder_name(track), self.tauon.encode_track_name(track)
				)
				+ codec
			)
			if os.path.isfile(idea):
				logging.info("Found transcode")
				return 0, idea

		self.get_now = track
		if not self.running:
			shoot_dl = threading.Thread(target=self.run)
			shoot_dl.daemon = True
			shoot_dl.start()
		return 1, path

	def run(self) -> None:
		self.running = True

		now = self.get_now
		self.get_now = None
		if now is not None:
			error = self.dl_file(now)
			if error:
				self.error = now
				self.running = False
				return

		if self.get_now is None:
			i = 0
			while i < 10:
				time.sleep(0.1)
				i += 1
				if self.get_now is not None:
					self.running = False
					return
			logging.info("Precache next track")
			next_track = self.pctl.advance(dry=True)
			if next_track is not None:
				self.dl_file(self.pctl.get_track(next_track))

		self.trim_cache()
		self.running = False
		return

	def trim_cache(self) -> None:
		# Remove untracked items
		for item in self.files:
			t = os.path.join(self.direc, item)
			if os.path.isfile(t) and item not in self.list:
				os.remove(t)

		# Check total size
		limit = self.prefs.cache_limit
		if self.prefs.tmp_cache:
			limit = 10
		while True:
			s = 0
			for item in list(self.list):
				t = os.path.join(self.direc, item)
				if not os.path.exists(t):
					self.list.remove(item)
					continue
				s += os.path.getsize(t)
			# Removed oldest items if over limit
			if s > limit * 1000 * 1000 and len(self.list) > 3:
				t = os.path.join(self.direc, self.list[0])
				os.remove(t)
				del self.list[0]
			else:
				break

	def dl_file(self, track: TrackClass) -> int | None:
		self.pctl.buffering_percent = 0
		key = self.get_key(track)
		path = Path(self.direc) / key
		if path.exists():
			if not path.is_file():
				return 1
			if key in self.list:
				return 0
			path.unlink()
		if not track.is_network:
			if not Path(track.fullpath).is_file():
				self.error = track
				self.running = False
				return 1

			logging.info("Start transfer")
			timer = Timer()
			target = path.open("wb")
			source = Path(track.fullpath).open("rb")
			while True:
				try:
					data = source.read(128000)
				except Exception:
					logging.exception("Transfer failed.")
					break
				if len(data) > 0:
					logging.info(f"Caching file @ {int(len(data) / timer.hit() / 1000)} kbps")
				else:
					break
				target.write(data)
			target.close()
			source.close()
			logging.info("got file")
			self.files.append(key)
			self.list.append(key)
			return 0

		try:
			logging.info("Download file")

			network_url, params = self.pctl.get_url(track)
			if not network_url:
				logging.info("No URL")
				return 1
			if type(network_url) in (list, tuple) and len(network_url) == 1:
				network_url = network_url[0]
			elif type(network_url) in (list, tuple):
				logging.info("Multi part DL")
				logging.info(path)
				# fmt:off
				ffmpeg_command = [
					str(self.tauon.get_ffmpeg()),
					"-i", "-",      # Input from stdin (pipe the data)
					"-f", "flac",   # Specify FLAC as the output format explicitly
					"-c:a", "copy", # Copy FLAC data without re-encoding
					path,           # Output file for extracted FLAC
				]
				# fmt:on
				p = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)
				i = 0
				for url in network_url:
					i += 1
					logging.info(i)
					response = requests.get(url, timeout=10)
					if response.status_code == HTTPStatus.OK:
						p.stdin.write(response.content)
					else:
						logging.error(f"ERROR CODE: {response.status_code}")
					if i == 3:
						self.ready = track

					self.gui.update += 1
					self.pctl.buffering_percent = math.floor(i / len(network_url) * 100)
					self.gui.buffering_text = str(self.pctl.buffering_percent) + "%"
					if self.get_now is not None and self.get_now != track:
						logging.info("Aborted loading track!")
						return None

				# logging.info("done")
				p.stdin.close()
				p.wait()

				logging.info("Done loading track")
				# self.ready = track
				self.files.append(key)
				self.list.append(key)
				return None

			part = requests.get(network_url, stream=True, params=params, timeout=(3, 10))

			if part.status_code == HTTPStatus.NOT_FOUND:
				self.show_message("Server: File not found", mode="error")
				self.error = track
				return 1
			if part.status_code != HTTPStatus.OK:
				self.show_message("Server Error", mode="error")
				self.error = track
				return 1

		except Exception as e:
			logging.exception("Download failed!")
			self.show_message(_("Error"), str(e), mode="error")
			self.error = track
			return 1

		a = 0
		length = 0
		cl = part.headers.get("Content-Length")
		if cl:
			length = int(cl)
			self.gui.buffering_text = "0%"

		timer = Timer()
		try:
			with path.open("wb") as f:
				for chunk in part.iter_content(chunk_size=1024):
					if chunk:  # filter out keep-alive new chunks
						a += 1
						if a == 3000 and self.prefs.jump_start:  # kilobyes~
							self.ready = track
						if a % 32 == 0:
							# time.sleep(0.03)
							# logging.info(f"Downloading file @ {round(32 / timer.hit())} kbps")
							if length:
								self.gui.update += 1
								self.pctl.buffering_percent = round(a * 1000 / length * 100)
								self.gui.buffering_text = str(round(a * 1000 / length * 100)) + "%"

						if self.get_now is not None and self.get_now != track:
							logging.warning("Aborted loading track!")
							return None

						# if self.cancel is True:
						# 	self.part.close()
						# 	self.status = "failed"
						# 	logging.info("Abort download")
						# 	return

						f.write(chunk)
			logging.info("Done loading track")
			self.ready = track
			self.files.append(key)
			self.list.append(key)
		except Exception:
			logging.exception("Download failed!")
			return 1
		return 0


def find_library(libname: str) -> Path | None:
	"""Search for 'libname.extension' in various formats.

	Return library Path loadable with ctypes.CDLL, otherwise return None
	"""
	# Can look like ~/Projects/Tauon/t_modules
	base_path = Path(__file__).parent
	search_paths: list[Path] = []
	so_extensions = importlib.machinery.EXTENSION_SUFFIXES
	site_packages_path = sysconfig.get_path("purelib")

	# Used to be lib but Slackware uses that for 32-bit,
	# all other distros seem to symlink lib64 to lib, so just use lib64
	libdir = "lib64"

	# Try looking in site-packages of the current environment, pwd and ../pwd
	for extension in so_extensions:
		# fmt:off
		search_paths += [
			(Path(site_packages_path)                        / (libname + extension)).resolve(),
			(Path(base_path)          / ".."                 / (libname + extension)).resolve(),
			(Path(base_path)          / ".." / ".."          / (libname + extension)).resolve(),
			# Compat with old way to store .so files
			(Path(base_path)          / ".." / ".." / libdir / (libname + ".so")).resolve(),
		]
		# fmt:on

	for path in search_paths:
		if path.exists():
			logging.debug(f"Lib {libname} found in {path!s}")
			return path

	# raise OSError(f"Can't find library '{libname}'. Searched at:\n" + "\n".join(str(p) for p in search_paths))
	return None


def get_phazor_path(pctl: PlayerCtl) -> Path:
	"""Locate the PHaZOR library in the specified priority order.

	Tries .so, .dll, .pyd, .dylib in that order and finally uses find_library as a fallback.

	:param pctl: PlayerCtl object containing installation details
	:return: Path to the library file
	:raises Exception: If no library is found
	"""
	# This is where compile-phazor.sh scripts place the dll
	base_path = Path(pctl.install_directory).parent.parent / "build"

	# Define the library name and extensions in priority order
	lib_name = "phazor-pw" if (not pctl.windows and not pctl.tauon.macos) and pctl.prefs.pipewire else "phazor"

	extensions = [".so", ".dll", ".pyd", ".dylib"]

	# Check explicitly for each file
	for ext in extensions:
		lib_path = base_path / f"lib{lib_name}{ext}"
		if lib_path.is_file():
			return lib_path

	# Fallback to find_library. Used if built using setuptools
	lib_path = find_library(lib_name)
	if lib_path:
		return Path(lib_path)

	raise Exception(f"Failed to load PHaZOR library ({lib_name})")


def phazor_exists(pctl: PlayerCtl) -> bool:
	"""Check for the existence of the PHaZOR library on the FS"""
	return get_phazor_path(pctl).exists()


_consecutive_load_failures: int = 0
_load_failure_timer: Timer = Timer()
MAX_CONSECUTIVE_LOAD_FAILURES: int = 5
LOAD_FAILURE_WINDOW: float = 3.0


def player4(tauon: Tauon) -> None:
	global _consecutive_load_failures

	def _handle_load_failure() -> bool:
		global _consecutive_load_failures
		if _load_failure_timer.get() > LOAD_FAILURE_WINDOW:
			_consecutive_load_failures = 0
		_consecutive_load_failures += 1
		_load_failure_timer.set()
		if _consecutive_load_failures >= MAX_CONSECUTIVE_LOAD_FAILURES:
			pctl.stop(run=True)
			if not gui.message_box:
				tauon.show_message(_("Multiple tracks could not be loaded"), mode="warning")
			_consecutive_load_failures = 0
			return True
		return False

	def scan_device() -> None:
		n = aud.scan_devices()
		devices = ["Default"]
		if n:
			for d in range(n):
				st = aud.get_device(d).decode()
				devices.append(st)
		prefs.phazor_devices = devices
		if prefs.phazor_device_selected not in devices:
			prefs.phazor_device_selected = devices[0]

	def pause_when_device_unavailable() -> None:
		pctl.pause_only()

	def calc_rg(track: TrackClass | None) -> float:
		if prefs.replay_gain == 0 and prefs.replay_preamp == 0:
			pctl.active_replaygain = 0
			return 0

		g = 0
		p = 1

		if track is not None:
			tg = track.replaygain_track_gain
			tp = track.replaygain_track_peak
			ag = track.replaygain_album_gain
			ap = track.replaygain_album_peak

			if prefs.replay_gain > 0:
				if prefs.replay_gain == 3 and tg is not None and ag is not None:
					gens = pctl.gen_codes.get(tauon.pl_to_id(pctl.active_playlist_playing))
					if pctl.random_mode or (gens and ("st" in gens or "rt" in gens or "r" in gens)):
						g = tg
						if tp is not None:
							p = tp
					else:
						g = ag
						if ap is not None:
							p = ap
				elif (prefs.replay_gain == 1 and tg is not None) or (
					prefs.replay_gain == 2 and ag is None and tg is not None
				):
					g = tg
					if tp is not None:
						p = tp
				elif ag is not None:
					g = ag
					if ap is not None:
						p = ap
				elif tg is not None and ag is None:
					g = tg
					if tp is not None:
						p = tp

		logging.debug("Detected ReplayGain")
		logging.debug("GAIN: " + str(g))
		logging.debug("PEAK: " + str(p))
		logging.debug("FINAL: " + str(min(10 ** ((g + prefs.replay_preamp) / 20), 1 / p)))

		if p == 0:
			logging.warning("Detected ReplayGain peak of 0")
			return 1
		pctl.active_replaygain = g
		return min(10 ** ((g + prefs.replay_preamp) / 20), 1 / p)

	def set_config(set_device: bool = False) -> None:
		aud.config_set_dev_buffer(prefs.device_buffer)
		aud.config_set_fade_duration(prefs.cross_fade_time)
		st = prefs.phazor_device_selected.encode()
		aud.config_set_dev_name(st)
		if set_device:
			aud.pause()
			aud.wait()
			aud.stop_out()
			aud.wait()
			aud.resume()
		if prefs.always_ffmpeg:
			aud.config_set_always_ffmpeg(1)
		if prefs.volume_power < 0 or prefs.volume_power > 10:
			prefs.volume_power = 2
		aud.config_set_volume_power(prefs.volume_power)
		aud.config_set_resample(prefs.avoid_resampling ^ True)
		if hasattr(aud, "config_set_stream_buffer"):
			aud.config_set_stream_buffer(prefs.stream_buffer)
		apply_eq_settings()

	def normalise_eq_bands() -> list[float]:
		try:
			bands = list(getattr(prefs, "eq", []) or [])
		except TypeError:
			bands = []
		if len(bands) < 10:
			bands.extend([0.0] * (10 - len(bands)))
		elif len(bands) > 10:
			bands = bands[:10]
		out: list[float] = []
		for v in bands:
			try:
				fv = float(v)
			except (TypeError, ValueError):
				fv = 0.0
			out.append(float(max(min(fv, 12.0), -12.0)))
		bands = out
		prefs.eq = bands
		return bands

	def apply_eq_settings() -> None:
		if not hasattr(aud, "eq_set_enable") or not hasattr(aud, "eq_set_band"):
			return
		aud.eq_set_enable(1 if prefs.use_eq else 0)
		for i, gain in enumerate(normalise_eq_bands()):
			aud.eq_set_band(i, ctypes.c_float(gain))

	def run_vis() -> None:
		if gui.turbo:  # and pctl.playing_time > 0.5:
			if gui.vis == 2:
				p_spec: list[float] = []
				aud.get_spectrum(24, bins1)
				bias = 1
				for b in list(bins1):
					p_spec.append(int(b * 1.7 * bias))
					bias += 0.04
				gui.spec = p_spec
				gui.level_update = True
				if pctl.playing_time > 0.5 and (pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM)):
					gui.update_spec = 1
			elif gui.vis == 4:
				p_spec: list[float] = []
				aud.get_spectrum(45, bins2)
				bias = 1
				for b in list(bins2):
					p_spec.append(int(b * 2.0 * bias))
					bias += 0.01
				gui.spec4_array = p_spec
				gui.level_update = True
				if pctl.playing_time > 0.5 and (pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM)):
					gui.update_spec = 1

			# Spectrogram widget: fed independently of gui.vis (own FFT buffers)
			# so it can run alongside the bar visualiser above. Raw log-spaced
			# spectrum columns, queued for SpectrogramWidget (t_custom) to
			# colourise and scroll. Frozen while paused/stopped.
			if gui.spectrogram_in_widget \
					and pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM):
				get_spectrum_spectrogram(len(bins3), bins3)
				gui.spectrogram_buffers.append(list(bins3))
				if len(gui.spectrogram_buffers) > 60:  # UI stalled; drop oldest
					del gui.spectrogram_buffers[0]
				gui.level_update = True
				if pctl.playing_time > 0.5:
					gui.update_spec = 1

	p_sync_timer = Timer()

	def track(end: bool = True) -> None:
		# run_vis() is now driven once per loop iteration in the main player
		# loop (before command processing), so commands can't starve it.

		if end and loaded_track and loaded_track.is_network and pctl.playing_time < 7 and aud.get_result() == 2:
			logging.info("STALL, RETRY")
			time.sleep(0.5)
			pctl.playerCommandReady = True
			pctl.playerCommand = "open"

		add_time = player_timer.hit()
		if add_time > 2:
			add_time = 2
		elif add_time < 0:
			add_time = 0

		# Don't advance the clock while a network stream is (re)buffering, e.g.
		# waiting on a seek's byte range — output is silent until it fills.
		# player_timer was still hit above, so the gap isn't counted later.
		if loaded_track_streamed and aud.is_buffering():
			add_time = 0

		pctl.total_playtime += add_time

		# Wait / speed up, if we are out of sync
		if p_sync_timer.get() > 1:
			real_position = aud.get_position_ms() / 1000
			if real_position and pctl.playing_time and real_position != pctl.last_real_position:
				diff = abs(real_position - pctl.playing_time)
				if 5 > diff > 0.11:  # in a CUE file real will be different that playing time
					# This assumes the first track in a CUE is > 5s
					if real_position < pctl.playing_time:
						add_time -= 5
						add_time = max(add_time, 0)
						p_sync_timer.force_set(2)  # wait for real to catch up again next clock
					else:
						add_time += 0.1
				pctl.last_real_position = real_position  # we still want to move on if playback stalled
			p_sync_timer.set()

		pctl.playing_time += add_time
		pctl.decode_time = pctl.playing_time

		if pctl.playing_time < 3 and pctl.a_time < 3:
			pctl.a_time = pctl.playing_time
		else:
			pctl.a_time += add_time

		tauon.lfm_scrobbler.update(add_time)

		if len(pctl.track_queue) > 0 and 2 > add_time > 0:
			tauon.star_store.add(pctl.track_queue[pctl.queue_step], add_time)
		if end and pctl.playing_time > 1:
			pctl.test_progress()

	def chrome_start(track_id: int, enqueue: bool = False, t: int = 0) -> None:
		track = pctl.get_track(track_id)
		# if track.is_cue:
		# 	logging.error("CUE cast not supported")
		# 	return
		if track.is_network:
			if track.file_ext == "SPTY":
				logging.error("Unsupported network source for cast")
				return
			network_url, params = pctl.get_url(track)
			if params:
				req = PreparedRequest()
				req.prepare_url(network_url, params)
				network_url = req.url

			tauon.chrome.start(track.index, enqueue=enqueue, url=network_url, t=t)
		else:
			tauon.chrome.start(track.index, enqueue=enqueue, t=t)

	# fmt:off
	gui   = tauon.gui
	pctl  = tauon.pctl
	prefs = tauon.prefs
	# fmt:on
	logging.debug("Starting PHAzOR backend…")

	player_timer = Timer()
	loaded_track = None
	fade_time = 400

	aud = tauon.aud

	aud.config_set_dev_name(prefs.phazor_device_selected.encode())

	aud.init()

	aud.get_device.restype = ctypes.c_char_p

	aud.feed_raw.argtypes = (ctypes.c_int, ctypes.c_char_p)
	aud.feed_raw.restype = None
	aud.set_volume(int(pctl.player_volume))

	try:
		aud.eq_set_enable.argtypes = (ctypes.c_int,)
		aud.eq_set_enable.restype = None
		aud.eq_set_band.argtypes = (ctypes.c_int, ctypes.c_float)
		aud.eq_set_band.restype = None
	except AttributeError:
		logging.warning("PHAzOR build does not expose EQ controls")

	bins1 = (ctypes.c_float * 24)()
	bins2 = (ctypes.c_float * 45)()
	bins3 = (ctypes.c_float * gui.spectrogram_bins)()  # spectrogram widget columns
	try:
		# Doubled (4096-sample) analysis window, own C-side buffers — the
		# standard get_spectrum path the other visualisers use is untouched.
		get_spectrum_spectrogram = aud.get_spectrum_hires
	except AttributeError:  # older libphazor build
		get_spectrum_spectrogram = aud.get_spectrum

	aud.get_level_peak_l.restype = ctypes.c_float
	aud.get_level_peak_r.restype = ctypes.c_float

	active_timer = Timer()

	scan_device()
	ff_run = FFRun(tauon)

	if sys.platform == "win32":
		FUNCTYPE = WINFUNCTYPE
	else:
		FUNCTYPE = CFUNCTYPE
	start_callback = FUNCTYPE(c_int, c_char_p, c_int, c_int)(ff_run.start)
	read_callback = FUNCTYPE(c_int, c_void_p, c_int)(ff_run.read)
	close_callback = FUNCTYPE(c_void_p)(ff_run.close)
	device_unavailable_callback = FUNCTYPE(c_void_p)(pause_when_device_unavailable)
	aud.set_callbacks(start_callback, read_callback, close_callback, device_unavailable_callback)

	cachement = tauon.cachement
	feeder = StreamFeeder(tauon, aud)
	tauon.stream_feeder = feeder  # the console graph reads download stats from here
	stream_unsupported: set[int] = set()  # tracks that failed direct streaming this session
	loaded_track_streamed = False

	def set_load_net(n: int) -> None:
		if feeder.enabled:
			aud.set_load_net(n)

	# aud.config_set_samplerate(prefs.samplerate)
	aud.config_set_resample_quality(prefs.resample)

	set_config()

	stall_timer = Timer()
	wall_timer = Timer()

	chrome_update = 0
	chrome_cool_timer = Timer()
	chrome_mode = False

	while True:
		# logging.error(aud.print_status())
		time.sleep(0.016)
		if tauon.player4_state == PlayerState.PAUSED:
			time.sleep(0.05)
		if tauon.player4_state != PlayerState.STOPPED or tauon.chrome_mode:
			active_timer.set()
		if active_timer.get() > 7:
			aud.stop()
			aud.phazor_shutdown()
			break

		# Level meter
		if (tauon.player4_state in (PlayerState.PLAYING, PlayerState.URL_STREAM)) and gui.vis == 1:
			amp = aud.get_level_peak_l()
			l = amp * 12
			amp = aud.get_level_peak_r()
			r = amp * 12

			tauon.level_train.append((0, l, r))
			gui.level_update = True

		if chrome_mode:
			if tauon.chrome is None:
				logging.critical("This should not happen, tauon.chrome was None")
				return
			if pctl.playerCommandReady:
				command = pctl.playerCommand
				# logging.info(command)
				subcommand = pctl.playerSubCommand
				pctl.playerSubCommand = ""
				pctl.playerCommandReady = False

				if command == "endchrome":
					chrome_mode = False
					tauon.player4_state = PlayerState.STOPPED
					pctl.playing_time = 0
					pctl.decode_time = 0
					pctl.stop()
					continue
				if command == "open":
					target_object = pctl.target_object
					if tauon.player4_state == PlayerState.PLAYING:
						t, pid, s, d = tauon.chrome.update()
						# logging.info((t, d))
						# logging.info(d - t)

						if d and t and 1 < d - t < 5:
							# logging.info("Enqueue next chromecast")
							chrome_start(target_object.index, enqueue=True, t=pctl.start_time_target)
							chrome_cool_timer.set()
							time.sleep(d - t)
							if pctl.commit:
								pctl.advance(quiet=True, end=True)
								pctl.commit = None
							continue

					chrome_start(target_object.index, t=pctl.start_time_target)
					chrome_cool_timer.set()
					if pctl.commit:
						pctl.advance(quiet=True, end=True)
						pctl.commit = None
					tauon.player4_state = PlayerState.PLAYING
				if command == "pauseon":
					tauon.chrome.pause()
					tauon.player4_state = PlayerState.PAUSED
				if command == "pauseoff":
					tauon.chrome.play()
					tauon.player4_state = PlayerState.PLAYING
				if command == "volume":
					tauon.chrome.volume(round(pctl.player_volume / 100, 3))
					tauon.player4_state = PlayerState.PLAYING
				if command == "seek":
					tauon.chrome.seek(float(round(pctl.new_time + pctl.start_time_target, 2)))
					chrome_cool_timer.set()
					pctl.playing_time = pctl.new_time
					pctl.decode_time = pctl.playing_time
				if command == "seteq":
					apply_eq_settings()
				if command == "stop":
					tauon.player4_state = PlayerState.STOPPED
					tauon.chrome.stop()

			if tauon.player4_state == PlayerState.PLAYING:
				if chrome_update > 0.8 and chrome_cool_timer.get() > 2.5:
					t, pid, s, d = tauon.chrome.update()
					pctl.playing_time = t - pctl.start_time_target
					pctl.decode_time = t - pctl.start_time_target
					player_timer.hit()
					chrome_update = 0

				add_time = player_timer.hit()
				add_time = min(add_time, 2)
				chrome_update += add_time
				pctl.a_time += add_time
				tauon.lfm_scrobbler.update(add_time)
				pctl.total_playtime += add_time
				if len(pctl.track_queue) > 0 and 2 > add_time > 0:
					tauon.star_store.add(pctl.track_queue[pctl.queue_step], add_time)

				pctl.test_progress()

			time.sleep(0.1)
			continue

		# Feed the visualisers once per loop iteration, independent of command
		# handling. run_vis() used to run only in the play branch below (via
		# track() / the URL_STREAM path), so a burst of commands would keep
		# taking the command branch and starve it — most visibly, holding the
		# volume bar fires a "volume" command every frame, which froze the
		# spectrogram scroll. Chrome playback already returned above, so this
		# only covers local output.
		if tauon.player4_state in (PlayerState.PLAYING, PlayerState.URL_STREAM):
			run_vis()

		# Command processing
		if pctl.playerCommandReady:
			command = pctl.playerCommand
			subcommand = pctl.playerSubCommand
			pctl.playerSubCommand = ""
			pctl.playerCommandReady = False
			# logging.info(command)

			if command == "startchrome":
				aud.stop()
				if tauon.player4_state == PlayerState.PLAYING:
					chrome_start(loaded_track.index, t=pctl.playing_time)
				chrome_mode = True

			if command == "reload":
				set_config()
			if command == "set-device":
				set_config(set_device=True)

			if command == "url":
				pctl.download_time = 0
				w = 0
				if not tauon.radiobox.run_proxy:
					set_load_net(0)
					aud.start(pctl.url.encode(), 0, 0, ctypes.c_float(calc_rg(None)))
					tauon.player4_state = PlayerState.URL_STREAM
					player_timer.hit()
				else:
					while len(tauon.stream_proxy.chunks) < 200:
						time.sleep(0.1)
						w += 1
						if w > 100:
							logging.info("Taking too long!")
							tauon.stream_proxy.stop()
							pctl.playerCommand = "stop"
							pctl.playerCommandReady = True
							break
					else:
						aud.config_set_feed_samplerate(prefs.samplerate)
						set_load_net(0)
						aud.start(b"RAW FEED", 0, 0, ctypes.c_float(calc_rg(None)))
						tauon.player4_state = PlayerState.URL_STREAM
						player_timer.hit()

			if command == "open":
				if tauon.player4_state == PlayerState.PAUSED:
					aud.set_volume(int(pctl.player_volume))

				stall_timer.set()
				pctl.download_time = 0
				target_object = pctl.target_object
				if not target_object:
					logging.exception("This shouldn't happen, target_object was None")
					continue
				target_path = target_object.fullpath
				subtrack = target_object.subtrack
				aud.set_subtrack(subtrack)

				logging.info(
					f"Open - requested start was {(pctl.start_time_target + pctl.jump_time)} ({pctl.start_time_target})"
				)
				try:
					logging.info(f"Extension: {target_path.split('.')[-1]}")
				except Exception:
					logging.exception("Failed to get extension - maybe file name does not have any dots?")

				stream_url: str | None = None
				if target_object.is_network:
					if target_object.file_ext == "SPTY":
						logging.warning("This network source is no longer supported")
						target_object.found = False
						pctl.playing_state = PlayingState.STOPPED
						pctl.jump_time = 0.0
						continue

					# Prefer an already complete local copy (cache or transcode)
					instant = cachement.get_local_instant(target_object)

					if instant is None and feeder.enabled and prefs.network_stream \
							and target_object.index not in stream_unsupported:
						try:
							network_url, params = pctl.get_url(target_object)
						except Exception:
							logging.exception("Failed to resolve track URL")
							network_url = None
							params = None
						# Multi-part urls (some Tidal tracks) use the download path
						if isinstance(network_url, str) and network_url.startswith("http"):
							if params:
								req = PreparedRequest()
								req.prepare_url(network_url, params)
								stream_url = req.url
							else:
								stream_url = network_url

					if instant:
						target_path = instant
					elif stream_url:
						# Stream directly; phazor pulls the data through the feeder
						logging.info("Direct stream network track")
						target_path = stream_url
						# With the persistent cache enabled, also save the
						# stream to disk if it downloads fully (tmp_cache off
						# means the persistent cache is selected)
						if not prefs.tmp_cache:
							feeder.request_cache(target_object, stream_url)
					else:
						while True:
							status, path = cachement.get_file(target_object)

							if status in (0, 2):
								break
							# status 1: the track is uncached and downloading,
							# show buffering immediately
							if gui.buffering is False:
								gui.buffering_text = ""
								pctl.buffering_percent = 0
								gui.buffering = True
								gui.update += 1
								tauon.wake()
							if cachement.ready == target_object and pctl.start_time_target + pctl.jump_time == 0.0:
								break
							time.sleep(0.05)
							# logging.info(status)

						gui.buffering = False
						gui.update += 1
						tauon.wake()

						if status == 2:
							logging.info("Could not locate resource")
							target_object.found = False
							pctl.playing_state = PlayingState.STOPPED
							pctl.jump_time = 0.0
							# pctl.advance(inplace=True, play=True)
							continue
						target_path = path

				elif prefs.precache:
					timer = Timer()
					timer.set()
					while True:
						status, path = cachement.get_file(target_object)
						if status in (0, 2):
							break
						if timer.get() > 0.25 and gui.buffering is False:
							gui.buffering_text = ""
							pctl.buffering_percent = 0
							gui.buffering = True
							gui.update += 1
							tauon.wake()

						time.sleep(0.05)

					gui.buffering = False
					gui.update += 1
					tauon.wake()

					if status == 2:
						target_object.found = False
						pctl.playing_state = PlayingState.STOPPED
						pctl.jump_time = 0.0
						if _handle_load_failure():
							continue
						pctl.advance(inplace=True, play=True)
						continue
					target_path = path

				if stream_url is None and not os.path.isfile(target_path):
					target_object.found = False
					if not target_object.is_network:
						pctl.playing_state = PlayingState.STOPPED
						pctl.jump_time = 0.0
						if _handle_load_failure():
							continue
						pctl.advance(inplace=True, play=True)
					continue
				_consecutive_load_failures = 0
				if not target_object.found:
					pctl.reset_missing_flags()

				# Tell the feeder which track to prefetch next, so its start
				# can be injected straight into the buffer when it plays
				if feeder.enabled and prefs.network_stream:
					try:
						nxt = pctl.advance(dry=True)
						feeder.set_prefetch(pctl.get_track(nxt) if nxt is not None else None)
					except Exception:
						logging.exception("Failed to set prefetch target")

				length: float = 0
				remain: float = 0
				position: float = 0

				if target_path and target_object and stream_url is None and target_object.length == 0 and not target_object.is_cue:
					logging.info("Track has duration of 0, scanning file")
					temp = tauon.TrackClass()
					temp.fullpath = target_path
					tauon.tag_scan(temp)
					target_object.length = temp.length
					if pctl.playing_object() is target_object:
						pctl.playing_length = target_object.length
					del temp

				if (
					tauon.player4_state == PlayerState.PLAYING
					and not pctl.start_time_target
					and not pctl.jump_time
					and loaded_track
				):
					length = aud.get_length_ms() / 1000
					position = aud.get_position_ms() / 1000
					remain = length - position

					# TODO(Martin): The GUI logger does not support multiline
					# logging.info(f"{loaded_track.title} -> {target_object.title}\nlength: {length!s}\nposition: {position!s}\nWe are {remain!s} from end")
					logging.info(f"{loaded_track.title} -> {target_object.title}")
					logging.info(f" --- length: {length!s}")
					logging.info(f" --- position: {position!s}")
					logging.info(f" --- We are {remain!s} from end")

					# Directly streamed tracks report an accurate duration from
					# the decoder; the metadata fallback is for the legacy
					# cache path where the file may still be growing
					if (loaded_track.is_network and not loaded_track_streamed) or length == 0:
						logging.warning("Phazor did not respond with a duration")
						length = loaded_track.length
						remain = length - position

				fade = 0
				error = False
				target_gapless_ready = (
					not target_object.is_network
					or stream_url is not None
					or cachement.get_file_cached_only(target_object) is not None
				)
				if (
					tauon.player4_state == PlayerState.PLAYING
					and length
					and position
					and not pctl.start_time_target
					and not pctl.jump_time
					and loaded_track
					and 0 < remain < 5.5
					and not loaded_track.is_cue
					and target_gapless_ready
					and subcommand != "now"
				):
					logging.info("Transition gapless")

					r_timer = Timer()
					r_timer.set()

					if loaded_track and loaded_track.file_ext.lower() in tauon.formats.GME:
						# GME formats dont have a physical end so we don't do gapless
						while r_timer.get() <= remain - prefs.device_buffer / 1000:
							if pctl.commit:
								track(end=False)
							time.sleep(0.016)
						aud.stop()

					set_load_net(1 if stream_url else 0)
					aud.next(
						target_path.encode(),
						int((pctl.start_time_target + pctl.jump_time) * 1000),
						ctypes.c_float(calc_rg(target_object)),
					)

					cont = False
					check_timer = Timer()
					check_timer.set()
					r_timer_saved = 0.0
					while True:
						if tauon.player4_state != PlayerState.PAUSED:
							if r_timer.get() > remain - prefs.device_buffer / 1000:
								break
						if pctl.commit and tauon.player4_state == PlayerState.PLAYING:
							track(end=False)
						time.sleep(0.016)
						if pctl.playerCommandReady and pctl.playerCommand in ("open", "stop"):
							logging.info("JANK")
							pctl.commit = None
							break
						if pctl.playerCommandReady and pctl.playerCommand == "seek":
							logging.info("Seek revert gapless")
							pctl.commit = None
							pctl.jump(loaded_track.index, jump=True)
							pctl.jump_time = pctl.new_time
							pctl.playing_time = pctl.new_time
							pctl.decode_time = pctl.new_time
							cont = True
							break
						if pctl.playerCommandReady and pctl.playerCommand == "pauseon":
							pctl.playerCommandReady = False
							tauon.player4_state = PlayerState.PAUSED
							pctl.playerCommand = ""
							aud.pause()
							r_timer_saved = r_timer.get()
						if pctl.playerCommandReady and pctl.playerCommand == "pauseoff":
							pctl.playerCommandReady = False
							tauon.player4_state = PlayerState.PLAYING
							pctl.playerCommand = ""
							aud.resume()
							player_timer.set()
							r_timer.force_set(r_timer_saved)
						if pctl.playerCommandReady and pctl.playerCommand == "volume":
							aud.ramp_volume(int(pctl.player_volume), 750)
							pctl.playerCommandReady = False
							pctl.playerCommand = ""

						if tauon.player4_state == PlayerState.PLAYING and check_timer.get() > 0.5:
							check_timer.set()
							abort_gapless = False
							if pctl.stop_mode in (1, 3):
								abort_gapless = True
							elif pctl.stop_mode in (2, 4) and pctl.commit:
								tr = pctl.playing_object()
								tr2 = pctl.get_track(pctl.commit)
								if tr and tr2 and (tr.parent_folder_path, tr.album) != (tr2.parent_folder_path, tr2.album):
									abort_gapless = True

							queue_override = pctl.force_queue and not pctl.pause_queue
							deterministic_next = queue_override or not pctl.random_mode
							if not abort_gapless and pctl.commit and deterministic_next:
								next_commit = pctl.advance(quiet=True, end=True, dry=True)
								repeat_self_commit = (
									subcommand == "repeat"
									and pctl.commit == loaded_track.index
									and target_object.index == loaded_track.index
									and not (pctl.force_queue and not pctl.pause_queue)
								)
								if next_commit != pctl.commit and not repeat_self_commit:
									abort_gapless = True

							if abort_gapless:
								resume_time = pctl.playing_time
								logging.info("Queue or stop mode revert gapless")
								pctl.abort_gapless_transition(loaded_track, resume_time)
								cont = True
								break

					if cont:
						continue
					if pctl.commit is not None:
						pctl.playing_time = 0
						pctl.decode_time = 0
						match = pctl.commit
						if match == loaded_track.index and subcommand == "repeat":
							pctl.update_change()
						else:
							pctl.advance(quiet=True, end=True)
						pt = pctl.playing_object()
						if pt and pt.index != match:
							logging.info("MISSFIRE")
							pctl.play_target()
							continue
						if pctl.playerCommandReady and pctl.playerCommand == "open":
							pctl.playerCommandReady = False
							pctl.playerCommand = ""

					loaded_track = target_object
					loaded_track_streamed = stream_url is not None
					pctl.playing_time = pctl.jump_time
				else:
					if pctl.commit and subcommand != "repeat":
						pctl.advance(quiet=True, end=True)
						pctl.commit = None
						continue

					if tauon.player4_state == PlayerState.PLAYING and prefs.use_jump_crossfade:
						fade = 1

					logging.info("Transition jump")
					# An uncached network stream isn't ready to play yet; show
					# buffering immediately and keep it until the play loop sees
					# the decoder has filled (is_buffering() clears).
					if stream_url and gui.buffering is False:
						gui.buffering = True
						gui.buffering_text = ""
						pctl.buffering_percent = 0
						gui.update += 1
						tauon.wake()
					set_load_net(1 if stream_url else 0)
					aud.start(
						target_path.encode(errors="surrogateescape"),
						int((pctl.start_time_target + pctl.jump_time) * 1000),
						fade,
						ctypes.c_float(calc_rg(target_object)),
					)
					loaded_track = target_object
					loaded_track_streamed = stream_url is not None
					pctl.playing_time = pctl.jump_time
					if pctl.jump_time:
						while aud.get_result() == 0:
							if stream_url and pctl.playerCommandReady and pctl.playerCommand in ("stop", "open"):
								break
							time.sleep(0.016)
							run_vis()
						aud.set_position_ms(int(pctl.jump_time * 1000))

					# Restart track is failed to load (for some network tracks) (broken with gapless loading)
					stream_fallback = False
					buff_timer = Timer()
					while True:
						r = aud.get_result()
						if r == 1:
							break
						if r == 2:
							if stream_url:
								# Direct streaming didn't work out; fall back
								# to the legacy download-to-cache path
								logging.warning("Direct stream failed, falling back to download")
								stream_unsupported.add(target_object.index)
								pctl.playerCommand = "open"
								pctl.playerCommandReady = True
								stream_fallback = True
								break
							if loaded_track.is_network:
								pctl.buffering_percent = 0
								gui.buffering = True
								gui.buffering_text = ""

								# while dm.request(loaded_track, whole=True) == "wait":
								# 	time.sleep(0.05)
								# 	if pctl.playerCommandReady:
								# 		break
								logging.info("Retry start file")
								set_load_net(0)
								aud.start(
									target_path.encode(),
									int((pctl.start_time_target + pctl.jump_time) * 1000),
									fade,
									ctypes.c_float(calc_rg(target_object)),
								)
								gui.buffering = False
								player_timer.set()
								break
							aud.stop()
							if not gui.message_box:
								tauon.show_message(_("Error loading track"), mode="warning")
							error = True
							break
						if stream_url:
							# Keep commands responsive if the network stalls during load
							if pctl.playerCommandReady and pctl.playerCommand in ("stop", "open"):
								logging.info("Command received while stream loading, cancel load")
								aud.stop()
								error = True
								break
							if buff_timer.get() > 0.25 and gui.buffering is False:
								gui.buffering_text = ""
								pctl.buffering_percent = 0
								gui.buffering = True
								gui.update += 1
								tauon.wake()
						time.sleep(0.016)
						run_vis()

					# For a successful direct stream, the decoder has loaded but
					# the PCM buffer may still be filling; leave the buffering
					# flag for the play loop to clear once is_buffering() reports
					# ready. Clear now for non-streamed tracks (ready already) or
					# if the load errored/aborted (the play loop won't run).
					if gui.buffering and (error or not loaded_track_streamed):
						gui.buffering = False
						gui.update += 1
						tauon.wake()
					if stream_fallback:
						continue

					tauon.player4_state = PlayerState.PLAYING
					if error:
						tauon.player4_state = PlayerState.STOPPED

				player_timer.set()
				pctl.jump_time = 0.0
				if loaded_track.length == 0 or loaded_track.file_ext.lower() in tauon.formats.MOD:
					i = 0
					t = 0
					while t == 0:
						time.sleep(0.3)
						t = aud.get_length_ms() / 1000
						i += 1
						if i > 9:
							break
					loaded_track.length = t
					if loaded_track.length != 0:
						pctl.playing_length = loaded_track.length
						gui.pl_update += 1

				pctl.commit = None
				stall_timer.set()
				wall_timer.force_set(3)

			if command == "seek":
				if tauon.player4_state != PlayerState.STOPPED:
					if loaded_track.is_network and loaded_track_streamed:
						# Direct streams seek natively; the decoder requests
						# the byte range it needs through the feeder. Show the
						# buffering state right away — the play loop freezes the
						# clock and clears this once the new position has filled.
						aud.seek(int((pctl.new_time + pctl.start_time_target) * 1000), prefs.pa_fast_seek)
						if gui.buffering is False:
							gui.buffering = True
							gui.buffering_text = ""
							gui.update += 1
							tauon.wake()
					elif loaded_track.is_network:  # and loaded_track.fullpath.endswith(".ogg"):
						timer = Timer()
						timer.set()
						i = 0
						while True:
							status, path = cachement.get_file(loaded_track)
							if status == 1:
								per = (pctl.new_time / loaded_track.length) * 100
								if per < 1:
									break
								if pctl.buffering_percent - per > 5:
									break
							if status in (0, 2):
								break
							if timer.get() > 0.25 and gui.buffering is False:
								gui.buffering_text = ""
								pctl.buffering_percent = 0
								gui.buffering = True
								gui.update += 1
								tauon.wake()
							if i * 0.05 > 2:
								aud.pause()
							if pctl.playerCommandReady:
								break

							time.sleep(0.05)
							i += 1

						gui.buffering = False
						gui.update += 1
						tauon.wake()
						if pctl.playerCommandReady:
							continue

						if status == 2:
							loaded_track.found = False
							pctl.playing_state = PlayingState.STOPPED
							pctl.jump_time = 0.0
							pctl.stop()
							continue

						# The vorbis decoder doesn't like appended files
						set_load_net(0)
						aud.start(
							path.encode(),
							int(pctl.new_time + pctl.start_time_target) * 1000,
							0,
							ctypes.c_float(calc_rg(loaded_track)),
						)
						while aud.get_result() == 0:
							time.sleep(0.01)
					else:
						aud.seek(int((pctl.new_time + pctl.start_time_target) * 1000), prefs.pa_fast_seek)

					pctl.playing_time = pctl.new_time

				pctl.decode_time = pctl.playing_time
				wall_timer.set()
				player_timer.set()

			if command == "volume":
				aud.ramp_volume(int(pctl.player_volume), 750)

			if command == "seteq":
				apply_eq_settings()

			if command == "runstop":
				length = aud.get_length_ms() / 1000
				position = aud.get_position_ms() / 1000
				remain = length - position
				# logging.info("length: " + str(length))
				# logging.info("position: " + str(position))
				# logging.info("We are %s from end" % str(remain))
				time.sleep(3)
				command = "stop"

			if command == "stop":
				if prefs.use_pause_fade and tauon.player4_state != PlayerState.URL_STREAM:
					if pctl.player_volume > 5:
						speed = fade_time / (int(pctl.player_volume) / 100)
					else:
						speed = fade_time / (5 / 100)

					aud.ramp_volume(0, int(speed))
					time.sleep((fade_time + 100) / 1000)

				tauon.player4_state = PlayerState.STOPPED
				pctl.playing_time = 0
				aud.stop()
				time.sleep(0.1)
				aud.set_volume(int(pctl.player_volume))

				# Clear any buffering indicator; the play loop will not run now
				if gui.buffering:
					gui.buffering = False
					gui.update += 1
					tauon.wake()

				if subcommand == "return":
					pctl.playerSubCommand = "stopped"
					# pctl.playerCommandReady = True

			if command == "pauseon":
				if prefs.use_pause_fade:
					if pctl.player_volume > 5:
						speed = fade_time / (int(pctl.player_volume) / 100)
					else:
						speed = fade_time / (5 / 100)

					aud.ramp_volume(0, int(speed))
					time.sleep((fade_time + 100) / 1000)
				aud.pause()
				tauon.player4_state = PlayerState.PAUSED

			if command == "pauseoff":
				if tauon.player4_state == PlayerState.STOPPED:
					t = pctl.playing_time
					pctl.play_target()
					pctl.jump_time = t
					pctl.playing_time = t
					pctl.decode_time = t
				else:
					if prefs.use_pause_fade:
						if pctl.player_volume > 5:
							speed = fade_time / (int(pctl.player_volume) / 100)
						else:
							speed = fade_time / (5 / 100)

						aud.ramp_volume(int(pctl.player_volume), int(speed))
					aud.resume()
					player_timer.set()
					stall_timer.set()
					tauon.player4_state = PlayerState.PLAYING

			if command == "unload":
				if prefs.use_pause_fade:
					if pctl.player_volume > 5:
						speed = fade_time / (int(pctl.player_volume) / 100)
					else:
						speed = fade_time / (5 / 100)

					aud.ramp_volume(0, int(speed))
					time.sleep((fade_time + 100) / 1000)

				aud.stop()
				aud.phazor_shutdown()

				if cachement.audio_cache.exists():
					shutil.rmtree(cachement.audio_cache)

				pctl.playerCommand = "done"
				pctl.playerCommandReady = True
				break
		else:
			if tauon.player4_state == PlayerState.URL_STREAM:
				pctl.radio_progress()
				# run_vis() runs once per iteration at the top of the loop now.

				add_time = player_timer.hit()
				pctl.playing_time += add_time
				pctl.decode_time = pctl.playing_time

				buffering = aud.is_buffering()
				if gui.buffering != buffering:
					gui.buffering = buffering
					gui.update += 1

			if tauon.player4_state == PlayerState.PLAYING:
				if loaded_track_streamed:
					# Surface buffering state if the network can't keep up
					buffering = aud.is_buffering()
					if gui.buffering != buffering:
						gui.buffering = buffering
						gui.buffering_text = ""
						gui.update += 1
						tauon.wake()
				track()
