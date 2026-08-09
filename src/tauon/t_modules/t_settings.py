"""Settings and preferences overlay."""

from __future__ import annotations

import builtins
import colorsys
import copy
import ctypes
import glob
import locale as py_locale
import logging
import math
import os
import random
import re
import threading
import webbrowser
from collections.abc import Callable, Sequence
from ctypes import c_void_p
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

import requests
import sdl3

from tauon.t_modules.t_enums import Backend, PlayingState
from tauon.t_modules.t_extra import (
	Timer,
	alpha_blend,
	alpha_mod,
	coll_point,
	filename_safe,
	get_artist_safe,
	grow_rect,
	hls_to_rgb,
	is_light,
	rgb_add_hls,
	rgb_to_hls,
	seconds_to_day_hms,
	shooter,
)
from tauon.t_modules.t_input import copy_from_clipboard, copy_to_clipboard
from tauon.t_modules.t_lyrics import lyric_sources, uses_scraping
from tauon.t_modules.t_models import ColourRGBA, Directories, Formats
from tauon.t_modules.t_prefs import Prefs
from tauon.t_modules.t_phazor import phazor_exists
from tauon.t_modules.t_scrobble import LastFMapi
from tauon.t_modules.t_state import ColoursClass, GuiVar, Input, MenuIcon, asset_loader
from tauon.t_modules.t_stars import StarStore
from tauon.t_modules.t_themeload import load_theme, save_theme
from tauon.t_modules.t_text import TextBox2
from tauon.t_modules.t_draw import TDraw
from tauon.t_modules.t_widgets import Fields, ScrollBox

if TYPE_CHECKING:
	from tauon.t_modules.t_player import PlayerCtl
	from tauon.t_modules.t_protocols import AppLike as Tauon


class BagLike(Protocol):
	prefs: Any
	window_size: Any
	logical_size: Any

	def __getattr__(self, name: str) -> Any: ...


Bag = BagLike
translate = getattr(builtins, "_", lambda text: text)

class Over:
	def __init__(self, tauon: Tauon) -> None:
		self.tauon:             Tauon = tauon
		self.bag:                 Bag = tauon.bag
		self.gui:              GuiVar = tauon.gui
		self.inp:               Input = tauon.inp
		self.ddt:               TDraw = tauon.ddt
		self.renderer                 = tauon.renderer
		self.coll                     = tauon.coll
		self.pctl:          PlayerCtl = tauon.pctl
		self.dirs:        Directories = tauon.dirs
		self.prefs:             Prefs = tauon.prefs
		self.fields:           Fields = tauon.fields
		self.lastfm:        LastFMapi = tauon.lastfm
		self.formats:         Formats = tauon.formats
		self.colours:    ColoursClass = tauon.colours
		self.window_size              = tauon.window_size
		self.show_message             = tauon.show_message
		self.album_mode_art_size: int = tauon.album_mode_art_size
		self.platform_system:     str = tauon.platform_system
		self.user_directory:     Path = tauon.user_directory
		self.flatpak_mode:       bool = tauon.flatpak_mode
		self.star_store:    StarStore = tauon.star_store
		self.snap_mode:          bool = tauon.snap_mode
		self.t_version:           str = tauon.t_version
		self.wayland:            bool = tauon.wayland
		self.macos:              bool = tauon.macos
		self.windows:               bool = tauon.windows
		self.phazor_found:       bool = phazor_exists(tauon.pctl)
		self.init2done:          bool = False

		# self.tab_width = round(115 * self.gui.scale)
		self.w = 100
		self.h = 100

		self.box_x = 100
		self.box_y = 100
		self.item_x_offset = round(25 * self.gui.scale)

		self.ext_ratio = {}
		self.last_db_size = -1

		self.enabled = False
		self.click = False
		self.right_click = False
		self.scroll = 0
		self.lock = False

		self.func_page = 0
		self.tab_active = 0
		self.settings_nav_scroll = 0.0
		self.settings_nav_scroll_bar = ScrollBox(tauon=tauon, pctl=tauon.pctl)
		self.settings_content_scroll = 0.0
		self.settings_content_scroll_bar = ScrollBox(tauon=tauon, pctl=tauon.pctl)
		self.settings_scale_preview_value: float | None = None
		# True until the first card of the settings category being rendered
		# has drawn its accent bar; only that card gets one (see
		# draw_settings_section / render_settings_category)
		self.settings_accent_bar_pending: bool = True
		self.settings_category_offsets: list[float] = []
		self.settings_doc_texture: sdl3.LP_SDL_Texture | None = None
		self.settings_doc_texture_size = (0, 0)
		self.app_icon = asset_loader(self.bag, self.bag.loaded_asset_dc, "app-icon.png")
		self.tabs = [
			_("General"),
			_("Connections"),
			_("Audio"),
			_("Theme"),
			_("View"),
			_("Transcode"),
			_("Services"),
			_("Advanced"),
			_("Stats"),
			_("About"),
		]

		self.stats_timer = Timer()
		self.stats_timer.force_set(1000)
		self.stats_pl_timer = Timer()
		self.stats_pl_timer.force_set(1000)
		self.total_albums = 0
		self.stats_pl = 0
		self.stats_pl_albums = 0
		self.stats_pl_length = 0

		self.device_scroll_bar_position = 0

		self.lyrics_panel = False
		self.account_view = 0

		self.settings_text_focus: TextBox2 | None = None
		self.settings_text_order: list[TextBox2] = []
		self.settings_text_seen: list[TextBox2] = []
		self.settings_text_hit = False

		self.themes = []
		self.theme_editor_enabled = False
		self.theme_editor_selected_attr = THEME_EDITOR_COMPONENTS[0][1][0]
		self.theme_editor_selected_attrs = THEME_EDITOR_COMPONENTS[0][1]
		self.theme_editor_dropdown_expansions = [False] * len(THEME_EDITOR_COMPONENTS)
		self.theme_editor_clipboard: ColourRGBA | None = None
		self.theme_editor_list_scroll = 0.0
		self.theme_editor_list_scroll_bar = ScrollBox(tauon=tauon, pctl=tauon.pctl)
		self.theme_editor_title_box: TextBox2 = TextBox2(tauon=tauon)
		self.theme_editor_original_colours: ColoursClass | None = None
		self.theme_editor_draft_colours: ColoursClass | None = None
		self.theme_editor_original_theme_name = ""
		self.theme_editor_original_theme_number = 0
		self.theme_editor_target_path: Path | None = None
		self.theme_editor_is_new = False
		self.theme_editor_dirty = False
		self.theme_editor_sv_texture = None
		self.theme_editor_sv_texture_key: tuple[int, int, int] | None = None
		self.theme_editor_hue_texture = None
		self.theme_editor_hue_texture_key: tuple[int, int] | None = None
		self.theme_editor_drag_target: str | None = None
		self.theme_editor_window_position: tuple[int, int] | None = None
		self.theme_editor_window_drag_start_mouse: tuple[int, int] = (0, 0)
		self.theme_editor_window_drag_start_position: tuple[int, int] = (0, 0)
		self.theme_editor_hue_value = 0.0
		self.theme_editor_sat_value = 1.0
		self.theme_editor_val_value = 1.0
		self.theme_editor_alpha_value = 1.0
		self.view_supporters = False

	def destroy_settings_texture(self) -> None:
		if self.settings_doc_texture is not None:
			sdl3.SDL_DestroyTexture(self.settings_doc_texture)
			self.settings_doc_texture = None
			self.settings_doc_texture_size = (0, 0)

	def destroy_theme_editor_gradient_textures(self) -> None:
		if self.theme_editor_sv_texture is not None:
			sdl3.SDL_DestroyTexture(self.theme_editor_sv_texture)
			self.theme_editor_sv_texture = None
		if self.theme_editor_hue_texture is not None:
			sdl3.SDL_DestroyTexture(self.theme_editor_hue_texture)
			self.theme_editor_hue_texture = None
		self.theme_editor_sv_texture_key = None
		self.theme_editor_hue_texture_key = None

	def ensure_settings_texture(self, size: tuple[int, int]) -> sdl3.LP_SDL_Texture:
		if self.settings_doc_texture is not None and self.settings_doc_texture_size == size:
			return self.settings_doc_texture

		self.destroy_settings_texture()
		self.settings_doc_texture = sdl3.SDL_CreateTexture(
			self.renderer,
			sdl3.SDL_PIXELFORMAT_ARGB8888,
			sdl3.SDL_TEXTUREACCESS_TARGET,
			size[0],
			size[1],
		)
		sdl3.SDL_SetTextureBlendMode(self.settings_doc_texture, sdl3.SDL_BLENDMODE_BLEND)
		self.settings_doc_texture_size = size
		return self.settings_doc_texture

	def settings_tab_accent(self, index: int) -> ColourRGBA:
		accents = (
			ColourRGBA(174, 118, 255, 255),
			ColourRGBA(196, 102, 244, 255),
			ColourRGBA(154, 124, 255, 255),
			ColourRGBA(226, 102, 216, 255),
			ColourRGBA(204, 122, 238, 255),
			ColourRGBA(236, 92, 190, 255),
			ColourRGBA(180, 112, 244, 255),
			ColourRGBA(216, 116, 230, 255),
			ColourRGBA(198, 136, 255, 255),
			ColourRGBA(229, 125, 214, 255),
			ColourRGBA(184, 184, 196, 255),
		)
		return accents[index % len(accents)]

	def sync_settings_nav_scroll(self, scroll_area: tuple[int, int, int, int], row_height: int, visible_rows: int) -> float:
		scroll_source = "settings nav"
		max_scroll = max(len(self.tabs) - visible_rows, 0)
		wheel_delta = self.scroll if self.scroll else self.inp.mouse_wheel
		if max_scroll <= 0:
			self.settings_nav_scroll = 0
			self.tauon.smooth_scroll.reset_motion(scroll_source)
			return 0

		touch_scroll = self.inp.touch_scroll_y != 0 and coll_point(self.inp.touch_position, scroll_area)
		use_smooth_scroll = (
			self.tauon.smooth_scroll.enabled()
			or touch_scroll
			or self.tauon.smooth_scroll.active(scroll_source)
		)
		if use_smooth_scroll:
			if self.coll(scroll_area) and wheel_delta:
				self.tauon.smooth_scroll.add_wheel_motion(scroll_source, -wheel_delta, row_height)
			if self.inp.touch_released:
				self.tauon.smooth_scroll.release_touch(scroll_source)
			elif touch_scroll:
				self.tauon.smooth_scroll.apply_touch_drag(scroll_source, -self.inp.touch_scroll_y)
			self.settings_nav_scroll += self.tauon.smooth_scroll.step_motion(scroll_source) / max(row_height, 1)
		elif self.coll(scroll_area) and wheel_delta:
			self.settings_nav_scroll -= wheel_delta

		self.settings_nav_scroll = min(max(self.settings_nav_scroll, 0), max_scroll)
		return max_scroll

	def draw_audio_device_selector(self, rect: tuple[int, int, int, int], accent: ColourRGBA | None = None) -> None:
		gui = self.gui
		ddt = self.ddt
		prefs = self.prefs
		colours = self.colours
		if accent is None:
			accent = self.settings_page_accent()

		x, y, w, h = rect
		inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
			rect,
			_("Audio Output Device"),
			_("Choose where Tauon sends playback."),
			accent,
		)

		section_bottom = y + h - round(14 * gui.scale)
		panel_fill = alpha_blend(ColourRGBA(255, 255, 255, 5), colours.box_background)
		panel_border = alpha_blend(ColourRGBA(255, 255, 255, 16), colours.box_text_border)
		selected_fill = alpha_blend(alpha_mod(accent, 34), panel_fill)
		hover_fill = alpha_blend(ColourRGBA(255, 255, 255, 12), panel_fill)
		badge_fill = alpha_blend(alpha_mod(accent, 22), panel_fill)
		badge_border = alpha_blend(alpha_mod(accent, 90), panel_border)
		panel_gap = round(8 * gui.scale)

		selected_device = prefs.phazor_device_selected
		if selected_device not in prefs.phazor_devices and prefs.phazor_devices:
			selected_device = prefs.phazor_devices[0]
		if not selected_device:
			selected_device = _("No device selected")

		stack_label_h = round(16 * gui.scale) if self.platform_system == "Linux" else 0
		stack_choice_h = round(42 * gui.scale) if self.platform_system == "Linux" else 0
		stack_gap = round(8 * gui.scale) if self.platform_system == "Linux" else 0
		list_y = inner_y
		list_bottom = section_bottom
		if self.platform_system == "Linux":
			list_bottom -= stack_choice_h + stack_gap + stack_label_h + round(10 * gui.scale)

		list_rect = (
			inner_x,
			list_y,
			inner_w,
			max(round(92 * gui.scale), list_bottom - list_y),
		)
		ddt.bordered_rect(list_rect, panel_fill, panel_border, round(1 * gui.scale))
		self.fields.add(list_rect)

		content_pad_x = round(8 * gui.scale)
		content_pad_y = round(8 * gui.scale)
		row_h = round(34 * gui.scale)
		row_gap = round(6 * gui.scale)
		row_step = row_h + row_gap
		scrollbar_w = round(10 * gui.scale)
		scrollbar_gap = round(8 * gui.scale)

		visible_rows = int(max(1, (list_rect[3] - content_pad_y * 2 + row_gap) // max(row_step, 1)))
		max_device_scroll = max(len(prefs.phazor_devices) - visible_rows, 0)
		if self.coll(list_rect) and self.scroll:
			self.device_scroll_bar_position -= self.scroll
		self.device_scroll_bar_position = min(max(self.device_scroll_bar_position, 0), max_device_scroll)
		scroll_index = int(self.device_scroll_bar_position)

		row_w = list_rect[2] - content_pad_x * 2
		if max_device_scroll > 0:
			row_w -= scrollbar_w + scrollbar_gap
			scrollbar_x = list_rect[0] + list_rect[2] - scrollbar_w - content_pad_x
			self.device_scroll_bar_position = self.tauon.device_scroll.draw(
				scrollbar_x,
				list_rect[1] + content_pad_y,
				scrollbar_w,
				list_rect[3] - content_pad_y * 2,
				self.device_scroll_bar_position,
				max_device_scroll,
				click=self.click,
			)
			self.device_scroll_bar_position = min(max(self.device_scroll_bar_position, 0), max_device_scroll)
			scroll_index = int(self.device_scroll_bar_position)

		if not prefs.phazor_devices:
			ddt.text(
				(list_rect[0] + list_rect[2] // 2, list_rect[1] + list_rect[3] // 2 - round(8 * gui.scale), 2),
				_("No output devices detected"),
				colours.box_text_label,
				212,
				bg=panel_fill,
				max_w=list_rect[2] - content_pad_x * 2,
			)
			ddt.text(
				(list_rect[0] + list_rect[2] // 2, list_rect[1] + list_rect[3] // 2 + round(10 * gui.scale), 2),
				_("Try refreshing audio or restarting Tauon."),
				colours.box_text_label,
				10,
				bg=panel_fill,
				max_w=list_rect[2] - content_pad_x * 2,
			)
		else:
			reload = False
			row_y = list_rect[1] + content_pad_y
			slice_end = int(scroll_index + visible_rows)
			for name in prefs.phazor_devices[scroll_index:slice_end]:
				row_rect = (list_rect[0] + content_pad_x, row_y, row_w, row_h)
				row_hover = self.coll(row_rect)
				row_selected = selected_device == name

				if self.click and row_hover and not row_selected:
					prefs.phazor_device_selected = name
					selected_device = name
					row_selected = True
					reload = True

				row_fill = panel_fill
				if row_hover:
					row_fill = hover_fill
				if row_selected:
					row_fill = selected_fill

				row_border = badge_border if row_selected else panel_border
				ddt.bordered_rect(row_rect, row_fill, row_border, round(1 * gui.scale))

				indicator_rect = (
					row_rect[0] + round(10 * gui.scale),
					row_rect[1] + (row_rect[3] - round(12 * gui.scale)) // 2,
					round(12 * gui.scale),
					round(12 * gui.scale),
				)
				ddt.bordered_rect(
					indicator_rect,
					alpha_blend(ColourRGBA(255, 255, 255, 8), row_fill),
					row_border,
					round(1 * gui.scale),
				)
				if row_selected:
					ddt.rect(
						(
							indicator_rect[0] + round(3 * gui.scale),
							indicator_rect[1] + round(3 * gui.scale),
							indicator_rect[2] - round(6 * gui.scale),
							indicator_rect[3] - round(6 * gui.scale),
						),
						accent,
					)

				label_x = indicator_rect[0] + indicator_rect[2] + round(10 * gui.scale)
				label_max_w = row_rect[2] - (label_x - row_rect[0]) - round(12 * gui.scale)
				device_name = self.tauon.trunc_line(name, 11, label_max_w)
				text_colour = colours.box_sub_text if row_selected or row_hover else colours.box_text
				ddt.text(
					(label_x, row_rect[1] + round(8 * gui.scale)),
					device_name,
					text_colour,
					11,
					bg=row_fill,
					max_w=label_max_w,
				)
				self.fields.add(row_rect)
				row_y += row_step

			if reload:
				self.pctl.playerCommand = "set-device"
				self.pctl.playerCommandReady = True

		if self.platform_system == "Linux":
			def set_pipewire(enabled: bool) -> None:
				old_pipewire = prefs.pipewire
				prefs.pipewire = enabled
				if prefs.pipewire != old_pipewire:
					self.show_message(_("Please restart Tauon for this change to take effect"))

			footer_label_y = section_bottom - stack_choice_h - stack_gap - stack_label_h
			ddt.text((inner_x, footer_label_y), _("Audio stack"), colours.box_text_label, 11, bg=self.ddt.text_background_colour)
			choice_y = footer_label_y + stack_label_h
			choice_w = (inner_w - panel_gap) // 2
			self.settings_choice_tile(
				(inner_x, choice_y, choice_w, stack_choice_h),
				_("PulseAudio"),
				"",
				not prefs.pipewire,
				lambda: set_pipewire(False),
				accent,
			)
			self.settings_choice_tile(
				(inner_x + choice_w + panel_gap, choice_y, choice_w, stack_choice_h),
				_("PipeWire"),
				"",
				prefs.pipewire,
				lambda: set_pipewire(True),
				accent,
			)

	def reload_device(self, _unused=None) -> None:
		self.pctl.playerCommand = "reload"
		self.pctl.playerCommandReady = True

	def settings_page_accent(self, page: int | None = None) -> ColourRGBA:
		accents = (
			ColourRGBA(174, 118, 255, 255),
			ColourRGBA(196, 102, 244, 255),
			ColourRGBA(226, 102, 216, 255),
			ColourRGBA(180, 112, 244, 255),
			ColourRGBA(204, 122, 238, 255),
		)
		if page is None:
			page = self.func_page
		return accents[page % len(accents)]

	def refresh_theme_presets(self) -> None:
		self.themes = [(ColoursClass(), "Mindaro", 0)]
		for index, theme in enumerate(get_themes(self.dirs)):
			colours = ColoursClass()
			try:
				load_theme(colours, Path(theme[0]))
			except Exception:
				logging.exception("Error loading theme preset preview")
				continue
			self.themes.append((colours, theme[1], index + 1))

	def get_active_theme_item(self) -> tuple[str, str] | None:
		if self.prefs.theme <= 0:
			return None
		themes = get_themes(self.dirs)
		theme_index = self.prefs.theme - 1
		if theme_index < 0 or theme_index >= len(themes):
			return None
		return themes[theme_index]

	def theme_path_is_user(self, path: Path) -> bool:
		if self.dirs.user_directory == self.dirs.install_directory:
			return False
		try:
			path.resolve().relative_to((self.dirs.user_directory / "theme").resolve())
		except ValueError:
			return False
		return True

	def active_theme_path(self) -> Path | None:
		theme_item = self.get_active_theme_item()
		if theme_item is None:
			return None
		return Path(theme_item[0])

	def active_theme_is_user_editable(self) -> bool:
		path = self.active_theme_path()
		return path is not None and self.theme_path_is_user(path)

	def unique_theme_name(self, base_name: str) -> str:
		existing_names = {theme[1] for theme in get_themes(self.dirs)}
		if base_name not in existing_names and base_name != "Mindaro":
			return base_name
		index = 2
		while True:
			candidate = f"{base_name} {index}"
			if candidate not in existing_names and candidate != "Mindaro":
				return candidate
			index += 1

	def theme_editor_selected_label(self) -> str:
		for label, attr in THEME_EDITOR_COMPONENTS:
			if attr[0] in self.theme_editor_selected_attrs:
				return _(label)
		return _("Component")

	def theme_colour_to_hex(self, colour: ColourRGBA) -> str:
		return f"#{colour.r:02X}{colour.g:02X}{colour.b:02X}{colour.a:02X}"

	def parse_theme_colour_text(self, text: str) -> ColourRGBA | None:
		match = re.fullmatch(r"#?([0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})", text.strip())
		if not match:
			return None
		value = match.group(1)
		if len(value) == 6:
			value += "FF"
		return ColourRGBA(
			int(value[0:2], 16),
			int(value[2:4], 16),
			int(value[4:6], 16),
			int(value[6:8], 16),
		)

	def theme_editor_current_colour(self) -> ColourRGBA:
		source = self.theme_editor_draft_colours or self.colours
		colour = getattr(source, self.theme_editor_selected_attr, None)
		if colour is None:
			return ColourRGBA(255, 255, 255, 255)
		return ColourRGBA(colour.r, colour.g, colour.b, colour.a)

	def apply_theme_preview_colours(self, source: ColoursClass) -> None:
		preview = clone_theme_colours(source)
		if self.prefs.transparent_mode:
			preview.apply_transparency(full=self.prefs.transparent_mode == 2)
		self.colours.__dict__.clear()
		self.colours.__dict__.update(copy.deepcopy(preview.__dict__))
		if self.colours.deco:
			self.tauon.deco.load(self.colours.deco)
		else:
			self.tauon.deco.unload()
		if self.colours.lm:
			self.gui.info_icon.colour = ColourRGBA(60, 60, 60, 255)
			self.gui.folder_icon.colour = ColourRGBA(255, 190, 80, 255)
			self.gui.settings_icon.colour = ColourRGBA(85, 187, 250, 255)
			self.gui.radiorandom_icon.colour = ColourRGBA(120, 200, 120, 255)
		else:
			self.gui.info_icon.colour = ColourRGBA(61, 247, 163, 255)
			self.gui.folder_icon.colour = ColourRGBA(244, 220, 66, 255)
			self.gui.settings_icon.colour = ColourRGBA(232, 200, 96, 255)
			self.gui.radiorandom_icon.colour = ColourRGBA(153, 229, 133, 255)
		self.ddt.text_background_colour = self.colours.playlist_panel_background
		self.gui.update_layout = True

	def sync_theme_editor_controls_from_current_colour(self) -> None:
		current_colour = self.theme_editor_current_colour()
		hue, sat, val = colorsys.rgb_to_hsv(
			current_colour.r / 255,
			current_colour.g / 255,
			current_colour.b / 255,
		)
		self.theme_editor_hue_value = hue
		self.theme_editor_sat_value = sat
		self.theme_editor_val_value = val
		self.theme_editor_alpha_value = current_colour.a / 255

	def begin_theme_editor(self, title: str, target_path: Path | None, is_new: bool) -> None:
		self.enabled = True
		self.theme_editor_enabled = True
		self.tauon.fader.fall()
		self.theme_editor_list_scroll = 0.0
		self.theme_editor_dirty = False
		self.theme_editor_is_new = is_new
		self.theme_editor_target_path = target_path
		self.theme_editor_window_position = None
		self.theme_editor_original_colours = clone_theme_colours(self.colours)
		self.theme_editor_draft_colours = clone_theme_colours(self.colours)
		self.theme_editor_original_theme_name = self.gui.theme_name
		self.theme_editor_original_theme_number = self.prefs.theme
		self.theme_editor_title_box.set_text(title)
		self.theme_editor_title_box.cursor_position = 0
		self.theme_editor_title_box.selection = 0
		self.sync_theme_editor_controls_from_current_colour()
		self.apply_theme_preview_colours(self.theme_editor_draft_colours)

	def clear_theme_editor_state(self) -> None:
		self.theme_editor_enabled = False
		self.theme_editor_draft_colours = None
		self.theme_editor_original_colours = None
		self.theme_editor_target_path = None
		self.theme_editor_dirty = False
		self.theme_editor_drag_target = None
		self.theme_editor_window_position = None
		self.theme_editor_hue_value = 0.0
		self.theme_editor_sat_value = 1.0
		self.theme_editor_val_value = 1.0
		self.theme_editor_alpha_value = 1.0
		self.destroy_theme_editor_gradient_textures()

	def open_theme_editor(self) -> None:
		if not self.active_theme_is_user_editable():
			self.show_message(
				_("Bundled themes are read-only"),
				_("Create a new theme first to edit a copy of the active look."),
				mode="warning",
			)
			return
		self.begin_theme_editor(self.gui.theme_name, self.active_theme_path(), is_new=False)

	def close_theme_editor(self) -> None:
		self.clear_theme_editor_state()
		self.tauon.fader.rise()
		self.destroy_settings_texture()
		self.gui.update_layout = True

	def create_user_theme(self) -> None:
		base_name = filename_safe(f"{self.gui.theme_name} Copy" if self.gui.theme_name else _("Custom Theme")).strip()
		if not base_name:
			base_name = _("Custom Theme")
		target_name = self.unique_theme_name(base_name)
		target_path = self.dirs.user_directory / "theme" / f"{target_name}.ttheme"
		try:
			save_theme(clone_theme_colours(self.colours), target_path)
		except OSError:
			logging.exception("Failed saving duplicated theme file")
			self.show_message(_("Could not save theme file"), mode="error")
			return

		self.refresh_theme_presets()
		self.prefs.theme = get_theme_number(self.dirs, target_name)
		self.prefs.theme_name = target_name
		self.gui.theme_name = target_name
		self.gui.reload_theme = True
		self.gui.update_layout = True
		self.destroy_settings_texture()
		self.show_message(_("Duplicated theme"), target_name, mode="done")

	def delete_active_user_theme(self) -> None:
		path = self.active_theme_path()
		if path is None or not self.theme_path_is_user(path):
			self.show_message(_("Only user themes can be deleted"), mode="warning")
			return

		try:
			path.unlink()
		except OSError:
			logging.exception("Failed deleting theme file")
			self.show_message(_("Could not delete theme file"), mode="error")
			return

		self.refresh_theme_presets()
		self.theme_editor_enabled = False
		self.prefs.theme = 0
		self.prefs.theme_name = "Mindaro"
		self.gui.theme_name = "Mindaro"
		self.gui.reload_theme = True
		self.gui.update_layout = True
		self.show_message(_("Deleted theme"), path.stem, mode="done")

	def save_active_user_theme(self) -> bool:
		if self.theme_editor_draft_colours is None:
			return False
		target_name = filename_safe(self.theme_editor_title_box.text.strip())
		if not target_name:
			self.show_message(_("Theme title cannot be empty"), mode="error")
			return False

		target_dir = self.dirs.user_directory / "theme"
		target_path = target_dir / f"{target_name}.ttheme"
		original_path = self.theme_editor_target_path
		if original_path is not None and target_path != original_path and target_path.exists():
			self.show_message(_("A theme with that title already exists"), mode="error")
			return False
		if original_path is None and target_path.exists():
			self.show_message(_("A theme with that title already exists"), mode="error")
			return False

		try:
			save_theme(self.theme_editor_draft_colours, target_path)
			if original_path is not None and original_path != target_path and original_path.exists():
				original_path.unlink()
		except OSError:
			logging.exception("Failed saving theme file")
			self.show_message(_("Could not save theme file"), mode="error")
			return False

		self.theme_editor_target_path = target_path
		self.theme_editor_original_colours = clone_theme_colours(self.theme_editor_draft_colours)
		self.theme_editor_original_theme_name = target_name
		self.theme_editor_original_theme_number = get_theme_number(self.dirs, target_name)
		self.theme_editor_is_new = False
		self.theme_editor_dirty = False
		self.refresh_theme_presets()
		self.prefs.theme = get_theme_number(self.dirs, target_name)
		self.prefs.theme_name = target_name
		self.gui.theme_name = target_name
		self.apply_theme_preview_colours(self.theme_editor_draft_colours)
		self.gui.update_layout = True
		self.show_message(_("Saved theme"), target_name, mode="done")
		return True

	def apply_theme_editor_colour(self, thing: tuple[str], colour: ColourRGBA) -> None:
		if self.theme_editor_draft_colours is None:
			return
		for attr in thing:
			setattr(self.theme_editor_draft_colours, attr, ColourRGBA(colour.r, colour.g, colour.b, colour.a))
		self.theme_editor_dirty = True
		self.apply_theme_preview_colours(self.theme_editor_draft_colours)

	def theme_editor_current_hsv(self) -> tuple[float, float, float]:
		colour = self.theme_editor_current_colour()
		return colorsys.rgb_to_hsv(colour.r / 255, colour.g / 255, colour.b / 255)

	def apply_theme_editor_hsv(self, hue: float, sat: float, val: float) -> None:
		colour = self.theme_editor_current_colour()
		hue = min(max(hue, 0.0), 1.0)
		sat = min(max(sat, 0.0), 1.0)
		val = min(max(val, 0.0), 1.0)
		self.theme_editor_hue_value = hue
		self.theme_editor_sat_value = sat
		self.theme_editor_val_value = val
		r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
		self.apply_theme_editor_colour(
			self.theme_editor_selected_attrs,
			ColourRGBA(int(r * 255), int(g * 255), int(b * 255), colour.a),
		)

	def apply_theme_editor_alpha(self, alpha: float) -> None:
		colour = self.theme_editor_current_colour()
		alpha = min(max(alpha, 0.0), 1.0)
		self.theme_editor_alpha_value = alpha
		self.apply_theme_editor_colour(
			self.theme_editor_selected_attrs,
			ColourRGBA(colour.r, colour.g, colour.b, int(alpha * 255)),
		)

	def theme_editor_texture_from_pixels(self, width: int, height: int, pixel_bytes: bytes) -> sdl3.LP_SDL_Texture | None:
		buffer = ctypes.create_string_buffer(pixel_bytes)
		surface = sdl3.SDL_CreateSurfaceFrom(
			width,
			height,
			sdl3.SDL_PIXELFORMAT_ARGB8888,
			ctypes.cast(buffer, c_void_p),
			width * 4,
		)
		texture = sdl3.SDL_CreateTextureFromSurface(self.renderer, surface)
		sdl3.SDL_DestroySurface(surface)
		if texture is not None:
			sdl3.SDL_SetTextureBlendMode(texture, sdl3.SDL_BLENDMODE_BLEND)
			if hasattr(sdl3, "SDL_SetTextureScaleMode") and hasattr(sdl3, "SDL_SCALEMODE_LINEAR"):
				sdl3.SDL_SetTextureScaleMode(texture, sdl3.SDL_SCALEMODE_LINEAR)
		return texture

	def render_theme_editor_texture(self, texture, rect: tuple[int, int, int, int]) -> None:
		if texture is None:
			return
		dest_rect = sdl3.SDL_FRect(float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]))
		sdl3.SDL_RenderTexture(self.renderer, texture, None, dest_rect)

	def ensure_theme_editor_sv_texture(self, width: int, height: int, hue: float):
		downscale = 10
		hue_buckets = max(48, min(width // 2, 144))
		quantized_hue = round(hue * hue_buckets) / max(hue_buckets, 1)
		texture_key = (width, height, round(quantized_hue * hue_buckets))
		if self.theme_editor_sv_texture is not None and self.theme_editor_sv_texture_key == texture_key:
			return self.theme_editor_sv_texture

		if self.theme_editor_sv_texture is not None:
			sdl3.SDL_DestroyTexture(self.theme_editor_sv_texture)
			self.theme_editor_sv_texture = None

		source_width = max(1, width // downscale)
		source_height = max(1, height // downscale)
		pixels = bytearray(source_width * source_height * 4)
		for y_pos in range(source_height):
			value = 1 - (y_pos / max(source_height - 1, 1))
			for x_pos in range(source_width):
				saturation = x_pos / max(source_width - 1, 1)
				r, g, b = colorsys.hsv_to_rgb(quantized_hue, saturation, value)
				offset = (y_pos * source_width + x_pos) * 4
				pixels[offset] = int(b * 255)
				pixels[offset + 1] = int(g * 255)
				pixels[offset + 2] = int(r * 255)
				pixels[offset + 3] = 255

		self.theme_editor_sv_texture = self.theme_editor_texture_from_pixels(source_width, source_height, bytes(pixels))
		self.theme_editor_sv_texture_key = texture_key
		return self.theme_editor_sv_texture

	def ensure_theme_editor_hue_texture(self, width: int, height: int):
		downscale = 10
		texture_key = (width, height)
		if self.theme_editor_hue_texture is not None and self.theme_editor_hue_texture_key == texture_key:
			return self.theme_editor_hue_texture

		if self.theme_editor_hue_texture is not None:
			sdl3.SDL_DestroyTexture(self.theme_editor_hue_texture)
			self.theme_editor_hue_texture = None

		source_width = max(1, width // downscale)
		source_height = max(1, height // downscale)
		row_bytes = bytearray(source_width * 4)
		for x_pos in range(source_width):
			hue_value = x_pos / max(source_width - 1, 1)
			r, g, b = colorsys.hsv_to_rgb(hue_value, 1, 1)
			offset = x_pos * 4
			row_bytes[offset] = int(b * 255)
			row_bytes[offset + 1] = int(g * 255)
			row_bytes[offset + 2] = int(r * 255)
			row_bytes[offset + 3] = 255
		pixels = bytes(row_bytes) * source_height

		self.theme_editor_hue_texture = self.theme_editor_texture_from_pixels(source_width, source_height, pixels)
		self.theme_editor_hue_texture_key = texture_key
		return self.theme_editor_hue_texture

	def theme_editor_copy_colour(self) -> None:
		self.theme_editor_clipboard = self.theme_editor_current_colour()
		copy_to_clipboard(self.theme_colour_to_hex(self.theme_editor_clipboard))
		self.show_message(_("Copied colour"), self.theme_colour_to_hex(self.theme_editor_clipboard), mode="done")

	def theme_editor_paste_colour(self) -> None:
		colour = self.theme_editor_clipboard
		if colour is None:
			colour = self.parse_theme_colour_text(copy_from_clipboard())
		if colour is None:
			self.show_message(_("There is no colour in the clipboard"), mode="error")
			return
		self.apply_theme_editor_colour(self.theme_editor_selected_attrs, colour)
		self.theme_editor_clipboard = ColourRGBA(colour.r, colour.g, colour.b, colour.a)
		self.sync_theme_editor_controls_from_current_colour()
		self.show_message(_("Pasted colour"), self.theme_editor_selected_label(), mode="done")

	def sync_settings_content_scroll(self, scroll_area: tuple[int, int, int, int], content_height: int) -> float:
		scroll_source = "settings content"
		max_scroll = max(content_height - scroll_area[3], 0)
		wheel_delta = self.scroll if self.scroll else self.inp.mouse_wheel
		if max_scroll <= 0:
			self.settings_content_scroll = 0
			self.tauon.smooth_scroll.reset_motion(scroll_source)
			return 0

		touch_scroll = self.inp.touch_scroll_y != 0 and coll_point(self.inp.touch_position, scroll_area)
		use_smooth_scroll = (
			self.tauon.smooth_scroll.enabled()
			or touch_scroll
			or self.tauon.smooth_scroll.active(scroll_source)
		)
		scroll_step = round(56 * self.gui.scale)
		if use_smooth_scroll:
			if self.coll(scroll_area) and wheel_delta:
				self.tauon.smooth_scroll.add_wheel_motion(scroll_source, -wheel_delta, scroll_step)
			if self.inp.touch_released:
				self.tauon.smooth_scroll.release_touch(scroll_source)
			elif touch_scroll:
				self.tauon.smooth_scroll.apply_touch_drag(scroll_source, -self.inp.touch_scroll_y)
			self.settings_content_scroll += self.tauon.smooth_scroll.step_motion(scroll_source)
		elif self.coll(scroll_area) and wheel_delta:
			self.settings_content_scroll -= wheel_delta * scroll_step

		self.settings_content_scroll = min(max(self.settings_content_scroll, 0), max_scroll)
		return max_scroll

	def draw_settings_range_slider(
		self,
		rect: tuple[int, int, int, int],
		title: str,
		value: float,
		min_value: float,
		max_value: float,
		step: float,
		accent: ColourRGBA | None = None,
		formatter=None,
		callback=None,
		log_scale: bool = False,
		disabled: bool = False,
	) -> float:
		if accent is None:
			accent = self.settings_page_accent()
		if disabled:
			accent = alpha_blend(ColourRGBA(128, 128, 128, 90), self.colours.box_background)

		x, y, w, h = tuple(round(v) for v in rect)
		fill = alpha_blend(ColourRGBA(255, 255, 255, 6), self.colours.box_background)
		border = alpha_blend(ColourRGBA(255, 255, 255, 18), self.colours.box_text_border)
		if disabled:
			fill = alpha_blend(ColourRGBA(128, 128, 128, 8), self.colours.box_background)
			border = alpha_blend(ColourRGBA(128, 128, 128, 36), self.colours.box_text_border)
		elif self.coll((x, y, w, h)):
			fill = alpha_blend(ColourRGBA(255, 255, 255, 8), fill)
		self.ddt.bordered_rect((x, y, w, h), fill, border, round(1 * self.gui.scale))

		self.ddt.text(
			(x + round(12 * self.gui.scale), y + round(8 * self.gui.scale)),
			title,
			alpha_mod(self.colours.box_text_label, 150) if disabled else self.colours.box_text,
			12,
			bg=fill,
			max_w=w - round(110 * self.gui.scale),
		)

		if formatter is None:
			display = str(value)
		else:
			display = formatter(value)
		self.ddt.text(
			(x + w - round(12 * self.gui.scale), y + round(8 * self.gui.scale), 1),
			display,
			alpha_mod(self.colours.box_text_label, 130) if disabled else self.colours.box_sub_text,
			211,
			bg=fill,
		)

		slider_x = x + round(12 * self.gui.scale)
		slider_y = y + h - round(16 * self.gui.scale)
		slider_w = w - round(24 * self.gui.scale)
		slider_h = round(2 * self.gui.scale)
		slider_rect = (slider_x, slider_y, slider_w, slider_h)
		grip_w = round(8 * self.gui.scale)
		grip_h = round(14 * self.gui.scale)
		use_log_scale = log_scale and min_value > 0 and max_value > min_value
		if use_log_scale:
			log_min = math.log(min_value)
			log_max = math.log(max_value)
			safe_value = min(max(value, min_value), max_value)
			ratio = 0.0 if log_max == log_min else (math.log(safe_value) - log_min) / (log_max - log_min)
		else:
			ratio = 0.0 if max_value == min_value else (value - min_value) / (max_value - min_value)
		ratio = min(max(ratio, 0.0), 1.0)
		grip_x = slider_x + round(slider_w * ratio) - grip_w // 2
		grip_rect = (grip_x, slider_y - (grip_h // 2) + slider_h // 2, grip_w, grip_h)

		self.ddt.rect(slider_rect, alpha_blend(ColourRGBA(255, 255, 255, 20), border))
		self.ddt.rect((slider_x, slider_y, round(slider_w * ratio), slider_h), accent)
		self.ddt.rect(grip_rect, accent)

		if disabled:
			return value

		hit_rect = grow_rect((slider_x, slider_y - round(10 * self.gui.scale), slider_w, round(20 * self.gui.scale)), round(4 * self.gui.scale))
		self.fields.add(hit_rect)
		if self.coll(hit_rect) and self.inp.mouse_down:
			portion = (self.inp.mouse_position[0] - slider_x) / max(slider_w, 1)
			portion = min(max(portion, 0.0), 1.0)
			if use_log_scale:
				raw_value = math.exp(log_min + (log_max - log_min) * portion)
			else:
				raw_value = min_value + (max_value - min_value) * portion
			if step:
				raw_value = round(round(raw_value / step) * step, 3)
			value = min(max(raw_value, min_value), max_value)
			self.gui.update_layout = True
			if callback is not None:
				callback(value)

		return value

	def draw_settings_section(
		self,
		rect: tuple[int, int, int, int],
		title: str,
		subtitle: str = "",
		accent: ColourRGBA | None = None,
	) -> tuple[int, int, int, int]:
		if accent is None:
			accent = self.settings_page_accent()

		x, y, w, h = rect
		fill = alpha_blend(ColourRGBA(255, 255, 255, 6), self.colours.box_background)
		border = alpha_blend(ColourRGBA(255, 255, 255, 18), self.colours.box_text_border)
		# Border drawn INSIDE the rect: the settings document texture is
		# blitted at exactly the view rect, so bordered_rect's outside border
		# would be cropped on cards at the document's left edge
		border_size = round(1 * self.gui.scale)
		self.ddt.rect(rect, border)
		self.ddt.rect((x + border_size, y + border_size, w - border_size * 2, h - border_size * 2), fill)
		# Accent bar only on the first card of the category
		if self.settings_accent_bar_pending:
			self.ddt.rect((x, y, round(4 * self.gui.scale), h), accent)
			self.settings_accent_bar_pending = False
		self.ddt.text_background_colour = fill

		pad_x = round(16 * self.gui.scale)
		inner_x = x + pad_x + round(4 * self.gui.scale)
		inner_y = y + round(14 * self.gui.scale)
		inner_w = w - pad_x * 2 - round(4 * self.gui.scale)

		if title:
			self.ddt.text((inner_x, inner_y), title, self.colours.box_text, 213, bg=fill)
			inner_y += round(20 * self.gui.scale)
		if subtitle:
			sub_h = self.ddt.text(
				(inner_x, inner_y, 4, inner_w, round(40 * self.gui.scale)),
				subtitle,
				self.colours.box_text_label,
				11,
				bg=fill,
			) or 0
			inner_y += max(sub_h, round(14 * self.gui.scale))

		if title or subtitle:
			divider = alpha_blend(alpha_mod(accent, 80), self.colours.box_text_border)
			inner_y += round(6 * self.gui.scale)
			self.ddt.rect((inner_x, inner_y, inner_w, round(1 * self.gui.scale)), divider)
			inner_y += round(12 * self.gui.scale)

		return inner_x, inner_y, inner_w, y + h - round(14 * self.gui.scale) - inner_y

	def settings_switch_row(
		self,
		rect: tuple[int, int, int, int],
		function: Callable[[int], bool | None] | bool,
		title: str,
		subtitle: str = "",
		accent: ColourRGBA | None = None,
		click: bool = False,
		show_active_bar: bool = False,
		disabled: bool = False,
		disabled_click: bool = False,
	) -> bool:
		if accent is None:
			accent = self.settings_page_accent()

		x, y, w, h = tuple(round(v) for v in rect)
		active = function if type(function) is bool else function(1)
		hover = self.coll((x, y, w, h))

		fill = alpha_blend(ColourRGBA(255, 255, 255, 6), self.colours.box_background)
		if disabled:
			fill = alpha_blend(ColourRGBA(128, 128, 128, 8), self.colours.box_background)
		elif active:
			fill = alpha_blend(alpha_mod(accent, 26), fill)
		if hover and not disabled:
			fill = alpha_blend(ColourRGBA(255, 255, 255, 10), fill)

		border = alpha_blend(ColourRGBA(255, 255, 255, 18), self.colours.box_text_border)
		if disabled:
			border = alpha_blend(ColourRGBA(128, 128, 128, 36), self.colours.box_text_border)
		elif active:
			border = alpha_blend(alpha_mod(accent, 90), border)

		self.ddt.bordered_rect((x, y, w, h), fill, border, round(1 * self.gui.scale))
		if active and show_active_bar and not disabled:
			self.ddt.rect((x, y, round(4 * self.gui.scale), h), accent)

		self.fields.add((x, y, w, h))
		if (self.click or click) and hover:
			self.inp.global_clicked = True
			if disabled and not disabled_click:
				pass
			elif type(function) is bool:
				active ^= True
			else:
				function()
				active = function(1)

		text_x = x + round(14 * self.gui.scale)
		title_font = 13
		title_max_w = w - round(84 * self.gui.scale)
		title_y = y + round(6 * self.gui.scale) if subtitle else y + round(7 * self.gui.scale)
		title_colour = alpha_mod(self.colours.box_text_label, 150) if disabled else self.colours.box_text
		subtitle_colour = alpha_mod(self.colours.box_text_label, 130) if disabled else self.colours.box_text_label
		self.ddt.text((text_x, title_y), title, title_colour, title_font, bg=fill, max_w=title_max_w)
		if subtitle:
			self.ddt.text(
				(text_x, y + round(21 * self.gui.scale)),
				subtitle,
				subtitle_colour,
				11,
				bg=fill,
				max_w=title_max_w,
			)

		switch_w = round(42 * self.gui.scale)
		switch_h = round(18 * self.gui.scale)
		switch_x = x + w - switch_w - round(12 * self.gui.scale)
		switch_y = y + (h - switch_h) // 2
		switch_fill = (
			alpha_blend(ColourRGBA(128, 128, 128, 24), fill)
			if disabled else
			alpha_blend(alpha_mod(accent, 54), fill)
			if active else
			alpha_blend(ColourRGBA(255, 255, 255, 16), fill)
		)
		switch_border = (
			border
			if disabled else
			alpha_blend(alpha_mod(accent, 120), border)
			if active else
			border
		)
		self.ddt.bordered_rect((switch_x, switch_y, switch_w, switch_h), switch_fill, switch_border, round(1 * self.gui.scale))

		knob_w = round(16 * self.gui.scale)
		knob_h = switch_h - round(6 * self.gui.scale)
		knob_x = switch_x + (switch_w - knob_w - round(3 * self.gui.scale) if active else round(3 * self.gui.scale))
		knob_y = switch_y + round(3 * self.gui.scale)
		knob_colour = alpha_mod(self.colours.box_text_label, 120) if disabled else self.colours.box_title_text if active else self.colours.box_text_label
		self.ddt.rect((knob_x, knob_y, knob_w, knob_h), knob_colour)

		return active

	def settings_toggle_chip(
		self,
		rect: tuple[int, int, int, int],
		function: Callable[[int], bool | None] | bool,
		title: str,
		subtitle: str = "",
		accent: ColourRGBA | None = None,
		show_active_bar: bool = True,
	) -> bool:
		if accent is None:
			accent = self.settings_page_accent()

		x, y, w, h = tuple(round(v) for v in rect)
		active = function if type(function) is bool else function(1)
		hover = self.coll((x, y, w, h))

		fill = alpha_blend(ColourRGBA(255, 255, 255, 6), self.colours.box_background)
		if active:
			fill = alpha_blend(alpha_mod(accent, 22), fill)
		if hover:
			fill = alpha_blend(ColourRGBA(255, 255, 255, 10), fill)

		border = alpha_blend(ColourRGBA(255, 255, 255, 18), self.colours.box_text_border)
		if active:
			border = alpha_blend(alpha_mod(accent, 90), border)

		self.ddt.bordered_rect((x, y, w, h), fill, border, round(1 * self.gui.scale))
		if active and show_active_bar:
			self.ddt.rect((x, y, w, round(3 * self.gui.scale)), accent)

		self.fields.add((x, y, w, h))
		if hover and self.click:
			self.inp.global_clicked = True
			if type(function) is bool:
				active ^= True
			else:
				function()
				active = function(1)

		indicator_w = round(12 * self.gui.scale)
		indicator_h = round(12 * self.gui.scale)
		indicator_y = y + round(10 * self.gui.scale) if subtitle else y + max(0, (h - indicator_h) // 2)
		indicator_rect = (
			x + w - indicator_w - round(10 * self.gui.scale),
			indicator_y,
			indicator_w,
			indicator_h,
		)
		self.ddt.bordered_rect(
			indicator_rect,
			alpha_blend(ColourRGBA(255, 255, 255, 8), fill),
			alpha_blend(ColourRGBA(255, 255, 255, 18), border),
			round(1 * self.gui.scale),
		)
		if active:
			self.ddt.rect(
				(
					indicator_rect[0] + round(3 * self.gui.scale),
					indicator_rect[1] + round(3 * self.gui.scale),
					indicator_rect[2] - round(6 * self.gui.scale),
					indicator_rect[3] - round(6 * self.gui.scale),
				),
				accent,
			)

		title_max_w = w - round(32 * self.gui.scale)
		title_font = 12
		title_y = y + round(11 * self.gui.scale)
		if not subtitle:
			title_y -= round(2 * self.gui.scale)
		self.ddt.text(
			(x + round(12 * self.gui.scale), title_y),
			title,
			self.colours.box_text,
			title_font,
			bg=fill,
			max_w=title_max_w,
		)
		if subtitle:
			self.ddt.text(
				(x + round(12 * self.gui.scale), y + round(25 * self.gui.scale), 4, title_max_w, h - round(28 * self.gui.scale)),
				subtitle,
				self.colours.box_text_label,
				10,
				bg=fill,
			)

		return active

	def settings_action_tile(
		self,
		rect: tuple[int, int, int, int],
		title: str,
		plug: Callable[[], None] | None = None,
		accent: ColourRGBA | None = None,
		emphasis: bool = False,
		show_arrow: bool = True,
	) -> bool:
		if accent is None:
			accent = self.settings_page_accent()

		x, y, w, h = tuple(round(v) for v in rect)
		button_h = round(34 * self.gui.scale)
		button_y = y + max(0, (h - button_h) // 2)
		button_rect = (x, button_y, w, button_h)
		hover = self.coll(button_rect)
		fill = alpha_blend(ColourRGBA(255, 255, 255, 8), self.colours.box_button_background)
		if emphasis:
			fill = alpha_blend(ColourRGBA(255, 255, 255, 4), fill)
		if hover:
			fill = alpha_blend(ColourRGBA(255, 255, 255, 10), fill)
		border = alpha_blend(ColourRGBA(255, 255, 255, 18), self.colours.box_text_border)
		if emphasis:
			border = alpha_blend(ColourRGBA(255, 255, 255, 10), border)

		self.ddt.bordered_rect(button_rect, fill, border, round(1 * self.gui.scale))

		self.fields.add(button_rect)
		hit = False
		if hover and self.click:
			self.inp.global_clicked = True
			hit = True
			if plug is not None:
				plug()

		text_colour = self.colours.box_text if hover or emphasis else self.colours.box_button_text
		text_font = 212
		text_max_w = w - (round(44 * self.gui.scale) if show_arrow else round(28 * self.gui.scale))
		# text_metrics = self.ddt.get_text_wh(title, text_font, text_max_w)
		text_y = button_y + round(8 * self.gui.scale)
		self.ddt.text((x + round(14 * self.gui.scale), text_y), title, text_colour, text_font, bg=fill, max_w=text_max_w)

		if show_arrow:
			arrow_y = button_y + button_h // 2
			arrow_colour = self.colours.box_text if hover else self.colours.box_text_label
			self.ddt.rect((x + w - round(20 * self.gui.scale), arrow_y - round(3 * self.gui.scale), round(7 * self.gui.scale), round(2 * self.gui.scale)), arrow_colour)
			self.ddt.rect((x + w - round(16 * self.gui.scale), arrow_y - round(1 * self.gui.scale), round(7 * self.gui.scale), round(2 * self.gui.scale)), arrow_colour)

		return hit

	def settings_icon_button(
		self,
		rect: tuple[int, int, int, int],
		plug: Callable[[], None] | None = None,
		accent: ColourRGBA | None = None,
		emphasis: bool = False,
		icon: MenuIcon | None = None,
		draw_icon: Callable[[tuple[int, int, int, int], ColourRGBA], None] | None = None,
		tooltip: str = "",
	) -> bool:
		if accent is None:
			accent = self.settings_page_accent()

		x, y, w, h = tuple(round(v) for v in rect)
		button_size = min(w, h, round(30 * self.gui.scale))
		button_x = x + max(0, (w - button_size) // 2)
		button_y = y + max(0, (h - button_size) // 2)
		button_rect = (button_x, button_y, button_size, button_size)
		hover = self.coll(button_rect)
		if hover and tooltip:
			self.tauon.tool_tip.test(button_rect[0] + 15 * self.gui.scale, button_rect[1] - 28 * self.gui.scale, tooltip)
		self.fields.add(button_rect)
		hit = False
		if hover and self.click:
			self.inp.global_clicked = True
			hit = True
			if plug is not None:
				plug()

		icon_colour = self.colours.box_text if hover or emphasis else self.colours.box_text_label
		if draw_icon is not None:
			draw_icon(button_rect, icon_colour)
		elif icon is not None:
			icon_x = button_rect[0] + (button_rect[2] - round(16 * self.gui.scale)) // 2 + round(icon.xoff * self.gui.scale)
			icon_y = button_rect[1] + (button_rect[3] - round(16 * self.gui.scale)) // 2 + round(icon.yoff * self.gui.scale)
			if icon.base_asset is None:
				icon.asset.render(icon_x, icon_y, icon_colour)
			else:
				icon.asset.render(icon_x, icon_y)

		return hit

	def draw_duplicate_theme_icon(self, rect: tuple[int, int, int, int], colour: ColourRGBA) -> None:
		size = round(10 * self.gui.scale)
		shift = round(3 * self.gui.scale)
		x = rect[0] + (rect[2] - size - shift) // 2
		y = rect[1] + (rect[3] - size - shift) // 2
		back_rect = (x, y, size, size)
		front_rect = (x + shift, y + shift, size, size)
		self.ddt.rect_s(back_rect, colour, round(1 * self.gui.scale))
		self.ddt.rect_s(front_rect, colour, round(1 * self.gui.scale))

	def settings_stepper_row(
		self,
		rect: tuple[int, int, int, int],
		title: str,
		value: int,
		lower_limit: int,
		upper_limit: int,
		units: str = "",
		step: int = 1,
		accent: ColourRGBA | None = None,
		callback=None,
		formatter=None,
	) -> int:
		if accent is None:
			accent = self.settings_page_accent()

		x, y, w, h = tuple(round(v) for v in rect)
		fill = alpha_blend(ColourRGBA(255, 255, 255, 6), self.colours.box_background)
		border = alpha_blend(ColourRGBA(255, 255, 255, 18), self.colours.box_text_border)
		if self.coll((x, y, w, h)):
			fill = alpha_blend(ColourRGBA(255, 255, 255, 8), fill)
		self.ddt.bordered_rect((x, y, w, h), fill, border, round(1 * self.gui.scale))

		self.ddt.text(
			(x + round(12 * self.gui.scale), y + round(8 * self.gui.scale)),
			title,
			self.colours.box_text,
			12,
			bg=fill,
			max_w=w - round(130 * self.gui.scale),
		)

		button_w = round(22 * self.gui.scale)
		value_w = round(54 * self.gui.scale)
		control_gap = round(4 * self.gui.scale)
		control_h = round(20 * self.gui.scale)
		control_x = x + w - (button_w * 2 + value_w + control_gap * 2) - round(10 * self.gui.scale)
		control_y = y + (h - control_h) // 2
		dec_rect = (control_x, control_y, button_w, control_h)
		value_rect = (control_x + button_w + control_gap, control_y, value_w, control_h)
		inc_rect = (value_rect[0] + value_rect[2] + control_gap, control_y, button_w, control_h)

		def draw_button(button_rect: tuple[int, int, int, int], label: str) -> bool:
			hovered = self.coll(button_rect)
			button_fill = alpha_blend(ColourRGBA(255, 255, 255, 8), fill)
			if hovered:
				button_fill = alpha_blend(alpha_mod(accent, 18), button_fill)
			self.ddt.bordered_rect(button_rect, button_fill, border, round(1 * self.gui.scale))
			self.fields.add(button_rect)
			self.ddt.text(
				(button_rect[0] + button_rect[2] // 2, button_rect[1] + round(2 * self.gui.scale), 2),
				label,
				accent if hovered else self.colours.box_text_label,
				211,
				bg=button_fill,
			)
			return hovered and self.click

		changed = False
		if draw_button(dec_rect, "−") and value > lower_limit:
			value -= step
			changed = True

		value_fill = alpha_blend(ColourRGBA(255, 255, 255, 4), fill)
		self.ddt.bordered_rect(value_rect, value_fill, border, round(1 * self.gui.scale))
		if formatter is not None:
			display_text = formatter(value)
		else:
			display_text = f"{value}{units}"
		self.ddt.text(
			(value_rect[0] + value_rect[2] // 2, value_rect[1] + round(2 * self.gui.scale), 2),
			display_text,
			self.colours.box_sub_text,
			211,
			bg=value_fill,
		)

		if draw_button(inc_rect, "+") and value < upper_limit:
			value += step
			changed = True

		if changed:
			self.gui.update_layout = True
			if callback is not None:
				callback(value)

		return value

	def settings_choice_tile(
		self,
		rect: tuple[int, int, int, int],
		title: str,
		subtitle: str,
		active: bool,
		callback: Callable[[], None] | None = None,
		accent: ColourRGBA | None = None,
		show_active_bar: bool = False,
	) -> bool:
		if accent is None:
			accent = self.settings_page_accent()

		x, y, w, h = tuple(round(v) for v in rect)
		hover = self.coll((x, y, w, h))
		fill = alpha_blend(ColourRGBA(255, 255, 255, 6), self.colours.box_background)
		if active:
			fill = alpha_blend(alpha_mod(accent, 24), fill)
		if hover:
			fill = alpha_blend(ColourRGBA(255, 255, 255, 10), fill)
		border = alpha_blend(ColourRGBA(255, 255, 255, 18), self.colours.box_text_border)
		if active:
			border = alpha_blend(alpha_mod(accent, 90), border)

		self.ddt.bordered_rect((x, y, w, h), fill, border, round(1 * self.gui.scale))
		if active and show_active_bar:
			self.ddt.rect((x, y, round(4 * self.gui.scale), h), accent)

		self.fields.add((x, y, w, h))
		hit = False
		if hover and self.click:
			self.inp.global_clicked = True
			hit = True
			if callback is not None:
				callback()

		indicator_h = round(12 * self.gui.scale)
		indicator_y = y + round(12 * self.gui.scale) if subtitle else y + max(0, (h - indicator_h) // 2)
		indicator_rect = (x + round(14 * self.gui.scale), indicator_y, round(12 * self.gui.scale), indicator_h)
		self.ddt.bordered_rect(
			indicator_rect,
			alpha_blend(ColourRGBA(255, 255, 255, 8), fill),
			alpha_blend(ColourRGBA(255, 255, 255, 18), border),
			round(1 * self.gui.scale),
		)
		if active:
			self.ddt.rect(
				(
					indicator_rect[0] + round(3 * self.gui.scale),
					indicator_rect[1] + round(3 * self.gui.scale),
					indicator_rect[2] - round(6 * self.gui.scale),
					indicator_rect[3] - round(6 * self.gui.scale),
				),
				accent,
			)

		text_x = x + round(34 * self.gui.scale)
		title_font = 13
		title_max_w = w - round(46 * self.gui.scale)
		title_y = y + round(9 * self.gui.scale)
		self.ddt.text((text_x, title_y), title, self.colours.box_text, title_font, bg=fill, max_w=title_max_w)
		if subtitle:
			self.ddt.text(
				(text_x, y + round(27 * self.gui.scale), 4, title_max_w, round(34 * self.gui.scale)),
				subtitle,
				self.colours.box_text_label,
				11,
				bg=fill,
			)

		return hit

	def settings_segmented_bar(
		self,
		pos: tuple[int, int],
		options: Sequence[tuple[str, bool, Callable[[], None]]],
		accent: ColourRGBA | None = None,
		width: int | None = None,
		click: bool | None = None,
	) -> int:
		"""Compact radio switcher: a single bordered bar of short-label buttons,
		the active one filled with the accent colour. Segment widths follow the
		labels; pass ``width`` to stretch the bar to a fixed total width (the
		slack is shared between segments). Returns the bar height."""
		if accent is None:
			accent = self.settings_page_accent()
		if click is None:
			click = self.click
		gui = self.gui
		x, y = round(pos[0]), round(pos[1])
		h = round(32 * gui.scale)
		pad = round(16 * gui.scale)
		font = 212
		widths = [self.ddt.get_text_w(label, font) + pad * 2 for label, _active, _callback in options]
		if width is not None:
			extra = round(width) - sum(widths)
			if extra > 0:
				share = extra // len(widths)
				widths = [seg_w + share for seg_w in widths]
				widths[-1] += extra - share * len(widths)
		fill = alpha_blend(ColourRGBA(255, 255, 255, 6), self.colours.box_background)
		border = alpha_blend(ColourRGBA(255, 255, 255, 18), self.colours.box_text_border)
		self.ddt.bordered_rect((x, y, sum(widths), h), fill, border, round(1 * gui.scale))

		seg_x = x
		prev_active = False
		for (label, active, callback), seg_w in zip(options, widths):
			rect = (seg_x, y, seg_w, h)
			hover = self.coll(rect)
			self.fields.add(rect)
			bg = fill
			if active:
				bg = accent
				self.ddt.rect(rect, bg)
			elif hover:
				bg = alpha_blend(ColourRGBA(255, 255, 255, 10), fill)
				self.ddt.rect(rect, bg)
			# Separators between plain segments only; the accent block provides
			# its own edges
			if seg_x != x and not active and not prev_active:
				self.ddt.rect((seg_x, y, round(1 * gui.scale), h), border)
			text_colour = ColourRGBA(20, 20, 25, 255) if active else self.colours.box_text
			self.ddt.text((seg_x + seg_w // 2, y + round(7 * gui.scale), 2), label, text_colour, font, bg=bg)
			if hover and click and not active:
				self.inp.global_clicked = True
				callback()
			prev_active = active
			seg_x += seg_w

		return h

	def settings_switcher_tile(
		self,
		rect: tuple[int, int, int, int],
		title: str,
		active: bool,
		callback: Callable[[], None] | None = None,
		accent: ColourRGBA | None = None,
	) -> bool:
		if accent is None:
			accent = self.settings_page_accent()

		x, y, w, h = tuple(round(v) for v in rect)
		hover = self.coll((x, y, w, h))
		fill = alpha_blend(ColourRGBA(255, 255, 255, 5), self.colours.box_background)
		if active:
			fill = alpha_blend(alpha_mod(accent, 24), fill)
		if hover:
			fill = alpha_blend(ColourRGBA(255, 255, 255, 9), fill)

		border = alpha_blend(ColourRGBA(255, 255, 255, 18), self.colours.box_text_border)
		if active:
			border = alpha_blend(alpha_mod(accent, 90), border)

		self.ddt.bordered_rect((x, y, w, h), fill, border, round(1 * self.gui.scale))

		self.fields.add((x, y, w, h))
		hit = False
		if hover and self.click:
			self.inp.global_clicked = True
			hit = True
			if callback is not None:
				callback()

		text_colour = self.colours.box_text if active or hover else self.colours.box_button_text
		self.ddt.text(
			(x + round(12 * self.gui.scale), y + round(8 * self.gui.scale)),
			title,
			text_colour,
			13,
			bg=fill,
			max_w=w - round(40 * self.gui.scale),
		)

		arrow_colour = accent if active else (self.colours.box_text if hover else self.colours.box_text_label)
		arrow_x = x + w - round(20 * self.gui.scale)
		arrow_y = y + h // 2
		self.ddt.rect(
			(arrow_x - round(4 * self.gui.scale), arrow_y - round(3 * self.gui.scale), round(7 * self.gui.scale), round(2 * self.gui.scale)),
			arrow_colour,
		)
		self.ddt.rect(
			(arrow_x, arrow_y - round(1 * self.gui.scale), round(7 * self.gui.scale), round(2 * self.gui.scale)),
			arrow_colour,
		)

		return hit

	def draw_settings_note(
		self,
		rect: tuple[int, int, int, int],
		text: str,
		accent: ColourRGBA | None = None,
		title: str = "",
	) -> None:
		x, y, w, h = rect
		fill = alpha_blend(ColourRGBA(255, 255, 255, 6), self.colours.box_background)
		border = alpha_blend(ColourRGBA(255, 255, 255, 18), self.colours.box_text_border)
		self.ddt.bordered_rect(rect, fill, border, round(1 * self.gui.scale))

		text_x = x + round(14 * self.gui.scale)
		text_y = y + round(7 * self.gui.scale)
		if title:
			self.ddt.text((text_x, text_y), title, self.colours.box_text, 212, bg=fill)
			text_y += round(17 * self.gui.scale)

		self.ddt.text(
			(text_x, text_y, 4, w - round(24 * self.gui.scale), h - round(14 * self.gui.scale)),
			text,
			self.colours.box_text_label,
			11,
			bg=fill,
		)

	def select_account_view(self, view: int) -> None:
		self.account_view = view
		self.settings_text_focus = None
		self.gui.update_layout = True

	def begin_settings_text_inputs(self) -> None:
		self.settings_text_seen = []
		self.settings_text_hit = False
		if self.inp.key_tab_press and self.settings_text_order:
			step = -1 if self.inp.key_shift_down or self.inp.key_shiftr_down else 1
			if self.settings_text_focus not in self.settings_text_order:
				self.settings_text_focus = self.settings_text_order[-1] if step < 0 else self.settings_text_order[0]
			else:
				index = self.settings_text_order.index(self.settings_text_focus)
				self.settings_text_focus = self.settings_text_order[(index + step) % len(self.settings_text_order)]

	def finish_settings_text_inputs(self) -> None:
		self.settings_text_order = self.settings_text_seen[:]
		if self.settings_text_focus not in self.settings_text_order:
			self.settings_text_focus = None
		elif (self.click or self.inp.level_2_right_click) and not self.settings_text_hit:
			self.settings_text_focus = None

	def settings_text_field_state(
		self,
		field_rect: tuple[int, int, int, int],
		text_box: TextBox2,
		accent: ColourRGBA,
		editable: bool = True,
	) -> tuple[bool, ColourRGBA, ColourRGBA]:
		if text_box not in self.settings_text_seen:
			self.settings_text_seen.append(text_box)

		hover = self.coll(field_rect)
		active = editable and self.settings_text_focus is text_box
		fill = alpha_blend(ColourRGBA(255, 255, 255, 6), self.colours.box_background)
		if hover or active:
			fill = alpha_blend(ColourRGBA(255, 255, 255, 8), fill)
		border = alpha_blend(ColourRGBA(255, 255, 255, 18), self.colours.box_text_border)
		active_border = alpha_blend(alpha_mod(accent, 90), border)
		if active:
			border = active_border

		self.fields.add(field_rect)
		if hover and ((self.click and editable) or self.inp.level_2_right_click):
			self.inp.global_clicked = True
			self.settings_text_focus = text_box
			self.settings_text_hit = True
			active = editable
			if editable:
				border = active_border
		elif hover and editable:
			self.settings_text_hit = self.settings_text_hit or self.inp.mouse_down

		return active, fill, border

	def draw_settings_text_field(
		self,
		rect: tuple[int, int, int, int],
		text_box: TextBox2,
		accent: ColourRGBA,
		stored_value: str | None = None,
		text_colour: ColourRGBA | None = None,
		secret: bool = False,
		placeholder: str = "",
		editable: bool = True,
		border_override: ColourRGBA | None = None,
	) -> str:
		x, y, w, h = tuple(round(v) for v in rect)
		if stored_value is not None and self.settings_text_focus is not text_box and text_box.text != stored_value:
			text_box.text = stored_value

		active, fill, border = self.settings_text_field_state((x, y, w, h), text_box, accent, editable=editable)
		if border_override is not None and not active:
			border = border_override
		self.ddt.bordered_rect((x, y, w, h), fill, border, round(1 * self.gui.scale))

		if placeholder and not text_box.text and not active:
			self.ddt.text(
				(x + round(5 * self.gui.scale), y + round(3 * self.gui.scale)),
				placeholder,
				self.colours.box_text_label,
				12,
				bg=fill,
			)

		text_box.draw(
			x + round(4 * self.gui.scale),
			y + round(3 * self.gui.scale),
			text_colour or self.colours.box_input_text,
			active,
			secret=secret,
			width=w - round(8 * self.gui.scale),
			click=self.click,
		)
		return text_box.text

	def draw_settings_action_row(
		self,
		rect: tuple[int, int, int, int],
		items: list[tuple[str, Callable[[], None] | None, bool]],
		accent: ColourRGBA | None = None,
	) -> None:
		if accent is None:
			accent = self.settings_page_accent()
		if not items:
			return

		x, y, w, h = tuple(round(v) for v in rect)
		gap = round(8 * self.gui.scale)
		count = len(items)
		tile_w = (w - gap * (count - 1)) // max(count, 1)
		tile_x = x
		for index, (title, callback, emphasis) in enumerate(items):
			current_w = tile_w if index < count - 1 else x + w - tile_x
			self.settings_action_tile((tile_x, y, current_w, h), title, callback, accent, emphasis=emphasis)
			tile_x += current_w + gap

	def settings_text_input(
		self,
		rect: tuple[int, int, int, int],
		title: str,
		text_box: TextBox2,
		stored_value: str,
		accent: ColourRGBA | None = None,
		secret: bool = False,
		placeholder: str = "",
	) -> str:
		if accent is None:
			accent = self.settings_page_accent()

		x, y, w, h = tuple(round(v) for v in rect)
		label_y = y
		field_y = y + round(16 * self.gui.scale)
		field_h = max(round(22 * self.gui.scale), h - round(18 * self.gui.scale))
		self.ddt.text((x, label_y), title, self.colours.box_text_label, 11, bg=self.ddt.text_background_colour)
		return self.draw_settings_text_field(
			(x, field_y, w, field_h),
			text_box,
			accent,
			stored_value=stored_value,
			secret=secret,
			placeholder=placeholder,
		)

	def toggle_lyrics_view(self) -> None:
		self.lyrics_panel ^= True

	def draw_lyrics_source_settings(self, rect: tuple[int, int, int, int], accent: ColourRGBA | None = None) -> None:
		if accent is None:
			accent = self.settings_page_accent()

		x, y, w, h = rect
		content_x, content_y, content_w, content_h = self.draw_settings_section(
			rect,
			_("Lyrics lookup"),
			_("Choose when and where Tauon searches for lyrics."),
			accent,
		)

		row_h = round(40 * self.gui.scale)
		row_gap = round(6 * self.gui.scale)
		self.prefs.auto_lyrics = self.settings_switch_row(
			(content_x, content_y, content_w, row_h),
			self.prefs.auto_lyrics,
			_("Auto-search lyrics"),
			_("Auto-search when lyrics enabled"),
			accent,
		)
		content_y += row_h + row_gap

		source_names = [name for name in lyric_sources if name != "Genius"]
		if "Genius" in lyric_sources:
			source_names.append("Genius")
		for name in source_names:
			enabled = name in self.prefs.lyrics_enables
			subtitle = _("Scraping source") if name in uses_scraping else _("API source")
			new = self.settings_switch_row(
				(content_x, content_y, content_w, row_h),
				enabled,
				name,
				subtitle,
				accent,
			)
			if new != enabled:
				if enabled:
					if name in self.prefs.lyrics_enables:
						self.prefs.lyrics_enables.remove(name)
				else:
					self.prefs.lyrics_enables.append(name)
			content_y += row_h + row_gap

	def funcs(self, x0: int, y0: int, w0: int, h0: int, accent_override: ColourRGBA | None = None) -> None:
		tauon   = self.tauon
		prefs   = self.prefs
		gui     = self.gui
		ddt     = self.ddt
		colours = self.colours
		accent  = accent_override if accent_override is not None else self.settings_page_accent()

		ddt.text_background_colour = colours.box_background

		if self.func_page != 4 and not Path(prefs.playlist_folder_path).is_dir():
			# reset options if user leaves a bad path in the box
			prefs.playlist_folder_path = ""
			prefs.autoscan_playlist_folder = False

		column_gap = round(12 * gui.scale)
		card_y = y0
		card_h = h0
		left_w = max(round(270 * gui.scale), min(round(w0 * 0.56), w0 - round(220 * gui.scale)))
		if self.func_page == 1:
			left_w = (w0 - column_gap) // 2
		right_w = w0 - left_w - column_gap
		left_rect = (x0, card_y, left_w, card_h)
		right_rect = (x0 + left_w + column_gap, card_y, right_w, card_h)
		row_gap = round(6 * gui.scale)
		row_h = round(42 * gui.scale)
		small_row_h = round(30 * gui.scale)

		if self.func_page == 0:
			x, y, w, section_h = self.draw_settings_section(
				left_rect,
				_("Common settings"),
				_("Common library and panel settings."),
				accent,
			)

			# ("Show artist info panel" switch removed — the panel is toggled
			# with its keyboard shortcut (Ctrl+O) / the View Switcher instead.)
			self.settings_switch_row(
				(x, y, w, row_h),
				tauon.toggle_auto_artist_dl,
				_("Auto fetch artist data"),
				_("Fetch artist data while the panel is open."),
				accent,
			)

			y += row_h + row_gap
			prefs.always_auto_update_playlists = self.settings_switch_row(
				(x, y, w, row_h),
				prefs.always_auto_update_playlists,
				_("Auto reload playlists"),
				_("Rescan playlists when you return to them."),
				accent,
			)

			# ("Tabs in top panel" switch moved to the top-panel right-click
			# window menu)

			y += row_h + row_gap + round(4 * gui.scale)
			ddt.text((x, y), _("End of playlist action"), colours.box_text_label, 11)
			y += round(20 * gui.scale)
			self.settings_segmented_bar(
				(x, y),
				(
					(_("Stop"), self.set_playlist_stop(1), self.set_playlist_stop),
					(_("Repeat"), self.set_playlist_repeat(1), self.set_playlist_repeat),
					(_("Next playlist"), self.set_playlist_advance(1), self.set_playlist_advance),
					(_("Cycle all"), self.set_playlist_cycle(1), self.set_playlist_cycle),
				),
				accent,
				width=w,
			)

			x, y, w, section_h = self.draw_settings_section(
				right_rect,
				_("Quick access"),
				_("Open the files and folders Tauon uses."),
				accent,
			)
			tile_h = round(36 * gui.scale)
			self.settings_action_tile((x, y, w, tile_h), _("Open config file"), tauon.open_config_file, accent, emphasis=gui.opened_config_file)
			y += tile_h + row_gap
			if gui.opened_config_file:
				self.settings_action_tile((x, y, w, tile_h), _("Reload edited config"), tauon.reload_config_file, accent, emphasis=True)
				y += tile_h + row_gap
			self.settings_action_tile((x, y, w, tile_h), _("Open data folder"), tauon.open_data_directory, accent)
			y += tile_h + row_gap
			self.settings_action_tile((x, y, w, tile_h), _("Open keymap file"), tauon.open_keymap_file, accent)

		elif self.func_page == 1:
			# ("End of playlist action" lives in Common settings now)
			x, y, w, section_h = self.draw_settings_section(
				left_rect,
				_("Session rules"),
				_("Playback behavior for restarts, sleep, wake and radio."),
				accent,
			)
			play_lock_old = prefs.block_suspend
			prefs.block_suspend = self.settings_switch_row(
				(x, y, w, row_h),
				prefs.block_suspend,
				_("Block suspend"),
				_("Keep the system awake during playback."),
				accent,
			)
			y += row_h + row_gap
			prefs.reload_play_state = self.settings_switch_row(
				(x, y, w, row_h),
				prefs.reload_play_state,
				_("Resume on restart"),
				_("Resume playback when Tauon starts."),
				accent,
			)
			y += row_h + row_gap
			prefs.resume_play_wake = self.settings_switch_row(
				(x, y, w, row_h),
				prefs.resume_play_wake,
				_("Resume from suspend"),
				_("Resume playback after waking."),
				accent,
			)

			y += row_h + row_gap
			auto_rec_old = prefs.auto_rec
			prefs.auto_rec = self.settings_switch_row(
				(x, y, w, row_h),
				prefs.auto_rec,
				_("Record radio"),
				_("Record internet radio and split tracks."),
				accent,
			)
			if prefs.auto_rec != auto_rec_old and prefs.auto_rec:
				self.show_message(
					_("Tracks will now be recorded. Restart any playback for change to take effect."),
					_("Tracks will be saved to \"Saved Radio Tracks\" playlist."),
					mode="info")

			if tauon.update_play_lock is None:
				prefs.block_suspend = False
			elif play_lock_old != prefs.block_suspend:
				tauon.update_play_lock()

			bottom = left_rect[1] + left_rect[3] - round(14 * gui.scale)
			remaining_h = bottom - y - row_h
			if prefs.auto_rec and remaining_h > round(50 * gui.scale):
				self.draw_settings_note(
					(x, y + row_h + row_gap, w, remaining_h - row_gap),
					_("Recorded tracks are added to \"Saved Radio Tracks\"."),
					accent,
					_("Radio capture"),
				)

			# (The "Track menu extras" search-provider switches moved to the
			# track menu's Layout submenu.)
			x, y, w, section_h = self.draw_settings_section(
				right_rect,
				_("Archive imports"),
				_("How Tauon handles archives and Downloads."),
				accent,
			)
			self.settings_switch_row(
				(x, y, w, row_h),
				tauon.toggle_extract,
				_("Extract archives"),
				_("Extract supported archives on drag and drop."),
				accent,
			)
			y += row_h + row_gap
			extract_archives_enabled = tauon.toggle_extract(1)
			self.settings_switch_row(
				(x, y, w, row_h),
				tauon.toggle_dl_mon,
				_("Enable download monitor"),
				_("Watch Downloads for one-click imports."),
				accent,
				disabled=not extract_archives_enabled,
			)
			y += row_h + row_gap
			self.settings_switch_row(
				(x, y, w, small_row_h),
				tauon.toggle_ex_del,
				_("Trash archive after extraction"),
				accent=accent,
				disabled=not extract_archives_enabled,
			)
			y += small_row_h + row_gap
			self.settings_switch_row(
				(x, y, w, small_row_h),
				tauon.toggle_music_ex,
				_("Always extract to Music folder"),
				accent=accent,
				disabled=not extract_archives_enabled,
			)

			bottom = right_rect[1] + right_rect[3] - round(14 * gui.scale)
			remaining_h = bottom - y - small_row_h
			if remaining_h > round(50 * gui.scale):
				self.draw_settings_note(
					(x, y + small_row_h + row_gap, w, remaining_h - row_gap),
					_("Useful if you often import from archives or Downloads."),
					accent,
					_("Import flow"),
				)

		elif self.func_page == 3:
			x, y, w, section_h = self.draw_settings_section(
				left_rect,
				_("Remote, presence and sharing"),
				_("Network and sharing features."),
				accent,
			)
			remote_old = prefs.enable_remote
			prefs.enable_remote = self.settings_switch_row(
				(x, y, w, row_h),
				prefs.enable_remote,
				_("Enable remote control"),
				_("Change requires restart."),
				accent,
			)
			y += row_h + row_gap

			if prefs.enable_remote and prefs.enable_remote != remote_old:
				self.show_message(
					_("Notice: This API is not security hardened."),
					_("Only enable in a trusted LAN and do not expose port (7814) to the internet"),
					mode="warning")

			listen_along_enabled = self.settings_switch_row(
				(x, y, w, row_h),
				tauon.toggle_enable_web,
				_("Enable Listen Along"),
				_("Start the web server for remote playback."),
				accent,
			)
			y += row_h + row_gap
			link = f"http://localhost:{prefs.metadata_page_port!s}/listenalong"

			def open_listenalong() -> None:
				webbrowser.open(link, new=2, autoraise=True)

			if listen_along_enabled:
				self.settings_action_tile((x, y, w, round(36 * gui.scale)), _("Open Listen Along page"), open_listenalong, accent, emphasis=True)
				y += round(36 * gui.scale) + row_gap

			discord_old = prefs.discord_enable
			discord_state = gui.discord_status if prefs.discord_enable else _("Disabled")
			discord_subtitle = _("Discord status: {state}").format(state=discord_state)
			prefs.discord_enable = self.settings_switch_row(
				(x, y, w, row_h),
				prefs.discord_enable,
				_("Enable Discord Rich Presence"),
				discord_subtitle,
				accent,
			)

			# if self.flatpak_mode and self.button(x + 215 * gui.scale, y, _("?")):
			# 	self.show_message(
			# 		_("For troubleshooting Discord RP"),
			# 		"https://github.com/Taiko2k/TauonMusicBox/wiki/Discord-RP", mode="link")

			if prefs.discord_enable and not discord_old:
				if self.snap_mode:
					self.show_message(_("Sorry, this feature is unavailable with snap"), mode="error")
					prefs.discord_enable = False
				elif not self.prefs.discord_allow:
					self.show_message(_("Missing dependency python-pypresence"))
					prefs.discord_enable = False
				else:
					try:
						tauon._signal_discord()
					except Exception:
						tauon.hit_discord()

			if discord_old and not prefs.discord_enable and prefs.discord_active:
				prefs.disconnect_discord = True

			self.draw_lyrics_source_settings(right_rect, accent)

		elif self.func_page == 4:
			x, y, w, section_h = self.draw_settings_section(
				left_rect,
				_("Exports and input"),
				_("Playlist export and input settings."),
				accent,
			)
			prefs.use_gamepad = self.settings_switch_row(
				(x, y, w, row_h),
				prefs.use_gamepad,
				_("Enable gamepad input"),
				_("Change requires restart."),
				accent,
			)
			y += row_h + round(12 * gui.scale)

			ddt.text((x, y), _("Default playlist export folder"), colours.box_text_label, 11)
			y += round(18 * gui.scale)
			rect1 = (x, y, w, round(22 * gui.scale))
			field_path = tauon.playlist_folder_box.text
			if self.prefs.playlist_folder_path:
				tauon.playlist_folder_box.text = self.prefs.playlist_folder_path
				field_path = tauon.playlist_folder_box.text
			path_invalid = bool(field_path) and not Path(field_path).is_dir()
			field_border = colours.status_text_over if path_invalid else alpha_blend(ColourRGBA(255, 255, 255, 18), colours.box_text_border)
			field_colour = colours.status_text_over if path_invalid else colours.box_input_text
			self.prefs.playlist_folder_path = self.draw_settings_text_field(
				rect1,
				tauon.playlist_folder_box,
				accent,
				stored_value=self.prefs.playlist_folder_path,
				text_colour=field_colour,
				border_override=field_border,
			)
			y += round(31 * gui.scale)

			helper_text = (
				_("Folder must exist before auto-import can use it.")
				if path_invalid else
				_("Leave blank to export beside the playlist, or set a folder here.")
			)
			helper_colour = colours.status_text_over if path_invalid else colours.box_text_label
			ddt.text((x + round(2 * gui.scale), y), helper_text, helper_colour, 11, max_w=w)
			y += round(18 * gui.scale)

			prefs.autoscan_playlist_folder = self.settings_switch_row(
				(x, y, w, row_h),
				prefs.autoscan_playlist_folder,
				_("Auto-import playlists from this folder"),
				_("Runs during \"Rescan All Folders\" only."),
				accent,
			)

			x, y, w, section_h = self.draw_settings_section(
				right_rect,
				_("Editing and diagnostics"),
				_("Lyrics writeback and debug settings."),
				accent,
			)
			prefs.save_synced_to_lrc = self.settings_switch_row(
				(x, y, w, small_row_h),
				prefs.save_synced_to_lrc,
				_("Save Synced to .lrc"),
				accent=accent,
			)

			y += small_row_h + row_gap
			prefs.save_lyrics_changes_to_files = self.settings_switch_row(
				(x, y, w, small_row_h),
				prefs.save_lyrics_changes_to_files,
				_("Save lyrics edits to tags"),
				accent=accent,
			)

			y += small_row_h + row_gap
			debug_path = self.user_directory / "debug"
			debug_state = debug_path.exists()
			old = debug_state
			debug_state = self.settings_switch_row(
				(x, y, w, small_row_h),
				debug_state,
				_("Enable debug mode"),
				accent=accent,
			)
			if old is False and debug_state is True:
				with debug_path.open("a"):
					pass
			elif old is True and debug_state is False:
				os.remove(debug_path)
			y += small_row_h + row_gap

			console_show = self.settings_switch_row(
				(x, y, w, small_row_h),
				tauon.console.show,
				_("Toggle Console"),
				accent=accent,
			)
			if console_show != tauon.console.show:
				tauon.console.show = console_show
				tauon.console.fps_only = False
				if console_show:
					tauon.console.fps.reset()

	def button(self, x: int, y: int, text: str, plug: Callable[[], None] | None = None, width: int = 0, bg: ColourRGBA | None = None) -> bool:
		"""PSA for anyone making a new button function: use fields.add(rect) to make the gui
		refresh when you pan the mouse over it
		"""
		w = width
		if w == 0:
			w = self.ddt.get_text_w(text, 211) + round(10 * self.gui.scale)

		h = round(20 * self.gui.scale)
		border_size = round(2 * self.gui.scale)

		rect = (round(x), round(y), round(w), round(h))
		rect2 = (rect[0] - border_size, rect[1] - border_size, rect[2] + border_size * 2, rect[3] + border_size * 2)

		if bg is None:
			bg = self.colours.box_background

		real_bg = bg
		hit = False

		self.ddt.rect(rect2, self.colours.box_check_border)
		self.ddt.rect(rect, bg)

		self.fields.add(rect)
		if self.coll(rect):
			self.ddt.rect(rect, ColourRGBA(255, 255, 255, 15))
			real_bg = alpha_blend(ColourRGBA(255, 255, 255, 15), bg)
			self.ddt.text((x + int(w / 2), rect[1] + 1 * self.gui.scale, 2), text, self.colours.box_title_text, 211, bg=real_bg)
			if self.click:
				hit = True
				if plug is not None:
					plug()
		else:
			self.ddt.text((x + int(w / 2), rect[1] + 1 * self.gui.scale, 2), text, self.colours.box_sub_text, 211, bg=real_bg)

		return hit

	def button2(self, x: int, y: int, text: str, width: int = 0, center_text: bool = False, force_on: bool = False) -> bool:
		"""PSA for anyone making a new button function: use fields.add(rect) to make the gui
		refresh when you pan the mouse over it
		"""
		w = width
		if w == 0:
			w = self.ddt.get_text_w(text, 211) + 10 * self.gui.scale
		rect = (x, y, w, 20 * self.gui.scale)

		border_colour = alpha_blend(ColourRGBA(255, 255, 255, 18), self.colours.box_text_border)
		bg_colour = alpha_blend(ColourRGBA(255, 255, 255, 8), self.colours.box_button_background)
		real_bg = bg_colour

		self.ddt.bordered_rect(rect, bg_colour, border_colour, round(1 * self.gui.scale))
		self.fields.add(rect)
		hit = False

		text_position = (x + int(7 * self.gui.scale), rect[1] + 1 * self.gui.scale)
		if center_text:
			text_position = (x + rect[2] // 2, rect[1] + 1 * self.gui.scale, 2)

		if self.coll(rect) or force_on:
			bg_colour = alpha_blend(self.colours.box_button_background_highlight, bg_colour)
			real_bg = bg_colour
			self.ddt.bordered_rect(rect, bg_colour, border_colour, round(1 * self.gui.scale))
			self.ddt.text(text_position, text, self.colours.box_button_text_highlight, 211, bg=real_bg)
			if self.click and not force_on:
				hit = True
		else:
			self.ddt.text(text_position, text, self.colours.box_button_text, 211, bg=real_bg)
		return hit

	def toggle_square(self, x: int, y: int, function: Callable[[int], bool | None] | bool, text: str , click: bool = False, subtitle: str = "") -> bool:
		gui     = self.gui
		colours = self.colours
		x = round(x)
		y = round(y)

		border = round(2 * gui.scale)
		gap = round(2 * gui.scale)
		inner_square = round(6 * gui.scale)

		full_w = border * 2 + gap * 2 + inner_square

		if subtitle:
			le = self.ddt.text((x + 20 * gui.scale, y - 1 * gui.scale), text, colours.box_text, 13)
			se = self.ddt.text((x + 20 * gui.scale, y + 14 * gui.scale), subtitle, colours.box_text_label, 13)
			hit_rect = (x - 10 * gui.scale, y - 3 * gui.scale, max(le, se) + 30 * gui.scale, 34 * gui.scale)
			y += round(8 * gui.scale)
		else:
			le = self.ddt.text((x + 20 * gui.scale, y - 1 * gui.scale), text, colours.box_text, 13)
			hit_rect = (x - 10 * gui.scale, y - 3 * gui.scale, le + 30 * gui.scale, 22 * gui.scale)

		# Border outline
		self.ddt.rect_a((x, y), (full_w, full_w), colours.box_check_border)
		# Inner background
		self.ddt.rect_a(
			(x + border, y + border), (gap * 2 + inner_square, gap * 2 + inner_square),
			alpha_blend(ColourRGBA(255, 255, 255, 14), colours.box_background))

		# Check if box clicked
		self.inp.global_clicked = False
		if (self.click or click) and self.coll(hit_rect):
			self.inp.global_clicked = True

		# There are two mode, function type, and passthrough bool type
		active = False
		active = function if type(function) is bool else function(1)

		if self.inp.global_clicked:
			if type(function) is bool:
				active ^= True
			else:
				function()
				active = function(1)

		# Draw inner check mark if enabled
		if active:
			self.ddt.rect_a((x + border + gap, y + border + gap), (inner_square, inner_square), colours.toggle_box_on)

		return active

	def clear_local_loves(self) -> None:
		if not self.inp.key_shift_down:
			self.show_message(
				_("This will mark all tracks in local database as unloved!"),
				_("Press button again while holding shift key if you're sure you want to do that."),
				mode="warning")
			return

		for key, star in self.star_store.db.items():
			star.loved = False
			self.star_store.db[key] = star

		self.gui.request_tracklist_redraw()
		self.show_message(_("Cleared all loves"), mode="done")

	def get_scrobble_counts(self) -> None:
		if not self.inp.key_shift_down:
			t = self.lastfm.get_all_scrobbles_estimate_time()
			if not t:
				self.show_message(_("Error, not connected to last.fm"))
				return
			self.show_message(
				_("Warning: This process will take approximately {T} minutes to complete.").format(T=(t // 60)),
				_("Press again while holding Shift if you understand"), mode="warning")
			return

		if not self.lastfm.scanning_friends and not self.lastfm.scanning_scrobbles and not self.lastfm.scanning_loves:
			shoot_dl = threading.Thread(target=self.lastfm.get_all_scrobbles)
			shoot_dl.daemon = True
			shoot_dl.start()
		else:
			self.show_message(_("A process is already running. Wait for it to finish."))

	def clear_scrobble_counts(self) -> None:
		for track in self.pctl.master_library.values():
			track.lfm_scrobbles = 0

		self.show_message(_("Cleared all scrobble counts"), mode="done")

	def get_friend_love(self) -> None:
		if not self.inp.key_shift_down:
			self.show_message(
				_("Warning: This process can take a long time to complete! (up to an hour or more)"),
				_("This feature is not recommended for accounts that have many friends."),
				_("Press again while holding Shift if you understand"), mode="warning")
			return

		if not self.lastfm.scanning_friends and not self.lastfm.scanning_scrobbles and not self.lastfm.scanning_loves:
			logging.info("Launch friend love thread")
			shoot_dl = threading.Thread(target=self.lastfm.get_friends_love)
			shoot_dl.daemon = True
			shoot_dl.start()
		else:
			self.show_message(_("A process is already running. Wait for it to finish."))

	def get_user_love(self) -> None:
		if not self.lastfm.scanning_friends and not self.lastfm.scanning_scrobbles and not self.lastfm.scanning_loves:
			shoot_dl = threading.Thread(target=self.lastfm.dl_love)
			shoot_dl.daemon = True
			shoot_dl.start()
		else:
			self.show_message(_("A process is already running. Wait for it to finish."))

	def previous_theme(self) -> None:
		self.prefs.theme -= 1
		self.gui.reload_theme = True
		if self.prefs.theme < 0:
			self.prefs.theme = len(get_themes(self.dirs))

	def toggle_x_scale(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.x_scale
		self.prefs.x_scale ^= True
		auto_scale(self.bag)
		self.gui.update_layout = True
		return None

	def topchart(
		self,
		x0: int,
		y0: int,
		w0: int,
		h0: int,
		show_return: bool = True,
		accent: ColourRGBA | None = None,
	) -> None:
		gui = self.gui
		prefs = self.prefs
		colours = self.colours

		if accent is None:
			accent = self.settings_tab_accent(max(len(self.tabs) - 2, 0))

		self.ddt.text_background_colour = colours.box_background

		def set_chart_mode(cascade: bool) -> None:
			prefs.chart_cascade = cascade
			self.gui.update_layout = True

		def randomise_bg() -> None:
			r = round(random.random() * 40)
			g = round(random.random() * 40)
			b = round(random.random() * 40)
			prefs.chart_bg = [r, g, b]
			if random.randrange(0, 4) == 1:
				c = 5 + round(random.random() * 20)
				prefs.chart_bg = [c, c, c]

		def start_generate() -> None:
			if self.gui.generating_chart:
				self.show_message(_("Be patient!"))
			elif not prefs.chart_font:
				self.show_message(_("No font set in config"), mode="error")
			else:
				shoot = threading.Thread(target=self.tauon.gen_chart)
				shoot.daemon = True
				shoot.start()
				self.gui.generating_chart = True

		inner_x, inner_y, inner_w, section_h = self.draw_settings_section(
			(x0, y0, w0, h0),
			_("Grid generator"),
			_("Build an album grid from the current playlist."),
			accent,
		)

		row_gap = round(8 * gui.scale)
		column_gap = round(10 * gui.scale)
		tile_h = round(46 * gui.scale)
		row_h = round(30 * gui.scale)
		action_h = round(36 * gui.scale)
		info_h = round(44 * gui.scale)

		dex = self.tauon.reload_albums(quiet=True, return_playlist=self.pctl.active_playlist_viewing)
		count = prefs.chart_rows * prefs.chart_columns
		if prefs.chart_cascade:
			count = prefs.chart_c1 * prefs.chart_d1 + prefs.chart_c2 * prefs.chart_d2 + prefs.chart_c3 * prefs.chart_d3

		info_fill = alpha_blend(ColourRGBA(255, 255, 255, 6), colours.box_background)
		info_border = alpha_blend(ColourRGBA(255, 255, 255, 18), colours.box_text_border)
		info_rect = (inner_x, inner_y, inner_w, info_h)
		self.ddt.bordered_rect(info_rect, info_fill, info_border, round(1 * gui.scale))
		text_x = info_rect[0] + round(14 * gui.scale)
		text_y = info_rect[1] + round(5 * gui.scale)
		self.ddt.text((text_x, text_y), _("Target playlist"), colours.box_text_label, 11, bg=info_fill)
		self.ddt.text(
			(text_x, text_y + round(17 * gui.scale)),
			self.pctl.multi_playlist[self.pctl.active_playlist_viewing].title,
			colours.box_text,
			13,
			bg=info_fill,
			max_w=info_rect[2] - round(120 * gui.scale),
		)
		self.ddt.text(
			(info_rect[0] + info_rect[2] - round(14 * gui.scale), text_y + round(17 * gui.scale), 1),
			_("{N} albums").format(N=str(len(dex))),
			colours.box_sub_text,
			12,
			bg=info_fill,
		)
		inner_y += info_h + row_gap

		left_w = max(round(250 * gui.scale), min(round(inner_w * 0.52), inner_w - round(200 * gui.scale)))
		right_w = inner_w - left_w - column_gap
		left_x = inner_x
		right_x = inner_x + left_w + column_gap
		mode_w = (left_w - column_gap) // 2
		right_y = inner_y

		self.settings_choice_tile(
			(left_x, inner_y, mode_w, tile_h),
			_("Grid"),
			_("Rows and columns"),
			not prefs.chart_cascade,
			callback=lambda: set_chart_mode(False),
			accent=accent,
			show_active_bar=False,
		)
		self.settings_choice_tile(
			(left_x + mode_w + column_gap, inner_y, mode_w, tile_h),
			_("Cascade"),
			_("Stacked groups"),
			prefs.chart_cascade,
			callback=lambda: set_chart_mode(True),
			accent=accent,
			show_active_bar=False,
		)
		inner_y += tile_h + row_gap

		if prefs.chart_cascade:
			step_w = (left_w - column_gap) // 2
			for level_name, count_key, by_key in (
				(_("Level 1"), "chart_c1", "chart_d1"),
				(_("Level 2"), "chart_c2", "chart_d2"),
				(_("Level 3"), "chart_c3", "chart_d3"),
			):
				count_value = int(getattr(prefs, count_key))
				count_value = int(self.settings_stepper_row((left_x, inner_y, step_w, row_h), level_name, count_value, 2, 20, accent=accent))
				setattr(prefs, count_key, count_value)

				by_value = int(getattr(prefs, by_key))
				by_value = int(self.settings_stepper_row((left_x + step_w + column_gap, inner_y, step_w, row_h), _("By"), by_value, 0, 10, accent=accent))
				setattr(prefs, by_key, by_value)
				inner_y += row_h + row_gap
		else:
			prefs.chart_rows = int(self.settings_stepper_row((left_x, inner_y, left_w, row_h), _("Rows"), int(prefs.chart_rows), 1, 100, accent=accent))
			inner_y += row_h + row_gap
			prefs.chart_columns = int(self.settings_stepper_row((left_x, inner_y, left_w, row_h), _("Columns"), int(prefs.chart_columns), 1, 100, accent=accent))
			inner_y += row_h + row_gap

		swatch_w = max(round(108 * gui.scale), right_w - round(126 * gui.scale))
		random_w = right_w - swatch_w - column_gap
		swatch_rect = (right_x, right_y, swatch_w, tile_h)
		self.ddt.bordered_rect(swatch_rect, info_fill, info_border, round(1 * gui.scale))
		self.ddt.text((swatch_rect[0] + round(12 * gui.scale), swatch_rect[1] + round(8 * gui.scale)), _("Background"), colours.box_text_label, 11, bg=info_fill)
		display_colour = ColourRGBA(prefs.chart_bg[0], prefs.chart_bg[1], prefs.chart_bg[2], 255)
		preview_rect = (swatch_rect[0] + round(12 * gui.scale), swatch_rect[1] + round(25 * gui.scale), round(34 * gui.scale), round(12 * gui.scale))
		self.ddt.rect(preview_rect, display_colour)
		self.ddt.rect_s(preview_rect, alpha_blend(ColourRGBA(255, 255, 255, 40), colours.box_text_border), round(1 * gui.scale))
		self.ddt.text(
			(preview_rect[0] + preview_rect[2] + round(10 * gui.scale), swatch_rect[1] + round(22 * gui.scale)),
			f"{prefs.chart_bg[0]}, {prefs.chart_bg[1]}, {prefs.chart_bg[2]}",
			colours.box_sub_text,
			11,
			bg=info_fill,
			max_w=swatch_rect[2] - preview_rect[2] - round(34 * gui.scale),
		)
		self.settings_action_tile((right_x + swatch_w + column_gap, right_y, random_w, tile_h), _("Randomize"), randomise_bg, accent)
		right_y += tile_h + row_gap

		use_padding = not prefs.chart_tile
		new_padding = self.settings_switch_row((right_x, right_y, right_w, row_h), use_padding, _("Use padding"), accent=accent)
		if new_padding != use_padding:
			prefs.chart_tile = not new_padding
		right_y += row_h + row_gap

		prefs.chart_text = self.settings_switch_row((right_x, right_y, right_w, row_h), prefs.chart_text, _("Include album titles"), accent=accent)
		right_y += row_h + row_gap
		prefs.topchart_sorts_played = self.settings_switch_row((right_x, right_y, right_w, row_h), prefs.topchart_sorts_played, _("Sort by top played"), accent=accent)

		bottom_y = max(inner_y, right_y + row_h) + row_gap
		generate_w = round(136 * gui.scale)
		return_w = round(98 * gui.scale) if show_return else 0
		status_x = inner_x
		if show_return:
			if self.settings_action_tile((inner_x, bottom_y, return_w, action_h), _("Return"), None, accent):
				self.chart_view = 0
			status_x += return_w + column_gap

		self.settings_action_tile((status_x, bottom_y, generate_w, action_h), _("Generate"), start_generate, accent, emphasis=True)
		status_x += generate_w + column_gap
		status_w = inner_x + inner_w - status_x

		if status_w > round(120 * gui.scale):
			status_rect = (status_x, bottom_y, status_w, action_h)
			self.ddt.bordered_rect(status_rect, info_fill, info_border, round(1 * gui.scale))
			line_y = status_rect[1] + round(4 * gui.scale)
			if self.gui.generating_chart:
				self.ddt.text((status_rect[0] + round(12 * gui.scale), line_y), _("Generating..."), colours.box_text, 12, bg=info_fill)
				self.ddt.text((status_rect[0] + round(12 * gui.scale), line_y + round(14 * gui.scale)), _("Please wait."), colours.box_text_label, 11, bg=info_fill)
			else:
				self.ddt.text(
					(status_rect[0] + round(12 * gui.scale), line_y),
					_("{N} Album chart").format(N=str(count)),
					colours.box_text,
					12,
					bg=info_fill,
				)
				if len(dex) < count:
					self.ddt.text(
						(status_rect[0] + round(12 * gui.scale), line_y + round(14 * gui.scale)),
						_("Not enough albums in the playlist!"),
						ColourRGBA(255, 120, 125, 255),
						11,
						bg=info_fill,
					)
				else:
					self.ddt.text(
						(status_rect[0] + round(12 * gui.scale), line_y + round(14 * gui.scale)),
						_("Ready"),
						colours.box_text_label,
						11,
						bg=info_fill,
					)

	def set_playlist_cycle(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.end_setting == "cycle"
		self.prefs.end_setting = "cycle"
		# pl_follow = False
		return None

	def set_playlist_advance(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.end_setting == "advance"
		self.prefs.end_setting = "advance"
		# pl_follow = False
		return None

	def set_playlist_stop(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.end_setting == "stop"
		self.prefs.end_setting = "stop"
		return None

	def set_playlist_repeat(self, mode: int = 0) -> bool | None:
		if mode == 1:
			return self.prefs.end_setting == "repeat"
		self.prefs.end_setting = "repeat"
		return None

	def small_preset(self) -> None:
		self.prefs.playlist_row_height = round(22 * self.prefs.ui_scale)
		self.prefs.playlist_font_size = 15
		self.prefs.tracklist_y_text_offset = 0
		self.gui.update_layout = True

	def large_preset(self) -> None:
		self.prefs.playlist_row_height = round(27 * self.prefs.ui_scale)
		self.prefs.playlist_font_size = 15
		self.gui.update_layout = True

	def render_settings_func_category(
		self,
		page: int,
		x: int,
		y: int,
		w: int,
		draw: bool = True,
		accent_override: ColourRGBA | None = None,
	) -> int:
		heights = (
			round(245 * self.gui.scale),
			round(275 * self.gui.scale),
			round(262 * self.gui.scale),
			round(300 * self.gui.scale),
			round(350 * self.gui.scale),
		)
		height = heights[page]
		if draw:
			old_page = self.func_page
			self.func_page = page
			self.funcs(x, y, w, height, accent_override=accent_override)
			self.func_page = old_page
		return height

	def render_settings_general_category(self, x: int, y: int, w: int, draw: bool = True) -> int:
		# (func page 2 is empty now — Archive imports moved beside Session
		# rules on page 1)
		block_gap = round(12 * self.gui.scale)
		general_accent = self.settings_page_accent(0)
		general_h = self.render_settings_func_category(0, x, y, w, draw, accent_override=general_accent)
		behaviour_y = y + general_h + block_gap
		behaviour_h = self.render_settings_func_category(1, x, behaviour_y, w, draw, accent_override=general_accent)
		return general_h + behaviour_h + block_gap

	def render_settings_connections_category(self, x: int, y: int, w: int, accent: ColourRGBA, draw: bool = True) -> int:
		gui = self.gui
		tauon = self.tauon
		prefs = self.prefs
		ddt = self.ddt
		colours = self.colours

		column_gap = round(12 * gui.scale)
		block_gap = round(12 * gui.scale)
		row_gap = round(6 * gui.scale)
		row_h = round(42 * gui.scale)
		compact_row_h = round(30 * gui.scale)
		choice_h = round(42 * gui.scale)
		label_gap = round(16 * gui.scale)
		tile_gap = round(8 * gui.scale)
		left_w = max(round(270 * gui.scale), min(round(w * 0.5), w - round(220 * gui.scale)))
		right_w = w - left_w - column_gap
		top_row_h = round(286 * gui.scale)
		discord_h = round(252 * gui.scale) if prefs.discord_enable else 0
		total_h = top_row_h + (block_gap + discord_h if discord_h else 0)
		if not draw:
			return total_h

		left_rect = (x, y, left_w, top_row_h)
		right_rect = (x + left_w + column_gap, y, right_w, top_row_h)

		inner_x, inner_y, inner_w, section_h = self.draw_settings_section(
			left_rect,
			_("Remote, presence and sharing"),
			_("Network and sharing features."),
			accent,
		)
		remote_old = prefs.enable_remote
		prefs.enable_remote = self.settings_switch_row(
			(inner_x, inner_y, inner_w, row_h),
			prefs.enable_remote,
			_("Enable remote control"),
			_("Change requires restart."),
			accent,
		)
		inner_y += row_h + row_gap

		if prefs.enable_remote and prefs.enable_remote != remote_old:
			self.show_message(
				_("Notice: This API is not security hardened."),
				_("Only enable in a trusted LAN and do not expose port (7814) to the internet"),
				mode="warning",
			)

		listen_along_enabled = self.settings_switch_row(
			(inner_x, inner_y, inner_w, row_h),
			tauon.toggle_enable_web,
			_("Enable Listen Along"),
			_("Start the web server for remote playback."),
			accent,
		)
		inner_y += row_h + row_gap
		link = f"http://localhost:{prefs.metadata_page_port!s}/listenalong"

		def open_listenalong() -> None:
			webbrowser.open(link, new=2, autoraise=True)

		if listen_along_enabled:
			self.settings_action_tile(
				(inner_x, inner_y, inner_w, round(36 * gui.scale)),
				_("Open Listen Along page"),
				open_listenalong,
				accent,
				emphasis=True,
			)
			inner_y += round(36 * gui.scale) + row_gap

		discord_old = prefs.discord_enable
		discord_state = gui.discord_status if prefs.discord_enable else _("Disabled")
		discord_subtitle = _("Discord status: {state}").format(state=discord_state)
		prefs.discord_enable = self.settings_switch_row(
			(inner_x, inner_y, inner_w, row_h),
			prefs.discord_enable,
			_("Enable Discord Rich Presence"),
			discord_subtitle,
			accent,
		)

		if prefs.discord_enable and not discord_old:
			if self.snap_mode:
				self.show_message(_("Sorry, this feature is unavailable with snap"), mode="error")
				prefs.discord_enable = False
			elif not self.prefs.discord_allow:
				self.show_message(_("Missing dependency python-pypresence"))
				prefs.discord_enable = False
			else:
				try:
					tauon._signal_discord()
				except Exception:
					tauon.hit_discord()

		if discord_old and not prefs.discord_enable and prefs.discord_active:
			prefs.disconnect_discord = True

		self.draw_lyrics_source_settings(right_rect, accent)

		if not prefs.discord_enable:
			return total_h

		discord_accent = ColourRGBA(88, 145, 255, 255)
		discord_rect = (x, y + top_row_h + block_gap, w, discord_h)
		inner_x, inner_y, inner_w, section_h = self.draw_settings_section(
			discord_rect,
			_("Discord"),
			_("Layout, buttons and idle behavior."),
			discord_accent,
		)

		left_col_w = (inner_w - column_gap) // 2
		right_col_x = inner_x + left_col_w + column_gap
		right_col_w = inner_w - left_col_w - column_gap
		choice_w = (left_col_w - tile_gap) // 2

		def set_discord_card_layout(layout: str) -> None:
			prefs.discord_card_layout = layout

		def set_member_list_display(display: str) -> None:
			prefs.discord_member_list_display = display

		ddt.text((inner_x, inner_y), _("Card order"), colours.box_text_label, 11)
		choice_y = inner_y + label_gap
		self.settings_choice_tile(
			(inner_x, choice_y, choice_w, choice_h),
			_("Song first"),
			"",
			prefs.discord_card_layout == "title_artist",
			lambda: set_discord_card_layout("title_artist"),
			discord_accent,
		)
		self.settings_choice_tile(
			(inner_x + choice_w + tile_gap, choice_y, choice_w, choice_h),
			_("Artist first"),
			"",
			prefs.discord_card_layout == "artist_title",
			lambda: set_discord_card_layout("artist_title"),
			discord_accent,
		)

		member_y = choice_y + choice_h + round(12 * gui.scale)
		ddt.text((inner_x, member_y), _("Member list shows:"), colours.box_text_label, 11)
		member_choice_y = member_y + label_gap
		self.settings_choice_tile(
			(inner_x, member_choice_y, choice_w, choice_h),
			_("Song"),
			"",
			prefs.discord_member_list_display == "song",
			lambda: set_member_list_display("song"),
			discord_accent,
		)
		self.settings_choice_tile(
			(inner_x + choice_w + tile_gap, member_choice_y, choice_w, choice_h),
			_("Artist"),
			"",
			prefs.discord_member_list_display == "artist",
			lambda: set_member_list_display("artist"),
			discord_accent,
		)

		ddt.text((right_col_x, inner_y), _("Options"), colours.box_text_label, 11)
		option_y = inner_y + label_gap
		prefs.discord_clean_title = self.settings_switch_row(
			(right_col_x, option_y, right_col_w, compact_row_h),
			prefs.discord_clean_title,
			_("Clean title (Removes .feat etc)"),
			accent=discord_accent,
		)
		option_y += compact_row_h + row_gap
		prefs.discord_lastfm_button = self.settings_switch_row(
			(right_col_x, option_y, right_col_w, compact_row_h),
			prefs.discord_lastfm_button,
			_("Last.fm link button"),
			accent=discord_accent,
		)
		option_y += compact_row_h + row_gap
		prefs.discord_show_tauon_button = self.settings_switch_row(
			(right_col_x, option_y, right_col_w, compact_row_h),
			prefs.discord_show_tauon_button,
			_("Tauon website button"),
			accent=discord_accent,
		)
		option_y += compact_row_h + row_gap
		prefs.discord_keep_idle = self.settings_switch_row(
			(right_col_x, option_y, right_col_w, compact_row_h),
			prefs.discord_keep_idle,
			_("Keep idle"),
			accent=discord_accent,
		)

		return total_h

	def render_settings_view_category(self, x: int, y: int, w: int, accent: ColourRGBA, draw: bool = True) -> int:
		# (The View card is gone: its scroll settings moved into the Window
		# card; "Centered metadata side panel", "Zoom album art to fit" and
		# "MilkDrop visualiser" moved to the side panel album art right-click
		# menu; "Showcase visualisation" to the showcase view's right-click
		# menu; the Gallery section to the gallery's background right-click
		# menu.)
		h = self.render_settings_window_category(x, y, w, accent, draw)
		h += round(12 * self.gui.scale)
		h += self.render_settings_layouts_card(x, y + h, w, accent, draw)
		return h

	def draw_move_up_icon(self, rect: tuple[int, int, int, int], colour: ColourRGBA) -> None:
		x, y, w, h = rect
		unit = max(round(1.5 * self.gui.scale), 1)
		steps = 4
		cx = x + w // 2
		top = y + (h - steps * unit) // 2
		for k in range(steps):
			row_w = (k * 2 + 1) * unit
			self.ddt.rect((cx - row_w // 2, top + k * unit, row_w, unit), colour)

	def draw_move_down_icon(self, rect: tuple[int, int, int, int], colour: ColourRGBA) -> None:
		x, y, w, h = rect
		unit = max(round(1.5 * self.gui.scale), 1)
		steps = 4
		cx = x + w // 2
		top = y + (h - steps * unit) // 2
		for k in range(steps):
			row_w = ((steps - 1 - k) * 2 + 1) * unit
			self.ddt.rect((cx - row_w // 2, top + k * unit, row_w, unit), colour)

	def request_delete_layout(self, slot: int) -> None:
		custom = self.tauon.custom
		self.gui.message_box_confirm_callback = custom.delete_slot
		self.gui.message_box_no_callback = None
		self.gui.message_box_confirm_reference = (slot,)
		self.show_message(_("Delete layout '%s'?") % custom.slot_title(slot), mode="confirm")

	def render_settings_layouts_card(self, x: int, y: int, w: int, accent: ColourRGBA, draw: bool = True) -> int:
		gui = self.gui
		custom = self.tauon.custom
		custom.ensure_loaded()
		row_h = round(30 * gui.scale)
		row_gap = round(6 * gui.scale)
		slot_count = len(custom.slots)
		# Header + rows + the New Empty Slot tile + bottom pad
		card_h = round(128 * gui.scale) + slot_count * (row_h + row_gap)
		card_rect = (x, y, w, card_h)
		if not draw:
			return card_h

		inner_x, inner_y, inner_w, section_h = self.draw_settings_section(
			card_rect,
			_("Custom Layouts"),
			_("The order layouts appear in the layout menu. The current layout is highlighted."),
			accent,
		)
		button_w = round(26 * gui.scale)
		button_gap = round(4 * gui.scale)
		buttons_x = inner_x + inner_w - (button_w * 3 + button_gap * 2) - round(6 * gui.scale)
		for i in range(slot_count):
			active = gui.custom_mode and i == custom.active_slot
			fill = alpha_blend(ColourRGBA(255, 255, 255, 6), self.colours.box_background)
			if active:
				fill = alpha_blend(alpha_mod(accent, 26), fill)
			border = alpha_blend(ColourRGBA(255, 255, 255, 18), self.colours.box_text_border)
			if active:
				border = alpha_blend(alpha_mod(accent, 90), border)
			self.ddt.bordered_rect((inner_x, inner_y, inner_w, row_h), fill, border, round(1 * gui.scale))
			self.ddt.text(
				(inner_x + round(14 * gui.scale), inner_y + round(7 * gui.scale)),
				custom.slot_title(i),
				self.colours.box_text,
				212,
				bg=fill,
				max_w=buttons_x - inner_x - round(22 * gui.scale),
			)
			if i > 0:
				self.settings_icon_button(
					(buttons_x, inner_y, button_w, row_h),
					lambda i=i: custom.move_slot(i, -1),
					accent=accent,
					draw_icon=self.draw_move_up_icon,
					tooltip=_("Move up"),
				)
			if i < slot_count - 1:
				self.settings_icon_button(
					(buttons_x + button_w + button_gap, inner_y, button_w, row_h),
					lambda i=i: custom.move_slot(i, 1),
					accent=accent,
					draw_icon=self.draw_move_down_icon,
					tooltip=_("Move down"),
				)
			self.settings_icon_button(
				(buttons_x + (button_w + button_gap) * 2, inner_y, button_w, row_h),
				lambda i=i: self.request_delete_layout(i),
				accent=accent,
				icon=self.gui.delete_icon,
				tooltip=_("Delete"),
			)
			inner_y += row_h + row_gap

		self.settings_action_tile(
			(inner_x, inner_y, round(200 * gui.scale), round(34 * gui.scale)),
			_("New Empty Slot"),
			plug=custom.add_slot,
			accent=accent,
			show_arrow=False,
		)
		return card_h

	def render_settings_theme_category(self, x: int, y: int, w: int, accent: ColourRGBA, draw: bool = True) -> int:
		gui = self.gui
		prefs = self.prefs
		row_gap = round(6 * gui.scale)
		action_h = round(36 * gui.scale)
		preset_gap = round(6 * gui.scale)
		preset_w = round(28 * gui.scale)
		preset_h = round(16 * gui.scale)
		style_label_h = round(20 * gui.scale)
		style_bar_h = round(32 * gui.scale)
		card_inner_w = w - round(36 * gui.scale)
		theme_count = max(len(self.themes), 1)
		preset_columns = max(1, min(theme_count, (card_inner_w + preset_gap) // max(preset_w + preset_gap, 1)))
		preset_rows = max(1, math.ceil(theme_count / preset_columns))
		preset_grid_h = preset_rows * preset_h + max(0, preset_rows - 1) * preset_gap
		# Preset grid, action buttons, then the Background Style bar at the bottom
		card_h = round(132 * gui.scale) + preset_grid_h + row_gap * 3 + action_h + style_label_h + style_bar_h
		card_rect = (x, y, w, card_h)
		if not draw:
			return card_rect[3]

		inner_x, inner_y, inner_w, section_h = self.draw_settings_section(
			card_rect,
			_("Theme preset"),
				gui.theme_name,
			accent,
		)
		preset_columns = max(1, min(theme_count, (inner_w + preset_gap) // max(preset_w + preset_gap, 1)))
		preset_rows = max(1, math.ceil(theme_count / preset_columns))
		grid_w = preset_columns * preset_w + max(0, preset_columns - 1) * preset_gap
		grid_x = inner_x + max(0, (inner_w - grid_w) // 2)
		grid_y = inner_y + round(4 * gui.scale)
		for index, (theme_colours, theme_name, theme_number) in enumerate(self.themes):
			col = index % preset_columns
			row = index // preset_columns
			cell_x = grid_x + col * (preset_w + preset_gap)
			cell_y = grid_y + row * (preset_h + preset_gap)
			rect = (cell_x, cell_y, preset_w, preset_h)
			hit_rect = grow_rect(rect, round(4 * gui.scale))
			hover = self.coll(hit_rect)
			active = theme_name == gui.theme_name
			if active:
				self.ddt.bordered_rect(
					(
						cell_x - round(2 * gui.scale),
						cell_y - round(2 * gui.scale),
						preset_w + round(4 * gui.scale),
						preset_h + round(4 * gui.scale),
					),
					alpha_blend(alpha_mod(accent, 20), self.colours.box_background),
					alpha_blend(alpha_mod(accent, 120), self.colours.box_text_border),
					round(1 * gui.scale),
				)

			base_fill = alpha_blend(ColourRGBA(255, 255, 255, 6), self.colours.box_background)
			if hover:
				base_fill = alpha_blend(ColourRGBA(255, 255, 255, 10), base_fill)
			border = alpha_blend(ColourRGBA(255, 255, 255, 18), self.colours.box_text_border)
			if active:
				border = alpha_blend(alpha_mod(accent, 90), border)
			self.ddt.bordered_rect(rect, base_fill, border, round(1 * gui.scale))
			self.fields.add(hit_rect)
			if hover and self.click:
				prefs.theme = theme_number
				gui.reload_theme = True

			c1 = theme_colours.playlist_panel_background
			c2 = theme_colours.artist_playing
			c3 = theme_colours.title_playing
			c4 = theme_colours.bottom_panel_colour
			if theme_name == "Carbon":
				c1 = theme_colours.title_playing
				c2 = theme_colours.playlist_panel_background
				c3 = theme_colours.top_panel_background
			if theme_name == "Lavender Light":
				c1 = theme_colours.tab_background_active
			if theme_name == "Neon Love":
				c2 = theme_colours.artist_text
				c4 = ColourRGBA(118, 85, 194, 255)
				c1 = c4
			if theme_name == "Sky":
				c2 = theme_colours.artist_text
			if theme_name == "Sunken":
				c2 = theme_colours.title_text
				c3 = theme_colours.artist_text
				c4 = ColourRGBA(59, 115, 109, 255)
				c1 = c4

			strip_x = cell_x + round(2 * gui.scale)
			strip_y = cell_y + round(2 * gui.scale)
			strip_w = preset_w - round(4 * gui.scale)
			strip_h = preset_h - round(4 * gui.scale)
			colours = (c1, c2, c3, c4)
			segment_w = max(1, strip_w // len(colours))
			for colour_index, colour_value in enumerate(colours):
				segment_x = strip_x + colour_index * segment_w
				if colour_index == len(colours) - 1:
					segment_width = strip_x + strip_w - segment_x
				else:
					segment_width = segment_w
				self.ddt.rect((segment_x, strip_y, segment_width, strip_h), colour_value)

		style_bar_y = card_rect[1] + card_rect[3] - round(14 * gui.scale) - style_bar_h
		style_label_y = style_bar_y - style_label_h
		action_y = style_label_y - row_gap - action_h
		icon_button_w = round(26 * gui.scale)
		icon_gap = round(4 * gui.scale)
		action_total_w = icon_button_w * 3 + icon_gap * 2
		action_x = inner_x + inner_w - action_total_w
		self.settings_icon_button(
			(action_x, action_y, icon_button_w, action_h),
			self.create_user_theme,
			accent=accent,
			draw_icon=self.draw_duplicate_theme_icon,
			tooltip=_("Duplicate"),
		)
		self.settings_icon_button(
			(action_x + icon_button_w + icon_gap, action_y, icon_button_w, action_h),
			self.open_theme_editor,
			accent=accent,
			icon=self.gui.rename_tracks_icon,
			tooltip=_("Edit"),
		)
		self.settings_icon_button(
			(action_x + (icon_button_w + icon_gap) * 2, action_y, icon_button_w, action_h),
			self.delete_active_user_theme,
			accent=accent,
			icon=self.gui.delete_icon,
			tooltip=_("Delete"),
		)

		# One mutually exclusive choice between the plain theme, window
		# transparency, auto-theming and the album-art backgrounds
		self.ddt.text((inner_x, style_label_y), _("Background Style"), self.colours.box_text_label, 11)
		self.settings_segmented_bar(
			(inner_x, style_bar_y),
			(
				(_("Standard"), self.tauon.set_bg_style_base(1), self.tauon.set_bg_style_base),
				(_("Glass"), self.tauon.set_bg_style_transparent_accent(1), self.tauon.set_bg_style_transparent_accent),
				(_("Glass+"), self.tauon.set_bg_style_full_transparent(1), self.tauon.set_bg_style_full_transparent),
				(_("Colourise"), self.tauon.set_bg_style_colourise(1), self.tauon.set_bg_style_colourise),
				(_("Art"), self.tauon.set_art_bg_clear(1), self.tauon.set_art_bg_clear),
				(_("Artist"), self.tauon.set_art_bg_artist(1), self.tauon.set_art_bg_artist),
				(_("Frost lo"), self.tauon.set_art_bg_frosted_low(1), self.tauon.set_art_bg_frosted_low),
				(_("Frost hi"), self.tauon.set_art_bg_frosted_high(1), self.tauon.set_art_bg_frosted_high),
			),
			accent,
			width=inner_w,
		)

		return card_rect[3]

	def render_settings_window_category(self, x: int, y: int, w: int, accent: ColourRGBA, draw: bool = True) -> int:
		gui = self.gui
		prefs = self.prefs
		column_gap = round(12 * gui.scale)
		left_w = max(round(270 * gui.scale), min(round(w * 0.5), w - round(220 * gui.scale)))
		right_w = w - left_w - column_gap
		left_rect = (x, y, left_w, round(500 * gui.scale))
		right_rect = (x + left_w + column_gap, y, right_w, round(360 * gui.scale))
		if not draw:
			return max(left_rect[3], right_rect[3])

		row_h = round(30 * gui.scale)
		row_gap = round(6 * gui.scale)
		inner_x, inner_y, inner_w, section_h = self.draw_settings_section(
			left_rect,
			_("Window"),
			_("Notifications, on-screen controls, scrolling and scale."),
			accent,
		)
		self.settings_switch_row((inner_x, inner_y, inner_w, row_h), self.tauon.toggle_notifications, _("Emit track change notifications"), accent=accent)
		inner_y += row_h + row_gap
		self.settings_switch_row((inner_x, inner_y, inner_w, row_h), self.tauon.toggle_borderless, _("Draw own window decorations"), accent=accent)
		inner_y += row_h + row_gap
		self.settings_switch_row(
			(inner_x, inner_y, inner_w, row_h), self.tauon.toggle_titlebar_line, _("Show playing in titlebar"),
			accent=accent, disabled=self.tauon.draw_border)
		inner_y += row_h + row_gap
		self.settings_switch_row(
			(inner_x, inner_y, inner_w, row_h), self.tauon.toggle_rounded_corners, _("Rounded window corners"),
			accent=accent, disabled=not self.tauon.draw_border)
		inner_y += row_h + row_gap
		new_radius = self.draw_settings_range_slider(
			(inner_x, inner_y, inner_w, round(46 * gui.scale)),
			_("Corner radius"),
			float(prefs.corner_radius),
			2,
			30,
			1,
			accent=accent,
			formatter=lambda value: f"{round(value)} px",
			disabled=not (self.tauon.draw_border and prefs.rounded_corners),
		)
		if round(new_radius) != prefs.corner_radius:
			prefs.corner_radius = round(new_radius)
			gui.request_frame()
		inner_y += round(52 * gui.scale)
		old_on_top = prefs.mini_mode_on_top
		prefs.mini_mode_on_top = self.settings_switch_row((inner_x, inner_y, inner_w, row_h), prefs.mini_mode_on_top, _("Mini-mode always on top"), accent=accent)
		if self.wayland and prefs.mini_mode_on_top and prefs.mini_mode_on_top != old_on_top:
			self.show_message(_("Always-on-top feature not yet implemented for Wayland mode"))
		# ("Top-panel visualiser" switch moved to the top-panel right-click
		# window menu)

		inner_y += row_h + row_gap
		self.settings_switch_row(
			(inner_x, inner_y, inner_w, round(42 * gui.scale)),
			self.tauon.toggle_smooth_scroll,
			_("Smooth scrolling"),
			_("Use inertial scrolling"),
			accent=accent,
			disabled=prefs.macos,
		)
		inner_y += round(42 * gui.scale) + row_gap
		prefs.smooth_scroll_speed = self.draw_settings_range_slider(
			(inner_x, inner_y, inner_w, round(46 * gui.scale)),
			_("Smooth scroll speed"),
			prefs.smooth_scroll_speed,
			0.25,
			10.0,
			0.05,
			accent=accent,
			formatter=lambda number: f"{number:.2f}x",
		)
		inner_y += round(52 * gui.scale)

		def normalize_scale_value(value: float) -> float:
			scale_value = max(min(round(round(value / 0.05) * 0.05, 2), 3.5), 0.5)
			if scale_value in (0.95, 1.05):
				scale_value = 1.0
			if scale_value in (1.95, 2.05):
				scale_value = 2.0
			if scale_value in (2.95, 3.05):
				scale_value = 3.0
			return scale_value

		def set_scale(value: float) -> None:
			prefs.scale_want = normalize_scale_value(value)
			prefs.x_scale = False
			gui.request_frame()
			gui.update_layout = True

		preview_scale = float(
			prefs.scale_want
			if self.settings_scale_preview_value is None else
			self.settings_scale_preview_value
		)
		scale_slider_rect = (inner_x, inner_y, inner_w, round(46 * gui.scale))
		holding_scale_slider = self.inp.mouse_down and self.coll(scale_slider_rect)
		new_preview_scale = self.draw_settings_range_slider(
			scale_slider_rect,
			_("Interface scale"),
			preview_scale,
			0.5,
			3.5,
			0.05,
			accent=accent,
			formatter=lambda value: (
				_("auto")
				if prefs.x_scale and not holding_scale_slider and self.settings_scale_preview_value is None else
				f"{normalize_scale_value(value):.2f}x"
			),
		)
		new_preview_scale = normalize_scale_value(new_preview_scale)
		if abs(new_preview_scale - preview_scale) > 0.0001:
			self.settings_scale_preview_value = new_preview_scale
		if self.inp.mouse_up and self.settings_scale_preview_value is not None:
			set_scale(self.settings_scale_preview_value)
			self.settings_scale_preview_value = None
		inner_y += round(52 * gui.scale)
		self.settings_switch_row((inner_x, inner_y, inner_w, row_h), self.toggle_x_scale, _("Auto scale"), accent=accent)

		inner_x, inner_y, inner_w, section_h = self.draw_settings_section(
			right_rect,
			_("Tray"),
			_("System tray options."),
			accent,
		)
		self.settings_switch_row((inner_x, inner_y, inner_w, row_h), self.tauon.toggle_use_tray, _("Show icon in system tray"), accent=accent)
		inner_y += row_h + row_gap
		self.settings_switch_row((inner_x, inner_y, inner_w, row_h), self.tauon.toggle_min_tray, _("Close to tray"), accent=accent)
		inner_y += row_h + row_gap
		self.settings_switch_row((inner_x, inner_y, inner_w, row_h), self.tauon.toggle_start_in_tray, _("Start in tray"), accent=accent, disabled=not prefs.use_tray)
		inner_y += row_h + row_gap
		self.settings_switch_row((inner_x, inner_y, inner_w, row_h), self.tauon.toggle_text_tray, _("Show title text"), accent=accent)
		inner_y += row_h + row_gap
		old_theme = prefs.tray_theme
		mono = self.settings_switch_row((inner_x, inner_y, inner_w, row_h), prefs.tray_theme == "gray", _("Monochrome tray icon"), accent=accent)
		prefs.tray_theme = "gray" if mono else "pink"
		if prefs.tray_theme != old_theme:
			self.tauon.set_tray_icons(force=True)
			self.show_message(_("Restart Tauon for change to take effect"))

		return max(left_rect[3], right_rect[3])

	def render_settings_audio_category(self, x: int, y: int, w: int, accent: ColourRGBA, draw: bool = True) -> int:
		gui = self.gui
		prefs = self.prefs
		if not self.phazor_found or prefs.backend != Backend.PHAZOR:
			body_h = round(120 * gui.scale)
			if draw:
				self.draw_settings_note(
					(x, y, w, body_h),
					_("Audio controls are only available with the PHAzOR backend."),
					accent,
					_("Playback backend"),
				)
			return body_h

		column_gap = round(12 * gui.scale)
		left_w = max(round(270 * gui.scale), min(round(w * 0.48), w - round(240 * gui.scale)))
		right_w = w - left_w - column_gap
		row1_h = round(416 * gui.scale)
		row2_h = round(355 * gui.scale)
		if not draw:
			return row1_h + row2_h + column_gap

		row_h = round(30 * gui.scale)
		row_gap = round(6 * gui.scale)
		left_rect = (x, y, left_w, row1_h)
		right_rect = (x + left_w + column_gap, y, right_w, row1_h)
		inner_x, inner_y, inner_w, section_h = self.draw_settings_section(
			left_rect,
			_("Playback and cache"),
			_("Playback behaviour and local file caching."),
			accent,
		)
		self.settings_switch_row((inner_x, inner_y, inner_w, row_h), self.tauon.toggle_pause_fade, _("Fade on pause and stop"), accent=accent)
		inner_y += row_h + row_gap
		self.settings_switch_row((inner_x, inner_y, inner_w, row_h), self.tauon.toggle_jump_crossfade, _("Fade on track jump"), accent=accent)
		inner_y += row_h + row_gap
		prefs.back_restarts = self.settings_switch_row((inner_x, inner_y, inner_w, row_h), prefs.back_restarts, _("Back restarts to beginning"), accent=accent)
		inner_y += row_h + row_gap
		prefs.precache = self.settings_switch_row((inner_x, inner_y, inner_w, row_h), prefs.precache, _("Cache local files"), accent=accent)
		inner_y += row_h + row_gap
		old_tmp_cache = prefs.tmp_cache
		prefs.tmp_cache = self.settings_switch_row((inner_x, inner_y, inner_w, row_h), prefs.tmp_cache ^ True, _("Use persistent network cache"), accent=accent) ^ True
		if old_tmp_cache != prefs.tmp_cache and self.tauon.cachement:
			self.tauon.cachement.__init__(self.tauon)
		inner_y += row_h + row_gap
		# Applies from the next track load. Shown inverted: when enabled,
		# network tracks are fully downloaded to the cache before playing
		# (network_stream off); when disabled, they are streamed directly.
		prefs.network_stream = self.settings_switch_row((inner_x, inner_y, inner_w, row_h), prefs.network_stream ^ True, _("Wait for entire file"), accent=accent) ^ True
		inner_y += row_h + row_gap
		cache_size_gb = round(self.draw_settings_range_slider(
			(inner_x, inner_y, inner_w, round(46 * gui.scale)),
			_("Cache size"),
			float(self.prefs.cache_limit / 1000),
			0.5,
			1000,
			0,
			accent=accent,
			formatter=lambda number: f"{round(number, 1):.1f} GB",
			log_scale=True,
		), 1)
		prefs.cache_limit = int(cache_size_gb * 1000)
		inner_y += round(52 * gui.scale)
		old_resample = prefs.avoid_resampling
		prefs.avoid_resampling = self.settings_switch_row((inner_x, inner_y, inner_w, row_h), prefs.avoid_resampling, _("Avoid resampling"), accent=accent)
		if prefs.avoid_resampling != old_resample:
			self.pctl.playerCommand = "reload"
			self.pctl.playerCommandReady = True

		self.draw_audio_device_selector(right_rect, accent)

		row2_y = y + row1_h + column_gap
		left_rect = (x, row2_y, left_w, row2_h)
		right_rect = (x + left_w + column_gap, row2_y, right_w, row2_h)

		inner_x, inner_y, inner_w, section_h = self.draw_settings_section(
			left_rect,
			_("ReplayGain"),
			_("Playback loudness matching."),
			accent,
		)
		bar_h = self.settings_segmented_bar(
			(inner_x, inner_y),
			(
				(_("Off"), self.tauon.switch_rg_off(1), self.tauon.switch_rg_off),
				(_("Auto"), self.tauon.switch_rg_auto(1), self.tauon.switch_rg_auto),
				(_("Album"), self.tauon.switch_rg_album(1), self.tauon.switch_rg_album),
				(_("Tracks"), self.tauon.switch_rg_track(1), self.tauon.switch_rg_track),
			),
			accent,
			width=inner_w,
		)
		inner_y += bar_h + round(12 * gui.scale)
		old_replay_preamp = prefs.replay_preamp
		prefs.replay_preamp = int(self.settings_stepper_row(
			(inner_x, inner_y, inner_w, round(30 * gui.scale)),
			_("Pre-amp"),
			prefs.replay_preamp,
			-15,
			15,
			accent=accent,
			formatter=lambda number: f"{number:+d} dB" if number else "0 dB",
		))
		if prefs.replay_preamp != old_replay_preamp:
			self.tauon.request_replaygain_update()
		inner_y += row_h + row_gap
		self.settings_switch_row(
			(inner_x, inner_y, inner_w, row_h),
			self.tauon.toggle_replaygain_compression,
			_("Allow compression"),
			accent=accent,
		)
		inner_y += row_h + round(10 * gui.scale)

		if self.pctl.playing_state == PlayingState.STOPPED or not self.pctl.replaygain_applied:
			applied_text = _("Applied") + ": " + _("Inactive")
		else:
			applied_text = _("Applied") + f": {self.pctl.active_replaygain_gain_db:+.2f} dB"
		self.ddt.text((inner_x, inner_y), applied_text, self.colours.box_text_label, 11)
		inner_y += round(19 * gui.scale)

		if self.pctl.output_compression_active:
			compression_text = (
				_("Compression") + ": " + _("Active")
				+ f" ({self.pctl.output_compression_reduction_db:.2f} dB)"
			)
			compression_colour = accent
		elif self.pctl.output_compression_enabled:
			compression_text = _("Compression") + ": " + _("Ready")
			compression_colour = self.colours.box_text_label
		else:
			compression_text = _("Compression") + ": " + _("Off")
			compression_colour = self.colours.box_sub_text
		self.ddt.text((inner_x, inner_y), compression_text, compression_colour, 11)

		inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
			right_rect,
			_("Equalizer"),
			_("Ten-band playback EQ."),
			accent,
		)
		if not isinstance(prefs.eq, list):
			try:
				prefs.eq = list(prefs.eq)
			except Exception:
				prefs.eq = []
		if len(prefs.eq) < 10:
			prefs.eq.extend([0.0] * (10 - len(prefs.eq)))
		elif len(prefs.eq) > 10:
			prefs.eq = prefs.eq[:10]

		eq_enabled = self.tauon.toggle_eq(1)
		switch_w = round(150 * gui.scale)
		self.settings_switch_row((inner_x, inner_y, switch_w, round(30 * gui.scale)), self.tauon.toggle_eq, _("Enable EQ"), accent=accent)
		reset_w = round(96 * gui.scale)
		reset_x = inner_x + inner_w - reset_w
		self.settings_action_tile((reset_x, inner_y, reset_w, round(30 * gui.scale)), _("Reset"), plug=self.reset_eq, accent=accent)
		bar_y = inner_y + round(44 * gui.scale)
		bar_h = min(round(150 * gui.scale), inner_h - round(52 * gui.scale))
		center = bar_h // 2
		bar_w = max(round(18 * gui.scale), (inner_w - round(18 * gui.scale)) // 10)
		bar_gap = max(round(3 * gui.scale), (inner_w - bar_w * 10) // 9)
		db_range = 12
		labels = ("31", "62", "125", "250", "500", "1k", "2k", "4k", "8k", "16k")
		self.ddt.rect((inner_x, bar_y + center, inner_w, round(1 * gui.scale)), alpha_blend(ColourRGBA(255, 255, 255, 20), self.colours.box_text_border))
		bar_fill_colour = accent if eq_enabled else alpha_blend(ColourRGBA(255, 255, 255, 80), self.colours.box_text_border)
		bar_x = inner_x
		for i, q in enumerate(prefs.eq):
			track_rect = (bar_x, bar_y, bar_w, bar_h)
			self.ddt.rect(track_rect, ColourRGBA(255, 255, 255, 18))
			hit_rect = grow_rect(track_rect, round(3 * gui.scale))
			self.fields.add(hit_rect)
			if self.coll(hit_rect):
				if self.inp.mouse_down:
					target = self.inp.mouse_position[1] - bar_y - center
					target = (target / max(center, 1)) * db_range * -1
					target = min(target, db_range)
					target = max(target, db_range * -1)
					if -0.1 < target < 0.1:
						target = 0
					prefs.eq[i] = target
					self.gui.request_frame()
					self.pctl.playerCommand = "seteq"
					self.pctl.playerCommandReady = True
				if self.right_click:
					prefs.eq[i] = 0
					self.gui.request_frame()
					self.pctl.playerCommand = "seteq"
					self.pctl.playerCommandReady = True

			start = (q / db_range) * center * -1
			fill_rect = (bar_x, bar_y + center, bar_w, start)
			self.ddt.rect(fill_rect, bar_fill_colour)
			self.ddt.text((bar_x + bar_w // 2, bar_y + bar_h + round(6 * gui.scale), 2), labels[i], self.colours.box_text_label, 10)
			bar_x += bar_w + bar_gap

		return row1_h + row2_h + column_gap

	def reset_eq(self) -> None:
		if not isinstance(self.prefs.eq, list):
			self.prefs.eq = [0.0] * 10
		for i in range(min(len(self.prefs.eq), 10)):
			self.prefs.eq[i] = 0.0
		self.gui.request_frame()
		self.pctl.playerCommand = "seteq"
		self.pctl.playerCommandReady = True

	def render_settings_transcode_category(self, x: int, y: int, w: int, accent: ColourRGBA, draw: bool = True) -> int:
		gui = self.gui
		prefs = self.prefs
		column_gap = round(12 * gui.scale)
		section_header_h = round(66 * gui.scale)
		section_bottom_pad = round(14 * gui.scale)
		row1_h = section_header_h + round(150 * gui.scale) + section_bottom_pad
		if prefs.transcode_codec == "opus":
			row1_h += round(36 * gui.scale)
		if prefs.transcode_codec != "flac":
			row1_h += round(30 * gui.scale)
		row2_h = section_header_h + round(322 * gui.scale) + section_bottom_pad
		if not draw:
			return row1_h + row2_h + column_gap

		row1_rect = (x, y, w, row1_h)
		inner_x, inner_y, inner_w, section_h = self.draw_settings_section(
			row1_rect,
			"",
			"",
			accent,
		)
		inner_column_gap = round(18 * gui.scale)
		left_w = max(round(270 * gui.scale), min(round(inner_w * 0.53), inner_w - round(220 * gui.scale)))
		right_w = inner_w - left_w - inner_column_gap
		left_x = inner_x
		right_x = left_x + left_w + inner_column_gap
		column_label_y = inner_y
		column_subtitle_y = column_label_y + round(16 * gui.scale) + round(2 * gui.scale)
		column_body_y = column_label_y + round(34 * gui.scale)
		divider_x = left_x + left_w + inner_column_gap // 2
		divider_h = row1_rect[1] + row1_rect[3] - round(14 * gui.scale) - column_label_y
		self.ddt.text((left_x, column_label_y), _("Encoding"), self.colours.box_text, 212)
		self.ddt.text((left_x, column_subtitle_y), _("Select default codec and bitrate."), self.colours.box_text_label, 10, max_w=left_w)
		self.ddt.text((right_x, column_label_y), _("Files"), self.colours.box_text, 212)
		self.ddt.text((right_x, column_subtitle_y), _("Output location and overwrite rules."), self.colours.box_text_label, 10, max_w=right_w)
		self.ddt.rect(
			(divider_x, column_label_y, round(1 * gui.scale), divider_h),
			alpha_blend(alpha_mod(accent, 70), self.colours.box_text_border),
		)

		inner_x = left_x
		inner_y = column_body_y + round(2 * gui.scale)
		inner_w = left_w
		bar_h = self.settings_segmented_bar(
			(inner_x, inner_y),
			(
				("FLAC", prefs.transcode_codec == "flac", self.tauon.switch_flac),
				("OPUS", prefs.transcode_codec == "opus", self.tauon.switch_opus),
				("OGG", prefs.transcode_codec == "ogg", self.tauon.switch_ogg),
				("MP3", prefs.transcode_codec == "mp3", self.tauon.switch_mp3),
			),
			accent,
			width=inner_w,
		)
		inner_y += bar_h + round(12 * gui.scale)
		if prefs.transcode_codec == "opus":
			self.settings_switch_row((inner_x, inner_y, inner_w, round(30 * gui.scale)), self.tauon.switch_opus_ogg, _("Save opus as .ogg"), accent=accent)
			inner_y += round(36 * gui.scale)
		if prefs.transcode_codec != "flac":
			prefs.transcode_bitrate = int(self.settings_stepper_row(
				(inner_x, inner_y, inner_w, round(30 * gui.scale)),
				_("Bitrate"),
				prefs.transcode_bitrate,
				32,
				320,
				accent=accent,
				step=8,
				formatter=lambda number: f"{int(number)} kbps",
			))

		inner_x = right_x
		inner_y = column_body_y + round(2 * gui.scale)
		inner_w = right_w
		self.settings_action_tile((inner_x, inner_y, inner_w, round(36 * gui.scale)), _("Open output folder"), self.tauon.open_encode_out, accent)
		inner_y += round(42 * gui.scale)
		self.settings_switch_row((inner_x, inner_y, inner_w, round(30 * gui.scale)), self.tauon.toggle_transcode_output, _("Save to output folder"), accent=accent)
		inner_y += round(36 * gui.scale)
		self.settings_switch_row((inner_x, inner_y, inner_w, round(30 * gui.scale)), self.tauon.toggle_transcode_inplace, _("Save and overwrite files in place"), accent=accent)

		row2_y = y + row1_h + column_gap
		sync_rect = (x, row2_y, w, row2_h)
		inner_x, inner_y, inner_w, section_h = self.draw_settings_section(
			sync_rect,
			_("Sync to device"),
			_("Transcode and copy a selected playlist."),
			accent,
		)
		pl = None
		if prefs.sync_playlist:
			pl = self.pctl.id_to_pl(prefs.sync_playlist)
		if pl is None:
			prefs.sync_playlist = None
		selected_playlist = _("No sync playlist selected")
		if prefs.sync_playlist and pl is not None:
			selected_playlist = self.pctl.multi_playlist[pl].title
		self.draw_settings_note((inner_x, inner_y, inner_w, round(42 * gui.scale)), selected_playlist, accent, _("Source Playlist"))
		inner_y += round(50 * gui.scale)

		self.ddt.text((inner_x, inner_y), _("Target folder"), self.colours.box_text_label, 11, bg=self.ddt.text_background_colour)
		inner_y += round(18 * gui.scale)
		field_h = round(24 * gui.scale)
		rect1 = (inner_x, inner_y, inner_w - round(42 * gui.scale), field_h)
		self.draw_settings_text_field(
			rect1,
			self.tauon.sync_target,
			accent,
			stored_value=self.tauon.sync_target.text,
			editable=not gui.sync_progress,
		)
		icon_rect = (rect1[0] + rect1[2] + round(8 * gui.scale), inner_y + round(1 * gui.scale), round(20 * gui.scale), round(20 * gui.scale))
		self.fields.add(icon_rect)
		icon_colour = self.colours.box_text_label
		if self.coll(icon_rect):
			icon_colour = accent
			if self.click:
				paths = auto_get_sync_targets()
				if paths:
					self.tauon.sync_target.text = paths[0]
					self.show_message(_("A mounted music folder was found!"), mode="done")
				else:
					self.show_message(_("Could not auto-detect mounted device path."), _("Make sure the device is mounted and path is accessible."))
		gui.power_bar_icon.render(icon_rect[0], icon_rect[1], icon_colour)
		inner_y += round(34 * gui.scale)
		prefs.sync_deletes = self.settings_switch_row((inner_x, inner_y, inner_w, round(30 * gui.scale)), prefs.sync_deletes, _("Delete other folders in target"), accent=accent)
		inner_y += round(36 * gui.scale)
		prefs.bypass_transcode = self.settings_switch_row((inner_x, inner_y, inner_w, round(30 * gui.scale)), prefs.bypass_transcode ^ True, _("Transcode files"), accent=accent) ^ True
		inner_y += round(36 * gui.scale)
		prefs.smart_bypass = self.settings_switch_row((inner_x, inner_y, inner_w, round(30 * gui.scale)), prefs.smart_bypass ^ True, _("Bypass low bitrate"), accent=accent) ^ True
		inner_y += round(40 * gui.scale)
		start_label = _("Start Sync") if prefs.bypass_transcode else _("Start Transcode and Sync")
		if gui.stop_sync:
			self.settings_action_tile((inner_x, inner_y, inner_w, round(36 * gui.scale)), _("Stopping..."), accent=accent, emphasis=True)
		elif gui.sync_progress:
			if self.settings_action_tile((inner_x, inner_y, inner_w, round(36 * gui.scale)), _("Stop"), accent=accent, emphasis=True):
				gui.stop_sync = True
				gui.sync_progress = _("Aborting Sync")
		else:
			def start_sync() -> None:
				if pl is not None:
					self.tauon.auto_sync(pl)
				else:
					self.show_message(_("Select a source playlist"), _("Right click tab > Misc... > Set as sync playlist"))
			self.settings_action_tile((inner_x, inner_y, inner_w, round(36 * gui.scale)), start_label, start_sync, accent, emphasis=True)
		return row1_h + row2_h + column_gap

	def settings_account_services(self) -> tuple[list[tuple[int, str, str]], list[tuple[int, str, str]]]:
		prefs = self.prefs
		scrobbling = [
			(1, "Last.fm" if not prefs.use_libre_fm else "Libre.fm", _("Scrobbles and loves.")),
			(2, "ListenBrainz", _("Token-based scrobbling.")),
			(9, "Maloja", _("Self-hosted scrobbling.")),
		]
		streaming = [
			(10, "Jellyfin", _("Network library.")),
			(12, "TIDAL", _("Albums and tracks.")),
			(7, "Airsonic", _("Subsonic library.")),
			(5, "PLEX", _("Network library.")),
			(11, "Tauon", _("Tauon-to-Tauon sync.")),
		]

		if self.inp.key_shift_down:
			scrobbling.append((4, "fanart.tv", _("Artwork sources.")))

		return scrobbling, streaming

	def render_settings_service_detail(
		self,
		view: int,
		x: int,
		y: int,
		w: int,
		accent: ColourRGBA,
		draw: bool = True,
	) -> int:
		gui = self.gui
		tauon = self.tauon
		prefs = self.prefs
		card_gap = round(12 * gui.scale)
		row_h = round(30 * gui.scale)
		info_row_h = round(42 * gui.scale)
		row_gap = round(6 * gui.scale)
		action_h = round(36 * gui.scale)
		field_h = round(42 * gui.scale)
		note_h = round(46 * gui.scale)

		if view == 1:
			service_name = "Last.fm" if not prefs.use_libre_fm else "Libre.fm"
			account_subtitle = prefs.last_fm_username or _("Account not connected.")
			card1_h = round(252 * gui.scale) if prefs.last_fm_token is None else round(216 * gui.scale)
			card2_h = round(200 * gui.scale)
			card3_h = round(146 * gui.scale)
			total_h = card1_h + card_gap + card2_h + card_gap + card3_h
			if not draw:
				return total_h

			card_y = y
			rect = (x, card_y, w, card1_h)
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
				rect,
				service_name,
				_("Scrobble playback and sync loves."),
				accent,
			)
			self.settings_switch_row(
				(inner_x, inner_y, inner_w, info_row_h),
				self.tauon.toggle_lfm_auto,
				_("Enable scrobbling"),
				account_subtitle,
				accent,
			)
			inner_y += info_row_h + row_gap
			if prefs.last_fm_token is None:
				self.draw_settings_action_row(
					(inner_x, inner_y, inner_w, action_h),
					[
						(_("Login"), self.lastfm.auth1, True),
						(_("Done"), self.lastfm.auth2, False),
					],
					accent,
				)
				inner_y += action_h + row_gap
				if self.lastfm.url is None:
					prefs.use_libre_fm = self.settings_switch_row(
						(inner_x, inner_y, inner_w, row_h),
						prefs.use_libre_fm,
						_("Use LibreFM"),
						accent=accent,
					)
					inner_y += row_h + row_gap
				note_text = _("Use Login, finish the browser step, then click Done.")
				if self.lastfm.url is not None:
					note_text = _("Finish authorisation in the browser, then click Done.")
				self.draw_settings_note((inner_x, inner_y, inner_w, note_h), note_text, accent, _("Authorisation"))
			else:
				self.draw_settings_action_row(
					(inner_x, inner_y, inner_w, action_h),
					[
						(_("Forget account"), self.lastfm.auth3, True),
					],
					accent,
				)
				inner_y += action_h + row_gap
				self.draw_settings_note((inner_x, inner_y, inner_w, note_h), prefs.last_fm_username, accent, _("Signed in as"))

			card_y += card1_h + card_gap
			rect = (x, card_y, w, card2_h)
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
				rect,
				_("Library sync"),
				_("Pull loves and scrobble counts into Tauon."),
				accent,
			)
			self.draw_settings_action_row(
				(inner_x, inner_y, inner_w, action_h),
				[
					(_("Get user loves"), self.get_user_love, True),
					(_("Clear local loves"), self.clear_local_loves, False),
				],
				accent,
			)
			inner_y += action_h + row_gap
			self.draw_settings_action_row(
				(inner_x, inner_y, inner_w, action_h),
				[
					(_("Get friend loves"), self.get_friend_love, True),
					(_("Clear friend loves"), self.lastfm.clear_friends_love, False),
				],
				accent,
			)
			inner_y += action_h + row_gap
			self.draw_settings_action_row(
				(inner_x, inner_y, inner_w, action_h),
				[
					(_("Get scrobble counts"), self.get_scrobble_counts, True),
					(_("Clear counts"), self.clear_scrobble_counts, False),
				],
				accent,
			)

			card_y += card2_h + card_gap
			rect = (x, card_y, w, card3_h)
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
				rect,
				_("Options"),
				_("Controls for import and playback display."),
				accent,
			)
			old_pull = prefs.lastfm_pull_love
			prefs.lastfm_pull_love = self.settings_switch_row(
				(inner_x, inner_y, inner_w, row_h),
				prefs.lastfm_pull_love,
				_("Pull love on scrobble/rescan"),
				accent=accent,
			)
			if old_pull != prefs.lastfm_pull_love and prefs.lastfm_pull_love:
				self.show_message(_("This will overwrite local love state when it differs from last.fm."))
			inner_y += row_h + row_gap
			self.settings_switch_row(
				(inner_x, inner_y, inner_w, row_h),
				self.tauon.toggle_scrobble_mark,
				_("Show threshold marker"),
				accent=accent,
			)
			return total_h

		if view == 2:
			card1_h = round(210 * gui.scale)
			card2_h = round(152 * gui.scale)
			total_h = card1_h + card_gap + card2_h
			if not draw:
				return total_h

			rect = (x, y, w, card1_h)
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
				rect,
				"ListenBrainz",
				_("Token-based scrobbling."),
				accent,
			)
			token_status = _("Token saved.") if prefs.lb_token else _("Paste a token to enable ListenBrainz.")
			self.settings_switch_row(
				(inner_x, inner_y, inner_w, info_row_h),
				self.tauon.toggle_lb,
				_("Enable scrobbling"),
				token_status,
				accent,
			)
			inner_y += info_row_h + row_gap
			self.draw_settings_action_row(
				(inner_x, inner_y, inner_w, action_h),
				[
					(_("Paste token"), self.tauon.lb.paste_key, True),
					(_("Clear"), self.tauon.lb.clear_key, False),
				],
				accent,
			)
			inner_y += action_h + row_gap
			endpoint_note = prefs.listenbrainz_url or _("Using the default ListenBrainz endpoint.")
			self.draw_settings_note((inner_x, inner_y, inner_w, note_h), endpoint_note, accent, _("Endpoint"))

			rect = (x, y + card1_h + card_gap, w, card2_h)
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
				rect,
				_("Options"),
				_("Extra controls for ListenBrainz."),
				accent,
			)
			self.draw_settings_action_row(
				(inner_x, inner_y, inner_w, action_h),
				[
					(_("Open profile"), lambda: webbrowser.open("https://listenbrainz.org/profile/", new=2, autoraise=True), True),
				],
				accent,
			)
			inner_y += action_h + row_gap
			self.settings_switch_row(
				(inner_x, inner_y, inner_w, row_h),
				self.tauon.toggle_scrobble_mark,
				_("Show threshold marker"),
				accent=accent,
			)
			return total_h

		if view == 4:
			card_h = round(240 * gui.scale)
			if not draw:
				return card_h

			def flip_current_artist() -> None:
				if self.inp.key_shift_down:
					prefs.bg_flips.clear()
					self.show_message(_("Reset flips"), mode="done")
					return
				track = self.pctl.playing_object()
				artist = get_artist_safe(track)
				if artist:
					if artist not in prefs.bg_flips:
						prefs.bg_flips.add(artist)
					else:
						prefs.bg_flips.remove(artist)
					tauon.style_overlay.flush()
				self.show_message(_("OK"), mode="done")

			rect = (x, y, w, card_h)
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
				rect,
				"fanart.tv",
				_("Artwork sources for artist images and covers."),
				accent,
			)
			self.draw_settings_note(
				(inner_x, inner_y, inner_w, note_h),
				_("Use fanart.tv for artist images and manual cover art lookup."),
				accent,
				_("About"),
			)
			inner_y += note_h + row_gap
			prefs.enable_fanart_cover = self.settings_switch_row(
				(inner_x, inner_y, inner_w, row_h),
				prefs.enable_fanart_cover,
				_("Cover art (manual only)"),
				accent=accent,
			)
			inner_y += row_h + row_gap
			prefs.enable_fanart_artist = self.settings_switch_row(
				(inner_x, inner_y, inner_w, row_h),
				prefs.enable_fanart_artist,
				_("Artist images (automatic)"),
				accent=accent,
			)
			inner_y += row_h + row_gap
			self.draw_settings_action_row(
				(inner_x, inner_y, inner_w, action_h),
				[
					(_("Flip current"), flip_current_artist, True),
				],
				accent,
			)
			return card_h

		if view == 5:
			two_factor = tauon.plex.two_factor_required
			card1_h = round(122 * gui.scale) if two_factor else round(266 * gui.scale)
			card2_h = round(206 * gui.scale)
			total_h = card1_h + card_gap + card2_h
			if not draw:
				return total_h

			rect = (x, y, w, card1_h)
			subtitle = _("Finish the sign-in step to continue.") if two_factor else _("Connect to a Plex server.")
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(rect, "PLEX", subtitle, accent)
			if two_factor:
				two_factor_text = self.settings_text_input(
					(inner_x, inner_y, inner_w, field_h),
					_("Two-factor code"),
					tauon.text_plex_2fa,
					tauon.text_plex_2fa.text,
					accent,
				)
				tauon.text_plex_2fa.text = two_factor_text
			else:
				prefs.plex_username = self.settings_text_input(
					(inner_x, inner_y, inner_w, field_h),
					_("Username / Email"),
					tauon.text_plex_usr,
					prefs.plex_username,
					accent,
				)
				inner_y += field_h + row_gap
				prefs.plex_password = self.settings_text_input(
					(inner_x, inner_y, inner_w, field_h),
					_("Password"),
					tauon.text_plex_pas,
					prefs.plex_password,
					accent,
					secret=True,
				)
				inner_y += field_h + row_gap
				prefs.plex_servername = self.settings_text_input(
					(inner_x, inner_y, inner_w, field_h),
					_("Server name"),
					tauon.text_plex_lib,
					prefs.plex_servername,
					accent,
				)

				inner_y += field_h + row_gap
				prefs.plex_library = self.settings_text_input(
					(inner_x, inner_y, inner_w, field_h),
					_("Library name"),
					tauon.text_plex_ser,
					prefs.plex_library,
					accent,
				)

			rect = (x, y + card1_h + card_gap, w, card2_h)
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
				rect,
				_("Actions"),
				_("Import from Plex."),
				accent,
			)
			if two_factor:
				self.draw_settings_action_row(
					(inner_x, inner_y, inner_w, action_h),
					[
						(_("Continue"), tauon.plex_get_album_thread, True),
						(_("Cancel"), tauon.plex_cancel_two_factor, False),
					],
					accent,
				)
			else:
				self.draw_settings_action_row(
					(inner_x, inner_y, inner_w, action_h),
					[
						(_("Import music to playlist"), tauon.plex_get_album_thread, True),
					],
					accent,
				)
			inner_y += action_h + row_gap
			prefs.scrobble_plex = self.settings_switch_row(
				(inner_x, inner_y, inner_w, info_row_h),
				prefs.scrobble_plex,
				_("Allow local scrobbling"),
				_("Disable if Plex scrobbles on its own."),
				accent,
			)
			return total_h

		if view == 7:
			card1_h = round(218 * gui.scale)
			card2_h = round(212 * gui.scale)
			total_h = card1_h + card_gap + card2_h
			if not draw:
				return total_h

			rect = (x, y, w, card1_h)
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
				rect,
				_("Airsonic / Subsonic"),
				_("Connect to a Subsonic-compatible server."),
				accent,
			)
			prefs.subsonic_user = self.settings_text_input(
				(inner_x, inner_y, inner_w, field_h),
				_("Username / Email"),
				tauon.text_air_usr,
				prefs.subsonic_user,
				accent,
			)
			inner_y += field_h + row_gap
			prefs.subsonic_password = self.settings_text_input(
				(inner_x, inner_y, inner_w, field_h),
				_("Password"),
				tauon.text_air_pas,
				prefs.subsonic_password,
				accent,
				secret=True,
			)
			inner_y += field_h + row_gap
			prefs.subsonic_server = self.settings_text_input(
				(inner_x, inner_y, inner_w, field_h),
				_("Server URL"),
				tauon.text_air_ser,
				prefs.subsonic_server,
				accent,
			)

			rect = (x, y + card1_h + card_gap, w, card2_h)
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
				rect,
				_("Options"),
				_("Import and authentication settings."),
				accent,
			)
			prefs.subsonic_password_plain = self.settings_switch_row(
				(inner_x, inner_y, inner_w, info_row_h),
				prefs.subsonic_password_plain,
				_("Use plain text authentication"),
				_("Needed for Nextcloud Music."),
				accent,
			)
			inner_y += info_row_h + row_gap
			prefs.scrobble_subsonic = self.settings_switch_row(
				(inner_x, inner_y, inner_w, info_row_h),
				prefs.scrobble_subsonic,
				_("Allow local scrobbling"),
				_("Disable if your server scrobbles on its own."),
				accent,
			)
			inner_y += info_row_h + row_gap
			self.draw_settings_action_row(
				(inner_x, inner_y, inner_w, action_h),
				[
					(_("Import music to playlist"), tauon.sub_get_album_thread, True),
				],
				accent,
			)
			return total_h

		if view == 9:
			card1_h = round(158 * gui.scale)
			card2_h = round(170 * gui.scale)
			card3_h = round(158 * gui.scale)
			total_h = card1_h + card_gap + card2_h + card_gap + card3_h
			if not draw:
				return total_h

			def test_maloja() -> None:
				if not prefs.maloja_url or not prefs.maloja_key:
					self.show_message(_("One or more fields are missing."))
					return
				url = prefs.maloja_url
				if not url.endswith("/mlj_1"):
					if not url.endswith("/"):
						url += "/"
					url += "apis/mlj_1"
				url += "/test"
				try:
					result = requests.get(url, params={"key": prefs.maloja_key}, timeout=10)
					if result.status_code == 403:
						self.show_message(_("Connection looked successful but the API key was invalid."), mode="warning")
					elif result.status_code == 200:
						self.show_message(_("Connection to Maloja server was successful."), mode="done")
					else:
						self.show_message(_("The Maloja server returned an error."), result.text, mode="warning")
				except Exception:
					logging.exception("Could not communicate with the Maloja server")
					self.show_message(_("Could not communicate with the Maloja server."), mode="warning")

			rect = (x, y, w, card1_h)
			status_text = prefs.maloja_url or _("No server configured.")
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
				rect,
				"Maloja",
				_("Self-hosted scrobble server."),
				accent,
			)
			self.settings_switch_row(
				(inner_x, inner_y, inner_w, info_row_h),
				self.tauon.toggle_maloja,
				_("Enable scrobbling"),
				status_text,
				accent,
			)
			inner_y += info_row_h + row_gap
			self.settings_switch_row(
				(inner_x, inner_y, inner_w, row_h),
				self.tauon.toggle_scrobble_mark,
				_("Show threshold marker"),
				accent=accent,
			)

			card_y = y + card1_h + card_gap
			rect = (x, card_y, w, card2_h)
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
				rect,
				_("Credentials"),
				_("Server address and API key."),
				accent,
			)
			prefs.maloja_url = self.settings_text_input(
				(inner_x, inner_y, inner_w, field_h),
				_("Server URL"),
				tauon.text_maloja_url,
				prefs.maloja_url,
				accent,
			).strip()
			inner_y += field_h + row_gap
			prefs.maloja_key = self.settings_text_input(
				(inner_x, inner_y, inner_w, field_h),
				_("API key"),
				tauon.text_maloja_key,
				prefs.maloja_key,
				accent,
				secret=True,
			).strip()

			card_y += card2_h + card_gap
			rect = (x, card_y, w, card3_h)
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
				rect,
				_("Actions"),
				_("Connectivity and library import."),
				accent,
			)
			self.draw_settings_action_row(
				(inner_x, inner_y, inner_w, action_h),
				[
					(_("About Maloja"), lambda: webbrowser.open("https://github.com/krateng/maloja", new=2, autoraise=True), False),
					(_("Test connectivity"), test_maloja, True),
				],
				accent,
			)
			inner_y += action_h + row_gap
			self.draw_settings_action_row(
				(inner_x, inner_y, inner_w, action_h),
				[
					(_("Get scrobble counts"), lambda: shooter(tauon.maloja_get_scrobble_counts), True),
					(_("Clear counts"), self.clear_scrobble_counts, False),
				],
				accent,
			)
			return total_h

		if view == 10:
			card1_h = round(266 * gui.scale)
			card2_h = round(158 * gui.scale)
			total_h = card1_h + card_gap + card2_h
			if not draw:
				return total_h

			def import_jelly_playlists() -> None:
				found = False
				for value in self.pctl.gen_codes.values():
					if value.startswith("jelly"):
						found = True
						break
				if not found:
					self.show_message(_("Run music import first"))
				else:
					tauon.jellyfin_get_playlists_thread()

			rect = (x, y, w, card1_h)
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
				rect,
				"Jellyfin",
				_("Connect to a Jellyfin server."),
				accent,
			)
			prefs.jelly_username = self.settings_text_input(
				(inner_x, inner_y, inner_w, field_h),
				_("Username"),
				tauon.text_jelly_usr,
				prefs.jelly_username,
				accent,
			)
			inner_y += field_h + row_gap
			prefs.jelly_password = self.settings_text_input(
				(inner_x, inner_y, inner_w, field_h),
				_("Password"),
				tauon.text_jelly_pas,
				prefs.jelly_password,
				accent,
				secret=True,
			)
			inner_y += field_h + row_gap
			prefs.jelly_server_url = self.settings_text_input(
				(inner_x, inner_y, inner_w, field_h),
				_("Server URL"),
				tauon.text_jelly_ser,
				prefs.jelly_server_url,
				accent,
			)
			inner_y += field_h + row_gap
			prefs.scrobble_jellyfin = self.settings_switch_row(
				(inner_x, inner_y, inner_w, info_row_h),
				prefs.scrobble_jellyfin,
				_("Allow local scrobbling"),
				_("Disable if Jellyfin scrobbles on its own."),
				accent,
			)

			rect = (x, y + card1_h + card_gap, w, card2_h)
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
				rect,
				_("Actions"),
				_("Import music and playlists."),
				accent,
			)
			self.draw_settings_action_row(
				(inner_x, inner_y, inner_w, action_h),
				[
					(_("Import music"), tauon.jellyfin_get_library_thread, True),
					(_("Import playlists"), import_jelly_playlists, False),
				],
				accent,
			)
			inner_y += action_h + row_gap
			self.draw_settings_action_row(
				(inner_x, inner_y, inner_w, action_h),
				[
					(_("Test connectivity"), tauon.jellyfin.test, False),
				],
				accent,
			)
			return total_h

		if view == 11:
			card1_h = round(170 * gui.scale)
			card2_h = round(116 * gui.scale)
			total_h = card1_h + card_gap + card2_h
			if not draw:
				return total_h

			rect = (x, y, w, card1_h)
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
				rect,
				"Tauon",
				_("Fetch a playlist from another Tauon instance."),
				accent,
			)
			prefs.sat_url = self.settings_text_input(
				(inner_x, inner_y, inner_w, field_h),
				_("IP"),
				tauon.text_sat_url,
				prefs.sat_url,
				accent,
			).strip()
			inner_y += field_h + row_gap
			playlist_name = self.settings_text_input(
				(inner_x, inner_y, inner_w, field_h),
				_("Playlist name"),
				tauon.text_sat_playlist,
				tauon.text_sat_playlist.text,
				accent,
			)
			tauon.text_sat_playlist.text = playlist_name

			def load_remote_playlist() -> None:
				if tauon.tau.processing:
					self.show_message(_("An operation is already running"))
				else:
					shooter(tauon.tau.get_playlist)

			rect = (x, y + card1_h + card_gap, w, card2_h)
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
				rect,
				_("Actions"),
				_("Fetch the named playlist."),
				accent,
			)
			self.draw_settings_action_row(
				(inner_x, inner_y, inner_w, action_h),
				[
					(_("Get playlist"), load_remote_playlist, True),
				],
				accent,
			)
			return total_h

		if view == 12:
			logged_in = os.path.isfile(tauon.tidal.save_path)
			waiting_for_redirect = tauon.tidal.login_stage != 0 and not logged_in
			card1_h = round(224 * gui.scale) if waiting_for_redirect else round(216 * gui.scale)
			card2_h = round(116 * gui.scale) if logged_in else 0
			total_h = card1_h + (card_gap + card2_h if card2_h else 0)
			if not draw:
				return total_h

			def paste_tidal_redirect() -> None:
				text = copy_from_clipboard()
				if text:
					tauon.tidal.login2(text)

			rect = (x, y, w, card1_h)
			subtitle = _("Signed in.") if logged_in else (_("Waiting for redirect.") if waiting_for_redirect else _("Not connected."))
			inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
				rect,
				"TIDAL",
				_("Authorise TIDAL and import favourites."),
				accent,
			)
			self.draw_settings_note((inner_x, inner_y, inner_w, note_h), subtitle, accent, _("Status"))
			inner_y += note_h + row_gap
			if logged_in:
				self.draw_settings_action_row(
					(inner_x, inner_y, inner_w, action_h),
					[
						(_("Logout"), tauon.tidal.logout, True),
					],
					accent,
				)
				inner_y += action_h + row_gap
				prefs.scrobble_tidal = self.settings_switch_row(
					(inner_x, inner_y, inner_w, info_row_h),
					prefs.scrobble_tidal,
					_("Allow local scrobbling"),
					_("Disable if TIDAL scrobbles on its own."),
					accent,
				)
			elif waiting_for_redirect:
				self.draw_settings_note(
					(inner_x, inner_y, inner_w, note_h),
					_("Copy the full URL of the resulting page, then paste it here."),
					accent,
					_("Redirect"),
				)
				inner_y += note_h + row_gap
				self.draw_settings_action_row(
					(inner_x, inner_y, inner_w, action_h),
					[
						(_("Paste redirect URL"), paste_tidal_redirect, True),
					],
					accent,
				)
			else:
				self.draw_settings_action_row(
					(inner_x, inner_y, inner_w, action_h),
					[
						(_("Login"), tauon.tidal.login1, True),
					],
					accent,
				)

			if logged_in:
				rect = (x, y + card1_h + card_gap, w, card2_h)
				inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
					rect,
					_("Imports"),
					_("Pull favourites into Tauon."),
					accent,
				)
				self.draw_settings_action_row(
					(inner_x, inner_y, inner_w, action_h),
					[
						(_("Import albums"), lambda: shooter(tauon.tidal.fav_albums), True),
						(_("Import tracks"), lambda: shooter(tauon.tidal.fav_tracks), False),
					],
					accent,
				)
			return total_h

		card1_h = round(164 * gui.scale)
		card2_h = round(104 * gui.scale)
		total_h = card1_h + card_gap + card2_h
		if not draw:
			return total_h

		rect = (x, y, w, card1_h)
		inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
			rect,
			_("Service"),
			_("No layout available."),
			accent,
		)
		self.draw_settings_note((inner_x, inner_y, inner_w, note_h), _("This service view is not available right now."), accent)
		rect = (x, y + card1_h + card_gap, w, card2_h)
		inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(rect, _("Actions"), "", accent)
		self.draw_settings_action_row((inner_x, inner_y, inner_w, action_h), [(_("Back to Last.fm"), lambda: self.select_account_view(1), True)], accent)
		return total_h

	def render_settings_services_category(self, x: int, y: int, w: int, accent: ColourRGBA, draw: bool = True) -> int:
		gui = self.gui
		column_gap = round(12 * gui.scale)
		left_w = max(round(250 * gui.scale), min(round(w * 0.34), w - round(320 * gui.scale)))
		right_w = w - left_w - column_gap
		scrobbling, streaming = self.settings_account_services()
		valid_views = {view for view, title, subtitle in scrobbling + streaming}
		if self.account_view not in valid_views:
			self.account_view = 1

		tile_h = round(34 * gui.scale)
		tile_gap = round(8 * gui.scale)
		group_gap = round(12 * gui.scale)
		scrobble_rows = max(1, len(scrobbling))
		stream_rows = max(1, len(streaming))
		nav_h = (
			round(122 * gui.scale)
			+ scrobble_rows * tile_h
			+ max(0, scrobble_rows - 1) * tile_gap
			+ group_gap
			+ round(18 * gui.scale)
			+ stream_rows * tile_h
			+ max(0, stream_rows - 1) * tile_gap
		)
		detail_h = self.render_settings_service_detail(self.account_view, x + left_w + column_gap, y, right_w, accent, draw=False)
		body_h = max(nav_h, detail_h)
		if not draw:
			return body_h

		left_rect = (x, y, left_w, body_h)
		inner_x, inner_y, inner_w, inner_h = self.draw_settings_section(
			left_rect,
			_("Accounts"),
			_("Pick a service to configure."),
			accent,
		)
		tile_w = inner_w

		for heading, items in (
			(_("Scrobbling"), scrobbling),
			(_("Streaming"), streaming),
		):
			self.ddt.text((inner_x, inner_y), heading, self.colours.box_text_label, 11)
			inner_y += round(16 * gui.scale)
			for view, title, subtitle_text in items:
				self.settings_switcher_tile(
					(inner_x, inner_y, tile_w, tile_h),
					title,
					self.account_view == view,
					callback=lambda view=view: self.select_account_view(view),
					accent=accent,
				)
				inner_y += tile_h + tile_gap
			inner_y += group_gap - tile_gap

		self.render_settings_service_detail(self.account_view, x + left_w + column_gap, y, right_w, accent, draw=True)
		return body_h

	def render_settings_stats_category(self, x: int, y: int, w: int, accent: ColourRGBA, draw: bool = True) -> int:
		gui = self.gui
		pctl = self.pctl
		colours = self.colours
		strings = self.tauon.strings
		column_gap = round(12 * gui.scale)
		row1_h = round(154 * gui.scale)
		row2_h = round(109 * gui.scale)
		row3_h = round(364 * gui.scale) if self.prefs.chart_cascade else round(334 * gui.scale)
		if self.stats_pl != pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int or self.stats_pl_timer.get() > 5:
			self.stats_pl = pctl.multi_playlist[pctl.active_playlist_viewing].uuid_int
			self.stats_pl_timer.set()

			album_names = set()
			folder_names = set()
			count = 0

			for track_id in pctl.default_playlist:
				tr = pctl.get_track(track_id)
				if not tr.album:
					if tr.parent_folder_path not in folder_names:
						count += 1
					folder_names.add(tr.parent_folder_path)
				else:
					if tr.parent_folder_path not in folder_names and tr.album not in album_names:
						count += 1
					folder_names.add(tr.parent_folder_path)
					album_names.add(tr.album)

			self.stats_pl_albums = count
			self.stats_pl_length = 0
			for item in pctl.default_playlist:
				self.stats_pl_length += pctl.master_library[item].length

		if self.stats_timer.get() > 5:
			album_names = set()
			folder_names = set()
			count = 0
			for pl in pctl.multi_playlist:
				for track_id in pl.playlist_ids:
					tr = pctl.get_track(track_id)
					if not tr.album:
						if tr.parent_folder_path not in folder_names:
							count += 1
						folder_names.add(tr.parent_folder_path)
					else:
						if tr.parent_folder_path not in folder_names and tr.album not in album_names:
							count += 1
						folder_names.add(tr.parent_folder_path)
						album_names.add(tr.album)
			self.total_albums = count
			self.stats_timer.set()

		if not draw:
			return row1_h + row2_h + row3_h + column_gap * 2

		left_w = max(round(260 * gui.scale), min(round(w * 0.48), w - round(220 * gui.scale)))
		right_w = w - left_w - column_gap
		left_rect = (x, y, left_w, row1_h)
		right_rect = (x + left_w + column_gap, y, right_w, row1_h)
		line_gap = round(20 * gui.scale)

		inner_x, inner_y, inner_w, section_h = self.draw_settings_section(
			left_rect,
			_("Current playlist"),
			self.pctl.multi_playlist[self.pctl.active_playlist_viewing].title,
			accent,
		)
		line = seconds_to_day_hms(self.stats_pl_length, strings.day, strings.days)
		for label, value in (
			(_("Tracks"), py_locale.format_string("%d", len(pctl.default_playlist), True)),
			(_("Albums"), str(self.stats_pl_albums)),
			(_("Duration"), line),
		):
			self.ddt.text((inner_x, inner_y), label, colours.box_text_label, 12)
			self.ddt.text((inner_x + inner_w, inner_y, 1), value, colours.box_sub_text, 12)
			inner_y += line_gap

		inner_x, inner_y, inner_w, section_h = self.draw_settings_section(
			right_rect,
			_("Library"),
			_("Totals across the database."),
			accent,
		)
		for label, value in (
			(_("Tracks"), py_locale.format_string("%d", len(pctl.master_library), True)),
			(_("Albums"), str(self.total_albums)),
			(_("Playtime"), seconds_to_day_hms(pctl.total_playtime, strings.day, strings.days)),
		):
			self.ddt.text((inner_x, inner_y), label, colours.box_text_label, 12)
			self.ddt.text((inner_x + inner_w, inner_y, 1), value, colours.box_sub_text, 12)
			inner_y += line_gap

		row2_y = y + row1_h + column_gap
		format_rect = (x, row2_y, w, row2_h)
		inner_x, inner_y, inner_w, section_h = self.draw_settings_section(
			format_rect,
			_("File formats"),
			_("Click a segment to build a playlist for that format."),
			accent,
		)
		if pctl.master_library:
			try:
				if self.last_db_size != len(pctl.master_library):
					self.last_db_size = len(pctl.master_library)
					self.ext_ratio = {}
					for key, value in pctl.master_library.items():
						if value.file_ext in self.ext_ratio:
							self.ext_ratio[value.file_ext] += 1
						else:
							self.ext_ratio[value.file_ext] = 1

				bar_rect = (inner_x, inner_y + round(8 * gui.scale), inner_w, round(14 * gui.scale))
				self.ddt.bordered_rect(
					bar_rect,
					alpha_blend(ColourRGBA(255, 255, 255, 10), colours.box_background),
					alpha_blend(ColourRGBA(255, 255, 255, 18), colours.box_text_border),
					round(1 * gui.scale),
				)
				d = 0
				for key, value in self.ext_ratio.items():
					colour = ColourRGBA(200, 200, 200, 255)
					if key in self.formats.colours:
						colour = self.formats.colours[key]
					colour_hls = colorsys.rgb_to_hls(colour.r / 255, colour.g / 255, colour.b / 255)
					colour_rgb = colorsys.hls_to_rgb(1 - colour_hls[0], colour_hls[1] * 0.8, colour_hls[2] * 0.8)
					colour = ColourRGBA(int(colour_rgb[0] * 255), int(colour_rgb[1] * 255), int(colour_rgb[2] * 255), 255)
					block_w = round(value / len(pctl.master_library) * bar_rect[2])
					if block_w <= 0:
						continue
					block_rect = (bar_rect[0] + d, bar_rect[1], max(block_w - 1, 1), bar_rect[3])
					self.ddt.rect(block_rect, colour)
					self.fields.add(block_rect)
					if self.coll(block_rect):
						self.ddt.text((block_rect[0] + block_rect[2] // 2, bar_rect[1] - round(18 * gui.scale), 2), key, colours.grey_blend_bg(220), 13)
						if self.click:
							self.tauon.gen_codec_pl(key)
					d += block_w
			except Exception:
				logging.exception("Error draw ext bar")

		row3_y = row2_y + row2_h + column_gap
		self.topchart(x, row3_y, w, row3_h, show_return=False, accent=accent)
		return row1_h + row2_h + row3_h + column_gap * 2

	def render_settings_about_category(self, x: int, y: int, w: int, accent: ColourRGBA, draw: bool = True) -> int:
		gui = self.gui
		column_gap = round(12 * gui.scale)
		left_h = round(224 * gui.scale)
		right_h = left_h
		row_h = max(left_h, right_h)
		if not draw:
			return row_h

		left_w = max(round(260 * gui.scale), min(round(w * 0.46), w - round(220 * gui.scale)))
		right_w = w - left_w - column_gap
		left_rect = (x, y, left_w, left_h)
		right_rect = (x + left_w + column_gap, y, right_w, right_h)
		inner_x, inner_y, inner_w, section_h = self.draw_settings_section(
			left_rect,
			_("Tauon"),
			self.t_version,
			accent,
		)
		action_h = round(34 * gui.scale)
		action_gap = round(8 * gui.scale)
		icon_x = left_rect[0] + left_rect[2] - round(16 * gui.scale) - round(self.app_icon.w)
		icon_y = left_rect[1] + round(10 * gui.scale)
		self.app_icon.render(icon_x, icon_y)
		copyright_h = self.ddt.text(
			(inner_x, inner_y, 4, inner_w, round(40 * gui.scale)),
			"Copyright © 2015-2026 Taiko2k",
			self.colours.box_sub_text,
			13,
		) or round(18 * gui.scale)
		inner_y += max(copyright_h + round(6 * gui.scale), round(24 * gui.scale))
		self.ddt.text((inner_x, inner_y, 4, inner_w, round(44 * gui.scale)), _("This program comes with absolutely no warranty."), self.colours.box_text_label, 11)
		button_y = left_rect[1] + left_rect[3] - round(14 * gui.scale) - action_h * 2 - action_gap
		self.settings_action_tile((inner_x, button_y, inner_w, action_h), _("Open website"), lambda: webbrowser.open("https://tauonmusicbox.rocks", new=2, autoraise=True), accent)
		button_y += action_h + action_gap
		self.settings_action_tile((inner_x, button_y, inner_w, action_h), _("Open GPL license"), lambda: webbrowser.open("https://www.gnu.org/licenses/gpl-3.0.html", new=2, autoraise=True), accent)

		inner_x, inner_y, inner_w, section_h = self.draw_settings_section(
			right_rect,
			_("Credits"),
			_("People and project links."),
			accent,
		)
		self.ddt.text((inner_x, inner_y), _("Created by"), self.colours.box_text_label, 12)
		self.ddt.text((inner_x + round(75 * gui.scale), inner_y), "Taiko2k", self.colours.box_sub_text, 13)
		inner_y += round(28 * gui.scale)
		self.settings_action_tile((inner_x, inner_y, inner_w, action_h), _("Contributors"), lambda: webbrowser.open("https://github.com/Taiko2k/Tauon/graphs/contributors", new=2, autoraise=True), accent)
		inner_y += round(40 * gui.scale)
		self.settings_action_tile((inner_x, inner_y, inner_w, action_h), _("Source code"), lambda: webbrowser.open("https://github.com/Taiko2k/Tauon", new=2, autoraise=True), accent)
		return row_h

	def draw_settings_category_heading(self, title: str, x: int, y: int, w: int) -> int:
		heading_h = round(34 * self.gui.scale)
		text_y = y + round(4 * self.gui.scale)
		line_y = y + round(14 * self.gui.scale)
		gap = round(14 * self.gui.scale)
		min_line_w = round(28 * self.gui.scale)
		text_w = min(self.ddt.get_text_w(title, 213), max(0, w - (gap + min_line_w) * 2))
		line_colour = self.colours.box_text_border
		center_x = x + w // 2
		left_line_w = max(0, center_x - x - text_w // 2 - gap)
		right_line_x = center_x + text_w // 2 + gap
		right_line_w = max(0, x + w - right_line_x)
		line_h = max(1, round(1 * self.gui.scale))
		if left_line_w:
			self.ddt.rect((x, line_y, left_line_w, line_h), line_colour)
		if right_line_w:
			self.ddt.rect((right_line_x, line_y, right_line_w, line_h), line_colour)
		self.ddt.text((center_x, text_y, 2), title, self.colours.box_text, 213, bg=self.colours.box_background, max_w=text_w)
		return heading_h

	def render_settings_category(self, index: int, x: int, y: int, w: int, draw: bool = True) -> int:
		self.settings_accent_bar_pending = True
		accent = self.settings_tab_accent(index)
		heading_h = round(34 * self.gui.scale)
		if draw and index < len(self.tabs):
			heading_h = self.draw_settings_category_heading(self.tabs[index], x, y, w)
		body_y = y + heading_h

		if index == 0:
			body_h = self.render_settings_general_category(x, body_y, w, draw)
		elif index == 1:
			body_h = self.render_settings_connections_category(x, body_y, w, accent, draw)
		elif index == 2:
			body_h = self.render_settings_audio_category(x, body_y, w, accent, draw)
		elif index == 3:
			body_h = self.render_settings_theme_category(x, body_y, w, accent, draw)
		elif index == 4:
			body_h = self.render_settings_view_category(x, body_y, w, accent, draw)
		elif index == 5:
			body_h = self.render_settings_transcode_category(x, body_y, w, accent, draw)
		elif index == 6:
			body_h = self.render_settings_services_category(x, body_y, w, accent, draw)
		elif index == 7:
			body_h = self.render_settings_func_category(4, x, body_y, w, draw)
		elif index == 8:
			body_h = self.render_settings_stats_category(x, body_y, w, accent, draw)
		else:
			body_h = self.render_settings_about_category(x, body_y, w, accent, draw)

		return heading_h + body_h

	# def style_up(self) -> None:
	# 	self.prefs.line_style += 1
	# 	if self.prefs.line_style > 5:
	# 		self.prefs.line_style = 1

	def inside(self) -> bool:
		return self.coll((self.box_x, self.box_y, self.w, self.h))

	def init2(self) -> None:
		self.init2done = True

	def close(self) -> None:
		self.enabled = False
		self.clear_theme_editor_state()
		self.tauon.smooth_scroll.reset_motion("settings nav")
		self.tauon.smooth_scroll.reset_motion("settings content")
		self.settings_scale_preview_value = None
		self.settings_text_focus = None
		self.settings_text_order = []
		self.settings_text_seen = []
		self.settings_text_hit = False
		self.destroy_settings_texture()
		self.tauon.fader.fall()
		if self.gui.opened_config_file:
			self.tauon.reload_config_file()

	def theme_editor_component_colour(self, name: str, fallback: ColourRGBA) -> ColourRGBA:
		"""Helper to either pull a colour from the draft ColoursClass instance or a fallback

		This is needed as some colours can be set to None which is annoying to catch
		"""
		if self.theme_editor_draft_colours is None:
			return fallback

		colour = getattr(self.theme_editor_draft_colours, name, None)
		return colour if isinstance(colour, ColourRGBA) else fallback

	def render_theme_editor_window(self) -> None:
		gui = self.gui
		ddt = self.ddt
		colours = self.colours
		current_colour = self.theme_editor_current_colour()
		hue = self.theme_editor_hue_value
		sat = self.theme_editor_sat_value
		val = self.theme_editor_val_value

		full_width = round(510 * gui.scale)
		full_height = round(375 * gui.scale)
		if self.theme_editor_window_position is None:
			x = int(self.window_size[0] / 2) - int(full_width / 2)
			y = int(self.window_size[1] / 2) - int(full_height / 2)
		else:
			x, y = self.theme_editor_window_position
		if self.theme_editor_drag_target == "window" and self.inp.mouse_down:
			x = (
				self.theme_editor_window_drag_start_position[0]
				+ self.inp.mouse_position[0]
				- self.theme_editor_window_drag_start_mouse[0]
			)
			y = (
				self.theme_editor_window_drag_start_position[1]
				+ self.inp.mouse_position[1]
				- self.theme_editor_window_drag_start_mouse[1]
			)
			self.tauon.input_sdl.mouse_capture_want = True
			gui.request_frame()
		margin = round(8 * gui.scale)
		x = min(max(x, margin), max(margin, self.window_size[0] - round(full_width * 0.5)))
		y = min(max(y, margin), max(margin, self.window_size[1] - round(full_height * 0.5)))
		self.theme_editor_window_position = (x, y)
		self.box_x = x
		self.box_y = y
		self.w = full_width
		self.h = full_height

		ddt.rect(
			(x - 5 * gui.scale, y - 5 * gui.scale, full_width + 10 * gui.scale, full_height + 10 * gui.scale),
			colours.box_border,
		)
		ddt.rect_a((x, y), (full_width, full_height), colours.box_background)
		ddt.text_background_colour = colours.box_background

		self.begin_settings_text_inputs()

		pad = round(12 * gui.scale)
		column_gap = round(10 * gui.scale)
		row_gap = round(6 * gui.scale)
		header_h = round(72 * gui.scale)
		left_w = round(full_width * 0.42)
		right_w = full_width - left_w - column_gap - pad * 2
		left_x = x + pad
		right_x = left_x + left_w + column_gap
		header_y = y + pad

		grip_w = round(23 * gui.scale)
		grip_gap = round(7 * gui.scale)
		grip_rect = (left_x, header_y + round(17 * gui.scale), grip_w, round(22 * gui.scale))
		title_field_x = left_x + grip_w + grip_gap
		title_field_w = full_width - pad * 2 - round(190 * gui.scale) - grip_w - grip_gap
		self.ddt.text((title_field_x, header_y), _("Theme title"), colours.box_text_label, 11, bg=colours.box_background)
		grip_hover = self.coll(grip_rect)
		self.fields.add(grip_rect)
		grip_dot = max(2, round(2 * gui.scale))
		grip_colour = colours.box_text if self.theme_editor_drag_target == "window" else colours.box_text_label
		for offset_x in (round(4 * gui.scale), round(10 * gui.scale), round(16 * gui.scale)):
			for offset_y in (round(5 * gui.scale), round(10 * gui.scale), round(15 * gui.scale)):
				ddt.rect((grip_rect[0] + offset_x, grip_rect[1] + offset_y, grip_dot, grip_dot), grip_colour)
		if self.click and grip_hover:
			self.theme_editor_drag_target = "window"
			self.theme_editor_window_drag_start_mouse = tuple(self.inp.mouse_position)
			self.theme_editor_window_drag_start_position = (x, y)
			self.tauon.input_sdl.mouse_capture_want = True
		self.draw_settings_text_field(
			(title_field_x, header_y + round(17 * gui.scale), title_field_w, round(22 * gui.scale)),
			self.theme_editor_title_box,
			self.settings_page_accent(4),
			stored_value=self.theme_editor_title_box.text,
			placeholder=_("Theme title"),
		)
		if self.theme_editor_dirty:
			self.ddt.text(
				(title_field_x, header_y + round(42 * gui.scale)),
				_("Unsaved changes!"),
				colours.box_text_label,
				11,
				bg=colours.box_background,
			)

		button_w = round(78 * gui.scale)
		button_h = round(30 * gui.scale)
		close_x = x + full_width - pad - button_w
		save_x = close_x - column_gap - button_w
		self.settings_action_tile((save_x, header_y + round(12 * gui.scale), button_w, button_h), _("Save"), self.save_active_user_theme, self.settings_page_accent(4), emphasis=True)
		self.settings_action_tile((close_x, header_y + round(12 * gui.scale), button_w, button_h), _("Close"), self.close_theme_editor, self.settings_page_accent(4))

		panel_y = y + header_h
		panel_h = full_height - header_h - pad
		left_rect = (left_x, panel_y, left_w, panel_h)
		right_rect = (right_x, panel_y, right_w, panel_h)
		panel_fill = alpha_blend(ColourRGBA(255, 255, 255, 6), colours.box_background)
		panel_border = alpha_blend(ColourRGBA(255, 255, 255, 18), colours.box_text_border)
		ddt.bordered_rect(left_rect, panel_fill, panel_border, round(1 * gui.scale))
		ddt.bordered_rect(right_rect, panel_fill, panel_border, round(1 * gui.scale))

		left_inner_x = left_rect[0] + pad
		left_inner_y = left_rect[1] + pad
		left_inner_w = left_rect[2] - pad * 2
		left_inner_h = left_rect[3] - pad * 2
		ddt.text((left_inner_x, left_inner_y - round(3 * gui.scale)), _("Components"), colours.box_text, 12, bg=panel_fill)
		list_y = left_inner_y + round(16 * gui.scale)
		row_h = round(26 * gui.scale)
		row_step = row_h + row_gap
		list_rect = (left_inner_x, list_y, left_inner_w, left_inner_h - round(10 * gui.scale))
		visible_rows = max(1, int((list_rect[3] + row_gap) // max(row_step, 1)))
		max_scroll = max(len(THEME_EDITOR_COMPONENTS) - visible_rows, 0)
		if self.coll(left_rect) and self.scroll:
			self.theme_editor_list_scroll -= self.scroll
		self.theme_editor_list_scroll = min(max(self.theme_editor_list_scroll, 0), max_scroll)
		scroll_index = int(self.theme_editor_list_scroll)
		scrollbar_w = round(10 * gui.scale)
		scrollbar_gap = round(8 * gui.scale)
		row_w = list_rect[2]
		if max_scroll > 0:
			row_w -= scrollbar_w + scrollbar_gap
			self.theme_editor_list_scroll = self.theme_editor_list_scroll_bar.draw(
				list_rect[0] + list_rect[2] - scrollbar_w,
				list_rect[1],
				scrollbar_w,
				list_rect[3],
				self.theme_editor_list_scroll,
				max_scroll,
				click=self.click,
				extend_field=round(4 * gui.scale),
			)
			scroll_index = int(self.theme_editor_list_scroll)

		rows_count = 0
		row_y = list_rect[1]
		for label, attr in THEME_EDITOR_COMPONENTS[scroll_index : scroll_index + visible_rows]:
			rows_count += 1
			if rows_count > visible_rows:
				break
			row_rect = (list_rect[0], row_y, row_w, row_h)
			hover = self.coll(row_rect)
			active = self.theme_editor_selected_attrs == attr
			row_fill = alpha_blend(ColourRGBA(255, 255, 255, 4), panel_fill)
			if active:
				row_fill = alpha_blend(alpha_mod(self.settings_page_accent(4), 24), row_fill)
			elif hover:
				row_fill = alpha_blend(ColourRGBA(255, 255, 255, 8), row_fill)
			row_border = alpha_blend(ColourRGBA(255, 255, 255, 18), panel_border)
			if active:
				row_border = alpha_blend(alpha_mod(self.settings_page_accent(4), 90), row_border)
			ddt.bordered_rect(row_rect, row_fill, row_border, round(1 * gui.scale))
			self.fields.add(row_rect)

			subcolors_are_identical = True
			if len(attr) > 1: # THEME_EDITOR_COMPONENTS is currently set up for a STATIC visible_rows value. if this value ever changes, get smarter.
				compare_color = self.theme_editor_component_colour(attr[0], current_colour)
				for color in attr:
					component_colour = self.theme_editor_component_colour(color, current_colour)
					subcolors_are_identical = subcolors_are_identical and component_colour == compare_color
					compare_color = component_colour

				dropdown_rect = (list_rect[0] + row_w - row_h, row_y, row_h, row_h)
				# ddt.bordered_rect(dropdown_rect, row_fill, row_border, round(1 * gui.scale))
				ddt.text(
					(dropdown_rect[0]+ round(10*gui.scale),dropdown_rect[1]+round(4*gui.scale)),
					"🞃" if self.theme_editor_dropdown_expansions[THEME_EDITOR_COMPONENTS.index((label,attr))] else "🞂",
					colours.box_button_text, 12, bg=row_fill
					)
				if self.coll(dropdown_rect) and self.click:
					self.theme_editor_dropdown_expansions[THEME_EDITOR_COMPONENTS.index((label,attr))] = not self.theme_editor_dropdown_expansions[THEME_EDITOR_COMPONENTS.index((label,attr))]
				dropped_down = self.theme_editor_dropdown_expansions[THEME_EDITOR_COMPONENTS.index((label,attr))]
				if dropped_down:

					for color in attr:
						row_y += row_step
						rows_count += 1
						if rows_count > visible_rows:
							break

						sub_rect = (list_rect[0] + round(10*gui.scale), row_y, row_w - round(10*gui.scale), row_h)
						subhover = self.coll(sub_rect)
						subactive = self.theme_editor_selected_attrs == color
						subrow_fill = alpha_blend(ColourRGBA(255, 255, 255, 4), panel_fill)
						if subactive:
							subrow_fill = alpha_blend(alpha_mod(self.settings_page_accent(4), 24), row_fill)
						elif subhover:
							subrow_fill = alpha_blend(ColourRGBA(255, 255, 255, 8), row_fill)
						subrow_border = alpha_blend(ColourRGBA(255, 255, 255, 18), panel_border)
						if subactive:
							subrow_border = alpha_blend(alpha_mod(self.settings_page_accent(4), 90), row_border)
						ddt.bordered_rect(sub_rect, subrow_fill, subrow_border, round(1 * gui.scale))
						self.fields.add(sub_rect)

						if subhover and self.click:
							self.theme_editor_selected_attr = color
							self.theme_editor_selected_attrs = (color,)
							self.theme_editor_drag_target = None
							self.sync_theme_editor_controls_from_current_colour()


						component_colour = self.theme_editor_component_colour(color, current_colour)
						swatch_rect = (sub_rect[0] + round(8 * gui.scale), sub_rect[1] + round(5 * gui.scale), round(14 * gui.scale), round(14 * gui.scale))
						ddt.rect(swatch_rect, component_colour)
						ddt.rect_s(swatch_rect, alpha_blend(ColourRGBA(255, 255, 255, 40), subrow_border), round(1 * gui.scale))
						ddt.text((swatch_rect[0] + swatch_rect[2] + round(8 * gui.scale), sub_rect[1] + round(4 * gui.scale)), color, colours.box_text if subactive else colours.box_button_text_highlight if subhover else colours.box_button_text, 12, bg=subrow_fill, max_w=sub_rect[2] - round(44 * gui.scale))



			if hover and self.click and ("dropdown_rect" in locals() and not self.coll(dropdown_rect)):
				self.theme_editor_selected_attr = attr[0]
				self.theme_editor_selected_attrs = attr
				self.theme_editor_drag_target = None
				self.sync_theme_editor_controls_from_current_colour()

			swatch_rect = (row_rect[0] + round(8 * gui.scale), row_rect[1] + round(5 * gui.scale), round(14 * gui.scale), round(14 * gui.scale))
			if subcolors_are_identical:
				component_colour = self.theme_editor_component_colour(attr[0], current_colour)
				ddt.rect(swatch_rect, component_colour)
				ddt.rect_s(swatch_rect, alpha_blend(ColourRGBA(255, 255, 255, 40), row_border), round(1 * gui.scale))
			else:
				ddt.text((swatch_rect[0] + round(1*gui.scale), row_rect[1] + round(7 * gui.scale)), "~", colours.box_text if active else colours.box_button_text_highlight if hover else colours.box_button_text, 20, bg=row_fill, max_w=row_rect[2] - round(44 * gui.scale))
			ddt.text((swatch_rect[0] + swatch_rect[2] + round(8 * gui.scale), row_rect[1] + round(4 * gui.scale)), _(label), colours.box_text if active else colours.box_button_text_highlight if hover else colours.box_button_text, 12, bg=row_fill, max_w=row_rect[2] - round(44 * gui.scale))
			row_y += row_step

		right_inner_x = right_rect[0] + pad
		right_inner_y = right_rect[1] + pad
		right_inner_w = right_rect[2] - pad * 2

		preview_y = right_inner_y
		button_w = round(62 * gui.scale)
		action_button_h = round(34 * gui.scale)
		preview_gap = row_gap
		preview_rect = (
			right_inner_x,
			preview_y,
			right_inner_w - button_w * 2 - preview_gap * 2,
			action_button_h,
		)
		ddt.bordered_rect(preview_rect, current_colour, panel_border, round(1 * gui.scale))
		preview_text = ColourRGBA(25, 25, 25, 255) if is_light(current_colour) else ColourRGBA(245, 245, 245, 255)
		ddt.text((preview_rect[0] + preview_rect[2] // 2, preview_rect[1] + round(8 * gui.scale), 2), self.theme_colour_to_hex(current_colour), preview_text, 212, bg=current_colour)

		button_y = preview_rect[1]
		copy_x = preview_rect[0] + preview_rect[2] + preview_gap
		paste_x = copy_x + button_w + preview_gap
		self.settings_action_tile((copy_x, button_y, button_w, action_button_h), _("Copy"), self.theme_editor_copy_colour, self.settings_page_accent(4), show_arrow=False)
		self.settings_action_tile((paste_x, button_y, button_w, action_button_h), _("Paste"), self.theme_editor_paste_colour, self.settings_page_accent(4), show_arrow=False)

		picker_top = preview_rect[1] + preview_rect[3] + round(20 * gui.scale)
		alpha_gap = round(8 * gui.scale)
		alpha_w = round(18 * gui.scale)
		hue_h = round(14 * gui.scale)
		hue_gap = round(12 * gui.scale)
		picker_area_h = right_rect[1] + right_rect[3] - pad - picker_top - round(10 * gui.scale)
		sv_available_w = right_inner_w - alpha_w - alpha_gap - round(20 * gui.scale)
		sv_available_h = picker_area_h - hue_gap - hue_h
		sv_side = max(round(150 * gui.scale), min(sv_available_w, sv_available_h))
		selector_w = sv_side + alpha_gap + alpha_w
		selector_h = sv_side + hue_gap + hue_h
		selector_x = right_inner_x + max(0, (right_inner_w - selector_w) // 2)
		selector_y = picker_top + max(0, (picker_area_h - selector_h) // 2)
		sv_rect = (selector_x, selector_y, sv_side, sv_side)
		hue_y = sv_rect[1] + sv_rect[3] + hue_gap
		hue_rect = (selector_x, hue_y, sv_rect[2], hue_h)
		display_hue = hue
		if self.theme_editor_drag_target == "hue" and self.inp.mouse_down:
			display_hue = min(max((self.inp.mouse_position[0] - hue_rect[0]) / max(hue_rect[2], 1), 0.0), 1.0)
		applied_hue = min(display_hue, 1.0 - (1.0 / max(hue_rect[2], 1)))
		display_sat = sat
		display_val = val
		if self.theme_editor_drag_target == "sv" and self.inp.mouse_down:
			display_sat = min(max((self.inp.mouse_position[0] - sv_rect[0]) / max(sv_rect[2], 1), 0.0), 1.0)
			display_val = min(max(1 - ((self.inp.mouse_position[1] - sv_rect[1]) / max(sv_rect[3], 1)), 0.0), 1.0)
		sv_texture = self.ensure_theme_editor_sv_texture(sv_rect[2], sv_rect[3], applied_hue)
		self.render_theme_editor_texture(sv_texture, sv_rect)
		ddt.rect_s(sv_rect, panel_border, round(1 * gui.scale))
		marker_x = sv_rect[0] + round(display_sat * sv_rect[2])
		marker_y = sv_rect[1] + round((1 - display_val) * sv_rect[3])
		ddt.rect((marker_x - round(4 * gui.scale), marker_y - round(4 * gui.scale), round(8 * gui.scale), round(8 * gui.scale)), preview_text)
		self.fields.add(sv_rect)
		if self.click and self.coll(sv_rect):
			self.theme_editor_drag_target = "sv"
		if self.theme_editor_drag_target == "sv" and self.inp.mouse_down:
			self.apply_theme_editor_hsv(applied_hue, display_sat, display_val)

		alpha_rect = (sv_rect[0] + sv_rect[2] + alpha_gap, sv_rect[1], alpha_w, sv_rect[3])
		checker_size = max(2, round(6 * gui.scale))
		checker_light = alpha_blend(ColourRGBA(255, 255, 255, 48), panel_fill)
		checker_dark = alpha_blend(ColourRGBA(0, 0, 0, 36), panel_fill)
		for check_y in range(alpha_rect[1], alpha_rect[1] + alpha_rect[3], checker_size):
			cell_h = min(checker_size, alpha_rect[1] + alpha_rect[3] - check_y)
			for check_x in range(alpha_rect[0], alpha_rect[0] + alpha_rect[2], checker_size):
				cell_w = min(checker_size, alpha_rect[0] + alpha_rect[2] - check_x)
				colour = checker_light if ((check_x - alpha_rect[0]) // checker_size + (check_y - alpha_rect[1]) // checker_size) % 2 == 0 else checker_dark
				ddt.rect((check_x, check_y, cell_w, cell_h), colour)
		alpha_steps = 32
		for index in range(alpha_steps):
			start_y = alpha_rect[1] + round(index * alpha_rect[3] / alpha_steps)
			end_y = alpha_rect[1] + round((index + 1) * alpha_rect[3] / alpha_steps)
			alpha_progress = index / max(alpha_steps - 1, 1)
			alpha_value = 255 - round((alpha_progress ** 2.0) * 255)
			ddt.rect((alpha_rect[0], start_y, alpha_rect[2], max(end_y - start_y, 1)), ColourRGBA(current_colour.r, current_colour.g, current_colour.b, alpha_value))
		ddt.rect_s(alpha_rect, panel_border, round(1 * gui.scale))
		alpha_marker_y = alpha_rect[1] + round((1 - self.theme_editor_alpha_value) * alpha_rect[3])
		ddt.rect((alpha_rect[0] - round(3 * gui.scale), alpha_marker_y - round(2 * gui.scale), alpha_rect[2] + round(6 * gui.scale), round(4 * gui.scale)), preview_text)
		self.fields.add(alpha_rect)
		if self.click and self.coll(alpha_rect):
			self.theme_editor_drag_target = "alpha"
		if self.theme_editor_drag_target == "alpha" and self.inp.mouse_down:
			alpha_portion = min(max((self.inp.mouse_position[1] - alpha_rect[1]) / max(alpha_rect[3], 1), 0.0), 1.0)
			self.apply_theme_editor_alpha(1 - alpha_portion)

		hue_texture = self.ensure_theme_editor_hue_texture(hue_rect[2], hue_rect[3])
		self.render_theme_editor_texture(hue_texture, hue_rect)
		ddt.rect_s(hue_rect, panel_border, round(1 * gui.scale))
		hue_marker_x = hue_rect[0] + round(display_hue * hue_rect[2])
		ddt.rect((hue_marker_x - round(2 * gui.scale), hue_rect[1] - round(3 * gui.scale), round(4 * gui.scale), hue_rect[3] + round(6 * gui.scale)), preview_text)
		self.fields.add(hue_rect)
		if self.click and self.coll(hue_rect):
			self.theme_editor_drag_target = "hue"
		if self.theme_editor_drag_target == "hue" and self.inp.mouse_down:
			self.apply_theme_editor_hsv(applied_hue, sat, val)
		if self.inp.mouse_up or not self.inp.mouse_down:
			self.theme_editor_drag_target = None
		self.finish_settings_text_inputs()
		self.click = False
		self.right_click = False

	def render(self) -> None:
		tauon   = self.tauon
		inp     = self.inp
		gui     = self.gui
		ddt     = self.ddt
		colours = self.colours
		if self.init2done is False:
			self.init2()

		if inp.key_esc_press and not self.theme_editor_enabled:
			self.close()

		if self.theme_editor_enabled:
			self.render_theme_editor_window()
			return

		full_width = round(875 * gui.scale)
		header_height = round(58 * gui.scale)
		full_height = round(440 * gui.scale) - header_height // 2
		side_width = round(150 * gui.scale)
		content_width = full_width - side_width
		content_height = full_height

		x = int(self.window_size[0] / 2) - int(full_width / 2)
		y = int(self.window_size[1] / 2) - int(full_height / 2)

		self.box_x = x
		self.box_y = y
		self.w = full_width
		self.h = full_height

		border_colour = colours.box_border
		ddt.rect(
			(x - 5 * gui.scale, y - 5 * gui.scale, full_width + 10 * gui.scale, full_height + 10 * gui.scale), border_colour)
		ddt.rect_a((x, y), (full_width, full_height), colours.box_background)

		tab_bg = colours.sys_tab_bg
		tab_hl = colours.sys_tab_hl
		tab_text = rgb_add_hls(tab_bg, 0, 0.3, -0.15)
		if is_light(tab_bg):
			h, l, s = rgb_to_hls(tab_bg.r, tab_bg.g, tab_bg.b)
			l = 0.1
			tab_text = hls_to_rgb(h, l, s)

		if self.click and gui.message_box:
			if not self.coll(tauon.message_box.get_rect()):
				gui.message_box = False
			else:
				inp.mouse_click = True
				self.click = False

		self.begin_settings_text_inputs()

		ddt.rect_a((x, y), (side_width, full_height), tab_bg)
		ddt.rect_a(
			(x + side_width - round(1 * gui.scale), y),
			(round(1 * gui.scale), full_height),
			alpha_mod(colours.box_text_border, 170))

		nav_x = x + round(10 * gui.scale)
		nav_y = y + round(14 * gui.scale)
		nav_h = full_height - round(28 * gui.scale)
		row_step = round(28 * gui.scale)
		row_height = round(26 * gui.scale)
		visible_rows = max(1, nav_h // max(row_step, 1))
		max_nav_scroll = self.sync_settings_nav_scroll((x, y, side_width, full_height), row_step, visible_rows)
		nav_w = side_width - round(12 * gui.scale)
		if max_nav_scroll > 0:
			scrollbar_w = round(10 * gui.scale)
			scrollbar_gap = round(8 * gui.scale)
			scrollbar_x = x + side_width - scrollbar_w - round(6 * gui.scale)
			nav_w -= scrollbar_w + scrollbar_gap
			self.settings_nav_scroll = self.settings_nav_scroll_bar.draw(
				scrollbar_x,
				y + round(8 * gui.scale),
				scrollbar_w,
				full_height - round(16 * gui.scale),
				self.settings_nav_scroll,
				max_nav_scroll,
				click=self.click,
				extend_field=round(4 * gui.scale))

		content_x = x + side_width
		content_y = y
		inner_pad_x = round(12 * gui.scale)
		content_top_pad = round(12 * gui.scale)
		content_bottom_pad = 0
		scrollbar_w = round(16 * gui.scale)
		scrollbar_gap = round(8 * gui.scale)
		scrollbar_right_inset = 0
		view_rect = (
			content_x + inner_pad_x,
			content_y,
			content_width - inner_pad_x * 2,
			content_height - content_bottom_pad,
		)
		scrollbar_x = content_x + content_width - scrollbar_right_inset - scrollbar_w
		doc_w = scrollbar_x - scrollbar_gap - view_rect[0]
		if doc_w < round(260 * gui.scale):
			doc_w = view_rect[2]

		self.settings_category_offsets = []
		category_heights: list[int] = []
		doc_height = content_top_pad
		category_gap = round(14 * gui.scale)
		for index in range(len(self.tabs)):
			self.settings_category_offsets.append(doc_height - content_top_pad)
			category_h = self.render_settings_category(index, view_rect[0], view_rect[1], doc_w, draw=False)
			category_heights.append(category_h)
			doc_height += category_h + category_gap
		if category_heights:
			doc_height -= category_gap
		doc_bottom_pad = round(16 * gui.scale)
		if category_heights:
			# Add enough trailing space for the final category to reach the top inset.
			doc_bottom_pad += max(0, view_rect[3] - (content_top_pad + category_heights[-1] + doc_bottom_pad))
			doc_height += doc_bottom_pad

			max_content_scroll = self.sync_settings_content_scroll((content_x, content_y, content_width, content_height), doc_height)
			active_anchor = self.settings_content_scroll + round(24 * gui.scale)
			for index, offset in enumerate(self.settings_category_offsets):
				if active_anchor >= offset:
					self.tab_active = index

			scroll_start = int(self.settings_nav_scroll)
			scroll_offset = (self.settings_nav_scroll - scroll_start) * max(row_step, 1)
			if is_light(tab_bg):
				active_bg = rgb_add_hls(tab_bg, l=-0.09, s=0.03)
				hover_bg = rgb_add_hls(tab_bg, l=-0.05, s=0.02)
			else:
				active_bg = rgb_add_hls(tab_bg, l=0.08, s=0.03)
				hover_bg = rgb_add_hls(tab_bg, l=0.04, s=0.02)
			yy = nav_y - scroll_offset
			for index, label in enumerate(self.tabs):
				if index < scroll_start:
					continue
				if yy > nav_y + nav_h - row_step:
					break

				rect = (nav_x, round(yy), nav_w, row_height)
				self.fields.add(rect)
				hovered = self.coll(rect)
				row_bg = tab_bg
				if self.tab_active == index:
					row_bg = active_bg
					ddt.rect_a((rect[0], rect[1]), (rect[2], rect[3]), row_bg)
				elif hovered:
					row_bg = hover_bg
					ddt.rect_a((rect[0], rect[1]), (rect[2], rect[3]), row_bg)
				ddt.text(
					(rect[0] + round(11 * gui.scale), rect[1] + round(4 * gui.scale)),
					label,
					colours.box_text if self.tab_active == index else tab_text,
					212,
					bg=row_bg,
					max_w=rect[2] - round(18 * gui.scale),
				)
				if hovered and self.click:
					self.tab_active = index
					if index < len(self.settings_category_offsets):
						self.settings_content_scroll = min(max(self.settings_category_offsets[index], 0), max_content_scroll)
						self.tauon.smooth_scroll.reset_motion("settings content")
						self.lyrics_panel = False
				yy += row_step

		content_scrollbar_extend = round(4 * gui.scale)
		content_scrollbar_click = (
			max_content_scroll > 0
			and (self.click or self.inp.mouse_down)
			and self.coll((scrollbar_x - content_scrollbar_extend, view_rect[1], scrollbar_w + content_scrollbar_extend, view_rect[3]))
		)
		if content_scrollbar_click:
			self.click = False
			bar_height = round(90 * gui.scale)
			if view_rect[3] > 400 * gui.scale and max_content_scroll < 20:
				bar_height = round(180 * gui.scale)
			half = bar_height // 2
			distance = max(view_rect[3] - bar_height, 1)
			position = min(max(self.inp.mouse_position[1] - view_rect[1] - half, 0), distance)
			self.settings_content_scroll_bar.held = True
			self.settings_content_scroll_bar.source_click_y = self.inp.mouse_position[1]
			self.settings_content_scroll_bar.source_bar_y = position
			self.settings_content_scroll_bar.input_sdl.mouse_capture_want = True
			self.settings_content_scroll = round(max_content_scroll * (position / distance))
		if max_content_scroll > 0:
			self.settings_content_scroll = self.settings_content_scroll_bar.draw(
				scrollbar_x,
				view_rect[1],
				scrollbar_w,
				view_rect[3],
				self.settings_content_scroll,
				max_content_scroll,
				click=content_scrollbar_click,
				extend_field=content_scrollbar_extend,
			)

		texture = self.ensure_settings_texture((max(1, int(self.window_size[0])), max(1, int(self.window_size[1]))))
		current_target = sdl3.SDL_GetRenderTarget(self.renderer)
		sdl3.SDL_SetRenderTarget(self.renderer, texture)
		sdl3.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 0)
		sdl3.SDL_RenderClear(self.renderer)

		doc_x = view_rect[0]
		doc_y = view_rect[1] + content_top_pad - self.settings_content_scroll
		visible_top = view_rect[1] - round(80 * gui.scale)
		visible_bottom = view_rect[1] + view_rect[3] + round(80 * gui.scale)
		for index, category_h in enumerate(category_heights):
			category_y = round(doc_y + self.settings_category_offsets[index])
			if category_y > visible_bottom or category_y + category_h < visible_top:
				continue
			self.render_settings_category(index, doc_x, category_y, doc_w, draw=True)

		sdl3.SDL_SetRenderTarget(self.renderer, current_target)
		src_rect = sdl3.SDL_FRect(view_rect[0], view_rect[1], view_rect[2], view_rect[3])
		dst_rect = sdl3.SDL_FRect(view_rect[0], view_rect[1], view_rect[2], view_rect[3])
		sdl3.SDL_RenderTexture(self.renderer, texture, src_rect, dst_rect)

		self.finish_settings_text_inputs()
		self.click = False
		self.right_click = False

		ddt.text_background_colour = colours.box_background

def get_themes(dirs: Directories, deco: bool = False) -> list[tuple[str, str]] | dict[str, str]:
	themes: list[tuple[str, str]] = []  # full path, theme file name
	decos: dict[str, str] = {}
	direcs = [str(dirs.install_directory / "theme")]
	if dirs.user_directory != dirs.install_directory:
		direcs.append(str(dirs.user_directory / "theme"))

	def scan_folders(folders: list[str]) -> None:
		for folder in folders:
			if not os.path.isdir(folder):
				continue
			paths = [os.path.join(folder, f) for f in os.listdir(folder)]
			for path in paths:
				if os.path.islink(path):
					path = os.readlink(path)
				if os.path.isfile(path):
					if path[-7:] == ".ttheme":
						themes.append((path, os.path.basename(path).split(".")[0]))
					elif path[-6:] == ".tdeco":
						decos[os.path.basename(path).split(".")[0]] = path
				elif os.path.isdir(path):
					scan_folders([path])

	scan_folders(direcs)
	themes.sort()
	if deco:
		return decos
	return themes

def get_theme_number(dirs: Directories, name: str) -> int:
	if name == "Mindaro":
		return 0
	themes = get_themes(dirs)
	for i, theme in enumerate(themes):
		if theme[1] == name:
			return i + 1
	return 0

def get_theme_name(dirs: Directories, number: int) -> str:
	if number == 0:
		return "Mindaro"
	number -= 1
	themes = get_themes(dirs)
	logging.info((number, themes))
	if len(themes) > number:
		return themes[number][1]
	return ""

THEME_EDITOR_COMPONENTS: tuple[tuple[str, tuple[str, ...]], ...] = (
	(translate("Window borders"), ("window_frame", "box_border", "box_check_border", "mini_mode_border", "art_box", "gallery_highlight", "box_thumb_background", )),
	(translate("Top panel BG"), ("top_panel_background",)),
	(translate("Playlist box BG"), ("playlist_box_background",)),
	(translate("Queue panel: BG"), ("queue_background",)),
	(translate("Gallery panel BG"), ("gallery_background",)),
	(translate("Info panel: BG"), ("lyrics_panel_background", "side_panel_background",)),
	(translate("Info panel: main text"), ("side_bar_line1", "active_lyric", )),
	(translate("Info panel: 2nd text"), ("side_bar_line2", "lyrics", )),
	(translate("Artist bio: BG"), ("artist_bio_background",)),
	(translate("Artist bio: text"), ("artist_bio_text",)),
	(translate("Bottom panel: BG"), ("bottom_panel_colour",)),
	(translate("Bottom panel: text"), ("bar_title_text","time_playing",)),
	(translate("List: BG"), ("playlist_panel_background",)),
	(translate("List: column bar"), ("column_bar_background",)),
	(translate("List: column info"), ("column_bar_text", "column_grip",)),
	# (translate("List: artist"), ("artist_text",)),
	# (translate("List: album"), ("album_text",)),
	# (translate("List: duration"), ("bar_time",)),
	# (translate("List: other fields"), ("index_text",)),
	(translate("List: folder"), ("folder_title","folder_line",)),
	# (translate("List: folder line"), ("folder_line",)),
	(translate("List: star line"), ("star_line", "star_line_playing", )),
	(translate("List: text"), ("title_text","artist_text","album_text","bar_time","index_text",)),
	(translate("List: select highlight"), ("row_select_highlight",)),
	(translate("List: playing text"), ("title_playing","artist_playing","album_playing","time_text","index_playing",)),
	(translate("List: play highlight"), ("row_playing_highlight",)),
	(translate("List: missing track"), ("playlist_text_missing",)),
	# (translate("List: playing artist"), ("artist_playing",)),
	# (translate("List: playing album"), ("album_playing",)),
	# (translate("List: playing duration"), ("time_text",)),
	# (translate("List: playing other"), ("index_playing",)),
	(translate("Seek/volume: fill"), ("seek_bar_fill", "volume_bar_fill", "vis_colour", )),
	(translate("Seek/volume: BG"), ("seek_bar_background", "volume_bar_background", "vis_bg", )),
	(translate("Scroll bar"), ("scroll_colour",)),
	(translate("Buttons: normal"), ("media_buttons_off", "mode_button_off", "status_text_normal", "corner_button", "window_button_icon_off", "window_button_x_off", "menu_icons", )),
	(translate("Buttons: hover"), ("media_buttons_over", "mode_button_over", "status_text_over", "window_buttons_icon_over", "window_button_x_on", )),
	(translate("Buttons: active"), ("media_buttons_active", "mode_button_active", "corner_button_active", )),
	(translate("Text btn: BG"), ("window_buttons_bg", "box_button_background", "tab_background", "menu_tab",)),
	(translate("Text btn: text"), ("box_button_text", "tab_text", "link_text", )),
	(translate("Text btn: BG hover"), ( "box_button_background_highlight", "tab_highlight", )),
	(translate("Text btn: text hover"), ("window_buttons_bg_over", "box_button_text_highlight", )),
	(translate("Tab btn: BG active"), ("tab_background_active",)),
	(translate("Tab btn: text active"), ("tab_text_active", )),
	(translate("Dynamic accents"), ("queue_drag_indicator_colour", "pulse_colour", "queue_card_background",)),
	(translate("Context menu: BG"), ("menu_background", )),
	(translate("Context menu: text"), ("menu_text", )),
	(translate("Context menu: invalid text"), ("menu_text_disabled",)),
	(translate("Context menu: highlight"), ("menu_highlight_background",)),
	(translate("Boxes: background"), ("box_background","message_box_bg",)),
	(translate("Boxes: title text"), ("box_title_text", "box_text_label",)),
	(translate("Boxes: body text"), ("box_text", "message_box_text",)),
	(translate("Boxes: sub text"), ("box_sub_text",)),
	(translate("Boxes: input text"), ("box_input_text",)),
	(translate("Mini: BG"), ("mini_mode_background",)),
	(translate("Mini: text 1"), ("mini_mode_text_1",)),
	(translate("Mini: text 2"), ("mini_mode_text_2",)),
)

def clone_theme_colours(colours: ColoursClass) -> ColoursClass:
	clone = ColoursClass()
	for key, value in colours.__dict__.items():
		setattr(clone, key, copy.deepcopy(value))
	return clone

def auto_scale(bag: Bag) -> None:
	prefs = bag.prefs
	old = prefs.scale_want

	if prefs.x_scale:
		prefs.scale_want = bag.window_size[0] / bag.logical_size[0]

	prefs.scale_want = round(round(prefs.scale_want / 0.05) * 0.05, 2)
	if prefs.x_scale and old != prefs.scale_want:
		logging.info("Applying scale based on buffer size")

	if prefs.scale_want == 0.95:
		prefs.scale_want = 1.0
	if prefs.scale_want == 1.05:
		prefs.scale_want = 1.0
	if prefs.scale_want == 1.95:
		prefs.scale_want = 2.0
	if prefs.scale_want == 2.05:
		prefs.scale_want = 2.0

	if old != prefs.scale_want:
		logging.info(f"Using UI scale: {prefs.scale_want}")

	prefs.scale_want = max(prefs.scale_want, 0.5)

def auto_get_sync_targets() -> list[str]:
	search_paths = [
		"/run/user/*/gvfs/*/*/[Mm]usic",
		"/run/media/*/*/[Mm]usic"]
	result_paths = []
	for item in search_paths:
		result_paths.extend(glob.glob(item))
	return result_paths
