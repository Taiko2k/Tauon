# Copyright © 2026, Tauon contributors

"""The modal, staged tag editor."""

from __future__ import annotations

import copy
import io
import logging
import threading
from dataclasses import dataclass, replace
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

from tauon.t_modules.t_draw import QuickThumbnail
from tauon.t_modules.t_extra import ColourRGBA, shooter
from tauon.t_modules.t_lookup_cache import LookupCache
from tauon.t_modules.t_musicbrainz_lookup import (
	LOOKUP_LIMIT,
	LookupCancelledError,
	LookupResult,
	MusicBrainzLookup,
	MusicBrainzLookupError,
	stage_album,
)
from tauon.t_modules.t_tagedit import MAIN_FIELDS, VALUE_FIELDS, TagChanges, TagEditSession, TagEntry

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Menu, Tauon, TrackClass

CONTROL_GREY = ColourRGBA(170, 170, 170, 255)


@dataclass(frozen=True)
class LookupComparison:
	before: tuple[str, str, str]
	after: tuple[str, str, str]
	matched: bool
	pending: bool = False


class TransEditBox:
	def __init__(self, tauon: Tauon) -> None:
		from tauon.t_modules.t_main import MultiLineTextBox, TextBox2, readable_text_colour  # noqa: PLC0415
		from tauon.t_modules.t_tag_textbox import TagTextBox  # noqa: PLC0415

		self.tauon = tauon
		self.gui = tauon.gui
		self.inp = tauon.inp
		self.ddt = tauon.ddt
		self.colours = tauon.colours
		self.readable_colour = readable_text_colour
		self.draw = tauon.draw
		self.coll = tauon.coll
		self.fields = tauon.fields
		self.pctl = tauon.pctl
		self.window_size = tauon.window_size
		self.show_message = tauon.show_message
		self.active = False
		self.session: TagEditSession | None = None
		self.tracks = []
		self.boxes = {field: (TagTextBox(tauon) if field in VALUE_FIELDS else TextBox2(tauon)) for field in MAIN_FIELDS}
		self.loading = False
		self.load_cancel = threading.Event()
		self.load_lock = threading.Lock()
		self.load_result: tuple[TagEditSession | None, str | None] | None = None
		self.load_done = 0
		self.load_file = ""
		self.load_thread: threading.Thread | None = None
		self.original: dict[str, str | None] = {}
		self.active_field = 0
		self.main_page = 0
		self.tab = 0
		self.row_page = 0
		self.row_key: str | None = None
		self.row_value_index: int | None = None
		self.row_value_slots: dict[Path, tuple[int, bool]] | None = None
		self.row_focus_new = False
		self.row_original = ""
		self.row_expected = ""
		self.row_box = MultiLineTextBox(tauon)
		self.row_scroll = 0
		self.new_key = TextBox2(tauon)
		self.key_active = False
		self.preview = QuickThumbnail(tauon)
		self.preview_dimensions = (0, 0)
		self.art_rect = (0, 0, 0, 0)
		self.art_count = 0
		self.art_mixed = False
		self.write_result: tuple[int, str | None] | None = None
		self.scope_open = False
		self.tools_menu = None
		self.presets_menu = None
		self.undo_icon = None
		self.scope_page = 0
		self.scope_filter = TextBox2(tauon)
		self.scope_anchor = (0, 0, 0, 0)
		self.notice = ""
		self.input_enabled = True
		self.row_values: list[str] | None = None
		self.row_is_list = False
		self.lookup_cancel = threading.Event()
		self.lookup_lock = threading.Lock()
		self.lookup_cache = LookupCache()
		self.lookup_running = False
		self.lookup_progress = ""
		self.lookup_result: tuple[LookupResult | None, str | None] | None = None
		self.lookup_results: LookupResult | None = None
		self.lookup_update: LookupResult | None = None
		self.lookup_apply_id: str | None = None
		self.lookup_error = ""
		self.lookup_open = False
		self.lookup_fraction = 0.0
		self.lookup_album = 0
		self.lookup_scroll = 0
		self.lookup_dragging = False

	def activate(self) -> None:
		if self.gui.write_tag_in_progress:
			return
		self._cancel_lookup()
		with self.load_lock:
			self.load_cancel.set()
			self.load_result = None
		self.active = False
		self.loading = False
		self.gui.box_over = False
		self.lookup_results = None
		self.lookup_error = ""
		self.lookup_open = False
		self.lookup_album = 0
		self.lookup_scroll = 0
		self.scope_open = False
		self._close_tools()
		self._close_presets()
		self.notice = ""
		positions = sorted(set(self.gui.shift_selection))
		if not positions and self.pctl.selected_ready():
			positions = [self.pctl.selected_in_playlist]
		self.tracks = list(
			{
				track.index: track
				for position in positions
				if 0 <= position < len(self.pctl.default_playlist)
				for track in [self.pctl.get_track(self.pctl.default_playlist[position])]
			}.values()
		)
		if not self.tracks:
			return
		if any(track.is_network or track.is_cue or track.is_embed_cue for track in self.tracks):
			self.show_message(_("Only local audio files without CUE subtracks can be edited."), mode="error")
			return
		self.session = None
		self.loading = True
		self.load_cancel = threading.Event()
		cancel = self.load_cancel
		paths = [track.fullpath for track in self.tracks]
		with self.load_lock:
			self.load_result = None
			self.load_done = 0
			self.load_file = ""
		self.tab = 0
		self.active_field = 0
		self.main_page = 0
		self.row_key = None
		self.row_page = 0
		self.new_key.clear()
		self.key_active = False
		self.active = True
		self.gui.box_over = True
		self.gui.side_drag = False
		self.gui.cursor_want = 0
		self.gui.request_frame()

		def progress(done: int, _total: int, path: Path) -> None:
			with self.load_lock:
				if cancel.is_set() or self.load_cancel is not cancel:
					raise InterruptedError
				self.load_done, self.load_file = done, path.name
			self.gui.request_frame()

		def read_tags() -> None:
			result, error = None, None
			try:
				result = TagEditSession(paths, progress=progress)
			except InterruptedError:
				return
			except Exception as failure:
				logging.exception("Could not read tags for editor")
				error = str(failure)
			with self.load_lock:
				if not cancel.is_set() and self.load_cancel is cancel:
					self.load_result = (result, error)
					self.gui.request_frame()

		self.load_thread = threading.Thread(target=read_tags, name="tauon-tag-read", daemon=True)
		self.load_thread.start()

	def _finish_loading(self) -> None:
		with self.load_lock:
			completed, self.load_result = self.load_result, None
		if completed is None:
			return
		self.session, error = completed
		self.loading = False
		if error is not None:
			self._close()
			self.show_message(_("Cannot open tag editor"), error, mode="error")
			return
		try:
			self._load_fields()
		except Exception as failure:
			logging.exception("Could not prepare tag editor")
			self._close()
			self.show_message(_("Cannot open tag editor"), str(failure), mode="error")

	def _loading_screen(self, x: int, y: int, width: int) -> None:
		scale = self.gui.scale
		with self.load_lock:
			done, filename = self.load_done, self.load_file
		total = len(self.tracks)
		self.ddt.text((x, y), _("Reading tags… {N}/{T}").format(N=done, T=total), self.input_colour, 13, max_w=width)
		self.ddt.text((x, y + round(25 * scale)), filename, self.label_colour, 11, max_w=width)
		bar = (x, y + round(55 * scale), width, round(14 * scale))
		self.ddt.bordered_rect(
			bar, self.colours.box_thumb_background, self.colours.box_text_border, max(1, round(scale))
		)
		inset = round(2 * scale)
		self.ddt.rect(
			(bar[0] + inset, bar[1] + inset, round((width - 2 * inset) * done / max(1, total)), bar[3] - 2 * inset),
			CONTROL_GREY,
		)
		if self.inp.key_esc_press or self.draw.button(
			_("Close"),
			x + width - round(84 * scale),
			self.editor_bottom - round(54 * scale),
			w=round(84 * scale),
			h=round(32 * scale),
		):
			self.inp.key_esc_press = False
			self._close()

	def _scan(self, track: TrackClass) -> TrackClass:
		from tauon.t_modules.t_main import TrackClass  # noqa: PLC0415

		scanned = TrackClass()
		for field in ("fullpath", "filename", "parent_folder_path", "parent_folder_name", "file_ext", "index"):
			setattr(scanned, field, getattr(track, field))
		self.tauon.tag_scan(scanned)
		if not scanned.found:
			raise ValueError(_("Could not read {file}").format(file=track.filename))
		return scanned

	def _load_fields(self) -> None:
		self.original = {field: self.session.common_main(field, False) for field in MAIN_FIELDS}
		self.effective = {field: self.session.common_main(field) for field in MAIN_FIELDS}
		self.value_lists = {field: self.session.common_values(field, main=True) for field in VALUE_FIELDS}
		for field, box in self.boxes.items():
			if field in VALUE_FIELDS:
				box.set_values(self.value_lists[field] or [])
			else:
				box.set_text(self.effective[field] or "")
		self.field_baseline = {field: box.text for field, box in self.boxes.items()}
		self._load_art()

	def _load_art(self) -> None:
		art = [self.session.effective_document(doc).artwork() for doc in self.session.scope_documents]
		self.art_count = len(art[0])
		self.art_mixed = any(value != art[0] for value in art)
		self._preview(art[0][0] if art[0] else None)

	def _preview(self, data: bytes | None) -> None:
		self.preview.destruct()
		self.preview_dimensions = (0, 0)
		if data:
			try:
				size = round(145 * self.gui.scale)
				self.preview.read_and_thumbnail(io.BytesIO(data), size, size)
			except Exception:
				logging.exception("Tag editor operation failed")
				self.show_message(_("Could not preview embedded artwork"), mode="warning")

	def accept_image_drop(self, target: str) -> bool:
		if not self.active:
			return False
		if (
			self.gui.write_tag_in_progress
			or self.lookup_running
			or self.lookup_open
			or self.tab != 0
			or self.loading
			or self.scope_open
			or (self.tools_menu is not None and self.tools_menu.active)
			or (self.presets_menu is not None and self.presets_menu.active)
			or not self.coll(self.art_rect)
		):
			return True
		try:
			with Image.open(Path(target)) as image:
				image.load()
				output = io.BytesIO()
				image.convert("RGBA" if "A" in image.getbands() else "RGB").save(output, "PNG")
			data = output.getvalue()
			self.session.validate({}, {}, True, data)
			self.session.art_changed = True
			self.session.art_data = data
			self._preview(data)
			self.art_count = 1
			self.art_mixed = False
			self.gui.request_frame()
		except Exception as error:
			logging.exception("Tag editor operation failed")
			self.show_message(_("Could not use that artwork"), str(error), mode="error")
		return True

	def _flush_fields(self) -> bool:
		if self.loading or self.session is None:
			return False
		updates = {}
		try:
			for field, box in self.boxes.items():
				if box.text == self.field_baseline[field]:
					continue
				if field in VALUE_FIELDS:
					changes = self.session.value_changes(field, box.values(), main=True)
				else:
					changes = {doc.path: TagChanges(main={field: box.text}) for doc in self.session.scope_documents}
				for path, change in changes.items():
					update = updates.setdefault(path, TagChanges())
					update.main.update(change.main)
					update.entries.update(change.entries)
			if self._row_dirty():
				value = [self.row_box.text] if self.row_box.text else []
				if self.row_is_list:
					for path, change in self.session.value_changes(
						self.row_key, value, slots=self.row_value_slots
					).items():
						updates.setdefault(path, TagChanges()).entries.update(change.entries)
				else:
					for doc in self.session.scope_documents:
						updates.setdefault(doc.path, TagChanges()).entries[self.row_key] = self.row_box.text
			self.session.stage_tracks(updates)
			if self._row_dirty() and self.row_value_slots is not None:
				self.row_value_slots = {
					path: (index, bool(self.row_box.text)) for path, (index, _present) in self.row_value_slots.items()
				}
			if any(
				change.entries and ("artist" in change.main or "albumartist" in change.main)
				for change in updates.values()
			):
				self.notice = _("Artist identifiers and credits cleared after changing names.")
			self.field_baseline = {field: box.text for field, box in self.boxes.items()}
			self.effective = {field: self.session.common_main(field) for field in MAIN_FIELDS}
			self.value_lists = {field: self.session.common_values(field, main=True) for field in VALUE_FIELDS}
			self.row_expected = self.row_box.text
			return True
		except Exception as error:
			logging.exception("Invalid tag editor values")
			self.show_message(_("Invalid tag value"), str(error), mode="error")
			return False

	def _row_dirty(self) -> bool:
		return self.row_key is not None and self.row_box.text != self.row_expected

	def _select_row(self, entry: TagEntry) -> None:
		if (
			self.tab == 1
			and self.row_key == entry.key
			and self._row_dirty()
			and not self.row_box.text
			and self.row_value_index is not None
			and entry.value_index is not None
			and 0 <= self.row_value_index < entry.value_index
		):
			entry = replace(entry, value_index=entry.value_index - 1)
		if not self._flush_fields():
			return
		self._load_row(entry)

	def _load_row(self, entry: TagEntry) -> None:
		self.row_key = entry.key
		self.row_value_index = entry.value_index
		self.row_value_slots = None
		self.row_values = self.session.common_values(entry.key)
		self.row_is_list = entry.kind in ("text", "JSON text values") or entry.lyrics
		self.row_original = entry.value
		if self.row_is_list and all(
			self.session.effective_document(doc).supports_multiple_values(
				self.session.effective_document(doc).portable_key(entry.key)
			)
			for doc in self.session.scope_documents
		):
			self.row_value_index = entry.value_index if entry.value_index is not None else 0
			values = []
			self.row_value_slots = {}
			for original in self.session.scope_documents:
				doc = self.session.effective_document(original)
				items = doc.text_values(doc.portable_key(entry.key)) or []
				index = len(items) if self.row_value_index == -1 else self.row_value_index
				present = index < len(items)
				self.row_value_slots[doc.path] = (min(index, len(items)), present)
				values.append(items[index] if present else "")
			self.row_original = values[0] if all(value == values[0] for value in values) else "<Multiple values>"
			self.row_expected = "" if self.row_original == "<Multiple values>" else self.row_original
			self.row_box.set_text(self.row_expected)
			self.row_scroll = 0
			self.key_active = False
			return
		self.row_expected = (
			(self.row_values[0] if self.row_values else "")
			if self.row_is_list
			else ""
			if entry.value == "<Multiple values>"
			else entry.value
		)
		self.row_box.set_text(self.row_expected)
		self.row_scroll = 0
		self.key_active = False

	def _misc_rows(self, lyrics: bool | None = None) -> list[TagEntry]:
		rows = []
		documents = [self.session.effective_document(doc) for doc in self.session.scope_documents]
		appending = self.row_key is not None and self.row_value_index == -1 and self.row_value_slots is not None
		for entry in self.session.entries(lyrics):
			if (
				not entry.editable
				or entry.kind not in ("text", "JSON text values")
				or any(not doc.supports_multiple_values(doc.portable_key(entry.key)) for doc in documents)
			):
				rows.append(entry)
				continue
			lists = []
			for doc in documents:
				native = doc.portable_key(entry.key)
				items = doc.text_values(native) if native in doc.tags else []
				if items is None:
					break
				if appending and entry.key == self.row_key:
					index, present = self.row_value_slots[doc.path]
					if present:
						del items[index : index + 1]
				lists.append(items)
			else:
				if appending and entry.key == self.row_key and not any(lists):
					continue
				for index in range(max(1, *map(len, lists))):
					values = [items[index] if index < len(items) else "" for items in lists]
					value = values[0] if all(item == values[0] for item in values) else _("Different values")
					rows.append(TagEntry(entry.key, value, entry.kind, lyrics=entry.lyrics, value_index=index))
				continue
			rows.append(entry)
		if appending:
			is_lyric = documents[0].is_lyric_key(documents[0].portable_key(self.row_key))
			rows.append(TagEntry(self.row_key, self.row_box.text or _("New value"), lyrics=is_lyric, value_index=-1))
			rows.sort(key=lambda row: row.key)
		return rows

	def _add_misc_key(self, key: str) -> None:
		if not self._flush_fields():
			return
		try:
			documents = [self.session.effective_document(doc) for doc in self.session.scope_documents]
			keys = {doc.portable_key(key) for doc in documents}
			is_lyric = documents[0].is_lyric_key(documents[0].portable_key(key))
			entry = next(
				(row for row in self.session.entries(None) if row.key in keys),
				TagEntry(documents[0].portable_key(key), "", lyrics=is_lyric),
			)
			entry = replace(entry, key=documents[0].portable_key(key))
			if not entry.editable or entry.kind not in ("text", "JSON text values"):
				self._load_row(entry)
				self.notice = _("This tag has a structured value; edit it as a whole.")
			elif any(not doc.supports_multiple_values(doc.portable_key(key)) for doc in documents):
				self._load_row(entry)
				self.notice = _("This tag stores one value; use a distinct description or language for another entry.")
			else:
				self._load_row(TagEntry(entry.key, "", lyrics=is_lyric, value_index=-1))
			self.new_key.clear()
			self.row_focus_new = True
			self.gui.request_frame()
		except Exception as error:
			logging.exception("Could not add tag value")
			self.show_message(_("Cannot add tag value"), str(error), mode="error")

	def _field_edited(self, field: str) -> bool:
		box = self.boxes[field]
		if box.text == self.field_baseline[field]:
			return self.session.field_edited(field, main=True)
		if field in VALUE_FIELDS:
			values = box.values()
			return any((doc.text_values(doc.key_for(field)) or []) != values for doc in self.session.scope_documents)
		return any(doc.main_value(field) != box.text for doc in self.session.scope_documents)

	def _entry_edited(self, key: str) -> bool:
		return (self.row_key == key and self._row_dirty()) or self.session.field_edited(key)

	def _changes_pending(self) -> bool:
		return (
			self.session.changed
			or self._row_dirty()
			or any(box.text != self.field_baseline[field] for field, box in self.boxes.items())
		)

	def _rollback_field(self, key: str, *, main: bool = False) -> None:
		self.session.rollback_field(key, main=main)
		if main:
			self.original[key] = self.session.common_main(key, False)
			self.effective[key] = self.session.common_main(key)
			self.field_baseline[key] = self.effective[key] or ""
			if key in VALUE_FIELDS:
				self.value_lists[key] = self.session.common_values(key, main=True)
				self.boxes[key].set_values(self.value_lists[key] or [])
			else:
				self.boxes[key].set_text(self.field_baseline[key])
			self.field_baseline[key] = self.boxes[key].text
		elif self.row_key == key:
			entry = next((row for row in self.session.entries(None) if row.key == key), None)
			if entry is None:
				self.row_key = None
			else:
				self._load_row(entry)
		self.notice = ""
		self.inp.mouse_click = False
		self.gui.request_frame()

	def _rollback_button(self, x: int, y: int, *, enabled: bool | None = None) -> bool:
		from tauon.t_modules.t_main import asset_loader  # noqa: PLC0415

		if self.undo_icon is None:
			self.undo_icon = asset_loader(self.tauon.bag, self.tauon.bag.loaded_asset_dc, "tag-undo.png", True)
		length = round(23 * self.gui.scale)
		colour = self.readable_colour(CONTROL_GREY, self.colours.box_background)
		hit = self.draw.button(
			"",
			x,
			y,
			w=length,
			h=length,
			font=14,
			text_colour=colour,
			press=(self.input_enabled if enabled is None else enabled) and self.inp.mouse_click,
			tooltip=_("Restore each file's original value in the current track scope."),
		)
		self.undo_icon.render(
			x + (length - self.undo_icon.w) / 2,
			y + (length - self.undo_icon.h) / 2,
			colour,
		)
		return hit

	def _edited_outline(self, rect: tuple[int, int, int, int]) -> None:
		x, y, width, height = rect
		border = max(1, round(self.gui.scale))
		for edge in (
			(x - border, y - border, width + 2 * border, border),
			(x - border, y + height, width + 2 * border, border),
			(x - border, y, border, height),
			(x + width, y, border, height),
		):
			self.ddt.rect(edge, self.colours.level_green)

	def write(self) -> None:
		if self.gui.write_tag_in_progress or self.lookup_running:
			return
		if not self._flush_fields():
			return
		if not self.session.changed:
			self.show_message(_("No tag changes to save."), mode="info")
			return
		self.gui.write_tag_in_progress = True
		self.write_result = None
		session = self.session

		def save() -> None:
			try:
				self.write_result = (session.write(), None)
			except Exception as error:
				logging.exception("Tag editor operation failed")
				self.write_result = (0, str(error))
			self.gui.request_frame()

		shooter(save)

	def _finish_write(self) -> None:
		count, error = self.write_result
		self.write_result = None
		self.gui.write_tag_in_progress = False
		if error is not None:
			self.show_message(_("Could not write tags"), error, mode="error")
			return
		try:
			self._refresh_database()
			selected = self.session.selected_document
			self.session = TagEditSession([track.fullpath for track in self.tracks])
			self.session.selected_document = selected
			self.lookup_results = None
			self._load_fields()
			self.row_key = None
		except Exception as error:
			logging.exception("Tag editor operation failed")
			self.active = False
			self.gui.box_over = False
			self.show_message(_("Tags saved, but the library could not be refreshed"), str(error), mode="error")
			return
		self.show_message(_("{N} files rewritten").format(N=count), mode="done")

	def _refresh_database(self) -> None:
		scanned_tracks = [self._scan(track) for track in self.tracks]
		for track, scanned in zip(self.tracks, scanned_tracks, strict=True):
			star = copy.deepcopy(self.tauon.star_store.full_get(track.index))
			self.tauon.star_store.remove(track.index)
			for field in track.__slots__:
				if field not in (
					"lfm_friend_likes",
					"lfm_scrobbles",
					"skips",
					"position",
					"is_network",
					"url_key",
					"art_url_key",
					"subtrack",
					"start_time",
					"is_cue",
					"is_embed_cue",
					"subsonic_folder_id",
					"tidal_album",
				):
					setattr(track, field, getattr(scanned, field))
			if star is not None:
				self.tauon.star_store.merge(track.index, star)
			if "rating" in self.session.pending[Path(track.fullpath).resolve()].main:
				self.tauon.star_store.set_rating(track.index, round((scanned.FMPS_Rating or 0) * 10))
			for cache in (
				self.tauon.search_string_cache,
				self.tauon.search_dia_string_cache,
				self.tauon.search_field_cache,
				self.tauon.search_dia_field_cache,
			):
				cache.pop(track.index, None)
		self.tauon.album_art_gen.clear_cache()
		self.pctl.notify_database_changed()
		self.tauon.bg_save()
		self.gui.request_tracklist_redraw()
		self.gui.album_artist_dict.clear()

	def fix_mojibake(self, encoding: str | None = None) -> None:
		if self.gui.write_tag_in_progress or self.lookup_running or not self._flush_fields():
			return
		try:
			fields, files, undetected = self.session.fix_mojibake(encoding)
			if not fields:
				self.show_message(
					_("Autodetect failed; choose an encoding in Tools.")
					if encoding is None
					else _("No text needed fixing."),
					mode="info",
				)
				return
			self._load_fields()
			self.row_key = None
			self.row_page = 0
			message = _("{N} fields fixed in {F} files; review before writing tags.").format(N=fields, F=files)
			if encoding is None and undetected:
				message += " " + _("Encoding not detected for {N} files.").format(N=undetected)
			self.show_message(message, mode="info")
			self.gui.request_frame()
		except Exception as error:
			logging.exception("Could not fix Mojibake in tag editor")
			self.show_message(_("Could not fix Mojibake"), str(error), mode="error")

	def _close_tools(self) -> None:
		self._close_menu(self.tools_menu)

	def _close_presets(self) -> None:
		self._close_menu(self.presets_menu)

	@staticmethod
	def _close_menu(menu: Menu | None) -> None:
		if menu is None:
			return
		from tauon.t_modules.t_main import Menu  # noqa: PLC0415

		menu.active = False
		Menu.active = any(menu.active for menu in Menu.instances)

	def open_presets(self, x: int, y: int) -> None:
		from tauon.t_modules.t_main import Menu, MenuItem  # noqa: PLC0415

		self._close_tools()
		self.scope_open = False
		if self.presets_menu is None:
			self.presets_menu = Menu(self.tauon, 180)
			for label, field in (
				(_("Unsynced lyrics"), "unsyncedlyrics"),
				(_("Synced lyrics"), "syncedlyrics"),
				(_("Comment"), "comment"),
				(_("BPM"), "bpm"),
				(_("Copyright"), "copyright"),
				(_("ISRC"), "isrc"),
				(_("Language"), "language"),
				(_("Grouping"), "grouping"),
				(_("Subtitle"), "subtitle"),
			):
				self.presets_menu.add(MenuItem(label, partial(self.add_preset, field)))
			for index, (title, fields) in enumerate(
				(
					(
						_("Credits"),
						(
							(_("Original artist"), "originalartist"),
							(_("Conductor"), "conductor"),
							(_("Remixer"), "remixer"),
							(_("Lyricist"), "lyricist"),
							(_("Encoded by"), "encodedby"),
						),
					),
					(
						_("Sort order"),
						(
							(_("Artist"), "artistsort"),
							(_("Album"), "albumsort"),
							(_("Title"), "titlesort"),
						),
					),
				)
			):
				self.presets_menu.add_sub(title, 180)
				for label, field in fields:
					self.presets_menu.add_to_sub(index, MenuItem(label, partial(self.add_preset, field)))
		self._activate_menu(self.presets_menu, x, y)

	def add_preset(self, field: str) -> None:
		self._close_presets()
		doc = self.session.effective_document(self.session.scope_documents[0])
		key = (
			doc.lyric_defaults()[field == "syncedlyrics"]
			if field in ("unsyncedlyrics", "syncedlyrics")
			else doc.key_for(field)
		)
		self._add_misc_key(key)

	def open_tools(self, x: int, y: int) -> None:
		from tauon.t_modules.t_main import Menu, MenuItem  # noqa: PLC0415

		self.scope_open = False
		self._close_presets()
		if self.tools_menu is None:
			self.tools_menu = Menu(self.tauon, 200)
			self.tools_menu.add(MenuItem(_("Upgrade ID3 tags to v2.4"), self.upgrade_id3))
			self.tools_menu.add(MenuItem(_("Fix Mojibake (auto)"), self.fix_mojibake))
		self._activate_menu(self.tools_menu, x, y)

	def _activate_menu(self, menu: Menu, x: int, y: int) -> None:
		if menu.active:
			self._close_menu(menu)
			return
		menu.rescale()
		menu.update_widths()
		width, height = menu.popup_size()
		x = max(0, min(x - width, self.window_size[0] - width))
		y = max(0, min(y, self.window_size[1] - height))
		menu.activate(position=[x, y])

	def upgrade_id3(self) -> None:
		if self.gui.write_tag_in_progress or self.lookup_running:
			return
		try:
			count, skipped = self.session.upgrade_id3()
			if not self._flush_fields():
				return
			self._load_fields()
			self.row_key = None
			self.notice = _("{N} ID3 files will upgrade to v2.4 on Write tags; {S} other formats kept.").format(
				N=count, S=skipped
			)
			self.gui.request_frame()
		except Exception as error:
			logging.exception("Could not upgrade ID3 tags")
			self.show_message(_("Cannot safely upgrade these tags"), str(error), mode="error")

	def select_track(self, index: int | None) -> None:
		if not self._flush_fields():
			return
		self.session.selected_document = index
		self.scope_open = False
		self.row_key = None
		self.row_page = 0
		self._load_fields()

	def _scope_selector(self, x: int, y: int, width: int, _height: int) -> None:
		scale = self.gui.scale
		index = self.session.selected_document
		label = _("All selected files") if index is None else self.session.documents[index].path.name
		rect = (x, y, width, round(28 * scale))
		self.scope_anchor = rect
		self.fields.add(rect)
		self.ddt.bordered_rect(
			rect, self.colours.box_thumb_background, self.colours.box_text_border, max(1, round(scale))
		)
		self.ddt.text(
			(x + round(9 * scale), y + round(4 * scale)), label, self.input_colour, 12, max_w=width - round(36 * scale)
		)
		self.ddt.text((x + width - round(22 * scale), y + round(4 * scale)), "▾", self.label_colour, 12)
		if self.input_enabled and self.inp.mouse_click and self.coll(rect):
			self.scope_open = not self.scope_open
			self.scope_filter.clear()
			self.scope_page = 0
			self.inp.mouse_click = False

	def _scope_popover(self, x: int, y: int, width: int, height: int) -> None:
		scale = self.gui.scale
		ax, ay, aw, ah = self.scope_anchor
		pw = min(width - round(32 * scale), max(aw, round(340 * scale)))
		px = min(ax, x + width - pw - round(16 * scale))
		py = ay + ah + round(4 * scale)
		ph = min(round(330 * scale), y + height - round(56 * scale) - py)
		rect = (px, py, pw, ph)
		if self.inp.mouse_click and not self.coll(rect):
			self.scope_open = False
			self.inp.mouse_click = False
			return
		self.ddt.bordered_rect(rect, self.colours.box_background, self.colours.box_border, max(1, round(scale)))
		self.ddt.text((px + round(12 * scale), py + round(8 * scale)), _("Choose tracks"), self.title_colour, 12)
		filter_rect = (px + round(9 * scale), py + round(29 * scale), pw - round(18 * scale), round(23 * scale))
		self.ddt.bordered_rect(
			filter_rect, self.colours.box_thumb_background, self.colours.box_text_border, max(1, round(scale))
		)
		if not self.scope_filter.text:
			self.ddt.text(
				(px + round(16 * scale), py + round(33 * scale)),
				_("Filter by filename or title"),
				self.label_colour,
				11,
				max_w=pw - round(32 * scale),
			)
		self.scope_filter.draw(
			px + round(12 * scale), py + round(30 * scale), self.input_colour, active=True, width=pw - round(24 * scale)
		)
		query = self.scope_filter.text.casefold()
		options = [(None, _("All selected files"), _("Apply edits to the full selection"))] + [
			(index, doc.path.name, self.session.effective_document(doc).main_value("title") or str(doc.path.parent))
			for index, doc in enumerate(self.session.documents)
			if query in doc.path.name.casefold() or query in doc.main_value("title").casefold()
		]
		page_size = max(1, int((ph / scale - 85) // 44))
		pages = max(1, (len(options) + page_size - 1) // page_size)
		self.scope_page = min(self.scope_page, pages - 1)
		ry = py + round(57 * scale)
		for position, name, subtitle in options[self.scope_page * page_size : (self.scope_page + 1) * page_size]:
			row = (px + round(5 * scale), ry, pw - round(10 * scale), round(43 * scale))
			self.fields.add(row)
			if self.coll(row) or position == self.session.selected_document:
				self.ddt.rect(row, self.colours.box_button_background_highlight)
			self.ddt.text(
				(px + round(12 * scale), ry + round(3 * scale)),
				"✓" if position == self.session.selected_document else "",
				self.input_colour,
				12,
			)
			self.ddt.text(
				(px + round(35 * scale), ry + round(3 * scale)),
				name,
				self.input_colour,
				12,
				max_w=pw - round(65 * scale),
			)
			self.ddt.text(
				(px + round(35 * scale), ry + round(23 * scale)),
				subtitle,
				self.label_colour,
				11,
				max_w=pw - round(48 * scale),
			)
			if position is not None and self.session.pending[self.session.documents[position].path].changed:
				self.ddt.text((px + pw - round(20 * scale), ry + round(4 * scale)), "•", self.colours.level_green, 12)
			if self.inp.mouse_click and self.coll(row):
				self.select_track(position)
				self.inp.mouse_click = False
				return
			ry += round(44 * scale)
		if pages > 1:
			if self.draw.button("<", px + pw - round(82 * scale), py + ph - round(26 * scale)):
				self.scope_page = max(0, self.scope_page - 1)
			if self.draw.button(">", px + pw - round(30 * scale), py + ph - round(26 * scale)):
				self.scope_page = min(pages - 1, self.scope_page + 1)
		self.inp.mouse_click = False

	def _cancel_lookup(self) -> None:
		with self.lookup_lock:
			self.lookup_cancel.set()
			self.lookup_running = False
			self.lookup_result = None
			self.lookup_update = None
			self.lookup_apply_id = None

	def start_lookup(self, more: bool = False, *, preview: str | None = None, apply_after: bool = False) -> None:
		if self.lookup_running or self.gui.write_tag_in_progress or not self._flush_fields():
			return
		prefs = getattr(self.tauon, "prefs", None)
		self.lookup_cancel = threading.Event()
		cancel = self.lookup_cancel
		self.lookup_open = True
		self.lookup_running = True
		self.lookup_fraction = 0.0
		self.lookup_dragging = False
		self.scope_open = False
		self._close_tools()
		self._close_presets()
		self.lookup_progress = (
			_("Loading album tracks…")
			if preview is not None
			else (_("Loading more editions…") if more else _("Starting fingerprint scan…"))
		)
		self.lookup_result = None
		self.lookup_update = None
		self.lookup_apply_id = preview if apply_after else None
		self.lookup_error = ""
		if not more and preview is None:
			self.lookup_results = None
			self.lookup_scroll = 0
		documents = list(self.session.documents)
		previous = self.lookup_results if more or preview is not None else None
		api_key = getattr(prefs, "acoustid_api_key", "")
		ffmpeg = self.tauon.get_ffmpeg()
		library_dirs = [self.tauon.install_directory, self.tauon.user_directory]

		def progress(message: str) -> None:
			if not cancel.is_set() and self.lookup_cancel is cancel:
				self.lookup_progress = message
				self.gui.request_frame()

		def fraction(value: float) -> None:
			if not cancel.is_set() and self.lookup_cancel is cancel:
				self.lookup_fraction = max(self.lookup_fraction, value)
				self.gui.request_frame()

		def results_ready(result: LookupResult) -> None:
			with self.lookup_lock:
				if not cancel.is_set() and self.lookup_cancel is cancel:
					self.lookup_update = result
					self.gui.request_frame()

		def lookup() -> None:
			result, error = None, None
			try:
				client = MusicBrainzLookup(
					api_key,
					"",
					getattr(self.tauon, "n_version", "unknown"),
					cancel,
					progress,
					ffmpeg=ffmpeg,
					library_dirs=library_dirs,
					cache=self.lookup_cache,
					progress_fraction=fraction,
					results_ready=results_ready,
					decode_audio=previous is None,
				)
				if preview is not None and previous is not None:
					result = client.load_preview(previous, preview)
				elif previous is not None:
					result = client.load_more(previous)
				else:
					result = client.run(documents)
			except LookupCancelledError:
				return
			except MusicBrainzLookupError as failure:
				error = str(failure)
			except Exception:
				logging.exception("MusicBrainz lookup failed")
				error = _("Unexpected lookup failure; check the application log.")
			with self.lookup_lock:
				if not cancel.is_set() and self.lookup_cancel is cancel:
					self.lookup_result = (result, error)
					self.gui.request_frame()

		shooter(lookup)

	def apply_lookup(self) -> None:
		if not self.lookup_results or not self.lookup_results.albums or not self._flush_fields():
			return
		try:
			album = self.lookup_results.albums[self.lookup_album]
			if not album.preview_loaded:
				if self.lookup_running:
					return
				self.start_lookup(preview=album.id, apply_after=True)
				return
			if not album.matches:
				self.show_message(
					_("Could not apply this album"), _("No selected files match this edition."), mode="error"
				)
				return
			if self.lookup_running:
				self._cancel_lookup()
			count = stage_album(self.session, album)
			self.session.selected_document = None
			self._load_fields()
			self.tab = 0
			self.row_key = None
			self.lookup_open = False
			self.notice = _("{N} matched files loaded into the editor.").format(N=count)
		except Exception as error:
			logging.exception("Could not stage MusicBrainz tags")
			self.show_message(_("Could not apply this album"), str(error), mode="error")

	def _close_lookup(self) -> None:
		self._cancel_lookup()
		self.lookup_open = False
		self.lookup_dragging = False

	def _lookup_comparisons(self) -> list[LookupComparison]:
		results = self.lookup_results
		album = results.albums[self.lookup_album] if results and results.albums else None
		errors = {source.path: source.error for source in results.files} if results else {}
		rows = []
		for original in self.session.documents:
			doc = self.session.effective_document(original)
			number = doc.main_value("tracknumber").split("/", 1)[0]
			disc = doc.main_value("discnumber").split("/", 1)[0]
			if disc.isdigit() and int(disc) > 1 and number:
				number = disc + "." + number.zfill(2)
			before = (number or "—", doc.main_value("artist"), doc.main_value("title") or _("Untitled"))
			if album is not None and album.preview_loaded and doc.path in album.matches:
				track = album.tracks[album.matches[doc.path]]
				number = f"{track.disc}.{track.number:02d}" if album.discs > 1 else f"{track.number:02d}"
				rows.append(LookupComparison(before, (number, track.credit, track.title), True))
			else:
				reason = errors.get(doc.path, "")
				pending = not reason and (
					(album is None and self.lookup_running)
					or (album is not None and not album.preview_loaded and not album.preview_error)
				)
				if not reason and album is not None:
					reason = album.preview_error or album.unmatched.get(doc.path, "")
				message = _("Loading tracks…") if pending else _("Unmatched") + (" · " + reason if reason else "")
				rows.append(LookupComparison(before, ("—", "", message), False, pending))
		return rows

	def _lookup_popover(self, x: int, y: int, width: int, height: int) -> None:
		scale = self.gui.scale
		pw, ph = min(round(720 * scale), width - round(16 * scale)), min(round(520 * scale), height - round(16 * scale))
		px, py = x + (width - pw) // 2, y + (height - ph) // 2
		if self.inp.mouse_click and not self.coll((px, py, pw, ph)):
			self.inp.mouse_click = False
			self._close_lookup()
			return
		self.ddt.rect((x, y, width, height), ColourRGBA(0, 0, 0, 115))
		self.ddt.bordered_rect(
			(px, py, pw, ph), self.colours.box_background, self.colours.box_border, max(1, round(scale))
		)
		pad = round(14 * scale)
		self.ddt.text(
			(px + pad, py + round(12 * scale)), _("MusicBrainz Lookup"), self.title_colour, 14, max_w=pw - 2 * pad
		)
		self.ddt.text(
			(px + pad, py + round(33 * scale)),
			_("{N} selected file(s)").format(N=len(self.session.documents)),
			self.label_colour,
			11,
		)
		footer_y = py + ph - round(40 * scale)
		results = self.lookup_results
		status = self.lookup_error or (
			self.lookup_progress if self.lookup_running else _("Select an album to compare tags.")
		)
		if results and results.warnings and not self.lookup_running and not self.lookup_error:
			status = results.warnings[0]
		self.ddt.text(
			(px + pad, py + round(49 * scale)), status, self.label_colour, 11, max_w=pw - 2 * pad - round(46 * scale)
		)
		if self.lookup_running:
			bar = (px + pad, py + round(68 * scale), pw - 2 * pad, round(12 * scale))
			self.ddt.bordered_rect(
				bar, self.colours.box_thumb_background, self.colours.box_text_border, max(1, round(scale))
			)
			fraction = max(0.0, min(1.0, self.lookup_fraction))
			inset = max(1, round(2 * scale))
			self.ddt.rect(
				(bar[0] + inset, bar[1] + inset, round((bar[2] - 2 * inset) * fraction), bar[3] - 2 * inset),
				self.colours.level_green,
			)
			self.ddt.text(
				(px + pw - pad - round(42 * scale), py + round(49 * scale)),
				f"{round(fraction * 100)}%",
				self.label_colour,
				11,
			)
		content_y = py + round(88 * scale)
		albums = results.albums[:LOOKUP_LIMIT] if results else []
		row_height = min(
			round(28 * scale), max(round(18 * scale), (footer_y - content_y - round(70 * scale)) // max(1, len(albums)))
		)
		if albums:
			self._lookup_albums(px + pad, content_y, pw - 2 * pad, row_height)
			content_y += len(albums) * row_height
		elif not self.lookup_running:
			self.ddt.text(
				(px + pad, content_y),
				self.lookup_error or _("No matching album editions found."),
				self.label_colour,
				11,
				max_w=pw - 2 * pad,
			)
			content_y += round(22 * scale)
		content_y += round(8 * scale)
		self._lookup_table(px + pad, content_y, pw - 2 * pad, footer_y - content_y - round(8 * scale))
		album = albums[self.lookup_album] if albums else None
		if (
			album
			and not album.preview_loaded
			and album.preview_error
			and not self.lookup_running
			and self.draw.button(_("Retry tracks"), px + pad, footer_y, w=round(110 * scale), h=round(28 * scale))
		):
			self.start_lookup(preview=album.id)
		if (
			album
			and album.preview_loaded
			and album.matches
			and self.draw.button(
				_("Use this album"), px + pw - round(212 * scale), footer_y, w=round(120 * scale), h=round(28 * scale)
			)
		):
			self.apply_lookup()
		if self.draw.button(
			_("Cancel") if self.lookup_running else _("Close"),
			px + pw - round(82 * scale),
			footer_y,
			w=round(68 * scale),
			h=round(28 * scale),
		):
			self._close_lookup()

	def _lookup_albums(self, x: int, y: int, width: int, row_height: int) -> None:
		results = self.lookup_results
		if results is None:
			return
		scale = self.gui.scale
		for index, album in enumerate(results.albums[:LOOKUP_LIMIT]):
			ry = y + index * row_height
			rect = (x, ry, width, row_height)
			self.fields.add(rect)
			if index == self.lookup_album or self.coll(rect):
				self.ddt.rect(rect, self.colours.box_button_background_highlight)
			if index == self.lookup_album:
				self.ddt.rect(
					(x, ry + round(2 * scale), round(3 * scale), row_height - round(4 * scale)),
					self.colours.level_green,
				)
			if self.inp.mouse_click and self.coll(rect):
				if self.lookup_album != index:
					self.lookup_scroll = 0
					self.lookup_dragging = False
				self.lookup_album = index
				self.inp.mouse_click = False
				self.gui.request_frame()
			matched = len(album.matches) if album.preview_loaded else album.supported_files
			counts = (
				_("{N}/{T} matched").format(N=matched, T=len(results.files))
				if album.preview_loaded
				else (_("Could not load tracks") if album.preview_error else _("Loading tracks…"))
			)
			details = " · ".join(
				value for value in (counts, album.date, album.country, album.format, album.disambiguation) if value
			)
			self.ddt.text(
				(x + round(8 * scale), ry + round(2 * scale)),
				album.title + (" · " + album.credit if album.credit else ""),
				self.input_colour,
				11,
				max_w=width * 0.6 - round(12 * scale),
			)
			self.ddt.text(
				(x + width * 0.6, ry + round(2 * scale)),
				details,
				self.label_colour,
				11,
				max_w=width * 0.4 - round(4 * scale),
			)

	def _lookup_table(self, x: int, y: int, width: int, height: int) -> None:
		scale = self.gui.scale
		header_height, row_height = round(32 * scale), round(22 * scale)
		arrow_width = round(24 * scale)
		rows = self._lookup_comparisons()
		y_rows = y + header_height
		body_height = max(row_height, height - header_height)
		visible = max(1, body_height // row_height)
		maximum = max(0, len(rows) - visible)
		area = (x, y_rows, width, visible * row_height)
		self.fields.add(area)
		wheel = getattr(self.inp, "mouse_wheel", 0)
		if wheel and self.coll(area):
			self.lookup_scroll -= round(wheel * 3)
			self.inp.mouse_wheel = 0
		self.lookup_scroll = max(0, min(maximum, self.lookup_scroll))
		if maximum:
			track = (x + width - round(8 * scale), y_rows, round(8 * scale), visible * row_height)
			self.fields.add(track)
			thumb_height = min(track[3], max(round(20 * scale), round(track[3] * visible / len(rows))))
			travel = track[3] - thumb_height
			if self.inp.mouse_click and self.coll(track):
				self.lookup_dragging = True
				self.inp.mouse_click = False
			if self.lookup_dragging:
				if getattr(self.inp, "mouse_down", False):
					ratio = (self.inp.mouse_position[1] - y_rows - thumb_height / 2) / max(1, travel)
					self.lookup_scroll = round(max(0, min(1, ratio)) * maximum)
					self.gui.request_frame()
				else:
					self.lookup_dragging = False
			self.ddt.rect(track, self.colours.box_thumb_background)
			self.ddt.rect(
				(
					track[0] + round(2 * scale),
					y_rows + round(travel * self.lookup_scroll / maximum),
					round(4 * scale),
					thumb_height,
				),
				self.label_colour,
			)
			width -= round(16 * scale)
		half = (width - arrow_width) // 2
		number_width = min(round(36 * scale), round(half * 0.17))
		artist_width = round((half - number_width) * 0.38)
		columns = (0, number_width, number_width + artist_width)
		widths = (number_width, artist_width, half - number_width - artist_width)
		for side, label in ((x, _("Before")), (x + half + arrow_width, _("After"))):
			self.ddt.text((side + round(3 * scale), y), label, self.label_colour, 11, max_w=half)
			for offset, cell_width, heading in zip(columns, widths, ("#", _("Artist"), _("Title")), strict=True):
				self.ddt.text(
					(side + offset + round(3 * scale), y + round(16 * scale)),
					heading,
					self.label_colour,
					10,
					max_w=cell_width - round(6 * scale),
				)
		self.ddt.rect((x, y_rows - round(scale), width, max(1, round(scale))), self.colours.box_text_border)
		for index, row in enumerate(rows[self.lookup_scroll : self.lookup_scroll + visible]):
			ry = y_rows + index * row_height
			if index % 2 == 0:
				self.ddt.rect((x, ry, width, row_height), self.colours.box_button_background_highlight)
			colour = (
				self.input_colour
				if row.matched
				else (
					self.label_colour
					if row.pending
					else self.readable_colour(ColourRGBA(235, 169, 80, 255), self.colours.box_background)
				)
			)
			self.ddt.text(
				(x + half + round(4 * scale), ry + round(2 * scale)),
				"→" if row.matched else "—",
				colour,
				11,
				max_w=arrow_width - round(4 * scale),
			)
			for side, values in ((x, row.before), (x + half + arrow_width, row.after)):
				for offset, cell_width, value in zip(columns, widths, values, strict=True):
					self.ddt.text(
						(side + offset + round(3 * scale), ry + round(2 * scale)),
						value.replace("\n", " / "),
						self.input_colour if side == x else colour,
						11,
						max_w=cell_width - round(6 * scale),
					)

	def _input(self, field: str, label: str, x: int, y: int, width: int) -> None:
		scale = self.gui.scale
		index = MAIN_FIELDS.index(field)
		box = self.boxes[field]
		self.ddt.text((x, y), label, self.label_colour, 11, max_w=width)
		y += round(16 * scale)
		rect = (x, y, width, round(23 * scale))
		self.fields.add(rect)
		self.ddt.bordered_rect(rect, self.colours.box_background, self.colours.box_text_border, max(1, round(scale)))
		control_width = 0
		if self._field_edited(field):
			control_width += round(25 * scale)
			if self._rollback_button(x + width - round((49 if field in VALUE_FIELDS else 23) * scale), y):
				self._rollback_field(field, main=True)
		if field in VALUE_FIELDS:
			control_width += round(24 * scale)
			if self.draw.button(
				"/",
				x + width - round(24 * scale),
				y + round(2 * scale),
				w=round(21 * scale),
				h=round(19 * scale),
				font=14,
				text_y_offset=1,
				text_colour=self.readable_colour(CONTROL_GREY, self.colours.box_background),
				press=self.input_enabled and self.inp.mouse_click,
				tooltip=_("Insert a separator to add another value to this tag."),
			):
				self.active_field = index
				box.insert_separator()
				self.inp.mouse_click = False
				self.gui.request_frame()
		if self.input_enabled and self.inp.mouse_click and self.coll((x, y, width - control_width, rect[3])):
			self.active_field = index
		box.draw(
			x + round(4 * scale),
			y + round(4 * scale),
			self.input_colour,
			active=self.input_enabled and self.active_field == index,
			width=width - round(8 * scale) - control_width,
		)
		mixed = self.value_lists[field] is None if field in VALUE_FIELDS else self.effective[field] is None
		if not box.text and mixed:
			self.ddt.text(
				(x + round(5 * scale), y + round(4 * scale)),
				_("Different values"),
				self.label_colour,
				12,
				max_w=width - round(10 * scale) - control_width,
			)
		if self._field_edited(field):
			self._edited_outline(rect)

	def _main(self, x: int, y: int, width: int, height: int) -> None:
		scale = self.gui.scale
		art_width = round(185 * scale)
		left_width = width - art_width - round(16 * scale)
		labels = (
			_("Track title"),
			_("Album"),
			_("Artist"),
			_("Album artist"),
			_("Year / date"),
			_("Original year / date"),
			_("Track number / total"),
			_("Disc number / total"),
			_("Genre"),
			_("Label"),
			_("Composer"),
		)
		groups = ((0,), (1,), (2,), (3,), (4, 5), (6, 7), (8,), (9, 10))
		if self.input_enabled and self.inp.key_tab_press:
			direction = -1 if self.inp.key_shift_down or self.inp.key_shiftr_down else 1
			self.active_field = (self.active_field + direction) % len(labels)
			self.inp.key_tab_press = False
			self.main_page = next(index for index, group in enumerate(groups) if self.active_field in group)
		row_height = round(42 * scale)
		rows_per_page = max(1, min(len(groups), (height - round(40 * scale)) // row_height))
		if rows_per_page < len(groups):
			rows_per_page = max(1, (height - round(64 * scale)) // row_height)
		self.main_page = min(self.main_page, len(groups) - rows_per_page)
		field_y = y
		if rows_per_page < len(groups):
			if self.draw.button("↑", x + left_width - round(55 * scale), field_y):
				self.main_page = max(0, self.main_page - rows_per_page)
			if self.draw.button("↓", x + left_width - round(25 * scale), field_y):
				self.main_page = min(len(groups) - rows_per_page, self.main_page + rows_per_page)
			field_y += round(25 * scale)
		for row, indices in enumerate(groups[self.main_page : self.main_page + rows_per_page]):
			for column, index in enumerate(indices):
				field_width = left_width if len(indices) == 1 else left_width // 2 - round(5 * scale)
				self._input(
					MAIN_FIELDS[index],
					labels[index],
					x + column * left_width // 2,
					field_y + row * row_height,
					field_width,
				)
		ry = field_y + rows_per_page * row_height + round(5 * scale)
		self.ddt.text((x, ry), _("Track rating"), self.label_colour, 11)
		value = self.boxes["rating"].text
		score = int(value or "0")
		self.tauon.draw_rating_widget(
			x + round(78 * scale),
			ry + round(5 * scale),
			self.tracks[0],
			allow_input=self.input_enabled,
			rating=score,
			on_change=lambda rating: self.boxes["rating"].set_text(str(rating)),
		)
		self.ddt.text(
			(x + round(165 * scale), ry + round(3 * scale)),
			_("Mixed") if self.effective["rating"] is None and not value else f"{score}/10",
			self.label_colour,
			11,
		)
		if self._field_edited("rating"):
			self._edited_outline((x, ry, left_width, round(24 * scale)))
			if self._rollback_button(x + left_width - round(23 * scale), ry):
				self._rollback_field("rating", main=True)
		ax = x + left_width + round(16 * scale)
		self.ddt.text((ax, y), _("Embedded album art"), self.label_colour, 11)
		art_height = max(round(30 * scale), min(round(160 * scale), height - round(110 * scale)))
		self.art_rect = (ax, y + round(20 * scale), art_width, art_height)
		self.fields.add(self.art_rect)
		background = (
			self.colours.box_button_background_highlight
			if self.gui.ext_drop_mode and self.coll(self.art_rect)
			else self.colours.box_thumb_background
		)
		self.ddt.bordered_rect(self.art_rect, background, self.colours.box_text_border, max(1, round(scale)))
		if self.preview.alive:
			if self.preview.texture is None:
				self.preview.prime()
				self.preview_dimensions = (self.preview.rect.w, self.preview.rect.h)
			source_w, source_h = self.preview_dimensions
			ratio = min((art_width - 8 * scale) / source_w, (art_height - 8 * scale) / source_h, 1)
			self.preview.rect.w, self.preview.rect.h = round(source_w * ratio), round(source_h * ratio)
			self.preview.draw(
				ax + (art_width - self.preview.rect.w) / 2,
				self.art_rect[1] + (self.art_rect[3] - self.preview.rect.h) / 2,
			)
		else:
			self.ddt.text(
				(ax + art_width / 2, self.art_rect[1] + art_height / 2 - 7 * scale, 2),
				_("No embedded art"),
				self.label_colour,
				11,
			)
		for offset, text in enumerate(
			(
				_("Drop an image to replace art"),
				_("Mixed artwork; first file shown")
				if self.art_mixed
				else _("{N} embedded image(s)").format(N=self.art_count),
			)
		):
			if height < round(150 * scale):
				break
			self.ddt.text(
				(ax, self.art_rect[1] + art_height + round((5 + offset * 18) * scale)),
				text,
				self.label_colour,
				11,
				max_w=art_width,
			)
		art_button_y = self.art_rect[1] + art_height + round((44 if height >= round(150 * scale) else 5) * scale)
		if self.draw.button(
			_("Remove all art"),
			ax,
			art_button_y,
			w=art_width - round(27 * scale),
			h=round(23 * scale),
			tooltip=_("Artwork changes replace or remove every embedded image in the chosen track scope."),
		):
			self.session.art_changed = True
			self.session.art_data = None
			self.art_count = 0
			self.art_mixed = False
			self._preview(None)
		if self.session.art_changed and art_button_y + round(29 * scale) < self.editor_bottom - round(65 * scale):
			self.ddt.text((ax, art_button_y + round(29 * scale)), _("Artwork changed"), self.colours.level_green, 11)
		if self.session.art_changed:
			self._edited_outline(self.art_rect)
			if self._rollback_button(ax + art_width - round(23 * scale), art_button_y):
				self.session.art_changed = False
				self.session.art_data = None
				self._load_art()
				self.inp.mouse_click = False

	def _table(self, x: int, y: int, width: int, height: int) -> None:
		scale = self.gui.scale
		rows = self._misc_rows()
		compact = height < round(180 * scale)
		reserved_height = 100 if compact else 220
		page_size = max(1, min(6, int(height / scale - reserved_height) // 24))
		if len(rows) > page_size:
			page_size = max(1, min(6, int(height / scale - reserved_height - 26) // 24))
		pages = max(1, (len(rows) + page_size - 1) // page_size)
		if self.row_focus_new:
			self.row_page = next(
				(
					index // page_size
					for index, entry in enumerate(rows)
					if entry.key == self.row_key and entry.value_index == self.row_value_index
				),
				self.row_page,
			)
			self.row_focus_new = False
		self.row_page = min(self.row_page, pages - 1)
		self.ddt.text((x, y), _("Native key"), self.label_colour, 11)
		self.ddt.text((x + width * 0.45, y), _("Value / type"), self.label_colour, 11)
		y += round((18 if compact else 20) * scale)
		list_y = y
		row_height = round((22 if compact else 24) * scale)
		button_height = round((21 if compact else 23) * scale)
		for entry in rows[self.row_page * page_size : (self.row_page + 1) * page_size]:
			rect = (x, y, width, row_height - round(scale))
			self.fields.add(rect)
			if self.row_key == entry.key and (self.row_value_index == entry.value_index):
				self.ddt.rect(rect, self.colours.box_button_background_highlight)
			self.ddt.text(
				(x + round(3 * scale), y + round(2 * scale)),
				("✓ " if self._entry_edited(entry.key) else "") + entry.key,
				self.input_colour,
				11,
				max_w=width * 0.43,
			)
			self.ddt.text(
				(x + width * 0.45, y + round(2 * scale)),
				entry.value.replace("\n", " / ") if entry.editable else entry.kind,
				self.label_colour,
				11,
				max_w=width * 0.54,
			)
			if self._entry_edited(entry.key):
				self._edited_outline(rect)
			if self.inp.mouse_click and self.coll(rect):
				self._select_row(entry)
				self.inp.mouse_click = False
			y += row_height
		if pages > 1:
			y = list_y + page_size * row_height
			if self.draw.button("<", x + width - round(100 * scale), y, w=round(23 * scale), h=button_height):
				self.row_page = max(0, self.row_page - 1)
			self.ddt.text(
				(x + width - round(72 * scale), y + round(2 * scale)),
				f"{self.row_page + 1}/{pages}",
				self.label_colour,
				11,
			)
			if self.draw.button(">", x + width - round(23 * scale), y, w=round(23 * scale), h=button_height):
				self.row_page = min(pages - 1, self.row_page + 1)
			y += round((23 if compact else 26) * scale)
		y += round(6 * scale)
		add_width = min(round((210 if compact else 260) * scale), round(width * 0.48))
		add_x = x + width - add_width
		self.ddt.text((add_x, y), _("Add key"), self.label_colour, 11)
		add_y = y + round(18 * scale)
		preset_space = round(80 * scale)
		preset_gap = round(4 * scale)
		rect = (add_x, add_y, add_width - round(49 * scale) - preset_space - preset_gap, round(23 * scale))
		self.ddt.bordered_rect(rect, self.colours.box_background, self.colours.box_text_border, max(1, round(scale)))
		if self.inp.mouse_click and self.coll(rect):
			self.key_active = True
		self.new_key.draw(
			add_x + round(3 * scale),
			add_y + round(4 * scale),
			self.input_colour,
			active=self.input_enabled and self.key_active,
			width=rect[2] - round(6 * scale),
		)
		if self.draw.button(
			_("Presets") + " ▾",
			x + width - preset_space,
			add_y,
			w=preset_space,
			h=round(23 * scale),
			press=self.input_enabled and self.inp.mouse_click,
		):
			self.open_presets(x + width, add_y + round(26 * scale))
			self.inp.mouse_click = False
		if self.draw.button(
			_("Add"),
			x + width - round(44 * scale) - preset_space - preset_gap,
			add_y,
			w=round(44 * scale),
			h=round(23 * scale),
		):
			key = self.new_key.text.strip()
			if key:
				self._add_misc_key(key)
		if not compact:
			y = add_y + round(33 * scale)
		if self.row_key is None:
			self.ddt.text(
				(x, y),
				_("Select a tag to edit; add custom text by name."),
				self.label_colour,
				11,
				max_w=width - add_width - round(12 * scale) if compact else width,
			)
			return
		entry = next(
			(row for row in rows if row.key == self.row_key and (row.value_index == self.row_value_index)),
			TagEntry(self.row_key, ""),
		)
		if not compact:
			kind = _("Text value") if self.row_is_list else entry.kind
			self.ddt.text((x, y), self.row_key + " · " + kind, self.label_colour, 11, max_w=width)
			y += round(20 * scale)
		if not entry.editable:
			self.ddt.text((x, y), _("Binary or structured tag: preserved without modification."), self.label_colour, 11)
			if not compact:
				self.ddt.text((x, y + round(24 * scale)), entry.value, self.input_colour, 11, max_w=width)
			return
		bottom = self.editor_bottom - round(65 * scale)
		box_height = max(round(21 * scale), bottom - y - round(27 * scale))
		box_width = width
		if compact:
			box_width -= add_width + round(12 * scale)
		rect = (x, y, box_width, box_height)
		self.ddt.bordered_rect(rect, self.colours.box_background, self.colours.box_text_border, max(1, round(scale)))
		if self.inp.mouse_click and self.coll(rect):
			self.key_active = False
		if self.row_original == "<Multiple values>" and not self.row_box.text:
			self.ddt.text(
				(x + round(8 * scale), y + round(4 * scale)),
				_("Different values; editing replaces this entry in each file."),
				self.label_colour,
				11,
				max_w=box_width - round(16 * scale),
			)
		self.row_scroll += self.row_box.draw(
			x + round(4 * scale),
			y + round(4 * scale),
			self.input_colour,
			active=self.input_enabled and not self.key_active,
			width=box_width - round(8 * scale),
			height=box_height - round(4 * scale),
			scroll=self.row_scroll,
			bounded=True,
		)
		self._row_edit_controls(rect)

	def _row_edit_controls(self, rect: tuple[int, int, int, int]) -> None:
		if self._entry_edited(self.row_key):
			self._edited_outline(rect)
			x, y = rect[:2]
			height = rect[3]
			if self._rollback_button(x, y + height + round(4 * self.gui.scale)):
				self._rollback_field(self.row_key)

	def _tabs(self, x: int, y: int, width: int) -> None:
		scale = self.gui.scale
		tab_width = min(round(94 * scale), width // 2)
		self.ddt.rect((x, y + round(32 * scale), width, max(1, round(scale))), self.colours.box_text_border)
		for index, label in enumerate((_("Main"), _("Misc"))):
			rect = (x + index * tab_width, y, tab_width, round(32 * scale))
			self.fields.add(rect)
			if self.tab == index or self.coll(rect):
				self.ddt.rect(rect, self.colours.box_button_background_highlight)
			if self.tab == index:
				self.ddt.rect(
					(rect[0], y + round(30 * scale), tab_width, max(2, round(2 * scale))), self.colours.level_green
				)
			self.ddt.text(
				(rect[0] + round(12 * scale), y + round(7 * scale)),
				label,
				self.input_colour if self.tab == index else self.label_colour,
				12,
				max_w=tab_width - round(18 * scale),
			)
			if self.input_enabled and self.inp.mouse_click and self.coll(rect):
				if not self._flush_fields():
					continue
				self.tab = index
				self.row_key = None
				self.row_page = 0
				self.key_active = False
				self.inp.mouse_click = False

	def _tag_badges(self, x: int, y: int, width: int) -> None:
		scale = self.gui.scale
		badges = dict.fromkeys(
			(self.session.effective_document(doc).label, doc.path.suffix[1:].upper())
			for doc in self.session.scope_documents
		)
		for label, extension in badges:
			colour = self.tauon.formats.colours.get(extension, ColourRGBA(130, 130, 130, 255))
			if sum(name == label for name, ext in badges) > 1:
				label += " · " + extension
			available = max(0, width)
			if available <= 0:
				break
			self.ddt.text((x, y), label, self.readable_colour(colour, self.colours.box_background), 11, max_w=available)
			advance = self.ddt.get_text_w(label, 11) + round(14 * scale)
			x += advance
			width -= advance

	def _close(self) -> None:
		with self.load_lock:
			self.load_cancel.set()
			self.load_result = None
		self.loading = False
		self.active = False
		self.gui.box_over = False
		self._close_lookup()
		self.preview.destruct()
		self._close_tools()
		self._close_presets()

	def _accept_lookup_results(self, result: LookupResult | None) -> None:
		previous = self.lookup_results
		selected = previous.albums[self.lookup_album].id if previous and previous.albums else None
		self.lookup_results = result
		self.lookup_album = 0
		if result is not None:
			result.albums = result.albums[:LOOKUP_LIMIT]
			for index, album in enumerate(result.albums):
				if selected in (album.id, album.requested_id):
					self.lookup_album = index
		if (
			result is None
			or not result.albums
			or selected not in (result.albums[self.lookup_album].id, result.albums[self.lookup_album].requested_id)
		):
			self.lookup_scroll = 0
			self.lookup_dragging = False

	def render(self) -> None:
		if not self.active:
			return
		if self.loading:
			self._finish_loading()
			if not self.active:
				return
		with self.lookup_lock:
			update, completed = self.lookup_update, self.lookup_result
			self.lookup_update = None
			self.lookup_result = None
		if update is not None:
			self._accept_lookup_results(update)
		if completed is not None:
			result, error = completed
			self._accept_lookup_results(result)
			self.lookup_error = error or ""
			self.lookup_running = False
			self.lookup_fraction = 1.0
			apply_id, self.lookup_apply_id = self.lookup_apply_id, None
			if apply_id is not None and result is not None:
				album = next((album for album in result.albums if apply_id in (album.id, album.requested_id)), None)
				if album is not None:
					self.lookup_album = result.albums.index(album)
					if album.preview_loaded:
						self.apply_lookup()
					else:
						self.show_message(_("Could not load album tracks"), album.preview_error, mode="error")
		if self.write_result is not None:
			self._finish_write()
		if self.gui.message_box:
			return
		if self.gui.level_2_click:
			self.inp.mouse_click = True
		self.gui.level_2_click = False
		self.label_colour = self.readable_colour(self.colours.box_text_label, self.colours.box_background)
		self.input_colour = self.readable_colour(self.colours.box_input_text, self.colours.box_background)
		self.title_colour = self.readable_colour(self.colours.box_title_text, self.colours.box_background, 5.4)
		scale = self.gui.scale
		width = min(round(760 * scale), self.window_size[0] - round(24 * scale))
		height = min(round(590 * scale), self.window_size[1] - round(24 * scale))
		x = (self.window_size[0] - width) // 2
		y = (self.window_size[1] - height) // 2
		self.editor_bottom = y + height
		self.ddt.bordered_rect(
			(x, y, width, height), self.colours.box_background, self.colours.box_border, max(1, round(scale))
		)
		self.ddt.text_background_colour = self.colours.box_background
		self.gui.box_over = True
		body_x, body_y = x + round(16 * scale), y + round(140 * scale)
		body_width, body_height = width - round(32 * scale), height - round(199 * scale)
		title = _("Tag editor")
		self.ddt.text((body_x, y + round(18 * scale)), title, self.title_colour, 215)
		file_count = len(self.tracks) if self.loading else len(self.session.scope_documents)
		file_label = _("{N} active file") if file_count == 1 else _("{N} active files")
		self.ddt.text(
			(body_x + body_width, y + round(20 * scale), 1),
			file_label.format(N=file_count),
			self.label_colour,
			11,
			max_w=body_width - self.ddt.get_text_w(title, 215) - round(16 * scale),
		)
		if self.loading:
			self._loading_screen(body_x, body_y, body_width)
			return
		if self.gui.write_tag_in_progress:
			self.ddt.text((body_x, body_y), _("Writing tags…"), self.input_colour, 13)
			return
		menu_open = self.tools_menu is not None and self.tools_menu.active
		presets_open = self.presets_menu is not None and self.presets_menu.active
		if self.inp.key_esc_press:
			self.inp.key_esc_press = False
			if menu_open:
				self._close_tools()
			elif presets_open:
				self._close_presets()
			elif self.lookup_open:
				self._close_lookup()
			elif self.scope_open:
				self.scope_open = False
			else:
				self._close()
			return
		self.input_enabled = not (menu_open or presets_open or self.scope_open or self.lookup_open)
		click = self.inp.mouse_click
		right_click = getattr(self.inp, "right_click", False)
		level_right_click = getattr(self.inp, "level_2_right_click", False)
		wheel = getattr(self.inp, "mouse_wheel", 0)
		if not self.input_enabled:
			self.inp.mouse_click = False
			self.inp.right_click = False
			self.inp.level_2_right_click = False
			self.inp.mouse_wheel = 0
		self._tabs(body_x, y + round(61 * scale), body_width - round(90 * scale))
		if not self.lookup_running and self.draw.button(
			_("Tools") + " ▾",
			x + width - round(96 * scale),
			y + round(64 * scale),
			w=round(80 * scale),
			h=round(26 * scale),
		):
			self.open_tools(x + width - round(16 * scale), y + round(95 * scale))
		self._scope_selector(body_x, body_y - round(34 * scale), body_width - round(175 * scale), body_height)
		if not self.lookup_running and self.draw.button(
			_("MusicBrainz Lookup"),
			x + width - round(180 * scale),
			body_y - round(34 * scale),
			w=round(164 * scale),
			h=round(28 * scale),
		):
			self.start_lookup()
			self.inp.mouse_click = False
		if self.tab == 0:
			self._main(body_x, body_y, body_width, body_height)
		else:
			self._table(body_x, body_y, body_width, body_height)
		footer_y = y + height - round(54 * scale)
		button_space = round(230 * scale)
		if not self.lookup_running and self.draw.button(
			_("Write tags"),
			x + width - round(230 * scale),
			footer_y,
			w=round(120 * scale),
			h=round(32 * scale),
			tooltip=_("Save the fields and every pending file, including tracks outside this view."),
		):
			self.write()
		if self.draw.button(
			_("Close"), x + width - round(100 * scale), footer_y, w=round(84 * scale), h=round(32 * scale)
		):
			self._close()
		self._tag_badges(body_x, footer_y + round(7 * scale), width - button_space - round(32 * scale))
		notice = self.notice
		if not notice and any(
			doc.family == "ID3"
			and doc.id3_version == 3
			and any(len(doc.text_values(key) or []) > 1 for key in doc.tags)
			for doc in (self.session.effective_document(source) for source in self.session.scope_documents)
		):
			notice = _("Multiple ID3v2.3 values may not work in other players. Tools can upgrade to ID3v2.4.")
		pending_width = 0
		if self._changes_pending():
			pending = _("Changes pending")
			pending_width = min(body_width, self.ddt.get_text_w(pending, 11) + round(16 * scale))
			self.ddt.text(
				(body_x + body_width - pending_width, y + height - round(18 * scale)),
				pending,
				self.colours.level_green,
				11,
				max_w=pending_width,
			)
		if notice and body_width > pending_width:
			self.ddt.text(
				(body_x, y + height - round(18 * scale)),
				notice,
				self.label_colour,
				11,
				max_w=body_width - pending_width,
			)
		if not self.input_enabled:
			self.inp.mouse_click = click
			self.inp.right_click = right_click
			self.inp.level_2_right_click = level_right_click
			self.inp.mouse_wheel = wheel
		if self.scope_open:
			self._scope_popover(x, y, width, height)
		elif self.lookup_open:
			self._lookup_popover(x, y, width, height)
