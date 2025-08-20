"""Tauon Music Box - Tag Module

The purpose of this module is to read metadata from FLAC, OGG, OPUS, APE and WV files
"""

# Copyright © 2015-2019, Taiko2k captain(dot)gxj(at)gmail.com

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

import io
import logging
import os
import struct
import wave
from pathlib import Path
from typing import TYPE_CHECKING

from tauon.t_modules.t_extra import process_odat

if TYPE_CHECKING:
	from io import BufferedReader, BytesIO
	from types import TracebackType

	from typing_extensions import Self

def parse_mbids_from_vorbis(obj: Ape | Flac | Opus, key: str, value: str | bytes) -> bool:
	if key == "musicbrainz_artistid":
		if "musicbrainz_artistids" not in obj.misc:
			obj.misc["musicbrainz_artistids"] = []
		obj.misc["musicbrainz_artistids"].append(value)
		return True

	if key == "musicbrainz_trackid":
		obj.misc["musicbrainz_recordingid"] = value
		return True

	if key == "musicbrainz_releasetrackid":
		obj.misc["musicbrainz_trackid"] = value
		return True

	if key == "musicbrainz_albumid":
		obj.misc["musicbrainz_albumid"] = value
		return True

	if key == "musicbrainz_releasegroupid":
		obj.misc["musicbrainz_releasegroupid"] = value
		return True

	return False


def parse_picture_block(f: BufferedReader) -> bytes:
	a = f.read(4)
	a = int.from_bytes(a, byteorder="big")
	# logging.info("Picture type: " + str(a))

	a = f.read(4)
	b = int.from_bytes(a, byteorder="big")
	# logging.info("MIME len: " + str(b))

	a = f.read(b)
	# logging.info(a)
	# logging.info("MIME: " + a.decode('ascii'))

	a = f.read(4)
	a = int.from_bytes(a, byteorder="big")
	# logging.info("Description len: " + str(a))

	a = f.read(a)
	# logging.info("Description: " + a.decode('utf-8'))

	a = f.read(4)
	# a = int.from_bytes(a, byteorder='big')
	# logging.info("Width: " + str(a))

	a = f.read(4)
	# a = int.from_bytes(a, byteorder='big')
	# logging.info("Height: " + str(a))

	a = f.read(4)
	# a = int.from_bytes(a, byteorder='big')
	# logging.info("BPP: " + str(a))

	a = f.read(4)
	# a = int.from_bytes(a, byteorder='big')
	# logging.info("Index colour: " + str(a))

	a = f.read(4)
	a = int.from_bytes(a, byteorder="big")
	# logging.info("Bin len: " + str(a))

	return f.read(a)

class TrackFile:
	"""Base class for codec classes"""

	def __init__(self) -> None:
		self.file: BufferedReader | None = None
		self.has_picture = False # Wav does not need this

		self.picture      = "" # Wav does not need this
		self.filepath     = ""
		self.album_artist = ""
		self.artist       = ""
		self.genre        = ""
		self.date         = "" # Wav does not need this
		self.comment      = "" # Wav does not need this
		self.album        = ""
		self.track_number = ""
		self.track_total  = "" # Wav does not need this
		self.title        = ""
		self.encoder      = "" # Wav does not need this
		self.disc_number  = "" # Wav does not need this
		self.disc_total   = "" # Wav does not need this
		self.lyrics       = "" # Wav does not need this
		self.composer     = "" # Wav does not need this
		self.misc: dict[str, str | float | list[str]] = {} # Wav does not need this

		self.sample_rate = 48000 # OPUS files are always 48000
		self.length = 0
		self.bit_rate = 0  # Wav does not need this
		self.bit_depth = 0 # Opus, M4a and Wav does not need this

		self.track_gain: float | None = None # Wav does not need this
		self.album_gain: float | None = None # Wav does not need this

	def __enter__(self) -> Self:
		"""Open the file when entering the context"""
		self.file = Path(self.filepath).open("rb")
		return self

	def __exit__(
		self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None,
	) -> None:
		"""Close the file when exiting the context"""
		if self.file:
			self.file.close()
		self.file = None

class Flac(TrackFile):

	def __init__(self, file: str) -> None:
		super().__init__()
		self.filepath = file
		self.cue_sheet = ""

	def read_vorbis(self, f: BufferedReader) -> None:
		block_position = 0

		buffer = f.read(4)
		block_position += 4
		jump = int.from_bytes(buffer, byteorder="little")

		f.read(jump)
		block_position += jump

		buffer = f.read(4)
		block_position += 4
		fields = int.from_bytes(buffer, byteorder="little")
		# logging.info(fields)
		album_artists: list[str] = []
		artists: list[str] = []
		genres: list[str] = []
		odat = ""

		for i in range(fields):
			buffer = f.read(4)
			block_position += 4

			jump = int.from_bytes(buffer, byteorder="little")
			buffer = f.read(jump)
			block_position += jump

			# logging.info(buffer.decode('utf-8'))

			position = 0

			while position < 40:
				# logging.info(sss[position:position+1])
				position += 1

				if buffer[position:position + 1] == b"=":
					a = buffer[0:position].decode("utf-8").lower()
					b = buffer[position + 1:]

					if parse_mbids_from_vorbis(self, a, b.decode()):
						pass
						# logging.info("Found MBID data:")
						# logging.info(a)
						# logging.info(b)
					elif a == "genre":
						#self.genre = b.decode("utf-8")
						genres.append(b.decode())
					elif a == "cuesheet":
						self.cue_sheet = b.decode()
					elif a == "date":
						self.date = b.decode("utf-8")
					elif a == "originaldate":
						odat = b.decode("utf-8")
					elif a == "comment":
						self.comment = b.decode("utf-8")
					elif a == "album":
						self.album = b.decode("utf-8")
					elif a == "title":
						self.title = b.decode("utf-8")
					elif a == "tracknumber":
						self.track_number = b.decode("utf-8")
					elif a in ("tracktotal", "totaltracks"):
						self.track_total = b.decode("utf-8")
					elif a == "encoder":
						self.encoder = b.decode("utf-8")
					elif a in ("albumartist", "album artist"):
						#self.album_artist = b.decode("utf-8")
						album_artists.append(b.decode("utf-8"))
					elif a == "artist":
						#self.artist = b.decode("utf-8")
						artists.append(b.decode())
					elif a in ("disctotal", "totaldiscs"):
						self.disc_total = b.decode("utf-8")
					elif a == "discnumber":
						self.disc_number = b.decode("utf-8")
					elif a == "metadata_block_picture":
						logging.info("Tag Scanner: Found picture inside vorbis comment inside a FLAC file. Ignoring")
						logging.info(f"      In file: {self.filepath}")
					elif a in ("lyrics", "unsyncedlyrics"):
						self.lyrics = b.decode("utf-8")
					elif a == "replaygain_track_gain":
						self.misc["replaygain_track_gain"] = float(b.decode("utf-8").lower().strip(" db").replace(",", "."))
					elif a == "replaygain_track_peak":
						self.misc["replaygain_track_peak"] = float(b.decode("utf-8").replace(",", "."))
					elif a == "replaygain_album_gain":
						self.misc["replaygain_album_gain"] = float(b.decode("utf-8").lower().strip(" db").replace(",", "."))
					elif a == "replaygain_album_peak":
						self.misc["replaygain_album_peak"] = float(b.decode("utf-8").replace(",", "."))
					elif a == "composer":
						self.composer = b.decode("utf-8")
					elif a == "fmps_rating":
						self.misc["FMPS_Rating"] = float(b.decode("utf-8"))
					elif a == "artistsort":
						self.misc["artist_sort"] = b.decode("utf-8")

					# else:
					#	 logging.info("Tag Scanner: Found unhandled FLAC Vorbis comment field: " + a)
					#	 logging.info(b)
					#	 logging.info("\n-------------------------------------------\n")

		f.seek(block_position * -1, 1)

		if album_artists:
			#self.album_artist = "; ".join(album_artists)
			self.album_artist = album_artists[0]
			if len(album_artists) > 1:
				self.misc["album_artists"] = album_artists
		if artists:
			self.artist = "; ".join(artists)
			if len(artists) > 1:
				self.misc["artists"] = artists
		if genres:
			self.genre = "; ".join(genres)
			if len(genres) > 1:
				self.misc["genres"] = genres
		process_odat(self, odat)

	def read_seek_table(self, f: BufferedReader) -> None:
		f.read(10)
		buffer = f.read(8)
		a = (int.from_bytes(buffer, byteorder="big"))
		k = bin(a)[2:].zfill(64)

		self.sample_rate = int(k[0:20], 2)

		bps = int(k[23:28], 2)
		self.bit_depth = bps + 1

		samples = int(k[28:64], 2)

		self.length = samples / self.sample_rate
		f.seek(-18, 1)

	def read(self, get_picture: bool = False) -> None:
		if not self.file:
			self.file = Path(self.filepath).open("rb")
		f = self.file

		# Very helpful: https://xiph.org/flac/format.html
		size = os.path.getsize(self.filepath) / 8
		if size < 100:
			return

		s = f.read(4)

		# Find start of FLAC stream
		if s != b"fLaC":
			while f.tell() < size + 100:
				f.seek(-3, 1)
				s = f.read(4)
				if s == b"fLaC":
					break
			else:
				return

		i = 0
		while i < 20:
			i += 1
			z = self.read_block(f)

			if z[1] == 0:
				self.read_seek_table(f)
			if z[1] == 4:
				self.read_vorbis(f)
			if z[1] == 5:
				logging.info("Tag Scan: Flac file has native embedded CUE. Not supported")
				logging.info(f"      In file: {self.filepath}")
				# mark = f.tell()
				#
				# logging.info("Found flac cue")
				#
				# a = f.read(16*8)
				# a = int.from_bytes(a, byteorder='big')
				# logging.info(("Catalog Number: " + str(a)))
				#
				#
				# f.seek(mark)
				# f.seek(z[2], 1)

			if z[1] == 6 and get_picture:
				self.picture = parse_picture_block(f)
				self.has_picture = True
			else:
				f.read(z[2])

			if z[0] == 1:
				break

	def read_block(self, f: BufferedReader) -> tuple[int, int, int]:
		q = f.read(1)
		a = (int.from_bytes(q, byteorder="big"))
		k = bin(a)[2:].zfill(8)
		flag = int(k[:1], 2)
		block_type = int(k[1:], 2)
		s = f.read(3)
		a = (int.from_bytes(s, byteorder="big"))
		length = a

		return flag, block_type, length

	def get(self) -> None:
		pass

# file = 'b.flac'
#
# item = Flac(file)
# item.read()

class Opus(TrackFile):

	def __init__(self, file: str) -> None:
		super().__init__()
		self.filepath = file
		self.length = 0

	def get_more(self, f: BufferedReader, v: BytesIO) -> int:
		header = struct.unpack("<4sBBqIIiB", f.read(27))

		segs = struct.unpack("B" * header[7], f.read(header[7]))
		l = sum(segs)

		o = v.tell()
		v.seek(0, 2)
		v.write(f.read(l))
		v.seek(o)

		return l

	def read(self) -> None:
		if not self.file:
			self.file = Path(self.filepath).open("rb")
		f = self.file

		header = struct.unpack("<4sBBqIIiB", f.read(27))

		# logging.info(header)

		segs = struct.unpack("B"*header[7], f.read(header[7]))

		# l = sum(segs)
		# logging.info(f.read(l + 4))
		# f.seek(l * -1)

		s = f.read(7)

		if s == b"OpusHea":
			f.seek(-7, 1)
		elif s == b"\x01vorbis":
			s = f.read(4)
			a = struct.unpack("<B4i", f.read(17)) # 44100
			self.sample_rate = a[1]
			self.bit_rate = int(a[3] / 1000)
			f.seek(-28, 1)
		else:
			return

		for p in segs:
			f.read(p)

		v = io.BytesIO()
		v.seek(0)

		l = self.get_more(f, v)

		s = v.read(7)
		l -= 7

		if s == b"OpusTag":
			v.read(1)
			l -= 1
		elif s == b"\x03vorbis":
			pass
		else:
			return

		s = v.read(4)
		l -= 4
		a = int.from_bytes(s, byteorder="little")  # Vendor string length
		s = v.read(a)  # Vendor string
		l -= a

		s = v.read(4)
		l -= 4

		number = int.from_bytes(s, byteorder="little")  # Number of comments

		album_artists: list[str] = []
		artists: list[str] = []
		genres: list[str] = []
		odat = ""

		for i in range(number):
			s = v.read(4)
			l -= 4

			length = int.from_bytes(s, byteorder="little")

			while l < length + 4:
				l += self.get_more(f, v)

			s = v.read(length)
			l -= length

			position = 0
			while position < 40:
				position += 1

				if s[position:position+1] == b"=":
					a = s[0:position].decode("utf-8").lower()
					b = s[position + 1:]

					# logging.info(a)  # Key
					# logging.info(b)  # Value

					if parse_mbids_from_vorbis(self, a, b.decode()):
						pass
						# logging.info("Found MBID data:")
						# logging.info(a)
						# logging.info(b)

					elif a == "genre":
						#self.genre = b.decode("utf-8")
						genres.append(b.decode())
					elif a == "date":
						self.date = b.decode("utf-8")
					elif a == "originaldate":
						odat = b.decode("utf-8")
					elif a == "comment":
						self.comment = b.decode("utf-8")
					elif a == "album":
						self.album = b.decode("utf-8")
					elif a == "title":
						self.title = b.decode("utf-8")
					elif a == "tracknumber":
						self.track_number = b.decode("utf-8")
					elif a in ("tracktotal", "totaltracks"):
						self.track_total = b.decode("utf-8")
					elif a == "encoder":
						self.encoder = b.decode("utf-8")
					elif a in ("albumartist", "album artist"):
						#self.album_artist = b.decode("utf-8")
						album_artists.append(b.decode("utf-8"))
					elif a == "artist":
						#self.artist = b.decode("utf-8")
						artists.append(b.decode())
					elif a == "metadata_block_picture":

						logging.info("Tag Scanner: Found picture in OGG/OPUS file.")
						logging.info(f"      In file: {self.filepath}")
						self.has_picture = True
						self.picture = b
						# logging.info(b)

					elif a == "replaygain_track_gain":
						self.misc["replaygain_track_gain"] = float(b.decode("utf-8").lower().strip(" db"))
					elif a == "replaygain_track_peak":
						self.misc["replaygain_track_peak"] = float(b.decode("utf-8"))
					elif a == "replaygain_album_gain":
						self.misc["replaygain_album_gain"] = float(b.decode("utf-8").lower().strip(" db"))
					elif a == "replaygain_album_peak":
						self.misc["replaygain_album_peak"] = float(b.decode("utf-8"))
					elif a == "discnumber":
						self.disc_number = b.decode("utf-8")
					elif a in ("disctotal", "totaldiscs"):
						self.disc_total = b.decode("utf-8")
					elif a in ("lyrics", "unsyncedlyrics"):
						self.lyrics = b.decode("utf-8")
					elif a == "composer":
						self.composer = b.decode("utf-8")
					elif a == "fmps_rating":
						self.misc["FMPS_Rating"] = float(b.decode("utf-8"))
					elif a == "artistsort":
						self.misc["artist_sort"] = b.decode("utf-8")
					# else:
					#	 logging.info("Tag Scanner: Found unhandled Vorbis comment field: " + a)
					#	 logging.info(b.decode("utf-8"))
					#	 logging.info("	  In file: " + self.filepath)

					break

		v.close()

		if album_artists:
			#self.album_artist = "; ".join(album_artists)
			self.album_artist = album_artists[0]
			if len(album_artists) > 1:
				self.misc["album_artists"] = album_artists
		if artists:
			self.artist = "; ".join(artists)
			if len(artists) > 1:
				self.misc["artists"] = artists
		if genres:
			self.genre = "; ".join(genres)
			if len(genres) > 1:
				self.misc["genres"] = genres
		process_odat(self, odat)

		# Find the last Ogg page from end of file to get track length
		f.seek(-1, 2)

		# Crudely seek back for it
		g = 100000
		while g > 0:
			if f.tell() < 10:
				break
			g -= 1
			f.seek(-5, 1)
			s = f.read(4)

			if s == b"OggS":
				f.seek(-4, 1)
				header = struct.unpack("<4sBBqIIiB", f.read(27))
				self.length = header[3] / self.sample_rate
				break

# file = 'a.ogg'
#
# item = Opus(file)
# item.read()

class Ape(TrackFile):
	"""Helpful: http://wiki.hydrogenaud.io/index.php?title=APEv2_specification"""

	def __init__(self, file: str) -> None:
		super().__init__()
		self.filepath = file
		self.found_tag = False
		self.label = ""

	def read(self) -> None:
		if not self.file:
			self.file = Path(self.filepath).open("rb")
		a = self.file

		# Check size of file
		a.seek(0, 2)
		file_size = a.tell()

		# Get last 32 bytes where ape tag footer might be
		a.seek(-32, 1)
		b = a.read(32)
		footer = struct.unpack("<8c6i", b)

		# For use later
		found = 1

		# If its not an ape footer, seek through the file for a bit to see if we find it
		if b"".join(footer[0:8]) != b"APETAGEX":
			found = 0
			a.seek(0, 2)
			g = 1000
			while g > 0:
				if a.tell() < 1000:
					break
				g -= 1
				a.seek(-9, 1)
				s = a.read(8)

				# Found it
				if s == b"APETAGEX":
					found = 2
					a.seek(-8, 1)
					b = a.read(32)
					footer = struct.unpack("<8c6i", b)

		if found == 0:
			logging.info("Tag Scanner: Cant find APE tag")
		else:
			self.found_tag = True
			tag_len = footer[9]  # The size of the tag data (excludes header)
			num_items = footer[10]  # Number of fields in tag

			# logging.info("Tag len: " + str(tag_len))
			# logging.info("Items: " + str(num_items))

			# Seek to start of tag (after any header)
			if found == 1:
				a.seek(tag_len * -1, 2)
			else:
				a.seek(8 + (tag_len * -1), 1)

			# For every field in tag
			for q in range(num_items):
				# (field value length, 0=text 2=binary)
				ta = struct.unpack("<ii", a.read(8))

				# Collect every character until we reach null terminator
				name = b""
				for i in range(100):
					ch = a.read(1)
					if ch == b"\x00":
						break
					name += ch

				key = name.decode("utf-8").lower()
				#logging.info("Key: " + key)

				value = a.read(ta[0])
				#logging.info(value)

				if ta[1] == 0:
					value = value.decode("utf-8")
				elif ta[1] == 2:
					# Avoid decode of binary data
					pass

				# Fill in the class attributes
				if key == "title":
					self.title = value
				elif key == "artist":
					self.artist = value
				elif key == "genre":
					self.genre = value
				elif key == "discnumber":
					self.disc_number = value
				elif key == "disc":

					# Ape track fields appear to use fraction format, rather than separate fields for number and total
					# So we need to handle that here for consistency
					if "/" in value:
						self.disc_number, self.disc_total = value.split("/")
					else:
						self.disc_number = value

				elif key == "comment":
					self.comment = value
				elif key == "track":

					# Same deal as with disc number
					if "/" in value:
						self.track_number, self.track_total = value.split("/")
					else:
						self.track_number = value

				elif key == "year":
					self.date = value
				elif key == "album":
					self.album = value
				elif key == "artist":
					self.artist = value
				elif key == "composer":
					self.composer = value
				elif key in ("album artist", "albumartist"):
					self.album_artist = value
				elif key == "label":
					self.label = value
				elif key == "lyrics":
					self.lyrics = value
				elif key == "replaygain_track_gain":
					self.misc["replaygain_track_gain"] = float(value.lower().strip(" db"))
				elif key == "replaygain_track_peak":
					self.misc["replaygain_track_peak"] = float(value)
				elif key == "replaygain_album_gain":
					self.misc["replaygain_album_gain"] = float(value.lower().strip(" db"))
				elif key == "replaygain_album_peak":
					self.misc["replaygain_album_peak"] = float(value)
				elif parse_mbids_from_vorbis(self, key, value):
					pass
				elif key == "cover art (front)":
					# Data appears to have a filename at the start of it, we need to remove to recover a valid picture
					# Im not sure what the actual specification is here

					off = 0
					while off < 64:
						if value[off:off+1] == b"\x00":

							off += 1
							break
						off += 1
					else:
						logging.info("Tag Scanner: Error reading APE album art")
						continue

					self.picture = value[off:]
					self.has_picture = True
					# logging.info(value)

		# Back to start of file to see if we can find sample rate and duration information
		a.seek(0)

		start = a.read(128)
		if start[0:3] == b"MAC":  # Ape files start with MAC
			version = struct.unpack("<h", start[4:6])[0]

			if version >= 3980:
				audio_info = struct.unpack("<IIIHHI", start[56:76])

				self.bit_depth = audio_info[3]
				self.sample_rate = audio_info[5]

				frames = audio_info[2] - 1
				blocks = audio_info[0]

				self.length = (frames * blocks) / self.sample_rate
			else:
				logging.info("Note: Old APE file format version")

		elif ".tta" in self.filepath:
			a.seek(0)
			header = struct.unpack("<4c3H3L", a.read(22))

			if b"".join(header[0:3]) != b"TTA1":
				self.sample_rate = header[7]
				bps = header[6]
				self.bit_depth = bps
				# channels = header[5]
				self.length = header[8] / self.sample_rate
			elif b"".join(header[0:3]) != b"TTA2":
				logging.info("WARNING: TTA2 type TTA file not supported")
				# To do
			else:
				logging.info("WARNING: Does not appear to be a valid TTA file")
		elif ".wv" in self.filepath:
			#  We can handle WavPack files here too
			#  This code likely wont cover all cases as is, I only tested it on a few files

			a.seek(0)

			#  I found that some WavPack files have padding at the beginning
			#  So here I crudely search for the actual start
			off = 0
			while off < file_size - 100:
				if a.read(4) == b"wvpk":
					a.seek(-4, 1)
					b = a.read(32)
					header = struct.unpack("<4cIH2B5I", b)

					sample_rates = [6000, 8000, 9600, 11025, 12000, 16000, 22050, 24000, 32000, 44100, 48000, 64000,
									88200, 96000, 192000]   # Adapted from example in WavPack/cli/wvparser.c
					n = ((header[11] & (15 << 23)) >> 23)   # Does my head in this
					self.sample_rate = sample_rates[n]
					self.length = header[8] / self.sample_rate
					break
			else:
				logging.info("Tag Scanner: Cannot verify WavPack file")
		else:
			logging.info("Tag Scanner: Does not appear to be an APE file")

class Wav(TrackFile):

	def __init__(self, file: str) -> None:
		super().__init__()
		self.filepath = file

	def read(self) -> None:
		if not self.file:
			self.file = Path(self.filepath).open("rb")
		f = self.file

		f.read(12)

		while True:
			wav_type = f.read(4)
			if not wav_type:
				break
			remain = int.from_bytes(f.read(4), "little")

			if wav_type != b"LIST":
				f.seek(remain, io.SEEK_CUR)
			else:
				info = f.read(4)
				if info == b"INFO":
					remain -= 4
					while remain > 0:
						tag_id = f.read(4).decode()
						size = int.from_bytes(f.read(4), "little")
						value = f.read(size)[:-1].decode("unicode_escape")
						if tag_id == "ITRK":
							self.track_number = value
						if tag_id == "IGNR":
							self.genre = value
						if tag_id == "IART":
							self.artist = value
						if tag_id == "INAM":
							self.title = value
						if tag_id == "IPRD":
							self.album = value

						if size % 2 == 1:
							size += 1
							f.read(1)

						remain -= (8 + size)

		with wave.open(self.filepath, "rb") as wav:
			self.sample_rate = wav.getframerate()
			self.length = wav.getnframes() / self.sample_rate


genre_dict = {
	0 : "Blues",
	1 : "Classic Rock",
	2 : "Country",
	3 : "Dance",
	4 : "Disco",
	5 : "Funk",
	6 : "Grunge",
	7 : "Hip-Hop",
	8 : "Jazz",
	9 : "Metal",
	10 : "New Age",
	11 : "Oldies",
	12 : "Other",
	13 : "Pop",
	14 : "R&B",
	15 : "Rap",
	16 : "Reggae",
	17 : "Rock",
	18 : "Techno",
	19 : "Industrial",
	20 : "Alternative",
	21 : "Ska",
	22 : "Death Metal",
	23 : "Pranks",
	24 : "Soundtrack",
	25 : "Euro-Techno",
	26 : "Ambient",
	27 : "Trip-Hop",
	28 : "Vocal",
	29 : "Jazz+Funk",
	30 : "Fusion",
	31 : "Trance",
	32 : "Classical",
	33 : "Instrumental",
	34 : "Acid",
	35 : "House",
	36 : "Game",
	37 : "Sound Clip",
	38 : "Gospel",
	39 : "Noise",
	40 : "Alternative Rock",
	41 : "Bass",
	42 : "Soul",
	43 : "Punk",
	44 : "Space",
	45 : "Meditative",
	46 : "Instrumental Pop",
	47 : "Instrumental Rock",
	48 : "Ethnic",
	49 : "Gothic",
	50 : "Darkwave",
	51 : "Techno-Industrial",
	52 : "Electronic",
	53 : "Pop-Folk",
	54 : "Eurodance",
	55 : "Dream",
	56 : "Southern Rock",
	57 : "Comedy",
	58 : "Cult",
	59 : "Gangsta",
	60 : "Top 40",
	61 : "Christian Rap",
	62 : "Pop/Funk",
	63 : "Jungle",
	64 : "Native US",
	65 : "Cabaret",
	66 : "New Wave",
	67 : "Psychadelic",
	68 : "Rave",
	69 : "Showtunes",
	70 : "Trailer",
	71 : "Lo-Fi",
	72 : "Tribal",
	73 : "Acid Punk",
	74 : "Acid Jazz",
	75 : "Polka",
	76 : "Retro",
	77 : "Musical",
	78 : "Rock & Roll",
	79 : "Hard Rock",
	80 : "Folk",
	81 : "Folk-Rock",
	82 : "National Folk",
	83 : "Swing",
	84 : "Fast Fusion",
	85 : "Bebob",
	86 : "Latin",
	87 : "Revival",
	88 : "Celtic",
	89 : "Bluegrass",
	90 : "Avantgarde",
	91 : "Gothic Rock",
	92 : "Progressive Rock",
	93 : "Psychedelic Rock",
	94 : "Symphonic Rock",
	95 : "Slow Rock",
	96 : "Big Band",
	97 : "Chorus",
	98 : "Easy Listening",
	99 : "Acoustic",
	100 : "Humour",
	101 : "Speech",
	102 : "Chanson",
	103 : "Opera",
	104 : "Chamber Music",
	105 : "Sonata",
	106 : "Symphony",
	107 : "Booty Bass",
	108 : "Primus",
	109 : "Porn Groove",
	110 : "Satire",
	111 : "Slow Jam",
	112 : "Club",
	113 : "Tango",
	114 : "Samba",
	115 : "Folklore",
	116 : "Ballad",
	117 : "Power Ballad",
	118 : "Rhythmic Soul",
	119 : "Freestyle",
	120 : "Duet",
	121 : "Punk Rock",
	122 : "Drum Solo",
	123 : "Acapella",
	124 : "Euro-House",
	125 : "Dance Hall",
	126 : "Goa",
	127 : "Drum & Bass",
	128 : "Club - House",
	129 : "Hardcore",
	130 : "Terror",
	131 : "Indie",
	132 : "BritPop",
	133 : "Negerpunk",
	134 : "Polsk Punk",
	135 : "Beat",
	136 : "Christian Gangsta Rap",
	137 : "Heavy Metal",
	138 : "Black Metal",
	139 : "Crossover",
	140 : "Contemporary Christian",
	141 : "Christian Rock",
	142 : "Merengue",
	143 : "Salsa",
	144 : "Thrash Metal",
	145 : "Anime",
	146 : "JPop",
	147 : "Synthpop",
	148 : "Unknown",
}

class M4a(TrackFile):

	def __init__(self, file: str) -> None:
		super().__init__()
		self.filepath = file
		self.sample_rate = 0 # Unknown sample rate

	def read(self, get_picture: bool = False) -> None:
		if not self.file:
			self.file = Path(self.filepath).open("rb")
		f = self.file

		k = [
			b"moov",
			b"trak",
			b"----",
			b"udta",
			b"meta",
			b"ilst",
			b"mdia",
			b"mdhd",
			b"minf",
			b"stbl",
			b"stsd",
			b"esds",
		]

#		s_name = b""

		def meta_get(f: BufferedReader, size: int) -> bytes:
			start = f.tell()
			f.seek(16, 1)
			data = f.read(size - 8 - 16)
			f.seek(start)
			return data

		def atom(f: BufferedReader, tail: bytes = b"", name: str | bytes = "") -> bool:
#			global s_name

			start = f.tell()
			b_size = f.read(4)
			size = int.from_bytes(b_size, "big")

			name = f.read(4)

			if name == b"":
				return False

			# logging.info("NAME: ", end="")
			# logging.info(tail + b"." + name)

			# Too lazy to parse each sub atom, lets just grab the data out the sub atom and
			# hope the file is formatted normally

			if name == b"\xa9nam":
				self.title = meta_get(f, size).decode().replace("\x00", "")

			if name == b"\xa9alb":
				self.album = meta_get(f, size).decode().replace("\x00", "")

			if name == b"\xa9ART":
				self.artist = meta_get(f, size).decode().replace("\x00", "")

			if name == b"\xa9wrt":
				self.composer = meta_get(f, size).decode().replace("\x00", "")

			if name == b"\xa9cmt":
				self.comment = meta_get(f, size).decode().replace("\x00", "")

			if name == b"\xa9lyr":
				self.lyrics = meta_get(f, size).decode().replace("\x00", "")

			if name == b"\xa9day":
				day = meta_get(f, size).decode().replace("\x00", "")
				if len(day) > 10 and day[10] == "T":
					day = day[:10]
				self.date = day

			if name == b"gnre":
				index = int.from_bytes(meta_get(f, size), "big")
				if index - 1 in genre_dict:
					self.genre = genre_dict[index - 1]

				#self.genre = meta_get(f, size).decode()

			if name == b"\xa9gen":
				self.genre = meta_get(f, size).decode().replace("\x00", "")

			if name == b"aART":
				self.album_artist = meta_get(f, size).decode().replace("\x00", "")

			if name == b"covr":
				self.has_picture = True
				if get_picture:
					self.picture = meta_get(f, size)

			if name == b"trkn":
				self.track_number = int(meta_get(f, size)[3])  # We'll just grab that

			if name == b"disk":  # They spelt disc wrong lol
				self.disc_number = int(meta_get(f, size)[3])

			# if tail[-4:] == b"----":
			#
			#
			#	 if name == b'name':
			#		 s_name = f.read(size - 8)
			#		 f.seek((size - 8) * -1, 1)
			#
			#	 elif name == b'data' and s_name != b"":
			#		 data = f.read(size - 8)
			#		 f.seek((size - 8) * -1, 1)
			#		 logging.info(s_name)
			#		 logging.info(data)

			if name in k:
				if name == b"----":
					f.seek(30, 1)

				if name == b"stsd":
					f.seek(44, 1)

				if name == b"meta":
					f.seek(4, 1)  # The 'meta' atom has some extra space at the start

				if name == b"mdhd":

					data = f.read(size - 8)
					f.seek((size - 8) * -1, 1)
					data = struct.unpack(">iiiiihh", data)
					self.sample_rate = data[3]
					self.length = data[4] / self.sample_rate

				if name == b"esds":
					f.seek(26, 1)
					bitrate = int.from_bytes(f.read(4), "big")
					f.seek(-30, 1)
					self.bit_rate = bitrate // 1000
				else:
					while f.tell() < start + size:
						if not atom(f, tail + b"." + name, name):
							break

			f.seek(start)
			f.seek(size, 1)
			return size != 0

		while atom(f):
			pass
