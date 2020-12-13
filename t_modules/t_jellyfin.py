# Tauon Music Box - Jellyin client API module

# Copyright © 2020, Taiko2k captain(dot)gxj(at)gmail.com

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


class Jellyfin():

    def __init__(self, tauon):
        self.tauon = tauon
        self.pctl = tauon.pctl
        self.prefs = tauon.prefs
        self.gui = tauon.gui

        self.scanning = False
        self.connected = False

    def _authenticate(self):
        # todo

        username = self.prefs.jelly_username
        password = self.prefs.jelly_password
        server = self.prefs.jelly_server_url

        self.connected = True

    def resolve_stream(self, id):
        # todo Return a raw http audio file/stream url for given id
        # If theres a choice of raw file or transcode, just use the raw file for now
        return ""

    def resolve_thumbnail(self, id):
        # todo Return an album art url for a given id
        return ""

    def ingest_library(self, return_list=False):
        pass
        # todo uncomment the below section...

        # self.gui.update += 1
        # self.scanning = True
        # if not self.connected:
        #     self._authenticate()
        #
        # if not self.connected:
        #     self.scanning = False
        #     return []
        #
        # playlist = []
        #
        # # This code is to identify if a track has already been imported
        # existing = {}
        # for track_id, track in self.pctl.master_library.items():
        #     if track.is_network and track.file_ext == "JELY":
        #         existing[track.url_key] = track_id
        #
        # # todo Here we want to populate a list with all tracks in the users library.
        # # Maybe there is a function like "get whole library", for "get folders". Tracks will need to be in
        # # order, in groups of folders (or albums)
        #
        # # for album in users_albums:
        # #   ....
        #
        #     parent = # (album_artist + " - " + album_title).strip("- ")  # todo We want some sort of
        #     # unique name for each folder. A proper folder path would be ideal, but we can make
        #     # something from the existing album info as in this example.
        #
        # #    for track in album:
        # #       ....
        #
        #         id = self.pctl.master_count  # id here is tauons track_id for the track
        #         replace_existing = False
        #
        #         e = existing.get(track.key)
        #         if e is not None:
        #             id = e
        #             replace_existing = True
        #
        #
        #         nt = self.tauon.TrackClass()
        #         nt.index = id  # this is tauons track id
        #
        #         # todo Here, fill in the metadata for the track
        #         nt.track_number = str(track.index)
        #         nt.file_ext = "JELY"
        #         nt.parent_folder_path = parent
        #         nt.parent_folder_name = parent
        #         nt.album_artist = album_artist
        #         nt.artist = track_artist
        #         nt.title = title
        #         nt.album = album_title
        #         nt.length = track.duration / 1000  # needs to be in seconds
        #         nt.date = str(year)
        #         nt.is_network = True
        #
        #         # todo Here, fill in the servers UID's for the track
        #         nt.url_key = # Here we want an identifier to get the raw url stream.
        #         nt.art_url_key = # we want some sort of id for the album art, this could be
        #                          # the same as the above stream id. Ignore / leave blank if none
        #
        #         self.pctl.master_library[id] = nt
        #         if not replace_existing:
        #             self.pctl.master_count += 1
        #         playlist.append(nt.index)
        #
        #
        # self.scanning = False
        #
        # if return_list:
        #     return playlist
        #
        # self.pctl.multi_playlist.append(tauon.pl_gen(title="Jellyfin Collection", playlist=playlist))
        # self.pctl.gen_codes[tauon.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "jelly"
        # tauon.switch_playlist(len(self.pctl.multi_playlist) - 1)