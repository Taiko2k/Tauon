"""Repair library paths after the user moves their music folder.

Given one missing track and the place the user says it now lives (a file, its
album folder, or any folder above that), work out a folder rewrite rule and
apply it to every missing track it explains. Tracks the rule can't place are
matched by filename and size within the folders the rule landed in.

Everything here only reads the filesystem, so it is safe to run off the main
thread. Applying the result to the library is left to the caller.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
	from collections.abc import Callable

SCAN_LIMIT = 500_000


def default_fold() -> Callable[[str], str]:
	"""Name comparison for this platform's usual filesystems."""
	if sys.platform in ("darwin", "win32"):
		return str.casefold
	return lambda s: s


def normalise(path: str) -> str:
	path = os.path.expanduser(path.strip()).replace("\\", "/")
	while len(path) > 1 and path.endswith("/") and not path.endswith(":/"):
		path = path[:-1]
	return path


def split_dir(path: str) -> tuple[str, str]:
	folder, _sep, name = path.rpartition("/")
	return folder, name


def join(folder: str, rest: str) -> str:
	return folder.rstrip("/") + "/" + rest.lstrip("/")


def remainder(path: str, root: str, fold: Callable[[str], str]) -> str | None:
	"""Return the part of `path` below `root` ("" for root itself), or None if outside."""
	root_parts = root.split("/") if root else [""]
	parts = path.split("/")
	if len(parts) < len(root_parts):
		return None
	for a, b in zip(parts, root_parts, strict=False):
		if fold(a) != fold(b):
			return None
	return "/".join(parts[len(root_parts):])


class LibTrack(NamedTuple):
	id: int
	path: str
	size: int
	cue_key: float | None  # Start time for cue sheet tracks, which share one file


@dataclass
class Mapping:
	base_old: str  # Folder pair the user's drop directly implies
	base_new: str
	old_root: str  # Same pair widened over the parent folders they share
	new_root: str


@dataclass
class RelocatePlan:
	mapping: Mapping | None = None
	moves: dict[int, tuple[str, str]] = field(default_factory=dict)  # id -> (old path, new path)
	duplicates: dict[int, int] = field(default_factory=dict)  # duplicate id -> original id
	unresolved: int = 0
	scan_truncated: bool = False
	error: str = ""


def widen(base_old: str, base_new: str, fold: Callable[[str], str]) -> tuple[str, str]:
	"""Strip trailing folder names the two paths share.

	A renamed library root with the same Artist/Album layout below it widens to the roots.
	"""
	o = base_old.split("/")
	n = base_new.split("/")
	while len(o) > 1 and len(n) > 1 and o[-1] and fold(o[-1]) == fold(n[-1]):
		o.pop()
		n.pop()
	return "/".join(o), "/".join(n)


def infer_mapping(old_path: str, target: str, fold: Callable[[str], str]) -> Mapping | None:
	"""Find where `old_path` sits under `target` by re-attaching its trailing path parts."""
	old_parts = old_path.split("/")
	if os.path.isfile(target):
		folder, name = split_dir(target)
		if fold(name) != fold(old_parts[-1]):
			return None
		base_old, base_new = "/".join(old_parts[:-1]), folder
	elif os.path.isdir(target):
		for k in range(1, len(old_parts)):
			if os.path.isfile(join(target, "/".join(old_parts[-k:]))):
				base_old, base_new = "/".join(old_parts[:-k]), target
				break
		else:
			return None
	else:
		return None
	old_root, new_root = widen(base_old, base_new, fold)
	return Mapping(base_old, base_new, old_root, new_root)


class _Listings:
	"""Cached folder listings as folded name -> real name, None if unreadable."""

	def __init__(self, fold: Callable[[str], str]) -> None:
		self.fold = fold
		self.cache: dict[str, dict[str, str] | None] = {}

	def get(self, folder: str) -> dict[str, str] | None:
		if folder in self.cache:
			return self.cache[folder]
		try:
			names = {self.fold(n): n for n in os.listdir(folder or "/")}
		except OSError:
			names = None
		self.cache[folder] = names
		return names


class _Candidates:
	"""Files found by the scan, bucketed per name by size and by parent folder name."""

	def __init__(self, found: dict[str, list[str]], fold: Callable[[str], str]) -> None:
		self.found = found
		self.fold = fold
		self.buckets: dict[str, tuple[dict[int, list[str]], dict[str, list[str]]]] = {}

	def get(self, name: str) -> tuple[dict[int, list[str]], dict[str, list[str]]]:
		bucket = self.buckets.get(name)
		if bucket is None:
			sizes: dict[int, list[str]] = {}
			parents: dict[str, list[str]] = {}
			for c in self.found.get(name, []):
				try:
					sizes.setdefault(os.path.getsize(c), []).append(c)
				except OSError:
					continue
				parents.setdefault(self.fold(split_dir(split_dir(c)[0])[1]), []).append(c)
			bucket = self.buckets[name] = (sizes, parents)
		return bucket


def _pick(candidates: _Candidates, track: LibTrack, claimed: set[str], fold: Callable[[str], str]) -> str | None:
	sizes, parents = candidates.get(fold(split_dir(track.path)[1]))
	old_parent = fold(split_dir(split_dir(track.path)[0])[1])
	if track.size > 0:
		sized = [p for p in sizes.get(track.size, []) if p not in claimed]
		if len(sized) == 1:
			return sized[0]
		if len(sized) > 1:
			narrowed = [p for p in sized if fold(split_dir(split_dir(p)[0])[1]) == old_parent]
			return narrowed[0] if len(narrowed) == 1 else None
	narrowed = [p for p in parents.get(old_parent, []) if p not in claimed]
	return narrowed[0] if len(narrowed) == 1 else None


def build_plan(
	tracks: list[LibTrack],
	anchor_path: str,
	target: str,
	*,
	fold: Callable[[str], str] | None = None,
	cancelled: Callable[[], bool] = lambda: False,
	progress: Callable[[int], None] | None = None,
	scan_limit: int = SCAN_LIMIT,
) -> RelocatePlan | None:
	"""Work out which missing tracks can be relocated to `target`. Returns None if cancelled."""
	fold = fold or default_fold()
	plan = RelocatePlan()
	target = normalise(target)
	if not target or os.path.dirname(target) == target:
		return plan  # Nothing typed yet, or just a filesystem root, which would mean scanning the whole disk
	if not os.path.exists(target):
		plan.error = "not_found"
		return plan

	mapping = infer_mapping(anchor_path, target, fold)
	plan.mapping = mapping
	listings = _Listings(fold)

	by_folder: dict[str, list[LibTrack]] = {}
	for t in tracks:
		if t.path:
			by_folder.setdefault(split_dir(t.path)[0], []).append(t)

	leftovers: list[LibTrack] = []
	for folder, items in by_folder.items():
		if cancelled():
			return None
		rest = remainder(folder, mapping.old_root, fold) if mapping else ""
		if rest is None:
			continue
		old_names = listings.get(folder)
		missing = [t for t in items if old_names is None or fold(split_dir(t.path)[1]) not in old_names]
		if not missing:
			continue
		new_names = listings.get(join(mapping.new_root, rest) if rest else mapping.new_root) if mapping else None
		for t in missing:
			name = fold(split_dir(t.path)[1])
			if new_names is not None and name in new_names:
				new_folder = join(mapping.new_root, rest) if rest else mapping.new_root
				plan.moves[t.id] = (t.path, join(new_folder, new_names[name]))
			else:
				leftovers.append(t)

	if leftovers:
		# Search only where the drop and the rule's hits say the library now lives
		scan_dirs = [target if os.path.isdir(target) else split_dir(target)[0]]
		scan_dirs += {split_dir(new)[0] for _old, new in plan.moves.values()}
		try:
			scan_root = os.path.commonpath(scan_dirs).replace("\\", "/")
		except ValueError:
			scan_root = scan_dirs[0]

		wanted = {fold(split_dir(t.path)[1]) for t in leftovers}
		found: dict[str, list[str]] = {}
		claimed = {new for _old, new in plan.moves.values()}
		count = 0
		for root, _dirs, files in os.walk(scan_root):
			if cancelled():
				return None
			root = root.replace("\\", "/")
			for f in files:
				key = fold(f)
				if key in wanted:
					found.setdefault(key, []).append(join(root, f))
			count += len(files)
			if progress and count // 2000 != (count - len(files)) // 2000:
				progress(count)
			if count > scan_limit:
				plan.scan_truncated = True
				break

		candidates = _Candidates(found, fold)
		chosen: dict[str, str] = {}  # old path -> new path, shared by cue tracks of one file
		for t in leftovers:
			if cancelled():
				return None
			new = chosen.get(t.path)
			if new is None:
				new = _pick(candidates, t, claimed, fold)
				if new is not None:
					chosen[t.path] = new
					claimed.add(new)
			if new is None:
				plan.unresolved += 1
			else:
				plan.moves[t.id] = (t.path, new)

	# Tracks the user already re-imported from the new location
	if plan.moves:
		existing = {(fold(t.path), t.cue_key): t.id for t in tracks if t.path}
		for t in tracks:
			move = plan.moves.get(t.id)
			if move is None:
				continue
			other = existing.get((fold(move[1]), t.cue_key))
			if other is not None and other != t.id and other not in plan.moves:
				plan.duplicates[other] = t.id

	return plan
