"""Tauon Music Box - Web interface module"""

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

import hashlib
import html
import io
import json
import logging
import os
import struct
import subprocess
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from typing import TYPE_CHECKING

from tauon.t_modules.t_enums import Backend, PlayingState, StopMode
from tauon.t_modules.t_extra import Timer

if TYPE_CHECKING:
	from typing import Any

	from tauon.t_modules.t_main import AlbumArt, GuiVar, PlayerCtl, Prefs, Strings, Tauon, TrackClass


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	pass


class VorbisMonitor:
	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.reset()
		self.enable: bool = True
		self.synced: bool = False
		self.buffer = io.BytesIO()
		self.tries: int = 0

	def reset(self, tries: int = 0) -> None:
		self.enable = True
		self.synced = False
		self.buffer = io.BytesIO()
		self.tries = tries

	def input(self, data: bytes) -> None:
		if not self.enable:
			return

		b = self.buffer
		b.seek(0, io.SEEK_END)
		b.write(data)

		# Check there's enough data to decode header
		b.seek(0, io.SEEK_END)
		l = b.tell()
		if l < 128:
			logging.info("Not enough data to parse vorbis")
			return

		# Get page length
		b.seek(0, io.SEEK_SET)
		ogg = b.read(4)

		if ogg != b"OggS":
			f = data.find(b"OggS")
			self.reset(self.tries)
			if f > -1:
				logging.info("Ogg stream synced")
				data = data[f:]
				b = self.buffer
				b.write(data)
			else:
				self.tries += 1
				if self.tries > 100:
					logging.info("Giving up looking for OGG pages")
					self.enable = False
				return

			# self.enable = False
			# return

		b.seek(0, io.SEEK_SET)
		header = struct.unpack("<4sBBqIIiB", b.read(27))
		segment_count = header[7]

		# Ensure we can read the segment table
		seg_bytes = b.read(segment_count)
		if len(seg_bytes) < segment_count:
			return  # wait for more data

		segs = seg_bytes

		length = 0
		for s in segs:
			length += s

		length += 27 + header[7]

		if l > length:
			h = b.read(7)
			# logging.info(h)
			if h in {b"\x03vorbis", b"OpusTag"}:
				if h == b"OpusTag":
					b.seek(1, io.SEEK_CUR)

				vendor_length = int.from_bytes(b.read(4), byteorder="little")
				vendor = int.from_bytes(b.read(vendor_length), byteorder="little")
				comment_list_length = int.from_bytes(b.read(4), byteorder="little")

				found_tags = {}
				for i in range(comment_list_length):
					comment_length = int.from_bytes(b.read(4), byteorder="little")
					comment = b.read(comment_length)

					key, value = comment.decode().split("=", 1)

					if key == "title":
						found_tags["title"] = value
					if key == "artist":
						found_tags["artist"] = value
					if key == "year":
						found_tags["year"] = value
					if key == "album":
						found_tags["album"] = value

				line = ""
				if "title" in found_tags:
					line += found_tags["title"]
					if "artist" in found_tags:
						line = found_tags["artist"] + " - " + line

				if self.tauon.radiobox.parse_vorbis_okay():
					self.tauon.pctl.found_tags = found_tags
					self.tauon.pctl.tag_meta = line

				logging.info("Found vorbis comment")
				logging.info(line)

			# Consume page from buffer
			b.seek(length, io.SEEK_SET)
			new = io.BytesIO()
			new.write(b.read())
			self.buffer = new


def send_file(path: str, mime: str, server) -> None:
	range_req = False
	start = 0
	end = None
	range_header = server.headers.get("Range")

	try:
		with open(path, "rb") as f:
			f.seek(0, 2)
			length = f.tell()

			if range_header:
				try:
					unit, value = range_header.split("=", 1)
					if unit.strip().lower() != "bytes" or "," in value:
						raise ValueError
					start_str, end_str = value.split("-", 1)
					if not start_str and not end_str:
						raise ValueError
					if start_str:
						start = int(start_str)
						if start < 0:
							raise ValueError
						end = int(end_str) if end_str else length - 1
						if end < 0:
							raise ValueError
					else:
						# Suffix ranges: bytes=-500 means last 500 bytes
						suffix_length = int(end_str)
						if suffix_length <= 0:
							raise ValueError
						start = max(0, length - suffix_length)
						end = length - 1
					range_req = True
				except (IndexError, ValueError):
					range_req = False
					start = 0
					end = None

			if range_req:
				if start >= length or end is None or end < start:
					server.send_response(416)
					server.send_header("Accept-Ranges", "bytes")
					server.send_header("Content-Range", f"bytes */{length}")
					server.end_headers()
					return
				if end >= length:
					end = length - 1
				chunk_length = end - start + 1
				server.send_response(206)
				server.send_header("Accept-Ranges", "bytes")
				server.send_header("Content-Range", f"bytes {start}-{end}/{length}")
				server.send_header("Content-Length", str(chunk_length))
				server.send_header("Content-Type", mime)
				f.seek(start)
			else:
				server.send_response(200)
				server.send_header("Accept-Ranges", "bytes")
				server.send_header("Content-Type", mime)
				server.send_header("Content-Length", str(length))
				f.seek(0)

			server.end_headers()

			remaining = end - start + 1 if range_req else None
			while True:
				read_size = 65536 if remaining is None else min(65536, remaining)
				if read_size <= 0:
					break
				data = f.read(read_size)
				if not data:
					break
				server.wfile.write(data)
				if remaining is not None:
					remaining -= len(data)
	except OSError:
		server.send_response(404)
		server.end_headers()


def webserve(
	pctl: PlayerCtl,
	prefs: Prefs,
	gui: GuiVar,
	album_art_gen: AlbumArt,
	install_directory: str,
	strings: Strings,
	tauon: Tauon,
) -> int | None:
	if prefs.enable_web is False:
		return 0

	gui.web_running = True

	class Server(BaseHTTPRequestHandler):
		def log_message(self, format: str, *args) -> None:
			logging.info(format % args)

		def send_file(self, path: str, mime: str) -> None:
			self.send_response(200)
			self.send_header("Content-type", mime)
			self.end_headers()

			with open(path, "rb") as f:
				self.wfile.write(f.read())

		def get_track_id(self, track: TrackClass) -> str:
			return hashlib.md5((str(track.index) + track.title + track.artist).encode()).hexdigest()

		def do_GET(self) -> None:
			path = self.path

			# logging.info(self.headers)
			# logging.info(path)

			if path == "/listenalong/":
				self.send_response(302)
				self.send_header("Location", "/listenalong")
				self.end_headers()

			elif path == "/listenalong":
				self.send_file(install_directory + "/templates/radio.html", "text/html")
			elif path == "/favicon.png":
				self.send_file(install_directory + "/assets/icon-64.png", "image/png")
			elif path == "/listenalong/play.svg":
				self.send_file(install_directory + "/templates/play.svg", "image/svg+xml")
			elif path == "/listenalong/pause.svg":
				self.send_file(install_directory + "/templates/pause.svg", "image/svg+xml")
			elif path == "/listenalong/stop.svg":
				self.send_file(install_directory + "/templates/stop.svg", "image/svg+xml")
			elif path == "/radio/radio.js":
				self.send_file(install_directory + "/templates/radio.js", "application/javascript")
			elif path == "/radio/theme.css":
				self.send_file(install_directory + "/templates/theme.css", "text/css")
			elif path == "/radio/logo-bg.png":
				self.send_file(install_directory + "/templates/logo-bg.png", "image/png")

			elif path.startswith("/llapi/audiofile/"):
				value = path[17:]
				track = pctl.playing_object()
				if not track:
					self.send_response(403)
					self.end_headers()
					return
				sid = self.get_track_id(track)
				if sid != value or track.is_network:
					self.send_response(403)
					self.end_headers()
					return
				if not track.fullpath or not os.path.isfile(track.fullpath):
					self.send_response(404)
					self.end_headers()
					return
				mime = "audio/mpeg"
				if track.file_ext == "FLAC":
					mime = "audio/flac"
				if track.file_ext in {"OGG", "OPUS", "OGA"}:
					mime = "audio/ogg"
				if track.file_ext == "M4A":
					mime = "audio/mp4"
				send_file(track.fullpath, mime, self)

			elif path == "/llapi/poll":
				self.send_response(200)
				self.send_header("Content-type", "application/json")

				ip = self.client_address[0]
				timer = tauon.listen_alongers.get(ip)
				if not timer:
					tauon.listen_alongers[ip] = Timer()
				else:
					timer.set()

				track = pctl.playing_object()
				if track is None:
					data = {"status": 0}
				else:
					data = {
						"status": pctl.playing_state,
						"id": self.get_track_id(track),
						"position": pctl.playing_time,
						"duration": track.length,
						"title": track.title,
						"artist": track.artist,
					}
				self.end_headers()
				data = json.dumps(data).encode()
				self.wfile.write(data)

			elif path.startswith("/llapi/picture/"):
				value = path[15:]
				track = pctl.playing_object()
				if not track:
					self.send_response(403)
					self.end_headers()
					return
				sid = self.get_track_id(track)
				if sid != value or track.is_network:
					self.send_response(403)
					self.end_headers()
					return

				try:
					base64 = album_art_gen.get_base64(track, (300, 300)).decode()
					data = {"image_data": base64}
				except Exception:
					logging.exception("No image data")
					data = {"image_data": "None"}

				lyrics = tauon.synced_to_static_lyrics.get(track)
				lyrics = html.escape(lyrics).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")
				data["lyrics"] = lyrics

				data = json.dumps(data).encode()
				self.send_response(200)
				self.send_header("Content-type", "application/json")
				self.send_header("Content-length", str(len(data)))
				self.end_headers()
				self.wfile.write(data)

			else:
				self.send_response(404)
				self.end_headers()
				self.wfile.write(b"404 Not found")

	try:
		httpd = ThreadedHTTPServer(("0.0.0.0", prefs.metadata_page_port), Server)
		tauon.radio_server = httpd
		httpd.serve_forever()
		httpd.server_close()
	except OSError as e:
		if str(e) == "[Errno 98] Address already in use":
			logging.error("Not starting radio page server, is another Tauon instance already running?")  # noqa: TRY400
		else:
			logging.exception("Unknown OSError starting radio page server!")
	except Exception:
		logging.exception("Failed starting radio page server!")


def webserve2(pctl: PlayerCtl, album_art_gen: AlbumArt, tauon: Tauon) -> None:
	play_timer = Timer()

	class Server(BaseHTTPRequestHandler):
		def log_message(self, format: str, *args) -> None:
			logging.info(format % args)

		def run_command(self, callback) -> None:
			self.send_response(200)
			# self.send_header("Content-type", "application/json")
			self.end_headers()
			callback()
			self.wfile.write(b"OK")

		def stream_opus_file(self, track: TrackClass) -> None:
			ffmpeg_path = tauon.get_ffmpeg()
			if ffmpeg_path is None:
				self.send_response(503)
				self.end_headers()
				self.wfile.write(b"ffmpeg unavailable")
				return

			command = [str(ffmpeg_path), "-v", "error"]
			if track.start_time:
				command.extend(["-ss", str(track.start_time)])
				if track.length > 0:
					command.extend(["-t", str(track.length)])
			command.extend([
				"-i", track.fullpath,
				"-vn",
				"-c:a", "libopus",
				"-b:a", "84k",
				"-f", "ogg",
				"-",
			])

			try:
				encoder = subprocess.Popen(
					command,
					stdin=subprocess.DEVNULL,
					stdout=subprocess.PIPE,
					stderr=subprocess.DEVNULL,
				)
			except OSError:
				logging.exception("Failed to start ffmpeg for /api1/fileopus")
				self.send_response(500)
				self.end_headers()
				self.wfile.write(b"Transcode start failed")
				return

			if encoder.stdout is None:
				self.send_response(500)
				self.end_headers()
				self.wfile.write(b"Transcode stream unavailable")
				return

			self.send_response(200)
			self.send_header("Content-type", "audio/ogg")
			self.send_header("Content-Disposition", 'attachment; filename="track.opus"')
			self.send_header("Connection", "close")
			self.end_headers()
			self.close_connection = True

			try:
				while True:
					data = encoder.stdout.read(65536)
					if not data:
						break
					self.wfile.write(data)
			except (BrokenPipeError, ConnectionResetError):
				pass
			finally:
				encoder.stdout.close()
				if encoder.poll() is None:
					encoder.terminate()
					try:
						encoder.wait(timeout=1)
					except subprocess.TimeoutExpired:
						encoder.kill()
						encoder.wait(timeout=1)

		def toggle_album_shuffle(self) -> None:
			pctl.album_shuffle_mode ^= True
			tauon.gui.update += 1

		def parse_trail(self, text: str) -> tuple[list[str], dict[str, str]]:
			params: dict[str, str] = {}
			both = text.split("?")
			levels = both[0].split("/")
			if len(both) > 1:
				pairs = both[1].split("&")
				for p in pairs:
					if "=" not in p:
						continue
					aa, bb = p.split("=", 1)
					params[aa] = bb

			return levels, params

		def get_track(
			self,
			track_position: int,
			playlist_index: int | None = None,
			track: TrackClass | None = None,
			album_id: int = -1,
		) -> dict[str, int | str | bool]:
			if track is None:
				if playlist_index is None:
					playlist = pctl.multi_playlist[pctl.active_playlist_playing].playlist_ids
				else:
					playlist = pctl.multi_playlist[playlist_index].playlist_ids
				track_id = playlist[track_position]
				track = pctl.get_track(track_id)

			data: dict[str, int | str | bool] = {}
			data["title"] = track.title
			data["artist"] = track.artist
			data["album"] = track.album
			data["album_artist"] = track.album_artist
			if not track.album_artist:
				data["album_artist"] = track.artist
			data["duration"] = int(track.length * 1000)
			data["id"] = track.index
			data["position"] = track_position
			data["path"] = track.fullpath
			data["album_id"] = album_id
			data["has_lyrics"] = track.lyrics != ""
			data["track_number"] = str(track.track_number).lstrip("0")
			data["can_download"] = not track.is_cue and not track.is_network

			return data

		def do_GET(self) -> None:
			path = self.path
			# logging.info(self.headers)
			if tauon.remote_limited and not tauon.chrome_mode:
				self.send_response(404)
				self.end_headers()
				self.wfile.write(b"404 Not found")
				return
			if tauon.remote_limited and (
				not path.startswith("/api1/pic/medium/")
				and not path.startswith("/api1/file/")
				and not path.startswith("/api1/fileopus")
			):
				self.send_response(404)
				self.end_headers()
				self.wfile.write(b"404 Not found")
				return

			if path.startswith("/api1/pic/small/"):
				value = path[16:]
				if value.isdigit() and int(value) in pctl.master_library:
					track = pctl.get_track(int(value))
					raw = album_art_gen.save_thumb(track, (75, 75), "")
					if raw:
						self.send_response(200)
						self.send_header("Content-type", "image/jpg")
						self.end_headers()
						self.wfile.write(raw.read())
					else:
						self.send_response(404)
						self.end_headers()
						self.wfile.write(b"No image found")

				else:
					self.send_response(404)
					self.end_headers()
					self.wfile.write(b"Invalid parameter")

			elif path.startswith("/api1/pic/medium/"):
				value = path[17:]
				logging.info(value)
				if value.isdigit() and int(value) in pctl.master_library:
					track = pctl.get_track(int(value))
					raw = album_art_gen.save_thumb(track, (1000, 1000), "")
					if raw:
						self.send_response(200)
						self.send_header("Content-type", "image/jpg")
						self.end_headers()
						self.wfile.write(raw.read())
					else:
						self.send_response(404)
						self.end_headers()
						self.wfile.write(b"No image found")

				else:
					self.send_response(404)
					self.end_headers()
					self.wfile.write(b"Invalid parameter")

			elif path.startswith("/api1/lyrics/"):
				value = path[13:]
				if value.isdigit() and int(value) in pctl.master_library:
					track = pctl.get_track(int(value))
					data = {}
					data["track_id"] = track.index
					data["lyrics_text"] = track.lyrics

					self.send_response(200)
					self.send_header("Content-type", "application/json")
					self.end_headers()
					data = json.dumps(data).encode()
					self.wfile.write(data)
				else:
					self.send_response(404)
					self.end_headers()
					self.wfile.write(b"Invalid parameter")

			# elif path.startswith("/api1/stream/"):
			# param = path[13:]
			#
			# if param.isdigit() and int(param) in pctl.master_library:
			# 	track = pctl.master_library[int(param)]
			# 	mime = "audio/mpeg"
			# 	#mime = "audio/ogg"
			# 	self.send_response(200)
			# 	self.send_header("Content-type", mime)
			# 	self.end_headers()
			#
			# 	cmd = ["ffmpeg", "-i", track.fullpath, "-c:a", "libopus", "-f", "ogg", "-"]
			# 	#cmd = ["ffmpeg", "-i", track.fullpath, "-c:a", "libvorbis", "-f", "ogg", "-"]
			# 	#cmd = ["ffmpeg", "-i", track.fullpath, "-c:a", "libmp3lame", "-f", "mp3", "-"]
			# 	encoder = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
			# 	while True:
			# 		data = encoder.stdout.read(1024)
			# 		if data:
			# 			self.wfile.write(data)
			elif path.startswith("/api1/playinghit/"):
				param = path[17:]
				if param.isdigit() and int(param) in pctl.master_library:
					t = play_timer.hit()
					if 0 < t < 5:
						tauon.star_store.add(int(param), t)

				self.send_response(200)
				self.send_header("Content-type", "text/plain")
				self.end_headers()
				self.wfile.write(b"OK")

			elif path.startswith("/api1/file/"):
				param = path[11:]

				# logging.info(self.headers)
				play_timer.hit()

				if param.isdigit() and int(param) in pctl.master_library:
					track = pctl.master_library[int(param)]
					if not track.fullpath or not os.path.isfile(track.fullpath):
						self.send_response(404)
						self.end_headers()
						self.wfile.write(b"File unavailable")
					else:
						mime = "audio/mpeg"
						if track.file_ext == "FLAC":
							mime = "audio/flac"
						if track.file_ext in {"OGG", "OPUS", "OGA"}:
							mime = "audio/ogg"
						if track.file_ext == "M4A":
							mime = "audio/mp4"
						send_file(track.fullpath, mime, self)
				else:
					self.send_response(404)
					self.end_headers()
					self.wfile.write(b"Invalid parameter")

			elif path.startswith("/api1/fileopus/"):
				param = path[15:].split("?", 1)[0]

				play_timer.hit()

				if param.isdigit() and int(param) in pctl.master_library:
					track = pctl.master_library[int(param)]
					if not track.fullpath or not os.path.isfile(track.fullpath):
						self.send_response(404)
						self.end_headers()
						self.wfile.write(b"File unavailable")
					else:
						self.stream_opus_file(track)
				else:
					self.send_response(404)
					self.end_headers()
					self.wfile.write(b"Invalid parameter")

			elif path.startswith("/api1/start/"):
				levels, _ = self.parse_trail(path)
				if len(levels) == 5:
					playlist = levels[3]
					position = levels[4]
					if playlist.isdigit() and position.isdigit():
						position = int(position)
						playlist = int(playlist)
						pl = tauon.id_to_pl(int(playlist))
						if pl is not None and pl < len(pctl.multi_playlist):
							playlist = pctl.multi_playlist[pl].playlist_ids
							if position < len(playlist):
								tauon.switch_playlist(pl, cycle=False, quiet=True)
								pctl.jump(playlist[position], position)

				self.send_response(200)
				self.send_header("Content-type", "text/plain")
				self.end_headers()
				self.wfile.write(b"OK")

			elif path == "/api1/play":
				self.run_command(tauon.pctl.play)
			elif path == "/api1/pause":
				self.run_command(tauon.pctl.pause_only)
			elif path == "/api1/stop":
				self.run_command(tauon.pctl.stop)
			elif path == "/api1/next":
				self.run_command(tauon.pctl.advance)
			elif path == "/api1/back":
				self.run_command(tauon.pctl.back)
			elif path == "/api1/shuffle":
				self.run_command(tauon.toggle_random)
			elif path == "/api1/album-shuffle":
				self.run_command(self.toggle_album_shuffle)
			elif path == "/api1/repeat":
				self.run_command(tauon.toggle_repeat)
			elif path == "/api1/auto-stop":
				if tauon.pctl.stop_mode == StopMode.OFF:
					tauon.pctl.stop_mode = StopMode.TRACK
				else:
					tauon.pctl.stop_mode = StopMode.OFF
				tauon.gui.update += 1
			elif path == "/api1/version":
				data = {"version": 1}
				self.send_response(200)
				self.send_header("Content-type", "application/json")
				self.end_headers()
				data = json.dumps(data).encode()
				self.wfile.write(data)

			elif path == "/api1/playlists":
				l = []
				for item in pctl.multi_playlist:
					p = {}
					p["name"] = item.title
					p["id"] = str(item.uuid_int)
					p["count"] = len(item.playlist_ids)
					l.append(p)
				data = {"playlists": l}
				self.send_response(200)
				self.send_header("Content-type", "application/json")
				self.end_headers()
				data = json.dumps(data).encode()
				self.wfile.write(data)

			elif path.startswith("/api1/albumtracks/"):
				# Get tracks that appear in an album /albumtracks/plid/albumid
				levels, _ = self.parse_trail(path)
				l = []
				if len(levels) == 5 and levels[3].isdigit() and levels[4].isdigit():
					pl = tauon.id_to_pl(int(levels[3]))
					if pl is not None:
						_, album, _ = tauon.get_album_info(int(levels[4]), pl)
						# logging.info(album)
						for p in album:
							l.append(self.get_track(p, pl, album_id=int(levels[4])))

				data = {"tracks": l}
				self.send_response(200)
				self.send_header("Content-type", "application/json")
				self.end_headers()
				data = json.dumps(data).encode()
				self.wfile.write(data)

			elif path.startswith("/api1/trackposition/"):
				# get track /trackposition/plid/playlistposition
				levels, _ = self.parse_trail(path)
				if len(levels) == 5 and levels[3].isdigit() and levels[4].isdigit():
					pl = tauon.id_to_pl(int(levels[3]))
					if pl is not None:
						data = self.get_track(int(levels[4]), pl)

						playlist = pctl.multi_playlist[pl].playlist_ids
						p = int(levels[4])
						if p < len(playlist):
							track = pctl.get_track(playlist[p])
							while True:
								if p < 0 or pctl.get_track(playlist[p]).parent_folder_path != track.parent_folder_path:
									p += 1
									break
								p -= 1
							data["album_id"] = p

							self.send_response(200)
							self.send_header("Content-type", "application/json")
							self.end_headers()
							data = json.dumps(data).encode()
							self.wfile.write(data)
						else:
							self.send_response(404)
							self.send_header("Content-type", "text/plain")
							self.end_headers()
							self.wfile.write(b"404 invalid track position")
					else:
						self.send_response(404)
						self.send_header("Content-type", "text/plain")
						self.end_headers()
						self.wfile.write(b"404 playlist not found")
				else:
					self.send_response(404)
					self.send_header("Content-type", "text/plain")
					self.end_headers()
					self.wfile.write(b"404 invalid track")

			elif path.startswith("/api1/setvolume/"):
				key = path[16:]
				if key.isdigit():
					volume = int(key)
					volume = max(volume, 0)
					volume = min(volume, 100)
					pctl.player_volume = volume
					pctl.set_volume()

				self.send_response(200)
				self.send_header("Content-type", "text/plain")
				self.end_headers()
				self.wfile.write(b"OK")

			elif path.startswith("/api1/setvolumerel/"):
				key = path[19:]
				if key.lstrip("-").isdigit() and key.count("-") < 2:
					volume = pctl.player_volume + int(key)
					volume = max(volume, 0)
					volume = min(volume, 100)
					pctl.player_volume = volume
					pctl.set_volume()

				self.send_response(200)
				self.send_header("Content-type", "text/plain")
				self.end_headers()
				self.wfile.write(b"OK")

			elif path.startswith("/api1/seek1k/"):
				key = path[13:]
				if key.isdigit():
					pctl.seek_decimal(int(key) / 1000)

				self.send_response(200)
				self.send_header("Content-type", "text/plain")
				self.end_headers()
				self.wfile.write(b"OK")

			elif path.startswith("/api1/seek/"):
				key = path[11:]
				if key.isdigit():
					pctl.seek_time(int(key) / 1000)

				self.send_response(200)
				self.send_header("Content-type", "text/plain")
				self.end_headers()
				self.wfile.write(b"OK")

			elif path.startswith("/api1/tracklist/"):
				# Return all tracks in a playlist /tracklist/plid
				key = path[16:]
				l = []
				if key.isdigit():
					pl = tauon.id_to_pl(int(key))
					if pl is not None and pl < len(pctl.multi_playlist):
						playlist = pctl.multi_playlist[pl].playlist_ids
						parent = ""
						album_id = 0
						for i, id in enumerate(playlist):
							tr = pctl.get_track(id)
							if i == 0:
								parent = tr.parent_folder_path
							elif parent != tr.parent_folder_path:
								parent = tr.parent_folder_path
								album_id = i

							l.append(self.get_track(i, pl, album_id=album_id))

				data = {"tracks": l}
				self.send_response(200)
				self.send_header("Content-type", "application/json")
				self.end_headers()
				data = json.dumps(data).encode()
				self.wfile.write(data)

			elif path.startswith("/api1/albums/"):
				# Returns lists of tracks that are start of albums /albums/plid
				key = path[13:]
				l = []
				if key.isdigit():
					pl = tauon.id_to_pl(int(key))
					if pl is not None:
						dex = tauon.reload_albums(True, pl)
						# logging.info(dex)
						for a in dex:
							l.append(self.get_track(a, pl, album_id=a))

				data = {"albums": l}
				self.send_response(200)
				self.send_header("Content-type", "application/json")
				self.end_headers()
				data = json.dumps(data).encode()
				self.wfile.write(data)

			elif path == "/api1/status":
				self.send_response(200)
				self.send_header("Content-type", "application/json")
				self.end_headers()
				data = {
					"status": "stopped",
					"inc": pctl.db_inc,
					"shuffle": pctl.random_mode is True,
					"album_shuffle": pctl.album_shuffle_mode is True,
					"repeat": pctl.repeat_mode is True,
					"progress": 0,
					"auto_stop": tauon.pctl.stop_mode != StopMode.OFF,
					"volume": pctl.player_volume,
					"playlist": str(tauon.get_playing_playlist_id()),
					"playlist_length": len(pctl.multi_playlist[pctl.active_playlist_playing].playlist_ids),
				}
				if pctl.playing_state == PlayingState.PLAYING:
					data["status"] = "playing"
				if pctl.playing_state == PlayingState.PAUSED:
					data["status"] = "paused"
				track = pctl.playing_object()
				if track:
					data["id"] = track.index
					data["title"] = track.title
					data["artist"] = track.artist
					data["album"] = track.album
					data["progress"] = round(pctl.playing_time * 1000)
					data["track"] = self.get_track(0, 0, track)

				p = pctl.playlist_playing_position
				data["position"] = p
				data["album_id"] = 0
				playlist = pctl.playing_playlist()

				if track is not None and p < len(playlist):
					while True:
						if p < 0 or pctl.get_track(playlist[p]).parent_folder_path != track.parent_folder_path:
							p += 1
							break
						p -= 1
					data["album_id"] = p

				data = json.dumps(data).encode()
				self.wfile.write(data)

			else:
				self.send_response(404)
				self.end_headers()
				self.wfile.write(b"404 Not found")
			tauon.wake()

	try:
		httpd = ThreadedHTTPServer(("0.0.0.0", 7814), Server)
		httpd.serve_forever()
		httpd.server_close()
	except OSError as e:
		if str(e) == "[Errno 98] Address already in use":
			logging.error("Not starting web api server, is another Tauon instance already running?")  # noqa: TRY400
		else:
			logging.exception("Unknown OSError starting web api server!")
	except Exception:
		logging.exception("Failed starting web api server!")


def controller(tauon: Tauon) -> None:
	import base64

	class Server(BaseHTTPRequestHandler):
		def log_message(self, format, *args) -> None:
			logging.info(format % args)

		def do_GET(self) -> None:
			path = self.path
			if not path.startswith("/open/"):
				path = path.rstrip("/")

			if path == "/raise":
				tauon.request_raise()
			if path == "/reloadtheme":
				tauon.gui.reload_theme = True
				tauon.gui.update += 1
			if path == "/playpause":
				if tauon.pctl.playing_state == PlayingState.STOPPED:
					tauon.pctl.play()
				else:
					tauon.pctl.pause()
			if path == "/play":
				tauon.pctl.play()
			if path == "/pause":
				tauon.pctl.pause_only()
			if path == "/stop":
				tauon.pctl.stop()
			if path == "/next":
				tauon.pctl.advance()
			if path == "/previous":
				tauon.pctl.back()
			if path == "/shuffle":
				tauon.toggle_random()
			if path == "/repeat":
				tauon.toggle_repeat()
			if path == "/randomalbum":
				tauon.random_album()
			if path.startswith("/open/"):
				rest = path[6:]
				try:
					path = base64.urlsafe_b64decode(rest.encode()).decode()
				except Exception:
					logging.exception("Invalid /open/ payload")
					self.send_response(400)
					self.end_headers()
					return
				tauon.open_uri(path)

			self.send_response(200)
			self.end_headers()
			tauon.wake()

	logging.info("Start controller server")
	try:
		httpd = HTTPServer(("127.0.0.1", 7813), Server)
		httpd.serve_forever()
		httpd.server_close()
	except OSError as e:
		if str(e) == "[Errno 98] Address already in use":
			logging.error("Not starting controller webserver, is another Tauon instance already running?")
		else:
			logging.exception("Unknown OSError starting controller server!")
	except Exception:
		logging.exception("Failed starting controller server!")


def authserve(tauon: Tauon) -> None:
	class Server(BaseHTTPRequestHandler):
		def log_message(self, format: str, *args) -> None:
			logging.info(format % args)

		def do_GET(self) -> None:
			code = ""
			path = self.path
			# if path.startswith("/tidalredir"):
			# 	self.send_response(200)
			# 	self.send_header("Content-type", "text/plain")
			# 	self.end_headers()
			#
			# 	tauon.tidal.login2(path)
			# 	self.wfile.write(b"You can close this now and return to Tauon Music Box")

			if path.startswith("/spotredir"):
				self.send_response(200)
				self.send_header("Content-type", "text/plain")
				self.end_headers()
				code = path.split("code=")
				if len(code) > 1:
					code = code[1]
					self.wfile.write(_("You can close this now and return to Tauon Music Box").encode("UTF-8"))
				tauon.wake()

			else:
				self.send_response(400)
				self.end_headers()

			if code:
				tauon.spot_ctl.paste_code(code)

	httpd = HTTPServer(("127.0.0.1", 7811), Server)
	httpd.serve_forever()
	httpd.server_close()


def stream_proxy(tauon: Tauon) -> None:
	class Server(BaseHTTPRequestHandler):
		def log_message(self, format: str, *args: Any) -> None:
			logging.info(format % args)

		def do_GET(self) -> None:
			self.send_response(200)
			self.send_header("Content-type", "audio/ogg")
			self.end_headers()

			position = 0
			tauon.vb.reset()

			while True:
				if not tauon.stream_proxy.download_running:
					return

				while position < tauon.stream_proxy.c:
					if position not in tauon.stream_proxy.chunks:
						logging.info("The buffer was deleted too soon!")
						return

					self.wfile.write(tauon.stream_proxy.chunks[position])

					if tauon.prefs.backend == Backend.PHAZOR:
						tauon.vb.input(tauon.stream_proxy.chunks[position])

					position += 1

				time.sleep(0.01)

	httpd = HTTPServer(("127.0.0.1", 7812), Server)
	httpd.serve_forever()
	httpd.server_close()
