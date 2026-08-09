"""Lyrics rendering, timed-lyrics editing, and LRC helpers."""

from __future__ import annotations

import copy
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Callable, Protocol

import mutagen

from tauon.t_modules.t_draw import TDraw
from tauon.t_modules.t_enums import PlayingState
from tauon.t_modules.t_extra import (
	Timer,
	alpha_blend,
	coll_point,
	rgb_add_hls,
	search_magic_beefy,
	test_lumi,
)
from tauon.t_modules.t_input import SmoothScroll
from tauon.t_modules.t_menu import Menu, MenuItem
from tauon.t_modules.t_models import ColourRGBA, TrackClass
from tauon.t_modules.t_overlays import SearchOverlay
from tauon.t_modules.t_prefs import Prefs
from tauon.t_modules.t_state import ColoursClass, GuiVar, Input, asset_loader
from tauon.t_modules.t_tagscan import Ape, Flac, Opus, lyrics_are_synced
from tauon.t_modules.t_text import MultiLineTextBox, TextBox2
from tauon.t_modules.t_visuals import draw_showcase_art_box
from tauon.t_modules.t_widgets import Drawing


class _LyricsPlayer(Protocol):
	def __getattr__(self, name: str) -> Any: ...


class _LyricsApp(Protocol):
	gui: GuiVar
	inp: Input
	ddt: TDraw
	pctl: _LyricsPlayer
	prefs: Prefs
	colours: ColoursClass
	window_size: list[int]

	def __getattr__(self, name: str) -> Any: ...
def strip_lrc_formatting(lyrics: str) -> str:
	text = ""
	for line in lyrics.split("\n"):
		if len(line) < 10 or (line[0] != "[" or (line[9] != "]" and ":" not in line)) or "." not in line:
			text += line + "\n"
		else:
			text += line.split("]")[-1] + "\n"
	return text
class LyricsRenMini:

	def __init__(self, tauon: _LyricsApp) -> None:
		self.pctl  = tauon.pctl
		self.ddt   = tauon.ddt
		self.colours = tauon.colours
		self.prefs = tauon.prefs
		self.index: int = -1
		self.text: str  = ""
		self.to_reload: bool = False

		self.lyrics_position = 0

	def generate(self, index: int, w: float) -> None:
		self.text = strip_lrc_formatting(self.pctl.master_library[index].lyrics)
		self.lyrics_position = 0

	def render(self, index: int, x: float, y: float, w: float, h: None, p: int) -> None:
		if index != self.index or self.to_reload: # or self.text != self.pctl.master_library[index].lyrics:
			self.index = index
			self.generate(index, w)
			self.to_reload = False

		colour = self.colours.lyrics
		bg = self.colours.lyrics_panel_background

		# if inp.key_ctrl_down:
		#	 if inp.mouse_wheel < 0:
		#		 prefs.lyrics_font_size += 1
		#	 if inp.mouse_wheel > 0:
		#		 prefs.lyrics_font_size -= 1

		self.ddt.text((x, y, 4, w), self.text, colour, self.prefs.lyrics_font_size, w - (w % 2), bg)
class LyricsRen:

	def __init__(self, tauon: _LyricsApp) -> None:
		self.ddt     = tauon.ddt
		self.colours = tauon.colours
		self.index = -1
		self.text = ""
		self.lrm     = tauon.lyrics_ren_mini

		self.lyrics_position = 0

	def test_update(self, track_object: TrackClass) -> None:
		if track_object.index != self.index or self.lrm.to_reload: # or self.text != track_object.lyrics:
			self.index = track_object.index
			self.text = strip_lrc_formatting(track_object.lyrics)
			self.lyrics_position = 0
			self.lrm.to_reload = False

	def render(self, x: int, y: int, w: int, h: int, p: int) -> None:
		colour = self.colours.lyrics
		bg = self.colours.lyrics_panel_background

		#colour = self.colours.grey(40)
		# if test_lumi(self.colours.lyrics_panel_background) < 0.5:
		#	colour = self.colours.grey(40)
		# TODO (Flynn): this used to check the gallery background & i don't even know why it did that much
		self.ddt.text((x, y, 4, w), self.text, colour, 17, w, bg)
class TimedLyricsToStatic:

	def __init__(self) -> None:
		self.cache_key = None
		self.cache_lyrics = ""

	def get(self, track: TrackClass) -> str:
		if track.is_network:
			return ""
		if track == self.cache_key:
			return self.cache_lyrics
		data = track.lyrics.splitlines() if track.lyrics else find_synced_lyric_data(track)

		if data is None:
			self.cache_lyrics = ""
			self.cache_key = track
			return ""
		text = ""

		for line in data:
			if line and line[0] != "[" and ":" not in line:
				text += line + "\n"
				continue

			if len(line) < 10:
				continue

			text += line.split("]")[-1].rstrip("\n") + "\n"

		self.cache_lyrics = text
		self.cache_key = track
		return text
class TimedLyricsRen:

	def __init__(self, tauon: _LyricsApp) -> None:
		self.tauon         = tauon
		self.ddt           = tauon.ddt
		self.gui           = tauon.gui
		self.inp           = tauon.inp
		self.coll          = tauon.coll
		self.pctl          = tauon.pctl
		self.prefs         = tauon.prefs
		self.colours       = tauon.colours
		self.top_panel     = tauon.top_panel
		self.window_size   = tauon.window_size
		self.showcase_menu = tauon.showcase_menu
		self.smooth_scroll = tauon.smooth_scroll
		self.lrm           = tauon.lyrics_ren_mini
		self.index         = -1

		self.scanned = {}
		self.ready = False
		self.data = []
		self.line_heights: list[int] = []

		self.scroll_position: int = 0

		self.recenter_timeout = Timer()
		self.temp_line: int = -1
		self.teleport_line: int | None = None
		self.temp_scale: float = self.gui.scale
		self.temp_w: int = -1
		self.temp_side_panel: bool = False

	def generate(self, track: TrackClass) -> bool | None:
		if self.index == track.index and not self.lrm.to_reload:
			return self.ready

		self.ready = False
		self.index = track.index
		self.scroll_position = 0
		self.data.clear()
		self.temp_scale = self.gui.scale

		data = find_synced_lyric_data(track)
		if data is None:
			return None

		for line in data:
			if len(line) < 10:
				continue

			if line[0] != "[" or "]" not in line or ":" not in line or "." not in line:
				continue

			try:
				text = line.split("]")[-1].rstrip("\n")
				t = line

				while t[0] == "[" and (t[9] == "]" or t[10] == "]") and ":" in t and "." in t:
					a = t.lstrip("[")
					t = t.split("]")[1] + "]"

					a = a.split("]")[0]
					mm, b = a.split(":")
					ss, ms = b.split(".")

					s = int(mm) * 60 + int(ss)
					if len(ms) == 2:
						s += int(ms) / 100
					elif len(ms) == 3:
						s += int(ms) / 1000

					self.data.append((s, text))

					if len(t) < 10:
						break
			except Exception:
				logging.exception("Failed generating timed lyrics")
				continue

		self.data = sorted(self.data, key=lambda x: x[0])
		if not self.data:
			return None
		self.line_heights = []
		self.recenter_timeout.set()
		self.temp_line = -1

		self.ready = True
		return True

	def render(self, index: int, x: int, y: int, side_panel: bool = False, w: int = 0, h: int = 0) -> bool | None:
		if index != self.index or self.lrm.to_reload:
			self.ready = False
			self.generate(self.pctl.master_library[index])
			self.lrm.to_reload = False
		line_positions: list[tuple[list[int], list[float | str], int]] = []
		# saves collider positions alongside their respective lines

		if self.inp.right_click and x and y and self.coll((x, y, w, h)):
			self.showcase_menu.activate(self.pctl.master_library[index])

		if not self.ready:
			return False

		line_active = -1
		last = -1

		highlight = True

		if side_panel:
			scroll_to = round(-h/3)
			bg = self.colours.lyrics_panel_background
			font_size = 15
			spacing = round(6 * self.gui.scale)
			self.ddt.rect((self.gui.rsp_x, y, self.gui.rspw, h), bg)
			y += 25 * self.gui.scale
			y_center = y + (h/2) - (spacing)
			allowed_width = round(w - 20 * self.gui.scale)
		else:
			scroll_to = 0
			bg = self.colours.lyrics_panel_background
			font_size = 20
			spacing = round(10 * self.gui.scale)
			y_center = self.window_size[1]/2
			allowed_width = round(w - 20 * self.gui.scale) - 108

		# reset scroll position after 5 seconds
		if self.recenter_timeout.get() > 5 and self.pctl.playing_state == PlayingState.PLAYING:
			self.scroll_position = scroll_to


		if self.teleport_line:
			line_active = self.teleport_line
			self.teleport_line = None
		else:
			# determine active lyric
			test_time = self.tauon.get_real_time()
			if self.pctl.track_queue[self.pctl.queue_step] == index:
				for i, line in enumerate(self.data):
					if line[0] <= test_time:
						last = i

					if line[0] > test_time:
						self.pctl.wake_past_time = line[0]
						line_active = last
						break
				else:
					line_active = len(self.data) - 1

		# record line heights so we can perfectly center the active lyric
		if not self.line_heights or self.temp_scale != self.gui.scale or self.temp_w != w or self.temp_side_panel != side_panel:
			self.scroll_position = scroll_to
			self.line_heights = []
			for i, line in enumerate(self.data):
				drop_w, line_h = self.ddt.get_text_wh(line[1], font_size, allowed_width, True)
				self.line_heights.append( line_h + spacing )
			self.temp_scale = self.gui.scale
			self.temp_w = w
			self.temp_side_panel = side_panel

		# don't autoscroll if the new active line is not visible
		if ( self.scroll_position > h/2 or self.scroll_position < -h/2 ) and self.temp_line != line_active:
			self.scroll_position -= ( self.temp_line - line_active ) * self.line_heights[line_active]
			self.temp_line = line_active


		scroll = self.scroll_position
		self.scroll_position -= self.smooth_scroll.get_scroll("timed lyrics",(x,y,w,h),30*self.gui.scale)
		if self.scroll_position != scroll:
			self.recenter_timeout.set()


		self.scroll_position = round(self.scroll_position)

		if side_panel:
			top_position =     sum( self.line_heights[ :max(0,line_active) ]) - h/2
			bottom_position = -sum( self.line_heights[ max(0,line_active): ]) + h/2 - self.gui.panelBY
		else:
			top_position =     sum( self.line_heights[ :max(0,line_active) ]) - self.window_size[1]/2 + y/2
			bottom_position = -sum( self.line_heights[ max(0,line_active): ]) + self.window_size[1]/2 - self.gui.panelBY

		if self.scroll_position < bottom_position:
			self.scroll_position = int(bottom_position)
		if self.scroll_position > top_position:
			self.scroll_position = int(top_position)


		center = y_center + self.scroll_position
		# scroll position refers to y offset (in pixels) from the active lyric

		for i, line in enumerate(self.data):
			# determine y val
			possible_y = center - \
				sum( self.line_heights[i: max(0,line_active) ] ) + \
				sum( self.line_heights[ max(line_active,0) :i] )

			if possible_y > 0 and possible_y < self.window_size[1]:
				colour = self.colours.lyrics

				#colour = self.colours.grey(70)
				#if test_lumi(self.colours.gallery_background) < 0.5:
				#	colour = self.colours.grey(40)

				if i == line_active and highlight:
					colour = self.colours.active_lyric

				location = [ round(x), round(possible_y), 4, allowed_width - 12 ]
				# see t_draw.py -> __draw_text_cairo -> line that says #Hack
				text = line[1]
				if text.rstrip() == "":
					text = "♪♪♪"
				line_h = self.ddt.text(location, text, colour, font_size, allowed_width, bg)

				collider = [ round(x), round(possible_y - spacing/2), allowed_width, self.line_heights[i] ]
				association = collider, line, i
				line_positions.append( association )


		# click a lyric to seek to it
		if self.inp.mouse_click \
			and self.gui.panelY < self.inp.mouse_position[1] < self.window_size[1] - self.gui.panelBY \
			and (not h or y-25*self.gui.scale < self.inp.mouse_position[1] < y+h-25*self.gui.scale):
			for rendered_line in line_positions:
				if self.coll(rendered_line[0]):
					self.pctl.seek_time(rendered_line[1][0] + self.prefs.sync_lyrics_time_offset/1000)
					self.scroll_position = scroll_to
					self.teleport_line = rendered_line[2]
					self.temp_line = rendered_line[2]
					break

		return None
class TimedLyricsEdit:

	def __init__(self, tauon: _LyricsApp) -> None:
		self.tauon: _LyricsApp             = tauon
		self.inp: Input               = tauon.inp
		self.gui: GuiVar              = tauon.gui
		self.ddt: TDraw               = tauon.ddt
		self.coll                     = tauon.coll
		self.draw: Drawing            = tauon.draw
		self.pctl: _LyricsPlayer          = tauon.pctl
		self.prefs: Prefs             = tauon.prefs
		self.colours: ColoursClass    = tauon.colours
		self.renderer                 = tauon.renderer
		self.overlay: SearchOverlay   = tauon.search_over
		self.window_size: list[int]   = tauon.window_size
		self.scroll: SmoothScroll     = tauon.smooth_scroll

		# main boys big kahunas
		self.struct_track:                          int = -1 # what track are we on
		self.structure: list[ tuple[ str, float, str] ] = [] # backbone of synced editing system
		                                                     # each line contains a timestamp as a string, that timestamp's actual time, and the line itself
		self.line_edit_box:                    TextBox2 = TextBox2(tauon=tauon) # there are no multi line text boxes so we have to reuse the same one for every single line
		self.unsynced_text_box:        MultiLineTextBox = MultiLineTextBox(tauon=tauon)
		self.x_posns:                         list[int] = [] # to display text editing buttons in the right places
		self.line_active:                           int = 0  # which lyric is currently playing
		self.view_is_synced:                       bool = True # which view do we display
		self.text:                                  str = "" # unsynced lyrics after lrc stuff is filtered out

		# icons
		self.synced_img   = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "synced.png", True)
		self.unsynced_img = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "unsynced.png", True)

		# these ones are only stored from one frame to the next
		self.pausing:                   bool = False # prevents typing a space in text box when pausing
		self.cursor:              int | None = None  # tracks text box cursor position across frames
		self.edit_point: tuple[int,int]|None = None  # so user no longer has to hover over the text box forever
		self.text_leftovers:      str | None = None  # text typed while editing line was offscreen
		self.big_paste:                 bool = False # do special things the frame after receiving a multi-line paste
		self.continuous:                bool = True  # track change behavior should only happen if the editor wasn't closed when the track changed
		self.queue_next_frame:          bool = False # update gui when things happen
		self.temp_line:                  int = -1    # special scroll thingy when the line advances while it's offscreen
		self.temp_w:                     int = 0     # these two are used to recalculate self.x_posns when the user...
		self.temp_scale:               float = self.gui.scale # ...resizes or rescales the window
		self.editing_line:               int = -1    # clear selection when line changes
		self.track_time_left:            int = -1    # we'll try to filter out manual track skips so we don't unexpectedly save
		self.repeat_mode:         list[bool] = []    # save the global repeat mode yada yada track end behavior
		self.rescroll:                  bool = False # scroll to the active line when you time it
		self.recalculate_colors() # can't think of a better place for this

		# scrolling
		self.scroll_position: int = 0 # measured in pixels - greater means scrolled further down - 0 means centered on active line
		self.lyrics_position: int = 0 # same thing but for the static view
		self.allow_scroll:   bool = True # cancels auto scroll correction when adding & removing lines. probably doesn't actually do anything
		self.font:            int = 20
		self.big_font:        int = 228
		self.line_height:     int = round(self.ddt.get_text_w("?", self.font, True))
		self.yy:              int = self.line_height + round(10 * self.gui.scale) #line height plus spacing

		# timers
		self.recenter_timeout: Timer = Timer() # when playing, snap back to current line after 5 seconds no scrolling
		self.autosave_timer:   Timer = Timer() # create autosave a couple seconds after most recent edit
		self.autosaved:         bool = True    # then don't do it again until next edit
		self.text_timer:       Timer = Timer() # should display lyrics search indicator

		# nudge timestamp
		self.check_timer:   Timer = Timer() # preview timing after half a second
		self.check_line:      int = -1
		self.check:   bool | None = None    # True if previewing now, False if waiting to preview, None if disengaged
		self.alt_timer:     Timer = Timer()
		self.alted:          bool = False

		# lrclib upload
		self.upload_synced:                                      bool = True
		self.upload_static:                                      bool = False
		self.potential_uploads: dict[ int, dict[ str, str | float ] ] = {}
		self.box_open:                                           bool = False
		self.shake_frames:                                        int = 0 # less intrusive than a whole error box
		self.clicks:                                              int = 0 # but if they click a bunch anyway then we should show an error box.

		# menus
		self.menu:          Menu = Menu(tauon, 135)
		self.unsynced_menu: Menu = Menu(tauon, 135)
		self.reload_menu()
		self.unsynced_menu.add(MenuItem(_("Exit Lyrics Editor"), self.exit_lyrics_editor, pass_ref=False))
		self.unsynced_menu.add(MenuItem(_("Search for Lyrics"), self.tauon.get_lyric_wiki, pass_ref=True))
		self.unsynced_menu.add(MenuItem(_("Copy From Synced"), self.copy_from_synced, pass_ref=False))
		self.unsynced_menu.add(MenuItem(_("Upload To LRCLIB"), self.upload_both_to_lrclib, pass_ref=False))
		self.show_save_dialog: bool = False
		self.will_overwrite: bool = False
		self.file_has_synced_already: bool|None = None
		self.placeholder: str = _("You don't yet have any static lyrics for this song. To start, you can either replace this text immediately, or you can right-click and select \"copy from synced\" if you already have synced lyrics.\n\nThe right-click menu will also let you search and download lyrics from your selected lyrics sources, if you think they may be available online.")


	# FUNCTIONS FROM THE RIGHT CLICK MENU

	def reload_menu(self) -> None:
		"""Recreates the context menu to properly display checkmarks"""
		self.menu.subs = []
		self.menu.sub_number = 0
		self.menu.items = []

		self.menu.add(MenuItem(_("Exit Lyrics Editor"), self.exit_lyrics_editor, pass_ref=False))
		self.menu.add(MenuItem(_("Search for Lyrics"), self.tauon.get_lyric_wiki, pass_ref=True))
		self.menu.add(MenuItem(_("Copy From Unsynced"), self.copy_from_unsynced, pass_ref=False))
		self.menu.add(MenuItem(_("Clear All Section Markers"), self.clear_section_markers, pass_ref=False))
		self.menu.add(MenuItem(_("Clear All Timestamps"), self.clear_all_timestamps, pass_ref=False))
		self.menu.add(MenuItem(_("Clear All Lyrics"), self.clear_lyrics, pass_ref=False))
		self.menu.add(MenuItem(_("Upload To LRCLIB"), self.upload_both_to_lrclib, pass_ref=False))

		self.menu.add_sub(_("Backups..."), 165)
		self.menu.add_to_sub(0, MenuItem(_("Load Current Backup"), self.autoload, pass_ref=False))
		self.menu.add_to_sub(0, MenuItem(_("Visit Current Backup"), self.visit_backup, pass_ref=False))
		self.menu.add_to_sub(0, MenuItem(_("Delete All Backups"), self.delete_autosaves, pass_ref=False))

		self.menu.add_sub(_("When track ends..."), 165)

		def end_mode_check(mode: str) -> Callable[[], bool]:
			return lambda: self.prefs.synced_lyrics_editor_track_end_mode == mode

		self.menu.add_to_sub(1, MenuItem(_("Repeat track"), self.end_set_repeat,
			check_test=end_mode_check("repeat")))
		self.menu.add_to_sub(1, MenuItem(_("Stop immediately"), self.end_set_stop,
			check_test=end_mode_check("stop")))
		self.menu.add_to_sub(1, MenuItem(_("Backup and continue"), self.end_set_autosave,
			check_test=end_mode_check("autosave")))
		self.menu.add_to_sub(1, MenuItem(_("Fully save and continue"), self.end_set_full_save,
			check_test=end_mode_check("full save")))

		self.menu.add(MenuItem(_("Save synced to .lrc"), self.toggle_lrc, pass_ref=False,
			check_test=lambda: self.prefs.save_synced_to_lrc))

	def end_set_repeat(self) -> None:
		self.prefs.synced_lyrics_editor_track_end_mode = "repeat"
		self.reload_menu()

	def end_set_stop(self) -> None:
		self.prefs.synced_lyrics_editor_track_end_mode = "stop"
		self.reload_menu()

	def end_set_autosave(self) -> None:
		self.prefs.synced_lyrics_editor_track_end_mode = "autosave"
		self.reload_menu()

	def end_set_full_save(self) -> None:
		self.prefs.synced_lyrics_editor_track_end_mode = "full save"
		self.reload_menu()

	def exit_lyrics_editor(self) -> None:
		self.autosave()
		self.gui.timed_lyrics_edit_view = False

	def delete_autosaves(self) -> None:
		count = 0
		target = self.tauon.config_directory / "lyrics-editor"
		if not target.is_dir():
			return
		for child in target.iterdir():
			if child.is_file():
				count += 1
				child.unlink()
		try:
			target.rmdir()
		except OSError:
			logging.error( _("You put a folder in the lyrics-editor directory. Don't do that.") )
		logging.info(f"Deleted {count} autosave files.")

	def clear_all_timestamps(self) -> None:
		for i, line in enumerate(self.structure):
			if line[0] != "tag":
				self.structure[i] = "??:??.??", -1.0, line[2]
		self.autosave_timer.set()
		self.autosaved = False

	def clear_lyrics(self) -> None:
		self.structure = [ ("??:??.??", -1.0, "") ]

	def clear_section_markers(self) -> None:
		deletes = []
		for i, line in enumerate(self.structure):
			if line[0] == "tag":
				continue
			if line[2].startswith("[") and line[2].endswith("]"):
				deletes.append(i)
		deletes.reverse()
		for i in deletes:
			del self.structure[i]

	def copy_from_unsynced(self) -> None:
		track = self.pctl.master_library[self.struct_track]
		self.structurize_current(track, True)

	def copy_from_synced(self) -> None:
		self.text = ""
		for line in self.structure:
			self.text += line[2] + "\n"
		self.text = self.text.strip()
		self.unsynced_text_box.text = self.text
		self.unsynced_text_box.text_height = 0

	def upload_both_to_lrclib(self) -> None:
		track = self.pctl.master_library[self.struct_track]
		synced_text = self.save(fetch_text=True)
		p = {
			"trackName": track.title,
			"artistName": track.artist,
			"albumName": track.album,
			"duration": track.length,
			"plainLyrics": self.text,
			"syncedLyrics": synced_text
		}
		self.potential_uploads[self.struct_track] = p

	def toggle_lrc(self) -> None:
		self.prefs.save_synced_to_lrc = not self.prefs.save_synced_to_lrc
		if not self.prefs.save_synced_to_lrc and self.prefs.allow_overwrite_synced_with_static:
			self.tauon.show_message(
				_("Be careful!"),
				_("A file's metadata can only store ONE type of lyrics data, synced or static, at a time."),
				_("Saving one type will now OVERWRITE the other in the files. (Tauon itself doesn't care.)"),
				mode="warning"
			)
		self.reload_menu()



	def button(
			self, text: str, x_pos: int, y_pos: int, font: int,
			bg: ColourRGBA | None = None, active_bg: ColourRGBA | None = None,
			txt: ColourRGBA | None = None, active_txt: ColourRGBA | None = None,
			tooltip: str = "", off: bool = False, return_rect: bool = False, big: bool = False) -> tuple[ bool | None, tuple[int, int, int, int] | None ]:
		"""Button centered around text display. off will disable the button if the condition is true,
		return_rect will return the rect as a second parameter. returns True for click, False for right click,
		None for nothing
		"""
		if bg is None:
			bg = self.colours.box_button_background
		if active_bg is None:
			active_bg = self.colours.box_button_background_highlight
		if txt is None:
			txt = self.colours.box_button_text
		if active_txt is None:
			active_txt = self.colours.box_button_text_highlight

		if off:
			bg = copy.deepcopy(bg)
			bg.a = round(bg.a * 0.5)
			txt = copy.deepcopy(txt)
			txt.a = round(txt.a * 0.5)
		inner_border = 7*self.gui.scale
		width = self.ddt.get_text_w(text, font)
		height = self.ddt.get_text_w("?", font, True) /2
		if big:
			rect = (x_pos - inner_border, y_pos - 2.5*inner_border, width + 2*inner_border, height + 2*inner_border)
		else:
			rect = (x_pos - inner_border, y_pos - inner_border, width + 2*inner_border, height + 2*inner_border)
		self.tauon.fields.add(rect)
		t_rect = (x_pos, y_pos)
		if self.coll(rect) and not off:
			self.ddt.bordered_rect( rect, active_bg, self.colours.box_text_border, round(1*self.gui.scale))
			self.ddt.text( t_rect, text, active_txt, font, bg=active_bg)
			if self.inp.mouse_click:
				if return_rect:
					return True, rect
				return True, None
			if self.inp.right_click:
				self.inp.right_click = False
				if return_rect:
					return False, rect
				return False, None
		else:
			self.ddt.bordered_rect( rect, bg, self.colours.box_text_border, round(1*self.gui.scale))
			self.ddt.text( t_rect, text, txt, font, bg=bg)

		if tooltip and self.coll(rect):
			self.tauon.tool_tip.test(x_pos + 15 * self.gui.scale, y_pos - 28 * self.gui.scale, tooltip)
		if return_rect:
			return None, rect
		return None, None

	def get_time_from_stamp(self, t: str) -> float:
		a = t.lstrip("[")
		t = t.split("]")[1] + "]"

		a = a.split("]")[0]
		mm, b = a.split(":")
		ss, ms = b.split(".")

		s = int(mm) * 60 + int(ss)
		if len(ms) == 2:
			s += int(ms) / 100
		elif len(ms) == 3:
			s += int(ms) / 1000
		return s

	def get_stamp_from_time(self, t: float) -> str:
		if t<0:
			return "??:??.??"
		ms = round( 100 * t ) % 100
		t = t//1
		ss = round(t%60)
		mm = round(t//60)
		return f"{format(mm,'02d')}:{format(ss,'02d')}.{format(ms,'02d')}"

	def structurize_current(self, track: TrackClass, from_unsynced: bool = False) -> None:
		"""reload synced data from saved track"""
		LRC_tags = "[ti:", "[ar:", "[al:", "[au:", "[lr:", "[length:", "[by:", "[offset:", "[re:", "[tool:", "[ve:", "[#:"
		self.structure = []
		self.struct_track = track.index

		if from_unsynced:
			lyrics = self.text
		elif track.synced:
			lyrics = find_synced_lyric_data(track)
		elif track.lyrics:
			lyrics = track.lyrics.splitlines()
		else:
			self.structure = [("??:??.??", -1.0, "")]
			self.scroll_position = 0
			lyrics=""

		for i, line in enumerate(lyrics):
			if any(tag in line for tag in LRC_tags):
				self.structure.append( ("tag", -1.0, line) )
				continue

			if len(line) >= 10 and line[0] == "[" and ":" in line[:10] \
			and "." in line[:10] and "]" in line:
				try:
					int( line[1] )
				except ValueError:
					pass
				else: # if current line is LRC-formatted
					stamp = line.split("]")[0].lstrip("[")
					time = self.get_time_from_stamp( line )
					line = line.split("]",1)[1]
					# LRCLIB returns lines with spaces at the start of them
					# it's not important when displaying but it kind of is in editing
					line = line.removeprefix(" ")
					self.structure.append( (stamp,time,line) )
					continue

			# if current line is NOT LRC-formatted
			self.structure.append( ("??:??.??", -1.0, line) )
		if self.structure == []:
			self.structure = [ ("??:??.??", -1.0, "") ]
		self.autosaved = True
		self.queue_next_frame = True

	def save(
		self,
		synced: bool = True,
		fetch_text: bool = False,
		save_to_lrc: bool | None = None,
		save_to_tags: bool | None = None,
	) -> None | str:
		lyrics: str = ""
		warning: list[bool] = [False, False, False]
		timed: int = 0
		max_stamp: float = 0.0

		track = self.pctl.master_library[self.struct_track]
		over = self.will_overwrite_lyrics(track)
		will_ovw_synced = self.will_overwrite_synced()
		save_tags = self.can_write_at_all() and \
			(self.prefs.save_lyrics_changes_to_files if save_to_tags is None else save_to_tags) and \
			(synced or (not will_ovw_synced or (will_ovw_synced and self.prefs.allow_overwrite_synced_with_static)))
		save_lrc = self.prefs.save_synced_to_lrc if save_to_lrc is None else save_to_lrc

		if synced:
			for line in self.structure:
				if line[1] < 0:
					lyrics += line[2].rstrip()
					if line[0] != "tag":
						warning[0] = True
					else:
						timed += 1
				else:
					if line[1] < max_stamp:
						warning[2] = True
					stamp = self.get_stamp_from_time( line[1] )
					lyrics += "[" + stamp + "]" + line[2]
					warning[1] = True
					timed += 1
					max_stamp = max(max_stamp, line[1])
				lyrics += "\n"
			lyrics = lyrics.strip()
		else:
			lyrics = self.text.strip()

		if warning[0] and warning[1] and not ( self.inp.key_lalt or self.inp.key_ralt ):
			if fetch_text:
					return "failed"
			self.tauon.show_message(
				_("Lyrics will misbehave if only some of them are timed."),
				_("You can time all of them or none of them, either will work."),
				_("Alternatively, save again while holding Alt to override."),
				mode="warning"
			)
			self.autosave()
		elif warning[2] and not ( self.inp.key_lalt or self.inp.key_ralt ):
			if fetch_text:
					return "failed"
			self.tauon.show_message(
				_("Lyrics might misbehave if their timestamps are out of order."),
				_("Please make sure all timestamps are ordered correctly."),
				_("Alternatively, save again while holding Alt to override."),
				mode="warning"
			)
			self.autosave()
		else:
			if ( self.inp.key_lalt or self.inp.key_ralt ):
				self.alted = True
			if timed > 0:
				if fetch_text:
					return lyrics
				track.synced = lyrics
				saved_lrc = False
				saved_tags = False
				if save_lrc:
					saved_lrc = self.tauon.write_lyrics(track, True, True, synced_target="lrc")
				if save_tags:
					saved_tags = self.tauon.write_lyrics(track, True, True, synced_target="tags")

				if saved_lrc and saved_tags:
					self.tauon.show_message(
						_("Synced lyrics saved successfully"),
						_("Saved to .lrc and tags"),
						mode="done"
					)
				elif saved_lrc:
					self.tauon.show_message(
						_("Synced lyrics saved successfully"),
						_("Saved to .lrc"),
						mode="done"
					)
				elif saved_tags:
					if over:
						self.tauon.show_message(
							_("Synced lyrics saved to tags"),
							_("Destroyed previously existing lyrics in file"),
							mode="done"
						)
					else:
						self.tauon.show_message(
							_("Synced lyrics saved to tags"),
							mode="done"
						)
				else:
					self.tauon.show_message(
						_("Synced lyrics saved in Tauon only"),
						mode="done"
					)
			else:
				if fetch_text:
					return "failed"
					# we don't want to upload any synced lyrics to LRCLIB
					# that are not actually synced properly
				if search_magic_beefy(lyrics, self.placeholder) > 90:
					return "failed"
				track.lyrics = lyrics
				saved = False
				if save_tags:
					saved = self.tauon.write_lyrics(track, False, True)
				if save_tags and saved:
					if over:
						self.tauon.show_message(
							_("Unsynced lyrics saved successfully"),
							_("Destroyed previously existing lyrics in file"),
							mode="done"
						)
					else:
						self.tauon.show_message(
							_("Unsynced lyrics saved successfully"),
							mode="done"
						)
				elif not save_tags:
					self.tauon.show_message(
						_("Unsynced lyrics saved in Tauon only"),
						mode="done"
					)
			self.test_update()
		self.queue_next_frame = True

		# clear cached search data (user can search by lyrics immediately)
		self.tauon.search_string_cache.pop(self.struct_track, None)
		self.tauon.search_dia_string_cache.pop(self.struct_track, None)
		self.tauon.search_field_cache.pop(self.struct_track, None)
		self.tauon.search_dia_field_cache.pop(self.struct_track, None)

		self.file_has_synced_already = None

		return None

	def will_overwrite_lyrics(self, track: TrackClass) -> bool:
		file = Path(track.fullpath)
		if not self.can_write_at_all():
			return False
		if track.file_ext == "MP3":
			try:
				audio = mutagen.id3.ID3(track.fullpath)
				if audio.getall("USLT"):
					return True
			except mutagen.id3._util.ID3NoHeaderError:
				logging.info("no header")
				return False
		elif track.file_ext == "FLAC":
			audio = mutagen.flac.FLAC(track.fullpath)
			if any(key in audio for key in ("LYRICS", "SYNCEDLYRICS", "UNSYNCEDLYRICS")):
				return True
		elif track.file_ext == "OPUS":
			audio = mutagen.oggopus.OggOpus(track.fullpath)
			if any(key in audio for key in ("LYRICS", "SYNCEDLYRICS", "UNSYNCEDLYRICS")):
				return True
		elif track.file_ext == "OGG":
			audio = mutagen.oggvorbis.OggVorbis(track.fullpath)
			if any(key in audio for key in ("LYRICS", "SYNCEDLYRICS", "UNSYNCEDLYRICS")):
				return True
		elif track.file_ext in ("APE","WV","TTA"):
			audio = mutagen.apev2.APEv2(track.fullpath)
			if "Lyrics" in audio:
				return True
		elif track.file_ext in ("MP4","M4A","M4B","M4P"):
			audio = mutagen.mp4.MP4(track.fullpath)
			if "\xa9lyr" in audio:
				return True
		return False


	def will_overwrite_synced(self) -> bool:
		if self.file_has_synced_already is not None:
			return self.file_has_synced_already
		track = self.pctl.master_library[self.struct_track]
		lyr = ''
		if not track.fullpath:
			return False
		file = Path(track.fullpath)
		try:
			if track.file_ext == "MP3":
				try:
					audio = mutagen.id3.ID3(track.fullpath)
					lyr = audio.getall("USLT")[0].text
				except IndexError:
					return False
				except mutagen.id3._util.ID3NoHeaderError:
					return False
			elif track.file_ext == "FLAC":
				with Flac(track.fullpath) as audio:
					audio.read()
					lyr = ''.join(audio.lyrics)
			elif track.file_ext in ("OPUS", "OGG", "OGA"):
				with Opus(track.fullpath) as audio:
					audio.read()
					lyr = ''.join(audio.lyrics)
			elif track.file_ext in ("WV", "TTA", "APE"):
				with Ape(track.fullpath) as audio:
					audio.read()
					lyr = ''.join(audio.lyrics)
			else:
				try:
					audio = mutagen.File(track.fullpath)
				except Exception as e:
					logging.error(e)
				if type(audio.tags) is mutagen.mp4.MP4Tags:
					if "\xa9lyr" in audio.tags:
						lyr = audio.tags["\xa9lyr"][0]
		except AttributeError:
			return False
		if lyr:
			return lyrics_are_synced(lyr)
		return False


	def can_write_at_all(self) -> bool:
		return self.pctl.master_library[self.struct_track].file_ext in \
			("MP3", "FLAC", "OPUS", "OGG", "OGA", "WV", "APE", "TTA", "M4A", "MP4", "M4B","M4P")


	# SAVE DIALOG

	def lrc_sidecar_off(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return not self.prefs.save_synced_to_lrc
		self.prefs.save_synced_to_lrc = False
		if self.prefs.allow_overwrite_synced_with_static:
			self.tauon.show_message(
				_("Be careful!"),
				_("A file's metadata can only store ONE type of lyrics data, synced or static, at a time."),
				_("Saving one type will now OVERWRITE the other in the files. (Tauon itself doesn't care.)"),
				mode="warning"
			)
		self.reload_menu()
		return None

	def lrc_sidecar_on(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.save_synced_to_lrc
		self.prefs.save_synced_to_lrc = True
		self.reload_menu()
		return None

	def save_dialog(self) -> None:
		gui = self.gui
		ddt = self.ddt
		colours = self.colours
		st = self.tauon.pref_box
		chooser_bar = self.tauon.pref_box.settings_segmented_bar

		w = 500 * gui.scale
		if self.view_is_synced:
			h = 200 * gui.scale
		else:
			h = 180 * gui.scale
		x = int(self.window_size[0] / 2) - int(w / 2)
		y = int(self.window_size[1] / 2) - int(h / 2)

		ddt.rect_a((x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale), self.colours.box_border)
		ddt.rect_a((x, y), (w, h), colours.box_background)
		ddt.text_background_colour = colours.box_background

		if self.inp.key_esc_press or ((self.inp.mouse_click or gui.level_2_click or self.inp.right_click or self.inp.level_2_right_click) and not self.coll(
				(x, y, w, h)) and not gui.message_box):
			self.show_save_dialog = False
			gui.box_over = False

		nomb = not gui.message_box
		ovw_synced = self.will_overwrite_synced()

		if self.view_is_synced:
			# Title
			ddt.text((x + 10 * gui.scale, y + 8 * gui.scale), _("Saving Synced Lyrics"), colours.box_title_text, 213)

			# Path entry
			x += round(15 * gui.scale)
			y += round(25 * gui.scale)

			ddt.text((x,y), _("Changes always save to Tauon's database."), self.colours.box_text, 11)
			y += round(25 * gui.scale)
			row_gap = round(6 * gui.scale)
			row_h = round(42*self.gui.scale)
			self.prefs.save_lyrics_changes_to_files = st.settings_switch_row(
				(x,y,w - round(30*gui.scale),row_h),
				self.prefs.save_lyrics_changes_to_files,
				_("Also save lyrics to files on disk"),
				_("(Specifically the Lyrics metadata field)"),
				click=self.inp.mouse_click and nomb
			)
			if self.prefs.save_lyrics_changes_to_files:
				y += row_h + row_gap
				ddt.text((x,y), _("Synced lyrics will save..."), self.colours.box_text, 11)
				y += round(20*self.gui.scale)
				chooser_bar(
					(x, y),
					(
						(_("...also to file metadata"), self.lrc_sidecar_off(1), self.lrc_sidecar_off),
						(_("...to a separate .lrc file"), self.lrc_sidecar_on(1), self.lrc_sidecar_on),
					),
					width=w - round(30*gui.scale),
					click=self.inp.mouse_click and nomb,
				)
			else:
				y += row_h + row_gap
				y += round(20*self.gui.scale)

			y += row_h + row_gap

			self.prefs.show_lyrics_save_menu = st.toggle_square(
				x, y, self.prefs.show_lyrics_save_menu, _("Show this every time"),
				self.inp.mouse_click and nomb)

			ww = ddt.get_text_w(_("Save lyrics"), 211)
			x = ((int(self.window_size[0] / 2) - int(w / 2)) + w) - (ww + round(40 * gui.scale))

			if self.draw.button(_("Save lyrics"), x, y - (2*gui.scale), press=self.inp.mouse_click and nomb):
				self.show_save_dialog = False
				self.save()

			if self.will_overwrite and self.prefs.save_lyrics_changes_to_files \
				and (not self.view_is_synced or not self.prefs.save_synced_to_lrc):
				ww += ddt.get_text_w(_("⚠️Overwriting"), 211) + row_gap
				x = ((int(self.window_size[0] / 2) - int(w / 2)) + w) - (ww + round(40 * gui.scale))
				ddt.text((x,y), _("⚠️Overwriting"), self.colours.box_button_text_highlight, 211)

		else: # unsynced save box
			ddt.text((x + 10 * gui.scale, y + 8 * gui.scale), _("Saving Static Lyrics"), colours.box_title_text, 213)

			# Path entry
			x += round(15 * gui.scale)
			y += round(25 * gui.scale)

			ddt.text((x,y), _("Changes always save to Tauon's database."), self.colours.box_text, 11)
			y += round(25 * gui.scale)
			row_gap = round(6 * gui.scale)
			row_h = round(42*self.gui.scale)
			self.prefs.save_lyrics_changes_to_files = st.settings_switch_row(
				(x,y,w - round(30*gui.scale),row_h),
				self.prefs.save_lyrics_changes_to_files,
				_("Also save lyrics to files on disk"),
				_("(Specifically the Lyrics metadata field)"),
				click=self.inp.mouse_click and nomb
			)
			if self.prefs.save_lyrics_changes_to_files and self.lrc_sidecar_off(1):
				y += row_h + row_gap
				self.prefs.allow_overwrite_synced_with_static = st.settings_switch_row(
					(x,y,w - round(30*gui.scale),row_h),
					self.prefs.allow_overwrite_synced_with_static,
					_("Even if it would overwrite synced lyrics"),
					click=self.inp.mouse_click and nomb
				)
			else:
				y += row_h + row_gap

			y += row_h + row_gap + round(2*gui.scale)

			self.prefs.show_lyrics_save_menu = st.toggle_square(
				x, y, self.prefs.show_lyrics_save_menu, _("Show this every time"),
				self.inp.mouse_click and nomb)

			ww = ddt.get_text_w(_("Save lyrics"), 211)
			x = ((int(self.window_size[0] / 2) - int(w / 2)) + w) - (ww + round(40 * gui.scale))

			if self.draw.button(_("Save lyrics"), x, y - (2*gui.scale), press=self.inp.mouse_click and nomb):
				self.show_save_dialog = False
				self.save(False)

			# are we even going to overwrite stuff in the files?
			if self.prefs.save_lyrics_changes_to_files and self.will_overwrite:
				# saving to the files now would mean overwriting
				if ovw_synced and self.prefs.allow_overwrite_synced_with_static:
					# we're going to overwrite synced lyrics, but that's ok
					ovw = True
				elif not ovw_synced:
					# we're going to overwrite static lyrics which is always ok
					ovw = True
				elif ovw_synced and not self.prefs.allow_overwrite_synced_with_static:
					# we would overwrite synced lyrics, but we're not allowed to
					ovw = False
			else:
				# we're not writing to disk, or not overwriting
				ovw = False

			if ovw:
				ww += ddt.get_text_w(_("⚠️Overwriting"), 211) + row_gap
				x = ((int(self.window_size[0] / 2) - int(w / 2)) + w) - (ww + round(40 * gui.scale))
				ddt.text((x,y), _("⚠️Overwriting"), self.colours.box_button_text_highlight, 211)


	def autosave(self) -> None:
		target = Path( self.tauon.config_directory / "lyrics-editor" / str( self.struct_track )).with_suffix(".csv")
		if not target.parent.is_dir():
			target.parent.mkdir()
		with open(target, "w", encoding="utf-8") as lyrics_file:
			for line in self.structure:
				stamp, time, line = line
				if stamp == "tag":
					stamp = "tag"
				lyrics_file.write( f"{stamp},{time!s},{line}\n")
		self.autosaved = True

	def autoload(self) -> None:
		target = Path( self.tauon.config_directory / "lyrics-editor" / str( self.struct_track )).with_suffix(".csv")
		if not target.is_file():
			return
		with target.open(encoding="utf-8-sig", errors="replace") as lyrics_file:
			self.structure = []
			for lyric in lyrics_file.readlines():
				stamp, time, line = lyric.strip().split(",", 2)
				if stamp == "tag":
					stamp = "tag"
				time = float(time)
				self.structure.append( (stamp,time,line) )
		self.queue_next_frame = True

	def visit_backup(self, synced: bool = True) -> None:
		suffix = ".csv" if synced else ".txt"
		target = Path( self.tauon.config_directory / "lyrics-editor" / str( self.struct_track )).with_suffix(suffix)
		if not target.parent.is_dir() and not synced:
			target.parent.mkdir()
		elif not target.is_file():
			self.tauon.show_message(
				_("Backup file does not exist")
			)
			return
		if not synced:
			with open(target, "w", encoding="utf-8") as lyrics_file:
				if self.text:
					lyrics_file.write( self.text )
				else:
					lyrics_file.write( _("Put the lyrics in this file."))

		if self.tauon.windows:
			os.startfile(target)
		elif self.tauon.macos:
			subprocess.call(["open", "-t", target])
		else:
			subprocess.call(["xdg-open", target])

	def recalculate_colors(self) -> None:
		self.normal_color = self.colours.lyrics
		self.faded_color = copy.deepcopy(self.normal_color)
		self.faded_color.a *= 0.6
		self.faded_color.a = round(self.faded_color.a)

		self.active_color = self.colours.active_lyric
		self.faded_active_color = copy.deepcopy(self.active_color)
		self.faded_active_color.a *= 0.6
		self.faded_active_color.a = round(self.faded_active_color.a)

		self.highlight = copy.deepcopy(self.active_color)
		self.highlight.a *= 0.1
		self.highlight.a = round(self.highlight.a)

	# SYNCED EDITING FUNCTIONS

	def previous(self, prev: float) -> None:
		self.pctl.seek_time(prev + self.prefs.sync_lyrics_time_offset/1000)
		if (self.inp.key_lalt or self.inp.key_ralt):
			self.alted = True
		if (len(self.structure)==self.line_active+1 or self.structure[self.line_active+1][1]<0) and self.structure[self.line_active][1]>prev \
			and not (self.inp.key_lalt or self.inp.key_ralt):
			stamp, time, line = self.structure[self.line_active]
			stamp = "??:??.??"
			time = -1.0
			full_line = ( stamp, time, line )
			self.structure[self.line_active] = full_line
			if self.line_active == len(self.structure)-1 and line == "":
				del self.structure[self.line_active]
		self.queue_next_frame = True

	def time_next_line(self, current: bool = False) -> None:
		time = self.pctl.decode_time
		if current:
			self.alted = True
		if (int(self.structure[self.line_active][1] < 0 or self.structure[self.line_active][1] > time) + int(current) == 1) and self.structure[self.line_active][0] != "tag":
			# if current line needs to be timed, time it
			full_line = ( self.get_stamp_from_time(time), time, self.structure[self.line_active][2] )
			self.structure[self.line_active] = full_line
		elif current and self.structure[self.line_active][1] < 0 or self.structure[self.line_active][1] > time:
			return # special behavior at the start of the song is confusing
		else:
			while ( self.line_active < len(self.structure)-1 and self.structure[self.line_active+1][0] == "tag"):
				self.line_active += 1 # increment until we're not going to timestanmp a tag
			if self.line_active == len(self.structure)-1 or (self.inp.key_rctrl_down or self.inp.key_ctrl_down):
				self.structure.insert( self.line_active+1, (self.get_stamp_from_time(time), time, "") )
			else:
				full_line = ( self.get_stamp_from_time(time), time, self.structure[self.line_active+1][2] ) # else time the next line
				self.structure[self.line_active+1] = full_line
		self.queue_next_frame = True
		self.rescroll = True

	def scroll_timestamp(self, current_line: int, active: bool = True) -> bool:
		stamp, time, line = self.structure[current_line]
		if time == -1.0:
			return False

		if self.inp.key_ctrl_down or self.inp.key_rctrl_down:
			adjust = 0.01
		else:
			adjust = 0.1

		old_time = time
		if self.inp.mouse_wheel:
			time -= self.inp.mouse_wheel * adjust
			if active:
				self.check = False
				self.check_line = current_line
				self.check_timer.set()
		elif self.inp.key_right_press or self.inp.key_left_press:
			time += adjust * (self.inp.key_right_press - self.inp.key_left_press)
			if active:
				self.check = False
				self.check_line = current_line
				self.check_timer.set()

		self.allow_scroll = False

		if old_time == time:
			return False

		self.alted = True
		time = round(time, 2)
		if current_line != 0 and self.structure[current_line - 1][1] != -1.0:
			time = max( time, self.structure[current_line - 1][1] )
		if current_line != len(self.structure)-1 and self.structure[current_line+1][1] != -1.0:
			time = min( time, self.structure[current_line+1][1] )
		time = max( time, 0 )
		stamp = self.get_stamp_from_time(time)
		self.structure[current_line] = (stamp,time,line)
		self.autosave_timer.set()
		self.autosaved = False
		if active:
			self.scroll_position += (current_line - self.line_active) * self.yy
			self.line_active = current_line
		self.check_if_time_is_good(current_line, active)
		self.queue_next_frame = True
		return True

	def check_if_time_is_good(self, line_number: int, active: bool) -> None:
		"""for scrolling timestamps - will play one second of audio after 0.5 seconds of waiting to make sure the timestamp is correct"""
		if self.check == False and self.structure[line_number][1] >= 0: # and self.check_timer.get > 0.5  and line_number == self.check_line
			self.recenter_timeout.set()
			if self.pctl.playing_state != PlayingState.PLAYING:
				self.pctl.stop(update_gui=False)
				self.pctl.jump_time = self.structure[line_number][1] + self.prefs.sync_lyrics_time_offset/1000
				self.pctl.play(update_gui=False)
				self.line_active = line_number
				self.check_timer.set()
				self.check = True
			else:
				self.pctl.decode_time = self.structure[line_number][1] + self.prefs.sync_lyrics_time_offset/1000
				self.pctl.new_time = self.pctl.decode_time
				self.pctl.playing_time = self.pctl.decode_time
				_seek = self.tauon.aud.seek(int((self.pctl.decode_time) * 1000), self.prefs.pa_fast_seek)
				if not active:
					self.check = None
			#self.scroll_position += (line_number - self.line_active) * self.yy
			self.allow_scroll = False
			self.queue_next_frame = True

	def accept_paste(self, current_line: int) -> None:
		LRC_tags = "[ti:", "[ar:", "[al:", "[au:", "[lr:", "[length:", "[by:", "[offset:", "[re:", "[tool:", "[ve:", "[#:"
		pasted_lines = self.line_edit_box.text.splitlines()
		temp_line = self.structure[current_line]
		overwrite: bool = (self.inp.key_lalt or self.inp.key_ralt)

		def is_int(number: str) -> bool:
			try:
				int(number)
				return True
			except ValueError:
				return False

		if not overwrite:
			out_line = ( temp_line[0], temp_line[1], pasted_lines[0] )
			self.structure[current_line] = out_line
			del pasted_lines[0]

		for i, line in enumerate(pasted_lines): # try to accept LRC-formatted paste text
			if any(tag in line for tag in LRC_tags):
					self.structure.append( ("tag", -1.0, line) )
					continue

			if len(line) >= 10 and line[0] == "[" and ":" in line[:10] \
				and "." in line[:10] and "]" in line and is_int(line[1]): # if line is LRC-formatted
				stamp = line.split("]")[0].lstrip("[")
				time = self.get_time_from_stamp( line )
				line = line.split("]",1)[1]
			else:
				stamp = "??:??.??"
				time = -1.0

			if overwrite and current_line+i <= len(self.structure)-1:
				if self.structure[current_line+i][1] != -1.0:
					time = self.structure[current_line+i][1]
					stamp = self.structure[current_line+i][0]
				self.structure[current_line+i] = (stamp,time,line)
			else:
				self.structure.insert( current_line+1+i, (stamp,time,line) )

			self.scroll_position -= self.yy
			if overwrite:
				self.big_paste = True

	def settings_for_one_line(self, line_number: int, y_pos: int) -> None:
		"""Deals with editing and manipulating synced lines while paused"""
		# x_posns contains in order: position for delete timestamp button, position for stamp teleport, position for text box, position for end of line
		if self.pausing or self.show_save_dialog:
			return

		stamp, time, line = self.structure[line_number]
		temp = self.structure[line_number]
		if self.line_active == line_number:
			text_color = self.colours.active_lyric
		else:
			text_color = self.colours.box_input_text

		# TIMESTAMP - TELEPORT, DELETE AND SCROLL EDIT
		if stamp != "??:??.??" and stamp != "tag":
			button, rect = self.button(stamp, self.x_posns[1], y_pos, self.font, tooltip=_("Teleport to timestamp"), return_rect=True, txt=text_color) # timestamp button
			if time >= 0 and button:
				self.pctl.stop()
				self.pctl.jump_time = time + self.prefs.sync_lyrics_time_offset/1000
				self.pctl.play()
				self.scroll_position += (line_number-self.line_active)*self.yy

			if self.button("x", self.x_posns[0], y_pos, self.font, active_bg=self.colours.level_red, tooltip=_("Delete timestamp"))[0]:
				stamp = "??:??.??"
				time = -1.0
				full_line = ( stamp, time, line )
				self.structure[line_number] = full_line
		else:
			self.button(stamp, self.x_posns[1], y_pos, self.font, tooltip=_("Timestamp unknown"))

		self.line_edit_box.text = line
		temp_text = self.line_edit_box.text # so we don't delete lines a frame early
		if self.big_paste:
			self.line_edit_box.text = self.line_edit_box.text[ : -self.line_edit_box.cursor_position ]
			self.big_paste = False

		if self.cursor is not None:
			self.line_edit_box.cursor_position =  len(self.line_edit_box.text) - self.cursor
			self.line_edit_box.cursor_position = max( self.line_edit_box.cursor_position, 0 )
			self.line_edit_box.selection = self.line_edit_box.cursor_position
			self.cursor = None
		self.line_edit_box.cursor_position = min( self.line_edit_box.cursor_position, len(self.line_edit_box.text) )
		self.line_edit_box.selection = min( self.line_edit_box.selection, len(self.line_edit_box.text) )
		if self.editing_line != line_number:
			self.line_edit_box.selection = self.line_edit_box.cursor_position
			self.editing_line = line_number

		if self.inp.key_lalt or self.inp.key_ralt:
			self.scroll_timestamp(line_number)
			stamp, time, line = self.structure[line_number]
			temp = self.structure[line_number]
			self.inp.key_left_press = False
			self.inp.key_right_press = False
			self.inp.mouse_wheel = 0

		height = self.ddt.get_text_w("?", self.font, True)
		x = round( (self.x_posns[3]-self.x_posns[2]) * 0.9 ) + 7*self.gui.scale

		back_cursor = self.line_edit_box.cursor_position
		front_cursor = len( self.line_edit_box.text ) - self.line_edit_box.cursor_position
		rect = (self.x_posns[2]-height/4, y_pos-height/4, x, height)
		self.ddt.bordered_rect( rect, self.colours.box_background, self.colours.box_text_border, round(1 * self.gui.scale) )
		self.line_edit_box.draw(
			self.x_posns[2], y_pos, text_color, True,
			font = self.font, width = ( x ), big=True,
			headroom=6
		)
		line = self.line_edit_box.text
		full_line = ( stamp, time, line )
		self.structure[line_number] = full_line
		position = len( self.line_edit_box.text ) - self.line_edit_box.cursor_position

		# DELETE LINE BUTTON
		x += self.x_posns[2]-height/4 + round(12*self.gui.scale)
		x = min( x, round( self.window_size[0]-self.yy - 12*self.gui.scale ) )
		if self.button("x", x, y_pos, self.font, active_bg=self.colours.level_red, tooltip=_("Delete line"))[0]:# or (self.inp.key_backspace_press and temp_text==""):
			del self.structure[line_number]
			if line_number >= self.line_active:
				if (self.inp.key_lalt or self.inp.key_ralt):
					self.scroll_position += self.yy
			elif not (self.inp.key_lalt or self.inp.key_ralt):
				self.scroll_position -= self.yy
			self.allow_scroll = False
		x += round(30*self.gui.scale)
		x = min( x, self.window_size[0]-self.line_height*0.9)

		# ADD LINE BUTTON
		if self.button("+", x, y_pos, self.font, active_bg=self.colours.level_green, tooltip=_("Add line"))[0]:
			if self.inp.key_lalt or self.inp.key_ralt: # hold alt to make a new line above
				self.structure.insert(line_number, ("??:??.??",-1.0,""))
				if line_number <= self.line_active:
					self.scroll_position += self.yy
			else:
				self.structure.insert(line_number+1, ("??:??.??",-1.0,""))
				if line_number >= self.line_active:
					self.scroll_position -= self.yy
			self.allow_scroll = False

		# advanced text editing
		if "\n" in self.line_edit_box.text: # can only happen if user pastes multi line string
			self.accept_paste(line_number)

		rect = (self.x_posns[2]-height/4, y_pos-height/4, x, self.yy)
		if coll_point(self.get_edit_point(), rect):
			position = len( self.line_edit_box.text ) - self.line_edit_box.cursor_position
			# ENTER
			if self.inp.key_return_press:
				if self.inp.key_lalt or self.inp.key_ralt:
					self.structure.insert(line_number, ("??:??.??",-1.0,""))
				else:
					line_one = self.line_edit_box.text[:position]
					line_two = self.line_edit_box.text[position:]
					self.structure[line_number] = (stamp, time, line_one)
					self.structure.insert(line_number+1, ("??:??.??",-1.0,line_two))
					if line_number >= self.line_active:
						self.scroll_position -= self.yy
					self.cursor = 0

			# BACKSPACE
			elif self.inp.key_backspace_press and position==0 and line_number >= 1 and temp_text == self.line_edit_box.text:
				p_stamp, p_time, p_line = self.structure[line_number-1]
				self.structure[line_number-1] = (p_stamp, p_time, (p_line + self.line_edit_box.text))
				del self.structure[line_number]
				if line_number > self.line_active:
					self.scroll_position += self.yy
				#self.inp.key_backspace_press = False
				self.line_edit_box.cursor_position = len(self.line_edit_box.text)
				self.line_edit_box.selection = self.line_edit_box.cursor_position
				#self.cursor = position

			# DELETE
			elif self.inp.key_del and self.line_edit_box.cursor_position==0 and line_number+1<len(self.structure) and temp_text == self.line_edit_box.text:
				p_stamp, p_time, p_line = self.structure[line_number+1]
				self.structure[line_number] = (stamp, time, (self.line_edit_box.text + p_line))
				del self.structure[line_number+1]
				self.line_edit_box.cursor_position += len(p_line)
				self.line_edit_box.selection = self.line_edit_box.cursor_position
				self.inp.key_del = False
				self.cursor = position
				if line_number < self.line_active:
					self.scroll_position -= self.yy

			# ARROW KEYS
			elif self.inp.key_up_press and line_number > 0:
				self.scroll_position += self.yy
				self.cursor = position
			elif self.inp.key_down_press and line_number+1 < len(self.structure):
				self.scroll_position -= self.yy
				self.cursor = position
			elif self.inp.key_left_press and line_number > 0 and front_cursor == 0:
				self.scroll_position += self.yy
				self.line_edit_box.cursor_position = 0
				self.line_edit_box.selection = self.line_edit_box.cursor_position
			elif self.inp.key_right_press and line_number+1 < len(self.structure) and back_cursor == 0:
				self.scroll_position -= self.yy
				self.cursor = 0

		if len(self.line_edit_box.text) == 0:
			pass
		#self.inp.key_backspace_press = False

		if len(self.structure) == 0:
			self.structure = [ ("??:??.??",-1.0,"") ]

		if line_number == len(self.structure) or temp != self.structure[line_number]:
			self.autosave_timer.set()
			self.autosaved = False

	def update_edit_point(self, text_coll: tuple[int, int, int, int], full_coll: tuple[int, int, int, int]) -> tuple[tuple[int,int], bool]:
		ctf = False
		not_cleared_already = self.edit_point is not None
		if self.inp.mouse_click:
			if self.coll(text_coll): # set edit point if clicking in text
				self.edit_point = copy.deepcopy(self.inp.mouse_position)
			elif self.coll(full_coll): # clear edit point if clicking away
				self.edit_point = None
				ctf = False # overengineered as fuck but now we can click a timestamp but can't instanly delete shit
			else:
				self.edit_point = None
				ctf = True and not_cleared_already
		if self.inp.key_esc_press and not_cleared_already:
			self.edit_point = None
			self.inp.key_esc_press = False
			ctf = True and not_cleared_already
		return self.edit_point if self.edit_point is not None else self.inp.mouse_position, ctf

	def get_edit_point(self) -> tuple[int, int]:
		return self.edit_point if self.edit_point is not None else self.inp.mouse_position

	def synced_render(self, index: int, x: int, y: int, hide_art: bool = False, w: int = 0, h: int = 0) -> None:
		line_ys: list[ tuple[ tuple[ int, int ], float ] | None ] = []
		# saves collider positions alongside their respective lines

		# pause after timestamp edit preview
		if ( self.check_timer.get() > 1.0 or \
		( (self.inp.key_lalt or self.inp.key_ralt) and ( self.inp.mouse_wheel or self.inp.key_left_press or self.inp.key_right_press ) ) ) \
		and self.pctl.playing_state == PlayingState.PLAYING and self.check:
			self.pctl.pause_only()
			self.pctl.decode_time = self.structure[self.check_line][1]
			self.check = None
		elif self.check:
			self.inp.key_left_press = False
			self.inp.key_right_press = False

		# scroll
		old_scroll_pos = self.scroll_position
		if not (self.inp.key_lalt or self.inp.key_ralt):
			self.scroll_position -= self.tauon.smooth_scroll.get_scroll("timed lyrics editor",(0,y,self.window_size[0],h),30*self.gui.scale)
			if old_scroll_pos != self.scroll_position:
				self.recenter_timeout.set()

		highlight = True

		scroll_to = 0
		bg = self.colours.lyrics_panel_background
		if vars(self.normal_color) != vars(self.colours.lyrics) or vars(self.active_color) != vars(self.colours.active_lyric):
			self.recalculate_colors()
		spacing = round(10 * self.gui.scale)
		y_center = self.window_size[1]/2

		# reset scroll position after 5 seconds
		if self.rescroll or (self.recenter_timeout.get() > 5 and self.pctl.playing_state == PlayingState.PLAYING):
			self.rescroll = False
			self.scroll_position = 0

		test_time = self.tauon.get_real_time()

		playing = self.pctl.playing_state == PlayingState.PLAYING

		if self.text_leftovers is not None:
			self.inp.input_text = self.inp.input_text + self.text_leftovers
			self.text_leftovers = None

		# determine active lyric
		if self.pctl.track_queue[self.pctl.queue_step] == index and self.allow_scroll:
			self.line_active = -1
			last = 0
			has_timed = 0
			for i, line in enumerate(self.structure):
				if line[0] == "tag":
					last = i
					continue

				if 0 <= line[1] < test_time:
					has_timed = i
					last = i

				if line[1] >= test_time:
					self.pctl.wake_past_time = line[1]
					self.line_active = last
					has_timed = i
					break
			else:
				self.line_active = has_timed

		# record line heights so we can perfectly center the active lyric
		if self.temp_scale != self.gui.scale or self.temp_w != w:
			self.scroll_position = scroll_to
			self.temp_scale = self.gui.scale
			self.temp_w = w
			self.line_height = self.ddt.get_text_w("?", self.font, True)
			self.yy = self.line_height + spacing

		# don't autoscroll if the new active line is not visible
		if ( self.scroll_position > self.window_size[1]/2 or self.scroll_position < -self.window_size[1]/2 ) \
		and self.temp_line != self.line_active and self.allow_scroll:
			self.scroll_position += self.yy
			self.temp_line = self.line_active

		# scroll boundaries
		if self.allow_scroll:
			self.scroll_position = min( self.scroll_position,  self.line_active*(self.yy) + self.window_size[1]/2 -(self.yy + self.gui.panelBY) )
			self.scroll_position = max( self.scroll_position, -(len(self.structure)-self.line_active)*(self.yy) - self.window_size[1]/2 +(self.yy + self.gui.panelY) )
		self.allow_scroll = True

		# edit point follows all scrolling
		if old_scroll_pos != self.scroll_position:
			distance = self.scroll_position - old_scroll_pos
			if self.edit_point is not None:
				self.edit_point = (self.edit_point[0], self.edit_point[1] + distance)

		center = y_center + self.scroll_position
		# scroll position refers to y offset (in pixels) from the active lyric



		# RENDER LINES
		prev = 0.0
		w = round( (self.x_posns[3]-self.x_posns[2]) * 0.9 )
		location = [ self.x_posns[2], 0 ]
		collider_width = self.x_posns[3] - self.x_posns[4]
		if hide_art:
			maximum_y = self.window_size[1]-self.gui.panelBY-35*self.gui.scale
		else:
			maximum_y = self.window_size[1]

		# highlight for active section
		hy = center + self.yy*(0-self.line_active) - self.yy*0.8
		highlight_y = max(hy, self.gui.panelY)
		highlight_rect = (
			self.x_posns[6-int(playing)],
			highlight_y,
			self.x_posns[6-int(playing)] + self.yy,
			min(max(hy + self.yy*(len(self.structure)+0.8), self.gui.panelY), maximum_y)
		)
		self.ddt.rect_abs(highlight_rect, self.highlight)
		text_boxes_rect = (
			self.x_posns[2],
			highlight_y,
			round( (self.x_posns[3]-self.x_posns[2]) * 0.9 ) + 7*self.gui.scale,
			min(max(hy + self.yy*(len(self.structure)+0.8), self.gui.panelY), maximum_y) - highlight_y,
		)
		full_coll_rect = (
			self.x_posns[1],
			highlight_y,
			round( (self.x_posns[3]-self.x_posns[2]) * 0.9 ) + 7*self.gui.scale + (self.x_posns[2]-self.x_posns[1]),# collider_width,
			min(max(hy + self.yy*(len(self.structure)+0.8), self.gui.panelY), maximum_y) - highlight_y,
		)

		# column headers
		# first we check if we have any real timestamps
		has_timestamps = False
		for line in self.structure:
			if line[1] > 0:
				has_timestamps = True
				break
		if len(self.structure) < 2 or not has_timestamps:
			tsw = self.ddt.get_text_w(_("Timestamps"), self.font, True)
			if playing:
				text_color = self.faded_active_color
				time_color = self.active_color
			else:
				time_color = self.faded_active_color
				text_color = self.active_color
			possible_y = center + self.yy*(-1-self.line_active)
			if possible_y > 0 and possible_y+self.line_height/2 < maximum_y:
				location[1] = round(possible_y)
				self.ddt.text(location, _("Lyrics text"), text_color, self.font, w, bg) # line
				location[0] = self.x_posns[1] - tsw
				self.ddt.text(location, _("Timestamps"), time_color, self.font, 100 * self.gui.scale, bg) # timestamp
				location[0] = self.x_posns[2]

		# render lines
		for i, line in enumerate(self.structure):
			# determine y val
			possible_y = center + self.yy*(i-self.line_active)
			if possible_y > 0 and possible_y+self.line_height/2 < maximum_y: # if line will be visible
				if i < self.line_active:
					prev = max( prev, line[1] )
				active = i == self.line_active and highlight and test_time >= line[1]
				match (active, playing):
					case (True, True):
						text_color = self.faded_active_color
						time_color = self.active_color
					case (False, True):
						text_color = self.faded_color
						time_color = self.normal_color
					case (True, False):
						time_color = self.faded_active_color
						text_color = self.active_color
					case (False, False):
						time_color = self.faded_color
						text_color = self.normal_color

				location[1] = round(possible_y)
				text = line[2]
				if text.rstrip() == "":
					text = "♪♪♪"
				self.ddt.text(location, text, text_color, self.font, w, bg) # line
				location[0] = self.x_posns[1]
				self.ddt.text(location, line[0], time_color, self.font, 100 * self.gui.scale, bg) # timestamp
				location[0] = self.x_posns[2]

				collider = ( round(possible_y), round(possible_y + self.yy) )
				association = collider, line[1]
				line_ys.append( association )
				self.tauon.fields.add( (self.x_posns[4], round(possible_y-0.25*self.line_height), collider_width, self.yy) )
			else:
				line_ys.append( None )


		# all line interactions
		did_one_line = False
		if not (self.gui.box_over or self.tauon.pref_box.enabled or self.box_open):
			self.gui.timed_lyrics_editing_now = False
			# click a lyric to seek to it
			if self.x_posns[4] < self.inp.mouse_position[0] < self.x_posns[3] or self.edit_point is not None:
				if playing:
					if self.gui.panelY < self.inp.mouse_position[1] < self.window_size[1] - self.gui.panelBY \
					and (not h or y < self.inp.mouse_position[1] < y+h) and not self.show_save_dialog:
						for i, rendered_line in enumerate(line_ys):
							if rendered_line is None:
								continue
							if rendered_line[0][0] < self.inp.mouse_position[1] < rendered_line[0][1]:
								if self.inp.mouse_click and rendered_line[1] != -1.0:
									self.pctl.seek_time(rendered_line[1] + self.prefs.sync_lyrics_time_offset/1000)
									self.scroll_position = scroll_to
								elif self.inp.middle_click:
									if rendered_line[1] != -1.0:
										self.structure[i] = ( "??:??.??", -1.0, self.structure[i][2] )
									else:
										self.line_active = i
										self.time_next_line(True)
								break
				else:
					# do line editing while paused
					position, cleared_this_frame = self.update_edit_point(text_boxes_rect, full_coll_rect)
					if self.edit_point is not None:
						self.gui.timed_lyrics_editing_now = True
					if not cleared_this_frame:
						for i, rendered_line in enumerate(line_ys):
							if rendered_line is None:
								continue
							if (rendered_line[0][0]-0.25*self.line_height) < position[1] < (rendered_line[0][1]-0.25*self.line_height):
								self.settings_for_one_line(i, rendered_line[0][0])
								self.gui.timed_lyrics_editing_now = True
								did_one_line = True
					# if user types, scroll to show editing line if it's off screen
					if self.edit_point is not None and self.inp.input_text and (position[1] > self.gui.panelBY or self.gui.panelY > position[1]) and not did_one_line:
						if position[1] > self.gui.panelBY: # scroll down
							self.scroll_position -= max(position[1] - (self.window_size[1]-self.gui.panelBY), 0) + self.yy + int(hide_art)*self.yy
							self.edit_point = (self.edit_point[0], self.edit_point[1] - max(position[1] - (self.window_size[1]-self.gui.panelBY), 0) - self.yy - int(hide_art)*self.yy)
						elif self.gui.panelY > position[1]: # scroll up
							self.scroll_position -= min(position[1] - self.gui.panelY, 0) - self.yy
							self.edit_point = (self.edit_point[0], self.edit_point[1] - min(position[1] - self.gui.panelY, 0) + self.yy)
						self.text_leftovers = self.inp.input_text # we can't put what they typed into the text box now so save it for next frame

			# KEYBOARD SHORTCUTS
			if not did_one_line:
				if (self.inp.key_lalt or self.inp.key_ralt):
					self.scroll_timestamp(self.line_active)

			# alt + up/down arrows to switch lines while playing
			if (self.inp.key_lalt or self.inp.key_ralt) and (self.inp.key_up_press or self.inp.key_down_press):
				if self.inp.key_up_press and self.line_active == 0:
					pass
				elif self.inp.key_down_press and self.line_active == len(self.structure) -1:
					pass
				elif self.structure[self.line_active - self.inp.key_up_press + self.inp.key_down_press][1] < 0:
					pass
				elif self.pctl.playing_state == PlayingState.PLAYING:
					self.pctl.seek_time(self.structure[self.line_active - self.inp.key_up_press + self.inp.key_down_press][1] + self.prefs.sync_lyrics_time_offset/1000)
					self.line_active -= self.inp.key_up_press - self.inp.key_down_press
					self.alted = True
				elif self.pctl.playing_state != PlayingState.STOPPED:
					self.pctl.decode_time = self.structure[self.line_active - self.inp.key_up_press + self.inp.key_down_press][1] + self.prefs.sync_lyrics_time_offset/1000
					self.pctl.new_time = self.pctl.decode_time
					self.pctl.playing_time = self.pctl.decode_time
					_seek = self.tauon.aud.seek(int((self.pctl.decode_time) * 1000), self.prefs.pa_fast_seek)
					self.alted = True
			elif self.alt_timer.get() < 0.3 and not self.alted and not (self.inp.key_lalt or self.inp.key_ralt) and self.structure[self.line_active][1] >= 0:
				if self.pctl.playing_state == PlayingState.PLAYING:
					self.pctl.seek_time(self.structure[self.line_active][1] + self.prefs.sync_lyrics_time_offset/1000)
					self.line_active -= self.inp.key_up_press - self.inp.key_down_press
				elif self.pctl.playing_state != PlayingState.STOPPED:
					self.pctl.decode_time = self.structure[self.line_active][1] + self.prefs.sync_lyrics_time_offset/1000
					self.pctl.new_time = self.pctl.decode_time
					self.pctl.playing_time = self.pctl.decode_time
					_seek = self.tauon.aud.seek(int((self.pctl.decode_time) * 1000), self.prefs.pa_fast_seek)
				self.alted = True
			elif self.alt_timer.get() > 0.3:
				self.alted = False

			if (self.inp.key_lalt or self.inp.key_ralt):
				self.alt_timer.set()

			# ctrl s to save
			if (self.inp.key_ctrl_down or self.inp.key_rctrl_down) and self.inp.key_s_press:
				if self.prefs.show_lyrics_save_menu or (self.inp.key_shift_down or self.inp.key_shiftr_down):
					self.show_save_dialog = True
				else:
					self.save()
				self.inp.key_s_press = False


			# BUTTONS IN THE CORNER
			widths = [
				self.ddt.get_text_w("≪5", self.font),
				self.ddt.get_text_w(_("⇧"), self.font),
				max( self.ddt.get_text_w(_("TIME⏎"), self.big_font), self.ddt.get_text_w(_("TIME+"), self.big_font), self.ddt.get_text_w(_("TIME⇨"), self.big_font)),
				self.ddt.get_text_w("🖫", self.font),
				self.ddt.get_text_w("🗑", self.font),
				self.ddt.get_text_w("   ", self.font)
			]
			if hide_art:
				buttons_y = self.window_size[1]-self.gui.panelBY-20*self.gui.scale
				buttons_x = 10*self.gui.scale
				x_gap = 18*self.gui.scale
			else:
				buttons_y = self.window_size[1]-self.gui.panelBY-35*self.gui.scale
				buttons_x = 25*self.gui.scale
				x_gap = self.yy
			save_gap = round(12 * self.gui.scale)

			# DELETE LINES WHILE PLAYING
			if self.inp.key_del and self.pctl.playing_state == PlayingState.PLAYING:
				self.inp.key_del = False
				if self.inp.key_lalt or self.inp.key_ralt:
					del self.structure[self.line_active]
					if self.line_active == len(self.structure):
						self.line_active -= 1
				elif self.line_active+1 <= len(self.structure)-1:
					del self.structure[self.line_active+1]
				if not self.structure:
					self.structure = [("??:??.??", -1.0, "")]
					self.line_active = max(0, self.line_active)
				self.queue_next_frame = True

			# SWITCH MODES
			if self.button("   ", buttons_x, buttons_y, self.font, tooltip="Go to Unsynced View")[0]:
				self.view_is_synced = False
				self.queue_next_frame = True
			self.synced_img.render(buttons_x-6*self.gui.scale, buttons_y-6*self.gui.scale, self.colours.box_button_text)
			buttons_x += widths[5] + x_gap

			# SAVE AND DISCARD
			gn = copy.deepcopy(self.colours.level_green)
			gn.a = round(gn.a * 0.3)
			saving = self.button( "🖫", buttons_x, buttons_y, self.font, gn, self.colours.level_green)[0]
			if saving is not None:
				if self.prefs.show_lyrics_save_menu or saving==False:
					self.show_save_dialog = True
					self.inp.mouse_click = False
					self.inp.right_click = False
					self.inp.level_2_right_click = False
				else:
					self.save()
			buttons_x += widths[3] + x_gap

			rd = copy.deepcopy(self.colours.level_red)
			rd.a = round(rd.a * 0.3)
			if self.button("🗑", buttons_x, buttons_y, self.font, rd, self.colours.level_red)[0]:
				self.structurize_current(self.pctl.master_library[self.struct_track])
			buttons_x += widths[4] + x_gap

			if not hide_art:
				btx_top: float = 25*self.gui.scale
				bty_top = buttons_y-self.yy-10*self.gui.scale
			else:
				btx_top = buttons_x
				bty_top = buttons_y

			# BACK 5 AND PREVIOUS
			if self.button("≪5", btx_top, bty_top, self.font, off=not playing,
				tooltip=_("Go back 5 seconds"))[0]:
				self.previous( max(test_time-5, 0) )
			btx_top += widths[0] + x_gap

			if self.button(_("⇧"), btx_top, bty_top, self.font,
				off = ( not prev or not playing ), tooltip=_("Go to previous line"))[0]:
				self.previous(prev)
			btx_top += widths[1] + x_gap

			# TIME or CURRENT or ADD TIME: click button or go to previous
			if self.inp.key_lalt or self.inp.key_ralt:
				text = _("TIME⇨")
				time_width = self.ddt.get_text_w(_("TIME⇨"), self.big_font)
			elif self.inp.key_ctrl_down or self.inp.key_rctrl_down:
				text = _("TIME+")
				time_width = self.ddt.get_text_w(_("TIME+"), self.big_font)
			else:
				text = _("TIME⏎")
				time_width = self.ddt.get_text_w(_("TIME⏎"), self.big_font)
			width = self.ddt.get_text_w(text, self.big_font)
			if hide_art:
				x_pos = btx_top + (widths[2] - width)/2
			else:
				x_pos = btx_top

			# the giant TIME button. most important thing in the whole window
			off = self.pctl.playing_state!=PlayingState.PLAYING or not (len(self.structure)>=self.line_active or self.structure[self.line_active][1]<0)
			advance, advance_rect = self.button(text, x_pos, bty_top, self.big_font,
				off=off, big=True, return_rect=True)
			match advance:
				case True:
					self.time_next_line(self.inp.key_lalt or self.inp.key_ralt)
				case False:
					self.previous( max(prev, self.pctl.decode_time-5, 0) )
				case None:
					if not off:
						if self.inp.key_return_press:
							self.time_next_line(self.inp.key_lalt or self.inp.key_ralt)
						elif self.inp.key_backspace_press:
							self.previous( max(test_time-5, 0, prev) )
					elif self.coll(advance_rect) and self.inp.mouse_click:
						self.pctl.play() # wht a terrible bit of code
						# if user clicks the giant TIME button while it's grayed out, start playing

			# lyrics search status
			if btx_top + widths[2] + x_gap + max( self.ddt.get_text_w(_("Searching..."), self.font), self.ddt.get_text_w(_("Errored"), self.font) ) > self.window_size[0]:
				btx_top = (25 - 15*hide_art) * self.gui.scale
				bty_top -= self.yy+10*self.gui.scale
			else:
				btx_top += time_width + x_gap -7*self.gui.scale
			match self.tauon.now_searching:
				case "off":
					pass
				case "searching":
					self.ddt.text([btx_top,bty_top],_("Searching..."), self.colours.lyrics, self.font)
				case "errored":
					if self.text_timer.get() > 10:
						self.text_timer.set()
						self.ddt.text([btx_top,bty_top],_("Failed"), self.colours.level_yellow, self.font)
					elif self.text_timer.get() < 2: # display error text for 2 seconds
						self.ddt.text([btx_top,bty_top],_("Failed"), self.colours.level_yellow, self.font)
					else:
						self.tauon.now_searching = "off"
				case "success":
					index = self.pctl.track_queue[self.pctl.queue_step]
					track = self.pctl.master_library[index]
					self.structurize_current(track)
					self.tauon.now_searching = "off"

			if self.show_save_dialog:
				self.save_dialog()

		# end of stuff blocked by boxes being open

		if self.prefs.synced_lyrics_editor_track_end_mode == "stop" or (self.prefs.synced_lyrics_editor_track_end_mode == "repeat" and self.pctl.playing_state == PlayingState.PLAYING):
			if self.pctl.playing_length - self.pctl.decode_time < 5.5:
				self.queue_next_frame = True
			if self.pctl.playing_length - self.pctl.decode_time < 2.1:
				if self.prefs.synced_lyrics_editor_track_end_mode == "stop":
					self.pctl.stop()
				elif not self.repeat_mode: # repeat
					self.repeat_mode = [ self.pctl.repeat_mode, self.pctl.album_repeat_mode ]
					self.pctl.repeat_mode = True
					self.pctl.album_repeat_mode = False


		if self.autosave_timer.get() > 5 and not self.autosaved:
			self.autosave()

		if self.pctl.playing_state == PlayingState.PLAYING:
			self.pausing = True
		else:
			self.pausing = False


	# UNSYNCED EDITING FUNCTIONS

	def test_update(self) -> None:
		"""reload unsynced data from saved track"""
		self.file_has_synced_already = None
		track_object = self.pctl.master_library[self.struct_track]
		LRC_tags = "[ti:", "[ar:", "[al:", "[au:", "[lr:", "[length:", "[by:", "[offset:", "[re:", "[tool:", "[ve:", "[#:"
		self.text = ""

		def is_int(number: str) -> bool:
			try:
				int(number)
				return True
			except ValueError:
				return False

		for line in track_object.lyrics.splitlines():
			if any(tag in line for tag in LRC_tags):
				continue
			if len(line) >= 10 and line[0] == "[" and ":" in line[:10] \
			and "." in line[:10] and "]" in line and is_int(line[1]):
				pos = line.index("]")+1
				self.text += line[pos:] + "\n"
			else:
				self.text += line + "\n"

		if len(self.text) <= 1:
			self.text = self.placeholder
			self.unsynced_text_box.text = self.text
			self.unsynced_text_box.font = self.font
			self.lyrics_position = 200
			self.unsynced_text_box.cursor_position = len(self.text)
			self.unsynced_text_box.selection = len(self.text)

		self.unsynced_text_box.text_height = 0 # triggers map_lines


	def unsynced_render(self, x: int, y: float, box: float, hide_art: bool) -> None:
		colour = self.colours.lyrics
		bg = self.colours.lyrics_panel_background

		x += box + int(self.window_size[0] * 0.15) + 10 * self.gui.scale
		x -= 100 * self.gui.scale
		w = self.window_size[0] - x - 30 * self.gui.scale
		y = int(self.gui.panelY)
		h = int(self.window_size[1] - self.gui.panelBY - self.gui.panelY)
		offset = 20*self.gui.scale

		# scroll
		old_pos = self.lyrics_position
		self.lyrics_position -= self.scroll.get_scroll("lyrics edit", (x,y,w,h), 30*self.gui.scale)
		tw, th = self.ddt.get_text_wh(self.text + "\n", self.font, w, True)
		self.lyrics_position = max(self.lyrics_position, th * -1 + 100 * self.gui.scale)
		self.lyrics_position = min(self.lyrics_position, 70 * self.gui.scale)
		self.queue_next_frame = self.queue_next_frame or old_pos != self.lyrics_position

		# text focus and keyboard shortcuts are mutually exclusive
		edit_pos, ignore = self.update_edit_point((x,y,w,h),(x,y,w,h))
		self.gui.timed_lyrics_editing_now = coll_point(edit_pos,(x,y,w,h))

		# main editing functionality
		self.unsynced_text_box.text = self.text
		# the draw function returns scroll info for if arrow keys move the cursor offscreen
		self.lyrics_position -= self.unsynced_text_box.draw(
			x, y, self.colours.lyrics, self.gui.timed_lyrics_editing_now and not self.show_save_dialog,
			font = self.font, width = ( w ), height = h, headroom=0,
			scroll=-self.lyrics_position
		)
		self.text = self.unsynced_text_box.text

		# buttons. start by measuring them
		widths = [
			self.ddt.get_text_w("   ", self.font),
			self.ddt.get_text_w(_("🖫"), self.font),
			self.ddt.get_text_w(_("🗑"), self.font),
		]
		if hide_art:
			buttons_y = self.window_size[1]-self.gui.panelBY-20*self.gui.scale
			buttons_x = 10*self.gui.scale
			x_gap = 18*self.gui.scale
		else:
			buttons_y = self.window_size[1]-self.gui.panelBY-35*self.gui.scale
			buttons_x = 25*self.gui.scale
			x_gap = self.yy
		save_gap = round(12 * self.gui.scale)

		# view switcher button
		if self.button("   ", buttons_x, buttons_y, self.font, tooltip="Go to Synced View")[0]:
			self.view_is_synced = True
		self.unsynced_img.render(buttons_x-6*self.gui.scale, buttons_y-6*self.gui.scale, self.colours.box_button_text)
		buttons_x += widths[0] + x_gap

		# save button
		gn = copy.deepcopy(self.colours.level_green)
		gn.a = round(gn.a * 0.3)
		saving = self.button( "🖫", buttons_x, buttons_y, self.font, gn, self.colours.level_green)[0]
		if saving is not None:
			if self.prefs.show_lyrics_save_menu or saving==False: # happens when right clicking
				self.show_save_dialog = True
				self.inp.mouse_click = False
				self.inp.right_click = False
				self.inp.level_2_right_click = False
			else:
				self.save(False)
		buttons_x += widths[1] + x_gap

		# discard button
		rd = copy.deepcopy(self.colours.level_red)
		rd.a = round(rd.a * 0.3)
		if self.button("🗑", buttons_x, buttons_y, self.font, rd, self.colours.level_red)[0]:
			self.test_update()
		buttons_x += widths[2] + x_gap

		# lyrics search status
		if not hide_art:
			btx_top = 25*self.gui.scale
			bty_top = buttons_y-self.yy-10*self.gui.scale
		else:
			btx_top = buttons_x
			bty_top = buttons_y

		match self.tauon.now_searching:
			case "off":
				pass
			case "searching":
				self.ddt.text([btx_top,bty_top],_("Searching..."), self.colours.lyrics, self.font)
			case "errored":
				if self.text_timer.get() > 10:
					self.text_timer.set()
					self.ddt.text([btx_top,bty_top],_("Failed"), self.colours.level_yellow, self.font)
				elif self.text_timer.get() < 2: # display error text for 2 seconds
					self.ddt.text([btx_top,bty_top],_("Failed"), self.colours.level_yellow, self.font)
				else:
					self.tauon.now_searching = "off"
			case "success":
				self.test_update()
				self.tauon.now_searching = "off"

		# ctrl + s to save
		if (self.inp.key_ctrl_down or self.inp.key_rctrl_down) and self.inp.key_s_press:
			if self.prefs.show_lyrics_save_menu or (self.inp.key_shift_down or self.inp.key_shiftr_down):
				self.show_save_dialog = True
			else:
				self.save(False)
			self.inp.key_s_press = False

		if self.show_save_dialog:
			self.save_dialog()


	def render(self) -> None:
		box = int(self.window_size[1] * 0.4 + 120 * self.gui.scale)
		box = min(self.window_size[0] // 2, box)

		hide_art = False
		if self.window_size[0] < 1200 * self.gui.scale:
			hide_art = True

		self.queue_next_frame = False
		index = self.pctl.track_queue[self.pctl.queue_step]
		track = self.pctl.master_library[index]
		if not self.structure or self.struct_track != index:
			if self.struct_track != index and self.struct_track != -1 and self.continuous and 0 < self.track_time_left < 5.0:
				match self.prefs.synced_lyrics_editor_track_end_mode:
					case "autosave":
						self.autosave()
					case "full save":
						self.save()
			self.structurize_current(track)
			self.lyrics_position = 0
			self.test_update()
			self.continuous = True
			self.edit_point = None
			self.clicks = 0
			self.will_overwrite = self.will_overwrite_lyrics(track)
		if self.pctl.decode_time < 1.0 and len(self.repeat_mode) == 2:
			self.pctl.repeat_mode, self.pctl.album_repeat_mode = self.repeat_mode
			self.repeat_mode = []

		self.track_time_left = self.pctl.playing_length - self.pctl.decode_time

		if self.gui.lyrics_editor_update_now[0]:
			self.test_update()
		if self.gui.lyrics_editor_update_now[1]:
			self.structurize_current(track)
		self.gui.lyrics_editor_update_now = [False, False]

		x = int(self.window_size[0] * 0.05)
		y = int((self.window_size[1] / 2) - (box / 2)) - 10 * self.gui.scale

		if hide_art:
			box = 45 * self.gui.scale
		elif self.window_size[1] / self.window_size[0] > 0.7:
			x = int(self.window_size[0] * 0.07)

		bbg = rgb_add_hls(self.colours.lyrics_panel_background, 0, 0.05, 0)  # [255, 255, 255, 18]
		bfg = rgb_add_hls(self.colours.lyrics_panel_background, 0, 0.09, 0)  # [255, 255, 255, 30]
		bft = self.colours.grey(235)
		bbt = self.colours.grey(200)

		t1 = self.colours.grey(250)

		self.gui.vis_4_colour = None
		light_mode = False
		if self.colours.lm:
			bbg = self.colours.vis_colour
			bfg = alpha_blend(ColourRGBA(255, 255, 255, 60), self.colours.vis_colour)
			bft = self.colours.grey(250)
			bbt = self.colours.grey(245)

		if test_lumi(self.colours.lyrics_panel_background) < 0.7:
			light_mode = True
			t1 = self.colours.grey(30)
			self.gui.vis_4_colour = ColourRGBA(40, 40, 40, 255)

		self.ddt.rect((0, self.gui.panelY, self.window_size[0], self.window_size[1] - self.gui.panelY), self.colours.lyrics_panel_background)

		if self.pctl.playing_state == PlayingState.URL_STREAM and not self.tauon.radiobox.dummy_track.title:
			if not self.pctl.tag_meta:
				y = int(self.window_size[1] / 2) - 60 - self.gui.scale
				self.ddt.text((self.window_size[0] // 2, y, 2), self.pctl.url, self.colours.side_bar_line2, 317)
			else:
				w = self.window_size[0] - (x + box) - 30 * self.gui.scale
				x = int((self.window_size[0]) / 2)

				y = int(self.window_size[1] / 2) - 60 - self.gui.scale
				self.ddt.text((x, y, 2), self.pctl.tag_meta, self.colours.side_bar_line1, 216, w)
		else:
			if len(self.pctl.track_queue) < 1:
				self.ddt.alpha_bg = False
				return

			# if self.pctl.draw.button("Return", 20, self.gui.panelY + 5, bg=colours.grey(30)):
			# 	pass

			if self.gui.force_showcase_index >= 0:
				if self.pctl.draw.button(
					_("Playing"), 25 * self.gui.scale, self.gui.panelY + 20 * self.gui.scale, text_highlight_colour=bft,
					text_colour=bbt, background_colour=bbg, background_highlight_colour=bfg):
					self.gui.force_showcase_index = -1
					self.ddt.force_gray = False

			if self.gui.force_showcase_index >= 0:
				index = self.gui.force_showcase_index
				track = self.pctl.master_library[index]
			elif self.pctl.playing_state == PlayingState.URL_STREAM:
				track = self.tauon.radiobox.dummy_track
			else:
				index = self.pctl.track_queue[self.pctl.queue_step]
				track = self.pctl.master_library[index]

			if not hide_art:
				draw_showcase_art_box(self.tauon, track, x, y, box)

			gcx = x + box + int(self.window_size[0] * 0.15) + 10 * self.gui.scale
			gcx -= 50 * self.gui.scale
			w = self.window_size[0] - (x + box) - round(30 * self.gui.scale)
			if self.temp_scale != self.gui.scale or self.temp_w != w or not self.x_posns:
				self.temp_scale = self.gui.scale
				self.temp_w = w
				self.line_height = round(self.ddt.get_text_w("?", self.font, True))
				self.yy = self.line_height + round( 10*self.gui.scale )
				self.x_posns = [ # determines button and text box placement
					round( max( gcx - 130*self.gui.scale, self.line_height/2 ) ),
					round( max( gcx - 100*self.gui.scale, self.yy) ),
					round( gcx ),
					round( max(self.window_size[0] - 90*self.gui.scale, self.window_size[0]*0.98) ),
					round( max( gcx - 145*self.gui.scale, 0 )),
					round( gcx - 70*self.gui.scale ), # vertical highlight for time column while playing
					round( gcx + 30*self.gui.scale ), # vertical highlight for text column while paused
					]
				self.x_posns[2] = max(self.x_posns[1] + 90*self.gui.scale, gcx)
			h = (self.window_size[1] - self.gui.panelBY) - self.gui.panelY

			if self.view_is_synced:
				self.synced_render(track.index, gcx, y, hide_art, w, h)
			else:
				self.unsynced_render(x, y, box, hide_art)

			if self.struct_track in self.potential_uploads:
				upload = self.potential_uploads[self.struct_track]
				if not self.box_open:
					self.upload_synced = self.view_is_synced and upload["syncedLyrics"] != "failed"
					self.upload_static = not self.view_is_synced
				self.box_open = True

				# measure the box height
				box_width = 400*self.gui.scale
				offset = 20*self.gui.scale
				drop_w, text_height = self.ddt.get_text_wh(
						_("Upload lyrics for {artist} - {title}?").format(artist=upload["artistName"], title=upload["trackName"]),
						self.font,
						box_width - 2*offset +12,
						True
					)
				button_height = self.line_height/2 + 14*self.gui.scale
				checkbox_height = 40*self.gui.scale
				box_height = text_height + button_height + checkbox_height + offset



				gn = copy.deepcopy(self.colours.level_yellow)
				gn.a = round(gn.a * 0.3)
				x, y = self.window_size[0]/2, self.window_size[1]/2

				if self.shake_frames:
					shake = (1, 2, 1, 0, -1, -2, -1, 0)
					x += 3*self.gui.scale * shake[ self.shake_frames % 8 ]
					self.shake_frames -= 1
					self.queue_next_frame = True
				rect = ( x - 0.5*box_width, y - 0.5*box_height, box_width, box_height)
				self.ddt.bordered_rect( rect, self.colours.box_background, self.colours.box_text_border, round(1*self.gui.scale))
				txt = self.colours.box_button_text

				x0 = rect[0] + offset
				y0 = rect[1] + offset
				self.ddt.text( [x0,y0,4,box_width-2*offset], _("Upload lyrics for {artist} - {title}?").format(artist=upload["artistName"], title=upload["trackName"]), txt, self.font)
				y0 += text_height

				width = self.ddt.get_text_w(_("Synced"), 13)
				cancel = self.ddt.get_text_w(_("Cancel"), self.font)

				# don't allow user to check synced box if synced lyrics are unusable
				# shake the box to indicate there's a problem, then show the error if they keep going
				old_upload_synced = self.upload_synced
				if self.tauon.pref_box.toggle_square(rect[0]+offset, y0, self.upload_synced, _("Synced"), self.inp.mouse_click):
					new_upload_synced = True
					if upload["syncedLyrics"] != "failed":
						self.upload_synced = True
					else:
						self.shake_frames = 30
						self.queue_next_frame = True
				else:
					new_upload_synced = False
					self.upload_synced = False
				self.clicks += new_upload_synced != old_upload_synced and upload["syncedLyrics"] == "failed"
				if self.clicks > 2:
					self.tauon.show_message(
							_("Lyrics must be formatted correctly"),
							_("Your synced lyrics are either out of order or not fully timed."),
							_("We cannot upload broken lyrics to LRCLIB."),
							mode="error"
						)
					self.clicks = 0

				self.upload_static = self.tauon.pref_box.toggle_square(rect[0]+3*offset+width, y0, self.upload_static, _("Unsynced"), self.inp.mouse_click)
				y0 += checkbox_height - 7*self.gui.scale
				if self.button(_("Upload"), rect[0] + offset, y0, self.font, gn, self.colours.level_yellow, off=not(self.upload_synced or self.upload_static))[0]:
					if not self.upload_synced:
						upload["syncedLyrics"] = ""
					if not self.upload_static:
						upload["plainLyrics"] = ""
					self.tauon.lrclib_uploads.append(upload)
					self.tauon.thread_manager.ready("worker")
					del self.potential_uploads[self.struct_track]
				if self.button(_("Cancel"), rect[0] + rect[2] - cancel - offset, y0, self.font, tooltip=_("Delete the file."))[0] \
					or ( self.inp.mouse_click and not self.coll(rect) ):
					del self.potential_uploads[self.struct_track]
					self.queue_next_frame = True
			else:
				self.box_open = False
				self.clicks = 0

			if self.gui.panelY < self.inp.mouse_position[1] < self.window_size[1] - self.gui.panelBY:
				if self.inp.right_click:
					# track = self.pctl.playing_object()
					if track is not None:
						if self.view_is_synced:
							self.menu.activate(track)
						else:
							self.unsynced_menu.activate(track)

		# queue a frame update if the user moves over or off of any button
		if self.queue_next_frame:
			self.gui.request_tracklist_redraw()
		self.ddt.alpha_bg = False
		self.ddt.force_gray = False
def find_synced_lyric_data(track: TrackClass, just_check: bool = False, reload: bool = False) -> list[str] | bool | None:
	"""Return list of strings if lyrics match LRC format, otherwise return None.
	just_check returns True if current track.lyrics fit LRC format.
	reload will try to OVERWRITE track.synced with new data.

	See https://en.wikipedia.org/wiki/LRC_(file_format)
	"""
	if not just_check:
		if not reload and track.synced:
			if lyrics_are_synced(track.synced):
				return track.synced.splitlines()
			logging.warning(
				f"Synced lyrics for {track.filename} do not look like LRC. Reclassifying them as static lyrics."
			)
			if not track.lyrics:
				track.lyrics = track.synced
			track.synced = ""
			return None
		if track.is_network:
			return None

	# Check if internal track lyrics are synced lyrics
	if track.lyrics:
		if lyrics_are_synced(track.lyrics):
			if not just_check:
				track.synced = track.lyrics
				return track.lyrics.splitlines()
			return True
		if just_check:
			return False


	# Check if we have a .LRC file
	direc = Path(track.parent_folder_path)
	if not direc.is_dir():
		logging.warning(f"Could not find directory: {track.parent_folder_path}")
		return None

	name = os.path.splitext(track.filename)[0]

	# Case-insensitive file check
	matched_file = next(
		(
			f for f in direc.iterdir()
			if f.is_file()
			and f.stem == name
			and f.suffix.lower() == ".lrc"
		),
		None,
	)

	if matched_file:
		try:
			with matched_file.open(encoding="utf-8") as f:
				data = f.readlines()
		except Exception:
			logging.exception("Read lyrics file error")
			return None
		track.synced = "\n".join(data)
		return data

	return None
