"""Tauon Music Box - Server playlist picker shared by the Jellyfin and Subsonic integrations"""

# Copyright © 2026, Taiko2k captain(dot)gxj(at)gmail.com

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

import logging
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from tauon.t_modules.t_main import GuiVar, PlayerCtl, Tauon


@dataclass
class RemotePlaylist:
	id: str
	name: str
	count: int = 0
	smart: bool = False


class RemotePlaylistSource:
	"""Lists a server's playlists and imports the ones picked in settings.

	Subclasses set code_prefix (the generator code, e.g. 'air' for air"<id>") and implement
	_list_playlists() and playlist_track_ids(). They also need tauon, pctl and gui attributes.
	"""

	code_prefix = ""
	tauon: Tauon
	pctl: PlayerCtl
	gui: GuiVar

	def init_remote_playlists(self) -> None:
		# None until the list has been fetched once
		self.remote_playlists: list[RemotePlaylist] | None = None
		self.remote_playlists_loading = False
		self.remote_playlists_error = ""
		# Ids queued or being imported, so their rows can say so
		self.remote_playlists_busy: set[str] = set()
		self.remote_playlists_lock = threading.Lock()

	def _list_playlists(self) -> list[RemotePlaylist] | None:
		"""The server's playlists, or None after setting remote_playlists_error."""
		raise NotImplementedError

	def playlist_track_ids(self, playlist_id: str) -> list[int] | None:
		"""Tauon track ids for a server playlist in its order, or None if it couldn't be fetched."""
		raise NotImplementedError

	def playlist_code(self, playlist_id: str) -> str:
		return f'{self.code_prefix}"{playlist_id}"'

	def imported_playlist(self, playlist_id: str) -> int | None:
		"""Index of the Tauon playlist a server playlist was imported to."""
		code = self.playlist_code(playlist_id)
		for i, pl in enumerate(self.pctl.multi_playlist):
			if code in self.pctl.gen_codes.get(pl.uuid_int, ""):
				return i
		return None

	def _refresh_ui(self) -> None:
		self.gui.update_layout = True
		self.gui.request_frame()
		self.tauon.wake()

	def fetch_playlist_list(self) -> None:
		self.remote_playlists_error = ""
		try:
			playlists = self._list_playlists()
		except OSError as e:
			# Includes requests' connection errors: the server is down or the URL is wrong
			logging.warning(f"Error listing {self.code_prefix} playlists: {e}")
			playlists = None
			self.remote_playlists_error = _("Could not connect to the server")
		except Exception:
			logging.exception(f"Error listing {self.code_prefix} playlists")
			playlists = None
			self.remote_playlists_error = _("Could not connect to the server")
		if playlists is not None:
			self.remote_playlists = playlists
		self.remote_playlists_loading = False
		self._refresh_ui()

	def start_fetch_playlist_list(self) -> None:
		if self.remote_playlists_loading:
			return
		self.remote_playlists_loading = True
		self._refresh_ui()
		thread = threading.Thread(target=self.fetch_playlist_list, daemon=True)
		thread.start()

	def import_playlist(self, playlist: RemotePlaylist) -> bool:
		"""Import a server playlist, or refresh it if it was imported before."""
		index = self.imported_playlist(playlist.id)
		if index is not None:
			# Regenerate rather than overwrite, so sorting the user added to the generator survives
			self.tauon.regenerate_playlist(index, silent=True)
			return True

		track_ids = self.playlist_track_ids(playlist.id)
		if track_ids is None:
			return False
		# Match what regenerating does, so the first import and later refreshes agree
		track_ids = list(dict.fromkeys(track_ids))
		# Navidrome reports 0 songs for a smart playlist it hasn't evaluated yet
		playlist.count = len(track_ids)
		self.pctl.multi_playlist.append(self.tauon.pl_gen(title=playlist.name, playlist_ids=track_ids))
		self.pctl.gen_codes[self.tauon.pl_to_id(len(self.pctl.multi_playlist) - 1)] = self.playlist_code(playlist.id)
		return True

	def import_playlists(self, playlists: list[RemotePlaylist]) -> None:
		failed: list[str] = []
		added = 0
		for playlist in playlists:
			is_new = self.imported_playlist(playlist.id) is None
			try:
				with self.remote_playlists_lock:
					ok = self.import_playlist(playlist)
			except Exception:
				logging.exception(f"Error importing playlist {playlist.name}")
				ok = False
			if not ok:
				failed.append(playlist.name)
			elif is_new:
				added += 1
			self.remote_playlists_busy.discard(playlist.id)
			self.gui.request_tracklist_redraw()
			self._refresh_ui()

		self.pctl.notify_database_changed()
		self.tauon.reload()
		if failed:
			self.tauon.show_message(
				_("Couldn't import some playlists"), ", ".join(failed), mode="warning")
		elif len(playlists) > 1:
			updated = len(playlists) - added
			if not updated:
				message = _("Imported {count} playlists").format(count=added)
			elif not added:
				message = _("Updated {count} playlists").format(count=updated)
			else:
				message = _("Imported {added} playlists, updated {updated}").format(added=added, updated=updated)
			self.tauon.show_message(message, mode="done")

	def _library_import_running(self) -> bool:
		# Both would add the same songs to the library at once and could duplicate them
		if getattr(self, "scanning", False):
			self.tauon.show_message(_("Wait for the music import to finish"))
			return True
		return False

	def start_import_playlists(self, playlists: list[RemotePlaylist]) -> None:
		if self._library_import_running():
			return
		playlists = [p for p in playlists if p.id not in self.remote_playlists_busy]
		if not playlists:
			return
		self.remote_playlists_busy.update(p.id for p in playlists)
		self._refresh_ui()
		thread = threading.Thread(target=self.import_playlists, args=(playlists,), daemon=True)
		thread.start()

	def import_all_playlists(self) -> None:
		# Fetch first, so playlists added on the server since the list was shown are included
		self.fetch_playlist_list()
		if self.remote_playlists_error:
			self.tauon.show_message(_("Couldn't load playlists"), self.remote_playlists_error, mode="warning")
			return
		playlists = [p for p in self.remote_playlists or [] if p.id not in self.remote_playlists_busy]
		if not playlists:
			self.tauon.show_message(_("No playlists to import"))
			return
		self.remote_playlists_busy.update(p.id for p in playlists)
		self._refresh_ui()
		self.import_playlists(playlists)

	def start_import_all_playlists(self) -> None:
		if self.remote_playlists_loading or self._library_import_running():
			return
		self.remote_playlists_loading = True
		self._refresh_ui()
		thread = threading.Thread(target=self.import_all_playlists, daemon=True)
		thread.start()
