"""Tauon Music Box - Basic Drawing and Text Drawing Functions Module"""

# Copyright © 2015-2019, Taiko2k captain(dot)gxj(at)gmail.com

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

import ctypes
import io
import logging
import math
import sys
from ctypes import c_bool, c_int, c_size_t, pointer
from typing import TYPE_CHECKING

import sdl3
from PIL import Image

from tauon.t_modules.t_extra import Timer, alpha_blend, coll_rect

if TYPE_CHECKING:
	from io import BytesIO

	from tauon.t_modules.t_main import Tauon

try:
	from jxlpy import JXLImagePlugin
	logging.info("Found jxlpy for JPEG XL support")
except ModuleNotFoundError:
	logging.warning("Unable to import jxlpy, JPEG XL support will be disabled.")
except Exception:
	logging.exception("Unkown error trying to import jxlpy, JPEG XL support will be disabled.")


system = "Linux"
if sys.platform == "win32":
	system = "Linux" #"windows"
	import os
	os.environ["PANGOCAIRO_BACKEND"] = "fc"

#if system == "Linux":
import struct

import cairo
import gi
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango, PangoCairo

#else:
#	import struct
#	from ctypes import CFUNCTYPE, POINTER, byref, c_void_p, windll
#
#	import win32api
#	import win32con
#	import win32gui
#	import win32ui



class QuickThumbnail:

	def __init__(self, tauon: Tauon) -> None:
		self.ddt      = tauon.ddt
		self.renderer = tauon.renderer
		self.items: list[QuickThumbnail] = []
		self.queue: list[QuickThumbnail] = []
		self.rect = sdl3.SDL_FRect(0., 0.)
		self.texture = None
		self.surface = None
		self.size = 50
		self.alive = False
		self.url = None

	def destruct(self) -> None:
		if self.surface:
			sdl3.SDL_DestroySurface(self.surface)
			self.surface = None
		if self.texture:
			sdl3.SDL_DestroyTexture(self.texture)
			self.texture = None
		self.alive = False

	def read_and_thumbnail(self, f: str, width: int, height: int) -> None:

		g = io.BytesIO()
		g.seek(0)
		im = Image.open(f)
		im.thumbnail((width, height), Image.Resampling.LANCZOS)
		im.save(g, "PNG")
		g.seek(0)
		self.surface = self.ddt.load_image(g)
		#self.items.append(self)
		self.alive = True

	def prime(self) -> None:

		texture = sdl3.SDL_CreateTextureFromSurface(self.renderer, self.surface)
		sdl3.SDL_DestroySurface(self.surface)
		self.surface = None
		tex_w = pointer(c_int(0))
		tex_h = pointer(c_int(0))
		sdl3.SDL_QueryTexture(texture, None, None, tex_w, tex_h)
		self.rect.w = int(tex_w.contents.value)
		self.rect.h = int(tex_h.contents.value)
		self.texture = texture

	def draw(self, x: int, y: int) -> bool | None:
		if len(self.items) > 30:
			img = self.items[0]
			img.destruct()
			self.items.remove(img)
		if not self.alive:
			if self not in self.queue:
				self.queue.append(self)
			return False
		if not self.texture:
			self.prime()
		self.rect.x = round(x)
		self.rect.y = round(y)
		sdl3.SDL_RenderCopy(self.renderer, self.texture, None, self.rect)

		return True

# TODO(Martin): This block never executes - https://github.com/Taiko2k/Tauon/issues/1318
if sys.platform == "win32":
	class RECT(ctypes.Structure):
		_fields_ = [
			("left", ctypes.c_long),
			("top", ctypes.c_long),
			("right", ctypes.c_long),
			("bottom", ctypes.c_long),
		]

	def RGB(r: int, g: int, b: int) -> int:
		return r | (g << 8) | (b << 16)

	def Wcolour(colour: list[int]) -> int:
		return colour[0] | (colour[1] << 8) | (colour[2] << 16)

	def native_bmp_to_sdl(hdc, bitmap_handle, width: int, height: int): # -> tuple[Unknown, Array[c_char]]
		bmpheader = struct.pack(
			"LHHHH", struct.calcsize("LHHHH"),
			width, height, 1, 24) #w,h, planes=1, bitcount)

		c_bmpheader = ctypes.c_buffer(bmpheader)

		#3 bytes per pixel, pad lines to 4 bytes
		c_bits = ctypes.c_buffer(b" " * (height * ((width*3 + 3) & -4)))

		res = ctypes.windll.gdi32.GetDIBits(
			hdc, bitmap_handle, 0, height,
			c_bits, c_bmpheader,
			win32con.DIB_RGB_COLORS)

		if not res:
			raise OSError("native_bmp_to_pil failed: GetDIBits")

		# TODO(Martin): Add the rest of the types in this function:
		logging.debug(f"IF YOU SEE THIS MESSAGE, ADD THESE TYPES TO native_bmp_to_sdl(): HDC: {type(hdc)}, bitmap_handle: {type(bitmap_handle)}, returnType:{type(sdl3.SDL_CreateSurfaceFrom(width, height, sdl3.SDL_PIXELFORMAT_BGR24, ctypes.pointer(c_bits), (width*3 + 3) & -4))}")
		# We need to keep c_bits pass else it may be garbage collected
		return sdl3.SDL_CreateSurfaceFrom(width, height, sdl3.SDL_PIXELFORMAT_BGR24, ctypes.pointer(c_bits), (width*3 + 3) & -4), c_bits


	class Win32Font:

		def __init__(
			self, name: str, height: int, weight:int = win32con.FW_NORMAL,
			italic: bool = False, underline: bool = False) -> None:

			self.font = win32ui.CreateFont({
				"name": name, "height": height,
				"weight": weight, "italic": italic, "underline": underline}) #'charset': win32con.MAC_CHARSET})

			#create a compatible DC we can use to draw:

			self.desktopHwnd = win32gui.GetDesktopWindow()
			self.desktopDC = win32gui.GetWindowDC(self.desktopHwnd)
			self.mfcDC = win32ui.CreateDCFromHandle(self.desktopDC)
			self.drawDC = self.mfcDC.CreateCompatibleDC()

			#initialize it

			self.drawDC.SelectObject(self.font)

		def get_metrics(self, text: str, max_x: int, wrap: bool) -> tuple[int, int]:

			#return self.drawDC.GetTextExtent(text)

			rect = RECT(0,0,0,0)
			rect.left = 0
			rect.right = round(max_x)
			rect.top = 0
			rect.bottom = 0

				#windll.User32.DrawTextW(t, text, len(text)) #, rect, win32con.DT_WORDBREAK)
			t = self.drawDC.GetSafeHdc()

			if wrap:

				windll.User32.DrawTextW(t, text, len(text), pointer(rect), win32con.DT_WORDBREAK | win32con.DT_CALCRECT)
			else:
				windll.User32.DrawTextW(t, text, len(text), pointer(rect), win32con.DT_CALCRECT | win32con.DT_END_ELLIPSIS)

			return rect.right, rect.bottom


		def renderText(self, text: str, bg: list[int], fg: list[int], wrap: bool = False, max_x: int = 100, max_y: int | None = None):

			self.drawDC.SetTextColor(Wcolour(fg))

			t = self.drawDC.GetSafeHdc()

			win32gui.SetBkMode(t, win32con.TRANSPARENT)

			#create the compatible bitmap:

			#w,h = self.drawDC.GetTextExtent(text)
			w, h = self.get_metrics(text, max_x, wrap)

			#logging.info(self.drawDC.GetTextFace())

			#w += 1
			#if wrap:
			#	h = int((w / max_x) * h) + h
			#	w = max_x + 1
			if max_y is not None:
				h = max_y

			saveBitMap = win32ui.CreateBitmap()

			saveBitMap.CreateCompatibleBitmap(self.mfcDC, w, h)

			self.drawDC.SelectObject(saveBitMap)

			#draw it

			br = win32ui.CreateBrush(win32con.BS_SOLID, Wcolour(bg), 0)

			self.drawDC.FillRect((0, 0, w, h), br)

			#self.drawDC.DrawText(text, (0, 0, w, h), win32con.DT_LEFT)

			#windll.gdi32.TextOutW(t, 0, 0, "test", 5)

			if wrap:
				rect = RECT(0,0,0,0)
				rect.left = 0
				rect.right = round(max_x)
				rect.top = 0
				rect.bottom = round(h)

				#windll.User32.DrawTextW(t, text, len(text)) #, rect, win32con.DT_WORDBREAK)
				windll.User32.DrawTextW(t, text, len(text), pointer(rect), win32con.DT_WORDBREAK)
			else:

				rect = RECT(0,0,0,0)
				rect.left = 0
				rect.right = round(max_x)
				rect.top = 0
				rect.bottom = round(h)

				#windll.User32.DrawTextW(t, text, len(text)) #, rect, win32con.DT_WORDBREAK)
				windll.User32.DrawTextW(t, text, len(text), pointer(rect), win32con.DT_END_ELLIPSIS)


				#windll.gdi32.TextOutW(t, 0, 0, text, len(text))

			#logging.info(rects)
			#logging.info(text)
			#windll.gdi32.ExtTextOutW(t, 0, 0, None, rect, text, len(text), None)
			#convert to SDL surface
			im, c_bits = native_bmp_to_sdl(self.drawDC.GetSafeHdc(), saveBitMap.GetHandle(), w, h)
			#clean-up
			win32gui.DeleteObject(saveBitMap.GetHandle())

			return im, c_bits


		def __del__(self) -> None:

			self.mfcDC.DeleteDC()
			self.drawDC.DeleteDC()
			win32gui.ReleaseDC(self.desktopHwnd, self.desktopDC)
			win32gui.DeleteObject(self.font.GetSafeHandle())

		def __del__(self) -> None:

			win32gui.DeleteObject(self.font.GetSafeHandle())

perf = Timer()

class TDraw:

	def __init__(self, renderer: sdl3.LP_SDL_Renderer) -> None:

		# All
		self.renderer = renderer
		self.scale = 1
		self.force_subpixel_text = False

		# Drawing
		self.sdlrect = sdl3.SDL_FRect(10., 10., 10., 10.)

		# Text and Fonts
		self.source_rect = sdl3.SDL_FRect(0., 0., 0., 0.)
		self.dest_rect = sdl3.SDL_FRect(0., 0., 0., 0.)


		if system == "Linux":
			self.surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0)
			self.context = cairo.Context(self.surf)
			self.layout = PangoCairo.create_layout(self.context)

		else:
			self.cache = {}
			self.ca_li = []
			self.y_offset_dict = {}

		self.text_background_colour = [0, 0, 0, 255]
		self.pretty_rect: tuple[int, int, int, int] | None = None
		self.real_bg:     bool = False
		self.alpha_bg:    bool = False
		self.force_gray:  bool = False
		self.f_dict: dict[str, Win32Font | tuple[str, int, int]] = {}
		self.ttc = {}
		self.ttl = []

		self.was_truncated = False

	def load_image(self, g: BytesIO) -> sdl3.LP_SDL_Surface:

		size = g.getbuffer().nbytes
		pointer = ctypes.c_void_p(ctypes.addressof(ctypes.c_char.from_buffer(g.getbuffer())))
		stream = sdl3.SDL_IOFromMem(pointer, c_size_t(size))
		return sdl3.IMG_Load_IO(stream, c_bool(True))

	def rect_s(self, rectangle: tuple[int, int, int, int], colour: tuple[int, int, int, int], thickness: int) -> None:
		sdl3.SDL_SetRenderDrawColor(self.renderer, colour[0], colour[1], colour[2], colour[3])
		x, y, w, h = (round(x) for x in rectangle)
		th = math.floor(thickness)
		self.sdlrect.x = x - th
		self.sdlrect.y = y - th
		self.sdlrect.w = th
		self.sdlrect.h = h + th
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect) # left
		self.sdlrect.x = x - th
		self.sdlrect.y = y + h
		self.sdlrect.w = w + th
		self.sdlrect.h = th
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect) # bottom
		self.sdlrect.x = x
		self.sdlrect.y = y - th
		self.sdlrect.w = w + th
		self.sdlrect.h = th
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect) # top
		self.sdlrect.x = x + w
		self.sdlrect.y = y
		self.sdlrect.w = th
		self.sdlrect.h = h + th
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect) # right

	def rect_si(self, rectangle: tuple[int, int, int, int], colour: tuple[int, int, int, int], thickness: int) -> None:
		sdl3.SDL_SetRenderDrawColor(self.renderer, colour[0], colour[1], colour[2], colour[3])
		x, y, w, h = (round(x) for x in rectangle)
		th = math.floor(thickness)
		self.sdlrect.x = x
		self.sdlrect.y = y
		self.sdlrect.w = th
		self.sdlrect.h = h
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect) # left
		self.sdlrect.x = x
		self.sdlrect.y = y + (h - th)
		self.sdlrect.w = w
		self.sdlrect.h = th
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect) # bottom
		self.sdlrect.x = x
		self.sdlrect.y = y
		self.sdlrect.w = w
		self.sdlrect.h = th
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect) # top
		self.sdlrect.x = x + (w - th)
		self.sdlrect.y = y
		self.sdlrect.w = th
		self.sdlrect.h = h
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect) # right

	def rect_a(self, location_xy: list[int], size_wh: list[int], colour: tuple[int, int, int, int]) -> None:
		self.rect((location_xy[0], location_xy[1], size_wh[0], size_wh[1]), colour)

	def clear_rect(self, rectangle: tuple[int, int, int, int]) -> None:
		sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_NONE)
		sdl3.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 0)

		self.sdlrect.x = float(rectangle[0])
		self.sdlrect.y = float(rectangle[1])
		self.sdlrect.w = float(rectangle[2])
		self.sdlrect.h = float(rectangle[3])

		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect)
		sdl3.SDL_SetRenderDrawBlendMode(self.renderer, sdl3.SDL_BLENDMODE_BLEND)

	def rect(self, rectangle: tuple[int, int, int, int], colour: tuple[int, int, int, int]) -> None:
		sdl3.SDL_SetRenderDrawColor(self.renderer, colour[0], colour[1], colour[2], colour[3])

		self.sdlrect.x = float(rectangle[0])
		self.sdlrect.y = float(rectangle[1])
		self.sdlrect.w = float(rectangle[2])
		self.sdlrect.h = float(rectangle[3])


		#if fill:
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect)
		# else:
		#	 sdl3.SDL_RenderDrawRect(self.renderer, self.sdlrect)

	def bordered_rect(self, rectangle: tuple[int, int, int, int], fill_colour: list[int], outer_colour: list[int], border_size: int) -> None:

		self.sdlrect.x = round(rectangle[0]) - border_size
		self.sdlrect.y = round(rectangle[1]) - border_size
		self.sdlrect.w = round(rectangle[2]) + border_size + border_size
		self.sdlrect.h = round(rectangle[3]) + border_size + border_size
		sdl3.SDL_SetRenderDrawColor(self.renderer, outer_colour[0], outer_colour[1], outer_colour[2], outer_colour[3])
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect)
		self.sdlrect.x = round(rectangle[0])
		self.sdlrect.y = round(rectangle[1])
		self.sdlrect.w = round(rectangle[2])
		self.sdlrect.h = round(rectangle[3])
		sdl3.SDL_SetRenderDrawColor(self.renderer, fill_colour[0], fill_colour[1], fill_colour[2], fill_colour[3])
		sdl3.SDL_RenderFillRect(self.renderer, self.sdlrect)

	def line(self, x1: int, y1: int, x2: int, y2: int, colour: list[int]) -> None:

		sdl3.SDL_SetRenderDrawColor(self.renderer, colour[0], colour[1], colour[2], colour[3])
		sdl3.SDL_RenderLine(self.renderer, round(x1), round(y1), round(x2), round(y2))

	def get_text_w(self, text: str, font: int, height: bool = False) -> int:

		x, y = self.get_text_wh(text, font, 3000)
		if height:
			return y
		return x

	def clear_text_cache(self) -> None:

		for key in self.ttl:
			so = self.ttc[key]
			sdl3.SDL_DestroyTexture(so[1])

		self.ttc.clear()
		self.ttl.clear()

	def win_prime_font(self, name: str, size: int, user_handle: str, weight: int, y_offset: int = 0) -> None:

		self.f_dict[user_handle] = Win32Font(name, int(size * self.scale), weight)
		self.y_offset_dict[user_handle] = y_offset

	def prime_font(self, name: str, size: int, user_handle: str, offset: int = 0) -> None:

		self.f_dict[user_handle] = (name + " " + str(size * self.scale), offset, size * self.scale)

	def get_text_wh(self, text: str, font: int, max_x: int, wrap: bool = False) -> tuple[int, int] | None:

		if system == "Linux":
			self.layout.set_font_description(Pango.FontDescription(self.f_dict[font][0]))
			self.layout.set_ellipsize(Pango.EllipsizeMode.END)
			self.layout.set_width(max_x * 1000)
			if wrap:
				self.layout.set_height(20000 * 1000)
			else:
				self.layout.set_height(0)

			try:
				self.layout.set_text(text, -1)
			except Exception:
				logging.exception(f"Exception in get_text_wh for: {text}")
				self.layout.set_text(text.encode("utf-8", "replace").decode("utf-8"), -1)

			return self.layout.get_pixel_size()
		#return self.__win_text_xy(text, font)
		return self.__win_text_xy(text, font, max_x, wrap)

	def get_y_offset(self, text: str, font: int, max_x: int, wrap: bool = False) -> int:
		"""HACKY"""
		self.layout.set_font_description(Pango.FontDescription(self.f_dict[font][0]))
		self.layout.set_ellipsize(Pango.EllipsizeMode.END)
		self.layout.set_width(max_x * 1000)
		if wrap:
			self.layout.set_height(20000 * 1000)
		else:
			self.layout.set_height(0)

		try:
			self.layout.set_text(text, -1)
		except Exception:
			logging.exception(f"Exception in get_y_offset for: {text}")
			self.layout.set_text(text.encode("utf-8", "replace").decode("utf-8"), -1)

		y_off = self.layout.get_baseline() / 1000
		y_off = round(round(y_off) - 13 * self.scale)  # 13 for compat with way text position used to work

		return y_off

	def __render_text(self, key: dict, x: int, y: int, range_top: int, range_height: int, align: int) -> None:

		sd = key

		if sd[3]:
			self.was_truncated = True

		if align == 1:
			sd[0].x = round(x) - sd[0].w

		elif align == 2:
			sd[0].x -= int(sd[0].w / 2)

		if range_height is not None and range_height < sd[0].h:

			if range_top < 0:
				range_top = 0

			if range_top > sd[0].h - range_height:
				range_top = sd[0].h - range_height

			self.source_rect.y = round(range_top)
			self.source_rect.w = sd[0].w
			self.source_rect.h = round(range_height)

			self.dest_rect.x = sd[0].x
			self.dest_rect.y = sd[0].y
			self.dest_rect.w = sd[0].w
			self.dest_rect.h = round(range_height)

			#sdl3.SDL_RenderCopyEx(self.renderer, sd[1], self.source_rect, self.dest_rect, 0, None, 0)
			sdl3.SDL_RenderTexture(self.renderer, sd[1], self.source_rect, self.dest_rect)
			return

		sdl3.SDL_RenderTexture(self.renderer, sd[1], None, sd[0])


	def __draw_text_cairo(
		self,
		location: list[int], text: str, colour: list[int], font: int, max_x: int, bg: tuple[int, int, int, int],
		align: int = 0, max_y: int | None = None, wrap: bool = False, range_top: int = 0,
		range_height: int | None = None, real_bg: bool = False, key: tuple[int, str, str, int, int, int, int, int, int, int] | None = None,
		) -> int:

		#perf.set()
		force_cache = False
		if key:
			force_cache = True

		self.was_truncated = False

		max_x += 12  # Hack
		max_x = round(max_x)

		alpha_bg = self.alpha_bg
		force_gray = self.force_gray
		#real_bg = True

		if bg[3] < 200:
			alpha_bg = True
			force_gray = True

		x = round(location[0])
		y = round(location[1])

		if self.pretty_rect:

			w, h = self.get_text_wh(text, font, max_x, wrap)
			quick_box = [x, y, w, h]

			if align == 1:
				quick_box[0] = x - quick_box[2]

			elif align == 2:
				quick_box[0] -= int(quick_box[2] / 2)

			if coll_rect(self.pretty_rect, quick_box):
				# self.rect_r(quick_box, [0, 0, 0, 100], True)
				# if self.real_bg:
				#	 real_bg = True
				alpha_bg = True
			else:
				alpha_bg = False


		if alpha_bg:
			bg = (0, 0, 0, 0)

		if max_y is not None:
			max_y = round(max_y)

		if len(text) == 0:
			return 0

		if key is None:
			key = (max_x, text, font, colour[0], colour[1], colour[2], colour[3], bg[0], bg[1], bg[2])

		if not real_bg or force_cache:
			sd = self.ttc.get(key)
			if sd:

				sd = self.ttc[key]
				sd[0].x = round(x)
				sd[0].y = round(y) - sd[2]

				self.__render_text(sd, x, y, range_top, range_height, align)
				self.ttl.remove(key)
				self.ttl.append(key)

				if wrap:
					return sd[0].h
				return sd[0].w

		if not self.pretty_rect:  # Would have already done this if True

			w, h = self.get_text_wh(text, font, max_x, wrap)

		if w < 1:
			return 0

		h += 4  # Compensate for characters that drop past the baseline, Pango doesn't seem to allow for this

		if wrap:
			w = max_x + 1

		data = ctypes.c_buffer(b"\x00" * (h * (w * 4)))
		ptr = pointer(data)

		if real_bg:
			box = sdl3.SDL_Rect(x, y - self.get_y_offset(text, font, max_x, wrap), w, h)

			if align == 1:
				box.x = x - box.w

			elif align == 2:
				box.x -= int(box.w / 2)

			ssurf = sdl3.SDL_RenderReadPixels(self.renderer, box) #, sdl3.SDL_PIXELFORMAT_XRGB8888, ctypes.pointer(data), (w * 4))
			ptr = ssurf.contents.pixels
			size = w * h * 4
			data_array = (ctypes.c_ubyte * size).from_address(ptr)
			data = memoryview(data_array)

		if alpha_bg:
			surf = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, w, h)
		else:
			surf = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_RGB24, w, h)

		context = cairo.Context(surf)

		if force_gray:
			options = context.get_font_options()
			options.set_antialias(cairo.ANTIALIAS_GRAY)
			#options.set_hint_style(cairo.HINT_STYLE_NONE)
			context.set_font_options(options)
		elif self.force_subpixel_text:
			options = context.get_font_options()
			#options.set_antialias(cairo.ANTIALIAS_NONE)
			#options.set_antialias(cairo.ANTIALIAS_GRAY)
			options.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
			context.set_font_options(options)

		layout = PangoCairo.create_layout(context)
		layout.set_auto_dir(False)

		if max_y is not None:
			layout.set_ellipsize(Pango.EllipsizeMode.END)
			layout.set_width(max_x * 1000)
			layout.set_height(max_y * 1000)
		else:
			layout.set_ellipsize(Pango.EllipsizeMode.END)
			layout.set_width(max_x * 1000)

			extra = 0
			if wrap:  # Compensate for height measurement being 1-2 lines too short. Pango bug?
				extra = round(400000 * self.scale)

			layout.set_height(h * 1000 + extra)

		if not wrap and max_y is None:
			layout.set_height(-1)

		# Attributes don't seem to be implemented in gi?
		# attrs = Pango.AttrList()
		# attrs.insert(Pango.Attribute(Pango.Underline.SINGLE))
		# layout.set_attributes(attrs)

		context.rectangle(0, 0, w, h)

		if not real_bg and not alpha_bg:
			context.set_source_rgb(bg[0] / 255, bg[1] / 255, bg[2] / 255)
			# context.set_source_rgba(0, 0, 0, 0)
			context.fill()

		context.set_source_rgb(colour[0] / 255, colour[1] / 255, colour[2] / 255)

		if font not in self.f_dict:
			logging.info("Font not loaded: " + str(font))
			return 10

		# desc = Pango.FontDescription(self.f_dict[font][0])
		# desc.set_family("Arial")

		layout.set_font_description(Pango.FontDescription(self.f_dict[font][0]))

		try:
			layout.set_text(text, -1)
		except Exception:
			logging.exception(f"Text error on text: {text}")
			layout.set_text(text.encode("utf-8", "replace").decode("utf-8"), -1)

		#logging.info(layout.get_direction(0))

		y_off = layout.get_baseline() / 1000
		y_off = round(round(y_off) - 13 * self.scale)  # 13 for compat with way text position used to work

		PangoCairo.show_layout(context, layout)

		self.was_truncated = layout.is_ellipsized()

		if alpha_bg:
			#sdl3.SDL_surface = sdl3.SDL_CreateRGBSurfaceWithFormatFrom(ctypes.pointer(data), w, h, 32, w * 4, sdl3.SDL_PIXELFORMAT_ARGB8888)
			format = sdl3.SDL_PIXELFORMAT_ARGB8888
			surface = sdl3.SDL_CreateSurfaceFrom(w, h, format, ptr, w * 4)
		else:
			format = sdl3.SDL_PIXELFORMAT_XRGB8888
			surface = sdl3.SDL_CreateSurfaceFrom(w, h, format, ptr, w * 4)

		# Here the background colour is keyed out allowing lines to overlap slightly
		if not real_bg and not alpha_bg:
			format_details = sdl3.SDL_GetPixelFormatDetails(format)
			ke = sdl3.SDL_MapRGB(format_details, None, bg[0], bg[1], bg[2])
			sdl3.SDL_SetSurfaceColorKey(surface, True, ke)

		c = sdl3.SDL_CreateTextureFromSurface(self.renderer, surface)
		sdl3.SDL_DestroySurface(surface)

		if alpha_bg:
			blend_mode = sdl3.SDL_ComposeCustomBlendMode(sdl3.SDL_BLENDFACTOR_ONE, sdl3.SDL_BLENDFACTOR_ONE_MINUS_SRC_ALPHA, sdl3.SDL_BLENDOPERATION_ADD, sdl3.SDL_BLENDFACTOR_ONE, sdl3.SDL_BLENDFACTOR_ONE_MINUS_SRC_ALPHA, sdl3.SDL_BLENDOPERATION_ADD)
			sdl3.SDL_SetTextureBlendMode(c, blend_mode)

		dst = sdl3.SDL_FRect(round(x), round(y))
		dst.w = round(w)
		dst.h = round(h)
		dst.y = round(y) - y_off

		pack = [dst, c, y_off, self.was_truncated]

		self.__render_text(pack, x, y, range_top, range_height, align)

		# Don't cache if using real background data
		if not real_bg or force_cache:
			self.ttc[key] = pack
			self.ttl.append(key)
			if len(self.ttl) > 350:
				key = self.ttl[0]
				so = self.ttc[key]
				sdl3.SDL_DestroyTexture(so[1])
				del self.ttc[key]
				del self.ttl[0]
		if wrap:
			return dst.h
		return dst.w


	# WINDOWS --------------------------------------------------------

	def __win_text_xy(self, text: str, font: int | None, max_x: int, wrap: bool) -> tuple[int, int] | None:

		if font is None or font not in self.f_dict:

			logging.info("Missing Font")
			logging.info(font)

			return None

		return self.f_dict[font].get_metrics(text, max_x, wrap)

	def __win_render_text(self, key: dict, x: int, y: int, range_top: int, range_height: int, align: int) -> None:


		sd = key

		sd[0].x = round(x)
		sd[0].y = round(y)
		if align == 1:
			sd[0].x = round(x) - sd[0].w
		elif align == 2:
			sd[0].x -= int(sd[0].w / 2)

		if range_height is not None and range_height < sd[0].h - 20:

			if range_top + range_height > sd[0].h:
				# range_top = 0
				range_height = sd[0].h - range_top

			self.source_rect.y = sd[0].h - round(range_height) - round(range_top)
			self.source_rect.w = sd[0].w
			self.source_rect.h = round(range_height)

			self.dest_rect.x = sd[0].x
			self.dest_rect.y = sd[0].y
			self.dest_rect.w = sd[0].w
			self.dest_rect.h = round(range_height)

			sdl3.SDL_RenderCopyEx(self.renderer, sd[1], self.source_rect, self.dest_rect, 0, None, sdl3.SDL_FLIP_VERTICAL)
			return

		sdl3.SDL_RenderCopyEx(self.renderer, sd[1], None, sd[0], 0, None, sdl3.SDL_FLIP_VERTICAL)

	def __draw_text_windows(
		self, x: int, y: int, text: str, bg: list[int], fg: list[int], font: Win32Font | None = None,
		align: int = 0, wrap: bool = False, max_x: int = 100, max_y: int | None = None,
		range_top: int = 0, range_height: int | None = None,
	) -> int:

		y += self.y_offset_dict[font]

		key = (text, font, fg[0], fg[1], fg[2], fg[3], bg[0], bg[1], bg[2], max_x)

		if key in self.cache:
			sd = self.cache[key]

			self.__win_render_text(sd, x, y, range_top, range_height, align)
			if wrap:
				return sd[0].h
			return sd[0].w

		if font is None or font not in self.f_dict:

			logging.info("Missing Font")
			logging.info(font)
			return 0

		#perf_timer.set()

		f = self.f_dict[font]

		w, h = f.get_metrics(text, max_x, wrap)
		if max_y and max_y > h:
			max_y = h

		im, c_bits = f.renderText(text, bg, fg, wrap, max_x, max_y)

		s_image = im
		ke = sdl3.SDL_MapRGB(s_image.contents.format, bg[0], bg[1], bg[2])
		sdl3.SDL_SetColorKey(s_image, True, ke)
		c = sdl3.SDL_CreateTextureFromSurface(self.renderer, s_image)
		tex_w = pointer(c_int(0))
		tex_h = pointer(c_int(0))
		sdl3.SDL_QueryTexture(c, None, None, tex_w, tex_h)
		dst = sdl3.SDL_FRect(round(x), round(y))
		dst.w = int(tex_w.contents.value)
		dst.h = int(tex_h.contents.value)

		sdl3.SDL_DestroySurface(s_image)
		#im.close()

		if align == 1:
			dst.x = round(x) - dst.w

		elif align == 2:
			dst.x -= int(dst.w / 2)

		#sdl3.SDL_RenderCopy(renderer, c, None, dst)
		#sdl3.SDL_RenderCopyEx(self.renderer, c, None, dst, 0, None, sdl3.SDL_FLIP_VERTICAL)

		#logging.info(perf_timer.get())
		self.cache[key] = [dst, c]
		self.__win_render_text([dst, c], x, y, range_top, range_height, align)

		self.ca_li.append(key)

		if len(self.ca_li) > 350:
			sdl3.SDL_DestroyTexture(self.cache[self.ca_li[0]][1])
			del self.cache[self.ca_li[0]]
			del self.ca_li[0]

		return dst.w

	def text(
		self, location: list[int], text: str, colour: list[int], font: int | Win32Font, max_w: int = 4000, bg: list[int] | None = None,
		range_top: int = 0, range_height: int | None = None, real_bg: bool = False, key: tuple[int, str, str, int, int, int, int, int, int, int] | None = None) -> int | None:

		#logging.info((text, font))

		if not text:
			return 0

		max_w = max(1, max_w)

		if bg is None:
			bg = self.text_background_colour

		if colour[3] != 255:
			colour = alpha_blend(colour, bg)
		align = 0
		if len(location) > 2:
			if location[2] == 1:
				align = 1
			if location[2] == 2:
				align = 2
			if location[2] == 4:
				max_h = None
				if len(location) > 4:
					max_h = location[4]

				if system == "Linux":
					return self.__draw_text_cairo(
						location, text, colour, font, location[3], bg, max_y=max_h, wrap=True,
						range_top=range_top, range_height=range_height,
					)
				return self.__draw_text_windows(
					location[0], location[1], text, bg, colour, font, 0, True, location[3], max_y=max_h,
					range_top=range_top, range_height=range_height,
				)

		if system == "Linux":
			return self.__draw_text_cairo(location, text, colour, font, max_w, bg, align, real_bg=real_bg, key=key)
		return self.__draw_text_windows(location[0], location[1], text, bg, colour, font, align=align, max_x=max_w)
