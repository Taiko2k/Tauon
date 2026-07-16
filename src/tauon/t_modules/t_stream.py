"""Tauon Music Box - URL stream download and encoding module"""

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

import copy
import datetime
import io
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from queue import Empty, Queue

import mutagen

from tauon.t_modules.t_enums import Backend
from tauon.t_modules.t_extra import filename_safe

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from subprocess import Popen
	from urllib.request import _UrlopenRet

	from tauon.t_modules.t_main import Tauon


class StreamEnc:
	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.download_running = False
		self.encode_running = False
		self.pump_running = False
		self.feed_running = False

		self.download_process = False
		self.abort = False

		self.s_name = ""
		self.s_bitrate = ""
		self.s_genre = ""
		self.s_description = ""
		self.s_mime = ""
		self.s_format = ""

		self.chunks = {}
		self.c = 0
		self.url = ""
		self.request_id = 0
		self.download_response = None
		self.decoder_process: subprocess.Popen[bytes] | None = None
		self.record_decoder_process: subprocess.Popen[bytes] | None = None
		self.record_encoder_process: subprocess.Popen[bytes] | None = None

	def state_log(self) -> str:
		return (
			f"request_id={self.request_id} abort={self.abort} "
			f"download_running={self.download_running} encode_running={self.encode_running} "
			f"pump_running={self.pump_running} feed_running={self.feed_running} "
			f"chunks={self.c} response_open={self.download_response is not None} "
			f"decoder_running={self.decoder_process is not None and self.decoder_process.poll() is None} "
			f"record_decoder_running={self.record_decoder_process is not None and self.record_decoder_process.poll() is None} "
			f"record_encoder_running={self.record_encoder_process is not None and self.record_encoder_process.poll() is None}"
		)

	def stop(self) -> None:
		logging.info(f"Radio stream stop requested: {self.state_log()}")
		if self.tauon.radiobox.websocket:
			self.tauon.radiobox.websocket.close()
			logging.info("Websocket closed")

		self.abort = True
		self.feed_running = False
		if self.download_response is not None:
			try:
				self.download_response.close()
				logging.info("Closed radio stream response")
			except Exception:
				logging.exception("Failed to close radio stream response")
			self.download_response = None
		self.stop_process(self.decoder_process, "radio decoder")
		self.decoder_process = None
		self.stop_process(self.record_decoder_process, "radio recording decoder")
		self.record_decoder_process = None
		if self.record_encoder_process is not None:
			self.close_pipe(self.record_encoder_process.stdin, "radio recording encoder stdin")
		self.tauon.radiobox.loaded_url = None
		logging.info(f"Radio stream stop flagged: {self.state_log()}")

	def ffmpeg_popen(
		self,
		cmd: list[str],
		stdin: int | None = None,
		stdout: int | None = None,
	) -> subprocess.Popen[bytes]:
		kwargs = {
			"stdin": stdin,
			"stdout": stdout,
			"stderr": subprocess.DEVNULL,
		}
		if self.tauon.windows:
			startupinfo = subprocess.STARTUPINFO()
			startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
			kwargs["startupinfo"] = startupinfo
			kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
		return subprocess.Popen(cmd, **kwargs)

	def close_pipe(self, pipe, label: str) -> None:
		if pipe is None:
			return
		try:
			pipe.close()
			logging.info(f"Closed {label}")
		except BrokenPipeError:
			logging.info(f"{label} already closed")
			pass
		except Exception:
			logging.exception("Failed to close %s", label)

	def stop_process(self, process: subprocess.Popen[bytes] | None, label: str, timeout: float = 0.4) -> None:
		if process is None or process.poll() is not None:
			if process is not None:
				logging.info(f"{label} already stopped with return code {process.poll()}")
			return
		logging.info(f"Stopping {label} process")
		try:
			process.terminate()
		except Exception:
			logging.exception("Failed to terminate %s", label)
		try:
			process.wait(timeout=timeout)
		except subprocess.TimeoutExpired:
			try:
				process.kill()
			except Exception:
				logging.exception("Failed to kill %s", label)
			try:
				process.wait(timeout=timeout)
			except Exception:
				logging.exception("Failed to wait for killed %s", label)
		except Exception:
			logging.exception("Failed to wait for %s", label)

	def finish_encoder(self, encoder: subprocess.Popen[bytes], timeout: float = 4) -> None:
		self.close_pipe(encoder.stdin, "encoder stdin")
		try:
			encoder.wait(timeout=timeout)
		except subprocess.TimeoutExpired:
			logging.warning("Encoder timed out")
			self.stop_process(encoder, "encoder")
		except Exception:
			logging.exception("Failed to wait for encoder")
			self.stop_process(encoder, "encoder")

	def read_stdout(
		self,
		process: subprocess.Popen[bytes],
		output: Queue[bytes],
		read_size: int,
		label: str,
		request_id: int,
	) -> None:
		logging.info(f"{label} reader started for request {request_id}")
		try:
			while not self.abort and self.request_id == request_id:
				data = process.stdout.read(read_size)
				if data:
					output.put(data)
				elif data == b"":
					logging.info(f"{label} reader got EOF for request {request_id}")
					break
				else:
					time.sleep(0.005)
		except (OSError, ValueError):
			logging.info(f"{label} reader stopped after pipe close for request {request_id}")
		except Exception:
			logging.exception("%s reader thread crashed", label)
		finally:
			logging.info(
				f"{label} reader exiting for request {request_id}; "
				f"current_request={self.request_id} abort={self.abort} queue_size={output.qsize()}"
			)

	def wait_until_idle(self, request_id: int, timeout: float = 5) -> bool:
		start = time.monotonic()
		next_log = start
		logging.info(f"Waiting for radio stream idle before request {request_id}: {self.state_log()}")
		while self.download_running or self.encode_running or self.pump_running:
			if self.request_id != request_id:
				logging.info(
					f"Radio stream idle wait abandoned for request {request_id}; "
					f"current request is {self.request_id}: {self.state_log()}"
				)
				return False
			now = time.monotonic()
			if now >= next_log:
				logging.info(f"Still waiting for radio stream idle: {self.state_log()}")
				next_log = now + 0.5
			if now - start > timeout:
				logging.warning(f"Timed out waiting for previous radio stream to stop: {self.state_log()}")
				return False
			time.sleep(0.01)
		logging.info(f"Radio stream is idle before request {request_id}")
		return True

	def start_download(self, url: str, request_id: int = 0) -> bool:
		logging.info(f"Radio stream start_download request={request_id} url={url}")
		self.abort = True
		self.request_id = request_id
		if not self.wait_until_idle(request_id):
			logging.warning(f"Radio stream start_download failed waiting for idle: {self.state_log()}")
			return False

		self.__init__(self.tauon)
		self.request_id = request_id

		self.url = url
		result = self.start_request(url, request_id)
		if not result:
			logging.warning(f"Radio stream start_request failed for request {request_id}")
			return False

		self.download_process = threading.Thread(target=self.pump)
		self.download_process.daemon = True
		self.download_process.start()
		logging.info(f"Radio stream pump thread started for request {request_id}")
		return True

	def start_request(self, url: str, request_id: int) -> bool:
		def NiceToICY(self) -> None:
			class InterceptedHTTPResponse:
				pass

			if not url.endswith(".ts"):
				line = self.fp.readline().replace(b"ICY 200 OK\r\n", b"HTTP/1.0 200 OK\r\n")
			else:
				line = self.fp.readline()
			InterceptedSelf = InterceptedHTTPResponse()
			InterceptedSelf.fp = io.BufferedReader(io.BytesIO(line))
			InterceptedSelf.debuglevel = self.debuglevel
			InterceptedSelf._close_conn = self._close_conn
			return ORIGINAL_HTTP_CLIENT_READ_STATUS(InterceptedSelf)

		ORIGINAL_HTTP_CLIENT_READ_STATUS = urllib.request.http.client.HTTPResponse._read_status
		urllib.request.http.client.HTTPResponse._read_status = NiceToICY

		retry = 5
		while True:
			try:
				urllib.request.http.client.HTTPResponse._read_status = NiceToICY
				r = urllib.request.Request(url)
				# r.add_header('GET', '1')
				if not url.endswith(".ts"):
					r.add_header("Icy-MetaData", "1")
				r.add_header("User-Agent", self.tauon.t_agent)
				logging.info("Open URL.....")
				r = urllib.request.urlopen(r, timeout=20, context=self.tauon.tls_context)
				self.download_response = r
				logging.info(f"URL opened for radio request {request_id}; headers={dict(r.info())}")
				if self.abort or self.request_id != request_id:
					logging.info(
						f"Closing newly opened radio response for stale request {request_id}; "
						f"current_request={self.request_id} abort={self.abort}"
					)
					r.close()
					if self.download_response is r:
						self.download_response = None
					return False

			except Exception as e:
				# TODO(Martin): Specify the exception better and turn the top part into debug statements, then only throw except when Connection fails below
				logging.exception("URL error...")
				retry -= 1
				if retry > 0 and "Temporary" in str(e):
					time.sleep(2)
					logging.debug("RETRYING...")
					continue
				logging.error("Connection failed")
				self.tauon.show_message(_("Failed to establish a connection"), str(e), mode="error")
				return False
			finally:
				urllib.request.http.client.HTTPResponse._read_status = ORIGINAL_HTTP_CLIENT_READ_STATUS
			break

		self.download_process = threading.Thread(target=self.run_download, args=([r]))
		self.download_process.daemon = True
		self.download_process.start()
		self.download_running = True
		logging.info(f"Radio stream download thread started for request {request_id}")
		return True

	def pump(self) -> None:
		logging.info(f"Radio pump starting: {self.state_log()}")
		aud = self.tauon.aud
		if self.tauon.prefs.backend != Backend.PHAZOR or not aud:
			logging.error("Radio error: Phazor not loaded")
			return
		self.pump_running = True

		rate = str(self.tauon.prefs.samplerate)
		# fmt:off
		cmd = [
			str(self.tauon.get_ffmpeg()),
			"-loglevel", "quiet",
			"-i", "pipe:0",
			"-acodec", "pcm_s16le",
			"-f", "s16le",
			"-ac", "2",
			"-ar", rate,
			"-",
		]
		# fmt:on

		decoder = self.ffmpeg_popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		self.decoder_process = decoder

		raw_audio = None
		max_read = 10000
		request_id = self.request_id
		raw_queue: Queue[bytes] = Queue()
		self.tauon.vb.reset()

		def feed(decoder: Popen[bytes]) -> None:
			position = 0
			self.feed_running = True
			logging.info(f"Radio feeder starting for request {request_id}")
			try:
				while True:
					if position < self.tauon.stream_proxy.c:
						if position not in self.tauon.stream_proxy.chunks:
							logging.info("The buffer was deleted too soon!")
							break

						chunk = self.chunks[position]
						try:
							decoder.stdin.write(chunk)
						except (BrokenPipeError, OSError, ValueError):
							break
						self.tauon.vb.input(self.tauon.stream_proxy.chunks[position])
						position += 1
					else:
						time.sleep(0.01)
					if self.abort or not self.pump_running or not self.feed_running:
						break
			except Exception:
				logging.exception("Feed not running!")
			finally:
				self.feed_running = False
				self.close_pipe(decoder.stdin, "decoder stdin")
			logging.info(
				f"Radio feeder exiting for request {request_id}; "
				f"position={position} chunks={self.c} abort={self.abort} pump_running={self.pump_running}"
			)

		feeder = threading.Thread(target=feed, args=[decoder])
		feeder.daemon = True
		feeder.start()

		reader = threading.Thread(target=self.read_stdout, args=(decoder, raw_queue, max_read, "Radio decoder", request_id))
		reader.daemon = True
		reader.start()

		try:
			last_wait_log = time.monotonic()
			while True:
				if not self.tauon.stream_proxy.download_running or self.abort or self.request_id != request_id:
					logging.info(
						f"Radio pump break for request {request_id}: "
						f"download_running={self.tauon.stream_proxy.download_running} "
						f"abort={self.abort} current_request={self.request_id}"
					)
					break
				if raw_audio is None:
					try:
						raw_audio = raw_queue.get(timeout=0.01)
					except Empty:
						if decoder.poll() is not None:
							logging.info(f"Radio decoder process ended with code {decoder.poll()} for request {request_id}")
							break
						now = time.monotonic()
						if now - last_wait_log > 1:
							logging.info(
								f"Radio pump waiting for decoded audio request={request_id} "
								f"chunks={self.c} raw_queue={raw_queue.qsize()} decoder_poll={decoder.poll()}"
							)
							last_wait_log = now
						continue
				if raw_audio:
					r = aud.feed_ready(max_read)
					if r:
						aud.feed_raw(len(raw_audio), raw_audio)
						if len(raw_audio) < max_read:
							time.sleep(0.01)
						raw_audio = None
						continue

				time.sleep(0.01)
		finally:
			self.feed_running = False
			self.stop_process(decoder, "decoder")
			if self.decoder_process is decoder:
				self.decoder_process = None
			self.close_pipe(decoder.stdin, "decoder stdin")
			self.pump_running = False
			logging.info(f"Radio pump exiting for request {request_id}: {self.state_log()}")

	def encode(self) -> None:
		self.encode_running = True
		decoder: subprocess.Popen[bytes] | None = None
		encoder: subprocess.Popen[bytes] | None = None

		try:
			ffmpeg_path = self.tauon.get_ffmpeg()
			if ffmpeg_path is None:
				logging.error("FFmpeg could not be found for stream encoder")
				return

			while self.c < 20:
				if self.abort:
					return
				time.sleep(0.05)

			ext = ".opus"
			rate = "48000"
			codec = self.tauon.prefs.radio_record_codec.upper()
			if codec == "OGG":
				ext = ".ogg"
				rate = "44100"
			if codec == "MP3":
				ext = ".mp3"
				rate = "44100"
			if codec == "FLAC":
				ext = ".flac"
				rate = "44100"

			target_file = self.tauon.cache_directory / "stream" / ext
			target_file.parent.mkdir(parents=True, exist_ok=True)
			if target_file.is_file():
				target_file.unlink()

			# fmt:off
			decoder_cmd = [
				str(ffmpeg_path),
				"-loglevel", "quiet",
				"-i", "pipe:0",
				"-acodec", "pcm_s16le",
				"-f", "s16le",
				"-ac", "2",
				"-ar", rate,
				"-",
			]
			# fmt:on

			decoder = self.ffmpeg_popen(decoder_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
			self.record_decoder_process = decoder

			position = 0
			request_id = self.request_id
			old_metadata = self.tauon.radiobox.song_key
			raw_queue: Queue[bytes] = Queue()

			##cmd = ["opusenc", "--raw", "--raw-rate", "48000", "-", target_file]
			# fmt:off
			encoder_cmd = [
				str(ffmpeg_path),
				"-loglevel", "quiet",
				"-f", "s16le",
				"-ar", rate,
				"-ac", "2",
				"-i", "pipe:0",
				str(target_file),
			]
			# fmt:on
			encoder = self.ffmpeg_popen(encoder_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL)
			self.record_encoder_process = encoder

			def feed_decoder(decoder: subprocess.Popen[bytes]) -> None:
				nonlocal position
				try:
					while True:
						if position < self.c:
							if position not in self.chunks:
								logging.info("The buffer was deleted too soon!")
								break

							try:
								decoder.stdin.write(self.chunks[position])
							except (BrokenPipeError, OSError, ValueError):
								break
							position += 1
						else:
							time.sleep(0.005)
						if self.abort or self.request_id != request_id:
							break
				except Exception:
					logging.exception("Encoder feeder thread crashed!")
				finally:
					logging.info(
						"Radio recording feeder exiting for request %s; position=%s chunks=%s abort=%s",
						request_id,
						position,
						self.c,
						self.abort,
					)

			feeder = threading.Thread(target=feed_decoder, args=[decoder])
			feeder.daemon = True
			feeder.start()

			reader = threading.Thread(target=self.read_stdout, args=(decoder, raw_queue, 10000, "Radio encoder decoder", request_id))
			reader.daemon = True
			reader.start()

			def save_track() -> None:
				# self.tauon.recorded_songs.append(song)

				save_file = f"{datetime.datetime.now():%Y-%m-%d %H-%M-%S} - "
				save_file += filename_safe(old_metadata)
				save_file = save_file.strip() + ext
				save_file = os.path.join(self.tauon.prefs.encoder_output, save_file)
				if os.path.exists(save_file):
					os.remove(save_file)
				if not os.path.exists(self.tauon.prefs.encoder_output):
					os.makedirs(self.tauon.prefs.encoder_output)
				shutil.move(target_file, save_file)

				# logging.info(self.tauon.pctl.tag_history)
				# logging.info(old_metadata)
				tags = self.tauon.pctl.tag_history.get(old_metadata, None)
				if tags:
					logging.info("Save metadata to file")
					# logging.info(tags)
					muta = mutagen.File(save_file, easy=True)
					muta["artist"] = tags.get("artist", "")
					muta["title"] = tags.get("title", "")
					muta["album"] = tags.get("album", "")
					# if tags["image"]:
					# 	tags["image"].seek(0)
					# 	im = Image.open(tags["image"])
					# 	width, height = im.size
					# 	tags["image"].seek(0)
					#
					# 	picture = Picture()
					# 	tags["image"].seek(0)
					# 	picture.data = tags["image"].read()
					# 	picture.type = 3
					# 	picture.desc = ""
					# 	picture.mime = "image/jpeg"
					# 	picture.width = width
					# 	picture.height = height
					#
					# 	mode_to_bpp = {'1': 1, 'L': 8, 'P': 8, 'RGB': 24, 'RGBA': 32, 'CMYK': 32, 'YCbCr': 24, 'I': 32,
					# 	'F': 32}
					# 	picture.depth = mode_to_bpp[im.mode]
					#
					# 	picture_data = picture.write()
					# 	encoded_data = base64.b64encode(picture_data)
					# 	vcomment_value = encoded_data.decode("ascii")
					# 	muta["metadata_block_picture"] = [vcomment_value]

					muta.save()

				target_pl = None
				for i, pl in enumerate(self.tauon.pctl.multi_playlist):
					if pl.title == "Saved Radio Tracks":
						target_pl = i
				if target_pl is None:
					self.tauon.pctl.multi_playlist.append(self.tauon.pl_gen(title="Saved Radio Tracks"))
					target_pl = len(self.tauon.pctl.multi_playlist) - 1

				load_order = self.tauon.pctl.LoadClass()
				load_order.playlist = self.tauon.pctl.multi_playlist[target_pl].uuid_int
				load_order.target = save_file
				self.tauon.load_orders.append(copy.deepcopy(load_order))
				self.tauon.gui.request_frame()

			def save_target_if_large() -> None:
				if target_file.exists():
					if target_file.stat().st_size > 256000:
						logging.info("Save file")
						save_track()
					else:
						logging.info("Discard small file")
						target_file.unlink()

			while True:
				if self.abort or self.request_id != request_id:
					logging.info(f"Radio recording stop requested for request {request_id}: {self.state_log()}")
					self.stop_process(decoder, "recording decoder")
					if self.record_decoder_process is decoder:
						self.record_decoder_process = None
					self.close_pipe(decoder.stdin, "recording decoder stdin")
					self.finish_encoder(encoder, timeout=2)
					if self.record_encoder_process is encoder:
						self.record_encoder_process = None
					save_target_if_large()
					return

				if old_metadata != self.tauon.radiobox.song_key:
					if (
						(self.c < 400 and not old_metadata)
						or not target_file.exists()
						or target_file.stat().st_size < 100000
					):
						old_metadata = self.tauon.radiobox.song_key
					else:
						logging.info("Split and save file")
						self.finish_encoder(encoder)
						if self.record_encoder_process is encoder:
							self.record_encoder_process = None
						save_target_if_large()
						encoder = self.ffmpeg_popen(encoder_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL)
						self.record_encoder_process = encoder

				raw_audio = None
				try:
					raw_audio = raw_queue.get(timeout=0.01)
				except Empty:
					if decoder.poll() is not None:
						logging.info("Decoder stopped")
						break
				if raw_audio:
					try:
						encoder.stdin.write(raw_audio)
					except (BrokenPipeError, OSError, ValueError):
						logging.warning("Encoder pipe closed")
						break
				else:
					time.sleep(0.005)

			self.finish_encoder(encoder, timeout=2)
			if self.record_encoder_process is encoder:
				self.record_encoder_process = None
			save_target_if_large()

		except Exception:
			logging.exception("Encoder thread crashed!")
		finally:
			if decoder is not None:
				self.stop_process(decoder, "recording decoder")
				if self.record_decoder_process is decoder:
					self.record_decoder_process = None
				self.close_pipe(decoder.stdin, "recording decoder stdin")
			if encoder is not None and encoder.poll() is None:
				self.finish_encoder(encoder, timeout=2)
			if self.record_encoder_process is encoder:
				self.record_encoder_process = None
			self.encode_running = False
			self.tauon.pctl.tag_history.clear()

	def run_download(self, r: _UrlopenRet) -> None:
		request_id = self.request_id
		logging.info(f"Radio download thread entering for request {request_id}")
		h = r.info()

		self.s_name = h.get("icy-name")
		metaint = h.get("icy-metaint")
		self.s_bitrate = h.get("icy-br")
		self.s_genre = h.get("icy-genre")
		self.s_description = h.get("icy-description")
		self.s_mime = h.get("Content-Type")

		logging.info(
			f"Radio stream headers request={request_id} mime={self.s_mime} "
			f"metaint={metaint} bitrate={self.s_bitrate} name={self.s_name}"
		)
		if self.s_mime == "audio/mpeg":
			self.s_format = "MP3"
		if self.s_mime == "audio/ogg":
			self.s_format = "OGG"
		if self.s_mime == "audio/aac":
			self.s_format = "AAC"
		if self.s_mime == "audio/aacp":
			self.s_format = "AAC+"

		test_done = 0

		icy = False
		m_remain = 0
		m = 0
		if metaint and int(metaint) > 0:
			m = int(metaint)
			m_remain = m
			icy = True

		maybe = b""

		if self.tauon.prefs.auto_rec:
			logging.info(f"Starting radio auto-record encoder for request {request_id}")
			self.download_process = threading.Thread(target=self.encode)
			self.download_process.daemon = True
			self.download_process.start()

		try:
			logging.info(f"Radio download read loop starting for request {request_id}")
			while True:
				chunk = r.read(256)

				if self.abort:
					r.close()
					logging.info(f"Abort stream connection for request {request_id}; chunks={self.c}")
					self.download_running = False
					return
				if not chunk:
					r.close()
					logging.info(f"Stream connection closed for request {request_id}; chunks={self.c}")
					self.download_running = False
					self.abort = True
					return

				if chunk:
					if not icy or m_remain > len(chunk):
						# We're sure its data Its data, send it on
						self.chunks[self.c] = chunk

						# Delete old data
						d = self.c - 90000
						if d in self.chunks:
							del self.chunks[d]

						test_done += len(chunk)
						self.c += 1
						m_remain -= len(chunk)

						continue
					# It may contain the metadata block, put it aside
					maybe += chunk

				# Try to extract ICY tag
				if maybe:
					data1 = maybe[:m_remain]
					inter = maybe[m_remain:]

					# Read the metadata length byte
					if inter:
						special = inter[0]
						follow = special * 16

						if len(inter) < follow + 2:
							# Not enough data yet
							continue

						text = inter[1 : follow + 1]
						data2 = inter[follow + 1 :]

						self.chunks[self.c] = data1 + data2
						# Delete old data
						d = self.c - 90000
						if d in self.chunks:
							del self.chunks[d]

						self.c += 1

						test_done += len(data1)
						test_done = 0

						m_remain = m - len(data2)
						test_done += len(data2)
						maybe = b""

						try:
							meta = text.decode().rstrip("\x00")
							for tag in meta.split(";"):
								if "=" in tag:
									a, b = tag.split("=", 1)
									if a == "StreamTitle":
										# logging.info("Set meta")
										self.tauon.pctl.tag_meta = b.rstrip("'").lstrip("'")
										break
						except Exception:
							logging.exception("Data malformation detected. Stream aborted.")
							r.close()
							self.download_running = False
							self.abort = True
							self.tauon.show_message(_("Data malformation detected. Stream aborted."), mode="error")
							raise
		except Exception:
			if self.abort:
				logging.info(f"Abort stream connection for request {request_id}; chunks={self.c}")
			else:
				logging.exception(f"Stream download thread crashed for request {request_id}!")
			self.abort = True
			return
		finally:
			logging.info(f"Radio download cleanup starting for request {request_id}: {self.state_log()}")
			try:
				r.close()
			except Exception:
				logging.exception("Failed to close radio stream response")
			if self.download_response is r:
				self.download_response = None
			self.download_running = False
			logging.info(f"Radio download cleanup complete for request {request_id}: {self.state_log()}")
