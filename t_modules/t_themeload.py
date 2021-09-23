# Tauon Music Box - Theme reading module

# Copyright © 2015-2020, Taiko2k captain(dot)gxj(at)gmail.com

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


def get_colour_from_line(cline):

    colour = ["", "", "", ""]
    mode = 0

    for i in cline:
        if i.isdigit():
            colour[mode] += i
        elif i == ',':
            mode += 1

    for b in range(len(colour)):
        if colour[b] == "":
            colour[b] = "255"
        colour[b] = int(colour[b])

    return colour


def load_theme(colours, path):
    a = open("/Users/kai/tttb.txt", "w")
    a.write(path)
    a.close()
    f = open(path, encoding="utf-8")
    content = f.readlines()

    for p in content:
        if "#" in p:
            continue
        if "light-mode" in p:
            colours.light_mode()
        if 'window frame' in p:
            colours.window_frame = get_colour_from_line(p)
        if 'gallery highlight' in p:
            colours.gallery_highlight = get_colour_from_line(p)
        if 'index playing' in p:
            colours.index_playing = get_colour_from_line(p)
        if 'time playing' in p:
            colours.time_text = get_colour_from_line(p)
        if 'artist playing' in p:
            colours.artist_playing = get_colour_from_line(p)
        if 'album line' in p:  # Bad name
            colours.album_text = get_colour_from_line(p)
        if 'track album' in p:
            colours.album_text = get_colour_from_line(p)
        if 'album playing' in p:
            colours.album_playing = get_colour_from_line(p)
        if 'player background' in p:  # bad name
            colours.top_panel_background = get_colour_from_line(p)
        if 'top panel' in p:
            colours.top_panel_background = get_colour_from_line(p)
        if 'queue panel' in p:
            colours.queue_background = get_colour_from_line(p)
        if 'side panel' in p:
            colours.side_panel_background = get_colour_from_line(p)
            colours.playlist_box_background = colours.side_panel_background
        if 'gallery background' in p:
            colours.gallery_background = get_colour_from_line(p)
        if 'playlist panel' in p:  # bad name
            colours.playlist_panel_background = get_colour_from_line(p)
        if 'tracklist panel' in p:
            colours.playlist_panel_background = get_colour_from_line(p)
        if 'track line' in p:
            colours.title_text = get_colour_from_line(p)
        if 'track missing' in p:
            colours.playlist_text_missing = get_colour_from_line(p)
        if 'playing highlight' in p:
            colours.row_playing_highlight = get_colour_from_line(p)
        if 'track time' in p:
            colours.bar_time = get_colour_from_line(p)
        if 'fav line' in p:
            colours.star_line = get_colour_from_line(p)
        if 'folder title' in p:
            colours.folder_title = get_colour_from_line(p)
        if 'folder line' in p:
            colours.folder_line = get_colour_from_line(p)
        if 'buttons off' in p:
            colours.media_buttons_off = get_colour_from_line(p)
        if 'buttons over' in p:
            colours.media_buttons_over = get_colour_from_line(p)
        if 'buttons active' in p:
            colours.media_buttons_active = get_colour_from_line(p)
        if 'playing time' in p:
            colours.time_playing = get_colour_from_line(p)
        if 'track index' in p:
            colours.index_text = get_colour_from_line(p)
        if 'track playing' in p:
            colours.title_playing = get_colour_from_line(p)
        if 'select highlight' in p:
            colours.row_select_highlight = get_colour_from_line(p)
        if 'track artist' in p:
            colours.artist_text = get_colour_from_line(p)
        if 'tab active line' in p:  # bad name
            colours.tab_text_active = get_colour_from_line(p)
        if 'tab line' in p:  # bad name
            colours.tab_text = get_colour_from_line(p)
        if 'tab active text' in p:
            colours.tab_text_active = get_colour_from_line(p)
        if 'tab text' in p:
            colours.tab_text = get_colour_from_line(p)
        if 'tab background' in p:
            colours.tab_background = get_colour_from_line(p)
        if 'tab over' in p:
            colours.tab_highlight = get_colour_from_line(p)
        if 'tab active background' in p:
            colours.tab_background_active = get_colour_from_line(p)
        if 'title info' in p:
            colours.side_bar_line1 = get_colour_from_line(p)
        if 'extra info' in p:
            colours.side_bar_line2 = get_colour_from_line(p)
        if 'bottom title' in p:
            colours.bar_title_text = get_colour_from_line(p)
        if 'scroll bar' in p:
            colours.scroll_colour = get_colour_from_line(p)
        if 'seek bar' in p:
            colours.seek_bar_fill = get_colour_from_line(p)
        if 'seek bg' in p:
            colours.seek_bar_background = get_colour_from_line(p)
        if 'volume bar' in p:
            colours.volume_bar_fill = get_colour_from_line(p)
        if 'volume bg' in p:
            colours.volume_bar_background = get_colour_from_line(p)
        if 'mode off' in p:
            colours.mode_button_off = get_colour_from_line(p)
        if 'mode over' in p:
            colours.mode_button_over = get_colour_from_line(p)
        if 'mode on' in p:
            colours.mode_button_active = get_colour_from_line(p)
        if 'art border' in p:
            colours.art_box = get_colour_from_line(p)
        if 'tb line' in p:
            colours.tb_line = get_colour_from_line(p)
        if 'music vis' in p:
            colours.vis_colour = get_colour_from_line(p)
        if 'menu background' in p:
            colours.menu_background = get_colour_from_line(p)
        if 'menu text' in p:
            colours.menu_text = get_colour_from_line(p)
        if 'menu disable' in p:
            colours.menu_text_disabled = get_colour_from_line(p)
        if 'menu icons' in p:
            colours.menu_icons = get_colour_from_line(p)
        if 'menu highlight' in p:
            colours.menu_highlight_background = get_colour_from_line(p)
        if 'menu border' in p:
            colours.menu_tab = get_colour_from_line(p)
        if 'lyrics showcase' in p:
            colours.lyrics = get_colour_from_line(p)
        if 'bottom panel' in p:
            colours.bottom_panel_colour = get_colour_from_line(p)
            # colours.menu_background = colours.bottom_panel_colour
        if 'mini bg' in p:
            colours.mini_mode_background = get_colour_from_line(p)
        if 'mini border' in p:
            colours.mini_mode_border = get_colour_from_line(p)
        if 'mini text 1' in p:
            colours.mini_mode_text_1 = get_colour_from_line(p)
        if 'mini text 2' in p:
            colours.mini_mode_text_2 = get_colour_from_line(p)
        if 'column-' in p:
            key = p[p.find("column-") + 7:].replace("-", " ").lower().title().rstrip()
            value = get_colour_from_line(p)
            colours.column_colours[key] = value
        if 'column+' in p:
            key = p[p.find("column+") + 7:].replace("-", " ").lower().title().rstrip()
            value = get_colour_from_line(p)
            colours.column_colours_playing[key] = value
        if 'menu bg' in p:
            colours.menu_background = get_colour_from_line(p)
        if 'playlist box bg' in p:  # bad name
            colours.playlist_box_background = get_colour_from_line(p)
        if 'playlist background' in p:
            colours.playlist_box_background = get_colour_from_line(p)

        if 'box background' in p:
            colours.box_background = get_colour_from_line(p)
        if 'box border' in p:
            colours.box_border = get_colour_from_line(p)
        if 'box text border' in p:
            colours.box_text_border = get_colour_from_line(p)
        if 'box text label' in p:
            colours.box_text_label = get_colour_from_line(p)

        if 'box title text' in p:
            colours.box_title_text = get_colour_from_line(p)
        if 'box text normal' in p:
            colours.box_text = get_colour_from_line(p)
        if 'box sub text' in p:
            colours.box_sub_text = get_colour_from_line(p)
        if 'box input text' in p:
            colours.box_input_text = get_colour_from_line(p)

        if 'box button text highlight' in p:
            colours.box_button_text_highlight = get_colour_from_line(p)
        if 'box button text normal' in p:
            colours.box_button_text = get_colour_from_line(p)
        if 'box button background normal' in p:
            colours.box_button_background = get_colour_from_line(p)
        if 'box button background highlight' in p:
            colours.box_button_background_highlight = get_colour_from_line(p)
        if 'box button border' in p:
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
        #     colours.corner_button = get_colour_from_line(p)
        # if "panel button on" in p:
        #     colours.corner_button_active = get_colour_from_line(p)

        colours.post_config()
        if colours.lm:
            colours.light_mode()
