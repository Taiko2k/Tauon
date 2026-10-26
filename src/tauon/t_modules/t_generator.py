# Copyright © 2026, Tauon contributors

"""Generator code table for smart playlists.

Each code a generator understands is described once here, so the editor can show
it as a step, explain it in words, and rebuild it after an edit. Running the
codes stays in Tauon.regenerate_playlist.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable

SOURCE = "source"
ADD = "add"
FILTER = "filter"
SORT = "sort"
LIMIT = "limit"
# Shown as a checkbox in the editor rather than as a step
OPTION = "option"

Values = dict[str, str]
Segment = tuple[str, bool]


def tokenize(code: str) -> tuple[list[str], bool]:
	"""Split code on spaces outside quotes, as parse_generator does. Also returns whether a quote is left open."""
	tokens: list[str] = []
	current = ""
	in_quote = False
	for char in code:
		if not in_quote and char == " ":
			if current:
				tokens.append(current)
			current = ""
			continue
		if char == "\"":
			in_quote ^= True
		current += char
	if current:
		tokens.append(current)
	return tokens, in_quote


def join(tokens: list[str]) -> str:
	return " ".join(tokens)


def clean_text(text: str) -> str:
	"""Make text safe to place inside a quoted code."""
	return text.replace("\"", "")


@dataclass(frozen=True)
class Kind:
	id: str
	category: str
	pattern: re.Pattern[str]
	key: Callable[[Values], str]
	value: Callable[[Values], str]
	say: Callable[[Values], list[Segment]]
	build: Callable[[Values], str]
	# "", "text", "artist", "genre", "playlist", "column", "number", "date" or "direction"
	edit: str = ""
	ops: tuple[str, ...] = ()
	unit: Callable[[], str] | None = None
	directions: tuple[Callable[[], str], Callable[[], str]] | None = None


@dataclass
class Step:
	token: str
	kind: Kind | None
	values: Values = field(default_factory=dict)

	@property
	def known(self) -> bool:
		return self.kind is not None

	@property
	def category(self) -> str:
		return self.kind.category if self.kind else ""

	@property
	def key(self) -> str:
		return self.kind.key(self.values) if self.kind else _("Unknown")

	@property
	def value(self) -> str:
		return self.kind.value(self.values) if self.kind else self.token

	@property
	def incomplete(self) -> bool:
		"""A step whose value still needs filling in."""
		if not self.kind or not self.kind.edit or self.kind.edit == "direction":
			return False
		return not (self.values.get("v") or self.values.get("n"))

	def say(self) -> list[Segment]:
		if self.kind is None:
			return [(_("unknown code"), False), (f"“{self.token}”", True)]
		return self.kind.say(self.values)

	def rebuilt(self, **changes: str) -> str:
		"""The token for this step with some values replaced."""
		if self.kind is None:
			return changes.get("token", self.token)
		return self.kind.build({**self.values, **changes})


def parse_step(token: str) -> Step:
	for kind in KINDS:
		match = kind.pattern.fullmatch(token)
		if match:
			return Step(token, kind, {k: v for k, v in match.groupdict().items() if v is not None})
	return Step(token, None)


def parse(code: str) -> list[Step]:
	"""Every token in the code, options included."""
	tokens, _open = tokenize(code)
	return [parse_step(token) for token in tokens]


def is_option(step: Step) -> bool:
	return step.category == OPTION


# Helpers for building the table ---------------------------------------------------

def _p(pattern: str) -> re.Pattern[str]:
	return re.compile(pattern)


def _alternatives(codes: tuple[str, ...]) -> re.Pattern[str]:
	"""Match any of the codes, keeping which one in the "code" group so aliases rebuild as written."""
	return _p("(?P<code>" + "|".join(re.escape(c) for c in codes) + ")")


def _fixed(text: Callable[[], str]) -> Callable[[Values], str]:
	return lambda _v: text()


def _v(values: Values) -> str:
	return values.get("v", "")


def _quoted(prefix: str) -> Callable[[Values], str]:
	return lambda v: f"{v.get('prefix', prefix)}\"{clean_text(v.get('v', ''))}\""


def _op_word(op: str, *, year: bool = False) -> str:
	if year and op == ">":
		return _("after")
	if year and op == "<":
		return _("before")
	return {
		">": _("more than"),
		"<": _("less than"),
		"=": _("exactly"),
		">=": _("at least"),
		"<=": _("at most"),
	}.get(op, op)


def _op_value(fmt: Callable[[str], str]) -> Callable[[Values], str]:
	def value(v: Values) -> str:
		op = v.get("op", "")
		return f"{op} {fmt(v.get('n', ''))}" if op != "=" else fmt(v.get("n", ""))
	return value


def _number_kind(  # noqa: PLR0917
	kind_id: str, prefix: str, key: Callable[[], str], ops: tuple[str, ...], fmt: Callable[[str], str],
	number: str = r"\d+(?:\.\d+)?", unit: Callable[[], str] | None = None, year: bool = False,
) -> Kind:
	op_pattern = "|".join(re.escape(op) for op in sorted(ops, key=len, reverse=True))
	return Kind(
		id=kind_id, category=FILTER,
		pattern=_p(rf"{re.escape(prefix)}(?P<op>{op_pattern})(?P<n>{number})"),
		key=lambda _v: key(),
		value=_op_value(fmt),
		say=lambda v: [
			(key().lower(), False),
			(f"{_op_word(v.get('op', ''), year=year)} {fmt(v.get('n', ''))}", True),
		],
		build=lambda v: f"{prefix}{v.get('op', ops[0])}{v.get('n', '')}",
		edit="number", ops=ops, unit=unit,
	)


def _flag_kind(kind_id: str, codes: tuple[str, ...], label: Callable[[], str], words: Callable[[], str]) -> Kind:
	return Kind(
		id=kind_id, category=FILTER,
		pattern=_alternatives(codes),
		key=lambda _v: _("Only"),
		value=_fixed(label),
		say=lambda _v: [(_("only"), False), (words(), True)],
		build=lambda v: v.get("code", codes[0]),
	)


def _sort_kind(
	kind_id: str, prefix: str, name: Callable[[], str], first: Callable[[], str], last: Callable[[], str],
	*, prefixes: tuple[str, ...] = (),
) -> Kind:
	"""A sort whose direction is > (first label) or < (last label)."""
	all_prefixes = (prefix, *prefixes)
	prefix_pattern = "|".join(re.escape(p) for p in all_prefixes)

	def first_or_last(v: Values) -> str:
		return first() if v.get("dir") == ">" else last()

	return Kind(
		id=kind_id, category=SORT,
		pattern=_p(rf"(?P<prefix>{prefix_pattern})(?P<dir>[<>])"),
		key=lambda _v: _("Sort"),
		value=lambda v: _("{name}, {order} first").format(name=name(), order=first_or_last(v)),
		say=lambda v: [
			(_("sort by"), False),
			(_("{name}, {order} first").format(name=name().lower(), order=first_or_last(v)), True),
		],
		build=lambda v: f"{v.get('prefix', prefix)}{v.get('dir', '>')}",
		edit="direction",
		directions=(lambda: _("{order} first").format(order=first()), lambda: _("{order} first").format(order=last())),
	)


def _alpha_sort_kind(kind_id: str, prefix: str, name: Callable[[], str]) -> Kind:
	"""A sort that runs A-Z with > and Z-A with <."""

	def order(v: Values) -> str:
		return _("A-Z") if v.get("dir") == ">" else _("Z-A")

	return Kind(
		id=kind_id, category=SORT,
		pattern=_p(rf"{re.escape(prefix)}(?P<dir>[<>])"),
		key=lambda _v: _("Sort"),
		value=lambda v: f"{name()}, {order(v)}",
		say=lambda v: [(_("sort by"), False), (f"{name().lower()}, {order(v)}", True)],
		build=lambda v: f"{prefix}{v.get('dir', '>')}",
		edit="direction",
		directions=(lambda: _("A-Z"), lambda: _("Z-A")),
	)


def _fixed_kind(  # noqa: PLR0917
	kind_id: str, category: str, codes: tuple[str, ...], key: Callable[[], str], value: Callable[[], str],
	words: Callable[[], str],
) -> Kind:
	return Kind(
		id=kind_id, category=category,
		pattern=_alternatives(codes),
		key=lambda _v: key(),
		value=_fixed(value),
		say=lambda _v: [(words(), True)],
		build=lambda v: v.get("code", codes[0]),
	)


def _text_kind(  # noqa: PLR0917
	kind_id: str, category: str, prefixes: tuple[str, ...], key: Callable[[Values], str], edit: str,
	before: Callable[[], str], after: Callable[[], str] | None = None,
) -> Kind:
	"""A code like a"name" whose value is quoted text."""
	prefix_pattern = "|".join(re.escape(p) for p in sorted(prefixes, key=len, reverse=True))

	def say(v: Values) -> list[Segment]:
		out: list[Segment] = [(before(), False), (_v(v), True)]
		if after is not None:
			out.append((after(), False))
		return out

	return Kind(
		id=kind_id, category=category,
		pattern=_p(rf"(?P<prefix>{prefix_pattern})\"(?P<v>[^\"]*)\""),
		key=key, value=_v, say=say, build=_quoted(prefixes[0]), edit=edit,
	)


def _limit_kind(kind_id: str, prefix: str, key: Callable[[], str], unit: Callable[[], str], words: Callable[[str], str]) -> Kind:
	return Kind(
		id=kind_id, category=LIMIT,
		pattern=_p(rf"{re.escape(prefix)}(?P<n>\d+)"),
		key=lambda _v: key(),
		value=lambda v: f"{v.get('n', '')} {unit()}",
		say=lambda v: [(words(v.get("n", "")), True)],
		build=lambda v: f"{prefix}{v.get('n', '')}",
		edit="number", unit=unit,
	)


def _stars(n: str) -> str:
	return f"{n}★"


def _minutes(n: str) -> str:
	return _("{N} min").format(N=n)


# The table. Order matters where patterns overlap: the first full match wins. ----------

KINDS: list[Kind] = [
	# Where tracks come from
	_text_kind("playlist", SOURCE, ("s",), lambda _v: _("Playlist"), "playlist", lambda: _("from playlist")),
	_fixed_kind("self", SOURCE, ("self",), lambda: "", lambda: _("This playlist"), lambda: _("from this playlist")),
	_fixed_kind("clear", SOURCE, ("clr",), lambda: _("Sources"), lambda: _("Clear"), lambda: _("clear the sources")),

	# Adding tracks
	_fixed_kind("all", ADD, ("a",), lambda: "", lambda: _("All tracks"), lambda: _("take all tracks")),
	_text_kind("artist", ADD, ("a",), lambda _v: _("Artist"), "artist", lambda: _("take tracks by")),
	_text_kind(
		"genre", ADD, ("g", "g=", "gm"),
		lambda v: {"g=": _("Genre (exact)"), "gm": _("Genre (multi)")}.get(v.get("prefix", ""), _("Genre")),
		"genre", lambda: _("take tracks in genre")),
	_text_kind("search", ADD, ("f", "find", "fs"), lambda _v: _("Search"), "text", lambda: _("take tracks matching")),
	_text_kind("folder", ADD, ("p",), lambda _v: _("Folder"), "text", lambda: _("take the folder matching")),
	_text_kind(
		"label", ADD, ("lb", "lb="), lambda v: _("Label (exact)") if v.get("prefix") == "lb=" else _("Label"),
		"text", lambda: _("take tracks on label")),
	_text_kind("ext", ADD, ("ext",), lambda _v: _("File type"), "text", lambda: _("take files of type")),

	# Service sources
	_fixed_kind("plex", ADD, ("plex",), lambda: "", lambda: "Plex", lambda: _("take the Plex library")),
	_fixed_kind("jelly", ADD, ("jelly",), lambda: "", lambda: "Jellyfin", lambda: _("take the Jellyfin library")),
	_text_kind("jelly_pl", ADD, ("jelly",), lambda _v: _("Jellyfin playlist"), "text", lambda: _("take Jellyfin playlist")),
	_fixed_kind("tau", ADD, ("tau",), lambda: "", lambda: "Tauon Satellite", lambda: _("take the Satellite playlist")),
	_fixed_kind("air", ADD, ("air",), lambda: "", lambda: "Airsonic", lambda: _("take the Airsonic library")),
	_text_kind("air_pl", ADD, ("air",), lambda _v: _("Airsonic playlist"), "text", lambda: _("take Airsonic playlist")),
	_text_kind("tidal_pl", ADD, ("tpl",), lambda _v: _("Tidal playlist"), "text", lambda: _("take Tidal playlist")),
	_fixed_kind("tidal_albums", ADD, ("tfa",), lambda: "", lambda: _("Tidal albums"), lambda: _("take Tidal favourite albums")),
	_fixed_kind("tidal_tracks", ADD, ("tft",), lambda: "", lambda: _("Tidal tracks"), lambda: _("take Tidal favourite tracks")),
	_text_kind("tidal_artist", ADD, ("tar",), lambda _v: _("Tidal artist"), "text", lambda: _("take Tidal artist")),
	_text_kind("tidal_mix", ADD, ("tmix",), lambda _v: _("Tidal mix"), "text", lambda: _("take Tidal mix")),

	# Filters
	_text_kind("not_in", FILTER, ("px",), lambda _v: _("Not in"), "playlist", lambda: _("minus anything in")),
	_text_kind("keep", FILTER, ("ff",), lambda _v: _("Keep matching"), "text", lambda: _("keep only matches for")),
	_text_kind("exclude", FILTER, ("fx",), lambda _v: _("Exclude matching"), "text", lambda: _("drop matches for")),
	_text_kind("comment", FILTER, ("com",), lambda _v: _("Comment has"), "text", lambda: _("keep comments containing")),
	_number_kind("year", "y", lambda: _("Year"), (">", "<", "=", ">=", "<="), str, number=r"\d+", year=True),
	Kind(
		id="year_match", category=FILTER, pattern=_p(r"y=(?P<v>\S+)"),
		key=lambda _v: _("Year"), value=_v,
		say=lambda v: [(_("date contains"), False), (_v(v), True)],
		build=lambda v: f"y={_v(v)}", edit="text",
	),
	_number_kind("rating", "rat", lambda: _("Rating"), (">", "<", "="), _stars),
	_number_kind("album_rating", "rata", lambda: _("Album rating"), (">", "<", "="), _stars),
	_number_kind("play_count", "pc", lambda: _("Play count"), (">", "<"), str, number=r"\d+"),
	_number_kind(
		"play_time", "pt", lambda: _("Play time"), (">", "<"), lambda n: _("{N} s").format(N=n),
		number=r"\d+", unit=lambda: _("seconds")),
	_number_kind("length", "d", lambda: _("Length"), (">", "<"), _minutes, unit=lambda: _("minutes")),
	_number_kind("album_length", "ad", lambda: _("Album length"), (">", "<"), _minutes, unit=lambda: _("minutes")),
	Kind(
		id="modified_days", category=FILTER, pattern=_p(r"m(?P<op>[<>])(?P<n>\d+)d"),
		key=lambda _v: _("Modified"),
		value=lambda v: (_("last {N} days") if v.get("op") == ">" else _("over {N} days ago")).format(N=v.get("n", "")),
		say=lambda v: [
			(_("modified"), False),
			((_("in the last {N} days") if v.get("op") == ">" else _("over {N} days ago")).format(N=v.get("n", "")), True),
		],
		build=lambda v: f"m{v.get('op', '>')}{v.get('n', '')}d",
		edit="number", ops=(">", "<"), unit=lambda: _("days"),
	),
	Kind(
		id="modified_date", category=FILTER, pattern=_p(r"m(?P<op>[<>])(?P<n>\d{4}-\d{2}-\d{2})"),
		key=lambda _v: _("Modified"),
		value=lambda v: (_("since {D}") if v.get("op") == ">" else _("before {D}")).format(D=v.get("n", "")),
		say=lambda v: [
			(_("modified"), False),
			((_("since {D}") if v.get("op") == ">" else _("before {D}")).format(D=v.get("n", "")), True),
		],
		build=lambda v: f"m{v.get('op', '>')}{v.get('n', '')}",
		edit="date", ops=(">", "<"), unit=lambda: _("YYYY-MM-DD"),
	),
	_number_kind("skips", "sk", lambda: _("Skips"), (">", "<"), str, number=r"\d+"),
	_flag_kind("loved", ("l", "love", "loved"), lambda: _("Loved"), lambda: _("loved tracks")),
	_flag_kind("lyrics", ("ly", "lyrics"), lambda: _("Has lyrics"), lambda: _("tracks with lyrics")),
	_flag_kind("today", ("today",), lambda: _("On this day"), lambda: _("tracks released on this day")),
	_flag_kind("rated", ("rat",), lambda: _("Rated"), lambda: _("rated tracks")),
	_flag_kind("unrated", ("norat",), lambda: _("Unrated"), lambda: _("unrated tracks")),
	_flag_kind("cue", ("cue",), lambda: _("CUE tracks"), lambda: _("CUE sheet tracks")),
	_flag_kind("hires", ("hr",), lambda: _("Hi-res"), lambda: _("hi-res files")),

	# Sorting
	_sort_kind("sort_year", "y", lambda: _("Year"), lambda: _("newest"), lambda: _("oldest")),
	_sort_kind("sort_rating", "rat", lambda: _("Rating"), lambda: _("highest"), lambda: _("lowest")),
	_fixed_kind(
		"sort_album_rating", SORT, ("rata>",), lambda: _("Sort"), lambda: _("Album rating, highest first"),
		lambda: _("sort by album rating, highest first")),
	_sort_kind("sort_play_time", "pt", lambda: _("Play time"), lambda: _("most"), lambda: _("least"), prefixes=("pc",)),
	_sort_kind("sort_album_play_time", "pa", lambda: _("Album play time"), lambda: _("most"), lambda: _("least")),
	_sort_kind("sort_length", "d", lambda: _("Length"), lambda: _("longest"), lambda: _("shortest")),
	_sort_kind("sort_album_length", "ad", lambda: _("Album length"), lambda: _("longest"), lambda: _("shortest")),
	_sort_kind("sort_modified", "m", lambda: _("Modified"), lambda: _("newest"), lambda: _("oldest")),
	_sort_kind("sort_imported", "ia", lambda: _("Imported"), lambda: _("newest"), lambda: _("oldest")),
	_alpha_sort_kind("sort_artist", "ar", lambda: _("Artist | Album")),
	_alpha_sort_kind("sort_album_artist", "aa", lambda: _("Album artist | Album")),
	Kind(
		id="sort_column", category=SORT, pattern=_p(r"\"(?P<v>[^\"]+)\"(?P<dir>[<>])"),
		key=lambda _v: _("Sort"),
		value=lambda v: f"{_v(v)} {'↑' if v.get('dir') == '>' else '↓'}",
		say=lambda v: [(_("sort by column"), False), (_v(v), True)],
		build=lambda v: f"\"{clean_text(_v(v))}\"{v.get('dir', '>')}",
		edit="column", directions=(lambda: _("Ascending"), lambda: _("Descending")),
	),
	_fixed_kind("shuffle", SORT, ("st", "rt", "r"), lambda: _("Shuffle"), lambda: _("Tracks"), lambda: _("shuffle tracks")),
	_fixed_kind("shuffle_albums", SORT, ("ra", "sa", "sf", "rf"), lambda: _("Shuffle"), lambda: _("Albums"), lambda: _("shuffle albums")),
	_fixed_kind("reverse", SORT, ("rv", "reverse"), lambda: _("Reverse"), lambda: _("Tracks"), lambda: _("reverse the order")),
	_fixed_kind("reverse_albums", SORT, ("rva",), lambda: _("Reverse"), lambda: _("Albums"), lambda: _("reverse album order")),
	_fixed_kind("path", SORT, ("path",), lambda: _("Sort"), lambda: _("File path"), lambda: _("sort by file path")),
	_fixed_kind("track_number", SORT, ("tn",), lambda: _("Sort"), lambda: _("Track number"), lambda: _("sort by track number")),
	_fixed_kind("year_per_artist", SORT, ("ypa",), lambda: _("Sort"), lambda: _("Year per artist"), lambda: _("sort by year per artist")),

	# Limits
	_limit_kind("limit", "n", lambda: _("Limit"), lambda: _("tracks"), lambda n: _("keep the first {N} tracks").format(N=n)),
	_limit_kind("time_limit", "t", lambda: _("Limit"), lambda: _("minutes"), lambda n: _("stop at {N} minutes").format(N=n)),
	_limit_kind(
		"per_artist", "per-artist", lambda: _("Max per artist"), lambda: _("tracks"),
		lambda n: _("at most {N} per artist").format(N=n)),

	# Options
	Kind(
		id="auto", category=OPTION, pattern=_p("auto"),
		key=lambda _v: _("Option"), value=lambda _v: _("Auto update"),
		say=lambda _v: [], build=lambda _v: "auto",
	),
]


# The stages a generator runs in: where tracks come from, what is taken, then what is done to them
FROM = "from"
TAKE = "take"
THEN = "then"
LANE_ORDER = (FROM, TAKE, THEN)


def lane_of(step: Step) -> str:
	if step.category == SOURCE:
		return FROM
	if step.category == ADD:
		return TAKE
	return THEN


def split_lanes(steps: list[Step]) -> dict[str, list[int]] | None:
	"""Indices of the steps in each lane, or None when the steps don't run in lane order."""
	lanes: dict[str, list[int]] = {lane: [] for lane in LANE_ORDER}
	stage = 0
	for i, step in enumerate(steps):
		if is_option(step):
			continue
		lane = lane_of(step)
		order = LANE_ORDER.index(lane)
		if order < stage:
			return None
		stage = order
		lanes[lane].append(i)
	return lanes


def arrange(lanes: dict[str, list[str]], options: list[str]) -> list[str]:
	"""Tokens in lane order. All tracks is taken when nothing else is but other steps exist."""
	take = lanes[TAKE]
	if not take and (lanes[FROM] or lanes[THEN]):
		take = ["a"]
	return [*lanes[FROM], *take, *lanes[THEN], *options]


def describe(steps: list[Step]) -> list[Segment]:
	"""The steps as one readable sentence, split into plain and emphasised parts."""
	out: list[Segment] = []
	have_source = False
	for step in steps:
		if is_option(step):
			continue
		if step.category == SOURCE:
			have_source = True
		parts = step.say()
		if step.category == ADD and not have_source and step.kind and step.kind.id in (
				"all", "artist", "genre", "search", "folder", "label", "ext"):
			parts = [(_("from"), False), (_("all playlists"), True), ("→", False), *parts]
		if step.kind and step.kind.id == "all":
			have_source = False
		if out:
			out.append(("→", False))
		out.extend(parts)
	return out


def problem(steps: list[Step]) -> str:
	"""A short message about the first thing wrong with the steps, or an empty string."""
	for step in steps:
		if not step.known:
			return _("Unknown code: {C}").format(C=step.token)
	for step in steps:
		if step.incomplete:
			return _("Enter a value for {K}").format(K=step.key)
	categories = [step.category for step in steps]
	if ADD not in categories:
		if categories:
			return _("Nothing is taken yet. Choose all tracks, an artist, a genre or a search.")
		return ""
	first_take = categories.index(ADD)
	if any(category in (FILTER, SORT, LIMIT) for category in categories[:first_take]):
		return _("A step runs before any tracks are taken, so it does nothing.")
	return ""


def rename_playlist_references(code: str, old: str, new: str) -> str:
	"""Point s"old" and px"old" codes at a renamed playlist."""
	if not old or old == new:
		return code
	tokens, open_quote = tokenize(code)
	if open_quote:
		return code
	changed = False
	for i, token in enumerate(tokens):
		step = parse_step(token)
		if step.kind and step.kind.id in ("playlist", "not_in") and step.values.get("v", "").lower() == old.lower():
			tokens[i] = step.rebuilt(v=new)
			changed = True
	return join(tokens) if changed else code


@dataclass(frozen=True)
class AddItem:
	label: Callable[[], str]
	token: str
	# Open the step editor right after adding
	edit: bool = False


@dataclass(frozen=True)
class AddGroup:
	label: Callable[[], str]
	items: tuple[AddItem | None, ...]


# Menu entries for each lane's add button. None is a separator.
FROM_MENU: tuple[AddItem | AddGroup | None, ...] = (
	AddItem(lambda: _("Playlist…"), 's""', edit=True),
	AddItem(lambda: _("This playlist"), "self"),
)

TAKE_MENU: tuple[AddItem | AddGroup | None, ...] = (
	AddItem(lambda: _("All tracks"), "a"),
	AddItem(lambda: _("Artist…"), 'a""', edit=True),
	AddItem(lambda: _("Genre…"), 'g""', edit=True),
	AddItem(lambda: _("Search…"), 'f""', edit=True),
	AddItem(lambda: _("Folder…"), 'p""', edit=True),
	AddItem(lambda: _("Label…"), 'lb""', edit=True),
	AddItem(lambda: _("File type…"), 'ext""', edit=True),
	None,
	AddGroup(lambda: _("Exact match"), (
		AddItem(lambda: _("Genre (exact)…"), 'g=""', edit=True),
		AddItem(lambda: _("Genre (multi-value)…"), 'gm""', edit=True),
		AddItem(lambda: _("Label (exact)…"), 'lb=""', edit=True),
		AddItem(lambda: _("Search (exact text)…"), 'fs""', edit=True),
	)),
	AddGroup(lambda: _("Services"), (
		AddItem(lambda: _("Plex library"), "plex"),
		AddItem(lambda: _("Jellyfin library"), "jelly"),
		AddItem(lambda: _("Jellyfin playlist…"), 'jelly""', edit=True),
		AddItem(lambda: _("Airsonic library"), "air"),
		AddItem(lambda: _("Airsonic playlist…"), 'air""', edit=True),
		AddItem(lambda: _("Tauon Satellite playlist"), "tau"),
		AddItem(lambda: _("Tidal playlist…"), 'tpl""', edit=True),
		AddItem(lambda: _("Tidal favourite albums"), "tfa"),
		AddItem(lambda: _("Tidal favourite tracks"), "tft"),
		AddItem(lambda: _("Tidal artist…"), 'tar""', edit=True),
		AddItem(lambda: _("Tidal mix…"), 'tmix""', edit=True),
	)),
)

THEN_MENU: tuple[AddItem | AddGroup | None, ...] = (
	AddGroup(lambda: _("Filter"), (
		AddItem(lambda: _("Year…"), "y>2000", edit=True),
		AddItem(lambda: _("Rating…"), "rat>3", edit=True),
		AddItem(lambda: _("Album rating…"), "rata>3", edit=True),
		AddItem(lambda: _("Play count…"), "pc>5", edit=True),
		AddItem(lambda: _("Length…"), "d>3", edit=True),
		AddItem(lambda: _("Album length…"), "ad>40", edit=True),
		AddItem(lambda: _("Play time…"), "pt>600", edit=True),
		AddItem(lambda: _("Recently modified…"), "m>30d", edit=True),
		AddItem(lambda: _("Modified since date…"), "m>2024-01-01", edit=True),
		AddItem(lambda: _("Skips…"), "sk<1", edit=True),
		None,
		AddItem(lambda: _("Loved"), "l"),
		AddItem(lambda: _("Has lyrics"), "ly"),
		AddItem(lambda: _("On this day"), "today"),
		AddItem(lambda: _("Rated"), "rat"),
		AddItem(lambda: _("Unrated"), "norat"),
		AddItem(lambda: _("Hi-res"), "hr"),
		AddItem(lambda: _("CUE tracks"), "cue"),
		None,
		AddItem(lambda: _("Keep matching…"), 'ff""', edit=True),
		AddItem(lambda: _("Exclude matching…"), 'fx""', edit=True),
		AddItem(lambda: _("Comment contains…"), 'com""', edit=True),
		AddItem(lambda: _("Not in playlist…"), 'px""', edit=True),
	)),
	AddGroup(lambda: _("Sort"), (
		AddItem(lambda: _("Shuffle tracks"), "st"),
		AddItem(lambda: _("Shuffle albums"), "ra"),
		None,
		AddItem(lambda: _("Year"), "y>", edit=True),
		AddItem(lambda: _("Rating"), "rat>", edit=True),
		AddItem(lambda: _("Album rating"), "rata>"),
		AddItem(lambda: _("Play time"), "pt>", edit=True),
		AddItem(lambda: _("Album play time"), "pa>", edit=True),
		AddItem(lambda: _("Length"), "d>", edit=True),
		AddItem(lambda: _("Album length"), "ad>", edit=True),
		AddItem(lambda: _("Modified"), "m>", edit=True),
		AddItem(lambda: _("Imported"), "ia>", edit=True),
		None,
		AddItem(lambda: _("Artist | Album"), "ar>", edit=True),
		AddItem(lambda: _("Album artist | Album"), "aa>", edit=True),
		AddItem(lambda: _("Track number"), "tn"),
		AddItem(lambda: _("File path"), "path"),
		AddItem(lambda: _("Year per artist"), "ypa"),
		AddItem(lambda: _("Column…"), '"Artist">', edit=True),
		AddItem(lambda: _("Reverse tracks"), "rv"),
		AddItem(lambda: _("Reverse albums"), "rva"),
	)),
	AddGroup(lambda: _("Limit"), (
		AddItem(lambda: _("Number of tracks…"), "n50", edit=True),
		AddItem(lambda: _("Total time…"), "t60", edit=True),
		AddItem(lambda: _("Max per artist…"), "per-artist2", edit=True),
	)),
)

# Everything, for codes shown as a single list
ADD_MENU: tuple[AddItem | AddGroup | None, ...] = (*FROM_MENU, None, *TAKE_MENU, None, *THEN_MENU)


@dataclass(frozen=True)
class Preset:
	name: Callable[[], str]
	code: str


# None is a separator
PRESETS: tuple[Preset | None, ...] = (
	Preset(lambda: _("Unplayed"), "a pc<1 ra"),
	Preset(lambda: _("On this day"), "a today y<"),
	Preset(lambda: _("Recently added"), "a m>30d m>"),
	None,
	Preset(lambda: _("Loved"), "a l"),
	Preset(lambda: _("Top rated albums"), "a rata>4 rata>"),
	Preset(lambda: _("Most played"), "a pt> n100"),
	None,
	Preset(lambda: _("One-hour mix"), "a st per-artist2 t60 auto"),
	Preset(lambda: _("Album roulette"), "a ad>30 ra"),
	Preset(lambda: _("Hi-res only"), "a hr path"),
	None,
	Preset(lambda: _("Auto-sorting"), "self a path tn ypa auto"),
)
