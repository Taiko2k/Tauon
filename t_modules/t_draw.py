
# Tauon Music Box - Basic Drawing and Text Drawing Functions Module

# Copyright © 2015-2018, Taiko2k captain(dot)gxj(at)gmail.com

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


from sdl2 import *
from t_modules.t_extra import *
import ctypes
import cairo
import gi
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango
from gi.repository import PangoCairo


# Performs alpha blending of one colour (RGB-A) onto another (RGB)
def alpha_blend(colour, base):
    alpha = colour[3] / 255
    return [int(alpha * colour[0] + (1 - alpha) * base[0]),
            int(alpha * colour[1] + (1 - alpha) * base[1]),
            int(alpha * colour[2] + (1 - alpha) * base[2]), 255]


perf = Timer()

class TDraw:

    def __init__(self, renderer=None):

        # All
        self.renderer = renderer
        self.scale = 1

        # Drawing
        self.sdl_rect = SDL_Rect(10, 10, 10, 10)

        # Text and Fonts
        self.source_rect = SDL_Rect(0, 0, 0, 0)
        self.dest_rect = SDL_Rect(0, 0, 0, 0)
        self.surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0)
        self.context = cairo.Context(self.surf)
        self.layout = PangoCairo.create_layout(self.context)
        # self.layout_context = self.layout.get_context()
        # fo = cairo.FontOptions()
        # fo.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
        # PangoCairo.context_set_font_options(self.layout_context, fo)

        self.text_background_colour = [0, 0, 0, 255]
        #self.pretty_rect = [0, 0, 0, 0]
        self.pretty_rect = None
        self.f_dict = {}
        self.ttc = {}
        self.ttl = []

    def rect_a(self, location_xy, size_wh, colour, fill=False):

        self.sdl_rect.x = round(location_xy[0])
        self.sdl_rect.y = round(location_xy[1])
        self.sdl_rect.w = round(size_wh[0])
        self.sdl_rect.h = round(size_wh[1])

        if fill is True:
            SDL_SetRenderDrawColor(self.renderer, colour[0], colour[1], colour[2], colour[3])
            SDL_RenderFillRect(self.renderer, self.sdl_rect)
        else:
            SDL_SetRenderDrawColor(self.renderer, colour[0], colour[1], colour[2], colour[3])
            SDL_RenderDrawRect(self.renderer, self.sdl_rect)

    def rect_r(self, rectangle, colour, fill=False):

        self.sdl_rect.x = round(rectangle[0])
        self.sdl_rect.y = round(rectangle[1])
        self.sdl_rect.w = round(rectangle[2])
        self.sdl_rect.h = round(rectangle[3])

        SDL_SetRenderDrawColor(self.renderer, colour[0], colour[1], colour[2], colour[3])

        if fill:
            SDL_RenderFillRect(self.renderer, self.sdl_rect)
        else:
            SDL_RenderDrawRect(self.renderer, self.sdl_rect)

    def line(self, x1, y1, x2, y2, colour):

        SDL_SetRenderDrawColor(self.renderer, colour[0], colour[1], colour[2], colour[3])
        SDL_RenderDrawLine(self.renderer, round(x1), round(y1), round(x2), round(y2))

    def get_text_w(self, text, font, height=False):

        x, y = self.get_text_wh(text, font, 3000)
        if height:
            return y
        else:
            return x

    def clear_text_cache(self):

        for key in self.ttl:
            so = self.ttc[key]
            SDL_DestroyTexture(so[1])

        self.ttc.clear()
        self.ttl.clear()

    def prime_font(self, name, size, user_handle, offset=0):

        self.f_dict[user_handle] = (name + " " + str(size * self.scale), offset, size)

    def get_text_wh(self, text, font, max_x, wrap=False):

        self.layout.set_font_description(Pango.FontDescription(self.f_dict[font][0]))
        self.layout.set_ellipsize(Pango.EllipsizeMode.END)
        self.layout.set_width(max_x * 1000)
        if wrap:
            self.layout.set_height(20000 * 1000)
        else:
            self.layout.set_height(0)
        self.layout.set_text(text, -1)

        return self.layout.get_pixel_size()

    def get_y_offset(self, text, font, max_x, wrap=False):  # HACKY

        self.layout.set_font_description(Pango.FontDescription(self.f_dict[font][0]))
        self.layout.set_ellipsize(Pango.EllipsizeMode.END)
        self.layout.set_width(max_x * 1000)
        if wrap:
            self.layout.set_height(20000 * 1000)
        else:
            self.layout.set_height(0)
        self.layout.set_text(text, -1)


        y_off = self.layout.get_baseline() / 1000
        y_off = round(round(y_off) - 13 * self.scale)  # 13 for compat with way text position used to work
        if self.scale == 2:
            y_off -= 2

        return y_off

    def __render_text(self, key, x, y, range_top, range_height, align):

        sd = key
        if align == 1:
            sd[0].x = x - sd[0].w

        elif align == 2:
            sd[0].x = sd[0].x - int(sd[0].w / 2)

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

            SDL_RenderCopyEx(self.renderer, sd[1], self.source_rect, self.dest_rect, 0, None, 0)
            return

        SDL_RenderCopy(self.renderer, sd[1], None, sd[0])

    def __draw_text_cairo(self, location, text, colour, font, max_x, bg, align=0, max_y=None, wrap=False, range_top=0, range_height=None):

        # perf.set()
        # print("START")

        max_x += 12  # Hack
        max_x = round(max_x)

        real_bg = False

        x = round(location[0])
        y = round(location[1])

        if self.pretty_rect:
            w, h = self.get_text_wh(text, font, max_x, wrap)

            quick_box = [x, y, w, h]

            if align == 1:
                quick_box[0] = x - quick_box[2]

            elif align == 2:
                quick_box[0] = quick_box[0] - int(quick_box[2] / 2)

            if coll_rect(self.pretty_rect, quick_box):
                # self.rect_r(quick_box, [0, 0, 0, 100], True)
                # print("PT")
                # print(text)
                real_bg = True

        if max_y is not None:
            max_y = round(max_y)

        if len(text) == 0:
            return 0


        key = (max_x, text, font, colour[0], colour[1], colour[2], colour[3], bg[0], bg[1], bg[2])

        if not real_bg:
            if key in self.ttc:
                sd = self.ttc[key]
                sd[0].x = x
                sd[0].y = y - sd[2]
                self.__render_text(sd, x, y, range_top, range_height, align)

                # print("CAHE")
                # print(perf.hit())

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

        if real_bg:
            box = SDL_Rect(x, y - self.get_y_offset(text, font, max_x, wrap), w, h)

            if align == 1:
                box.x = x - box.w

            elif align == 2:
                box.x = box.x - int(box.w / 2)

            SDL_RenderReadPixels(self.renderer, box, SDL_PIXELFORMAT_RGB888, ctypes.pointer(data), (w * 4))

            # print("READ")
            # print(perf.hit())

        surf = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_RGB24, w, h)

        context = cairo.Context(surf)
        layout = PangoCairo.create_layout(context)

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

        # Attributes don't seem to be implemented in gi?
        # attrs = Pango.AttrList()
        # attrs.insert(Pango.Attribute(Pango.Underline.SINGLE))
        # layout.set_attributes(attrs)

        context.rectangle(0, 0, w, h)

        if not real_bg:
            context.set_source_rgb(bg[0] / 255, bg[1] / 255, bg[2] / 255)
            #context.set_source_rgba(0, 0, 0, 0)
            context.fill()
        context.set_source_rgb(colour[0] / 255, colour[1] / 255, colour[2] / 255)

        if font not in self.f_dict:
            print("Font not loaded: " + str(font))
            return 10

        layout.set_font_description(Pango.FontDescription(self.f_dict[font][0]))

        # This seems broken, it always uses the system fonconfig and override here does not work?
        # options = context.get_font_options()
        # options.set_antialias(cairo.ANTIALIAS_GRAY)
        # context.set_font_options(options)

        # options = context.get_font_options()
        # print(options.get_antialias())

        layout.set_text(text, -1)

        y_off = layout.get_baseline() / 1000
        y_off = round(round(y_off) - 13 * self.scale)  # 13 for compat with way text position used to work
        if self.scale == 2:
            y_off -= 2

        PangoCairo.show_layout(context, layout)

        # print("TEXT")
        # print(perf.hit())

        sdl_surface = SDL_CreateRGBSurfaceWithFormatFrom(ctypes.pointer(data), w, h, 24, w*4, SDL_PIXELFORMAT_RGB888)
        #sdl_surface = SDL_CreateRGBSurfaceWithFormatFrom(ctypes.pointer(data), w, h, 32, w*4, SDL_PIXELFORMAT_ARGB8888)

        # Here the background colour is keyed out allowing lines to overlap slightly
        if not real_bg:
            ke = SDL_MapRGB(sdl_surface.contents.format, bg[0], bg[1], bg[2])
            SDL_SetColorKey(sdl_surface, True, ke)



        c = SDL_CreateTextureFromSurface(self.renderer, sdl_surface)
        SDL_FreeSurface(sdl_surface)

        dst = SDL_Rect(x, y)
        dst.w = w
        dst.h = h
        dst.y = y - y_off

        pack = [dst, c, y_off]

        # print("RENDER")
        # print(perf.hit())

        self.__render_text(pack, x, y, range_top, range_height, align)

        # print("DONE")
        # print(perf.hit())

        # Don't cache if using real background data
        if not real_bg:
            self.ttc[key] = pack
            self.ttl.append(key)
            if len(self.ttl) > 350:
                key = self.ttl[0]
                so = self.ttc[key]
                SDL_DestroyTexture(so[1])
                del self.ttc[key]
                del self.ttl[0]
        if wrap:
            return dst.h
        return dst.w

    def draw_text(self, location, text, colour, font, max_w=4000, bg=None, range_top=0, range_height=None):

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
                return self.__draw_text_cairo(location, text, colour, font, location[3], bg, max_y=max_h, wrap=True,
                                              range_top=range_top, range_height=range_height)

        return self.__draw_text_cairo(location, text, colour, font, max_w, bg, align)

