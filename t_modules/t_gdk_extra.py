import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
from sdl2 import *
import ctypes

def cursor_gen(type):

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

def cairo_cursor_to_sdl(cairo_surface, x_hot, y_hot):

    #cairo_surface, x_hot, y_hot = Gdk.Cursor.get_surface(cursor)

    w = cairo_surface.get_width()
    h = cairo_surface.get_height()

    mem = cairo_surface.get_data()
    buff = ctypes.c_buffer(mem.tobytes())

    #return buff, round(x_hot), round(y_hot)

    sdl_surface = SDL_CreateRGBSurfaceWithFormatFrom(ctypes.pointer(buff), w, h, 24, w * 4, SDL_PIXELFORMAT_ARGB8888)
    return SDL_CreateColorCursor(sdl_surface, round(x_hot), round(y_hot))


