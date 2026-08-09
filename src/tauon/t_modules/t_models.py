"""Foundational data models shared by Tauon modules."""

from __future__ import annotations

import os
import random
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tauon.t_modules.t_enums import QueueType

if TYPE_CHECKING:
	from pathlib import Path


_MISC_TO_FIELD = {
	"album_artists": "album_artists", "artists": "artists", "artist_sort": "artist_sort",
	"codec": "codec", "container": "container", "FMPS_Rating": "FMPS_Rating", "genres": "genres",
	"musicbrainz_albumid": "musicbrainz_albumid", "musicbrainz_artistids": "musicbrainz_artistids",
	"musicbrainz_recordingid": "musicbrainz_recordingid",
	"musicbrainz_releasegroupid": "musicbrainz_releasegroupid",
	"musicbrainz_trackid": "musicbrainz_trackid",
	"parent-length": "parent_length", "parent-size": "parent_size", "POPM": "POPM",
	"position": "position", "rdat": "rdat",
	"replaygain_album_gain": "replaygain_album_gain", "replaygain_album_peak": "replaygain_album_peak",
	"replaygain_track_gain": "replaygain_track_gain", "replaygain_track_peak": "replaygain_track_peak",
	"subsonic-folder-id": "subsonic_folder_id", "tidal_album": "tidal_album",
}


class LoadClass:
	"""Object for import track jobs (passed to worker thread)"""

	def __init__(self) -> None:
		self.target:            str = ""
		self.playlist:          int = 0  # Playlist UID
		self.tracks:            list[TrackClass] = []
		self.stage:             int = 0
		self.playlist_position: int | None = None
		self.replace_stem:      bool = False
		self.notify:            bool = False
		self.play:              bool = False
		self.force_scan:        bool = False


@dataclass
class ColourRGBA:
	"""Red, Green, Blue and Alpha.

	SDR, ranging from 0 to 255.
	"""

	r: int
	g: int
	b: int
	a: int


@dataclass
class RadioStation:
	title: str
	stream_url: str
	country: str = ""
	website_url: str = ""
	icon: str = ""
	stream_url_fallback: str = ""


@dataclass
class RadioPlaylist:
	name: str
	uid: int
	scroll: int = 0
	stations: list[RadioStation] = field(default_factory=list[RadioStation])


@dataclass
class StarRecord:
	"""Playtime in seconds, 0 to 10 rating, loved/hated status & timestamp.

	Hate status is currently not implemented. Integrations such as ListenBrainz use it.
	"""

	playtime: float = 0
	rating: int = 0
	loved: bool = False
	loved_timestamp: float = 0
	hated: bool = False
	hated_timestamp: float = 0


@dataclass
class TauonQueueItem:
	"""An item in the Tauon playback queue."""

	track_id: int
	position: int
	playlist_id: int
	type: QueueType
	album_stage: int
	uuid_int: int
	auto_stop: bool


def uid_gen() -> int:
	return random.randrange(1, 100000000)


def queue_item_gen(
	track_id: int,
	position: int,
	pl_id: int,
	queue_type: QueueType = QueueType.TRACK,
	album_stage: int = 0,
) -> TauonQueueItem:
	auto_stop = False
	return TauonQueueItem(
		track_id=track_id,
		position=position,
		playlist_id=pl_id,
		type=queue_type,
		album_stage=album_stage,
		uuid_int=uid_gen(),
		auto_stop=auto_stop,
	)


@dataclass
class TauonPlaylist:
	"""A Tauon playlist and its persisted view state."""

	title: str
	playing: int
	playlist_ids: list[int]
	position: int
	hide_title: bool
	selected: int
	uuid_int: int
	last_folder: list[str]
	hidden: bool
	locked: bool
	parent_playlist_id: int
	persist_time_positioning: bool
	playlist_file: str = ""
	auto_export: bool = False
	auto_import: bool = False
	relative_export: bool = False
	export_type: str = "xspf"
	file_size: int = 0


class TrackClass:
	"""The fundamental object/data structure of a track."""

	__slots__ = [
		"index", "subtrack", "fullpath", "filename", "parent_folder_path", "parent_folder_name",
		"file_ext", "size", "modified_time",
		"is_network", "url_key", "art_url_key",
		"artist", "album_artist", "title", "composer", "length", "bitrate", "samplerate", "bit_depth",
		"album", "date", "track_number", "track_total", "start_time", "is_cue", "is_embed_cue",
		"cue_sheet", "genre", "found", "skips", "comment", "disc_number", "disc_total", "lyrics", "synced",
		"lfm_friend_likes", "lfm_scrobbles",
		"album_artists", "artists", "artist_sort", "codec", "container", "FMPS_Rating", "genres",
		"musicbrainz_albumid", "musicbrainz_artistids", "musicbrainz_recordingid",
		"musicbrainz_releasegroupid", "musicbrainz_trackid", "parent_length", "parent_size", "POPM",
		"position", "rdat", "replaygain_album_gain", "replaygain_album_peak",
		"replaygain_track_gain", "replaygain_track_peak", "subsonic_folder_id", "tidal_album",
	]

	def __init__(self) -> None:
		self.index:              int = 0
		self.subtrack:           int = 0
		self.fullpath:           str = ""
		self.filename:           str = ""
		self.parent_folder_path: str = ""
		self.parent_folder_name: str = ""
		self.file_ext:           str = ""
		self.size:               int = 0
		self.modified_time:      float = 0

		self.is_network:   bool = False
		self.url_key:      str = ""
		self.art_url_key:  str = ""

		self.artist:       str = ""
		self.album_artist: str = ""
		self.title:        str = ""
		self.composer:     str = ""
		self.length:     float = 0
		self.bitrate:      int = 0
		self.samplerate:   int = 0
		self.bit_depth:    int = 0
		self.album:        str = ""
		self.date:         str = ""
		self.track_number: str = ""
		self.track_total:  str = ""
		self.start_time:   int = 0
		self.is_cue:       bool = False
		self.is_embed_cue: bool = False
		self.cue_sheet:    str = ""
		self.genre:        str = ""
		self.found:        bool = True
		self.skips:        int = 0
		self.comment:      str = ""
		self.disc_number:  str = ""
		self.disc_total:   str = ""
		self.lyrics:       str = ""
		self.synced:       str = ""

		self.lfm_friend_likes   = set()
		self.lfm_scrobbles: int = 0

		self.album_artists = None
		self.artists = None
		self.artist_sort = None
		self.codec = None
		self.container = None
		self.FMPS_Rating = None
		self.genres = None
		self.musicbrainz_albumid = None
		self.musicbrainz_artistids = None
		self.musicbrainz_recordingid = None
		self.musicbrainz_releasegroupid = None
		self.musicbrainz_trackid = None
		self.parent_length = None
		self.parent_size = None
		self.POPM = None
		self.position = None
		self.rdat = None
		self.replaygain_album_gain = None
		self.replaygain_album_peak = None
		self.replaygain_track_gain = None
		self.replaygain_track_peak = None
		self.subsonic_folder_id = None
		self.tidal_album = None


# Low-cardinality string fields that repeat heavily across a library (many
# tracks share the same album/artist/folder/etc). Interning collapses the
# duplicates onto shared objects to save memory. High-cardinality fields
# (title, fullpath, filename, mbids, lyrics...) are deliberately excluded:
# they barely dedup, so interning them would just waste effort.
_INTERN_FIELDS = (
	"parent_folder_path", "parent_folder_name", "file_ext",
	"artist", "album_artist", "album", "artist_sort", "composer",
	"genre", "date", "codec", "container",
	"track_number", "track_total", "disc_number", "disc_total",
)
# List-valued fields whose repeated string elements are worth deduplicating.
_INTERN_LIST_FIELDS = ("artists", "album_artists", "genres")


def intern_track_strings(tr: TrackClass) -> None:
	"""Deduplicate repeated low-cardinality string fields via sys.intern."""
	for field_name in _INTERN_FIELDS:
		value = getattr(tr, field_name)
		if type(value) is str and value:
			setattr(tr, field_name, sys.intern(value))
	for field_name in _INTERN_LIST_FIELDS:
		value = getattr(tr, field_name)
		if value:
			setattr(tr, field_name, [sys.intern(v) if type(v) is str else v for v in value])


# Extended-metadata fields shared by TrackFile (the tag scanner) and
# TrackClass. TrackFile mirrors these by name, so import copies them straight
# across instead of remapping a "misc" dict.
_TRACKFILE_METADATA_FIELDS = (
	"artists", "album_artists", "artist_sort", "genres",
	"musicbrainz_artistids", "musicbrainz_recordingid", "musicbrainz_trackid",
	"musicbrainz_albumid", "musicbrainz_releasegroupid",
	"replaygain_track_gain", "replaygain_track_peak",
	"replaygain_album_gain", "replaygain_album_peak",
	"FMPS_Rating", "rdat",
)


def copy_trackfile_metadata(nt: TrackClass, audio: object) -> None:
	"""Copy shared extended-metadata fields from a scanned TrackFile."""
	for field_name in _TRACKFILE_METADATA_FIELDS:
		setattr(nt, field_name, getattr(audio, field_name))


def get_end_folder(direc: str) -> str | None:
	for width in range(len(direc)):
		if direc[-width - 1] in "\\/":
			return direc[-width:]
	return None


def set_path(nt: TrackClass, path: str) -> None:
	nt.fullpath = path.replace("\\", "/")
	nt.filename = os.path.basename(path)
	nt.parent_folder_path = os.path.dirname(path.replace("\\", "/"))
	nt.parent_folder_name = get_end_folder(os.path.dirname(path))
	nt.file_ext = os.path.splitext(os.path.basename(path))[1][1:].upper()


@dataclass
class Directories:
	"""Hold application directories."""

	install_directory:      Path
	svg_directory:          Path
	asset_directory:        Path
	scaled_asset_directory: Path
	locale_directory:       Path
	user_directory:         Path
	config_directory:       Path
	cache_directory:        Path
	home_directory:         Path
	music_directory:        Path
	download_directory:     Path
	n_cache_directory:      Path
	e_cache_directory:      Path
	g_cache_directory:      Path
	a_cache_directory:      Path
	r_cache_directory:      Path
	b_cache_directory:      Path


@dataclass
class Formats:
	"""File extensions grouped by the way Tauon handles them."""

	colours: dict[str, ColourRGBA]
	VID:     set[str]
	MOD:     set[str]
	GME:     set[str]
	DA:      set[str]
	Archive: set[str]
