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
try:
    import tekore as tk
    tekore_imported = True
except:
    tekore_imported = False

import pickle
import requests
import io
import webbrowser
import subprocess
import time
import json
from t_modules.t_extra import Timer


class SpotCtl:

    def __init__(self, tauon):
        self.tauon = tauon
        self.strings = tauon.strings
        self.start_timer = Timer()
        self.status = 0
        self.spotify = None
        self.loaded_art = ""
        self.playing = False
        self.coasting = False
        self.paused = False
        self.token = None
        self.cred = None
        self.started_once = False
        self.redirect_uri = f"http://localhost:7811/spotredir"
        self.current_imports = {}
        self.spotify_com = False
        self.sender = None
        self.cache_saved_albums = []
        self.scope = "user-read-playback-position streaming user-modify-playback-state user-library-modify user-library-read user-read-currently-playing user-read-playback-state playlist-read-private playlist-modify-private playlist-modify-public"
        self.launching_spotify = False
        self.preparing_spotify = False
        self.progress_timer = Timer()
        self.update_timer = Timer()

        self.token_path = os.path.join(self.tauon.user_directory, "spot-token-pkce")
        self.pkce_code = None
        self.local = True

        self.coast_context = ""

    def prep_cred(self):

        rc = tk.RefreshingCredentials
        self.cred = rc(client_id=self.tauon.prefs.spot_client,
                                    redirect_uri=self.redirect_uri)

    def connect(self):
        if not self.tauon.prefs.spotify_token or not self.tauon.prefs.spot_mode:
            return
        if len(self.tauon.prefs.spot_client) != 32:
            return
        if self.cred is None:
            self.prep_cred()
        if self.spotify is None:
            if self.token is None:
                self.load_token()
            if self.token:
                print("Init spotify support")
                self.sender = tk.RetryingSender(retries=3)
                self.spotify = tk.Spotify(self.token, sender=self.sender)

    def paste_code(self, code):
        if self.cred is None:
            self.prep_cred()

        self.token = self.cred.request_pkce_token(code.strip().strip("\n"), self.pkce_code)
        if self.token:
            self.save_token()
            self.tauon.gui.show_message(self.strings.spotify_account_connected, mode="done")
        self.tauon.prefs.spot_mode = True
    def save_token(self):

        if self.token:
            f = open(self.token_path, "w")
            f.write(str(self.token.refresh_token))
            f.close()
            self.tauon.prefs.spotify_token = str(self.token.refresh_token)

    def load_token(self):
        if os.path.isfile(self.token_path):
            f = open(self.token_path, "r")
            self.tauon.prefs.spotify_token = f.read().replace("\n", "").strip()
            f.close()

        if self.tauon.prefs.spotify_token:
            try:
                self.token = tk.refresh_pkce_token(self.tauon.prefs.spot_client, self.tauon.prefs.spotify_token)
            except:
                self.tauon.gui.show_message("Please re-authenticate Spotify in settings")
                print("ERROR LOADING TOKEN")
                self.tauon.prefs.spotify_token = ""
        else:
            self.tauon.gui.show_message("Please authenticate Spotify in settings")

    def delete_token(self):
        self.tauon.prefs.spotify_token = ""
        self.token = None
        if os.path.exists(self.token_path):
            os.remove(self.token_path)

    def auth(self):
        if not tekore_imported:
            self.tauon.gui.show_message("python-tekore not installed",
                                        "If you installed via AUR, you'll need to install this optional dependency, then restart Tauon.", mode="error")
            return
        if len(self.tauon.prefs.spot_client) != 32:
            self.tauon.gui.show_message("Invalid client ID. See Spotify tab in settings.", mode="error")
            return
        if self.cred is None:
            self.prep_cred()
        url, self.pkce_code = self.cred.pkce_user_authorisation(scope=self.scope)
        webbrowser.open(url, new=2, autoraise=True)

    def control(self, command, param=None):

        try:
            if command == "pause" and (self.playing or self.coasting) and not self.paused:
                self.spotify.playback_pause()
                self.paused = True
                self.start_timer.set()
            if command == "stop" and (self.playing or self.coasting):
                self.paused = False
                self.playing = False
                self.coasting = False
                self.spotify.playback_pause()
                self.start_timer.set()
            if command == "resume" and (self.coasting or self.playing) and self.paused:
                self.spotify.playback_resume()
                self.paused = False
                self.progress_timer.set()
                self.start_timer.set()
            if command == "volume":
                self.spotify.playback_volume(param)
            if command == "seek":
                self.spotify.playback_seek(param)
                self.start_timer.set()
            if command == "next":
                self.spotify.playback_next(param)
                #self.start_timer.set()
            if command == "previous":
                self.spotify.playback_previous(param)
                #self.start_timer.set()

        except Exception as e:
            print(repr(e))
            if "No active device found" in repr(e):
                try:
                    tr = self.tauon.pctl.playing_object()
                    if command == "resume" and tr and tr.file_ext == "SPTY" and tr.url_key:
                        self.tauon.gui.show_message("Resuming Spotify playback")
                        p = self.tauon.pctl.playing_time
                        self.play_target(tr.url_key)
                        time.sleep(0.3)
                        self.spotify.playback_seek(int(p * 1000))
                        self.tauon.gui.message_box = False
                        self.tauon.gui.update += 1
                        return
                except:
                    pass
                self.tauon.gui.show_message("It looks like there are no more active Spotify devices")

    def get_username(self):
        self.connect()
        if not self.spotify:
            return None
        c = self.spotify.current_user()
        if c and c.id:
            return c.id
        return None
    def add_album_to_library(self, url):
        self.connect()
        if not self.spotify:
            return None

        id = url.strip("/").split("/")[-1]

        try:
            self.spotify.saved_albums_add([id])
            if url not in self.cache_saved_albums:
                self.cache_saved_albums.append(url)
        except:
            print("Error saving album")

    def remove_album_from_library(self, url):

        self.connect()
        if not self.spotify:
            return None
        id = url.strip("/").split("/")[-1]

        try:
            self.spotify.saved_albums_delete([id])
            if url in self.cache_saved_albums:
                self.cache_saved_albums.remove(url)
        except:
            print("Error removing album")

    def get_album_url_from_local(self, track_object):

        if "spotify-album-url" in track_object.misc:
            return track_object.misc["spotify-album-url"]

        self.connect()
        if not self.spotify:
            return None

        results = self.spotify.search(track_object.artist + " " + track_object.album, types=('album',), limit=1)
        for album in results[0].items:
            if "spotify" in album.external_urls:
                return album.external_urls["spotify"]

        return None

    def get_artist_url_from_local(self, track_object):

        if "spotify-artist-url" in track_object.misc:
            return track_object.misc["spotify-artist-url"]

        self.connect()
        if not self.spotify:
            return None

        results = self.spotify.search(track_object.artist + " " + track_object.album, types=('artist',), limit=1)
        for artist in results[0].items:
            if "spotify" in artist.external_urls:
                return artist.external_urls["spotify"]

        return None

    def import_all_playlists(self):

        self.spotify_com = True

        playlists = self.get_playlist_list()
        if playlists:
            for item in playlists:
                self.playlist(item[1], silent=True)
                self.tauon.gui.update += 1
                time.sleep(0.1)

        self.spotify_com = False
        if not playlists:
            self.tauon.gui.show_message(self.strings.spotify_need_enable)
            return
        self.tauon.gui.show_message(self.strings.spotify_import_complete, mode="done")

    def get_playlist_list(self):
        self.connect()
        if not self.spotify:
            self.tauon.gui.show_message(self.strings.spotify_need_enable)
            return None

        playlists = []
        results = self.spotify.playlists(self.spotify.current_user().id)
        pages = self.spotify.all_pages(results)
        for page in pages:
            items = page.items
            for item in items:
                name = item.name
                url = item.external_urls["spotify"]
                playlists.append((name, url))

        return playlists

    def search(self, text):
        self.connect()
        if not self.spotify:
            return

        results = self.spotify.search(text,
                                      types=('artist', 'album', 'track'),
                                      limit=20
                                      )

        finds = []

        self.tauon.QuickThumbnail.queue.clear()

        if results[0]:

            for i, album in enumerate(results[0].items[1:]):

                img = self.tauon.QuickThumbnail()
                img.url = album.images[-1].url
                img.size = round(50 * self.tauon.gui.scale)
                self.tauon.QuickThumbnail().items.append(img)
                if i < 10:
                    self.tauon.QuickThumbnail().queue.append(img)
                try:
                    self.tauon.gall_ren.lock.release()
                except:
                    pass

                finds.append((11, (album.name, album.artists[0].name), album.external_urls["spotify"], 0, 0, img))

            for artist in results[1].items[0:1]:
                finds.insert(1, (10, artist.name, artist.external_urls["spotify"], 0, 0, None))
            for artist in results[1].items[1:2]:
                finds.insert(11, (10, artist.name, artist.external_urls["spotify"], 0, 0, None))

            for track in results[2].items[0:1]:
                finds.insert(2, (12, (track.name, track.artists[0].name), track.external_urls["spotify"], 0, 0, None))
            for track in results[2].items[5:6]:
                finds.insert(8, (12, (track.name, track.artists[0].name), track.external_urls["spotify"], 0, 0, None))

        return finds


    def search_track(self, track):
        if track is None:
            return

        self.connect()
        if not self.spotify:
            return

        if track.artist and track.title:
            results = self.spotify.search(track.artist + " " + track.title,
                                     types=('track',),
                                     limit=1
                                     )

    def prime_device(self):
        self.connect()
        if not self.spotify:
            return

        devices = self.spotify.playback_devices()

        if devices:
            pass
        else:
            print("No spotify devices found")

        if not devices:
            return False
        for d in devices:
            if d.is_active:
                return None
        for d in devices:
            if not d.is_restricted:
                return d.id
        return None

    def transfer_to_tauon(self, wait=7):
        self.connect()
        if not self.spotify:
            return
        time.sleep(wait)

        p = self.spotify.playback()
        if not p or not p.is_playing:
            self.tauon.gui.show_message("Nothing playing")
            return

        devices = self.spotify.playback_devices()
        for d in devices:
            if d.name == "Tauon Music Box":
                self.spotify.playback_transfer(d.id, True)
                print("Found Tauon Spotify player")
                break
        else:
            self.tauon.gui.show_message("Error - Tauon device not found")

        # if not self.coasting or self.playing:
        #     self.update(start=True)
    def play_target(self, id, force_new_device=False):

        self.coasting = False
        self.connect()
        if not self.spotify:
            self.preparing_spotify = False
            self.tauon.gui.show_message("Error. You may need to click Authorise in Settings > Accounts > Spotify.", mode="warning")
            return

        d_id = self.prime_device()
        # if d_id is False:
        #     return

        print("play spotify target")
        #if self.tauon.pctl.playing_state == 1 and self.playing and self.tauon.pctl.playing_time
        #try:
        if d_id is False or force_new_device:
            if not force_new_device:
                self.launching_spotify = True
            self.tauon.gui.update += 1

            print("no devices")
            if self.tauon.prefs.launch_spotify_web:
                webbrowser.open("https://open.spotify.com/", new=2, autoraise=False)
                tries = 0
                while True:
                    time.sleep(2)
                    if tries == 0:
                        self.tauon.focus_window()
                    devices = self.spotify.playback_devices()
                    if devices:
                        self.progress_timer.set()
                        self.spotify.playback_start_tracks([id], device_id=devices[0].id)
                        break
                    tries += 1
                    if tries > 13:
                        self.tauon.pctl.stop()
                        self.tauon.gui.show_message(self.strings.spotify_error_starting, mode="error")
                        self.launching_spotify = False
                        self.preparing_spotify = False
                        self.tauon.gui.update += 1
                        return
            else:

                if self.tauon.prefs.launch_spotify_local:
                    print("start librespot command")
                    self.tauon.tm.ready_playback()
                    self.tauon.pctl.playerCommand = 'spotcon'
                    self.tauon.pctl.playerCommandReady = True
                    #self.tauon.pctl.playing_state = 3
                elif self.tauon.msys:
                    p = os.getenv('APPDATA') + "\\Spotify\\Spotify.exe"
                    if not os.path.isfile(p):
                        return
                    subprocess.Popen([p])
                    time.sleep(3)
                else:
                    subprocess.run(["xdg-open", "spotify:track"])
                    time.sleep(3)
                print("LAUNCH SPOTIFY")

                time.sleep(0.5)
                tries = 0
                playing = False
                while True:
                    print("WAIT FOR DEVICE...")
                    devices = self.spotify.playback_devices()
                    if devices and tries < 13:
                        print("DEVICE FOUND")
                        self.tauon.focus_window()
                        time.sleep(0.5)
                        print("ATTEMPT START")
                        try:
                            self.spotify.playback_start_tracks([id], device_id=devices[0].id)
                        except Exception as e:
                            print(str(e))
                            time.sleep(1)
                            tries += 2
                            continue
                        while True:
                            result = self.spotify.playback_currently_playing()
                            if result and result.is_playing:
                                playing = True
                                self.progress_timer.set()
                                print("TRACK START SUCCESS")
                                break
                            time.sleep(1)
                            tries += 1
                            print("NOT PLAYING YET...")
                            if tries > 13:
                                break

                    if playing:
                        break
                    tries += 1
                    if tries > 13:
                        print("TOO MANY TRIES")
                        self.tauon.pctl.stop()
                        self.tauon.gui.show_message(self.strings.spotify_error_starting, mode="error")
                        self.launching_spotify = False
                        self.preparing_spotify = False
                        self.tauon.gui.update += 1
                        return
                    time.sleep(1)

            self.launching_spotify = False
            self.preparing_spotify = False
            self.tauon.gui.update += 1

        else:
            #print(d_id)
            try:
                self.progress_timer.set()
                okay = False

                # Check conditions for a proper transition
                if self.playing:
                    print("already playing")
                    result = self.spotify.playback_currently_playing()
                    if result and result.item and result.is_playing:
                        remain = result.item.duration_ms - result.progress_ms
                        if 1400 < remain < 3500:
                            self.spotify.playback_queue_add("spotify:track:" + id,  device_id=d_id)
                            okay = True
                            time.sleep(remain / 1000)
                            self.progress_timer.set()
                            time.sleep(1)
                            result = self.spotify.playback_currently_playing()
                            if not (result and result.item and result.is_playing):
                                print("A queue transition failed")
                                okay = False

                # Force a transition
                if not okay:
                    print("Force")
                    self.spotify.playback_start_tracks([id], device_id=d_id)

            # except tk.client.decor.error.InternalServerError:
            #     self.tauon.gui.show_message("Spotify server error. Maybe try again later.")
            #     return
            except Exception as e:
                self.launching_spotify = False
                self.preparing_spotify = False
                print(str(e))
                self.tauon.gui.show_message("Spotify error, try again?", str(e), mode="warning")
                return

        # except Exception as e:
        #     self.tauon.gui.show_message("Error. Do you have playback started somewhere?", mode="error")
        self.playing = True
        self.started_once = True
        self.launching_spotify = False
        self.preparing_spotify = False
        self.start_timer.set()
        self.tauon.pctl.playing_time = 0
        self.tauon.pctl.decode_time = 0
        self.tauon.gui.pl_update += 1
        self.tauon.tm.ready_playback()

    def get_library_albums(self, return_list=False):
        self.connect()
        if not self.spotify:
            self.spotify_com = False
            self.tauon.gui.show_message(self.strings.spotify_need_enable)
            return []

        albums = self.spotify.saved_albums()

        playlist = []
        self.update_existing_import_list()
        self.cache_saved_albums.clear()

        pages = self.spotify.all_pages(albums)

        for page in pages:
            for a in page.items:
                self.load_album(a.album, playlist)

                if a.album.external_urls["spotify"] not in self.cache_saved_albums:
                    self.cache_saved_albums.append(a.album.external_urls["spotify"])

        if return_list:
            return playlist

        self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title=self.strings.spotify_albums, playlist=playlist))
        self.tauon.pctl.gen_codes[self.tauon.pl_to_id(len(self.tauon.pctl.multi_playlist) - 1)] = "sal"
        self.spotify_com = False

    def append_track(self, url, playlist_number=None):

        self.connect()
        if not self.spotify:
            return

        if url.startswith("spotify:track:"):
            id = url[14:]
        else:
            url = url.split("?")[0]
            id = url.strip("/").split("/")[-1]

        if playlist_number is None:
            playlist_number = self.tauon.pctl.active_playlist_viewing

        track = self.spotify.track(id)
        tr = self.load_track(track)
        self.tauon.pctl.master_library[tr.index] = tr
        self.tauon.pctl.multi_playlist[playlist_number][2].append(tr.index)
        self.tauon.gui.pl_update += 1

    def append_album(self, url, playlist_number=None, return_list=False):

        self.connect()
        if not self.spotify:
            return []

        if url.startswith("spotify:album:"):
            id = url[14:]
        else:
            url = url.split("?")[0]
            id = url.strip("/").split("/")[-1]

        album = self.spotify.album(id)
        playlist = []
        self.update_existing_import_list()
        self.load_album(album, playlist)

        if return_list:
            return playlist

        if playlist_number is None:
            playlist_number = self.tauon.pctl.active_playlist_viewing

        self.tauon.pctl.multi_playlist[playlist_number][2].extend(playlist)
        self.tauon.gui.pl_update += 1

    def playlist(self, url, return_list=False, silent=False):

        self.connect()
        if not self.spotify:
            return []

        if url.startswith("spotify:playlist:"):
            id = url[17:]
        else:
            url = url.split("?")[0]
            if len(url) != 22:
                id = url.strip("/").split("/")[-1]
            else:
                id = url

        if len(id) != 22:
            print("ID Error")
            if return_list:
                return []
            return

        p = self.spotify.playlist(id)
        playlist = []
        self.update_existing_import_list()
        pages = self.spotify.all_pages(p.tracks)
        for page in pages:
            for item in page.items:
                nt = self.load_track(item.track, include_album_url=True)
                self.tauon.pctl.master_library[nt.index] = nt
                playlist.append(nt.index)

        if return_list:
            return playlist

        title = p.name + " by " + p.owner.display_name
        if p.name == "Discover Weekly" or p.name == "Release Radar":
            #self.tauon.pctl.multi_playlist[len(self.tauon.pctl.multi_playlist) - 1][4] = 1
            title = p.name
        self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title=title, playlist=playlist))

        self.tauon.pctl.gen_codes[self.tauon.pl_to_id(len(self.tauon.pctl.multi_playlist) - 1)] = f"spl\"{id}\""
        if not silent:
            self.tauon.switch_playlist(len(self.tauon.pctl.multi_playlist) - 1)

    def artist_playlist(self, url):
        id = url.strip("/").split("/")[-1]
        artist = self.spotify.artist(id)
        artist_albums = self.spotify.artist_albums(id, limit=50, include_groups=["album"])
        playlist = []
        self.update_existing_import_list()

        for a in artist_albums.items:
            full_album = self.spotify.album(a.id)
            self.load_album(full_album, playlist)

        self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title=artist.name, playlist=playlist))
        self.tauon.switch_playlist(len(self.tauon.pctl.multi_playlist) - 1)
        self.tauon.gui.message_box = False

    def album_playlist(self, url):
        l = self.append_album(url, return_list=True)
        self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title=f"{self.tauon.pctl.g(l[0]).artist} - {self.tauon.pctl.g(l[0]).album}",
                                          playlist=l,
                                          hide_title=0,
                                          ))
        self.tauon.switch_playlist(len(self.tauon.pctl.multi_playlist) - 1)

    def update_existing_import_list(self):
        self.current_imports.clear()
        for tr in self.tauon.pctl.master_library.values():
            if "spotify-track-url" in tr.misc:
                self.current_imports[tr.misc["spotify-track-url"]] = tr

    def create_playlist(self, name):
        print("Create new spotify playlist")
        self.connect()
        if not self.spotify:
            return None

        try:
            user = self.spotify.current_user()
            playlist = self.spotify.playlist_create(user.id, name, True)
            return playlist.id
        except:
            return None

    def upload_playlist(self, playlist_id, track_urls):
        self.connect()
        if not self.spotify:
            return None

        try:
            uris = []
            for url in track_urls:
                uris.append("spotify:track:" + url.strip("/").split("/")[-1])

            self.spotify.playlist_clear(playlist_id)
            time.sleep(0.05)
            with self.spotify.chunked(True):
                self.spotify.playlist_add(playlist_id, uris)
        except:
            self.tauon.gui.show_message("Spotify upload error!", mode="error")

    def load_album(self, album, playlist):
        #a = item
        album_url = album.external_urls["spotify"]
        art_url = album.images[0].url
        album_name = album.name
        total_tracks = album.total_tracks
        date = album.release_date
        album_artist = album.artists[0].name
        id = album.id
        parent = (album_artist + " - " + album_name).strip("- ")

        # print(a.release_date, a.name)
        for track in album.tracks.items:

            pr = None
            if "spotify" in track.external_urls:
                pr = self.current_imports.get(track.external_urls["spotify"])
            if pr:
                new = False
                nt = pr
            else:
                new = True
                nt = self.tauon.TrackClass()
                nt.index = self.tauon.pctl.master_count

            nt.is_network = True
            nt.file_ext = "SPTY"
            nt.url_key = track.id
            if track.artists and "spotify" in track.artists[0].external_urls:
                nt.misc["spotify-artist-url"] = track.artists[0].external_urls["spotify"]
            nt.misc["spotify-album-url"] = album_url
            if "spotify" in track.external_urls:
                nt.misc["spotify-track-url"] = track.external_urls["spotify"]
            nt.artist = track.artists[0].name
            nt.album_artist = album_artist
            nt.date = date
            nt.album = album_name
            nt.disc_number = track.disc_number
            #nt.disc_total =
            nt.length = track.duration_ms / 1000
            nt.title = track.name
            nt.track_number = track.track_number
            nt.track_total = total_tracks
            nt.art_url_key = art_url
            nt.parent_folder_path = parent
            nt.parent_folder_name = parent
            if new:
                self.tauon.pctl.master_count += 1
                self.tauon.pctl.master_library[nt.index] = nt
            playlist.append(nt.index)



    def load_track(self, track, update_master_count=True, include_album_url=False):
        if "spotify" in track.external_urls:
            pr = self.current_imports.get(track.external_urls["spotify"])
        
        else:
            pr = False

        if pr:
            new = False
            nt = pr
        else:
            new = True
            nt = self.tauon.TrackClass()
            nt.index = self.tauon.pctl.master_count

        nt.is_network = True
        nt.file_ext = "SPTY"
        nt.url_key = track.id
        #if new:
        if "spotify" in track.artists[0].external_urls:
            nt.misc["spotify-artist-url"] = track.artists[0].external_urls["spotify"]
        if include_album_url and "spotify-album-url" not in nt.misc:
            if "spotify" in track.album.external_urls:
                nt.misc["spotify-album-url"] = track.album.external_urls["spotify"]
        if "spotify" in track.external_urls:
            nt.misc["spotify-track-url"] = track.external_urls["spotify"]
        if track.artists[0].name:
            nt.artist = track.artists[0].name
        if track.album.artists:
            nt.album_artist = track.album.artists[0].name
        if track.album.release_date:
            nt.date = track.album.release_date
        nt.album = track.album.name
        nt.disc_number = track.disc_number
        nt.length = track.duration_ms / 1000
        nt.title = track.name
        nt.track_number = track.track_number
        # nt.track_total = total_tracks
        if track.album.images:
            nt.art_url_key = track.album.images[0].url
        parent = (nt.album_artist + " - " + nt.album).strip("- ")
        nt.parent_folder_path = parent
        nt.parent_folder_name = parent

        if update_master_count and new:
            self.tauon.pctl.master_count += 1

        return nt

    def like_track(self, tract_object):
        self.connect()
        if not self.spotify:
            return 
        track_url = tract_object.misc.get("spotify-track-url", False)
        if track_url:
            id = track_url.strip("/").split("/")[-1]
            results = self.spotify.saved_tracks_contains([id])
            if not results or results[0] is False:
                self.spotify.saved_tracks_add([id])
                tract_object.misc["spotify-liked"] = True
                self.tauon.gui.show_message(self.strings.spotify_like_added, mode="done")
                return
            self.tauon.gui.show_message(self.strings.spotify_already_liked)
            return

    def unlike_track(self, tract_object):
        self.connect()
        if not self.spotify:
            return
        track_url = tract_object.misc.get("spotify-track-url", False)
        if track_url:
            id = track_url.strip("/").split("/")[-1]
            results = self.spotify.saved_tracks_contains([id])
            if not results or results[0] is True:
                self.spotify.saved_tracks_delete([id])
                tract_object.misc.pop("spotify-liked", None)
                self.tauon.gui.show_message(self.strings.spotify_un_liked, mode="done")
                return
            self.tauon.gui.show_message(self.strings.spotify_already_un_liked)
            return

    def get_library_likes(self, return_list=False):
        self.connect()
        if not self.spotify:
            self.spotify_com = False
            self.tauon.gui.show_message(self.strings.spotify_need_enable)
            return []

        self.update_existing_import_list()
        tracks = self.spotify.saved_tracks()

        playlist = []

        for tr in self.tauon.pctl.master_library.values():
            tr.misc.pop("spotify-liked", None)

        pages = self.spotify.all_pages(tracks)
        for page in pages:
            for item in page.items:
                nt = self.load_track(item.track)
                self.tauon.pctl.master_library[nt.index] = nt
                playlist.append(nt.index)
                nt.misc["spotify-liked"] = True

        if return_list:
            return playlist

        for p in self.tauon.pctl.multi_playlist:
            if p[0] == self.tauon.strings.spotify_likes:
                p[2][:] = playlist[:]
                self.spotify_com = False
                return

        self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title=self.tauon.strings.spotify_likes, playlist=playlist))
        self.tauon.pctl.gen_codes[self.tauon.pl_to_id(len(self.tauon.pctl.multi_playlist) - 1)] = "slt"
        self.spotify_com = False

    def monitor(self):
        tr = self.tauon.pctl.playing_object()
        result = None

        # Detect if playback has resumed
        if self.playing and self.paused:
            result = self.spotify.playback_currently_playing()
            if result and result.is_playing:
                self.paused = False
                self.progress_timer.set()
                self.tauon.pctl.playing_state = 1
                self.tauon.gui.update += 1

        # Detect is playback has been modified
        elif self.playing and self.start_timer.get() > 4 and self.tauon.pctl.playing_time + 5 < tr.length:

            if not result:
                result = self.spotify.playback_currently_playing()

            # Playback has been stopped?
            if (result is None or result.item is None) or tr is None:
                self.playing = False
                self.tauon.pctl.stop()
                return
            # Playback has been paused?
            elif tr and result and not result.is_playing:
                self.paused = True
                self.tauon.pctl.playing_state = 2
                self.tauon.gui.update += 1
                return
            # Something else is now playing? If so, switch into coast mode
            if result.item.name != tr.title:
                self.tauon.pctl.playing_state = 3
                self.playing = False
                self.coasting = True
                self.coast_update(result)
                self.tauon.gui.pl_update += 2
                return

            p = result.progress_ms
            if p is not None:
                #if abs(self.tauon.pctl.playing_time - (p / 1000)) > 0.4:
                    # print("DESYNC")
                    # print(abs(self.tauon.pctl.playing_time - (p / 1000)))
                self.tauon.pctl.playing_time = p / 1000
                self.tauon.pctl.decode_time = self.tauon.pctl.playing_time
                # else:
                #     print("SYNCED")

    def update(self, start=False):

        if self.playing:
            self.coasting = False
            return

        self.connect()
        if not self.spotify:
            return

        result = self.spotify.playback_currently_playing()
        self.tauon.tm.ready_playback()

        if self.playing or (not self.coasting and not start):
            return

        try:
            self.tauon.tm.player_lock.release()
        except:
            pass

        if result is None or result.is_playing is False:
            if self.coasting:

                if self.tauon.pctl.radio_image_bin:
                    self.loaded_art = ""
                    self.tauon.pctl.radio_image_bin.close()
                    self.tauon.pctl.radio_image_bin = None
                    self.tauon.dummy_track.artist = ""
                    self.tauon.dummy_track.date = ""
                    self.tauon.dummy_track.title = ""
                    self.tauon.dummy_track.album = ""
                    self.tauon.dummy_track.art_url_key = ""
                    self.tauon.gui.clear_image_cache_next = True
                    self.paused = True

            else:
                self.tauon.gui.show_message(self.strings.spotify_not_playing)
            return

        self.coasting = True
        self.started_once = True
        self.tauon.pctl.playing_state = 3

        if result.is_playing:
            self.paused = False
        else:
            self.paused = True

        self.coast_update(result)

    def append_playing(self, playlist_number):
        if not self.coasting:
            return
        tr = self.tauon.pctl.playing_object()
        if tr and "spotify-track-url" in tr.misc:
            self.append_track(tr.misc["spotify-track-url"], playlist_number=playlist_number)

    def coast_update(self, result):

        if result is None or result.item is None:
            print("Spotify returned unknown")
            return

        self.tauon.dummy_track.artist = result.item.artists[0].name
        self.tauon.dummy_track.title = result.item.name
        self.tauon.dummy_track.album = result.item.album.name
        self.tauon.dummy_track.date = result.item.album.release_date
        self.tauon.dummy_track.file_ext = "Spotify"

        self.progress_timer.set()
        self.update_timer.set()

        d = result.item.duration_ms
        if d is not None:
            self.tauon.pctl.playing_length = d / 1000

        p = result.progress_ms
        if p is not None:
            self.tauon.pctl.playing_time = p / 1000

        self.tauon.pctl.decode_time = self.tauon.pctl.playing_time

        art_url = result.item.album.images[0].url
        self.tauon.dummy_track.url_key = result.item.id
        self.tauon.dummy_track.misc["spotify-album-url"] = result.item.album.external_urls["spotify"]
        self.tauon.dummy_track.misc["spotify-track-url"] = result.item.external_urls["spotify"]

        if art_url and self.loaded_art != art_url:
            self.loaded_art = art_url
            art_response = requests.get(art_url)
            if self.tauon.pctl.radio_image_bin:
                self.tauon.pctl.radio_image_bin.close()
                self.tauon.pctl.radio_image_bin = None
            self.tauon.pctl.radio_image_bin = io.BytesIO(art_response.content)
            self.tauon.pctl.radio_image_bin.seek(0)
            self.tauon.dummy_track.art_url_key = "ok"
            self.tauon.gui.clear_image_cache_next = True

        self.tauon.gui.update += 2
        self.tauon.gui.pl_update += 1

    def import_context(self):
        self.connect()
        if not self.spotify:
            return
        result = self.spotify.playback_currently_playing()
        if not result or not result.context:
            self.tauon.gui.show_message("No Spotify context found")
            return

        if result.context.type == "playlist":
                self.playlist(result.context.uri)

        if result.context.type == "album":
                self.album_playlist(result.context.uri)

        if result.context.type == "artist":
                self.artist_playlist(result.context.uri)

        self.tauon.gui.pl_update += 1


