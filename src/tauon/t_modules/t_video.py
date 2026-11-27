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
from tauon.t_modules.t_enums import GuiMode, PlayingState
from tauon.t_modules.t_extra import ColourRGBA

if TYPE_CHECKING:
	from tauon.t_modules.t_draw import TDraw
	from tauon.t_modules.t_main import Tauon, TrackClass

VIDEO_EXTENSIONS = {"mp4", "m4v", "webm", "mkv", "avi", "mov"}

# Longest edge decoded, whatever the box: beyond this SDL upscales
MAX_EDGE = 3840
# Decoded frames held ahead of the clock
QUEUE_FRAMES = 4

_SHOWINFO = re.compile(r"\]\s+n:\s*\d+\s+pts:\s*\S+\s+pts_time:(\S+).*?\ss:(\d+)x(\d+)")
_DURATION = re.compile(r"^\s*Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")
_METADATA = re.compile(r"^\s{4}(\w+)\s*:\s?(.*)$")
# Stream #0:0(und): Video: h264 (High) (avc1 / 0x31637661), yuv420p, 1920x1080 [SAR 1:1 DAR 16:9], 23.98 fps
_VIDEO_STREAM = re.compile(r"Stream #0:\d+\S*: Video: (\w+).*?, (\d+)x(\d+)")
_STREAM_FPS = re.compile(r", (\d+(?:\.\d+)?k?) (fps|tbr)\b")
_NO_VIDEO = ("matches no streams", "does not contain any stream")


def startup_info() -> subprocess.STARTUPINFO | None:
	if sys.platform != "win32":
		return None
	info = subprocess.STARTUPINFO()
	info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
	return info


def fps_label(fps: float) -> str:
	text = f"{fps:.2f}".rstrip("0").rstrip(".")
	return _("{rate} fps").format(rate=text)


def draw_fullscreen_icon(ddt: TDraw, rect: tuple[int, int, int, int], scale: float, colour: ColourRGBA) -> None:
	"""Four corner brackets"""
	x, y, w, h = rect
	t = max(1, round(1.5 * scale))
	arm = round(w * 0.4)
	for cx, cy, dx, dy in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
		left = cx if dx > 0 else cx - arm
		top = cy if dy > 0 else cy - t
		ddt.rect((left, top, arm, t), colour)
		left = cx if dx > 0 else cx - t
		top = cy if dy > 0 else cy - arm
		ddt.rect((left, top, t, arm), colour)


def draw_window_icon(ddt: TDraw, rect: tuple[int, int, int, int], scale: float, colour: ColourRGBA) -> None:
	"""A window frame with a title bar, filled by the picture"""
	x, y, w, h = rect
	t = max(1, round(scale))
	bar = max(2, round(2.5 * scale))
	ddt.rect((x, y, w, bar), colour)
	ddt.rect((x, y + h - t, w, t), colour)
	ddt.rect((x, y, t, h), colour)
	ddt.rect((x + w - t, y, t, h), colour)
	pad = t * 2
	ddt.rect((x + pad, y + bar + t, w - pad * 2, h - bar - t - pad), colour)


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
		# The source stream as FFmpeg reports it: codec, size and frame rate
		self.codec = ""
		self.source_size: tuple[int, int] | None = None
		self.source_fps: float | None = None
		self._pts_seen: list[float] = []

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

	def _parse_stream(self, line: str) -> None:
		match = _VIDEO_STREAM.search(line)
		if not match or "attached pic" in line:
			return
		self.codec = match.group(1)
		self.source_size = (int(match.group(2)), int(match.group(3)))
		rates = {kind: value for value, kind in _STREAM_FPS.findall(line)}
		rate = rates.get("fps") or rates.get("tbr")
		if rate:
			self.source_fps = float(rate[:-1]) * 1000 if rate.endswith("k") else float(rate)

	def _read_log(self) -> None:
		inputs = True
		try:
			for raw in self.proc.stderr:
				line = raw.decode(errors="replace").rstrip()
				if inputs:
					if line.startswith(("Stream mapping:", "Output #")):
						inputs = False
					elif not self.source_size:
						self._parse_stream(line)
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
						if len(self._pts_seen) < 25:
							self._pts_seen.append(pts)
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

	def frame_rate(self) -> float | None:
		"""The stream's stated rate, or one measured from the first frames"""
		if self.source_fps:
			return self.source_fps
		seen = self._pts_seen
		if len(seen) >= 10 and seen[-1] > seen[0]:
			return (len(seen) - 1) / (seen[-1] - seen[0])
		return None

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
		# codec, source size and frame rate of the video on screen
		self.info: tuple[str, tuple[int, int] | None, float | None] = ("", None, None)
		self.fullscreen = VideoFullscreen(tauon, self)
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
		self.info = ("", None, None)

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
			# A frame is due a loop period early: the loop notices the wake up to
			# one period late and the present waits up to a refresh, so on average
			# it reaches the screen on time rather than always behind.
			lead = self.tauon.frame_pace()
			# Paused, the first frame after a seek lands just past the position
			frame = decoder.take(position + (lead if playing else max(lead, 0.1)))
			if frame is not None:
				self._upload(frame)
			if not decoder.finished:
				if playing:
					next_pts = decoder.next_pts()
					self._wake(1 / 60 if next_pts is None else min(1.0, next_pts - lead - position))
				elif (self.frame_pts is None or abs(self.frame_pts - position) > 0.25) and decoder.next_pts() is None:
					self._wake(1 / 30)

		if not self.has_frame or self.texture is None:
			return None

		dw, dh = fit((round(rect[2]), round(rect[3])), self.texture_size[0] / self.texture_size[1])
		dx = round(rect[0] + (rect[2] - dw) / 2)
		dy = round(rect[1] + (rect[3] - dh) / 2)
		sdl3.render_texture(self.renderer, self.texture, None, sdl3.FRect(dx, dy, dw, dh))
		return dx, dy, dw, dh

	def draw_reflection(self, rect: tuple[int, int, int, int], height: float, clip: float | None = None) -> None:
		"""Candy Factory's wet-floor reflection under the frame drawn at rect."""
		if self.texture is None or not self.has_frame:
			return
		# The frame draws opaque; the reflection's fade needs blending
		sdl3.set_texture_blend_mode(self.texture, sdl3.SDL_BLENDMODE_BLEND)
		self.tauon.aero.reflection(self.texture, rect, 0, height, clip)
		sdl3.set_texture_blend_mode(self.texture, sdl3.SDL_BLENDMODE_NONE)

	def source_info(self) -> tuple[str, tuple[int, int] | None, float | None]:
		decoder = self.decoder
		if decoder is not None and decoder.codec:
			rate = decoder.frame_rate() or self.info[2]
			self.info = (decoder.codec, decoder.source_size, rate)
		return self.info

	def draw_overlay(self, rect: tuple[int, int, int, int]) -> None:
		"""Hover tags over the video: frame rate top left, fullscreen buttons bottom right.

		Shift adds the codec and source size, as it adds detail to the art's tags.
		"""
		tauon = self.tauon
		ddt = tauon.ddt
		inp = tauon.inp
		scale = self.gui.scale
		x, y, w, h = rect
		tag_h = round(18 * scale)
		inset = round(10 * scale)
		text_x = round(6 * scale)
		back = ColourRGBA(8, 8, 8, 255)
		text_bg = ColourRGBA(30, 30, 30, 255)
		ink = ColourRGBA(200, 200, 200, 255)

		codec, size, fps = self.source_info()
		lines = [fps_label(fps)] if fps else []
		if inp.key_shift_down:
			if codec:
				lines.append(codec)
			if size:
				lines.append(f"{size[0]}×{size[1]}")
		ty = y + inset
		for line in lines:
			tw = ddt.get_text_w(line, 12) + round(12 * scale)
			ddt.rect_a((x + inset, ty), (tw, tag_h), back)
			ddt.text((x + inset + text_x, ty), line, ink, 12, bg=text_bg)
			ty += tag_h

		size = round(24 * scale)
		gap = round(4 * scale)
		if size * 2 + gap + inset * 2 > w or tag_h + size + inset * 3 > h:
			return
		buttons = ((_("Fullscreen"), True, draw_fullscreen_icon), (_("Fill Window"), False, draw_window_icon))
		right = x + w - inset
		by = y + h - inset - size
		for label, desktop, draw_icon in buttons:
			bx = right - size
			hover = tauon.coll((bx, by, size, size))
			ddt.rect((bx, by, size, size), ColourRGBA(55, 55, 55, 255) if hover else back)
			icon = round(12 * scale)
			edge = (size - icon) // 2
			draw_icon(ddt, (bx + edge, by + edge, icon, icon), scale, ColourRGBA(240, 240, 240, 255) if hover else ink)
			if hover:
				tip_w = ddt.get_text_w(label, 13) + 20 * scale
				tauon.tool_tip.test(bx + size - tip_w, by - 30 * scale, label)
				if inp.mouse_click:
					inp.mouse_click = False
					self.fullscreen.activate(desktop)
			right = bx - gap

class VideoFullscreen:
	"""The playing video over the whole window, or the whole screen.

	Any click or Escape leaves. Keyboard shortcuts keep working; the pointer is
	muted so the UI underneath never reacts.
	"""

	def __init__(self, tauon: Tauon, player: VideoPlayer) -> None:
		self.tauon = tauon
		self.player = player
		self.gui = tauon.gui
		self.inp = tauon.inp
		self.active = False
		self._entered_window_fullscreen = False
		# The pointer is muted for the UI underneath; this keeps where it really is
		self.pointer: tuple[float, float] = (-1.0, -1.0)
		# Clicks held for the window controls, which are drawn after input handling
		self._click = False
		self._up = False
		self._ab = False

	def _controls_shown(self) -> bool:
		"""Fill Window shows Tauon's window controls while the pointer is near the top"""
		return not self.gui.fullscreen and self.tauon.draw_border \
			and 0 <= self.pointer[1] < round(48 * self.gui.scale)

	def _controls_rect(self) -> tuple[int, int, int, int]:
		scale = self.gui.scale
		width = round(110 * scale)
		x = 0 if self.tauon.prefs.left_window_control else self.tauon.window_size[0] - width
		return x, 0, width, round(32 * scale)

	def activate(self, desktop: bool) -> None:
		if self.active or self.gui.mode != GuiMode.MAIN:
			return
		self.active = True
		if desktop and not self.gui.fullscreen:
			self.gui.fullscreen = True
			self._entered_window_fullscreen = True
			sdl3.set_window_fullscreen_mode(self.tauon.t_window, None)
			sdl3.set_window_fullscreen(self.tauon.t_window, True)
		self.gui.request_frame()

	def close(self) -> None:
		if not self.active:
			return
		self.active = False
		# Only leave OS fullscreen if this view entered it and it's still set
		if self._entered_window_fullscreen and self.gui.fullscreen:
			self.gui.fullscreen = False
			sdl3.set_window_fullscreen(self.tauon.t_window, False)
		self._entered_window_fullscreen = False
		self.gui.request_frame()

	def handle_input(self) -> None:
		if not self.active:
			return
		inp = self.inp
		# Runs more than once a frame; later passes see the muted pointer
		if inp.mouse_position[0] > -2999:
			self.pointer = (inp.mouse_position[0], inp.mouse_position[1])
		on_controls = False
		if self._controls_shown():
			x, y, w, h = self._controls_rect()
			on_controls = x <= self.pointer[0] < x + w and y <= self.pointer[1] < y + h
			# A press without a motion event in between was recorded at the muted position
			if inp.click_location[0] <= -2999:
				inp.click_location = list(self.pointer)
		if inp.key_esc_press:
			inp.key_esc_press = False
			self.close()
		elif on_controls and inp.mouse_click:
			self._click = True
		elif inp.mouse_click or inp.right_click or inp.middle_click:
			self.close()
		if on_controls:
			self._up |= inp.mouse_up
			self._ab |= inp.ab_click
		inp.mouse_click = False
		inp.d_mouse_click = False
		inp.right_click = False
		inp.middle_click = False
		inp.mouse_wheel = 0
		inp.mouse_position[0] = -3000.0
		inp.mouse_position[1] = -3000.0

	def render(self) -> None:
		if not self.active:
			return
		tauon = self.tauon
		pctl = tauon.pctl
		track = pctl.playing_object()
		if pctl.playing_state not in (PlayingState.PLAYING, PlayingState.PAUSED) \
				or not self.player.is_video_file(track) or track.fullpath in self.player.no_video \
				or (self._entered_window_fullscreen and not self.gui.fullscreen):
			# Stopped, moved on to audio, or the window left fullscreen behind our back
			self.close()
			return
		w, h = tauon.window_size
		tauon.ddt.rect((0, 0, w, h), ColourRGBA(0, 0, 0, 255))
		self.player.draw(track, (0, 0, w, h), "fullscreen")
		if self._controls_shown():
			self._draw_controls()
		self._click = self._up = self._ab = False

	def _draw_controls(self) -> None:
		"""The window controls on a patch of top panel, with the real pointer handed back to them"""
		tauon = self.tauon
		inp = self.inp
		panel = tauon.colours.top_panel_background
		tauon.ddt.rect(self._controls_rect(), ColourRGBA(panel.r, panel.g, panel.b, 255))
		saved = (list(inp.mouse_position), inp.mouse_click, inp.mouse_up, inp.ab_click)
		inp.mouse_position[:] = self.pointer
		inp.mouse_click, inp.mouse_up, inp.ab_click = self._click, self._up, self._ab
		try:
			tauon.draw_window_tools()
		finally:
			inp.mouse_position[:] = saved[0]
			inp.mouse_click, inp.mouse_up, inp.ab_click = saved[1:]
