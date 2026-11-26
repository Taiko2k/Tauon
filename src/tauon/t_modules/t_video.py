"""Video playback in the art boxes.

PHAzOR plays the file's audio through its FFmpeg path as with any other track.
A second FFmpeg process decodes the picture to RGBA frames, already scaled to
the pixel size they're shown at, and each frame is shown once the heard audio
position reaches its timestamp.
"""
from __future__ import annotations

import contextlib
import logging
import re
import subprocess
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tauon.t_modules import t_native as sdl3
from tauon.t_modules.t_enums import PlayingState

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Tauon, TrackClass

VIDEO_EXTENSIONS = {"mp4", "m4v", "webm", "mkv", "avi", "mov"}

# Longest edge decoded, whatever the box: beyond this SDL upscales
MAX_EDGE = 3840
# Decoded frames held ahead of the clock
QUEUE_FRAMES = 4

_SHOWINFO = re.compile(r"\]\s+n:\s*\d+\s+pts:\s*\S+\s+pts_time:(\S+).*?\ss:(\d+)x(\d+)")
_DURATION = re.compile(r"^\s*Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")
_METADATA = re.compile(r"^\s{4}(\w+)\s*:\s?(.*)$")
_NO_VIDEO = ("matches no streams", "does not contain any stream")


def startup_info() -> subprocess.STARTUPINFO | None:
	if sys.platform != "win32":
		return None
	info = subprocess.STARTUPINFO()
	info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
	return info


def fit(box: tuple[int, int], aspect: float) -> tuple[int, int]:
	"""Largest size of the given aspect inside box"""
	w, h = box
	if w <= 0 or h <= 0 or aspect <= 0:
		return 0, 0
	if w / h > aspect:
		return max(1, round(h * aspect)), h
	return w, max(1, round(w / aspect))


def ffmpeg_probe(ffmpeg: str, path: str) -> tuple[float, dict[str, str]]:
	"""Duration and container tags from FFmpeg's own report, for when ffprobe is missing"""
	result = subprocess.run(
		[ffmpeg, "-hide_banner", "-nostdin", "-i", path],
		stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, startupinfo=startup_info(), check=False, timeout=20)
	duration = 0.0
	tags: dict[str, str] = {}
	in_metadata = False
	for line in result.stderr.decode(errors="replace").splitlines():
		match = _DURATION.match(line)
		if match:
			duration = int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))
			in_metadata = False
			continue
		if line.startswith("  Metadata:"):
			in_metadata = True
			continue
		if line.lstrip().startswith("Stream #"):
			break
		if in_metadata:
			match = _METADATA.match(line)
			if match:
				tags.setdefault(match.group(1).lower(), match.group(2).strip())
	return duration, tags


@dataclass
class Frame:
	pts: float
	w: int
	h: int
	data: bytes


class VideoDecoder:
	"""One FFmpeg process decoding the first video stream from `start`, fitted to `box`.

	showinfo logs each frame's timestamp and size to stderr before the frame
	is written to stdout, so the nth log line describes the nth frame.
	"""

	def __init__(self, ffmpeg: str, path: str, start: float, box: tuple[int, int], checksum_option: bool = True) -> None:
		self.path = path
		self.start = start
		self.box = box
		self.started_at = time.monotonic()
		self.frames: deque[Frame] = deque()
		self.cond = threading.Condition()
		self.headers: deque[tuple[float, int, int]] = deque()
		self.log_done = False
		self.finished = False
		self.closed = False
		self.produced = 0
		self.last_pts = start
		self.errors: deque[str] = deque(maxlen=12)

		bw = max(2, min(box[0], MAX_EDGE))
		bh = max(2, min(box[1], MAX_EDGE))
		# Fit inside the box in square pixels without upscaling past the source;
		# Lanczos with full chroma keeps small sizes clean
		vf = (
			f"scale=w='trunc(min(min({bw},{bh}*dar),iw*sar)/2)*2':h='trunc(ow/dar/2)*2'"
			":flags=lanczos+accurate_rnd+full_chroma_int,format=rgba,setsar=1,"
			+ ("showinfo=checksum=0" if checksum_option else "showinfo"))
		cmd = [ffmpeg, "-hide_banner", "-nostats", "-nostdin", "-loglevel", "info"]
		if start > 0:
			cmd += ["-ss", f"{start:.3f}"]
		cmd += ["-i", path, "-map", "0:V:0", "-an", "-sn", "-dn", "-vf", vf, "-f", "rawvideo", "-"]
		self.proc = subprocess.Popen(
			cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
			startupinfo=startup_info())
		threading.Thread(target=self._read_log, daemon=True).start()
		threading.Thread(target=self._read_frames, daemon=True).start()

	def _read_log(self) -> None:
		try:
			for raw in self.proc.stderr:
				line = raw.decode(errors="replace").rstrip()
				match = _SHOWINFO.search(line)
				if match:
					try:
						pts = float(match.group(1))
					except ValueError:  # NOPTS
						pts = None
					with self.cond:
						if pts is None:
							pts = self.headers[-1][0] + 1 / 30 if self.headers else self.last_pts - self.start
						self.headers.append((pts, int(match.group(2)), int(match.group(3))))
						self.cond.notify_all()
				elif "Parsed_showinfo" not in line or "checksum" in line:
					# showinfo's other per-frame lines aren't worth keeping
					self.errors.append(line)
		except (OSError, ValueError):
			pass
		with self.cond:
			self.log_done = True
			self.cond.notify_all()

	def _read_exact(self, size: int) -> bytes | None:
		parts = []
		remaining = size
		while remaining:
			chunk = self.proc.stdout.read(remaining)
			if not chunk:
				return None
			parts.append(chunk)
			remaining -= len(chunk)
		return parts[0] if len(parts) == 1 else b"".join(parts)

	def _read_frames(self) -> None:
		try:
			while True:
				with self.cond:
					while not self.headers and not self.log_done and not self.closed:
						self.cond.wait()
					if self.closed or not self.headers:
						break
					pts, w, h = self.headers.popleft()
				data = self._read_exact(w * h * 4)
				if data is None:
					break
				with self.cond:
					while len(self.frames) >= QUEUE_FRAMES and not self.closed:
						self.cond.wait()
					if self.closed:
						break
					frame = Frame(self.start + pts, w, h, data)
					self.frames.append(frame)
					self.produced += 1
					self.last_pts = frame.pts
		except (OSError, ValueError):
			pass
		with self.cond:
			self.finished = True
			self.cond.notify_all()

	def take(self, position: float) -> Frame | None:
		"""The newest frame due at position, dropping any it passes over"""
		due = None
		with self.cond:
			while self.frames and self.frames[0].pts <= position:
				due = self.frames.popleft()
			if due is not None:
				self.cond.notify_all()
		return due

	def next_pts(self) -> float | None:
		with self.cond:
			return self.frames[0].pts if self.frames else None

	def no_video_stream(self) -> bool:
		return self.finished and self.produced == 0 and any(
			text in line for line in self.errors for text in _NO_VIDEO)

	def checksum_unsupported(self) -> bool:
		return self.finished and self.produced == 0 and any("checksum" in line for line in self.errors)

	def close(self) -> None:
		with self.cond:
			self.closed = True
			self.frames.clear()
			self.cond.notify_all()
		proc = self.proc

		def reap() -> None:
			try:
				proc.kill()
				proc.wait(timeout=5)
			except Exception:
				logging.debug("FFmpeg video decoder did not exit cleanly", exc_info=True)
			for stream in (proc.stdout, proc.stderr):
				with contextlib.suppress(OSError):
					stream.close()

		threading.Thread(target=reap, daemon=True).start()


class VideoPlayer:
	"""Shows the playing video file's picture in place of its art"""

	# A new box size has to hold this long before the decoder restarts at it
	RESIZE_SETTLE = 0.3
	# Surfaces not drawn for this long stop counting towards the decode size
	REQUEST_EXPIRY = 0.5

	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.gui = tauon.gui
		self.pctl = tauon.pctl
		self.renderer = tauon.renderer
		self.decoder: VideoDecoder | None = None
		self.key: tuple[int, str] | None = None
		self.texture = None
		self.texture_size: tuple[int, int] = (0, 0)
		self.frame_pts: float | None = None  # timestamp of the frame in the texture
		self.has_frame = False
		self.requests: dict[str, tuple[tuple[int, int], float]] = {}
		self.target: tuple[int, int] = (0, 0)
		self.target_since = 0.0
		self.last_draw = 0.0
		self.wake_at = 0.0
		self.checksum_option = True
		self.no_video: set[str] = set()
		self._ffmpeg: str | None = None
		self._ffmpeg_checked = -1000.0

	def ffmpeg(self) -> str | None:
		"""FFmpeg's path, looked up again at most every 30 s while missing"""
		now = time.monotonic()
		if self._ffmpeg is None and now - self._ffmpeg_checked > 30:
			self._ffmpeg_checked = now
			path = self.tauon.get_ffmpeg()
			self._ffmpeg = str(path) if path else None
		return self._ffmpeg

	def apply_formats(self) -> None:
		"""Video files import only while FFmpeg can play them"""
		formats = self.tauon.formats
		if self.tauon.prefs.allow_video_formats and self.ffmpeg():
			formats.DA |= formats.VID
		else:
			formats.DA -= formats.VID

	@staticmethod
	def is_video_file(track: TrackClass | None) -> bool:
		return (
			track is not None and not track.is_network and bool(track.fullpath)
			and track.file_ext.lower() in VIDEO_EXTENSIONS)

	def aspect(self, track: TrackClass | None) -> float | None:
		"""Shown frame's aspect ratio when track is the video on screen"""
		if self.has_frame and self.key is not None and track is not None \
				and self.key == (track.index, track.fullpath) and self.texture_size[1]:
			return self.texture_size[0] / self.texture_size[1]
		return None

	def _playing(self, track: TrackClass) -> bool:
		pctl = self.pctl
		if pctl.playing_state not in (PlayingState.PLAYING, PlayingState.PAUSED):
			return False
		playing = pctl.playing_object()
		return playing is not None and playing.index == track.index

	def stop(self) -> None:
		if self.decoder:
			self.decoder.close()
			self.decoder = None
		self.key = None
		self.has_frame = False
		self.frame_pts = None
		self.requests.clear()

	def destroy_texture(self) -> None:
		if self.texture is not None:
			sdl3.destroy_texture(self.texture)
			self.texture = None
			self.texture_size = (0, 0)
		self.has_frame = False

	def tick(self) -> None:
		"""Once per drawn frame: let go of the decoder once nothing shows it"""
		if self.decoder is None and self.texture is None:
			return
		idle = time.monotonic() - self.last_draw > 1.5
		playing = self.pctl.playing_object()
		moved_on = self.key is not None and (playing is None or (playing.index, playing.fullpath) != self.key)
		if idle or moved_on or self.pctl.playing_state == PlayingState.STOPPED:
			self.stop()
			self.destroy_texture()

	def _start(self, path: str, position: float) -> None:
		if self.decoder:
			self.decoder.close()
		ffmpeg = self.ffmpeg()
		self.decoder = None
		# The old frame stays on screen, but no longer marks where playback is
		self.frame_pts = None
		if not ffmpeg:
			return
		try:
			self.decoder = VideoDecoder(ffmpeg, path, max(0.0, position), self.target, self.checksum_option)
		except Exception:
			logging.exception("Failed to start FFmpeg for video")

	def _upload(self, frame: Frame) -> None:
		if self.texture is None or self.texture_size != (frame.w, frame.h):
			if self.texture is not None:
				sdl3.destroy_texture(self.texture)
			self.texture = sdl3.create_texture(
				self.renderer, sdl3.SDL_PIXELFORMAT_RGBA32, sdl3.SDL_TEXTUREACCESS_STREAMING, frame.w, frame.h)
			sdl3.set_texture_scale_mode(self.texture, sdl3.SDL_SCALEMODE_LINEAR)
			sdl3.set_texture_blend_mode(self.texture, sdl3.SDL_BLENDMODE_NONE)
			self.texture_size = (frame.w, frame.h)
		sdl3.update_texture(self.texture, None, frame.data, frame.w * 4)
		self.frame_pts = frame.pts
		self.has_frame = True

	def _wake(self, delay: float) -> None:
		if self.gui.lowered:
			return
		now = time.monotonic()
		due = now + delay
		if now < self.wake_at <= due + 0.003:
			return
		self.wake_at = due
		self.gui.delay_frame(max(delay, 0.001))

	def _needs_rescale(self, decoder: VideoDecoder) -> bool:
		if decoder.box == self.target or not self.has_frame:
			return False
		w, h = self.texture_size
		aspect = w / h
		want = fit(self.target, aspect)
		was = fit(decoder.box, aspect)
		if w < was[0] - 4:
			# Capped at the source size: only a smaller box changes anything
			return want[0] < w - 4
		return abs(want[0] - w) > 4 or abs(want[1] - h) > 4

	def draw(
		self, track: TrackClass | None, rect: tuple[float, float, float, float], caller: str,
		fast: bool = False) -> tuple[int, int, int, int] | None:
		"""Draw the current frame fitted inside rect, returning where it went.

		None means there's no picture to show and the caller draws the art.
		fast (a side panel drag) keeps the decoded size and lets SDL stretch it.
		"""
		if not self.is_video_file(track) or not self._playing(track):
			return None
		path = track.fullpath
		if path in self.no_video or not self.ffmpeg():
			return None

		now = time.monotonic()
		self.last_draw = now
		box = (max(2, round(rect[2])), max(2, round(rect[3])))
		self.requests[caller] = (box, now)
		self.requests = {k: v for k, v in self.requests.items() if now - v[1] < self.REQUEST_EXPIRY}
		target = max((v[0] for v in self.requests.values()), key=lambda b: b[0] * b[1])
		if target != self.target:
			self.target = target
			self.target_since = now

		position = self.tauon.get_heard_time()
		key = (track.index, path)
		if key != self.key:
			self.stop()
			self.key = key
			self.requests[caller] = (box, now)
			self.target = box
			self._start(path, position)

		decoder = self.decoder
		if decoder is not None:
			if decoder.finished and decoder.produced == 0:
				if decoder.no_video_stream():
					logging.info("No video stream in %s", path)
					self.no_video.add(path)
					self.stop()
					return None
				if self.checksum_option and decoder.checksum_unsupported():
					self.checksum_option = False
					self._start(path, position)
					decoder = self.decoder

		if decoder is not None:
			reference = self.frame_pts if self.frame_pts is not None else decoder.start
			ahead = decoder.last_pts if decoder.produced else decoder.start
			seeked = position < reference - 1.0 or (
				position > ahead + 2.5 and now - decoder.started_at > 1.0 and not decoder.finished)
			if seeked:
				self._start(path, position)
			elif not fast and not self.gui.side_drag and now - self.target_since > self.RESIZE_SETTLE \
					and self._needs_rescale(decoder):
				self._start(path, position)
			decoder = self.decoder

		if decoder is not None:
			playing = self.pctl.playing_state == PlayingState.PLAYING
			# Paused, the first frame after a seek lands just past the position
			frame = decoder.take(position + (0.01 if playing else 0.1))
			if frame is not None:
				self._upload(frame)
			if not decoder.finished:
				if playing:
					next_pts = decoder.next_pts()
					self._wake(1 / 60 if next_pts is None else min(1.0, next_pts - position))
				elif (self.frame_pts is None or abs(self.frame_pts - position) > 0.25) and decoder.next_pts() is None:
					self._wake(1 / 30)

		if not self.has_frame or self.texture is None:
			return None

		dw, dh = fit((round(rect[2]), round(rect[3])), self.texture_size[0] / self.texture_size[1])
		dx = round(rect[0] + (rect[2] - dw) / 2)
		dy = round(rect[1] + (rect[3] - dh) / 2)
		sdl3.render_texture(self.renderer, self.texture, None, sdl3.FRect(dx, dy, dw, dh))
		return dx, dy, dw, dh
