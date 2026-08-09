"""Shared UI and application state classes."""

from __future__ import annotations

import time
from collections import deque
from ctypes import c_char_p, c_float, c_ubyte, pointer
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Protocol

import sdl3

from tauon.t_modules.t_enums import GuiMode
from tauon.t_modules.t_extra import (
	FPSCounter,
	TestTimer,
	Timer,
	alpha_blend,
	alpha_mod,
	colour_value,
	rgb_add_hls,
	test_lumi,
)
from tauon.t_modules.t_models import ColourRGBA, TauonQueueItem

if TYPE_CHECKING:
	from tauon.t_modules.t_models import Directories
	from tauon.t_modules.t_prefs import Prefs


class StateBag(Protocol):
	"""Structural subset of Bag consumed by the shared UI state classes."""

	console: DConsole
	dirs: Directories
	loaded_asset_dc: dict[str, WhiteModImageAsset | LoadImageAsset]
	phone: bool
	prefs: Prefs
	renderer: sdl3.LP_SDL_Renderer
	windows: bool
	window_size: list[int]


@dataclass
class Decorator:
	text_colour: ColourRGBA | None
	bg_colour: ColourRGBA | None
	text: str | None

@dataclass(frozen=True)
class MenuTrackRef:
	track_id: int
	position: int
	playlist_id: int


class LoadImageAsset:
	# TODO(Martin): Global class var!
	assets: ClassVar[list[LoadImageAsset]] = []

	def __init__(
		self, *, bag: StateBag, path: str, is_full_path: bool = False, reload: bool = False, scale_name: str = ""
	) -> None:
		if not reload:
			self.assets.append(self)
		self.bag = bag
		self.dirs = bag.dirs
		self.renderer = bag.renderer
		self.path = path
		self.scale_name = scale_name

		raw_image = sdl3.IMG_Load(c_char_p(self.path.encode()))
		self.texture = sdl3.SDL_CreateTextureFromSurface(self.renderer, raw_image)

		p_w = pointer(c_float(0.0))
		p_h = pointer(c_float(0.0))
		sdl3.SDL_GetTextureSize(self.texture, p_w, p_h)

		if is_full_path:
			sdl3.SDL_SetTextureAlphaMod(self.texture, c_ubyte(bag.prefs.custom_bg_opacity))

		self.rect = sdl3.SDL_FRect(0, 0, p_w.contents.value, p_h.contents.value)
		sdl3.SDL_DestroySurface(raw_image)
		self.w = p_w.contents.value
		self.h = p_h.contents.value

		# Lazily created copies of this texture on other renderers (e.g. a
		# SecondaryWindow), keyed by renderer_key(). The home renderer's texture
		# lives in self.texture above.
		self._alt_textures: dict[int, sdl3.LP_SDL_Texture] = {}

	def _texture_for(self, renderer: sdl3.LP_SDL_Renderer | None) -> sdl3.LP_SDL_Texture:
		if renderer is None:
			return self.texture
		from tauon.t_modules.t_window import renderer_key
		key = renderer_key(renderer)
		if key == renderer_key(self.renderer):
			return self.texture
		texture = self._alt_textures.get(key)
		if texture is None:
			raw_image = sdl3.IMG_Load(c_char_p(self.path.encode()))
			texture = sdl3.SDL_CreateTextureFromSurface(renderer, raw_image)
			sdl3.SDL_DestroySurface(raw_image)
			self._alt_textures[key] = texture
		return texture

	def _destroy_alt_textures(self) -> None:
		for texture in self._alt_textures.values():
			sdl3.SDL_DestroyTexture(texture)
		self._alt_textures.clear()

	def reload(self) -> None:
		sdl3.SDL_DestroyTexture(self.texture)
		self._destroy_alt_textures()
		if self.scale_name:
			self.path = str(self.dirs.scaled_asset_directory / self.scale_name)
		self.__init__(bag=self.bag, path=self.path, reload=True, scale_name=self.scale_name)

	def render(self, x: float, y: float, _colour: ColourRGBA | None = None, renderer: sdl3.LP_SDL_Renderer | None = None) -> None:
		self.rect.x = round(x)
		self.rect.y = round(y)
		sdl3.SDL_RenderTexture(renderer or self.renderer, self._texture_for(renderer), None, self.rect)

class WhiteModImageAsset:
	# TODO(Martin): Global class var!
	assets: ClassVar[list[WhiteModImageAsset]] = []

	def __init__(self, *, bag: StateBag, path: str, reload: bool = False, scale_name: str = "") -> None:
		self.bag  = bag
		self.dirs = bag.dirs
		if not reload:
			self.assets.append(self)
		self.path = path
		self.scale_name = scale_name

		raw_image = sdl3.IMG_Load(path.encode())
		self.texture = sdl3.SDL_CreateTextureFromSurface(self.bag.renderer, raw_image)
		self.colour = ColourRGBA(255, 255, 255, 255)
		p_w = pointer(c_float(0.0))
		p_h = pointer(c_float(0.0))
		sdl3.SDL_GetTextureSize(self.texture, p_w, p_h)
		self.rect = sdl3.SDL_FRect(0, 0, p_w.contents.value, p_h.contents.value)
		sdl3.SDL_DestroySurface(raw_image)
		self.w = p_w.contents.value
		self.h = p_h.contents.value

		# Lazily created copies on other renderers, with each copy's last applied
		# colour-mod tracked separately: value is [texture, last_colour].
		self._alt_textures: dict[int, list] = {}

	def _entry_for(self, renderer: sdl3.LP_SDL_Renderer | None) -> tuple[sdl3.LP_SDL_Texture, ColourRGBA, int | None]:
		"""Return (texture, last_colour, alt_key) for the given renderer.

		alt_key is None when the home texture is used (its colour state lives in
		self.colour); otherwise it identifies the per-renderer copy.
		"""
		if renderer is None:
			return self.texture, self.colour, None
		from tauon.t_modules.t_window import renderer_key
		key = renderer_key(renderer)
		if key == renderer_key(self.bag.renderer):
			return self.texture, self.colour, None
		entry = self._alt_textures.get(key)
		if entry is None:
			raw_image = sdl3.IMG_Load(self.path.encode())
			texture = sdl3.SDL_CreateTextureFromSurface(renderer, raw_image)
			sdl3.SDL_DestroySurface(raw_image)
			entry = [texture, ColourRGBA(255, 255, 255, 255)]
			self._alt_textures[key] = entry
		return entry[0], entry[1], key

	def _destroy_alt_textures(self) -> None:
		for entry in self._alt_textures.values():
			sdl3.SDL_DestroyTexture(entry[0])
		self._alt_textures.clear()

	def reload(self) -> None:
		sdl3.SDL_DestroyTexture(self.texture)
		self._destroy_alt_textures()
		if self.scale_name:
			self.path = str(self.dirs.scaled_asset_directory / self.scale_name)
		self.__init__(bag=self.bag, path=self.path, reload=True, scale_name=self.scale_name)

	def render(self, x: float, y: float, colour: ColourRGBA, renderer: sdl3.LP_SDL_Renderer | None = None) -> None:
		texture, last_colour, alt_key = self._entry_for(renderer)
		if colour != last_colour:
			sdl3.SDL_SetTextureColorMod(texture, colour.r, colour.g, colour.b)
			sdl3.SDL_SetTextureAlphaMod(texture, colour.a)
			if alt_key is None:
				self.colour = colour
			else:
				self._alt_textures[alt_key][1] = colour
		self.rect.x = round(x)
		self.rect.y = round(y)
		sdl3.SDL_RenderTexture(renderer or self.bag.renderer, texture, None, self.rect)

class DConsole:
	"""GUI console with logs"""

	def __init__(self) -> None:
		self.show: bool = False
		self.fps_only: bool = False
		self.fps = FPSCounter(window_size=20, min_update_interval=0.12, max_frame_time=0.5)
		# The full console keeps its traditional inter-frame average above. The
		# non-driving diagnostic instead counts frames in a wall-clock window, so
		# a short 60 Hz input burst after a long idle reads as a few FPS, not 60.
		self.diagnostic_frames: deque[float] = deque()

	def diagnostic_tick(self) -> None:
		now = time.perf_counter()
		self.diagnostic_frames.append(now)
		cutoff = now - 1.0
		while self.diagnostic_frames and self.diagnostic_frames[0] <= cutoff:
			self.diagnostic_frames.popleft()

	def diagnostic_fps(self) -> int:
		return len(self.diagnostic_frames)

	def toggle(self) -> None:
		"""Cycle the diagnostics overlay through console, FPS-only and hidden."""
		if self.show:
			self.show = False
			self.fps_only = True
			# Discard samples gathered while the console was driving frames.
			self.diagnostic_frames.clear()
		elif self.fps_only:
			self.fps_only = False
		else:
			self.show = True
			self.fps.reset()

class GuiVar:
	"""Use to hold any variables for use in relation to UI"""

	def set_drag_source(self) -> None:
		self.drag_source_position = tuple(self.inp.click_location)
		self.drag_source_position_persist = tuple(self.inp.click_location)

	def delay_frame(self, t: float) -> None:
		self.frame_callback_list.append(TestTimer(t))

	def request_frame(self) -> None:
		"""Request the main loop render a frame. The flag is flipped off at the
		start of every frame, so calling this while drawing means "render
		another frame after this one"."""
		self.update = True

	def request_tracklist_redraw(self) -> None:
		"""Request the playlist/tracklist view re-render on the next frame. The
		flag is flipped off as the tracklist render starts, so calling this
		mid-render means "render the tracklist again next frame"."""
		self.pl_update = True

	def destroy_textures(self) -> None:
		sdl3.SDL_DestroyTexture(self.spec4_tex)
		sdl3.SDL_DestroyTexture(self.spec1_tex)
		sdl3.SDL_DestroyTexture(self.spec2_tex)
		sdl3.SDL_DestroyTexture(self.spec_level_tex)

	# def test_text_input(self):
	#	 if self.text_input_request and not self.text_input_active:
	#		 sdl3.SDL_StartTextInput()
	#		 self.update += 1
	#	 if not self.text_input_request and self.text_input_active:
	#		 sdl3.SDL_StopTextInput()
	#	 self.text_input_request = False

	def rescale(self) -> None:
		self.spec_y = round(5 * self.scale)
		self.spec_w = round(80 * self.scale)
		self.spec_h = round(20 * self.scale)
		self.spec1_rec = sdl3.SDL_FRect(0, self.spec_y, self.spec_w, self.spec_h)

		self.spec4_y = round(200 * self.scale)
		self.spec4_w = round(322 * self.scale)
		self.spec4_h = round(100 * self.scale)
		self.spec4_rec = sdl3.SDL_FRect(0, self.spec4_y, self.spec4_w, self.spec4_h)

		self.bar = sdl3.SDL_FRect(10, 10, round(3 * self.scale), 10)  # spec bar bin
		self.bar4 = sdl3.SDL_FRect(10, 10, round(3 * self.scale), 10)  # spec bar bin
		self.set_height = round(25 * self.scale)
		self.panelBY = round(51 * self.scale)
		self.panelY = round(30 * self.scale)
		self.panelY2 = round(30 * self.scale)
		self.playlist_top = self.panelY + (8 * self.scale)
		self.playlist_top_bk = self.playlist_top
		self.scroll_hide_box = (0, self.panelY, 28, self.bag.window_size[1] - self.panelBY - self.panelY)

		self.spec2_y = round(22 * self.scale)
		self.spec2_w = round(140 * self.scale)
		self.spec2 = [0] * self.spec2_y
		self.spec2_phase = 0
		self.spec2_buffers = []
		self.spec2_rec = sdl3.SDL_FRect(1230, round(4 * self.scale), self.spec2_w, self.spec2_y)
		self.spec2_source = sdl3.SDL_FRect(900, round(4 * self.scale), self.spec2_w, self.spec2_y)
		self.spec2_dest = sdl3.SDL_FRect(900, round(4 * self.scale), self.spec2_w, self.spec2_y)
		self.spec2_position = 0
		self.spec2_timer = Timer()
		self.spec2_timer.set()

		self.level_w = 5 * self.scale
		self.level_y = 16 * self.scale
		self.level_s = 1 * self.scale
		self.level_ww = round(79 * self.scale)
		self.level_hh = round(18 * self.scale)
		self.spec_level_rec = sdl3.SDL_FRect(
			0, round(self.level_y - 10 * self.scale), round(self.level_ww),round(self.level_hh))

		self.spec2_tex = sdl3.SDL_CreateTexture(
			self.bag.renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET, self.spec2_w, self.spec2_y)
		self.spec4_tex = sdl3.SDL_CreateTexture(
			self.bag.renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET, self.spec4_w, self.spec4_y)
		self.spec1_tex = sdl3.SDL_CreateTexture(
			self.bag.renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET, self.spec_w, self.spec_h)
		self.spec_level_tex = sdl3.SDL_CreateTexture(
			self.bag.renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET, self.level_ww, self.level_hh)
		sdl3.SDL_SetTextureBlendMode(self.spec4_tex, sdl3.SDL_BLENDMODE_BLEND)
		# Blend so a translucent vis_bg (frosted art background) lets the
		# panel and art beneath show through
		sdl3.SDL_SetTextureBlendMode(self.spec1_tex, sdl3.SDL_BLENDMODE_BLEND)
		sdl3.SDL_SetTextureBlendMode(self.spec2_tex, sdl3.SDL_BLENDMODE_BLEND)
		sdl3.SDL_SetTextureBlendMode(self.spec_level_tex, sdl3.SDL_BLENDMODE_BLEND)
		self.artist_panel_height = 320 * self.scale
		self.last_artist_panel_height = self.artist_panel_height

		self.window_control_hit_area_w = 100 * self.scale
		self.window_control_hit_area_h = 30 * self.scale

	def __init__(self, bag: StateBag, tracklist_texture_rect: sdl3.SDL_FRect, tracklist_texture: sdl3.LP_SDL_Texture, main_texture_overlay_temp: sdl3.LP_SDL_Texture, main_texture: sdl3.LP_SDL_Texture, max_window_tex: int) -> None:
		self.bag: StateBag = bag
		self.console: DConsole = bag.console
		self.inp: Input = Input(gui=self)
		self.keymaps: KeyMap = KeyMap(bag=bag, inp=self.inp)

		self.scale: float = self.bag.prefs.ui_scale

		self.panelY: int = 0
		self.panelY2: int = 0
		self.panelBY: float = 0

		self.window_id = 0
		self.update: bool = True  # Render a frame on the next main loop pass
		self.update_layout: bool = True
		self.turbo:      bool = True
		self.turbo_next = 0
		self.pl_update: bool = True  # Re-render the tracklist on the next frame
		self.lowered:           bool = False
		self.maximized:         bool = False
		self.side_drag:         bool = False
		self.ext_drop_mode:     bool = False
		self.quick_search_mode: bool = False
		self.b_info_bar:        bool = False
		self.editline: str = ""
		self.rename_index:        int = 0
		self.last_row:            int = 0
		self.album_v_gap:       float = 66
		self.album_h_gap:       float = 30
		self.album_v_slide_value: int = 50
		self.album_scroll_px: float = self.album_v_slide_value
		# Playlist Panel
		self.pl_rect = (2, 12, 10, 10)

		self.track_box: bool = False
		self.track_box_track_id: int = 0

		self.move_on_title: bool = False

		self.message_box: bool = False
		self.message_text: str = ""
		self.message_mode: str = "info"
		self.message_subtext: str = ""
		self.message_subtext2: str = ""
		self.message_box_confirm_reference = None
		self.message_box_use_reference: bool = True
		self.message_box_confirm_callback = None
		self.message_box_no_callback = None

		self.save_size = [450, 310]
		self.show_playlist: bool = True
		self.show_bottom_title: bool = False
		# self.show_top_title: bool = True
		self.search_error: bool = False

		self.level_update: bool = False
		self.level_time: Timer = Timer()
		self.level_peak: list[float] = [0, 0]
		self.level = 0
		self.time_passed = 0
		self.level_meter_colour_mode = 3

		self.vis = 0  # visualiser mode actual
		self.vis_want = 2  # visualiser mode setting
		self.spec: list[float] | None = None
		self.s_spec = [0] * 24
		self.s4_spec = [0] * 45
		self.update_spec = 0

		self.new_playlist_cooldown: bool = False
		self.playlist_hold_position = 0
		self.playlist_hold: bool = False
		self.selection_stage = 0
		self.playlist_scroll_pixels: float = 0

		self.shift_selection: list[int] = []

		# self.spec_rect = [0, 5, 80, 20]  # x = 72 + 24 - 6 - 10

		self.spec4_array: list[float] = []

		self.draw_spec4: bool = False

		self.combo_mode: bool = False
		# Custom Layout System (opt-in). When custom_mode is set the custom
		# layout engine composites over the frame; custom_edit toggles edit mode.
		self.custom_mode: bool = False
		self.custom_edit: bool = False
		# The Custom Layout MilkDrop Box widget owns the (singleton) visualiser:
		# gates the ArtBox / MetaBox milk paths off so both never run at once.
		self.milkdrop_in_widget: bool = False
		# The Custom Layout Sticks visualiser widget is in the layout: makes
		# update_layout_do() switch gui.vis to 4 so PHAZOR feeds spec4_array.
		self.vis4_in_widget: bool = False
		# Ditto for the Spectrogram widget (gui.vis 6): PHAZOR pushes raw
		# spectrum columns of spectrogram_bins values into spectrogram_buffers.
		self.spectrogram_in_widget: bool = False
		# When non-zero, render_gallery uses this row length instead of deriving
		# it from album_mode_art_size, and switches to edge-to-edge placement
		# inset by gallery_grid_margin (scaled px) on the left/right. Set (and
		# restored) around the call by the Custom Layout's Gallery: Compact
		# widget; 0 = preset behaviour.
		self.gallery_forced_row_len: int = 0
		self.gallery_grid_margin: int = 0
		# Smooth-scroll momentum channel used by render_gallery. Each Gallery:
		# Compact instance swaps in its own key so several galleries scroll
		# independently; "gallery" = the preset / Classic widget channel.
		self.gallery_scroll_key: str = "gallery"
		self.spectrogram_bins: int = 256
		self.spectrogram_buffers: list[list[float]] = []
		self.showcase_mode: bool = False
		self.timed_lyrics_edit_view: bool = False
		self.timed_lyrics_editing_now: bool = False
		self.lyrics_editor_update_now: list[bool] = [False, False]
		self.display_time_mode = 0

		self.pl_text_real_height = 12
		self.pl_title_real_height = 11

		self.row_extra = 0
		self.test: bool = False
		self.light_mode: bool = False

		self.level_2_click: bool = False
		self.universal_y_text_offset = 0

		self.star_text_y_offset = 0

		self.set_bar: bool = True
		self.set_mode: bool = False
		self.set_hold = -1
		self.set_label_hold = -1
		self.set_label_point = (0, 0)
		self.set_point = 0
		self.set_old = 0
		self.pl_st: list[list[str | int | bool]] = [
			["Artist", 156, False], ["Title", 188, False], ["T", 40, True], ["Album", 153, False],
			["P", 28, True], ["Starline", 86, True], ["Date", 48, True], ["Codec", 55, True],
			["Time", 53, True]]
		self.pl_box_h: int = 0

		# Leading inset before the first column in columns (set) mode. Kept as an
		# independent variable (not an entry in pl_st) so the first grip can drag
		# the whole column block left/right. Stored pre-scale (a base value at 1x)
		# and multiplied by gui.scale at each use, so it persists correctly across
		# ui-scale changes.
		self.pl_st_left: float = 16

		for item in self.pl_st:
			item[1] = item[1] * self.scale

		self.offset_extra: int = 0

		self.playlist_row_height:    int = 16
		self.playlist_text_offset: float = 0
		self.row_font_size:          int = 13
		self.compact_bar: bool = False
		self.tracklist_texture_rect: sdl3.SDL_FRect = tracklist_texture_rect
		self.tracklist_texture = tracklist_texture

		self.trunk_end = "..."  # "…"
		self.temp_themes: dict[str, ColoursClass] = {}
		self.theme_temp_current = -1

		self.pl_title_y_offset = 0
		self.pl_title_font_offset = -1

		self.playlist_box_d_click = -1

		self.gallery_show_text: bool = True
		self.bb_show_art: bool = False

		self.rename_folder_box: bool = False

		self.present: bool = False
		self.drag_source_position = (0, 0)
		self.drag_source_position_persist = (0, 0)
		#self.old_album_pos: int = -55
		self.album_playlist_width: int = 430

		self.album_tab_mode: bool = False
		self.main_art_box = (0, 0, 10, 10)
		self.gall_tab_enter: bool = False

		self.lightning_copy: bool = False

		self.gallery_animate_highlight_on = 0

		self.seek_cur_show: bool = False
		self.cur_time = "0"
		self.force_showcase_index = -1

		self.frame_callback_list: list[TestTimer] = []

		self.playlist_left: float | None = None
		self.image_downloading:     bool = False
		self.tc_cancel:             bool = False
		self.im_cancel:             bool = False
		self.force_search:          bool = False

		self.pl_pulse: bool = False

		self.view_name = "S"
		self.restart_album_mode: bool = False

		self.dtm3_index = -1
		self.dtm3_cum = 0
		self.dtm3_total = 0
		self.previous_playlist_id: int = 0

		self.star_mode = "line"
		self.heart_fields: list[list[float]] = [] # list of rectangles
		self.show_ratings: bool = False

		self.web_running: bool = False

		self.rsp: bool = True
		if self.bag.phone:
			self.rsp = False
		self.rspw: float = round(300 * self.scale)
		self.lsp: bool = False
		self.lspw: float = round(220 * self.scale)
		self.lsp_x: float = 0
		self.plw: float | None = None
		self.rsp_on_left: bool = False
		self.rsp_x: float = 0
		self.rsp_split_x: float = 0

		self.pref_rspw = 300

		self.pref_gallery_w = 600

		self.artist_info_panel: bool = False
		self.album_artist_dict: dict[int, str] = {}

		self.show_hearts: bool = True

		self.search_index: int = 0

		self.cursor_is = 0
		self.cursor_want = 0
		# 0 standard
		# 1 drag horizontal
		# 2 text
		# 3 hand

		self.power_bar = None
		self.gallery_scroll_field_left = 1
		self.combo_was_album: bool = False

		self.gallery_positions: dict[int, float] = {}

		self.remember_library_mode: bool = False

		self.first_in_grid = None

		self.art_aspect_ratio = 1
		self.art_drawn_rect = None
		self.art_unlock_ratio: bool = False
		self.art_max_ratio_lock = 1
		self.side_bar_drag_source = 0
		self.side_bar_drag_original = 0

		self.scroll_direction = 0
		self.add_music_folder_ready: bool = False

		self.playlist_current_visible_tracks = 0
		self.playlist_current_visible_tracks_id = 0

		self.theme_name = ""
		self.rename_playlist_box: bool = False
		self.queue_frame_draw = None  # Set when need draw frame later

		self.mode = GuiMode.MAIN

		self.save_position = [0, 0]

		self.draw_vis4_top: bool = False
		# self.vis_4_colour = ColourRGBA(0,0,0,255)
		self.vis_4_colour: ColourRGBA | None = None

		self.layer_focus = 0
		self.tab_menu_pl = 0

		self.tool_tip_lock_off_f: bool = False
		self.tool_tip_lock_off_b: bool = False

		self.auto_play_import: bool = False

		self.transcoding_batch_total = 0
		self.transcoding_batch_done = 0

		self.seek_bar_rect = (0, 0, 0, 0)
		self.volume_bar_rect = (0, 0, 0, 0)

		self.mini_mode_return_maximized: bool = False

		self.opened_config_file: bool = False

		self.notify_main_id: bool | None = None

		self.halt_image_rendering: bool = False
		self.generating_chart: bool = False

		self.top_bar_mode2: bool = False
		self.mode_toast_text = ""

		self.rescale()
		# self.smooth_scrolling = False

		self.compact_artist_list: bool = False

		self.rsp_full_lock: bool = False

		self.queue_toast_plural: bool = False
		self.reload_theme: bool = False
		self.theme_number = 0
		self.toast_queue_object: TauonQueueItem | None = None
		self.toast_love_object = None
		self.toast_love_added: bool = True

		self.force_side_on_drag: bool = False
		self.last_left_panel_mode = "playlist"
		self.showing_l_panel: bool = False
		self.l_panel_h: int = 0
		self.l_panel_y: int = 0

		self.downloading_bass: bool = False
		self.d_click_ref = -1

		self.max_window_tex = max_window_tex # Both X and Y of maximal Tauon window texture size
		self.main_texture = main_texture
		self.main_texture_overlay_temp = main_texture_overlay_temp

		# True while the current frame has the album-art background drawn
		# underneath the UI; panels must blend over it rather than clearing
		# or replacing their region's pixels
		self.have_art_bg: bool = False

		self.preview_artist: str = ""
		self.preview_artist_location = (0, 0)
		self.preview_artist_loading: str = ""
		self.mouse_left_window: bool = False

		self.rendered_playlist_position = 0
		self.playlist_view_length: int = 0

		self.show_album_ratings: bool = False
		self.album_rating_hover: bool = False
		self.scrollbar_active: bool = False
		self.scrollbar_interaction_lock: bool = False
		self.gen_code_errors: bool = False

		self.regen_single = -1
		self.regen_single_id = None

		self.tracklist_bg_is_light: bool = False
		self.clear_image_cache_next = 0

		self.click_time = time.time()

		self.column_d_click_timer = Timer(10)
		self.column_d_click_on = -1
		self.column_sort_ani_timer = Timer(10)
		self.column_sort_down_icon = asset_loader(self.bag, self.bag.loaded_asset_dc, "sort-down.png", True)
		self.column_sort_up_icon = asset_loader(self.bag, self.bag.loaded_asset_dc, "sort-up.png", True)
		self.column_sort_ani_direction = 1
		self.column_sort_ani_x = 0

		self.inc_arrow               = asset_loader(self.bag, self.bag.loaded_asset_dc, "inc.png", True)
		self.dec_arrow               = asset_loader(self.bag, self.bag.loaded_asset_dc, "dec.png", True)
		self.corner_icon             = asset_loader(self.bag, self.bag.loaded_asset_dc, "corner.png", True)
		self.heart_icon              = MenuIcon(asset_loader(self.bag, self.bag.loaded_asset_dc, "heart-menu.png", True))
		self.heart_row_icon          = asset_loader(self.bag, self.bag.loaded_asset_dc, "heart-track.png", True)
		self.heart_notify_icon       = asset_loader(self.bag, self.bag.loaded_asset_dc, "heart-notify.png", True)
		self.heart_notify_break_icon = asset_loader(self.bag, self.bag.loaded_asset_dc, "heart-notify-break.png", True)
		self.star_pc_icon            = asset_loader(self.bag, self.bag.loaded_asset_dc, "star-pc.png", True)
		self.star_row_icon           = asset_loader(self.bag, self.bag.loaded_asset_dc, "star.png", True)
		self.star_half_row_icon      = asset_loader(self.bag, self.bag.loaded_asset_dc, "star-half.png", True)

		self.heartx_icon        = MenuIcon(asset_loader(self.bag, self.bag.loaded_asset_dc, "heart-menu.png", True))
		self.transcode_icon     = MenuIcon(asset_loader(self.bag, self.bag.loaded_asset_dc, "transcode.png", True))
		self.mod_folder_icon    = MenuIcon(asset_loader(self.bag, self.bag.loaded_asset_dc, "mod_folder.png", True))
		self.settings_icon      = MenuIcon(asset_loader(self.bag, self.bag.loaded_asset_dc, "settings2.png", True))
		self.rename_tracks_icon = MenuIcon(asset_loader(self.bag, self.bag.loaded_asset_dc, "pen.png", True))
		self.add_icon           = MenuIcon(asset_loader(self.bag, self.bag.loaded_asset_dc, "new.png", True))

		self.filter_icon      = MenuIcon(asset_loader(self.bag, self.bag.loaded_asset_dc, "filter.png", True))
		self.folder_icon      = MenuIcon(asset_loader(self.bag, self.bag.loaded_asset_dc, "folder.png", True))
		self.info_icon        = MenuIcon(asset_loader(self.bag, self.bag.loaded_asset_dc, "info.png", True))
		self.delete_icon      = MenuIcon(asset_loader(self.bag, self.bag.loaded_asset_dc, "del.png", True))
		self.revert_icon      = MenuIcon(asset_loader(self.bag, self.bag.loaded_asset_dc, "revert.png", True))
		self.radiorandom_icon = MenuIcon(asset_loader(self.bag, self.bag.loaded_asset_dc, "radiorandom.png", True))

		self.last_fm_icon       = asset_loader(self.bag, self.bag.loaded_asset_dc, "as.png", True)
		self.power_bar_icon     = asset_loader(self.bag, self.bag.loaded_asset_dc, "power.png", True)
		self.mac_circle         = asset_loader(self.bag, self.bag.loaded_asset_dc, "macstyle.png", True)

		self.restore_showcase_view: bool = False
		self.restore_radio_view: bool = False

		self.tracklist_center_mode: bool = False
		self.tracklist_inset_left = 0
		self.tracklist_inset_width = 0
		self.tracklist_highlight_width = 0
		self.highlight_left = 0
		self.tracklist_highlight_left = 0

		self.hide_tracklist_in_gallery: bool = False

		self.saved_prime_tab = 0
		self.saved_prime_direction = 0

		self.stop_sync: bool = False
		self.sync_progress = ""
		self.sync_speed = ""

		self.bar_hover_timer = Timer()

		self.level_decay_timer = Timer()

		self.showed_title: bool = False

		self.to_get = 0 # Used to store temporary import count display
		self.to_got: int | str = 0
		self.switch_showcase_off: bool = False

		self.backend_reloading: bool = False

		self.tray_active: bool = False
		self.buffering: bool = False
		self.buffering_text = ""

		self.update_on_drag: bool = False
		self.pl_update_on_drag: bool = False
		self.drop_playlist_target = 0
		self.discord_status: str = "Standby"
		self.mouse_unknown: bool = False
		self.macstyle = self.bag.prefs.macstyle
		self.radio_view: bool = False
		self.window_size = self.bag.window_size
		self.box_over: bool = False
		self.suggest_clean_db: bool = False
		self.style_worker_timer: Timer = Timer()

		self.shuffle_was_showcase: bool = False
		self.shuffle_was_random: bool = True
		self.shuffle_was_repeat: bool = False

		self.was_radio: bool = False
		self.fullscreen: bool = False
		self.mouse_in_window: bool = True

		self.write_tag_in_progress: bool = False
		self.tag_write_count = 0
		# self.text_input_request = False
		# self.text_input_active = False
		self.center_blur_pixel = (0, 0, 0)
		self.cursor_hand = sdl3.SDL_CreateSystemCursor(sdl3.SDL_SYSTEM_CURSOR_POINTER)
		self.cursor_standard = sdl3.SDL_CreateSystemCursor(sdl3.SDL_SYSTEM_CURSOR_DEFAULT)
		self.cursor_shift = sdl3.SDL_CreateSystemCursor(sdl3.SDL_SYSTEM_CURSOR_EW_RESIZE)
		# General-purpose vertical-resize cursor, available on every platform
		# (unlike cursor_top_side which is only NS on Windows/X11).
		self.cursor_ns = sdl3.SDL_CreateSystemCursor(sdl3.SDL_SYSTEM_CURSOR_NS_RESIZE)
		self.cursor_text = sdl3.SDL_CreateSystemCursor(sdl3.SDL_SYSTEM_CURSOR_TEXT)

		self.cursor_br_corner   = self.cursor_standard
		self.cursor_right_side  = self.cursor_standard
		self.cursor_top_side    = self.cursor_standard
		self.cursor_left_side   = self.cursor_standard
		self.cursor_bottom_side = self.cursor_standard

		self.toast_length = 1


		if bag.windows:
			self.cursor_br_corner = sdl3.SDL_CreateSystemCursor(sdl3.SDL_SYSTEM_CURSOR_NWSE_RESIZE)
			self.cursor_right_side = self.cursor_shift
			self.cursor_left_side = self.cursor_shift
			self.cursor_top_side = sdl3.SDL_CreateSystemCursor(sdl3.SDL_SYSTEM_CURSOR_NS_RESIZE)
			self.cursor_bottom_side = self.cursor_top_side



class Fonts:
	"""Used to hold font sizes (I forget to use this)"""

	def __init__(self) -> None:
		self.tabs = 211
		self.panel_title = 213

		self.side_panel_line1 = 214
		self.side_panel_line2 = 313

		self.bottom_panel_time = 212

		# if system == 'Windows':
		#	 self.bottom_panel_time = 12  # The Arial bold font is too big so just leaving this as normal. (lazy)

class Input:
	"""Used to keep track of button states (or should be)"""

	def __init__(self, gui: GuiVar) -> None:
		self.gui = gui
		self.ab_click:            bool = False
		self.d_mouse_click:       bool = False # Double click
		self.mouse_click:         bool = False
		self.middle_click:        bool = False
		self.right_click:         bool = False
		self.level_2_right_click: bool = False
		self.level_2_enter:       bool = False
		self.backspace_press:      int = 0
		self.mouse_wheel:        float = 0
		self.mouse_wheel_precise: bool = False
		self.mouse_down:          bool = False
		self.mouse_up:            bool = False
		self.right_down:          bool = False
		self.click_location:      list[int] = [200, 200]
		self.last_click_location: list[int] = [0, 0]
		self.mouse_position:      list[int] = [0, 0]
		# Active view transform: screen = local + view_offset. Non-zero only while
		# something renders a sub-view in its own local coordinate space (the
		# Custom Layout reframing a widget). Use to_screen()/to_local() to convert
		# between that local space and real screen coordinates.
		self.view_offset:         tuple[int, int] = (0, 0)
		self.mouse_up_position:   list[int] = [0, 0]
		self.touch_position:      list[int] = [0, 0]
		self.touch_scroll_y:     float = 0
		self.touch_active:        bool = False
		self.touch_released:      bool = False
		self.active_touch_id = None
		self.trackpad_scroll_mode_until: float = 0.0
		self.scroll_debug_last_mode: str = ""
		self.scroll_debug_last_log: float = 0.0
		self.drag_mode:           bool = False
		self.quick_drag:          bool = False
		self.clicked:             bool = False

		self.key_del:             bool = False
		self.key_c_press:         bool = False
		self.key_v_press:         bool = False
		#self.key_f_press:        bool = False
		self.key_a_press:         bool = False
		self.key_s_press:         bool = False
		#self.key_t_press:        bool = False
		self.key_z_press:         bool = False
		self.key_x_press:         bool = False
		self.key_backspace_press: bool = False
		self.key_home_press:      bool = False
		self.key_end_press:       bool = False

		self.k_input:             bool = True
		self.key_return_press:    bool = False
		self.key_tab_press:       bool = False
		self.key_down_press:      bool = False
		self.key_up_press:        bool = False
		self.key_right_press:     bool = False
		self.key_left_press:      bool = False
		self.key_esc_press:       bool = False

		self.key_shift_down:      bool = False
		self.key_shiftr_down:     bool = False
		self.key_ctrl_down:       bool = False
		self.key_rctrl_down:      bool = False
		self.key_meta:            bool = False
		self.key_ralt:            bool = False
		self.key_lalt:            bool = False

		self.global_clicked:      bool = False

		self.media_key = ""
		self.input_text = ""
		self.key_focused = 0

	def to_screen(self, x: float, y: float) -> tuple[float, float]:
		"""Convert a point from the active local view space to real screen
		coordinates. Identity unless a view transform is active."""
		ox, oy = self.view_offset
		return (x + ox, y + oy)

	def to_local(self, x: float, y: float) -> tuple[float, float]:
		"""Convert a real screen point into the active local view space."""
		ox, oy = self.view_offset
		return (x - ox, y - oy)

	def test_shift(self, _value: int) -> bool:
		return self.key_shift_down or self.key_shiftr_down

	def m_key_play(self) -> None:
		self.media_key = "Play"
		self.gui.request_frame()

	def m_key_pause(self) -> None:
		self.media_key = "Pause"
		self.gui.request_frame()

	def m_key_stop(self) -> None:
		self.media_key = "Stop"
		self.gui.request_frame()

	def m_key_next(self) -> None:
		self.media_key = "Next"
		self.gui.request_frame()

	def m_key_previous(self) -> None:
		self.media_key = "Previous"
		self.gui.request_frame()

class KeyMap:

	def __init__(self, bag: StateBag, inp: Input) -> None:
		self.bag: StateBag = bag
		self.inp: Input = inp
		self.hits: list[str | sdl3.SDL_Scancode] = []  # The keys hit this frame
		self.maps: dict[str, list[tuple[str | sdl3.SDL_Scancode, list[str]]]] = {}  # Loaded from input.txt

	def load(self) -> None:
		path = self.bag.dirs.config_directory / "input.txt"
		with path.open(encoding="utf_8") as f:
			content = f.read().splitlines()
			for p in content:
				if len(p) == 0 or len(p) > 100:
					continue
				if p[0] == " " or p[0] == "#":
					continue

				items = p.split()
				if 1 < len(items) < 5:
					function = items[0]

					if items[1] in ("MB4", "MB5"):
						key = items[1]
					else:
						if self.bag.prefs.use_scancodes:
							key = sdl3.SDL_GetScancodeFromName(items[1].encode())
						else:
							key = sdl3.SDL_GetKeyFromName(items[1].encode())
						if key == 0:
							continue

					mod: list[str] = []

					if len(items) > 2:
						mod.append(items[2].lower())
					if len(items) > 3:
						mod.append(items[3].lower())

					if function in self.maps:
						self.maps[function].append((key, mod))
					else:
						self.maps[function] = [(key, mod)]

	def test(self, function: str) -> bool:
		inp = self.inp
		if not self.hits:
			return False
		if function not in self.maps:
			return False

		for code, mod in self.maps[function]:
			if code in self.hits:
				ctrl = (inp.key_ctrl_down or inp.key_rctrl_down) * 1
				shift = (inp.key_shift_down or inp.key_shiftr_down) * 10
				alt = (inp.key_lalt or inp.key_ralt) * 100

				if ctrl + shift + alt == ("ctrl" in mod) * 1 + ("shift" in mod) * 10 + ("alt" in mod) * 100:
					return True
		return False

class ColoursClass:
	"""Used to store colour values for UI elements

	These are changed for themes
	"""

	def grey(self, value: int) -> ColourRGBA:
		return ColourRGBA(value, value, value, 255)

	def alpha_grey(self, value: int) -> ColourRGBA:
		return ColourRGBA(255, 255, 255, value)

	def grey_blend_bg(self, value: int) -> ColourRGBA:
		return alpha_blend(ColourRGBA(255, 255, 255, value), self.box_background)

	def __init__(self) -> None:
		self.deco: str | None = None
		self.column_colours: dict[str, ColourRGBA] = {}
		self.column_colours_playing: dict[str, ColourRGBA] = {}

		self.last_album = ""
		self.link_text = ColourRGBA(100, 200, 252, 255)

		self.tb_line = self.grey(21)  # not currently used
		self.art_box = self.grey(24)

		self.volume_bar_background = self.grey(30)
		self.volume_bar_fill = self.grey(125)
		self.seek_bar_background = self.grey(30)
		self.seek_bar_fill = self.grey(80)

		self.tab_text_active = self.grey(230)
		self.tab_text = self.grey(215)
		self.tab_background = self.grey(25)
		self.tab_highlight = self.grey(40)
		self.tab_background_active = self.grey(45)

		self.title_text = ColourRGBA(190, 190, 190, 255)
		self.index_text = self.grey(70)
		self.time_text = self.grey(180)
		self.artist_text = ColourRGBA(195, 255, 104, 255)
		self.album_text = ColourRGBA(245, 240, 90, 255)

		self.index_playing = self.grey(190)
		self.artist_playing = ColourRGBA(195, 255, 104, 255)
		self.album_playing = ColourRGBA(245, 240, 90, 255)
		self.title_playing = self.grey(230)

		self.time_playing = ColourRGBA(180, 194, 107, 255)

		self.playlist_text_missing = self.grey(85)
		self.bar_time = self.grey(70)

		self.top_panel_background = self.grey(15)
		self.status_text_over: ColourRGBA | None = None
		self.status_text_normal: ColourRGBA | None = None


		self.side_panel_background = self.grey(18)
		self.lyrics_panel_background: ColourRGBA | None = None
		self.gallery_background = self.side_panel_background
		self.playlist_panel_background = self.grey(21)
		self.bottom_panel_colour = self.grey(15)

		self.row_playing_highlight = ColourRGBA(255, 255, 255, 4)
		self.row_select_highlight = ColourRGBA(255, 255, 255, 5)

		self.side_bar_line1 = self.grey(230)
		self.side_bar_line2 = self.grey(210)

		self.mode_button_off = self.grey(50)
		self.mode_button_over = self.grey(200)
		self.mode_button_active = self.grey(190)

		self.media_buttons_over = self.grey(220)
		self.media_buttons_active = self.grey(220)
		self.media_buttons_off = self.grey(55)

		self.star_line = ColourRGBA(100, 100, 100, 255)
		self.star_line_playing: ColourRGBA | None = None
		self.folder_title = ColourRGBA(130, 130, 130, 255)
		self.folder_line  = ColourRGBA(40, 40, 40, 255)

		self.scroll_colour = ColourRGBA(45, 45, 45, 255)

		self.level_1_bg   = ColourRGBA(0, 30, 0, 255)
		self.level_2_bg   = ColourRGBA(30, 30, 0, 255)
		self.level_3_bg   = ColourRGBA(30, 0, 0, 255)
		self.level_green  = ColourRGBA(20, 120, 20, 255)
		self.level_red    = ColourRGBA(190, 30, 30, 255)
		self.level_yellow = ColourRGBA(135, 135, 30, 255)

		self.vis_colour = self.grey(200)
		self.vis_bg = ColourRGBA(0, 0, 0, 255)

		self.menu_background: ColourRGBA | None = None  # self.grey(12)
		self.menu_highlight_background: ColourRGBA | None = None
		self.menu_text = ColourRGBA(230, 230, 230, 255)
		self.menu_text_disabled = self.grey(50)
		self.menu_icons = ColourRGBA(255, 255, 255, 25)
		self.menu_tab = self.grey(30)

		self.gallery_highlight = self.artist_playing

		self.status_info_text = ColourRGBA(245, 205, 0, 255)
		self.lyrics = self.grey(245)
		self.active_lyric = ColourRGBA(255, 210, 50, 255)

		self.corner_button        = ColourRGBA(255, 255, 255, 50)  # [60, 60, 60, 255]
		self.corner_button_active = ColourRGBA(255, 255, 255, 230)  # [230, 230, 230, 255]

		self.window_buttons_bg        = ColourRGBA(0, 0, 0, 50)
		self.window_buttons_bg_over   = ColourRGBA(255, 255, 255, 10)  # [80, 80, 80, 120]
		self.window_buttons_icon_over = ColourRGBA(255, 255, 255, 60)
		self.window_button_icon_off   = ColourRGBA(255, 255, 255, 40)
		self.window_button_x_on: ColourRGBA | None = None
		self.window_button_x_off = self.window_button_icon_off

		self.message_box_bg = self.grey(0)
		self.message_box_text = self.grey(230)

		self.lm = False

		self.pulse_colour = ColourRGBA(244, 212, 66, 255)

		self.mini_mode_background = ColourRGBA(19, 19, 19, 255)
		self.mini_mode_border     = ColourRGBA(45, 45, 45, 255)
		self.mini_mode_text_1     = ColourRGBA(255, 255, 255, 240)
		self.mini_mode_text_2     = ColourRGBA(255, 255, 255, 77)

		self.queue_drag_indicator_colour = ColourRGBA(200, 50, 240, 255)

		self.playlist_box_background = self.side_panel_background

		self.bar_title_text = None

		self.corner_icon = ColourRGBA(40, 40, 40, 255)
		self.queue_background: ColourRGBA | None = None  # self.side_panel_background #self.grey(18) # 18
		self.queue_card_background = self.grey(23)

		self.column_bar_background = ColourRGBA(30, 30, 30, 255)
		self.column_grip           = ColourRGBA(255, 255, 255, 14)
		self.column_bar_text       = ColourRGBA(240, 240, 240, 255)

		self.window_frame = ColourRGBA(30, 30, 30, 255)

		self.box_background = ColourRGBA(16, 16, 16, 255)
		self.box_border = rgb_add_hls(self.box_background, 0, 0.17, 0)
		self.box_text_border = rgb_add_hls(self.box_background, 0, 0.1, 0)
		self.box_text_label = rgb_add_hls(self.box_background, 0, 0.32, -0.1)
		self.box_check_border = ColourRGBA(255, 255, 255, 18)

		self.box_title_text = self.grey(245)
		self.box_text = self.grey(240)
		self.box_sub_text = self.grey_blend_bg(225)
		self.box_input_text = self.grey(225)
		self.box_button_text_highlight = self.grey(250)
		self.box_button_text = self.grey(225)
		self.box_button_background = alpha_blend(ColourRGBA(255, 255, 255, 11), self.box_background)
		self.box_thumb_background: ColourRGBA | None = None
		self.box_button_background_highlight = alpha_blend(ColourRGBA(255, 255, 255, 20), self.box_background)

		self.artist_bio_background = ColourRGBA(27, 27, 27, 255)
		self.artist_bio_text       = ColourRGBA(230, 230, 230, 255)

		# Theme-supplied alphas of the fills the art background shows through,
		# filled in by post_config
		self.base_alpha: dict[str, int] = {}

	# The art background draws underneath the UI, so these fills are made
	# translucent to let it show through. Panels take the bulk of it; the
	# smaller furniture sitting on them lets less through.
	art_bg_panel_colours = (
		"playlist_panel_background",
		"side_panel_background",
		"top_panel_background",
		"bottom_panel_colour",
		"gallery_background",
		"queue_background",
		"playlist_box_background",
		"lyrics_panel_background",
	)
	art_bg_element_colours = (
		"tab_background",
		"tab_background_active",
		"seek_bar_background",
		"volume_bar_background",
		"column_bar_background",
		"folder_line",
	)

	def apply_transparency(self, full: bool = False) -> None:
		"""Translucent panel fills for compositor window transparency.

		Accent mode leaves the tracklist area opaque; full mode makes every
		panel see-through."""
		self.top_panel_background.a = 140
		self.side_panel_background.a = 140
		self.art_box.a = 100
		self.window_frame.a = 100
		self.bottom_panel_colour.a = 200

		if full:
			for name in (
				"playlist_panel_background",
				"gallery_background",
				"queue_background",
				"playlist_box_background",
				"lyrics_panel_background",
			):
				c = getattr(self, name, None)
				if c is not None:
					c.a = 175

	def post_config(self) -> None:
		if self.box_thumb_background is None:
			self.box_thumb_background = alpha_mod(self.box_button_background, 175)

		if self.lyrics_panel_background is None:
			self.lyrics_panel_background = self.side_panel_background
		if self.status_text_over is None:
			self.status_text_over = rgb_add_hls(self.top_panel_background, 0, 0.83, 0)
		if self.status_text_normal is None:
			self.status_text_normal = rgb_add_hls(self.top_panel_background, 0, 0.30, -0.15)

		# Pre calculate alpha blend for spec background
		self.vis_bg.r = int(0.05 * 255 + (1 - 0.05) * self.top_panel_background.r)
		self.vis_bg.g = int(0.05 * 255 + (1 - 0.05) * self.top_panel_background.g)
		self.vis_bg.b = int(0.05 * 255 + (1 - 0.05) * self.top_panel_background.b)
		self.vis_bg.a = int(0.05 * 255 + (1 - 0.05) * self.top_panel_background.a)

		self.message_box_bg = self.box_background
		self.sys_tab_bg = self.tab_background
		self.sys_tab_hl = self.tab_background_active
		self.toggle_box_on = self.folder_title
		self.toggle_box_on = ColourRGBA(255, 150, 100, 255)
		self.toggle_box_on = self.artist_playing
		if colour_value(self.toggle_box_on) < 150:
			self.toggle_box_on = ColourRGBA(160, 160, 160, 255)
		# self.time_sub = [255, 255, 255, 80]#alpha_blend(ColourRGBA(255, 255, 255, 80), self.bottom_panel_colour)

		self.time_sub = rgb_add_hls(self.bottom_panel_colour, 0, 0.29, 0)

		if test_lumi(self.bottom_panel_colour) < 0.2:
			# self.time_sub = [0, 0, 0, 80]
			self.time_sub = rgb_add_hls(self.bottom_panel_colour, 0, -0.15, -0.3)
		elif test_lumi(self.bottom_panel_colour) < 0.8:
			self.time_sub = ColourRGBA(255, 255, 255, 135)
		# self.time_sub = self.mode_button_off

		if self.bar_title_text is None:
			self.bar_title_text = self.side_bar_line1

		self.gallery_artist_line = alpha_mod(self.side_bar_line2, 120)

		if self.menu_highlight_background is None:
			self.menu_highlight_background = ColourRGBA(40, 40, 40, 255)

		if not self.queue_background:
			self.queue_background = self.side_panel_background

		if test_lumi(self.queue_background) > 0.8:
			self.queue_card_background = alpha_blend(ColourRGBA(255, 255, 255, 10), self.queue_background)

		if self.menu_background is None and not self.lm:
			self.menu_background = self.bottom_panel_colour

		self.message_box_text = self.box_text
		self.message_box_border = self.box_border

		if self.window_button_x_on is None:
			self.window_button_x_on = self.artist_playing

		if test_lumi(self.column_bar_background) < 0.4:
			self.column_bar_text = ColourRGBA(40, 40, 40, 200)
			self.column_grip     = ColourRGBA(255, 255, 255, 20)

		# Snapshot the alphas the theme actually asked for. The art background
		# scales these down each frame and must clamp against them: a theme
		# whose seek bar or tabs are deliberately translucent (Carbon's seek
		# background is white at alpha 60) must not be forced opaque when no
		# art background is showing.
		self.base_alpha = {}
		for name in self.art_bg_panel_colours + self.art_bg_element_colours:
			colour = getattr(self, name, None)
			if colour is not None:
				self.base_alpha[name] = colour.a

	def light_mode(self) -> None:
		self.lm = True
		self.star_line_playing = ColourRGBA(255, 255, 255, 255)
		self.sys_tab_bg = self.grey(25)
		self.sys_tab_hl = self.grey(45)
		# self.box_background = self.grey(30)
		self.toggle_box_on = self.tab_background_active
		# if colour_value(self.tab_background_active) < 250:
		#	self.toggle_box_on = [255, 255, 255, 200]

		# self.time_sub = [0, 0, 0, 200]
		self.gallery_artist_line = self.grey(40)
		# self.bar_title_text = self.grey(30)
		self.status_text_normal = self.grey(70)
		self.status_text_over = self.grey(40)
		self.status_info_text = ColourRGBA(40, 40, 40, 255)

		# self.bar_title_text = self.grey(255)
		self.vis_bg = ColourRGBA(235, 235, 235, 255)
		# self.menu_background = [240, 240, 240, 250]
		# self.menu_text = self.grey(40)
		# self.menu_text_disabled = self.grey(180)
		# self.menu_highlight_background = [200, 200, 200, 250]
		if self.menu_background is None:
			self.menu_background = ColourRGBA(15, 15, 15, 250)
		if not self.menu_icons:
			self.menu_icons = ColourRGBA(0, 0, 0, 40)

		# self.menu_background = [40, 40, 40, 250]
		# self.menu_text = self.grey(220)
		# self.menu_text_disabled = self.grey(120)
		# self.menu_highlight_background = [120, 80, 220, 250]

		self.corner_button = self.grey(160)
		self.corner_button_active = self.grey(35)
		# self.window_buttons_bg = ColourRGBA(0, 0, 0, 5]
		self.message_box_bg = ColourRGBA(245, 245, 245, 255)
		self.message_box_text = self.grey(20)
		self.message_box_border = self.grey(40)
		self.gallery_background = self.grey(230)
		self.gallery_artist_line = self.grey(40)
		self.pulse_colour = ColourRGBA(212, 66, 244, 255)


class MenuIcon:

	def __init__(self, asset: WhiteModImageAsset | LoadImageAsset) -> None:
		self.asset = asset
		self.colour = ColourRGBA(170, 170, 170, 255)
		self.base_asset = None
		self.base_asset_mod = None
		self.colour_callback = None
		self.mode_callback = None
		self.xoff = 0
		self.yoff = 0


def asset_loader(
	bag: StateBag, loaded_asset_dc: dict[str, WhiteModImageAsset | LoadImageAsset], name: str, mod: bool = False,
) -> WhiteModImageAsset | LoadImageAsset:
	if name in loaded_asset_dc:
		return loaded_asset_dc[name]

	target = str(bag.dirs.scaled_asset_directory / name)
	if mod:
		item = WhiteModImageAsset(bag=bag, path=target, scale_name=name)
	else:
		item = LoadImageAsset(bag=bag, path=target, scale_name=name)
	loaded_asset_dc[name] = item
	return item
