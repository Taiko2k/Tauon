"""Low-level text input and editing widgets."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol

import sdl3

from tauon.t_modules.t_models import ColourRGBA
from tauon.t_modules.t_state import GuiVar, Input

if TYPE_CHECKING:
	from tauon.t_modules.t_draw import TDraw


class _TextFields(Protocol):
	def add(self, rect: object, callback: Callable[..., object] | None = None) -> None: ...


class _TextApp(Protocol):
	gui: GuiVar
	inp: Input
	ddt: Any
	coll: Callable[[object], bool]
	fields: _TextFields
	renderer: Any
	t_window: Any


class MultiLineTextBox:
	cursor = True

	def __init__(self, tauon: _TextApp) -> None:
		self.tauon:    _TextApp = tauon
		self.coll     = tauon.coll
		self.ddt:      TDraw = tauon.ddt
		self.gui:     GuiVar = tauon.gui
		self.inp:      Input = tauon.inp
		self.fields:  _TextFields = tauon.fields
		self.t_window = tauon.t_window
		self.renderer = tauon.renderer
		self.text: str = ""
		self.lines: list[str] = []
		self.text_height: int = 0
		self.visible_lines: list[str] = [] # lines as they are displayed with text wrapping
		self.line_counts: dict[int, int] = {} # get from cursor position to line number
		self.line_ys: list[int] = 0
		self.cursor_position: int = 0
		self.selection: int = 0
		self.offset: int = 0
		self.temp_x_pos: int | None = None
		self.down_lock: bool = False
		self.paste_text: str = ""

		self.x: int
		self.y: int
		self.font: int
		self.known_window_size: tuple[int] = (0,0)
		self.known_scale: float = self.gui.scale


	def initialize(self, x: int, y: int, width: int, height: int) -> None:
		gui = self.gui
		if width == 0:
			width = round(2000*gui.scale)
		if height == 0:
			height = round(20000*gui.scale)
		try:
			sdl3.SDL_DestroyTexture(self.text_box_canvas)
		except AttributeError:
			pass # just means we're creating it 4 the first time
		self.text_box_canvas_rect = sdl3.SDL_FRect(0, 0, width, height)
		self.text_box_canvas_hide_rect = sdl3.SDL_FRect(0, 0, width, height)
		self.text_box_canvas = sdl3.SDL_CreateTexture(
			self.renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET, round(self.text_box_canvas_rect.w), round(self.text_box_canvas_rect.h))
		sdl3.SDL_SetTextureBlendMode(self.text_box_canvas, sdl3.SDL_BLENDMODE_BLEND)
		self.x = x
		self.y = y


	def map_lines(self, width: int) -> None:
		"""this function has been lightly Sloptimized™"""
		self.line_ys = []
		self.visible_lines = []
		self.line_counts = {}
		throwaway, self.text_height = self.ddt.get_text_wh(_("?"), self.font, 200)
		count = len(self.text)
		last_count = None
		for i, line in enumerate(self.ddt.get_wrapped_lines(self.text, self.font, width)):
			count -= len(line)
			self.visible_lines.append(line)
			self.line_ys.append(i * self.text_height)
			self.line_counts[count] = (i,True)
			if last_count:
				# we have to track which lines start with a newline character vs which are from text wrapping
				# so that we can correctly place the text cursor at the start or end of every line
				self.line_counts[last_count] = (self.line_counts[last_count][0], line.startswith('\n'))
			last_count = count
		self.known_scale = self.gui.scale
		self.known_window_size = tuple(self.gui.window_size)


	def which_line_by_y(self, y_position: int) -> int:
		return min(len(self.line_ys)-1, round(y_position/self.text_height))


	def which_line_by_char(self, char: int) -> int:
		inexact = False
		while char > 0:
			try:
				if inexact or self.line_counts[char][1]:
					return self.line_counts[char][0]
				# inexact helps place the cursor correctly when it's AT a line break
				return self.line_counts[char][0] + 1
			except KeyError:
				inexact = True
				char -= 1
		return len(self.visible_lines)-1


	def _get_suffix_lengths(self) -> list[int]:
		"""this function is 100% Genuine Slop™"""
		key_id = id(self.visible_lines)
		if getattr(self, '_suffix_cache_id', None) != key_id:
			lengths = [0] * (len(self.visible_lines) + 1)
			total = 0
			for i in range(len(self.visible_lines) - 1, -1, -1):
				total += len(self.visible_lines[i])
				lengths[i] = total
			self._suffix_lengths = lengths
			self._suffix_cache_id = key_id
		return self._suffix_lengths

	def partial_line_from_char(self, char: int) -> str:
		"""this function has been Sloptimized™"""
		line = self.which_line_by_char(char)
		try:
			line_text = self.visible_lines[line]
		except IndexError as e:
			if line == -1:
				self.text_height = 0 # signal to regen lists etc
				return ''
			else:
				logging.error(e) # this should be impossible.
		suffix_after = self._get_suffix_lengths()[line + 1] if line + 1 < len(self.visible_lines) + 1 else 0
		r = char - suffix_after
		cut = len(line_text) - r
		if line_text.startswith("\n"):
			return line_text[1:cut]
		return line_text[:cut]


	def set_cursor_from_click(self, scroll: int, selection: bool, in_pos: tuple[int,int] | None = None) -> None:
		"""this function has been Sloptimized™"""
		if in_pos is None:
			in_pos = self.inp.mouse_position

		line = self.which_line_by_y(in_pos[1] - self.y + scroll - 0.25 * self.text_height)
		temp_total = sum(len(tally) for tally in self.visible_lines[line+1:])

		try:
			text = self.visible_lines[line]
		except IndexError as e:
			if len(self.visible_lines) == 0:
				if selection:
					self.selection = 0
				else:
					self.cursor_position = 0
				return
			else:
				logging.error(e)
		meas = text.lstrip('\n')

		x_in_line = in_pos[0] - self.x

		if x_in_line <= 0:
			out_val = temp_total + len(meas)
		else:
			full, char_index, trailing = self.ddt.measure_and_locate(meas, self.font, x_in_line)
			if x_in_line >= full:
				out_val = temp_total
			else:
				temp = len(meas) - char_index - (1 if trailing else 0)
				out_val = temp + temp_total

		if selection:
			self.selection = out_val
		else:
			self.cursor_position = out_val


	def pixel_position_from_cursor_position(self, selection: bool = False) -> tuple[int, int]:
		if selection:
			pos = self.selection
		else:
			pos = self.cursor_position
		line = self.which_line_by_char(pos)

		if pos == 0:
			width = self.ddt.get_text_w(self.text.split('\n')[-1], self.font)
		else:
			width = self.ddt.get_text_w(self.partial_line_from_char(pos), self.font)
		return width,line*self.text_height


	def switch_lines(self, scroll: int, up: bool) -> None:
		"""up and down arrow keys"""
		pos = self.pixel_position_from_cursor_position()
		if self.temp_x_pos is not None:
			pos = self.temp_x_pos, pos[1]
		else:
			self.temp_x_pos = pos[0]
		# this is relative
		if up:
			offset = -self.text_height
		else:
			offset = self.text_height
		pos = pos[0] + self.x, pos[1] - scroll + self.y + offset
		self.set_cursor_from_click(scroll, False, pos)


	def selection_highlight_inbetweens(self, start_line: int, end_line: int, scroll: int) -> tuple[list[tuple[str, int]], tuple[int, int], str]:
		"""this function has been Sloptimized™. Returns:
		- a list of text lines paired with their displayed y-values
		- x and y position of the final partially-highlighted line
		- the text from that line that's actually highlighted"""
		test = start_line - end_line
		if -1 < test < 1:
			return None

		highlight_color = ColourRGBA(40, 120, 180, 255)

		if test in (-1, 1):
			temp = self.partial_line_from_char(min(self.selection, self.cursor_position))
			y = (min(start_line, end_line) + 1) * self.text_height - scroll
			return [], (0, y), temp

		start = min(start_line, end_line)
		end = max(start_line, end_line)

		full_lines = []  # (text, y) pairs — each drawn/cached independently
		for i, line in enumerate(self.visible_lines[start+1:end]):
			stripped = line.lstrip('\n')
			x = self.ddt.get_text_w(stripped, self.font)
			y = (start + i + 1) * self.text_height - scroll
			self.ddt.rect((0, y - 0.25*self.text_height, x, self.text_height), highlight_color)
			full_lines.append((stripped, y))

		temp = self.partial_line_from_char(min(self.selection, self.cursor_position))
		partial_y = (start + 1 + len(full_lines)) * self.text_height - scroll

		return full_lines, (0, partial_y), temp


	def draw_selection_highlight(self, scroll: int, font: int, text_color: ColourRGBA, width: int) -> None:
		"""this function has been Sloptimized™"""
		highlight_color = ColourRGBA(40, 120, 180, 255)
		rect1 = self.pixel_position_from_cursor_position()
		rect2 = self.pixel_position_from_cursor_position(True)
		if rect1[1] == rect2[1]:
			self.ddt.rect(
				(rect1[0], rect1[1] - scroll - 0.25*self.text_height, rect2[0]-rect1[0], self.text_height),
				highlight_color
			)
			point1 = max(self.selection, self.cursor_position)
			point2 = min(self.selection, self.cursor_position)
			if point2 == 0:
				hl_text = self.text[-point1:]
			else:
				hl_text = self.text[-point1:-point2]
			xx = min(rect1[0], rect2[0])
			self.ddt.text(
				(xx, rect1[1] - scroll),
				hl_text,
				text_color,
				self.font,
				bg=highlight_color,
			)
		else:
			if rect1[1] > rect2[1]: # cursor is lower in text than selection:
				cursor_line = self.which_line_by_char(self.cursor_position)
				if self.cursor_position == 0:
					cursor_width = self.ddt.get_text_w(self.text.split('\n')[-1], font)
				else:
					cursor_width = self.ddt.get_text_w(self.partial_line_from_char(self.cursor_position), font)
				self.ddt.rect(
					(0, rect1[1] - scroll - 0.25*self.text_height, cursor_width, self.text_height),
					highlight_color
				)
				select_line = self.which_line_by_char(self.selection)
				txt = self.partial_line_from_char(self.selection)
				partial_line_text = self.visible_lines[select_line].lstrip('\n')[len(txt):]
				select_start = self.ddt.get_text_w(txt, font)
				select_width = self.ddt.get_text_w(self.visible_lines[select_line].lstrip('\n'), font) - select_start
				self.ddt.rect(
					(select_start, rect2[1] - scroll - 0.25*self.text_height, select_width, self.text_height),
					highlight_color
				)
				self.ddt.text(
					(select_start, rect2[1] - scroll),
					partial_line_text,
					text_color,
					self.font,
					bg=highlight_color,
				)
			else:
				select_line = self.which_line_by_char(self.selection)
				if self.selection == 0:
					select_width = self.ddt.get_text_w(self.text.split('\n')[-1], font)
				else:
					select_width = self.ddt.get_text_w(self.partial_line_from_char(self.selection), font)
				self.ddt.rect(
					(0, rect2[1] - scroll - 0.25*self.text_height, select_width, self.text_height),
					highlight_color
				)
				cursor_line = self.which_line_by_char(self.cursor_position)
				txt = self.partial_line_from_char(self.cursor_position)
				partial_line_text = self.visible_lines[cursor_line].lstrip('\n')[len(txt):]
				cursor_start = self.ddt.get_text_w(txt, font)
				cursor_width = self.ddt.get_text_w(self.visible_lines[cursor_line].lstrip('\n'), font) - cursor_start
				self.ddt.rect(
					(cursor_start, rect1[1] - scroll - 0.25*self.text_height, cursor_width, self.text_height),
					highlight_color
				)
				self.ddt.text(
					(cursor_start, rect1[1] - scroll),
					partial_line_text,
					text_color,
					self.font,
					bg=highlight_color,
				)
			# Sloptacular™:
			highlight_info = self.selection_highlight_inbetweens(select_line, cursor_line, scroll)
			if highlight_info is not None:
				full_lines, partial_pos, partial_text = highlight_info

				for line_text, y in full_lines:
					self.ddt.text((0, y), line_text, text_color, self.font, bg=highlight_color)

				self.ddt.text(partial_pos, partial_text, text_color, self.font, bg=highlight_color)


	def get_scroll_output(self, scroll: int, headroom: int, height: int, autoscroll: bool) -> int:
		"""Allows us to change scroll position by holding arrow keys, typing offscreen, highlighting while moving mouse offscreen"""
		scroll_output = 0
		if self.down_lock:
			if self.inp.mouse_position[1] < self.y:
				return 0- (self.y - self.inp.mouse_position[1])
			elif self.inp.mouse_position[1] > self.y+height:
				return (self.inp.mouse_position[1] - self.y-height)
		if autoscroll:
			test_y = self.pixel_position_from_cursor_position()[1] - scroll
			scroll_output = 0
			if test_y < -headroom + self.text_height: # scroll up
				scroll_output = test_y + headroom - self.text_height
			elif test_y > height-headroom - self.text_height: # scroll down
				scroll_output = test_y -height+headroom + self.text_height
			return scroll_output
		return 0


	def paste(self) -> None:
		if sdl3.SDL_HasClipboardText():
			clip = sdl3.SDL_GetClipboardText().decode("utf-8")
			self.paste_text = clip

	def copy(self) -> None:
		text = self.get_selection()
		if not text:
			text = self.text
		if text:
			sdl3.SDL_SetClipboardText(text.encode("utf-8"))

	def set_text(self, text: str) -> None:
		self.text = text
		if self.cursor_position > len(text):
			self.cursor_position = 0
			self.selection = 0
		else:
			self.selection = self.cursor_position

	def clear(self) -> None:
		self.text = ""
		#self.cursor_position = 0
		self.selection = self.cursor_position

	def highlight_all(self) -> None:
		self.selection = len(self.text)
		self.cursor_position = 0

	def eliminate_selection(self) -> None:
		if self.selection != self.cursor_position:
			if self.selection > self.cursor_position:
				self.text = self.text[0: len(self.text) - self.selection] + self.text[len(self.text) - self.cursor_position:]
				self.selection = self.cursor_position
			else:
				self.text = self.text[0: len(self.text) - self.cursor_position] + self.text[len(self.text) - self.selection:]
				self.cursor_position = self.selection

	def get_selection(self, p: int = 1) -> str | None:
		if self.selection != self.cursor_position:
			if p == 1:
				if self.selection > self.cursor_position:
					return self.text[len(self.text) - self.selection: len(self.text) - self.cursor_position]

				return self.text[len(self.text) - self.cursor_position: len(self.text) - self.selection]
			if p == 0:
				return self.text[0: len(self.text) - max(self.cursor_position, self.selection)]
			if p == 2:
				return self.text[len(self.text) - min(self.cursor_position, self.selection):]
			return None
		return ""


	def draw(
			self, x: int, y: int, colour: ColourRGBA, active: bool = True, font: int = 13,
			width: int = 0, height: int = 0, click: bool = False, selection_height: int = 18, big: bool = False,
			headroom: int = 0, scroll: int = 0) -> int:
		"""Flynn addition: headroom is a hacky way of dealing with bug where larger text will get shaved down from the top
		this function is not very well optimized but i've spent so long on text logic i don't care anymore
		if someone is writing a novel in their unsynced lyrics then they will have problems which i will fix. until then this is what u get
		(the fix will be drawing the text in pieces so we can cache it better)"""

		try:
			self.text_box_canvas_rect.x
		except AttributeError:
			self.initialize(x,y,width,height)
			self.font = font
		if self.text_height == 0 or list(self.known_window_size) != self.gui.window_size \
		or self.known_scale != self.gui.scale:
			self.initialize(x,y,width,height)
			self.font = font
			self.map_lines(width)

		autoscroll = False
		# A little bit messy
		# For now, this is set up so where 'width' is set > 0, the cursor position becomes editable,
		# otherwise it is fixed to end
		previous_target = sdl3.SDL_GetRenderTarget(self.renderer)
		sdl3.SDL_SetRenderTarget(self.renderer, self.text_box_canvas)
		sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_NONE)
		sdl3.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 0)

		self.text_box_canvas_rect.x = 0
		self.text_box_canvas_rect.y = 0
		# if height != 0:
		# 	self.text_box_canvas_rect.h = height
		sdl3.SDL_RenderFillRect(self.renderer, self.text_box_canvas_rect)

		sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_BLEND)

		selection_height *= self.gui.scale

		if click is False:
			click = self.inp.mouse_click
		if self.inp.mouse_down:
			self.gui.request_frame()  # TODO(Taiko): more elegant fix

		rect = (x - 3, y - 2 - headroom, width - 3, height)
		select_rect = (x - 20 * self.gui.scale, y - 2 - headroom, width + 20 * self.gui.scale, height + 21 * self.gui.scale)

		self.fields.add(rect)

		# Activate Menu
		if self.coll(rect) and (self.inp.right_click or self.inp.level_2_right_click):
			self.tauon.field_menu.activate(self)

		if width > 0 and active:
			if click and self.tauon.field_menu.active:
				# field_menu.click()
				click = False

			# Add text from input
			if self.inp.input_text:
				self.temp_x_pos = None
				autoscroll = True
				self.eliminate_selection()
				self.text = self.text[0: len(self.text) - self.cursor_position] + self.inp.input_text + self.text[len(
					self.text) - self.cursor_position:]

			def g() -> str | None:
				if len(self.text) == 0 or self.cursor_position == len(self.text):
					return None
				return self.text[len(self.text) - self.cursor_position -1]

			def g2() -> str | None:
				if len(self.text) == 0 or self.cursor_position == 0:
					return None
				return self.text[len(self.text) - self.cursor_position]

			def d() -> None:
				self.text = self.text[0: len(self.text) - self.cursor_position-1] + self.text[len(
					self.text) - self.cursor_position:]
				self.selection = self.cursor_position

			def d2() -> None:
				self.text = self.text[0:len(self.text) - self.cursor_position] + self.text[len(
					self.text) - self.cursor_position + 1:]
				if self.cursor_position > 0:
					self.cursor_position -= 1
				self.selection = self.cursor_position

			if self.inp.backspace_press or self.inp.key_right_press or \
				self.inp.key_left_press or self.inp.key_return_press:
				self.temp_x_pos = None
				autoscroll = True

			# Ctrl + Backspace to delete word
			if self.inp.backspace_press and (self.inp.key_ctrl_down or self.inp.key_rctrl_down) and \
					self.cursor_position == self.selection and len(self.text) > 0 and self.cursor_position < len(
				self.text):
				while g() not in (" ", "\n"):
					d()
				while g() in (" ", "\n") and g() is not None:
					d()

			# Ctrl + left to move cursor back a word
			elif (self.inp.key_ctrl_down or self.inp.key_rctrl_down) and self.inp.key_left_press:
				while g() in (" ", "\n"):
					self.cursor_position += 1
					if not self.inp.key_shift_down:
						self.selection = self.cursor_position
				while g() is not None and g() not in " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~":
					self.cursor_position += 1
					if not self.inp.key_shift_down:
						self.selection = self.cursor_position
					if g() in (" ", "\n"):
						self.cursor_position -= 1
						if not self.inp.key_shift_down:
							self.selection = self.cursor_position
						break

			# Ctrl + right to move cursor forward a word
			elif (self.inp.key_ctrl_down or self.inp.key_rctrl_down) and self.inp.key_right_press:
				while g2() in (" ", "\n"):
					self.cursor_position -= 1
					if not self.inp.key_shift_down:
						self.selection = self.cursor_position
				while g2() is not None and g2() not in " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~":
					self.cursor_position -= 1
					if not self.inp.key_shift_down:
						self.selection = self.cursor_position
					if g2() in (" ", "\n"):
						self.cursor_position += 1
						if not self.inp.key_shift_down:
							self.selection = self.cursor_position
						break

			# Handle normal backspace
			elif self.inp.backspace_press and len(self.text) > 0 and self.cursor_position < len(self.text):
				while self.inp.backspace_press and len(self.text) > 0 and self.cursor_position < len(self.text):
					if self.selection != self.cursor_position:
						self.eliminate_selection()
					else:
						self.text = self.text[0:len(self.text) - self.cursor_position-1] + self.text[len(
							self.text) - self.cursor_position:]
					self.inp.backspace_press -= 1
			elif self.inp.backspace_press and len(self.get_selection()) > 0:
				self.eliminate_selection()

			# Left and right arrow keys to move cursor
			if self.inp.key_right_press:
				autoscroll = True
				if not self.inp.key_shift_down and not self.inp.key_shiftr_down:
					if self.selection != self.cursor_position:
						self.cursor_position = min(self.selection, self.cursor_position)
					if self.cursor_position > 0:
						self.cursor_position -= 1
					self.selection = self.cursor_position
				else:
					if self.cursor_position > 0:
						self.cursor_position -= 1

			if self.inp.key_left_press:
				autoscroll = True
				if not self.inp.key_shift_down and not self.inp.key_shiftr_down:
					if self.selection != self.cursor_position:
						self.cursor_position = max(self.selection, self.cursor_position)
					if self.cursor_position < len(self.text):
						self.cursor_position += 1
					self.selection = self.cursor_position
				else:
					if self.cursor_position < len(self.text):
						self.cursor_position += 1

			# up and down to switch lines
			if self.inp.key_up_press:
				autoscroll = True
				if self.which_line_by_char(self.cursor_position) != 0:
					self.switch_lines(scroll, True)
				if not self.inp.key_shift_down and not self.inp.key_shiftr_down:
					self.selection = self.cursor_position

			if self.inp.key_down_press:
				autoscroll = True
				if self.which_line_by_char(self.cursor_position) != len(self.visible_lines)-1:
					self.switch_lines(scroll, False)
				if not self.inp.key_shift_down and not self.inp.key_shiftr_down:
					self.selection = self.cursor_position

			if self.paste_text:
				autoscroll = True
				if "http://" in self.text and "http://" in self.paste_text:
					self.text = ""

				self.paste_text = self.paste_text.rstrip(" ").lstrip(" ")
				self.paste_text = self.paste_text.replace("\n", " ").replace("\r", "")

				self.eliminate_selection()
				self.text = self.text[0: len(self.text) - self.cursor_position] + self.paste_text + self.text[len(
					self.text) - self.cursor_position:]
				self.paste_text = ""

			# Paste via ctrl-v
			if self.inp.key_ctrl_down and self.inp.key_v_press:
				autoscroll = True
				clip = sdl3.SDL_GetClipboardText().decode("utf-8")
				self.eliminate_selection()
				self.text = self.text[0: len(self.text) - self.cursor_position] + clip + self.text[len(
					self.text) - self.cursor_position:]

			if self.inp.key_ctrl_down and self.inp.key_c_press:
				self.copy()

			if self.inp.key_ctrl_down and self.inp.key_x_press and len(self.get_selection()) > 0:
				autoscroll = True
				text = self.get_selection()
				if text:
					sdl3.SDL_SetClipboardText(text.encode("utf-8"))
				self.eliminate_selection()

			if self.inp.key_ctrl_down and self.inp.key_a_press:
				self.cursor_position = 0
				self.selection = len(self.text)

			# self.ddt.rect(rect, [255, 50, 50, 80], True)
			if self.coll(rect) and not self.tauon.field_menu.active:
				self.gui.cursor_want = 2

			# Delete key to remove text in front of cursor
			if self.inp.key_del and (self.inp.key_ctrl_down or self.inp.key_rctrl_down) and \
				self.cursor_position == self.selection and len(self.text) > 0 and self.cursor_position > 0:
				autoscroll = True
				while g2() not in (" ", "\n"):
					d2()
				while g2() in (" ", "\n") and g2() is not None:
					d2()
			elif self.inp.key_del:
				autoscroll = True
				if self.selection != self.cursor_position:
					self.eliminate_selection()
				else:
					self.text = self.text[0:len(self.text) - self.cursor_position] + self.text[len(
						self.text) - self.cursor_position + 1:]
					if self.cursor_position > 0:
						self.cursor_position -= 1
					self.selection = self.cursor_position

			if self.inp.key_return_press:
				autoscroll = True
				if self.selection != self.cursor_position:
					self.eliminate_selection()
				self.text = self.text[0:len(self.text) - self.cursor_position] + "\n" + self.text[len(
					self.text) - self.cursor_position:]
				self.selection = self.cursor_position

			if self.inp.key_home_press:
				autoscroll = True
				while g() != "\n" and self.cursor_position < len(self.text):
					self.cursor_position += 1
				if not self.inp.key_shift_down and not self.inp.key_shiftr_down:
					self.selection = self.cursor_position
			if self.inp.key_end_press:
				autoscroll = True
				while g2() != "\n" and self.cursor_position > 0:
					self.cursor_position -= 1
				if not self.inp.key_shift_down and not self.inp.key_shiftr_down:
					self.selection = self.cursor_position

			# width -= round(15 * self.gui.scale)
			t_len, t_wid = self.ddt.get_text_wh(self.text, font, width, True)
			if active and self.gui.editline and self.gui.editline != self.inp.input_text:
				t_len += self.ddt.get_text_w(self.gui.editline, font)
			if not click and not self.down_lock:
				cursor_x = self.ddt.get_text_w(self.partial_line_from_char(self.cursor_position), font) #self.text[:len(self.text) - self.cursor_position]
				margin = round(15 * self.gui.scale)
				max_offset = max(t_len - width, 0)
				if self.cursor_position == len(self.text):
					self.offset = 0
				elif self.cursor_position == 0:
					self.offset = max_offset
				elif cursor_x < self.offset + margin:
					self.offset = max(cursor_x - margin, 0)
				elif cursor_x > self.offset + width:
					self.offset = min(cursor_x - width, max_offset)
				else:
					self.offset = min(max(self.offset, 0), max_offset)

			x -= self.offset

			if self.coll(select_rect):  # self.coll((x - 15, y, width + 16, selection_height + 1)):
				# ddt.rect_r((x - 15, y, width + 16, 19), [50, 255, 50, 50], True)
				if click:
					if self.inp.mouse_position[1] < self.y -headroom -scroll + 1 and not self.down_lock:
						self.cursor_position = len(self.text)
					else:
						self.set_cursor_from_click(scroll, False)
					self.down_lock = True

			if self.inp.mouse_up:
				self.down_lock = False
			if self.down_lock:
				text = self.text
				if self.inp.mouse_position[1] < self.y -headroom -scroll + 1:
					self.selection = len(self.text)
				else:
					self.set_cursor_from_click(scroll, True)

			text = self.text
			self.ddt.text((0, headroom-scroll, 4, width, 40000), text, colour, self.font, max_w=width)

			# draw the blinking text cursor
			space, line = self.pixel_position_from_cursor_position()
			if TextBox.cursor and self.selection == self.cursor_position:
				self.ddt.rect((0 + space, line  + headroom-scroll - 0.2*self.text_height, 1 * self.gui.scale, 0.8*self.text_height), colour)

			if click:
				self.selection = self.cursor_position

			if self.selection != self.cursor_position:
				# text is selected
				self.draw_selection_highlight(scroll - headroom, font, colour, width)
		else:
			# width -= round(15 * self.gui.scale)
			text = self.text
			t_len, t_wid = self.ddt.get_text_wh(text, font, max_x=width)
			self.ddt.text((0, headroom-scroll, 4, width, 40000), text, colour, self.font, max_w=width)
			self.offset = 0
			if self.coll(rect) and not self.tauon.field_menu.active:
				self.gui.cursor_want = 2

		if active:
			tw, th = self.ddt.get_text_wh(self.text, font, max_x=width)
			if self.gui.editline not in ("", self.inp.input_text):
				ex = self.ddt.text((space + round(4 * self.gui.scale), headroom-scroll), self.gui.editline, ColourRGBA(240, 230, 230, 255), font, max_w=width)
				self.ddt.rect((space + round(4 * self.gui.scale), th + round(2 * self.gui.scale), ex, round(1 * self.gui.scale)), ColourRGBA(245, 245, 245, 255))

			pixel_to_logical = self.tauon.pixel_to_logical
			rect = sdl3.SDL_Rect(pixel_to_logical(x), pixel_to_logical(y), pixel_to_logical(tw), pixel_to_logical(th))
			sdl3.SDL_SetTextInputArea(self.t_window, rect, pixel_to_logical(space))

		self.tauon.animate_monitor_timer.set()
		self.text_box_canvas_hide_rect.x = 0
		self.text_box_canvas_hide_rect.y = 0

		sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_NONE)

		self.text_box_canvas_hide_rect.w = round(self.offset)
		if height != 0:
			self.text_box_canvas_hide_rect.h = height
		sdl3.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 0)
		sdl3.SDL_RenderFillRect(self.renderer, self.text_box_canvas_hide_rect)

		self.text_box_canvas_hide_rect.w = round(t_len)
		self.text_box_canvas_hide_rect.x = round(self.offset + width + round(5 * self.gui.scale))
		sdl3.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 0)
		sdl3.SDL_RenderFillRect(self.renderer, self.text_box_canvas_hide_rect)

		sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_BLEND)
		sdl3.SDL_SetRenderTarget(self.renderer, previous_target)

		self.text_box_canvas_rect.x = round(x)
		self.text_box_canvas_rect.y = round(y) - headroom

		sdl3.SDL_RenderTexture(self.renderer, self.text_box_canvas, None, self.text_box_canvas_rect)

		if autoscroll:
			self.map_lines(width)
		return self.get_scroll_output(scroll, headroom, height, autoscroll)

class TextBox2:
	# TODO(Martin): Global class var!
	cursor = True

	def __init__(self, tauon: _TextApp) -> None:
		self.tauon:    _TextApp = tauon
		self.coll     = tauon.coll
		self.ddt:      TDraw = tauon.ddt
		self.gui:     GuiVar = tauon.gui
		self.inp:      Input = tauon.inp
		self.fields:  _TextFields = tauon.fields
		self.t_window = tauon.t_window
		self.renderer = tauon.renderer
		self.text: str = ""
		self.cursor_position = 0
		self.selection = 0
		self.offset = 0
		self.down_lock: bool = False
		self.paste_text: str = ""

	def paste(self) -> None:
		if sdl3.SDL_HasClipboardText():
			clip = sdl3.SDL_GetClipboardText().decode("utf-8")
			self.paste_text = clip

	def copy(self) -> None:
		text = self.get_selection()
		if not text:
			text = self.text
		if text:
			sdl3.SDL_SetClipboardText(text.encode("utf-8"))

	def set_text(self, text: str) -> None:
		self.text = text
		if self.cursor_position > len(text):
			self.cursor_position = 0
			self.selection = 0
		else:
			self.selection = self.cursor_position

	def clear(self) -> None:
		self.text = ""
		#self.cursor_position = 0
		self.selection = self.cursor_position

	def highlight_all(self) -> None:
		self.selection = len(self.text)
		self.cursor_position = 0

	def eliminate_selection(self) -> None:
		if self.selection != self.cursor_position:
			if self.selection > self.cursor_position:
				self.text = self.text[0: len(self.text) - self.selection] + self.text[len(self.text) - self.cursor_position:]
				self.selection = self.cursor_position
			else:
				self.text = self.text[0: len(self.text) - self.cursor_position] + self.text[len(self.text) - self.selection:]
				self.cursor_position = self.selection

	def get_selection(self, p: int = 1) -> str | None:
		if self.selection != self.cursor_position:
			if p == 1:
				if self.selection > self.cursor_position:
					return self.text[len(self.text) - self.selection: len(self.text) - self.cursor_position]

				return self.text[len(self.text) - self.cursor_position: len(self.text) - self.selection]
			if p == 0:
				return self.text[0: len(self.text) - max(self.cursor_position, self.selection)]
			if p == 2:
				return self.text[len(self.text) - min(self.cursor_position, self.selection):]
			return None
		return ""

	def draw(
			self, x: int, y: int, colour: ColourRGBA, active: bool = True, secret: bool = False, font: int = 13, width: int = 0, click: bool = False, selection_height: int = 18, big: bool = False, headroom: int = 0) -> None:
		# Flynn addition: headroom is a hacky way of dealing with bug where larger text will get shaved down from the top

		# A little bit messy
		# For now, this is set up so where 'width' is set > 0, the cursor position becomes editable,
		# otherwise it is fixed to end
		previous_target = sdl3.SDL_GetRenderTarget(self.renderer)
		sdl3.SDL_SetRenderTarget(self.renderer, self.tauon.text_box_canvas)
		sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_NONE)
		sdl3.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 0)

		self.tauon.text_box_canvas_rect.x = 0
		self.tauon.text_box_canvas_rect.y = 0
		sdl3.SDL_RenderFillRect(self.renderer, self.tauon.text_box_canvas_rect)

		sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_BLEND)

		selection_height *= self.gui.scale

		if click is False:
			click = self.inp.mouse_click
		if self.inp.mouse_down:
			self.gui.request_frame()  # TODO(Taiko): more elegant fix

		rect = (x - 3, y - 2, width - 3, 21 * self.gui.scale)
		select_rect = (x - 20 * self.gui.scale, y - 2, width + 20 * self.gui.scale, 21 * self.gui.scale)

		self.fields.add(rect)

		# Activate Menu
		if self.coll(rect) and (self.inp.right_click or self.inp.level_2_right_click):
			self.tauon.field_menu.activate(self)

		if width > 0 and active:
			if click and self.tauon.field_menu.active:
				# field_menu.click()
				click = False

			# Add text from input
			if self.inp.input_text:
				self.eliminate_selection()
				self.text = self.text[0: len(self.text) - self.cursor_position] + self.inp.input_text + self.text[len(
					self.text) - self.cursor_position:]

			def g() -> str | None:
				if len(self.text) == 0 or self.cursor_position == len(self.text):
					return None
				return self.text[len(self.text) - self.cursor_position - 1]

			def g2() -> str | None:
				if len(self.text) == 0 or self.cursor_position == 0:
					return None
				return self.text[len(self.text) - self.cursor_position]

			def d() -> None:
				self.text = self.text[0: len(self.text) - self.cursor_position - 1] + self.text[len(
					self.text) - self.cursor_position:]
				self.selection = self.cursor_position

			# Ctrl + Backspace to delete word
			if self.inp.backspace_press and (self.inp.key_ctrl_down or self.inp.key_rctrl_down) and \
					self.cursor_position == self.selection and len(self.text) > 0 and self.cursor_position < len(
				self.text):
				while g() == " ":
					d()
				while g() != " " and g() is not None:
					d()

			# Ctrl + left to move cursor back a word
			elif (self.inp.key_ctrl_down or self.inp.key_rctrl_down) and self.inp.key_left_press:
				while g() == " ":
					self.cursor_position += 1
					if not self.inp.key_shift_down:
						self.selection = self.cursor_position
				while g() is not None and g() not in " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~":
					self.cursor_position += 1
					if not self.inp.key_shift_down:
						self.selection = self.cursor_position
					if g() == " ":
						self.cursor_position -= 1
						if not self.inp.key_shift_down:
							self.selection = self.cursor_position
						break

			# Ctrl + right to move cursor forward a word
			elif (self.inp.key_ctrl_down or self.inp.key_rctrl_down) and self.inp.key_right_press:
				while g2() == " ":
					self.cursor_position -= 1
					if not self.inp.key_shift_down:
						self.selection = self.cursor_position
				while g2() is not None and g2() not in " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~":
					self.cursor_position -= 1
					if not self.inp.key_shift_down:
						self.selection = self.cursor_position
					if g2() == " ":
						self.cursor_position += 1
						if not self.inp.key_shift_down:
							self.selection = self.cursor_position
						break

			# Handle normal backspace
			elif self.inp.backspace_press and len(self.text) > 0 and self.cursor_position < len(self.text):
				while self.inp.backspace_press and len(self.text) > 0 and self.cursor_position < len(self.text):
					if self.selection != self.cursor_position:
						self.eliminate_selection()
					else:
						self.text = self.text[0:len(self.text) - self.cursor_position - 1] + self.text[len(
							self.text) - self.cursor_position:]
					self.inp.backspace_press -= 1
			elif self.inp.backspace_press and len(self.get_selection()) > 0:
				self.eliminate_selection()

			# Left and right arrow keys to move cursor
			if self.inp.key_right_press:
				if self.cursor_position > 0:
					self.cursor_position -= 1
				if not self.inp.key_shift_down and not self.inp.key_shiftr_down:
					self.selection = self.cursor_position

			if self.inp.key_left_press:
				if self.cursor_position < len(self.text):
					self.cursor_position += 1
				if not self.inp.key_shift_down and not self.inp.key_shiftr_down:
					self.selection = self.cursor_position

			if self.paste_text:
				if "http://" in self.text and "http://" in self.paste_text:
					self.text = ""

				self.paste_text = self.paste_text.rstrip(" ").lstrip(" ")
				self.paste_text = self.paste_text.replace("\n", " ").replace("\r", "")

				self.eliminate_selection()
				self.text = self.text[0: len(self.text) - self.cursor_position] + self.paste_text + self.text[len(
					self.text) - self.cursor_position:]
				self.paste_text = ""

			# Paste via ctrl-v
			if self.inp.key_ctrl_down and self.inp.key_v_press:
				clip = sdl3.SDL_GetClipboardText().decode("utf-8")
				self.eliminate_selection()
				self.text = self.text[0: len(self.text) - self.cursor_position] + clip + self.text[len(
					self.text) - self.cursor_position:]

			if self.inp.key_ctrl_down and self.inp.key_c_press:
				self.copy()

			if self.inp.key_ctrl_down and self.inp.key_x_press and len(self.get_selection()) > 0:
				text = self.get_selection()
				if text:
					sdl3.SDL_SetClipboardText(text.encode("utf-8"))
				self.eliminate_selection()

			if self.inp.key_ctrl_down and self.inp.key_a_press:
				self.cursor_position = 0
				self.selection = len(self.text)

			# self.ddt.rect(rect, [255, 50, 50, 80], True)
			if self.coll(rect) and not self.tauon.field_menu.active:
				self.gui.cursor_want = 2

			# Delete key to remove text in front of cursor
			if self.inp.key_del:
				if self.selection != self.cursor_position:
					self.eliminate_selection()
				else:
					self.text = self.text[0:len(self.text) - self.cursor_position] + self.text[len(
						self.text) - self.cursor_position + 1:]
					if self.cursor_position > 0:
						self.cursor_position -= 1
					self.selection = self.cursor_position

			if self.inp.key_home_press:
				self.cursor_position = len(self.text)
				if not self.inp.key_shift_down and not self.inp.key_shiftr_down:
					self.selection = self.cursor_position
			if self.inp.key_end_press:
				self.cursor_position = 0
				if not self.inp.key_shift_down and not self.inp.key_shiftr_down:
					self.selection = self.cursor_position

			width -= round(15 * self.gui.scale)
			t_len = self.ddt.get_text_w(self.text, font)
			if active and self.gui.editline and self.gui.editline != self.inp.input_text:
				t_len += self.ddt.get_text_w(self.gui.editline, font)
			if not click and not self.down_lock:
				cursor_x = self.ddt.get_text_w(self.text[:len(self.text) - self.cursor_position], font)
				margin = round(15 * self.gui.scale)
				max_offset = max(t_len - width, 0)
				if self.cursor_position == len(self.text):
					self.offset = 0
				elif self.cursor_position == 0:
					self.offset = max_offset
				elif cursor_x < self.offset + margin:
					self.offset = max(cursor_x - margin, 0)
				elif cursor_x > self.offset + width:
					self.offset = min(cursor_x - width, max_offset)
				else:
					self.offset = min(max(self.offset, 0), max_offset)

			x -= self.offset

			if self.coll(select_rect):  # self.coll((x - 15, y, width + 16, selection_height + 1)):
				# ddt.rect_r((x - 15, y, width + 16, 19), [50, 255, 50, 50], True)
				if click:
					pre = 0
					post = 0
					if self.inp.mouse_position[0] < x + 1:
						self.cursor_position = len(self.text)
					else:
						for i in range(len(self.text)):
							post = self.ddt.get_text_w(self.text[0:i + 1], font)
							# pre_half = int((post - pre) / 2)

							if x + pre - 0 <= self.inp.mouse_position[0] <= x + post + 0:
								diff = post - pre
								if self.inp.mouse_position[0] >= x + pre + int(diff / 2):
									self.cursor_position = len(self.text) - i - 1
								else:
									self.cursor_position = len(self.text) - i
								break
							pre = post
						else:
							self.cursor_position = 0
					self.selection = 0
					self.down_lock = True

			if self.inp.mouse_up:
				self.down_lock = False
			if self.down_lock:
				pre = 0
				post = 0
				text = self.text
				if secret:
					text = "●" * len(self.text)
				if self.inp.mouse_position[0] < x + 1:
					self.selection = len(text)
				else:

					for i in range(len(text)):
						post = self.ddt.get_text_w(text[0:i + 1], font)
						# pre_half = int((post - pre) / 2)

						if x + pre - 0 <= self.inp.mouse_position[0] <= x + post + 0:
							diff = post - pre

							if self.inp.mouse_position[0] >= x + pre + int(diff / 2):
								self.selection = len(text) - i - 1

							else:
								self.selection = len(text) - i

							break
						pre = post

					else:
						self.selection = 0

			text = self.text[0: len(self.text) - self.cursor_position]
			if secret:
				text = "●" * len(text)
			a = self.ddt.get_text_w(text, font)

			text = self.text[0: len(self.text) - self.selection]
			if secret:
				text = "●" * len(text)
			b = self.ddt.get_text_w(text, font)

			top = y
			if big:
				top -= 12 * self.gui.scale

			self.ddt.rect([a, 0, b - a, selection_height], ColourRGBA(40, 120, 180, 255))

			if self.selection != self.cursor_position:
				inf_comp = 0
				text = self.get_selection(0)
				if secret:
					text = "●" * len(text)
				space = self.ddt.text((0, headroom), text, colour, font)
				text = self.get_selection(1)
				if secret:
					text = "●" * len(text)
				space += self.ddt.text((0 + space - inf_comp, headroom), text, ColourRGBA(240, 240, 240, 255), font, bg=ColourRGBA(40, 120, 180, 255))
				text = self.get_selection(2)
				if secret:
					text = "●" * len(text)
				self.ddt.text((0 + space - (inf_comp * 2), headroom), text, colour, font)
			else:
				text = self.text
				if secret:
					text = "●" * len(text)
				self.ddt.text((0, headroom), text, colour, font)

			text = self.text[0: len(self.text) - self.cursor_position]
			if secret:
				text = "●" * len(text)
			space = self.ddt.get_text_w(text, font)

			if TextBox.cursor and self.selection == self.cursor_position:
				# ddt.line(x + space, y + 2, x + space, y + 15, colour)
				self.ddt.rect((0 + space, 0  + headroom, 1 * self.gui.scale, 14 * self.gui.scale), colour)

			if click:
				self.selection = self.cursor_position
		else:
			width -= round(15 * self.gui.scale)
			text = self.text
			if secret:
				text = "●" * len(text)
			t_len = self.ddt.get_text_w(text, font)
			self.ddt.text((0, headroom), text, colour, font)
			self.offset = 0
			if self.coll(rect) and not self.tauon.field_menu.active:
				self.gui.cursor_want = 2

		if active:
			tw, th = self.ddt.get_text_wh(self.gui.editline, font, max_x=2000)
			if self.gui.editline not in ("", self.inp.input_text):
				ex = self.ddt.text((space + round(4 * self.gui.scale), headroom), self.gui.editline, ColourRGBA(240, 230, 230, 255), font)
				self.ddt.rect((space + round(4 * self.gui.scale), th + round(2 * self.gui.scale), ex, round(1 * self.gui.scale)), ColourRGBA(245, 245, 245, 255))

			pixel_to_logical = self.tauon.pixel_to_logical
			rect = sdl3.SDL_Rect(pixel_to_logical(x), pixel_to_logical(y), pixel_to_logical(tw), pixel_to_logical(th))
			sdl3.SDL_SetTextInputArea(self.t_window, rect, pixel_to_logical(space))

		self.tauon.animate_monitor_timer.set()

		self.tauon.text_box_canvas_hide_rect.x = 0
		self.tauon.text_box_canvas_hide_rect.y = 0

		# if self.offset:
		sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_NONE)

		self.tauon.text_box_canvas_hide_rect.w = round(self.offset)
		sdl3.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 0)
		sdl3.SDL_RenderFillRect(self.renderer, self.tauon.text_box_canvas_hide_rect)

		self.tauon.text_box_canvas_hide_rect.w = round(t_len)
		self.tauon.text_box_canvas_hide_rect.x = round(self.offset + width + round(5 * self.gui.scale))
		sdl3.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 0)
		sdl3.SDL_RenderFillRect(self.renderer, self.tauon.text_box_canvas_hide_rect)

		sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_BLEND)
		sdl3.SDL_SetRenderTarget(self.renderer, previous_target)

		self.tauon.text_box_canvas_rect.x = round(x)
		self.tauon.text_box_canvas_rect.y = round(y) - headroom
		sdl3.SDL_RenderTexture(self.renderer, self.tauon.text_box_canvas, None, self.tauon.text_box_canvas_rect)

class TextBox:
	# TODO(Martin): Global class var!
	cursor = True

	def __init__(self, tauon: _TextApp) -> None:
		self.tauon:   _TextApp = tauon
		self.ddt:     TDraw = tauon.ddt
		self.gui:    GuiVar = tauon.gui
		self.inp:     Input = tauon.inp
		self.coll           = tauon.coll
		self.fields: _TextFields = tauon.fields
		self.t_window       = tauon.t_window
		self.renderer       = tauon.renderer
		self.text: str = ""
		self.cursor_position = 0
		self.selection = 0
		self.down_lock: bool = False

	def paste(self) -> None:
		if sdl3.SDL_HasClipboardText():
			clip = sdl3.SDL_GetClipboardText().decode("utf-8")

			if "http://" in self.text and "http://" in clip:
				self.text = ""

			clip = clip.rstrip(" ").lstrip(" ")
			clip = clip.replace("\n", " ").replace("\r", "")

			self.eliminate_selection()
			self.text = self.text[0: len(self.text) - self.cursor_position] + clip + self.text[len(
				self.text) - self.cursor_position:]

	def copy(self) -> None:
		text = self.get_selection()
		if not text:
			text = self.text
		if text:
			sdl3.SDL_SetClipboardText(text.encode("utf-8"))

	def set_text(self, text: str) -> None:
		self.text = text
		self.cursor_position = 0
		self.selection = 0

	def clear(self) -> None:
		self.text = ""

	def highlight_all(self) -> None:
		self.selection = len(self.text)
		self.cursor_position = 0

	def highlight_none(self) -> None:
		self.selection = 0
		self.cursor_position = 0

	def eliminate_selection(self) -> None:
		if self.selection != self.cursor_position:
			if self.selection > self.cursor_position:
				self.text = self.text[0: len(self.text) - self.selection] + self.text[
					len(self.text) - self.cursor_position:]
				self.selection = self.cursor_position
			else:
				self.text = self.text[0: len(self.text) - self.cursor_position] + self.text[
					len(self.text) - self.selection:]
				self.cursor_position = self.selection

	def get_selection(self, p: int = 1):
		if self.selection != self.cursor_position:
			if p == 1:
				if self.selection > self.cursor_position:
					return self.text[len(self.text) - self.selection: len(self.text) - self.cursor_position]

				return self.text[len(self.text) - self.cursor_position: len(self.text) - self.selection]
			if p == 0:
				return self.text[0: len(self.text) - max(self.cursor_position, self.selection)]
			if p == 2:
				return self.text[len(self.text) - min(self.cursor_position, self.selection):]
		else:
			return ""
		return None

	def draw(
		self, x: int, y: int, colour: list[int], active: bool = True, secret: bool = False,
		font: int = 13, width: int = 0, click: bool = False, selection_height: float = 18, big: bool = False) -> None:
		inp = self.inp
		ddt = self.ddt
		gui = self.gui

		# A little bit messy
		# For now, this is set up so where 'width' is set > 0, the cursor position becomes editable,
		# otherwise it is fixed to end

		selection_height *= self.gui.scale

		if click is False:
			click = self.inp.mouse_click

		if width > 0 and active:

			rect = (x - 3, y - 2, width - 3, 21 * gui.scale)
			select_rect = (x - 20 * gui.scale, y - 2, width + 20 * gui.scale, 21 * gui.scale)
			if big:
				rect = (x - 3, y - 15 * gui.scale, width - 3, 35 * gui.scale)
				select_rect = (x - 50 * gui.scale, y - 15 * gui.scale, width + 50 * gui.scale, 35 * gui.scale)

			# Activate Menu
			if self.coll(rect) and (inp.right_click or inp.level_2_right_click):
				self.tauon.field_menu.activate(self)

			if click and self.tauon.field_menu.active:
				# field_menu.click()
				click = False

			# Add text from input
			if self.inp.input_text:
				self.eliminate_selection()
				self.text = self.text[0: len(self.text) - self.cursor_position] + self.inp.input_text + self.text[
					len(self.text) - self.cursor_position:]

			def g() -> str | None:
				if len(self.text) == 0 or self.cursor_position == len(self.text):
					return None
				return self.text[len(self.text) - self.cursor_position - 1]

			def g2() -> str | None:
				if len(self.text) == 0 or self.cursor_position == 0:
					return None
				return self.text[len(self.text) - self.cursor_position]

			def d() -> None:
				self.text = self.text[0: len(self.text) - self.cursor_position - 1] + self.text[
					len(self.text) - self.cursor_position:]
				self.selection = self.cursor_position

			# Ctrl + Backspace to delete word
			if inp.backspace_press and (inp.key_ctrl_down or inp.key_rctrl_down) and \
					self.cursor_position == self.selection and len(self.text) > 0 and self.cursor_position < len(
				self.text):
				while g() == " ":
					d()
				while g() != " " and g() is not None:
					d()

			# Ctrl + left to move cursor back a word
			elif (inp.key_ctrl_down or inp.key_rctrl_down) and inp.key_left_press:
				while g() == " ":
					self.cursor_position += 1
					if not inp.key_shift_down:
						self.selection = self.cursor_position
				while g() is not None and g() not in " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~":
					self.cursor_position += 1
					if not inp.key_shift_down:
						self.selection = self.cursor_position
					if g() == " ":
						self.cursor_position -= 1
						if not inp.key_shift_down:
							self.selection = self.cursor_position
						break

			# Ctrl + right to move cursor forward a word
			elif (inp.key_ctrl_down or inp.key_rctrl_down) and inp.key_right_press:
				while g2() == " ":
					self.cursor_position -= 1
					if not inp.key_shift_down:
						self.selection = self.cursor_position
				while g2() is not None and g2() not in " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~":
					self.cursor_position -= 1
					if not inp.key_shift_down:
						self.selection = self.cursor_position
					if g2() == " ":
						self.cursor_position += 1
						if not inp.key_shift_down:
							self.selection = self.cursor_position
						break

			# Handle normal backspace
			elif inp.backspace_press and len(self.text) > 0 and self.cursor_position < len(self.text):
				while inp.backspace_press and len(self.text) > 0 and self.cursor_position < len(self.text):
					if self.selection != self.cursor_position:
						self.eliminate_selection()
					else:
						self.text = self.text[0:len(self.text) - self.cursor_position - 1] + self.text[
							len(self.text) - self.cursor_position:]
					inp.backspace_press -= 1
			elif inp.backspace_press and len(self.get_selection()) > 0:
				self.eliminate_selection()

			# Left and right arrow keys to move cursor
			if inp.key_right_press:
				if self.cursor_position > 0:
					self.cursor_position -= 1
				if not inp.key_shift_down and not inp.key_shiftr_down:
					self.selection = self.cursor_position

			if inp.key_left_press:
				if self.cursor_position < len(self.text):
					self.cursor_position += 1
				if not inp.key_shift_down and not inp.key_shiftr_down:
					self.selection = self.cursor_position

			# Paste via ctrl-v
			if inp.key_ctrl_down and inp.key_v_press:
				clip = sdl3.SDL_GetClipboardText().decode("utf-8")
				self.eliminate_selection()
				self.text = self.text[0: len(self.text) - self.cursor_position] + clip + self.text[len(
					self.text) - self.cursor_position:]

			if inp.key_ctrl_down and inp.key_c_press:
				self.copy()

			if inp.key_ctrl_down and inp.key_x_press and len(self.get_selection()) > 0:
				text = self.get_selection()
				if text:
					sdl3.SDL_SetClipboardText(text.encode("utf-8"))
				self.eliminate_selection()

			if inp.key_ctrl_down and inp.key_a_press:
				self.cursor_position = 0
				self.selection = len(self.text)

			# ddt.rect_r(rect, [255, 50, 50, 80], True)
			if self.coll(rect) and not self.tauon.field_menu.active:
				gui.cursor_want = 2

			self.fields.add(rect)

			# Delete key to remove text in front of cursor
			if inp.key_del:
				if self.selection != self.cursor_position:
					self.eliminate_selection()
				else:
					self.text = self.text[0:len(self.text) - self.cursor_position] + self.text[len(
						self.text) - self.cursor_position + 1:]
					if self.cursor_position > 0:
						self.cursor_position -= 1
					self.selection = self.cursor_position

			if inp.key_home_press:
				self.cursor_position = len(self.text)
				if not inp.key_shift_down and not inp.key_shiftr_down:
					self.selection = self.cursor_position
			if inp.key_end_press:
				self.cursor_position = 0
				if not inp.key_shift_down and not inp.key_shiftr_down:
					self.selection = self.cursor_position

			if self.coll(select_rect):
				# ddt.rect_r((x - 15, y, width + 16, 19), [50, 255, 50, 50], True)
				if click:
					pre = 0
					post = 0
					if inp.mouse_position[0] < x + 1:
						self.cursor_position = len(self.text)
					else:
						for i in range(len(self.text)):
							post = ddt.get_text_w(self.text[0:i + 1], font)
							# pre_half = int((post - pre) / 2)

							if x + pre - 0 <= inp.mouse_position[0] <= x + post + 0:
								diff = post - pre
								if inp.mouse_position[0] >= x + pre + int(diff / 2):
									self.cursor_position = len(self.text) - i - 1
								else:
									self.cursor_position = len(self.text) - i
								break
							pre = post
						else:
							self.cursor_position = 0
					self.selection = 0
					self.down_lock = True

			if inp.mouse_up:
				self.down_lock = False
			if self.down_lock:
				pre = 0
				post = 0
				if inp.mouse_position[0] < x + 1:

					self.selection = len(self.text)
				else:

					for i in range(len(self.text)):
						post = ddt.get_text_w(self.text[0:i + 1], font)
						# pre_half = int((post - pre) / 2)

						if x + pre - 0 <= inp.mouse_position[0] <= x + post + 0:
							diff = post - pre

							if inp.mouse_position[0] >= x + pre + int(diff / 2):
								self.selection = len(self.text) - i - 1
							else:
								self.selection = len(self.text) - i

							break
						pre = post

					else:
						self.selection = 0

			a = ddt.get_text_w(self.text[0: len(self.text) - self.cursor_position], font)

			# logging.info("")
			# logging.info(self.selection)
			# logging.info(self.cursor_position)

			b = ddt.get_text_w(self.text[0: len(self.text) - self.selection], font)

			# rint((a, b))

			top = y
			if big:
				top -= 12 * gui.scale

			ddt.rect([x + a, top, b - a, selection_height], ColourRGBA(40, 120, 180, 255))

			if self.selection != self.cursor_position:
				inf_comp = 0
				space = ddt.text((x, y), self.get_selection(0), colour, font)
				space += ddt.text(
					(x + space - inf_comp, y), self.get_selection(1), ColourRGBA(240, 240, 240, 255), font,
					bg=ColourRGBA(40, 120, 180, 255))
				ddt.text((x + space - (inf_comp * 2), y), self.get_selection(2), colour, font)
			else:
				ddt.text((x, y), self.text, colour, font)

			space = ddt.get_text_w(self.text[0: len(self.text) - self.cursor_position], font)

			if TextBox.cursor and self.selection == self.cursor_position:
				# ddt.line(x + space, y + 2, x + space, y + 15, colour)

				if big:
					# ddt.rect_r((xx + 1 , yy - 12 * gui.scale, 2 * gui.scale, 27 * gui.scale), colour, True)
					ddt.rect((x + space, y - 15 * gui.scale + 2, 1 * gui.scale, 30 * gui.scale), colour)
				else:
					ddt.rect((x + space, y + 2, 1 * gui.scale, 14 * gui.scale), colour)

			if click:
				self.selection = self.cursor_position

		else:
			if active:
				self.text += self.inp.input_text
				if self.inp.input_text:
					self.cursor = True

				while inp.backspace_press and len(self.text) > 0:
					self.text = self.text[:-1]
					inp.backspace_press -= 1

				if inp.key_ctrl_down and inp.key_v_press:
					self.paste()

			if secret:
				space = ddt.text((x, y), "●" * len(self.text), colour, font)
			else:
				space = ddt.text((x, y), self.text, colour, font)

			if active and TextBox.cursor:
				xx = x + space + 1
				yy = y + 3
				if big:
					ddt.rect((xx + 1, yy - 12 * gui.scale, 2 * gui.scale, 27 * gui.scale), colour)
				else:
					ddt.rect((xx, yy, 1 * gui.scale, 14 * gui.scale), colour)

		if active:
			tw, th = ddt.get_text_wh(self.gui.editline, font, max_x=2000)
			if self.gui.editline not in ("", self.inp.input_text):
				ex = ddt.text((x + space + round(4 * gui.scale), y), self.gui.editline, ColourRGBA(240, 230, 230, 255), font)

				ddt.rect((x + space + round(4 * gui.scale), (y + th) - round(4 * gui.scale), ex, round(1 * gui.scale)),
					ColourRGBA(245, 245, 245, 255))

			pixel_to_logical = self.tauon.pixel_to_logical
			rect = sdl3.SDL_Rect(pixel_to_logical(x), pixel_to_logical(y), pixel_to_logical(tw), pixel_to_logical(th))
			sdl3.SDL_SetTextInputArea(self.t_window, rect, pixel_to_logical(space))

		self.tauon.animate_monitor_timer.set()
