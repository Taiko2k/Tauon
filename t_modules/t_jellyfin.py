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
import os

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
        self.playlists = []


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

    def upload_playlist(self, pl):
        if not self.connected or not self.accessToken:
            self._authenticate()
        if not self.connected:
            return

        codes = self.pctl.gen_codes.get(self.pctl.multi_playlist[pl][6], "")

        ids = []
        for t in self.pctl.multi_playlist[pl][2]:
            track = self.pctl.g(t)
            if track.url_key not in ids and track.file_ext == "JELY":
                ids.append(track.url_key)

        if "jelly\"" not in codes:

            response = requests.post(
                f"{self.prefs.jelly_server_url}/Playlists",
                data={},
                headers={
                    "Token": self.accessToken,
                    "X-Application": "Tauon/1.0",
                    "x-emby-authorization": self._get_jellyfin_auth(),
                    "Content-Type": "text/json"
                },
                params={
                    "UserId": self.userId,
                    "Name": self.pctl.multi_playlist[pl][0],
                    "Ids": ",".join(ids),
                    "MediaType": "Music"
                }
            )

            id = response.json()["Id"]
            self.pctl.gen_codes[self.pctl.multi_playlist[pl][6]] = f"jelly\"{id}\""
            print("New jellyfin playlist created")

        else:
            code = codes.split(" ")[0]
            if not code.startswith("jelly\""):
                return
            code = code[6:-1]
            if "\"" in code or not code:
                return

            # upload difference
            response = requests.get(
                f"{self.prefs.jelly_server_url}/Playlists/{code}/Items",
                headers={
                    "Token": self.accessToken,
                    "X-Application": "Tauon/1.0",
                    "x-emby-authorization": self._get_jellyfin_auth()
                },
                params={
                    "UserId": self.userId,
                }
            )
            if response.status_code != 200:
                print("error")
                return

            d_ids = []
            for item in response.json()["Items"]:
                d_ids.append(item["PlaylistItemId"])

            response = requests.delete(
                f"{self.prefs.jelly_server_url}/Playlists/{code}/Items",
                headers={
                    "Token": self.accessToken,
                    "X-Application": "Tauon/1.0",
                    "x-emby-authorization": self._get_jellyfin_auth()
                },
                params={
                    "UserId": self.userId,
                    "EntryIds": ",".join(d_ids),
                }
            )

            if response.status_code not in (200, 204):
                print("error2")
                return

            response = requests.post(
                f"{self.prefs.jelly_server_url}/Playlists/{code}/Items",
                data={},
                headers={
                    "Token": self.accessToken,
                    "X-Application": "Tauon/1.0",
                    "x-emby-authorization": self._get_jellyfin_auth(),
                    "Content-Type": "text/json"
                },
                params={
                    "UserId": self.userId,
                    "Ids": ",".join(ids),
                }
            )
        print("DONE")


    def get_playlist(self, id, name="", return_list=False):
        if not self.connected or not self.accessToken:
            self._authenticate()
        if not self.connected:
            return []
        response = requests.get(
            f"{self.prefs.jelly_server_url}/Playlists/{id}/Items",
            headers={
                "Token": self.accessToken,
                "X-Application": "Tauon/1.0",
                "x-emby-authorization": self._get_jellyfin_auth()
            },
            params={
                "UserId": self.userId,
            }
        )

        existing = {}
        for track_id, track in self.pctl.master_library.items():
            if track.is_network and track.file_ext == "JELY":
                existing[track.url_key] = track_id

        playlist = []
        for item in response.json()["Items"]:
            track_id = existing.get(item["Id"])
            if track_id is not None:
                playlist.append(track_id)

        if return_list:
            return playlist

        self.scanning = False
        self.pctl.multi_playlist.append(self.tauon.pl_gen(title=name, playlist=playlist))
        self.pctl.gen_codes[self.tauon.pl_to_id(len(self.pctl.multi_playlist) - 1)] = f"jelly\"{id}\""

    def get_playlists(self):
        if not self.playlists:
            self.ingest_library(return_list=True)
        if not self.connected:
            return

        for p in self.playlists:
            found = False
            for pp in self.pctl.multi_playlist:
                if f"jelly\"{p['Id']}\"" in self.pctl.gen_codes.get(pp[6], ""):
                    found = True
                    break
            if found:
                continue

            # Get Playlist
            response = requests.get(
                f"{self.prefs.jelly_server_url}/Playlists/{p['Id']}/Items",
                headers={
                    "Token": self.accessToken,
                    "X-Application": "Tauon/1.0",
                    "x-emby-authorization": self._get_jellyfin_auth()
                },
                params={
                    "UserId": self.userId,
                }
            )

            existing = {}
            for track_id, track in self.pctl.master_library.items():
                if track.is_network and track.file_ext == "JELY":
                    existing[track.url_key] = track_id

            playlist = []
            for item in response.json()["Items"]:
                track_id = existing.get(item["Id"])
                if track_id is not None:
                    playlist.append(track_id)

            self.scanning = False
            self.pctl.multi_playlist.append(self.tauon.pl_gen(title=p['Name'], playlist=playlist))
            self.pctl.gen_codes[self.tauon.pl_to_id(len(self.pctl.multi_playlist) - 1)] = f"jelly\"{p['Id']}\""

    def get_info(self, fast=False):
        dones = []
        i = 0
        for p in self.pctl.multi_playlist:
            for t in p[2]:
                tr = self.pctl.g(t)
                i += 1
                if i % 1000 == 0:
                    print(i)
                if tr.file_ext == "JELY":
                    if tr.fullpath and fast:
                        continue
                    if tr.url_key not in dones:
                        dones.append(tr.url_key)

                    # Get media info
                    response = requests.get(
                        f"{self.prefs.jelly_server_url}/Items/{tr.url_key}/PlaybackInfo",
                        headers={
                            "Token": self.accessToken,
                            "X-Application": "Tauon/1.0",
                            "x-emby-authorization": self._get_jellyfin_auth()
                        },
                        params={
                            "UserId": self.userId,
                        }
                    )
                    if response.status_code == 200:
                        try:
                            d = response.json()
                            tr.fullpath = d["MediaSources"][0]["Path"]
                            tr.filename = os.path.basename(tr.fullpath)
                            tr.parent_folder_path = os.path.dirname(tr.fullpath)
                            tr.parent_folder_name = os.path.basename(tr.parent_folder_path)
                            tr.misc["container"] = d["MediaSources"][0]["Container"].upper()
                            tr.misc["codec"] = d["MediaSources"][0]["MediaStreams"][0]["Codec"]
                            tr.bitrate = round(d["MediaSources"][0]["MediaStreams"][0]["BitRate"] / 1000)
                            tr.bit_depth = d["MediaSources"][0]["MediaStreams"][0].get("BitDepth", 0)
                            tr.samplerate = round(d["MediaSources"][0]["MediaStreams"][0]["SampleRate"])
                        except:
                            print("ERROR")

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
            playlist_items = list(filter(lambda item: item["Type"] == "Playlist", response.json()["Items"]))
            self.playlists = playlist_items
            # sort by artist, then album, then track number
            sorted_items = sorted(audio_items, key=lambda item: (item.get("AlbumArtist", ""), item.get("Album", ""), item.get("IndexNumber", -1)))
            # group by parent
            grouped_items = itertools.groupby(sorted_items, lambda item: (item.get("AlbumArtist", "") + " - " + item.get("Album", "")).strip("- "))
        else:
            self.scanning = False
            self.tauon.gui.show_message("Error accessing Jellyfin", mode="warning")
            return

        mem_folder = {}
        fav_status = {}
        for parent, items in grouped_items:
            for track in items:
                id = self.pctl.master_count  # id here is tauons track_id for the track
                existing_track = existing.get(track.get("Id"))
                replace_existing = existing_track is not None
                #print(track.items())
                if replace_existing:
                    id = existing_track
                    nt = self.pctl.g(id)
                else:
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
                    fav_status[nt] = user_data.get("IsFavorite")


        print("Jellyfin import complete")
        self.gui.update += 1
        self.tauon.wake()

        def set_favs(d):
            for tr, v in d.items():
                star = self.tauon.star_store.full_get(tr.index)

                if v:
                    if star is None:
                        star = self.tauon.star_store.new_object()
                    if 'L' not in star[1]:
                        star[1] += "L"
                    self.tauon.star_store.insert(tr.index, star)
                else:
                    if star is None:
                        pass
                    else:
                        star = [star[0], star[1].replace("L", ""), star[2]]
                        self.tauon.star_store.insert(tr.index, star)

        if return_list:
            self.get_info(fast=True)
            playlist.sort(key=lambda x: self.pctl.master_library[x].parent_folder_path)
            self.tauon.sort_track_2(0, playlist)
            set_favs(fav_status)
            self.scanning = False
            return playlist

        self.pctl.multi_playlist.append(self.tauon.pl_gen(title="Jellyfin Collection", playlist=playlist))
        self.pctl.gen_codes[self.tauon.pl_to_id(len(self.pctl.multi_playlist) - 1)] = "jelly"
        self.tauon.switch_playlist(len(self.pctl.multi_playlist) - 1)

        self.get_info()
        playlist.sort(key=lambda x: self.pctl.master_library[x].parent_folder_path)
        self.tauon.sort_track_2(0, playlist)
        set_favs(fav_status)
        self.scanning = False
        self.gui.update += 1
        self.tauon.wake()

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
