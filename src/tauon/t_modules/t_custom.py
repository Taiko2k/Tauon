"""Custom Layout System.

An opt-in layout engine that composes the window from a tree of nested stacks
(vertical / horizontal) whose leaves are widgets drawn into arbitrary rects. It
is completely inert unless ``gui.custom_mode`` is set, so the existing preset
layouts are unaffected.

Implemented here:

* Layout tree (``Stack`` / ``Leaf``) of arbitrary nesting depth, with empty
  leaves, per-node gutter/border, per-axis pixel locks and an aspect lock.
* The resize / layout pass: locked children take fixed (scaled) pixels, the rest
  split the remainder by ``weight``; the cross axis fills.
* Edit mode: hover highlight, right-click context menu (Add stack / Add widget /
  Remove / Remove Stack / Lock V/H/Aspect / Gutter / Border / Load Template),
  edge-drag resizing with weight/pixel semantics and resize cursors.
* Validation: a stack must keep at least one child scalable on its axis
  (rejected with an error toast), and single-instance widgets are gated.
* Offscreen render-to-rect compositing (shared ``gui.tracklist_texture`` scratch
  target, clipped blit onto the frame), plus the "Size too small" fallback.
* A widget registry: a real album Art Box adapter and clearly-labelled
  placeholders for the heavier panels (drop-in adapters land later).
* Window-controls fallback drawn on hover when no widget provides them.
* Three slots (Custom A/B/C) persisted to ``custom_layouts.json``.

Deferred: pixel-faithful adapters for the heavy existing panels (Tracklist,
Gallery, side-panel internals) — those require extracting tightly-coupled draw
code and are added as registry adapters without touching the engine.
"""
from __future__ import annotations

import builtins
import json
import logging
from typing import TYPE_CHECKING, Callable

import sdl3

from tauon.t_modules.t_extra import ColourRGBA

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Tauon


def _t(s: str) -> str:
	"""Translate via the app's installed gettext ``_`` when present, else
	identity (so the module is importable/testable standalone)."""
	f = getattr(builtins, "_", None)
	return f(s) if callable(f) else s


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------

class Widget:
	"""Base widget: knows how to draw into a local rect and, optionally, handle a
	click within it. Declares sizing constraints so the engine can auto-lock
	axes, enforce minimums and gate single-instance widgets.
	"""

	kind: str = "widget"
	name: str = "Widget"
	lock_v: bool = False
	lock_h: bool = False
	fixed_w: int = 0
	fixed_h: int = 0
	min_w: int = 40
	min_h: int = 30
	single_instance: bool = False
	draws_window_controls: bool = False
	# When True the engine routes the widget through the offscreen scratch
	# texture before compositing (for widgets that may draw out of bounds).
	offscreen: bool = True

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		raise NotImplementedError

	def click(self, tauon: Tauon, local_x: int, local_y: int, w: int, h: int) -> None:
		return None


class PlaceholderWidget(Widget):
	"""A labelled coloured box standing in for a not-yet-extracted panel. Carries
	the panel's intended sizing defaults so the layout behaviour is already
	correct; only the visual content is a placeholder. Also used to demonstrate
	the offscreen composite path and per-widget input routing.
	"""

	def __init__(self, spec: WidgetSpec) -> None:
		self.kind = spec.kind
		self.name = spec.name
		self.lock_v = spec.lock_v
		self.lock_h = spec.lock_h
		self.fixed_w = spec.fixed_w
		self.fixed_h = spec.fixed_h
		self.single_instance = spec.single_instance
		self.draws_window_controls = spec.draws_window_controls
		self.colour = spec.colour
		self._flash = 0

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		gui = tauon.gui
		ddt = tauon.ddt
		colour = self.colour
		if self._flash:
			colour = ColourRGBA(
				min(255, colour.r + 50), min(255, colour.g + 50), min(255, colour.b + 50), colour.a)
			self._flash -= 1
			gui.update = 2
		ddt.rect((x, y, w, h), colour)
		ddt.text_background_colour = colour
		ddt.text(
			(round(x + w / 2), round(y + h / 2) - 9 * gui.scale, 2),
			self.name, ColourRGBA(225, 225, 225, 255), 314, max_w=round(w - 8 * gui.scale))

	def click(self, tauon: Tauon, local_x: int, local_y: int, w: int, h: int) -> None:
		self._flash = 12
		tauon.gui.update = 2


class ArtBoxWidget(Widget):
	"""Real album art placed into an arbitrary rect; keeps a centred square."""

	kind = "art"
	name = "Art Box"
	min_w = 32
	min_h = 32
	offscreen = False

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		gui = tauon.gui
		track = tauon.pctl.playing_object()
		if track is None:
			tauon.ddt.rect((x, y, w, h), ColourRGBA(20, 20, 20, 255))
			tauon.ddt.text_background_colour = ColourRGBA(20, 20, 20, 255)
			tauon.ddt.text(
				(round(x + w / 2), round(y + h / 2) - 9 * gui.scale, 2),
				"No track", ColourRGBA(120, 120, 120, 255), 313)
			return
		side = max(1, min(round(w), round(h)))
		ox = round(x) + (round(w) - side) // 2
		oy = round(y) + (round(h) - side) // 2
		tauon.album_art_gen.display(track, [ox, oy], (side, side), fast=True)


class WidgetSpec:
	"""Registry entry describing an addable widget and its sizing defaults."""

	def __init__(self, kind: str, name: str, category: str, factory: Callable[[WidgetSpec], Widget],
			lock_v: bool = False, lock_h: bool = False, fixed_w: int = 0, fixed_h: int = 0,
			single_instance: bool = False, draws_window_controls: bool = False,
			colour: ColourRGBA | None = None, in_default: bool = True) -> None:
		self.kind = kind
		self.name = name
		self.category = category
		self.factory = factory
		self.lock_v = lock_v
		self.lock_h = lock_h
		self.fixed_w = fixed_w
		self.fixed_h = fixed_h
		self.single_instance = single_instance
		self.draws_window_controls = draws_window_controls
		self.colour = colour or ColourRGBA(28, 28, 34, 255)
		self.in_default = in_default

	def make(self) -> Widget:
		return self.factory(self)


def _placeholder(spec: WidgetSpec) -> Widget:
	return PlaceholderWidget(spec)


def _art(spec: WidgetSpec) -> Widget:
	return ArtBoxWidget()


# Registry — the Add menu and (de)serialization are driven by this table. The
# lock / single-instance defaults follow the agreed widget table.
WIDGET_SPECS: list[WidgetSpec] = [
	WidgetSpec("top_panel", "Top Panel", "Panels", _placeholder,
		lock_v=True, fixed_h=30, draws_window_controls=True, colour=ColourRGBA(38, 38, 46, 255)),
	WidgetSpec("playback_panel", "Playback Panel", "Panels", _placeholder,
		lock_v=True, fixed_h=64, colour=ColourRGBA(32, 32, 40, 255)),
	WidgetSpec("tab_strip", "Playlist Tab Strip", "Panels", _placeholder,
		lock_v=True, fixed_h=28, colour=ColourRGBA(34, 34, 42, 255)),
	WidgetSpec("tracklist", "Tracklist", "Content", _placeholder, colour=ColourRGBA(24, 24, 28, 255)),
	WidgetSpec("gallery", "Album Gallery", "Content", _placeholder, colour=ColourRGBA(26, 24, 30, 255)),
	WidgetSpec("art", "Art Box", "Content", _art, colour=ColourRGBA(20, 20, 20, 255)),
	WidgetSpec("folder_nav", "Folder Navigator", "Content", _placeholder, colour=ColourRGBA(24, 26, 28, 255)),
	WidgetSpec("artist_list", "Artist List", "Content", _placeholder, colour=ColourRGBA(24, 28, 26, 255)),
	WidgetSpec("queue", "Queue", "Content", _placeholder, colour=ColourRGBA(28, 26, 24, 255)),
	WidgetSpec("lyrics", "Lyrics Box", "Content", _placeholder, colour=ColourRGBA(26, 26, 30, 255)),
	WidgetSpec("meta_center", "Centered Metadata", "Content", _placeholder, colour=ColourRGBA(30, 30, 34, 255)),
	WidgetSpec("meta_align", "Aligned Metadata", "Content", _placeholder, colour=ColourRGBA(30, 32, 34, 255)),
	WidgetSpec("milkdrop", "MilkDrop Box", "Visualizers", _placeholder,
		single_instance=True, colour=ColourRGBA(18, 18, 28, 255), in_default=False),
	WidgetSpec("spectrum", "Spectrum / Level Meter", "Visualizers", _placeholder,
		lock_v=True, fixed_h=40, colour=ColourRGBA(20, 22, 26, 255), in_default=False),
	WidgetSpec("side_panel", "Side Panel (composite)", "Panels", _placeholder, colour=ColourRGBA(28, 28, 32, 255)),
]
SPEC_BY_KIND: dict[str, WidgetSpec] = {s.kind: s for s in WIDGET_SPECS}


def make_widget(kind: str) -> Widget | None:
	spec = SPEC_BY_KIND.get(kind)
	return spec.make() if spec else None


# ---------------------------------------------------------------------------
# Layout tree
# ---------------------------------------------------------------------------

class Node:
	"""Base layout node: sizing within the parent stack + computed rect."""

	def __init__(self) -> None:
		self.weight: float = 1.0
		self.lock_v: bool = False
		self.lock_h: bool = False
		self.fixed_w: int = 0
		self.fixed_h: int = 0
		self.aspect: bool = False          # keep widget content aspect on draw
		self.gutter: int = 0               # inset around content, px (unscaled)
		self.border: bool = False
		self.rect: tuple[float, float, float, float] = (0, 0, 0, 0)

	# -- serialization --
	def _base_dict(self) -> dict:
		return {
			"weight": self.weight, "lock_v": self.lock_v, "lock_h": self.lock_h,
			"fixed_w": self.fixed_w, "fixed_h": self.fixed_h, "aspect": self.aspect,
			"gutter": self.gutter, "border": self.border,
		}

	def _load_base(self, d: dict) -> None:
		self.weight = d.get("weight", 1.0)
		self.lock_v = d.get("lock_v", False)
		self.lock_h = d.get("lock_h", False)
		self.fixed_w = d.get("fixed_w", 0)
		self.fixed_h = d.get("fixed_h", 0)
		self.aspect = d.get("aspect", False)
		self.gutter = d.get("gutter", 0)
		self.border = d.get("border", False)


class Leaf(Node):
	def __init__(self, widget: Widget | None = None) -> None:
		super().__init__()
		self.widget = widget
		if widget is not None:
			self._adopt(widget)

	def _adopt(self, widget: Widget) -> None:
		if widget.lock_v:
			self.lock_v = True
			self.fixed_h = widget.fixed_h
		if widget.lock_h:
			self.lock_h = True
			self.fixed_w = widget.fixed_w

	@property
	def kind(self) -> str | None:
		return self.widget.kind if self.widget else None

	def to_dict(self) -> dict:
		d = self._base_dict()
		d["type"] = "leaf"
		d["kind"] = self.kind
		return d

	@staticmethod
	def from_dict(d: dict) -> "Leaf":
		kind = d.get("kind")
		leaf = Leaf(make_widget(kind) if kind else None)
		leaf._load_base(d)
		return leaf


class Stack(Node):
	def __init__(self, orient: str, children: list[Node]) -> None:
		super().__init__()
		assert orient in ("v", "h")
		self.orient = orient
		self.children = children

	def to_dict(self) -> dict:
		d = self._base_dict()
		d["type"] = "stack"
		d["orient"] = self.orient
		d["children"] = [c.to_dict() for c in self.children]
		return d

	@staticmethod
	def from_dict(d: dict) -> "Stack":
		st = Stack(d.get("orient", "v"), [node_from_dict(c) for c in d.get("children", [])])
		st._load_base(d)
		return st


def node_from_dict(d: dict) -> Node:
	return Stack.from_dict(d) if d.get("type") == "stack" else Leaf.from_dict(d)


# -- layout pass ------------------------------------------------------------

def _fixed_on(node: Node, axis: str, scale: float) -> float | None:
	if axis == "v" and node.lock_v:
		return node.fixed_h * scale
	if axis == "h" and node.lock_h:
		return node.fixed_w * scale
	return None


def layout(node: Node, x: float, y: float, w: float, h: float, scale: float) -> None:
	"""Assign rects to ``node`` and its descendants. Locked children take fixed
	(scaled) pixels along the parent's axis; the remainder splits by weight; the
	cross axis fills. Gutter insets each child's allotted slot.
	"""
	node.rect = (x, y, w, h)
	if not isinstance(node, Stack) or not node.children:
		return

	axis = node.orient
	total = h if axis == "v" else w
	fixed = [_fixed_on(c, axis, scale) for c in node.children]
	locked_total = sum(f for f in fixed if f is not None)
	flex = [c for c, f in zip(node.children, fixed) if f is None]
	weight_total = sum(c.weight for c in flex) or 1.0
	available = max(0.0, total - locked_total)

	cursor = y if axis == "v" else x
	for child, f in zip(node.children, fixed):
		length = f if f is not None else available * (child.weight / weight_total)
		g = child.gutter * scale
		if axis == "v":
			cx, cy, cw, ch = x + g, cursor + g, max(0.0, w - 2 * g), max(0.0, length - 2 * g)
		else:
			cx, cy, cw, ch = cursor + g, y + g, max(0.0, length - 2 * g), max(0.0, h - 2 * g)
		# The child's rect already accounts for its gutter inset; descendants and
		# draw use it directly (no double inset).
		layout(child, cx, cy, cw, ch, scale)
		cursor += length


def content_rect(leaf: Leaf, scale: float) -> tuple[float, float, float, float]:
	"""Drawable rect of a leaf. The gutter inset is already baked into
	``leaf.rect`` by the layout pass, so this is just the rect."""
	return leaf.rect


def iter_leaves(node: Node):
	if isinstance(node, Stack):
		for c in node.children:
			yield from iter_leaves(c)
	else:
		yield node


def leaf_at(node: Node, px: float, py: float) -> Node | None:
	x, y, w, h = node.rect
	if not (x <= px < x + w and y <= py < y + h):
		return None
	if isinstance(node, Stack):
		for c in node.children:
			hit = leaf_at(c, px, py)
			if hit is not None:
				return hit
		return node
	return node


def find_parent(root: Node, target: Node) -> Stack | None:
	if isinstance(root, Stack):
		for c in root.children:
			if c is target:
				return root
			found = find_parent(c, target)
			if found is not None:
				return found
	return None


def count_kind(root: Node, kind: str) -> int:
	return sum(1 for leaf in iter_leaves(root) if isinstance(leaf, Leaf) and leaf.kind == kind)


def _contains(node: Node, target: Node) -> bool:
	if node is target:
		return True
	return isinstance(node, Stack) and any(_contains(c, target) for c in node.children)


def top_level_ancestor(root: Node, target: Node) -> Node | None:
	"""The direct child of ``root`` that is, or contains, ``target`` — i.e. the
	topmost stack/segment the target belongs to, one level below the root."""
	if not isinstance(root, Stack):
		return None
	for child in root.children:
		if _contains(child, target):
			return child
	return None


def stack_has_flex_axis(stack: Stack) -> bool:
	"""True if at least one child is scalable along the stack's axis."""
	axis = stack.orient
	for c in stack.children:
		if axis == "v" and not c.lock_v:
			return True
		if axis == "h" and not c.lock_h:
			return True
	return False


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

GUTTER_OPTIONS = [0, 2, 4, 8, 16]
STACK_COUNTS = [2, 3, 4, 5]
TEMPLATES = ["Standard", "Art-focused", "Minimal"]
SLOT_NAMES = ["Custom A", "Custom B", "Custom C"]


class CustomLayout:
	"""Owns the custom layout trees and drives them. Active only while
	``gui.custom_mode`` is set; edits only while ``gui.custom_edit`` is set.
	"""

	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.gui = tauon.gui
		self.ddt = tauon.ddt
		self.renderer = tauon.renderer
		self.slots: list[Node | None] = [None, None, None]
		self.active_slot = 0
		self._loaded = False

		# edit-mode transient state
		self.menu_target: Node | None = None
		self.drag: dict | None = None          # {stack, index, axis}
		# Native context menu (a t_main Menu instance), built by
		# build_custom_layout_menu() in t_main and assigned here. The engine only
		# activates it and exposes callbacks; all drawing is the native system's.
		self.menu = None

	# -- templates / defaults -----------------------------------------------

	def _empty(self) -> Leaf:
		return Leaf(None)

	def _leaf(self, kind: str) -> Leaf:
		return Leaf(make_widget(kind))

	def template(self, name: str) -> Node:
		if name == "Minimal":
			top = self._leaf("top_panel")
			body = self._leaf("tracklist")
			body.weight = 1.0
			return Stack("v", [top, body])
		if name == "Art-focused":
			top = self._leaf("top_panel")
			art = self._leaf("art")
			art.weight = 1.0
			meta = self._leaf("meta_center")
			meta.weight = 1.0
			body = Stack("h", [art, meta])
			body.weight = 1.0
			bottom = self._leaf("playback_panel")
			return Stack("v", [top, body, bottom])
		# "Standard" (and fallback): top / [tracklist | art over meta] / playback
		top = self._leaf("top_panel")
		tracklist = self._leaf("tracklist")
		tracklist.weight = 3.0
		art = self._leaf("art")
		art.weight = 2.0
		meta = self._leaf("meta_center")
		meta.weight = 1.0
		side = Stack("v", [art, meta])
		side.weight = 1.0
		body = Stack("h", [tracklist, side])
		body.weight = 1.0
		bottom = self._leaf("playback_panel")
		return Stack("v", [top, body, bottom])

	def _default_tree(self) -> Node:
		"""Per spec, an unconfigured slot starts as a vertical 2-stack with the
		Top Panel locked at the top and an empty scalable segment below.
		"""
		top = self._leaf("top_panel")
		body = self._empty()
		body.weight = 1.0
		return Stack("v", [top, body])

	def ensure_slot(self) -> Node:
		if not self._loaded:
			self.load_slots()
		if self.slots[self.active_slot] is None:
			self.slots[self.active_slot] = self._default_tree()
		return self.slots[self.active_slot]

	# -- persistence ---------------------------------------------------------

	def _path(self):
		return self.tauon.user_directory / "custom_layouts.json"

	def load_slots(self) -> None:
		self._loaded = True
		try:
			p = self._path()
			if p.is_file():
				data = json.loads(p.read_text(encoding="utf-8"))
				for i in range(3):
					d = data.get(str(i))
					self.slots[i] = node_from_dict(d) if d else None
		except Exception:
			logging.exception("Failed to load custom layouts")

	def save_slots(self) -> None:
		try:
			data = {str(i): (n.to_dict() if n else None) for i, n in enumerate(self.slots)}
			self._path().write_text(json.dumps(data, indent=1), encoding="utf-8")
		except Exception:
			logging.exception("Failed to save custom layouts")

	# -- entry / exit --------------------------------------------------------

	def enter(self, slot: int) -> None:
		self.active_slot = slot
		self.gui.custom_mode = True
		self.gui.custom_edit = False
		self._close_menu()
		self.ensure_slot()
		self.tauon.show_message(_t("%s — press F7 to customize, Escape to return") % SLOT_NAMES[slot])
		self.gui.update = 2

	def exit_mode(self) -> None:
		self.gui.custom_mode = False
		self.gui.custom_edit = False
		self._close_menu()
		self.gui.update = 2

	def toggle_edit(self) -> None:
		self.gui.custom_edit = not self.gui.custom_edit
		self._close_menu()
		self.gui.update = 2

	# -- tree actions (pure; unit-tested) -----------------------------------

	def act_add_stack(self, target: Node, orient: str, count: int) -> None:
		root = self.ensure_slot()
		children: list[Node] = []
		if isinstance(target, Leaf) and target.widget is not None:
			# Keep the existing widget as the first cell.
			keep = Leaf(target.widget)
			keep._load_base(target.to_dict())
			children.append(keep)
		while len(children) < count:
			children.append(self._empty())
		new = Stack(orient, children)
		# Inherit the target's sizing within its own parent.
		new.weight = target.weight
		self._replace(root, target, new)
		self.save_slots()

	def act_add_widget(self, target: Node, kind: str) -> bool:
		root = self.ensure_slot()
		spec = SPEC_BY_KIND.get(kind)
		if spec is None:
			return False
		if spec.single_instance and count_kind(root, kind) > 0:
			self.tauon.show_message(_t("Only one %s allowed") % spec.name, mode="warning")
			return False
		if not isinstance(target, Leaf):
			return False
		old = (target.widget, target.lock_v, target.lock_h, target.fixed_w, target.fixed_h)
		target.widget = spec.make()
		target._adopt(target.widget)
		# Validate that adding (with any auto-lock) didn't fully lock a parent axis.
		parent = find_parent(root, target)
		if parent is not None and not stack_has_flex_axis(parent):
			target.widget, target.lock_v, target.lock_h, target.fixed_w, target.fixed_h = old
			self.tauon.show_message(_t("Can't add: every panel in this row/column would be locked"), mode="warning")
			return False
		self.save_slots()
		return True

	def act_remove_widget(self, target: Node) -> None:
		if isinstance(target, Leaf):
			target.widget = None
			target.lock_v = target.lock_h = False
			target.aspect = False
			self.save_slots()

	def act_remove_stack(self, target: Node) -> None:
		"""Remove the topmost stack the target segment belongs to — the direct
		child of the root that contains it — replacing it with a single empty
		segment. The rest of the layout (root + siblings) is left intact; this
		never clears the entire layout.
		"""
		root = self.slots[self.active_slot]
		if not isinstance(root, Stack) or target is None or target is root:
			return
		top = top_level_ancestor(root, target)
		if top is None:
			return
		new = self._empty()
		new.weight = top.weight
		root.children[root.children.index(top)] = new
		self.save_slots()

	def act_set_lock(self, target: Node, axis: str) -> None:
		root = self.ensure_slot()
		if axis == "v":
			new = not target.lock_v
			if new:
				target.fixed_h = max(1, round(target.rect[3] / self.gui.scale))
			target.lock_v = new
		elif axis == "h":
			new = not target.lock_h
			if new:
				target.fixed_w = max(1, round(target.rect[2] / self.gui.scale))
			target.lock_h = new
		else:  # aspect
			target.aspect = not target.aspect
			self.save_slots()
			return
		parent = find_parent(root, target)
		if parent is not None and not stack_has_flex_axis(parent):
			# Revert — would fully lock the stack's axis.
			if axis == "v":
				target.lock_v = False
			else:
				target.lock_h = False
			self.tauon.show_message(_t("Can't lock: every panel in this row/column would be locked"), mode="warning")
			return
		self.save_slots()

	def act_set_gutter(self, target: Node, px: int) -> None:
		target.gutter = px
		self.save_slots()

	def act_toggle_border(self, target: Node) -> None:
		target.border = not target.border
		self.save_slots()

	def act_load_template(self, name: str) -> None:
		self.slots[self.active_slot] = self.template(name)
		self.save_slots()

	def _replace(self, root: Node, target: Node, new: Node) -> None:
		if target is root:
			self.slots[self.active_slot] = new
			return
		parent = find_parent(root, target)
		if parent is not None:
			parent.children[parent.children.index(target)] = new

	# -- input ---------------------------------------------------------------

	def handle_input(self) -> None:
		"""Process interaction early in the frame and consume events so the
		underlying UI doesn't also react. Called only while custom_mode is set.
		"""
		inp = self.tauon.inp
		gui = self.gui

		# While the native context menu or a message box (confirm dialog) is open,
		# let those systems handle input. The main loop already routes clicks to
		# active menus before this runs, so just stand down.
		if (self.menu is not None and self.menu.active) or gui.message_box:
			return

		if not gui.custom_edit:
			if inp.key_esc_press:
				self.exit_mode()
			elif inp.mouse_click:
				self._route_click(inp)
			self._consume(inp)
			return

		# --- edit mode ---
		if inp.key_esc_press:
			self.exit_mode()
			self._consume(inp)
			return

		# Edge-drag resize.
		if self.drag is not None:
			if inp.mouse_down:
				self._drag_move(inp)
			else:
				self.drag = None
				self.save_slots()
		elif inp.mouse_click:
			self._try_start_drag(inp)

		# Right-click opens the native context menu on the segment under cursor.
		if inp.right_click:
			root = self.ensure_slot()
			layout(root, 0, 0, self.tauon.window_size[0], self.tauon.window_size[1], gui.scale)
			self.menu_target = leaf_at(root, inp.mouse_position[0], inp.mouse_position[1])
			if self.menu is not None:
				self.menu.activate(in_reference=None, position=[inp.mouse_position[0], inp.mouse_position[1]])

		self._consume(inp)

	def _consume(self, inp) -> None:
		inp.mouse_click = False
		inp.right_click = False
		inp.mouse_up = False
		inp.key_esc_press = False
		inp.key_return_press = False

	def _route_click(self, inp) -> None:
		root = self.ensure_slot()
		layout(root, 0, 0, self.tauon.window_size[0], self.tauon.window_size[1], self.gui.scale)
		seg = leaf_at(root, inp.mouse_position[0], inp.mouse_position[1])
		if isinstance(seg, Leaf) and seg.widget is not None:
			x, y, w, h = content_rect(seg, self.gui.scale)
			seg.widget.click(
				self.tauon, round(inp.mouse_position[0] - x), round(inp.mouse_position[1] - y), round(w), round(h))

	# -- drag ----------------------------------------------------------------

	def _try_start_drag(self, inp) -> bool:
		root = self.ensure_slot()
		layout(root, 0, 0, self.tauon.window_size[0], self.tauon.window_size[1], self.gui.scale)
		grab = 5 * self.gui.scale
		hit = self._boundary_at(root, inp.mouse_position[0], inp.mouse_position[1], grab)
		if hit is not None:
			orient, stack, index = hit
			self.drag = {"stack": stack, "index": index, "axis": stack.orient,
				"last": (inp.mouse_position[0], inp.mouse_position[1])}
			return True
		return False

	def _iter_boundaries(self, node: Node, grab: float):
		"""Yield (orient, grab_rect, stack, index) for every internal stack
		boundary, outermost first. Single source of truth for both the
		resize-cursor hit-test and the hover field registration, so the two stay
		byte-aligned — any mismatch makes the cursor stick (cursor set on a pixel
		that no field covers, so leaving it never triggers a repaint)."""
		if isinstance(node, Stack):
			for i, c in enumerate(node.children[:-1]):
				x, y, w, h = node.rect
				cx, cy, cw, ch = c.rect
				if node.orient == "v":
					yield ("v", (x, cy + ch - grab, w, grab * 2), node, i)
				else:
					yield ("h", (cx + cw - grab, y, grab * 2, h), node, i)
			for c in node.children:
				yield from self._iter_boundaries(c, grab)

	def _boundary_at(self, node: Node, mx: float, my: float, grab: float):
		for orient, rect, stack, index in self._iter_boundaries(node, grab):
			rx, ry, rw, rh = rect
			if rx <= mx < rx + rw and ry <= my < ry + rh:
				return (orient, stack, index)
		return None

	def _drag_move(self, inp) -> None:
		d = self.drag
		stack: Stack = d["stack"]
		i = d["index"]
		axis = d["axis"]
		lx, ly = d["last"]
		mx, my = inp.mouse_position[0], inp.mouse_position[1]
		delta = (my - ly) if axis == "v" else (mx - lx)
		d["last"] = (mx, my)
		if delta == 0:
			return
		a = stack.children[i]
		b = stack.children[i + 1]
		a_locked = a.lock_v if axis == "v" else a.lock_h
		b_locked = b.lock_v if axis == "v" else b.lock_h
		scale = self.gui.scale
		min_px = 24 * scale

		def px(n: Node) -> float:
			return n.rect[3] if axis == "v" else n.rect[2]

		if a_locked and not b_locked:
			cur = (a.fixed_h if axis == "v" else a.fixed_w) * scale
			newpx = max(min_px, cur + delta)
			if axis == "v":
				a.fixed_h = round(newpx / scale)
			else:
				a.fixed_w = round(newpx / scale)
		elif b_locked and not a_locked:
			cur = (b.fixed_h if axis == "v" else b.fixed_w) * scale
			newpx = max(min_px, cur - delta)
			if axis == "v":
				b.fixed_h = round(newpx / scale)
			else:
				b.fixed_w = round(newpx / scale)
		elif not a_locked and not b_locked:
			pa, pb = px(a), px(b)
			total_px = pa + pb
			total_w = a.weight + b.weight
			new_pa = min(max(min_px, pa + delta), total_px - min_px)
			a.weight = total_w * (new_pa / total_px)
			b.weight = total_w - a.weight
		self.gui.update = 2

	# -- context menu (native Menu system) ----------------------------------
	#
	# The MenuItem objects are built once in build_custom_layout_menu() (t_main)
	# and wired to the callbacks below. They act on self.menu_target, which is
	# set when the menu is activated. Submenu items receive their value via the
	# MenuItem ``args`` field, so callbacks are (reference, value); main-item
	# callbacks take no arguments. show_test/disable_test predicates receive the
	# menu reference (unused — they read self.menu_target).

	def _close_menu(self) -> None:
		"""Close the native context menu if it is the active one."""
		if self.menu is not None and self.menu.active:
			self.menu.active = False
			from tauon.t_modules.t_main import Menu  # local import avoids cycle
			for m in Menu.instances:
				if m.active:
					break
			else:
				Menu.active = False

	# -- action callbacks --
	def _menu_add_stack(self, ref, payload) -> None:
		orient, count = payload
		if self.menu_target is not None:
			self.act_add_stack(self.menu_target, orient, count)

	def _menu_add_widget(self, ref, kind) -> None:
		if self.menu_target is not None:
			self.act_add_widget(self.menu_target, kind)

	def _menu_remove_widget(self) -> None:
		if self.menu_target is not None:
			self.act_remove_widget(self.menu_target)

	def _menu_remove_stack(self) -> None:
		if self.menu_target is not None:
			self.act_remove_stack(self.menu_target)

	def _menu_lock_v(self) -> None:
		if self.menu_target is not None:
			self.act_set_lock(self.menu_target, "v")

	def _menu_lock_h(self) -> None:
		if self.menu_target is not None:
			self.act_set_lock(self.menu_target, "h")

	def _menu_lock_aspect(self) -> None:
		if self.menu_target is not None:
			self.act_set_lock(self.menu_target, "a")

	def _menu_border(self) -> None:
		if self.menu_target is not None:
			self.act_toggle_border(self.menu_target)

	def _menu_gutter(self, ref, px) -> None:
		if self.menu_target is not None:
			self.act_set_gutter(self.menu_target, px)

	def _menu_template(self, ref, name) -> None:
		self.tauon.gui.message_box_confirm_callback = self._confirm_load_template
		self.tauon.gui.message_box_no_callback = None
		self.tauon.gui.message_box_confirm_reference = (name,)
		self.tauon.show_message(_t("Load '%s' template? Replaces this layout.") % name, mode="confirm")

	def _confirm_load_template(self, name) -> None:
		self.act_load_template(name)

	# -- test predicates (receive the menu reference; read self.menu_target) --
	def _t_has_widget(self, ref=None) -> bool:
		return isinstance(self.menu_target, Leaf) and self.menu_target.widget is not None

	def _t_locked_v(self, ref=None) -> bool:
		return self.menu_target is not None and self.menu_target.lock_v

	def _t_unlocked_v(self, ref=None) -> bool:
		return self.menu_target is not None and not self.menu_target.lock_v

	def _t_locked_h(self, ref=None) -> bool:
		return self.menu_target is not None and self.menu_target.lock_h

	def _t_unlocked_h(self, ref=None) -> bool:
		return self.menu_target is not None and not self.menu_target.lock_h

	def _t_aspect_on(self, ref=None) -> bool:
		return self.menu_target is not None and self.menu_target.aspect

	def _t_aspect_off(self, ref=None) -> bool:
		return self.menu_target is not None and not self.menu_target.aspect

	def _t_border_on(self, ref=None) -> bool:
		return self.menu_target is not None and self.menu_target.border

	def _t_border_off(self, ref=None) -> bool:
		return self.menu_target is not None and not self.menu_target.border

	def kind_disabled(self, kind: str) -> bool:
		"""Disable-test for an Add-widget item: True if the (single-instance)
		widget already exists in the active layout."""
		spec = SPEC_BY_KIND.get(kind)
		if spec is None or not spec.single_instance:
			return False
		root = self.slots[self.active_slot]
		return root is not None and count_kind(root, kind) > 0

	# -- rendering -----------------------------------------------------------

	def render(self) -> None:
		tauon = self.tauon
		gui = self.gui
		ddt = self.ddt
		ww, wh = tauon.window_size[0], tauon.window_size[1]

		ddt.rect((0, 0, ww, wh), tauon.colours.playlist_panel_background)

		root = self.ensure_slot()
		layout(root, 0, 0, ww, wh, gui.scale)

		for leaf in iter_leaves(root):
			if isinstance(leaf, Leaf):
				self._draw_leaf(leaf)

		# Window-controls fallback when nothing provides them.
		if not self._provides_window_controls(root):
			self._draw_window_controls_fallback()

		if gui.custom_edit:
			self._draw_edit_overlay(root)

	def _provides_window_controls(self, root: Node) -> bool:
		return any(isinstance(l, Leaf) and l.widget is not None and l.widget.draws_window_controls
			for l in iter_leaves(root))

	def _draw_leaf(self, leaf: Leaf) -> None:
		tauon = self.tauon
		gui = self.gui
		ddt = self.ddt
		cx, cy, cw, ch = content_rect(leaf, gui.scale)
		widget = leaf.widget

		if widget is None:
			return  # empty segment: just background

		if cw < widget.min_w * gui.scale or ch < widget.min_h * gui.scale:
			ddt.rect((cx, cy, cw, ch), ColourRGBA(40, 20, 20, 255))
			ddt.text_background_colour = ColourRGBA(40, 20, 20, 255)
			ddt.text((round(cx + cw / 2), round(cy + ch / 2) - 8 * gui.scale, 2),
				"Size too small", ColourRGBA(200, 120, 120, 255), 211)
		else:
			dx, dy, dw, dh = cx, cy, cw, ch
			if leaf.aspect:
				# Keep a square content region (Art Box-style), centred.
				side = min(dw, dh)
				dx = cx + (cw - side) / 2
				dy = cy + (ch - side) / 2
				dw = dh = side
			if not widget.offscreen:
				widget.draw(tauon, dx, dy, dw, dh)
			else:
				self._draw_offscreen(widget, dx, dy, dw, dh)

		if leaf.border:
			b = max(1, round(1 * gui.scale))
			col = ColourRGBA(90, 90, 100, 255)
			ddt.rect((cx, cy, cw, b), col)
			ddt.rect((cx, cy + ch - b, cw, b), col)
			ddt.rect((cx, cy, b, ch), col)
			ddt.rect((cx + cw - b, cy, b, ch), col)

	def _draw_offscreen(self, widget: Widget, x: float, y: float, w: float, h: float) -> None:
		renderer = self.renderer
		gui = self.gui
		iw, ih = max(1, round(w)), max(1, round(h))
		prev = sdl3.SDL_GetRenderTarget(renderer)
		sdl3.SDL_SetRenderTarget(renderer, gui.tracklist_texture)
		sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
		sdl3.SDL_RenderClear(renderer)
		widget.draw(self.tauon, 0, 0, iw, ih)
		sdl3.SDL_SetRenderTarget(renderer, prev)
		src = sdl3.SDL_FRect(0, 0, iw, ih)
		dst = sdl3.SDL_FRect(round(x), round(y), iw, ih)
		sdl3.SDL_RenderTexture(renderer, gui.tracklist_texture, src, dst)

	def _draw_edit_overlay(self, root: Node) -> None:
		gui = self.gui
		ddt = self.ddt
		inp = self.tauon.inp
		ww, wh = self.tauon.window_size[0], self.tauon.window_size[1]
		ddt.rect((0, 0, ww, wh), ColourRGBA(255, 190, 50, 10))

		grab = 5 * gui.scale
		# Register hover regions so the GUI repaints as the mouse moves across
		# segments and resize boundaries. Tauon only redraws when the set of
		# fields under the cursor changes (see fields.test() in the main loop),
		# so these must be added every render regardless of current hover state.
		for lf in iter_leaves(root):
			self.tauon.fields.add(tuple(lf.rect))
		for _orient, brect, _stack, _idx in self._iter_boundaries(root, grab):
			self.tauon.fields.add(brect)

		menu_active = self.menu is not None and self.menu.active
		mx, my = inp.mouse_position[0], inp.mouse_position[1]
		# While the menu is open, keep the right-clicked segment highlighted;
		# otherwise track the segment under the cursor and show resize cursors.
		if menu_active:
			seg = self.menu_target
		else:
			hit = self._boundary_at(root, mx, my, grab)
			if hit is not None:
				# 12 = custom NS-resize cursor (see dispatch in main loop); 1 =
				# EW-resize (cursor_shift). cursor_top_side (9) isn't an NS cursor
				# on macOS/Linux, so we use our own.
				gui.cursor_want = 12 if hit[0] == "v" else 1
			seg = leaf_at(root, mx, my)
		if seg is not None:
			x, y, w, h = seg.rect
			b = round(2 * gui.scale)
			edge = ColourRGBA(255, 190, 50, 220)
			ddt.rect((x, y, w, b), edge)
			ddt.rect((x, y + h - b, w, b), edge)
			ddt.rect((x, y, b, h), edge)
			ddt.rect((x + w - b, y, b, h), edge)
			ddt.rect((x, y, w, h), ColourRGBA(255, 190, 50, 18))

	# -- window controls fallback -------------------------------------------

	def _draw_window_controls_fallback(self) -> None:
		"""Minimal min/maximize/close drawn top-right, shown on hover — so a
		layout without a Top Panel is still controllable.
		"""
		gui = self.gui
		ddt = self.ddt
		inp = self.tauon.inp
		ww = self.tauon.window_size[0]
		bw = round(46 * gui.scale)
		bh = round(28 * gui.scale)
		zone = (ww - bw * 3, 0, bw * 3, bh)
		# Register the hover zone every frame so moving into it triggers a redraw
		# (and the controls appear) — same fields requirement as everything else.
		self.tauon.fields.add(zone)
		hovering = self.tauon.coll(zone)
		if not hovering:
			return
		labels = [("—", self._win_minimize), ("□", self._win_maximize), ("✕", self._win_close)]
		for i, (label, cb) in enumerate(labels):
			bx = ww - bw * (3 - i)
			rect = (bx, 0, bw, bh)
			self.tauon.fields.add(rect)
			over = self.tauon.coll(rect)
			ddt.rect(rect, ColourRGBA(70, 70, 78, 200) if over else ColourRGBA(40, 40, 46, 160))
			ddt.text_background_colour = ColourRGBA(70, 70, 78, 200) if over else ColourRGBA(40, 40, 46, 160)
			ddt.text((bx + round(bw / 2), round(bh / 2) - 8 * gui.scale, 2), label, ColourRGBA(230, 230, 230, 255), 212)
			if over and inp.mouse_click:
				inp.mouse_click = False
				cb()

	def _win_minimize(self) -> None:
		try:
			sdl3.SDL_MinimizeWindow(self.tauon.t_window)
		except Exception:
			logging.exception("minimize failed")

	def _win_maximize(self) -> None:
		try:
			flags = sdl3.SDL_GetWindowFlags(self.tauon.t_window)
			if flags & sdl3.SDL_WINDOW_MAXIMIZED:
				sdl3.SDL_RestoreWindow(self.tauon.t_window)
			else:
				sdl3.SDL_MaximizeWindow(self.tauon.t_window)
		except Exception:
			logging.exception("maximize failed")

	def _win_close(self) -> None:
		self.tauon.exit("Custom layout close button")
