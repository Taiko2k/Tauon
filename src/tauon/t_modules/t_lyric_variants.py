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
from typing import TYPE_CHECKING, NamedTuple

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
# Enhanced LRC word stamp: [00:12.00]<00:12.00>Some <00:12.40>words
LRC_WORD_STAMP_RE = re.compile(r"<(\d{1,3}):(\d{1,2})(?:[.:](\d{1,3}))?>")


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
		entries = parse_lrc_lines(text.splitlines())
		if entries:
			# Word stamps count, so a word-timed copy isn't merged into a line-timed one
			return "\n".join(
				f"{round(entry.time * 100)}|{entry.text}|{','.join(str(round(w.start * 100)) for w in entry.words)}"
				for entry in entries)
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


class LyricWord(NamedTuple):
	"""One timed span of a synced line. first/last are character offsets into
	the line's text (last exclusive). end is None until it's known."""
	start: float
	end: float | None
	first: int
	last: int


class LrcLine(NamedTuple):
	time: float
	text: str
	words: list[LyricWord]  # Empty unless the line has enhanced LRC word stamps


# Longest a final word is assumed to last when nothing marks its end
LAST_WORD_MAX = 3.0


def split_word_stamps(text: str, line_time: float = 0.0) -> tuple[str, list[LyricWord]]:
	"""Strip enhanced LRC <mm:ss.xx> word stamps from a line.

	Each stamp times the text up to the next stamp; text before the first stamp
	starts at line_time. A stamp followed only by spaces just ends the previous
	word. Returns the stripped text and its words (none if the stamps go backwards).
	"""
	pieces: list[tuple[float, str]] = []
	time = line_time
	position = 0
	for match in LRC_WORD_STAMP_RE.finditer(text):
		pieces.append((time, text[position:match.start()]))
		time = _stamp_seconds(match)
		position = match.end()
	if not pieces:
		return text, []
	pieces.append((time, text[position:]))

	joined = "".join(piece for _, piece in pieces)
	clean = joined.strip()
	offset = -(len(joined) - len(joined.lstrip()))
	words: list[LyricWord] = []
	for start, piece in pieces:
		first = offset + len(piece) - len(piece.lstrip())
		last = offset + len(piece.rstrip())
		offset += len(piece)
		if words:
			if start < words[-1].start:
				return clean, []
			if words[-1].end is None:
				words[-1] = words[-1]._replace(end=start)
		if last > first:
			words.append(LyricWord(start, None, first, last))
	return clean, words


def _close_last_word(words: list[LyricWord], next_time: float | None) -> list[LyricWord]:
	"""Give an unended final word an end: about twice the line's average word,
	stopping at the next line."""
	if not words or words[-1].end is not None:
		return words
	final = words[-1]
	timed = [w.end - w.start for w in words[:-1] if w.end is not None]
	length = min(LAST_WORD_MAX, max(0.6, 2 * sum(timed) / len(timed))) if timed else 1.0
	end = final.start + length
	if next_time is not None and next_time > final.start:
		end = min(end, next_time)
	return [*words[:-1], final._replace(end=max(end, final.start))]


def parse_lrc_lines(lines: Iterable[str]) -> list[LrcLine]:
	"""Synced lines from LRC text, sorted by time.

	Lines sharing a timestamp are joined into one entry, as are untimed lines
	following a timed line, so translations and romanisations stay with their
	original line. ID tags like [ar:...] and blank lines are skipped. Word
	stamps are taken from the first line of an entry and stripped from all.
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
			text, words = split_word_stamps(line[position:].strip(), stamps[0])
			last = []
			for stamp in stamps:
				entry = by_time.get(stamp)
				if entry is None:
					# A repeated line's word stamps move with its line stamp
					shift = stamp - stamps[0]
					shifted = [w._replace(start=w.start + shift, end=None if w.end is None else w.end + shift) for w in words]
					entry = [stamp, [text], shifted if text else []]
					by_time[stamp] = entry
					entries.append(entry)
				elif text:
					entry[1].append(text)
				last.append(entry)
			continue
		if LRC_ID_TAG_RE.match(line):
			last = []
			continue
		text = split_word_stamps(line)[0]
		for entry in last:
			entry[1].append(text)

	entries.sort(key=lambda entry: entry[0])
	result: list[LrcLine] = []
	for i, (stamp, texts, words) in enumerate(entries):
		next_time = entries[i + 1][0] if i + 1 < len(entries) else None
		# The first text leads the joined text, so word offsets still hold
		text = "\n".join(part for part in texts if part)
		result.append(LrcLine(stamp, text, _close_last_word(words, next_time) if texts[0] else []))
	return result


def parse_lrc(lines: Iterable[str]) -> list[tuple[float, str]]:
	"""(seconds, text) entries from LRC lines, sorted by time. See parse_lrc_lines."""
	return [(line.time, line.text) for line in parse_lrc_lines(lines)]


# Scripts written without spaces between words; each character is timed alone
UNSPACED_CHAR = "぀-ヿ㐀-䶿一-鿿豈-﫿"
ESTIMATE_TOKEN_RE = re.compile(rf"[{UNSPACED_CHAR}]|[^\s{UNSPACED_CHAR}]+")
# Seconds per character when spreading a line over its words
ESTIMATE_CHAR_TIME = 0.09


def estimate_words(text: str, start: float, next_time: float | None) -> list[LyricWord]:
	"""Guess word timing for a line that only has a line stamp.

	Words share the line's time by length. The line is assumed to take up most
	of the gap to the next line, but no longer than a typical singing pace.
	Only the first text line is timed, so translations below stay unswept.
	"""
	first_line = text.split("\n", 1)[0]
	tokens = list(ESTIMATE_TOKEN_RE.finditer(first_line))
	if not tokens:
		return []
	weights = [len(token.group()) + 1 for token in tokens]
	total = sum(weights)
	gap = next_time - start if next_time is not None and next_time > start else 4.0
	span = min(gap * 0.85, max(1.0, total * ESTIMATE_CHAR_TIME))
	words: list[LyricWord] = []
	time = start
	for token, weight in zip(tokens, weights, strict=True):
		end = time + span * weight / total
		words.append(LyricWord(time, end, token.start(), token.end()))
		time = end
	return words

