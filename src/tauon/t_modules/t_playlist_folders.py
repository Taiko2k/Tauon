# Copyright © 2026, Tauon contributors

"""Playlist folders: a user-arranged tree over the flat playlist list.

The tree holds playlist uuids and PlaylistFolder nodes. Its depth-first order of
playlists always matches pctl.multi_playlist, so code that works with playlist
indexes needs no changes: tree edits are applied to multi_playlist by reordering
it, and outside changes to multi_playlist (new, deleted or moved playlists) are
folded back into the tree by sync().
"""

from __future__ import annotations

import bisect
import logging
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable, Iterator

# Deepest folder nesting allowed; a folder at the root is at level 1
MAX_DEPTH = 3

# Folder colours as RGB, picked in turn for new folders
FOLDER_COLOURS: list[tuple[int, int, int]] = [
	(90, 160, 230),
	(230, 120, 90),
	(110, 200, 120),
	(210, 110, 200),
	(230, 190, 70),
	(80, 200, 200),
	(170, 130, 230),
	(220, 90, 130),
]


@dataclass(eq=False)
class PlaylistFolder:
	uuid_int: int
	title: str
	colour: int = 0
	collapsed: bool = False
	pinned: bool = False
	children: list[int | PlaylistFolder] = field(default_factory=list)


@dataclass
class FolderRow:
	"""A visible row of the side panel list."""

	entry: int | PlaylistFolder
	depth: int
	# Folders containing this row, outermost first
	ancestors: tuple[PlaylistFolder, ...]


def _kept_by_lis(current: list[int], order: list[int]) -> set[int]:
	"""Largest set of items whose relative order is the same in both lists."""
	position = {u: i for i, u in enumerate(current)}
	seq = [u for u in order if u in position]
	tails: list[int] = []  # smallest tail position of an increasing run of each length
	tail_items: list[int] = []
	back: dict[int, int | None] = {}
	for u in seq:
		p = position[u]
		k = bisect.bisect_left(tails, p)
		back[u] = tail_items[k - 1] if k > 0 else None
		if k == len(tails):
			tails.append(p)
			tail_items.append(u)
		else:
			tails[k] = p
			tail_items[k] = u
	kept: set[int] = set()
	u = tail_items[-1] if tail_items else None
	while u is not None:
		kept.add(u)
		u = back[u]
	return kept


class PlaylistFolders:

	def __init__(self) -> None:
		self.root: list[int | PlaylistFolder] = []
		self._parent: dict[int, PlaylistFolder | None] = {}  # playlist uuid -> folder
		self._folder_parent: dict[int, PlaylistFolder | None] = {}  # folder uuid -> folder
		self._folders: dict[int, PlaylistFolder] = {}
		self._order: tuple[int, ...] | None = None  # playlist order the tree was last synced to

	# --- Persistence

	def to_saved(self) -> list:
		def dump(entry: int | PlaylistFolder) -> int | dict:
			if isinstance(entry, int):
				return entry
			return {
				"uuid": entry.uuid_int,
				"title": entry.title,
				"colour": entry.colour,
				"collapsed": entry.collapsed,
				"pinned": entry.pinned,
				"children": [dump(c) for c in entry.children],
			}
		return [dump(e) for e in self.root]

	def load(self, data: object) -> None:
		seen_playlists: set[int] = set()
		seen_folders: set[int] = set()

		def parse(items: object) -> list[int | PlaylistFolder]:
			out: list[int | PlaylistFolder] = []
			if not isinstance(items, list):
				return out
			for item in items:
				if isinstance(item, int) and not isinstance(item, bool):
					if item not in seen_playlists:
						seen_playlists.add(item)
						out.append(item)
				elif isinstance(item, dict):
					uuid_int = item.get("uuid")
					if not isinstance(uuid_int, int) or uuid_int in seen_folders:
						continue
					seen_folders.add(uuid_int)
					colour = item.get("colour", 0)
					out.append(PlaylistFolder(
						uuid_int=uuid_int,
						title=str(item.get("title", "")),
						colour=colour if isinstance(colour, int) else 0,
						collapsed=bool(item.get("collapsed", False)),
						pinned=bool(item.get("pinned", False)),
						children=parse(item.get("children", [])),
					))
			return out

		try:
			self.root = parse(data)
		except Exception:
			logging.exception("Failed to load playlist folders")
			self.root = []
		self._trim_depth(self.root, 1)
		self._changed()

	def _trim_depth(self, items: list[int | PlaylistFolder], level: int) -> None:
		"""Flatten folders nested deeper than MAX_DEPTH into their parent."""
		i = 0
		while i < len(items):
			entry = items[i]
			if isinstance(entry, PlaylistFolder):
				if level > MAX_DEPTH:
					items[i:i + 1] = entry.children
					continue
				self._trim_depth(entry.children, level + 1)
			i += 1

	# --- Lookups

	def _changed(self) -> None:
		self._parent.clear()
		self._folder_parent.clear()
		self._folders.clear()

		def index(items: list[int | PlaylistFolder], parent: PlaylistFolder | None) -> None:
			for entry in items:
				if isinstance(entry, int):
					self._parent[entry] = parent
				else:
					self._folder_parent[entry.uuid_int] = parent
					self._folders[entry.uuid_int] = entry
					index(entry.children, entry)

		index(self.root, None)
		self._order = None

	def walk(self, items: list[int | PlaylistFolder] | None = None, depth: int = 0) -> Iterator[tuple[int | PlaylistFolder, int]]:
		"""Every entry depth first, with its depth (0 at the root)."""
		for entry in self.root if items is None else items:
			yield entry, depth
			if isinstance(entry, PlaylistFolder):
				yield from self.walk(entry.children, depth + 1)

	def playlist_order(self) -> list[int]:
		return [e for e, _d in self.walk() if isinstance(e, int)]

	def folders(self) -> list[PlaylistFolder]:
		return [e for e, _d in self.walk() if isinstance(e, PlaylistFolder)]

	def get_folder(self, uuid_int: int) -> PlaylistFolder | None:
		return self._folders.get(uuid_int)

	def has_folders(self) -> bool:
		return bool(self._folders)

	def parent_of(self, entry: int | PlaylistFolder) -> PlaylistFolder | None:
		if isinstance(entry, int):
			return self._parent.get(entry)
		return self._folder_parent.get(entry.uuid_int)

	def ancestors(self, entry: int | PlaylistFolder) -> list[PlaylistFolder]:
		"""Folders containing an entry, outermost first."""
		out: list[PlaylistFolder] = []
		parent = self.parent_of(entry)
		while parent is not None:
			out.append(parent)
			parent = self._folder_parent.get(parent.uuid_int)
		out.reverse()
		return out

	def level(self, folder: PlaylistFolder | None) -> int:
		"""Nesting level of a folder: 0 for the root, 1 for a top level folder."""
		return 0 if folder is None else len(self.ancestors(folder)) + 1

	def height(self, folder: PlaylistFolder) -> int:
		"""Levels of folders in a subtree, counting the folder itself."""
		return 1 + max((self.height(c) for c in folder.children if isinstance(c, PlaylistFolder)), default=0)

	def contains(self, folder: PlaylistFolder, entry: int | PlaylistFolder) -> bool:
		"""True if an entry is anywhere inside a folder."""
		return folder in self.ancestors(entry)

	def subtree_playlists(self, folder: PlaylistFolder) -> list[int]:
		return [e for e, _d in self.walk(folder.children) if isinstance(e, int)]

	def first_playlist_from(self, folder: PlaylistFolder) -> int | None:
		"""First playlist at or after a folder's place in the list."""
		found = False
		for entry, _depth in self.walk():
			if entry is folder:
				found = True
			elif found and isinstance(entry, int):
				return entry
		return None

	def pinned_folder_of(self, pl_uuid: int) -> PlaylistFolder | None:
		"""Outermost pinned folder containing a playlist."""
		for folder in self.ancestors(pl_uuid):
			if folder.pinned:
				return folder
		return None

	def container(self, folder: PlaylistFolder | None) -> list[int | PlaylistFolder]:
		return self.root if folder is None else folder.children

	def _locate(self, entry: int | PlaylistFolder) -> tuple[list[int | PlaylistFolder], int]:
		items = self.container(self.parent_of(entry))
		for i, e in enumerate(items):
			if e is entry or (isinstance(entry, int) and e == entry):
				return items, i
		raise LookupError(entry)

	# --- Views

	def rows(self) -> list[FolderRow]:
		"""Side panel rows, leaving out the contents of collapsed folders."""
		out: list[FolderRow] = []

		def add(items: list[int | PlaylistFolder], ancestors: tuple[PlaylistFolder, ...]) -> None:
			for entry in items:
				out.append(FolderRow(entry, len(ancestors), ancestors))
				if isinstance(entry, PlaylistFolder) and not entry.collapsed:
					add(entry.children, (*ancestors, entry))

		add(self.root, ())
		return out

	def top_items(self, hidden: Callable[[int], bool]) -> list[int | PlaylistFolder]:
		"""Tabs for the top panel: pinned folders and playlists that aren't hidden.

		A pinned folder stands in for everything inside it.
		"""
		out: list[int | PlaylistFolder] = []

		def add(items: list[int | PlaylistFolder]) -> None:
			for entry in items:
				if isinstance(entry, int):
					if not hidden(entry):
						out.append(entry)
				elif entry.pinned:
					out.append(entry)
				else:
					add(entry.children)

		add(self.root)
		return out

	# --- Syncing with multi_playlist

	def sync(self, order: list[int]) -> bool:
		"""Bring the tree in line with the playlist order in multi_playlist.

		Playlists missing from the tree are placed after the playlist before
		them (so a playlist inserted next to one in a folder joins that folder)
		or at the start or end of the root. Playlists gone from multi_playlist
		are dropped. Returns True if the tree changed.
		"""
		key = tuple(order)
		if key == self._order:
			return False
		if len(set(key)) != len(key):
			return False

		current = self.playlist_order()
		if current == order:
			self._order = key
			return False

		present = set(order)
		for u in current:
			if u not in present:
				items, i = self._locate(u)
				del items[i]
		self._changed()
		current = [u for u in current if u in present]

		kept = _kept_by_lis(current, order)
		for u in current:
			if u not in kept:
				items, i = self._locate(u)
				del items[i]
		self._changed()

		last = len(order) - 1
		for i, u in enumerate(order):
			if u in kept:
				continue
			if i == 0:
				self.root.insert(0, u)
			elif i == last:
				self.root.append(u)
			else:
				items, j = self._locate(order[i - 1])
				items.insert(j + 1, u)
			self._changed()

		self._order = key
		return True

	def in_sync(self, order: list[int]) -> bool:
		return tuple(order) == self._order

	def mark_synced(self) -> None:
		"""Record that multi_playlist now follows the tree order."""
		self._order = tuple(self.playlist_order())

	# --- Editing

	def _new_uuid(self) -> int:
		while True:
			u = random.randrange(1, 100000000)
			if u not in self._folders:
				return u

	def new_folder(self, title: str, parent: PlaylistFolder | None = None, index: int | None = None) -> PlaylistFolder | None:
		if self.level(parent) >= MAX_DEPTH:
			return None
		folder = PlaylistFolder(uuid_int=self._new_uuid(), title=title, colour=len(self._folders) % len(FOLDER_COLOURS))
		items = self.container(parent)
		items.insert(len(items) if index is None else index, folder)
		self._changed()
		return folder

	def delete_folder(self, folder: PlaylistFolder) -> None:
		"""Remove a folder, moving what it held up into its place."""
		items, i = self._locate(folder)
		items[i:i + 1] = folder.children
		self._changed()

	def can_place(self, entry: int | PlaylistFolder, parent: PlaylistFolder | None) -> bool:
		if isinstance(entry, int):
			return True
		if parent is entry or (parent is not None and self.contains(entry, parent)):
			return False
		return self.level(parent) + self.height(entry) <= MAX_DEPTH

	def move(self, entry: int | PlaylistFolder, parent: PlaylistFolder | None, index: int | None = None) -> bool:
		"""Move an entry into a container at an index (None for the end)."""
		if not self.can_place(entry, parent):
			return False
		items, i = self._locate(entry)
		target = self.container(parent)
		if index is None:
			index = len(target)
		if items is target and i < index:
			index -= 1
		del items[i]
		target.insert(index, entry)
		self._changed()
		return True

	def move_beside(self, entry: int | PlaylistFolder, ref: int | PlaylistFolder, after: bool) -> bool:
		"""Move an entry next to another, into the same container."""
		if entry is ref or (isinstance(entry, int) and entry == ref):
			return False
		parent = self.parent_of(ref)
		if not self.can_place(entry, parent):
			return False
		items, i = self._locate(entry)
		del items[i]
		target, j = self._locate(ref)
		target.insert(j + 1 if after else j, entry)
		self._changed()
		return True
