"""Background worker coordination and download monitoring."""

from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable, Protocol

from tauon.t_modules.t_enums import Backend
from tauon.t_modules.t_extra import Timer, archive_file_scan, folder_file_scan, get_folder_size
from tauon.t_modules.t_models import Formats
from tauon.t_modules.t_phazor import player4
from tauon.t_modules.t_prefs import Prefs
from tauon.t_modules.t_state import GuiVar


class _WorkerPlayer(Protocol):
	def __getattr__(self, name: str) -> Any: ...


class _WorkerApp(Protocol):
	prefs: Prefs
	gui: GuiVar
	pctl: _WorkerPlayer
	formats: Formats

	def __getattr__(self, name: str) -> Any: ...
class ThreadManager:
	def __init__(self, tauon: _WorkerApp) -> None:
		self.tauon = tauon
		self.prefs = tauon.prefs
		self.worker1:  threading.Thread | None = None  # Artist list, download monitor, folder move, importing, db cleaning, transcoding
		self.worker2:  threading.Thread | None = None  # Art bg, search
		self.worker3:  threading.Thread | None = None  # Gallery rendering
		self.playback: threading.Thread | None = None
		self.player_lock:       threading.Lock = threading.Lock()
		self.d: dict[str, tuple[Callable[..., None], list, threading.Thread | None]] = {}

	def ready(self, name: str) -> None:
		if self.d[name][2] is None or not self.d[name][2].is_alive():
			shoot = threading.Thread(target=self.d[name][0], args=self.d[name][1])
			shoot.daemon = True
			shoot.start()
			self.d[name][2] = shoot

	def ready_playback(self) -> None:
		if self.playback is None or not self.playback.is_alive():
			if self.prefs.backend == Backend.PHAZOR:
				self.playback = threading.Thread(target=player4, args=[self.tauon])
			# elif self.prefs.backend == Backend.GSTREAMER:
			# 	from tauon.t_modules.t_gstreamer import player3
			# 	self.playback = threading.Thread(target=player3, args=[tauon])
			self.playback.daemon = True
			self.playback.start()

	def check_playback_running(self) -> bool:
		if self.playback is None:
			return False
		return self.playback.is_alive()
class DLMon:

	def __init__(self, tauon: _WorkerApp) -> None:
		self.tauon: _WorkerApp = tauon
		self.gui: GuiVar = tauon.gui
		self.windows: bool = tauon.windows
		self.pctl: _WorkerPlayer = tauon.pctl
		self.prefs: Prefs = tauon.prefs
		self.formats: Formats = tauon.formats
		self.music_directory: Path = tauon.music_directory
		self.ticker = Timer()
		self.ticker.force_set(8)

		self.watching: dict[str, int] = {}
		self.ready = set()
		self.done = set()
		self.unavailable_directories: set[str] = set()

	def scan(self) -> None:
		if len(self.watching) == 0:
			if self.ticker.get() < 10:
				return
		elif self.ticker.get() < 2:
			return

		self.ticker.set()

		for downloads in self.tauon.download_directories:
			try:
				items = os.listdir(downloads)
			except PermissionError:
				if downloads not in self.unavailable_directories:
					logging.warning(f"Skipping unreadable download directory: {downloads}")
					self.unavailable_directories.add(downloads)
				continue
			except OSError:
				logging.exception(f"Failed to scan download directory: {downloads}")
				self.unavailable_directories.add(downloads)
				continue
			else:
				self.unavailable_directories.discard(downloads)

			for item in items:
				path = os.path.join(downloads, item)

				if path in self.done:
					continue

				if path in self.ready and not os.path.exists(path):
					del self.ready[path]
					continue

				if path in self.watching and not os.path.exists(path):
					del self.watching[path]
					continue

				# stamp = os.stat(path)[stat.ST_MTIME]
				try:
					stamp = os.path.getmtime(path)
				except Exception:
					logging.exception(f"Failed to scan item at {path}")
					self.done.add(path)
					continue

				min_age = (time.time() - stamp) / 60
				ext = os.path.splitext(path)[1][1:].lower()

				if self.windows and "TauonMusicBox" in path:
					continue

				if min_age < 240 and os.path.isfile(path) and ext in self.formats.Archive:
					size = os.path.getsize(path)
					#logging.info("Check: " + path)
					if path in self.watching:
						# Check if size is stable, then scan for audio files
						#logging.info("watching...")
						if size == self.watching[path] and size != 0:
							#logging.info("scan")
							del self.watching[path]

							# Check if folder to extract to exists
							split = os.path.splitext(path)
							target_dir = split[0]
							if self.prefs.extract_to_music and self.music_directory is not None:
								target_dir = os.path.join(str(self.music_directory), os.path.basename(target_dir))

							if os.path.exists(target_dir):
								pass
								#logging.info("Target folder for archive already exists")

							elif archive_file_scan(path, self.formats.DA, self.tauon.launch_prefix) >= 0.4:
								self.ready.add(path)
								self.gui.request_frame()
								#logging.info("Archive detected as music")
							else:
								pass
								#logging.info("Archive rejected as music")
							self.done.add(path)
						else:
							#logging.info("update.")
							self.watching[path] = size
					else:
						self.watching[path] = size
						#logging.info("add.")
				elif min_age < 60 \
				and os.path.isdir(path) \
				and path not in self.tauon.quick_import_done \
				and "encode-output" not in path:
					try:
						size = get_folder_size(path)
					except FileNotFoundError:
						logging.warning(f"Failed to find watched folder {path}, deleting from watchlist")
						if path in self.watching:
							del self.watching[path]
						continue
					except Exception:
						logging.exception("Unknown error getting folder size")
						continue
					if path in self.watching:
						# Check if size is stable, then scan for audio files
						if size == self.watching[path]:
							del self.watching[path]
							if folder_file_scan(path, self.formats.DA) > 0.5:

								# Check if folder not already imported
								imported = False
								for pl in self.pctl.multi_playlist:
									for i in pl.playlist_ids:
										if path.replace("\\", "/") == self.pctl.master_library[i].fullpath[:len(path)]:
											imported = True
										if imported:
											break
									if imported:
										break
								else:
									self.ready.add(path)
								self.gui.request_frame()
							self.done.add(path)
						else:
							self.watching[path] = size
					else:
						self.watching[path] = size
				else:
					self.done.add(path)

		if len(self.ready) > 0:
			temp = set()
			#logging.info(self.tauon.quick_import_done)
			#logging.info(self.ready)
			for item in self.ready:
				if item not in self.tauon.quick_import_done:
					if os.path.exists(path):
						temp.add(item)
				# else:
				# 	logging.info("FILE IMPORTED")
			self.ready = temp

		if len(self.watching) > 0:
			self.tauon.gui.request_frame()
