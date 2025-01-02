"""Guitar Chord Tauon module

At the moment unused, and not fully working due to broken vars which used to be global.

Used to work with api.guitarchord.com in the past.
"""
from __future__ import annotations

import logging
import os
import urllib.parse
from pathlib import Path
from typing import TYPE_CHECKING

import requests

from tauon.t_modules.t_extra import filename_safe
from tauon.t_modules.t_main import copy_from_clipboard

if TYPE_CHECKING:
	from tauon.t_modules.t_draw import TDraw
	from tauon.t_modules.t_main import GuiVar, Input, PlayerCtl, TrackClass

class GuitarChords:

	def __init__(self, user_directory: Path, inp: Input, ddt: TDraw, gui: GuiVar, pctl: PlayerCtl) -> None:
		self.store_a:         Path = user_directory / "guitar-chords-a"  # inline format
		self.store_b:         Path = user_directory / "guitar-chords-b"  # 2 lines format
		self.inp:            Input = inp
		self.ddt:            TDraw = ddt
		self.gui:           GuiVar = gui
		self.pctl:       PlayerCtl = pctl
		self.data:            list = []
		self.current:          str = ""
		self.auto_scroll:     bool = True
		self.scroll_position:  int = 0
		self.ready: dict[str, int] = {}
		self.widespace:        str = "　"

	def clear(self, track: TrackClass) -> None:

		cache_title = self.get_cache_title(track)
		self.prep_folders()
		self.current = ""
		self.scroll_position = 0

		self.ready[cache_title] = 0

		for item in os.listdir(self.store_a):
			if item == cache_title:
				(self.store_a / cache_title).unlink()

		for item in os.listdir(self.store_b):
			if item == cache_title:
				(self.store_b / cache_title).unlink()

	def search_guitarparty(self, track_object: TrackClass):
		if not track_object.title:
			show_message(_("Insufficient metadata to search"))
		self.fetch(track_object)

	def paste_chord_lyrics(self, track_object: TrackClass) -> None:
		if track_object.title:
			self.save_format_b(track_object)


	def clear_chord_lyrics(self, track_object: TrackClass) -> None:
		if track_object.title:
			self.clear(track_object)

	def save_format_b(self, track: TrackClass) -> None:

		t = copy_from_clipboard()
		if not t:
			show_message(_("Clipboard has no text"))
			self.inp.mouse_click = False
			return

		cache_title = self.get_cache_title(track)

		t = t.replace("\r", "")

		f = (self.store_b / cache_title).open("w")
		f.write(t)
		f.close()

	def parse_b(self, lines: list[str]):

		final: list[tuple[str, list[tuple[str, int]]]] = []

		last = ""

		for line in lines:

			if line in (" ", "", "\n"):
				line = "                                          "

			line = line.replace("\n", "")
			line = line.replace("\r", "")

			if not last and (len(line) < 6 or \
				"    "   in line \
				or "D "  in line \
				or "Am " in line \
				or "Fm"  in line \
				or "Em " in line \
				or "C "  in line \
				or "G "  in line \
				or "F "  in line \
				or "Dm"  in line) and any(c.isalpha() for c in line):
				last = line
				continue

			w = list(line)
			for i, c in enumerate(w):
				if i > 0 and c == " " and (w[i - 1] == " " or w[i - 1] == self.widespace):
					w[i - 1] = self.widespace
					w[i] = self.widespace
			line = "".join(w)

			if not last:
				final.append((line, []))
				continue

			on = 0
			mode = 0
			distance = 0
			chords: list[tuple[str, int]] = []

			while on < len(last):

				if mode == 0:
					if last[on] == " ":
						on += 1
						continue
					mode = 1
					distance = self.ddt.get_text_w(line[:on], 16)

				on2 = on
				while on2 < len(last) and last[on2] != " ":
					on2 += 1

				grab = last[on:on2]

				chords.append((grab, distance))
				mode = 0
				on = on2
				on += 1

			final.append((line, chords))
			last = ""
		self.data = final

	def prep_folders(self) -> None:

		if not self.store_a.exists():
			os.makedirs(self.store_a)

		if not self.store_b.exists():
			os.makedirs(self.store_b)

	def fetch(self, track: TrackClass) -> None:

		if self.test_ready_status(track) != 0:
			return

		cache_title = self.get_cache_title(track)

		try:

			r = requests.get(
				"http://api.guitarparty.com/v2/songs/?query=" + urllib.parse.quote(cache_title),
				headers={"Guitarparty-Api-Key": "e9c0e543798c4249c24f698022ced5dd0c583ec7"},
				timeout=10)
			d = r.json()["objects"][0]["body"]

			self.prep_folders()
			f = (self.store_a / cache_title).open("w")
			f.write(d)
			f.close()

			self.ready[cache_title] = 1

		except Exception:
			logging.exception("Could not find matching track on GuitarParty")
			show_message(_("Could not find matching track on GuitarParty"))
			self.inp.mouse_click = False
			self.ready[cache_title] = 2

	def test_ready_status(self, track: TrackClass) -> int:

		# 0 not searched
		# 1 ready
		# 2 failed

		cache_title = self.get_cache_title(track)

		if cache_title in self.ready:
			if self.ready[cache_title] == 1:
				return 1
			if self.ready[cache_title] == 2:
				return 2
			return 0

		self.prep_folders()
		if cache_title in os.listdir(self.store_a):
			self.ready[cache_title] = 1
			return 1
		if cache_title in os.listdir(self.store_b):
			self.ready[cache_title] = 1
			return 1
		self.ready[cache_title] = 0
		return 0

	def parse(self, lines: list[str]) -> None:

		final = []

		for line in lines:
			line = line.rstrip()
			# while "  " in line:
			# line = line.replace("  ", "　　")
			w = list(line)

			for i, c in enumerate(w):
				if i > 0 and c == " " and (w[i - 1] == " " or w[i - 1] == self.widespace):
					w[i - 1] = self.widespace
					w[i] = self.widespace

			lyrics: list[str] = []
			chords: list[tuple[str, int]] = []

			on = 0
			mode = 0

			chord_part: list[str] = []

			while on < len(w):
				if mode == 0:
					# If normal, add to lyric list
					if w[on] != "[":
						lyrics.append(w[on])
						on += 1
						continue

					# Start of [, delete it
					mode = 1
					del w[on]
					continue

				if w[on] == "]":
					del w[on]
					mode = 0

					distance = 0
					if on > 0:
						distance = self.ddt.get_text_w("".join(w[:on]), 16)

					chords.append(("".join(chord_part), distance))
					chord_part = []
					continue

				chord_part.append(w[on])
				del w[on]

			final.append(("".join(lyrics), chords))

		logging.info(final)
		self.data = final

	def get_cache_title(self, track: TrackClass) -> str:

		name = track.artist + " " + track.title
		name = filename_safe(name, sub="_")
		return name

	def render(self, track: TrackClass, x: int, y: int) -> bool:

		cache_title = self.get_cache_title(track)

		if self.current == cache_title:
			if not self.data:
				return False
		else:
			self.prep_folders()
			if cache_title in os.listdir(self.store_a):
				f = (self.store_a / cache_title).open()
				lines = f.readlines()
				f.close()
				self.parse(lines)
				self.current = cache_title
				self.scroll_position = 0

			elif cache_title in os.listdir(self.store_b):
				f = (self.store_b / cache_title).open()
				lines = f.readlines()
				f.close()
				self.parse_b(lines)
				self.current = cache_title
				self.scroll_position = 0
			else:
				return False

		if self.auto_scroll:

			if self.pctl.playing_length > 20:
				progress = max(0, self.pctl.playing_time - 12) / (self.pctl.playing_length - 3)
				height = len(self.data) * (18 + 15) * self.gui.scale

				self.scroll_position = height * progress
				# gui.update += 1
				self.gui.frame_callback_list.append(TestTimer(0.3))
				# time.sleep(0.032)

		if mouse_wheel and self.gui.panelY < mouse_position[1] < window_size[1] - self.gui.panelBY:
			self.scroll_position += int(mouse_wheel * 30 * gui.scale * -1)
			self.auto_scroll = False
		y -= self.scroll_position

		if self.data:

			self.ready[cache_title] = 1

			for line in self.data:

				if window_size[0] > y > 0:
					min_space = 0
					for ch in line[1]:
						xx = max(x + ch[1], min_space)

						if len(ch[0]) == 2 and ch[0][1].lower() == "x":
							min_space = 1 + xx + self.ddt.text((xx, y), ch[0], [220, 120, 240, 255], 214)
						else:
							min_space = 1 + xx + self.ddt.text((xx, y), ch[0], [140, 120, 240, 255], 213)
				y += 15 * self.gui.scale

				if window_size[0] > y > 0:
					colour = colours.lyrics
					if colours.lm:
						colour = [30, 30, 30, 255]
					self.ddt.text((x, y), line[0], colour, 16)

				y += 18 * self.gui.scale

			return True
		return False
