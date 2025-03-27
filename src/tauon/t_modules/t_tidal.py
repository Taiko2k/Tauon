"""Tauon Music Box - Tidal streaming module"""
from __future__ import annotations

import json
import logging
import os
import webbrowser
from datetime import datetime, timezone
from typing import TYPE_CHECKING

allow_tidal = False
try:
	import tidalapi
	from tidalapi import Quality, Session
	allow_tidal = True
except ModuleNotFoundError:
	logging.warning("Unable to import tidalapi, Tidal support will be disabled.")
except Exception:
	logging.exception("Tidalapi not found")

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Tauon, TrackClass
class Tidal:

	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.session = None
		self.save_path = str(tauon.cache_directory / "tidal.json")
		self.login_stage = 0
		self.import_cache = {}

	def logout(self) -> None:
		self.session = None
		self.login_stage = 0
		if os.path.isfile(self.save_path):
			os.remove(self.save_path)

	def login1(self) -> None:
		if not allow_tidal:
			self.tauon.show_message(_("Tidalapi package not loaded"))
			return
		logging.info("LOGIN 1")
		session = tidalapi.Session()
		#session.config.pkce_uri_redirect = f"http://localhost:7811/tidalredir"
		login_url = session.pkce_login_url()
		webbrowser.open(login_url, new=2, autoraise=True)
		self.session = session
		self.login_stage = 2

	def login2(self, url: str) -> None:
		logging.info("LOGIN 2")
		if not allow_tidal:
			return
		auth_token = self.session.pkce_get_auth_token(url)
		self.session.process_auth_token(auth_token, is_pkce_token=True)
		logging.info("login2 done")
		self.save_session()
		self.login_stage = 0
		# https://tidal.com/android/login/auth?code=eyVyPty.WiGdw-abQ&state=na&appMode=android

	def try_load(self) -> None:
		if not allow_tidal:
			self.tauon.show_message(_("Tidalapi package not loaded"))
			return
		if not self.session and os.path.isfile(self.save_path):
			with open(self.save_path) as f:
				session_data = json.load(f)
			session = tidalapi.Session()

			expiry_time = None
			if session_data["expiry_time"]:
				expiry_time = datetime.fromisoformat(session_data["expiry_time"])
				# Ensure the datetime is timezone-aware
				if expiry_time.tzinfo is None:
					expiry_time = expiry_time.replace(tzinfo=timezone.utc)

			success = session.load_oauth_session(
				session_data["token_type"],
				session_data["access_token"],
				session_data["refresh_token"],
				expiry_time,
				session_data["is_pkce"],
			)
			if success:
				self.session = session
				self.save_session()
				logging.info("loaded TIDAL login")
			else:
				logging.error("Failed to load TIDAL login")
				self.tauon.show_message(_("Failed to load TIDAL login, please try log in again"))
				os.remove(self.save_path)

	def save_session(self) -> None:
		if self.session:
			session = self.session
			session_data = {
				"token_type": session.token_type,
				"access_token": session.access_token,
				"refresh_token": session.refresh_token,
				"expiry_time": session.expiry_time.isoformat() if session.expiry_time else None,
				"is_pkce": session.is_pkce,
			}
			with open(self.save_path, "w") as f:
				json.dump(session_data, f)

	def resolve_stream(self, tr: TrackClass) -> list[str] | None:
		track_id = tr.url_key
		self.try_load()
		if not self.session:
			logging.info("Tidal: not logged in")
			return None

		if self.tauon.prefs.tidal_quality == 2:
			logging.info("TRY 24 bit flac")
			self.session.audio_quality = Quality.hi_res_lossless
			try:
				result = self.resolve_stream2(tr)
				if result:
					return result
			except Exception:
				logging.exception("Failed to resolve stream")

		if self.tauon.prefs.tidal_quality == 1:
			logging.info("TRY 16bit flac")
			self.session.audio_quality = Quality.high_lossless
			try:
				result = self.resolve_stream2(tr)
				if result:
					return result
			except Exception:
				logging.exception("Failed to resolve stream")

		logging.info("TRY LOW")
		self.session.audio_quality = Quality.low_320k
		try:
			result = self.resolve_stream2(tr)
			if result:
				return result
		except Exception:
				logging.exception("Failed to resolve stream")

	def resolve_stream2(self, tr: TrackClass) -> list[str] | None:
		track_id = tr.url_key
		track = self.session.track(track_id)
		logging.info(f"{track.id}: '{track.name}' by '{track.artist.name}'")
		stream = track.get_stream()
		logging.info(f"MimeType:{stream.manifest_mime_type}")

		manifest = stream.get_stream_manifest()
		audio_resolution = stream.get_audio_resolution()

		logging.info(f"track:{track.id}, (quality:{stream.audio_quality}, codec:{manifest.get_codecs()}, {audio_resolution[0]}bit/{audio_resolution[1]}Hz)")
		tr.misc["container"] = manifest.get_codecs().upper()
		tr.samplerate = str(audio_resolution[1])
		tr.bit_depth = audio_resolution[0]
		if stream.is_MPD:
			logging.info("MPD!")
			return manifest.get_urls()
		if stream.is_BTS:
			logging.info("BTS!")
			return manifest.get_urls()

		return None

	def build_cache(self) -> None:
		for id, nt in self.tauon.pctl.master_library.items():
			if nt.url_key and nt.file_ext == "TIDAL":
				self.import_cache[nt.url_key] = nt

	def new_track(self, track: TrackClass) -> TrackClass:

		new = False
		nt = self.import_cache.get(track.id)

		if not nt:
			new = True
			nt = self.tauon.TrackClass()
			nt.index = self.tauon.pctl.master_count

		nt.is_network = True
		nt.file_ext = "TIDAL"
		nt.url_key = str(track.id)

		nt.track_number = str(track.track_num)
		nt.title = track.name
		nt.artist = track.artist.name
		nt.album = track.album.name
		nt.length = track.duration
		nt.album_artist = track.album.artist.name
		nt.misc["tidal_album"] = track.album.id

		parent = (nt.album_artist + " - " + nt.album).strip("- ")
		nt.parent_folder_path = parent
		nt.parent_folder_name = parent

		nt.art_url_key = ""
		if track.album.cover:
			nt.art_url_key = track.album.image(dimensions=1280)

		if new:
			self.tauon.pctl.master_count += 1
			self.tauon.pctl.master_library[nt.index] = nt

		return nt

	def track(self, id: int) -> None:
		self.try_load()
		if not self.session:
			return []
		self.build_cache()

		t = self.session.track(id)
		nt = self.new_track(t)
		self.tauon.pctl.multi_playlist[self.tauon.pctl.active_playlist_viewing].playlist_ids.append(nt.index)
		self.tauon.gui.pl_update += 1

	def fav_albums(self, return_list: bool = False) -> list[TrackClass] | None:

		self.try_load()
		if not self.session:
			return []
		self.build_cache()

		try:
			f = tidalapi.Favorites(self.session, self.session.user.id)
		except Exception:
			logging.exception("Error getting tidal user favorites")
			return []

		playlist = []
		for album in f.albums():
			for track in album.tracks():
				nt = self.new_track(track)
				playlist.append(nt.index)

		if return_list:
			return playlist

		self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title="TIDAL Albums", playlist_ids=playlist))
		self.tauon.pctl.gen_codes[self.tauon.pl_to_id(len(self.tauon.pctl.multi_playlist) - 1)] = "tfa"
		self.tauon.show_message("Playlist load complete", mode="done")

	def fav_tracks(self, return_list: bool = False) -> list[TrackClass] | None:

		self.try_load()
		if not self.session:
			return []
		self.build_cache()

		try:
			f = tidalapi.Favorites(self.session, self.session.user.id)
		except Exception:
			logging.exception("Error getting tidal user favorites")
			return []

		playlist = []
		for track in f.tracks():
			nt = self.new_track(track)
			playlist.append(nt.index)

		if return_list:
			return playlist

		self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title="TIDAL Tracks", playlist_ids=playlist))
		self.tauon.pctl.gen_codes[self.tauon.pl_to_id(len(self.tauon.pctl.multi_playlist) - 1)] = "tft"
		self.tauon.show_message("Playlist load complete", mode="done")

	def playlist(self, id: int, return_list: bool = False) -> list[TrackClass] | None:

		self.try_load()
		if not self.session:
			return []
		self.build_cache()

		try:
			p = self.session.playlist(id)
		except Exception:
			logging.exception("Error getting tidal playlist")
			return []

		playlist = []
		for track in p.tracks():
			nt = self.new_track(track)
			playlist.append(nt.index)

		if return_list:
			return playlist

		self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title=p.name, playlist_ids=playlist))
		self.tauon.pctl.gen_codes[self.tauon.pl_to_id(len(self.tauon.pctl.multi_playlist) - 1)] = f"tpl\"{id}\""

	def mix(self, id: int, return_list: bool = False) -> list[TrackClass] | None:

		self.try_load()
		if not self.session:
			return []
		self.build_cache()

		try:
			p = self.session.mix(id)
		except Exception:
			logging.exception("Error getting tidal mix")
			return []

		playlist = []
		for item in p.items():
			if item.type in ("track", None):  # tracks are None, api bug?
				nt = self.new_track(item)
				playlist.append(nt.index)

		if return_list:
			return playlist

		self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title=p.title, playlist_ids=playlist))
		self.tauon.pctl.gen_codes[self.tauon.pl_to_id(len(self.tauon.pctl.multi_playlist) - 1)] = f"tmix\"{id}\""

	def artist(self, id: int, return_list: bool = False) -> list[TrackClass] | None:

		self.try_load()
		if not self.session:
			return []
		self.build_cache()

		try:
			a = self.session.artist(id)
		except Exception:
			logging.exception("Error getting tidal artist")
			return []

		playlist = []

		for album in a.get_albums():
			for track in album.tracks():
				nt = self.new_track(track)
				playlist.append(nt.index)

		if return_list:
			return playlist

		self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title=a.name, playlist_ids=playlist))
		self.tauon.pctl.gen_codes[self.tauon.pl_to_id(len(self.tauon.pctl.multi_playlist) - 1)] = f"tar\"{id}\""

	def append_album(self, id: int) -> None:
		self.try_load()
		if not self.session:
			return

		self.build_cache()

		album = self.session.album(id)
		tracks = album.tracks()

		for track in tracks:
			logging.info(f"{track.id}: '{track.name}' by '{track.artist.name}'")

			nt = self.new_track(track)
			self.tauon.pctl.multi_playlist[self.tauon.pctl.active_playlist_viewing].playlist_ids.append(nt.index)
			self.tauon.gui.pl_update += 1

	# def test(self):
	#	 logging.info("Test Tidal")
	#	 self.try_load()
	#	 if not self.session:
	#		 logging.info("Tidal: not logged in")
	#		 return
	#
	#	 session = self.session
	#	 # Override the required playback quality, if necessary
	#	 # Note: Set the quality according to your subscription.
	#	 # Low: Quality.low_96k          (m4a 96k)
	#	 # Normal: Quality.low_320k      (m4a 320k)
	#	 # HiFi: Quality.high_lossless   (FLAC)
	#	 # HiFi+ Quality.hi_res          (FLAC MQA)
	#	 # HiFi+ Quality.hi_res_lossless (FLAC HI_RES)
	#	 session.audio_quality = Quality.high_lossless
	#	 session.audio_quality = Quality.low_320k
	#	 # album_id = "249593867"  # Alice In Chains / We Die Young (Max quality: HI_RES MHA1 SONY360)
	#	 # album_id = "77640617"   # U2 / Achtung Baby              (Max quality: HI_RES MQA, 16bit/44100Hz)
	#	 # album_id = "110827651"  # The Black Keys / Let's Rock    (Max quality: LOSSLESS FLAC, 24bit/48000Hz)
	#	 album_id = "77646169"  # Beck / Sea Change               (Max quality: HI_RES_LOSSLESS FLAC, 24bit/192000Hz)
	#	 album = session.album(album_id)
	#	 res = album.get_audio_resolution()
	#	 tracks = album.tracks()
	#	 # list album tracks
	#	 for track in tracks:
	#		 logging.info("{}: '{}' by '{}'".format(track.id, track.name, track.artist.name))
	#		 stream = track.get_stream()
	#		 logging.info("MimeType:{}".format(stream.manifest_mime_type))
	#
	#		 manifest = stream.get_stream_manifest()
	#		 audio_resolution = stream.get_audio_resolution()
	#
	#		 logging.info("track:{}, (quality:{}, codec:{}, {}bit/{}Hz)".format(track.id,
	#																	 stream.audio_quality,
	#																	 manifest.get_codecs(),
	#																	 audio_resolution[0],
	#																	 audio_resolution[1]))
	#		 if stream.is_MPD:
	#			 logging.info("MPD!")
	#			 # HI_RES_LOSSLESS quality supported when using MPEG-DASH stream (PKCE only!)
	#			 # 1. Export as MPD manifest
	#			 mpd = stream.get_manifest_data()
	#			 # 2. Export as HLS m3u8 playlist
	#			 hls = manifest.get_hls()
	#			 logging.info(hls)
	#			 # with open("{}_{}.mpd".format(album_id, track.id), "w") as my_file:
	#			 #	my_file.write(mpd)
	#			 # with open("{}_{}.m3u8".format(album_id, track.id), "w") as my_file:
	#			 #	my_file.write(hls)
	#			 urls = manifest.get_urls()
	#			 if urls:
	#				 f = io.BytesIO()
	#				 i = 0
	#				 for url in urls:
	#					 i += 1
	#					 logging.info(i, end=",")
	#					 response = requests.get(url)
	#					 if response.status_code == 200:
	#						 f.write(response.content)
	#					 else:
	#						 logging.error(f"ERROR CODE: {response.status_code}")
	#				 f.seek(0)
	#				 with open("test", 'wb') as a:
	#					 a.write(f.read())
	#				 logging.info("done")
	#
	#		 if stream.is_BTS:
	#			 logging.info("BTS!")
	#			 # Direct URL (m4a or flac) is available for Quality < HI_RES_LOSSLESS
	#			 url = manifest.get_urls()
	#			 logging.info(f"URL = {url}")
	#		 for url in manifest.get_urls():
	#			 logging.info(url)
	#		 break
