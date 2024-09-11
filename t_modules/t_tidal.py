import io
from datetime import datetime, timezone

import requests
import tidalapi
from tidalapi import Session
from tidalapi import Quality
import webbrowser
from pathlib import Path
import os
import json

class Tidal:

    def __init__(self, tauon):
        self.tauon = tauon
        self.session = None
        self.save_path = os.path.join(tauon.cache_directory, "tidal.json")
        self.login_stage = 0

    def logout(self):
        self.session = None
        self.login_stage = 0
        if os.path.isfile(self.save_path):
            os.remove(self.save_path)
    def login1(self):
        print("LOGIN 1")
        session = tidalapi.Session()
        #session.config.pkce_uri_redirect = f"http://localhost:7811/tidalredir"
        login_url = session.pkce_login_url()
        webbrowser.open(login_url, new=2, autoraise=True)
        self.session = session
        self.login_stage = 2

    def login2(self, url):
        print("LOGIN 2")
        auth_token = self.session.pkce_get_auth_token(url)
        self.session.process_auth_token(auth_token, is_pkce_token=True)
        print("login2 done")
        self.save_session()
        self.login_stage = 0
        # https://tidal.com/android/login/auth?code=eyVyPty.WiGdw-abQ&state=na&appMode=android

    def try_load(self):
        if not self.session and os.path.isfile(self.save_path):
            with open(self.save_path, 'r') as f:
                session_data = json.load(f)
            session = tidalapi.Session()

            expiry_time = None
            if session_data['expiry_time']:
                expiry_time = datetime.fromisoformat(session_data['expiry_time'])
                # Ensure the datetime is timezone-aware
                if expiry_time.tzinfo is None:
                    expiry_time = expiry_time.replace(tzinfo=timezone.utc)

            success = session.load_oauth_session(
                session_data['token_type'],
                session_data['access_token'],
                session_data['refresh_token'],
                expiry_time,
                session_data['is_pkce']
            )
            if success:
                self.session = session
                self.save_session()
                print("loaded TIDAL login")
            else:
                print("Failed to load TIDAL login")
                self.tauon.show_message("Failed to load TIDAL login, please try log in again")
                os.remove(self.save_path)

    def save_session(self):
        if self.session:
            session = self.session
            session_data = {
                "token_type": session.token_type,
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "expiry_time": session.expiry_time.isoformat() if session.expiry_time else None,
                "is_pkce": session.is_pkce
            }
            with open(self.save_path, 'w') as f:
                json.dump(session_data, f)

    def test(self):
        print("Test Tidal")
        self.try_load()
        if not self.session:
            print("Tidal: not logged in")
            return

        session = self.session
        # Override the required playback quality, if necessary
        # Note: Set the quality according to your subscription.
        # Low: Quality.low_96k          (m4a 96k)
        # Normal: Quality.low_320k      (m4a 320k)
        # HiFi: Quality.high_lossless   (FLAC)
        # HiFi+ Quality.hi_res          (FLAC MQA)
        # HiFi+ Quality.hi_res_lossless (FLAC HI_RES)
        session.audio_quality = Quality.high_lossless
        session.audio_quality = Quality.low_320k
        # album_id = "249593867"  # Alice In Chains / We Die Young (Max quality: HI_RES MHA1 SONY360)
        # album_id = "77640617"   # U2 / Achtung Baby              (Max quality: HI_RES MQA, 16bit/44100Hz)
        # album_id = "110827651"  # The Black Keys / Let's Rock    (Max quality: LOSSLESS FLAC, 24bit/48000Hz)
        album_id = "77646169"  # Beck / Sea Change               (Max quality: HI_RES_LOSSLESS FLAC, 24bit/192000Hz)
        album = session.album(album_id)
        res = album.get_audio_resolution()
        tracks = album.tracks()
        # list album tracks
        for track in tracks:
            print("{}: '{}' by '{}'".format(track.id, track.name, track.artist.name))
            stream = track.get_stream()
            print("MimeType:{}".format(stream.manifest_mime_type))

            manifest = stream.get_stream_manifest()
            audio_resolution = stream.get_audio_resolution()

            print("track:{}, (quality:{}, codec:{}, {}bit/{}Hz)".format(track.id,
                                                                        stream.audio_quality,
                                                                        manifest.get_codecs(),
                                                                        audio_resolution[0],
                                                                        audio_resolution[1]))
            if stream.is_MPD:
                print("MPD!")
                # HI_RES_LOSSLESS quality supported when using MPEG-DASH stream (PKCE only!)
                # 1. Export as MPD manifest
                mpd = stream.get_manifest_data()
                # 2. Export as HLS m3u8 playlist
                hls = manifest.get_hls()
                print(hls)
                # with open("{}_{}.mpd".format(album_id, track.id), "w") as my_file:
                #    my_file.write(mpd)
                # with open("{}_{}.m3u8".format(album_id, track.id), "w") as my_file:
                #    my_file.write(hls)
                urls = manifest.get_urls()
                if urls:
                    f = io.BytesIO()
                    i = 0
                    for url in urls:
                        i += 1
                        print(i, end=",")
                        response = requests.get(url)
                        if response.status_code == 200:
                            f.write(response.content)
                        else:
                            print(f"ERROR CODE: {response.status_code}")
                    f.seek(0)
                    with open("test", 'wb') as a:
                        a.write(f.read())
                    print("done")

            if stream.is_BTS:
                print("BTS!")
                # Direct URL (m4a or flac) is available for Quality < HI_RES_LOSSLESS
                url = manifest.get_urls()
                print(f"URL = {url}")
            for url in manifest.get_urls():
                print(url)
            break