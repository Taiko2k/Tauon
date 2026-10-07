# Copyright © 2026, Tauon contributors

"""Single-line tag inputs with editable, visually distinct value boundaries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tauon.t_modules.t_main import TextBox2, readable_text_colour

if TYPE_CHECKING:
	from tauon.t_modules.t_draw import TDraw
	from tauon.t_modules.t_extra import ColourRGBA


class ValueTextDraw:
	def __init__(self, base: TDraw, separator: str, scale: float, green: ColourRGBA) -> None:
		self.base, self.separator, self.scale, self.green = base, separator, scale, green

	def __getattr__(self, name: str) -> object:
		"""Delegate drawing operations unrelated to inline value boundaries."""
		return getattr(self.base, name)

	@staticmethod
	def visible(text: str) -> str:
		return text.replace("\n", "↵").replace("\r", "↵")

	def separator_width(self, font: int) -> int:
		return self.base.get_text_w(" / ", font) + round(4 * self.scale)

	def get_text_w(self, text: str, font: int, height: bool = False) -> int:
		if height:
			return self.base.get_text_w(self.visible(text.replace(self.separator, "/")), font, True)
		parts = text.split(self.separator)
		return sum(self.base.get_text_w(self.visible(part), font) for part in parts) + (
			len(parts) - 1
		) * self.separator_width(font)

	def text(self, location: tuple, text: str, colour: ColourRGBA, font: int, **kwargs: object) -> int:
		x, y = location[:2]
		advance = 0
		parts = text.split(self.separator)
		for index, part in enumerate(parts):
			if index:
				padding = (self.separator_width(font) - self.base.get_text_w("/", font)) / 2
				for stroke in (0, max(1, round(self.scale / 2))):
					self.base.text((x + advance + padding + stroke, y), "/", self.green, font, **kwargs)
				advance += self.separator_width(font)
			visible = self.visible(part)
			self.base.text((x + advance, y), visible, colour, font, **kwargs)
			advance += self.base.get_text_w(visible, font)
		return advance


class TagTextBox(TextBox2):
	separator = "\ue000"

	def set_values(self, values: list[str]) -> None:
		text = "".join(values)
		self.separator = next(chr(code) for code in range(0xE000, 0xF900) if chr(code) not in text)
		self.set_text(self.separator.join(values))

	def values(self) -> list[str]:
		return [value for value in self.text.split(self.separator) if value]

	def insert_separator(self) -> None:
		self.eliminate_selection()
		position = len(self.text) - self.cursor_position
		self.text = self.text[:position] + self.separator + self.text[position:]
		self.selection = self.cursor_position

	def copy(self) -> None:
		import sdl3  # noqa: PLC0415

		text = self.get_selection() or self.text
		if text:
			sdl3.SDL_SetClipboardText(text.replace(self.separator, " / ").encode("utf-8"))

	def draw(self, *args: object, **kwargs: object) -> None:
		base = self.ddt
		green = readable_text_colour(self.tauon.colours.level_green, self.tauon.colours.box_background)
		self.ddt = ValueTextDraw(base, self.separator, self.gui.scale, green)
		try:
			super().draw(*args, **kwargs)
		finally:
			self.ddt = base
