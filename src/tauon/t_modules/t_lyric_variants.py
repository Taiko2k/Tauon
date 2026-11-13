"""Alternate lyrics for one track (#1303): languages, translations, synced or plain.

Sources follow existing conventions:
- Sidecar files named like subtitles in mpv/Jellyfin/Plex: Song.lrc, Song.en.lrc,
  Song.jpn.lrc, Song.ja.romaji.lrc. ISO 639-1 and 639-2 codes both work.
- ID3 USLT/SYLT frames, which each carry a language code and a description.
- OpenSubsonic structuredLyrics, which carry lang and kind.

parse_lrc also groups LRC lines that belong together (#567): repeated timestamps
(a translation under the original) and untimed lines under a timed one.
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from tauon.t_modules.t_tagscan import lyrics_are_synced

if TYPE_CHECKING:
	from collections.abc import Callable, Iterable

LYRIC_EXTENSIONS = (".lrc", ".txt")

# Subtitle-style flags that mean nothing for lyrics
IGNORED_FLAGS = {"default", "forced", "sdh", "cc", "hi", "lyrics", "lyric"}

KIND_TAGS = {"pronunciation": "pron"}

NO_LANGUAGE = {"", "und", "xxx", "zxx", "mis", "mul", "unk"}

# ISO 639-2 (B and T) to 639-1, so Song.eng.lrc and Song.en.lrc count as one language
ISO639_2_TO_1 = {
	"ara": "ar", "cat": "ca", "ces": "cs", "cze": "cs", "chi": "zh", "zho": "zh", "dan": "da",
	"deu": "de", "ger": "de", "ell": "el", "gre": "el", "eng": "en", "spa": "es", "fas": "fa",
	"per": "fa", "fin": "fi", "fra": "fr", "fre": "fr", "heb": "he", "hin": "hi", "hun": "hu",
	"ind": "id", "ita": "it", "jpn": "ja", "kor": "ko", "msa": "ms", "may": "ms", "nld": "nl",
	"dut": "nl", "nor": "no", "nob": "nb", "pol": "pl", "por": "pt", "ron": "ro", "rum": "ro",
	"rus": "ru", "swe": "sv", "tha": "th", "tgl": "tl", "tur": "tr", "ukr": "uk", "vie": "vi",
}

LANG_TOKEN_RE = re.compile(r"^[a-z]{2,3}(?:-[a-z0-9]{2,8})*$")
QUALIFIER_TOKEN_RE = re.compile(r"^[\w-]{1,24}$")
LRC_STAMP_RE = re.compile(r"\[(\d{1,3}):(\d{1,2})(?:[.:](\d{1,3}))?\]")
LRC_ID_TAG_RE = re.compile(r"^\[[A-Za-z#]+:.*\]$")


def normalize_lang(code: str | None) -> str:
	"""Lowercase a language code and fold 639-2 to 639-1. Unknown codes give ""."""
	if not code:
		return ""
	code = str(code).strip().replace("_", "-").lower()
	primary, _, rest = code.partition("-")
	if primary in NO_LANGUAGE:
		return ""
	primary = ISO639_2_TO_1.get(primary, primary)
	return f"{primary}-{rest}" if rest else primary


@dataclass
class LyricVariant:
	synced: bool
	text: str
	lang: str = ""
	tag: str = ""      # Extra qualifier: an ID3 description, a file flag like "romaji", a server kind
	source: str = ""   # "tags", "file", "server"
	base: bool = False  # Came from track.lyrics / track.synced

	@property
	def key(self) -> str:
		"""What the remembered preference matches against."""
		if self.tag:
			return f"{self.lang}.{self.tag}" if self.lang else self.tag
		return self.lang

	@property
	def label(self) -> str:
		"""Short switcher label, or "" for an unlabelled variant."""
		if self.lang and self.tag:
			return f"{self.lang.upper()}·{self.tag[:6]}"
		if self.lang:
			return self.lang.upper()
		return self.tag[:8].capitalize()


def sidecar_qualifier(stem: str, name: str) -> tuple[str, str, str] | None:
	"""Return (lang, tag, extension) if a file is a lyrics sidecar of the track, else None.

	Song.lrc gives ("", "", ".lrc"); Song.en.romaji.lrc gives ("en", "romaji", ".lrc").
	"""
	base, ext = os.path.splitext(name)
	ext = ext.lower()
	if ext not in LYRIC_EXTENSIONS:
		return None
	if base == stem:
		return "", "", ext
	if not base.startswith(stem + "."):
		return None
	qualifier = base[len(stem) + 1:]
	if not qualifier or len(qualifier) > 40:
		return None
	tokens = [token for token in qualifier.lower().split(".") if token]
	if not tokens or not all(QUALIFIER_TOKEN_RE.match(token) for token in tokens):
		return None
	lang = ""
	found_lang = False
	tags: list[str] = []
	for token in tokens:
		if token in IGNORED_FLAGS:
			continue
		if not found_lang and LANG_TOKEN_RE.match(token):
			lang = normalize_lang(token)
			found_lang = True
			continue
		tags.append(token)
	return lang, ".".join(tags), ext


def scan_sidecar_variants(
	folder: str, filename: str, read_text: Callable[[Path], str | None],
) -> list[LyricVariant]:
	"""Every lyrics sidecar of a track, with and without a language suffix.

	A file is skipped when another non-lyrics file shares its full stem, so
	Song.remix.lrc stays with Song.remix.flac rather than joining Song.flac.
	"""
	stem = os.path.splitext(filename)[0]
	candidates: list[tuple[str, tuple[str, str, str]]] = []
	other_stems: set[str] = set()
	try:
		with os.scandir(folder) as entries:
			for entry in entries:
				name = entry.name
				if not name.startswith(stem):
					continue
				found = sidecar_qualifier(stem, name)
				if found is None:
					if name != filename:
						other_stems.add(os.path.splitext(name)[0])
					continue
				if entry.is_file():
					candidates.append((entry.path, found))
	except OSError:
		return []

	variants: list[LyricVariant] = []
	for path, (lang, tag, _ext) in sorted(candidates):
		candidate_stem = os.path.splitext(os.path.basename(path))[0]
		# Song.lrc is shared by Song.mp3 and Song.flac; only suffixed names can collide
		if candidate_stem != stem and candidate_stem in other_stems:
			continue
		text = read_text(Path(path))
		if not text or not text.strip():
			continue
		text = "\n".join(text.splitlines()).strip("\n")
		variants.append(LyricVariant(lyrics_are_synced(text), text, lang, tag, "file"))
	return variants


def sylt_to_lrc(entries: Iterable[tuple[str, int]]) -> str:
	"""SYLT (text, milliseconds) pairs as LRC, formatted like the tag scanner does."""
	return "\n".join(f"[{stamp // 60000:02d}:{stamp % 60000 / 1000:06.3f}]{text}" for text, stamp in entries)


def _junk_lyrics(text: str) -> bool:
	return 0 < len(text) < 150 and ("unavailable" in text or ".com" in text or "www." in text)


def id3_lyric_variants(tags: object) -> list[LyricVariant]:
	"""Every USLT and millisecond SYLT frame in an ID3 tag."""
	variants: list[LyricVariant] = []
	getall = getattr(tags, "getall", None)
	if getall is None:
		return variants
	for frame in getall("USLT"):
		text = str(frame.text or "").strip("\n")
		if not text.strip() or _junk_lyrics(text):
			continue
		desc = str(getattr(frame, "desc", "") or "").strip().lower()[:16]
		variants.append(LyricVariant(
			lyrics_are_synced(text), text, normalize_lang(getattr(frame, "lang", "")), desc, "tags"))
	for frame in getall("SYLT"):
		if getattr(frame, "format", 0) != 2:
			continue
		text = sylt_to_lrc(frame.text)
		if not text.strip():
			continue
		desc = str(getattr(frame, "desc", "") or "").strip().lower()[:16]
		variants.append(LyricVariant(True, text, normalize_lang(getattr(frame, "lang", "")), desc, "tags"))
	return variants


def read_embedded_variants(path: str) -> list[LyricVariant]:
	"""Lyrics frames from a file's ID3 tag. Other tag formats hold one lyric, already on the track."""
	try:
		import mutagen  # noqa: PLC0415
		audio = mutagen.File(path)
	except Exception:
		logging.debug(f"Could not read tags for lyric variants: {path}")
		return []
	if audio is None or audio.tags is None:
		return []
	return id3_lyric_variants(audio.tags)


def structured_lyric_variants(
	entries: Iterable[dict], plain: Callable[[dict], str], lrc: Callable[[dict], str],
) -> list[LyricVariant]:
	"""OpenSubsonic structuredLyrics entries as variants."""
	variants: list[LyricVariant] = []
	for entry in entries:
		if not isinstance(entry, dict):
			continue
		kind = str(entry.get("kind") or "main").lower()
		tag = "" if kind in ("main", "translation") else KIND_TAGS.get(kind, kind[:12])
		lang = normalize_lang(entry.get("lang"))
		if entry.get("synced"):
			text = lrc(entry)
			if text:
				variants.append(LyricVariant(True, text, lang, tag, "server"))
				continue
		text = plain(entry)
		if text:
			variants.append(LyricVariant(False, text, lang, tag, "server"))
	return variants


def _compare_text(text: str, synced: bool = False) -> str:
	"""Text to spot duplicates by. Synced text compares by timing and words, so
	[00:02.00] and [00:02.000] or added ID tags still match."""
	if synced:
		entries = parse_lrc(text.splitlines())
		if entries:
			return "\n".join(f"{round(stamp * 100)}|{line}" for stamp, line in entries)
	return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def merge_variants(base_synced: str, base_plain: str, extras: Iterable[LyricVariant]) -> list[LyricVariant]:
	"""The track's own lyrics plus extras, deduplicated by text and grouped by language.

	A base variant with the same text as a labelled extra takes that label.
	Variants that would share a label get their source as a qualifier.
	"""
	merged: list[LyricVariant] = []
	seen: dict[tuple[bool, str], LyricVariant] = {}

	def add(variant: LyricVariant) -> None:
		compare = _compare_text(variant.text, variant.synced)
		if not compare:
			return
		key = (variant.synced, compare)
		existing = seen.get(key)
		if existing is not None:
			if not existing.key and variant.key:
				existing.lang, existing.tag = variant.lang, variant.tag
			return
		seen[key] = variant
		merged.append(variant)

	if base_synced:
		add(LyricVariant(True, base_synced, base=True))
	if base_plain:
		add(LyricVariant(False, base_plain, base=True))
	for variant in extras:
		add(LyricVariant(variant.synced, variant.text, variant.lang, variant.tag, variant.source))

	taken: set[tuple[str, bool]] = set()
	for variant in merged:
		if (variant.key, variant.synced) in taken:
			variant.tag = ".".join(part for part in (variant.tag, variant.source or "alt") if part)
			number = 2
			original = variant.tag
			while (variant.key, variant.synced) in taken:
				variant.tag = f"{original}{number}"
				number += 1
		taken.add((variant.key, variant.synced))

	order: dict[str, int] = {}
	for variant in merged:
		order.setdefault(variant.lang, len(order))
	merged.sort(key=lambda v: (order[v.lang], v.key, not v.synced))
	return merged


def choose_variant(variants: list[LyricVariant], synced: bool, preferred: str) -> LyricVariant | None:
	"""The variant of one kind to show, given the remembered key."""
	candidates = [variant for variant in variants if variant.synced == synced]
	if not candidates:
		return None
	for variant in candidates:
		if variant.key == preferred:
			return variant
	preferred_lang = preferred.split(".", 1)[0]
	if preferred_lang:
		for variant in candidates:
			if variant.lang == preferred_lang:
				return variant
	for variant in candidates:
		if variant.base:
			return variant
	return candidates[0]


def _stamp_seconds(match: re.Match[str]) -> float:
	minutes, seconds, fraction = match.groups()
	value = int(minutes) * 60 + int(seconds)
	if fraction:
		value += int(fraction) / (10 ** len(fraction))
	return value


def parse_lrc(lines: Iterable[str]) -> list[tuple[float, str]]:
	"""(seconds, text) entries from LRC lines, sorted by time.

	Lines sharing a timestamp are joined into one entry, as are untimed lines
	following a timed line, so translations and romanisations stay with their
	original line. ID tags like [ar:...] and blank lines are skipped.
	"""
	entries: list[list] = []
	by_time: dict[float, list] = {}
	last: list[list] = []
	for raw in lines:
		line = raw.strip()
		if not line:
			continue
		stamps: list[float] = []
		position = 0
		while True:
			match = LRC_STAMP_RE.match(line, position)
			if match is None:
				break
			stamps.append(_stamp_seconds(match))
			position = match.end()
		if stamps:
			text = line[position:].strip()
			last = []
			for stamp in stamps:
				entry = by_time.get(stamp)
				if entry is None:
					entry = [stamp, [text]]
					by_time[stamp] = entry
					entries.append(entry)
				elif text:
					entry[1].append(text)
				last.append(entry)
			continue
		if LRC_ID_TAG_RE.match(line):
			last = []
			continue
		for entry in last:
			entry[1].append(line)

	entries.sort(key=lambda entry: entry[0])
	return [(stamp, "\n".join(part for part in texts if part)) for stamp, texts in entries]

