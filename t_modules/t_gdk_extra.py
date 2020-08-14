# Tauon Music Box - System cursor loader

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


import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
from sdl2 import *
import ctypes


def cursor_get_gdk(type):

    if type == 4:
        cursor = Gdk.Cursor(Gdk.CursorType.BOTTOM_RIGHT_CORNER)
    elif type == 8:
        cursor = Gdk.Cursor(Gdk.CursorType.RIGHT_SIDE)
    elif type == 9:
        cursor = Gdk.Cursor(Gdk.CursorType.TOP_SIDE)
    elif type == 10:
        cursor = Gdk.Cursor(Gdk.CursorType.LEFT_SIDE)
    elif type == 11:
        cursor = Gdk.Cursor(Gdk.CursorType.BOTTOM_SIDE)

    else:
        return None

    return Gdk.Cursor.get_surface(cursor)


def cairo_cursor_to_sdl(cairo_surface, x_hot, y_hot, fallback=None):

    if not cairo_surface:
        return fallback

    w = cairo_surface.get_width()
    h = cairo_surface.get_height()

    mem = cairo_surface.get_data()
    buff = ctypes.c_buffer(mem.tobytes())

    sdl_surface = SDL_CreateRGBSurfaceWithFormatFrom(ctypes.pointer(buff), w, h, 32, w * 4, SDL_PIXELFORMAT_ARGB8888)
    return SDL_CreateColorCursor(sdl_surface, round(x_hot), round(y_hot))

