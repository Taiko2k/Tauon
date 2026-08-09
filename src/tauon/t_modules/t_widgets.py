"""Low-level drawing, field, scroll, and feedback widgets."""

from __future__ import annotations

import copy
import io
import logging
from collections.abc import Callable
from ctypes import c_float, pointer
from typing import TYPE_CHECKING, Any, Protocol

import sdl3
from PIL import Image, ImageDraw, ImageFilter

from tauon.t_modules.t_extra import (
	TestTimer,
	Timer,
	point_proximity_test,
	window_is_focused,
)
from tauon.t_modules.t_models import ColourRGBA, StarRecord, TrackClass
from tauon.t_modules.t_state import ColoursClass, GuiVar, Input
from tauon.t_modules.t_stars import StarStore

if TYPE_CHECKING:
	from tauon.t_modules.t_draw import TDraw


class _WidgetFields(Protocol):
	def add(self, rect: object, callback: Callable[..., object] | None = None) -> None: ...


class _WidgetPlayer(Protocol):
	star_store: StarStore
	playlist_view_position: int


class _WidgetApp(Protocol):
	gui: GuiVar
	inp: Input
	ddt: Any
	coll: Callable[[object], bool]
	fields: _WidgetFields
	colours: ColoursClass
	window_size: list[int]
	renderer: Any
	pctl: _WidgetPlayer
	t_window: Any
	input_sdl: Any
	scroll_timer: Timer
	show_message: Callable[..., object]
	star_store: StarStore


class Drawing:
	def __init__(self, tauon: _WidgetApp, pctl: _WidgetPlayer) -> None:
		self.tauon: _WidgetApp      = tauon
		self.gui: GuiVar        = tauon.gui
		self.inp: Input        = tauon.inp
		self.ddt: TDraw        = tauon.ddt
		self.coll       = tauon.coll
		self.fields: _WidgetFields     = tauon.fields
		self.colours: ColoursClass    = tauon.colours
		self.star_store: StarStore = pctl.star_store

	def button(
		self, text: str, x: int, y: int, w: int | None = None, h: int | None = None, font: int = 212, text_highlight_colour: ColourRGBA | None = None, text_colour: ColourRGBA | None = None,
		background_colour: ColourRGBA | None = None, background_highlight_colour: ColourRGBA | None = None, press: bool | None = None, tooltip: str = "") -> bool:
		"""PSA for anyone making a new button function: use fields.add(rect) to make the gui
		refresh when you pan the mouse over it
		"""
		if w is None:
			w = self.ddt.get_text_w(text, font) + 18 * self.gui.scale
		if h is None:
			h = self.ddt.get_text_w(text, font, True) + 6*self.gui.scale

		rect = (x, y, w, h)
		self.fields.add(rect)

		if text_highlight_colour is None:
			text_highlight_colour = self.colours.box_button_text_highlight
		if text_colour is None:
			text_colour = self.colours.box_button_text
		if background_colour is None:
			background_colour = self.colours.box_button_background
		if background_highlight_colour is None:
			background_highlight_colour = self.colours.box_button_background_highlight

		click = False
		text_y = rect[1] + rect[3] / 2 - 9 * self.gui.scale

		if press is None:
			press = self.inp.mouse_click

		if self.coll(rect):
			if tooltip:
				self.tauon.tool_tip.test(x + 15 * self.gui.scale, y - 28 * self.gui.scale, tooltip)
			self.ddt.rect(rect, background_highlight_colour)

			# if background_highlight_colour[3] != 255:
			#	 background_highlight_colour = None

			self.ddt.text(
				(rect[0] + int(rect[2] / 2), text_y, 2), text, text_highlight_colour, font, bg=background_highlight_colour)
			if press:
				click = True
		else:
			self.ddt.rect(rect, background_colour)
			if background_highlight_colour.a != 255:
				background_colour = None
			self.ddt.text(
				(rect[0] + int(rect[2] / 2), text_y, 2), text, text_colour, font, bg=background_colour)
		return click

class DropShadow:

	def __init__(self, tauon: _WidgetApp) -> None:
		self.gui      = tauon.gui
		self.ddt      = tauon.ddt
		self.renderer = tauon.renderer
		self.readys = {}
		self.underscan = int(15 * tauon.gui.scale)
		self.radius = 4
		self.grow = 2 * tauon.gui.scale
		self.opacity = 90

	def prepare(self, w: int, h: int) -> None:
		fh = h + self.underscan
		fw = w + self.underscan

		im = Image.new("RGBA", (round(fw), round(fh)), 0x00000000)
		d = ImageDraw.Draw(im)
		d.rectangle(((self.underscan, self.underscan), (w + 2, h + 2)), fill="black")

		im = im.filter(ImageFilter.GaussianBlur(self.radius))

		g = io.BytesIO()
		g.seek(0)
		im.save(g, "PNG")
		g.seek(0)


		s_image = self.ddt.load_image(g)

		c = sdl3.SDL_CreateTextureFromSurface(self.renderer, s_image)
		sdl3.SDL_SetTextureAlphaMod(c, self.opacity)

		tex_w = pointer(c_float(0))
		tex_h = pointer(c_float(0))
		sdl3.SDL_GetTextureSize(c, tex_w, tex_h)

		dst = sdl3.SDL_FRect(0, 0)
		dst.w = int(tex_w.contents.value)
		dst.h = int(tex_h.contents.value)

		sdl3.SDL_DestroySurface(s_image)
		g.close()
		im.close()

		unit = (dst, c)
		self.readys[(w, h)] = unit

	def render(self, x: int, y: int, w: int, h: int) -> None:
		if (w, h) not in self.readys:
			self.prepare(w, h)

		unit = self.readys[(w, h)]
		unit[0].x = round(x) - round(self.underscan)
		unit[0].y = round(y) - round(self.underscan)
		sdl3.SDL_RenderTexture(self.renderer, unit[1], None, unit[0])

class ToolTip:

	def __init__(self, tauon: _WidgetApp) -> None:
		self.gui     = tauon.gui
		self.ddt     = tauon.ddt
		self.colours = tauon.colours
		self.text = ""
		self.h = 24 * self.gui.scale
		self.w = 62 * self.gui.scale
		self.x = 0
		self.y = 0
		self.timer = Timer()
		self.trigger = 1.1
		self.font = 13
		self.called = False
		self.a = False

	def test(self, x: float, y: float, text: str) -> None:
		if self.text != text or x != self.x or y != self.y:
			self.text = text
			# self.timer.set()
			self.a = False

			self.x = x
			self.y = y
			self.w = self.ddt.get_text_w(text, self.font) + 20 * self.gui.scale
			self.h = 24 * self.gui.scale

		self.called = True

		if self.a is False:
			self.timer.set()
			self.gui.frame_callback_list.append(TestTimer(self.trigger))
		self.a = True

	def render(self) -> None:
		if self.called is True:
			if self.timer.get() > self.trigger:
				self.ddt.rect((self.x, self.y, self.w, self.h), self.colours.box_button_background)
				# ddt.rect((self.x, self.y, self.w, self.h), self.colours.grey(45))
				self.ddt.text(
					(self.x + int(self.w / 2), self.y + 4 * self.gui.scale, 2), self.text,
					self.colours.menu_text, self.font, bg=self.colours.box_button_background)
			else:
				# self.gui.update += 1
				pass
		else:
			self.timer.set()
			self.a = False
		self.called = False

class ToolTip3:

	def __init__(self, tauon: _WidgetApp) -> None:
		self.inp     = tauon.inp
		self.ddt     = tauon.ddt
		self.gui     = tauon.gui
		self.pctl    = tauon.pctl
		self.coll    = tauon.coll
		self.colours = tauon.colours
		self.x = 0
		self.y = 0
		self.text = ""
		self.rect: list[int] = []
		self.font = None
		self.show = False
		self.width = 0
		self.height = 24 * self.gui.scale
		self.timer = Timer()
		self.pl_position = 0
		self.click_exclude_point = (0, 0)

	def set(self, x: int, y: int, text: str, font, rect: list[int]) -> None:
		y -= round(11 * self.gui.scale)
		if self.show is False or self.y != y or x != self.x or self.pl_position != self.pctl.playlist_view_position:
			self.timer.set()

		if point_proximity_test(self.click_exclude_point, self.inp.mouse_position, 20 * self.gui.scale):
			self.timer.set()
			return

		if self.inp.mouse_click:
			self.click_exclude_point = copy.copy(self.inp.mouse_position)
			self.timer.set()
			return

		self.x = x
		self.y = y
		self.text = text
		self.font = font
		self.show = True
		self.rect = rect
		self.pl_position = self.pctl.playlist_view_position

	def render(self) -> None:
		if not self.show:
			return

		if not point_proximity_test(self.click_exclude_point, self.inp.mouse_position, 20 * self.gui.scale):
			self.click_exclude_point = (0, 0)

		if not self.coll(
				self.rect) or self.inp.mouse_click or self.gui.level_2_click or self.pl_position != self.pctl.playlist_view_position:
			self.show = False

		self.gui.frame_callback_list.append(TestTimer(0.02))

		if self.timer.get() < 0.6:
			return

		w = self.ddt.get_text_w(self.text, 312) + self.height
		x = self.x  # - int(self.width / 2)
		y = self.y
		h = self.height

		border = 1 * self.gui.scale

		self.ddt.rect((x - border, y - border, w + border * 2, h + border * 2), self.colours.grey(60))
		self.ddt.rect((x, y, w, h), self.colours.menu_background)
		p = self.ddt.text(
			(x + int(w / 2), y + 3 * self.gui.scale, 2), self.text, self.colours.menu_text, 312, bg=self.colours.menu_background)

		if not self.coll(self.rect):
			self.show = False

class Fields:
	def __init__(self, tauon: _WidgetApp) -> None:
		self.tauon = tauon
		self.coll  = tauon.coll
		self.id = []
		self.last_id = []

		self.field_array = []
		self.force = False

	def add(self, rect, callback=None) -> None:
		# Honour the active view transform so a widget rendering in a local view
		# space registers its hover fields in real screen coordinates.
		ox, oy = self.tauon.inp.view_offset
		if ox or oy:
			rect = (rect[0] + ox, rect[1] + oy, rect[2], rect[3])
		self.field_array.append((rect, callback))

	def test(self) -> bool:
		if self.force:
			self.force = False
			return True

		self.last_id = self.id
		#logging.info(len(self.id))
		self.id = []

		for f in self.field_array:
			if self.coll(f[0]):
				self.id.append(1)  # += "1"
				if f[1] is not None:  # Call callback if present
					f[1]()
			else:
				self.id.append(0)  # += "0"

		return self.last_id != self.id

	def clear(self) -> None:
		self.field_array = []

class ScrollBox:

	def __init__(self, tauon: _WidgetApp, pctl: _WidgetPlayer) -> None:
		self.tauon     = tauon
		self.pctl      = pctl
		self.gui       = tauon.gui
		self.inp       = tauon.inp
		self.ddt       = tauon.ddt
		self.coll      = tauon.coll
		self.fields    = tauon.fields
		self.colours   = tauon.colours
		self.t_window  = tauon.t_window
		self.input_sdl = tauon.input_sdl
		self.held = False
		self.slide_hold = False
		self.source_click_y = 0
		self.source_bar_y = 0
		self.direction_lock = -1
		self.d_position = 0

	def draw(
		self, x: int, y: int, w: int, h: int, value: float, max_value: float, force_dark_theme: bool = False, click: bool | None = None, r_click: bool = False, jump_distance: int = 4, extend_field: int = 0) -> float:
		if max_value <= 0:
			return 0

		if click is None:
			click = self.inp.mouse_click

		bar_height = round(90 * self.gui.scale)

		if h > 400 * self.gui.scale and max_value < 20:
			bar_height = round(180 * self.gui.scale)

		bg     = ColourRGBA(255, 255, 255, 7)
		fg     = ColourRGBA(255, 255, 255, 30)
		fg_h   = ColourRGBA(255, 255, 255, 40)
		fg_off = ColourRGBA(255, 255, 255, 15)

		if self.colours.lm and not force_dark_theme:
			bg     = ColourRGBA(0, 0, 0, 15)
			fg_off = ColourRGBA(0, 0, 0, 30)
			fg     = ColourRGBA(0, 0, 0, 60)
			fg_h   = ColourRGBA(0, 0, 0, 70)

		self.ddt.rect((x, y, w, h), bg)

		half = bar_height // 2

		ratio = value / max_value

		mi = y + half
		mo = y + h - half
		distance = mo - mi
		position = round(distance * ratio)

		fw = w + extend_field
		fx = x - extend_field

		if self.coll((fx, y, fw, h)):
			if self.inp.mouse_down:
				self.gui.request_frame()

			if r_click:
				p = self.inp.mouse_position[1] - half - y
				p = max(0, p)

				range = h - bar_height
				p = min(p, range)

				per = p / range

				value = round(max_value * per)

				ratio = value / max_value

				mi = y + half
				mo = y + h - half
				distance = mo - mi
				position = round(distance * ratio)

			in_bar = False
			if self.coll((x, mi + position - half, w, bar_height)):
				in_bar = True
				if click:
					self.held = True

					# p_y = pointer(c_int(0))
					# sdl3.SDL_GetGlobalMouseState(None, p_y)
					self.input_sdl.mouse_capture_want = True
					self.source_click_y = self.inp.mouse_position[1]
					self.source_bar_y = position

			if self.pctl.playlist_view_position < 0:
				self.pctl.playlist_view_position = 0
			elif self.inp.mouse_down and not self.held:
				if click and not in_bar:
					self.slide_hold = True
					self.direction_lock = 1
					if self.inp.mouse_position[1] - y < position:
						self.direction_lock = 0

					self.d_position = value / max_value

				if self.slide_hold:
					if (self.direction_lock == 1 and self.inp.mouse_position[1] - y < position + half) or \
							(self.direction_lock == 0 and self.inp.mouse_position[1] - y > position + half):
						pass
					else:

						tt = self.tauon.scroll_timer.hit()
						if tt > 0.1:
							tt = 0

						flip = -1
						if self.direction_lock:
							flip = 1

						self.d_position = min(max(self.d_position + (((tt * jump_distance) / max_value) * flip), 0), 1)
			else:
				self.slide_hold = False

		if (self.held and self.inp.mouse_up) or not self.inp.mouse_down:
			self.held = False

		if self.held and not window_is_focused(self.t_window):
			self.held = False

		if self.held:
			self.input_sdl.mouse_capture_want = True
			new_y = self.inp.mouse_position[1]
			self.gui.request_frame()

			offset = new_y - self.source_click_y

			position = self.source_bar_y + offset

			position = max(position, 0)
			position = min(position, distance)

			ratio = position / distance
			value = max_value * ratio

		colour = fg_off
		rect = (x, mi + position - half, w, bar_height)
		self.fields.add(rect)
		if self.coll(rect):
			colour = fg
		if self.held:
			colour = fg_h

		self.ddt.rect(rect, colour)

		if self.slide_hold:
			return round(max_value * self.d_position)

		return value

class Fader:

	def __init__(self, tauon: _WidgetApp) -> None:
		self.tauon = tauon
		self.window_size = tauon.window_size

		self.total_timer = Timer()
		self.timer = Timer()
		self.ani_duration = 0.3
		self.state = 0  # 0 = Want off, 1 = Want fade on
		self.a = 0  # The fade progress (0-1)

	def render(self) -> None:
		if self.total_timer.get() > self.ani_duration:
			self.a = self.state
		elif self.state == 0:
			t = self.timer.hit()
			self.a -= t / self.ani_duration
			self.a = max(0, self.a)
		elif self.state == 1:
			t = self.timer.hit()
			self.a += t / self.ani_duration
			self.a = min(1, self.a)

		rect = [0, 0, self.window_size[0], self.window_size[1]]
		self.tauon.ddt.rect(rect, ColourRGBA(0, 0, 0, int(110 * self.a)))

		if self.a not in (0, 1):
			self.tauon.gui.request_frame()

	def rise(self) -> None:
		self.state = 1
		self.timer.hit()
		self.total_timer.set()

	def fall(self) -> None:
		if self.state == 0:
			return
		self.state = 0
		self.timer.hit()
		self.total_timer.set()

class EdgePulse:

	def __init__(self, tauon: _WidgetApp) -> None:
		self.gui     = tauon.gui
		self.ddt     = tauon.ddt
		self.colours = tauon.colours
		self.timer = Timer()
		self.timer.force_set(10)
		self.ani_duration = 0.5

	def render(self, x: int, y: int, w: int, h: int, r: int = 200, g: int = 120, b: int = 0) -> bool:
		r = self.colours.pulse_colour.r
		g = self.colours.pulse_colour.g
		b = self.colours.pulse_colour.b
		time = self.timer.get()
		if time < self.ani_duration:
			alpha = 255 - int(255 * (time / self.ani_duration))
			self.ddt.rect((x, y, w, h), ColourRGBA(r, g, b, alpha))
			self.gui.request_frame()
			return True
		return False

	def pulse(self) -> None:
		self.timer.set()

class EdgePulse2:

	def __init__(self, tauon: _WidgetApp) -> None:
		self.inp     = tauon.inp
		self.ddt     = tauon.ddt
		self.gui     = tauon.gui
		self.colours = tauon.colours
		self.timer = Timer()
		self.timer.force_set(10)
		self.ani_duration = 0.22

	def render(self, x: int, y: int, w: int, h: int, bottom: bool = False) -> bool | None:
		time = self.timer.get()
		if time < self.ani_duration:
			if bottom:
				if self.inp.mouse_wheel > 0:
					self.timer.force_set(10)
					return None
			elif self.inp.mouse_wheel < 0:
				self.timer.force_set(10)
				return None

			alpha = 30 - int(25 * (time / self.ani_duration))
			h_off = (h // 5) * (time / self.ani_duration) * 4

			if self.colours.lm:
				colour = ColourRGBA(0, 0, 0, alpha)
			else:
				# colour = ColourRGBA(255, 255, 255, alpha)
				colour = self.colours.pulse_colour

			if not bottom:
				self.ddt.rect((x, y, w, h - h_off), colour)
			else:
				self.ddt.rect((x, y - (h - h_off), w, h - h_off), colour)
			self.gui.request_frame()
			return True
		return False

	def pulse(self) -> None:
		self.timer.set()

class Undo:

	def __init__(self, tauon: _WidgetApp) -> None:
		self.gui: GuiVar = tauon.gui
		self.pctl: Any = tauon.pctl
		self.star_store: StarStore = tauon.star_store
		self.show_message = tauon.show_message
		self.e: list[
			tuple[str, TrackClass, StarRecord | None, int, TrackClass, StarRecord | None, int] |
			tuple[str, list[int]] |
			tuple[str, int, list[tuple[int, int]]]
			] = []

	def undo(self) -> None:
		if not self.e:
			self.show_message(_("There are no more steps to undo."))
			return

		job = self.e.pop()

		if job[0] == "playlist":
			self.pctl.multi_playlist.append(job[1])
			self.pctl.switch_playlist(len(self.pctl.multi_playlist) - 1)
		elif job[0] == "tracks":
			uid = job[1]
			li = job[2]

			for i, playlist in enumerate(self.pctl.multi_playlist):
				if playlist.uuid_int == uid:
					pl = playlist.playlist_ids
					self.pctl.switch_playlist(i)
					break
			else:
				logging.info("No matching playlist ID to restore tracks to")
				return

			for i, ref in reversed(li):
				if i > len(pl):
					logging.error("restore track error - playlist not correct length")
					continue
				pl.insert(i, ref)

				if not self.pctl.playlist_view_position < i < self.pctl.playlist_view_position + self.gui.playlist_view_length:
					self.pctl.playlist_view_position = i
					logging.debug("Position changed by undo")
		elif job[0] == "ptt":
			j, fr, fr_s, fr_scr, to, to_s, to_scr = job
			self.star_store.insert(fr.index, fr_s)
			self.star_store.insert(to.index, to_s)
			to.lfm_scrobbles = to_scr
			fr.lfm_scrobbles = fr_scr

		self.gui.request_tracklist_redraw()

	def bk_playlist(self, pl_index: int) -> None:
		self.e.append(("playlist", self.pctl.multi_playlist[pl_index]))

	def bk_tracks(self, pl_index: int, indis: list[tuple[int, int]]) -> None:
		uid = self.pctl.multi_playlist[pl_index].uuid_int
		self.e.append(("tracks", uid, indis))

	def bk_playtime_transfer(self, fr: TrackClass, fr_s: StarRecord | None, fr_scr: int, to: TrackClass, to_s: StarRecord | None, to_scr: int) -> None:
		self.e.append(("ptt", fr, fr_s, fr_scr, to, to_s, to_scr))
