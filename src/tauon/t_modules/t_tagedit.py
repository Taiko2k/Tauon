# Copyright © 2026, Tauon contributors

"""Format-aware tag edits, kept separate from the SDL editor."""

# Validation errors carry user-facing details; Vorbis iteration returns key/value pairs.
# ruff: noqa: TRY003, SIM118

from __future__ import annotations

import base64
import copy
import ctypes
import datetime
import io
import json
import os
import re
import shutil
import sys
import tempfile
from collections.abc import Callable, Iterator, MutableMapping
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path

import mutagen
from mutagen._vorbis import VCommentDict
from mutagen.apev2 import APEBinaryValue, APENoHeaderError, APETextValue, APEv2
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, ID3, POPM, SYLT, TCON, TXXX, UFID, USLT, Frames, TextFrame, TimeStampTextFrame, UrlFrame
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover, MP4FreeForm
from PIL import Image

from tauon.t_modules.t_extra import j_chars

MAIN_FIELDS = (
	"title",
	"album",
	"artist",
	"albumartist",
	"date",
	"originaldate",
	"tracknumber",
	"discnumber",
	"genre",
	"label",
	"composer",
	"rating",
)
VALUE_FIELDS = {"title", "album", "artist", "albumartist", "genre", "label", "composer"}
POPM_LEVELS = (0, 1, 64, 128, 196, 255)
ID3_KEYS = dict(
	zip(
		MAIN_FIELDS,
		("TIT2", "TALB", "TPE1", "TPE2", "TDRC", "TDOR", "TRCK", "TPOS", "TCON", "TPUB", "TCOM", "TXXX:FMPS_RATING"),
		strict=True,
	)
)
MP4_KEYS = dict(
	zip(
		MAIN_FIELDS,
		(
			"©nam",
			"©alb",
			"©ART",
			"aART",
			"©day",
			"----:com.apple.iTunes:ORIGINALDATE",
			"trkn",
			"disk",
			"©gen",
			"----:com.apple.iTunes:LABEL",
			"©wrt",
			"----:com.apple.iTunes:FMPS_RATING",
		),
		strict=True,
	)
)
APE_KEYS = {
	"title": "Title",
	"album": "Album",
	"artist": "Artist",
	"albumartist": "Album Artist",
	"date": "Year",
	"originaldate": "Originaldate",
	"tracknumber": "Track",
	"discnumber": "Disc",
	"genre": "Genre",
	"label": "Label",
	"composer": "Composer",
	"rating": "FMPS_RATING",
}
COMMON_ID3_KEYS = {
	"comment": "COMM::eng",
	"composer": "TCOM",
	"bpm": "TBPM",
	"copyright": "TCOP",
	"isrc": "TSRC",
	"language": "TLAN",
	"conductor": "TPE3",
	"originalartist": "TOPE",
	"remixer": "TPE4",
	"lyricist": "TEXT",
	"encodedby": "TENC",
	"artistsort": "TSOP",
	"albumsort": "TSOA",
	"titlesort": "TSOT",
	"grouping": "TIT1",
	"subtitle": "TIT3",
}
COMMON_MP4_KEYS = {
	"comment": "©cmt",
	"composer": "©wrt",
	"copyright": "cprt",
	"artistsort": "soar",
	"albumsort": "soal",
	"titlesort": "sonm",
	"grouping": "©grp",
	"bpm": "tmpo",
	"compilation": "cpil",
	"isrc": "----:com.apple.iTunes:ISRC",
	"language": "----:com.apple.iTunes:LANGUAGE",
	"conductor": "----:com.apple.iTunes:CONDUCTOR",
	"originalartist": "----:com.apple.iTunes:ORIGINALARTIST",
	"remixer": "----:com.apple.iTunes:REMIXER",
	"lyricist": "----:com.apple.iTunes:LYRICIST",
	"encodedby": "©too",
	"subtitle": "----:com.apple.iTunes:SUBTITLE",
}
COMMON_APE_KEYS = {
	"comment": "Comment",
	"bpm": "BPM",
	"copyright": "Copyright",
	"isrc": "ISRC",
	"language": "Language",
	"conductor": "Conductor",
	"originalartist": "Original Artist",
	"remixer": "MixArtist",
	"lyricist": "Lyricist",
	"encodedby": "EncodedBy",
	"artistsort": "Artistsort",
	"albumsort": "Albumsort",
	"titlesort": "Titlesort",
	"grouping": "Grouping",
	"subtitle": "Subtitle",
	"compilation": "Compilation",
}
MP4_TEXT_KEYS = {"aART", "sonm", "soal", "soar", "soaa", "soco", "desc", "ldes", "cprt"}
ALIASES = {
	"year": "date",
	"originalyear": "originaldate",
	"track": "tracknumber",
	"disc": "discnumber",
	"disk": "discnumber",
	"album artist": "albumartist",
	"original artist": "originalartist",
	"comment": "comment",
	"composer": "composer",
	"original year": "originaldate",
	"track number": "tracknumber",
	"disc number": "discnumber",
	"disk number": "discnumber",
	"album_artist": "albumartist",
	"publisher": "label",
	"organization": "label",
	"record label": "label",
}
LYRIC_NAMES = {"lyrics", "unsyncedlyrics", "syncedlyrics"}
ART_NAMES = {"metadata_block_picture", "coverart", "coverartmime", "cover art (front)", "cover art (back)", "covr"}


@dataclass(frozen=True)
class TagEntry:
	key: str
	value: str
	kind: str = "text"
	editable: bool = True
	lyrics: bool = False
	value_index: int | None = None


def file_stamp(path: Path) -> tuple[int, int, int, int]:
	stat = path.stat()
	return stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size, stat.st_ino


def copy_tag_file(source: Path, destination: Path) -> None:
	"""Preserve file metadata, including macOS extended attributes and ACLs."""
	shutil.copy2(source, destination)
	if sys.platform == "darwin":
		copyfile = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True).copyfile
		copyfile.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_uint32)
		copyfile.restype = ctypes.c_int
		# COPYFILE_METADATA = COPYFILE_ACL | COPYFILE_STAT | COPYFILE_XATTR.
		if copyfile(os.fsencode(source), os.fsencode(destination), None, 7) != 0:
			error = ctypes.get_errno()
			raise OSError(error, os.strerror(error), str(source))


def decode_sylt(frame: SYLT) -> str:
	if frame.format != 2:
		return repr(frame.text)
	return "\n".join(f"[{stamp // 60000:02d}:{stamp % 60000 / 1000:06.3f}]{text}" for text, stamp in frame.text)


def encode_sylt(text: str) -> list[tuple[str, int]]:
	result = []
	for line in text.splitlines():
		if not line.strip():
			continue
		match = re.fullmatch(r"\[(\d+):(\d{1,2})(?:\.(\d{1,3}))?\](.*)", line)
		if not match or int(match[2]) >= 60:
			raise ValueError("Synced lyrics require [mm:ss.mmm]text on each line.")
		stamp = int(match[1]) * 60000 + int(match[2]) * 1000 + int((match[3] or "").ljust(3, "0"))
		if result and stamp < result[-1][1]:
			raise ValueError("Synced lyric timestamps must be in order.")
		result.append((match[4], stamp))
	return result


MOJIBAKE_ENCODINGS = ("cp932", "utf-8", "big5hkscs", "gbk")


def repair_mojibake_text(text: str, encoding: str) -> str:
	"""Reverse a mistaken single-byte decode without dropping any characters."""
	for source in ("latin-1", "cp1252"):
		try:
			return text.encode(source).decode(encoding)
		except UnicodeError:
			continue
	return text


def detect_mojibake_encoding(
	hints: list[str], values: list[str], folder: str, encodings: tuple[str, ...]
) -> str | None:
	for text in hints:
		if not text.strip() or text.strip() in folder:
			continue
		for encoding in encodings:
			fixed = repair_mojibake_text(text, encoding)
			if fixed != text and fixed.strip() and fixed.strip() in folder:
				return encoding
	if "utf-8" in encodings and any(repair_mojibake_text(text, "utf-8") != text for text in values):
		return "utf-8"
	for encoding in encodings:
		for text in values:
			fixed = repair_mojibake_text(text, encoding)
			if fixed != text and any(char in j_chars for char in fixed):
				return encoding
	return None


class TagDocument:
	def __init__(self, path: str | Path) -> None:
		self.path = Path(path).resolve(strict=True)
		self.stamp = file_stamp(self.path)
		self.audio = mutagen.File(self.path)
		if self.audio is None:
			raise ValueError(f"Unsupported audio file: {self.path.name}")
		had_tags = self.audio.tags is not None
		if isinstance(self.audio, MP3):
			try:
				APEv2(self.path)
			except APENoHeaderError:
				pass
			else:
				raise ValueError("APEv2 tags on MP3 files require an external editor; library rescanning uses ID3.")
		if not had_tags:
			self.audio.add_tags()
		self.tags = self.audio.tags
		self.id3_version = 4
		self.legacy_opaque = False
		if isinstance(self.tags, ID3):
			version = self.tags.version[1]
			self.legacy_opaque = version == 2 and bool(self.tags.unknown_frames)
			if had_tags and version in (3, 4):
				self.audio.tags = type(self.tags)(self.path, translate=False)
				self.tags = self.audio.tags
				self.id3_version = version
			self.family = "ID3"
			source_label = f"ID3v{self.tags.version[0]}.{version}" if self.tags.version[0] == 1 else f"ID3v2.{version}"
			target_label = f"ID3v2.{self.id3_version}"
			self.label = source_label if source_label == target_label else f"{source_label} → {target_label}"
		elif isinstance(self.tags, APEv2):
			self.family = "APE"
			self.label = "APEv2"
		elif isinstance(self.audio, MP4):
			self.family = "MP4"
			self.label = "MP4 / iTunes"
		elif isinstance(self.tags, VCommentDict):
			self.family = "Vorbis"
			self.label = "Vorbis comments" + (" / FLAC pictures" if isinstance(self.audio, FLAC) else "")
		else:
			raise TypeError(f"Unsupported tag container: {type(self.tags).__name__}")
		if not had_tags:
			self.label = "No tags → " + self.label.split(" → ")[-1]
		if file_stamp(self.path) != self.stamp:
			raise ValueError(f"File changed while reading: {self.path.name}")

	def key_for(self, field: str) -> str:
		if self.family == "ID3":
			if self.id3_version == 3 and field in ("date", "originaldate"):
				return {"date": "TYER", "originaldate": "TORY"}[field]
			key = ID3_KEYS.get(field, COMMON_ID3_KEYS.get(field, "TXXX:" + field))
			if field == "rating":
				return next((native for native in self.tags.keys() if native.lower() == key.lower()), key)
			return key
		if self.family == "MP4":
			key = MP4_KEYS.get(field, COMMON_MP4_KEYS.get(field, "----:com.apple.iTunes:" + field))
			if field == "originaldate":
				for candidate in (key, "----:com.apple.iTunes:ORIGINALYEAR"):
					for native in self.tags.keys():
						if native.lower() == candidate.lower():
							return native
			return next((native for native in self.tags.keys() if native.lower() == key.lower()), key)
		if self.family == "APE":
			candidates = (
				("Originaldate", "Originalyear")
				if field == "originaldate"
				else (APE_KEYS.get(field, COMMON_APE_KEYS.get(field, field)), field)
			)
		else:
			candidates = {
				"rating": ("fmps_rating",),
				"originaldate": ("originaldate", "originalyear"),
				"albumartist": ("albumartist", "album artist"),
				"label": ("label", "organization", "publisher"),
			}.get(field, (field,))
		for key in candidates:
			if key in self.tags:
				return next(native for native in self.tags.keys() if native.lower() == key.lower())
		return candidates[0]

	def main_keys(self, field: str) -> list[str]:
		"""Include existing aliases owned by a Main field so clearing cannot revive them."""
		key = self.key_for(field)
		aliases = {key.lower()}
		if field == "originaldate" and self.family != "ID3":
			aliases.update(
				{"----:com.apple.itunes:originaldate", "----:com.apple.itunes:originalyear"}
				if self.family == "MP4"
				else {"originaldate", "originalyear"}
			)
		elif field == "albumartist" and self.family in ("APE", "Vorbis"):
			aliases.update(("albumartist", "album artist"))
		elif field == "label" and self.family == "Vorbis":
			aliases.update(("label", "organization", "publisher"))
		elif field == "date" and self.family == "APE":
			aliases.update(("year", "date"))
		elif field in ("date", "originaldate") and self.family == "ID3":
			aliases.update(("TYER", "TDRC", "TDAT", "TIME") if field == "date" else ("TORY", "TDOR"))
			aliases = {native.lower() for native in aliases}
		elif field in ("tracknumber", "discnumber") and self.family == "Vorbis":
			aliases.update(("tracktotal", "totaltracks") if field == "tracknumber" else ("disctotal", "totaldiscs"))
		return list(dict.fromkeys([key, *(native for native in self.tags.keys() if native.lower() in aliases)]))

	def resolve_key(self, key: str) -> str:
		key = key.strip()
		if not key:
			raise ValueError("A tag key is required.")
		if "\x00" in key:
			raise ValueError("Tag keys cannot contain NUL characters.")
		if key in self.tags:
			return next(
				native
				for native in self.tags.keys()
				if native == key or (self.family in ("APE", "Vorbis") and native.lower() == key.lower())
			)
		if self.family in ("APE", "Vorbis") and key.lower() == "originalyear":
			return "Originalyear" if self.family == "APE" else "originalyear"
		name = ALIASES.get(key.lower(), key.lower())
		if name in MAIN_FIELDS or name in COMMON_ID3_KEYS or name in COMMON_MP4_KEYS:
			return self.key_for(name)
		if self.family == "ID3" and ":" not in key and key not in Frames:
			return "TXXX:" + key
		if (
			self.family == "MP4"
			and key not in self.tags
			and key not in MP4_TEXT_KEYS
			and key not in ("tmpo", "cpil")
			and not key.startswith(("©", "----:"))
		):
			return "----:com.apple.iTunes:" + key
		if self.family in ("APE", "Vorbis"):
			return next(
				(native for native in self.tags.keys() if native.lower() == key.lower()),
				key.lower() if self.family == "Vorbis" else key,
			)
		return key

	def is_lyric_key(self, key: str) -> bool:
		if self.family == "ID3":
			return key[:4] in ("USLT", "SYLT") or (key.startswith("TXXX:") and key[5:].lower() in LYRIC_NAMES)
		return key.lower() in LYRIC_NAMES or key == "©lyr" or key.lower().endswith(":syncedlyrics")

	def entries(self) -> dict[str, TagEntry]:
		entries = {}
		for key, value in self.tags.items():
			lyrics = self.is_lyric_key(key)
			kind, editable = "text", True
			if key.lower() in ART_NAMES or key.startswith("APIC:"):
				text, kind, editable = "Embedded artwork (use Main)", "artwork", False
			elif isinstance(value, SYLT):
				text = decode_sylt(value)
				kind, editable = (
					"synced lyrics (milliseconds)" if value.format == 2 else "synced lyrics (MPEG frames)",
					value.format == 2,
				)
			elif isinstance(value, UFID) and value.owner == "http://musicbrainz.org":
				try:
					text = value.data.decode("ascii")
				except UnicodeError:
					text, kind, editable = "Undecodable identifier data", "binary", False
			elif isinstance(value, USLT):
				text = value.text
			elif isinstance(value, TCON):
				text = "\n".join(value.genres)
			elif isinstance(value, TextFrame):
				text = "\n".join(map(str, value.text))
			elif self.family == "ID3" and key.startswith("COMM:"):
				text = "\n".join(value.text)
			elif isinstance(value, UrlFrame):
				text = value.url
			elif isinstance(value, APETextValue) or (
				isinstance(value, list) and all(isinstance(item, str) for item in value)
			):
				text = "\n".join(value)
			elif (
				self.family == "MP4"
				and key.startswith("----:")
				and all(isinstance(item, MP4FreeForm) and item.dataformat == 1 for item in value)
			):
				try:
					text = "\n".join(item.decode("utf-8") for item in value)
				except UnicodeError:
					text, kind, editable = "Undecodable freeform data", "binary", False
			elif self.family == "MP4" and (
				isinstance(value, bool)
				or (isinstance(value, list) and all(isinstance(item, (int, bool, tuple)) for item in value))
			):
				text, kind = json.dumps(value), "JSON numbers / booleans"
			else:
				text = (
					value.pprint()[:2000]
					if self.family == "ID3"
					else f"{type(value).__name__}: {len(value)} bytes / values"
				)
				kind, editable = "binary / structured", False
			if kind == "text" and not lyrics and key not in {self.key_for(name) for name in MAIN_FIELDS}:
				values = None
				if isinstance(value, (list, APETextValue)) and all(isinstance(item, str) for item in value):
					values = list(value)
				elif isinstance(value, TextFrame):
					values = list(map(str, value.text))
				elif self.family == "MP4" and key.startswith("----:"):
					values = [item.decode("utf-8") for item in value]
				if values is not None and any(not item or "\n" in item or "\r" in item for item in values):
					text, kind = json.dumps(values, ensure_ascii=False), "JSON text values"
			entries[key] = TagEntry(key, text, kind, editable, lyrics)
		if self.family == "ID3":
			for index, data in enumerate(self.tags.unknown_frames):
				key = f"Unknown frame {data[:4].decode('ascii', errors='replace')} [{index + 1}]"
				entries[key] = TagEntry(key, f"{len(data)} bytes (opaque ID3 frame)", "binary / structured", False)
		return entries

	def text_values(self, key: str) -> list[str] | None:
		"""Read editable text as separate values, retaining embedded line breaks."""
		value = self.tags.get(key)
		if value is None:
			return None
		if isinstance(value, UFID) and value.owner == "http://musicbrainz.org":
			try:
				return [value.data.decode("ascii")]
			except UnicodeError:
				return None
		if isinstance(value, UrlFrame):
			return [value.url]
		if isinstance(value, SYLT):
			return [decode_sylt(value)] if value.format == 2 else None
		if isinstance(value, USLT):
			return [value.text]
		if isinstance(value, TCON):
			return value.genres
		if isinstance(value, TextFrame):
			return list(map(str, value.text))
		if self.family == "ID3" and key.startswith("COMM:"):
			return list(value.text)
		if isinstance(value, APETextValue) or (
			isinstance(value, list) and all(isinstance(item, str) for item in value)
		):
			return list(value)
		if (
			self.family == "MP4"
			and key.startswith("----:")
			and all(isinstance(item, MP4FreeForm) and item.dataformat == 1 for item in value)
		):
			try:
				return [item.decode("utf-8") for item in value]
			except UnicodeError:
				return None
		return None

	def supports_multiple_values(self, key: str) -> bool:
		return not (
			self.family == "ID3"
			and (key[:4] in ("USLT", "SYLT", "UFID") or (key[:4] in Frames and issubclass(Frames[key[:4]], UrlFrame)))
		)

	def main_value(self, field: str) -> str:
		entry = self.entries().get(self.key_for(field))
		if entry is None:
			if field == "rating" and self.family == "ID3":
				frames = self.tags.getall("POPM")
				if frames:
					rating = frames[0].rating
					for score, limit in enumerate(POPM_LEVELS):
						if rating <= limit:
							return str(score * 2)
			return ""
		if self.family == "MP4" and field in ("tracknumber", "discnumber"):
			number, total = self.tags[entry.key][0]
			return str(number) + (f"/{total}" if total else "")
		if self.family == "Vorbis" and field in ("tracknumber", "discnumber"):
			value = entry.value
			keys = ("tracktotal", "totaltracks") if field == "tracknumber" else ("disctotal", "totaldiscs")
			if "/" not in value:
				for key in keys:
					if self.tags.get(key):
						return value + "/" + self.tags[key][0]
			return value
		if field == "rating":
			return str(round(float(entry.value) * 10))
		return entry.value.replace("\n", "; ")

	def lyric_defaults(self) -> tuple[str, str]:
		keys = {"ID3": ("USLT::eng", "SYLT::eng"), "MP4": ("©lyr", "----:com.apple.iTunes:SYNCEDLYRICS")}.get(
			self.family, ("unsyncedlyrics", "syncedlyrics")
		)
		return tuple(self.resolve_key(key) for key in keys)

	def portable_key(self, key: str) -> str:
		"""Map shared text conventions when a selection contains multiple formats."""
		if key.startswith("USLT:") or key == "©lyr" or key.lower() == "unsyncedlyrics":
			return key if self.family == "ID3" and key.startswith("USLT:") else self.lyric_defaults()[0]
		if key.startswith("SYLT:") or key.lower() in ("syncedlyrics", "----:com.apple.itunes:syncedlyrics"):
			return key if self.family == "ID3" and key.startswith("SYLT:") else self.lyric_defaults()[1]
		if key.lower() == "lyrics" and self.family in ("ID3", "MP4"):
			return self.lyric_defaults()[0]
		for mapping in (ID3_KEYS, MP4_KEYS, COMMON_ID3_KEYS, COMMON_MP4_KEYS, COMMON_APE_KEYS):
			for name, native in mapping.items():
				if key == native and name not in ("date", "originaldate", "rating", "tracknumber", "discnumber"):
					return self.key_for(name)
		if key.startswith("TXXX:") and self.family != "ID3":
			return self.resolve_key(key[5:])
		if key.startswith("----:") and self.family != "MP4":
			return self.resolve_key(key.split(":", 2)[-1])
		if key in ("TCOM", "©wrt"):
			return self.key_for("composer")
		if key.startswith("COMM:") or key == "©cmt":
			return key if self.family == "ID3" and key.startswith("COMM:") else self.key_for("comment")
		if self.family != "ID3" and key in Frames:
			raise ValueError(f"Native ID3 frame {key} has no safe mapping for {self.label}; edit a single tag format.")
		return self.resolve_key(key)

	def set_main(self, field: str, text: str | list[str]) -> None:
		key = self.key_for(field)
		if isinstance(text, list):
			if field not in VALUE_FIELDS:
				raise ValueError(f"{field} requires a single value.")
			for native in self.main_keys(field):
				self._set_native_entry(native, text)
			return
		if field in ("tracknumber", "discnumber") and text:
			if not re.fullmatch(r"\d+(?:/\d+)?", text) or any(int(item) > 65535 for item in text.split("/")):
				raise ValueError("Track and disc numbers must be 0-65535, optionally number/total.")
			if self.family == "MP4":
				parts = [int(item) for item in text.split("/")]
				self.tags[key] = [(parts[0], parts[1] if len(parts) == 2 else 0)]
				return
		if self.family == "Vorbis" and field in ("tracknumber", "discnumber"):
			total_keys = ("tracktotal", "totaltracks") if field == "tracknumber" else ("disctotal", "totaldiscs")
			parts = text.split("/", 1)
			self._set_native_entry(key, parts[0])
			for total_key in total_keys:
				if total_key in self.tags:
					del self.tags[total_key]
			if len(parts) == 2:
				self.tags[total_keys[0]] = [parts[1]]
			return
		if field in ("date", "originaldate") and text:
			if not re.fullmatch(r"\d{4}(?:-\d{2}(?:-\d{2})?)?", text):
				raise ValueError("Dates must be YYYY, YYYY-MM or YYYY-MM-DD.")
			datetime.date.fromisoformat(text + {4: "-01-01", 7: "-01", 10: ""}[len(text)])
			if self.family == "ID3" and self.id3_version == 3 and len(text) != 4:
				raise ValueError("ID3v2.3 year fields require YYYY; existing full dates are preserved unless edited.")
		if field == "rating":
			popm_rating = 0
			if text:
				rating = int(text)
				if not 0 <= rating <= 10:
					raise ValueError("Rating must be between 0 and 10.")
				text = f"{rating / 10:.2f}" if rating else ""
				popm_rating = POPM_LEVELS[(rating + 1) // 2]
			if self.family == "ID3":
				frames = self.tags.getall("POPM")
				if text and not frames:
					self.tags.add(POPM(email="tauonmusicbox", rating=popm_rating, count=0))
				for frame in frames:
					if not text:
						del self.tags[frame.HashKey]
					else:
						frame.rating = popm_rating
		if self.family == "ID3" and field in ("date", "originaldate"):
			obsolete = ("TYER", "TDRC", "TDAT", "TIME") if field == "date" else ("TORY", "TDOR")
			for native in obsolete:
				if native != key:
					self.tags.pop(native, None)
		keys = self.main_keys(field)
		if field == "originaldate" and self.family != "ID3":
			if text and key.lower().endswith("originalyear") and len(text) > 4:
				keys.insert(
					0,
					MP4_KEYS[field]
					if self.family == "MP4"
					else "Originaldate"
					if self.family == "APE"
					else "originaldate",
				)
			if text and self.family == "APE" and not any(native.lower() == "originalyear" for native in keys):
				keys.append("Originalyear")
			for native in keys:
				self._set_native_entry(native, text[:4] if native.lower().endswith("originalyear") else text)
			return
		text = text.replace("; ", "\n") if field in ("artist", "albumartist", "genre") else text
		for native in keys:
			self._set_native_entry(native, text)

	def set_entry(self, key: str, text: str | list[str]) -> None:
		self._set_native_entry(self.portable_key(key), text)

	def _set_native_entry(self, key: str, text: str | list[str]) -> None:
		entry = self.entries().get(key)
		if entry and not entry.editable:
			raise ValueError(f"{key} is binary or structured and cannot be edited as text.")
		if key.lower() in ART_NAMES or key.startswith("APIC:"):
			raise ValueError("Use the artwork preview to change embedded images.")
		if not text:
			if key in self.tags:
				del self.tags[key]
			return
		if isinstance(text, str) and entry and entry.kind == "JSON text values":
			text = json.loads(text)
			if not isinstance(text, list) or not all(isinstance(item, str) for item in text):
				raise ValueError(f"{key} requires a JSON array of text values.")
			if not text:
				self.tags.pop(key, None)
				return
		explicit_values = isinstance(text, list)
		values = list(text) if explicit_values else text.splitlines() or [text]
		if any("\x00" in value for value in values):
			raise ValueError("Tag text cannot contain NUL characters; use separate values instead.")
		if explicit_values and len(values) > 1 and not self.supports_multiple_values(key):
			raise ValueError(
				f"{key} stores a single value; use distinct frame descriptions/languages for additional entries."
			)
		text = "\n".join(text) if isinstance(text, list) else text
		if self.family == "ID3":
			frame_id, separator, suffix = key.partition(":")
			frame = copy.deepcopy(self.tags.get(key))
			if key == "UFID:http://musicbrainz.org":
				frame = UFID(owner="http://musicbrainz.org", data=text.encode("ascii"))
			elif frame_id == "SYLT":
				if frame is None:
					desc, lang = suffix.rsplit(":", 1) if ":" in suffix else ("", "eng")
					frame = SYLT(encoding=1, desc=desc, lang=lang, format=2, type=1)
				frame.text = encode_sylt(text)
			elif frame_id == "USLT":
				if frame is None:
					desc, lang = suffix.rsplit(":", 1) if ":" in suffix else ("", "eng")
					frame = USLT(encoding=1, desc=desc, lang=lang)
				frame.text = text
			elif frame is not None and isinstance(frame, UrlFrame):
				frame.url = text
			elif frame is not None and (isinstance(frame, TextFrame) or frame_id == "COMM"):
				frame.text = values
			elif frame_id == "TXXX" and separator:
				frame = TXXX(encoding=1, desc=suffix, text=values)
			elif frame_id == "COMM":
				desc, lang = suffix.rsplit(":", 1) if ":" in suffix else ("", "eng")
				frame = Frames[frame_id](encoding=1, desc=desc, lang=lang, text=values)
			elif frame_id in Frames and issubclass(Frames[frame_id], TextFrame) and frame_id != "TXXX":
				frame = Frames[frame_id](encoding=1, text=values)
			elif frame_id in Frames and issubclass(Frames[frame_id], UrlFrame):
				frame = Frames[frame_id](url=text, desc=suffix) if frame_id == "WXXX" else Frames[frame_id](url=text)
			else:
				raise ValueError(f"Unsupported ID3 frame: {key}. Use TXXX:name for custom text.")
			if frame.HashKey != key:
				raise ValueError(f"Use the full native key: {frame.HashKey}")
			if isinstance(frame, TimeStampTextFrame):
				for value, stamp in zip(values, frame.text, strict=True):
					normalized = value.replace("T", " ")
					if str(stamp) != normalized or not re.fullmatch(
						r"[0-9]{4}(?:-[0-9]{2}(?:-[0-9]{2}(?: [0-9]{2}(?::[0-9]{2}(?::[0-9]{2})?)?)?)?)?",
						normalized,
					):
						raise ValueError(f"{key} requires YYYY-MM-DD HH:MM:SS or a shorter valid timestamp.")
					parts = list(map(int, re.split(r"[- :]", normalized)))
					defaults = [1, 1, 1, 0, 0, 0]
					datetime.datetime(*(parts + defaults[len(parts) :]))  # noqa: DTZ001
			self.tags.add(frame)
		elif self.family == "MP4":
			if key.startswith("----:"):
				if len(key.split(":")) != 3:
					raise ValueError("MP4 custom keys must be ----:namespace:name.")
				self.tags[key] = [
					MP4FreeForm(value.encode("utf-8"))
					for value in ([text] if key.lower().endswith(":syncedlyrics") and not explicit_values else values)
				]
			elif entry and entry.kind == "JSON numbers / booleans":
				parsed = json.loads(text)
				old = self.tags[key]
				if isinstance(old, bool):
					if not isinstance(parsed, bool):
						raise TypeError(f"{key} requires true or false.")
					self.tags[key] = parsed
					return
				if (
					not isinstance(parsed, list)
					or not parsed
					or (any(type(value) is not type(old[0]) for value in parsed) and not isinstance(old[0], tuple))
				):
					raise ValueError(f"Keep the JSON value types used by {key}.")
				if isinstance(old[0], tuple):
					if any(
						not isinstance(value, list)
						or len(value) != 2
						or any(type(number) is not int for number in value)
						for value in parsed
					):
						raise ValueError("Number pairs require [[number, total]].")
					parsed = [tuple(value) for value in parsed]
				self.tags[key] = parsed
			elif key == "tmpo":
				self.tags[key] = [int(text)]
			elif key == "cpil":
				if text.lower() not in ("true", "false"):
					raise ValueError("Compilation must be true or false.")
				self.tags[key] = text.lower() == "true"
			elif key.startswith("©") or key in MP4_TEXT_KEYS:
				self.tags[key] = [text] if key == "©lyr" and not explicit_values else values
			else:
				raise ValueError(f"Unsupported MP4 atom: {key}. Use ----:com.apple.iTunes:name for custom text.")
		elif self.family == "APE":
			if (
				not 2 <= len(key) <= 255
				or any(not 32 <= ord(char) <= 126 for char in key)
				or key.lower() in ("id3", "tag", "oggs", "mp+")
			):
				raise ValueError("APEv2 keys require 2-255 printable ASCII characters and cannot be reserved names.")
			self.tags[key] = text if key.lower() in LYRIC_NAMES and not explicit_values else values
		else:
			if not key or any(not 32 <= ord(char) <= 125 or char == "=" for char in key):
				raise ValueError("Vorbis keys require printable ASCII characters other than '='.")
			self.tags[key] = [text] if key.lower() in LYRIC_NAMES and not explicit_values else values

	def artwork(self) -> list[bytes]:
		if self.family == "ID3":
			return [frame.data for frame in self.tags.getall("APIC")]
		if self.family == "MP4":
			return list(self.tags.get("covr", []))
		if isinstance(self.audio, FLAC):
			return [picture.data for picture in self.audio.pictures]
		if self.family == "APE":
			return [
				bytes(value).split(b"\x00", 1)[1]
				for key, value in self.tags.items()
				if key.lower().startswith("cover art") and isinstance(value, APEBinaryValue) and b"\x00" in bytes(value)
			]
		result = [Picture(base64.b64decode(value)).data for value in self.tags.get("metadata_block_picture", [])]
		result.extend(base64.b64decode(value) for value in self.tags.get("coverart", []))
		return result

	def set_artwork(self, data: bytes | None) -> None:
		mime, width, height = "", 0, 0
		if data is not None:
			with Image.open(io.BytesIO(data)) as image:
				if image.format not in ("JPEG", "PNG"):
					raise ValueError("Embedded artwork must be a JPEG or PNG image.")
				mime, width, height = Image.MIME[image.format], image.width, image.height
				image.verify()
		if self.family == "ID3":
			self.tags.delall("APIC")
			if data is not None:
				self.tags.add(APIC(encoding=1, mime=mime, type=3, desc="Cover", data=data))
		elif self.family == "MP4":
			self.tags.pop("covr", None)
			if data is not None:
				self.tags["covr"] = [
					MP4Cover(data, imageformat=MP4Cover.FORMAT_PNG if mime == "image/png" else MP4Cover.FORMAT_JPEG)
				]
		elif self.family == "APE":
			for key in list(self.tags):
				if key.lower().startswith("cover art"):
					del self.tags[key]
			if data is not None:
				self.tags["Cover Art (Front)"] = APEBinaryValue(
					(b"cover.png" if mime == "image/png" else b"cover.jpg") + b"\x00" + data
				)
		else:
			if isinstance(self.audio, FLAC):
				self.audio.clear_pictures()
			for key in ("metadata_block_picture", "coverart", "coverartmime"):
				if key in self.tags:
					del self.tags[key]
			if data is not None:
				picture = Picture()
				picture.type, picture.mime, picture.width, picture.height, picture.depth, picture.data = (
					3,
					mime,
					width,
					height,
					24,
					data,
				)
				if isinstance(self.audio, FLAC):
					self.audio.add_picture(picture)
				else:
					self.tags["metadata_block_picture"] = [base64.b64encode(picture.write()).decode("ascii")]

	def save(self) -> None:
		self.ensure_safe_offsets()
		if self.family == "ID3":
			self.audio.save(v2_version=self.id3_version, v23_sep=None)
		else:
			self.audio.save()

	def ensure_safe_offsets(self) -> None:
		if self.family != "ID3":
			return

		def check(tags: ID3) -> None:
			for frame in tags.values():
				if frame.FrameID == "ASPI" or (
					frame.FrameID == "CHAP" and (frame.start_offset != 0xFFFFFFFF or frame.end_offset != 0xFFFFFFFF)
				):
					raise ValueError(
						f"Cannot safely preserve ID3 byte offsets in {self.path.name}. Use an external editor."
					)
				if hasattr(frame, "sub_frames"):
					check(frame.sub_frames)

		check(self.tags)

	def upgrade_id3(self) -> None:
		if self.family != "ID3":
			raise ValueError("This file uses a native tag format other than ID3.")
		if (
			self.id3_version == 4
			and not self.legacy_opaque
			and not any(
				key in self.tags for key in ("TYER", "TDAT", "TIME", "TORY", "IPLS", "RVAD", "EQUA", "TRDA", "TSIZ")
			)
		):
			return
		converted = copy.deepcopy(self.tags)
		converted.update_to_v24()

		def check(before: ID3, after: ID3, prefix: str = "") -> None:
			if getattr(before, "unknown_frames", []):
				raise ValueError(f"Cannot safely upgrade unknown ID3 frames in {self.path.name}.")
			translations = {"TYER": "TDRC", "TDAT": "TDRC", "TIME": "TDRC", "TORY": "TDOR", "IPLS": "TIPL"}
			for key, frame in before.items():
				if key not in after and key not in translations:
					raise ValueError(f"Upgrade would discard {prefix}{key} in {self.path.name}.")
				if key in translations:
					target = after.get(translations[key])
					if target is None:
						raise ValueError(f"Upgrade could not translate {prefix}{key} in {self.path.name}.")
					if key == "IPLS" and target.people != frame.people:
						raise ValueError(f"Conflicting performer credits in {self.path.name}.")
					if key in ("TYER", "TORY", "TDAT", "TIME"):
						stamps = list(map(str, target.text))
						for index, value in enumerate(map(str, frame.text)):
							stamp = stamps[index].replace(" ", "T") if index < len(stamps) else ""
							valid = bool(re.fullmatch(r"[0-9]{4}", value))
							if key in ("TYER", "TORY"):
								valid = valid and stamp.startswith(value)
							elif key == "TDAT":
								valid = (
									valid
									and stamp[4:10] == f"-{value[2:]}-{value[:2]}"
									and 1 <= int(value[:2]) <= 31
									and 1 <= int(value[2:]) <= 12
								)
							else:
								valid = (
									valid
									and stamp[10:16] == f"T{value[:2]}:{value[2:]}"
									and int(value[:2]) < 24
									and int(value[2:]) < 60
								)
							if not valid:
								raise ValueError(
									f"Upgrade would lose or conflict with {prefix}{key} in {self.path.name}."
								)
				if hasattr(frame, "sub_frames"):
					check(frame.sub_frames, after[key].sub_frames, prefix + key + "/")

		check(self.tags, converted)
		self.tags = self.audio.tags = converted
		self.id3_version = 4
		self.label = self.label.split(" → ")[0] + " → ID3v2.4"

	def ensure_unchanged(self) -> None:
		if file_stamp(self.path) != self.stamp:
			raise ValueError(f"File changed since opening the editor: {self.path.name}. Reopen to load current tags.")
		if self.path.stat().st_nlink > 1:
			raise ValueError(f"Cannot safely replace a file with hard links: {self.path.name}. Use an external editor.")


@dataclass
class TagChanges:
	main: dict[str, str | list[str]] = field(default_factory=dict)
	entries: dict[str, str | list[str]] = field(default_factory=dict)
	art_changed: bool = False
	art_data: bytes | None = None
	id3_upgrade: bool = False

	@property
	def changed(self) -> bool:
		return bool(self.main or self.entries or self.art_changed or self.id3_upgrade)


class ScopedChanges(MutableMapping[str, str]):
	"""A UI view over the pending values of one file or all selected files."""

	def __init__(self, session: TagEditSession, attribute: str) -> None:
		self.session, self.attribute = session, attribute

	def _maps(self) -> list[dict]:
		return [getattr(self.session.pending[doc.path], self.attribute) for doc in self.session.scope_documents]

	def __getitem__(self, key: str) -> str:
		"""Return a common staged value, formatted for the UI."""
		maps = self._maps()
		value = maps[0][key]
		if any(key not in mapping or mapping[key] != value for mapping in maps):
			raise KeyError(key)
		if isinstance(value, list):
			if self.attribute == "entries":
				doc = self.session.scope_documents[0]
				entry = self.session.effective_document(doc).entries().get(doc.portable_key(key))
				if entry is not None:
					return entry.value
			return ("; " if self.attribute == "main" else "\n").join(value)
		return value

	def __setitem__(self, key: str, value: str) -> None:
		"""Stage a value for every file in the current scope."""
		for mapping in self._maps():
			mapping[key] = value

	def __delitem__(self, key: str) -> None:
		"""Remove a staged value throughout the current scope."""
		found = False
		for mapping in self._maps():
			if key in mapping:
				del mapping[key]
				found = True
		if not found:
			raise KeyError(key)

	def __iter__(self) -> Iterator[str]:
		"""Iterate keys whose pending values agree throughout the scope."""
		for key in self._maps()[0]:
			try:
				self[key]
			except KeyError:
				continue
			yield key

	def __len__(self) -> int:
		"""Count common pending values."""
		return sum(1 for key in self)

	def pop(self, key: str, default: str | None = None) -> str | None:
		value = self.get(key, default)
		with suppress(KeyError):
			del self[key]
		return value


class TagEditSession:
	def __init__(self, paths: list[str], *, progress: Callable[[int, int, Path], None] | None = None) -> None:
		documents = {}
		for index, path in enumerate(paths):
			if progress is not None:
				progress(index, len(paths), Path(path))
			doc = TagDocument(path)
			documents[doc.path] = doc
			if progress is not None:
				progress(index + 1, len(paths), doc.path)
		self.documents = list(documents.values())
		self.pending = {doc.path: TagChanges() for doc in self.documents}
		self.selected_document: int | None = None
		self._effective_cache: dict[Path, tuple[TagChanges, TagDocument]] = {}

	@property
	def scope_documents(self) -> list[TagDocument]:
		return self.documents if self.selected_document is None else [self.documents[self.selected_document]]

	@property
	def main_changes(self) -> ScopedChanges:
		return ScopedChanges(self, "main")

	@main_changes.setter
	def main_changes(self, values: dict[str, str]) -> None:
		for doc in self.scope_documents:
			self.pending[doc.path].main = dict(values)

	@property
	def entry_changes(self) -> ScopedChanges:
		return ScopedChanges(self, "entries")

	@entry_changes.setter
	def entry_changes(self, values: dict[str, str]) -> None:
		for doc in self.scope_documents:
			self.pending[doc.path].entries = dict(values)

	@property
	def art_changed(self) -> bool:
		return any(self.pending[doc.path].art_changed for doc in self.scope_documents)

	@art_changed.setter
	def art_changed(self, value: bool) -> None:
		for doc in self.scope_documents:
			self.pending[doc.path].art_changed = value

	@property
	def art_data(self) -> bytes | None:
		return self.pending[self.scope_documents[0].path].art_data

	@art_data.setter
	def art_data(self, data: bytes | None) -> None:
		for doc in self.scope_documents:
			self.pending[doc.path].art_data = data

	@property
	def changed(self) -> bool:
		return any(changes.changed for changes in self.pending.values())

	def field_edited(self, key: str, *, main: bool = False) -> bool:
		"""Compare effective field values with each file's original values."""
		for doc in self.scope_documents:
			changes = self.pending[doc.path]
			if not changes.main and not changes.entries:
				continue
			candidate = self.effective_document(doc)
			try:
				native = candidate.key_for(key) if main else candidate.portable_key(key)
				original_key = doc.key_for(key) if main else doc.portable_key(key)
			except ValueError:
				continue
			if main and key not in VALUE_FIELDS:
				if candidate.main_value(key) != doc.main_value(key):
					return True
				continue
			before, after = doc.text_values(original_key), candidate.text_values(native)
			if before is not None or after is not None:
				if (before or []) != (after or []):
					return True
			elif doc.tags.get(original_key) != candidate.tags.get(native):
				return True
		return False

	def rollback_field(self, key: str, *, main: bool = False) -> None:
		"""Restore each file's original tag, retaining edits outside this field/scope."""
		for doc in self.scope_documents:
			changes = self.pending[doc.path]
			if not changes.main and not changes.entries:
				continue
			candidate = self.effective_document(doc)
			try:
				native = candidate.key_for(key) if main else candidate.portable_key(key)
			except ValueError:
				continue
			artist = next((name for name in ("artist", "albumartist") if native in candidate.main_keys(name)), None)
			restored = set(candidate.main_keys(key)) if main else {native}
			related = (
				{"musicbrainzartistid", "artistcredit"}
				if artist == "artist"
				else {"musicbrainzalbumartistid", "albumartistcredit"}
				if artist == "albumartist"
				else set()
			)
			for name in list(changes.main):
				if native in candidate.main_keys(name):
					del changes.main[name]
			for name in list(changes.entries):
				metadata = re.sub(r"[^a-z]", "", name.rsplit(":", 1)[-1].lower())
				if candidate.portable_key(name) in restored or metadata in related:
					del changes.entries[name]

	def effective_document(self, doc: TagDocument) -> TagDocument:
		changes = self.pending[doc.path]
		if not changes.changed:
			return doc
		cached = self._effective_cache.get(doc.path)
		if cached is not None and changes == cached[0]:
			return cached[1]
		candidate = copy.deepcopy(doc)
		self._apply(candidate, changes)
		self._effective_cache[doc.path] = (copy.deepcopy(changes), candidate)
		return candidate

	@staticmethod
	def _apply(doc: TagDocument, changes: TagChanges) -> None:
		if changes.changed:
			doc.ensure_safe_offsets()
		if changes.changed and doc.legacy_opaque:
			raise ValueError(
				f"Cannot safely upgrade opaque ID3v2.2 frames in {doc.path.name}. Use an external tag editor."
			)
		if changes.id3_upgrade:
			doc.upgrade_id3()
		for field_name, value in changes.main.items():
			doc.set_main(field_name, value)
		for key, value in changes.entries.items():
			doc.set_entry(key, value)
		if changes.art_changed:
			doc.set_artwork(changes.art_data)
		if changes.id3_upgrade:
			doc.upgrade_id3()

	def common_main(self, field: str, include_changes: bool = True) -> str | None:
		if field in VALUE_FIELDS and self.common_values(field, main=True, include_changes=include_changes) is None:
			return None
		values = [
			(self.effective_document(doc) if include_changes else doc).main_value(field) for doc in self.scope_documents
		]
		return values[0] if values and all(value == values[0] for value in values) else None

	def common_values(self, key: str, *, main: bool = False, include_changes: bool = True) -> list[str] | None:
		values = []
		for original in self.scope_documents:
			doc = self.effective_document(original) if include_changes else original
			native = doc.key_for(key) if main else doc.portable_key(key)
			values.append(doc.text_values(native) if native in doc.tags else [])
		return copy.deepcopy(values[0]) if values and all(value == values[0] for value in values) else None

	def value_changes(
		self,
		key: str,
		values: list[str],
		*,
		main: bool = False,
		mode: str = "replace",
		slots: dict[Path, tuple[int, bool]] | None = None,
	) -> dict[Path, TagChanges]:
		"""Build edits; slots optionally identify each file's (index, existing-value flag)."""
		if mode not in ("replace", "append", "remove"):
			raise ValueError("Unknown value editing action.")
		updates = {}
		for original in self.scope_documents:
			doc = self.effective_document(original)
			native = doc.key_for(key) if main else doc.portable_key(key)
			current = doc.text_values(native) if native in doc.tags else []
			if current is None:
				raise ValueError(f"{native} is not an editable list of text values.")
			result = (
				list(values)
				if mode == "replace"
				else current + values
				if mode == "append"
				else [value for value in current if value not in values]
			)
			if slots is not None:
				if mode != "replace" or len(values) > 1:
					raise ValueError("Individual entries require one replacement value.")
				index, present = slots[original.path]
				if index < 0:
					raise ValueError("Value index must not be negative.")
				result = list(current)
				index = min(index, len(result))
				result[index : index + int(present)] = values
			if result == current:
				continue
			update = TagChanges(main={key: result}) if main else TagChanges(entries={key: result})
			artist_field = (
				key if main else next((name for name in ("artist", "albumartist") if native == doc.key_for(name)), None)
			)
			if artist_field in ("artist", "albumartist"):
				# Artist identifiers and formatted credits belong to the original artist list.
				names = (
					{"musicbrainzartistid", "artistcredit"}
					if artist_field == "artist"
					else {"musicbrainzalbumartistid", "albumartistcredit"}
				)
				for tagged in doc.tags.keys():
					name = re.sub(r"[^a-z]", "", tagged.rsplit(":", 1)[-1].lower())
					if name in names:
						update.entries[tagged] = ""
			updates[original.path] = update
		return updates

	def edit_values(self, key: str, values: list[str], *, main: bool = False, mode: str = "replace") -> None:
		self.stage_tracks(self.value_changes(key, values, main=main, mode=mode))

	def upgrade_id3(self) -> tuple[int, int]:
		updates = {
			doc.path: TagChanges(id3_upgrade=True)
			for doc in self.scope_documents
			if doc.family == "ID3"
			and not self.pending[doc.path].id3_upgrade
			and (self.effective_document(doc).id3_version != 4 or doc.tags.version[:2] != (2, 4))
		}
		self.stage_tracks(updates)
		return len(updates), sum(doc.family != "ID3" for doc in self.scope_documents)

	def entries(self, lyrics: bool | None, include_changes: bool = True) -> list[TagEntry]:
		documents = [self.effective_document(doc) if include_changes else doc for doc in self.scope_documents]
		maps = [doc.entries() for doc in documents]
		keys = set().union(*(mapping.keys() for mapping in maps))
		if include_changes:
			keys.update(doc.portable_key(key) for doc in documents for key in self.pending[doc.path].entries)
		if lyrics:
			keys.update(key for doc in documents for key in doc.lyric_defaults())
		main_keys = {doc.key_for(field) for doc in documents for field in MAIN_FIELDS}
		result = []
		for key in sorted(keys):
			present = [mapping.get(key) for mapping in maps]
			is_lyric = key in {native_key for doc in documents for native_key in doc.lyric_defaults()}
			sample = next((entry for entry in present if entry is not None), TagEntry(key, "", lyrics=is_lyric))
			if (lyrics is not None and sample.lyrics != lyrics) or (not sample.lyrics and key in main_keys):
				continue
			values = [entry.value if entry else "" for entry in present]
			value = values[0] if all(value == values[0] for value in values) else "<Multiple values>"
			result.append(
				TagEntry(
					key, value, sample.kind, all(entry is None or entry.editable for entry in present), sample.lyrics
				)
			)
		return result

	def validate(
		self,
		main: dict[str, str | list[str]],
		entries: dict[str, str | list[str]],
		art_changed: bool = False,
		art_data: bytes | None = None,
	) -> None:
		for doc in self.scope_documents:
			changes = copy.deepcopy(self.pending[doc.path])
			changes.main.update(main)
			changes.entries.update(entries)
			if art_changed:
				changes.art_changed, changes.art_data = True, art_data
			self._apply(copy.deepcopy(doc), changes)

	def stage_main(self, name: str, text: str) -> None:
		updates = {}
		for doc in self.scope_documents:
			value = text
			candidate = self.effective_document(doc)
			if name in VALUE_FIELDS and text == candidate.main_value(name):
				native = candidate.tags.get(candidate.key_for(name))
				if isinstance(native, TextFrame):
					value = list(map(str, native.text))
				elif isinstance(native, (list, APETextValue)):
					value = list(native)
			updates[doc.path] = TagChanges(main={name: value})
		self.stage_tracks(updates)

	def stage_tracks(self, changes: dict[Path, TagChanges]) -> None:
		"""Validate the full batch before merging pending edits."""
		merged = {}
		for path, update in changes.items():
			pending = copy.deepcopy(self.pending[path])
			doc = next(doc for doc in self.documents if doc.path == path)
			candidate = self.effective_document(doc)
			for name in update.main:
				for key in list(pending.entries):
					if candidate.portable_key(key) == candidate.key_for(name):
						del pending.entries[key]
			pending.main.update(update.main)
			for key in update.entries:
				for name in list(pending.main):
					if candidate.portable_key(key) == candidate.key_for(name):
						del pending.main[name]
			pending.entries.update(update.entries)
			if update.art_changed:
				pending.art_changed, pending.art_data = True, update.art_data
			pending.id3_upgrade |= update.id3_upgrade
			doc = next(doc for doc in self.documents if doc.path == path)
			self._apply(copy.deepcopy(doc), pending)
			merged[path] = pending
		self.pending.update(merged)

	def fix_mojibake(
		self, encoding: str | None = None, encodings: tuple[str, ...] = MOJIBAKE_ENCODINGS
	) -> tuple[int, int, int]:
		"""Stage text repairs in the current scope; return fields, files, undetected."""
		if encoding is not None and encoding not in encodings:
			raise ValueError("Unsupported Mojibake encoding.")
		updates = {}
		field_count = 0
		undetected = 0
		for original in self.scope_documents:
			doc = self.effective_document(original)
			entries = doc.entries()
			values = {key: doc.text_values(key) for key, entry in entries.items() if entry.editable}
			values = {key: texts for key, texts in values.items() if texts is not None}
			hints = [value for name in ("artist", "album") for value in values.get(doc.key_for(name), [])]
			detected = encoding or detect_mojibake_encoding(
				hints, [text for texts in values.values() for text in texts], str(doc.path.parent), encodings
			)
			if detected is None:
				undetected += 1
				continue
			pending = copy.deepcopy(self.pending[doc.path])
			main_keys = {doc.key_for(name): name for name in MAIN_FIELDS}
			changed = False
			for key, texts in values.items():
				fixed = [repair_mojibake_text(text, detected) for text in texts]
				if fixed == texts:
					continue
				for staged_key in list(pending.entries):
					if doc.portable_key(staged_key) == key:
						del pending.entries[staged_key]
				if key in main_keys:
					name = main_keys[key]
					pending.main[name] = fixed if name in VALUE_FIELDS else fixed[0]
				else:
					pending.entries[key] = fixed
				changed = True
				field_count += 1
			if changed:
				self._apply(copy.deepcopy(original), pending)
				updates[doc.path] = pending
		self.pending.update(updates)
		return field_count, len(updates), undetected

	def write(self) -> int:
		"""Prepare changed files before committing; roll back if a commit fails."""
		if not self.changed:
			return 0
		documents = [doc for doc in self.documents if self.pending[doc.path].changed]
		for doc in documents:
			self.effective_document(doc)
			doc.ensure_unchanged()
		prepared: list[tuple[TagDocument, Path, Path]] = []
		committed = []
		retained = set()
		try:
			for doc in documents:
				doc.ensure_unchanged()
				staged_fd, staged_name = tempfile.mkstemp(
					prefix=".tauon-tags-", suffix=doc.path.suffix, dir=doc.path.parent
				)
				os.close(staged_fd)
				try:
					backup_fd, backup_name = tempfile.mkstemp(
						prefix=".tauon-backup-", suffix=doc.path.suffix, dir=doc.path.parent
					)
				except OSError:
					Path(staged_name).unlink(missing_ok=True)
					raise
				os.close(backup_fd)
				staged, backup = Path(staged_name), Path(backup_name)
				prepared.append((doc, staged, backup))
				copy_tag_file(doc.path, staged)
				copy_tag_file(doc.path, backup)
				candidate = TagDocument(staged)
				self._apply(candidate, self.pending[doc.path])
				candidate.save()
				TagDocument(staged)
			for doc, staged, backup in prepared:
				doc.ensure_unchanged()
				staged.replace(doc.path)
				committed.append((doc, backup, None))
				committed[-1] = (doc, backup, file_stamp(doc.path))
		except Exception as error:
			for doc, backup, stamp in reversed(committed):
				try:
					if stamp is None or file_stamp(doc.path) != stamp:
						retained.add(backup)
						continue
					backup.replace(doc.path)
				except OSError:
					retained.add(backup)
			if retained:
				raise OSError(
					f"Save failed; restore these retained backups: {', '.join(map(str, retained))}"
				) from error
			raise
		finally:
			for _source_doc, staged, backup in prepared:
				staged.unlink(missing_ok=True)
				if backup not in retained:
					backup.unlink(missing_ok=True)
		return len(documents)
