# Tauon Music Box - Download program adaptor

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

import os
import subprocess
import shlex
import shutil
import copy
import stagger
import io
from PIL import Image
import multiprocessing as mp
from multiprocessing import Process

#mp.set_start_method('spawn')

class AutoDownload:

    def __init__(self, tauon):
        self.tauon = tauon
        self.downloading = False
        self.dl_dir = os.path.join(self.tauon.cache_directory, "ddl")

    def get_downloaders_list(self):

        downloaders = ['youtube-dl', 'spotdl', 'bandcamp-dl', 'scdl']

        for i in reversed(range(len(downloaders))):
            if not self.tauon.whicher(downloaders[i]):
                del downloaders[i]

        return downloaders

    def import_item(self, path):

        if os.path.exists(path):

            load_order = self.tauon.pctl.LoadClass()
            load_order.target = path
            load_order.force_scan = True
            pln = self.tauon.pctl.active_playlist_viewing
            load_order.playlist = self.tauon.pctl.multi_playlist[pln][6]
            for i, pl in enumerate(self.tauon.pctl.multi_playlist):
                if pl[0].lower() == "downloads":
                    load_order.playlist = pl[6]
                    pln = i
                    break

            self.tauon.load_orders.append(copy.deepcopy(load_order))
            self.tauon.switch_playlist(pln)
            self.tauon.gui.show_message("Import of downloaded tracks complete", 'done', "Remember to support the artists!")

    def embed_image(self, path, string):

        print("Embed")
        tag = stagger.read_tag(path)
        tt = tag[stagger.id3.APIC][0]
        tt.data = string
        tag.write()
        print("Done")


    def run(self, text):

        text = text.strip()

        # Verify text is a link
        if not text.startswith("http"):
            self.tauon.gui.show_message("Could not identify text as link")
            return
        if " " in text:
            self.tauon.gui.show_message("Could not verify text as link")
            return

        downloaders = self.get_downloaders_list()
        dl_dir = self.dl_dir

        # Clear old download cache folder and make anew
        if os.path.exists(dl_dir):
            shutil.rmtree(dl_dir)
        os.makedirs(dl_dir)

        # Youtube downloader
        if "youtube.com" in text or "youtu.be" in text:
            if "youtube-dl" not in downloaders:
                self.tauon.gui.show_message("Downloading Youtube tracks requires youtube-dl")
                return

            self.tauon.gui.show_message("Type detected: Youtube", 'info', 'Link: ' + text)

            # youtube_dir = os.path.join(dl_dir, 'Youtube')
            youtube_dir = dl_dir
            # os.makedirs(youtube_dir)

            line = self.tauon.launch_prefix + "youtube-dl -f bestaudio -o \"" + youtube_dir + "/%(title)s.%(ext)s\" --extract-audio --embed-thumbnail --add-metadata --audio-quality 160K --audio-format mp3 " + text
            self.downloading = True
            subprocess.run(shlex.split(line))

            for item in os.listdir(youtube_dir):
                if item.endswith(".mp3"):
                    path = os.path.join(youtube_dir, item)
                else:
                    continue

                # Get image from mp3 file
                tag = stagger.read_tag(path)
                tt = tag[stagger.id3.APIC][0]
                s = io.BytesIO(tt.data)
                im = Image.open(s)

                # Check for side bars (hacky, but should work most the time)
                w, h = im.size
                p1 = im.getpixel((1, 1))
                p2 = im.getpixel((30, 30))
                p3 = im.getpixel((w - 30, h - 30))
                p4 = im.getpixel((w - 1, h - 1))
                if p1 == p2 == p3 == p4:

                    # Crop to square
                    m = min(w, h)
                    im = im.crop((
                        (w - m) / 2,
                        (h - m) / 2,
                        (w + m) / 2,
                        (h + m) / 2,
                    ))

                    # Convert to bytes string
                    g = io.BytesIO()
                    g.seek(0)
                    im.save(g, 'JPEG')
                    g.seek(0)
                    string = g.getvalue()

                    # Embed back into mp3
                    # Workaround for unix signals issue
                    p = Process(target=self.embed_image, args=(path, string))
                    p.start()
                    p.join()


        # Spotify -> Youtube downloader
        elif "open.spotify.com/album/" in text:
            if "spotdl" not in downloaders:
                self.tauon.gui.show_message("Downloading Spotify (via Youtube) albums requires spotdl")
                return

            if "youtube-dl" not in downloaders:
                self.tauon.gui.show_message("Downloading Youtube songs (from Spotify) requires youtube-dl")
                return

            track_list_file = os.path.join(dl_dir, "tracklist.txt")
            code = text.split("/")[-1]

            line = self.tauon.launch_prefix + "spotdl --write-to=\"" + track_list_file + "\" --album " + text
            self.downloading = True
            subprocess.run(shlex.split(line))

            if not os.path.isfile(track_list_file):
                self.downloading = False
                self.tauon.gui.show_message("Could not get tracklist from Spotify")
                return

            self.downloading = True
            self.tauon.gui.show_message("Type detected: Spotify", 'info', 'Link: ' + text)
            os.makedirs(os.path.join(dl_dir, code))
            line = self.tauon.launch_prefix + "spotdl --list=\"" + track_list_file + "\" --folder=\"" + os.path.join(dl_dir, code) + "\""
            subprocess.run(shlex.split(line))

            if os.path.isfile(track_list_file):
                os.remove(track_list_file)

        # Bandcamp downloader
        elif ".bandcamp.com" in text:
            if "bandcamp-dl" not in downloaders:
                self.tauon.gui.show_message("Downloading Bandcamp albums requires bandcamp-dl")
                return

            self.tauon.gui.show_message("Type detected: Bandcamp", 'info', 'Link: ' + text)
            line = self.tauon.launch_prefix + "bandcamp-dl -e --base-dir=\"" + dl_dir + "\" --template=\"%{artist} - %{album}/%{track} - %{title}\" " + text
            self.downloading = True
            subprocess.run(shlex.split(line))

        # Soundcloud downloader
        elif "soundcloud.com" in text:
            if "scdl" not in downloaders:
                self.tauon.gui.show_message("Downloading Soundcloud playlists requires scdl")
                return

            self.tauon.gui.show_message("Type detected: Soundcloud", 'info', 'Link: ' + text)
            line = self.tauon.launch_prefix + "scdl -l --path=\"" + dl_dir + "\" " + text
            self.downloading = True
            subprocess.run(shlex.split(line))

        # No downloader for link found
        else:
            self.tauon.gui.show_message("Not compatible with this type of link")

        # Move downloads from cache folder to music folder
        for item in os.listdir(dl_dir):
            item_path = os.path.join(dl_dir, item)
            target_path = os.path.join(self.tauon.music_directory, item)

            if target_path not in self.tauon.dl_mon.done:
                self.tauon.dl_mon.done.add(target_path)
            try:
                shutil.move(item_path, self.tauon.music_directory)
                self.import_item(target_path)
            except:
                self.downloading = False
                self.tauon.gui.show_message("File already exists", 'error')
                raise
                return

        # Give warning about spotdl
        if 'open.spotify.com' in text:
            self.tauon.gui.show_message("Download complete", 'done', "Warning: This method is unreliable, found tracks may not match")

        self.downloading = False

