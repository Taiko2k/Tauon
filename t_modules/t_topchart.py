
import cairo
from gi.repository import Pango
from gi.repository import PangoCairo
import gi
import os
import random

class TopChart:

    def __init__(self, tauon, album_art_gen):

        self.pctl = tauon.pctl
        self.cache_dir = tauon.cache_directory
        self.user_dir = tauon.user_directory

        self.album_art_gen = album_art_gen

    def generate(self, tracks, bg=(10,10,10), rows=3, columns=3, show_lables=True):

        bg = (bg[0] / 255, bg[1] / 255, bg[2] / 255)

        border = 29
        text_offset = -12
        size = 170
        spacing = 8

        h = round((border * 2) + (size * rows) + (spacing * rows - 1))
        w = round((border * 2) + (size * columns) + (spacing * columns - 1))
        ww = w

        pctl = self.pctl

        if show_lables:
            ww += 500

        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, ww, h)
        c = cairo.Context(surface)

        c.set_source_rgb(bg[0], bg[1], bg[2])
        c.paint()

        text = ""
        i = -1
        for r in range(rows):
            for d in range(columns):

                i += 1

                x = round(border + ((spacing + size) * d))
                y = round(border + ((spacing + size) * r))
                #c.translate(x, y)

                if i > len(tracks) - 1:
                    break

                track = tracks[i]
                artist = track.artist
                if track.album_artist:
                    artist = track.album_artist
                text += f"{track.album} - {artist}\n"

                temp_target = os.path.join(self.cache_dir, "temp")
                try:
                    self.album_art_gen.save_thumb(track, (size, size), temp_target, png=True)
                except:
                    continue

                temp_target += ".png"


                if os.path.isfile(temp_target):
                    art = cairo.ImageSurface.create_from_png(temp_target)
                    c.set_source_surface(art, x, y)
                    c.paint()
            text += "\n"

        if show_lables:
            options = c.get_font_options()
            options.set_antialias(cairo.ANTIALIAS_GRAY)
            c.set_font_options(options)
            layout = PangoCairo.create_layout(c)
            layout.set_ellipsize(Pango.EllipsizeMode.END)
            layout.set_width((500 - text_offset - spacing) * 1000)
            layout.set_height(h * 1000)
            layout.set_spacing(3 * 1000)
            layout.set_font_description(Pango.FontDescription("Monospace 10"))

            layout.set_text(text, -1)
            c.translate(w + text_offset, border + 3)
            c.set_source_rgb(0.9, 0.9, 0.9)
            PangoCairo.show_layout(c, layout)

        output_path = os.path.join(self.user_dir, "chart.png")
        surface.write_to_png(output_path)
        return output_path

