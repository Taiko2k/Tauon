
import tidalapi
from tidalapi import Session
from tidalapi import Quality
import webbrowser
from pathlib import Path

class Tidal:

    def __init__(self, tauon):
        self.tauon = tauon
        self.session = None

    def login1(self):
        print("LOGIN 1")
        session = tidalapi.Session()
        login_url = session.pkce_login_url()
        webbrowser.open(login_url, new=2, autoraise=True)
        self.session = session

    def login2(self):
        print("LOGIN 2")
        # https://tidal.com/android/login/auth?code=eyVyPty.WiGdw-abQ&state=na&appMode=android


    def test(self):
        session = self.session
        # Override the required playback quality, if necessary
        # Note: Set the quality according to your subscription.
        # Low: Quality.low_96k          (m4a 96k)
        # Normal: Quality.low_320k      (m4a 320k)
        # HiFi: Quality.high_lossless   (FLAC)
        # HiFi+ Quality.hi_res          (FLAC MQA)
        # HiFi+ Quality.hi_res_lossless (FLAC HI_RES)
        session.audio_quality = Quality.high_lossless
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
                # with open("{}_{}.mpd".format(album_id, track.id), "w") as my_file:
                #    my_file.write(mpd)
                # with open("{}_{}.m3u8".format(album_id, track.id), "w") as my_file:
                #    my_file.write(hls)
            elif stream.is_BTS:
                print("BTS!")
                # Direct URL (m4a or flac) is available for Quality < HI_RES_LOSSLESS
                url = manifest.get_urls()
                print(f"URL = {url}")
            break