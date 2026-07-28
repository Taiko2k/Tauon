from __future__ import annotations

import logging
import socket
import threading
from typing import TYPE_CHECKING
from uuid import UUID

import pychromecast
import zeroconf
from pychromecast.controllers.media import BaseMediaPlayer, MediaController, MediaStatus

from tauon.t_modules.t_extra import shooter

if TYPE_CHECKING:
	from pychromecast import Chromecast
	from pychromecast.discovery import CastBrowser

	from tauon.t_modules.t_main import Tauon


DISCOVERY_TIMEOUT = 5.0
CAST_CONNECT_TIMEOUT = 10.0
STYLED_RECEIVER_APP_ID = "2F76715B"


def get_ip(target_host: str | None = None) -> str:
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.settimeout(0)
	try:
		# This does not send traffic, but asks the OS which interface it would use
		# to reach the Chromecast. Falling back to a private address preserves the
		# previous behaviour when no cast host is available.
		s.connect((target_host or "10.255.255.255", 8009))
		ipv4 = s.getsockname()[0]
	except Exception:
		logging.exception("Failed to get socket name.")
		ipv4 = "127.0.0.1"
	finally:
		s.close()
	return ipv4


class StyledMediaController(MediaController):
	def __init__(self, app_id: str) -> None:
		BaseMediaPlayer.__init__(self, supporting_app_id=app_id, app_must_match=False)
		self.media_session_id = 0
		self.status = MediaStatus()
		self.session_active_event = threading.Event()
		self._status_listeners = []


class Chrome:
	def __init__(self, tauon: Tauon) -> None:
		self.tauon: Tauon = tauon
		self.services: list[tuple[str, str]] = []
		self.active: bool = False
		self.cast: Chromecast | None = None
		self.save_vol: float = 100
		self.ip: str = ""
		self.browser: CastBrowser | None = None
		self.media_controller: StyledMediaController | None = None

	def discover_services(self, timeout: float = DISCOVERY_TIMEOUT) -> list[tuple[str, str]]:
		zconf = zeroconf.Zeroconf()
		try:
			browser = pychromecast.discovery.CastBrowser(
				pychromecast.discovery.SimpleCastListener(),
				zconf,
			)
		except Exception:
			zconf.close()
			raise
		try:
			browser.start_discovery()
			threading.Event().wait(timeout)
		finally:
			browser.stop_discovery()
		return sorted(
			[
				(str(device.uuid), str(device.friendly_name))
				for device in browser.devices.values()
			],
			key=lambda service: service[1].casefold(),
		)

	def rescan(self) -> None:
		logging.info("Scanning for chromecasts...")

		if True:  # not self.services:
			try:
				# self.tauon.show_message(self.tauon.strings.scan_chrome)
				services = self.discover_services()
				menu = self.tauon.chrome_menu
				if menu is None:
					logging.critical("menu was None, this should not happen!")
					return
				MenuItem = self.tauon.MenuItem
				chrome_submenu_index = len(menu.subs) - 1
				if chrome_submenu_index < 0:
					logging.critical("Chromecast submenu was missing, this should not happen!")
					return

				self.services = services
				menu.subs[chrome_submenu_index].clear()
				for item in self.services:
					menu.add_to_sub(
						chrome_submenu_index,
						MenuItem(
							self.tauon.strings.cast_to % item[1],
							self.three,
							pass_ref=True,
							args=item,
						),
					)
				menu.add_to_sub(
					chrome_submenu_index,
					MenuItem(self.tauon.strings.stop_cast, self.end, show_test=lambda x: self.active),
				)
			except Exception:
				logging.exception("Failed to get chromecasts")
				raise

	def three(self, _, item: tuple[str, str]) -> None:
		shooter(self.four, [item])

	def _release_connection(self) -> None:
		"""Release pychromecast's socket and discovery resources."""
		cast = self.cast
		browser = self.browser
		media_controller = self.media_controller
		self.cast = None
		self.browser = None
		self.media_controller = None

		if cast and media_controller:
			try:
				cast.unregister_handler(media_controller)
			except Exception:
				logging.exception("Failed to unregister Chromecast media controller")
		if cast:
			try:
				cast.disconnect(timeout=0)
			except TimeoutError:
				logging.debug("Chromecast connection is shutting down asynchronously")
			except Exception:
				logging.exception("Failed to disconnect Chromecast")
		if browser:
			try:
				browser.stop_discovery()
			except Exception:
				logging.exception("Failed to stop Chromecast discovery")

	def four(self, item: tuple[str, str]) -> None:
		if self.active:
			self.end()
		else:
			self._release_connection()
		self.tauon.start_remote()
		ccs, browser = pychromecast.get_listed_chromecasts(
			uuids=[UUID(item[0])], discovery_timeout=3.0
		)
		self.browser = browser
		if not ccs:
			logging.error("No Chromecast found for selected device")
			self._release_connection()
			return
		self.cast = ccs[0]
		try:
			self.cast.wait(timeout=CAST_CONNECT_TIMEOUT)
		except Exception:
			logging.exception("Failed to connect to Chromecast")
			self._release_connection()
			return
		self.save_vol = self.tauon.pctl.player_volume
		volume = self.cast.status.volume_level if self.cast.status else 0
		if not self.cast.status:
			logging.critical("self.cast.status was None, this should not happen!")
		self.tauon.pctl.player_volume = min(volume * 100, 100)
		self.ip = get_ip(self.cast.cast_info.host)
		self.media_controller = StyledMediaController(STYLED_RECEIVER_APP_ID)
		self.cast.register_handler(self.media_controller)

		self.tauon.chrome_mode = True
		self.active = True
		self.tauon.gui.request_frame()
		self.tauon.pctl.playerCommand = "startchrome"
		self.tauon.pctl.playerCommandReady = True
		self.tauon.thread_manager.ready_playback()

	def update(self) -> tuple:
		if self.media_controller is None:
			logging.critical("self.media_controller was None, this should not happen!")
			return (0.0, None, None, 0.0)
		self.media_controller.update_status()
		status = self.media_controller.status
		if status is None:
			logging.critical("self.media_controller.status was None, this should not happen!")
			return (0.0, None, None, 0.0)
		custom_data = status.media_custom_data if isinstance(status.media_custom_data, dict) else {}
		return (
			status.current_time,
			custom_data.get("id"),
			status.player_state,
			status.duration,
		)

	def start(self, track_id: int, enqueue: bool = False, t: int = 0, url: str | None = None) -> bool:
		if self.cast is None:
			logging.critical("self.cast was None, this should not happen!")
			return False
		if self.media_controller is None:
			logging.critical("self.media_controller was None, this should not happen!")
			return False
		try:
			self.cast.wait(timeout=CAST_CONNECT_TIMEOUT)
		except Exception:
			logging.exception("Chromecast connection timed out while starting playback")
			return False
		try:
			self.cast.start_app(STYLED_RECEIVER_APP_ID)
		except Exception:
			logging.exception("Failed to start Chromecast receiver")
			return False
		tr = self.tauon.pctl.get_track(track_id)
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
			"releaseDate": tr.date,
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

		try:
			self.media_controller.play_media(
				url, self._mime_type(tr.file_ext), media_info=m, metadata=d, current_time=t, enqueue=enqueue
			)
		except Exception:
			logging.exception("Failed to start Chromecast media")
			return False
		return True

	@staticmethod
	def _mime_type(file_ext: str) -> str:
		return {
			"FLAC": "audio/flac",
			"OGG": "audio/ogg",
			"OPUS": "audio/ogg",
			"OGA": "audio/ogg",
			"M4A": "audio/mp4",
		}.get(file_ext.upper(), "audio/mpeg")

	def stop(self) -> None:
		if self.media_controller is None:
			logging.critical("self.media_controller was None, this should not happen!")
			return
		self.media_controller.stop()

	def play(self) -> None:
		if self.media_controller is None:
			logging.critical("self.media_controller was None, this should not happen!")
			return
		self.media_controller.play()

	def pause(self) -> None:
		if self.media_controller is None:
			logging.critical("self.media_controller was None, this should not happen!")
			return
		self.media_controller.pause()

	def seek(self, position: float) -> None:
		if self.media_controller is None:
			logging.critical("self.media_controller was None, this should not happen!")
			return
		self.media_controller.seek(position)

	def volume(self, decimal: int) -> None:
		if self.cast is None:
			logging.critical("self.cast was None, this should not happen!")
			return
		self.cast.set_volume(decimal)

	def end(self) -> None:
		self.tauon.pctl.playerCommand = "endchrome"
		self.tauon.pctl.playerCommandReady = True
		if self.active:
			if self.media_controller:
				try:
					self.media_controller.stop()
				except Exception:
					logging.exception("Failed to stop Chromecast playback")
			self.active = False
		self.tauon.chrome_mode = False
		self.tauon.pctl.player_volume = self.save_vol
		self._release_connection()
