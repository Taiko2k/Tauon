"""Overlay and dialog UI components."""

from __future__ import annotations

import copy
import logging
import os
import webbrowser
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Protocol

import mutagen
import sdl3
from PIL import Image

from tauon.t_modules.t_art import AlbumArt
from tauon.t_modules.t_enums import GuiMode, MiniModeMode, PlayingState, StopMode
from tauon.t_modules.t_extra import (
	TestTimer,
	Timer,
	alpha_blend,
	check_equal,
	clean_string,
	hls_to_rgb,
	hls_hue_mix,
	hls_pull_contrast,
	point_proximity_test,
	rgb_to_hls,
	shooter,
)
from tauon.t_modules.t_models import ColourRGBA, TauonPlaylist, TrackClass, queue_item_gen
from tauon.t_modules.t_prefs import Prefs
from tauon.t_modules.t_state import ColoursClass, GuiVar, Input, MenuTrackRef, asset_loader
from tauon.t_modules.t_templates import parse_template2, unique_template
from tauon.t_modules.t_text import TextBox, TextBox2
from tauon.t_modules.t_widgets import Fields

if TYPE_CHECKING:
	from tauon.t_modules.t_draw import TDraw


class _OverlayApp(Protocol):
	gui: GuiVar
	ddt: TDraw
	inp: Input
	coll: Callable[[object], bool]
	draw: Any
	pctl: Any
	fields: Fields
	colours: ColoursClass
	prefs: Prefs
	window_size: list[int]
	bag: Any
	dirs: Any
	show_message: Callable[..., object]

class TransEditBox:

	def __init__(self, tauon: _OverlayApp) -> None:
		self.tauon             = tauon
		self.gui               = tauon.gui
		self.ddt               = tauon.ddt
		self.inp               = tauon.inp
		self.coll              = tauon.coll
		self.draw              = tauon.draw
		self.pctl              = tauon.pctl
		self.fields            = tauon.fields
		self.colours           = tauon.colours
		self.star_store        = tauon.star_store
		self.window_size       = tauon.window_size
		self.show_message      = tauon.show_message
		self.edit_title        = tauon.edit_title
		self.edit_album        = tauon.edit_album
		self.edit_artist       = tauon.edit_artist
		self.edit_album_artist = tauon.edit_album_artist
		self.active = False
		self.active_field = 1
		self.selected = []
		self.playlist = -1

	def render(self) -> None:
		if not self.active:
			return

		if self.gui.level_2_click:
			self.inp.mouse_click = True
		self.gui.level_2_click = False

		w = 500 * self.gui.scale
		h = 255 * self.gui.scale
		x = int(self.window_size[0] / 2) - int(w / 2)
		y = int(self.window_size[1] / 2) - int(h / 2)

		self.ddt.rect_a((x - 2 * self.gui.scale, y - 2 * self.gui.scale), (w + 4 * self.gui.scale, h + 4 * self.gui.scale), self.colours.box_border)
		self.ddt.rect_a((x, y), (w, h), self.colours.box_background)
		self.ddt.text_background_colour = self.colours.box_background

		if self.inp.key_esc_press or ((self.inp.mouse_click or self.inp.right_click or self.inp.level_2_right_click) and not self.coll((x, y, w, h))):
			self.active = False

		select = list(set(self.gui.shift_selection))
		if not select and self.pctl.selected_ready():
			select = [self.pctl.selected_in_playlist]

		titles        = [self.pctl.get_track(self.pctl.default_playlist[s]).title for s in select]
		artists       = [self.pctl.get_track(self.pctl.default_playlist[s]).artist for s in select]
		albums        = [self.pctl.get_track(self.pctl.default_playlist[s]).album for s in select]
		album_artists = [self.pctl.get_track(self.pctl.default_playlist[s]).album_artist for s in select]

		#logging.info(select)
		if select != self.selected or self.pctl.active_playlist_viewing != self.playlist:
			#logging.info("reset")
			self.selected = select
			self.playlist = self.pctl.active_playlist_viewing
			self.edit_album.clear()
			self.edit_artist.clear()
			self.edit_title.clear()
			self.edit_album_artist.clear()

			if len(select) == 0:
				return

			tr = self.pctl.get_track(self.pctl.default_playlist[select[0]])
			self.edit_title.set_text(tr.title)

			if check_equal(artists):
				self.edit_artist.set_text(artists[0])

			if check_equal(albums):
				self.edit_album.set_text(albums[0])

			if check_equal(album_artists):
				self.edit_album_artist.set_text(album_artists[0])

		x += round(20 * self.gui.scale)
		y += round(18 * self.gui.scale)

		self.ddt.text((x, y), _("Simple tag editor"), self.colours.box_title_text, 215)

		if self.draw.button(_("?"), x + 440 * self.gui.scale, y):
			self.show_message(
				_("Press Enter in each field to apply its changes to local database."),
				_("When done, press WRITE TAGS to save to tags in actual files. (Optional but recommended)"),
				mode="info")

		y += round(24 * self.gui.scale)
		self.ddt.text((x, y), _("Number of tracks selected: {N}").format(N=len(select)), self.colours.box_title_text, 313)

		y += round(24 * self.gui.scale)

		if self.inp.key_tab_press:
			if self.inp.key_shift_down or self.inp.key_shiftr_down:
				self.active_field -= 1
			else:
				self.active_field += 1

		if self.active_field < 0:
			self.active_field = 3
		if self.active_field == 4:
			self.active_field = 0
			if len(select) > 1:
				self.active_field = 1

		def field_edit(x: int, y: int, label: str, field_number: int, names: list[str], text_box: TextBox2) -> bool:
			changed = False
			self.ddt.text((x, y), label, self.colours.box_text_label, 11)
			y += round(16 * self.gui.scale)
			rect1 = (x, y, round(370 * self.gui.scale), round(17 * self.gui.scale))
			self.fields.add(rect1)
			if (self.coll(rect1) and self.inp.mouse_click) or (self.inp.key_tab_press and self.active_field == field_number):
				self.active_field = field_number
			self.ddt.bordered_rect(rect1, self.colours.box_background, self.colours.box_text_border, round(1 * self.gui.scale))
			tc = self.colours.box_input_text
			if names and check_equal(names) and text_box.text == names[0]:
				h, l, s = rgb_to_hls(tc.r, tc.g, tc.b)
				l *= 0.7
				tc = hls_to_rgb(h, l, s)
			else:
				changed = True
			if not (names and check_equal(names)) and not text_box.text:
				changed = False
				self.ddt.text((x + round(2 * self.gui.scale), y), _("<Multiple selected>"), self.colours.box_text_label, 12)
			text_box.draw(x + round(3 * self.gui.scale), y, tc, self.active_field == field_number, width=370 * self.gui.scale)
			if changed:
				self.ddt.text((x + 377 * self.gui.scale, y - 1 * self.gui.scale), "⮨", self.colours.box_title_text, 214)
			return changed

		changed = False
		if len(select) == 1:
			changed |= field_edit(x, y, _("Track title"), 0, titles, self.edit_title)
		y += round(40 * self.gui.scale)
		changed |= field_edit(x, y, _("Album name"), 1, albums, self.edit_album)
		y += round(40 * self.gui.scale)
		changed |= field_edit(x, y, _("Artist name"), 2, artists, self.edit_artist)
		y += round(40 * self.gui.scale)
		changed |= field_edit(x, y, _("Album-artist name"), 3, album_artists, self.edit_album_artist)

		y += round(40 * self.gui.scale)
		for s in select:
			tr = self.pctl.get_track(self.pctl.default_playlist[s])
			if tr.is_network:
				self.ddt.text((x, y), _("Editing network tracks is not recommended!"), ColourRGBA(245, 90, 90, 255), 312)

		if self.inp.key_return_press:
			self.gui.request_tracklist_redraw()
			if self.active_field == 0 and len(select) == 1:
				for s in select:
					tr = self.pctl.get_track(self.pctl.default_playlist[s])
					star = self.star_store.full_get(tr.index)
					self.star_store.remove(tr.index)
					tr.title = self.edit_title.text
					self.star_store.merge(tr.index, star)

			if self.active_field == 1:
				for s in select:
					tr = self.pctl.get_track(self.pctl.default_playlist[s])
					tr.album = self.edit_album.text
			if self.active_field == 2:
				for s in select:
					tr = self.pctl.get_track(self.pctl.default_playlist[s])
					star = self.star_store.full_get(tr.index)
					self.star_store.remove(tr.index)
					tr.artist = self.edit_artist.text
					self.star_store.merge(tr.index, star)
			if self.active_field == 3:
				for s in select:
					tr = self.pctl.get_track(self.pctl.default_playlist[s])
					tr.album_artist = self.edit_album_artist.text
			self.tauon.bg_save()

		ww = self.ddt.get_text_w(_("WRITE TAGS"), 212) + round(48 * self.gui.scale)
		if self.gui.write_tag_in_progress:
			text = f"{self.gui.tag_write_count}/{len(select)}"
		text = _("WRITE TAGS")
		if self.draw.button(text, (x + w) - ww, y - (0) * self.gui.scale):
			if changed:
				self.show_message(_("Press enter on fields to apply your changes first!"))
				return

			if self.gui.write_tag_in_progress:
				return

			def write_tag_go() -> None:
				for s in select:
					tr = self.pctl.get_track(self.pctl.default_playlist[s])

					if tr.is_network:
						self.show_message(_("Writing to a network track is not applicable!"), mode="error")
						self.gui.write_tag_in_progress = True
						return
					if tr.is_cue:
						self.show_message(_("Cannot write CUE sheet types!"), mode="error")
						self.gui.write_tag_in_progress = True
						return

					muta = mutagen.File(tr.fullpath, easy=True)

					def write_tag(track: TrackClass, muta, field_name_tauon, field_name_muta) -> int:
						item = muta.get(field_name_muta)
						if item and len(item) > 1:
							self.show_message(_("Cannot handle multi-field! Please use external tag editor"), mode="error")
							return 0
						if not getattr(tr, field_name_tauon):  # Want delete tag field
							if item:
								del muta[field_name_muta]
						else:
							muta[field_name_muta] = getattr(tr, field_name_tauon)
						return 1

					write_tag(tr, muta, "artist", "artist")
					write_tag(tr, muta, "album", "album")
					write_tag(tr, muta, "title", "title")
					write_tag(tr, muta, "album_artist", "albumartist")

					muta.save()
					self.gui.tag_write_count += 1
					self.gui.request_frame()
				self.tauon.bg_save()
				if not self.gui.message_box:
					self.show_message(_("{N} files rewritten").format(N=self.gui.tag_write_count), mode="done")
				self.gui.write_tag_in_progress = False
			if not self.gui.write_tag_in_progress:
				self.gui.tag_write_count = 0
				self.gui.write_tag_in_progress = True
				shooter(write_tag_go)

class SubLyricsBox:

	def __init__(self, tauon: _OverlayApp) -> None:
		self.ddt:             TDraw = tauon.ddt
		self.gui:            GuiVar = tauon.gui
		self.inp:             Input = tauon.inp
		self.coll                   = tauon.coll
		self.fields:         Fields = tauon.fields
		self.prefs:           Prefs = tauon.prefs
		self.colours:  ColoursClass = tauon.colours
		self.window_size: list[int] = tauon.window_size
		self.sub_lyrics_a: TextBox2 = tauon.sub_lyrics_a
		self.sub_lyrics_b: TextBox2 = tauon.sub_lyrics_b
		self.active:           bool = False
		self.target_track: TrackClass | None = None
		self.active_field:      int = 1

	def activate(self, track: TrackClass) -> None:
		self.active = True
		self.gui.box_over = True
		self.target_track = track

		self.sub_lyrics_a.text = self.prefs.lyrics_subs.get(self.target_track.artist, "")
		self.sub_lyrics_b.text = self.prefs.lyrics_subs.get(self.target_track.title, "")

		if not self.sub_lyrics_a.text:
			self.sub_lyrics_a.text = self.target_track.artist
		if not self.sub_lyrics_b.text:
			self.sub_lyrics_b.text = self.target_track.title

	def render(self) -> None:
		if not self.active:
			return

		if self.gui.level_2_click:
			self.inp.mouse_click = True
		self.gui.level_2_click = False

		w = 400 * self.gui.scale
		h = 155 * self.gui.scale
		x = int(self.window_size[0] / 2) - int(w / 2)
		y = int(self.window_size[1] / 2) - int(h / 2)

		self.ddt.rect_a((x - 2 * self.gui.scale, y - 2 * self.gui.scale), (w + 4 * self.gui.scale, h + 4 * self.gui.scale), self.colours.box_border)
		self.ddt.rect_a((x, y), (w, h), self.colours.box_background)
		self.ddt.text_background_colour = self.colours.box_background

		if self.inp.key_esc_press or ((self.inp.mouse_click or self.inp.right_click or self.inp.level_2_right_click) and not self.coll((x, y, w, h))):
			self.active = False
			self.gui.box_over = False

			if self.sub_lyrics_a.text and self.sub_lyrics_a.text != self.target_track.artist:
				self.prefs.lyrics_subs[self.target_track.artist] = self.sub_lyrics_a.text
			elif self.target_track.artist in self.prefs.lyrics_subs:
				del self.prefs.lyrics_subs[self.target_track.artist]

			if self.sub_lyrics_b.text and self.sub_lyrics_b.text != self.target_track.title:
				self.prefs.lyrics_subs[self.target_track.title] = self.sub_lyrics_b.text
			elif self.target_track.title in self.prefs.lyrics_subs:
				del self.prefs.lyrics_subs[self.target_track.title]

		self.ddt.text((x + 10 * self.gui.scale, y + 8 * self.gui.scale), _("Substitute Lyric Search"), self.colours.grey(230), 213)

		y += round(35 * self.gui.scale)
		x += round(23 * self.gui.scale)

		xx = x
		xx += self.ddt.text(
			(x + round(0 * self.gui.scale), y + round(0 * self.gui.scale)), _("Substitute"), self.colours.box_text_label, 212)
		xx += round(6 * self.gui.scale)
		self.ddt.text((xx, y + round(0 * self.gui.scale)), self.target_track.artist, self.colours.box_sub_text, 312)

		y += round(19 * self.gui.scale)
		xx = x
		xx += self.ddt.text((xx + round(0 * self.gui.scale), y + round(0 * self.gui.scale)), _("with"), self.colours.box_text_label, 212)
		xx += round(6 * self.gui.scale)
		rect1 = (xx, y, round(250 * self.gui.scale), round(17 * self.gui.scale))
		self.fields.add(rect1)
		self.ddt.bordered_rect(rect1, self.colours.box_background, self.colours.box_text_border, round(1 * self.gui.scale))
		if (self.coll(rect1) and self.inp.mouse_click) or (self.inp.key_tab_press and self.active_field == 2):
			self.active_field = 1
			self.inp.key_tab_press = False

		self.sub_lyrics_a.draw(
			xx + round(4 * self.gui.scale), y, self.colours.box_input_text, self.active_field == 1,
			width=rect1[2] - 8 * self.gui.scale)

		y += round(28 * self.gui.scale)

		xx = x
		xx += self.ddt.text(
			(x + round(0 * self.gui.scale), y + round(0 * self.gui.scale)), _("Substitute"), self.colours.box_text_label, 212)
		xx += round(6 * self.gui.scale)
		self.ddt.text((xx, y + round(0 * self.gui.scale)), self.target_track.title, self.colours.box_sub_text, 312)

		y += round(19 * self.gui.scale)
		xx = x
		xx += self.ddt.text((xx + round(0 * self.gui.scale), y + round(0 * self.gui.scale)), _("with"), self.colours.box_text_label, 212)
		xx += round(6 * self.gui.scale)
		rect1 = (xx, y, round(250 * self.gui.scale), round(16 * self.gui.scale))
		self.fields.add(rect1)
		if (self.coll(rect1) and self.inp.mouse_click) or (self.inp.key_tab_press and self.active_field == 1):
			self.active_field = 2
		# ddt.rect(rect1, [40, 40, 40, 255], True)
		self.ddt.bordered_rect(rect1, self.colours.box_background, self.colours.box_text_border, round(1 * self.gui.scale))
		self.sub_lyrics_b.draw(
			xx + round(4 * self.gui.scale), y, self.colours.box_input_text, self.active_field == 2, width=rect1[2] - 8 * self.gui.scale)

class ExportPlaylistBox:

	def __init__(self, tauon: _OverlayApp) -> None:
		self.tauon        = tauon
		self.ddt          = tauon.ddt
		self.gui          = tauon.gui
		self.inp          = tauon.inp
		self.coll         = tauon.coll
		self.draw         = tauon.draw
		self.pctl         = tauon.pctl
		self.prefs        = tauon.prefs
		self.fields       = tauon.fields
		self.colours      = tauon.colours
		self.pref_box     = tauon.pref_box
		self.window_size  = tauon.window_size
		self.show_message = tauon.show_message
		self.active = False
		self.playlist_id = 0
		self.directory_text_box = TextBox2(tauon)

		# self.default = {
		# 	"path": self.prefs.playlist_folder_path if self.prefs.playlist_folder_path else ( str(tauon.dirs.music_directory) if tauon.dirs.music_directory else str(tauon.dirs.user_directory / "playlists") ),
		# 	"type": "xspf",
		# 	"relative": False,
		# 	"auto": False,
		# 	"auto_imp": False,
		# }

	def activate(self, playlist_index: int) -> None:
		"""Runs when the playlist export menu is opened"""
		self.active = True
		self.gui.box_over = True

		playlist = self.pctl.multi_playlist[playlist_index]
		id = playlist.uuid_int
		self.playlist_id = id

		if not playlist.playlist_file:
			playlist.playlist_file = self.suggest_default_playlist_target(playlist)

	def suggest_default_playlist_target(self, playlst: TauonPlaylist) -> str:
		if self.prefs.playlist_folder_path:
			path = str(self.prefs.playlist_folder_path)
			if not path.endswith("/") and not path.endswith("\\"):
				path += "/"
			return path
		if self.tauon.dirs.music_directory:
			return str(self.tauon.dirs.music_directory) + "/"
		return str(self.tauon.dirs.user_directory / "playlists/")

	def render(self) -> None:
		"""Runs every frame that the playlist export menu is open.
		also deals with the export entry logic.
		"""
		if not self.active:
			return

		gui = self.tauon.gui
		ddt = self.tauon.ddt
		colours = self.tauon.colours

		w = 500 * gui.scale
		h = 180 * gui.scale
		x = int(self.window_size[0] / 2) - int(w / 2)
		y = int(self.window_size[1] / 2) - int(h / 2)

		ddt.rect_a((x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale), colours.box_border)
		ddt.rect_a((x, y), (w, h), colours.box_background)
		ddt.text_background_colour = colours.box_background

		playlist_id = self.playlist_id
		pl = self.pctl.id_to_pl(playlist_id)

		if pl is None or self.inp.key_esc_press or ((self.inp.mouse_click or gui.level_2_click or self.inp.right_click or self.inp.level_2_right_click) and not self.coll(
				(x, y, w, h))):
			self.active = False
			gui.box_over = False

		playlist = self.pctl.multi_playlist[pl]

		# Title
		ddt.text((x + 10 * gui.scale, y + 8 * gui.scale), _("Import/Export Playlist"), colours.grey(230), 213)

		# Path entry
		x += round(15 * gui.scale)
		y += round(25 * gui.scale)
		ddt.text((x, y + 8 * gui.scale), _("Target folder or file"), colours.grey(230), 11)
		y += round(30 * gui.scale)
		rect1 = (x, y, round(450 * gui.scale), round(16 * gui.scale))
		self.fields.add(rect1)
		ddt.bordered_rect(rect1, colours.box_background, colours.box_text_border, round(1 * gui.scale))

		self.directory_text_box.text = playlist.playlist_file
		self.directory_text_box.draw(
			x + round(4 * gui.scale), y, colours.box_input_text, True,
			width=rect1[2] - 8 * gui.scale, click=gui.level_2_click)

		text = self.directory_text_box.text
		playlist.playlist_file = text
		root, ext = os.path.splitext(text)

		xx = x + rect1[2]
		yy = y + rect1[3] + round(3 * gui.scale)
		if text.endswith("/") or text.endswith("\\"):
			if Path(self.pctl.resolve_full_playlist_path(playlist)).exists():
				ddt.text((xx, yy, 1), _("Will overwrite existing file: ") + f" {self.pctl.resolve_full_playlist_path(playlist, get_name=True)}", ColourRGBA(80, 230, 80, 255), 10)
				yy += round(13 * gui.scale)
			else:
				ddt.text((xx, yy, 1), _("Will save with playlist name:") + f" {self.pctl.resolve_full_playlist_path(playlist, get_name=True)}", colours.grey(190), 10)
				yy += round(13 * gui.scale)
		elif not ext:
			ddt.text((xx, yy, 1), _("No file extension?"), colours.grey(190), 10)
			yy += round(13 * gui.scale)
		elif ext:
			if playlist.export_type == "xspf" and ext.lower() != ".xspf":
				ddt.text((xx, yy, 1), _("Incorrect extension?"), colours.grey(190), 10)
				yy += round(13 * gui.scale)
			if playlist.export_type == "m3u" and ext.lower() not in (".m3u", ".m3u8"):
				ddt.text((xx, yy, 1), _("Incorrect extension?"), colours.grey(190), 10)
				yy += round(13 * gui.scale)
		if not Path(self.pctl.resolve_full_playlist_path(playlist)).parent.is_dir():
			ddt.text((xx, yy, 1), _("Will create directory"), colours.grey(190), 10)

		y += round(30 * gui.scale)
		if playlist.playlist_file.lower().endswith(".xspf"):
			playlist.export_type = "xspf"
		if playlist.playlist_file.lower().endswith(".m3u") or playlist.playlist_file.lower().endswith(".m3u8"):
			playlist.export_type = "m3u"

		old = playlist.export_type
		if self.pref_box.toggle_square(x, y, playlist.export_type == "xspf", "XSPF", gui.level_2_click):
			playlist.export_type = "xspf"
		if self.pref_box.toggle_square(x + round(80 * gui.scale), y, playlist.export_type == "m3u", "M3U", gui.level_2_click):
			playlist.export_type = "m3u"

		# fix ext if user changed it
		new = playlist.export_type
		if old != new and ext and ext in (".m3u", ".xspf", ".m3u8"):
			path = Path(text).with_suffix("." + playlist.export_type)
			playlist.playlist_file = str(path)

		y += round(30 * gui.scale)
		playlist.relative_export = self.pref_box.toggle_square(
			x, y, playlist.relative_export, _("Use relative paths"),
			gui.level_2_click)
		ww = ddt.get_text_w(_("Use relative paths"), 211)
		if self.draw.button(_("?"), x + ww + round(45*gui.scale), y - (3*gui.scale), press=gui.level_2_click):
			self.show_message(
						_("Enable relative paths when keeping playlist files together with audio"),
						_("Disable to move playlist files while keeping audio in one location"))


		y += round(30 * gui.scale)
		playlist.auto_export = self.pref_box.toggle_square(x, y, playlist.auto_export, _("Auto-export"), gui.level_2_click)
		playlist.auto_import = self.pref_box.toggle_square(x + round(130*gui.scale), y, playlist.auto_import, _("Auto-import"), gui.level_2_click)


		y += round(0 * gui.scale)
		ww = ddt.get_text_w(_("Export"), 211)
		x = ((int(self.window_size[0] / 2) - int(w / 2)) + w) - (ww + round(40 * gui.scale))

		if self.draw.button(_("Export"), x, y - (2*gui.scale), press=gui.level_2_click):
			self.run_export(playlist_id, warnings=True)

	def run_export(self, id, warnings: bool = True) -> None:
		logging.info("Exporting playlist")

		# Fetch corresponding TauonPlaylist object
		pl = None
		pl = self.pctl.id_to_pl(id)
		if pl is None:
			return
		playlist = self.pctl.multi_playlist[pl]

		# Resolve full path
		path = Path(self.pctl.resolve_full_playlist_path(playlist))
		logging.info(f"Export path: {path}")

		if not path.exists():
			logging.warning("Path does not exist, attempting to create")

		try:
			if not path.parent.is_dir():
				path.parent.mkdir(parents=True)
		except PermissionError:
			logging.error("Export failed, cannot create dirs due to permissions")  # noqa: TRY400
			return



		target = ""
		try:
			if playlist.export_type == "xspf":
				target = self.tauon.export_xspf(self.pctl.id_to_pl(id), pl_file=path, relative=playlist.relative_export)
			if playlist.export_type == "m3u":
				target = self.tauon.export_m3u(self.pctl.id_to_pl(id), pl_file=path, relative=playlist.relative_export)
		except PermissionError:
			logging.error("Export failed due to permissions")  # noqa: TRY400

		if target and isinstance(target, Path):
			playlist.file_size = target.stat().st_size
			playlist.playlist_file = str( target )

		if warnings and target != 1:
			self.show_message(_("Playlist exported"), str(target), mode="done")

class MessageBox:

	def __init__(self, tauon: _OverlayApp) -> None:
		self.tauon       = tauon
		self.ddt         = tauon.ddt
		self.gui         = tauon.gui
		self.inp         = tauon.inp
		self.draw        = tauon.draw
		self.colours     = tauon.colours
		self.window_size = tauon.window_size
		bag = tauon.bag
		self.message_info_icon     = asset_loader(bag, bag.loaded_asset_dc, "notice.png")
		self.message_warning_icon  = asset_loader(bag, bag.loaded_asset_dc, "warning.png")
		self.message_tick_icon     = asset_loader(bag, bag.loaded_asset_dc, "done.png")
		self.message_arrow_icon    = asset_loader(bag, bag.loaded_asset_dc, "ext.png")
		self.message_error_icon    = asset_loader(bag, bag.loaded_asset_dc, "error.png")
		self.message_bubble_icon   = asset_loader(bag, bag.loaded_asset_dc, "bubble.png")
		self.message_download_icon = asset_loader(bag, bag.loaded_asset_dc, "ddl.png")

	def get_rect(self) -> tuple[int, int, float, int]:
		w1 = self.ddt.get_text_w(self.gui.message_text, 15) + 74 * self.gui.scale
		w2 = self.ddt.get_text_w(self.gui.message_subtext, 12) + 74 * self.gui.scale
		w3 = self.ddt.get_text_w(self.gui.message_subtext2, 12) + 74 * self.gui.scale
		w = max(w1, w2, w3)

		w = max(w, 210 * self.gui.scale)

		h = round(60 * self.gui.scale)
		if self.gui.message_subtext2:
			h += round(15 * self.gui.scale)

		x = int(self.window_size[0] / 2) - int(w / 2)
		y = int(self.window_size[1] / 2) - int(h / 2)

		return x, y, w, h

	def render(self) -> None:
		inp = self.inp
		gui = self.gui
		ddt = self.ddt
		if inp.mouse_click or inp.key_return_press or inp.right_click or inp.key_esc_press or inp.backspace_press \
				or gui.keymaps.test("quick-find") or (inp.k_input and self.tauon.message_box_min_timer.get() > 1.2):

			if not inp.key_focused and self.tauon.message_box_min_timer.get() > 0.4:
				gui.message_box = False
				gui.request_frame()
				inp.key_return_press = False

		x, y, w, h = self.get_rect()

		ddt.rect_a((x - 2 * gui.scale, y - 2 * gui.scale), (w + 4 * gui.scale, h + 4 * gui.scale),
			self.colours.box_text_border)
		ddt.rect_a((x, y), (w, h), self.colours.message_box_bg)

		ddt.text_background_colour = self.colours.message_box_bg

		if gui.message_mode == "info":
			self.message_info_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(self.message_info_icon.h / 2) - 1)
		elif gui.message_mode == "warning":
			self.message_warning_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(self.message_info_icon.h / 2) - 1)
		elif gui.message_mode == "done":
			self.message_tick_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(self.message_info_icon.h / 2) - 1)
		elif gui.message_mode == "arrow":
			self.message_arrow_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(self.message_info_icon.h / 2) - 1)
		elif gui.message_mode == "download":
			self.message_download_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(self.message_info_icon.h / 2) - 1)
		elif gui.message_mode == "error":
			self.message_error_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(self.message_error_icon.h / 2) - 1)
		elif gui.message_mode == "bubble":
			self.message_bubble_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(self.message_bubble_icon.h / 2) - 1)
		elif gui.message_mode == "link":
			self.message_info_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(self.message_bubble_icon.h / 2) - 1)
		elif gui.message_mode == "confirm":
			self.message_info_icon.render(x + 14 * gui.scale, y + int(h / 2) - int(self.message_info_icon.h / 2) - 1)
			ddt.text((x + 62 * gui.scale, y + 9 * gui.scale), gui.message_text, self.colours.message_box_text, 15)
			if self.draw.button("Yes", (w // 2 + x) - 70 * gui.scale, y + 32 * gui.scale, w=60*gui.scale):
				gui.message_box = False
				if gui.message_box_confirm_callback:
					gui.message_box_confirm_callback(*gui.message_box_confirm_reference)
			if self.draw.button("No", (w // 2 + x) + 25 * gui.scale, y + 32 * gui.scale, w=60*gui.scale):
				gui.message_box = False
				if gui.message_box_no_callback:
					gui.message_box_no_callback(*gui.message_box_confirm_reference)
			return

		if gui.message_subtext:
			ddt.text((x + 62 * gui.scale, y + 11 * gui.scale), gui.message_text, self.colours.message_box_text, 15)
			if gui.message_mode in ("bubble", "link"):
				link_pa = self.tauon.draw_linked_text((x + 63 * gui.scale, y + (9 + 22) * gui.scale), gui.message_subtext,
					self.colours.message_box_text, 12)
				self.tauon.link_activate(x + 63 * gui.scale, y + (9 + 22) * gui.scale, link_pa)
			else:
				ddt.text((x + 63 * gui.scale, y + (9 + 22) * gui.scale), gui.message_subtext, self.colours.message_box_text,
					12)

			if gui.message_subtext2:
				ddt.text((x + 63 * gui.scale, y + (9 + 42) * gui.scale), gui.message_subtext2, self.colours.message_box_text,
					12)
		else:
			ddt.text((x + 62 * gui.scale, y + 20 * gui.scale), gui.message_text, self.colours.message_box_text, 15)

class PresetDownloadBox:

	def __init__(self, tauon: _OverlayApp) -> None:
		self.tauon = tauon
		self.gui = tauon.gui
		self.inp = tauon.inp
		self.ddt = tauon.ddt
		self.draw = tauon.draw
		self.colours = tauon.colours
		self.window_size = tauon.window_size
		self.active: bool = False
		self.cancel_requested: bool = False
		self.progress: float = 0.0
		self.title: str = ""
		self.status: str = ""
		self.detail: str = ""
		self.done: bool = False
		self.cancel_detail: str = ""

	def start(self, *, title: str, status: str, cancel_detail: str) -> None:
		self.active = True
		self.cancel_requested = False
		self.done = False
		self.progress = 0.0
		self.title = title
		self.status = status
		self.detail = ""
		self.cancel_detail = cancel_detail
		self.gui.request_frame()

	def update(self, progress: float | None, status: str, detail: str = "") -> None:
		if progress is not None:
			self.progress = max(0.0, min(1.0, progress))
		self.status = status
		self.detail = detail
		self.gui.request_frame()

	def finish(self) -> None:
		self.active = False
		self.cancel_requested = False
		self.done = False
		self.gui.request_frame()

	def complete(self, status: str, detail: str = "", toast_text: str | None = None) -> None:
		self.progress = 1.0
		self.status = status
		self.detail = detail
		self.finish()
		if toast_text:
			self.tauon.toast(toast_text)

	def fail(self, status: str, detail: str = "") -> None:
		self.active = True
		self.cancel_requested = False
		self.done = True
		self.status = status
		self.detail = detail
		self.gui.request_frame()

	def cancel(self) -> None:
		self.cancel_requested = True
		self.status = _("Cancelling...")
		self.detail = self.cancel_detail
		self.gui.request_frame()

	def render(self) -> None:
		if not self.active:
			return

		gui = self.gui
		ddt = self.ddt
		scale = gui.scale
		w = round(430 * scale)
		h = round(134 * scale)
		x = int(self.window_size[0] / 2) - int(w / 2)
		y = int(self.window_size[1] / 2) - int(h / 2)

		panel = self.colours.message_box_bg
		border = self.colours.box_text_border
		ddt.rect_a((x - 2 * scale, y - 2 * scale), (w + 4 * scale, h + 4 * scale), border)
		ddt.rect_a((x, y), (w, h), panel)
		ddt.text_background_colour = panel

		ddt.text((x + 22 * scale, y + 16 * scale), self.title, self.colours.message_box_text, 15)
		ddt.text((x + 22 * scale, y + 43 * scale), self.status, self.colours.box_text_label, 12, max_w=w - 44 * scale)
		if self.detail:
			ddt.text((x + 22 * scale, y + 62 * scale), self.detail, self.colours.box_text_label, 12, max_w=w - 44 * scale)

		bar_x = x + round(22 * scale)
		bar_y = y + round(86 * scale)
		bar_w = w - round(44 * scale)
		bar_h = round(10 * scale)
		fill_w = round(bar_w * self.progress)
		ddt.rect((bar_x, bar_y, bar_w, bar_h), self.colours.box_button_background)
		if fill_w > 0:
			ddt.rect((bar_x, bar_y, fill_w, bar_h), self.colours.link_text)
		percent = f"{round(self.progress * 100)}%"
		ddt.text((bar_x + bar_w, bar_y + round(15 * scale), 1), percent, self.colours.box_text_label, 12)

		if self.done:
			label = _("Close")
			press = None
		elif self.cancel_requested:
			label = _("Cancelling...")
			press = False
		else:
			label = _("Cancel")
			press = None
		button_w = round((112 if self.cancel_requested else 74) * scale)
		if self.draw.button(label, x + w - button_w - round(22 * scale), y + h - round(34 * scale), w=button_w, press=press):
			if self.done:
				self.finish()
			else:
				self.cancel()

class NagBox:
	SPLASH_VERSION = "11.0.0"
	RELEASE_NOTES_URL = "https://github.com/Taiko2k/TauonMusicBox/releases"
	DONATE_URL = "https://github.com/sponsors/Taiko2k"
	PATREON_URL = "https://www.patreon.com/taiko2k"
	CHANGELOG_ITEMS = (
		("New layout engine supporting custom layouts!", False),
		("Added rounded corners setting", False),
		("Added lyrics search to global search", False),
		("Added new widget: Spectogram", False),
		("Added new widget: Track Details", False),
		("Added new widget: Compact Gallery", False),
		("Improvements to network buffering", False),
	)

	def __init__(self, tauon: _OverlayApp) -> None:
		self.tauon        = tauon
		self.gui          = tauon.gui
		self.inp          = tauon.inp
		self.ddt          = tauon.ddt
		self.prefs        = tauon.prefs
		self.colours      = tauon.colours
		self.window_size  = tauon.window_size
		self.drawer       = tauon.draw

	def dismiss(self) -> None:
		self.prefs.show_nag = False
		self.gui.request_frame()
		self.gui.level_2_click = False
		self.inp.mouse_click = False
		self.inp.key_return_press = False
		self.inp.key_esc_press = False

	def show(self) -> None:
		self.prefs.show_nag = True
		self.gui.request_frame()
		self.gui.level_2_click = False
		self.inp.mouse_click = False

	def open_release_notes(self) -> None:
		webbrowser.open(self.RELEASE_NOTES_URL, new=2, autoraise=True)

	def open_donate_link(self) -> None:
		webbrowser.open(self.DONATE_URL, new=2, autoraise=True)

	def thank_donor(self) -> None:
		self.dismiss()
		self.tauon.show_message(_("Yay! Thank you!! 🎉 ✨"), mode="done")

	def draw_left_accent_gradient(self, x: int, y: int, w: int, h: int) -> None:
		top = ColourRGBA(205, 226, 92, 255)
		bottom = ColourRGBA(86, 190, 104, 255)
		steps = max(1, round(h / max(self.gui.scale, 1)))
		for step in range(steps):
			ratio = step / max(steps - 1, 1)
			colour = ColourRGBA(
				round(top.r + (bottom.r - top.r) * ratio),
				round(top.g + (bottom.g - top.g) * ratio),
				round(top.b + (bottom.b - top.b) * ratio),
				255,
			)
			y1 = y + round((h * step) / steps)
			y2 = y + round((h * (step + 1)) / steps)
			self.ddt.rect((x, y1, w, max(1, y2 - y1)), colour)

	def draw(self) -> None:
		w = round(640 * self.gui.scale)
		h = round(384 * self.gui.scale)
		x = int(self.window_size[0] / 2) - int(w / 2)
		y = int(self.window_size[1] / 2) - int(h / 2)

		if self.inp.key_esc_press or self.inp.key_return_press or self.inp.backspace_press:
			self.dismiss()
			return

		if self.gui.level_2_click and not self.tauon.coll((x, y, w, h)):
			self.dismiss()
			return

		scale = self.gui.scale
		accent = self.colours.link_text
		accent_warm = ColourRGBA(255, 158, 94, 255)
		panel_border = alpha_blend(ColourRGBA(255, 255, 255, 20), self.colours.box_text_border)
		panel_fill = self.colours.message_box_bg
		section_fill = alpha_blend(ColourRGBA(255, 255, 255, 7), self.colours.box_button_background)
		divider = alpha_blend(ColourRGBA(255, 255, 255, 24), self.colours.box_text_border)
		inner_pad = round(24 * scale)
		inner_x = x + inner_pad
		inner_y = y + round(22 * scale)
		inner_w = w - inner_pad * 2

		self.ddt.bordered_rect((x, y, w, h), panel_fill, panel_border, round(1 * scale))
		self.draw_left_accent_gradient(x, y, round(5 * scale), h)
		self.ddt.text_background_colour = panel_fill

		version_text = "_OverlayApp v11"
		self.ddt.text((inner_x, inner_y), version_text, self.colours.box_title_text, 217, bg=panel_fill)
		self.ddt.text(
			(inner_x, inner_y + round(27 * scale), 4, inner_w, round(42 * scale)),
			_("Your ultimate _OverlayApp upgrade is here!"),
			self.colours.box_title_text,
			12,
			bg=panel_fill,
		)

		changelog_y = inner_y + round(58 * scale)
		changelog_h = round(172 * scale)
		self.ddt.rect((inner_x, changelog_y, inner_w, changelog_h), section_fill)
		self.ddt.rect((inner_x, changelog_y, inner_w, round(1 * scale)), divider)
		self.ddt.rect((inner_x, changelog_y + changelog_h - round(1 * scale), inner_w, round(1 * scale)), divider)
		self.ddt.text(
			(inner_x + round(16 * scale), changelog_y + round(13 * scale)),
			_("Changelog Highlights"),
			self.colours.box_text,
			213,
			bg=section_fill,
		)

		row_y = changelog_y + round(38 * scale)
		row_gap = round(18 * scale)
		bullet_colour = ColourRGBA(176, 214, 104, 255)
		for item, removed in self.CHANGELOG_ITEMS:
			text_colour = self.colours.box_text_label if removed else self.colours.box_text
			self.ddt.rect(
				(inner_x + round(17 * scale), row_y + round(5 * scale), round(6 * scale), round(6 * scale)),
				bullet_colour,
			)
			self.ddt.text(
				(inner_x + round(34 * scale), row_y),
				item,
				text_colour,
				13,
				bg=section_fill,
				max_w=inner_w - round(52 * scale),
			)
			row_y += row_gap

		support_y = changelog_y + changelog_h + round(16 * scale)
		self.ddt.text((inner_x, support_y), _("Please help support me make free software. ❤️  "), self.colours.box_text, 213, bg=panel_fill)
		self.ddt.text(
			(inner_x, support_y + round(19 * scale)),
			_("Special thanks to everyone who donated."),
			self.colours.box_text,
			12,
			bg=panel_fill,
			max_w=inner_w,
		)
		donate_y = support_y + round(37 * scale)
		donate_link = self.tauon.draw_linked_text(
			(inner_x, donate_y),
			_("If you haven't, please consider donating at https://github.com/sponsors/Taiko2k"),
			self.colours.box_text,
			12,
			replace=_("GitHub Sponsors"),
		)
		self.tauon.link_activate(inner_x, donate_y, donate_link, click=self.gui.level_2_click)
		patreon_x = inner_x + donate_link[0] + donate_link[1] + self.ddt.get_text_w(" ", 12)
		patreon_prefix = _("or on my ")
		self.ddt.text(
			(patreon_x, donate_y),
			patreon_prefix,
			self.colours.box_text,
			12,
			bg=panel_fill,
		)
		patreon_link_x = patreon_x + self.ddt.get_text_w(patreon_prefix, 12)
		patreon_link = self.tauon.draw_linked_text(
			(patreon_link_x, donate_y),
			self.PATREON_URL,
			self.colours.box_text,
			12,
			force=True,
			replace="Patreon.",
		)
		self.tauon.link_activate(patreon_link_x, donate_y, patreon_link, click=self.gui.level_2_click)
		self.ddt.text(
			(inner_x, support_y + round(55 * scale)),
			_("Your continued support helps keep this app alive."),
			self.colours.box_text,
			12,
			bg=panel_fill,
			max_w=inner_w,
		)

		button_y = y + h - round(46 * scale)
		button_h = round(30 * scale)
		close_w = max(round(96 * scale), self.ddt.get_text_w(_("Close"), 212) + round(22 * scale))
		close_x = x + w - close_w - inner_pad

		if self.drawer.button(_("Close"), close_x, button_y, w=close_w, h=button_h, press=self.gui.level_2_click):
			self.dismiss()

class PowerTag:

	def __init__(self) -> None:
		self.name: str = "BLANK"
		self.path: str = ""
		self.position: int = 0
		self.colour: ColourRGBA | None = None

		#self.peak_x: int = 0
		self.ani_timer: Timer = Timer()
		self.ani_timer.force_set(10)
class StyleOverlay:
	"""Stage:
	0 - blank
	1 - preparing first
	2 - render first
	"""

	def __init__(self, tauon: _OverlayApp) -> None:
		self.tauon:   _OverlayApp = tauon
		self.gui:     GuiVar = tauon.gui
		self.ddt:     TDraw = tauon.ddt
		self.pctl:    Any = tauon.pctl
		self.prefs:   Prefs = tauon.prefs
		self.renderer       = tauon.renderer
		self.window_size: list[int]    = tauon.window_size
		self.album_art_gen: AlbumArt  = AlbumArt(tauon=tauon, style_overlay=self)
		self.thread_manager: Any = tauon.thread_manager
		self.min_on_timer:   Timer = Timer()
		self.fade_on_timer:  Timer = Timer(0)
		self.fade_off_timer: Timer = Timer()

		# TODO(Martin): Document and probably turn into an enum
		self.stage: int = 0

		self.im = None
		# SDL surface decoded by the worker, awaiting texture upload
		self.surface = None

		self.a_texture = None
		self.a_rect = None

		self.b_texture = None
		self.b_rect = None

		# 0 = album art, 1 = artist background (anchored to the window top)
		self.a_type = 0
		self.b_type = 0

		self.window_size_int = None
		self.parent_path = None

		self.hole_punches: list[sdl3.SDL_FRect] = []
		#self.hole_refills = []

		# Small copy of the processed blur image for sampling local colour
		# under UI elements (see sample_background). `sample_source` is set
		# by the worker thread, promoted to `sample_a` alongside a_texture;
		# the previous sample is kept as `sample_b` so sampled colours can
		# crossfade in step with the art transition.
		self.sample_source: Image.Image | None = None
		self.sample_a: Image.Image | None = None
		self.sample_b: Image.Image | None = None

		# Averaged sample for the whole tracklist area, refreshed at the
		# start of each tracklist render so all its text shares one tint
		self.tracklist_sample: ColourRGBA | None = None

		# Fade progress quantised into 8 steps: the tracklist only re-renders
		# on step changes, and text colours only take 8 values per fade
		# instead of a new cache entry every frame
		self._fade_step: int = -1

		self.go_to_sleep: bool = False

		self.current_track_album: str = "none"
		self.current_track_id: int = -1

	def worker(self) -> None:
		if self.stage == 0:
			if (self.gui.mode == GuiMode.MINI and self.prefs.mini_mode_mode == MiniModeMode.SLATE):
				pass

			if self.pctl.playing_ready() and self.min_on_timer.get() > 0:

				track = self.pctl.playing_object()

				self.window_size_int = copy.copy(self.window_size)
				self.parent_path = track.parent_folder_path
				self.current_track_id = track.index
				self.current_track_album = track.album

				try:
					self.im = self.album_art_gen.get_blur_im(track)
				except Exception:
					logging.exception("Blur blackground error")
					raise
					#logging.debug(track.fullpath)

				if self.im is None or self.im is False:
					if self.a_texture:
						self.stage = 2
						self.fade_off_timer.set()
						self.go_to_sleep = True
						return
					self.flush()
					self.min_on_timer.force_set(-4)
					return

				# Decode to an SDL surface here on the worker thread; a
				# full-size image decode on the main thread would hitch the
				# start of the fade
				self.surface = self.ddt.load_image(self.im)
				self.im.close()
				self.im = None

				self.stage = 1
				self.gui.request_frame()
				return

	def flush(self) -> None:
		if self.a_texture is not None:
			sdl3.SDL_DestroyTexture(self.a_texture)
			self.a_texture = None
		if self.b_texture is not None:
			sdl3.SDL_DestroyTexture(self.b_texture)
			self.b_texture = None
		if self.surface is not None:
			sdl3.SDL_DestroySurface(self.surface)
			self.surface = None
		self.sample_a = None
		self.sample_b = None
		self._fade_step = -1
		# Drop any baked-in tints from the tracklist
		self.gui.request_tracklist_redraw()
		self.min_on_timer.force_set(-0.2)
		self.parent_path = "None"
		self.stage = 0
		self.thread_manager.ready("worker")
		self.gui.style_worker_timer.set()
		self.gui.delay_frame(0.25)
		self.gui.request_frame()

	def sample_background(self, x: float, y: float) -> ColourRGBA | None:
		"""Local colour of the blurred art background near window point (x, y).

		While a new art background is fading in over the old one, the two
		samples are crossfaded with the same timing so derived colours
		follow the transition instead of jumping. Returns None when the art
		background isn't currently displayed. (No stage check: while the
		worker prepares the next track's blur the old background is still
		on screen, and its sample stays valid.)"""
		sample = self.sample_a
		if sample is None or self.a_rect is None or not self.gui.have_art_bg:
			return None
		# Offscreen Custom Layout widgets draw in a local space at the
		# scratch origin; map to true window coordinates so they sample
		# the art actually behind them
		x, y = self.tauon.inp.to_screen(x, y)
		fx = min(1.0, max(0.0, (x - self.a_rect.x) / max(1.0, self.a_rect.w)))
		fy = min(1.0, max(0.0, (y - self.a_rect.y) / max(1.0, self.a_rect.h)))
		w, h = sample.size
		r, g, b = sample.getpixel((int(fx * (w - 1)), int(fy * (h - 1))))[:3]
		t = self.fade_on_timer.get()
		if t < 0.4 and self.sample_b is not None:
			w2, h2 = self.sample_b.size
			r2, g2, b2 = self.sample_b.getpixel((int(fx * (w2 - 1)), int(fy * (h2 - 1))))[:3]
			f = min(1.0, max(0.0, int(t / 0.4 * 8) / 8))
			r = round(r2 + (r - r2) * f)
			g = round(g2 + (g - g2) * f)
			b = round(b2 + (b - b2) * f)
		return ColourRGBA(r, g, b, 255)

	def sample_background_average(self, x: float, y: float, w: float, h: float) -> ColourRGBA | None:
		"""Average of a grid of local samples across the given window rect,
		for tinting a whole region's text with one uniform colour."""
		rt = gt = bt = 0
		points = (0.17, 0.5, 0.83)
		for fx in points:
			for fy in points:
				s = self.sample_background(x + w * fx, y + h * fy)
				if s is None:
					return None
				rt += s.r
				gt += s.g
				bt += s.b
		n = len(points) ** 2
		return ColourRGBA(round(rt / n), round(gt / n), round(bt / n), 255)

	def adjust_strength(self) -> float:
		"""0..1 weight for background-derived colour adjustments.

		Ramps up with the art fade-in when there is no previous art to
		crossfade from, and back down with the fade-out, so tinted/boosted
		colours track the background's actual visibility. Quantised to the
		same 8 steps as the sample crossfade."""
		if self.go_to_sleep:
			t = self.fade_off_timer.get()
			if t > 1:
				return max(0.0, 1.0 - int(min(0.4, t - 1) / 0.4 * 8) / 8)
			return 1.0
		if self.sample_b is None:
			return min(1.0, int(max(0.0, self.fade_on_timer.get()) / 0.4 * 8) / 8)
		return 1.0

	def tint_from_background(
		self, colour: ColourRGBA, x: float, y: float, amount: float = 0.15,
		panel: ColourRGBA | None = None, boost: float = 1.0,
	) -> ColourRGBA:
		"""Mix a little of the background art's local hue/saturation into
		colour (keeping its lightness and alpha), so grey furniture doesn't
		clash with a coloured backdrop. Passes colour through unchanged when
		no art background is showing.

		If `panel` (the translucent panel fill the element sits on) is given,
		the colour's lightness is also boosted away from the effective
		backdrop — the panel blended over the local art — so buttons can't
		land at the same lightness as the art behind them. The boost is
		gentler below high art strength; `boost` scales it further."""
		return self.tint_from_sample(colour, self.sample_background(x, y), amount, panel, boost)

	def tint_from_sample(
		self, colour: ColourRGBA, sample: ColourRGBA | None, amount: float = 0.15,
		panel: ColourRGBA | None = None, boost: float = 1.0,
	) -> ColourRGBA:
		"""tint_from_background against an already-sampled background colour
		(e.g. the averaged tracklist sample)."""
		if sample is None:
			return colour
		strength = self.adjust_strength()
		if strength <= 0:
			return colour
		colour = hls_hue_mix(colour, sample, amount * strength)
		if panel is not None:
			f = panel.a / 255
			backdrop = ColourRGBA(
				round(panel.r * f + sample.r * (1 - f)),
				round(panel.g * f + sample.g * (1 - f)),
				round(panel.b * f + sample.b * (1 - f)), 255)
			floor = 0.18 if self.prefs.art_bg_stronger >= 3 else 0.12
			colour = hls_pull_contrast(colour, backdrop, floor * strength * boost)
		return colour

	def display(self, background: bool = False) -> None:
		if background:
			# True-background mode: draw an opaque base directly onto the
			# current render target at the start of the frame; the art fades
			# in over it and the UI (translucent panels, text) draws on top.
			base = self.tauon.colours.playlist_panel_background
			self.ddt.rect(
				(0, 0, self.window_size[0], self.window_size[1]),
				ColourRGBA(base.r, base.g, base.b, 255))

		if self.min_on_timer.get() < 0:
			return

		if self.stage == 1 and self.surface is None:
			# Flushed between the worker's decode and the upload; start over
			self.stage = 0

		if self.stage == 1:

			# The surface was decoded on the worker thread; only the texture
			# upload happens here. (Streaming the upload in strips across
			# frames was tried and made things worse: on Metal every
			# mid-frame SDL_UpdateTexture splits the render pass, turning
			# one stall into many.)
			surf = self.surface.contents

			c = sdl3.SDL_CreateTextureFromSurface(self.renderer, self.surface)

			dst = sdl3.SDL_FRect(-40)
			dst.w = surf.w
			dst.h = surf.h

			sdl3.SDL_DestroySurface(self.surface)
			self.surface = None

			self.fade_on_timer.set()
			# Step 0 of the colour crossfade reproduces the on-screen
			# colours; skip its tracklist redraw — this frame already
			# carries the texture upload
			self._fade_step = 0

			if self.a_texture is not None:
				self.b_texture = self.a_texture
				self.b_rect = self.a_rect
				self.b_type = self.a_type
				self.sample_b = self.sample_a

			self.a_texture = c
			self.a_rect = dst
			self.a_type = self.album_art_gen.loaded_bg_type
			self.sample_a = self.sample_source

			self.stage = 2
			self.radio_meta = None

			self.gui.request_frame()

		if self.stage == 2:
			track = self.pctl.playing_object()

			if self.pctl.playing_state == PlayingState.URL_STREAM:
				if self.radio_meta != self.pctl.tag_meta:
					self.radio_meta = self.pctl.tag_meta
					self.current_track_id = -1
					self.stage = 0

			elif not self.go_to_sleep and self.b_texture is None and self.current_track_id != track.index:
				self.radio_meta = None
				if not track.album:
					self.stage = 0
				else:
					self.current_track_id = track.index
					if (
							self.parent_path != self.pctl.playing_object().parent_folder_path or self.current_track_album != self.pctl.playing_object().album):
						self.stage = 0

		if self.gui.mode == GuiMode.MINI and self.prefs.mini_mode_mode == MiniModeMode.SLATE:
			pass

		t = self.fade_on_timer.get()
		if not background:
			sdl3.SDL_SetRenderTarget(self.renderer, self.gui.main_texture_overlay_temp)
			sdl3.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)
			sdl3.SDL_RenderClear(self.renderer)

		if self.a_texture is not None and self.window_size_int != self.window_size:
			self.flush()

		if self.b_texture is not None:

			self.b_rect.y = 0 - self.b_rect.h // 4
			if self.b_type == 1:
				self.b_rect.y = 0

			if t < 0.4:
				if background:
					# The alpha mod may be left over from when this was the
					# fading-in front texture
					sdl3.SDL_SetTextureAlphaMod(self.b_texture, 255)
				sdl3.SDL_RenderTexture(self.renderer, self.b_texture, None, self.b_rect)

			elif t > 0.55:
				# Deferred a beat past the fade's end: releasing a large
				# texture on the same frame the animation lands is a
				# visible hitch
				sdl3.SDL_DestroyTexture(self.b_texture)
				self.b_texture = None
				self.b_rect = None
			else:
				self.gui.request_frame()

		if self.a_texture is not None:

			self.a_rect.y = 0 - self.a_rect.h // 4
			if self.a_type == 1:
				self.a_rect.y = 0

			if t < 0.4:
				fade = round(t / 0.4 * 255)
				self.gui.request_frame()
				# Tracklist text colours derived from the background are
				# baked into its cached texture; re-render it through the
				# fade, but only at each quantised colour step
				step = int(t / 0.4 * 8)
				if step != self._fade_step:
					self._fade_step = step
					self.gui.request_tracklist_redraw()

			else:
				fade = 255
				if self._fade_step != -1:
					# One last re-render at the fade's final colours
					self._fade_step = -1
					self.gui.request_tracklist_redraw()

			if self.go_to_sleep:
				t = self.fade_off_timer.get()
				self.gui.request_frame()
				# Colour adjustments only ramp down in the 1..1.4 stretch
				if t > 1:
					step = int(min(0.4, t - 1) / 0.4 * 8)
					if step != self._fade_step:
						self._fade_step = step
						self.gui.request_tracklist_redraw()

				if t < 1:
					fade = 255
				elif t < 1.4:
					fade = 255 - round((t - 1) / 0.4 * 255)
				else:
					self.go_to_sleep = False
					self.flush()
					return

			# Center image
			if self.window_size[0] < 900 * self.gui.scale:
				self.a_rect.x = (self.window_size[0] // 2) - self.a_rect.w // 2
			else:
				self.a_rect.x = -40

			if background:
				# Drawn straight onto the frame background; panel translucency
				# (set in update_layout_do) controls how strongly it shows
				# through, so no whole-window opacity pass or hole punching
				# is needed.
				sdl3.SDL_SetTextureAlphaMod(self.a_texture, fade)
				sdl3.SDL_RenderTexture(self.renderer, self.a_texture, None, self.a_rect)
				return

			sdl3.SDL_SetRenderTarget(self.renderer, self.gui.main_texture_overlay_temp)

			sdl3.SDL_SetTextureAlphaMod(self.a_texture, fade)
			sdl3.SDL_RenderTexture(self.renderer, self.a_texture, None, self.a_rect)

			sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_NONE)

			sdl3.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 0)
			for rect in self.hole_punches:
				sdl3.SDL_RenderFillRect(self.renderer, rect)

			sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_BLEND)

			sdl3.SDL_SetRenderTarget(self.renderer, self.gui.main_texture)
			opacity = self.prefs.art_bg_opacity
			if self.prefs.mini_mode_mode == MiniModeMode.SLATE and self.gui.mode == GuiMode.MINI:
				opacity = 255

			sdl3.SDL_SetTextureAlphaMod(self.gui.main_texture_overlay_temp, opacity)
			sdl3.SDL_RenderTexture(self.renderer, self.gui.main_texture_overlay_temp, None, None)

			sdl3.SDL_SetRenderTarget(self.renderer, self.gui.main_texture)

		elif not background:
			sdl3.SDL_SetRenderTarget(self.renderer, self.gui.main_texture)
class RenameTrackBox:

	def __init__(self, tauon: _OverlayApp) -> None:
		self.tauon        = tauon
		self.inp          = tauon.inp
		self.ddt          = tauon.ddt
		self.gui          = tauon.gui
		self.draw         = tauon.draw
		self.pctl         = tauon.pctl
		self.coll         = tauon.coll
		self.prefs        = tauon.prefs
		self.colours      = tauon.colours
		self.star_store   = tauon.star_store
		self.window_size  = tauon.window_size
		self.rename_files = tauon.rename_files
		self.show_message = tauon.show_message
		self.active = False
		self.target_track_id = None
		self.single_only = False

	def activate(self, track_ref: MenuTrackRef) -> None:
		self.active = True
		self.target_track_id = track_ref.track_id
		if self.inp.key_shift_down or self.inp.key_shiftr_down:
			self.single_only = True
		else:
			self.single_only = False

	def disable_test(self, track_ref: MenuTrackRef) -> bool:
		track_id = track_ref.track_id
		single_only = bool(self.inp.key_shift_down or self.inp.key_shiftr_down)

		if not single_only:
			for item in self.pctl.default_playlist:
				if self.pctl.master_library[item].parent_folder_path == self.pctl.master_library[track_id].parent_folder_path:
					if self.pctl.master_library[item].is_network is True:
						return True
		return False

	def render(self) -> None:
		if not self.active:
			return

		if self.gui.level_2_click:
			self.inp.mouse_click = True
		self.gui.level_2_click = False

		w = 420 * self.gui.scale
		h = 155 * self.gui.scale
		x = int(self.window_size[0] / 2) - int(w / 2)
		y = int(self.window_size[1] / 2) - int(h / 2)

		self.ddt.rect_a((x - 2 * self.gui.scale, y - 2 * self.gui.scale), (w + 4 * self.gui.scale, h + 4 * self.gui.scale), self.colours.box_border)
		self.ddt.rect_a((x, y), (w, h), self.colours.box_background)
		self.ddt.text_background_colour = self.colours.box_background

		if self.inp.key_esc_press or ((self.inp.mouse_click or self.inp.right_click or self.inp.level_2_right_click) and not self.coll((x, y, w, h))):
			self.tauon.rename_track_box.active = False

		r_todo = []

		# Find matching folder tracks in playlist
		if not self.single_only:
			for item in self.pctl.default_playlist:
				if self.pctl.master_library[item].parent_folder_path == self.pctl.master_library[
					self.target_track_id].parent_folder_path:

					# Close and display error if any tracks are not single local files
					if self.pctl.master_library[item].is_network is True:
						self.tauon.rename_track_box.active = False
						self.show_message(_("Cannot rename"), _("One or more tracks is from a network location!"), mode="info")
					if self.pctl.master_library[item].is_cue is True:
						self.tauon.rename_track_box.active = False
						self.show_message(_("This function does not support renaming CUE Sheet tracks."))
					else:
						r_todo.append(item)
		else:
			r_todo = [self.target_track_id]

		self.ddt.text((x + 10 * self.gui.scale, y + 8 * self.gui.scale), _("Track Renaming"), self.colours.grey(230), 213)
		input_h = 23 * self.gui.scale

		# if draw.button("Default", x + 230 * gui.scale, y + 8 * gui.scale,
		if self.rename_files.text != self.prefs.rename_tracks_template and self.draw.button(
			_("Default"), x + w - 85 * self.gui.scale, y + h - 35 * self.gui.scale, 70 * self.gui.scale, input_h):
			self.rename_files.set_text(self.prefs.rename_tracks_template)
			self.rename_files.offset = 0

		# ddt.draw_text((x + 14, y + 40,), NRN + cursor, self.colours.grey(150), 12)
		self.rename_files.draw(
			x + 14 * self.gui.scale,
			y + 39 * self.gui.scale,
			self.colours.box_input_text,
			width=300 * self.gui.scale,
		)
		NRN = self.rename_files.text

		self.ddt.rect_s(
			(x + 8 * self.gui.scale, y + 36 * self.gui.scale, 300 * self.gui.scale, 22 * self.gui.scale), self.colours.box_text_border, 1 * self.gui.scale)

		afterline = ""
		warn = False
		underscore = False

		for item in r_todo:
			if self.pctl.master_library[item].track_number == "" or self.pctl.master_library[item].artist == "" or \
					self.pctl.master_library[item].title == "" or self.pctl.master_library[item].album == "":
				warn = True

			if item == self.target_track_id:
				afterline = parse_template2(NRN, self.pctl.master_library[item])

		self.ddt.text((x + 10 * self.gui.scale, y + 68 * self.gui.scale), _("BEFORE"), self.colours.box_text_label, 212)
		line = self.tauon.trunc_line(self.pctl.master_library[self.target_track_id].filename, 12, 335)
		self.ddt.text((x + 70 * self.gui.scale, y + 68 * self.gui.scale), line, self.colours.grey(210), 211, max_w=340)

		self.ddt.text((x + 10 * self.gui.scale, y + 83 * self.gui.scale), _("AFTER"), self.colours.box_text_label, 212)
		self.ddt.text((x + 70 * self.gui.scale, y + 83 * self.gui.scale), afterline, self.colours.grey(210), 211, max_w=340)

		if (len(NRN) > 3 and len(self.pctl.master_library[self.target_track_id].filename) > 3 and afterline[-3:].lower() !=
			self.pctl.master_library[self.target_track_id].filename[-3:].lower()) or len(NRN) < 4 or "." not in afterline[-5:]:
			self.ddt.text(
				(x + 10 * self.gui.scale, y + 108 * self.gui.scale), _("Warning: This may change the file extension"),
				ColourRGBA(245, 90, 90, 255),
				13)

		colour_warn = ColourRGBA(143, 186, 65, 255)
		if not unique_template(NRN):
			self.ddt.text(
				(x + 10 * self.gui.scale, y + 123 * self.gui.scale), _("Warning: The filename might not be unique"),
				ColourRGBA(245, 90, 90, 255),
				13)
		if warn:
			self.ddt.text(
				(x + 10 * self.gui.scale, y + 135 * self.gui.scale), _("Warning: A track has incomplete metadata"),
				ColourRGBA(245, 90, 90, 255),
				13)
			colour_warn = ColourRGBA(180, 60, 60, 255)

		label = _("Write") + " (" + str(len(r_todo)) + ")"

		if self.draw.button(
			label, x + (8 + 300 + 10) * self.gui.scale, y + 36 * self.gui.scale, 80 * self.gui.scale, input_h,
			text_highlight_colour=self.colours.grey(255), background_highlight_colour=colour_warn,
			tooltip=_("Physically renames all the tracks in the folder")) or self.inp.level_2_enter:

			self.inp.mouse_click = False
			total_todo = len(r_todo)
			pre_state = 0

			for item in r_todo:
				if self.pctl.playing_state != PlayingState.STOPPED and item == self.pctl.track_queue[self.pctl.queue_step]:
					pre_state = self.pctl.stop(True)

				try:
					afterline = parse_template2(NRN, self.pctl.master_library[item], strict=True)

					oldname = self.pctl.master_library[item].filename
					oldpath = self.pctl.master_library[item].fullpath

					logging.info("Renaming...")

					star = self.star_store.full_get(item)
					star_key = self.star_store.key(item)

					oldpath = self.pctl.master_library[item].fullpath

					oldsplit = os.path.split(oldpath)

					if os.path.exists(os.path.join(oldsplit[0], afterline)):
						logging.error("A file with that name already exists")
						total_todo -= 1
						continue

					if not afterline:
						logging.error("Rename Error")
						total_todo -= 1
						continue

					if "." in afterline and not afterline.split(".")[0]:
						logging.error("A file does not have a target filename")
						total_todo -= 1
						continue

					os.rename(self.pctl.master_library[item].fullpath, os.path.join(oldsplit[0], afterline))

					self.pctl.master_library[item].fullpath = os.path.join(oldsplit[0], afterline)
					self.pctl.master_library[item].filename = afterline

					self.tauon.search_string_cache.pop(item, None)
					self.tauon.search_dia_string_cache.pop(item, None)
					self.tauon.search_field_cache.pop(item, None)
					self.tauon.search_dia_field_cache.pop(item, None)

					if star is not None:
						self.star_store.db.pop(star_key, None)
						self.star_store.insert(item, star)

				except Exception:
					logging.exception("Rendering error")
					total_todo -= 1

			self.tauon.rename_track_box.active = False
			logging.info("Done")
			if pre_state == 1:
				self.pctl.revert()

			if total_todo != len(r_todo):
				self.show_message(
					_("Rename complete."),
					_("{N} / {T} filenames were written.")
					.format(N=str(total_todo), T=str(len(r_todo))), mode="warning")
			else:
				self.show_message(
					_("Rename complete."),
					_("{N} / {T} filenames were written.")
					.format(N=str(total_todo), T=str(len(r_todo))), mode="done")
			self.pctl.notify_database_changed()
class SearchOverlay:


	def __init__(self, tauon: _OverlayApp) -> None:
		self.tauon:    _OverlayApp = tauon
		self.ddt:      TDraw = tauon.ddt
		self.gui:     GuiVar = tauon.gui
		self.inp:      Input = tauon.inp
		self.coll            = tauon.coll
		self.pctl: Any = tauon.pctl
		self.prefs:    Prefs = tauon.prefs
		self.fields:  Fields = tauon.fields
		self.window_size: list[int] = tauon.window_size
		self.worker2_lock  = tauon.worker2_lock
		self.show_message  = tauon.show_message
		self.smooth_scroll: Any = tauon.smooth_scroll

		self.active: bool = False
		self.search_text: TextBox = TextBox(tauon)

		self.results: list[tuple[int, list[int | str | None]]] = []
		self.searched_text: str = ""
		self.on: int = 0
		self.force_select: int = -1
		self.old_mouse = [0, 0]
		self.sip: bool = False
		self.delay_enter: bool = False
		self.last_animate_time: float = 0
		self.animate_timer: Timer = Timer(100)
		self.input_timer: Timer = Timer(100)
		self.all_folders: bool = False

	def clear(self) -> None:
		self.search_text.text = ""
		self.results.clear()
		self.searched_text = ""
		self.on = 0
		self.all_folders = False

	def click_artist(self, name: str, get_list: bool = False, search_lists: list[list[int]] | None = None) -> list[int] | None:
		playlist: list[int] = []

		if search_lists is None:
			search_lists = []
			for pl in self.pctl.multi_playlist:
				search_lists.append(pl.playlist_ids)

		for pl in search_lists:
			for item in pl:
				tr = self.pctl.master_library[item]
				n = name.lower()
				if tr.artist.lower() == n \
						or tr.album_artist.lower() == n \
						or (tr.artists is not None and name in tr.artists):
					if item not in playlist:
						playlist.append(item)

		if get_list:
			return playlist

		self.pctl.multi_playlist.append(self.tauon.pl_gen(
			title=_("Artist: ") + name,
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))

		if self.gui.combo_mode:
			self.tauon.exit_combo()
		self.pctl.switch_playlist(len(self.pctl.multi_playlist) - 1)
		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "a\"" + name + "\""

		self.inp.key_return_press = False
		return None

	def click_year(self, name, get_list: bool = False) -> list[int] | None:
		playlist: list [int] = []
		for pl in self.pctl.multi_playlist:
			for item in pl.playlist_ids:
				if name in self.pctl.master_library[item].date and item not in playlist:
					playlist.append(item)

		if get_list:
			return playlist

		self.pctl.multi_playlist.append(self.tauon.pl_gen(
			title=_("Year: ") + name,
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))

		if self.gui.combo_mode:
			self.tauon.exit_combo()

		self.pctl.switch_playlist(len(self.pctl.multi_playlist) - 1)
		self.inp.key_return_press = False
		return None

	def click_composer(self, name: str, get_list: bool = False) -> list[int] | None:
		playlist: list[int] = []
		for pl in self.pctl.multi_playlist:
			for item in pl.playlist_ids:
				if self.pctl.master_library[item].composer.lower() == name.lower():
					if item not in playlist:
						playlist.append(item)

		if get_list:
			return playlist

		self.pctl.multi_playlist.append(self.tauon.pl_gen(
			title=_("Composer: ") + name,
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))

		if self.gui.combo_mode:
			self.tauon.exit_combo()

		self.pctl.switch_playlist(len(self.pctl.multi_playlist) - 1)

		self.inp.key_return_press = False
		return None

	def click_meta(self, name: str, get_list: bool = False, search_lists: list[list[int]] | None = None) -> list[int] | None:
		if search_lists is None:
			search_lists = []
			for pl in self.pctl.multi_playlist:
				search_lists.append(pl.playlist_ids)

		playlist: list[int] = []
		for pl in search_lists:
			for item in pl:
				if name in self.pctl.master_library[item].parent_folder_path and item not in playlist:
					playlist.append(item)

		if get_list:
			return playlist

		self.pctl.multi_playlist.append(self.tauon.pl_gen(
			title=os.path.basename(name).upper(),
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))

		if self.gui.combo_mode:
			self.tauon.exit_combo()

		self.pctl.switch_playlist(len(self.pctl.multi_playlist) - 1)

		self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "p\"" + name + "\""

		self.inp.key_return_press = False
		return None

	def click_genre(self, name: str, get_list: bool = False, search_lists: list[list[int]] | None = None) -> list[int] | None:
		playlist: list[int] = []

		if search_lists is None:
			search_lists = []
			for pl in self.pctl.multi_playlist:
				search_lists.append(pl.playlist_ids)

		include_multi = False
		if name.endswith("+") or not self.prefs.sep_genre_multi:
			name = name.rstrip("+")
			include_multi = True

		for pl in search_lists:
			for item in pl:
				track = self.pctl.master_library[item]
				if track.genre.lower().replace("-", "").replace(" ", "") == name.lower().replace("-", "").replace(" ", ""):
					if item not in playlist:
						playlist.append(item)
				elif include_multi and ("/" in track.genre or "," in track.genre or ";" in track.genre):
					for split in track.genre.replace(",", "/").replace(";", "/").split("/"):
						split = split.strip()
						if name.lower().replace("-", "").replace(" ", "") == split.lower().replace("-", "").replace(" ", ""):
							if item not in playlist:
								playlist.append(item)

		if get_list:
			return playlist

		self.pctl.multi_playlist.append(self.tauon.pl_gen(
			title=_("Genre: ") + name,
			playlist_ids=copy.deepcopy(playlist),
			hide_title=False))

		if self.gui.combo_mode:
			self.tauon.exit_combo()

		self.pctl.switch_playlist(len(self.pctl.multi_playlist) - 1)

		if include_multi:
			self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "gm\"" + name + "\""
		else:
			self.pctl.gen_codes[self.pctl.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "g=\"" + name + "\""

		self.inp.key_return_press = False
		return None

	def click_album(self, index) -> None:
		self.pctl.jump(index)
		if self.gui.combo_mode:
			self.tauon.exit_combo()

		self.pctl.show_current()
		self.inp.key_return_press = False

	def queue_track_result(self, track_id: int, playlist_id: int) -> None:
		pl = self.pctl.id_to_pl(playlist_id)
		if pl is None:
			return

		playlist = self.pctl.multi_playlist[pl].playlist_ids
		if track_id not in playlist:
			return

		queue_object = queue_item_gen(track_id, playlist.index(track_id), playlist_id)
		self.pctl.force_queue.append(queue_object)
		self.tauon.queue_timer_set(queue_object=queue_object)
		if self.prefs.stop_end_queue:
			self.pctl.stop_mode = StopMode.OFF

	def queue_album_result(self, track_id: int, playlist_id: int) -> None:
		pl = self.pctl.id_to_pl(playlist_id)
		if pl is None:
			return

		playlist = self.pctl.multi_playlist[pl].playlist_ids
		if track_id not in playlist:
			return

		self.tauon.add_album_to_queue(track_id, playlist.index(track_id), playlist_id)

	def tracks_for_result(self, item: list[int | str | None]) -> list[int]:
		n = item[0]
		match n:
			case 0:
				if isinstance(item[1], str):
					return self.click_artist(item[1], get_list=True) or []
			case 1:
				if isinstance(item[2], int):
					for k, pl in enumerate(self.pctl.multi_playlist):
						if item[2] in pl.playlist_ids:
							return self.tauon.get_album_from_first_track(pl.playlist_ids.index(item[2]), item[2], k)
			case 2:
				if isinstance(item[2], int):
					return [item[2]]
			case 3:
				if isinstance(item[1], str):
					return self.click_genre(item[1], get_list=True) or []
			case 5:
				if isinstance(item[1], str):
					return self.click_meta(item[1], get_list=True) or []
			case 6:
				if isinstance(item[1], str):
					return self.click_composer(item[1], get_list=True) or []
			case 7:
				if isinstance(item[1], str):
					return self.click_year(item[1], get_list=True) or []
			case 8:
				if isinstance(item[3], int):
					pl = self.pctl.id_to_pl(item[3])
					if pl is not None:
						return list(self.pctl.multi_playlist[pl].playlist_ids)
		return []

	def toast_playlist_add(self, added_count: int) -> None:
		playlist_name = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].title
		if added_count == 1:
			text = _("Added 1 track to playlist: {name}").format(name=playlist_name)
		else:
			text = _("Added {N} tracks to playlist: {name}").format(N=added_count, name=playlist_name)
		self.tauon.toast(text, duration=2.5)

	def render_help_legend(self) -> None:
		gui = self.gui
		icon_size = round(26 * gui.scale)
		margin = round(18 * gui.scale)
		icon_rect = (
			self.window_size[0] - margin - icon_size,
			self.window_size[1] - margin - icon_size,
			icon_size,
			icon_size,
		)
		self.fields.add(icon_rect)

		hover = self.coll(icon_rect)
		icon_text = ColourRGBA(210, 210, 215, 105)
		if hover:
			icon_text = ColourRGBA(245, 245, 245, 230)

		cx = icon_rect[0] + icon_size // 2
		self.ddt.text(
			(cx, icon_rect[1] + round(3 * gui.scale), 2),
			"?",
			icon_text,
			214,
		)

		if not hover:
			return

		lines = [
			(_("Go / open:"), _("left-click or press Enter.")),
			(_("Show / reveal:"), _("right-click or press Shift+Enter.")),
			(_("Add to current playlist:"), _("Ctrl+left-click.")),
			(_("Add to queue:"), _("middle-click (track or album).")),
		]
		font = 13
		label_font = 213
		pad = round(12 * gui.scale)
		label_gap = round(5 * gui.scale)
		line_h = round(22 * gui.scale)
		width = max(
			self.ddt.get_text_w(label, label_font) + label_gap + self.ddt.get_text_w(text, font)
			for label, text in lines
		) + pad * 2
		height = line_h * len(lines) + pad * 2
		tooltip_x = max(margin, self.window_size[0] - margin - width)
		tooltip_y = max(margin, icon_rect[1] - height - round(10 * gui.scale))
		tooltip_bg = ColourRGBA(18, 18, 22, 245)

		self.ddt.rect((tooltip_x, tooltip_y, width, height), tooltip_bg)
		for i, (label, text) in enumerate(lines):
			line_x = tooltip_x + pad
			line_y = tooltip_y + pad + i * line_h
			label_width = self.ddt.text(
				(line_x, line_y),
				label,
				ColourRGBA(245, 245, 245, 255),
				label_font,
				bg=tooltip_bg,
			)
			self.ddt.text(
				(line_x + label_width + label_gap, line_y),
				text,
				ColourRGBA(245, 245, 245, 255),
				font,
				bg=tooltip_bg,
			)

	def render(self) -> None:
		prefs = self.prefs
		inp   = self.inp
		gui   = self.gui
		control_down = inp.key_ctrl_down or inp.key_rctrl_down

		if self.active is False:
			# Activate search overlay on key presses
			if prefs.search_on_letter and inp.input_text and gui.layer_focus == 0 and \
					not inp.key_lalt and not inp.key_ralt and \
					not control_down and not self.tauon.radiobox.active and not self.tauon.rename_track_box.active and \
					not gui.quick_search_mode and not self.tauon.pref_box.enabled and not gui.rename_playlist_box \
					and not gui.rename_folder_box and inp.input_text.isalnum() and not gui.box_over \
					and not self.tauon.trans_edit_box.active and not gui.timed_lyrics_editing_now:

				# Divert to artist list if mouse over
				if gui.lsp and prefs.left_panel_mode == "artist list" and gui.lsp_x + 2 < inp.mouse_position[0] < gui.lsp_x + gui.lspw \
						and gui.panelY < inp.mouse_position[1] < self.window_size[1] - gui.panelBY:
					self.tauon.artist_list_box.locate_artist_letter(inp.input_text)
					return

				self.tauon.activate_search_overlay()
				self.old_mouse = copy.deepcopy(inp.mouse_position)

		if self.active:
			x = 0
			y = 0
			w = self.window_size[0]
			h = self.window_size[1]

			if gui.keymaps.test("add-to-queue"):
				inp.input_text = ""

			if inp.backspace_press:
				# self.searched_text = ""
				# self.results.clear()

				if len(self.search_text.text) - inp.backspace_press < 1:
					self.active = False
					self.search_text.text = ""
					self.results.clear()
					self.searched_text = ""
					return

			if inp.key_esc_press:
				if self.delay_enter:
					self.delay_enter = False
				else:
					self.active = False
					self.search_text.text = ""
					self.results.clear()
					self.searched_text = ""
					return

			if gui.level_2_click and inp.mouse_position[0] > 350 * gui.scale:
				self.active = False
				self.search_text.text = ""

			mouse_change = False
			if not point_proximity_test(self.old_mouse, inp.mouse_position, 25):
				mouse_change = True
			# mouse_change = True

			overlay_background = ColourRGBA(12, 12, 12, 255)
			track_in_bar_colour = ColourRGBA(244, 209, 66, 255)
			self.ddt.rect((x, y, w, h), ColourRGBA(3, 3, 3, 235))
			if control_down:
				badge_margin = round(14 * gui.scale) + 5
				badge_pad = round(5 * gui.scale)
				badge_h = round(20 * gui.scale)
				badge_text_y = round(18 * gui.scale)
				icon_size = round(8 * gui.scale)
				icon_thickness = max(round(2 * gui.scale), 1)
				icon_gap = round(5 * gui.scale)
				badge_text = self.pctl.multi_playlist[self.pctl.active_playlist_viewing].title
				max_badge_w = max(round(120 * gui.scale), self.window_size[0] - badge_margin * 2)
				badge_w = min(
					icon_size + icon_gap + self.ddt.get_text_w(badge_text, 312) + badge_pad * 2,
					max_badge_w,
				)
				badge_rect = (self.window_size[0] - badge_margin - badge_w, badge_margin, badge_w, badge_h)
				self.ddt.rect(badge_rect, track_in_bar_colour)
				icon_x = badge_rect[0] + badge_pad
				icon_y = badge_rect[1] + (badge_h - icon_size) // 2
				self.ddt.rect(
					(icon_x, icon_y + (icon_size - icon_thickness) // 2, icon_size, icon_thickness),
					overlay_background,
				)
				self.ddt.rect(
					(icon_x + (icon_size - icon_thickness) // 2, icon_y, icon_thickness, icon_size),
					overlay_background,
				)
				self.ddt.text_background_colour = track_in_bar_colour
				self.ddt.text(
					(icon_x + icon_size + icon_gap, badge_text_y),
					badge_text,
					overlay_background,
					312,
					max_w=badge_rect[2] - badge_pad * 2 - icon_size - icon_gap,
					bg=track_in_bar_colour,
				)
			self.ddt.text_background_colour = overlay_background


			input_text_x = 80 * gui.scale
			highlight_x = 30 * gui.scale
			thumbnail_rx = 100 * gui.scale
			text_lx = 120 * gui.scale

			s_font = 15
			s_b_font = 214
			b_font = 215

			if self.window_size[0] < 400 * gui.scale:
				input_text_x = 30 * gui.scale
				highlight_x = 4 * gui.scale
				thumbnail_rx = 65 * gui.scale
				text_lx = 80 * gui.scale
				s_font = 415
				s_b_font = 514
				d_font = 515

			#album_art_size_s = 0 * gui.scale

			# Search active animation
			if self.sip:
				x = round(15 * gui.scale)
				y = x
				s = round(7 * gui.scale)
				g = round(4 * gui.scale)

				t = self.animate_timer.get()
				if abs(t - self.last_animate_time) > 0.3:
					self.animate_timer.set()
					t = 0

				self.last_animate_time = t

				for item in range(4):
					a = 100
					if round(t * 14) % 4 == item:
						a = 255
					colour = ColourRGBA(140, 100, 255, a)

					self.ddt.rect((x, y, s, s), colour)
					x += g + s

				gui.request_frame()

			# No results found message
			elif not self.results and len(self.search_text.text) > 1:
				if self.input_timer.get() > 0.5 and not self.sip:
					self.ddt.text((self.window_size[0] // 2, 200 * gui.scale, 2), _("No results found"), ColourRGBA(250, 250, 250, 255), 216,
						bg=ColourRGBA(12, 12, 12, 255))

			self.search_text.draw(input_text_x, 60 * gui.scale, ColourRGBA(230, 230, 230, 255), True, False, 30,
				self.window_size[0] - 100, big=True, click=gui.level_2_click, selection_height=30)

			if inp.input_text or inp.key_backspace_press:
				self.input_timer.set()

				gui.request_frame()
			elif self.input_timer.get() >= 0.20 and \
					(len(self.search_text.text) > 1 or (len(self.search_text.text) == 1 and ord(self.search_text.text) > 128)) \
					and self.search_text.text != self.searched_text:
				self.sip = True
				if self.worker2_lock.locked():
					try:
						self.worker2_lock.release()
					except RuntimeError as e:
						if str(e) == "release unlocked lock":
							logging.error("RuntimeError: Attempted to release already unlocked worker2_lock")  # noqa: TRY400
						else:
							logging.exception("Unknown RuntimeError trying to release worker2_lock")
					except Exception:
						logging.exception("Unknown error trying to release worker2_lock")

			if self.input_timer.get() < 10:
				gui.frame_callback_list.append(TestTimer(0.1))

			yy = 110 * gui.scale

			if inp.key_down_press:
				self.force_select += 1
				if self.force_select > 4:
					self.on = self.force_select - 4
				self.force_select = min(self.force_select, len(self.results) - 1)
				self.old_mouse = copy.deepcopy(inp.mouse_position)

			if inp.key_up_press:
				if self.force_select > -1:
					self.force_select -= 1
					self.force_select = max(self.force_select, 0)

					if self.force_select < self.on + 4:
						self.on = self.force_select - 4
						self.on = max(self.on, 0)

				self.old_mouse = copy.deepcopy(inp.mouse_position)

			scroll_distance = self.smooth_scroll.scroll("search overlay")
			self.on = max( (self.on - scroll_distance), 0)
			self.force_select = max( (self.force_select - scroll_distance), 0)

			enter = False

			if self.delay_enter and not self.sip and self.search_text.text == self.searched_text:
				enter = True
				self.delay_enter = False
			elif inp.key_return_press:
				if self.results:
					enter = True
					self.delay_enter = False
				elif self.sip or self.input_timer.get() < 0.25:
					self.delay_enter = True
				else:
					enter = True
					self.delay_enter = False

			inp.key_return_press = False

			bar_colour = ColourRGBA(140, 80, 240, 255)

			self.on = max(self.on, 0)
			self.on = min(len(self.results) - 1, self.on)

			full_count = 0

			sec = False

			p = -1

			if self.on > 4:
				p += self.on - 4
			p = self.on - 1
			clear = False

			for i, item in enumerate(self.results):
				p += 1

				if p > len(self.results) - 1:
					break

				item: list[int] = self.results[p]

				fade = 1
				selected = self.on
				if self.force_select > -1:
					selected = self.force_select

				#logging.info(selected)

				if selected != p:
					fade = 0.8

				start = yy

				n = item[0]

				names = {
					0: "Artist",
					1: "Album",
					2: "Track",
					3: "Genre",
					5: "Folder",
					6: "Composer",
					7: "Year",
					8: "Playlist",
					9: "Lyrics",
				}
				type_colours = {
					0:  ColourRGBA(250, 140, 190, 255),  # Artist
					1:  ColourRGBA(250, 140, 190, 255),  # Album
					2:  ColourRGBA(250, 220, 190, 255),  # Track
					3:  ColourRGBA(240, 240, 160, 255),  # Genre
					5:  ColourRGBA(250, 100,  50, 255),   # Folder
					6:  ColourRGBA(180, 250, 190, 255),  # Composer
					7:  ColourRGBA(250, 50,  140, 255),   # Year
					8:  ColourRGBA(100, 210, 250, 255),  # Playlist
					9:  ColourRGBA(250, 220, 190, 255),  # Track from lyrics
				}
				if n not in names:
					name = "NYI"
					colour = ColourRGBA(255, 255, 255, 255)
				else:
					name = names[n]
					colour = type_colours[n]
					colour.a = int(colour.a * fade)

				pad = round(4 * gui.scale)
				height = round(25 * gui.scale)
				if n == 1:
					height = round(50 * gui.scale)
				album_art_size = height


				# Selection bar
				s_rect = (highlight_x, yy, 600 * gui.scale, height + pad + pad - 1)
				self.fields.add(s_rect)
				if fade == 1:
					self.ddt.rect((highlight_x, yy + pad, 4 * gui.scale, height), bar_colour)
				if n in (2,):
					if control_down and item[2] in self.pctl.default_playlist:
						self.ddt.rect((highlight_x + round(5 * gui.scale), yy + pad, 4 * gui.scale, height), track_in_bar_colour)

				# Type text
				if n in (0, 3, 5, 6, 7, 8, 9):
					self.ddt.text((thumbnail_rx, yy + pad + round(3 * gui.scale), 1), names[n], type_colours[n], 214)

				# Thumbnail
				if n in (1, 2):
					thl = thumbnail_rx - album_art_size
					self.ddt.rect((thl, yy + pad, album_art_size, album_art_size), ColourRGBA(50, 50, 50, 150))
					self.tauon.gall_ren.render(self.pctl.get_track(item[2]), (thl, yy + pad), album_art_size)
					if fade != 1:
						self.ddt.rect((thl, yy + pad, album_art_size, album_art_size), ColourRGBA(0, 0, 0, 70))
				# Result text
				if n in (0, 5, 6, 7, 8):  # Bold
					xx = self.ddt.text((text_lx, yy + pad + round(3 * gui.scale)), item[1], ColourRGBA(255, 255, 255, int(255 * fade)), b_font)
				if n in (3,):  # Genre
					xx = self.ddt.text((text_lx, yy + pad + round(3 * gui.scale)), item[1].rstrip("+"), ColourRGBA(255, 255, 255, int(255 * fade)), b_font)
					if item[1].endswith("+"):
						self.ddt.text(
							(xx + text_lx + 13 * gui.scale, yy + pad + round(3 * gui.scale)), _("(Include multi-tag results)"),
							ColourRGBA(255, 255, 255, int(255 * fade) // 2), 313)
				if n in (2,9,):  # Local library track
					track = self.pctl.get_track(item[2])
					title_val = track.title or clean_string(track.filename)
					artist_val = track.artist
					album_val = track.album

					yyy = yy + pad + round(3 * gui.scale)
					text_max_w = max(round(80 * gui.scale), self.window_size[0] - text_lx - round(24 * gui.scale))
					text_max_w = min(round(560 * gui.scale), text_max_w)
					metadata_val = artist_val or album_val
					if metadata_val:
						gap = round(8 * gui.scale)
						by_label = "BY" if artist_val else ""
						by_width = self.ddt.get_text_w(by_label, 212) if by_label else 0
						metadata_width = self.ddt.get_text_w(metadata_val, s_font)
						if by_label:
							metadata_width += by_width + gap
						min_title_width = round(120 * gui.scale)
						if metadata_width + min_title_width + gap > text_max_w:
							metadata_width = max(round(70 * gui.scale), text_max_w - min_title_width - gap)
						title_width = max(round(40 * gui.scale), text_max_w - metadata_width - gap)
						drawn_title_width = self.ddt.text(
							(text_lx, yyy),
							title_val,
							ColourRGBA(255, 255, 255, int(255 * fade)),
							s_b_font,
							max_w=title_width,
						) or 0
						meta_x = text_lx + drawn_title_width + gap
						if by_label:
							self.ddt.text((meta_x, yyy), by_label, ColourRGBA(250, 240, 110, int(255 * fade)), 212)
							meta_x += by_width + gap
						self.ddt.text(
							(meta_x, yyy),
							metadata_val,
							ColourRGBA(250, 250, 250, int(255 * fade)) if artist_val else ColourRGBA(220, 220, 220, int(255 * fade)),
							s_font,
							max_w=max(round(1 * gui.scale), text_max_w - (meta_x - text_lx)),
						)
					else:
						self.ddt.text(
							(text_lx, yyy),
							title_val,
							ColourRGBA(255, 255, 255, int(255 * fade)),
							s_b_font,
							max_w=text_max_w,
						)

				if n in (1,):  # Two line album
					track = self.pctl.master_library[item[2]]
					artist = track.album_artist
					if not artist:
						artist = track.artist

					xx = self.ddt.text((text_lx, yy + pad + round(5 * gui.scale)), item[1], ColourRGBA(255, 255, 255, int(255 * fade)), s_b_font)

					self.ddt.text((text_lx + 5 * gui.scale, yy + 30 * gui.scale), "BY", ColourRGBA(250, 240, 110, int(255 * fade)), 212)
					xx += 8 * gui.scale
					xx += self.ddt.text((text_lx + 30 * gui.scale, yy + 30 * gui.scale), artist, ColourRGBA(250, 250, 250, int(255 * fade)), s_font)

				yy += height + pad + pad

				show = False
				go = False
				extend = False
				queue_result = False
				if self.coll(s_rect) and mouse_change:
					if self.force_select != p:
						self.force_select = p
						gui.request_frame()

					if gui.level_2_click:
						if control_down:
							extend = True
						else:
							go = True
							clear = True

					if inp.level_2_right_click:
						show = True
						clear = True

					if inp.middle_click and n in (1, 2, 9):
						queue_result = True
						inp.middle_click = False

				if enter and inp.key_shift_down and fade == 1:
					show = True
					clear = True

				elif enter and fade == 1:
					if inp.key_shift_down or inp.key_shiftr_down:
						show = True
						clear = True
					else:
						go = True
						clear = True

				if queue_result:
					match n:
						case 1:
							self.queue_album_result(item[2], item[3])
						case 2:
							self.queue_track_result(item[2], item[3])
						case 9:
							self.queue_track_result(item[2], item[3])
				elif extend:
					tracks = self.tracks_for_result(item)
					if tracks:
						self.pctl.default_playlist.extend(tracks)
						self.tauon.reload_albums(True)
						self.pctl.notify_database_changed()
						self.toast_playlist_add(len(tracks))
				elif show:
					match n:
						case 0 | 1 | 2 | 3 | 5 | 6 | 7 | 9:
							self.pctl.show_current(index=item[2], playing=False)

						case 8:
							pl = self.pctl.id_to_pl(item[3])
							if pl is not None:
								self.pctl.switch_playlist(pl)
				elif go:
					match n:
						case 0:
							self.click_artist(item[1])
						case 1 | 2 | 9:
							self.click_album(item[2])
							self.pctl.show_current(index=item[2])
							self.pctl.playlist_view_position = self.pctl.selected_in_playlist
						case 3:
							self.click_genre(item[1])
						case 5:
							self.click_meta(item[1])
						case 6:
							self.click_composer(item[1])
						case 7:
							self.click_year(item[1])
						case 8:
							pl = self.pctl.id_to_pl(item[3])
							if pl is not None:
								self.pctl.switch_playlist(pl)
				if n in (2,9,) and gui.keymaps.test("add-to-queue") and fade == 1:
					self.queue_track_result(item[2], item[3])

				# ----

				# ---
				if i > 40:
					break
				if yy > self.window_size[1] - (100 * gui.scale):
					break

				continue

			if clear:
				self.active = False
				self.search_text.text = ""
				self.results.clear()
				self.searched_text = ""

			if self.active:
				self.render_help_legend()
