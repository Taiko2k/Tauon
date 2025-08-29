"""Guitar Chord Tauon module

At the moment unused, and not fully working due to broken vars which used to be global.

Used to work with api.guitarchord.com in the past.
"""
from __future__ import annotations

import logging
import os
import urllib.parse
import sdl3
from pathlib import Path
from typing import TYPE_CHECKING

import requests

from tauon.t_modules.t_extra import ColourRGBA, TestTimer, filename_safe

if TYPE_CHECKING:
	from tauon.t_modules.t_main import TrackClass, Tauon

# TODO(Martin): Dupe code here to make things work in a dirty fashion until t_main gets a bigger rework
#from tauon.t_modules.t_main import copy_from_clipboard

def copy_from_clipboard():
	return sdl3.SDL_GetClipboardText().decode()
# ENDTODO

class GuitarChords:
	def __init__(
		self, tauon: Tauon, mouse_wheel: float, mouse_position: list[int], window_size: list[int],
	) -> None:
		self.inp                   = tauon.inp
		self.ddt                   = tauon.ddt
		self.gui                   = tauon.gui
		self.pctl                  = tauon.pctl
		self.colours               = tauon.colours
		self.store_a               = tauon.user_directory / "guitar-chords-a"  # inline format
		self.store_b               = tauon.user_directory / "guitar-chords-b"  # 2 lines format
		self.show_message          = tauon.show_message
		self.mouse_wheel           = mouse_wheel
		self.mouse_position        = mouse_position
		self.window_size           = window_size
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
		"""Search guitarparty.com for the lyrics with guitar chords.

		[2025-01-22] Note from site owners:
			We stopped maintaining a public facing Api with API keys in our latest version as of about late 2020.
			We have focused on providing our own features and services for our subscribers instead.
			You can use the internal public API intended for the frontend as you are doing, but it is undocumented and might not be stable.
			That being said, you can search for songs using the search api: https://www.guitarparty.com/api/v3/core/search/?q=jolene
			There is no filtering available in the core/songs url
			The search API does search in title as well as lyrics, it's the exact same search function as the frontpage and header of the site use.
			If you find a match in the search API, then you can fetch the song detail using the id, we have chords in all of our songs.
		"""
		if not track_object.title:
			self.show_message(_("Insufficient metadata to search"))
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
			self.show_message(_("Clipboard has no text"))
			self.inp.mouse_click = False
			return

		cache_title = self.get_cache_title(track)

		t = t.replace("\r", "")

		f = (self.store_b / cache_title).open("w", encoding="utf-8")
		f.write(t)
		f.close()

	def parse_b(self, lines: list[str]) -> None:
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
			Path.mkdir(self.store_a, parents=True)

		if not self.store_b.exists():
			Path.mkdir(self.store_b, parents=True)

	def fetch(self, track: TrackClass) -> None:
		if self.test_ready_status(track) != 0:
			return

		cache_title = self.get_cache_title(track)

		try:
			response = requests.get(
				f"https://www.guitarparty.com/api/v3/core/search/?format=json&q={urllib.parse.quote(cache_title)}",
				timeout=15)
		except Exception:
			logging.exception("Error finding matching track on GuitarParty")
			self.show_message(_("Error finding matching track on GuitarParty"))
			self.inp.mouse_click = False
			self.ready[cache_title] = 2
			return

		try:
			parsed_response = response.json()
		except Exception:
			logging.exception("Failed to parse search response from www.guitarparty.com")
			logging.debug(response)
			self.inp.mouse_click = False
			self.ready[cache_title] = 2
			return

		if len(parsed_response) == 0:
			logging.info("Track not found on GuitarParty")
			self.show_message(_("Track not found on GuitarParty"))
			self.inp.mouse_click = False
			self.ready[cache_title] = 2
			return

		logging.debug(f"Found {len(parsed_response)} results from guitarparty.com, using the first one")

		song = parsed_response[0]

		try:
			response = requests.get(
				f"https://www.guitarparty.com/api/v3/core/songs/{song['id']}/?format=json&q={urllib.parse.quote(cache_title)}",
				timeout=15)
		except Exception:
			logging.exception("Error getting song from GuitarParty")
			self.show_message(_("Error getting song from GuitarParty"))
			self.inp.mouse_click = False
			self.ready[cache_title] = 2
			return

		try:
			parsed_response = response.json()
		except Exception:
			logging.exception("Failed to parse response from www.guitarparty.com")
			logging.debug(response)
			self.inp.mouse_click = False
			self.ready[cache_title] = 2
			return

		if "song" not in parsed_response:
			logging.error("Field 'song' from guitarparty.com is empty!")
			logging.debug(parsed_response)
			self.inp.mouse_click = False
			self.ready[cache_title] = 2
			return

		result = parsed_response["song"]

		self.prep_folders()
		with (self.store_a / cache_title).open("w", encoding="utf-8") as file:
			file.write(result)
		self.ready[cache_title] = 1

		if "title" in parsed_response:
			logging.debug(f"Wrote chords for found song title: {parsed_response['title']}")
		else:
			logging.error("Song had no title?!")
			logging.debug(parsed_response)

	def test_ready_status(self, track: TrackClass) -> int:
		"""Return:

		0 not searched
		1 ready
		2 failed
		"""
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
		return filename_safe(name, sub="_")

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

		if self.auto_scroll and self.pctl.playing_length > 20:
			progress = max(0, self.pctl.playing_time - 12) / (self.pctl.playing_length - 3)
			height = len(self.data) * (18 + 15) * self.gui.scale

			self.scroll_position = height * progress
			# gui.update += 1
			self.gui.frame_callback_list.append(TestTimer(0.3))
				# time.sleep(0.032)

		if self.mouse_wheel and self.gui.panelY < self.mouse_position[1] < self.window_size[1] - self.gui.panelBY:
			self.scroll_position += int(self.mouse_wheel * 30 * self.gui.scale * -1)
			self.auto_scroll = False
		y -= self.scroll_position

		if self.data:
			self.ready[cache_title] = 1
			for line in self.data:
				if self.window_size[0] > y > 0:
					min_space = 0
					for ch in line[1]:
						xx = max(x + ch[1], min_space)

						if len(ch[0]) == 2 and ch[0][1].lower() == "x":
							min_space = 1 + xx + self.ddt.text((xx, y), ch[0], ColourRGBA(220, 120, 240, 255), 214)
						else:
							min_space = 1 + xx + self.ddt.text((xx, y), ch[0], ColourRGBA(140, 120, 240, 255), 213)
				y += 15 * self.gui.scale

				if self.window_size[0] > y > 0:
					colour = self.colours.lyrics
					if self.colours.lm:
						colour = ColourRGBA(30, 30, 30, 255)
					self.ddt.text((x, y), line[0], colour, 16)

				y += 18 * self.gui.scale

			return True
		return False
