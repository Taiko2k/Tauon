# Copyright © 2026, Taiko2k captain(dot)gxj(at)gmail.com

"""Gallery art prefetch.

In shuffle, the next track can be anywhere in the playlist, and skipping to it
scrolls the gallery there. Once the gallery has drawn everything it shows, this
works out which tiles it would show for the next track. NetArtFetcher downloads
their network art (once the playing track's audio is buffered, one at a time, giving
way to art wanted on screen), and the gallery's thumbnail worker makes their
thumbnails as the art arrives, between thumbnails wanted on screen.
"""
from __future__ import annotations

import logging
import math
from bisect import bisect_right
from typing import TYPE_CHECKING

from tauon.t_modules.t_enums import PlayingState

if TYPE_CHECKING:
	from collections.abc import Iterable, Sequence

	from tauon.t_modules.t_main import Tauon, TrackClass

	ThumbKey = tuple[TrackClass, int, int]


def album_index(album_dex: Sequence[int], position: int) -> int:
	"""Index in album_dex of the album holding playlist position"""
	return max(0, min(bisect_right(album_dex, position) - 1, len(album_dex) - 1))


def locate_scroll(
	album_dex: Sequence[int], position: int, row_len: int, pitch: float,
	scroll: float, slide: float, view_h: float, force: bool = False,
) -> tuple[float, int]:
	"""The gallery scroll that brings position's album into view, and that album's
	index. A view already showing it only moves enough to show the whole row."""
	index = album_index(album_dex, position)
	px = (index // max(row_len, 1)) * pitch
	if not force and scroll + slide < px < scroll + view_h:
		limit = px + pitch + 43 - view_h
		if view_h > pitch * 2 and scroll <= limit:
			scroll += math.floor(limit - scroll) + 1
	else:
		scroll = max(px - slide, -slide)
	return scroll, index


def visible_albums(row_len: int, pitch: float, scroll: float, view_h: float, count: int) -> range:
	"""Album indexes the gallery draws at scroll, including the part rows at the edges"""
	first_row = max(0, math.ceil((scroll - pitch) / pitch))
	end_row = max(first_row, math.ceil((scroll + view_h) / pitch))
	return range(min(first_row * row_len, count), min(end_row * row_len, count))


def album_is_singles(tracks: Iterable[TrackClass]) -> bool:
	"""Whether the gallery draws a tile as a fan of singles rather than one cover"""
	changes = 0
	ones = 0
	last_album = ""
	for track in tracks:
		if track.album != last_album:
			if last_album:
				changes += 1
			last_album = track.album
			if str(track.track_number) == "1":
				ones += 1
	return changes > 2 or ones > 2


SINGLES_SHOWN = 5  # tracks a singles tile draws


class GalleryPrefetch:
	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.reported = False  # a gallery has drawn this frame
		self.view: tuple | None = None  # what the prefetch list was worked out for
		self._position: tuple[tuple[int, int, int], int] | None = None  # (key, next track's position)

	def new_frame(self) -> None:
		"""Called at the start of each frame; no gallery drawn last frame means none is open"""
		if not self.reported and self.view is not None:
			self._set(None, ())
		self.reported = False

	def gallery_drawn(self, row_len: int) -> None:
		"""Called by a gallery after drawing its tiles. Only the first each frame counts."""
		if self.reported:
			return
		self.reported = True
		try:
			found = self._predict(row_len)
			if found is None:
				self._set(None, [])
			elif found[0] != self.view:
				self._set(found[0], self._tiles(*found[1:]))
		except Exception:
			logging.exception("Gallery prefetch failed")
			self._set(None, [])

	def _set(self, view: tuple | None, tiles: list[ThumbKey]) -> None:
		if view is None and self.view is None:
			return
		self.view = view
		gall = self.tauon.gall_ren
		# Art first: the worker makes each thumbnail once its art is here
		self.tauon.album_art_gen.net_art.set_extra(key[0] for key in tiles if not gall.has_thumb(key))
		gall.set_prepare(tiles)

	def _next_position(self, playlist: list[int], track_id: int) -> int | None:
		key = (id(playlist), len(playlist), track_id)
		if self._position is not None and self._position[0] == key:
			position = self._position[1]
			if position < len(playlist) and playlist[position] == track_id:
				return position
		try:
			position = playlist.index(track_id)
		except ValueError:
			return None
		self._position = (key, position)
		return position

	def _predict(self, row_len: int) -> tuple[tuple, range, int] | None:
		"""(view key, album indexes shown, next track's album index) for the gallery as
		it would be after skipping to the next track, or None if there's nothing to do"""
		tauon = self.tauon
		pctl = tauon.pctl
		gui = tauon.gui
		gall = tauon.gall_ren
		playing = pctl.playing_object()
		upcoming = tauon.album_art_gen.net_art.next_track
		if not (
			pctl.random_mode and upcoming is not None
			and playing is not None and playing.is_network
			and pctl.playing_state in (PlayingState.PLAYING, PlayingState.PAUSED)
			and pctl.active_playlist_viewing == pctl.active_playlist_playing
		):
			return None
		# Whatever is on screen comes first
		if gall.busy():
			return None
		album_dex = tauon.album_dex
		playlist = pctl.default_playlist
		if not album_dex or not playlist or row_len < 1:
			return None
		position = self._next_position(playlist, upcoming.index)
		if position is None:
			return None
		pitch = tauon.album_mode_art_size + gui.album_v_gap
		view_h = tauon.window_size[1]
		scroll, index = locate_scroll(
			album_dex, position, row_len, pitch, gui.album_scroll_px, gui.album_v_slide_value, view_h)
		albums = visible_albums(row_len, pitch, scroll, view_h, len(album_dex))
		starts = tuple(playlist[album_dex[a]] for a in albums if album_dex[a] < len(playlist))
		return (starts, gall.size), albums, index

	def _tiles(self, albums: range, index: int) -> list[ThumbKey]:
		"""Thumbnails the tiles in albums would draw and that aren't made yet,
		nearest the next track's first"""
		tauon = self.tauon
		pctl = tauon.pctl
		gall = tauon.gall_ren
		playlist = pctl.default_playlist
		wanted: list[ThumbKey] = []
		for a in sorted(albums, key=lambda a: abs(a - index)):
			start = tauon.album_dex[a]
			if start >= len(playlist):
				continue
			album = [pctl.get_track(playlist[p]) for p in tauon.get_album_info(start)[1]]
			if album_is_singles(album):
				size = round(tauon.album_mode_art_size * 0.5)
				keys = [gall.key(track, size, 0) for track in album[:SINGLES_SHOWN]]
			else:
				keys = [gall.key(pctl.get_track(playlist[start]))]
			wanted.extend(key for key in keys if key not in gall.gall)
		return wanted
