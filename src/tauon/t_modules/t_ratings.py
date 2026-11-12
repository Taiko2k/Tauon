# Copyright © 2026, Tauon contributors

"""Track ratings stored in file tags: FMPS_RATING everywhere, POPM in ID3 and WM/SharedUserRating in ASF.

Ratings are 0-10 (half stars), 0 meaning unrated.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

import mutagen
from mutagen.asf import ASFTags
from mutagen.id3 import ID3

from tauon.t_modules.t_asf import asf_rating

if TYPE_CHECKING:
	from tauon.t_modules.t_main import TrackClass

# Windows Media Player's levels for 1-5 stars, which most players read
POPM_LEVELS = (0, 1, 64, 128, 196, 255)
# The POPM email most players recognise; Tauon adds this one when a file has none
POPM_EMAIL = "Windows Media Player 9 Series"


def popm_to_rating(value: int | None) -> int:
	"""Map a POPM byte to 0-10 (whole stars, 0 for unrated)."""
	if not value:
		return 0
	return next(score * 2 for score, limit in enumerate(POPM_LEVELS) if value <= limit)


def rating_to_popm(rating: int) -> int:
	"""Map 0-10 to a POPM byte, rounding half stars up."""
	return POPM_LEVELS[(rating + 1) // 2]


def fmps_to_rating(value: float | None) -> int:
	"""Map an FMPS 0.0-1.0 value to 0-10, 0 when missing or out of range."""
	if value is None or not 0 <= value <= 1:
		return 0
	return round(value * 10)


def parse_fmps(text: str | bytes) -> float | None:
	"""Parse an FMPS_RATING value, None if malformed."""
	if isinstance(text, bytes):
		text = text.decode("utf-8", "replace")
	try:
		value = float(str(text).strip().replace(",", "."))
	except ValueError:
		return None
	return value if 0 <= value <= 1 else None


def tag_rating(fmps: float | None, popm: int | None) -> int:
	"""The rating a file's tags carry, preferring FMPS over POPM. 0 if none."""
	return fmps_to_rating(fmps) or popm_to_rating(popm)


def track_rating_file(track: TrackClass) -> bool:
	"""Whether the track owns its file's rating. CUE tracks share a file, so they never do."""
	return bool(track.fullpath) and not track.is_network and not track.is_cue and not track.is_embed_cue


def read_file_rating(path: str) -> int:
	"""Read a file's rating straight from disk, 0 if it has none."""
	audio = mutagen.File(path)
	tags = audio.tags if audio is not None else None
	if tags is None:
		return 0
	if isinstance(tags, ID3):
		fmps = None
		for frame in tags.getall("TXXX"):
			if frame.desc.lower() == "fmps_rating" and frame.text:
				fmps = parse_fmps(frame.text[0])
		popm = None
		for frame in tags.getall("POPM"):
			if frame.rating:
				popm = frame.rating
		return tag_rating(fmps, popm)
	if isinstance(tags, ASFTags):
		value = asf_rating(tags)
		return fmps_to_rating(value) if value is not None else 0
	# Vorbis comments iterate as key/value pairs
	for key in tags.keys():  # noqa: SIM118
		name = key.lower()
		if name in ("fmps_rating", "----:com.apple.itunes:fmps_rating"):
			value = tags[key]
			if isinstance(value, list):
				value = value[0] if value else ""
			# MP4 freeform values are bytes, APE values stringify
			return fmps_to_rating(parse_fmps(value if isinstance(value, bytes) else str(value)))
	return 0


def write_file_rating(path: str, rating: int) -> None:
	"""Write a 0-10 rating to the file's standard fields, or remove them for 0. Raises on failure."""
	from tauon.t_modules.t_tagedit import TagDocument  # noqa: PLC0415 — t_tagedit pulls in PIL

	if not 0 <= rating <= 10:
		raise ValueError(rating)
	if not os.path.isfile(path):
		raise FileNotFoundError(path)
	doc = TagDocument(path)
	doc.set_main("rating", str(rating) if rating else "")
	doc.save()
	logging.info("Wrote rating %s to %s", rating, path)


@dataclass
class RatingJob:
	"""A background pass writing the library's ratings into their files."""

	total: int = 0
	done: int = 0
	changed: int = 0
	failed: int = 0
	cancel: bool = False
