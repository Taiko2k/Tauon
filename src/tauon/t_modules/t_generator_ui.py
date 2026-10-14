# Copyright © 2026, Tauon contributors

"""The smart playlist (generator) editor box."""

from __future__ import annotations

import time
from functools import partial
from typing import TYPE_CHECKING

from tauon.t_modules import t_generator as gen
from tauon.t_modules.t_extra import ColourRGBA, alpha_blend

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Menu, Tauon

CATEGORY_COLOURS = {
	gen.SOURCE: ColourRGBA(79, 143, 220, 255),
	gen.ADD: ColourRGBA(76, 175, 80, 255),
	gen.FILTER: ColourRGBA(224, 160, 64, 255),
	gen.SORT: ColourRGBA(166, 120, 224, 255),
	gen.LIMIT: ColourRGBA(60, 184, 196, 255),
}
UNKNOWN_COLOUR = ColourRGBA(224, 85, 85, 255)
WARN_COLOUR = ColourRGBA(240, 170, 80, 255)
OK_COLOUR = ColourRGBA(100, 230, 100, 255)
SUGGESTION_LIMIT = 5
# Playlist and column pick lists show more, as they start with every choice
PICK_LIMIT = 8
ALL_TRACKS = "a"


class GeneratorEditBox:

	def __init__(self, tauon: Tauon) -> None:
		from tauon.t_modules.t_main import TextBox2, readable_text_colour  # noqa: PLC0415

		self.tauon = tauon
		self.gui = tauon.gui
		self.inp = tauon.inp
		self.ddt = tauon.ddt
		self.draw = tauon.draw
		self.coll = tauon.coll
		self.fields = tauon.fields
		self.pctl = tauon.pctl
		self.prefs = tauon.prefs
		self.colours = tauon.colours
		self.window_size = tauon.window_size
		self.thread_manager = tauon.thread_manager
		self.readable_colour = readable_text_colour

		self.active = False
		self.playlist_id = 0
		self.name_box = TextBox2(tauon)
		self.code_box = TextBox2(tauon)
		self.value_box = TextBox2(tauon)
		# "name", "code" or "value" (the step editor field)
		self.focus = "code"

		self.original_code: str | None = None
		self.original_title = ""
		self.original_ids: list[int] = []
		self.last_code = ""
		self.last_preset_name = ""

		# Step editor popover
		self.editing: int | None = None
		self.edit_step: gen.Step | None = None
		self.edit_op = ""
		# The editor field's text when it opened
		self.edit_initial = ""
		self.edit_rect = (0, 0, 0, 0)

		# Chip press and drag
		self.press_index: int | None = None
		self.press_position = (0, 0)
		# Pointer position within the pressed chip
		self.press_offset = (0, 0)
		self.dragging = False

		# Add menus by lane, plus "all" for codes shown as a single list
		self.add_menus: dict[str, Menu] = {}
		self.preset_menu: Menu | None = None

		self.suggestion_pools: dict[str, list[str]] = {}
		self.duration_key: tuple[int, int, str] | None = None
		self.duration = 0.0

		self.label_colour = self.colours.box_text_label
		self.input_colour = self.colours.box_input_text
		self.title_colour = self.colours.box_title_text
		self.input_enabled = False

	# Opening and closing -------------------------------------------------------

	def activate(self, index: int) -> None:
		if self.gui.radio_view or not 0 <= index < len(self.pctl.multi_playlist):
			return
		playlist = self.pctl.multi_playlist[index]
		self.playlist_id = playlist.uuid_int
		self.original_code = self.pctl.gen_codes.get(self.playlist_id)
		self.original_title = playlist.title
		self.original_ids = list(playlist.playlist_ids)
		code = self.original_code or ""
		self.name_box.set_text(playlist.title)
		self._set_code(code)
		self.last_code = code
		self.last_preset_name = ""
		self.focus = "code"
		self.editing = None
		self.edit_step = None
		self.press_index = None
		self.dragging = False
		self.suggestion_pools.clear()
		self.duration_key = None
		self.gui.gen_code_errors = False
		self.active = True
		self.gui.box_over = True
		if code:
			self._request_regen()

	def _close(self) -> None:
		self.active = False
		self.gui.box_over = False
		self.editing = None
		self.edit_step = None
		self._close_menus()
		self.gui.request_frame()

	def done(self) -> None:
		pl = self.pctl.id_to_pl(self.playlist_id)
		if pl is not None:
			title = self.name_box.text.strip()
			playlist = self.pctl.multi_playlist[pl]
			if title and title != playlist.title:
				old = playlist.title
				playlist.title = title
				self.tauon.rename_playlist_references(old, title)
			code = self.code_box.text.strip()
			if code:
				self.pctl.gen_codes[self.playlist_id] = code
			else:
				self.pctl.gen_codes.pop(self.playlist_id, None)
		self._close()

	def cancel(self) -> None:
		pl = self.pctl.id_to_pl(self.playlist_id)
		if self.gui.regen_single_id == self.playlist_id:
			self.gui.regen_single_id = None
		# Let a regeneration already running finish so it can't overwrite the restore
		deadline = time.monotonic() + 3
		while self.pctl.regen_in_progress and time.monotonic() < deadline:
			time.sleep(0.01)
		if self.original_code is None:
			self.pctl.gen_codes.pop(self.playlist_id, None)
		else:
			self.pctl.gen_codes[self.playlist_id] = self.original_code
		if pl is not None:
			playlist = self.pctl.multi_playlist[pl]
			playlist.title = self.original_title
			playlist.playlist_ids[:] = self.original_ids
			self.tauon.tree_view_box.clear_target_pl(0, self.playlist_id)
			self.gui.request_tracklist_redraw()
			self.tauon.reload()
		self._close()

	def convert_to_normal(self) -> None:
		"""Keep the current tracks and remove the generator."""
		self.pctl.gen_codes.pop(self.playlist_id, None)
		pl = self.pctl.id_to_pl(self.playlist_id)
		title = self.name_box.text.strip()
		if pl is not None and title:
			self.pctl.multi_playlist[pl].title = title
		self._close()

	# Code and token edits -----------------------------------------------------

	def _set_code(self, code: str) -> None:
		self.code_box.set_text(code)
		self.code_box.cursor_position = 0
		self.code_box.selection = 0

	def _tokens(self) -> list[str]:
		return gen.tokenize(self.code_box.text)[0]

	def _set_tokens(self, tokens: list[str]) -> None:
		self._set_code(gen.join(tokens))

	def _request_regen(self) -> None:
		self.gui.regen_single_id = self.playlist_id
		self.thread_manager.ready("worker")

	def _sync_code(self) -> None:
		"""Store the code and regenerate when it has changed."""
		code = self.code_box.text
		if code == self.last_code:
			return
		self.last_code = code
		self.pctl.gen_codes[self.playlist_id] = code
		self._request_regen()

	def add_token(self, token: str, edit: bool) -> None:
		tokens = self._tokens()
		# New steps go after the last step, ahead of any trailing options
		at = len(tokens)
		while at > 0 and gen.is_option(gen.parse_step(tokens[at - 1])):
			at -= 1
		tokens.insert(at, token)
		self._set_tokens(tokens)
		self._close_editor()
		if edit:
			self._open_editor(at, tokens[at])

	def add_to_lane(self, lane: str | None, token: str, edit: bool) -> None:
		"""Add a step to the end of its lane, or to the end when the code isn't in lane order."""
		tokens = self._tokens()
		steps = [gen.parse_step(t) for t in tokens]
		lanes = gen.split_lanes(steps) if lane else None
		if lanes is None:
			self.add_token(token, edit)
			return
		lane_tokens = {name: [tokens[i] for i in indices] for name, indices in lanes.items()}
		options = [t for t, step in zip(tokens, steps, strict=True) if gen.is_option(step)]
		take = lane_tokens[gen.TAKE]
		# A specific take replaces All tracks on its own, which would include everything anyway
		if lane == gen.TAKE and take == [ALL_TRACKS] and token != ALL_TRACKS:
			take.clear()
		lane_tokens[lane].append(token)
		tokens = gen.arrange(lane_tokens, options)
		if lane == gen.FROM:
			at = len(lane_tokens[gen.FROM]) - 1
		elif lane == gen.TAKE:
			at = len(lane_tokens[gen.FROM]) + len(lane_tokens[gen.TAKE]) - 1
		else:
			at = len(tokens) - len(options) - 1
		self._set_tokens(tokens)
		self._close_editor()
		if edit:
			self._open_editor(at, tokens[at])

	def remove_token(self, index: int) -> None:
		tokens = self._tokens()
		if 0 <= index < len(tokens):
			del tokens[index]
			steps = [gen.parse_step(t) for t in tokens]
			lanes = gen.split_lanes(steps)
			if lanes is not None:
				# Keep All tracks when the last take step goes but other steps remain
				options = [t for t, step in zip(tokens, steps, strict=True) if gen.is_option(step)]
				tokens = gen.arrange({name: [tokens[i] for i in indices] for name, indices in lanes.items()}, options)
			self._set_tokens(tokens)
		self._close_editor()

	def move_token(self, source: int, target: int) -> None:
		tokens = self._tokens()
		if not 0 <= source < len(tokens):
			return
		token = tokens.pop(source)
		if target > source:
			target -= 1
		tokens.insert(max(0, min(target, len(tokens))), token)
		self._set_tokens(tokens)

	def toggle_auto(self) -> None:
		tokens = self._tokens()
		if "auto" in tokens:
			tokens = [t for t in tokens if t != "auto"]
		else:
			tokens.append("auto")
		self._set_tokens(tokens)

	def apply_preset(self, preset: gen.Preset) -> None:
		self._close_editor()
		self._set_code(preset.code)
		name = self.name_box.text.strip()
		if not name or name == self.last_preset_name or name.startswith(_("New Playlist")):
			self.name_box.set_text(preset.name())
			self.last_preset_name = preset.name()

	# Step editor ---------------------------------------------------------------

	def _open_editor(self, index: int, token: str) -> None:
		step = gen.parse_step(token)
		self.editing = index
		self.edit_step = step
		self.edit_op = step.values.get("op", step.kind.ops[0] if step.kind and step.kind.ops else "")
		if step.kind is None:
			text = token
		elif step.kind.edit in ("number", "date"):
			text = step.values.get("n", "")
		else:
			text = step.values.get("v", "")
		self.value_box.set_text(text)
		self.edit_initial = text
		self.value_box.highlight_all()
		self.focus = "value"

	def _close_editor(self) -> None:
		if self.editing is not None:
			self.editing = None
			self.edit_step = None
			self.focus = "code"

	def _apply_edit(self, **changes: str) -> None:
		"""Replace the edited step's token with one rebuilt from the editor."""
		if self.editing is None or self.edit_step is None:
			return
		tokens = self._tokens()
		if not 0 <= self.editing < len(tokens):
			self._close_editor()
			return
		if self.edit_step.kind is None:
			token = changes.get("token", tokens[self.editing]).strip()
			if not token:
				return
		else:
			# Keep earlier edits, such as a picked direction, as other fields change
			self.edit_step.values.update(changes)
			token = self.edit_step.rebuilt()
		if token != tokens[self.editing]:
			tokens[self.editing] = token
			self._set_tokens(tokens)

	def _suggestions(self, edit: str, query: str) -> list[str]:
		if edit == "playlist":
			pool = [p.title for p in self.pctl.multi_playlist if p.uuid_int != self.playlist_id]
		elif edit == "column":
			pool = list(self.tauon.column_names)
		else:
			pool = self.suggestion_pools.get(edit)
			if pool is None:
				names: set[str] = set()
				for track in self.pctl.master_library.values():
					if edit == "artist":
						names.add(track.artist)
						names.add(track.album_artist)
					elif edit == "genre":
						names.add(track.genre)
				names.discard("")
				pool = sorted(names, key=str.lower)
				self.suggestion_pools[edit] = pool
		query = query.lower()
		if not query:
			return pool[:PICK_LIMIT] if edit in ("playlist", "column") else []
		starts = [name for name in pool if name.lower().startswith(query) and name.lower() != query]
		contains = [name for name in pool if query in name.lower() and not name.lower().startswith(query)]
		return (starts + contains)[:SUGGESTION_LIMIT]

	# Menus ---------------------------------------------------------------------

	def _own_menus(self) -> list[Menu]:
		menus = list(self.add_menus.values())
		if self.preset_menu is not None:
			menus.append(self.preset_menu)
		return menus

	def _menus_open(self) -> bool:
		return any(menu.active for menu in self._own_menus())

	def _close_menus(self) -> None:
		from tauon.t_modules.t_main import Menu  # noqa: PLC0415

		for menu in self._own_menus():
			menu.active = False
		Menu.active = any(menu.active for menu in Menu.instances)

	def _show_menu(self, menu: Menu, x: int, y: int) -> None:
		menu.rescale()
		menu.update_widths()
		width, height = menu.popup_size()
		x = max(0, min(x, self.window_size[0] - width))
		y = max(0, min(y, self.window_size[1] - height))
		menu.activate(position=[x, y])

	def open_add_menu(self, lane: str | None, x: int, y: int) -> None:
		"""Open the add menu for a lane, or the full menu when lane is None."""
		from tauon.t_modules.t_main import Menu, MenuItem  # noqa: PLC0415

		key = lane or "all"
		menu = self.add_menus.get(key)
		if menu is None:
			entries = {gen.FROM: gen.FROM_MENU, gen.TAKE: gen.TAKE_MENU, gen.THEN: gen.THEN_MENU}.get(key, gen.ADD_MENU)
			menu = Menu(self.tauon, 215)
			for entry in entries:
				if entry is None:
					menu.br()
				elif isinstance(entry, gen.AddGroup):
					menu.add_sub(entry.label(), 215)
					sub = menu.sub_number - 1
					for item in entry.items:
						if item is not None:
							menu.add_to_sub(sub, self._add_menu_item(MenuItem, lane, item))
				else:
					menu.add(self._add_menu_item(MenuItem, lane, entry))
			self.add_menus[key] = menu
		self._show_menu(menu, x, y)

	def _add_menu_item(self, menu_item: type, lane: str | None, item: gen.AddItem) -> object:
		hint = item.token.rstrip("0123456789") if item.edit else item.token
		return menu_item(item.label(), partial(self.add_to_lane, lane, item.token, item.edit), hint=hint)

	def open_preset_menu(self, x: int, y: int) -> None:
		from tauon.t_modules.t_main import Menu, MenuItem  # noqa: PLC0415

		if self.preset_menu is None:
			self.preset_menu = Menu(self.tauon, 170)
			for preset in gen.PRESETS:
				if preset is None:
					self.preset_menu.br()
				else:
					self.preset_menu.add(MenuItem(preset.name(), partial(self.apply_preset, preset)))
		menu = self.preset_menu
		menu.rescale()
		menu.update_widths()
		width, _height = menu.popup_size()
		self._show_menu(menu, x - width, y)

	# Layout helpers --------------------------------------------------------------

	def _chip_size(self, step: gen.Step, max_w: int) -> tuple[int, int, int]:
		"""Chip width, and the widths available for its key and value text."""
		scale = self.gui.scale
		key_w = self.ddt.get_text_w(step.key, 12) + round(6 * scale) if step.key else 0
		value_w = self.ddt.get_text_w(step.value or "…", 12)
		fixed = round(10 * scale) + round(22 * scale)
		value_w = max(round(20 * scale), min(value_w, max_w - fixed - key_w))
		return fixed + key_w + value_w, key_w, value_w

	def _layout_chips(
		self, steps: list[tuple[int, gen.Step]], x: int, y: int, width: int, *, separator: str, add_label: str,
	) -> tuple[list[tuple[int, gen.Step, tuple[int, int, int, int], int, int]], tuple[int, int, int, int], int]:
		"""Place chips in wrapping rows. Returns chips with rects, the add button rect and the total height."""
		scale = self.gui.scale
		h = round(26 * scale)
		separator_w = self.ddt.get_text_w(separator, 12) + round(10 * scale)
		gap_y = round(6 * scale)
		cx, cy = x, y
		chips = []
		for n, (index, step) in enumerate(steps):
			w, key_w, value_w = self._chip_size(step, width)
			lead = separator_w if n else 0
			if cx + lead + w > x + width and cx > x:
				cx = x
				cy += h + gap_y
			cx += lead
			chips.append((index, step, (cx, cy, w, h), key_w, value_w))
			cx += w
		add_w = self.ddt.get_text_w(add_label, 12) + round(20 * scale)
		lead = round(8 * scale) if chips else 0
		if cx + lead + add_w > x + width and cx > x:
			cx = x
			cy += h + gap_y
			lead = 0
		add_rect = (cx + lead, cy, add_w, h)
		return chips, add_rect, cy + h - y

	def _layout_lanes(self, all_steps: list[gen.Step], steps: list[tuple[int, gen.Step]], width: int) -> list[dict]:
		"""Lay out the From, Take and Then lanes, or a single list when the code isn't in lane order.

		Chip and add button rects are relative to the inside of the step area.
		"""
		scale = self.gui.scale
		split = gen.split_lanes(all_steps)
		if split is None:
			chips, add, h = self._layout_chips(steps, 0, 0, width, separator="›", add_label=_("+ Add step"))  # noqa: RUF001
			return [{"name": None, "label": "", "separator": "›", "add_label": _("+ Add step"),  # noqa: RUF001
				"chips": chips, "add": add, "y": 0, "h": h}]

		specs = (
			(gen.FROM, _("From"), "", _("All playlists")),
			(gen.TAKE, _("Take"), "+", _("All tracks")),
			(gen.THEN, _("Then"), "›", _("+ Filter, sort or limit")),  # noqa: RUF001
		)
		label_w = max(self.ddt.get_text_w(label, 11) for _name, label, _sep, _empty in specs) + round(16 * scale)
		lanes = []
		y = 0
		for name, label, separator, empty_label in specs:
			lane_steps = [(i, all_steps[i]) for i in split[name]]
			# An empty lane's button shows the default it falls back to
			add_label = "+" if lane_steps else empty_label
			chips, add, h = self._layout_chips(
				lane_steps, label_w, y, width - label_w, separator=separator, add_label=add_label)
			lanes.append({"name": name, "label": label, "separator": separator, "add_label": add_label,
				"chips": chips, "add": add, "y": y, "h": h})
			y += h + round(14 * scale)
		return lanes

	def _status(self, steps: list[gen.Step], open_quote: bool, pl: int) -> tuple[str, ColourRGBA]:
		code = self.code_box.text.strip()
		if open_quote:
			return _("Close the quotation mark…"), self.label_colour
		message = gen.problem([s for s in steps if not gen.is_option(s)])
		if message:
			unknown = any(not s.known for s in steps)
			return message, UNKNOWN_COLOUR if unknown else WARN_COLOUR
		if not code:
			return _("Disabled. This is a normal playlist."), self.label_colour
		errors = self.gui.gen_code_errors
		if errors == "playlist":
			return _("Playlist not found"), UNKNOWN_COLOUR
		if errors == "empty":
			return _("No tracks match"), WARN_COLOUR
		if errors:
			return _("Some codes could not run"), UNKNOWN_COLOUR
		count = len(self.pctl.multi_playlist[pl].playlist_ids)
		ready = _("Ready. {N} track in playlist") if count == 1 else _("Ready. {N} tracks in playlist")
		return ready.format(N=f"{count:,}"), OK_COLOUR

	def _track_summary(self, pl: int) -> str:
		if self.gui.gen_code_errors == "empty":
			return _("No tracks")
		ids = self.pctl.multi_playlist[pl].playlist_ids
		key = (id(ids), len(ids), self.last_code)
		if key != self.duration_key and not self.pctl.regen_in_progress:
			self.duration_key = key
			self.duration = sum(self.pctl.master_library[i].length for i in ids if i in self.pctl.master_library)
		minutes = round(self.duration / 60)
		count = _("{N} track") if len(ids) == 1 else _("{N} tracks")
		return count.format(N=f"{len(ids):,}") + " · " + _("{H} h {M} m").format(H=minutes // 60, M=minutes % 60)

	# Drawing pieces -------------------------------------------------------------

	def _label(self, x: int, y: int, text: str, max_w: int = 4000) -> None:
		self.ddt.text((x, y), text, self.label_colour, 11, max_w=max_w, bg=self.colours.box_background)

	def _field(self, box: object, rect: tuple[int, int, int, int], name: str, click: bool) -> None:
		scale = self.gui.scale
		border = self.colours.box_text_border
		if self.focus == name:
			border = alpha_blend(ColourRGBA(255, 255, 255, 40), self.colours.box_text_border)
		self.ddt.bordered_rect(rect, self.colours.box_background, border, max(1, round(scale)))
		self.fields.add(rect)
		if click and self.coll(rect):
			self.focus = name
			if name != "value":
				self._close_editor()
		cursor = self.gui.cursor_want
		box.draw(
			rect[0] + round(4 * scale), rect[1] + round(4 * scale), self.input_colour,
			active=self.input_enabled and self.focus == name,
			width=rect[2] - round(8 * scale),
			click=click and self.coll(rect),
		)
		# No text cursor when a menu or the step editor covers the field
		covered = name != "value" and self.editing is not None and self.coll(self.edit_rect)
		if not self.input_enabled or covered:
			self.gui.cursor_want = cursor

	def _draw_chip(
		self, step: gen.Step, rect: tuple[int, int, int, int], key_w: int, value_w: int, *,
		editing: bool, lifted: bool = False,
	) -> bool:
		"""Draw a chip. Returns whether the mouse is over its remove button."""
		scale = self.gui.scale
		hover = self.coll(rect) and not self.dragging
		fill = self.colours.box_button_background_highlight if hover or editing or lifted else self.colours.box_button_background
		stripe = CATEGORY_COLOURS.get(step.category, UNKNOWN_COLOUR)
		key_colour = self.label_colour
		if not step.known:
			fill = alpha_blend(ColourRGBA(224, 85, 85, 45 if hover or editing else 30), self.colours.box_background)
			key_colour = self.readable_colour(ColourRGBA(230, 140, 140, 255), fill)
		border = alpha_blend(ColourRGBA(255, 255, 255, 70), self.colours.box_background) if lifted else self.colours.box_text_border
		self.ddt.bordered_rect(rect, fill, border, max(1, round(scale)))
		self.ddt.rect((rect[0], rect[1], round(3 * scale), rect[3]), stripe)
		self.fields.add(rect)
		tx = rect[0] + round(10 * scale)
		ty = rect[1] + round(5 * scale)
		if step.key:
			self.ddt.text((tx, ty), step.key, key_colour, 12, bg=fill)
		value_colour = self.input_colour if step.value and not step.incomplete else self.label_colour
		self.ddt.text((tx + key_w, ty), step.value if not step.incomplete else "…", value_colour, 12, max_w=value_w, bg=fill)
		remove_rect = (rect[0] + rect[2] - round(20 * scale), rect[1] + round(4 * scale), round(17 * scale), rect[3] - round(8 * scale))
		over_remove = hover and self.coll(remove_rect)
		if hover or editing:
			colour = self.input_colour if over_remove else self.label_colour
			self.ddt.text((remove_rect[0] + remove_rect[2] // 2, ty - round(1 * scale), 2), "×", colour, 13, bg=fill)  # noqa: RUF001
		return over_remove

	def _segmented(self, x: int, y: int, labels: list[tuple[str, str]], selected: str, h: int, *, click: bool, w: int = 0) -> str | None:
		"""A row of joined toggle buttons. Returns the value clicked."""
		scale = self.gui.scale
		chosen = None
		for value, label in labels:
			bw = w or max(round(30 * scale), self.ddt.get_text_w(label, 12) + round(16 * scale))
			rect = (x, y, bw, h)
			self.fields.add(rect)
			on = value == selected
			fill = self.colours.box_button_background_highlight if on or self.coll(rect) else self.colours.box_button_background
			border = alpha_blend(ColourRGBA(255, 255, 255, 50), self.colours.box_background) if on else self.colours.box_text_border
			self.ddt.bordered_rect(rect, fill, border, max(1, round(scale)))
			colour = self.title_colour if on else self.label_colour
			self.ddt.text((x + bw // 2, y + h // 2 - round(8 * scale), 2), label, colour, 12, bg=fill)
			if click and self.coll(rect):
				chosen = value
			x += bw + round(1 * scale)
		return chosen

	def _editor_height(self, step: gen.Step, suggestions: int) -> int:
		scale = self.gui.scale
		h = round(10 * scale) + round(18 * scale)
		edit = step.kind.edit if step.kind else "text"
		if edit in ("text", "artist", "genre", "playlist", "column", "number", "date"):
			h += round(23 * scale)
			if suggestions:
				h += round(4 * scale) + suggestions * round(20 * scale)
			if edit == "column":
				h += round(6 * scale) + round(23 * scale)
			if edit in ("number", "date") and step.kind and step.kind.unit:
				h += round(18 * scale)
			if edit == "playlist":
				h += round(18 * scale)
		elif edit == "direction":
			h += round(23 * scale)
		else:
			h += round(16 * scale)
		if step.kind is None:
			h += round(18 * scale)
		return h + round(10 * scale)

	def _draw_editor(self, anchor: tuple[int, int, int, int], click: bool) -> None:
		step = self.edit_step
		if step is None:
			return
		scale = self.gui.scale
		edit = step.kind.edit if step.kind else "text"
		suggestions: list[str] = []
		if step.kind and edit in ("artist", "genre", "playlist", "column"):
			query = self.value_box.text
			# Pick lists show every choice until something is typed
			if edit in ("playlist", "column") and query == self.edit_initial:
				query = ""
			suggestions = self._suggestions(edit, query)
		w = round(290 * scale)
		h = self._editor_height(step, len(suggestions))
		x = max(round(8 * scale), min(anchor[0], self.window_size[0] - w - round(8 * scale)))
		y = anchor[1] + anchor[3] + round(4 * scale)
		if y + h > self.window_size[1] - round(8 * scale):
			y = max(0, anchor[1] - h - round(4 * scale))
		self.edit_rect = (x, y, w, h)
		bg = self.colours.box_background
		self.ddt.bordered_rect(self.edit_rect, bg, self.colours.box_border, max(1, round(scale)))
		self.fields.add(self.edit_rect)

		pad = round(10 * scale)
		ix, iy, iw = x + pad, y + pad, w - pad * 2
		title = step.key if step.kind else _("Unknown code")
		title_colour = self.label_colour if step.kind else UNKNOWN_COLOUR
		self.ddt.text((ix, iy), title, title_colour, 11, max_w=iw, bg=bg)
		iy += round(18 * scale)
		field_h = round(23 * scale)

		if step.kind is None:
			self._field(self.value_box, (ix, iy, iw, field_h), "value", click)
			self._apply_edit(token=self.value_box.text)
			iy += field_h + round(6 * scale)
			self.ddt.text((ix, iy), _("Kept as written. Fix it here or remove it."), self.label_colour, 11, max_w=iw, bg=bg)
			return

		if edit in ("text", "artist", "genre", "playlist", "column"):
			self._field(self.value_box, (ix, iy, iw, field_h), "value", click)
			self._apply_edit(v=gen.clean_text(self.value_box.text))
			iy += field_h + round(4 * scale)
			if edit == "column" and self._direction_buttons(step, ix, iy + round(2 * scale), iw, field_h, click):
				return
			if edit == "column":
				iy += field_h + round(6 * scale)
			for name in suggestions:
				rect = (ix, iy, iw, round(20 * scale))
				self.fields.add(rect)
				hover = self.coll(rect)
				fill = self.colours.box_button_background_highlight if hover else bg
				if hover:
					self.ddt.rect(rect, fill)
				self.ddt.text((ix + round(6 * scale), iy + round(3 * scale)), name, self.input_colour if hover else self.label_colour, 12, max_w=iw - round(12 * scale), bg=fill)
				if click and hover:
					self.value_box.set_text(name)
					self._apply_edit(v=gen.clean_text(name))
					self._close_editor()
					return
				iy += round(20 * scale)
			if edit == "playlist":
				self.ddt.text((ix, iy + round(2 * scale)), _("Renaming that playlist updates this."), self.label_colour, 11, max_w=iw, bg=bg)

		elif edit in ("number", "date"):
			ops = [(op, op) for op in step.kind.ops]
			seg_w = 0
			if ops:
				for _op, label in ops:
					seg_w += max(round(30 * scale), self.ddt.get_text_w(label, 12) + round(16 * scale)) + round(1 * scale)
				picked = self._segmented(ix, iy, ops, self.edit_op, field_h, click=click)
				if picked is not None:
					self.edit_op = picked
					self.focus = "value"
				seg_w += round(5 * scale)
			self._field(self.value_box, (ix + seg_w, iy, iw - seg_w, field_h), "value", click)
			values = {"n": self.value_box.text.strip()}
			if ops:
				values["op"] = self.edit_op
			self._apply_edit(**values)
			if step.kind.unit:
				self.ddt.text((ix, iy + field_h + round(5 * scale)), step.kind.unit(), self.label_colour, 11, max_w=iw, bg=bg)

		elif edit == "direction" and step.kind.directions:
			self._direction_buttons(step, ix, iy, iw, field_h, click)

		else:
			self.ddt.text((ix, iy), _("No settings. Drag the step to move it."), self.label_colour, 11, max_w=iw, bg=bg)

	def _direction_buttons(self, step: gen.Step, x: int, y: int, w: int, h: int, click: bool) -> bool:  # noqa: PLR0917
		"""Draw the two sort direction buttons. Returns whether one was clicked."""
		if not step.kind or not step.kind.directions:
			return False
		tokens = self._tokens()
		current = tokens[self.editing] if self.editing is not None and self.editing < len(tokens) else ""
		current_dir = gen.parse_step(current).values.get("dir", step.values.get("dir", ">"))
		labels = [(">", step.kind.directions[0]()), ("<", step.kind.directions[1]())]
		half = (w - round(1 * self.gui.scale)) // 2
		picked = self._segmented(x, y, labels, current_dir, h, click=click, w=half)
		if picked is None:
			return False
		self._apply_edit(dir=picked)
		return True

	def _button(  # noqa: PLR0917
		self, text: str, x: int, y: int, w: int, h: int, press: bool, *,
		fill: ColourRGBA | None = None, fill_highlight: ColourRGBA | None = None, ink: ColourRGBA | None = None,
		tooltip: str = "",
	) -> bool:
		"""A box button that shows no hover while a menu or the step editor is open."""
		fill = fill or self.colours.box_button_background
		ink = ink or self.colours.box_button_text
		blocked = self._menus_open() or self.editing is not None
		if blocked:
			return self.draw.button(
				text, x, y, w=w, h=h, press=False, background_colour=fill, background_highlight_colour=fill,
				text_colour=ink, text_highlight_colour=ink)
		return self.draw.button(
			text, x, y, w=w, h=h, press=press, background_colour=fill,
			background_highlight_colour=fill_highlight or self.colours.box_button_background_highlight,
			text_colour=ink, tooltip=tooltip)

	def _checkbox(self, x: int, y: int, *, on: bool, title: str, subtitle: str, width: int, click: bool) -> bool:
		"""Draw a checkbox row. Returns whether it was clicked."""
		scale = self.gui.scale
		bg = self.colours.box_background
		size = round(14 * scale)
		self.ddt.bordered_rect((x, y + round(2 * scale), size, size), self.colours.box_button_background, self.colours.box_check_border, max(1, round(scale)))
		if on:
			inner = round(4 * scale)
			self.ddt.rect((x + inner, y + round(2 * scale) + inner, size - inner * 2, size - inner * 2), self.colours.toggle_box_on)
		tx = x + size + round(10 * scale)
		self.ddt.text((tx, y), title, self.input_colour, 13, max_w=width - (tx - x), bg=bg)
		self.ddt.text((tx, y + round(18 * scale)), subtitle, self.label_colour, 11, max_w=width - (tx - x), bg=bg)
		rect = (x - round(4 * scale), y - round(2 * scale), width, round(36 * scale))
		self.fields.add(rect)
		return click and self.coll(rect)

	def _auto_hint(self, on: bool, tokens: list[str]) -> str:
		if on:
			return _("Regenerates on playlist entry and after importing music.")
		if not self.prefs.always_auto_update_playlists:
			return _("Off. Use Regenerate to update it.")
		if any(gen.parse_step(t).kind and gen.parse_step(t).kind.id in ("shuffle", "shuffle_albums") for t in tokens):
			return _("Off. Shuffled playlists don't update unless this is ticked.")
		return _("Following the global setting: updates on entry and after imports.")

	def capture_wheel(self) -> None:
		"""Keep the wheel from scrolling things behind the box."""
		if self.active:
			self.inp.mouse_wheel = 0
			self.inp.mouse_wheel_precise = False

	# Frame ------------------------------------------------------------------------

	def render(self) -> None:
		if not self.active:
			return
		pl = self.pctl.id_to_pl(self.playlist_id)
		if pl is None:
			self._close()
			return

		inp = self.inp
		gui = self.gui
		scale = gui.scale
		colours = self.colours
		bg = colours.box_background
		gui.box_over = True

		message_open = gui.message_box
		if not message_open:
			if gui.level_2_click:
				inp.mouse_click = True
			gui.level_2_click = False
		menus_open = self._menus_open()
		self.input_enabled = not message_open and not menus_open
		click = self.input_enabled and inp.mouse_click

		self.label_colour = self.readable_colour(colours.box_text_label, bg)
		self.input_colour = self.readable_colour(colours.box_input_text, bg)
		self.title_colour = self.readable_colour(colours.box_title_text, bg, 5.4)

		# Keys
		if inp.key_esc_press and not message_open:
			inp.key_esc_press = False
			if menus_open:
				self._close_menus()
			elif self.editing is not None:
				self._close_editor()
			else:
				self.cancel()
				return
		if self.input_enabled and inp.key_return_press:
			inp.key_return_press = False
			if self.editing is not None:
				self._close_editor()
			else:
				self.done()
				return
		if self.input_enabled and inp.key_tab_press:
			inp.key_tab_press = False
			self._close_editor()
			self.focus = "code" if self.focus == "name" else "name"

		tokens, open_quote = gen.tokenize(self.code_box.text)
		all_steps = [gen.parse_step(t) for t in tokens]
		steps = [(i, s) for i, s in enumerate(all_steps) if not gen.is_option(s)]
		auto_on = any(gen.is_option(s) for s in all_steps)

		# Layout
		w = min(round(680 * scale), self.window_size[0] - round(24 * scale))
		pad = round(16 * scale)
		inner_w = w - pad * 2
		area_pad = round(8 * scale)
		lanes = self._layout_lanes(all_steps, steps, inner_w - area_pad * 2)
		chips = [chip for lane in lanes for chip in lane["chips"]]
		area_h = max(lanes[-1]["y"] + lanes[-1]["h"], round(58 * scale)) + area_pad * 2

		h = (pad + round(22 * scale)  # title
			+ round(14 * scale) + round(16 * scale) + round(23 * scale)  # name
			+ round(14 * scale) + round(16 * scale) + area_h  # steps
			+ round(14 * scale) + round(16 * scale) + round(23 * scale)  # code
			+ round(16 * scale) + round(36 * scale)  # option
			+ round(14 * scale) + round(28 * scale) + pad)  # footer
		x = (self.window_size[0] - w) // 2
		y = max(gui.panelY, (self.window_size[1] - h) // 2)
		box_rect = (x, y, w, h)

		# A click outside the step editor only closes it, though it can still pick another chip.
		# A click outside the box finishes editing.
		dismiss_click = False
		dismissed = None
		if click and self.editing is not None and not self.coll(self.edit_rect):
			dismissed = self.editing
			self._close_editor()
			dismiss_click = True
			click = False
			inp.mouse_click = False
		if click and self.editing is None and not self.coll(box_rect):
			inp.mouse_click = False
			self.done()
			return
		editor_click = click and self.editing is not None and self.coll(self.edit_rect)
		under_click = click and not editor_click

		self.ddt.bordered_rect(box_rect, bg, colours.box_border, max(1, round(scale)))
		self.ddt.text_background_colour = bg
		self.fields.add(box_rect)
		cx = x + pad
		cy = y + pad

		# Title and result
		self.ddt.text((cx, cy), _("Smart playlist"), self.title_colour, 215, bg=bg)
		if self.code_box.text.strip():
			self.ddt.text((cx + inner_w, cy + round(2 * scale), 1), self._track_summary(pl), self.label_colour, 11, max_w=inner_w // 2, bg=bg)
		cy += round(22 * scale) + round(14 * scale)

		# Name and presets
		self._label(cx, cy, _("Playlist name"))
		cy += round(16 * scale)
		preset_w = max(round(90 * scale), self.ddt.get_text_w(_("Presets"), 212) + round(40 * scale))
		preset_open = self.preset_menu is not None and self.preset_menu.active
		if self.draw.dropdown(
			_("Presets"), cx + inner_w - preset_w, cy, w=preset_w, h=round(23 * scale),
			expanded=preset_open, enabled=self.input_enabled or preset_open, dim=False, press=under_click,
		):
			self.open_preset_menu(cx + inner_w, cy + round(26 * scale))
			inp.mouse_click = False
			under_click = False
		self._field(self.name_box, (cx, cy, inner_w - preset_w - round(8 * scale), round(23 * scale)), "name", under_click)
		cy += round(23 * scale) + round(14 * scale)

		# Steps
		if len(lanes) > 1:
			self._label(cx, cy, _("Click a step to edit it. Drag to reorder."), inner_w)
		else:
			self._label(cx, cy, _("This generator has several stages, so it's shown as one list."), inner_w)
		cy += round(16 * scale)
		area = (cx, cy, inner_w, area_h)
		self.ddt.bordered_rect(area, bg, colours.box_text_border, max(1, round(scale)))
		ox, oy = cx + area_pad, cy + area_pad

		# Dragging stays within the pressed chip's lane
		drag_chips = next(
			(lane["chips"] for lane in lanes if any(chip[0] == self.press_index for chip in lane["chips"])), chips)
		self._handle_drag(drag_chips, ox, oy)
		drop = self._drop_index(drag_chips, ox, oy) if self.dragging else None
		marker = self._drop_marker(drag_chips, drop, ox, oy) if drop is not None else None

		editing_rect = None
		dragged = None
		faint = alpha_blend(ColourRGBA(255, 255, 255, 60), bg)
		for number, lane in enumerate(lanes):
			if number:
				line_y = oy + lane["y"] - round(7 * scale)
				self.ddt.rect((cx + 1, line_y, inner_w - 2, max(1, round(scale))), colours.box_text_border)
			if lane["label"]:
				self.ddt.text((ox, oy + lane["y"] + round(6 * scale)), lane["label"], self.label_colour, 11, bg=bg)
			for n, (index, step, rect, key_w, value_w) in enumerate(lane["chips"]):
				rect = (rect[0] + ox, rect[1] + oy, rect[2], rect[3])
				if n:
					separator_w = self.ddt.get_text_w(lane["separator"], 12) + round(10 * scale)
					self.ddt.text(
						(rect[0] - separator_w // 2, rect[1] + round(5 * scale), 2), lane["separator"], faint, 12, bg=bg)
				if index == self.editing:
					editing_rect = rect
				if self.dragging and index == self.press_index:
					# Leave an outline where the chip came from; the chip itself follows the pointer
					self.ddt.bordered_rect(rect, bg, colours.box_text_border, max(1, round(scale)))
					dragged = (step, rect, key_w, value_w)
				else:
					over_remove = self._draw_chip(step, rect, key_w, value_w, editing=index == self.editing)
					chip_click = under_click or (dismiss_click and index != dismissed)
					if chip_click and self.coll(rect) and self.editing is None:
						if over_remove:
							self.remove_token(index)
							under_click = dismiss_click = False
						else:
							self.press_index = index
							self.press_position = (inp.mouse_position[0], inp.mouse_position[1])
							self.press_offset = (inp.mouse_position[0] - rect[0], inp.mouse_position[1] - rect[1])
							under_click = dismiss_click = False

			add_rect = lane["add"]
			add = (add_rect[0] + ox, add_rect[1] + oy, add_rect[2], add_rect[3])
			menu = self.add_menus.get(lane["name"] or "all")
			add_open = menu is not None and menu.active
			add_hover = (self.coll(add) and self.input_enabled) or add_open
			add_bg = colours.box_button_background if add_hover else bg
			self.fields.add(add)
			self.ddt.bordered_rect(add, add_bg, alpha_blend(ColourRGBA(255, 255, 255, 35), bg), max(1, round(scale)))
			self.ddt.text(
				(add[0] + add[2] // 2, add[1] + round(5 * scale), 2), lane["add_label"],
				self.input_colour if add_hover else self.label_colour, 12, bg=add_bg)
			if under_click and self.coll(add):
				self._close_editor()
				self.open_add_menu(lane["name"], add[0], add[1] + add[3] + round(2 * scale))
				inp.mouse_click = False
				under_click = False
		if marker is not None:
			self.ddt.rect(marker, self.input_colour)
		cy += area_h + round(14 * scale)

		# Code
		self._label(cx, cy, _("Generator code"))
		cy += round(16 * scale)
		self._field(self.code_box, (cx, cy, inner_w, round(23 * scale)), "code", under_click)
		cy += round(23 * scale) + round(16 * scale)

		# Option
		if self._checkbox(
			cx, cy, on=auto_on, title=_("Auto update"), subtitle=self._auto_hint(auto_on, tokens),
			width=inner_w, click=under_click,
		):
			self.toggle_auto()
			under_click = False
		cy += round(36 * scale) + round(14 * scale)

		# Footer
		status, status_colour = self._status(all_steps, open_quote, pl)
		button_h = round(28 * scale)
		done_w = max(round(70 * scale), self.ddt.get_text_w(_("Done"), 212) + round(28 * scale))
		cancel_w = max(round(70 * scale), self.ddt.get_text_w(_("Cancel"), 212) + round(28 * scale))
		bx = cx + inner_w - done_w
		if self._button(
			_("Done"), bx, cy, done_w, button_h, under_click,
			fill=alpha_blend(ColourRGBA(40, 150, 40, 70), bg),
			fill_highlight=alpha_blend(ColourRGBA(40, 150, 40, 110), bg),
		):
			self.done()
			return
		bx -= cancel_w + round(8 * scale)
		if self._button(_("Cancel"), bx, cy, cancel_w, button_h, under_click):
			self.cancel()
			return
		if self.code_box.text.strip() or self.original_code:
			convert = _("Convert to normal playlist")
			convert_w = self.ddt.get_text_w(convert, 212) + round(20 * scale)
			bx -= convert_w + round(8 * scale)
			if self._button(
				convert, bx, cy, convert_w, button_h, under_click,
				fill=bg, ink=self.label_colour,
				tooltip=_("Keep the current tracks and remove the generator"),
			):
				self.convert_to_normal()
				return
		self.ddt.text((cx, cy + round(6 * scale)), status, status_colour, 12, max_w=bx - cx - round(12 * scale), bg=bg)

		# The dragged chip follows the pointer, drawn over everything else
		if dragged is not None:
			step, rect, key_w, value_w = dragged
			ghost = (
				inp.mouse_position[0] - self.press_offset[0], inp.mouse_position[1] - self.press_offset[1],
				rect[2], rect[3])
			self._draw_chip(step, ghost, key_w, value_w, editing=False, lifted=True)

		# Step editor on top
		if self.editing is not None:
			if editing_rect is None:
				self._close_editor()
			else:
				self._draw_editor(editing_rect, editor_click)

		self._sync_code()

	def _handle_drag(self, chips: list, ox: int, oy: int) -> None:
		inp = self.inp
		if self.press_index is None:
			return
		self.gui.request_frame()
		if inp.mouse_down and not self.dragging:
			dx = inp.mouse_position[0] - self.press_position[0]
			dy = inp.mouse_position[1] - self.press_position[1]
			if abs(dx) + abs(dy) > round(6 * self.gui.scale):
				self.dragging = True
				self._close_editor()
		if inp.mouse_down:
			return
		index = self.press_index
		if self.dragging:
			drop = self._drop_index(chips, ox, oy)
			if drop is not None:
				self.move_token(index, self._token_index_for_drop(chips, drop))
		else:
			tokens = self._tokens()
			if index < len(tokens):
				self._open_editor(index, tokens[index])
		self.press_index = None
		self.dragging = False

	def _drop_index(self, chips: list, ox: int, oy: int) -> int | None:
		"""The token index of the chip the dragged chip would land before, or -1 for the end."""
		mx, my = self.inp.mouse_position
		rows: dict[int, list] = {}
		for chip in chips:
			rows.setdefault(chip[2][1], []).append(chip)
		if not rows:
			return None

		# Over another chip: take its place, landing after it when moving right and before it when moving left
		source = self.press_index
		for n, (index, _step, rect, _k, _v) in enumerate(chips):
			if index == source or not self.coll((ox + rect[0], oy + rect[1], rect[2], rect[3])):
				continue
			if source is not None and index > source:
				return chips[n + 1][0] if n + 1 < len(chips) else -1
			return index

		# Between chips: land before the first chip whose centre is right of the pointer
		row_y = min(rows, key=lambda ry: abs(oy + ry + chips[0][2][3] // 2 - my))
		for index, _step, rect, _k, _v in rows[row_y]:
			if mx < ox + rect[0] + rect[2] // 2:
				return index
		later = [chip[0] for chip in chips if chip[2][1] > row_y]
		return later[0] if later else -1

	def _drop_marker(self, chips: list, drop: int, ox: int, oy: int) -> tuple[int, int, int, int] | None:
		"""Where to draw the insertion line, beside the chip the dragged one lands next to."""
		if not chips:
			return None
		scale = self.gui.scale
		w = max(2, round(2 * scale))
		position = next((n for n, chip in enumerate(chips) if chip[0] == drop), len(chips))
		if position < len(chips) and (position == 0 or chips[position][2][1] == chips[position - 1][2][1]):
			rect = chips[position][2]
			return (ox + rect[0] - round(3 * scale) - w // 2, oy + rect[1], w, rect[3])
		rect = chips[position - 1][2]
		return (ox + rect[0] + rect[2] + round(3 * scale) - w // 2, oy + rect[1], w, rect[3])

	@staticmethod
	def _token_index_for_drop(chips: list, drop: int) -> int:
		if drop != -1:
			return drop
		return chips[-1][0] + 1 if chips else 0
