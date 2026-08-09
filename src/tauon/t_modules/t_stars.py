"""Star ratings and play-count storage."""

from __future__ import annotations

import logging
import math
from typing import Protocol

import mutagen.flac
import mutagen.id3
import mutagen.oggvorbis

from tauon.t_modules.t_extra import shooter
from tauon.t_modules.t_models import StarRecord, TrackClass


class _StarPrefs(Protocol):
	write_ratings: bool


class _StarSubsonic(Protocol):
	def set_rating(self, track: TrackClass, value: int) -> object: ...


class _StarApp(Protocol):
	prefs: _StarPrefs
	after_scan: list[TrackClass]
	subsonic: _StarSubsonic


class _StarPlayer(Protocol):
	master_library: dict[int, TrackClass]

	def get_track(self, index: int) -> TrackClass: ...


class StarStore:
	"""Functions for reading and setting play counts."""

	def __init__(self, tauon: _StarApp, pctl: _StarPlayer) -> None:
		self.tauon = tauon
		self.pctl = pctl
		self.prefs = tauon.prefs
		self.after_scan = tauon.after_scan
		self.db: dict[tuple[str, str, str], StarRecord] = {}

	def key(self, track_id: int) -> tuple[str, str, str]:
		track_object = self.pctl.master_library[track_id]
		return track_object.artist, track_object.title, track_object.filename

	def object_key(self, track: TrackClass) -> tuple[str, str, str]:
		return track.artist, track.title, track.filename

	def add(self, index: int, value: float) -> None:
		"""Increments the play time"""
		track_object = self.pctl.master_library[index]

		if self.after_scan and track_object in self.after_scan:
			return

		key = track_object.artist, track_object.title, track_object.filename

		if key in self.db:
			self.db[key].playtime += value
			if value < 0 and self.db[key].playtime < 0:
				self.db[key].playtime = 0
		else:
			self.db[key] = StarRecord(playtime=value)

	def get(self, index: int) -> float:
		"""Returns the track play time"""
		if index < 0:
			return 0
		return self.db.get(self.key(index), StarRecord()).playtime

	def get_rating(self, index: int) -> int:
		"""Returns the track user rating"""
		key = self.key(index)
		if key in self.db:
			return self.db[key].rating
		return 0

	def set_rating(self, index: int, value: int, write: bool = False) -> None:
		"""Sets the track user rating"""
		key = self.key(index)
		if key not in self.db:
			self.db[key] = StarRecord()
		self.db[key].rating = value

		tr = self.pctl.get_track(index)
		if tr.file_ext == "SUB":
			self.db[key].rating = math.ceil(value / 2) * 2
			shooter(self.tauon.subsonic.set_rating, (tr, value))

		if self.prefs.write_ratings and write:
			logging.info("Writing rating..")
			assert value <= 10
			assert value >= 0

			if tr.file_ext in ("OGG", "OPUS"):
				tag = mutagen.oggvorbis.OggVorbis(tr.fullpath)
				if value == 0:
					if "FMPS_RATING" in tag:
						del tag["FMPS_RATING"]
						tag.save()
				else:
					tag["FMPS_RATING"] = [f"{value / 10:.2f}"]
					tag.save()

			elif tr.file_ext == "MP3":
				tag = mutagen.id3.ID3(tr.fullpath)

				# if True:
				#	 if value == 0:
				#		 tag.delall("POPM")
				#	 else:
				#		 p_rating = 0
				#
				#	 tag.add(mutagen.id3.POPM(email="Windows Media Player 9 Series", rating=int))

				if value == 0:
					changed = False
					frames = tag.getall("TXXX")
					for i in reversed(range(len(frames))):
						if frames[i].desc.lower() == "fmps_rating":
							changed = True
					if changed:
						tag.delall("TXXX:FMPS_RATING")
						tag.save()
				else:
					changed = False
					frames = tag.getall("TXXX")
					for i in reversed(range(len(frames))):
						if frames[i].desc.lower() == "fmps_rating":
							frames[i].text = f"{value / 10:.2f}"
							changed = True
					if not changed:
						tag.add(
							mutagen.id3.TXXX(
								encoding=mutagen.id3.Encoding.UTF8, text=f"{value / 10:.2f}",
								desc="FMPS_RATING"))
					tag.save()

			elif tr.file_ext == "FLAC":
				audio = mutagen.flac.FLAC(tr.fullpath)
				tags = audio.tags
				if value == 0:
					if "FMPS_Rating" in tags:
						del tags["FMPS_Rating"]
						audio.save()
				else:
					tags["FMPS_Rating"] = f"{value / 10:.2f}"
					audio.save()

			tr.FMPS_Rating = float(value / 10)
			if value == 0:
				tr.FMPS_Rating = None

	def get_by_object(self, track: TrackClass) -> float:
		return self.db.get(self.object_key(track), StarRecord()).playtime

	def get_total(self) -> float:
		return sum(item.playtime for item in self.db.values())

	def full_get(self, index: int) -> StarRecord | None:
		return self.db.get(self.key(index))

	def remove(self, index: int) -> None:
		key = self.key(index)
		if key in self.db:
			del self.db[key]

	def insert(self, index: int, record: StarRecord) -> None:
		key = self.key(index)
		self.db[key] = record

	def merge(self, index: int, record: StarRecord | None) -> None:
		if record is None or record == StarRecord():
			return
		key = self.key(index)
		if key not in self.db:
			self.db[key] = record
		else:
			self.db[key].playtime += record.playtime
			self.db[key].rating = record.rating
