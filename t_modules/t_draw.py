
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

import sys
from sdl2 import *
from t_modules.t_extra import *
import ctypes

system = "linux"
if sys.platform == 'win32':
    system = "windows"

if system == "linux":
    import cairo
    import gi
    gi.require_version('Pango', '1.0')
    gi.require_version('PangoCairo', '1.0')
    from gi.repository import Pango
    from gi.repository import PangoCairo
else:
    from ctypes import windll, CFUNCTYPE, POINTER, c_int, c_void_p, byref, pointer
    import win32con, win32api, win32gui, win32ui
    import struct
    
if system == "windows":

    class RECT(ctypes.Structure):
        _fields_ = [('left', ctypes.c_long),
                    ('top', ctypes.c_long),
                    ('right', ctypes.c_long),
                    ('bottom', ctypes.c_long)
                    ]

    def RGB(r, g, b):
        return r | (g << 8) | (b << 16)

    def Wcolour(colour):
        return colour[0] | (colour[1] << 8) | (colour[2] << 16)

    def native_bmp_to_sdl(hdc, bitmap_handle, width, height):

        bmpheader = struct.pack("LHHHH", struct.calcsize("LHHHH"),
                                width, height, 1, 24) #w,h, planes=1, bitcount)

        c_bmpheader = ctypes.c_buffer(bmpheader)

        #3 bytes per pixel, pad lines to 4 bytes
        c_bits = ctypes.c_buffer(b" " * (height * ((width*3 + 3) & -4)))

        res = ctypes.windll.gdi32.GetDIBits(
            hdc, bitmap_handle, 0, height,
            c_bits, c_bmpheader,
            win32con.DIB_RGB_COLORS)

        if not res:
            raise IOError("native_bmp_to_pil failed: GetDIBits")

        # We need to keep c_bits pass else it may be garbage collected
        return SDL_CreateRGBSurfaceWithFormatFrom(ctypes.pointer(c_bits), width, height, 24, (width*3 + 3) & -4 , SDL_PIXELFORMAT_BGR24), c_bits


    class Win32Font:

        def __init__(self, name, height, weight=win32con.FW_NORMAL,
                     italic=False, underline=False):
                     
            self.font = win32ui.CreateFont({
                'name': name, 'height': height,
                'weight': weight, 'italic': italic, 'underline': underline,}) #'charset': win32con.MAC_CHARSET})

            #create a compatible DC we can use to draw:

            self.desktopHwnd = win32gui.GetDesktopWindow()
            self.desktopDC = win32gui.GetWindowDC(self.desktopHwnd)
            self.mfcDC = win32ui.CreateDCFromHandle(self.desktopDC)
            self.drawDC = self.mfcDC.CreateCompatibleDC()

            #initialize it

            self.drawDC.SelectObject(self.font)

        def get_metrics(self, text, max_x, wrap):

            #return self.drawDC.GetTextExtent(text)
            
            rect = RECT(0,0,0,0)
            rect.left = 0
            rect.right = max_x
            rect.top = 0
            rect.bottom = 0

                #windll.User32.DrawTextW(t, text, len(text)) #, rect, win32con.DT_WORDBREAK)
            t = self.drawDC.GetSafeHdc()
            
            if wrap:
                windll.User32.DrawTextW(t, text, len(text), pointer(rect), win32con.DT_WORDBREAK | win32con.DT_CALCRECT)
            else:
                windll.User32.DrawTextW(t, text, len(text), pointer(rect), win32con.DT_CALCRECT | win32con.DT_END_ELLIPSIS)
                
            return rect.right, rect.bottom
            
          

        def renderText(self, text, bg, fg, wrap=False, max_x=100, max_y=None):

            self.drawDC.SetTextColor(Wcolour(fg))

            t = self.drawDC.GetSafeHdc()

            win32gui.SetBkMode(t, win32con.TRANSPARENT)


            #create the compatible bitmap:

            #w,h = self.drawDC.GetTextExtent(text)
            w, h = self.get_metrics(text, max_x, wrap)

            #print(self.drawDC.GetTextFace())

            #w += 1
            #if wrap:
            #    h = int((w / max_x) * h) + h
            #    w = max_x + 1
            if max_y != None:
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
                rect.right = max_x
                rect.top = 0
                rect.bottom = h

                #windll.User32.DrawTextW(t, text, len(text)) #, rect, win32con.DT_WORDBREAK)
                windll.User32.DrawTextW(t, text, len(text), pointer(rect), win32con.DT_WORDBREAK)
            else:
                
                rect = RECT(0,0,0,0)
                rect.left = 0
                rect.right = max_x
                rect.top = 0
                rect.bottom = h

                #windll.User32.DrawTextW(t, text, len(text)) #, rect, win32con.DT_WORDBREAK)
                windll.User32.DrawTextW(t, text, len(text), pointer(rect), win32con.DT_END_ELLIPSIS)                
                
                
                #windll.gdi32.TextOutW(t, 0, 0, text, len(text))

            # print(rects)
            #print(text)
            #windll.gdi32.ExtTextOutW(t, 0, 0, None, rect, text, len(text), None)
            #convert to SDL surface
            im, c_bits = native_bmp_to_sdl(self.drawDC.GetSafeHdc(), saveBitMap.GetHandle(), w, h)
            #clean-up
            win32gui.DeleteObject(saveBitMap.GetHandle())

            return im, c_bits


        def __del__(self):

            self.mfcDC.DeleteDC()
            self.drawDC.DeleteDC()
            win32gui.ReleaseDC(self.desktopHwnd, self.desktopDC)
            win32gui.DeleteObject(self.font.GetSafeHandle())

        def __del__(self):

            win32gui.DeleteObject(self.font.GetSafeHandle())



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
        
        if system == "linux":
            self.surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 0, 0)
            self.context = cairo.Context(self.surf)
            self.layout = PangoCairo.create_layout(self.context)
       
            
        else:
            self.cache = {}
            self.ca_li = []
            self.y_offset_dict = {}

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

    def win_prime_font(self, name, size, user_handle, weight, y_offset=0):
    
        self.f_dict[user_handle] = Win32Font(name, size, weight)
        self.y_offset_dict[user_handle] = y_offset

    def prime_font(self, name, size, user_handle, offset=0):

        self.f_dict[user_handle] = (name + " " + str(size * self.scale), offset, size)

    def get_text_wh(self, text, font, max_x, wrap=False):

        if system == "linux":
            self.layout.set_font_description(Pango.FontDescription(self.f_dict[font][0]))
            self.layout.set_ellipsize(Pango.EllipsizeMode.END)
            self.layout.set_width(max_x * 1000)
            if wrap:
                self.layout.set_height(20000 * 1000)
            else:
                self.layout.set_height(0)
            self.layout.set_text(text, -1)

            return self.layout.get_pixel_size()
        else:
            #return self.__win_text_xy(text, font)
            return self.__win_text_xy(text, font, max_x, wrap)

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

        # desc = Pango.FontDescription(self.f_dict[font][0])
        # desc.set_family("Arial")

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

        self.__render_text(pack, x, y, range_top, range_height, align)

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


    # WINDOWS --------------------------------------------------------

    def __win_text_xy(self, text, font, max_x, wrap):

        if font == None or font not in self.f_dict:

            print("Missing Font")
            print(font)

            return

        return self.f_dict[font].get_metrics(text, max_x, wrap)

    def __win_render_text(self, key, x, y, range_top, range_height, align):
   

        sd = key
        
        sd[0].x = x
        sd[0].y = y
        if align == 1:
            sd[0].x = x - sd[0].w
        elif align == 2:
            sd[0].x = sd[0].x - int(sd[0].w / 2)

        if range_height is not None and range_height < sd[0].h - 20:
        

            self.source_rect.y = sd[0].h - round(range_height) - round(range_top)
            self.source_rect.w = sd[0].w
            self.source_rect.h = round(range_height)

            self.dest_rect.x = sd[0].x
            self.dest_rect.y = sd[0].y
            self.dest_rect.w = sd[0].w
            self.dest_rect.h = round(range_height)
            
            SDL_RenderCopyEx(self.renderer, sd[1], self.source_rect, self.dest_rect, 0, None, SDL_FLIP_VERTICAL)
            return

        SDL_RenderCopyEx(self.renderer, sd[1], None, sd[0], 0, None, SDL_FLIP_VERTICAL)


    def __draw_text_windows(self, x, y, text, bg, fg, font=None, align=0, wrap=False, max_x=100, max_y=None, range_top=0, range_height=None):

        y += self.y_offset_dict[font]
        #y += self.y_offset_dict[font]
        key = (text, font, fg[0], fg[1], fg[2], fg[3], bg[1], bg[2], bg[3], max_x)

        if key in self.cache:
            sd = self.cache[key]


            self.__win_render_text(sd, x, y, range_top, range_height, align)
            if wrap:
                return sd[0].h
            return sd[0].w


            #sd[0].x = x
            #sd[0].y = y
            #if align == 1:
            #    sd[0].x = x - sd[0].w
            #elif align == 2:
            #    sd[0].x = sd[0].x - int(sd[0].w / 2)
            #SDL_RenderCopyEx(self.renderer, sd[1], None, sd[0], 0, None, SDL_FLIP_VERTICAL)
            #return sd[0].w


        if font == None or font not in self.f_dict:

            print("Missing Font")
            print(font)
            return 0

        #perf_timer.set()

        f = self.f_dict[font]
        
        w, h = f.get_metrics(text, max_x, wrap)
        if max_y and max_y > h:
            max_y = h

        im, c_bits = f.renderText(text, bg, fg, wrap, max_x, max_y)

        #buff = io.BytesIO()

        #im.save(buff, format="BMP")

        #buff.seek(0)

        #wop = rw_from_object(buff)

        #s_image = IMG_Load_RW(wop, 0)

        s_image = im

        ke = SDL_MapRGB(s_image.contents.format, bg[0], bg[1], bg[2])

        SDL_SetColorKey(s_image, True, ke)

        c = SDL_CreateTextureFromSurface(self.renderer, s_image)

        tex_w = pointer(c_int(0))

        tex_h = pointer(c_int(0))

        SDL_QueryTexture(c, None, None, tex_w, tex_h)

        dst = SDL_Rect(x, y)

        dst.w = int(tex_w.contents.value)

        dst.h = int(tex_h.contents.value)

        SDL_FreeSurface(s_image)

        #im.close()

        if align == 1:
            dst.x = x - dst.w

        elif align == 2:
            dst.x = dst.x - int(dst.w / 2)

        #SDL_RenderCopy(renderer, c, None, dst)

        #SDL_RenderCopyEx(self.renderer, c, None, dst, 0, None, SDL_FLIP_VERTICAL)


        #print(perf_timer.get())
        self.cache[key] = [dst, c]

        self.__win_render_text([dst, c], x, y, range_top, range_height, align)


        self.ca_li.append(key)

        if len(self.ca_li) > 350:
            SDL_DestroyTexture(self.cache[self.ca_li[0]][1])
            del self.cache[self.ca_li[0]]
            del self.ca_li[0]

        return dst.w    
    
    
    
    def draw_text(self, location, text, colour, font, max_w=4000, bg=None, range_top=0, range_height=None):

        #print((text, font))

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
                    
                if system == "linux":
                    return self.__draw_text_cairo(location, text, colour, font, location[3], bg, max_y=max_h, wrap=True,
                                                  range_top=range_top, range_height=range_height)
                else:
                    return self.__draw_text_windows(location[0], location[1], text, bg, colour, font, 0, True, location[3], max_y=max_h,
                                                     range_top=range_top, range_height=range_height)

        if system == "linux":
            return self.__draw_text_cairo(location, text, colour, font, max_w, bg, align)
        else:
            return self.__draw_text_windows(location[0], location[1], text, bg, colour, font, align=align, max_x=max_w)
