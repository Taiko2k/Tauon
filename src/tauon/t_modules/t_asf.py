# Copyright © 2026, Tauon contributors

"""Shared ASF field conventions and embedded picture encoding."""

# ASF iteration yields attribute pairs; validation messages are user-facing.
# ruff: noqa: SIM118, TRY003

from __future__ import annotations

import logging
import struct
from dataclasses import dataclass

from mutagen.asf import ASFByteArrayAttribute, ASFTags, ASFUnicodeAttribute

ASF_KEYS = {
	"title": "Title",
	"album": "WM/AlbumTitle",
	"artist": "Author",
	"albumartist": "WM/AlbumArtist",
	"date": "WM/Year",
	"originaldate": "WM/OriginalReleaseTime",
	"tracknumber": "WM/TrackNumber",
	"discnumber": "WM/PartOfSet",
	"genre": "WM/Genre",
	"label": "WM/Publisher",
	"composer": "WM/Composer",
	"rating": "FMPS_RATING",
	"comment": "Description",
	"bpm": "WM/BeatsPerMinute",
	"copyright": "Copyright",
	"isrc": "WM/ISRC",
	"language": "WM/Language",
	"conductor": "WM/Conductor",
	"originalartist": "WM/OriginalArtist",
	"remixer": "WM/ModifiedBy",
	"lyricist": "WM/Writer",
	"encodedby": "WM/EncodedBy",
	"artistsort": "WM/ArtistSortOrder",
	"albumsort": "WM/AlbumSortOrder",
	"titlesort": "WM/TitleSortOrder",
	"grouping": "WM/ContentGroupDescription",
	"subtitle": "WM/SubTitle",
	"compilation": "WM/IsCompilation",
}
ASF_ALIASES = {
	"originaldate": ("WM/OriginalReleaseTime", "WM/OriginalReleaseYear"),
	"tracknumber": ("WM/TrackNumber", "WM/Track"),
	"rating": ("FMPS_RATING", "WM/SharedUserRating"),
}
ASF_RATING_LEVELS = (0, 1, 25, 50, 75, 99)


def asf_key(tags: ASFTags, key: str) -> str:
	"""Retain the spelling of an existing attribute."""
	return next((native for native in tags.keys() if native.lower() == key.lower()), key)


def asf_field_key(tags: ASFTags, field: str) -> str:
	candidates = ASF_ALIASES.get(field, (ASF_KEYS.get(field, field),))
	return next((asf_key(tags, key) for key in candidates if asf_key(tags, key) in tags), candidates[0])


def asf_text_values(tags: ASFTags, key: str) -> list[str] | None:
	values = tags.get(key)
	if values is None or not all(isinstance(value, ASFUnicodeAttribute) for value in values):
		return None
	return [value.value for value in values]


def asf_field_values(tags: ASFTags, field: str) -> list[str]:
	values = tags.get(asf_field_key(tags, field), [])
	return [str(value.value) for value in values if isinstance(value.value, (str, int, bool))]


def asf_rating(tags: ASFTags) -> float | None:
	"""Return a normalized rating, preferring Tauon's precise FMPS value."""
	for key in ASF_ALIASES["rating"]:
		values = tags.get(asf_key(tags, key), [])
		if not values:
			continue
		try:
			value = float(values[0].value)
			if key == "FMPS_RATING":
				if 0 <= value <= 1:
					return value
			elif 0 <= value <= 99:
				return next(index / 5 for index, limit in enumerate(ASF_RATING_LEVELS) if value <= limit)
		except (TypeError, ValueError):
			logging.warning("Invalid ASF rating in %s", key)
	return None


@dataclass(frozen=True)
class AsfPicture:
	data: bytes
	picture_type: int = 3
	mime: str = "image/jpeg"
	description: str = ""

	@classmethod
	def from_bytes(cls, value: bytes) -> AsfPicture:
		if len(value) < 5:
			raise ValueError("Truncated ASF picture header.")
		picture_type, length = struct.unpack_from("<BI", value)
		offset = 5
		strings = []
		for _index in range(2):
			start = offset
			while offset + 2 <= len(value) and value[offset : offset + 2] != b"\x00\x00":
				offset += 2
			if offset + 2 > len(value):
				raise ValueError("Unterminated ASF picture string.")
			strings.append(value[start:offset].decode("utf-16-le"))
			offset += 2
		if len(value) - offset != length:
			raise ValueError("Invalid ASF picture data length.")
		return cls(value[offset:], picture_type, strings[0], strings[1])

	def to_bytes(self) -> bytes:
		if "\x00" in self.mime or "\x00" in self.description:
			raise ValueError("ASF picture strings cannot contain NUL characters.")
		return (
			struct.pack("<BI", self.picture_type, len(self.data))
			+ (self.mime + "\x00" + self.description + "\x00").encode("utf-16-le")
			+ self.data
		)


def asf_pictures(tags: ASFTags) -> list[tuple[int, AsfPicture]]:
	"""Keep original indices so editing a valid image preserves malformed siblings."""
	pictures = []
	for index, value in enumerate(tags.get(asf_key(tags, "WM/Picture"), [])):
		if not isinstance(value, ASFByteArrayAttribute):
			continue
		try:
			pictures.append((index, AsfPicture.from_bytes(value.value)))
		except (ValueError, UnicodeError):
			logging.warning("Ignoring malformed ASF picture at index %s", index)
	return pictures
