"""Tauon Music Box - Theme reading module"""

# Copyright © 2015-2022, Taiko2k captain(dot)gxj(at)gmail.com

#     This file is part of Tauon Music Box.
#
#     Tauon Music Box is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Tauon Music Box is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Lesser General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Tauon Music Box.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import annotations

import base64
import io
import json
import logging
import os
import sdl3
from typing import TYPE_CHECKING

from PIL import Image

from tauon.t_modules.t_extra import ColourRGBA, rgb_add_hls, test_lumi

if TYPE_CHECKING:
	from pathlib import Path
	from tauon.t_modules.t_draw import TDraw
	from tauon.t_modules.t_main import ColoursClass, Tauon

def get_colour_from_line(cline: str) -> ColourRGBA:
	colour     = [-1, -1, -1, -1]
	colour_str = ["", "", "", ""]
	mode = 0

	is_hex = False
	if "," not in cline[:8]:
		if cline[:6].isalnum():
			is_hex = True
		if cline[0] == "#" and cline[1:7].isalnum() and cline[7].isspace() and cline[8].isspace():
			is_hex = True
		if cline[0] == "#" and cline[1:9].isalnum() and cline[9].isspace() and cline[10].isspace():
			is_hex = True

	if is_hex:
		# hex mode
		if cline.startswith("0x"):
			cline = cline[2:]
		if cline.startswith("#"):
			cline = cline[1:]
		ll = cline
		a = 255
		r = int(ll[0] + ll[1], 16)
		g = int(ll[2] + ll[3], 16)
		b = int(ll[4] + ll[5], 16)
		if ll[6].isalnum() and ll[7].isalnum():
			a = int(ll[6] + ll[7], 16)
		return ColourRGBA(r, g, b, a)
	# rgb mode
	for i in cline:
		if i.isdigit():
			colour_str[mode] += i
		elif i == ",":
			mode += 1

	# Convert str list to int list
	for b in range(len(colour_str)):
		if colour_str[b] == "":
			colour[b] = 255
		else:
			colour[b] = int(colour_str[b])

	return ColourRGBA(colour[0], colour[1], colour[2], colour[3])


def load_theme(colours: ColoursClass, path: Path) -> None:

	with path.open(encoding="utf-8") as f:
		content = f.readlines()
		status_text_color_defined = 0
		lyrics_panel_color_defined = 0
		# allows program to fallback on old colors if new options not provided
		for p in content:
			p = p.strip()
			if p.startswith("#"):
				continue
			if "# " in p:
				p = p.split("# ")[0]
			if not p:
				continue
			if p[0] == "#" and ("-" in p[:7] or " " in p[:7] or "\t" in p[:7]):
				continue
			if p.startswith("deco="):
				colours.deco = p.split("=", 1)[1].strip()
			if "light-mode" in p:
				colours.light_mode()
			if "window frame" in p:
				colours.window_frame = get_colour_from_line(p)
			if "gallery highlight" in p:
				colours.gallery_highlight = get_colour_from_line(p)
			if "index playing" in p:
				colours.index_playing = get_colour_from_line(p)
			if "time playing" in p:
				colours.time_text = get_colour_from_line(p)
			if "artist playing" in p:
				colours.artist_playing = get_colour_from_line(p)
			if "album line" in p:  # Bad name
				colours.album_text = get_colour_from_line(p)
			if "track album" in p:
				colours.album_text = get_colour_from_line(p)
			if "album playing" in p:
				colours.album_playing = get_colour_from_line(p)
			if "top panel" in p or "player background" in p:
				colours.top_panel_background = get_colour_from_line(p)

				if test_lumi(colours.bottom_panel_colour) < 0.2:
					colours.corner_icon = ColourRGBA(0, 0, 0, 60)
				elif test_lumi(colours.bottom_panel_colour) < 0.8:
					colours.corner_icon = ColourRGBA(40, 40, 40, 255)
				else:
					colours.corner_icon = ColourRGBA(255, 255, 255, 30)

				if test_lumi(colours.bottom_panel_colour) < 0.2:
					colours.corner_icon = ColourRGBA(0, 0, 0, 60)

				if not colours.lm:
					colours.corner_button = rgb_add_hls(colours.top_panel_background, 0, 0.18, 0)
			if "status text" in p:
				status_text_temp = get_colour_from_line(p)
				
				colours.status_text_over = status_text_temp #rgb_add_hls(status_text_temp, 0, 0.83, 0)
				colours.status_text_normal = rgb_add_hls(status_text_temp, 0, 0.30, -0.15)
				status_text_color_defined = 1
				
			if "corner button off" in p:
				colours.corner_button = get_colour_from_line(p)
			if "corner button on" in p:
				colours.corner_button_active = get_colour_from_line(p)
			if "menu button normal" in p:
				colours.status_text_normal = get_colour_from_line(p)
			if "menu button hover" in p:
				colours.status_text_over = get_colour_from_line(p)
			if "queue panel" in p:
				colours.queue_background = get_colour_from_line(p)
			if "side panel" in p:
				colours.side_panel_background = get_colour_from_line(p)
				colours.playlist_box_background = colours.side_panel_background
			if "lyrics panel" in p:
				colours.lyrics_panel_background = get_colour_from_line(p)
				lyrics_panel_color_defined = 1
			if "gallery background" in p:
				colours.gallery_background = get_colour_from_line(p)
			if "playlist panel" in p:  # bad name
				colours.playlist_panel_background = get_colour_from_line(p)
			if "tracklist panel" in p:
				colours.playlist_panel_background = get_colour_from_line(p)
			if "track line" in p:
				colours.title_text = get_colour_from_line(p)
			if "track missing" in p:
				colours.playlist_text_missing = get_colour_from_line(p)
			if "playing highlight" in p:
				colours.row_playing_highlight = get_colour_from_line(p)
			if "track time" in p:
				colours.bar_time = get_colour_from_line(p)
			if "fav line" in p:
				colours.star_line = get_colour_from_line(p)
			if "folder title" in p:
				colours.folder_title = get_colour_from_line(p)
			if "folder line" in p:
				colours.folder_line = get_colour_from_line(p)
			if "buttons off" in p:
				colours.media_buttons_off = get_colour_from_line(p)
			if "buttons over" in p:
				colours.media_buttons_over = get_colour_from_line(p)
			if "buttons active" in p:
				colours.media_buttons_active = get_colour_from_line(p)
			if "playing time" in p:
				colours.time_playing = get_colour_from_line(p)
			if "track index" in p:
				colours.index_text = get_colour_from_line(p)
			if "track playing" in p:
				colours.title_playing = get_colour_from_line(p)
			if "select highlight" in p:
				colours.row_select_highlight = get_colour_from_line(p)
			if "track artist" in p:
				colours.artist_text = get_colour_from_line(p)
			if "tab active line" in p:  # bad name
				colours.tab_text_active = get_colour_from_line(p)
			if "tab line" in p:  # bad name
				colours.tab_text = get_colour_from_line(p)
			if "tab active text" in p:
				colours.tab_text_active = get_colour_from_line(p)
			if "tab text" in p:
				colours.tab_text = get_colour_from_line(p)
			if "tab background" in p:
				colours.tab_background = get_colour_from_line(p)
			if "tab over" in p:
				colours.tab_highlight = get_colour_from_line(p)
			if "tab active background" in p:
				colours.tab_background_active = get_colour_from_line(p)
			if "title info" in p:
				colours.side_bar_line1 = get_colour_from_line(p)
			if "extra info" in p:
				colours.side_bar_line2 = get_colour_from_line(p)
			if "bottom title" in p:
				colours.bar_title_text = get_colour_from_line(p)
			if "scroll bar" in p:
				colours.scroll_colour = get_colour_from_line(p)
			if "seek bar" in p:
				colours.seek_bar_fill = get_colour_from_line(p)
			if "seek bg" in p:
				colours.seek_bar_background = get_colour_from_line(p)
			if "volume bar" in p:
				colours.volume_bar_fill = get_colour_from_line(p)
			if "volume bg" in p:
				colours.volume_bar_background = get_colour_from_line(p)
			if "mode off" in p:
				colours.mode_button_off = get_colour_from_line(p)
			if "mode over" in p:
				colours.mode_button_over = get_colour_from_line(p)
			if "mode on" in p:
				colours.mode_button_active = get_colour_from_line(p)
			if "art border" in p:
				colours.art_box = get_colour_from_line(p)
			if "tb line" in p:
				colours.tb_line = get_colour_from_line(p)
			if "music vis" in p:
				colours.vis_colour = get_colour_from_line(p)
			if "menu background" in p:
				colours.menu_background = get_colour_from_line(p)
			if "menu text" in p:
				colours.menu_text = get_colour_from_line(p)
			if "menu disable" in p:
				colours.menu_text_disabled = get_colour_from_line(p)
			if "menu icons" in p:
				colours.menu_icons = get_colour_from_line(p)
			if "menu highlight" in p:
				colours.menu_highlight_background = get_colour_from_line(p)
			if "menu border" in p:
				colours.menu_tab = get_colour_from_line(p)
			if "lyrics showcase" in p:
				colours.lyrics = get_colour_from_line(p)
			if "bottom panel" in p:
				colours.bottom_panel_colour = get_colour_from_line(p)
				# colours.menu_background = colours.bottom_panel_colour
			if "mini bg" in p:
				colours.mini_mode_background = get_colour_from_line(p)
			if "mini border" in p:
				colours.mini_mode_border = get_colour_from_line(p)
			if "mini text 1" in p:
				colours.mini_mode_text_1 = get_colour_from_line(p)
			if "mini text 2" in p:
				colours.mini_mode_text_2 = get_colour_from_line(p)
			if "column-" in p:
				key = p[p.find("column-") + 7:].replace("-", " ").lower().title().rstrip()
				value = get_colour_from_line(p)
				colours.column_colours[key] = value
			if "column+" in p:
				key = p[p.find("column+") + 7:].replace("-", " ").lower().title().rstrip()
				value = get_colour_from_line(p)
				colours.column_colours_playing[key] = value
			if "menu bg" in p:
				colours.menu_background = get_colour_from_line(p)
			if "playlist box bg" in p:  # bad name
				colours.playlist_box_background = get_colour_from_line(p)
			if "playlist background" in p:
				colours.playlist_box_background = get_colour_from_line(p)

			if "box background" in p:
				colours.box_background = get_colour_from_line(p)
			if "box border" in p:
				colours.box_border = get_colour_from_line(p)
			if "box text border" in p:
				colours.box_text_border = get_colour_from_line(p)
			if "box text label" in p:
				colours.box_text_label = get_colour_from_line(p)

			if "box title text" in p:
				colours.box_title_text = get_colour_from_line(p)
			if "box text normal" in p:
				colours.box_text = get_colour_from_line(p)
			if "box sub text" in p:
				colours.box_sub_text = get_colour_from_line(p)
			if "box input text" in p:
				colours.box_input_text = get_colour_from_line(p)

			if "box button text highlight" in p:
				colours.box_button_text_highlight = get_colour_from_line(p)
			if "box button text normal" in p:
				colours.box_button_text = get_colour_from_line(p)
			if "box button background normal" in p:
				colours.box_button_background = get_colour_from_line(p)
			if "box button background highlight" in p:
				colours.box_button_background_highlight = get_colour_from_line(p)
			if "box button border" in p:
				colours.box_check_border = get_colour_from_line(p)

			if "window buttons background" in p:
				colours.window_buttons_bg = get_colour_from_line(p)
			if "window buttons on" in p:
				colours.window_buttons_bg_over = get_colour_from_line(p)
			if "window buttons icon off" in p:
				colours.window_button_icon_off = get_colour_from_line(p)
				colours.window_button_x_off = colours.window_button_icon_off
			if "window buttons icon over" in p:
				colours.window_buttons_icon_over = get_colour_from_line(p)
				colours.window_button_x_on = colours.window_buttons_icon_over
			if "window button x on" in p:
				colours.window_button_x_on = get_colour_from_line(p)
			if "window button x off" in p:
				colours.window_button_x_off = get_colour_from_line(p)
			if "column bar background" in p:
				colours.column_bar_background = get_colour_from_line(p)

			if "artist bio background" in p:
				colours.artist_bio_background = get_colour_from_line(p)
			if "artist bio text" in p:
				colours.artist_bio_text = get_colour_from_line(p)
			# if "panel button off" in p:
			#	 colours.corner_button = get_colour_from_line(p)
			# if "panel button on" in p:
			#	 colours.corner_button_active = get_colour_from_line(p)
		if status_text_color_defined == 0:
				colours.status_text_over = rgb_add_hls(colours.top_panel_background, 0, 0.83, 0)
				colours.status_text_normal = rgb_add_hls(colours.top_panel_background, 0, 0.30, -0.15)
		if lyrics_panel_color_defined == 0:
			colours.lyrics_panel_background = colours.side_panel_background
		colours.post_config()
		if colours.lm:
			colours.light_mode()


class Drawable:
	def __int__(self) -> None:
		self.location = 1
		self.x = 0
		self.y = 0
		self.w = 100
		self.y = 100
		self.rect = None
		self.texture = None

class Deco:
	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.renderer = None
		self.pctl = tauon.pctl
		self.prefs = tauon.prefs
		self.drawables = []

	def unload(self) -> None:
		for item in self.drawables:
			sdl3.SDL_DestroyTexture(item.texture)
		self.drawables.clear()

	def load(self, name: str) -> None:
		self.unload()
		if not name:
			return

		decos = self.get_themes(deco=True, dirs=self.tauon.dirs)

		if name not in decos:
			logging.error("Missing deco file")
			return

		target = decos[name]
		with open(target) as f:
			j = json.load(f)

		if "images" not in j:
			return
		images = j["images"]
		if not images:
			return
		item = images[0]
		if item.get("location") != 1:
			return
		x = int(item.get("x-margin", 0))
		y = int(item.get("y-margin", 0))
		opacity = int(item.get("opacity", 100))
		logical_h = int(item.get("logical-height", 400))
		file = item.get("file")
		if file:
			path = os.path.join(os.path.dirname(target), file)
			im = Image.open(path)
		else:
			s = item.get("image-data")
			if not s:
				return
			b = io.BytesIO(base64.b64decode(s))
			im = Image.open(b)

		w, h = im.size
		scale = self.tauon.gui.scale
		if not abs(h - (logical_h * scale)) < 10:
			new_h = round(logical_h * scale)
			ratio = w / h
			new_w = round(new_h * ratio)
			im = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
			w, h = new_w, new_h

		g = io.BytesIO()
		g.seek(0)
		im.save(g, "PNG")
		g.seek(0)
		s_image = self.tauon.ddt.load_image(g)
		texture = sdl3.SDL_CreateTextureFromSurface(self.renderer, s_image)
		sdl3.SDL_SetTextureAlphaMod(texture, opacity)
		sdl3.SDL_DestroySurface(s_image)
		sdl_rect = sdl3.SDL_FRect(0, 0, w, h)

		drawable = Drawable()
		drawable.x = x
		drawable.y = y
		drawable.w = w
		drawable.h = h
		drawable.rect = sdl_rect
		drawable.texture = texture
		self.drawables.append(drawable)

	def draw(self, ddt: TDraw, x: int, y: int, pretty_text: bool = False) -> None:
		if self.drawables:
			d = self.drawables[0]
			d.rect.x = round(x - int(d.w + round(d.x * self.tauon.gui.scale)))
			d.rect.y = round(y - int(d.h + round(d.y * self.tauon.gui.scale)))
			sdl3.SDL_RenderTexture(self.renderer, d.texture, None, d.rect)

			if pretty_text:
				ddt.pretty_rect = (d.rect.x, d.rect.y, d.rect.w, d.rect.h)
				ddt.alpha_bg = True
