"""Playback controller and player-side task helpers."""

from __future__ import annotations

import copy
import json
import logging
import os
import random
import re
import threading
import time
from ctypes import CDLL
from pathlib import Path
from typing import Any, Literal, Protocol

import requests
import sdl3

from tauon.t_modules.t_enums import GuiMode, MiniModeMode, PlayingState, QueueType, StopMode
from tauon.t_modules.t_extra import (
	Timer,
	clean_string,
	filename_safe,
	reduce_paths,
	shooter,
	sleep_timeout,
	tryint,
)
from tauon.t_modules.t_input import copy_to_clipboard
from tauon.t_modules.t_menu import close_all_menus
from tauon.t_modules.t_models import (
	LoadClass,
	RadioPlaylist,
	TauonPlaylist,
	TauonQueueItem,
	TrackClass,
	uid_gen,
)
from tauon.t_modules.t_panels import ArtistInfoBox, RadioBox
from tauon.t_modules.t_playlist import ArtistList, QueueBox, TreeView
from tauon.t_modules.t_prefs import Prefs
from tauon.t_modules.t_scrobble import LastFMapi, LastScrob
from tauon.t_modules.t_stars import StarStore
from tauon.t_modules.t_state import ColoursClass, GuiVar, Input
from tauon.t_modules.t_widgets import Drawing, ScrollBox


class _PlayerBag(Protocol):
	prefs: Prefs

	def __getattr__(self, name: str) -> Any: ...


class _PlayerApp(Protocol):
	bag: _PlayerBag
	inp: Input
	gui: GuiVar
	colours: ColoursClass
	prefs: Prefs

	def __getattr__(self, name: str) -> Any: ...


class WinTask:
	def __init__(self, tauon: _PlayerApp, pctl: PlayerCtl) -> None:
		self.pctl: PlayerCtl = pctl
		self.prefs: Prefs = tauon.prefs
		self.tauon: _PlayerApp = tauon
		self.start: float = time.time()
		self.updated_state = 0

	def update(self) -> None:

		# URL streams have no known duration, so show no progress for them either
		if self.pctl.playing_state in (PlayingState.STOPPED, PlayingState.URL_STREAM) and self.updated_state != 0:
			self.updated_state = 0
			sdl3.SDL_SetWindowProgressValue(self.tauon.t_window, 0.0)
			sdl3.SDL_SetWindowProgressState(self.tauon.t_window, sdl3.SDL_PROGRESS_STATE_NONE)

		elif self.prefs.taskbar_progress:

			if self.pctl.playing_state == PlayingState.PLAYING:
				if self.updated_state != 1:
					sdl3.SDL_SetWindowProgressState(self.tauon.t_window, sdl3.SDL_PROGRESS_STATE_NORMAL)

				self.updated_state = 1
				if self.pctl.playing_length > 1.1:
					frac = self.pctl.playing_time / self.pctl.playing_length
				else:
					frac = 0.0

				frac = min(max(frac, 0.0), 1.0)
				sdl3.SDL_SetWindowProgressValue(self.tauon.t_window, frac)

			elif self.pctl.playing_state == PlayingState.PAUSED and self.updated_state != 2:
				self.updated_state = 2
				sdl3.SDL_SetWindowProgressState(self.tauon.t_window, sdl3.SDL_PROGRESS_STATE_PAUSED)


class PlayerCtl:
	"""Main class that controls playback (play, pause, stepping, playlists, queue etc). Sends commands to backend."""

	# C-PC
	def __init__(self, tauon: _PlayerApp) -> None:
		self.tauon: _PlayerApp                     = tauon
		self.inp: Input                       = self.tauon.inp
		self.gui: GuiVar                      = self.tauon.gui
		self.bag: _PlayerBag                         = self.tauon.bag
		self.colours: ColoursClass            = self.tauon.colours
		self.smtc: bool                       = self.tauon.bag.smtc
		self.show_message              = self.tauon.show_message
		self.star_store: StarStore            = StarStore(tauon=tauon, pctl=self)
		self.draw: Drawing                    = Drawing(tauon=tauon, pctl=self)
		self.radiobox: RadioBox               = RadioBox(tauon=tauon, pctl=self)
		self.mini_lyrics_scroll: ScrollBox    = ScrollBox(tauon=tauon, pctl=self)
		self.playlist_panel_scroll: ScrollBox = ScrollBox(tauon=tauon, pctl=self)
		self.artist_info_scroll: ScrollBox    = ScrollBox(tauon=tauon, pctl=self)
		self.device_scroll: ScrollBox         = ScrollBox(tauon=tauon, pctl=self)
		self.artist_list_scroll: ScrollBox    = ScrollBox(tauon=tauon, pctl=self)
		self.gallery_scroll: ScrollBox        = ScrollBox(tauon=tauon, pctl=self)
		self.tree_view_scroll: ScrollBox      = ScrollBox(tauon=tauon, pctl=self)
		self.radio_view_scroll: ScrollBox     = ScrollBox(tauon=tauon, pctl=self)
		self.tree_view_box: TreeView          = TreeView(tauon=tauon, pctl=self)
		self.windows: bool                       = self.tauon.windows
		self.queue_box: QueueBox              = QueueBox(tauon=tauon, pctl=self)
		self.running:                    bool = True
		self.prefs: Prefs                     = self.bag.prefs
		self.sm: CDLL | None                  = self.bag.sm
		self.lastfm: LastFMapi                = LastFMapi(tauon=tauon, pctl=self, copy_to_clipboard_fn=copy_to_clipboard)
		self.lfm_scrobbler: LastScrob         = LastScrob(tauon=tauon, pctl=self)
		self.artist_info_box: ArtistInfoBox   = ArtistInfoBox(tauon=tauon, pctl=self)
		self.artist_list_box: ArtistList      = ArtistList(tauon=tauon, pctl=self)
		self.install_directory: Path          = self.bag.dirs.install_directory
		self.loading_in_progress:        bool = False
		self.album_dex: list[int]                 = self.tauon.album_dex

		self.cargo: list[int]          = []
		# Database

		self.master_count: int = self.bag.master_count
		self.total_playtime: float = 0
		self.master_library: dict[int, TrackClass] = self.bag.master_library
		# Lets clients know when to invalidate cache
		self.db_inc: int = random.randint(0, 10000)
		# self.star_library = star_library
		self.LoadClass = LoadClass

		self.gen_codes: dict[int, str] = self.bag.gen_codes

		self.shuffle_pools: dict[int, list[int]] = {}
		self.after_import_flag = False
		self.quick_add_target = None

		self.album_mbid_release_cache = {}
		self.album_mbid_release_group_cache = {}
		self.mbid_image_url_cache = {}

		# ----------------------------------------
		# Misc player control

		self.url: str = ""
		# self.save_urls = url_saves
		self.tag_meta: str = ""
		self.found_tags: dict[str, str] = {}
		#self.encoder_pause = 0

		# Playback

		self.track_queue: list[int] = self.bag.track_queue
		self.default_playlist: list[int] = []
		self.queue_step: int = self.bag.playing_in_queue
		self.playing_time: float = 0
		self.last_real_position: float = 0
		self.playlist_playing_position: int = self.bag.playlist_playing  # track in playlist that is playing
		if self.playlist_playing_position is None:
			self.playlist_playing_position = -1
		self.playlist_view_position: int = self.bag.playlist_view_position
		self.selected_in_playlist: int = self.bag.selected_in_playlist
		self.target_open: str = ""
		self.target_object: TrackClass | None = None
		self.start_time = 0
		self.b_start_time = 0
		self.playerCommand: str = ""
		self.playerSubCommand: str = ""
		self.playerCommandReady: bool = False
		self.playing_state: PlayingState = PlayingState.STOPPED
		self.playing_length: float = 0
		self.jump_time:      float = 0.0
		self.random_mode:        bool = self.prefs.random_mode
		self.repeat_mode:        bool = self.prefs.repeat_mode
		self.album_repeat_mode:  bool = self.prefs.album_repeat_mode
		self.album_shuffle_mode: bool = self.prefs.album_shuffle_mode
		# self.album_shuffle_pool = []
		# self.album_shuffle_id = ""
		self.last_playing_time: float = 0
		self.multi_playlist: list[TauonPlaylist] = self.bag.multi_playlist
		self.active_playlist_viewing: int = self.bag.active_playlist_viewing  # the playlist index that is being viewed
		self.active_playlist_playing: int = self.bag.active_playlist_playing  # the playlist index that is playing from
		self.force_queue: list[TauonQueueItem] = self.bag.p_force_queue
		self.pause_queue: bool = False
		self.left_time: float = 0
		self.left_index: int = 0
		self.player_volume: float = self.bag.volume
		self.volume_store: float = 50  # Used to save the previous volume when muted
		self.new_time: float = 0
		#self.time_to_get = []
		self.a_time: float = 0
		self.b_time: float = 0
		# self.playlist_backup = []
		self.active_replaygain: float = 0
		self.active_replaygain_gain_db: float = 0
		self.replaygain_applied: bool = False
		self.output_compression_enabled: bool = False
		self.output_compression_active: bool = False
		self.output_compression_reduction_db: float = 0
		self.stop_mode: StopMode = StopMode.OFF
		self.stop_ref: tuple[str, str] | None = None

		self.record_stream: bool = False
		self.record_title: str = ""

		#self.gst_devices = []  # Display names
		#self.gst_outputs = {}  # Display name : (sink, device)
		self.mpris: Any | None = None
		self.tray_update = None
		self.eq = [0] * 2  # not used
		self.enable_eq = True  # not used

		self.playing_time_int = 0  # playing time but with no decimel
		self.ab_repeat_a: float = -1.0
		self.ab_repeat_b: float = -1.0

		self.windows_progress = WinTask(tauon, self)

		self.finish_transition = False
		# self.queue_target = 0
		self.start_time_target = 0

		self.decode_time = 0
		self.download_time = 0

		self.radio_meta_on = ""

		self.radio_scrobble_trip = True
		self.radio_scrobble_timer = Timer()

		self.radio_image_bin = None
		self.radio_rate_timer = Timer(2)
		self.radio_poll_timer = Timer(2)

		self.volume_update_timer = Timer()
		self.wake_past_time = 0

		self.regen_in_progress = False
		self.notify_in_progress = False
		self.mac_nowplaying_art_generation = 0
		self.mac_nowplaying_art_track_index = -1
		self.mac_nowplaying_art_path = ""
		self.mac_nowplaying_art_ready = False

		self.radio_playlists = self.bag.radio_playlists
		self.radio_playlist_viewing = self.bag.radio_playlist_viewing
		self.tag_history: dict[str, dict[str, str]] = {}

		self.commit: int | None = None

		self.buffering_percent = 0

	# def re_import(pl: int) -> None:
	#
	#	 path = pctl.multi_playlist[pl].last_folder
	#	 if path == "":
	#		 return
	#	 for i in reversed(range(len(pctl.multi_playlist[pl].playlist_ids))):
	#		 if path.replace('\\', '/') in pctl.master_library[pctl.multi_playlist[pl].playlist_ids[i]].parent_folder_path:
	#			 del pctl.multi_playlist[pl].playlist_ids[i]
	#
	#	 load_order = LoadClass()
	#	 load_order.replace_stem = True
	#	 load_order.target = path
	#	 load_order.playlist = pctl.multi_playlist[pl].uuid_int
	#	 tauon.load_orders.append(copy.deepcopy(load_order))

	def resolve_full_playlist_path(self, playlist: TauonPlaylist, get_name: bool = False) -> str:

		target = playlist.playlist_file
		if target.endswith(("/", "\\")):
			name = filename_safe(playlist.title)
			if not name:
				name = str(playlist.uuid_int)
			target += name
			if playlist.export_type == "xspf":
				target += ".xspf"
			if playlist.export_type == "m3u":
				target += ".m3u"
		if get_name:
			path = Path(target)
			return path.name
		return target


	def index_key(self, index: int) -> (list[int | str] | Literal["a"]):
		tr = self.master_library[index]
		s = str(tr.track_number)
		d = str(tr.disc_number)

		if "/" in d:
			d = d.split("/", maxsplit=1)[0]

		# Make sure the value for disc number is an int, make 1 if 0, otherwise ignore
		if d:
			try:
				dd = int(d)
				if dd < 2:
					dd = 1
				d = str(dd)
			except ValueError:
				logging.debug(f"Failed to parse disc_number '{tr.disc_number}' as int, using an empty string instead")
				d = ""
			except Exception:
				logging.exception(f"Unknown exception parsing disc_number '{tr.disc_number}' as int")
				d = ""


		# Add the disc number for sorting by CD, make it '1' if there isn't one
		if s or d:
			s = f"1d{s}" if not d else f"{d}d{s}"
		# Use the filename if we dont have any metadata to sort by,
		# since it could likely have the track number in it
		else:
			s = tr.filename

		if (not tr.disc_number or tr.disc_number == "0") and tr.is_cue:
			s = tr.filename + "-" + s

		# This splits the line by groups of numbers, causing the sorting algorithm to sort
		# by those numbers. Should work for filenames, even with the disc number in the name
		try:
			return [tryint(c) for c in re.split(r"(\d+)", s)]
		except Exception:
			logging.exception("Failed to parse as int, returning 'a'")
			return "a"

	def re_import2(self, pl: int) -> None:
		paths = self.multi_playlist[pl].last_folder

		reduce_paths(paths)

		for path in paths:
			if os.path.isdir(path):
				load_order = LoadClass()
				load_order.replace_stem = True
				load_order.target = path
				load_order.notify = True
				load_order.playlist = self.multi_playlist[pl].uuid_int
				self.tauon.load_orders.append(copy.deepcopy(load_order))

		if paths:
			self.show_message(_("Rescanning folders..."), mode="info")

	def rescan_all_folders(self) -> None:
		for i, p in enumerate(self.multi_playlist):
			self.re_import2(i)
		self.tauon.playlist_autoscan = True
		self.tauon.thread_manager.ready("worker")


	def try_reload_playlist_from_file(self, playlist: TauonPlaylist, _warnings: bool = False) -> None:
		"""Reload designated playlist from file if it meets the requirements"""
		if not playlist.auto_import:
			return

		code = self.gen_codes.get(playlist.uuid_int)
		if code and "self" not in code:
			logging.warning(f"Playlist to import has a generator!: {playlist.title}")
			return

		path = Path(self.resolve_full_playlist_path(playlist))
		if not path.exists() or not path.is_file():
			logging.error(f"Playlist file not found: {path}")
			return
		try:
			current_size = path.stat().st_size
		except FileNotFoundError:
			logging.error(f"Playlist file not found: {path}")  # noqa: TRY400
			return
		except Exception:
			logging.exception("Unknown exception!")
			return

		if current_size != playlist.file_size:
			logging.info(f"Reload playlist from changed file: {playlist.title}")
			if playlist.export_type == "m3u":
				p, stations = self.tauon.parse_m3u(str(path))
				playlist.playlist_ids[:] = p[:]

			elif playlist.export_type == "xspf":
				p, stations, _name = self.tauon.parse_xspf(str(path))
				playlist.playlist_ids[:] = p[:]

			playlist.file_size = path.stat().st_size
			if stations:
				self.tauon.add_stations(stations, playlist.title)


	def switch_playlist(self, number: int, cycle: bool = False, quiet: bool = False) -> None:
		# Close any active menus
		# for instance in Menu.instances:
		# 	instance.active = False
		close_all_menus()
		if self.gui.radio_view:
			if cycle:
				self.radio_playlist_viewing += number
			else:
				self.radio_playlist_viewing = number
			if self.radio_playlist_viewing > len(self.radio_playlists) - 1:
				self.radio_playlist_viewing = 0
			return

		self.gui.previous_playlist_id = self.multi_playlist[self.active_playlist_viewing].uuid_int

		self.gui.request_tracklist_redraw()
		self.gui.search_index = 0
		self.gui.column_d_click_on = -1
		self.gui.search_error = False
		if self.gui.quick_search_mode:
			self.gui.force_search = True

		# if pl_follow:
		# 	self.multi_playlist[self.playlist_active][1] = copy.deepcopy(self.playlist_playing)

		if self.gui.showcase_mode and self.gui.combo_mode and not quiet:
			self.tauon.view_standard()

		self.multi_playlist[self.active_playlist_viewing].playlist_ids = self.default_playlist
		self.multi_playlist[self.active_playlist_viewing].position = self.playlist_view_position
		self.multi_playlist[self.active_playlist_viewing].selected = self.selected_in_playlist

		if self.tauon.gall_pl_switch_timer.get() > 240:
			self.gui.gallery_positions.clear()
		self.tauon.gall_pl_switch_timer.set()

		self.gui.gallery_positions[self.gui.previous_playlist_id] = self.gui.album_scroll_px

		if cycle:
			self.active_playlist_viewing += number
		else:
			self.active_playlist_viewing = number

		while self.active_playlist_viewing > len(self.multi_playlist) - 1:
			self.active_playlist_viewing -= len(self.multi_playlist)
		while self.active_playlist_viewing < 0:
			self.active_playlist_viewing += len(self.multi_playlist)

		id = self.multi_playlist[self.active_playlist_viewing].uuid_int

		if self.prefs.always_auto_update_playlists:
			self.try_reload_playlist_from_file(self.multi_playlist[self.active_playlist_viewing], True)
		self.render_playlist()

		self.default_playlist = self.multi_playlist[self.active_playlist_viewing].playlist_ids
		self.playlist_view_position = self.multi_playlist[self.active_playlist_viewing].position
		self.selected_in_playlist = self.multi_playlist[self.active_playlist_viewing].selected
		logging.debug("Position changed by playlist change")
		self.gui.shift_selection = [self.selected_in_playlist]

		code = self.gen_codes.get(id)
		if code is not None and self.tauon.check_auto_update_okay(code, self.active_playlist_viewing):
			self.gui.regen_single_id = id
			self.tauon.thread_manager.ready("worker")

		if self.prefs.album_mode:
			self.tauon.reload_albums(True)
			if id in self.gui.gallery_positions:
				self.gui.album_scroll_px = self.gui.gallery_positions[id]
			else:
				self.tauon.goto_album(self.playlist_view_position)

		if self.prefs.auto_goto_playing:
			self.show_current(this_only=True, playing=False, highlight=True, no_switch=True)

		if self.prefs.shuffle_lock:
			self.tauon.view_box.lyrics(hit=True)
			if self.active_playlist_viewing is not None:
				self.active_playlist_playing = self.active_playlist_viewing
				self.tauon.random_track()


	def cycle_playlist_pinned(self, step: int) -> None:
		if self.gui.radio_view:
			self.radio_playlist_viewing += step * -1
			if self.radio_playlist_viewing > len(self.radio_playlists) - 1:
				self.radio_playlist_viewing = 0
			if self.radio_playlist_viewing < 0:
				self.radio_playlist_viewing = len(self.radio_playlists) - 1
			return

		if step > 0:
			p = self.active_playlist_viewing
			le = len(self.multi_playlist)
			on = p
			on -= 1
			while True:
				if on < 0:
					on = le - 1
				if on == p:
					break
				if self.multi_playlist[on].hidden is False or not self.prefs.tabs_on_top or (
						self.gui.lsp and self.prefs.left_panel_mode == "playlist"):
					self.switch_playlist(on)
					break
				on -= 1

		elif step < 0:
			p = self.active_playlist_viewing
			le = len(self.multi_playlist)
			on = p
			on += 1
			while True:
				if on == le:
					on = 0
				if on == p:
					break
				if self.multi_playlist[on].hidden is False or not self.prefs.tabs_on_top or (
						self.gui.lsp and self.prefs.left_panel_mode == "playlist"):
					self.switch_playlist(on)
					break
				on += 1

	def move_radio_playlist(self, source: int, dest: int) -> None:
		if dest > source:
			dest += 1
		try:
			temp = self.radio_playlists[source]
			self.radio_playlists[source] = "old"
			self.radio_playlists.insert(dest, temp)
			self.radio_playlists.remove("old")
			self.radio_playlist_viewing = self.radio_playlists.index(temp)
		except Exception:
			logging.exception("Playlist move error")

	def move_playlist(self, source: int, dest: int) -> None:
		if dest > source:
			dest += 1
		try:
			active = self.multi_playlist[self.active_playlist_playing]
			view = self.multi_playlist[self.active_playlist_viewing]

			temp = self.multi_playlist[source]
			self.multi_playlist[source] = "old"
			self.multi_playlist.insert(dest, temp)
			self.multi_playlist.remove("old")

			self.active_playlist_playing = self.multi_playlist.index(active)
			self.active_playlist_viewing = self.multi_playlist.index(view)
			self.default_playlist = self.multi_playlist[self.active_playlist_viewing].playlist_ids
		except Exception:
			logging.exception("Playlist move error")

	def delete_playlist(self, index: int, force: bool = False, check_lock: bool = False) -> None:
		if self.gui.radio_view:
			del self.radio_playlists[index]
			if not self.radio_playlists:
				self.radio_playlists = [RadioPlaylist(uid=uid_gen(),name="Default", stations=[])]
			return

		if check_lock and self.tauon.pl_is_locked(index):
			self.show_message(_("Playlist is locked to prevent accidental deletion"))
			return

		if not force and self.tauon.pl_is_locked(index):
			self.show_message(_("Playlist is locked to prevent accidental deletion"))
			return

		if self.gui.rename_playlist_box:
			return

		# Set screen to be redrawn
		self.gui.request_tracklist_redraw()
		self.gui.request_frame()

		# Backup the playlist to be deleted
		# self.playlist_backup.append(self.multi_playlist[index])
		# self.playlist_backup.append(self.multi_playlist[index])
		self.tauon.undo.bk_playlist(index)

		# If we're deleting the final playlist, delete it and create a blank one in place
		if len(self.multi_playlist) == 1:
			logging.warning("Deleting final playlist and creating a new Default one")
			self.multi_playlist.clear()
			self.multi_playlist.append(self.tauon.pl_gen())
			self.default_playlist = self.multi_playlist[0].playlist_ids
			self.active_playlist_playing = 0
			return

		# Take note of the id of the playing playlist
		old_playing_id = self.multi_playlist[self.active_playlist_playing].uuid_int

		# Take note of the id of the viewed open playlist
		old_view_id = self.multi_playlist[self.active_playlist_viewing].uuid_int

		# Delete the requested playlist
		del self.multi_playlist[index]

		# Re-set the open viewed playlist number by uid
		for i, pl in enumerate(self.multi_playlist):
			if pl.uuid_int == old_view_id:
				self.active_playlist_viewing = i
				break
		else:
			# logging.info("Lost the viewed playlist!")
			# Try find the playing playlist and make it the viewed playlist
			for i, pl in enumerate(self.multi_playlist):
				if pl.uuid_int == old_playing_id:
					self.active_playlist_viewing = i
					break
			else:
				# Playing playlist was deleted, lets just move down one playlist
				if self.active_playlist_viewing > 0:
					self.active_playlist_viewing -= 1

		# Re-initiate the now viewed playlist
		if old_view_id != self.multi_playlist[self.active_playlist_viewing].uuid_int:
			self.default_playlist = self.multi_playlist[self.active_playlist_viewing].playlist_ids
			self.playlist_view_position = self.multi_playlist[self.active_playlist_viewing].position
			logging.debug("Position reset by playlist delete")
			self.selected_in_playlist = self.multi_playlist[self.active_playlist_viewing].selected
			self.gui.shift_selection = [self.selected_in_playlist]

			if self.prefs.album_mode:
				self.tauon.reload_albums(True)
				self.tauon.goto_album(self.playlist_view_position)

		# Re-set the playing playlist number by uid
		for i, pl in enumerate(self.multi_playlist):

			if pl.uuid_int == old_playing_id:
				self.active_playlist_playing = i
				break
		else:
			logging.info("Lost the playing playlist!")
			self.active_playlist_playing = self.active_playlist_viewing
			self.playlist_playing_position = -1

		self.tauon.test_show_add_home_music()

		# Cleanup
		ids: list[int] = []
		for p in self.multi_playlist:
			ids.append(p.uuid_int)

		for key in list(self.gui.gallery_positions.keys()):
			if key not in ids:
				del self.gui.gallery_positions[key]
		for key in list(self.gen_codes.keys()):
			if key not in ids:
				del self.gen_codes[key]

		self.db_inc += 1

	def delete_playlist_force(self, index: int) -> None:
		self.delete_playlist(index, force=True, check_lock=True)

	def delete_playlist_by_id(self, pl_id: int, force: bool = False, check_lock: bool = False) -> None:
		pl = self.id_to_pl(pl_id)
		if pl is None:
			return
		self.delete_playlist(pl, force=force, check_lock=check_lock)

	def delete_playlist_ask(self, index: int) -> None:
		if self.gui.radio_view:
			self.delete_playlist_force(index)
			return
		gen = self.gen_codes.get(self.pl_to_id(index), "")
		if (gen and not gen.startswith("self ")) or len(self.multi_playlist[index].playlist_ids) < 2:
			self.delete_playlist(index)
			return

		self.gui.message_box_confirm_callback = self.delete_playlist_by_id
		self.gui.message_box_no_callback = None
		self.gui.message_box_confirm_reference = (self.pl_to_id(index), True, True)
		self.show_message(_("Are you sure you want to delete playlist: {name}?").format(name=self.multi_playlist[index].title), mode="confirm")

	def id_to_pl(self, pl_id: int) -> int | None:
		for i, item in enumerate(self.multi_playlist):
			if item.uuid_int == pl_id:
				return i
		return None

	def pl_to_id(self, pl: int) -> int:
		return self.multi_playlist[pl].uuid_int

	def notify_database_changed(self) -> None:
		self.db_inc += 1
		self.tauon.bg_save()

	def update_tag_history(self) -> None:
		if self.prefs.auto_rec:
			self.tag_history[self.radiobox.song_key] = {
				"title": self.radiobox.dummy_track.title,
				"artist": self.radiobox.dummy_track.artist,
				"album": self.radiobox.dummy_track.album,
				# "image": self.radio_image_bin
			}

	def radio_progress(self) -> None:
		if self.radiobox.loaded_url and "radio.plaza.one" in self.radiobox.loaded_url and self.radio_poll_timer.get() > 0:
			self.radio_poll_timer.force_set(-10)
			response = requests.get("https://api.plaza.one/status", timeout=10)

			if response.status_code == 200:
				d = json.loads(response.text)
				if "song" in d and "artist" in d["song"] and "title" in d["song"]:
					self.tag_meta = d["song"]["artist"] + " - " + d["song"]["title"]

		if self.tag_meta:
			if self.radio_rate_timer.get() > 7 and self.radio_meta_on != self.tag_meta:
				self.radio_rate_timer.set()
				self.radio_scrobble_trip = False
				self.radio_meta_on = self.tag_meta

				self.radiobox.dummy_track.art_url_key = ""
				self.radiobox.dummy_track.title = ""
				self.radiobox.dummy_track.date = ""
				self.radiobox.dummy_track.artist = ""
				self.radiobox.dummy_track.album = ""
				self.radiobox.dummy_track.lyrics = ""
				self.radiobox.dummy_track.date = ""

				tags = self.found_tags
				if "title" in tags:
					self.radiobox.dummy_track.title = tags["title"]
					if "artist" in tags:
						self.radiobox.dummy_track.artist = tags["artist"]
					if "year" in tags:
						self.radiobox.dummy_track.date = tags["year"]
					if "album" in tags:
						self.radiobox.dummy_track.album = tags["album"]

				elif self.tag_meta.count(
						"-") == 1 and ":" not in self.tag_meta and "advert" not in self.tag_meta.lower():
					artist, title = self.tag_meta.split("-")
					self.radiobox.dummy_track.title = title.strip()
					self.radiobox.dummy_track.artist = artist.strip()

				if self.tag_meta:
					self.radiobox.song_key = self.tag_meta
				else:
					self.radiobox.song_key = self.radiobox.dummy_track.artist + " - " + self.radiobox.dummy_track.title

				self.update_tag_history()
				if self.radiobox.loaded_url not in self.radiobox.websocket_source_urls:
					self.radio_image_bin = None
				logging.info("NEXT RADIO TRACK")

				try:
					self.tauon.get_radio_art()
				except Exception:
					logging.exception("Get art error")

				self.refresh_now_playing(mpris=False)
				if self.mpris:
					self.mpris.update(force=True)

				self.lfm_scrobbler.listen_track(self.radiobox.dummy_track)
				self.lfm_scrobbler.start_queue()

			if self.radio_scrobble_trip is False and self.radio_scrobble_timer.get() > 45:
				self.radio_scrobble_trip = True
				self.lfm_scrobbler.scrob_full_track(copy.deepcopy(self.radiobox.dummy_track))

	def update_shuffle_pool(self, pl_id: int) -> None:
		pl = self.id_to_pl(pl_id)
		if pl is None:
			self.shuffle_pools.pop(pl_id, None)
			return
		new_pool = copy.deepcopy(self.multi_playlist[pl].playlist_ids)
		random.shuffle(new_pool)
		self.shuffle_pools[pl_id] = new_pool
		logging.info("Refill shuffle pool")

	def refresh_now_playing_fire(self, force: bool = False) -> None:
		if self.mpris is not None:
			self.mpris.update(force=force)
		if self.tauon.update_play_lock is not None:
			self.tauon.update_play_lock()
		# if self.tray_update is not None:
		#	 self.tray_update()
		self.notify_in_progress = False

	def update_macos_nowplaying_art_async(self, helper, track_index: int, generation: int) -> None:
		art_path = ""
		try:
			track = self.get_track(track_index)
			art_path = self.tauon.thumb_tracks.path(track) or ""
		except Exception:
			logging.exception("Failed to get thumb path for macOS Now Playing")

		if generation != self.mac_nowplaying_art_generation:
			return

		current_track = self.playing_object()
		if helper is not self.tauon.bag.nowplaying_helper or current_track is None or current_track.index != track_index:
			return

		self.mac_nowplaying_art_track_index = track_index
		self.mac_nowplaying_art_path = art_path
		self.mac_nowplaying_art_ready = True

		state = 0
		if self.playing_state == PlayingState.PLAYING:
			state = 1
		if self.playing_state == PlayingState.PAUSED:
			state = 2

		try:
			helper.update(
				title=current_track.title,
				artist=current_track.artist,
				album=current_track.album,
				art_path=art_path,
				state=state,
				duration=float(self.playing_length),
				elapsed=float(self.playing_time),
			)
		except Exception:
			logging.exception("Failed to update macOS Now Playing helper")

	def refresh_now_playing(self, mpris: bool = True, force: bool = False) -> None:
		self.tauon.tray_releases += 1
		if self.tauon.tray_lock.locked():
			try:
				self.tauon.tray_lock.release()
			except RuntimeError as e:
				if str(e) == "release unlocked lock":
					logging.error("RuntimeError: Attempted to release already unlocked tray_lock")  # noqa: TRY400
				else:
					logging.exception("Unknown RuntimeError trying to release tray_lock")
			except Exception:
				logging.exception("Failed to release tray_lock")

		if mpris and self.smtc:
			tr = self.playing_object()
			if tr:
				state = 0
				if self.playing_state == PlayingState.PLAYING:
					state = 1
				if self.playing_state == PlayingState.PAUSED:
					state = 2
				image_path = ""
				try:
					image_path = self.tauon.thumb_tracks.path(tr)
				except Exception:
					logging.exception("Failed to set image_path from thumb_tracks.path")

				if image_path is None:
					image_path = ""

				image_path = image_path.replace("/", "\\")
				#logging.info(image_path)

				self.sm.update(
					state, tr.title.encode("utf-16"), len(tr.title), tr.artist.encode("utf-16"), len(tr.artist),
					image_path.encode("utf-16"), len(image_path))

		helper = self.tauon.bag.nowplaying_helper
		if helper is not None:
			tr = self.playing_object()
			try:
				if tr:
					state = 0
					if self.playing_state == PlayingState.PLAYING:
						state = 1
					if self.playing_state == PlayingState.PAUSED:
						state = 2

					art_path = self.mac_nowplaying_art_path if tr.index == self.mac_nowplaying_art_track_index else ""
					if tr.index != self.mac_nowplaying_art_track_index:
						self.mac_nowplaying_art_generation += 1
						self.mac_nowplaying_art_track_index = tr.index
						self.mac_nowplaying_art_path = ""
						self.mac_nowplaying_art_ready = False
						shoot = threading.Thread(
							target=self.update_macos_nowplaying_art_async,
							args=(helper, tr.index, self.mac_nowplaying_art_generation),
							daemon=True,
						)
						shoot.start()
					elif self.mac_nowplaying_art_ready:
						helper.update(
							title=tr.title,
							artist=tr.artist,
							album=tr.album,
							art_path=art_path,
							state=state,
							duration=float(self.playing_length),
							elapsed=float(self.playing_time),
						)
				else:
					self.mac_nowplaying_art_generation += 1
					self.mac_nowplaying_art_track_index = -1
					self.mac_nowplaying_art_path = ""
					self.mac_nowplaying_art_ready = False
					helper.clear()
			except Exception:
				logging.exception("Failed to update macOS Now Playing helper")

		if self.mpris is not None and mpris is True:
			while self.notify_in_progress:
				time.sleep(0.01)
			self.notify_in_progress = True
			shoot = threading.Thread(target=self.refresh_now_playing_fire, args=(force,))
			shoot.daemon = True
			shoot.start()
		if self.prefs.art_bg or (self.gui.mode == GuiMode.MINI and self.prefs.mini_mode_mode == MiniModeMode.SLATE):
			self.tauon.thread_manager.ready("style")

		self.windows_progress.update()

	def get_url(self, track_object: TrackClass) -> tuple[list[str] | str | None, dict[str, str] | None]:
		if track_object.file_ext == "TIDAL":
			return self.tauon.tidal.resolve_stream(track_object), None
		if track_object.file_ext == "PLEX":
			return self.tauon.plex.resolve_stream(track_object.url_key), None

		if track_object.file_ext == "JELY":
			return self.tauon.jellyfin.resolve_stream(track_object.url_key)

		if track_object.file_ext == "SUB":
			self.tauon.subsonic.scan_lyrics(track_object)
			return self.tauon.subsonic.resolve_stream(track_object.url_key)

		if track_object.file_ext == "TAU":
			return self.tauon.tau.resolve_stream(track_object.url_key), None

		return None, None

	def playing_playlist(self) -> list[int]:
		return self.multi_playlist[self.active_playlist_playing].playlist_ids

	def playing_ready(self) -> bool:
		return len(self.track_queue) > 0

	def selected_ready(self) -> bool:
		return bool(self.default_playlist) and -1 < self.selected_in_playlist < len(self.default_playlist)

	def render_playlist(self) -> None:
		self.gui.request_tracklist_redraw()

	def show_selected(self) -> int:
		if self.gui.playlist_view_length < 1:
			return 0

		for i in range(len(self.multi_playlist[self.active_playlist_viewing].playlist_ids)):
			if i == self.selected_in_playlist:
				if i < self.playlist_view_position:
					self.playlist_view_position = i - random.randint(2, int((self.gui.playlist_view_length / 3) * 2) + int(self.gui.playlist_view_length / 6))
					logging.debug("Position changed show selected (a)")
				elif abs(self.playlist_view_position - i) > self.gui.playlist_view_length:
					self.playlist_view_position = i
					logging.debug("Position changed show selected (b)")
					if i > 6:
						self.playlist_view_position -= 5
						logging.debug("Position changed show selected (c)")
					if i > self.gui.playlist_view_length * 1 and i + (self.gui.playlist_view_length * 2) < len(
							self.multi_playlist[self.active_playlist_viewing].playlist_ids) and i > 10:
						self.playlist_view_position = i - random.randint(2, int(self.gui.playlist_view_length / 3) * 2)
						logging.debug("Position changed show selected (d)")
					break
		self.render_playlist()
		return 0

	def get_track(self, track_index: int) -> TrackClass:
		"""Get track object by track_index"""
		return self.master_library[track_index]

	def get_track_in_playlist(self, track_index: int, playlist_index: int) -> TrackClass | None:
		"""Get track object by playlist_index and track_index"""
		if playlist_index == -1:
			playlist_index = self.active_playlist_viewing
		try:
			playlist = self.multi_playlist[playlist_index].playlist_ids
			return self.get_track(playlist[track_index])
		except IndexError:
			logging.exception("Failed getting track object by playlist_index and track_index!")
		except Exception:
			logging.exception("Unknown error getting track object by playlist_index and track_index!")
		return None

	def show_object(self) -> TrackClass | None:
		"""The track to show in the metadata side panel"""
		target_track = None

		if self.playing_state == PlayingState.URL_STREAM:
			return self.radiobox.dummy_track

		if self.playing_state in (PlayingState.PLAYING, PlayingState.PAUSED):
			target_track = self.playing_object()

		elif self.playing_state == PlayingState.STOPPED and self.prefs.meta_shows_selected:
			if -1 < self.selected_in_playlist < len(self.multi_playlist[self.active_playlist_viewing].playlist_ids):
				target_track = self.get_track(self.multi_playlist[self.active_playlist_viewing].playlist_ids[self.selected_in_playlist])

		elif self.playing_state == PlayingState.STOPPED and self.prefs.meta_persists_stop:
			# A saved queue position can become stale when the queue was changed
			# before the previous shutdown. Do not let metadata rendering prevent
			# Tauon from starting in that case.
			if 0 <= self.queue_step < len(self.track_queue):
				target_track = self.master_library[self.track_queue[self.queue_step]]

		if self.prefs.meta_shows_selected_always \
		and -1 < self.selected_in_playlist < len(self.multi_playlist[self.active_playlist_viewing].playlist_ids):
			target_track = self.get_track(self.multi_playlist[self.active_playlist_viewing].playlist_ids[self.selected_in_playlist])

		return target_track

	def playing_object(self) -> TrackClass | None:
		if self.playing_state == PlayingState.URL_STREAM:
			return self.radiobox.dummy_track

		if 0 <= self.queue_step < len(self.track_queue):
			return self.master_library[self.track_queue[self.queue_step]]
		return None

	def title_text(self) -> str:
		line = ""
		track = self.playing_object()
		if track:
			title = track.title or ""
			artist = track.artist or ""

			if not title and not artist:
				if self.playing_state == PlayingState.URL_STREAM:
					return self.tag_meta
				return clean_string(track.filename)

			if artist:
				line += artist
			if title:
				if line:
					line += "  -  "
				line += title

		return line

	def show(self) -> int | None:
		if not self.track_queue:
			return 0
		return None

	def show_current(
		self, select: bool = True, playing: bool = True, quiet: bool = False, this_only: bool = False, highlight: bool = False,
		index: int | None = None, no_switch: bool = False, folder_list: bool = True,
	) -> int | None:

		# logging.info("show------")
		# logging.info(select)
		# logging.info(playing)
		# logging.info(quiet)
		# logging.info(this_only)
		# logging.info(highlight)
		# logging.info("--------")
		logging.debug("Position set by show playing")

		if not self.track_queue:
			return 0

		track_index = self.track_queue[self.queue_step]
		if index is not None:
			track_index = index

		# Switch to source playlist
		if not no_switch and self.active_playlist_viewing != self.active_playlist_playing and (
				track_index not in self.multi_playlist[self.active_playlist_viewing].playlist_ids):
			self.switch_playlist(self.active_playlist_playing)

		if self.gui.playlist_view_length < 1:
			return 0

		for i in range(len(self.multi_playlist[self.active_playlist_viewing].playlist_ids)):
			if self.multi_playlist[self.active_playlist_viewing].playlist_ids[i] == track_index:

				if self.playlist_playing_position < len(self.multi_playlist[self.active_playlist_viewing].playlist_ids) and \
						self.active_playlist_viewing == self.active_playlist_playing and track_index == \
						self.multi_playlist[self.active_playlist_viewing].playlist_ids[self.playlist_playing_position] and \
						i != self.playlist_playing_position:
					# continue
					i = self.playlist_playing_position

				if select:
					self.selected_in_playlist = i

				if playing:
					# Make the found track the playing track
					self.playlist_playing_position = i
					self.active_playlist_playing = self.active_playlist_viewing

				vl = self.gui.playlist_view_length
				if self.multi_playlist[self.active_playlist_viewing].uuid_int == self.gui.playlist_current_visible_tracks_id:
					vl = self.gui.playlist_current_visible_tracks

				if not (quiet and self.playing_object().length < 15):
				# or (abs(self.playlist_view_position - playlist_id) < vl - 1)):

					# Align to album if in view range (and folder titles are active)
					ap = self.tauon.get_album_info(i)[1][0]

					if not (quiet and self.playlist_view_position <= i <= self.playlist_view_position + vl) and (
					not abs(i - ap) > vl - 2) and not self.multi_playlist[self.active_playlist_viewing].hide_title:
						self.playlist_view_position = ap

					# Move to a random offset ---

					elif i == self.playlist_view_position - 1 and self.playlist_view_position > 1:
						self.playlist_view_position -= 1

					# Move a bit if its just out of range
					elif self.playlist_view_position + vl - 2 == i and i < len(
							self.multi_playlist[self.active_playlist_viewing].playlist_ids) - 5:
						self.playlist_view_position += 3

					# We know its out of range if above view position
					elif i < self.playlist_view_position:
						self.playlist_view_position = i - random.randint(2, int((
							self.gui.playlist_view_length / 3) * 2) + int(self.gui.playlist_view_length / 6))

					# If its below we need to test if its in view. If playing track in view, don't jump
					elif abs(self.playlist_view_position - i) >= vl:
						self.playlist_view_position = i
						if i > 6:
							self.playlist_view_position -= 5
						if i > self.gui.playlist_view_length and i + (self.gui.playlist_view_length * 2) < len(
								self.multi_playlist[self.active_playlist_viewing].playlist_ids) and i > 10:
							self.playlist_view_position = i - random.randint(2,
								int(self.gui.playlist_view_length / 3) * 2)
				break
		else:  # Search other all other playlists
			if not this_only:
				for i, playlist in enumerate(self.multi_playlist):
					if track_index in playlist.playlist_ids:
						self.switch_playlist(i, quiet=True)
						self.show_current(select, playing, quiet, this_only=True, index=track_index)
						break

		self.playlist_view_position = max(self.playlist_view_position, 0)

		# if self.playlist_view_position > len(self.multi_playlist[self.active_playlist_viewing].playlist_ids) - 1:
		#	 logging.info("Run Over")

		if select:
			self.gui.shift_selection = []

		self.render_playlist()

		if not quiet and self.tauon.custom.gallery_locate(self.selected_in_playlist, highlight=highlight):
			pass  # located in a custom-layout gallery widget instead of the preset
		elif self.prefs.album_mode and not quiet:
			if highlight:
				self.gui.gallery_animate_highlight_on = self.tauon.goto_album(self.selected_in_playlist)
				self.tauon.gallery_select_animate_timer.set()
			else:
				self.tauon.goto_album(self.selected_in_playlist)

		if self.prefs.left_panel_mode == "artist list" and self.gui.lsp and not quiet:
			self.artist_list_box.locate_artist(self.playing_object())

		if folder_list and self.prefs.left_panel_mode == "folder view" and self.gui.lsp and not quiet and not self.tree_view_box.lock_pl:
			self.tree_view_box.show_track(self.playing_object())

		return 0

	def toggle_mute(self) -> None:
		if self.player_volume > 0:
			self.volume_store = self.player_volume
			self.player_volume = 0
		else:
			self.player_volume = self.volume_store

		self.set_volume()

	def set_volume(self, notify: bool = True) -> None:
		self.volume_update_timer.set()

		if self.playerCommandReady:
			# send vol command later if command busy. Solution not great.
			def govol() -> None:
				time.sleep(1)
				if not self.playerCommandReady:
					self.playerCommand = "volume"
					self.playerCommandReady = True
				time.sleep(1)
				if not self.playerCommandReady:
					self.playerCommand = "volume"
					self.playerCommandReady = True
			shooter(govol)
		else:
			self.playerCommand = "volume"
			self.playerCommandReady = True
		if notify:
			self.refresh_now_playing()

	def clear_ab_repeat(self, update_gui: bool = True) -> None:
		self.ab_repeat_a = -1.0
		self.ab_repeat_b = -1.0
		if update_gui:
			self.tauon.gui.request_frame()

	def reset_ab_repeat_on_track_change(self, track_id: int) -> None:
		if self.ab_repeat_a < 0 and self.ab_repeat_b < 0:
			return
		if self.target_object is not None and self.target_object.index == track_id:
			return
		self.clear_ab_repeat()

	def revert(self) -> None:
		if self.queue_step == 0:
			return

		prev = 0
		while len(self.track_queue) > prev + 1 and prev < 5:
			if self.track_queue[len(self.track_queue) - 1 - prev] == self.left_index:
				self.queue_step = len(self.track_queue) - 1 - prev
				self.jump_time = self.left_time
				self.playing_time = self.left_time
				self.decode_time = self.left_time
				break
			prev += 1
		else:
			self.queue_step -= 1
			self.jump_time = 0.0
			self.playing_time = 0
			self.decode_time = 0

		if not len(self.track_queue) > self.queue_step >= 0:
			logging.error("There is no previous track?")
			return

		self.reset_ab_repeat_on_track_change(self.track_queue[self.queue_step])
		self.target_open = self.master_library[self.track_queue[self.queue_step]].fullpath
		self.target_object = self.master_library[self.track_queue[self.queue_step]]
		self.start_time = self.master_library[self.track_queue[self.queue_step]].start_time
		self.start_time_target = self.start_time
		self.playing_length = self.master_library[self.track_queue[self.queue_step]].length
		self.playerCommand = "open"
		self.playerCommandReady = True
		self.playing_state = PlayingState.PLAYING

		if self.tauon.stream_proxy.download_running:
			self.tauon.stream_proxy.stop()

		self.show_current()
		self.render_playlist()

	def deduct_shuffle(self, track_id: int) -> None:
		if self.multi_playlist and self.random_mode:
			pl = self.multi_playlist[self.active_playlist_playing]
			pl_id = pl.uuid_int

			if pl_id not in self.shuffle_pools:
				self.update_shuffle_pool(pl.uuid_int)

			pool = self.shuffle_pools[pl_id]
			if not pool:
				del self.shuffle_pools[pl_id]
				self.update_shuffle_pool(pl.uuid_int)
			pool = self.shuffle_pools[pl_id]

			if track_id in pool:
				pool.remove(track_id)

	def play_target_rr(self, play: bool = True) -> None:
		self.tauon.thread_manager.ready_playback()
		self.playing_length = self.master_library[self.track_queue[self.queue_step]].length

		if self.playing_length > 2:
			random_start = random.randrange(1, int(self.playing_length) - 45 if self.playing_length > 50 else int(
				self.playing_length))
		else:
			random_start = 0

		self.playing_time = random_start
		target_id = self.track_queue[self.queue_step]
		self.reset_ab_repeat_on_track_change(target_id)
		self.target_open = self.master_library[target_id].fullpath
		self.target_object = self.master_library[target_id]
		self.start_time = self.master_library[target_id].start_time
		self.start_time_target = self.start_time
		self.jump_time = random_start
		if play:
			self.playerCommand = "open"
			if not self.prefs.use_jump_crossfade:
				self.playerSubCommand = "now"
			self.playerCommandReady = True
			self.playing_state = PlayingState.PLAYING
		self.radiobox.loaded_station = None

		if self.tauon.stream_proxy.download_running:
			self.tauon.stream_proxy.stop()

		if self.prefs.update_title:
			self.tauon.update_title_do()

		self.deduct_shuffle(self.target_object.index)

	def play_target(self, _gapless: bool = False, jump: bool = False, play: bool = True, update_gui: bool = True) -> None:
		self.tauon.thread_manager.ready_playback()

		#logging.info(self.track_queue)
		self.playing_time = 0
		self.decode_time = 0
		target = self.master_library[self.track_queue[self.queue_step]]
		self.reset_ab_repeat_on_track_change(target.index)
		self.target_open = target.fullpath
		self.target_object = target
		self.start_time = target.start_time
		self.start_time_target = self.start_time
		self.playing_length = target.length
		self.last_playing_time = 0
		self.commit = None
		self.radiobox.loaded_station = None

		if self.tauon.stream_proxy and self.tauon.stream_proxy.download_running:
			self.tauon.stream_proxy.stop()

		if self.multi_playlist[self.active_playlist_playing].persist_time_positioning:
			t = (target.position if target.position is not None else 0)
			if t:
				self.playing_time = 0
				self.decode_time = 0
				self.jump_time = t

		if play:
			self.playerCommand = "open"
			if jump:  # and not prefs.use_jump_crossfade:
				self.playerSubCommand = "now"
			self.playerCommandReady = True
			self.playing_state = PlayingState.PLAYING

		self.update_change(update_gui)
		self.deduct_shuffle(target.index)

	def abort_gapless_transition(self, track: TrackClass, resume_time: float) -> None:
		self.target_open = track.fullpath
		self.target_object = track
		self.start_time = track.start_time
		self.start_time_target = self.start_time
		self.playing_length = track.length
		self.jump_time = resume_time
		self.playing_time = resume_time
		self.decode_time = resume_time
		self.last_playing_time = resume_time
		self.gui.update_spec = 0
		self.commit = None
		self.radiobox.loaded_station = None
		self.playerCommand = "open"
		self.playerSubCommand = "now"
		self.playerCommandReady = True
		self.playing_state = PlayingState.PLAYING

	def update_change(self, update_gui: bool = True) -> None:
		if self.prefs.update_title and update_gui:
			self.tauon.update_title_do()
		self.refresh_now_playing()
		# Wake and start Discord RPC worker immediately on change
		try:
			self.tauon._signal_discord()
		except Exception:
			# Fallback to legacy start if signalling fails
			self.tauon.hit_discord()
		if update_gui:
			self.render_playlist()

		if self.lfm_scrobbler.a_sc:
			self.lfm_scrobbler.a_sc = False
			self.a_time = 0

		self.lfm_scrobbler.start_queue()

		if (self.prefs.album_mode or not self.gui.rsp) and (self.gui.theme_name == "Carbon" or self.prefs.colour_from_image):
			target = self.playing_object()
			# Skip only when the already-applied theme is for this album. The
			# theme cache is keyed on album (theme_temp_current); last_album is a
			# folder path that the cache-apply path doesn't keep in sync, so
			# comparing against it here left stale themes after revisiting an
			# album (issue #2205).
			if target and self.prefs.colour_from_image and target.album == self.gui.theme_temp_current:
				return

			self.tauon.album_art_gen.display(target, (0, 0), (50, 50), theme_only=True)

	def jump(self, index: int, pl_position: int | None = None, jump: bool = True) -> None:
		self.lfm_scrobbler.start_queue()
		if self.stop_mode == StopMode.TRACK:  # Disable auto stop track
			self.stop_mode = StopMode.OFF
		if self.stop_mode == StopMode.ALBUM and self.playing_state != PlayingState.STOPPED:  # Disable auto stop album if album different
			tr = self.get_track(index)
			if (tr.parent_folder_path, tr.album) != self.stop_ref:
				self.stop_mode = StopMode.OFF
				self.stop_ref = None
		if self.stop_mode == StopMode.ALBUM_PERSIST:  # Assign new current album for stopping
			tr = self.get_track(index)
			self.stop_ref = (tr.parent_folder_path, tr.album)

		if self.force_queue and not self.pause_queue:
			if self.force_queue[0].type == QueueType.ALBUM and self.force_queue[0].album_stage == 1:
				if self.get_track(self.force_queue[0].track_id).parent_folder_path != self.get_track(index).parent_folder_path:
					del self.force_queue[0]

		if len(self.track_queue) > 0:
			self.left_time = self.playing_time
			self.left_index = self.track_queue[self.queue_step]

			if self.playing_state == PlayingState.PLAYING and self.left_time > 5 and self.playing_length - self.left_time > 15:
				self.master_library[self.left_index].skips += 1

		self.gui.update_spec = 0
		self.active_playlist_playing = self.active_playlist_viewing
		self.track_queue.append(index)
		self.queue_step = len(self.track_queue) - 1
		self.gui.playlist_hold = False
		self.play_target(jump=jump)

		if pl_position is not None:
			self.playlist_playing_position = pl_position

		self.gui.request_tracklist_redraw()

	def back(self) -> None:

		play = True
		if self.playing_state == PlayingState.PAUSED and not self.prefs.resume_on_jump:
			play = False
			self.playerCommand = "stop"
			self.playerCommandReady = True

		if self.playing_state != PlayingState.URL_STREAM and self.prefs.back_restarts and self.playing_time > 6:
			self.seek_time(0)
			self.render_playlist()
			return

		if len(self.track_queue) > 0:
			self.left_time = self.playing_time
			self.left_index = self.track_queue[self.queue_step]

		self.gui.update_spec = 0
		# Move up
		if self.random_mode is False and len(self.playing_playlist()) > self.playlist_playing_position > 0:

			if len(self.track_queue) > 0 and self.playing_playlist()[self.playlist_playing_position] != \
					self.track_queue[
						self.queue_step]:

				try:
					p = self.playing_playlist().index(self.track_queue[self.queue_step])
				except Exception:
					logging.exception("Failed to change playing_playlist")
					p = random.randrange(len(self.playing_playlist()))
				if p is not None:
					self.playlist_playing_position = p

			self.playlist_playing_position -= 1
			self.track_queue.append(self.playing_playlist()[self.playlist_playing_position])
			self.queue_step = len(self.track_queue) - 1
			self.play_target(jump=True, play=play)

		elif self.random_mode is True and self.queue_step > 0:
			self.queue_step -= 1
			self.play_target(jump=True, play=play)
		else:
			logging.info("BACK: NO CASE!")
			self.show_current()

		if self.active_playlist_viewing == self.active_playlist_playing:
			self.show_current(False, True)

		if self.prefs.album_mode:
			self.tauon.goto_album(self.playlist_playing_position)
		if self.gui.combo_mode and self.active_playlist_viewing == self.active_playlist_playing:
			self.show_current()

		self.render_playlist()
		self.refresh_now_playing()
		self.tauon.notify_song()
		self.lfm_scrobbler.start_queue()
		self.gui.request_tracklist_redraw()

	def stop(self, block: bool = False, run: bool = False, update_gui: bool = True) -> int:
		stream_proxy = getattr(self.tauon, "stream_proxy", None)
		stream_state = stream_proxy.state_log() if stream_proxy else "unavailable"
		self.playerCommand = "stop"
		if run:
			self.playerCommand = "runstop"
		if block:
			self.playerSubCommand = "return"

		self.playerCommandReady = True

		if self.tauon.thread_manager.player_lock.locked():
			try:
				self.tauon.thread_manager.player_lock.release()
			except RuntimeError as e:
				if str(e) == "release unlocked lock":
					logging.error("RuntimeError: Attempted to release already unlocked player_lock")  # noqa: TRY400
				else:
					logging.exception("Unknown RuntimeError trying to release player_lock")
			except Exception:
				logging.exception("Unknown exception trying to release player_lock")

		self.record_stream = False
		if len(self.track_queue) > 0:
			self.left_time = self.playing_time
			self.left_index = self.track_queue[self.queue_step]

		if self.tauon.radiobox.load_connecting or self.playing_state == PlayingState.URL_STREAM:
			# Keep loaded_station so play() can resume the radio after a stop
			self.tauon.radiobox.abort_load(clear_station=False)

		previous_state = self.playing_state
		self.playing_state = PlayingState.STOPPED
		if update_gui:
			self.playing_time = 0
			self.decode_time = 0
			self.render_playlist()

			self.gui.update_spec = 0
			# gui.update_level = True  # Allows visualiser to enter decay sequence
			self.gui.request_frame()
			if self.prefs.update_title:
				self.tauon.update_title_do()  # Update title bar text

		if self.tauon.stream_proxy and self.tauon.stream_proxy.download_running:
			logging.info(f"Player stop is stopping radio stream: {self.tauon.stream_proxy.state_log()}")
			self.tauon.stream_proxy.stop()

		if block:
			sleep_timeout(lambda: self.playerSubCommand != "stopped", 2)
			if self.tauon.stream_proxy.download_running:
				sleep_timeout(lambda: self.tauon.stream_proxy.download_running, 2)

		self.refresh_now_playing()
		self.lfm_scrobbler.start_queue()
		return previous_state

	def pause(self) -> None:
		if self.playing_state == PlayingState.URL_STREAM:
			return

		if self.playing_state == PlayingState.PLAYING:
			self.playerCommand = "pauseon"
			self.playing_state = PlayingState.PAUSED
		elif self.playing_state == PlayingState.PAUSED:
			self.playerCommand = "pauseoff"
			self.playing_state = PlayingState.PLAYING
			self.tauon.notify_song()

		self.playerCommandReady = True

		self.render_playlist()
		self.refresh_now_playing()

	def pause_only(self) -> None:
		if self.playing_state == PlayingState.PLAYING:
			self.playerCommand = "pauseon"
			self.playing_state = PlayingState.PAUSED

			self.playerCommandReady = True
			self.render_playlist()
			self.refresh_now_playing()

	def play_pause(self) -> None:
		if self.playing_state == PlayingState.URL_STREAM:
			self.stop()
		elif self.playing_state != PlayingState.STOPPED:
			self.pause()
		else:
			self.play()

	def seek_decimal(self, decimal: float) -> None:
		# if self.commit:
		#	 return
		if self.playing_state in (PlayingState.PLAYING, PlayingState.PAUSED):
			if decimal > 1:
				decimal = 1
			elif decimal < 0:
				decimal = 0
			self.new_time = self.playing_length * decimal
			#logging.info('seek to:' + str(self.new_time))
			self.playerCommand = "seek"
			self.playerCommandReady = True
			self.playing_time = self.new_time

			self.windows_progress.update()

			if self.mpris is not None:
				self.mpris.seek_do(self.playing_time)

	def seek_time(self, new: float) -> None:
		# if self.commit:
		#	 return
		if self.playing_state in (PlayingState.PLAYING, PlayingState.PAUSED):

			if new > self.playing_length - 0.5:
				self.advance()
				return

			if new < 0.4:
				new = 0

			self.new_time = new
			self.playing_time = new

			self.playerCommand = "seek"
			self.playerCommandReady = True

			if self.mpris is not None:
				self.mpris.seek_do(self.playing_time)

	def play(self, update_gui: bool = True) -> None:
		# Unpause if paused
		if self.playing_state == PlayingState.PAUSED:
			self.playerCommand = "pauseoff"
			self.playerCommandReady = True
			self.playing_state = PlayingState.PLAYING
			self.refresh_now_playing()

		# If stopped
		elif self.playing_state == PlayingState.STOPPED:

			if self.radiobox.loaded_station:
				self.radiobox.start(self.radiobox.loaded_station)
				return

			# If the queue is empty
			if self.track_queue == [] and len(self.multi_playlist[self.active_playlist_playing].playlist_ids) > 0:
				self.track_queue.append(self.multi_playlist[self.active_playlist_playing].playlist_ids[0])
				self.queue_step = 0
				self.playlist_playing_position = 0

				self.play_target(update_gui)

			# If the queue is not empty, play?
			elif len(self.track_queue) > 0:
				if self.stop_mode == StopMode.ALBUM_PERSIST:  # Assign new current album for stopping
					tr = self.playing_object()
					self.stop_ref = (tr.parent_folder_path, tr.album)
				self.play_target(update_gui)

		if update_gui:
			self.render_playlist()

	def purge_track(self, track_id: int, fast: bool = False) -> None:
		"""Remove a track from the database"""
		# Remove from all playlists
		if not fast:
			for playlist in self.multi_playlist:
				while track_id in playlist.playlist_ids:
					self.album_dex.clear()
					playlist.playlist_ids.remove(track_id)
		# Stop if track is playing track
		if self.track_queue and self.track_queue[self.queue_step] == track_id \
		and self.playing_state != PlayingState.STOPPED:
			self.stop(block=True)
		# Remove from playback history
		while track_id in self.track_queue:
			self.track_queue.remove(track_id)
			self.queue_step -= 1
		# Remove track from force queue
		for i in reversed(range(len(self.force_queue))):
			if self.force_queue[i].track_id == track_id:
				del self.force_queue[i]
		del self.master_library[track_id]

	def test_progress(self) -> None:
		# Fuzzy reload lastfm for rescrobble
		if self.lfm_scrobbler.a_sc and self.playing_time < 1:
			self.lfm_scrobbler.a_sc = False
			self.a_time = 0

		# Update the UI if playing time changes a whole number
		# next_round = int(self.playing_time)
		# if self.playing_time_int != next_round:
		#	 #if not prefs.power_save:
		#	 #self.gui.update += 1
		#	 self.playing_time_int = next_round

		tr = self.playing_object()
		gap_extra = 2
		if tr and tr.is_network:
			# Network tracks can transition gaplessly when streamed natively;
			# otherwise wait for the very end like before
			feeder = getattr(self.tauon, "stream_feeder", None)
			if not (self.prefs.network_stream and feeder is not None and feeder.enabled):
				gap_extra = 0

		if self.tauon.chrome_mode:
			gap_extra = 3

		self.windows_progress.update()

		if self.commit is not None:
			return

		if self.playing_state == PlayingState.PLAYING and self.ab_repeat_b > self.ab_repeat_a >= 0:
			if self.ab_repeat_b <= self.decode_time <= self.ab_repeat_b + 2 and self.playing_length > 0:
				self.decode_time = self.ab_repeat_a
				self.seek_decimal(self.ab_repeat_a / self.playing_length)
				return
		if self.ab_repeat_a >= 0:
			gap_extra = 0  # disable gapless for ab repeat

		if self.playing_state == PlayingState.PLAYING and self.multi_playlist[self.active_playlist_playing].persist_time_positioning:
			tr = self.playing_object()
			if tr:
				tr.position = self.decode_time

		if self.playing_state == PlayingState.PLAYING and self.decode_time + gap_extra >= self.playing_length and self.decode_time > 0.2:

			# Allow some time for backend to provide a length
			if self.playing_time < 6 and self.playing_length == 0:
				return
			if self.a_time < 2:
				return

			self.decode_time = 0

			pp = self.playing_playlist()

			stopped = False
			if self.stop_mode != StopMode.OFF:  # and not self.force_queue and not (self.force_queue and self.pause_queue):
				if self.stop_mode == StopMode.TRACK:
					self.stop(run=True)
					self.stop_mode = StopMode.OFF
					stopped = True
				if self.stop_mode == StopMode.ALBUM:
					tr = self.playing_object()
					i = self.advance(dry=True)
					if i is None:
						self.stop(run=True)
						self.stop_mode = StopMode.OFF
						stopped = True
					else:
						tr2 = self.get_track(i)
						if (tr.parent_folder_path, tr.album) != (tr2.parent_folder_path, tr2.album):
							self.stop(run=True)
							self.stop_mode = StopMode.OFF
							stopped = True
				if self.stop_mode == StopMode.TRACK_PERSIST:
					self.stop(run=True)
					stopped = True
				if self.stop_mode == StopMode.ALBUM_PERSIST:
					i = self.advance(dry=True)
					if i is None:
						self.stop(run=True)
						stopped = True
					else:
						tr2 = self.get_track(i)
						if self.stop_ref != (tr2.parent_folder_path, tr2.album):
							self.stop(run=True)
							stopped = True
				if stopped is True:
					if self.force_queue or (not self.force_queue and not self.random_mode and not self.repeat_mode):
						self.advance(play=False)
					self.gui.request_frame()
					return

			if self.force_queue and not self.pause_queue:
				id = self.advance(end=True, quiet=True, dry=True)
				if id is not None:
					self.start_commit(id)
					return
				self.advance(end=True, quiet=True)

			elif self.repeat_mode is True:
				if self.album_repeat_mode:
					if not pp:
						self.stop(run=True)
						self.gui.request_frame()
						return
					if self.playlist_playing_position > len(pp) - 1:
						self.playlist_playing_position = 0  # TODO(Taiko): Hack fix, race condition bug?

					ti = self.get_track(pp[self.playlist_playing_position])

					i = self.playlist_playing_position

					# Test if next track is in same folder
					if i + 1 < len(pp):
						nt = self.get_track(pp[i + 1])
						if ti.parent_folder_path == nt.parent_folder_path:
							# The next track is in the same folder
							# so advance normally
							self.advance(quiet=True, end=True)
							return

					# We need to backtrack to see where the folder begins
					i -= 1
					while i >= 0:
						nt = self.get_track(pp[i])
						if ti.parent_folder_path != nt.parent_folder_path:
							i += 1
							break
						i -= 1
					i = max(i, 0)

					self.selected_in_playlist = i
					self.gui.shift_selection = [i]

					self.jump(pp[i], i, jump=False)

				elif self.prefs.playback_follow_cursor and self.playing_ready() \
						and self.selected_ready() \
						and self.default_playlist[self.selected_in_playlist] != self.playing_object().index:

					logging.info("Repeat follow cursor")

					self.playing_time = 0
					self.decode_time = 0
					self.active_playlist_playing = self.active_playlist_viewing
					self.playlist_playing_position = self.selected_in_playlist

					self.track_queue.append(self.default_playlist[self.selected_in_playlist])
					self.queue_step = len(self.track_queue) - 1
					self.play_target(jump=False)
					self.render_playlist()
					self.lfm_scrobbler.start_queue()

				else:
					id = self.track_queue[self.queue_step]
					self.commit = id
					target = self.get_track(id)
					self.target_open = target.fullpath
					self.target_object = target
					self.start_time = target.start_time
					self.start_time_target = self.start_time
					self.playerCommand = "open"
					self.playerSubCommand = "repeat"
					self.playerCommandReady = True

					#self.render_playlist()
					self.lfm_scrobbler.start_queue()

					# Reload lastfm for rescrobble
					if self.lfm_scrobbler.a_sc:
						self.lfm_scrobbler.a_sc = False
						self.a_time = 0

			elif self.random_mode is False and len(pp) > self.playlist_playing_position + 1 and \
					self.master_library[pp[self.playlist_playing_position]].is_cue is True \
					and self.master_library[pp[self.playlist_playing_position + 1]].filename == \
					self.master_library[pp[self.playlist_playing_position]].filename and int(
				self.master_library[pp[self.playlist_playing_position]].track_number) == int(
				self.master_library[pp[self.playlist_playing_position + 1]].track_number) - 1:

				#  not (self.force_queue and not self.pause_queue) and \

				# We can shave it closer
				if not self.playing_time + 0.1 >= self.playing_length:
					return

				logging.info("Do transition CUE")
				self.playlist_playing_position += 1
				self.queue_step += 1
				self.track_queue.append(pp[self.playlist_playing_position])
				self.playing_state = PlayingState.PLAYING
				self.playing_time = 0
				self.decode_time = 0
				self.playing_length = self.master_library[self.track_queue[self.queue_step]].length
				self.start_time = self.master_library[self.track_queue[self.queue_step]].start_time
				self.start_time_target = self.start_time
				self.lfm_scrobbler.start_queue()

				self.gui.request_frame()
				self.gui.request_tracklist_redraw()

				if self.prefs.update_title:
					self.tauon.update_title_do()
				self.refresh_now_playing()
			else:
				# self.advance(quiet=True, end=True)

				id = self.advance(quiet=True, end=True, dry=True)
				if id is not None:
					#logging.info("Commit")
					self.start_commit(id)
					return

				self.advance(quiet=True, end=True)
				self.playing_time = 0
				self.decode_time = 0

	def start_commit(self, commit_id: int, repeat: bool = False) -> None:
		self.commit = commit_id
		target = self.get_track(commit_id)
		self.reset_ab_repeat_on_track_change(target.index)
		self.target_open = target.fullpath
		self.target_object = target
		self.start_time = target.start_time
		self.start_time_target = self.start_time
		self.playerCommand = "open"
		if repeat:
			self.playerSubCommand = "repeat"
		self.playerCommandReady = True

	def advance(
		self, rr: bool = False, quiet: bool = False, inplace: bool = False, end: bool = False,
		force: bool = False, play: bool = True, dry: bool = False,
	) -> int | None:

		if self.playing_state == PlayingState.PAUSED and not self.prefs.resume_on_jump:
			play = False
			if not dry:
				self.playerCommand = "stop"
				self.playerCommandReady = True

		# Temporary Workaround for UI block causing unwanted dragging
		if not dry:
			self.tauon.quick_d_timer.set()

		quiet = False  # Feature disabled intentionally, not a bug

		# Trim the history if it gets too long
		if not dry:
			while len(self.track_queue) > 250:
				self.queue_step -= 1
				del self.track_queue[0]

		# Save info about the track we are leaving
		if not dry and len(self.track_queue) > 0:
			self.left_time = self.playing_time
			self.left_index = self.track_queue[self.queue_step]

		# Test to register skip (not currently used for anything)
		if not dry and self.playing_state == PlayingState.PLAYING and 1 < self.left_time < 45:
			self.master_library[self.left_index].skips += 1
			#logging.info('skip registered')

		if not dry:
			self.playing_time = 0
			self.decode_time = 0
			self.playing_length = 100
			self.gui.update_spec = 0

		old = self.queue_step
		end_of_playlist = False

		# Force queue (middle click on track)
		if len(self.force_queue) > 0 and not self.pause_queue:

			q = self.force_queue[0]
			target_index = q.track_id

			if q.type == QueueType.ALBUM:
				if q.album_stage == 0:
					# We have not started playing the album yet
					# So we go to that track
					# (This is a copy of the track code, but we don't delete the item)

					if not dry:
						pl = self.id_to_pl(q.playlist_id)
						if pl is not None:
							self.active_playlist_playing = pl

						if target_index not in self.playing_playlist():
							del self.force_queue[0]
							self.advance()
							return None

					if dry:
						return target_index

					self.playlist_playing_position = q.position
					self.track_queue.append(target_index)
					self.queue_step = len(self.track_queue) - 1
					# self.queue_target = len(self.track_queue) - 1
					#if play:
					self.play_target(jump=not end, play=play)

					#  Set the flag that we have entered the album
					self.force_queue[0].album_stage = 1

					# This code is mirrored below -------
					ok_continue = True

					# Check if we are at end of playlist
					pl = self.multi_playlist[self.active_playlist_playing].playlist_ids
					if self.playlist_playing_position > len(pl) - 3:
						ok_continue = False

					# Check next song is in album
					if ok_continue and self.get_track(pl[self.playlist_playing_position + 1]).parent_folder_path != self.get_track(target_index).parent_folder_path:
						ok_continue = False

					# -----------

				elif q.album_stage == 1:
					# We have previously started playing this album

					# Check to see if we still are:
					ok_continue = True

					if self.get_track(target_index).parent_folder_path != self.playing_object().parent_folder_path:
						# Remember to set jumper check this too (leave album if we jump to some other track, i.e. double click))
						ok_continue = False

					pl = self.multi_playlist[self.active_playlist_playing].playlist_ids

					# Check next song is in album
					if ok_continue:

						# Check if we are at end of playlist, or already at end of album
						if self.playlist_playing_position >= len(pl) - 1 or (self.playlist_playing_position < len(
								pl) - 1 and \
								self.get_track(pl[self.playlist_playing_position + 1]).parent_folder_path != self.get_track(
							target_index).parent_folder_path):

							if dry:
								return None

							del self.force_queue[0]
							self.advance()
							return None


						# Check if 2 songs down is in album, remove entry in queue if not
						if self.playlist_playing_position < len(pl) - 2 and \
								self.get_track(pl[self.playlist_playing_position + 2]).parent_folder_path != self.get_track(
							target_index).parent_folder_path:
							ok_continue = False

					# if ok_continue:
					# We seem to be still in the album. Step down one and play
					if not dry:
						self.playlist_playing_position += 1

					if len(pl) <= self.playlist_playing_position:
						if dry:
							return None
						logging.info("END OF PLAYLIST!")
						del self.force_queue[0]
						self.advance()
						return None

					if dry:
						return pl[self.playlist_playing_position + 1]
					self.track_queue.append(pl[self.playlist_playing_position])
					self.queue_step = len(self.track_queue) - 1
					# self.queue_target = len(self.track_queue) - 1
					#if play:
					self.play_target(jump=not end, play=play)

				if not ok_continue:
					# It seems this item has expired, remove it and call advance again

					if dry:
						return None

					logging.info("Remove expired album from queue")
					del self.force_queue[0]

					if q.auto_stop:
						self.stop_mode = StopMode.TRACK
					if self.prefs.stop_end_queue and not self.force_queue:
						self.stop_mode = StopMode.TRACK

					if self.queue_box.scroll_position > 0:
						self.queue_box.scroll_position -= 1

						# self.advance()
						# return

			else:
				# This is track type
				pl = self.id_to_pl(q.playlist_id)
				if not dry and pl is not None:
					self.active_playlist_playing = pl

				if target_index not in self.playing_playlist():
					if dry:
						return None
					del self.force_queue[0]
					self.advance()
					return None

				if dry:
					return target_index

				self.playlist_playing_position = q.position
				self.track_queue.append(target_index)
				self.queue_step = len(self.track_queue) - 1
				# self.queue_target = len(self.track_queue) - 1
				#if play:
				self.play_target(jump=not end, play=play)
				del self.force_queue[0]
				if q.auto_stop:
					self.stop_mode = StopMode.TRACK
				if self.prefs.stop_end_queue and not self.force_queue:
					self.stop_mode = StopMode.TRACK
				if self.queue_box.scroll_position > 0:
					self.queue_box.scroll_position -= 1

		# Stop if playlist is empty
		elif len(self.playing_playlist()) == 0:
			if dry:
				return None
			self.stop()
			return 0

		# Playback follow cursor
		elif self.prefs.playback_follow_cursor and self.playing_ready() \
				and self.selected_ready() \
				and self.default_playlist[self.selected_in_playlist] != self.playing_object().index:

			if dry:
				return self.default_playlist[self.selected_in_playlist]

			self.active_playlist_playing = self.active_playlist_viewing
			self.playlist_playing_position = self.selected_in_playlist

			self.track_queue.append(self.default_playlist[self.selected_in_playlist])
			self.queue_step = len(self.track_queue) - 1
			#if play:
			self.play_target(jump=not end, play=play)

		# If random, jump to random track
		elif (self.random_mode or rr) and len(self.playing_playlist()) > 0 and not (
				self.album_shuffle_mode or self.prefs.album_shuffle_lock_mode):
			# self.queue_step += 1
			new_step = self.queue_step + 1

			if new_step == len(self.track_queue):

				if self.album_repeat_mode and self.repeat_mode:
					# Album shuffle mode
					pp = self.playing_playlist()
					k = self.playlist_playing_position
					# ti = self.get_track(pp[k])
					ti = self.master_library[self.track_queue[self.queue_step]]

					if ti.index not in pp:
						if dry:
							return None
						logging.info("No tracks to repeat!")
						return 0

					matches: list[tuple[int, int]] = []
					for i, p in enumerate(pp):

						if self.get_track(p).parent_folder_path == ti.parent_folder_path:
							matches.append((i, p))

					if matches:
						# Avoid a repeat of same track
						if len(matches) > 1 and (k, ti.index) in matches:
							matches.remove((k, ti.index))

						i, p = random.choice(matches)  # not used

						if self.prefs.true_shuffle:
							id = ti.parent_folder_path
							while True:
								if id in self.shuffle_pools:
									pool = self.shuffle_pools[id]

									if not pool:
										del self.shuffle_pools[id]  # Trigger a refill
										continue

									ref = pool.pop()
									if dry:
										pool.append(ref)
										return ref[1]
									# ref = random.choice(pool)
									# pool.remove(ref)

									if ref[1] not in pp:  # Check track still in the live playlist
										logging.info("Track not in pool")
										continue

									i, p = ref  # Find position of reference in playlist
									break

								# Refill the pool
								random.shuffle(matches)
								self.shuffle_pools[id] = matches
								logging.info("Refill folder shuffle pool")

						self.playlist_playing_position = i
						self.track_queue.append(p)
				else:
					# Normal select from playlist
					if self.prefs.true_shuffle:
						# True shuffle avoids repeats by using a pool
						pl = self.multi_playlist[self.active_playlist_playing]
						id = pl.uuid_int

						while True:

							if id in self.shuffle_pools:
								pool = self.shuffle_pools[id]
								if not pool:
									del self.shuffle_pools[id]  # Trigger a refill
									continue

								ref = pool.pop()
								if dry:
									pool.append(ref)
									return ref
								# ref = random.choice(pool)
								# pool.remove(ref)

								if ref not in pl.playlist_ids:  # Check track still in the live playlist
									continue

								random_jump = pl.playlist_ids.index(ref)  # Find position of reference in playlist
								break

							# Refill the pool
							self.update_shuffle_pool(pl.uuid_int)
					else:
						random_jump = random.randrange(len(self.playing_playlist()))  # not used

					self.playlist_playing_position = random_jump
					self.track_queue.append(self.playing_playlist()[random_jump])

			if inplace and self.queue_step > 1:
				del self.track_queue[self.queue_step]
			else:
				if dry:
					return self.track_queue[new_step]
				self.queue_step = new_step

			if rr:
				if dry:
					return None
				self.play_target_rr(play=play)
			else:
				self.play_target(jump=not end, play=play)


		# If not random mode, Step down 1 on the playlist
		elif self.random_mode is False and len(self.playing_playlist()) > 0:
			# Stop at end of playlist
			if self.playlist_playing_position == len(self.playing_playlist()) - 1:
				if dry:
					return None
				if self.prefs.end_setting == "stop":
					self.playing_state = PlayingState.STOPPED
					self.playerCommand = "runstop"
					self.playerCommandReady = True
					end_of_playlist = True

				elif self.prefs.end_setting in ("advance", "cycle"):
					# If at end playlist and not cycle mode, stop playback
					if self.active_playlist_playing == len(
							self.multi_playlist) - 1 and self.prefs.end_setting != "cycle":
						self.playing_state = PlayingState.STOPPED
						self.playerCommand = "runstop"
						self.playerCommandReady = True
						end_of_playlist = True

					else:
						p = self.active_playlist_playing
						for i in range(len(self.multi_playlist)):

							k = (p + i + 1) % len(self.multi_playlist)

							# Skip a playlist if empty
							if not (self.multi_playlist[k].playlist_ids):
								continue

							# Skip a playlist if hidden
							if self.multi_playlist[k].hidden and self.prefs.tabs_on_top:
								continue

							# Set found playlist as playing the first track
							self.active_playlist_playing = k
							self.playlist_playing_position = -1
							self.advance(end=end, force=True, play=play)
							break

						else:
							# Restart current if no other eligible playlist found
							self.playlist_playing_position = -1
							self.advance(end=end, force=True, play=play)

						return None

				elif self.prefs.end_setting == "repeat":
					self.playlist_playing_position = -1
					self.advance(end=end, force=True, play=play)
					return None

				self.gui.request_frame()

			else:
				if self.playlist_playing_position > len(self.playing_playlist()) - 1:
					if dry:
						return None
					self.playlist_playing_position = 0

				elif not force and self.track_queue and self.playing_playlist()[
					self.playlist_playing_position] != self.track_queue[
					self.queue_step] and self.track_queue[self.queue_step] in self.playing_playlist():
					try:
						if dry:
							return None
						self.playlist_playing_position = self.playing_playlist().index(
							self.track_queue[self.queue_step])
					except Exception:
						logging.exception("Failed to set playlist_playing_position")

				if len(self.playing_playlist()) == self.playlist_playing_position + 1:
					return None

				if dry:
					return self.playing_playlist()[self.playlist_playing_position + 1]
				self.playlist_playing_position += 1
				self.track_queue.append(self.playing_playlist()[self.playlist_playing_position])

				# logging.info("standand advance")
				# self.queue_target = len(self.track_queue) - 1
				# if end:
				#	 self.play_target_gapless(jump= not end)
				# else:
				self.queue_step = len(self.track_queue) - 1
				#if play:
				self.play_target(jump=not end, play=play)

		elif self.random_mode and (self.album_shuffle_mode or self.prefs.album_shuffle_lock_mode):
			# Album shuffle mode
			logging.info("Album shuffle mode")
			po = self.playing_object()
			redraw = False

			# Checks
			if po is not None and len(self.playing_playlist()) > 0:
				# If we at end of playlist, we'll go to a new album
				if len(self.playing_playlist()) == self.playlist_playing_position + 1:
					redraw = True
				# If the next track is a new album, go to a new album
				elif po.parent_folder_path != self.get_track(
						self.playing_playlist()[self.playlist_playing_position + 1]).parent_folder_path:
					redraw = True
				# Always redraw on press in album shuffle lockdown
				if self.prefs.album_shuffle_lock_mode and not end:
					redraw = True

				if not redraw:
					if dry:
						return self.playing_playlist()[self.playlist_playing_position + 1]
					self.playlist_playing_position += 1
					self.track_queue.append(self.playing_playlist()[self.playlist_playing_position])
					self.queue_step = len(self.track_queue) - 1
					# self.queue_target = len(self.track_queue) - 1
					#if play:
					self.play_target(jump=not end, play=play)
				else:
					if dry:
						return None
					albums: list[int] = []
					current_folder = ""
					for i in range(len(self.playing_playlist())):
						if i == 0:
							albums.append(i)
							current_folder = self.master_library[self.playing_playlist()[i]].parent_folder_path
						elif self.master_library[self.playing_playlist()[i]].parent_folder_path != current_folder:
							current_folder = self.master_library[self.playing_playlist()[i]].parent_folder_path
							albums.append(i)

					random.shuffle(albums)

					for a in albums:
						if self.get_track(self.playing_playlist()[a]).parent_folder_path != self.playing_object().parent_folder_path:
							self.playlist_playing_position = a
							self.track_queue.append(self.playing_playlist()[a])
							self.queue_step = len(self.track_queue) - 1
							# self.queue_target = len(self.track_queue) - 1
							#if play:
							self.play_target(jump=not end, play=play)
							break
					else:
						# There was no different album; restart from the first album in the playlist.
						a = 0
						self.playlist_playing_position = a
						self.track_queue.append(self.playing_playlist()[a])
						self.queue_step = len(self.track_queue) - 1
						#if play:
						self.play_target(jump=not end, play=play)
						# logging.info("THERE IS ONLY ONE ALBUM IN THE PLAYLIST")
						# self.stop()
		else:
			logging.error("ADVANCE ERROR - NO CASE!")

		if dry:
			return None

		if self.active_playlist_viewing == self.active_playlist_playing:
			self.show_current(quiet=quiet)
		elif self.prefs.auto_goto_playing:
			self.show_current(quiet=quiet, this_only=True, playing=False, highlight=True, no_switch=True)

		# if self.prefs.album_mode:
		#	 self.tauon.goto_album(self.playlist_playing)

		self.render_playlist()

		self.refresh_now_playing()
		self.lfm_scrobbler.start_queue()
		if play:
			self.tauon.notify_song(end_of_playlist, delay=1.3)
		return None

	def reset_missing_flags(self) -> None:
		for value in self.master_library.values():
			value.found = True
		self.gui.request_tracklist_redraw()
