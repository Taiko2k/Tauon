# Tauon Music Box - Album chart image generator

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


import gi
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
import cairo
from gi.repository import Pango
from gi.repository import PangoCairo
import os
from PIL import Image


class TopChart:

    def __init__(self, tauon, album_art_gen):

        self.pctl = tauon.pctl
        self.cache_dir = tauon.cache_directory
        self.user_dir = tauon.user_directory
        self.album_art_gen = album_art_gen

    def generate(self, tracks, bg=(10,10,10), rows=3, columns=3, show_lables=True, font="Monospace 10"):

        # Main control variables
        border = 29
        text_offset = -7
        size = 170
        spacing = 9

        # Determine the final width and height of album grid
        h = round((border * 2) + (size * rows) + (spacing * (rows - 1)))
        w = round((border * 2) + (size * columns) + (spacing * (columns - 1)))
        ww = w

        if show_lables:
            ww += 500  # Add extra area to final size for text

        # Prepare a blank Cairo surface
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, ww, h)
        context = cairo.Context(surface)

        bg = (bg[0] / 255, bg[1] / 255, bg[2] / 255)  # Convert 8-bit rgb values to decimal
        context.set_source_rgb(bg[0], bg[1], bg[2])
        context.paint()  # Fill in the background colour

        text = ""
        i = -1
        for r in range(rows):
            for c in range(columns):

                i += 1

                # Determine coordinates for current album
                x = round(border + ((spacing + size) * c))
                y = round(border + ((spacing + size) * r))

                # Break if we run out of albums
                if i > len(tracks) - 1:
                    break

                # Determine the text label line
                track = tracks[i]
                artist = track.artist
                if track.album_artist:
                    artist = track.album_artist
                text += f"{artist} - {track.album}\n"

                # Export the album art to file object
                try:
                    art_file = self.album_art_gen.save_thumb(track, (size, size), None, png=True)
                except:
                    # Skip drawing this album if loading of artwork failed
                    continue

                # Load image into Cairo and draw
                art = cairo.ImageSurface.create_from_png(art_file)
                context.set_source_surface(art, x, y)
                context.paint()

            text += " \n"  # Insert extra line to form groups for each row

        if show_lables:

            # Setup font and prepare Pango layout
            options = context.get_font_options()
            options.set_antialias(cairo.ANTIALIAS_GRAY)
            context.set_font_options(options)
            layout = PangoCairo.create_layout(context)
            layout.set_ellipsize(Pango.EllipsizeMode.END)
            layout.set_width((500 - text_offset - spacing) * 1000)
            # layout.set_height((h - spacing * 2) * 1000)
            #layout.set_spacing(3 * 1000)
            layout.set_font_description(Pango.FontDescription(font))
            layout.set_text(text, -1)

            # Here we make sure the font size is small enough to fit
            font_comp = font.split(" ")
            font_size = font_comp.pop()
            try:
                font_size = int(font_size)
                while font_size > 2:
                    th = layout.get_pixel_size()[1]
                    if th < h - border:
                        break
                    font_size -= 1
                    font = " ".join(font_comp) + " " + str(font_size)
                    layout.set_font_description(Pango.FontDescription(font))
                    layout.set_text(text, -1)
            except:
                print("error adjusting font size")

            # All good to render now
            context.translate(w + text_offset, border + 3)
            context.set_source_rgb(0.9, 0.9, 0.9)
            PangoCairo.show_layout(context, layout)

        # Finally export as PNG
        output_path = os.path.join(self.user_dir, "chart.png")
        surface.write_to_png(output_path)

        # Convert to JPEG for convenience
        output_path2 = os.path.join(self.user_dir, "chart.jpg")
        im = Image.open(output_path)
        im.save(output_path2, 'JPEG', quality=92)

        return output_path2

