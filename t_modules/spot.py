
import os
import tekore as tk
import pickle
import requests
import io
import webbrowser

from t_modules.t_extra import Timer

class SpotCtl:

    def __init__(self, tauon):
        self.tauon = tauon

        self.start_timer = Timer()
        self.status = 0
        self.spotify = None
        self.loaded_art = ""
        self.playing = False
        self.coasting = False
        self.paused = False
        self.token = None
        self.cred = None
        self.redirect_uri = f"http://localhost:7811/spotredir"

        self.progress_timer = Timer()
        self.update_timer = Timer()

        self.token_path = os.path.join(self.tauon.user_directory, "spot-r-token")

    def prep_cred(self):
        self.cred = tk.auth.RefreshingCredentials(client_id=self.tauon.prefs.spot_client,
                                    client_secret=self.tauon.prefs.spot_secret,
                                    redirect_uri=self.redirect_uri)

    def connect(self):
        if self.cred is None:
            self.prep_cred()
        if self.spotify is None:
            if self.token is None:
                if os.path.isfile(self.token_path):
                    f = open(self.token_path, "rb")
                    self.token = pickle.load(f)
                    f.close()
                    print("LOADED TOKEN FROM FILE")
                else:
                    print("NO TOKEN!")
                    return

            print("INIT SPOTIFY")
            self.spotify = tk.Spotify(self.token)

    def paste_code(self, code):
        if self.cred is None:
            self.prep_cred()
        self.token = self.cred.request_user_token(code)
        print("Paste")
        pickle.dump(self.token, open(self.token_path, "wb"))

    def auth(self):
        if self.cred is None:
            self.prep_cred()
        print("AUTH")
        url = self.cred.user_authorisation_url(scope="user-read-playback-position streaming user-modify-playback-state user-library-modify user-library-read user-read-currently-playing user-read-playback-state")
        webbrowser.open(url, new=2, autoraise=True)

    def control(self, command, param=None):

        if command == "pause" and self.coasting and not self.paused:
            self.spotify.playback_pause()
            self.paused = True
        if command == "pause" and self.playing:
            self.spotify.playback_pause()
            self.playing = False
        if command == "resume" and self.coasting and self.paused:
            self.spotify.playback_resume()
            self.paused = False
        if command == "volume":
            self.spotify.playback_volume(param)
        if command == "seek":
            self.spotify.playback_seek(param)

    def get_album_url_from_local(self, track_object):

        if "spotify-album-url" in track_object.misc:
            return track_object.misc["spotify-album-url"]

        self.connect()
        if not self.spotify:
            return None

        results = self.spotify.search(track_object.artist + " " + track_object.album, types=('album',), limit=1)
        print(results)
        for album in results[0].items:
            print(album.external_urls["spotify"])
            return album.external_urls["spotify"]

        return None

    def search(self, text):
        self.connect()
        if not self.spotify:
            return
        results = self.spotify.search(text,
                                      types=('track', 'album',),
                                      limit=9
                                      )
        print(results)
        finds = []

        if results[0]:
            for album in results[0].items[0:9]:
                finds.append((11, (album.name, album.artists[0].name), album.external_urls["spotify"], 0, 0))

        print(finds)
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
            print(dir(results))
            print(results)

    def prime_device(self):
        self.connect()
        if not self.spotify:
            return

        devices = self.spotify.playback_devices()
        if not devices:
            return False
        for d in devices:
            if d.is_active:
                return None
        for d in devices:
            if not d.is_restricted:
                return d.id
        return None

    def play_target(self, id):

        self.connect()
        if not self.spotify:
            return

        d_id = self.prime_device()
        if d_id is False:
            return

        #if self.tauon.pctl.playing_state == 1 and self.playing and self.tauon.pctl.playing_time
        #try:
        self.spotify.playback_start_tracks([id], device_id=d_id)
        # except Exception as e:
        #     self.tauon.gui.show_message("Error. Do you have playback started somewhere?", mode="error")
        self.playing = True
        self.progress_timer.set()
        self.start_timer.set()

    def get_library_albums(self):
        self.connect()
        if not self.spotify:
            return

        print("LIST SAVED ALBUMS")
        albums = self.spotify.saved_albums()

        playlist = []

        for a in albums.items:
            self.load_album(a.album, playlist)

        self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title="Spotify Albums", playlist=playlist))

    def append_album(self, url):
        self.connect()
        if not self.spotify:
            return

        id = url[31:]
        album = self.spotify.album(id)
        playlist = []
        self.load_album(album, playlist)

        self.tauon.pctl.multi_playlist[self.tauon.pctl.active_playlist_viewing][2].extend(playlist)
        self.tauon.gui.pl_update += 1

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
            nt = self.tauon.TrackClass()

            nt.index = self.tauon.pctl.master_count
            nt.is_network = True
            nt.file_ext = "SPTY"
            print("TRACK -------------")
            nt.url_key = track.id
            nt.misc["spotify-artist-url"] = track.artists[0].external_urls["spotify"]
            nt.misc["spotify-album-url"] = album_url
            nt.misc["spotify-track-url"] = track.external_urls["spotify"]
            nt.artist = track.artists[0].name
            nt.album_artist = album_artist
            nt.date = date
            nt.album = album_name
            nt.disc_total = track.disc_number
            nt.length = track.duration_ms / 1000
            #print(track.images[0]["url])
            nt.title = track.name
            nt.track_number = track.track_number
            nt.track_total = total_tracks
            nt.art_url_key = art_url
            nt.parent_folder_path = parent
            nt.parent_folder_name = parent

            self.tauon.pctl.master_library[nt.index] = nt
            playlist.append(nt.index)
            self.tauon.pctl.master_count += 1




    def get_library_likes(self):
        self.connect()
        if not self.spotify:
            return

        print("LIST SAVED ALBUMS")
        tracks = self.spotify.saved_tracks()

        playlist = []

        for item in tracks.items:
            track = item.track
            nt = self.tauon.TrackClass()
            print(track)
            nt.index = self.tauon.pctl.master_count
            nt.is_network = True
            nt.file_ext = "SPTY"
            print("TRACK -------------")
            nt.url_key = track.id
            nt.misc["spotify-artist-url"] = track.artists[0].external_urls["spotify"]
            #nt.misc["spotify-album-url"] = album_url
            nt.misc["spotify-track-url"] = track.external_urls["spotify"]
            nt.artist = track.artists[0].name
            nt.album_artist = track.album.artists[0].name
            nt.date = track.album.release_date
            nt.album = track.album.name
            nt.disc_total = track.disc_number
            nt.length = track.duration_ms / 1000
            #print(track.images[0]["url])
            nt.title = track.name
            nt.track_number = track.track_number
            #nt.track_total = total_tracks
            nt.art_url_key = track.album.images[0].url
            parent = (nt.album_artist + " - " + nt.album).strip("- ")
            nt.parent_folder_path = parent
            nt.parent_folder_name = parent

            self.tauon.pctl.master_library[nt.index] = nt
            playlist.append(nt.index)
            self.tauon.pctl.master_count += 1

        self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title="Spotify Likes", playlist=playlist))


    def monitor(self):
        if self.playing:
            result = self.spotify.playback_currently_playing()
            tr = self.tauon.pctl.playing_object()
            if result is None:
                print("DETACH STOP")
                self.tauon.pctl.stop()
            if tr is None:
                return
            if result.item.name != tr.title:
                self.tauon.pctl.playing_state = 3
                self.playing = False
                self.coasting = True
                self.coast_update(result)
                self.tauon.gui.pl_update += 2
                return

            p = result.progress_ms
            if p is not None:
                self.tauon.pctl.playing_time = p / 1000
            self.tauon.pctl.decode_time = self.tauon.pctl.playing_time

    def update(self):
        self.connect()
        if not self.spotify:
            return

        print("UPDATE SPOT PLAYBACK")
        result = self.spotify.playback_currently_playing()

        if result is None:
            print("UPDATE STOP")
            self.tauon.pctl.stop()
            self.coasting = False
            return

        self.coasting = True
        self.tauon.pctl.playing_state = 3

        if result.is_playing:
            self.paused = False
        else:
            self.paused = True

        self.coast_update(result)

    def coast_update(self, result):

        self.tauon.dummy_track.artist = result.item.artists[0].name
        self.tauon.dummy_track.title = result.item.name
        self.tauon.dummy_track.album = result.item.album.name
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

