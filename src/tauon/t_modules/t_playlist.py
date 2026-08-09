"""Playlist, library navigation, and queue UI components."""

from __future__ import annotations

import copy
import io
import logging
import math
import os
import threading
import time
from collections.abc import Callable
from ctypes import c_float, pointer
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

import sdl3
from PIL import Image

from tauon.t_modules.t_enums import PlayingState, QueueType, StopMode
from tauon.t_modules.t_extra import (
	Timer,
	TestTimer,
	alpha_blend,
	alpha_mod,
	clean_string,
	coll_point,
	d_date_display,
	d_date_display2,
	filename_safe,
	get_artist_strip_feat,
	get_display_time,
	get_hms_time,
	get_modify_date_string,
	point_distance,
	point_proximity_test,
	rgb_add_hls,
	subtract_rect,
	test_lumi,
	year_search,
)
from tauon.t_modules.t_menu import MenuItem
from tauon.t_modules.t_models import (
	ColourRGBA,
	TauonQueueItem,
	TrackClass,
	queue_item_gen,
)
from tauon.t_modules.t_prefs import Prefs
from tauon.t_modules.t_state import ColoursClass, Decorator, GuiVar, Input, LoadImageAsset, MenuTrackRef, asset_loader
from tauon.t_modules.t_widgets import Fields

if TYPE_CHECKING:
	from tauon.t_modules.t_draw import TDraw


class _PlaylistPlayer(Protocol):
	default_playlist: list[int]
	multi_playlist: list[Any]
	force_queue: list[Any]

	def __getattr__(self, name: str) -> Any: ...


class _PlaylistApp(Protocol):
	gui: GuiVar
	inp: Input
	ddt: TDraw
	coll: Callable[[object], bool]
	pctl: _PlaylistPlayer
	prefs: Prefs
	colours: ColoursClass
	fields: Fields
	window_size: list[int]
	renderer: Any
	smooth_scroll: Any

	def __getattr__(self, name: str) -> Any: ...


SCROLL_PHYSICS_TRACKLIST_PRECISE_SCALE = 1.0

class StandardPlaylist:
	def __init__(self, tauon: _PlaylistApp, pl_bg: LoadImageAsset | None) -> None:
		self.tauon         = tauon
		self.pl_bg         = pl_bg
		self._clip_rect    = None  # set per full_render(rect) to clip the texture blit
		self.gui           = tauon.gui
		self.inp           = tauon.inp
		self.ddt           = tauon.ddt
		self.coll          = tauon.coll
		self.pctl          = tauon.pctl
		self.deco          = tauon.deco
		self.prefs         = tauon.prefs
		self.colours       = tauon.colours
		self.renderer      = tauon.renderer
		self.star_store    = tauon.star_store
		self.window_size   = tauon.window_size
		self.smooth_scroll = tauon.smooth_scroll

	def _tracklist_step_height(self, track_position: int) -> float:
		if track_position < 0 or track_position >= len(self.pctl.default_playlist):
			return float(self.gui.playlist_row_height)

		step = float(self.gui.playlist_row_height)
		if not self.pctl.multi_playlist[self.pctl.active_playlist_viewing].hide_title and self.prefs.break_enable:
			if track_position == 0 or self.pctl.get_track(self.pctl.default_playlist[track_position]).parent_folder_path != self.pctl.get_track(
				self.pctl.default_playlist[track_position - 1]
			).parent_folder_path:
				step += self.gui.playlist_row_height
		return step

	def _apply_tracklist_pixel_scroll(self) -> None:
		pctl = self.pctl
		gui = self.gui
		position_before = pctl.playlist_view_position
		pixels_before = gui.playlist_scroll_pixels
		forward_steps = 0
		backward_steps = 0

		while pctl.playlist_view_position < len(pctl.default_playlist) and gui.playlist_scroll_pixels >= self._tracklist_step_height(
			pctl.playlist_view_position
		):
			gui.playlist_scroll_pixels -= self._tracklist_step_height(pctl.playlist_view_position)
			pctl.playlist_view_position += 1
			forward_steps += 1

		while gui.playlist_scroll_pixels < 0 and pctl.playlist_view_position > 0:
			pctl.playlist_view_position -= 1
			gui.playlist_scroll_pixels += self._tracklist_step_height(pctl.playlist_view_position)
			backward_steps += 1

		if pctl.playlist_view_position <= 0 and gui.playlist_scroll_pixels < 0:
			gui.playlist_scroll_pixels = 0
			self.smooth_scroll.reset_motion("playlist")

		if pctl.playlist_view_position >= len(pctl.default_playlist):
			pctl.playlist_view_position = len(pctl.default_playlist)
			gui.playlist_scroll_pixels = 0
			self.smooth_scroll.reset_motion("playlist")

		# if logging.getLogger().isEnabledFor(logging.DEBUG) and (
		# 	forward_steps
		# 	or backward_steps
		# 	or position_before != pctl.playlist_view_position
		# 	or abs(pixels_before - gui.playlist_scroll_pixels) >= 0.01
		# ):
			# logging.debug(
			# 	"Playlist pixel scroll apply pos_before=%d pos_after=%d pixels_before=%.4f pixels_after=%.4f forward_steps=%d backward_steps=%d",
			# 	position_before,
			# 	pctl.playlist_view_position,
			# 	pixels_before,
			# 	gui.playlist_scroll_pixels,
			# 	forward_steps,
			# 	backward_steps,
			# )

	def _same_album_art_block(self, track_a: TrackClass, track_b: TrackClass) -> bool:
		return (
			track_a.parent_folder_path == track_b.parent_folder_path
			and track_a.album == track_b.album
			and track_a.album_artist == track_b.album_artist
		)

	def _album_art_block_bounds(self, track_position: int) -> tuple[int, int]:
		pctl = self.pctl
		if track_position < 0 or track_position >= len(pctl.default_playlist):
			return track_position, track_position

		start = track_position
		while start > 0:
			track = pctl.get_track(pctl.default_playlist[start])
			previous_track = pctl.get_track(pctl.default_playlist[start - 1])
			if not self._same_album_art_block(track, previous_track):
				break
			start -= 1

		end = track_position + 1
		while end < len(pctl.default_playlist):
			track = pctl.get_track(pctl.default_playlist[end - 1])
			next_track = pctl.get_track(pctl.default_playlist[end])
			if not self._same_album_art_block(track, next_track):
				break
			end += 1

		return start, end

	def _folder_title_would_appear(self, track_position: int) -> bool:
		pctl = self.pctl
		if (
			pctl.multi_playlist[pctl.active_playlist_viewing].hide_title
			or not self.prefs.break_enable
			or track_position < 0
			or track_position >= len(pctl.default_playlist)
		):
			return False
		if track_position == 0:
			return True
		track = pctl.get_track(pctl.default_playlist[track_position])
		previous_track = pctl.get_track(pctl.default_playlist[track_position - 1])
		return track.parent_folder_path != previous_track.parent_folder_path

	def _queue_album_art_column(
			self,
			track_position: int,
			row_y: float,
			column_x: float,
			column_width: float,
			rendered_blocks: set[int],
			draws: list[tuple[TrackClass, tuple[float, float], int, int]]) -> None:
		block_start, block_end = self._album_art_block_bounds(track_position)
		block_row_offset = track_position - block_start
		block_y = row_y - self.gui.playlist_row_height * block_row_offset
		self._queue_album_art_block(block_start, block_end, block_y, column_x, column_width, rendered_blocks, draws)

	def _queue_previous_album_art_for_folder_title(
			self,
			track_position: int,
			title_y: float,
			column_x: float,
			column_width: float,
			rendered_blocks: set[int],
			draws: list[tuple[TrackClass, tuple[float, float], int, int]]) -> None:
		if track_position <= 0 or not self._folder_title_would_appear(track_position):
			return

		block_start, block_end = self._album_art_block_bounds(track_position - 1)
		if block_end != track_position:
			return

		block_y = title_y - (block_end - block_start) * self.gui.playlist_row_height
		self._queue_album_art_block(block_start, block_end, block_y, column_x, column_width, rendered_blocks, draws)

	def _queue_album_art_block(
			self,
			block_start: int,
			block_end: int,
			block_y: float,
			column_x: float,
			column_width: float,
			rendered_blocks: set[int],
			draws: list[tuple[TrackClass, tuple[float, float], int, int]]) -> None:
		if column_width <= 8 * self.gui.scale:
			return

		if block_start in rendered_blocks:
			return
		rendered_blocks.add(block_start)

		horizontal_padding = round(1 * self.gui.scale)
		vertical_padding = round(5 * self.gui.scale)
		folder_title_bottom_gap = round(5 * self.gui.scale)

		art_size = max(1, round(column_width) - horizontal_padding * 2)
		block_height = (block_end - block_start) * self.gui.playlist_row_height
		allowed_bottom = block_y + block_height - vertical_padding
		if self._folder_title_would_appear(block_end):
			allowed_bottom = block_y + block_height + self.gui.playlist_row_height - folder_title_bottom_gap
		draw_y = block_y + vertical_padding
		draw_height = min(art_size, allowed_bottom - draw_y)

		playlist_bottom = self.window_size[1] - self.gui.panelBY
		if draw_height <= 0 or draw_y >= playlist_bottom or draw_y + draw_height <= self.gui.playlist_top:
			return

		track = self.pctl.get_track(self.pctl.default_playlist[block_start])
		draws.append((track, (column_x + horizontal_padding, draw_y), art_size, round(draw_height)))

	def compute_tracklist_insets(self) -> None:
		"""Compute the tracklist highlight/inset geometry from the current
		gui.playlist_left / gui.plw / window size. Mirrors the inline computation
		in update_layout_do(); used by the Custom Layout's Tracklist widget after
		it points those vars at its segment. (The preset path keeps its own inline
		copy untouched.)
		"""
		gui = self.gui
		prefs = self.prefs
		window_size = self.window_size
		width = gui.plw

		# In custom mode the Tracklist widget renders into its own segment, so use
		# a plain default margin instead of reacting to the (hidden) preset's left/
		# right side panels or tracks-only centering.
		if gui.custom_mode:
			gui.highlight_left = 0
			gui.tracklist_center_mode = False
			gui.tracklist_highlight_left = 0
			gui.tracklist_highlight_width = width
			gui.tracklist_inset_left = round(23 * gui.scale)
			gui.tracklist_inset_width = width - round(32 * gui.scale)
			return

		center_mode = True
		if gui.lsp or gui.rsp or gui.set_mode:
			center_mode = False
		if gui.set_mode and window_size[0] < 600:
			center_mode = False

		gui.highlight_left = 0
		highlight_width = width
		inset_left = gui.highlight_left + 23 * gui.scale
		inset_width = highlight_width - 32 * gui.scale
		if gui.lsp and not gui.rsp:
			inset_width -= 10 * gui.scale
		if gui.lsp:
			inset_left -= 10 * gui.scale
			inset_width += 10 * gui.scale
		if gui.rsp_on_left:
			inset_left -= 11 * gui.scale
			inset_width += 6 * gui.scale
		if center_mode:
			if gui.set_mode:
				gui.highlight_left = int(pow((window_size[0] / gui.scale * 0.005), 2) * gui.scale)
			else:
				gui.highlight_left = int(pow((window_size[0] / gui.scale * 0.01), 2) * gui.scale)
			if window_size[0] < 600 * gui.scale:
				gui.highlight_left = 3 * gui.scale
			highlight_width -= gui.highlight_left * 2
			inset_left = gui.highlight_left + 18 * gui.scale
			inset_width = highlight_width - 25 * gui.scale
		if window_size[0] < 600 and gui.lsp:
			inset_width = highlight_width - 18 * gui.scale

		gui.tracklist_center_mode = center_mode
		gui.tracklist_inset_left = inset_left
		gui.tracklist_inset_width = inset_width
		gui.tracklist_highlight_left = gui.highlight_left
		gui.tracklist_highlight_width = highlight_width

	def get_column_text(self, name: str, n_track: TrackClass, p_track: int) -> str:
		"""Return the display string for a text column (used by Magnet Mode layout
		to pre-measure widths). Must stay in sync with the text produced in the
		column render loop. Returns "" for widget/non-text columns."""
		pctl = self.pctl
		prefs = self.prefs
		if name == "Title":
			return n_track.title if n_track.title else n_track.filename
		if name == "Artist":
			return n_track.artist
		if name == "Album":
			return n_track.album
		if name == "Album Artist":
			text = n_track.album_artist
			if not text and prefs.column_aa_fallback_artist:
				text = n_track.artist
			return text
		if name == "Composer":
			return n_track.composer
		if name == "Comment":
			return n_track.comment.replace("\n", " ").replace("\r", " ")
		if name == "S":
			return str(n_track.lfm_scrobbles) if n_track.lfm_scrobbles > 0 else ""
		if name == "#":
			if prefs.use_absolute_track_index and pctl.multi_playlist[pctl.active_playlist_viewing].hide_title:
				return str(p_track)
			return self.tauon.track_number_process(n_track.track_number)
		if name == "Date":
			return n_track.date
		if name == "Filepath":
			return clean_string(n_track.fullpath)
		if name == "Filename":
			return clean_string(n_track.filename)
		if name == "Disc":
			return str(n_track.disc_number)
		if name == "Codec":
			text = n_track.file_ext
			if text == "JELY" and n_track.container is not None:
				text = n_track.container
			return text
		if name == "Lyrics":
			if n_track.synced:
				return "⧗"
			if n_track.lyrics:
				return "✓"
			return ""
		if name == "CUE":
			return "✓" if n_track.is_cue else ""
		if name == "Genre":
			return n_track.genre
		if name == "ID":
			return str(n_track.index)
		if name == "=/=":
			return get_modify_date_string(n_track.modified_time)
		if name == "Bitrate":
			text = str(n_track.bitrate)
			if text == "0":
				text = ""
			ex = n_track.file_ext
			if n_track.container is not None:
				ex = n_track.container
			if ex in ("FLAC", "WAV", "APE"):
				text = str(round(n_track.samplerate / 1000, 1)).rstrip("0").rstrip(".") + "|" + str(n_track.bit_depth)
			return text
		if name == "Time":
			return get_display_time(n_track.length)
		if name == "P":
			ratio = 0
			total = self.star_store.get_by_object(n_track)
			if total > 0 and n_track.length > 2:
				if n_track.length > 15:
					total += 2
				ratio = total / (n_track.length - 1)
			text = str(int(ratio))
			if text == "0":
				text = ""
			return text
		return ""

	def compute_magnet_layout(self, start_run: float, end: float, n_track: TrackClass, p_track: int) -> dict[int, tuple[float, float]]:
		"""Work out packed text positions for Magnet Mode column groups.

		A magnet group is a run of magnet-on columns plus the following column
		(magnet-off) which terminates but is still included in the group. Within a
		group the columns' text is drawn packed left with a standard-layout gap
		instead of each being confined to its own column. If the combined text
		fits the group's width it is drawn at natural size; otherwise each text is
		truncated to a share of the space proportional to its column's width.

		Returns (layout, separators):
		  - layout: column index -> (text_x, text_max_w) for columns drawn with
		    magnet positioning. Columns absent from the map render normally.
		  - separators: column index -> separator_x. When two magnet-packed columns
		    that sit next to each other share the same text colour (so the eye can't
		    tell them apart), a " - " separator is drawn after the first one, exactly
		    as the standard tracklist does between artist and title.
		"""
		gui = self.gui
		pl_st = gui.pl_st
		ddt = self.ddt
		colours = self.colours
		font = gui.row_font_size
		scale = gui.scale
		lead = 6 * scale
		gap = 6 * scale
		trail = 14 * scale
		sep_text = " - "
		sep_w = ddt.get_text_w(sep_text, font)

		def magnet_on(item: list) -> bool:
			return len(item) > 3 and bool(item[3])

		def base_colour(name: str):
			if name in colours.column_colours:
				return colours.column_colours[name]
			if name == "Title":
				return colours.title_text
			if name == "Artist" or name == "Album Artist":
				return colours.artist_text
			if name == "Album":
				return colours.album_text
			if name == "Time":
				return colours.bar_time
			return colours.index_text

		# Precompute the left edge (run) of each column
		run_positions = []
		run = start_run
		for item in pl_st:
			run_positions.append(run)
			run += item[1]

		layout: dict[int, tuple[float, float]] = {}
		separators: dict[int, float] = {}
		n = len(pl_st)
		h = 0
		while h < n:
			if not magnet_on(pl_st[h]):
				h += 1
				continue
			# Gather the group: magnet-on columns plus the terminating column
			group = []
			k = h
			while k < n:
				group.append(k)
				if not magnet_on(pl_st[k]):
					break
				k += 1

			if len(group) < 2:
				# Nothing to the right to magnet onto (last column) - render normally
				h = group[-1] + 1
				continue

			group_start = run_positions[group[0]]
			sum_widths = sum(pl_st[i][1] for i in group)
			group_end = min(group_start + sum_widths, end)
			group_span = group_end - group_start

			texts = [self.get_column_text(pl_st[i][0], n_track, p_track) for i in group]
			nats = [ddt.get_text_w(t, font) if t else 0 for t in texts]
			present = [idx for idx in range(len(group)) if texts[idx]]

			# Decide, per gap between two adjacent present columns, whether a " - "
			# separator is needed (same colour) or just a plain gap.
			between = {}  # position-in-present -> width consumed between it and the next
			for pos in range(len(present) - 1):
				col_a = group[present[pos]]
				col_b = group[present[pos + 1]]
				if base_colour(pl_st[col_a][0]) == base_colour(pl_st[col_b][0]):
					between[pos] = sep_w
				else:
					between[pos] = gap
			total_between = sum(between.values())

			available = group_span - lead - trail - total_between
			available = max(0, available)

			sum_nat = sum(nats)
			if sum_nat <= available:
				allocs = list(nats)
			else:
				# Truncate: share the space by column width ratio within the group
				allocs = [available * (pl_st[group[idx]][1] / sum_widths) if sum_widths else 0 for idx in range(len(group))]

			x = group_start + lead
			for pos, idx in enumerate(present):
				col = group[idx]
				alloc = max(0, allocs[idx])
				layout[col] = (x, alloc)
				x += min(nats[idx], alloc)
				if pos < len(present) - 1:
					if between[pos] == sep_w:
						separators[col] = x
					x += between[pos]

			h = group[-1] + 1

		return layout, separators

	def full_render(self, rect: tuple[float, float, float, float] | None = None) -> None:
		"""Render the tracklist.

		With rect=None (the preset path) it uses the standard gui layout vars
		unchanged. With a rect (the Custom Layout Tracklist widget) it renders into
		that segment by pointing the layout vars at it for the duration of the
		render, then restoring them — the heavy body (_render_body) is shared and
		left untouched, so preset rendering is byte-identical.
		"""
		if rect is None:
			self._clip_rect = None
			self._render_body()
			return
		gui = self.gui
		window_size = self.window_size
		saved = (gui.playlist_left, gui.plw, gui.panelY, gui.playlist_top, window_size[1], gui.show_playlist)
		x, y, w, h = rect
		gui.playlist_left = round(x)
		gui.plw = round(w)
		gui.panelY = round(y)
		gui.playlist_top = round(y) + round(8 * gui.scale)
		if gui.set_bar and gui.set_mode:
			# Drop the body below the columns header bar (same offset the preset
			# applies in update_layout_do) so the first rows aren't hidden under it.
			gui.playlist_top += round(gui.set_height) - round(6 * gui.scale)
		window_size[1] = round(y + h) + gui.panelBY
		gui.show_playlist = True
		# Copy only this segment from the texture to the main texture, so the
		# tracklist can't bleed past its region (see the final blit in _render_body).
		self._clip_rect = (round(x), round(y), round(w), round(h))
		self.compute_tracklist_insets()
		try:
			self._render_body()
		finally:
			(gui.playlist_left, gui.plw, gui.panelY, gui.playlist_top, window_size[1], gui.show_playlist) = saved

	def _render_body(self) -> None:
		tauon       = self.tauon
		prefs       = self.prefs
		pctl        = self.pctl
		gui         = self.gui
		inp         = self.inp
		window_size = self.window_size
		ddt         = self.ddt
		colours     = self.colours
		pl_bg       = self.pl_bg
		deco        = self.deco
		left        = gui.playlist_left
		width       = gui.plw

		self.update_album_rating_hover()

		highlight_width    = gui.tracklist_highlight_width
		gui.highlight_left = gui.tracklist_highlight_left
		inset_width        = gui.tracklist_inset_width
		inset_left         = gui.tracklist_inset_left
		center_mode        = gui.tracklist_center_mode
		scrollbar_width    = 15 * gui.scale
		if gui.set_mode and prefs.left_align_album_artist_title:
			scrollbar_width = 11 * gui.scale
		scrollbar_x = gui.playlist_left + gui.plw - scrollbar_width - 2 * gui.scale
		scrollbar_hitbox_width = 28 * gui.scale
		scrollbar_hitbox_right = scrollbar_x + scrollbar_width + 1 * gui.scale
		scrollbar_hitbox_left = scrollbar_hitbox_right - scrollbar_hitbox_width
		scrollbar_hitbox = (
			scrollbar_hitbox_left,
			gui.panelY,
			scrollbar_hitbox_width,
			window_size[1] - gui.panelBY - gui.panelY,
		)

		w = 0
		gui.row_extra = 0
		cv = 0  # update gui.playlist_current_visible_tracks

		# Draw the background
		sdl3.SDL_SetRenderTarget(self.renderer, gui.tracklist_texture)
		sdl3.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 0)
		sdl3.SDL_RenderClear(self.renderer)

		rect = (left, gui.panelY, width, window_size[1] - (gui.panelBY + gui.panelY))

		# One averaged art-bg sample shared by all tracklist text this render
		tauon.style_overlay.tracklist_sample = tauon.style_overlay.sample_background_average(*rect)
		ddt.rect(rect, colours.playlist_panel_background)

		# This draws an optional background image
		if pl_bg:
			x = (left + highlight_width) - (pl_bg.w + round(60 * gui.scale))
			pl_bg.render(x, window_size[1] - gui.panelBY - pl_bg.h)
			ddt.pretty_rect = (x, window_size[1] - gui.panelBY - pl_bg.h, pl_bg.w, pl_bg.h)
			ddt.alpha_bg = True
		else:
			xx = left + inset_left + inset_width
			if center_mode:
				xx -= round(15 * gui.scale)
			deco.draw(ddt, xx, window_size[1] - gui.panelBY, pretty_text=True)

		# When the artist-info panel occupies the top of the tracklist column,
		# exclude its area so wheel/touch scrolling over the bio doesn't also
		# scroll the tracklist underneath it.
		artist_panel_offset = gui.artist_panel_height if gui.artist_info_panel else 0
		scroll_top = gui.panelY + artist_panel_offset
		scroll_area = (gui.playlist_left, scroll_top, gui.plw, window_size[1] - gui.panelBY - scroll_top)
		mouse_scroll = inp.mouse_wheel != 0 and window_size[1] - gui.panelBY - 1 > inp.mouse_position[
			1] > scroll_top - 2 and gui.playlist_left < inp.mouse_position[0] < gui.playlist_left + gui.plw \
				and not (self.coll(gui.pl_rect)) and not tauon.search_over.active and not tauon.radiobox.active
		touch_scroll = (
			inp.touch_scroll_y != 0
			and coll_point(inp.touch_position, scroll_area)
			and not tauon.search_over.active
			and not tauon.radiobox.active
		)
		use_smooth_scroll = (
			self.smooth_scroll.enabled()
			or touch_scroll
			or self.smooth_scroll.active("playlist")
		)
		pointer_input = (
			inp.mouse_click
			or inp.right_click
			or inp.middle_click
			or inp.mouse_down
			or inp.mouse_up
		)
		if not use_smooth_scroll and inp.k_input and not pointer_input and not mouse_scroll and not touch_scroll:
			gui.playlist_scroll_pixels = 0
		a = gui.playlist_view_length
		match a:
			case _ if a < 10:
				mx = 2
			case _ if a < 25:
				mx = 3
			case _ if a > 40:
				mx = 5
			case _:
				mx = 4

		# Mouse wheel scrolling
		if use_smooth_scroll:
			if mouse_scroll:
				self.smooth_scroll.add_wheel_motion(
					"playlist", -inp.mouse_wheel, gui.playlist_row_height * mx, SCROLL_PHYSICS_TRACKLIST_PRECISE_SCALE
				)

			if inp.touch_released and coll_point(self.smooth_scroll.start_location, scroll_area):
				self.smooth_scroll.release_touch("playlist")
			elif touch_scroll:
				self.smooth_scroll.apply_touch_drag("playlist", -inp.touch_scroll_y)

			gui.playlist_scroll_pixels += self.smooth_scroll.step_motion("playlist")
			self._apply_tracklist_pixel_scroll()

			if mouse_scroll or touch_scroll or self.smooth_scroll.active("playlist"):
				tauon.scroll_hide_timer.set()
				gui.frame_callback_list.append(TestTimer(0.9))
		elif mouse_scroll:
			gui.playlist_scroll_pixels = 0
			pctl.playlist_view_position -= self.smooth_scroll.scroll("playlist", mx)

			pctl.playlist_view_position = min(pctl.playlist_view_position, len(pctl.default_playlist))
			if pctl.playlist_view_position < 1:
				pctl.playlist_view_position = 0
				if pctl.default_playlist:
					tauon.edge_playlist2.pulse()

			tauon.scroll_hide_timer.set()
			gui.frame_callback_list.append(TestTimer(0.9))

		align_tracklist_to_row = False

		# Show notice if playlist empty
		if len(pctl.default_playlist) == 0:
			colour = alpha_mod(colours.index_text, 200)  # colours.playlist_text_missing

			top_a = gui.panelY
			if gui.artist_info_panel:
				top_a += gui.artist_panel_height

			b = window_size[1] - top_a - gui.panelBY
			half = int(top_a + (b * 0.60))

			if pl_bg:
				rect = (
					left + int(width / 2) - 80 * gui.scale, half - 10 * gui.scale, 190 * gui.scale, 60 * gui.scale)
				ddt.pretty_rect = rect
				ddt.alpha_bg = True

			ddt.text(
				(left + int(width / 2) + 10 * gui.scale, half, 2),
				_("Playlist is empty"), colour, 213, bg=colours.playlist_panel_background)
			ddt.text(
				(left + int(width / 2) + 10 * gui.scale, half + 30 * gui.scale, 2),
				_("Drag and drop files to import"), colour, 13, bg=colours.playlist_panel_background)

			ddt.pretty_rect = None
			ddt.alpha_bg = False

		# Show notice if at end of playlist
		elif pctl.playlist_view_position > len(pctl.default_playlist) - 1:
			colour = alpha_mod(colours.index_text, 200)

			top_a = gui.panelY
			if gui.artist_info_panel:
				top_a += gui.artist_panel_height

			b = window_size[1] - top_a - gui.panelBY
			half = int(top_a + (b * 0.17))

			if pl_bg:
				rect = (
					left + int(width / 2) - 60 * gui.scale, half - 5 * gui.scale, 140 * gui.scale, 30 * gui.scale)
				ddt.pretty_rect = rect
				ddt.alpha_bg = True

			ddt.text(
				(left + int(width / 2) + 10 * gui.scale, half, 2), _("End of Playlist"),
				colour, 213)

			ddt.pretty_rect = None
			ddt.alpha_bg = False

			# line = "Contains " + str(len(pctl.default_playlist)) + ' track'
			# if len(pctl.default_playlist) > 1:
			#     line += "s"
			#
			# ddt.draw_text((left + int(width / 2) + 10 * gui.scale, half + 24 * gui.scale, 2), line,
			#           colour, 12)

		# Process Input

		# type (0 is track, 1 is fold title), track_position, track_object, box, input_box,
		list_items = []
		number = 0
		render_rows = gui.playlist_view_length + 2
		row_input_right_pad = 0
		if prefs.scroll_enable:
			tracklist_right = left + gui.highlight_left + highlight_width
			row_input_right_pad = max(0, round(tracklist_right - scrollbar_hitbox_left))

		for i in range(render_rows):
			track_position = i + pctl.playlist_view_position

			# Make sure the view position is valid
			pctl.playlist_view_position = max(pctl.playlist_view_position, 0)

			# Break if we are at end of playlist
			if len(pctl.default_playlist) <= track_position or number >= render_rows:
				break

			track_object = pctl.get_track(pctl.default_playlist[track_position])
			track_id = track_object.index
			self.gui.move_on_title = False

			line_y = gui.playlist_top + gui.playlist_row_height * number - gui.playlist_scroll_pixels

			track_box = (
				left + gui.highlight_left, line_y, highlight_width,
				gui.playlist_row_height - 1)

			input_box = (
				track_box[0] + 30 * gui.scale,
				track_box[1] + 1,
				track_box[2] - 36 * gui.scale - row_input_right_pad,
				track_box[3],
			)

			# Are folder titles enabled?
			if not pctl.multi_playlist[pctl.active_playlist_viewing].hide_title and self.prefs.break_enable:
				# Is this track from a different folder than the last?
				if track_position == 0 or track_object.parent_folder_path != pctl.get_track(
						pctl.default_playlist[track_position - 1]).parent_folder_path:
					# Make folder title

					highlight = False
					drag_highlight = False

					# Shift selection highlight
					if (track_position in self.gui.shift_selection and len(self.gui.shift_selection) > 1):
						highlight = True

					# Tracks have been dropped?
					if gui.playlist_hold is True and self.coll(input_box) and inp.mouse_up:
						gui.move_on_title = True

					# Ignore click in ratings box
					click_title = (inp.mouse_click or inp.right_click or self.inp.middle_click) and self.coll(input_box)
					if click_title and gui.show_album_ratings:
						if self.inp.mouse_position[0] > (input_box[0] + input_box[2]) - 80 * gui.scale:
							click_title = False

					# Detect folder title click
					if click_title and self.inp.mouse_position[1] < window_size[1] - gui.panelBY:

						gui.request_tracklist_redraw()
						# Add folder to queue if middle click
						if self.inp.middle_click and self.tauon.is_level_zero():
							if self.inp.key_ctrl_down:  # Add as ungrouped tracks
								i = track_position
								parent = pctl.get_track(pctl.default_playlist[i]).parent_folder_path
								while i < len(pctl.default_playlist) and parent == pctl.get_track(
										pctl.default_playlist[i]).parent_folder_path:
									pctl.force_queue.append(queue_item_gen(pctl.default_playlist[i], i, pctl.pl_to_id(
										pctl.active_playlist_viewing)))
									i += 1
								self.tauon.queue_timer_set(plural=True)
								if prefs.stop_end_queue:
									pctl.stop_mode = StopMode.OFF

							else:  # Add as grouped album
								self.tauon.add_album_to_queue(track_id, track_position, pctl.pl_to_id(pctl.active_playlist_viewing))
							pctl.selected_in_playlist = track_position
							gui.shift_selection = [pctl.selected_in_playlist]
							gui.request_tracklist_redraw()

						# Play if double click:
						if inp.d_mouse_click and track_position in self.gui.shift_selection and coll_point(
							self.inp.last_click_location, (input_box)):
							gui.click_time -= 1.5
							align_tracklist_to_row = True
							pctl.jump(track_id, track_position)
							line_hit = False
							inp.mouse_click = False

							if prefs.album_mode:
								tauon.goto_album(pctl.playlist_playing_position)

						# Show selection menu if right clicked after select
						if inp.right_click:
							self.tauon.folder_menu.activate(
								MenuTrackRef(track_id, track_position, pctl.pl_to_id(pctl.active_playlist_viewing))
							)
							gui.selection_stage = 2
							gui.request_tracklist_redraw()

							if track_position not in self.gui.shift_selection:
								self.gui.shift_selection = []
								pctl.selected_in_playlist = track_position
								u = track_position
								while u < len(pctl.default_playlist) and track_object.parent_folder_path == \
										pctl.master_library[
											pctl.default_playlist[u]].parent_folder_path:
									self.gui.shift_selection.append(u)
									u += 1

						# Add folder to selection if clicked
						if (
							inp.mouse_click
							and not (prefs.scroll_enable and self.coll(scrollbar_hitbox) and not gui.album_rating_hover)
							and not gui.side_drag
						):
							self.inp.quick_drag = True
							gui.set_drag_source()

							if not tauon.pl_is_locked(pctl.active_playlist_viewing) or self.inp.key_shift_down:
								self.gui.playlist_hold = True

							gui.selection_stage = 1
							temp = tauon.get_folder_tracks_local(track_position)
							pctl.selected_in_playlist = track_position

							if len(self.gui.shift_selection) > 0 and self.inp.key_shift_down:
								if track_position < self.gui.shift_selection[0]:
									for item in reversed(temp):
										if item not in self.gui.shift_selection:
											self.gui.shift_selection.insert(0, item)
								else:
									for item in temp:
										if item not in self.gui.shift_selection:
											self.gui.shift_selection.append(item)

							else:
								self.gui.shift_selection = copy.copy(temp)

					# Should draw drag highlight?

					if self.inp.mouse_down and self.gui.playlist_hold and self.coll(input_box) and track_position not in self.gui.shift_selection:
						if len(self.gui.shift_selection) < 2 and not self.inp.key_shift_down:
							pass
						else:
							drag_highlight = True

					# Something to do with quick search, I forgot
					if pctl.selected_in_playlist > track_position + 1:
						gui.row_extra += 1

					list_items.append(
						(1, track_position, track_object, track_box, input_box, highlight, number, drag_highlight, False))
					number += 1

			if number >= render_rows:
				break

			# Standard track ---------------------------------------------------------------------
			playing = False

			highlight = False
			drag_highlight = False
			line_y = gui.playlist_top + gui.playlist_row_height * number - gui.playlist_scroll_pixels

			track_box = (
				left + gui.highlight_left, line_y, highlight_width,
				gui.playlist_row_height - 1)

			input_box = (
				track_box[0] + 30 * gui.scale,
				track_box[1] + 1,
				track_box[2] - 36 * gui.scale - row_input_right_pad,
				track_box[3],
			)

			# Test if line has mouse over or been clicked
			line_over = False
			line_hit = False
			if self.coll(input_box) and self.inp.mouse_position[1] < window_size[1] - gui.panelBY:
				line_over = True
				if (inp.mouse_click or inp.right_click or (self.inp.middle_click and self.tauon.is_level_zero())):
					line_hit = True
					gui.request_tracklist_redraw()
				else:
					line_hit = False
			else:
				line_hit = False
				line_over = False

			# Prevent click if near scroll bar
			if prefs.scroll_enable and self.coll(scrollbar_hitbox) and not gui.album_rating_hover:
				line_hit = False

			# Double click to play
			if self.inp.key_shift_down is False and inp.d_mouse_click and line_hit and track_position == pctl.selected_in_playlist and coll_point(
					self.inp.last_click_location, input_box):

				align_tracklist_to_row = True
				pctl.jump(track_id, track_position)

				gui.click_time -= 1.5
				self.inp.quick_drag = False
				self.inp.mouse_down = False
				self.inp.mouse_up = False
				line_hit = False

				if prefs.album_mode:
					tauon.goto_album(pctl.playlist_playing_position)

			if len(pctl.track_queue) > 0 and pctl.track_queue[pctl.queue_step] == track_id:
				if track_position == pctl.playlist_playing_position and pctl.active_playlist_viewing == pctl.active_playlist_playing:
					this_line_playing = True

			# Add to queue on middle click
			if self.inp.middle_click and line_hit:
				pctl.force_queue.append(
					queue_item_gen(track_id,
					track_position, pctl.pl_to_id(pctl.active_playlist_viewing)))
				pctl.selected_in_playlist = track_position
				self.gui.shift_selection = [pctl.selected_in_playlist]
				gui.request_tracklist_redraw()
				self.tauon.queue_timer_set()
				if prefs.stop_end_queue:
					pctl.stop_mode = StopMode.OFF

			# Deselect multiple if one clicked on and not dragged (mouse up is probably a bit of a hacky way of doing it)
			if len(self.gui.shift_selection) > 1 and self.inp.mouse_up and line_over and not self.inp.key_shift_down and not self.inp.key_ctrl_down and point_proximity_test(
					gui.drag_source_position, self.inp.mouse_position, 15):  # and not self.gui.playlist_hold:
				self.gui.shift_selection = [track_position]
				pctl.selected_in_playlist = track_position
				gui.request_tracklist_redraw()
				gui.request_frame()

			# # Begin drag block selection
			# if self.inp.mouse_down and line_over and track_position in self.gui.shift_selection and len(self.gui.shift_selection) > 1:
			#     if not tauon.pl_is_locked(pctl.active_playlist_viewing):
			#         self.gui.playlist_hold = True
			#     elif self.inp.key_shift_down:
			#         self.gui.playlist_hold = True

			# Begin drag single track
			if inp.mouse_click and line_hit and not gui.side_drag:
				self.inp.quick_drag = True
				gui.set_drag_source()

			# Shift Move Selection
			if gui.move_on_title or (self.inp.mouse_up and self.gui.playlist_hold is True and self.coll((
					left + gui.highlight_left, line_y, highlight_width - row_input_right_pad, gui.playlist_row_height))):

				if len(self.gui.shift_selection) > 1 or self.inp.key_shift_down:
					if track_position not in self.gui.shift_selection:  # p_track != self.gui.playlist_hold_position and

						if len(self.gui.shift_selection) == 0:
							ref = pctl.default_playlist[self.gui.playlist_hold_position]
							pctl.default_playlist[self.gui.playlist_hold_position] = "old"
							if gui.move_on_title:
								pctl.default_playlist.insert(track_position, "new")
							else:
								pctl.default_playlist.insert(track_position + 1, "new")
							pctl.default_playlist.remove("old")
							pctl.selected_in_playlist = pctl.default_playlist.index("new")
							pctl.default_playlist[pctl.default_playlist.index("new")] = ref

							gui.request_tracklist_redraw()


						else:
							ref = []
							gui.selection_stage = 2
							for item in self.gui.shift_selection:
								ref.append(pctl.default_playlist[item])

							for item in self.gui.shift_selection:
								pctl.default_playlist[item] = "old"

							for item in self.gui.shift_selection:
								if gui.move_on_title:
									pctl.default_playlist.insert(track_position, "new")
								else:
									pctl.default_playlist.insert(track_position + 1, "new")

							for b in reversed(range(len(pctl.default_playlist))):
								if pctl.default_playlist[b] == "old":
									del pctl.default_playlist[b]
							self.gui.shift_selection = []
							for b in range(len(pctl.default_playlist)):
								if pctl.default_playlist[b] == "new":
									self.gui.shift_selection.append(b)
									pctl.default_playlist[b] = ref.pop(0)

							pctl.selected_in_playlist = self.gui.shift_selection[0]
							gui.request_tracklist_redraw()

						tauon.reload_albums(True)
						pctl.notify_database_changed()

			# Test show drag indicator
			if self.inp.mouse_down and self.gui.playlist_hold and self.coll(input_box) and track_position not in self.gui.shift_selection:
				if len(self.gui.shift_selection) > 1 or self.inp.key_shift_down:
					drag_highlight = True

			# Right click menu activation
			if self.inp.right_click and line_hit and self.inp.mouse_position[0] > gui.playlist_left + 10:
				if len(self.gui.shift_selection) > 1 and track_position in self.gui.shift_selection:
					self.tauon.selection_menu.activate(pctl.default_playlist[track_position])
					gui.selection_stage = 2
				else:
					self.tauon.track_menu.activate(
						MenuTrackRef(
							pctl.default_playlist[track_position],
							track_position,
							pctl.pl_to_id(pctl.active_playlist_viewing),
						)
					)
					gui.request_tracklist_redraw()
					gui.request_frame()

					if track_position not in self.gui.shift_selection:
						pctl.selected_in_playlist = track_position
						self.gui.shift_selection = [pctl.selected_in_playlist]

			if line_over and inp.mouse_click:
				if track_position in self.gui.shift_selection:
					pass
				else:
					gui.selection_stage = 2
					if self.inp.key_shift_down:
						start_s = track_position
						end_s = pctl.selected_in_playlist
						if end_s < start_s:
							end_s, start_s = start_s, end_s
						for y in range(start_s, end_s + 1):
							if y not in self.gui.shift_selection:
								self.gui.shift_selection.append(y)
						self.gui.shift_selection.sort()
						pctl.selected_in_playlist = track_position
					elif self.inp.key_ctrl_down:
						self.gui.shift_selection.append(track_position)
					else:
						pctl.selected_in_playlist = track_position
						self.gui.shift_selection = [pctl.selected_in_playlist]

				if not tauon.pl_is_locked(pctl.active_playlist_viewing) or self.inp.key_shift_down:
					self.gui.playlist_hold = True
					self.gui.playlist_hold_position = track_position

			# Activate drag if shift key down
			if self.inp.quick_drag and tauon.pl_is_locked(pctl.active_playlist_viewing) and self.inp.mouse_down:
				if self.inp.key_shift_down:
					self.gui.playlist_hold = True
				else:
					self.gui.playlist_hold = False

			# Multi Select Highlight
			if track_position in self.gui.shift_selection or track_position == pctl.selected_in_playlist:
				highlight = True

			if pctl.playing_state != PlayingState.URL_STREAM and len(pctl.track_queue) > 0 \
			and pctl.track_queue[pctl.queue_step] == pctl.default_playlist[track_position]:
				if track_position == pctl.playlist_playing_position and pctl.active_playlist_viewing == pctl.active_playlist_playing:
					playing = True

			list_items.append(
				(0, track_position, track_object, track_box, input_box, highlight, number, drag_highlight, playing))
			number += 1

			if number >= render_rows:
				break
		# ---------------------------------------------------------------------------------------

		if align_tracklist_to_row:
			gui.playlist_scroll_pixels = 0

		# For every track in view
		# for i in range(gui.playlist_view_length + 1):
		gui.tracklist_bg_is_light = test_lumi(colours.playlist_panel_background) < 0.55
		album_art_rendered_blocks: set[int] = set()
		album_art_column_draws: list[tuple[TrackClass, tuple[float, float], int, int]] = []

		for type, track_position, tr, track_box, input_box, highlight, number, drag_highlight, playing in list_items:
			line_y = gui.playlist_top + gui.playlist_row_height * number - gui.playlist_scroll_pixels
			ddt.text_background_colour = colours.playlist_panel_background

			if type == 1:
				# Is type ALBUM TITLE
				# separator = " - "
				# if prefs.row_title_separator_type == 1:
				# 	separator = " ‒ "  # noqa: RUF003 - The separator is correct here
				# if prefs.row_title_separator_type == 2:
				# 	separator = " ⦁ "  # noqa: RUF003 - The separator is correct here
				separator = " ‒ "

				date = ""
				duration = ""

				line = tr.parent_folder_name

				# Use folder name if mixed/singles?
				if len(pctl.default_playlist) > track_position + 1 and pctl.get_track(
						pctl.default_playlist[track_position + 1]).album != tr.album and \
						pctl.get_track(pctl.default_playlist[track_position + 1]).parent_folder_path == tr.parent_folder_path:
					line = tr.parent_folder_name
				else:
					if tr.album_artist and tr.album:
						line = tr.album_artist + separator + tr.album

						if prefs.left_align_album_artist_title and not True:
							album_artist_mode = True
							line = tr.album

					if len(line) < 6 and "CD" in line:
						line = tr.album

					if prefs.append_date and year_search.search(tr.date):
						year = d_date_display2(tr)
						if not year:
							year = d_date_display(tr)
						date = "(" + year + ")"

					if line.endswith(")"):
						b = line.split("(")
						if len(b) > 1 and len(b[1]) <= 11:

							match = year_search.search(b[1])

							if match:
								line = b[0]
								date = "(" + b[1]
					elif line.startswith("("):
						b = line.split(")")
						if len(b) > 1 and len(b[0]) <= 11:

							match = year_search.search(b[0])

							if match:
								line = b[1]
								date = b[0] + ")"

					if "(" in line and year_search.search(line):
						date = ""

				line = line.replace(" - ", separator)

				qq = 0
				d_date = date
				title_line = line

				# Calculate folder duration

				q = track_position

				total_time = 0
				while q < len(pctl.default_playlist):
					if pctl.get_track(pctl.default_playlist[q]).parent_folder_path != tr.parent_folder_path:
						break

					total_time += pctl.get_track(pctl.default_playlist[q]).length

					q += 1
					qq += 1

				if qq > 1:
					duration = " [ " + get_display_time(total_time) + " ]" # Hair space inside brackets for better visual spacing

				if prefs.append_total_time:
					date += duration

				folder_title_right_pad = round(3 * gui.scale) if gui.rsp_on_left else 0
				ex = left + gui.highlight_left + highlight_width - 7 * gui.scale
				ex -= folder_title_right_pad

				height = line_y + gui.playlist_row_height - 19 * gui.scale  # gui.pl_title_y_offset

				# Over the art background the title line gets the hue mix-in
				# and lightness boost like the panel buttons do, from the
				# tracklist's shared averaged sample
				folder_title_colour = tauon.style_overlay.tint_from_sample(
					colours.folder_title,
					tauon.style_overlay.tracklist_sample,
					0.2, colours.playlist_panel_background)

				star_offset = 0
				if gui.show_album_ratings:
					star_offset = round(72 * gui.scale)
					ex -= star_offset
					self.tauon.draw_rating_widget(
						ex + 6 * gui.scale,
						height,
						tr,
						album=True,
						allow_input=not gui.scrollbar_active,
					)

				light_offset = 0
				if colours.lm:
					light_offset = 3 * gui.scale
				ex -= light_offset

				if qq > 1:
					ex += 1 * gui.scale

				ddt.text_background_colour = colours.playlist_panel_background

				if gui.scale == 2:
					height += 1

				if highlight:
					ddt.text_background_colour = alpha_blend(
						colours.row_select_highlight,
						colours.playlist_panel_background)
					ddt.rect_a(
						(left + gui.highlight_left, gui.playlist_top + gui.playlist_row_height * number - gui.playlist_scroll_pixels),
						(highlight_width, gui.playlist_row_height), colours.row_select_highlight)

				#logging.info(d_date) # date of album release / release year
				#logging.info(tr.parent_folder_name) # folder name
				#logging.info(tr.album)
				#logging.info(tr.artist)
				#logging.info(tr.album_artist)
				#logging.info(tr.genre)

				if prefs.row_title_format == 2:
					separator = " | "

					start_offset = round(15 * gui.scale)
					xx = left + gui.highlight_left + start_offset
					ww = highlight_width

					was = False
					run = 0
					duration = get_display_time(total_time)
					colour = copy.deepcopy(folder_title_colour)
					colour.a = max(colour.a - 50, 0)

					if prefs.append_total_time and duration:
						was = True
						run += ddt.text(
							(ex - run, height, 1), duration, colour,
							gui.row_font_size + gui.pl_title_font_offset)
					if d_date:
						if was:
							run += ddt.text(
								(ex - run, height, 1), separator, colour,
								gui.row_font_size + gui.pl_title_font_offset)
						was = True
						run += ddt.text(
							(ex - run, height, 1), d_date.rstrip(")").lstrip("("), colour,
							gui.row_font_size + gui.pl_title_font_offset)
					if tr.genre and prefs.row_title_genre:
						if was:
							run += ddt.text(
								(ex - run, height, 1), separator, colour,
								gui.row_font_size + gui.pl_title_font_offset)
						was = True
						run += ddt.text(
							(ex - run, height, 1), tr.genre, colour,
							gui.row_font_size + gui.pl_title_font_offset)

					w2 = ddt.text((xx, height), title_line, folder_title_colour, gui.row_font_size + gui.pl_title_font_offset, max_w=ww - (start_offset + run + round(10 * gui.scale) + folder_title_right_pad))
				else:
					date_w = 0
					if date:
						date_w = ddt.text(
							(ex, height, 1), date, folder_title_colour,
							gui.row_font_size + gui.pl_title_font_offset)
						date_w += 4 * gui.scale
						if qq > 1:
							date_w -= 1 * gui.scale

					aa = 0

					ft_width = ddt.get_text_w(line, gui.row_font_size + gui.pl_title_font_offset)
					left_align = highlight_width - date_w - 13 * gui.scale - light_offset
					left_align -= star_offset
					extra = aa
					left_align -= extra

					if ft_width > left_align:
						date_w += 19 * gui.scale
						ddt.text(
							(left + gui.highlight_left + 8 * gui.scale + extra, height), line,
							folder_title_colour,
							gui.row_font_size + gui.pl_title_font_offset,
							highlight_width - date_w - extra - star_offset - folder_title_right_pad)
					else:
						ddt.text(
							(ex - date_w, height, 1), line,
							folder_title_colour,
							gui.row_font_size + gui.pl_title_font_offset)

				# -----

				# Draw separation line below title
				ddt.rect(
					(left + gui.highlight_left, line_y + gui.playlist_row_height - 1 * gui.scale, highlight_width,
					1 * gui.scale), colours.folder_line)

				# Draw blue highlight insert line
				if drag_highlight:
					ddt.rect(
						[left + gui.highlight_left, line_y + gui.playlist_row_height - 1 * gui.scale,
						highlight_width, 3 * gui.scale], ColourRGBA(135, 145, 190, 255))

				if gui.set_mode:
					start = (gui.pl_st_left + 2) * gui.scale
					if center_mode:
						start = inset_left
					elif gui.playlist_left:
						start += gui.playlist_left

					run = start
					end = start + gui.plw
					if center_mode:
						end = highlight_width + start

					for item in gui.pl_st:
						column_width = min(item[1], end - run)
						if run > end - 50 * gui.scale:
							break
						if item[0] == "Album Art":
							self._queue_previous_album_art_for_folder_title(
								track_position,
								line_y,
								run,
								column_width,
								album_art_rendered_blocks,
								album_art_column_draws)
						run += item[1]

				continue

			# Draw playing highlight
			if playing:
				ddt.rect(track_box, colours.row_playing_highlight)
				ddt.text_background_colour = alpha_blend(colours.row_playing_highlight, ddt.text_background_colour)

			# Blue drop line
			if drag_highlight:  # self.gui.playlist_hold_position != p_track:

				ddt.rect(
					[left + gui.highlight_left, line_y + gui.playlist_row_height - 1 * gui.scale, highlight_width,
					3 * gui.scale], ColourRGBA(125, 105, 215, 255))

			# Highlight
			if highlight:
				ddt.rect_a(
					(left + gui.highlight_left, line_y), (highlight_width, gui.playlist_row_height),
					colours.row_select_highlight)

				ddt.text_background_colour = alpha_blend(colours.row_select_highlight, ddt.text_background_colour)

			if not self.pctl.multi_playlist[self.pctl.active_playlist_viewing].hide_title and track_position > 0 and track_position < len(pctl.default_playlist) and tr.disc_number and tr.disc_number != "0" and tr.album and tr.disc_number != pctl.get_track(pctl.default_playlist[track_position - 1]).disc_number \
					and tr.album == pctl.get_track(pctl.default_playlist[track_position - 1]).album and tr.parent_folder_path == pctl.get_track(pctl.default_playlist[track_position - 1]).parent_folder_path:
				# Draw disc change line
				ddt.rect(
					(left + gui.highlight_left, line_y + 0 * gui.scale, highlight_width,
					1 * gui.scale), colours.folder_line)

			if not gui.set_mode:
				left_trim = round(9 * gui.scale) if gui.custom_mode else 0
				tauon.line_render(
					tr, track_position, gui.playlist_text_offset + line_y,
					playing, 255, left + inset_left - left_trim, inset_width + left_trim, 1, line_y)
			else:
				# NEE ---------------------------------------------------------
				n_track = tr
				p_track = track_position
				this_line_playing = playing

				start = (gui.pl_st_left + 2) * gui.scale

				if center_mode:
					start = inset_left

				elif gui.playlist_left:
					start += gui.playlist_left

				run = start
				end = start + gui.plw

				if center_mode:
					end = highlight_width + start

				# gui.tracklist_center_mode = center_mode
				# gui.tracklist_inset_left = inset_left - round(20 * gui.scale)
				# gui.tracklist_inset_width = inset_width + round(20 * gui.scale)

				magnet_layout, magnet_seps = self.compute_magnet_layout(start, end, n_track, p_track)

				for h, item in enumerate(gui.pl_st):
					wid = item[1] - 20 * gui.scale
					column_width = min(item[1], end - run)
					y = gui.playlist_text_offset + gui.playlist_top + gui.playlist_row_height * number - gui.playlist_scroll_pixels
					ry = gui.playlist_top + gui.playlist_row_height * number - gui.playlist_scroll_pixels

					if run > end - 50 * gui.scale and h not in magnet_layout:
						# Magnet-packed text lives within the group's clamped span, so
						# it stays on-screen even when this column's own run does not.
						break

					if len(gui.pl_st) == h + 1:
						wid -= 6 * gui.scale

					if item[0] == "Album Art":
						self._queue_album_art_column(
							track_position,
							ry,
							run,
							column_width,
							album_art_rendered_blocks,
							album_art_column_draws)

					if item[0] == "Rating":
						if wid > 45 * gui.scale:
							yy = ry + (gui.playlist_row_height // 2) - (6 * gui.scale)
							self.tauon.draw_rating_widget(run + 4 * gui.scale, yy, n_track)

					if item[0] == "Starline":
						total = self.star_store.get_by_object(n_track)

						if total > 0 and n_track.length != 0 and wid > 0:
							ratio = total / n_track.length
							if ratio > 0.55:
								star_x = int(ratio * (4 * gui.scale))
								star_x = min(star_x, wid)

								colour = colours.star_line
								if playing and colours.star_line_playing is not None:
									colour = colours.star_line_playing

								sy = (gui.playlist_top + gui.playlist_row_height * number - gui.playlist_scroll_pixels) + int(
									gui.playlist_row_height / 2)
								ddt.rect((run + 4 * gui.scale, sy, star_x, 1 * gui.scale), colour)
					else:
						text = ""
						font = gui.row_font_size
						colour = ColourRGBA(200, 200, 200, 255)
						norm_colour = colour
						y_off = 0
						if item[0] == "Title":
							colour = colours.title_text
							if n_track.title:
								text = n_track.title
							else:
								text = n_track.filename
							#     colour = colours.index_playing
							if this_line_playing is True:
								colour = colours.title_playing

						elif item[0] == "Artist":
							text = n_track.artist
							colour = colours.artist_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.artist_playing
						elif item[0] == "Album":
							text = n_track.album
							colour = colours.album_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.album_playing
						elif item[0] == "Album Artist":
							text = n_track.album_artist
							if not text and prefs.column_aa_fallback_artist:
								text = n_track.artist
							colour = colours.artist_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.artist_playing
						elif item[0] == "Composer":
							text = n_track.composer
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "Comment":
							text = n_track.comment.replace("\n", " ").replace("\r", " ")
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "S":
							if n_track.lfm_scrobbles > 0:
								text = str(n_track.lfm_scrobbles)

							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "#":

							if prefs.use_absolute_track_index and pctl.multi_playlist[pctl.active_playlist_viewing].hide_title:
								text = str(p_track)
							else:
								text = tauon.track_number_process(n_track.track_number)

							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "Date":
							text = n_track.date
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "Filepath":
							text = clean_string(n_track.fullpath)
							colour = colours.index_text
							norm_colour = colour
						elif item[0] == "Filename":
							text = clean_string(n_track.filename)
							colour = colours.index_text
							norm_colour = colour
						elif item[0] == "Disc":
							text = str(n_track.disc_number)
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "Codec":
							text = n_track.file_ext
							if text == "JELY" and tr.container is not None:
								text = tr.container
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "Lyrics":
							text = ""
							if n_track.lyrics:
								text = "✓"
							if n_track.synced:
								text = "⧗"
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "CUE":
							text = ""
							if n_track.is_cue:
								text = "✓"
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "Genre":
							text = n_track.genre
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "ID":
							text = str(n_track.index)
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "=/=":
							text = get_modify_date_string( n_track.modified_time )
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "Bitrate":
							text = str(n_track.bitrate)
							if text == "0":
								text = ""

							ex = n_track.file_ext
							if n_track.container is not None:
								ex = n_track.container
							if ex in ("FLAC", "WAV", "APE"):
								text = str(round(n_track.samplerate / 1000, 1)).rstrip("0").rstrip(".") + "|" + str(
									n_track.bit_depth)
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing
						elif item[0] == "Time":
							text = get_display_time(n_track.length)
							colour = colours.bar_time
							norm_colour = colour
							# colour = colours.time_text
							if this_line_playing is True:
								colour = colours.time_text
						elif item[0] == "❤":
							# col love
							u = 5 * gui.scale
							yy = ry + (gui.playlist_row_height // 2) - (5 * gui.scale)
							if gui.scale == 1.25:
								yy += 1

							if tauon.get_love(n_track):
								j = 0  # justify right
								if run < start + 100 * gui.scale:
									j = 1  # justify left
								self.tauon.display_you_heart(run + 6 * gui.scale, yy, j)
								u += 18 * gui.scale

							count = 0
							for name in n_track.lfm_friend_likes:
								spacing = 6 * gui.scale
								if u + (gui.heart_row_icon.w + spacing) * count > wid + 7 * gui.scale:
									break

								x = run + u + (gui.heart_row_icon.w + spacing) * count

								j = 0  # justify right
								if run < start + 100 * gui.scale:
									j = 1  # justify left

								self.tauon.display_friend_heart(x, yy, name, j)
								count += 1

							# if n_track.track_number == 1 or n_track.track_number == "1":
							#     ss = wid - (wid % 15)
							#     tauon.gall_ren.render(n_track, (run, y), ss)


						elif item[0] == "P":
							ratio = 0
							total = self.star_store.get_by_object(n_track)
							if total > 0 and n_track.length > 2:
								if n_track.length > 15:
									total += 2
								ratio = total / (n_track.length - 1)

							text = str(int(ratio))
							if text == "0":
								text = ""
							colour = colours.index_text
							norm_colour = colour
							if this_line_playing is True:
								colour = colours.index_playing

						if prefs.dim_art and prefs.album_mode and \
								n_track.parent_folder_name \
								!= pctl.master_library[pctl.track_queue[pctl.queue_step]].parent_folder_name:
							colour = alpha_mod(colour, 150)
						if n_track.found is False:
							colour = colours.playlist_text_missing

						if text:
							if item[0] in colours.column_colours:
								colour = colours.column_colours[item[0]]

							if this_line_playing and item[0] in colours.column_colours_playing:
								colour = colours.column_colours_playing[item[0]]

							text_x = run + 6 * gui.scale
							if h in magnet_layout:
								# Magnet Mode: draw packed after the previous column's text
								text_x, wid = magnet_layout[h]
							elif run + 6 * gui.scale + wid > end:
								wid = end - run - 40 * gui.scale
								if center_mode:
									wid += 25 * gui.scale

							col_left = text_x - 6 * gui.scale
							wid = max(0, wid)

							# Grey column text picks up a hint of the art hue
							# over the art background (coloured text passes
							# through; no lightness boost for row text), from
							# the tracklist's shared averaged sample
							colour = tauon.style_overlay.tint_from_sample(
								colour, tauon.style_overlay.tracklist_sample, 0.2)

							# # Hacky. Places a dark background behind light text for readability over mascot
							# if pl_bg and gui.set_mode and colour_value(norm_colour) < 400 and not colours.lm:
							# 	w, h = ddt.get_text_wh(text, font, wid)
							# 	quick_box = [run + round(5 * gui.scale), y + y_off, w + round(2 * gui.scale), h]
							# 	if coll_rect((left + width - pl_bg.w - 60 * gui.scale, window_size[1] - gui.panelBY - pl_bg.h, pl_bg.w, pl_bg.h), quick_box):
							# 		quick_box = (run, ry, item[1], gui.playlist_row_height)
							# 		ddt.rect(quick_box, [0, 0, 0, 40], True)
							# 		ddt.rect(quick_box, alpha_mod(colours.playlist_panel_background, 150), True)

							ddt.text(
								(text_x, y + y_off),
								text,
								colour,
								font,
								max_w=wid)

							# Magnet Mode: draw a " - " separator after this column when
							# the next packed column shares its colour (readability).
							if h in magnet_seps:
								ddt.text(
									(magnet_seps[h], y + y_off),
									" - ",
									colour,
									font)

							if ddt.was_truncated:
								#logging.info(text)
								rect = (col_left, y, wid - 1, gui.playlist_row_height - 1)
								gui.heart_fields.append(rect)

								if self.coll(rect):
									self.tauon.columns_tool_tip.set(col_left - 7 * gui.scale, y, text, font, rect)

					run += item[1]

			# -----------------------------------------------------------------
			# Count the number if visible tracks (used by Show Current function)
			if gui.playlist_top + gui.playlist_row_height * w > window_size[0] - gui.panelBY - gui.playlist_row_height:
				pass
			else:
				cv += 1

			# w += 1
			# if w > gui.playlist_view_length:
			#     break

		for track, location, art_size, draw_height in album_art_column_draws:
			tauon.gall_ren.render(track, location, art_size, max_height=draw_height)

		# This is a bit hacky since its only generated after drawing
		# Used to keep track of how many tracks are actually in view
		gui.playlist_current_visible_tracks = cv
		gui.playlist_current_visible_tracks_id = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int

		if (inp.right_click and gui.playlist_top + 5 * gui.scale + gui.playlist_row_height * len(list_items) <
				self.inp.mouse_position[1] < window_size[1] - 55 and width + left > self.inp.mouse_position[0] > gui.playlist_left + 15):
			tauon.playlist_menu.activate()

		sdl3.SDL_SetRenderTarget(self.renderer, gui.main_texture)
		self._blit_tracklist()

		if self.inp.mouse_down is False:
			self.gui.playlist_hold = False

		ddt.pretty_rect = None
		ddt.alpha_bg = False

	def _blit_tracklist(self) -> None:
		"""Copy the tracklist texture to the main texture, constrained to the
		tracklist's region (the widget rect in Custom Layout, the playlist
		viewport in the preset path) so partially scrolled rows can't draw
		over — or show through — the surrounding panels."""
		gui = self.gui
		if self._clip_rect is not None:
			cx, cy, cw, ch = self._clip_rect
			bar_top = cy
		else:
			cx = gui.playlist_left
			cy = gui.panelY
			cw = gui.plw
			ch = self.window_size[1] - gui.panelY - gui.panelBY
			bar_top = cy
			if gui.artist_info_panel:
				bar_top += gui.artist_panel_height
		# The columns header bar draws translucent over the art background,
		# so rows scrolled up behind it would show through; crop them out
		if gui.set_mode and gui.set_bar and not gui.combo_mode:
			cut = bar_top + gui.set_height - cy
			cy += cut
			ch -= cut
		r = sdl3.SDL_FRect(round(cx), round(cy), round(cw), round(ch))
		sdl3.SDL_RenderTexture(self.renderer, self.gui.tracklist_texture, r, r)

	def cache_render(self) -> None:
		self.update_album_rating_hover()
		self._blit_tracklist()

	def update_album_rating_hover(self) -> None:
		gui = self.gui
		gui.album_rating_hover = False

		if (
			not gui.show_album_ratings
			or gui.combo_mode
			or not gui.show_playlist
			or not self.prefs.break_enable
			or not self.pctl.multi_playlist
			or self.pctl.active_playlist_viewing >= len(self.pctl.multi_playlist)
			or self.pctl.multi_playlist[self.pctl.active_playlist_viewing].hide_title
		):
			return

		boundary = 3 * gui.scale
		if not gui.playlist_top + boundary < self.inp.mouse_position[1] <= self.window_size[1] - gui.panelBY - boundary:
			return

		track_position = max(self.pctl.playlist_view_position, 0)
		number = 0
		render_rows = gui.playlist_view_length + 2
		playlist_length = len(self.pctl.default_playlist)

		while track_position < playlist_length and number < render_rows:
			if self._folder_title_would_appear(track_position):
				line_y = gui.playlist_top + gui.playlist_row_height * number - gui.playlist_scroll_pixels
				rating_x = (
					gui.playlist_left
					+ gui.tracklist_highlight_left
					+ gui.tracklist_highlight_width
					- 7 * gui.scale
					- (round(3 * gui.scale) if gui.rsp_on_left else 0)
					- round(72 * gui.scale)
					+ 6 * gui.scale
				)
				rating_y = line_y + gui.playlist_row_height - 19 * gui.scale
				rating_rect = (
					rating_x - round(5 * gui.scale),
					rating_y - round(4 * gui.scale),
					round(80 * gui.scale),
					round(24 * gui.scale),
				)
				if self.coll(rating_rect):
					gui.album_rating_hover = True
					return
				number += 1

			number += 1
			track_position += 1
class RenamePlaylistBox:

	def __init__(self, tauon: _PlaylistApp) -> None:
		self.tauon            = tauon
		self.ddt              = tauon.ddt
		self.gui              = tauon.gui
		self.inp              = tauon.inp
		self.coll             = tauon.coll
		self.pctl             = tauon.pctl
		self.colours          = tauon.colours
		self.window_size      = tauon.window_size
		self.thread_manager   = tauon.thread_manager
		self.rename_text_area = tauon.rename_text_area
		self.x = 300
		self.y = 300
		self.playlist_index = 0

		self.edit_generator = False
		# When set, the box renames something other than a playlist: on commit
		# the callback receives the entered text (skipped when empty) and the
		# playlist paths are bypassed. Cleared after every commit and whenever
		# the box opens for a playlist. Used by the Custom Layout slot rename.
		self.done_callback: Callable[[str], None] | None = None

	def toggle_edit_gen(self) -> None:
		self.edit_generator ^= True
		if self.edit_generator:

			if len(self.rename_text_area.text) > 0:
				self.pctl.multi_playlist[self.playlist_index].title = self.rename_text_area.text

			pl = self.playlist_index
			id = self.pctl.pl_to_id(pl)

			text = self.pctl.gen_codes.get(id)
			if not text:
				text = ""

			self.rename_text_area.set_text(text)
			self.rename_text_area.highlight_none()

			self.gui.regen_single = self.tauon.rename_playlist_box.playlist_index
			self.thread_manager.ready("worker")
		else:
			self.rename_text_area.set_text(self.pctl.multi_playlist[self.playlist_index].title)
			self.rename_text_area.highlight_none()
			# self.rename_text_area.highlight_all()

	def render(self) -> None:
		if self.gui.level_2_click:
			self.inp.mouse_click = True
		self.gui.level_2_click = False

		if self.inp.key_tab_press and self.done_callback is None:
			self.toggle_edit_gen()

		text_w = self.ddt.get_text_w(self.rename_text_area.text, 315)
		min_w = max(250 * self.gui.scale, text_w + 50 * self.gui.scale)

		# Keep the box on-screen horizontally - its x can come from a menu-item
		# callback's mouse position, which may sit near (or past) the edge.
		margin = round(10 * self.gui.scale)
		self.x = max(margin, min(self.x, self.window_size[0] - min_w - margin))

		rect = [self.x, self.y, min_w, 37 * self.gui.scale]
		bg = ColourRGBA(40, 40, 40, 255)
		if self.edit_generator:
			bg = ColourRGBA(70, 50, 100, 255)
		self.ddt.text_background_colour = bg

		# Draw background
		self.ddt.rect(rect, bg)

		# Draw text entry
		self.rename_text_area.draw(
			rect[0] + 10 * self.gui.scale, rect[1] + 8 * self.gui.scale, self.colours.alpha_grey(250),
			width=350 * self.gui.scale, font=315)

		# Draw accent
		rect2 = [self.x, self.y + rect[3] - 4 * self.gui.scale, min_w, 4 * self.gui.scale]
		self.ddt.rect(rect2, ColourRGBA(255, 255, 255, 60))

		if self.edit_generator:
			pl = self.playlist_index
			id = self.pctl.pl_to_id(pl)
			self.pctl.gen_codes[id] = self.rename_text_area.text

			if self.inp.input_text or self.inp.key_backspace_press:
				self.gui.regen_single = self.tauon.rename_playlist_box.playlist_index
				self.thread_manager.ready("worker")

				# self.regenerate_playlist(self.tauon.rename_playlist_box.playlist_index)
			# if self.gui.gen_code_errors:
			#     del_icon.render(rect[0] + rect[2] - 21 * self.gui.scale, rect[1] + 10 * self.gui.scale, ColourRGBA(255, 70, 70, 255))
			self.ddt.text_background_colour = ColourRGBA(4, 4, 4, 255)
			hint_rect = [rect[0], rect[1] + round(50 * self.gui.scale), round(560 * self.gui.scale), round(300 * self.gui.scale)]

			if hint_rect[0] + hint_rect[2] > self.window_size[0]:
				hint_rect[0] = self.window_size[0] - hint_rect[2]

			self.ddt.rect(hint_rect, ColourRGBA(0, 0, 0, 245))
			xx0 = hint_rect[0] + round(15 * self.gui.scale)
			xx = hint_rect[0] + round(25 * self.gui.scale)
			xx2 = hint_rect[0] + round(85 * self.gui.scale)
			yy = hint_rect[1] + round(10 * self.gui.scale)

			text_colour = ColourRGBA(150, 150, 150, 255)
			title_colour = text_colour
			code_colour = ColourRGBA(250, 250, 250, 255)
			hint_colour = ColourRGBA(110, 110, 110, 255)

			title_font = 311
			code_font = 311
			hint_font = 310

			# self.ddt.pretty_rect = hint_rect

			self.ddt.text(
				(xx0, yy), _("Type codes separated by spaces. Codes will be executed left to right."), text_colour, title_font)
			yy += round(18 * self.gui.scale)
			self.ddt.text((xx0, yy), _("Select sources: (default: all playlists)"), title_colour, title_font)
			yy += round(14 * self.gui.scale)
			self.ddt.text((xx, yy), "s\"name\"", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Select source playlist by name"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "self", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Select playlist itself"), hint_colour, hint_font)

			yy += round(16 * self.gui.scale)
			self.ddt.text((xx0, yy), _("Add tracks from sources: (at least 1 required)"), title_colour, title_font)
			yy += round(14 * self.gui.scale)

			self.ddt.text((xx, yy), "a\"name\"", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Search artist name"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "g\"genre\"", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Search genre"), hint_colour, hint_font)
			# yy += round(12 * self.gui.scale)
			# self.ddt.text((xx, yy), "p\"text\"", code_colour, code_font)
			# self.ddt.text((xx2, yy), "Search filepath segment", hint_colour, hint_font)

			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "f\"terms\"", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Find / Search / Path"), hint_colour, hint_font)

			# yy += round(12 * self.gui.scale)
			# self.ddt.text((xx, yy), "ext\"flac\"", code_colour, code_font)
			# self.ddt.text((xx2, yy), "Search by file type", hint_colour, hint_font)

			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "a", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Add all tracks"), hint_colour, hint_font)

			yy += round(16 * self.gui.scale)
			self.ddt.text((xx0, yy), _("Filters"), title_colour, title_font)
			yy += round(14 * self.gui.scale)
			self.ddt.text((xx, yy), "n123", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Limit to number of tracks"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "y>1999", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Year: >, <, ="), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "pc>5", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Play count: >, <"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "d>3", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Track duration (minutes): >, <"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "ad>5", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Album duration (minutes): >, <"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "rat>3.5", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Track rating 0-5: >, <, ="), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "l", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Loved tracks"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "ly", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Has lyrics"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "ff\"terms\"", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Search and keep"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "fx\"terms\"", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Search and exclude"), hint_colour, hint_font)

			# yy += round(12 * self.gui.scale)
			# self.ddt.text((xx, yy), "com\"text\"", code_colour, code_font)
			# self.ddt.text((xx2, yy), "Search in comment", hint_colour, hint_font)
			# yy += round(12 * self.gui.scale)

			xx += round(260 * self.gui.scale)
			xx2 += round(260 * self.gui.scale)
			xx0 += round(260 * self.gui.scale)
			yy = hint_rect[1] + round(10 * self.gui.scale)
			yy += round(18 * self.gui.scale)

			# yy += round(16 * self.gui.scale)
			self.ddt.text((xx0, yy), _("Sorters"), title_colour, title_font)
			yy += round(14 * self.gui.scale)

			self.ddt.text((xx, yy), "st", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Shuffle tracks"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "ra", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Shuffle albums"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "y>", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Year: >, <"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "d>", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Track duration: >, <"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "pt>", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Track Playtime: >, <"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "pa>", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Album playtime: >, <"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "ad>", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Album duration: >, <"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "rv", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Invert tracks"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "rva", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Invert albums"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "rat>", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Track rating: >, <"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "rata>", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Album rating: >, <"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "m>", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Modification date: >, <"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "path", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Filepath"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "tn", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Track number per album"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "ypa", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Year per artist"), hint_colour, hint_font)
			yy += round(12 * self.gui.scale)
			self.ddt.text((xx, yy), "\"artist\">", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Sort by column name: >, <"), hint_colour, hint_font)

			yy += round(16 * self.gui.scale)
			self.ddt.text((xx0, yy), _("Special"), title_colour, title_font)
			yy += round(14 * self.gui.scale)
			self.ddt.text((xx, yy), "auto", code_colour, code_font)
			self.ddt.text((xx2, yy), _("Automatically reload on imports"), hint_colour, hint_font)

			yy += round(24 * self.gui.scale)
			# xx += round(80 * self.gui.scale)
			xx2 = xx
			xx2 += self.ddt.text((xx2, yy), _("Status:"), ColourRGBA(90, 90, 90, 255), 212) + round(6 * self.gui.scale)
			if self.rename_text_area.text:
				if self.gui.gen_code_errors:
					if self.gui.gen_code_errors == "playlist":
						self.ddt.text((xx2, yy), _("Playlist not found"), ColourRGBA(255, 100, 100, 255), 212)
					elif self.gui.gen_code_errors == "empty":
						self.ddt.text((xx2, yy), _("Result is empty"), ColourRGBA(250, 190, 100, 255), 212)
					elif self.gui.gen_code_errors == "close":
						self.ddt.text((xx2, yy), _("Close quotation..."), ColourRGBA(110, 110, 110, 255), 212)
					else:
						self.ddt.text((xx2, yy), "...", ColourRGBA(255, 100, 100, 255), 212)
				else:
					self.ddt.text((xx2, yy), _("OK"), ColourRGBA(100, 255, 100, 255), 212)
			else:
				self.ddt.text((xx2, yy), _("Disabled"), ColourRGBA(110, 110, 110, 255), 212)

		# self.ddt.pretty_rect = None

		# If enter or click outside of box: save and close
		if self.inp.key_return_press or (self.inp.key_esc_press and len(self.gui.editline) == 0) \
				or ((self.inp.mouse_click or self.inp.level_2_right_click) and not self.coll(rect)):
			self.gui.rename_playlist_box = False

			if self.done_callback is not None:
				cb = self.done_callback
				self.done_callback = None
				if len(self.rename_text_area.text) > 0:
					cb(self.rename_text_area.text)
			elif self.edit_generator:
				pass
			elif len(self.rename_text_area.text) > 0:
				if self.gui.radio_view:
					self.pctl.radio_playlists[self.playlist_index].name = self.rename_text_area.text
				else:
					self.pctl.multi_playlist[self.playlist_index].title = self.rename_text_area.text
			self.inp.key_return_press = False
class PlaylistBox:

	def recalc(self) -> None:
		self.tab_h = round(25 * self.gui.scale)
		self.gap = round(2 * self.gui.scale)

		self.text_offset = 2 * self.gui.scale
		if self.gui.scale == 1.25:
			self.text_offset = 3

	def __init__(self, tauon: _PlaylistApp) -> None:
		self.tauon       = tauon
		self.inp         = tauon.inp
		self.gui         = tauon.gui
		self.ddt         = tauon.ddt
		self.coll        = tauon.coll
		self.pctl        = tauon.pctl
		self.prefs       = tauon.prefs
		self.fields      = tauon.fields
		self.colours     = tauon.colours
		self.window_size = tauon.window_size
		self.scroll_on   = tauon.prefs.old_playlist_box_position
		self.drag = False
		self.drag_source = 0
		self.drag_on = -1

		self.adds = []

		self.indicate_w = round(2 * self.gui.scale)

		bag              = tauon.bag
		self.lock_icon = asset_loader(bag, bag.loaded_asset_dc, "lock-corner.png", True)
		self.pin_icon = asset_loader(bag, bag.loaded_asset_dc, "dia-pin.png", True)
		self.gen_icon = asset_loader(bag, bag.loaded_asset_dc, "gen-gear.png", True)


		# if gui.scale == 1.25:
		self.tab_h = 0
		self.gap = 0

		self.text_offset = 2 * self.gui.scale
		self.recalc()

	def draw(self, x: int, y: int, w: int, h: int) -> None:
		tauon = self.tauon
		ddt   = self.ddt
		pctl  = self.pctl
		gui   = self.gui

		# self.ddt.rect_r((x, y, w, h), self.colours.side_panel_background, True)
		self.ddt.rect((x, y, w, h), self.colours.playlist_box_background)
		self.ddt.text_background_colour = self.colours.playlist_box_background

		row_step = self.gap + self.tab_h
		top_pad = 5 * gui.scale
		max_tabs = max(0, int((h - top_pad + self.gap) // max(row_step, 1)))
		scroll_needed = len(pctl.multi_playlist) > max_tabs
		bottom_pad = 12 * gui.scale if scroll_needed else 0
		visible_scroll_rows = max(0, ((h - top_pad - bottom_pad - self.tab_h) / max(row_step, 1)) + 1)
		max_scroll = max(len(pctl.multi_playlist) - visible_scroll_rows, 0)

		tab_title_colour = self.colours.tab_text

		bg_lumi = test_lumi(self.colours.playlist_box_background)
		light_mode = False

		if bg_lumi < 0.55:
			light_mode = True
			tab_title_colour = ColourRGBA(20, 20, 20, 255)

		dark_mode = False
		if bg_lumi > 0.8:
			dark_mode = True

		indicate_w = round(3 * gui.scale) if light_mode else round(2 * gui.scale)

		show_scroll = False
		tab_start = x + 10 * self.gui.scale

		if self.window_size[0] < 700 * self.gui.scale:
			tab_start = x + 4 * self.gui.scale

		scroll_area = (x, y, w, h)
		self.scroll_on += self.tauon.smooth_scroll.get_scroll("playlist side pane", scroll_area, row_step)  / max(row_step, 1)

		self.scroll_on = min(self.scroll_on, max_scroll)
		self.scroll_on = max(self.scroll_on, 0)

		if scroll_needed:
			show_scroll = True
		else:
			self.scroll_on = 0

		if show_scroll:
			tab_start += 15 * self.gui.scale

		if self.colours.lm:
			w -= round(6 * gui.scale)
		tab_width = w - tab_start  # - 0 * gui.scale
		visible_tab_limit = max_tabs + 1 if show_scroll else max_tabs

		def clipped_to_box(rect):
			rect_y = max(rect[1], y)
			rect_bottom = min(rect[1] + rect[3], y + h)
			if rect_bottom <= rect_y:
				return None
			return (rect[0], rect_y, rect[2], rect_bottom - rect_y)

		# Draw scroll bar
		if show_scroll:
			self.scroll_on = self.tauon.playlist_panel_scroll.draw(
				x + 2, y + 1, 15 * self.gui.scale, h, self.scroll_on, max_scroll)

		draw_pin_indicator = False  # self.prefs.tabs_on_top

		# if not gui.album_tab_mode:
		# 	if self.inp.key_left_press or self.inp.key_right_press:
		# 		if pctl.active_playlist_viewing < self.scroll_on:
		# 			self.scroll_on = pctl.active_playlist_viewing
		# 		elif pctl.active_playlist_viewing + 1 > self.scroll_on + max_tabs:
		# 			self.scroll_on = (pctl.active_playlist_viewing - max_tabs) + 1

		# Process inputs
		delete_pl = None
		tab_on = 0
		scroll_start = int(self.scroll_on)
		scroll_offset = (self.scroll_on - scroll_start) * max(row_step, 1)
		yy = y + top_pad - scroll_offset
		for i, pl in enumerate(pctl.multi_playlist):

			if tab_on >= visible_tab_limit:
				break
			if i < scroll_start:
				continue

			# if not pl.hidden and i in tabs_on_top:
			# 	continue

			tab_on += 1
			tab_hit_rect = clipped_to_box((tab_start, yy - 1, tab_width, (self.tab_h + 1)))

			if tab_hit_rect is not None and self.coll(tab_hit_rect):
				if self.inp.right_click:
					if gui.radio_view:
						tauon.radio_tab_menu.activate(i, self.inp.mouse_position)
					else:
						tauon.tab_menu.activate(i, self.inp.mouse_position)
					gui.tab_menu_pl = i

				if tauon.tab_menu.active is False and self.inp.middle_click:
					delete_pl = i
					# delete_playlist(i)
					# break

				if self.inp.mouse_up and self.drag and coll_point(self.inp.mouse_up_position, tab_hit_rect):
					# If drag from top bar to side panel, make hidden
					if self.drag_source == 0 and self.prefs.drag_to_unpin:
						pctl.multi_playlist[self.drag_on].hidden = True

					# Move playlist tab
					if i != self.drag_on and not point_proximity_test(gui.drag_source_position, self.inp.mouse_position, 10 * gui.scale):
						if self.inp.key_shift_down:
							pctl.multi_playlist[i].playlist_ids += pctl.multi_playlist[self.drag_on].playlist_ids
							pctl.delete_playlist(self.drag_on, force=True)
						else:
							pctl.move_playlist(self.drag_on, i)

					gui.request_frame()

				# Double click to play
				if self.inp.mouse_up and pctl.pl_to_id(i) == self.tauon.top_panel.tab_d_click_ref == pctl.pl_to_id(pctl.active_playlist_viewing) and \
					self.tauon.top_panel.tab_d_click_timer.get() < 0.25 and \
					point_distance(self.inp.last_click_location, self.inp.mouse_up_position) < 5 * gui.scale:

					if pctl.playing_state == PlayingState.PAUSED and pctl.active_playlist_playing == i:
						pctl.play()
					elif pctl.selected_ready() and (pctl.playing_state != PlayingState.PLAYING or pctl.active_playlist_playing != i):
						pctl.jump(pctl.default_playlist[pctl.selected_in_playlist], pl_position=pctl.selected_in_playlist)
				if self.inp.mouse_up:
					self.tauon.top_panel.tab_d_click_timer.set()
					self.tauon.top_panel.tab_d_click_ref = pctl.pl_to_id(i)

				if not draw_pin_indicator and self.inp.mouse_click:
					pctl.switch_playlist(i)
					self.drag_on = i
					self.drag = True
					self.drag_source = 1
					gui.set_drag_source()

				# Process input of dragging tracks onto tab
				if self.inp.quick_drag is True and self.inp.mouse_up:
					self.tauon.top_panel.tab_d_click_ref = -1
					self.tauon.top_panel.tab_d_click_timer.force_set(100)
					if (pctl.gen_codes.get(pctl.pl_to_id(i)) and "self" not in pctl.gen_codes[pctl.pl_to_id(i)]):
						self.tauon.clear_gen_ask(pctl.pl_to_id(i))
					self.inp.quick_drag = False
					modified = False
					gui.request_tracklist_redraw()

					for item in self.gui.shift_selection:
						pctl.multi_playlist[i].playlist_ids.append(pctl.default_playlist[item])
						modified = True
					if len(self.gui.shift_selection) > 0:
						self.adds.append(
							[pctl.multi_playlist[i].uuid_int, len(self.gui.shift_selection), Timer()])  # ID, num, timer
						modified = True
					if modified:
						pctl.after_import_flag = True
						tauon.dropped_playlist = i
						tauon.thread_manager.ready("worker")
						pctl.notify_database_changed()
						pctl.update_shuffle_pool(pctl.multi_playlist[i].uuid_int)
						tauon.tree_view_box.clear_target_pl(i)

			# Toggle hidden flag on click
			pin_hit_rect = clipped_to_box((tab_start + 5 * gui.scale, yy + 3 * gui.scale, 25 * gui.scale, 26 * gui.scale))
			if draw_pin_indicator and self.inp.mouse_click and pin_hit_rect is not None and self.coll(pin_hit_rect):
				pl.hidden ^= True

			yy += self.tab_h + self.gap

		# Draw tabs
		# delete_pl = None
		tab_on = 0
		yy = y + top_pad - scroll_offset
		for i, pl in enumerate(pctl.multi_playlist):

			# if yy + self.tab_h > y + h:
			#     break
			if tab_on >= visible_tab_limit:
				break
			if i < scroll_start:
				continue

			tab_on += 1

			name = pl.title
			hidden = pl.hidden

			# Background is invisible by default (for highlighting if selected)
			bg = ColourRGBA(0, 0, 0, 0)
			if self.prefs.transparent_mode:
				bg = rgb_add_hls(self.colours.playlist_box_background, 0, 0.09, 0)
				bg = ColourRGBA(bg.r, bg.g, bg.b, 255)

			drop_hit_rect = clipped_to_box(
				(tab_start + 50 * gui.scale, yy - 1, tab_width - 50 * gui.scale, (self.tab_h + 1))
			)

			# Highlight if playlist selected (viewing)
			if i == pctl.active_playlist_viewing or (tauon.tab_menu.active and tauon.tab_menu.reference == i):
				# bg = [255, 255, 255, 25]

				# Adjust highlight for different background brightnesses
				bg = rgb_add_hls(self.colours.playlist_box_background, 0, 0.06, 0)
				if light_mode:
					bg = ColourRGBA(0, 0, 0, 25)
				if self.prefs.transparent_mode:
					bg = rgb_add_hls(self.colours.playlist_box_background, 0, 0.03, 0)
					bg = ColourRGBA(bg.r, bg.g, bg.b, 255)

			# Highlight target playlist when tragging tracks over
			if drop_hit_rect is not None and self.coll(drop_hit_rect) and self.inp.quick_drag and not (
				pctl.gen_codes.get(pctl.pl_to_id(i)) and "self" not in pctl.gen_codes[pctl.pl_to_id(i)]):
				# bg = [255, 255, 255, 15]
				bg = rgb_add_hls(self.colours.playlist_box_background, 0, 0.04, 0)
				if light_mode:
					bg = ColourRGBA(0, 0, 0, 16)

			# Get actual bg from blend for text bg
			real_bg = alpha_blend(bg, self.colours.playlist_box_background)

			# Draw highlight
			self.ddt.rect((tab_start, yy - round(1 * gui.scale), tab_width, self.tab_h), bg)

			# Draw title text
			text_start = 10 * gui.scale
			if draw_pin_indicator:
				# text_start = 40 * gui.scale
				text_start = 32 * gui.scale

			if not pl.hidden and self.prefs.tabs_on_top:
				cl = ColourRGBA(255, 255, 255, 25)

				if light_mode:
					cl = ColourRGBA(0, 0, 0, 40)

				xx = tab_start + tab_width - self.lock_icon.w
				self.lock_icon.render(xx, yy, cl)

			text_max_w = tab_width - text_start - 15 * gui.scale
			# if indicator_run_x:
			#     text_max_w = tab_width - (indicator_run_x + text_start + 17 * gui.scale + slide)
			self.ddt.text(
				(tab_start + text_start, yy + self.text_offset), name, tab_title_colour if i != pctl.active_playlist_viewing else self.colours.tab_text_active, 211, max_w=text_max_w, bg=real_bg)

			# Is mouse collided with tab?
			hit = drop_hit_rect is not None and self.coll(drop_hit_rect)

			# if not self.prefs.tabs_on_top:
			if i == pctl.active_playlist_playing:
				indicator_colour = self.colours.title_playing
				if self.colours.lm:
					indicator_colour = self.colours.seek_bar_fill

				ddt.rect((tab_start + 0 - 2 * gui.scale, yy - round(1 * gui.scale), indicate_w, self.tab_h), indicator_colour)

			# # If mouse over
			if hit:
				# Draw indicator for dragging tracks
				if (self.inp.quick_drag or gui.ext_drop_mode) and self.tauon.pl_is_mut(i):
					ddt.rect((tab_start + tab_width - self.indicate_w, yy, self.indicate_w, self.tab_h), ColourRGBA(80, 200, 180, 255))

				# Draw indicators for moving tab
				if self.drag and i != self.drag_on and not point_proximity_test(
					gui.drag_source_position, self.inp.mouse_position, 10 * gui.scale):
					if self.inp.key_shift_down:
						ddt.rect(
							(tab_start + tab_width - 4 * gui.scale, yy, self.indicate_w, self.tab_h),
							ColourRGBA(80, 160, 200, 255))
					elif i < self.drag_on:
						ddt.rect((tab_start, yy - self.indicate_w, tab_width, self.indicate_w), ColourRGBA(80, 160, 200, 255))
					else:
						ddt.rect((tab_start, yy + (self.tab_h - self.indicate_w), tab_width, self.indicate_w), ColourRGBA(80, 160, 200, 255))

			elif self.inp.quick_drag and not point_proximity_test(gui.drag_source_position, self.inp.mouse_position, 15 * gui.scale):
				for item in gui.shift_selection:
					if len(pctl.default_playlist) > item and pctl.default_playlist[item] in pl.playlist_ids:
						ddt.rect((tab_start + tab_width - self.indicate_w, yy, self.indicate_w, self.tab_h), ColourRGBA(190, 170, 20, 255))
						break
			# Drag red line highlight if playlist is generator playlist
			if self.inp.quick_drag and not point_proximity_test(gui.drag_source_position, self.inp.mouse_position, 15 * gui.scale):
				if not self.tauon.pl_is_mut(i):
					ddt.rect((tab_start + tab_width - self.indicate_w, yy, self.indicate_w, self.tab_h), ColourRGBA(200, 70, 50, 255))

			# Draw effect of adding tracks to playlist
			if len(self.adds) > 0:
				for k in reversed(range(len(self.adds))):
					if pctl.multi_playlist[i].uuid_int == self.adds[k][0]:
						if self.adds[k][2].get() > 0.3:
							del self.adds[k]
						else:
							ay = yy + 4 * gui.scale
							ay -= 6 * gui.scale * self.adds[k][2].get() / 0.3

							ddt.text(
								(tab_start + tab_width - 10 * gui.scale, round(ay), 1),
								"+" + str(self.adds[k][1]), self.colours.pulse_colour, 212, bg=real_bg)
							gui.request_frame()

							ddt.rect(
								(tab_start + tab_width, yy, self.indicate_w, self.tab_h - self.indicate_w),
								ColourRGBA(244, 212, 66, int(255 * self.adds[k][2].get() / 0.3) * -1))

			yy += self.tab_h + self.gap

		if delete_pl is not None:
			# delete_playlist(delete_pl)
			self.pctl.delete_playlist_ask(delete_pl)
			gui.request_frame()

		# Create new playlist if drag in blank space after tabs
		rect_y = max(yy, y)
		rect = (x, rect_y, w - 10 * gui.scale, max(0, y + h - rect_y))
		if rect[3] > 0:
			self.fields.add(rect)

		if rect[3] > 0 and self.coll(rect):
			if self.inp.quick_drag or gui.ext_drop_mode:
				ddt.rect((tab_start, yy, tab_width, self.indicate_w), ColourRGBA(80, 160, 200, 255))
				if self.inp.mouse_up:
					self.tauon.drop_tracks_to_new_playlist(gui.shift_selection)

			if self.inp.right_click:
				self.tauon.extra_tab_menu.activate(pctl.active_playlist_viewing)

			# Move tab to end playlist if dragged past end
			if self.drag:
				if self.inp.mouse_up:
					if self.inp.key_ctrl_down:
						# Duplicate playlist on ctrl
						self.tauon.gen_dupe(tauon.playlist_box.drag_on)
						gui.request_frame()
						self.drag = False
					else:
						# If drag from top bar to side panel, make hidden
						if self.drag_source == 0 and self.prefs.drag_to_unpin:
							pctl.multi_playlist[self.drag_on].hidden = True

						pctl.move_playlist(self.drag_on, i)
						gui.request_frame()
						self.drag = False
				elif self.inp.key_ctrl_down:
					ddt.rect((tab_start, yy, tab_width, self.indicate_w), ColourRGBA(255, 190, 0, 255))
				else:
					ddt.rect((tab_start, yy, tab_width, self.indicate_w), ColourRGBA(80, 160, 200, 255))
@dataclass
class ArtistListSaveState:

	all_artists: list[str]
	album_counts: dict[str, list[str]]
	scroll_position: int
	playlist_length: int
	artist_track_counts: dict[str, int]
	filtered_artists: int
class ArtistList:

	def __init__(self, tauon: _PlaylistApp, pctl: _PlaylistPlayer) -> None:
		self.tauon                 = tauon
		self.pctl                  = pctl
		self.ddt                   = tauon.ddt
		self.inp                   = tauon.inp
		self.gui                   = tauon.gui
		self.coll                  = tauon.coll
		self.prefs                 = tauon.prefs
		self.fields                = tauon.fields
		self.colours               = tauon.colours
		self.renderer              = tauon.renderer
		self.lastfm                = pctl.lastfm
		self.star_store            = pctl.star_store
		self.window_size           = tauon.window_size
		self.smooth_scroll         = tauon.smooth_scroll
		self.thread_manager        = tauon.thread_manager
		self.artist_info_box       = pctl.artist_info_box
		self.artist_list_menu      = tauon.artist_list_menu
		self.a_cache_directory     = tauon.a_cache_directory
		self.artist_list_scroll    = pctl.artist_list_scroll
		self.artist_preview_render = tauon.artist_preview_render
		self.tab_h = round(60 * self.gui.scale)
		self.thumb_size = round(55 * self.gui.scale)

		self.current_artists: list[str] = []
		self.current_album_counts: dict[str, list[str]] = {}
		self.current_artist_track_counts: dict[str, int] = {}

		self.thumb_cache: dict[str, list[sdl3.LP_SDL_Texture | sdl3.SDL_FRect] | None] = {}

		self.to_fetch = ""
		self.to_fetch_mbid_a = ""

		self.scroll_position: int = 0

		self.id_to_load = ""

		self.d_click_timer = Timer()
		self.d_click_ref = -1

		self.click_ref = -1
		self.click_highlight_timer = Timer()

		self.saves: dict[int, ArtistListSaveState] = {}

		self.load = False

		self.shown_letters = []

		self.hover_on = "NONE"
		self.hover_timer = Timer(10)

		self.sample_tracks = {}

	def load_img(self, artist: str) -> None:
		filepath = self.artist_info_box.get_data(artist, get_img_path=True)

		if filepath and os.path.isfile(filepath):
			try:
				g = io.BytesIO()
				g.seek(0)

				with Image.open(filepath) as im:
					w, h = im.size
					if w != h:
						m = min(w, h)
						im = im.crop((
							round((w - m) / 2),
							round((h - m) / 2),
							round((w + m) / 2),
							round((h + m) / 2),
						))

					im.thumbnail((self.thumb_size, self.thumb_size), Image.Resampling.LANCZOS)

					im.save(g, "PNG")
				g.seek(0)

				s_image = self.ddt.load_image(g)
				texture = sdl3.SDL_CreateTextureFromSurface(self.renderer, s_image)
				sdl3.SDL_DestroySurface(s_image)
				tex_w = pointer(c_float(0))
				tex_h = pointer(c_float(0))
				sdl3.SDL_GetTextureSize(texture, tex_w, tex_h)
				rect = sdl3.SDL_FRect(0, 0)
				rect.w = int(tex_w.contents.value)
				rect.h = int(tex_h.contents.value)

				self.thumb_cache[artist] = [texture, rect]
			except Exception:
				logging.exception("Artist thumbnail processing error")
				self.thumb_cache[artist] = None

		elif artist in self.prefs.failed_artists:
			self.thumb_cache[artist] = None
		elif not self.to_fetch:
			if self.prefs.auto_dl_artist_data:
				self.to_fetch = artist
				self.thread_manager.ready("worker")
			else:
				self.thumb_cache[artist] = None

	def worker(self) -> None:
		if self.load:
			if self.tauon.after_scan:
				return

			self.prep()
			self.load = False
			return

		if self.to_fetch:
			if self.tauon.get_lfm_wait_timer.get() < 6:
				return

			artist = self.to_fetch
			f_artist = filename_safe(artist)

			self.tauon.artist_info_box.get_data(artist, silent=True)
			if not self.tauon.artist_info_box.get_data(artist, get_img_path=True):
				if artist not in self.prefs.failed_artists:
					logging.error(f"Failed fetching: {artist}")
					self.prefs.failed_artists.append(artist)

			self.to_fetch = ""

	def prep(self) -> None:
		self.scroll_position = 0

		curren_pl_no = self.pctl.id_to_pl(self.id_to_load)
		if curren_pl_no is None:
			return
		current_pl = self.pctl.multi_playlist[curren_pl_no]

		all: list[str] = []
		artist_parents = {}
		counts: dict[str, int] = {}
		play_time = {}
		filtered = 0
		b = 0

		try:
			for item in current_pl.playlist_ids:
				b += 1
				if b % 100 == 0:
					time.sleep(0.001)

				track = self.pctl.get_track(item)

				if track.artists is not None:
					artists = track.artists
				else:
					if self.prefs.artist_list_prefer_album_artist and track.album_artist:
						artists = track.album_artist
					else:
						artists = get_artist_strip_feat(track)

					artists = [x.strip() for x in artists.split(";")]

				pp = 0
				if self.prefs.artist_list_sort_mode == "play":
					pp = self.star_store.get(item)

				for artist in artists:
					if artist:
						# Add play time
						if self.prefs.artist_list_sort_mode == "play":
							p = play_time.get(artist, 0)
							play_time[artist] = p + pp

						# Get a sample track for fallback art
						if artist not in self.sample_tracks:
							self.sample_tracks[artist] = track

						# Confirm to final list if appeared at least 5 times
						# if artist not in all:
						if artist not in counts:
							counts[artist] = 0
						counts[artist] += 1
						if artist not in all:
							if counts[artist] > self.prefs.artist_list_threshold or len(current_pl.playlist_ids) < 1000:
								all.append(artist)
							else:
								filtered += 1

						if artist not in artist_parents:
							artist_parents[artist] = []
						if track.parent_folder_path not in artist_parents[artist]:
							artist_parents[artist].append(track.parent_folder_path)

			current_album_counts = artist_parents

			if self.prefs.artist_list_sort_mode == "popular":
				all.sort(key=counts.get, reverse=True)
			elif self.prefs.artist_list_sort_mode == "play":
				all.sort(key=play_time.get, reverse=True)
			else:
				all.sort(key=lambda y: y.lower().removeprefix("the "))
		except Exception:
			logging.exception("Album scan failure")
			time.sleep(4)
			return

		# Artist-list, album-counts, scroll-position, playlist-length, number ignored
		save = ArtistListSaveState(all, current_album_counts, 0, len(current_pl.playlist_ids), counts, filtered)

		# Scroll to playing artist
		scroll = 0
		if self.pctl.playing_ready():
			track = self.pctl.playing_object()
			for i, item in enumerate(save.all_artists):
				if item in (track.artist, track.album_artist):
					scroll = i
					break
		save.scroll_position = scroll

		viewing_pl_id = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].uuid_int
		if viewing_pl_id in self.saves:
			self.saves[viewing_pl_id].scroll_position = self.scroll_position

		self.saves[current_pl.uuid_int] = save
		self.gui.request_frame()

	def locate_artist_letter(self, text: str) -> None:
		if not text or self.prefs.artist_list_sort_mode != "alpha":
			return

		letter = text[0].lower()
		letter_upper = letter.upper()
		for i, item in enumerate(self.current_artists):
			if item.startswith(("the ", "The ")):
				if len(item) > 4 and (item[4] == letter or item[4] == letter_upper):
					self.scroll_position = i
					break
			elif item and (item[0] == letter or item[0] == letter_upper):
				self.scroll_position = i
				break

		viewing_pl_id = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].uuid_int
		if self.pctl.multi_playlist[self.pctl.active_playlist_viewing].parent_playlist_id:
			viewing_pl_id = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].parent_playlist_id
		if viewing_pl_id in self.saves:
			self.saves[viewing_pl_id].scroll_position = self.scroll_position

	def locate_artist(self, track: TrackClass) -> None:
		for i, item in enumerate(self.current_artists):
			if item in (track.artist, track.album_artist) or (track.artists is not None and item in track.artists):
				self.scroll_position = i
				break

		viewing_pl_id = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].uuid_int
		if viewing_pl_id in self.saves:
			self.saves[viewing_pl_id].scroll_position = self.scroll_position

	def draw_card_text_only(self, artist: str, x: int, y: int, w: int, area: list[int], thin_mode: bool, line1_colour: ColourRGBA, line2_colour: ColourRGBA, light_mode: bool, bg: ColourRGBA) -> None:
		album_mode = False
		for albums in self.current_album_counts.values():
			if len(albums) > 1:
				album_mode = True
				break

		if not album_mode:
			count = self.current_artist_track_counts[artist]
			if count > 1:
				text = _("{N} tracks").format(N=str(count))
			else:
				text = _("{N} track").format(N=str(count))
		else:
			album_count = len(self.current_album_counts[artist])
			if album_count > 1:
				text = _("{N} albums").format(N=str(album_count))
			else:
				text = _("{N} album").format(N=str(album_count))

		if self.gui.preview_artist_loading == artist:
			# . Max 20 chars. Alt: Downloading image, Loading image
			text = _("Downloading data...")

		x_text = round(10 * self.gui.scale)
		artist_font = 313
		count_font = 312
		extra_text_space = 0
		self.ddt.text(
			(x_text, y + round(2 * self.gui.scale)), artist, line1_colour, artist_font,
			extra_text_space + w - x_text - 30 * self.gui.scale, bg=bg)
		# self.ddt.text((x_text, y + self.tab_h // 2 - 2 * self.gui.scale), text, line2_colour, count_font,
		#          extra_text_space + w - x_text - 15 * self.gui.scale, bg=bg)

	def draw_card_with_thumbnail(self, artist: str, x: int, y: int, w: int, area: list[int], thin_mode: bool, line1_colour: ColourRGBA, line2_colour: ColourRGBA, light_mode: bool, bg: ColourRGBA) -> None:
		if artist not in self.thumb_cache:
			self.load_img(artist)

		thumb_x = round(x + 10 * self.gui.scale)
		x_text = x + self.thumb_size + 19 * self.gui.scale
		artist_font = 513
		count_font = 312
		extra_text_space = 0
		if thin_mode:
			thumb_x = round(x + 10 * self.gui.scale)
			x_text = x + self.thumb_size + 17 * self.gui.scale
			artist_font = 211
			count_font = 311
			extra_text_space = 135 * self.gui.scale
			thin_mode = True
			area = (4 * self.gui.scale, y, w - 7 * self.gui.scale, self.tab_h - 2)
			self.fields.add(area)

		back_colour = ColourRGBA(30, 30, 30, 255)
		back_colour_2 = ColourRGBA(27, 27, 27, 255)
		border_colour = ColourRGBA(60, 60, 60, 255)
		# if self.colours.lm:
		# 	back_colour = ColourRGBA(200, 200, 200, 255)
		# 	back_colour_2 = ColourRGBA(240, 240, 240, 255)
		# 	border_colour = ColourRGBA(160, 160, 160, 255)
		rect = (thumb_x, round(y), self.thumb_size, self.thumb_size)

		if thin_mode and self.coll(area) and self.tauon.is_level_zero() and y + self.tab_h < self.window_size[1] - self.gui.panelBY:
			tab_rect = (x, y - round(2 * self.gui.scale), round(190 * self.gui.scale), self.tab_h - round(1 * self.gui.scale))

			for r in subtract_rect(tab_rect, rect):
				r = sdl3.SDL_FRect(r[0], r[1], r[2], r[3])
				self.tauon.style_overlay.hole_punches.append(r)

			self.ddt.rect(tab_rect, back_colour_2)
			bg = back_colour_2

		self.ddt.rect(rect, back_colour)
		self.ddt.rect(rect, border_colour)

		self.fields.add(rect)
		if self.coll(rect) and self.tauon.is_level_zero(True):
			self.hover_any = True

			hover_delay = 0.5
			if self.gui.compact_artist_list:
				hover_delay = 2

			if self.gui.preview_artist != artist:
				if self.hover_on != artist:
					self.hover_on = artist
					self.gui.preview_artist = ""
					self.hover_timer.set()
					self.gui.delay_frame(hover_delay)
				elif self.hover_timer.get() > hover_delay and not self.gui.preview_artist_loading:
					self.gui.preview_artist = ""
					path = self.artist_info_box.get_data(artist, get_img_path=True)
					if not path:
						self.gui.preview_artist_loading = artist
						shoot = threading.Thread(
							target=self.tauon.get_artist_preview,
							args=((artist, round(thumb_x + self.thumb_size), round(y))))
						shoot.daemon = True
						shoot.start()

					if path:
						self.tauon.set_artist_preview(path, artist, round(thumb_x + self.thumb_size), round(y))

			if self.inp.mouse_click:
				self.hover_timer.force_set(-2)
				self.gui.delay_frame(2 + hover_delay)

		drawn = False
		if artist in self.thumb_cache:
			thumb = self.thumb_cache[artist]
			if thumb is not None:
				thumb[1].x = thumb_x
				thumb[1].y = round(y)
				sdl3.SDL_RenderTexture(self.renderer, thumb[0], None, thumb[1])
				drawn = True
				if self.prefs.art_bg:
					rect = sdl3.SDL_FRect(thumb_x, round(y), self.thumb_size, self.thumb_size)
					if (rect.y + rect.h) > self.window_size[1] - self.gui.panelBY:
						diff = (rect.y + rect.h) - (self.window_size[1] - self.gui.panelBY)
						rect.h -= round(diff)
					self.tauon.style_overlay.hole_punches.append(rect)
		if not drawn:
			track = self.sample_tracks.get(artist)
			if track:
				self.tauon.gall_ren.render(track, (round(thumb_x), round(y)), self.thumb_size)

		if thin_mode:
			text = artist[:2].title()
			if text not in self.shown_letters:
				ww = self.ddt.get_text_w(text, 211)
				self.ddt.rect(
					(thumb_x + round(1 * self.gui.scale), y + self.tab_h - 20 * self.gui.scale, ww + 5 * self.gui.scale, 13 * self.gui.scale),
					ColourRGBA(20, 20, 20, 255))
				self.ddt.text(
					(thumb_x + 3 * self.gui.scale, y + self.tab_h - 23 * self.gui.scale), text, ColourRGBA(240, 240, 240, 255), 210,
					bg=ColourRGBA(20, 20, 20, 255))
				self.shown_letters.append(text)

		# Draw labels
		if not thin_mode or (self.coll(area) and self.tauon.is_level_zero() and y + self.tab_h < self.window_size[1] - self.gui.panelBY):
			album_mode = False
			for albums in self.current_album_counts.values():
				if len(albums) > 1:
					album_mode = True
					break

			if not album_mode:
				count = self.current_artist_track_counts[artist]
				if count > 1:
					text = _("{N} tracks").format(N=str(count))
				else:
					text = _("{N} track").format(N=str(count))
			else:
				album_count = len(self.current_album_counts[artist])
				if album_count > 1:
					text = _("{N} albums").format(N=str(album_count))
				else:
					text = _("{N} album").format(N=str(album_count))

			if self.gui.preview_artist_loading == artist:
				# . Max 20 chars. Alt: Downloading image, Loading image
				text = _("Downloading data...")

			self.ddt.text(
				(x_text, y + self.tab_h // 2 - 19 * self.gui.scale), artist, line1_colour, artist_font,
				extra_text_space + w - x_text - 30 * self.gui.scale, bg=bg)
			self.ddt.text(
				(x_text, y + self.tab_h // 2 - 2 * self.gui.scale), text, line2_colour, count_font,
				extra_text_space + w - x_text - 15 * self.gui.scale, bg=bg)

	def draw_card(self, artist, x, y, w) -> None:
		area = (4 * self.gui.scale, y, w - 26 * self.gui.scale, self.tab_h - 2)
		if self.prefs.artist_list_style == 2:
			area = (4 * self.gui.scale, y, w - 26 * self.gui.scale, self.tab_h - 1)

		self.fields.add(area)

		light_mode = False
		line1_colour = ColourRGBA(235, 235, 235, 255)
		line2_colour = ColourRGBA(255, 255, 255, 120)
		fade_max = 50

		thin_mode = False
		if self.gui.compact_artist_list:
			thin_mode = True
			line2_colour = ColourRGBA(115, 115, 115, 255)
		elif test_lumi(self.colours.side_panel_background) < 0.55 and not thin_mode:
			light_mode = True
			fade_max = 20
			line1_colour = ColourRGBA(35, 35, 35, 255)
			line2_colour = ColourRGBA(100, 100, 100, 255)

		# Fade on click
		bg = self.colours.side_panel_background
		if not thin_mode:
			if self.coll(area) and self.tauon.is_level_zero(True):
			# or pctl.get_track(pctl.default_playlist[pctl.playlist_view_position]).artist == artist:
				self.ddt.rect(area, ColourRGBA(50, 50, 50, 50))
				bg = alpha_blend(ColourRGBA(50, 50, 50, 50), self.colours.side_panel_background)
				if self.prefs.transparent_mode:
					bg = rgb_add_hls(self.colours.playlist_box_background, 0, 0.2, 0)
					self.ddt.rect(area, bg)
			else:
				fade = 0
				t = self.click_highlight_timer.get()
				if self.click_ref == artist and (t < 2.2 or self.artist_list_menu.active):
					if t < 1.9 or self.artist_list_menu.active:
						fade = fade_max
					else:
						fade = fade_max - round((t - 1.9) / 0.3 * fade_max)

					self.gui.request_frame()
					self.ddt.rect(area, ColourRGBA(50, 50, 50, fade))

				bg = alpha_blend(ColourRGBA(50, 50, 50, fade), self.colours.side_panel_background)
				if self.prefs.transparent_mode:
					bg = self.colours.side_panel_background

		if self.prefs.artist_list_style == 1:
			self.draw_card_with_thumbnail(artist, x, y, w, area, thin_mode, line1_colour, line2_colour, light_mode, bg)
		else:
			self.draw_card_text_only(artist, x, y, w, area, thin_mode, line1_colour, line2_colour, light_mode, bg)

		if self.coll(area) and self.inp.mouse_position[1] < self.window_size[1] - self.gui.panelBY:
			if self.inp.mouse_click:
				if self.click_ref != artist:
					self.pctl.playlist_view_position = 0
					self.pctl.selected_in_playlist = 0
				self.click_ref = artist

				double_click = False
				if self.d_click_timer.get() < 0.4 and self.d_click_ref == artist:
					double_click = True

				self.click_highlight_timer.set()
				replace = False
				parent_playlist_id = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].parent_playlist_id
				if parent_playlist_id:
					if self.pctl.id_to_pl(parent_playlist_id) is None:
						self.pctl.multi_playlist[self.pctl.active_playlist_viewing].parent_playlist_id = 0
					else:
						self.tauon.create_artist_pl(artist, replace=True)
						replace = True

				blocks = []
				current_block = []

				in_artist = False
				this_artist = artist.casefold()
				last_ref = None
				on = 0

				for i in range(len(self.pctl.default_playlist)):
					track = self.pctl.get_track(self.pctl.default_playlist[i])
					if track.artist.casefold() == this_artist or track.album_artist.casefold() == this_artist or (
							track.artists is not None and artist in track.artists):
						# Matching artist
						if not in_artist:
							in_artist = True
							last_ref = track
							current_block.append(i)

						elif (last_ref and track.album != last_ref.album) or track.parent_folder_path != last_ref.parent_folder_path:
							current_block.append(i)
							last_ref = track
					# Not matching
					elif in_artist:
						blocks.append(current_block)
						current_block = []
						in_artist = False

				if current_block:
					blocks.append(current_block)
					current_block = []

				#logging.info(blocks)
				# return

				# block_starts = []
				# current = False
				# for i in range(len(self.pctl.default_playlist)):
				# 	track = self.pctl.get_track(self.pctl.default_playlist[i])
				# 	if current is False:
				# 		if track.artist == artist or track.album_artist == artist or (
				# 				track.artists is not None and artist in track.artists):
				# 			block_starts.append(i)
				# 			current = True
				# 	else:
				# 		if track.artist != artist and track.album_artist != artist or (
				# 				track.artists is not None and artist in track.artists):
				# 			current = False
				#
				# if not block_starts:
				# 	logging.info("No matching artists found in playlist")
				# 	return

				if not blocks:
					return

				#select = block_starts[0]

				# if len(block_starts) > 1:
				# 	if -1 < self.pctl.selected_in_playlist < len(self.pctl.default_playlist):
				# 		if self.pctl.selected_in_playlist in block_starts:
				# 			tauon.scroll_hide_timer.set()
				# 			self.gui.frame_callback_list.append(TestTimer(0.9))
				# 			if block_starts[-1] == self.pctl.selected_in_playlist:
				# 				pass
				# 			else:
				# 				select = block_starts[block_starts.index(self.pctl.selected_in_playlist) + 1]

				self.gui.request_tracklist_redraw()

				self.click_highlight_timer.set()

				select = blocks[0][0]

				if double_click:
					# Stat first artist track in playlist

					self.pctl.jump(self.pctl.default_playlist[select], pl_position=select)
					self.pctl.playlist_view_position = select
					self.pctl.selected_in_playlist = select
					self.gui.shift_selection.clear()
					self.d_click_timer.force_set(10)
				elif not replace:
					# Goto next artist section in playlist
					c = self.pctl.selected_in_playlist
					next = False
					track = self.pctl.get_track_in_playlist(c, -1)
					if track is None:
						logging.error("Index out of range!")
						self.pctl.selected_in_playlist = 0
						return
					if track.artist.casefold != artist.casefold:
						self.pctl.selected_in_playlist = 0
						self.pctl.playlist_view_position = 0
					if len(blocks) == 1:
						block = blocks[0]
						if len(block) > 1:
							if c < block[0] or c >= block[-1]:
								select = block[0]
								self.tauon.toast(_("First of artist's albums ({N} albums)")
									.format(N=len(block)))
							else:
								select = block[-1]
								self.tauon.toast(_("Last of artist's albums ({N} albums)")
									.format(N=len(block)))
					else:
						select = None
						for bb, block in enumerate(blocks):
							for i, al in enumerate(block):
								if al <= c:
									continue
								next = True
								if i == 0:
									select = al
									if len(block) > 1:
										self.tauon.toast(_("Start of location {N} of {T} ({Nb} albums)")
											.format(N=bb + 1, T=len(blocks), Nb=len(block)))
									else:
										self.tauon.toast(_("Location {N} of {T}")
											.format(N=bb + 1, T=len(blocks)))
									break

							if next and not select:
								select = block[-1]
								if len(block) > 1:
									self.tauon.toast(_("End of location {N} of {T} ({Nb} albums)")
										.format(N=bb + 1, T=len(blocks), Nb=len(block)))
								else:
									self.tauon.toast(_("Location {N} of {T}")
										.format(N=bb, T=len(blocks)))
								break
							if select:
								break
					if not select:
						select = blocks[0][0]
						if len(blocks[0]) > 1:
							if len(blocks) > 1:
								self.tauon.toast(_("Start of location 1 of {N} ({Nb} albums)")
									.format(N=len(blocks), Nb=len(blocks[0])))
							else:
								self.tauon.toast(_("Location 1 of {N} ({Nb} albums)")
									.format(N=len(blocks), Nb=len(blocks[0])))
						else:
							self.tauon.toast(_("Location 1 of {N}")
								.format(N=len(blocks)))

					self.pctl.playlist_view_position = select
					self.pctl.selected_in_playlist = select
					self.d_click_ref = artist
					self.d_click_timer.set()
					if self.prefs.album_mode:
						self.tauon.goto_album(select)
				else:
					self.d_click_ref = artist
					self.d_click_timer.set()

			if self.inp.middle_click:
				self.click_ref = artist
				self.click_highlight_timer.set()
				self.tauon.create_artist_pl(artist)

			if self.inp.right_click:
				self.click_ref = artist
				self.click_highlight_timer.set()

				self.artist_list_menu.activate(in_reference=artist)

	def render(self, x: int, y: int, w: int, h: int) -> None:
		if self.prefs.artist_list_style == 1:
			self.tab_h = round(60 * self.gui.scale)
		else:
			self.tab_h = round(22 * self.gui.scale)

		viewing_pl_id = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].uuid_int

		# use parent playlst is set
		if self.pctl.multi_playlist[self.pctl.active_playlist_viewing].parent_playlist_id:

			# test if parent still exists
			new = self.pctl.id_to_pl(self.pctl.multi_playlist[self.pctl.active_playlist_viewing].parent_playlist_id)
			if new is None:
				self.pctl.multi_playlist[self.pctl.active_playlist_viewing].parent_playlist_id = 0
			else:
				viewing_pl_id = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].parent_playlist_id

		if viewing_pl_id in self.saves:
			self.current_artists = self.saves[viewing_pl_id].all_artists
			self.current_album_counts = self.saves[viewing_pl_id].album_counts
			self.current_artist_track_counts = self.saves[viewing_pl_id].artist_track_counts
			self.scroll_position = self.saves[viewing_pl_id].scroll_position

			if self.saves[viewing_pl_id].playlist_length != len(self.pctl.multi_playlist[self.pctl.id_to_pl(viewing_pl_id)].playlist_ids):
				del self.saves[viewing_pl_id]
				return
		else:
			# if self.current_pl != viewing_pl_id:
			self.id_to_load = viewing_pl_id
			if not self.load:
				# self.prep()
				self.current_artists = []
				self.current_album_counts = []
				self.current_artist_track_counts = {}
				self.load = True
				self.thread_manager.ready("worker")

		area = (x, y, w, h)
		area2 = (x + 1, y, w - 3, h)

		self.ddt.rect(area, self.colours.side_panel_background)
		self.ddt.text_background_colour = self.colours.side_panel_background

		item_height = self.tab_h
		touch_scroll = self.inp.touch_scroll_y != 0 and coll_point(self.inp.touch_position, area)
		use_smooth_scroll = (
			self.smooth_scroll.enabled()
			or touch_scroll
			or self.smooth_scroll.active("artist list")
		)
		if use_smooth_scroll:
			if self.coll(area) and self.inp.mouse_wheel:
				mx = 1
				if self.prefs.artist_list_style == 2:
					mx = 3
				self.smooth_scroll.add_wheel_motion("artist list", -self.inp.mouse_wheel, item_height * mx)
			if self.inp.touch_released:
				self.smooth_scroll.release_touch("artist list")
			elif touch_scroll:
				self.smooth_scroll.apply_touch_drag("artist list", -self.inp.touch_scroll_y)
			self.scroll_position += self.smooth_scroll.step_motion("artist list") / max(item_height, 1)
		elif self.coll(area) and self.inp.mouse_wheel:
			mx = 1
			if self.prefs.artist_list_style == 2:
				mx = 3
			self.scroll_position -= self.smooth_scroll.scroll("artist list", mx)

		self.scroll_position = max(self.scroll_position, 0)

		range = (h // self.tab_h) - 1

		whole_range = math.floor(h // self.tab_h)

		if range > 4 and self.scroll_position > len(self.current_artists) - range:
			self.scroll_position = len(self.current_artists) - range

		if len(self.current_artists) <= whole_range:
			self.scroll_position = 0

		self.fields.add(area2)
		scroll_x = x + w - 18 * self.gui.scale
		if self.colours.lm:
			scroll_x = x + w - 22 * self.gui.scale
		if (self.coll(area2) or self.tauon.artist_list_scroll.held) and not self.tauon.pref_box.enabled:
			scroll_width = 15 * self.gui.scale
			inset = 0
			if self.gui.compact_artist_list:
				pass
				# scroll_width = round(6 * self.gui.scale)
				# scroll_x += round(9 * self.gui.scale)
			else:
				self.scroll_position = self.tauon.artist_list_scroll.draw(
					scroll_x, y + 1, scroll_width, h, self.scroll_position,
					len(self.current_artists) - range, r_click=self.inp.right_click,
					jump_distance=35, extend_field=6 * self.gui.scale)

		if not self.current_artists:
			text = _("No artists in playlist")

			if self.pctl.default_playlist:
				text = _("Artist threshold not met")
			if self.load:
				text = _("Loading Artist List...")
				if self.pctl.loading_in_progress or self.tauon.transcode_list or self.tauon.after_scan:
					text = _("Busy...")

			self.ddt.text(
				(x + w // 2, y + (h // 7), 2), text, alpha_mod(self.colours.side_bar_line2, 100), 212,
				max_w=w - 17 * self.gui.scale)

		i = int(self.scroll_position)
		yy = y + 12 * self.gui.scale - ((self.scroll_position - i) * self.tab_h)

		if viewing_pl_id in self.saves:
			self.saves[viewing_pl_id].scroll_position = self.scroll_position

		prefetch_mode = False
		prefetch_distance = 22

		self.shown_letters.clear()

		self.hover_any = False

		for i, artist in enumerate(self.current_artists[i:], start=i):
			if not prefetch_mode:
				self.draw_card(artist, x, round(yy), w)

				yy += self.tab_h

				# Enter prefetch (stop drawing) only once the *next* card's top has
				# passed the bottom edge of the widget. Using a 24px margin here
				# culled cards while their top was still inside the widget, so with
				# smooth scrolling items vanished ~24px before scrolling off.
				if yy - y >= h:
					prefetch_mode = True
					continue

			if prefetch_mode:
				if self.prefs.artist_list_style == 2:
					break
				prefetch_distance -= 1
				if prefetch_distance < 1:
					break
				if artist not in self.thumb_cache:
					self.load_img(artist)
					break

		if not self.hover_any:
			self.gui.preview_artist = ""
			self.hover_timer.force_set(10)
			self.artist_preview_render.show = False
			self.hover_on = False
class TreeView:

	def __init__(self, tauon: _PlaylistApp, pctl: _PlaylistPlayer) -> None:
		self.tauon                 = tauon
		self.pctl                  = pctl
		self.ddt                   = tauon.ddt
		self.inp                   = tauon.inp
		self.gui                   = tauon.gui
		self.coll                  = tauon.coll
		self.windows                  = tauon.windows
		self.prefs                 = tauon.prefs
		self.fields                = tauon.fields
		self.colours               = tauon.colours
		self.formats               = tauon.formats
		self.window_size           = tauon.window_size
		self.smooth_scroll         = tauon.smooth_scroll
		self.tree_view_scroll      = pctl.tree_view_scroll
		self.folder_tree_menu      = tauon.folder_tree_menu
		self.folder_tree_stem_menu = tauon.folder_tree_stem_menu
		self.trees = {}  # Per playlist tree
		self.rows = []  # For display (parsed from tree)
		self.rows_id = ""

		self.opens = {}  # Folders clicks to show per playlist

		self.scroll_positions = {}

		# Recursive gen_rows vars
		self.count = 0
		self.depth = 0

		self.background_processing = False
		self.d_click_timer = Timer(100)
		self.d_click_id = ""

		self.menu_selected = ""
		self.folder_colour_cache = {}
		self.dragging_name = ""

		self.force_opens = []
		self.click_drag_source = None

		self.tooltip_on = ""
		self.tooltip_timer = Timer(10)

		self.lock_pl: int | None = None

		# self.bold_colours = ColourGenCache(0.6, 0.7)

	def clear_all(self) -> None:
		self.rows_id = ""
		self.trees.clear()

	def collapse_all(self) -> None:
		pl_id = self.pctl.pl_to_id(self.pctl.active_playlist_viewing)

		if self.lock_pl:
			pl_id = self.lock_pl

		opens = self.opens.get(pl_id)
		if opens is None:
			opens = []
			self.opens[pl_id] = opens

		opens.clear()
		self.rows_id = ""

	def clear_target_pl(self, pl_number: int, pl_id=None) -> None:
		if pl_id is None:
			pl_id = self.pctl.pl_to_id(pl_number)

		if self.gui.lsp and self.prefs.left_panel_mode == "folder view":
			if pl_id in self.trees and not self.background_processing:
				self.background_processing = True
				shoot_dl = threading.Thread(target=self.gen_tree, args=[pl_id])
				shoot_dl.daemon = True
				shoot_dl.start()
		elif pl_id in self.trees:
			del self.trees[pl_id]

	def show_track(self, track: TrackClass) -> None:
		if track is None:
			return

		# Get tree and opened folder data for this playlist
		pl_id = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].uuid_int
		opens = self.opens.get(pl_id)
		if opens is None:
			opens = []
			self.opens[pl_id] = opens

		tree = self.trees.get(pl_id)
		if not tree:
			return

		scroll_position = self.scroll_positions.get(pl_id)
		if scroll_position is None:
			scroll_position = 0

		# Clear all opened folders
		opens.clear()

		# Set every folder in path as opened
		path = ""
		crumbs = track.parent_folder_path.split("/")[1:]
		for c in crumbs:
			path += "/" + c
			opens.append(path)

		# Regenerate row display
		self.gen_rows(tree, opens)

		# Locate and set scroll position to playing folder
		for i, row in enumerate(self.rows):
			if row[1] + "/" + row[0] == track.parent_folder_path:

				scroll_position = i - 5
				scroll_position = max(scroll_position, 0)
				break

		max_scroll = len(self.rows) - ((self.window_size[0] - (self.gui.panelY + self.gui.panelBY)) // round(22 * self.gui.scale))
		scroll_position = min(scroll_position, max_scroll)
		scroll_position = max(scroll_position, 0)

		self.scroll_positions[pl_id] = scroll_position

		self.gui.update_layout = True
		self.gui.request_frame()

	def get_pl_id(self) -> int:
		if self.lock_pl is not None:
			# The locked playlist may have been deleted; unlock automatically.
			if self.pctl.id_to_pl(self.lock_pl) is not None:
				return self.lock_pl
			self.lock_pl = None
		return self.pctl.multi_playlist[self.pctl.active_playlist_viewing].uuid_int

	def render(self, x: int, y: int, w: int, h: int) -> None:
		pl_id = self.get_pl_id()
		tree = self.trees.get(pl_id)

		# Generate tree data if not done yet
		if tree is None:
			if not self.background_processing:
				self.background_processing = True
				shoot_dl = threading.Thread(target=self.gen_tree, args=[pl_id])
				shoot_dl.daemon = True
				shoot_dl.start()

			self.playlist_id_on = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].uuid_int

		opens = self.opens.get(pl_id)
		if opens is None:
			opens = []
			self.opens[pl_id] = opens

		scroll_position = self.scroll_positions.get(pl_id)
		if scroll_position is None:
			scroll_position = 0

		area = (x, y, w, h)
		self.fields.add(area)
		self.ddt.rect(area, self.colours.side_panel_background)
		self.ddt.text_background_colour = self.colours.side_panel_background

		if self.background_processing and self.rows_id != pl_id:
			self.ddt.text(
				(x + w // 2, y + (h // 7), 2), _("Loading Folder Tree..."), alpha_mod(self.colours.side_bar_line2, 100),
				212, max_w=w - 17 * self.gui.scale)
			return

		# if not tree or not self.rows:
		#     self.ddt.text((x + w // 2, y + (h // 7), 2), _("Folder Tree"), alpha_mod(self.colours.side_bar_line2, 100),
		#              212, max_w=w - 17 * self.gui.scale)
		#     return
		if not tree:
			self.ddt.text(
				(x + w // 2, y + (h // 7), 2), _("Folder Tree"), alpha_mod(self.colours.side_bar_line2, 100),
				212, max_w=w - 17 * self.gui.scale)
			return

		if self.rows_id != pl_id:
			if not self.background_processing:
				self.gen_rows(tree, opens)
				self.rows_id = pl_id
				max_scroll = len(self.rows) - (h // round(22 * self.gui.scale))
				scroll_position = min(scroll_position, max_scroll)

			else:
				return

		if not self.rows:
			self.ddt.text(
				(x + w // 2, y + (h // 7), 2), _("Folder Tree"), alpha_mod(self.colours.side_bar_line2, 100),
				212, max_w=w - 17 * self.gui.scale)
			return

		spacing = round(21 * self.gui.scale)
		max_scroll = len(self.rows) - (h // round(22 * self.gui.scale))

		mouse_in = self.coll(area)
		touch_scroll = self.inp.touch_scroll_y != 0 and coll_point(self.inp.touch_position, area)
		use_smooth_scroll = (
			self.smooth_scroll.enabled()
			or touch_scroll
			or self.smooth_scroll.active("tree view")
		)

		# Mouse wheel scrolling
		if use_smooth_scroll:
			if mouse_in and self.inp.mouse_wheel:
				self.smooth_scroll.add_wheel_motion("tree view", -self.inp.mouse_wheel, spacing * 2)
			if self.inp.touch_released:
				self.smooth_scroll.release_touch("tree view")
			elif touch_scroll:
				self.smooth_scroll.apply_touch_drag("tree view", -self.inp.touch_scroll_y)
			scroll_position += self.smooth_scroll.step_motion("tree view") / max(spacing, 1)
			scroll_position = max(scroll_position, 0)
			scroll_position = min(scroll_position, max_scroll)
		elif mouse_in and self.inp.mouse_wheel:
			scroll_position -= self.smooth_scroll.scroll("tree view",2)
			scroll_position = max(scroll_position, 0)
			scroll_position = min(scroll_position, max_scroll)

		focused = self.tauon.is_level_zero()

		# Draw scroll bar
		if mouse_in or self.tree_view_scroll.held:
			scroll_position = self.tree_view_scroll.draw(
				x + w - round(12 * self.gui.scale), y + 1, round(11 * self.gui.scale), h,
				scroll_position,
				max_scroll, r_click=self.inp.right_click, jump_distance=40)

		self.scroll_positions[pl_id] = scroll_position
		scroll_start = int(scroll_position)
		scroll_offset = (scroll_position - scroll_start) * spacing
		yy = y + round(11 * self.gui.scale) - scroll_offset
		xx = x + round(22 * self.gui.scale)

		# Draw folder rows
		playing_track = self.pctl.playing_object()
		max_w = w - round(45 * self.gui.scale)

		light_mode = test_lumi(self.colours.side_panel_background) < 0.5
		semilight_mode = test_lumi(self.colours.side_panel_background) < 0.8

		for i, item in enumerate(self.rows):

			if i < scroll_start:
				continue

			if yy > y + h - spacing:
				break

			target = item[1] + "/" + item[0]

			inset = item[2] * round(10 * self.gui.scale)
			rect = (xx + inset - round(15 * self.gui.scale), yy, max_w - inset + round(15 * self.gui.scale), spacing - 1)
			self.fields.add(rect)

			# text_colour = ColourRGBA(255, 255, 255, 100)
			text_colour = rgb_add_hls(self.colours.side_panel_background, 0, 0.35, -0.15)

			box_colour = ColourRGBA(200, 100, 50, 255)

			if semilight_mode:
				text_colour = ColourRGBA(255, 255, 255, 180)

			if light_mode:
				text_colour = ColourRGBA(0, 0, 0, 200)

			full_folder_path = item[1] + "/" + item[0]

			# Hold highlight while menu open
			if (self.folder_tree_menu.active or self.folder_tree_stem_menu.active) and full_folder_path == self.menu_selected:
				text_colour = ColourRGBA(255, 255, 255, 170)
				if semilight_mode:
					text_colour = ColourRGBA(255, 255, 255, 255)
				if light_mode:
					text_colour = ColourRGBA(0, 0, 0, 255)

			# Hold highlight while dragging folder
			if self.inp.quick_drag and not point_proximity_test(self.gui.drag_source_position, self.inp.mouse_position, 15):
				if self.gui.shift_selection:
					if self.pctl.get_track(self.pctl.multi_playlist[self.pctl.id_to_pl(pl_id)].playlist_ids[self.gui.shift_selection[0]]).fullpath.startswith(
							full_folder_path + "/") and self.dragging_name and item[0].endswith(self.dragging_name):
						text_colour = ColourRGBA(255, 255, 255, 230)
						if semilight_mode:
							text_colour = ColourRGBA(255, 255, 255, 255)
						if light_mode:
							text_colour = ColourRGBA(0, 0, 0, 255)

			# Set highlight colours if folder is playing
			if (self.pctl.playing_state in (PlayingState.PLAYING, PlayingState.PAUSED)) and playing_track:
				if playing_track.parent_folder_path == full_folder_path or full_folder_path + "/" in playing_track.fullpath:
					text_colour = ColourRGBA(255, 255, 255, 225)
					box_colour  = ColourRGBA(140, 220, 20, 255)
					if semilight_mode:
						text_colour = ColourRGBA(255, 255, 255, 255)
					if light_mode:
						text_colour = ColourRGBA(0, 0, 0, 255)

			if self.inp.right_click:
				mouse_in = self.coll(rect) and self.tauon.is_level_zero(False)
			else:
				mouse_in = self.coll(rect) and focused and not (
					self.inp.quick_drag and not point_proximity_test(self.gui.drag_source_position, self.inp.mouse_position, 15))

			if mouse_in and not self.tree_view_scroll.held:
				if self.inp.middle_click:
					self.tauon.stem_to_new_playlist(full_folder_path)
				elif self.inp.right_click:
					if item[3]:
						for p, id in enumerate(self.pctl.multi_playlist[self.pctl.id_to_pl(pl_id)].playlist_ids):
							if self.windows:
								if self.pctl.get_track(id).fullpath.startswith(target.lstrip("/")):
									self.folder_tree_menu.activate(in_reference=MenuTrackRef(id, p, pl_id))
									self.menu_selected = full_folder_path
									break
							elif self.pctl.get_track(id).fullpath.startswith(target):
								self.folder_tree_menu.activate(in_reference=MenuTrackRef(id, p, pl_id))
								self.menu_selected = full_folder_path
								break
					elif self.windows:
						self.folder_tree_stem_menu.activate(in_reference=full_folder_path.lstrip("/"))
						self.menu_selected = full_folder_path.lstrip("/")
					else:
						self.folder_tree_stem_menu.activate(in_reference=full_folder_path)
						self.menu_selected = full_folder_path

				elif self.inp.mouse_click:
					# self.inp.quick_drag = True
					if not self.click_drag_source:
						self.click_drag_source = item
						self.gui.set_drag_source()

				elif self.inp.mouse_up and self.click_drag_source == item:
					# Click tree level folder to open/close branch

					if target not in opens:
						opens.append(target)
					else:
						for s in reversed(range(len(opens))):
							if opens[s].startswith(target):
								del opens[s]

					if item[3]:
						# Locate the first track of folder in playlist
						track_id = None
						for p, id in enumerate(self.pctl.default_playlist):
							if self.windows:
								if self.pctl.get_track(id).fullpath.startswith(target.lstrip("/")):
									track_id = id
									break
							elif self.pctl.get_track(id).fullpath.startswith(target):
								track_id = id
								break
						else:  # Fallback to folder name if full-path not found (hack for networked items)
							for p, id in enumerate(self.pctl.default_playlist):
								if self.pctl.get_track(id).parent_folder_name == item[0]:
									track_id = id
									break

						if track_id is not None:
							# Single click base folder to locate in playlist
							if self.d_click_timer.get() > 0.5 or self.d_click_id != target:
								self.pctl.show_current(select=True, index=track_id, no_switch=True, highlight=True, folder_list=False)
								self.d_click_timer.set()
								self.d_click_id = target

							# Double click base folder to play
							else:
								self.pctl.jump(track_id)

					# Regenerate display rows after clicking
					self.gen_rows(tree, opens)

			# Highlight folder text on mouse over
			if (mouse_in and not self.inp.mouse_down) or item == self.click_drag_source:
				text_colour = ColourRGBA(255, 255, 255, 235)
				if semilight_mode:
					text_colour = ColourRGBA(255, 255, 255, 255)
				if light_mode:
					text_colour = ColourRGBA(0, 0, 0, 255)

			# Render folder name text
			if item[4] > 50:
				font = 514
				text_label_colour = text_colour  # self.bold_colours.get(full_folder_path)
			else:
				font = 414
				text_label_colour = text_colour

			if mouse_in:
				tw = self.ddt.get_text_w(item[0], font)

				if self.tooltip_on != item:
					self.tooltip_on = item
					self.tooltip_timer.set()
					self.gui.frame_callback_list.append(TestTimer(0.6))

				if tw > max_w - inset and self.tooltip_on == item and self.tooltip_timer.get() >= 0.6:
					rect = (xx + inset, yy - 2 * self.gui.scale, tw + round(20 * self.gui.scale), 20 * self.gui.scale)
					self.ddt.rect(rect, self.ddt.text_background_colour)
					self.ddt.text((xx + inset, yy), item[0], text_label_colour, font)
				else:
					self.ddt.text((xx + inset, yy), item[0], text_label_colour, font, max_w=max_w - inset)
			else:
				self.ddt.text((xx + inset, yy), item[0], text_label_colour, font, max_w=max_w - inset)

			# # Draw inset bars
			# for m in range(item[2] + 1):
			#     if m == 0:
			#         continue
			#     colour = ColourRGBA(255, 255, 255, 20)
			#     if semilight_mode:
			#         colour = ColourRGBA(255, 255, 255, 30)
			#     if light_mode:
			#         colour = ColourRGBA(0, 0, 0, 60)
			#
			#     if i > 0 and self.rows[i - 1][2] == m - 1:  # the top one needs to be slightly lower lower
			#         self.ddt.rect((x + (12 * m) + 2, yy - round(1 * self.gui.scale), round(1 * self.gui.scale), round(17 * self.gui.scale)), colour, True)
			#     else:
			#         self.ddt.rect((x + (12 * m) + 2, yy - round(5 * self.gui.scale), round(1 * self.gui.scale), round(21 * self.gui.scale)), colour, True)

			if self.prefs.folder_tree_codec_colours:
				box_colour = self.folder_colour_cache.get(full_folder_path)
				if box_colour is None:
					box_colour = ColourRGBA(150, 150, 150, 255)

			# Draw indicator box and +/- icons next to folder name
			if item[3]:
				rect = (xx + inset - round(9 * self.gui.scale), yy + round(7 * self.gui.scale), round(4 * self.gui.scale),
						round(4 * self.gui.scale))
				if light_mode or semilight_mode:
					border = round(1 * self.gui.scale)
					self.ddt.rect((rect[0] - border, rect[1] - border, rect[2] + border * 2, rect[3] + border * 2), ColourRGBA(0, 0, 0, 150))
				self.ddt.rect(rect, box_colour)

			elif True:
				if not mouse_in or self.tree_view_scroll.held:
					# text_colour = ColourRGBA(255, 255, 255, 50)
					text_colour = rgb_add_hls(self.colours.side_panel_background, 0, 0.2, -0.10)
					if semilight_mode:
						text_colour = ColourRGBA(255, 255, 255, 70)
					if light_mode:
						text_colour = ColourRGBA(0, 0, 0, 70)
				if target in opens:
					self.ddt.text((xx + inset - round(7 * self.gui.scale), yy + round(1 * self.gui.scale), 2), "-", text_colour, 19)
				else:
					self.ddt.text((xx + inset - round(7 * self.gui.scale), yy + round(1 * self.gui.scale), 2), "+", text_colour, 19)

			yy += spacing

		if self.click_drag_source and not point_proximity_test(self.gui.drag_source_position, self.inp.mouse_position, 15) and \
			self.pctl.default_playlist is self.pctl.multi_playlist[self.pctl.id_to_pl(pl_id)].playlist_ids:
			self.inp.quick_drag = True
			self.gui.playlist_hold = True

			self.dragging_name = self.click_drag_source[0]
			logging.info(self.dragging_name)

			if "/" in self.dragging_name:
				self.dragging_name = os.path.basename(self.dragging_name)

			self.gui.shift_selection.clear()
			self.gui.set_drag_source()
			for p, id in enumerate(self.pctl.multi_playlist[self.pctl.id_to_pl(pl_id)].playlist_ids):
				if self.windows:
					if self.pctl.get_track(id).fullpath.startswith(
							self.click_drag_source[1].lstrip("/") + "/" + self.click_drag_source[0] + "/"):
						self.gui.shift_selection.append(p)
				elif self.pctl.get_track(id).fullpath.startswith(f"{self.click_drag_source[1]}/{self.click_drag_source[0]}/"):
					self.gui.shift_selection.append(p)
			self.click_drag_source = None

		if self.dragging_name and not self.inp.quick_drag:
			self.dragging_name = ""
		if not self.inp.mouse_down:
			self.click_drag_source = None

	def gen_row(self, tree_point, path, opens) -> None:

		for item in tree_point:
			p = path + "/" + item[1]
			self.count += 1
			enter_level = False
			if len(tree_point) > 1 or path in self.force_opens:  # Ignore levels that are only a single folder wide

				if path in opens or self.depth == 0 or path in self.force_opens:  # Only show if parent stem is open, but always show the root displayed folders

					# If there is a single base folder in subfolder, combine the path and show it in upper level
					if len(item[0]) == 1 and len(item[0][0][0]) == 1 and len(item[0][0][0][0][0]) == 0:
						self.rows.append(
							[item[1] + "/" + item[0][0][1] + "/" + item[0][0][0][0][1], path, self.depth, True, len(item[0])])
					elif len(item[0]) == 1 and len(item[0][0][0]) == 0:
						self.rows.append([item[1] + "/" + item[0][0][1], path, self.depth, True, len(item[0])])

					# Add normal base folder type
					else:
						self.rows.append([item[1], path, self.depth, len(item[0]) == 0, len(item[0])])  # Folder name, folder path, depth, is bottom

					# If folder is open and has only one subfolder, mark that subfolder as open
					if len(item[0]) == 1 and (p in opens or p in self.force_opens):
						self.force_opens.append(p + "/" + item[0][0][1])

				self.depth += 1
				enter_level = True

			self.gen_row(item[0], p, opens)

			if enter_level:
				self.depth -= 1

	def gen_rows(self, tree, opens) -> None:
		self.count = 0
		self.depth = 0
		self.rows.clear()
		self.force_opens.clear()

		self.gen_row(tree, "", opens)

		self.gui.update_layout = True
		self.gui.request_frame()

	def gen_tree(self, pl_id: int) -> None:
		pl_no = self.pctl.id_to_pl(pl_id)
		if pl_no is None:
			self.background_processing = False
			self.gui.request_frame()
			self.tauon.wake()
			return

		playlist = self.pctl.multi_playlist[pl_no].playlist_ids
		# Generate list of all unique folder paths
		paths = []
		z = 5000
		for p in playlist:
			z += 1
			if z > 1000:
				time.sleep(0.01)  # Throttle thread
				z = 0
			track = self.pctl.get_track(p)
			path = track.parent_folder_path
			if path not in paths:
				paths.append(path)
				self.folder_colour_cache[path] = self.formats.colours.get(track.file_ext)

		# Genterate tree from folder paths
		tree = []
		news = []
		for path in paths:
			z += 1
			if z > 5000:
				time.sleep(0.01)  # Throttle thread
				z = 0
			split_path = path.split("/")
			on = tree
			for level in split_path:
				if not level:
					continue
				# Find if level already exists
				for sub_level in on:
					if sub_level[1] == level:
						on = sub_level[0]
						break
				else:  # Create new level
					new = [[], level]
					news.append(new)
					on.append(new)
					on = new[0]

		self.trees[pl_id] = tree
		self.rows_id = ""
		self.background_processing = False
		self.gui.request_frame()
		self.tauon.wake()
class QueueBox:

	def __init__(self, tauon: _PlaylistApp, pctl: _PlaylistPlayer) -> None:
		self.tauon         = tauon
		self.pctl          = pctl
		self.ddt           = tauon.ddt
		self.gui           = tauon.gui
		self.inp           = tauon.inp
		self.coll          = tauon.coll
		self.prefs         = tauon.prefs
		self.colours       = tauon.colours
		self.window_size   = tauon.window_size
		self.queue_menu    = tauon.queue_menu
		self.smooth_scroll = tauon.smooth_scroll
		self.dragging = None
		self.fq = []
		self.drag_start_y = 0
		self.drag_start_top = 0
		self.tab_h = 0
		self.scroll_position: int = 0
		self.right_click_id = None
		self.d_click_ref = None
		self.recalc()

		self.queue_menu.add(MenuItem(_("Remove This"), self.right_remove_item, show_test=self.queue_remove_show))
		self.queue_menu.add(MenuItem(_("Play Now"), self.play_now, show_test=self.queue_remove_show))
		self.queue_menu.add(MenuItem(_("Auto-Stop Here"), self.toggle_auto_stop, self.toggle_auto_stop_deco, show_test=self.queue_remove_show))

		self.queue_menu.add(MenuItem(_("Pause Queue"), self.toggle_pause, tauon.queue_pause_deco))
		self.queue_menu.add(MenuItem(_("Clear Queue"), tauon.clear_queue, tauon.queue_deco, hint="Alt+Shift+Q"))

		self.queue_menu.add(MenuItem(_("↳ Except for This"), self.clear_queue_crop, show_test=self.except_for_this_show_test))

		self.queue_menu.add(MenuItem(_("Queue to New Playlist"), self.make_as_playlist, tauon.queue_deco))
		# self.queue_menu.add("Finish Playing Album", tauon.finish_current, tauon.finish_current_deco)

	def recalc(self) -> None:
		self.tab_h = 34 * self.gui.scale

	def except_for_this_show_test(self, ref) -> bool:
		return self.queue_remove_show(ref) and self.inp.test_shift(ref)

	def make_as_playlist(self) -> None:
		if self.pctl.force_queue:
			playlist = []
			for item in self.pctl.force_queue:
				if item.type == QueueType.TRACK:
					playlist.append(item.track_id)
				else:

					pl = self.pctl.id_to_pl(item.playlist_id)
					if pl is None:
						logging.info("Lost the target playlist")
						continue

					pp = self.pctl.multi_playlist[pl].playlist_ids

					i = item.position  # = self.pctl.playlist_playing_position + 1

					parts = []
					album_parent_path = self.pctl.get_track(item.track_id).parent_folder_path

					while i < len(pp):
						if self.pctl.get_track(pp[i]).parent_folder_path != album_parent_path:
							break

						parts.append((pp[i], i))
						i += 1

					for part in parts:
						playlist.append(part[0])

			self.pctl.multi_playlist.append(
				self.tauon.pl_gen(
					title=_("Queued Tracks"),
					playlist_ids=copy.deepcopy(playlist),
					hide_title=False))

	def drop_tracks_insert(self, insert_position) -> None:
		if not self.gui.shift_selection:
			return

		# remove incomplete album from queue
		if insert_position == 0 and self.pctl.force_queue and self.pctl.force_queue[0].album_stage == 1:
			self.tauon.split_queue_album(self.pctl.force_queue[0].uuid_int)

		playlist_index = self.pctl.active_playlist_viewing
		playlist_id = self.pctl.pl_to_id(self.pctl.active_playlist_viewing)

		main_track_position = self.gui.shift_selection[0]
		main_track_id = self.pctl.default_playlist[main_track_position]
		self.inp.quick_drag = False

		if len(self.gui.shift_selection) > 1:
			# if shift selection contains only same folder
			for position in self.gui.shift_selection:
				if self.pctl.get_track(self.pctl.default_playlist[position]).parent_folder_path != self.pctl.get_track(
						main_track_id).parent_folder_path or self.inp.key_ctrl_down:
					break
			else:
				# Add as album type
				self.pctl.force_queue.insert(
					insert_position, queue_item_gen(main_track_id, main_track_position, playlist_id, QueueType.ALBUM))
				return

		if len(self.gui.shift_selection) == 1:
			self.pctl.force_queue.insert(insert_position, queue_item_gen(main_track_id, main_track_position, playlist_id))
		else:
			# Add each track
			for position in reversed(self.gui.shift_selection):
				self.pctl.force_queue.insert(
					insert_position, queue_item_gen(self.pctl.default_playlist[position], position, playlist_id))

	def clear_queue_crop(self) -> None:
		save = False
		for item in self.pctl.force_queue:
			if item.uuid_int == self.right_click_id:
				save = item
				break

		self.tauon.clear_queue()
		if save:
			self.pctl.force_queue.append(save)

	def play_now(self) -> None:
		queue_item = None
		queue_index = 0
		for i, item in enumerate(self.pctl.force_queue):
			if item.uuid_int == self.right_click_id:
				queue_item = item
				queue_index = i
				break
		else:
			return

		del self.pctl.force_queue[queue_index]
		# [trackid, position, pl_id, type, album_stage, uid_gen(), auto_stop]

		if self.pctl.force_queue and self.pctl.force_queue[0].album_stage == 1:
			self.tauon.split_queue_album(None)

		target_track_id = queue_item.track_id

		pl = self.pctl.id_to_pl(queue_item.playlist_id)
		if pl is not None:
			self.pctl.active_playlist_playing = pl

		if target_track_id not in self.pctl.playing_playlist():
			self.pctl.advance()
			return

		self.pctl.jump(target_track_id, queue_item.position)

		if queue_item.type == QueueType.ALBUM:
			queue_item.album_stage = 1  # set as partway playing
			self.pctl.force_queue.insert(0, queue_item)

	def toggle_auto_stop(self) -> None:
		for item in self.pctl.force_queue:
			if item.uuid_int == self.right_click_id:
				item.auto_stop ^= True
				break

	def toggle_auto_stop_deco(self) -> Decorator:
		enabled = False
		for item in self.pctl.force_queue:
			if item.uuid_int == self.right_click_id and item.auto_stop:
				enabled = True
				break

		if enabled:
			return Decorator(self.colours.menu_text, self.colours.menu_background, _("Cancel Auto-Stop"))
		return Decorator(self.colours.menu_text, self.colours.menu_background, _("Auto-Stop"))

	def queue_remove_show(self, _unused: int) -> bool:
		return self.right_click_id is not None

	def right_remove_item(self) -> None:
		if self.right_click_id is None:
			self.show_message(_("Eh?"))

		for u in reversed(range(len(self.pctl.force_queue))):
			if self.pctl.force_queue[u].uuid_int == self.right_click_id:
				del self.pctl.force_queue[u]
				self.gui.request_tracklist_redraw()
				break
		else:
			self.show_message(_("Looks like it's gone now anyway"))

	def toggle_pause(self) -> None:
		self.pctl.pause_queue ^= True

	def draw_card(
		self,
		x: int, y: int,
		w: int, h: int,
		yy: int,
		track: TrackClass, fqo: TauonQueueItem,
		draw_back: bool = False, draw_album_indicator: bool = True,
	) -> None:

		# text_colour = ColourRGBA(230, 230, 230, 255)
		bg = self.colours.queue_background

		# if fq[i].type == QueueType.TRACK:

		rect = (x + 13 * self.gui.scale, yy, w - 28 * self.gui.scale, self.tab_h)

		if draw_back:
			self.ddt.rect(rect, self.colours.queue_card_background)
			bg = self.colours.queue_card_background

		text_colour1 = rgb_add_hls(bg, 0, 0.28, -0.15)  # [255, 255, 255, 70]
		text_colour2 = ColourRGBA(255, 255, 255, 230)
		if test_lumi(bg) < 0.2:
			text_colour1 = ColourRGBA(0, 0, 0, 130)
			text_colour2 = ColourRGBA(0, 0, 0, 230)

		self.tauon.gall_ren.render(track, (rect[0] + 4 * self.gui.scale, rect[1] + 4 * self.gui.scale), round(28 * self.gui.scale))

		self.ddt.rect((rect[0] + 4 * self.gui.scale, rect[1] + 4 * self.gui.scale, 26, 26), ColourRGBA(0, 0, 0, 6))

		line = track.album
		if fqo.type == QueueType.TRACK:
			line = track.title

		if not line:
			line = clean_string(track.filename)

		line2y = yy + 14 * self.gui.scale

		artist_line = track.artist
		if fqo.type == QueueType.ALBUM and track.album_artist:
			artist_line = track.album_artist

		if fqo.type == QueueType.TRACK and not artist_line:
			line2y -= 7 * self.gui.scale

		self.ddt.text(
			(rect[0] + (40 * self.gui.scale), yy - 1 * self.gui.scale), artist_line, text_colour1, 210,
			max_w=rect[2] - 60 * self.gui.scale, bg=bg)

		self.ddt.text(
			(rect[0] + (40 * self.gui.scale), line2y), line, text_colour2, 211,
			max_w=rect[2] - 60 * self.gui.scale, bg=bg)

		if draw_album_indicator:
			if fqo.type == QueueType.ALBUM:
				if fqo.album_stage == 0:
					self.ddt.rect((rect[0] + rect[2] - 5 * self.gui.scale, rect[1], 5 * self.gui.scale, rect[3]), ColourRGBA(220, 130, 20, 255))
				else:
					self.ddt.rect((rect[0] + rect[2] - 5 * self.gui.scale, rect[1], 5 * self.gui.scale, rect[3]), ColourRGBA(140, 220, 20, 255))

			if fqo.auto_stop:
				xx = rect[0] + rect[2] - 9 * self.gui.scale
				if fqo.type == QueueType.ALBUM:
					xx -= 11 * self.gui.scale
				self.ddt.rect((xx, rect[1] + 5 * self.gui.scale, 7 * self.gui.scale, 7 * self.gui.scale), ColourRGBA(230, 190, 0, 255))

	def draw(self, x: int, y: int, w: int, h: int) -> None:
		yy = y
		yy += round(4 * self.gui.scale)

		sep_colour = alpha_blend(ColourRGBA(255, 255, 255, 11), self.colours.queue_background)

		if y > self.gui.panelY + 10 * self.gui.scale:  # Draw fancy light mode border
			self.gui.queue_frame_draw = y
		# else:
		# 	if not self.colours.lm:
		# 		self.ddt.rect((x, y, w, 3 * self.gui.scale),  self.colours.queue_background, True)

		yy += round(3 * self.gui.scale)

		box_rect = (x, yy - 6 * self.gui.scale, w, h)
		self.ddt.rect(box_rect, self.colours.queue_background)
		self.ddt.text_background_colour = self.colours.queue_background

		if self.coll(box_rect) and self.inp.quick_drag and not self.pctl.force_queue:
			self.ddt.rect(box_rect, ColourRGBA(255, 255, 255, 2))
			self.ddt.text_background_colour = alpha_blend(ColourRGBA(255, 255, 255, 2), self.ddt.text_background_colour)

		# if y < self.gui.panelY * 2:
		#     self.ddt.rect((x, y - 3 * self.gui.scale, w, 30 * self.gui.scale), self.colours.queue_background, True)

		if h > 40 * self.gui.scale:
			if not self.pctl.force_queue:
				text = _("Add to Queue") if self.inp.quick_drag else _("Queue")
				self.ddt.text((x + (w // 2), y + 15 * self.gui.scale, 2), text, alpha_mod(self.colours.index_text, 200), 212)

		qb_right_click = 0

		if self.coll(box_rect):
			# Update scroll position
			scroll_distance = self.smooth_scroll.scroll("queue")
			self.scroll_position -= scroll_distance
			self.scroll_position = max(self.scroll_position, 0)

			if self.inp.right_click:
				qb_right_click = 1

		# text_colour = ColourRGBA(255, 255, 255, 91)
		text_colour = rgb_add_hls(self.colours.queue_background, 0, 0.3, -0.15)
		if test_lumi(self.colours.queue_background) < 0.2:
			text_colour = ColourRGBA(0, 0, 0, 200)

		line = _("Up Next:")
		if self.pctl.force_queue:
			# line = "Queue"
			self.ddt.text((x + (10 * self.gui.scale), yy + 2 * self.gui.scale), line, text_colour, 211)

		yy += 7 * self.gui.scale

		if len(self.pctl.force_queue) < 3:
			self.scroll_position = 0

		# Draw square dots to indicate view has been scrolled down
		if self.scroll_position > 0:
			ds = 3 * self.gui.scale
			gp = 4 * self.gui.scale

			self.ddt.rect((x + int(w / 2), yy, ds, ds), ColourRGBA(230, 190, 0, 255))
			self.ddt.rect((x + int(w / 2), yy + gp, ds, ds), ColourRGBA(230, 190, 0, 255))
			self.ddt.rect((x + int(w / 2), yy + gp + gp, ds, ds), ColourRGBA(230, 190, 0, 255))

		# Draw pause icon
		if self.pctl.pause_queue:
			self.ddt.rect((x + w - 24 * self.gui.scale, yy + 2 * self.gui.scale, 3 * self.gui.scale, 9 * self.gui.scale), ColourRGBA(230, 190, 0, 255))
			self.ddt.rect((x + w - 19 * self.gui.scale, yy + 2 * self.gui.scale, 3 * self.gui.scale, 9 * self.gui.scale), ColourRGBA(230, 190, 0, 255))

		yy += 6 * self.gui.scale

		yy += 10 * self.gui.scale

		i = 0

		# Get new copy of queue if not dragging
		if not self.dragging:
			self.fq = copy.deepcopy(self.pctl.force_queue)
		else:
			# self.gui.update += 1
			self.gui.update_on_drag = True

		# End drag if mouse not in correct state for it
		if not self.inp.mouse_down and not self.inp.mouse_up:
			self.dragging = None

		if not self.queue_menu.active:
			self.right_click_id = None

		fq = self.fq

		list_top = yy

		i: int = round(self.scroll_position)

		# Limit scroll distance
		if i > len(fq):
			self.scroll_position = len(fq)
			i = self.scroll_position

		showed_indicator = False
		list_extends = False
		x1 = x + 13 * self.gui.scale  # highlight position
		w1 = w - 28 * self.gui.scale - 10 * self.gui.scale

		while i < len(fq) + 1:
			# Stop drawing if past window
			if yy > self.window_size[1] - self.gui.panelBY - self.gui.panelY - (50 * self.gui.scale):
				list_extends = True
				break

			# Calculate drag collision box. Special case for first and last which extend out in y direction
			h_rect = (x + 13 * self.gui.scale, yy, w - 28 * self.gui.scale, self.tab_h + 3 * self.gui.scale)
			if i == len(fq):
				h_rect = (x + 13 * self.gui.scale, yy, w - 28 * self.gui.scale, self.tab_h + 3 * self.gui.scale + 1000 * self.gui.scale)
			if i == 0:
				h_rect = (
				0, yy - 1000 * self.gui.scale, w - 28 * self.gui.scale + 10000, self.tab_h + 3 * self.gui.scale + 1000 * self.gui.scale)

			if self.dragging is not None and self.coll(h_rect) and self.inp.mouse_up:
				ob = None
				for u in reversed(range(len(self.pctl.force_queue))):

					if self.pctl.force_queue[u].uuid_int == self.dragging:
						ob = self.pctl.force_queue[u]
						self.pctl.force_queue[u] = None
						break
				else:
					self.dragging = None

				if self.dragging:
					self.pctl.force_queue.insert(i, ob)
					self.dragging = None

				for u in reversed(range(len(self.pctl.force_queue))):
					if self.pctl.force_queue[u] is None:
						del self.pctl.force_queue[u]
						self.gui.request_tracklist_redraw()
						continue

					# Reset album in flag if not first item
					if self.pctl.force_queue[u].album_stage == 1:
						if u != 0:
							self.pctl.force_queue[u].album_stage = 0

				self.inp.mouse_click = False
				self.draw(x, y, w, h)
				return

			if i > len(fq) - 1:
				break

			track = self.pctl.get_track(fq[i].track_id)
			rect = (x + 13 * self.gui.scale, yy, w - 28 * self.gui.scale, self.tab_h)

			if self.inp.mouse_click and self.coll(rect):
				self.dragging = fq[i].uuid_int
				self.drag_start_y = self.inp.mouse_position[1]
				self.drag_start_top = yy

				if self.tauon.d_click_timer.get() < 1:
					if self.d_click_ref == fq[i].uuid_int:
						pl = self.pctl.id_to_pl(fq[i].playlist_id)
						if pl is not None:
							self.pctl.switch_playlist(pl)

						self.pctl.show_current(playing=False, highlight=True, index=fq[i].track_id)
						self.d_click_ref = None
				# else:
				self.d_click_ref = fq[i].uuid_int

				self.tauon.d_click_timer.set()

			if self.dragging and self.coll(h_rect):
				yy += self.tab_h
				yy += 4 * self.gui.scale

			if qb_right_click and self.coll(rect):
				self.right_click_id = fq[i].uuid_int
				qb_right_click = 2

			if self.inp.middle_click and self.coll(rect):
				self.pctl.force_queue.remove(fq[i])
				self.gui.request_tracklist_redraw()

			if fq[i].uuid_int == self.dragging:
				# self.ddt.rect_r(rect, [22, 22, 22, 255], True)
				pass
			else:

				db = False
				if fq[i].uuid_int == self.right_click_id:
					db = True

				self.draw_card(x, y, w, h, yy, track, fq[i], db)

				# Drag tracks from main playlist and insert ------------
				if self.inp.quick_drag:
					if x < self.inp.mouse_position[0] < x + w:
						y1 = yy - 4 * self.gui.scale
						y2 = y1
						h1 = self.tab_h // 2
						if i == 0:
							# Extend up if first element
							y1 -= 5 * self.gui.scale
							h1 += 10 * self.gui.scale

						insert_position = None

						if y1 < self.inp.mouse_position[1] < y1 + h1:
							self.ddt.rect((x1, yy - 2 * self.gui.scale, w1, 2 * self.gui.scale), self.colours.queue_drag_indicator_colour)
							showed_indicator = True

							if self.inp.mouse_up:
								insert_position = i
						elif y2 < self.inp.mouse_position[1] < y2 + self.tab_h + 5 * self.gui.scale:
							self.ddt.rect(
								(x1, yy + self.tab_h + 2 * self.gui.scale, w1, 2 * self.gui.scale),
								self.colours.queue_drag_indicator_colour)
							showed_indicator = True

							if self.inp.mouse_up:
								insert_position = i + 1

						if insert_position is not None:
							self.drop_tracks_insert(insert_position)

				# -----------------------------------------
				yy += self.tab_h
				yy += 4 * self.gui.scale

			i += 1

		# Show drag marker if mouse holding below list
		if self.inp.quick_drag and not list_extends and not showed_indicator and fq and self.inp.mouse_position[
			1] > yy - 4 * self.gui.scale and self.coll(box_rect):
			yy -= self.tab_h
			yy -= 4 * self.gui.scale
			self.ddt.rect((x1, yy + self.tab_h + 2 * self.gui.scale, w1, 2 * self.gui.scale), self.colours.queue_drag_indicator_colour)
			yy += self.tab_h
			yy += 4 * self.gui.scale

		yy += 15 * self.gui.scale
		if fq:
			self.ddt.rect((x, yy, w, 3 * self.gui.scale), sep_colour)
		yy += 11 * self.gui.scale

		# Calculate total queue duration
		duration = 0
		tracks = 0

		for item in fq:
			if item.type == QueueType.TRACK:
				duration += self.pctl.get_track(item.track_id).length
				tracks += 1
			else:
				pl = self.pctl.id_to_pl(item.playlist_id)
				if pl is not None:
					playlist = self.pctl.multi_playlist[pl].playlist_ids
					i = item.position

					album_parent_path = self.pctl.get_track(item.track_id).parent_folder_path

					playing_track = self.pctl.playing_object()

					if pl == self.pctl.active_playlist_playing \
					and item.album_stage \
					and playing_track and playing_track.parent_folder_path == album_parent_path:
						i = self.pctl.playlist_playing_position + 1

					if item.track_id not in playlist:
						continue
					if i > len(playlist) - 1:
						continue
					if playlist[i] != item.track_id:
						i = playlist.index(item.track_id)

					while i < len(playlist):
						if self.pctl.get_track(playlist[i]).parent_folder_path != album_parent_path:
							break

						duration += self.pctl.get_track(playlist[i]).length
						tracks += 1
						i += 1

		# Show total duration text "n Tracks [0:00:00]"
		if tracks and fq:
			if tracks < 2:
				line = _("{N} Track").format(N=str(tracks)) + " [" + get_hms_time(duration) + "]"
				self.ddt.text((x + 12 * self.gui.scale, yy), line, text_colour, 11.5, bg=self.colours.queue_background)
			else:
				line = _("{N} Tracks").format(N=str(tracks)) + " [" + get_hms_time(duration) + "]"
				self.ddt.text((x + 12 * self.gui.scale, yy), line, text_colour, 11.5, bg=self.colours.queue_background)

		if self.dragging:
			fqo = None
			for item in fq:
				if item.uuid_int == self.dragging:
					fqo = item
					break
			else:
				self.dragging = False

			if self.dragging:
				yyy = self.drag_start_top + (self.inp.mouse_position[1] - self.drag_start_y)
				yyy = max(yyy, list_top)
				track = self.pctl.get_track(fqo.track_id)
				self.draw_card(x, y, w, h, yyy, track, fqo, draw_back=True)

		# Drag and drop tracks from main playlist into queue
		if self.inp.quick_drag and self.inp.mouse_up and self.coll(box_rect) and self.gui.shift_selection:
			self.drop_tracks_insert(len(fq))

		# Right click context menu in blank space
		if qb_right_click:
			if qb_right_click == 1:
				self.right_click_id = None
			self.queue_menu.activate(position=self.inp.mouse_position)
