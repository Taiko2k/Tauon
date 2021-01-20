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

import requests
import json
import itertools
import io


class Jellyfin():

    def __init__(self, tauon):
        self.tauon = tauon
        self.pctl = tauon.pctl
        self.prefs = tauon.prefs
        self.gui = tauon.gui

        self.scanning = False
        self.connected = False

        self.accessToken = None
        self.userId = None
        self.currentId = None

    def _get_jellyfin_auth(self):
        auth_str = f"MediaBrowser Client={self.tauon.t_title}, Device={self.tauon.device}, DeviceId=-, Version={self.tauon.t_version}"
        if self.accessToken:
            auth_str += f", Token={self.accessToken}"
        return auth_str

    def _authenticate(self):
        username = self.prefs.jelly_username
        password = self.prefs.jelly_password
        server = self.prefs.jelly_server_url

        try:
            response = requests.post(
                f"{server}/Users/AuthenticateByName",
                headers={
                    "Content-type": "application/json",
                    "X-Application": self.tauon.t_agent,
                    "x-emby-authorization": self._get_jellyfin_auth()
                },
                data=json.dumps({ "username": username, "Pw": password }),
            )
        except:
            return

        if response.status_code == 200:
            info = response.json()
            self.accessToken = info["AccessToken"]
            self.userId = info["User"]["Id"]
            self.connected = True


    def resolve_stream(self, id):
        if not self.connected or not self.accessToken:
            self._authenticate()

        if not self.connected:
            return ""

        base_url = f"{self.prefs.jelly_server_url}/Audio/{id}/stream"
        headers = {
            "Token": self.accessToken,
            "X-Application": "Tauon/1.0",
            "x-emby-authorization": self._get_jellyfin_auth()
        }
        params = {
            "UserId": self.userId,
            "static": "true"
        }

        if self.prefs.network_stream_bitrate > 0:
            params["MaxStreamingBitrate"] = self.prefs.network_stream_bitrate

        url = base_url + "?" + requests.compat.urlencode(params)

        return base_url, params

    def get_cover(self, track):
        if not self.connected or not self.accessToken:
            self._authenticate()

        if not self.connected:
            return None

        if not track.art_url_key:
            return None

        headers = {
            "Token": self.accessToken,
            "X-Application": "Tauon/1.0",
            "x-emby-authorization": self._get_jellyfin_auth()
        }
        params = {}
        base_url = f"{self.prefs.jelly_server_url}/Items/{track.art_url_key}/Images/Primary"
        response = requests.get(base_url, headers=headers, params=params)

        if response.status_code == 200:
            return io.BytesIO(response.content)
        else:
            print("Jellyfin album art api error:", response.status_code, response.text)
            return None

    def ingest_library(self, return_list=False):
        self.gui.update += 1
        self.scanning = True
        if not self.connected or not self.accessToken:
            self._authenticate()

        if not self.connected:
            self.scanning = False
            if not return_list:
                self.tauon.gui.show_message("Error connecting to Jellyfin")
            return []

        playlist = []

        # This code is to identify if a track has already been imported
        existing = {}
        for track_id, track in self.pctl.master_library.items():
            if track.is_network and track.file_ext == "JELY":
                existing[track.url_key] = track_id

        response = requests.get(
            f"{self.prefs.jelly_server_url}/Users/{self.userId}/Items",
            headers={
                "Token": self.accessToken,
                "X-Application": "Tauon/1.0",
                "x-emby-authorization": self._get_jellyfin_auth()
            },
            params={
                "recursive": True,
                "filter": "music"
            }
        )

        if response.status_code == 200:
            # filter audio items only
            audio_items = list(filter(lambda item: item["Type"] == "Audio", response.json()["Items"]))
            # sort by artist, then album, then track number
            sorted_items = sorted(audio_items, key=lambda item: (item.get("AlbumArtist", ""), item.get("Album", ""), item.get("IndexNumber", -1)))
            # group by parent
            grouped_items = itertools.groupby(sorted_items, lambda item: (item.get("AlbumArtist", "") + " - " + item.get("Album", "")).strip("- "))
        else:
            self.scanning = False
            self.tauon.gui.show_message("Error accessing Jellyfin")
            return

        for parent, items in grouped_items:
            for track in items:
                id = self.pctl.master_count  # id here is tauons track_id for the track
                existing_track = existing.get(track.get("Id"))
                replace_existing = existing_track is not None

                if replace_existing:
                    id = existing_track

                nt = self.tauon.TrackClass()
                nt.index = id  # this is tauons track id

                nt.track_number = str(track.get("IndexNumber", ""))
                nt.file_ext = "JELY"
                nt.parent_folder_path = parent
                nt.parent_folder_name = parent
                nt.album_artist = track.get("AlbumArtist", "")
                nt.artist = track.get("AlbumArtist", "")
                nt.title = track.get("Name", "")
                nt.album = track.get("Album", "")
                nt.length = track.get("RunTimeTicks", 0) / 10000000   # needs to be in seconds
                nt.date = str(track.get("ProductionYear"))
                nt.is_network = True

                nt.url_key = track.get("Id")
                nt.art_url_key = track.get("Id") if track.get("AlbumPrimaryImageTag", False) else None

                self.pctl.master_library[id] = nt
                if not replace_existing:
                    self.pctl.master_count += 1
                playlist.append(nt.index)

        self.scanning = False

        if return_list:
            return playlist

        self.pctl.multi_playlist.append(self.tauon.pl_gen(title="Jellyfin Collection", playlist=playlist))
        self.pctl.gen_codes[self.tauon.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "jelly"
        self.tauon.switch_playlist(len(self.pctl.multi_playlist) - 1)
