"""Tauon Music Box - Phazor audio backend module"""

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

from __future__ import annotations

import ctypes
import logging
import sys
from http import HTTPStatus

if sys.platform == "win32":
	from ctypes import WINFUNCTYPE
import hashlib
import importlib.machinery
import math
import os.path
import shutil
import subprocess
import sysconfig
import threading
import time
from ctypes import CFUNCTYPE, POINTER, c_char, c_char_p, c_int, c_void_p, cast
from pathlib import Path
from typing import TYPE_CHECKING

import requests
from requests.models import PreparedRequest

from tauon.t_modules.t_extra import Timer, shooter, tmp_cache_dir

if TYPE_CHECKING:
	from tauon.t_modules.t_main import PlayerCtl, Tauon, TrackClass

class LibreSpot:
	def __init__(self, tauon: Tauon) -> None:
		self.tauon           = tauon
		self.aud             = tauon.aud
		self.gui             = tauon.gui
		self.msys            = tauon.msys
		self.pctl            = tauon.pctl
		self.prefs           = tauon.prefs
		self.spot_ctl        = tauon.spot_ctl
		self.librespot_p     = tauon.librespot_p
		self.show_message    = tauon.show_message
		self.cache_directory = tauon.cache_directory
		self.running    = False
		self.flush      = False

	def go(self, force: bool = False) -> int:
		self.aud.config_set_feed_samplerate(44100)
		self.aud.config_set_min_buffer(1000)
		if not shutil.which("librespot"):
			self.show_message(_("SPP: Error, librespot not found"))
			return 1
		# if not prefs.spot_username or not prefs.spot_password:
		#	 self.show_message("Please enter your spotify username and password in settings")
		#	 return 1
		if self.librespot_p:
			if force:
				logging.info("SPP: Force restart librespot")
				self.end()
				self.librespot_p = None
			else:
				self.flush = True

		self.pctl.spot_playing = True

		if not self.librespot_p:
			logging.info("SPP: Librespot not running")
			username = self.spot_ctl.get_username()
			if not username or not self.prefs.spotify_token:
				logging.error("SPP: Missing auth data")
				return 1

			cache = str(self.cache_directory / "lsspot")
			if not Path(cache).exists():
				os.makedirs(cache)

			access_token = str(self.spot_ctl.spotify.token.access_token)

			cmd = ["librespot", "-k", access_token, "--backend", "pipe", "-n", "Tauon", "--disable-audio-cache", "--device-type", "computer", "--volume-ctrl", "fixed", "--initial-volume", "100"]

			#self.spot_ctl.preparing_spotify = True
			self.gui.update += 1

			startupinfo = None
			if sys.platform == "win32":
				startupinfo = subprocess.STARTUPINFO()
				startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
			try:
				self.librespot_p = subprocess.Popen(cmd, stdout=subprocess.PIPE, startupinfo=startupinfo)
				logging.info("SPP: Librespot now started")
			except Exception:
				logging.exception("SPP: Error starting librespot")
				#tauon.spot_ctl.preparing_spotify = False
				self.gui.update += 1
				return 1
		return 0

	def soft_end(self) -> None:
		self.running = False
		self.pctl.spot_playing = False

	def end(self) -> None:
		self.running = False
		self.pctl.spot_playing = False
		if self.librespot_p:
			if self.msys:
				self.librespot_p.terminate()
				#self.librespot_p.communicate()
			else:
				import signal
				self.librespot_p.send_signal(signal.SIGINT)  # terminate() doesn't work

	def worker(self) -> None:
		self.running = True
		logging.info("SPP: Enter librespot feeder thread")
		while True:
			if self.running is False:
				logging.info("SPP: Exit Librespot worker thread")
				return
			if self.flush:
				self.flush = False
				logging.info("SPP: Flushing some data...")
				self.librespot_p.stdout.read(70000)  # rough
				logging.info("SPP: Done flush")
			if self.aud.feed_ready(1000) == 1 and self.aud.get_buff_fill() < 2000:
				data = self.librespot_p.stdout.read(1000)
				self.aud.feed_raw(len(data), data)

			if self.tauon.player4_state == 0:
				self.librespot_p.stdout.read(50)
				time.sleep(0.0002)
			else:
				time.sleep(0.002)

class FFRun:
	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.decoder = None

	def close(self) -> None:
		if self.decoder:
			self.decoder.terminate()
			if self.decoder.stdin:
				logging.debug("Closing STDIN in FFrun")
				self.decoder.stdin.close()
			if self.decoder.stdout:
				logging.debug("Closing STDOUT in FFrun")
				self.decoder.stdout.close()
			if self.decoder.stderr:
				logging.debug("Closing STDERR in FFrun")
				self.decoder.stderr.close()
			self.decoder.wait()  # Ensure the process fully terminates
		self.decoder = None

	def start(self, uri: bytes, start_ms: int, samplerate: int) -> int:
		self.close()
		path = self.tauon.get_ffmpeg()
		if not path:
			self.tauon.test_ffmpeg()
			return 1
		cmd = [path]
		cmd += ["-loglevel", "quiet"]
		if start_ms > 0:
			cmd += ["-ss", f"{start_ms}ms"]
		cmd += ["-i", uri.decode(), "-acodec", "pcm_s16le", "-f", "s16le", "-ac", "2", "-ar", f"{samplerate}", "-"]
		startupinfo = None
		if sys.platform == "win32":
			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		try:
			self.decoder = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, startupinfo=startupinfo)
		except Exception:
			logging.exception("Failed to start ffmpeg")
			return 1
		return 0

	def read(self, buffer: int, maximum: int) -> int:
		if self.decoder:
			data = self.decoder.stdout.read(maximum)
			p = cast(buffer, POINTER(c_char * maximum))
			p.contents.value = data
			return len(data)
		return 0

class Cachement:
	def __init__(self, tauon: Tauon) -> None:
		self.tauon        = tauon
		self.gui          = tauon.gui
		self.pctl         = tauon.pctl
		self.prefs        = tauon.prefs
		self.show_message = tauon.show_message
		self.audio_cache  = tauon.cache_directory / "network-audio1"
		self.audio_cache2 = tauon.cache_directory / "audio-cache"
		self.direc = str(self.audio_cache2)
		if self.prefs.tmp_cache:
			self.direc = os.path.join(tmp_cache_dir(), "audio-cache")
		if not Path(self.direc).exists():
			os.makedirs(self.direc)
		self.list: list[str] = self.prefs.cache_list
		self.files = os.listdir(self.direc)
		self.get_now = None
		self.running = False
		self.ready = None
		self.error = None

	def get_key(self, track: TrackClass) -> str:
		if track.is_network:
			return hashlib.sha256((str(track.index) + track.url_key).encode()).hexdigest()
		return hashlib.sha256(track.fullpath.encode()).hexdigest()

	def get_file_cached_only(self, track: TrackClass) -> str | None:
		key = self.get_key(track)
		if key in self.files:
			path = Path(self.direc) / key
			if path.is_file():
				return str(path)
		return None

	def get_file(self, track: TrackClass) -> tuple[int, str | None]:
		# 0: file ready
		# 1: file downloading
		# 2: file not found
		if self.error == track:
			return 2, None

		key = self.get_key(track)
		path = os.path.join(self.direc, key)

		if self.running and self.get_now == track:
			return 1, path

		if key in self.files and os.path.isfile(path):
			logging.info("Got cached file")
			self.files.remove(key)
			self.files.append(key)  # bump to top of list
			self.get_now = None
			if not self.running:
				shoot_dl = threading.Thread(target=self.run)
				shoot_dl.daemon = True
				shoot_dl.start()
			return 0, path

		# disable me for debugging
		for codec in (".opus", ".ogg", ".flac", ".mp3"):
			idea = os.path.join(self.prefs.encoder_output, self.tauon.encode_folder_name(track), self.tauon.encode_track_name(track)) + codec
			if os.path.isfile(idea):
				logging.info("Found transcode")
				return 0, idea

		self.get_now = track
		if not self.running:
			shoot_dl = threading.Thread(target=self.run)
			shoot_dl.daemon = True
			shoot_dl.start()
		return 1, path

	def run(self) -> None:
		self.running = True

		now = self.get_now
		self.get_now = None
		if now is not None:
			error = self.dl_file(now)
			if error:
				self.error = now
				self.running = False
				return

		if self.get_now is None:
			i = 0
			while i < 10:
				time.sleep(0.1)
				i += 1
				if self.get_now is not None:
					self.running = False
					return
			logging.info("Precache next track")
			next_track = self.pctl.advance(dry=True)
			if next_track is not None:
				self.dl_file(self.pctl.get_track(next_track))

		self.trim_cache()
		self.running = False
		return

	def trim_cache(self) -> None:
		# Remove untracked items
		for item in self.files:
			t = os.path.join(self.direc, item)
			if os.path.isfile(t) and item not in self.list:
				os.remove(t)

		# Check total size
		limit = self.prefs.cache_limit
		if self.prefs.tmp_cache:
			limit = 10
		while True:
			s = 0
			for item in list(self.list):
				t = os.path.join(self.direc, item)
				if not os.path.exists(t):
					self.list.remove(item)
					continue
				s += os.path.getsize(t)
			# Removed oldest items if over limit
			if s > limit * 1000 * 1000 and len(self.list) > 3:
				t = os.path.join(self.direc, self.list[0])
				os.remove(t)
				del self.list[0]
			else:
				break

	def dl_file(self, track: TrackClass) -> int | None:
		self.pctl.buffering_percent = 0
		key = self.get_key(track)
		path = Path(self.direc) / key
		if path.exists():
			if not path.is_file():
				return 1
			if key in self.list:
				return 0
			path.unlink()
		if not track.is_network:
			if not Path(track.fullpath).is_file():
				self.error = track
				self.running = False
				return 1

			logging.info("Start transfer")
			timer = Timer()
			target = path.open("wb")
			source = Path(track.fullpath).open("rb")
			while True:
				try:
					data = source.read(128000)
				except Exception:
					logging.exception("Transfer failed.")
					break
				if len(data) > 0:
					logging.info(f"Caching file @ {int(len(data) / timer.hit() / 1000)} kbps")
				else:
					break
				target.write(data)
			target.close()
			source.close()
			logging.info("got file")
			self.files.append(key)
			self.list.append(key)
			return 0

		try:
			logging.info("Download file")

			network_url, params = self.pctl.get_url(track)
			if not network_url:
				logging.info("No URL")
				return 1
			if type(network_url) in (list, tuple) and len(network_url) == 1:
				network_url = network_url[0]
			elif type(network_url) in (list, tuple):
				logging.info("Multi part DL")
				logging.info(path)
				ffmpeg_command = [
					self.tauon.get_ffmpeg(),
					"-i", "-",      # Input from stdin (pipe the data)
					"-f", "flac",   # Specify FLAC as the output format explicitly
					"-c:a", "copy", # Copy FLAC data without re-encoding
					path,           # Output file for extracted FLAC
				]
				p = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)
				i = 0
				for url in network_url:
					i += 1
					logging.info(i)
					response = requests.get(url, timeout=10)
					if response.status_code == HTTPStatus.OK:
						p.stdin.write(response.content)
					else:
						logging.error(f"ERROR CODE: {response.status_code}")
					if i == 3:
						self.ready = track

					self.gui.update += 1
					self.pctl.buffering_percent = math.floor(i / len(network_url) * 100)
					self.gui.buffering_text = str(self.pctl.buffering_percent) + "%"
					if self.get_now is not None and self.get_now != track:
						logging.info("Aborted loading track!")
						return None

				#logging.info("done")
				p.stdin.close()
				p.wait()

				logging.info("Done loading track")
				self.files.append(key)
				self.list.append(key)
				return None

			part = requests.get(network_url, stream=True, params=params, timeout=(3, 10))

			if part.status_code == HTTPStatus.NOT_FOUND:
				self.show_message("Server: File not found", mode="error")
				self.error = track
				return 1
			if part.status_code != HTTPStatus.OK:
				self.show_message("Server Error", mode="error")
				self.error = track
				return 1

		except Exception as e:
			logging.exception("Download failed!")
			self.show_message(_("Error"), str(e), mode="error")
			self.error = track
			return 1

		a = 0
		length = 0
		cl = part.headers.get("Content-Length")
		if cl:
			length = int(cl)
			self.gui.buffering_text = "0%"


		timer = Timer()
		try:
			with path.open("wb") as f:
				for chunk in part.iter_content(chunk_size=1024):
					if chunk:  # filter out keep-alive new chunks
						a += 1
						if a == 1500:  # kilobyes~
							self.ready = track
						if a % 32 == 0:
							#time.sleep(0.03)
							#logging.info(f"Downloading file @ {round(32 / timer.hit())} kbps")
							if length:
								self.gui.update += 1
								self.pctl.buffering_percent = round(a * 1000 / length * 100)
								self.gui.buffering_text = str(round(a * 1000 / length * 100)) + "%"


						if self.get_now is not None and self.get_now != track:
							logging.warning("Aborted loading track!")
							return None

						# if self.cancel is True:
						#	 self.part.close()
						#	 self.status = "failed"
						#	 logging.info("Abort download")
						#	 return

						f.write(chunk)
			logging.info("Done loading track")
			self.files.append(key)
			self.list.append(key)
		except Exception:
			logging.exception("Download failed!")
			return 1
		return 0

def find_library(libname: str) -> Path | None:
	"""Search for 'libname.extension' in various formats.

	Return library Path loadable with ctypes.CDLL, otherwise return None
	"""
	# Can look like ~/Projects/Tauon/t_modules
	base_path = Path(__file__).parent
	search_paths: list[Path] = []
	so_extensions = importlib.machinery.EXTENSION_SUFFIXES
	site_packages_path = sysconfig.get_path("purelib")

	# Used to be lib but Slackware uses that for 32-bit,
	# all other distros seem to symlink lib64 to lib, so just use lib64
	libdir="lib64"

	# Try looking in site-packages of the current environment, pwd and ../pwd
	for extension in so_extensions:
		search_paths += [
			(Path(site_packages_path)                        / (libname + extension)).resolve(),
			(Path(base_path)          / ".."                 / (libname + extension)).resolve(),
			(Path(base_path)          / ".." / ".."          / (libname + extension)).resolve(),
			# Compat with old way to store .so files
			(Path(base_path)          / ".." / ".." / libdir / (libname + ".so")).resolve(),
		]

	for path in search_paths:
		if path.exists():
			logging.debug(f"Lib {libname} found in {path!s}")
			return path

	#raise OSError(f"Can't find library '{libname}'. Searched at:\n" + "\n".join(str(p) for p in search_paths))
	return None

def get_phazor_path(pctl: PlayerCtl) -> Path:
	"""Locate the PHaZOR library in the specified priority order.

	Tries .so, .dll, .pyd, .dynlib in that order and finally uses find_library as a fallback.

	:param pctl: PlayerCtl object containing installation details
	:return: Path to the library file
	:raises Exception: If no library is found
	"""
	# This is where compile-phazor.sh scrips place the dll
	base_path = Path(pctl.install_directory).parent.parent / "build"

	# Define the library name and extensions in priority order
	lib_name = "phazor-pw" if pctl.prefs.pipewire else "phazor"

	extensions = [".so", ".dll", ".pyd", ".dynlib"]

	# Check explicitly for each file
	for ext in extensions:
		lib_path = base_path / f"lib{lib_name}{ext}"
		if lib_path.is_file():
			return lib_path

	# Fallback to find_library. Used if built using setuptools
	lib_path = find_library(lib_name)
	if lib_path:
		return Path(lib_path)

	raise Exception(f"Failed to load PHaZOR library ({lib_name})")

def phazor_exists(pctl: PlayerCtl) -> bool:
	"""Check for the existence of the PHaZOR library on the FS"""
	return get_phazor_path(pctl).exists()

def player4(tauon: Tauon) -> None:
	def scan_device() -> None:
		n = aud.scan_devices()
		devices = ["Default"]
		if n:
			for d in range(n):
				st = aud.get_device(d).decode()
				devices.append(st)
		prefs.phazor_devices = devices
		if prefs.phazor_device_selected not in devices:
			prefs.phazor_device_selected = devices[0]

	def pause_when_device_unavailable() -> None:
		pctl.pause_only()

	def calc_rg(track: TrackClass | None) -> float:
		if prefs.replay_gain == 0 and prefs.replay_preamp == 0:
			pctl.active_replaygain = 0
			return 0

		g = 0
		p = 1

		if track is not None:
			tg = track.misc.get("replaygain_track_gain")
			tp = track.misc.get("replaygain_track_peak")
			ag = track.misc.get("replaygain_album_gain")
			ap = track.misc.get("replaygain_album_peak")

			if prefs.replay_gain > 0:
				if prefs.replay_gain == 3 and tg is not None and ag is not None:
					gens = pctl.gen_codes.get(tauon.pl_to_id(pctl.active_playlist_playing))
					if pctl.random_mode or (gens and ("st" in gens or "rt" in gens or "r" in gens)):
						g = tg
						if tp is not None:
							p = tp
					else:
						g = ag
						if ap is not None:
							p = ap
				elif (prefs.replay_gain == 1 and tg is not None) or (prefs.replay_gain == 2 and ag is None and tg is not None):
					g = tg
					if tp is not None:
						p = tp
				elif ag is not None:
					g = ag
					if ap is not None:
						p = ap

		# logging.info("Replay gain")
		# logging.info("GAIN: " + str(g))
		# logging.info("PEAK: " + str(p))
		# logging.info("FINAL: " + str(min(10 ** ((g + prefs.replay_preamp) / 20), 1 / p)))
		if p == 0:
			logging.warning("Detected replay gain peak of 0")
			return 1
		pctl.active_replaygain = g
		return min(10 ** ((g + prefs.replay_preamp) / 20), 1 / p)

	def set_config(set_device: bool = False) -> None:
		aud.config_set_dev_buffer(prefs.device_buffer)
		aud.config_set_fade_duration(prefs.cross_fade_time)
		st = prefs.phazor_device_selected.encode()
		aud.config_set_dev_name(st)
		if set_device:
			aud.pause()
			aud.wait()
			aud.stop_out()
			aud.wait()
			aud.resume()
		if prefs.always_ffmpeg:
			aud.config_set_always_ffmpeg(1)
		if prefs.volume_power < 0 or prefs.volume_power > 10:
			prefs.volume_power = 2
		aud.config_set_volume_power(prefs.volume_power)
		aud.config_set_resample(prefs.avoid_resampling ^ True)

	def run_vis() -> None:
		if gui.turbo:  # and pctl.playing_time > 0.5:
			if gui.vis == 2:
				p_spec = []
				aud.get_spectrum(24, bins1)
				bias = 1
				for b in list(bins1):
					p_spec.append(int(b * 1.7 * bias))
					bias += 0.04
				gui.spec = p_spec
				gui.level_update = True
				if pctl.playing_time > 0.5 and (pctl.playing_state in (1, 3)):
					gui.update_spec = 1
			elif gui.vis == 4:
				p_spec = []
				aud.get_spectrum(45, bins2)
				bias = 1
				for b in list(bins2):
					p_spec.append(int(b * 2.0 * bias))
					bias += 0.01
				gui.spec4_array = p_spec
				gui.level_update = True
				if pctl.playing_time > 0.5 and (pctl.playing_state in (1, 3)):
					gui.update_spec = 1

	def track(end: bool = True) -> None:
		run_vis()

		if end and loaded_track and loaded_track.is_network and pctl.playing_time < 7 and aud.get_result() == 2:
			logging.info("STALL, RETRY")
			time.sleep(0.5)
			pctl.playerCommandReady = True
			pctl.playerCommand = "open"

		add_time = player_timer.hit()
		if add_time > 2:
			add_time = 2
		elif add_time < 0:
			add_time = 0

		pctl.total_playtime += add_time

		##t = aud.get_position_ms() / 1000
		pctl.playing_time += add_time
		pctl.decode_time = pctl.playing_time

		if pctl.playing_time < 3 and pctl.a_time < 3:
			pctl.a_time = pctl.playing_time
		else:
			pctl.a_time += add_time

		tauon.lfm_scrobbler.update(add_time)

		if len(pctl.track_queue) > 0 and 2 > add_time > 0:
			tauon.star_store.add(pctl.track_queue[pctl.queue_step], add_time)
		if end and pctl.playing_time > 1:
			pctl.test_progress()

	def chrome_start(track_id: int, enqueue: bool = False, t: int = 0) -> None:
		track = pctl.get_track(track_id)
		# if track.is_cue:
		#	 logging.error("CUE cast not supported")
		#	 return
		if track.is_network:
			if track.file_ext == "SPTY":
				logging.error("Spotify cast not supported")
				return
			network_url, params = pctl.get_url(track)
			if params:
				req = PreparedRequest()
				req.prepare_url(network_url, params)
				network_url = req.url

			tauon.chrome.start(track.index, enqueue=enqueue, url=network_url, t=t)
		else:
			tauon.chrome.start(track.index, enqueue=enqueue, t=t)

	def start_librespot() -> None:
		logging.info("SPP: Start librespot command received. Set Phazor input raw mode")
		aud.start(b"RAW FEED", 0, 0, ctypes.c_float(calc_rg(None)))
		spotc.go(force=True)
		if not spotc.running:
			shooter(spotc.worker)

	gui   = tauon.gui
	pctl  = tauon.pctl
	prefs = tauon.prefs
	state = tauon.player4_state

	logging.debug("Starting PHAzOR backend…")

	player_timer = Timer()
	loaded_track = None
	fade_time = 400

	aud = tauon.aud

	aud.config_set_dev_name(prefs.phazor_device_selected.encode())

	aud.init()

	aud.get_device.restype = ctypes.c_char_p

	aud.feed_raw.argtypes = (ctypes.c_int,ctypes.c_char_p)
	aud.feed_raw.restype = None
	aud.set_volume(int(pctl.player_volume))

	bins1 = (ctypes.c_float * 24)()
	bins2 = (ctypes.c_float * 45)()

	aud.get_level_peak_l.restype = ctypes.c_float
	aud.get_level_peak_r.restype = ctypes.c_float

	active_timer = Timer()

	scan_device()
	spotc = tauon.spotc
	ff_run = FFRun(tauon)


	if sys.platform == "win32":
		FUNCTYPE = WINFUNCTYPE
	else:
		FUNCTYPE = CFUNCTYPE
	start_callback = FUNCTYPE(c_int, c_char_p, c_int, c_int)(ff_run.start)
	read_callback = FUNCTYPE(c_int, c_void_p, c_int)(ff_run.read)
	close_callback = FUNCTYPE(c_void_p)(ff_run.close)
	device_unavailable_callback = FUNCTYPE(c_void_p)(pause_when_device_unavailable)
	aud.set_callbacks(start_callback, read_callback, close_callback, device_unavailable_callback)

	cachement = tauon.cachement

	#aud.config_set_samplerate(prefs.samplerate)
	aud.config_set_resample_quality(prefs.resample)

	set_config()

	stall_timer = Timer()
	wall_timer = Timer()

	chrome_update = 0
	chrome_cool_timer = Timer()
	chrome_mode = False

	while True:
		#logging.error(aud.print_status())
		time.sleep(0.016)
		if state == 2:
			time.sleep(0.05)
		if state != 0 or tauon.spot_ctl.playing or tauon.spot_ctl.coasting or tauon.chrome_mode:
			active_timer.set()
		if active_timer.get() > 7:
			aud.stop()
			aud.phazor_shutdown()
			spotc.soft_end()
			break

		# Level meter
		if (state in (1, 3)) and gui.vis == 1:
			amp = aud.get_level_peak_l()
			l = amp * 12
			amp = aud.get_level_peak_r()
			r = amp * 12

			tauon.level_train.append((0, l, r))
			gui.level_update = True

		if chrome_mode:
			if pctl.playerCommandReady:
				command = pctl.playerCommand
				# logging.info(command)
				subcommand = pctl.playerSubCommand
				pctl.playerSubCommand = ""
				pctl.playerCommandReady = False

				if command == "endchrome":
					chrome_mode = False
					state = 0
					pctl.playing_time = 0
					pctl.decode_time = 0
					pctl.stop()
					continue
				if command == "open":
					target_object = pctl.target_object
					if state == 1:
						t, pid, s, d = tauon.chrome.update()
						# logging.info((t, d))
						# logging.info(d - t)

						if d and t and 1 < d - t < 5:
							# logging.info("Enqueue next chromecast")
							chrome_start(target_object.index, enqueue=True, t=pctl.start_time_target)
							chrome_cool_timer.set()
							time.sleep(d - t)
							if pctl.commit:
								pctl.advance(quiet=True, end=True)
								pctl.commit = None
							continue

					chrome_start(target_object.index, t=pctl.start_time_target)
					chrome_cool_timer.set()
					if pctl.commit:
						pctl.advance(quiet=True, end=True)
						pctl.commit = None
					state = 1
				if command == "pauseon":
					tauon.chrome.pause()
					state = 2
				if command == "pauseoff":
					tauon.chrome.play()
					state = 1
				if command == "volume":
					tauon.chrome.volume(round(pctl.player_volume / 100, 3))
					state = 1
				if command == "seek":
					tauon.chrome.seek(float(round(pctl.new_time + pctl.start_time_target, 2)))
					chrome_cool_timer.set()
					pctl.playing_time = pctl.new_time
					pctl.decode_time = pctl.playing_time
				if command == "stop":
					state = 0
					tauon.chrome.stop()

			if state == 1:
				if chrome_update > 0.8 and chrome_cool_timer.get() > 2.5:
					t, pid, s, d = tauon.chrome.update()
					pctl.playing_time = t - pctl.start_time_target
					pctl.decode_time = t - pctl.start_time_target
					player_timer.hit()
					chrome_update = 0

				add_time = player_timer.hit()
				add_time = min(add_time, 2)
				chrome_update += add_time
				pctl.a_time += add_time
				tauon.lfm_scrobbler.update(add_time)
				pctl.total_playtime += add_time
				if len(pctl.track_queue) > 0 and 2 > add_time > 0:
					tauon.star_store.add(pctl.track_queue[pctl.queue_step], add_time)

				pctl.test_progress()

			time.sleep(0.1)
			continue

		# Command processing
		if pctl.playerCommandReady:
			command = pctl.playerCommand
			subcommand = pctl.playerSubCommand
			pctl.playerSubCommand = ""
			pctl.playerCommandReady = False
			#logging.info(command)

			if command == "spotcon":
				#aud.stop()
				logging.info("SPP: Start librespot command received. Set Phazor input raw mode")
				start_librespot()
				state = 4
				#time.sleep(20)
				#tauon.spot_ctl.preparing_spotify = False

			if command == "startchrome":
				aud.stop()
				if state == 1:
					chrome_start(loaded_track.index, t=pctl.playing_time)
				chrome_mode = True

			if command == "reload":
				set_config()
			if command == "set-device":
				set_config(set_device=True)

			if command == "url":
				pctl.download_time = 0
				w = 0
				if not tauon.radiobox.run_proxy:
					aud.start(pctl.url.encode(), 0, 0, ctypes.c_float(calc_rg(None)))
					state = 3
					player_timer.hit()
				else:
					while len(tauon.stream_proxy.chunks) < 200:
						time.sleep(0.1)
						w += 1
						if w > 100:
							logging.info("Taking too long!")
							tauon.stream_proxy.stop()
							pctl.playerCommand = "stop"
							pctl.playerCommandReady = True
							break
					else:
						aud.config_set_feed_samplerate(prefs.samplerate)
						aud.start(b"RAW FEED", 0, 0, ctypes.c_float(calc_rg(None)))
						state = 3
						player_timer.hit()

			if command == "open":
				if state == 2:
					aud.set_volume(int(pctl.player_volume))


				stall_timer.set()
				pctl.download_time = 0
				target_object = pctl.target_object
				target_path = target_object.fullpath
				subtrack = target_object.subtrack
				aud.set_subtrack(subtrack)

				logging.info(f"Open - requested start was {int(pctl.start_time_target + pctl.jump_time)} ({pctl.start_time_target})")
				try:
					logging.info(f"Extension: {target_path.split('.')[-1]}")
				except Exception:
					logging.exception("Failed to get extension - maybe file name does not have any dots?")

				if (tauon.spot_ctl.playing or tauon.spot_ctl.coasting) and target_object.file_ext != "SPTY":
					tauon.spot_ctl.control("stop")

				if target_object.is_network:

					if target_object.file_ext == "SPTY":
						tauon.level_train.clear()
						if target_object.found is False:
							pctl.playing_state = 0
							pctl.jump_time = 0
							pctl.advance(inplace=True, play=True)
							continue
						if state > 0 and state != 4:
							aud.stop()
						if state != 4:
							state = 0

						try:
							f = False
							if spotc.running and state != 4:
								aud.start(b"RAW FEED", 0, 0, ctypes.c_float(calc_rg(None)))
								state = 4
							if prefs.launch_spotify_local and not spotc.running:
								aud.start(b"RAW FEED", 0, 0, ctypes.c_float(calc_rg(None)))
								state = 4
								if not tauon.librespot_p:
									tauon.spot_ctl.preparing_spotify = True
									f = True
								spotc.go()
								if not spotc.running:
									shooter(spotc.worker)

							tauon.spot_ctl.play_target(target_object.url_key, force_new_device=f, start_callback=start_librespot)
							#tauon.spot_ctl.preparing_spotify = False
							if pctl.playerCommand == "spotcon":  # such spaghetti code
								state = 4
								pctl.playerCommand = ""
								pctl.playerCommandReady = False

						except Exception:
							logging.exception("Failed to start Spotify track")
							#tauon.spot_ctl.preparing_spotify = False
							pctl.playerCommand = "stop"
							pctl.playerCommandReady = True
						continue

					spotc.running = False
					#tauon.spot_ctl.preparing_spotify = False
					pctl.spot_playing = False
					timer = Timer()
					timer.set()
					while True:
						status, path = cachement.get_file(target_object)

						if status in (0, 2):
							break
						if timer.get() > 0.25 and gui.buffering is False:
							gui.buffering_text = ""
							pctl.buffering_percent = 0
							gui.buffering = True
							gui.update += 1
							tauon.wake()
						if cachement.ready == target_object and pctl.start_time_target + pctl.jump_time == 0:
							break
						time.sleep(0.05)
						#logging.info(status)

					gui.buffering = False
					gui.update += 1
					tauon.wake()

					if status == 2:
						logging.info("Could not locate resource")
						target_object.found = False
						pctl.playing_state = 0
						pctl.jump_time = 0
						#pctl.advance(inplace=True, play=True)
						continue
					target_path = path

				elif prefs.precache:
					timer = Timer()
					timer.set()
					while True:
						status, path = cachement.get_file(target_object)
						if status in (0, 2):
							break
						if timer.get() > 0.25 and gui.buffering is False:
							gui.buffering_text = ""
							pctl.buffering_percent = 0
							gui.buffering = True
							gui.update += 1
							tauon.wake()

						time.sleep(0.05)

					gui.buffering = False
					gui.update += 1
					tauon.wake()

					if status == 2:
						target_object.found = False
						pctl.playing_state = 0
						pctl.jump_time = 0
						pctl.advance(inplace=True, play=True)
						continue
					target_path = path

				if not os.path.isfile(target_path):
					target_object.found = False
					if not target_object.is_network:
						pctl.playing_state = 0
						pctl.jump_time = 0
						pctl.advance(inplace=True, play=True)
					continue
				if not target_object.found:
					pctl.reset_missing_flags()

				spotc.running = False
				length: float = 0
				remain: float = 0
				position: float = 0

				if target_path and target_object and target_object.length == 0 and not target_object.is_cue:
					logging.info("Track has duration of 0, scanning file")
					temp = tauon.TrackClass()
					temp.fullpath = target_path
					tauon.tag_scan(temp)
					target_object.length = temp.length
					if pctl.playing_object() is target_object:
						pctl.playing_length = target_object.length
					del temp

				if state == 1 and not pctl.start_time_target and not pctl.jump_time and loaded_track:
					length = aud.get_length_ms() / 1000
					position = aud.get_position_ms() / 1000
					remain = length - position

					#TODO(Martin): The GUI logger does not support multiline
					#logging.info(f"{loaded_track.title} -> {target_object.title}\nlength: {length!s}\nposition: {position!s}\nWe are {remain!s} from end")
					logging.info(loaded_track.title + " -> " + target_object.title)
					logging.info(" --- length: " + str(length))
					logging.info(" --- position: " + str(position))
					logging.info(f" --- We are {remain!s} from end")

					if loaded_track.is_network or length == 0:
						logging.warning("Phazor did not respond with a duration")
						length = loaded_track.length
						remain = length - position

				fade = 0
				error = False
				if state == 1 \
				and length \
				and position \
				and not pctl.start_time_target \
				and not pctl.jump_time \
				and loaded_track \
				and 0 < remain < 5.5 \
				and not loaded_track.is_cue \
				and subcommand != "now":

					logging.info("Transition gapless")

					r_timer = Timer()
					r_timer.set()

					if loaded_track and loaded_track.file_ext.lower() in tauon.gme_formats:
						# GME formats dont have a physical end so we don't do gapless
						while r_timer.get() <= remain - prefs.device_buffer / 1000:
							if pctl.commit:
								track(end=False)
							time.sleep(0.016)
						aud.stop()

					aud.next(target_path.encode(), int(pctl.start_time_target + pctl.jump_time) * 1000, ctypes.c_float(calc_rg(target_object)))

					cont = False
					while r_timer.get() <= remain - prefs.device_buffer / 1000:
						if pctl.commit:
							track(end=False)
						time.sleep(0.016)
						if pctl.playerCommandReady and pctl.playerCommand in ("open", "stop"):
							logging.info("JANK")
							pctl.commit = None
							break
						if pctl.playerCommandReady and pctl.playerCommand == "seek":
							logging.info("Seek revert gapless")
							pctl.commit = None
							pctl.jump(loaded_track.index, jump=True)
							pctl.jump_time = pctl.new_time
							pctl.playing_time = pctl.new_time
							pctl.decode_time = pctl.new_time
							cont = True
							break

					if cont:
						continue
					if pctl.commit is not None:
						pctl.playing_time = 0
						pctl.decode_time = 0
						match = pctl.commit
						if match == loaded_track.index and subcommand == "repeat":
							pctl.update_change()
						else:
							pctl.advance(quiet=True, end=True)
						pt = pctl.playing_object()
						if pt and pt.index != match:
							logging.info("MISSFIRE")
							pctl.play_target()
							continue
						if pctl.playerCommandReady and pctl.playerCommand == "open":
							pctl.playerCommandReady = False
							pctl.playerCommand = ""

					loaded_track = target_object
					pctl.playing_time = pctl.jump_time
				else:
					if pctl.commit and subcommand != "repeat":
						pctl.advance(quiet=True, end=True)
						pctl.commit = None
						continue

					if state == 1 and prefs.use_jump_crossfade:
						fade = 1

					logging.info("Transition jump")
					aud.start(target_path.encode(errors="surrogateescape"), int(pctl.start_time_target + pctl.jump_time) * 1000, fade, ctypes.c_float(calc_rg(target_object)))
					loaded_track = target_object
					pctl.playing_time = pctl.jump_time
					if pctl.jump_time:
						while aud.get_result() == 0:
							time.sleep(0.016)
							run_vis()
						aud.set_position_ms(int(pctl.jump_time * 1000))

					# Restart track is failed to load (for some network tracks) (broken with gapless loading)
					while True:
						r = aud.get_result()
						if r == 1:
							break
						if r == 2:
							if loaded_track.is_network:
								pctl.buffering_percent = 0
								gui.buffering = True
								gui.buffering_text = ""

								# while dm.request(loaded_track, whole=True) == "wait":
								#	 time.sleep(0.05)
								#	 if pctl.playerCommandReady:
								#		 break
								logging.info("Retry start file")
								aud.start(
									target_path.encode(), int(pctl.start_time_target + pctl.jump_time) * 1000,
									fade, ctypes.c_float(calc_rg(target_object)))
								gui.buffering = False
								player_timer.set()
								break
							aud.stop()
							if not gui.message_box:
								tauon.show_message(_("Error loading track"), mode="warning")
							error = True
							break
						time.sleep(0.016)
						run_vis()

					state = 1
					if error:
						state = 0

				player_timer.set()
				pctl.jump_time = 0
				if loaded_track.length == 0 or loaded_track.file_ext.lower() in tauon.formats.MOD:
					i = 0
					t = 0
					while t == 0:
						time.sleep(0.3)
						t = aud.get_length_ms() / 1000
						i += 1
						if i > 9:
							break
					loaded_track.length = t
					if loaded_track.length != 0:
						pctl.playing_length = loaded_track.length
						gui.pl_update += 1

				pctl.commit = None
				stall_timer.set()
				wall_timer.force_set(3)

			if command == "seek":
				if tauon.spot_ctl.coasting or tauon.spot_ctl.playing:
					tauon.spot_ctl.control("seek", int(pctl.new_time * 1000))
					pctl.playing_time = pctl.new_time
				elif state > 0:
					if loaded_track.is_network:  # and loaded_track.fullpath.endswith(".ogg"):
						timer = Timer()
						timer.set()
						i = 0
						while True:
							status, path = cachement.get_file(loaded_track)
							if status == 1:
								per = (pctl.new_time / loaded_track.length) * 100
								if per < 1:
									break
								if pctl.buffering_percent - per > 5:
									break
							if status in (0, 2):
								break
							if timer.get() > 0.25 and gui.buffering is False:
								gui.buffering_text = ""
								pctl.buffering_percent = 0
								gui.buffering = True
								gui.update += 1
								tauon.wake()
							if i * 0.05 > 2:
								aud.pause()
							if pctl.playerCommandReady:
								break

							time.sleep(0.05)
							i += 1

						gui.buffering = False
						gui.update += 1
						tauon.wake()
						if pctl.playerCommandReady:
							continue

						if status == 2:
							loaded_track.found = False
							pctl.playing_state = 0
							pctl.jump_time = 0
							pctl.stop()
							continue

						# The vorbis decoder doesn't like appended files
						aud.start(path.encode(), int(pctl.new_time + pctl.start_time_target) * 1000, 0, ctypes.c_float(calc_rg(loaded_track)))
						while aud.get_result() == 0:
							time.sleep(0.01)
					else:
						aud.seek(int((pctl.new_time + pctl.start_time_target) * 1000), prefs.pa_fast_seek)

					pctl.playing_time = pctl.new_time

				pctl.decode_time = pctl.playing_time
				wall_timer.set()

			if command == "volume":
				if (tauon.spot_ctl.coasting or tauon.spot_ctl.playing) and not spotc.running:
					tauon.spot_ctl.control("volume", int(pctl.player_volume))
				else:
					aud.ramp_volume(int(pctl.player_volume), 750)

			if command == "runstop":
				length = aud.get_length_ms() / 1000
				position = aud.get_position_ms() / 1000
				remain = length - position
				# logging.info("length: " + str(length))
				# logging.info("position: " + str(position))
				# logging.info("We are %s from end" % str(remain))
				time.sleep(3)
				command = "stop"

			if command == "stop":
				if prefs.use_pause_fade and state != 3:
					if pctl.player_volume > 5:
						speed = fade_time / (int(pctl.player_volume) / 100)
					else:
						speed = fade_time / (5 / 100)

					aud.ramp_volume(0, int(speed))
					time.sleep((fade_time + 100) / 1000)

				state = 0
				pctl.playing_time = 0
				aud.stop()
				spotc.running = False
				time.sleep(0.1)
				aud.set_volume(int(pctl.player_volume))

				if subcommand == "return":
					pctl.playerSubCommand = "stopped"
					#pctl.playerCommandReady = True

			if command == "pauseon":
				if prefs.use_pause_fade:
					if pctl.player_volume > 5:
						speed = fade_time / (int(pctl.player_volume) / 100)
					else:
						speed = fade_time / (5 / 100)

					aud.ramp_volume(0, int(speed))
					time.sleep((fade_time + 100) / 1000)
				aud.pause()
				state = 2

			if command == "pauseoff":
				if prefs.use_pause_fade:
					if pctl.player_volume > 5:
						speed = fade_time / (int(pctl.player_volume) / 100)
					else:
						speed = fade_time / (5 / 100)

					aud.ramp_volume(int(pctl.player_volume), int(speed))
				aud.resume()
				player_timer.set()
				stall_timer.set()
				state = 1

			if command == "unload":
				if prefs.use_pause_fade:
					if pctl.player_volume > 5:
						speed = fade_time / (int(pctl.player_volume) / 100)
					else:
						speed = fade_time / (5 / 100)

					aud.ramp_volume(0, int(speed))
					time.sleep((fade_time + 100) / 1000)

				spotc.end()
				aud.stop()
				aud.phazor_shutdown()

				if cachement.audio_cache.exists():
					shutil.rmtree(cachement.audio_cache)

				pctl.playerCommand = "done"
				pctl.playerCommandReady = True
				break
		else:
			pctl.spot_test_progress()

			if state == 4:
				run_vis()

			if state == 3:
				pctl.radio_progress()
				run_vis()

				add_time = player_timer.hit()
				pctl.playing_time += add_time
				pctl.decode_time = pctl.playing_time

				buffering = aud.is_buffering()
				if gui.buffering != buffering:
					gui.buffering = buffering
					gui.update += 1

			if state == 1:
				track()
