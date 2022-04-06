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
import time
import threading
from t_modules.t_extra import Timer

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

        self.session_thread_active = False
        self.session_status = 0
        self.session_item_id = None
        self.session_update_timer = Timer()
        self.session_last_item = None


    def _get_jellyfin_auth(self):
        auth_str = f"MediaBrowser Client={self.tauon.t_title}, Device={self.tauon.device}, DeviceId=-, Version={self.tauon.t_version}"
        if self.accessToken:
            auth_str += f", Token={self.accessToken}"
        return auth_str

    def _authenticate(self, debug=False):
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
                data=json.dumps({ "username": username, "Pw": password }), timeout=(5, 10)
            )
        except:
            self.gui.show_message("Could not establish connection to server.", "Check server is running and URL is correct.", mode="error")
            return

        if response.status_code == 200:
            info = response.json()
            self.accessToken = info["AccessToken"]
            self.userId = info["User"]["Id"]
            self.connected = True
            if debug:
                self.gui.show_message("Connection and authorisation successful", mode="done")
        else:
            if response.status_code == 401:
                self.gui.show_message("401 Authentication failed", "Check username and password.", mode="warning")
            else:
                self.gui.show_message("Jellyfin auth error", f"{response.status_code} {response.text}", mode="warning")

    def test(self):
        self._authenticate(debug=True)

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

        if not self.session_thread_active:
            shoot = threading.Thread(target=self.session)
            shoot.daemon = True
            shoot.start()

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

    def favorite(self, track, un=False):
        try:
            if not self.connected or not self.accessToken:
                self._authenticate()

            if not self.connected:
                return None

            headers = {
                "Token": self.accessToken,
                "X-Application": "Tauon/1.0",
                "x-emby-authorization": self._get_jellyfin_auth()
            }

            params = {}
            base_url = f"{self.prefs.jelly_server_url}/Users/{self.userId}/FavoriteItems/{track.url_key}"
            if un:
                response = requests.delete(base_url, headers=headers, params=params)
            else:
                response = requests.post(base_url, headers=headers, params=params)

            if response.status_code == 200:
                return
            else:
                print("Jellyfin fav api error")

        except:
            print("Failed to submit favorite to Jellyfin server")

    def ingest_library(self, return_list=False):
        self.gui.update += 1
        self.scanning = True
        self.gui.to_got = 0

        print("Prepare for Jellyfin library import...")

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

        print("Get items...")

        try:
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
        except:
            self.gui.show_message("Error connecting to Jellyfin for Import", mode="error")
            self.scanning = False
            return

        if response.status_code == 200:

            print("Connection successful, soring items...")

            # filter audio items only
            audio_items = list(filter(lambda item: item["Type"] == "Audio", response.json()["Items"]))
            # sort by artist, then album, then track number
            sorted_items = sorted(audio_items, key=lambda item: (item.get("AlbumArtist", ""), item.get("Album", ""), item.get("IndexNumber", -1)))
            # group by parent
            grouped_items = itertools.groupby(sorted_items, lambda item: (item.get("AlbumArtist", "") + " - " + item.get("Album", "")).strip("- "))
        else:
            self.scanning = False
            self.tauon.gui.show_message("Error accessing Jellyfin", mode="warning")
            return

        mem_folder = {}
        for parent, items in grouped_items:
            for track in items:
                id = self.pctl.master_count  # id here is tauons track_id for the track
                existing_track = existing.get(track.get("Id"))
                replace_existing = existing_track is not None
                #print(track.items())
                if replace_existing:
                    id = existing_track

                nt = self.tauon.TrackClass()
                nt.index = id  # this is tauons track id
                nt.track_number = str(track.get("IndexNumber", ""))
                nt.disc_number = str(track.get("ParentIndexNumber", ""))
                nt.file_ext = "JELY"
                nt.album_artist = track.get("AlbumArtist", "")
                artists = track.get("Artists", [])
                nt.artist = "; ".join(artists)
                if len(artists) > 1:
                    nt.misc["artists"] = artists
                nt.title = track.get("Name", "")
                nt.album = track.get("Album", "")
                nt.length = track.get("RunTimeTicks", 0) / 10000000   # needs to be in seconds
                nt.date = str(track.get("ProductionYear"))

                folder_name = nt.album_artist
                if folder_name and nt.album:
                    folder_name += " / "
                folder_name += nt.album

                if track.get("AlbumId") and folder_name:
                    key = track.get("AlbumId") + nt.album
                    if key not in mem_folder:
                        mem_folder[key] = folder_name
                    folder_name = mem_folder[key]
                elif nt.album:
                    folder_name = nt.album

                nt.parent_folder_path = folder_name
                nt.parent_folder_name = nt.parent_folder_path
                nt.is_network = True

                nt.url_key = track.get("Id")
                nt.art_url_key = track.get("AlbumId") if track.get("AlbumPrimaryImageTag", False) else None

                self.pctl.master_library[id] = nt
                if not replace_existing:
                    self.pctl.master_count += 1
                playlist.append(nt.index)

                # Sync favorite
                star = self.tauon.star_store.full_get(nt.index)
                user_data = track.get("UserData")
                if user_data:
                    if user_data.get("IsFavorite"):
                        if star is None:
                            star = self.tauon.star_store.new_object()
                        if 'L' not in star[1]:
                            star[1] += "L"
                        self.tauon.star_store.insert(nt.index, star)
                    else:
                        if star is None:
                            pass
                        else:
                            star = [star[0], star[1].replace("L", ""), star[2]]
                            self.tauon.star_store.insert(nt.index, star)

        self.scanning = False
        print("Jellyfin import complete")

        playlist.sort(key=lambda x: self.pctl.master_library[x].parent_folder_path)
        self.tauon.sort_track_2(0, playlist)

        if return_list:
            return playlist

        self.pctl.multi_playlist.append(self.tauon.pl_gen(title="Jellyfin Collection", playlist=playlist))
        self.pctl.gen_codes[self.tauon.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "jelly"
        self.tauon.switch_playlist(len(self.pctl.multi_playlist) - 1)

    def session_item(self, track):
        return {
            "QueueableMediaTypes": ["Audio"],
            "CanSeek": True,
            "ItemId": track.url_key,
            "IsPaused": self.pctl.playing_state == 2,
            "IsMuted": self.pctl.player_volume == 0,
            "PositionTicks": int(self.pctl.playing_time * 10000000),
            "PlayMethod": "DirectStream",
            "PlaySessionId": "0",
        }

    def session(self):

        if not self.connected:
            return

        self.session_thread_active = True

        while True:
            time.sleep(1)
            track = self.pctl.playing_object()

            if track.file_ext != "JELY" or (self.session_status == 0 and self.pctl.playing_state == 0):
                if self.session_status != 0:
                    data = self.session_last_item
                    self.session_send("Sessions/Playing/Stopped", data)
                    self.session_status = 0
                self.session_thread_active = False
                return

            if (self.session_status == 0 or self.session_item_id != track.index) and self.pctl.playing_state == 1:
                data = self.session_item(track)
                self.session_send("Sessions/Playing", data)
                self.session_update_timer.set()
                self.session_status = 1
                self.session_item_id = track.index
                self.session_last_item = data
            elif self.session_status == 1 and self.session_update_timer.get() >= 10:
                data = self.session_item(track)
                data["EventName"] = "TimeUpdate"
                self.session_send("Sessions/Playing/Progress", data)
                self.session_update_timer.set()
            elif self.session_status in (1, 2) and self.pctl.playing_state in (0, 3):
                data = self.session_last_item
                self.session_send("Sessions/Playing/Stopped", data)
                self.session_status = 0
            elif self.session_status == 1 and self.pctl.playing_state == 2:
                data = self.session_item(track)
                data["EventName"] = "Pause"
                self.session_send("Sessions/Playing/Progress", data)
                self.session_update_timer.set()
                self.session_status = 2
            elif self.session_status == 2 and self.pctl.playing_state == 1:
                data = self.session_item(track)
                data["EventName"] = "Unpause"
                self.session_send("Sessions/Playing/Progress", data)
                self.session_update_timer.set()
                self.session_status = 1

    def session_send(self, point, data):

        response = requests.post(
            f"{self.prefs.jelly_server_url}/{point}", data=json.dumps(data),
            headers={
                "Token": self.accessToken,
                "X-Application": "Tauon/1.0",
                "x-emby-authorization": self._get_jellyfin_auth(),
                "Content-Type": "application/json"
            })
