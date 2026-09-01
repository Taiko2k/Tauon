"""Decode and time animated cover art (GIF, APNG and animated JPEG XL)."""

# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from PIL import Image

# Every frame is decoded up front and held as a texture, so both a frame count
# and a memory budget are needed to stop a pathological image eating the heap.
# Art over either limit is simply shown as a still.
ANIM_FRAME_LIMIT = 200
ANIM_SOURCE_BUDGET = 96 * 1024 * 1024   # Full size decoded frames, held only while loading
ANIM_TEXTURE_BUDGET = 64 * 1024 * 1024  # Frame textures, held for as long as the art is cached

# Frame delay to use where the file gives none, or gives one too short to be
# worth honouring. 100 ms matches what browsers substitute for GIFs, which are
# commonly authored with a zero delay.
ANIM_DEFAULT_DELAY = 0.1
ANIM_MIN_DELAY = 0.02

# Floor on how soon the next frame can be asked for. Landing a hair before a
# frame boundary is a certainty with float delays, and waking for less than
# this only to find the same frame still showing is wasted work.
ANIM_TICK = 0.001


class AnimatedArt:
	"""The decoded frames of an animated image, and how long each is shown for"""

	def __init__(self, frames: list[Image.Image], delays: list[float]) -> None:
		self.frames: list[Image.Image] = frames
		self.delays: list[float] = delays
		self.duration: float = sum(delays)

	def frame_at(self, position: float) -> tuple[int, float]:
		return frame_at(self.delays, position)


def read_animation(im: Image.Image) -> AnimatedArt | None:
	"""Decode every frame of an animated image, or return None if it isn't one.

	Covers animated GIF, APNG and -- where jxlpy is installed -- animated JPEG
	XL, being simply whatever Pillow exposes a frame sequence for. Frames come
	back composited and in RGB, ready to be resized per display size.

	JPEG XL keeps its frame durations in the frame headers, which jxlpy doesn't
	surface, so those animations all play at the default delay.
	"""
	try:
		if not getattr(im, "is_animated", False):
			return None
		count = int(getattr(im, "n_frames", 1))
	except Exception:
		logging.exception("Failed to check image for animation")
		return None

	if count < 2:
		return None
	if count > ANIM_FRAME_LIMIT:
		logging.debug(f"Art has {count} frames, over the animation limit; showing as a still")
		return None
	if im.size[0] * im.size[1] * 3 * count > ANIM_SOURCE_BUDGET:
		logging.debug("Art is too large to decode every frame of; showing as a still")
		return None

	frames: list[Image.Image] = []
	delays: list[float] = []
	try:
		for i in range(count):
			# Frames have to be walked in order for GIF and APNG frame
			# disposal to composite into the right thing
			im.seek(i)
			frames.append(im.convert("RGB"))
			delay = float(im.info.get("duration") or 0) / 1000
			delays.append(delay if delay >= ANIM_MIN_DELAY else ANIM_DEFAULT_DELAY)
	except Exception:
		logging.exception("Failed to decode animated image frames")
		return None

	if len(frames) < 2:
		return None
	return AnimatedArt(frames, delays)


def frame_at(delays: list[float], position: float) -> tuple[int, float]:
	"""Which frame is showing at position seconds into the loop, and for how much longer.

	position is expected to have already been wrapped into the loop's length;
	one that runs off the end (or float error landing just short of a boundary)
	gives the last frame rather than failing. The time remaining never comes
	back as zero, so stepping through a loop by it always makes progress.
	"""
	for i, delay in enumerate(delays):
		if position < delay:
			return i, max(delay - position, ANIM_TICK)
		position -= delay
	return len(delays) - 1, ANIM_MIN_DELAY


def fits_texture_budget(size: tuple[int, int], count: int) -> bool:
	"""Whether count frames at this display size are worth keeping as textures"""
	return size[0] * size[1] * 4 * count <= ANIM_TEXTURE_BUDGET
