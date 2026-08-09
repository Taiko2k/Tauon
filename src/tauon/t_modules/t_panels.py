"""Panel, mode, browser-display, and radio UI components."""

from __future__ import annotations

import copy
import io
import json
import logging
import math
import os
import random
import socket
import threading
import time
import urllib.parse
import webbrowser
from collections.abc import Callable
from ctypes import c_float, pointer
from typing import TYPE_CHECKING, Any, Protocol

import requests
import sdl3
from bs4 import BeautifulSoup
from PIL import Image

from tauon.t_modules.t_custom import draw_layout_glyph
from tauon.t_modules.t_enums import Backend, GuiMode, PlayingState, StopMode
from tauon.t_modules.t_extra import (
	FPSCounter,
	Timer,
	TestTimer,
	alpha_blend,
	alpha_mod,
	clean_string,
	colour_slide,
	coll_point,
	contrast_ratio,
	filename_safe,
	get_display_time,
	get_first_artist,
	hls_pull_contrast,
	hls_to_rgb,
	point_distance,
	point_proximity_test,
	rgb_add_hls,
	rgb_to_hls,
	test_lumi,
)
from tauon.t_modules.t_menu import Menu, MenuItem
from tauon.t_modules.t_models import ColourRGBA, LoadClass, RadioStation, TrackClass
from tauon.t_modules.t_prefs import Prefs
from tauon.t_modules.t_state import ColoursClass, Fonts, GuiVar, Input, asset_loader
from tauon.t_modules.t_text import TextBox2
from tauon.t_modules.t_widgets import Drawing, Fields, ScrollBox
from tauon.t_modules.t_webserve import stream_proxy

if TYPE_CHECKING:
	from websocket import WebSocketApp

	from tauon.t_modules.t_draw import TDraw


class _PanelPlayer(Protocol):
	default_playlist: list[int]
	multi_playlist: list[Any]
	force_queue: list[Any]

	def __getattr__(self, name: str) -> Any: ...

class TopPanel:
	def __init__(self, tauon: _PanelApp) -> None:
		self.tauon:          _PanelApp = tauon
		self.ddt:            TDraw = tauon.ddt
		self.gui:           GuiVar = tauon.gui
		self.inp:            Input = tauon.inp
		self.coll            = tauon.coll
		self.pctl:       _PanelPlayer = tauon.pctl
		self.prefs:          Prefs = tauon.prefs
		self.fonts:          Fonts = tauon.fonts
		self.fields:        Fields = tauon.fields
		self.colours: ColoursClass = tauon.colours
		self.renderer        = tauon.renderer
		self.window_size: list[int] = tauon.window_size
		self.overflow_menu:    Menu = tauon.overflow_menu
		self.draw_min_button:  bool = tauon.draw_min_button
		self.draw_max_button:  bool = tauon.draw_max_button
		self.height:            int = self.gui.panelY
		self.ty:                int = 0

		self.start_space_left = round(46 * self.gui.scale)
		self.start_space_compact_left = 46 * self.gui.scale

		self.tab_text_font = self.fonts.tabs
		self.tab_extra_width = round(17 * self.gui.scale)
		self.tab_text_start_space = 8 * self.gui.scale
		self.tab_text_y_offset = 7 * self.gui.scale
		self.tab_spacing = 0

		self.ini_menu_space = 17 * self.gui.scale  # 17
		self.menu_space = 17 * self.gui.scale
		self.click_buffer = 4 * self.gui.scale

		self.tabs_right_x = 0  # computed for drag and drop code elsewhere (hacky)
		self.tabs_left_x = 1

		self.prime_tab = self.gui.saved_prime_tab
		self.prime_side = self.gui.saved_prime_direction  # 0=left, 1=right
		self.shown_tabs = []

		# ---
		self.space_left = 0
		self.tab_text_spaces: list[int] = []
		self.index_playing = -1
		self.drag_zone_start_x = 300 * self.gui.scale

		bag                   = tauon.bag
		self.exit_button      = asset_loader(bag, bag.loaded_asset_dc, "ex.png", True)
		self.maximize_button  = asset_loader(bag, bag.loaded_asset_dc, "max.png", True)
		self.restore_button   = asset_loader(bag, bag.loaded_asset_dc, "restore.png", True)
		self.restore_button   = asset_loader(bag, bag.loaded_asset_dc, "restore.png", True)
		self.playlist_icon    = asset_loader(bag, bag.loaded_asset_dc, "playlist.png", True)
		self.return_icon      = asset_loader(bag, bag.loaded_asset_dc, "return.png", True)
		self.artist_list_icon = asset_loader(bag, bag.loaded_asset_dc, "artist-list.png", True)
		self.folder_list_icon = asset_loader(bag, bag.loaded_asset_dc, "folder-list.png", True)
		self.dl_button        = asset_loader(bag, bag.loaded_asset_dc, "dl.png", True)
		self.overflow_icon    = asset_loader(bag, bag.loaded_asset_dc, "overflow.png", True)

		self.drag_slide_timer = Timer(100)
		self.tab_d_click_timer = Timer(10)
		self.tab_d_click_ref = None

		self.adds: list[list[int | Timer]] = []

	def left_overflow_switch_playlist(self, pl: int) -> None:
		self.prime_side = 0
		self.prime_tab = pl
		self.pctl.switch_playlist(pl)

	def right_overflow_switch_playlist(self, pl: int) -> None:
		self.prime_side = 1
		self.prime_tab = pl
		self.pctl.switch_playlist(pl)

	def render(self) -> None:
		tauon       = self.tauon
		pctl        = self.pctl
		gui         = self.gui
		ddt         = self.ddt
		inp         = self.inp
		colours     = self.colours
		prefs       = self.prefs
		window_size = self.window_size

		# C-TD
		hh = gui.panelY2
		yy = gui.panelY - hh
		self.height = hh

		if inp.quick_drag is True:
			# gui.pl_update = 1
			gui.update_on_drag = True

		# Draw the background (blend over the art background if active,
		# otherwise clear first so window transparency works)
		if not gui.have_art_bg:
			ddt.clear_rect((0, 0, window_size[0], gui.panelY))
		ddt.rect((0, 0, window_size[0], gui.panelY), colours.top_panel_background)

		if prefs.shuffle_lock and not gui.compact_bar:
			colour = ColourRGBA(250, 250, 250, 255)
			if colours.lm:
				colour = ColourRGBA(10, 10, 10, 255)
			text = _("_PanelApp SHUFFLE!")
			if prefs.album_shuffle_lock_mode:
				text = _("ALBUM SHUFFLE")
			ddt.text((window_size[0] // 2, 8 * gui.scale, 2), text, colour, 212, bg=colours.top_panel_background)
		if gui.top_bar_mode2:
			tr = pctl.playing_object()
			if tr:
				tauon.album_art_gen.display(tr, (window_size[0] - gui.panelY - 1, 0), (gui.panelY, gui.panelY))
				if pctl.loading_in_progress or \
						tauon.to_scan or \
						tauon.cm_clean_db or \
						tauon.lastfm.scanning_friends or \
						tauon.after_scan or \
						tauon.move_in_progress or \
						tauon.plex.scanning or \
						tauon.transcode_list or tauon.subsonic.scanning or \
						gui.sync_progress or tauon.lastfm.scanning_scrobbles:
					ddt.rect(
						(window_size[0] - (gui.panelY + 20), gui.panelY - gui.panelY2, gui.panelY + 25, gui.panelY2),
						colours.top_panel_background)

				maxx = window_size[0] - (gui.panelY + 30 * gui.scale)
				title_colour = colours.grey(249)
				if colours.lm:
					title_colour = colours.grey(30)
				title = tr.title
				if not title:
					title = tr.filename
				artist = tr.artist

				if pctl.playing_state == PlayingState.URL_STREAM and not tauon.radiobox.dummy_track.title:
					title = pctl.tag_meta
					artist = tauon.radiobox.loaded_url  # pctl.url

				ddt.text_background_colour = colours.top_panel_background

				ddt.text((round(14 * gui.scale), round(15 * gui.scale)), title, title_colour, 215, max_w=maxx)
				ddt.text((round(14 * gui.scale), round(40 * gui.scale)), artist, colours.grey(120), 315, max_w=maxx)

		wwx = 0
		if prefs.left_window_control and not gui.compact_bar:
			if gui.macstyle:
				wwx = 24
				# wwx = round(64 * gui.scale)
				if self.draw_min_button:
					wwx += 20
				if self.draw_max_button:
					wwx += 20
				wwx = round(wwx * gui.scale)
			else:
				wwx = 26
				# wwx = round(90 * gui.scale)
				if self.draw_min_button:
					wwx += 35
				if self.draw_max_button:
					wwx += 33
				wwx = round(wwx * gui.scale)

		# The panel button sits in the second corner slot; the layout/edit-menu
		# button (below) takes the first, matching its position in custom mode.
		rect = (wwx + 44 * gui.scale, yy + 4 * gui.scale, 34 * gui.scale, 25 * gui.scale)
		self.fields.add(rect)

		if self.coll(rect) and not prefs.shuffle_lock and not gui.custom_mode:
			if inp.mouse_click:

				if gui.combo_mode:
					gui.switch_showcase_off = True
				else:
					gui.lsp ^= True

				gui.update_layout = True
				gui.request_frame()
			if self.inp.mouse_down and self.inp.quick_drag:
				gui.lsp = True
				gui.update_layout = True
				gui.request_frame()

			if self.inp.middle_click:
				self.tauon.toggle_left_last()
				gui.update_layout = True
				gui.request_frame()

			if inp.right_click:
				# prefs.artist_list ^= True
				self.tauon.lsp_menu.activate(position=(5 * gui.scale, gui.panelY))
				self.tauon.update_layout_do()

		colour = colours.corner_button  # [230, 230, 230, 255]

		if gui.lsp:
			colour = colours.corner_button_active
		if gui.combo_mode:
			colour = colours.corner_button
			if self.coll(rect):
				colour = colours.corner_button_active
		colour = self.tauon.style_overlay.tint_from_background(
			colour, wwx + 60 * gui.scale, yy + 16 * gui.scale, 0.2,
			colours.bottom_panel_colour)

		if not prefs.shuffle_lock and not gui.custom_mode:
			# The panel button hides in custom mode (the layout/edit button below
			# keeps the first slot there, drawn by the layout engine).
			if gui.combo_mode:
				self.return_icon.render(wwx + 49 * gui.scale, yy + 8 * gui.scale, colour)
			elif prefs.left_panel_mode == "artist list":
				self.artist_list_icon.render(wwx + 48 * gui.scale, yy + 8 * gui.scale, colour)
			elif prefs.left_panel_mode == "folder view":
				self.folder_list_icon.render(wwx + 49 * gui.scale, yy + 8 * gui.scale, colour)
			else:
				self.playlist_icon.render(wwx + 48 * gui.scale, yy + 8 * gui.scale, colour)

		if not prefs.shuffle_lock and not gui.custom_mode:
			# Corner layout/edit-menu button, in the first slot (before the panel
			# button). Same dim styling; active colour while its menu is open;
			# opens the layout menu.
			lrect = (wwx + 9 * gui.scale, yy + 3 * gui.scale, 34 * gui.scale, 25 * gui.scale)
			self.fields.add(lrect)
			if self.coll(lrect) and inp.mouse_click and not self.tauon.layout_menu.click_dismissed:
				inp.mouse_click = False
				self.tauon.layout_menu.activate(position=(lrect[0], lrect[1] + lrect[3]))
			lcol = colours.corner_button_active if self.tauon.layout_menu.active else colours.corner_button
			lcol = self.tauon.style_overlay.tint_from_background(
				lcol, wwx + 20 * gui.scale, yy + 16 * gui.scale, 0.2,
				colours.bottom_panel_colour)
			gw = round(18 * gui.scale)
			gh = round(13 * gui.scale)
			draw_layout_glyph(
				ddt, gui.scale,
				lrect[0] + round((lrect[2] - gw) / 2), lrect[1] + round((lrect[3] - gh) / 2),
				gw, gh, lcol)

		# if prefs.artist_list:
		#     self.artist_list_icon.render(13 * gui.scale, yy + 8 * gui.scale, colour)
		# else:
		#     self.playlist_icon.render(13 * gui.scale, yy + 8 * gui.scale, colour)

		if tauon.playlist_box.drag:
			self.inp.drag_mode = False

		# Need to test length
		self.tab_text_spaces = []

		if gui.radio_view:
			for item in pctl.radio_playlists:
				le = ddt.get_text_w(item.name, self.tab_text_font)
				self.tab_text_spaces.append(le)
		else:
			for i, item in enumerate(pctl.multi_playlist):
				le = ddt.get_text_w(pctl.multi_playlist[i].title, self.tab_text_font)
				self.tab_text_spaces.append(le)

		x = self.start_space_left + wwx
		if not prefs.shuffle_lock and not gui.custom_mode:
			# The corner holds two buttons (layout/edit menu, then the panel
			# button); start the tab strip after the second slot.
			x += round(35 * gui.scale)
		y = yy  # self.ty

		# Calculate position for playing text and text
		offset = 15 * gui.scale
		if tauon.draw_border and not prefs.left_window_control:
			offset += 61 * gui.scale
			if self.draw_max_button:
				offset += 61 * gui.scale
		if gui.turbo:
			offset += 90 * gui.scale
			if gui.vis == 3:
				offset += 57 * gui.scale
		if gui.top_bar_mode2:
			offset = 0

		p_text_len = 180 * gui.scale
		right_space_es = p_text_len + offset

		x_start = x

		if tauon.playlist_box.drag and not gui.radio_view:
			if self.inp.mouse_up:
				if self.inp.mouse_up_position[0] > gui.playlist_left and self.inp.mouse_up_position[1] > gui.panelY:
					tauon.playlist_box.drag = False
					if prefs.drag_to_unpin:
						if tauon.playlist_box.drag_source == 0:
							pass
							# Disabled drag to unpin feature
							#pctl.multi_playlist[tauon.playlist_box.drag_on].hidden = True
						else:
							pctl.multi_playlist[tauon.playlist_box.drag_on].hidden = False
					gui.request_frame()
			gui.update_on_drag = True

		# List all tabs eligible to be shown
		#logging.info("-------------")
		ready_tabs: list[int] = []
		show_tabs: list[int] = []

		if prefs.tabs_on_top or gui.radio_view:
			if gui.radio_view:
				for i, tab in enumerate(pctl.radio_playlists):
					ready_tabs.append(i)
				self.prime_tab = min(self.prime_tab, len(pctl.radio_playlists) - 1)
			else:
				for i, tab in enumerate(pctl.multi_playlist):
					# Skip if hide flag is set
					if tab.hidden:
						continue
					ready_tabs.append(i)
				self.prime_tab = min(self.prime_tab, len(pctl.multi_playlist) - 1)
			max_w = window_size[0] - (x + right_space_es + round(34 * gui.scale))

			left_tabs: list[int] = []
			right_tabs: list[int] = []
			if prefs.shuffle_lock:
				for p in ready_tabs:
					left_tabs.append(p)

			else:
				for p in ready_tabs:
					if p < self.prime_tab:
						left_tabs.append(p)

				for p in ready_tabs:
					if p > self.prime_tab:
						right_tabs.append(p)
				left_tabs.reverse()

			run = max_w

			if self.prime_tab in ready_tabs:
				size = self.tab_text_spaces[self.prime_tab] + self.tab_extra_width
				if size < run:
					show_tabs.append(self.prime_tab)
					run -= size

			if self.prime_side == 0:
				for tab in right_tabs:
					size = self.tab_text_spaces[tab] + self.tab_extra_width
					if size < run:
						show_tabs.append(tab)
						run -= size
					else:
						break
				for tab in left_tabs:
					size = self.tab_text_spaces[tab] + self.tab_extra_width
					if size < run:
						show_tabs.insert(0, tab)
						run -= size
					else:
						break
			else:
				for tab in left_tabs:
					size = self.tab_text_spaces[tab] + self.tab_extra_width
					if size < run:
						show_tabs.insert(0, tab)
						run -= size
					else:
						break
				for tab in right_tabs:
					size = self.tab_text_spaces[tab] + self.tab_extra_width
					if size < run:
						show_tabs.append(tab)
						run -= size
					else:
						break

			# for tab in show_tabs:
			#     logging.info(pctl.multi_playlist[tab].title)
			#logging.info("---")
			left_overflow = [x for x in left_tabs if x not in show_tabs]
			right_overflow = [x for x in right_tabs if x not in show_tabs]
			self.shown_tabs = show_tabs

			if left_overflow:
				hh = round(20 * gui.scale)
				rect = [x, y + (self.height - hh), 17 * gui.scale, hh]
				ddt.rect(rect, colours.tab_background)
				self.overflow_icon.render(rect[0] + round(3 * gui.scale), rect[1] + round(4 * gui.scale), colours.tab_text)

				x += 17 * gui.scale
				x_start = x

				if inp.mouse_click and self.coll(rect):
					self.overflow_menu.items.clear()
					for tab in reversed(left_overflow):
						if gui.radio_view:
							self.overflow_menu.add(
								MenuItem(pctl.radio_playlists[tab].name, self.left_overflow_switch_playlist,
								pass_ref=True, set_ref=tab))
						else:
							self.overflow_menu.add(
								MenuItem(pctl.multi_playlist[tab].title, self.left_overflow_switch_playlist,
								pass_ref=True, set_ref=tab))
					self.overflow_menu.activate(0, (rect[0], rect[1] + rect[3]))

			xx = x + (max_w - run)  # + round(6 * gui.scale)
			self.tabs_left_x = x_start

			if right_overflow:
				hh = round(20 * gui.scale)
				rect = [xx, y + (self.height - hh), 17 * gui.scale, hh]
				ddt.rect(rect, colours.tab_background)
				self.overflow_icon.render(
					rect[0] + round(3 * gui.scale), rect[1] + round(4 * gui.scale),
					colours.tab_text)
				if inp.mouse_click and self.coll(rect):
					self.overflow_menu.items.clear()
					for tab in right_overflow:
						if gui.radio_view:
							self.overflow_menu.add(
								MenuItem(
									pctl.radio_playlists[tab].name, self.left_overflow_switch_playlist, pass_ref=True, set_ref=tab))
						else:
							self.overflow_menu.add(
								MenuItem(
									pctl.multi_playlist[tab].title, self.left_overflow_switch_playlist, pass_ref=True, set_ref=tab))
					self.overflow_menu.activate(0, (rect[0], rect[1] + rect[3]))

			if gui.radio_view:
				if not self.inp.mouse_down and pctl.radio_playlist_viewing not in show_tabs and pctl.radio_playlist_viewing in ready_tabs:
					if pctl.radio_playlist_viewing < self.prime_tab:
						self.prime_side = 0
					elif pctl.radio_playlist_viewing > self.prime_tab:
						self.prime_side = 1
					self.prime_tab = pctl.radio_playlist_viewing
					gui.request_frame()
			elif not self.inp.mouse_down and pctl.active_playlist_viewing not in show_tabs and pctl.active_playlist_viewing in ready_tabs:
				if pctl.active_playlist_viewing < self.prime_tab:
					self.prime_side = 0
				elif pctl.active_playlist_viewing > self.prime_tab:
					self.prime_side = 1
				self.prime_tab = pctl.active_playlist_viewing
				gui.request_frame()

			if tauon.playlist_box.drag and self.inp.mouse_position[0] > xx and inp.mouse_position[1] < gui.panelY:
				gui.request_frame()
				if 0.5 < self.drag_slide_timer.get() < 1 and show_tabs and right_overflow:
					self.drag_slide_timer.set()
					self.prime_side = 1
					self.prime_tab = right_overflow[0]
				if self.drag_slide_timer.get() > 1:
					self.drag_slide_timer.set()
			if tauon.playlist_box.drag and self.inp.mouse_position[0] < x and inp.mouse_position[1] < gui.panelY:
				gui.request_frame()
				if 0.5 < self.drag_slide_timer.get() < 1 and show_tabs and left_overflow:
					self.drag_slide_timer.set()
					self.prime_side = 0
					self.prime_tab = left_overflow[0]
				if self.drag_slide_timer.get() > 1:
					self.drag_slide_timer.set()

		# TAB INPUT PROCESSING
		target = pctl.multi_playlist
		if gui.radio_view:
			target = pctl.radio_playlists
		for i, tab in enumerate(target):
			if not gui.radio_view:
				if not prefs.tabs_on_top or prefs.shuffle_lock:
					break

				if len(pctl.multi_playlist) != len(self.tab_text_spaces):
					break

			if i not in show_tabs:
				continue

			# Determine the tab width
			tab_width = self.tab_text_spaces[i] + self.tab_extra_width

			# Save the far right boundary of the tabs (hacky)
			self.tabs_right_x = x + tab_width

			# Detect mouse over and add tab to mouse over detection
			f_rect = [x, y + 1, tab_width - 1, self.height - 1]
			tab_hit = self.coll(f_rect)

			# Tab functions
			if tab_hit:
				if not gui.radio_view:
					# Double click to play
					if self.inp.mouse_up and pctl.pl_to_id(i) == self.tab_d_click_ref == pctl.pl_to_id(pctl.active_playlist_viewing) and \
							self.tab_d_click_timer.get() < 0.25 and point_distance(
								self.inp.last_click_location, self.inp.mouse_up_position) < 5 * gui.scale:

						if pctl.playing_state == PlayingState.PAUSED and pctl.active_playlist_playing == i:
							pctl.play()
						elif pctl.selected_ready() and (pctl.playing_state != PlayingState.PLAYING or pctl.active_playlist_playing != i):
							pctl.jump(pctl.default_playlist[pctl.selected_in_playlist], pl_position=pctl.selected_in_playlist)
					if self.inp.mouse_up:
						self.tab_d_click_timer.set()
						self.tab_d_click_ref = pctl.pl_to_id(i)

				# Click to change playlist
				if inp.mouse_click:
					gui.request_tracklist_redraw()
					tauon.playlist_box.drag = True
					tauon.playlist_box.drag_source = 0
					tauon.playlist_box.drag_on = i
					if gui.radio_view:
						pctl.radio_playlist_viewing = i
					else:
						pctl.switch_playlist(i)
					gui.set_drag_source()

				# Drag to move playlist
				if self.inp.mouse_up and tauon.playlist_box.drag and coll_point(self.inp.mouse_up_position, f_rect):
					if gui.radio_view:
						pctl.move_radio_playlist(tauon.playlist_box.drag_on, i)
					else:
						if tauon.playlist_box.drag_source == 1:
							pctl.multi_playlist[tauon.playlist_box.drag_on].hidden = False

						if i != tauon.playlist_box.drag_on:

							# # Reveal the tab in case it has been hidden
							# pctl.multi_playlist[tauon.playlist_box.drag_on].hidden = False

							if self.inp.key_shift_down:
								pctl.multi_playlist[i].playlist_ids += pctl.multi_playlist[tauon.playlist_box.drag_on].playlist_ids
								pctl.delete_playlist(tauon.playlist_box.drag_on, check_lock=True, force=True)
							else:
								pctl.move_playlist(tauon.playlist_box.drag_on, i)

					tauon.playlist_box.drag = False
					gui.request_frame()

				# Delete playlist on wheel click
				elif tauon.tab_menu.active is False and self.inp.middle_click:
					# delete_playlist(i)
					self.pctl.delete_playlist_ask(i)
					break

				# Activate menu on right click
				elif inp.right_click:
					if gui.radio_view:
						tauon.radio_tab_menu.activate(copy.deepcopy(i))
					else:
						tauon.tab_menu.activate(copy.deepcopy(i))
					gui.tab_menu_pl = i

				# Quick drop tracks
				elif not gui.radio_view and self.inp.quick_drag is True and self.inp.mouse_up:
					self.tab_d_click_ref = -1
					self.tab_d_click_timer.force_set(100)
					if (pctl.gen_codes.get(pctl.pl_to_id(i)) and "self" not in pctl.gen_codes[pctl.pl_to_id(i)]):
						tauon.clear_gen_ask(pctl.pl_to_id(i))
					self.inp.quick_drag = False
					modified = False
					gui.request_tracklist_redraw()

					for item in gui.shift_selection:
						pctl.multi_playlist[i].playlist_ids.append(pctl.default_playlist[item])
						modified = True
					if len(gui.shift_selection) > 0:
						modified = True
						self.adds.append(
							[pctl.multi_playlist[i].uuid_int, len(gui.shift_selection), Timer()])  # ID, num, timer

					if modified:
						pctl.after_import_flag = True
						tauon.dropped_playlist = i
						pctl.notify_database_changed()
						pctl.update_shuffle_pool(pctl.multi_playlist[i].uuid_int)
						tauon.tree_view_box.clear_target_pl(i)
						tauon.thread_manager.ready("worker")

				if self.inp.mouse_up and tauon.radio_view.drag:
					pctl.radio_playlists[i].stations.append(tauon.radio_view.drag)
					self.tauon.toast(_("Added station to: ") + pctl.radio_playlists[i].name)

					tauon.radio_view.drag = None

			x += tab_width + self.tab_spacing

		# Test dupelicate tab function
		if tauon.playlist_box.drag:
			rect = (0, x, self.height, window_size[0])
			self.fields.add(rect)

		if self.inp.mouse_up and tauon.playlist_box.drag and self.inp.mouse_position[0] > x and self.inp.mouse_position[1] < self.height:
			if gui.radio_view:
				pass
			elif self.inp.key_ctrl_down:
				tauon.gen_dupe(tauon.playlist_box.drag_on)

			else:
				if tauon.playlist_box.drag_source == 1:
					pctl.multi_playlist[tauon.playlist_box.drag_on].hidden = False

				pctl.move_playlist(tauon.playlist_box.drag_on, i)
			tauon.playlist_box.drag = False

		# Need to test length again
		# Need to test length
		self.tab_text_spaces = []

		if gui.radio_view:
			for item in pctl.radio_playlists:
				le = ddt.get_text_w(item.name, self.tab_text_font)
				self.tab_text_spaces.append(le)
		else:
			for i, item in enumerate(pctl.multi_playlist):
				le = ddt.get_text_w(pctl.multi_playlist[i].title, self.tab_text_font)
				self.tab_text_spaces.append(le)

		# Reset X draw position
		x = x_start
		bar_highlight_size = round(2 * gui.scale)

		# TAB DRAWING
		shown = []
		for i, tab in enumerate(target):

			if not gui.radio_view:
				if not prefs.tabs_on_top or prefs.shuffle_lock:
					break

				if len(pctl.multi_playlist) != len(self.tab_text_spaces):
					break

			# if tab.hidden is True:
			#     continue

			if i not in show_tabs:
				continue

			# if window_size[0] - x - (self.tab_text_spaces[i] + self.tab_extra_width) < right_space_es:
			#     break

			shown.append(i)

			tab_width = self.tab_text_spaces[i] + self.tab_extra_width
			rect = [x, y, tab_width, self.height]

			# Detect mouse over and add tab to mouse over detection
			f_rect = [x, y + 1, tab_width - 1, self.height - 1]
			self.fields.add(f_rect)
			tab_hit = self.coll(f_rect)
			playing_hint = False
			active = False

			# Determine tab background colour
			if not gui.radio_view:
				if i == pctl.active_playlist_viewing:
					bg = colours.tab_background_active
					active = True
				elif (
						tauon.tab_menu.active is True and tauon.tab_menu.reference == i) or (tauon.tab_menu.active is False and tab_hit and not tauon.playlist_box.drag):
					bg = colours.tab_highlight
				elif i == pctl.active_playlist_playing:
					bg = colours.tab_background
					playing_hint = True
				else:
					bg = colours.tab_background
			elif pctl.radio_playlist_viewing == i:
				bg = colours.tab_background_active
				active = True
			else:
				bg = colours.tab_background

			# Draw tab background
			ddt.rect(rect, bg)
			if playing_hint:
				ddt.rect(rect, ColourRGBA(255, 255, 255, 7))

			# Determine text colour
			fg = colours.tab_text_active if active else colours.tab_text

			# Draw tab text
			text = tab.name if gui.radio_view else tab.title
			ddt.text((x + self.tab_text_start_space, y + self.tab_text_y_offset), text, fg, self.tab_text_font, bg=bg)

			# Drop pulse

			if gui.pl_pulse and gui.drop_playlist_target == i and self.tauon.tab_pulse.render(
			x, y + self.height - bar_highlight_size, tab_width, bar_highlight_size, r=200,g=130) is False:
				gui.pl_pulse = False

			# Drag to move playlist
			if tab_hit:
				if self.inp.mouse_down and i != tauon.playlist_box.drag_on and tauon.playlist_box.drag is True:
					if self.inp.key_shift_down:
						ddt.rect((x, y + self.height - bar_highlight_size, tab_width, bar_highlight_size), ColourRGBA(80, 160, 200, 255))
					elif tauon.playlist_box.drag_on < i:
						ddt.rect((x + tab_width - bar_highlight_size, y, bar_highlight_size, gui.panelY2), ColourRGBA(80, 160, 200, 255))
					else:
						ddt.rect((x, y, bar_highlight_size, gui.panelY2), ColourRGBA(80, 160, 200, 255))
				elif not gui.radio_view and (self.inp.quick_drag or gui.ext_drop_mode) is True and tauon.pl_is_mut(i):
					ddt.rect((x, y + self.height - bar_highlight_size, tab_width, bar_highlight_size), ColourRGBA(80, 200, 180, 255))
			# Drag yellow line highlight if single track already in playlist
			elif not gui.radio_view and self.inp.quick_drag and not point_proximity_test(gui.drag_source_position, self.inp.mouse_position, 15 * gui.scale):
				for item in gui.shift_selection:
					if item < len(pctl.default_playlist) and pctl.default_playlist[item] in tab.playlist_ids:
						ddt.rect((x, y + self.height - bar_highlight_size, tab_width, bar_highlight_size), ColourRGBA(190, 160, 20, 255))
						break
			# Drag red line highlight if playlist is generator playlist
			if not gui.radio_view and self.inp.quick_drag and not point_proximity_test(gui.drag_source_position, self.inp.mouse_position, 15 * gui.scale):
				if not self.tauon.pl_is_mut(i):
					ddt.rect((x, y + self.height - bar_highlight_size, tab_width, bar_highlight_size), ColourRGBA(200, 70, 50, 255))

			if not gui.radio_view:
				if len(self.adds) > 0:
					for k in reversed(range(len(self.adds))):
						if pctl.multi_playlist[i].uuid_int == self.adds[k][0]:
							if self.adds[k][2].get() > 0.3:
								del self.adds[k]
							else:
								ay = y + 4
								ay -= 6 * self.adds[k][2].get() / 0.3

								ddt.text(
									(x + tab_width - 3, round(ay), 1), "+" + str(self.adds[k][1]), colours.pulse_colour, 212, bg=bg)
								gui.request_frame()

			x += tab_width + self.tab_spacing

		# Quick drag single track onto bar to create new playlist function and indicator
		if prefs.tabs_on_top:
			if (self.inp.quick_drag or gui.ext_drop_mode) and self.inp.mouse_position[0] > x and self.inp.mouse_position[1] < gui.panelY and tauon.quick_d_timer.get() > 1:
				ddt.rect((x, y, 2 * gui.scale, gui.panelY2), ColourRGBA(80, 200, 180, 255))

				if self.inp.mouse_up:
					tauon.drop_tracks_to_new_playlist(gui.shift_selection)

			# Draw end drag tab indicator
			if tauon.playlist_box.drag and self.inp.mouse_position[0] > x and self.inp.mouse_position[1] < gui.panelY:
				if self.inp.key_ctrl_down:
					ddt.rect((x, y, 2 * gui.scale, gui.panelY2), ColourRGBA(255, 190, 0, 255))
				else:
					ddt.rect((x, y, 2 * gui.scale, gui.panelY2), ColourRGBA(80, 160, 200, 255))

		if prefs.tabs_on_top and right_overflow:
			x += 24 * gui.scale
			self.tabs_right_x += 24 * gui.scale

		# -------------
		# Other input
		if self.inp.mouse_up:
			# In the Custom Layout the Header Bar widget renders in tree order,
			# usually before drop targets like the Queue widget; ending the drag
			# here would eat their drop, so the engine ends it after all widgets
			# have drawn (CustomMode.render) instead.
			if not gui.custom_mode:
				self.inp.quick_drag = False
			tauon.playlist_box.drag = False
			tauon.radio_view.drag = None

		# Scroll anywhere on panel to cycle playlist
		# (This is a bit complicated because we need to skip over hidden playlists)
		if self.inp.mouse_wheel != 0 and 1 < self.inp.mouse_position[1] < gui.panelY + 1 and len(pctl.multi_playlist) > 1 and self.inp.mouse_position[0] > 5:

			pctl.cycle_playlist_pinned(self.inp.mouse_wheel)
			# TODO (Flynn): does this one need a smooth scrolling update?

			gui.request_tracklist_redraw()
			if not prefs.tabs_on_top:
				if pctl.active_playlist_viewing not in shown:  # and not gui.lsp:
					gui.mode_toast_text = pctl.multi_playlist[pctl.active_playlist_viewing].title
					tauon.toast_mode_timer.set()
					gui.frame_callback_list.append(TestTimer(1))
				else:
					tauon.toast_mode_timer.force_set(10)
					gui.mode_toast_text = ""
		# ---------
		# Menu Bar

		x += self.ini_menu_space
		y += 7 * gui.scale
		ddt.text_background_colour = colours.top_panel_background

		# MENU -----------------------------

		word = _("MENU")
		word_length = ddt.get_text_w(word, 212)
		rect = [x - self.click_buffer, yy + self.ty + 1, word_length + self.click_buffer * 2, self.height - 1]
		hit = self.coll(rect)
		self.fields.add(rect)

		if (tauon.x_menu.active or hit) and not tauon.tab_menu.active:
			bg = colours.status_text_over
		else:
			bg = colours.status_text_normal
		bg = tauon.style_overlay.tint_from_background(
			bg, x, y + 8 * gui.scale, 0.2, colours.top_panel_background)
		ddt.text((x, y), word, bg, 212)

		if hit and inp.mouse_click:
			if tauon.x_menu.active:
				tauon.x_menu.active = False
			elif not tauon.x_menu.click_dismissed:
				# click_dismissed: this same click already closed the menu's
				# popup window (event loop) — don't instantly reopen it.
				xx = x
				if x > window_size[0] - (210 * gui.scale):
					xx = window_size[0] - round(210 * gui.scale)
				# View Switcher no longer pops out here (layouts live in the
				# corner layout menu now); menu sits 7px further left.
				tauon.x_menu.activate(position=(xx + round(5 * gui.scale), gui.panelY))

		# if True:
		#     border = round(3 * gui.scale)
		#     border_colour = colours.grey(30)
		#     rect = (5 * gui.scale, gui.panelY, round(90 * gui.scale), round(25 * gui.scale))
		#

		dl = len(tauon.dl_mon.ready)
		watching = len(tauon.dl_mon.watching)

		if (dl > 0 or watching > 0) and tauon.core_timer.get() > 2 and prefs.auto_extract and prefs.monitor_downloads:
			x += 52 * gui.scale
			rect = (x - 5 * gui.scale, y - 2 * gui.scale, 30 * gui.scale, 23 * gui.scale)
			self.fields.add(rect)

			if self.coll(rect):
				colour = colours.corner_button_active
				# if colours.lm:
				# colour = ColourRGBA(40, 40, 40, 255)
				if (dl > 0 or watching > 0) and inp.right_click:
					tauon.dl_menu.activate(position=(inp.mouse_position[0], gui.panelY))
				if dl > 0:
					if inp.mouse_click:
						pln = 0
						for item in tauon.dl_mon.ready:
							load_order = LoadClass()
							load_order.target = item
							pln = pctl.active_playlist_viewing
							load_order.playlist = pctl.multi_playlist[pln].uuid_int

							for i, pl in enumerate(pctl.multi_playlist):
								if prefs.download_playlist is not None:
									if pl.uuid_int == prefs.download_playlist:
										load_order.playlist = pl.uuid_int
										pln = i
										break
							else:
								for i, pl in enumerate(pctl.multi_playlist):
									if pl.title.lower() == "downloads":
										load_order.playlist = pl.uuid_int
										pln = i
										break

							tauon.load_orders.append(copy.deepcopy(load_order))

						if len(tauon.dl_mon.ready) > 0:
							tauon.dl_mon.ready.clear()
							pctl.switch_playlist(pln)

							pctl.playlist_view_position = len(pctl.default_playlist)
							logging.debug("Position changed by track import")
							gui.request_frame()
				else:
					colour = colours.corner_button  # ColourRGBA(60, 60, 60, 255)
					# if colours.lm:
					# 	colour = ColourRGBA(180, 180, 180, 255)
					if inp.mouse_click:
						inp.mouse_click = False
						self.show_message(
							_("It looks like something is being downloaded..."), _("Let's check back later..."), mode="info")


			else:
				colour = colours.corner_button  # ColourRGBA(60, 60, 60, 255)
				if colours.lm:
					# colour = ColourRGBA(180, 180, 180, 255)
					if tauon.dl_mon.ready:
						colour = colours.corner_button_active  # ColourRGBA(60, 60, 60, 255)

			colour = tauon.style_overlay.tint_from_background(
				colour, x, y + 8 * gui.scale, 0.2, colours.top_panel_background)
			self.dl_button.render(x, y + 1 * gui.scale, colour)
			if dl > 0:
				ddt.text((x + 18 * gui.scale, y - 4 * gui.scale), str(dl), colours.pulse_colour, 209)  # ColourRGBA(244, 223, 66, 255)
				# ColourRGBA(166, 244, 179, 255)

		# LAYOUT --------------------------------
		x += self.menu_space + word_length

		self.drag_zone_start_x = x - 5 * gui.scale
		status = True

		if pctl.loading_in_progress:
			bg = colours.status_info_text
			if gui.to_got == "xspf":
				text = _("Importing XSPF playlist")
			elif gui.to_got == "xspfl":
				text = _("Importing XSPF playlist...")
			elif gui.to_got == "ex":
				text = _("Extracting Archive...")
			else:
				text = _("Importing...  ") + str(gui.to_got)  # + "/" + str(gui.to_get)
				if inp.right_click and self.coll([x, y, 180 * gui.scale, 18 * gui.scale]):
					tauon.cancel_menu.activate(position=(x + 20 * gui.scale, y + 23 * gui.scale))
		elif tauon.after_scan:
			# bg = colours.status_info_text
			bg = ColourRGBA(100, 200, 100, 255)
			text = _("Scanning Tags...  {N} remaining").format(N=str(len(tauon.after_scan)))
		elif tauon.playlist_autoscan:
			# bg = colours.status_info_text
			bg = ColourRGBA(100, 200, 100, 255)
			text = _("Auto-importing playlists...")
		elif tauon.move_in_progress:
			text = _("File copy in progress...")
			bg = colours.status_info_text
		elif tauon.cm_clean_db and gui.to_get > 0:
			per = str(int(gui.to_got / gui.to_get * 100))
			text = _("Cleaning db...  ") + per + "%"
			bg = ColourRGBA(100, 200, 100, 255)
		elif tauon.to_scan:
			text = _("Rescanning Tags...  {N} remaining").format(N=str(len(tauon.to_scan)))
			bg = ColourRGBA(100, 200, 100, 255)
		elif tauon.plex.scanning:
			text = _("Accessing PLEX library...")
			if gui.to_got:
				text += f" {gui.to_got}"
			bg = ColourRGBA(229, 160, 13, 255)
		elif tauon.subsonic.scanning:
			text = _("Accessing AIRSONIC library...")
			if gui.to_got:
				text += f" {gui.to_got}"
			bg = ColourRGBA(58, 194, 224, 255)
		elif tauon.jellyfin.scanning:
			text = _("Accessing JELLYFIN library...")
			bg = ColourRGBA(90, 170, 240, 255)
		elif tauon.chrome_mode:
			text = _("Chromecast Mode")
			bg = ColourRGBA(207, 94, 219, 255)
		elif gui.sync_progress and not tauon.transcode_list:
			text = gui.sync_progress
			bg = ColourRGBA(100, 200, 100, 255)
			if inp.right_click and self.coll([x, y, 280 * gui.scale, 18 * gui.scale]):
				tauon.cancel_menu.activate(position=(x + 20 * gui.scale, y + 23 * gui.scale))
		elif tauon.transcode_list and gui.tc_cancel:
			bg = ColourRGBA(150, 150, 150, 255)
			text = _("Stopping transcode...")
		elif tauon.lrclib_uploads:
			bg = ColourRGBA(100, 200, 100, 255)
			text = _("Uploading lyrics to LRCLIB...")
		elif tauon.lastfm.scanning_friends or tauon.lastfm.scanning_loves:
			text = _("Scanning: ") + tauon.lastfm.scanning_username
			bg = ColourRGBA(200, 150, 240, 255)
		elif tauon.lastfm.scanning_scrobbles:
			text = _("Scanning Scrobbles...")
			bg = ColourRGBA(219, 88, 18, 255)
		elif gui.buffering:
			text = _("Buffering... ")
			text += gui.buffering_text
			bg = ColourRGBA(18, 180, 180, 255)
		elif tauon.lfm_scrobbler.queue and tauon.scrobble_warning_timer.get() < 260:
			text = _("Network error. Will try again later.")
			bg = ColourRGBA(250, 250, 250, 255)
			gui.last_fm_icon.render(x - 4 * gui.scale, y + 4 * gui.scale, ColourRGBA(250, 40, 40, 255))
			x += 21 * gui.scale
		elif tauon.listen_alongers:
			new = {}
			for ip, timer in tauon.listen_alongers.items():
				if timer.get() < 6:
					new[ip] = timer
			tauon.listen_alongers = new

			text = _("{N} listening along").format(N=len(tauon.listen_alongers))
			bg = ColourRGBA(40, 190, 235, 255)
		else:
			status = False

		if status:
			bg = tauon.style_overlay.tint_from_background(
				bg, x, y + 8 * gui.scale, 0.2, colours.top_panel_background)
			x += ddt.text((x, y), text, bg, 311)
			# x += ddt.get_text_w(text, 11)
		# TODO(Taiko): list listening clients
		elif tauon.transcode_list:
			bg = tauon.style_overlay.tint_from_background(
				colours.status_info_text, x, y + 8 * gui.scale, 0.2,
				colours.top_panel_background)
			# if inp.key_ctrl_down and inp.key_c_press:
			# 	del tauon.transcode_list[1:]
			# 	gui.tc_cancel = True
			if inp.right_click and self.coll([x, y, 280 * gui.scale, 18 * gui.scale]):
				tauon.cancel_menu.activate(position=(x + 20 * gui.scale, y + 23 * gui.scale))

			w = 100 * gui.scale
			x += ddt.text((x, y), _("Transcoding"), bg, 311) + 8 * gui.scale

			if gui.transcoding_batch_total:

				# c1 = ColourRGBA(40, 40, 40, 255)
				# c2 = ColourRGBA(60, 60, 60, 255)
				# c3 = ColourRGBA(130, 130, 130, 255)
				#
				# if colours.lm:
				# 	c1 = ColourRGBA(100, 100, 100, 255)
				# 	c2 = ColourRGBA(130, 130, 130, 255)
				# 	c3 = ColourRGBA(180, 180, 180, 255)

				c1 = ColourRGBA(40, 40, 40, 255)
				c2 = ColourRGBA(100, 59, 200, 200)
				c3 = ColourRGBA(150, 70, 200, 255)

				if colours.lm:
					c1 = ColourRGBA(100, 100, 100, 255)
					c2 = ColourRGBA(170, 140, 255, 255)
					c3 = ColourRGBA(230, 170, 255, 255)

				yy = y + 4 * gui.scale
				h = 9 * gui.scale
				box = [x, yy, w, h]
				# ddt.rect_r(box, ColourRGBA(100, 100, 100, 255))
				ddt.rect(box, c1)

				done = round(gui.transcoding_batch_done / gui.transcoding_batch_total * 100)
				doing = round(self.tauon.core_use / gui.transcoding_batch_total * 100)

				ddt.rect([x, yy, done, h], c3)
				ddt.rect([x + done, yy, doing, h], c2)

			x += w + 8 * gui.scale

			if gui.sync_progress:
				text = gui.sync_progress
			else:
				text = _("{N} Folder Remaining {T}").format(N=str(len(tauon.transcode_list)), T=tauon.transcode_state)
				if len(tauon.transcode_list) > 1:
					text = _("{N} Folders Remaining {T}").format(N=str(len(tauon.transcode_list)), T=tauon.transcode_state)

			x += ddt.text((x, y), text, bg, 311) + 8 * gui.scale


		if colours.lm:
			colours.tb_line = colours.grey(200)
			ddt.rect((0, int(gui.panelY - 1 * gui.scale), window_size[0], int(1 * gui.scale)), colours.tb_line)

class _PanelApp(Protocol):
	gui: GuiVar
	inp: Input
	ddt: TDraw
	coll: Callable[[object], bool]
	pctl: _PanelPlayer
	prefs: Prefs
	colours: ColoursClass
	fields: Fields
	window_size: list[int]
	renderer: Any

	def __getattr__(self, name: str) -> Any: ...
class BottomBarType1:
	def __init__(self, tauon: _PanelApp) -> None:
		self.tauon         = tauon
		self.gui           = tauon.gui
		self.inp           = tauon.inp
		self.ddt           = tauon.ddt
		self.coll          = tauon.coll
		self.pctl          = tauon.pctl
		self.prefs         = tauon.prefs
		self.fields        = tauon.fields
		self.colours       = tauon.colours
		self.renderer      = tauon.renderer
		self.window_size   = tauon.window_size
		self.smooth_scroll = tauon.smooth_scroll
		self.mode          = 0

		self.seek_time = 0

		self.seek_down = False
		self.seek_hit = False
		self.volume_hit = False
		self.volume_bar_being_dragged = False
		self.control_line_bottom = 35 * self.gui.scale
		self.repeat_click_off = False
		self.random_click_off = False

		self.seek_bar_position = [300 * self.gui.scale, self.window_size[1] - self.gui.panelBY]
		self.seek_bar_size = [self.window_size[0] - (300 * self.gui.scale), 15 * self.gui.scale]
		self.volume_bar_size = [135 * self.gui.scale, 14 * self.gui.scale]
		self.volume_bar_position = [0, 45 * self.gui.scale]

		self.play_button        = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "play.png", True)
		self.forward_button     = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "ff.png", True)
		self.back_button        = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "bb.png", True)
		self.repeat_button      = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "tauon_repeat.png", True)
		self.repeat_button_off  = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "tauon_repeat_off.png", True)
		self.shuffle_button_off = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "tauon_shuffle_off.png", True)
		self.shuffle_button     = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "tauon_shuffle.png", True)
		self.repeat_button_a    = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "tauon_repeat_a.png", True)
		self.shuffle_button_a   = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "tauon_shuffle_a.png", True)

		self.buffer_shard       = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "shard.png", True)

		self.scrob_stick = 0

	def update(self) -> None:
		if self.mode == 0:
			self.volume_bar_position[0] = self.window_size[0] - (210 * self.gui.scale)
			self.volume_bar_position[1] = self.window_size[1] - (27 * self.gui.scale)
			self.seek_bar_position[1]   = self.window_size[1] - self.gui.panelBY

			seek_bar_x = 300 * self.gui.scale
			if self.window_size[0] < 600 * self.gui.scale:
				seek_bar_x = 250 * self.gui.scale

			self.seek_bar_size[0] = self.window_size[0] - seek_bar_x
			self.seek_bar_position[0] = seek_bar_x

			# if gui.bb_show_art:
			#     self.seek_bar_position[0] = 300 + gui.panelBY
			#     self.seek_bar_size[0] = window_size[0] - 300 - gui.panelBY

			# self.seek_bar_position[0] = 0
			# self.seek_bar_size[0] = window_size[0]

	def render(self) -> None:
		window_size = self.window_size
		tauon       = self.tauon
		ddt         = self.ddt
		gui         = self.gui
		prefs       = self.prefs
		pctl        = self.pctl
		inp         = self.inp
		colours     = self.colours
		fonts       = self.tauon.fonts

		# Replace pixels (for window transparency) unless the art background
		# is underneath, in which case blend over it
		if not self.gui.have_art_bg:
			sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_NONE)
		ddt.rect_a((0, self.window_size[1] - self.gui.panelBY), (self.window_size[0], self.gui.panelBY), colours.bottom_panel_colour)
		sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_BLEND)

		# Let the grey furniture inherit a hint of the local art hue/saturation
		so = tauon.style_overlay
		seek_bg = so.tint_from_background(
			colours.seek_bar_background,
			self.seek_bar_position[0] + self.seek_bar_size[0] / 2,
			self.seek_bar_position[1] + self.seek_bar_size[1] / 2,
			panel=colours.bottom_panel_colour, boost=0.6)

		# If a bright art backdrop forced the seek background lighter than its
		# base grey, the fill (normally the lighter of the two) can be left
		# dimmer than the boosted background. When that boost happened, pull
		# the fill's lightness back above the background so the played portion
		# stays distinct.
		seek_fill = colours.seek_bar_fill
		seek_bg_l = rgb_to_hls(seek_bg.r, seek_bg.g, seek_bg.b)[1]
		seek_base_l = rgb_to_hls(
			colours.seek_bar_background.r, colours.seek_bar_background.g, colours.seek_bar_background.b)[1]
		if seek_bg_l > seek_base_l + 0.01:
			seek_fill = hls_pull_contrast(seek_fill, seek_bg, floor=0.12)
		volume_bg = so.tint_from_background(
			colours.volume_bar_background,
			self.volume_bar_position[0] + self.volume_bar_size[0] / 2,
			self.volume_bar_position[1] + self.volume_bar_size[1] / 2,
			panel=colours.bottom_panel_colour)
		buttons_y = window_size[1] - self.control_line_bottom
		panel_bg = colours.bottom_panel_colour
		mb_off = so.tint_from_background(colours.media_buttons_off, 150 * gui.scale, buttons_y, 0.2, panel_bg)
		mb_active = so.tint_from_background(colours.media_buttons_active, 150 * gui.scale, buttons_y, 0.2, panel_bg)
		mb_over = so.tint_from_background(colours.media_buttons_over, 150 * gui.scale, buttons_y, 0.2, panel_bg)
		md_off = so.tint_from_background(colours.mode_button_off, window_size[0] - 120 * gui.scale, buttons_y, 0.2, panel_bg)
		md_active = so.tint_from_background(colours.mode_button_active, window_size[0] - 120 * gui.scale, buttons_y, 0.2, panel_bg)
		md_over = so.tint_from_background(colours.mode_button_over, window_size[0] - 120 * gui.scale, buttons_y, 0.2, panel_bg)

		ddt.rect_a(self.seek_bar_position, self.seek_bar_size, seek_bg)

		right_offset = 0
		if gui.display_time_mode >= 2:
			right_offset = 22 * self.gui.scale

		if self.window_size[0] < 670 * self.gui.scale:
			right_offset -= 90 * self.gui.scale
		# Scrobble marker

		if prefs.scrobble_mark \
		and (prefs.auto_lfm or self.tauon.lb.enable or prefs.maloja_enable) and not prefs.scrobble_hold \
		and pctl.playing_length > 0 and (self.pctl.playing_state in (PlayingState.PLAYING, PlayingState.PAUSED)):
			if pctl.master_library[pctl.track_queue[pctl.queue_step]].length > 240 * 2:
				l_target = 240
			else:
				l_target = int(pctl.master_library[pctl.track_queue[pctl.queue_step]].length * 0.50)
			l_lead = l_target - pctl.a_time

			if l_lead > 0 and pctl.master_library[pctl.track_queue[pctl.queue_step]].length > 30:
				l_x = self.seek_bar_position[0] + math.ceil(
					pctl.playing_time * self.seek_bar_size[0] / int(pctl.playing_length))
				l_x += math.ceil(self.seek_bar_size[0] / int(pctl.playing_length) * l_lead)

				if abs(self.scrob_stick - l_x) < 2:
					l_x = self.scrob_stick
				else:
					self.scrob_stick = l_x
				ddt.rect((self.scrob_stick, self.seek_bar_position[1], 2 * self.gui.scale, self.seek_bar_size[1]), ColourRGBA(240, 10, 10, 80))

		# # MINI ALBUM ART
		# if gui.bb_show_art:
		# 	rect = [self.seek_bar_position[0] - gui.panelBY, self.seek_bar_position[1], gui.panelBY, gui.panelBY]
		# 	ddt.rect_r(rect, [255, 255, 255, 8], True)
		# 	if self.pctl.playing_state in (PlayingState.PLAYING, PlayingState.PAUSED:
		# 		tauon.album_art_gen.display(pctl.track_queue[pctl.queue_step], (rect[0], rect[1]), (rect[2], rect[3]))

		# ddt.rect_r(rect, ColourRGBA(255, 255, 255, 20))

		# SEEK BAR------------------
		if pctl.playing_time < 1:
			self.seek_time = 0

		if inp.mouse_click and coll_point(
			self.inp.mouse_position,
			self.seek_bar_position + [self.seek_bar_size[0]] + [
			self.seek_bar_size[1] + 2]):
			self.seek_down = True
			self.volume_hit = True
		if inp.right_click and coll_point(
			inp.mouse_position, self.seek_bar_position + [self.seek_bar_size[0]] + [self.seek_bar_size[1] + 2]):
			pctl.pause()
			if pctl.playing_state == PlayingState.STOPPED:
				pctl.play()

		self.fields.add(self.seek_bar_position + self.seek_bar_size)
		if self.coll(self.seek_bar_position + self.seek_bar_size):

			if self.inp.middle_click and pctl.playing_state != PlayingState.STOPPED:
				gui.seek_cur_show = True

			inp.global_clicked = True
			if self.inp.mouse_wheel != 0:
				pctl.seek_time(pctl.playing_time + (self.inp.mouse_wheel * 3))

		if gui.seek_cur_show:
			gui.request_frame()

			# self.fields.add([inp.mouse_position[0] - 1, inp.mouse_position[1] - 1, 1, 1])
			# ddt.rect_r([inp.mouse_position[0] - 1, inp.mouse_position[1] - 1, 1, 1], [255,0,0,180], True)

			bargetX = self.inp.mouse_position[0]
			bargetX = min(bargetX, self.seek_bar_position[0] + self.seek_bar_size[0])
			bargetX = max(bargetX, self.seek_bar_position[0])
			bargetX -= self.seek_bar_position[0]
			seek = bargetX / self.seek_bar_size[0]
			gui.cur_time = get_display_time(pctl.playing_object().length * seek)

		if self.seek_down is True and self.inp.mouse_position[0] == 0:
			self.seek_down = False
			self.seek_hit = True

		if (self.inp.mouse_up and self.coll(self.seek_bar_position + self.seek_bar_size) \
		and coll_point(self.inp.last_click_location, self.seek_bar_position + self.seek_bar_size) \
		and coll_point(self.inp.click_location, self.seek_bar_position + self.seek_bar_size)) \
		or (self.inp.mouse_up and self.volume_hit) or self.seek_hit:
			self.volume_hit = False
			self.seek_down = False
			self.seek_hit = False

			bargetX = self.inp.mouse_position[0]
			bargetX = min(bargetX, self.seek_bar_position[0] + self.seek_bar_size[0])
			bargetX = max(bargetX, self.seek_bar_position[0])
			bargetX -= self.seek_bar_position[0]
			seek = bargetX / self.seek_bar_size[0]

			pctl.seek_decimal(seek)
			#logging.info(seek)

			self.seek_time = pctl.playing_time

		if tauon.radiobox.load_connecting or gui.buffering:
			x = self.seek_bar_position[0] - round(26 - gui.scale)
			y = self.seek_bar_position[1]
			while x < self.seek_bar_position[0] + self.seek_bar_size[0]:
				offset = (math.floor(((tauon.core_timer.get() * 1) % 1) * 13) / 13) * self.buffer_shard.w
				gui.delay_frame(0.01)

				# colour = colours.seek_bar_fill
				h, l, s = rgb_to_hls(
					colours.seek_bar_background.r, colours.seek_bar_background.g, colours.seek_bar_background.b)
				l = min(1, l + 0.05)
				colour = hls_to_rgb(h, l, s)
				colour.a = colours.seek_bar_background.a

				self.buffer_shard.render(x + offset, y, colour)
				x += self.buffer_shard.w

			ddt.rect(
				(self.seek_bar_position[0] - self.buffer_shard.w, y, self.buffer_shard.w, self.buffer_shard.h),
				colours.bottom_panel_colour)

		if pctl.playing_length > 0:
			if pctl.download_time != 0:
				if pctl.download_time == -1:
					pctl.download_time = pctl.playing_length

				colour = ColourRGBA(255, 255, 255, 10)
				if gui.theme_name == "Lavender Light" or gui.theme_name == "Carbon":
					colour = ColourRGBA(255, 255, 255, 40)

				gui.seek_bar_rect = (
					self.seek_bar_position[0], self.seek_bar_position[1],
					int(pctl.download_time * self.seek_bar_size[0] / pctl.playing_length),
					self.seek_bar_size[1])
				ddt.rect(gui.seek_bar_rect, colour)

			gui.seek_bar_rect = (
				self.seek_bar_position[0], self.seek_bar_position[1],
				int(self.seek_time * self.seek_bar_size[0] / pctl.playing_length),
				self.seek_bar_size[1])
			ddt.rect(gui.seek_bar_rect, seek_fill)
			tauon.draw_ab_repeat_markers(
				self.seek_bar_position[0], self.seek_bar_position[1],
				self.seek_bar_size[0], self.seek_bar_size[1])

		if gui.seek_cur_show:
			if self.coll(
				[self.seek_bar_position[0] - 50, self.seek_bar_position[1] - 50, self.seek_bar_size[0] + 50, self.seek_bar_size[1] + 100]):
				if self.inp.mouse_position[0] > self.seek_bar_position[0] - 1:
					cur = [self.inp.mouse_position[0] - 40, self.seek_bar_position[1] - 25, 42, 19]
					ddt.rect(cur, colours.grey(15))
					# ddt.rect_r(cur, colours.grey(80))
					ddt.text(
						(self.inp.mouse_position[0] - 40 + 3, self.seek_bar_position[1] - 24), gui.cur_time,
						colours.grey(180), 213,
						bg=colours.grey(15))

					ddt.rect(
						[self.inp.mouse_position[0], self.seek_bar_position[1], 2, self.seek_bar_size[1]],
						ColourRGBA(100, 100, 20, 255))
			else:
				gui.seek_cur_show = False

		if gui.buffering and pctl.buffering_percent:
			ddt.rect_a((self.seek_bar_position[0], self.seek_bar_position[1] + self.seek_bar_size[1] - round(3 * gui.scale)), (self.seek_bar_size[0] * pctl.buffering_percent / 100, round(3 * gui.scale)), ColourRGBA(255, 255, 255, 50))
		# Volume mouse wheel control -----------------------------------------
		if self.inp.mouse_wheel != 0 and self.inp.mouse_position[1] > self.seek_bar_position[1] + 4 \
		and not coll_point(self.inp.mouse_position, self.seek_bar_position + self.seek_bar_size):
			scroll_distance = self.smooth_scroll.scroll("volume bar")
			pctl.player_volume += scroll_distance * prefs.volume_wheel_increment
			if pctl.player_volume < 1:
				pctl.player_volume = 0
			elif pctl.player_volume > 100:
				pctl.player_volume = 100

			pctl.player_volume = int(pctl.player_volume)
			pctl.set_volume()

		# Volume Bar 2 ------------------------------------------------
		if window_size[0] < 670 * gui.scale:
			x = window_size[0] - right_offset - 207 * gui.scale
			y = window_size[1] - round(14 * gui.scale)

			rect = (x - 8 * gui.scale, y - 17 * gui.scale, 55 * gui.scale, 23 * gui.scale)
			# ddt.rect(rect, [255,255,255,25])
			if self.coll(rect) and self.inp.mouse_down:
				gui.update_on_drag = True

			h_rect = (x - 6 * gui.scale, y - 17 * gui.scale, 4 * gui.scale, 23 * gui.scale)
			if self.coll(h_rect) and self.inp.mouse_down:
				pctl.player_volume = 0

			step = round(1 * gui.scale)
			min_h = round(4 * gui.scale)
			spacing = round(5 * gui.scale)

			if inp.right_click and self.coll((h_rect[0], h_rect[1], h_rect[2] + 50 * gui.scale, h_rect[3])):
				if inp.right_click:
					pctl.toggle_mute()

			for bar in range(8):
				h = min_h + bar * step
				rect = (x, y - h, 3 * gui.scale, h)
				h_rect = (x - 1 * gui.scale, y - 17 * gui.scale, 4 * gui.scale, 23 * gui.scale)

				if self.coll(h_rect):
					if self.inp.mouse_down or self.inp.mouse_up:
						gui.update_on_drag = True

						if bar == 0:
							pctl.player_volume = 5
						if bar == 1:
							pctl.player_volume = 10
						if bar == 2:
							pctl.player_volume = 20
						if bar == 3:
							pctl.player_volume = 30
						if bar == 4:
							pctl.player_volume = 45
						if bar == 5:
							pctl.player_volume = 55
						if bar == 6:
							pctl.player_volume = 70
						if bar == 7:
							pctl.player_volume = 100

						pctl.set_volume()

				colour = md_off

				if bar == 0 and pctl.player_volume > 0:
					colour = md_active
				elif bar == 1 and pctl.player_volume >= 10:
					colour = md_active
				elif bar == 2 and pctl.player_volume >= 20:
					colour = md_active
				elif bar == 3 and pctl.player_volume >= 30:
					colour = md_active
				elif bar == 4 and pctl.player_volume >= 45:
					colour = md_active
				elif bar == 5 and pctl.player_volume >= 55:
					colour = md_active
				elif bar == 6 and pctl.player_volume >= 70:
					colour = md_active
				elif bar == 7 and pctl.player_volume >= 95:
					colour = md_active

				ddt.rect(rect, colour)
				x += spacing

		# Volume Bar --------------------------------------------------------
		else:
			if (inp.mouse_click and self.coll((
					self.volume_bar_position[0] - right_offset, self.volume_bar_position[1], self.volume_bar_size[0],
					self.volume_bar_size[1] + 4))) or \
					self.volume_bar_being_dragged is True:
				inp.global_clicked = True

				if inp.mouse_click is True or self.volume_bar_being_dragged is True:
					gui.request_frame()

					self.volume_bar_being_dragged = True
					volgetX = self.inp.mouse_position[0]
					volgetX = min(volgetX, self.volume_bar_position[0] + self.volume_bar_size[0] - right_offset)
					volgetX = max(volgetX, self.volume_bar_position[0] - right_offset)
					volgetX -= self.volume_bar_position[0] - right_offset
					pctl.player_volume = volgetX / self.volume_bar_size[0] * 100

					time.sleep(0.005)

					if self.inp.mouse_down is False:
						self.volume_bar_being_dragged = False
						pctl.player_volume = int(pctl.player_volume)
						pctl.set_volume(True)

				if self.inp.mouse_down:
					pctl.player_volume = int(pctl.player_volume)
					pctl.set_volume(False)

			if inp.right_click and self.coll((
					self.volume_bar_position[0] - 15 * gui.scale, self.volume_bar_position[1] - 10 * gui.scale,
					self.volume_bar_size[0] + 30 * gui.scale,
					self.volume_bar_size[1] + 20 * gui.scale)):

				if pctl.player_volume > 0:
					pctl.volume_store = pctl.player_volume
					pctl.player_volume = 0
				else:
					pctl.player_volume = pctl.volume_store

				pctl.set_volume()

			ddt.rect_a(
				(self.volume_bar_position[0] - right_offset, self.volume_bar_position[1]),
				self.volume_bar_size, volume_bg)  # 22

			gui.volume_bar_rect = (
				self.volume_bar_position[0] - right_offset, self.volume_bar_position[1],
				int(pctl.player_volume * self.volume_bar_size[0] / 100), self.volume_bar_size[1])

			ddt.rect(gui.volume_bar_rect, colours.volume_bar_fill)

			self.fields.add(self.volume_bar_position + self.volume_bar_size)
			if pctl.active_replaygain != 0 and (self.coll((
				self.volume_bar_position[0], self.volume_bar_position[1], self.volume_bar_size[0],
				self.volume_bar_size[1])) or self.volume_bar_being_dragged):

				if pctl.player_volume > 50:
					ddt.text(
						(self.volume_bar_position[0] - right_offset + 8 * gui.scale,
						self.volume_bar_position[1] - 1 * gui.scale), str(pctl.active_replaygain) + " dB",
						colours.volume_bar_background,
						11, bg=colours.volume_bar_fill)
				else:
					ddt.text(
						(self.volume_bar_position[0] - right_offset + 85 * gui.scale,
						self.volume_bar_position[1] - 1 * gui.scale), str(pctl.active_replaygain) + " dB",
						colours.volume_bar_fill,
						11, bg=colours.volume_bar_background)

		gui.show_bottom_title = gui.showed_title ^ True
		if not prefs.hide_bottom_title:
			gui.show_bottom_title = True

		if gui.show_bottom_title and pctl.playing_state != PlayingState.STOPPED and window_size[0] > 820 * gui.scale:
			line = pctl.title_text()

			x = self.seek_bar_position[0] + 1
			mx = window_size[0] - 710 * gui.scale
			# if self.gui.bb_show_art:
			#  x += 10 * self.gui.scale
			#  mx -= self.gui.panelBY - 10

			# line = self.tauon.trunc_line(line, 213, mx)
			ddt.text(
				(x, self.seek_bar_position[1] + 24 * gui.scale), line, colours.bar_title_text,
				fonts.panel_title, max_w=mx)

		if (inp.mouse_click or inp.right_click) and self.coll((
				self.seek_bar_position[0] - 10 * gui.scale, self.seek_bar_position[1] + 20 * gui.scale,
				window_size[0] - 710 * gui.scale, 30 * gui.scale)):
			# if pctl.playing_state == PlayingState.URL_STREAM:
			# 	copy_to_clipboard(pctl.tag_meta)
			# 	self.show_message("Copied text to clipboard")
			# 	if input.mouse_click or inp.right_click:
			# 		input.mouse_click = False
			# 		inp.right_click = False
			# else:
			if inp.mouse_click and pctl.playing_state != PlayingState.URL_STREAM:
				pctl.show_current()

			if pctl.playing_ready() and not gui.fullscreen:
				if inp.right_click:
					tauon.mode_menu.activate()

				if self.tauon.d_click_timer.get() < 0.3 and inp.mouse_click:
					self.tauon.set_mini_mode()
					gui.request_frame()
					return
				self.tauon.d_click_timer.set()

		# TIME----------------------

		x = window_size[0] - 57 * gui.scale
		y = window_size[1] - 29 * gui.scale

		r_start = x - 10 * gui.scale
		if gui.display_time_mode in (2, 3):
			r_start -= 20 * gui.scale
		rect = (r_start, y - 3 * gui.scale, 80 * gui.scale, 27 * gui.scale)
		# ddt.rect_r(rect, [255, 0, 0, 40], True)
		if inp.mouse_click and self.coll(rect):
			gui.display_time_mode += 1
			if gui.display_time_mode > 3:
				gui.display_time_mode = 0

		if gui.display_time_mode == 0:
			text_time = get_display_time(pctl.playing_time)
			ddt.text(
				(x + 1 * gui.scale, y), text_time, colours.time_playing,
				fonts.bottom_panel_time)
		elif gui.display_time_mode == 1:
			if pctl.playing_state == PlayingState.STOPPED:
				text_time = get_display_time(0)
			else:
				text_time = get_display_time(pctl.playing_length - pctl.playing_time)
			ddt.text(
				(x + 1 * gui.scale, y), text_time, colours.time_playing,
				fonts.bottom_panel_time)
			ddt.text(
				(x - 5 * gui.scale, y), "-", colours.time_playing,
				fonts.bottom_panel_time)
		elif gui.display_time_mode == 2:

			# colours.time_sub = alpha_blend(ColourRGBA(255, 255, 255, 80), colours.bottom_panel_colour)

			x -= 4
			text_time = get_display_time(pctl.playing_time)
			ddt.text(
				(x - 25 * gui.scale, y), text_time, colours.time_playing,
				fonts.bottom_panel_time)

			offset1 = 10 * gui.scale

			offset2 = offset1 + 7 * gui.scale

			ddt.text(
				(x + offset1, y), "/", colours.time_sub,
				fonts.bottom_panel_time)
			text_time = get_display_time(pctl.playing_length)
			if pctl.playing_state == PlayingState.STOPPED:
				text_time = get_display_time(0)
			elif pctl.playing_state == PlayingState.URL_STREAM:
				text_time = "-- : --"
			ddt.text(
				(x + offset2, y), text_time, colours.time_sub,
				fonts.bottom_panel_time)
		elif gui.display_time_mode == 3:
			# colours.time_sub = alpha_blend(ColourRGBA(255, 255, 255, 80), colours.bottom_panel_colour)
			track = pctl.playing_object()
			if track and track.index != gui.dtm3_index:

				gui.dtm3_cum = 0
				gui.dtm3_total = 0
				run = True
				collected = []
				for item in pctl.default_playlist:
					if pctl.master_library[item].parent_folder_path == track.parent_folder_path:
						if item not in collected:
							collected.append(item)
							gui.dtm3_total += pctl.master_library[item].length
							if item == track.index:
								run = False
							if run:
								gui.dtm3_cum += pctl.master_library[item].length
				gui.dtm3_index = track.index

			x -= 4
			text_time = get_display_time(gui.dtm3_cum + pctl.playing_time)

			ddt.text(
				(x - 25 * gui.scale, y), text_time, colours.time_playing,
				fonts.bottom_panel_time)

			offset1 = 10 * gui.scale
			offset2 = offset1 + 7 * gui.scale

			ddt.text(
				(x + offset1, y), "/", colours.time_sub,
				fonts.bottom_panel_time)
			text_time = get_display_time(gui.dtm3_total)
			if pctl.playing_state == PlayingState.STOPPED:
				text_time = get_display_time(0)
			elif pctl.playing_state == PlayingState.URL_STREAM:
				text_time = "-- : --"
			ddt.text(
				(x + offset2, y), text_time, colours.time_sub,
				fonts.bottom_panel_time)

		# BUTTONS
		# bottom buttons

		if gui.mode == GuiMode.MAIN:
			# PLAY---
			buttons_x_offset = 0
			compact = False
			if window_size[0] < 650 * gui.scale:
				compact = True

			play_colour = mb_off
			pause_colour = mb_off
			stop_colour = mb_off
			forward_colour = mb_off
			back_colour = mb_off

			if pctl.playing_state == PlayingState.PLAYING:
				play_colour = mb_active

			if pctl.stop_mode != StopMode.OFF:
				stop_colour = mb_active

			if pctl.playing_state == PlayingState.PAUSED:
				pause_colour = mb_active
				play_colour = mb_active
			elif pctl.playing_state == PlayingState.URL_STREAM:
				play_colour = mb_active
				if tauon.stream_proxy.encode_running:
					play_colour = ColourRGBA(220, 50, 50, 255)

			if not compact or (compact and pctl.playing_state != PlayingState.PLAYING):
				rect = (
				buttons_x_offset + (10 * gui.scale), window_size[1] - self.control_line_bottom - (13 * gui.scale),
				50 * gui.scale, 40 * gui.scale)
				self.fields.add(rect)
				if self.coll(rect):
					play_colour = mb_over
					if inp.mouse_click:
						if compact and pctl.playing_state == PlayingState.PLAYING:
							pctl.pause()
						elif pctl.playing_state == PlayingState.PLAYING:
							pctl.show_current(highlight=True)
						else:
							pctl.play()
						inp.mouse_click = False
					tauon.tool_tip2.test(33 * gui.scale, y - 35 * gui.scale, _("Play, RC: Go to playing"))

					if inp.right_click:
						pctl.show_current(highlight=True)

				self.play_button.render(29 * gui.scale, window_size[1] - self.control_line_bottom, play_colour)
				# ddt.rect_r(rect,[255,0,0,255], True)

			# PAUSE---
			if compact:
				buttons_x_offset = -46 * gui.scale

			x = (75 * gui.scale) + buttons_x_offset
			y = window_size[1] - self.control_line_bottom

			if not compact or (compact and pctl.playing_state == PlayingState.PLAYING):

				rect = (x - 15 * gui.scale, y - 13 * gui.scale, 50 * gui.scale, 40 * gui.scale)
				self.fields.add(rect)
				if self.coll(rect) and pctl.playing_state != PlayingState.URL_STREAM:
					pause_colour = mb_over
					if inp.mouse_click:
						pctl.pause()
					if inp.right_click:
						pctl.show_current(highlight=True)
					tauon.tool_tip2.test(x, y - 35 * gui.scale, _("Pause"))

				# ddt.rect_r(rect,[255,0,0,255], True)
				ddt.rect_a((x, y + 0), (4 * gui.scale, 13 * gui.scale), pause_colour)
				ddt.rect_a((x + 10 * gui.scale, y + 0), (4 * gui.scale, 13 * gui.scale), pause_colour)

			# STOP---
			x = 125 * gui.scale + buttons_x_offset
			rect = (x - 14 * gui.scale, y - 13 * gui.scale, 50 * gui.scale, 40 * gui.scale)
			self.fields.add(rect)
			if self.coll(rect):
				stop_colour = mb_over
				if inp.mouse_click:
					pctl.stop()
				if inp.right_click:
					#pctl.auto_stop ^= True
					tauon.stop_menu.activate(position=(x - 0 * gui.scale, y - 6 * gui.scale))
				#tauon.tool_tip2.test(x, y - 35 * gui.scale, _("Stop, RC: Toggle auto-stop"))

			ddt.rect_a((x, y + 0), (13 * gui.scale, 13 * gui.scale), stop_colour)
			# ddt.rect_r(rect,[255,0,0,255], True)

			if compact:
				buttons_x_offset -= 5 * gui.scale

			# FORWARD---
			rect = (buttons_x_offset + 230 * gui.scale, window_size[1] - self.control_line_bottom - 10 * gui.scale,
					50 * gui.scale, 35 * gui.scale)
			self.fields.add(rect)
			if self.coll(rect) and pctl.playing_state != PlayingState.URL_STREAM:
				forward_colour = mb_over
				if inp.mouse_click:
					pctl.advance()
					gui.tool_tip_lock_off_f = True
				if inp.right_click:
					# pctl.random_mode ^= True
					tauon.toggle_random()
					gui.tool_tip_lock_off_f = True
					# if window_size[0] < 600 * gui.scale:
					# . Shuffle set to on
					gui.mode_toast_text = _("Shuffle On")
					if not pctl.random_mode:
						# . Shuffle set to off
						gui.mode_toast_text = _("Shuffle Off")
					tauon.toast_mode_timer.set()
					gui.delay_frame(1)
				if self.inp.middle_click:
					pctl.advance(rr=True)
					gui.tool_tip_lock_off_f = True
				# tauon.tool_tip.test(buttons_x_offset + 230 * gui.scale + 50 * gui.scale, window_size[1] - self.control_line_bottom - 20 * gui.scale, "Advance")
				# if not gui.tool_tip_lock_off_f:
				# 	tauon.tool_tip2.test(x + 45 * gui.scale, y - 35 * gui.scale, _("Forward, RC: Toggle shuffle, MC: Radio random"))
			else:
				gui.tool_tip_lock_off_f = False

			self.forward_button.render(
				buttons_x_offset + 240 * gui.scale, 1 + window_size[1] - self.control_line_bottom, forward_colour)

			# ddt.rect_r(rect,[255,0,0,255], True)

			# BACK---
			rect = (buttons_x_offset + 170 * gui.scale, window_size[1] - self.control_line_bottom - 10 * gui.scale,
					50 * gui.scale, 35 * gui.scale)
			self.fields.add(rect)
			if self.coll(rect) and pctl.playing_state != PlayingState.URL_STREAM:
				back_colour = mb_over
				if inp.mouse_click:
					pctl.back()
					gui.tool_tip_lock_off_b = True
				if inp.right_click:
					tauon.toggle_repeat()
					gui.tool_tip_lock_off_b = True
					# if window_size[0] < 600 * gui.scale:
					# . Repeat set to on
					gui.mode_toast_text = _("Repeat On")
					if not pctl.repeat_mode:
						# . Repeat set to off
						gui.mode_toast_text = _("Repeat Off")
					tauon.toast_mode_timer.set()
					gui.delay_frame(1)
				if self.inp.middle_click:
					pctl.revert()
					gui.tool_tip_lock_off_b = True
				if not gui.tool_tip_lock_off_b:
					tauon.tool_tip2.test(x, y - 35 * gui.scale, _("Back, RC: Toggle repeat, MC: Revert"))
			else:
				gui.tool_tip_lock_off_b = False

			self.back_button.render(buttons_x_offset + 180 * gui.scale, 1 + window_size[1] - self.control_line_bottom,
									back_colour)
			# ddt.rect_r(rect,[255,0,0,255], True)

			# menu button

			x = window_size[0] - 252 * gui.scale - right_offset
			y = window_size[1] - round(26 * gui.scale)
			rpbc = md_off
			rect = (x - 9 * gui.scale, y - 5 * gui.scale, 40 * gui.scale, 25 * gui.scale)
			self.fields.add(rect)
			if self.coll(rect):
				if not tauon.extra_menu.active:
					tauon.tool_tip.test(x, y - 28 * gui.scale, _("Playback menu"))
				rpbc = md_over
				if inp.mouse_click:
					tauon.extra_menu.activate(position=(x - 115 * gui.scale, y - 6 * gui.scale), bottom_anchor=True)
				elif inp.right_click:
					tauon.mode_menu.activate(position=(x - 115 * gui.scale, y - 6 * gui.scale))
			if tauon.extra_menu.active:
				rpbc = md_active

			spacing = round(5 * gui.scale)
			ddt.rect_a((x, y), (24 * gui.scale, 2 * gui.scale), rpbc)
			y += spacing
			ddt.rect_a((x, y), (24 * gui.scale, 2 * gui.scale), rpbc)
			y += spacing
			ddt.rect_a((x, y), (24 * gui.scale, 2 * gui.scale), rpbc)

			if self.mode == 0 and window_size[0] > 530 * gui.scale:

				# shuffle button
				x = window_size[0] - 318 * gui.scale - right_offset
				y = window_size[1] - 27 * gui.scale

				rect = (x - 5 * gui.scale, y - 5 * gui.scale, 60 * gui.scale, 25 * gui.scale)
				self.fields.add(rect)

				rpbc = md_off
				off = True
				if (inp.mouse_click or inp.right_click) and self.coll(rect):
					if inp.mouse_click:
						# pctl.random_mode ^= True
						tauon.toggle_random()
						if pctl.random_mode is False:
							self.random_click_off = True
					else:
						tauon.shuffle_menu.activate(position=(x + 30 * gui.scale, y - 7 * gui.scale))

				if pctl.random_mode:
					rpbc = md_active
					off = False
					if self.coll(rect):
						tauon.tool_tip.test(x, y - 28 * gui.scale, _("Shuffle"))
				elif self.coll(rect):
					tauon.tool_tip.test(x, y - 28 * gui.scale, _("Shuffle"))
					if self.random_click_off is True:
						rpbc = md_off
					elif pctl.random_mode is True:
						rpbc = md_active
					else:
						rpbc = md_over
				else:
					self.random_click_off = False

				# Keep hover highlight on if menu is open
				if tauon.shuffle_menu.active and not pctl.random_mode:
					rpbc = md_over

				#self.shuffle_button.render(x + round(1 * gui.scale), y + round(1 * gui.scale), rpbc)

				#y += round(3 * gui.scale)
				#ddt.rect_a((x, y), (25 * gui.scale, 3 * gui.scale), rpbc)

				icon_x_shift = round(2 * gui.scale)
				if pctl.album_shuffle_mode:
					self.shuffle_button_a.render(x + round(1 * gui.scale) + icon_x_shift, y + round(1 * gui.scale), rpbc)
				elif off:
					self.shuffle_button_off.render(x + round(1 * gui.scale) + icon_x_shift, y + round(1 * gui.scale), rpbc)
				else:
					self.shuffle_button.render(x + round(1 * gui.scale) + icon_x_shift, y + round(1 * gui.scale), rpbc)

					#ddt.rect_a((x + 25 * gui.scale, y), (23 * gui.scale, 3 * gui.scale), rpbc)

				#y += round(5 * gui.scale)
				#ddt.rect_a((x, y), (48 * gui.scale, 3 * gui.scale), rpbc)

				# REPEAT
				x = window_size[0] - round(380 * gui.scale) - right_offset
				y = window_size[1] - round(27 * gui.scale)

				rpbc = md_off
				off = True

				rect = (x - 6 * gui.scale, y - 5 * gui.scale, 61 * gui.scale, 25 * gui.scale)
				self.fields.add(rect)
				if (inp.mouse_click or inp.right_click) and self.coll(rect):
					if inp.mouse_click:
						tauon.toggle_repeat()
						if pctl.repeat_mode is False:
							self.repeat_click_off = True
					else:  # right click
						tauon.repeat_menu.activate(position=(x + 30 * gui.scale, y - 7 * gui.scale))
						# pctl.album_repeat_mode ^= True
						# if not pctl.repeat_mode:
						#     self.repeat_click_off = True

				if pctl.repeat_mode:
					rpbc = md_active
					off = False
					if self.coll(rect):
						if pctl.album_repeat_mode:
							tauon.tool_tip.test(x, y - 28 * gui.scale, _("Repeat album"))
						else:
							tauon.tool_tip.test(x, y - 28 * gui.scale, _("Repeat track"))
				elif self.coll(rect):

					# Tooltips. But don't show tooltips if menus open
					if not tauon.repeat_menu.active and not tauon.shuffle_menu.active:
						if pctl.album_repeat_mode:
							tauon.tool_tip.test(x, y - 28 * gui.scale, _("Repeat album"))
						else:
							tauon.tool_tip.test(x, y - 28 * gui.scale, _("Repeat track"))

					if self.repeat_click_off is True:
						rpbc = md_off
					elif pctl.repeat_mode is True:
						rpbc = md_active
					else:
						rpbc = md_over
				else:
					self.repeat_click_off = False

				# Keep hover highlight on if menu is open
				if tauon.repeat_menu.active and not pctl.repeat_mode:
					rpbc = md_over

				rpbc = alpha_blend(rpbc, colours.bottom_panel_colour)  # bake in alpha in case of overlap

				y += round(3 * gui.scale)
				w = round(3 * gui.scale)
				y = round(y)
				x = round(x)

				ar = x + round(50 * gui.scale)
				h = round(5 * gui.scale)

				if pctl.album_repeat_mode:
					self.repeat_button_a.render(ar - round(45 * gui.scale) + icon_x_shift, y - round(2 * gui.scale), rpbc)
					#ddt.rect_a((x + round(4 * gui.scale), y), (round(25 * gui.scale), w), rpbc)
				elif off:
					self.repeat_button_off.render(ar - round(45 * gui.scale) + icon_x_shift, y - round(2 * gui.scale), rpbc)
				else:
					self.repeat_button.render(ar - round(45 * gui.scale) + icon_x_shift, y - round(2 * gui.scale), rpbc)
class BottomBarType_ao1:
	def __init__(self, tauon: _PanelApp) -> None:
		self.tauon         = tauon
		self.ddt           = tauon.ddt
		self.gui           = tauon.gui
		self.inp           = tauon.inp
		self.coll          = tauon.coll
		self.pctl          = tauon.pctl
		self.fonts         = tauon.fonts
		self.prefs         = tauon.prefs
		self.fields        = tauon.fields
		self.colours       = tauon.colours
		self.renderer      = tauon.renderer
		self.window_size   = tauon.window_size
		self.smooth_scroll = tauon.smooth_scroll

		self.mode = 0
		self.seek_time = 0
		self.seek_down = False
		self.seek_hit = False
		self.volume_hit = False
		self.volume_bar_being_dragged = False
		self.control_line_bottom = 35 * self.gui.scale
		self.repeat_click_off = False
		self.random_click_off = False

		self.seek_bar_position = [300 * self.gui.scale, self.window_size[1] - self.gui.panelBY]
		self.seek_bar_size = [self.window_size[0] - (300 * self.gui.scale), 15 * self.gui.scale]
		self.volume_bar_size = [135 * self.gui.scale, 14 * self.gui.scale]
		self.volume_bar_position = [0, 45 * self.gui.scale]

		self.play_button    = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "play.png", True)
		self.forward_button = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "ff.png", True)
		self.back_button    = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "bb.png", True)

		self.scrob_stick = 0

	def update(self) -> None:
		if self.mode == 0:
			self.volume_bar_position[0] = self.window_size[0] - (210 * self.gui.scale)
			self.volume_bar_position[1] = self.window_size[1] - (27 * self.gui.scale)
			self.seek_bar_position[1]   = self.window_size[1] - self.gui.panelBY

			seek_bar_x = 300 * self.gui.scale
			if self.window_size[0] < 600 * self.gui.scale:
				seek_bar_x = 250 * self.gui.scale

			self.seek_bar_size[0] = self.window_size[0] - seek_bar_x
			self.seek_bar_position[0] = seek_bar_x

			# if gui.bb_show_art:
			#     self.seek_bar_position[0] = 300 + gui.panelBY
			#     self.seek_bar_size[0] = window_size[0] - 300 - gui.panelBY

			# self.seek_bar_position[0] = 0
			# self.seek_bar_size[0] = window_size[0]

	def render(self) -> None:

		# Replace pixels (for window transparency) unless the art background
		# is underneath, in which case blend over it
		if not self.gui.have_art_bg:
			sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_NONE)
		self.ddt.rect_a((0, self.window_size[1] - self.gui.panelBY), (self.window_size[0], self.gui.panelBY), self.colours.bottom_panel_colour)
		sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_BLEND)

		right_offset = 0
		if self.gui.display_time_mode >= 2:
			right_offset = 22 * self.gui.scale

		if self.window_size[0] < 670 * self.gui.scale:
			right_offset -= 90 * self.gui.scale

		# # MINI ALBUM ART
		# if gui.bb_show_art:
		# 	rect = [self.seek_bar_position[0] - gui.panelBY, self.seek_bar_position[1], gui.panelBY, gui.panelBY]
		# 	ddt.rect_r(rect, [255, 255, 255, 8], True)
		# 	if (self.pctl.playing_state in (PlayingState.PLAYING, PlayingState.PAUSED):
		# 		tauon.album_art_gen.display(pctl.track_queue[pctl.queue_step], (rect[0], rect[1]), (rect[2], rect[3]))

		# ddt.rect_r(rect, [255, 255, 255, 20])

		# Volume mouse wheel control -----------------------------------------
		if self.inp.mouse_wheel != 0 and self.inp.mouse_position[1] > self.seek_bar_position[1] + 4 and not coll_point(
			self.inp.mouse_position, self.seek_bar_position + self.seek_bar_size):
			scroll_distance = self.smooth_scroll.scroll("volume bar")
			self.pctl.player_volume += scroll_distance * self.prefs.volume_wheel_increment
			if self.pctl.player_volume < 1:
				self.pctl.player_volume = 0
			elif self.pctl.player_volume > 100:
				self.pctl.player_volume = 100

			self.pctl.player_volume = int(self.pctl.player_volume)
			self.pctl.set_volume()

		# mode menu
		if self.inp.right_click:
			if self.inp.mouse_position[0] > 190 * self.gui.scale and \
					self.inp.mouse_position[1] > self.window_size[1] - self.gui.panelBY and \
					self.inp.mouse_position[0] < self.window_size[0] - 190 * self.gui.scale:
				self.tauon.mode_menu.activate()

		# Volume Bar 2 ------------------------------------------------
		if True:
			x = self.window_size[0] - right_offset - 120 * self.gui.scale
			y = self.window_size[1] - round(21 * self.gui.scale)

			if self.gui.compact_bar:
				x -= 90 * self.gui.scale

			rect = (x - 8 * self.gui.scale, y - 17 * self.gui.scale, 55 * self.gui.scale, 23 * self.gui.scale)
			# ddt.rect(rect, [255,255,255,25])
			if self.coll(rect) and self.inp.mouse_down:
				self.gui.update_on_drag = True

			h_rect = (x - 6 * self.gui.scale, y - 17 * self.gui.scale, 4 * self.gui.scale, 23 * self.gui.scale)
			if self.coll(h_rect) and self.inp.mouse_down:
				self.pctl.player_volume = 0

			step = round(1 * self.gui.scale)
			min_h = round(4 * self.gui.scale)
			spacing = round(5 * self.gui.scale)

			if self.inp.right_click and self.coll((h_rect[0], h_rect[1], h_rect[2] + 50 * self.gui.scale, h_rect[3])):
				if self.inp.right_click:
					if self.pctl.player_volume > 0:
						self.pctl.volume_store = self.pctl.player_volume
						self.pctl.player_volume = 0
					else:
						self.pctl.player_volume = self.pctl.volume_store

					self.pctl.set_volume()

			for bar in range(8):
				h = min_h + bar * step
				rect = (x, y - h, 3 * self.gui.scale, h)
				h_rect = (x - 1 * self.gui.scale, y - 17 * self.gui.scale, 4 * self.gui.scale, 23 * self.gui.scale)

				if self.coll(h_rect) and self.inp.mouse_down:
					self.gui.update_on_drag = True

					if bar == 0:
						self.pctl.player_volume = 5
					if bar == 1:
						self.pctl.player_volume = 10
					if bar == 2:
						self.pctl.player_volume = 20
					if bar == 3:
						self.pctl.player_volume = 30
					if bar == 4:
						self.pctl.player_volume = 45
					if bar == 5:
						self.pctl.player_volume = 55
					if bar == 6:
						self.pctl.player_volume = 70
					if bar == 7:
						self.pctl.player_volume = 100

					self.pctl.set_volume()

				colour = self.colours.mode_button_off

				if bar == 0 and self.pctl.player_volume > 0:
					colour = self.colours.mode_button_active
				elif bar == 1 and self.pctl.player_volume >= 10:
					colour = self.colours.mode_button_active
				elif bar == 2 and self.pctl.player_volume >= 20:
					colour = self.colours.mode_button_active
				elif bar == 3 and self.pctl.player_volume >= 30:
					colour = self.colours.mode_button_active
				elif bar == 4 and self.pctl.player_volume >= 45:
					colour = self.colours.mode_button_active
				elif bar == 5 and self.pctl.player_volume >= 55:
					colour = self.colours.mode_button_active
				elif bar == 6 and self.pctl.player_volume >= 70:
					colour = self.colours.mode_button_active
				elif bar == 7 and self.pctl.player_volume >= 95:
					colour = self.colours.mode_button_active

				self.ddt.rect(rect, colour)
				x += spacing

		# TIME----------------------

		x = self.window_size[0] - 57 * self.gui.scale
		y = self.window_size[1] - 35 * self.gui.scale

		r_start = x - 10 * self.gui.scale
		if self.gui.display_time_mode in (2, 3):
			r_start -= 20 * self.gui.scale
		rect = (r_start, y - 3 * self.gui.scale, 80 * self.gui.scale, 27 * self.gui.scale)
		# ddt.rect_r(rect, [255, 0, 0, 40], True)
		if self.inp.mouse_click and self.coll(rect):
			self.gui.display_time_mode += 1
			if self.gui.display_time_mode > 3:
				self.gui.display_time_mode = 0

		if self.gui.display_time_mode == 0:
			text_time = get_display_time(self.pctl.playing_time)
			self.ddt.text((x + 1 * self.gui.scale, y), text_time, self.colours.time_playing, self.fonts.bottom_panel_time)
		elif self.gui.display_time_mode == 1:
			if self.pctl.playing_state == PlayingState.STOPPED:
				text_time = get_display_time(0)
			else:
				text_time = get_display_time(self.pctl.playing_length - self.pctl.playing_time)
			self.ddt.text((x + 1 * self.gui.scale, y), text_time, self.colours.time_playing, self.fonts.bottom_panel_time)
			self.ddt.text((x - 5 * self.gui.scale, y), "-", self.colours.time_playing, self.fonts.bottom_panel_time)
		elif self.gui.display_time_mode == 2:
			self.colours.time_sub = alpha_blend(ColourRGBA(255, 255, 255, 80), self.colours.bottom_panel_colour)

			x -= 4
			text_time = get_display_time(self.pctl.playing_time)
			self.ddt.text((x - 25 * self.gui.scale, y), text_time, self.colours.time_playing, self.fonts.bottom_panel_time)

			offset1 = 10 * self.gui.scale

			offset2 = offset1 + 7 * self.gui.scale

			self.ddt.text((x + offset1, y), "/", self.colours.time_sub, self.fonts.bottom_panel_time)
			text_time = get_display_time(self.pctl.playing_length)
			if self.pctl.playing_state == PlayingState.STOPPED:
				text_time = get_display_time(0)
			elif self.pctl.playing_state == PlayingState.URL_STREAM:
				text_time = "-- : --"
			self.ddt.text((x + offset2, y), text_time, self.colours.time_sub, self.fonts.bottom_panel_time)

		elif self.gui.display_time_mode == PlayingState.URL_STREAM:
			self.colours.time_sub = alpha_blend(ColourRGBA(255, 255, 255, 80), self.colours.bottom_panel_colour)

			track = self.pctl.playing_object()
			if track and track.index != self.gui.dtm3_index:

				self.gui.dtm3_cum = 0
				self.gui.dtm3_total = 0
				run = True
				collected = []
				for item in self.pctl.default_playlist:
					if self.pctl.master_library[item].parent_folder_path == track.parent_folder_path:
						if item not in collected:
							collected.append(item)
							self.gui.dtm3_total += self.pctl.master_library[item].length
							if item == track.index:
								run = False
							if run:
								self.gui.dtm3_cum += self.pctl.master_library[item].length
				self.gui.dtm3_index = track.index

			x -= 4
			text_time = get_display_time(self.gui.dtm3_cum + self.pctl.playing_time)

			self.ddt.text((x - 25 * self.gui.scale, y), text_time, self.colours.time_playing, self.fonts.bottom_panel_time)

			offset1 = 10 * self.gui.scale
			offset2 = offset1 + 7 * self.gui.scale

			self.ddt.text((x + offset1, y), "/", self.colours.time_sub, self.fonts.bottom_panel_time)
			text_time = get_display_time(self.gui.dtm3_total)
			if self.pctl.playing_state == PlayingState.STOPPED:
				text_time = get_display_time(0)
			elif self.pctl.playing_state == PlayingState.URL_STREAM:
				text_time = "-- : --"
			self.ddt.text((x + offset2, y), text_time, self.colours.time_sub, self.fonts.bottom_panel_time)

		# BUTTONS
		# bottom buttons

		if self.gui.mode == GuiMode.MAIN:
			# PLAY---
			buttons_x_offset = 0
			compact = False
			if self.window_size[0] < 650 * self.gui.scale:
				compact = True

			play_colour = self.colours.media_buttons_off
			pause_colour = self.colours.media_buttons_off
			stop_colour = self.colours.media_buttons_off
			forward_colour = self.colours.media_buttons_off
			back_colour = self.colours.media_buttons_off

			if self.pctl.playing_state == PlayingState.PLAYING:
				play_colour = self.colours.media_buttons_active

			if self.pctl.stop_mode != StopMode.OFF:
				stop_colour = self.colours.media_buttons_active

			if self.pctl.playing_state == PlayingState.PAUSED:
				pause_colour = self.colours.media_buttons_active
				play_colour = self.colours.media_buttons_active
			elif self.pctl.playing_state == PlayingState.URL_STREAM:
				play_colour = self.colours.media_buttons_active
				if self.pctl.record_stream:
					play_colour = ColourRGBA(220, 50, 50, 255)

			if not compact or (compact and self.pctl.playing_state != PlayingState.PAUSED):
				rect = (
				buttons_x_offset + (10 * self.gui.scale), self.window_size[1] - self.control_line_bottom - (13 * self.gui.scale),
				50 * self.gui.scale, 40 * self.gui.scale)
				self.fields.add(rect)
				if self.coll(rect):
					play_colour = self.colours.media_buttons_over
					if self.inp.mouse_click:
						if compact and self.pctl.playing_state == PlayingState.PLAYING:
							self.pctl.pause()
						elif self.pctl.playing_state == PlayingState.PLAYING:
							self.pctl.show_current(highlight=True)
						else:
							self.pctl.play()
						self.inp.mouse_click = False
					self.tauon.tool_tip2.test(33 * self.gui.scale, y - 35 * self.gui.scale, _("Play, RC: Go to playing"))

					if self.inp.right_click:
						self.pctl.show_current(highlight=True)

				self.play_button.render(29 * self.gui.scale, self.window_size[1] - self.control_line_bottom, play_colour)
				# self.ddt.rect_r(rect,[255,0,0,255], True)

			# PAUSE---
			if compact:
				buttons_x_offset = -46 * self.gui.scale

			x = (75 * self.gui.scale) + buttons_x_offset
			y = self.window_size[1] - self.control_line_bottom

			if not compact or (compact and self.pctl.playing_state == PlayingState.PAUSED):

				rect = (x - 15 * self.gui.scale, y - 13 * self.gui.scale, 50 * self.gui.scale, 40 * self.gui.scale)
				self.fields.add(rect)
				if self.coll(rect) and self.pctl.playing_state != PlayingState.URL_STREAM:
					pause_colour = self.colours.media_buttons_over
					if self.inp.mouse_click:
						self.pctl.pause()
					if self.inp.right_click:
						self.pctl.show_current(highlight=True)
					self.tauon.tool_tip2.test(x, y - 35 * self.gui.scale, _("Pause"))

				# self.ddt.rect_r(rect,[255,0,0,255], True)
				self.ddt.rect_a((x, y + 0), (4 * self.gui.scale, 13 * self.gui.scale), pause_colour)
				self.ddt.rect_a((x + 10 * self.gui.scale, y + 0), (4 * self.gui.scale, 13 * self.gui.scale), pause_colour)

			# FORWARD---
			rect = (
				buttons_x_offset + 125 * self.gui.scale,
				self.window_size[1] - self.control_line_bottom - 10 * self.gui.scale, 50 * self.gui.scale, 35 * self.gui.scale)
			self.fields.add(rect)
			if self.coll(rect) and self.pctl.playing_state != PlayingState.URL_STREAM:
				forward_colour = self.colours.media_buttons_over
				if self.inp.mouse_click:
					self.pctl.advance()
					self.gui.tool_tip_lock_off_f = True
				if self.inp.right_click:
					# self.pctl.random_mode ^= True
					self.tauon.toggle_random()
					self.gui.tool_tip_lock_off_f = True
					# if self.window_size[0] < 600 * self.gui.scale:
					# . Shuffle set to on
					self.gui.mode_toast_text = _("Shuffle On")
					if not self.pctl.random_mode:
						# . Shuffle set to off
						self.gui.mode_toast_text = _("Shuffle Off")
					self.tauon.toast_mode_timer.set()
					self.gui.delay_frame(1)
				if self.inp.middle_click:
					self.pctl.advance(rr=True)
					self.gui.tool_tip_lock_off_f = True
				# tool_tip.test(buttons_x_offset + 230 * self.gui.scale + 50 * self.gui.scale, self.window_size[1] - self.control_line_bottom - 20 * self.gui.scale, "Advance")
				# if not self.gui.tool_tip_lock_off_f:
				# 	tauon.tool_tip2.test(x + 45 * self.gui.scale, y - 35 * self.gui.scale, _("Forward, RC: Toggle shuffle, MC: Radio random"))
			else:
				self.gui.tool_tip_lock_off_f = False

			self.forward_button.render(
				buttons_x_offset + 125 * self.gui.scale,
				1 + self.window_size[1] - self.control_line_bottom, forward_colour)
class MiniMode:
	def __init__(self, tauon: _PanelApp) -> None:
		self.tauon         = tauon
		self.ddt           = tauon.ddt
		self.inp           = tauon.inp
		self.gui           = tauon.gui
		self.coll          = tauon.coll
		self.pctl          = tauon.pctl
		self.prefs         = tauon.prefs
		self.fields        = tauon.fields
		self.colours       = tauon.colours
		self.window_size   = tauon.window_size
		self.album_art_gen = tauon.album_art_gen
		self.smooth_scroll = tauon.smooth_scroll
		self.save_position = None
		self.was_borderless = True
		self.volume_timer = Timer()
		self.volume_timer.force_set(100)

		self.left_slide  = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "left-slide.png", True)
		self.right_slide = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "right-slide.png", True)
		self.repeat      = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "repeat-mini-mode.png", True)
		self.shuffle     = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "shuffle-mini-mode.png", True)

		self.shuffle_fade_timer = Timer(100)
		self.repeat_fade_timer = Timer(100)

	def render(self) -> None:
		# We only set seek_r and seek_w if track is currently on, but use it anyway later, so make sure it exists
		if "seek_r" not in locals():
			seek_r = [0, 0, 0, 0]
			seek_w = 0

		w = self.window_size[0]
		h = self.window_size[1]

		y1 = w
		if w == h:
			y1 -= 79 * self.gui.scale

		h1 = h - y1

		# Draw background
		bg = self.colours.mini_mode_background
		# bg = ColourRGBA(250, 250, 250, 255)

		self.ddt.rect((0, 0, w, h), bg)
		self.ddt.text_background_colour = bg

		detect_mouse_rect = (3, 3, w - 6, h - 6)
		self.fields.add(detect_mouse_rect)
		mouse_in = self.coll(detect_mouse_rect)

		# Play / Pause when right clicking below art
		if self.inp.right_click:  # and self.inp.mouse_position[1] > y1:
			self.pctl.play_pause()

		# Volume change on scroll
		if self.inp.mouse_wheel != 0:
			self.volume_timer.set()
			scroll_distance = self.smooth_scroll.scroll("volume bar")
			self.pctl.player_volume += scroll_distance * self.prefs.volume_wheel_increment * 3
			if self.pctl.player_volume < 1:
				self.pctl.player_volume = 0
			elif self.pctl.player_volume > 100:
				self.pctl.player_volume = 100

			self.pctl.player_volume = int(self.pctl.player_volume)
			self.pctl.set_volume()

		track = self.pctl.playing_object()

		control_hit_area = (3, y1 - 15 * self.gui.scale, w - 6, h1 - 3 + 15 * self.gui.scale)
		mouse_in_area = self.coll(control_hit_area)
		self.fields.add(control_hit_area)

		self.ddt.rect((0, 0, w, w), ColourRGBA(0, 0, 0, 45))
		if track is not None:
			# Render album art
			self.album_art_gen.display(track, (0, 0), (w, w))

			line1c = self.colours.mini_mode_text_1
			line2c = self.colours.mini_mode_text_2

			if h == w and mouse_in_area:
				# self.ddt.pretty_rect = (0, 260 * self.gui.scale, w, 100 * self.gui.scale)
				self.ddt.rect((0, y1, w, h1), ColourRGBA(0, 0, 0, 220))
				line1c = ColourRGBA(255, 255, 255, 240)
				line2c = ColourRGBA(255, 255, 255, 77)

			# Double click bottom text to return to full window
			text_hit_area = (60 * self.gui.scale, y1 + 4, 230 * self.gui.scale, 50 * self.gui.scale)

			if self.coll(text_hit_area) and self.inp.mouse_click:
				if self.tauon.d_click_timer.get() < 0.3:
					self.tauon.restore_full_mode()
					self.gui.request_frame()
					return
				self.tauon.d_click_timer.set()

			# Draw title texts
			line1 = track.artist
			line2 = track.title

			# Calculate seek bar position
			seek_w = int(w * 0.70)

			seek_r = [(w - seek_w) // 2, y1 + 58 * self.gui.scale, seek_w, 6 * self.gui.scale]
			seek_marker_rect = tuple(seek_r)
			seek_r_hit = [seek_r[0], seek_r[1] - 4 * self.gui.scale, seek_r[2], seek_r[3] + 8 * self.gui.scale]

			if w != h or mouse_in_area:

				if not line1 and not line2:
					self.ddt.text((w // 2, y1 + 18 * self.gui.scale, 2), track.filename, line1c, 214, self.window_size[0] - 30 * self.gui.scale)
				else:
					self.ddt.text((w // 2, y1 + 10 * self.gui.scale, 2), line1, line2c, 514, self.window_size[0] - 30 * self.gui.scale)
					self.ddt.text((w // 2, y1 + 31 * self.gui.scale, 2), line2, line1c, 414, self.window_size[0] - 30 * self.gui.scale)

				# Test click to seek
				if self.inp.mouse_up and self.coll(seek_r_hit):
					click_x = self.inp.mouse_position[0]
					click_x = min(click_x, seek_r[0] + seek_r[2])
					click_x = max(click_x, seek_r[0])
					click_x -= seek_r[0]

					if click_x < 6 * self.gui.scale:
						click_x = 0
					seek = click_x / seek_r[2]

					self.pctl.seek_decimal(seek)

				# Draw progress bar background
				self.ddt.rect(seek_r, ColourRGBA(255, 255, 255, 32))

				# Calculate and draw bar foreground
				progress_w = 0
				if self.pctl.playing_length > 1:
					progress_w = self.pctl.playing_time * seek_w / self.pctl.playing_length
				seek_colour = ColourRGBA(210, 210, 210, 255)
				if self.gui.theme_name == "Carbon":
					seek_colour = self.colours.bottom_panel_colour

				if self.pctl.playing_state != PlayingState.PLAYING:
					seek_colour = ColourRGBA(210, 40, 100, 255)

				seek_r[2] = progress_w

				if self.volume_timer.get() < 0.9:
					progress_w = self.pctl.player_volume * (seek_w - (4 * self.gui.scale)) / 100
					self.gui.request_frame()
					seek_colour = ColourRGBA(210, 210, 210, 255)
					seek_r[2] = progress_w
					seek_r[0] += 2 * self.gui.scale
					seek_r[1] += 2 * self.gui.scale
					seek_r[3] -= 4 * self.gui.scale

				self.ddt.rect(seek_r, seek_colour)
				self.tauon.draw_ab_repeat_markers(*seek_marker_rect)

		left_area = (1, y1, seek_r[0] - 1, 45 * self.gui.scale)
		right_area = (seek_r[0] + seek_w, y1, seek_r[0] - 2, 45 * self.gui.scale)

		self.fields.add(left_area)
		self.fields.add(right_area)

		hint = 0
		if self.coll(control_hit_area):
			hint = 30
		if self.coll(left_area):
			hint = 240
		if hint and not self.prefs.shuffle_lock:
			self.left_slide.render(16 * self.gui.scale, y1 + 17 * self.gui.scale, ColourRGBA(255, 255, 255, hint))

		hint = 0
		if self.coll(control_hit_area):
			hint = 30
		if self.coll(right_area):
			hint = 240
		if hint:
			self.right_slide.render(
				self.window_size[0] - self.right_slide.w - 16 * self.gui.scale, y1 + 17 * self.gui.scale,
				ColourRGBA(255, 255, 255, hint))

		# Shuffle

		shuffle_area = (seek_r[0] + seek_w, seek_r[1] - 10 * self.gui.scale, 50 * self.gui.scale, 30 * self.gui.scale)
		# self.fields.add(shuffle_area)
		# self.ddt.rect_r(shuffle_area, [255, 0, 0, 100], True)

		if self.coll(control_hit_area) and not self.prefs.shuffle_lock:
			colour = ColourRGBA(255, 255, 255, 20)
			if self.inp.mouse_click and self.coll(shuffle_area):
				# self.pctl.random_mode ^= True
				self.tauon.toggle_random()
			if self.pctl.random_mode:
				colour = ColourRGBA(255, 255, 255, 190)

			sx = seek_r[0] + seek_w + 12 * self.gui.scale
			sy = seek_r[1] - 2 * self.gui.scale
			self.shuffle.render(sx, sy, colour)


			# sx = seek_r[0] + seek_w + 8 * self.gui.scale
			# sy = seek_r[1] - 1 * self.gui.scale
			# self.ddt.rect_a((sx, sy), (14 * self.gui.scale, 2 * self.gui.scale), colour)
			# sy += 4 * self.gui.scale
			# self.ddt.rect_a((sx, sy), (28 * self.gui.scale, 2 * self.gui.scale), colour)

		shuffle_area = (seek_r[0] - 41 * self.gui.scale, seek_r[1] - 10 * self.gui.scale, 40 * self.gui.scale, 30 * self.gui.scale)
		if self.coll(control_hit_area) and not self.prefs.shuffle_lock:
			colour = ColourRGBA(255, 255, 255, 20)
			if self.inp.mouse_click and self.coll(shuffle_area):
				self.tauon.toggle_repeat()
			if self.pctl.repeat_mode:
				colour = ColourRGBA(255, 255, 255, 190)


			sx = seek_r[0] - 36 * self.gui.scale
			sy = seek_r[1] - 1 * self.gui.scale
			self.repeat.render(sx, sy, colour)


			# sx = seek_r[0] - 39 * self.gui.scale
			# sy = seek_r[1] - 1 * self.gui.scale

			#tw = 2 * self.gui.scale
			# self.ddt.rect_a((sx + 15 * self.gui.scale, sy), (13 * self.gui.scale, tw), colour)
			# self.ddt.rect_a((sx + 4 * self.gui.scale, sy + 4 * self.gui.scale), (25 * self.gui.scale, tw), colour)
			# self.ddt.rect_a((sx + 30 * self.gui.scale - tw, sy), (tw, 6 * self.gui.scale), colour)


		# Forward and back clicking
		if self.inp.mouse_click:
			if self.coll(left_area) and not self.prefs.shuffle_lock:
				self.pctl.back()
			if self.coll(right_area):
				self.pctl.advance()

		# Show exit/min buttons when mouse over
		tool_rect = [self.window_size[0] - 110 * self.gui.scale, 2, 108 * self.gui.scale, 45 * self.gui.scale]
		if self.prefs.left_window_control:
			tool_rect[0] = 0
		self.fields.add(tool_rect)
		if self.coll(tool_rect):
			self.tauon.draw_window_tools()

		if w != h:
			self.ddt.rect_s((1, 1, w - 2, h - 2), self.colours.mini_mode_border, 1 * self.gui.scale)
			if self.gui.scale == 2:
				self.ddt.rect_s((2, 2, w - 4, h - 4), self.colours.mini_mode_border, 1 * self.gui.scale)
class MiniMode2:
	def __init__(self, tauon: _PanelApp) -> None:
		self.tauon         = tauon
		self.ddt           = tauon.ddt
		self.inp           = tauon.inp
		self.gui           = tauon.gui
		self.coll          = tauon.coll
		self.pctl          = tauon.pctl
		self.prefs         = tauon.prefs
		self.fields        = tauon.fields
		self.colours       = tauon.colours
		self.window_size   = tauon.window_size
		self.album_art_gen = tauon.album_art_gen
		self.smooth_scroll = tauon.smooth_scroll
		self.save_position = None
		self.was_borderless = True
		self.volume_timer = Timer()
		self.volume_timer.force_set(100)

		self.left_slide  = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "left-slide.png", True)
		self.right_slide = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "right-slide.png", True)

	def render(self) -> None:
		w = self.window_size[0]
		h = self.window_size[1]

		x1 = h

		# Draw background
		self.ddt.rect((0, 0, w, h), self.colours.mini_mode_background)
		self.ddt.text_background_colour = self.colours.mini_mode_background

		detect_mouse_rect = (2, 2, w - 4, h - 4)
		self.fields.add(detect_mouse_rect)
		mouse_in = self.coll(detect_mouse_rect)

		# Play / Pause when right clicking below art
		if self.inp.right_click:  # and self.inp.mouse_position[1] > y1:
			self.pctl.play_pause()

		# Volume change on scroll
		if self.inp.mouse_wheel != 0:
			self.volume_timer.set()
			scroll_distance = self.smooth_scroll.scroll("volume bar")
			self.pctl.player_volume += scroll_distance * self.prefs.volume_wheel_increment * 3
			if self.pctl.player_volume < 1:
				self.pctl.player_volume = 0
			elif self.pctl.player_volume > 100:
				self.pctl.player_volume = 100

			self.pctl.player_volume = int(self.pctl.player_volume)
			self.pctl.set_volume()

		track = self.pctl.playing_object()

		if track is not None:
			# Render album art
			self.album_art_gen.display(track, (0, 0), (h, h))

			text_hit_area = (x1, 0, w, h)

			if self.coll(text_hit_area) and self.inp.mouse_click:
				if self.tauon.d_click_timer.get() < 0.3:
					self.tauon.restore_full_mode()
					self.gui.request_frame()
					return
				self.tauon.d_click_timer.set()

			# Draw title texts
			line1 = track.artist
			line2 = track.title

			if not line1 and not line2:

				self.ddt.text(
					(x1 + 15 * self.gui.scale, 44 * self.gui.scale), track.filename, self.colours.grey(150), 315,
					self.window_size[0] - x1 - 30 * self.gui.scale)
			else:
				# if self.ddt.get_text_w(line2, 215) > window_size[0] - x1 - 30 * self.gui.scale:
				#     self.ddt.text((x1 + 15 * self.gui.scale, 19 * self.gui.scale), line2, self.colours.grey(249), 413,
				#              window_size[0] - x1 - 35 * self.gui.scale)
				#
				#     self.ddt.text((x1 + 15 * self.gui.scale, 43 * self.gui.scale), line1, self.colours.grey(110), 513,
				#              window_size[0] - x1 - 35 * self.gui.scale)
				# else:

				self.ddt.text(
					(x1 + 15 * self.gui.scale, 18 * self.gui.scale), line2, self.colours.grey(249), 514,
					self.window_size[0] - x1 - 30 * self.gui.scale)

				self.ddt.text(
					(x1 + 15 * self.gui.scale, 43 * self.gui.scale), line1, self.colours.grey(110), 514,
					self.window_size[0] - x1 - 30 * self.gui.scale)

		# Show exit/min buttons when mouse over
		tool_rect = [self.window_size[0] - 110 * self.gui.scale, 2, 108 * self.gui.scale, 45 * self.gui.scale]
		if self.prefs.left_window_control:
			tool_rect[0] = 0
		self.fields.add(tool_rect)
		if self.coll(tool_rect):
			self.tauon.draw_window_tools()

		# Seek bar
		bg_rect = (h, h - round(5 * self.gui.scale), w - h, round(5 * self.gui.scale))
		self.ddt.rect(bg_rect, ColourRGBA(255, 255, 255, 18))

		if self.pctl.playing_state != PlayingState.STOPPED:
			hit_rect = h - 5 * self.gui.scale, h - 12 * self.gui.scale, w - h + 5 * self.gui.scale, 13 * self.gui.scale

			if self.coll(hit_rect) and self.inp.mouse_up:
				p = (self.inp.mouse_position[0] - h) / (w - h)

				if p < 0 or self.inp.mouse_position[0] - h < 6 * self.gui.scale:
					self.pctl.seek_time(0)
				elif p > .96:
					self.pctl.advance()
				else:
					self.pctl.seek_decimal(p)

			if self.pctl.playing_length:
				seek_rect = (
					h, h - round(5 * self.gui.scale), round((w - h) * (self.pctl.playing_time / self.pctl.playing_length)),
					round(5 * self.gui.scale))
				colour = self.colours.artist_text
				if self.gui.theme_name == "Carbon":
					colour = self.colours.bottom_panel_colour
				if self.pctl.playing_state != PlayingState.PLAYING:
					colour = ColourRGBA(210, 40, 100, 255)
				self.ddt.rect(seek_rect, colour)

		self.tauon.draw_ab_repeat_markers(*bg_rect)
class MiniMode3:
	def __init__(self, tauon: _PanelApp) -> None:
		self.tauon         = tauon
		self.ddt           = tauon.ddt
		self.inp           = tauon.inp
		self.gui           = tauon.gui
		self.coll          = tauon.coll
		self.pctl          = tauon.pctl
		self.prefs         = tauon.prefs
		self.fields        = tauon.fields
		self.colours       = tauon.colours
		self.window_size   = tauon.window_size
		self.album_art_gen = tauon.album_art_gen
		self.smooth_scroll = tauon.smooth_scroll
		self.save_position = None
		self.was_borderless = True
		self.volume_timer = Timer()
		self.volume_timer.force_set(100)

		self.left_slide  = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "left-slide.png", True)
		self.right_slide = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "right-slide.png", True)

		self.shuffle_fade_timer = Timer(100)
		self.repeat_fade_timer = Timer(100)

	def render(self) -> None:
		# We only set seek_r and seek_w if track is currently on, but use it anyway later, so make sure it exists
		if "seek_r" not in locals():
			seek_r = [0, 0, 0, 0]
			seek_w = 0
			volume_r = [0, 0, 0, 0]
			volume_w = 0

		w = self.window_size[0]
		h = self.window_size[1]

		y1 = w #+ 10 * gui.scale
		# if w == h:
		#     y1 -= 79 * gui.scale

		h1 = h - y1

		track = self.pctl.playing_object()
		wid = (w // 2) + round(60 * self.gui.scale)
		ins = (self.window_size[0] - wid) / 2
		art_rect = sdl3.SDL_FRect(round(ins), round(ins), round(wid), round(wid))
		self.tauon.style_overlay.hole_punches.clear()
		if track is not None:
			self.tauon.style_overlay.hole_punches.append(art_rect)

		# Draw background
		bg = self.colours.mini_mode_background
		# bg = [250, 250, 250, 255]

		self.ddt.rect((0, 0, w, h), bg)

		self.tauon.style_overlay.display()

		transit = False
		#self.ddt.text_background_colour = list(gui.center_blur_pixel) + [255,] #bg
		if self.tauon.style_overlay.fade_on_timer.get() < 0.4 or self.tauon.style_overlay.stage != 2:
			self.ddt.alpha_bg = True
			transit = True

		detect_mouse_rect = (3, 3, w - 6, h - 6)
		self.fields.add(detect_mouse_rect)
		mouse_in = self.coll(detect_mouse_rect)

		# Play / Pause when right clicking below art
		if self.inp.right_click:  # and self.inp.mouse_position[1] > y1:
			self.pctl.play_pause()

		# Volume change on scroll
		if self.inp.mouse_wheel != 0:
			self.volume_timer.set()
			scroll_distance = self.smooth_scroll.scroll("volume bar")
			self.pctl.player_volume += scroll_distance * self.prefs.volume_wheel_increment * 3
			if self.pctl.player_volume < 1:
				self.pctl.player_volume = 0
			elif self.pctl.player_volume > 100:
				self.pctl.player_volume = 100

			self.pctl.player_volume = int(self.pctl.player_volume)
			self.pctl.set_volume()

		control_hit_area = (3, y1 - 15 * self.gui.scale, w - 6, h1 - 3 + 15 * self.gui.scale)
		mouse_in_area = self.coll(control_hit_area)
		self.fields.add(control_hit_area)

		#self.ddt.rect((0, 0, w, w), (0, 0, 0, 45))
		if track is not None:

			# Render album art

			off = round(4 * self.gui.scale)

			self.tauon.drop_shadow.render(ins + off, ins + off, wid + off * 2, wid + off * 2)
			self.ddt.rect((ins + 1, ins + 1, wid - 1, wid - 1), ColourRGBA(20, 20, 20, 255))
			self.album_art_gen.display(track, (ins, ins), (wid, wid))

			line1c = ColourRGBA(255, 255, 255, 255) #self.colours.mini_mode_text_1
			line2c = ColourRGBA(255, 255, 255, 255) #self.colours.mini_mode_text_2

			# if h == w and mouse_in_area:
			# 	# self.ddt.pretty_rect = (0, 260 * self.gui.scale, w, 100 * self.gui.scale)
			# 	self.ddt.rect((0, y1, w, h1), [0, 0, 0, 220])
			# 	line1c = [255, 255, 255, 240]
			# 	line2c = [255, 255, 255, 77]

			# Double click bottom text to return to full window
			text_hit_area = (60 * self.gui.scale, y1 + 4, 230 * self.gui.scale, 50 * self.gui.scale)

			if self.coll(text_hit_area) and self.inp.mouse_click:
				if self.tauon.d_click_timer.get() < 0.3:
					self.tauon.restore_full_mode()
					self.gui.request_frame()
					return
				self.tauon.d_click_timer.set()

			# Draw title texts
			line1 = track.artist
			line2 = track.title
			key = None
			if not line1 and not line2:
				if not self.ddt.alpha_bg:
					key = (track.filename, 214, self.tauon.style_overlay.current_track_id)
				self.ddt.text(
					(w // 2, y1 + 18 * self.gui.scale, 2), track.filename, line1c, 214,
					self.window_size[0] - 30 * self.gui.scale, real_bg=not transit, key=key)
			else:
				if not self.ddt.alpha_bg:
					key = (line1, 515, self.tauon.style_overlay.current_track_id)
				self.ddt.text(
					(w // 2, y1 + 5 * self.gui.scale, 2), line1, line2c, 515,
					self.window_size[0] - 30 * self.gui.scale, real_bg=not transit, key=key)
				if not self.ddt.alpha_bg:
					key = (line2, 415, self.tauon.style_overlay.current_track_id)
				self.ddt.text(
					(w // 2, y1 + 31 * self.gui.scale, 2), line2, line1c, 415,
					self.window_size[0] - 30 * self.gui.scale, real_bg=not transit, key=key)

			y1 += round(10 * self.gui.scale)

			# Calculate seek bar position
			seek_w = int(w * 0.80)

			seek_r = [(w - seek_w) // 2, y1 + 58 * self.gui.scale, seek_w, 9 * self.gui.scale]
			seek_marker_rect = tuple(seek_r)
			seek_r_hit = [seek_r[0], seek_r[1] - 5 * self.gui.scale, seek_r[2], seek_r[3] + 12 * self.gui.scale]

			if w != h or mouse_in_area:
				# Test click to seek
				if self.inp.mouse_up and self.coll(seek_r_hit):
					click_x = self.inp.mouse_position[0]
					click_x = min(click_x, seek_r[0] + seek_r[2])
					click_x = max(click_x, seek_r[0])
					click_x -= seek_r[0]

					if click_x < 6 * self.gui.scale:
						click_x = 0
					seek = click_x / seek_r[2]

					self.pctl.seek_decimal(seek)

				# Draw progress bar background
				self.ddt.rect(seek_r, ColourRGBA(255, 255, 255, 32))

				# Calculate and draw bar foreground
				progress_w = 0
				if self.pctl.playing_length > 1:
					progress_w = self.pctl.playing_time * seek_w / self.pctl.playing_length
				seek_colour = ColourRGBA(210, 210, 210, 255)
				if self.gui.theme_name == "Carbon":
					seek_colour = self.colours.bottom_panel_colour

				if self.pctl.playing_state != PlayingState.PLAYING:
					seek_colour = ColourRGBA(210, 40, 100, 255)

				seek_r[2] = progress_w

			self.ddt.rect(seek_r, seek_colour)
			self.tauon.draw_ab_repeat_markers(*seek_marker_rect)

			volume_w = int(w * 0.50)
			volume_r = [(w - volume_w) // 2, y1 + 80 * self.gui.scale, volume_w, 6 * self.gui.scale]
			volume_r_hit = [volume_r[0], volume_r[1] - 5 * self.gui.scale, volume_r[2], volume_r[3] + 10 * self.gui.scale]

			# Test click to volume
			if (self.inp.mouse_up or self.inp.mouse_down) and self.coll(volume_r_hit):
				self.gui.update_on_drag = True
				click_x = self.inp.mouse_position[0]
				click_x = min(click_x, volume_r[0] + volume_r[2])
				click_x = max(click_x, volume_r[0])
				click_x -= volume_r[0]

				if click_x < 6 * self.gui.scale:
					click_x = 0
				volume = click_x / volume_r[2]

				self.pctl.player_volume = int(volume * 100)
				self.pctl.set_volume()

			self.ddt.rect(volume_r, ColourRGBA(255, 255, 255, 32))

			#if self.volume_timer.get() < 0.9:
			progress_w = self.pctl.player_volume * (volume_w - (4 * self.gui.scale)) / 100
			volume_colour = ColourRGBA(210, 210, 210, 255)
			volume_r[2] = progress_w
			volume_r[0] += 2 * self.gui.scale
			volume_r[1] += 2 * self.gui.scale
			volume_r[3] -= 4 * self.gui.scale

			self.ddt.rect(volume_r, volume_colour)


		left_area = (1, y1, volume_r[0] - 1, 45 * self.gui.scale)
		right_area = (volume_r[0] + volume_w, y1, volume_r[0] - 2, 45 * self.gui.scale)

		self.fields.add(left_area)
		self.fields.add(right_area)

		hint = 0
		if True: #self.coll(control_hit_area):
			hint = 30
		if self.coll(left_area):
			hint = 240
		if hint and not self.prefs.shuffle_lock:
			self.left_slide.render(16 * self.gui.scale, y1 + 10 * self.gui.scale, ColourRGBA(255, 255, 255, hint))

		hint = 0
		if True: #self.coll(control_hit_area):
			hint = 30
		if self.coll(right_area):
			hint = 240
		if hint:
			self.right_slide.render(
				self.window_size[0] - self.right_slide.w - 16 * self.gui.scale, y1 + 10 * self.gui.scale, ColourRGBA(255, 255, 255, hint))

		# Shuffle
		shuffle_area = (volume_r[0] + volume_w, volume_r[1] - 10 * self.gui.scale, 50 * self.gui.scale, 30 * self.gui.scale)
		# self.fields.add(shuffle_area)
		# self.ddt.rect_r(shuffle_area, [255, 0, 0, 100], True)

		if True: #self.coll(control_hit_area) and not self.prefs.shuffle_lock:
			colour = ColourRGBA(255, 255, 255, 20)
			if self.inp.mouse_click and self.coll(shuffle_area):
				# self.pctl.random_mode ^= True
				self.tauon.toggle_random()
			if self.pctl.random_mode:
				colour = ColourRGBA(255, 255, 255, 190)

			sx = volume_r[0] + volume_w + 12 * self.gui.scale
			sy = volume_r[1] - 3 * self.gui.scale
			self.tauon.mini_mode.shuffle.render(sx, sy, colour)

			#
			# sx = volume_r[0] + volume_w + 8 * self.gui.scale
			# sy = volume_r[1] - 1 * self.gui.scale
			# self.ddt.rect_a((sx, sy), (14 * self.gui.scale, 2 * self.gui.scale), colour)
			# sy += 4 * self.gui.scale
			# self.ddt.rect_a((sx, sy), (28 * self.gui.scale, 2 * self.gui.scale), colour)

		shuffle_area = (volume_r[0] - 41 * self.gui.scale, volume_r[1] - 10 * self.gui.scale, 40 * self.gui.scale, 30 * self.gui.scale)
		if True: #self.coll(control_hit_area) and not self.prefs.shuffle_lock:
			colour = ColourRGBA(255, 255, 255, 20)
			if self.inp.mouse_click and self.coll(shuffle_area):
				self.tauon.toggle_repeat()
			if self.pctl.repeat_mode:
				colour = ColourRGBA(255, 255, 255, 190)

			sx = volume_r[0] - 39 * self.gui.scale
			sy = volume_r[1] - 1 * self.gui.scale
			self.tauon.mini_mode.repeat.render(sx, sy, colour)

			# sx = volume_r[0] - 39 * self.gui.scale
			# sy = volume_r[1] - 1 * self.gui.scale
			#
			# tw = 2 * self.gui.scale
			# self.ddt.rect_a((sx + 15 * self.gui.scale, sy), (13 * self.gui.scale, tw), colour)
			# self.ddt.rect_a((sx + 4 * self.gui.scale, sy + 4 * self.gui.scale), (25 * self.gui.scale, tw), colour)
			# self.ddt.rect_a((sx + 30 * self.gui.scale - tw, sy), (tw, 6 * self.gui.scale), colour)

		# Forward and back clicking
		if self.inp.mouse_click:
			if self.coll(left_area) and not self.prefs.shuffle_lock:
				self.pctl.back()
			if self.coll(right_area):
				self.pctl.advance()

		self.tauon.search_over.render()


		# Show exit/min buttons when mouse over
		tool_rect = [self.window_size[0] - 110 * self.gui.scale, 2, 108 * self.gui.scale, 45 * self.gui.scale]
		if self.prefs.left_window_control:
			tool_rect[0] = 0
		self.fields.add(tool_rect)
		if self.coll(tool_rect):
			self.tauon.draw_window_tools()

		# if w != h:
		# 	self.ddt.rect_s((1, 1, w - 2, h - 2), self.colours.mini_mode_border, 1 * self.gui.scale)
		# 	if self.gui.scale == 2:
		# 		self.ddt.rect_s((2, 2, w - 4, h - 4), self.colours.mini_mode_border, 1 * self.gui.scale)
		self.ddt.alpha_bg = False
class MiniModeSignal:
	def __init__(self, tauon: _PanelApp) -> None:
		self.tauon         = tauon
		self.ddt           = tauon.ddt
		self.inp           = tauon.inp
		self.gui           = tauon.gui
		self.coll          = tauon.coll
		self.pctl          = tauon.pctl
		self.prefs         = tauon.prefs
		self.fields        = tauon.fields
		self.colours       = tauon.colours
		self.window_size   = tauon.window_size
		self.album_art_gen = tauon.album_art_gen
		self.smooth_scroll = tauon.smooth_scroll
		self.save_position = None
		self.was_borderless = True
		self.volume_timer = Timer()
		self.volume_timer.force_set(100)
		self.visual_timer = Timer()
		self.motion_timer = Timer()
		self.fps = FPSCounter(window_size=20, min_update_interval=0.12, max_frame_time=0.5)
		self.visual_levels = [0.0] * 18
		self.focus_position = 0.0
		self.focus_target = 0.0
		self.focus_ready = False
		self.light_theme = False
		self.pending_track_jump: tuple[int, int] | None = None
		self.pending_jump_frames = 0

	def _cut_panel(
		self,
		rect: tuple[int, int, int, int],
		fill: ColourRGBA,
		border: ColourRGBA,
		cut: int,
		accent: ColourRGBA | None = None,
	) -> None:
		x, y, w, h = (round(v) for v in rect)
		cut = max(6, min(cut, max(6, w // 4), max(6, h // 4)))
		self.ddt.rect((x, y, w - cut, h), fill)
		self.ddt.rect((x, y + cut, w, h - cut), fill)
		for offset in range(cut):
			xx = x + w - cut + offset
			self.ddt.line(xx, y + offset, xx, y + cut, fill)
		self.ddt.line(x, y, x + w - cut, y, border)
		self.ddt.line(x + w - cut, y, x + w, y + cut, border)
		self.ddt.line(x + w, y + cut, x + w, y + h, border)
		self.ddt.line(x + w, y + h, x, y + h, border)
		self.ddt.line(x, y + h, x, y, border)
		if accent is not None:
			bar_w = min(round(92 * self.gui.scale), max(24, w - cut - 16))
			self.ddt.rect((x + round(10 * self.gui.scale), y + round(10 * self.gui.scale), bar_w, round(3 * self.gui.scale)), accent)

	def _corner_marks(self, rect: tuple[int, int, int, int], colour: ColourRGBA, size: int) -> None:
		x, y, w, h = (round(v) for v in rect)
		size = max(6, size)
		self.ddt.line(x, y + size, x, y, colour)
		self.ddt.line(x, y, x + size, y, colour)
		self.ddt.line(x + w - size, y, x + w, y, colour)
		self.ddt.line(x + w, y, x + w, y + size, colour)
		self.ddt.line(x, y + h - size, x, y + h, colour)
		self.ddt.line(x, y + h, x + size, y + h, colour)
		self.ddt.line(x + w - size, y + h, x + w, y + h, colour)
		self.ddt.line(x + w, y + h - size, x + w, y + h, colour)

	def _grid(self, rect: tuple[int, int, int, int], colour: ColourRGBA, step: int) -> None:
		x, y, w, h = (round(v) for v in rect)
		step = max(8, step)
		for xx in range(x + step, x + w, step):
			self.ddt.line(xx, y, xx, y + h, colour)
		for yy in range(y + step, y + h, step):
			self.ddt.line(x, yy, x + w, yy, colour)

	def _spectrum_targets(self) -> list[float]:
		source = self.gui.spec if self.gui.spec else []
		band_count = len(self.visual_levels)
		if source:
			targets = []
			source_len = len(source)
			# Keep a light lower/mid emphasis so the visualiser stays lively
			# while remaining close to the original full-range mapping.
			usable_len = max(1, round(source_len * 0.945))
			for i in range(band_count):
				left = (i / band_count) ** 1.175
				right = ((i + 1) / band_count) ** 1.175
				start = min(source_len - 1, int(left * usable_len))
				end = max(start + 1, int(right * usable_len))
				end = min(source_len, end + 1)
				segment = source[start:end]
				value = max(segment) if segment else 0
				gain = 1.0 + (1.0 - min(1.0, i / max(1, band_count - 1))) * 0.055
				targets.append(max(0.0, min((value * gain) / 20, 1.0)))
			return targets
		t = time.time() * 1.8
		return [0.08 + ((math.sin(t + i * 0.45) + 1) * 0.08) for i in range(band_count)]

	def _update_visual_levels(self) -> list[float]:
		dt = min(self.visual_timer.hit(), 0.08)
		targets = self._spectrum_targets()
		for i, target in enumerate(targets):
			current = self.visual_levels[i]
			if target > current:
				current += (target - current) * min(1.0, dt * 12)
			else:
				current = max(target, current - dt * 1.35)
			self.visual_levels[i] = current
		return self.visual_levels

	def _current_playlist_position(self) -> int:
		playlist = self.pctl.default_playlist
		if not playlist:
			return -1
		if 0 <= self.pctl.playlist_playing_position < len(playlist):
			return self.pctl.playlist_playing_position
		track = self.pctl.playing_object()
		if track is not None:
			try:
				return playlist.index(track.index)
			except ValueError:
				pass
		if 0 <= self.pctl.selected_in_playlist < len(playlist):
			return self.pctl.selected_in_playlist
		return 0

	def _update_focus_position(self, current_index: int) -> None:
		if current_index < 0:
			return
		self.focus_target = float(current_index)
		if not self.focus_ready:
			self.focus_position = float(current_index)
			self.focus_ready = True
			self.motion_timer.force_set(0)
			return
		dt = min(self.motion_timer.hit(), 0.08)
		delta = self.focus_target - self.focus_position
		step = dt * 8.0
		if abs(delta) <= step:
			self.focus_position = self.focus_target
		else:
			self.focus_position += math.copysign(step, delta)

	def _track_title(self, track: TrackClass) -> str:
		return track.title or track.filename or "Unknown track"

	def render(self) -> None:
		self.fps.tick()
		w = self.window_size[0]
		h = self.window_size[1]
		scale = self.gui.scale

		clear_bg = ColourRGBA(0, 0, 0, 0)
		if self.light_theme:
			shell_fill = ColourRGBA(254, 254, 254, 255)
			shell_border = ColourRGBA(4, 4, 6, 255)
			art_fill = ColourRGBA(246, 246, 243, 252)
			text_main = ColourRGBA(0, 0, 0, 255)
			text_dim = ColourRGBA(34, 34, 38, 255)
			text_faint = ColourRGBA(0, 0, 0, 112)
			track_text = ColourRGBA(62, 62, 66, 255)
			primary = ColourRGBA(0, 0, 0, 255)
			secondary = ColourRGBA(72, 72, 76, 255)
			grid_line = ColourRGBA(0, 0, 0, 28)
			point_marker = ColourRGBA(0, 0, 0, 200)
		else:
			shell_fill = ColourRGBA(16, 16, 18, 236)
			shell_border = ColourRGBA(96, 96, 106, 255)
			art_fill = ColourRGBA(22, 22, 26, 244)
			text_main = ColourRGBA(236, 236, 240, 255)
			text_dim = ColourRGBA(154, 154, 164, 255)
			text_faint = ColourRGBA(255, 255, 255, 30)
			track_text = ColourRGBA(154, 154, 164, 255)
			primary = ColourRGBA(235, 72, 170, 255)
			secondary = ColourRGBA(64, 232, 224, 255)
			grid_line = ColourRGBA(255, 255, 255, 24)
			point_marker = ColourRGBA(255, 255, 255, 180)

		self.ddt.alpha_bg = True
		self.ddt.clear_rect((0, 0, w, h))
		self.ddt.text_background_colour = clear_bg

		frame = round(14 * scale)
		box_y = round(14 * scale)
		box_side = min(w - frame * 2, h - round(30 * scale))
		box_rect = (frame, box_y, w - frame * 2, box_side)
		seek_bar = [
			box_rect[0] + round(18 * scale),
			box_rect[1] + box_rect[3] - round(18 * scale),
			box_rect[2] - round(36 * scale),
			max(4, round(5 * scale)),
		]
		seek_hit = [
			seek_bar[0],
			seek_bar[1] - round(8 * scale),
			seek_bar[2],
			seek_bar[3] + round(16 * scale),
		]

		self._cut_panel(box_rect, shell_fill, shell_border, round(16 * scale), accent=primary)
		grid_rect = (box_rect[0] + round(10 * scale), box_rect[1] + round(10 * scale), box_rect[2] - round(20 * scale), box_rect[3] - round(20 * scale))
		grid_step = round(20 * scale)
		self._grid(grid_rect, grid_line, grid_step)
		self.ddt.text_background_colour = shell_fill
		self.ddt.text((box_rect[0] + round(14 * scale), box_rect[1] + round(12 * scale)), "TAUON \\\\ SIGNAL", text_main, 210, round(120 * scale), shell_fill)
		self.ddt.text((box_rect[0] + box_rect[2] - round(104 * scale), box_rect[1] + round(12 * scale)), "SPECTRUM ARRAY", text_dim, 210, round(90 * scale), shell_fill)
		fps_text = f"{int(round(self.fps.get()))} FPS"
		self.ddt.text((box_rect[0] + box_rect[2] - round(56 * scale), box_rect[1] + box_rect[3] - round(16 * scale)), fps_text, text_faint, 209, round(52 * scale), shell_fill)
		theme_rect = (
			box_rect[0] + round(16 * scale),
			box_rect[1] + box_rect[3] - round(40 * scale),
			round(54 * scale),
			round(16 * scale),
		)
		self.fields.add(theme_rect)
		theme_label = "LIGHT" if not self.light_theme else "DARK"
		theme_colour = text_faint
		if self.coll(theme_rect) and self.inp.mouse_click:
			self.light_theme = not self.light_theme
			self.inp.mouse_click = False
			theme_colour = text_main
		elif self.coll(theme_rect):
			theme_colour = text_dim
		self.ddt.text_background_colour = shell_fill
		self.ddt.text((theme_rect[0] + round(4 * scale), theme_rect[1] - round(1 * scale)), theme_label, theme_colour, 209, theme_rect[2] - round(4 * scale), shell_fill)
		self.ddt.text_background_colour = shell_fill

		track = self.pctl.playing_object()
		playlist = self.pctl.default_playlist

		if self.inp.mouse_wheel != 0:
			self.volume_timer.set()
			scroll_distance = self.smooth_scroll.scroll("volume bar")
			self.pctl.player_volume += scroll_distance * self.prefs.volume_wheel_increment * 3
			if self.pctl.player_volume < 1:
				self.pctl.player_volume = 0
			elif self.pctl.player_volume > 100:
				self.pctl.player_volume = 100
			self.pctl.player_volume = int(self.pctl.player_volume)
			self.pctl.set_volume()

		box_restore_rect = (box_rect[0], box_rect[1], box_rect[2], round(34 * scale))
		self.fields.add(box_restore_rect)
		if self.coll(box_restore_rect) and self.inp.mouse_click:
			if self.tauon.d_click_timer.get() < 0.3:
				self.ddt.alpha_bg = False
				self.tauon.restore_full_mode()
				self.gui.request_frame()
				return
			self.tauon.d_click_timer.set()

		art_size = round(127 * scale)
		art_rect = (
			box_rect[0] + box_rect[2] - art_size - round(18 * scale),
			box_rect[1] + round(34 * scale),
			art_size,
			art_size,
		)
		art_inner = (art_rect[0] + round(7 * scale), art_rect[1] + round(7 * scale), art_rect[2] - round(14 * scale), art_rect[3] - round(14 * scale))

		levels = self._update_visual_levels()
		self.fields.add(tuple(seek_hit))
		self.ddt.rect(tuple(seek_bar), alpha_blend(ColourRGBA(255, 255, 255, 14), shell_fill))
		for i in range(1, 9):
			x = seek_bar[0] + round(seek_bar[2] * (i / 10))
			self.ddt.line(x, seek_bar[1] - round(4 * scale), x, seek_bar[1] + seek_bar[3] + round(4 * scale), ColourRGBA(255, 255, 255, 18))
		progress = 0.0
		if self.pctl.playing_length > 0:
			progress = max(0.0, min(self.pctl.playing_time / self.pctl.playing_length, 1.0))
		progress_w = round((seek_bar[2] - round(4 * scale)) * progress)
		if progress_w > 0:
			self.ddt.rect((seek_bar[0] + round(2 * scale), seek_bar[1] + round(2 * scale), progress_w, seek_bar[3] - round(4 * scale)), primary)
			marker_x = seek_bar[0] + round(progress * seek_bar[2])
			self.ddt.rect((marker_x - round(1 * scale), seek_bar[1] - round(4 * scale), round(3 * scale), seek_bar[3] + round(8 * scale)), secondary)
		if self.inp.mouse_up and self.coll(tuple(seek_hit)) and self.pctl.playing_length > 0:
			click_x = min(max(self.inp.mouse_position[0], seek_bar[0]), seek_bar[0] + seek_bar[2]) - seek_bar[0]
			self.pctl.seek_decimal(click_x / seek_bar[2])

		graph_rect = (
			box_rect[0] + round(12 * scale),
			box_rect[1] + round(28 * scale),
			box_rect[2] - round(24 * scale),
			box_rect[3] - round(54 * scale),
		)
		baseline = graph_rect[1] + graph_rect[3] - round(16 * scale)
		midline = graph_rect[1] + graph_rect[3] // 2
		self.ddt.line(graph_rect[0], baseline, graph_rect[0] + graph_rect[2], baseline, alpha_blend(ColourRGBA(255, 255, 255, 18), shell_border))
		self.ddt.line(graph_rect[0], midline, graph_rect[0] + graph_rect[2], midline, ColourRGBA(255, 255, 255, 10))

		current_index = self._current_playlist_position()
		self._update_focus_position(current_index)

		anchor_x = box_rect[0] + round(box_rect[2] * 0.32) + round(75 * scale)
		anchor_y = box_rect[1] + round(box_rect[3] * 0.24)
		x_step = round(18 * scale)
		y_step = round(16 * scale)
		max_delta = 7
		clicked_track = False
		if playlist:
				start = max(0, int(math.floor(self.focus_position)) - max_delta)
				end = min(len(playlist), int(math.ceil(self.focus_position)) + max_delta + 1)
				for i in range(start, end):
					rel = i - self.focus_position
					if abs(rel) > 7:
						continue
					tx = anchor_x + round(rel * x_step)
					ty = anchor_y + round(rel * y_step)
					if ty < graph_rect[1] - round(20 * scale) or ty > baseline - round(4 * scale):
						continue

					track_object = self.pctl.get_track(playlist[i])
					title = self._track_title(track_object)
					is_current = i == current_index
					font = 413 if is_current else 211
					alpha = max(18, 170 - int(abs(rel) * 22) - max(0, int(-rel)) * 12)
					colour = text_main if is_current else ColourRGBA(track_text.r, track_text.g, track_text.b, alpha)
					tw = self.ddt.get_text_w(title, font)
					th = self.ddt.get_text_w(title, font, height=True)
					if tw is None:
						tw = round(120 * scale)
					if th is None:
						th = round(14 * scale)
					if tx > graph_rect[0] + graph_rect[2] or tx + round(tw) < graph_rect[0]:
						continue
					hit_rect = (
						round(tx) - round(4 * scale),
						round(ty) - round(2 * scale),
						round(tw) + round(8 * scale),
						round(th) + round(4 * scale),
					)
					self.fields.add(hit_rect)
					if self.coll(hit_rect):
						colour = text_main if not is_current else secondary
						if self.inp.mouse_click:
							self.pctl.selected_in_playlist = i
							self.gui.shift_selection = [i]
							self.focus_target = float(i)
							self.pending_track_jump = (playlist[i], i)
							self.pending_jump_frames = 1
							self.inp.mouse_click = False
							clicked_track = True
					self.ddt.text((tx, ty), title, colour, font, round(box_rect[2] * 0.54), shell_fill)
					if is_current:
						underline_y = round(ty + 15 * scale)
						underline_w = min(round(tw), round(box_rect[2] * 0.44))
						self.ddt.rect((round(tx), underline_y, underline_w, max(1, round(2 * scale))), secondary)

		self.ddt.rect(art_rect, art_fill)
		self.ddt.rect((art_rect[0], art_rect[1], art_rect[2], 1), shell_border)
		self.ddt.rect((art_rect[0], art_rect[1] + art_rect[3] - 1, art_rect[2], 1), shell_border)
		self.ddt.rect((art_rect[0], art_rect[1], 1, art_rect[3]), shell_border)
		self.ddt.rect((art_rect[0] + art_rect[2] - 1, art_rect[1], 1, art_rect[3]), shell_border)
		self.ddt.rect((art_rect[0] + round(10 * scale), art_rect[1] + round(10 * scale), min(round(92 * self.gui.scale), max(24, art_rect[2] - 16)), round(3 * scale)), secondary)
		if track is not None:
			self.album_art_gen.display(track, (art_inner[0], art_inner[1]), (art_inner[2], art_inner[3]))
			self._corner_marks(art_inner, secondary, round(10 * scale))
		else:
			self.ddt.rect(art_inner, alpha_blend(ColourRGBA(255, 255, 255, 8), art_fill))
			self._corner_marks(art_inner, secondary, round(10 * scale))
			self.ddt.text_background_colour = art_fill
			self.ddt.text((art_rect[0] + art_rect[2] // 2, art_rect[1] + round(34 * scale), 2), "NO ART", text_main, 210, art_rect[2] - round(14 * scale), art_fill)

		if self.coll(art_rect) and self.inp.right_click:
			self.pctl.play_pause()

		if self.pending_track_jump is not None:
			if self.pending_jump_frames > 0:
				self.pending_jump_frames -= 1
			else:
				track_id, pl_position = self.pending_track_jump
				self.pending_track_jump = None
				self.pctl.jump(track_id, pl_position=pl_position)

		bar_gap = round(4 * scale)
		bar_w = max(round(5 * scale), (graph_rect[2] - bar_gap * (len(levels) - 1)) // len(levels))
		max_h = graph_rect[3] - round(24 * scale)
		prev_point = None
		time_bias = time.time() * 3
		for i, value in enumerate(levels):
			x = graph_rect[0] + i * (bar_w + bar_gap)
			bar_h = max(round(value * max_h), 0)
			segments = max(1, bar_h // max(1, round(6 * scale)))
			for seg in range(segments):
				y = baseline - round((seg + 1) * (5 * scale))
				height = round(3 * scale)
				seg_colour = colour_slide(primary, secondary, seg, max(segments, 1))
				self.ddt.rect((x, y, bar_w, height), seg_colour)
			reflection = max(round(bar_h * 0.25), 0)
			if reflection > 0 and not self.light_theme:
				self.ddt.rect((x + round(1 * scale), midline + round(4 * scale), max(1, bar_w - round(2 * scale)), reflection), ColourRGBA(primary.r, primary.g, primary.b, 36))
			point_x = x + bar_w // 2
			point_y = midline - round(value * (graph_rect[3] * 0.22)) - round(math.sin(time_bias + i * 0.35) * 4 * scale)
			if prev_point is not None:
				self.ddt.line(prev_point[0], prev_point[1], point_x, point_y, secondary)
			prev_point = (point_x, point_y)
			self.ddt.rect((point_x - round(1 * scale), point_y - round(1 * scale), round(3 * scale), round(3 * scale)), point_marker)

		self._corner_marks(graph_rect, primary, round(10 * scale))

		if self.coll(box_rect) and self.inp.mouse_click and not clicked_track and not self.coll(tuple(seek_hit)):
			self.tauon.d_click_timer.set()

		tool_rect = [self.window_size[0] - 110 * self.gui.scale, 2, 108 * self.gui.scale, 45 * self.gui.scale]
		if self.prefs.left_window_control:
			tool_rect[0] = 0
		self.fields.add(tool_rect)
		if self.coll(tool_rect):
			self.tauon.draw_window_tools()

		self.gui.request_frame()
		self.ddt.alpha_bg = False
class ArtBox:

	def __init__(self, tauon: _PanelApp) -> None:
		self.tauon   = tauon
		self.gui     = tauon.gui
		self.inp     = tauon.inp
		self.ddt     = tauon.ddt
		self.pctl    = tauon.pctl
		self.coll    = tauon.coll
		self.fields  = tauon.fields
		self.colours = tauon.colours

	def draw(self, x: int, y: int, w: int, h: int, target_track: TrackClass | None = None, tight_border: bool = False, default_border: tuple[int, int, int, int] | None = None, inset: bool = True, quick_draw: bool = False, draw_border: bool = True, draw_background: bool = True) -> None:
		tauon   = self.tauon
		ddt     = self.ddt
		colours = self.colours
		gui     = self.gui
		inp     = self.inp

		# Draw a background for whole area. The centered side-panel layout has
		# already painted its full panel, so it disables this second fill to avoid
		# stacking the translucent panel colour into an opaque block behind art.
		if draw_background:
			if not gui.have_art_bg:
				ddt.clear_rect((x, y, w, h))
			ddt.rect((x, y, w, h), colours.side_panel_background)
		# ddt.rect_r((x, y, w ,h), [255, 0, 0, 200], True)

		# We need to find the size of the inner square for the artwork
		# box = min(w, h)

		box_w = w
		box_h = h

		if inset:  # The Custom Layout Art Box passes inset=False (its gutter spaces it)
			box_w -= 17 * gui.scale  # Inset the square a bit
			box_h -= 17 * gui.scale  # Inset the square a bit

		box_x = x + ((w - box_w) // 2)
		box_y = y + ((h - box_h) // 2)

		# And position the square
		rect = (box_x, box_y, box_w, box_h)
		gui.main_art_box = rect

		# Draw the album art. If side bar is being dragged set quick draw flag
		showc = None
		result = 1
		show_vis = False

		if target_track:  # Only show if song playing or paused

			result = tauon.album_art_gen.display(target_track, (rect[0], rect[1]), (box_w, box_h), gui.side_drag or quick_draw, async_hold=True, caller_id="art_box")
			showc = tauon.album_art_gen.get_info(target_track)

			# Milkdrop visualiser
			# code mirrored in l_panel
			if tauon.prefs.milk and not gui.milkdrop_in_widget and self.tauon.pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM, PlayingState.PAUSED):
				if self.pctl.a_time < 1.3:
					if 1 < self.pctl.a_time < 1.3:
						tauon.milky.render(discard=True)
						tauon.milky.burn(target_track)
				else:
					tauon.milky.render()
					show_vis = True
				if self.tauon.pctl.playing_state != PlayingState.PAUSED:
					# Re-arm the next frame while the visualiser animates (the flag
					# clears at frame start, so a mid-draw request means one more frame);
					# the central pacer caps the rate at the display refresh rate.
					gui.request_frame()

		# Draw faint border on album art
		if tight_border and not show_vis:
			if result == 0 and gui.art_drawn_rect:
				border = gui.art_drawn_rect
				ddt.rect_s(gui.art_drawn_rect, colours.art_box, 1 * gui.scale)
			elif default_border:
				border = default_border
				ddt.rect_s(default_border, colours.art_box, 1 * gui.scale)
			else:
				border = rect
		else:
			if draw_border:  # Custom Layout passes False when the segment border is on
				ddt.rect_s(rect, colours.art_box, 1 * gui.scale)
			border = rect

		self.fields.add(border)

		# Draw image downloading indicator
		if gui.image_downloading:
			ddt.text(
				(x + int(box_w / 2), 38 * gui.scale + int(box_h / 2), 2), _("Fetching image..."),
				colours.side_bar_line1,
				14, bg=colours.side_panel_background)
			gui.request_frame()

		# Input for album art
		if target_track:
			# Cycle images on click
			if self.coll(gui.main_art_box) and inp.mouse_click is True and inp.key_focused == 0:

				if show_vis:
					tauon.milky.projectm.load_next = "random"
				else:
					tauon.album_art_gen.cycle_offset(target_track)

					if self.pctl.mpris:
						self.pctl.mpris.update(force=True)

		# Activate picture context menu on right click
		if inp.right_click and tauon.prefs.milk and not gui.milkdrop_in_widget and self.coll(rect):
			self.tauon.milky_menu.activate(in_reference=target_track)
		elif tight_border and gui.art_drawn_rect:
			if inp.right_click and self.coll(gui.art_drawn_rect) and target_track:
				self.tauon.picture_menu.activate(in_reference=target_track)
		elif inp.right_click and self.coll(rect) and target_track:
			self.tauon.picture_menu.activate(in_reference=target_track)

		# Draw picture metadata
		if showc is not None and self.coll(border) \
			and tauon.rename_track_box.active is False \
			and tauon.radiobox.active is False \
			and tauon.pref_box.enabled is False \
			and gui.rename_playlist_box is False \
			and gui.message_box is False \
			and gui.track_box is False \
			and gui.layer_focus == 0:

			padding = 6 * gui.scale

			xw = box_x + box_w
			yh = box_y + box_h
			if tight_border and gui.art_drawn_rect and gui.art_drawn_rect[2] > 50 * gui.scale:
				xw = gui.art_drawn_rect[0] + gui.art_drawn_rect[2]
				yh = gui.art_drawn_rect[1] + gui.art_drawn_rect[3]

			if not show_vis:
				self.tauon.art_metadata_overlay(xw, yh, showc)

			if show_vis:
				line = tauon.milky.projectm.get_current_name()

				padding = round(0 * gui.scale)
				xx = x + round(12 * gui.scale)
				if gui.custom_mode:
					# Match the Custom Layout Milkdrop widget's tag position
					xx -= 5
				yy = y + round(25 * gui.scale)
				mw = box_w - round(25 * gui.scale)
				tag_width, tag_height = self.ddt.get_text_wh(line, 312, max_x = mw)
				tag_width += round(17 * self.gui.scale)

				self.ddt.rect_a((xx, yy), (tag_width, 18 * self.gui.scale),
								ColourRGBA(8, 8, 8, 255))
				self.ddt.text(((xx) + (6 * self.gui.scale + padding), yy), line, ColourRGBA(220, 220, 220, 255),
							  312, bg=ColourRGBA(30, 30, 30, 255), max_w = mw)

				if self.tauon.prefs.auto_milk:
					line = _("Auto Cycle")
					yy += round(30 * gui.scale)
					tag_width, tag_height = self.ddt.get_text_wh(line, 12, max_x = mw)
					tag_width += round(14 * self.gui.scale)

					self.ddt.rect_a(
						(xx, yy), (tag_width, 18 * self.gui.scale),
						ColourRGBA(8, 8, 8, 255))
					self.ddt.text(
						((xx) + (6 * self.gui.scale + padding), yy), line, ColourRGBA(210, 210, 210, 255),
						12, bg=ColourRGBA(30, 30, 30, 255), max_w = mw)

				if self.tauon.pctl.playing_state not in (PlayingState.PLAYING, PlayingState.URL_STREAM):
					tauon.milky.fps.reset()
				line = f"FPS: {round(tauon.milky.fps.get())}"
				yy += round(30 * gui.scale)
				tag_width, tag_height = self.ddt.get_text_wh(line, 12, max_x = mw)
				tag_width += round(14 * self.gui.scale)

				self.ddt.rect_a((xx, yy), (tag_width, 18 * self.gui.scale),
								ColourRGBA(8, 8, 8, 255))
				self.ddt.text(((xx) + (6 * self.gui.scale + padding), yy), line, ColourRGBA(210, 210, 210, 255),
							  12, bg=ColourRGBA(30, 30, 30, 255), max_w = mw)
class RadioBox:

	def __init__(self, tauon: _PanelApp, pctl: _PanelPlayer) -> None:
		self.pctl: _PanelPlayer           = pctl
		self.tauon: _PanelApp          = tauon
		self.ddt: TDraw            = tauon.ddt
		self.inp: Input            = tauon.inp
		self.gui: GuiVar            = tauon.gui
		self.coll           = tauon.coll
		self.draw: Drawing           = pctl.draw
		self.prefs: Prefs          = tauon.prefs
		self.fields: Fields         = tauon.fields
		self.colours: ColoursClass        = tauon.colours
		self.window_size: list[int]    = tauon.window_size
		self.show_message   = tauon.show_message
		self.smooth_scroll: Any  = tauon.smooth_scroll
		self.thread_manager: Any = tauon.thread_manager
		self.active: bool = False
		self.station_editing: RadioStation | None = None
		self.edit_mode: bool = True
		self.add_mode: bool = False
		self.radio_field_active: int = 1
		self.radio_field: TextBox2        = TextBox2(tauon)
		self.radio_field_title: TextBox2  = TextBox2(tauon)
		self.radio_field_search: TextBox2 = TextBox2(tauon)

		self.x = 1
		self.y = 1
		self.w = 1
		self.h = 1
		self.center: bool = False

		self.scroll_position: int = 0
		self.scroll: ScrollBox = ScrollBox(tauon=tauon, pctl=pctl)

		self.dummy_track: TrackClass = TrackClass()
		self.dummy_track.index = -2
		self.dummy_track.is_network = True
		self.dummy_track.art_url_key = ""  # radio"
		self.dummy_track.file_ext = "RADIO"
		self.playing_title: str = ""

		self.proxy_started: bool = False
		self.loaded_url: str | None = None
		self.loaded_station: RadioStation | None = None
		self.load_connecting: bool = False
		self.load_failed: bool = False
		self.load_request_id: int = 0
		self.searching: bool = False
		self.load_failed_timer: Timer = Timer()
		self.right_clicked_station: RadioStation | None = None
		self.right_clicked_station_p: int | None = None
		self.click_point = (0, 0)

		self.song_key = ""

		self.drag = None

		self.tab = 0
		self.temp_list: list[RadioStation] = []

		self.hosts = None
		self.host = None

		self.search_menu = Menu(tauon, 170)
		self.search_menu.add(MenuItem(_("Search Tag"), self.search_tag, pass_ref=True))
		self.search_menu.add(MenuItem(_("Search Country Code"), self.search_country, pass_ref=True))
		self.search_menu.add(MenuItem(_("Search Title"), self.search_title, pass_ref=True))

		self.websocket = None
		self.ws_interval = 4.5
		self.websocket_source_urls = ("https://listen.moe/kpop/stream", "https://listen.moe/stream")
		self.run_proxy: bool = True

	def parse_vorbis_okay(self) -> bool:
		return (
			self.loaded_url not in self.websocket_source_urls) and \
			"radio.plaza.one" not in self.loaded_url and \
			"gensokyoradio.net" not in self.loaded_url

	def search_country(self, text: str) -> None:
		if len(text) == 2 and text.isalpha():
			self.search_radio_browser(
				f"/json/stations/search?countrycode={text}&order=votes&limit=250&reverse=true")
		else:
			self.search_radio_browser(
				f"/json/stations/search?country={text}&order=votes&limit=250&reverse=true")

	def search_tag(self, text) -> None:
		text = text.lower()
		self.search_radio_browser(f"/json/stations/search?order=votes&limit=250&reverse=true&tag={text}")

	def search_title(self, text) -> None:
		text = text.lower()
		self.search_radio_browser(f"/json/stations/search?order=votes&limit=250&reverse=true&name={text}")

	def is_m3u(self, url: str) -> bool:
		return url.lower().endswith(".m3u") or url.lower().endswith(".m3u8")

	def extract_stream_m3u(self, url: str, recursion_limit: int = 5) -> str | None:
		if recursion_limit <= 0:
			return None
		logging.info("Fetching M3U...")

		try:
			response = requests.get(url, timeout=10)
			if response.status_code != 200:
				logging.error(f"M3U Fetch error code: {response.status_code}")
				return None

			content = response.text
			lines = content.strip().split("\n")

			for line in lines:
				line = line.strip()
				if not line.startswith("#") and len(line) > 0:
					if self.is_m3u(line):
						next_url = urllib.parse.urljoin(url, line)
						return self.extract_stream_m3u(next_url, recursion_limit - 1)
					return urllib.parse.urljoin(url, line)

			return None

		except Exception:
			logging.exception("Failed to extract M3U")
			return None

	def abort_load(self, clear_station: bool = True) -> None:
		logging.info(
			f"Radio load abort requested clear_station={clear_station} "
			f"load_request_id={self.load_request_id} load_connecting={self.load_connecting} "
			f"loaded_url={self.loaded_url}"
		)
		self.load_request_id += 1
		self.load_connecting = False
		self.load_failed = False
		self.loaded_url = None
		if clear_station:
			self.loaded_station = None
		if self.websocket:
			self.websocket.close()
			logging.info("Websocket closed")
		self.tauon.stream_proxy.stop()
		self.pctl.record_stream = False
		self.gui.request_frame()

	def start(self, station: RadioStation) -> None:
		url = station.stream_url
		logging.info(
			f"Start radio station title={station.title!r} url={url!r} "
			f"load_request_id={self.load_request_id} load_connecting={self.load_connecting} "
			f"playing_state={self.pctl.playing_state}"
		)
		# Otherwise we'll be mute if we're starting from a paused state
		self.pctl.set_volume()
		if self.is_m3u(url):
			url = self.extract_stream_m3u(url)
			logging.info(f"Extracted URL is: {url}")
			if not url:
				logging.info("Failed to extract stream from M3U")
				return

		if self.load_connecting:
			self.abort_load(clear_station=False)

		if self.websocket:
			self.websocket.close()
			logging.info("Websocket closed")

		self.playing_title = ""
		self.playing_title = station.title
		self.dummy_track.art_url_key = ""
		self.dummy_track.title = ""
		self.dummy_track.artist = ""
		self.dummy_track.album = ""
		self.dummy_track.date = ""
		self.pctl.radio_meta_on = ""

		self.tauon.album_art_gen.clear_cache()

		if not self.tauon.test_ffmpeg():
			self.prefs.auto_rec = False
			return

		self.run_proxy = True
		if url.endswith(".ts"):
			self.run_proxy = False

		if self.run_proxy and not self.proxy_started and self.prefs.backend != Backend.PHAZOR:
			shoot = threading.Thread(target=stream_proxy, args=[self.tauon])
			shoot.daemon = True
			shoot.start()
			self.proxy_started = True

		# self.pctl.url = url
		self.pctl.url = f"http://127.0.0.1:{7812}"
		if not self.run_proxy:
			self.pctl.url = station.stream_url
		self.loaded_url = None
		self.pctl.tag_meta = ""
		self.pctl.radio_meta_on = ""
		self.pctl.found_tags = {}
		self.song_key = ""
		self.pctl.playing_time = 0
		self.pctl.decode_time = 0
		self.loaded_station = station

		if self.tauon.stream_proxy.download_running or self.tauon.stream_proxy.encode_running or self.tauon.stream_proxy.pump_running:
			logging.info(
				f"Stopping existing radio stream before new request: "
				f"{self.tauon.stream_proxy.state_log()}"
			)
			self.tauon.stream_proxy.stop()

		self.load_request_id += 1
		request_id = self.load_request_id
		self.load_connecting = True
		self.load_failed = False
		logging.info(f"Radio start request queued request_id={request_id} run_proxy={self.run_proxy} url={url!r}")

		shoot = threading.Thread(target=self.start2, args=[url, request_id, self.run_proxy])
		shoot.daemon = True
		shoot.start()

	def start2(self, url: str, request_id: int, run_proxy: bool) -> None:
		logging.info(
			f"Radio start2 entered request_id={request_id} current_request={self.load_request_id} "
			f"run_proxy={run_proxy} url={url!r}"
		)
		if request_id != self.load_request_id:
			logging.info(f"Radio start2 ignoring stale request_id={request_id}")
			return

		if run_proxy and not self.tauon.stream_proxy.start_download(url, request_id):
			if request_id == self.load_request_id:
				self.load_failed_timer.set()
				self.load_failed = True
				self.load_connecting = False
				self.gui.request_frame()
				logging.error(
					f"Starting radio failed request_id={request_id}: "
					f"{self.tauon.stream_proxy.state_log()}"
				)
			# self.show_message(_("Failed to establish a connection"), mode="error")
			return

		if request_id != self.load_request_id:
			logging.info(
				f"Radio start2 became stale after download start request_id={request_id} "
				f"current_request={self.load_request_id}"
			)
			if run_proxy and self.tauon.stream_proxy.request_id == request_id:
				self.tauon.stream_proxy.stop()
			return

		logging.info(f"Radio start2 activating playback request_id={request_id} url={url!r}")
		self.loaded_url = url
		self.pctl.record_stream = False
		self.pctl.playerCommand = "url"
		self.pctl.playerCommandReady = True
		self.pctl.playing_state = PlayingState.URL_STREAM
		self.pctl.playing_time = 0
		self.pctl.decode_time = 0
		self.pctl.playing_length = 0
		self.pctl.windows_progress.update()
		self.tauon.thread_manager.ready_playback()
		# ensure RPC is started and woken immediately for radio start
		try:
			self.tauon._signal_discord()
		except Exception:
			self.tauon.hit_discord()

		if self.tauon.update_play_lock is not None:
			self.tauon.update_play_lock()

		time.sleep(0.1)
		self.load_connecting = False
		self.load_failed = False
		self.gui.request_frame()

		wss = ""
		if url == "https://listen.moe/kpop/stream":
			wss = "wss://listen.moe/kpop/gateway_v2"
		if url == "https://listen.moe/stream":
			wss = "wss://listen.moe/gateway_v2"
		if wss:
			logging.info("Connecting to Listen.moe")
			import _thread as th

			import websocket

			def send_heartbeat(ws: WebSocketApp) -> None:
				#logging.info(self.ws_interval)
				time.sleep(self.ws_interval)
				try:
					ws.send('{"op":9}')
				except Exception:
					logging.info("Websocket already closed")
				logging.info("Send heartbeat")

			def on_message(ws: WebSocketApp, message: str) -> None:
				logging.info(message)
				d = json.loads(message)
				if d["op"] == 10:
					shoot = threading.Thread(target=send_heartbeat, args=[ws])
					shoot.daemon = True
					shoot.start()

				if d["op"] == 0:
					self.ws_interval = d["d"]["heartbeat"] / 1000
					try:
						ws.send('{"op":9}')
					except Exception:
						logging.info("Websocket already closed")

				if d["op"] == 1:
					try:

						found_tags = {}
						found_tags["title"] = d["d"]["song"]["title"]
						if d["d"]["song"]["artists"]:
							found_tags["artist"] = d["d"]["song"]["artists"][0]["name"]
						line = ""
						if "title" in found_tags:
							line += found_tags["title"]
							if "artist" in found_tags:
								line = found_tags["artist"] + " - " + line

						self.pctl.found_tags = found_tags
						self.pctl.tag_meta = line

						album_image = d["d"]["song"]["albums"][0].get("image")
						if album_image:
							filename = album_image
							fulllink = "https://cdn.listen.moe/covers/" + filename

							#logging.info(fulllink)
							art_response = requests.get(fulllink, timeout=10)
							#logging.info(art_response.status_code)

							if art_response.status_code == 200:
								if self.pctl.radio_image_bin:
									self.pctl.radio_image_bin.close()
									self.pctl.radio_image_bin = None
								self.pctl.radio_image_bin = io.BytesIO(art_response.content)
								self.pctl.radio_image_bin.seek(0)
								self.dummy_track.art_url_key = "ok"
								logging.info("Got new art")

					except Exception:
						logging.exception("No image")
						if self.pctl.radio_image_bin:
							self.pctl.radio_image_bin.close()
							self.pctl.radio_image_bin = None
					self.gui.clear_image_cache_next += 1
					self.gui.request_frame()

			def on_error(ws: WebSocketApp, error) -> None:
				logging.error(error)

			def on_close(ws: WebSocketApp) -> None:
				logging.info("### closed ###")

			def on_open(ws: WebSocketApp) -> None:
				def run(*args) -> None:
					pass
					# for i in range(3):
					#     time.sleep(4.5)
					#     ws.send("{\"op\":9}")
					# time.sleep(10)
					# ws.close()
					#logging.info("thread terminating...")

				th.start_new_thread(run, ())

			# websocket.enableTrace(True)
			#logging.info(wss)
			ws = websocket.WebSocketApp(wss, on_message=on_message, on_error=on_error)
			ws.on_open = on_open
			self.websocket = ws
			shoot = threading.Thread(target=ws.run_forever)
			shoot.daemon = True
			shoot.start()

	def delete_radio_entry(self, station: RadioStation) -> None:
		for i, saved in enumerate(self.prefs.radio_urls):
			if saved.stream_url == station.stream_url and saved.title == station.title:
				del self.prefs.radio_urls[i]

	def delete_radio_entry_after(self, station) -> None:
		p = self.right_clicked_station_p
		del self.prefs.radio_urls[p + 1:]

	def edit_entry(self, station: RadioStation) -> None:
		self.radio_field_title.text = station.title
		self.radio_field.text = station.stream_url

	def browser_get_hosts(self) -> list[str]:
		"""Get all base urls of all currently available radiobrowser servers

		Returns:
		list: a list of strings

		"""
		hosts = []
		# get all hosts from DNS
		ips = socket.getaddrinfo(
			"all.api.radio-browser.info", 80, 0, 0, socket.IPPROTO_TCP)
		for ip_tupple in ips:
			try:
				ip = ip_tupple[4][0]

				# do a reverse lookup on every one of the ips to have a nice name for it
				host_addr = socket.gethostbyaddr(ip)
				# add the name to a list if not already in there
				if host_addr[0] not in hosts:
					hosts.append(host_addr[0])
			except socket.herror:
				logging.exception(f"IP PTR lookup fail for {ip}")
			except Exception:
				logging.exception(f"Unknown exception - IP PTR lookup fail for {ip}")

		# sort list of names
		hosts.sort()
		# add "https://" in front to make it a url
		return list(map(lambda x: "https://" + x, hosts))

	def search_page(self) -> None:
		y = self.y
		x = self.x
		w = self.w
		h = self.h

		yy = y + round(40 * self.gui.scale)

		width = round(330 * self.gui.scale)
		rect = (x + 8 * self.gui.scale, yy - round(2 * self.gui.scale), width, 22 * self.gui.scale)
		self.fields.add(rect)
		# if (self.coll(rect) and self.gui.level_2_click) or (input.key_tab_press and self.radio_field_active == 2):
		#     self.radio_field_active = 1
		#     input.key_tab_press = False
		if not self.radio_field_search.text and not self.gui.editline:
			self.ddt.text((x + 14 * self.gui.scale, yy), _("Search text…"), self.colours.box_text_label, 312)
		self.radio_field_search.draw(
			x + 14 * self.gui.scale, yy, self.colours.box_input_text,
			active=True,
			width=width, click=self.gui.level_2_click)

		self.ddt.rect_s(rect, self.colours.box_text_border, 1 * self.gui.scale)

		if self.draw.button(
			_("Search"), x + width + round(21 * self.gui.scale), yy - round(3 * self.gui.scale),
			press=self.gui.level_2_click, w=round(80 * self.gui.scale)) or self.inp.level_2_enter:

			text = self.radio_field_search.text.replace("/", "").replace(":", "").replace("\\", "").replace(".", "").replace(
				"-", "").upper()
			text = urllib.parse.quote(text)
			if len(text) > 1:
				self.search_menu.activate(text, position=(x + width + round(21 * self.gui.scale), yy + round(20 * self.gui.scale)))
		if self.draw.button(_("Get Top Voted"), x + round(8 * self.gui.scale), yy + round(30 * self.gui.scale), press=self.gui.level_2_click):
			self.search_radio_browser("/json/stations?order=votes&limit=250&reverse=true")

		ww = self.ddt.get_text_w(_("Get Top Voted"), 212)
		if self.draw.button(_("Developer Picks"), x + ww + round(35 * self.gui.scale), yy + round(30 * self.gui.scale), press=self.gui.level_2_click):
			self.temp_list.clear()

			self.temp_list.append(
				RadioStation(
					title="Nightwave Plaza",
					stream_url_fallback="https://radio.plaza.one/ogg",
					stream_url="https://radio.plaza.one/ogg",
					website_url="https://plaza.one/",
					icon="https://plaza.one/icons/apple-touch-icon.png",
					country="Japan"))

			self.temp_list.append(
				RadioStation(
					title="Gensokyo Radio",
					stream_url_fallback="https://stream.gensokyoradio.net/GensokyoRadio-enhanced.m3u",
					stream_url="https://stream.gensokyoradio.net/1",
					website_url="https://gensokyoradio.net/",
					icon="https://gensokyoradio.net/favicon.ico",
					country="Japan"))

			self.temp_list.append(
				RadioStation(
					title="Listen.moe | Jpop",
					stream_url_fallback="https://listen.moe/stream",
					stream_url="https://listen.moe/stream",
					website_url="https://listen.moe/",
					icon="https://avatars.githubusercontent.com/u/26034028?s=200&v=4",
					country="Japan"))

			self.temp_list.append(
				RadioStation(
					title="Listen.moe | Kpop",
					stream_url_fallback="https://listen.moe/kpop/stream",
					stream_url="https://listen.moe/kpop/stream",
					website_url="https://listen.moe/",
					icon="https://avatars.githubusercontent.com/u/26034028?s=200&v=4",
					country="Korea"))

			self.temp_list.append(
				RadioStation(
					title="HBR1 Dream Factory | Ambient",
					stream_url_fallback="http://radio.hbr1.com:19800/ambient.ogg",
					stream_url="http://radio.hbr1.com:19800/ambient.ogg",
					website_url="http://www.hbr1.com/"))

			self.temp_list.append(
				RadioStation(
					title="Yggdrasil Radio | Anime & Jpop",
					stream_url_fallback="http://shirayuki.org:9200/",
					stream_url="http://shirayuki.org:9200/",
					website_url="https://yggdrasilradio.net/"))

			for station in self.tauon.primary_stations:
				self.temp_list.append(station)

	def search_radio_browser(self, param: str) -> None:
		if self.searching:
			return
		self.searching = True
		shoot = threading.Thread(target=self.search_radio_browser2, args=[param])
		shoot.daemon = True
		shoot.start()

	def search_radio_browser2(self, param: str) -> None:
		if not self.hosts:
			self.hosts = self.browser_get_hosts()
			# In case we get an empty list for some reason
			if not self.hosts:
				logging.warning("Got an empty radio list back, returning early!")
				self.searching = False
				return
		if not self.host:
			self.host = random.choice(self.hosts)

		uri = self.host + param
		req = urllib.request.Request(uri)
		req.add_header("User-Agent", self.tauon.t_agent)
		req.add_header("Content-Type", "application/json")
		response = urllib.request.urlopen(req, context=self.tauon.tls_context)
		data = response.read()
		data = json.loads(data.decode())
		self.parse_data(data)
		self.searching = False

	def parse_data(self, data: dict) -> None:
		self.temp_list.clear()
		for station in data:
			#logging.info(station)
			radio: RadioStation = RadioStation(
				title=station["name"],
				stream_url_fallback=station["url"],
				stream_url=station["url_resolved"],
				icon=station["favicon"],
				country=station["country"])
			if radio.country == "The Russian Federation":
				radio.country = "Russia"
			elif radio.country == "The United States Of America":
				radio.country = "USA"
			elif radio.country == "The United Kingdom Of Great Britain And Northern Ireland":
				radio.country = "United Kingdom"
			elif radio.country == "Islamic Republic Of Iran":
				radio.country = "Iran"
			elif len(station["country"]) > 20:
				radio.country = station["countrycode"]
			radio.website_url = station["homepage"]
			self.temp_list.append(radio)
		self.gui.request_frame()

	def render(self) -> None:
		if self.edit_mode:
			w = round(510 * self.gui.scale)
			h = round(120 * self.gui.scale)  # + sh

			self.w = w
			self.h = h
			# self.x = x
			# self.y = y
			width = w
			if self.center:
				x = int(self.window_size[0] / 2) - int(w / 2)
				y = int(self.window_size[1] / 2) - int(h / 2)
				yy = y
				self.y = y
				self.x = x
			else:
				yy = self.y
				y = self.y
				x = self.x
			self.ddt.rect_a((x - 2 * self.gui.scale, y - 2 * self.gui.scale), (w + 4 * self.gui.scale, h + 4 * self.gui.scale), self.colours.box_border)
			self.ddt.rect_a((x, y), (w, h), self.colours.box_background)
			self.ddt.text_background_colour = self.colours.box_background
			if self.inp.key_esc_press or (self.gui.level_2_click and not self.coll((x, y, w, h))):
				self.active = False

			if self.add_mode:
				self.ddt.text((x + 10 * self.gui.scale, yy + 8 * self.gui.scale), _("Add Station"), self.colours.box_title_text, 213)
			else:
				self.ddt.text((x + 10 * self.gui.scale, yy + 8 * self.gui.scale), _("Edit Station"), self.colours.box_title_text, 213)

			self.saved()
			return

		w = round(510 * self.gui.scale)
		h = round(356 * self.gui.scale)  # + sh
		x = int(self.window_size[0] / 2) - int(w / 2)
		y = int(self.window_size[1] / 2) - int(h / 2)

		self.w = w
		self.h = h
		self.x = x
		self.y = y

		yy = y

		self.ddt.rect_a((x - 2 * self.gui.scale, y - 2 * self.gui.scale), (w + 4 * self.gui.scale, h + 4 * self.gui.scale), self.colours.box_border)
		self.ddt.rect_a((x, y), (w, h), self.colours.box_background)

		self.ddt.text_background_colour = self.colours.box_background

		if self.inp.key_esc_press or (self.gui.level_2_click and not self.coll((x, y, w, h))):
			self.active = False

		self.ddt.text((x + 10 * self.gui.scale, yy + 8 * self.gui.scale), _("Station Browser"), self.colours.box_title_text, 213)

		# ---
		if self.load_connecting:
			self.ddt.text((x + 495 * self.gui.scale, yy + 8 * self.gui.scale, 1), _("Connecting..."), self.colours.box_title_text, 311)
		elif self.load_failed:
			self.ddt.text((x + 495 * self.gui.scale, yy + 8 * self.gui.scale, 1), _("Failed to connect!"), self.colours.box_title_text, 311)
			if self.load_failed_timer.get() > 3:
				self.gui.delay_frame(0.2)
				self.load_failed = False
		elif self.searching:
			self.ddt.text((x + 495 * self.gui.scale, yy + 8 * self.gui.scale, 1), _("Searching..."), self.colours.box_title_text, 311)
		elif self.pctl.playing_state == PlayingState.URL_STREAM:
			text = ""
			if self.tauon.stream_proxy.s_format:
				text = str(self.tauon.stream_proxy.s_format)
			if self.tauon.stream_proxy.s_bitrate and self.tauon.stream_proxy.s_bitrate.isnumeric():
				text += " " + self.tauon.stream_proxy.s_bitrate + "kbps"

			self.ddt.text((x + 495 * self.gui.scale, yy + 8 * self.gui.scale, 1), text, self.colours.box_title_text, 311)
			# if tauon.stream_proxy.s_format:
			#     self.ddt.text((x + 425 * self.gui.scale, yy + 8 * self.gui.scale,), tauon.stream_proxy.s_format, self.colours.box_title_text, 311)
			# if tauon.stream_proxy.s_bitrate:
			#     self.ddt.text((x + 454 * self.gui.scale, yy + 8 * self.gui.scale,), tauon.stream_proxy.s_bitrate + "kbps", self.colours.box_title_text, 311)

		# --- ----------------------------------------------------------------------
		if self.tab == 1:
			self.search_page()
		elif self.tab == 0:
			self.saved()
		self.draw_list()
		# self.footer()
		return

	def saved(self) -> None:
		y = self.y
		x = self.x
		w = self.w
		h = self.h

		yy = y + round(40 * self.gui.scale)

		width = round(370 * self.gui.scale)

		rect = (x + 8 * self.gui.scale, yy - round(2 * self.gui.scale), width, 22 * self.gui.scale)
		self.fields.add(rect)
		if (self.coll(rect) and self.gui.level_2_click) or (self.inp.key_tab_press and self.radio_field_active == 2):
			self.radio_field_active = 1
			self.inp.key_tab_press = False
		if not self.radio_field_title.text and not (self.radio_field_active == 1 and self.gui.editline):
			self.ddt.text((x + 14 * self.gui.scale, yy), _("Name / Title"), self.colours.box_text_label, 312)
		self.radio_field_title.draw(
			x + 14 * self.gui.scale, yy, self.colours.box_input_text,
			active=self.radio_field_active == 1,
			width=width, click=self.gui.level_2_click)

		self.ddt.rect_s(rect, self.colours.box_text_border, 1 * self.gui.scale)

		yy += round(30 * self.gui.scale)

		rect = (x + 8 * self.gui.scale, yy - round(2 * self.gui.scale), width, 22 * self.gui.scale)
		self.ddt.rect_s(rect, self.colours.box_text_border, 1 * self.gui.scale)
		self.fields.add(rect)
		if (self.coll(rect) and self.gui.level_2_click) or (self.inp.key_tab_press and self.radio_field_active == 1):
			self.radio_field_active = 2
			self.inp.key_tab_press = False

		if not self.radio_field.text and not (self.radio_field_active == 2 and self.gui.editline):
			self.ddt.text((x + 14 * self.gui.scale, yy), _("Raw Stream URL http://example.stream:1234"), self.colours.box_text_label, 312)
		self.radio_field.draw(
			x + 14 * self.gui.scale, yy, self.colours.box_input_text, active=self.radio_field_active == 2,
			width=width, click=self.gui.level_2_click)

		if self.draw.button(_("Save"), x + width + round(21 * self.gui.scale), yy - round(20 * self.gui.scale), press=self.gui.level_2_click):
			if not self.radio_field.text:
				self.show_message(_("Enter a stream URL"))
			elif "http://" in self.radio_field.text or "https://" in self.radio_field.text:
				radio = self.station_editing
				if self.add_mode:
					radio: RadioStation = RadioStation(
						title=self.radio_field_title.text,
						stream_url=self.radio_field.text)
				radio.title = self.radio_field_title.text
				if radio.stream_url != self.radio_field.text:
					radio.stream_url = self.radio_field.text
					radio.website_url = "" # Different URL, null the website # TODO(Martin): no way to edit for now

				if self.add_mode:
					self.pctl.radio_playlists[self.pctl.radio_playlist_viewing].stations.append(radio)
				self.active = False
			else:
				self.show_message(_("Could not validate URL. Must start with https:// or http://"))

	def draw_list(self) -> None:
		x = self.x
		y = self.y
		w = self.w
		h = self.h

		if self.drag:
			self.gui.update_on_drag = True

		yy = y + round(100 * self.gui.scale)
		x += round(10 * self.gui.scale)

		radio_list = self.prefs.radio_urls
		if self.tab == 1:
			radio_list = self.temp_list

		rect = (x, y, w, h)
		if self.coll(rect):
			scroll_distance = self.smooth_scroll.scroll("radio box")
			self.scroll_position -= scroll_distance
		self.scroll_position = max(self.scroll_position, 0)
		self.scroll_position = min(self.scroll_position, len(radio_list) // 2 - 7)

		if len(radio_list) // 2 > 9:
			self.scroll_position = self.scroll.draw(
				(x + w) - round(35 * self.gui.scale), yy, round(15 * self.gui.scale),
				round(210 * self.gui.scale), self.scroll_position,
				len(radio_list) // 2 - 7, True, click=self.gui.level_2_click)

		self.scroll_position = max(self.scroll_position, 0)

		p = self.scroll_position * 2
		offset = 0
		to_delete = None
		swap = None

		while True:
			if p > len(radio_list) - 1:
				break

			xx = x + offset
			station = radio_list[p]

			rect = (xx, yy, round(233 * self.gui.scale), round(40 * self.gui.scale))
			self.fields.add(rect)

			bg = self.colours.box_background
			text_colour = self.colours.box_input_text

			playing = self.pctl.playing_state == PlayingState.URL_STREAM and self.loaded_url == station.stream_url

			if playing:

				bg = self.colours.tab_background_active
				text_colour = self.colours.tab_text_active
				self.ddt.rect(rect, bg)

			if self.tauon.radio_view.drag:
				if station == self.tauon.radio_view.drag:
					text_colour = self.colours.box_sub_text
					bg = ColourRGBA(255, 255, 255, 10)
					self.ddt.rect(rect, bg)
			elif (self.tauon.radio_entry_menu.active and self.tauon.radio_entry_menu.reference == p) or \
					((not self.tauon.radio_entry_menu.active and self.coll(rect)) and not playing):
				text_colour = self.colours.box_sub_text
				bg = ColourRGBA(255, 255, 255, 10)
				self.ddt.rect(rect, bg)

			if self.coll(rect):
				if self.gui.level_2_click:
					# self.drag = p
					# self.click_point = copy.copy(self.inp.mouse_position)
					self.tauon.radio_view.drag = station
					self.tauon.radio_view.click_point = copy.copy(self.inp.mouse_position)
				if self.inp.mouse_up:  # self.gui.level_2_click:
					self.gui.request_frame()
					# if self.drag is not None and p != self.drag:
					#     swap = p
					if point_proximity_test(self.tauon.radio_view.click_point, self.inp.mouse_position, round(4 * self.gui.scale)):
						self.start(station)
				if self.inp.middle_click:
					to_delete = p
				if self.inp.level_2_right_click:
					self.right_clicked_station = station
					self.right_clicked_station_p = p
					self.tauon.radio_entry_menu.activate(station)

			bg = alpha_blend(bg, self.colours.box_background)

			boxx = round(32 * self.gui.scale)
			toff = boxx + round(10 * self.gui.scale)
			if station.title:
				self.ddt.text(
					(xx + toff, yy + round(3 * self.gui.scale)), station.title, text_colour, 212, bg=bg,
					max_w=rect[2] - (15 * self.gui.scale + toff))
			else:
				self.ddt.text(
					(xx + toff, yy + round(3 * self.gui.scale)), station.stream_url, text_colour, 212, bg=bg,
					max_w=rect[2] - (15 * self.gui.scale + toff))

			country = station.country
			if country:
				self.ddt.text(
					(xx + toff, yy + round(18 * self.gui.scale)), country, text_colour, 11, bg=bg,
					max_w=rect[2] - (15 * self.gui.scale + toff))

			b_rect = (xx + round(4 * self.gui.scale), yy + round(4 * self.gui.scale), boxx, boxx)
			self.ddt.rect(b_rect, self.colours.box_thumb_background)
			self.tauon.radio_thumb_gen.draw(station, b_rect[0], b_rect[1], b_rect[2])

			if offset == 0:
				offset = rect[2] + round(4 * self.gui.scale)
			else:
				offset = 0
				yy += round(43 * self.gui.scale)

			if yy > y + 300 * self.gui.scale:
				break

			p += 1

		# if to_delete is not None:
		#     del radio_list[to_delete]
		#
		# if self.inp.mouse_up and self.drag and self.inp.mouse_position[1] > yy + round(22 * self.gui.scale):
		#     swap = len(radio_list)

		# if self.drag and not point_proximity_test(self.click_point, self.inp.mouse_position, round(4 * self.gui.scale)):
		#     self.ddt.rect((
		#              self.inp.mouse_position[0] + round(8 * self.gui.scale), self.inp.mouse_position[1] - round(8 * self.gui.scale), 45 * self.gui.scale,
		#              13 * self.gui.scale), self.colours.grey(70))

		# if swap is not None:
		#
		#     old = radio_list[self.drag]
		#     radio_list[self.drag] = None
		#
		#     if swap > self.drag:
		#         swap += 1
		#
		#     radio_list.insert(swap, old)
		#     radio_list.remove(None)
		#
		#     self.drag = None
		#     self.gui.update += 1

		# if not self.inp.mouse_down:
		#     self.drag = None

	def footer(self) -> None:
		y = self.y
		x = self.x + round(15 * self.gui.scale)
		w = self.w
		h = self.h

		yy = y + round(328 * self.gui.scale)
		if self.pctl.playing_state == PlayingState.URL_STREAM and not self.prefs.auto_rec:
			old = self.prefs.auto_rec
			if not old and self.tauon.pref_box.toggle_square(
				x, yy, self.prefs.auto_rec, _("Record and auto split songs"),
				click=self.gui.level_2_click):
				self.show_message(_("Please stop playback first before toggling this setting"))
		elif self.pctl.playing_state == PlayingState.URL_STREAM:
			old = self.prefs.auto_rec
			if old and not self.tauon.pref_box.toggle_square(
				x, yy, self.prefs.auto_rec, _("Record and auto split songs"),
				click=self.gui.level_2_click):
				self.show_message(_("Please stop playback first to end current recording"))

		else:
			old = self.prefs.auto_rec
			self.prefs.auto_rec = self.tauon.pref_box.toggle_square(
				x, yy, self.prefs.auto_rec, _("Record and auto split songs"),
				click=self.gui.level_2_click)
			if self.prefs.auto_rec != old and self.prefs.auto_rec:
				self.show_message(
					_("Tracks will now be recorded."),
					_("Tip: You can press F9 to view the output folder."), mode="info")

		if self.tab == 0:
			if self.draw.button(
				_("Browse"), (x + w) - round(130 * self.gui.scale), yy - round(3 * self.gui.scale),
				press=self.gui.level_2_click, w=round(100 * self.gui.scale)):
				self.tab = 1
		elif self.tab == 1:
			if self.draw.button(
				_("Saved"), (x + w) - round(130 * self.gui.scale), yy - round(3 * self.gui.scale),
				press=self.gui.level_2_click, w=round(100 * self.gui.scale)):
				self.tab = 0
		self.gui.level_2_click = False
class MetaBox:

	def __init__(self, tauon: _PanelApp) -> None:
		self.tauon: _PanelApp = tauon
		self.ddt: TDraw = tauon.ddt
		self.gui: GuiVar = tauon.gui
		self.inp: Input = tauon.inp
		self.coll            = tauon.coll
		self.pctl: _PanelPlayer = tauon.pctl
		self.fonts: Fonts = tauon.fonts
		self.prefs: Prefs = tauon.prefs
		self.fields: Fields = tauon.fields
		self.colours: ColoursClass = tauon.colours
		self.showcase_menu: Menu = tauon.showcase_menu
		self.lyrics_ren_mini: Any = tauon.lyrics_ren_mini

	def l_panel(self, x: int, y: int, w: int, h: int, track: TrackClass, top_border: bool = True) -> None:
		colours = self.colours
		ddt = self.ddt

		if not track:
			return

		border_colour = ColourRGBA(255, 255, 255, 30)
		line1_colour = ColourRGBA(255, 255, 255, 235)
		line2_colour = ColourRGBA(255, 255, 255, 200)
		if test_lumi(colours.gallery_background) < 0.55:
			border_colour = ColourRGBA(0, 0, 0, 30)
			line1_colour = ColourRGBA(0, 0, 0, 200)
			line2_colour = ColourRGBA(0, 0, 0, 230)

		rect = (x, y, w, h)

		ddt.rect(rect, colours.gallery_background)
		if top_border:
			ddt.rect((x, y, w, round(1 * self.gui.scale)), border_colour)
		else:
			ddt.rect((x, y + h - round(1 * self.gui.scale), w, round(1 * self.gui.scale)), border_colour)

		ddt.text_background_colour = colours.gallery_background

		insert = round(9 * self.gui.scale)
		border = round(2 * self.gui.scale)

		compact_mode = False
		if w < h * 1.9:
			compact_mode = True

		art_rect: list[float] = [
			x + insert - 2 * self.gui.scale, y + insert, h - insert * 2 + 1 * self.gui.scale, h - insert * 2 + 1 * self.gui.scale]

		if compact_mode:
			art_rect[0] = x + round(w / 2 - art_rect[2] / 2) - round(1 * self.gui.scale)  # - border

		border_rect = (
			art_rect[0] - border, art_rect[1] - border, art_rect[2] + (border * 2), art_rect[3] + (border * 2))

		self.gui.main_art_box = art_rect


		if (self.inp.mouse_click or self.inp.right_click) and self.tauon.is_level_zero(False):
			if self.coll(border_rect):
				if self.inp.mouse_click:
					self.tauon.milky.projectm.load_next = "random"
				else:
					self.tauon.album_art_gen.cycle_offset(track)
				if self.inp.right_click:
					if self.tauon.prefs.milk and not self.gui.milkdrop_in_widget:
						self.tauon.milky_menu.activate(in_reference=track)
					else:
						self.tauon.picture_menu.activate(in_reference=track)
			elif self.coll(rect):
				if self.inp.mouse_click:
					self.pctl.show_current()
				if self.inp.right_click:
					self.showcase_menu.activate(track)

		ddt.rect(border_rect, border_colour)
		ddt.rect(art_rect, colours.gallery_background)



		self.tauon.album_art_gen.display(track, (art_rect[0], art_rect[1]), (art_rect[2], art_rect[3]))

		self.fields.add(border_rect)

		if self.tauon.prefs.milk and not self.gui.milkdrop_in_widget and self.tauon.pctl.playing_state in (
				PlayingState.PLAYING, PlayingState.URL_STREAM, PlayingState.PAUSED):
			if self.pctl.a_time < 1.3:
				if 1 < self.pctl.a_time < 1.3:
					self.tauon.milky.render(discard=True)
					self.tauon.milky.burn(track)
			else:
				self.tauon.milky.render()
			if self.tauon.pctl.playing_state != PlayingState.PAUSED:
				# Re-arm the next frame while the visualiser animates (the flag
				# clears at frame start, so a mid-draw request means one more frame);
				# the central pacer caps the rate at the display refresh rate.
				self.gui.request_frame()

		elif self.coll(border_rect) and self.tauon.is_level_zero(True):
			showc = self.tauon.album_art_gen.get_info(track)
			self.tauon.art_metadata_overlay(
				art_rect[0] + art_rect[2] + 2 * self.gui.scale, art_rect[1] + art_rect[3] + 12 * self.gui.scale, showc)

		if not compact_mode:
			text_x = border_rect[0] + border_rect[2] + round(10 * self.gui.scale)
			max_w = w - (border_rect[2] + 28 * self.gui.scale)
			yy = y + round(15 * self.gui.scale)

			ddt.text((text_x, yy), track.title, line1_colour, 316, max_w=max_w)
			yy += round(20 * self.gui.scale)
			ddt.text((text_x, yy), track.artist, line2_colour, 14, max_w=max_w)
			yy += round(30 * self.gui.scale)
			ddt.text((text_x, yy), track.album, line2_colour, 14, max_w=max_w)
			yy += round(20 * self.gui.scale)
			ddt.text((text_x, yy), track.date, line2_colour, 14, max_w=max_w)

			self.gui.showed_title = True

	def lyrics(self, x: int, y: int, w: int, h: int, track: TrackClass) -> None:
		bg = self.colours.lyrics_panel_background
		self.ddt.rect((x, y, w, h), bg)
		self.ddt.text_background_colour = bg

		if not track:
			return

		# Test for show lyric menu on right ckick
		if self.coll((x + 10, y, w - 10, h)):
			if self.inp.right_click:  # and (self.pctl.playing_state in (PlayingState.PLAYING, PlayingState.PAUSED)):
				self.gui.force_showcase_index = -1
				self.showcase_menu.activate(track)

		# Test for scroll wheel input
		scroll_area = (x + 10, y, w - 10, h)
		lp = self.lyrics_ren_mini.lyrics_position
		self.lyrics_ren_mini.lyrics_position -= self.tauon.smooth_scroll.get_scroll("sidebar lyrics", scroll_area, (30*self.gui.scale))
		if self.lyrics_ren_mini.lyrics_position != lp:
			if self.lyrics_ren_mini.lyrics_position > 0:
				self.lyrics_ren_mini.lyrics_position = 0
				self.tauon.lyric_side_top_pulse.pulse()

			self.gui.request_frame()

		tw, th = self.ddt.get_text_wh(track.lyrics + "\n", 15, w - 50 * self.gui.scale, True)

		oth = th

		th -= h
		th += 25 * self.gui.scale  # Empty space buffer at end

		if self.lyrics_ren_mini.lyrics_position * -1 > th:
			self.lyrics_ren_mini.lyrics_position = th * -1
			if oth > h:
				self.tauon.lyric_side_bottom_pulse.pulse()

		scroll_w = 15 * self.gui.scale
		if self.gui.maximized:
			scroll_w = 17 * self.gui.scale

		self.lyrics_ren_mini.lyrics_position = self.tauon.mini_lyrics_scroll.draw(
			x + w - 17 * self.gui.scale, y, scroll_w, h,
			self.lyrics_ren_mini.lyrics_position * -1, th,
			jump_distance=160 * self.gui.scale) * -1

		margin = 10 * self.gui.scale
		if self.colours.lm:
			margin += 1 * self.gui.scale

		self.lyrics_ren_mini.render(
			self.pctl.track_queue[self.pctl.queue_step], x + margin,
			y + self.lyrics_ren_mini.lyrics_position + 13 * self.gui.scale,
			w - 50 * self.gui.scale,
			None, 0)

		self.ddt.rect((x, y + h - 1, w, 1), self.colours.lyrics_panel_background)

		self.tauon.lyric_side_top_pulse.render(x, y, w - round(17 * self.gui.scale), 16 * self.gui.scale)
		self.tauon.lyric_side_bottom_pulse.render(x, y + h, w - round(17 * self.gui.scale), 15 * self.gui.scale, bottom=True)

	def draw(self, x: int, y: int, w: int, h: int, track: TrackClass | None=None, lyrics_ui: bool = True) -> None:
		# lyrics_ui=False (the custom-layout titles widget) drops the lyrics
		# context menu and the "Lyrics" showcase link.
		bg = self.colours.side_panel_background
		self.ddt.text_background_colour = bg
		if not self.gui.have_art_bg:
			self.ddt.clear_rect((x, y, w, h))
		self.ddt.rect((x, y, w, h), bg)


		if not track:
			return

		# Test for show lyric menu on right ckick
		if lyrics_ui and self.coll((x + 10, y, w - 10, h)):
			if self.inp.right_click:  # and (self.pctl.playing_state in (PlayingState.PLAYING, PlayingState.PAUSED)):
				self.gui.force_showcase_index = -1
				self.showcase_menu.activate(track)

		if self.pctl.playing_state == PlayingState.STOPPED:
			if not self.prefs.meta_persists_stop and not self.prefs.meta_shows_selected and not self.prefs.meta_shows_selected_always:
				return

		if h < 15:
			return

		# Check for lyrics if auto setting
		self.tauon.test_auto_lyrics(track)


		# # Draw lyrics if available
		# if prefs.show_lyrics_side and pctl.track_queue \
		# and track.lyrics and h > 45 * gui.scale and w > 200 * gui.scale:
		#
		# 	self.lyrics(x, y, w, h, track)

		# Draw standard metadata

		if len(self.pctl.track_queue) > 0:
			if self.pctl.playing_state == PlayingState.STOPPED:
				if not self.prefs.meta_persists_stop and not self.prefs.meta_shows_selected and not self.prefs.meta_shows_selected_always:
					return

			self.ddt.text_background_colour = self.colours.side_panel_background

			if self.coll((x + 10, y, w - 10, h)):
				# Click area to jump to current track
				if self.inp.mouse_click:
					self.pctl.show_current()
					self.gui.request_frame()

			title = ""
			album = ""
			artist = ""
			ext = ""
			date = ""
			genre = ""

			margin = x + 10 * self.gui.scale
			if self.colours.lm:
				margin += 2 * self.gui.scale

			text_width = w - 25 * self.gui.scale
			tr = None

			# if pctl.playing_state != PlayingState.URL_STREAM:

			if self.pctl.playing_state == PlayingState.STOPPED and self.prefs.meta_persists_stop:
				tr = self.pctl.master_library[self.pctl.track_queue[self.pctl.queue_step]]
			if self.pctl.playing_state == PlayingState.STOPPED and self.prefs.meta_shows_selected:
				if -1 < self.pctl.selected_in_playlist < len(self.pctl.multi_playlist[self.pctl.active_playlist_viewing].playlist_ids):
					tr = self.pctl.get_track(self.pctl.multi_playlist[self.pctl.active_playlist_viewing].playlist_ids[self.pctl.selected_in_playlist])

			if self.prefs.meta_shows_selected_always and self.pctl.playing_state != PlayingState.URL_STREAM:
				if -1 < self.pctl.selected_in_playlist < len(self.pctl.multi_playlist[self.pctl.active_playlist_viewing].playlist_ids):
					tr = self.pctl.get_track(self.pctl.multi_playlist[self.pctl.active_playlist_viewing].playlist_ids[self.pctl.selected_in_playlist])

			if tr is None:
				tr = self.pctl.playing_object()
			if tr is None:
				return

			title = tr.title
			album = tr.album
			artist = tr.artist
			ext = tr.file_ext
			if ext == "JELY":
				ext = "Jellyfin"
				if tr.container is not None:
					ext = (tr.container if tr.container is not None else "") + " | Jellyfin"
			if tr.lyrics and lyrics_ui:
				ext += ","
			date = tr.date
			genre = tr.genre

			if not title and not artist:
				title = self.pctl.tag_meta

			if h > 58 * self.gui.scale:
				block_y = y + 7 * self.gui.scale

				if not self.prefs.show_side_art:
					block_y += 3 * self.gui.scale

				if title:
					self.ddt.text(
						(margin, block_y + 2 * self.gui.scale), title, self.colours.side_bar_line1, self.fonts.side_panel_line1,
						max_w=text_width)
				if artist:
					self.ddt.text(
						(margin, block_y + 23 * self.gui.scale), artist, self.colours.side_bar_line2, self.fonts.side_panel_line2,
						max_w=text_width)

				self.gui.showed_title = True

				if h > 140 * self.gui.scale:
					block_y = y + 80 * self.gui.scale
					if artist:
						self.ddt.text(
							(margin, block_y), album, self.colours.side_bar_line2,
							self.fonts.side_panel_line2, max_w=text_width)

					if not genre == date == "":
						line = date
						if genre:
							if line:
								line += " | "
							line += genre

						self.ddt.text(
							(margin, block_y + 20 * self.gui.scale), line, self.colours.side_bar_line2,
							self.fonts.side_panel_line2, max_w=text_width)

					if ext:
						if ext == "RADIO":
							ext = self.tauon.radiobox.playing_title
						sp = self.ddt.text(
							(margin, block_y + 40 * self.gui.scale), ext, self.colours.side_bar_line2,
							self.fonts.side_panel_line2, max_w=text_width)

						if lyrics_ui and tr and tr.lyrics:
							if self.tauon.draw_internal_link(
								margin + sp + 6 * self.gui.scale, block_y + 40 * self.gui.scale, "Lyrics", self.colours.side_bar_line2, self.fonts.side_panel_line2):
								self.prefs.show_lyrics_showcase = True
								self.tauon.enter_showcase_view(track_id=tr.index)

	def centered(self, x: int, y: int, w: int, h: int, track: TrackClass | None) -> None:
		"""Centered track text layout used by the custom-layout "Track: Titles
		(Centred)" widget: artist/title/album text centred in the box, no album
		art. Based on the centered side-panel layout (prefs.side_panel_layout == 1)
		minus that layout's lyrics display and lyrics context menu — the widget
		only ever shows the track text."""
		ddt = self.ddt
		colours = self.colours
		gui = self.gui
		pctl = self.pctl
		window_size = self.tauon.window_size
		radiobox = self.tauon.radiobox
		target_track = track

		if not gui.have_art_bg:
			ddt.clear_rect((x, y, w, h))
		ddt.rect((x, y, w, h), colours.side_panel_background)
		small_mode = window_size[1] < 550 * gui.scale
		text_y = y + round(h * 0.40)
		text_x = x + w // 2
		ww = w - 25 * gui.scale
		gui.showed_title = True
		if target_track:
			ddt.text_background_colour = colours.side_panel_background
			if pctl.playing_state == PlayingState.URL_STREAM and not radiobox.dummy_track.title:
				title = pctl.tag_meta
			else:
				title = target_track.title
				if not title:
					title = clean_string(target_track.filename)
			if small_mode:
				ddt.text((text_x, text_y - 15 * gui.scale, 2), target_track.artist, colours.side_bar_line1, 315, max_w=ww)
				ddt.text((text_x, text_y + 12 * gui.scale, 2), title, colours.side_bar_line1, 216, max_w=ww)
				line = " | ".join(filter(None, (target_track.album, target_track.date, target_track.genre)))
				ddt.text((text_x, text_y + 35 * gui.scale, 2), line, colours.side_bar_line2, 313, max_w=ww)
			else:
				ddt.text((text_x, text_y - 15 * gui.scale, 2), target_track.artist, colours.side_bar_line1, 317, max_w=ww)
				ddt.text((text_x, text_y + 17 * gui.scale, 2), title, colours.side_bar_line1, 218, max_w=ww)
				line = " | ".join(filter(None, (target_track.album, target_track.date, target_track.genre)))
				ddt.text((text_x, text_y + 45 * gui.scale, 2), line, colours.side_bar_line2, 314, max_w=ww)
class PictureRender:

	def __init__(self, tauon: _PanelApp) -> None:
		self.tauon    = tauon
		self.ddt      = tauon.ddt
		self.renderer = tauon.renderer
		self.show = False
		self.path = ""

		self.image_data = None
		self.texture = None
		self.srect = None
		self.size = (0, 0)

	def load(self, path: str, box_size: tuple[int, int] | None = None) -> None:
		if not os.path.isfile(path):
			logging.warning("NO PICTURE FILE TO LOAD")
			return

		g = io.BytesIO()
		g.seek(0)

		im = Image.open(path)
		if box_size is not None:
			im.thumbnail(box_size, Image.Resampling.LANCZOS)

		im.save(g, "BMP")
		g.seek(0)
		self.image_data = g
		logging.info("Save BMP to memory")
		self.size = im.size[0], im.size[1]

	def draw(self, x: int, y: int, w: int | None = None, h: int | None = None) -> None:
		# w/h optionally scale the rendered image (keeping the loaded texture);
		# when omitted the image draws at its loaded (thumbnailed) resolution.
		if self.show is False:
			return

		if self.image_data is not None:
			if self.texture is not None:
				sdl3.SDL_DestroyTexture(self.texture)

			# Convert raw image to sdl texture
			#logging.info("Create Texture")
			s_image = self.ddt.load_image(self.image_data)
			self.texture = sdl3.SDL_CreateTextureFromSurface(self.renderer, s_image)
			sdl3.SDL_DestroySurface(s_image)
			tex_w = pointer(c_float(0))
			tex_h = pointer(c_float(0))
			sdl3.SDL_GetTextureSize(self.texture, tex_w, tex_h)
			self.srect = sdl3.SDL_FRect(round(x), round(y))
			self.srect.w = int(tex_w.contents.value)
			self.srect.h = int(tex_h.contents.value)
			self.image_data = None

		if self.texture is not None:
			self.srect.x = round(x)
			self.srect.y = round(y)
			if w is not None:
				self.srect.w = round(w)
			if h is not None:
				self.srect.h = round(h)
			sdl3.SDL_RenderTexture(self.renderer, self.texture, None, self.srect)
			self.tauon.style_overlay.hole_punches.append(self.srect)
class ArtistInfoBox:

	def __init__(self, tauon: _PanelApp, pctl: _PanelPlayer) -> None:
		self.pctl                  = pctl
		self.tauon                 = tauon
		self.gui                   = tauon.gui
		self.ddt                   = tauon.ddt
		self.inp                   = tauon.inp
		self.coll                  = tauon.coll
		self.prefs                 = tauon.prefs
		self.fields                = tauon.fields
		self.colours               = tauon.colours
		self.smooth_scroll         = tauon.smooth_scroll
		self.user_directory        = tauon.user_directory
		self.a_cache_directory     = tauon.a_cache_directory
		self.artist_info_menu      = tauon.artist_info_menu
		self.artist_picture_render = tauon.artist_picture_render
		self.artist_on = None
		self.min_rq_timer = Timer()
		self.min_rq_timer.force_set(10)

		self.urls: list[tuple[str, ColourRGBA, str]] = []
		self.text = ""
		self.status = ""
		self.scroll_y = 0

		self.process_text_artist = ""
		self.processed_text = ""
		self.th = 0
		self.w = 0
		self.lock = False

		self.mini_box = asset_loader(tauon.bag, tauon.bag.loaded_asset_dc, "mini-box.png", True)

	def manual_dl(self) -> None:
		track = self.pctl.playing_object()
		if track is None or not track.artist:
			self.show_message(_("No artist name found"), mode="warning")
			return

		# Check if the artist has changed
		self.artist_on = get_first_artist(track.artist)

		if not self.lock and self.artist_on:
			self.lock = True
			# self.min_rq_timer.set()

			self.scroll_y = 0
			self.status = _("Looking up...")
			self.process_text_artist = ""

			shoot_dl = threading.Thread(target=self.get_data, args=([track.artist, False, True]))
			shoot_dl.daemon = True
			shoot_dl.start()

	def draw(self, x: int, y: int, w: int, h: int, panel_mode: bool = True) -> None:
		# panel_mode covers the standard artist-info panel's self-management
		# (auto-shrink the bio pref, auto-close when too narrow); the custom
		# layout widget passes False — its segment size is user-controlled.
		if panel_mode:
			if self.gui.artist_panel_height > 300 * self.gui.scale and w < 500 * self.gui.scale:
				self.tauon.bio_set_small()

			if w < 300 * self.gui.scale:
				self.gui.artist_info_panel = False
				self.gui.update_layout = True
				return

		track = self.pctl.playing_object()
		if track is None:
			return

		# Check if the artist has changed
		artist = get_first_artist(track.artist)
		wait = False

		# Activate menu
		if self.inp.right_click and self.coll((x, y, w, h)):
			self.artist_info_menu.activate(in_reference=artist)

		background = self.colours.artist_bio_background
		text_colour = self.colours.artist_bio_text
		self.ddt.rect((x + 10, y + 5, w - 15, h - 5), background)

		if artist != self.artist_on:
			if artist == "":
				return

			if self.min_rq_timer.get() < 10:  # Limit rate
				if os.path.isfile(os.path.join(self.a_cache_directory, artist + "-lfm.txt")):
					pass
				else:
					self.status = _("Cooldown...")
					wait = True

			if self.pctl.playing_time < 2:
				if os.path.isfile(os.path.join(self.a_cache_directory, artist + "-lfm.txt")):
					pass
				else:
					self.status = "..."
					wait = True

			if not wait and not self.lock:
				self.lock = True
				# self.min_rq_timer.set()

				self.scroll_y = 0
				self.status = _("Loading...")

				shoot_dl = threading.Thread(target=self.get_data, args=([track.artist]))
				shoot_dl.daemon = True
				shoot_dl.start()

		if self.process_text_artist != self.artist_on:
			self.process_text_artist = self.artist_on

			text = self.text
			#lic = ""
			link = ""

			if "<a" in text:
				text, ex = text.split('<a href="', 1)
				link, ex = ex.split('">', 1)
				#lic = ex.split("</a>. ", 1)[1]

			text += "\n"
			self.urls = [(link, ColourRGBA(200, 60, 60, 255), "L")]
			for word in text.replace("\n", " ").split(" "):
				if word.strip()[:4] == "http" or word.strip()[:4] == "www.":
					word = word.rstrip(".")
					if word.strip()[:4] == "www.":
						word = "http://" + word
					if "bandcamp" in word:
						self.urls.append((word.strip(), ColourRGBA(200, 150, 70, 255), "B"))
					elif "soundcloud" in word:
						self.urls.append((word.strip(), ColourRGBA(220, 220, 70, 255), "S"))
					elif "twitter" in word:
						self.urls.append((word.strip(), ColourRGBA(80, 110, 230, 255), "T"))
					elif "facebook" in word:
						self.urls.append((word.strip(), ColourRGBA(60, 60, 230, 255), "F"))
					elif "youtube" in word:
						self.urls.append((word.strip(), ColourRGBA(210, 50, 50, 255), "Y"))
					else:
						self.urls.append((word.strip(), ColourRGBA(120, 200, 60, 255), "W"))

			self.processed_text = text
			self.w = -1  # trigger text recalc

		if self.status == "Ready":
			scale = self.gui.scale
			pad = round(10 * scale)
			pic = self.artist_picture_render
			has_pic = bool(pic.show and pic.size and pic.size[0] and pic.size[1])

			# Stack the text under the image when the widget is taller than wide.
			stacked = has_pic and h > w

			img_x = img_y = 0
			img_w = img_h = 0.0
			if has_pic:
				img_ar = pic.size[0] / pic.size[1]
				if stacked:
					# Image on top; cap its height to half the widget height.
					img_w = w - 2 * pad
					img_h = img_w / img_ar
					max_h = h * 0.5 - pad
					if img_h > max_h:
						img_h = max_h
						img_w = img_h * img_ar
				else:
					# Image on the left; cap its width to half the widget width.
					img_h = h - 2 * pad
					img_w = img_h * img_ar
					max_w = w * 0.5 - pad
					if img_w > max_w:
						img_w = max_w
						img_h = img_w / img_ar
				# Never upscale beyond the loaded resolution.
				if img_w > pic.size[0]:
					img_w = pic.size[0]
					img_h = img_w / img_ar
				img_x = round(x + pad)
				img_y = round(y + pad)
				img_w = round(img_w)
				img_h = round(img_h)

			# Text region: below the image when stacked, else to its right.
			# Room for the link-pin column (pins sit at ~25px from the right, and
			# shift left another 15px when the scrollbar shows) plus a small gap.
			right_margin = round(45 * scale)
			if stacked:
				text_x = round(x + pad)
				text_top = img_y + img_h + pad
				text_area_h = (y + h) - text_top - pad
			else:
				text_x = (img_x + img_w + pad) if has_pic else round(x + pad)
				text_top = round(y + 14 * scale)
				text_area_h = h - round(22 * scale)
			text_w = (x + w - right_margin) - text_x
			width = int(text_w - (text_w % 20))

			if self.w != width:
				tw, th = self.ddt.get_text_wh(self.processed_text, 14.5, max(width, 20), True)
				self.th = th
				self.w = width

			scroll_max = max(self.th - text_area_h, 0)
			coll = (x, y, w, h)
			self.scroll_y += self.smooth_scroll.get_scroll("artistinfo",coll,round(20*self.gui.scale))
			self.scroll_y = max(self.scroll_y, 0)
			self.scroll_y = min(self.scroll_y, scroll_max)

			right = x + w - 25 * self.gui.scale

			if self.th > text_area_h:
				self.scroll_y = self.tauon.artist_info_scroll.draw(
					x + w - 20, y + 5, 15, h - 5,
					self.scroll_y, scroll_max, True, jump_distance=250 * self.gui.scale)
				right -= 15

			if has_pic:
				pic.draw(img_x, img_y, img_w, img_h)

			if width > 20 * scale:
				self.ddt.text(
					(text_x, text_top, 4, width, 14000), self.processed_text,
					text_colour, 14.5, bg=background, range_height=text_area_h, range_top=self.scroll_y)

			# Pin the link column to the top of the text region (below the image
			# when stacked) so it never sits on top of the artwork.
			yy = (text_top - round(2 * scale)) if stacked else (y + 12)
			for item in self.urls:
				rect = (right - 2, yy - 2, 16, 16)

				self.fields.add(rect)
				self.mini_box.render(right, yy, alpha_mod(item[1], 100))
				if self.coll(rect):
					if not self.inp.mouse_click:
						self.gui.cursor_want = 3
					if self.inp.mouse_click:
						webbrowser.open(item[0], new=2, autoraise=True)
					self.gui.request_tracklist_redraw()
					w = self.ddt.get_text_w(item[0], 13)
					xx = (right - w) - 17 * self.gui.scale
					self.ddt.rect(
						(xx - 10 * self.gui.scale, yy - 4 * self.gui.scale, w + 20 * self.gui.scale, 24 * self.gui.scale),
						ColourRGBA(15, 15, 15, 255))
					self.ddt.rect(
						(xx - 10 * self.gui.scale, yy - 4 * self.gui.scale, w + 20 * self.gui.scale, 24 * self.gui.scale),
						ColourRGBA(50, 50, 50, 255))

					self.ddt.text((xx, yy), item[0], ColourRGBA(250, 250, 250, 255), 13, bg=ColourRGBA(15, 15, 15, 255))
					self.mini_box.render(right, yy, ColourRGBA(item[1].r + 20, item[1].g + 20, item[1].b + 20, 255))
				# self.ddt.rect_r(rect, [210, 80, 80, 255], True)

				yy += 19 * self.gui.scale
		else:
			self.ddt.text((x + w // 2, y + h // 2 - 7 * self.gui.scale, 2), self.status, ColourRGBA(255, 255, 255, 60), 313, bg=background)

	def get_data(self, artist: str, get_img_path: bool = False, force_dl: bool = False, silent: bool = False) -> str | None:
		if not get_img_path:
			logging.info("Load Bio Data")

		if not silent and artist is None and not get_img_path:
			self.artist_on = None
			self.lock = False
			return ""

		f_artist = filename_safe(artist)

		img_filename = f_artist + "-ftv-full.jpg"
		text_filename = f_artist + "-lfm.txt"
		img_filepath_dcg = os.path.join(self.a_cache_directory, f_artist + "-dcg.jpg")
		img_filepath = os.path.join(self.a_cache_directory, img_filename)
		text_filepath = os.path.join(self.a_cache_directory, text_filename)

		standard_path = os.path.join(self.a_cache_directory, f_artist + "-lfm.webp")
		image_paths = [
			str(self.user_directory / "artist-pictures" / (f_artist + ".png")),
			str(self.user_directory / "artist-pictures" / (f_artist + ".jpg")),
			str(self.user_directory / "artist-pictures" / (f_artist + ".webp")),
			str(self.a_cache_directory / (f_artist + "-ftv-full.jpg")),
			str(self.a_cache_directory / (f_artist + "-lfm.png")),
			str(self.a_cache_directory / (f_artist + "-lfm.jpg")),
			str(self.a_cache_directory / (f_artist + "-lfm.webp")),
			str(self.a_cache_directory / (f_artist + "-dcg.jpg")),
		]

		if get_img_path:
			for path in image_paths:
				if os.path.isfile(path):
					return path
			return ""

		# Check for cache
		box_size = (round(self.gui.artist_panel_height - 20 * self.gui.scale) * 2, round(self.gui.artist_panel_height - 20 * self.gui.scale))
		try:
			if not silent and os.path.isfile(text_filepath):
				logging.info("Load cached bio and image")

				self.artist_picture_render.show = False

				for path in image_paths:
					if os.path.isfile(path):
						filepath = path
						self.artist_picture_render.load(filepath, box_size)
						self.artist_picture_render.show = True
						break

				with open(text_filepath, encoding="utf-8") as f:
					self.text = f.read()
				self.status = "Ready"
				self.gui.request_frame()
				self.artist_on = get_first_artist(artist)
				self.lock = False

				return ""

			if not silent and not force_dl and not self.prefs.auto_dl_artist_data:
				# . Alt: No artist data has been downloaded (try imply this needs to be manually triggered)
				self.status = _("No artist data downloaded")
				self.artist_on = get_first_artist(artist)
				self.artist_picture_render.show = False
				self.lock = False
				return None

			if silent and not force_dl and not self.prefs.auto_dl_artist_data:
				return None
			# Get new from last.fm
			# . Alt: Looking up artist data
			if not silent:
				self.status = _("Looking up...")
				self.gui.request_frame()
				self.text = ""

			data = self.tauon.lastfm.artist_info(artist)
			text = ""

			if data[0] is False:
				if not silent:
					self.artist_picture_render.show = False
					self.status = _("No artist bio found")
					self.artist_on = get_first_artist(artist)
					self.lock = False
				return None
			if data[1]:
				text = data[1]
				if not silent:
					self.text = text
			# cover_link = data[2]
			# Save text as file
			f = open(text_filepath, "w", encoding="utf-8")
			f.write(text)
			f.close()
			logging.info("Save bio text")

			if not silent:
				self.artist_picture_render.show = False

			got_image_path = ""
			if data[3] and self.prefs.enable_fanart_artist:
				try:
					self.tauon.save_fanart_artist_thumb(data[3], img_filepath)
					got_image_path = img_filepath
				except Exception:
					logging.exception("Failed to find image from fanart.tv")

			if not got_image_path and self.tauon.verify_discogs():
				try:
					self.tauon.save_discogs_artist_thumb(artist, img_filepath_dcg)
					got_image_path = img_filepath_dcg
				except Exception:
					logging.exception("Failed to find image from discogs")

			if not got_image_path and data[4]:
				try:
					r = requests.get(data[4], timeout=10)
					html = BeautifulSoup(r.text, "html.parser")
					tag = html.find("meta", property="og:image")
					if tag and tag.get("content"):
						url = tag["content"]
						r = requests.get(url, timeout=10)
						assert len(r.content) > 1000
						with open(standard_path, "wb") as f:
							f.write(r.content)
						got_image_path = standard_path

				except Exception:
					logging.exception("Failed to scrape art")
				else:
					if not got_image_path:
						logging.info(f"No artist image found for '{artist}'")

			if not silent and got_image_path:
				self.artist_picture_render.load(got_image_path, box_size)
				self.artist_picture_render.show = True
			if silent:
				return None

			# Trigger reload of thumbnail in artist list box
			for key, value in list(self.tauon.artist_list_box.thumb_cache.items()):
				if key == artist:
					del self.tauon.artist_list_box.thumb_cache[artist]
					break

			self.status = "Ready"
			self.gui.request_frame()

			# if cover_link and 'http' in cover_link:
			#     # Fetch cover_link
			#     try:
			#         #logging.info("Fetching artist image...")
			#         response = urllib.request.urlopen(cover_link)
			#         info = response.info()
			#         #logging.info("got response")
			#         if info.get_content_maintype() == 'image':
			#
			#             f = open(filepath, 'wb')
			#             f.write(response.read())
			#             f.close()
			#
			#             #logging.info("written file, now loading...")
			#
			#             self.artist_picture_render.load(filepath, round(self.gui.artist_panel_height - 20 * self.gui.scale))
			#             self.artist_picture_render.show = True
			#
			#             self.status = "Ready"
			#             self.gui.update = 2
			#     # except HTTPError as e:
			#     #     self.status = e
			#     #     logging.exception("request failed")
			#     except Exception:
			#         logging.exception("request failed")
			#         self.status = "Request Failed"


		except Exception:
			logging.exception("Failed to load bio")
			self.status = _("Load Failed")

		self.artist_on = get_first_artist(artist)
		self.processed_text = ""
		self.process_text_artist = ""
		self.min_rq_timer.set()
		self.lock = False
		self.gui.request_frame()
		return ""
class RadioThumbGen:
	def __init__(self, tauon: _PanelApp) -> None:
		self.gui               = tauon.gui
		self.ddt               = tauon.ddt
		self.prefs             = tauon.prefs
		self.t_agent           = tauon.t_agent
		self.renderer          = tauon.renderer
		self.r_cache_directory = tauon.r_cache_directory
		self.thread_manager    = tauon.thread_manager
		self.cache = {}
		self.requests: list[tuple[RadioStation, int]] = []
		self.size = 100

	def loader(self) -> None:
		while self.requests:
			item = self.requests[0]
			del self.requests[0]
			station = item[0]
			size = item[1]
			key = (station.title, size)
			src = None
			filename = filename_safe(station.title)

			cache_path = os.path.join(self.r_cache_directory, filename + ".jpg")
			if os.path.isfile(cache_path):
				src = open(cache_path, "rb")
			else:
				cache_path = os.path.join(self.r_cache_directory, filename + ".png")
				if os.path.isfile(cache_path):
					src = open(cache_path, "rb")
				else:
					cache_path = os.path.join(self.r_cache_directory, filename)
					if os.path.isfile(cache_path):
						src = open(cache_path, "rb")

			if src:
				pass
				#logging.info("found cached")
			elif station.icon and station.icon not in self.prefs.radio_thumb_bans:
				try:
					r = requests.get(station.icon, headers={"User-Agent": self.t_agent}, timeout=5, stream=True)
					if r.status_code != 200 or int(r.headers.get("Content-Length", 0)) > 2000000:
						raise Exception("Error get radio thumb")
				except Exception:
					logging.exception("error get radio thumb")
					self.cache[key] = [0]
					if station.icon and station.icon not in self.prefs.radio_thumb_bans:
						self.prefs.radio_thumb_bans.append(station.icon)
					continue
				src = io.BytesIO()
				length = 0
				for chunk in r.iter_content(1024):
					src.write(chunk)
					length += len(chunk)
					if length > 2000000:
						src = None
				if src is None:
					self.cache[key] = [0]
					if station.icon and station.icon not in self.prefs.radio_thumb_bans:
						self.prefs.radio_thumb_bans.append(station.icon)
					continue
				src.seek(0)
				with open(cache_path, "wb") as f:
					f.write(src.read())
				src.seek(0)
			else:
				# logging.info("no icon")
				self.cache[key] = [0]
				continue

			try:
				im = Image.open(src)
				if im.mode != "RGBA":
					im = im.convert("RGBA")
			except Exception:
				logging.exception("malform get radio thumb")
				self.cache[key] = [0]
				if station.icon and station.icon not in self.prefs.radio_thumb_bans:
					self.prefs.radio_thumb_bans.append(station.icon)
				continue

			im = im.resize((size, size), Image.Resampling.LANCZOS)
			g = io.BytesIO()
			g.seek(0)
			im.save(g, "PNG")
			g.seek(0)
			s_image = self.ddt.load_image(g)
			self.cache[key] = [2, None, None, s_image]
			self.gui.request_frame()

			if src is not None:
				src.close()

	def draw(self, station: RadioStation, x: int, y: int, w: int) -> int:
		if not station.title:
			return 0
		key = (station.title, w)

		r = self.cache.get(key)
		if r is None:
			if len(self.requests) < 3:
				self.requests.append((station, w))
				self.thread_manager.ready("radio-thumb")
			return 0
		if r[0] == 2:
			texture = sdl3.SDL_CreateTextureFromSurface(self.renderer, r[3])
			sdl3.SDL_DestroySurface(r[3])
			tex_w = pointer(c_float(0))
			tex_h = pointer(c_float(0))
			sdl3.SDL_GetTextureSize(texture, tex_w, tex_h)
			rect = sdl3.SDL_FRect(0, 0)
			rect.w = int(tex_w.contents.value)
			rect.h = int(tex_h.contents.value)
			r[2] = texture
			r[1] = rect
			r[0] = 1
		if r[0] == 1:
			r[1].x = round(x)
			r[1].y = round(y)
			sdl3.SDL_RenderTexture(self.renderer, r[2], None, r[1])
			return 1
		return 0
class RadioView:
	def __init__(self, tauon: _PanelApp) -> None:
		self.tauon         = tauon
		self.ddt           = tauon.ddt
		self.inp           = tauon.inp
		self.gui           = tauon.gui
		self.coll          = tauon.coll
		self.pctl          = tauon.pctl
		self.fields        = tauon.fields
		self.colours       = tauon.colours
		self.prefs         = tauon.prefs
		self.radiobox      = tauon.radiobox
		self.window_size   = tauon.window_size
		self.smooth_scroll = tauon.smooth_scroll
		bag = tauon.bag
		self.add_icon    = asset_loader(bag, bag.loaded_asset_dc, "add-station.png", True)
		self.search_icon = asset_loader(bag, bag.loaded_asset_dc, "station-search.png", True)
		self.save_icon   = asset_loader(bag, bag.loaded_asset_dc, "save-station.png", True)
		self.menu_icon   = asset_loader(bag, bag.loaded_asset_dc, "radio-menu.png", True)
		self.drag = None
		self.click_point = (0, 0)

	def render(self) -> None:
		pctl        = self.pctl
		gui         = self.gui
		window_size = self.window_size
		radiobox    = self.radiobox
		# box = int(window_size[1] * 0.4 + 120 * gui.scale)
		# box = min(window_size[0] // 2, box)
		bg = self.colours.playlist_panel_background
		self.ddt.rect((0, gui.panelY, window_size[0], window_size[1] - gui.panelY), bg)
		#logging.info(prefs.radio_urls)

		# Add station button
		x = window_size[0] - round(60 * gui.scale)
		y = gui.panelY + round(30 * gui.scale)
		rect = (x, y, round(25 * gui.scale), round(25 * gui.scale))
		self.fields.add(rect)

		# right buttions colours
		a_colour = rgb_add_hls(bg, l=0.2, s=-0.3) #colours.box_button_text_highlight
		b_colour = rgb_add_hls(bg, l=0.4, s=-0.3) #colours.box_button_text_highlight
		if test_lumi(bg) < 0.38:
			a_colour = ColourRGBA(20, 20, 20, 200)
			b_colour = ColourRGBA(60, 60, 60, 200)

		if self.coll(rect):
			colour = b_colour
			if self.inp.mouse_click:
				self.tauon.add_station()
		else:
			colour = a_colour

		self.add_icon.render(rect[0] + round(4 * gui.scale), rect[1] + round(4 * gui.scale), colour)

		y += round(33 * gui.scale)
		rect = (x, y, round(25 * gui.scale), round(25 * gui.scale))
		self.fields.add(rect)

		if not self.coll(rect):
			colour = a_colour
		else:
			colour = b_colour
			if self.inp.mouse_click:
				self.tauon.station_browse()
		self.search_icon.render(rect[0] + round(4 * gui.scale), rect[1] + round(4 * gui.scale), colour)

		if pctl.radio_playlist_viewing > len(pctl.radio_playlists) - 1:
			pctl.radio_playlist_viewing = 0
		if not pctl.radio_playlists:
			return
		radios = pctl.radio_playlists[pctl.radio_playlist_viewing].stations

		y += round(32 * gui.scale)
		if pctl.playing_state == PlayingState.URL_STREAM and radiobox.loaded_station not in radios:
			rect = (x, y, round(25 * gui.scale), round(25 * gui.scale))
			self.fields.add(rect)

			if not self.coll(rect):
				colour = a_colour
			else:
				colour = b_colour
				if self.inp.mouse_click:
					radios.append(radiobox.loaded_station)
					self.tauon.toast(_("Added station to: ") + pctl.radio_playlists[pctl.radio_playlist_viewing].name)

			self.save_icon.render(rect[0] + round(3 * gui.scale), rect[1] + round(4 * gui.scale), colour)

		x = round(30 * gui.scale)
		y = gui.panelY + round(30 * gui.scale)
		yy = y

		rbg = rgb_add_hls(self.colours.playlist_panel_background, 0, 0.03, -0.03)
		tbg = rgb_add_hls(self.colours.playlist_panel_background, 0, 0.07, -0.05)
		if contrast_ratio(bg, rbg) < 1.05:
			rbg = ColourRGBA(30, 30, 30, 255)
			tbg = ColourRGBA(60, 60, 60, 255)

		w = round(400 * gui.scale)
		h = round(55 * gui.scale)
		gap = round(7 * gui.scale)

		mm = (window_size[1] - (gui.panelBY + yy + h + round(15 * gui.scale))) // (h + gap) + 1

		count = 0
		scroll = pctl.radio_playlists[pctl.radio_playlist_viewing].scroll
		scroll_area = (0, gui.panelY, w + round(70 * gui.scale), window_size[1] - gui.panelBY - gui.panelY)
		touch_scroll = self.inp.touch_scroll_y != 0 and coll_point(self.inp.touch_position, scroll_area)
		use_smooth_scroll = (
			self.smooth_scroll.enabled()
			or touch_scroll
			or self.smooth_scroll.active("radios")
		)
		if not radiobox.active or (radiobox.active and not self.coll((radiobox.x, radiobox.y, radiobox.w, radiobox.h))):
			if use_smooth_scroll:
				if gui.panelY < self.inp.mouse_position[1] < window_size[1] - gui.panelBY \
				and self.inp.mouse_position[0] < w + round(70 * gui.scale) and self.inp.mouse_wheel:
					self.smooth_scroll.add_wheel_motion("radios", -self.inp.mouse_wheel, h + gap)
				if self.inp.touch_released:
					self.smooth_scroll.release_touch("radios")
				elif touch_scroll:
					self.smooth_scroll.apply_touch_drag("radios", -self.inp.touch_scroll_y)
				scroll += self.smooth_scroll.step_motion("radios") / max(h + gap, 1)
			elif gui.panelY < self.inp.mouse_position[1] < window_size[1] - gui.panelBY \
			and self.inp.mouse_position[0] < w + round(70 * gui.scale):
				scroll_distance = self.smooth_scroll.scroll("radios")
				scroll -= scroll_distance

		scroll = min(scroll, len(radios) - mm + 1)
		scroll = max(scroll, 0)
		if len(radios) > mm:
			scroll = self.tauon.radio_view_scroll.draw(
				round(7 * gui.scale), yy, round(15 * gui.scale), (mm * (h + gap)) - gap, scroll, len(radios) - mm + 1)
		else:
			scroll = 0

		pctl.radio_playlists[pctl.radio_playlist_viewing].scroll = scroll
		insert = None
		scroll_start = int(scroll)
		scroll_offset = (scroll - scroll_start) * max(h + gap, 1)
		yy = y - scroll_offset

		for i, radio in enumerate(radios):
			if count == mm:
				break
			if i < scroll_start:
				continue
			count += 1
			rect = (x, yy, w, h)
			self.ddt.rect(rect, rbg)
			yyy = yy
			pic_rect = (
			x + round(5 * gui.scale), yy + round(5 * gui.scale), h - round(10 * gui.scale), h - round(10 * gui.scale))
			self.ddt.rect(pic_rect, tbg)
			self.tauon.radio_thumb_gen.draw(radio, pic_rect[0], pic_rect[1], pic_rect[2])

			l1_colour = ColourRGBA(10, 10, 10, 210)
			if test_lumi(rbg) > 0.45:
				l1_colour = ColourRGBA(255, 255, 255, 220)
			l2_colour = ColourRGBA(30, 30, 30, 200)
			if test_lumi(rbg) > 0.45:
				l2_colour = ColourRGBA(245, 245, 245, 200)

			toff = h + round(2 * gui.scale)
			yyy += round(9 * gui.scale)
			self.ddt.text(
				(x + toff, yyy), radio.title, l1_colour, 212,
				max_w=w - (toff + round(90 * gui.scale)), bg=rbg)
			yyy += round(19 * gui.scale)
			self.ddt.text(
				(x + toff, yyy), radio.country, l2_colour, 312,
				max_w=w - (toff + round(90 * gui.scale)), bg=rbg)

			hit = False
			start_rect = (
				x + (w - round(40 * gui.scale)), yy + round(8 * gui.scale), h - round(15 * gui.scale),
				round(42 * gui.scale))
			# self.ddt.rect(hit_rect, [255, 255, 255, 3])
			self.fields.add(start_rect)
			colour = rgb_add_hls(tbg, l=0.05)
			if self.coll(start_rect):
				if self.inp.mouse_click:
					radiobox.start(radio)
					hit = True
				colour = rgb_add_hls(colour, l=0.3)

			self.tauon.bottom_bar1.play_button.render(x + (w - round(30 * gui.scale)), yy + round(23 * gui.scale), colour)

			extra_rect = (
				x + (w - round(82 * gui.scale)), yy + round(8 * gui.scale), h - round(15 * gui.scale),
				round(35 * gui.scale))
			# self.ddt.rect(extra_rect, [255, 255, 255, 2])
			self.fields.add(extra_rect)
			colour = rgb_add_hls(tbg, l=0.05)
			if self.coll(extra_rect):
				colour = rgb_add_hls(colour, l=0.3) #alpha_mod(colours.side_bar_line1, 47)
				if self.inp.mouse_click:
					hit = True
					radiobox.x = extra_rect[0] + extra_rect[2]
					radiobox.y = extra_rect[1]
					self.tauon.radio_context_menu.activate((i, radio), position=(radiobox.x, yy + round(20 * gui.scale)))

			self.menu_icon.render(x + (w - round(75 * gui.scale)), yy + round(26 * gui.scale), colour)

			# self.tauon.bottom_bar1.play_button.render(x + (w - round(30 * gui.scale)), yy + round(23 * gui.scale), colour)
			if self.inp.mouse_up and self.drag and self.coll(rect):
				if radiobox.active and self.coll((radiobox.x, radiobox.y, radiobox.w, radiobox.h)):
					pass
				else:
					insert = i
				if not radiobox.active and self.drag in radios and radios.index(self.drag) < i:
					insert += 1
			elif self.coll(rect) and not hit and self.inp.mouse_click:
				self.drag = radio
				self.click_point = copy.copy(self.inp.mouse_position)

			yy += round(h + gap)

		if self.inp.mouse_up and self.drag and not insert and self.drag not in radios:
			if not (radiobox.active and self.coll((radiobox.x, radiobox.y, radiobox.w, radiobox.h))):
				if self.inp.mouse_position[1] > gui.panelY:
					insert = len(radios)

		count = ((window_size[0] - w) / 2) + w
		boxx = round(200 * gui.scale)
		art_rect = (count - boxx / 2, window_size[1] / 3 - boxx / 2, boxx, boxx)

		if window_size[0] > round(700 * gui.scale):
			if pctl.playing_state == PlayingState.URL_STREAM and radiobox.loaded_station:
				r = self.tauon.album_art_gen.display(radiobox.dummy_track, (art_rect[0], art_rect[1]), (art_rect[2], art_rect[3]))
				if r:
					r = self.tauon.radio_thumb_gen.draw(radiobox.loaded_station, art_rect[0], art_rect[1], art_rect[2])
					# if not r:
					# 	self.ddt.rect(art_rect, colours.b)
			# else:
			# 	self.ddt.rect(art_rect, [40, 40, 40, 255])

			yy = window_size[1] / 3 - boxx / 2
			yy += boxx + round(30 * gui.scale)

			if radiobox.loaded_station and pctl.playing_state == PlayingState.URL_STREAM:
				space = window_size[0] - round(500 * gui.scale)
				self.ddt.text(
					(count, yy, 2), radiobox.loaded_station.title, ColourRGBA(230, 230, 230, 255), 213, max_w=space)
				yy += round(25 * gui.scale)
				self.ddt.text((count, yy, 2), radiobox.song_key, ColourRGBA(230, 230, 230, 255), 313, max_w=space)
				if radiobox.dummy_track.album:
					yy += round(21 * gui.scale)
					self.ddt.text((count, yy, 2), radiobox.dummy_track.album, ColourRGBA(230, 230, 230, 255), 313, max_w=space)

		if self.drag:
			gui.update_on_drag = True

		if insert is not None:
			radios.insert(insert, "New")
			if self.drag in radios:
				radios.remove(self.drag)
			else:
				self.tauon.toast(_("Added station to: ") + pctl.radio_playlists[pctl.radio_playlist_viewing].name)

			radios[radios.index("New")] = self.drag
			self.drag = None
			gui.request_frame()
