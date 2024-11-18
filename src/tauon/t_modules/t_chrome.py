from __future__ import annotations

import logging
import socket
from typing import TYPE_CHECKING

import pychromecast

from tauon.t_modules.t_extra import shooter

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Tauon

def get_ip() -> str:
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.settimeout(0)
	try:
		# doesn't even have to be reachable
		s.connect(("10.255.255.255", 1))
		IP = s.getsockname()[0]
	except Exception:
		logging.exception("Failed to get socket name.")
		IP = "127.0.0.1"
	finally:
		s.close()
	return IP


class Chrome:
	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.services = []
		self.active = False
		self.cast = None
		self.target_playlist = None
		self.target_id = None
		self.save_vol = 100

	def rescan(self) -> None:
		logging.info("Scanning for chromecasts...")

		if True: #not self.services:
			try:
				#self.tauon.gui.show_message(self.tauon.strings.scan_chrome)
				services, browser = pychromecast.discovery.discover_chromecasts()
				pychromecast.discovery.stop_discovery(browser)
				menu = self.tauon.chrome_menu
				MenuItem = self.tauon.MenuItem

				#menu.items.clear()
				for item in services:
					self.services.append([str(item.uuid), str(item.friendly_name)])
					menu.add_to_sub(1, MenuItem(self.tauon.strings.cast_to % str(item.friendly_name), self.three, pass_ref=True, args=[str(item.uuid), str(item.friendly_name)]))
				menu.add_to_sub(1, MenuItem(self.tauon.strings.stop_cast, self.end, show_test=lambda x: self.active))
			except Exception:
				logging.exception("Failed to get chromecasts")
				raise


	def three(self, _, item: tuple) -> None:
		shooter(self.four, [item])

	def four(self, item: dict) -> None:
		if self.active:
			self.end()
		self.tauon.start_remote()
		ccs, browser = pychromecast.get_listed_chromecasts(friendly_names=[item[1]], discovery_timeout=3.0)
		self.browser = browser
		self.cast = ccs[0]
		self.cast.wait()
		self.save_vol = self.tauon.pctl.player_volume
		self.tauon.pctl.player_volume = min(self.cast.status.volume_level * 100, 100)
		self.ip = get_ip()

		mc = self.cast.media_controller
		mc.app_id = "2F76715B"

		self.tauon.chrome_mode = True
		self.active = True
		self.tauon.gui.update += 1
		self.tauon.pctl.playerCommand = "startchrome"
		self.tauon.pctl.playerCommandReady = True
		self.tauon.tm.ready_playback()


	def update(self) -> None:
		self.cast.media_controller.update_status()
		return self.cast.media_controller.status.current_time, \
			self.cast.media_controller.status.media_custom_data.get("id"), \
			self.cast.media_controller.status.player_state, \
			self.cast.media_controller.status.duration

	def start(self, track_id: int, enqueue: bool = False, t: int = 0, url: str | None = None) -> None:
		self.cast.wait()
		tr = self.tauon.pctl.g(track_id)
		n = 0
		try:
			n = int(tr.track_number)
		except Exception:
			logging.exception("Failed to get track number")
		d = {
			"metadataType": 3,
			"albumName": tr.album,
			"title": tr.title,
			"albumArtist": tr.album_artist,
			"artist": tr.artist,
			"trackNumber": n,
			"images": [{"url": f"http://{self.ip}:7814/api1/pic/medium/{track_id}"}],
			"releaseDate": tr.date
		}
		m = {
			"duration": round(float(tr.length), 1),
			"customData": {"id": str(tr.index)},
		}

		if url is None:
			url = f"http://{self.ip}:7814/api1/file/{track_id}"
		else:
			url = url.replace("localhost", self.ip)
			url = url.replace("127.0.0.1", self.ip)

		self.cast.media_controller.play_media(url, "audio/mpeg", media_info=m, metadata=d, current_time=t, enqueue=enqueue)

	def stop(self) -> None:
		self.cast.media_controller.stop()

	def play(self) -> None:
		self.cast.media_controller.play()

	def pause(self) -> None:
		self.cast.media_controller.pause()

	def seek(self, t: str) -> None:
		self.cast.media_controller.seek(t)

	def volume(self, decimal: int) -> None:
		self.cast.set_volume(decimal)

	def end(self) -> None:
		self.tauon.pctl.playerCommand = "endchrome"
		self.tauon.pctl.playerCommandReady = True
		if self.active:
			if self.cast:
				mc = self.cast.media_controller
				mc.stop()
			self.active = False
		self.tauon.chrome_mode = False
		self.tauon.pctl.player_volume = self.save_vol
